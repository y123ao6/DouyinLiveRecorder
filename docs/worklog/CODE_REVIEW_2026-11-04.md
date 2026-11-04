# 全仓静态代码审查报告（2026-11-04）

> 审查执行时间：2026-11-04 18:31 ~ 19:45（本机时钟，Windows / x64 / Git Bash）
> 审查对象工作区：`D:\DouyinLiveRecorder`，分支 `main`，HEAD = `c38e22a`
> **声明：本次审查全程只读，未修改、未创建、未删除任何源文件；本报告是本次审查新增的唯一仓库文件。**
> 报告放置说明：沿用本仓既有惯例落 `docs/worklog/`（与 `CODE_REVIEW_2026-09-18` 至 `2026-10-30` 共 21 份历轮报告同目录），文件名取委托当日日期；用户仅指定文件名、未指定目录，故按仓库惯例补齐，并在首行说明。经检索 `CODE_REVIEW_2026-11-04.md` 不存在，无需 `_2` 后缀。

---

## 1. 审查概述与背景

### 1.1 触发背景与口径锁定

用户要求对当前工作区全部源代码执行一次全面、系统的**只读**静态审查，四维度为代码质量、潜在缺陷、安全漏洞、逻辑错误与死代码；逐文件记录问题（路径 + 行号 + 类型 + 严重度 + 修复建议），同类问题归类合并，产出 `CODE_REVIEW_YYYY-MM-DD.md`。按本仓《只读审查生命周期》Skill 的阶段 0 拆成四要素，写入本节备查：

| 要素 | 本轮口径 |
| --- | --- |
| 范围 | 仓库根节点递归遍历全部手写源代码（Python / JavaScript / Node.js `.mjs` / VBScript / Shell / HTML / CSS / Proto / 配置与 CI 文件）；排除第三方依赖、构建产物、锁文件、压缩/二进制产物与文档正文 |
| 维度 | ① 代码质量 ② 潜在缺陷 ③ 安全漏洞 ④ 逻辑错误与死代码 |
| 输出 | `CODE_REVIEW_2026-11-04.md`，重名追加 `_2`/`_3`；目录沿用 `docs/worklog/` |
| 只读边界 | 允许新增报告文件本身；**禁止**修改任何源文件、禁止写入型格式化/安装/测试命令；所有探针与简报落 `%TEMP%` |

### 1.2 决定本轮结论的背景事实（实测，取数时刻 18:34 与 19:42）

1. **仓库状态干净**：`git rev-parse --short HEAD` = `c38e22a`；`git status --porcelain` 起始 0 条、收尾 0 条；`git grep -c '^<<<<<<< ' HEAD` 与工作树均 rc=1、0 块 0 文件。不存在历史轮次出现过的「冲突块残留 / 提交态产物损坏」语境，本轮全部发现均来自对当前干净主干的直读。
2. **语法面健全**：快照 AST ok=257 / broken=0；主控独立复跑 257 个 `.py` 的 `ast.parse`，`ast_parse_errors=0`。AST 判据预扫（超长函数 ≥200 行 13 处、嵌套 ≥6 层 29 处、形参 ≥9 个 10 处、裸 `open()` 12 处、`subprocess` 近似无 timeout 27 处、`except: pass` 无邻近注释 36 处、疑似未用 import 29 处）命中后逐条实读，**绝大多数属误报或刻意设计**，核销记录见 §7.2。
3. **静态门禁面全绿，但防线判定面存在空转**：本轮实跑 7 项只读型门禁并取真实退出码（`命令 >"$LOG" 2>&1; echo rc=$?`）——`check_annotations.py`、`compile_po.py --check`、`check_version.py`、`check_runtime_pins.py`、`check_skill_agents_consistency.py`、`black --check --line-length 120 --target-version py314 .`、`isort --check-only --profile black --line-length 120 .` **全部 rc=0**。但静态审查发现其中两项存在「判定面为空仍退 0」「告警降级不判失败」的形态（M-11、M-12），即**门禁全绿不等于防线成立**。
4. **只读自证**：`review_scope.py` 基线（18:34:18）与收尾复比（19:51:10，跟踪文件口径）均为 `changed=0 added=0 removed=0`、`RESULT: clean`；`repo_review_snapshot.py snapshot` 起始 tracked=473 / untracked=0 / manifest=473，收尾 `verify --allow-added docs/worklog/CODE_REVIEW_2026-11-04.md` 为 `CHANGED 0 / REMOVED 0 / ADDED 1 / UNEXPECTED_ADDED 0 / RESULT PASS`（rc=0）；`git status --porcelain` 定稿仅 1 条 `?? docs/worklog/CODE_REVIEW_2026-11-04.md`。即**报告是唯一新增文件、源文件零改动**，审查期内无并发工作包改盘，§7.3 因此为空。

### 1.3 结论摘要

| 严重程度 | 数量（同族合并后） | 主要分布 |
| --- | --- | --- |
| 严重 | **1** | 出站重定向跟随链的凭据外带与 host 校验时序（S-01） |
| 中等 | **24** | 输入校验与解析边界 6、门禁/防线判定面 6、并发与资源 3、构建发布与配置同源 6、逻辑契约 3 |
| 轻微 | **16 族** | 结构度量、重复代码、注释失真、硬编码算法常量、边界残余、测试存量债务等 |

**总体判断**：主干健康度良好——录制链 argv 构造、选源探针与分片层探测、运行时钉定 fail-closed、Web 26 条路由鉴权与三重脱敏、Qt 主线程契约、JS 签名脚本字节钉定（5/5）经逐行核对均成立；`XSS` 可达注入点、`shell=True`/`os.system`/`pickle.loads`/`yaml.load(`、真实凭据入库、路径穿越、GET 状态变更接口均实测 0 处。本轮风险集中在两类：**一是「防线写对了但顺序错了」**（S-01：host 校验晚于带凭据跳转；M-11~M-13：判定面空转或被绕过）；**二是「主线修好了但镜像面/判定器没跟上」**（standalone 独立发行副本、门禁脚本自身、测试断言判据）。最需要先动的是 S-01，其次是一批低成本的判定面收口。

---

## 2. 审查范围与方法

### 2.1 范围（实测 2026-11-04 18:34）

| 区域 | 文件数 | 行数 | 审查方式 |
| --- | --- | --- | --- |
| 根目录（入口 / 构建 / 配置 / 部署） | 26 | 16390 | 逐行精读，切 3 区（`main.py` 5517 行按 L1–2800 / L2801–5517 两区） |
| `src/` 顶层 | 41 | 27991 | 逐行精读，切 5 区（网络配置 / 录制选源 / 工具安装 / Web 后端 / spider 两段） |
| `src/gui_qt/` + `src/ui_*` + `src/web_tray.py` | 23 | 6095 | 逐行精读 1 区 |
| `src/platforms/` + `src/proto/` + `src/javascript/` | 17 | 4303 | 逐行精读 1 区 + 存根/钉定对账 |
| `web/` | 4 | 3244 | 逐行精读（与 Web 后端同区） |
| `scripts/` | 18 | 8470 | 逐行精读 1 区 |
| `tests/` + `tests/frontend/` | 161 | 73959 | Grep 全量模式扫描 + 关键文件逐行抽读（2 区），覆盖边界见附录 A |
| `typings/` | 12 | 261 | 逐文件核对同步性 |
| `.github/` + `config/` | 15 | 2682 | 逐行精读 + 同源性对账 |
| **纳入审查合计** | **285** | **134118** | 生产代码约 6.0 万行逐行精读，测试约 7.4 万行扫描 + 抽读 |

**排除项（逐项说明）**：`.venv/` `venv/` `node_modules/` `vendor/` `node/` `ffmpeg/`（第三方依赖与运行时二进制）；`build/` `dist/` `out/` `coverage/` `coverage.json` `coverage.xml` `__pycache__/` `*.pyc` `DouyinLiveRecorder.egg-info/`（构建 / 派生 / 生成物）；`.git/` `.workbuddy/` `.zcode/`（版本库与本地工具目录）；`uv.lock` 与压缩产物（锁文件 / 归档，不读正文）；`assets/app.ico`（二进制，仅核结构）；`src/javascript/crypto-js.min.js` 正文（第三方压缩库，仅做 SHA256 钉定对账）；`src/proto/douyin_pb2.py` 正文（protoc 生成物，只核与 `.proto`/`.pyi` 同步）；`docs/**` 与根 `*.md`（文档正文只做同源性核对，含上轮遗留报告）；`i18n/*` 正文（只做四语键集合与抽样对账）。

### 2.2 方法

1. **基线自证**：`review_scope.py` 生成逐文件 sha256 清单 + 范围表（落 `%TEMP%`）；`repo_review_snapshot.py snapshot` 生成 `manifest.json`/`facts.json`；记录 HEAD、分支、脏文件数、HEAD/工作区冲突块。收尾 `--check` / `verify` 复比。
2. **语法与结构层**：Python 3.14.9 全量 `ast.parse`；`ast_probe.py` 判据扫描（阈值：函数 ≥200 行、嵌套 ≥6 层、形参 ≥9 个、`except: pass` ±4 行无注释、裸 `open()`、危险原语、无 timeout 子进程、疑似未用 import）。**命中只作线索**，逐条实读裁决。
3. **只读门禁实跑**：按 §1.2 第 3 条取真实 rc；未运行 pytest / 覆盖率 / mypy 全量（原因见 §9 未执行项声明）。
4. **高危模式横向扫描**：`shell=True` / `os.system(` / `eval(` / `exec(` / `pickle.loads` / `yaml.load(` / `_create_unverified_context` / `verify=False` / 硬编码凭据字面量 / `innerHTML` / `@_route` 计数；主控复跑干净范围读数（§8.3）。
5. **同源性对账**：`pyproject.toml [project.dependencies]` ↔ `requirements.txt`（18/18，差集 ∅）、JS 钉定表 5/5、`.gitignore` ↔ `.dockerignore` ↔ `Dockerfile`、注释回归锁 ↔ 用例存在性、前后端布尔 token 集合。
6. **分区逐行精读**：14 个只读子代理，每区 2.0k–6.6k 行，统一作业简报（只读硬约束 + 16 条带仓内出处的刻意设计白名单 + 严重度定义 + 回传格式）；每区回传「覆盖确认 + 最多 20 条发现 + 范围性卫生扫描结果（0 命中也写）」。
7. **主控复核**：54 条行号/证据校准探针（52 PASS，2 处为探针写法过窄、代码在相邻行，非断言错误）；对全部「严重 / 中等」断言独立复跑判据或实读代码，含 httpx 0.28 源码 `_redirect_headers`、XHS 短链分支、门禁脚本、VBS UTF-16 解码、Windows 异常类型；被推翻/修正的断言一律登记 §7.2，不静默删除。

### 2.3 工具版本口径

Python 3.14.9（venv）；black 26.10.1、isort 9.0.2、mypy 2.4.1、pytest 9.2.0、basedpyright 1.40.2、starlette 1.10.0、httpx 0.28.1（本地 `importlib.metadata` 实测）。上述为**本地口径，未经 CI 同版本验证**（`.github/workflows/ci.yml` 现为仅 `workflow_dispatch` 手动触发，见 L-09）。本轮未运行 mypy / basedpyright / pytest，原因与交回动作见 §9。

### 2.4 严重度定义

