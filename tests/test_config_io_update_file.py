# tests/test_config_io_update_file.py - src/config_io.py 的**写侧**行为锁。
#
# 已有的 config_io 用例集中在 delete_line 的行尾归一（SEV-05）、只读降级
# （test_config_io_readonly.py）与备份轮换（test_config_io_backup.py）；
# update_file / update_anchor_name / 备份脱敏这三条「会把用户配置写坏」的路径
# 长期没有回归防护。本文件补齐：
#   1) update_file 的段级精确替换：URL 前缀重叠（/1 与 /12）时不得误改他行；
#      读取失败必须用 ini_URL_content 快照回滚，而不是留下空文件；
#   2) update_anchor_name 的幂等与注释前缀/画质段保留；
#   3) CR-07 备份脱敏：[Cookie]/[Authorization]/[账号密码] 的值不得进备份目录，
#      且 DLR_BACKUP_KEEP_SECRETS=1 时原样复制（用户显式放行的语义）。
#
# 沿用 tests/test_config_io.py 的 newline="" 读写口径：断言的是**文件字节形态**
# （含 CRLF），否则「行尾被顺手改成 LF」这类永久破坏看不出来。

import configparser
import os
import threading
import types
from pathlib import Path
from typing import Any

import pytest
from pytest import MonkeyPatch

import main  # noqa: E402  (config_io 通过 import main 惰性读取模块全局，须先加载)
from src import config_io  # noqa: E402

# 分支 → 用例 对照表（本文件只管写侧；读侧/只读降级见 test_config_io_readonly.py，
# 备份轮换见 test_config_io_backup.py）。
#
# _rewrite_line_by_match：所代批改进段级精确替换的四个方向——
#   整行命中 / 段命中 / 全角逗号分隔 / 相似前缀不误伤。最后一个是 6.1 的
#   真缺陷形态（旧实现用 str.replace，.../1 会顺带改坏 .../12），必须单独
#   一条用例盯住，否则任何「改回 substring 匹配」的重构都能静默过闸。
# update_file：noop 短路与「不得抢锁」/ 快照前进时机 / 读取失败回滚 / 原子写
#   失败时快照不得前进。最后两条是同一枚硬币的两面：快照只能追上「已落盘」
#   的内容，追快了就会把写失败伪装成写成功。
# update_anchor_name：幂等（已是目标名要返 False，否则每轮重录都回写一次磁盘）、
#   单层 # 前缀保留、全角冒号归一为半角（与 main.py 的行解析约定同源）。
# 备份脱敏（CR-07）：默认对凭据段打 ***；DLR_BACKUP_KEEP_SECRETS=1 时原样复制；
#   脱敏自身报错时回退原样复制。最后一条的降级方向是「宁可留明文也不能没备份」，
#   不要误改成「脱敏失败则不备份」——那会把可用性换成了不存在的安心感。


URL_A = "https://live.douyin.com/1111111111"
URL_B = "https://live.douyin.com/11111111112"


def _write_text(path: Path, text: str, encoding: str = "utf-8-sig") -> None:
    # 默认 utf-8-sig 不是随手选的：仓库里 URL_config.ini / config.ini 的真实形态就是
    # 带 BOM 的 UTF-8，而 main.text_encoding 也按这个值读取。换成纯 utf-8 会让
    # 「首行键名带上 BOM 字符」这类只在真实配置上出现的问题从测试里消失。
    # newline="" 则保证写入时不做换行符翻译，用例里写的 \r\n 就是盘上的 \r\n。
    with open(path, "w", encoding=encoding, newline="") as f:
        _ = f.write(text)


def _read_text(path: Path, encoding: str = "utf-8-sig") -> str:
    with open(path, "r", encoding=encoding, newline="") as f:
        return f.read()


@pytest.fixture
def url_config(tmp_path: Path, monkeypatch: MonkeyPatch) -> Path:
    # 把「写哪份配置」从仓库里的真 config/ 改到 tmp_path：本文件的用例会真回写文件，
    # 误写真实配置等于改掉用户环境。file_update_lock 也换成新锁，避免与同进程
    # 其他用例共享 main 的全局锁而互相串行。
    path = tmp_path / "URL_config.ini"
    monkeypatch.setattr(main, "url_config_file", str(path))
    monkeypatch.setattr(main, "text_encoding", "utf-8-sig")
    monkeypatch.setattr(main, "ini_URL_content", "")
    monkeypatch.setattr(main, "file_update_lock", threading.Lock())
    return path


