# -*- encoding: utf-8 -*-
# 统一 cookie 缓存模块
#
# 背景：原先各平台各自维护一份「从该网址动态获取的访客 cookie」缓存并各自请求网址
# （如 src/ttwid.py 的抖音 ttwid、src/spider.py 的快手 did）。在「每个 room 独立线程 +
# 独立 asyncio.run 循环」的并发模型下，同网址会被多个房间重复请求，触发平台风控
# （返回 HTTP 200 但空响应体），表现为解析静默失败。
#
# 本模块把「按网址动态获取 cookie」的缓存统一到进程内唯一一份存储：
#   - fetch_cookies(url, proxy, ...) : 统一读取入口——命中缓存直接返回；未命中则加锁只
#                                     拉取一次，其余并发调用等待复用同一份结果。
#   - get_cached(url, proxy)        : 同步只读查询（不触发网络请求），供其他模块复用。
#   - get_cookie_str(url, proxy, ...) : 同上但返回拼接好的 "k=v; k=v" 字符串。
#   - invalidate(url, proxy) / clear() : 失效与清空，供调试或强制刷新。
#
# ── 存储结构 ──
#   _cookie_cache: dict[str, tuple[dict[str, str], float]]，key = _make_key(url, proxy)
#   （归一化网址 + 代理地址），value = (原始 cookie 字典, 写入时刻 monotonic)。
#   缓存的是「网址下发的原始访客 cookie 字典」，不做平台特定的字段裁剪，
#   由各调用方按自己的需要提取（如 ttwid 取 "ttwid"，快手取 "did"/"didv"）。
#
# ── 失效策略 ──
#   - TTL 失效：条目带写入时间戳，超过 ttl 秒即失效、下次访问重新拉取。
#     DEFAULT_TTL = 30 * 60（30 分钟），与 src/room.py 的 sec_uid 缓存保持一致，
#     在「消除重复请求」与「cookie 失效后自愈」之间取得平衡（录制进程可能连续运行数天）。
#   - 失败不缓存：拉取异常或返回空字典时一律不写入缓存，下次访问会重试，
#     避免把「瞬时失败」固化成长期空值。
#   - 世代号（MI-12）：invalidate() / clear() 递增 _cache_generation，在途拉取者写回前比对，
#     期间发生过失效就丢弃本次结果。原实现只清结果字典、不动 _inflight 登记表，于是
#     invalidate() 后立即重新 fetch_cookies() 若命中在途登记，又会拿到那份**已被判定过期**的
#     cookie，平台风控作废后的自愈链被打断，直到 TTL（默认 30 分钟）自然过期为止。
#   - 并发去重（singleflight）：threading.Lock 只保护「缓存字典 + 在途登记表」的同步
#     读写，绝不在锁内 await——锁跨 await 持有时，同事件循环内的并发协程属于同一
#     线程、全部可重入该锁，互斥完全失效（多个协程会并发请求同一网址，恰恰是要消除
#     的风控触发源）。每个房间线程各自 asyncio.run() 独立循环：抢到拉取权的协程负责
#     拉取，等待者（同循环或跨循环）登记 future 复用同一份结果，跨循环交付经
#     loop.call_soon_threadsafe 回写（future 非线程安全，禁止跨线程直接 set_result）。
#
# ── 跨模块调用方式 ──
#   from .cookie_cache import fetch_cookies, get_cached, get_cookie_str
#   1) 动态获取并复用：cookies = await fetch_cookies("https://live.douyin.com/", proxy_addr=proxy)
#   2) 仅复用不拉取：   cached  = get_cached("https://live.douyin.com/", proxy_addr=proxy)
#   3) 取拼接字符串：   s      = await get_cookie_str("https://live.kuaishou.com/", proxy_addr=proxy)
# pyright: reportImplicitStringConcatenation=none, reportUnknownArgumentType=none, reportUnknownMemberType=none, reportUnknownVariableType=none
import asyncio
import threading
import time
from typing import Any, Callable, Optional

import i18n

