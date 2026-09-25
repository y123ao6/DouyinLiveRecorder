# 静态守卫：全仓 tests/*.py 的「测试可信度」门禁（MID-64/65/66/67 沉淀，2026-09-20）。
#
# 为什么用 AST 而不是运行时用例：这几类缺陷的共同征兆是「用例全绿但什么都没证明」
# 或「用一例拖挂整个会话」，征兆只在**别的**用例身上显现（进程级 stdlib 被改写、GC 延迟
# 抛出的告警逸出到任意后续用例），靠人眼 grep 一定会漏。本文件不 import 任何被测模块，
# 只读源码文本 + ast.parse，因此自身零副作用、秒级完成。
#
# 五条规则（R1–R4 + R6；R5 全仓无定义，是跳号而非漏实现——2026-09-23 按 grep 核对）：
#   R1 禁止改写 stdlib / 第三方模块本体（两种形态同罪，SEV-2225 补齐第二种）：
#      a) 经「别的模块的命名空间」拿到模块对象再 setattr：monkeypatch.setattr(main.time, "sleep", ...)
#         改的是全进程唯一的那个 time 模块本体，loguru enqueue 线程 / harness 守护线程 / coverage
#         都会吃到假实现（MID-66 的 10 处实例）。
#      b) 字符串形态 patch("subprocess.Popen") / patch("time.sleep")：mock 与 monkeypatch 都会先
#         按导入根 importlib 出那个 stdlib 模块对象、再 setattr 到它**本体**上，与 a) 完全同形。
#      正确写法见 AGENTS.md「测试编写强制约定」：types.SimpleNamespace(**vars(mod)) 浅拷贝后
#      setattr(模块, "名", shim)（即只替换**被测模块命名空间里的全局引用**）。
#   R2 禁止宽泛 filterwarnings("ignore::<整类告警>")（本仓「pytest 0 警告口径」要求修根因）。
#   R3 名为 known_hash / known_answer / *_kat 的用例必须断言**具体字面值**，
#      只断 isinstance/len 即假绿（MID-67 的 SM3 实例）。
#   R4 tests/ 目录里不得留下一次性调试产物（MID-64/66 排查期写下的 _exc.log 一类残留）。
#   R6 手工 pytest.MonkeyPatch() 实例必须配对 undo()：pytest 不会自动还原它们，
#      漏 undo 的用例**单独运行**永远是对的，只有全量跑才暴露成跨文件假失败。
#
# 例外表 _SANCTIONED 逐条给出理由：AGENTS.md 亲自规定的跨平台写法（config_io.os.replace 的
# 「文件只读」用例）与被守卫的形态同形，门禁不得推翻文档级约定。

import ast
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent

# 经模块命名空间改写这些模块的本体 = 全进程生效，一律禁止。
# stdlib 侧取本仓测试实际踩过的集合 + 常见的「被 main/src 直接引用」的模块；
# 第三方侧 httpx/requests/websockets 同理（main.httpx.Client 即 MID-66 的实例之一）。
# 刻意**不含 sys**：sys.frozen / sys.argv / sys.executable 是解释器状态标志，
# 没有替代手段能进入 PyInstaller 冻结分支等代码路径（tests/test_ttwid.py 的
# TestAppRootFrozen 即靠它），且 monkeypatch 会逐属性还原，不掩盖被测逻辑。
_MUTABLE_MODULE_NAMES = frozenset(
    {
        "time",
        "os",
        "datetime",
        "subprocess",
        "random",
        "shutil",
        "socket",
        "signal",
        "threading",
        "json",
        "logging",
        "math",
        "re",
        "httpx",
        "requests",
        "aiohttp",
        "websockets",
        "PIL",
        "customtkinter",
    }
)

