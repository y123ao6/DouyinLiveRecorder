# Tests for src/config_io.py — delete_line 的行尾归一与返回值（SEV-05 回归锁），
# 以及写入锁/快照同步等既有契约不被改坏。
#
# 中文：本文件的存在理由是 SEV-05——delete_line 按 MI-11 用 newline="" 读原文（文件行带
# \r\n），而所有调用方传进来的行都经 universal newlines 归一为 \n 结尾，整行精确比较在
# CRLF 文件上恒不成立 → 面板点「删除」永久静默 no-op 却回报成功。CI 在 Linux（天然 LF）
# 跑，结构上发现不了，故必须补显式的 CRLF 用例。

from pathlib import Path
from types import TracebackType
from typing import Self

import pytest
from pytest import MonkeyPatch

import main  # noqa: E402  (config_io 通过 import main 惰性读取模块全局，须先加载)
from src import config_io  # noqa: E402


class _RecordingLock:
    # 替身锁：记录 with 进入次数，用于断言「持锁读写」这一既有契约未被改坏
    # （AGENTS：函数要么只在内部加锁、要么只由调用方加锁，二选一须可机检）。
    def __init__(self) -> None:
        self.entered = 0

    def __enter__(self) -> Self:
        self.entered += 1
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None


def _write_lines(path: Path, lines: list[str], encoding: str = "utf-8-sig") -> None:
    # newline="" 写入：不做换行符翻译，逐字保留 \r\n（Windows 上 URL_config.ini 的真实形态）
    # 用默认换行写会得到 LF，那正是本缺陷在 CI（Linux）上看不见的原因——CI 天然 LF，
    # 只有显式构造 CRLF 文件才能把「读侧行尾不匹配」这条路径暴露出来。
    with open(path, "w", encoding=encoding, newline="") as f:
        _ = f.write("".join(lines))


def _read_raw(path: Path, encoding: str = "utf-8-sig") -> list[str]:
    # 同样按 newline="" 读回：断言的是「文件字节形态」，而不是被 universal newlines
    # 修饰过的视图——否则「行尾是否被改成 LF」这一子问题永远断不出来。
    with open(path, "r", encoding=encoding, newline="") as f:
        return f.readlines()


class TestDeleteLineLineEndings:
    # SEV-05：CRLF 文件 + \n 结尾的入参（调用方的真实形态）必须真的删掉行。

    def test_crlf_file_with_lf_argument_removes_line(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        target = tmp_path / "URL_config.ini"
        kept_url = "https://live.douyin.com/111111111111\n"
        gone_url = "https://live.douyin.com/222222222222\n"
        _write_lines(target, [kept_url.replace("\n", "\r\n"), gone_url.replace("\n", "\r\n")])
        monkeypatch.setattr(main, "url_config_file", str(tmp_path / "other.ini"))

        # 调用方传的是 universal newlines 读出的 \n 结尾行（web_api 的 raw_line / main 的 origin_line）
        assert config_io.delete_line(str(target), gone_url) is True

        remaining = _read_raw(target)
        assert [kept_url.replace("\n", "\r\n")] == remaining
        # 未被整体改写成 LF：保留原文件的 CRLF 行尾（MI-11 语义不变）
        assert all(line.endswith("\r\n") for line in remaining)

    def test_lf_file_still_removes_line(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        target = tmp_path / "URL_config.ini"
        _write_lines(target, ["https://a.example/1\n", "https://a.example/2\n"])
        monkeypatch.setattr(main, "url_config_file", str(tmp_path / "other.ini"))

        assert config_io.delete_line(str(target), "https://a.example/1\n") is True
        assert _read_raw(target) == ["https://a.example/2\n"]

    def test_missing_line_returns_false_and_keeps_file(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        target = tmp_path / "URL_config.ini"
        original = ["https://a.example/1\r\n", "#https://a.example/2\r\n"]
        _write_lines(target, original)
        monkeypatch.setattr(main, "url_config_file", str(tmp_path / "other.ini"))

        assert config_io.delete_line(str(target), "https://a.example/999\n") is False
        assert _read_raw(target) == original

    def test_comment_prefix_not_matched_by_bare_url(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        # 精确整行比较的语义必须保留：被注释掉（# 前缀）的行不等于该 URL 本身
        target = tmp_path / "URL_config.ini"
        original = ["#https://a.example/1\r\n"]
        _write_lines(target, original)
        monkeypatch.setattr(main, "url_config_file", str(tmp_path / "other.ini"))

        assert config_io.delete_line(str(target), "https://a.example/1\n") is False
        assert _read_raw(target) == original

    def test_delete_all_removes_every_match(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        target = tmp_path / "URL_config.ini"
        dup = "https://a.example/1\r\n"
        _write_lines(target, [dup, "https://a.example/2\r\n", dup])
        monkeypatch.setattr(main, "url_config_file", str(tmp_path / "other.ini"))

        assert config_io.delete_line(str(target), "https://a.example/1\n", delete_all=True) is True
        assert _read_raw(target) == ["https://a.example/2\r\n"]

    def test_single_match_only_by_default(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        target = tmp_path / "URL_config.ini"
        dup = "https://a.example/1\r\n"
        _write_lines(target, [dup, dup])
        monkeypatch.setattr(main, "url_config_file", str(tmp_path / "other.ini"))

        assert config_io.delete_line(str(target), "https://a.example/1\n") is True
        assert _read_raw(target) == [dup]

    def test_read_failure_returns_false(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        missing = tmp_path / "not-here.ini"
        monkeypatch.setattr(main, "url_config_file", str(tmp_path / "other.ini"))
        assert config_io.delete_line(str(missing), "https://a.example/1\n") is False


class TestDeleteLineWriteContract:
    # 既有契约：持锁 + 原子写 + 命中 URL 配置文件时同步快照。

    def test_holds_file_update_lock(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        target = tmp_path / "URL_config.ini"
        _write_lines(target, ["https://a.example/1\r\n", "https://a.example/2\r\n"])
        recorder = _RecordingLock()
        monkeypatch.setattr(main, "file_update_lock", recorder)
        monkeypatch.setattr(main, "url_config_file", str(tmp_path / "other.ini"))

        assert config_io.delete_line(str(target), "https://a.example/1\n") is True
        assert recorder.entered == 1

    def test_atomic_write_failure_returns_false(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        # 写盘失败必须回报 False（调用方据此报错，不能再回报成功）
        target = tmp_path / "URL_config.ini"
        original = ["https://a.example/1\r\n"]
        _write_lines(target, original)
        monkeypatch.setattr(main, "url_config_file", str(tmp_path / "other.ini"))
        monkeypatch.setattr(config_io, "_atomic_write_text", lambda *a, **kw: False)

        assert config_io.delete_line(str(target), "https://a.example/1\n") is False
        assert _read_raw(target) == original

    def test_snapshot_updated_for_url_config_file(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        target = tmp_path / "URL_config.ini"
        _write_lines(target, ["https://a.example/1\r\n", "https://a.example/2\r\n"])
        monkeypatch.setattr(main, "url_config_file", str(target))
        monkeypatch.setattr(main, "ini_URL_content", "OLD-SNAPSHOT")

        assert config_io.delete_line(str(target), "https://a.example/1\n") is True
        # 快照更新为「已落盘内容」，供 update_file 的异常恢复基线使用
        assert main.ini_URL_content == "https://a.example/2\r\n"


if __name__ == "__main__":  # pragma: no cover - 仅手工单文件调试入口
    raise SystemExit(pytest.main([__file__, "-q"]))
