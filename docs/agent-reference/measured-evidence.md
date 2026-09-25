# 实测数据与证据明细（自 AGENTS.md「已知坑」外迁的纯参考段）

> 2026-09-20 自 [`AGENTS.md`](../../AGENTS.md)「已知坑（避免回归）」外迁。
> **外迁判据**：只搬「一次性实测读数 / 采样表 / 提速倍数口径」这类参考证据——本文件不含任何祈使式约定；
> 「必须怎样、不得怎样」的约束全部留在根文件。根文件仍是长期约定的唯一事实源，本文件只是其明细，不另立版本。
> 每条下方的小标题即根文件里指向它的链接锚点，改名须同步两侧。

## 探针客户端复用作用域

实测（本地 HTTP/1.1，60 次）：仅构造+关闭 Client **6.7 ms**、新建 Client+单次探针 15.9 ms、复用 Client+单次探针 0.77 ms，故「每轮一支」已拿到大部分收益。**并发连接峰值实测（4 条同 host 候选、每条 HEAD+Range-GET）**：原实现 4 条连接 / 峰值 1 / 70.88 ms，当前 P1 **1 条连接 / 峰值 1 / 12.78 ms**——候选是串行校验的，复用不会抬高瞬时连接数，反而净减少新建连接数；据此「P1 加重虎牙连接预算消耗」的疑虑已证伪。

## 禁止关掉探针客户端keepalive

另注意口径：原实现的 `with httpx.Client(...)` 内 HEAD 与 Range-GET **已经**复用同一条连接（每候选 1 条连接，不是每请求 1 条），故复用的真实提速约 **5.5×**（70.88→12.78 ms），而非「每请求新建」基准给出的 36× 上界。

实测 `httpx.Limits(max_keepalive_connections=0)` 会让连接数从 1 涨到 **8**、耗时从 12.78 ms 退回 **72.99 ms**（等价于每次请求新建连接）。

## 虎牙选档ratio

实测 huya.com/chuhe（bitRate=30000）七档 ffmpeg 采样验证：原画 2560x1440\@60 / 蓝光30M\~8M 均 1920x1080\@60 / 蓝光4M 1920x1080\@30 / 超清 1280x720\@30 / 流畅 800x450\@24。

## 斗鱼本地重试链

实测 douyu.com/3168536：请求 rate=8200 被钳到下发 rate=4（蓝光4M `_4000.flv`），请求 rate=1 被钳到 rate=2。

## isort 静默跳文件

2026-09-20 实测（本机 Windows / GBK 语言环境，isort 9.0.1，命令 `python -m isort --check-only --profile black --line-length 120 .`）：
不带 `PYTHONUTF8` 时 **rc=0**，stderr 同时出现 **17 条** `UserWarning: Unable to parse file …: 'gbk' codec can't encode character`，
被跳过的文件为 `main.py`、`gui.py`、`web.py`、`build_exe.py`、`src/spider.py`、`src/stream_select.py`、
`src/config_io.py`、`src/notify.py`、`src/async_http.py`、`scripts/douyin_live_recorder_standalone.py`、
`scripts/smoke_test.py` 与 `tests/` 下 6 个（`test_config_bool.py`、`test_config_io_readonly.py`、
`test_http_config.py`、`test_i18n_migration.py`、`test_record_container.py`、`test_web_api.py`）。
抛错点在 `isort/core.py:479` 的 **encode**（不是 decode）。同一命令加 `PYTHONUTF8=1` 后
**0 条**该告警——门禁覆盖面恢复为全量：本轮仓库内自有 .py 共 **131** 个（根 6 + src 43 +
scripts 11 + tests 71，不含 `typings/` 的 14 个 `.pyi` 存根），其中 17 个此前处于「未检查」状态。
（报告 MID-63 记为 16 个 / 5 个测试文件；本轮实测集合为 17 个 / 6 个测试文件，另含
`src/async_http.py` 与 `scripts/` 下 2 个。计数随并行改动漂移，以 `grep -c "Unable to parse file"` 现测为准。）

2026-09-21 复测（同一台 Windows / `locale.getpreferredencoding(False) == cp936`，isort 9.0.1，
门禁参数 `--check-only --profile black --line-length 120 .`）：不带 `PYTHONUTF8` 时 **rc=0**、
stderr **18 条** `Unable to parse file`；带 `PYTHONUTF8=1` 时 **rc=0、stderr 完全为空（0 条）**。
较 09-20 基线多出的 1 个是 `src/collector.py`（其间并行改动新增的中文注释文件）。
逐文件清单：`build_exe.py`、`gui.py`、`main.py`、`web.py`、
`src/async_http.py`、`src/collector.py`、`src/config_io.py`、`src/notify.py`、`src/spider.py`、
`src/stream_select.py`、`scripts/douyin_live_recorder_standalone.py`、`scripts/smoke_test.py`、
`tests/test_config_bool.py`、`tests/test_config_io_readonly.py`、`tests/test_http_config.py`、
`tests/test_i18n_migration.py`、`tests/test_record_container.py`、`tests/test_web_api.py`。
同轮附带发现：`scripts/run_gates.py` 自身在 cp936 下会因转发 black 成功行的 `✨` 抛
`UnicodeEncodeError` 而崩溃（rc=1、无门禁结论），已由其 `ensure_utf8_streams()` 修复——
即 `PYTHONUTF8=1` 必须同时覆盖**子进程**与**转发输出的父进程**，只设一侧仍会失效。