# 字符串形态 patch("<名>.<路径>") 的判定子集：只取名单里确属标准库的那些名字。
# 为什么不整份复用 _MUTABLE_MODULE_NAMES（三方名也在其中）：判据要表达的是「改的是不是
# 全进程唯一的 stdlib 模块本体」，而 httpx/requests/PIL 等三方模块被 patch 的是**它们自己包
# 内的属性**，危害面不同；现网仍有 6 处 patch("httpx.AsyncClient")（tests/test_async_http_lock.py，
# 不属本条目范围）未迁，直接按整份名单判会让别人负责的文件无故变红。
# 取 sys.stdlib_module_names（3.10+ 提供）而不是再手写一份名字清单，避免第二事实源。
# **已知未覆盖面（不得读成「已全覆盖」）**：patch("src.x.time.sleep") 这类「首段是被测模块、
# 中间段才是 stdlib 模块」的深路径同样改到 time 本体，现网 11+ 处（SEV-2225 的兄弟形态），
# 本规则按首段判定、不覆盖它 —— **不覆盖 ≠ 合规**，扩判据前必须先迁完那些调用点。
_STDLIB_MUTABLE_NAMES = frozenset(_MUTABLE_MODULE_NAMES) & sys.stdlib_module_names

# R3 的触发词：只认「哈希/标准答案」类命名，避免把普通枚举用例误判成 KAT
_KAT_NAME_PREFIXES = ("test_known_hash", "test_known_answer", "test_kat", "test_known_vector")

# tests/ 下允许存在的非 .py 正式资产（黄金基准与前端用例目录）；其余按一次性产物处理。
# 2026-09-24 收敛：删去 `_out_e2e` —— 唯一写它的 tests/test_srt_timeline_anchor.py 已改走
# tmp_path，`tests/conftest.py::_TEST_OUT_DIRS` 也同步不再清理它；保留 `_out_live` 是因为
# 五个 `test_*_live_collector.py` 双模式脚本（含真机验证）仍往该目录写 SRT。
# 注意（避免误读成本次改动有行为变化）：下方 R4 的谓词只筛 `.is_file()` 且 `suffix == ".py"`
# 的条目，目录名在此处不参与判定（它们只在 `_TEST_OUT_DIRS` 那边才承担清理语义），
# 所以本项收敛是「名单与实际写入方对齐」，不是放宽门禁。
_ALLOWED_TESTS_ENTRIES = frozenset({"__init__.py", "conftest.py", "__pycache__", "golden", "frontend", "_out_live"})

_SANCTIONED: dict[str, frozenset[str]] = {
    # AGENTS.md「『文件只读』用例不能只靠 chmod(0o444)」条目明文规定的写法：
    # os.replace 是 config_io 原子写的唯一失败点，Windows/Linux 语义不同，只能在此处拦截；
    # 该条目同时要求「其余路径透传真实 os.replace」，影响面受控。
    "test_config_io_readonly.py": frozenset({"os.replace"}),
}


def _test_files() -> list[Path]:
    # 只扫 tests/ 顶层正式用例；tests/frontend/*.mjs 是 Node 用例，不在本门禁范围内
    return sorted(p for p in _TESTS_DIR.glob("test_*.py") if p.is_file())


def _dotted_name(node: ast.AST) -> str | None:
    # a.b.c -> "a.b.c"；下标/调用等复杂表达式返回 None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return None if base is None else base + "." + node.attr
    return None


def _is_setter(fname: str | None) -> bool:
    # setattr 家族：setattr(obj, "name", v) / monkeypatch.setattr(...) / mock.patch.object(...)
    # —— 约定第一参是「被改的容器」、第二参是属性名字面量，故容器是模块对象时就构成 R1 违例。
    if fname is None:
        return False
    return fname == "setattr" or fname.endswith(".setattr") or fname.endswith("patch.object")


def _is_dotted_target_call(fname: str | None) -> bool:
    # 首参是「点路径字符串」的替身写法：patch("a.b") / mock.patch("a.b") /
    # monkeypatch.setattr("a.b", v) —— 三者都先解析出 a.b 的**容器对象**再 setattr。
    # 刻意不含 patch.object(obj, "name")：它的 obj 是 AST 里的真模块对象，走 _is_setter 那一支。
    if fname is None:
        return False
    return fname == "patch" or fname.endswith(".patch") or fname.endswith(".setattr")


