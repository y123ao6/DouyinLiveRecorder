# B站弹幕实现，移植自 dart simple_live_core 的 bilibili_danmaku.dart。
#
# 协议：WebSocket wss://{serverHost}/sub，大头序 16B 帧头
# [包长4][头长2=16][protover2][op4][seq4]。
# protover=2 需 zlib 解压，=3 需 brotli 解压（依赖 brotli 包）。
# buvid 获取链（进程缓存→登录 cookie→spi→首页 Set-Cookie→随机 UUID 兜底）与
# AUTH_REPLY 显式校验的完整约定见 AGENTS.md「B站弹幕 buvid 必须真实」条目；本文件
# 负责被拒侧：_reject_auth() 断开并使 spider 侧 buvid 缓存失效 + 看门狗兜底静默拒绝。

from __future__ import annotations

import asyncio
import json
import re
import struct
import zlib
from typing import Any, Union

import brotli
from loguru import logger

import i18n
from src.base import DanmakuBase, DanmakuMessage, DanmakuMessageType, spawn_danmaku_task

# MI-01：解压上限与带限长解压助手统一取自 ws_client
from src.ws_client import _MAX_DECOMPRESSED_BYTES, WsClient, decompress_brotli_limited, decompress_limited

HEADER_LEN = 16

# SEV-2215（2026-09-22）：弹幕 WS 的连接主机完全取自 getDanmuInfo 的响应，而连接时
# 会带上用户登录 Cookie（SESSDATA/DedeUserID）→ 响应可把凭据引向任意主机（凭据外泄 + SSRF）。
# 真实 host 形如 broadcastlv.chat.bilibili.com / broadcastlv2.chat.bilibili.com；
# 白名单按「精确等于或 . 后缀」判定，覆盖 B站官方域名族实际会出现的域。
_BILI_DANMAKU_ALLOWED_HOST_SUFFIXES = (
    "bilibili.com",
    "bilivideo.com",
    "bilivideo.cn",
    "hdslb.com",
)


def _bili_danmaku_host_allowed(host: str) -> bool:
    # 判定弹幕服务器 host 是否落在 B站官方域名族内。用「精确等于或 . 后缀」而非裸 endswith，
    # 防 evil-bilibili.com / notbilibili.com 这类后缀伪装被放行。空/带端口/带 path 一律拒绝。
    name = (host or "").strip().lower()
    if not name or "/" in name or ":" in name:
        return False
    return any(name == suffix or name.endswith("." + suffix) for suffix in _BILI_DANMAKU_ALLOWED_HOST_SUFFIXES)