from . import utils
from .async_http import async_req
from .logger import logger

OptionalStr = str | None

# 进程级唯一 cookie 缓存：key -> (cookie_dict, expire_ts)
_cookie_cache: dict[str, tuple[dict[str, str], float]] = {}
# 在途拉取登记表：key 在表中即表示某协程正在拉取该网址；value 为等待结果的
# (等待者所在事件循环, 等待者 future) 列表，拉取完成后逐个交付
_inflight: dict[str, list[tuple[asyncio.AbstractEventLoop, asyncio.Future[dict[str, str]]]]] = {}
# 去重锁：只保护 _cookie_cache 与 _inflight 的同步读写（临界区内绝无 await）
_cache_lock = threading.Lock()

# MI-12：缓存世代号，invalidate() / clear() / invalidate_generic() 递增它，在途拉取者写回前
# 比对，世代变了就丢弃本次结果（避免「刚失效就被在途请求回填」）。
# fetch_cookies 与 singleflight 两层共用同一个计数器，语义必须保持一致。
_cache_generation = 0
# 等待其它线程在途拉取的超时余量（秒）：拉取线程若异常死亡（如 asyncio.run 被硬杀），
# 等待者按 timeout + 余量 超时返回空结果，避免永久挂起
_INFLIGHT_WAIT_MARGIN = 5.0

# 默认失效时间：30 分钟。允许调用方按需覆盖（如更长生命周期的凭据）。
DEFAULT_TTL = 30 * 60


def _make_key(url: str, proxy_addr: OptionalStr) -> str:
    # 以「归一化网址 + 代理」为 key。
    # 访客 cookie 由域名下发，与查询参数/尾斜杠无关，故去掉 ? 与尾随 /。
    # 代理不同（直连 vs 走代理）下发的 cookie 可能不同，故纳入 key 区分。
    normalized = url.split("?")[0].rstrip("/")
    return f"{normalized}|{proxy_addr or ''}"


def _get_cached_entry(key: str) -> tuple[dict[str, str], float] | None:
    # 在锁内读取，避免并发下的字典视图不一致
    with _cache_lock:
        return _cookie_cache.get(key)


def get_cached(url: str, proxy_addr: OptionalStr = None) -> dict[str, str] | None:
    # 同步只读查询：命中且未过期返回 cookie 字典，否则返回 None（不触发网络请求）。
    # 供其他模块在不发起请求的前提下复用已缓存的同网址 cookie。
    entry = _get_cached_entry(_make_key(url, proxy_addr))
    if entry is None:
        return None
    cookies, expire_ts = entry
    if (time.monotonic() - expire_ts) >= DEFAULT_TTL:
        return None
    return cookies


def _deliver(
    waiter_loop: asyncio.AbstractEventLoop, fut: asyncio.Future[dict[str, str]], cookies: dict[str, str]
) -> None:
    # 把拉取结果交付给等待者（须在拉取方协程内调用）：
    # - 等待者与拉取方同循环：本函数正运行于该循环线程，直接 set_result 安全；
    # - 跨循环：future 非线程安全，必须经 call_soon_threadsafe 调度到等待者
    #   自己的循环线程执行；其循环已关闭时结果无处交付（等待方的超时兜底）。
    def _set() -> None:
        if not fut.done():
            fut.set_result(cookies)

    if waiter_loop is asyncio.get_running_loop():
        _set()
        return
    try:
        waiter_loop.call_soon_threadsafe(_set)
    except RuntimeError:
        # 等待者所在循环已关闭：丢弃结果，其 wait_for 超时兜底
        pass


