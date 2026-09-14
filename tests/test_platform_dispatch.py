# 平台分发表回归用例（CODE_REVIEW_FIX_1 F-01c）
#
# F-01 把 _resolve_platform_stream 的 60+ 层 elif 链改成了「（匹配器, 处理函数）」分发表。
# 本文件锁定三条契约，防止后续「加平台 / 调顺序」时静默改变平台判定优先级：
#   1. 分发表非空、无重复处理函数、顺序即优先级（前若干项与主平台白名单一致）；
#   2. 每个代表 URL 经分派后得到预期平台名，且走的是预期解析入口（记录 spider/stream 调用）；
#   3. 无法识别的地址返回 None；自定义流地址的扩展名判定大小写不敏感。
#
# 所有 spider / stream 调用均替换为记录型异步桩，用例不发任何真实网络请求。

import sys
import threading
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def main_mod() -> Any:
    # 与 test_start_record_command_golden 一致：导入前把 sys.argv[0] 钉到 main.py，
    # 否则 _app_root() 解析出的路径不对（配置/日志目录会落到别处）。
    old_argv = sys.argv[:]
    sys.argv = [str(_REPO_ROOT / "main.py")]
    try:
        import main

        return main
    finally:
        sys.argv = old_argv


class _RecordingShim:
    # 记录型异步桩：任何属性访问都返回一个「记录调用名与入参、返回空 dict」的协程函数，
    # 既避免真实请求，又能让用例断言「这条 URL 走了哪个解析入口」。
    def __init__(self, tag: str, sink: list) -> None:
        self._tag = tag
        self._sink = sink

    def __getattr__(self, name: str) -> object:
        async def _fake(*args: object, **kwargs: object) -> object:
            self._sink.append((self._tag, name))
            return {}

        return _fake


@pytest.fixture
def dispatch_env(main_mod: Any, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, list]:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(main_mod, "spider", _RecordingShim("spider", calls), raising=False)
    monkeypatch.setattr(main_mod, "stream", _RecordingShim("stream", calls), raising=False)
    # main() 运行期才赋值的全局量：import 期不存在，需补齐否则 NameError
    for name in (
        "dy_cookie",
        "tiktok_cookie",
        "ks_cookie",
        "hy_cookie",
        "douyu_cookie",
        "yy_cookie",
        "bili_cookie",
        "xhs_cookie",
        "bigo_cookie",
        "blued_cookie",
        "sooplive_cookie",
        "netease_cookie",
        "qiandurebo_cookie",
        "pandatv_cookie",
        "maoerfm_cookie",
        "winktv_cookie",
        "flextv_cookie",
        "look_cookie",
        "twitcasting_cookie",
        "baidu_cookie",
        "weibo_cookie",
        "kugou_cookie",
        "liveme_cookie",
        "global_proxy",
    ):
        if not hasattr(main_mod, name):
            monkeypatch.setattr(main_mod, name, "", raising=False)
    if not hasattr(main_mod, "semaphore"):
        monkeypatch.setattr(main_mod, "semaphore", threading.Semaphore(8), raising=False)
    return main_mod, calls


def test_resolver_table_is_wellformed(main_mod: Any) -> None:
    table = main_mod._PLATFORM_RESOLVERS
    # 空表意味着分派链整体丢失（所有地址都会落到「无法识别」）
    assert table, "平台分发表不应为空"
    handlers = [handler for _, handler in table]
    # 处理函数不可重复：重复意味着某个平台分支被登记两次，后一半永远不可达
    assert len(handlers) == len(set(handlers)), "分发表存在重复处理函数"
    # 两个可调用对象缺一即会在分派循环里抛 TypeError
    assert all(callable(matcher) and callable(handler) for matcher, handler in table)


def test_resolver_table_priority_head(main_mod: Any) -> None:
    # 前五项 = 迁移前 elif 链的前五个平台（抖音 / TikTok / 快手 / 虎牙 / 斗鱼）。
    # 顺序即优先级：抖音短链 v.douyin.com 等形态必须最先判定，不能被更宽松的片段抢走。
    names = [handler.__name__ for _, handler in main_mod._PLATFORM_RESOLVERS[:5]]
    assert names == [
        "_resolve_douyin_com",
        "_resolve_tiktok_com",
        "_resolve_live_kuaishou_com",
        "_resolve_huya_com",
        "_resolve_douyu_com",
    ]
    # 自定义流地址必须垫底：它只按扩展名匹配，放前面会截获平台地址
    assert main_mod._PLATFORM_RESOLVERS[-1][1].__name__ == "_resolve_custom_stream"


