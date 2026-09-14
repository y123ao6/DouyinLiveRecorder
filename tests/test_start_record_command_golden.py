# 黄金样本测试：在 F-01（start_record 五条 ffmpeg 命令构造路径统一）重构之前，
# 先把当前「逐分支内联构造」产出的 ffmpeg 命令行逐字节冻结成基准快照。
#
# 设计要点：
# - 不改动 main.py 任何命令构造逻辑；本测试只「驱动」start_record 并捕获其产出的 ffmpeg_command。
# - 所有模块级配置全局量（在 main() 中赋值，import 时并不存在）由本 harness 显式钉死。
# - 网络/IO（_resolve_platform_stream / select_source_url / get_record_headers /
#   get_record_user_agent / check_subprocess / direct_download_stream / danmaku hub）
#   全部 mock，避免任何真实请求与磁盘/子进程副作用。
# - 时间冻结：datetime.today()/now() 与 time.strftime/localtime/sleep 全部替换为固定值，
#   使文件名中的时间戳确定，从而命令可逐字节比对。
# - 捕获点在 check_subprocess（5 条 ffmpeg 路径）与 direct_download_stream（直下 FLV 路径）。
#
# 用法：
#   GOLDEN_REGEN=1 python -m pytest tests/test_start_record_command_golden.py -q   # 重新生成基准
#   python -m pytest tests/test_start_record_command_golden.py -q                  # 比对基准（重构后回归）
#
# 重构 F-01 后，重跑普通模式，若任一命令与基准不符即说明行为被改动——必须回到「等价重构」。

import datetime
import json
import os
import sys
import threading
from collections.abc import Generator
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_GOLDEN_PATH = Path(__file__).resolve().parent / "golden" / "start_record_commands.json"
_REGEN = bool(os.environ.get("GOLDEN_REGEN"))

# 冻结时间：所有时间戳统一为这一刻（真实 strftime 保证确定性，且各分支格式差异被如实保留）。
_FIXED = datetime.datetime(2026, 9, 13, 12, 0, 0)

# select_source_url 字典字面量里引用的全部 Cookie 全局量（main() 中赋值，import 时不存在）。
_COOKIE_GLOBALS = [
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
]


@pytest.fixture(scope="module")
def main_mod() -> ModuleType:
    # 与 test_main_fixes 一致：导入前把 sys.argv[0] 钉到 main.py，否则 _app_root 解析错路径。
    old_argv = sys.argv[:]
    sys.argv = [str(_REPO_ROOT / "main.py")]
    try:
        import main

        return main
    finally:
        sys.argv = old_argv


# 收集 start_record 在某次调用中产出的 ffmpeg 命令 / 直下下载参数
# （原为类 docstring，与 AGENTS.md「注释统一 # 行注释、禁三引号 docstring」冲突，
# scripts/check_annotations.py 会判违规；改为行注释，语义不变）
class _Cap:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.downloads: list[dict] = []


# 用例默认值：20 个用例里大多数字段相同，用「默认 + 覆盖」构造，避免 20 份复制粘贴的
# 字面量（也顺带满足 black 的行宽/换行规则，无需把每个字典逐键展开）。
# 新增用例只需列出与默认值不同的字段；默认值本身不得随意改动——改动等于改动基准语义。
_CASE_DEFAULTS = {
    "anchor_name": "测试主播",
    "quality": "原画",
    "platform": "抖音直播",
    "record_url": "https://live.douyin.com/123",
    "real_url": "http://pull.douyin.com/123.flv",
    "flv_url": "http://other.flv",
    "save_type": "TS",
    "split": False,
}


def _case(case_id: str, **overrides: Any) -> dict[str, Any]:
    # 构造一条用例：defaults 覆盖顺序在后，case_id 作为黄金基准的键名
    case = dict(_CASE_DEFAULTS)
    case.update(overrides)
    case["id"] = case_id
    return case


