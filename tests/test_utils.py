# Tests for src/utils.py - utility function tests for coverage improvement.

import builtins
import os
import tempfile
import zipfile
from pathlib import Path
from typing import IO, Any

import pytest

from src.utils import (
    ProgramError,
    check_disk_capacity,
    check_md5,
    dict_to_cookie_str,
    get_file_paths,
    get_query_params,
    handle_proxy_addr,
    jsonp_to_json,
    read_config_value,
    remove_duplicate_lines,
    remove_emojis,
    replace_url,
    trace_error_decorator,
    trace_error_decorator_or_none,
    unzip_file,
    update_config,
)


# 字典转 Cookie 头字符串：把爬虫拿到的 cookie 字典拼成请求头。
# 守卫空/单/多键值三种形态的拼接正确性。
class TestDictToCookieStr:
    # Test dict_to_cookie_str.

    def test_empty_dict(self) -> None:
        assert dict_to_cookie_str({}) == ""

    # 单键值须拼成 "k=v" 单一片段
    def test_single_cookie(self) -> None:
        assert dict_to_cookie_str({"key": "value"}) == "key=value"

    # 多键值须全部出现并以 "; " 连接（顺序无关但分隔符固定）
    def test_multiple_cookies(self) -> None:
        result = dict_to_cookie_str({"a": "1", "b": "2"})
        assert "a=1" in result
        assert "b=2" in result
        assert "; " in result