async def fetch_cookies(
    url: str,
    proxy_addr: OptionalStr = None,
    *,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 10,
    http2: bool = False,
    ttl: int = DEFAULT_TTL,
    fetcher: Callable[..., Any] | None = None,
) -> dict[str, str]:
    # 统一读取入口：命中缓存直接返回；未命中则加锁只拉取一次，并发调用复用同一结果。
    # 返回该网址下发的原始访客 cookie 字典（调用方按需提取字段）。
    #
    # fetcher: 实际发起 HTTP 请求的可调用对象，默认用本模块的 async_req。**调用方应传入自身
    # 命名空间下的 async_req**（如 ttwid / spider 模块导入的那一个），否则单测对
    # "src.<mod>.async_req" 打的桩拦不住这里的请求——各模块导入的是同一函数对象，但分属不同
    # 命名空间，对模块命名空间打桩不会改动本模块的默认引用。这是一条测试设计契约，不是可选优化。
    # 签名需兼容 (url, *, proxy_addr, headers, return_cookies, timeout, http2) -> dict。
    key = _make_key(url, proxy_addr)
    now = time.monotonic()
    do_fetch: Callable[..., Any] = fetcher if callable(fetcher) else async_req

    # 快速路径（无锁）：绝大多数调用命中此处
    entry = _get_cached_entry(key)
    if entry is not None and (now - entry[1]) < ttl:
        return entry[0]

    # 未命中：锁内二次检查缓存（锁内绝无 await）。key 已在途则登记为等待者复用同一份结果，
    # 否则本协程登记为拉取者
    loop = asyncio.get_running_loop()
    waiter: asyncio.Future[dict[str, str]] | None = None
    with _cache_lock:
        entry = _cookie_cache.get(key)
        if entry is not None and (time.monotonic() - entry[1]) < ttl:
            return entry[0]
        if key in _inflight:
            waiter = loop.create_future()
            _inflight[key].append((loop, waiter))
        else:
            _inflight[key] = []  # 占位：本协程即拉取者，列表留给后续等待者登记
    if waiter is not None:
        try:
            return await asyncio.wait_for(waiter, timeout + _INFLIGHT_WAIT_MARGIN)
        except TimeoutError:
            # 拉取者所在线程异常退出（循环被硬杀等极端场景）：超时返回空结果，
            # 失败不缓存，下次访问重新走拉取
            logger.warning(
                i18n.tr(
                    "等待其它线程的 cookie 拉取超时，返回空结果: {masked_key}",
                    masked_key=utils.mask_credentials(key),
                )
            )
            return {}

    # 本协程为拉取者：异常/空结果同样要交付等待者（失败语义与单协程路径一致）
    with _cache_lock:
        _gen_before = _cache_generation
    try:
        try:
            result = await do_fetch(
                url=url,
                proxy_addr=proxy_addr,
                headers=headers,
                return_cookies=True,
                timeout=timeout,
                http2=http2,
            )
        except Exception as e:
            # 失败不缓存、下次重试；带类型 + URL 便于排查（Windows 下 e 的 str() 可能为空）。
            # WD-01：异常文本常内嵌完整请求 URL（含签名/鉴权查询串），必须一并脱敏
            logger.warning(
                i18n.tr(
                    "动态获取 cookie 失败: {url} - {type_name}: {e}",
                    url=utils.mask_credentials(url),
                    type_name=type(e).__name__,
                    e=utils.mask_credentials(str(e)),
                )
            )
            cookies = {}
        else:
            # async_req(return_cookies=True, include_cookies=False) 成功返回 dict，异常返回 {}
            if isinstance(result, dict):
                cookies = {k: str(v) for k, v in result.items()}
            elif isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                cookies = {k: str(v) for k, v in result[1].items()}
            else:
                cookies = {}
    except BaseException:
        # 本协程被取消（房间停止/进程退出）：立即摘除登记并给等待者交付空结果，
        # 避免其它线程的等待者一直等到超时
        with _cache_lock:
            pending = _inflight.pop(key, [])
        for waiter_loop, waiter_fut in pending:
            _deliver(waiter_loop, waiter_fut, {})
        raise
    # 仅缓存非空结果（空结果视为失败、不固化，下次可重试）；写回前比对世代号（MI-12），
    # 期间被 invalidate()/clear() 失效过就丢弃本次结果
    if cookies:
        with _cache_lock:
            if _gen_before == _cache_generation:
                _cookie_cache[key] = (cookies, time.monotonic())
        logger.debug(
            i18n.tr(
                "动态获取 cookie 成功并缓存: {masked_key}",
                masked_key=utils.mask_credentials(key),
            )
        )
    with _cache_lock:
        pending = _inflight.pop(key, [])
    for waiter_loop, waiter_fut in pending:
        _deliver(waiter_loop, waiter_fut, cookies)
    return cookies


