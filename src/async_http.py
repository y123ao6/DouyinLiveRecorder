# -*- coding: utf-8 -*-
# 异步 HTTP 客户端模块 - 提供高效的异步 HTTP 请求功能

import asyncio
import re
import threading
from collections.abc import Mapping, Sequence
from typing import cast
from urllib.parse import urlparse

import httpx

import i18n

from . import http_config as config
from . import utils
from .logger import logger

OptionalStr = str | None
OptionalDict = dict[str, str] | None

# 全局连接池配置，提高 HTTP 请求性能
_httpx_limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)

# AsyncClient 必须在其事件循环内创建并使用，进程退出时 aclose() 释放连接池，故缓存按循环分桶。
#
# 缓存键含「事件循环」维度（MID-21，2026-09-20）：AsyncClient 与其连接池绑定到创建它的
# 循环，而本仓是「每房间一个独立线程 + 每轮 asyncio.run() 一个新循环」。旧键只有
# (proxy, verify, http2)，于是 B 房间发现缓存条目属于 A 房间的循环时**把 A 正在使用的条目
# pop 掉**再自建，A 下一请求又把 B 逐出 —— 承诺的 keepalive 完全不成立（每请求重做
# TCP+TLS）；且被逐出的实例仍持活连接：按 2026-09-04 的跨循环决策不为它创建 aclose 协程，
# 又已脱离缓存、不在 close_all_clients_sync 覆盖范围内，只能等 socket finalizer。
# 现按循环分桶：只可能逐出「属于当前循环」的条目，其余按其 loop.is_closed() 惰性清扫
# （只丢引用，绝不创建跨循环协程）。循环维度不等于跨 asyncio.run() 复用同一连接（每轮必然
# 重建客户端），真要做到需把房间线程改成常驻事件循环——那是另一项改动。
_CacheKey = tuple[str, bool, bool, asyncio.AbstractEventLoop]
# MIN-2217：值第三元是创建线程。atexit/信号钩子跑在某个具体线程上，只能安全关闭
# 「本线程 + 本循环」创建的那份连接池；其余既不能跨循环 await，也不能 schedule 到他的循环。
_CacheValue = tuple[httpx.AsyncClient, asyncio.AbstractEventLoop, threading.Thread]
_client_cache: dict[_CacheKey, _CacheValue] = {}
# 保护 _client_cache 的跨线程锁：多房间「独立线程+独立事件循环」并发取客户端时序列化
# check-then-act 竞态。临界区只做同步 dict 操作、绝不含 await。
# MIN-2221（2026-09-23）：必须是 **RLock**——本锁会被同一线程重入持有。主线程除 asyncio.run()
# 驱动 async_req（warmup_ttwid、启动期探测）而持有本锁之外，还会在 safe_exit（SIGINT/SIGTERM
# 处理器，同样跑在主线程）里调 close_all_clients_sync() 取本锁；信号恰好落在 _get_client 临界区
# 的两行 dict 操作之间时，非重入锁让信号处理器自死锁。症状：「Ctrl+C 后既不退出也不报错」。
# 临界区内零 await，故 RLock 不引入跨循环风险；改回 Lock 即重新引入该死锁。
_client_cache_lock = threading.RLock()
# 惰性清扫阈值：每轮 asyncio.run() 都留下一个「循环已关闭」的条目，不清则随房间数×轮数
# 无界增长。全表扫描需持锁，故仅在缓存规模超过阈值时才扫（正常规模远小于此）。
_CACHE_SWEEP_THRESHOLD = 32


def _sweep_closed_loop_entries(current_loop: asyncio.AbstractEventLoop) -> None:
    # 必须在持有 _client_cache_lock 时调用（只做同步 dict 操作）。跨循环的失效条目
    # **只丢引用、绝不 await/调度 aclose**——2026-09-04 的决策依然成立：外部线程无法可靠
    # 控制他线程循环的生命周期，创建协程只会换来 "never awaited" 或 "Task was destroyed
    # but it is pending"（完整论证见 _get_client 内的跨循环注）。
    if len(_client_cache) <= _CACHE_SWEEP_THRESHOLD:
        return
    for key, (_client, loop, _owner) in list(_client_cache.items()):
        if loop is current_loop or not loop.is_closed():
            continue
        _client_cache.pop(key, None)


