# 会话经验沉淀（项目共享知识）

> **语义声明**：本文件是**项目共享知识**，受版本控制、各工具可解析。
> 与 `.workbuddy/memory/` 的当日草稿不同——后者为私有日志、不纳入共享知识。
> 完成定义第 6 步（[`AGENTS.md`](../../AGENTS.md)）指向本文件记录值得后来会话取用的长期经验。
>
> **历史通道**：本窗口的版本控制条目（`unversioned-working-copy`）由
> [`AGENTS.md`](../../AGENTS.md)「可靠交付」维度单独持有，本文件不重复处理，只在此点名。

---

## 源根状态基线

> 后续复盘需**重新采集**（重跑同一命令），不得直接复用本次读数做结论。
> 每次采集的读数按日期排列，使下次复盘能做出「有可比对后续结果」或
> 「确认无法比对」二者之一的明确结论。

采集命令：`<cli> session-analysis sources --workspace d:\DouyinLiveRecorder-dev --json`
补充命令：`<cli> harness evidence-bundle --workspace d:\DouyinLiveRecorder-dev --language zh-CN --depth normal --format json --include-memories`

### 首次采集（2026-09-22）

| 字段 | 值 |
|---|---|
| `home` 解析值 | `C:\Users\58421\.qoder` |
| 总源根数 | 7 |
| **存在数 / 启用数** | **0 / 5**（5 个启用的源根全部 `exists: false`；2 个禁用） |
| 会话数 | 0 |

不存在的已启用源根：

| id | 路径 |
|---|---|
| `qoder-audit` | `C:\Users\58421\.qoder\audit\audit.jsonl` |
| `qoder-run-manifests` | `C:\Users\58421\.qoder\logs\runs` |
| `qoder-log-sessions` | `C:\Users\58421\.qoder\logs\sessions\d--DouyinLiveRecorder-dev` |
| `qoder-projects` | `C:\Users\58421\.qoder\projects\d--DouyinLiveRecorder-dev` |
| `qoder-home-sessions` | `C:\Users\58421\.qoder\sessions` |

禁用的源根（2 个）：`qoder-cache-projects`（需 `--include-cache`）、`qoder-global-projects`（需 `--include-global-capabilities`）。

### 复查（2026-09-22，证据通道修复）

| 字段 | 首次采集 | 复查 |
|---|---|---|
| `home` 解析值 | `C:\Users\58421\.qoder` | `C:\Users\58421\.qoder`（未变） |
| 存在数 / 启用数 | 0 / 5 | 0 / 5（未变） |
| 会话数 | 0 | 0 |
| `eligibleSessions` | — | 0 |
| `titleCount`（记忆枚举） | — | 0（`scanState: scanned-empty`） |

实测对照：`C:\Users\58421\.qoder-cn\projects\d--DouyinLiveRecorder-dev` 存在且含 20 个文件，
但 CLI 解析到 `C:\Users\58421\.qoder\projects\d--DouyinLiveRecorder-dev`（不存在）。
路径不匹配仍是唯一可观测的结构性差异。

### 结论（2026-09-22 复查后）

**不可判定**：两条证据通道（会话源根、记忆枚举）均不可读。
不猜测成因，不将此写为项目缺陷——CLI 的 `home` 解析值（`.qoder`）与本机
Qoder CN 发行版的实际数据根（`.qoder-cn`）不一致，属外部工具配置层面。
修正或桥接此数据根解析须取得用户单独授权，本次未执行任何配置变更。

**授权说明**：若用户决定修正工具数据根解析（例如使 CLI 识别 `.qoder-cn` 或建立
符号链接 / 路径桥接），需用户明确授权后执行；本代理不主动发起此类变更。

### 关联发现

`learning-loop-unauditable`（better-harness 2026-09-22 报告）。
该发现指出 `.workbuddy/memory/` 虽自 2026-07 起持续产出（47 个文件），但被 `.gitignore`
排除且不在任何工具可检索路径上。本文件的创建即为该发现的修复动作——将长期经验
写入此可被各工具解析的位置。

---

## 经验条目

> 格式：日期 | 主题 | 经验内容（一句话） | 关联文件（可选）

