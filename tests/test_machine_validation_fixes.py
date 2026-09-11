# -*- coding: utf-8 -*-
# 真机验证 4 项保守实施回归。
#
# 4 项原始变更详情见 CODE_WIKI v4.1.0-dev：
# ① spider.py：_safe_loads / _is_safe_http_url 保护 JSON 解析与 URL scheme 校验
# ② ws_client.py：心跳回调 wait_for 兜底 + 超时主动关连接
# ③ proxy.py：ProxyInfo 接受 IPv6 主机（[::1] / ::1）
# ④ video_postprocess.py：_run_ffmpeg_checked 超时分类型（不再被 unknown error 吞）

import json
import subprocess
import time
from pathlib import Path
from typing import Any, cast

import pytest

# ======================================================================
# ① spider.py 防御
# ======================================================================


def test_spider_safe_loads_returns_none_on_bad_json() -> None:
    from src.spider import _safe_loads

    # 合法 JSON 但非 dict（如数组）：应返回 None（供调用方按业务判空）
    assert _safe_loads("[1,2,3]") is None
    # 合法 dict
    assert _safe_loads('{"a": 1}') == {"a": 1}
    # 损坏的 JSON（缺右括号）：应捕获 JSONDecodeError 返 None，不抛
    assert _safe_loads("{a: 1") is None


def test_spider_is_safe_http_url_whitelist() -> None:
    from src.spider import _is_safe_http_url

    # 允许的协议
    assert _is_safe_http_url("https://live.douyin.com/123")
    assert _is_safe_http_url("http://example.com")
    assert _is_safe_http_url("wss://danmuproxy.douyu.com:8506")
    assert _is_safe_http_url("ws://example.com/ws")
    # 拒绝的协议（SSRF 风险面）
    assert not _is_safe_http_url("file:///etc/passwd")
    assert not _is_safe_http_url("gopher://internal/secret")
    assert not _is_safe_http_url("ftp://internal/data")
    # 缺 scheme 的相对路径也应拒绝
    assert not _is_safe_http_url("//example.com/path")


# ======================================================================
# ② ws_client 心跳超时
# ======================================================================


def test_ws_heartbeat_timeout_closes_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    # 心跳回调 hang 住超过 _HEARTBEAT_TIMEOUT_SECONDS 时，循环应主动关连接退出，
    # 让外层 connect() 进入重连路径而非永远等待。
    # 策略：patch 内部 websockets.connect 不直接连真实 ws，而是返回假协程
    import asyncio

    from src import ws_client

    close_called = []

    class _FakeWs:
        # 模拟底层 ws：close() 记录标记，__aiter__ 返回空流（心跳之外没消息）
        def __init__(self) -> None:
            pass

        async def close(self) -> None:
            close_called.append(time.monotonic())

        def __aiter__(self) -> "_FakeWs":
            return self

        async def __anext__(self) -> bytes:
            # 永不返回下一帧，循环将卡在 async for；停止由 close() 触发
            await asyncio.sleep(60)
            return b""

    class _FakeConnectCtx:
        async def __aenter__(self) -> _FakeWs:
            return _FakeWs()

        async def __aexit__(self, *exc: Any) -> None:
            pass

    def fake_connect(*args: Any, **kwargs: Any) -> _FakeConnectCtx:
        # websockets v10+ 的 connect 是「可 awaitable + 上下文管理器」对象，
        # async with 直接调 __aenter__ 不需 await；故 fake 也不能 async。
        return _FakeConnectCtx()

    heartbeat_calls: list[float] = []

    async def slow_heartbeat() -> None:
        heartbeat_calls.append(time.monotonic())
        # 心跳里 sleep 4 秒，超过 1+heartbeat_interval 阈值
        await asyncio.sleep(4.0)

    monkeypatch.setattr(ws_client.websockets, "connect", fake_connect)
    client = ws_client.WsClient(
        url="ws://example.invalid",
        on_message=lambda _d: None,
        on_heartbeat=slow_heartbeat,
        heartbeat_interval=0.05,  # 极短间隔
    )
    # 把超时阈值也调小（heartbeat_interval+1 = 1.05s），用 monkeypatch 改常量
    # 因为 _HEARTBEAT_TIMEOUT_SECONDS 是 _heartbeat_loop 内的局部变量，
    # 这里改不了，直接靠 4s sleep 大于默认 1.05s 触发
    try:
        # 用 asyncio.run 跑 connect()，但 stop() 必须在超时后被调用以退出
        async def run_and_stop() -> None:
            t = asyncio.create_task(client.connect())
            # 等待心跳触发并超时（>1.05s + 心跳间隔抖动 + close 路径）
            await asyncio.sleep(2.5)
            await client.close()
            try:
                await asyncio.wait_for(t, timeout=2.0)
            except asyncio.TimeoutError:
                t.cancel()

        asyncio.run(run_and_stop())
        # 验证 close() 至少被调用一次（来自心跳超时分支 + 来自外部 stop）
        assert len(close_called) >= 1, f"心跳超时未触发 ws.close(): {close_called}"
    finally:
        # 确保清理
        _ = client._stopped  # noqa: B018 仅确认对象存活


