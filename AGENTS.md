# AGENTS.md — DouyinLiveRecorder 核心约定

> 本文件是项目长期约定的**唯一事实源**：编码规范、架构决策、并发/线程模型、测试编写规则、构建与格式化流程、以及所有「已知坑」均已在此收敛。新增长期性约定请直接写回本文件对应章节。
>
> **可达性约定**：纯参考性长段（项目结构目录树、一次性实测读数）已外迁到 `docs/agent-reference/` 并由本文件用链接指向；约定、门禁命令、风险控制、「已知坑」的约束句一律留在本文件内，不得出现第二份事实源。判定：「每次会话都必须遵守的约束」留根文件，「在哪找东西的清单 / 佐证读数」可外迁。
>
> **阅读顺序**：先读「风险控制（前置）」→ 需要跑门禁时读「格式化命令」→ 动手前读所在主题的「已知坑」条目。

## 项目概览

- **名称**: DouyinLiveRecorder
- **版本**: 4.3.0（唯一事实源：`pyproject.toml` 的 `version`；`main.py`/`src/web_api.py` 经 `importlib.metadata` 动态读取，`Dockerfile` 经 `APP_VERSION` 构建参数注入，`zh_CN.po` 不再携带版本号；详见「关键约定」第 1 条）
- **描述**: 支持抖音、TikTok、YouTube、快手等 60+ 平台的直播录制工具
- **许可证**: MIT

## 风险控制（前置）

> 本节只做路由：把越权边界与凭据红线提到最前，细则仍以其指向的条目为唯一事实源。

### 必须停下来交回用户的情形

- **批量重装 venv 依赖**：必须由用户在普通终端执行 `pip install --ignore-installed --no-deps -r requirements.txt`——沙箱拦截发生在 pip 已开始卸载之后，会清空包目录。分级流程见「CI / workflow 约定」的「venv 依赖修复分级处置」。
- **清理范围越界**：收尾清理只限本次任务自己产生的一次性脚本与 `tests/` 下用例生成的临时输出；`downloads/`/`logs/`/`backup_config/` 等运行期产物目录**不删**，`scripts/` 下正式维护脚本**不动**（见「测试收尾清理临时脚本」）。
- **删除被 harness safe-delete 拦截**：记下路径、按同节口径逐文件重试；仍删不净时在回复里明确列出残留路径交回用户，**不得静默跳过**。
- **治理式流程技能（vibe 等）需要 run 范围与 artifact root**：先由用户确认，不得把工具安装目录当产物根目录（见「流程编排技能的使用边界」）。

### 凭据与敏感配置红线

- **不得提交 / 外传运行时配置**：`config/config.ini` 与 `config/URL_config.ini` 含凭据、已被 `.gitignore` 忽略且经 `.dockerignore` 不入镜像；新增同类文件须同步确认忽略规则。
- **写入配置或日志前必须脱敏**：URL / 代理地址一律经 `utils.mask_credentials()`；Web 面板敏感键判定走「节白名单 + 键名正则」双重口径，`'***'` 掩码跳过是写入侧唯一防线（见「已知坑」「凭据与敏感配置脱敏」）。
- **文档与审查记录里不得出现真实凭据**：新增 `CODE_REVIEW_*.md` / `DIAGNOSIS_*.md` 类根目录文档时只写脱敏后的样例值。

## Python 版本

- **最低要求 / 目标 / mypy 检查版本**: Python >= 3.14（`requires-python = ">=3.14"`）。
- **3.14 破坏性变更基线**: `asyncio.get_event_loop()` 不再隐式创建事件循环（无当前循环时抛 RuntimeError）；`pkg_resources`、PEP 594 亡故电池模块已移除；新代码统一走 `ctypes.WinDLL`（对齐 web.py 惯例，而非 `ctypes.windll`）。
- 语法/编译检查一律使用项目 venv 的 Python 3.14（见「已知坑」PEP 758 条目）。

## 代码风格

> 以下 Black / isort / mypy 三段 TOML 是 `pyproject.toml` 中 `[tool.*]` 的摘录；配置本体才是事实源。

### Black

```toml
line-length = 120
target-version = ['py314']
include = '\.pyi?$'
```

排除目录: `.git`, `.venv`, `build`, `dist`, `__pycache__`, `.pyc`, `node`, `ffmpeg`, `downloads`, `logs`

- **except 多异常写法**: 本仓统一写 `except A, B:`（不带括号，PEP 758，依赖 ≥3.14）。两种写法 black 均接受，统一无括号是**风格约定，不是门禁强制**；新增/修改代码写无括号，**存量带括号写法不要为对齐而批量改动**（会造成无意义 diff）。需要 `as` 绑定时必须回退加括号（`except (A, B) as e:`）。不要为兼容 <3.14 而加括号。

### isort

```toml
profile = "black"
line_length = 120
known_first_party = ["src", "i18n"]
```

排除目录: `.git`, `node`, `ffmpeg`, `downloads`, `__pycache__`, `*.pyc`

### mypy

```toml
python_version = "3.14"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true
```

- **不带路径参数**：检查范围由 `pyproject.toml [tool.mypy].files` 定义（src/ + 根入口 + build_exe.py + scripts/ + tests/）。显式传参（如 `mypy src/`）会**覆盖**该配置只查 src/；排障可收窄，但**门禁结果以无参数跑法为准**。早期只查 src/ 时根入口漏 import（gui.py 的 `logger`/`session_id` 运行时 NameError）长期逃逸。
- **平台符号门控双跑同样不带路径**：见「已知坑」平台专属符号条目。

#### typings/ 存根的「仅 IDE 暴露」告警处理（2026-09-24 定稿）

`[tool.mypy].exclude` 含 `typings`，CLI 门禁不查；但 IDE 的 mypy 语言服务器仍实时检查单独打开的 `.pyi` 且不消费 `ignore_missing_imports = true`——出现「门禁全绿、IDE 单文件红」属 IDE 噪声，不得按门禁失败处理，也不得放任不管。

- **唯一允许的修复方式**：文件级 `# mypy: disable-error-code="<code>"`，写在头部注释块内（先于任何 `import`），并紧跟「为什么不引入 `types-*` 依赖」的说明。
- **不得**为此新增 `types-*` 开发依赖；**不得**在 `pyproject.toml` 加全局 `disable_error_code`；**不得**用行内 `# type: ignore[<code>]`（本项目配置下变 unused）或 `# mypy: ignore-errors` 整文件豁免。pyright/basedpyright 放宽走同目录既有的 `# pyright: ...` 指令。
- **现存量两处**（新增第三处前先复跑枚举命令确认归因）：① `typings/execjs/*` 的 `import six` 报 `[import-untyped]`；② `typings/customtkinter/__init__.pyi` 的 `_CTkWidget` 混入覆盖报 `[misc]`（与类型依赖无关，装任何包都不消失）。
- 改完存根后须确认：`mypy`（无参）exit 0、`black --check` 对被改文件 unchanged、`python scripts/check_annotations.py` 通过。

### 注释约定

- **统一使用 `#` 行注释，不使用三引号 docstring**（可机检约束：docstring 进 AST，`#` 注释不进，AST 等价性校验借此证明「逻辑未改动、未误插 docstring」）。
- **写「为什么」而非「做什么」**：边界条件、平台差异、风控信号、降级路径、异常吞没后果、并发与时序假设。
- 三个层次：模块头总览 / 函数级职责 / 关键分支与边界的「为什么」。`src/stream_select.py`、`src/scheduler.py` 是参照。
- **修改注释只增不改**：不得删除或重写已有解释性注释；需修正时在其下方补充。
- **「只增不改」的例外**：不适用于已被证伪的事实性陈述——源码注释里的错误结论改正原文并压为一行带日期历史注；本文件自身被证伪的条目直接改正文。
- **「更正考古」段可压缩**：多层叠加的修订段落允许压为「当前实测状态 + 一行 `[历史注]`」，但实测读数、主机名/URL、常量名、环境变量名、平台名、判据、并发与时序假设、错误码、真实存在的回归锁用例名一律逐字保留。

### 注释检查工具（scripts/check_annotations.py）

三模式：

| 命令 | 用途 |
| --- | --- |
| `python scripts/check_annotations.py` | 规范检查（禁 docstring、密度阈值、模块头） |
| `python scripts/check_annotations.py --snapshot DIR` | 建立基线快照 |
| `python scripts/check_annotations.py --baseline DIR` | 与基线比对，证明「只改了注释、未改逻辑」 |
| `python scripts/check_annotations.py --min-density N` | 自定义密度阈值（默认 13.0） |

- 等价性校验：Python 比对 `ast.dump` 全量序列化；JS/CSS/HTML 剥离注释后比对有效代码行。注释与空行不参与。
- 密度检查只对 Python 生效；前端注释按各自语言惯例。
- 排除项：`douyin_pb2.py`（protoc 生成）、`douyin_live_recorder_standalone.py`（历史遗留），以及 `__pycache__/node/ffmpeg/.venv/build/dist` 等目录。
- **三个盲点（工具发现不了，须另行检查）**：
  1. `except A, B:` 与 `except (A, B):` AST 完全相同——无括号被改写成带括号不会被校验发现，`grep -c 'except [A-Za-z_][A-Za-z0-9_.]*, [A-Za-z_]' <file>` 核对。
  2. 注释缩进错误不影响 AST，只有 `black --check` 能发现——必须与 black 配套。
  3. **换行符形态变化对两者完全隐形**：`ast.parse` 把 `\r\n` 与 `\n` 视为同一行尾，black 按文件首个行尾为准。本仓 CRLF/LF 混存（`main.py`/`src/web_api.py`/`gui.py`/`i18n.py` 等纯 CRLF，部分 `tests/*.py` 纯 LF），整文件 `Path.write_text()` 重写会静默转 LF。判据（改任何文件前后各跑一次，两侧「原本为 0 的那项」必须仍为 0）：`python -c "import pathlib;b=pathlib.Path(f).read_bytes();print(b.count(b'\r\n'), b.count(b'\n')-b.count(b'\r\n'))"`。连带后果：按原文匹配 `\n\n` 的断言遇纯 CRLF 源文件恒不匹配（`tests/frontend/test_regression_2026_09_22_gates.mjs` 的 MIN-2241 曾因此长期红，锚点已改 `\r?\n\r?\n`）。

## 项目结构

完整目录树已外迁为纯参考段：[项目结构目录树][struct-tree]；逐模块覆盖率阈值数值不在本文件维护（事实源 `scripts/check_coverage.py` 的 `MODULE_THRESHOLDS`）。

[struct-tree]: docs/agent-reference/project-structure.md

## 入口点

| 命令                    | 模块          | 说明       |
| --------------------- | ----------- | -------- |
| `douyin-recorder`     | `main:main` | CLI 录制核心 |
| `douyin-recorder-gui` | `gui:main`  | 图形界面     |
| `douyin-recorder-web` | `web:main`  | Web 管理面板 |

## 依赖管理

- **运行时依赖**: `pyproject.toml [project.dependencies]` 与 `requirements.txt` 保持同步（23 条，2026-09-26 复核：`h2`/`socksio` 于 2026-09-23 补入后由 21→23，两侧包名集合逐项相等）。
- **开发 / 构建 / GUI 依赖**: `pip install .[dev]`（pytest/black/isort/mypy）/`.[build]`（PyInstaller>=6.10.0）/`.[gui]`（customtkinter/pystray/Pillow）；三者均不进运行时清单，故 `requirements.txt` 只有 23 条运行时依赖。
- **i18n 依赖**: PyYAML（zh_TW.yaml 加载；缺失时仅损失 YAML 格式）。
- **版本下限（须与 `requirements.txt` 和 `pyproject.toml [project.dependencies]` 三处一致）**: `pystray>=0.19.5`、`Pillow>=12.3.0`、`customtkinter>=6.0.0`。
- **安全下限（清单只写下限）**: 「声明区间内仍含已知受影响版本」是真实风险，只能靠抬高下限消除：`starlette>=1.3.1`（CVE-2026-48710 受影响 <=1.0.0；PYSEC-2026-2280/2281 修复于 1.1.0；PYSEC-2026-248/249 修复于 1.3.0/1.3.1——旧下限 1.0.1 自身仍在受影响段内，2026-09-21 已二次抬升）、`urllib3>=2.7.0`（显式声明，因是 requests 传递依赖且运行期同步出站 HTTP 穿过它，CVE-2026-44431）、`h2>=4.4.1`（PYSEC-2026-3628 / GHSA-6hr6-w5qg-qmwg，重复 Host 头致请求走私，OSV 区间 `introduced=0` / `fixed=4.4.1`；旧下限 4.3.0 自身落在受影响段——它只修了同源的 PYSEC-2026-1435，2026-09-26 由 `deps-audit`「下限复核」步抓出）。`python-multipart>=0.0.32`、`requests>=2.34.2` 均已高于修复版本。`pip-audit` 同属 CI 审计工具，**不得**进 `requirements.txt`/`[project.dependencies]`。新增/上调下限时跑一次 `deps-audit`。
- **前端测试零 Python/npm 依赖**: `tests/frontend/*.mjs` 用 Node 内置 `node:test`，只需系统 Node.js（与 JS 签名脚本共用运行时）。
- **依赖缺失排查**: venv 缺 `brotli`/`protobuf` 等表现为**测试收集期** `ModuleNotFoundError`，先核对 `pip list` 与 `requirements.txt` 差异再怀疑代码；pip 走本地代理被拒时用 `HTTP_PROXY="" HTTPS_PROXY="" pip install --proxy "" <pkg>` 绕过（装完出现「目录破损」按「CI / workflow 约定」分级处置，不要直接重试 pip）。

