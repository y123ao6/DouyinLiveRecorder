---
name: platform-source-selection
description: >
  DouyinLiveRecorder 项目中平台流地址选源、探针可达性校验与画质档位映射的硬约束。
  当修改平台解析函数、选源流程、探针逻辑、画质映射或新增平台时使用此 Skill。
  触发词：select_source_url、stream_select、探针、probe、FLV-first、HLS 排除、
  画质映射、QUALITY_MAPPING、_validate_stream_url、_confirm_get_ok、
  _PROBE_BACKOFF_PLATFORMS、_FLV_FIRST_PLATFORMS、trace_error_decorator。
---

# 平台选源流程与画质映射

> **约束事实源**: dlr-dev-playbook `references/known-pitfalls.md` 的「流地址探针与可达性校验」、
> 「平台接口、签名与流地址解析」、「画质档位与选源映射」。
> 本 Skill 提取高频复用内容供按需加载；约束变更以 AGENTS.md 为准。
>
> **详细内容已拆分至 `references/` 子目录**，主文件仅保留路由表与触发条件。

## 何时加载

- 修改 `src/stream_select.py`（选源/探针/可达性校验）。
- 修改 `src/stream.py`（画质映射/平台选档）。
- 修改 `src/spider.py`（平台解析函数）。
- 新增平台接入或修改已有平台的流地址解析。
- 调试流地址不可达、选源回退异常、画质档位错误。

## 路由表

| 子主题 | 文件 | 触发场景 |
| --- | --- | --- |
| 探针可达性校验与节流 | [`references/probe-reachability.md`](references/probe-reachability.md) | 修改探针逻辑、HEAD/GET 探测流程、节流/抖动、UA 一致性、退避撤销 |
| 平台专属选源约束 | [`references/platform-selection.md`](references/platform-selection.md) | 虎牙/斗鱼选源规则、FLV-first 调序、HLS 采集排除 |
| 画质档位映射 | [`references/quality-mapping.md`](references/quality-mapping.md) | 通用画质映射、蓝光子档位、虎牙选档、斗鱼本地重试链 |
| 平台解析函数返回契约 | [`references/parser-contract.md`](references/parser-contract.md) | 装饰器选择、JSON 解析兜底、`_loads_dict` 行为 |

## 验证

### 最小验证步骤

1. **项目级门禁（由 `python scripts/run_gates.py` 统一兖底，Skill 不重复）**：
   ```bash
   python scripts/run_gates.py
   ```
   预期：退出码 0。

2. **本领域专项检查**：
   ```bash
   # 1. 选源流程检查
   pytest tests/test_stream_select.py -v
   # 预期：全绿

   # 2. 画质映射检查
   pytest tests/test_stream.py -v
   # 预期：全绿

   # 3. 平台解析函数检查
   pytest tests/test_spider.py -v
   # 预期：全绿

   # 4. JSON 兖底检查
   pytest tests/test_spider_hardening.py -v
   # 预期：全绿

   # 5. 平台分发检查
   pytest tests/test_platform_dispatch.py -v
   # 预期：全绿
   ```

3. **配置检查**（跨平台 Python 命令）：
   ```bash
   # 确认斗鱼不在 FLV-first 名单中
   python -c "import sys; c=open('src/stream_select.py',encoding='utf-8').read(); m=[l for l in c.split('\n') if '_FLV_FIRST_PLATFORMS' in l and '=' in l]; print('OK: 斗鱼不在名单' if not any('斗鱼' in l for l in m) else 'FAIL'); sys.exit(0 if not any('斗鱼' in l for l in m) else 1)"

   # 确认仅虎牙在探针退避名单中
   python -c "import sys; c=open('src/stream_select.py',encoding='utf-8').read(); m=[l for l in c.split('\n') if '_PROBE_BACKOFF_PLATFORMS' in l and '=' in l]; print('OK: 仅虎牙' if any('虎牙' in l for l in m) and not any('斗鱼' in l for l in m) else 'FAIL'); sys.exit(0 if any('虎牙' in l for l in m) and not any('斗鱼' in l for l in m) else 1)"
   ```
   预期：两行均输出 `OK`，退出码 0。

### 项目级门禁（由 `python scripts/run_gates.py` 统一兖底，Skill 不重复）

- `black --check`、`isort --check-only`、`mypy`（含 `--platform linux` / `--platform win32`）、`check_annotations.py`

### 本领域专项检查

1. `pytest tests/test_stream_select.py` — 全绿
2. `pytest tests/test_stream.py` — 全绿（画质映射）
3. `pytest tests/test_spider.py` — 全绿
4. `pytest tests/test_spider_hardening.py` — 全绿（裸 JSON loads 上限）
5. `pytest tests/test_platform_dispatch.py` — 全绿
6. 配置检查：用上方跨平台 Python 命令确认斗鱼不在 FLV-first 名单、仅虎牙在探针退避名单

### spider.py 变更的强制回归（MUST）

> **约束事实源**: dlr-dev-playbook `references/known-pitfalls.md` 的「流地址探针与可达性校验」、「平台接口、签名与流地址解析」。
>
> **MUST**: 改动 `src/spider.py` 的任一 `get_*_stream_data` / `get_*_stream_url`（含新增平台、调整返回字段、修改签名/重试/回退分支）时，上方「本领域专项检查」的 7 项**全部必须运行**，不得只跑与被改平台同名者。
>
> **Why**: spider.py 的输出结构（`m3u8_url` / `flv_url` / `record_url` / `play_url_list`）直接作为 `stream_select.py` 的候选列表进入选源/探针链路；候选数量、字段可用性、URL host 形态任一变化都会穿过 `_FLV_FIRST_PLATFORMS`、`_PROBE_BACKOFF_PLATFORMS`、`_validate_stream_url`、`_throttle_probe` 与末位放行分支走一遍新路径。故单平台改动仍需覆盖三个横向面：平台分发（`test_platform_dispatch.py`）、探针/选源（`test_stream_select.py` + `test_stream.py`）、JSON 兜底（`test_spider_hardening.py`）。
>
> **执行面**: 本约束**不新增** CI 路径过滤或专属 pre-commit hook——dlr-dev-playbook `references/ci-workflow.md` 与 ci.yml 头注已定「`workflow_dispatch` 场景下 `dorny/paths-filter` 会造假绿、过滤器已整体移除」。CI 侧的真实兖底为 `test` job 的全量 `pytest --cov=src`，配合 `scripts/check_coverage.py` 对 `src/spider.py` 的 50% 阈值与 `test_platform_dispatch.py` 的收集锁；Skill 层的职责是让开发者**显式确认** 7 项都已跑过，不另立第二份门禁。