- **严重**：进程崩溃 / 数据损坏 / 凭据泄露 / 安全防线失效 / 功能完全不可用。
- **中等**：特定条件下行为错误、资源持续增长、防线可被绕过、维护上会误导后人（含悬空引用与文档承诺与实现不符）。
- **轻微**：可读性、命名、日志噪声、备案性观察。

---

## 3. 严重问题（S 组）

### S-01 出站重定向在主机白名单校验之前携带凭据头，且注释承诺的凭据剥离未实现

- **位置**：`src/async_http.py:383-405`、`src/async_http.py:590-598`、`src/async_http.py:610-619`；`src/spider.py:2584-2596`、`src/spider.py:2602-2605`、`src/spider.py:2658-2659`；关联 `src/spider.py:6923`（咪咕 CDN 重定向）。
- **类型**：安全（凭据外带 / SSRF 防线时序失效）；**严重度**：严重。
- **证据**（主控实读 + 独立复跑）：
  - `async_req` 的四条请求分支把 `follow_redirects=True` 硬编码（`async_http.py:383/392/402/405`），调用方无法关闭；
  - 逐跳复检 `_redirect_hop_rejection_reason` 只判「scheme 白名单 + 内网/保留目标」（`:596-598`），对**合法 https + 公网 IP 的落地目标不命中**；`:610-619` 已如实登记「跳转那一跳的出站连接已经发生 / DNS 重绑定窗口」残余风险，但**未登记自定义头随重定向外带**；
  - 主控读取 `venv/Lib/site-packages/httpx/_client.py:546-571` 确认 `_redirect_headers` 为 `Headers(request.headers)` 全量复制，跨源仅 `pop("Authorization")`（:556）与 `pop("Cookie")`（:569），`xy-common-params` 等自定义头**不做剥离**；
  - `spider.py:2588` 把 `"platform=iOS&sid=" + sid_value` 放入请求头，`:2596` 用这份 headers 对**用户提供的短链**发 `redirect_url=True` 请求；`:2602-2605` 注释明确写「不校验就…等于把 Cookie 与会话 sid 递送给任意 host」「并剥离 Cookie / xy-common-params」，但 `:2606-2659` 全段**没有任何 `headers.pop`**；落地页 host 白名单（`:2607`）在请求发出之后才判；不符合白名单时 `url` 保持原始短链，`:2659` 又用同一份 headers 再请求一次并再次自动跟随。
- **潜在影响**：短链被 302 到任意公网主机（或平台/中间链路返回恶意 Location）时，会话 sid 会随自定义头送达该主机；`sid` 可由用户在 `config.ini [Cookie] xhs_session_sid` / 环境变量 `XHS_SESSION_SID` 配置为**真实登录态**（`spider.py:2580` 明确提示配置有效 sid），此时构成用户凭据泄露。响应体还被当作业务数据回传（`:419` 返回 `str(response.url)`）。默认安装形态下 `_XHS_BUILTIN_SESSION_SID` 是已过期的内置游客态常量，实际危害取决于用户是否配置了真实会话值——此边界如实说明，不夸大可达性。
- **修复建议**：① `async_req` 增加 `follow_redirects` 参数，默认改为 `False`，短链解析改手工逐跳（每跳先校验 scheme/host 白名单、再决定是否继续）；② 在 `_build_hop_guard` 之外补「跨源重定向重建 headers」逻辑，剥离所有自定义凭据类头（至少 `xy-*`、`x-bogus`、`a-bogus`）；③ `spider.py` 短链分支用不含凭据的 headers 取 Location，落地页通过 `_xhs_is_allowed_host` 与内网判定后，才用带凭据 headers 请求；④ 把「丢弃跳转时剥离凭据」从注释落成代码，并补一条断言「跨源跳转后自定义头集合为空」的回归锁。
- **修复成本**：中（涉及统一出站入口，需对 XHS / 咪咕 / 知乎 / Shopee 短链路径做真实 URL 增量验证）。
- **主控复核**：已实证（三段代码实读 + httpx 源码复跑 + 行号校准探针 PASS）；未做联网构造 302 的运行态复现，列 §9 未执行项。

---

## 4. 中等问题（M 组，同族已合并）

> 每条均含文件路径、行号、类型、严重度、影响与修复建议。本轮为只读审查，处置状态一律「未修」。

### 4.1 输入校验与解析边界

**M-01 日志与异常文本脱敏无全局兜底，多处 `e=e` 绕过中央漏斗**
- 位置：`src/spider.py:806-810`、`src/spider.py:1002-1006`（`logger.exception`）；`src/ws_client.py:255`、`:381`，`src/ttwid.py:152`、`:222`，`src/config_io.py`（9 处）、`src/proxy.py`（5 处）等共 22 处裸异常对象；`src/logger.py:101`（patcher 只处理房间字段）；`src/web_api.py:894-898`、`src/web_api.py:403-405`。
- 类型：安全（敏感信息泄露）；严重度：中等。
- 影响：`ws_client.py` 文件头约定「所有出口一律先过 `utils.mask_credentials`」、`base.py:48-50` 明载 websockets/httpx 异常 `str()` 内嵌完整 URL（可带 token / 代理 userinfo）；`e=e` 把异常对象交 loguru 就地 `str()` 绕过脱敏。`PlayURL.log` 是 INFO 级专记流 URL 的文件 sink（`logger.py` 轮转 300KB × 保留 3 份），任一调用点漏过码即长期明文落盘。`utils.py:1188-1190` 注释自承「治本是在 logger 注册 patcher，故另案处理」，属如实登记但未闭合。
- 建议：在 `logger.py` 注册统一 patcher 对 `record["message"]` 过 `mask_credentials`；上述日志点统一改 `e=utils.mask_credentials(str(e))`；优先修 `ws_client`/`ttwid`/`spider` 的 6 处。成本：低～中（会改变按整行断言的用例，需同步调整）。

**M-02 平台 ID 未判数字/未 percent 编码即拼进 JSON 请求体与请求 URL（11 处，上轮 L-02 遗留）**
- 位置：`src/spider.py:4553`（百度）、`:6523`（淘宝）、`:6714`、`:6735`、`:6753`（京东）裸字符串拼 JSON；`:6106`（浪Live `room_id=`）、`:6800`（Faceit nickname 入 path）、`:6852`（咪咕 `web_id` 入 path）等共 11 处；对照 `:5777`（知乎 `quote`）、`:6327`/`:6374`（Shopee `quote`）。
- 类型：安全（未校验输入 / 参数走私）；严重度：中等。
- 影响：ID 含 `"` 破坏 JSON 结构致接口失败，含 `&`/`#`/`../` 时可改写 query 或路径；相邻平台已设同名防线，易误导后人以为此处同样安全。ID 来自用户自填配置而非外部响应，危害限于畸形请求与漏录，无 RCE / 凭据外送。
- 建议：A 类改 `json.dumps` 构造 body 并按平台收窄 `re.fullmatch(r"[0-9]+", room_id)`；B 类统一 `urllib.parse.quote(..., safe="")`。成本：中（改变线上请求字节形态，按 DoD 需真实 URL 增量验证）；该项在 `docs/worklog/CODE_REVIEW_2026-10-30_FIX.md` §3 登记为「暂缓」，本轮复核仍未修（§7.1）。

**M-03 录后自定义脚本的动态参数未 `shlex.quote`，Windows 路径/含引号主播名损坏参数**
- 位置：`main.py:1464-1483`（`f'--record_name "{record_name}"'`、`f'"{save_file_path}"'`、`script_command.strip() + " " + " ".join(params)`）；被调方 `src/notify.py:193-273`（`shlex.split(posix=True)` + argv `Popen`）。
- 类型：缺陷（参数构造 / 边界处理）；严重度：中等。
- 影响：主控独立复核确认**不是命令注入**——`run_script` 全程 argv 列表、无 `shell=True`，shell 元字符只作普通字符；真实影响是反斜杠被 POSIX 词法当转义吞掉、未闭合引号令 `shlex.split` 抛 `ValueError` 被 `notify.py:265` 吞成「脚本命令解析失败」，录后脚本拿到错误路径或整条不执行。`if "python" in script_command`（`:1466`）子串判定还会误选参数格式。
- 建议：拼接前对每个动态值 `shlex.quote`，或改 argv 列表直传；「python」判定改按脚本后缀/显式配置。成本：低。

**M-04 TARS 解析器 7 处边界读绕过 `_need`，畸形帧抛 `struct.error`/`IndexError`**
- 位置：`src/platforms/_tars.py:60`、`:66`、`:81`、`:164`、`:168`、`:172`、`:176`；对照 `:193` 的 `read_string` 先 `_need(1)`。
- 类型：缺陷（空值/边界处理）；严重度：中等。
- 影响：注释 `:25-28`/`:84-85` 承诺「一切协议长度都经此消费」「畸形帧统一降级为 `ValueError`」；分区代理只读内联探针实测 `b'\x12'`→`struct.error`、`b'\x16'`/`b'\xf0'`→`IndexError`。上层 `huya.py:113` 的 `except Exception` 兜住故不崩，但共享解析器被不兜异常的调用方复用即暴露，且异常类型契约与注释互相说谎。另 `:106` MAP 注释「每键值对至少 2 字节」与 `:107` 的 `n > len(self._data)` 检查口径不一致。
- 建议：7 处补 `_need(1)` / `_need(n)` 后再解包；统一异常降级为 `ValueError`；修正 MAP 注释或检查式。成本：低。

**M-05 弹幕主机白名单未过滤控制字符**
- 位置：`src/platforms/bilibili.py:41-46`。
- 类型：安全（输入校验）；严重度：中等·**待确认**（缺 WS 客户端对含控制字符 URL 的运行态实测）。
- 影响：该函数是 `:26-29` 自述的「防 `getDanmuInfo` 响应把登录 Cookie 引向任意主机（凭据外泄 + SSRF）」防线；过滤集仅含 `/ : ? # @ \`，未含 `\n \r \t` 与空格，形如 `evil\n.bilibili.com` 可通过 `endswith` 后缀判定进入 `wss://{host}/sub`。多数 WS 库会拒绝 CRLF URL，故不升级。
- 建议：过滤集补控制字符，或改严格 DNS label 正则 `^[a-z0-9.-]+$` 后再做后缀判定。成本：低。

**M-06 `main.py` 一处 `in json_data` 缺 None 短路保护**
- 位置：`main.py:2428`（有 `if json_data and`）对比 `:2443`（`if "play_url_list" in json_data:`），`:2446`；对照 `:1844`/`:2284`/`:2542` 均有兜底。
- 类型：缺陷（空值处理）；严重度：中等·待确认（缺 `get_flextv_stream_data` 返回 None 契约的实证）。
- 影响：同函数已承认返回值可为假值；若 spider 返回 None，`:2443` 抛 `TypeError`，该 `with semaphore` 分支无 except，整轮取流失败并可能计入按 host 熔断样本。
- 建议：改 `if json_data and "play_url_list" in json_data:`，None 按未识别/离线处理。成本：极低。