class TestRewriteLineByMatch:
    def test_whole_line_match_replaces_and_keeps_eol(self) -> None:
        assert config_io._rewrite_line_by_match(f"{URL_A}\r\n", URL_A, URL_B) == f"{URL_B}\r\n"

    def test_segment_match_preserves_other_segments(self) -> None:
        line = f"原画,{URL_A},主播: 张三\r\n"
        assert config_io._rewrite_line_by_match(line, URL_A, URL_B) == f"原画,{URL_B},主播: 张三\r\n"

    def test_fullwidth_comma_is_a_separator_too(self) -> None:
        line = f"{URL_A}，主播: 张三\n"
        assert config_io._rewrite_line_by_match(line, URL_A, URL_B) == f"{URL_B}，主播: 张三\n"

    def test_similar_prefix_line_is_not_touched(self) -> None:
        # 6.1 的核心：旧实现是整行 substring 替换，/1111111111 会顺带把 /11111111112 改坏
        line = f"{URL_B},主播: 李四\n"
        assert config_io._rewrite_line_by_match(line, URL_A, "REPLACED") is None

    def test_empty_target_never_matches(self) -> None:
        assert config_io._rewrite_line_by_match("anything\n", "   ", "X") is None

    def test_new_string_carrying_commas_stays_one_segment(self) -> None:
        line = f"{URL_A}\n"
        assert config_io._rewrite_line_by_match(line, URL_A, f"{URL_B},主播: 王五") == f"{URL_B},主播: 王五\n"

    def test_trailing_newline_in_new_string_is_not_doubled(self) -> None:
        assert config_io._rewrite_line_by_match(f"{URL_A}\n", URL_A, f"{URL_B}\n") == f"{URL_B}\n"


class TestUpdateFile:
    # update_file 的四类失败必须彼此可区分：noop 短路（不该抢锁）、读取失败（要用快照
    # 回滚）、无命中（不该前进快照）、原子写失败（快照更不能前进）。
    # 前三类都是「不写盘」，最后一类是「差点写坏盘」——只有返回値无法区分它们，
    # 所以断言必须落回到「盘上内容 + 快照内容」两件事实上。
    def test_noop_when_old_equals_new(self, url_config: Path, monkeypatch: MonkeyPatch) -> None:
        _write_text(url_config, f"{URL_A}\n")
        entered = 0

        class _CountingLock:
            def __enter__(self) -> "_CountingLock":
                nonlocal entered
                entered += 1
                return self

            def __exit__(self, *exc: object) -> None:
                return None

        monkeypatch.setattr(main, "file_update_lock", _CountingLock())
        assert config_io.update_file(str(url_config), URL_A, URL_A) == URL_A
        assert entered == 0, "无变化的调用不应抢写入锁"

    def test_replaces_matching_line_and_updates_snapshot(self, url_config: Path) -> None:
        _write_text(url_config, f"原画,{URL_A}\r\n{URL_B}\r\n")
        assert (
            config_io.update_file(str(url_config), URL_A, "https://live.douyin.com/999")
            == "https://live.douyin.com/999"
        )
        content = _read_text(url_config)
        assert "https://live.douyin.com/999" in content
        assert URL_B in content, "相似前缀行不得被顺带改掉"
        assert content.count("\r\n") == 2, "CRLF 行尾必须原样保留"
        assert main.ini_URL_content == content

    def test_start_str_comments_out_hit_line(self, url_config: Path) -> None:
        _write_text(url_config, f"{URL_A}\n")
        assert config_io.update_file(str(url_config), URL_A, URL_A, start_str="#") == URL_A
        assert _read_text(url_config) == f"#{URL_A}\n"

    def test_duplicate_lines_are_collapsed(self, url_config: Path) -> None:
        _write_text(url_config, f"{URL_A}\n{URL_A}\n{URL_B}\n")
        _ = config_io.update_file(str(url_config), URL_B, URL_B, start_str="")
        assert _read_text(url_config) == f"{URL_A}\n{URL_B}\n"

    def test_empty_file_short_circuits(self, url_config: Path) -> None:
        _write_text(url_config, "")
        assert config_io.update_file(str(url_config), URL_A, URL_B) == URL_A
        assert _read_text(url_config) == ""

    def test_read_failure_restores_snapshot(self, url_config: Path, monkeypatch: MonkeyPatch) -> None:
        main.ini_URL_content = f"{URL_B}\n"
        monkeypatch.setattr(main, "text_encoding", "utf-8-sig")
        # BOM 后紧跟非法 UTF-8 字节：严格解码必失败，走到「用快照恢复」这条降级分支
        url_config.write_bytes(b"\xef\xbb\xbf\xff\xfe\xfd")
        assert config_io.update_file(str(url_config), URL_A, URL_B) == URL_A
        assert _read_text(url_config) == f"{URL_B}\n", "读取失败须回滚到快照而非清空"

    def test_read_failure_without_snapshot_leaves_file_intact(self, url_config: Path) -> None:
        url_config.write_bytes(b"\xef\xbb\xbf\xff\xfe\xfd")
        main.ini_URL_content = ""
        assert config_io.update_file(str(url_config), URL_A, URL_B) == URL_A
        assert url_config.read_bytes().startswith(b"\xef\xbb\xbf\xff")

    def test_atomic_write_failure_returns_old_string(self, url_config: Path, monkeypatch: MonkeyPatch) -> None:
        _write_text(url_config, f"{URL_A}\n")
        monkeypatch.setattr(config_io, "_atomic_write_text", lambda *_a, **_k: False)
        assert config_io.update_file(str(url_config), URL_A, URL_B) == URL_A
        assert _read_text(url_config) == f"{URL_A}\n"
        assert main.ini_URL_content == "", "写失败时快照不得前进"


