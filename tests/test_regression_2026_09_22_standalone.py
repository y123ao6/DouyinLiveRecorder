# -*- coding: utf-8 -*-
# 2026-09-23 追加：CODE_REVIEW_2026-09-22.md 第十章「孪生副本」语义漂移 + §5.1 副本侧条目的回归锁。
#
# 被测对象是 scripts/douyin_live_recorder_standalone.py —— 它按设计**不 import src/**，
# 是 src/scheduler.py 并发实现与 src/spider.py 部分平台解析的独立副本，因此必须有一份
# 自己的用例（AGENTS「改并发语义必须两处同改、两边注释互相点名」此前只靠注释约束、无机检）。
# 本文件不推断 src/ 侧「应该是什么」，只把副本自身应满足的不变量钉住：
#   MID-2257  PlatformBreaker 的 half-open 回报须经 _probing/_probe_owner 门控——
#             非探针线程 / 租约重授予后的陈旧探针只能入窗口、不得驱动状态迁移；
#             样本窗口须为 deque(maxlen) + 挤出时增量扣减（副本旧实现用 list.pop(0)，持锁 O(n)）；
#   MIN-2259  validate_stream_url 的 .m3u8 判定大小写不敏感（与同文件两处命令构造同口径），
#             且「判走 HLS 分支」的证据是探针序列（HEAD 后紧跟 Range GET），不是返回值；
#   MIN-2201  副本的字母房间号反查须剥引号，非数字/尾斜杠形态不得把坏 roomid 发给接口。
# 另有 --selftest 子进程锁：自检是副本唯一的离线自检入口，新增判据必须真在它里面变绿。
#
# 原则（AGENTS「测试不得自实现被测逻辑」）：只打桩网络层（_fetch_html/_fetch_json/http_probe）
# 与探针限速，熔断状态机、正则、地址拼接一律走副本真实代码。

import ast
import copy
import importlib.util
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_STANDALONE_PATH = _ROOT / "scripts" / "douyin_live_recorder_standalone.py"


def _load_standalone() -> Any:
    # 以模块形式加载单文件副本：其顶层只有常量与函数定义（真网络请求只发生在 main() 里），
    # import 无副作用，故可直接驱动内部函数而不走 CLI。
    spec = importlib.util.spec_from_file_location("dlr_standalone_under_test", _STANDALONE_PATH)
    assert spec and spec.loader, "无法为单文件副本构造 importlib spec"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SA = _load_standalone()


# ────────────────────────────────────────────────────────────
# MID-2257：PlatformBreaker 的 half-open 探针门控
# ────────────────────────────────────────────────────────────


def _open_breaker() -> Any:
    # 阈值与 src/scheduler.py 默认值同形：window=10 / fail_rate=0.5 / MIN_SAMPLES=8
    # → 连打 8 条失败样本必进入 open；cooldown=0 让冷却窗口不干扰用例节奏。
    breaker = SA.PlatformBreaker("t", window=10, fail_rate=0.5, cooldown=0.0)
    for _ in range(8):
        breaker.record(False)
    return breaker


def _report_from_other_thread(breaker: Any, success: bool) -> None:
    # 用真线程制造「另一线程的回报」——归属判据就是线程身份，用 monkeypatch 假造
    # current_thread() 等于把被测逻辑搬进测试自实现，故这里走真实线程。
    worker = threading.Thread(target=lambda: breaker.record(success))
    worker.start()
    worker.join()


