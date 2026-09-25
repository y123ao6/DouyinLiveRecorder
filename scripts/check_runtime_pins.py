# 运行时二进制 SHA256 钉定表的一致性检查（SEV-10 的门禁侧，CI 可调用）。
#
# 职责：校验 build_exe.py 里那张「按平台分列的运行时二进制钉定表」的**完整性与形状**，
#       并在发布路径上要求每一项都已填入官方值。
#
# 为什么需要单独一个检查：CR-11 加的校验框架把表留成了空的 `_PINNED_RUNTIME_SHA256 = {}`，
#   未钉定只 warn 后继续（SEV-10）——「空表」在旧实现里是**静默通过**的。本脚本把
#   「空表 / 缺平台 / 缺槽位」从可跳过状态升级为硬失败，因此它是 fail-closed 机器的
#   前半段（后半段是 build_exe.py 的 --require-pinned）。
#
# 两种模式（退出码语义不同，务必区分）：
#   默认（结构模式，进 AGENTS.md「格式化命令」门禁块）
#       —— 只查表的结构：表非空、键覆盖 RELEASE_RUNTIME_KEYS、每键含全部槽位、取值要么是
#          64 位小写十六进制、要么明显是占位/可疑值。占位值只告警不判红：「官方哈希还没人工
#          核实」是开发期的常态，不该弄红每个 PR。
#   --strict（发布模式，由 build-release.yml 的 prepare job 执行）
#       —— 占位/可疑值一律判红：发布链路绝不构建未经校验的产物。
#
# 钉定值的唯一事实源是 build_exe.py 的 _PINNED_RUNTIME_SHA256：本脚本动态加载它来取表，
# 「什么算填好了」也一律问 build_exe._slot_is_gated()（= 官方哈希已钉定 ∨ 证据齐备的第 4 类
# 「源码可复现构建」），这里不复述判定——两处各判一次，迟早演化出两种「已钉定」。
# 同理**不得**把哈希副本写进 workflow：CI 用 --emit-env 的输出注入 DLR_RUNTIME_SHA256，
# 换版本只改 build_exe.py 一处。
# --strict 的失败集合只覆盖**发布矩阵真正构建的运行时键**；表里为本地/未来构建方保留的额外键
# （如 macos-x64、linux-arm64）未钉定时只告警、且**必须把告警打出来**——没有 runner 产出它们，
# 要求钉定既不拦下任何真实产物，又制造「每个键都被管住了」的错觉。矩阵覆盖检查（第 4 段）才
# 是防漏的那半。
#   [历史注] 2026-09-22 W1 前判据是 build_exe._is_pinned()，只认官方哈希那一类满足方式。
#
# 用法：
#   python scripts/check_runtime_pins.py              # 结构检查（本地门禁 / ci.yml static）
#   python scripts/check_runtime_pins.py --strict     # 发布检查（build-release.yml prepare）
#   python scripts/check_runtime_pins.py --emit-env   # 打印 DLR_RUNTIME_SHA256 的 JSON 值（CI 注入用）
#
# 退出码：0 通过；1 --strict 下存在未钉定项（发布被拦）；2 结构缺陷 / 取不到表
#         （属「门禁本身失效」，与「代码不合格」区分，同 run_gates.py 口径）。

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parent.parent

# runner 标签 → 运行时键。与 build-release.yml 的 matrix.include 三平台一致：
# windows-latest / ubuntu-latest 为 x64，macos-latest 为 arm64（Apple Silicon）。
# 若矩阵将来改用显式架构标签或加入 linux-arm64，须同步这张映射，否则会出现
# 「表里有键、矩阵里没平台」（无害）或「矩阵有平台、表里缺键」（本脚本报红）。
RUNNER_TO_RUNTIME_KEY = {
    "windows-latest": "windows-x64",
    "ubuntu-latest": "linux-x64",
    "macos-latest": "macos-arm64",
}

_OS_TAGS = ("windows", "linux", "macos")
_ARCH_TAGS = ("x64", "arm64")
_WORKFLOW = ROOT / ".github" / "workflows" / "build-release.yml"