class TestUpdateAnchorName:
    def test_missing_arguments_return_false(self, url_config: Path) -> None:
        assert config_io.update_anchor_name("", "x") is False
        assert config_io.update_anchor_name(URL_A, "") is False

    def test_absent_file_returns_false(self, url_config: Path) -> None:
        assert config_io.update_anchor_name(URL_A, "张三") is False

    def test_appends_anchor_field_and_keeps_quality(self, url_config: Path) -> None:
        _write_text(url_config, f"原画,{URL_A}\r\n{URL_B}\r\n")
        assert config_io.update_anchor_name(URL_A, "张三") is True
        lines = _read_text(url_config).splitlines()
        assert lines[0] == f"原画,{URL_A},主播: 张三"
        assert lines[1] == URL_B, "相似前缀行不得被改"

    def test_existing_field_is_replaced_and_idempotent(self, url_config: Path) -> None:
        _write_text(url_config, f"{URL_A},主播: 旧名\n")
        assert config_io.update_anchor_name(URL_A, "新名") is True
        assert _read_text(url_config) == f"{URL_A},主播: 新名\n"
        assert config_io.update_anchor_name(URL_A, "新名") is False, "已是目标名须幂等跳过"

    def test_fullwidth_colon_line_is_normalized(self, url_config: Path) -> None:
        _write_text(url_config, f"{URL_A},主播： 旧名\n")
        assert config_io.update_anchor_name(URL_A, "新名") is True
        assert _read_text(url_config) == f"{URL_A},主播: 新名\n"

    def test_commented_line_keeps_its_prefix(self, url_config: Path) -> None:
        # 只剥**一层** # 前缀（find("#")+1），余下部分参与段级匹配；双层注释行不命中。
        _write_text(url_config, f"#{URL_A}\n")
        assert config_io.update_anchor_name(URL_A, "张三") is True
        assert _read_text(url_config) == f"#{URL_A},主播: 张三\n"

    def test_double_comment_prefix_is_not_matched(self, url_config: Path) -> None:
        _write_text(url_config, f"## {URL_A}\n")
        assert config_io.update_anchor_name(URL_A, "张三") is False
        assert _read_text(url_config) == f"## {URL_A}\n"

    def test_unrelated_lines_are_left_alone(self, url_config: Path) -> None:
        _write_text(url_config, "\n# 说明行\n")
        assert config_io.update_anchor_name(URL_A, "张三") is False

    def test_unreadable_file_returns_false(self, url_config: Path, monkeypatch: MonkeyPatch) -> None:
        url_config.write_bytes(b"\xef\xbb\xbf\xff\xfe")
        monkeypatch.setattr(main, "text_encoding", "utf-8-sig")
        assert config_io.update_anchor_name(URL_A, "张三") is False

    def test_write_failure_does_not_advance_snapshot(self, url_config: Path, monkeypatch: MonkeyPatch) -> None:
        _write_text(url_config, f"{URL_A}\n")
        monkeypatch.setattr(config_io, "_atomic_write_text", lambda *_a, **_k: False)
        assert config_io.update_anchor_name(URL_A, "张三") is False
        assert main.ini_URL_content == ""