## 测试

```toml
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
```

- **质量门禁（须保持）**: `pytest`（0 警告）+ black/isort/mypy 三条（路径换成 `tests/`）+ `basedpyright tests/`（0 error/0 warning；basedpyright 为本地补充门禁）。
- **pytest「0 警告」口径**: warnings summary 为空（0 条）。第三方库告警一律经 `pyproject.toml [tool.pytest.ini_options].filterwarnings` 显式 ignore 并附来源注释；**禁止用 filterwarnings 掩盖项目自身告警**，禁止给用例加宽泛过滤。协程类 RuntimeWarning 由 GC 延迟触发、ignore 拦不住——必须修根因（见「已知坑」跨循环关闭 AsyncClient）。
- 覆盖率源码 `src/`、排除 `tests/`/`__pycache__/`/`node/`/`ffmpeg/` 等（与 `.gitignore`/`.dockerignore`/pyproject 同源）；门禁：`python scripts/check_coverage.py`（阈值事实源 `MODULE_THRESHOLDS`）。
- **前端用例（`tests/frontend/*.mjs`）**: Node 内置 `node:test` + `node:vm` 沙箱驱动 `web/app.js`，零 npm 依赖；由同名 Python 包装用例以子进程 `node --test` 调用，Node 缺失时 skip。新增前端用例沿用「`.mjs` 真用例 + `.py` 包装」双文件结构。
- **创建/更新测试**: 按「源码分析 → Mock 配置 → 验证执行」编写；新建用例与被测模块同名（`src/x.py` ↔ `tests/test_x.py`），并用变异验证证明用例真能抓回归（删掉生产实现用例应变红）。**变异验证必做**：新增安全不变量类用例（黄金快照、`-reconnect*`/`-segment_format` 回归锁、节流/锁/退避）；**免做**：仅调整既有断言或新增已被完整覆盖的平凡用例。

### 测试编写强制约定

- **环境变量一律用 `monkeypatch.setenv/delenv`，禁用 `patch.dict(os.environ)`**: `patch.dict` 整体快照 `os.environ`，harness 注入的 `CODEBUDDY_MCP_CONFIG` 膨胀超 32767 上限写回即抛 `ValueError`。`monkeypatch` 只动单个 key。已有 `_clear_proxy_env(monkeypatch)` helper。
- **patch `main.py` 的 subprocess 必须替换 main 的全局引用**: 禁 `monkeypatch.setattr(main.subprocess, "Popen", ...)`（会波及 harness 守护线程）。正确：`shim = types.SimpleNamespace(**vars(subprocess))` → `shim.Popen = FakePopen` → `monkeypatch.setattr(main, "subprocess", shim)`。
- **FakePopen 必须是类且定义 `__class_getitem__`**: `check_subprocess` 内层 `proc: subprocess.Popen[bytes]` 在 `def` 时求值（`main.py` 未启用 `from __future__ import annotations`）。
- **双模式测试脚本须带 `int(sys.argv)` 守卫**: `tests/test_*_live_collector.py`（bili/douyin/douyu/huya/twitch 共 5 个）既可独立运行也被 pytest 收集，顶层 `SECONDS = int(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else N`。
- **harness safe-delete 护栏按轮次计删除配额**: 测试内 `os.remove` 可能被拦（`SAFE_DELETE_BULK_CONFIRM_REQUIRED` / `SAFE_DELETE_FAIL_CLOSED`）。**均非代码回归**——预清测试输出目录后重跑即可。清理范围只限 `tests/` 下由用例生成的临时输出（Windows：`Get-ChildItem tests -Recurse -Directory -Filter tmp* | Remove-Item -Recurse -Force`），**不要**删 `downloads/`/`logs/`/`backup_config/`。
- **「文件只读」用例不能只靠 `chmod(0o444)`**: `config_io.py`/`utils.py` 写回均走 `_atomic_write_text`（同目录临时文件 + `os.replace`），而 `os.replace` 只校验目标**所在目录**写权限。正确做法：`monkeypatch.setattr(config_io.os, "replace", deny)` 对目标路径抛 `PermissionError`，其余透传真实 `os.replace`，跨平台稳定复现（`test_read_config_value_missing_key_readonly_ok` 即此坑）。
- **改锁类型需同步改测试**: `tests/test_concurrency.py::test_ttwid_module_pattern` 断言凭据锁具体类型。
- **测试产物一律走 `tmp_path`**: 不得写导入期 makedirs 的会话级共享目录（避免多 pytest 会话重叠竞态，全量红、单文件绿）。`tests/_out_live` 由 5 个 live_collector 手跑真机验证时写，但会被任意会话退出清掉，要留存得先复制出去。

### 测试收尾清理临时脚本

- **收尾必须删除任务中生成的一次性脚本与产物**：前缀分三类——`_tmp_`/`tmp_`（通用临时）、`mock_`（桩服务/模拟器）。残留会污染 `git status`、被 mypy 收编（`[tool.mypy].files` 含 `scripts/`/`tests/`）、误导协作者。**任务收尾一律删除**，不留「下次可能还用」。
- **优先写在仓库之外**: 落 `%TEMP%`/`/tmp` 或 `tempfile.mkdtemp()`；确需写在仓库内者用完即删，统一前缀命名；需长期复用才进 `scripts/`。
- **清理范围与禁区**: 只删本次任务产生的临时脚本与输出；**不要**删 `downloads/`/`logs/`/`backup_config/` 运行期产物目录、**不要**动 `scripts/` 下正式维护脚本。
- 清理前 `git status --short` 列出未跟踪文件，对 `.workbuddy/` 等 gitignore 目录显式枚举后确认再删；被 safe-delete 拦截时逐文件重试或列出残留交回用户，**不得静默跳过**。

```powershell
# Windows PowerShell（代理沙箱 Git Bash 有 coreutils，POSIX 段亦可执行）
Get-ChildItem -Recurse -File -Include *_tmp_*.py,tmp_*.py,mock_*.py,*_tmp_*.txt,tmp_*.txt |
  Where-Object { $_.FullName -notmatch '\\(\.venv|node_modules)\\' } | Remove-Item -Force
```

```bash
# POSIX / Linux CI
find . -type f \( -name '*_tmp_*.py' -o -name 'tmp_*.py' -o -name 'mock_*.py' \
  -o -name '*_tmp_*.txt' -o -name 'tmp_*.txt' \) -not -path '*/.venv/*' -delete
```

## 构建命令

```bash
pip install -r requirements.txt
python build_exe.py              # 标准打包
python build_exe.py --smoke      # 打包 + 冒烟测试
python build_exe.py --no-zip     # 只打包不压缩
python build_exe.py --no-runtime # 跳过 ffmpeg/node（减小体积）
python build_exe.py --dual       # 同时生成 lite + full 两个 zip
docker build --build-arg APP_VERSION="$(python -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")" -t douyin-recorder .
docker compose up -d
```

### 打包与冒烟测试语义（build_exe.py）

- 打包入口一次产出 CLI / GUI / Web 三个 exe + 共享 `_internal/`（`.github/workflows/build-release.yml` 三平台跑 `--smoke`）。
- 冒烟判定：`FATAL_MARKERS = ("Traceback (most recent call last)", "ModuleNotFoundError", "ImportError")`；`_finish()` 仅当进程已退出且输出含 FATAL_MARKERS 才判失败（进程存活时 Traceback 视为良性）；GUI 冒烟用 `ignore_patterns=("Failed to dock icon",)` 忽略 headless 良性堆栈。

### 产物体积门禁（2026-09-24 定稿）

- **度量侧唯一入口**: `python scripts/report_bundle_size.py dist/DouyinLiveRecorder`（`--top N`/`--json F`/`--compare F`/`--strict`）。体积结论**只以本机实跑为准**，不估算。
- **排除侧唯一入口**: `build_exe.py` 的 `BLOAT_EXCLUDES` 由 `SPEC_TEMPLATE` 生成 `excludes_bloat` 挂在**三个** Analysis 上（必须三处都挂，否则合并去重后等于没排）。新增排除项准入：① 指出运行期不可达；② 复测体积；③ 本地 `--smoke --no-runtime` 三入口通过。判据是「不可达」不是「看着没用」。
- **已知体积大头（固定成本，不可删）**: `python314.dll` 6.47MB、`libcrypto/libssl` 7.22MB（HTTPS）、`pydantic_core` 4.93MB（FastAPI）、Tcl/Tk 5.28MB（GUI），合计约 24MB。
- **已评估未采纳（勿重复提议）**: ① `strip=True`——Windows 无 strip 可执行文件；② `upx=True`——提高杀软误报率，本产物未签名。

### CI / workflow 约定

- **网络安装重试统一走 `.github/actions/retry` 复合动作**（线性退避），禁止在 job 内重新内联 `for i in 1 2 3` 重试循环；核对 `grep -c 'uses: \./\.github/actions/retry' .github/workflows/<file>`。
- **actions 大版本基线 v7**: `checkout`/`setup-python`/`setup-node`/`upload-artifact` 统一 v7；第三方非认证动作的 ref 口径见「已知坑」MIN-17。
- **版本常量跨 workflow 同值**: `python_build`(3.14) 与 `node_version`(24) 在 ci.yml 与 build-release.yml 各自声明，改一处须同步另一处。
- **触发与并发策略区分**: ci.yml 限 main 的 push/PR + `cancel-in-progress: true`；build-release.yml 由 `v*` tag 触发 + `cancel-in-progress: false`。
- **dockerignore / gitignore 同源约定**: 本地工具生成目录（`.mimosa/`/`.qoder/`/`.agents/`/`.pnpm-store/`/`.npm-cache/`/`.dsh-validation/`/`.ego-browser-test/`/`.plugin-src/`/`.tmp-dps-extract/`/`.v2c/`/`pytest-cache-files-*/`）与运行期产物目录（`downloads/`/`logs/`/`backup_config/`）须在两份 ignore 文件与 pyproject 各工具排除列表（black/isort/mypy/basedpyright/coverage）同步维护，漏一处即「未跟踪目录 / 误入镜像 / 工具误扫描」。
- **配置键审计须先归一化大小写**: 核对「代码读取的键」与 `config/config.ini` 实际键时先转小写再比对（configparser 大小写不敏感，代码常量大写、配置文件小写，精确比对会误报缺失键）。`config/config.ini` 被 `.gitignore` 忽略，故 README 配置块才是新用户默认值事实源，本地个性化取值不是文档漂移。
- **venv 依赖修复分级处置**: 批量 `pip install --force-reinstall` 会被沙箱拦截且拦截在卸载之后，清空包目录（`ImportError: cannot import name 'x' from 'y' (unknown location)`，`pip check` 查不出）。三级：① **一级（代理自行）**单/少数包破损——wheel 直解绕开卸载：`pip download --no-deps -d <tmpdir> <pkg>` → `zipfile.ZipFile(wheel).extractall(<site-packages>)`；② **二级（代理可试）**常规补装单个小包 `HTTP_PROXY="" HTTPS_PROXY="" pip install --proxy "" <pkg>`，被拦立即转三级；③ **三级（交回用户）**批量重装 `pip install --ignore-installed --no-deps -r requirements.txt`。**破损检测三查法**：① 包目录递归数 `.py`/`.pyd` 为 0；② 目录整体消失逐个 import 实测；③ RECORD 对账只作辅助。
- **覆盖率排除规则两 job 同源**: `pyproject [tool.coverage.report]` 与 `.coveragerc-concurrency` 排除条目必须一致且一律用 `exclude_also`（追加）而非 `exclude_lines`（替换，会丢三条默认排除规则）。
- **镜像额外排除集**（仅 `.dockerignore`）：`uv.lock`/`scripts/`/`AGENTS.md`/`README_EN.md`/`CODE_WIKI_EN.md`/`.coveragerc-concurrency` 及审查记录通配 `CODE_REVIEW_*.md`/`DIAGNOSIS_*.md`/`PERF_REVIEW_*.md`/`PROPOSAL_*.md`（随仓库分发，不得加进 `.gitignore`；换用新前缀必须三处同改）。
- **门禁环境变量 `PYTHONUTF8=1`**: 见「格式化命令」MID-63 条目。
- **`deps-audit` job**: `ci.yml` 中 `pip-audit -r requirements.txt`（按 OSV 审镜像与 CI 实际消费清单），独立成 job 且是 `ci-summary.needs` 的一部分（required check 唯一暴露面）。出现新公告优先抬下限而非 `--ignore-vuln` 白名单。本地复现须自带 `PYTHONUTF8=1`（中文 Windows 下 pip-audit 读中文注释行会 `UnicodeDecodeError`）。
- **发布链运行时钉定在 prepare 单点收敛（SEV-10）**: 钉定值事实源是 `build_exe.py`，不得把哈希副本写进 workflow（见「已知坑」发布钉定条目）。

