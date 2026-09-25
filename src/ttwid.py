# -*- encoding: utf-8 -*-
# 抖音 ttwid 共享缓存模块
#
# 背景：原先 spider.py 与 room.py 各自维护一份 ttwid 缓存并各自请求抖音主页，
# 在「每个 room 独立线程 + 独立 asyncio.run 循环」的并发模型下会出现重复拉取，
# 并产生 ReadError 瞬时重试噪声。
#
# 本模块将 ttwid 的获取与缓存统一到进程级唯一一份缓存：
#   - get_ttwid()    : 统一读取入口（懒加载 + 加锁仅拉取一次），所有模块/线程共用；
#   - warmup_ttwid() : 程序启动期同步预热，提前把缓存填好，后续调用直接命中；
#   - invalidate_ttwid() : 凭据被抖音拒绝时的失效入口（MID-33），三层缓存一并作废。
#
# 跨线程/跨循环去重：每个 room 各自 asyncio.run() 独立循环并发执行，per-loop 的 asyncio.Lock
# 无法跨循环协调，故用 threading 锁（类型判据见下方 _ttwid_lock 的说明）。
# pyright: reportUnreachable=none, reportImplicitStringConcatenation=none, reportUnusedCallResult=none
import asyncio
import configparser
import os
import sys
import threading
import time

import i18n

from .async_http import async_req
from .cookie_cache import DEFAULT_TTL as _CACHE_TTL_SECONDS
from .cookie_cache import fetch_cookies as _cache_fetch_cookies
from .cookie_cache import invalidate as _cache_invalidate_cookies
from .cookie_cache import invalidate_generic as _cache_invalidate_generic
from .cookie_cache import singleflight as _cache_singleflight
from .logger import logger

OptionalStr = str | None

# ttwid 的来源网址：cookie 缓存按「归一化网址 + 代理」为键，失效时需复用同一网址。
_DOUYIN_HOME_URL = "https://live.douyin.com/"


def _app_root() -> str:
    # 返回应用程序根目录（exe 同级目录），与 logger.py 保持一致，用于独立定位 config.ini
    #     - 源码运行：主脚本所在目录（项目根）。
    #     - 冻结运行（PyInstaller）：exe 同级目录（_internal 的父目录），供定位 config/ffmpeg/node。
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.realpath(sys.executable))
    return os.path.split(os.path.realpath(sys.argv[0]))[0]


# 进程级唯一缓存
_cached_ttwid: str = ""
# MID-33（2026-09-20）：模块全局由「非空即永久返回」改为「带获取时刻、按 TTL 判陈旧」。
# 旧语义下抖音一旦作废 ttwid（风控常见形态），本进程就永不重新获取，表现为抖音解析长期
# 「HTTP 200 + 空响应体」，而 cookie_cache 的 30 分钟自愈在这层根本不参与判定
# （对照 src/room.py 的 sec_uid 缓存——它是唯一按 TTL 判定的同类全局）。
# TTL 直接取 cookie_cache.DEFAULT_TTL，与承载它的 singleflight 层同一口径，避免两层各自过期
# 造成「全局刚清、下层又立刻命中同一份旧值」的抖动。
_cached_ttwid_at: float = 0.0
# MIN-2220（2026-09-23）：上面的模块全局**不再参与快路判定**，只作「最近一次成功写入值」的
# 镜像（供 warmup 观测与本仓既有用例读取）；真正按出口分列的缓存是下面这份 dict。
# 为什么要按出口分列：另外两层（_ttwid_scopes 记的 (key, proxy) 组合、singleflight 的 key）
# 都刻意带了代理维度，唯独最外层快路 `if _cached_ttwid: return` 完全不看 proxy_addr——于是
# 首个成功出口（常见形态：直连房间先抢到）的 ttwid 会在 TTL 内被所有其它出口复用。抖音的
# ttwid 与出口 IP 强相关，跨出口复用表现为间歇「HTTP 200 + 空响应体」（风控指纹），且
# invalidate_ttwid 的作废链会把别的出口本来正常的值一并清掉、下一轮又重新抢占回来，
# 整条链路来回抖动。键：`proxy_addr or ""`（与 singleflight key 的代理维度同一写法，空串=直连）。
_cached_ttwid_by_proxy: dict[str, tuple[str, float]] = {}
# 本进程用过的 (singleflight key, 代理) 组合：invalidate_ttwid() 据此把下两层缓存一并
# 作废（key 含代理维度，不记录就找不到要清的那条）。
_ttwid_scopes: "set[tuple[str, OptionalStr]]" = set()
# 跨线程去重锁。H-2（2026-09-12）把网络拉取移出临界区后，本模块已不再 acquire 它（去重改由
# cookie_cache.singleflight 承担），保留它是因为 tests/test_concurrency.py 的
# test_ttwid_module_pattern 断言了其类型——**改锁类型会直接让该用例变红**。类型必须是可重入的
# RLock 而不是 threading.Lock：这类凭据去重锁一旦被重新接线成「跨越 await 持有」，同一事件循环里的
# 第二个并发协程就会自旋死锁（持锁协程永无法恢复），RLock 让同线程重入退化为一次幂等重复拉取，
# 跨线程去重语义不变；同样不得退回 asyncio.Lock 单例（模块级 asyncio.Lock 会绑定到首个 await 它的
# 循环，每房间独立循环下直接 RuntimeError）。同族约束见 AGENTS.md「锁的强制约定」。
_ttwid_lock = threading.RLock()