def _load_build_exe() -> Any:
    # 以文件路径动态加载根目录 build_exe.py：scripts/ 不在包路径内，且 build_exe 在
    # import 期只做常量定义（main() 受 __name__ 守卫保护），加载是安全的。
    # 之所以「加载」而不是「AST 复制一份判定」：钉定表与其合法性判定的唯一事实源都在
    # build_exe.py，复制判定逻辑就会造出第二份事实源（本仓明令禁止并行清单）。
    path = ROOT / "build_exe.py"
    spec = importlib.util.spec_from_file_location("_runtime_pins_probe", path)
    if spec is None or spec.loader is None:
        print(f"ERROR: 无法加载 {path}", file=sys.stderr)
        sys.exit(2)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _runtime_matrix_keys() -> list[str]:
    # 从 build-release.yml 的 matrix.include 里解析出实际参与发布的 runner 标签，
    # 映射为运行时键。解析失败即报「门禁本身失效」，绝不退化成「无平台可查 → 通过」。
    if not _WORKFLOW.exists():
        print(f"ERROR: 找不到 {_WORKFLOW}，无法校验发布矩阵与钉定表的覆盖关系", file=sys.stderr)
        sys.exit(2)
    text = _WORKFLOW.read_text(encoding="utf-8")
    oses = re.findall(r"^\s*-\s*os:\s*([A-Za-z0-9._-]+)\s*$", text, re.MULTILINE)
    if not oses:
        print("ERROR: 未能从 build-release.yml 解析出 matrix 的 os 列表（结构可能已变更）", file=sys.stderr)
        sys.exit(2)
    unknown = [o for o in oses if o not in RUNNER_TO_RUNTIME_KEY]
    if unknown:
        print(
            f"ERROR: 发布矩阵出现未登记的 runner 标签 {unknown}，"
            f"请同步 scripts/check_runtime_pins.py 的 RUNNER_TO_RUNTIME_KEY",
            file=sys.stderr,
        )
        sys.exit(2)
    return [RUNNER_TO_RUNTIME_KEY[o] for o in oses]


