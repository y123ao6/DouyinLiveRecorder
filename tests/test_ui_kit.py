# tests/test_ui_kit.py —— src/ui_kit.py 的回归锁（阶段4 GUI 控件层）。
#
# 组织：DataTable.sync 的行级增量语义是本模块的核心安全不变量（「不再闪烁、点击不落空」的
# 结构保证），用假 Treeview 记录调用面无头锁住——未变化行零触碰 / 只改差异行 / 顺序收敛，
# 删掉生产实现任一条判据必须转红（变异验证）。工厂与浮层单元格编辑器的真实 Tk 行为走
# 真窗用例（无显示环境 skip，与 tests/test_ui_theme.py 的 TestApplyTtk 同一口径）。
#
# 替身口径：DataTable 只依赖注入的 tree 对象，不建窗；替身只复刻 sync 用到的那一小片
# Treeview 协议（get_children/insert/delete/item/move），不模拟其余行为。

import ast
import tkinter as tk
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, cast

import pytest

from src.ui_kit import DataTable

ROOT = Path(__file__).resolve().parents[1]

_COLUMNS = [
    ("name", "主播名称", 3, "w"),
    ("set_quality", "设置画质", 1, "w"),
    ("switch", "切换画质", 2, "w"),
]


class FakeTree:
    # 只复刻 DataTable.sync/clear 用到的 Treeview 协议切片，并记录每次变更调用。
    def __init__(self) -> None:
        self.rows: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
        self.order: list[str] = []
        self.calls: list[tuple[str, str]] = []

    def get_children(self) -> list[str]:
        return list(self.order)

    def delete(self, *iids: str) -> None:
        for iid in iids:
            self.rows.pop(iid, None)
            self.order.remove(iid)
            self.calls.append(("delete", iid))

    def insert(self, _parent: str, _index: str, iid: str, values: tuple[str, ...], tags: tuple[str, ...]) -> None:
        self.rows[iid] = (tuple(values), tuple(tags))
        self.order.append(iid)
        self.calls.append(("insert", iid))

    def item(self, iid: str, field: str | None = None, **kwargs: object) -> object:
        # setter 形态（tree.item(iid, values=..., tags=...)）：更新并记录变更调用
        if kwargs:
            values, tags = self.rows[iid]
            if "values" in kwargs:
                values = tuple(kwargs["values"])  # type: ignore[arg-type]
            if "tags" in kwargs:
                tags = tuple(kwargs["tags"])  # type: ignore[arg-type]
            self.rows[iid] = (values, tags)
            self.calls.append(("item", iid))
            return None
        values, tags = self.rows[iid]
        if field == "values":
            return list(values)
        if field == "tags":
            return list(tags)
        raise AssertionError(f"unexpected item() access: {field}")

    def move(self, iid: str, _parent: str, index: int) -> None:
        self.order.remove(iid)
        self.order.insert(index, iid)
        self.calls.append(("move", iid))


def _make_table() -> tuple[DataTable, FakeTree]:
    tree = FakeTree()
    table = DataTable.__new__(DataTable)
    # 绕过 __init__（它要真 Tk 建 Treeview）：只装配 sync/clear 用到的字段——
    # 与 tests/test_gui_tail_robustness.py 的 object.__new__ 桩同一口径。
    table.tree = tree  # type: ignore[assignment]
    table._columns = tuple(_COLUMNS)
    table._weights = tuple(c[2] for c in _COLUMNS)
    table._editor = None
    table._editor_column = None
    table._editor_handlers = None
    return table, tree


_ROWS = {
    "A": ("主播A", "原画", ""),
    "B": ("主播B", "高清", ""),
}

# 行 key 带空格（「序号N 主播名」的真实形态）：Treeview iid 含空格必须安全——
# tkinter 经 Tcl 参数化调用传递，若有人改回「自行拼字符串进 Tcl」的写法这里当场炸。
_ROWS_SPACED_KEY = "序号1 主播A"


