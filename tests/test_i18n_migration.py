# -*- coding: utf-8 -*-
# i18n.tr() 形参迁移的静态防回归。
#
# 背景：logger/print 的 f-string 会在查目录之前先完成插值，于是目录里带占位符的
# msgid 永远匹配不上，翻译静默退化为原文（200+ 条形参日志因此长期「有翻译但用不上」）。
# 迁移把这些调用点改写为 i18n.tr(模板, **kw)——「先查表、后插值」。
#
# 本文件锁定三条不变量（全部静态成立，零运行时依赖）：
#   ① 不再出现「有价值的」logger/print f-string（防止有人改回旧写法）；
#   ② 每个 tr() 调用的模板占位符集合 == 关键字实参集合（防止改模板漏改实参）；
#   ③ 运行时模板集合 ⊆ zh_CN.po 键集合（目录覆盖完整，等价于提取器「缺失 0」）。

import ast
import importlib.util
import re
from pathlib import Path

# 项目根：本文件位于 tests/ 下，取上级目录；后续所有路径都相对它解析
ROOT = Path(__file__).resolve().parent.parent
# 与 scripts/extract_i18n_strings.py 的 LOGGER_METHODS 保持同口径：
# 只有 logger.<这些方法>(...) 的首参才被提取器视为「可翻译串」
LOGGER_METHODS = {
    "debug",
    "info",
    "success",
    "warning",
    "error",
    "critical",
    "exception",
    "trace",
    "log",
    "catch",
}


def _load_extractor() -> object:
    # 提取器是 scripts/ 下的独立脚本（不在包内），用 importlib 按文件路径加载，
    # 复用其 SCAN_FILES / scan_file / is_valuable——避免在本文件里复制一份扫描
    # 口径，否则两边一旦漂移，回归测试会与真实提取器给出不同结论（假绿/假红）
    spec = importlib.util.spec_from_file_location("_extract_i18n_probe", ROOT / "scripts" / "extract_i18n_strings.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_EX = _load_extractor()
SCAN_FILES: list[Path] = getattr(_EX, "SCAN_FILES")
is_valuable = getattr(_EX, "is_valuable")
scan_file = getattr(_EX, "scan_file")
# tr() 的模块别名集合取自提取器，避免两处硬编码各自漂移
TR_CALLER_IDS: set[str] = getattr(_EX, "TR_CALLER_IDS")


def _iter_files() -> list[Path]:
    # gui_legacy.py 已删除，SCAN_FILES 里可能仍留历史条目 → 统一用 exists() 过滤，
    # 避免因某个待扫描文件不存在而让整个回归测试误报
    return [p for p in SCAN_FILES if p.exists()]


def test_no_valuable_fstring_in_logger_or_print() -> None:
    # ① 迁移后不应再有「有价值的」f-string 出现在 logger.* 首参或 print 任意位置
    offenders: list[str] = []
    for path in _iter_files():
        src = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(src, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            is_print = isinstance(node.func, ast.Name) and node.func.id == "print"
            is_log = (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in LOGGER_METHODS
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "logger"
            )
            if not (is_print or is_log):
                continue
            args = node.args if is_print else node.args[:1]
            for arg in args:
                if not isinstance(arg, ast.JoinedStr):
                    continue
                parts: list[str] = []
                for v in arg.values:
                    if isinstance(v, ast.Constant) and isinstance(v.value, str):
                        parts.append(v.value)
                    elif isinstance(v, ast.FormattedValue):
                        parts.append("{" + (ast.get_source_segment(src, v.value) or "") + "}")
                if is_valuable("".join(parts)):
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert not offenders, "以下位置仍是 logger/print f-string（应改用 i18n.tr）：" + ", ".join(offenders)


def test_tr_template_placeholders_match_kwargs() -> None:
    # ② 每个 tr() 调用的模板占位符集合必须与关键字实参集合一致
    offenders: list[str] = []
    for path in _iter_files():
        src = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(src, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            func = node.func
            is_tr = (isinstance(func, ast.Name) and func.id == "tr") or (
                isinstance(func, ast.Attribute)
                and func.attr == "tr"
                and isinstance(func.value, ast.Name)
                and func.value.id in TR_CALLER_IDS
            )
            if not is_tr:
                continue
            first = node.args[0]
            if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
                continue
            placeholders = set(re.findall(r"\{([^{}]*)\}", first.value))
            kwargs = {kw.arg for kw in node.keywords if kw.arg}
            # 占位符必须是纯标识符：tr() 内部走 str.format，花括号里出现表达式/属性/下标
            # 会直接抛 KeyError（这正是迁移前 f-string 形态无法被目录命中的原因）
            non_ident = sorted(p for p in placeholders if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", p))
            if non_ident or placeholders != kwargs:
                offenders.append(
                    f"{path.relative_to(ROOT)}:{node.lineno} 模板={sorted(placeholders)} 实参={sorted(kwargs)}"
                    + (f" 非标识符占位符={non_ident}" if non_ident else "")
                )
    assert not offenders, "tr() 模板占位符与关键字实参不一致：\n" + "\n".join(offenders)


def test_runtime_templates_covered_by_catalog() -> None:
    # ③ 运行时提取到的模板集合必须被 zh_CN.po 键集合完全覆盖（等价于提取器「缺失 0」）
    runtime: set[str] = set()
    for path in _iter_files():
        runtime |= scan_file(path)
    # 只保留有价值串（与提取器同口径）：纯装饰线/纯占位符模板本就不入目录
    runtime = {s for s in runtime if is_valuable(s)}

    # 直接复用 compile_po 的权威 .po 解析（多行 msgid / 转义还原均正确），
    # 不自己写解析器，避免两套解析口径不一致导致误判
    spec = importlib.util.spec_from_file_location("_compile_po_probe", ROOT / "scripts" / "compile_po.py")
    assert spec is not None and spec.loader is not None
    cp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cp)
    # 剔除 gettext 头部空 msgid（目录本就不含它，不剔除会永远报「多 1 条」）
    keys = set(cp.parse_po(cp.PO_PATH)) - {""}

    missing = sorted(runtime - keys)
    assert not missing, f"目录缺失 {len(missing)} 条运行时模板：\n" + "\n".join(repr(m) for m in missing)