## pip-audit 本地审计读数

2026-09-21 于 Windows 10 / 中文 locale（cp936）本地实测，工具版本 `pip-audit 2.10.1`，
装在仓库外的临时 venv 中（项目 venv 未被写入任何包，`requirements.txt` / `pyproject` 亦未新增条目）。

| 调用形态 | 不带 `PYTHONUTF8` | 带 `PYTHONUTF8=1` |
| --- | --- | --- |
| `-r requirements.txt`（解析全部传递依赖） | `UnicodeDecodeError: 'gbk' codec can't decode byte 0xa1 in position 112`，rc=1 | `No known vulnerabilities found`，rc=0 |
| `-r requirements.txt --no-deps`（只看声明的 21 条下限） | 同上崩溃 | 无漏洞，rc=0 |
| `--path .venv/Lib/site-packages`（项目实际安装态，只读） | 不适用（不经清单解析） | 无漏洞，rc=0 |

崩溃点是 `pip_requirements_parser.auto_decode()` → `locale.getpreferredencoding(False)`，
即解码发生在**读清单文件**阶段、早于任何 OSV 查询，故报错形态与「发现漏洞」毫无关系。
本轮三种形态的结论一致：现有下限（`starlette>=1.3.1`、`urllib3>=2.7.0`、`requests>=2.34.2`、
`python-multipart>=0.0.32`、`protobuf>=6.33.5,<8`）对 2026-09-21 的 OSV 数据均为干净集合。
注：`--venv` 不是 2.10.1 的合法参数（实测 `unrecognized arguments`），审计已安装环境走 `--path`。

## Node 24 / FFmpeg 9.0 版本基线详情

Node 运行时以 24.19.0 实测为准（全部 JS 签名脚本 + migu.js 通过），Dockerfile 随之安装 Node 24 LTS。FFmpeg 以 9.0 为基线，9.0 移除的 CLI 参数清单：`-vsync` / `-top` / `-qphist` / `-filter_complex_script` / `-adrift_threshold`。录制命令中的冗余 `-v verbose` 已删除（被 `-loglevel error` 覆盖）。

## egg-info 腐化实例

2026-09-18 对账时发现 `DouyinLiveRecorder.egg-info` 仍停留在 4.1.0 快照：`PKG-INFO` 版本 4.1.0（pyproject 已 4.3.0）、`requires.txt` 仍是 `websockets>=12.0` 与无上限的 `protobuf>=6.31.1`、`SOURCES.txt` 缺 30+ 文件。

## Dockerfile ARG 旧门禁失效形态

旧 `scripts/check_version.py` 只正则匹配「有没有 `version="${APP_VERSION}"` 这个字面」，顺序颠倒照样判 DYNAMIC——即门禁对 ARG 声明在使用点之后的失效永久失明。

## macOS / Linux ffmpeg 上游不公布 SHA256 实测

2026-09-22 实测三家上游不公布 SHA256：evermeet 只提供「追加 `/sig` 取 GPG 签名」、johnvansickle 只提供 `*.md5`。按「不得凭本地下载结果填写」的硬约束，宁可让发布链继续红在这 4 个槽位上（这是预期，不是回归）。

## 虎牙 FLV-first 冷启动采样

依据：2026-08-28/29 三轮真机两房间复现——虎牙 HLS 三条 CDN 线路（hs/tx/al）冷启动探针假绿（探针 200/206、ffmpeg 打开即 403，返回码 3436169992），TX/AL 次轮探针也稳定 403；FLV 每轮稳定可用（最长连录 6 分钟）。

## 虎牙探针退避窗口实测

实测虎牙 880214（2026-08-28）：重试 7 轮仅 2 轮侥幸录上，两轮日志中「CDN 探针退避中」告警**一次都没出现**。

## ffmpeg reconnect 事故形态实测

**另一形态（2026-09-11 事故）**：09-10 把这三个选项移到 `-i` 之前时丢失了 `-reconnect_streamed` / `-reconnect_at_eof` 的布尔值 `1`，ffmpeg 把下一个选项名当作值——`Unable to parse "reconnect_streamed" option value "-reconnect_at_eof" as boolean` → Invalid argument，**输入未打开即退出（-22）**，真实录制 100% 复现；而 `-reconnect_delay_max 60` 因带着值幸免。