def _stdlib_body_key_from_dotted(target: ast.expr) -> str | None:
    # R1 的字符串形态：返回违规键 "subprocess.Popen"，合规时 None。
    # 判据只看**首段**：mock/monkeypatch 解析 "a.b.c" 时会 importlib 出顶层包 a、沿 getattr 链
    # 走到 a.b，最后 setattr(a.b, "c", 替身)。故 a 是 stdlib 顶层模块名时，被改对象就是
    # 全进程唯一的 stdlib 模块本体 —— 与被拦下的 setattr(模块对象, "c", ...) 同形同害。
    if not isinstance(target, ast.Constant) or not isinstance(target.value, str):
        return None
    parts = target.value.split(".")
    if len(parts) < 2:
        return None
    if parts[0] not in _STDLIB_MUTABLE_NAMES:
        return None
    return target.value


def _module_body_mutation_calls(tree: ast.Module) -> list[tuple[int, str]]:
    # R1：返回 [(行号, "被改模块.属性名"), ...]
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        fname = _dotted_name(node.func)
        target = node.args[0]
        # 两支的分流判据是「首参是不是点路径字符串」，不是函数名：
        # monkeypatch.setattr 同时出现在两支里（setattr("time.sleep", v) 是字符串形态、
        # setattr(main.time, "sleep", v) 是对象形态），早期实现按函数名互斥处理，
        # 会让后者整条被 continue 掉——R1 的原有 setattr 判据当场失效（由
        # test_guard_actually_catches_the_patterns 抓到，勿再改回去）。
        if _is_dotted_target_call(fname) and isinstance(target, ast.Constant) and isinstance(target.value, str):
            key = _stdlib_body_key_from_dotted(target)
            if key is not None:
                out.append((node.lineno, key))
            continue
        if not _is_setter(fname):
            continue
        # 对象形态只认 setattr(obj, "name")（obj 必须是属性访问，如 main.time / config_io.os）
        #   [历史注] 2026-09-23 前此处写着「字符串形态在本仓未使用」，实测相反（test_main_fixes /
        #   test_spider_fixes 共 6 处 patch("subprocess.Popen"|"subprocess.run") 在用），
        #   字符串形态已由上面的首支判据接管。
        if not isinstance(target, ast.Attribute):
            continue
        owner = target.attr  # main.time -> "time"；config_io.os -> "os"
        if owner not in _MUTABLE_MODULE_NAMES:
            continue
        attr = ""
        if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
            attr = str(node.args[1].value)
        out.append((node.lineno, f"{owner}.{attr}"))
    return out


def _broad_filterwarnings_calls(tree: ast.Module) -> list[tuple[int, str]]:
    # R2：pytest.mark.filterwarnings 里出现整类/全量 ignore
    out: list[tuple[int, str]] = []
    broad = (
        "RuntimeWarning",
        "UserWarning",
        "Warning",
        "DeprecationWarning",
        "PendingDeprecationWarning",
        "WarningMessage",
    )
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _dotted_name(node.func) != "pytest.mark.filterwarnings":
            continue
        for arg in node.args:
            text = arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None
            if text is None:
                out.append((node.lineno, "<非字面量参数，无法审计>"))
                continue
            if not text.startswith("ignore"):
                continue
            # 「ignore:具体消息:具体告警类」是精确过滤，允许；整类 / 无类别 / 全量禁止。
            # 注意 filterwarnings 的完整语法是 action:message:category:module:lineno，
            # 「ignore::RuntimeWarning」split 后 message 为空、category 在第 3 段——
            # 早期实现只按 "::" 切，会把 ignore:msg:ResourceWarning 这种精确过滤误判为宽泛。
            parts = text.split(":")
            category = parts[2].strip() if len(parts) > 2 else ""
            if not category or category in broad or category == "Exception":
                out.append((node.lineno, text))
    return out


def _has_literal_equality(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    # KAT 断言的最低门槛：存在一次 Eq 比较，且比较对象不是「整数/布尔字面量」——
    # 于是 isinstance(x, str) + len(x) == 64 这种假绿形态不算数，
    # 而 x == "66c7f0..."（字面摘要）与 x == digest（参数化进来的模块级字面量表）都算。
    # 局限：只比对两个变量的 r1 == r2 也会被放行，所以触发词刻意只认 known_hash/known_answer/
    # kat/known_vector 前缀（这类命名才承诺「外部标准答案」）。
    for node in ast.walk(func):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, ast.Eq) for op in node.ops):
            continue
        operands = [node.left, *node.comparators]
        for operand in operands:
            if isinstance(operand, ast.Constant):
                if isinstance(operand.value, str) or isinstance(operand.value, bytes):
                    return True
                continue  # int/bool/None 字面量：len()==64 之类不算真值断言
            if isinstance(operand, ast.Name):
                return True
            if isinstance(operand, ast.Subscript):
                return True
    return False