**M-07 GUI 缩放偏好解析漏捕 `OverflowError`，损坏配置可致 GUI 完全起不来**
- 位置：`src/ui_scale.py:57-61`（`int(float(text))` + `except ValueError`）；`src/gui_qt/main_window.py:443`（`load_scale_preference` 在 `__init__` 链上）；同族 `src/gui_qt/shared.py:61-65`、`src/ui_theme.py:46-47`。
- 类型：缺陷（边界处理）；严重度：中等。
- 影响：主控实读确认 `parse_scale` 的 `except ValueError` 不含 `OverflowError`；`config.ini [GUI] gui_scale` 写成 `1e400`/`inf` 时 `int(float(...))` 抛 `OverflowError`，而 `load_scale_preference` 的 `parser.read` 保护段不覆盖 `:85` 的 `parse_scale` 调用，异常冒泡到 `MainWindow.__init__`，与 `:51` 注释「配置损坏绝不能让 GUI 起不来」承诺相反。分区代理用内联解释器实证异常类型。
- 建议：三处补 `OverflowError`（PEP 758 无括号形态）、`ui_theme` 补 `ValueError`；`_resolve_initial_theme_and_scale` 对偏好读取段整体兜底回落默认。成本：低。

### 4.2 并发、资源与生命周期

**M-08 采集器生命周期标志位跨线程无锁 check-then-set**
- 位置：`src/collector.py:255-258`（`_stop_called`）、`:624-635`（`_room_closed_reported`）、`:142-144`/`:229-231`/`:494-498`（`_started` 同族）。
- 类型：缺陷（并发）；严重度：中等。
- 影响：主控实读确认三个 bool 均无锁；`_on_close`（事件循环线程）与 `stop()`（录制线程）可同时读到 False 而双投 `room_closed` 事件，正是 `:259` 注释「首投生效」要去重的形态；`hub.room_closed` 含 IO 会释放 GIL，竞态可实际发生。
- 建议：用一把 `threading.Lock` 包住「检查 + 置位」，或把 `_room_closed_reported` 改为带锁的原子领取。成本：低。

**M-09 弹幕边车 JSONL 轮转持续失败时无累计字节上限**
- 位置：`src/danmaku_monitor.py:45-50`、`:107-120`（`if fh.tell() >= _ROTATE_BYTES and not _rotate_in_backoff(path):` 命中退避后仍 `fh.write`）。
- 类型：缺陷（资源泄漏 / 磁盘无界增长）；严重度：中等。
- 影响：`.1` 备份被第三方长期占用或跨卷 `os.replace` 永久失败时，每 300s 重试一次均失败、文件持续追加且无上限；7×24 常驻进程可耗尽磁盘。短窗退避是注释登记的刻意取舍，但「永久失败态」缺兜底。
- 建议：给退避加连续失败计数，达阈值禁用写入并升级告警；或退避期内仍按字节上限停止追加。成本：低。

**M-10 Twitch IRC 跨帧半行缓冲无上限**
- 位置：`src/platforms/twitch.py:114-116`（`text = self._line_buf + text; ...; self._line_buf = _parts.pop()`）。
- 类型：缺陷（资源 / 边界）；严重度：中等·待确认（正常 IRC 帧必带 CRLF，触发需畸形/篡改帧）。
- 影响：持续推送不含 `\n` 的帧时 `_line_buf` 无限累积且每帧 O(n) 重拼，形成 O(n²) CPU 与内存增长；对照 `bilibili.py:320-331` 的解压限长，本支缺对应上限。
- 建议：给 `_line_buf` 设字节上限，超阈值清空并留 debug 线索。成本：低。

### 4.3 门禁与防线判定面（本轮最集中）

**M-11 `check_annotations.py` 空判定面仍退 0（门禁假绿）**
- 位置：`scripts/check_annotations.py:347`（`for path in iter_source_files(root)`）、`:400`（`return len(problems)`）、`:566-583`（`return 1 if ... > 0 else 0`）；同族 `check_equivalence():513-563`。
- 类型：缺陷（门禁可信度）；严重度：中等。
- 影响：主控实读确认 `--root` 传错、目录不存在或源文件全被排除时循环 0 次 → `problems=0` → 打印「共扫描 0 个 Python 文件 / 全部通过」而 rc=0。同门禁块 `check_coverage.py:398-404`、`check_runtime_pins.py:192-193`、`check_skill_agents_consistency.py:169-180` 对空判定面均 `sys.exit(2)`，本文件 `:350-361` 自承「与 rc=2 分级契约冲突」却只收口单文件读不动。分区代理用内联探针实证 `check_conventions(不存在root)` → RETURN=0。
- 建议：`stats`/`scanned` 为 0 时 `sys.exit(2)`；`check_equivalence` 空并集同样退 2。成本：极低。

**M-12 `check_skill_agents_consistency.py` 检查 3 降级为只发 WARN 而 rc 仍 0**
- 位置：`scripts/check_skill_agents_consistency.py:11`（文件头「必须声明 AGENTS.md 为约束事实源」）、`:219-226`（缺措辞仅 `warnings.append`）、`:257-265`（`elif warnings: ... return 0`）。
- 类型：缺陷（防线可绕过 / 文档承诺与实现不符）；严重度：中等。
- 影响：实现只要 SKILL.md 出现 `AGENTS.md` 字样即过，未标注「约束事实源」只记告警；同文件检查 5 特意把「只告警 rc=0」升级为硬失败并写明「告警即失败」判据，唯独检查 3 保留放行面。与 `AGENTS.md`「新增门禁若存在跳过/降级只发 warning、退出码仍 0 形态必须同回路判失败」直接冲突。
- 建议：把「未标注约束事实源」从 `warnings` 移入 `errors`（退 1）。成本：极低。

**M-13 `agent_hook_guard.py` 单个 `|` 紧接受保护目录名可绕过删除路径守卫**
- 位置：`scripts/agent_hook_guard.py:100-101`（`_PROTECTED_TAIL_BOUNDARY` 不含 `|`，注释却称 `|`「已被切成独立语句」）、`:266-270`（`_statements` 按 `&&`/`||`/`;`/`\n` 切，单 `|` 不切）、`:358-372`（`_protected_hit` 的 tail 边界判定）。
- 类型：安全（防线绕过）；严重度：中等。
- 影响：主控实读 `:364-367` 确认 tail 不在边界集合即 `continue`；分区代理只读探针实证 `check_bash_command('rm -rf logs|cat')` → `None`（放行），而 `check_bash_command('rm -rf logs')` → `R-CLEAN-SCOPE`（拦下）。`AGENTS.md` 把 `logs/` 等运行期目录列为禁删区，该形态下守卫失效。
- 建议：边界集合纳入 `|`（及 `&`），或让 `_statements` 把边界字符并入判定；补 `logs|` 形态进 self-test 的 `block_cases`。成本：极低。

**M-14 `test_regression_gates.py` 三处文本/源码切片判据可被 def 行或注释喂饱**
- 位置：`tests/test_regression_gates.py:664`（`assert src.count("read_version()") >= 1`）、`:270`（`any(symbol in body_src ...)`）、`:304-305`（`"if not args.keep_going:" in src`）；同文件 `:598-601` 自述「必须匹配可执行形态，否则注释文本就能喂饱断言」。
- 类型：逻辑（回归锁失效）；严重度：中等。
- 影响：`build_exe.py` 中 `read_version()` 仅 2 处命中 = `def read_version() -> str:` + 唯一调用点；删掉调用点后 `count` 仍 ≥1、断言恒绿。`:270`/`:304-305` 同型（`ast.get_source_segment` 含注释）。主控校准探针确认 `:664` 行内容。
- 建议：改 AST 取 `ast.Call` 并排除 `FunctionDef` 行；`:270`/`:304-305` 复用本文件已有的 `_function_body_source` AST 口径。成本：低。

**M-15 两条资产接线锁在干净克隆 / CI 上恒 skip**
- 位置：`tests/test_agent_hook_guard.py:467-492`（`if not settings.is_file(): pytest.skip(...)`、`if not command_file.is_file(): pytest.skip(...)`）；文件头 `:18-19` 自述 `.qoder/` 被 gitignore、全新克隆缺该目录。
- 类型：质量（覆盖缺口）；严重度：中等·待仲裁（简报白名单未列此条，但文件头注释自述为刻意）。
- 影响：「hooks 指向本脚本」「命令资产不复制门禁清单」两条契约在 CI 无覆盖；`test_script_self_test_entrypoint_passes` 只证脚本自测、不证接线。全仓 `pytest.skip` 22 处中无条件 skip 实测 0 处，本条属条件 skip 但条件在 CI 恒真。
- 建议：接线契约改读仓库内可跟踪清单，或给这两条加 CI 可见的跳过计数断言。成本：低。

**M-16 R11 弱断言棘轮不识别 `_` 前导 helper，4 个有判据用例被误登记为债务**
- 位置：`tests/test_test_hygiene.py:1630`（`_R11_HELPER_PREFIXES = ("check_", "expect_", "assert_")`）、`:1660`、`:1603`（债务表 `"test_regression_main.py": 4`）；对照 `tests/test_regression_main.py:147`/`:160`（helper 内含 assert）与 `:182`/`:185`/`:1193`/`:1196` 调用点。
- 类型：逻辑（判定器缺陷）；严重度：中等。
- 影响：4 个实际有判据的用例被计为「函数体内无任何判据」，债务表虚高，并给该文件发放 4 个隐性「可退化额度」；与本文件 `:1582-1588` 自述要消灭的「债务表与现实脱钩」相悖。
- 建议：前缀增补 `_assert_`/`_check_`/`_expect_`（或判前 `lstrip("_")`），同步下调债务表并复核同类文件。成本：极低。

### 4.4 构建、发布与配置同源

**M-17 凭据排除仍是「两文件名黑名单」，新增 config 下凭据文件可入库并进对外镜像**
- 位置：`.gitignore:216-217`、`.dockerignore:133-134`（各只列 `config/config.ini` / `config/URL_config.ini`）；`Dockerfile:146-147`（注释称排除 `config/*.ini`，实际 `COPY --chown=recorder:recorder . ./`）；`build_exe.py:470-471`、`:551`（自承「白名单漏一个名字＝那个文件带着真实凭据进对外 zip」，仅在 zip 通道用全树扫描修复）。
- 类型：安全（凭据泄露）；严重度：中等。
- 影响：`config/cookies.json`、`config/proxy.ini`、`config/profiles/*.ini` 之类不被忽略，随 `COPY . .` 进入镜像；`docker-publish.yml` 推公开 GHCR 时镜像层内凭据可被提取（compose 卷挂载只在运行时遮蔽）。`CODE_REVIEW_2026-10-30_FIX.md` §1 已把 `config/URL_config.ini` 的跟踪态列为「待用户裁定」，本轮复核仍为跟踪态（§7.1）。
- 建议：两份 ignore 改目录级排除（`config/*.ini`、`config/*.json` 等）+ 已跟踪模板 `!` 反选；Dockerfile 改显式 COPY 清单。成本：低。

**M-18 Linux ffmpeg 解压临时目录落在发布目录，却不在残留断言与清理清单**
- 位置：`build_exe.py:1902`（`with tempfile.TemporaryDirectory(dir=ffmpeg_dir.parent) as tmp:`，parent 即 `RELEASE_DIR`）；`build_exe.py:1677-1683`（`RELEASE_TEMP_DIR_NAMES = ("_node_extract",)`）、`:1708-1719`（`_assert_no_release_temp_residue` 只按 4 个归档 glob + `_node_extract` 判定）、`:2153-2174`（`_clean_runtime_artifacts_from_release` 只删 logs/backup_config/downloads/`__pycache__`）。
- 类型：缺陷（产物污染）；严重度：中等。
- 影响：`finally` 只覆盖正常/异常/SystemExit；进程被强杀或崩溃后残留 `tmpXXXX/`（含解出的 ffmpeg 二进制）无人清理，下一次 `make_zip`（`:2225`）会整包打进对外 zip，而两道清理/断言都不认这个形态。
- 建议：临时目录改到系统 temp，或登记进 `RELEASE_TEMP_DIR_NAMES` 并在断言增列 `tmp*` 形态。成本：低。

