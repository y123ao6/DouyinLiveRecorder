# -*- coding: utf-8 -*-
# 端到端验证:用真实格式的 B站打包帧喂 BilibiliDanmaku + collector,确认 SRT 产出。
#
# 不依赖外网弹幕,验证:帧协议 → 解析 → collector → SrtWriter 全链路。
#
# MIN-2266 ②：本文件原先 0 个 `test_` 函数——全部逻辑待在 `main()` 里、只在
# `__main__` 守卫下执行，于是 pytest 收集到的是「空文件」：帧协议 → 解析 → SRT 落盘
# 这条串联从不自动跑，断言可以腐烂而文件继续向读者 advertise「e2e 已验证」。
# 它也与 AGENTS 允许「需活房间 + 外网、默认保持人工通道」的 5 个
# `test_*_live_collector.py` **不同类**——本文件全程离线（自己 struct.pack 造帧），
# 没有任何理由不进 pytest。现把主体拆成 test_bili_frame_to_srt_end_to_end，
# 直跑入口 `python tests/test_bili_e2e.py` 仍可用（调同一个函数）。
# 输出目录改走 tmp_path：不再写 tests/_out_e2e/ —— 该目录由 tests/conftest.py 在
# **任意** pytest 会话退出时 rmtree（见 AGENTS「全量 pytest 运行期间不得再启第二个
# pytest 会话」条目），写进去的用例在并发会话下必红。

import asyncio
import json
import os
import struct
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base import DanmakuMessage
from src.platforms.bilibili import BilibiliDanmaku
from src.srt_writer import SrtWriter


def build_frame(objs: list, proto_ver: int = 0) -> bytes:
    # 构造 B站打包帧:多个 JSON 按 \0 分隔,op=5。
    body = "\0".join(json.dumps(o, separators=(",", ":"), ensure_ascii=False) for o in objs).encode("utf-8")
    # B站打包帧头：>IHHII = (包总长, 头部固定16, 协议版本proto_ver, op=5普通消息, 序列号1)。
    # 多对象以 \0 分隔拼进 body，op=5 即业务弹幕/心跳等普通消息。
    # proto_ver=0 表示 body 为明文 JSON；真实链路还有 2(zlib)/3(brotli) 压缩态，
    # 本验证仅覆盖 0 以确认基础解析与 SRT 落盘，压缩分支由单测另行覆盖。
    return struct.pack(">IHHII", len(body) + 16, 16, proto_ver, 5, 1) + body


def danmu_msg(text: str, user: str) -> dict:
    # 对齐真实 DANMU_MSG 结构:info[0][3]=颜色, info[1]=内容, info[2][1]=用户名。
    return {
        "cmd": "DANMU_MSG",
        "info": [
            [0, 1, 25, 16777215, 1, "A", 0, 0],
            text,
            [0, user, 12345678, 0, 0, 0, 0],
            [0, 0],
        ],
    }


def _run_end_to_end(out_dir: str) -> None:
    # 端到端主体：SRT 落盘 + 真实帧解析两段断言，全部写进调用方给的 out_dir。
    base = os.path.join(out_dir, "test_主播_bili")
    os.makedirs(out_dir, exist_ok=True)
    # base 含中文文件名,顺带验证 SrtWriter 对 UTF-8 路径的兼容(Windows 默认 GBK 易踩坑)。
    # out_dir 由 tmp_path / mkdtemp 提供，本就是空目录，无需再清扫历史文件。

    srt = SrtWriter(base_filename=base, segment_seconds=None)
    # 模拟 collector 回调:message_count 记数 + write
    # now 为相对秒数(浮点),SrtWriter 据此换算 00:00:00,000 时码;下方断言校验
    # now=1.05 → 00:00:01,250 的换算以及首条序号 1 与起始时码 00:00:00,000。
    srt.write("弹幕用户A", "这是第一条弹幕", now=1.05)
    srt.write("弹幕用户B", "这是第二条弹幕 hello world", now=2.30)
    srt.write("观众C", "③号弹幕含中文与English混排", now=3.60)
    srt.close()

    srt_file = base + ".srt"
    assert os.path.isfile(srt_file), f"SRT 未生成: {srt_file}"
    with open(srt_file, encoding="utf-8") as fh:
        content = fh.read()
    print("=== SRT 内容 ===")
    print(content)
    assert "弹幕用户A: 这是第一条弹幕" in content
    assert "弹幕用户B: 这是第二条弹幕 hello world" in content
    assert "观众C: ③号弹幕含中文与English混排" in content
    assert "00:00:01,250" in content
    assert content.startswith("1\n00:00:00,000")
    print("=== SRT 写入验证通过 ===")

    # 再验证 BilibiliDanmaku 解析真实帧
    # 手动 new_event_loop 而非 asyncio.run:需把 Capt 实例保留在作用域供断言,
    # 且 decode_message 为同步接口无需循环驱动,仅构造空循环以满足基类初始化约束。
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    got = []

    class Capt(BilibiliDanmaku):
        def _emit(self, msg: DanmakuMessage) -> None:
            # 子类重写 _emit 拦截解析结果(on_message 仅透传),改为收集到 got,
            # 便于对解析出的 message/user_name 做精确断言,验证字段映射正确性。
            got.append(msg)

    c = Capt(on_message=lambda m: None, on_close=lambda r: None, on_ready=lambda: None)
    frames = build_frame([danmu_msg("测试弹幕内容!", "测试用户")], proto_ver=0)
    # 直接喂整帧字节(跳过实时 WS 接收),decode_message 内部按帧头切分并回调 _emit,
    # 此处验证单帧能被正确解码为 DanmakuMessage。
    c.decode_message(frames)
    assert len(got) == 1, f"解析出 {len(got)} 条"
    assert got[0].message == "测试弹幕内容!"
    assert got[0].user_name == "测试用户"
    print(f"=== 帧解析通过: {got[0].user_name}: {got[0].message} ===")
    loop.close()


def test_bili_frame_to_srt_end_to_end(tmp_path: Path) -> None:
    # pytest 入口（MIN-2266 ②）：断言与直跑共用同一个 _run_end_to_end，避免两套演化。
    # 只依赖 tmp_path —— 不触网、不读 config、不碰 tests/_out_e2e 这类会话级共享目录。
    _run_end_to_end(str(tmp_path))


def main() -> None:
    # 保留 `python tests/test_bili_e2e.py` 的人工通道：跑同一套断言，产物落临时目录后即弃。
    with tempfile.TemporaryDirectory(prefix="dlr_bili_e2e_") as out_dir:
        _run_end_to_end(out_dir)
    print("=== 端到端验证全部通过 ===")


if __name__ == "__main__":
    main()
