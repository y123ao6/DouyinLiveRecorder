# ffmpeg -reconnect* 输入选项「带值 + 位于 -i 之前」回归测试（2026-09-11 事故沉淀）。
#
# 背景：2026-09-10 代码审查修复把 -reconnect_delay_max / -reconnect_streamed /
# -reconnect_at_eof 从 -i 之后整体移到 -i 之前，移动过程中后两个选项的布尔值 "1"
# 丢失。ffmpeg 解析 -reconnect_streamed 时把下一个选项名 -reconnect_at_eof 当作
# 其值 → 「Unable to parse "reconnect_streamed" option value "-reconnect_at_eof"
# as boolean」→ Invalid argument，输入未打开即退出（-22）。该缺陷在 09-10 当晚
# 首次真实录制（抖音 h264 HLS 拉流）即 100% 复现。
#
# 旧写法（-i 之后）ffmpeg 会静默接受、退出码 0、无任何可见症状（2026-09-10 实测），
# 缺值写法则直接打不开输入——两种失效模式都不易从运行日志直觉定位，故在此固化为
# AST 断言，同时锁定两个不变量：
#   1. 每个 -reconnect* 选项后必须紧跟一个非选项名的字面量取值；
#   2. -reconnect* 必须全部位于 -i 之前（input 级选项归属输入侧，2026-09-10 已知坑）。
#
# 本文件与 tests/test_record_container.py 同构：字面量错位能通过格式检查、类型检查
# 与 AST 等价性校验，只有这类语义断言能拦住。
#
# 不变量三（2026-09-11 事故沉淀）：-reconnect_at_eof 对 HLS(m3u8) 输入是致命项——
# hls demuxer 依赖播放列表读到 EOF 才完成解析并开始拉取媒体段，该选项令 http 层在
# 播放列表 EOF 处无限重连（ffmpeg -report 实测：「Will reconnect at <size> in
# N second(s), error=End of file」，1/3/7/15/31/60s 指数退避永不放弃），媒体段一个
# 都拉不到、视频数据零字节产出、进程永不退出（-loglevel error 下零输出零报错）。
# 生产事故形态：斗鱼/抖音房间（HLS 优先选源）仅产出弹幕 SRT、无视频文件；虎牙房间
# （HLS 排除、恒 FLV）不受影响。复现实验：同命令带 -t 10 限时，60 秒仍不退出且
# 零字节产物；仅去掉该选项后 10 秒录制 9MB 正常退出。
# 故 m3u8 输入必须在命令构造处移除该参数对；FLV 输入保留（CDN 掐断长连接时在
# EOF 处重连续写同一文件）。

import ast
from pathlib import Path

_MAIN_PATH = Path(__file__).resolve().parent.parent / "main.py"
# 同类回归的第二处定义点：scripts/douyin_live_recorder_standalone.py 的两处录制命令
# 同样拼接 -reconnect*（与 main.py 保持一字不差是对它的既有要求，一并纳入防线）。
_STANDALONE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "douyin_live_recorder_standalone.py"


