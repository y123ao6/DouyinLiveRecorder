# build_exe.py 发布链「运行时二进制来源」的回归用例（2026-09-22 新增）。
#
# 被测面：_FFMPEG_DOWNLOAD_URLS / _ffmpeg_source_url 与 _PINNED_RUNTIME_SHA256 的**键同构**，
# 以及 macOS arm64 下载点缺陷的形态锁。全程离线——不发起网络请求、不下载任何二进制，
# 故「某条 URL 当下是否 200」不进本文件（那属真机验证，实测记录见 CODE_WIKI 更新日志）。
#
# 为什么值得单独锁（本仓缺失的一类失效）：旧实现的 macOS arm64 分支按 `machine` 现场拼 URL
# （`getrelease-arm64/zip`，上游根本没有这个产物），请求 404 → 被 _download_ffmpeg 外层的
# `except Exception` 吞成一行 warning → Apple Silicon 的 full zip **静默不含 ffmpeg**，
# 而构建流程照样报成功、`--dual` 照常出包。三层叠加才让它不可见：
#   ① URL 不在任何清单里（拼出来的，静态检查看不出它指向不存在的端点）；
#   ② 失败被宽泛 except 捕获后只返回 False（组件级降级，不参与总判定）；
#   ③ 发布链没有对「full 包必须含 ffmpeg」做事后校验。
# 本文件锁 ①（URL 只能来自按运行时键分列的表）与表/钉定表的同构关系；②③ 的处置见
# 同日信任策略评审结论，属需审批的生产改动，未在此顺手改。

from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import io
import os
import re
import subprocess
import sys
import tarfile
import types
import zipfile
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent

# evermeet / gyan.dev / BtbN(github) 三家 + nodejs.org 官方 dist：来源清单与
# _FFMPEG_DOWNLOAD_URLS / _download_nodejs 的拼接主机一一对应。
# [2026-09-26] 加入 github.com（Linux ffmpeg 换用 BtbN 的 n9.0 系列资产），同时**移除** johnvansickle.com：
# 该主机不再出现在来源表里，留在清单内等于给一条已退役的来源保留通行证——将来真要再用，
# 必须在这里显式改回来并说明理由（本清单就是那道说明的落点）。
_ALLOWED_HOSTS = frozenset({"www.gyan.dev", "evermeet.ca", "github.com", "nodejs.org"})


def _load_build_exe() -> Any:
    # 与 scripts/check_runtime_pins.py 同一手法：根目录模块不在包路径内，按文件路径显式加载；
    # build_exe 的 import 期只有常量定义（main() 受 __name__ 守卫），故加载无副作用。
    spec = importlib.util.spec_from_file_location("_build_exe_runtime_probe", ROOT / "build_exe.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_exe = _load_build_exe()


def test_ffmpeg_source_table_covers_release_matrix_exactly() -> None:
    # 缺键 = 该平台构建时查不到来源；多键 = 表与矩阵漂移（没人再核对它）。两侧都要拦。
    keys = build_exe.RELEASE_RUNTIME_KEYS
    missing = [k for k in keys if k not in build_exe._FFMPEG_DOWNLOAD_URLS]
    assert not missing, f"ffmpeg 来源表缺运行时键 {missing}，该平台 full 包将无 ffmpeg"
    extra = [k for k in build_exe._FFMPEG_DOWNLOAD_URLS if k not in keys]
    assert not extra, f"ffmpeg 来源表含矩阵外的键 {extra}"


def test_source_table_and_pin_table_share_the_same_runtime_keys() -> None:
    # 两张表必须同键：钉定判定按运行时键取段，来源表若多出/少了一个键，
    # 就会出现「有来源没钉定」或「有钉定没来源」的静默半边。
    assert set(build_exe._FFMPEG_DOWNLOAD_URLS) == set(build_exe._PINNED_RUNTIME_SHA256)


def test_macos_arm64_resolves_to_the_same_evermeet_build_as_x64(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build_exe, "runtime_slot_key", lambda: "macos-arm64")
    url = build_exe._ffmpeg_source_url()
    assert url == build_exe._FFMPEG_DOWNLOAD_URLS["macos-x64"], "两架构必须共用同一份 evermeet 构建"
    assert url.endswith("/ffmpeg/getrelease/zip"), url


def test_broken_arm64_endpoint_cannot_be_resurrected() -> None:
    # 形态锁，且**只看字符串字面量与函数体**：注释里记录「这条端点不存在」是必要的文档，
    # 但它绝不能再成为取值——无论写进来源表还是在下载函数里按 machine 现场拼接。
    tree = ast.parse((ROOT / "build_exe.py").read_text(encoding="utf-8"), filename="build_exe.py")
    offenders = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and "getrelease-arm64" in node.value
    ]
    assert not offenders, f"不存在的 evermeet arm64 端点重新出现在字面量里: {offenders}"
    download_src = inspect.getsource(build_exe._download_ffmpeg)
    assert "platform.machine" not in download_src, "URL 不得再由 platform.machine() 派生（走运行时键查表）"
    assert "_ffmpeg_source_url()" in download_src, "下载函数未从来源表取 URL，等于回到现场拼的旧形态"


def test_every_pinned_source_url_is_https_on_an_allowlisted_host() -> None:
    # 供应链侧的最低门槛：明文 http 或新增镜像域都必须显式改进本清单（并在评审里说明理由）。
    urls = list(build_exe._FFMPEG_DOWNLOAD_URLS.values())
    assert len(urls) == len(build_exe.RELEASE_RUNTIME_KEYS)
    for url in urls:
        assert url.startswith("https://"), f"非 TLS 来源: {url}"
        host = url.split("/", 3)[2]
        assert host in _ALLOWED_HOSTS, f"来源主机 {host} 不在允许清单内"
    # node 的 URL 是 f-string 现拼的，锁它的两个模板主机而不是具体版本
    node_source = (ROOT / "build_exe.py").read_text(encoding="utf-8")
    assert 'urllib.request.urlopen("https://nodejs.org/dist/index.json"' in node_source
    assert 'url = f"https://nodejs.org/dist/{version}/{filename}"' in node_source


def test_both_macos_ffmpeg_slots_stay_consistent() -> None:
    # 两个槽指向同一份产物 → 取值必须同为占位或同为同一个官方哈希。
    # 只在其中一个填值会让 macos-x64 有校验、arm64 无校验（或反之），而 --strict 只数「未钉定」。
    x64 = build_exe._PINNED_RUNTIME_SHA256["macos-x64"]["ffmpeg"]
    arm = build_exe._PINNED_RUNTIME_SHA256["macos-arm64"]["ffmpeg"]
    assert x64 == arm, "macOS 两槽的 ffmpeg 钉定值不一致：同一份构建被钉成了两个值"