def _build_client(
    proxy_addr: OptionalStr,
    timeout: int,
    verify: bool,
    http2: bool,
) -> httpx.AsyncClient:
    # 构造一支新的 AsyncClient；构造放在锁外（httpx.AsyncClient.__init__ 涉及传输层初始化）。
    return httpx.AsyncClient(
        proxy=proxy_addr,
        timeout=timeout,
        verify=verify,
        http2=http2,
        limits=_httpx_limits,
    )


async def _get_client(
    proxy_addr: OptionalStr,
    timeout: int,
    verify: bool,
    http2: bool,
) -> httpx.AsyncClient:
    # 按 (代理, verify, http2, 当前事件循环) 维度复用 AsyncClient；timeout 每次请求单独传入，
    # 避免不同调用方覆盖彼此的超时。
    current_loop = asyncio.get_running_loop()
    current_thread = threading.current_thread()
    key: _CacheKey = (proxy_addr or "", verify, http2, current_loop)
    # 2026-09-12 审查 6.3：原实现在锁外创建 client 后于锁内无条件覆盖写入，两个协程并发首建
    # 同一 key 时后写者覆盖先写者——被覆盖的 AsyncClient 从此无引用、连接池无人 aclose，
    # 跨事件循环场景下随房间数累积泄漏。改为「探查 → 按需创建 → 写前二次检查 →
    # 落败者主动关闭自建实例」。
    with _client_cache_lock:
        _sweep_closed_loop_entries(current_loop)
        cached = _client_cache.get(key)
    if cached is not None:
        # 第三元 owner 不参与这里的判定——复用只取决于循环归属；它在 _close_all_clients
        # 里才起作用（那里必须知道「这份连接池是哪个线程建的」），见 MIN-2217。
        client, client_loop, _owner = cached
        # key 已含当前循环，故命中必然同循环：client 未关闭即可直接复用
        if not client.is_closed and client_loop is current_loop:
            return client
        stale = False
        with _client_cache_lock:
            # 二次检查：可能已被并发协程替换，替换成功者负责旧 client 的释放
            if _client_cache.get(key) is cached:
                _client_cache.pop(key, None)
                stale = True
        if stale and not client.is_closed:
            # 同循环的失效客户端：当前循环就是它的创建循环，await aclose 安全
            try:
                await client.aclose()
            except Exception as e:
                logger.debug(i18n.tr("关闭失效 AsyncClient 失败: {e}", e=e))
            # 跨事件循环的旧循环（运行中/已停止/已关闭）一律不创建 aclose 协程（2026-09-04 定稿）。
            # 三条备选都被否证：① run_coroutine_threadsafe 只调度不等待——旧循环已停/已关时回调
            #   永不执行，协程从未被 await，GC 时报 "coroutine ... aclose was never awaited"，
            #   且数量随机波动（1~2 条 flaky，经 unraisableexception 逸出到任意后续用例）；
            # ② 改成 is_running() 门控 + fut.result(timeout) 等待也治不了根——asyncio.run 收尾窗口内
            #   循环还在运转但随时停止，安排的任务可能永不执行（"Task was destroyed but it is
            #   pending"），future 永不完成还会把一次收尾竞态放大成整段超时时长的阻塞；
            # ③ 在当前循环直接 await 旧 client.aclose() 会操作绑定旧循环的 transport（httpcore
            #   连接池关闭触碰旧循环的 call_soon，循环已关时直接 RuntimeError）。
            # 故唯一可靠做法就是不创建协程，丢引用交 GC（AsyncClient 析构会尝试关底层传输），
            # 进程级收尾仍由 atexit 的 close_all_clients_sync 负责。
            # 2026-09-20 MID-21 之后该分支在 _get_client 内已不可达（键含循环 → 命中必同循环），
            # 跨循环条目的回收改由 _sweep_closed_loop_entries 承担：同样只丢引用、不创建协程。

    new_client = _build_client(proxy_addr, timeout, verify, http2)
    reused: httpx.AsyncClient | None = None
    with _client_cache_lock:
        # 写前二次检查：并发首建时可能已有他协程写入同 key。
        # 落败者必须主动关闭自建实例，否则其连接池同样泄漏（与审查指出的同型问题）
        winner = _client_cache.get(key)
        if winner is not None and not winner[0].is_closed and winner[1] is current_loop:
            reused = winner[0]
        else:
            _client_cache[key] = (new_client, current_loop, current_thread)
    if reused is not None:
        try:
            await new_client.aclose()
        except Exception as e:
            logger.debug(i18n.tr("关闭并发重复创建的 AsyncClient 失败: {e}", e=e))
        return reused
    return new_client


