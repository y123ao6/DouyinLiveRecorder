# DouyinLiveRecorder 代码改动记录

## v4.0.8-dev (2026-05-17) — 项目基础设施完善

### 配置与构建文件

| 文件 | 改动 | 说明 |
|------|------|------|
| `requirements.txt` | 重构 | 添加版本约束和分类注释，补充每个依赖的用途说明 |
| `pyproject.toml` | 修正 | 移除无效的 `[project.entry-points]` 空字典；`tool.black` 排除规则新增 `node/`、`ffmpeg/`、`downloads/`、`logs/` 目录；`classifiers` 添加 `MacOS X`/`Win32`/`X11`/`Python 3.13`；`[optional-dependencies]` 合并 `all` 到 `gui` |
| `Dockerfile` | 🔴 关键修复 | **修复运行时阶段缺失 Node.js 的严重 Bug**（原多阶段构建仅在 builder 安装 Node.js，运行阶段缺少 PyExecJS 运行时导致所有平台签名脚本无法执行） |
| `docker-compose.yaml` | 修正 | 修复 `network_mode: bridge` 与 `networks:` 配置块的冲突（移除内联 `network_mode`，统一使用 `networks:` 声明）；healthcheck 改用 `pgrep` 检测主进程；`start_period` 延长至 15s |
| `.gitignore` | 重构 | 消除两个重复的"项目专用"区块；移除 `*.exe`/`*.dll`/`*.cmd`/`*.bat`/`*.vbs` 破坏性通配符（改用 `ffmpeg/*.exe` 等精确路径）；新增 `uv.lock`、`*.orig`、`*.desktop`、`*.lnk`、`index.html`；按 13 个功能区块重组织 |
| `.dockerignore` | 完善 | 新增排除 `gui.py`/`demo.py`/`ffmpeg_install.py`/`StopRecording.vbs`/`index.html`（Docker 无头环境不需要这些文件）；新增 `ffmpeg/`/`.python-version`/`uv.lock` 排除规则 |

### 文档文件

| 文件 | 改动 | 说明 |
|------|------|------|
| `README.md` | 更新 | 修正过时 GUI 入口文件名引用；修正配置区块名 `[settings]` → `[录制设置]`；修正配置项名匹配实际 config.ini；移除多余的 `</div>` 闭合标签；新增 Docker Node.js 常见问题解答；新增 `.dockerignore`/`.gitignore` 到项目结构树 |
| `CODE_WIKI.md` | 重写 | 基于最新代码分析重写架构文档：修正 GUI 入口文件名引用、补充 room.py 新增函数、补充 spider.py 平台函数列表、补充 Docker 构建说明、补充版本历史表 |
| `CODE_CHANGES.md` | 重写 | 本文件，记录历史变更和本次基础完善 |

### GUI 文件

| 文件 | 改动 | 说明 |
|------|------|------|
| `gui.py` | 美化 | 设计现代化深色主题 GUI：新增 `Colors`/`CardFrame`/`GradientBanner`/`StatusIndicator`/`ModernTextWidget`/`SystemTray` 组件；补充 5 个缺失的 ttk 样式配置；修复 CardFrame 背景色未生效；添加跨平台字体回退（`_resolve_font`）；ModernTextWidget 添加 `<Configure>` 自适应尺寸；清理 `scrolledtext` 死代码 |

---

## v4.0.7 (2025-10-24)

- 修复抖音风控无法获取数据问题
- 新增 soop.com 录制支持
- 修复 bigo 录制

## v4.0.6 (2025-01-27)

- 新增淘宝、京东、faceit 直播录制
- 修复小红书直播流录制以及转码问题
- 修复畅聊、VV星球、flexTV 直播录制
- 修复批量微信直播推送
- 新增 email 发送 ssl 和 port 配置
- 新增强制转 h264 配置
- 更新 ffmpeg 版本
- 重构包为异步函数

## v4.0.5 (2024-11-30)

- 新增 shopee、youtube 直播录制
- 新增支持自定义 m3u8、flv 地址录制
- 新增自定义执行脚本，支持 python、bat、bash 等
- 修复 YY 直播、花椒直播和小红书直播录制
- 修复 b 站标题获取错误
- 修复 log 日志错误

## v4.0.4 (2024-10-30)

- 新增嗨秀直播、vv星球直播、17Live、浪Live、SOOP、畅聊直播、飘飘直播、六间房直播、乐嗨直播、花猫直播等 10 个平台
- 修复小红书直播录制，支持小红书作者主页地址录制直播
- 新增支持 ntfy 消息推送，以及新增支持批量推送多个地址
- 修复 Liveme 直播录制、twitch 直播录制
- 新增 Windows 平台一键停止录制 VB 脚本程序

## v4.0.3 (2024-10-05)

- 新增邮箱和 Bark 推送
- 新增直播注释停止录制
- 优化分段录制
- 重构部分代码

## v4.0.2 (2024-09-28)

- 新增知乎直播、CHZZK 直播录制
- 修复音播直播录制

## v4.0.1 (2024-09-03)

- 新增抖音双屏录制、音播直播录制
- 修复 PandaTV、bigo 直播录制

## v4.0.0 (2024-07-13)

- 新增映客直播录制

---

*最后更新: 2026-05-17*