# DouyinLiveRecorder 代码改动记录

## v4.0.8-dev (2026-06-20) — Bug 修复与静态检查

### Bug 修复

| 文件 | 问题 | 修复 |
|------|------|------|
| `src/spider.py` | `get_play_url_list` 中 `bandwidth_list` 与 `play_url_list` 长度不匹配时 `url_to_bandwidth[url]` 抛出 KeyError | 添加长度检查 `if bandwidth_list and len(bandwidth_list) == len(play_url_list)` |
| `src/spider.py` | `extract_douyin_hevc_flv_url(html_str)` 调用时 `html_str` 可能是 tuple 而非 str | 调整调用顺序，先执行 `_get_str_response()` |
| `src/spider.py` | `get_tiktok_stream_data` 重试 3 次全部 EOF 时静默返回 None | 循环结束后增加 `raise ConnectionError` |
| `src/stream.py` | `get_bilibili_stream_url` 返回 None 时仍设置 `is_live: True` | 添加 None 检查，返回 `is_live: False` |
| `src/stream.py` | 快手 `video_quality=None` 时跳过 URL 提取 | 移除 `if video_quality in QUALITY_MAPPING` 条件判断 |
| `gui.py` | f-string 无占位符 `f'IMAGENAME eq ffmpeg.exe'` | 改为普通字符串 |
| `gui.py` | `stop_recording` 中 `pid = self.process_pid` 赋值后从未使用 | 删除该行 |
| `gui.py` | `small_font`、`mono_font` 赋值后从未使用（死代码） | 删除两行 |
| `src/weverse_auth.py` | `import json` 未使用（`json=` 是 requests 参数，`response.json()` 是方法调用） | 删除该导入 |

### i18n 翻译文件更新

| 文件 | 改动 | 说明 |
|------|------|------|
| `i18n/zh_CN/LC_MESSAGES/zh_CN.po` | 更新 | 版本号 4.0.7 → 4.0.8-dev，日期更新为 2026-06-20；新增 20 条翻译条目（spider.py 异常错误消息 11 条、room.py HTTP 异常消息 2 条、utils.py 配置文件与磁盘空间消息 7 条） |
| `i18n/zh_CN/LC_MESSAGES/zh_CN.mo` | 重编译 | 使用 msgfmt 重新编译生成，总翻译条目 200 条 |

### 静态检查验证

- `python -m py_compile` 全部 20 个 Python 文件编译通过
- `python -m pyflakes` 仅余可接受的警告（`_output` 前缀约定、`global error_window` 冗余声明、`import src.logger` 副作用导入）

---

## v4.0.8-dev (2026-05-17) — 项目基础设施完善

### 配置与构建文件

| 文件 | 改动 | 说明 |
|------|------|------|
| `requirements.txt` | 重构 | 添加版本约束和分类注释，补充每个依赖的用途说明 |
| `pyproject.toml` | 修正 | 移除无效的 `[project.entry-points]` 空字典；`tool.black` 排除规则新增 `node/`、`ffmpeg/`、`downloads/`、`logs/` 目录，`target-version` 新增 `py313`；`classifiers` 添加 `MacOS X`/`Win32`/`POSIX :: Linux`/`Python 3.13`；`[optional-dependencies]` 合并 `all` 到 `gui` |
| `Dockerfile` | 🔴 关键修复 | **修复运行时阶段缺失 Node.js 的严重 Bug**（原多阶段构建仅在 builder 安装 Node.js，运行阶段缺少 `node` 命令导致 PyExecJS 无法执行签名脚本）；基础镜像升级至 Python 3.13；依赖安装从 `--user` 改为 venv 虚拟环境；新增 `procps` 包供健康检查使用；**修复 HEALTHCHECK 无效检测**（原 `python -c "import sys; sys.exit(0)"` 永远返回 0，改用 `pgrep -f 'python main.py'`）；添加 `TZ` 构建参数支持时区自定义；运行时创建 `backup_config` 目录 |
| `docker-compose.yaml` | 修正 | 修复无效健康检查（原 `python -c "import sys; sys.exit(0)"` 永远返回 0），改用 `pgrep -f 'python main.py'` 检测主进程存活；`start_period` 延长至 15s；新增 GUI 模式服务（YAML 锚点复用 recorder 配置，通过 `--profile gui` 启动）；新增 `.env` 文件加载支持；移除显式 `network_mode` 与 `networks` 冲突配置 |
| `.gitignore` | 重构 | 消除两个重复的"项目专用"区块；移除 `*.exe`/`*.dll`/`*.cmd`/`*.bat`/`*.vbs` 破坏性通配符（改用 `ffmpeg/*.exe` 等精确路径）；新增 `uv.lock`、`*.orig`、`*.desktop`、`*.lnk`、`index.html`；按 13 个功能区块重组织 |
| `.dockerignore` | 完善 | 新增排除 `gui.py`/`gui.pyw`/`demo.py`/`ffmpeg_install.py`/`StopRecording.vbs`/`index.html`（Docker 无头环境不需要这些文件）；移除 `*.exe`/`*.dll`/`*.cmd`/`*.bat`/`*.vbs` 破坏性通配符（改用 `ffmpeg/*.exe` 等精确路径）；消除底部重复的临时文件条目；新增 `ffmpeg/`/`.python-version`/`uv.lock`/`*.orig` 排除规则 |