def _fake_kat_funcs(tree: ast.Module) -> list[tuple[int, str]]:
    # R3：自称「已知标准值」却没有任何字面等价断言的用例
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(node.name.startswith(p) for p in _KAT_NAME_PREFIXES):
            continue
        if not _has_literal_equality(node):
            out.append((node.lineno, node.name))
    return out


@pytest.mark.parametrize("path", _test_files(), ids=lambda p: p.name)
def test_no_stdlib_module_body_mutation(path: Path) -> None:
    # R1 回归锁（MID-66 的 setattr 形态 + SEV-2225 的字符串形态）：实例已改为浅拷贝 shim，此处防止再被写回来
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    allowed = _SANCTIONED.get(path.name, frozenset())
    hits = _module_body_mutation_calls(tree)
    offenders = [(ln, key) for ln, key in hits if key not in allowed]
    assert not offenders, (
        f"{path.name} 改写了 stdlib 模块本体（全进程生效：harness 守护线程 / loguru enqueue 线程 / coverage "
        f"都会吃到假实现；patch('subprocess.Popen') 这类字符串形态与 setattr(模块.time, 'sleep', ...) 同罪）。"
        f"须改 types.SimpleNamespace(**vars(mod)) 浅拷贝后 setattr(被测模块, 名, shim): "
        + ", ".join(f"第{ln}行 {key}" for ln, key in offenders)
    )


@pytest.mark.parametrize("path", _test_files(), ids=lambda p: p.name)
def test_no_broad_filterwarnings(path: Path) -> None:
    # R2 回归锁（MID-65）：全仓唯一一处 ignore::RuntimeWarning 已移除并修根因（在
    # tests/test_async_http_lock.py）。宽泛过滤之所以禁止：协程类告警由 GC 延迟触发、会逸出到
    # 任意后续用例，ignore 既拦不住也顺手吃掉「实现里真有个 never-awaited 协程」这个缺陷；
    # 精确到消息 + 类别的 ignore 不在禁止之列（判据见 _broad_filterwarnings_calls 的分段口径）。
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits = _broad_filterwarnings_calls(tree)
    assert not hits, f"{path.name} 使用宽泛 filterwarnings（0 警告口径要求修根因）: " + ", ".join(
        f"第{ln}行 {text!r}" for ln, text in hits
    )


@pytest.mark.parametrize("path", _test_files(), ids=lambda p: p.name)
def test_digest_reference_tests_pin_concrete_values(path: Path) -> None:
    # R3 回归锁（MID-67）：SM3 那条假绿已补真值，此处防同类「只断长度」再出现
    # （函数名刻意不以 test_known_hash 开头，否则本门禁会扫到自己）
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits = _fake_kat_funcs(tree)
    assert not hits, f"{path.name} 的 known-hash/KAT 用例没有字面值断言（任何实现都能过）: " + ", ".join(
        f"第{ln}行 {name}" for ln, name in hits
    )


def test_no_stray_debug_artifacts_in_tests_dir() -> None:
    # R4：一次性排查产物（_exc.log / *.tmp / 临时脚本）不得留在 tests/。
    # 本条同时是自我约束——门禁自身若开始写文件，下一轮就会变红。
    stray = [
        p.name
        for p in _TESTS_DIR.iterdir()
        if p.is_file() and p.name not in _ALLOWED_TESTS_ENTRIES and not p.name.startswith("test_") and p.suffix == ".py"
    ]
    # 只拦「.py 但不是 test_ 前缀」的临时脚本 + 已知调试日志后缀，避免误伤 README 类文档
    stray += [p.name for p in _TESTS_DIR.glob("*.log") if p.is_file()]
    assert not stray, f"tests/ 下存在一次性调试产物（收尾须删除）: {sorted(set(stray))}"