async def _acquire_client(
    proxy_addr: OptionalStr,
    timeout: int,
    verify: bool,
    http2: bool,
    stateful: bool,
) -> tuple[httpx.AsyncClient, bool]:
    # 返回 (客户端, 是否由本次调用独占)。独占客户端必须在**当前循环**内关闭，
    # 故只用于「本次请求自建自管」的形态，不进缓存。
    if not stateful:
        return await _get_client(proxy_addr, timeout, verify, http2), False
    return _build_client(proxy_addr, timeout, verify, http2), True


async def _release_client(client: httpx.AsyncClient) -> None:
    # 关闭当前循环内自建的独占客户端（同循环 aclose 是被允许的唯一形态）。
    try:
        if not client.is_closed:
            await client.aclose()
    except Exception as e:
        # 复用已在四语目录里的 "关闭失效 AsyncClient 失败: {e}"——新增 tr 模板须同步五处目录
        # （四份后端 + web/app.js）并重编译 .mo，否则 test_i18n_migration 的
        # 「运行时模板 ⊆ zh_CN.po 键集合」断言即红。异常类型按本仓硬约定拼进实参。
        logger.debug(i18n.tr("关闭失效 AsyncClient 失败: {e}", e=f"{type(e).__name__}: {e}"))


async def _close_all_clients() -> None:
    # 进程退出时释放**本线程本循环**创建的 AsyncClient，避免连接池泄漏。
    #
    # MIN-2217（2026-09-23）：旧实现无条件 `await client.aclose()` 遍历全表，正是
    # 2026-09-04 定稿禁止的形态——缓存里绝大多数条目属于**其它房间线程**的循环，在 atexit
    # （跑在主线程 + 主线程自己那个 asyncio.run 循环）里 await 它们，等于用当前循环去操作
    # 绑定旧循环的 httpcore 传输（触碰旧循环的 call_soon：旧循环已关时直接 RuntimeError，
    # 被下面的 except 吞成一条 debug）。现按 (owner 线程, 创建循环) 双条件过滤，
    # 其余一律只丢引用交 GC。两个条件缺一不可：只判线程会漏掉「同线程但循环已换」
    # （每轮 asyncio.run 一个新循环），此时 await 依旧是在**新**循环上操作**旧**循环的 transport。
    current_loop = asyncio.get_running_loop()
    current_thread = threading.current_thread()
    with _client_cache_lock:
        entries = list(_client_cache.values())
        _client_cache.clear()
    closed = 0
    for client, client_loop, owner in entries:
        if client_loop is not current_loop or owner is not current_thread:
            continue
        try:
            if not client.is_closed:
                await client.aclose()
                closed += 1
        except Exception as e:
            # Windows 下 socket.timeout 等异常 str() 可能为空串，必须带类型名否则日志空白无线索
            logger.debug(i18n.tr("进程退出释放 AsyncClient 失败: {type_name}: {e}", type_name=type(e).__name__, e=e))
    skipped = len(entries) - closed
    if skipped:
        # 只清引用、未真正关闭的条目数：跨线程客户端交由 GC，属预期降级而非泄漏——
        # 不写这一行就会有人把它当「连接池没释放」重新引入跨循环 await。
        logger.debug(i18n.tr("进程退出跳过 {count} 个非本线程/本循环的 AsyncClient（只丢引用）", count=skipped))


def close_all_clients_sync() -> None:
    # 同步安全清理（供 atexit / 信号处理器调用）。本函数**从不**「在当前线程的可用循环上
    # 驱动全部客户端的 aclose」——_close_all_clients 内部只关「本线程 + 本循环」创建的条目
    # （见其注释）。实际落点只有三种：
    #   ① 当前线程有可用且**未运行**的循环 → 用它跑一次 _close_all_clients()，
    #      其中仅主线程自己那批客户端会真正关闭；
    #   ② 循环正在运行（信号在事件循环线程中触发）→ 无法再 run_until_complete，只清引用；
    #   ③ 当前线程没有循环 / 循环已关闭 / 上面任何一步抛错 → 同样只清引用。
    # ②③ 与「其它房间的条目」一样交由 GC 兜底（httpx.AsyncClient 析构会尝试关底层传输）。
    with _client_cache_lock:
        if not _client_cache:
            return
    try:
        # Python 3.14 起 asyncio.get_event_loop() 不再隐式创建事件循环：当前线程无循环时抛
        # RuntimeError；捕获后置 None，与「循环已关闭」一并走下方引用清理兜底（交由 GC 关连接）
        loop: asyncio.AbstractEventLoop | None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None
        if loop is None or loop.is_closed():
            raise RuntimeError("loop closed")
        if loop.is_running():
            # 信号/atexit 钩子在事件循环线程中触发时无法再 run_until_complete，
            # 仅清理缓存引用，让循环关闭时由 AsyncClient.__del__ 兜底关闭
            with _client_cache_lock:
                _client_cache.clear()
            return
        loop.run_until_complete(_close_all_clients())
    except Exception as e:
        logger.debug(i18n.tr("close_all_clients_sync 回退到引用清理: {e}", e=e))
        with _client_cache_lock:
            _client_cache.clear()


