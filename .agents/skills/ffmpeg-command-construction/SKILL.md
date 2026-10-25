---
name: ffmpeg-command-construction
description: >
  DouyinLiveRecorder 项目中 ffmpeg 命令构造与容器格式的硬约束。
  当修改或新增 ffmpeg 录制命令、保存类型分支、输入/输出参数构造、
  分段格式映射时使用此 Skill。
trigger:
  - ffmpeg
  - -reconnect
  - -segment_format
  - _build_ffmpeg_output_args
  - _build_ffmpeg_input_args
  - _run_ffmpeg_record
  - record_save_type
  - 容器格式
  - FLV
  - TS
  - MP4
  - M4A
  - MKV
---

# ffmpeg 命令构造与容器格式

> **约束事实源**: dlr-dev-playbook `references/known-pitfalls.md`「ffmpeg 命令构造与容器格式」章节。
> 本 Skill 提取高频复用内容供按需加载；约束变更以 AGENTS.md 为准。
>
> **详细内容已拆分至 `references/` 子目录**，主文件仅保留路由表与核心约束。

## 何时加载

- 修改 `main.py::start_record` / `_build_ffmpeg_input_args` /
  `_build_ffmpeg_output_args` / `_build_record_output_path` /
  `_run_ffmpeg_record` / `_convert_after_record` 中的任何一个。
- 新增保存类型分支或输出格式。
- 涉及 `-reconnect*`、`-thread_queue_size`、`-segment_format`、`-headers`、
  `-tls_verify`、`-http_proxy` 等 ffmpeg 选项。
- 调试 ffmpeg 退出码异常、静默损坏、重连失效。

## 核心约束：四个单一定义点（F-01 收官）

禁止回退成内联复制粘贴。所有平台分支必须经过以下函数：

1. **输入侧**: `_build_ffmpeg_input_args(real_url, user_agent, tuning, headers, tls_verify, proxy_address)`
   - 所有选项按 `-i` 锚点定位或插列表头，**禁裸数字下标**。
2. **输出路径**: `_build_record_output_path(...)`
   - 扩展名 / 分段时间戳格式 / `_%03d` / `_%02d` 全查表。
3. **执行骨架**: `_run_ffmpeg_record(...)` + 录后转码 `_convert_after_record(...)`
   - 五条保存类型分支只调这三个函数，禁各自写 try/except + check_subprocess。
4. **平台分发**: `_PLATFORM_RESOLVERS`（`(匹配器, 处理函数)` 表）+ `_PlatformResolveContext`
   - 表项顺序即优先级，**禁插 elif**。

回归锁：`tests/test_platform_dispatch.py` + `tests/test_start_record_command_golden.py`。

## 路由表

| 子主题 | 文件 | 触发场景 |
| --- | --- | --- |
| `-reconnect*` 与 `-thread_queue_size` 位置约束 | [`references/reconnect-constraints.md`](references/reconnect-constraints.md) | 修改重连参数、thread_queue_size 位置、HLS 输入处理 |
| `-segment_format` 查表与容器格式 | [`references/segment-format-lookup.md`](references/segment-format-lookup.md) | 修改分段格式映射、容器格式、扩展名查表 |
| 录制结果反馈 | [`references/recording-feedback.md`](references/recording-feedback.md) | 修改录制成功/失败上报、探针退避交互 |
| 黄金命令比对 | [`references/golden-command-comparison.md`](references/golden-command-comparison.md) | 修改 ffmpeg 命令构造逻辑、更新黄金基准 |

## 验证

### 最小验证步骤

1. **项目级门禁（由 `python scripts/run_gates.py` 统一兖底，Skill 不重复）**：
   ```bash
   python scripts/run_gates.py
   ```
   预期：退出码 0。

2. **本领域专项检查**：
   ```bash
   # 1. ffmpeg 重连参数检查
   pytest tests/test_ffmpeg_reconnect_args.py -v
   # 预期：全绿

   # 2. 录制容器格式检查
   pytest tests/test_record_container.py -v
   # 预期：全绿

   # 3. 黄金命令比对检查
   pytest tests/test_start_record_command_golden.py -v
   # 预期：全绿

   # 4. 平台分发检查
   pytest tests/test_platform_dispatch.py -v
   # 预期：全绿

   # 5. 录制失败反馈检查
   pytest tests/test_record_failure_feedback.py -v
   # 预期：全绿
   ```

3. **AST 检查**（跨平台 Python 命令）：
   ```bash
   # 检查无 `-reconnect*` 出现在 `-i` 之后
   python -c "import sys,re; c=open('main.py',encoding='utf-8').read(); m=re.search(r'-i.*-reconnect',c,re.DOTALL); print('FAIL' if m else 'OK'); sys.exit(1 if m else 0)"

   # 检查无 `-segment_format` 裸字面量
   python -c "import sys,re; c=open('main.py',encoding='utf-8').read(); m=re.findall(r'-segment_format\s+\w+',c); print('FAIL' if m else 'OK'); sys.exit(1 if m else 0)"
   ```
   预期：两行均输出 `OK`，退出码 0。

### 项目级门禁（由 `python scripts/run_gates.py` 统一兖底，Skill 不重复）

- `black --check`、`isort --check-only`、`mypy`（含 `--platform linux` / `--platform win32`）、`check_annotations.py`

### 本领域专项检查

1. `pytest tests/test_ffmpeg_reconnect_args.py` — 全绿
2. `pytest tests/test_record_container.py` — 全绿
3. `pytest tests/test_start_record_command_golden.py` — 全绿
4. `pytest tests/test_platform_dispatch.py` — 全绿
5. `pytest tests/test_record_failure_feedback.py` — 全绿
6. AST 检查：用上方跨平台 Python 命令确认无 `-reconnect*` 出现在 `-i` 之后、无 `-segment_format` 裸字面量