def _build_cases() -> list[dict[str, Any]]:
    # 用例清单按「分支」分组，组间空行 + 注释标明该组要锁住的行为不变量
    cases = [
        # —— TS（else 分支）：非分段 / 分段 / m3u8（删 -reconnect_at_eof）——
        _case("ts_plain"),
        _case("ts_seg", split=True),
        _case("ts_m3u8", real_url="http://pull.douyin.com/123.m3u8"),
        _case("ts_m3u8_seg", real_url="http://pull.douyin.com/123.m3u8", split=True),
        # —— 海外 + https + 关闭证书校验：超时时长放大 + -tls_verify 0 ——
        _case(
            "ts_overseas_https",
            platform="TikTok直播",
            record_url="https://www.tiktok.com/@user/live",
            real_url="https://pull.tiktok.com/stream.m3u8",
            overseas=["tiktok.com"],
            ssl_off=True,
        ),
        # —— FLV（ffmpeg 分支，非直下）：非分段 / 分段 ——
        _case("flv_ffmpeg", save_type="FLV"),
        _case("flv_ffmpeg_seg", save_type="FLV", split=True),
        # —— MKV ——
        _case("mkv", save_type="MKV"),
        _case("mkv_seg", save_type="MKV", split=True),
        # —— MP4 ——
        _case("mp4", save_type="MP4"),
        _case("mp4_seg", save_type="MP4", split=True),
        # —— 音频：MP3（保存类型含 MP3）/ M4A ——
        _case("mp3", save_type="MP3"),
        _case("mp3_seg", save_type="MP3", split=True),
        _case("m4a", save_type="M4A"),
        _case("m4a_seg", save_type="M4A", split=True),
        # —— 纯音频平台（猫耳FM）：only_audio_record=True，保存类型为 TS → 走音频分支 .m4a ——
        _case(
            "audio_only_platform",
            platform="猫耳FM直播",
            record_url="https://fm.missevan.com/live/1",
            real_url="http://pull.missevan.com/1.flv",
        ),
        # —— 代理：注入 -http_proxy ——
        _case(
            "proxy",
            record_url="https://live.douyin.com/123?plat=抖音直播",
            proxy="http://127.0.0.1:8888",
        ),
        # —— 请求头：注入 -headers ——
        _case("headers", save_type="MP4", headers=True),
        # —— FLV h265 → 强制 TS（P0 事故区：段容器必须为 mpegts 而非 ipod）——
        _case(
            "h265_flv_to_ts",
            real_url="http://pull.douyin.com/123.flv?codec=h265",
            flv_url="http://pull.douyin.com/123.flv?codec=h265",
            save_type="FLV",
        ),
        # —— 直下 FLV（shopee/花椒）：不经 check_subprocess，捕获下载参数 ——
        _case(
            "direct_flv_download",
            platform="shopee",
            record_url="https://shopee.com/live/1",
            real_url="http://pull.shopee.com/1.flv",
            flv_url="http://pull.shopee.com/1.flv",
            save_type="FLV",
        ),
    ]
    return cases


_CASES = _build_cases()
_GOLDEN_IDS = [c["id"] for c in _CASES]


