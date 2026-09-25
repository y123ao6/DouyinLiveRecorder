# SrtWriter 重试开片与片内状态回归（CODE_REVIEW_2026-09-20 的 MIN-24①）。
#
# 全部离线：只在 tmp_path 下读写 .srt 文件，不涉及网络与采集线程。
#
# 锁定的不变量：
#   ① MIN-24①：句柄缺失后的「节流重试开片」必须在生成字幕条目**之前**完成——
#      _open_segment() 会重置 _index/_last_end，旧顺序（先拼行后重试）会让同一个 .srt
#      里出现重复/非单调块号，而 SRT 规范要求块序号递增；
#   ② 注入清洗（换行 / "-->"）与片内时间轴钳制两项既有保证不得被上述改动破坏。

from pathlib import Path

from src.srt_writer import SrtWriter


def _block_numbers(content: str) -> list[int]:
    # 从 SRT 文本里取出各块的序号行（块结构：序号 / 时间轴 / 文本 / 空行）
    numbers: list[int] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.isdigit():
            numbers.append(int(stripped))
    return numbers


def test_retry_open_happens_before_line_generation(tmp_path: Path) -> None:
    # 目录不存在 → 前若干条写入全部因句柄缺失被丢弃；目录恢复后按节流重试重新开片。
    # 期望：重新开片后首块序号为 1，且全文件序号严格递增、无重复。
    missing_dir = tmp_path / "not-yet"
    base = str(missing_dir / "live")
    writer = SrtWriter(base_filename=base, segment_seconds=None)
    writer.start(now=0.0)
    assert writer._fp is None

    for i in range(3):
        writer.write(f"用户{i}", f"弹幕{i}", now=float(i))

    missing_dir.mkdir(parents=True)
    # 绕过 10s 节流窗口（等价于「距上次尝试已超过 _OPEN_RETRY_INTERVAL」）
    writer._last_open_attempt = 0.0
    writer.write("用户3", "弹幕3", now=3.0)
    writer.write("用户4", "弹幕4", now=4.0)
    writer.close()

    content = (tmp_path / "not-yet" / "live.srt").read_text(encoding="utf-8")
    numbers = _block_numbers(content)
    assert numbers == [1, 2], f"块序号非从 1 严格递增（重试开片状态串了）: {numbers}"
    assert content.count("-->") == 2


def test_retry_open_keeps_timestamp_state_consistent(tmp_path: Path) -> None:
    # _open_segment 同时重置 _last_end；若顺序颠倒，重试后写入的那一行仍带着
    # 重置前算出的 end，时间轴会与片内基准不一致（下一条又会从 0 附近重来）。
    missing_dir = tmp_path / "gone"
    base = str(missing_dir / "seg")
    writer = SrtWriter(base_filename=base, segment_seconds=1800.0, display_duration=1.5)
    writer.start(now=0.0)
    writer._last_end = 999.0  # 模拟重试前已被抬高的上一条结束时间
    missing_dir.mkdir()
    writer._last_open_attempt = 0.0

    writer.write("u", "m1", now=10.0)
    writer.write("u", "m2", now=11.0)
    writer.close()

    content = (missing_dir / "seg_000.srt").read_text(encoding="utf-8")
    numbers = _block_numbers(content)
    assert numbers == [1, 2]
    # 片内时间轴从 start() 锚点算起（10s/11s）；重试前残留的 _last_end=999 必须已被
    # 开片重置——旧顺序（先算 end 再重试开片）会把 00:16:40,500 这种越界 end 写进文件。
    assert "00:00:10,000 --> 00:00:11,500" in content
    assert "00:00:11,000 --> 00:00:12,500" in content
    assert "00:16:40,500" not in content


def test_segment_switch_still_restarts_numbering(tmp_path: Path) -> None:
    # 切片时序号与时间轴按片重置（既有语义，不得被重试顺序调整破坏）
    base = str(tmp_path / "seg")
    writer = SrtWriter(base_filename=base, segment_seconds=1.0)
    writer.start(now=0.0)
    writer.write("u", "第一片", now=0.2)
    writer.write("u", "第二片", now=1.2)
    writer.write("u", "第二片b", now=1.4)
    writer.close()

    first = _block_numbers((tmp_path / "seg_000.srt").read_text(encoding="utf-8"))
    second = _block_numbers((tmp_path / "seg_001.srt").read_text(encoding="utf-8"))
    assert first == [1]
    assert second == [1, 2]


def test_injection_sanitizing_and_in_segment_clamp_unchanged(tmp_path: Path) -> None:
    # 两条既有硬保证：注入文本被清洗为可见字符（块结构不被破坏）、
    # 末条 end 不越过片边界。
    base = str(tmp_path / "safe")
    writer = SrtWriter(base_filename=base, segment_seconds=2.0, display_duration=5.0)
    writer.start(now=0.0)
    writer.write("攻击者\n2\n00:00:99,000 --> 00:00:99,999\nFAKE", "正常文本 --> 伪造轴", now=0.5)
    writer.close()

    content = (tmp_path / "safe_000.srt").read_text(encoding="utf-8")
    assert content.count("-->") == 1, "注入的伪时间轴行未被清洗"
    assert _block_numbers(content) == [1]
    # end 钳制到片边界（start=0.5，display_duration=5 → 仍不超过 2.0）
    assert "00:00:00,500 --> 00:00:02,000" in content