def _rows_of(**overrides: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    rows: dict[str, tuple[str, ...]] = {k: v for k, v in _ROWS.items()}
    rows.update(overrides)
    return rows


class TestSyncIncremental:
    # 增量语义六格：本类的每条判据都对应 sync 的一个差异分支（插入/零触碰/单行更新/
    # 标记更新/删除/顺序收敛），变异验证把 sync 改回「整表删除重建」时须整体转红。

    def test_inserts_new_rows_in_order(self) -> None:
        table, tree = _make_table()
        # 首轮全量插入：调用面只允许 insert（不允许以 delete 兜底）
        table.sync(["A", "B"], _rows_of(), {"A": ("normal",), "B": ("normal",)})
        assert tree.order == ["A", "B"]
        assert tree.rows["A"] == (_ROWS["A"], ("normal",))
        assert all(kind == "insert" for kind, _ in tree.calls)

    def test_insert_with_spaced_key(self) -> None:
        # 生产键是「序号N 主播名」（含空格）：以空格 key 走一遍插入+更新
        table, tree = _make_table()
        table.sync([_ROWS_SPACED_KEY], {_ROWS_SPACED_KEY: _ROWS["A"]}, {_ROWS_SPACED_KEY: ("normal",)})
        assert tree.order == [_ROWS_SPACED_KEY]
        table.sync([_ROWS_SPACED_KEY], {_ROWS_SPACED_KEY: _ROWS["B"]}, {_ROWS_SPACED_KEY: ("normal",)})
        assert ("item", _ROWS_SPACED_KEY) in tree.calls

    def test_unchanged_rows_are_never_touched(self) -> None:
        table, tree = _make_table()
        table.sync(["A", "B"], _rows_of(), {"A": ("normal",), "B": ("normal",)})
        tree.calls.clear()
        table.sync(["A", "B"], _rows_of(), {"A": ("normal",), "B": ("normal",)})
        # 核心判据：无变化轮零触碰（旧实现每轮 destroy+重建正败于此）
        assert tree.calls == [], f"未变化轮不应有任何变更调用: {tree.calls}"

    def test_only_changed_row_is_updated(self) -> None:
        table, tree = _make_table()
        table.sync(["A", "B"], _rows_of(), {"A": ("normal",), "B": ("normal",)})
        tree.calls.clear()
        table.sync(["A", "B"], _rows_of(B=("主播B", "超清", "")), {"A": ("normal",), "B": ("normal",)})
        assert ("item", "B") in tree.calls
        assert all(iid == "B" for _kind, iid in tree.calls), f"更新波及了无关行: {tree.calls}"
        assert tree.rows["B"][0] == ("主播B", "超清", "")

    def test_tag_change_is_updated(self) -> None:
        # 标记（降级/断连行着色载体）变化也要走 item() 更新，而不是重建行
        table, tree = _make_table()
        table.sync(["A", "B"], _rows_of(), {"A": ("normal",), "B": ("normal",)})
        tree.calls.clear()
        table.sync(["A", "B"], _rows_of(), {"A": ("downgraded",), "B": ("normal",)})
        assert ("item", "A") in tree.calls
        assert tree.rows["A"][1] == ("downgraded",)

    def test_removed_row_is_deleted(self) -> None:
        # 消失行必须走 delete 且只删该行——「停止录制后旧行残留」是旧实现同族缺陷面
        table, tree = _make_table()
        table.sync(["A", "B"], _rows_of(), {"A": ("normal",), "B": ("normal",)})
        tree.calls.clear()
        table.sync(["A"], _rows_of(A=_ROWS["A"]), {"A": ("normal",)})
        assert tree.calls == [("delete", "B")]
        assert tree.order == ["A"]

    def test_reorder_converges_without_rebuild(self) -> None:
        # 顺序收敛只允许 move（行对象不动）：destroy+重建顺序的写法在这里当场红
        table, tree = _make_table()
        table.sync(["A", "B"], _rows_of(), {"A": ("normal",), "B": ("normal",)})
        tree.calls.clear()
        table.sync(["B", "A"], _rows_of(), {"A": ("normal",), "B": ("normal",)})
        assert tree.order == ["B", "A"]
        assert all(kind != "delete" and kind != "insert" for kind, _ in tree.calls), "顺序收敛不得重建行"

    def test_clear_removes_all_rows(self) -> None:
        # clear() 供「停止录制清空重开」路径使用：只清行，不得动列宽/表头（由列配置承载）
        table, tree = _make_table()
        table.sync(["A", "B"], _rows_of(), {"A": ("normal",), "B": ("normal",)})
        tree.calls.clear()
        table.clear()
        assert tree.order == [] and tree.rows == {}
        assert tree.calls and all(kind == "delete" for kind, _ in tree.calls)

    def test_missing_values_key_does_not_abort_sync(self) -> None:
        # 行为锁①：keys 是展示集合、values/tags 是两个独立字典，三者脱节在热更新
        # 竞态里是真实可发生的形态。旧实现 values[key] 直索引抛 KeyError——**整轮 sync
        # 半途而废**：异常点之后的行不插入、删除与顺序收敛都不执行，表格静默停在旧数据
        # 上且日志一条没有（比缺一格难看的数据严重得多）。定稿 values.get(key, ())：
        # 缺值行落空元组照常存在，其余行完整同步。
        table, tree = _make_table()
        changed = table.sync(["A", "B"], {"A": _ROWS["A"]}, {})
        assert tree.order == ["A", "B"], "缺值行不得带走整轮同步"
        assert tree.rows["B"] == ((), ())
        assert changed == ["A", "B"]
        # 后续轮次仍能被同一 key 正常接管（空行不是终态）
        table.sync(["A", "B"], _rows_of(), {"A": ("normal",), "B": ("normal",)})
        assert tree.rows["B"][0] == _ROWS["B"]

    def test_row_with_both_value_and_tag_change_counts_once(self) -> None:
        # 行为锁②：changed 的语义是「这一行变了」，不是「变了几个字段」。旧实现值
        # 分支与标记分支各自 append(key)，两者同变的行在返回值里出现两遍——调用方的
        # 「变化行高亮衰减」会对同一行叠两轮动画。行级增量语义不得回退（未变化行零触碰
        # 由 test_unchanged_rows_are_never_touched 守着）。
        table, tree = _make_table()
        table.sync(["A"], _rows_of(A=_ROWS["A"]), {"A": ("normal",)})
        changed = table.sync(["A"], _rows_of(A=_ROWS["B"]), {"A": ("downgraded",)})
        assert changed == ["A"], "值与标记同时变化时 changed 必须去重"


class TestSourceLocks:
    def test_sync_defined_once_with_no_destroy_rebuild(self) -> None:
        # 结构锁（行为锁的兜底）：sync 的实现里不得出现「全部删除再重建」的形态——
        # 行为锁锁调用面，这把锁防止未来重构把「delete(*children) + 全量 insert」带回来
        import src.ui_kit as uk

        src = Path(uk.__file__).read_text(encoding="utf-8")
        fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "sync")
        seg = ast.get_source_segment(src, fn)
        assert seg, "sync 源码段提取失败"
        assert "delete(*" not in seg, "sync 不得整表删除重建"
        assert seg.count("tree.insert") == 1 and seg.count("tree.item(") >= 1


