# -*- coding: utf-8 -*-
# 同步 HTTP 客户端：urllib 直连 / requests 代理两条出站路径，含 ssl_verify 单次覆盖与响应体上限
import atexit
import gzip
import http.client
import io
import json
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request
import weakref
from collections.abc import Mapping, Sequence
from typing import TypeAlias, cast

import requests

import i18n

# JSON 可序列化类型别名：对齐 requests._types.JsonType 的结构（该别名在较新版 requests 中
# 定义于 TYPE_CHECKING 块内、运行时不可导入，故本地显式重定义，同时满足运行时注解求值
# 与 requests.post(json=...) 的参数类型校验两端）。
JsonType: TypeAlias = None | bool | int | float | str | Sequence["JsonType"] | Mapping[str, "JsonType"]

from . import http_config as config
from . import utils
from .logger import logger

# 禁用代理的处理器（本地请求不使用代理）
no_proxy_handler = urllib.request.ProxyHandler({})

# 预构建 opener：仅禁用代理，保留默认证书验证（ssl_verify=True 时使用）
_opener_secure = urllib.request.build_opener(no_proxy_handler)

# ── 安全边界说明（2026-09-12 审查 6.7 / 2026-09-14 F-12 落地，行为向后兼容）──
# 「不校验证书」的 SSLContext 与 opener 一律**按需惰性构造**，禁止改回模块级常驻：import 期就
# 存在一个不校验的 SSLContext，等于给整个进程开了静默的全局降级面——任何误用（含第三方库走默认
# 上下文的分支）都是一次不告而变的跳过校验。惰性化后只有「本次请求要求跳过校验」的分支才创建它。
# 保留按需降级能力的原因：个别平台 CDN 存在证书链/主机名不匹配（虎牙 TX CDN 等），用户可能需要为
# 解析请求放行；同时 ssl_verify 单次覆盖参数让凭据类调用点（未来新增的登录 / token 刷新等）可以显式
# 强制校验，不被全局开关拖下水。CERT_NONE 路径在生产中同样不可达（`http_config.ssl_verify` 无任何
# set_ssl_verify(False) 调用点），风险是**潜在误用面**而非现实暴露面；惰性构造的防线仍保留。
#
# 调用面（如实写，不编造）：**本模块当前没有任何生产 importer**，去留待维护者决定。取证命令：
#   grep -rn "sync_http\|sync_req(" --include=*.py src/ main.py gui.py web.py msg_push.py i18n.py scripts/
# 实测只命中①本文件自身、②同样零生产调用点的 `src/weverse_auth.py`（2026-09-23 已删除）、③`tests/`；
# `src/spider.py` 导入的是 `from .async_http import async_req`（httpx 异步面），登录、消息推送
# （msg_push.py 自建 requests/urllib 调用）、Web 面板也不经本模块。
#   [历史注] 2026-09-23 之前本段写作「sync_req 调用点全部位于 src/spider.py」，已被证伪（SEV-2226）。
# 本体仍保留：它承载别处没有的两点——F-12 的「同步/异步两条出站路径同时透传 ssl_verify 单次覆盖」
# 不变量，以及 `tests/test_sync_http.py` 对该不变量的回归锁。若将来确认不再接线，应连同 F-12 的双侧
# 陈述一起清理，而不是留成第二条无人执行、却会被文档当作事实源的「同名不同实现」。
_ssl_context_insecure: ssl.SSLContext | None = None
_opener_insecure: urllib.request.OpenerDirector | None = None


def _get_insecure_context() -> ssl.SSLContext:
    # 惰性构造 CERT_NONE 上下文（仅在确实需要跳过校验时被调用）
    global _ssl_context_insecure
    if _ssl_context_insecure is None:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        _ssl_context_insecure = ctx
    return _ssl_context_insecure


def _get_insecure_opener() -> urllib.request.OpenerDirector:
    # 惰性构造「禁用代理 + 禁用证书验证」的 opener（仅在确实需要时被调用）
    global _opener_insecure
    if _opener_insecure is None:
        _opener_insecure = urllib.request.build_opener(
            no_proxy_handler, urllib.request.HTTPSHandler(context=_get_insecure_context())
        )
    return _opener_insecure


def _resolve_ssl_verify(override: bool | None) -> bool:
    # 单次请求的证书校验裁决：显式 override 优先（凭据类调用点可强制校验），
    # 未指定时跟随控制面全局开关（现状语义，向后兼容）。
    return config.ssl_verify if override is None else override


