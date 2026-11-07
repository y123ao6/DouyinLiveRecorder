# NO_PROXY 方括号 IPv6 归一化的回归锁（实现单一事实源：src/proxy.py，生产启动期与
# tests/conftest.py 收集前共用 normalize_no_proxy_env）。
#
# 根因（httpx 0.28.1，最新稳定版仍无上游修复可抬）：
#   urllib.getproxies() 把 NO_PROXY 收作 {'no': ...}；httpx._utils.get_environment_proxies
#   逐条目建 bypass 挂载时 is_ipv6_hostname('[::1]') 为 False（ipaddress.IPv6Address 不接受
#   URL 方括号），落入通配兜底分支产出非法挂载键 'all://*[::1]'；Client.__init__ 对每个键
#   建 URLPattern 时端口解析炸出 InvalidURL: Invalid port ':1]'——凡 trust_env=True 且
#   proxy=None 的 Client/AsyncClient 构造即崩（本机实测 41 条用例因此失败）。
#   裸 '::1' 则走正确的 'all://[::1]' bypass 分支，故归一化只去方括号、语义不变。
#   生产侧已双层加固：启动期归一化进程环境 + 全部构造点 trust_env=False 显式解析环境代理
#   （结构锁见 tests/test_proxy.py）；本文件的 conftest 接线锁仍保留——测试进程不一定走
#   生产入口，收集前归一化是测试环境自己的确定性保证。
#
# 变异敏感点：
#   · pytest_configure 里的归一化调用摘掉 → test_pytest_configure_normalizes_both_env_names 红；
#   · normalize_no_proxy_value 改恒等 → 主机值用例 / httpx 见证红；
#   · 未来 httpx 修好该解析 → test_raw_bracketed_value_crashes_httpx 红（提醒收回本守卫，勿留僵尸）。

import os

import httpx
import pytest

from src.proxy import normalize_no_proxy_value
from tests import conftest

# 触发本锁的真实宿主值（curl 风格 NO_PROXY 允许方括号 IPv6）
HOST_NO_PROXY = "localhost,.localhost,127.0.0.1,127.0.0.0/8,[::1],::1"
HOST_NO_PROXY_NORMALIZED = "localhost,.localhost,127.0.0.1,127.0.0.0/8,::1,::1"


def test_normalize_strips_brackets_only_from_valid_ipv6() -> None:
    assert normalize_no_proxy_value(HOST_NO_PROXY) == HOST_NO_PROXY_NORMALIZED


def test_normalize_preserves_non_ipv6_entries() -> None:
    # 域名通配 / IPv4 / CIDR / 带端口方括号 / 非 IP 方括号 / 空条目一律原样：
    # 只有「纯方括号 + 合法 IPv6」才去括号，避免误改不相关条目
    value = "*.example.com,127.0.0.1,192.168.0.0/16,[::1]:8080,[not-an-ip],[127.0.0.1],[deadbeef],,"
    assert normalize_no_proxy_value(value) == value


def test_normalize_strips_entry_whitespace() -> None:
    # httpx 自身按 host.strip() 消费条目，去空格不改 bypass 语义
    assert normalize_no_proxy_value(" [::1] , localhost ") == "::1,localhost"


def test_normalize_is_idempotent() -> None:
    once = normalize_no_proxy_value(HOST_NO_PROXY)
    assert normalize_no_proxy_value(once) == once


def test_pytest_configure_normalizes_both_env_names(monkeypatch: pytest.MonkeyPatch) -> None:
    # 接线锁：pytest_configure 在收集前运行，大小写两个变量名都要归一化
    # （getproxies_environment 对名字 lower() 后取 '_proxy' 前缀，两名等效）。
    # 逐名验证而非同时设置：Windows 环境变量大小写不敏感，两名实为同一键，后写覆盖前写
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.setenv(name, HOST_NO_PROXY)
        conftest.pytest_configure(config=None)
        assert os.environ[name] == HOST_NO_PROXY_NORMALIZED
        monkeypatch.delenv(name)


def test_httpx_client_constructs_and_keeps_ipv6_bypass(monkeypatch: pytest.MonkeyPatch) -> None:
    # 行为见证：归一化后 httpx.Client 可构造，且 ::1 的 bypass 挂载语义保留
    monkeypatch.setenv("NO_PROXY", normalize_no_proxy_value(HOST_NO_PROXY))
    client = httpx.Client()
    try:
        patterns = {p.pattern for p in client._mounts}
        assert "all://[::1]" in patterns
        assert "all://localhost" in patterns
    finally:
        client.close()


def test_raw_bracketed_value_crashes_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    # 根因见证（防守卫僵尸化）：原始宿主值必须真的能炸 httpx 0.28.1；
    # 未来依赖升级修复该解析后本用例转红，即提醒评估收回 conftest 归一化层
    monkeypatch.setenv("NO_PROXY", HOST_NO_PROXY)
    with pytest.raises(httpx.InvalidURL):
        httpx.Client()