def test_unlisted_arch_falls_back_to_family_x64_and_warns(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(build_exe, "runtime_slot_key", lambda: "windows-arm64")
    assert build_exe._ffmpeg_source_url() == build_exe._FFMPEG_DOWNLOAD_URLS["windows-x64"]
    assert "回落" in capsys.readouterr().out, "回落必须留痕，否则「拿不到本架构构建」会被伪装成正常"


def test_unknown_family_raises_instead_of_skipping_silently(monkeypatch: pytest.MonkeyPatch) -> None:
    # 连同族 x64 都没有时**必须抛错**：静默返回空串会让 _download_file 拿不到 URL，
    # 失败又被外层 except 吞掉——正是本文件开头描述的三层失效。
    monkeypatch.setattr(build_exe, "runtime_slot_key", lambda: "freebsd-x64")
    with pytest.raises(KeyError):
        build_exe._ffmpeg_source_url()


def test_runtime_slots_cover_both_pinnable_components() -> None:
    # 钉定表按槽位分列；槽位集合与 RUNTIME_SLOTS 不一致时，check_runtime_pins 会静默少查一类。
    assert set(build_exe.RUNTIME_SLOTS) == {"ffmpeg", "node"}
    for key, entry in build_exe._PINNED_RUNTIME_SHA256.items():
        assert set(entry) == set(build_exe.RUNTIME_SLOTS), f"{key} 的槽位集合不完整"


def test_is_pinned_shape_rule_rejects_every_placeholder_form() -> None:
    # SEV-10 的「已钉定」唯一判据是形状（64 位小写十六进制）：占位串、空串、大写、缺位、
    # 带空白一律算未钉定。形状关把不住，后面所有「缺钉定即终止构建」的语义都无从谈起。
    is_pinned = build_exe._is_pinned
    assert is_pinned("a" * 64) is True
    for bad in (
        build_exe.UNVERIFIED_PIN,
        build_exe.OFFICIAL_SIGNATURE_PIN,  # 签名档标记不得被当成「已钉定的哈希」，否则哈希分支会拿它去比 digest
        "",
        "A" * 64,
        "a" * 63,
        "z" * 64,
        "  " + "a" * 64 + " ",
    ):
        assert is_pinned(bad) is False, f"形状判定对 {bad!r} 放宽了"


# ---------------------------------------------------------------------------
# P-2：官方 GPG 签名核验（2026-09-22 批准引入 gnupg）
#
# 全部离线：gpg 与 urlopen 都被打桩。桩只替换 build_exe 的**模块全局名**（urllib / _run_gpg），
# 绝不改 stdlib 模块本体。
# ---------------------------------------------------------------------------

_PRIMARY_FPR = "20F6EA3E0CFD6B4C53447A73476C4B611A660874"
_SIGNING_SUBKEY_FPR = "31B0C6D7E8F90A1B2C3D4E5F60718293A4B5C6D7"
_UNRELATED_FPR = "99AABBCCDDEEFF00112233445566778899AABBCC"


def _colon_fpr_line(fingerprint: str) -> str:
    # gpg --with-colons 的 fpr 记录：指纹在第 10 字段（下标 9）
    fields = [""] * 10
    fields[0] = "fpr"
    fields[9] = fingerprint
    return ":".join(fields)


def _keyring_record(*fingerprints: str) -> bytes:
    lines = [f"pub:-:4096:1:1600000000:::{fingerprints[0]}:"] + [_colon_fpr_line(f) for f in fingerprints]
    return ("\n".join(lines) + "\n").encode("ascii")


class _FakeResponse:
    # 桩同时服务两种调用方：_verify_gpg_artifact 整块 read()，而 _download_file 按 read(65536)
    # 分块循环读到空字节为止，并要 headers["Content-Length"]。故这里必须**逐次排空**——
    # 每次返回同一份 payload 会让下载循环永不退出。
    headers: dict[str, str] = {}

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self, size: int = -1) -> bytes:
        take = len(self._payload) if size is None or size < 0 else min(size, len(self._payload))
        chunk, self._payload = self._payload[:take], self._payload[take:]
        return chunk

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None


def _install_fake_urlopen(monkeypatch: pytest.MonkeyPatch, payload: bytes | OSError) -> list[str]:
    seen: list[str] = []

    def fake_urlopen(url: str, *args: Any, **kwargs: Any) -> Any:
        seen.append(url)
        if isinstance(payload, OSError):
            raise payload
        return _FakeResponse(payload)

    monkeypatch.setattr(build_exe, "urllib", types.SimpleNamespace(request=types.SimpleNamespace(urlopen=fake_urlopen)))
    return seen


def _install_fake_gpg(
    monkeypatch: pytest.MonkeyPatch,
    *,
    keyring: bytes,
    verify_status: bytes,
    import_available: bool = True,
) -> list[list[str]]:
    calls: list[list[str]] = []

    def fake_run_gpg(args: list[str], timeout: int = 180) -> Any:
        calls.append(args)
        if "--recv-keys" in args:
            if not import_available:
                return None  # None == gpg 这个工具不可用（未安装/超时/起不动）
            return types.SimpleNamespace(stdout=b"", returncode=0)
        if "--list-keys" in args:
            return types.SimpleNamespace(stdout=keyring, returncode=0)
        return types.SimpleNamespace(stdout=verify_status, returncode=0)

    monkeypatch.setattr(build_exe, "_run_gpg", fake_run_gpg)
    return calls


def _macos_release_env(monkeypatch: pytest.MonkeyPatch, *, release: bool) -> None:
    monkeypatch.setattr(build_exe, "runtime_slot_key", lambda: "macos-arm64")
    monkeypatch.setattr(build_exe, "require_pinned_hashes", lambda: release)


def test_gpg_config_shape_and_source_consistency() -> None:
    # 只登记「上游确实公布 detached 签名」的槽位；且签名 URL 必须是产物 URL + "/sig"
    # （evermeet 的既定约定），否则改了产物来源却忘了改签名来源，验签会长期假失败。
    for key, slots in build_exe._RUNTIME_GPG_SIGNATURES.items():
        assert key in build_exe._FFMPEG_DOWNLOAD_URLS, f"签名配置指向了不存在的运行时键 {key}"
        for slot, (sig_url, fingerprint) in slots.items():
            assert slot in build_exe.RUNTIME_SLOTS
            assert re.fullmatch(r"[0-9a-fA-F]{40}", fingerprint), f"{key}/{slot} 指纹不是 40 位十六进制"
            artifact = build_exe._FFMPEG_DOWNLOAD_URLS[key] if slot == "ffmpeg" else ""
            assert sig_url == f"{artifact}/sig", f"{key}/{slot} 签名 URL 与产物 URL 脱钩: {sig_url}"


