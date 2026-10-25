---
name: runtime-pin-verification
description: >
  DouyinLiveRecorder 项目中运行时二进制（ffmpeg/node）钉定与完整性验证的硬约束。
  当修改 build_exe.py 的钉定哈希、新增/删除下载源、修改 check_runtime_pins.py、
  或涉及发布链运行时二进制获取时使用此 Skill。
trigger:
  - _PINNED_RUNTIME_SHA256
  - --require-pinned
  - check_runtime_pins
  - ffmpeg 下载
  - node 下载
  - TOFU
  - GPG 验签
  - _is_pinned
  - _slot_is_gated
  - DLR_RUNTIME_SHA256
  - releases/tags
---

# 运行时钉定验证

> **约束事实源**: dlr-dev-playbook `references/known-pitfalls.md`「构建产物、依赖与运行时基线」下的
> 「发布链运行时二进制必须 fail-closed 钉定」及「三类钉定/校验互不覆盖」。
> 本 Skill 提取高频复用内容供按需加载；约束变更以 AGENTS.md 为准。
>
> **详细内容已拆分至 `references/` 子目录**，主文件仅保留路由表与核心约束。

## 何时加载

- 修改 `build_exe.py` 的 `_PINNED_RUNTIME_SHA256` / `_FFMPEG_DOWNLOAD_URLS` /
  `_is_pinned()` / `_slot_is_gated()` / `--require-pinned`。
- 修改 `scripts/check_runtime_pins.py`。
- 新增/删除/替换 ffmpeg 或 node 的下载源。
- 修改 `src/ffmpeg_install.py` / `src/node_install.py` 的 TOFU 逻辑。
- 涉及发布链中运行时二进制的获取、校验、分发。

## 核心约束：三层防线（发布期运行时二进制，SEV-10）

### 第一层：钉定哈希

- `build_exe.py` 的 `_PINNED_RUNTIME_SHA256`（按 `<os>-<arch>` 分列，槽位 ffmpeg/node）。
- 「已钉定」唯一判据是 `_is_pinned()` 形状：**64 位小写十六进制**。
- 占位/空串/截断一律未钉定。
- **不得为让 CI 绿回填本地自算哈希**（那是固化「构建机已中毒」）。

### 第二层：强制校验门

- `--require-pinned`（CI 因 `GITHUB_ACTIONS=true` 自动开）。
- 缺钉定即在下载前 `SystemExit`（继承 `BaseException` 吞不掉）。
- `slot` 是必填关键字参数（漏传会静默降级为无校验下载）。

### 第三层：静态校验脚本

- `scripts/check_runtime_pins.py`（`--strict` 由 build-release.yml prepare job 执行）。
- 表为空/缺平台/缺槽位一律 rc=2。
- 「算满足」两档的唯一口径是 `build_exe._slot_is_gated()`：
  - 64 位十六进制官方哈希；或
  - **官方签名档**（取值 = `OFFICIAL_SIGNATURE_PIN`，且该槽在 `_RUNTIME_GPG_SIGNATURES` 确有登记、指纹为 40 位十六进制）。
  - **标记本身绝不构成放行**。

## 路由表

| 子主题 | 文件 | 触发场景 |
| --- | --- | --- |
| 官方签名档 | [`references/official-signatures.md`](references/official-signatures.md) | 修改签名验证逻辑、GPG 验签流程 |
| macOS 取数端点约束 | [`references/macos-endpoints.md`](references/macos-endpoints.md) | 修改 macOS ffmpeg 下载源、evermeet 端点 |
| Linux 取数端点约束 | [`references/linux-endpoints.md`](references/linux-endpoints.md) | 修改 Linux ffmpeg 下载源、月末标签 |
| 三类钉定边界与来源增删 | [`references/pin-categories.md`](references/pin-categories.md) | 新增/删除下载源、TOFU 基线、钉定分类 |

## 验证

### 最小验证步骤

1. **项目级门禁（由 `python scripts/run_gates.py` 统一兖底，Skill 不重复）**：
   ```bash
   python scripts/run_gates.py
   ```
   预期：退出码 0。

2. **本领域专项检查**：
   ```bash
   # 1. 运行时钉定检查（严格模式）
   python scripts/check_runtime_pins.py --strict
   # 预期：退出码 0

   # 2. 构建脚本测试
   pytest tests/test_build_exe.py -v
   # 预期：全绿（钉定/签名/主机白名单/不可变标签）

   # 3. ffmpeg 安装测试
   pytest tests/test_ffmpeg_install.py -v
   # 预期：全绿（TOFU/下载源白名单）
   ```

3. **配置检查**（跨平台 Python 命令）：
   ```bash
   # 确认退役主机已移出白名单
   python -c "import sys; c=open('tests/test_build_exe.py',encoding='utf-8').read(); m=[l for l in c.split('\n') if '_ALLOWED_HOSTS' in l]; print('OK: 检查 _ALLOWED_HOSTS 定义' if m else 'FAIL'); sys.exit(0 if m else 1)"

   # 确认无 /releases/download/latest/ 路径
   python -c "import sys; c=open('tests/test_build_exe.py',encoding='utf-8').read(); m=[l for l in c.split('\n') if 'releases/latest' in l]; print('OK: 无 latest 路径' if not m else 'FAIL'); sys.exit(0 if not m else 1)"
   ```
   预期：两行均输出 `OK`，退出码 0。

### 项目级门禁（由 `python scripts/run_gates.py` 统一兖底，Skill 不重复）

- `python scripts/check_runtime_pins.py`（已在门禁清单内）

### 本领域专项检查

1. `python scripts/check_runtime_pins.py --strict` — rc=0
2. `pytest tests/test_build_exe.py` — 全绿（钉定/签名/主机白名单/不可变标签）
3. `pytest tests/test_ffmpeg_install.py` — 全绿（TOFU/下载源白名单）
4. 配置检查：用上方跨平台 Python 命令确认退役主机已移出白名单、无 `/releases/download/latest/` 路径