# 配置文件中的 ttwid 键名（位于 [Cookie] 段），用户手动填写时优先于自动获取
_CONFIG_TTWID_KEY = "ttwid"
_CONFIG_SECTION = "Cookie"

# 模块全局缓存的生命周期：与 cookie_cache 的默认 TTL 同值（30 分钟）。
_TTWID_TTL_SECONDS: float = float(_CACHE_TTL_SECONDS)


def _proxy_slot(proxy_addr: OptionalStr) -> str:
    # 缓存分列键：与 singleflight key 里的代理维度同一写法（None/空串都归到「直连」桶）。
    return proxy_addr or ""


def _cache_ttwid(value: str, proxy_addr: OptionalStr = None) -> str:
    # 写入按出口分列的缓存（MIN-2220 的真实缓存），并同步一份「最近写入值」镜像（仅供观测、
    # 不参与判定，理由见上方 _cached_ttwid_by_proxy）。MID-33：值与获取时刻必须同一入口设置，
    # 漏一处即退化成「永久有效」。
    global _cached_ttwid, _cached_ttwid_at
    now = time.monotonic()
    _cached_ttwid_by_proxy[_proxy_slot(proxy_addr)] = (value, now)
    _cached_ttwid = value
    _cached_ttwid_at = now
    return value


def _take_cached_ttwid(proxy_addr: OptionalStr) -> str:
    # 读取当前出口的缓存值；陈旧则删除条目并返回空串（MID-33 的 TTL 判定按出口各算各的）。
    #
    # 第一道 `_cached_ttwid` 判空**不是**遗留的跨出口复用路径，而是「整体失效开关」：本模块的分桶
    # 缓存不提供公开的 clear-by-bucket 入口，外部（tests/conftest.py 的逐用例重置、排障时手工置空）
    # 只会写 `_cached_ttwid = ""`。让镜像为空即禁用快路，外部重置才真的生效——否则 conftest 清掉
    # 镜像、分桶却仍留着上一个用例的值，会把凭据带进下一个用例（跨用例串号）。写侧唯一入口
    # _cache_ttwid() 总是「镜像 + 分桶」成对写，故镜像非空 ⟺ 至少一个桶有值。
    if not _cached_ttwid:
        return ""
    slot = _cached_ttwid_by_proxy.get(_proxy_slot(proxy_addr))
    if not slot:
        return ""
    value, fetched_at = slot
    if (time.monotonic() - fetched_at) >= _TTWID_TTL_SECONDS:
        # 陈旧的值先删掉再往下走，否则「非空即返回」会让 cookie_cache 的
        # 30 分钟自愈在本层永久短路。
        _cached_ttwid_by_proxy.pop(_proxy_slot(proxy_addr), None)
        return ""
    return value