def test_gpg_verification_is_skipped_for_slots_without_official_sig(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # gyan.dev / johnvansickle 不公布签名：未登记的槽位必须**一次网络与进程都不碰**，
    # 而不是「试一下失败后放行」——后者会把「无物可验」伪装成「验过了」。
    def explode(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("未登记签名的槽位不得发起核验")

    monkeypatch.setattr(build_exe, "urllib", types.SimpleNamespace(request=types.SimpleNamespace(urlopen=explode)))
    monkeypatch.setattr(build_exe, "_run_gpg", explode)
    monkeypatch.setattr(build_exe, "runtime_slot_key", lambda: "windows-x64")
    build_exe._verify_official_signature(tmp_path / "a.zip", "ffmpeg", "ffmpeg (gyan.dev)")


def test_gpg_accepts_signature_made_by_pinned_keys_subkey(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # VALIDSIG 报的是**实际签名的子钥**指纹。逐字比主钥会把合法产物判失败（假红），
    # 所以判据必须是「签名钥匙属于那把钥匙的主钥/子钥集合」。
    artifact = tmp_path / "ffmpeg.zip"
    artifact.write_bytes(b"payload")
    _macos_release_env(monkeypatch, release=True)
    _install_fake_urlopen(monkeypatch, b"detached-sig")
    status = (
        b"[GNUPG:] GOODSIG 1234567890ABCDEF someone@example.org\n"
        b"[GNUPG:] VALIDSIG " + _SIGNING_SUBKEY_FPR.lower().encode("ascii") + b" 1600000000 1600000000 0 4 0 1 22 00\n"
    )
    calls = _install_fake_gpg(
        monkeypatch, keyring=_keyring_record(_PRIMARY_FPR, _SIGNING_SUBKEY_FPR), verify_status=status
    )
    build_exe._verify_official_signature(artifact, "ffmpeg", "ffmpeg (evermeet)")
    assert any("--verify" in c for c in calls), "根本没跑 gpg --verify，上一条断言成了自证"


@pytest.mark.parametrize(
    ("keyring", "verify_status"),
    [
        # 签名者不属于钉定钥匙
        (
            _keyring_record(_PRIMARY_FPR, _SIGNING_SUBKEY_FPR),
            b"[GNUPG:] GOODSIG x y\n[GNUPG:] VALIDSIG " + _UNRELATED_FPR.encode() + b" 1 1 0 4 0 1 22 00\n",
        ),
        # 明确的坏签名
        (_keyring_record(_PRIMARY_FPR), b"[GNUPG:] BADSIG 1234567890ABCDEF someone@example.org\n"),
        # 只有 GOODSIG 没有 VALIDSIG（状态行不完整）
        (_keyring_record(_PRIMARY_FPR), b"[GNUPG:] GOODSIG 1234567890ABCDEF someone@example.org\n"),
        # 钥匙环里没有钉定的那把主钥（import 拿到别的钥匙）
        (
            _keyring_record(_UNRELATED_FPR),
            b"[GNUPG:] GOODSIG x y\n[GNUPG:] VALIDSIG " + _UNRELATED_FPR.encode() + b" 1 1 0 4 0 1 22 00\n",
        ),
    ],
    ids=["signer-not-pinned", "badsig", "no-validsig", "wrong-key-in-ring"],
)
def test_gpg_rejects_every_untrustworthy_shape(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, keyring: bytes, verify_status: bytes
) -> None:
    artifact = tmp_path / "ffmpeg.zip"
    artifact.write_bytes(b"payload")
    _macos_release_env(monkeypatch, release=True)
    _install_fake_urlopen(monkeypatch, b"detached-sig")
    _install_fake_gpg(monkeypatch, keyring=keyring, verify_status=verify_status)
    with pytest.raises(SystemExit):
        build_exe._verify_official_signature(artifact, "ffmpeg", "ffmpeg (evermeet)")


@pytest.mark.parametrize("release", [True, False], ids=["release", "local"])
def test_gpg_tool_or_sig_missing_never_passes_silently(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, release: bool, capsys: pytest.CaptureFixture[str]
) -> None:
    # 「gpg 不可用」与「取不到签名文件」都属工具/网络缺失：发布路径必须终止，本地路径必须
    # **留一条明确的跳过日志**——两侧都不许出现「什么都没发生」的形态。
    artifact = tmp_path / "ffmpeg.zip"
    artifact.write_bytes(b"payload")
    _macos_release_env(monkeypatch, release=release)

    _install_fake_urlopen(monkeypatch, OSError("network down"))
    _install_fake_gpg(monkeypatch, keyring=_keyring_record(_PRIMARY_FPR), verify_status=b"")
    if release:
        with pytest.raises(SystemExit):
            build_exe._verify_official_signature(artifact, "ffmpeg", "ffmpeg (evermeet)")
    else:
        build_exe._verify_official_signature(artifact, "ffmpeg", "ffmpeg (evermeet)")
        assert "签名核验跳过" in capsys.readouterr().out

    _install_fake_urlopen(monkeypatch, b"detached-sig")
    _install_fake_gpg(monkeypatch, keyring=_keyring_record(_PRIMARY_FPR), verify_status=b"", import_available=False)
    if release:
        with pytest.raises(SystemExit):
            build_exe._verify_official_signature(artifact, "ffmpeg", "ffmpeg (evermeet)")
    else:
        build_exe._verify_official_signature(artifact, "ffmpeg", "ffmpeg (evermeet)")
        assert "gnupg 不可用" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# P-5：full 包产物自检
# ---------------------------------------------------------------------------


def test_verify_runtime_binaries_flags_every_missing_component(tmp_path: Path) -> None:
    problems = build_exe.verify_runtime_binaries(tmp_path)
    text = "\n".join(problems)
    assert len(problems) == 3, problems
    for name in ("ffmpeg", "ffprobe", "node"):
        assert name in text, f"未报告缺失组件 {name}: {text}"


def test_verify_runtime_binaries_accepts_nested_bin_layout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # node 的 tar.gz 解压后是 bin/node，ffmpeg 的 Windows 包是 bin/ffmpeg.exe：
    # 递归匹配才不会把布局差异误判成缺件（那会让 macOS/Linux 构建无端变红）。
    (tmp_path / "ffmpeg" / "bin").mkdir(parents=True)
    (tmp_path / "ffmpeg" / "bin" / "ffmpeg").write_bytes(b"x" * 10)
    (tmp_path / "ffmpeg" / "ffprobe").write_bytes(b"y" * 10)
    (tmp_path / "node" / "bin").mkdir(parents=True)
    (tmp_path / "node" / "bin" / "node").write_bytes(b"z" * 10)
    monkeypatch.setattr(build_exe, "_probe_runnable", lambda binary: None)
    assert build_exe.verify_runtime_binaries(tmp_path) == []


def test_zero_byte_runtime_binary_is_not_counted_as_present(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 下载被截断时文件存在但 0 字节；只看存在性会判「就绪」。
    (tmp_path / "ffmpeg").mkdir()
    (tmp_path / "ffmpeg" / "ffmpeg").write_bytes(b"")
    (tmp_path / "ffmpeg" / "ffprobe").write_bytes(b"ok")
    (tmp_path / "node").mkdir()
    (tmp_path / "node" / "node").write_bytes(b"ok")
    monkeypatch.setattr(build_exe, "_probe_runnable", lambda binary: None)
    problems = build_exe.verify_runtime_binaries(tmp_path)
    assert len(problems) == 1 and "ffmpeg" in problems[0], problems


def test_unrunnable_binary_is_reported_with_upstream_reason(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 文件在、跑不动（macOS 缺 dylib 闭包 / 无 Rosetta）必须被点名，且报错里带上游第一行原因。
    # 顺带锁「按字节读输出」：桩返回的是 stderr **bytes**。
    for rel in ("ffmpeg/ffmpeg", "ffmpeg/ffprobe", "node/node"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"binary")
    fake = types.SimpleNamespace(**vars(subprocess))
    fake.run = lambda *args, **kwargs: types.SimpleNamespace(
        returncode=1, stdout=b"", stderr=b"dyld: Library not loaded: /opt/homebrew/lib/libx265.215.dylib\n"
    )
    monkeypatch.setattr(build_exe, "subprocess", fake)
    problems = build_exe.verify_runtime_binaries(tmp_path)
    assert len(problems) == 3, problems
    assert any("libx265" in p for p in problems), problems


@pytest.mark.parametrize("release", [True, False], ids=["release", "local"])
def test_dual_full_aborts_on_release_path_when_runtime_incomplete(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, release: bool, capsys: pytest.CaptureFixture[str]
) -> None:
    # 这一条锁的是本轮缺陷的收口：_download_ffmpeg 返回 False 不再等于「这轮构建可以出包」。
    monkeypatch.setattr(build_exe, "_download_ffmpeg", lambda target: False)
    monkeypatch.setattr(build_exe, "_download_nodejs", lambda target: False)
    monkeypatch.setattr(build_exe, "require_pinned_hashes", lambda: release)
    if release:
        with pytest.raises(SystemExit):
            build_exe.download_runtime_binaries(tmp_path)
    else:
        build_exe.download_runtime_binaries(tmp_path)
        assert "不得用于发布" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# W1（2026-09-22 批准）：第 4 类完整性口径「源码可复现构建」
# 锁的是两件事：满足条件不可被标记单独糊过去；声明第 4 类的槽位不得再走下载路径。
# ---------------------------------------------------------------------------

_MARKER = build_exe.SOURCE_BUILD_PROVENANCE
_EVIDENCE_OK = {"source_sha256": "b" * 64, "recipe_sha256": "c" * 64, "provenance_ref": "build-release.yml@abc"}


@pytest.mark.parametrize(
    ("value", "evidence", "expected"),
    [
        ("a" * 64, {}, True),  # 常规：已钉定的官方哈希
        ("", {}, False),
        (_MARKER, {}, False),  # 光有标记 = 不满足
        (_MARKER, {"source_sha256": "b" * 64, "recipe_sha256": "c" * 64, "provenance_ref": ""}, False),
        (_MARKER, {"source_sha256": "b" * 63, "recipe_sha256": "c" * 64, "provenance_ref": "w@1"}, False),
        (_MARKER, _EVIDENCE_OK, True),  # 三件证据齐备且过形状关
        ("a" * 64, _EVIDENCE_OK, True),  # 钉定哈希不受证据表影响（两条路任一成立即管住）
    ],
    ids=["pinned", "empty", "marker-only", "no-ref", "short-source", "full-evidence", "pinned-plus-evidence"],
)
def test_slot_is_gated_is_the_single_authority_predicate(
    monkeypatch: pytest.MonkeyPatch, value: str, evidence: dict[str, str], expected: bool
) -> None:
    monkeypatch.setattr(build_exe, "_SOURCE_BUILD_EVIDENCE", {"macos-arm64": {"ffmpeg": dict(evidence)}})
    assert build_exe._slot_is_gated(value, "macos-arm64", "ffmpeg") is expected


def test_table_never_declares_the_fourth_class_without_evidence() -> None:
    # 永久不变量：谁启用第 4 类，就必须同时把三件证据填进 _SOURCE_BUILD_EVIDENCE，
    # 否则「更容易填的标记」就成了绕闸通道（本用例即那条防线的静态面）。
    offenders = [
        f"{key}/{slot}"
        for key, entry in build_exe._PINNED_RUNTIME_SHA256.items()
        for slot, value in entry.items()
        if value == _MARKER and not build_exe._is_source_build_satisfied(value, key, slot)
    ]
    assert not offenders, f"以下槽位声明第 4 类但证据不齐: {offenders}"


@pytest.mark.parametrize("release", [True, False], ids=["release", "local"])
def test_declared_source_build_slot_refuses_to_download_on_both_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, release: bool
) -> None:
    # 第 4 类的产物应由构建步骤产出，不是从上游拉：走到下载就必须终止，**两侧都一样**
    # （本地路径若放行，等于「换个标记就把校验整个跳过」——这正是本类最容易被误用的地方）。
    def explode(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("第 4 类槽位不得发起下载")

    monkeypatch.setattr(build_exe, "require_pinned_hashes", lambda: release)
    monkeypatch.setattr(build_exe, "runtime_slot_key", lambda: "macos-arm64")
    monkeypatch.setattr(build_exe, "_PINNED_RUNTIME_SHA256", {"macos-arm64": {"ffmpeg": _MARKER, "node": "a" * 64}})
    monkeypatch.setattr(build_exe, "urllib", types.SimpleNamespace(request=types.SimpleNamespace(urlopen=explode)))
    with pytest.raises(SystemExit) as caught:
        build_exe._download_file(
            "https://example.invalid/x.zip", tmp_path / "x.zip", "ffmpeg (evermeet)", slot="ffmpeg"
        )
    assert "SOURCE-BUILD-PROVENANCE" in str(caught.value)


def test_env_injected_marker_also_refuses_download(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 标记也可能由 CI 经 DLR_RUNTIME_SHA256 注入（build-release.yml 的透传通道），
    # 拒下载判定必须看**合并环境变量后的实际取值**，而不是只看内置表。
    def explode(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("第 4 类槽位不得发起下载")

    payload = '{"macos-arm64": {"ffmpeg": "%s"}}' % _MARKER
    monkeypatch.setenv("DLR_RUNTIME_SHA256", payload)
    monkeypatch.setattr(build_exe, "runtime_slot_key", lambda: "macos-arm64")
    monkeypatch.setattr(build_exe, "require_pinned_hashes", lambda: False)
    monkeypatch.setattr(build_exe, "urllib", types.SimpleNamespace(request=types.SimpleNamespace(urlopen=explode)))
    with pytest.raises(SystemExit):
        build_exe._download_file(
            "https://example.invalid/x.zip", tmp_path / "x.zip", "ffmpeg (evermeet)", slot="ffmpeg"
        )


def test_pinned_slot_still_downloads_and_verifies_normally(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 反向防线：别把「拒下载」写成对所有槽位生效——那会让已钉定的 windows 构建悄悄拿不到 ffmpeg。
    payload = b"chunk" * 4
    digest = hashlib.sha256(payload).hexdigest()
    dest = tmp_path / "artifact.zip"
    remaining = [payload]

    class _Resp:
        headers = {"Content-Length": str(len(payload))}

        def read(self, size: int = -1) -> bytes:
            return remaining.pop(0) if remaining else b""

        def __enter__(self) -> "_Resp":
            return self

        def __exit__(self, *exc: Any) -> None:
            return None

    monkeypatch.setattr(build_exe, "runtime_slot_key", lambda: "windows-x64")
    monkeypatch.setattr(build_exe, "require_pinned_hashes", lambda: True)
    monkeypatch.setattr(build_exe, "_PINNED_RUNTIME_SHA256", {"windows-x64": {"ffmpeg": digest, "node": "a" * 64}})
    monkeypatch.setattr(
        build_exe, "urllib", types.SimpleNamespace(request=types.SimpleNamespace(urlopen=lambda *a, **k: _Resp()))
    )
    seen: list[tuple] = []
    monkeypatch.setattr(build_exe, "_verify_official_signature", lambda *a: seen.append(a))
    build_exe._download_file("https://example.invalid/x.zip", dest, "ffmpeg (gyan.dev)", slot="ffmpeg")
    assert dest.read_bytes() == payload
    assert seen == [(dest, "ffmpeg", "ffmpeg (gyan.dev)")], "钉定通过后才应触发验签，且不得对未核过内容的产物验签"


# ---------------------------------------------------------------------------
# 2026-09-26 官方签名档（macOS 两槽）：上游不公布 SHA256，判据 = 官方分离 GPG 签名
# + 带外钉死的 40 位主钥指纹。下面各锁分别拦一种具体失效形态：
#   ① 「光有标记就拿免检」——标记比 64 位十六进制更容易填，缺登记 / 缺形状必须同等拦下；
#   ② SEV-2221「验签代码写在下载后、闸口卡在下载前」——若签名档槽位不在哈希分支之外也验签，
#      这一档在真实构建路径上永不可达，看着有防线其实一次都没跑过；
#   ③ 签名档**没有哈希兜底**，故发布路径上「gpg 不可用 / 验签判坏」必须终止，不得降级放行。
# 全程离线：urlopen 与 _run_gpg 一律打桩（桩替换 build_exe 的模块全局名，不改 stdlib 本体）。
# ---------------------------------------------------------------------------

_SIG_MARKER = build_exe.OFFICIAL_SIGNATURE_PIN
_GOOD_VERIFY_STATUS = (
    b"[GNUPG:] GOODSIG 1234567890ABCDEF someone@example.org\n"
    b"[GNUPG:] VALIDSIG " + _PRIMARY_FPR.lower().encode("ascii") + b" 1600000000 1600000000 0 4 0 1 22 00\n"
)


@pytest.mark.parametrize(
    ("key", "slot", "expected"),
    [
        ("macos-arm64", "ffmpeg", True),
        ("macos-x64", "ffmpeg", True),
        ("macos-arm64", "node", False),  # 同一运行时键的另一槽没登记签名 → 不许蹭同键的登记
        ("linux-x64", "ffmpeg", False),  # BtbN 不公布 detached 签名，无物可验
        ("windows-x64", "ffmpeg", False),
    ],
    ids=["arm64-ffmpeg", "x64-ffmpeg", "同键另一槽", "linux-无签名", "windows-无签名"],
)
def test_signature_mode_is_satisfied_only_by_a_registered_slot(key: str, slot: str, expected: bool) -> None:
    # 与第 4 类同一条防线：标记本身绝不构成放行，必须「该槽确有登记」且「指纹形状对」。
    assert build_exe._is_signature_satisfied(_SIG_MARKER, key, slot) is expected
    # 唯一口径必须同步认下这一档：_slot_is_gated 若漏并，--strict 会把已按签名管住的槽判成未钉定。
    assert build_exe._slot_is_gated(_SIG_MARKER, key, slot) is expected


def test_signature_mode_marker_is_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    # _pinned_slots() 会把内置表与 DLR_RUNTIME_SHA256 注入值统一 .strip().lower()；
    # 若标记按原样逐字比，CI 注入通道就永远认不出签名档（与 test_env_injected_marker_also_refuses_download
    # 抓出来的第 4 类同一形态）。
    assert build_exe._is_signature_satisfied(_SIG_MARKER.lower(), "macos-arm64", "ffmpeg") is True


@pytest.mark.parametrize(
    "bad_fpr",
    ["", "20F6EA3E", "z" * 40, "20F6EA3E0CFD6B4C53447A73476C4B611A66087"],
    ids=["空指纹", "过短", "非十六进制", "39位"],
)
def test_signature_mode_rejects_malformed_fingerprint(monkeypatch: pytest.MonkeyPatch, bad_fpr: str) -> None:
    # 指纹形状关把不住，「登记一把不存在的钥匙」就成了新的绕闸通道。
    monkeypatch.setitem(
        build_exe._RUNTIME_GPG_SIGNATURES, "macos-arm64", {"ffmpeg": ("https://example.invalid/sig", bad_fpr)}
    )
    assert build_exe._is_signature_satisfied(_SIG_MARKER, "macos-arm64", "ffmpeg") is False
    assert build_exe._slot_is_gated(_SIG_MARKER, "macos-arm64", "ffmpeg") is False


def test_table_never_declares_signature_mode_without_satisfaction() -> None:
    # 永久不变量（对齐 test_table_never_declares_the_fourth_class_without_evidence）：
    # 谁把某槽改成签名档，就必须同批把签名 URL 与指纹登记进 _RUNTIME_GPG_SIGNATURES。
    offenders = [
        f"{key}/{slot}"
        for key, entry in build_exe._PINNED_RUNTIME_SHA256.items()
        for slot, value in entry.items()
        if value == _SIG_MARKER and not build_exe._is_signature_satisfied(value, key, slot)
    ]
    assert not offenders, f"以下槽位声明官方签名档但未满足登记/指纹条件: {offenders}"


@pytest.mark.parametrize("release", [True, False], ids=["release", "local"])
def test_signature_mode_slot_downloads_and_actually_verifies(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, release: bool
) -> None:
    # SEV-2221 的可达性锁：签名档槽位必须**真的走到验签**。把验签调用点挪回「只在哈希已过的分支里」
    # （改造前形态）→ 本用例红，因为 macOS 槽值永远过不了 _is_pinned。
    dest = tmp_path / "ffmpeg.zip"
    payload = b"evermeet-archive"
    _macos_release_env(monkeypatch, release=release)
    _install_fake_urlopen(monkeypatch, payload)
    _install_fake_gpg(monkeypatch, keyring=_keyring_record(_PRIMARY_FPR), verify_status=_GOOD_VERIFY_STATUS)
    seen: list[tuple] = []
    real_verify = build_exe._verify_official_signature

    def _spy(*args: Any) -> None:
        seen.append(args)
        real_verify(*args)

    monkeypatch.setattr(build_exe, "_verify_official_signature", _spy)
    build_exe._download_file("https://example.invalid/x.zip", dest, "ffmpeg (evermeet)", slot="ffmpeg")
    assert seen == [(dest, "ffmpeg", "ffmpeg (evermeet)")], "签名档没有触发验签：验签又落回了哈希分支"
    assert dest.read_bytes() == payload


def test_signature_mode_aborts_build_when_signature_is_bad(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 验签判坏必须终止构建：签名档是这一槽唯一的判据，这里降级就等于整槽无校验。
    dest = tmp_path / "ffmpeg.zip"
    _macos_release_env(monkeypatch, release=True)
    _install_fake_urlopen(monkeypatch, b"evermeet-archive")
    _install_fake_gpg(
        monkeypatch, keyring=_keyring_record(_PRIMARY_FPR), verify_status=b"[GNUPG:] BADSIG 1 x@example.org\n"
    )
    with pytest.raises(SystemExit):
        build_exe._download_file("https://example.invalid/x.zip", dest, "ffmpeg (evermeet)", slot="ffmpeg")


def test_signature_mode_aborts_build_when_gpg_unavailable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 「gpg 这个工具不存在」在发布路径必须终止：签名档没有哈希兜底，跳过验签=跳过校验。
    dest = tmp_path / "ffmpeg.zip"
    _macos_release_env(monkeypatch, release=True)
    _install_fake_urlopen(monkeypatch, b"evermeet-archive")
    _install_fake_gpg(monkeypatch, keyring=b"", verify_status=b"", import_available=False)
    with pytest.raises(SystemExit):
        build_exe._download_file("https://example.invalid/x.zip", dest, "ffmpeg (evermeet)", slot="ffmpeg")


def test_signature_mode_marker_without_registration_never_downloads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # 声明了签名档但登记不齐（例如同步改表时漏改签名表）→ 必须**在下载前**拦下，
    # 且不发起任何请求；报错文案点名「未登记/指纹形状」，别让维护者去核对一个不存在的哈希。
    def explode(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("未满足的签名档不得发起下载")

    monkeypatch.setattr(build_exe, "runtime_slot_key", lambda: "linux-x64")
    monkeypatch.setattr(build_exe, "require_pinned_hashes", lambda: True)
    monkeypatch.setattr(build_exe, "_PINNED_RUNTIME_SHA256", {"linux-x64": {"ffmpeg": _SIG_MARKER, "node": "a" * 64}})
    monkeypatch.setattr(build_exe, "urllib", types.SimpleNamespace(request=types.SimpleNamespace(urlopen=explode)))
    with pytest.raises(SystemExit) as caught:
        build_exe._download_file("https://example.invalid/x.tar.xz", tmp_path / "x.tar.xz", "ffmpeg", slot="ffmpeg")
    assert "官方签名档" in str(caught.value) and "未满足" in str(caught.value)


def _make_tar_xz(archive: Path, members: dict[str, bytes]) -> None:
    # 造一份最小 tar.xz：只用于驱动真实的 tarfile 解包与递归查名，不碰网络。
    with tarfile.open(archive, "w:xz") as tf:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o755
            tf.addfile(info, io.BytesIO(data))


@pytest.mark.parametrize(
    "members",
    [
        # BtbN 实测布局（2026-09-26 取该资产归档前 4 MB 列成员所得）
        {
            "ffmpeg-n9.0-latest-linux64-gpl-9.0/bin/ffmpeg": b"ELF-ffmpeg",
            "ffmpeg-n9.0-latest-linux64-gpl-9.0/bin/ffprobe": b"ELF-ffprobe",
            "ffmpeg-n9.0-latest-linux64-gpl-9.0/doc/ffmpeg.html": b"docs",
        },
        # johnvansickle 旧布局：平铺在 ffmpeg-<ver>-<arch>-static/ 下
        {
            "ffmpeg-7.0-amd64-static/ffmpeg": b"ELF-ffmpeg",
            "ffmpeg-7.0-amd64-static/ffprobe": b"ELF-ffprobe",
        },
    ],
    ids=["BtbN-bin布局", "johnvansickle-平铺布局"],
)
def test_linux_ffmpeg_extraction_is_layout_agnostic(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, members: dict[str, bytes]
) -> None:
    # 换源后归档内层级从平铺变成带 bin/：写死任一种，另一种会「解包成功但一件没拷」，
    # 而调用方要到出包前的 verify_runtime_binaries 才发现。本函数不读 sys.platform，
    # 故在 Windows 开发机与 Linux CI 上都会真实执行（AGENTS.md「平台分支不得靠 skipif 让 CI 丢锁」同源）。
    archive = tmp_path / "runtime.tar.xz"
    _make_tar_xz(archive, members)
    ffmpeg_dir = tmp_path / "ffmpeg"
    ffmpeg_dir.mkdir()
    build_exe._extract_linux_ffmpeg_binaries(archive, ffmpeg_dir)
    for binary, content in (("ffmpeg", b"ELF-ffmpeg"), ("ffprobe", b"ELF-ffprobe")):
        got = ffmpeg_dir / binary
        assert got.is_file() and got.read_bytes() == content, f"{binary} 未被取出（布局假设被写死了）"


def test_linux_ffmpeg_extraction_aborts_when_binary_absent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 缺件抛 SystemExit（BaseException 不被 _download_ffmpeg 外层 except Exception 吞）：
    # 否则回到「一行 warning + 出包成功」的 arm64 404 形态。
    archive = tmp_path / "runtime.tar.xz"
    _make_tar_xz(archive, {"ffmpeg-x/doc/README": b"docs only"})
    ffmpeg_dir = tmp_path / "ffmpeg"
    ffmpeg_dir.mkdir()
    with pytest.raises(SystemExit):
        build_exe._extract_linux_ffmpeg_binaries(archive, ffmpeg_dir)


# ---------------------------------------------------------------------------
# MID-2254：发布 zip 与冒烟解耦 + 「运行期产物不得进包」
# 冒烟以 cwd=RELEASE_DIR 连跑 CLI 25s / Web 90s / GUI 8s，src/logger.py 会在包内落
# streamget.log / PlayURL.log / web_console.log（含 runner 绝对路径、用户名、告警堆栈），
# 「缺键补写」还会改写包内 config.ini。旧顺序把冒烟排在 full 压缩之前，等于把这些
# 打进对外分发的 zip。下面几条分别锁：顺序、清理、实物断言。
# 全程桩掉 PyInstaller / 下载 / 压缩 / 起进程，不执行真实打包。
# ---------------------------------------------------------------------------


def _stub_build_steps(monkeypatch: pytest.MonkeyPatch, order: list[str]) -> None:
    # 把 main() 的每个重活换成「记名字」的桩：既验证顺序，也保证不碰网络与磁盘产物。
    def _make(name: str, ret: object) -> Any:
        def _stub(*args: object, **kwargs: object) -> object:
            order.append(name)
            return ret

        return _stub

    for name in ("run_pyinstaller", "copy_external_binaries", "download_runtime_binaries", "smoke_test"):
        monkeypatch.setattr(build_exe, name, _make(name, None))
    monkeypatch.setattr(build_exe, "_prepare_url_config", _make("_prepare_url_config", None))
    monkeypatch.setattr(build_exe, "make_zip", _make("make_zip", Path("stub.zip")))


def _zip_positions(order: list[str]) -> list[int]:
    return [i for i, name in enumerate(order) if name == "make_zip"]


def test_dual_build_zips_both_variants_before_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []
    _stub_build_steps(monkeypatch, order)
    monkeypatch.setattr(sys, "argv", ["build_exe.py", "--dual", "--smoke"])
    build_exe.main()
    zips = _zip_positions(order)
    assert len(zips) == 2, f"--dual 应产出 lite + full 两个 zip：{order}"
    assert "smoke_test" in order, order
    smoke_at = order.index("smoke_test")
    assert all(z < smoke_at for z in zips), f"冒烟必须排在两个 zip 之后（否则日志进包）：{order}"
    # full zip 必须在运行时下载之后（否则包里没有 ffmpeg/node），且仍在冒烟之前
    assert order.index("download_runtime_binaries") < zips[-1] < smoke_at, order


def test_single_build_zips_before_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []
    _stub_build_steps(monkeypatch, order)
    monkeypatch.setattr(sys, "argv", ["build_exe.py", "--smoke"])
    build_exe.main()
    zips = _zip_positions(order)
    assert len(zips) == 1, order
    assert zips[0] < order.index("smoke_test"), f"非 dual 路径同样必须先压缩后冒烟：{order}"


def test_no_zip_build_still_smokes(monkeypatch: pytest.MonkeyPatch) -> None:
    # 反向：--no-zip（ci.yml 的 build-verify 即用此形态）不该因为「zip 在前」的新顺序
    # 而丢掉冒烟——本用例锁「冒烟仍在」，防止把解耦写成「干脆不冒烟」。
    order: list[str] = []
    _stub_build_steps(monkeypatch, order)
    monkeypatch.setattr(sys, "argv", ["build_exe.py", "--smoke", "--no-zip", "--no-runtime"])
    build_exe.main()
    assert "make_zip" not in order, order
    assert "smoke_test" in order, order


def test_ensure_utf8_streams_keeps_replace_error_policy() -> None:
    # 回归锁（2026-09-23 故障）：_ensure_utf8_streams 一旦退回裸 reconfigure(encoding="utf-8")，
    # 就会把 pytest fd 捕获包装器（EncodedFile）的 errors 从 replace 就地翻成 strict，而代价
    # 不在当场——要等几十个用例之后会话收尾读捕获时才以 UnicodeDecodeError 炸出来，
    # 且往往先嫁祸给无关用例（见 DIAGNOSIS_2026-09-23_pytest-teardown-crash.md）。
    # 这里在**真实的 pytest 捕获**下调用它，要求两侧流的错误策略一字不变。
    before = (getattr(sys.stdout, "errors", None), getattr(sys.stderr, "errors", None))
    build_exe._ensure_utf8_streams()
    after = (getattr(sys.stdout, "errors", None), getattr(sys.stderr, "errors", None))
    # 前提：本用例必须跑在 pytest 的 fd 捕获之下，否则这条锁失去意义（而不是假通过）
    assert before == ("replace", "replace"), f"本用例依赖 pytest fd 捕获的 replace 策略，实测：{before}"
    assert after == before, f"_ensure_utf8_streams 改动了标准流错误策略：{before} -> {after}"


def test_ensure_utf8_streams_passes_explicit_errors_replace(monkeypatch: pytest.MonkeyPatch) -> None:
    # 形态锁：错误策略必须**显式**写成 "replace"，不能指望「省略即兜底」——省略恰恰会被
    # TextIOWrapper.reconfigure 解释成 strict（见上一条用例的注释）。
    calls: list[dict[str, str]] = []

    class _FakeStream:
        # 模拟 Windows CI 的默认形态：非 UTF-8 编码 + 严格错误策略
        encoding = "cp1252"
        errors = "strict"

        def reconfigure(self, **kwargs: str) -> None:
            calls.append(kwargs)

    monkeypatch.setattr(sys, "stdout", _FakeStream())
    monkeypatch.setattr(sys, "stderr", _FakeStream())
    build_exe._ensure_utf8_streams()
    assert calls == [
        {"encoding": "utf-8", "errors": "replace"},
        {"encoding": "utf-8", "errors": "replace"},
    ], f"两个标准流都必须带 errors='replace' 重配置：{calls}"


def test_release_cleaner_removes_runtime_artifacts_and_keeps_payload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    release = tmp_path / build_exe.APP_NAME
    for name in build_exe.RUNTIME_ARTIFACT_DIR_NAMES:
        (release / name).mkdir(parents=True)
        (release / name / "junk.txt").write_text("leak", encoding="utf-8")
    (release / "_internal" / "src" / "__pycache__").mkdir(parents=True)
    keep = release / "_internal" / "src" / "utils.py"
    keep.write_text("#\n", encoding="utf-8")
    cfg = release / "config"
    cfg.mkdir()
    (cfg / "config.ini").write_text("[录制设置]\n", encoding="utf-8")
    monkeypatch.setattr(build_exe, "RELEASE_DIR", release)

    removed = build_exe._clean_runtime_artifacts_from_release()

    for name in build_exe.RUNTIME_ARTIFACT_DIR_NAMES:
        assert not (release / name).exists(), f"{name}/ 未被剔除，会随 zip 外发"
    assert not (release / "_internal" / "src" / "__pycache__").exists(), "嵌套 __pycache__ 未剔除"
    assert keep.is_file() and (cfg / "config.ini").is_file(), "清理误伤发布载荷（源码/配置模板）"
    assert {p.replace("\\", "/") for p in removed} == {
        "logs/",
        "backup_config/",
        "downloads/",
        "_internal/src/__pycache__/",
    }, removed


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (f"{build_exe.APP_NAME}/logs/streamget.log", True),
        (f"{build_exe.APP_NAME}\\logs\\PlayURL.log", True),
        (f"{build_exe.APP_NAME}/downloads/x/1.ts", True),
        (f"{build_exe.APP_NAME}/_internal/src/__pycache__/utils.cpython-314.pyc", True),
        ("logs/web_console.log", True),
        (f"{build_exe.APP_NAME}/config/config.ini", False),
        (f"{build_exe.APP_NAME}/_internal/src/utils.py", False),
        (f"{build_exe.APP_NAME}/_internal/web/logs_note.js", False),
        (f"{build_exe.APP_NAME}/", False),
    ],
)
def test_zip_member_runtime_artifact_predicate(member: str, expected: bool) -> None:
    # `unzip -l` 那一列的判定逻辑；反斜杠形态也要认出（Windows 上手工造的 zip 会这样存）。
    assert build_exe._zip_member_is_runtime_artifact(member) is expected


def _fake_archive_with(members: list[str]) -> Any:
    # 桩掉 `_zip_release_dir`（make_zip 内部的压缩动作）而不是 shutil.make_archive：
    # 2026-09-24 体积优化后 make_zip 改为自建 zipfile（为指定 compresslevel=9），
    # 压缩这一步的**唯一接缝**就是该函数。桩在这里，两条用例的语义原样保留——
    # 「实物断言独立成立，不靠上游先删干净」。
    def _fake(zip_path: Path) -> None:
        with zipfile.ZipFile(zip_path, "w") as zf:
            for member in members:
                zf.writestr(member, "x")

    return _fake


def _stub_make_zip_inputs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, members: list[str]) -> None:
    release = tmp_path / build_exe.APP_NAME
    release.mkdir(parents=True)
    dist = tmp_path / "dist"
    dist.mkdir()
    monkeypatch.setattr(build_exe, "RELEASE_DIR", release)
    monkeypatch.setattr(build_exe, "DIST_DIR", dist)
    monkeypatch.setattr(build_exe, "assert_no_credentials_in_release", lambda: None)
    # 把清理本身桩成 no-op：证明「实物断言」独立成立，不靠上游先删干净
    monkeypatch.setattr(build_exe, "_clean_runtime_artifacts_from_release", lambda: [])
    monkeypatch.setattr(build_exe, "_zip_release_dir", _fake_archive_with(members))


def test_make_zip_aborts_when_archive_still_contains_logs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _stub_make_zip_inputs(monkeypatch, tmp_path, [f"{build_exe.APP_NAME}/logs/streamget.log"])
    with pytest.raises(SystemExit) as caught:
        build_exe.make_zip("9.9.9")
    assert "logs/streamget.log" in str(caught.value)


def test_make_zip_accepts_clean_archive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 反向：不得把断言写成「永远红」——干净清单必须出包成功。
    _stub_make_zip_inputs(
        monkeypatch,
        tmp_path,
        [f"{build_exe.APP_NAME}/config/config.ini", f"{build_exe.APP_NAME}/_internal/a.py"],
    )
    zip_path = build_exe.make_zip("9.9.9")
    assert zip_path.is_file()


# ---------------------------------------------------------------------------
# MID-2255：.dockerignore / .gitignore 的行内 `#` 与空规则
# 两份文件都只有**行首** `#` 是注释；`pattern   # 说明` 让模式变成「带空格与中文的长串」，
# 永不匹配 —— 规则看着在、实际等于没写，而且**伪装成已排除**（比漏写更危险）。
# ---------------------------------------------------------------------------


def _ignore_patterns(name: str) -> list[str]:
    text = (ROOT / name).read_text(encoding="utf-8-sig")
    return [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


@pytest.mark.parametrize("ignore_file", [".dockerignore", ".gitignore"])
def test_ignore_files_have_no_inline_comments(ignore_file: str) -> None:
    patterns = _ignore_patterns(ignore_file)
    offenders = [
        f"{ignore_file}:{no} -> {line!r}" for no, line in enumerate(patterns, 1) if " #" in line or "\t#" in line
    ]
    assert not offenders, "以下忽略规则把注释写在了行内，模式永不匹配（须移到独立行）：\n" + "\n".join(offenders)


def test_dockerignore_excludes_dev_only_artifacts_as_bare_patterns() -> None:
    patterns = _ignore_patterns(".dockerignore")
    # 这三条是本轮实测「伪装成已排除」的形态：65KB 打包脚本 / 37KB UTF-16 的 Windows 脚本 /
    # 仓库内散落的 *.jsonl（弹幕监控边车日志）都会经 COPY . ./ 进镜像。
    for must in ("build_exe.py", "StopRecording.vbs", "*.jsonl"):
        assert must in patterns, f".dockerignore 缺少裸模式 {must!r}（带行内注释的规则永不匹配）"
    # 空规则：i18n/ 下从来没有 compile_po.py（真身在 scripts/，已整目录排除），留着只会误导读者
    assert not [p for p in patterns if "compile_po" in p], "i18n/**/compile_po.py 永不匹配，属空规则"


def test_gitignore_runtime_dirs_are_bare_patterns() -> None:
    patterns = _ignore_patterns(".gitignore")
    # node/ 与 node-v*.zip 曾只有这一条规则（无其它兜底），行内注释让运行时下载的 Node.js
    # 目录几乎整体入库（node.exe 只是恰好被下面的 *.exe 拦住）；另两条一并钉住。
    for must in ("node/", "node-v*.zip", "backup_config/", "logs/", "*.jsonl"):
        assert must in patterns, f".gitignore 缺少裸模式 {must!r}"
    # 运行期产物目录**必须**保持忽略：修正规则形态不等于放开忽略意图
    assert "!node/" not in patterns and "!logs/" not in patterns and "!backup_config/" not in patterns


# ---------------------------------------------------------------------------
# MIN-2260：scripts/smoke_test.py 的「0 断言」不得算通过
# _ci_web_smoke.sh 原样透传 rc，CI 的「Web panel smoke test」步骤因此可以查了个空气还报成功。
# ---------------------------------------------------------------------------

_SMOKE_SCRIPT = ROOT / "scripts" / "smoke_test.py"


def _run_smoke_script(tmp_path: Path, content: str) -> int:
    cfg = tmp_path / "cfg.json"
    cfg.write_text(content, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(_SMOKE_SCRIPT), "-c", str(cfg)],
        capture_output=True,
        env={**os.environ, "PYTHONUTF8": "1"},
        cwd=str(ROOT),
        check=False,
    )
    rc: int = proc.returncode
    return rc


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ('{"base_url": "http://127.0.0.1:9", "checks": []}', 2),
        ('{"base_url": "http://127.0.0.1:9"}', 2),
        ("[]", 2),
        ('[{"url": "http://127.0.0.1:9/none", "expected_status": 418, "name": "closed port"}]', 1),
    ],
    ids=["empty-checks", "missing-checks-key", "empty-top-level", "one-real-check-fails"],
)
def test_smoke_script_exit_codes_on_empty_config(tmp_path: Path, content: str, expected: int) -> None:
    # 前三条锁「空清单 = 2（配置问题）」，第四条锁「有断言时仍按结果退 1」——
    # 少了第四条，「任何配置一律退 2」的改法也会全绿（变异验证结论见本轮交付说明）。
    # 第 4 条只连 127.0.0.1 的关闭端口（连接被拒即返回），不外发任何请求。
    assert _run_smoke_script(tmp_path, content) == expected


def test_smoke_load_config_still_reads_valid_checks(tmp_path: Path) -> None:
    # 反向：加严「checks 必须存在」不得顺手把合法配置读坏。
    spec = importlib.util.spec_from_file_location("_smoke_cfg_probe", _SMOKE_SCRIPT)
    assert spec is not None and spec.loader is not None
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)
    cfg = tmp_path / "ok.json"
    cfg.write_text('{"base_url": "http://127.0.0.1:9", "checks": [{"url": "/health"}]}', encoding="utf-8")
    checks, base_url = smoke.load_config(str(cfg))
    assert base_url == "http://127.0.0.1:9"
    assert checks == [{"url": "/health"}]
    # 缺 checks 键：ValueError（而不是静默的 0 检查）
    bad = tmp_path / "bad.json"
    bad.write_text('{"base_url": "http://127.0.0.1:9"}', encoding="utf-8")
    with pytest.raises(ValueError):
        smoke.load_config(str(bad))


# ---------------------------------------------------------------------------
# 产物体积优化（2026-09-24）：排除清单与资源清单的回归锁
#
# 为什么值得锁：这些排除项**在源码里看不出代价**——排除一个模块在本地 Windows 上可能毫无
# 变化（如 uvloop 只在 POSIX 安装），排除错了却会在某个平台/某条分支上以
# ModuleNotFoundError 的形态在**冻结产物运行时**炸出来，而单测跑的是源码、覆盖不到。
# 因此这里锁三件事：① 清单不含「生产代码真的导入了」的模块；② 三个入口都挂上清单
# （COLLECT 合并去重，只挂一个等于没排）；③ i18n 资源不含 .po 但含运行时真正读的格式。
# ---------------------------------------------------------------------------


def _production_import_names() -> set[str]:
    # 收集生产代码（根入口 + src/）里出现过的所有导入模块名，用于判定「排除项是否可达」。
    # 用 AST 而不是正则：正则会把注释与字符串里的 import 也算进去（既漏判又误判）。
    files = [ROOT / name for name in ("main.py", "gui.py", "web.py", "i18n.py", "msg_push.py")]
    files += sorted((ROOT / "src").rglob("*.py"))
    names: set[str] = set()
    for path in files:
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
    return names


def test_bloat_excludes_never_hide_a_module_that_production_imports() -> None:
    # 正向安全阀：清单里任何一项都不得是生产代码（含其父模块）会导入的模块。
    # 「等于或以其为前缀」单向查：排除 `PIL` 会让生产导入的 `PIL.Image` 一起消失
    # （该形态必须拦）；反过来排除 `PIL._avif` 而生产只导入 `PIL` 是安全的、必须放行。
    imported = _production_import_names()
    collisions = sorted(
        name
        for excluded in build_exe.BLOAT_EXCLUDES
        for name in imported
        if name == excluded or name.startswith(excluded + ".")
    )
    assert not collisions, f"排除项与生产导入冲突（冻结后会 ModuleNotFoundError）：{collisions}"


def test_bloat_excludes_still_cover_the_measured_bloat() -> None:
    # 反向：只锁「清单不许乱加」会让「把体积项删掉」也全绿。这几项是 2026-09-24 实测
    # 进产物的死重量（基线 lite 82.77MB 中的约 11.7MB），删任一项都会让体积悄悄回弹。
    for required in (
        "pydantic.v1.mypy",  # 拖入整个 mypy 包（0.71MB / 69 文件）
        "PIL._avif",  # 7.52MB，产物内最大的单个非解释器文件
        "PIL._imagingft",  # 2.07MB
        "httptools",  # 0.17MB
        "watchfiles",  # 0.61MB
        "nodejs_wheel",  # 114MB：venv 里有、requirements.txt 没有
    ):
        assert required in build_exe.BLOAT_EXCLUDES, f"体积排除清单缺 {required!r}，产物体积将回弹"


def test_every_analysis_applies_the_bloat_excludes() -> None:
    # COLLECT 把三个 Analysis 的 binaries/datas 合并去重后落同一个 _internal/，
    # 所以「只在 CLI 上排除 PIL」等于没排（GUI 收进来、CLI 产物照样带着）。
    rendered = build_exe.SPEC_TEMPLATE.format(
        app=build_exe.APP_NAME,
        bloat_excludes=list(build_exe.BLOAT_EXCLUDES),
        i18n_datas=build_exe.i18n_datas_entries(),
    )
    assert rendered.count("excludes=excludes_bloat +") == 3, "三个 Analysis 必须都挂上排除清单"


def test_i18n_datas_skip_po_sources_but_keep_runtime_formats() -> None:
    # i18n.py 的加载优先级是 .mo → .json → .yaml，*.po 是翻译源文件、运行期不读；
    # 用整目录拷贝（旧写法 ('i18n','i18n')）会把它一起打进分发包。
    entries = build_exe.i18n_datas_entries()
    assert entries, "i18n 资源清单为空（i18n/ 目录缺失或过滤条件写错）"
    sources = [src for src, _dest in entries]
    assert not [s for s in sources if s.endswith(".po")], f"i18n 资源仍含 .po 源文件：{sources}"
    suffixes = {Path(s).suffix for s in sources}
    assert {".mo", ".json", ".yaml"} <= suffixes, f"运行时格式缺失（实际 {sorted(suffixes)}）"
    # 目标路径必须仍落在 i18n/ 下：i18n.py 用 __file__ 定位 _internal/i18n，改了就找不到目录
    assert all(dest == "i18n" or dest.startswith("i18n/") for _src, dest in entries)


def test_zip_release_dir_prefixes_members_with_app_name(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 压缩接缝换成自建 zipfile 后，成员名前缀必须与旧 shutil.make_archive(root_dir=DIST,
    # base_dir=APP_NAME) 同构——_assert_zip_has_no_runtime_artifacts 靠这个前缀判运行期产物，
    # 前缀丢了那条断言会永远绿（正是它存在的意义所在）。
    release = tmp_path / build_exe.APP_NAME
    (release / "config").mkdir(parents=True)
    (release / "config" / "config.ini").write_text("[录制设置]\n", encoding="utf-8")
    monkeypatch.setattr(build_exe, "RELEASE_DIR", release)
    zip_path = tmp_path / "out.zip"
    build_exe._zip_release_dir(zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert f"{build_exe.APP_NAME}/config/config.ini" in names
        assert all(n.startswith(f"{build_exe.APP_NAME}/") for n in names), names
        # 必须是 deflate（体积优化的全部意义）
        info = zf.getinfo(f"{build_exe.APP_NAME}/config/config.ini")
        assert info.compress_type == zipfile.ZIP_DEFLATED