async def get_cookie_str(
    url: str,
    proxy_addr: OptionalStr = None,
    *,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 10,
    http2: bool = False,
    ttl: int = DEFAULT_TTL,
    fetcher: Callable[..., Any] | None = None,
) -> str:
    # 便捷封装：返回拼接好的 "k=v; k=v" 字符串；无 cookie 时返回空串。
    cookies = await fetch_cookies(
        url, proxy_addr, headers=headers, timeout=timeout, http2=http2, ttl=ttl, fetcher=fetcher
    )
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


# 通用 singleflight 缓存（2026-09-12 审查 H-2）：与 fetch_cookies 完全同范式，
# 但缓存值是任意对象而非 cookie dict，供「一次性拉取、长期复用」的凭据类数据
# （Twitch Client-Id、B站 buvid3、快手 did 字符串、抖音 ttwid）复用。
#
# 背景：这些拉取点原先是「threading.Lock 临界区内 await 网络请求」的反模式——
# 本项目为「每房间独立线程 + 独立事件循环」模型，锁内 await 期间房间 B 执行到
# with 语句会同步阻塞其整个事件循环线程；B站处为不可重入锁，同循环内两协程并发
# 进入即互等死锁。本函数把「临界区只做字典读写、网络请求移出锁外」固化成公共实现。
_generic_cache: dict[str, tuple[Any, float]] = {}
_generic_inflight: dict[str, list[tuple[asyncio.AbstractEventLoop, asyncio.Future[Any]]]] = {}


def _deliver_generic(waiter_loop: asyncio.AbstractEventLoop, fut: asyncio.Future[Any], value: Any) -> None:
    # 与 _deliver 同语义，仅类型放宽为 Any（见 _deliver 的跨循环交付说明）
    def _set() -> None:
        if not fut.done():
            fut.set_result(value)

    if waiter_loop is asyncio.get_running_loop():
        _set()
        return
    try:
        waiter_loop.call_soon_threadsafe(_set)
    except RuntimeError:
        pass