def _setup_case(main: ModuleType, monkeypatch: pytest.MonkeyPatch, case: dict[str, Any]) -> _Cap:
    cap = _Cap()

    # —— 钉死所有录制状态 / 配置全局量 ——
    plain = {
        "exit_recording": False,
        "recording_enabled": True,
        "recording": set(),
        "recording_time_list": {},
        "record_state_lock": threading.Lock(),
        "need_update_line_list": [],
        "not_record_list": [],
        "error_window": [],
        "url_comments": set(),
        "scheduler": None,
        "auto_update_anchor_name": False,
        "show_url": False,
        "live_status_push": False,
        "begin_show_push": False,
        "over_show_push": False,
        "over_push_message_text": "",
        "begin_push_message_text": "",
        "disable_record": False,
        "push_check_seconds": 0,
        "create_time_file": False,
        "converts_to_mp4": False,
        "delete_origin_file": False,
        "custom_script": "",
        "video_save_path": "",
        "folder_by_author": False,
        "folder_by_time": False,
        "folder_by_title": False,
        "filename_by_title": False,
        "default_path": "/recordings",
        "enable_https_recording": False,
        "loop_time": False,
        "delay_default": 0,
        "video_save_type": case["save_type"],
        "split_video_by_time": case["split"],
        "split_time": "600",
        "proxy_addr": case.get("proxy", ""),
        "proxy_addr_bak": "",
        "enable_proxy_platform_list": ["抖音直播"] if case.get("proxy") else [],
        "extra_enable_proxy_platform_list": [],
        "OVERSEAS_PLATFORM_HOST": case.get("overseas", []),
        "color_obj": MagicMock(),
    }
    for name, value in plain.items():
        monkeypatch.setattr(main, name, value, raising=False)

    for ck in _COOKIE_GLOBALS:
        monkeypatch.setattr(main, ck, "", raising=False)

        # ssl 校验裁决：main.py 在 get_effective_ssl_verify 返回 False（校验关闭）时才插入
        # -tls_verify 0。故 ssl_off=True 应让该接口返回 False。
        monkeypatch.setattr(
            main._http_config,
            "get_effective_ssl_verify",
            lambda platform: not bool(case.get("ssl_off", False)),
        )

    # —— 冻结时间 ——
    # 注意：真实 datetime.strftime 内部会回调 time.strftime；若把 time.strftime 直接转发给
    # _FIXED.strftime 会形成「_FIXED.strftime → time.strftime → _FIXED.strftime」无限递归
    # （实测 Stack overflow）。故此处捕获「原始」time.strftime，并以固定 timetuple 喂入，
    # 既保证确定性（格式相关，各分支真实时间戳差异被如实保留），又切断递归。
    import time as _time

    _orig_strftime = _time.strftime  # 必须在 Patch 之前捕获原始实现
    _fixed_tt = _FIXED.timetuple()
    monkeypatch.setattr(main.time, "strftime", lambda fmt, t=None: _orig_strftime(fmt, _fixed_tt))
    monkeypatch.setattr(main.time, "localtime", lambda t=None: _fixed_tt)
    monkeypatch.setattr(main.time, "sleep", lambda *a, **k: None)
    monkeypatch.setattr(main.time, "time", lambda: 1_000_000.0)

    class _FrozenDateTime(datetime.datetime):
        # 返回类型标 Any：typeshed 中 datetime.now/today 返回 Self，标具体类型会触发
        # override 不兼容告警（测试内冻结类，无需精确覆写签名）
        @classmethod
        def today(cls) -> Any:
            return _FIXED

        @classmethod
        def now(cls, tz: datetime.tzinfo | None = None) -> Any:
            return _FIXED

    # datetime.datetime 是 C 类型，不能 setattr 类方法；整体替换为冻结子类。
    monkeypatch.setattr(main.datetime, "datetime", _FrozenDateTime)

    # 所有文件系统副作用：makedirs 变 no-op，full_path 仅为确定字符串
    monkeypatch.setattr(main.os, "makedirs", lambda *a, **k: None)

    # —— mock 网络 / IO ——
    port_info = {
        "is_live": True,
        "anchor_name": case["anchor_name"],
        "title": "",
        "m3u8_url": case["real_url"],
        "flv_url": case["flv_url"],
        "actual_quality": None,
    }

    monkeypatch.setattr(
        main,
        "_resolve_platform_stream",
        lambda *a, **k: (case["platform"], port_info, None, ""),
    )
    monkeypatch.setattr(
        main,
        "select_source_url",
        lambda *a, **k: case["real_url"],
    )
    monkeypatch.setattr(
        main,
        "get_record_headers",
        lambda *a, **k: ({"Referer": "http://example.com", "Cookie": "a=b"} if case.get("headers") else None),
    )
    # 返回 None → 走默认移动端 UA（确定性）
    monkeypatch.setattr(main, "get_record_user_agent", lambda *a, **k: None)

    def _check(
        record_name: str,
        record_url: str,
        ffmpeg_command: list[str],
        record_save_type: str,
        custom_script: str,
        platform: str | None = None,
        danmaku_args: dict[str, Any] | None = None,
    ) -> bool:
        cap.commands.append(list(ffmpeg_command))
        return True  # comment_end=True → 触发 if comment_end: return，干净退出

    monkeypatch.setattr(main, "check_subprocess", _check)
    monkeypatch.setattr(main, "record_success", lambda *a, **k: None)
    monkeypatch.setattr(main, "record_error", lambda *a, **k: None)

    def _dl(
        flv_url: str,
        save_file_path: str,
        record_name: str,
        record_url: str,
        platform: str,
        cookies: str | None = None,
    ) -> bool:
        cap.downloads.append(
            {
                "flv_url": flv_url,
                "save_file_path": save_file_path,
                "record_name": record_name,
                "record_url": record_url,
                "platform": platform,
            }
        )
        # 用 setattr 而非 main.exit_recording = ...：main 已标注为 ModuleType，
        # 直接属性赋值会被 mypy 判 attr-defined（该全局量在 main() 中才绑定）
        setattr(main, "exit_recording", True)  # 直下路径无 check_subprocess，靠退出标志干净退出
        return True

    monkeypatch.setattr(main, "direct_download_stream", _dl)
    # TS 非分段分支会无条件起一个非 daemon 线程跑 converts_mp4（真实函数会卡在假路径上），
    # 这里直接 no-op，避免 pytest 等待该线程导致挂死。
    monkeypatch.setattr(main, "converts_mp4", lambda *a, **k: None)

    # 退出时房间清理：hub 调用 no-op
    import src.danmaku_monitor as _dm

    monkeypatch.setattr(_dm, "get_hub", lambda: MagicMock())
    # conftest 已把 _hub 设为 hermetic；此处再兜底，防止 finally 真连
    if hasattr(_dm, "_hub"):
        monkeypatch.setattr(_dm, "_hub", MagicMock(), raising=False)

    # logger.error 在 start_record 的 except 中被调用且 loguru 队列会卡死，
    # 这里同步落盘以便看到真实异常（排查循环根因用）。
    def _sync_err(msg: object, *a: Any, **k: Any) -> None:
        try:
            import traceback as _tb

            with open("D:/DouyinLiveRecorder-dev/tests/_exc.log", "w", encoding="utf-8") as _f:
                _f.write(str(msg) + "\n")
                _tb.print_exc(file=_f)
        except Exception:
            pass

    monkeypatch.setattr(main.logger, "error", _sync_err)
    monkeypatch.setattr(main.logger, "warning", _sync_err)
    # 真实异常会被 start_record 内部 except 吞掉并无限循环；让 record_error 触发退出标志，
    # 使循环在首个异常后干净退出，便于读取 _exc.log 中的真实异常。
    monkeypatch.setattr(main, "record_error", lambda *a, **k: setattr(main, "exit_recording", True))

    return cap


