#!/usr/bin/env python3
# 版本号同步脚本 — 以 pyproject.toml 的 version 为准，把仍写死版本的文件改齐。
#
# 用法:
# python scripts/sync_version.py              # 使用 pyproject.toml 中的版本号
# python scripts/sync_version.py 4.0.9.0      # 指定新版本号
# python scripts/sync_version.py --check      # 仅检查是否一致，不修改文件
# python scripts/sync_version.py --dry-run    # 显示将要做的变更但不实际写入
#
# 现状（2026-09-23）：版本号已全部动态化，**没有待同步目标**（SYNC_TARGETS 为空）——
#   - main.py / src/web_api.py  运行时从 pyproject.toml（importlib.metadata）动态读取
#   - Dockerfile                经 APP_VERSION 构建参数从 pyproject.toml 注入
#   - i18n/zh_CN.po             不再携带版本号
#   - README.md / CODE_WIKI.md  为文档，版本由人工维护，不在本脚本范围
# 所以「版本一致性」的门禁不是本脚本，而是 scripts/check_version.py（校验动态化有没有被改回
# 写死，且它在 AGENTS.md 的门禁命令块里）。本脚本结构保留，供将来真出现写死版本时复用。
#

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 项目根目录（脚本在 scripts/ 下，上一级即为根目录）
ROOT_DIR = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"

# ── 需要同步的目标文件及其替换规则 ─────────────────────────────────────
# 每条规则: (相对路径, [(正则模式, 替换模板), ...])
#   替换模板中可用 \1 捕获组 + {version} 占位符
# 版本号已全部动态化（形态见文件头），故清单为空——本脚本当下是**空转**的：--check 会打印
# 「所有文件版本号一致」，那只是「零目标全部通过」，不自证任何事。要核版本一致性请跑
# scripts/check_version.py（它在门禁命令块里，查的是「动态化有没有被改回写死」）。
# 未来确实新增写死版本的文件时，在此追加规则；check_all() 的「先判命中再判等」会立刻暴露
# 正则失配的锚点，别把它改回「sub 结果与原文相同 = 已一致」。
SYNC_TARGETS: list[tuple[str, list[tuple[str, str]]]] = []


def read_version_from_pyproject() -> str:
    # 从 pyproject.toml 读取 version 字段。
    text = PYPROJECT_PATH.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*["\'](.+?)["\']', text, re.MULTILINE)
    if not m:
        print("ERROR: 无法从 pyproject.toml 读取 version 字段", file=sys.stderr)
        sys.exit(1)
    return m.group(1)


def sync_file(rel_path: str, patterns: list[tuple[str, str]], version: str, dry_run: bool) -> bool:
    # 对单个文件按顺序套用全部替换规则，返回是否产生了变更。
    # 文件不存在时这里只 SKIP（写型操作不该凭缺失造出失败），而同样的缺失在 check_all 里判
    # 不一致——两条路径的口径本就不同：检查要比对，同步无从可改。
    # 每条规则只替换首个匹配（count=1）：锚点若在一文件里命中多处，全量替换会误伤正文中
    # 同形态的文本。
    file_path = ROOT_DIR / rel_path
    if not file_path.exists():
        print(f"  SKIP  {rel_path} (文件不存在)")
        return False

    original = file_path.read_text(encoding="utf-8")
    content = original

    for pattern, replacement in patterns:
        fmt_replacement = replacement.format(version=version)
        content = re.sub(pattern, fmt_replacement, content, count=1)

    changed = content != original
    if changed:
        prefix = "WOULD UPDATE" if dry_run else "UPDATED"
        print(f"  {prefix}  {rel_path}")
        if not dry_run:
            file_path.write_text(content, encoding="utf-8")
    else:
        print(f"  OK    {rel_path}")
    return changed


def check_all(version: str) -> bool:
    # 检查所有文件版本号是否已一致。返回 True 表示全部一致。
    # 注意：SYNC_TARGETS 为空时这里 vacuous True（见该常量处的说明），不得拿它当版本门禁——
    # 动态化有没有被改回写死，由 scripts/check_version.py 判。
    all_ok = True
    for rel_path, patterns in SYNC_TARGETS:
        file_path = ROOT_DIR / rel_path
        if not file_path.exists():
            print(f"  MISSING  {rel_path}")
            all_ok = False
            continue
        content = file_path.read_text(encoding="utf-8")
        # 对每个 pattern，检查替换后内容是否不变（即已是目标版本）
        file_ok = True
        for pattern, replacement in patterns:
            fmt_replacement = replacement.format(version=version)
            # 2026-09-12 审查 6.7：先判命中再判等。原实现只看 `re.sub 结果 != 原文`
            # ——正则一旦失配（文件改版导致锚点文本变化），re.sub 返回原文本，
            # 判定分支走进"已一致"，门禁静默变绿：版本号明明没同步却报 OK，
            # 恰在需要报警的时刻失效。
            if re.search(pattern, content) is None:
                print(f"    pattern 未命中（正则已失配，请更新 SYNC_TARGETS）: {pattern}")
                file_ok = False
                break
            new_content = re.sub(pattern, fmt_replacement, content, count=1)
            if new_content != content:
                file_ok = False
                break
            content = new_content
        if file_ok:
            print(f"  OK    {rel_path}")
        else:
            print(f"  MISMATCH  {rel_path}")
            all_ok = False
    return all_ok


def main() -> None:
    # 退出码只在 --check 分支产生（0 一致 / 1 不一致）；同步与 --dry-run 分支一律正常退出，
    # 它是「执行工具」，成功与否由调用方看输出——不要把它接成门禁命令（版本门禁见 check_version.py）。
    parser = argparse.ArgumentParser(description="同步 pyproject.toml 版本号到所有相关文件")
    parser.add_argument("version", nargs="?", default=None, help="指定新版本号（默认从 pyproject.toml 读取）")
    parser.add_argument("--check", action="store_true", help="仅检查一致性，不修改文件")
    parser.add_argument("--dry-run", action="store_true", help="显示将要做的变更但不实际写入")
    args = parser.parse_args()

    if args.version:
        version = args.version
        print(f"使用指定版本号: {version}")
    else:
        version = read_version_from_pyproject()
        print(f"从 pyproject.toml 读取版本号: {version}")

    print()

    if args.check:
        all_ok = check_all(version)
        print()
        if all_ok:
            print("[OK] 所有文件版本号一致")
            sys.exit(0)
        else:
            print("[FAIL] 部分文件版本号不一致，运行 `python scripts/sync_version.py` 进行同步")
            sys.exit(1)

    changed_count = 0
    for rel_path, patterns in SYNC_TARGETS:
        if sync_file(rel_path, patterns, version, args.dry_run):
            changed_count += 1

    print()
    if changed_count:
        action = "would be updated" if args.dry_run else "updated"
        print(f"完成: {changed_count} 个文件{action}到版本 {version}")
    else:
        print(f"所有文件已是最新版本 {version}")


if __name__ == "__main__":
    main()