def _failure_result(
    redirect_url: bool, return_cookies: bool, include_cookies: bool
) -> str | dict[str, str] | tuple[str, dict[str, str]]:
    # 失败时的返回契约（三处失败出口共用，写第二遍迟早分叉）：
    #   redirect_url / 默认文本 -> 空字符串（调用方据此判定未取到 URL / 走各自异常分支）
    #   return_cookies          -> 空 dict 或 ("", {})（调用方据此判定登录/取 cookie 失败）
    # 类型契约必须「与成功路径同形」，否则调用方解包时抛 ValueError 又被自己的兜底装饰器
    # 二次吞掉，根因彻底丢失（见 AGENTS「平台解析函数的返回契约必须匹配兜底装饰器」）。
    if redirect_url:
        return ""
    if return_cookies:
        return ("", cast(dict[str, str], {})) if include_cookies else cast(dict[str, str], {})
    return ""


# ── MIN-2216（async 侧）：可选依赖缺失不得伪装成「空响应 = 疑似风控」 ────────────
# httpx 在**构造** AsyncClient 时就为缺依赖抛异常（实测 httpx 0.28.1）：
#   http2=True 缺 h2      -> ImportError("Using http2=True, but the 'h2' package is not installed…")
#   proxy=socks*://… 缺 socksio -> ImportError("Using SOCKS proxy, but the 'socksio' package is not installed…")
#   旧版 httpx 的 h2 检查抛 RuntimeError（同样在 AsyncClient.__init__）
# 该异常原先落进 async_req 的通用 except → logger.debug + 返回 ""，而调用方（spider 各平台）
# 把「HTTP 200 + 空响应体」判成风控，于是触发无意义的 HTML 兜底与整轮重试风暴
# （本机实测：摘掉 h2 后抖音解析返回空串，日志里只有一条 debug）。这类「缺包」是**配置/环境级**
# 故障，必须 warning 级 + 给出安装命令，且按模块名去重（80+ 房间 × 每轮一条会把真线索淹掉，
# 与 spider 侧「未开播刻意静默」同一考量）。
_MISSING_PACKAGE_PATTERN = re.compile(r"the '([\w.\-]+)' package")
# warn-once 登记表：set.add 在 GIL 下原子，跨线程竞态最坏是同一模块多打一条 warning，
# 不值得为它加锁（加锁反而把这条热路径挂到 _client_cache_lock 之外的另一把跨线程锁上）。
_dep_warned: set[str] = set()


def _missing_dependency_name(err: BaseException) -> str:
    # 取「缺的是哪个包」：ModuleNotFoundError 自带 .name；httpx 主动抛的 ImportError/
    # RuntimeError 没有 .name，只能从其固定文案里抠（"the 'h2' package"）。
    name = getattr(err, "name", None)
    if isinstance(name, str) and name:
        return name
    match = _MISSING_PACKAGE_PATTERN.search(str(err))
    return match.group(1) if match else ""


def _install_hint(module: str) -> str:
    # httpx 的两个可选 extra 名与包名不同（h2 → httpx[http2]、socksio → httpx[socks]）；
    # 直接 `pip install h2` 也能用，但按 httpx 自己的建议给 extra 更不容易装错版本。
    extra = {"h2": "http2", "socksio": "socks"}.get(module)
    return f"httpx[{extra}]" if extra else (module or "httpx[http2,socks]")


