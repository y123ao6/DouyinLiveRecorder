#!/usr/bin/env python3
# Per-module coverage gate check.
#
# Reads the .coverage data file produced by pytest-cov and verifies that each
# declared module meets its minimum coverage threshold.
#
# Thresholds mirror the comments in pyproject.toml:
#    spider.py  >= 50%   stream.py  >= 70%   utils.py   >= 80%
#    ttwid.py   >= 85%   ab_sign.py >= 95%   proxy.py   >= 50%
#
# Usage:
#    # After running pytest with coverage
#    pytest --cov=src --cov-report=term-missing
#    python scripts/check_coverage.py
#
#    # Or specify a custom .coverage data file
#    python scripts/check_coverage.py --data-file path/to/.coverage

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import cast

# -- Per-module coverage thresholds ------------------------------------------
# Keep in sync with pyproject.toml comments
MODULE_THRESHOLDS: dict[str, float] = {
    "src/spider.py": 50,
    "src/stream.py": 70,
    "src/utils.py": 80,
    "src/ttwid.py": 85,
    "src/ab_sign.py": 95,
    "src/proxy.py": 50,
}

# coverage JSON 报告为嵌套异构 dict，统一以 dict[str, object] 建模，读取处用 cast 收敛
CoverageData = dict[str, object]


def _get_coverage_json(data_file: str | None) -> CoverageData:
    # Generate and parse a coverage JSON report.
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        cmd = [sys.executable, "-m", "coverage", "json", "-o", tmp_path]
        if data_file:
            cmd.extend(["--data-file", data_file])

        # 加超时与显式编码：防止 coverage 挂起卡死 CI，并兼容 Windows 非 UTF-8 locale
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            print(f"ERROR: coverage json timed out: {' '.join(cmd)}")
            sys.exit(2)

        if result.returncode != 0:
            # coverage json 可能因全局 fail_under 未达标而返回非零退出码（报告仍已生成），
            # 真正的失败以「JSON 能否生成并解析」为准，此处仅提示不中断。
            print(f"WARN: coverage json exited with code {result.returncode}:\n{result.stderr}", file=sys.stderr)

        try:
            with open(tmp_path, encoding="utf-8") as f:
                return cast(CoverageData, json.load(f))
        except OSError, ValueError:
            print(f"ERROR: failed to read coverage json report: {tmp_path}")
            sys.exit(2)
    finally:
        # 无论成功、失败还是提前退出，都清理临时文件
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


def _find_module_coverage(coverage_data: CoverageData, module_path: str) -> CoverageData | None:
    # Locate a module's coverage data in the JSON report.
    files = cast(dict[str, CoverageData], coverage_data.get("files", {}))

    # Direct match
    if module_path in files:
        return files[module_path]

    # 2026-09-12 审查 6.7：原模糊匹配过宽——`Path(file).name == Path(module).name`
    # 会按**纯文件名**命中任意同名文件（如 src/utils.py 的配置命中 tests/utils.py、
    # 或 vendor 目录下的同名模块），读到的覆盖率根本不是目标模块，门禁据此判定
    # 通过 = 静默变绿。改为按「规范化相对路径」匹配，逐级收紧：
    module_normalized = Path(module_path).as_posix()

    # 归一化两侧：去 src/ 前缀与盘符，使 "src/x.py" 与 "x.py" 可互相匹配
    def _norm(p: str) -> str:
        q = Path(p).as_posix()
        if q.startswith("src/"):
            q = q[4:]
        return q

    module_norm = _norm(module_normalized)
    # ① 相对路径完全相等（覆盖 src/ 前缀差异）
    for file_path, file_data in files.items():
        if _norm(file_path) == module_norm:
            return file_data
    # ② 路径后缀匹配，但必须以 "/" 边界起始——避免 "myutils.py" 命中 "utils.py"
    for file_path, file_data in files.items():
        file_norm = _norm(file_path)
        if file_norm.endswith("/" + module_norm) or file_norm.endswith("/src/" + module_norm):
            return file_data
    # ③ 仅当 module_path 本身不含目录（配置里写的就是纯文件名）时，才允许按文件名
    #    匹配，且限定父目录为 src 或项目根——不再无门槛接受任意同名文件
    if "/" not in module_normalized:
        for file_path, file_data in files.items():
            file_norm_path = Path(file_path)
            if file_norm_path.name == module_normalized and file_norm_path.parent.name in ("src", ""):
                return file_data

    return None


def check_coverage(data_file: str | None = None) -> int:
    # Check per-module coverage thresholds. Returns 0 if all pass, 1 otherwise.
    coverage_data = _get_coverage_json(data_file)

    failures: list[tuple[str, float, float]] = []
    passes: list[tuple[str, float, float]] = []
    missing_modules: list[str] = []

    for module_path, threshold in sorted(MODULE_THRESHOLDS.items()):
        file_data = _find_module_coverage(coverage_data, module_path)

        if file_data is None:
            missing_modules.append(module_path)
            continue

        summary = cast(CoverageData, file_data.get("summary", {}))
        coverage_pct = cast(float, summary.get("percent_covered", 0.0))

        if coverage_pct >= threshold:
            passes.append((module_path, coverage_pct, threshold))
        else:
            failures.append((module_path, coverage_pct, threshold))

    # Print results
    print("=" * 60)
    print("Per-module coverage gate")
    print("=" * 60)

    if passes:
        print(f"\n[PASS] {len(passes)} module(s) meet threshold:")
        for module, pct, threshold in passes:
            print(f"   {module:25s} {pct:5.1f}%  (>= {threshold:.0f}%)")

    if missing_modules:
        print(f"\n[FAIL] {len(missing_modules)} module(s) missing from coverage data:")
        for module in missing_modules:
            print(f"   {module}")
        # 模块在覆盖率数据里查不到，通常意味着 .coverage 未采集到它、或 --cov=src 未生效。
        # 这是「门禁失效」而非「达标」，必须判失败——否则会输出
        # 「PASSED: All 0 module(s) meet coverage threshold」的假绿。
        print("       （查不到即视为门禁失效，按失败处理）")

    if failures or missing_modules:
        if failures:
            print(f"\n[FAIL] {len(failures)} module(s) below threshold:")
            for module, pct, threshold in failures:
                deficit = threshold - pct
                print(f"   {module:25s} {pct:5.1f}%  (>= {threshold:.0f}%)  <- {deficit:.1f}% short")
        print(f"\n{'=' * 60}")
        print(f"FAILED: {len(failures)} module(s) below threshold, {len(missing_modules)} module(s) missing from data")
        print(f"{'=' * 60}")
        return 1

    print(f"\n{'=' * 60}")
    print(f"PASSED: All {len(passes)} module(s) meet coverage threshold")
    print(f"{'=' * 60}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Per-module coverage gate check")
    _ = parser.add_argument(
        "--data-file",
        type=str,
        default=None,
        help="Path to .coverage data file (auto-detected by default)",
    )
    args = parser.parse_args()
    sys.exit(check_coverage(data_file=cast(str | None, args.data_file)))


if __name__ == "__main__":
    main()