`ffmpeg -report` 实测特征：连续 `Will reconnect at <size> in N second(s), error=End of file`，1/3/7/15/31s 指数退避、`-reconnect_delay_max 60` 只限单次延迟上限、重连无次数上限、永不放弃。

生产事故形态（2026-09-11 凌晨实测）：抖音/斗鱼房间（HLS 优先选源）仅产出弹幕 SRT、视频零字节、ffmpeg 常驻不退出（`-loglevel error` 下零输出零报错，`check_subprocess` 只看到进程存活）——"只录到字幕没录到视频"即为该故障；虎牙（`_FLV_FIRST_PLATFORMS` + HLS 排除列表）不受影响。**对照实验**：同命令加 `-t 10` 限时，60s 仍不退出且零字节产物；仅去掉该选项后 10s 录制 9MB 正常退出。

## ffmpeg per-file 选项归属实测

上游 ffmpeg 已把该选项从 `(input/output)` 收窄为 **`(output)` 专属**——`doc/ffmpeg.texi` 对照：6.1 / 7.1 / 8.0 / 9.0.2 均标 `(input/output)`、master 标 `(output)`；本机 master 构建 `N-126755-g52f05ac780-20260922` 的 `ffmpeg -h full` 把它列在 **"Advanced per-file options (output-only)"** 段。

A/B 读数（golden 产出的真实参数向量 × 本地 HLS/FLV 源）：选项在 `-i` 前 rc=4294967274 且零字节，在 `-i` 后 rc=0、275420 字节。

## 布尔配置写入 true 或 false 的漂移实测

实测把 `config.ini` 批量改成 `true/false` 后 8 项生效值漂移，其中最严重的是
`是否跳过代理检测 = true` 被判为 `False` → `global_proxy=False` → TikTok/SOOP/PandaTV/WinkTV/
Flextv/PopkonTV/Twitch/LiveMe/Faceit 共 9 个海外平台的解析分支全部走 `else`（只打印「网络异常」、
`port_info` 为空）→ **100% 无法录制**；其余漂移项覆盖保存目录层级（产物落 `downloads/<平台>/` 而非
`<主播>/`）、分段录制关闭、弹幕 SRT 不再产出、https 拉流降级为 http。

## 性能优化与修复变更记录

近期性能优化与修复的完整变更记录见 `CODE_WIKI.md` / `CODE_WIKI_EN.md` 的「更新日志 / Changelog」。2026-08-28/29 的 P1~P5 性能优化（探针客户端复用 / `requests.Session` 线程级复用 / 主循环 set 去重 / 调度器增量计数 / 正则提常量）、探针退避窗口对齐主循环、录制成功清除退避、虎牙 FLV-first、Web 模式 loguru 控制台 sink 重建，均已逐条落地为 AGENTS.md 约定与「录制结果反馈约定」「并发与线程模型」章节。

## 本机全量 pytest 偶发段错误

征兆是进度到 34% 前后（`test_log_archive` / 弹幕监控频段）崩在 `loguru._handler._queued_writer` → `_terminate_file` 的 `os.rename`——Windows 上多测试共享日志文件时轮转改名撞上未关闭句柄（`PermissionError WinError 32`），叠加 `enqueue=True` 的后台 writer 在 teardown 后写已关闭 sink。属环境噪声：单跑 `pytest tests/test_log_archive.py` 稳定 14 passed，跨版本改动前亦出现过。判读结果时若看到 `Segmentation fault`，先重跑并单独跑崩溃点所在文件，不要据此认定代码回归；同时优先清理 `logs/` 与 `.venv/Lib/site-packages/pytest/logs/` 下的残留日志句柄。

## 并行分组代码审查分工口径

2026-09-19 沉淀：把「审查全量源码」拆成 6~7 个模块组并行深读时，必须在每个子任务的 prompt 里写明本项目的刻意约定白名单（`#` 行注释不用 docstring、`except A, B:` 为 PEP 758 风格、line-length 120、四语 i18n、弹幕与视频链路解耦等），否则子代理会把刻意风格大面积误报为问题。同时要求每条结论附 `文件:行号` + 逐字符原文片段（≤12 行）+ 置信度，并在汇总前逐条回源复核严重项——这一步能筛掉「凭常识推测项目存在某问题」的臆测条目（本次实测：子代理给出的 14 项疑似问题经复核确认均不成立，已单列「已核实但不构成问题」章节）。

## 与根文件的分工

- 根文件保留条目的**约束与结论**并就地链接本文件对应小节；本文件只保留**支撑该结论的原始读数**，一字未改。
- 新增同类证据段沿用同一判据：句中不得出现「必须 / 禁止 / 不得 / 须」这类祈使式约束才可外迁。