## 格式化命令（门禁唯一基准）

> 本节是全项目门禁命令唯一事实源。`ci.yml` 各 job 与之逐字一致；其它章节一律**引用本节**，不得另定一套。

```bash
# PYTHONUTF8=1 是门禁语义的一部分，不得删（MID-63）：GBK locale 下 isort 会对含中文注释文件
# 抛 'gbk' codec can't encode 并静默跳过、rc 仍 0——本地与 CI 都没查。
PYTHONUTF8=1 python -m black --check --diff --line-length 120 --target-version py314 .
PYTHONUTF8=1 python -m isort --check-only --diff --profile black --line-length 120 .
mypy                      # 不带路径，范围取 pyproject [tool.mypy].files
mypy --platform linux     # 涉及平台专属符号时增跑
python scripts/check_annotations.py
python scripts/compile_po.py --check
python scripts/check_version.py
python scripts/check_runtime_pins.py  # 只查结构；--strict（发布路径）见「CI / workflow 约定」
```

- **`check_annotations.py` 不止查注释**: 常驻符号可达性检查，报告「引用了全仓都没有绑定的名字」（删除模块级函数/常量却留调用点的形态）。该命令在上方清单内，CI 与 `run_gates.py` 两侧都跑。
- **本地一次性触发点**: `python scripts/run_gates.py` 按原顺序跑完全部 `--check` 型门禁（含条件增跑的 `mypy --platform linux`），任一失败非 0 退出；`--list`/`--only`/`--keep-going` 用于排障。脚本运行时解析本节 bash 块，**本节仍是唯一事实源**，禁止另建并行清单。给门禁写行尾注释安全，写行首注释会被整行跳过。
- **一律显式传参**（`--line-length 120 --target-version py314`/`--profile black`）：配置会继承，但显式参数避免本地配置漂移造成「本地过、CI 挂」，也与 CI 逐字对齐。排除目录不需传（由 pyproject 生效）。
- **`PYTHONUTF8=1` + 「告警即失败」（MID-63）**: isort 读文件用平台默认编码，GBK locale 下遇中文注释只发 `UserWarning: Unable to parse file …` 就**跳过该文件**、rc 仍 0——本地全绿、CI 也全绿，两侧都没查。两条配套约束：① `run_gates.py` 把行首 `NAME=value` 转子进程环境变量并对 stderr 中 `Unable to parse file` 判失败；② `ci.yml` 用 step 级 `env: PYTHONUTF8: "1"` + 独立 silent-skip 兜底步骤。
- **`PYTHONUTF8` 必须同时覆盖子进程和转发输出的父进程**: `run_gates.py` 逐行读子进程 stderr 再写自己 stdout，中文 Windows 下本进程 stdout 是 cp936，black 通过时 emoji 行会让转发语句抛 `UnicodeEncodeError` 炸掉门禁进程。现由 `run_gates.ensure_utf8_streams()`（`reconfigure(encoding="utf-8", errors="replace")`）修根因；`errors="replace"` 是兜底，**不得**用「只判断退出码」或「过滤 emoji」绕过。
- **`reconfigure(encoding="utf-8")` 必须同时写 `errors="replace"`**: CPython 规定只传 `encoding` 未传 `errors` 时会把错误处理器重置为 `'strict'`。本仓「Windows 控制台 UTF-8 补丁」重复实现于 6 处，`build_exe._ensure_utf8_streams()` 曾漏写 `errors`，而 `tests/test_build_exe.py` 在 pytest 进程内调 `build_exe.main()`——pytest 的 fd 捕获包装器被就地翻成 strict，非 UTF-8 字节落进捕获文件会在会话收尾读回时抛 `UnicodeDecodeError`。三条约束：① 任何 `reconfigure` 显式给 `errors`；② `tests/conftest.py` 的 `_guard_stdio_encoding_policy` 逐用例校对 `(encoding, errors)`，宿主进程编码策略属框架资产、用例不得改；③ `gui._install_crash_sink()` 仅 `__name__ == "__main__"` 时装进程级钩子。
- **门禁「告警即失败」推广口径**: 新增门禁若存在「跳过/降级只发 warning、退出码仍 0」形态（isort `Unable to parse file`/coverage「无数据」/pytest warnings summary），必须同回路判失败，否则写明该门禁不自证覆盖。
- **`mypy` 不带路径参数**: 见「代码风格」mypy 条目。

### basedpyright（本地补充门禁，CI 不跑）

- 命令：`basedpyright`（不传路径，范围取 `pyproject [tool.basedpyright]`）；要求 0 error/0 warning。
- 与 mypy 分工：mypy 是跨平台 CI 门禁（Linux runner）；basedpyright 是本地严格度补充，报错码不同，ignore 注释按各自 code 填写。
- **裁决规则**: CI 只跑 mypy。只在 Linux 或只在 Windows 出现的基于 basedpyright 结论，以与 CI 一致的 Linux 一侧为准；不要为两侧静默而加 `# type: ignore`（会触发 `reportUnnecessaryTypeIgnoreComment`）。

### isort 收尾清理 `.isorted` 备份残留

清理命令必须匹配 `*.isorted`（`*.py.isorted` 匹配不到 `*.pyi.isorted`）：

```powershell
Get-ChildItem -Recurse -Filter *.isorted |
  Where-Object { $_.FullName -notmatch '\\(\.venv|node_modules)\\' } | Remove-Item -Force
```

```bash
find . -name "*.isorted" -delete
```

## 完成定义（Definition of Done）

代码通过门禁 **不等于** 完成。改动落地后按序执行 1→6，任一条不满足即未完成：

1. **门禁全绿**: `python scripts/run_gates.py` + `pytest`（0 警告）+ `scripts/check_coverage.py`；basedpyright 本地核一次。
2. **端到端真机验证**: 涉及录制链路/选源/ffmpeg 参数/平台解析的改动必须用**真实 URL** 增量跑（至少一受影响平台）并写进回复——只有单测绿不算验证过。判定口径：回复含脚本名（`test_{bili,douyin,douyu,huya,twitch}_live_collector.py`）+ 脱敏 URL + 结果状态（PASS/WARN/FAIL）+ 可核对读数（消息数/SRT 字节数）。无法执行（无外网/无活房间）时记「未执行 + 原因 + 交回用户的动作」且**不得宣布完成**。验证结论同时写进 `CODE_WIKI.md`/`CODE_WIKI_EN.md` 更新日志。
3. **回归锁**: 动到带「回归锁」标注的行为时确认对应用例存在且覆盖；缺则补。
4. **文档同源**: `CODE_WIKI.md`/`CODE_WIKI_EN.md` 更新日志追加本次变更（中英双份）；新增长期约定写回本文件。
5. **收尾清理**: 删除仓库内一次性脚本与产物（`*_tmp_*.py`/`tmp_*.py`/`mock_*.py`/`*_out.txt`），`git status --short` 核对无未跟踪残留；被 safe-delete 拦截须重试或列出残留交回用户。
6. **日志**: 当日 `.workbuddy/memory/YYYY-MM-DD.md` 追加一条；值得后来会话取用的经验同时写进 `docs/agent-reference/session-learnings.md`。

**豁免**: 纯文档/注释改动只做 1（门禁可只跑受影响部分）+4+6，第 5 步仅本次确实写过一次性脚本时执行；只改测试且不涉及生产行为时免 2。

## 流程编排技能的使用边界

- 本仓库日常改动（缺陷修复、性能优化、真机验证迭代、重构）**不进入**治理式运行时类技能（如 `vibe`）——其需求/计划冻结与阶段性硬停会打断「改一点→真机跑→看日志→再改」节奏。
- 仅当次会话用户**显式**要求（`$vibe`/`/vibe`/「进 vibe」）才加载；确需治理式执行时先由用户确认 run 范围与 artifact root。
- `brainstorming` 类「先出设计再动手」技能，对「方案已在 AGENTS.md/CODE_WIKI 钉死」或「用户已批准、正在连续推进」的改动不适用（含单文件缺陷修复）。

## 并发与线程模型

> 涉及锁 / 事件循环 / 信号量的改动必须先读本节。

### 基础模型

- **每房间一个独立线程 + 各自独立的 `asyncio.run()` 事件循环**: `main()` 为每个 URL 启常驻 `threading.Thread`（`_room_thread_target` → `start_record`），线程内以 `asyncio.run(...)` 逐轮驱动异步请求。**不存在共享的全局事件循环。**

### 调度中枢 src/scheduler.py

- 取代旧「单个全局 `Semaphore(1)` + 单向压制的 `adjust_max_request`」模型（80 房间共抢 3 槽位、严重延迟）。
- `ConcurrencyScheduler` 为中枢：
  - **并发模式由「最大同时录制数(0为不限制)」是否为 0 决定**：为 0 → 动态调速（默认 min=1/max=128，`max(下限, min(上限, ceil(活跃数/缩放因子)))`，错误率极高时温和降容但永不低于下限，杜绝死螺旋）；非 0 → 固定并发（忽略动态调速与背压，最小 1 槽）。
  - `adjust_loop` 守护循环每 5s 重算容量，取代 `adjust_max_request`（固定模式下重算为幂等 no-op）。
  - `main()` 首轮初始化 `scheduler = ConcurrencyScheduler(configured_limit=max_request)`，把全局 `semaphore`/`recording_semaphore` 两 `ResizableSemaphore` 指向其属性。
- `ResizableSemaphore`: 支持运行时 `set_value` 调容（增大唤醒等待者；减小仅降上限、不强行回收已持槽位）；`__init__`/`set_value` **允许容量 0**（暂停态）。
- `PlatformBreaker`（按 host 熔断，`closed→open→half-open`）: open 经冷却后放唯一探针，成功→closed、失败→重新 open；按 host 隔离。探针带租约（`_PROBE_LEASE_SECONDS=60s`）——探针轮可能以 `continue` 结束且不触发 `record`（主播未开播等待/`disable_record`/线程退出），`_probing` 无租约兜底将永不复位→永久熔断；租约超时后 `allow()` 重新授予探针自愈。回归测试 `test_platform_breaker_probe_lease_regrants_after_timeout`。
- **接线点仅限固定几处**: `notify.record_error/record_success` 增 `key` 形参委托 `main.scheduler`；`start_record` 入口 `record_host = host_of(record_url)` 且**必须在 `while True` 外层 try 之前预置 `record_host = ""`**（否则 basedpyright 判 possibly unbound）；平台分派前 `scheduler.allow(record_host)` 预检、False 则退避后 `continue`；`check_subprocess` 录制循环受 `recording_semaphore` 管控。
- 相关配置项「最大同时录制数(0为不限制)」兼作网络并发模式开关；「同一时间访问网络的线程数」在动态模式下为容量下限之一、固定模式下即固定并发值（最小 1）。键名禁止含 `=`/`:`（见「已知坑」configparser 分隔符）。
- **调度模块测试**: `tests/test_scheduler.py`（16 用例）；改动后 `pytest tests/test_scheduler.py`。全量 pytest 中 `tests/test_twitch_live_collector.py` 会因 safe-delete 护栏失败，属环境限制非调度问题。

### 录制结果反馈约定（main.py / src/stream_select.py）

