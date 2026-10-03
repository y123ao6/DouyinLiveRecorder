# better-harness 证据采集口径（纯参考段）

> 本文件是**纯参考证据**，不含祈使式编码约定；「必须怎样、不得怎样」的约束仍留在 [`AGENTS.md`](../../AGENTS.md)。
> 用途：固化一条可复核的 better-harness 会话证据采集口径，避免后续复盘把「空集」当成「项目无活动」的事实。
> 隐私红线：本文件**只记口径与目录特征**，不落任何用户主目录绝对路径，也不落 `~` 前缀形式的路径。

## 一句话口径

在 Qoder CN 发行版上采集会话类证据（`session-analysis` / `harness evidence-bundle`）时，**必须显式传入 provider 主目录参数**，指向本机**带 `-cn` 后缀的那个真实用户主目录**下的 Qoder 资产根；否则命令会解析到一个不存在的默认目录，把会话通道报成空集而报告表面仍全绿。

## 为什么会踩空集（默认解析落错目录）

- `session-analysis` 的 Qoder 平台在解析作用域时，provider 主目录取 `options.home ?? options["qoder-home"] ?? "~/.qoder"`（见插件包 `scripts/session-analysis/platforms/qoder.mjs` 的 `resolveScope`）。
- 默认值 `~/.qoder` **不带 `-cn` 后缀**；本机真实的 Qoder 资产根目录是带 `-cn` 后缀的那一个。默认解析出的目录在本机根本不存在，于是所有来源根 `exists=false`、`eligibleSessions=0`，报告却不会因此报错——这就是「把空集当事实」的成因。
- 项目会话根与执行日志根都拼在这个主目录之下（`<home>/projects/<workspaceSlug>`、`<home>/logs/runs`、`<home>/logs/sessions/<workspaceSlug>`），主目录一旦落空，这三者一起消失。

## 参数落点（两个命令的入参名不同）

| 命令 | 显式主目录参数 | 说明 |
| --- | --- | --- |
| `session-analysis sources/sessions/...` | `--home <带 -cn 后缀的 Qoder 资产根>` | 也接受 `--qoder-home`，二者等价 |
| `harness evidence-bundle` | `--qoder-home <同上>` | 该子命令**只认 `--qoder-home`**，传 `--home` 会以「unknown argument」退出 |

## 有界发现实测（2026-10-02 本机复跑，作为口径佐证）

- **默认解析**（不传主目录）：`session-analysis sources` 读出的 `scope.home` 为不带 `-cn` 后缀的目录，`sources[]` 中每一条 `exists=false`（0 根存在），会话通道为空。
- **修正解析**（显式传入带 `-cn` 后缀的主目录）：同一工作区
  - 存在的来源根数 = **5**（项目会话根、执行日志根 `logs/runs`、执行事件根 `logs/sessions/<slug>` 等均 `exists=true`；仅 `audit`、`home-sessions` 两个可选根本机确无，属正常）；
  - 会话数 = **58**（`session-analysis sources` 顶层 `sessions[]` 去重后 58 个 sessionId）。
  - 已核实带 `-cn` 后缀目录下的 `projects/<workspaceSlug>`（项目会话根）与 `logs/runs`（执行日志根）确实存在。

## 已知偏差：lead 分析面仍按默认主目录取样

同一次 `harness evidence-bundle`（带 `--qoder-home` 修正）跑出的 `status=complete` 证据包内，**两个通道对会话规模的读数不一致**：

- **Session Evidence 通道**（`lanes.sessionEvidence.data.scope`）随 `--qoder-home` 修正：`eligibleSessions=58 / selectedSessions=58`。
- **lead 分析面**（`lead.data.summaryFacts`）不随该参数变化：仍报 `evidenceMode=session-limited`、`Source roots: 0 of 6 enabled roots exist`、`eligibleCount=0 / analyzedCount=0`，其 `sourceFingerprint` 也不因主目录修正而改变。

**因此的取数口径**：判定会话规模、重复工作流、验证闭环、经验沉淀这类依赖会话数量的结论时，**一律以 Session Evidence 通道的计数（如上例 58）为准，不得采信 lead 分析面的 0**。把 lead 面的 0 当事实，会把「有数十个会话」误判成「项目无活动」。

补充：资产清点面（Agent Customize / lead 的 `aiAgentPractice.coverageRows`）会因主目录修正而**纳入用户级 / 插件级条目**（数量远大于项目级，如 Skills 会跳到几十条并出现插件缓存路径）；判定项目自身规模时只取标注 **Project 作用域**的行。

## 复核命令（把 `<CN_QODER_HOME>` 换成本机带 `-cn` 后缀的 Qoder 资产根，勿写进仓库）

```powershell
$bh = "<better-harness 插件包>/scripts/better-harness.mjs"
# 1) 有界发现：先验证每个根的 exists 状态与会话数
node $bh session-analysis sources --platform qoder --workspace <target> --home <CN_QODER_HOME>
#   判据：存在的根数 > 0 且 sessions[] 会话数 > 0
# 2) 整包：确认 status=complete，并按上节以 Session Evidence 通道计数为会话规模口径
node $bh harness evidence-bundle --platform qoder --workspace <target> --qoder-home <CN_QODER_HOME> --format json --canvas-out <run>/canvas.json --replace-canvas
```

> `--canvas-out` 重写已存在的 `canvas.json` 会报 `CANVAS_OUTPUT_EXISTS` 并使 lead 通道 unavailable、整包 `status=failed`；重跑须带 `--replace-canvas`。