**M-19 非 SSL 分支 STARTTLS 失败仅告警后仍以明文链路发送邮箱授权码**
- 位置：`msg_push.py:353`（`smtplib.SMTP(email_host, port, timeout=10)`）、`:358-369`（`except smtplib.SMTPException` 内只 `logger.warning`）、`:371`（`smtp_obj.login(login_email, email_pass)`）；默认 `open_ssl=True`（`:306`）。
- 类型：安全（凭据泄露）；严重度：中等。
- 影响：主控实读确认：显式 `open_ssl=False` 且服务器不支持 STARTTLS 时，等同邮箱口令的授权码走明文链路，可被链路嗅探；SSL 分支（`:347`）已用 `ssl.create_default_context()` 校验证书。`:354-355` 注释把「明确告警而非静默明文登录」写成既定取舍——**属知情降级，不享白名单豁免**，但定级时已考虑「用户显式关闭 SSL」这一前提。
- 建议：STARTTLS 不可用时返回失败，或把降级收敛到独立的显式 `allow_plaintext` 配置项（默认拒绝）。成本：低。

**M-20 `build_exe.py` 注释「永不被在线值覆盖」与 adopt 分支覆盖注入值相矛盾**
- 位置：`build_exe.py:1546-1549`（注释）、`:1597-1598`（`merged[slot] = online`）；`.github/workflows/build-release.yml:405-415`（注入 `DLR_RUNTIME_SHA256` 同时 `--pin-source adopt`）、`:667`（把注入定位为「发布密钥与代码仓分离」）。
- 类型：质量（文档承诺与实现不符）；严重度：中等。
- 影响：维护者据注释会以为 CI 注入钉定是最终判据，实际 adopt 档被在线清单值替换，发布判据优先级被误读。运行时钉定 fail-closed 链本身经核对成立（A8 区实证「标记绝不放行」），本条是口径误导而非钉定失效。
- 建议：注释改为「只改本次构建的 merged 副本、事实源表/env 不动；adopt 档以在线值为准」，并在 workflow 注明注入值退为回退基线。成本：极低。

**M-21 standalone 独立发行副本未回灌主线录制看门狗，且差异未登记**
- 位置：`scripts/douyin_live_recorder_standalone.py:2072`（`return proc.wait()` 无 timeout）、`:1811`（`_RECORD_UNLIMITED_CAP = "315360000"`）；对照 `main.py:874-888`（看门狗）、`:1397-1413`（`proc.wait(timeout=30)` + kill 回收）；文件头回灌清单与 `tests/test_regression_standalone.py:611-614`。
- 类型：缺陷（防线漂移 / 资源占用）；严重度：中等。
- 影响：主线看门狗专防「FLV `-reconnect*` 指数退避无限重连、永不退出、一直持有录制槽位」；standalone 唯一等待点无上界，常驻模式下 ffmpeg 挂起即房间线程永久阻塞、录制槽位永久占用。白名单 #12 允许刻意差异，但要求「差异已登记」，本项在回灌清单与回归锁中均未见「刻意不回灌及原因」。
- 建议：补「主线防线编号 → standalone 符号存在性」清单并登记理由，或回灌最小停滞检测；至少给 `proc.wait()` 加上界 + 超时补杀。成本：中。

**M-22 standalone 日志轮转注释与实现矛盾，且并发轮转无保护**
- 位置：`scripts/douyin_live_recorder_standalone.py:119-121`、`:126-136`、`:148`、`:1884-1886`、`:2007`、`:2224`。
- 类型：缺陷（悬空引用 / 并发）；严重度：中等。
- 影响：`:119-121` 注释称「standalone.log 与 ffmpeg.log 均为无上限 append」，`:148`/`:2007` 实有单代轮转；`:1885` 又称「该日志 append 无轮转」，三处过时注释误导后人。更实质的是 `:2224` 每房间一线程并发录制，多个 `run_ffmpeg` 对同一 `logs/ffmpeg.log` 做 `os.replace`，Windows 文件被占用时 `:135-136` `except OSError: pass` 静默跳过 → 轮转长期失效，回到注释自承的「磁盘占满」形态。
- 建议：更新三处注释；轮转纳入 `_print_lock` 或独立锁，失败计数并告警而非静默吞掉。成本：低。

### 4.5 逻辑与契约

**M-23 `StopRecording.vbs` killTree 分支身份复核硬编码 ffmpeg 映像名，回退补刀恒不触发**
- 位置：`StopRecording.vbs:45`（`PROCESS_FFMPEG = "ffmpeg.exe"`）、`:126`（`TerminateProcesses(recorderList, True)`）、`:431`（`If killTree Then`）、`:441-442`（`ProcessIdentityStillMatches(pid, PROCESS_FFMPEG)` → `taskkill /f /pid`）、`:453`（Else 分支同款，处理 ffmpegList 时正确）、`:500`（`If procName = LCase(expectedName) Then`）。
- 类型：逻辑（死代码 / 条件写反）；严重度：中等。
- 影响：主控按 UTF-16 LE 解码全文 570 行复核确认：`recorderList` 内为 `DouyinLiveRecorder*.exe`/`douyin-recorder*.exe`/`python.exe`（`:194`/`:196`），永远不等于 `ffmpeg.exe`，`:442` 的补刀成死代码；主进程 `taskkill /t` 与 WMI 终止双双失败时不会再补刀。`:439-440` 注释「不加身份复核的补刀就是误杀（宁可漏杀）」说明保守意图，但传错常量使防线整体空转。
- 建议：`:441` 改按该 pid 实际映像名（或复用归类时记录的 `Name`）调用；`:453` 保持 ffmpeg 不变；补 killTree 分支补刀命中的离线用例。成本：低。

**M-24 `set_https_recording` 遗留联动与主线「不再联动」语义冲突**
- 位置：`src/http_config.py:24-27`、`:41-45`（`set_stream_ssl_verify(not value)`）、`:52-58`；`main.py:4706`（恒 `set_https_recording(False)`）、`:4942`（注释「不得在这里按开关联动」）；`tests/test_http_config.py:32-34`、`:134`（仍锁联动语义）。
- 类型：逻辑（文档/测试/实现不符）；严重度：中等。
- 影响：模块头仍文档化「开启 = https 拉流 + 拉流侧禁用证书校验」，字段实为恒 False；若后人按文档在热更新恢复联动，`stream_ssl_verify=False` 会让 `get_effective_ssl_verify` 无视平台名单直接返回 False，重新引入全站拉流 TLS 降级。当前接线一致，但防线可被按文档改回。
- 建议：移除 `set_https_recording` 内的 `set_stream_ssl_verify` 联动与 `https_recording_enabled` 字段，同步模块头注释与测试断言。成本：低。

---

## 5. 轻微问题（L 组，同族已合并）