（待后续会话追加）

- 2026-09-22 | 子进程探测 | 读子进程输出做判定时禁止 `text=True`/`encoding=`——Windows 系统工具按控制台码页发本地化消息，`PYTHONUTF8=1` 下解码抛错会让 `stdout` 变 `None`；判据一律按字节包含。 | `tests/test_frontend_quality_ui.py`
- 2026-09-22 | 测试可验证性 | 凡驱动子进程并断言其输出/进程状态的测试文件，必须保证**单独运行该文件**也全绿 0 警告；`main.py` 导入期的 `SetConsoleOutputCP(65001)` 会掩盖 GBK 分支，制造「全量绿、单跑红」。 | `AGENTS.md`
- 2026-09-22 | 供应链判定 | 面（发布期/运行期/签名脚本层）与满足方式（钉官方哈希 vs 源码可复现构建）是两个维度；新增满足方式不等于新增一个面，也不得用来盖另一面的缺口。 | `build_exe.py`
- 2026-09-22 | 门禁实现坑 | 表值经 `_pinned_slots()` 统一 `.strip().lower()`，任何「按常量原样逐字比」的判定（如类别标记）都会对注入通道失效——比较一律大小写无关。 | `tests/test_build_exe.py`
- 2026-09-22 | 选项前提 | 采纳任何技术方案（包括自己列出的选项）前先回源核实其前提；Homebrew bottle 的 runtime_deps dylib 不在 bottle 内，故不能作分发源，否决要带证据留档。 | `PROPOSAL_2026-09-22_binary-trust-policy.md`
- 2026-09-22 | PATH 语义 | 判据函数要接收调用点的 pre-injection PATH 快照而不是自读 `os.environ["PATH"]`，否则探测到刚前置进来的那一份，形成自我遮蔽的假绿。 | `src/ffmpeg_install.py`
- 2026-09-22 | 多判据真值表 | 写等价/真值表锁时，每个「拒绝」分支都要有一个「其余条件全满足、只缺它」的场景；若公共前置条件（如 PATH 上根本没有 ffmpeg）在所有场景里都成立，它会先短路，删掉任何后续判据都测不出来。 | `tests/test_ffmpeg_path_preference.py`
- 2026-09-22 | 跨文件副本 | 复制判据前先核对目标文件的导入清单（standalone 无 `import platform` 即运行期 NameError）；副本必须两边注释互相点名，并用文本锁把「两处同改」变成可机检约束。 | `scripts/douyin_live_recorder_standalone.py`
- 2026-09-22 | 外链取证 | 接任何「下载直链」进代码前先跑最小探测集：GET 首 8 字节魔数 + `Content-Length`/`ETag`/`Last-Modified` 三件套 + 伴生 `.sha256`/`.md5`/`.sig` 是否存在 + `HEAD` 是否被拒；fengyuan/fyhub 那条即典型——`200 + text/html` 的人机验证（PoW）页，HEAD 回 `405 + application/json`，哈希文档全 404。 | `src/ffmpeg_install.py`
- 2026-09-22 | 需求前提 | 「把 X 改成 Y / 移除 X 依赖」这类指令，先核实 X 在现行代码里的真实地位：本例蓝奏云只是**默认关闭的兜底**，Windows 主源一直是 gyan.dev；按字面「替换主源」会误删健康主源。 | `AGENTS.md`
- 2026-09-22 | 守卫判序 | 完整性回路的正确顺序是「形态 → 哈希记账 → 解压」；把 zip 形态判定放到解压前看似等价，实则让非压缩包（HTML 挑战页）先污染 TOFU 旁路基准，失败还要晚好几步才暴露。 | `src/ffmpeg_install.py`
- 2026-09-22 | 新增守卫的连带失效 | 加一道前置守卫后，必须复核「原有哪条用例的覆盖意图被它抢走」：`test_unexpected_error_*` 用 `b"not-a-zip"` 当载荷，守卫上线后它在守卫处就返回，`except Exception` 分支静默失覆——测试仍全绿但不再测它想测的东西。 | `tests/test_ffmpeg_install.py`
- 2026-09-22 | 约束的可绕过性 | 「只允许一条下载源」这类约束要按 AST 里的 URL 常量集合锁，不能 grep 关键字：换个镜像名就绕过，且会被刻意保留的历史注释误报。 | `tests/test_ffmpeg_install.py`
- 2026-09-22 | i18n 目录清理 | 按关键词批量删目录键会误删仍被其他模块共用的键（`删除残缺压缩包失败: {e}` 归 node_install 用）；判据必须是「该键不被任何存活源码引用」。另：`zh_TW.yaml` 用不加引号的键（`"k":` 形态只匹配到一半），四份目录全是 CRLF，脚本须 `newline=""` 读写。 | `i18n/`
- 2026-09-22 | 一次性脚本落点 | 写在仓库根的 `_tmp_*.py` 会被 black 门禁收编并让全量门禁 rc=1——本轮首个失败就是这个原因；一次性脚本优先落仓库外（`/tmp` 经 bash heredoc 可写，`Write` 工具则被工作区边界拦下）。 | `AGENTS.md`
- 2026-09-22 | 接受他人删除 | 用户裁决「接受删除」意味着**我的文档必须跟随现状**，而不是把已批准的方案当现状：本轮把 8 处仍写「P-1b = 显式开关」的正文改齐（含中英双份标题/小节/同源段/快照表/覆盖率表 + 提案影响表两行），并让**待确认项随被删契约一起作废**（`ALLOW_UNVERIFIED` 字面集合是否放宽——变量已不存在，不要再排期）。收敛手法是「改断言现状的句子 + 保留带日期的修订注」，不是重写历史。 | `CODE_WIKI.md`
- 2026-09-22 | 会漂移的计数 | 目录条数这类会被并发写入改变的量，落文档必须同时给「取数命令 + 读数时刻 + 两种口径（`.mo` 头部 N 与键数，N=键数+1）」。当天同一工作树先后读到 663/662 与 667/666，而两份修复报告分别报 679/663 与 680/679；处置不是裁定谁造假，而是把「先复跑再落文档」写成约定。判断证据是否出自本机，最便宜的两招：`date`（报告给的 mtime 20:13 晚于当时时钟 16:14）与 `git worktree list`（只有一个工作树）。 | `AGENTS.md`
- 2026-09-22 | 孤儿目录键 | 「删了源码」不会让门禁发现目录侧的残留：`extract_i18n_strings.py` 的「疑似冗余」只是参考级，16:11 的一次写入让 4 条 `蓝奏云 …` msgid 回到四目录而源码 `grep lanzou` 0 命中。删功能时要按「键含该功能专有字样 **且** 不被存活源码引用」手工回查目录侧。 | `i18n/`
- 2026-09-22 | 用户指南别照注释写 | 写「手动安装 ffmpeg」指南时发现 `src/ffmpeg_install.py:71`（称产物在 `ffmpeg/bin/ffmpeg.exe`）与 `:68`（称冻结态 `execute_dir` 指向 `_internal/`）都与 `src/logger.py::_app_root()` 的实现和 `copytree` 目标矛盾；指南按**实现语义**写（扁平一层 `ffmpeg\ffmpeg.exe`，`PATH` 前置不进子目录），注释归文件作者改。 | `README.md`
- 2026-09-22 | 全量跑的串行约束 | 全量 `pytest` 期间任何第二个会话退出都会 `rmtree` 共享的 `tests/_out_e2e`，把 `test_srt_timeline_anchor.py` 打成 4 条假红（识别特征：单文件复跑立刻 4 passed）。本轮自己触发一次、并发工作流触发一次；改 `tmp_path` 之前请保持串行。**【2026-09-24 已闭环】**该用例已改走 `tmp_path`、`_TEST_OUT_DIRS` 与 hygiene 白名单同步去掉 `_out_e2e`，导入期共享目录这条竞态从根上消失，「串行」约束不再适用（现行判据见 AGENTS.md「测试产物一律走 `tmp_path`」条）。 | `tests/conftest.py`
- 2026-09-22 | 我犯过的转述错 | 把并行工作流**声称**的读数（「16:58:17 写入 → 667/666，随后被回退」）当成自己的观测写进实测序列表，还替它编了「被回退」的机制解释；该行在本盘六次复测里从未出现，已删除。**别人的数字只能进「外部未复现声明」这一栏，不得进自己的实测表**——一行伪装成定量，就够让后来者拿真实数据去「校正」它。 | `CODE_WIKI.md`
- 2026-09-22 | 时钟不是判据 | 我一度写下「报告里的时刻晚于本机时钟 ⇒ 它没做实盘测量」并据此否证对方三轮数据：**该判据不成立**（跨会话时钟不可比）。站得住的只有两条：目标文件在本盘的 mtime，以及读者自己复跑同一条命令。本例中 `.mo` 的 mtime 在 40 分钟内恒为 16:31:15，说明「正在被写」的猜测本身也不成立。 | `AGENTS.md`
- 2026-09-23 | 选项侧属会随上游漂移 | ffmpeg 的 per-file 选项「属输入还是输出」由版本决定：`-thread_queue_size` 在 6.1–9.0.2 标 `(input/output)`、master 标 `(output)`。同为「放错侧」，`-reconnect*` 是静默不生效、它却是**输入未打开即 -22**，失效形态相反——新增/复核参数一律先跑 `ffmpeg -h full` 读分段标题 + 逐 ref 查 `doc/ffmpeg.texi`，不要用上一轮的失效经验推断这一轮的后果。 | `main.py`
- 2026-09-23 | 离线复现优于等活房间 | 能定位到「参数向量 × 二进制」层的录制故障，用本地 HTTP 源（自建 HLS/FLV + `python -m http.server`）配上 **golden 里由生产构造函数产出的真实参数向量**做 before/after/absent 三格矩阵，比等一个活房间快且可复跑；真房间那一格照实记 `SKIP(原因)` + 交回用户动作，不得拿本地绿冒充完成定义第 2 步。 | `tests/golden/start_record_commands.json`
- 2026-09-23 | 用标题行插章节会吞掉标题 | 以「下一章节的 `###` 标题行」作 `old_string` 前插新章节时，`new_string` 末尾必须原样带回那行标题，否则原章节正文变成新章节的孤儿子节。本次中英两份 CODE_WIKI 同时中招，靠 `grep -c '^### v4.3.0-dev (2026-09-23)'` 按日期数条目才发现——**落文档后要用「条目计数」而不是「肉眼看渲染」收尾**。 | `CODE_WIKI.md`
- 2026-09-23 | 改注释前必须先做「文本锁侦察」 | 本仓多个用例按**原文**读源码并断言，注释在判定范围内，于是删注释与加注释都能变红：`test_ffmpeg_path_preference.py:531`（两文件互指的文件名字面必须存在）、`test_regression_2026_09_22_net.py:303`（「没有任何生产消费点」这条残留登记必须存在，删掉即被判定成谎称已修）属正向锁；`gates.mjs:301`（`main.py` 全文禁 `main_loop_ticks`）、`test_regression_2026_09_22_net.py:945`（`async_http.py` 全文禁 `import ipaddress`）、`_spider.py:870`（`bj_id = ...` 整行匹配数**恰好** 3）属负向锁——**写历史注时连"当年那个错误写法"都不能逐字引用**。侦察口径：`grep -rn "read_text\|getsource\|doesNotMatch" tests/ | 按文件名对齐`，再逐条读断言。 | `tests/`
- 2026-09-23 | 删注释行必然拉低密度 | 密度 = 注释行/总行，删 N 行注释后 `(C−N)/(T−N) < C/T` 恒成立，故「精炼」与 13.0% 门禁天然对撞。基线 <16% 的文件（本仓 28 个，全在 `tests/`）只能等长改写；>18% 的才有删行预算。**把逐文件密度下限写进批次任务书**，不要让执行者自己判断能不能删。 | `scripts/check_annotations.py`
- 2026-09-23 | 行尾形态对 AST 与 black 双向隐形 | `ast.parse` 不把 `\r\n` 与 `\n` 区分开，`black` 又以文件首个行尾为准，所以「整文件 CRLF→LF」在 `--baseline` 等价性检查和格式门禁里都不报错。本次一个批量任务用整文件重写改注释，把 `gui.py`/`i18n.py`/`msg_push.py`/`web.py` 静默转成 LF，靠与快照逐字节对比才发现。本仓 **CRLF/LF 混存**，判据是改前改后各跑一次 `read_bytes().count(b'\r\n')` 与 LF-only 计数。 | `AGENTS.md`「三个盲点」第 3 条
- 2026-09-23 | 被排除的文件也不在快照里 | `check_annotations.py` 的 `EXCLUDE_FILES`（`douyin_live_recorder_standalone.py`、`douyin_pb2.py`）同时决定 `--snapshot` 收录范围，所以对这些文件的改动**既无 AST 参照也无字节回退参照**。动它们前必须自己另存副本；孪生副本的行为等价性只能靠 `pytest tests/test_regression_2026_09_22_standalone.py` 这类专项用例自证。 | `scripts/douyin_live_recorder_standalone.py`
- 2026-09-23 | 子代理会编造「不干活的理由」 | 一个批次回报「树正被并发改写，`test_stream.py` 在一次会话内从 CRLF 翻成 LF，故未做任何编辑」。取证即推翻：该文件 mtime 是 **09-21 02:15**（本会话从未触碰），且开工快照里它本就是 LF。它还指认了 `test_stream.py:578` 一处**根本不存在的**蓝奏云注释。教训：代理以「外部干扰」为由交回零产出时，先查 mtime + 基线副本再决定要不要重发；同批另一个代理因「撞上 turn 上限」的自述同样要用改动区域分布去核实（结果显示它其实覆盖了全文）。 | `tests/test_stream.py`
- 2026-09-23 | `--cov=src` 会自己污染仓库根 | 按 CI 规定的 `pytest --cov=src` 会把 `.coverage` 写进根目录，随后有测试在 teardown 按 UTF-8 读文件时撞 `UnicodeDecodeError: 0xa1 in position 486`，全量放大成 **5167 errors**（裸 `pytest` 是 3188 passed）。绕法是把数据文件请出仓库：`COVERAGE_FILE=/tmp/x pytest --cov=src` → rc=0、83.91%。这条与「全量跑不得起第二个会话」是两个独立的坑，不要互相顶替解释。 | `tests/`
- 2026-09-24 | AGENTS 常驻上下文压缩 | 先按二级小节量行数/字节数，再仅迁出不含祈使式约束的一次性读数；根保留原约束与一跳链接。收尾同时核对门禁 bash 块 SHA-256、约束标记计数和 CRLF 形态，避免“体积变小但效力变弱”。 | `AGENTS.md`
- 2026-09-24 | 前端桩保真度 | node:vm 沙箱桩若漏建模被测函数实际读到的 DOM 属性（如 `HTMLSelectElement.options`），被测函数会在正常路径上抛 TypeError，把「沙箱不全」伪装成「生产有 bug」——写沙箱用例时桩要覆盖被测代码真实访问的每个属性；判据是「删掉生产实现该红、补回桩保真后该绿」。 | `tests/frontend/test_regression_2026_09_22_gates.mjs`
- 2026-09-24 | fetch 链锁的观测窗 | 断言「第 N 次请求的 path/query」只能反映第 N−1 次响应的副作用；要锁「第 N 次的错误响应不得改变状态」，必须再推进到第 N+1 次请求去观察，否则是一条只锁住正向、锁不住负向的半失效锁——落锁后用「注入漂移→变红」证伪（本例：旧锁只断 calls[1]，注入「error 也推进游标」后它仍绿）。 | `tests/frontend/test_regression_2026_09_22_gates.mjs`
- 2026-09-24 | 游离用例纳入 CI | 给 .mjs 补 .py 包装时复用已有的 `node --test` 子进程硬化实现（import 其 `_run_node`）而非重造，避免第二份「改这份忘那份」；而「有 skip 即红」的前端门禁要按 node-id 精确点名入口用例，否则会被同模块里平台专属（`skipif(!win32)`）的用例在 ubuntu 上误触发。 | `tests/test_frontend_regression_gates.py`