# B站弹幕客户端：封装 WebSocket 连接、进房、心跳与消息解密。
class BilibiliDanmaku(DanmakuBase):
    heartbeat_interval = 60.0  # 60s

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._args: dict = {}
        self._ws: WsClient | None = None
        self._session_ok = False
        self._auth_ok = False

    # 启动：解析房间/服务器参数，逐个尝试 host 建立 WebSocket 连接，失败则回调 on_close。
    async def start(self, args: Any) -> None:
        self._args = args if isinstance(args, dict) else {}
        server_host = self._args.get("server_host", "")
        room_id = self._args.get("room_id")
        if not server_host or not room_id:
            if self._on_close:
                self._on_close("缺少 server_host/room_id")
            return

        hosts = [str(h) for h in (self._args.get("host_list") or []) if h]
        if server_host and server_host not in hosts:
            hosts.insert(0, server_host)
        # SEV-2215：在建立连接（携带登录 Cookie）之前先按官方域白名单过滤。响应指定的 host
        # 不落在白名单内即跳过并 WARNING——绝不向该 host 发凭据。原先所有候选被过滤掉时降级
        # 为「只录视频不录弹幕」（on_close 通知，不建连），而非退回去连不可信 host。
        _allowed: list[str] = []
        for _h in hosts:
            if _bili_danmaku_host_allowed(_h):
                _allowed.append(_h)
            else:
                logger.warning(
                    i18n.tr(
                        "[B站弹幕]跳过非官方域弹幕服务器（可能被劫持，不发送凭据）: {host}",
                        host=_h,
                    )
                )
        hosts = _allowed
        if not hosts:
            if self._on_close:
                self._on_close(i18n.tr("无可用弹幕服务器（host 均不在 B站官方域白名单内）"))
            self._session_ok = False
            return

        # 逐个尝试 getDanmuInfo 返回的 host，全部连不上才放弃（单 host 固定会卡死）
        cookie = self._args.get("cookie", "")
        for idx, host in enumerate(hosts):
            if self._stopped:
                return
            backup = hosts[idx + 1] if idx + 1 < len(hosts) else None
            self._ws = WsClient(
                url=f"wss://{host}/sub",
                backup_url=f"wss://{backup}/sub" if backup else None,
                heartbeat_interval=self.heartbeat_interval,
                on_message=self.decode_message,
                on_ready=self._on_ws_ready,
                on_heartbeat=self.heartbeat,
                on_close=self._on_close,
                on_reconnect=self._on_reconnect,
                headers={"cookie": cookie} if cookie else None,
                max_reconnect=2,
                reconnect_interval=3.0,
                connect_timeout=8.0,
            )
            await self._ws.connect()
            if self._session_ok or self._stopped:
                break

    # WS 就绪回调：置进房成功标志、触发 on_ready 并异步发送进房包。
    def _on_ws_ready(self) -> None:
        self._session_ok = True
        # 每次新连接（含断线重连）都须重新过 AUTH：上一连接的 _auth_ok 若不清零，
        # 重连后的看门狗会误判「已认证」而永不兜底（2026-09-12 审查 H-4 接线时补）
        self._auth_ok = False
        if self._on_ready:
            self._on_ready()
        # spawn_danmaku_task：裸 ensure_future 的进房协程异常（room_id 非数字/发送失败）
        # 会静默死亡，改用带异常落盘的调度（2026-09-12 审查）
        spawn_danmaku_task(self._join_room())

    # 异步发送进房请求（uid/roomid/token 等），加入指定直播间。
    async def _join_room(self) -> None:
        if self._ws is None:
            return
        # 与 dart 一致：uid/buvid 匿名亦可，token 必须。uid 必须是观众自身 uid（匿名=0），不能传
        # 房间主的 uid（get_bilibili_danmaku_info 返回的 uid 是主播 uid）：真机对照探针证实
        # uid=主播uid 时弹幕服务器在 AUTH 后立刻硬断连（1006 / "no close frame"），uid=0 则正常
        # 收到 AUTH_REPLY 与弹幕。登录态 cookie（SESSDATA）携带 DedeUserID 时取其作为观众 uid。
        _m = re.search(r"DedeUserID=(\d+)", str(self._args.get("cookie") or ""))
        viewer_uid = int(_m.group(1)) if _m else 0
        join_body = json.dumps(
            {
                "uid": viewer_uid,
                "roomid": int(self._args.get("room_id", 0)),
                "protover": 3,
                "buvid": self._args.get("buvid", ""),
                "platform": "web",
                "type": 2,
                "key": str(self._args.get("token", "")),
            },
            separators=(",", ":"),
        )
        await self._ws.send(self._encode(join_body, action=7))
        # 2026-09-12 审查 H-4：看门狗此前从未接线（全仓无调用点），「服务器静默不回
        # AUTH_REPLY、连接保持、心跳照发、0 弹幕且无日志」的软拒绝形态无人兜底，
        # _auth_ok 也永远不会被置 True；进房包发出即挂看门狗，超时未认证按被拒处理。
        spawn_danmaku_task(self._auth_watchdog(self._ws))

    # 进房认证超时（秒）：AUTH 发出后该时长内未收到 code=0 回应视为被拒/异常
    _AUTH_TIMEOUT = 8.0

    # 认证看门狗：进房包发出后限时未收到 AUTH_REPLY(code=0) 则按被拒处理（静默拒绝与 code!=0 的
    # 软拒绝表现一致：连接保持、心跳照发，只能靠这里兜底；处置理由见 _reject_auth）。
    # ws 为发送进房包时的连接实例：若期间已切换到下一 host，本次看门狗作废。
    async def _auth_watchdog(self, ws: WsClient) -> None:
        await asyncio.sleep(self._AUTH_TIMEOUT)
        if self._stopped or self._auth_ok:
            return
        if self._ws is not ws:
            return  # 会话已切换 host，旧看门狗作废
        logger.warning(
            i18n.tr(
                "[B站弹幕]进房认证 {AUTH_TIMEOUT} 秒无回应，按被拒处理主动断开",
                AUTH_TIMEOUT=f"{self._AUTH_TIMEOUT:.0f}",
            )
        )
        self._reject_auth()

    # 认证被拒统一处理：置停止标志、关闭连接，并使 spider 侧 buvid 缓存失效——兜底随机 UUID
    # 被服务器拒后不可复用，失效后下一轮监测重走真实获取链（cookie/spi/首页 Set-Cookie）；
    # 真实 buvid 被拒时重取亦无副作用。
    # MID-2245：这里必须走 WsClient.fail() 而不是 close()。close() 的语义是「调用方主动停止」，
    # connect() 的两条 `if self._stopped: break` 出口都不回调 on_close，于是 collector 侧与
    # room_connected 配对的 hub.room_closed() 永不发出，Web 弹幕监控页会把该房间永久停在
    # 「已连接 / 0 条」——即本文件要消灭的「静默零弹幕无线索」。
    def _reject_auth(self) -> None:
        self._stopped = True
        if self._ws is not None:
            asyncio.ensure_future(self._ws.fail(i18n.tr("进房认证被拒（AUTH_REPLY 非 0 或超时未回应）")))
        try:
            from src import spider  # 懒加载：避免 platforms <-> spider 循环导入

            spider.invalidate_bili_buvid_cache()
        except Exception:
            pass

    # 发送心跳包（action=2），维持 WebSocket 长连接。
    async def heartbeat(self) -> None:
        if self._ws is not None:
            await self._ws.send(self._encode("", action=2))

    async def stop(self) -> None:
        self._stopped = True
        if self._ws is not None:
            await self._ws.close()

    # 将文本按 B站 16 字节大头序帧头封装为发送字节串，返回 bytes。
    @staticmethod
    def _encode(msg: str, action: int) -> bytes:
        data = msg.encode("utf-8")
        return struct.pack(">IHHII", len(data) + HEADER_LEN, HEADER_LEN, 0, action, 1) + data

    # 解析收到的字节流（处理粘包），逐帧解码并分发弹幕/在线消息。
    def decode_message(self, data: Union[bytes, str]) -> None:
        if isinstance(data, str):
            return
        # 粘包循环：一帧最少 16 字节头
        offset = 0
        n = len(data)
        while offset + HEADER_LEN <= n:
            packet_len = struct.unpack_from(">I", data, offset)[0]
            if packet_len < HEADER_LEN or offset + packet_len > n:
                break
            try:
                self._decode_packet(data[offset : offset + packet_len])
            except Exception as e:
                # 单帧解析失败不影响后续/录像，但须留异常类型+帧头 hex 线索，避免「0 弹幕零线索」
                logger.debug(
                    i18n.tr(
                        "[B站弹幕]帧解析异常: {type_name} head={head}",
                        type_name=type(e).__name__,
                        head=data[offset : offset + 16].hex(),
                    )
                )
            offset += packet_len

    # 解码单帧：按 protover 解压，解析心跳回应/弹幕消息并 emit。
    def _decode_packet(self, frame: bytes) -> None:
        if len(frame) < HEADER_LEN:
            return
        proto_ver = struct.unpack_from(">H", frame, 6)[0]
        operation = struct.unpack_from(">I", frame, 8)[0]
        body = frame[HEADER_LEN:]

        if operation == 3:
            # 心跳回应：4B 人气值
            if len(body) >= 4:
                online = struct.unpack_from(">I", body, 0)[0]
                self._emit(
                    DanmakuMessage(
                        type=DanmakuMessageType.ONLINE,
                        user_name="",
                        message="",
                        data=online,
                        color="#FFFFFF",
                    )
                )
            return

        if operation == 8:
            # 进房包（AUTH）回应：code==0 才会推弹幕。非 0 时服务器软拒绝——连接保持不断开也不推
            # 弹幕（此前完全无感知），故显式校验并主动断开：_reject_auth 同时使 buvid 缓存失效，
            # 等下一轮监测重取参数进房。
            try:
                reply = json.loads(body.decode("utf-8", errors="ignore") or "{}")
            except Exception:
                reply = {}
            code = reply.get("code", -1) if isinstance(reply, dict) else -1
            if code == 0:
                self._auth_ok = True  # 解除认证看门狗
                logger.debug("[B站弹幕]进房认证成功（AUTH_REPLY code=0）")
            else:
                logger.warning(
                    i18n.tr(
                        "[B站弹幕]进房认证失败（AUTH_REPLY code={code}），主动断开: {reply}", code=code, reply=reply
                    )
                )
                self._reject_auth()
            return
        if operation != 5:
            return  # 其他操作码忽略

        try:
            # MI-01：三处解压都必须限长。zlib/brotli 的高压缩比会让几百 KB 的帧在内存里
            # 展开成 GB 级对象（解压炸弹面），而本进程同时还跑着录制主流程。
            if proto_ver == 2:
                payload = decompress_limited(body, _MAX_DECOMPRESSED_BYTES, wbits=15)
            elif proto_ver == 3:
                # brotli 绑定无 max_output_size 参数，改用分块解压 + 累计限长
                payload = decompress_brotli_limited(body, _MAX_DECOMPRESSED_BYTES)
            else:
                payload = body
        except Exception:
            return  # 解压失败或超限丢弃

        # 解压后的包内多条 JSON 以控制字符（\x00-\x1f）分隔（与 dart split [\x00-\x1f] 一致），
        # 使用 splitlines 会把整包当一行导致 json.loads 失败，这里按控制字符切分
        for item in re.split(r"[\x00-\x1f]+", payload.decode("utf-8", errors="ignore")):
            item = item.strip()
            if len(item) > 2 and item.startswith("{"):
                try:
                    self._parse_message(json.loads(item))
                except Exception as e:
                    logger.debug(
                        i18n.tr(
                            "[B站弹幕]消息解析异常: {type_name} item={item}",
                            type_name=type(e).__name__,
                            item=repr(item[:64]),
                        )
                    )

    # 解析单条 JSON 弹幕消息（弹幕/SC），提取内容、用户、颜色并 emit。
    def _parse_message(self, obj: dict) -> None:
        cmd = str(obj.get("cmd", ""))
        if "DANMU_MSG" in cmd:
            info = obj.get("info")
            if isinstance(info, list) and len(info) > 2:
                message = str(info[1])
                color_int = 0
                # info[0][3] 为弹幕颜色十进制
                try:
                    if isinstance(info[0], list) and len(info[0]) > 3:
                        color_int = int(info[0][3])
                except TypeError, ValueError:
                    color_int = 0
                user_info = info[2]
                if isinstance(user_info, list) and len(user_info) > 1:
                    self._emit(
                        DanmakuMessage(
                            type=DanmakuMessageType.CHAT,
                            user_name=str(user_info[1]),
                            message=message,
                            color=f"#{color_int:06X}" if color_int else "#FFFFFF",
                        )
                    )
        elif cmd == "SUPER_CHAT_MESSAGE":
            data = obj.get("data")
            if data:
                self._emit(
                    DanmakuMessage(
                        type=DanmakuMessageType.SUPER_CHAT,
                        user_name=str(data.get("user_info", {}).get("uname", "")),
                        message=str(data.get("message", "")),
                        data=data,
                        color="#FFFFFF",
                    )
                )