- **`check_subprocess` 须按 ffmpeg 退出码上报调度样本**: `rc==0` → `record_success(host_of(record_url))`；`rc!=0` → `record_error(...)`。**禁止轮末无条件 `record_success`**——失败轮记成成功会稀释按 host 熔断统计（虎牙房间秒级 403 死循环根因之一）。
- **快速失败须记入探针退避**: `time.time() - _proc_started_at <= _FFMPEG_FAST_FAIL_SECONDS`(20.0) 判快速失败时，解析 `-i` 后实际拉流地址调 `stream_select.mark_ffmpeg_reject(url, platform)`；下一轮 `select_source_url` 跳过该线路。`platform` 不在退避白名单（`_PROBE_BACKOFF_PLATFORMS = ("虎牙直播",)`）时静默无操作，勿扩大到斗鱼。缺 `-i` 以 `except ValueError` 跳过退避标记。慢速失败只记失败样本不记退避。
- **录制成功须撤销该地址探针退避（`clear_ffmpeg_reject`，与 `mark` 对称）**: 成功分支解析 `-i` 后实际拉流地址调 `clear_ffmpeg_reject(url, platform)`（只清实际成功的 FLV，HLS 退避不顺带清）；共用同一白名单与退避键。
- **解析成功轮即上报成功样本**: `port_info["anchor_name"]` 非空须 `record_success(record_host)`，与解析失败分支 `record_error` 对称（此前成功样本仅在 ffmpeg 退出时上报，half-open 探针房间长时间录制期间同 host 其余房间持续熔断饿死）。
- **直下路径（`direct_download_stream`）补成功样本**: 成功路径末尾 `record_success(record_host)`。
- 回归测试：`tests/test_record_failure_feedback.py`（5 用例）、`tests/test_stream_select.py::test_mark_ffmpeg_reject_marks_backoff`。

### 锁的强制约定

- **禁止模块级 `asyncio.Lock()` 单例**: 惰性绑定首个 `await` 它的事件循环，后续新循环 `await` 即抛 `RuntimeError: … bound to a different event loop`。正确做法见 `src/async_http.py` 的 `_get_client_lock()`：**随当前事件循环缓存/重建**（比对 `asyncio.get_running_loop()`）。仅单房间不报错，**必须并发多房间才能复现**。
- **跨 `await` 持有的跨线程锁一律用 `threading.RLock`，不得用 `threading.Lock`**: 凭据去重锁（`_ttwid_lock`/`_kuaishou_did_lock`/`_twitch_client_id_lock`）跨越 `await` 持有；普通 `Lock` 下同一循环第二个并发协程会自旋死锁。`RLock` 使同线程重入退化为幂等重复拉取，跨线程去重语义不变。

## 关键约定

1. **版本号同步**: 唯一事实源 `pyproject.toml`，各消费方动态读取不写死。`main.py`/`src/web_api.py` 经 `importlib.metadata` 读取；`Dockerfile` 经 `APP_VERSION` 注入；`zh_CN.po` 不再写版本号。`scripts/check_version.py` 校验上述动态化状态。
2. **行宽**: 120 字符（black + isort 统一）。
3. **导入排序**: isort `black` profile，`known_first_party = ["src", "i18n"]`。
4. **运行时资源**: `config/`/`ffmpeg/`/`node/` 与 exe 同级，不进入 `_internal/`。
5. **JS 签名脚本**: 位于 `src/javascript/`，通过 `__file__` 定位，打包收入 `_internal/`。
6. **编码与注释风格**: 源文件 UTF-8、注释中文；注释统一 `#`（见「注释约定」），禁止 docstring（多行字符串字面量如 `SPEC_TEMPLATE` 合法保留）。
7. **排除目录**: `node/`/`ffmpeg/`/`downloads/`/`__pycache__/` 在所有工具均排除。
8. **停止录制流程日志归档**: 四个运行日志（`logs/streamget.log`/`PlayURL.log`/`danmaku_monitor.jsonl`/`web_console.log`）在停止录制时经 `src/log_archive.py::archive_runtime_logs` 改名归档（冲突追加 `_N`，缺失/失败仅告警跳过）。触发点两处：Web「停止录制」（`reopen_streams=True`）、进程退出 atexit（须先于两个 cleanup 注册、`reopen_streams=False`）。硬约束：Windows 句柄未关 rename 必抛 PermissionError，改名前须先关句柄（loguru sink 经 `logger.remove()`、弹幕边车经 `DanmakuMonitorHub.close_file()`、`web_console.log` 经 flush+close+`rebind_console_sink()`）。`DLR_GUI_PARENT=1` 与测试（`DOUYIN_DISABLE_LOG_ARCHIVE=1`）一律早返回。回归锁：`tests/test_log_archive.py`+`tests/test_web_api.py::TestRecordingToggle`。
9. **布尔配置项统一解析口径**: 禁止「字典查表+兜底实参」或「字符串相等比较」，一律走：纯解析函数 `src/config_bool.py::parse_config_bool(raw, default)`（零依赖，可被 `src/logger.py` 引用，不得放 `config_io.py`/`utils.py`）；配置层 `src/config_io.py::read_config_bool(parser, section, option, default)`（读取+缺键补写，main.py 全部布尔读取点用它）。识别集合：是/否、true/false、t/f、yes/no、y/n、on/off、1/0（strip+lower）；空值与未识别返回 default 且不覆写用户原文。另三处同源口径（`logger.py`/`web_config.read_web_config`/`gui._get_dynamic_status_info`）已改复用同一解析；`web/app.js` 按内嵌 `parseConfigBool`+`CONFIG_*_TOKENS` 保持同集合（改任一侧须同步）。**禁止**新增 `options.get(read_config_value(...), 兜底)`。回归锁：`tests/test_config_bool.py`+`tests/frontend/test_quality_ui.mjs`。
10. **出站下载源必须登记进可机检白名单**: 任何新的出站二进制/脚本下载点必须同时登记进 `tests/test_ffmpeg_install.py` 的 `DOWNLOAD_SOURCES`（键=主机，值=(完整性方式, 为什么可接受)）与 `DOWNLOAD_MODULES`；两处缺一即锁红。完整性方式为 **TOFU 的源必须默认关闭**（如 `FFMPEG_MASTER_ALLOWED`，取值走 `config_bool`），开启与跳过两侧都落 warning。权威上游必须排在任何镜像之前。该锁自带反向见证（断言确实看到 `gyan.dev` 与镜像常量）。
11. **camelCase 凭据键必须同步脱敏表**: `utils._SECRET_KEYS` 是「黑名单+左边界断言」，天然漏 camelCase（`accessToken`/`wsAuth`/`tk` 曾明文落轮转日志）。新接入平台若凭据参数是 camelCase，**必须**同步该表并在 `TestMaskCredentialsCoverage` 增加「**值确实消失**」断言——不得只断言「调用了 `mask_credentials`」。
12. **修复类注释必须附可复核判据**: 注释写「已修 X」或「回归锁：`tests/…::test_xxx`」时该用例必须真实存在且能因该修复被破坏而变红；否则如实写「待办+为何未做」。判据 `grep -rn "回归锁：tests/" main.py src/ | 逐条 grep 用例名` 复核。
13. **跨模块字符串契约不得靠自然语言子串**: 面板/GUI 解析录制端日志时 `if "没有正在录制" in msg` 在 `language=en_US/en_GB/zh_TW` 下恒假（正文经 `i18n.tr()`）。比较对象一律取 `i18n.tr(...)` 后形态，不得直接拿简中常量；结构化前缀（`#DLRQ|` 键值协议）属待批准长期方案。
14. **i18n 扫描盲区清单**: `scripts/extract_i18n_strings.py` 扫不到 ①`color_obj.print_colored(...)` ②`messagebox.show*` ③**推送正文**（`msg_push.py` 裸字面量+`str.replace` 模板）——三类新增用户可见文案必须手工登记四语目录并重编 `.mo`；并行修复中间态落 `_i18n_pending*.json` 由中央合并脚本一次性落四目录。

## 已知坑（避免回归）

### 录制链与房间线程主循环

- **录制链不得嵌套于 `if headers:` 内**: 录制主链必须位于条件判断**之外**，仅把「是否附加自定义头」作局部行为；用该条件包裹整条流程会导致无自定义头时静默不录制。
- **`real_url` 为空必须跳过录制链**: `select_source_url` 返回 None 时 `if not real_url: 告警+等待+continue`，否则 None 流入录制执行链崩溃或复用残留命令。守卫之后 `now`/`title_in_name` 为无条件赋值（移除恒真 `if real_url:` 包装）。
- **弹幕监控房间须随录制线程退出而移除**: `main.start_record` 在 outer try 的 `finally` 调 `get_hub().room_stopped(record_name)`（各 return 全覆盖），GUI `_danmaku_dispatch` 收到 `state=="stopped"` 后 pop 房间行；删掉该清理会残留失效直播间。
- **「已被注释」检查必须在解析之前**: 房间线程内层循环顶部（`exit_recording` 检查后）先查 `record_url in url_comments` 再进平台解析——原检查点在解析成功后，平台持续失败（风控空响应）时永远走不到，线程滞留占用监控位。
- **录制并发槽必须在 `Popen` 之前 acquire**（main.py::check_subprocess）: `recording_semaphore` 语义是限制同时进行 ffmpeg 数，先起进程再 acquire 则上限根本不约束 ffmpeg 进程数（资源耗尽）。结构：「`acquire` → `try:`（`Popen`+注册+弹幕启动+主循环）→ `finally: release`」，**启动段也必须落 `try` 内**，抛错同样归还槽位否则泄漏累积饿死所有后续录制。

### 流地址探针与可达性校验

- **GET 复核容错语义不得简化**（src/stream_select.py::_confirm_get_ok）: 401/403 先原样重试一次再定罪；候选已是末位（无 record_url 备选）时稳定拒绝也仅告警放行、交由 ffmpeg 定夺。删重试或末位放行会重引「探针误杀可用源」。同语义扩展：m3u8 Range-GET 探针 401/403 同样先隔 `_GET_RECHECK_INTERVAL` 重试；HLS 为唯一候选或 FLV 为 h265 不可用时传 `last_resort=True`。
- **末位候选 content-type 拒绝也须放行**: `_validate_stream_url` 的 text/html 分支与尾部非 200 分支对 `last_resort=True` 必须仅告警放行（斗鱼 hw CDN HEAD 回 405+text/html，ffmpeg 实际 GET 正常）。
- **虎牙探针退避仅限 `_PROBE_BACKOFF_PLATFORMS` 名单**: 虎牙 aldirect CDN 对同路径短时间连击限流，每轮探针+ffmpeg 拉流烧光连接预算→秒级失败循环。**绝不可把斗鱼等加入名单**（斗鱼 hw 偶发 403 由「重试一次」救回，负缓存回退会致斗鱼回退 FLV 游客态 ~70s 被掐）。
- **虎牙选源必须 FLV-first（`_FLV_FIRST_PLATFORMS`），斗鱼绝不加入**: 候选序列 FLV→HLS→record_url，冷启动假绿损失归零；FLV 不可用仍回退 HLS。斗鱼游客态 FLV ~70s 被掐必须 HLS 优先。退避中末位放行随序列末位变化，核心不变式是零探针。
- **探针退避窗口必须 ≥ 一个主循环周期**: `_probe_backoff_window() = max(_PROBE_BACKOFF_SECONDS, main.delay_default + _PROBE_BACKOFF_INTERVAL_MARGIN)`（delay_default 默认 120s），**不可改回固定 60s 常量**——否则快速失败记入退避后下一轮早已超出窗口又去撞死线路。margin 取 70s 覆盖最坏节奏。
- **录制成功须撤销探针退避（`clear_ffmpeg_reject`）**: 细则见「录制结果反馈约定」同名条目（只清实际拉流成功地址、HLS 不顺带清；与 `mark` 共用白名单与退避键）。
- **UA 双端一字不差约定**: `main.py` ffmpeg 默认移动 UA ≡ `stream_select.MOBILE_UA`（校验探针与 ffmpeg 指纹一致）；`room.HEADERS` 的 UA 参与 X-Bogus 签名（改字符串须同步四处：`MOBILE_UA`/`main.py ffmpeg 默认 UA`/`room.HEADERS`/B站 H5 UA）。全库基准（2026-08）：桌面 Chrome/141、Edg/141、Firefox/148、移动 `Android 14; Pixel 8` Chrome/141——禁止回落过旧指纹（风控特征之一）。
- **探针节流/抖动语义不得移除**: 同 host 节流（`_throttle_probe`，`_PROBE_MIN_HOST_INTERVAL=0.35s`+抖动）与重试抖动（`_recheck_delay`，`0.8s+uniform(0,0.7s)`）消除机器人节奏指纹；改为固定值或移除会重引风控误伤。测试侧 autouse fixture 置 `_throttle_probe` 为 no-op；节流专项测试经 from-import 绕过。
- **流地址可达性探测方法基线**: 抖音等 CDN 对 m3u8 的 `HEAD` 常回 4xx（含 404）而 `GET` 能拉流，故一律「HEAD 非 2xx → Range `GET bytes=0-0` 探测（200/206 判可达）」，**不要只覆盖 400/401/403/405**。同步/异步校验器的 proxy/verify/UA 三者必须一致（否则境外平台直连误判不可达）。本条与「GET 复核容错/末位放行/探针节流抖动/虎牙退避」四条互补。
- **「HLS 采集排除平台」是整组剔除，与「FLV-first 调序」两种语义不可互实现**: `[录制设置] HLS采集排除平台(逗号分隔)` 命中的平台直接不把 HLS 候选放入序列（探针一次不发、FLV 失败也不回退 HLS）；`_FLV_FIRST_PLATFORMS` 只是把 FLV 排到 HLS 前、HLS 仍留作回退。平台名须与 `platform` 字段完全一致，默认空=不排除。回归锁：`tests/test_stream_select.py` 的 5 个排除列用例。