def _log_dependency_missing(err: BaseException, url: str) -> None:
    module = _missing_dependency_name(err)
    scope = module or type(err).__name__
    masked_url = utils.mask_credentials(url)
    if scope in _dep_warned:
        # 已就同一模块告警过：降级 debug，保留线索但不刷屏
        logger.debug(
            i18n.tr(
                "async_req 可选依赖仍缺失（已告警过）: {masked_url} - {type_name}: {e} - 缺失模块 {module}",
                masked_url=masked_url,
                type_name=type(err).__name__,
                e=utils.mask_credentials(str(err)),
                module=module,
            )
        )
        return
    _dep_warned.add(scope)
    logger.warning(
        i18n.tr(
            "async_req 缺少可选依赖，请求根本没有发出（本轮按空响应返回，非风控）: {masked_url} - {type_name}: {e}"
            " - 缺失模块 {module}，请执行 pip install {install}",
            masked_url=masked_url,
            type_name=type(err).__name__,
            e=utils.mask_credentials(str(err)),
            module=module,
            install=_install_hint(module),
        )
    )


async def async_req(
    url: str,
    proxy_addr: OptionalStr = None,
    headers: OptionalDict = None,
    data: Mapping[str, object] | str | bytes | bytearray | memoryview | None = None,
    json_data: Mapping[str, object] | Sequence[object] | None = None,
    timeout: int = 20,
    redirect_url: bool = False,
    return_cookies: bool = False,
    include_cookies: bool = False,
    abroad: bool = False,
    content_encoding: str = "utf-8",
    verify: bool | None = None,
    http2: bool = True,
) -> str | dict[str, str] | tuple[str, dict[str, str]]:
    # 异步 HTTP 请求：支持 GET/POST、代理、Cookie。abroad / content_encoding 仅为与 sync_req
    # 保持签名兼容，异步实现无需显式使用。
    _ = (abroad, content_encoding)
    if headers is None:
        headers = {}
    # 2026-09-12 审查 6.3：请求入口接入 scheme 白名单（SSRF 防线接线）。is_safe_http_url 先前
    # 定义在 spider.py 时因循环依赖无法在此引用，导致这条防线零生产调用；上移到 utils 后
    # 在此统一拦截 file:// / gopher:// 等协议。
    if not utils.is_safe_http_url(url):
        logger.warning(
            i18n.tr(
                "async_req 拒绝非白名单协议的请求: {masked_url}",
                masked_url=utils.mask_credentials(url),
            )
        )
        return _failure_result(redirect_url, return_cookies, include_cookies)
    # MIN-2218：content= 与 json= 同传在 httpx 0.28.1 下**不报错**——`Request.__init__` 里
    # content 优先，json 被静默丢弃（实测 body == 传入的 bytes，json 完全没参与）。调用方以为
    # 发了 JSON、服务端收到的是裸体，只会看到「返回空/解析失败」，与本仓反复强调的
    # 「静默降级比报错更难排查」同型。现显式拒绝：这是编程错误而非网络故障，故**故意不进**
    # except 的「返回空串」契约——让它冒到调用方，用例与人工跑都能立刻看到
    # （当前全仓无同传调用点，属 latent 防线）。
    if data is not None and json_data is not None:
        raise ValueError(
            i18n.tr(
                "async_req 不接受同时传 data 与 json_data: {masked_url}",
                masked_url=utils.mask_credentials(url),
            )
        )
    # 未显式指定时使用全局 SSL 验证开关
    if verify is None:
        verify = config.ssl_verify
    try:
        proxy_addr = utils.handle_proxy_addr(proxy_addr)
        # MID-22（2026-09-20）：return_cookies=True 的调用点全部是「登录 / 取 Cookie / 刷新
        # token」（src/cookie_cache.py 与 spider.py 的 4 处），而共享缓存客户端带持久 cookie jar
        # ——httpx 会把响应的 Set-Cookie 存进客户端并在后续同域请求自动附上。该缓存按
        # (proxy, verify, http2, loop) 共享，意味着 A 账号登录拿到的 session cookie 会被 B 账号/
        # 其它房间的请求自动带上（登录串号 + 风控指纹异常）。故此类调用**不走缓存**：每次自建
        # 一支一次性客户端、用完即在当前循环内关闭（独占客户端的循环归属明确，aclose 安全，
        # 不违反 2026-09-04 的跨循环决策）。普通文本请求仍复用缓存客户端：其 cookie 由调用方经
        # headers 逐请求显式下发（见 AGENTS「客户端跨候选复用时业务头必须逐请求下发」）。
        # 代价：登录类请求每轮多一次 TCP+TLS 握手——低频路径（cookie 缓存命中即跳过），换取账号隔离。
        client, owned_client = await _acquire_client(proxy_addr, timeout, verify, http2, bool(return_cookies))
        # 用 is not None 判定而非真值判定：json_data={} / data="" / b"" 表示「显式传了空体」，
        # 真值判断会让它们静默退化成 GET——服务端收到空 GET，调用方只看到空响应。
        try:
            # MIN-2218：三条 POST 分支一律 follow_redirects=True，与下方 GET 分支对齐。旧写法三条
            # 都不带该参数，而异步 POST 的调用点（Twitch GQL / popkontv / acfun 签名等，见
            # spider.py）拿到的是 **301/302 的重定向页**而不是业务响应，且本函数不判状态码就返回
            # response.text → 上层 _loads_dict 解出 {} → 归因成「空响应 / 疑似风控」，真实成因
            # （站点把接口整体挪到 https 或加了斜杠）被完全掩盖。选「跟随」而非「3xx 直接返回空串
            # + 告警」：这些接口是同源业务 API，重定向是运维侧的 URL 迁移而非攻击面，而 GET 分支
            # 早已跟随，两半不一致本身就是坑。
            # 语义边界（别误以为「跟随后 POST 一定还是 POST」）：httpx 与 requests 同款——
            # 301/302/303 会把 POST 改成 GET 并丢请求体，只有 307/308 保方法保体；真依赖
            # 301 后继续 POST 的接口在本仓调用点不存在。
            if data is not None or json_data is not None:
                if isinstance(data, (bytes, bytearray, memoryview)):
                    # bytearray/memoryview 转 bytes（已是 bytes 时直接使用，避免无谓拷贝）
                    content_data = data if isinstance(data, bytes) else bytes(data)
                    response = await client.post(
                        url,
                        content=content_data,
                        json=json_data,
                        headers=headers,
                        timeout=timeout,
                        follow_redirects=True,
                    )
                elif isinstance(data, str):
                    response = await client.post(
                        url,
                        content=data,
                        json=json_data,
                        headers=headers,
                        timeout=timeout,
                        follow_redirects=True,
                    )
                else:
                    # data 是 dict（表单）或 None
                    response = await client.post(
                        url,
                        data=data,
                        json=json_data,
                        headers=headers,
                        timeout=timeout,
                        follow_redirects=True,
                    )
            else:
                response = await client.get(url, headers=headers, follow_redirects=True, timeout=timeout)

            # 结果分支必须在 try 块内访问 response——异常时 response 尚未定义
            if redirect_url:
                return str(response.url)
            elif return_cookies:
                cookies_dict = {name: value for name, value in response.cookies.items()}
                return (response.text, cookies_dict) if include_cookies else cookies_dict
            else:
                resp_str = response.text
        finally:
            if owned_client:
                await _release_client(client)
    except (ImportError, ModuleNotFoundError, RuntimeError) as e:
        # MIN-2216（async 侧）：依赖缺失是**环境级**故障，原先与网络异常同一条 debug 出口，
        # 表现为「200 + 空响应体 = 疑似风控」+ 无意义的 HTML 兜底与重试风暴。三类异常都来自
        # httpx 构造客户端时的可选依赖检查（http2 缺 h2 在 0.28.1 抛 ImportError、更早版本抛
        # RuntimeError；显式 socks 代理缺 socksio 抛 ImportError）；ModuleNotFoundError 是
        # ImportError 的子类，列出来是为了让「缺包」这一类在代码里显式成立，不必读者再查继承关系。
        # 返回契约不变（仍走 _failure_result 的空值）：调用方全部按「本轮没拿到数据」处理，
        # 改成抛异常会击穿 50+ 平台函数的兜底装饰器语义。
        _log_dependency_missing(e, url)
        return _failure_result(redirect_url, return_cookies, include_cookies)
    except Exception as e:
        # 异常时按调用方期望的返回契约回退（统一走 _failure_result，见其注释）。
        # WD-01：url 与异常文本 e **两者**都必须脱敏——httpx/urllib3 的异常字符串**必然内嵌完整
        # 请求 URL**（如 "Max retries exceeded with url: /api/x?signature=..."），代理分支还会带上
        # user:pass@host；原实现只包了 url 形参，等于把同一份凭据换个字段写进日志
        # （logs 轮转保留多份＝凭据长期落盘）。
        logger.debug(
            i18n.tr(
                "async_req 请求失败: {masked_url} - {type_name}: {e}",
                masked_url=utils.mask_credentials(url),
                type_name=type(e).__name__,
                e=utils.mask_credentials(str(e)),
            )
        )
        return _failure_result(redirect_url, return_cookies, include_cookies)

    return resp_str


