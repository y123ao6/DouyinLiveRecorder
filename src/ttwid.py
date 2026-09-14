# -*- encoding: utf-8 -*-
# 抖音 ttwid 共享缓存模块
#
# 背景：原先 spider.py 与 room.py 各自维护一份 ttwid 缓存并各自请求抖音主页，
# 在「每个 room 独立线程 + 独立 asyncio.run 循环」的并发模型下会出现重复拉取，
# 并产生 ReadError 瞬时重试噪声。
#
# 本模块将 ttwid 的获取与缓存统一到进程级唯一一份缓存：
#   - get_ttwid()    : 统一读取入口（懒加载 + 加锁仅拉取一次），所有模块/线程共用；
#   - warmup_ttwid() : 程序启动期同步预热，提前把缓存填好，后续调用直接命中。
#
# 跨线程/跨循环去重：每个 room 各自 asyncio.run() 独立循环并发执行，
# per-loop 的 asyncio.Lock 无法跨循环协调，故用 threading.Lock。
# 安全性：单个 asyncio.run 循环内仅一个 get_ttwid 协程，持有 threading.Lock 跨越 await 不会死锁。
# pyright: reportUnreachable=none, reportImplicitStringConcatenation=none, reportUnusedCallResult=none
import asyncio
import configparser
import os
import sys
import threading

import i18n

from .async_http import async_req
from .cookie_cache import fetch_cookies as _cache_fetch_cookies
from .cookie_cache import singleflight as _cache_singleflight
from .logger import logger

OptionalStr = str | None


def _app_root() -> str:
    # 返回应用程序根目录（exe 同级目录），与 logger.py 保持一致，用于独立定位 config.ini
    #     - 源码运行：主脚本所在目录（项目根）。
    #     - 冻结运行（PyInstaller）：exe 同级目录（_internal 的父目录），供定位 config/ffmpeg/node。
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.realpath(sys.executable))
    return os.path.split(os.path.realpath(sys.argv[0]))[0]


# 进程级唯一缓存
_cached_ttwid: str = ""
# 跨线程去重锁。RLock 允许同线程重入：锁跨越 await 时同事件循环的并发协程
# 重入不会自旋死锁（threading.Lock 情况下同线程二次 acquire 会永久阻塞）
_ttwid_lock = threading.RLock()

# 配置文件中的 ttwid 键名（位于 [Cookie] 段），用户手动填写时优先于自动获取
_CONFIG_TTWID_KEY = "ttwid"
_CONFIG_SECTION = "Cookie"


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
        return ""
    if not raw:
        return ""
    # 归一化：确保形如 ttwid=<value>
    return raw if raw.lower().startswith("ttwid=") else f"ttwid={raw}"


async def _fetch_ttwid(proxy_addr: OptionalStr = None) -> str:
    # 实际拉取并写入缓存，失败返回空字符串。
    # 改经统一 cookie 缓存（src/cookie_cache.fetch_cookies）从抖音主页动态获取，
    # 同网址下的其他模块（弹幕、url 解析等）直接复用，避免重复请求触发风控。
    global _cached_ttwid
    try:
        cookies_dict = await _cache_fetch_cookies(
            url="https://live.douyin.com/",
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
            _cached_ttwid = f"ttwid={cookies_dict['ttwid']}"
            logger.debug("自动获取抖音 ttwid 成功")
    except Exception as e:
        logger.warning(i18n.tr("自动获取抖音 ttwid 失败: {e}", e=e))
    return _cached_ttwid


async def get_ttwid(proxy_addr: OptionalStr = None) -> str:
    # 统一读取入口：命中缓存直接返回；未命中则加锁只拉取一次，其余并发调用等待复用
    # 获取优先级：已有缓存 > 本地配置文件中的 ttwid > 自动从抖音网站获取
    #
    # 2026-09-12 审查 H-2：原实现为「_ttwid_lock 跨越 await _fetch_ttwid 持有」。
    # 本项目每房间独立线程 + 独立事件循环：持锁协程 await 网络（最坏 10s+ 重试）期间，
    # 其它房间线程执行到 acquire() 会**同步阻塞其整个事件循环线程**，多房间并发冷
    # 启动全部串行卡顿；等待者拿到锁后 owner 已失败时又会各自重发请求。
    # 改为 cookie_cache.singleflight：临界区仅做字典读写，网络拉取在锁外，等待者
    # 经 future 复用同一份结果（跨循环经 call_soon_threadsafe 交付），彻底消除
    # 「跨房间阻塞」与「等待者重复请求」两个问题。
    global _cached_ttwid
    if _cached_ttwid:
        return _cached_ttwid

    # 配置优先：用户手填 ttwid 属本地确定值，不进 singleflight（无网络、无竞争必要）
    cfg = _read_config_ttwid()
    if cfg:
        _cached_ttwid = cfg
        logger.debug("使用配置文件中的 ttwid")
        return _cached_ttwid

    async def _fetch() -> str:
        return await _fetch_ttwid(proxy_addr)

    got = await _cache_singleflight(key=f"douyin_ttwid|{proxy_addr or ''}", factory=_fetch, timeout=10)
    if isinstance(got, str) and got:
        _cached_ttwid = got
    return _cached_ttwid


def warmup_ttwid(proxy_addr: OptionalStr = None) -> None:
    # 程序启动期同步预热：拉取一次写入全局缓存，后续调用直接命中。
    # 必须在同步上下文（无运行中的事件循环）调用，如 main() 的启动阶段。
    try:
        asyncio.run(get_ttwid(proxy_addr))
    except Exception as e:
        logger.warning(i18n.tr("启动时预热 ttwid 失败: {e}", e=e))