class TestStandaloneBreakerProbeGate:
    def test_open_state_grants_probe_on_caller_thread(self) -> None:
        breaker = _open_breaker()
        assert breaker.state == "open", breaker.state
        assert breaker.allow() is True
        assert breaker.state == "half-open", breaker.state

    def test_in_flight_report_from_other_thread_does_not_close(self) -> None:
        # 失效形态（回灌前）：熔断转 half-open 后，一条在熔断前就已放行、此刻才收尾的普通
        # 轮次 record_success 被当成探针结果 → clear() 窗口 + 置 closed →
        # 坏 CDN 立刻重新拿到全部房间流量。
        breaker = _open_breaker()
        assert breaker.allow() is True  # 本线程持有探针
        _report_from_other_thread(breaker, True)
        assert breaker.state == "half-open", "非探针线程的回报驱动了 half-open→closed 迁移"
        # 样本仍照常入窗口（供 closed 态复用阈值判定），只是不得改状态
        assert len(breaker._samples) == 9, breaker._samples

    def test_stale_probe_report_after_regrant_does_not_close(self) -> None:
        # 租约重授予后的**陈旧探针**同样不得替新探针关熔断：先让另一线程重获得探针，
        # 再由第 1 代持有线程回报——此刻它已不是 _probe_owner。
        breaker = _open_breaker()
        breaker.allow()  # 主线程 = 第 1 代持有者
        breaker._granted_at -= SA.PlatformBreaker.LEASE_SECONDS + 1.0  # 免真等 60 秒
        regrant: dict[str, object] = {}
        new_holder = threading.Thread(target=lambda: regrant.__setitem__("granted", breaker.allow()))
        new_holder.start()
        new_holder.join()
        assert regrant.get("granted") is True, regrant
        assert breaker.state == "half-open", breaker.state
        breaker.record(True)  # 第 1 代持有者（本线程）的陈旧回报
        assert breaker.state == "half-open", "陈旧探针的回报关掉了新探针的熔断"

    def test_owner_thread_report_closes_breaker(self) -> None:
        # 反向防线：门控不得把**合法**探针回报也挡掉，否则该 host 永久熔断直到进程重启。
        breaker = _open_breaker()
        assert breaker.allow() is True
        breaker.record(True)
        assert breaker.state == "closed", breaker.state
        assert len(breaker._samples) == 0, breaker._samples

    def test_failed_probe_reopens_breaker(self) -> None:
        # 反向防线：门控不得顺手废掉「探针失败 → 重新熔断」这一步（回灌后 half-open 分支
        # 若整体早退，坏 CDN 会被当成「探针没回报」而永远停在 half-open）。
        breaker = _open_breaker()
        assert breaker.allow() is True
        breaker.record(False)
        assert breaker.state == "open", breaker.state
        assert breaker.allow() is True  # cooldown=0 → 立即可再授予
        assert breaker.state == "half-open", breaker.state
        assert breaker.allow() is False, "half-open 期间必须只放一个探针"

    def test_probe_seq_advances_on_regrant(self) -> None:
        breaker = _open_breaker()
        breaker.allow()
        first = breaker._probe_seq
        breaker._granted_at -= SA.PlatformBreaker.LEASE_SECONDS + 1.0
        breaker.allow()
        assert breaker._probe_seq == first + 1, "重授予未递增探针代数，两代探针无从区分"

    def test_window_is_bounded_deque_with_incremental_count(self) -> None:
        # 副本 _push 此前是 list + pop(0)：满员时在**持锁下**做一次 O(n) 元素搬移，
        # 而 src 早已改成 deque(maxlen) + 增量扣减。这里同时锁容器形态与计数一致性。
        breaker = SA.PlatformBreaker("t", window=5, fail_rate=0.5, cooldown=0.0)
        for i in range(9):
            breaker._push(i % 2)
        assert isinstance(breaker._samples, deque), type(breaker._samples).__name__
        assert breaker._samples.maxlen == 5, breaker._samples.maxlen
        assert len(breaker._samples) == 5
        assert breaker._fail_count == sum(breaker._samples), "挤出样本时未扣减增量计数"


# ────────────────────────────────────────────────────────────
# MIN-2259：validate_stream_url 的容器判定大小写
# ────────────────────────────────────────────────────────────