class TestRealWindowWidgets:
    # 真窗用例（无显示环境 skip，与本文件唯一 skip 面）：浮层编辑器与派生样式依赖真实
    # Tcl 事件循环，无头环境无法等价驱动；tk_root fixture 形态取
    # tests/test_ui_theme.py::TestApplyTtk.tk_root。
    # [历史注 2026-10-18] 此前「无显示即 skip」是空头承诺：三条用例裸 tk.Tk()，
    # 无显示器时抛 TclError 以 ERROR 形态进门禁、把「没显示设备」伪装成「代码回归」，故补 fixture。
    # 与 AGENTS「平台专属分支的测试不得靠 skipif 让 CI 跳过」不冲突：那条禁的是按
    # sys.platform 跳过**代码分支**（Windows/POSIX 两侧逻辑都得在 CI 真跑），本处缺的是
    # **显示设备**本身；CI 侧仍由 xvfb-run 提供虚拟显示让这些用例常态执行（见 ci.yml 的
    # 「Install ffmpeg + xvfb + Qt runtime libs (apt)」与「pytest 全程跑在 xvfb 下」两步，
    # 其注释已把 test_ui_kit 的真窗用例列为常态执行面），skip 只兜无 xvfb 的裸环境。
    # 与范本的唯一差异：**不 withdraw**——bbox 取单元格几何、event_generate 打真实事件，
    # 都要求窗体真正映射过；隐藏根窗后 winfo 宽度退化为 1，用例会以「目标单元格不可见」误红。
    @pytest.fixture()
    def tk_root(self) -> Generator[tk.Tk, None, None]:
        try:
            root = tk.Tk()
        except tk.TclError as e:
            pytest.skip(f"无显示环境，跳过 Tk 真窗用例: {e}")
        yield root
        root.destroy()

    _COLUMNS_GUI = [
        ("name", "主播名称", 3, "w"),
        ("set_quality", "设置画质", 1, "w"),
        ("switch", "切换画质", 2, "w"),
    ]

    def _build(self, root: object) -> tuple[DataTable, list[tuple[str, str]]]:
        from src.ui_kit import font_style  # 真窗分支内导入（无显示环境 skip 前不触碰 Tk）

        table = DataTable(root, self._COLUMNS_GUI)  # type: ignore[arg-type]
        table.tree.pack()
        commits: list[tuple[str, str]] = []
        table.bind_cell_editor(
            "switch",
            # 值/初值/提交全部以行 key 为实参——与 gui._quality_row_setq 的缓存口径一致
            values_for=lambda key: ["默认画质", "高清", "原画"],
            initial_for=lambda key: "高清",
            on_commit=lambda key, value: commits.append((key, value)),
        )
        root.update()  # type: ignore[attr-defined]
        return table, commits

    def test_cell_editor_opens_and_commits(self, tk_root: tk.Tk) -> None:
        # 点击「切换画质」列 → 单元格 bbox 上浮 readonly 下拉，初值 = 该行当前画质；
        # 选中即按 (行, 选中值) 提交并销毁；这两步合起来锁「点击不落空」的新实现面
        table, commits = self._build(tk_root)
        table.sync(
            ["A", "B"],
            {"A": ("主播A", "高清", ""), "B": ("主播B", "原画", "")},
            {"A": ("normal",), "B": ("normal",)},
        )
        tk_root.update()
        bbox = table.tree.bbox("A", "#3")
        assert bbox, "目标单元格不可见，无法驱动浮层编辑器"
        x, y = bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2
        table.tree.event_generate("<Button-1>", x=x, y=y)
        tk_root.update()
        assert table._editor is not None, "点击「切换画质」列未弹出浮层编辑器"
        assert table._editor.get() == "高清", "浮层编辑器初值应为该行当前画质"
        # 选中即提交并销毁（模拟用户在下拉里选「原画」）
        table._editor.set("原画")
        table._editor.event_generate("<<ComboboxSelected>>")
        tk_root.update()
        assert commits == [("A", "原画")], f"提交回调未按 (行, 选中值) 触发: {commits}"
        assert table._editor is None, "选中后浮层编辑器应销毁"

    def test_font_style_derives_and_caches(self, tk_root: tk.Tk) -> None:
        from tkinter import ttk

        import src.ui_kit as uk

        style = ttk.Style(tk_root)
        style.configure("Prov.TButton", background="#123456")
        style.map("Prov.TButton", background=[("active", "#234567")])
        name1 = uk.font_style("Prov.TButton", ("Arial", 20), tk_root)
        name2 = uk.font_style("Prov.TButton", ("Arial", 20), tk_root)
        assert name1 == name2, "同 (变体, 字体) 必须复用同一派生样式"
        assert name1.endswith(".Prov.TButton")
        derived_cfg = style.configure(name1)
        assert derived_cfg is not None and "font" in derived_cfg, "派生样式必须注入字体"
        assert derived_cfg.get("background") == "#123456", "派生样式必须继承基础变体静态配置"
        derived_map = style.map(name1)
        assert derived_map.get("background") == [("active", "#234567")], "派生样式必须继承基础变体状态映射"
        # 与基础变体不同字体的另一枚派生样式
        name3 = uk.font_style("Prov.TButton", ("Arial", 12), tk_root)
        assert name3 != name1

    def test_translatable_text_registers_and_retranslates(
        self, tk_root: tk.Tk, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # T()（ui_i18n.Translatable）经工厂「建时查表 + 登记重译」：语言切换后
        # retranslate_all 回填当前语言值。删掉工厂里的 register 调用本用例必须转红（变异验证）。
        import i18n
        import src.ui_kit as uk
        from src import ui_i18n

        label = uk.Label(tk_root, text=ui_i18n.T("待 机"))
        button = uk.Button(tk_root, text=ui_i18n.T("开始录制"))
        assert label.cget("text") == "待 机"
        assert button.cget("text") == "开始录制"
        # 非恒等翻译：证明重译走 tr 查表（每次渲染取当前目录），而不是建时定格
        monkeypatch.setattr(i18n, "_tr", lambda text: f"<<{text}>>")
        applied = ui_i18n.retranslate_all()
        assert applied >= 2, "两个控件都必须登记在册"
        assert label.cget("text") == "<<待 机>>"
        assert button.cget("text") == "<<开始录制>>"
        # 普通 str 文本不登记：切语言不得被改写
        plain = uk.Label(tk_root, text="DouyinLiveRecorder")
        assert ui_i18n.retranslate_all() >= 2
        assert plain.cget("text") == "DouyinLiveRecorder"


# ─── 纯几何 / 动画辅助（无 Tk 依赖的部分） ──────────────────────────────────
#
# 本组用例刻意不建任何 Tk 对象：_capture_geometry / _restore_geometry / slide_in /
# scale_in_window 只把 widget 当作「几何管理器协议 + place/geometry 调用面」使用，
# 最小替身即可无头驱动。真窗用例（TestRealWindowWidgets）仍保留给浮层编辑器这类
# 必须依赖 Tcl 事件循环的路径——两者的边界是「是否真的需要 Tcl」，不是「难不难写」。
#
# 覆盖面动机：ui_kit.py 原缺口恰好集中在这批从未被任何用例触及的纯函数上（GLOBAL_FLOOR
# 提到 60% 后 57% 会立刻判红）。补测优先于往 COVERAGE_DEBT 里塞一条「UI 模块可测性差」
# 的债——后者正是白名单退化成记账本的形态。


class _FakeFont:
    # _font_key 的非元组分支：真实 tk.font.Font 只在有 Tk 解释器时存在，替身只复刻
    # actual() 这一条读取面；boom=True 复刻「字体已随解释器销毁」的取值失败。
    def __init__(self, *, family: str = "Arial", size: int = 12, weight: str = "normal", boom: bool = False) -> None:
        self._values: dict[str, object] = {"family": family, "size": size, "weight": weight}
        self._boom = boom

    def actual(self, key: str) -> object:
        if self._boom:
            raise ValueError("字体已失效")
        return self._values[key]


class _FakeGeometryWidget:
    # 只复刻几何管理器协议切片；errors 里点名的方法一律抛 tk.TclError，
    # 用于驱动 _capture_geometry / _restore_geometry / slide_in 的降级分支。
    def __init__(
        self,
        *,
        grid_info: dict[str, object] | None = None,
        pack_info: dict[str, object] | None = None,
        errors: frozenset[str] = frozenset(),
    ) -> None:
        self._grid_info = grid_info or {}
        self._pack_info = pack_info or {}
        self._errors = errors
        self.place_calls: list[dict[str, object]] = []
        self.place_forget_calls = 0
        self.grid_configure_calls: list[dict[str, object]] = []
        self.pack_configure_calls: list[dict[str, object]] = []

    def grid_info(self) -> dict[str, object]:
        if "grid_info" in self._errors:
            raise tk.TclError("grid_info 不可读")
        return dict(self._grid_info)

    def pack_info(self) -> dict[str, object]:
        if "pack_info" in self._errors:
            raise tk.TclError("pack_info 不可读")
        return dict(self._pack_info)

    def place(self, **kwargs: object) -> None:
        if "place" in self._errors:
            raise tk.TclError("控件已销毁")
        self.place_calls.append(kwargs)

    def place_forget(self) -> None:
        self.place_forget_calls += 1

    def grid_configure(self, **kwargs: object) -> None:
        if "restore" in self._errors:
            raise tk.TclError("控件已销毁")
        self.grid_configure_calls.append(kwargs)

    def pack_configure(self, **kwargs: object) -> None:
        if "restore" in self._errors:
            raise tk.TclError("控件已销毁")
        self.pack_configure_calls.append(kwargs)


class _FakeMotion:
    # 复刻 MotionController.run_frames 的调用面：按 0.0 / 1.0 采两帧后落终态。
    # 不排 after、不读 Tk——动效的**几何算术**本来就与帧调度无关，这正是本组用例
    # 能无头断言「起点偏移 / 终点精确归位」的原因。
    def __init__(self) -> None:
        self.jobs: list[tuple[str, int, int]] = []

    def run_frames(
        self,
        _widget: object,
        job_key: str,
        on_frame: Callable[[float], None],
        *,
        duration_ms: int,
        frames: int,
        on_done: Callable[[], None] | None = None,
    ) -> None:
        self.jobs.append((job_key, duration_ms, frames))
        on_frame(0.0)
        on_frame(1.0)
        if on_done is not None:
            on_done()


class _FakeWindow:
    # 复刻 scale_in_window 用到的 Toplevel 协议切片：尺寸读数 + geometry 写入。
    def __init__(self, *, width: int = 320, height: int = 240, errors: frozenset[str] = frozenset()) -> None:
        self._width = width
        self._height = height
        self._errors = errors
        self.geometry_calls: list[str] = []

    def update_idletasks(self) -> None:
        if "update" in self._errors:
            raise tk.TclError("窗口已销毁")

    def winfo_width(self) -> int:
        return self._width

    def winfo_height(self) -> int:
        return self._height

    def winfo_rootx(self) -> int:
        return 10

    def winfo_rooty(self) -> int:
        return 20

    def geometry(self, spec: str) -> None:
        if "geometry" in self._errors:
            raise tk.TclError("窗口已销毁")
        self.geometry_calls.append(spec)


class TestFontKeyAndScaleRegistration:
    def test_font_key_prefers_actual_triple_for_font_objects(self) -> None:
        # 非元组分支：tk.font.Font 的缓存键必须取 actual() 三元组，而不是 str(font)
        # （后者带对象地址，同一字体每次建新键 = 派生样式缓存永不命中）。
        import src.ui_kit as uk

        assert uk._font_key(_FakeFont(family="Arial", size=20, weight="bold")) == "Arial|20|bold"

    def test_font_key_falls_back_to_str_when_actual_fails(self) -> None:
        # 字体随解释器销毁后 actual() 会抛异常：此时回退 str(font)，而不是把异常抛给
        # 调用方——font_style 位于控件构建路径，抛出去等于整个页面建不出来。
        import src.ui_kit as uk

        font = _FakeFont(boom=True)
        assert uk._font_key(font) == str(font)

    def test_set_scale_percent_registers_and_clears_cache(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 换档必须同时清空派生样式缓存：否则新档位会命中按旧 padding 派生的样式名，
        # 表现为「字号变大了、按钮内边距还是老样子」。
        import src.ui_kit as uk

        monkeypatch.setattr(uk, "_SCALE_PERCENT", 100)
        monkeypatch.setattr(uk, "_FONT_STYLE_CACHE", {("Prov.TButton", "Arial|20", 100): "DLRF0.Prov.TButton"})
        uk.set_scale_percent(125)
        assert uk.current_scale_percent() == 125
        assert uk._FONT_STYLE_CACHE == {}, "换档后派生样式缓存必须清空"

    def test_clear_font_style_cache_empties_registry(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.ui_kit as uk

        monkeypatch.setattr(uk, "_FONT_STYLE_CACHE", {("x", "y", 100): "DLRF0.x"})
        uk.clear_font_style_cache()
        assert uk._FONT_STYLE_CACHE == {}


class TestGeometryManagerCapture:
    # _capture_geometry / _restore_geometry 是滑入动效「终帧精确归位」的地基：
    # 抓错管理器（把 grid 页面当 place 处理）会让页面在过渡后被 place 永久接管，
    # 原本 grid 的布局直接失效——本组逐分支锁死。

    def test_grid_managed_widget_is_captured_as_grid(self) -> None:
        import src.ui_kit as uk

        widget = _FakeGeometryWidget(grid_info={"column": 1})
        assert uk._capture_geometry(cast("Any", widget)) == ("grid", {"column": 1})

    def test_pack_managed_widget_is_captured_as_pack(self) -> None:
        import src.ui_kit as uk

        widget = _FakeGeometryWidget(pack_info={"side": "top"})
        assert uk._capture_geometry(cast("Any", widget)) == ("pack", {"side": "top"})

    def test_unmanaged_widget_reports_none(self) -> None:
        import src.ui_kit as uk

        assert uk._capture_geometry(cast("Any", _FakeGeometryWidget())) == ("none", {})

    def test_tclerror_falls_through_to_none(self) -> None:
        # 控件已销毁时 grid_info/pack_info 双抛 TclError：必须收敛成 ("none", {})，
        # 而不是把异常冒给动效回调（回调在 after 队列里，抛出去整条链就断了）。
        import src.ui_kit as uk

        widget = _FakeGeometryWidget(errors=frozenset({"grid_info", "pack_info"}))
        assert uk._capture_geometry(cast("Any", widget)) == ("none", {})

    def test_restore_skips_unmanaged_widget(self) -> None:
        import src.ui_kit as uk

        widget = _FakeGeometryWidget()
        uk._restore_geometry(cast("Any", widget), ("none", {}))
        assert widget.place_forget_calls == 0

    def test_restore_grid_manager_rewrites_grid_info(self) -> None:
        # 顺序判据：必须「先 place_forget 再 grid_configure」——反过来的话 place 会
        # 压住 grid，页面永久停在过渡期的偏移位置。
        import src.ui_kit as uk

        widget = _FakeGeometryWidget()
        uk._restore_geometry(cast("Any", widget), ("grid", {"column": 2}))
        assert widget.place_forget_calls == 1
        assert widget.grid_configure_calls == [{"column": 2}]

    def test_restore_pack_manager_rewrites_pack_info(self) -> None:
        import src.ui_kit as uk

        widget = _FakeGeometryWidget()
        uk._restore_geometry(cast("Any", widget), ("pack", {"side": "left"}))
        assert widget.pack_configure_calls == [{"side": "left"}]

    def test_restore_swallows_tclerror_after_widget_destroyed(self) -> None:
        # 窗口关闭后迟到的 after 回调：还原失败只能吞掉，不得回头炸整条事件链。
        import src.ui_kit as uk

        widget = _FakeGeometryWidget(errors=frozenset({"restore"}))
        uk._restore_geometry(cast("Any", widget), ("grid", {"column": 1}))
        assert widget.place_forget_calls == 1
        assert widget.grid_configure_calls == []


class TestSlideInGeometry:
    # 页面滑入的几何算术：起点偏移 = distance、终帧归位到原布局器。
    # 真窗用例只能证明「能跑」，这里锁的是「偏移量与归位动作」本身。

    def test_slide_in_offsets_then_restores_grid_manager(self) -> None:
        import src.ui_kit as uk

        widget = _FakeGeometryWidget(grid_info={"column": 0})
        motion = _FakeMotion()
        uk.slide_in(cast("Any", widget), motion, distance=120, duration_ms=180, job_key="page")
        # 帧序列：progress=0 → x=120，progress=1 → x=0
        assert [call["x"] for call in widget.place_calls] == [120, 0]
        assert widget.place_calls[0]["relx"] == 0.0 and widget.place_calls[0]["relwidth"] == 1.0
        # 终帧必须把原 grid 配置写回（否则页面被 place 永久接管）
        assert widget.place_forget_calls == 1
        assert widget.grid_configure_calls == [{"column": 0}]
        assert motion.jobs == [("page", 180, 10)]

    def test_slide_in_survives_destroyed_widget_during_frames(self) -> None:
        # 过渡途中控件被销毁：每帧 place 都会抛 TclError，必须逐帧吞掉并走完终态，
        # 不得让异常从 after 回调里逃出去。
        import src.ui_kit as uk

        widget = _FakeGeometryWidget(errors=frozenset({"place"}))
        motion = _FakeMotion()
        uk.slide_in(cast("Any", widget), motion, distance=10, duration_ms=100, job_key="k")
        assert motion.jobs and widget.place_calls == []


class TestScaleInWindow:
    def test_scales_from_start_ratio_and_settles_to_base_size(self) -> None:
        import src.ui_kit as uk

        window = _FakeWindow(width=320, height=240)
        motion = _FakeMotion()
        uk.scale_in_window(cast("Any", window), motion, start_scale=0.8, duration_ms=150, job_key="dlg")
        # progress=0 → 0.8 倍（256x192），progress=1 → 1.0 倍（320x240）；两帧都带居中偏移
        assert window.geometry_calls[0] == "256x192-10-20"
        assert window.geometry_calls[1] == "320x240-10-20"
        # 终帧无条件回到基尺寸（不带偏移），避免残留缩放
        assert window.geometry_calls[2] == "320x240"
        assert motion.jobs == [("dlg", 150, 8)]

    def test_bails_out_when_window_geometry_is_not_realised(self) -> None:
        # 窗口刚建时 winfo_width 还是 1：拿它当基准会把弹窗缩成一条线，
        # 故 <=1 一律直接返回、不动效。
        import src.ui_kit as uk

        window = _FakeWindow(width=1, height=240)
        motion = _FakeMotion()
        uk.scale_in_window(cast("Any", window), motion, start_scale=0.5, duration_ms=100, job_key="k")
        assert window.geometry_calls == [] and motion.jobs == []

    def test_bails_out_when_toplevel_already_destroyed(self) -> None:
        import src.ui_kit as uk

        window = _FakeWindow(errors=frozenset({"update"}))
        motion = _FakeMotion()
        uk.scale_in_window(cast("Any", window), motion, start_scale=0.5, duration_ms=100, job_key="k")
        assert motion.jobs == []

    def test_swallows_geometry_errors_during_frames_and_settle(self) -> None:
        import src.ui_kit as uk

        window = _FakeWindow(errors=frozenset({"geometry"}))
        motion = _FakeMotion()
        uk.scale_in_window(cast("Any", window), motion, start_scale=0.5, duration_ms=100, job_key="k")
        assert window.geometry_calls == []