| 编号 | 位置（代表） | 类型 | 说明与建议 |
| --- | --- | --- | --- |
| L-01 | `main.py:1060`/`:3769`/`:4786`；`src/spider.py:6481`/`:6235`；`src/gui_qt/theme.py:227`；`msg_push.py:296`/`:456`/`:518`；`src/async_http.py:311` | 质量 | 结构度量族：≥200 行函数 13 个（最长 `start_record` 794 行）、嵌套 ≥6 层 29 处、形参 ≥9 个 10 处。均有完整注释与回归锁，属可维护性备案；建议随重构拆分，不单独造大 diff |
| L-02 | `src/spider.py:695-709`/`:1158-1163`/`:1365-1373`；`:532-578`/`:3108-3130`/`:3199-3214` | 质量 | 逐平台 headers 构造重复（`if cookies:` 28 处、`Mozilla/5.0` 27 处）；m3u8 清单解析三份实现，其中 `:3122-3125` 未按 `:557-559` 过滤 `.m3u8` path。建议抽 `_build_headers()` 并复用 `get_play_url_list` |
| L-03 | `build_exe.py:2402-2403`；`.github/workflows/ci.yml:6`/`:677`；`requirements.txt:6`/`:29`；`main.py:188`；`src/gui_qt/theme.py:213-219`；`src/web_tray.py:228-229`；`tests/test_test_hygiene.py:8-9`；`src/platforms/douyin.py:6` | 质量 | 注释与实现/事实失实：config.ini 实为 LF 却称 CRLF；已移除 FastAPI 却仍称 FastAPI TestClient；依赖项说明被拼接；`exit_recording` 注释与复位实现矛盾；R11 追加后文件头仍称「九条规则」。建议逐处订正（注释只增不改口径下以补充更正为准） |
| L-04 | `src/spider.py:88-93`/`:1060-1063`/`:2409`/`:5935`/`:5937`/`:7004`；`src/javascript/liveme.js:332`；`src/platforms/twitch.py:85` | 安全·观察 | 硬编码应用级凭据/签名常量（含已过期内置 sid、嗨秀 accessToken、来秀签名盐、站方 RSA 公钥、公开匿名 IRC 口令）。均有 env/config 覆盖入口与过期告警，非用户私人凭据；`CODE_REVIEW_2026-10-30_FIX.md` §1 把 M-17 列为「待用户裁定」，本轮仍在。建议补来源注释或按裁定外移 |
| L-05 | `src/spider.py:12`；`src/ffmpeg_install.py:1023-1030`；`src/platforms/douyin.py:231-232`；`src/stream_select.py:66-68`；`src/spider.py:5382`/`:5887-5888`；`tests/frontend/test_motion.mjs:78` | 逻辑·死代码 | 真未用 import 1 处（`itemgetter`）；恒真守卫 `if not is_RHS:`（注释已登记保留）；`METHOD_ONLINE: pass` 死分支；`clean_name` 保留名 `partition(".")` 因 `rstr` 已剥点号恒空（不可达）；两处对已绝对化地址做 `urljoin` 恒等冗余；DOM 桩 `? null : null`。建议逐个删或改注释说明 |
| L-06 | `src/spider.py:1316-1321`/`:1435`/`:1523`/`:4696-4697`/`:6080`/`:6172`/`:6451`/`:7090`；`src/srt_writer.py:47`；`src/video_postprocess.py:284`/`:353`/`:415-418` | 缺陷 | 空值与边界残余：两处裸 `.get()` 取字符串字段未按 `_dig_str` 收敛；`is_live` 未归一 bool（Picarto 直接透传 `online`）；17Live 冗余 `and`；微博 `split("_")[0]` 拼坏回退候选；SRT 小时位未封顶 2 位（≥100 小时输出 `100:00:00`）；`rsplit(".")` 在目录含点且文件无扩展名时错位。建议逐点收窄，成本均极低 |
| L-07 | `main.py:1372-1387`；`src/log_archive.py:198-206`；`src/gui_qt/main_window.py:748-756`/`:1234-1243`；`build_exe.py:307` | 缺陷 | 资源细节：ffmpeg stderr 临时文件在 finally 未补删（异常路径残留）；devnull 句柄覆盖前未 close；GUI 图标读失败被宽 except 吞成空字节后误报「文件损坏」且重复读/校验；`open_downloads_folder` 的 fire-and-forget Popen 无 timeout/退出回收。建议按位点补清理与归因文案 |
| L-08 | `build_exe.py:307`（`subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)` 无 timeout）；`.github/workflows/issue-translator.yml:31-34` | 缺陷 | 唯一一处 `subprocess.run` 缺 timeout（CI 有 job 级超时兜底）；22 个 job 中唯一缺 `timeout-minutes` 的手动触发 job。`CODE_REVIEW_2026-10-30_FIX.md` §3 已把前者登记为「请用户手工补」，本轮复核仍未补。建议加宽松 timeout / 补 `timeout-minutes: 10` |
| L-09 | `.github/workflows/*.yml`（`uses:` 64 行：本地 17 / 浮动标签 46 / SHA40 1）；`.github/workflows/ci.yml:83-90` | 安全·配置 | 第三方 action 47 个中仅 trivy-action 按 40 位 SHA 钉定，其余为可重指向的 tag；`ci.yml` 仅 `workflow_dispatch` 触发、PR 无自动门禁。文件头对两者均有「刻意保留/QUARANTINED」说明，按备案登记；建议在分支保护侧同步核对 required check 与手动流解耦 |
| L-10 | `web/app.js:699`/`:1178`/`:1181`/`:1616`/`:215-228`/`:718`/`:1075`/`:690`；`src/web_api.py:1490` | 质量 | 15 处 `innerHTML` 逐处实读，服务端可控数据 **0 处未转义**（`esc()` 63 次调用）；4 处静态翻译串未 esc（值来自硬编码字典，不可达注入）；`apiError` 把完整响应体写浏览器控制台；3 处异步操作未纳入代次链；`upload_icon` 回显绝对安装路径但不被前端消费。建议收紧静态串与诊断输出 |
| L-11 | `tests/test_test_hygiene.py:1595-1624`（R11 债务表 19 文件 45 处无判据 + 3 文件 10 处裸 `assert_called*`）；`tests/test_async_http.py:560-574`；`tests/test_regression_spider.py:714`/`:725`；`tests/test_regression_utils.py:268-303`；`tests/test_web_api.py:2504-2533`；`tests/test_config_io_readonly.py:40`；`tests/frontend/test_regression_gates.mjs:1162`/`:1188` | 质量 | 测试存量债务：弱断言受双向棘轮管理（仓内已登记，非新增缺陷）；bytes POST 用例只断言返回值、缺 `content=` 分派断言；2 处 `pytest.raises(Exception, match=...)` 类型过宽；模块级 list 记录器靠 `clear()` 隔离；Windows 无 symlink 权限时 2 条路径穿越用例恒跳过；一处改 stdlib `os.replace` 本体与同族 shim 约定相悖；2 条 M-85 行为锁非 Windows 跳过。建议按债务表逐文件补真实行为断言 |
| L-12 | `tests/conftest.py:18`；`src/stream_select.py:965`/`:1254`；`.github/workflows/ci.yml:6` | 质量 | 悬空/漂移引用：注释指向 `AGENTS.md` 中并不存在的「测试产物一律走 tmp_path」具名条目（全文件 Grep 0 命中）；`.m3u8` 用子串包含判定而非扩展名（query 含该字样会误判 HLS）。建议改指向现有条目 / 改 `urlsplit().path.endswith()` |
| L-13 | `web.py:295`；`build_exe.py:880`；`src/web_api.py:429` | 质量 | 环境变量布尔解析内联（`in ("1","true","yes")` / `== "true"`），token 集合与唯一入口 `parse_config_bool` 的 `TRUE_TOKENS` 不一致；`on` 等合法真值被判假（只影响破例开关识别，不放宽防线）。配置文件侧唯一入口成立。建议统一或明确 env 不纳入该口径 |
| L-14 | `DouyinLiveRecorder.spec:12`/`:51-58` | 质量 | 自动生成物入库且携带构建机绝对路径 `D:\DouyinLiveRecorder\assets\app.ico`；`build_exe.py` 每次重写故实际影响有限。建议移出版本库或改跨平台占位 |
| L-15 | `src/spider.py:2164-2168`/`:2338`；`src/logger.py:204-215`；`src/utils.py:1188-1190` | 安全·观察 | 脱敏口径细节：buvid3 本地随机值在 1 处 debug 日志打印完整值（同文件其余 2 处走 `_buvid_log_form`）；`PlayURL.log` 专记流 URL，注释自承待治本。值为本地生成、不可还原真实凭据，危害有限但口径破窗。建议统一 |
| L-16 | `src/async_http.py:327-330`（`_ = abroad` 空转参数，130 处调用点传 `abroad=True` 无效）；`src/sync_http.py:120-156`/`:487-495`（`verify=False` 可显式绕过但生产 importer 0 处）；`src/config_io.py:449-456`（备份唯一命名 check-then-act）；`src/stream_select.py:1324`/`:1382-1386`（序列候选探针前未过形态白名单）；`web/app.js:338-661`（前端点分键与后端中文 msgid 两套 i18n 体系） | 逻辑·备案 | 观察/知情接受项：均已带注释登记、当前不可达或无行为后果。建议在对应模块补「疑似刻意设计」的仓内出处，避免后轮反复争论 |

---

## 6. 逐文件问题索引

> 下表对**有发现**的文件逐个记录（路径 → 行号 → 条目编号 → 类型/严重度 → 一句话修复建议）。同族多文件已合并的条目，在代表位置后以「等 N 处」标注，完整位点见对应条目正文。