### 弹幕采集与 SRT 写入

- **弹幕 WS 连接必须显式 `proxy=None`**（src/ws_client.py::connect）: 使 WebSocket 直连不跟随系统代理，否则 B站/斗鱼等报 `connecting through a SOCKS proxy requires python-socks` 连接即断。改动须保留 `proxy=None`。
- **B站弹幕 buvid 必须真实、AUTH_REPLY 必须显式校验**: spi 端点是 `/x/frontend/finger/spi`（少写结尾 `i` 会 200+空 body 永远 JSONDecodeError）；buvid 获取链按真实注册标识优先排序（进程缓存→cookie `buvid3=`→spi→`www.bilibili.com` 首页 Set-Cookie→随机 UUID 兜底标记 is_fallback）。`_decode_packet` 须校验 operation=8 回应的 code：非 0 经 `_reject_auth()` 告警+断开+`spider.invalidate_bili_buvid_cache()`；`_auth_watchdog` 兜底「服务器 8s 不回 AUTH_REPLY 的静默拒绝」。
- **`collector.stop()` 与采集线程握手顺序不可单独调整**（src/collector.py）: `stop()` 必须先 `set(self._stop_event)` 再读 `self._loop`；`_run()` 必须先发布 `self._loop` 再检查 `self._stop_event`（两相反顺序保证信号必被一方接收）。缺一半会丢信号致 `join(timeout=8)` 超时、线程与 SRT 句柄双泄漏。另：`_shutdown` 中 `await danmaku.stop()` 必须 `asyncio.wait_for` 限时（`_SHUTDOWN_TIMEOUT_SECONDS`），否则 SDK 半开连接挂住 `loop.stop()` 永不执行。
- **弹幕文本写入 SRT 前必须转义**（src/srt_writer.py::_sanitize_srt_text）: `user_name`/`message` 为外部可控输入，含 `\n` 截断 SRT 块、含 `-->` 被解析成新时间轴行可伪造字幕。替换（非删除）为可见字符。回归锁：注入 `normal\n2\n00:00:99,000 --> 00:00:99,999\nFAKE\n` 后产物必须仍只有 1 个块 1 条时间轴。片内 `end` 须 `max(start, min(end, _seg_seconds))` 钳制。
- **弹幕链路接线点与分段命名约定**: `start_record` 各平台分支收集 `record_danmaku_args`（局部变量每轮重置为 None）→ 6 处 `check_subprocess(..., platform=platform, danmaku_args=record_danmaku_args)` → `src/__init__.py::get_danmaku_collector(platform, args, base_filename, segment_seconds)`（实现在 `src/collector.py`）。硬约束：① `danmaku_collector.stop()` 必须在 `while process.poll() is None` 循环之外（`DanmakuCollector.stop()` 有 `_stop_called` 防重入幂等）；② 分段文件名——视频 `_%03d`（FLV 已从 `_%02d` 对齐；音频仍 `_%02d`）、SRT `{seg:03d}` 与之对应，`check_subprocess` 需同时剥离两种占位符；③ 抖音弹幕空 cookie 时在 `DouyinDanmaku.start()` 协程内 `await get_ttwid()` 动态获取（不再硬编码 ttwid）。配置项 `弹幕分片时长(秒)` 走 `_safe_float(..., 1800.0)`。
- **抖音弹幕 `signature` 保持不编码，禁止顺手加 `quote()`**（F-13）: XBogus 字符表含 `+`/`/`，但上游确认直接拼接不 encodeComponent、服务端不按 form-urlencoded 把 `+` 解成空格。改编码会让本端成为唯一异类指纹。回归锁：`tests/test_douyin_signature_encoding.py`。

### 平台接口、签名与流地址解析

- **斗鱼必须附带 FLV→m3u8 同 token HLS 候选**: 斗鱼 H5 只返 FLV，游客态 FLV 长连接 ~70s 被掐；wsAuth token 对 FLV/HLS 通用，把路径 `.flv` 改 `.m3u8` 即同 token HLS（hw CDN 200+mpegurl）。该候选由 `select_source_url` 校验 gating、不可达自动回退 FLV，须保留。
- **migu.js 输出契约为完整签名 URL**；`src/javascript/` 的**文件增删必须与 `utils._JS_SHA256_EXPECTED` 同批提交**（2026-09-26 CI 实测坑）：`tests/test_utils.py::TestJsPinTable::test_every_executable_js_is_pinned` 断言「目录里每个 `.js` == 钉定表键集」双向相等，删除脚本却没推送 `.js` 本体（或反之）会让 CI 红，而本地已删的工作区全绿——本地与远端内容不一致时**只信远端**。 `src/javascript/migu.js` 适配 migu 播放器 v_20260731+ wasm 接口（12 个导入函数、导出名重排），输出带 `ddCalcu`/`sv` 参数的完整地址（`sv` 失败回退内置默认因子）；`spider.get_migu_stream_url` 直接使用，不再拼接过期 `sv=10010`。
- **抖音接口风控信号是「HTTP 200 + 空响应体」不是 4xx**: 解析失败先看 `len(response.text)`，为 0 基本是 UA/Cookie 被拒。三条配套：① UA 敏感——`src/room.py` 模块级 `HEADERS` 是 2020 三星安卓 UA，`iesdouyin.com/web/api/v2/user/info/` 用它必被静默拒，此类接口一律用 `room.DESKTOP_UA`；② `iesdouyin.com/share/user/<sec_uid>` 已是 JS 反爬壳页，取 `unique_id` 请走 `https://www.iesdouyin.com/web/api/v2/user/info/?sec_uid=<sec_uid>`；③ `webcast.amemv.com/webcast/room/reflow/info/` 用占位 `room_id=2`+`sec_user_id` 解析主页行不通（status_code=10011）。
- **`live.douyin.com` 的 `web_rid` 同时接受数字房间号与抖音号**: `webcast/room/web/enter/` 两者皆可，`live.douyin.com/<抖音号>` 不重定向。**不要写「抖音号需先重定向解析成数字」的逻辑**（已被实测证伪并删除）。`main.py` 以 `port_info["anchor_name"]` 为空作「网址内容获取失败」判据。
- **`hevc_flv_url` 必须带 `codec=h265` 标记**（src/spider.py::extract_douyin_hevc_flv_url）: 正则抠出的 HEVC 地址必须补 `&codec=h265`（已带则原样返回）。下游 `_is_h265()`/`main.py` 的 h265 兜底**只认 URL 上的 codec 查询参数**。注意 `utils.get_query_params` 返回 **list**（`spider.get_params` 返回 str，不可混用）。

### 画质档位与选源映射

- **蓝光子档位（BD4/8/20/30）必须折叠到 BD 索引，不得塞进 `QUALITY_MAPPING`**（src/stream.py::get_quality_index）: 统一折叠为 `BD`（索引 1），细粒度靠 `BD_SUB_TIERS` 承载。`QUALITY_MAPPING` 是抖音/通用排序权威索引（OD=0,BD=1,UHD=2,HD=3,SD=4,LD=5）。`QUALITY_MAPPING_BIT`/`QUALITY_LEVEL`/`QUALITY_CODE_TO_ZH` 是其超集。中文映射（`get_quality_code`/`web_config.QUALITY_KEYWORDS`/`main.py` 白名单/`web/index.html`）均须含蓝光4M/8M/20M/30M，新增须同步四处理。测试按超集语义断言（`tests/test_stream.py::TestQualityMapping`）。
- **虎牙选档 ratio 按房间码率上限推导，exsphd 优先、bitRate 兜底，不可用时就近降级或回原画**（src/stream.py::get_huya_stream_url）: `ratio_val` 由 `bitRate` 上限推导（`HUYA_FIXED_TIERS`），exsphd 档位表存在时优先取 ≤ 上限的 ratio。请求档不可用（ratio 不在可用集合）时就近向下降级，无任何更低档时不附加 ratio 按原画(OD) 拉流，**绝不可抛异常或返回空流地址**，保持 `is_live=True` 契约交由上层重试。
- **斗鱼本地重试链只补强服务端 rate 钳制，不得替代 HLS 候选与全局退避**（src/stream.py::get_douyu_stream_url）: 按 `DOUYU_RATE_BY_CODE` 映射 rate，服务端钳制时经 `DOUYU_RATE_DESC` 全序本地最多回退 2 档重试（复用同一 `get_douyu_stream_data`）；全部失败时明确告警「已无更低档位」并保持 `is_live=True`。

### HTTP 客户端复用与连接管理

- **httpx 请求级 headers 是「合并」不是「替换」**: 把 UA/Referer/Cookie 挂 client 级时，只传 `{"Range": "bytes=0-0"}` 的请求仍带全部 client 级头——不要据此判「丢了请求头」。但客户端一旦在多个候选间复用（select_source_url 整轮共用一支），业务头绝不能再挂 client 级（候选间互相污染），必须逐请求显式传入。
- **探针客户端复用作用域 = 单次选源，禁止升级为全局缓存**: `_validate_stream_url` 新增可选 `client` 参数（不传时自建自管）；刻意不做按 `(proxy, verify)` 模块级全局缓存（虎牙 CDN 按连接预算限流，常驻 keepalive 会与 ffmpeg 拉流争抢）。
- **禁止为「保险」关掉探针客户端 keepalive**: 会把复用收益全部退掉；排查虎牙 403 应临时改回「每候选一支 Client」。
- **`requests.Session` 必须线程级复用，禁止每次新建**（src/sync_http.py）: `_session()` 经 `threading.local()` 缓存（Session 非线程安全不可跨线程共享）。改回每次新建会让每次出站多一轮 TCP+TLS 握手（实测 11.9→1.47ms，约 8× 退化）。`tests/test_sync_http.py` 的代理替身 patch 目标须是 `src.sync_http._session` 不是 `src.sync_http.requests`。**注意**：该模块当前无生产 importer（sync_req 调用点现只剩 tests/），保留是因为 requests 仍在运行时清单且 8× 复用结论成立——任何「已经吃到这个收益」的表述不得再写。
- **`sync_req` 的 SSL 降级路径必须保持惰性+单次覆盖**（F-12）: CERT_NONE 上下文与 opener 由 `_get_insecure_context()`/`_get_insecure_opener()` 按需构造，禁止改回模块级常驻。「无调用者」只是当下状态，不作为放宽惰性要求的理由。

### 并发、事件循环与锁

- **`asyncio.get_event_loop()` 3.14 起不再隐式创建事件循环**: 当前线程无循环时抛 RuntimeError。`src/async_http.py::close_all_clients_sync` 已改为捕获 RuntimeError 走引用清理兜底；协程内获取循环一律 `get_running_loop()`。
- **跨事件循环禁止创建/调度旧 AsyncClient 的 aclose 协程**（src/async_http.py::_get_client）: 淘汰他循环创建的旧客户端时一律**不创建** `aclose()` 协程，释放引用交 GC 兜底（三个坑：run_coroutine_threadsafe 只调度不等待、加 is_running 门控 await 仍可能永不执行、当前循环直接 await 旧 client.aclose 会操作旧循环 transport）。回归锁：`tests/test_async_http_lock.py::test_cross_loop_running_old_loop_skips_close`/`test_cross_loop_stopped_old_loop_skips_close`。
- **熔断计数必须增量、不得 `sum(deque)`；`import time` 提顶层**（src/scheduler.py）: `_fail_count`/`_global_error_count` 在样本入队/挤出时增量维护（O(1)），替代 `record()` 内 `sum(self._samples)`（O(40) 持锁遍历）；`_now`/`_allow_sleep` 用的 `time` 已在模块顶层 `import time`。
- **「调用方持锁」改「内部自持锁」必须同步清调用点外层锁**: `web_api._purge_expired_tokens()` 改为内部 `with _tokens_lock:` 后，`login` 里原有 `with _tokens_lock: _purge_expired_tokens()` 未移除——`threading.Lock` 非重入，每个登录请求自死锁（征兆：接口不报错、永远不返回）。约定：函数要么只内部加锁、要么只由调用方加锁，二选一并在注释写明；改造其一必须 `grep` 全部调用点。
- **可重入性判定一律以源码定义行为为准**: 不要把文档清单当推断依据（main.file_update_lock/`_cache_lock` 实为 `RLock`）。改动前必须 `grep` 定义行确认。

### ffmpeg 命令构造与容器格式