def _read_config_ttwid() -> str:
    # 从 config.ini 的 [Cookie] 段读取用户手动填写的 ttwid；为空或缺失返回 ""
    # 与 logger.py 一致：用 RawConfigParser + utf-8-sig 独立读取，避免依赖 main.py 的执行顺序
    try:
        parser = configparser.RawConfigParser()
        _ = parser.read(f"{_app_root()}/config/config.ini", encoding="utf-8-sig")
        raw = parser.get(_CONFIG_SECTION, _CONFIG_TTWID_KEY).strip()
    except configparser.NoSectionError, configparser.NoOptionError, configparser.Error:
        return ""
    except Exception:
        # 吞没即正确：本函数只是「可选的用户手填覆盖值」读取，配置文件缺失/损坏/无权限
        # 一律按「未填写」处理并回落到自动获取，绝不应让录制链路因读不到覆盖值而抛错。
        # 真正的配置损坏由 main.py 的启动期读取负责报告，此处重复告警只会刷屏。
        return ""
    if not raw:
        return ""
    # 归一化：确保形如 ttwid=<value>
    return raw if raw.lower().startswith("ttwid=") else f"ttwid={raw}"


async def _fetch_ttwid(proxy_addr: OptionalStr = None) -> str:
    # 实际拉取并写入缓存，失败返回空字符串。
    # 改经统一 cookie 缓存（src/cookie_cache.fetch_cookies）从抖音主页动态获取，
    # 同网址下的其他模块（弹幕、url 解析等）直接复用，避免重复请求触发风控。
    try:
        cookies_dict = await _cache_fetch_cookies(
            url=_DOUYIN_HOME_URL,
            proxy_addr=proxy_addr,
            headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
            },
            timeout=10,
            http2=False,  # 抖音对 HTTP/2 支持不稳定，常触发 ReadError('')，降级到 HTTP/1.1
            fetcher=async_req,  # 传入本模块 async_req，使单测对 src.ttwid.async_req 打桩仍生效
        )
        if isinstance(cookies_dict, dict) and cookies_dict.get("ttwid"):
            logger.debug("自动获取抖音 ttwid 成功")
            return _cache_ttwid(f"ttwid={cookies_dict['ttwid']}", proxy_addr)
    except Exception as e:
        # MIN-2222：Windows 下 socket.timeout / httpx 超时族的 str() 可能为空串，
        # 只打 {e} 会得到一条空白告警，无法区分超时/DNS/证书/依赖缺失。
        logger.warning(i18n.tr("自动获取抖音 ttwid 失败: {type_name}: {e}", type_name=type(e).__name__, e=e))
    # MIN-2220：失败时**不得**回落到 `_cached_ttwid` 镜像返回——那正是「把别的出口的值
    # 当本出口的值」的入口（本出口这次什么都没拿到，返回空串由调用方按未开播/风控处理）。
    return ""