# （URL, 预期平台名, 预期命中的解析入口）。入口名用于确认「走的是哪条分支」——
# 只断言平台名会漏掉「匹配到了但处理函数被换错」这类错误。
_DISPATCH_CASES = [
    ("https://live.douyin.com/123", "抖音直播", "get_douyin_web_stream_data"),
    ("https://v.douyin.com/abc/", "抖音直播", "get_douyin_app_stream_data"),
    ("https://www.tiktok.com/@u/live", "TikTok直播", "get_tiktok_stream_data"),
    ("https://live.kuaishou.com/u/x", "快手直播", "get_kuaishou_stream_data"),
    ("https://www.huya.com/660002", "虎牙直播", "get_huya_stream_data"),
    ("https://www.douyu.com/9999", "斗鱼直播", "get_douyu_info_data"),
    ("https://live.bilibili.com/1", "B站直播", "get_bilibili_room_info"),
    ("https://www.picarto.tv/x", "Picarto", "get_picarto_stream_url"),
]


@pytest.mark.parametrize("url,expected_platform,expected_entry", _DISPATCH_CASES)
def test_resolve_platform_stream_dispatches(
    dispatch_env: tuple, url: str, expected_platform: str, expected_entry: str
) -> None:
    main_mod, calls = dispatch_env
    # 代理非空才会走 TikTok / LiveMe 等「需要代理」的分支，此处统一带代理避免空转
    result = main_mod._resolve_platform_stream(url, "http://127.0.0.1:1", "原画")
    assert result is not None, f"{url} 应被识别，实际返回 None"
    platform, _port_info, _danmaku, _new_url = result
    assert platform == expected_platform
    assert expected_entry in [name for _tag, name in calls]


def test_resolve_platform_stream_unknown_returns_none(dispatch_env: tuple) -> None:
    main_mod, _calls = dispatch_env
    assert main_mod._resolve_platform_stream("https://example.com/nothing", None, "原画") is None


# 自定义流地址分支：扩展名大小写两种形态都要落到「自定义录制直播」，
# 且按扩展名写入对应的流地址键（flv_url / m3u8_url）。
_CUSTOM_STREAM_CASES = [
    ("https://cdn.example.com/live/1.m3u8", "m3u8_url"),
    # 大写扩展名同样要识别：历史上 find(".m3u8") 大小写敏感导致自定义地址被判「未知链接」
    ("https://cdn.example.com/live/1.M3U8", "m3u8_url"),
    ("http://cdn.example.com/live/1.flv", "flv_url"),
    ("http://cdn.example.com/live/1.FLV", "flv_url"),
]


@pytest.mark.parametrize("url,expected_key", _CUSTOM_STREAM_CASES)
def test_custom_stream_suffix_is_case_insensitive(dispatch_env: tuple, url: str, expected_key: str) -> None:
    main_mod, _calls = dispatch_env
    result = main_mod._resolve_platform_stream(url, None, "原画")
    assert result is not None
    platform, port_info, _danmaku, _new_url = result
    assert platform == "自定义录制直播"
    assert expected_key in port_info


def test_new_platform_entry_can_be_registered(main_mod: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    # 「新平台接入成本」是 F-01 的核心诉求：追加一个处理函数 + 一条表项即可，
    # 不需要进 600 行链里插分支。此处用一个临时表项验证该扩展点确实可用。
    seen: list[str] = []

    def _fake_handler(ctx: Any) -> None:
        seen.append(ctx.record_url)
        ctx.platform = "测试平台"

    monkeypatch.setattr(
        main_mod,
        "_PLATFORM_RESOLVERS",
        ((main_mod._match_host("https://probe.example/"), _fake_handler),),
    )
    result = main_mod._resolve_platform_stream("https://probe.example/room", None, "原画")
    assert result is not None
    assert result[0] == "测试平台"
    assert seen == ["https://probe.example/room"]