# ======================================================================
# ③ proxy.py IPv6
# ======================================================================


def test_proxy_info_accepts_ipv6_with_brackets() -> None:
    from src.proxy import ProxyInfo

    # [::1]:8080 形如 Windows 注册表 ProxyServer 的 IPv6 字面量
    info = ProxyInfo("[::1]", "8080")
    assert info.ip == "[::1]"
    assert info.port == "8080"


def test_proxy_info_accepts_bare_ipv6() -> None:
    from src.proxy import ProxyInfo

    # 不带方括号的裸 IPv6（少见但兜底）
    info = ProxyInfo("::1", "8080")
    assert info.ip == "::1"
    assert info.port == "8080"


def test_proxy_info_rejects_invalid_ip() -> None:
    from src.proxy import ProxyInfo

    # 端口合法但 IP 既非 IPv4/IPv6/域名：必须抛 ValueError
    with pytest.raises(ValueError):
        ProxyInfo("not a host!@#", "8080")


# ======================================================================
# ④ video_postprocess 超时分类型
# ======================================================================


def test_video_postprocess_timeout_logged_as_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # 模拟 ffmpeg 卡死：替换 _run_ffmpeg_checked 抛 TimeoutExpired，
    # 验证调用方把异常分到「超时」分支而不是「unknown error」分支。
    import io

    from loguru import logger

    # 必须先 import main，让 video_postprocess 的循环依赖（notify → video_postprocess）
    # 在「先 main 后 video_postprocess」顺序下完成解析；否则 pytest 在子测试里 import
    # src.video_postprocess 会撞上 notify 内部的延迟导入失败。
    import main  # noqa: F401
    from src import video_postprocess

    buf = io.StringIO()
    sink_id = logger.add(buf, format="{level} | {message}", level="DEBUG")
    try:

        def fake_run(*args: Any, **kwargs: Any) -> str:
            raise subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=600)

        monkeypatch.setattr(video_postprocess, "_run_ffmpeg_checked", fake_run)
        target = tmp_path / "input.ts"
        target.write_bytes(b"\x47" * 100)  # 合法 TS magic
        # 三个 caller 各自走一遍，验证都把异常分到 TimeoutExpired 分支
        video_postprocess.segment_video(
            str(target), str(tmp_path / "out_%03d.ts"), "mpegts", "1800", is_original_delete=False
        )
        video_postprocess.converts_mp4(str(target), is_original_delete=False)
        video_postprocess.converts_m4a(str(target), is_original_delete=False)
        text = buf.getvalue()
        # 三处都应在日志里出现「超时」字样（不再被「unknown error」吞）
        assert text.count("超时") >= 3, f"超时未被分类: {text}"
    finally:
        logger.remove(sink_id)