def test_guard_actually_catches_the_patterns() -> None:
    # 自检：门禁不得退化成「扫不到任何东西的绿灯」。用等价违规片段逐条验证能报。
    bad_r1 = ast.parse('monkeypatch.setattr(main.time, "sleep", lambda s: None)\n')
    bad_r2 = ast.parse('@pytest.mark.filterwarnings("ignore::RuntimeWarning")\ndef test_x():\n    pass\n')
    bad_r3 = ast.parse(
        "def test_known_hash():\n    result = SM3().sum('abc', output_format='hex')\n    assert len(result) == 64\n"
    )
    assert _module_body_mutation_calls(bad_r1) == [(1, "time.sleep")], "R1 失效：setattr(main.time, ...) 未被发现"
    assert _broad_filterwarnings_calls(bad_r2), "R2 失效：ignore::RuntimeWarning 未被发现"
    assert _fake_kat_funcs(bad_r3), "R3 失效：只断长度的 KAT 用例未被发现"

    # 反向自检：合规写法不得误报（浅拷贝 shim / 命名空间重绑 / 精确过滤 / 带真值的 KAT）
    good_r1 = ast.parse('monkeypatch.setattr(main, "time", shim)\n')
    # patch("src.spider.time") 是把 src.spider 命名空间里的 time 重绑为替身，不改 stdlib 本体
    good_r1b = ast.parse('patch.object(spider, "time", shim)\n')
    good_r2 = ast.parse('@pytest.mark.filterwarnings("ignore:by e:ResourceWarning")\ndef test_x():\n    pass\n')
    good_r3 = ast.parse("def test_known_hash():\n    assert md5('hello') == '5d41402abc4b2a76b9719d911017c592'\n")
    # 参数化 KAT：期望值来自模块级字面量表，比较对象是变量名——同样视为已钉死
    good_r3b = ast.parse(
        "def test_known_hash(msg, digest):\n    assert SM3().sum(msg, output_format='hex') == digest\n"
    )
    assert not _module_body_mutation_calls(good_r1), "R1 误报：浅拷贝 shim 写法被拦"
    assert not _module_body_mutation_calls(good_r1b), "R1 误报：项目模块命名空间重绑被拦"
    assert not _broad_filterwarnings_calls(good_r2), "R2 误报：精确过滤被拦"
    assert not _fake_kat_funcs(good_r3), "R3 误报：真值 KAT 被拦"
    assert not _fake_kat_funcs(good_r3b), "R3 误报：参数化 KAT 被拦"


def test_guard_catches_string_form_stdlib_module_patch() -> None:
    # SEV-2225 的反向见证（防「新判据自己就是假绿」）：合成样本里三种字符串形态改写 stdlib
    # 模块本体都必须被报出。逐条断言**具体键**，不只看「有没有报」——
    # 只断非空会让「把 os.replace 误报成 subprocess.Popen」这类判据错位照样通过。
    bad_popen = ast.parse('with patch("subprocess.Popen", return_value=fake):\n    pass\n')
    bad_run = ast.parse('with patch("subprocess.run", side_effect=fake_run):\n    pass\n')
    # monkeypatch.setattr 的点路径首参同罪：解析后 setattr 的容器就是 stdlib 模块本体
    bad_mp_setattr = ast.parse('monkeypatch.setattr("time.sleep", lambda s: None)\n')
    want_popen = [(1, "subprocess.Popen")]
    want_run = [(1, "subprocess.run")]
    want_mp = [(1, "time.sleep")]
    assert _module_body_mutation_calls(bad_popen) == want_popen, "R1 失效：patch('subprocess.Popen') 未被发现"
    assert _module_body_mutation_calls(bad_run) == want_run, "R1 失效：patch('subprocess.run') 未被发现"
    assert _module_body_mutation_calls(bad_mp_setattr) == want_mp, "R1 失效：setattr('time.sleep', ...) 未被发现"