def _internal_stream_target_reason(url: str, proxy_addr: OptionalStr) -> str | None:
    # MIN-2219（2026-09-23）：本函数的 url 是**从平台响应里正则/JSON 解出来的流地址**，属外部
    # 可控输入。原先只过 scheme 白名单，于是一份被攻陷或被 MITM 的响应写下
    # "http://127.0.0.1:6379/" / "http://169.254.169.254/latest/meta-data/" 就能让本进程去发
    # HEAD（失败再 Range-GET），并把 status_code + content-type 回显进 debug 日志——那是一个
    # 稳定的「内网端口开放情况观测口」。默认拒绝范围：回环 / 私网 / 链路本地（含 169.254 云
    # 元数据）/ 未指定 / 组播 / 保留 / CGNAT 100.64.0.0/10 / 内部用途域名（metadata、
    # *.internal、*.local …）。
    # 判定**复用仓内既有口径** web_config._host_internal_reason（推送 / SMTP / 代理 / 房间地址
    # 四条写入路径都在用它）——两处口径不一致本身就是缺口，故本函数一律不自己写规则。
    #
    # 唯一与写入侧的差异：**走代理的请求对域名不做 DNS 判定**。_host_internal_reason 对非字面量
    # 主机名会先解析再定罪，这对「用户往配置里写地址」是对的（写入即定罪），但对探针不成立：
    #   ① 有代理时真正建立连接的是代理侧，本机解析结果与落地目标无关，按本机结果拒绝会误杀
    #      「境外域名本机 DNS 被污染/查不到、代理却能解析」的合法流（正是 AGENTS
    #      「探针误杀可用源」那条反复强调的形态）；
    #   ② 无代理时本机解析 = 即将连接的地址，判定有效，且多一次 getaddrinfo 可接受（探针本身
    #      按 host 限流、每候选每轮一次，而 httpx 随后还要再解析一次）。
    # IP 字面量（含 [::1] / 0x7f.0.0.1 等缩写形态）两种情况下都判——它不依赖解析，且经代理时
    # http 代理按绝对 URI 转发，回环/元数据仍然可达。
    #
    # 打桩口径：用例经 monkeypatch src.web_config._resolve_host_ips 这个既有 DNS seam 隔离真实
    # 解析（见 tests/test_regression_2026_09_22_net.py 的 _stub_dns_public）。
    # 这里**函数内 import** 而非模块级：src/stream_select.py 有模块级 `import main`、main.py 又
    # `from src.stream_select import ...`，本仓已存在这条导入环；给 async_http 加一条模块级出边
    # 会改变各模块的初始化顺序（实测足以让 `from .stream_select import MOBILE_UA` 撞上半成品
    # 模块）。本函数是探针路径、每次选源才走几次，多一次已缓存的 sys.modules 查找没有成本。
    from . import web_config

    host = (urlparse(url).hostname or "").lower()
    if not host:
        return "流地址缺少主机名"
    if proxy_addr and web_config._parse_ip_literal(host) is None:
        return None
    return web_config._host_internal_reason(host)


