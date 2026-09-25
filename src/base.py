# 弹幕模块基类与数据结构（对标 dart simple_live_core 的 LiveDanmaku / LiveMessage）。
#
# 本模块定义各平台弹幕实现的公共契约与传输数据结构：
# - DanmakuMessageType：弹幕消息类型枚举（聊天/礼物/在线人数/醒目留言）
# - DanmakuMessage：单条弹幕的数据载体（类型、用户名、内容、颜色、时间戳等）
# - DanmakuBase：抽象基类，各平台子类实现 start/stop/heartbeat/decode_message，
#   并通过 on_message / on_close / on_ready 回调把事件上抛给采集器。

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

import i18n


# 弹幕消息类型枚举：取值为字符串（chat/gift/online/superChat），供消息过滤与分发判断使用。
class DanmakuMessageType(Enum):
    # 对标 dart simple_live_core 的 LiveMessageType。

    CHAT = "chat"
    GIFT = "gift"
    ONLINE = "online"
    SUPER_CHAT = "superChat"


# 单条弹幕消息数据类（对标 dart LiveMessage）：type 消息类型、user_name 用户名、
# message 正文、data 平台原始数据、color 显示颜色、timestamp_ms 相对时间戳。
@dataclass
class DanmakuMessage:
    # timestamp_ms 由 DanmakuCollector 在收到时注入（time.monotonic 基准的相对秒），
    # 平台实现不写该字段。

    type: DanmakuMessageType
    user_name: str
    message: str
    data: Any = None
    color: str = "#FFFFFF"
    timestamp_ms: float = 0.0


# 后台弹幕协程的统一异常落盘（2026-09-12 审查）：裸 asyncio.ensure_future 的异常仅在
# 任务被 GC 时以 "Task exception was never retrieved" 打印到 stderr，进房协程抛异常
# （如 room_id 非数字、发送失败）将完全无日志地静默死亡；各平台调度后台协程一律改用
# spawn_danmaku_task，在完成回调里捕获并落盘异常。
def _log_task_exception(task: "asyncio.Task[None]") -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        from src.logger import logger

        logger.warning(i18n.tr("[弹幕]后台协程异常: {type_name}: {exc}", type_name=type(exc).__name__, exc=exc))


def spawn_danmaku_task(coro: Awaitable[None]) -> "asyncio.Task[None]":
    task = asyncio.ensure_future(coro)
    task.add_done_callback(_log_task_exception)
    return task


# 平台弹幕客户端抽象基类：统一连接生命周期与回调协议，子类需实现四个抽象方法。
class DanmakuBase(ABC):
    # 对标 dart LiveDanmaku。收到可分发的弹幕时调 self._emit(DanmakuMessage(...)) 上抛。

    heartbeat_interval: float = 45.0  # 秒，各平台子类覆盖

    # 初始化：登记 on_message / on_close / on_ready 三个回调（语义见方法名），并把停止标记 _stopped 置 False。
    def __init__(
        self,
        on_message: Optional[Callable[[DanmakuMessage], None]] = None,
        on_close: Optional[Callable[[str], None]] = None,
        on_ready: Optional[Callable[[], None]] = None,
    ) -> None:
        self._on_message = on_message
        self._on_close = on_close
        self._on_ready = on_ready
        self._stopped = False

    # 断线重连回调（2026-09-12 审查 6.4）：各平台原先一律把 on_reconnect 指向
    # self._on_close，而 _on_close 的语义是「房间已关闭」——它会调监控枢纽的
    # room_closed() 把房间标记为断开。重连是**中间态**（连接仍在 max_reconnect
    # 次数内会自动恢复），把它当成关闭上报，会让监控面板出现「房间已断开」的假事件，
    # 实际几秒后重连成功又活过来。改为独立的重连回调：只记 debug 日志，不上报关闭。
    def _on_reconnect(self, reason: str) -> None:
        from src.logger import logger

        logger.debug(i18n.tr("[{cls}]弹幕连接断开，正在重连: {reason}", cls=type(self).__name__, reason=reason))

    # 抽象方法：用平台启动参数 args（room_id / token 等）建立连接并持续接收弹幕，无返回值。
    @abstractmethod
    async def start(self, args: Any) -> None:
        pass

    # 抽象方法：停止接收弹幕并关闭底层连接，无入参无返回值。
    @abstractmethod
    async def stop(self) -> None:
        pass

    # 抽象方法：向服务端发送一次平台约定的心跳包，由 WsClient 按 heartbeat_interval 定时调用。
    @abstractmethod
    async def heartbeat(self) -> None:
        pass

    # 抽象方法：解析一帧原始数据 data（bytes 或 str），解析结果经 _emit 回调上抛，无返回值。
    @abstractmethod
    def decode_message(self, data: bytes | str) -> None:
        pass

    # 子类统一经 _emit 上抛弹幕（而不是直接调 _on_message），保留一处判空与解耦点。
    def _emit(self, msg: DanmakuMessage) -> None:
        if self._on_message:
            self._on_message(msg)