- **`-reconnect*` 必须在 `-i` 之前且每个选项紧跟取值**: `-reconnect_delay_max`/`-reconnect_streamed`/`-reconnect_at_eof` 是 input 级选项，写在 `-i` 之后被划入输出组且 ffmpeg 不报错（静默接受、退出码 0，输入侧从未应用）→ 重连完全失效且零可见症状。回归锁：`tests/test_ffmpeg_reconnect_args.py`（AST 锁「每 `-reconnect*` 紧跟字面量值」+「全在 `-i` 之前」）。**HLS 输入必须移除 `-reconnect_at_eof`**（`if ".m3u8" in url: del`，main.py 与 standalone 共三处定义点同步）——m3u8 播放列表 HTTP 响应结束即 EOF，该选项让 http 层无限重连，hls demuxer 永远停「待列表」一个媒体段都拉不到。回归锁：`tests/test_ffmpeg_reconnect_args.py::TestReconnectAtEofDroppedForHls`。
- **`-thread_queue_size` 只能位于 `-i` 之后**（2026-09-23 事故）: 放错侧不再是静默不生效而是拒绝打开输入（实测 `Option thread_queue_size ... cannot be applied to input url` → 退出码 -22，录制 100% 失败）。输出侧是本项目支持面内唯一合法位置。推广口径：新增任何 per-file 选项前先用 `ffmpeg -h full` 分段标题确认归属。`tests/test_ffmpeg_reconnect_args.py::TestOutputOnlyOptionsFollowInputFlag`。
- **`-segment_format` 必须与输出扩展名严格一致，且一律经 `SEGMENT_FORMAT_BY_SUFFIX` 查表**（2026-09-04 P0）: `.ts→mpegts`/`.flv→flv`/`.mkv→matroska`/`.mp4→mp4`/`.m4a→ipod`（音频分支 `SEGMENT_FORMAT_BY_SUFFIX.get("." + extension, "ipod")` 兜底）。**禁止任何分支直接写 `-segment_format` 字符串字面量**——TS 分支误写 `ipod`、M4A 误写 `mpegts` 的事故：HEVC `-c copy` 进 `ipod` 直接 `AVERROR(EINVAL)` 退出；H.264 不报错 exit 0 但把 MP4 内容写进 `.ts`（魔数 ftyp 非 0x47）静默损坏。回归锁：`tests/test_record_container.py`（映射表内容+AST 扫描「5 处取值全查表、无裸字面量」+ 查表键已注册 + 音频兜底 ipod）。
- **ffmpeg「输出侧」参数构造已统一到 `_build_ffmpeg_output_args()`，禁止各平台分支手写 `command=[...]`**（F-01）: 原 5 份复制粘贴是 `-segment_format` 字面值错配 P0 根因。输入级选项（`-reconnect*`/`-headers`/`-tls_verify`/`-http_proxy`）与 `save_file_path`/时间戳仍留 `start_record` 内，builder 只拼输出参数。新增格式分支必须经此 builder 的 `record_save_type`/`is_audio` 分发。回归锁：`tests/test_start_record_command_golden.py`（GOLDEN_REGEN=1 重生成 `tests/golden/start_record_commands.json`，字节级比对；20 用例覆盖 5 路径+m3u8 丢弃 `-reconnect_at_eof`+头/代理注入+海外超时+FLV-h265→TS+shopee 直下）。
- **F-01 收官：命令构造与平台分发的四个单一定义点**（禁止回退成内联复制粘贴）：① 输入侧 `_build_ffmpeg_input_args(real_url, user_agent, tuning, headers, tls_verify, proxy_address)`（全按 `-i` 锚点定位或插列表头，禁裸数字下标）；② 输出路径 `_build_record_output_path(...)`（扩展名/分段时间戳格式/`_%03d`/`_%02d` 全查表）；③ 执行骨架 `_run_ffmpeg_record(...)`+录后转码 `_convert_after_record(...)`（五条保存类型分支只调这三个函数，禁各自写 try/except+check_subprocess）；④ 平台分发 `_PLATFORM_RESOLVERS`（`(匹配器,处理函数)` 表）+ `_PlatformResolveContext`（原 53 层 elif 拆成 52 个 `_resolve_<host>()`，表项顺序即优先级，禁插 elif）。回归锁：`tests/test_platform_dispatch.py`+`tests/test_start_record_command_golden.py`。附带已修行为漂移（改回即回归）：TS 非分段结束时必须受 `converts_to_mp4` 裁决；分段提示行打印实际输出路径 basename。

### 日志、控制台与 GUI / 后台模式

- **Web 后台模式必须重建 loguru 控制台 sink**（web.py::_enter_background_mode）: 在 `import main` 之后才把 stdout/stderr 重定向到 `logs/web_console.log`。loguru sink 在 `add()` 时绑定具体对象，不调 `rebind_console_sink()` 重建则全部日志写往被隐藏控制台，`web_console.log` 只剩 print。**排查 Web 模式问题一律先看 `logs/streamget.log`/`PlayURL.log`，不要只看 `web_console.log`。**
- **GUI 父进程绝不持有录制日志文件句柄（`DLR_GUI_PARENT` 标记）**: `gui.py` 必须在导入任何 `src` 模块**之前**设 `os.environ["DLR_GUI_PARENT"]="1"`，拉起录制核心时 env 经 `src/logger.py::child_process_env()` 构建（剔除标记+固定 `PYTHONIOENCODING=utf-8`）。`src/logger.py` 导入期读该标记决定文件 sink 归属：GUI 进程只写 `logs/gui.log`，绝不创建 streamget.log/PlayURL.log（否则与录制子进程双开同日志文件、轮转 rename 抛 WinError 32、文件日志静默丢失+stderr 刷屏）。回归锁：`tests/test_logger_gui_parent.py`。
- **异常日志必须带异常类型与上下文，禁止裸 `logger.xxx(e)`**: Windows 下 `socket.timeout`/`TimeoutError` 的 `str()` 为空，只写 `{e}` 打出空白行。写法：`i18n.tr()` 模板+关键字实参（禁止 f-string）：`logger.debug(tr("<动作>: {masked_url} - {type_name}: {err}", masked_url=utils.mask_credentials(url), type_name=type(e).__name__, err=e))`。硬要求 `{type_name}`/`{masked_url}` 不可省；流地址校验失败还须额外输出 `status_code` 与 `content-type`，禁止静默吞异常。
- **macOS GUI 双重主线程约束**（gui.py）: Tcl/Tk 只能跑主线程，而 pystray darwin 后端 `icon.run()` 接管主线程——两者互斥。唯一正确方案：主线程先 `tray.run_detached()`（darwin 后端仅注册 NSStatusItem 不启事件循环）再 `root.mainloop()`，绝不允许把 mainloop 放子线程。配套：① `run_detached()` 前主线程调 `icon._assert_image()` 预热并置 `_icon_valid=True`（PIL 惰性编码器在冻结环境非主线程首次初始化会原生崩溃）；② `_assert_image` 是 darwin 专有方法，通用路径调用会 AttributeError 被吞导致托盘静默禁用；③ detached 退出先 `icon.visible=False` 再 `icon.stop()`。改动后必须 `py_compile` 并通过 CI（复现需 macOS 冻结构建）。
- **无控制台环境 `sys.stderr is None`，`logger.add` 前必须判空**（src/logger.py）: `pythonw.exe` 与冻结 `console=False` exe 不分配控制台，stderr 全为 None，裸写 `logger.add(sink=sys.stderr,...)` 在导入期抛 TypeError 致 gui.py 静默死亡（pythonw 跑 gui.py 失败真正根因）。必须 `if sys.stderr is not None:` 才加控制台 sink，无控制台时跳过由文件 sink 兜底。排查窗口化静默崩溃：先装 `sys.excepthook`/`threading.excepthook` 落盘+弹窗钩子，再顺调用链 grep `sink=sys.`/`print_exc`/`sys.stdout.write` 判空。
- **多房间交织日志靠 `extra[room]` 列切出，不要靠 `[record_name]` 前缀**（src/logger.py::ROOM_FIELD）: 全局 patcher 写 `record["extra"]["room"]`（ContextVar 承载当前房间），两个录制文件 sink format 含 `{extra[room]}`。`start_record` 入口先绑 `序号{count}` 占位、解析出主播名后升级为完整 `record_name`。三条不要动：① `logger.configure(extra={ROOM_FIELD: ""})` 默认值不可删（缺则每一条日志 KeyError 被丢弃）；② `logs/gui.log` 行格式刻意不带该列；③ 本机制只加关联标识，不得顺手改日志级别/filter 分档/rotation/retention。已知边界：新起线程不继承 ContextVar（弹幕线程/push_message/转码线程池该列为空，仍靠关键字辅助）。回归锁：`tests/test_logger_room_context.py`。

### i18n 文案、目录与占位符

- **i18n 多格式目录与语言热切换**: `i18n.py` 按语言探测 gettext `.mo`→`<lang>.json`→`<lang>.yaml`（zh_CN 用 .mo、en_US/en_GB 用 .json、zh_TW 用 .yaml）；四目录键集合必须一致。修改 zh_CN.po 后必须 `python scripts/compile_po.py` 重编 .mo（测试强制字节级同步）。新增翻译串提取用 `python scripts/extract_i18n_strings.py`。**前端另行维护内嵌目录**：`web/app.js` 自带四套 UI 字串，**新增/修改翻译串须同步五处**（四份 i18n 目录+`web/app.js`），改完必跑 `node --check web/app.js`+`node --test tests/frontend/`。
- **形参日志必须走 `i18n.tr(模板, **kw)`，禁止再用 f-string**: f-string 在查目录前完成插值，带占位符的 msgid 永远匹配不上、翻译静默退化为原文。三条硬约束：① 模板必须是字面量常量串，占位符只能是纯标识符；② 格式/转换符由调用方预先求值后作实参传入；③ 占位符名由表达式确定性派生（`type(e).__name__`→`type_name` 等），改模板名必须同步改 kwarg 名。回归锁：`tests/test_i18n_migration.py`。`main.py` 的 `import i18n` 必须置于模块级 banner 打印**之前**。
- **测试必须冻结翻译为恒等映射**: `tests/conftest.py::_pin_identity_translation` 把 `i18n._tr` 固定为 `lambda t: t`，断言与语言解耦；不可删除该 fixture（翻译机制本身由 `tests/test_i18n_tr.py`/`test_web_api.py` 覆盖）。
- **i18n 提取器扫不到「彩色输出 / 对话框」两条路径，新增文案必须手工同步四目录**: `color_obj.print_colored(...)` 与 `messagebox.show*` 不在扫描范围——新增/修改文案必须手工补进 zh_CN.po/en_US.json/en_GB.json/zh_TW.yaml 并重编 .mo，否则 `extract_i18n_strings.py` 报「0 缺失」假绿。
- **`_2` 后缀占位符只在代码真传 `xxx_2=` 时才合法**: 目录里 `{message_2}`/`{msg_2}` 等来自调用方显式传入同名关键字（如 `msg_push.py` 传 `message=`/`msg=`/`errmsg=`）；历史上曾把只出现一次的占位符误写 `*_2` 致繁体 KeyError。新增带重复占位符的模板须确认调用方确实传了 `_2` 实参。
- **四语目录条目数权威口径是 `.mo` 头部 N（含头部空 msgid，故 N == 键数+1），往文档写条数必须同时给「取数命令+读数时刻+两种口径」并实测，不要推算**: 读取 `struct.unpack('<6I', open(mo,'rb').read()[:24])[2]`；与 `scripts/compile_po.py --check` 自报数一致，否则 .po/.mo 不同步。孤儿 msgid 不会变红需人工核对（删源码功能时要手工回查目录侧）。
- **形参日志门禁判据是「首参子树」不是「首参本身」（MID-68）**: `tests/test_i18n_migration.py` 不变量① 判据收紧为「首参子树中存在含 FormattedValue 的 JoinedStr」，唯一收敛处是 `tr()` 调用（只递归模板位）。`extract_i18n_strings.py` 仍只认常量串/单个 f-string 首参，看不见 `BinOp` 拼接——故新增形参日志一律写 `i18n.tr(常量模板, **kw)` 而非拼接式实参。
- **i18n 三件套门禁必须在 UTF-8 环境跑（MID-63 同源）**: `compile_po.py --check`/`extract_i18n_strings.py`/`tests/test_i18n*.py` 一律带 `PYTHONUTF8=1`，细则见「格式化命令」。

### 配置键名、布尔口径与 SSL 验证

