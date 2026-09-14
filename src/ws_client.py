# 异步 WebSocket 客户端封装（对标 dart simple_live_core 的 WebScoketUtils）。
#
# 提供心跳定时、断线重连（最多 max_reconnect 次，间隔 reconnect_interval 秒）。
# 所有平台弹幕共用此客户端。

from __future__ import annotations

import asyncio
import inspect
import ssl
from typing import Awaitable, Callable, Optional, Union, cast

import websockets

import i18n

from .logger import logger

# 单次连接内"毒消息"（处理抛异常的帧）的最大逐条记日志条数：
# 超出后只记一次汇总，避免同型异常把日志刷满、掩盖其它真实问题。
_POISON_LOG_LIMIT = 5


# 根据 url 生成默认 SSL 上下文：wss:// 返回放宽到 @SECLEVEL=1 的 SSLContext 以兼容老套件，ws:// 返回 None。
def _default_ssl_context(url: str) -> Optional[ssl.SSLContext]:
    # 为 wss 连接构造宽松 SSL context。
    #
    #    某些直播平台弹幕服务（如斗鱼 danmuproxy:8506）使用旧 RSA 密钥交换套件，
    #    OpenSSL 3.x 默认 SECLEVEL=1 之上会拒绝握手。降级到 @SECLEVEL=1 以兼容。
    #    ws:// 连接返回 None。
    if not url.startswith("wss://"):
        return None
    ctx = ssl.create_default_context()
    try:
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
    except ssl.SSLError:
        pass  # 某些构建不支持该字符串，退回默认
    return ctx