### 文档文件

| 文件 | 改动 | 说明 |
|------|------|------|
| `README.md` | 更新 | 修正过时 GUI 入口文件名引用；修正配置区块名 `[settings]` → `[录制设置]`；修正配置项名匹配实际 config.ini；移除多余的 `</div>` 闭合标签；新增 Docker Node.js 常见问题解答；新增 `.dockerignore`/`.gitignore` 到项目结构树 |
| `CODE_WIKI.md` | 重写 | 基于最新代码分析重写架构文档：修正 GUI 入口文件名引用、补充 room.py 新增函数、补充 spider.py 平台函数列表、补充 Docker 构建说明、补充版本历史表 |
| `CODE_CHANGES.md` | 重写 | 本文件，记录历史变更和本次基础完善 |

### GUI 文件

| 文件 | 改动 | 说明 |
|------|------|------|
| `gui.py` | 新增 | 全新现代化 GUI 界面（1275 行），替代原 `gui.pyw`：新增 `Colors`/`CardFrame`/`GradientBanner`/`StatusIndicator`/`ModernTextWidget`/`SystemTray` 组件；实现 WCAG AA 标准高对比度色彩系统；DPI 感知字体自适应缩放；补充 5 个缺失的 ttk 样式配置；跨平台字体回退（`_resolve_font`）；ModernTextWidget `<Configure>` 自适应尺寸 |
| `gui.pyw` | 删除 | 原 904 行 GUI 代码，被 `gui.py` 完全替代 |

### 核心模块文件

| 文件 | 改动 | 说明 |
|------|------|------|
| `main.py` | 优化 | 为所有全局变量添加类型标注；模块 docstring 转为注释风格；新增 `start_display_time` 变量；优化"等待直播"输出逻辑（仅无录制任务时显示） |
| `src/spider.py` | 优化 | 模块及所有函数 docstring 转为行内注释（3681→3708 行，功能不变） |
| `src/stream.py` | 优化 | 模块及函数 docstring 转为行内注释（468→396 行，功能不变） |
| `src/utils.py` | 优化 | 移除模块和函数 docstring，转为行内注释 |
| `src/initializer.py` | 优化 | 移除 docstring 转为行内注释；`get_package_manager` 添加返回类型标注 |
| `src/logger.py` | 优化 | 移除模块 docstring 转为行内注释 |
| `src/proxy.py` | 优化 | 移除所有类和方法 docstring，转为行内注释 |
| `src/weverse_auth.py` | 优化 | 移除模块和函数 docstring，转为行内注释 |
| `src/__init__.py` | 优化 | 简化模块 docstring |
| `msg_push.py` | 优化 | 移除所有 docstring 转为行内注释；为模块级变量添加类型标注 |
| `ffmpeg_install.py` | 优化 | 移除 docstring 转为行内注释；修复 `block_size` 参数为 `chunk_size` |
| `i18n.py` | 优化 | 移除 docstring 转为行内注释 |
| `i18n/zh_CN/LC_MESSAGES/zh_CN.po` | 完善 | 新增 32 条翻译条目（YouTube/FlexTV/PopkonTV/TwitCasting 错误消息） |
| `src/debug_douyin_streams.py` | 新增 | 抖音流数据调试工具（406 行），支持多 UA 配置测试和编解码器检测（H265/HEVC/VP9/DASH） |
| `src/http_clients/async_http.py` | 保留 | 异步 HTTP 客户端模块，被 `spider.py`/`stream.py`/`debug_douyin_streams.py` 导入使用 |
| `src/http_clients/sync_http.py` | 保留 | 同步 HTTP 客户端模块 |

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

*最后更新: 2026-06-25*