class TestSecretRedaction:
    def test_credential_sections_are_masked(self) -> None:
        text = "[Cookie]\ndouyin_cookie = secret-value\n[录制设置]\nlanguage = zh_CN\n"
        out = config_io._redact_ini_secrets(text)
        assert "secret-value" not in out
        assert "douyin_cookie = ***" in out
        assert "language = zh_CN" in out, "非凭据段不得被脱敏"

    def test_empty_values_are_left_as_is(self) -> None:
        out = config_io._redact_ini_secrets("[Cookie]\ndouyin_cookie = \n")
        assert "douyin_cookie = ***" not in out

    def test_unparseable_content_is_returned_unchanged(self) -> None:
        # 脱敏失败宁可留明文也不能丢备份
        raw = "this is not an ini file [[[\n"
        assert config_io._redact_ini_secrets(raw) == raw

    def test_missing_web_config_symbol_falls_back(self, monkeypatch: MonkeyPatch) -> None:
        import builtins

        real_import = builtins.__import__

        def deny(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "src.web_config":
                raise ImportError("blocked")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", deny)
        raw = "[Cookie]\ndouyin_cookie = abc\n"
        assert config_io._redact_ini_secrets(raw) == raw


class TestPermissionHardening:
    def test_chmod_failure_is_ignored(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        target = tmp_path / "b.ini"
        target.write_text("x", encoding="utf-8")
        config_io._harden_permissions(str(target))  # Windows 上大概率是 no-op，不得抛

        def deny(*args: object, **kwargs: object) -> None:
            raise OSError("unsupported")

        # 按仓内约定走浅拷贝 shim：monkeypatch.setattr(config_io.os, "chmod", ...) 改的是
        # 全进程唯一的 os 模块本体，会波及 harness 守护线程与其他用例（R1 门禁）。
        shim = types.SimpleNamespace(**vars(os))
        shim.chmod = deny
        monkeypatch.setattr(config_io, "os", shim)
        config_io._harden_permissions(str(target))


class TestBackupSecretHandling:
    def test_backup_is_masked_by_default(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        src = tmp_path / "config.ini"
        _write_text(src, "[Cookie]\ndouyin_cookie = top-secret\n")
        monkeypatch.delenv("DLR_BACKUP_KEEP_SECRETS", raising=False)
        monkeypatch.setattr(main, "text_encoding", "utf-8-sig")
        backup_dir = tmp_path / "backup"
        config_io.backup_file(str(src), str(backup_dir))
        copies = list(backup_dir.iterdir())
        assert len(copies) == 1
        text = copies[0].read_text(encoding="utf-8-sig")
        assert "top-secret" not in text
        assert "douyin_cookie = ***" in text

    def test_keep_secrets_flag_copies_verbatim(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        src = tmp_path / "config.ini"
        _write_text(src, "[Cookie]\ndouyin_cookie = top-secret\n")
        monkeypatch.setenv("DLR_BACKUP_KEEP_SECRETS", "1")
        monkeypatch.setattr(main, "text_encoding", "utf-8-sig")
        backup_dir = tmp_path / "backup"
        config_io.backup_file(str(src), str(backup_dir))
        copies = list(backup_dir.iterdir())
        assert copies[0].read_text(encoding="utf-8-sig") == "[Cookie]\ndouyin_cookie = top-secret\n"

    def test_unreadable_source_falls_back_to_copy(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        # 宁可留下明文备份，也不能没有备份——CR-07 的降级方向是刻意选择的。
        src = tmp_path / "config.ini"
        src.write_bytes(b"[Cookie]\ndouyin_cookie = raw\n")
        monkeypatch.delenv("DLR_BACKUP_KEEP_SECRETS", raising=False)
        monkeypatch.setattr(config_io, "_redact_ini_secrets", lambda text: (_ for _ in ()).throw(OSError("boom")))
        backup_dir = tmp_path / "backup"
        config_io.backup_file(str(src), str(backup_dir))
        assert list(backup_dir.iterdir())[0].read_bytes() == b"[Cookie]\ndouyin_cookie = raw\n"

    def test_total_failure_is_swallowed(
        self, tmp_path: Path, monkeypatch: MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.delenv("DLR_BACKUP_KEEP_SECRETS", raising=False)
        captured: list[str] = []
        monkeypatch.setattr(config_io.logger, "error", lambda msg, *a, **k: captured.append(str(msg)))
        config_io.backup_file(str(tmp_path / "missing.ini"), str(tmp_path / "backup"))
        assert any("备份配置文件" in m for m in captured)
        assert capsys.readouterr().out == ""


class _StopBackupLoop(BaseException):
    # 派生自 BaseException：backup_file_start 的循环里有 `except Exception`，
    # 用普通 Exception 作停止信号会被吞掉、循环停不下来。
    pass


class TestBackupLoop:
    def test_unchanged_files_are_not_backed_up_twice(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        cfg = tmp_path / "config.ini"
        _write_text(cfg, "[录制设置]\nlanguage = zh_CN\n")
        urls = tmp_path / "URL_config.ini"
        _write_text(urls, f"{URL_A}\n")
        monkeypatch.setattr(main, "config_file", str(cfg))
        monkeypatch.setattr(main, "url_config_file", str(urls))
        monkeypatch.setattr(main, "backup_dir", str(tmp_path / "backup"))
        monkeypatch.delenv("DLR_BACKUP_KEEP_SECRETS", raising=False)
        monkeypatch.setattr(main, "text_encoding", "utf-8")

        loops: list[int] = []

        def stop(_seconds: float) -> None:
            loops.append(1)
            raise _StopBackupLoop

        monkeypatch.setattr(config_io, "time", types.SimpleNamespace(sleep=stop))

        # 第一轮：两份配置各备份一次；第二轮在 sleep 处终止（MD5 未变 → 不重复备份）
        backed_up: list[str] = []
        original_backup = config_io.backup_file

        def spy_backup(file_path: str, backup_dir_path: str, limit_counts: int = 6) -> None:
            backed_up.append(Path(file_path).name)
            original_backup(file_path, backup_dir_path, limit_counts)

        monkeypatch.setattr(config_io, "backup_file", spy_backup)
        with pytest.raises(_StopBackupLoop):
            config_io.backup_file_start()
        assert backed_up == ["config.ini", "URL_config.ini"]
        assert (tmp_path / "backup").is_dir()

    def test_md5_failure_is_reported_and_loop_continues(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        cfg = tmp_path / "config.ini"
        cfg.write_text("[录制设置]\nlanguage = zh_CN\n", encoding="utf-8")
        urls = tmp_path / "URL_config.ini"
        urls.write_text(f"{URL_A}\n", encoding="utf-8")
        monkeypatch.setattr(main, "config_file", str(cfg))
        monkeypatch.setattr(main, "url_config_file", str(urls))
        monkeypatch.setattr(main, "backup_dir", str(tmp_path / "backup"))

        def deny(*args: object, **kwargs: object) -> None:
            raise OSError("stat failed")

        monkeypatch.setattr(config_io.utils, "check_md5", deny)
        captured: list[str] = []
        monkeypatch.setattr(config_io.logger, "error", lambda msg, *a, **k: captured.append(str(msg)))
        sleeps: list[float] = []

        def stop_after_recording(_seconds: float) -> None:
            sleeps.append(_seconds)
            raise _StopBackupLoop

        monkeypatch.setattr(config_io, "time", types.SimpleNamespace(sleep=stop_after_recording))
        with pytest.raises(_StopBackupLoop):
            config_io.backup_file_start()
        assert any("备份配置文件失败" in m for m in captured)
        assert sleeps == [600], "异常路径也必须按节拍等待（否则退化成紧循环）"


class TestParserHelpers:
    # _safe_int / _safe_float / read_config_bool 是「配置值不会把启动带崩」的唯一防线：
    # 非法值必须回退到默认并留一条告警，而不是抛 ValueError 让主循环死在 import 阶段。
    def test_safe_int_and_float_fallbacks(self) -> None:
        assert config_io._safe_int(" 12 ", 5) == 12
        assert config_io._safe_int("", 5) == 5
        assert config_io._safe_int(None, 5) == 5
        assert config_io._safe_float("1.5", 0.5) == 1.5
        assert config_io._safe_float("oops", 0.5) == 0.5
        assert config_io._safe_float(None, 0.5) == 0.5

    def test_read_config_bool_uses_string_default_as_writeback(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(main, "config_file", str(tmp_path / "config.ini"))
        monkeypatch.setattr(main, "file_update_lock", threading.Lock())
        monkeypatch.setattr(config_io, "_atomic_write_text", lambda *_a, **_k: True)
        parser = configparser.RawConfigParser()
        assert config_io.read_config_bool(parser, "录制设置", "只开启粉丝弹幕", default=True) is True
        parser2 = configparser.RawConfigParser()
        parser2.read_string("[录制设置]\n只开启粉丝弹幕 = 否\n")
        assert config_io.read_config_bool(parser2, "录制设置", "只开启粉丝弹幕") is False