class TestStandaloneM3u8CaseInsensitive:
    def _probe_with(self, monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
        # 采集**探针调用序列**：判走 HLS 分支的证据不是返回值（HEAD=200 时两条分支都会 True），
        # 而是 HEAD 之后有没有紧跟一次带 Range 的 GET。
        calls: list[tuple[str, str]] = []

        def fake_probe(
            url: str,
            *,
            method: str = "HEAD",
            headers: dict[str, str] | None = None,
            timeout: float = 8.0,
            proxy: str | None = None,
        ) -> Any:
            calls.append((method, (headers or {}).get("Range", "")))
            if method == "HEAD":
                # 多家 CDN 对 m3u8 的 HEAD 恒回 4xx（斗鱼 hw 即 405 + text/html）
                return SA.ProbeResult(405, {"content-type": "text/html"})
            return SA.ProbeResult(206, {"content-type": "application/vnd.apple.mpegurl"})

        monkeypatch.setattr(SA, "http_probe", fake_probe)
        monkeypatch.setattr(SA, "_throttle_probe", lambda url: None)
        monkeypatch.setattr(SA, "_probe_reject_until", {})
        return calls

    @pytest.mark.parametrize("suffix", [".m3u8", ".M3U8", ".M3u8"])
    def test_hls_suffix_reaches_range_get_probe(self, monkeypatch: pytest.MonkeyPatch, suffix: str) -> None:
        # 大写形态此前落进「非 m3u8」分支：content-type 启发式判 text/html → 非末位候选
        # 直接判不可达（探针误杀可用源），整轮回退或放弃录制。
        calls = self._probe_with(monkeypatch)
        ok = SA.validate_stream_url(f"https://cdn.example/live/a{suffix}", platform="斗鱼直播")
        assert ok is True, calls
        assert [m for m, _ in calls] == ["HEAD", "GET"], calls
        assert calls[1][1] == "bytes=0-0", calls

    def test_flv_suffix_does_not_fall_into_hls_branch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 反向防线：统一 lower() 不得把 FLV 也拖进 HLS 分支——HEAD=405 时 FLV 属
        # 「非流媒体 content-type」，应直接定罪而不是补一次 Range GET。
        calls = self._probe_with(monkeypatch)
        ok = SA.validate_stream_url("https://cdn.example/live/a.flv", platform="斗鱼直播")
        assert ok is False, calls
        assert [m for m, _ in calls] == ["HEAD"], calls

    def test_every_function_that_tests_m3u8_also_lowercases(self) -> None:
        # 同文件三处容器判定（校验 1 处 + 两处命令构造）必须同口径。判据按**函数**取：
        # 只要求「该函数里出现过 .lower()」，既允许就地 lower()，也允许 validate 那种
        # 「小写化一次、多个判定复用 url_lower」的写法（探针预算要求少算重复的 lower()）。
        # 走 AST 而非扫文本：注释里也提到 .m3u8，文本比对会把它们数进来。
        tree = ast.parse(_STANDALONE_PATH.read_text(encoding="utf-8"))
        offenders: list[str] = []
        checked = 0
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            body = ast.unparse(fn)
            tests_hls = any(
                isinstance(node, ast.Compare) and isinstance(node.ops[0], ast.In) and ".m3u8" in ast.unparse(node)
                for node in ast.walk(fn)
            )
            if not tests_hls:
                continue
            checked += 1
            if ".lower()" not in body:
                offenders.append(fn.name)
        assert checked >= 3, f".m3u8 判定所在函数少于三处（结构变了须同步本用例）: {checked}"
        assert offenders == [], f"这些函数在大小写敏感的 URL 上判容器: {offenders}"


# ────────────────────────────────────────────────────────────
# MIN-2201（副本侧）：字母房间号反查
# ────────────────────────────────────────────────────────────

_HUYA_OFF = {"data": {"profileInfo": {"nick": "虎牙主播"}, "realLiveStatus": "OFF"}}


class TestStandaloneHuyaLetterRoom:
    def _resolve(
        self,
        monkeypatch: pytest.MonkeyPatch,
        url: str,
        html: str,
    ) -> tuple[Any, list[str]]:
        seen: list[str] = []
        monkeypatch.setattr(SA, "_fetch_html", lambda target, **kw: html)

        def fake_json(api: str, **kw: object) -> dict[str, Any]:
            # 每次返回新副本：resolve_huya 只读，但共享同一 dict 会让某次用例的意外写入
            # 泄漏到后续用例（表现为「单跑绿、全量红」）。
            seen.append(api)
            return copy.deepcopy(_HUYA_OFF)

        monkeypatch.setattr(SA, "_fetch_json", fake_json)
        return SA.resolve_huya(url), seen

    def test_quoted_profile_room_strips_quotes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 页面内联 "ProfileRoom":"6030242"（字符串形态）时非贪婪捕获连引号一起收下，
        # 不剥引号则恒判非数字、白丢微信小程序兜底接口。
        quoted_page = 'x = {"ProfileRoom":"6030242","sPrivateHost":true};'
        info, seen = self._resolve(monkeypatch, "https://www.huya.com/abcroom", quoted_page)
        assert seen, f"未取得数字房间号即放弃兜底: {info.error}"
        assert "roomid=6030242" in seen[0], seen[0]
        assert "%22" not in seen[0], f"引号被当成房间号的一部分发出去了: {seen[0]}"

    def test_trailing_slash_numeric_room_still_requests(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # rstrip("/") 的行为锁：带尾斜杠的数字房间号与不带的必须走同一个 roomid。
        _info, seen = self._resolve(monkeypatch, "https://www.huya.com/6030242/", "")
        assert seen and "roomid=6030242" in seen[0], seen

    def test_regex_miss_does_not_hit_api(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 页面改版取不到 ProfileRoom：不得把字母号原样发给小程序接口，且须留 error 说明。
        info, seen = self._resolve(monkeypatch, "https://www.huya.com/abcroom", "no profile field here")
        assert seen == [], seen
        assert info.error, "未取得数字房间号须有可诊断的 error"


# ────────────────────────────────────────────────────────────
# --selftest：副本唯一的离线自检入口
# ────────────────────────────────────────────────────────────


def _run_selftest() -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(_STANDALONE_PATH), "--selftest"],
        capture_output=True,
        timeout=180,
    )


class TestStandaloneSelftest:
    def test_selftest_passes(self) -> None:
        # 按字节比较，不让解码参与判定（AGENTS「探测子进程输出一律按字节比较」）：
        # 中文 Windows 下让 text=True 读子进程输出曾直接抛 UnicodeDecodeError。
        proc = _run_selftest()
        out = proc.stdout or b""
        assert b"[FAIL]" not in out, out.decode("utf-8", errors="replace")[-2000:]
        assert b"[PASS]" in out, out[-500:]
        assert proc.returncode == 0, out.decode("utf-8", errors="replace")[-2000:]

    def test_selftest_covers_the_backfilled_invariants(self) -> None:
        # 自检脚本不得退化成「只跑老用例」：本轮新增的三条判据必须出现在自检输出里，
        # 否则说明有人把 --selftest 用例如期删掉而 pytest 这边察觉不到。
        out = _run_selftest().stdout or b""
        decoded = out.decode("utf-8", errors="replace")
        for needle in ("非探针线程回报不得关熔断", "陈旧探针回报不得关熔断", "大写 .M3U8"):
            assert needle in decoded, f"selftest 缺少判据 {needle!r}"
