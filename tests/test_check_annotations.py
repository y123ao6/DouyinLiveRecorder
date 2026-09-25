# scripts/check_annotations.py 中「符号可达性检查」的回归用例。
#
# 背景（2026-09-22）：删除模块级函数/常量只删定义、留下调用点，会让 mypy / basedpyright /
# pytest 三面同时转红；该形态已第二次复现（CODE_REVIEW_2026-09-21 补-N04），故固化成门禁动作。
# 本文件锁住三件事：
#   1) 真能报：留下调用点但全仓无绑定的名字必须被点名（含文件与行号）；
#   2) 不误报：导入 / def / 参数 / 内建 / dunder 这些有来源或由解释器注入的名字一律放行
#      ——判据是「宁漏勿噪」，误报会让门禁天天红、反而被忽略；
#   3) 当前仓库零悬空引用：将来谁删了符号留下调用点，本条立刻变红（端到端回路锁）。
#
# 全部离线：只做 AST 扫描，不执行任何子进程。

from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent


def _load_check_annotations() -> ModuleType:
    # 沿用仓内惯例（tests/test_run_gates.py）：scripts/ 不在包路径内，用
    # spec_from_file_location 显式加载，避免 sys.path 注入被 isort 重排到 import 之前
    spec = importlib.util.spec_from_file_location("_check_annotations_probe", ROOT / "scripts" / "check_annotations.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_annotations = _load_check_annotations()


def _write(root: Path, rel: str, source: str) -> None:
    # 按相对路径落盘（自动补父目录），源码统一 dedent 以便用例里缩进可读
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source), encoding="utf-8")


def test_dangling_call_site_is_reported(tmp_path: Path) -> None:
    # 复现 main.py:1346 的形态：定义已被删除，调用点留在 `and` 右侧
    _write(
        tmp_path,
        "pkg/mod.py",
        """
        # 模块头注释


        def caller(flag: bool) -> bool:
            return flag and missing_symbol(1)
        """,
    )
    _scanned, problems = check_annotations.check_dangling_symbols(tmp_path)
    assert len(problems) == 1, f"应只报一处悬空引用：{problems}"
    assert "missing_symbol" in problems[0]
    assert problems[0].startswith("pkg/mod.py:"), f"违规描述须带相对路径与行号：{problems[0]}"


def test_bound_builtin_and_dunder_names_are_not_reported(tmp_path: Path) -> None:
    # 宁漏勿噪：导入名 / def 名 / 参数 / 内建 / dunder 都不得报（否则门禁会被误报淹没）
    _write(
        tmp_path,
        "pkg/mod.py",
        """
        # 模块头注释

        import os

        CONSTANT = 1


        def helper(value: int) -> int:
            name = __name__
            return value + len(name) + CONSTANT + len(os.getcwd())
        """,
    )
    _scanned, problems = check_annotations.check_dangling_symbols(tmp_path)
    assert problems == [], f"有来源的名字不得报悬空：{problems}"


def test_wildcard_dynamic_injection_is_not_reported(tmp_path: Path) -> None:
    # 同仓另一处存在同名绑定时放行：覆盖 `from x import *` / monkeypatch / globals() 注入
    _write(tmp_path, "pkg/producer.py", "PLUGIN = 1\n")
    _write(
        tmp_path,
        "pkg/consumer.py",
        """
        # 模块头注释


        def use() -> int:
            return PLUGIN
        """,
    )
    _scanned, problems = check_annotations.check_dangling_symbols(tmp_path)
    assert problems == [], f"全仓别处有绑定的名字不得报悬空：{problems}"


def test_repository_has_no_dangling_symbols() -> None:
    # 端到端回路锁：本仓当前必须零悬空引用。谁删了模块级符号留下调用点，本条立刻变红，
    # 并会在门禁输出里收到「删前先 grep 全部调用点」的提示
    _scanned, problems = check_annotations.check_dangling_symbols(ROOT)
    assert problems == [], f"存在悬空引用：{problems}"