# 取「-reconnect* 选项常量在其所属 List 字面量中的位置」清单：
# (list_node, index)。ffmpeg 命令均为函数内的 list 字面量，AST 扫描即可覆盖。
def _reconnect_entries(path: Path) -> list[tuple[ast.List, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    entries: list[tuple[ast.List, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.List):
            continue
        for index, item in enumerate(node.elts):
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                if item.value.startswith("-reconnect"):
                    entries.append((node, index))
    return entries


class TestReconnectOptionsHaveValues:
    # 不变量一：每个 -reconnect* 后必须紧跟字面量取值——缺值时 ffmpeg 会把下一个
    # 选项名当作值，boolean 解析直接失败（2026-09-11 事故的根因）

    def test_scan_finds_all_definition_points(self) -> None:
        # 扫描本身必须命中预期选项条目（每个 -reconnect* 一条：main.py 3 个选项、
        # standalone 2 处命令 × 3 选项），否则下面的断言会退化成空跑的假绿
        assert len(_reconnect_entries(_MAIN_PATH)) == 3, "main.py 的 -reconnect* 选项数量变化"
        assert len(_reconnect_entries(_STANDALONE_PATH)) == 6, "standalone 的 -reconnect* 选项数量变化"

    def test_every_reconnect_option_has_literal_value(self) -> None:
        for path in (_MAIN_PATH, _STANDALONE_PATH):
            for node, index in _reconnect_entries(path):
                label = ast.unparse(node.elts[index])
                if index + 1 >= len(node.elts):
                    raise AssertionError(f"{path.name}: {label} 缺少取值（位于列表末尾）")
                value_node = node.elts[index + 1]
                assert isinstance(
                    value_node, ast.Constant
                ), f"{path.name}: {label} 后必须紧跟字面量取值，发现: {ast.unparse(value_node)}"
                assert isinstance(value_node.value, str) and not value_node.value.startswith(
                    "-"
                ), f"{path.name}: {label} 的取值不能是选项名: {ast.unparse(value_node)}"


class TestReconnectBeforeInputFlag:
    # 不变量二：-reconnect* 属 input 级(HTTP 协议)选项，必须位于 -i 之前。
    # 曾置于 -i 之后：ffmpeg 静默接受、退出码 0，输入侧从未应用，重连完全失效
    # 且无可见症状（2026-09-10 已知坑，当时已计划本断言但未落地，本次一并补齐）。

    def test_reconnect_options_precede_i_flag(self) -> None:
        for path in (_MAIN_PATH, _STANDALONE_PATH):
            for node, index in _reconnect_entries(path):
                i_indices = [
                    i for i, item in enumerate(node.elts) if isinstance(item, ast.Constant) and item.value == "-i"
                ]
                assert i_indices, f"{path.name}: 命令列表缺少 -i: {[ast.unparse(e) for e in node.elts[:5]]}..."
                label = ast.unparse(node.elts[index])
                assert index < min(i_indices), f"{path.name}: {label} 必须位于 -i 之前（input 级选项归属输入侧）"


# 取「'.m3u8' in <url> 判定 + 函数体删除 -reconnect_at_eof 参数对」的守卫清单：
# 事故三的防线。守卫 = If 节点（test 含 .m3u8）且函数体同时含 reconnect_at_eof
# 引用与 del 语句。
def _hls_drop_guards(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    guards: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or ".m3u8" not in ast.unparse(node.test):
            continue
        body_src = "\n".join(ast.unparse(s) for s in node.body)
        if "reconnect_at_eof" in body_src and any(isinstance(s, ast.Delete) for s in node.body):
            guards.append(ast.unparse(node))
    return guards


class TestReconnectAtEofDroppedForHls:
    # 不变量三：m3u8 输入必须移除 -reconnect_at_eof 参数对（守卫必须存在于每个
    # 命令定义点）。main.py 1 处（录制主命令）；standalone 2 处（build_ffmpeg_cmd
    # 与 run_ffmpeg 内联列表须同步，任一缺失即命令不一致）。

    def test_main_py_drops_reconnect_at_eof_for_hls(self) -> None:
        guards = _hls_drop_guards(_MAIN_PATH)
        assert guards, "main.py 缺少「m3u8 输入移除 -reconnect_at_eof」守卫（HLS 录制会无限挂起）"

    def test_standalone_drops_reconnect_at_eof_for_hls_both_sites(self) -> None:
        guards = _hls_drop_guards(_STANDALONE_PATH)
        assert len(guards) == 2, (
            "standalone 的 build_ffmpeg_cmd 与 run_ffmpeg 两处命令必须同步移除"
            f"-reconnect_at_eof（m3u8 输入），实际守卫数: {len(guards)}"
        )
