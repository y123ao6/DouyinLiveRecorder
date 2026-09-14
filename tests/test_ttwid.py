# Tests for src/ttwid.py - ttwid module tests for coverage improvement.

import asyncio
import configparser
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.ttwid as ttwid_module
from src.cookie_cache import clear as clear_cookie_cache
from src.ttwid import (
    _app_root,
    _cached_ttwid,
    _fetch_ttwid,
    _read_config_ttwid,
    get_ttwid,
    warmup_ttwid,
)


# _app_root 定位配置根目录：普通运行取脚本旁 config/，frozen 运行取可执行文件目录。
# 正确解析是后续所有配置读取的基础。
class TestAppRoot:
    # Test _app_root.

    def test_returns_string(self) -> None:
        result = _app_root()
        assert isinstance(result, str)
        assert len(result) > 0


# _read_config_ttwid 从 config.ini 读取预置 ttwid：须正确处理前缀、空值、缺失配置。
# 守卫"不写出空/重复前缀 ttwid"的脏数据。
class TestReadConfigTtwid:
    # Test _read_config_ttwid.

    # 配置目录不存在时须返回空串而非抛异常（首次运行/未填 ttwid 配置的常态）
    def test_no_config_returns_empty(self) -> None:
        # 配置目录不存在时须返回空串而非抛异常（首次运行 / 未填 ttwid 配置的常态）
        with patch("src.ttwid._app_root", return_value="/nonexistent/path"):
            result = _read_config_ttwid()
            assert result == ""

    def test_with_config_ttwid(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.ini"
        config_file.write_text("[Cookie]\nttwid = abc123\n", encoding="utf-8-sig")
        with patch("src.ttwid._app_root", return_value=str(tmp_path)):
            result = _read_config_ttwid()
            assert result == "ttwid=abc123"

    def test_with_config_already_prefixed(self, tmp_path: Path) -> None:
        # 配置已带 ttwid= 前缀时不得重复拼接，否则会变成 "ttwid=ttwid=xyz789"
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.ini"
        config_file.write_text("[Cookie]\nttwid = ttwid=xyz789\n", encoding="utf-8-sig")
        with patch("src.ttwid._app_root", return_value=str(tmp_path)):
            result = _read_config_ttwid()
            assert result == "ttwid=xyz789"

    def test_empty_ttwid_returns_empty(self, tmp_path: Path) -> None:
        # ttwid 值为空（占位未填）必须返回空串，避免写出 "ttwid=" 空值被当成有效 cookie
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.ini"
        config_file.write_text("[Cookie]\nttwid = \n", encoding="utf-8-sig")
        with patch("src.ttwid._app_root", return_value=str(tmp_path)):
            result = _read_config_ttwid()
            assert result == ""


class TestFetchTtwid:
    # Test _fetch_ttwid.

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        ttwid_module._cached_ttwid = ""
        clear_cookie_cache()
        # async_req 返回含 ttwid 的 cookies，须拼成 "ttwid=<value>" 并写入模块级缓存
        cookies = {"ttwid": "test_value_123"}
        with patch("src.ttwid.async_req", new_callable=AsyncMock, return_value=cookies):
            result = await _fetch_ttwid()
            assert result == "ttwid=test_value_123"
            assert ttwid_module._cached_ttwid == "ttwid=test_value_123"
        ttwid_module._cached_ttwid = ""

    @pytest.mark.asyncio
    async def test_no_ttwid_in_cookies(self) -> None:
        ttwid_module._cached_ttwid = ""
        clear_cookie_cache()
        # 响应无 ttwid 字段（风控页/异常页）时必须返回空，而非拼出 "ttwid=" 空值伪装成有效
        cookies = {"other": "value"}
        with patch("src.ttwid.async_req", new_callable=AsyncMock, return_value=cookies):
            result = await _fetch_ttwid()
            assert result == ""
        ttwid_module._cached_ttwid = ""

    @pytest.mark.asyncio
    async def test_exception_returns_empty(self) -> None:
        ttwid_module._cached_ttwid = ""
        clear_cookie_cache()
        with patch("src.ttwid.async_req", new_callable=AsyncMock, side_effect=Exception("net")):
            result = await _fetch_ttwid()
            assert result == ""
        ttwid_module._cached_ttwid = ""


class TestGetTtwid:
    # Test get_ttwid.

    @pytest.mark.asyncio
    async def test_cached_returns_directly(self) -> None:
        ttwid_module._cached_ttwid = "ttwid=cached_value"
        result = await get_ttwid()
        assert result == "ttwid=cached_value"
        ttwid_module._cached_ttwid = ""

    @pytest.mark.asyncio
    async def test_reads_config_first(self) -> None:
        ttwid_module._cached_ttwid = ""
        with (
            patch("src.ttwid._read_config_ttwid", return_value="ttwid=from_config"),
            patch("src.ttwid._fetch_ttwid", new_callable=AsyncMock, return_value=""),
        ):
            result = await get_ttwid()
            assert result == "ttwid=from_config"
        ttwid_module._cached_ttwid = ""

    @pytest.mark.asyncio
    async def test_falls_back_to_fetch(self) -> None:
        ttwid_module._cached_ttwid = ""
        with (
            patch("src.ttwid._read_config_ttwid", return_value=""),
            patch("src.ttwid._fetch_ttwid", new_callable=AsyncMock, return_value="ttwid=fetched"),
        ):
            result = await get_ttwid()
            assert result == "ttwid=fetched"
        ttwid_module._cached_ttwid = ""


class TestWarmupTtwid:
    # Test warmup_ttwid.

    def test_success(self) -> None:
        ttwid_module._cached_ttwid = ""
        clear_cookie_cache()
        # warmup 在程序启动时预取并缓存 ttwid，避免首帧录制才拉取造成开播延迟
        # warmup_ttwid calls asyncio.run(get_ttwid()), which internally calls _fetch_ttwid
        # and sets _cached_ttwid. We mock async_req to control _fetch_ttwid's behavior.
        cookies = {"ttwid": "warm_value"}
        with (
            patch("src.ttwid.async_req", new_callable=AsyncMock, return_value=cookies),
            patch("src.ttwid._read_config_ttwid", return_value=""),
        ):
            warmup_ttwid()
            assert ttwid_module._cached_ttwid == "ttwid=warm_value"
        ttwid_module._cached_ttwid = ""

    def test_exception_handled(self) -> None:
        with patch("src.ttwid.get_ttwid", new_callable=AsyncMock, side_effect=Exception("fail")):
            # Should not raise
            warmup_ttwid()


class TestAppRootFrozen:
    # _app_root 的 frozen 分支（PyInstaller 冻结运行）仅在 sys.frozen=True 时执行，
    # 单测默认不触发，这里显式 patch 覆盖，避免该分支永久处于零覆盖。
    # frozen 模式须返回可执行文件所在目录，与开发态（脚本目录）区分
    def test_frozen_returns_exe_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ttwid_module.sys, "frozen", True, raising=False)
        result = _app_root()
        assert isinstance(result, str)
        assert result == os.path.dirname(os.path.realpath(sys.executable))