def test_guard_allows_module_namespace_shim_for_subprocess() -> None:
    # SEV-2225 的合规侧见证：仓内规定范式（浅拷贝 + 只换被测模块命名空间里的引用）不得被误报，
    # 否则这条判据会把 test_record_failure_feedback.py / test_main_fixes.py 迁移后的写法一起打死，
    # 后来者只会把判据删掉而不是改写法。
    good_shim = ast.parse(
        "shim = types.SimpleNamespace(**vars(subprocess))\n"
        "shim.Popen = FakePopen\n"
        'monkeypatch.setattr(video_postprocess, "subprocess", shim)\n'
    )
    # 字符串形态、但被改容器是**项目模块自身的属性**（现网主流写法，如 patch("src.spider.async_req")）：
    # 改的是 src.spider 命名空间里的名字，不涉及 stdlib 本体
    good_dotted_project_root = ast.parse('patch("src.spider.async_req", new=fake_req)\n')
    # patch.object 的容器是 AST 里的真模块对象、不是字符串，走另一支判据
    good_patch_object = ast.parse('with patch.object(utils, "subprocess", shim):\n    pass\n')
    assert not _module_body_mutation_calls(good_shim), "R1 误报：浅拷贝 shim + 换被测模块全局引用的合规写法被拦"
    assert not _module_body_mutation_calls(good_dotted_project_root), "R1 误报：首段为被测模块的点路径替身被拦"
    assert not _module_body_mutation_calls(good_patch_object), "R1 误报：patch.object(项目模块, ...) 被拦"


def test_scan_root_is_not_empty() -> None:
    # 兜底：路径解析错位时 glob 会扫到 0 个文件、三条参数化用例集体「空跑通过」——
    # 正是本文件要消灭的假绿形态，故显式断言扫描根与文件数。
    files = _test_files()
    assert len(files) > 50, f"tests/ 用例文件数异常（{len(files)}），扫描根目录可能错位: {_TESTS_DIR}"
    assert (_REPO_ROOT / "main.py").exists()


def _manual_monkeypatch_violations(tree: ast.AST) -> list[str]:
    # R6：手工 `pytest.MonkeyPatch()` 实例不会被 pytest 自动还原，必须自己 undo()。
    # 本仓已因此付出过一次真实代价：src/sync_http.py 的代理用例在同一会话里发出了
    # 一次未打桩的出站请求（漏 undo 的补丁把 src.utils.handle_proxy_addr 置空，
    # 令代理分支静默落到直连分支），表现为 11 条「跨文件假失败」。
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        created = 0
        undone = 0
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Call):
                continue
            func = inner.func
            if isinstance(func, ast.Attribute) and func.attr == "undo":
                undone += 1
            elif (
                isinstance(func, ast.Attribute)
                and func.attr == "MonkeyPatch"
                and isinstance(func.value, ast.Name)
                and func.value.id == "pytest"
            ):
                created += 1
        if created > undone:
            offenders.append(f"{node.name}:{node.lineno} 创建 {created} 个、undo {undone} 个")
    return offenders


@pytest.mark.parametrize("path", _test_files(), ids=lambda p: p.name)
def test_manual_monkeypatch_instances_are_undone(path: Path) -> None:
    # 逐文件判据。漏 undo 的用例在**单独运行**时永远是对的，只有全量跑才暴露——
    # 所以这条必须扫全部 tests/，不能只扫被改文件。
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    offenders = _manual_monkeypatch_violations(tree)
    assert not offenders, f"{path.relative_to(_REPO_ROOT)} 有手工 MonkeyPatch 未配对 undo(): {offenders}"


def test_guard_r6_actually_catches_a_leaked_monkeypatch() -> None:
    # 反向见证（防空门禁）：合成一段「创建了却从不 undo」的源码，判据必须报出来；
    # 再给一段配对正确的，必须不报——否则 R6 只是摆设。
    bad = ast.parse("def test_x():\n    mp = pytest.MonkeyPatch()\n    mp.setattr(a, 'b', 1)\n")
    assert _manual_monkeypatch_violations(bad), "R6 判据失效：漏 undo 的形态没被抓到"
    good = ast.parse("def test_y():\n    mp = pytest.MonkeyPatch()\n    mp.setattr(a, 'b', 1)\n    mp.undo()\n")
    assert not _manual_monkeypatch_violations(good), "R6 误报：配对 undo() 的合规写法被拦"