async def singleflight(
    key: str,
    factory: Callable[[], Any],
    *,
    ttl: float = DEFAULT_TTL,
    timeout: float = 10.0,
    cache_falsy: bool = False,
) -> Any:
    # 通用 singleflight：同 key 的并发调用只执行一次 factory，其余等待复用同一结果。
    #
    # - key：缓存键（调用方自行保证不同用途不碰撞，建议带前缀，如 "twitch_client_id|proxy"）
    # - factory：无参协程工厂（Callable[[], Awaitable[Any]]）；被调用于锁外，故可安全 await
    # - ttl：缓存秒数；cache_falsy=False（默认）时空结果不缓存（视为失败，下次重试）
    # - timeout：等待其它协程在途拉取的超时（秒），超时返回 None 而非永久挂起
    #
    # 返回值语义：命中缓存返回缓存值；本协程为拉取者返回 factory 结果；
    # 等待者返回拉取者结果（拉取者异常/取消时返回 None）。
    now = time.monotonic()

    # 快速路径（MI-13：纳入 _cache_lock）。原实现无锁读，与 invalidate_generic / clear
    # 的持锁写不互斥——本模块其余所有字典访问都在锁内，口径不一致。
    # 临界区只有一次 dict.get、无 await，加锁不会退化为锁内 await。
    with _cache_lock:
        entry = _generic_cache.get(key)
        if entry is not None and (now - entry[1]) < ttl:
            return entry[0]

    loop = asyncio.get_running_loop()
    waiter: asyncio.Future[Any] | None = None
    with _cache_lock:
        entry = _generic_cache.get(key)
        if entry is not None and (time.monotonic() - entry[1]) < ttl:
            return entry[0]
        if key in _generic_inflight:
            waiter = loop.create_future()
            _generic_inflight[key].append((loop, waiter))
        else:
            _generic_inflight[key] = []

    if waiter is not None:
        try:
            return await asyncio.wait_for(waiter, timeout + _INFLIGHT_WAIT_MARGIN)
        except TimeoutError:
            logger.warning(
                i18n.tr(
                    "等待其它线程的凭据拉取超时，返回空结果: {masked_key}",
                    masked_key=utils.mask_credentials(key),
                )
            )
            return None

    # 本协程为拉取者：锁外执行 factory（临界区内绝无 await），写回前比对世代号——MI-12 的
    # 机制与 fetch_cookies 共用同一个 _cache_generation，两层必须同口径：否则「凭据被平台拒绝
    # → invalidate_generic(key)」与「同 key 在途拉取」并发时，已被判定作废的那份结果（如 B 站
    # 软拒绝的随机 UUID buvid3）会在拉取结束后重新固化进缓存、直到 TTL（30 分钟）自然过期，
    # 自愈链在 singleflight 侧断开（MID-40 修的正是这个，fetch_cookies 一侧早已修好）。
    with _cache_lock:
        _gen_before = _cache_generation
    try:
        try:
            value = await factory()
        except Exception as e:
            logger.warning(
                i18n.tr(
                    "凭据拉取失败: {masked_key} - {type_name}: {e}",
                    masked_key=utils.mask_credentials(key),
                    type_name=type(e).__name__,
                    e=e,
                )
            )
            value = None
    except BaseException:
        # 本协程被取消：摘除登记并给等待者交付 None，避免其空等超时
        with _cache_lock:
            pending = _generic_inflight.pop(key, [])
        for waiter_loop, waiter_fut in pending:
            _deliver_generic(waiter_loop, waiter_fut, None)
        raise

    if value or cache_falsy:
        with _cache_lock:
            # 世代变更（期间被 invalidate_generic / clear / invalidate 作废）则丢弃本次结果、
            # 不回填缓存——与 fetch_cookies 的 MI-12 口径一致（那里同样静默丢弃，等待者仍拿
            # 到本次值，但下一轮会重新走拉取，从而让「被拒凭据」不被固化 30 分钟）。
            if _gen_before == _cache_generation:
                _generic_cache[key] = (value, time.monotonic())
    with _cache_lock:
        pending = _generic_inflight.pop(key, [])
    for waiter_loop, waiter_fut in pending:
        _deliver_generic(waiter_loop, waiter_fut, value)
    return value


def invalidate_generic(key: str | None = None) -> None:
    # 失效通用缓存（key 为 None 时清空全部）。供调试或凭据失效后强制刷新。
    global _cache_generation
    with _cache_lock:
        _cache_generation += 1
        if key is None:
            _generic_cache.clear()
            return
        _generic_cache.pop(key, None)


def invalidate(url: str | None = None, proxy_addr: OptionalStr = None) -> None:
    # 失效指定网址（或整份）缓存。url 为 None 时清空全部。
    global _cache_generation
    with _cache_lock:
        # MI-12：递增世代，令在途拉取者放弃回填
        _cache_generation += 1
        if url is None:
            _cookie_cache.clear()
            return
        _cookie_cache.pop(_make_key(url, proxy_addr), None)


def clear() -> None:
    # 清空全部缓存（调试/测试用）：cookie 缓存与通用 singleflight 缓存一并清。
    # 2026-09-12 审查 H-2：新增通用缓存后，若 clear() 只清 cookie 缓存，
    # 单测间会残留上一条用例的凭据（如 ttwid=fetched），导致下一条用例
    # 命中旧缓存而非本次打桩值——表现为"测试莫名失败且只在整包运行时出现"。
    global _cache_generation
    with _cache_lock:
        _cache_generation += 1
        _cookie_cache.clear()
        _generic_cache.clear()