| 文件 | 行号/范围 | 条目 | 类型 / 严重度 | 修复建议（一句话） |
| --- | --- | --- | --- | --- |
| `src/async_http.py` | 383-405, 590-598, 610-619 | S-01 | 安全 / 严重 | 默认关闭自动跟随 + 跨源重建 headers + 登记头外带残余风险 |
| `src/async_http.py` | 327-330, 443, 472, 788 | L-16, M-01 | 逻辑·备案 / 安全·中等 | 实现或移除 `abroad`；异常文本统一过 `mask_credentials` |
| `src/spider.py` | 2584-2596, 2602-2605, 2658-2659 | S-01 | 安全 / 严重 | 短链取 Location 不带凭据，落地页校验通过后才带凭据请求 |
| `src/spider.py` | 6923 | S-01（关联） | 安全 / 严重 | CDN 重定向前校验落地 host |
| `src/spider.py` | 806-810, 1002-1006 | M-01 | 安全 / 中等 | 两处 `logger.exception` 改 `e=mask_credentials(str(e))` |
| `src/spider.py` | 4553, 6523, 6714, 6735, 6753, 6106, 6800, 6852 等 11 处 | M-02 | 安全 / 中等 | `json.dumps` 构造 body、`quote(..., safe="")` 编码 path/query |
| `src/spider.py` | 88-93, 1060-1063, 2409, 5935, 5937, 7004 | L-04 | 安全·观察 | 应用级常量补来源注释或按裁定外移 |
| `src/spider.py` | 12, 1316-1321, 1435, 1523, 2164-2168, 2338, 4696-4697, 5382, 5887-5888, 6080, 6172, 6451, 6481, 6235, 7090, 695-709, 3108-3130 | L-01, L-02, L-05, L-06, L-15 | 质量/逻辑 / 轻微 | 删未用 import、统一 `_dig_str`/`is_live`、抽公共 headers helper |
| `src/http_config.py` | 24-27, 41-45, 52-58 | M-24 | 逻辑 / 中等 | 移除 `set_https_recording` 的 TLS 联动并同步测试 |
| `src/ws_client.py` | 255, 381 | M-01 | 安全 / 中等 | 异常文本过脱敏漏斗 |
| `src/ttwid.py` | 152, 222 | M-01 | 安全 / 中等 | 同上 |
| `src/config_io.py` | 9 处异常日志点, 449-456 | M-01, L-16 | 安全·中等 / 备案 | 统一脱敏；备份唯一命名改 O_EXCL 或纳入锁 |
| `src/proxy.py` | 5 处异常日志点 | M-01 | 安全 / 中等 | 统一脱敏 |
| `src/logger.py` | 101, 181, 204-215 | M-01, L-15 | 安全 / 中等 | 注册全局 patcher 对 message 过 `mask_credentials` |
| `src/web_api.py` | 403-405, 894-898, 1490, 718/1075 关联 | M-01, L-10 | 安全·中等 / 轻微 | 异常/traceback 脱敏；去掉多余 `path` 回显 |
| `src/web_api.py` | 595-705, 713-1526, 1649-1681 | §7.4（无发现） | — | 26/26 路由鉴权、路径穿越 0 处，保持现状 |
| `src/web_config.py` | 871-1151 | §7.4（无发现） | — | 节白名单 + 键名正则 + `'***'` 三重脱敏成立 |
| `src/web_models.py` | 65-211 | §7.4（无发现） | — | 模型与前端字段一致 |
| `src/collector.py` | 142-144, 229-231, 255-258, 494-498, 624-635 | M-08 | 缺陷 / 中等 | 三标志位加 `threading.Lock` 包住 check-then-set |
| `src/danmaku_monitor.py` | 45-50, 107-120 | M-09 | 缺陷 / 中等 | 轮转退避加连续失败计数与字节上限 |
| `src/stream_select.py` | 66-68, 965, 1254, 1324, 1382-1386 | L-05, L-12, L-16 | 逻辑 / 轻微 | 删不可达分支、改扩展名判定、探针前过滤形态 |
| `src/srt_writer.py` | 47 | L-06 | 缺陷 / 轻微 | 小时位 `min(h, 99)` |
| `src/video_postprocess.py` | 284, 353, 415-418 | L-06 | 缺陷 / 轻微 | 改 `os.path.splitext`；小时位封顶 |
| `src/stream.py`, `src/ffmpeg_proc.py`, `src/recorder_status.py`, `src/room.py`, `src/scheduler.py`, `src/startup_cleanup.py` | 全文 | §7.4（无发现） | — | 选源/熔断/管道回收/清理白名单经逐行核对成立 |
| `src/utils.py` | 998-1081, 1183-1200 | §7.2, L-15 | 观察 | `_SECRET_KEYS` 已含 `sid`；补 `xy-*` 头名登记 |
| `src/notify.py` | 193-273 | M-03（被调方） | 缺陷 / 中等 | 被调方 argv 契约成立；上游需 `shlex.quote` |
| `src/log_archive.py` | 186-206, 216-219 | L-07 | 缺陷 / 轻微 | devnull 覆盖前 flush+close |
| `src/gui_qt/main_window.py` | 443, 748-756, 1234-1243 | M-07, L-07 | 缺陷 / 中等·轻微 | 偏好读取段兜底；图标读失败按「无法读取」提示；Popen 回收 |
| `src/ui_scale.py` | 57-61 | M-07 | 缺陷 / 中等 | 补 `OverflowError` |
| `src/gui_qt/shared.py` | 61-65 | M-07（同族） | 缺陷 / 中等 | 补 `OverflowError` |
| `src/gui_qt/theme.py` | 213-219, 227-505 | L-01, L-03 | 质量 / 轻微 | 未知 theme_id 一并回落；长 QSS 模板备案 |
| `src/ui_theme.py` | 46-47 | M-07（同族） | 缺陷 / 中等 | 补 `ValueError` |
| `src/web_tray.py` | 228-229 | L-03 | 质量 / 轻微 | 注释与 action 赋值时序对齐 |
| `src/platforms/_tars.py` | 60, 66, 81, 106-107, 164-176 | M-04 | 缺陷 / 中等 | 7 处补 `_need`，统一降级 `ValueError` |
| `src/platforms/twitch.py` | 85, 114-116, 255 行附近 | M-10, L-04 | 缺陷 / 中等 | `_line_buf` 设上限；公开 IRC 口令备案 |
| `src/platforms/bilibili.py` | 41-46, 228-233, 320-331 | M-05, L-03 | 安全 / 中等 | host 白名单过滤控制字符；补吞异常归因注释 |
| `src/platforms/douyin.py` | 6, 231-232 | L-05, L-03 | 逻辑 / 轻微 | 文件头措辞与 `pass` 占位分支对齐 |
| `src/platforms/huya.py`, `douyu.py`, `_xbogus.py`, `__init__.py` | 全文 | §7.4（无发现） | — | 粘包边界、签名编码经实读无缺陷 |
| `src/proto/douyin.proto`, `douyin_pb2.py`, `douyin_pb2.pyi` | 全文 | §7.4（无发现） | — | 字段号与存根同步，0 处不同步 |
| `src/javascript/x-bogus.js` | 375-376 | §2 白名单 #7 | 观察 | 混淆脚本 `eval` 固有形态，哈希钉定 5/5 |
| `src/javascript/liveme.js` | 332, 348 | L-04 | 安全·观察 | 站方算法常量，补来源注释 |
| `src/javascript/haixiu.js` | 5, 524 | L-04 | 安全·观察 | 同上 |
| `src/javascript/migu.js` | 20, 381 | §7.4（无发现） | — | 信任边界护栏成立 |
| `main.py` | 1464-1483 | M-03 | 缺陷 / 中等 | 动态参数 `shlex.quote` 或 argv 直传 |
| `main.py` | 2428, 2443, 2446 | M-06 | 缺陷 / 中等 | 补 `json_data and` 短路 |
| `main.py` | 1372-1387 | L-07 | 缺陷 / 轻微 | finally 补删 stderr 临时文件 |
| `main.py` | 188, 874-888, 1060, 1397-1413, 3769-4562, 4599-4600, 4786-5513, 3981-4006 | L-01, L-03, L-07, §7.2 | 质量 / 轻微 | 巨型函数备案；`exit_recording` 注释订正；推送线程 `start()` 补 `RuntimeError` 兜底（待确认） |
| `build_exe.py` | 307, 470-471, 551, 880, 1546-1549, 1597-1598, 1677-1719, 1902, 2153-2174, 2402-2403 | M-18, M-20, L-03, L-08, L-13 | 缺陷/质量 / 中等·轻微 | 临时目录外置；注释与 adopt 对齐；补 timeout |
| `msg_push.py` | 296, 306, 347-371, 456, 518 | M-19, L-01 | 安全 / 中等 | STARTTLS 失败默认拒绝明文登录 |
| `web.py` | 294-295, 358-359 | L-13 | 质量 / 轻微 | env 布尔统一到 `parse_config_bool` |
| `gui.py`, `i18n.py`, `index.html`, `pyproject.toml`, `requirements.txt`, `docker-compose.yaml`, `pyrightconfig.json`, `.gitattributes`, `.pre-commit-config.yaml`, `coverage.json`, `DouyinLiveRecorder.spec` | 见 L-03, L-14 | 部分轻微 | — | 注释订正 / 生成物移出版本库；其余无发现 |
| `config/config.ini` | 全文 | §2 白名单 #13（无发现） | — | 脱敏基线模板，敏感键为空 |
| `config/URL_config.ini` | 全文 | M-17（跟踪态） | 安全 / 中等 | 改目录级排除；跟踪态待用户裁定 |
| `.gitignore` | 216-217 | M-17 | 安全 / 中等 | 改 `config/*.ini`/`config/*.json` 目录级排除 |
| `.dockerignore` | 133-134 | M-17 | 安全 / 中等 | 同上 |
| `Dockerfile` | 146-147 | M-17 | 安全 / 中等 | 改显式 COPY 清单 |
| `StopRecording.vbs` | 45, 126, 431-442, 453, 500 | M-23 | 逻辑 / 中等 | killTree 分支按实际映像名复核 |
| `web/app.js` | 215-228, 316, 338-661, 690-699, 1021-1344, 1616, 1861-1888 | L-10 | 质量 / 轻微 | 4 处静态串补 `esc()`；诊断输出只记 status+path |
| `web/index.html`, `web/motion.js`, `web/style.css` | 全文 | §7.4（无发现） | — | 无内联脚本、无 DOM XSS sink |
| `scripts/check_annotations.py` | 347-400, 513-583 | M-11 | 缺陷 / 中等 | 空判定面 `sys.exit(2)` |
| `scripts/check_skill_agents_consistency.py` | 11, 20, 196-204, 219-226, 257-265 | M-12, §7.2 | 缺陷 / 中等 | 检查 3 告警升级为 errors；缺目录分档对齐 rc=2 文案 |
| `scripts/agent_hook_guard.py` | 100-101, 266-270, 358-372 | M-13 | 安全 / 中等 | 边界集合纳入 `|`；补 self-test 用例 |
| `scripts/douyin_live_recorder_standalone.py` | 119-148, 119-121, 1811, 1884-1886, 2007, 2008, 2049, 2072, 2224, 2382 | M-21, M-22, L-01 | 缺陷 / 中等 | 回灌看门狗 + 登记差异；日志轮转加锁并订正注释 |
| `scripts/run_gates.py` | 33-35, 542-559, 701-708 | §7.2 | 观察 | pytest warnings 兜底超时退 1 与文件头「超时按 2」分档不一致（非假绿，待仲裁） |
| `scripts/compile_po.py` | 177-179 | L-07 | 缺陷 / 轻微 | `.tmp` 加 try/finally 清理 |
| `scripts/sync_version.py`, `scripts/report_bundle_size.py`, `scripts/smoke_test.py` | 40/57/74, 234, 379/445 | L-07 | 缺陷 / 轻微 | 写盘改 `tmp+os.replace` 并校验 `rel_path` 不越界 |
| `scripts/sync_metadata.py` | 235, 250, 261 | §7.2 | 质量 / 轻微 | `regenerate()` 返回值被丢弃、`check()` 重复执行 |
| `scripts/_ci_web_smoke.sh`, `scripts/spike_arm64_static_ffmpeg.sh`, `scripts/check_*.py`（其余）, `scripts/extract_i18n_strings.py`, `scripts/smoke_web.json`, `typings/execjs/*.pyi` | 全文 | §7.4（无发现） | — | `set -e` 2/2 达标、fail-closed 齐备、存根同步 0 处不同步 |
| `.github/workflows/ci.yml` | 6, 41, 83-90, 677 | L-03, L-09 | 质量 / 轻微 | 订正 FastAPI 措辞；核对 PR 触发与 required check |
| `.github/workflows/build-release.yml` | 405-415, 667 | M-20 | 质量 / 中等 | 注明注入值退为回退基线 |
| `.github/workflows/issue-translator.yml` | 31-34 | L-08 | 缺陷 / 轻微 | 补 `timeout-minutes: 10` |
| `.github/workflows/docker-publish.yml`, `trivy.yml`, `actions/retry/action.yml`, `ISSUE_TEMPLATE/*` | 全文 | §7.4（无发现） | — | 权限按需提升、密钥 step 级引用，0 处越权 |
| `tests/conftest.py` | 18 | L-12 | 质量 / 轻微 | 注释改指向 AGENTS.md 现有条目 |
| `tests/test_regression_gates.py` | 270, 304-305, 660-666 | M-14 | 逻辑 / 中等 | 文本判据改 AST `ast.Call` |
| `tests/test_agent_hook_guard.py` | 467-492 | M-15 | 质量 / 中等 | 接线锁改读可跟踪清单 |
| `tests/test_async_http.py` | 560-574 | L-11 | 质量 / 轻微 | 补 `content=` 分派断言 |
| `tests/test_test_hygiene.py` | 8-9, 1595-1624, 1630, 1660, 1736, 1755 | M-16, L-03, L-11 | 逻辑 / 中等 | helper 前缀增补 `_` 变体；债务表下调 |
| `tests/test_regression_main.py` | 147, 160, 182, 185, 1193, 1196 | M-16（对照） | 逻辑 / 中等 | 4 个用例实有判据，随判定器修正解除债务 |
| `tests/test_config_io_readonly.py` | 40 | L-11 | 质量 / 轻微 | 改绑 `config_io.os` shim |
| `tests/test_regression_spider.py` | 714, 725 | L-11 | 质量 / 轻微 | 异常类型收窄为 `ValueError` |
| `tests/test_regression_utils.py` | 268-269, 302-303 | L-11 | 质量 / 轻微 | 记录器改 fixture 局部 list |
| `tests/test_web_api.py` | 2504-2514, 2522-2533 | L-11 | 质量 / 轻微 | 补 mock `islink` 的离线等价覆盖 |
| `tests/test_config_io_backup.py`, `tests/test_config_io.py`, `tests/test_config_io_update_file.py`, `tests/test_i18n_migration.py`, `tests/test_ci_pytest_env_parity.py`, `tests/test_spider_hardening.py`, `tests/test_build_exe.py`, `tests/test_ffmpeg_install.py`, `tests/test_start_record_command_golden.py`, `tests/test_ws_client.py`, `tests/test_scripts_error_paths.py`, `tests/test_web_config_secret_mask.py`, `tests/test_stream_select.py`, `tests/test_utils.py`, `tests/golden/start_record_commands.json` | 抽读区间 | §7.4 / L-11 | 部分轻微 | 假绿形态实测 0 处；golden 结构与判据同步 |
| `tests/frontend/test_motion.mjs` | 78 | L-05 | 逻辑 / 轻微 | 恒等三元改 `return null` |
| `tests/frontend/test_regression_gates.mjs` | 1107-1108, 1162, 1188, 1253 | L-11 | 质量 / 轻微 | 2 条 M-85 skip 在包装层登记 sanctioned |
| `tests/frontend/test_auth_reauth.mjs`, `test_quality_ui.mjs`, `test_motion.py`, `test_auth_reauth.py` | 全文 | §7.4（无发现） | — | 每个 `test()` 均含实断言，0 处恒真 |
| 其余 `tests/test_*.py`（约 130 个文件，见附录 A） | 仅 Grep 全量扫描 | §7.4（无发现） | — | 模式扫描覆盖，未逐行精读 |

---

## 7. 结论性核对

### 7.1 上一轮遗留项核对（对照 `CODE_REVIEW_2026-10-30.md` 与 `_FIX.md`）

