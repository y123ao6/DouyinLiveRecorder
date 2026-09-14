# -*- coding: utf-8 -*-
import atexit
import gzip
import http.client
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

# 同步 HTTP 客户端模块 - 提供同步 HTTP 请求功能


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

# ── 安全边界说明（2026-09-12 审查 6.7 / 2026-09-14 F-12 落地，行为保持向后兼容）──
# 「不校验证书」的 SSLContext 与 opener 改为**按需惰性构造**，不再在 import 时常驻：
# 模块级常驻 CERT_NONE 上下文意味着「只要 import 本模块，进程里就存在一个不校验的
# SSLContext」，任何误用（含第三方库走默认上下文的分支）都是一次静默的全局降级。
# 惰性化后，只有真正走到「本次请求要求跳过校验」的分支才会创建它。
#
# 调用面核实（2026-09-14，修正 2026-09-12 审查的风险描述）：
# sync_req 的 123 处调用点**全部位于 src/spider.py**（平台解析 / 流地址获取），
# 登录、消息推送（msg_push.py 自建 requests/urllib 调用）、Web 面板均不经本模块；
# 且控制面开关 http_config.ssl_verify 在生产链路中无任何 set_ssl_verify(False)
# 调用点（该开关已从「是否启用https录制」解耦，详见 http_config 注释），恒为 True。
# 因此 CERT_NONE 路径在生产中不可达，风险为**潜在误用面**而非现实暴露面。
#
# 仍保留按需降级能力的原因：个别平台 CDN 存在证书链/主机名不匹配（虎牙 TX CDN 等），
# 用户可能需要为解析请求放行；同时提供 ssl_verify 单次覆盖参数，让凭据类调用点
# （未来新增的登录 / token 刷新等）可以显式强制校验，不被全局开关拖下水。
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
    # 线程内复用的 requests.Session。requests 的模块级 get/post 每次都会新建一个
    # Session 并在退出时销毁，底层 urllib3 连接池随之丢弃——每次请求都要重新建立
    # TCP（HTTPS 还要重新握手），实测单次约 11.9ms vs 复用的 1.5ms、200 次请求产生
    # 200 条连接 vs 1 条。本函数是 sync_req 的必经路径（125 处调用点，位于平台解析
    # 主链路），80+ 房间并发时收益显著。
    # Session 本身不是线程安全的，故用 thread-local 每线程一份：既避免跨线程共享，
    # 又能让同一房间线程（长期存活）持续复用同一连接池。
    session: requests.Session | None = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        _thread_local.session = session
        with _all_sessions_lock:
            _all_sessions.add(session)
    return session


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
    # 同步 HTTP 请求函数，支持 GET/POST、代理、重定向、gzip 解压等功能
    # ssl_verify：本次请求的证书校验覆盖（None=跟随控制面全局开关）。
    # 凭据类调用点（登录 / token 刷新等）应显式传 True，避免被全局降级波及。
    if headers is None:
        headers = {}
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
            resp_str = response.text
        else:
            # 不使用代理的请求
            # 处理请求数据编码
            # 2026-09-12 审查 6.3：判定由真值（`if data and ...`）改 `is not None`。
            # 原写法与上方代理分支（第 124 行 `data is not None or json_data is not None`）
            # 语义相反——data="" / json_data={} 时，配代理走 POST、不配代理静默退化成
            # GET，调用方只看到空响应且无法归因（async_req 侧已于早前统一为 is not None）。
            if data is not None and not isinstance(data, bytes):
                if isinstance(data, dict):
                    # dict 类型转换为 URL 编码
                    data = urllib.parse.urlencode(data).encode(content_encoding)
                else:
                    # 其他类型转换为字符串再编码
                    data = str(data).encode(content_encoding)
            if json_data is not None and isinstance(json_data, (dict, list)):
                # JSON 数据编码
                data = json.dumps(json_data).encode(content_encoding)

            # 创建请求对象
            req = urllib.request.Request(url, data=cast("bytes | None", data), headers=headers)

            try:
                if abroad:
                    # 海外请求：仅在全局禁用证书验证时使用 CERT_NONE 上下文
                    _resp = cast(
                        http.client.HTTPResponse,
                        urllib.request.urlopen(
                            req, timeout=timeout, context=None if verify else _get_insecure_context()
                        ),
                    )
                else:
                    # 本地请求（使用按全局配置选择的 opener）
                    _resp = cast(http.client.HTTPResponse, _get_opener(ssl_verify).open(req, timeout=timeout))
                try:
                    if redirect_url:
                        return _resp.url

                    # 处理响应编码和 gzip 解压
                    resp_encoding = _resp.headers.get("Content-Encoding")
                    if resp_encoding == "gzip":
                        # gzip 解压
                        resp_bytes = gzip.decompress(_resp.read())
                        resp_str = resp_bytes.decode(content_encoding)
                    else:
                        # 普通解码
                        resp_str = _resp.read().decode(content_encoding)
                finally:
                    _resp.close()

            except urllib.error.HTTPError as e:
                # HTTP 错误处理
                try:
                    if e.code == 400:
                        resp_str = e.read().decode(content_encoding)
                    else:
                        raise
                finally:
                    e.close()
            except urllib.error.URLError as e:
                # URL 错误记录日志
                logger.warning(i18n.tr("URL Error: {e}", e=e))
                raise
            except Exception as e:
                # 其他错误记录日志
                # 2026-09-12 审查（低危）：异常文本经 mask_credentials 脱敏——
                # URLError/OSError 的文本常内嵌完整 URL（含 signature/token 查询串），
                # 直连日志轮转保留多份＝凭据长期落盘（与 async_req 的脱敏口径对齐）。
                logger.error(
                    i18n.tr("An error occurred: {masked}", masked=utils.mask_credentials(f"{type(e).__name__}: {e}"))
                )
                raise

    except Exception as e:
        # 请求失败统一记录并返回空串：错误文本伪装成响应体会被上游误当有效数据解析
        # 同上：URL 与异常文本统一脱敏后再落日志
        logger.error(
            i18n.tr(
                "sync_req 请求失败: {masked_url} - {type_name}: {e}",
                masked_url=utils.mask_credentials(url),
                type_name=type(e).__name__,
                e=e,
            )
        )
        resp_str = ""

    return resp_str