class TestCheckMd5:
    # Test check_md5.

    def test_returns_md5(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world", encoding="utf-8")
        result = check_md5(test_file)
        assert len(result) == 32
        assert result.isalnum()

    def test_same_content_same_md5(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("same content", encoding="utf-8")
        f2.write_text("same content", encoding="utf-8")
        assert check_md5(f1) == check_md5(f2)


class TestCheckDiskCapacity:
    # Test check_disk_capacity.

    def test_returns_positive_float(self, tmp_path: Path) -> None:
        # 磁盘容量查询返回正浮点（字节数），负值/异常代表挂载失败（录制前需据此告警）
        result = check_disk_capacity(str(tmp_path))
        assert isinstance(result, float)
        assert result > 0

    # show=True 时须打印 Total/Free 信息，供用户在 UI 确认剩余空间
    def test_with_show(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        result = check_disk_capacity(str(tmp_path), show=True)
        captured = capsys.readouterr()
        assert "Total" in captured.out
        assert "Free" in captured.out
        assert isinstance(result, float)


class TestRemoveDuplicateLines:
    # Test remove_duplicate_lines.

    # 连续/间隔重复行须去重且仅保留首次出现顺序，编码用 utf-8-sig 兼容 BOM
    def test_removes_duplicates(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("line1\nline2\nline1\nline3\nline2\n", encoding="utf-8-sig")
        remove_duplicate_lines(test_file)
        content = test_file.read_text(encoding="utf-8-sig")
        lines = [l for l in content.strip().split("\n") if l]
        assert len(lines) == 3
        assert "line1" in lines
        assert "line2" in lines
        assert "line3" in lines


class TestReadConfigValue:
    # Test read_config_value.

    # 存在的 section/key 须返回原始字符串值
    def test_read_existing_key(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.ini"
        config_file.write_text("[section1]\nkey1 = value1\n", encoding="utf-8-sig")
        result = read_config_value(config_file, "section1", "key1")
        assert result == "value1"

    def test_read_missing_key(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        config_file = tmp_path / "config.ini"
        config_file.write_text("[section1]\nkey1 = value1\n", encoding="utf-8-sig")
        result = read_config_value(config_file, "section1", "missing_key")
        assert result is None
        captured = capsys.readouterr()
        assert "does not exist" in captured.out

    # 缺失 section 须返回 None 并提示，与缺失 key 同处理
    def test_read_missing_section(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        config_file = tmp_path / "config.ini"
        config_file.write_text("[section1]\nkey1 = value1\n", encoding="utf-8-sig")
        result = read_config_value(config_file, "missing_section", "key1")
        assert result is None
        captured = capsys.readouterr()
        assert "does not exist" in captured.out

    # read_config_value 关闭 BasicInterpolation：含 % 的值（cookie/URL 编码）不应抛异常（批次5修复）.
    def test_percent_value_readable(self, tmp_path: Path) -> None:
        # % 在 ini 默认插值中是特殊字符（BasicInterpolation 会解析 %(x)s），关闭后含 % 的 cookie/URL 才能原样读出
        cfg = tmp_path / "c.ini"
        cfg.write_text("[s]\nk = 100%x\n", encoding="utf-8")
        assert read_config_value(cfg, "s", "k") == "100%x"

    def test_missing_key_returns_none(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        cfg = tmp_path / "c.ini"
        cfg.write_text("[s]\nk = v\n", encoding="utf-8")
        assert read_config_value(cfg, "s", "nope") is None
        _ = capsys.readouterr()  # 吞掉提示输出


class TestUpdateConfig:
    # Test update_config.

    def test_update_existing_key(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        config_file = tmp_path / "config.ini"
        config_file.write_text("[section1]\nkey1 = old_value\n", encoding="utf-8-sig")
        update_config(config_file, "section1", "key1", "new_value")
        result = read_config_value(config_file, "section1", "key1")
        assert result == "new_value"
        captured = capsys.readouterr()
        assert "updated" in captured.out

    def test_update_missing_section(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        config_file = tmp_path / "config.ini"
        config_file.write_text("[section1]\nkey1 = value1\n", encoding="utf-8-sig")
        update_config(config_file, "missing_section", "key1", "new_value")
        captured = capsys.readouterr()
        assert "does not exist" in captured.out


class TestGetFilePaths:
    # Test get_file_paths.

    # 须递归列出目录下所有文件（含子目录），返回数量与路径匹配
    def test_returns_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_text("hello")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.txt").write_text("world")
        result = get_file_paths(str(tmp_path))
        assert len(result) == 2
        assert any("a.txt" in p for p in result)
        assert any("b.txt" in p for p in result)

    def test_empty_directory(self, tmp_path: Path) -> None:
        result = get_file_paths(str(tmp_path))
        assert result == []


class TestRemoveEmojis:
    # Test remove_emojis.

    # 无 emoji 文本须原样返回，不引入多余空白
    def test_no_emojis(self) -> None:
        assert remove_emojis("hello world") == "hello world"

    def test_with_emojis(self) -> None:
        # \U0001f600 为笑脸 emoji（多字节），验证其被剥离而非残留乱码或报错
        result = remove_emojis("hello \U0001f600 world")
        assert result == "hello  world"

    def test_replace_text(self) -> None:
        # 提供 replace 参数时 emoji 被替换为占位串而非删除，保留文本长度结构
        result = remove_emojis("hello \U0001f600", "[emoji]")
        assert result == "hello [emoji]"


# handle_proxy_addr 规范化代理地址，补齐 http 前缀。
# 守卫 None/空/有无前缀四种输入。
class TestHandleProxyAddr:
    # Test handle_proxy_addr.

    # None 代理须返回 None，避免把 None 当字符串传给 requests
    def test_none_returns_none(self) -> None:
        assert handle_proxy_addr(None) is None

    def test_empty_returns_none(self) -> None:
        # 空串代理视为未配置，返回 None（不应把空串当地址传给 requests）
        assert handle_proxy_addr("") is None

    def test_no_prefix_adds_http(self) -> None:
        assert handle_proxy_addr("127.0.0.1:8080") == "http://127.0.0.1:8080"

    def test_with_prefix_kept(self) -> None:
        assert handle_proxy_addr("https://proxy.com:1080") == "https://proxy.com:1080"


class TestJsonpToJson:
    # Test jsonp_to_json.

    def test_valid_jsonp(self) -> None:
        # 标准 callback({...}) 包裹的 JSONP 须正确提取为 dict
        jsonp = 'callback({"key": "value"});'
        result = jsonp_to_json(jsonp)
        assert result == {"key": "value"}

    def test_dotted_callback_name(self) -> None:
        # 回调名可含点号（命名空间，如 namespace.callback），正则须能匹配带点的名字
        jsonp = 'a.b.callback({"a": 1});'
        result = jsonp_to_json(jsonp)
        assert result == {"a": 1}

    def test_no_callback_raises(self) -> None:
        # 无法定位 callback(...) 包裹的 JSON 时必须抛 "No JSON data" 异常，而非返回 None 误导调用方
        with pytest.raises(Exception, match="No JSON data"):
            jsonp_to_json("not a jsonp string")


class TestReplaceUrl:
    # Test replace_url.

    # 整行即 URL 时须整行替换为新地址
    def test_replace_exact_line(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("https://old.com/stream\nother line\n", encoding="utf-8-sig")
        replace_url(f, "https://old.com/stream", "https://new.com/stream")
        content = f.read_text(encoding="utf-8-sig")
        assert "https://new.com/stream" in content

    def test_replace_inline(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("url = https://old.com/live\n", encoding="utf-8-sig")
        replace_url(f, "https://old.com/live", "https://new.com/live")
        content = f.read_text(encoding="utf-8-sig")
        assert "https://new.com/live" in content

    def test_no_match_unchanged(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("unrelated content\n", encoding="utf-8-sig")
        replace_url(f, "https://old.com", "https://new.com")
        content = f.read_text(encoding="utf-8-sig")
        assert "unrelated content" in content


# get_query_params 解析 URL query 参数，支持按 key 过滤。
# 守卫全量/单 key/缺失三种查询。
class TestGetQueryParams:
    # Test get_query_params.

    def test_all_params(self) -> None:
        result = get_query_params("https://example.com?a=1&b=2", None)
        assert "a" in result
        assert "b" in result

    # 指定 key 时只返回该 key 对应的值列表（支持多值）
    def test_specific_param(self) -> None:
        result = get_query_params("https://example.com?a=1&b=2", "a")
        assert result == ["1"]

    # 缺失的 key 须返回空列表而非 None 或抛出异常
    def test_missing_param(self) -> None:
        result = get_query_params("https://example.com?a=1", "missing")
        assert result == []


class TestTraceErrorGuard:
    # Test trace_error_decorator / trace_error_decorator_or_none（同步路径此前完全未覆盖）。

    # 同步正常路径：无异常时原样返回，不得落入任何兜底分支
    def test_sync_success(self) -> None:
        @trace_error_decorator
        def ok() -> dict[str, bool]:
            return {"is_live": True}

        assert ok() == {"is_live": True}

    # 同步 ProgramError（Node 环境缺失等 JS 执行失败）：吞异常返回 fallback，而非向调用方抛出
    def test_sync_program_error(self) -> None:
        @trace_error_decorator_or_none
        def boom() -> str:
            raise ProgramError("node missing")

        assert boom() is None

    # 同步任意异常：同样吞掉返回 fallback，把「崩溃」降级为「未开播/空结果」语义
    def test_sync_generic_error(self) -> None:
        @trace_error_decorator_or_none
        def boom() -> str:
            raise RuntimeError("disk gone")

        assert boom() is None

    # 异步包装器的 ProgramError 分支与同步是独立代码路径，须单独守卫
    async def test_async_program_error(self) -> None:
        @trace_error_decorator_or_none
        async def boom() -> str:
            raise ProgramError("node missing")

        assert await boom() is None


class TestUnzipFile:
    # Test unzip_file.

    # 正常解压：文件落位，且默认 delete=True 时源 zip 被清理（node/ffmpeg 安装缓存场景）
    def test_unzip_and_delete(self, tmp_path: Path) -> None:
        zip_file = tmp_path / "pkg.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("inner.txt", "payload")
        dest = tmp_path / "out"
        unzip_file(zip_file, dest)
        assert (dest / "inner.txt").read_text(encoding="utf-8") == "payload"
        assert not zip_file.exists()

    # delete=False 保留源 zip（共享缓存复用场景）
    def test_keep_zip_when_delete_false(self, tmp_path: Path) -> None:
        zip_file = tmp_path / "pkg.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("a.txt", "1")
        dest = tmp_path / "out"
        unzip_file(zip_file, dest, delete=False)
        assert (dest / "a.txt").exists()
        assert zip_file.exists()

    # Zip Slip 目录穿越必须被拒绝：成员经 ../ 逃逸出目标目录时抛 ValueError 且不落盘
    def test_zip_slip_rejected(self, tmp_path: Path) -> None:
        zip_file = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("../escape.txt", "pwn")
        dest = tmp_path / "out"
        with pytest.raises(ValueError, match="Unsafe path"):
            unzip_file(zip_file, dest)
        assert not (dest / "escape.txt").exists()


class TestReadConfigValueErrors:
    # Test read_config_value 异常兜底。

    # ini 内容非法（缺 section 头）时 config.read 抛解析异常 → 必须返回 None 并打印原因，
    # 而非让解析异常击穿调用方（注意：目录路径等 OSError 会被 configparser.read 吞掉，走不到这里）
    def test_invalid_ini_returns_none(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        bad_file = tmp_path / "bad.ini"
        bad_file.write_text("no_section_header = oops\n", encoding="utf-8")
        assert read_config_value(bad_file, "s", "k") is None
        assert "Error occurred while reading" in capsys.readouterr().out


class TestUpdateConfigErrors:
    # Test update_config 异常兜底。

    # ini 内容非法时读取阶段失败 → 直接返回，目标文件内容保持原样
    def test_invalid_ini_returns_early(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        cfg = tmp_path / "bad.ini"
        cfg.write_text("no_section_header = oops\n", encoding="utf-8")
        update_config(cfg, "s", "k", "v")
        assert "An error occurred while reading" in capsys.readouterr().out
        assert cfg.read_text(encoding="utf-8") == "no_section_header = oops\n"

    # 写失败（只读文件）必须被捕获并打印原因，源内容保留——只读目录盘满等场景不应崩掉录制流程
    def test_readonly_file_write_failure(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        cfg = tmp_path / "cfg.ini"
        cfg.write_text("[s]\nk = old\n", encoding="utf-8")
        cfg.chmod(0o444)
        try:
            update_config(cfg, "s", "k", "new")
            assert "Error occurred while writing" in capsys.readouterr().out
            assert "k = old" in cfg.read_text(encoding="utf-8")
        finally:
            cfg.chmod(0o644)  # 恢复可写，避免 pytest 清理 tmp_path 时因只读残留


class TestRemoveDuplicateLinesEncodingFallback:
    # Test remove_duplicate_lines 的编码回退路径。

    # utf-8-sig 读取撞上 UnicodeDecodeError → 须回退系统默认编码重读且去重结果正确。
    # 用 monkeypatch 模拟解码失败而非写真 GBK 字节：GBK 内容在 Linux CI（默认 UTF-8）
    # 的回退读取会二次炸掉，无法做出跨平台稳定的用例；纯 ASCII 内容在任何默认编码下一致。
    def test_fallback_on_unicode_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        real_open = builtins.open

        # 只拦截 utf-8-sig 读：回退读（encoding=None）与回写（mode 含 w）必须放行走真 open
        def fake_open(file: Any, mode: str = "r", **kwargs: Any) -> IO[Any]:
            if "r" in mode and kwargs.get("encoding") == "utf-8-sig":
                raise UnicodeDecodeError("utf-8-sig", b"\xff", 0, 1, "simulated decode failure")
            return real_open(file, mode, **kwargs)

        monkeypatch.setattr(builtins, "open", fake_open)

        test_file = tmp_path / "dup.txt"
        test_file.write_text("alpha\nalpha\nbeta\n", encoding="ascii")
        remove_duplicate_lines(test_file)
        # 用 bytes 解码绕开被 patch 的 open，utf-8-sig 同时剥掉回写产生的 BOM
        content = test_file.read_bytes().decode("utf-8-sig")
        assert content.split() == ["alpha", "beta"]