class TestReadConfigTtwidBroadExcept:
    # _read_config_ttwid 的兜底 broad except：捕获非 configparser 的意外异常并返回 ""。
    def test_unexpected_exception_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class _BoomParser:
            def read(self, *args: object, **kwargs: object) -> list[str]:
                return []

            def get(self, *args: object, **kwargs: object) -> str:
                raise ValueError("unexpected")

        monkeypatch.setattr(ttwid_module.configparser, "RawConfigParser", _BoomParser)
        with patch("src.ttwid._app_root", return_value="/nonexistent"):
            assert _read_config_ttwid() == ""


class TestFetchTtwidException:
    # _fetch_ttwid 内部 _cache_fetch_cookies 抛异常时，须记 warning 并返回 ""（不冒泡）。
    @pytest.mark.asyncio
    async def test_cookie_fetch_raises_logs_warning(self) -> None:
        ttwid_module._cached_ttwid = ""
        # _cache_fetch_cookies 抛异常时须记 warning 并返回空，不冒泡影响录制启动
        with patch(
            "src.ttwid._cache_fetch_cookies",
            new_callable=AsyncMock,
            side_effect=Exception("net down"),
        ):
            result = await _fetch_ttwid()
            assert result == ""
        ttwid_module._cached_ttwid = ""


# get_ttwid 的并发去重语义（2026-09-12 审查 H-2 后改写）
#
# 旧设计：_ttwid_lock 跨越 await 持有，用假锁（acquire 恒 False）模拟"锁被其他线程
#   持有"来覆盖兜底分支。新设计改用 cookie_cache.singleflight（锁内零 await、
#   等待者经 future 复用结果），"锁竞争"场景已不存在，该用例的旧断言随之失效。
#
# 新用例覆盖的才是新设计的核心不变量：并发 N 个 get_ttwid 只打一次 _fetch_ttwid，
#   且所有调用方拿到同一份结果——这正是原实现用锁想保证（但会跨房间阻塞事件循环）
#   的性质。若 singleflight 退化成各自拉取，fetch 次数会 >1，用例失败。
class TestGetTtwidSingleflight:
    @pytest.mark.asyncio
    async def test_concurrent_calls_fetch_once(self) -> None:
        ttwid_module._cached_ttwid = ""
        clear_cookie_cache()

        calls = 0

        async def _fake_fetch(proxy_addr: object = None) -> str:
            nonlocal calls
            calls += 1
            await asyncio.sleep(0.05)  # 制造窗口，让并发调用都能进入等待队列
            return "ttwid=once"

        with (
            patch("src.ttwid._fetch_ttwid", new=_fake_fetch),
            patch("src.ttwid._read_config_ttwid", return_value=""),
        ):
            results = await asyncio.gather(*[get_ttwid() for _ in range(5)])

        assert calls == 1, f"singleflight 去重失效：_fetch_ttwid 被调用 {calls} 次"
        assert all(r == "ttwid=once" for r in results)
        ttwid_module._cached_ttwid = ""

    @pytest.mark.asyncio
    async def test_config_ttwid_bypasses_network(self) -> None:
        # 配置优先：用户手填 ttwid 时不进 singleflight，不发任何网络请求
        ttwid_module._cached_ttwid = ""
        clear_cookie_cache()

        async def _boom(proxy_addr: object = None) -> str:
            raise AssertionError("配置优先时不应发起网络请求")

        with (
            patch("src.ttwid._fetch_ttwid", new=_boom),
            patch("src.ttwid._read_config_ttwid", return_value="ttwid=from_config"),
        ):
            result = await get_ttwid()

        assert result == "ttwid=from_config"
        ttwid_module._cached_ttwid = ""