def _actual_of(case: dict[str, Any], cap: _Cap) -> dict[str, Any]:
    if case["platform"] in ("shopee", "花椒直播"):
        return {"download": cap.downloads[0]} if cap.downloads else {"download": None}
    return {"command": cap.commands[0]} if cap.commands else {"command": None}


@pytest.fixture(scope="session", autouse=True)
def _write_golden(request: pytest.FixtureRequest) -> Generator[None]:
    yield
    if _REGEN:
        _GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        _GOLDEN_PATH.write_text(json.dumps(_REGEN_DICT, ensure_ascii=False, indent=2), encoding="utf-8")


_REGEN_DICT: dict = {}


@pytest.mark.parametrize("case", _CASES, ids=_GOLDEN_IDS)
def test_start_record_command_golden(
    main_mod: ModuleType, monkeypatch: pytest.MonkeyPatch, case: dict[str, Any]
) -> None:
    cap = _setup_case(main_mod, monkeypatch, case)
    main_mod.start_record((case["quality"], case["record_url"], case["anchor_name"]))
    actual = _actual_of(case, cap)

    if _REGEN:
        _REGEN_DICT[case["id"]] = actual
        return

    if not _GOLDEN_PATH.exists():
        pytest.fail(f"黄金基准文件缺失：{_GOLDEN_PATH}（先以 GOLDEN_REGEN=1 生成）")
    golden = json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))
    expected = golden.get(case["id"])
    if expected is None:
        pytest.fail(f"黄金基准缺少用例 {case['id']}（重新 GOLDEN_REGEN=1 生成）")
    assert actual == expected, (
        f"命令与黄金基准不符（用例 {case['id']}）。\n"
        f"  期望: {expected}\n  实际: {actual}\n"
        "若属预期重构，请先 GOLDEN_REGEN=1 重新生成基准。"
    )