# 各平台弹幕共用的异步 WebSocket 客户端：负责连接、收包分发、定时心跳、断线重连与主动关闭。
class WsClient:
    # 初始化客户端：url/backup_url 为主备地址，on_message/on_ready/on_heartbeat/on_close/on_reconnect 为回调，
    # heartbeat_interval、max_reconnect、reconnect_interval、connect_timeout 控制心跳与重连策略，
    # headers/proxy/ssl_context 为连接参数（ssl_context 未传时按 url 自动生成）；仅保存配置，不发起连接。
    def __init__(
        self,
        url: str,
        on_message: Callable[[Union[bytes, str]], None],
        on_ready: Optional[Callable[[], None]] = None,
        on_heartbeat: Optional[Callable[[], Union[None, Awaitable[None]]]] = None,
        on_close: Optional[Callable[[str], None]] = None,
        on_reconnect: Optional[Callable[[str], None]] = None,
        heartbeat_interval: float = 45.0,
        headers: Optional[dict] = None,
        backup_url: Optional[str] = None,
        max_reconnect: int = 5,
        reconnect_interval: float = 5.0,
        connect_timeout: float = 10.0,
        ssl_context: Optional[ssl.SSLContext] = None,
        proxy: Optional[str] = None,
    ) -> None:
        self._url = url
        self._backup_url = backup_url
        self._on_message = on_message
        self._on_ready = on_ready
        self._on_heartbeat = on_heartbeat
        self._on_close = on_close
        self._on_reconnect = on_reconnect
        self.heartbeat_interval = heartbeat_interval
        self._headers = headers
        self.max_reconnect = max_reconnect
        self.reconnect_interval = reconnect_interval
        self.connect_timeout = connect_timeout
        # 显式代理(如 Twitch 等海外平台)。None=直连,其余平台行为不变。
        self._proxy = proxy
        # 默认 wss 用宽松 SECLEVEL=1 context；可被 ssl_context 覆盖
        self._ssl_context = ssl_context if ssl_context is not None else _default_ssl_context(url)

        self._ws: Optional["websockets.WebSocketClientProtocol"] = None  # type: ignore[name-defined]
        self._stopped = False
        self._reconnect_count = 0
        self._send_lock = asyncio.Lock()

    # 主协程：连接（重连时改用备用地址）→ 触发 on_ready 并起心跳任务 → 逐帧回调 on_message；
    # 异常或正常断开时按 max_reconnect / reconnect_interval 重连，耗尽则回调 on_close 后返回。
    async def connect(self) -> None:
        # 建立连接并循环收消息，断线后按策略重连。整个生命周期阻塞到 stop 或重连耗尽。
        while not self._stopped:
            url = self._url
            # 重连时切换备用地址（如有）
            if self._reconnect_count > 0 and self._backup_url:
                url = self._backup_url
            # 本次连接内的"毒消息"计数（每次成功建连重置：换地址/重连后重新计数，
            # 避免一次历史风暴永久压制后续真实告警的日志可见性）
            _poison_count = 0
            try:
                async with websockets.connect(
                    url,
                    additional_headers=self._headers,
                    open_timeout=self.connect_timeout,
                    ping_interval=None,  # 各平台自带心跳，关闭库默认 ping
                    max_size=None,
                    ssl=self._ssl_context,
                    proxy=self._proxy,  # None=直连(B站/虎牙等);Twitch 等海外平台可传显式代理
                ) as ws:
                    self._ws = ws
                    self._reconnect_count = 0  # 连上即重置
                    if self._on_ready:
                        self._on_ready()
                    hb_task = asyncio.create_task(self._heartbeat_loop())
                    try:
                        async for data in ws:
                            if self._stopped:
                                break
                            # 2026-09-12 审查（低危）：单条"毒消息"隔离。
                            # 原实现让 _on_message 的异常直接冒泡到外层 except →
                            # 触发整条连接重建；若某条消息恒定解析失败（平台协议变体、
                            # 畸形帧），重连后服务端重放同一条 → 无限重连风暴
                            # （max_reconnect 快速耗尽、CPU 与日志被刷满、弹幕永久不可用）。
                            # 单帧解析失败只丢该帧并记日志，连接保持——与各平台
                            # decode_message 内部的 debug 兜底构成两级防御。
                            try:
                                self._on_message(data)
                            except Exception as e:
                                _poison_count += 1
                                if _poison_count <= _POISON_LOG_LIMIT:
                                    logger.warning(
                                        i18n.tr(
                                            "弹幕消息处理异常（已丢弃该帧，连接保持）: {type_name}: {e}",
                                            type_name=type(e).__name__,
                                            e=e,
                                        )
                                    )
                                elif _poison_count == _POISON_LOG_LIMIT + 1:
                                    # 超限后降级为不再逐条记，避免日志被同型异常刷满
                                    logger.warning(
                                        i18n.tr(
                                            "弹幕消息处理异常持续出现，后续同类异常不再逐条记录（累计 {count} 条）",
                                            count=_poison_count,
                                        )
                                    )
                                continue
                    finally:
                        hb_task.cancel()
                        try:
                            await hb_task
                        except asyncio.CancelledError:
                            # hb_task 按预期被取消（回收心跳任务）属正常路径，吞掉即可；
                            # 若系本协程自身被取消（hb_task 并未处于 cancelled 态），
                            # 不得吞掉取消信号，原样上抛交由外层统一退出
                            if not hb_task.cancelled():
                                raise
                        except Exception:
                            pass
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._stopped:
                    break
                self._reconnect_count += 1
                if self._reconnect_count <= self.max_reconnect:
                    if self._on_reconnect:
                        self._on_reconnect(str(e))
                    await asyncio.sleep(self.reconnect_interval)
                    continue
                # 重连耗尽
                if self._on_close:
                    self._on_close(f"重连超过最大次数，与服务器断开连接: {e}")
                break
            else:
                # 正常关闭（onDone）但未 stop，尝试重连
                if self._stopped:
                    break
                self._reconnect_count += 1
                if self._reconnect_count <= self.max_reconnect:
                    if self._on_reconnect:
                        self._on_reconnect("连接已关闭，正在尝试重连")
                    await asyncio.sleep(self.reconnect_interval)
                    continue
                if self._on_close:
                    self._on_close("重连超过最大次数，与服务器断开连接")
                break

            if self._ws is not None:
                try:
                    await self._ws.close()
                except Exception:
                    pass
                self._ws = None

    # 异步发送一帧数据 data（bytes 或 str）：未连接则直接返回，发送加锁串行化，异常记日志后忽略，无返回值。
    async def send(self, data: Union[bytes, str]) -> None:
        if self._ws is None:
            return
        async with self._send_lock:
            try:
                await self._ws.send(data)
            except Exception as e:
                # 2026-09-12 审查（低危）：原为裸 except: pass——发送失败（连接已断、
                # 帧过大被拒、编码错误）完全无声，表现为「进房包发了但永远收不到弹幕」
                # 且无任何线索可查。至少留一条 debug；不重抛是刻意的——send 多由
                # on_ready 等同步回调经 _send_nowait 触发，重抛会打断收包主循环。
                logger.debug(i18n.tr("弹幕数据发送失败（已忽略）: {type_name}: {e}", type_name=type(e).__name__, e=e))

    # 同步版发送：把 send(data) 作为任务丢进事件循环，立即返回不等待结果（供 on_ready 等同步回调使用）。
    def send_nowait(self, data: Union[bytes, str]) -> None:
        # 同步回调（on_ready 等）中调用的非阻塞发送。
        if self._ws is None:
            return
        asyncio.ensure_future(self.send(data))

    # 心跳循环任务：每隔 heartbeat_interval 秒调用 on_heartbeat（同步或协程均支持），
    # 已停止或连接为空时退出；单次心跳加 asyncio.wait_for 兜底——心跳回调若因网络阻塞
    # 永久挂起（无 asyncio.TimeoutError 出口），后续心跳将永远无法被调度，连接「无心跳
    # 被服务端主动切断」时也误判为正常关闭。timeout 取 heartbeat_interval + 1s 缓冲：
    # 心跳正常 1 秒内必返回，超时即视为本轮失败但仍让连接继续走重连路径。
    async def _heartbeat_loop(self) -> None:
        _HEARTBEAT_TIMEOUT_SECONDS = max(1.0, self.heartbeat_interval + 1.0)
        while not self._stopped:
            await asyncio.sleep(self.heartbeat_interval)
            if self._stopped or self._ws is None:
                break
            if self._on_heartbeat:
                try:
                    result = self._on_heartbeat()
                    if inspect.isawaitable(result):
                        # 协程型心跳加 wait_for 兜底：超时即关连接、退出心跳循环
                        # 让外层 connect 走重连；非协程型（同步回调）则原样调用、不加超时
                        # ——同步回调阻塞本协程属于「调用方违反契约」,此处无法挽救。
                        try:
                            await asyncio.wait_for(cast(Awaitable[None], result), timeout=_HEARTBEAT_TIMEOUT_SECONDS)
                        except TimeoutError:
                            from loguru import logger as _log

                            _log.warning(
                                f"[ws_client] 心跳回调超时 ({_HEARTBEAT_TIMEOUT_SECONDS:.0f}s),关闭连接以触发重连"
                            )
                            try:
                                if self._ws is not None:
                                    await self._ws.close()
                            except Exception:
                                pass
                            break
                except Exception:
                    pass

    # 主动关闭：置停止标记（阻止后续重连与心跳）并关闭底层连接，异常忽略，无返回值。
    async def close(self) -> None:
        self._stopped = True
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