def check(strict: bool) -> int:
    # 返回 0 通过 / 1 发布级失败（--strict 下存在未钉定项）/ 2 结构缺陷。
    module = _load_build_exe()
    table = cast("dict[str, dict[str, str]]", module._PINNED_RUNTIME_SHA256)
    slots = cast("tuple[str, ...]", module.RUNTIME_SLOTS)
    declared_keys = cast("tuple[str, ...]", module.RELEASE_RUNTIME_KEYS)
    # 判定口径一律取自 build_exe（见文件头）：本脚本不自己判形状，也不复制槽位/键清单
    slot_is_gated = cast("Any", module._slot_is_gated)
    is_marker = cast("Any", module._is_source_build_marker)
    placeholder = cast(str, module.UNVERIFIED_PIN)
    matrix_keys = _runtime_matrix_keys()

    problems: list[str] = []  # 结构缺陷 → rc=2
    unpinned: list[str] = []  # 矩阵内未钉定项 → --strict 时 rc=1
    unpinned_offmatrix: list[str] = []  # 矩阵外的键：只告警，绝不静默丢弃
    declared_class: list[str] = []  # 第 4 类已满足的槽位（显式列出，不与「已钉定」混为一谈）

    # 1) 空表必须硬失败：SEV-10 的原始缺陷形态就是「表为空且无人察觉」
    if not table:
        problems.append("_PINNED_RUNTIME_SHA256 为空——未钉定的运行时二进制会被无校验打进发布包")

    # 2) 键形状与覆盖面：声明的运行时键必须逐个存在，不得多写不认识的键
    for key in declared_keys:
        if key not in table:
            problems.append(f"缺少运行时键 {key} 的钉定段")
    for key in table:
        if key not in declared_keys:
            problems.append(f"钉定段 {key} 不在 RELEASE_RUNTIME_KEYS 内（矩阵/表漂移）")
        os_tag, _, arch_tag = key.partition("-")
        if os_tag not in _OS_TAGS or arch_tag not in _ARCH_TAGS:
            problems.append(f"钉定键 {key} 不符合 <os>-<arch> 形态")

    # 3) 每个键都要覆盖全部槽位（ffmpeg / node），且取值合法或明确未钉定
    for key, entry in table.items():
        if not isinstance(entry, dict):
            problems.append(f"{key} 的值不是 {{槽位: 哈希}} 映射")
            continue
        for slot in slots:
            value = str(entry.get(slot, ""))
            if slot not in entry:
                problems.append(f"{key} 缺少槽位 {slot} 的钉定项")
                continue
            if slot_is_gated(value, key, slot):
                if is_marker(value):
                    declared_class.append(f"{key}/{slot} 走第 4 类（源码可复现构建，三件证据齐备）")
                continue
            if is_marker(value):
                # 声明了第 4 类但证据不齐 = 与「未钉定」同等处置。这条是防「换个标记拿免检」的关键：
                # 标记若比 64 位十六进制更容易填，放宽判定就等于把闸口拆了。
                unpinned.append(f"{key}/{slot} 声明为第 4 类但证据不齐（三件证据缺任一或形状不符）")
                continue
            reason = "仍是占位标记" if value == placeholder else ("取值为空" if not value else f"形状非法（{value!r}）")
            bucket = unpinned if key in matrix_keys else unpinned_offmatrix
            bucket.append(f"{key}/{slot} 未钉定：{reason}")

    # 4) 与发布矩阵的覆盖关系（跨文件同源检查，防「矩阵加了平台、表里没这一份」）
    for key in matrix_keys:
        if key not in table:
            problems.append(f"发布矩阵需要 {key}，但钉定表无该段")

    print(f"运行时二进制钉定表：{len(table)} 个运行时键 × {len(slots)} 个槽位")
    print(f"发布矩阵运行时键：{', '.join(matrix_keys)}")

    if problems:
        print("\n[FAIL] 钉定表结构缺陷（门禁本身失效，按 rc=2 处理）:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2

    for line in declared_class:
        print(f"[NOTE] {line}")

    if unpinned_offmatrix:
        # 矩阵外的键：本地/未来构建方保留的段。只告警，但**必须打出来**——静默省略等于
        # 让后来的人以为「表里所有键都被 --strict 管着」。
        print(
            f"\n[WARN] {len(unpinned_offmatrix)} 个槽位未钉定，但其运行时键不在发布矩阵内（无 runner 产出，不参与 --strict 判定）:"
        )
        for u in unpinned_offmatrix:
            print(f"  - {u}")

    if unpinned:
        print(f"\n[WARN] {len(unpinned)} 个**矩阵内**槽位尚未钉定（官方哈希待人工核实）:")
        for u in unpinned:
            print(f"  - {u}")
        if strict:
            print(
                "\n[FAIL] --strict（发布路径）：发布矩阵所需槽位存在未钉定项即终止。"
                "请核对官方公布值后写入 build_exe.py 的 _PINNED_RUNTIME_SHA256，"
                "或由 CI 注入 DLR_RUNTIME_SHA256；上游确实不公布哈希时改走第 4 类"
                "（SOURCE-BUILD-PROVENANCE + 三件证据，见 W1）。",
                file=sys.stderr,
            )
            return 1
        print("  → 本地门禁放行；build-release.yml 的 prepare job 以 --strict 拦下发布。")
    elif not unpinned_offmatrix:
        print("\n[OK] 全部槽位均已钉定（64 位十六进制）或已按第 4 类给出齐备证据")
    return 0


def emit_env() -> int:
    # 打印 DLR_RUNTIME_SHA256 应取的 JSON（按运行时键分列），供 CI 注入 build job。
    # 占位值原样导出：build_exe 侧仍按形状判定为未钉定，因此这条通道不会把
    # 「没填」伪装成「已填」。
    module = _load_build_exe()
    table = cast("dict[str, dict[str, str]]", module._PINNED_RUNTIME_SHA256)
    print(json.dumps(table, ensure_ascii=False, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="运行时二进制 SHA256 钉定表一致性检查")
    _ = parser.add_argument("--strict", action="store_true", help="发布模式：存在未钉定项即失败")
    _ = parser.add_argument("--emit-env", action="store_true", help="输出 DLR_RUNTIME_SHA256 的 JSON 值")
    args = parser.parse_args(argv)
    if cast(bool, args.emit_env):
        return emit_env()
    return check(strict=cast(bool, args.strict))


if __name__ == "__main__":
    sys.exit(main())