- **「禁用SSL证书验证的平台」仅在需要证书校验时生效（FFmpeg 9.0 语义）**: `http_config.get_effective_ssl_verify` 的平台覆盖仅在全局 `ssl_verify=True`（http 录制模式）参与读取；https 录制模式全局已禁用、平台覆盖无意义。`main.py` 启动时经 `_sync_ssl_disable_platforms` 把证书异常平台（虎牙/B站，`SSL_DISABLE_REQUIRED_PLATFORMS`）追加至配置键并写回——只追加绝不移除用户手填项。`update_config_line` 键匹配大小写不敏感，改回精确匹配会导致代码常量（大写）与配置文件行（小写）无法互找。
- **config.ini 键名禁止含 `=`/`:` 等 configparser 分隔符**: 含 `=` 时读取侧在首个分隔符处截断、写回侧 Python 3.14+ `configparser.write()` 抛 `InvalidWriteError`（3.13 静默写成功，勿把仅 3.13 失败、3.14 通过的用例误判为回归）。括号提示可写 `(0为不限制)` 无分隔符形式。`read_config_value` 的缺键兜底已硬化为内存 StringIO 序列化成功才落盘+捕获 `(OSError, configparser.Error)` 降级，但键名本身须避开分隔符。
- **布尔配置写入 `true/false` 曾被静默判成兜底值**（P0）: 旧实现 `options.get(read_config_value(...), 兜底)` 值不在字典里时静默返回硬编码兜底，导致系列配置生效值漂移。审计须比对「生效值」而非字符串（逐键算 `解析(现值,默认)` 与 `解析(旧值,默认)`）。现已统一到 `src/config_bool.py`（见「关键约定」第 9 条）。回归锁：`tests/test_config_bool.py`/`tests/frontend/test_quality_ui.mjs`。
- **`config.ini` 键集审计三个陷阱**: ① `read_config_value` 的**键是第 3 个参数**——按首参字面量写正则会扫出 0 条；② `config/config.ini` **带 UTF-8 BOM**，审计脚本须用 `encoding="utf-8-sig"`；③ 扫出「缺失键」里有 3 个是有意不写回的旧键迁移读取（`是否强制启用https录制`/`是否禁用SSL证书验证(是/否)`/`虎牙是否禁用SSL证书验证(是/否)`），由 `config.has_option(...)` 守卫，不是缺口不要补。

### 凭据与敏感配置脱敏

- **敏感配置判定必须「节白名单 + 键名正则」双重**（src/web_config.py/web/app.js）: 仅按节名会漏掉 `[推送配置]` 内的 `tgapi令牌`/`发件人密码(授权码)`/`pushplus推送token` 及各平台节内 `popkontv_token` 等独立凭据。`expiry|timeout|有效期|过期` 反向例外放行数值型运维参数。前端 `saveConfig` 跳过 `'***'` 掩码的约定是写入侧唯一防线不可移除。写日志 URL/代理一律经 `utils.mask_credentials()`（logs 会轮转保留多份，凭据等于长期落盘）。

### 类型检查、注释与静态门禁

- **PEP 758 `except A, B:` 在 3.14 合法，语法/编译检查一律用项目 venv 的 Python 3.14**: 用 3.13 做 `compileall`/`py_compile` 会把全树误报 `SyntaxError: multiple exception types must be parenthesized`。新增/修改写无括号，但不要把现有无括号写法修回加括号（与约定相反）。
- **protoc 生成模块需手写 `.pyi` 存根**（src/proto/douyin_pb2.py）: 消息类经动态注入，mypy 看不到 `PushFrame`/`Response`/`ChatMessage` 属性而报 `attr-defined`。已建 `src/proto/douyin_pb2.pyi` 声明 3 个消息类及字段（继承 `google.protobuf.message.Message`）。新增字段引用必须同步补存根。
- **平台专属符号必须 `sys.platform` 字面量门控**（mypy 跨平台 CI 检查）: `ctypes.WinDLL`/`windll` 仅 Windows typeshed 有，CI 的 mypy 跑在 linux runner。修复模式：函数体首行早返回 `if sys.platform != "win32": return`；注解需引用平台符号时降级为 `object | None`（禁 `sys.platform` 条件类型别名）。**禁用 `# type: ignore`**（Linux 必要、Windows 多余，basedpyright 报 `reportUnnecessaryTypeIgnoreComment`）。验证双跑且均不带路径：`mypy`+`mypy --platform linux`。门控条件写反静态检查发现不了，须运行时用例锁定（`tests/test_i18n.py::TestWindowsUiLanguagePlatformGate`）。
- **三参 `getattr` 不做字面量名解析，模块级已声明属性一律直接访问**（mypy Any 泄漏）: `getattr(obj, "attr", default)` 返回 `Any | None`，`warn_return_any` 下报 `no-any-return` 且后续属性链类型检查全部失效。凡目标属性有模块级声明（如 `main.scheduler: ConcurrencyScheduler | None`）直接 `main.scheduler` 访问；确需容错用 `cast`。
- **protobuf 升级必须先同代重新生成再放开版本上限**（F-14）: `douyin_pb2.py` 为 protoc 25.x 产物、标注 DO NOT EDIT，本环境无 protoc。**禁止手改生成文件**；`protobuf>=6.31.1,<8` 上限不可删。回归锁：`tests/test_proto_runtime_compat.py`。
- **`main.py` 内引用模块全局量不得加 `main.` 前缀**: 本文件模块级 `main` 是入口函数而非模块对象，`main.recording_enabled` 运行期必抛 `AttributeError`。
- **PEP 758 的 `except A, B:` 不支持 `as` 绑定**: 有异常对象时必须 `except (A, B) as e:`（语法强制），与「不要为兼容 <3.14 加括号」不冲突（前者风格、此处语法）。批量替换时务必 grep `as` 用法。
- **删除模块级函数/常量前必须 grep 全部调用点**: `main.py` 曾删 `_ffmpeg_reported_output_failure()` 但留调用点，mypy/basedpyright/tests 三面同时转红，且因调用点在 `and` 右侧短路、在 Linux CI 上恰不炸（典型「本地红、CI 绿」）。执行「删除符号」改动：① grep 收全调用点再删；② 删完立刻跑 mypy+完整 pytest；③ 用例输出路径必须用 `tempfile.gettempdir()`（旧 `"/tmp/out.ts"` 在 Windows 父目录不存在，两端语义相反）。`check_annotations.py` 已常驻符号可达性检查兜底。
- **测试桩转发函数里 `*args`/`**kwargs` 一律注解 `Any`（写成 `object` 只有 basedpyright 报错）**: `monkeypatch.setattr(Path, "unlink", stub)` 类转发桩若 `*a: object, **k: object` 转发，basedpyright 会按声明类型逐个匹配形参报 `reportArgumentType`；mypy 不报故只跑 mypy 会漏。统一 `*args: Any, **kwargs: Any`（必要时 `cast` 收窄返回值）。
- **CI 的 typecheck job 必须装 pytest，否则 `tests/` 的类型检查是半盲的**（2026-09-26 修，含历史注）: 该 job 曾只装 `requirements.txt + mypy`，`tests/` 里的 `pytest.*` 全按 `Any` 检查——fixture / `MonkeyPatch` 免检不说，连 `pytest.fail()` 的 `NoReturn` 都丢失，mypy 会把「声明了非 `None` 返回类型、却以 `pytest.fail()` 收尾」的辅助函数判成 `[return]`（`tests/test_proto_runtime_compat.py::_declared_protobuf_specifier` 2026-09-26 实测：只在 CI 红、本机装了 pytest 恒绿，无法本地复现）。[历史注] 现已随 consts 补装固定版本 `pytest==9.1.1`（与 black / isort / mypy 同口径，防「代码未改动却 CI 变红」）。约定仍成立：辅助函数走不到终点时统一 `raise AssertionError(...)`（天然 `NoReturn`，不依赖 pytest 是否可见），**不要**依赖 `pytest.fail()` 的返回类型，**也不要**在其后补不可达语句（basedpyright 报 `reportUnreachable`）。复现「pytest 不可见」的老环境：`mypy --no-site-packages`（该模式下 `src/` 多出的 5 条 `no-any-return` 属过度剥离噪声，非真实问题）。

### 热路径性能（数据结构 / 正则）

- **`main.py` 主循环去重容器必须为 `set`，禁止退化成 list/O(N²)**: `url_comments`/`line_list`/`url_line_list` 均 `set` 做成员检测，移除用 `.discard()` 而非列表重建，`text_no_repeat_url` 用 `dict.fromkeys` 保序去重。80+ 房间时 list 实现退化 O(N²)。`need_update_line_list` 仍 `list`（要保序 append+pop）。
- **高频正则提模块级常量、按 key 缓存，禁止函数内 `re.compile`**: `_EMOJI_PATTERN`/`_URL_PATTERN`/`_BANDWIDTH_PATTERN`/`_DOUYIN_HEVC_FLV_PATTERN` 提模块级编译；`update_config_line` 按 key 编译的正经 `functools.lru_cache(maxsize=128)` 缓存。

### 构建产物、依赖与运行时基线