def _get_opener(ssl_verify: bool | None = None) -> urllib.request.OpenerDirector:
    # 按「本次请求」的 SSL 验证裁决选择本地请求 opener。
    # ssl_verify=None 表示跟随全局开关（历史行为）；显式传值时以该次调用为准。
    return _opener_secure if _resolve_ssl_verify(ssl_verify) else _get_insecure_opener()


_thread_local = threading.local()
# 进程内全部线程 Session 的弱引用登记：线程销毁后条目自动回收，不阻止 GC；
# 进程退出时（atexit）据此统一优雅关闭仍存活的连接池（80+ 房间长跑场景）
_all_sessions: "weakref.WeakSet[requests.Session]" = weakref.WeakSet()
_all_sessions_lock = threading.Lock()


def _session() -> requests.Session:
    # 线程内复用的 requests.Session。requests 的模块级 get/post 每次都新建一个 Session 并在
    # 退出时销毁，底层 urllib3 连接池随之丢弃——每次请求都要重做 TCP（HTTPS 还要重握手）：
    # 微基准实测单次 11.9ms vs 复用的 1.47ms（约 8×），200 次请求产生 200 条连接 vs 1 条。
    # 该读数取自**同步出站层被接线**的前提下；本模块当前无生产 importer（见模块头「调用面」），
    # 故只保留结论本身，不声称收益已落地。
    # Session 本身不是线程安全的，故用 thread-local 每线程一份：既避免跨线程共享（会互相踩
    # 连接状态），又能让长期存活的房间线程持续复用同一连接池。
    # 测试约定：打桩目标是 `src.sync_http._session`，**不是** `src.sync_http.requests`
    # ——改回后者会让用例绕过真实复用路径、失防（tests/test_sync_http.py 即按此写）。
    session: requests.Session | None = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        _thread_local.session = session
        with _all_sessions_lock:
            _all_sessions.add(session)
    return session


def session() -> requests.Session:
    # 线程级 Session 的公开出口（MIN-08 新增）：供「必须拿到状态码 / 响应头、因而无法走
    # sync_req」的调用点复用同一份连接池。sync_req 的返回契约是「响应文本，失败一律空串」，
    # 非 200 与网络异常都塌成同一个 ""，登录/令牌刷新类端点若走它会丢掉 MI-22 刚补的
    # status_code 诊断线索——这类调用点必须用本函数，而不是绕过 sync_http 直接 requests.post
    # （后者丢掉线程级 Session 复用、代理与 SSL 策略接线）。
    # 打桩时 patch 的仍是 _session（与本仓测试约定一致）。
    return _session()


def close_session() -> None:
    # 关闭当前线程的 Session 并释放其连接池（房间线程退出路径可显式调用）。
    # 关闭后下次 _session() 会重建，不影响后续请求
    session: requests.Session | None = getattr(_thread_local, "session", None)
    if session is not None:
        _thread_local.session = None
        try:
            session.close()
        except Exception:
            pass


def close_all_sessions() -> None:
    # 进程退出时统一关闭所有线程（含主线程）的 Session 连接池，由 atexit 调用；
    # WeakSet 快照迭代受 _IterationGuard 保护，期间条目被 GC 移除也安全
    with _all_sessions_lock:
        sessions = list(_all_sessions)
        _all_sessions.clear()
    for session in sessions:
        try:
            session.close()
        except Exception:
            pass


atexit.register(close_all_sessions)


OptionalStr = str | None
OptionalDict = dict[str, str] | None

# ─── 响应体上限（SEV-2226 收尾，2026-09-23）：读侧与解压侧各一道，缺一不可 ───────
# 为什么必须有上限：无参 `resp.read()` = 「对端给多少就申请多少」，而 gzip 压缩比可达 1000:1 以上
# ——被 MITM / 劫持的响应（或恶意平台）只要回几十 KB 的 gzip，就能让房间线程在解压时申请数 GB 内存；
# 本进程 OOM 不是「这一房间失败」而是**整个录制进程被带走**（80+ 房间与 Web 面板同进程）。且原
# `except Exception` 只兜网络/解析异常，MemoryError 属 BaseException、连兜底都兜不住。
# 为什么是**两道**而不是一道：只限压缩体会漏掉主要形态（压缩 30KB → 解压 30MB）；只限解压输出又会
# 先在 `_resp.read()` 上被无上限的压缩体打爆。故 ① 压缩态按块读、累计超过 _MAX_RESPONSE_BYTES 立即
# 拒绝（顺带挡住「无 Content-Length 的慢速大响应」这一非炸弹形态）；② 解压侧用 GzipFile 分块读、
# 累计超过 _MAX_DECOMPRESSED_BYTES 立即拒绝——峰值内存因此钉在「压缩上限 + 一个块」，而非解压后全量。
# 取值口径：平台页面 / JSON / m3u8 播放列表的真实量级在几十 KB ~ 1MB，两个上限都比最宽的正常响应高
# 一个数量级以上，宁可放宽也不误杀（误杀 = 该平台整轮漏录，代价高于内存风险）。超限后抛 ValueError →
# 由 sync_req 的既有失败分支记一条脱敏 error 日志并返回空串，调用方按「空响应 = 未开播/疑似风控」处理
# （与 async_req 的失败语义一致，不新增契约）。
_MAX_RESPONSE_BYTES = 8 * 1024 * 1024  # 压缩/原始响应体的读入上限
_MAX_DECOMPRESSED_BYTES = 32 * 1024 * 1024  # gzip 解压后的产出上限
_READ_CHUNK_BYTES = 64 * 1024