async def get_ttwid(proxy_addr: OptionalStr = None) -> str:
    # 统一读取入口：命中缓存直接返回；未命中则只拉取一次，其余并发调用等待复用。
    # 获取优先级：已有缓存 > 本地配置文件中的 ttwid > 自动从抖音网站获取。
    #
    # H-2（2026-09-12）：原实现为「_ttwid_lock 跨越 await _fetch_ttwid 持有」。本项目每房间独立线程
    # + 独立事件循环：持锁协程 await 网络（最坏 10s + 重试）期间，其它房间线程执行到 acquire() 会
    # **同步阻塞其整个事件循环线程**，多房间并发冷启动全部串行卡顿；等待者拿到锁后 owner 已失败时
    # 又会各自重发请求。现改为 cookie_cache.singleflight：临界区仅做字典读写、网络拉取在锁外，
    # 等待者经 future 复用同一份结果（跨循环经 call_soon_threadsafe 交付）。
    # MID-33 + MIN-2220：快路按「本次调用的出口」取缓存，陈旧即丢弃并继续往下走。
    cached = _take_cached_ttwid(proxy_addr)
    if cached:
        return cached

    # 配置优先：用户手填 ttwid 属本地确定值，不进 singleflight（无网络、无竞争必要）
    cfg = _read_config_ttwid()
    if cfg:
        _cache_ttwid(cfg, proxy_addr)
        logger.debug("使用配置文件中的 ttwid")
        return _cached_ttwid

    async def _fetch() -> str:
        return await _fetch_ttwid(proxy_addr)

    key = f"douyin_ttwid|{proxy_addr or ''}"
    # 记下 (key, 代理)：invalidate_ttwid() 需要它才能定位到承载本值的那条下层缓存
    _ttwid_scopes.add((key, proxy_addr))
    got = await _cache_singleflight(key=key, factory=_fetch, timeout=10)
    if isinstance(got, str) and got:
        _cache_ttwid(got, proxy_addr)
    # 只返回本出口的值（_fetch_ttwid 成功时已按 proxy_addr 写入；失败时这里是空串，
    # 不再像旧实现那样把别的出口的镜像值递出去）。
    return _take_cached_ttwid(proxy_addr)


# 显式作废进程内的 ttwid（MID-33 的失效入口，与 spider.invalidate_bili_buvid_cache 同形）：
# 抖音侧拒绝该凭据（HTTP 200 + 空 body 的风控形态、弹幕鉴权失败）时由调用方触发，
# 下一轮 get_ttwid 会重新获取，而不是等 TTL 自然过期。
# 三层缓存必须一并清：模块全局（本层）、generic singleflight、同网址的 cookie 缓存——
# 只清全局会立刻被下层的同一份旧值回填（MID-40 描述的正是这种「失效只生效一半」）。
def invalidate_ttwid(proxy_addr: OptionalStr = None) -> None:
    # 与 spider.invalidate_bili_buvid_cache 同形：无日志、纯清缓存（失效本身的可观测性由
    # 下一轮「自动获取抖音 ttwid 成功」的 debug 承担，避免为目录新增无占位符条目）。
    global _cached_ttwid, _cached_ttwid_at
    _cached_ttwid = ""
    _cached_ttwid_at = 0.0
    # MIN-2220：分桶缓存必须跟着镜像一起清，否则快路仍会命中被平台拒绝的那份值。刻意**整体清空**
    # 而不是只清 proxy_addr 那一个桶：本函数的语义是「抖音拒了这支凭据」，而同一进程各桶的值很可能
    # 来自同一次主页请求（cookie_cache 会跨出口复用 set-cookie），逐桶保留会留下同样被拒的值。
    # 代价只是各出口下一轮重新拉取一次，属低频路径。
    _cached_ttwid_by_proxy.clear()
    scopes = set(_ttwid_scopes)
    if proxy_addr is not None:
        scopes.add((f"douyin_ttwid|{proxy_addr or ''}", proxy_addr or None))
    for key, scope_proxy in scopes:
        _cache_invalidate_generic(key)
        _cache_invalidate_cookies(_DOUYIN_HOME_URL, scope_proxy)


def warmup_ttwid(proxy_addr: OptionalStr = None) -> None:
    # 程序启动期同步预热：拉取一次写入全局缓存，后续调用直接命中。
    # 必须在同步上下文（无运行中的事件循环）调用，如 main() 的启动阶段。
    try:
        asyncio.run(get_ttwid(proxy_addr))
    except Exception as e:
        # MIN-2222：同 _fetch_ttwid，异常文本可能为空串（Windows 下的超时类异常），
        # 缺类型名会让「预热失败」成为一条无法归因的空行。
        logger.warning(i18n.tr("启动时预热 ttwid 失败: {type_name}: {e}", type_name=type(e).__name__, e=e))