async def get_response_status(
    url: str,
    *,
    proxy: OptionalStr = None,
    proxy_addr: OptionalStr = None,
    headers: OptionalDict = None,
    timeout: int = 10,
    verify: bool | None = None,
    http2: bool = False,
    abroad: bool = False,
    platform: str = "",
) -> bool:
    # 流地址可达性校验（HEAD，失败再 Range-GET 复核）。未显式指定 verify 时用**拉流侧按平台的**
    # SSL 策略（见下方 MID-26 注释）。
    # MID-26（2026-09-20）：全部关键字传参、与流层调用方一致。proxy_addr 是迁移期兼容别名
    # （src/stream.py 的旧调用名），两者等价、同传时 proxy 优先；headers / http2 / abroad 保留原有形态。
    # UA 由调用方经 headers 下发（AGENTS：同步/异步校验器的 proxy / verify / UA 三者一致），本函数不
    # 另立一份 UA 以免指纹分叉——唯一事实源为 src/stream_select.py 的 get_record_user_agent(platform) or MOBILE_UA。
    _ = abroad
    effective_proxy = proxy if proxy is not None else proxy_addr
    # 同 async_req：请求入口接入 scheme 白名单（见上方说明）
    if not utils.is_safe_http_url(url):
        logger.warning(i18n.tr("get_response_status 拒绝非白名单协议的请求: {url}", url=utils.mask_credentials(url)))
        return False
    # MIN-2219：代理地址先归一再判目标——_internal_stream_target_reason 需要知道「这次探测
    # 到底是不是经代理出站」，才能决定要不要按本机 DNS 结果定罪（见其注释）。
    proxy_addr = utils.handle_proxy_addr(effective_proxy)
    internal_reason = _internal_stream_target_reason(url, proxy_addr)
    if internal_reason is not None:
        # 这是**安全判定**而非可达性判定，故 warning 级：一条被塞进响应的内网地址必须留下
        # 线索，不能被当成「这个 CDN 节点不通」而降级到相邻画质。URL 脱敏同 WD-01。
        logger.warning(
            i18n.tr(
                "get_response_status 拒绝内网/保留目标（疑似被篡改的流地址）: {masked_url} - {reason}",
                masked_url=utils.mask_credentials(url),
                reason=internal_reason,
            )
        )
        return False
    if verify is None:
        # MID-26 修复：本函数的入参是**流地址**（src/stream.py 的 HLS 候选校验），原先回落到
        # 控制面 config.ssl_verify（生产恒 True、严格校验），而 ffmpeg 的 -tls_verify 与
        # stream_select 的同步校验器都按 get_effective_ssl_verify(platform) 取值。于是
        # 「https 录制模式（拉流侧已全局豁免）」或「平台命中禁用SSL证书验证名单（虎牙 TX CDN
        # 主机名不匹配正是该名单的立论）」时，探针必然 SSL 报错 → 判不可达 → 上层降到相邻画质，
        # 而 ffmpeg 其实录得上原画（校验假红）。现与本仓另两个校验口同源；verify 显式传值仍以
        # 调用方为准（单次覆盖语义）。
        verify = config.get_effective_ssl_verify(platform)
    try:
        client: httpx.AsyncClient = await _get_client(proxy_addr, timeout, verify, http2)
        response = await client.head(url, headers=headers, follow_redirects=True, timeout=timeout)
        if response.status_code == 200:
            return True
        # 部分 CDN（如抖音 m3u8）对 HEAD 返回非 200（含 403/404），但 GET 可正常拉流，故对 m3u8
        # 源再做一次 Range-GET 轻量可达性探测，避免误判不可达而降级画质。
        # 注意：只覆盖 400/401/403/405 会漏掉 404（部分 CDN 对 HEAD 一律回 404），
        # 因此 HEAD 非 2xx 的 m3u8 源一律进入探测。
        # 2026-09-12 审查（低危）：扩展名按小写判定——大写 .M3U8 的源会漏掉 Range-GET 探测，
        # 被 HEAD 的 4xx 直接判成不可达，导致明明可播的源被降级/跳过。
        if ".m3u8" in url.lower() and response.status_code != 200:
            probe = await client.get(
                url, headers={**(headers or {}), "Range": "bytes=0-0"}, follow_redirects=True, timeout=timeout
            )
            if probe.status_code in (200, 206):
                return True
            # WD-01：此处 url 是带 codec/签名/鉴权的真实 m3u8/flv 直链，必须脱敏
            logger.debug(
                i18n.tr(
                    "get_response_status 校验未通过: {url} - HEAD={status_code}, Range-GET={status_code_2}, content-type={content_type}",
                    url=utils.mask_credentials(url),
                    status_code=response.status_code,
                    status_code_2=probe.status_code,
                    content_type=probe.headers.get("content-type", ""),
                )
            )
            return False
        logger.debug(
            i18n.tr(
                "get_response_status 校验未通过: {url} - status_code={status_code}, content-type={content_type}",
                url=utils.mask_credentials(url),
                status_code=response.status_code,
                content_type=response.headers.get("content-type", ""),
            )
        )
        return False
    except Exception as e:
        # 注意：Windows 下 socket.timeout 的 str() 为空，仅打印 {e} 会得到空白日志，
        # 必须带上 URL 与异常类型，否则无法定位是超时、连接被拒还是证书问题。
        # WD-01：URL 与异常文本统一脱敏（异常文本常内嵌完整直链）。
        logger.debug(
            i18n.tr(
                "get_response_status 校验失败（判定为不可达）: {url} - {type_name}: {e}",
                url=utils.mask_credentials(url),
                type_name=type(e).__name__,
                e=utils.mask_credentials(str(e)),
            )
        )
    return False