def _read_capped(resp: http.client.HTTPResponse, limit: int, kind: str) -> bytes:
    # 单次带 amt 的 read：HTTPResponse.read(amt) 至多返回 amt 字节，故「读进内存的量」
    # 天然被钉在 limit+1 之内；读完仍满额即判超限并拒绝该响应。
    # **刻意不写成 while 累加循环**：本仓 tests/test_sync_http.py 的响应替身是 MagicMock，
    # 其 read() 无论传什么参数都返回同一个非空串——「读到空块才退出」的循环在测试里会变成
    # 死循环（且全量 pytest 表现为零输出挂死）。单次带 amt 的读法对该替身同样成立。
    data = resp.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"响应体超过{kind}上限 {limit} 字节，已拒绝该响应")
    return data


def _gunzip_capped(data: bytes, limit: int) -> bytes:
    # 分块解压：GzipFile 每次 read() 只解压够数的量，因此峰值内存受 limit 约束；
    # 用 gzip.decompress(data) 做不到这一点——它一次性把整棵树展开成完整字节。
    # 这里可以安全地循环：底层是 io.BytesIO，EOF 必然返回 b''（与上面的替身形态无关）。
    handle = gzip.GzipFile(fileobj=io.BytesIO(data), mode="rb")
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = handle.read(_READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise ValueError(f"gzip 解压结果超过上限 {limit} 字节（解压炸弹形态），已拒绝该响应")
        chunks.append(chunk)
    return b"".join(chunks)


def sync_req(
    url: str,
    proxy_addr: OptionalStr = None,
    headers: OptionalDict = None,
    data: Mapping[str, object] | str | bytes | None = None,
    json_data: JsonType = None,
    timeout: int = 20,
    redirect_url: bool = False,
    abroad: bool = False,
    content_encoding: str = "utf-8",
    ssl_verify: bool | None = None,
) -> str:
    # 同步 HTTP 请求：支持 GET/POST、代理、重定向、gzip 解压。失败一律返回空串。
    # ssl_verify：本次请求的证书校验覆盖（None = 跟随控制面全局开关）。
    # 凭据类调用点（登录 / token 刷新等）应显式传 True，避免被全局降级波及；
    # 该覆盖必须同时透传 urllib 与 requests(代理) 两条路径（F-12，曾只改一条即出现口径分叉）。
    if headers is None:
        headers = {}
    # MID-27：代理地址归一（裸 ip:port 补 http:// 前缀）原先只存在于异步侧
    # （async_http.async_req / get_response_status 入口都调 handle_proxy_addr），
    # 而配置项「代理地址」由 read_config_value 原样读入、用户普遍写成 127.0.0.1:7890。
    # 于是同一份配置下 async 解析正常、本函数的调用点（当时 src/ 里约 125 处）全部把裸值
    # 交给 requests → InvalidSchema/InvalidURL 被外层 except 吞成空串，形态是「开了代理后
    # 某平台解析全失败且表现为空响应」——本仓最难归因的一类失败。
    # 两侧现共用同一 helper、同一语义。（调用点计数为 MID-27 当时快照，本模块现已无生产 importer。）
    proxy_addr = utils.handle_proxy_addr(proxy_addr)
    verify = _resolve_ssl_verify(ssl_verify)
    resp_str = ""
    try:
        if proxy_addr:
            # 使用代理的请求
            proxies = {"http": proxy_addr, "https": proxy_addr}
            if data is not None or json_data is not None:
                # POST 请求（带代理）
                response = _session().post(
                    url,
                    data=data,
                    json=json_data,
                    headers=headers,
                    proxies=proxies,
                    timeout=timeout,
                    verify=verify,
                )
            else:
                # GET 请求（带代理）
                response = _session().get(url, headers=headers, proxies=proxies, timeout=timeout, verify=verify)
            if redirect_url:
                return response.url
            # 已知残留缺口（如实写明，不假装闭合）：本分支的 `response.text` 由 requests/urllib3 自行
            # 解码 gzip，**不受**上面两个上限保护（上限只对无代理的 urllib 路径生效）。补法要么改成
            # stream=True + 手工分块（会让失败语义从「空串」变成「半途截断」，且打死
            # tests/test_sync_http.py 对 Session 替身的既有契约），要么给 Session 挂 HTTPAdapter/max_size
            # 钩子（requests 无此原生能力）。2026-09-23 那轮只收口了无代理 urllib 路径，代理侧同一风险随
            # 「无生产 importer」一并交回维护者决策——不在无人调用的路径上顺手大改。
            resp_str = response.text
        else:
            # 2026-09-12 审查 6.3：请求体的判定由真值（`if data and ...`）改为 `is not None`。
            # 原写法与上方代理分支（`data is not None or json_data is not None`）语义相反——
            # data="" / json_data={} 时配代理走 POST、不配代理静默退化成 GET，调用方只看到
            # 空响应且无法归因（async_req 侧早于此处统一为 is not None）。
            if data is not None and not isinstance(data, bytes):
                if isinstance(data, dict):
                    data = urllib.parse.urlencode(data).encode(content_encoding)
                else:
                    data = str(data).encode(content_encoding)
            if json_data is not None and isinstance(json_data, (dict, list)):
                data = json.dumps(json_data).encode(content_encoding)

            req = urllib.request.Request(url, data=cast("bytes | None", data), headers=headers)

            try:
                if abroad:
                    # 海外请求：仅当（本次裁决为）不校验证书时才带上 CERT_NONE 上下文，
                    # 直连路径不经过 opener，故必须在此处单独透传同一份裁决
                    _resp = cast(
                        http.client.HTTPResponse,
                        urllib.request.urlopen(
                            req, timeout=timeout, context=None if verify else _get_insecure_context()
                        ),
                    )
                else:
                    # 本地请求：opener 按「本次调用」的 ssl_verify 覆盖选择（无代理）
                    _resp = cast(http.client.HTTPResponse, _get_opener(ssl_verify).open(req, timeout=timeout))
                try:
                    if redirect_url:
                        return _resp.url

                    # 响应编码与 gzip 解压：两个上限（读入 / 解压产出）都必需，
                    # 理由与取值口径见 _MAX_RESPONSE_BYTES 上方的整段说明——无上限时
                    # 一个被 MITM 的小响应就足以把整个录制进程打成 OOM。
                    resp_encoding = _resp.headers.get("Content-Encoding")
                    if resp_encoding == "gzip":
                        resp_bytes = _gunzip_capped(
                            _read_capped(_resp, _MAX_RESPONSE_BYTES, "压缩响应体"), _MAX_DECOMPRESSED_BYTES
                        )
                        resp_str = resp_bytes.decode(content_encoding)
                    else:
                        # 未压缩时同一条读入上限即已足够
                        resp_str = _read_capped(_resp, _MAX_RESPONSE_BYTES, "响应体").decode(content_encoding)
                finally:
                    _resp.close()

            except urllib.error.HTTPError as e:
                # 仅 400 例外：部分平台在参数不合规时回 400 且正文含可用信息，原样返回给调用方；
                # 其余状态码继续上抛，交给下面的统一失败分支
                try:
                    if e.code == 400:
                        resp_str = e.read().decode(content_encoding)
                    else:
                        raise
                finally:
                    e.close()
            except urllib.error.URLError as e:
                # WD-01：URLError 的文本内嵌完整请求 URL（含签名/鉴权查询串），必须脱敏
                logger.warning(i18n.tr("URL Error: {e}", e=utils.mask_credentials(str(e))))
                raise
            except Exception as e:
                # 2026-09-12 审查（低危）：异常文本统一经 mask_credentials 脱敏——
                # URLError/OSError 的文本常内嵌完整 URL（含 signature/token 查询串），
                # 直连日志轮转保留多份＝凭据长期落盘（与 async_req 的脱敏口径对齐）。
                logger.error(
                    i18n.tr("An error occurred: {masked}", masked=utils.mask_credentials(f"{type(e).__name__}: {e}"))
                )
                raise

    except Exception as e:
        # 请求失败统一记日志并返回空串：错误文本若伪装成响应体会被上游当有效数据解析。
        # URL 与异常文本同样先脱敏再落日志。
        logger.error(
            i18n.tr(
                "sync_req 请求失败: {masked_url} - {type_name}: {e}",
                masked_url=utils.mask_credentials(url),
                type_name=type(e).__name__,
                e=utils.mask_credentials(str(e)),
            )
        )
        resp_str = ""

    return resp_str