| 上轮项 | 当前真实状态 | 依据 |
| --- | --- | --- |
| S-04/S-06/S-07、M-08（favicon 任意文件读）、M-09、M-10、M-12、M-13、M-26、M-34 | **已处置** | 本轮 A10 区实读：26/26 路由经鉴权、`_is_within`/`realpath` 路径穿越 0 处；`_SECRET_KEYS` 已含 `sid`/`sessdata`/`sig`/`jwt` 等补录项（`utils.py:998-1081`） |
| M-17 嗨秀/嗨嗨硬编码默认 accessToken（待用户裁定） | **仍存在** | `src/spider.py:5935`/`:5937` 形态仍在，本轮 L-04；`_FIX.md` §1 记录提问未获答复 |
| M-23 `.zcode/config.json` 与 `config/URL_config.ini` 跟踪态（待用户裁定） | **仍存在** | 本轮快照 `git ls-files` 473 文件，`.zcode/` 1 文件、`config/URL_config.ini` 15 行仍在跟踪；并入 M-17 |
| L-02 全族（A 类 JSON 拼接 6 处 + B 类 URL 未编码 38 处，暂缓） | **仍存在（本轮 M-02 报 11 处代表）** | `spider.py:4553`/`:6523`/`:6106` 等实读；`_FIX.md` §3 以「需真机验证」暂缓，理由有效 |
| L-04③ `build_exe.py` PyInstaller `subprocess.run` 无 timeout（请用户手工补） | **仍存在** | `build_exe.py:307` 实读，本轮 L-08；`_FIX.md` §3 记录被钩子误拦 |
| L-09 结构度量族（超长函数 15 个 / 深嵌套 30 处 / 多形参 10 处） | **仍存在** | 本轮 AST 预扫 13/29/10，本轮 L-01；属备案重构项 |
| M-24 standalone 孪生漂移（上轮 P3 待办） | **仍存在且新增形态** | 本轮 M-21 发现「看门狗未回灌且差异未登记」、M-22「日志轮转注释矛盾」，为新增子项 |
| 5 处悬空回归锁引用 | **基本已清，新增 1 处不同形态** | 本轮 A14 区「回归锁悬空引用 0 处」；A13 发现 `tests/conftest.py:18` 指向 AGENTS.md 不存在的具名条目（本轮 L-12） |
| L-11 残留 spike `set -e` 静默中止 / L-10 前端三项 / L-12①② Qt 两项 | **本轮未复核** | 分区代理未在对应区立项；列入附录 A 覆盖边界与 §9 未执行项，不宣称已修 |

### 7.2 子代理断言被主控推翻 / 修正（方法学透明）

| 子代理断言 | 主控复核实测 | 处理 |
| --- | --- | --- |
| A2 区把 `main.py:1464-1483` 标为「`run_script` 是否 `shell=True` 待 A1 确认」，隐含命令注入可能 | 主控实读 `src/notify.py:193-273` 与 A8 区独立判断：`shlex.split` + argv `Popen`、无 `shell=True`；全仓生产 `os.system(` = 0、`shell=True` 16 处全为注释 | **不采纳「命令注入」**，改判「参数损坏」，落在 M-03（严重度维持中等） |
| A6 区 `[越界]`：`_SECRET_KEYS` 未收录 `xy-common-params` 及 `xy-*` 类自定义头键名，故日志过码也抹不掉 | 主控实读 `src/utils.py:998-1081`：`"sid"`（:1014）、`"session"`、`"authorization"` 等已在表内，复合值 `platform=iOS&sid=...` 中的 `sid=` 形态可被掩；仅「头名 `xy-common-params` 本身未入表」成立 | **部分不采纳**：不单列缺陷，降为 L-15 的「补 `xy-*` 头名登记」建议 |
| A8 区：「全仓 `shlex.quote` 实测 0 处」 | 主控干净范围复跑 `shlex.quote=5`，Grep 定位 `tests/test_notify.py:43/72/83`、`tests/test_notify_script_guard.py:494`——全在测试侧 | **口径修正**：生产代码 0 处成立，`M-03` 结论不变 |
| A8 区 [1]：「若调用方证实未过码则升为严重」 | 主控：未构造含 token URL 异常穿透到 `PlayURL.log` 的运行实证；`logger.exception` 全仓 2 处（`spider.py:809/1005`）已定位 | **不升格**，采纳为 M-01 中等，前置条件写进 §9 未执行项 |
| A1 区 [3]「finally 漏删 ffmpeg stderr 临时文件」 | 主控：A2 区复核 finally 已完整回收进程与状态，仅临时文件残留 | **降级**为 L-07 轻微 |
| A2 区 [1]「推送线程 `.start()` 未捕获 RuntimeError 冒泡吞掉本轮录制」 | 主控：静态形态存在（`main.py:3985` 为 `).start()`），但触发需线程数打满，代理自标「待确认」 | **采纳为待确认观察**，不进 M 组，写入 §6 `main.py` 行 |
| A5 区 [2]「`is_live` 未归一 bool」、A7 区 [2]「clean_name 不可达分支」、A7 区 [3]「SRT 小时位」 | 主控校准探针逐条 PASS，但均需特定 API 返回类型 / ≥100 小时录制 / 注释前提 | **降级**为 L-05 / L-06 轻微 |
| A3 区 [8]「浮动 action 属刻意设计待仲裁」、[12]「ci.yml 仅手动触发待仲裁」 | 主控：两处文件头均有「刻意保留 / QUARANTINED」出处，符合简报白名单规则「需仓内出处」 | **豁免**，落 L-09 备案 |
| A3 区 [10]「env 布尔内联，唯一入口是否覆盖环境变量待主控界定」 | 主控：AGENTS.md 的「唯一入口」口径针对配置文件；env 不属该口径 | **降级**为 L-13 轻微 |
| A11 区 [6]「缺目录退 1 与文件头 rc=2 契约不符」、[7]「pytest warnings 超时退 1」 | 主控：两者 rc 均非 0、无假绿；文件头分档文案确有出入 | **降级**为备案，L-07 / §7.2 登记，不进 M 组 |
| AST 预扫 117 处线索（裸 `open()` 12、`subprocess` 近似无 timeout 27、`except: pass` 36、疑似未用 import 29、超长函数 13） | 分区实读逐条核销：裸 `open()` 4 处为长期持有句柄并有配对回收；`Popen` 无 timeout 由 `communicate(timeout)`/看门狗收口；`except: pass` 79 处带归因注释；未用 import 多为重导出/测试锚点 | **大面积不采纳**（扫描命中 ≠ 缺陷），仅保留 `itemgetter` 1 处真未用（L-05）与 `build_exe.py:307` 1 处真缺 timeout（L-08） |
| A13 区 [1]「`:270`/`:304-305` 是否已被注释喂饱待确认」、A12 区 [03]「控制字符能否真正连到非官方主机」、A1 区 [2]「spider 是否返回 None」 | 主控未做运行态复现 | **保留「待确认」标注**，不删不改，见 M-05 / M-06 / M-14 与 §9 |

### 7.3 审查期内被并发工作包修复的项

**无。** 起始 `git status --porcelain` 0 条 → 定稿 1 条，且该条即本报告（`?? docs/worklog/CODE_REVIEW_2026-11-04.md`）；`review_scope.py --check` 在成稿前（18:34:18 → 19:42:47）与成稿后（19:51:10，跟踪文件口径）均报 `changed=0 added=0 removed=0`；`repo_review_snapshot.py verify` 报 `ADDED 1` 且被 `--allow-added` 精确允许、`UNEXPECTED_ADDED 0`、`RESULT PASS`。审查期内**无任何源文件被改动**，行号以各条目标注时刻为准。

### 7.4 全仓健康度横向结论（按面给实测读数）

| 面 | 实测读数与判据 | 结论 |
| --- | --- | --- |
| 命令注入 / 代码执行 | 生产 `os.system(`=0、`shell=True`=16（全为注释）、`eval(`/`exec(` 命中仅 Qt `.exec()` 与白名单 `x-bogus.js`、`pickle.loads`=0、`yaml.load(`=0 | 成立；ffmpeg/通知/node 一律 argv 列表 |
| XSS / CSRF / 鉴权 | `web/app.js` `innerHTML` 15 处逐处实读、服务端可控数据未转义 0 处、`esc()` 63 次；`web_api.py` 26 条路由 26/26 经 `auth_middleware`；GET 状态变更 0 处；路径穿越 0 处（`realpath`+`_is_within`+`_safe_download_filename`） | 成立；同源校验无 token 但 Bearer 在 Authorization 头 |
| 凭据 / 脱敏 | 硬编码真实凭据 0 处；`mask_credentials` 218 处调用；`_SECRET_KEYS` 覆盖 sid/token/cookie 等；Web 写侧三重拒绝 + `'***'` 掩码跳过 | 主体成立；**例外**为 S-01（跨 host 头外带）与 M-01（异常文本口径不统一） |
| 反序列化 / 协议边界 | `pickle`/`yaml.load` 0；`_tars.py` 10/17 边界读点有 `_need` 保护（7 处缺口 → M-04）；protobuf 字段号与 `.pyi` 同步 0 处不同步 | 基本成立，TARS 有明确缺口 |
| 并发与资源 | 模块级 `asyncio.Lock` 0 处；threading 锁块内 `await` 0 处；队列/缓冲/日志留存全部有界 | 成立；**例外** M-08（标志位无锁）、M-09/M-10（无上限增长） |
| 静态门禁 | 7 项只读门禁 rc 全 0；AST 257 文件 0 失败；black/isort `--check` 0 | **当前全绿**；但 M-11/M-12/M-13/M-14/M-16 暴露判定面空转、告警降级、守卫绕过、断言可被注释喂饱 |
| 同源性 | pyproject ↔ requirements 18/18 差集 ∅；JS 钉定 5/5；`uv.lock`/egg-info version 4.7.0 同步；路由 26 条与硬集合一致 | 成立；例外为 M-17（ignore 黑名单）、M-20/M-24（注释与实现） |

---

## 8. 改进建议与修复优先级

### 8.1 优先级矩阵（按「风险 × 修复成本」排序）

| 优先级 | 项 | 风险若不动 | 修复成本 | 说明 |
| --- | --- | --- | --- | --- |
| **P0** | S-01 | 用户真实会话 sid 可被 302 带往任意主机；防线时序失效 | 中 | 统一出站入口改手工逐跳 + 跨源剥头；须真实 URL 增量验证 |
| **P0** | M-17 | 新增 config 凭据文件可入库并进公开镜像 | 低 | 两份 ignore + Dockerfile 三处，一次性收口 |
| **P0** | M-11 / M-12 / M-13 | 门禁可在空判定面/告警降级下假绿；删除守卫可被 `|` 绕过 | 极低 | 三条均为单点小改 + 各补 1 条回归锁，建议同批落地 |
| **P1** | M-19 / M-01 / M-04 / M-07 / M-08 | 明文授权码、日志凭据、畸形帧异常类型、GUI 启动崩溃、重复关闭事件 | 低～中 | 前四项为单点修复；M-01 需同步调整按整行断言的用例 |
| **P1** | M-02 / M-03 / M-18 / M-21 / M-23 / M-24 | 请求字节形态、参数损坏、发布包污染、standalone 挂起、补刀死代码、TLS 降级可被改回 | 低～中 | M-02/M-21 按 DoD 需真机/真实 URL 验证，故不进 P0 |
| **P2** | M-05 / M-06 / M-09 / M-10 / M-14 / M-15 / M-16 / M-20 / M-22 | 特定条件下行为错误、资源增长、判定器误判、文档误导 | 低 | 多为「补一个上限/一个前缀/一行注释」，可与 P1 合并成一批 |
| **P3** | L 组 16 族 | 可维护性、日志噪声、备案性观察 | 低～高 | 结构度量族（L-01）与重复代码族（L-02）建议随下次重构顺势处理，不单独造大 diff |

### 8.2 流程性建议（可落地成门禁/脚本，不停留在「加强意识」）