- **Node 24 / FFmpeg 9.0 兼容基线**: 9.0 移除的 CLI 参数禁止引入。
- **近期性能优化与修复完整变更记录见 `CODE_WIKI.md`/`CODE_WIKI_EN.md` 更新日志**: 本文件只沉淀可回归硬约定。
- **`StopRecording.vbs` 必须保存为 UTF-16 LE（带 BOM）**: 由 wscript/cscript 消费，按系统 ANSI 解释 `.vbs`，UTF-8 保存会让中文乱码（源文件统一 UTF-8 约定不适用于该文件）。进程匹配现为三层：① 程序专属 exe 按映像名命中；② python 须命令行含入口脚本或 pip 启动器名 `douyin-recorder`（刻意不按项目目录匹配，避免误杀编辑器工具进程）；③ ffmpeg 须「父进程为已识别录制主进程」或「路径/命令行锚定程序目录」。结束顺序先录制主进程（`taskkill /f /t /pid` 连带子进程树）后残留 ffmpeg——原「先杀 ffmpeg→等 10s→再杀主进程」存在主进程重建 ffmpeg 竞态，且强杀不走 atexit 不执行日志归档（本脚本仅作最后手段）。
- **包内 ffmpeg 的 PATH 前置在 Apple Silicon 上必须「让位」（W6）**: full 包内置 macOS ffmpeg 是 x86_64 静态构建，已装原生 arm64 用户会被遮蔽强制走 Rosetta。判据收敛到 `src/ffmpeg_install.should_prepend_bundled_ffmpeg_dir()`（唯一事实源，main.py 只保留「重复插入跳过」守卫）。五条判据：`darwin` ∧ `arm64` ∧ 包内目录存在 ∧ 注入前 PATH 快照另有 ffmpeg ∧ 那份 realpath 不在包内目录。三条不可回退：① 探测必须用调用点传进来的 pre-injection PATH 快照（直接读 `os.environ["PATH"]` 会探到自己刚前置的那份）；② 自我遮蔽形态（用户已把包内目录永久写进 PATH）须按 realpath 归一后排除；③ Windows/Linux/Intel Mac 行为逐字不变。`scripts/douyin_live_recorder_standalone.py` 有同名同语义判据（该文件不 import src），改判据必须两处同改、两边注释互相点名，行为等价性由 `tests/test_ffmpeg_path_preference.py::test_twin_agrees_on_every_criterion_combination`（9 格矩阵）锁住。
- **`DouyinLiveRecorder.egg-info` 是构建产物但会长期腐化，改 `pyproject.toml` 后须重建**: `importlib.metadata`/`pip install -e .` 会读它。重建：`python -c "import sys; sys.argv=['setup.py','egg_info','--egg-base','.']; from setuptools import setup; setup()"`。改 `[project].dependencies`/`version`/`packages`/`package-data` 后应重跑。
- **依赖对账必须先剥 `requirements.txt` 行内注释**: 注释紧贴版本号不带空格（如 `brotli>=1.2.0#b站弹幕解压`），整行比对会全量误报不一致；比对前 `line.split("#", 1)[0].strip()` 再归一化。egg-info 里 `protobuf` 规格被 setuptools 规范化成 `<8,>=6.31.1`（与 pyproject `>=6.31.1,<8` 顺序不同不是差异），应按「包名+规格集合」比对。
- **排除目录归一化必须先剥 `**/` 再剥 `*/`**: basedpyright 用 `**/downloads`、coverage 用 `*/downloads/*`，若先剥 `*/` 会把 `**/downloads` 切成 `*downloads` 致「basedpyright 缺 7 个目录」假结论。
- **发布链运行时二进制必须 fail-closed 钉定（SEV-10）**: full 版把 ffmpeg+node 打进对外分发 zip，以子进程执行，危害半径是所有下载用户。三层防线缺一不可：① `build_exe.py` 的 `_PINNED_RUNTIME_SHA256`（按 `<os>-<arch>` 分列，槽位 ffmpeg/node），「已钉定」唯一判据是 `_is_pinned()` 形状（64 位小写十六进制），占位/空串/截断一律未钉定，**不得为让 CI 绿回填本地自算哈希**（那是固化「构建机已中毒」）；② `--require-pinned`（CI 因 `GITHUB_ACTIONS=true` 自动开），缺钉定即在下载前 `SystemExit`（该异常继承 BaseException 吞不掉）；`slot` 已改为必填关键字参数（漏传会静默降级为无校验下载）；③ `scripts/check_runtime_pins.py`（--strict 由 build-release.yml prepare job 执行并 --emit-env 透传 `DLR_RUNTIME_SHA256`）。表为空/缺平台/缺槽位一律 rc=2。「算满足」有两档，唯一口径是 `build_exe._slot_is_gated()`（`check_runtime_pins.py` 不得自判）：64 位十六进制官方哈希，或**官方签名档**（取值 = `OFFICIAL_SIGNATURE_PIN` 标记，且该槽在 `_RUNTIME_GPG_SIGNATURES` 确有登记、指纹为 40 位十六进制；**标记本身绝不构成放行**，与第 4 类同一道防线）。钉定进度（2026-09-26 复核）：node×5 槽 + windows-x64/linux-x64/linux-arm64 的 ffmpeg 均已按官方公布值钉定（Linux 取值来自 `api.github.com` 的 `assets[].digest`）；macOS 两槽 ffmpeg 走官方签名档——evermeet 不公布哈希，**验签即该槽唯一判据**。[历史注] 此前 macOS/Linux 四个 ffmpeg 槽位刻意保持占位，因当时所选上游确实不公布 SHA256。node 下载版本按最新 LTS 动态解析，上游发新 LTS 即钉定失效拦下发布——刻意人工闸口，不得改自动取哈希。
- **三类「钉定/校验」互不覆盖，不得用其一冒充其二（SEV-10/MID-62 边界）**: ① 发布期运行时二进制 → `build_exe._PINNED_RUNTIME_SHA256`+`--require-pinned`，上游公布 detached 签名的槽位钉定后还须过官方 GPG 验签（带外钉完整 40 位主钥指纹，VALIDSIG 报子钥指纹逐字比主钥会假红）；**官方签名档**属 ① 内部的第二种满足方式、不是新增一个面——该槽没有公布哈希时验签即**唯一判据**，故验签调用点**不得**留在「哈希已过」的分支里（否则那一档在真实构建路径上永不可达，即 SEV-2221；回归锁 `tests/test_build_exe.py::test_signature_mode_slot_downloads_and_actually_verifies`）；② 运行期自动安装 ffmpeg/node → `src/ffmpeg_install.py`/`src/node_install.py` 的 ToFU 基线，首次安装先取上游官方公布哈希文档验（TOFU 退化为取不到时的显式降级并记 warning，不得反过来）；Windows 运行期只有 gyan.dev 一条自动路径，蓝奏云兜底源已整体删除；③ 签名脚本层 `src/javascript/*.js` 与远程 `mgprtcl.wasm` → `src/utils.py::_JS_SHA256_EXPECTED` 只钉得住胶水脚本、钉不住 wasm。任何新增「远程获取并在子进程/本进程内执行的代码」都必须落进上述三类之一并注明是哪类。第 4 类「源码可复现构建」`SOURCE_BUILD_PROVENANCE` 仅用于 CI 自源码构建、上游本无公布值的产物（声明该类槽位不得走下载路径），不是第四个「面」。
- **发布面 ffmpeg 来源增删必须同批改三处（2026-09-26，随 Linux 换源 BtbN 落地）**: ① `build_exe._FFMPEG_DOWNLOAD_URLS`（按运行时键一条，与 `_PINNED_RUNTIME_SHA256` 键同构，`tests/test_build_exe.py` 的双向覆盖锁会红）；② 该键的钉定取值或签名档标记；③ `tests/test_build_exe.py::_ALLOWED_HOSTS` 主机白名单——退役的主机要**移出**清单，留着等于给已不用的来源保留通行证。归档内部层级一律经 `_extract_linux_ffmpeg_binaries()` 递归按名取件，**不得**写死 `bin/` 或平铺（BtbN 带 `bin/`、johnvansickle 平铺；写死另一种会「解包成功但一件没拷」，缺件必须 `SystemExit` 而非 `return False`，否则又落回「一行 warning + 出包成功」）。该函数不读 `sys.platform`，故两种布局的用例在 Windows 开发机与 Linux CI 上都真实执行。换源对 `--dual` Linux full 包体积影响极大（BtbN 150,998,508 B vs johnvansickle 41,888,096 B），体积结论只以 `scripts/report_bundle_size.py` 实跑为准——本机无 Linux 且 `github.com` 直链被重置，尚未实测，交回 CI 首跑。
- **`Dockerfile` 的 `ARG` 必须声明在使用它的指令之前，且门禁要断言行序（MIN-14）**: `LABEL version="${APP_VERSION}"` 写在 `ARG APP_VERSION` 之前会固化空串且构建期不报错。现 `check_version.py` 另断言「`ARG APP_VERSION` 声明行 < 使用点所在指令起始行」（多行续写须回溯指令头、跳过注释行）。新增 ARG/ENV 消费点同理。
- **`scripts/check_coverage.py` 无数据即 rc=2 硬失败，不得退回 WARN（MIN-19）**: 「数据文件不存在」「JSON 读不出」「files 为空」三类都必须走 rc=2 并打印 `pytest --cov=src` 下一步命令（与「模块查不到按失败处理」同族防线，不可互替）。CI test job 顺序固定 `pytest --cov=src` → `check_coverage.py`。
- **不可信输入不得跑浮动 ref 的第三方动作（MIN-17）**: `issue-translator.yml` 触发源是任意外部贡献者正文，已降级为仅 `workflow_dispatch`+降权。不得凭记忆填 SHA、不得为恢复便利加回触发器；其余第三方非认证动作（`trivy-action` 已 SHA 钉定等）按同判据区分。
- **`docker-compose.yaml` 不得保留 `:latest` 拉取回退（MIN-18）**: 锚点内已设 `pull_policy: build`，直接 `up` 就地构建而非拉 registry 同名 `:latest`。

### 装饰器与平台兜底契约

- **装饰器与 `def` 之间的注释会让装饰器绑到下一个 `def`**: Python 允许 `@decorator` 与 `def` 间夹注释行，会把兜底套在返回 `str` 的同步辅助函数上而目标平台入口裸奔无兜底。约定：`@decorator` 必须紧贴 `def`，说明注释写在装饰器**上方**。排查 `grep -A3 '^@trace_error' src/spider.py`。
- **平台解析函数返回契约必须匹配兜底装饰器**: `trace_error_decorator` 失败时回 `{"is_live": False}` 只适用于返回 dict 的函数；返回 str/tuple/None 的必须用 `trace_error_decorator_or_none`（回 None），否则调用方解包抛 ValueError 被自己装饰器二次吞没。调用点须显式判空再解包，新增平台先看返回注解再选装饰器。
- **`_loads_dict` 与 `_safe_loads` 的分工**: `_loads_dict` 内部复用 `_safe_loads`——平台返回 HTML（WAF/302/Cloudflare/截断 JSON）时回 `{}` 并记 warning，**不再抛 JSONDecodeError**（约 40 处调用任一抛错都会被兜底装饰器吞成「未开播」）。`tests/test_spider.py::TestLoadsDict::test_invalid_json` 断言返回 `{}` 不要改回 `pytest.raises`。
- **spider.py 平台解析一律走 `_loads_dict`+`_dig/_dig_str/_list`，裸 `json.loads` 由棘轮锁住不得回升（MID-48）**: 剩余唯一 1 处是 `get_twitchtv_room_info`（GQL 返回数组）。判据 `tests/test_spider_hardening.py::BARE_JSON_LOADS_CEILING = 1`（只降不升）+ 零裸 loads AST 扫描。配套：① 取不到字段不得静默变空（数值型字段走保留数值的 `_dig`+cast）；② 凭据不入日志（AID/BNO/visitor_st 等只按原值取用，归因日志只带 code/msg）；③ 未开播/已下播每 120s 一轮正常轮次刻意保持静默。
- **兜底装饰器失败语义影响熔断样本**: 补上装饰器后异常不再穿透到 main.py 通用 except；反之移除装饰器会使该平台瞬时故障计入失败样本、达阈值可能把房间地址自动注释掉。

### Web / GUI 面板与接口层

- **GUI/WEB 画质切换写回 `URL_config.ini` 后必须同步「编辑器快照」与「显示源」**: ① 反查表 `_anchor_url_map` 键是纯主播名，画质菜单传带 `序号N ` 前缀显示名，查表前必须 `re.sub(r"^序号\d+\s+", "", anchor_name)` 剥离；② 写回后必须调 `_load_config()` 同步 `config_text`（否则编辑器持旧快照、用户保存覆盖刚写的画质段）；③ 画质监控表格「设置画质」列必须以配置文件为准（`_anchor_quality_map`），不能取子进程日志值（切换不重启子进程、日志恒为旧值）。WEB 端 `PUT /api/rooms/quality` 与 GUI 共用 `src/web_config.py::update_room_quality`（保留 `#` 注释前缀、os.replace 原子写、换行注入 ValueError），两端改一处即同步。档位白名单只允许 `BUILTIN_QUALITIES`。回归锁：`tests/test_web_config.py::TestUpdateRoomQuality`+`tests/test_web_api.py::TestRoomQualityApi`+`tests/frontend/test_quality_ui.mjs`。
- **Web 面板「直播间列表」表格必须维持 `table-layout: fixed`**（`web/style.css` 末尾段）: 窄视口下默认 auto 布局 6 列 min-content 溢出。修复后按表头定列宽（画质 128/名称 150/启用 72/录制中 72/操作 76，地址列吃剩余宽），地址/名称 `td` 单行省略，≤768px 走 `min-width:640px + .panel overflow-x:auto`。约束：改回 auto 布局或删省略号会让错位回归；新增列必须补对应 `th:nth-child(n)` 定宽；该段作用域保持 `#rooms-view`，勿扩大到其它三张表。

### 测试质量与审查协作流程

- **测试不得自实现被测逻辑（假绿）**: 曾存在测试里重新实现锁/凭证缓存再断言自实现——删掉 `src/` 对应实现仍全绿等于没覆盖。判据「**删掉生产实现就会失败**」：只允许打桩网络层与时间常量，去重/限流/锁逻辑走真实代码。`tests/test_concurrency_rate_limit.py` 已重写。另：不得 `monkeypatch.setattr(main.time, "sleep", ...)`（`main.time` 是 stdlib 时间模块本体，会替换全进程 sleep，应浅拷贝成 `SimpleNamespace` 覆盖单属性）；覆盖率门禁「模块查不到」按失败处理（非告警）。
- **探测子进程输出一律按字节比较，且这类用例必须能单文件独立运行**: 凡读子进程输出做判定的探测不得用 `text=True`/`encoding=`（Windows `tasklist`/`taskkill` 按控制台码页发本地化消息，UTF-8 模式下 reader 线程解码即抛 `UnicodeDecodeError`→`TypeError`+违背 0 警告）。判据写成字节包含（`str(pid).encode() in probe.stdout`）与码页/语言解耦。`main.py` 导入期 `SetConsoleOutputCP(65001)` 会把整个 pytest 进程控制台码页切 UTF-8，只要同会话有用例先 import main，GBK 分支永不显现→「全量绿、单文件跑红」。故任何驱动子进程并断言其输出/进程状态的测试文件必须保证 `pytest tests/<该文件>` 单独运行全绿且 0 警告。
- **本机全量 pytest 偶发段错误（exit 139）**: 属环境噪声，不要据此认定代码回归。
- **平台专属分支的测试不得靠 `skipif` 让 CI 跳过（2026-09-26 CI 实测定稿）**: CI 全部 job 跑在 ubuntu，而 Windows 专属分支（如 `src/ffmpeg_proc.py` 的「向 stdin 写 `q` 再 close」）若按 `os.name`/`sys.platform` skip，相关回归锁会在 CI 上**静默消失**——与 MID-2264「skipped 与 passed 在汇总里不可区分」同一风险。做法：把平台判定抽成模块级常量（如 `_QUIT_VIA_STDIN = os.name == "nt"`），测试用 `monkeypatch.setattr(module, "_QUIT_VIA_STDIN", True)` 强制走进该分支，让 Windows 路径在 Linux CI 上真实执行。同理，**门禁工具（black / isort / mypy）必须装进 test job**：`tests/test_run_gates.py` 与 `tests/test_regression_2026_09_22_gates.py` 有两条锁真起子进程调用它们（复现 isort 的 `Unable to parse file` 走 UserWarning、rc 仍为 0；验证裸 console-script 不在 PATH 时 `python -m` 兜底不误报 rc=3），缺装即 `No module named isort` → rc=1 → 红。版本取 setup job 的 `black_version` / `isort_version` / `mypy_version` 常量，与 static / typecheck 两 job 同值。
- **并行分组代码审查分工口径**: 子任务 prompt 必须写明本项目刻意约定白名单，避免子代理误报风格为问题。