1. **给所有 `--check` 型门禁加「判定面非空」前置**：统一封装 `require_nonempty(scanned, label)`，空则 `sys.exit(2)`；把 `check_annotations.py` / `check_equivalence()` 纳入，并补一条「传不存在 root → rc=2」的用例（对应 M-11）。
2. **门禁「告警即失败」同回路**：`check_skill_agents_consistency.py` 检查 3 的 `warnings` 改 `errors`；新增门禁评审时把「存在 `warnings` 且 `return 0` 分支」列为静态检查项（对应 M-12，对齐 `AGENTS.md` 第 152 行）。
3. **删除守卫 self-test 扩形**：`agent_hook_guard.py` 的 `block_cases` 增列 `logs|`、`logs&`、`logs;` 等边界形态，并加一条机检断言「边界集合 = 语句切分字符集 ∪ 引号/空白」（对应 M-13）。
4. **回归锁判据统一走 AST**：新增 `scripts/check_assertion_shape.py`（或扩展 `test_test_hygiene.py`），拒绝 `src.count("symbol()")`、`"code" in src` 这类文本判据，改 `ast.Call` / `ast.get_source_segment` 去注释（对应 M-14、M-16）。
5. **CI 跳过可见性**：把 `pytest.skip` 按「平台/依赖/资产缺失」分类登记，包装层对非平台类 skip 判红或要求 sanctioned 清单（对应 M-15、L-11）。
6. **跨源出站的结构锁**：新增用例断言「`async_req` 的 `follow_redirects` 默认值 + 跨源重定向后自定义头集合为空」，防止 S-01 回归；把 httpx 版本钉进依赖注释。
7. **standalone 孪生对账**：把「主线防线编号 → standalone 符号存在性」做成 JSON 清单 + 机检脚本，差异必须附「刻意不回灌及原因」字段（对应 M-21，闭合 `CODE_REVIEW_2026-10-04.md` 自承未落地的那一项）。
8. **凭据目录级排除的机检**：新增用例枚举 `config/` 下所有非模板文件，断言均被 `.gitignore` / `.dockerignore` / `Dockerfile` / 发布 zip 四通道排除（对应 M-17）。

### 8.3 可复跑判据清单（命令 + 期望值 + 当前实测值）

```bash
# 工作目录：D:/DouyinLiveRecorder；解释器一律 .venv/Scripts/python.exe
# 1. 工作区干净（期望 0；当前实测 0）
git status --porcelain | wc -l
# 2. HEAD 无冲突块（期望 rc=1 且 0 命中；当前实测 rc=1 / 0 块）
git grep -c '^<<<<<<< ' HEAD
# 3. 全量 .py 可解析（期望 0；当前实测 py_files=257 / ast_parse_errors=0）
.venv/Scripts/python.exe -c "import ast,pathlib; ..."   # 见本轮 %TEMP% 探针口径
# 4. 依赖同源（期望差集 []；当前实测 18/18 / []）
.venv/Scripts/python.exe -c "import tomllib,re,pathlib; ..."
# 5. JS 签名脚本钉定（期望 5/5 True；当前实测 5/5）
.venv/Scripts/python.exe -c "import hashlib,pathlib; from src.utils import _JS_SHA256_EXPECTED as T; d=pathlib.Path('src/javascript'); [print(n, hashlib.sha256((d/n).read_bytes()).hexdigest()==e) for n,e in sorted(T.items())]"
# 6. Web 路由数（期望 26；当前实测 26）
# grep -c '@_route(app, \[' src/web_api.py
# 7. 前端 XSS sink（期望 innerHTML=15 / esc>=15；当前实测 15 / 63）
# grep -c '\.innerHTML\s*=' web/app.js
# 8. 生产面危险原语（期望 0；当前实测 os.system=0 / pickle.loads=0 / yaml.load=0；
#    shell=True=16 含注释、_create_unverified_context=5 含注释、logger.exception=2 即 M-01 位点）
# 9. 只读门禁真实 rc（期望全 0；当前实测全 0，见 §1.2 第 3 条）
.venv/Scripts/python.exe scripts/check_annotations.py > "$TEMP/ann.log" 2>&1; echo rc=$?
.venv/Scripts/python.exe scripts/compile_po.py --check > "$TEMP/po.log" 2>&1; echo rc=$?
.venv/Scripts/python.exe scripts/check_skill_agents_consistency.py > "$TEMP/skill.log" 2>&1; echo rc=$?
# 10. 空判定面不得假绿（期望 rc=2；当前实测 rc=0 —— M-11 未修）
.venv/Scripts/python.exe scripts/check_annotations.py --root <不存在的目录>
# 11. 删除守卫边界（期望两条都拦下；当前实测 'rm -rf logs' 拦下、'rm -rf logs|cat' 放行 —— M-13 未修）
.venv/Scripts/python.exe -c "from scripts.agent_hook_guard import check_bash_command as c; print(c('rm -rf logs'), c('rm -rf logs|cat'))"
# 12. 只读自证（跟踪文件口径期望 changed=0 added=0 removed=0；当前实测全 0，19:51:10）
.venv/Scripts/python.exe .agents/skills/code-review-lifecycle/scripts/review_scope.py --root . --check <基线 JSON>
# 12b. 快照口径（期望 ADDED=1 且 UNEXPECTED_ADDED=0 / PASS；当前实测 RESULT PASS，唯一新增为本报告）
.venv/Scripts/python.exe .agents/skills/code-review-lifecycle/scripts/repo_review_snapshot.py verify \
  --manifest <snapshot 目录>/manifest.json --allow-added "docs/worklog/CODE_REVIEW_2026-11-04.md"
```

> 判据 10/11 的「当前实测」即本轮发现，整改后应分别变为 `rc=2` 与「两条均返回 `R-CLEAN-SCOPE`」。判据 1–9 复制粘贴即可复跑；第 3/4/8 条的完整内联脚本落在本轮 `%TEMP%` 探针中（收尾已删除，按 §2.2 口径可重建）。

---

## 9. 总结与后续行动项

**结论**：本轮对 285 个源文件、约 13.4 万行完成只读静态审查，形成 1 条严重、24 条中等、16 族轻微（同族合并后）结论。仓库主干的录制、选源、鉴权、钉定、协议解析等核心防线经逐行核对成立，静态门禁 7 项 rc 全绿、AST 0 失败、JS 钉定 5/5、依赖同源差集 ∅；风险不集中在「功能坏了」，而集中在 **① 出站重定向的防线时序（S-01）**、**② 门禁/守卫/回归锁的判定面可空转或被绕过（M-11～M-16）**、**③ 主线与镜像面（standalone、注释、ignore 清单）的不同步（M-17～M-24）**。这三类共同特征是「修复成本低、不修则让所有绿灯失去意义」，建议按 §8.1 的 P0 批次优先收口。

**行动项（建议按序执行）**

1. 【P0】修复 S-01：统一出站入口默认关闭自动跟随、跨源剥离自定义凭据头、短链解析改手工逐跳并落实注释承诺的 `headers.pop`；随后用真实 XHS 短链 / 咪咕 CDN 做增量验证，并补结构锁用例。
2. 【P0】同批收口 M-17、M-11、M-12、M-13：两份 ignore 改目录级排除 + Dockerfile 显式 COPY；三个判定面/守卫各补一行与一条回归锁。
3. 【P1】处理 M-19、M-01、M-04、M-07、M-08（安全与稳定性单点修复），再按 M-02 / M-21 的真机验证条件安排平台解析与 standalone 回灌批次。
4. 【P2】处理 M-05/M-06/M-09/M-10/M-14/M-15/M-16/M-20/M-22 与 §8.2 的流程性门禁；L 组随重构顺势处理，其中 L-04 的嗨秀常量与 M-17 的 `URL_config.ini` 跟踪态**仍需用户裁定**（上轮提问未获答复）。
5. 【P3】按本仓《只读审查生命周期》的整改分支流程逐条回写处置状态与复跑判据，同步 `CODE_WIKI.md`/`CODE_WIKI_EN.md` 更新日志与当日 `.workbuddy/memory/` 日志。

**未执行项声明（逐条，不写成「应当没问题」）**

| 未执行 | 原因 | 交回动作 / 作为哪些整改的验收前置 |
| --- | --- | --- |
| 未跑全量 `pytest` / `pytest --cov` / 覆盖率门禁 | 只读硬约束：会写 `.pytest_cache`/`.coverage`，且本轮为静态审查而非整改验收 | 整改轮在最后一次编辑后跑 `scripts/run_gates.py` + 全量 pytest（0 警告）+ `check_coverage.py`；是 M-02/M-21/L 组全部代码改动的验收前置 |
| 未跑 mypy / basedpyright / 平台双跑 | 会生成缓存目录；且工具版本与 CI 常量未联网核对 | 整改轮按 `AGENTS.md`「格式化命令」跑三平台 mypy 与 basedpyright（0 error/0 warning） |
| 未做端到端真机 / 真实 URL 验证 | 本轮无外网与活房间条件，且只读审查不触发录制链 | S-01、M-02、M-05、M-21、M-23 的修复涉及出站请求字节、短链跳转、ffmpeg 挂起与 VBS 进程树，必须按 DoD 第 2 步用真实 URL 增量验证 |
| 未联网核对 `ci.yml` consts 与本地工具版本 | 本轮不联网；`ci.yml` 现仅手动触发 | 报告 §2.3 已标「本地口径」；下次手动触发 CI 时核对 black/isort/mypy/pytest 常量 |
| 未对 `tests/` 约 7.4 万行逐行精读 | 按仓库 Skill 口径为「模式扫描全覆盖 + 关键文件逐行抽读」 | 两区合计精读/抽读约 1.0 万行，其余约 6.9 万行仅由 Grep 判据覆盖，边界见附录 A；若需逐行结论应另立一轮 |
| 未构造 302 / 畸形帧 / STARTTLS 失败的运行态复现 | 只读审查不发起网络与真实进程 | S-01、M-05、M-06、M-19、M-23 的「待确认」标注在正文保留，整改轮需补离线复现用例后再关闭 |

---

## 附录 A：方法与覆盖的诚实边界

- **逐行精读覆盖**：14 个分区代理合计约 6.0 万行生产代码逐行读满——`main.py` 全 5517 行（两区）、`src/spider.py` 全 7095 行（两区）、`build_exe.py` 2641 行、根入口与配置约 5400 行、`src/` 网络/录制/工具三簇约 1.66 万行、GUI 与托盘约 6095 行、Web 前后端约 6526 行、`scripts/` 约 8730 行、平台/协议/JS/前端测试约 7450 行。每个分区均回传「覆盖确认」并声明实际切断点。
- **模式扫描覆盖**：257 个 `.py` 全量 AST 解析与 8 类 AST 判据；全仓 Grep 判据（注入原语、脱敏、重定向、XSS sink、路由、异常形态、跳过形态、落盘形态、硬编码凭据/路径、回归锁引用）；473 个跟踪文件 sha256 基线；`tests/` 156 个 `.py` 的全量判据扫描。
- **未逐行精读**：`tests/` 约 130 个文件、约 6.9 万行仅由 Grep 模式覆盖（A13 区 77 文件 26718 行中精读/抽读约 4950 行；A14 区 77 文件 42906 行中精读/抽读约 4967 行）；`docs/**` 与根 `*.md` 正文、`i18n/*` 正文、`crypto-js.min.js` 正文、`douyin_pb2.py` 描述符长行、`x-bogus.js` 3 处混淆长行（Read 按 2000 字符截断）按 §2.1 排除项处理。**「未发现」不等于「不存在」**，这些区域的结论以模式扫描为限。
- **并发限制**：审查期内工作区 0 漂移（基线 18:34:18 → 19:42:47），无并发工作包；报告行号以各条目标注时刻的实读为准，复核前请先跑 §8.3 判据 1/2/12 确认基线未变。
- **脱敏**：报告中所有口令 / Cookie / token 仅以键名或脱敏样例出现，未包含任何真实凭据值；`src/javascript/liveme.js` 的算法常量仅描述形态，未抄录完整值。
