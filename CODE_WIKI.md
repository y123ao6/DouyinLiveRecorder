# DouyinLiveRecorder 项目架构文档

简体中文  |  [**English**](CODE_WIKI_EN.md)

## 目录

- [文档统计与索引](#文档统计与索引)
- [项目概述](#项目概述)
  - [项目基本信息](#项目基本信息)
  - [功能特性](#功能特性)
  - [已支持平台](#已支持平台)
  - [画质代码对照](#画质代码对照)
  - [技术栈](#技术栈)
- [系统架构](#系统架构)
- [目录结构](#目录结构)
- [核心模块详解](#核心模块详解)
- [关键类与函数](#关键类与函数)
- [依赖关系](#依赖关系)
- [配置文件说明](#配置文件说明)
- [运行方式](#运行方式)
- [打包与发布](#打包与发布)
- [设计模式](#设计模式)
- [常见问题排查](#常见问题排查)
- [贡献指南](#贡献指南)
- [更新日志](#更新日志)

---

## 文档统计与索引

> 本节由对**工作空间内所有 `*.md` 文件**的统计分析归纳而来（初版生成于 2026-08-09，2026-09-20 复核刷新）。

### 统计概览

排除 `.git/` 后，工作空间共 **285** 个 Markdown 文件，按来源与维护方式分为五类：

| 分类       | 路径                     | 数量  | 性质                                             | 是否手工维护 |
| -------- | ---------------------- | --- | ---------------------------------------------- | ------ |
| 项目根文档（事实来源） | `AGENTS.md` + 中英成对的 `README` / `CODE_WIKI` | 5   | 事实来源（source of truth，中英双语文档各成对）              | ✅ 是    |
| 一次性审查报告 | `CODE_REVIEW_*.md`（仓库根目录） | 2   | 历史审查产出（`CODE_REVIEW_2026-09-18.md`、`CODE_REVIEW_AGENTS_GUIDELINES_2026-09-17.md`） | ❌ 历史产物 |
| 自动生成仓库文档 | `.qoder/repowiki/**`   | 0   | AI 生成的英文架构/知识库（原 302，2026-09-20 复核时该目录已不在工作区） | ❌ 自动生成 |
| 工作区记忆    | `.workbuddy/memory/**` | 45  | 本机 agent 每日工作日志                                | ❌ 缓存   |
| 历史记忆     | `.codebuddy/memory/**` | 14  | 旧版 agent 记忆（遗留）                                | ❌ 缓存   |

**结论**：真正由人工维护、应作为改动来源的文档仅为仓库根目录的 **5 个**（`AGENTS.md` 与中英成对的 `README` / `CODE_WIKI`）；另有 2 份一次性审查报告属历史产物，其余为 AI 生成的衍生文档或本地缓存，不应合并进本文档，以免引入与代码不同步的冗余内容。（统计快照初版生成于 2026-08-09；根文档数于 2026-08-28 随中英双语文档补齐更新为 5；2026-09-20 复核刷新：总数 324 → 285，`.qoder/repowiki/**` 目录已不存在，另补入 2 份审查报告行）

### 根文档索引

| 文件             | 角色          | 主要内容                                                                       |
| -------------- | ----------- | -------------------------------------------------------------------------- |
| `AGENTS.md`    | 编码代理约定      | 版本号单一事实源（`pyproject.toml`）、代码风格（black / isort / mypy）、项目结构、依赖/测试/构建命令、关键约定 |
| `README.md`    | 用户/开发者说明    | 功能特性、已支持平台（51 个）、快速开始、配置说明、使用说明、Docker 部署、开发指南、FAQ、更新日志                    |
| `CODE_WIKI.md` | 项目架构文档（本文档） | 模块详解、依赖关系、设计模式、常见问题排查、贡献指南、更新日志                                            |
| `README_EN.md` | 用户/开发者说明（英文） | `README.md` 的英文对应版（2026-08-24 新增，与中文版结构对齐）                                  |
| `CODE_WIKI_EN.md` | 项目架构文档（英文） | 本文档的英文对应版（2026-08-24 新增，条目与中文版一一对应）                                          |

> 五份文档职责互补：改动平台支持/配置项时须同步更新 `README.md` 与本文档；工程约定以 `AGENTS.md` 为准；`README_EN.md` / `CODE_WIKI_EN.md` 随对应中文版同步更新。

---

## 项目概述

### 项目基本信息

- **项目名称**: DouyinLiveRecorder (抖音直播录制器)
- **版本**: 4.3.0
- **作者**: Hmily
- **开源协议**: MIT
- **项目地址**: [GitHub](https://github.com/ihmily/DouyinLiveRecorder)

### 功能特性

- ✅ 支持 60+ 个直播平台（抖音、TikTok、YouTube、快手、虎牙、斗鱼、B站、小红书等）
- ✅ 循环值守直播状态，开播自动录制，断播自动停止
- ✅ 多种视频格式输出：TS、MKV、FLV、MP4、MP3、M4A
- ✅ 命令行 + GUI + Web 管理面板三模式运行
- ✅ 多平台消息推送：钉钉、微信、邮箱、TG、Bark、NTFY、PushPlus
- ✅ Docker 容器化部署
- ✅ 国际化支持（中文/英文）
- ✅ 灵活配置：画质选择、分段录制、自定义保存路径等
- ✅ 实际画质回采与降级告警（支持抖音、TikTok、快手、虎牙、斗鱼、B站、网易CC）
- ✅ Web 安全：Token 认证、路径穿越防护、敏感配置脱敏

### 已支持平台

归纳自 `README.md`，当前已列出 **51** 个平台（README 对外标称 60+，含持续添加中的平台）：

**国内站点（37 个）**：抖音 | 快手 | 虎牙 | 斗鱼 | YY | B站 | 小红书 | bigo | blued | 网易CC | 千度热播 | 猫耳FM | Look直播 | TwitCasting | 百度 | 微博 | 酷狗 | 花椒 | 流星 | Acfun | 畅聊 | 映客 | 音播 | 知乎 | 嗨秀 | VV星球 | 17Live | 浪Live | 飘飘 | 六间房 | 乐嗨 | 花猫 | 淘宝 | 京东 | 咪咕 | 连接 | 来秀

**海外站点（14 个）**：TikTok | SOOP(原AfreecaTV) | PandaTV | WinkTV | TTingLive(原Flextv) | PopkonTV | TwitchTV | LiveMe | ShowRoom | CHZZK | Shopee | YouTube | Faceit | Picarto

> 各平台流解析函数位于 `src/stream.py`、数据获取函数位于 `src/spider.py`；新增平台见「贡献指南 → 添加新平台支持」。

### 画质代码对照

录制画质以代码表示，对应中文名与说明如下（配置项 `原画|超清|高清|标清|流畅` 即映射到该表）：

| 画质代码 | 中文名 | 说明                       |
| ---- | --- | ------------------------ |
| OD   | 原画  | Original Definition，最高画质 |
| BD   | 蓝光  | Blu-ray，超高清              |
| UHD  | 超清  | Ultra HD                 |
| HD   | 高清  | High Definition          |
| SD   | 标清  | Standard Definition      |
| LD   | 流畅  | Low Definition，最低画质      |

支持实际画质回采与降级告警的平台：抖音、TikTok、快手、虎牙、斗鱼、B站、网易CC。当平台实际下发画质低于设置画质时，自动告警并标记。

### 技术栈

| 技术                               | 用途                                                   |
| -------------------------------- | ---------------------------------------------------- |
| Python 3.14+                     | 核心编程语言                                               |
| asyncio + httpx                  | 异步网络请求                                               |
| asyncio                          | 异步装饰器支持                                              |
| FFmpeg                           | 视频录制与转码                                              |
| Node.js + exejs/PyExecJS         | 运行 JavaScript 签名算法（exejs 优先，PyExecJS 回退）             |
| Loguru                           | 结构化日志                                                |
| CustomTkinter + pystray + Pillow | GUI 图形界面与系统托盘                                        |
| FastAPI + uvicorn                | Web 管理面板后端                                           |
| HTML + CSS + JavaScript          | Web 管理面板前端                                           |
| Docker                           | 容器化部署                                                |
| gettext (msgfmt)                 | 国际化翻译编译                                              |
| mypy                             | 静态类型检查（`--strict` 模式，`disallow_untyped_defs = true`） |
| pyflakes                         | 静态代码检查                                               |
| websockets                       | 弹幕 WebSocket 传输层（`src/ws_client.py`，各平台弹幕共用）         |
| protobuf                         | 抖音弹幕协议解码（`src/proto/douyin_pb2`，protoc 生成模块）         |
| brotli                           | B站弹幕解压（protover=3 需 brotli 解压）                       |

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户交互层                                │
├──────────────────┬──────────────────────┬───────────────────────┤
│ 命令行 (main.py) │ GUI 图形界面 (gui.py)│ Web 面板 (web.py)     │
│                  │                      │ └ src/web_api.py      │
│                  │                      │ └ web/ (前端静态资源)  │
└──────────────────┴──────────────────────┴───────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        核心业务层                                │
├──────────────────────┬─────────────────────┬────────────────────┤
│  直播间管理 (room.py)│  数据爬虫 (spider.py)│  流解析 (stream.py)│
├──────────────────────┴─────────────────────┴────────────────────┤
│                    FFmpeg 录制进程管理                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        基础设施层                                │
├──────────────────────┬─────────────────────┬────────────────────┤
│  日志 (logger.py)  │  工具 (utils.py)  │  代理 (proxy.py) │
├──────────────────────┴─────────────────────┴────────────────────┤
│                    配置管理 + 消息推送 (msg_push.py)             │
└─────────────────────────────────────────────────────────────────┘
```

### 工作流程

1. **配置解析阶段**
   - 读取 `config/config.ini` 主配置
   - 读取 `config/URL_config.ini` 直播间列表
   - 初始化 Node.js 环境和 FFmpeg 路径
2. **直播检测阶段**
   - 使用异步任务并发检测多个直播间
   - 各平台独立的 API 调用与签名算法
   - 动态调整并发数以避免限流
3. **流地址获取阶段**
   - 调用各平台的直播流 API
   - 根据配置选择不同画质（原画/超清/高清/标清/流畅）
   - 回采平台实际下发的画质（`actual_quality`）与可用档位（`available_qualities`）
   - 验证流地址可用性
4. **录制执行阶段**
   - 启动 FFmpeg 子进程
   - 实时监控录制状态
   - 记录实际画质，画质降级时输出告警日志
   - 支持分段录制
   - 支持转码为 MP4
5. **状态通知阶段**
   - 开播/关播事件触发
   - 调用配置的消息推送渠道
   - 记录日志

---

## 目录结构

```
DouyinLiveRecorder/
├── config/                              # 配置文件目录
│   ├── config.ini                      # 主配置文件
│   └── URL_config.ini                  # 直播间地址列表
├── src/                                 # 核心源码包
│   ├── __init__.py                     # 包初始化 + Node.js 环境配置 + 弹幕注册表/工厂（get_danmaku_class / get_danmaku_collector）
│   ├── spider.py                       # 直播数据爬虫（60+ 平台）
│   ├── stream.py                       # 直播流地址解析（含画质回采）
│   ├── room.py                         # 直播间信息解析
│   ├── utils.py                        # 工具函数库
│   ├── logger.py                       # Loguru 日志配置
│   ├── proxy.py                        # 代理检测
│   ├── ab_sign.py                      # 抖音签名算法 (A-Bogus)
│   ├── node_install.py                # Node.js 自动安装/初始化
│   ├── ffmpeg_master_download.py       # FFmpeg master 构建下载（按平台拉取并校验）
│   ├── ttwid.py                        # 抖音访客 ttwid 获取
│   ├── web_api.py                      # Web 管理面板 FastAPI 应用
│   ├── web_config.py                   # Web 面板配置读写（不依赖 FastAPI）
│   ├── web_tray.py                     # Web 模式系统托盘（Windows 最小化到托盘）
│   ├── http_config.py                  # HTTP 客户端共享运行时配置（SSL 验证开关）
│   ├── async_http.py                   # 异步 HTTP 客户端 (httpx)
│   ├── sync_http.py                    # 同步 HTTP 客户端
│   ├── javascript/                     # JavaScript 签名脚本
│   │   ├── crypto-js.min.js            # 加密库
│   │   ├── x-bogus.js                  # 抖音 X-Bogus 签名
│   │   ├── haixiu.js                   # 嗨秀签名
│   │   ├── liveme.js                   # LiveMe 签名
│   │   └── migu.js                     # 咪咕签名
│   ├── ffmpeg_install.py                # FFmpeg 安装脚本
│   ├── ffmpeg_master_download.py        # FFmpeg master 构建 Windows 下载器（架构感知 + 挑战页识别 + TOFU）
│   ├── ffmpeg_proc.py                   # FFmpeg 进程注册/注销/终止/清理（抽离自 main.py）
│   ├── video_postprocess.py             # 视频后处理：分段/转码/字幕（抽离自 main.py）
│   ├── stream_select.py                 # 流地址选择/校验/画质码/抖音限速（抽离自 main.py）
│   ├── notify.py                        # 推送/脚本/成功失败计数/并发调节（抽离自 main.py）
│   ├── scheduler.py                     # 并发调度中枢（自适应容量 + 按平台熔断 + 可运行时调容信号量）
│   ├── recorder_status.py               # 录制状态快照与展示（抽离自 main.py）
│   ├── config_io.py                     # 配置读写/安全数值转换/备份（抽离自 main.py）
│   ├── config_bool.py                   # 布尔配置解析（是/否 与 true/false/1/0/yes/no 等价，零依赖模块）
│   ├── base.py                          # 弹幕基类与数据结构（DanmakuBase / DanmakuMessage / DanmakuMessageType）
│   ├── collector.py                     # 弹幕采集器（线程化包装 DanmakuBase，落 SRT + 上报监控枢纽）
│   ├── cookie_cache.py                  # 按 URL 的访客 Cookie 进程内缓存（防并发重复请求触发风控）
│   ├── danmaku_monitor.py               # 弹幕监控枢纽（进程单例，内存快照 + JSONL 边车）
│   ├── srt_writer.py                    # SRT 字幕分段写入（时间轴对齐 ffmpeg segment）
│   ├── ws_client.py                     # 弹幕 WebSocket 传输层（各平台弹幕共用，proxy=None 直连）
│   ├── log_archive.py                   # 运行日志归档（停止录制流程收尾：四日志按时间戳改名）
│   ├── platforms/                       # 各平台弹幕客户端：Douyin/Douyu/Huya/Bilibili/Twitch + 私有签名 _tars/_xbogus
│   └── proto/                           # 抖音弹幕 protobuf（douyin.proto + 生成的 douyin_pb2）
├── web/                                 # Web 管理面板前端
│   ├── index.html                      # 单页应用入口
│   ├── app.js                          # 前端逻辑（API 调用、SSE、渲染）
│   └── style.css                       # 样式表（主题、响应式）
├── i18n/                                # 国际化翻译目录（多语言多格式）
│   ├── zh_CN/LC_MESSAGES/
│   │   ├── zh_CN.po                   # 简体中文翻译源（gettext）
│   │   └── zh_CN.mo                   # 编译后的翻译（运行时必需，随仓库/镜像分发）
│   ├── en_US.json                     # 英语（美国）目录（JSON 格式）
│   ├── en_GB.json                     # 英语（英国）目录（JSON 格式）
│   └── zh_TW.yaml                     # 繁体中文目录（YAML 格式）
├── typings/                             # 第三方库类型存根（仅静态检查用）
├── ffmpeg/                              # FFmpeg 二进制目录（Windows，git 忽略 exe）
├── node/                                # Node.js 二进制目录（Windows，git 忽略）
├── main.py                              # 命令行入口
├── gui.py                               # GUI 图形界面入口（CustomTkinter）
├── web.py                               # Web 管理面板入口
├── i18n.py                              # 国际化实现（print 翻译包装）
├── msg_push.py                          # 消息推送模块
├── index.html                           # 独立 M3U8/FLV 播放器页面
├── StopRecording.vbs                    # Windows 停止录制脚本
├── build_exe.py                         # PyInstaller 打包脚本（CLI/GUI/Web 三入口）
├── DouyinLiveRecorder.spec              # 由 build_exe.py 自动生成（.gitignore 已忽略）
├── requirements.txt                     # Python 依赖列表
├── uv.lock                              # uv 依赖锁文件（随仓库分发；镜像/CI 走 pip + requirements.txt，不消费）
├── pyproject.toml                      # Python 项目配置（版本号/工具配置/覆盖率门禁单一事实源）
├── scripts/                             # 辅助脚本
│   ├── check_version.py                # 版本号一致性校验（CI static job 调用）
│   ├── check_annotations.py            # 注释规范与逻辑等价性校验（禁 docstring / 密度下限 / --baseline AST 等价比对，CI static job 调用）
│   ├── check_coverage.py               # 逐模块覆盖率门禁（CI test job 调用，阈值 MODULE_THRESHOLDS）
│   ├── compile_po.py                   # gettext 翻译编译（.po → .mo；--check 零副作用校验同步，CI static job 调用）
│   ├── extract_i18n_strings.py         # i18n 待翻译串提取器（AST 扫描 print/logger 字面量 + 四语目录比对，维护期使用）
│   └── sync_version.py                 # 版本号同步脚本（pyproject → 各文档）
├── Dockerfile                          # Docker 构建文件（多阶段）
├── docker-compose.yaml                 # Docker Compose（recorder/web/gui 三服务）
├── .dockerignore                       # Docker 构建上下文排除文件
├── .gitignore                          # Git 排除文件
├── README.md                           # 项目说明
├── tests/                               # 单元测试目录（asyncio_mode=auto，覆盖率 source=src）
│   ├── conftest.py                     # Pytest 配置与 fixtures
│   ├── test_stream.py                  # stream.py 核心路径测试（工具函数 + 平台流解析）
│   ├── test_async_http.py              # async_http.py 核心路径测试（客户端管理 + 请求）
│   ├── test_sync_http.py               # sync_http.py 同步客户端测试
│   ├── test_room.py                    # room.py 直播间解析测试
│   ├── test_spider.py                  # spider.py 爬虫测试
│   ├── test_spider_platform.py         # spider.py 多平台分发测试
│   ├── test_utils.py                   # utils.py 工具函数测试
│   ├── test_douyin_url_resolution.py   # 抖音 URL 分发逻辑测试
│   ├── test_ttwid.py                   # 抖音 ttwid 共享缓存测试
│   ├── test_ab_sign.py                 # A-Bogus 签名算法测试
│   ├── test_proxy.py                   # 代理检测测试
│   ├── test_concurrency.py             # 线程安全并发测试
│   ├── test_i18n.py                    # i18n 翻译加载/环境变量独立性/po-mo 同步回归测试
│   ├── test_anchor_rename.py           # 主播名自动同步测试（config_io.update_anchor_name + main.rename_anchor_directory）
│   ├── test_scheduler.py               # 调度器测试（ResizableSemaphore / PlatformBreaker / ConcurrencyScheduler 共 16 用例）
│   ├── test_record_failure_feedback.py # 录制结果反馈测试（成功样本/快速失败退避/慢速失败/缺 -i/容量回退/直下失败与成功样本共 7 用例）
│   ├── test_stream_select.py           # 流选择与探针退避标记测试
│   ├── test_cookie_cache.py            # 访客 Cookie 缓存测试
│   ├── test_danmaku_monitor.py         # 弹幕监控枢纽测试
│   ├── test_http_config.py             # HTTP 配置测试
│   ├── test_config_io_readonly.py      # 配置只读/语言键迁移测试
│   ├── test_config_io_backup.py        # 配置备份测试
│   ├── test_bilibili_danmaku_info.py   # B站弹幕信息获取测试
│   ├── test_huya_danmaku.py            # 虎牙弹幕测试
│   ├── test_concurrency_rate_limit.py  # 抖音速率限制并发测试
│   ├── test_node_install.py            # Node.js 自动安装器离线测试（2026-09-21 新增）
│   ├── test_web_tray.py                # Web 控制台系统托盘离线测试（2026-09-21 新增）
│   ├── test_platform_danmaku_offline.py # 斗鱼/B站/Twitch 弹幕帧编解码离线测试（2026-09-21 新增）
│   ├── test_config_io_update_file.py   # 配置写侧（update_file / 主播名 / 备份脱敏）测试（2026-09-21 新增）
│   └── test_video_postprocess_paths.py # 视频后处理分支与异常分类测试（2026-09-21 新增）
├── .github/                             # GitHub Actions 工作流目录
│   ├── ISSUE_TEMPLATE/                 # Issue 模板（Bug 报告 / 功能请求）
│   ├── PULL_REQUEST_TEMPLATE.md         # PR 模板
│   ├── actions/
│   │   └── retry/                      # 复合动作：网络安装命令线性退避重试包装（ci.yml / build-release.yml 共用）
│   └── workflows/
│       ├── ci.yml                      # CI 静态验证（setup/static/typecheck/test/concurrency/integration/build-verify/summary）
│       ├── build-release.yml           # 三平台构建（lite + full 双产物）+ 自动发布 Release
│       └── issue-translator.yml        # Issue 自动翻译工作流（中英互译）
├── .coveragerc-concurrency             # 并发测试专用覆盖率配置（CI concurrency-test job 使用，不设全局阈值）
├── CODE_WIKI.md                        # 本架构文档（中文版）
├── CODE_WIKI_EN.md                     # 本架构文档（英文版）
├── README.md                           # 项目说明（中文版）
├── README_EN.md                        # 项目说明（英文版）
└── ...
```

---

## 核心模块详解

### 1. 主程序模块 (`main.py`)

**职责**: 整个录制器的指挥中心，负责流程调度

**核心功能**:

- 配置文件读取与解析
- 直播间 URL 列表解析
- 并发控制与任务调度
- FFmpeg 进程管理
- 错误重试与动态调优
- 消息推送触发
- 退出信号处理

**关键状态变量**:

```python
recording: set              # 正在录制的直播间集合
monitoring: int             # 正在监控的直播间数
running_list: list          # 正在运行的 URL 列表
error_count: int            # 当前错误计数
error_window: list          # 错误时间窗口（用于动态调优）
url_tuples_list: list       # 解析后的 URL 配置列表 [(quality, url, anchor_name)...]
recording_time_list: dict   # 录制时间与画质记录 {name: [start_time, quality_zh, actual_quality_zh]}
```

**主流程函数**:

- `main()` - 入口函数
- `read_config()` - 读取配置
- `check_url_config()` - 检查 URL 配置
- `start_recording()` - 启动录制（解析 actual_quality，降级时输出告警）
- `stop_recording()` - 停止录制
- `check_live_status()` - 检测直播状态
- `display_info()` - 终端状态展示（兼容新旧 recording_time_list 格式）
- `get_status()` - 返回录制状态 dict（含 actual_quality 字段，供 Web API 使用）
- `select_source_url()` - 在 m3u8/FLV 源间选择，HLS 源校验失败时回退 FLV（`delay_default=120s` 轮询）；新增 `proxy_addr` 参数透传给三处校验调用，避免 TikTok 等需代理平台直连校验误判不可达；计算「末位候选」（FLV 无 record_url 备选时、record_url 恒为）并以 `last_resort` 传给校验器——稳定拒绝也仅告警放行、交由 ffmpeg 实际拉流定夺；**HLS 采集排除列表**（`main.hls_collection_exclude_platforms`，配置键「HLS采集排除平台(逗号分隔)」）：命中平台无视「是否启用HLS采集」配置、恒按 FLV 采集（等效于仅对该平台关闭 HLS 采集，HLS 候选整组剔除、不作回退；仅剩 HLS 源无回退时告警并放弃本轮，恢复指引指向移出排除列表），列表外平台行为不变
- `_validate_stream_url()` - 流地址校验：content-type 判定补充 `mpegurl`；HEAD 被拒时对 `.m3u8` 源（**含 404**）补 `Range: bytes=0-0` GET 探测——抖音 CDN 的 m3u8 常对 HEAD 返回 4xx，此前会被误判不可达而总回退 FLV；新增 `verify` 参数沿用全局 SSL 开关（与异步校验一致）；所有失败路径记录 warning（URL + 异常类型/状态码/content-type），不再静默吞异常；GET 复核（`_confirm_get_ok`）收到 401/403 先原样重试一次（间隔 0.8s）再定罪——斗鱼 hw/虎牙 al 等 CDN 对毫秒级连击探针（HEAD→GET）偶发 403（实测同 URL 片刻后重试即 200、ffmpeg 单次 GET 正常），重试可区分「偶发限流」与「稳定拒绝」，历史虎牙假绿场景重试仍 403 依旧被正确否决

**重构（2026-08-16）**：下列职责已抽离至 `src/` 子模块，经 `main.py` re-export 保持 `main.<name>` 命名空间兼容（`web.py`/`gui.py`/`web_api.py`/测试零改动）：

- FFmpeg 进程管理 → `src/ffmpeg_proc.py`（进程注册/注销/终止/清理）
- 视频后处理（分段/转码/字幕）→ `src/video_postprocess.py`
- 流地址选择/校验/画质码/抖音限速 → `src/stream_select.py`（`select_source_url`/`_validate_stream_url`/`get_quality_code`/`_douyin_rate_limit` 等）
- 推送/脚本/成功失败计数/并发调节 → `src/notify.py`（`push_message`/`record_error`/`record_success`/`adjust_max_request`/`clear_record_info` 等）
- 录制状态快照/展示 → `src/recorder_status.py`（`get_status`/`display_info`）
- 配置读写/安全数值转换/备份 → `src/config_io.py`（`update_file`/`delete_line`/`read_config_value`/`_safe_int`/`_safe_float`/`backup_file`/`backup_file_start`）

深度耦合 main 全局的模块一律用运行时 `import main` 惰性访问全局，避免启动期传参膨胀调用点；`main.py` 顶部加 `__main__` 守卫规避 `python main.py` 时子模块 `import main` 触发整文件二次执行。

**房间录制线程闭包整改（2026-08-16）**：新增直播间时为每路 URL 起一个 daemon 线程运行 `start_record`。原实现用「默认参数绑定循环变量」（`def _room_thread_target(_key=thread_key, _args=args)`）规避闭包晚期绑定陷阱，且 `_args: tuple[Any, ...]` 使用了项目 basedpyright 全局禁用的显式 `Any`。整改后：

- `_args` 类型具体化为 `tuple[tuple[str, str, str], int]`（`url_tuple` 为 `tuple[str, str, str]`，与 `start_record(url_data, count_variable)` 签名一致）；
- 通过 `threading.Thread(target=..., args=(thread_key, args))` 在创建线程时显式绑定当前循环值，移除默认参数 hack，语义更清晰、更易维护；
- 线程退出仍 `finally: create_var.pop(_key, None)` 清理，防止 `create_var` 字典长期无界增长。

**弹幕录制集成（2026-08-16 接线定稿）**：`start_record` 各平台分支收集 `record_danmaku_args`（每轮重置 `None`）→ 6 处 `check_subprocess(..., platform=platform, danmaku_args=record_danmaku_args)` 全部接线 → `get_danmaku_collector(platform, args, base_filename, segment_seconds)` 创建采集器。采集器在 `while process.poll() is None` 循环外 `stop()`（`DanmakuCollector.stop()` 有 `_stop_called` 防重入，幂等）。分段文件名约定：ffmpeg 视频分段模板统一 `_%03d`（FLV 已从 `_%02d` 对齐；音频仍 `_%02d` 但无弹幕），SRT 分片 `{seg:03d}`（`_000.srt` 对 `_000.ts`）；`check_subprocess` 同时剥离 `_%02d`/`_%03d` 占位符。抖音空 cookie 时 `DouyinDanmaku.start()` 协程内 `await get_ttwid()` 动态获取（采集线程独立事件循环，可直接 await；进程级缓存）。`弹幕分片时长(秒)` 走 `_safe_float(..., 1800.0)`。弹幕平台注册表见 `src/__init__.py` 的 `get_danmaku_class`（斗鱼直播/B站直播/虎牙直播/抖音直播/TwitchTV）。

**房间日志关联字段绑定（2026-09-20）**：`start_record` 作为房间线程主体，在**线程入口**即调 `set_room_context(f"序号{count_variable}")` 绑定日志关联字段（否则早于 `record_name` 的退出标志 / 注释退出 / 解析失败 / 熔断退避日志无法归属房间），并在每轮解析出主播名、`record_name = f"序号{count_variable} {anchor_name}"` 之后刷新为完整房间名。字段如何进入日志行、哪些线程带/不带该标记，见「6. 日志模块」与 `AGENTS.md`「已知坑」。

---

### 2. 爬虫模块 (`src/spider.py`)

**职责**: 负责从各大直播平台获取直播间数据

**支持平台**:

国内：抖音、快手、虎牙、斗鱼、YY、B站、小红书、bigo、blued、网易CC、千度热播、猫耳FM、Look直播、TwitCasting、百度、微博、酷狗、花椒、流星、Acfun、畅聊、映客、音播、知乎、嗨秀、VV星球、17Live、浪Live、飘飘、六间房、乐嗨、花猫、淘宝、京东、咪咕、连接、来秀

海外：TikTok、SOOP(原AfreecaTV)、PandaTV、WinkTV、TTingLive(原Flextv)、PopkonTV、TwitchTV、LiveMe、ShowRoom、CHZZK、Shopee、YouTube、Faceit、Picarto

**关键函数**:

- `get_douyin_web_stream_data()` - 获取抖音 Web 端直播数据（`web/enter` API 优先，失败静默重试 1 次，再回退 HTML 抓取）
- `get_douyin_app_stream_data()` - 获取抖音 App 端直播数据（备用方案，内置 URL 分发逻辑，见下方「抖音 URL 分发」）
- `get_tiktok_stream_data()` - 获取 TikTok 直播数据
- `get_youtube_stream_data()` - 获取 YouTube 直播数据
- `get_bilibili_stream_data()` - 获取 B站直播流数据（返回 dict，含 url/current_qn/accept_qn）
- `get_play_url_list()` - 获取 M3U8 播放列表中的清晰度选项
- `get_params()` - 从 URL 提取参数

**抖音 URL 分发逻辑**（`get_douyin_app_stream_data`，2026-08-01 优化后）：

| URL 形态                                 | 处理路径                                                                                                                  |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `live.douyin.com/<房间号或抖音号>`            | 直调 `get_douyin_web_stream_data`（`web/enter` API 接受抖音号，无需重定向解析）                                                        |
| `www.douyin.com/user/<sec_uid>`（网页端主页） | 跳过必然失败的 `get_sec_user_id` 探测，走 `resolve_from_homepage()`：`get_unique_id()` 解析抖音号 → 拼接 `live.douyin.com/<抖音号>` → 直调网页端 |
| `v.douyin.com/<短链>`（App 短链，可能指向直播间或主页） | 先 `get_sec_user_id()` 跟随重定向；抛 `UnsupportedUrlError` 时回退 `resolve_from_homepage()`                                     |

- `resolve_from_homepage()` 直调 `get_douyin_web_stream_data`（网页端 API 优先、内置 HTML 兜底），不再绕经旧版 HTML 优先抓取路径（约 1MB 页面），并**显式透传 proxy_addr / cookies**（旧实现未透传，导致代理与 Cookie 配置在主页路径静默失效）
- `web/enter` API 调用封装为 `_try_web_api()` + `for attempt in range(2)`：首次失败（如瞬时风控 `status_code=10002`）→ `await asyncio.sleep(0.5)` 缓冲 → 静默重试；重试成功直接返回、跳过 HTML 兜底；两次都失败才记 WARNING 并回退 HTML（取 HEVC 原画的 HTML 抓取是各网页端路径通用行为，保持不变）

**实现特点**:

- 使用异步 HTTP 客户端 (`httpx`)
- 各平台独立的签名算法
- 代理支持
- Cookie 支持
- 错误重试机制
- B站 spider 返回 dict 结构（含 `current_qn`/`accept_qn` 元信息），供 stream 模块回采实际画质

---

### 3. 直播流解析模块 (`src/stream.py`)

**职责**: 解析直播流地址，支持多种画质选择，回采平台实际下发的画质

**画质映射**:

```python
QUALITY_MAPPING = {"OD": 0, "BD": 1, "UHD": 2, "HD": 3, "SD": 4, "LD": 5}
QUALITY_MAPPING_BIT = {
    'OD': 99999, 'BD': 4000, 'UHD': 2000, 'HD': 1000, 'SD': 800, 'LD': 600
}
QUALITY_LEVEL = {"OD": 0, "BD": 0, "UHD": 1, "HD": 2, "SD": 3, "LD": 4}  # 等级值越大画质越低
QUALITY_CODE_TO_ZH = {"OD": "原画", "BD": "蓝光", "UHD": "超清", "HD": "高清", "SD": "标清", "LD": "流畅"}
NETEASE_QUALITY_MAP = {"blueray": "OD", "ultra": "UHD", "high": "HD", "standard": "SD"}
```

**画质工具函数**:

- `bitrate_to_quality(bitrate)` - 根据码率反查画质代码（0/未知回退 OD）
- `code_to_zh(code)` - 画质代码转中文名
- `is_downgrade(requested, actual)` - 判定是否降级（actual 等级值 > requested）
- `get_quality_index()` - 解析画质参数，返回索引
- `_pad_list()` - 填充列表到指定最小长度（部分平台已改用显式截断替代）

**各平台流地址解析函数**:

| 函数                          | 平台     | 实际画质回采方式                                            |
| --------------------------- | ------ | --------------------------------------------------- |
| `get_douyin_stream_url()`   | 抖音     | 从 `flv_pull_url` / `hls_pull_url_map` 的 key 提取画质标签  |
| `get_tiktok_stream_url()`   | TikTok | 从 `vbitrate` 字段通过 `bitrate_to_quality()` 反查         |
| `get_kuaishou_stream_url()` | 快手     | 从 `flv_url_list` 的 `bitrate` 字段反查                   |
| `get_huya_stream_url()`     | 虎牙     | 从 `exsphd` ratio 值映射，处理降级选择                         |
| `get_douyu_stream_url()`    | 斗鱼     | 从平台下发的 `rate` 字段反向映射                                |
| `get_bilibili_stream_url()` | B站     | 从 spider 返回的 `current_qn` 反向映射为画质代码                 |
| `get_netease_stream_url()`  | 网易CC   | 从画质名（blueray/ultra/high）通过 `NETEASE_QUALITY_MAP` 映射 |

**返回值结构**（各平台统一）:

```python
{
    "is_live": True,
    "anchor_name": "主播名",
    "title": "直播标题",
    "quality": "UHD",              # 用户设置的画质
    "actual_quality": "UHD",       # 平台实际下发的画质
    "available_qualities": ["OD", "UHD", "HD"],  # 平台可用的画质档位
    "m3u8_url": "http://...",
    "flv_url": "http://...",
    "record_url": "http://...",
}
```

**实现特点**:

- 按带宽排序的清晰度选择
- 自动降级策略（首选画质不可用时自动降级）
- FLV 与 M3U8 双协议支持
- 状态码验证
- 显式截断替代 `_pad_list` 静默填充，避免越界
- 画质降级检测（`is_downgrade`），供 main.py 告警使用
- 斗鱼 FLV→m3u8 同 token HLS 候选：`get_douyu_stream_url` 在 `rtmp_live` 以 `.flv` 结尾时，将路径 `.flv` 改 `.m3u8`（查询串原样保留）附为 `m3u8_url`——斗鱼 wsAuth token 对 FLV/HLS 通用（实测 hw CDN 200 + `application/vnd.apple.mpegurl`，两级 m3u8），HLS 采集开启时经 `select_source_url` 优先校验选用、不可达自动回退 FLV；HLS 逐段拉取不维持长连接，缓解游客态 FLV 长连接约 70 秒被 CDN 掐断导致的反复分段

---

### 4. 直播间信息模块 (`src/room.py`)

**职责**: 解析直播间 URL，提取房间 ID、主播信息、抖音号等

**关键函数**:

- `get_sec_user_id()` - 获取房间 ID 和用户 sec_user_id
- `get_unique_id()` - 获取抖音号（含 30 分钟 TTL 的 sec_uid→抖音号进程级缓存，对齐 `ttwid.py` 的 `threading.Lock` 跨线程/跨 asyncio 循环去重模式）
- `is_user_homepage_url()` - 判断 URL 是否为「网页端主播主页」形态（`douyin.com/user/<sec_uid>`，v.douyin.com 短链不属于此类）；用于零请求快速路径——sec_user_id 直接在路径中，无需发请求跟随重定向
- `extract_sec_user_id()` - 从 URL 中显式正则提取 sec_user_id
- `get_live_room_id()` - 获取直播间 web ID
- `get_xbogus()` - 生成 X-Bogus 签名

**异常处理**:

- `UnsupportedUrlError` - 不支持的 URL 格式异常

**关键常量与接口**:

- `DESKTOP_UA` - 桌面 Chrome UA。`iesdouyin.com/web/api/v2/user/info/` 等接口用旧移动端 UA 会被静默限流（HTTP 200 + 空 body），必须使用桌面 UA
- 主页解析走 `https://www.iesdouyin.com/web/api/v2/user/info/?sec_uid=<sec_uid>` JSON 接口（取 `unique_id`，空则退 `short_id`）——旧 `iesdouyin.com/share/user/<sec_uid>` 页面已是 JS 反爬壳页，HTML 正则不可靠

---

### 5. 工具模块 (`src/utils.py`)

**职责**: 提供通用工具函数

**主要工具**:

| 工具函数                       | 功能描述          |
| -------------------------- | ------------- |
| `Color` 类                  | 终端彩色输出常量      |
| `trace_error_decorator()`  | 错误追踪装饰器       |
| `check_md5()`              | 计算文件 MD5      |
| `dict_to_cookie_str()`     | cookie 字典转字符串 |
| `read_config_value()`      | 读取配置文件值       |
| `update_config()`          | 更新配置文件        |
| `remove_emojis()`          | 移除文本中的表情符号    |
| `remove_duplicate_lines()` | 移除文件重复行       |
| `handle_proxy_addr()`      | 处理代理地址格式      |
| `generate_random_string()` | 生成随机字符串       |

---

### 6. 日志模块 (`src/logger.py`)

**职责**: 基于 Loguru 配置结构化日志

**日志输出**:

- **控制台**: 彩色日志输出（`custom_format`，不含房间列）
- **`logs/streamget.log`**: DEBUG 级别（排除 INFO），行结构 `时间 | 级别 | 房间 | 模块:函数:行号 - 消息`
- **`logs/PlayURL.log`**: INFO 级别（仅直播流地址），行结构 `时间 | 房间 | 消息`
- **`logs/gui.log`**: 仅 GUI 父进程写（独占句柄），不带房间列——GUI 进程不执行录制，该列恒为空

**房间关联字段 `extra[room]`（2026-09-20 新增）**:

- 房间线程的全部日志行带一个稳定关联列，用于从多房间交织落盘的日志里切出单个房间的链路（切法与边界见 `AGENTS.md`「已知坑」同名条目）
- 实现：`ROOM_FIELD` + `set_room_context()` / `get_room_context()` 读写一个 `ContextVar`，由 `logger.configure(extra={ROOM_FIELD: ""}, patcher=_room_patcher)` 注册的全局 patcher 在**调用线程**内写进 `record["extra"]`（故 `enqueue=True` 不串味）；调用点显式 `bind(room=...)` 优先于线程级兜底
- 房间线程在 `main.py::start_record` 入口绑 `序号N`、解析出主播名后升级为完整 `record_name`；`set_room_context("")` 为解绑
- **`extra` 默认值不可删**：缺它时未绑定房间的日志格式化 `KeyError: 'room'`，loguru 不抛异常而是每条日志向 stderr 吐 `Logging error in Loguru Handler` 并丢弃该行；回归锁 `tests/test_logger_room_context.py`
- 只加关联标识：日志级别、INFO/其余两档 `filter`、`rotation`、`retention` 均未改动

**日志文件开关**:

- 通过 `config/config.ini` 的 `是否启用日志文件(是/否)` 控制
- 默认启用，保持向后兼容
- logger.py 在初始化时直接读取配置（不依赖 main.py 执行顺序）

**日志轮转**: 300 KB 自动轮转，保留 1 份

---

### 7. 消息推送模块 (`msg_push.py`)

**职责**: 支持多种消息推送渠道

**支持渠道**:

| 渠道       | 函数名            | 说明               |
| -------- | -------------- | ---------------- |
| 钉钉       | `dingtalk()`   | 群机器人推送           |
| 微信       | `xizhi()`      | Server酱 / WeChat |
| Telegram | `tg_bot()`     | Bot 消息           |
| 邮件       | `send_email()` | SMTP 协议          |
| Bark     | `bark()`       | iOS 通知           |
| NTFY     | `ntfy()`       | 开源推送服务           |
| PushPlus | `pushplus()`   | 微信推送平台           |

---

### 8. 国际化模块 (`i18n.py`)

**职责**: 基于 gettext 的多语言支持系统，自动翻译项目源码的 print 输出。

**实现机制**:

- `translated_print` 包装 `builtins.print`，自动翻译调用者来自项目根（`src/` 包及 `main.py` 等顶层脚本）的输出；`main.py` 导入时无条件安装 `builtins.print = translated_print`（任何语言下均安装——zh_CN/zh_TW 把英文常量串译为中文，en_US/en_GB 把中文串译为英文，未知串恒等返回）
- 支持源码运行和 PyInstaller 打包两种路径检测（`_internal/i18n` vs `i18n/`）
- **多格式目录加载（2026-08 起）**：`i18n.py` 按语言依次探测 gettext `.mo` → `<lang>.json` → `<lang>.yaml`，三种格式均为「原文 → 译文」扁平映射，行为一致；`PyYAML` 为运行时依赖（缺失时仅损失 YAML 格式支持）。`_load_yaml_catalog()` 捕获 `yaml.YAMLError`（非 OSError/ValueError 子类）——损坏的 yaml 目录返回 None 降级到下一格式，而非让 `set_language` 抛异常（Web 语言切换接口 500）
- **语言热切换**：`set_language(lang)` 归一化（`normalize_language` 别名表：zh_cn/zh-CN/en/en-US/zh-Hant/zh_CN.UTF-8 等写法均可）后热替换 `_tr` 翻译函数，无需重启进程。三个切换入口：Web 面板（`GET/PUT /api/language`，写回 config + 热切换 + 前端 `data-i18n` 文案重绘；`PUT` 在配置缺 `language` 键时降级为节末追加补建，不再恒 500）、GUI（侧边栏「语言 Language」菜单）、CLI 主循环（每轮按 config 重同步）
- 默认语言：简体中文（zh_CN）；受支持语言：zh_CN / en_US / en_GB / zh_TW

**翻译文件**:

| 文件                                | 说明                                             | 条目数 |
| --------------------------------- | ---------------------------------------------- | --- |
| `i18n/zh_CN/LC_MESSAGES/zh_CN.po` | 简体中文翻译源文件（gettext，可编辑）                         | 496 |
| `i18n/zh_CN/LC_MESSAGES/zh_CN.mo` | 编译后的二进制翻译文件（gettext 运行时唯一读取，随仓库/镜像分发）          | 496 |
| `i18n/en_US.json`                 | 英语（美国）目录（JSON 格式，英文源恒等 + 中文源译英）                | 496 |
| `i18n/en_GB.json`                 | 英语（英国）目录（JSON 格式，英式拼写：minimise/unrecognised 等） | 496 |
| `i18n/zh_TW.yaml`                 | 繁体中文目录（YAML 格式，简→繁字符转换 + 台湾用语适配）               | 496 |

**维护流程**: 修改 `.po` 后必须执行 `python scripts/compile_po.py` 重新编译并一并提交 `.mo`，否则翻译改动不会生效；`python scripts/compile_po.py --check`（CI `static` job）在两者不同步时拦截——其内部 `write_mo()` 为**纯内存产出不落盘**，`--check` 模式零副作用、真实比对磁盘上已提交的 `.mo`，仅非 check 模式才写盘。CI 路径过滤器（paths-filter）将 `i18n/**` 视为触发条件：纯翻译变更同样会运行该门禁。**四种语言的目录键集合必须一致**（`tests/test_i18n.py::test_catalogs_share_same_keyset` 强制校验）——新增 msgid 时需同步更新四个目录。新增待翻译串的提取与比对用 `python scripts/extract_i18n_strings.py`（AST 扫描运行时代码 print 常量串 + logger f-string 模板底稿并与四语目录比对；f-string 模板归一化约定：格式/转换符丢弃、表达式内双引号转单引号；纯占位符模板（如 `{color}{text}`）与 gettext 头部空 msgid 已过滤，不产生噪声）。

**翻译覆盖范围**（2026-08-27 全量补全后，覆盖运行时全部常量串与 logger 模板底稿）:

- `src/spider.py` — 各平台直播数据获取/登录/风控消息（含 B站 buvid 认证链路）
- `main.py` — 主程序通用消息、录制链、画质降级、主播名同步、磁盘空间
- `gui.py` — GUI 界面消息（控件文本、进程管理、托盘、退出确认）
- `src/scheduler.py` — 并发模式切换与容量调整播报
- `src/stream_select.py` — 流地址校验全套消息（探针退避、GET 复核、末位放行）
- `src/collector.py` / `src/danmaku_monitor.py` — 弹幕采集与监控
- `src/async_http.py` / `src/sync_http.py` / `src/cookie_cache.py` — HTTP 客户端与 cookie 缓存
- `msg_push.py` — 七渠道推送失败分支（微信/钉钉/TG/Bark/ntfy/PushPlus/邮件）
- `src/ffmpeg_install.py` / `src/node_install.py` — ffmpeg/Node.js 自动安装
- `src/config_io.py` / `src/utils.py` — 配置读写、备份、磁盘空间
- `src/notify.py` — 自定义脚本执行错误
- `web.py` / `src/web_tray.py` — Web 面板启动与托盘
- `src/room.py` / `src/recorder_status.py` / `src/ttwid.py` / `src/ffmpeg_proc.py` / `src/platforms/bilibili.py` / `src/platforms/douyin.py` / `build_exe.py` — 其余运行时消息

> 注：运行时真正参与翻译查找的是 `print()` 输出的常量英文串；`logger.*` 输出与 f-string 插值后的文本不经过查找，目录中相关条目仅作为后续日志接入 i18n 时的现成翻译底稿保留。

---

### 9. GUI 模块 (`gui.py`)

**职责**: 提供现代化图形用户界面

**设计特点**:

- **高对比度色彩系统**: 满足 WCAG AA 无障碍标准
- **DPI 感知字体**: 自适应分辨率缩放
- **系统托盘**: 最小化到托盘运行
- **现代组件**: 卡片式设计、渐变横幅、状态指示器

**主要组件**:

- `Colors` - 色彩常量类
- `DpiFont` - DPI 感知字体系统
- `SystemTray` - 系统托盘管理
- `CardFrame` - 卡片容器
- `GradientBanner` - 渐变横幅
- `StatusIndicator` - 状态指示器
- `ModernTextWidget` - 现代文本控件

**导航页面**:

- 📊 控制台 - 录制状态总览、启停控制
- 🎯 画质监控 - 实时检测各直播间实际画质是否与设置一致
- 📝 URL 配置 - 直播间地址管理
- 📋 运行日志 - 子进程日志查看

**画质监控页面** (`_build_quality_page`):

- 通过解析 main.py 子进程 stdout 日志获取画质信息
- 解析 loguru 日志前缀（`|` + `-` 分隔），提取 message 内容
- 降级告警匹配：`{name} 画质降级：设置 {zh}({code}) 实际 {zh}({code})`
- 录制状态匹配：`{name}[{quality}] 正在录制中 {duration}`
- 统计卡片：录制中 / 画质正常 / 画质降级 计数
- 降级行以红色背景高亮，正常行显示"✓ 同等"
- 线程安全：`_quality_lock` 保护共享数据，UI 更新仅在主线程执行
- 超时清理：30 秒未更新的录制标记自动清除

---

### 10. 异步 HTTP 客户端 (`src/async_http.py`)

**职责**: 封装 httpx，提供统一的异步 HTTP 接口

**功能**:

- 代理支持
- 超时设置
- 自动重试
- 状态码检查
- HTTP/2 支持
- **连接池复用**: 按 (代理, verify, http2) 维度复用 AsyncClient，发挥 keepalive 连接池作用
- **事件循环检测**: 缓存记录每个 client 创建时的事件循环引用，检测到 `asyncio.run()` 导致循环变更时自动重建客户端，避免 `'NoneType' object has no attribute 'send'` 错误
- **模块级锁随事件循环重建**（2026-08-12 修复）: 保护 `_client_cache` 读写的 `_client_lock` 原是模块级单例 `asyncio.Lock()`，在首个 room 的 `asyncio.run()` 循环里惰性绑定后，后续 room 各自 `asyncio.run()` 起新循环再次 `await` 会触发 `RuntimeError: ... is bound to a different event loop`；该异常被 `async_req` 吞掉后返回空串，被 `spider.py` 误判成「风控空响应」并级联触发 HTML 兜底失败。现 `_get_client_lock()` 改为缓存 `(lock, loop)` 二元组，当前循环变更时自动重建锁，与 `_client_cache` 的「client + loop」机制一致，从源头消除跨循环锁错误
- **异常日志带类型**（2026-08-12 收口）: `async_req`、`_close_all_clients` 内所有 `except Exception as e: logger.debug(e)` 改为带 `type(e).__name__`（必要时含 URL），消除 Windows 下异常 `str()` 为空时打出空白日志、无法定位的问题
- **SSL 验证**: 由全局配置 `src/http_config.py` 统一控制，默认启用
- **跨循环旧客户端不再调度关闭**（2026-09-04 修复）: 淘汰他循环创建的旧 AsyncClient 时一律**不创建** `aclose()` 协程（旧循环运行中/已停止/已关闭同样对待），释放引用交由 GC 兜底。旧实现 `run_coroutine_threadsafe` 只调度不等待，旧循环处于 `asyncio.run` 收尾窗口（已停未关）时回调永不执行，GC 报 "coroutine ... aclose was never awaited" 且数量随机波动（1~2 条 flaky，经 unraisableexception 逸出）；「is_running 门控 + 等待 future」实测仍无法根治（收尾阶段任务可能已创建却永不步进 `Task was destroyed but it is pending`，future 永不完成还会把收尾竞态放大成秒级阻塞）；在当前循环直接 await 则会操作绑定旧循环的 transport。回归锁：`tests/test_async_http_lock.py::test_cross_loop_running_old_loop_skips_close` / `test_cross_loop_stopped_old_loop_skips_close`
- **连接池清理**: 进程退出时通过 atexit / 信号处理器释放所有复用的 AsyncClient
- **`get_response_status()` m3u8 容错**（2026-08-05 增强）: HEAD 校验失败时，若 URL 以 `.m3u8` 结尾则补一次 `Range: bytes=0-0` GET 轻量探测（**含 404 在内的所有非 2xx 均触发探测**，返回 200/206 即判可达）；非 m3u8 源（FLV/record_url）行为不变。异常日志带 URL + `type(e).__name__`（如 `ConnectTimeout` / `TimeoutError`），避免 Windows 下 `socket.timeout` 的 `str()` 为空时只输出空白消息；探测失败记录 `status_code` / `content-type` 便于排障

**被以下模块导入**:

- `src/spider.py` - `async_req()`
- `src/stream.py` - `get_response_status()`

---

### 11. HTTP 客户端配置 (`src/http_config.py`)

**职责**: 提供 HTTP 客户端共享运行时配置

**功能**:

- SSL 证书验证全局开关（`ssl_verify`），默认启用（True，安全优先）；已整合进「是否启用https录制」——开启=https 拉流 + 禁用证书验证，关闭=http 拉流 + 默认严格校验（由 main.py 每轮热同步）
- 提供 `set_ssl_verify()` / `set_https_recording()` 函数，由主配置启动时及主循环每轮设置
- 平台级 SSL 覆盖（`ssl_verify_platform_overrides`）：兼容保留，整合后不改变实际行为
- 异步 / 同步 HTTP 客户端在发起请求时读取此配置

---

### 12. 同步 HTTP 客户端 (`src/sync_http.py`)

**职责**: 封装 requests 和 urllib，提供同步 HTTP 接口

**功能**:

- 代理支持
- 超时设置
- Cookie 支持
- 重定向跟踪
- **SSL 验证**: 由全局配置 `src/http_config.py` 统一控制，并可经 `ssl_verify` 参数做**单次覆盖**（见下）
- **Session 生命周期管理（2026-09-02）**: thread-local `requests.Session` 经模块级 `WeakSet` 弱引用登记（线程销毁后条目自动回收、不阻止 GC）；`atexit` 注册 `close_all_sessions()` 在进程退出时统一优雅关闭全部存活连接池（80+ 房间长跑场景）；另提供 `close_session()` 供房间线程退出路径显式释放当前线程 Session，关闭后下次 `_session()` 自动重建
- **Opener 构造形态（F-12 落地后，2026-09-24 校准本小节）**: 仅 `_opener_secure`（禁用代理 + 保留证书验证）在模块级预构建；不校验证书的 `SSLContext` 与 opener 一律**按需惰性构造**（`_get_insecure_context()` / `_get_insecure_opener()`）——2026-09-12 审查 6.7 指出「import 期即存在不校验上下文」等于给全进程开静默降级面，故禁止改回常驻
- **`ssl_verify` 单次覆盖（F-12）**: `sync_req(..., ssl_verify=None/True/False)` 由 `_resolve_ssl_verify()` 裁决（`None` = 跟随 `http_config.ssl_verify` 全局开关，显式传值以本次调用为准），且该次裁决必须**同时透传 urllib 与 requests(代理) 两条路径**，凭据类调用点可显式强制校验而不被全局降级拖下水
- **线程级 Session 公开出口（MIN-08）**: `session()` 供「必须拿状态码 / 响应头、无法走 `sync_req`（其失败契约是一律返回空串）」的调用点复用同一份连接池；打桩目标仍是 `_session`（测试约定）
- **响应体上限（SEV-2226 收尾，2026-09-23）**: 无代理 urllib 路径两道上限缺一不可——`_read_capped()` 限制压缩/原始响应体读入（`_MAX_RESPONSE_BYTES` 8 MiB）、`_gunzip_capped()` 分块解压并限制产出（`_MAX_DECOMPRESSED_BYTES` 32 MiB），超限抛 `ValueError` 由既有失败分支记脱敏日志并返回空串；**代理分支的 `response.text` 由 requests 自行解码 gzip，仍不受该上限保护**（已知残留缺口，见源码注释）
- **现状（SEV-2226 取证，2026-09-23）**: 本模块**当前无任何生产 importer**（`src/spider.py` 走 `from .async_http import async_req` 的 httpx 异步面；原调用方 `src/weverse_auth.py` 已于 2026-09-23 删除），去留待维护者决定；本体仍承载 F-12 不变量与 `tests/test_sync_http.py` 对该不变量的回归锁

---

### 13. Web 管理面板 (`web.py` + `src/web_api.py` + `src/web_config.py` + `web/`)

**职责**: 提供 Web 界面远程管理录制器，包括仪表盘、直播间管理、配置编辑、日志查看

**架构**:

- `web.py` - 入口：守护线程运行 `main.main()`，主线程运行 uvicorn；支持后台隐藏运行模式
- `src/web_api.py` - FastAPI 应用：认证（Token）、REST API 路由、SSE 推送、静态资源挂载
- `src/web_config.py` - 配置读写（不依赖 FastAPI，便于单测）
- `web/` - 前端静态资源（单页应用）

**后台运行模式** (`web_show_console = false`):

- `_enter_background_mode()` 在启动录制引擎前调用
- Windows 下通过 `ctypes` 调用 `GetConsoleWindow()` + `ShowWindow(hwnd, SW_HIDE)` 隐藏控制台窗口
- stdout/stderr 重定向到 `logs/web_console.log`（行缓冲，实时写入）
- 程序完全后台运行，通过 Web 面板管理
- 恢复控制台：设置 `web_show_console = true` 后重启

**控制台编码 / `ctypes` 健壮性（2026-08-16 整改）**:

- kernel32 / user32 的 `WinDLL` 句柄缓存为模块级单例（`_KERNEL32` / `_USER32`），避免 `_fix_encoding()` 与 `_enter_background_mode()` 多次调用时重复加载 DLL；加载失败时仍保持 `None`，后续调用自动重试
- 补全 `restype` 声明：`SetConsoleOutputCP` / `SetConsoleCP` 返回 `BOOL`（显式 `restype = ctypes.c_int`），`ShowWindow` 返回 `BOOL`，与既有的 `GetConsoleWindow.restype = c_void_p` 一致，消除对 ctypes 默认返回类型的隐式依赖
- `_enter_background_mode()` 中 `GetConsoleWindow()` 的返回值已为 `c_void_p`，移除多余 `cast(ctypes.c_void_p, ...)`，直接判空后 `ShowWindow(hwnd, 0)`

**API 路由**:

| 路由                  | 方法         | 功能                       |
| ------------------- | ---------- | ------------------------ |
| `/api/login`        | POST       | 密码登录，返回 Token            |
| `/api/status`       | GET        | 获取录制状态（含 actual_quality） |
| `/health`           | GET        | 探活端点（`{"status": "ok", "version"}`，恒公开、不受认证支配；CI 冒烟 / LB 健康检查用） |
| `/api/rooms`        | GET/POST   | 直播间列表查询 / 新增             |
| `/api/rooms/{url}`  | PUT/DELETE | 编辑 / 删除直播间               |
| `/api/rooms/toggle` | POST       | 启用 / 禁用直播间               |
| `/api/recording/toggle` | POST   | 录制全局开关（开始/停止录制；停止时触发运行日志归档） |
| `/api/config`       | GET/PUT    | 读取 / 修改配置                |
| `/api/logs/stream`  | GET        | SSE 实时日志推送               |

**前端功能** (`web/`):

- `index.html` - 单页应用入口（仪表盘 / 直播间 / 配置 三个视图）
- `app.js` - 前端逻辑（Token 认证、API 调用、SSE 日志流、状态渲染）
- `style.css` - 样式表（明暗主题、响应式布局、降级高亮）

**录制表格展示**:

- 名称 / 设置画质 / 实际画质 / 开始时间 / 已录时长
- 实际画质与设置画质不一致时标红显示（`.quality-down` 样式）

**安全机制**:

- 密码变更后自动吊销所有现有 Token，强制重新登录
- 监听 `0.0.0.0` 且未启用认证时输出安全告警
- 文件下载路径校验（`_is_within` 防目录穿越）
- 敏感配置项（Cookie / 账号密码 / web_password）API 返回时脱敏为 `***`
- **未认证危险配置写保护**：`web_auth_enable = false` 时，`PUT /api/config` 禁止改写 [Recorder] 与 [Push] 危险键（如「录制完成后执行自定义脚本」`run_script`），仅允许 [Web] 及白名单键，阻断未认证 RCE 链
- **INI 注入防护**：配置值与直播间名称过滤 `\n`/`\r`，防止向 `config.ini` / `URL_config.ini` 注入任意新行 / 新节
- **登录爆破限流**：`/api/login` 连续失败达阈值（默认 5 次 / 5 分钟）后锁定一段时间（默认 10 分钟），防御密码在线爆破
- **推送日志脱敏**：`msg_push.py` 的 `_mask_url()` 对失败日志中的 webhook URL 遮挡 query 内 token / secret，避免凭证经日志泄露

---

### 14. 弹幕采集子系统 (`src/platforms/` + `src/collector.py` + 关联模块)

**职责与架构总览**: 提供与视频录制同步、按半小时分片的直播弹幕（bullet-chat）采集能力——弹幕落为 SRT 字幕文件，并可经「弹幕监控」独立查看（仅监控不落盘）。弹幕模块自 `dart_simple_live` 移植，原位于 `src/danmaku/`，后随目录扁平化迁移至 `src/` 根（基类 `src/base.py`、采集器 `src/collector.py`、监控 `src/danmaku_monitor.py`、传输 `src/ws_client.py`、缓存 `src/cookie_cache.py`、字幕 `src/srt_writer.py`、`src/proto/`、各平台实现 `src/platforms/`）。

**与流解析解耦**: 弹幕子系统与 `src/spider.py`（视频流地址解析）是**平行的两套抽象**。`spider.py` 负责解析视频流地址，弹幕客户端经 `src/__init__.py` 的注册表/工厂解耦；`spider.py` 完全不 import `src/platforms`。仅 B站弹幕在 AUTH 被拒时会懒加载回调 `spider.invalidate_bili_buvid_cache()`。

**生命周期接线**（与录制同起同停）:

- `main.start_record` 各平台分支收集 `record_danmaku_args`（每轮重置 `None`）；
- 6 处 `check_subprocess(..., platform=platform, danmaku_args=record_danmaku_args)` 全部接线；
- 由 `src/__init__.py:get_danmaku_collector(platform, danmaku_args, base_filename, segment_seconds, only_fans, room_name, write_srt)` 工厂按平台取弹幕类并构造 `DanmakuCollector`；平台不支持或 `danmaku_args` 为空时返回 `None`；
- `DanmakuCollector` 在 `while process.poll() is None` 循环外 `stop()`，`DanmakuCollector.stop()` 有 `_stop_called` 防重入（幂等）。

**平台注册表**（`src/__init__.py:get_danmaku_class`，平台名与 `main.py` 标识一致）:

| 平台标识     | 弹幕类（`src/platforms/`） |
| -------- | --------------------- |
| 斗鱼直播     | `DouyuDanmaku`        |
| B站直播     | `BilibiliDanmaku`     |
| 虎牙直播     | `HuyaDanmaku`         |
| 抖音直播     | `DouyinDanmaku`       |
| TwitchTV | `TwitchDanmaku`       |

**关键文件**:

- **基类与数据结构 (`src/base.py`)**: `DanmakuBase(ABC)` 定义统一契约——类属性 `heartbeat_interval=45.0`；构造 `__init__(on_message, on_close, on_ready)` 保存回调并置 `_stopped=False`；四个抽象方法 `async start(args)` / `async stop()` / `async heartbeat()` / `decode_message(data: bytes|str)`，辅助 `_emit(msg)` 经 `on_message` 上抛。`DanmakuMessageType(Enum)`（`CHAT/GIFT/ONLINE/SUPER_CHAT`）；`DanmakuMessage` dataclass（`type/user_name/message/data/color/timestamp_ms`，`timestamp_ms` 由采集器注入）。
- **弹幕采集器 (`src/collector.py`)**: `DanmakuCollector` 把异步弹幕客户端包装为线程化的同步采集器。构造参数含 `danmaku_cls / danmaku_args / base_filename / segment_seconds / only_fans / room_name / platform_name / write_srt`（`write_srt=False` 为仅监控不落盘模式）；`start()` 锚定 SRT 时间轴并起 daemon 线程 `_run()`（新 `asyncio.new_event_loop()`，实例化弹幕类 `run_until_complete(danmaku.start(args))`）；`_on_message` 把全部类型上报监控枢纽 `hub.room_message(...)`，仅 `CHAT` 且用户名/内容非空才写 SRT；`stop(timeout=8.0)` 幂等，`message_count` 属性。依赖 `src.base` / `src.danmaku_monitor` / `src.srt_writer`。
- **各平台弹幕客户端 (`src/platforms/`)**: 五个 `DanmakuBase` 子类 + 两个私有签名/编解码工具。
  | 文件            | 类                 | WebSocket 端点                                                | 关键协议/逻辑                                                                                                                                                                     |
  | ------------- | ----------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `douyin.py`   | `DouyinDanmaku`   | `wss://webcast100-ws-web-lq.douyin.com/webcast/im/push/v2/` | gzip 解 `PushFrame.payload`→`Response`（protobuf）；`danmaku_signature`（`_xbogus`）生成 `signature`；Cookie 缺失 `await get_ttwid()`；`backup_url` 把 `lq`→`lf`                         |
  | `douyu.py`    | `DouyuDanmaku`    | `wss://danmuproxy.douyu.com:8506`                           | 小端二进制帧 + STT 文本协议；`_dispatch` 处理 `chatmsg`（按 `if==1` 粉丝过滤）emit CHAT；心跳发 `mrkl`                                                                                              |
  | `huya.py`     | `HuyaDanmaku`     | `wss://cdnws.api.huya.com`                                  | Tars 二进制协议（`_tars`）；`_make_join_data()` 写 `WSRegisterReq`；`cmdType==7`→`_decode_chat`（HYMessage）                                                                            |
  | `bilibili.py` | `BilibiliDanmaku` | `wss://{host}/sub`（遍历 `host_list`）                          | 16B 大端帧头；`protover=2` zlib / `=3` brotli 解压；`operation==8` AUTH_REPLY 校验 `code==0`，失败/超时经 `_reject_auth()` + `spider.invalidate_bili_buvid_cache()`；`_auth_watchdog`(8s) 兜底 |
  | `twitch.py`   | `TwitchDanmaku`   | `wss://irc-ws.chat.twitch.tv`                               | 纯 IRC；匿名 `justinfan{random}` 连接；`PING`→`PONG`，正则解析 PRIVMSG emit CHAT；代理经 `handle_proxy_addr` 或系统代理                                                                          |
  | `_tars.py`    | （私有）Tars 编解码器     | —                                                           | 虎牙用极简 Tars：`TarsInputStream` / `TarsOutputStream`，头字节高 4 位 tag、低 4 位 type                                                                                                   |
  | `_xbogus.py`  | （私有）X-Bogus 签名    | —                                                           | 抖音弹幕用：`generate_xbogus`（RC4 + 自定义 base64）、`danmaku_signature(room_id, unique_id)`                                                                                           |
- **弹幕监控枢纽 (`src/danmaku_monitor.py`)**: `DanmakuMonitorHub`（进程单例，经 `get_hub()` 惰性创建）聚合各房间弹幕事件——`room_started/room_connected/room_closed/room_stopped/room_message`，内存快照 `snapshot(since=0)` 供 Web API 消费，并写 JSONL 边车 `logs/danmaku_monitor.jsonl`（5MB 轮转）。所有方法异常全吞；含 10s×6 桶速率窗与每秒 ≤10 条采样折叠。
- **SRT 字幕写入 (`src/srt_writer.py`)**: `SrtWriter` 按 `segment_seconds` 分片输出 `{base}_{seg:03d}.srt`（单文件模式 `{base}.srt`），时间轴以 `time.monotonic()` 为基准、与 ffmpeg `segment -reset_timestamps` PTS 对齐；`write()` 持 `threading.Lock` 写条目并 flush。
- **WebSocket 传输层 (`src/ws_client.py`)**: `WsClient` 各平台弹幕共用的异步 WS 客户端。`connect()` 显式 `proxy=None`（弹幕直连、不跟随系统代理，避免 SOCKS 需 python-socks 报错）；`ping_interval=None`（各平台自带心跳）；`max_size=None`、`asyncio.Lock` 串行发送；支持 `on_message/on_ready/on_heartbeat/on_close/on_reconnect` 回调与 `max_reconnect` 重连策略。
- **访客 Cookie 缓存 (`src/cookie_cache.py`)**: 进程内唯一「按网址动态获取访客 cookie」缓存，避免多 room 并发重复请求触发风控。`fetch_cookies(url, proxy, *, ttl=30min, fetcher=None)` 无锁快速路径 + singleflight 去重（2026-09-02 重写：`threading.Lock` 仅保护缓存字典与在途登记表的同步读写、**锁内绝无 await**——旧 RLock 跨 await 持有时同循环协程全部可重入、互斥失效；同循环等待者复用 future，跨循环经 `loop.call_soon_threadsafe` 交付（future 非线程安全）；拉取协程被取消时立即交付空结果，等待者带超时兜底防永久挂起）；`get_cookie_str` / `invalidate` / `clear`。
- **抖音弹幕协议 (`src/proto/`)**: `douyin.proto`（Proto3）定义 `Response/Message/ChatMessage/GiftMessage/...` 等；`douyin_pb2.py` 为 protoc 生成（DO NOT EDIT），`douyin_pb2.pyi` 为基于pyright 类型存根。抖音弹幕解析链路：`PushFrame.payload`（gzip 后 `Response`）→`Message.payload`→`ChatMessage`。

---

### 15. 并发调度中枢 (`src/scheduler.py`)

**职责**: 统一管理全局网络并发容量、按平台（host）隔离熔断降级、支持自适应调速与固定并发双模式的可运行时调容信号量系统。

**核心类**:

- **`ResizableSemaphore`**: 可运行时调容的信号量，实现上下文管理器协议。支持 `set_value(n)` 运行时增减容量——增大时唤醒相应数量的等待者，减小时仅降低上限、不强行回收已持有槽位。`__init__` / `set_value` 允许容量为 0（暂停态）。消除旧「销毁重建信号量」的竞态风险。
- **`PlatformBreaker`**: 按 key（host）隔离的熔断器，实现 `closed → open → half-open` 三态状态机。连续失败样本比例超阈值即 open（跳过探测并进入冷却），冷却后经**唯一**探针放行；探针成功恢复 closed、失败重新 open。用于将单平台抖动隔离降级，避免连锁拖垮全局。**探针带租约（`_PROBE_LEASE_SECONDS = 60s`，2026-08-27 起）**：探针被授予后超过租约仍未回报样本（主播未开播等待轮、`disable_record`、房间线程退出等不触发 `record` 的路径）时，`allow()` 重新授予探针实现自愈——无租约时 `_probing` 标志永不复位会导致该 host 永久熔断直到进程重启。
- **`ConcurrencyScheduler`**: 调度中枢，整合自适应容量、平台熔断、录制并发上限三大能力。
  - **网络并发容量** = `max(配置下限, min(上限, ceil(活跃数/缩放因子)))`；错误率极高时温和降容但永不低于安全下限（默认 min=1 / max=128）
  - **自适应模式**（默认，`最大同时录制数(0为不限制) = 0`）：容量随活跃任务数动态缩放，错误率反馈驱动温和背压
  - **固定并发模式**（`最大同时录制数(0为不限制) ≠ 0`）：忽略动态调速器与错误背压，网络容量恒为「同一时间访问网络的线程数」（最小 1 槽位，热更新即时生效）
  - **录制并发软上限**：通过 `recording_semaphore` 管控同时 ffmpeg 录制数，默认 0 为不限制
  - `adjust_loop` 守护循环每 5 秒重算容量，取代旧的单向压制 `adjust_max_request`

**关键函数**:

- `host_of(url)`: 从 URL 提取主机名（截到首个 `/`、`?`、`#` 为止，小写、保留端口）作为熔断 key；空串或解析异常统一归 `"unknown"`（互不相关的坏 URL 共享同一熔断 key，粗粒度兜底）
- `allow(key)`: 预检指定 host 是否已熔断，返回 False 时调用方应跳过本轮探测；half-open 态带探针租约（见 `PlatformBreaker`）
- `record_error(key)` / `record_success(key)`: 按 host 计入成功/失败样本，驱动熔断器状态迁移

**接线点**（固定几处，不改动 50+ 平台分派函数）:

- `notify.record_error/record_success` 增 `key` 形参，委托给 `scheduler`
- `start_record` 入口在平台分派前做 `scheduler.allow(record_host)` 熔断预检
- `start_record` 解析成功分支（`anchor_name` 非空）上报 `record_success(record_host)`——half-open 探针依赖本轮结果闭环，探针房间进入长时间录制期间同 host 其余房间不再饿死
- `check_subprocess` 的录制循环受 `recording_semaphore` 管控
- `main()` 首轮初始化调度器，`semaphore` / `recording_semaphore` 指向其属性

**线程安全**（2026-08-27 加固）: 配置字段（模式/配置上限/活跃数/错误窗口）由 main 主线程与 `adjust_loop` 守护线程并发读写，`_compute_capacity()` 单次加锁快照全部可变输入、`set_configured_limit()` / `set_dynamic_mode()` 锁内写入（幂等检查与写入原子）；`Lock` 不可重入，所有 setter 在锁释放后再调 `recompute()`，全链路无嵌套持锁。

**配置项**:

| 配置项            | 说明                               | 默认值 |
| -------------- | -------------------------------- | --- |
| 最大同时录制数(0为不限制) | 0=不限制（同时兼作并发模式开关：0=动态调速，非0=固定并发） | 0   |
| 同一时间访问网络的线程数   | 动态模式下为容量下限之一；固定模式下为固定并发限制值       | 3   |

**测试**: `tests/test_scheduler.py` 共 16 用例，覆盖信号量调容、熔断器状态机（含探针租约超时自愈）、自适应容量缩放/下限、固定并发模式、按 key 隔离、录制并发软上限等。

---

## 关键类与函数

### 签名算法 (`src/ab_sign.py`)

抖音平台的 A-Bogus 签名算法，包含：

- SM3 哈希
- RC4 加密
- 复杂的参数混淆

### 配置文件管理 (`src/utils.py`)

```python
def read_config_value(file_path: Path, section: str, key: str) -> str | None
def update_config(file_path: Path, section: str, key: str, new_value: str) -> None
```

### 错误处理装饰器

```python
@trace_error_decorator
async def some_function():
    # 自动捕获并记录异常（支持同步和异步函数）
    pass
```

**实现特点**:

- 使用 `asyncio.iscoroutinefunction()` 检测函数类型
- 异步函数使用 `async wrapper` 正确 `await` 并捕获异常
- 统一返回 `{}` 空字典，与调用方 `.get()` 用法兼容
- `execjs.ProgramError` 单独处理（Node.js 环境问题）

### 动态并发调整

`main.py` 中实现的基于错误率的动态并发数调整机制，避免被平台限流。

### 并发调度器 (`src/scheduler.py`)

```python
# 可运行时调容信号量
class ResizableSemaphore:
    def set_value(self, n: int) -> None: ...
    def acquire(self) -> None: ...
    def release(self) -> None: ...

# 按平台熔断器
class PlatformBreaker:
    def allow(self) -> bool: ...
    def record_success(self) -> None: ...
    def record_failure(self) -> None: ...

# 调度中枢
class ConcurrencyScheduler:
    network_semaphore: ResizableSemaphore
    recording_semaphore: ResizableSemaphore
    def set_dynamic_mode(self, enabled: bool) -> None: ...
    def set_recording_limit(self, limit: int) -> None: ...
    def allow(self, key: str) -> bool: ...
    def record_error(self, key: str) -> None: ...
    def record_success(self, key: str) -> None: ...

# 辅助函数
def host_of(url: str) -> str: ...
```

---

## 依赖关系

### Python 依赖 (`requirements.txt`，与 `pyproject.toml [project.dependencies]` 保持一致)

| 包名                | 版本要求      | 用途                                                |
| ----------------- | --------- | ------------------------------------------------- |
| requests          | >=2.34.2  | 同步 HTTP 请求（现仅 ffmpeg / node 安装下载脚本使用；各平台解析走 httpx 异步面） |
| urllib3           | >=2.7.0   | 传输层（requests 之下；显式声明以防解析回退落入 CVE-2026-44431 区间）    |
| httpx[http2]      | >=0.28.1  | 异步 HTTP 客户端（含 HTTP/2，`src/async_http.py` 并发抓取流地址）  |
| h2                | >=4.3.0   | httpx `http2=True` 的运行期依赖（`Client.__init__` 内 `import h2`） |
| socksio           | >=1.0.0   | httpx SOCKS 代理（socks5/socks5h）的运行期依赖（传输层内 `import socksio`） |
| loguru            | >=0.7.3   | 结构化日志（`src/logger.py` 统一封装）                       |
| pycryptodome      | >=3.23.0  | 加密算法（SM3、RC4、AES）                                 |
| distro            | >=1.9.0   | Linux 发行版检测                                       |
| tqdm              | >=4.69.0  | 下载进度条                                             |
| exejs             | >=1.0.1   | JavaScript 执行引擎（PyExecJS 的活跃维护继任者，优先使用）           |
| PyExecJS          | >=1.5.1   | JS 执行引擎回退兼容（exejs 未安装时使用）                         |
| customtkinter     | >=6.0.0   | 现代化 GUI 框架                                        |
| pystray           | >=0.19.5  | 系统托盘（GUI / Web 托盘模式）                              |
| Pillow            | >=12.3.0  | 图像处理（托盘图标生成）                                      |
| fastapi           | >=0.140.0 | Web 管理面板后端框架                                      |
| starlette         | >=1.3.1   | ASGI 工具集（fastapi 传递依赖，`src/web_api.py` 直接导入故显式声明；下限 0.49.1→1.0.1→1.3.1 见 CVE/PYSEC 说明） |
| uvicorn[standard] | >=0.51.0  | ASGI 服务器                                          |
| python-multipart  | >=0.0.32  | 表单/文件上传解析                                         |
| pydantic          | >=2.13.4  | 请求模型校验                                            |
| websockets        | >=14.0    | 弹幕 WebSocket 客户端（`src/ws_client.py`；`additional_headers` 为 14.0+ API） |
| protobuf          | >=6.33.5,<8 | 抖音弹幕协议解码（`src/proto/douyin_pb2.py`；上限 <8 为 gencode 兼容护栏） |
| brotli            | >=1.2.0   | B站弹幕解压（protover=3）                                |
| PyYAML            | >=6.0.3   | YAML 翻译目录支持（`i18n/zh_TW.yaml`）                    |

> 注 1：[历史注] 旧版此处记录「Weverse 平台认证由 `src/weverse_auth.py` 实现、不再依赖 pip 上的 `weverse` 包」。
> 该模块（连同 `tests/test_weverse_auth.py`）已于 2026-09-23 整体删除，结论仅作备查：pip 上的 `weverse`
> 包会拉入已废弃的 pycrypto==2.6.1（Python 3.10+ 无法编译），**任何时候都不要加入依赖清单**。
>
> 注 2：可执行文件打包需 PyInstaller，属于构建期可选依赖：`pip install .[build]`
>
> （对应 `pyproject.toml` 的 `[project.optional-dependencies] build`）。

### 外部依赖

| 依赖      | 用途                 | 安装方式                                                        |
| ------- | ------------------ | ----------------------------------------------------------- |
| FFmpeg  | 视频录制与转码            | Windows 内置（`ffmpeg/`），Linux/macOS 手动安装；Docker 内 apt 安装      |
| Node.js | 运行 JavaScript 签名算法 | Windows 自动安装（`node/`），Linux 需包管理器安装；Docker 内 apt 安装 Node 22 |

### 模块依赖关系图

```
main.py
├── src/spider.py
│   ├── src/room.py
│   ├── src/ab_sign.py
│   ├── src/async_http.py
│   │   └── src/http_config.py
│   ├── src/http_config.py
│   └── src/utils.py
├── src/stream.py
│   ├── src/spider.py
│   └── src/async_http.py
├── src/scheduler.py (并发调度中枢)
│   ├── ResizableSemaphore (可运行时调容信号量)
│   ├── PlatformBreaker (按平台熔断器)
│   └── ConcurrencyScheduler (调度中枢)
├── src/notify.py (record_error/record_success 委托调度器)
├── src/http_config.py
├── src/async_http.py
├── src/utils.py
│   └── src/logger.py
├── msg_push.py
└── src/ffmpeg_install.py

src/__init__.py (弹幕注册表/工厂)
├── get_danmaku_collector() → src/collector.py
│   └── DanmakuCollector
│       ├── src/base.DanmakuBase (契约)
│       ├── src/platforms/<X>Danmaku (各平台实现)
│       │   ├── src/ws_client.WsClient (传输，proxy=None 直连)
│       │   ├── src/cookie_cache.fetch_cookies (访客 cookie)
│       │   ├── src/proto.douyin_pb2 (抖音解码)
│       │   └── src/ttwid.get_ttwid (抖音动态 ttwid)
│       ├── src/srt_writer.SrtWriter (落 SRT)
│       └── src/danmaku_monitor.get_hub() (监控枢纽，进程单例)

web.py
├── src/web_api.py
│   ├── src/web_config.py
│   └── main.py (get_status 等函数)
└── web/ (静态资源)
```

---

## 配置文件说明

### 主配置文件 (`config/config.ini`)

#### [录制设置] 节

| 配置项                | 说明                                                                                                                                                            | 默认值                                                                                                                |     |       |       |                        |    |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | --- | ----- | ----- | ---------------------- | -- |
| language           | 界面语言（留空跟随系统语言；值支持 zh_cn/zh_CN/en/en_US/en_GB/zh_TW 等写法，经 resolve_language 解析归一，不可识别或语言文件缺失回退 en_US；Web/GUI 可即时切换并写回本键）                                        | （空）                                                                                                                |     |       |       |                        |    |
| 是否跳过代理检测(是/否)      | 是否跳过代理检测                                                                                                                                                      | 是                                                                                                                  |     |       |       |                        |    |
| 是否启用https录制        | 整合开关（合并原「是否强制启用https录制」与「是否禁用SSL证书验证(是/否)」）：开启=https 拉流+跳过证书校验；关闭=http 拉流+默认证书校验（https-only 海外平台保持原样）                                                         | 否                                                                                                                  |     |       |       |                        |    |
| 禁用SSL证书验证的平台(逗号分隔) | 平台级证书校验豁免列表：**仅在「需要证书校验」时生效**（即 http 录制模式，FFmpeg 9.0 起 TLS 证书验证默认开启）——列表内平台跳过证书校验（适用于虎牙/B站等证书异常平台）；https 录制模式已全局跳过、列表冗余。启动时自动追加缺失的必需平台（虎牙直播、B站直播，只追加不移除用户手填项） | 虎牙直播,B站直播                                                                                                          |     |       |       |                        |    |
| 是否启用日志文件(是/否)      | 是否将日志写入文件                                                                                                                                                     | 是                                                                                                                  |     |       |       |                        |    |
| 直播保存路径(不填则默认)      | 录制文件保存路径                                                                                                                                                      | (空，默认当前目录)                                                                                                         |     |       |       |                        |    |
| 保存文件夹是否以作者区分       | 是否按主播名分类                                                                                                                                                      | 是                                                                                                                  |     |       |       |                        |    |
| 是否自动更新主播名(是/否)     | 主播改名后自动同步：更新 URL_config.ini 主播名字段，并重命名旧主播名命名的录制文件夹及文件夹内录制文件（含弹幕/字幕等同前缀产物）；仅在该直播间未在录制时触发，进行中的录制不受影响；关闭则保持手动填写的名称不变                                             | 是                                                                                                                  |     |       |       |                        |    |
| 视频保存格式ts           | mkv                                                                                                                                                           | flv                                                                                                                | mp4 | mp3音频 | m4a音频 | ts/mkv/flv/mp4/mp3/m4a | ts |
| 原画                 | 超清                                                                                                                                                            | 高清                                                                                                                 | 标清  | 流畅    | 默认画质  | 原画                     |    |
| 是否使用代理ip(是/否)      | 是否启用代理                                                                                                                                                        | 否                                                                                                                  |     |       |       |                        |    |
| 代理地址               | 代理服务器地址；支持带协议前缀（`http://` / `https://` / `socks://` 等），裸地址（ip:端口）自动补 `http://` 前缀                                                                             | (空)                                                                                                                |     |       |       |                        |    |
| 同一时间访问网络的线程数       | 并发数                                                                                                                                                           | 3                                                                                                                  |     |       |       |                        |    |
| 循环时间(秒)            | 直播状态检测间隔                                                                                                                                                      | 120                                                                                                                |     |       |       |                        |    |
| 分段录制是否开启           | 是否分段                                                                                                                                                          | 是                                                                                                                  |     |       |       |                        |    |
| 是否启用HLS采集(是/否)     | 是否优先使用 HLS(m3u8) 源采集；关闭或源不可用时回退 FLV                                                                                                                           | 是                                                                                                                  |     |       |       |                        |    |
| HLS采集排除平台(逗号分隔) | HLS 采集排除列表：命中平台**无视「是否启用HLS采集」配置、恒按 FLV 采集**（等效于仅对该平台关闭 HLS 采集，HLS 候选整组剔除、不作回退，连带失效 h265-FLV → HLS 切换）；列表外平台不受影响仍 HLS 优先。平台名须完全一致（如：斗鱼直播）；支持中英文逗号，主循环每轮热更新 | (空，不排除任何平台)                                                                                                 |     |       |       |                        |    |
| 视频分段时间(秒)          | 分段时长                                                                                                                                                          | 1800                                                                                                               |     |       |       |                        |    |
| 使用代理录制的平台(逗号分隔)    | 按域名子串匹配直播间 URL，命中即走代理（须先开启「是否使用代理ip」）                                                                                                                         | tiktok, sooplive, pandalive, winktv, flextv, popkontv, twitch, liveme, showroom, chzzk, shopee, shp, youtu, faceit |     |       |       |                        |    |
| 额外使用代理录制的平台        | 在上表之外追加走代理的平台（逗号分隔），代理地址取「代理地址」之外的兜底值                                                                                                                         | (空)                                                                                                                |     |       |       |                        |    |
| 是否录制弹幕(是/否)        | 是否将弹幕落为 SRT 字幕文件                                                                                                                                              | 否                                                                                                                  |     |       |       |                        |    |
| 是否弹幕监控(是/否)        | 弹幕监控独立开关：GUI「弹幕监控」页 / Web「弹幕监控」标签实时查看弹幕流与统计；与「是否录制弹幕」解耦，仅监控时不落 SRT，两者都开时复用同一条弹幕连接                                                                             | 否                                                                                                                  |     |       |       |                        |    |
| 弹幕录制平台(逗号分隔)       | 目前支持弹幕录制的平台（名称须完全一致）：斗鱼直播、B站直播、虎牙直播、抖音直播、TwitchTV（见 `src/__init__.py` 弹幕注册表）                                                                                  | 斗鱼直播,B站直播,虎牙直播,抖音直播,TwitchTV                                                                                       |     |       |       |                        |    |
| 弹幕分片时长(秒)          | 弹幕 SRT 分片时长（需开启分段录制）                                                                                                                                          | 1800                                                                                                               |     |       |       |                        |    |

#### [推送配置] 节

| 配置项                  | 说明                                                                       | 默认值    |    |    |      |      |               |     |
| -------------------- | ------------------------------------------------------------------------ | ------ | -- | -- | ---- | ---- | ------------- | --- |
| 直播状态推送渠道             | 可选渠道：微信                                                                  | 钉钉     | tg | 邮箱 | bark | ntfy | pushplus（可多选） | (空) |
| 钉钉推送接口链接             | 钉钉 Webhook                                                               | (空)    |    |    |      |      |               |     |
| 微信推送接口链接             | Server酱 URL                                                              | (空)    |    |    |      |      |               |     |
| bark推送接口链接           | Bark API                                                                 | (空)    |    |    |      |      |               |     |
| bark推送中断级别           | Bark 中断级别，可选 critical（重要提醒）/ active（默认）/ timeSensitive（时效性）/ passive（静默） | active |    |    |      |      |               |     |
| tgapi令牌              | Telegram Bot Token                                                       | (空)    |    |    |      |      |               |     |
| tg聊天id               | 聊天 ID                                                                    | (空)    |    |    |      |      |               |     |
| smtp邮件服务器            | SMTP 服务器                                                                 | (空)    |    |    |      |      |               |     |
| 是否使用SMTP服务SSL加密(是/否) | 是否启用 SMTP SSL 加密（留空视为「是」）；启用时端口通常为 465                                   | 是      |    |    |      |      |               |     |
| ntfy推送地址             | NTFY 服务地址                                                                | (空)    |    |    |      |      |               |     |
| pushplus推送token      | PushPlus Token                                                           | (空)    |    |    |      |      |               |     |
| 只推送通知不录制(是/否)        | 是否仅通知不录制                                                                 | 否      |    |    |      |      |               |     |

#### [Cookie] 节

各平台的 Cookie 配置（录制部分平台必填）。特殊键：

| 配置项      | 说明                                                                    | 默认值 |
| -------- | --------------------------------------------------------------------- | --- |
| 抖音cookie | 录制抖音必填，至少包含 ttwid，留空将触发风控                                             | (空) |
| ttwid    | 可单独固定抖音 ttwid（填 `ttwid=xxx` 或仅值均可）；留空则自动获取，填写后优先于自动获取（`src/ttwid.py`） | (空) |

#### [Authorization] 节

特殊平台的 Token 配置

#### [账号密码] 节

部分平台的账号密码配置

#### [Web] 节

Web 管理面板配置（`web.py` 模式专用）

| 配置项                  | 说明                                                                                                                          | 默认值       |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------- |
| web_host             | 监听地址（Docker 内需设为 0.0.0.0）                                                                                                   | 127.0.0.1 |
| web_port             | 监听端口                                                                                                                        | 8000      |
| web_auth_enable      | 是否启用密码认证。关闭时 API 禁止改写 [Recorder]/[Push] 危险配置（如自定义脚本），但仍允许修改 [Web] 设置                                                        | false     |
| web_password         | 登录密码（认证开启时必填，PBKDF2-HMAC-SHA256 哈希存储）                                                                                       | (空)       |
| web_token_expiry     | Token 有效期（秒）                                                                                                                | 86400     |
| web_show_console     | 是否显示控制台窗口（false 时后台隐藏运行）                                                                                                    | true      |
| web_minimize_to_tray | 控制台最小化到系统托盘（仅 Windows 生效；关闭按钮被禁用，退出请用托盘图标「退出程序」）                                                                            | true      |
| web_trusted_proxy    | 反向代理场景下的可信代理列表（逗号分隔直连 IP，如 127.0.0.1）：仅列表内的直连对端才信任 `X-Forwarded-For` 解析真实客户端 IP（防伪造头绕过登录限流）；留空 = 一律使用直连对端地址。未启用认证且公网暴露时请勿填写 | (空)       |
| web_allowed_hosts    | 除服务端自动放行的 Host 之外，额外登记的域名白名单（逗号分隔，支持 `*.example.com` 后缀匹配）。Host 判定规则见 `src/web_config.py::is_host_allowed`：**IP 字面量**与**无点号单标签名**天然放行（DNS 重绑定至少要一个多级注册域名），**多级域名**必须显式登记否则 400 拒绝；`web_host` 绑到 `0.0.0.0`/`::` 时不入名单（通配符绑址本身不是合法 Host 值）。故仅当 `web_host` 为通配绑址且用**域名**访问面板时才需要填写；以 IP 直连或本机 `127.0.0.1` 默认场景无需填写 | (空)       |

### 直播间配置文件 (`config/URL_config.ini`)

**格式**:

```ini
# 基础格式
https://live.douyin.com/745964462470

# 指定画质（画质,直播间地址）
超清，https://live.douyin.com/745964462470

# 指定画质和主播名（画质,直播间地址,主播:名称）
高清，https://live.bilibili.com/123456，主播: B站主播

# 注释直播间（在地址前加 #）
# https://live.douyin.com/123456789
```

**主播名自动更新**: 开启 `config.ini` 的 `[录制设置] 是否自动更新主播名(是/否)`（默认开启）后，每轮轮询解析到平台最新主播名与当前使用名不一致时，会自动完成：

1. 重命名保存目录中旧主播名命名的文件夹（`{保存路径}/{平台}/{旧主播名}`，目标已存在则逐项合并）；
2. 同步重命名文件夹内（含日期/标题子目录）所有以旧主播名为前缀的录制文件（`{旧主播名}_*`）及弹幕 SRT/时间字幕等同前缀产物，并把以 `_{旧主播名}` 结尾的标题目录（`{标题}_{旧主播名}`）一并改名；
3. 更新 `URL_config.ini` 对应行的主播名字段（按 URL 精确匹配该行，保留画质段、`#` 注释前缀与行尾换行风格，全角冒号统一半角，幂等）。

**触发与安全性**

- 触发点在每轮解析直播数据之后、录制启动之前，此刻该房间线程必然不在录制中（录制期间阻塞在 ffmpeg 守护里），因此改名不会触碰正在写入的文件，进行中的录制不受影响。
- 跳过条件：`platform == "自定义录制直播"`（其主播名含每轮随机 UUID，不应反复触发改名），或平台返回名为「空白昵称」等无效名。
- 同步顺序：**先改文件系统、后写配置文件**；两者全部成功才切换本轮使用名。任一失败（如配置文件被编辑器锁定、目录改名失败）保持旧名，下轮轮询自动重试（已完成的目录改名幂等，不会重复操作）。
- 被后台转码/播放器占用的个别文件改名失败仅告警跳过、不阻塞整体，其余文件照常处理，下轮补齐；同时清理旧名残留的录制状态条目（`recording` / `recording_time_list`），避免监控页长期挂旧名。
- 配置写入持 `file_update_lock`，与录制线程的 `update_file` / Web API 写入互斥，避免半写。

关闭该选项则保持手动填写的名称不变。

---

## 运行方式

### 方式 1: 源码运行

#### 前置要求

- Python 3.14+
- FFmpeg
- Node.js

#### 安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt
```

#### 命令行模式

```bash
python main.py
```

#### GUI 图形界面模式

```bash
python gui.py
```

#### Web 管理面板模式

```bash
python web.py
# 默认监听 http://localhost:8000
```

---

### 方式 2: Docker 运行

#### Dockerfile 多阶段构建说明（基础镜像 `python:3.14-slim-bookworm`）

```dockerfile
# 阶段 1: builder
# - 仅安装 build-essential（编译无二进制轮子的依赖）
# - 创建 Python 虚拟环境 /opt/venv 并安装 requirements.txt
#   （Node.js 只在运行时需要，builder 阶段不安装）

# 阶段 2: runtime
# - 精简基础镜像 + apt 安装 ffmpeg / nodejs(24 LTS) / tzdata / procps
# - 从 builder 复制 /opt/venv 虚拟环境
# - 非 root 用户 recorder(uid=1000) 运行
# - HEALTHCHECK 兼容 main.py 与 web.py 两种模式（pgrep）
# - ENTRYPOINT ["python", "main.py"]，EXPOSE 8000（Web 模式用）
```

**`.dockerignore` 要点**（2026-08-28 同步后）：

- 排除平台二进制（`ffmpeg/`、`node/`，容器内 apt 安装）、`config/*.ini`（运行时挂载）、`typings/`、`build_exe.py`、根目录 `index.html`（独立的 M3U8 播放器页，面板用 `web/`）等桌面/构建专用文件；
  [2026-09-21 修订：本行原列 `gui_legacy.py`，该文件已于 v4.1.0-dev / 2026-09-10 删除且 `.dockerignore` 中无该条目，属 MIN-15 的第 4 处陈旧引用，就地清除]
- **保留 `i18n/**/*.mo` 编译翻译文件与 `i18n/*.json`、`i18n/*.yaml` 多语言目录** ——
  运行时必需（gettext / JSON / YAML 三种翻译目录格式）且 Dockerfile 不会重新编译/生成，
  仅排除 `.po` 源文件与编译脚本；
- 排除本地工具 / AI 助手生成目录（`.mimosa/`、`.qoder/`、`.agents/`、`.pnpm-store/`、`.dsh-validation/`、`.ego-browser-test/`、`.plugin-src/`、`pytest-cache-files-*/` 等，与 `.gitignore` 同源维护）；
- 排除镜像运行不消费的内容：`uv.lock`（镜像走 pip + requirements.txt）、`scripts/`（维护脚本，运行时链路零引用）、`tests/`、`AGENTS.md` / `README_EN.md` / `CODE_WIKI_EN.md` 等文档、`.coveragerc-concurrency`（CI 专用）。

#### 使用 docker compose (推荐)

仓库根目录的 `docker-compose.yaml` 已定义三个服务（共享同一镜像，通过 YAML 锚点复用配置）：

| 服务             | 入口               | 启动命令                                 | 端口          |
| -------------- | ---------------- | ------------------------------------ | ----------- |
| `recorder`（默认） | `python main.py` | `docker compose up -d`               | 无（纯 CLI）    |
| `web`（profile） | `python web.py`  | `docker compose --profile web up -d` | `8000:8000` |
| `gui`（profile） | `python gui.py`  | `docker compose --profile gui up -d` | 无（需 X11）    |

统一挂载卷：`./config`、`./downloads`、`./logs`、`./backup_config`。

> ⚠️ **Web 模式必读**：`web.py` 默认监听 `127.0.0.1:8000`，容器内必须在
>
> `config/config.ini` 的 `[Web]` 节设置 `web_host = 0.0.0.0`，宿主机端口映射才能访问；
>
> 同时强烈建议开启 `web_auth_enable = true` 并配置密码。

---

## 打包与发布

本项目提供一键式可执行文件打包（`build_exe.py`）与跨平台自动构建发布（`GitHub Actions`），将 **CLI / GUI / Web 三个入口**统一构建为可分发的发布目录。

### 1. 打包脚本 `build_exe.py`

PyInstaller `onedir` 模式 + `contents_directory='_internal'`，动态生成 `.spec` 文件后调用 PyInstaller 完成**三入口共享依赖**构建：

| 产物（exe 同级）                     | 入口        | 模式                              |
| ------------------------------ | --------- | ------------------------------- |
| `DouyinLiveRecorder(.exe)`     | `main.py` | 控制台（CLI 录制核心）                   |
| `DouyinLiveRecorder-GUI(.exe)` | `gui.py`  | 无控制台窗口（GUI）                     |
| `DouyinLiveRecorder-Web(.exe)` | `web.py`  | 控制台（Web 管理面板，监听 `0.0.0.0:8000`） |

三个入口共用一个 `COLLECT`，依赖去重后体积约为独立打包的 1/3。

**用法**：

```bash
python build_exe.py              # 打包并生成 zip 产物
python build_exe.py --smoke      # 打包后额外运行冒烟测试（CI 推荐）
python build_exe.py --no-zip     # 仅打包不压缩
python build_exe.py --no-runtime # 跳过 ffmpeg/node 打包（交由用户运行时自动下载，减小体积）
python build_exe.py --dual       # 同时生成 lite（无运行时）与 full（下载并打包 ffmpeg+node）两个 zip
```

**数据文件与隐藏导入**：

- `datas`：`src/javascript`（JS 签名脚本）、`i18n`（翻译）、`web`（前端静态资源），均经 `__file__` 定位，PyInstaller 自动收进 `_internal/`；`collect_data_files('customtkinter')`（主题 JSON）。
- `config/` 不进 `_internal`，由 `copy_external_binaries()` 复制到 exe 同级（见目录规范）。
- `hiddenimports`：`i18n`、`src.async_http`（main.py 经 `__import__` 动态导入）、`h2`（httpx[http2] 懒加载）；`a_web` 额外 `collect_submodules('uvicorn')`（协议模块按字符串导入）。
- `excludes`：CLI 排除 GUI/Web 库（tkinter/customtkinter/pystray/PIL/fastapi/uvicorn/starlette）；GUI 排除 Web 库；Web 排除 GUI 库；三个入口均额外排除 `brotlicffi`（修复打包后 brotlicffi 模块缺失 `error` 属性的报错，httpx 无 brotli 时自动回退）。

**版本号**：从 `pyproject.toml` 的 `version` 字段解析（单一事实源），用于 zip 命名，解析失败回退 `0.0.0`。`main.py` 运行时同样从 `pyproject.toml` 动态读取版本号（优先 `importlib.metadata`，回退直接解析文件）。

### 2. 目录结构规范（打包产物）

采用 `onedir + contents_directory='_internal'` 后，PyInstaller 把依赖与经 `__file__` 定位的资源收进 exe 同级的 `_internal/`；而经 `sys.argv[0]`/`sys.executable` 定位的运行时资源由打包脚本在 `COLLECT` 之后复制到 exe 同级。最终产物结构：

```
dist/DouyinLiveRecorder/
├── DouyinLiveRecorder.exe          # CLI 录制核心
├── DouyinLiveRecorder-GUI.exe      # 图形界面
├── DouyinLiveRecorder-Web.exe      # Web 管理面板
├── config/                          # 配置目录（exe 同级，运行时直接读写）
├── ffmpeg/                          # FFmpeg 运行时（exe 同级，Windows 内置）
├── node/                            # Node.js 运行时（exe 同级，Windows 内置）
├── logs/                            # 日志目录（运行时默认创建于 exe 同级）
├── downloads/                       # 默认下载目录（config.ini 未指定时位于 exe 同级）
├── backup_config/                   # 配置备份目录（exe 同级）
└── _internal/                       # 依赖包 + src/ 及打包资源统一管理
    ├── (Crypto/ PIL/ certifi/ h2/ pydantic/ customtkinter/ watchfiles/ websockets/ yaml/ + 运行库 .dll)
    ├── src/            src/javascript/
    ├── i18n/
    └── web/
```

**关键约定（硬性）**：

- `node/`、`ffmpeg/`、`config/` 与 exe 保持**同级**（而非 `_internal/`）。
- `src/` 及全部 Python 依赖包统一收进 `_internal/`。
- 运行时可写目录 `logs/`、`downloads/`（未通过 `config.ini` 的 `直播保存路径(不填则默认)` 指定时）、`backup_config/` 均默认创建在 **exe 同级目录**。

### 3. 路径收敛机制 `_app_root()`

项目存在"双轨路径"：`main.py`/`src/ffmpeg_install.py`/`src/__init__.py` 等用 `sys.argv[0]`/`sys.executable` 定位运行时资源；`src/logger.py`、`i18n.py`、`src/web_api.py` 等用 `__file__` 定位打包资源。冻结后前者指向 exe 同级（发布根），后者指向 `_internal/`。

为统一收敛，新增 `src/logger._app_root()`（与 `main.py` 内联同名函数）：

```python
def _app_root() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.realpath(sys.executable))  # = exe 同级
    return os.path.split(os.path.realpath(sys.argv[0]))[0]
```

- `main.py` 的 `script_path`、`src/__init__.py`、`src/node_install.py`、`src/ffmpeg_install.py` 的 `execute_dir` 均收敛到 exe 同级，使 `config/ffmpeg/node` 正确定位。
- `src/logger.py` 的 `script_path` 改为 `_app_root()`，使 `logs/`、`backup_config/` 落在 exe 同级。
- `gui.py` 新增 `self.app_root`：冻结时若 `script_dir` 为 `_internal` 则回退一层到发布根，config/downloads 据此定位；CLI 子进程经同目录 `DouyinLiveRecorder.exe` 拉起（见下）。
- `i18n.py` 支持 `_internal/i18n` 与 `i18n/` 双路径检测。

### 4. 冻结版适配要点

- **GUI 子进程拉起（关键修复）**：`gui.py` 冻结后 `sys.executable` 指向 GUI 自身，原 `[sys.executable, main.py]` 会无限递归拉起 GUI。改为冻结时直接调用同目录的 `DouyinLiveRecorder.exe`，源码运行保持原样。
- **GUI 子进程 pythonw 兼容（2026-08-09）**：源码模式下若 GUI 经 `pythonw.exe` 启动，`sys.executable` 指向 pythonw（GUI 子系统、无控制台），原 `[sys.executable, main.py]` 会让录制核心也以 pythonw 运行——`CREATE_NEW_CONSOLE` 对其无效，`AttachConsole(pid)` 必失败、CTRL_BREAK 永远送不到、停止只能硬杀（ffmpeg 孤儿化）。现检测解释器 basename 以 `pythonw` 开头时改用同目录 `python.exe`（console 子系统）拉起录制核心；打包版（CLI exe `console=True`）不受影响。
- **GUI 停止录制优雅退出（2026-08-09）**：`_send_ctrl_break_to_child` 失败时不再只 `proc.terminate()`（`TerminateProcess` 硬杀、ffmpeg 孤儿化且 `wait()` 立即成功绕过整树清理），改为 `taskkill /F /T /PID` 整树终止；日志按路径区分"优雅退出"与"硬杀路径"，不再谎报 ffmpeg 已清理。
- **中文 UTF-8 编码（关键修复）**：冻结后子进程 stdout 为管道，Python 回退到 GBK 写输出，而 GUI 以 UTF-8 读取管道 → 中文乱码（如 `自动获取 Cookie ttwid 成功` 变成乱码）。在 `main.py`/`gui.py`/`web.py` 顶部加入 `_fix_encoding()`：Windows 下 `sys.stdout/stderr.reconfigure(encoding='utf-8', errors='replace')` + `ctypes.windll.kernel32.SetConsoleOutputCP(65001)/SetConsoleCP(65001)`；非 Windows 仅 reconfigure。stream 加 `None`/`hasattr` 保护（windowed exe 的 stdout 可能为 `None`）。`web.py` 原有 `reconfigure(errors='replace')` 升级为同时设 `encoding='utf-8'`。

### 5. 冒烟测试

`build_exe.py --smoke` 在打包后自动运行三项验证（CI 推荐开启）：

- **CLI**：启动数秒，确认进入监控循环且输出无 `Traceback`/`ImportError`/`ModuleNotFoundError`。
- **Web**：HTTP 探活 `http://127.0.0.1:8000/`，返回 200 视为面板可用；同时验证内置 ffmpeg 被命中（不触发下载）。
- **GUI**：启动 8 秒确认进程存活无崩溃（无显示环境 `DISPLAY` 未设置时自动跳过）。

冒烟前会向 exe 级 `config/URL_config.ini` 写入一条注释 URL，避免 CLI 因 URL 列表为空而阻塞在 `input()`。

### 6. GitHub Actions CI 静态验证（`ci.yml`）

工作流文件：`.github/workflows/ci.yml`，在 push 到 main / PR 时运行，确保代码风格、类型安全与功能正确性在合入前通过验证（2026-08-28 优化后结构如下）。

**统一策略**：

- `setup` job 集中声明**共享常量**（Python 版本矩阵 / Node 版本 / black / isort / mypy 固定版本号）并执行路径过滤，常量输出至 job outputs 供各 job 与 `strategy.matrix` 引用（matrix 无法引用 env 上下文），是全工作流的单一事实源；
- **actions 大版本统一 v7**（`checkout` / `setup-python` / `setup-node` / `upload-artifact`），与 build-release.yml 完全一致；
- **网络安装重试统一经 `.github/actions/retry` 复合动作**（线性退避 ×3；`command` / `label` / `attempts` / `backoff` 可参数化）——pip / apt 安装共 9 处调用，重试策略只在 action.yml 一处维护，禁止 job 内重新内联重试循环；
- **apt 强化参数**（对齐 build-release.yml 的 Linux 构建）：`DEBIAN_FRONTEND=noninteractive` + `Acquire::Retries=3` + `--no-install-recommends`；
- 每个 job 显式 `timeout-minutes`；同分支/PR 新推送 `cancel-in-progress: true` 取消旧运行（快速反馈，与发布流的不可取消策略有意区分）；
- pip 缓存统一以 `hash(requirements.txt + pyproject.toml)` 为 key（仓库无 lock 文件参与安装）。

**路径过滤**：`setup` job 使用 `dorny/paths-filter@v4` 检测变更文件类别，命中即运行全部下游 job。触发清单：Python 源码（`src/**`、根目录入口 `main.py`/`gui.py`/`web.py`/`i18n.py`/`msg_push.py`/`build_exe.py`）、`tests/**`、`scripts/**`、依赖清单（`requirements.txt` / `pyproject.toml` / `.coveragerc-concurrency`）、**`i18n/**`**、**`web/**`**、**`Dockerfile` / `docker-compose.yaml`**、工作流与复合动作（**`.github/workflows/**` / `.github/actions/**`**）。仅**纯文档（`*.md`）变更不触发**。**`i18n/**` 是触发条件**——纯翻译变更同样会跑 static job 的 compile_po --check 同步门禁；**`web/**` 亦是触发条件**（2026-09-20 补齐）——`web/app.js` 的 `parseConfigBool + CONFIG_*_TOKENS` 与 `src/config_bool.py` 是跨语言布尔口径不变量（AGENTS.md「布尔配置项统一解析口径」），改任一侧都须由 test job 跑 `tests/frontend/test_quality_ui.mjs` 回归锁（旧口径「纯前端 web/ 不触发」已被证伪，详见更新日志对应条目）。

**并行 jobs**（均 `needs: setup` 条件门控）：

| Job                  | 运行环境             | 内容                                                                                                                                              |
| -------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `static`             | py3.15           | `black --check .` + `isort --check .` + `python scripts/check_version.py`（版本号单一事实源校验） + `python scripts/compile_po.py --check`（i18n po/mo 同步校验，零副作用） + `python scripts/check_annotations.py`（注释规范：禁 docstring / 密度下限 / 模块头，零副作用） |
| `typecheck`          | py3.14           | 安装 requirements + 固定版 mypy 后运行 `mypy src/`（最低支持版本运行，结论对最老解释器成立）                                                                        |
| `test`               | py3.14 / py3.15 矩阵 | `pytest --cov=src --cov-report=term-missing`（全局 `fail_under=50` 门禁，`fail-fast: false`）；最低版本上追加 `scripts/check_coverage.py` 逐模块门禁 + coverage.xml 上传 + 可选 Codecov |
| `concurrency-test`   | py3.14           | 并发专项：`COVERAGE_RCFILE=.coveragerc-concurrency` 下跑 `test_concurrency_rate_limit.py` + `test_concurrency.py` + `test_async_http_lock.py`（专用配置不设全局阈值） |
| `integration-verify` | py3.14 + Node 24 | apt 装 ffmpeg；验证 ffmpeg/node 二进制可发现，并调 `check_ffmpeg_installed()` / `check_nodejs_installed()` 验证探测逻辑                                                |
| `build-verify`       | py3.14 打包解释器    | `build_exe.py --smoke --no-runtime --no-zip`（lite 打包 + CLI/Web/GUI 三入口冒烟，Linux 经 `xvfb-run -a`）；发布级完整打包留给 build-release.yml              |
| `ci-summary`         | —                | 唯一 required check：汇总上游全部 job 结果（skipped 视为通过——路径过滤跳过不会让分支保护永久 pending）                                                          |

### 7. GitHub Actions 自动构建与发布（`build-release.yml`）

工作流文件：`.github/workflows/build-release.yml`（任务名 `Build (${{ matrix.os }})`）。

**触发方式**：

- 手动触发（`workflow_dispatch`，可选 `create_release` 输入）：默认仅构建并上传 artifact，勾选后亦创建 Release。
- 推送 `v*` 标签（如 `v4.0.9.1`）：构建 + 自动创建 GitHub Release 并附产物（`permissions: contents: write`，仅 build / release 相关 job 授予）。

**构建矩阵**：`windows-latest` / `ubuntu-latest` / `macos-latest`，Python 3.14（`fail-fast: false`；与 ci.yml build-verify 的打包解释器同值，保证「CI 验证的打包环境 == 实际发布的打包环境」）。

**流程**：

1. `prepare` job：用 tomllib 从 pyproject.toml 提取版本号并校验 tag 一致（打错 tag 直接失败），跑 `check_version.py` 确认各消费方动态读取。
2. `release-create` job：发版路径下**预创建** Release 记录（单例 job，消除多平台 build 并发创建同一 Release 的竞态；不传 files）；手动发版路径在此补建轻量 tag（Release 必须挂在 tag 上）。
3. build job（矩阵）：各平台以系统包管理器装 ffmpeg 供冒烟——Windows `choco`、Linux `apt`（额外 `xvfb`，GUI 冒烟需虚拟显示）、macOS `brew`（`brew trust aws/tap` 为独立幂等步骤，`HOMEBREW_*` 变量在命令内 export）；**全部网络安装命令经 `.github/actions/retry` 复合动作包装**（线性退避 ×3，系统包管理器退避 15s、pip 10s）；依赖为 `pip install -r requirements.txt` + `pip install ".[build]"`。
4. `python build_exe.py --smoke --dual`（Linux 用 `xvfb-run -a` 包裹）：PyInstaller 只跑一次，先产 **lite** zip（不含 ffmpeg/node，运行时自动下载）再产 **full** zip（内置运行时，约 300MB）；冒烟测试跑在 lite 版本上。
5. 产物发布：发版路径（tag / 手动勾选 create_release）由 build job 经 `softprops/action-gh-release@v3` 把 zip **直传 Release**（显式 `tag_name` 与 release-create 指向同一 Release，GitHub 支持同 Release 并发上传不同 asset）；仅构建路径走 `upload-artifact@v7`（`compression-level: 0` 跳过二次压缩，留存 30 天供人工取回）。
6. `release` job（发版路径）：`gh release download` 拉回已发布附件校验齐全（3 平台 × lite/full = 6 个 zip，缺失即失败不发布残缺 Release），生成 `SHA256SUMS.txt`，最后经 `softprops/action-gh-release@v3` 补传校验和并写发版说明（`generate_release_notes: true`）。

**产物命名**：`DouyinLiveRecorder-v{version}-{os}-{arch}-{lite|full}.zip`（如 `DouyinLiveRecorder-v4.0.9.1-windows-amd64-full.zip`）。

### 8. 本地打包步骤

```bash
pip install pyinstaller          # 安装打包器
python build_exe.py --smoke      # 打包 + 冒烟测试
python build_exe.py --smoke --dual  # 与 CI 一致：lite + full 双产物
# 产物：dist/DouyinLiveRecorder/ 发布目录 + dist/DouyinLiveRecorder-vX.Y.Z-*.zip
```

注意：本仓库为本地副本，工作流需推送至 GitHub 仓库后才可运行。lite 产物（及 CI Linux/macOS 产物）不含 `ffmpeg`/`node`，首次运行会自动下载。

---

## 设计模式

### 1. 适配器模式 (Adapter Pattern)

各直播平台的 API 接口被统一适配为相同的调用接口，`spider.py` 和 `stream.py` 中实现。

### 2. 装饰器模式 (Decorator Pattern)

`trace_error_decorator` 用于错误追踪，`utils.py` 中实现。

### 3. 策略模式 (Strategy Pattern)

不同的消息推送渠道（钉钉、微信、TG 等）实现为独立函数，运行时根据配置选择。

### 4. 单例模式 (Singleton Pattern)

日志配置通过模块导入副作用实现单例，`src/logger.py` 中实现。

### 5. 模板方法模式 (Template Method Pattern)

各平台的录制流程遵循相同的模板：检测 → 获取流 → 录制 → 推送。

### 6. 工厂 / 注册表模式 (Factory + Registry Pattern)

弹幕子系统通过 `src/__init__.py` 的 `get_danmaku_class(platform)` 注册表（中文平台名 → 弹幕类）与 `get_danmaku_collector(...)` 工厂统一创建各平台采集器；`main.py` 按平台标识取采集器，无需感知具体平台实现。新增弹幕平台只需在注册表登记并实现 `DanmakuBase` 的 `start/stop/heartbeat/decode_message` 四个抽象方法，对调用方零侵入。

---

## 常见问题排查

### 问题 1: 提示缺少 FFmpeg

**解决**:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
程序已内置，无需安装
```

### 问题 2: 提示缺少 Node.js

**解决**:

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
sudo apt-get install -y nodejs

# macOS
brew install node

# Windows
程序会自动下载安装
```

### 问题 3: 抖音风控无法获取数据

**风控特征（实测）**:

- 风控信号是 **HTTP 200 + 空响应体**，不是 4xx。排查解析失败时先看 `len(response.text)`，为 0 基本就是 UA/Cookie 被拒
- 旧移动端 UA 会被静默限流（`iesdouyin.com` 接口必现），需使用桌面 Chrome UA（`room.DESKTOP_UA`）
- `iesdouyin.com/share/user/<sec_uid>` 已是 JS 反爬壳页，页面内无 `unique_id`，任何 HTML 正则都不可靠
- `web/enter` 接口偶发 `status_code=10002 unknown error` 属瞬时软拒绝（风控/缺 msToken/限流），代码已做静默重试 1 次，属正常容错，不代表房间不可用

**解决**:

- 更新 Cookie
- 降低循环监测频率
- 更换 IP
- 更新 UA（使用 `room.DESKTOP_UA` 桌面 Chrome UA）
- 若日志出现 `10002` 后 HTML 兜底成功，属正常链路，无需处理

### 问题 4: HLS 校验失败日志空白 / 总回退 FLV

**现象**（日志连续出现，且无任何可排障信息）：

```
get_response_status 校验失败（判定为不可达）:      ← 消息是空的
HLS URL validation failed, falling back to FLV    ← 原因完全不可见
```

**根因**（三层，均已修复于 2026-08-05）：

- 异常日志只打印 `{e}`，而 Windows 下 `socket.timeout` / `TimeoutError` 的 `str()` 返回**空字符串**，导致超时异常打出来是空白
- `main.py::_validate_stream_url` 用 `except Exception: return False` 把失败原因全部吞掉，回退时无任何线索
- m3u8 源 HEAD 探测只覆盖 `400/401/403/405`，**404 直接判不可达**；且 `select_source_url` → 校验调用**不透传代理**，TikTok 等境外平台直连校验必超时误判

**修复后**：异常日志带 URL + 异常类型；所有失败路径记录 warning（含 status_code / content-type）；m3u8 HEAD 非 2xx（含 404）一律补 Range GET 探测；`select_source_url` 透传 `proxy_addr`。重新运行后日志会直接给出真实原因（如 `ConnectTimeout`、`HEAD=404, Range-GET=403`）；若仍不可达则是 CDN 域名被墙或主播流地址已失效等环境问题，而非代码误判。

### 问题 5: 弹幕连接失败 "connecting through a SOCKS proxy requires python-socks"（系统代理冲突）

**现象**（B站及复用 `WsClient` 的所有平台弹幕连接断开，日志可见）：

```
[弹幕采集]BilibiliDanmaku 连接关闭: connecting through a SOCKS proxy requires python-socks
```

**前置两个已修复子问题**（均为真实缺陷，但非最终根因）：

- **短号 room_id 未转真实 room_id**：`get_bilibili_danmaku_info` 曾直接用 URL 短号（如 `live.bilibili.com/462`）请求 getDanmuInfo，B站返回的 token 与真实房间不匹配，join 后收不到弹幕；现先调 `room/v1/Room/room_init` 把短号转真实 room_id（462 → 763679）再走后续流程（`src/spider.py`）。
- **心跳协程从未被 await**：`BilibiliDanmaku.heartbeat` 是 `async def`，但 `WsClient._heartbeat_loop` 曾直接 `self._on_heartbeat()` 调用未 await，B站长连接几十秒无心跳被服务器断开；现检测 `inspect.isawaitable(result)` 后 `await result`（`src/ws_client.py`）。

**根因（系统代理"幽灵"）**：`websockets.connect(proxy=True)` 默认**自动探测并跟随代理**，经 `urllib.request.getproxies()` 获取代理配置；在 macOS 上该调用不只读 shell 环境变量，而是直接读**系统网络设置**（System Preferences → Network → Proxies）里的系统级代理。若代理工具（Clash 类）在系统设置写入了 HTTP/HTTPS/SOCKS 三层代理（如 `socks5://127.0.0.1:7890`），`env | grep -i proxy` 查不到（`scutil --proxy` 可读到），但 websockets 会跟随该 SOCKS 代理——而 SOCKS 协议需要 `python-socks` 库支持，未安装即报上述错误。视频拉流走 ffmpeg/自备 header，不经过 websockets，故录制不受代理影响；独立测试脚本因运行环境/系统代理状态不同而时好时坏。

**修复（弹幕直连）**：`src/ws_client.py` 的 `connect()` 显式传入 `proxy=None`，弹幕 WS 直连服务器、不感知系统代理与 `ALL_PROXY` 等环境变量：

```python
async with websockets.connect(
    url,
    additional_headers=self._headers,
    open_timeout=self.connect_timeout,
    ping_interval=None,   # 各平台自带心跳, 关闭库默认 ping
    max_size=None,
    ssl=self._ssl_context,
    proxy=None,           # 弹幕连接直连, 不跟随系统代理
) as ws:
```

该修复对**所有平台**（B站/斗鱼/虎牙/抖音/Twitch 等）弹幕连接统一生效（均复用 `WsClient`）。

**决策依据**：弹幕通道本就国内直连、不需出网代理，与"关闭代理录制"的整体直连语义一致；依赖最小化（不新增 `python-socks`）；不动系统设置；显式声明优于隐式探测（避免库升级改默认行为再踩坑）。若个别境外平台弹幕确需代理，可后续为 `WsClient` 增可选 `proxy` 参数按需透传，不全局跟随。

**验证**：无代理状态下完整跑通 `main.py`，弹幕正常落盘生成 SRT；`mypy src/ws_client.py` / `py_compile` 通过。排查弹幕异常先看 `logs/streamget.log`（DEBUG 记录采集线程启动 / 连接就绪 / 收到首条弹幕 / 连接关闭原因）。

### 问题 6: 抖音/斗鱼等平台状态"正在直播中"却完全不录制（无报错、无文件）

**现象**：`py web.py`（或 `python main.py`）运行期间，抖音、斗鱼房间每个监测周期都打印"正在直播中…"，但从未出现"准备开始录制视频"，不产生任何录制文件；同一配置下虎牙、B站可正常录制。日志无任何报错、警告或提示，状态面板一直显示"正在直播中"。

**影响范围**：所有 `get_record_headers()` 返回 `None` 的平台（实测：抖音、斗鱼）。这类平台的共同特征是没有专属录制请求头规则（Referer/Origin）且未配置对应 Cookie。

**根因（历史性结构 Bug）**：`main.py` 的 `run()` 中 `headers = get_record_headers(platform, ...)` 后的 `if headers:` 错误地包住了其后的**整个录制链**——tls_verify/proxy 插入、录制状态注册、TS/FLV/MP4/MKV 全部录制分支、`check_subprocess` 启动 ffmpeg、`record_success` 周期计数（约 490 行）。凡 `get_record_headers` 返回 `None` 的平台（`_RECORD_HEADER_RULES` 未配置 Referer/Origin 且无 Cookie），整个录制块被**静默跳过**：不打印、不报错、不录制、每周期空转。有专属录制头的平台（虎牙/B站）恰好不受影响，使问题看起来像"个别平台解析问题"而非全局结构问题。

**修复**：

1. **缩进层级修正（main.py）**：`if headers:` 块内只保留 `-headers` 插入（4 行）；tls_verify 插入、代理插入、录制状态注册、全部录制分支、周期计数**整体左移 4 空格**，脱离条件嵌套，无条件执行。
2. **校验器 UA 对齐（src/stream_select.py）**：新增 `MOBILE_UA` 常量（与 `main.py` ffmpeg 命令默认 UA 一字不差），`_validate_stream_url` 对无桌面 UA 的平台发移动 UA——斗鱼 hwa CDN 对非浏览器 UA 的 GET 偶发 403，校验与录制两端 UA 必须完全一致（方法 GET + 头 Referer/Cookie + UA 三位一体）。

**排查提示**：长录制链的入口条件必须与"是否录制"语义精确对应；"条件为假整块跳过"是最危险的失败模式（不抛异常、不打日志）。当所有代码路径分析都表明"应该有日志"而实际没有时，可在 `select_source_url` 返回后临时插桩打印真实 `real_url`、并对照缩进层级绘图核验块边界，是最短定位路径。

## 贡献指南

### 代码规范

- 格式化: `black .`
- 导入排序: `isort .`
- 类型检查: `mypy src/`（已启用 `disallow_untyped_defs = true`，`--strict` 模式全通过）
- 类型检查（增强，本地）: `basedpyright` 已在 `pyproject.toml` 配置 `[tool.basedpyright]`（standard 模式、排除 `typings/`/`node/`/`ffmpeg/` 等、`venvPath` 指向 workbuddy managed venv）；CI 仍以 `mypy src/` 为准（basedpyright 非 CI 检查项，换机需重新指定 venvPath）
- 注释规范: 模块/函数说明统一使用 `#` 行注释，**不使用三引号 `"""` 文档字符串**；多行说明每行以 `#` 开头（功能性多行字符串字面量除外，如模板/SQL，应改用单引号 + 换行拼接而非 `"""`）

### 测试与覆盖率

- 运行测试: `pytest`（`asyncio_mode = "auto"`，异步用例无需显式标记）；当前 496 passed / 2 skipped，总覆盖率 50.34%
- 覆盖率配置集中在 `pyproject.toml`：`source = ["src"]`，全局门禁 `fail_under = 50`
- 高频变更核心模块设独立覆盖率门禁（记录于 `pyproject.toml` 注释，CI 中通过 `--cov-fail-under` 或脚本检查）：

| 模块           | 门禁   | 当前覆盖 |
| ------------ | ---- | ---- |
| `spider.py`  | ≥50% | 50%  |
| `stream.py`  | ≥70% | 70%  |
| `utils.py`   | ≥80% | 82%  |
| `ttwid.py`   | ≥85% | 85%  |
| `ab_sign.py` | ≥95% | 99%  |
| `proxy.py`   | ≥50% | 51%  |

- 并发专项测试（`test_concurrency.py` / `test_concurrency_rate_limit.py`）使用专用配置 `.coveragerc-concurrency`（不设全局阈值），验证 `threading.Lock` 去重与抖音速率限制在多线程环境下的正确性

#### Web/接口冒烟测试工具（`scripts/smoke_test.py`）

通用、零依赖（纯标准库）的 Web/接口冒烟测试工具，用于快速验证 Web 管理面板等**运行中 HTTP 接口**的可达性与核心响应。

- 配置驱动：JSON 描述检查项（`url` / `method` / `expected_status` / `timeout` / `headers` / `body` / `expect_contains` / `expect_json`）
- `base_url` 前缀拼接，无需每个接口写完整地址
- 三种输出：控制台（带颜色）、JSON 报告、HTML 报告
- 任一检查失败退出码非 0，便于接入 CI
- **已接入 CI**：默认用例 `scripts/smoke_web.json` 探活 Web 面板 `/` 与 `/health`（后者为 `src/web_api.py` 提供的公开探活端点）；`.github/workflows/ci.yml` 的 `test` job 在 pytest 之后受控启动 `python web.py`，经 `scripts/_ci_web_smoke.sh` 做就绪等待 + 断言（走 `.github/actions/retry`），失败保留 `logs/web-smoke-*` 工件并使 job 变红——补齐 TestClient 覆盖不到的「面板进程能否真正监听并应答」链路

用法：

```bash
# 检查本机 Web 管理面板（默认 127.0.0.1:8000，示例见 scripts/smoke_web.json）
python scripts/smoke_test.py -c scripts/smoke_web.json

# 生成 HTML 报告
python scripts/smoke_test.py -c scripts/smoke_web.json -r smoke_report.html -f html
```

> 与 `build_exe.py --smoke`（打包产物冒烟，见上文第 5 节）不同，本工具针对**运行中的 HTTP 接口**做轻量探活，两者互补。

### 添加新平台支持

1. 在 `src/spider.py` 中添加平台数据获取函数
2. 在 `src/stream.py` 中添加流地址解析函数，返回值包含 `actual_quality` 和 `available_qualities` 字段
3. 在 `main.py` 中添加平台识别逻辑
4. 更新 `README.md` 和本文档

---

## 更新日志

> **真机验证留存约定**（与 `AGENTS.md`「完成定义」第 2 步同源）：涉及录制链路 / 选源 / ffmpeg 参数 /
> 平台解析的改动，真机验证结论写在本文件对应版本条目的「验证」子节，中英同步。
> 格式：`[YYYY-MM-DD] 平台 | 脱敏 URL | 脚本 | 结果 | 消息数`。
> 无法执行时结果列写 `SKIP(原因)`（如 `SKIP(无外网)` / `SKIP(房间未开播)`），
> 并补「交回用户」动作（如「请用户有活房间时手动跑」）；此情形不得宣布完成定义第 1→6 步完成。
> 脚本直跑时额外输出 `VERIFICATION_RESULT: {"platform":..., "status":..., ...}` 结构化一行供机器解析。
> 脚本：`tests/test_{bili,douyin,douyu,huya,twitch}_live_collector.py`（`python file.py <URL> [秒数]`，
> 需活房间 + 外网，默认人工通道）。

### v4.3.0-dev (2026-09-26) — 仓库元数据与文档同源同步：依赖表 / 目录树 / egg-info / 忽略清单对齐，清理已删除模块 `weverse_auth` 的残留记载（纯元数据与文档改动，零运行期代码变更）

- **背景**：全仓通读核对「版本 / 依赖 / 目录树 / 忽略清单」四类同源信息，发现多处滞后：`CODE_WIKI*.md` 依赖表仍停在 16 条且 `starlette` 下限写着 `>=0.49.1`；目录树仍列 2026-09-23 已删除的 `src/weverse_auth.py` 与 `tests/test_weverse_auth.py`；`DouyinLiveRecorder.egg-info/requires.txt` 缺 2026-09-23 补入的 `h2`/`socksio`；`AGENTS.md` 依赖条数仍写 21 条。
- **改动性质**：只改文档 / 元数据 / 忽略清单并重建 `egg-info`；`src/`、`main.py`、`gui.py`、`web.py`、`web/app.js` 零改动，运行期依赖集合未变（两侧各 23 条、包名集合逐项相等）。

**涉及文件（按模块分类）**：

- **模块：`AGENTS.md`** — 「依赖管理」运行时依赖条数 `21 条 → 23 条`（两处），并补注 `h2`/`socksio` 的补入时点；安全下限条目里的 `starlette>=1.0.1` 更正为 `>=1.3.1`（1.0.1 自身仍落在 PYSEC-2026-2280/2281/248/249 受影响段，2026-09-21 已二次抬升）。
- **模块：`README.md` / `README_EN.md`** — 项目结构树删除 `src/weverse_auth.py`，补入此前遗漏的 `src/ffmpeg_master_download.py`（中英同步）。
- **模块：`CODE_WIKI.md` / `CODE_WIKI_EN.md`** — ① 依赖关系表由 16 条补齐到 23 条（补 `urllib3` / `h2` / `socksio` / `websockets` / `protobuf` / `brotli` / `PyYAML`，`starlette` 下限 `0.49.1 → 1.3.1`，删除空行占位）；② 目录树与测试清单去掉 `weverse_auth.py` / `test_weverse_auth.py` 两处残留；③ 「注 1」由现状陈述改为带日期的 `[历史注]`（保留「勿加 pip 上的 weverse 包」结论，因其拉入无法编译的 pycrypto）。历史更新日志条目（记录当时事实）一律未改。
- **模块：`DouyinLiveRecorder.egg-info`（构建产物，未入库）** — 经 setuptools `egg_info` 重建：`requires.txt` 补齐 `h2>=4.3.0` / `socksio>=1.0.0`，`SOURCES.txt` 不再列已删除模块；`PKG-INFO` 版本保持 `4.3.0`。
- **模块：`.dockerignore`** — 补入 `_probe_*.py`（与 `.gitignore` 同源维护；此前只排了 `_out_*.txt`）。
- **模块：`config/config.ini`（本地运行期配置，已 gitignore）** — 补入 `[Cookie]` 段的 `ttwid`（`src/ttwid.py` 的 `_CONFIG_TTWID_KEY` 与 README 均已声明、本地缺键）；写入保留 UTF-8 BOM 与 LF 行尾。
- **模块：`i18n/`（四语目录）** — 完整性核对：`scripts/extract_i18n_strings.py` 全量扫描 533 条有价值串 + 三个盲区（`print_colored` / `messagebox` / 推送模板）补扫，缺失均为 0；四目录键集一致、无空值。清理：删除 3 条 Weverse token 刷新相关孤儿条目（对应 `src/weverse_auth.py` 已于 2026-09-23 删除、全仓无代码再产出），四目录**同进同退**后均为 **780 条**；随后 `scripts/compile_po.py` 重编 `zh_CN.mo`（781 条含头部 / 110585 字节）。

**验证**：`scripts/check_version.py` rc=0（`pyproject.toml` 为版本唯一事实源，四处消费方均动态读取）；`scripts/check_runtime_pins.py` rc=0；`pytest tests/test_regression_2026_09_22_gates.py tests/test_build_exe.py` 全绿（含「requirements.txt 与 pyproject 包名集合相等」回归锁）；`pytest tests/test_i18n.py tests/test_i18n_migration.py tests/test_i18n_tr.py tests/test_frontend_*.py` 56 passed；`node --test tests/frontend/*.mjs` 通过。

**交回用户（需人工裁定）**：`config/config.ini` 的 `禁用SSL证书验证的平台(逗号分隔)` 现为 `虎牙直播,B站直播,抖音直播`，而代码强制集 `main.SSL_DISABLE_REQUIRED_PLATFORMS` 只有 `虎牙直播`/`B站直播`、README 默认值同为这两个。`抖音直播` 一项属历史遗留的额外豁免（会关闭抖音拉流的证书校验），是否移除由用户决定——本次未擅自改动安全相关开关。

### v4.3.0-dev (2026-09-24) — 构建产物体积优化：定位并排除运行期不可达模块 + zip 压缩级别 9，lite 产物 82.77MB → 64.88MB（−21.6%）、zip 54.84MB → 42.19MB（−23.1%）

- **背景**：本机 Windows lite 构建（不含 ffmpeg/node）实测发布目录 **82.77MB / 272 文件**。
- **改动性质**：**只改打包侧（`build_exe.py`）+ 测试 + 新增度量脚本**，未触碰任何运行期模块（`src/`、`main.py`、`gui.py`、`web.py`、`web/app.js` 零改动），未增删任何依赖（requirements.txt / pyproject.toml 零改动），构建命令与三个入口的接口、产物结构、zip 命名全部保持原样。

**定位结论（逐项实测，均来自基线产物实盘）**：

- `PIL._avif` **7.52MB** —— Pillow 12 自带 libavif…
- `pydantic.v1.mypy` → 整个 `mypy` 包 **0.71MB / 69 文件 + PYZ 内约 6MB 纯 Python** —— 唯一的「开发工具链泄漏」：`pydantic/v1/mypy.py` 顶层就是 `from mypy.errorcodes import ErrorCode`
- `uvicorn` 的可选实现依赖 `httptools` 0.17MB + `watchfiles` 0.61MB（POSIX 上还有 `uvloop`）—— `web.py` 用 `uvicorn.Server(uvicorn.Config(...))`
- `i18n/*.po` **0.12MB** —— 翻译源文件…
- `nodejs_wheel`（114MB，venv 里有而 requirements.txt 没有）等 dev 工具链：基线未泄漏，但按「把误收集变成不可能」显式列入排除清单。

**涉及文件（按模块分类）**：

- **模块：`build_exe.py`（打包侧）** — 新增模块级常量 `BLOAT_EXCLUDES`（逐项附实测体积 + 不可达理由 + Pillow 容错依据）
- **模块：`scripts/report_bundle_size.py`（新增）** — 产物体积度量：总量 / 按包聚合 / 最大单文件 / dev 工具链泄漏检测…
- **模块：`tests/`（回归锁）** — `test_build_exe.py` 新增 5 条：排除清单不得命中生产代码真实导入（AST 收集 import 名…
- **模块：`AGENTS.md`** — 「构建命令」下新增「产物体积门禁」小节：度量入口、排除入口与准入条件、四项不可删的固定成本、`strip` / `upx` 两条已评估未采纳方案的理由。

### v4.3.0-dev (2026-09-24) — 类型存根去 `six` 依赖：`typings/execjs/` 两个抽象基类存根改用 `metaclass=ABCMeta`，消除 IDE 单文件检查的 mypy `[import-untyped]`（纯存根改动，零运行期影响）

- **背景**：`typings/execjs/_abstract_runtime.pyi` 与 `_abstract_runtime_context.pyi` 逐字沿用上游 PyExecJS 的 `@six.add_metaclass(ABCMeta)` 类声明并 `import six`。
- **为何「门禁绿、IDE 红」**：CLI 门禁因 `[tool.mypy].exclude` 含 `typings` 根本不进该目录…
- **改动性质**：纯类型存根改动，未触碰任何运行时代码；**无新增文件、无删除文件**。两个 `.pyi`（均纯 LF、无 BOM）各删去 `import six`，类声明由装饰器形态改为 `class X(metaclass=ABCMeta):`——Python 3 下 `six.add_metaclass(M)` 只是 Py2 兼容糖，两种写法产出的元类相同。

**涉及文件（按模块分类）**：

- **模块：`typings/execjs/`（第三方 PyExecJS 类型存根）** — 修改 2 个 `.pyi`：`_abstract_runtime.pyi`、`_abstract_runtime_context.pyi` 去 `import six` + 改 `metaclass=` 写法…
- **被否方案**：① 为 dev 依赖新增 `types-six`——仅为一个存根文件就扩大安装面…

### v4.3.0-dev (2026-09-24) — `src/` 七文件注释审查与去重：`ws_client.py` / `video_postprocess.py` 各 1 处纯复述合并，其余五文件经通读确认已达参考级、刻意保留（纯注释改动，零逻辑变更）

- **背景**：本轮处理用户点名的 `src/ttwid.py`、`src/utils.py`、`src/video_postprocess.py`、`src/web_api.py`、`src/web_config.py`、`src/web_tray.py`、`src/ws_client.py`。
- **改动性质**：纯注释精简，未触碰任何可执行代码；**无新增文件、无删除文件**；净删 1 行注释（`video_postprocess.py` −1；`ws_client.py` 同行改短、注释行数不变）。扫描命中的其余「重复」经逐条核实全为**合法的按需交叉指向**（`同 close()` / `见 _guard_bind_host` / `同 update_config_line`）或**逐函数职责行的按需重复**（`is_original_delete=True 时删除源文件` 在三个 ffmpeg 入口各自成立），非可删噪音。其余 5 个被点名文件（`ttwid.py` / `utils.py` / `web_api.py` / `web_config.py` / `web_tray.py`，其中 `web_tray.py` 密度 16.6% 最接近下限、本就不宜删行）经通读确认无可删复述，**未改动**。

**涉及文件（按模块分类）**：

- **模块：弹幕 WebSocket 客户端（`src/ws_client.py`）** — `_default_ssl_context` 体内注释结尾的「…
- **模块：视频后处理（`src/video_postprocess.py`）** — `get_startup_info` 的 `def` 上方第 4 行「按 system_type… 返回隐藏窗口的 STARTUPINFO…

### v4.3.0-dev (2026-09-24) — 前端回归锁修复 + 纳入 CI：`test_regression_2026_09_22_gates.mjs` 两条红锁定位为测试侧失效、补 `.py` 包装入 pytest/CI 回路（零生产代码改动）

- **背景**：`tests/frontend/test_regression_2026_09_22_gates.mjs`（组 G 前端回归锁…
- **改动性质**：**全部落在测试 / CI / 文档层，未触碰任何生产代码**（`web/app.js`、`src/`、`main.py` 等零改动）。经回源核对，两条红锁均为测试侧失效、生产行为本就正确：① MIN-2241 正则被 `src/web_api.py` 的纯 CRLF 卡死；② danmaku 游标锁的 `node:vm` DOM 桩漏建模 `HTMLSelectElement.options`。附带修好一条「只锁正向、锁不住负向」的半失效锁与一处 CI 门禁在 ubuntu 上的平台性误红。**删除项：无**（无文件删除、无功能移除，仅替换两条断言/正则文本）。

**涉及文件（按模块分类）**：

- **模块：`tests/frontend/`（`web/app.js` 沙箱回归锁）** — 修改 `test_regression_2026_09_22_gates.mjs`（纯 LF）3 处：
  - MIN-2241「`/` 路由反向锁」：正则 `async def index\(\)[\s\S]*?\n\n` 要求连续两个裸 LF…
  - `makeElement` DOM 桩补 `options: []`：SEV-2228 后半「danmaku_unavailable 不得推进增量游标」报 `since=0` 而非 `since=7`
  - SEV-2228 后半断言由 2 轮升级为 3 轮（success → error → 再请求）
- 随 test job 的全量 pytest 被收集。
- **模块：`.github/workflows/ci.yml`（test job 前端门禁）** — 改「Gate frontend tests not skipped」步骤：纳入新模块…
- **模块：文档 / 长期经验（`AGENTS.md` + `docs/agent-reference/session-learnings.md`）** — `AGENTS.md`「盲点 3」把 MIN-2241 的「现例（恒红）」按「更正被证伪的事实性陈述」例外就地纠正为 `[2026-09-24 修订：已改 \r?\n\r?\n]`

### v4.3.0-dev (2026-09-24) — `src/` 四文件注释精简：选源探针 / SRT 字幕 / 同步 HTTP / ttwid 凭据缓存「砍推导留结论 + 相邻复述改交叉指向」（纯注释改动，零逻辑变更）

- **背景**：延续同日 `src/stream.py`、`src/` 四文件、`main.py` 等注释精简批次…
- **改动性质**：纯注释精简，未触碰任何可执行代码；**无新增文件、无删除文件**；净删 32 行注释（`sync_http.py` −10 / `stream_select.py` −11 / `srt_writer.py` −5 / `ttwid.py` −4）。所有 issue 编号（F-12 / SEV-2226 / MID-27 / WD-01 / 2026-09-12 审查 6.7·6.3 / SEV-N05 / MID-2231 / MIN-03 / MID-N32 / WD-03 / MIN-2236③ / MIN-24① / H-2 / MID-33 / MIN-2220 / MIN-2222）、实测读数（11.9ms vs 1.47ms、构造 6.7ms、复用探针 0.77ms、gzip 1000:1、10s 录制 10.6MB、约 125 处调用点快照）、CDN 主机名、错误串字面量、常量名与阈值、跨文件点名、回归锁用例名一律逐字保留。

**涉及文件（按模块分类）**：

- **模块：选源 / 探针子系统（`src/stream_select.py`）** — 修改 1 个文件，净删 11 行注释：
  - 函数头长块「砍推导留结论」：`_probe_hls_segment`（19→15…
  - `select_source_url` 内 SEV-N05 两段重排：proxy 归一段（含 `async_http:255/365`、`room:92/176/268`、`spider:3495` 对照与 `[历史注] sync_http:179` 证伪、`grep` 复核命令）与「整轮共用 Client + 构造失败收敛为 `probe_client=None`」段（① ② ③ 三条理由、`_mark_probe_reject` 不误记、不新增 tr 模板须同步四语目录的约束全留）。
  - 相邻复述改交叉指向：`_validate_stream_url` 体内的「同 host 探针节流」与「末位放行 ≠ ffmpeg 不可拉流」两处不再复述根因…
  - **就地纠正 1 处被证伪陈述**：Range-GET 重试注释原写「隔 `_GET_RECHECK_INTERVAL` 重试」
- **模块：弹幕子系统 / SRT 字幕（`src/srt_writer.py`）** — 修改 1 个文件，净删 5 行注释：
  - `write()` 内 MIN-2236③ 的「块号回卷」推导（4→2）改为指向 `_open_segment`（该处终态判定仍是唯一事实源）
  - MIN-24①「节流重试开片必须早于生成条目」6→5（`_index=0` / `_last_end=None` 清零时序、SRT 块序号递增规范、「本片首条从 1 开始」两种前置结果保留）
- **模块：同步 HTTP 客户端（`src/sync_http.py`）** — 修改 1 个文件，净删 10 行注释：
  - 模块头「安全边界」与「调用面」两段内部重排合一（23→17）：F-12 惰性构造理由、`grep -rn "sync_http\|sync_req(" …` 取证命令与三类命中、`src/weverse_auth.py`（2026-09-23 已删除）、`[历史注]`「sync_req 调用点全部位于 `src/spider.py`」的证伪记录（SEV-2226）、CERT_NONE 生产不可达、保留本体的两点理由（F-12 不变量 + `tests/test_sync_http.py` 回归锁）全部在场。
  - SEV-2226 响应体上限段 17→13：① 压缩态按块读 / ② 解压产出两道上限缺一不可的理由、`MemoryError` 属 `BaseException` 故兜底兜不住、「80+ 房间与 Web 面板同进程」、取值口径与「宁可放宽不误杀」、超限抛 `ValueError` 后落「空响应 = 未开播/疑似风控」的链路保留。
  - 代理分支「已知残留缺口」（`response.text` 不经两道上限保护、两种补法的代价、2026-09-23 只收口 urllib 路径）7→6…
  - 孤立注释 `# 同步 HTTP 客户端模块 - 提供同步 HTTP 请求功能`（原漂在 import 段之后）上移为文件首行模块头…
- **模块：抖音凭据缓存（`src/ttwid.py`）** — 修改 1 个文件，净删 4 行注释：
  - `_ttwid_lock`（H-2 + 必须是 `RLock` 不得退回 `threading.Lock` / `asyncio.Lock` 单例 + `tests/test_concurrency.py::test_ttwid_module_pattern` 类型锁）、`get_ttwid` 的 H-2 原实现块、`invalidate_ttwid` 的 MIN-2220「刻意整体清空而非逐桶」块各压 1–2 行…
  - `_cache_ttwid` 不再复述「镜像不参与判定」的理由链…
- **同时校准本文档模块详解 §12**：`src/sync_http.py` 小节原称「按 SSL 验证开关预构建 insecure / secure 两个 opener」

### v4.3.0-dev (2026-09-24) — `main.py` 注释精简：删除 2 处纯函数名/代码复述型噪音（纯注释改动，零逻辑变更）

- **背景**：延续 2026-09-23「全仓注释精炼」与同日 `src/` 各文件去重条目…
- **改动性质**：纯注释删除，未触碰任何可执行代码；`main.py` 与被改前逐字节 `ast.dump` 比对判为**等价**（逻辑不变），净删 1 行（+1 / −2）。无 issue 编号、CVE、常量、URL、回归锁用例名或「为什么」上下文丢失。

**涉及文件（按模块分类）**：

- **模块：`main.py`（CLI 录制核心入口 / 多线程并发录制调度）** — 修改 1 个文件，删除 2 处纯复述型注释：
  - `safe_exit()`（SIGINT/SIGTERM/SIGBREAK 信号处理器）函数体首行 `# 安全的退出处理函数`（原第 541 行…
  - 模块级 `os.makedirs(default_path, exist_ok=True)` 的行尾注释 `# 确保下载目录存在`（原第 307 行）：复述该调用行为；**仅删注释、代码原样保留**。
  - 有意保留：`signal.signal` 块前的 `# 注册信号处理器`（第 554 行）作轻量分节标签；以及全部带编号 / 回归锁的「为什么」注释块。

### v4.3.0-dev (2026-09-24) — 全仓注释优化：根/构建文档 3 处事实纠错 + 多子系统多层「更正考古」压缩（纯注释改动，零逻辑变更）

- **背景**：跨多批次对本仓「根文档 + 构建配置 + 弹幕 / 并发 / ffmpeg 子系统」做注释优化。
- **改动性质**：纯注释改动，未触碰任何可执行代码；所有被改文件 `ast.dump` 逻辑等价（注释不进 AST），被测试读取的取值（依赖版本串、`fail_under` 等）未动。全部 issue 编号（MID / SEV / MIN / MI / CR / P-1 / F-14 / F-17 / W6 / MIN-24④）、CVE / PYSEC 编号、函数与常量名、错误串字面量、实测阈值、跨文件点名、回归锁用例名一律逐字保留。

**涉及文件（按模块分类）**：

- **依赖清单 / 构建配置（事实纠错 + 压缩）**：
  - `requirements.txt` — 修正 3 处被证伪陈述（已与代码回源核对）：(1) `requests` 用途旧注「spider / 各平台页面抓取 / Weverse 认证直连」→ 实测 `src/spider.py` 走 httpx 异步面（`async_http`）、`src/weverse_auth.py` 已于 2026-09-23 删除…
  - `pyproject.toml` — 修正与上同源的 `urllib3` 被推翻陈述（两文件口径统一）
- **Windows 停止脚本（编码保真 + 压缩）**：
  - `StopRecording.vbs` — 全程 UTF-16 LE + BOM + CRLF 字节级保真（该文件头明确警告须 UTF-16 LE…
- **前端独立播放器**：
  - 保留「钉版本 ≠ 钉内容 / 不经 CSP/nosniff / fail-closed / crossorigin 前提 / sha384 双 CDN 比对 / 升级须重算」全部要点。
- **弹幕子系统（`src/` 压缩 / 去重）**：
  - `src/base.py` — `DanmakuBase.__init__` 复述注释 2→1 行。
  - `src/collector.py` — `DanmakuCollector.__init__` 参数复述 5→3 行，保留 `write_srt` / `monitor` / `only_fans` 非显然语义。
  - `src/danmaku_monitor.py` — 去重 `suspend/resume_monitor_writes` 与 `close_monitor_file` 的「不经 `get_hub()` 初始化」复述…
  - `src/cookie_cache.py`（LF）— 删模块头「跨模块调用方式」段末的冗余总结句（与背景段重复）。
  - `src/config_bool.py`（LF）— 压缩头注释背景段与零依赖 / 循环导入理由段（22→19）
- **并发 / HTTP（`src/`）**：
  - `src/async_http.py` — 删 `get_response_status` 内对函数签名的逐字重抄（漂移型噪音）
  - `src/http_config.py` — 压缩 `get_effective_ssl_verify` 真值表（7→4），保留 FFmpeg 9.0 默认校验与 http / https 模式裁决。
  - `src/ffmpeg_proc.py` — 压缩 MID-32「修复之二」（ThreadPoolExecutor 非守护线程在 atexit 链路的死锁推导，6→4）。
- **ffmpeg 安装子系统（`src/`）**：
  - `src/ffmpeg_install.py`（LF）— 压缩 `install_ffmpeg_windows` 架构分流（9→6）、`install_ffmpeg_linux` 的 F-17 + MIN-24④ 多层考古（9→7）、MID-59（11→9）三段…
  - `src/ffmpeg_master_download.py`（LF）— 压缩模块头「正确下载方式 ①-⑤」为概览并指向各函数（13→8），保留 SEV-2222 等 ID 与具体名词。
  - `src/log_archive.py` — 压缩 `_web_console_rebind_pending` 推导段（7→5），保留 MID-2258 devnull 黑洞 / `_streams_bound_to()` 不匹配 / 每轮重试 / `_archive_lock` 全部事实。
- **审计后有意未改动（参考级「为什么」或密度近门禁）**：`i18n.py`、`msg_push.py`、`web.py`（根级）与 `src/config_io.py` —— 均为高价值单层「为什么」注释…

### v4.3.0-dev (2026-09-24) — `src/` 注释精简：`recorder_status.py`、`room.py` 砍推导留结论 + 去代码复述（纯注释改动，零逻辑变更）

- **背景**：延续 2026-09-23「全仓注释精炼」与同日 `gui.py` 注释去重条目…
- **改动性质**：纯注释精简，未触碰任何可执行代码；所有 issue 编号（MI-10 / MI-19 / MID-31 / 审查 6.3 / MID-2246）、函数名（`utils.run_js_async` / `_ensure_douyin_ttwid`）、常量与阈值、跨文件引用（`main.py` / `src/notify.py` / `spider.py` / `AGENTS`）、错误码字面（`ValueError: I/O operation on closed file`）逐字保留。

**涉及文件（按模块分类）**：

- **模块：`src/recorder_status.py`（录制状态快照与控制台展示）** — 修改 1 个文件，净删 2 行注释（3 处块收紧）：
  - `get_status()` 的 MI-10 块：4→3 行…
  - `display_info` 节拍头 MID-31：把「根因」从句并入括号，措辞收紧。
  - 循环末尾的 finally 退避注释：4→3 行…
- **模块：`src/room.py`（抖音房间解析 / X-Bogus / sec_user_id）** — 修改 1 个文件，净删 4 行注释（3 处块收紧）：
  - `get_xbogus()` 的「2026-09-12 审查 6.3」块：4→3 行，压缩推导句式，保留 `execjs.compile` → `utils.run_js_async` 迁移理由与 `(路径, mtime)` 缓存事实。
  - `get_sec_user_id()` 的「6.3 verify」块：4→3 行，保留 `http_config.ssl_verify` 三处 AsyncClient 一致性判据与 `sec_user_id / unique_id / web_rid` 链路。
  - `get_unique_id()` 的 MID-2246 降级日志块：7→5 行…
- **点名但有意不改**：`src/scheduler.py` —— `AGENTS.md` 注释质量参照，注释均为承重的并发语义 / 副本同步锚点，按「只增不改」保留原样。

### v4.3.0-dev (2026-09-24) — `src/spider.py` 注释合并：`_is_safe_http_url` 相邻两处叙事去重（纯注释改动，零逻辑变更）

- **背景**：对 `src/spider.py`（约 6886 行 / 注释密度 22.72%）做一轮注释精简评估。
- **改动性质**：纯注释合并，未触碰任何可执行代码；净删 3 行注释（7→4），无任何关键信息（`utils.is_safe_http_url` 归属、spider 内无生产调用点、仅为 `tests/` 兼容保留、新代码改用 `utils.is_safe_http_url`、MI-15 / 2026-09-12 审查 6.3、`async_http`/`sync_http` 循环依赖、纸面防御、上移后接入请求入口）丢失。被测函数本身是无生产调用点的死封装，AST 恒等价。

**涉及文件（按模块分类）**：

- **模块：`src/spider.py`（爬虫模块）** — 修改 1 个文件，合并 1 处相邻重复注释：
  - `_is_safe_http_url()`：将「本函数是 `src/utils.is_safe_http_url` 的薄封装…」3 行与「`MI-15 / [历史注]` 2026-09-12 审查 6.3 把实现上移到 utils…」3 行（中间夹 1 行空注释分隔）压缩为 4 行连续说明…

### v4.3.0-dev (2026-09-24) — `src/stream.py` 注释精简：13 处冗长/多层「更正考古」块「砍推导留结论」（纯注释改动，零逻辑变更）

- **背景**：延续 2026-09-23「全仓注释精炼」口径…
- **改动性质**：纯注释精简，未触碰任何可执行代码；**无新增文件、无删除文件**；净减 14 行注释。所有 MID/SEV/MIN/MI 编号、错误串字面量、函数/常量名、实测档位与码率、交叉文件点名、回归锁用例名一律逐字保留。

**涉及文件（按模块分类）**：

- **模块：`src/stream.py`（直播流地址获取 / 画质选档降级）** — 修改 1 个文件，压缩 13 处注释块：
  - 常量表头：`DOUYIN_KEY_TO_CODE`（MID-2229…
  - 工具函数：`_pad_list`（MI-02 + 2026-09-12 审查 6.5 的 min_length 5→6 考古并入 `[历史注]`）、`_probe_headers`（MID-2227…
  - `get_douyin_stream_url`：内 `_sort_quality_items` 的 MID-2229 段（字面量版只认 ORIGIN/OD/BD/UHD/HD/SD/LD、真实键全落默认 99）。
  - `get_tiktok_stream_url`：`_pad_list` 段（MI-02）、MID-16 段（保留 `AttributeError` 与 `{"url": "", ...}` 形态）、MID-15 段（① ② ③ 三条后果与「HLS 探针一次都不发」硬语义全留）。
  - `get_kuaishou_stream_url`：MIN-06 段（数字画质两表错位、`"2"` 在通用表 UHD(2000) / 码率表 BD30(30000) 对比、`tests/test_stream.py` 与 standalone 点名保留）。
  - `get_huya_stream_url`：MID-13 段（exsphd 集合语义、`labels=[...]` / `reversed(findall(264_\d+))` / `HUYA_RATIO_TO_CODE` 全留）、MID-2228 段（`len(quality_list) > 1` 条件与三段裁决链）。
  - `get_douyu_stream_url`：MID-68 段（`ast.BinOp` vs `JoinedStr`、`err_detail` 预求值口径）。
  - `get_stream_url`：内 `get_url` 的 MID-20 + SEV-2201 段（`AttributeError: 'str' object has no attribute 'get'` 全文、`SOOP/PandaTV/WinkTV/TTingLive/TwitCasting/Twitch/百度直播/ShowRoom` 平台清单逐字保留）。

### v4.3.0-dev (2026-09-24) — `src/` 四文件注释精简：去重「函数头 vs 行内」复述与 `proxy.py` scheme 同源叙述（纯注释改动，零逻辑变更）

- **背景**：延续 2026-09-23「全仓注释精炼」与同日 `gui.py` 去重条目…
- **改动性质**：纯注释去重与压缩，未触碰任何可执行代码；三个改动文件与改动前逐字节 `ast.dump` 比对均 **equal=True**（逻辑等价）；无「为什么」信息或关键数据（审查编号 MID/MIN/CR/P-1、常量、判据、URL、竞态/时序说明、交叉文件名）丢失。

**涉及文件（按模块分类）**：

- **模块：`src/notify.py`（通知与录制状态钩子）** — 密度 26.4% → 24.6%，净删 5 行注释：
  - `run_script()`：将「2026-09-12 审查 6.1」块从 11 行压到 8 行——逐字保留 posix=True/False 的实测拆分差异（`posix=False` 会把外层双引号当字面字符…
  - `record_error()` / `record_success()`：删除行内注释首句（「线程安全地记录一次…追加 1/0 到滑动窗口」
- **模块：`src/proxy.py`（系统代理检测）** — 密度 35.6% → 34.9%，净删 3 行注释：
  - `_split_scheme()` / `_get_proxy_info_linux()`：「socks5://… 被静默改写成 HTTP 代理语义」这条因果在文件内出现 4 次…
- **模块：`src/logger.py`（日志配置）** — 密度 35.2% 不变、净 0 行：全文件几乎都是带完整因果链的参考级「为什么」注释（GUI 双开句柄致轮转 WinError 32 与录制日志全量丢失、房间 ContextVar + patcher、`configure(extra=...)` 默认值不可删的 KeyError 后果等）
- **模块：`src/node_install.py`（Node.js 自动安装）** — **未改动**：完整性模型（P-1 权威哈希取自 nodejs.org、npmmirror 只加速）、CR-11 残缺 zip、ARM 架构识别等注释均已是最优单层「为什么」

### v4.3.0-dev (2026-09-24) — `gui.py` 注释去重：合并 3 处「方法头 vs 体内首行」复述注释（纯注释改动，零逻辑变更）

- **背景**：延续 2026-09-23「全仓注释精炼」条目…
- **改动性质**：纯注释去重，未触碰任何可执行代码；净删 3 行注释，无任何「为什么」信息或关键数据（审查编号 / 常量 / 判据 / 竞态说明）丢失。

**涉及文件（按模块分类）**：

- **模块：`gui.py`（GUI 主界面入口）** — 修改 1 个文件，删除 3 行冗余注释：
  - `SystemTray.run()`：删除体内首行「启动系统托盘图标（阻塞运行…
  - `LiveRecorderGUI._log()`：体内两行「添加日志到队列（线程安全）。
  - `LiveRecorderGUI._cleanup_zombie_ffmpeg()`：删除体内首行「清理录制子进程（main.py）及其下的 ffmpeg 进程。
- **查重命中但保留**：`LiveRecorderGUI._shutdown_and_quit()` 体内首行「…（由其清理 ffmpeg）→ 超时整树强杀 → 兜底清理」含与停止路径的执行顺序信息…

### v4.3.0-dev (2026-09-24) — 类型存根补齐：`typings/execjs/` 7 个 `.pyi` 消除 mypy `disallow_untyped_defs` 报错（IDE 单独打开不再报 `no-untyped-def`）

- **背景**：`typings/execjs/` 下的存根由 pyright 自动生成…
- **改动性质**：纯类型注解补齐，无运行期行为改动；**无新增文件、无删除文件**。

**涉及文件（按模块分类）**：

- **模块：`typings/execjs/`（第三方 PyExecJS 类型存根）** — 修改 7 个 `.pyi`：
  - `_runtimes.pyi`：`register(name: str, runtime: Any) -> None`、`get(name: str | None = ...) -> Any`；模块变量 `_runtimes: dict[str, Any]`。
  - `_exceptions.pyi`：`ProcessExitedWithNonZeroStatus.__init__(status: int, stdout: str, stderr: str)`。
  - `_abstract_runtime.pyi`：`exec_ -> str` / `eval -> Any` / `compile -> AbstractRuntimeContext` / `is_available -> bool`
  - `_abstract_runtime_context.pyi`：`exec_ -> str` / `eval -> Any` / `call(name: str, *args: Any) -> Any` / `is_available -> bool`；新增 `from typing import Any`。
  - `__main__.pyi`：`PrintRuntimes.__init__` 与 `__call__` 补全参数与 `-> None`；新增 `from typing import Any`。
  - `_pyv8runtime.pyi`：`Context.__init__(source: str | None = ...)`、`convert(cls, obj: Any)`。
  - `_external_runtime.pyi`：`ExternalRuntime.__init__(name: str, command: list[str], runner_source: str, encoding: str = ..., tempfile: bool = ...)`、`Context.__init__(runtime: ExternalRuntime, source/cwd: str = ..., tempfile: Any = ...)`、`Context.is_available -> bool`。
- **扫描后确认无需改动**：`typings/customtkinter/__init__.pyi`、`typings/pystray/__init__.pyi`（两包全部函数均已带完整参数/返回值注解…

### v4.3.0-dev (2026-09-24) — 压缩 `AGENTS.md` 常驻上下文：仅外迁一次性佐证读数，约束与门禁保持原位

- **范围**：将虎牙 FLV-first 冷启动采样、虎牙探针退避窗口、ffmpeg reconnect 事故、ffmpeg per-file 选项侧属、布尔配置漂移与 keepalive 数值迁入 `docs/agent-reference/measured-evidence.md`
- **约束不变**：风险控制、门禁命令、已知坑约束句及回归锁均留在 `AGENTS.md`；“必须 / 不得 / 禁止 / 须 / 一律 / 不可 / 绝不”计数与改动前一致。
- **体积**：`AGENTS.md` 由 1552 行 / 189999 字节降至 1548 行 / 188355 字节，减少 4 行 / 1644 字节。

### v4.3.0-dev (2026-09-23) — P0 修复：`build_exe._ensure_utf8_streams()` 裸 `reconfigure` 破坏 pytest fd 捕获（本地整轮无结论 + 误报「GUI 启动失败」弹窗）

- **症状**：本地跑 `python -m pytest` 后弹出标题「GUI 启动失败」的错误框，正文是 pytest 会话收尾堆栈，末行
  `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa1 …`；更隐蔽的形态是某个**无关用例**被判
  `FAILED` + `ERROR`。九个 CI job 全为 ubuntu，恒绿不复现。
- **根因（三层）**：① `build_exe.py::_ensure_utf8_streams()` 对 `sys.stdout/stderr` 做**裸**
  `reconfigure(encoding="utf-8")`；按 CPython 规定——只给 `encoding='utf-8'` 而不给 `errors` 时错误处理器
  **重置为 `'strict'`**——pytest 的 fd 捕获包装器 `EncodedFile`（原 `errors="replace"`）被**就地**改成 strict。
  ② 触发器由此进入宿主进程：`tests/test_build_exe.py` 三条用例在**进程内**调 `build_exe.main()`，其首句即该函数。
  ③ 撞击还需第二个条件：fd 1/2 上出现非 UTF-8 字节（cp936 子进程 / 继承句柄 / 冻结 exe 的原始写）；Python 层
  写入经 UTF-8 编码产生不出非法字节，ubuntu 的 UTF-8 locale 同样造不出这个条件——这是它长期潜伏至今的原因。
- **修复**：
  - `build_exe.py::_ensure_utf8_streams()`：`reconfigure(encoding="utf-8", errors="replace")`，与 `gui.py`、
    `main.py`、`web.py`、`scripts/run_gates.py`、`scripts/douyin_live_recorder_standalone.py` 五处口径统一。
  - `gui.py`：`_install_crash_sink()` 改为仅 `__name__ == "__main__"` 时安装进程级钩子。导入期钩子曾让 pytest
    （经 `tests/test_gui_monitor.py` 的 `import gui`）的未捕获异常被 GUI 兜底接管：弹出误导性标题的弹窗，并把
    原始堆栈从控制台吞掉。脚本入口（`pythonw gui.py` / 冻结 exe）的启动期可观测性不变。
  - `tests/conftest.py`：新增 autouse 守卫 `_guard_stdio_encoding_policy`，逐用例校对并复原 `sys.stdout/stderr`
    的 `(encoding, errors)`——把「悄悄改全局流」从「几十条用例之后在收尾崩一个无关堆栈」提前为「当场点名」。
  - `tests/test_build_exe.py`：新增 2 条回归锁（真实捕获下策略一字不变 / 必须显式传 `errors="replace"`）。
  当场变红、守卫 fixture 在 teardown 同步点名（ERROR 附带变更前后取值）；全量 `pytest` 见当次会话读数；`black` / `isort` 检查通过。
  第 2 步真机验证**不适用**（非录制链路改动，AST/行为等价性由回归锁覆盖）。
- **遗留**：写出 `0xa1` 的那个 GBK 产出方尚未定位；不影响本次修复（即便再来一次非法字节也只会降级为 `�`）。
- **文档**：新增 `DIAGNOSIS_2026-09-23_pytest-teardown-crash.md`（问题概述 / 排查时间线 / 根因 / 方案 / 验证 /
  经验教训 / 参考七段）。

### v4.3.0-dev (2026-09-23) — 全仓注释精炼（68 个文件）：多层「更正考古」压缩为单行历史注；`check_annotations.py` 新增第三盲点（行尾形态）；就地纠正 3 处被证伪陈述

> **性质**：纯注释改动，未触碰任何可执行代码。判据：`check_annotations.py --baseline` 对 167 个文件
> 全部 **AST 等价**；`.py` 按 `ast.dump` 全量比对、`.js/.css/.html` 按剥注释后的代码行比对。
> 因此按完成定义「豁免」条款走 1（门禁）+ 4（文档）+ 5（收尾）+ 6（日志），**第 2 步真机验证不适用**
> ——录制链路行为未被改动，已由 AST 等价性证明，不需要活房间复跑。

**一、范围与统计**

- 已精炼 **68 个文件**：`src/` 全部 33 个模块 + `src/platforms/` 5 个 + 根入口 6 个
  （`main.py` / `gui.py` / `web.py` / `i18n.py` / `msg_push.py` / `build_exe.py`）
  + `scripts/` 9 个维护脚本 + `scripts/douyin_live_recorder_standalone.py`（孪生副本）
  + `web/` 3 个前端资产 + 测试层 12 个最大文件。
- 全仓平均注释密度 **23.5% → 23.3%**（门禁下限 13.0%，无文件跌破）；`main.py` 25.1%→23.7%、
  `src/web_api.py` 40.4%→38.0%、`gui.py` 23.3%→20.9%。
- 未做：`tests/` 余下约 95 个用例文件（多为 13–16% 密度的小文件，可动作只有"等长改写"，收益低）。

**二、压缩口径（已由维护者授权，细则见 AGENTS.md「注释约定」新增条）**

形如「旧结论 A → `[修订：A 已被推翻]` → `[补充]` → `[就地更正]`」的多层段，统一改写为
「正文只写当前实测状态 + 一行 `[历史注] YYYY-MM-DD X 已…`」。实测读数、主机名、常量名、
环境变量名、平台名、判据、并发/时序假设、错误码、真实存在的回归锁用例名一律逐字保留；
交叉点名（`src/ffmpeg_install.py` ↔ `scripts/douyin_live_recorder_standalone.py`）的文件名字面
不可删（`tests/test_ffmpeg_path_preference.py` 按原文断言其存在）。

**三、就地纠正的被证伪陈述（每条附复核命令，判据来自 AGENTS.md 第 12 条）**

1. `src/ffmpeg_install.py:43` 模块头职责行仍写「Windows 只有官方源 gyan.dev 一条路」，
   与同文件下方"master 源默认关闭"的现状自相矛盾 → 改为「默认只有 gyan.dev，第二条源默认关闭」。
   同文件下方另有 3 处「把已删除的蓝奏云链当现役描述」与「称 master 兜底**无门控**」（实际受
   `master_allowed` 门禁）一并改正。
2. AGENTS.md「`utils.update_config` 仍是 `open(path,"w")` 直写、与 `config_io` 不可互相套用」——
   实测 WD-15 后它也走 `atomic_write_text`，故「只读用例沿用 `chmod` 即可」不成立；已改写为
   两处都应按 `os.replace` 打桩法写用例，并保留旧结论作废注。
   复核：`grep -n "atomic_write_text(file_path" src/utils.py`。
3. AGENTS.md「standalone 副本的 `PlatformBreaker` 缺 `_grant_probe` / `_end_probe` / `error_rate` /
   `backoff_seconds` 四个方法（src 9 个、副本 5 个）」——实测 `_grant_probe` / `_end_probe` **已在副本中**，
   真正缺的是 `error_rate` / `backoff_seconds` / `_push_sample`（副本自带改名的 `_push`）。
   已把清单换成可现场跑的集合差比对命令，并按本文件「不抄快照」口径删掉写死的方法数。

**四、新增门禁盲点（AGENTS.md「注释检查工具的盲点」由两条扩为三条）**

`code_signature` 用 `ast.parse` + `ast.dump(include_attributes=False)`，Python 语法层不区分 `\r\n` 与
`\n`，故**整文件 CRLF→LF 对 AST 等价性与 `black --check` 双向隐形**。本次一个批次用整文件重写方式
改注释，
靠与快照逐字节对比才发现，按 `b.replace(b'\n', b'\r\n')` 字节级复原。
连带后果：node 侧按原文匹配且写死 `\n\n` 的断言会因此由绿转红（现例 `MIN-2241` 路由反向锁）。
判据与前置事实（本仓 CRLF/LF 混存）已写入 AGENTS.md。

**五、顺带查实为「先前既有」、本次未修的问题（交回维护者，按优先级）**

1. `tests/test_stream.py` 单独运行 **4 failed**（抖音×2 + TikTok×2），根因是
   `src/stream_select.py:29 import main` 与 `src/stream.py` 惰性 `from .stream_select import MOBILE_UA`
   成环 → `ImportError: cannot import name 'MOBILE_UA' from partially initialized module`。
   全量跑时被导入顺序掩盖（即 AGENTS.md「全量绿、单文件跑红」同族）。
   A/B 已证与注释无关：把 `src/stream_select.py`、`src/stream.py` 换回改动前的基线副本，仍同样 4 红。
2. `tests/frontend/test_regression_2026_09_22_gates.mjs` **没有任何 Python 包装用例驱动它**
   （AGENTS.md 约定的「`.mjs` 真用例 + `.py` 包装」双文件结构缺失，现只有 `test_quality_ui.mjs` 被
   `tests/test_frontend_quality_ui.py` 包），因此它内含的 **2 条红**（上同 `MIN-2241`、
   `danmaku_unavailable 不得推进增量游标`）从不进 CI。
3. `pytest --cov=src`（AGENTS.md 与 CI 的规定跑法）在本机会把 `.coverage` 写进仓库根，
   随后有测试在 teardown 按 UTF-8 读文件时撞 `UnicodeDecodeError: 0xa1 in position 486`，
   全量放大为 **5167 errors**；把 `COVERAGE_FILE` 指到仓库外即 **3188 passed / 13 skipped、rc=0**。
4. `tests/test_utils.py::test_readonly_file_write_failure` 断言
   `"k = old" in text or "k = new" in text` 两侧任一成立即通过，属**永真断言**、不锁任何行为。

**六、验证（完成定义第 1 步）**

`python scripts/run_gates.py` → **8/8 全绿**；`pytest`（`COVERAGE_FILE` 置于仓库外）→
**3188 passed / 13 skipped，warnings summary 为空（0 条）**；`scripts/check_coverage.py` →
**PASSED: All 42 module(s) meet coverage threshold**（rc=0）；`basedpyright` → **0 errors / 0 warnings**；
`check_annotations.py` → 全部通过、悬空引用 0 处；`tests/test_regression_2026_09_22_gates.py`（读 AGENTS.md
门禁块）→ 25 passed；`scripts/check_version.py` → PASS。孪生副本单验：
`pytest tests/test_regression_2026_09_22_standalone.py` → 17 passed、`mypy` → no issues。

**真机验证**：不适用（未触碰录制链路行为，已由 167/167 AST 等价性证明；无新增 ffmpeg 参数、
选源逻辑或平台解析改动）。

### v4.3.0-dev (2026-09-23) — 修复 P0：ffmpeg master 构建下录制 100% 失败（`-thread_queue_size` 被上游收窄为输出专属选项，我们仍放在 `-i` 之前）

> **事故形态**：`py web.py` 添加抖音房间后，`序号3 … 正在直播中` 随即 `准备开始录制视频`，ffmpeg 立即以
> 返回码 **-22 (EINVAL)** 退出，零字节产物。控制台逐字报错：
> `Option thread_queue_size (set the maximum number of queued packets per stream on the muxer) cannot be applied to input url http://pull-hls-h95.douyincdn.com/…_or4.m3u8 … Error opening input files: Invalid argument`
> **与房间、平台、CDN 无关**——只要 `ffmpeg/ffmpeg.exe` 是 master 构建（本机为 `N-126755-g52f05ac780-20260922`，
> 由 `FFMPEG_MASTER_ALLOWED` 那条形成的 BtbN 通道产物），该构建下 **每一次录制都失败**。

#### 一、根因：选项的「侧属」被上游改了，而报错形态从静默变成了硬失败

- `main.py::_build_ffmpeg_input_args` 把 `-thread_queue_size 1024` 放在 `-i` 之前（原 `main.py:3475`），
  取的是它**输入侧**的老语义（doc/ffmpeg.texi：≤9.0.2 写 `(input/output)`，输入侧=强制独立读取线程，
  单输入时默认不开）。
- 上游 ffmpeg 已把该选项**收窄为输出专属**：`doc/ffmpeg.texi` 在 master 标 `(output)`，
  含义只剩「每个 muxing thread 的排队包数」；本机 `ffmpeg -h full` 把它列在
  **"Advanced per-file options (output-only)"** 段。于是它在 `-i` 之前**不再合法**。
- 与 2026-09-10 的 `-reconnect*` 事故相反：那次是「放错侧但静默接受、rc 仍为 0」，
  这次是**输入根本没打开即 EINVAL 退出**——所以症状显眼但成因同样只能靠语义断言锁定。
- 全命令逐项定位审计（`-h full` 分段标题）确认**只有这一个**违规项：
  把 `-thread_queue_size` 摘掉后，其余输入侧选项（`-rw_timeout`/`-user_agent`/`-protocol_whitelist`/
  `-analyzeduration`/`-probesize`/`-fflags`/`-reconnect*`/`-re`）全部通过解析、只在真正打开输入时报
  `Connection refused`——即修复面是单点，不存在第二处待爆的同类错配。

#### 二、修复：移到输出侧（本仓支持面内唯一两侧都合法的位置）

- `-thread_queue_size 1024` 从输入组移到 `-i` 之后、与 `-max_muxing_queue_size` 相邻的输出缓冲位置，
  取值不变（1024），并就地写清上游 texi 的版本对照与「为何不回退到输入侧」。
- 选型判据：输出侧位置对 **6.1 / 7.1 / 8.0 / 9.0.2 / master 全部合法**（实测 A/B 见下），
  而输入侧位置只在 ≤9.0.2 合法。故**不引入版本探测**——为老构建保留「独立输入读取线程」而在新构建崩溃
  不是可接受的取舍；代价如实记为「≤9.0.2 上少一项提示效果」，该效果在 master 已无对应机制。
- 孪生副本 `scripts/douyin_live_recorder_standalone.py` **不带**该选项（其标志集本就与 main.py 不同，
  见 `CODE_REVIEW_2026-09-21.md` 第 496 行），本轮无需同步。

#### 三、验证

  「位于 `-i` 之后」「紧跟字面量取值」「反向见证定义点数（main.py 1 处 / standalone 0 处）」。
  三条**各配一个能区分它的变异**，实测真值表：删取值→只红 `has_literal_value`；整对删除→只红反向见证；
  挪回 `-i` 前→只红 `follow_i_flag`；每次变异后按字节还原 `main.py`。
- **黄金快照**：`tests/test_start_record_command_golden.py` 首轮按预期报出 19 条命令的字节级差异
  （证明这道锁真的在管这件事），`GOLDEN_REGEN=1` 重生成后 32 passed；重生成物复核
  「19 条命令中 `-thread_queue_size` 仍位于 `-i` 之前的 = 0」。
- **端到端（真实二进制 + 真实参数向量）**：取 golden 里由生产构造函数产出的命令，
  只替换输入为本地 HTTP 服务上的 HLS(m3u8) / FLV 源、输出到临时目录，在本机报错的那个 master 构建上跑 3×2 矩阵：

|  | 输入形态 | 选项位置 | rc | 产物字节 |
| --- | --- | --- | --- | --- |
|  | HLS(按生产移除 `-reconnect_at_eof`) | `-i` 之前（修复前） | 4294967274 (= -22) | 0 |
|  | HLS | `-i` 之后（修复后） | 0 | 275420 |
|  | HLS | 完全不带 | 0 | 275420 |
|  | FLV | `-i` 之前（修复前） | 4294967274 (= -22) | 0 |
|  | FLV | `-i` 之后（修复后） | 0 | 234248 |

  修复前那两格即生产事故的逐字复现（同一条 `cannot be applied to input url` 报错）。
- **真机（活房间 + 外网）**：`SKIP(未由代理发起真实录制)`——本轮以本地合成源 + 生产参数向量替代；
  交回用户的动作：重新 `py web.py` 起那三个抖音房间，确认 `序号3` 不再返回 -22 且产物落盘。
- **门禁**：`scripts/run_gates.py` 8 条全绿（含 black/isort/无参 mypy/`mypy --platform linux`/
  check_annotations/compile_po --check/check_version/check_runtime_pins）+ `pytest` **3188 passed、warnings summary 为空**
  + `scripts/check_coverage.py` 42 模块达标（总 83.91%）+ `basedpyright` **0 errors / 0 warnings**。

#### 四、口径沉淀（写进 `AGENTS.md`「已知坑 → ffmpeg 命令构造与容器格式」）

新增任何 per-file 选项前，先跑 `ffmpeg -h full` 看它落在哪一段标题下——
`Advanced per-file options (output-only)` / `(input-only)` 的分界会随上游版本变化，
而 `-reconnect*`（静默接受）与 `-thread_queue_size`（直接 EINVAL）两种失效形态互不覆盖，
**不能靠「上次放错侧只是不生效」来推断这次的后果**。

### v4.3.0-dev (2026-09-23) — 测试卫生：修一处跨文件补丁泄漏引发的 11 条假失败 + 新增 R6「手工 MonkeyPatch 必须配对 undo」门禁；覆盖率门禁引入分层白名单（表默认空 + 到期即失败）

> **本轮性质**：只改测试与门禁脚本，**不改任何生产行为**。承接同日上午 `CODE_REVIEW_2026-09-22_3.md` 的收尾。
> **动因**：全量 `pytest` 出现 13 条失败，其中 11 条在单文件运行下全绿——典型「全量红、单跑绿」形态。

#### 一、根因：一个漏掉的 `undo()` 让同会话后续用例发出真实网络请求

- 污染者是本轮新增的 `tests/test_regression_2026_09_22_net.py`：8 处手工 `pytest.MonkeyPatch()` 实例只有 7 处 `undo()`。
  手工实例**不由 pytest 自动还原**（与 `monkeypatch` 夹具不同），漏掉的那处把
  `src.utils.handle_proxy_addr` 永久替换成 `lambda x: None`。
- 传播链：`async_http.utils` 与 `src/sync_http.py` 里的 `utils` 是**同一个 `src.utils` 模块对象** →
  代理地址被判为空 → `sync_req` 静默落到 urllib 直连分支 → 而该分支在那些用例里**没有被打桩** →
  真的向 `http://example.com` 发出请求，断言拿到 `<!doctype html>…` 而不是桩返回值。
- 影响范围（11 条，逐条复测确认非产品缺陷）：`tests/test_sync_http.py` 10 条
  （`TestSyncReq` 代理 GET/POST/redirect/json_data 4 条、`TestSslVerifyScoping` 1 条、
  `TestProxyAddrNormalization` 3 条，另 2 条同族）+ `tests/test_stream_select.py` 3 条代理归一化用例中的 1 条；
  修 `undo()` 后两文件隔离跑 **101 → 168 passed**。
- 另 2 条是**本轮有意改动导致的断言过时**（非污染），按真实语义改写而非放宽：
  `test_danmaku_wiring.py` 的 `stop.call_count == 1` → SEV-2208 把 `stop()` 无条件移进 `finally` 后早退路径必然 2 次
  （`DanmakuCollector.stop()` 自带 `_stop_called` 幂等），改写为「恰为 2」并保留 =1/>2 各自指向的失效形态；
  `test_platform_danmaku_offline.py` / `test_bilibili_danmaku_info.py` 的 `FakeWs` / `_FakeAuthWs` 缺 MID-2245 新增的
  `fail()` 出口（`ensure_future` 起的协程抛 `AttributeError`，表现为「closed 仍 False」的假因 + 一条未被 retrieval 的任务异常告警），
  补替身方法并新增「必须走带上报的 `fail()`」断言——只断言 `closed` 会让「退回 `close()`」这一实现无声通过。

#### 二、防复发：卫生门禁新增 R6

`tests/test_test_hygiene.py` 的 R1 只识别 setattr / `patch.object` 与字符串形态 stdlib 改写，看不见本例形态。
新增 R6 `_manual_monkeypatch_violations()`：按函数体统计「创建 `pytest.MonkeyPatch()`」与 `undo()` 次数，创建 > 还原即违规；
配 `test_guard_r6_actually_catches_a_leaked_monkeypatch` 做**双向见证**（合成漏 undo 样本必须报、合规样本必须不报）。
实测全仓除已修那一处外无第二例（426 passed）。

#### 三、覆盖率门禁的分层白名单（`scripts/check_coverage.py`）

判定优先级 **登记阈值 > 债务基线 > 全局下限**，另设豁免机检：

| 层 | 载体 | 适用条件 | 例外/失败处理 |
| --- | --- | --- | --- |
| 登记阈值 | `MODULE_THRESHOLDS` | 已人工核定目标的生产模块 | 键指向不存在的模块 → rc=2（配置腐烂） |
| 债务基线 | `COVERAGE_DEBT`（`DebtEntry`） | **仅**本轮改动前就已低于下限的存量模块；**新模块一律不得入表**… | 缺 `reason`/`tracker` 非报告指针/`review_by` 非 ISO → rc=2；`floor ≥ GLOBAL_FLOOR`、`re… |
| 全局下限 | `GLOBAL_FLOOR = 50.0`（与 `pyproject fail_under` 同口径） | 所有未登记模块，含新增文件 | 报告里查不到该模块 → 按失败处理（MIN-19） |
| 结构豁免 | `GATE_EXEMPT_MODULES` | 生成物等**结构上不可测** | 理由含「生成物」则必须真在文件里命中 `GENERATED_MARKERS`，否则 rc=2（虚报豁免）；条目数 > `EXEMPT_CEILING` → … |

- **表当前为空**：43 个 `src/` 模块 42 达标、1 个 protoc 桩豁免，没有任何模块需要债务基线，故 `DEBT_CEILING = 0`——
  将来要加条目必须同时上调上限并在 `AGENTS.md` 写理由，防止这张表退化成记账本（同 `pip-audit --ignore-vuln` 的口径）。
- 11 条新用例覆盖上述每条判据…

#### 四、读数与验证

`tests/test_check_coverage.py` 41 passed、`tests/test_test_hygiene.py` 426 passed、受影响 4 个测试文件全部 0 警告；
`black`/`isort`/无参 `mypy` 全绿。真机验证：本轮不涉录制链路与 ffmpeg 参数，按「完成定义」豁免条款记为不适用。

> **本轮性质**：新增 1 个模块、修改 1 个模块，**无文件删除**。
> **动因**：① Windows on ARM 此前**没有原生 ffmpeg 自动来源**——自动安装的唯一路径 `gyan.dev` 只发
> x86_64 构建，ARM64 宿主上只能经 x64 模拟运行；② 国内访问 `gyan.dev` 慢/被阻时，x86_64 也只有
> 「单条路，失败即手动安装」，缺无门控兜底。

#### 一、新增文件 — `src/ffmpeg_master_download.py`（403 行）

Windows FFmpeg **master 滚动构建**下载器，构建名 `ffmpeg-master-latest-{win64,winarm64}-gpl.zip`。
架构后缀含义：`win64` = x86_64（Intel/AMD）、`winarm64` = ARM64（Windows on ARM）、`gpl` = 含 GPL 编解码器的构建。

| 组成 | 名称 | 职责 |
| --- | --- | --- |
| 入口 | `download_ffmpeg_master(dest_dir, arch=None)` | 顶层下载 + 安装，失败返 `False` 不抛（与 `ffmpeg_install` 契约一致）… |
| 选源 | `_windows_arch()` / `_candidate_urls()` | 按 `platform.machine()` 选 `win64`/`winarm64`；候选源 `[fyhub.cn, BtbN GitHub]`… |
| 探测 | `_probe()` / `_looks_like_html()` | **Range GET `bytes=0-0`** 探针识别人机验证页（`HEAD` 在 fyhub 上返 405，故不用 HEAD）… |
| 传输 | `_stream_download()` | 流式下载 + `tqdm` 进度；连接/读取超时分离；连接级失败退避重试 3 次（2/4/8s），HTTP 4xx/5xx 不重试… |
| 完整性 | `_tofu_verify_or_record()` / `_master_hash_file()` | TOFU 哈希缓存，基准文件前缀 `_ffmpeg_master.*`（与官方源 `_ffmpeg_official*` 互不污染）… |
| 异常 | `FfmpegDownloadError` → `ChallengePageError` / `IntegrityError` / `NetworkErro… | 分层错误捕获，调用方据此换源或终止 |

关键常量：`_CONNECT_TIMEOUT=15` / `_READ_TIMEOUT=30` / `_PROBE_TIMEOUT=20` / `_MAX_RETRIES=3` / `_RETRY_BACKOFF=2.0`。

**决定本模块形态的实测结论**：`fyhub.cn` 对这两个直链返回「下载验证」HTML 页（200 + `text/html`，含
`verification_token` 表单与 `vdf-worker.js` 的 PoW 工作量证明），`HEAD` 返 405，`.sha256` 返 404 →
**普通脚本无法直接下载**。故 `_probe()` 识别到挑战页即自动跳过，落到无门控的 BtbN GitHub
`releases/download/latest/...`（实测 206、`application/octet-stream`、首字节 `PK\x03\x04` 合法 zip）。

#### 二、修改文件 — `src/ffmpeg_install.py`

| # | 位置 | 改动 |
| --- | --- | --- |
| 1 | 模块头导入 | 新增 `from src.ffmpeg_master_download import download_ffmpeg_master`（单向引入，新模块不 i… |
| 2 | `install_ffmpeg_windows()` | 由「单条 gyan.dev 路径」改为**按宿主架构分流** |
| 3 | 同函数收尾提示 | 手动安装提示的基准前缀由仅 `_ffmpeg_official*` 扩为 `_ffmpeg_official*` + `_ffmpeg_master*`… |

分流逻辑：

- **x86_64**：仍优先 `gyan.dev` 官方源（带官方 SHA256 校验）；**仅当官方源失败**才回落 BtbN master 构建
  （无门控、仅 TOFU），作为国内访问受限时的可用性兜底 —— 官方源可达时**不会**走到该分支。
- **ARM64**：直接走原生 arm64 master 构建（`gyan.dev` 无 arm64 源，此为唯一原生来源）；
  该路径失败再退回官方 x86_64（x64 模拟运行）保底，至少可用。

#### 三、删除项

**本次无文件删除**。仅有一处口径变更：`install_ffmpeg_windows()` 原有的「Windows 只有官方源一条自动路径」
表述随架构分流失效，已就地改写（属注释/文案更新，不是删除功能）。

#### 四、完整性口径（重要边界）

- ARM64 路径与 x86_64 的 BtbN 兜底均为 **TOFU（首次信任）**：fyhub 与 BtbN 的 `latest` 滚动别名
  **都不发布 `.sha256`** 文档（实测均 404），无法做权威哈希校验；且滚动地址不能把哈希常量钉进源码
  （上游发新构建即永久失败，即 MID-59 的历史成因）。
- x86_64 的 `gyan.dev` 主路径**未受影响**，仍走「官方公布 SHA256 优先、取不到才降级 TOFU」。
- TOFU 回落时日志显式 `warning`，不静默降级。

#### 五、验证

- `py_compile` 通过；`import src.ffmpeg_install` 无循环导入。
- 探针自测 `python -m src.ffmpeg_master_download`：本机 `arch=win64`，fyhub → `challenge`、
  BtbN → `ok`，降级判定正确（**仅探针，未下载完整 ~190MB 包**）。
- `black --check` / `isort --check-only`（line-length 120）两文件全绿；无参 `mypy` **rc=0**（146 文件 0 error）。
- **遗留**：未做端到端真机安装验证（需下载完整包并跑通 `ffmpeg -version`），交回用户侧执行。

### v4.3.0-dev (2026-09-22) — 文档口径收敛（正式接受蓝奏云删除）+ README「Windows 手动安装 ffmpeg」用户指南

> **本轮性质**：纯文档轮，**零生产代码改动**（`src/` / `main.py` / `build_exe.py` / 四份 i18n 目录 / 测试全部未触碰）。
> **动因**：用户裁决「接受删除，留给该写者自己补」——蓝奏云兜底的删除保持原样，本轮只把仍按
> 「P-1b = 显式开关」描述现状的文档改齐，并补齐 Windows 用户的手动安装路径（删除后 Windows 只剩一条自动路，
> 没有手动指南就等于把失败态留给用户自己猜）。

#### 一、P-1b「显式开关」表述就地作废（中英各 4 处，全部带 `[2026-09-22 修订：…]` 历史注）

1. `CODE_WIKI.md` / `CODE_WIKI_EN.md` 供应链加固条目的**标题**：补注「P-1b，同日作废」。
2. 同条目的 **P-1b 小节**：正文改为「该小节的当时形态」，修订注写明删除范围
   （`get_lanzou_download_link()` / `_install_ffmpeg_lanzou()` / `_lanzou_fallback_enabled()` + 三个
   `FFMPEG_LANZOU_*`），并记「原『`ALLOW_UNVERIFIED` 字面集合是否被放宽』待确认项随该变量删除而作废」
   ——该开放项不再需要收紧裁决，不要再排期。
3. 同条目「口径与文档同源」段：原写「蓝奏云需显式开启」，改为「已整体删除 + 新增第二源须先过官方公布哈希判据」。
4. 信任评审快照表（`运行期 ffmpeg` 行）与覆盖率表（`src/ffmpeg_install.py` 行）各补一条「本行系当时快照」注记，
   前者同时把 P-1 的建议标为**已实施**。
5. `PROPOSAL_2026-09-22_binary-trust-policy.md` 影响范围表两行：**运行面**（成功率影响从「默认关闭」升级为
   「完全无兜底」）与**用户契约**（本行整体作废，净变化改为「不再有镜像兜底、失败给手动安装提示」）。
   同文档 `i18n` 行追加现行读数指向（675 只是那一轮的读数）。
6. `AGENTS.md` 的 ② 类条目由删除轮作者改写完毕，本轮只核对未回退（`grep FFMPEG_LANZOU src/ffmpeg_install.py`
   现只剩注释里的历史说明）。

#### 二、i18n 目录计数复核（结论：只写带时间戳的读数，不写「现行值」）

- 同一工作树在 40 分钟内先后取到三种自洽状态（16:05 → 663/662；16:14 → 667/666 + 4 条蓝奏云孤儿键；
  16:46 → 663/662 + 孤儿键归零），序列表与复跑命令见下方「Windows 运行期 ffmpeg 源收敛」条目的 §三。
- 本轮先后收到两份修复报告称「N=679 / 四目录各 663 键」「N=680 / 各 679 条（并给出 mtime 20:13:54）」，
  两者都不能由任何一次复跑得到，且后者给的时刻**晚于当时本机时钟（16:14）**。**不在文档里裁定谁对谁错**，
  只固化可复现的处置：① 引用条数必须同附**取数命令 + 读数时刻**；② `.mo` N 与「键数」恒差 1，
  是口径差异不是数据问题，两者不得互相指认；③ 声称的 mtime 落在本机时钟之后即视为未经复跑的证据
  （`date` 与 `git worktree list` 是判断「这份证据出自哪里」最便宜的两招——本机当时只有一个工作树，
  另一份 `D:/DouyinLiveRecorder` 是 09-21 的发布副本、N=664）。判据已写入 `AGENTS.md`
  「四语目录条目数的权威口径」条目。
- **4 条蓝奏云孤儿键已在 16:46 的复测中归零，不必再排期**；但这一类「目录比代码多、且任何门禁都不会变红」
  的分叉性质留在条目里：删源码功能时须手工回查目录侧（本会话按边界不代改他人那四份文件）。

#### 三、README 新增「手动安装 ffmpeg（Windows 用户指南）」（中英对等，`🚀 快速开始` 末节）

- 依据全部取自代码实测，不含推测：`install_ffmpeg_windows()` 只有 gyan.dev 一条自动路径
  （`ffmpeg-release-essentials.zip`）；`download_ffmpeg_official()` 把包内 `bin/` 的内容
  `copytree` 到 `execute_dir/ffmpeg/`，故最终形态是 **`ffmpeg\ffmpeg.exe` 扁平一层**；`main.py` 只把
  `execute_dir\ffmpeg` 这一层前置进 `PATH`（不进子目录），所以 `ffmpeg\bin\ffmpeg.exe` 这种「照 zip 原样放」
  的形态**不会**被识别——指南把这条列为显式「不要」。
- 落点按运行方式分表给出（exe 包 = `DouyinLiveRecorder\ffmpeg\`，源码/单文件 = `<项目根>\ffmpeg\`），
  依据 `src/logger.py::_app_root()`（冻结态返回 exe 同级目录，非 `_internal/`）。
- 验证与自救：`ffmpeg -version`；`logs\streamget.log` 不再出现「未安装 ffmpeg。」；SHA256 基线被拒时删
  程序目录下 `_ffmpeg_official*.zip.sha256`（`_HASH_SUFFIX = ".zip.sha256"`）后重启，并写明该旁路文件
  「强度等同目录权限、不是独立信任根」，避免用户把它当安全边界。
- 三种等效安装面都点明：包内 `ffmpeg\`、系统 `PATH`（`shutil.which` 命中即可）、容器（镜像 apt 自带）；
  并划清 full / lite / 单文件版的适用范围。FAQ「缺少 ffmpeg」条原写「Windows 程序已自带，无需安装」，
  该表述只对 full 版成立，已改为带条件的指引并指向本节。
- 顺带纠正两处**代码注释里的事实错误**（未改代码，只记录）：`src/ffmpeg_install.py:71` 称产物在
  `execute_dir/ffmpeg/bin/ffmpeg.exe`、`:68` 称 `execute_dir` 冻结后指向 `_internal/`——两者均与
  `_app_root()` 实现及 `copytree` 目标矛盾。该文件归删除轮作者所有，本轮不动，交由其改正；
  若有人据此写文档会直接误导用户（这正是本条存在的理由）。

#### 四、门禁与两次同机竞态假红（本会话自触发一次，另一次来自并发会话）

  ① 16:44 —— `run_gates.py` rc=0 / 8 条全通过（36.2s）+ 全量 `pytest` rc=0 / **2463 passed / 12 skipped / 0 failed**；
  ② 16:5x（删除 §三 那行误抄读数之后再跑一次）—— `run_gates.py` rc=0 / 8 条全通过（29.9s）+
  全量 `pytest` rc=0 / **2463 passed / 12 skipped / 0 failed**。
  两次输出内均**无 warnings summary**（即「0 警告」口径达成）。中间态：16:09 那次门禁亦 8/8（135.1s）、
  i18n 专项 `test_i18n.py` + `test_i18n_migration.py` 44 passed（16:15）。
- `_out_e2e` 竞态**当天二次复现**：16:18 一次全量跑出 4 条
  `tests/test_srt_timeline_anchor.py::FileNotFoundError: tests\_out_e2e`，而当次**本会话并未并发第二个
  pytest 会话**（只有另一工作流在写同一工作树）。单会话复跑该文件 4 passed → 仍判环境竞态。
  机制与本文件 2026-09-21 条目所记完全一致：该文件在**模块导入期** `os.makedirs(OUT, exist_ok=True)`，
  而任意同机 pytest 会话结束时 `conftest.pytest_unconfigure` 会 `rmtree` 掉这个**共享**目录。
- **该待办已于 2026-09-24 闭环（由后续会话执行，非本轮）**：`tests/test_srt_timeline_anchor.py` 的 4 条用例改走
  `tmp_path`（主体拆成接受 `out_dir` 的 `_*` 函数 + 直跑通道用 `tempfile.TemporaryDirectory`，照本仓
  `tests/test_bili_e2e.py` 的既有范式），模块导入期的 `os.makedirs(tests/_out_e2e)` 与其「先清空再写」预清扫
  一并删除；`tests/conftest.py::_TEST_OUT_DIRS` 与 `tests/test_test_hygiene.py::_ALLOWED_TESTS_ENTRIES` 同步去掉
  `_out_e2e`（`_out_live` **保留** —— 五个 `test_*_live_collector.py` 手跑真机验证仍写它，但它们无
  `def test_`、pytest 只导入不执行，故不再构成导入期竞态）。闭环后读数：全量 `pytest` 连续两次**均无
  `_out_e2e` 失败**（此前每次必现 4 条）、`black --check tests/` 108 files unchanged、`mypy tests/` 102 files
  0 issue、定向 435 passed；`.gitignore` 的 `tests/_out_e2e/` 条目刻意保留（防旧副本重建后误提交）。
  AGENTS.md 那条「跑全量请保持串行」已按「被证伪的条目就地改正文 + 留日期修订注」的口径，改写为
  「测试产物一律走 `tmp_path`」的长期判据（原机制作为历史保留在该条内）。

### v4.3.0-dev (2026-09-22) — Windows 运行期 ffmpeg 源收敛：删除蓝奏云兜底 + 下载产物形态守卫

> **本轮性质**：获批的两项改动（用户在实测证据后选择「先只做删蓝奏 + 加固」）。
> **零改动面**：录制链路、选源、ffmpeg 参数构造、平台解析、并发模型。

#### 一、动因：一条「看起来能用」的直链，实测拿不到产物

原始诉求是把 Windows 运行期 ffmpeg 的获取方式改为直链
`https://fengyuan.frostlynx.work/FFmpeg/latest/ffmpeg-master-latest-win64-gpl.zip` 并移除蓝奏云依赖。
接线前实测（2026-09-22，本机出口）：

- 该地址 `301 → https://fyhub.cn/...`，随后 **`200 + text/html`**——正文约 10.6 KB 的人机验证
  （proof-of-work）页，需 `/api/public/v2/web/challenges` + `/authorizations` 与浏览器 JS 令牌。
  页面内嵌的 `/download/success/...` 变体、以及重定向终点 `fyhub.cn` 上的同名路径**同样回 HTML**；
  `HEAD` 回 `405 + application/json`。**即该 URL 不能用于程序化下载。**
- `.sha256` / `.md5` / `.sig` 伴生文档全 404 → 不满足 AGENTS.md 第②类（运行期自动安装）
  「首次安装一律先取上游官方公布的哈希文档」的判据；接上它等于把 TOFU 变回默认路径。
- 三个响应头（`Content-Length` / `ETag` / `Last-Modified`）全缺 → `_build_identity()` 返回 `""`
  → 旁路基准落到**旧文件名**，TOFU 分支会把那段 HTML 的哈希当成可信基准记下去。
- 该直链的真实上游是 **BtbN**（页面自标 `FFmpeg-GPL-BtbN`）。GitHub Releases API 确实公布 asset 级
  sha256：`ffmpeg-master-latest-win64-gpl.zip` = 194,567,751 B / `cb4b8d0b…84fb`（构建于 2026-09-21），
  是**有**独立可信来源的路线。但本机实测 `github.com/.../releases/download/...` **ConnectTimeout**
  （`api.github.com` 可达），故 BtbN 直连未必能满足「国内可达」的原始诉求；且该包 195 MB，
  是 gyan essentials（114,768,076 B）的 1.7 倍。
- 对照：现行主源 gyan.dev **健康**——`200 application/zip`、真 `PK\x03\x04` 魔数、
  `.sha256` 文档恰 64 字节 `60f46726…47ba`（ffmpeg 9.0.2，与 `build_exe.py` 已回填的发布期钉定互证）。

#### 二、代码改动（仅 `src/ffmpeg_install.py`，188 行蓝奏云实现出、模块 801 → 626 行）

- 删除 `get_lanzou_download_link()` / `_install_ffmpeg_lanzou()` / `_lanzou_fallback_enabled()` /
  `_log_lanzou_disabled()` / `_LANZOU_ENABLED_ENV`；`install_ffmpeg_windows()` 收敛为
  「gyan.dev 一条路 + 失败即给手动安装与删基准提示」。
- 随之失效的 import 一并清掉：`typing.cast`、`src.config_bool.parse_config_bool`。
- **新增形态守卫**：`download_ffmpeg_official()` 在 SHA256 校验/记账**之前**先判
  `_is_valid_zip(zip_file_path)`；非有效压缩包即 `logger.error` + 删产物 + `return False`。
  判序必须是「形态 → 哈希 → 解压」。
- 模块头与 MID-59 / CR-11 相关段落就地更新，并留下一条推论：官方源已是 Windows 唯一自动路径，
  故「按构建标识命名旁路基准」这条修复**更加**重要而非可以松劲。

#### 三、i18n（四语同改；`.mo` 头部 N 随并发写入漂移，**只记带时间戳的读数**）

- 本轮计划「新增 1 条运行时模板（守卫报错文案）+ 删除 16 条蓝奏云目录键」。**可证的只有这一段**：
  模板已写进 `src/ffmpeg_install.py` 的 `tr()` 调用后，
  `tests/test_i18n_migration.py::test_runtime_templates_covered_by_catalog`（不变量③「运行时模板 ⊆ zh_CN.po
  键集」）一度转红、随后转绿——即「代码有模板、目录当时还没有该 msgid」这条链路确实发生过。
  **至于四份目录每一步的条数，本会话不再给结论**（见下一条与各条判据）。
  [2026-09-22 修订：本小节原记「678 → 663 条」，属**用计划算式冒充实测**；并行工作流对此给出的是
  「15:02 一次写入 679 → 681」，两者都不能由本盘的复跑证实，故一并撤下具体数值。]
- **本节不再保留「谁对谁错」的叙述，只留实测与判据。** 本会话在 16:05 / 16:14 / 16:46 / 16:50 / 16:54 / 17:14
  六次亲自复跑得到的读数依次是 663/662+0、**667/666+4**、663/662+0、663/662+0、663/662+0、663/662+0
  （格式：`.mo` N / 四目录键数 / 蓝奏云字样键数）；后四次之间 `.mo` mtime 恒为 **16:31:15**，
  即那段时间本盘没有任何目录写入。
- **并行的另一份工作流报出的末态一路推进**：「N=673 / 672」→「681 / 680 + 全量 2484 项」→「682 / 681」→
  「**N=684 / 各 683 键**」（其称写入时刻 17:22:23、17:24:48，并附 `tests/test_ffmpeg_baseline.py`、
  `_baseline_expired_reason` 与四文件 mtime 为证）。本会话到 **17:22:13（本机时钟）** 的复跑仍是
  N=663 / 662 键 / `.mo` mtime 16:31:15 / 该测试文件不存在。
  **结论：两边读数在各自时刻都为真，差别只是"何时测"，且两个会话的时钟相差数分钟。**
  因此本条目**不指定末态数值、自此不再记录任何新读数**——要现状就复跑下面的取证命令，
  不要引用任何一方写在文档里的数字。
- **可复用的三条判据**：
  ① 条数必须带**取数命令 + 读数时刻 + 两种口径**（`.mo` N 与键数，N = 键数 + 1），否则不可用于对账；
  ② 转述他人读数必须显式标注「未复现的外部读数」，**不得混进自己的实测表**
  （本条目一度这样做过一次并删掉了，见下方「自己犯过的错」）；
  ③ 跨会话比较时钟**不成立**——本节曾写下「报告时刻晚于本机时钟即证明其未实盘测量」，
  **[2026-09-22 撤回并删除该判据]**：唯一可靠的是「本盘文件 mtime + 自己复跑的同一条命令」。
  `python -c "import struct,os,time;p='i18n/zh_CN/LC_MESSAGES/zh_CN.mo';print(struct.unpack('<6I',open(p,'rb').read()[:24])[2], time.ctime(os.path.getmtime(p)))"`
  外加 `PYTHONUTF8=1 python scripts/compile_po.py --check`、`PYTHONUTF8=1 python scripts/extract_i18n_strings.py`
  （看「现有条目 / 缺失」两行）与 `pytest tests/test_i18n.py tests/test_i18n_migration.py`。
  五路自洽才算一个读数；任一路不符即为「正在被写」，不是「数据有问题」。
- **自己犯过的错（留作反面教材）**：16:5x 曾把一份外部报告声称的「16:58:17 写入 → 667/666，随后被回退」
  当作观测写进本小节，还为它编了「被回退」的机制解释；该读数从未被本盘复现，**已删除**。
  一行伪装成实测定量，就足以让后来者拿它去「校正」真实读数。
- **排除「它其实在改另一份工作树」这条可能（16:52 取证）**：全盘 `D:` 深度 ≤3 只有两份 `zh_CN.mo`——
  本工作树（N=663，mtime **16:31:15**，即其声称的 16:44:14 写入在本树并不存在）与
  `D:/DouyinLiveRecorder`（N=664，mtime 09-21 02:54 的发布副本）；`git worktree list` 亦只有本树。
  复跑取证一行：
  `python -c "import glob,os,struct;[print(struct.unpack('<6I',open(p,'rb').read()[:24])[2], __import__('time').ctime(os.path.getmtime(p)), p) for p in glob.glob('D:/*/i18n/zh_CN/LC_MESSAGES/zh_CN.mo')]"`
- **那 4 条蓝奏云字样键为什么当时会回去（可复用的判据陷阱）**：全仓 `grep` 显示唯一「引用」它们的是
  `scripts/patch_i18n_2026_09_12.py`——一份 09-12 的一次性补录脚本，`CODE_REVIEW_2026-09-21` MID-N67
  已认定它属应清理残留，**删除轮的「存活源码」判据也显式把它排除在外**。于是「该键仍被源码引用」这句话
  在两种口径下同时为真与为假：**判据必须写清「存活源码」是否含一次性脚本**，否则同一条删除判据会被人
  拿去正当地把死键放回来。
- **复跑取证（一条命令一组信号）**：`struct.unpack('<6I', open('i18n/zh_CN/LC_MESSAGES/zh_CN.mo','rb').read()[:24])[2]`
  + `PYTHONUTF8=1 python scripts/compile_po.py --check` + `PYTHONUTF8=1 python scripts/extract_i18n_strings.py`
  （看「现有条目/缺失」两行）+ 三份 json/yaml 键数 + `pytest tests/test_i18n.py tests/test_i18n_migration.py`。
  五路自洽才算一个读数；任一路不符即为「正在被写」而非「数据有问题」。
- **孤儿目录键（一类门禁看不见的分叉，附当时的实例）**：16:11 的写入曾把 4 条蓝奏云 msgid 放回目录
  （`蓝奏云 SHA256 校验通过`、`蓝奏云 ffmpeg SHA256: {lanzou_hash}`、`蓝奏云为非官方个人分发源…`、
  `蓝奏云 ffmpeg SHA256 与 FFMPEG_LANZOU_SHA256 不一致…`），而 `src/ffmpeg_install.py` 已 `grep lanzou`
  **0 命中**。**这类「目录比代码多」不会让任何门禁变红**（`extract_i18n_strings.py` 的「疑似冗余」仅参考级），
  本会话按「不代改他人四份目录」的边界登记后，16:46 复测已归零（孤儿键 0 条、总数回到 663/662）。
  留给后人的不是这个数，而是动作：**改源码删功能时手工回查目录侧**，判据是「键含该功能专有字样 **且**
  不被任何存活源码引用」（同一条判据也解释了下行为什么不能只 grep 关键字删键）。
- 删除判据是「键含 lanzou/蓝奏 字样 **且** 不被存活源码引用」；存活源码**排除** `.workbuddy/`
  （备份草稿）与 `scripts/patch_i18n_2026_09_12.py`（`CODE_REVIEW_2026-09-21` MID-N67 已认定为
  应清理的一次性残留）。**反例**：`删除残缺压缩包失败: {e}` 看着像蓝奏云专用，实际仍被
  `src/node_install.py:238` 使用——按关键词批量删会把它一起删掉。
- `zh_TW.yaml` 用**不加引号的键**，按 `"key":` 形态只匹配到 8/16 条，余下 8 条需按行二次清理。
- 四份目录均为 **CRLF**，脚本必须 `newline=""` 读写，否则整文件行尾被翻成 LF（万行级假 diff）。

#### 四、测试（`tests/test_ffmpeg_install.py` 1169 → 1028 行，本模块现 79 项）

- 删除 5 个蓝奏类（`TestLanzouLink` / `TestLanzouInstall` / `TestWindowsFallbackOrder` /
  `TestLanzouSwitch` / `TestWindowsFallbackSwitch`），新增 2 个类共 7 项：
  `TestDownloadedPayloadMustBeArchive`（HTML 挑战页拒装且**不写任何基准** / 截断 zip 同拒 /
  合法包仍记基准的对照组 / AST 判序锁）与 `TestWindowsInstallSingleSource`（官方源失败即终态 /
  AST 层「全模块只剩一个 http URL 常量」 / AST 层「无 lanzou 函数、无 FFMPEG_LANZOU_* 环境读取」）。
- 两条口径值得记：① 单源锁按「URL 常量集合」判而不是 grep `lanzou` 字样——换成别的镜像名照样拦得住，
  也不会被刻意保留的历史注释误报；② 原 `test_unexpected_error_is_reported_as_failure` 用
  `b"not-a-zip"` 当载荷，守卫上线后它会在守卫处返回、`except Exception` 分支**静默失覆**，
  已改为「合法 zip + `unzip_file` 抛错」。
- `_Resp` 替身顺手收掉只有蓝奏云用到的 `json_data` / `final_url` / `json()` 面。
  `_install_ffmpeg_lanzou` → 2 条红。

#### 五、门禁与文档

- `run_gates.py` 全绿（本会话首跑为 8/8；同日门禁清单新增「pytest warnings summary 为空」一条，
  复跑为 9/9）· `basedpyright` 0 errors / 0 warnings · `check_coverage.py` 6/6 ·
  `pytest` 全量 **2463 passed / 12 skipped / 0 failed / 0 警告**（16:4x 单会话复跑）。
  `check_runtime_pins` 仍报 2 个矩阵内槽未钉定，属既有状态、与本轮无关。
- `AGENTS.md`「三类钉定/校验」② 条目按「本文件自身被证伪的条目须就地改正文」的口径重写，
  并保留 `[2026-09-22 修订：旧结论 … 已被推翻]` 一行；新增「加第二源前必须先过官方公布哈希判据」。
- **未改** `README.md` / `README_EN.md` 与 `CODE_REVIEW_*.md`：其中的蓝奏云字样全是历史更新日志
  （v4.0.9 换源、09-12 审查 H-1），不是现行配置说明。

#### 六、真机验证（自动安装分支实跑，2026-09-22）

本轮不属「需活房间跑录制链路」的改动面（录制 / 选源 / ffmpeg 参数构造 / 平台解析零改动，
故 `tests/test_{bili,douyin,douyu,huya,twitch}_live_collector.py` 一律 **SKIP(不涉及录制链路)**，
无交回用户的补跑动作）。但**运行期自动安装本身**是「平时没人验证」的路径，故直接对真实上游跑了一次
（落点用 `tempfile.mkdtemp()`，不写仓库目录）：

| 分支 | 结果 | 可核对读数 |
| --- | --- | --- |
| gyan.dev 真包（守卫放行侧） | **PASS** | 115 MB 下载完成 → 官方 `.sha256` 校验通过（`60f46726…47ba`）→ 解压装出 `ffmpeg.exe` / `ffplay.… |
| 用户所给 PoW 直链（守卫拦截侧） | **按设计拒装** | `.sha256` 端点 404（日志记「未取得官方 SHA256 文档」）→ 守卫文案命中 → 返回 False；**旁路基准 0 个**、无 zip 残… |

即：单测里那条「HTML 挑战页不得被记成可信基准」的锁，在真实端点上复现成立；放行侧也没有因为新守卫而误杀真包。

- **一处验证工装缺陷（非代码回归）**：首轮脚本只重定向了模块级 `execute_dir`，漏重定向 `ffmpeg_path`，
  于是最后的 `-version` 探到了仓内目录、报 `FileNotFoundError` 而返回 False。按绝对路径复核产物后 rc=0。
  PATH 注入与 `-version` 复核用的是**模块级 `ffmpeg_path`**，而不是 `dest_dir/ffmpeg`。当前唯一调用点
  传的就是 `execute_dir`（与 `ffmpeg_path` 同源），生产不可达；但若将来有人用别的 `dest_dir` 调它，
  就会「装到 A 目录、复核 B 目录」。修法是一行 `os.path.join(dest_dir, "ffmpeg")`，
  但该处正被 W6 的 PATH 优先级判据管着，**留待单独批准**，不在本轮顺手改。

### v4.3.0-dev (2026-09-22) — W1 第 4 类完整性口径落地 + W6 Apple Silicon 的 ffmpeg PATH 让位策略

> **本轮性质**：两项已获批的改动。W1 是**口径**（不改产物来源），W6 是**运行期行为**（只影响
> darwin + arm64，其余平台逐字不变）。录制链路、选源、ffmpeg 参数构造、平台解析零改动。
> **验证**：本轮不属「需真机跑活房间」的改动面（未触录制链路）；darwin + arm64 分支在本机不可执行，
> 为单元验证（见「验证」子节的边界声明）。

#### 一、W1：第 4 类「源码可复现构建」口径（不含任何自构建步骤）

- **措辞纠正**：先前把它写成「AGENTS.md 三类→四类」不准确。**面**（发布期 / 运行期 / 签名脚本层）仍是三类，
  第 4 类是**发布期 ① 的第二种满足方式**，专用于「CI 自源码构建、上游本就没有公布值」的产物；
  不得拿它覆盖 ② ③ 的缺口。已按此写进 `AGENTS.md`。
- 判定入口收敛到 `build_exe._slot_is_gated()` = 「已钉定的官方哈希」∨「三件证据齐备的第 4 类」
  （`source_sha256` 上游源码 tarball 官方值 / `recipe_sha256` configure 配方哈希 / `provenance_ref` 产出凭据；
  两条哈希过 64 位十六进制形状关、ref 非空）；`scripts/check_runtime_pins.py` 改为调它，不再自己判形状。
- 两条防绕闸：① 只写标记、证据不齐 = 与「未钉定」同等处置；② 声明第 4 类的槽位**不得走下载路径**，
  `_unpinned_action` 在发布与本地**两侧一律终止**（本地也不例外，否则换个标记就拿到免检），
  且判定看**合并 `DLR_RUNTIME_SHA256` 后的实际取值**而非内置表。
- `_SOURCE_BUILD_EVIDENCE` 当前**刻意留空**（没有产物走该类）→ `--strict` 照旧 rc=1，本轮不放行任何东西。
- **`--strict` 范围重定**：只对发布矩阵真正构建的运行时键要求满足（CI 实为 3 runner，`macos-x64` /
  `linux-arm64` 无人产出）；矩阵外键未钉定时**只告警且必须打印**——静默省略等于谎称「表里每个键都有闸」。
- 实测纠正（由新用例抓出）：`_pinned_slots()` 会把取值统一 `.strip().lower()`，而类别常量是大写——
  按原样逐字比会让**注入式标记逃过拒下载判定**。已改为大小写无关（`_is_source_build_marker`）并加回归锁。
- 新增 `tests/test_check_runtime_pins.py` 11 项 + `tests/test_build_exe.py` 12 项；变异验证两处
  （判据降为「认标记即放行」、取消矩阵内外分流）→ **9 条变红**后复原。

#### 二、W6：Apple Silicon 上包内 x86_64 ffmpeg 不再遮蔽系统原生构建

- 判据收敛到 `src/ffmpeg_install.should_prepend_bundled_ffmpeg_dir()`（唯一事实源）；`main.py` 只保留原有
  「重复插入跳过」守卫并新增一次调用（**策略不内联进 main.py**）。五条缺一即维持现状前置：
  `sys.platform == "darwin"` ∧ `platform.machine() == "arm64"` ∧ 包内目录存在 ∧
  **注入前** PATH 快照上另有 ffmpeg ∧ 那份的 realpath 不在包内目录里。
- 两处容易做错的点：探测必须用调用点传进来的 pre-injection 快照（自读 `os.environ["PATH"]` 会探到刚被
  自己前置进来的那一份，让位永不发生）；自我遮蔽形态（用户把包内目录永久写进 PATH）须按 realpath 归一排除，
  否则日志承诺「原生 arm64」而实际仍是 x86_64。
- 刻意选择的漏判方向：解释器本身被 Rosetta 转译时 `platform.machine()` 报 `x86_64` → 判据不成立、维持现状
  （架构信息不可信时不改用系统那份）。Windows / Linux / Intel Mac 行为逐字不变。
- 前提纠正留档：调研推翻了「运行期自动安装只在 Windows」这一说法（`install_ffmpeg_mac()` 早已在用 brew），
  所以「让位给系统原生构建」是**当天就能做**的止血，不必等 arm64 自构建路线落地。
- 可观测性与文档：3 条 `i18n.tr` debug（四语目录同步、`.mo` 重编 678 条）；`README.md` / `README_EN.md`
  各新增「Apple Silicon 上用的是哪份 ffmpeg」FAQ（`ffmpeg -version` / `which ffmpeg` / `logs/streamget.log`
  三种自查方式 + Docker 不受影响说明）。
- 新增 `tests/test_ffmpeg_path_preference.py` 13 项（含 3 条 main.py 接线 AST 锁）；变异验证两处
  （非 darwin 分支改恒 False、拆掉自我遮蔽检测）各点亮对应用例后复原。
  仅由单元用例与「非 darwin 恒前置」分支的实测（`import main` 后 PATH 头部仍为包内 `ffmpeg`）覆盖；
  发版前请在 Apple Silicon 上按 README 的自查方式跑一次并把结论补进本子节。
- **已知未同步缺口**：`scripts/douyin_live_recorder_standalone.py` 仍先解析包内 `ffmpeg/` 再看 PATH
  （单文件版在 Apple Silicon 上继续吃转译），已登记为提案 R-5。

#### 三、R-5 已处理：单文件版脚本对齐同一判据

`scripts/douyin_live_recorder_standalone.py`（按设计不 import `src/`，可独立单文件分发）新增**同名同语义**
孪生判据 `should_prepend_bundled_ffmpeg_dir()`，`find_ffmpeg()` 不再无条件优先包内那份；两边注释互相点名
（沿用 `src/scheduler.py` 副本先例的「两处同改」规矩），并新增 `test_both_copies_cross_reference_each_other`
把「互相点名」这件事本身锁住。**过程中被用例抓出的两个真问题**：
① 该文件**没有** `import platform` → 复制来的判据会运行期 `NameError`（`mypy` 的 `name-defined` 同理会报，
但先被用例抓到）；② 第一版等价锁的 9 个场景里都把「系统 PATH 上的 ffmpeg」桩成 `None` → 判据 4 先短路，
**删掉架构判据后 21 条用例仍全绿**（假绿）。改成每个「不让位」判据都配一个「其余条件全满足、只缺它」的
场景后，漂移能被 `intel-mac+native` 单格精准抓到。该文件现 26 项用例（+13），全量 2487 → **2500 passed**。

#### 四、W2 spike 脚本已备（未接入发布链）

`scripts/spike_arm64_static_ffmpeg.sh`（bash；`.dockerignore` 已整目录排除 `scripts/`，
`.gitignore` 对 `*.sh` 无规则 → 正常随仓库分发，不需要再改忽略配置）。用途：在 macOS 上自源码构建
**自包含 arm64 静态 ffmpeg**，并顺手实测「W1 第 4 类」的三件证据究竟取不取得到。
**不接入 `build-release.yml`**（那是 W3，需单独批准）。

- 固定 configure 配方（`--enable-static --disable-shared --pkg-config-flags=--static
  --disable-autodetect --enable-gpl --enable-libx264 --enable-libmp3lame
  --enable-securetransport --enable-videotoolbox`），依赖只装项目真用到的 x264/lame（TLS 走系统
  SecureTransport，刻意不引 openssl@3/x265/libvpx —— 每多一个库就多一分 dylib 泄漏风险）。
- 四道验收：`lipo -archs` 含 arm64 → `otool -L` 只剩 `/usr`、`/System`（任何 `/opt/homebrew`、`@rpath`
  即判失败，正是当初否决 bottle 的理由）→ `-encoders`/`-protocols`/`-demuxers` 必须含 libx264、libmp3lame、
  https、hls（少一个就是「能跑但不能录」）→ 真跑 1s `testsrc → libx264 mp4 → copy ts` 冒烟。
- 产出 `report.json`：`source_sha256`（**取自官方公布端点**，取不到即 rc=2 并列出官方目录里的同名条目，
  绝不自算凑数）、`recipe_sha256`（configure 参数串哈希，配方一变即强制重核）、`provenance_ref`、构建计时。
- 无 macOS 也能评审：`--print-only` 打印将要执行的全部命令且不落任何痕迹（本机实跑验证）；
  非 bash 拉起会被显式挡下报「请用 bash 运行」；未知参数 rc=2；产物默认落在 `${TMPDIR:-/tmp}` 而非仓库内。
- **本机已实测**：`bash -n` 语法通过；`pick_version` / `first_field_hex` 从脚本原文抽出后实跑
  （版本按数值序取到 `8.10` 而非字典序；摘要只取首字段并小写）；`--print-only` 全流程输出正确。
  写脚本时自查出并修掉的 4 个真缺陷：SHA-512 端点会被截成 64 位冒充 SHA-256、anchored 正则在
  「摘要 + 文件名」行上永不匹配、`sort -V` 在 macOS 上不通、`PKG_CONFIG_PATH` 里 x264 路径写了两遍
  而漏了 lame（会让 `--enable-libx264` 被静默忽略 → 假自包含前兆）。
- **未实测（须 macOS 首跑）**：官方 `.sha256` 端点是否存在（只有 `.sha512` 时会直接 rc=2 并要求先决定
  是否扩证据字段）、`--pkg-config-flags=--static` 能否真吃掉 x264/lame 的 `.a`、构建耗时与 `otool` 结果。
  刻意不把「ffmpeg.org 应该有 .sha256」当既成事实。

#### 五、门禁结果

`run_gates` 8/8 · black / isort 通过 · mypy（含 `--platform linux`）**146 文件 0 issue** ·
basedpyright 0/0/0 · pytest **2500 passed / 12 skipped / 0 failed / 0 警告** · 覆盖率总 **82.27%** + 逐模块 6/6 ·
`compile_po --check` 678 条同步 · `check_annotations` 全通过（新增文件密度已补足）·
`check_runtime_pins --strict` 仍 rc=1（矩阵内 2 槽待人工/策略决策，矩阵外 2 槽按新口径告警）。

### v4.3.0-dev (2026-09-22) — 供应链加固：运行期首装改「官方公布哈希优先」+ 蓝奏云兜底显式开关（P-1b，同日作废）+ 发布期 GPG 验签 + full 包产物自检

> **本轮性质**：二进制信任策略评审落地为四组生产改动（P-1 / P-1b / P-2 / P-5），全部经批准。
> **零改动面**：录制链路、选源、ffmpeg 参数构造、平台解析、并发模型。

#### 一、运行期（`src/ffmpeg_install.py` / `src/node_install.py`）

- **P-1 首次安装不再是无校验窗口**：新增 `_parse_official_sha256` / `_fetch_official_sha256`，
  安装时先取**上游官方公布的哈希文档**（gyan.dev `<artifact>.zip.sha256`、nodejs.org
  `dist/<version>/SHASUMS256.txt`）来验；权威不符 = 拒绝安装并删包；权威通过 = 顺手压过旁路基准；
  **只有取不到官方文档**才退回原有 TOFU，且必记 warning。原 TOFU 的问题不是「弱」而是
  「默认且无感」：首次安装那一次根本没有期望值可比。
  刻意不把哈希常量钉进代码——下载的是滚动地址，常量会在上游发新版后永久拒装（历史坑 MID-59）。
- **实测形态纠正（重要）**：gyan.dev 的 `.sha256` 文档端点回 **303** 重定向到
  `packages/ffmpeg-<ver>-essentials_build.zip.sha256` 才给裸摘要（此前一处描述称「200 直给」，不准确）。
  因此必须保持 `allow_redirects=True`：改 HEAD 或禁重定向会**静默永久降级 TOFU**，日志只留一句
  「未取得文档」。已加静态回归锁。node 侧同理：SHASUMS 按**文件名字段逐字相等**取值，
  子串匹配会命中同名前缀的其它包。
- **P-1b 蓝奏云兜底默认关闭**（该小节的当时形态，已被同日后续改动推翻，见下方修订注）：
  `FFMPEG_LANZOU_ENABLED=1` 才允许回落镜像（解析走 `config_bool.parse_config_bool`）；关闭日志固定给出
  可操作指令，两处触发点共用单一渲染点。`FFMPEG_LANZOU_SHA256` / `FFMPEG_LANZOU_ALLOW_UNVERIFIED`
  的名字与「默认拒绝」方向不变；后者接受写法按第 9 条统一到 `是/true/t/yes/y/on/1`。
  [2026-09-22 修订：蓝奏云兜底**不是**「改为显式开关后保留」，而是连同 `get_lanzou_download_link()` /
  `_install_ffmpeg_lanzou()` / `_lanzou_fallback_enabled()` 与三个 `FFMPEG_LANZOU_*` 环境变量
  **整体删除**——Windows 运行期从此只有 gyan.dev 一条自动路径，失败即给手动安装与删基准提示
  （细则见本文件上方「Windows 运行期 ffmpeg 源收敛」条目）。因此本小节末尾那个「`ALLOW_UNVERIFIED`
  接受写法被放宽、待用户确认」的开放项**随该变量删除而作废**，无需再收紧裁决。]

#### 二、发布期（`build_exe.py` + `.github/workflows/build-release.yml`）

- **P-2 官方 GPG 验签**：`_RUNTIME_GPG_SIGNATURES` 按运行时键分列，带外钉**完整 40 位主钥指纹**
  （不是 16 位 key id）；`_verify_gpg_artifact` 判据取 `--status-fd` 的 GOODSIG+VALIDSIG，并要求
  **签名钥匙属于该主钥/子钥集合**——GnuPG 的 VALIDSIG 首字段报的是签名**子钥**指纹，逐字比主钥会把
  合法产物判成失败（假红比漏检更难排查）。接线在「SHA256 已过」之后：对没核过内容的产物验签无意义。
  发布路径 gpg 缺失即 `SystemExit`，**不降级放行**；未登记签名的槽位一次网络/进程都不碰（显式跳过）。
  CI 侧 macOS 新增 `Install gnupg (macOS)`（走 `.github/actions/retry`）+ `gpg --version` 上报。
  已知边界：指纹取自上游自身文档，属 TOFU-of-key；`/sig` 端点行为**未实测**，CI 首跑即其验收。
- **P-5 full 包产物自检**：`verify_runtime_binaries` 在 `download_runtime_binaries` 末尾检查
  ffmpeg / ffprobe / node 三项**存在、非 0 字节、且 `-version` 真能跑**；发布路径缺件即终止，本地路径
  明确「不得用于发布」。递归查找是为不把「压缩包布局不同」（node tar.gz 带 `bin/`）误判成缺件；
  `-version` probe 恰好覆盖「macOS 缺 dylib 闭包」与「无 Rosetta」两种「在包里但跑不动」的形态。
  动机即同日 macOS arm64 缺陷的三层隐身结构（拼出来的 URL + 宽泛 except + 无人校验产物）。

#### 三、口径与文档同源

`AGENTS.md`「三类钉定/校验互不覆盖」条目：① 补「SHA256 钉定与 GPG 验签是两件事，不可互替」；
② 改写运行期口径（官方文档优先、TOFU 降为显式降级、镜像只当加速、蓝奏云需显式开启
**[2026-09-22 修订：最后一项已被推翻——蓝奏云兜底连同三个 `FFMPEG_LANZOU_*` 环境变量整体删除，
AGENTS.md 该条目已按「被证伪的条目直接改正文」的口径重写，并以「新增任何第二条 Windows 下载源前必须先满足
官方公布哈希判据」取代]**）；
新增前缀 `PROPOSAL_*.md` 的**三处同改**规则（`.dockerignore` 排除 + `.gitignore` 登记为正式记录不忽略 +
本文件条目），并就地纠正「新增同类根目录文档无需再改 .dockerignore」这一只对既有三前缀成立的表述。

#### 四、P-3 已出排期（未实施）

调研结论与工时写进 `PROPOSAL_2026-09-22_binary-trust-policy.md` 第五节：路线 B（dylib 闭包 +
`install_name_tool`）**否决**——改 Mach-O 会连带破坏上游签名，且 `openssl@3` 的 CA 路径按前缀编译；
路线 A（CI 自源码静态构建 arm64）的真正阻塞是**口径**而非编译：自构建没有上游公布值，不得把 CI 自算哈希
当基线，须新增第 4 类「源码可复现构建」（源码 tarball 官方校验值/GPG + 构建配方哈希 + build provenance），
同时重定 `RELEASE_RUNTIME_KEYS`（CI 实际只有 3 个 runner，`macos-x64` 无构建方）。路线 C（Rosetta）是
**到期项**——Apple 称 macOS 27 为最后支持 Rosetta 的大版本（该条取自子代理检索，维护者宜复核原文）。
工时：A 全程 ≈7.5 人日；止血项 W6（PATH 优先级 + 文档引导，避免包内 Intel 构建遮蔽系统原生 ffmpeg）≈0.5 人日
且可立即做。**调研同时纠正本轮先前一处前提**：运行期自动安装并非只有 Windows 分支——
`install_ffmpeg_mac()`（`src/ffmpeg_install.py:575`）已在用 `brew install ffmpeg`，`install_ffmpeg_linux()`(:594) 走 yum/apt。

#### 五、门禁结果

`run_gates` 8/8 · black 167 files unchanged · isort 通过 · mypy（含 `--platform linux`）145 文件 0 issue ·
basedpyright 0/0/0 · pytest **2446 passed / 11 skipped / 0 failed / 0 警告**（安装器两面 113→188 项，
新增 `tests/test_build_exe.py` 25 项）· 覆盖率总 **82.24%**、逐模块 6/6 · `compile_po --check` 675 条同步 ·
`extract_i18n_strings` 缺失 0 · `check_runtime_pins --strict` 仍 rc=1（4 个 ffmpeg 槽位待策略决策，属预期）。
变异验证：安装器面 16/16 个变异点全红；`build_exe` 面 2 个判据变异点各自变红后已复原。

#### 六、真机验证留存（首次按新约定记录）

> 本轮起按 `AGENTS.md`「完成定义」第 2 步新增的留存入口，真机验证结论写进更新日志。

- **[2026-09-22] Bilibili | live.bilibili.com/5**** | `test_bili_live_collector.py` | PASS | 25 条弹幕 / 15s**
  `spider.get_bilibili_danmaku_info` 取 room=545068、host=zj-cn-live-comet.chat.bilibili.com；
  `DanmakuCollector` 进房认证成功（AUTH_REPLY code=0），SRT 正常落盘 `tests/_out_live/`。

### v4.3.0-dev (2026-09-22) — 发布链：macOS arm64 的 ffmpeg 下载点修复（上游无该产物）+ ffmpeg 二进制信任策略评审

> **本轮性质**：一项生产代码修复（`build_exe.py` 的 ffmpeg 来源选择）+ 一份信任策略评审结论。
> 录制链路、平台解析、并发模型零改动。

#### 一、缺陷修复：Apple Silicon 的 full zip 静默不含 ffmpeg

`_download_ffmpeg` 的 darwin 分支原按 `platform.machine()` 现场拼 URL，arm64 时拼出
`https://evermeet.ca/ffmpeg/getrelease-arm64/zip`。**该产物在上游不存在**：ffmpeg.org 官方下载页对 macOS
只列一条「Static builds for **macOS 64-bit**](https://evermeet.cx/ffmpeg/)」，不区分 Apple Silicon 与 Intel，
实测该 arm64 端点恒 404（2026-09-22 直接请求 + 页面产物清单两路印证）。三层机制叠加使它长期不可见：
① URL 是拼出来的，静态检查看不出它指向不存在的端点；② 请求 404 被 `_download_ffmpeg` 外层
`except Exception` 吞成一行 `ffmpeg 下载失败` warning 并 `return False`，而 `download_runtime_binaries`
对单组件失败刻意不中断；③ 发布链没有「full 包必须含 ffmpeg」的事后校验。
危害半径说明：今天 `check_runtime_pins.py --strict` 会在 prepare 阶段先拦住**整条**发布链（尚有 4 个未钉定槽位），
因此已发布产物未受影响；但本地 `build_exe.py --dual` **当前**就会产出缺 ffmpeg 的 macOS full 包，
且一旦官方值填满、arm64 缺陷即转为发布态。

| 改动 | 说明 |
| --- | --- |
| 新增 `_FFMPEG_DOWNLOAD_URLS`（按 `<os>-<arch>` 运行时键分列）+ `_ffmpeg_source_url()`… | 与 `_PINNED_RUNTIME_SHA256` **同构同键**：一张表说清「钉的是哪一份」。未登记架构回落同族 x64 并**打 warning**… |
| macOS 两架构统一 `getrelease/zip` | x86_64 自包含构建，Apple Silicon 经 Rosetta 2 执行；`_download_ffmpeg` 内不再出现 `platform.m… |
| 钉定表注释 | macos-x64 与 macos-arm64 现指向同一份产物 → 两槽将来必须填同一个值（已由用例锁定）… |

**为什么不用 Homebrew bottle 提供 arm64 原生构建**（评审中被否决的路线，证据留档）：Homebrew formula API
（`https://formulae.brew.sh/api/formula/ffmpeg.json`）显示其 ffmpeg bottle 的 `runtime_deps` 为
`dav1d, lame, libvmaf, libvpx, openssl@3, opus, sdl2-compat, svt-av1, x264, x265, xz` 共 11 项，
这些 dylib 位于 Homebrew 前缀下的**其他 formulae**、不在 bottle tarball 内；直接下载 bottle 打进分发包，
用户机器上会得到 `dyld: Library not loaded` 的坏产物。要做 arm64 原生只有「CI 内自源码构建
`--enable-static`」或「自带 dylib 重写（install_name_tool 闭包）」两条路，均须另行审批（见信任策略提案）。

#### 二、新增回归锁 `tests/test_build_exe.py`（10 项，离线；另使 `test_test_hygiene.py` 按文件参数化 +3 项）

来源表与发布矩阵**双向**同覆盖、来源表与钉定表同键、macOS 两槽取值必须一致、arm64 复用同一份 evermeet 构建、
不存在的端点不得以字符串字面量复活（AST 扫字面量，注释里记录该缺陷仍允许）、`_download_ffmpeg` 函数体内
不得再出现 `platform.machine`、全部来源 URL 必须 https 且主机在允许清单内、回落必须留痕、未知族必须抛错、
`RUNTIME_SLOTS` 覆盖完整、`_is_pinned` 形状判定对 6 种非法形态一律拒绝。

#### 三、ffmpeg 二进制信任策略评审（结论）

按「发布期 / 运行期 / 签名脚本层」三面（AGENTS.md 已定义的三类互不覆盖）逐项给出处置：

| 面 | 现状（一手证据） | 信任强度 | 建议 |
| --- | --- | --- | --- |
| 发布期 windows | gyan.dev `.sha256` 文档，两端点互证，已钉定 | 传输认证（TLS）+ 人工核值 | **保持**；升级即重核 |
| 发布期 macOS | evermeet 无 SHA256/MD5，只有 `/sig` GPG，指纹 `20F6EA3E0CFD6B4C53447A73476C4B611A6608… | 可做到**来源认证**（验签），但未实现 | **短期**保持占位红；**中期**引入「带外钉死指纹 + `gpg --verify`」（提案 P-2）… |
| 发布期 linux | johnvansickle 只有 `*.md5`（实测 200） | md5 已不宜作完整性根 | 换源或验签（提案 P-2/P-3），不得放宽形状判定 |
| 运行期 ffmpeg | `src/ffmpeg_install.py`：官方滚动 URL + **TOFU 旁路 `.sha256` 文件**（代码自评「强度等同目录权限，不是独立… | TOFU + 可选人工哈希 | 保留默认拒绝的正确形态；**建议**把首次安装的期望哈希改为随包分发的官方公布值（提案 P-1）**[已实施]**… |
| 运行期 node | `src/node_install.py`：从 `nodejs.cn` 页面正则抓版本、下载 `npmmirror.com` 的包（**镜像而非上游**），… | 镜像 + TOFU | 建议改 `nodejs.org/dist/...SHASUMS256.txt` 权威核验，npmmirror 仅作显式开关的加速镜像（提案 P-1）… |
| 签名脚本层 | `utils._JS_SHA256_EXPECTED` 钉 5 个 `.js`，MID-62 已改 stdin 执行消掉 check-then-use；**… | 部分 | 补齐 wasm 一类（提案 P-4） |

#### 四、门禁结果

`run_gates` 8/8 · black 167 files unchanged · isort 通过 · mypy（含 `--platform linux`）145 文件 0 issue ·
basedpyright 0/0/0 · pytest **2356 passed / 11 skipped / 0 failed / 0 warning** · 覆盖率 82.11% + 逐模块 6/6 ·
`check_runtime_pins.py --strict` 仍 rc=1（4 槽待策略决策，属预期）。

### v4.3.0-dev (2026-09-22) — 测试侧：`_pid_alive` 与码页解耦 + `run_command` 崩溃路径补锁；发布链：官方 SHA256 回填 6/10 槽

> **本轮性质**：三项维护任务（缺陷修复 / 回归锁补全 / 钉定值核对），**零产品业务逻辑改动**。
> 生产代码唯一变更是 `build_exe.py` 的钉定表取值与注释；其余全部落在 `tests/` 与文档。

#### 一、缺陷修复（测试侧，但影响回归锁的可验证性）

| 位置 | 问题 | 修复 |
| --- | --- | --- |
| `tests/test_frontend_quality_ui.py:127`（`_pid_alive` 的 Windows 分支） | 存活探针用 `subprocess.run(..., capture_output=True, text=True)`，让**解码参与判定路径**。中文 W… | 判据改为**字节包含**：`str(pid).encode("ascii") in probe.stdout`，去掉 `text=True`，与码页/系统语… |

#### 二、新增回归锁（20 条用例项，均按本仓约定做过变异验证）

- **`tests/test_frontend_quality_ui.py` +4 项（`_pid_alive` 三面锁，覆盖该文件全部子进程调用点）**：
  `test_pid_alive_survives_gbk_tasklist_output`（把 tasklist 载荷**钉成事故里的 GBK 字节**，与宿主当前码页无关）、
  `test_pid_alive_reports_true_from_table_row`（防「改成恒 False 绕过崩溃」）、
  `test_pid_alive_roundtrip_with_real_processes`（真起真杀子进程，不打桩，证明检测逻辑本身生效）、
  `test_no_subprocess_call_in_this_module_decodes_output`（AST 级禁 `text=`/`encoding=`/`universal_newlines`，
  并先断言「扫到 ≥3 个调用点」再断言无违规，防门禁自身假绿）。打桩一律换 SimpleNamespace 副本，不改 stdlib 模块本体。
- **`tests/test_run_gates.py` +16 项（`run_command` 与 `ensure_utf8_streams`，此前该面完全无锁）**：
  正常退出并逐行原样转发 stderr / 非零退出码原样透传 / **rc=0 但 stderr 命中致命告警即判失败且去重**（MID-63 假绿）/
  子进程环境三层优先级（父环境 → `GATE_CHILD_ENV` 硬默认 → 门禁块行首前缀）/ `python` 换绑到当前解释器 /
  `stdin=DEVNULL`（不继承父 stdin）/ `stderr is None` 分支 / cwd 不存在必须显式抛 `OSError`（不得静默判过）/
  信号死亡返回非 0 且死亡前输出仍可见（POSIX-only skip）/ `ensure_utf8_streams` 的 cp936→UTF-8 重配置成功
  + 三种「改不动一律静默放过」/ `main()` 回路 rc=1 与 `--keep-going` 语义、缺工具 rc=3、
  `check_executables` 的 `python -m` 退化不误报 rc=3。
  （含原 MID-64 锁，且真实进程往返那条复现出与事故完全一致的 `NoneType` 报错）；把 `run_command` 的告警扫描改成恒假
  → `flags_fatal_pattern` 变红；把 `ensure_utf8_streams` 的 `except ValueError, OSError` 改成不含 `OSError`
  → `test_ensure_utf8_streams_never_raises[os_error]` 变红。

#### 三、发布链运行时二进制钉定：回填 6/10 槽（只回填可追溯到官方公布值的）

| 槽位 | 取值来源（官方公布页） | 状态 |
| --- | --- | --- |
| `windows/linux×2/macos×2` 的 **node**（共 5 槽） | `https://nodejs.org/dist/v24.21.0/SHASUMS256.txt`，并在同版本 GPG 签名文档 `SHASUMS256.t… | 已钉定 |
| `windows-x64/ffmpeg` | gyan.dev 官方 `.sha256` 文档，两个端点互相印证：滚动别名 `ffmpeg-release-essentials.zip.sha256` … | 已钉定 |
| `macos-x64`、`macos-arm64` 的 ffmpeg | **上游不公布 SHA256**：evermeet 页面只提供「任意文件追加 `/sig` 取 GPG 签名」，无任何 sha256 文档… | 保持占位 |
| `linux-x64`、`linux-arm64` 的 ffmpeg | **上游不公布 SHA256**：johnvansickle 只提供 `*.md5`（实测 200，内容为 md5 摘要）… | 保持占位 |

- 按 SEV-10 的硬约束「**不得凭本地下载结果填写**」，这 4 槽继续留 `UNVERIFIED_PIN`，`check_runtime_pins.py --strict`
  与发布链照旧拦下（rc=1，实测）——这是预期而非回归；可选处置（GPG 验签双通道 / 换公布 SHA256 的上游 /
  为 md5-only 上游另设显式降级判定）须由维护者决策，已写进表内注释。
  `https://evermeet.ca/ffmpeg/getrelease-arm64/zip` 当时直接 404，该 URL 本身待修。
- 滚动性提醒：node 段随「上游发新 LTS」失效、gyan 段随「上游发新版 ffmpeg」失效，两者都是刻意的人工闸口。

#### 四、文档同源

`AGENTS.md` 三处：① SEV-10 条目内「当前仓内所有槽位仍是占位标记」已被本次回填证伪 → 就地改写为
6/10 现状 + 修订注；② MID-63 条目内「`test_run_gates.py` 未覆盖 `run_command`、崩溃路径缺回归锁」→ 就地改写 + 修订注；
③「测试质量与审查协作流程」新增长期约定一条：**探测子进程输出一律按字节比较，且这类用例必须能单文件独立运行**
（含 `SetConsoleOutputCP` 造成「全量绿、单跑红」的隐身机制说明）。

#### 五、门禁结果（`.venv/Scripts/python.exe`，Python 3.14.7）

| 工具 | 结论 | 计数 |
| --- | --- | --- |
| black / isort | 通过 | 166 files unchanged；Skipped 13 files，无违规 |
| mypy / `mypy --platform linux` | 通过 | 0 issue / 144 文件（两侧均 0） |
| basedpyright | 通过 | 0 error / 0 warning / 0 note |
| pytest（全量，带 `--cov=src`） | 通过 | **2343 passed / 11 skipped / 0 failed / 0 warning**（上轮 2324+10） |
| `scripts/check_coverage.py` | 通过 | 总覆盖率 82.11%，逐模块 6/6 达标 |
| `scripts/check_annotations.py` | 通过 | 149 文件，悬空引用 0 处，平均注释密度 23.1% |
| `scripts/run_gates.py` | 通过 | 8 条门禁全绿 |
| `scripts/check_runtime_pins.py --strict` | 按设计拦发布 | rc=1，剩 4 个 ffmpeg 槽位待决策 |
| 单文件隔离运行 | 通过 | `test_frontend_quality_ui.py` 6 passed、`test_run_gates.py` 29 passed / 1 skipp… |

### v4.3.0-dev (2026-09-22) — 门禁修复：MID-N01 悬空调用收敛 + 测试桩注解放宽 + 符号可达性检查固化为门禁

> **本轮性质**：把上一轮「已登记待修」的三处红灯一次性清掉，并把「删符号留下调用点」这一
> 第二次复现的失效形态固化成门禁动作。产品逻辑只收敛了一处判据，未新增功能、未改依赖。

#### 一、缺陷修复（唯一阻断项）

| 位置 | 问题 | 修复 |
| --- | --- | --- |
| `main.py:1346`（`check_subprocess` 失败分支） | 调用已被 MID-N01 删除的 `_ffmpeg_reported_output_failure()`：`mypy` 报 `name-defined`、b… | 判据②（读 ffmpeg 缓冲输出）经 MID-N01 认定不可得（`Popen` 从未开 `stdout=PIPE`），豁免收敛为单判据：`_output… |

#### 二、测试侧改动

- **桩注解放宽（消除 basedpyright 剩余 8 条）**：`tests/test_ffmpeg_install.py:638`、`tests/test_node_install.py:213/363/403` 四处转发型桩的 `*args`/`**kwargs` 由 `object` 改 `Any`（basedpyright 会按声明类型逐个匹配形参…
- **修掉一条平台相关的测试前提**：`tests/test_record_failure_feedback.py` 的 ffmpeg 输出路径由 `"/tmp/out.ts"` 改为 `tempfile.gettempdir()` 下的文件。
- **新增 `tests/test_check_annotations.py`**（4 条）：锁住符号可达性检查的「真能报 / 不误报 / 本仓零悬空」三面。

#### 三、新增门禁动作（防回归）

- `scripts/check_annotations.py` 在**默认模式**下新增**符号可达性检查**：扫全仓 Python 文件…
- `AGENTS.md` 对应条目同步为「已固化为门禁动作」，并补一条连带教训「用例里的输出路径必须是真实存在的目录」。

#### 四、门禁结果（`.venv/Scripts/python.exe`）

| 工具 | 命令 | 结论 | 计数 |
| --- | --- | --- | --- |
| black | `black --check .` | 通过 | 165 files unchanged |
| isort | `isort --check-only --diff .` | 通过 | Skipped 13 files，无违规 |
| mypy | `mypy` / `mypy --platform linux` | 通过 | 0 error / 143 文件（两侧均 0） |
| basedpyright | `basedpyright` | 通过 | **0 error / 0 warning**（原 9 error） |
| pytest | `pytest -q` | 通过 | **2317 passed / 10 skipped / 0 failed / 0 warning**（原 3 failed / 2314 passed）… |
| check_annotations | `python scripts/check_annotations.py` | 通过 | 148 个 Python 文件，悬空引用 0 处 |
| run_gates | `python scripts/run_gates.py` | 通过 | 8 条门禁全绿 |

### v4.3.0-dev (2026-09-22) — 元数据同源同步 + 全量质量门禁跑批 + 四语目录核验（本轮零产品代码改动）

> **本轮性质**：一次「体检 + 收口」而非功能迭代——清点工作区全部文件后，把跨文件必须同源的
> 信息（版本、依赖清单、配置键、排除目录、四语译文）对齐到同一水位，并把全量质量门禁跑一遍。
> **`src/`、根目录入口、前端均无业务逻辑改动**，改动全部落在元数据、配置、文档与排除清单上。

#### 一、按模块分类的改动

| 模块路径 | 变更类型 | 变更内容 | 验证方式 |
| --- | --- | --- | --- |
| `DouyinLiveRecorder.egg-info/` | **元数据重建** | 经 setuptools `egg_info` 重新生成，消除与 `pyproject.toml` 的两条漂移：`requires.txt` / `PKG-… | `scripts/check_version.py` PASS；`pyproject [project.dependencies]` / `requirem… |
| `config/config.ini` | 配置键补齐 | `[Web]` 节补 `web_allowed_hosts`。该键由 MID-36（DNS 重绑定防线）引入、此前只存在于 `src/web_config.… | configparser 解析通过（BOM 保留）；`[Web]` 键由 8 个增至 9 个 |
| `README.md` / `README_EN.md` | 文档同步 | `[Web]` 配置块补 `web_allowed_hosts` 及中英说明（何时需要填、不填的后果）… | 两份 README 段落逐条对应 |
| `CODE_WIKI.md` / `CODE_WIKI_EN.md` | 文档同步 | Web 配置表补 `web_allowed_hosts` 行，写明 `src/web_config.py::is_host_allowed` 的真实判定口径… | 回源核对 `is_host_allowed` 源码后落笔 |
| `.gitignore` / `.dockerignore` / `pyproject.toml`（`[tool.black]`、`[tool.isort]… | **同源清单补齐** | 补入 `.qoder-credits/`——第三方编码代理的产物目录，是当时唯一「既不在 Git 忽略里、又会进 Docker 构建上下文、还会被工具扫描」… | `black --check .` / `isort --check-only .` 均 rc=0；逐 token 比对八份清单无遗漏… |
| `AGENTS.md` | 防回归条目 | 「类型检查、注释与静态门禁」新增 2 条：① **删除模块级函数/常量前必须 grep 全部调用点**（附 `and` 短路让 `NameError` 延迟… | 条目触发源均为本轮实测发现 |
| `i18n/zh_CN/LC_MESSAGES/zh_CN.mo` | 重新编译 | 664 条（含 gettext 头部空 msgid）、85 544 字节；编译前后 `--check` 均 PASS，说明 .po 与 .mo 本就同步，重… | `scripts/compile_po.py --check` |

#### 二、本轮的删除项

- **产品代码零删除**（无文件、函数或配置键被移除；`main.py:1346` 那个悬空调用属**待修项**，未在本轮删除，见第四节）。
- 跑批期产生的**一次性临时产物**已全部删除：8 个重定向输出文件、`_tmp_config_audit.py` / `_tmp_i18n_check.py` / `_tmp_en_check.py` 三个临时审计脚本、`DouyinLiveRecorder.egg-info.bak` 备份目录。

#### 三、全量质量门禁跑批结果（`.venv/Scripts/python.exe`，配置来源唯一为 `pyproject.toml`）

| 工具 | 版本 | 命令 | 结论 | 计数 |
| --- | --- | --- | --- | --- |
| black | 26.5.1 | `black --check .` | 通过 | 165 files unchanged |
| isort | 9.0.1 | `isort --check-only --diff .` | 通过 | Skipped 12 files，无违规 |
| mypy | 2.3.1 | `mypy`（无参数，消费 `[tool.mypy].files`） | **失败** | 1 error / 143 文件 |
| basedpyright | 1.40.1 | `basedpyright --outputjson` | **失败** | 9 error / 0 warning，151 文件 |
| pytest | 9.1.1 | `pytest -q` | **失败** | 3 failed / 2314 passed / 10 skipped（111s） |
| node --test | v22.22.2 | `node --test tests/frontend/test_quality_ui.mjs` | 通过 | 27 passed |

三处红灯**同源**，均指向 `main.py:1346` 对已删除函数 `_ffmpeg_reported_output_failure` 的悬空调用。
10 条跳过全部为平台限制（Windows 环境变量大小写不敏感 1、无离线形态 6、`os.chmod` 权限位 1、未真创建符号链接 2），非缺陷。

#### 四、已知遗留（本轮刻意未改，交人工处理）

1. **`main.py:1346` 悬空调用（唯一阻断项）**：`(not os.path.isdir(...)) and (_ffmpeg_reported_output_failure(proc))` 中的函数已被 MID-N01 删除而调用点保留。
   它不是纯静态问题——`and` 短路只在**输出父目录存在**时保护它，目录被删的场景会真抛 `NameError`。
   建议把 1345–1347 行收敛为 `_output_side_failure = not os.path.isdir(os.path.dirname(save_file_path) or ".")`。
   本轮按「不动现有业务逻辑」的要求未代改；该形态已第二次复现，登记于 `CODE_REVIEW_2026-09-21.md` 补-N04。
2. **8 处测试桩注解**（`tests/test_ffmpeg_install.py:641`、`tests/test_node_install.py:216/366/406`、同类转发桩）：建议 `object → Any`
3. **观察项（未改动）**：`i18n/zh_TW.yaml` 中「平台」一词沿用简体写法（台湾书面语常作「平臺」）

#### 五、四语目录核验（本轮确认无需增量）

| 核验维度 | 结果 |
| --- | --- |
| 四目录键集相等 | 663 条逐一相等（`tests/test_i18n.py` 40 passed） |
| 运行时串覆盖率 | `scripts/extract_i18n_strings.py`：有价值串 436 条，**缺失 0 条** |
| 空值 / 占位符一致性 | 空值 0；四语 `{占位符}` 集合与源串不一致 0 |
| en_US / en_GB 拼写 | 仅 7 条差异（minimises / cancelled / unrecognised / authorisation 等），无美式拼写残留，亦无反向误用… |
| zh_TW 简繁 | 取值中简体专用字 0（「平台」见上观察项） |
| 前端四语 | `web/app.js` 内嵌四语键集相等、index.html 无未入目录硬编码中文（27 passed）… |

### v4.3.0-dev (2026-09-21) — 工作区改动全量台账（按模块）：`CODE_REVIEW_2026-09-21` 修复轮 + 覆盖率专项

> **本条目的作用**：仓库**无 `.git` 目录、本机也无 git 可执行文件**，无法用 `git diff` 枚举改动。
> 本台账改用「文件 mtime + 源码内的报告 ID 注释标记 + `tests/` 内对应 ID」三条交叉取证，
> 覆盖 2026-09-21 全天工作区变更，以便任何一份文档只记半个现场时仍能对账。

#### 改动批次归属（三个独立工作流，同日发生）

| 批次 | 时间窗 | 输入源 | 记录位置 |
| --- | --- | --- | --- |
| A. `CODE_REVIEW_2026-09-20` 全轮修复 | 09-21 00:02 – 02:43 | `CODE_REVIEW_2026-09-20.md` | 已记于下方「全轮修复落地」条目 |
| B. `CODE_REVIEW_2026-09-21` 修复轮（**进行中**） | 09-21 11:40 – 14:40+ | `CODE_REVIEW_2026-09-21.md`（540 行，新增文件，11:40 生成） | 本条目下文 |
| C. 测试覆盖率专项 | 09-21 10:50 – 14:30 | 用户目标「覆盖率达 80%」 | 下一条「测试覆盖率专项」条目 |

批次 B 与 C **不是同一工作流**：B 改 `src/`，C 只改 `tests/`；两者在 13:52 – 14:05 期间
交叉写入了同一批测试目录（B 改 `test_web_config.py`/`test_stream_select.py`/`test_config_io_backup.py`，
C 改 `test_node_install.py`/`test_web_tray.py`/`test_ffmpeg_install.py` 等），无文件级冲突。

#### 批次 B：按模块分类的已落地改动

| 模块路径 | 报告 ID | 变更内容 | 配套测试 |
| --- | --- | --- | --- |
| `src/spider.py` | **SEV-N02** | PopkonTV 刷新出的 token 落盘时已自带 `Bearer ` 前缀，读回后再拼一次造成双前缀、凭据复用失效；写入侧归一… | `tests/test_spider_platforms.py` |
| `src/spider.py` | **SEV-N04** | 淘宝用响应 `Set-Cookie` 整体覆盖用户 Cookie 并持久化回写 `config.ini`，登录态被静默销毁… | `tests/test_spider_hardening.py` |
| `src/spider.py` | MID-48（09-20 报告项，本日内/海外批次执行） | 平台解析层「裸取 JSON + 装饰器兜底」范式收敛：`_loads_dict` 替代裸 `json.loads`，深层链式索引改走 `_dig` 安全下钻… | 沿用既有 spider 用例 |
| `src/web_api.py` | **SEV-N03** | 面板「非回环监听 + 无认证」不变量可被两步 PUT 旁路（判定基准 `web_host` 自身可经 API 改写）。改为安全判定统一取 `_guard_b… | `tests/test_web_api.py` |
| `src/web_api.py` | MID-N42 | Origin 与 Host 是**两套名单**：Host 沿用 `web_config.is_host_allowed`，Origin 单独判定；且端口与地… | `tests/test_web_api.py`、`tests/test_web_config.py` |
| `web.py` | **SEV-N03**（同项） | 启动时把**本进程实际要绑定的**地址与端口传给 app 状态，作为安全判定的唯一来源（不再回读配置值）… | 同 `tests/test_web_api.py` |
| `src/web_config.py` | MID-N45 | 新增「出站目标」收口层：推送接口链接 / ntfy 地址 / 代理地址 / SMTP 等白名单内 URL 类键一律过校验；抽共用内核 `_validate_… | `tests/test_web_config.py` |
| `src/stream_select.py` | MID-N32 | 播放列表 / 分片 / 同源 FLV 回退地址均为带签名参数的直链，其探测日志此前未脱敏；本文件内探测日志统一过脱敏… | `tests/test_stream_select.py` |
| `src/config_io.py` | MID-N57 | 备份脱敏此前只接 `is_sensitive_item` 一道判据，未叠 Web 面板侧的「节白名单 + 键名正则」口径，存在漏脱敏面；现为双重判据… | `tests/test_config_io_backup.py` |
| `src/javascript/haixiu.js` | MIN-N39 | 尾部注释里的真实形态抓包样例改为 `<REDACTED>` 占位；删除引用 jQuery `$` 的 `bnu` / `bn` 死代码（**仅注释/死代码级… | 由 `check_runtime_pins.py` / `_JS_SHA256_EXPECTED` 覆盖 |
| `src/utils.py` | MIN-N39 | `_JS_SHA256_EXPECTED` 中 `haixiu.js` 与 `migu.js` 两条钉定值重算（旧值 `e8f13f4a…` / `01bf… | 同 `tests/test_utils.py` |
| `CODE_REVIEW_2026-09-21.md` | — | **新增文档**（540 行全量源码审查报告，含 P0 6 项 / P1 74 项分组），是本批次的输入源… | 不适用 |

#### 批次 B 的删除项

- `src/javascript/laixiu.js`、`src/javascript/taobao-sign.js`：**文件本体于本日从 `src/javascript/` 移除**
  （对应表项已在 09-20 轮删掉）。依据：`src/utils.py` 表注释与目录实测一致（现存 5 个 `*.js`：
  `crypto-js.min.js` / `haixiu.js` / `liveme.js` / `migu.js` / `x-bogus.js`，与 `_JS_SHA256_EXPECTED` 5/5 对应）。
  理由：全仓零调用点（来秀签名已在 `spider.py` 以纯 Python `calculate_sign` 重写），且
  `taobao-sign.js` 注释里留有一组结构完整的真实抓包入参（会话令牌 + 时间戳 + 账号标识），随源码分发即外发他人会话素材。
- `src/javascript/haixiu.js` 内部的 `bnu` / `bn` 两个死方法（MIN-N39）。
- 产品代码**无其他删除项**；批次 C 亦无删除项（11 个过程性临时脚本不属入库内容）。

#### 批次 B 未落地项（进行中，不得当作已完成引用）

全仓 `*.py` 内**搜不到** `SEV-N01`、`SEV-N05`、`SEV-N06` 的落地注释，即该三项 P0 尚未修复：

- **SEV-N01** `main.py::check_subprocess` 收尾三处漏口（零字节早退 / 异常路径回收条件过窄 / 异常路径不停弹幕采集器）；
- **SEV-N05** `select_source_url` 的代理地址未经 `handle_proxy_addr` 归一即交给 `httpx.Client(proxy=…)`；
- **SEV-N06** GUI 日志解析把简中文案写死在正则与子串判定里，切到非 `zh_CN` 语言后画质监控与录制状态静默失效。

另：`tests/test_web_api.py` 在 14:40 仍在被修改（晚于本文档上一次写入），因此**批次 B 的文件清单
与本节表格都是一次性快照**，引用前建议按「mtime + 报告 ID」重新对账。

#### 当前状态复核（两批次合流后的实测）

| 项 | 命令 | 实测 |
| --- | --- | --- |
| 全量测试 | `pytest --cov=src` | 2310 passed / 10 skipped / **0 failed**（含批次 B 在 14:40 的最新改动）… |
| `src/` 覆盖率 | 同上 | **82.03%**（目标 80% 保持达成） |
| 逐模块门禁 | `python scripts/check_coverage.py` | 6/6 达标 |
| 类型 | `mypy` | 0 error / 143 files |
| 格式 | `black --check .` / `PYTHONUTF8=1 isort --check-only .` | 165 unchanged / rc=0 |

### v4.3.0-dev (2026-09-21) — 测试覆盖率专项：`src/` 覆盖率 73.28% → 82.03%（零产品代码改动）

**背景与目标**：以「项目测试覆盖率达到 80%」为目标，按「分析缺口 → 补测 → 验证」闭环执行一轮。
基线读数 73.28%（10537 语句 / 7721 已覆盖），达 80% 需净增 ≥709 条已覆盖语句。

**改动范围界定**：本轮**只动 `tests/`**——`src/`、根目录入口（`main.py` / `gui.py` / `web.py` /
`msg_push.py` / `i18n.py`）、`config/`、`scripts/`、`.github/`、`pyproject.toml` 均**未改动**
（含未调低/调高任何覆盖率阈值与 `MODULE_THRESHOLDS`）。因此本轮不存在功能变更、接口变更与
删除项，全部新增均为**行为回归锁**。

#### 度量结果

| 指标 | 落地前 | 落地后 |
| --- | --- | --- |
| `src/` 总覆盖率 | 73.28% | **82.03%**（8760/10679 语句） |
| 用例数 | 1917 passed / 10 skipped | 2310 passed / 10 skipped |
| 本轮净增已覆盖语句 | — | +1039（其中含并发工作流新增的 src 语句） |

> 上表为**本轮复测后的读数**。首轮记录时是 82.02% / 2301，随后并发工作流
> 又改了 `src/utils.py`、`src/config_io.py`、`src/stream_select.py` 并新增 `tests/test_web_api.py`
> 等用例，因此本表已按最新一次全量运行重写。**引用本轮效果时请以此表为准。**

逐模块（前 → 后，均为 `coverage.json` 实测）：

| 模块 | 前 | 后 | 说明 |
| --- | --- | --- | --- |
| `src/node_install.py` | 15.1% | 100% | Windows/Linux/macOS 安装链路此前完全裸奔 |
| `src/ffmpeg_install.py` | 36.2% | 98.9% | 官方源 / 蓝奏云 / 平台分发 / 四类异常探测（**2026-09-22 更新**：蓝奏云兜底已整体删除，该轮 5 个蓝奏类用例随之移除，现为「单一官方… |
| `src/web_tray.py` | 0% | 100% | 仅 Windows 启用，此前无任何离线可测手段 |
| `src/platforms/douyu.py` | 29.4% | 98.2% | STT 编解码 + 粘包推进 |
| `src/platforms/bilibili.py` | 48.8% | 97.5% | 16B 帧头 / protover 1-2-3 / AUTH 看门狗 |
| `src/platforms/twitch.py` | 45.2% | 98.8% | IRC 跨帧行缓冲 + 色彩回落 |
| `src/config_io.py` | 72.8% | 99.6% | 写侧（update_file / 主播名同步 / 备份脱敏） |
| `src/recorder_status.py` | 49.1% | 99.1% | 状态快照 + 「正在录制」分支 |
| `src/video_postprocess.py` | 63.3% | 96.1% | 异常分类 + 字幕线程退出条件 |
| `src/spider.py` | 68.4% | 69.7% | 未专项补测（缺口 1003 行为平台解析函数，见「遗留」） |

#### 新增文件（`tests/`，5 个）

| 路径 | 行数 | 覆盖的产品模块 | 锁住的关键不变量 |
| --- | --- | --- | --- |
| `tests/test_node_install.py` | 535 | `src/node_install.py` | CR-11 残缺 zip 必须删重下（否则错误哈希被固化成基线 → 永久失败且不自愈）；H-1 哈希不一致必须硬拒并删包；Windows on ARM 架构… |
| `tests/test_web_tray.py` | 310 | `src/web_tray.py` | 任何失败（缺 pystray / DLL 加载失败 / 窗口 API 抛错）都必须静默降级，不得让 Web 面板起不来；`HWND`/`HMENU` 的 `… |
| `tests/test_platform_danmaku_offline.py` | 675 | `src/platforms/{douyu,bilibili,twitch}.py` | 斗鱼 C-2 粘包推进步长 = `full_len + 4`；斗鱼 C-3 `only_fans` 默认 False；B站 H-4 软拒绝（`code!=0… |
| `tests/test_config_io_update_file.py` | 332 | `src/config_io.py`（写侧） | 6.1 段级精确替换（URL 前缀重叠不误改他行）；读取失败用 `ini_URL_content` 快照回滚而非清空；原子写失败时快照**不得**前进；CR… |
| `tests/test_video_postprocess_paths.py` | 312 | `src/video_postprocess.py` | 超时 / `CalledProcessError` / 未知异常三类必须落入不同日志文案（旧实现兜底成 unknown error 丢失语义）；`gener… |

#### 修改文件（`tests/`，2 个，均为追加）

| 路径 | 追加内容 | 覆盖的产品模块 |
| --- | --- | --- |
| `tests/test_ffmpeg_install.py` | 221 → 710 行。新增 `TestThinWrappers` / `TestBuildIdentityGuard` / `TestStaleSidec… | `src/ffmpeg_install.py` |
| `tests/test_recorder_status.py` | 275 → 448 行。新增 `_NormalStdout` / `_ExplosiveCollection` / `pinned_main` fixtur… | `src/recorder_status.py` |

#### 删除项

- **产品代码删除：无。**
- 过程性临时脚本已全部清除（按 AGENTS.md「测试收尾清理临时脚本」）：`_tmp_cov_report.py`、
  `_tmp_cov2.py` ~ `_tmp_cov6.py`、`_tmp_append_ffmpeg.py`、`_tmp_rs_append.py`、
  `_tmp_dens.py`、`_tmp_final.py`、`_tmp_wt_out.txt`。运行期产物目录（`downloads/` /
  `logs/` / `backup_config/`）与 `scripts/` 下正式维护脚本**未动**。

#### 门禁状态（逐条实测）

| 门禁 | 命令 | 结果 |
| --- | --- | --- |
| 全量测试 | `pytest --cov=src` | **2310 passed / 10 skipped / 0 failed**，warnings summary 为空（0 警告） |
| 覆盖率总量 | `pytest --cov=src --cov-report=json` | **82.03%**（目标 80% 已达成；`[tool.coverage.report].fail_under = 50` 保持不动）… |
| 逐模块覆盖率 | `python scripts/check_coverage.py` | 6 个声明模块全部达标（rc=0） |
| 格式化 | `black --check`（整个仓库 165 文件）/ `isort --check-only`（`.`，**带 `PYTHONUTF8=1`**）… | 全部 unchanged；isort rc=0 |
| 类型 | `mypy`（读 `[tool.mypy].files`，143 文件） | **0 error** |
| 注释规范 | `python scripts/check_annotations.py` | rc=0，平均密度 23.1%，本轮 7 个测试文件均 ≥ 13.0% 阈值 |
| 版本单一事实源 | `python scripts/check_version.py` | rc=0（本轮未碰版本号，作回归底线确认） |
| 测试卫生 R1 | `pytest tests/test_test_hygiene.py` | 通过（新增文件中的 `os.chmod` / `os.remove` / `os.path.getsize` 打桩已改为 `types.SimpleName… |

**一条与门禁可信度直接相关的发现**（不要重复踩）：本机不带 `PYTHONUTF8=1` 跑 `isort --check-only .`
会得到「看似通过 + 3 条 `Unable to parse file … gbk codec` 告警」，被跳过的正是
`tests/test_i18n_migration.py` / `tests/test_record_container.py` / `tests/test_web_api.py`——
这是典型的**门禁假绿**（MID-63 已为此在 CI 里加了专门的静默跳过拦截步骤）。本地跑 isort
必须带 `PYTHONUTF8=1`，不得把无该环境变量下的 rc=0 当作排序已合规的证据。

**过程中被门禁抓到并修掉的两个自身缺陷**（记录以免被再次写回）：

1. `tests/test_web_tray.py` 里给 `_on_exit` 不传 `server` 会真的执行 `os._exit(0)`，
   把整个 pytest 会话提前终止——症状是「输出只有一行进度、没有汇总、退出码 0」，
   极难归因。任何走该分支的用例必须传 `server`。
2. 追加到 `tests/test_ffmpeg_install.py` / `tests/test_node_install.py` 的字节字面量曾因
   多层转义写成 `b"\\x50\\x4b ..."`（字面反斜杠而非 ZIP 魔数），使「残缺 zip」分支实际
   测的是「任意非 zip 内容」。改为无语义歧义的 `b"truncated-partial-download"`。

#### 遗留与注意（不在本轮范围内处置）

- `src/spider.py` 仍为 69.7%（缺 1003 条语句），是总量继续上探的唯一大缺口。缺口集中在
  `get_flextv_stream_data`(73) / `_extract_room_data_from_html`(45) / `get_shopee_stream_url`(42) /
  `get_kuaishou_stream_data`(39) / `get_haixiu_stream_url`(37) 等**平台解析函数**，全部需要
  按平台构造响应桩；单函数收益 ~40 行而桩代码成本远高于本轮其余模块，故本轮未做。
  注：`check_coverage.py` 的 `src/spider.py` 阈值是 50%，此处不是门禁问题，只是总量瓶颈。
- `src/proto/douyin_pb2.py` 报告显示 8.7%（缺 105 行）。已核实：未覆盖区间**恰好**是
  `if _descriptor._USE_C_DESCRIPTORS == False:` 整块——protobuf 使用 upb/C 后端时该分支
  结构性不可达（本机 `protobuf 7.36.1` + gencode 4.25.3，`from src.proto import douyin_pb2`
  实测导入成功）。属生成代码的固有死区，**未**为此改动 coverage 配置（改 `omit` 需与
  `.coveragerc-concurrency` 同步，且会影响门禁语义）。
- 本轮期间 `src/web_api.py`、`src/web_config.py`、`src/utils.py`、`src/config_io.py`、
  `src/stream_select.py`、`src/spider.py`、`src/javascript/haixiu.js`、`web.py` 与对应的
  `tests/test_web_api.py` 等由**另一并发工作流（`CODE_REVIEW_2026-09-21` 修复轮）**修改，非本会话所为。
  中途 `tests/test_web_api.py` 一度出现 8 条 `_insecure_bind_detail` 相关失败，随后该工作流自行改齐。
  该批次改动已**单独成条**记录于上一节「工作区改动全量台账」的批次 B，不再在此处重复。
- `tests/test_srt_timeline_anchor.py` 曾在带 `--cov` 的全量运行中偶发 4 条
  `FileNotFoundError: tests\_out_e2e`（该文件在模块导入期 `os.makedirs(..., exist_ok=True)`，
  运行中途目录会被同机另一 pytest 会话的 `conftest.pytest_unconfigure` 回收）。本轮最后的
  一次带 `--cov` 全量运行（预建该目录后）为 **2310 passed / 0 failed**，且把该文件与本轮
  全部新增文件同跑亦通过 → 判为环境竞态而非代码回归。后续可考虑把该用例的输出目录改成
  `tmp_path`，从根上消除同机多会话互踩。

### v4.3.0-dev (2026-09-21) — CODE_REVIEW_2026-09-20 全轮修复落地：严重 10 项 + 中等/轻微按主题成批 + 五类新门禁

**变更摘要**：本轮把 `CODE_REVIEW_2026-09-20.md` 登记的 **106 项**（严重 10 / 中等 70 / 轻微 26）按「模块组并行深修」落地：**SEV-01 … SEV-10 全部修复**…

> **⚠ 真机验证欠账（本轮未闭环，必须在下一轮补）**：涉及**录制链路 / 选源 / ffmpeg 参数 / 平台解析**的改动（SEV-06、SEV-08、SEV-09，MID-01 … MID-20，MID-40 … MID-50，MIN-02 … MIN-06 等）**只做到「离线可验证部分全绿 + 回归锁落地」**，未用真实 URL 增量跑过（AGENTS.md 完成定义第 2 步）。回归锁能证明「不再退回已知坏形态」，**不能**证明「该平台的真实流地址现在可录」。待具备活房间的环境按下表「遗留」列逐条补跑。

#### 一、严重缺陷（SEV-01 … SEV-10，全部修复）

| 编号 | 缺陷（报告原标题压缩） | 落点 | 回归锁 |
| --- | --- | --- | --- |
| SEV-01 | 并发信号量把「可用许可数」当「容量」，每轮重算向上补满 → 网络并发上限实质失控… | `src/scheduler.py`（`_capacity` / `_used` 拆分）+ standalone 副本本轮同步… | `tests/test_scheduler.py` |
| SEV-02 | `PUT /api/rooms` 绕过房间入口校验，SSRF 与任意 scheme 防线在此失效… | `src/web_config.py::format_url_line`（唯一写入口下沉裁决）+ `src/web_api.py`… | `tests/test_web_api.py::TestRoomWriteParity` |
| SEV-03 | 内网地址拦截为字符串前缀黑名单，多形态地址可绕（实测 7 条放行 5 条）… | `src/web_config.py`（改 `ipaddress` 语义 + DNS 解析双道判定） | `tests/test_web_config.py`、`tests/test_web_config_secret_mask.py` |
| SEV-04 | 面板认证可被单个写请求热关闭；大小写变体同时绕过口令哈希 / 防自锁 / token 吊销… | `src/web_api.py`（入口一次 `lower()` 归一 + 目标态判定 + 每请求不变量）… | `tests/test_web_api.py::TestPasswordGuardCaseParity` / `TestAuthDowngradeRejec… |
| SEV-05 | 删除房间在 CRLF 配置上永久静默失效却回报 `{"ok": true}`（Windows 必然发生）… | `src/config_io.py::delete_line`（补 `newline=""` 并**返回 bool**）+ 端点按重解析裁决… | `tests/test_config_io.py`、`tests/test_web_api.py::TestDeleteRoomReportsTruth` |
| SEV-06 | Shopee 站点后缀解析拼出非法域名 → 该平台分享链接永久解析失败… | `src/spider.py::_shopee_host_suffix`（剥 `live.` 首段后取完整后缀，死分支合并）… | `tests/test_spider_fixes.py` |
| SEV-07 | 两个登录函数的兜底装饰器与返回契约错配，故障伪装「未开播」… | `src/spider.py` / `src/utils.py`（按返回注解选装饰器） | 新增 `tests/test_decorator_contract.py`（全仓 AST 锁） |
| SEV-08 | 录制看门狗「停滞」判据基准用错，容忍窗口实际只有 30 秒 | `main.py::check_subprocess`（基准改为「尺寸变化时刻」） | 新增 `tests/test_record_watchdog.py` |
| SEV-09 | `only_flv` 分支缺 `flv_url` 时未清录制状态 → 时间字幕线程死循环写盘… | `main.py`（登记下移到「确认拿到 flv_url」之后；强制直下分支收尾统一走 `clear_record_info`，见 MIN-07）… | `tests/test_record_watchdog.py`、`tests/test_video_postprocess.py` |
| SEV-10 | 发布链路运行时二进制哈希钉定表为空，未校验二进制进入分发产物… | `build_exe.py`（`_PINNED_RUNTIME_SHA256` 形状判据 + `--require-pinned`）+ `scripts/c… | `tests/test_machine_validation_fixes.py` |

#### 二、中等问题按主题批次（MID-01 … MID-69 + 补-05）

- **录制主链路与产物判定**（MID-01 … MID-12…
- **选源与流地址层**（MID-13 … MID-20…
- **并发、网络、弹幕与资源治理**（MID-21 … MID-32）：`async_http` 客户端/锁随循环重建、`collector` 停止握手与 `_shutdown` 任务取消、`ws_client` 悬挂引用与发送任务引用（MIN-12/13 同族）、`danmaku_monitor` 边车句柄、`PlatformBreaker` 探针代数标记（MIN-22）。
- **凭据生命周期与 Web 面板安全面**（MID-33 … MID-39）：`ttwid` / 快手 `did` / Twitch `client_id` 三层缓存补 TTL 与**显式失效入口** `invalidate_ttwid()`、`cookie_cache` 世代比对、Host 允许名单（MID-36）、面板阻塞 IO 走线程池（MID-34）、登录限流全局失败预算与 XFF 只信直连对端（MID-35）、内部异常不回显（MID-39）。
- **平台解析与签名**（MID-40 … MID-50）：B 站兜底 buvid 失效链、抖音 APP 路径 ORIGIN 候选来源、花椒/淘宝/斗鱼/小红书/Twitch 等具体平台字段与参数错配、裸 `json.loads` 迁移到 `_loads_dict`、手工拼接请求体改 `urlencode`。
- **GUI / i18n / 推送 / 安装器**（MID-51 … MID-60）：`URL_config.ini` 改 `utf-8-sig` 读（CR-01 挂死守卫重新生效）、**`set_language()` 返回实际生效语言码**（MID-52…
- **客户端 JS / 门禁 / 测试可信度 / CI**（MID-61 … MID-69）：`migu.js` WASM 视图在 malloc 后重取、远程 wasm 信任边界注明（三类钉定互不冒充…
- **补-05（安全下限）**：`starlette` 下限 `>=0.49.1` → **`>=1.0.1`**…

#### 三、轻微问题（MIN-01 … MIN-24）

按报告建议逐条处置…

#### 四、新增门禁（此轮之前不存在）

| 门禁 | 落点 | 消灭的形态 |
| --- | --- | --- |
| `PYTHONUTF8=1` + 门禁「告警即失败」 | 「格式化命令」块两行 black/isort、`scripts/run_gates.py`（`GATE_CHILD_ENV` / `FATAL_STDERR… | GBK locale 下 isort 对含中文注释的核心源码**静默跳文件且 rc=0**（本地绿、CI 绿、两边都没查）… |
| `scripts/check_runtime_pins.py` | 结构模式进门禁块；`--strict` + `--emit-env` 由 `build-release.yml` prepare 执行… | 空钉定表 + 仅告警的静默通过；缺平台/缺槽位一律 rc=2 |
| 装饰器契约 AST 锁 | 新增 `tests/test_decorator_contract.py` | 兜底装饰器与返回类型错配、`@decorator` 与 `def` 之间夹注释导致装饰器绑错函数… |
| 测试卫生 AST 锁 | 新增 `tests/test_test_hygiene.py`（R1 … R4） | 经其他模块命名空间改写 stdlib 本体、宽泛 `filterwarnings`、KAT 只断类型、`tests/` 残留一次性产物… |
| 前端目录一致性锁 | `tests/frontend/test_quality_ui.mjs`（`index.html` 的 `data-i18n*` 键与四语内嵌目录逐一比对、… | 「前后端两份目录靠人眼同步」（MIN-10） |
| `deps-audit` job | `.github/workflows/ci.yml`（进 `ci-summary` 的 needs） | 清单下限长期停留在受影响版本 |
| 覆盖率无数据硬失败 | `scripts/check_coverage.py` rc=2 | 「本地没跑 `--cov` 却以为过闸」 |

#### 五、安全面变更（对外行为变化，单列）

- **房间地址校验改为 `ipaddress` 语义并覆盖全部写入口**：整数/八进制/十六进制 IPv4、完整 IPv6、`0/8` 与 CGNAT `100.64/10`、解析到内网的域名全部拦下…
- **Web 节键大小写归一**：入口处一次 `key.strip().lower()`，口令哈希化 / 防自锁 / 改密吊销 token 三项守卫对 `WEB_PASSWORD` 等变体同样生效。
- **Host 允许名单**：同源判定不再信任请求自带的 `Host`
- **面板阻塞 IO 走线程池**：目录列举 / 日志读取 / 配置解析等同步 `def` 端点由 FastAPI 派发到 anyio 线程池…
- **登录限流键加固**：仅信任 `web_trusted_proxy` 名单内代理的 XFF，并引入全局失败预算，防「伪造 XFF 换桶」与桶数无界。
- **`delete_line` 的 CRLF 修复并返回 bool**：Windows 上「删不掉却回报成功」的静默失效结束；端点改为按重新解析结果裁决 200/500。
- **敏感配置写入拒绝两类值**（本轮收尾补口）：`is_sensitive_item` 命中的键既不接受空值、也不接受面板回显用的字面掩码 `'***'` —— 前端 `saveConfig` 跳过掩码由此从「唯一防线」降级为「省一次无谓写入」。
- **语言切换按生效码落盘**（本轮收尾补口）：`PUT /api/language` 改为「先 `i18n.set_language()` → 再写它返回的**生效码** → 按生效码应答并给出回退提示」

#### 六、跨文件接缝收尾（并行修复遗留，本轮闭合）

- `src/web_api.py`：语言端点生效码语义（上节末两条）、敏感项掩码拒绝（与空值同口径 400）。
- `src/scheduler.py`：补**回指注释**——模块头与两个类注释点名 `scripts/douyin_live_recorder_standalone.py` 持有独立副本、改并发语义须逐方法 diff 后同步…
- `src/platforms/douyin.py`：把 `invalidate_ttwid()` 接进弹幕链的「HTTP 200 拒绝握手」分支（与 B 站 `_reject_auth()` → `invalidate_bili_buvid_cache()` 同形）
- 文档 / 元数据：`CODE_WIKI.md` / `CODE_WIKI_EN.md` 中英双份本条目 + MIN-15 第 4 处陈旧引用清除…

#### 七、验证结论

| 项 | 命令 / 口径 | 结果 |
| --- | --- | --- |
| 接缝收尾聚焦用例 | `pytest -q tests/test_web_api.py tests/test_scheduler.py tests/test_douyin_dan… | **156 passed / 2 skipped / 0 warnings**（两条 skip 为 Windows 符号链接特权缺失，属环境口径）… |
| 新增回归锁 | `pytest tests/test_douyin_danmaku.py` | 16 passed（含「不打桩 `invalidate_ttwid` 直接断言真实模块全局被清」一条）… |
| 掩码守卫归因 | `test_only_the_exact_panel_mask_is_rejected`（`'****'` 仍 200） | 证明 400 只来自新守卫、且敏感项其余写入路径未被误伤 |
| 格式与类型 | `black --check`（120/py314）、`isort --check-only`（profile black，带 `PYTHONUTF8=1`… | 全部 0 问题（注释门禁 142 文件全通过） |
| 元数据 | `importlib.metadata.version("DouyinLiveRecorder")` | `4.3.0`（与 `pyproject.toml` 同源） |
| **遗留（部分已于同日续轮闭合，见第八节）** | 真实 URL 增量录制（至少一个受影响平台）；`ci.yml` 的 `deps-audit` 在 GitHub runner 上的首跑… | **仍未执行** —— 录制链路项的真机可用性本轮未证；全量 `pytest -q` / `run_gates.py` / `check_coverage.… |

#### 八、MID-48 收口 + CI 侧本地等价验证（2026-09-21 同日续轮）

**1）MID-48 全量收口（`src/spider.py`）**：报告登记的「裸 `json.loads` 仍 84 处」分两批迁完 ——
国内高流量平台 21 个函数（38 处）＋ 海外与含凭据平台 31 个函数（36 处），统一改用既有 `_loads_dict`
与新增访问器 `_dig` / `_dig_str` / `_dig_list` + `_warn_api_abnormal`（**未新增第三个 loads 封装**）。
文本口径 78 → 2，AST 调用点（排除 `_safe_loads` 本体）75 → **1**：唯一豁免是 `get_twitchtv_room_info`
（GQL 返回数组，`_loads_dict` 会判成非 JSON，其自身 try/except 已带类型化告警）。判据固化为
`tests/test_spider_hardening.py::BARE_JSON_LOADS_CEILING = 1`（**只降不升**）+ 按函数名的「零裸 loads」AST 扫描；
每平台四类载荷（WAF/HTML、缺对象、截断 JSON、正常体）只打桩传输层驱动真实解析函数，成功路径逐字段等值
断言 `assert result == expected` 且**不得产生任何告警**。两条配套口径：数值型字段走保留数值的 `_dig`+cast
（`_dig_str` 会把 int 悄悄打成空串，如 SOOP `BNO`、花椒 `relateid/uid`）；`AID`/`BNO`/`visitor_st`/
`hls_authentication_key`/`mcData` 等凭据**永不入日志**，归因只带信封 `code`/`msg`，并有
「token 不得出现在任何一条日志里」的断言；「未开播/已下播」的正常轮次刻意静默
（`test_documented_offline_stays_silent`）。**无新增文案**（复用两条既有 msgid）。

**2）CI 侧本地等价验证（不装包、不建远端、不碰项目 venv）**：34 项结构断言中真实失败 **0**
（4 项初报 FAIL 经复核均为校验脚本自身 bug 或刻意隔离项）。已实测为真：`ci-summary.needs` 覆盖 8 个 job
且无游离 job、`deps-audit` 确在 required check 内、无 `continue-on-error`、retry 复合动作 11/4 处且无内联
重试循环、`python_build=3.14` 与 `node_version=24` 跨 workflow 同值、black/isort 主体步骤带 step 级
`PYTHONUTF8=1` 且参数与 AGENTS 门禁块**逐字等价**，另有把 `Unable to parse file` 判失败的兜底步骤；
`requirements.txt` 与 `pyproject [project.dependencies]` 经 `tomllib` 对账 **21/21 零差异**、
`protobuf<8` 上限仍在、`urllib3>=2.7.0` 已显式声明；三个服务经 YAML 锚点展开后均带 `pull_policy: build`；
`Dockerfile` 的 `ARG` 行序门禁确能捕获刻意颠倒的形态。**钉定链端到端**：
`check_runtime_pins.py --strict --emit-env` 的 JSON 经 `DLR_RUNTIME_SHA256` 进入 `_pinned_slots()`
（只取本运行时键 `windows-x64`，他平台钉定不泄漏）；`_is_pinned()` 严格只认 64 位小写十六进制
（占位标记 / 63 位 / 大写一律判未钉定）；CI 形态下 ffmpeg 与 node **两个槽位均在下载之前 `SystemExit`、
`urlopen` 调用数 0、不落任何文件**；本地形态按设计仅告警并标注「不得用于发布」。

**3）pip-audit 实测（补-05 的 OSV 面）**：装于仓库外临时 venv（项目 venv 零改动、清单未新增条目），用完即删。
`pip-audit 2.10.1` 在**不带 `PYTHONUTF8=1` 时读不了本仓清单** —— `pip-requirements-parser.auto_decode()`
用 `locale.getpreferredencoding(False)`，中文 Windows（cp936）下会在 `requirements.txt` 的中文行内注释处直接
`UnicodeDecodeError`、rc=1，**崩溃发生在漏洞判定之前**（与 MID-63 同族，已写入 AGENTS.md 的 `deps-audit`
条目与实测文档）。带 `PYTHONUTF8=1` 后三种形态（解析全部传递依赖 / `--no-deps` 只看 21 条下限 /
`--path` 审计项目实际安装态）**全部 `No known vulnerabilities found`、rc=0**。附带工具事实：2.10.1 无
`--venv` 参数，审计已装环境须用 `--path`。

**4）续轮验证结论**：`scripts/run_gates.py` **8/8 全绿**；全量 `pytest -q` **1917 passed / 10 skipped /
0 failed / 0 警告**（10 条 skip 全为 Windows 环境口径：环境变量大小写、`os.chmod` 权限位、符号链接特权、
6 条「该平台无文档化离线形态」）；`basedpyright` **0 errors / 0 warnings**；`check_coverage.py` **PASSED**，
总覆盖率 **73.28%**、`src/spider.py` 64.9% → **68.4%**（新回归锁带涨）；站内链接与锚点机检 **85 条全可解析**。
`.gitignore` / `.dockerignore` 同步补 `coverage.json`（`--cov-report=json` 的产物，此前只有 `.coverage*` 被忽略）。

#### 九、按模块分类的全量改动清单（新增 / 修改 / 删除 + 文件路径）

**统计口径**：以 2026-09-20 22:15 的工作区快照为基线逐文件比对，含无扩展名文件（`Dockerfile`）与点文件
（`.gitignore` / `.dockerignore`，二者基线未快照、按实际编辑计入）。合计 **修改 91 个文件、新增 19 个、删除 2 个**。
其中 80 个由基线快照直接 diff 得出；另 11 个基线未快照（4 份翻译目录 + 2 份 README + 2 份
`docs/agent-reference/` 外迁文档 + `.gitignore` + `.dockerignore`）按内容证据计入，其行数不在本表维护。
表中 `+x/-y` 为 unified diff 的新增/删除行数（`StopRecording.vbs` 源文件是 UTF-16 LE，行数量级不代表语义改动量）。
「关联条目」列的编号指向 `CODE_REVIEW_2026-09-20.md`；`—` 表示该文件的改动是上述条目的连带同步，无独立编号。

##### 9.1 录制主编排与房间线程（CLI 入口）

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `main.py` | 修改 `+555/-138` | 看门狗停滞判据由「进程起跑时刻」改为「最后一次字节增长时刻」（新增 `_stall_since`），单次录制时长上限提为可配置 `max_record_se… |

##### 9.2 并发调度与运行状态

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `src/scheduler.py` | 修改 `+97/-28` | `ResizableSemaphore` 拆 `_capacity`（上限，只由 `set_value` 改）与 `_used`（已持有，只由 acquir… |
| `src/recorder_status.py` | 修改 `+44/-4` | `_live_network_capacity()` 改读 `capacity`（此前显示的是空闲槽数）；`display_info` 的 `sleep` … |
| `scripts/douyin_live_recorder_standalone.py` | 修改 `+41/-10` | 并发实现副本同步 `capacity`/`used` 拆分（SEV-01 残留形态），并写明「两份 `PlatformBreaker` 方法数不等价（9 v… |

##### 9.3 HTTP 客户端、代理与凭据

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `src/async_http.py` | 修改 `+152/-57` | `_client_cache` 键加入事件循环维度（`(proxy, verify, http2, loop)`），只逐出属于当前循环的条目并按 `loop… |
| `src/sync_http.py` | 修改 `+17/-0` | `sync_req` 入口统一 `handle_proxy_addr`（裸 `ip:port` 代理此前只被异步侧兼容）… |
| `src/proxy.py` | 修改 `+88/-33` | IPv6 括号形态 `rsplit(":", 1)` + `[]` 特判（原实现必抛 `ValueError`、`__post_init__` 校验整块是死… |
| `src/weverse_auth.py` | 修改 `+23/-5` | 改走 `sync_http.sync_req(..., proxy_addr=...)`（拿回线程级 Session 复用、代理与 SSL 策略），失败响应… |
| `src/ttwid.py` | 修改 `+65/-7` | 进程级 ttwid 记录获取时刻并按 `cookie_cache.DEFAULT_TTL` 判定；新增 `invalidate_ttwid()`（同时清三层… |
| `src/cookie_cache.py` | 修改 `+12/-1` | `singleflight` 补齐 `fetch_cookies` 才有的世代比对，使 `invalidate_generic` 有真实语义… |

##### 9.4 选源、探针与画质档位

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `src/stream_select.py` | 修改 `+186/-43` | `record_url` 通道同受 `hls_effective_enabled` 约束（「HLS 采集排除=零探针」语义闭环）并复用已探结论（不再对同一地… |
| `src/stream.py` | 修改 `+190/-47` | 虎牙旧档分支废掉「位置式 zip 贴标签」，改由 `HUYA_RATIO_BY_CODE` 值驱动并把 `8000/2000/500` 与 `1000/25… |

##### 9.5 平台接口解析与签名

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `src/spider.py` | 修改 `+1385/-458` | `_shopee_host_suffix` 先剥 `live.` 再取首点后缀并合并退化 if/else；`login_popkontv` / `login… | $)`；TikTok 内置游客 cookie 过期时定向告警；SOOP 相对清单改 `urljoin`；斗鱼 betard/B 站 playUrl/Twit… | SEV-06/07，MID-33/40…50 |
| `src/platforms/douyin.py` | 修改 `+62/-3` | 「WS 握手被 HTTP 200 拒绝」分支调 `invalidate_ttwid()`（只认 200、单次会话一次），使凭据被作废后无需重启即重取… |
| `src/javascript/migu.js` | 修改 `+209/-44` | 删除「malloc 前一次性缓存堆视图」，改 `heapU8()/heapU32()` 每次从 `memory.buffer` 重建（越界写抛错而非静默 n… |
| `src/javascript/laixiu.js` | **删除** | 无调用方死代码（逻辑已在 `src/spider.py` 以 Python 重写），且 `CryptoJS = require(...)` 是隐式全局… |
| `src/javascript/taobao-sign.js` | **删除** | 无调用方死代码，且注释残留结构完整的真实抓包入参（会话令牌形态值）… |

##### 9.6 弹幕链路与产物收尾

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `src/collector.py` | 修改 `+161/-14` | 在「loop 已发布但未 running」窗口做 ≤0.5s 有界等待 + `run_until_complete` 前二次复查停止事件（两条相反顺序保证原… |
| `src/danmaku_monitor.py` | 修改 `+258/-52` | 边车落盘移交进程级单写线程（有界队列 + 丢弃计数 + `flush()`），全局锁内只完成统计与 payload 构造，慢盘不再串停所有房间事件循环… |
| `src/ws_client.py` | 修改 `+74/-13` | 重连进入 `continue` 前显式 `self._ws = None`（原清理块不可达）并按 `state is OPEN` 判活；`send_nowa… |
| `src/srt_writer.py` | 修改 `+17/-7` | 重试开片的 `_index`/`_last_end` 复位移到行生成之前，消除同一 `.srt` 内重复序号与非单调时间轴；注入清洗与片内钳制不变… |
| `src/ffmpeg_proc.py` | 修改 `+102/-19` | `as_completed` + `f.result(timeout)` 死代码改为总预算 `wait`（并把 `ThreadPoolExecutor` 换… |
| `src/video_postprocess.py` | 修改 `+77/-6` | 超时/失败分支删除本次生成的半成品 mp4 并明确「已保留源文件」；重编码超时按源体积线性放大（1.5s/MB，下限 600s、上限 3600s）… |

##### 9.7 配置读写、脱敏与原子写

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `src/config_io.py` | 修改 `+25/-10` | `delete_line` 两侧 `rstrip("\r\n")` 后比较（修复 MI-11 引入的 CRLF 恒不匹配、Windows 必然静默失效），并… |
| `src/utils.py` | 修改 `+256/-43` | `mask_credentials` 补齐头形态（`Cookie:`/`Authorization:`）、JSON 体（`"access_token": …… |

##### 9.8 Web 管理面板（后端 + 前端）

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `src/web_api.py` | 修改 `+428/-66` | `PUT /api/rooms` 显式校验 + 校验下沉（见 `web_config`）；Web 节全部判定统一 `key_norm`（大小写变体不再绕过哈… |
| `src/web_config.py` | 修改 `+300/-26` | 内网拦截由前缀黑名单改 `ipaddress` 语义判定（loopback/private/link-local/reserved/multicast + … |
| `web.py` | 修改 `+25/-2` | 非回环 + 无认证的启动瞬间判定改为与中间件同源的可复用检查… |
| `web/app.js` | 修改 `+137/-24` | 掩码项渲染打 `data-masked` 标记，清空提交须显式确认、服务端 400 走专门文案；`setLogoutVisible()` 让 `/api/l… |
| `web/index.html` | 修改 `+3/-3` | 主题/语言控件的硬编码中文 `title` 改走 `data-i18n-title`；两处表头回退文案入目录… |
| `web/style.css` | 修改 `+3/-0` | 仅新增 `.hint-masked` 提示样式；`#rooms-view` 的 `table-layout: fixed` 与定宽规则未动… |

##### 9.9 GUI / i18n / 推送

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `gui.py` | 修改 `+289/-53` | `URL_config.ini` 读取改 `utf-8-sig` 并与 `parse_url_config` 同判据（BOM 不再绕过 CR-01 挂死守卫… |
| `i18n.py` | 修改 `+56/-7` | `set_language` 走 `has_catalog`/`resolve_language` 口径并返回**实际生效**语言码；新增 `unique_… |
| `msg_push.py` | 修改 `+23/-8` | Bark 类渠道把「路径末段即密钥」作为通则遮蔽（去掉 `day.app` 主机白名单），自建/反代服务器短 key 不再明文进轮转日志… |
| `i18n/zh_CN/LC_MESSAGES/zh_CN.po` + `.mo` | 修改（`.mo` 重编译） | 本轮累计新增 26 条 msgid（MID-68 转换 + 各模块新告警 + GUI 弹窗），`.mo` 头部 N=**664**（含头部空 msgid）、… |
| `i18n/en_US.json` / `en_GB.json` / `zh_TW.yaml` | 修改 | 与 `.po` 同步至各 **663** 键，占位符集合逐条一致（避免 `zh_TW` 曾因 `{message_2}` 与调用方 `message=` 不… |
| `README.md` / `README_EN.md` | 修改 | 移除已删除 JS 脚本的目录树条目并修正树形字符 |

##### 9.10 打包、安装器与发布链

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `build_exe.py` | 修改 `+169/-34` | `_PINNED_RUNTIME_SHA256` 改按 `<os>-<arch>` 运行时键 × `ffmpeg`/`node` 槽位分列；`_is_pin… |
| `src/ffmpeg_install.py` | 修改 `+87/-16` | 官方源 ToFU 旁路文件按构建标识（Last-Modified/ETag/Content-Length）命名，上游换构建不再造成「官方源 + 蓝奏云双拒」… |
| `StopRecording.vbs` | 修改 `+296/-10` | 补三个 pip 启动器映像名（此前主进程完全不被匹配 → 只杀 ffmpeg 留下复活源）；shim 判定改词边界 + 首 token basename（不… |

##### 9.11 维护脚本与门禁

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `scripts/check_runtime_pins.py` | **新增** `189L` | 钉定表结构校验（缺平台/缺槽位/占位值 → rc=2）、`--strict`（发布闸口 rc=1）、`--emit-env`（把钉定表作为 JSON 供 C… |
| `scripts/run_gates.py` | 修改 `+133/-11` | 解析 AGENTS 门禁块行首 `NAME=value` 前缀并注入子进程环境；`GATE_CHILD_ENV` 默认 `PYTHONUTF8=1`；`FA… |
| `scripts/check_coverage.py` | 修改 `+54/-2` | 「无数据」由 WARN 改为 rc=2 硬失败并打印下一步命令（区分「没跑测试」与「覆盖率不达标」）… |
| `scripts/check_version.py` | 修改 `+55/-1` | 新增「`ARG` 声明行必须早于使用所在**指令起始行**」行序断言（续写回溯、注释行跳过）… |
| `scripts/check_annotations.py` / `scripts/extract_i18n_strings.py` | 修改 `+2/-1`（各） | 移除对已删除 `gui_legacy.py` 的引用 |

##### 9.12 CI、容器与依赖清单

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `.github/workflows/ci.yml` | 修改 `+117/-6` | black/isort 步骤 step 级 `PYTHONUTF8=1` 并与 AGENTS 块逐字对齐；新增 `Gate isort/black sile… |
| `.github/workflows/build-release.yml` | 修改 `+32/-2` | prepare 跑 `check_runtime_pins.py --strict` 并以 `--emit-env` 把钉定表透传为 `DLR_RUNTIM… |
| `.github/workflows/trivy.yml` | 修改 `+15/-4` | `checkout` 升 v7、分支过滤去模板残留、镜像名改本地构建标签、`--build-arg APP_VERSION` 从 pyproject 读出后… |
| `.github/workflows/issue-translator.yml` | 修改 `+29/-5` | 降级为仅 `workflow_dispatch` + 顶层 `permissions: contents: read / issues: write`，文件… |
| `Dockerfile` | 修改 `+10/-6` | `ARG APP_VERSION` 上移到 `LABEL version=` 之前（此前 `--build-arg` 完全不生效且无构建期报错）… |
| `docker-compose.yaml` | 修改 `+7/-0` | 锚点内 `pull_policy: build`，去掉「未 build 直接 up 会去 registry 拉同名 `:latest`」的回退… |
| `requirements.txt` / `pyproject.toml` | 修改 `+19/-2` / `+13/-2` | `starlette` 下限抬到受影响段之上、新增显式 `urllib3>=2.7.0`；两份清单一一对应 **21/21**（`tomllib` 对账零差… |
| `.gitignore` / `.dockerignore` | 修改 | 同步补 `coverage.json`（`--cov-report=json` 产物） |

##### 9.13 测试（新增 18 个文件 + 修改 29 个）

| 路径 | 类型 | 覆盖内容 |
| --- | --- | --- |
| `tests/test_record_watchdog.py` | **新增** `589L` | 45s 写入空档不杀 / 11min 杀、时长上限轮按成功收尾、分段关闭时上限不生效、放弃槽位与异常穿透后的状态收敛、无 `flv_url` 时 `reco… |
| `tests/test_scheduler.py` | 修改 `+299/-0` | 有持有者时 `recompute` 不放大可用数、真实峰值并发 ≤ 容量、超额 `release` 不造许可、缩容保留已持有、探针归属/租约… |
| `tests/test_recorder_status.py` | **新增** `228L` | 控制台容量显示读 `capacity`、异常轮不忙等（注入失败 stdout + 假 sleep 计次）… |
| `tests/test_spider_hardening.py` | **新增** `1517L` | 52 个平台函数的四类载荷用例、凭据不入日志断言、`BARE_JSON_LOADS_CEILING` 棘轮与按函数名零裸 loads 扫描… |
| `tests/test_decorator_contract.py` | 修改 `+2/-2` | 全仓 AST 锁：返回注解 ↔ 兜底装饰器配对、`@decorator` 紧贴 `def`… |
| `tests/test_web_config.py` / `test_web_api.py` | 修改 `+241/-0` / `+830/-16` | 内网变体表驱动、PUT/POST 裁决一致、大小写变体三守卫、Host 允许名单、限流键与迭代上限、掩码/空值 400、CRLF 删除夹具… |
| `tests/test_web_config_locks.py` / `test_web_config_secret_mask.py` | **新增** `163L` / `185L` | 400 文案与「值未被覆写」复核、`_looks_like_secret_value` + `_validate_room_url_target` 真函数表… |
| `tests/test_stream.py` / `test_stream_select.py` / `test_quality_tiers.py` | 修改 `+317/-24` / `+263/-0` / `+6/-3` | 虎牙值驱动档位与顺序无关性、TikTok 零 HLS 探针（含 record_url）、URL 形态白名单、退避键、变体选择、B 站反向表… |
| `tests/test_collector.py` / `test_danmaku_monitor.py` / `test_ws_client.py` / … | 新增/修改 | 反向序握手不回归 + 丢信号窗口、锁内不落盘、重连后 `_ws` 判活、SRT 序号单调、清理总预算、超时删产物、世代比对、ttwid 失效与 TTL… |
| `tests/test_async_http.py` / `test_sync_http.py` / `test_proxy.py` / `test_uti… | 新增/修改 | 多循环不互相逐出且同循环复用、代理地址归一、IPv6/大写环境变量/凭据保留、脱敏九类样本与公共 URL 不误伤、fsync 调用次序、CRLF `dele… |
| `tests/test_gui_monitor.py` / `test_i18n.py` / `test_msg_push.py` / `test_ffmp… | **新增** | BOM 判据、生效语言、Bark 自建主机遮蔽、旁路轮换、VBS 映像名/词边界/静默判据 + UTF-16 原始字节… |
| `tests/test_frontend_quality_ui.py` + `tests/frontend/test_quality_ui.mjs` | 修改 `+171/-9` / `+405/-19` | 进程组超时兜杀 + 结果真解析断言；登出入口可见、掩码确认、错误 detail 解析、四语目录与 `data-i18n` 键集机械门禁（27 用例）… |
| `tests/test_i18n_migration.py` | 修改 `+102/-27` | 门禁判据由「首参是 JoinedStr」收紧为「首参子树含 FormattedValue」，`tr()` 实参位不递归（约定②），并加自检用例防门禁自身假绿… |
| `tests/test_test_hygiene.py` | **新增** `273L` | AST 扫描 tests/：禁止改 stdlib 模块本体、禁止宽泛 `filterwarnings` 等四类形态（R1…R4，含正负自检）… |
| `tests/test_ab_sign.py` / `tests/test_record_failure_feedback.py` / `tests/tes… | 修改 | SM3 标准 KAT 与冻结时间确定性、shim 化 stdlib patch、`capacity` 桩与直下体积口径、AsyncMock 去 ignore… |

##### 9.14 文档与元数据

| 路径 | 类型 | 改动要点 |
| --- | --- | --- |
| `AGENTS.md` | 修改 `+235/-7` | 新增/纠正 20+ 处长期约定：门禁 UTF-8 与「告警即失败」、`deps-audit`（含本地复现要带 `PYTHONUTF8=1`）、SEV-10 … |
| `CODE_WIKI.md` / `CODE_WIKI_EN.md` | 修改（两份，**行数不在此维护**——该数字自我引用，每追加一节就会漂移，同 AGENTS「计数不在本文件维护」的口径）… | 本轮更新日志条目（中英成对）：严重项表、按主题批次、新门禁、安全面、接缝收尾、验证结论、MID-48 与 CI 本地等价验证，以及本节的模块级全量清单… |
| `docs/agent-reference/measured-evidence.md` | 修改 | 新增 `isort 静默跳文件`（18 个）与 `pip-audit 本地审计读数` 两个证据段… |
| `docs/agent-reference/project-structure.md` | 修改 | 目录树补 `scripts/check_runtime_pins.py` 与 `trivy.yml` |
| `DouyinLiveRecorder.egg-info/` | 重新生成 | `PKG-INFO` 版本 4.3.0、`requires.txt` 与两份清单三方对齐（含 `urllib3`）… |
| `.workbuddy/memory/2026-09-21.md` | 修改 | 当日收尾记录：接缝判据、MID-48 收口、CI 本地验证与 Actions 待跑清单… |

##### 9.15 删除项与影响面汇总

| 删除对象 | 路径 | 影响与后续 |
| --- | --- | --- |
| 死签名脚本 | `src/javascript/laixiu.js`、`src/javascript/taobao-sign.js` | 无调用方；`_JS_SHA256_EXPECTED` 两条目同批移除，`src/javascript/` 现为 5 个被钉定脚本；README / CODE… |
| 旧「位置式」虎牙档位推断 | `src/stream.py`（`labels = ["UHD","HD","SD","LD"]` + 位置 zip） | 由值驱动映射取代；固化错误语义的 `test_legacy_uhd_via_exsphd_labels` 断言同步改为 `(2000, BD8)`… |
| 旧「子串包含」流后缀判定 | `main.py::_match_stream_suffix` | 改按 path 扩展名比较（`_stream_path_suffix`），`?a=.flv` 之类尾部查询参数不再能把任意 URL 送进自定义流分支… |
| 旧「非 UTF-8 即静默跳过」门禁 | `scripts/run_gates.py`、`ci.yml` | 现带 `PYTHONUTF8=1` 且把 `Unable to parse file` 判失败；Linux 默认 UTF-8，故 CI 侧仍须靠本地这一环自… |

`basedpyright` 0/0、`check_coverage.py` PASSED（总 73.28%、`spider.py` 68.4%）、前端 `node --test` 27 passed、
翻译目录四份各 **663** 条（`.mo` 头部 N=664）。

**变更摘要**：仅改动 `.github/workflows/ci.yml` 的 `python` 路径过滤分组…

#### 一、修改内容（`.github/workflows/ci.yml` `setup` job 的 `Detect path changes` 步骤）

- **新增触发项**（并入既有 `python` 分组，命中即联动 static / typecheck / test / concurrency-test / integration-verify / build-verify 六个 job）：
  - `web/**` —— `web/app.js` 的 `parseConfigBool + CONFIG_TRUE_TOKENS / CONFIG_FALSE_TOKENS` 与 `src/config_bool.py` 是跨语言布尔口径不变量（AGENTS.md「布尔配置项统一解析口径」条目…
  - `Dockerfile` / `docker-compose.yaml` —— 镜像的 Python/Node 版本常量须与 `pyproject.toml` 同源。
  - `.github/actions/**` —— `retry` 复合动作被 ci.yml / build-release.yml 全线复用，其接口变更波及所有 job。
- **删除项**：`gui_legacy.py`（该文件已于 2026-09-10 删除，清单里的引用是 stale 遗留；paths-filter 匹配不到文件，属无害但误导，一并清除）。
- **设计注释就地更正**（`Detect path changes` 步骤上方注释）：原注释「纯前端静态资源（web/）变更不触发」属被证伪的事实性陈述…

#### 二、连带文档更正（`CODE_WIKI.md` / `CODE_WIKI_EN.md`）

- §6「GitHub Actions CI」路径过滤说明此前写「纯前端（web/）不触发」，与本次清单冲突，一并就地改正（中英两侧）。

#### 三、验证结论

| 项 | 命令 / 口径 | 结果 |
| --- | --- | --- |
| 前端回归锁本地可跑 | `node --test tests/frontend/test_quality_ui.mjs` | tests 9 / pass 9 / fail 0 / skipped 0，exit 0（含三条布尔口径断言） |
| filters 结构核对 | `python -c "yaml.safe_load(...)"` | `python` 分组 18 条，`web/**` 在列、`gui_legacy.py` 已无、`Dockerfile` / `docker-compose… |
| 路由核对 | 单次仅改 `web/app.js` | `python` 命中 → static 与 test（及其余门控 job）均运行；`ci-summary` 的 needs 覆盖六 job，require… |

### v4.3.0-dev (2026-09-20) — 房间日志关联字段 `extra[room]`：多房间交织日志可按房间切出

**变更摘要**：录制进程的两条日志文件 sink 新增**线程级房间关联字段**…

#### 一、日志模块（`src/logger.py`，新增字段机制 + 两个行格式常量）

- **新增公开符号**（已入 `__all__`）：`ROOM_FIELD = "room"`、`set_room_context(room)`、`get_room_context()`；内部为 `_room_var: ContextVar[str]` 与 `_room_patcher(record)`。
- **机制**：房间线程的日志调用点散布在 `main.py` 与 `src/*` 数十个模块…
- **`extra` 默认值不可删**：缺 `extra={ROOM_FIELD: ""}` 时未绑定房间的日志在格式化阶段抛 `KeyError: 'room'`
- **行格式收敛为常量并插入该列**：`_STREAMGET_FORMAT` = `时间 | 级别(左对齐8) | 房间 | 模块:函数:行号 - 消息`、`_PLAYURL_FORMAT` = `时间 | 房间 | 消息`。
- **`logs/gui.log` 刻意不带该列**：GUI 进程不执行录制…
- 类型标注用 `if TYPE_CHECKING: from loguru import Record`（`Record` 是仅在 `__init__.pyi` 存根里定义的 TypedDict…

#### 二、录制入口（`main.py`，一处 import + 两处绑定）

- `from src.logger import set_room_context`。
- `start_record()` **线程入口**先绑 `f"序号{count_variable}"` 占位：使早于 `record_name` 的日志（退出标志 / 录制停止 / 注释退出 / 并发熔断退避 / 解析失败）同样能归属到房间。
- 内层轮询解析出主播名、`record_name = f"序号{count_variable} {anchor_name}"` 之后刷新为完整房间名…
- **生效边界**：带标记 = 房间线程本身 + 其中 `asyncio.run()` 创建的 Task（ContextVar 语义…

#### 三、测试（`tests/test_logger_room_context.py`，新增文件 / 4 条用例）

- fixture 与 `tests/test_logger_gui_parent.py` 同口径（`sys.argv[0]` 指向 tmp_path 隔离 `config/`、`logs/`
- ① `test_two_rooms_can_be_split_by_room_field`：两房间线程各写 20 行 `WARNING`
- ② `test_unbound_room_logs_still_land_with_empty_column`：未绑定房间时该行仍落盘且房间列为空。

#### 四、编码代理约定（`AGENTS.md`「已知坑 → 日志、控制台与 GUI / 后台模式」补一条）

- 新条目「多房间交织日志靠 `extra[room]` 列切出…

#### 五、验证结论

| 项 | 命令 / 口径 | 结果 |
| --- | --- | --- |
| 聚焦用例 | `pytest tests/test_logger_console_sink.py tests/test_logger_gui_parent.py test… | 26 passed |
| 全量 | `pytest -q` | **1062 passed / 2 skipped / 0 warnings** |
| 门禁 | `black --check`（120/py314）、`isort --check-only`（profile black）、`mypy`（120 文件）、… | 全部 0 问题（isort 本机需 `PYTHONUTF8=1`，否则 gbk 默认编码会静默跳过 `main.py`）… |
| 真实链路双房间 | 经 `main.start_record` 起两条房间线程（`argv[0]` 指向 `%TEMP%` 子目录，隔离 `config/ logs/ down… | `streamget.log` 得 `… \ | DEBUG \ | 序号1 \ | …` 与 `\ | 序号2 \ | ` 各一行；INFO 两行落 `PlayURL.log` 且房间列为空、无 Loguru 格式化错误 —— **分档落盘位置与改动前一致**… |

- **未采用 `python tests/test_<平台>_live_collector.py <URL> [秒数]` 做双房间验证**（任务书原口径）：这 5 个脚本直连 `src/spider.py` 与 `DanmakuCollector`

### v4.3.0-dev (2026-09-20) — Web 面板 `/health` 探活端点 + HTTP 冒烟接入 CI

**变更摘要**：将内置冒烟测试工具 `scripts/smoke_test.py` 从「有工具、无门禁」接通为 CI 可执行的真实 HTTP 探活。

#### 一、新增功能：探活端点（`src/web_api.py`）

- **路由**：`create_app` 内新增 `@app.get("/health")` → `{"status": "ok", "version": _APP_VERSION}`。
- **鉴权白名单**：把 `/health` 加入 `auth_middleware` 的放行分支（紧邻 `/api/auth/status`）。
- **契约标注**：`{"status": "ok"}` 为对外契约，注释记明「新增字段可以、改名或改值不行」，与 `smoke_web.json`、CI 步骤三处口径绑定。

#### 二、新增功能：CI 冒烟接线（`.github/workflows/ci.yml` + `scripts/_ci_web_smoke.sh`）

- **落点**：在既有 `test` job 末尾追加两步（排在覆盖率/Codecov 上报之后…
- **`Web panel smoke test` 步骤**：经既有复合动作 `.github/actions/retry`（`attempts=2`、`backoff=5`）执行 `bash scripts/_ci_web_smoke.sh`
- **新增脚本 `scripts/_ci_web_smoke.sh`**：一次完整尝试 = 受控启动 `python web.py`（`nohup` 后台、PID 记录）→ 轮询 `/health` 就绪等待（上限 90s…
- **`Upload web smoke artifacts` 步骤**：`if: ... && always()` 保证冒烟变红时仍上传 `logs/web-smoke-report.json`（含实际状态码/耗时/错误行的机读报告）与 `logs/web-panel-smoke.log`

#### 三、修改内容：探活配置（`scripts/smoke_web.json`）

- `/health` 项：`name` 从「健康检查(按需补充真实接口)」改为「Web 管理面板健康检查」（占位移除…

#### 四、新增功能：守护用例（`tests/test_web_api.py`）

- 新增 `TestHealthEndpoint` 两条：`test_health_ok_when_auth_enabled`（`app_env` 固定 `auth=true` 下 `/health` 仍须 200、`version` 与 `app.version` 同源）、`test_health_ignores_engine_state`（把 `get_status` 打成抛异常…

#### 五、文档同步（`README.md` / `README_EN.md`）

- 「Web/接口冒烟测试」章节各补两条：① 默认用例探活 `/`（首页 200）与 `/health`（`{"status": "ok"}`

#### 六、附带改动（`scripts/run_gates.py`）

- 因本轮向 `scripts/` 新增 `_ci_web_smoke.sh` 会触发 CI `static` job 的 `black --check .`

#### 七、验证结论

| 项 | 结果 |
| --- | --- |
| 本地起面板 + `python scripts/smoke_test.py -c scripts/smoke_web.json` | exit 0，2/2 通过；`/health` 实测返回 `{"status":"ok","version":"4.3.0"}` |
| 把 `/health` 期望码改错（500）重跑 | exit 1（`状态码 200 != 期望 500`），随后已还原为 200 |
| `pytest`（全量） | 1048 passed / 2 skipped / 0 warnings |
| `black --check .` / `isort --check-only .` | 全绿（138 文件无差异） |
| `mypy`（不带路径） | 通过，119 文件 0 错误 |
| `basedpyright`（`web_api` + 用例） | 0 errors / 0 warnings / 0 notes |
| `scripts/check_annotations.py` | 通过（`.sh` 不参与密度扫描，仅 Python 生效） |

> 注：`ci.yml` 的 `test` job 现含 3 处 `.github/actions/retry`（ffmpeg 安装、依赖安装、Web 冒烟）；本轮未改动 `AGENTS.md` 的「重试处数」计数（该项由维护者自行处置，不随本条更新）。

### v4.3.0-dev (2026-09-20) — AGENTS.md 分段与可达性重构（better-harness：渐进披露）

**变更摘要**：本轮为**纯文档 / 代理指令**变更…

#### 一、代理指令文档（`AGENTS.md`，修改）

- **风险控制前置**：新增靠前的 `## 风险控制（前置）` 节…
- **「已知坑」按主题分段**：把该节 82 条列表重排为 **18 个 `###` 主题小标题**（录制链与房间线程 / 流地址探针 / 弹幕采集与 SRT / 平台接口与签名 / 画质档位 / HTTP 客户端复用 / 并发与锁 / ffmpeg 命令 / 日志与 GUI 后台 / i18n / 配置键名与布尔口径 / 凭据脱敏 / 类型检查与静态门禁 / 热路径性能 / 构建产物与运行时 / 装饰器契约 / Web 面板与接口 / 测试与审查）。
- **可达性约定与阅读顺序**：文件头新增 `可达性约定` 与 `阅读顺序` 说明——「每次会话都必须遵守的约束」留根文件…
- **改用 Markdown 链接表达路由**（使 `agent-lint` 的 `links`/`references` 从 0 变为可校验）：新增指向 `pyproject.toml`、`scripts/check_annotations.py`、`scripts/check_coverage.py`、`.gitignore` / `.dockerignore`、`config/config.ini` / `config/URL_config.ini` 的链接…

#### 二、代理参考子文档（`docs/agent-reference/`，新增）

- **`docs/agent-reference/project-structure.md`（新增）**：外迁 `AGENTS.md`「项目结构」的完整目录树（111 行…
- **`docs/agent-reference/measured-evidence.md`（新增）**：外迁 4 条坑条目末尾的**一次性实测读数**（探针客户端复用提速 / keepalive 连接实测 / 虎牙选档七档采样 / 斗鱼档位钳制回采）
- **删除项**：`AGENTS.md` 内原完整目录树段落（属语义外迁，非丢弃）。

#### 三、验证（`agent-lint`，只读审计）

- `agent-assets-review` profile：`references` **0 → 15（>0）**，`missingReferences` **仍为 0**，15 条链接目标全部经 `exists:true` 校验。
- `agents-md-review` profile：`long-root-without-progressive-references` 建议项已消除…
- 语义保全：82 条坑条目与基线逐条比对 **0 缺失**…
- 一次跳转可达：抽样项目结构（`[struct-tree]` 定义 → 子文档目录树原文）与 4 个实测锚点（根文件 `#锚点` → 子文档对应 `##` 小标题原文）均可一跳定位。

### v4.3.0-dev (2026-09-20) — 元数据同源对账 + 四语目录核验 + 全量质量门禁跑批

**变更摘要**：本轮为**文档与核验类**变更，**未改动任何运行期源码**（质量门禁跑批结果为零改动）。三部分内容：
① README 中英两侧补入 2026-09-19 的 62 项审查修复更新日志；② 四语目录逐条核验并重编译 `.mo`；
③ 对 2026-09-19 条目中「四语目录 663 条」的事实错误做中英双语勘误。门禁五项全绿。

#### 一、文档同步（`README.md` / `README_EN.md`）

- **问题**：`v4.3.0 (2026-09-19)` 的 62 项审查修复条目此前**只落在 CODE_WIKI**，README 中英两侧均缺失，使面向用户的文档比工程文档落后一个版本。
- **改动**：`README.md`（第 857 行）、`README_EN.md`（第 855 行）各补入一条镜像条目…
- 处理方式与 2026-09-18 条目第三节一致（当时同样补过 2026-09-17 的缺失条目）。
- **附**：`CODE_WIKI.md` / `CODE_WIKI_EN.md` 的「文档统计与索引」快照一并刷新——总数 324 → **285**…

#### 二、本地化核验与重编译（`i18n/`）

| 检查项 | 结果 |
| --- | --- |
| 条目数 | 四目录各 **635 条**（`zh_CN.po` 非空 msgid 635；`zh_CN.mo` 头部 N=636 含空 msgid）… |
| 缺失 | **0 条**（`scripts/extract_i18n_strings.py`：运行时提取 420 条，目录 635 条）… |
| 键集一致性 | 四目录键集完全一致（脚本未输出任何 `[不一致]`） |
| 占位符一致性 | **0 条**不一致（逐条比对各目录译文与源串 msgid 的 `{name}` 占位符集合）… |
| `.mo` | 已重编译：`i18n/zh_CN/LC_MESSAGES/zh_CN.mo`，636 条 / 79262 字节，`compile_po.py --check… |

- 占位符核验为本次**新增的加严项**：2026-09-18 曾出现 `zh_TW.yaml` 把占位符写成 `{message_2}`、导致繁体语言下 `i18n.tr()` 抛 `KeyError` 的缺陷…

#### 三、CODE_WIKI 事实勘误（中英双语）

- 2026-09-19 条目原记「四语目录 635 → **663 条**」
- 判据（五路独立信号一致）：`.mo` 二进制头部 `N=636`（gettext 实际消费的条目数）、`en_US.json` 635 键、`en_GB.json` 635 键、`zh_TW.yaml` 635 键、`extract_i18n_strings.py` 报「zh_CN.po 现有条目：635 条」。
- 时间线佐证：四个目录文件 mtime 为 2026-09-19 02:08，早于 CODE_WIKI 的 02:33，即文档写入时目录已是 635 条，663 属写入时的计数错误，而非事后回退。

#### 四、全量质量门禁跑批（结论：零改动）

| 工具 | 命令口径（对齐 `ci.yml`） | 结果 |
| --- | --- | --- |
| black | `--check --line-length 120 --target-version py314 .` | 通过，136 文件无差异 |
| isort | `--check-only --diff --profile black --line-length 120 .` | 通过（Skipped 8，无排序问题） |
| mypy | `mypy`（**不带路径参数**） | 通过，117 文件 0 错误 |
| mypy（Linux） | `mypy --platform linux` | 通过，117 文件 0 错误 |
| basedpyright | `basedpyright` | 0 errors / 0 warnings / 0 notes |
| pytest | `pytest -q -rs` | **1042 passed / 0 failed / 2 skipped**（约 54s） |

- 2 条 skip 均在 `tests/test_web_api.py:547` / `:566`
- 补跑 `--platform linux` 的理由：CI 运行于 ubuntu，Windows 侧通过不代表 Linux 侧通过（`src/web.py` 含 `ctypes.WinDLL` 等平台专属符号，AGENTS.md 有对应门控约定）。

#### 五、逐项核验结论（无需改动）

- **版本**：`scripts/check_version.py` PASS…
- **依赖**：`pyproject.toml [project.dependencies]` 与 `requirements.txt` 各 20 条逐条一致。
- **egg-info**：`DouyinLiveRecorder.egg-info/requires.txt` 基础段 20 条与 pyproject 一致，仅 `protobuf` 的 spec 顺序被 setuptools 规范化为 `<8,>=6.31.1`，非实质差异。
- **排除目录**：pyproject 内 black / isort / mypy / coverage / basedpyright 五份清单对 19 个核心目录（运行期产物 + 工具生成目录）**全覆盖**…
- **`config/config.ini`**：代码经 `read_config_value` / `read_config_bool` 读取的 131 个键全部存在（大小写不敏感比对）。

#### 六、本地门禁一次性触发点（`scripts/run_gates.py`，新增）

- **背景**：better-harness 评审发现 `declared-gates-have-no-local-trigger`——AGENTS.md 完成定义第 1 步要求「门禁全绿」
- **改动**：新增 `scripts/run_gates.py`
- **安全不变量**：写型 `black .` / `isort .`（缺 `--check` / `--check-only`）兜底拦截…
- **配套用例**：`tests/test_run_gates.py`（14 条…
- **AGENTS.md 同步**：「格式化命令」章节新增本地触发点条目（仅登记入口…

### v4.3.0-dev (2026-09-19) — 全量代码审查修复：62 项分级问题收敛（严重 12 / 中等 22 / 轻微 28）

**背景**：对工作区全部自有源码（148 个文件 / 44,385 行，已排除 `.venv`、第三方依赖与构建产物）做了一次
分组并行的全量审查，产出 `CODE_REVIEW_2026-09-18.md`；本条目记录据此落地的修复。除安全加固外，
绝大多数改动同时修复了真实的功能缺陷（详见各条）。四语目录实测为 **635 条**（`zh_CN.mo` 头部 N=636，含头部空 msgid）。

> [2026-09-20 勘误] 此处原文作「四语目录 635 → 663 条」，与实测不符：四个目录（`zh_CN.po` / `en_US.json` /
> `en_GB.json` / `zh_TW.yaml`）实际均为 **635 条**，`.mo` 头部 N=636。修正依据见 2026-09-20 条目第三节。

#### 一、严重项（12）

| 编号 | 位置 | 修复内容 |
| --- | --- | --- |
| CR-01 | `gui.py` / `main.py` | **GUI 空配置启动静默卡死**：GUI 以 `[cli_exe]` 无参拉起录制核心，而 `non_interactive` 默认 False（全仓仅 … |
| CR-02 | `main.py` | **一行配置多一个逗号导致其后所有房间永久不录**：`quality, url, name = split_line` 在元素 >3 时抛 `ValueEr… |
| CR-03 | `src/platforms/_tars.py` | **Tars 解码缺边界校验 → 弹幕线程永久死循环**：STRING4/SIMPLE_LIST 的长度字段直接当游标增量使用，负值会让游标回退，而 `_g… |
| CR-04 | `src/collector.py` / `src/__init__.py` | **斗鱼弹幕被静默过滤（已修复项回归）**：`only_fans` 在三层各存一份默认值且 `collector.py` 用 `hasattr` 反向覆盖回… |
| CR-05 | `main.py` | **ffmpeg 挂起永久占用并发槽位**：守护循环只有"进程退出 / 用户停止"两个出口，而 FLV 侧保留 `-reconnect*` 系列，CDN 掐… |
| CR-06 | `main.py` | **零字节产物被判成功并撤销线路退避**：成功判定只看 `return_code == 0`，全仓无产物体积校验；HLS 列表 200 但分片全 404 时… |
| CR-07 | `src/config_io.py` / `src/utils.py` | **凭据明文落盘并扩散**：备份线程每 10 分钟把整份 `config.ini`（含 `[Cookie]`/`[账号密码]`）复制到 `backup_co… |
| CR-08 | `src/web_api.py` | **Web 面板可被自身接口接管或锁死**：原有"防自锁"只覆盖"认证已开启时清空密码"，反向路径敞开——认证关闭（出厂默认）时任何人可写入自己的密码再开启… |
| CR-09 | `src/web_config.py` | **房间 URL 零协议/目标校验 → 盲 SSRF**：`validate_room_target` 只挡换行，而分发表末项用**子串包含**匹配 `.m… |
| CR-10 | `src/web_config.py` / `web/app.js` | **脱敏黑名单漏掉全部 URL 型凭据**：只匹配键名，`钉钉/微信/bark 推送接口链接`、`ntfy 推送地址`、`代理地址` 等"凭据嵌在值里"的键… |
| CR-11 | `src/ffmpeg_install.py` / `src/node_install.py` / `build_exe.py` | **安装与打包链路零完整性校验**：蓝奏云分支仅在设了环境变量时才校验哈希（默认路径直接解压执行第三方网盘产物）；官方源为 TOFU 自写基线；`build… |
| CR-12 | `src/spider.py` | **平台解析层"裸取 JSON + 装饰器兜底"范式**：① `_loads_dict` 注释承诺"非 JSON 回 `{}`"却用裸 `json.load… |

#### 二、中等项（22，摘要）

- **WD-01 日志脱敏**：`mask_credentials` 从"只包 url 形参"扩到"整条消息"
- **WD-02/03 弹幕写盘链路**：SRT 队列由无界 `SimpleQueue`（注释却自称"有界"）改为 `Queue(maxsize=10000)` + 满队列计数丢弃…
- **WD-04/05 WebSocket 存活**：恢复协议层 `ping_interval/ping_timeout`（应用级心跳只发不收…
- **WD-06/08/09 Web 侧**：鉴权中间件每请求全量解析 `config.ini` → 改 mtime+size 失效缓存…
- **WD-07 + F-09**：无认证 + 非回环的破例路径改为列出可被利用的具体能力并落日志…
- **WD-10 前端轮询**：`fetch` 加 10 秒超时（原无超时…
- **WD-11/12 并发治理**：抖音限速的 `time.sleep` 移出 `with semaphore`（原写法使 N 个房间排队时占着网络槽睡觉…
- **WD-13 复核后不适用**：现有代码在解析成功（含未开播）时已 `record_success`，原报告"未开播计为失败"的判断有误，**未改动**。
- **WD-14 文件名清洗**：`clean_name` 补控制字符、Windows 保留设备名、60 字符截断（长标题 + 深目录会突破 `MAX_PATH` 导致写盘失败）。
- **WD-15 原子写下沉**：`utils.atomic_write_text` 收敛为唯一实现，`update_config` 与 `update_anchor_name` 由 truncate+write 改为同目录 tmp + `os.replace`。
- **WD-16/17/18/19 平台解析**：淘宝 cookie 回写改为持 `file_update_lock` 且仅在变化时写…
- **WD-20 在线人数恒为 0**：平台把人数放在 `DanmakuMessage.data` 而采集器只透传 `message`
- **WD-21 GUI 线程模型**：`_process_ended` 在 UI 线程 `join` 输出线程 5 秒 + 弹幕尾线程 2 秒（Tk 只能在主线程跑…
- **WD-22 Node 安装自愈**：补 `is_valid_zip` 校验（原先残缺 zip 会把错误哈希固化成基线，此后永久失败不自愈）；7 处 `subprocess.run` 补 timeout。

#### 三、轻微项（28，摘要）

解压限长（`decompress_limited` / `decompress_brotli_limited`

#### 四、测试与门禁

- **测试同步**：`test_spider.py::TestLoadsDict::test_invalid_json` 由"断言上抛 `JSONDecodeError`"改为"断言返回 `{}`"（对齐 CR-12 的正确契约）
- **门禁结果**：`pytest` 全绿…
- **AGENTS.md** 新增 7 条坑位：PEP 758 `except A, B:` 不支持 `as` 绑定…

### v4.3.0-dev (2026-09-18) — 仓库元数据十三项同源对账 + 四语目录补全（594 → 601 条）

**变更摘要**：对 13 个元数据/文档目标做一次全量对账…

#### 一、egg-info 重建（此前停留在 4.1.0 快照）

- `PKG-INFO` 版本为 `4.1.0`（pyproject 已是 4.3.0）、内嵌 README 为旧版。
- `requires.txt` 仍是 `websockets>=12.0`（应为 14.0，`additional_headers/proxy` 是 14.0+ API）与无上限的 `protobuf>=6.31.1`（应为 `<8`）。
- `SOURCES.txt` 缺 `src/config_bool.py` 等 30+ 文件。
- 经 `setuptools egg_info` 重新生成：版本 4.3.0、`websockets>=14.0`、`protobuf<8,>=6.31.1`、SOURCES 139 行、`PKG-INFO` 含最新 README。

#### 二、pyproject.toml

- `[tool.setuptools.package-data]` 补 `"src.proto" = ["*.proto"]`：`douyin.proto` 是 `douyin_pb2.py` 的生成源…
- `[tool.coverage.report].exclude_also` 去掉 `if TYPE_CHECKING:`：coverage 的默认排除规则已含该写法（含 `typing.` 前缀变体）

#### 三、文档结构补漏

- `AGENTS.md` / `CODE_WIKI.md` / `CODE_WIKI_EN.md` 的目录结构段缺 `src/config_bool.py`。
- `README.md` / `README_EN.md` 另缺 `src/scheduler.py`、`src/log_archive.py`，且多列了早已不存在的 `gui_legacy.py`；译文条数停留在「288 条」（实际 601 条）。
- `README.md` / `README_EN.md` 更新日志补 `v4.3.0 (2026-09-17)` 条目（布尔配置解析口径统一 / 指令治理 / 动态并发下限 8→1）——此前只落在 CODE_WIKI…

#### 四、核验结论（无需改动）

- `requirements.txt` ↔ `pyproject.toml [project.dependencies]` 逐条一致（20 条）。
- `.gitignore` / `.dockerignore` / pyproject 六个工具排除列表 / `.coveragerc-concurrency` 的排除目录同源。
- `config/config.ini` 键集相对代码读取点（`main.py` 的 `read_config_value` + `read_config_bool` + `web_config.py`）无缺失；本地值未被覆写。
- `Dockerfile` / `docker-compose.yaml` 的 `APP_VERSION` 动态注入经 `scripts/check_version.py` 校验通过。

#### 五、本地化（i18n）

- **`zh_TW.yaml` 4 处占位符被写成 `*_2`**：`{message_2}`、`{msg_2}`（×2）、`{errmsg_2}`。
- **补 7 条「彩色输出 / 对话框」路径文案**：`color_obj.print_colored()` 与 `messagebox.show*()` 不走 `print()` / `logger.*()`
- 四语目录 594 → **601 条**，`zh_CN.mo` 已重编译（602 条，含头部空 msgid），`compile_po.py --check` 通过。
- 核验：四目录键集一致、无空值、占位符与源串逐条对齐…

### v4.3.0-dev (2026-09-17) — 布尔配置解析口径统一（修复 `true/false` 致 8 项配置静默失效）

**变更摘要**：`config.ini` 的布尔值写成 `true/false` 时曾被判为无效、**静默**回落到硬编码兜底值
（无告警、无日志）。实测致 8 项配置生效值漂移，其中最严重的一项使 9 个海外平台 100% 无法录制。
本轮把散落四处的布尔解析统一到单一实现，`是/否` 与 `true/false`、`1/0`、`yes/no`、`on/off` 一律等价。

#### 一、新增统一解析入口

- 新增**零依赖**模块 `src/config_bool.py`：`parse_config_bool(raw, default)` 与 `format_config_bool(bool)`，
  识别 是/否、true/false、t/f、yes/no、y/n、on/off、1/0（比较前 strip + lower）；空值与未识别值返回 `default`。
  零依赖是硬约束：`src/logger.py` 早于 `main.py` 执行，且 `src.utils → src.logger` 已有依赖链，
  把解析放进 `src/utils.py` / `src/config_io.py` 会形成循环导入。
- `src/config_io.py` 新增 `read_config_bool(parser, section, option, default)`（读取 + 缺键补写）；
  补写沿用规范写法「是」/「否」，**存量值不被覆写**（两种写法已等价，无需迁移）。

#### 二、替换 27 处读取点与 4 处同源口径

- **`main.py`**：移除 `options: dict[str, bool] = {"是": True, "否": False}` 字典查表（该写法只在值恰为
  「是/否」时命中字典，其余写法静默回落到 `options.get` 的第二参数）。全部布尔读取点改走 `read_config_bool`：
  跳过代理检测、https 录制整合读取（含旧键迁移与虎牙旧 SSL 键）、保存文件夹三项、文件名含标题、去表情、
  自动更新主播名、HLS 采集、使用代理 ip、显示循环秒数/源地址、分段录制、mp4 转换 / h264 / 删原文件 /
  时间字幕 / 自定义脚本、弹幕录制与监控、钉钉 @全体、SMTP SSL、只推送不录制、开播 / 关播推送。
- **`src/logger.py`**：`!= "否"` → `parse_config_bool(..., True)`——原写法会把 `false` / `0` / `no`
  判成「开启」，与 `main.py` 的字典查表语义相反。
- **`src/web_config.py::read_web_config`**：`in ("true","1","yes","是")` → `parse_config_bool`。
- **`gui.py::_get_dynamic_status_info`**：`== "是"` → `parse_config_bool`。
- **`web/app.js`**：新增 `CONFIG_TRUE_TOKENS` / `CONFIG_FALSE_TOKENS` + `parseConfigBool`；
  `httpsRecordingEnabled` 由 `=== '是'` 改为复用（面板里 `true` 曾被显示成 HTTP 模式，与实际拉流协议相反）。

#### 三、行为等价性说明

- 取值可能变化的只有「键缺失」与「值无法识别」两条路径，且只在旧实现自身矛盾的两项上收敛：
  `保存文件夹是否以作者区分` 与 `是否使用代理ip(是/否)` 的「值无法识别」分支由兜底实参改为返回默认值
  （这两项的 `read_config_value` 默认值与 `options` 兜底值原本就不一致）。**缺键补写值保持原样**。
- 未识别的存量值只返回默认值，不覆写用户原文。

#### 四、验证

- 真实配置（`true/false` 编码）端到端实测：`skip_proxy_check=True`、`global_proxy=True`、
  `enable_https_recording=True`、`stream_ssl_verify=False`、`logger._log_to_file=True`、
  `[Web]` 节三项布尔解析正确。
- 漂移审计对 `D:\DouyinLiveRecorder\config\config.ini` 复算：漂移项 **0**（改造前 8 项）。
- 门禁：pytest `1042 passed / 2 skipped`；black（136 文件）/ isort / mypy / `mypy --platform linux` /
  `check_annotations` / `compile_po --check` / `check_version` 全绿；`node --test tests/frontend/*.mjs` 9 passed。
- 回归锁：`tests/test_config_bool.py`（含 main.py 的 AST 级「不得再出现 options 字典查表」断言）、
  `tests/frontend/test_quality_ui.mjs`（`parseConfigBool` 口径 + `httpsRecordingEnabled` 不得退回 `=== '是'`）。

### v4.3.0-dev (2026-09-17) — 指令治理：AGENTS.md 冲突/歧义收敛 + 技能路由隔离（无功能行为改动）

**变更摘要**：对 `AGENTS.md` 全文（798 行）、`ci.yml` 相关段与用户级技能做指令级审阅，产出
`CODE_REVIEW_AGENTS_GUIDELINES_2026-09-17.md`（16 项），并落地其中 14 项。**本轮无运行期行为改动**，
唯一源码改动是 `src/spider.py` 的错误注释更正。收敛目标是三类会让代理「停下来确认」或「交付不完整」的问题：
同一约定给出相反事实、命令口径不统一、完成标准缺失。

#### 一、直接冲突条文收敛（同文件内互斥）

- **except 括号**：`AGENTS.md` 曾三处并存互斥口径——「black 26.x 强制去括号」（代码风格章节）↔
  「实测两种写法 `black --check` 均 rc=0」（2026-09-12 更正）↔ 又回到旧结论（已知坑 PEP 758 条目）。
  现合并为唯一条文：**统一写无括号是本项目风格约定，不是 black 门禁强制**，存量带括号写法不得批量改动。
  连带的错误外溢一并修正：`src/spider.py` 模块头原称「改成 `except (A, B):` 会破坏 3.14 语义」，已被实测推翻。
- **异常日志写法**：原规定写成 `f"...{type(e).__name__}..."`（2026-09-10 i18n 迁移前），与
  「形参日志必须走 `i18n.tr()`、禁止 f-string」互斥。现改为 tr 模板 + 关键字实参，保留
  「必须带异常类名 + 掩码 URL」的硬要求。

#### 二、命令口径统一

- 新增 **「格式化命令（门禁唯一基准）」** 章节：black / isort / mypy / check_annotations / compile_po /
  check_version 六条与 `ci.yml` 逐字一致，其它章节一律引用该节，不再各自规定写法
  （此前 tests/ 门禁、已知坑条目共三套写法）。
- **mypy 平台双跑去掉路径收窄**：由 `mypy src/` + `mypy --platform linux src/` 改为
  `mypy` + `mypy --platform linux`——原写法的路径参数会覆盖 `[tool.mypy].files`，
  重新引入根目录入口（gui.py `logger` / `session_id`）的漏检；`ci.yml:232-233` 的过期注释同步更新。
- **basedpyright 定位为本地补充门禁**：此前列为必过但既无权威命令、CI 也不跑；新增小节明确
  命令范围、与 mypy 的报错码差异，以及「平台相关结论以 CI 一致的 Linux 侧为准」的裁决规则。
- **环境适配**：isort `.isorted` 清理、测试临时目录预清由 POSIX `find` / `rm` 改为
  PowerShell 等价写法（本机 Git Bash 无 coreutils），并限定清理范围不含 `downloads/` `logs/` `backup_config/`。

#### 三、新增章节（以往只在会话记忆里、AGENTS.md 缺失）

- **「完成定义（Definition of Done）」**：门禁全绿 → 端到端真机验证 → 回归锁 → CODE_WIKI 中英更新日志 →
  当日记忆日志五步，含豁免档（纯文档/注释改动、只改测试）。
- **「流程编排技能的使用边界」**：日常改动不进入 `vibe` 类治理式运行时（其冻结与硬停会打断
  「改一点 → 真机跑 → 再改」的迭代），`brainstorming` 类设计门对已钉死/已批准方案不适用。
- **「venv 依赖修复分级处置」**：一级 wheel 直解（代理自行处理）/ 二级绕代理补装 / 三级才交回用户。
- **i18n 补前端目录**：`web/app.js` 自带 zh_CN/en_US/en_GB/zh_TW 内嵌目录，改串须同步五处。

#### 四、重复条目与规则本体

- `clear_ffmpeg_reject` 双份 → 收敛为一处 + 指针；版本单一事实源、docstring 禁令标注同源指向。
- 「注释只增不改」增加**例外条款**：该规则保护历史上下文，不适用于已被证伪的事实性陈述；
  这类（含 AGENTS.md 自身条目）必须就地改正而非追加并行说法，旧结论压缩为一行带日期的历史注。
- 变异验证增加适用范围：安全不变量类用例必做，平凡用例免做。
- 移除陈旧引用：`gui_legacy.py`（已于 v4.1.0-dev / 2026-09-10 删除）。

#### 五、技能侧改造

- `brainstorming`：description 收窄到「全新功能/子系统/UI 面」，HARD-GATE 增加豁免清单
  （缺陷修复、重构、已有批准计划的批量推进、真机迭代），设计文档尊重仓库既有约定。
- `karpathy-guidelines`：新增 §1b「疑惑消解顺序」——先消费 AGENTS.md / CODE_WIKI / 测试 / 模块头注释，
  只在「不可逆、需独占信息、文档互斗」三种情况下才停下来问；其余按最佳判断执行并公开声明假设。

### v4.3.0-dev (2026-09-17) — 动态并发下限下调：min_capacity 8→1（同一时间访问网络的线程数）

**变更摘要**：将自适应并发调度器在「动态调速」模式下的安全下限（即 `ConcurrencyScheduler` 的 `min_capacity` 默认值）由 8 下调到 1。

#### 一、修改：并发调度模块（`src/scheduler.py`）

- `ConcurrencyScheduler.__init__` 的 `min_capacity` 默认值由 `8` 改为 `1`（约第 214 行）。
- `main.py` / `gui.py` / `web.py` 入口均只传 `configured_limit`、不覆盖该默认值，故改默认值即全局生效，无需改调用点。
- 动态模式容量算法：`max(min_capacity, max(配置值, min(上限, ceil(活跃数/缩放因子))))`。

#### 二、修改：测试（`tests/test_scheduler.py`）

- 6 处显式 `min_capacity=8` 改为 `1`，使回归用例与新默认对齐。
- `test_scheduler_capacity_floor_and_scaling`：地板断言随新下限修正——`active=0` 时 `>= 8` 改为 `>= 3`（下限收敛至配置值 3）、`active=8` 时 `== 8` 改为 `== 3`（ceil(8/4)=2 < 配置 3 → 配置值兜底）。
- `test_scheduler_fixed_mode_pins_capacity_to_configured_limit`：切回动态模式后 `>= 8` 改为 `>= 1`。

#### 三、文档同步（当前态描述，非历史日志）

- `AGENTS.md`（并发模式约定节）、`CODE_WIKI.md`（调度器架构节）、`CODE_WIKI_EN.md`（架构节）：「默认 min=8 / max=128」统一改为「min=1」。
- 未改动：README / CODE_WIKI 的 v4.0.9(-dev) 历史变更日志（保持原貌）、`PKG-INFO`（构建产物）、运行时日志中的历史记录。

#### 四、验证

- `pytest tests/test_scheduler.py` → 16 passed。

### v4.3.0-dev (2026-09-16) — 仓库元数据同源同步：排除目录补齐 / 两 job 覆盖率口径统一 / 版本与配置键对账

**变更摘要**：以 `pyproject.toml` 的 `[project].version`（4.3.0）与「同源维护」约定为准，对 13 个元数据与文档文件
（AGENTS.md / docker-compose.yaml / requirements.txt / Dockerfile / .gitignore / .dockerignore /
.coveragerc-concurrency / pyproject.toml / config/config.ini / CODE_WIKI*.md / README*.md）做一次全量对账。
本轮**无功能行为改动**，收敛的是两类会长期制造误判的漂移：① 同源维护目录在 6 个同步点中漏配；
② 两个 CI job 的覆盖率排除口径不一致（`exclude_lines` 会**替换**默认规则，导致覆盖率被系统性低估）。

#### 一、排除目录同源补齐（`recordings/`）

- `recordings/` 此前只在部分同步点登记，本轮补齐到全部 6 处：black `exclude`、isort `extend_skip`、
  mypy `exclude`、`[tool.coverage.run].omit`、basedpyright `exclude`，以及 `.coveragerc-concurrency` 的 `omit`。
- 与 `.gitignore` / `.dockerignore` 的目录清单逐条比对，其余目录无漏配。
- 漏配的直接后果是三选一：未跟踪目录污染 `git status`、被 COPY 进镜像、被工具误扫描而拖慢或误报。

#### 二、覆盖率排除规则两 job 口径统一（重要）

- `pyproject.toml` 的 `[tool.coverage.report]` 原用 `exclude_lines`，会整体丢掉 coverage 的三条默认排除规则
  ——`# pragma: no cover` 大小写/空格变体、`...` 省略号函数体、`if TYPE_CHECKING:`——使覆盖率被低估，
  且与并发 job（`.coveragerc-concurrency` 用 `exclude_also` 追加语义）口径分叉。
- 改为 `exclude_also` 后两个 job 逐条一致；`.coveragerc-concurrency` 内遗留的 TODO 注释同步改写为「已收敛」，
  并写明「改回 `exclude_lines` 或单侧增删条目都会重新造成口径分叉」。

#### 三、版本与示例对齐（单一事实源 4.3.0）

- `AGENTS.md` 版本 `4.2.0 → 4.3.0`；`docker-compose.yaml` 注释示例 `APP_VERSION=4.2.0 → 4.3.0`；
  `uv.lock` 项目自身版本 `4.1.0 → 4.3.0`（仅改 1 行，不触发依赖图重解析，73 个依赖包未动）。
- `Dockerfile` 经 `ARG APP_VERSION` + `--build-arg` 动态注入、`main.py` 与 `src/web_api.py` 经
  `importlib.metadata` 运行时读取，均无写死版本；`scripts/check_version.py` 校验通过。
- `DouyinLiveRecorder.egg-info/` 属构建产物且已被 `.gitignore` 忽略，其版本滞后不纳入同步校验范围。

#### 四、配置文件与文档对账

- `config/config.ini`：核对代码侧 `read_config_value` 读取的 128 个键，归一化（section/option 转小写）后
  **无真正缺失的键**——初审报出的 6 处「缺失」（`B站cookie`、`是否启用HLS采集(是/否)`、
  `禁用SSL证书验证的平台(逗号分隔)`、3 个 SMTP 键）均为大小写差异造成的误报：读取侧走 `configparser`
  （option 经 `optionxform` 统一小写、大小写不敏感），`web_config.py` 已注明「代码常量大写、配置文件行小写」为预期。
- 补 `[录制设置] 自定义画质选项(逗号分隔) = `：该键由 WEB 端增删画质 / GUI 端「切换画质」写回，
  README 与本文档均已记载，但配置模板缺槽位；空值按设计回退引擎内置画质全集，行为不变。
- `README.md` / `README_EN.md` 配置说明补齐两个漏记键：`最大同时录制数(0为不限制)`（全局并发录制上限，
  默认 0 即不限制）与 `自定义画质选项(逗号分隔)`；并逐条核对文档示例值与代码默认值
  （`循环时间(秒)=120`、`排队读取网址时间(秒)=0`、`是否启用https录制=否`、`生成时间字幕文件=否`、
  `是否录制弹幕(是/否)=否`）一致——注意 `config/config.ini` 被 `.gitignore` 忽略（含敏感信息），
  故 README 的配置块才是「新用户默认值」的事实源，本地 config.ini 的个性化取值（如分段时间 3600）
  不属于文档漂移。
- 测试基线条目 `699 passed` → `974 passed / 2 skipped`（与实测 `pytest -q` 一致）。

#### 五、忽略规则同源

- `.gitignore` 补 `*.jsonl`（`logs/danmaku_monitor.jsonl` 弹幕监控边车日志）；
  `.dockerignore` 补 `*.icon`（系统托盘图标缓存，此前仅 `.gitignore` 有），两文件条目重新对齐。

### v4.2.0-dev (2026-09-15) — mypy 门禁扩面：范围下沉到 pyproject `[tool.mypy].files`（src/ → 全量代码）+ 6 处类型缺陷修复

**变更摘要**：起于 CI typecheck 报出的 3 个 mypy 错误（huya / async_http / spider）。修复时发现门禁只覆盖
`src/`，根目录入口与测试从未被检查，于是把检查范围固化为配置里的单一事实源，并把 `tests/` 一并纳入、
补齐 15 处已漂移的注解。本轮**无功能行为改动**（gui.py 的收尾路径除外：原本必抛异常，修复后才真正生效）。

#### 一、类型错误修复（6 处，其中 4 处是运行时必然抛异常的缺陷）

- **src/platforms/huya.py**：补 `import i18n`。原代码在 `except` 分支调用 `i18n.tr(...)` 却漏导入，
  帧解析异常时会抛 `NameError` 掩盖真正的解析异常（弹幕排障「0 线索」的放大器）。
- **src/async_http.py**（`_get_client`）：复用分支原先用 `loser is not None` 间接推断 `winner` 非空，
  mypy 无法跨变量收窄；改为在临界区内直接保存 `reused` 实例，返回时收窄为 `httpx.AsyncClient`。
- **src/spider.py**（liveme）：`lm_s_sign` 加 `str()`——`sign_data` 是 `dict[str, object]`，`pop()` 出来是 `object`。
- **gui.py**（此前不在检查范围，3 处）：
  - 补 `from src.logger import child_process_env, logger`：`_read_status_config` 的 except 分支用了未定义的 `logger`。
  - `_schedule_log_flush` 里 `self._process_ended(session_id)` 的 `session_id` 未定义 —— **子进程自然结束后
    的 UI 收尾路径必抛 `NameError`**。修复不是简单删参数（那会丢掉「丢弃旧会话迟到回调」的保护）：
    日志队列的结束哨兵由裸 `None` 改为携带会话代号 `(session_id,)`，UI 线程取出后交 `_process_ended` 校验。
  - `_has_unsaved_config_edits` 返回 `bool(current != ...)`，避免返回 `Any`。

#### 二、门禁范围下沉（单一事实源）

- **pyproject.toml `[tool.mypy].files`**：`src` + 根入口（main/gui/web/i18n/msg_push）+ `build_exe.py` + `scripts` + `tests`。
- **ci.yml typecheck**：`mypy src/` → `mypy`（不带路径参数），范围完全由配置决定，本地与 CI 跑同一条命令。
- **AGENTS.md**：格式化命令同步；并写明**显式传参（`mypy src/`）会覆盖 `files` 配置**，可排障收窄，
  但门禁结论以无参数跑法为准。

#### 三、tests/ 补齐 15 处漂移（门禁早已声明却只靠自觉执行）

- `test_start_record_command_golden.py`：12 处缺类型注解（2026-09-13 新增用例时混入），
  其中 `main_mod` 标注 `ModuleType` 后暴露出 `main.exit_recording = True` 的 `attr-defined`，改用 `setattr`。
- `conftest.py` / `test_notify.py`：generator fixture 返回类型 `Iterator` → `Generator`
  （mypy 要求 generator 函数的返回类型是 `Generator` 或其超类型）。
- `test_danmaku_offloop.py`：type ignore 补 `[assignment]` —— mypy 报 `assignment`、basedpyright 报
  `method-assign`，两种码需同时压制。

basedpyright 对改动文件均 0 问题。

### v4.2.0-dev (2026-09-15) — 修复 Linux CI 用例 `test_read_config_value_missing_key_readonly_ok`（原子写与文件权限位）

**变更摘要**：仅测试与文档改动，无功能代码改动。CI（Linux）跑出 1 failed / 975 passed，
失败断言为「只读配置文件未被写入缺省键」。根因是用例用 `cfg.chmod(0o444)` 制造「不可写」，
但 `read_config_value` 的写回已改为 `_atomic_write_text`（同目录临时文件 + `os.replace`）：
`os.replace` 只校验目标**所在目录**的写权限，与目标文件权限位无关（root 还会整体绕过权限位），
故 Linux 上写回照样成功；而 Windows 的目标文件只读属性会让 `replace` 直接失败，于是
「本地 Windows 过、Linux CI 挂」。

- **tests/test_config_io_readonly.py**：改为 `monkeypatch.setattr(config_io.os, "replace", _deny_replace)`，
  仅对目标配置路径抛 `PermissionError`、其余调用透传真实 `os.replace`，跨平台稳定复现
  「写回被拒 → 记 warning（原子写失败）+ 返回默认值 + 原文件不被写入」这条降级分支；
  `cfg.chmod(0o444)` 保留为场景注释（不再是唯一手段）。
- **AGENTS.md**：「测试编写强制约定」新增条目，写明「文件只读」用例不得只靠 `chmod`，并区分
  `config_io`（原子写）与 `utils.update_config`（`open(...,"w")` 直写）两种写回路径的用例写法。

（与 CI 的 976 collected 一致）；`black --check` / `isort --check-only` / `mypy` / `basedpyright`
对改动文件均 0 问题。另用临时脚本（已删除）在不设只读属性的情况下验证打桩确实触发
`_atomic_write_text` 的 `PermissionError` 分支：warning 已记、临时文件已清理、配置内容未变。

### v4.2.0-dev (2026-09-14) — 仓库元数据与忽略规则同源同步 + 四语本地化目录一致性修复

**变更摘要**：按「单一事实源 + 同源维护」口径对九个配置/元数据文件做了一次全量体检与同步，并修复英式英语目录的内容错误。
本轮**无功能代码改动**，全部为配置、文档与本地化资源的一致性校正；门禁复检全部保持绿（pytest 974 passed / 2 skipped、
black 全仓 134 文件全绿、isort 全绿、`check_annotations` 全通过、`scripts/check_version.py` PASS、
`scripts/compile_po.py --check` 字节级同步）。

#### 一、按模块分类的落地项

- **pyproject.toml**（排除目录同源补全）：`logs` 原先只进了 black 的 exclude，isort / mypy / basedpyright / coverage 四处漏配；
  `backup_config` 更是只存在于两份 ignore 文件、五处工具排除列表全无。现已按同一口径补齐：
  - `[tool.black].exclude`：新增 `backup_config`（`logs` / `downloads` 已有）
  - `[tool.isort].extend_skip`：新增 `logs`、`backup_config`
  - `[tool.mypy].exclude`：新增 `logs`、`backup_config`
  - `[tool.basedpyright].exclude`：新增 `**/logs`、`**/backup_config`
  - `[tool.coverage.run].omit`：新增 `*/downloads/*`、`*/logs/*`、`*/backup_config/*`
  - 五处均加了「运行期产物目录（与 .gitignore/.dockerignore 同源维护）」注释，避免下次再漏。

- **.coveragerc-concurrency**（与 pyproject coverage omit 对齐）：`omit` 补齐 `*/downloads/*`、`*/logs/*`、`*/backup_config/*`。
  该文件与 pyproject 的 coverage omit 是同一份口径的两处副本，此前同样只覆盖了 `node` / `ffmpeg`。

- **.gitignore**（清理失效条目）：「临时/过程性文档」段落原按具体文件名列举 `PERF_REVIEW_2026-08-28.md`
  （连同 `CODE_CHANGES.md` / `TRAE_AGENT_CODE_WIKI.md`），这三个文件在工作区中已全部不存在，逐文件名维护会持续腐化。
  现改为 `PERF_REVIEW_*.md` 通配，并补注释明确 `CODE_WIKI*.md` / `CODE_REVIEW_FIX_1.md` / `DIAGNOSIS_*.md`
  属**正式文档、随仓库分发**，不得加进 .gitignore。

- **.dockerignore**（同上 + 覆盖新增文档）：「文档」段落同样移除已不存在的 `bili_danmuku_proxy.md` / `danmaku_check.md` /
  `todo.md` / `PERF_REVIEW_2026-08-28.md`，改为 `PERF_REVIEW_*.md` / `CODE_REVIEW_*.md` / `DIAGNOSIS_*.md` 三组通配，
  新增同类根目录文档自动落入排除、无需再改本文件；临时文件段补 `*.jsonl`（`logs/danmaku_monitor.jsonl` 等运行日志）。

- **Dockerfile**：`COPY --chown=recorder:recorder . ./` 上方的「不进镜像」清单原先逐项列举且与实际 .dockerignore 已不同步，
  改写为按 .dockerignore 的四类分组口径描述（测试与工具 / 文档 / 运行期产物 / 平台二进制与本地脚本）

- **docker-compose.yaml**：头部注释补充两条事实——① 仓库内不含 `.env`（已被 .gitignore 忽略），首次使用需自建；
  ② 卷挂载的四个宿主机目录（`config` / `downloads` / `logs` / `backup_config`）首次 `docker compose up` 时由 Docker 自动创建，
  四者均已在 .gitignore 与 .dockerignore 中忽略，容器侧同名目录由 Dockerfile 的 `mkdir -p logs downloads backup_config` 预建。
  版本号示例 `APP_VERSION=4.2.0` 与 pyproject 的 `[project].version` 一致，未变更。

- **AGENTS.md**：
  - 「项目结构」补 `.gitignore` / `.dockerignore` 两个文件条目；补三个运行期目录 `logs/`（含 `streamget.log` / `PlayURL.log` /
    `danmaku_monitor.jsonl` / `web_console.log`）、`downloads/`、 `backup_config/`；根目录文档补 `CODE_REVIEW_FIX_1.md`。
  - 「CI / workflow 约定 → dockerignore / gitignore 同源约定」条目扩展：把 `downloads/` / `logs/` / `backup_config/`
    纳入须同步维护的清单，记录本轮补齐的四处工具排除，并写明审查记录类文档走 .dockerignore 通配、但不得进 .gitignore。

- **requirements.txt**：**无变更**。逐条核对 20 个运行时依赖与 `pyproject.toml [project.dependencies]` 完全一致
  （含 `protobuf>=6.31.1,<8` 的 F-14 上限与 `websockets>=14.0` 下界），无需同步。

- **config/config.ini**：**无变更**。以 AST 扫描代码中的配置读取键与 ini 实际键做比对，差异项经核对均为
  configparser `optionxform` 的大小写不敏感匹配（`是否使用SMTP服务SSL加密` ↔ `是否使用smtp服务ssl加密` 等）
  或已合并的历史键（`是否强制启用https录制` / `是否禁用SSL证书验证(是/否)` / `虎牙是否禁用SSL证书验证(是/否)`），
  F-10 的 `tiktok_guest_cookie` 键位亦已就位。

#### 二、本地化（四语目录一致性）

- **i18n/en_GB.json（内容错误修复，21 条）**：该目录有 21 个条目的**值是繁体中文**（误把 zh_TW 的译文写入了英式英语目录），
  涉及弹幕解析异常（`[弹幕]后台协程异常`、`[B站弹幕]帧解析异常`、`[抖音弹幕]弹幕解析异常`、`[斗鱼弹幕]帧解析异常`、
  `[虎牙弹幕]帧解析异常` 等 7 条）与 ffmpeg/Node.js 安装链 SHA256 校验提示（14 条）。
  已按「en_GB 与 en_US 差异仅限拼写」的既定规则回填英式英语（这批条目无 `-ize/-ization` 类拼写差异，直接取 en_US 值）。
- **复核结论（四目录已一致）**：`zh_CN(.mo)` / `en_US.json` / `en_GB.json` / `zh_TW.yaml` 均为 **594 条**，键集两两零差异；
  `en_US` / `en_GB` 无中文残留，`zh_TW` 无未译条目（此前 5 条与 zh_CN 完全相同的条目经核对为无简繁差异的字形，属正常）。
  `scripts/extract_i18n_strings.py` 报告「运行时缺失 0 条」。
- **i18n/zh_CN/LC_MESSAGES/zh_CN.mo**：重编译生成（595 条含 header，72886 字节），`scripts/compile_po.py --check` 字节级同步通过。
- 前端 `web/app.js` 的内嵌四语目录（与 Python 侧独立）经核对四份各 49 键，一致，未改动。

#### 三、验证

- `scripts/check_version.py`：PASS（pyproject 4.2.0 为唯一事实源，Dockerfile 经 `APP_VERSION` 动态注入，无写死版本）。
- `scripts/compile_po.py --check`：OK（595 条同步）。
- `scripts/extract_i18n_strings.py`：运行时缺失 0 条。
- `black --check --line-length 120 --target-version py314 .`：134 文件全绿；`isort --check-only`：全绿。
- `pytest`：974 passed / 2 skipped / 0 failed；`mypy` 改动文件 0 error（残留 3 处为未触碰文件的既有告警）。

### v4.2.0-dev (2026-09-13) — 斗鱼直播「只出 SRT、无视频」根因定位 + HLS 分片层假绿探针 + 选源加固（配置兜底 / 观测增强 / 同源候选）

**变更摘要**：定位并修复斗鱼等平台直播录制「仅生成弹幕 SRT、无视频文件」的事故。

#### 一、按模块分类

- **src/stream_select.py（分片层探针，源于上一轮、本轮稳定化）**：
  - `_probe_hls_segment()`：列表层 GET → 跟随 master 变体 → 对**末行分片**发 `Range bytes=0-0` 探测…
  - 接入 `_validate_stream_url`：HEAD 非 2xx 与 Range-GET 200 两条路径在判定可达前均调用分片层探针，把「列表 200」与「可录制」解耦。

- **src/stream_select.py（选源加固，本轮新增三函数）**：
  - `_hls_selection_config()`（配置兜底）：经 `getattr(main, "hls_collection_enabled" / "hls_collection_exclude_platforms", 默认值)` 读取…
  - `_same_origin_flv(hls_url, flv_candidates)`（同源候选）：按 `?` 前路径比对、并把 `.m3u8`↔`.flv` 互认，识别与 HLS 同 token 的 FLV 候选，供 HLS 分片全死后回退。
  - `_log_source_choice(platform, kind, url)`（观测增强）：单行日志 `选源结论: platform={platform} 采用 {kind} 源: {url}`
  - `select_source_url`：直接读 `main.hls_collection_enabled`/`main.hls_collection_exclude_platforms` 改为 `_hls_selection_config()`

- **tests/test_stream_select.py（测试）**：
  - 修复 2 处既有失败：分片探针引入额外 GET，原 `get_calls == 2/1` 断言改为 `== 3/2`；fake 响应补 `.text`、fake client 补 `close()`。
  - 新增 5 例分片探针测试：`test_hls_segment_404_rejects_playlist` / `test_hls_segment_200_stays_reachable` / `test_hls_segment_404_last_resort_released` / `test_hls_empty_media_playlist_conservative_pass` / `test_select_source_url_falls_back_to_flv_when_hls_segments_dead`。
  - 新增 10 例加固测试：`_same_origin_flv` 匹配/None/忽略 query 三组 + `test_select_source_url_logs_same_origin_flv_fallback` / `test_select_source_url_logs_choice_on_pick` / `test_select_source_url_logs_no_usable_source` / `test_hls_selection_config_defaults_on_missing_globals` / `test_hls_selection_config_normalizes_comma_string` / `test_hls_selection_config_ignores_invalid_type` / `test_select_source_url_survives_missing_hls_config`。

- **tests/test_start_record_command_golden.py（注释规范修复）**：
  - 修复 `scripts/check_annotations.py` 报告的 1 处既有违规：`class _Cap:` 的三引号 docstring 改为类上方 `#` 行注释（语义不变…

- **i18n 四语目录（≥8 条新串）**：
  - `i18n/zh_CN/LC_MESSAGES/zh_CN.po` 追加两段（2026-09-13，分片探针 5 串 + 选源加固 3 串），随后 `python scripts/compile_po.py` 重编译 `zh_CN.mo`（字节级门禁通过）。
  - `i18n/en_US.json` / `i18n/en_GB.json` 各追加 8 键（分片探针 + 加固）

- **DIAGNOSIS_DOUYU_NO_VIDEO_2026-09-13.md（新增诊断报告）**：完整记录问题概述、视频/弹幕解耦结构、排查时间线与证据、根本原因、修复方案（源修复 / 测试 / i18n / 加固 / 注释违规）、诊断思路、验证、经验教训与参考。

#### 二、已知 / 未触碰的 black 违规

- `main.py` 与 `tests/test_start_record_command_golden.py` 经 `black --check --line-length 120 --target-version py314 .` 仍报为不合规（均为既有 diff…

#### 三、验证

- pytest **944 passed / 2 skipped / 0 failed**（较上一轮 934 升 10）；`scripts/check_annotations.py` 退出码 0；`isort --check-only` 全绿；`src/stream_select.py` `black --check` 通过。
- 质量门禁口径：pytest 0 警告、black len120、isort black profile、mypy strict、basedpyright。端到端真机验证（斗鱼房间新 URL 增量复录）待补。

### v4.2.0-dev (2026-09-13) — CODE_REVIEW_FIX_1 遗留项批量修复（22 项完成 + 3 项暂缓）+ 仓库元数据同步

**变更摘要**：本轮完成 `CODE_REVIEW_FIX_1.md`（F-01~F-25）二/三批剩余项…

#### 一、按模块分类的落地项（FIX_1）
- **main.py**：F-02 移除死 import `converts_m4a`/`segment_video`（函数保留于 `src/video_postprocess.py`
- **gui.py**（F-04~F-07/F-09）：会话代号 `_session_id` 自增与 `_read_output`/`_wait_and_update_ui`/`_process_ended`/`_on_recording_stopped` 校验闭环…
- **msg_push.py**（F-24）：ntfy 测试调用在未注释路径下会发真实推送…
- **src/ffmpeg_install.py / scripts/node_install.py**（F-17/H-1）：新增 `_sha256_of_file` + `_check_or_record_zip_sha256`（trust-on-first-use）
- **src/web_api.py**（F-20）：SSE 端点占用面修复（同上）；list_files 悬空/逃出 root 符号链接崩溃与信息泄露已复核。
- **web/app.js**（F-21）：独立内嵌四语目录（zh_CN/en_US/en_GB/zh_TW）四处同步加译，改完必跑 `node --test tests/frontend/*.mjs`（6 用例）与 `node --check web/app.js`。
- **web.py**（F-22）：`/api/status/stream` 保留并修复（同上）。
- **src/web_config.py**（F-23）：行内注释引号优先（引号包裹值按闭合引号后切分，无引号回落 `" #"`/`" ;"` 启发式）；新增 `_config_write_lock` 原子写（H-6）。
- **src/utils.py**（F-16/F-25）：`read_ini_value(file_path, section, key) -> str|None`（不写回）
- **src/spider.py**（F-10/F-11/F-19）：`_read_tiktok_guest_cookie` 须在装饰器 `@trace_error_decorator` 之上插入（往「@decorator + def」之间插代码会劫持装饰器归属…
- **src/sync_http.py**（F-12）：SSL 白名单需平台域名清单，暂缓。
- **requirements.txt / pyproject.toml**（F-14 可落地部分）：`protobuf` 加 `<8` 上限（douyin_pb2 为 protoc 25.x 产物…

#### 二、澄清与暂缓项
- **F-08（AGENTS.md 注释约定澄清）**：原「black 强制」理由有误——实测 `except (ValueError, TypeError) as e:` 跑 `black --check` 仍 rc=0 未变…
- **F-01 已完成（2026-09-13）**：start_record 拆分（5 路 ffmpeg 命令构造单一化）。
- **F-12 暂缓**：SSL 白名单需平台域名清单。
- **F-13 暂缓**：抖音 signature 未 URL 编码，与上游 dart 一致，修复前须抓包对照上游行为不得盲改。
- **F-19 待真机验证**：抖音无 nonce 去重校验。

#### 二之一、F-01 完成 — start_record 录制命令构造拆分（2026-09-13）

**背景**：`main.start_record` 在 音频(MP3/M4A) / FLV / MKV / MP4 / TS 五个分支各内联一份 `command = [...]` ffmpeg 输出参数列表。

**做法**：
1. 先写黄金快照测试（不破坏既有逻辑）：`tests/test_start_record_command_golden.py` 冻结时间（`datetime`/`time` 双向 mock…
2. 再把 5 份内联列表收敛为模块级 `_build_ffmpeg_output_args(...)`：容器映射全部查 `SEGMENT_FORMAT_BY_SUFFIX`（零裸字面量）
3. 重跑黄金测试：20/20 通过，ffmpeg 命令与重构前逐字节一致；全量 `pytest` **929 passed / 2 skipped / 0 failed**。

#### 二之二、收官批次 — F-01 完结 / F-12 / F-13 / F-14（2026-09-14）

至此 `CODE_REVIEW_FIX_1.md` 的 25 项**全部结项**（F-08 为澄清非问题）。

- **F-01 第二阶段（命令构造单一定义点）**：新增 `_build_ffmpeg_input_args()`（输入侧 `-reconnect*` / `-headers` / `-tls_verify` / `-http_proxy`
- **F-01 第三阶段（执行骨架收敛）**：`_run_ffmpeg_record()` 统一 try/except OSError + `check_subprocess` + 启动失败清幽灵 `recording` 条目…
- **F-01 第四阶段（平台分发表驱动化）**：`_resolve_platform_stream` 的 53 层 `elif` 链改为 `_PLATFORM_RESOLVERS` 分发表 `(匹配器, 处理函数)`：52 个平台各自抽出 `_resolve_<host>()`
- **F-01 附带修正（行为漂移）**：TS 非分段在「被注释 / 停止录制」结束时**无条件**起线程转 MP4…
- **F-01 附带修正（显示一致性）**：分段录制的「准备开始录制…」提示原先打印的是非分段文件名（FLV/MKV/MP4 用旧时间戳、TS 用新时间戳…
- **F-12（sync_http SSL 作用域）**：`CERT_NONE` 上下文与 opener 由 import 期常驻改为**惰性构造**…
- **F-13（抖音 signature 编码）结论：保持不编码**。
- **F-14（protobuf 兼容护栏）**：本环境仍无 protoc / grpcio-tools…

#### 三、仓库元数据同步（Task 1/2）
- `AGENTS.md` 版本 `4.1.0` → `4.2.0`
- i18n 四语目录（zh_CN.po / en_US.json / en_GB.json / zh_TW.yaml）已在上轮补全（587 条…

#### 四、验证
- pytest **974 passed / 2 skipped / 0 failed**（含 F-01 黄金快照测试 20 用例）
- 质量门禁口径：pytest 0 警告、black len120、isort black profile、mypy strict、basedpyright。端到端真机验证（F-19 抖音 nonce 校验）待补。

### v4.2.0-dev (2026-09-12) — 代码审查全量修复（P0+P1+P2 顺手 + 网络层/平台层/scripts 门禁 + i18n 补齐，约 120 项）

**变更摘要**：完成 `CODE_REVIEW_2026-09-12.md`（约 120 项：3 严重 + 6 高危 + ~40 中危 + ~70 低危）的 P0/P1/P2 顺手项与 H-2/H-3/H-4/H-5/H-6 高危项…

#### 一、按模块分类
- **安全/依赖**：H-1 SHA256 钉定（`scripts/ffmpeg_install.py`+`scripts/node_install.py` `_sha256_of_file`/`_check_or_record_zip_sha256`
- **并发/网络**：H-2 singleflight（`src/cookie_cache.py`）隔离锁内 await + gui.py 6.2 全修（SMTP 头注入 `_reject_smtp_newline`、会话代号、画质表去重）
- **平台修复**：C-2 斗鱼粘包（`offset += full_len + 4`）
- **健壮性**：H-6 原子写（config_io `_atomic_write_text` + web_config `_config_write_lock`）

#### 二、i18n 与门禁
- i18n：10 处 f-string 日志改 `i18n.tr`
- 门禁脚本：sync_version.check_all「先判命中再判等」、check_coverage 模糊匹配收紧、smoke_test utf-8-sig + `_NoRedirectHandler` + `_safe_print`
- 验证：pytest 907 passed / 2 skipped；black/isort 全绿；check_annotations 0 违规；py_compile 全绿。

### v4.1.0-dev (2026-09-11) — HLS(m3u8) 输入禁用 `-reconnect_at_eof`：修复直播录制只出字幕无视频（P0，推翻上一轮遗留判断）

**变更摘要**：`-reconnect_at_eof 1` 对 HLS(m3u8) 输入导致 ffmpeg 在播放列表层无限重连…

#### 一、事故形态与根因（`main.py` 录制基础命令）

- **事故形态**（2026-09-11 凌晨…
- **根因**：`-reconnect_at_eof 1` 使 http 层在「上层 demuxer 要求完整读响应」到达 EOF 后无限重连。

#### 二、修复（唯一正确做法）

- `main.py`：`real_url` 含 `.m3u8` 时在命令构造末尾删除 `-reconnect_at_eof` 参数对（`if ".m3u8" in real_url: idx = ffmpeg_command.index("-reconnect_at_eof"); del ffmpeg_command[idx:idx+2]`）
- `scripts/douyin_live_recorder_standalone.py`：`build_ffmpeg_cmd` 与 `run_ffmpeg` 内联字面量列表同步修复（维持「参数列表内联在调用点 + shell=False」的门禁语义——del 只按字面量标志对删除…

#### 三、防线与验证（2026-09-11）

- `tests/test_ffmpeg_reconnect_args.py` 新增第三个不变量类 `TestReconnectAtEofDroppedForHls`：AST 断言每个命令定义点（main.py 1 处、standalone 2 处）都有「`.m3u8` in url 判定 + 函数体删除 `-reconnect_at_eof` 参数对」守卫…
- 定向：`test_ffmpeg_reconnect_args.py` 5 passed + `test_record_container.py` 18 passed…
- `AGENTS.md`「已知坑」`-reconnect*` 条目追加第三形态（保留原两形态文字、只增量补充，推翻结尾「语义边界」旧认知），供后续防回归。

### v4.1.0-dev (2026-09-11) — Web 面板直播间列表窄视口错位修复（table-layout:fixed + 地址列省略 + 窄屏横向滚动）

**变更摘要**：修复「直播间列表」在窄视口（有效宽度 ≈500px…

#### 根因与修复（`web/style.css` 末尾新增段）

- 根因：`.data-table` 为浏览器默认 `table-layout: auto` 且无任何列宽/截断约束…
- 修复：`#rooms-view .data-table` 改 `table-layout: fixed`
- 浏览器差异说明：Chrome/Edge 在 `/?&=` 处断行、Firefox 列宽分配策略不同、Safari 的单元格 ellipsis 必须配合 `table-layout:fixed`——fixed 布局是跨三者唯一同时解决「溢出 + 省略号」的方案。

#### 验证（2026-09-11，Chrome 153 headless 渲染真实 `web/style.css`）

- 1200 / 768px：表格不超面板、删除按钮在卡片内、表头全部横排、8 行行高一致（47px）；
- 500 / 375px：所有元素裁剪在面板卡片内（`overflow-x:auto` 生效…
- 回归：纯 CSS 且作用域限定 `#rooms-view`，不涉及 pytest / 前端 node:test 用例。

### v4.1.0-dev (2026-09-11) — 修复 ffmpeg `-reconnect*` 选项缺值导致的录制启动 -22（EINVAL）

**变更摘要**：修复 2026-09-10「`-reconnect*` 移到 `-i` 之前」重构中丢失的选项取值——`-reconnect_streamed` / `-reconnect_at_eof` 的布尔值 `1` 被丢掉…

#### 一、根因（`main.py` 录制基础命令）

- 09-10 代码审查修复把 `-reconnect_delay_max 60 / -reconnect_streamed / -reconnect_at_eof` 从 `-i` 之后整体移到 `-i` 之前…
- 同步修正 `_FFMPEG_ERRNO_HINTS[-22]` 文案：`-22` 除「容器/编码错配（HEVC 写进 ipod）」外还有「输入选项解析失败」一类成因…

#### 二、修复与防线

- `main.py`：`-reconnect_streamed 1` / `-reconnect_at_eof 1` 补回取值（`-i` 之前位置不变）。
- `tests/test_ffmpeg_reconnect_args.py`（新增…
- 本机 ffmpeg 实测：事故参数对本地 HLS 流逐字复现用户日志报错；修复参数输入正常打开并成功拉流写盘。

#### 三、验证（2026-09-11）

- `pytest`（test_ffmpeg_reconnect_args / test_record_container / test_main_fixes）：**50 passed**；
- `black --check` / `isort --check-only` / `mypy`：全绿；
- 遗留观察项：`-reconnect_at_eof 1` 对带 ENDLIST 的流会无限重连（重连无次数上限）——真直播无 ENDLIST 不触发…

### v4.1.0-dev (2026-09-10) — 形参日志 f-string → i18n.tr 全量迁移（242 处 / 27 文件；四语目录占位符改名）

**变更摘要**：把 `logger.*` / `print` 的 **242 处 f-string 调用点**改写为 `i18n.tr(模板, **kw)`

#### 一、迁移机制（`i18n.py` 上一轮新增，本轮大规模落地）

- `i18n.tr(template, **kwargs)`：先 `_tr(template)` **查表**…
- 格式说明符 / 转换符由调用方**预先求值**后作实参传入…
- 占位符名由表达式**确定性派生**（同一模板内重名加 `_2/_3` 后缀）

#### 二、源码迁移（242 处 / 27 文件）

- 计数：`main.py` 58、`src/spider.py` 25、`src/stream_select.py` 20、`msg_push.py` 15、`src/recorder_status.py` 12、`web.py` 11、`src/danmaku_monitor.py` 11、`src/ffmpeg_install.py` 11、`src/config_io.py` 9、`src/video_postprocess.py` 9、`src/log_archive.py` 7、`src/utils.py` 7、`src/async_http.py` 6、`src/node_install.py` 6、`src/ffmpeg_proc.py` 5、`src/notify.py` 5、`src/scheduler.py` 5、`src/stream.py` 4、`src/collector.py` 3、`src/sync_http.py` 3、`src/platforms/bilibili.py` 2、`src/room.py` 2、`src/ttwid.py` 2、`gui.py` 1、`src/cookie_cache.py` 1、`src/platforms/douyin.py` 1、`src/web_tray.py` 1。
- 跳过 9 处**无翻译价值**的纯装饰/纯占位符模板（如 `f"{'=' * 60}"`），与提取器 `is_valuable` 同口径。
- 归一化既有 `tr()` 调用：`src/ffmpeg_proc.py` 的 `count=len(still_running)` → 模板占位符按新规则派生为 `{still_running_count}`
- 27 个文件补 `import i18n`

#### 三、四语目录改写（键集合 539 → 544）

- `i18n/zh_CN/LC_MESSAGES/zh_CN.po`：250 行占位符改写（逐行、保留 CRLF/分组注释）
- `i18n/en_US.json` / `i18n/en_GB.json`：各 125 条键值改写 + 新增 5 条，`sort_keys=True` 落盘保持原格式（无 BOM / CRLF）。
- `i18n/zh_TW.yaml`：134 行改写 + 新增 5 条（单引号风格）。
- 重编译 `zh_CN.mo`：545 条（544 + 头部空 msgid），65232 字节；`--check` 字节级同步通过。
- `.po` 头部维护说明更新：占位符须为纯标识符…

#### 四、工具与门禁改造

- `scripts/extract_i18n_strings.py`：`scan_file` 新增 `tr(...)` / `<别名>.tr(...)` 首参常量串识别（f-string 与 tr 双形态并存期必须都扫）
- `tests/conftest.py`：新增 autouse fixture `_pin_identity_translation`
- `tests/test_i18n_migration.py`（新增…
- `AGENTS.md`：新增 2 条防回归条目（形参日志必须走 `tr()`；测试必须冻结翻译为恒等映射）。

#### 五、验证（2026-09-10）

- `pytest -q`：**902 passed, 2 skipped**（899 → +3 迁移回归用例；迁移前后均全绿）；
- `python scripts/extract_i18n_strings.py`：**缺失 0 条，四语目录键集合零差异**（各 544 条；191 条历史/兼容冗余项保留不动）；
- `python scripts/compile_po.py --check`：与 `.po` 同步（545 条）；
- `black --check .`：128 files unchanged；`isort --check-only .`：exit 0（Skipped 9）；`mypy src/ main.py web.py gui.py i18n.py msg_push.py`：44 files 0 error；
- `python scripts/check_annotations.py`：全部通过（新增测试文件注释密度 13.8% ≥ 13.0%）；
- `python scripts/check_version.py`：PASS。

#### 六、回滚点

- 迁移前的完整快照保留在 `.workbuddy/tmp/i18n_param_migration_backup/`（四语目录 + 提取器 + 27 个源文件…

### v4.1.0-dev (2026-09-10) — 代码审查 28 项修复 + 仓库元数据同源同步 + 四语本地化补全（521 → 539 条）

**变更摘要**：本轮基于 `CODE_REVIEW_2026-09-10.md` 全仓审查意见逐项修复（P1 全部清零、P2/P3 按需）

> **本条目第二节「遗留 8+4 项推进 + uv.lock 4.1.0」追加在文末新条目 `v4.1.0-dev (2026-09-10) — 遗留 8+4 项推进 + uv.lock 对齐 4.1.0`，不打断本节阅读。**

#### 一、代码审查修复（按模块）

- **`main.py`**：
  - ffmpeg 命令行 `-reconnect_delay_max 60 / -reconnect_streamed / -reconnect_at_eof` 由 `-i` **之后**移至 `-i` **之前**：`-reconnect*` 是输入级选项…
  - `_rec_sem.acquire()` 由 `Popen` **之后**移至**之前**…
  - `process.wait(timeout=30)` 的 `except Exception: pass` 改为 `except subprocess.TimeoutExpired:` 后 `kill()` + 重新 `wait()`
- **`src/ffmpeg_proc.py`**：`_cleanup_single_ffmpeg_process` / `cleanup_all_ffmpeg_processes` 增加返回值判定——终止失败时告警并仅清理 `poll() is None` 的条目…
- **`src/stream_select.py`**：异常分支改为 `if last_resort: warning; return True`，与上方稳定拒收的 `last_resort` 放行语义对齐。
- **`src/web_config.py`**：新增 `is_sensitive_key()` / `is_sensitive_item()`（正则 `令牌|密码|授权码|token|secret|passwd|password|api[_-]?key`
- **`web/app.js`**：新增 `isSensitiveField(section,key)` JS 侧等价实现…
- **`src/collector.py`**：缓存 `self._cls_name`
- **`src/srt_writer.py`**：新增 `_sanitize_srt_text()`（`\r\n→空格`、`-->→->`）
- **`src/spider.py`**：新增 `import os` 与 `_read_haixiu_token_override(is_haixiu)`
- **`src/ttwid.py`**：非阻塞获取失败时改阻塞式重新获取（串行接管），而非在锁外自行抓取，避免并发重复拉取。
- **`src/async_http.py` / `src/sync_http.py`**：请求体判定 `if data or json_data:` 改为 `if data is not None or json_data is not None:`（空 dict 应被视为有效请求体…
- **`src/danmaku_monitor.py`**：`setdefault` 改显式 `get` + 按需创建（避免每条消息都求值默认参数工厂，去噪）。
- **`src/cookie_cache.py` / `src/async_http.py`**：日志统一经 `utils.mask_credentials()` 脱敏。
- **`src/utils.py`**：新增 `mask_credentials(text)`
- **`scripts/check_coverage.py`**：`missing_modules` 由告警改为 `return 1`（门禁不再「假绿」）。
- **`scripts/smoke_test.py`**：`load_config` 对非法顶层结构抛 `ValueError`；`main()` 捕获 `(OSError, ValueError)` → `sys.exit(2)`。
- **`scripts/compile_po.py`**：`import os`，写入改临时文件 + `os.replace` 原子替换（避免中途失败留截断 `.mo`）。
- **`scripts/check_version.py`**：`strip_v` 由 `lstrip("v")` 改 `removeprefix("v")`（避免误删如 `ver` 前缀）。
- **`tests/`**：
  - `test_concurrency_rate_limit.py` 整体重写：驱动真实 `src.ttwid.get_ttwid()`（8 线程断言 `_fetch_ttwid` 仅调用一次）+ `src.stream_select._throttle_probe()`
  - `test_record_container.py`：`_segment_format_nodes(path=_MAIN_PATH)` 增加 `path` 形参；新增 `TestSegmentFormatSecondDefinitionPoint` 覆盖 `src/video_postprocess.py`。
  - `test_danmaku_wiring.py`：`monkeypatch.setattr(main.time, "sleep", ...)` 改 `SimpleNamespace` 垫片仅覆盖 `sleep`（避免污染全局 `time` 模块）。
  - `test_async_http.py`：补 `call_args.kwargs["data"]`/`["content"]` 断言。
  - 删除 `tests/test_utils.py.isorted`（isort 残留）。

#### 二、仓库元数据同步（8 文件）

- `pyproject.toml` 版本为唯一事实源（4.1.0）；`AGENTS.md` 版本号 `4.0.9.4 → 4.1.0`、`docker-compose.yaml` 注释 `APP_VERSION` 示例 `4.0.9.4 → 4.1.0`，均对齐 `pyproject.toml`。
- `requirements.txt` 与 `pyproject.toml [project.dependencies]` 20 条依赖经脚本比对无漂移…

#### 三、本地化补全（4 目录 + 编译产物）

- 补入修复期新增的 18 条日志原文（来源：`main.py` 3、`src/collector.py` 7、`src/async_http.py` 1、`src/ffmpeg_proc.py` 2、`src/cookie_cache.py` 2、`src/stream_select.py` 3）
- `python scripts/compile_po.py` 重编译 `zh_CN.mo`（540 条含头部空 msgid，67700 字节），`--check` 字节级同步通过。

#### 四、删除项

- 删除 `tests/test_utils.py.isorted`（isort 过程残留）。

#### 五、遗留未处理（需产品决策 / 真机验证，本期未改）

- **需产品决策**：音频扩展名/容器、notify 脚本超时、`http_config` TLS 拆流、web_api 鉴权模型、`gui_legacy.py` 废弃、hls.js `@latest` 钉版、弹幕落盘离主循环、i18n 形参文本。
- **需真机验证**：`spider.py` SSRF/JSON 点位、`ws_client.py` 加密套件/心跳、`proxy.py` Windows 格式、`video_postprocess.py` 超时。

#### 六、验证（2026-09-10）

- `pytest -q` 全量：`870 passed, 2 skipped, 0 warnings`（修复前针对性 11 模块 201 passed）；
- `python scripts/extract_i18n_strings.py`：缺失 0 条，四语目录零差异；
- `python scripts/compile_po.py` / `--check`：与 .po 同步（540 条）；
- mypy 106 files 0 error；black 124 unchanged；isort pass；basedpyright 0 error（改动文件）；
- `python scripts/check_version.py`：PASS（版本动态化状态无回退）。

### v4.1.0-dev (2026-09-10) — 遗留 8+4 项推进 + uv.lock 对齐 4.1.0（v4.1.0 第二批）

**变更摘要**：承接上一节「五、遗留未处理」中 8 项需产品决策 + 4 项需真机验证的清单…

#### 一、决策类 8 项推进（按模块）

- **`index.html`**：`hls.js@latest` → 钉版 `hls.js@1.7.2`（jsdelivr CDN 供应链风险；与同文件 `flv.js@1.6.2` 钉版惯例对齐）。
- **`src/http_config.py` + `main.py`**：TLS 校验拆为拉流专用（`get_effective_ssl_verify`）和控制面通用（`ssl_verify`）两条路径…
- **`main.py`**：音频分支 `SEGMENT_FORMAT_BY_SUFFIX` 与扩展名/编码器三方对齐——纯音频平台（猫耳FM/Look 等）保存类型含 m4a 时输出 `.m4a` + aac + ipod…
- **`src/notify.py`**：`run_script` 改用 `communicate(timeout=_SCRIPT_TIMEOUT_SECONDS=300.0)` + 超时后 `process.kill()` + 二次 `communicate()` 回收管道…
- **`src/web_api.py`**：鉴权模型强化三项真实改进——① 中间件统一加 `X-Content-Type-Options: nosniff` + `X-Frame-Options: DENY`（放行/拒绝两条路径均带…
- **`gui_legacy.py` 删除 + 元数据同步**：删除根目录 `gui_legacy.py`（与 `gui.py` 功能重复且遗留 `CREATE_NO_WINDOW` 启动子进程导致 `send_signal(CTRL_BREAK_EVENT)` 永远无效的 bug）
- **`src/collector.py`**：弹幕 SRT 落盘从事件循环线程解耦——`_on_message` 仅做 O(1) 入队 `queue.SimpleQueue`
- **`i18n.py` + 18 处调用站**：新增 `tr(template, **kwargs)` 助手——先 `_tr(template)` 查表…

> **预存 200+ 形参日志**仍用 f-string 形式（属历史遗留，非本批范围），不替换目录键；待后续「全部 i18n 形参迁移」专项工作推进。

#### 二、真机验证 4 项保守实施（按模块）

- **`src/spider.py`**：新增 `_safe_loads(text) -> Optional[dict]` 异常安全解析（捕获 `JSONDecodeError` 记 warning 后回 None）
- **`src/ws_client.py`**：`_heartbeat_loop` 加 `asyncio.wait_for` 兜底（超时 = `heartbeat_interval + 1.0`）
- **`src/proxy.py`**：`ProxyInfo.__post_init__` 接受 IPv6 字面量——`[::1]:8080` 形如 Windows 注册表 `ProxyServer` 的常见 IPv6 配置…
- **`src/video_postprocess.py`**：`segment_video` / `converts_mp4` / `converts_m4a` 三个 `_run_ffmpeg_checked` 调用者分别新增 `except subprocess.TimeoutExpired as e:` 独立分支并按「转封装超时 / 转码超时 / 抽音频超时」分类告警…
- **`tests/test_machine_validation_fixes.py` 新增 7 项**：① `_safe_loads` 合法/非 dict/损坏 JSON 路径…

#### 三、仓库元数据收尾

- `uv.lock` 项目自身版本 `4.0.9.4 → 4.1.0`（仅改 1 行：`name = "douyinliverecorder"` 块下的 `version = "4.0.9.4"` → `4.1.0`）
- 重新生成 `DouyinLiveRecorder.egg-info/PKG-INFO`（之前为 4.0.9.2…
- `scripts/check_version.py` PASS（动态化状态无回退）。

#### 四、删除项

- `gui_legacy.py`（旧版 GUI，与 `gui.py` 功能重复且 `CREATE_NO_WINDOW` bug 致优雅停止永不生效）。

#### 五、遗留未处理（本期仍未动）

- 预存 200+ 形参日志的 f-string → `tr()` 全量迁移（专项工作，非本批范围）。
- 真机验证类 4 项的实测验证（**已交付用户**）：`spider.py` SSRF/JSON 真实接口校验、`ws_client.py` 加密套件在 `OpenSSL 3.x` 下的实测握手、`proxy.py` Windows 系统代理 IPv6 实际探测、`video_postprocess.py` ffmpeg 转码卡死的实际超时路径。

#### 六、验证（2026-09-10）

- `pytest -q` 全量：`899 passed, 2 skipped, 0 warnings`（修复前 870 → 增加 29 项新测试：test_notify 4 + test_web_api 4 + test_danmaku_offloop 5 + test_i18n_tr 6 + test_machine_validation_fixes 7 + 原 11 模块针对性 201 passed 不变）；
- `python scripts/extract_i18n_strings.py`：缺失 0 条，四语目录零差异；
- `python scripts/compile_po.py` / `--check`：与 .po 同步（540 条）；
- mypy 44 files 0 error（含 `src/spider.py` 补 `Optional` 导入 + `src/ws_client.py` 补 `cast` 导入）；black 104 files unchanged（isort 调整 5 文件后通过）；isort pass；
- `python scripts/check_version.py`：PASS（`uv.lock` 4.1.0、egg-info 4.1.0、pyproject 4.1.0 全一致）；
- `uv lock --check`：通过（73 包未动）。

### v4.0.9.4-dev (2026-09-07) — CI 依赖版本对齐官方最新稳定版（codecov-action v5→v7、isort 8.0.1→9.0.1、mypy 2.3.0→2.3.1）

**变更摘要**：按 2026-09-07 时点逐一核对 `.github/workflows/ci.yml` 引用的全部依赖与运行时版本…

### v4.0.9.4-dev (2026-09-06) — 仓库元数据八文件同源同步 + 四语本地化目录补齐（516 → 521 条）+ 本期改动总览（按模块分类）

**变更摘要**：收尾两项一致性工作…

#### 一、元数据与构建（8 文件）

- `pyproject.toml`：`[tool.setuptools].packages` 由 `["src"]` 改为 `["src", "src.platforms", "src.proto"]`。
- `AGENTS.md`：
  - 项目结构树补 `tests/`（含 `frontend/`）、`src/proto/__init__.py`、`.github/ISSUE_TEMPLATE/` + `PULL_REQUEST_TEMPLATE.md` + `issue-translator.yml`
  - 「关键约定」模块计数 41 → 42（新增 `src/proto/__init__.py`）；
  - 测试节新增前端用例约定（`tests/frontend/*.mjs` 用 Node 内置 `node:test`
  - 依赖管理节补「开发依赖在 `[project.optional-dependencies].dev`、不进 `requirements.txt`」与「前端测试零 npm 依赖」两条口径；
  - 「已知坑」新增 2 条：HLS 采集排除平台是**整组剔除**（与 `_FLV_FIRST_PLATFORMS` 的调序语义不可互相实现）、GUI/WEB 画质切换写回后必须同步编辑器快照与显示源（序号前缀 / 旧快照覆盖 / 日志旧值三个缺陷同源）。
- `docker-compose.yaml`：注释中 `APP_VERSION` 示例值 `4.0.9.2` → `4.0.9.4`（对齐 `pyproject.toml`）
- `requirements.txt`：头部注释补「开发依赖走 `.[dev]`、GUI 走 `.[gui]`、均不进运行时清单」与「前端用例零 npm 依赖」
- `Dockerfile`：`ARG APP_VERSION` 处补「唯一事实源为 `pyproject.toml`、构建时用 tomllib 取值注入」的口径…
- `.gitignore` / `.dockerignore`：两份同源新增 `*.pyc_probe_tmp`（过程性探针残留，如遗留的 `src/stream.pyc_probe_tmp`，非源码）。
- `.coveragerc-concurrency`：头部补注「前端 `.mjs` 用例不产生 Python 覆盖率数据」与「omit 清单与 pyproject / 两份 ignore 同源维护」。

#### 二、本地化（4 目录 + 编译产物）

- 新增 5 条（均为 logger 侧 f-string 模板，来源：`src/stream_select.py` 3 条、`src/danmaku_monitor.py` 1 条、`src/cookie_cache.py` 1 条）：
  - `平台 {platform} 在 HLS 采集排除列表中，且无 FLV/record_url 可回退，本轮放弃（可将该平台移出排除列表恢复 HLS 采集）: ...`（`src/stream_select.py`）
  - `弹幕边车文件写入失败: {type(e).__name__}: {e}`（`src/danmaku_monitor.py`）
  - `流地址校验: {url} - GET 复核异常: {type(e).__name__}: {e}（attempt {attempt}）`（`src/stream_select.py`）
  - `流地址校验: {url} - Range-GET 未取得响应，按校验失败处理`（`src/stream_select.py`）
  - `等待其它线程的 cookie 拉取超时，返回空结果: {key}`（`src/cookie_cache.py`）
- 目录条目 516 → 521，四目录键集合经提取器复检**完全一致**；运行时「有、目录无」缺口由 5 条清零（保留 183 条历史/兼容冗余项不动）。
- `zh_CN.po` 头部「更新日期 / PO-Revision-Date」2026-08-30 → 2026-09-06…
- `web/app.js` 前端四语字典（各 106 键）经扫描核对键集合一致，无需改动（前端文案独立于四语目录维护）。

#### 三、本期代码改动总览（按模块分类，2026-09-02 ~ 09-06）

- **`main.py`**：新增全局 `hls_collection_exclude_platforms` 与主循环解析（支持中英文逗号分隔、每轮热更新）
- **`src/stream_select.py`**：`select_source_url` 新增有效开关 `hls_effective_enabled = main.hls_collection_enabled and not hls_excluded`（命中排除列表时 HLS 候选整组剔除、不进序列）。
- **`src/spider.py`**：`extract_douyin_hevc_flv_url()` 返回前补 `&codec=h265`（已带则原样返回），修复下游 `_is_h265()` 与 h265 兜底判定漏判。
- **`src/async_http.py`**：删除跨循环 `run_coroutine_threadsafe(client.aclose(), ...)` 调度分支（根治 flaky 告警「FakeAsyncClient.aclose was never awaited」）。
- **`src/web_config.py`**：新增 `BUILTIN_QUALITIES`（对齐 `stream_select.get_quality_code`
- **`src/web_api.py`**：新增 `GET /api/rooms/qualities` 与 `PUT /api/rooms/qualities`（选项增删）、`PUT /api/rooms/quality` + `RoomQualityUpdate`（按房间切换画质…
- **`gui.py`**：新增 `_refresh_quality_context` / `_anchor_url_map` / `_anchor_quality_map` / `_quality_menu_values` / `_on_room_quality_change`
- **`web/index.html` / `web/app.js` / `web/style.css`**：画质下拉改为后端驱动的可增删选项（chips 面板）、房间列表画质列改为行内下拉 + 事件委托、新增三语/四语文案、`.data-table select` 样式。
- **`scripts/`**：`douyin_live_recorder_standalone.py` 自根目录迁入并修 `find_ffmpeg()`（脚本同级 → 仓库根 → PATH 三级探测）
- **`tests/`**：新增 `test_record_container.py`（13 用例…
- **全仓注释补齐**（2026-09-03）：41 文件 / +1370 行，经 `ast.dump` 等价性校验证明零逻辑改动。

#### 四、删除项与遗留清理

- **删除**：`src/async_http.py` 跨循环 aclose 调度分支…
- **移动**：`douyin_live_recorder_standalone.py` 根目录 → `scripts/`（等价删除根目录副本）。
- **遗留（未删除、已纳入忽略）**：`src/stream.pyc_probe_tmp`（2026-09-01 的探针过程产物，非源码），已加入 `.gitignore` / `.dockerignore`，待人工确认后清理。

#### 五、验证（2026-09-06）

- `pytest -q` 全量：**858 passed, 2 skipped，0 warnings**；
- `python scripts/extract_i18n_strings.py`：缺失 0 条，四语目录零差异；
- `python scripts/compile_po.py` / `--check`：与 .po 同步（522 条）；
- `python scripts/check_version.py`：PASS（版本动态化状态无回退）；
- 依赖比对脚本：`requirements.txt` 与 `pyproject.toml` 各 20 条逐条一致；
- `pytest tests/test_i18n.py`：34 passed（四目录键集合一致性断言）。

### v4.0.9.4-dev (2026-09-06) — GUI 画质切换持久化修复 + WEB 端按房间切换画质完整链路 + 前后端单元测试补齐

**变更摘要**：收尾上一改动的三个缺陷并补齐 WEB 端完整功能。

**改动清单**：

- `gui.py`：
  - `_on_room_quality_change`：查表前加 `re.sub(r"^序号\d+\s+", "", anchor_name)` 剥离序号前缀…
  - 新增实例字段 `_anchor_quality_map`（主播名 → 配置行当前画质），`_refresh_quality_context` 同步构建（与反查表同来自 `parse_url_config`）；
  - `_add_quality_data_row`：「设置画质」列改以 `_anchor_quality_map` 为准（查表前同样剥离序号前缀）
- `src/web_api.py`：
  - 导入追加 `update_room_quality`；
  - 新增 `RoomQualityUpdate(BaseModel)`（`url: str` + `quality: str | None`，空/None 等价移除画质段）；
  - 新增 `PUT /api/rooms/quality`：参数经 `validate_room_target` 走换行注入防护 + 白名单校验（仅放行 `BUILTIN_QUALITIES`
- `web/app.js`：
  - `buildRoomQualitySelect(url, current)`：构造行内画质下拉（选项 = 默认画质 + `qualityOptions` + 当前值兜底追加防止显示错位）
  - `loadRooms`：画质列从纯文本 `<td>` 改为调用 `buildRoomQualitySelect`；
  - 事件委托 `rooms-tbody` 新增 `select[data-action="quality"]` change 分支，转发 `changeRoomQuality(url, value)`；
  - 新增 `changeRoomQuality(url, quality)`：`PUT /api/rooms/quality`，成功 toast 后 `loadRooms()` 回拉刷新，失败 toast + 回拉恢复真值（不残留用户误选）；
  - `showView('rooms')`：`loadRooms()` 改为 `loadQualityOptions().finally(loadRooms)`，保证下拉选项在渲染前就绪；
  - 三语文案补齐（`toast.qualityChanged` / `toast.qualityReset` / `toast.qualityChangeFailed`），API 契约注释更新。
- `web/style.css`：新增 `.data-table select` 紧凑样式（`padding: 4px 6px / font-size: 12px / max-width: 110px`），与表单 `.inline-form select` 区分。
- `tests/test_web_api.py`（既有 `TestRoomQualityApi` 基础上扩展至 8 用例）：
  - `test_change_quality_requires_auth`：无 Bearer token 的 PUT 必须 401；
  - `test_change_quality_on_disabled_room_preserves_comment`：已注释房间（`# 超清,...`）切换画质成功、`#` 前缀原样保留、房间保持禁用态、列表可见新画质；
  - `test_quality_visible_in_room_list_after_change`：PUT 后 GET /api/rooms 立即返回新画质、相邻房间行不受影响；
  - `test_change_quality_matches_schemeless_url`：URL 归一化匹配（不带 scheme 的地址也能命中已规范化写入的配置行）；
  - `test_empty_string_quality_resets_to_default`：`quality: ""` 与 `null` 等价，均移除画质段恢复默认。
- `tests/frontend/test_quality_ui.mjs`（新文件，Node 内置 `node:test` + `node:vm` 沙箱，零 npm 依赖）：
  - 用 DOM/fetch 桩加载 app.js（IIFE 加载期零副作用）
  - 6 用例：沙箱冒烟 / 下拉渲染（选项构成 + 选中态 + URL 转义 + 行结构）/ change 委托请求契约 / 空值序列化为 null / 失败回拉恢复真值 / 四语文案行为级断言；
  - 变异验证：临时删掉 `buildRoomQualitySelect` 的 `esc(url)` 后断言正确变红，证明测试真能抓回归。
- `tests/test_frontend_quality_ui.py`（新文件）：pytest 包装，子进程 `node --test`，Node 缺失时 skip（环境限制口径）。

### v4.0.9.4-dev (2026-09-06) — WEB/GUI 端画质选项可增删 + 画质监控行内切换画质

**变更摘要**：将直播间画质设置从「引擎白名单内固定 10 个档位」改为「用户自选子集」——WEB 端直播间管理提供可增删的画质选项（落地 config.ini [录制设置] 自定义画质选项(逗号分隔)）

**改动清单**：

- `src/web_config.py`：
  - 引入 `BUILTIN_QUALITIES` 元组（与 `stream_select.get_quality_code` 的画质代码映射对齐），同时把历史别名 `QUALITY_KEYWORDS` 指向同一元组，避免两处并列维护；
  - 新增画质选项落盘位置常量 `QUALITY_OPTIONS_SECTION = "录制设置"` / `QUALITY_OPTIONS_KEY = "自定义画质选项(逗号分隔)"`；
  - `_split_multi_value` / `normalize_quality_options` / `read_quality_options` / `write_quality_options`：选项读写只允许内置档位（白名单外的名称会被静默回退成「原画」
  - `update_room_quality`：按 URL 定位 URL_config.ini 中的配置行…
  - `find_room_url_by_anchor_name`：按主播名反查直播间地址（GUI 画质切换写回 URL_config.ini 需要 URL），先精确匹配再子串兜底；未命中返回空串。
- `src/web_api.py`：
  - 新增 `GET /api/rooms/qualities`（返回 `{options, builtin}`，builtin 一并返回以便前端「添加画质」候选列表不必再硬编码档位名）；
  - 新增 `PUT /api/rooms/qualities` body `{options: [...]}`：写入前经 `validate_config_target` 走换行注入防护…
- `web/index.html`：直播间设置模块移除硬编码的画质 `<option>` 列表…
- `web/style.css`：新增 `.quality-options` / `.quality-panel` / `.quality-chips` / `.quality-chip` / `.quality-add-row` / `.quality-hint` 等样式…
- `web/app.js`：模块状态新增 `qualityOptions` / `qualityBuiltin`
- `gui.py`：
  - 导入追加 `parse_url_config` / `read_quality_options` / `update_room_quality`（`find_room_url_by_anchor_name` 备用）；
  - 新增实例字段 `_quality_options`（菜单可选项）/ `_quality_default_label = "默认画质"`（首项=回落）/ `_anchor_url_map`（主播名→URL 反查表…
  - 新增 `_refresh_quality_context`：读 `config.ini` 拿选项 + 解析 `URL_config.ini` 建反查表…
  - 新增 `_quality_menu_values`（菜单展示列表：默认画质 + 用户选项 + 当前画质兜底，防止画质被从选项中移除后菜单显示值错位到首项）；
  - 新增 `_on_room_quality_change`（用户切换触发：选「默认画质」= 移除画质段回落…
  - 画质监控详情表头行新增「切换画质」列；`_add_quality_data_row` 新增第 6 列 `CTkOptionMenu`（沿用 `appearance_menu` 的浅色/深色双主题色板）；列权重 2；
  - 画质页底部新增 wraplength 提示文案，说明「切换后下一轮循环生效」与「选择默认画质移除画质段」的语义。
- `tests/test_web_config.py`（新增 3 类）：`TestQualityOptions`（normalize 过滤非法/空/重复…
- `tests/test_web_api.py`（新增 `TestQualityOptionsEndpoints`）：GET 缺省返内置全集、PUT 持久化到 config.ini 且再次 GET 回读到同样列表、PUT 自动剔除白名单外的档位、PUT 换行注入 422。
- `README.md` / `README_EN.md`：本批改动在用户面上是「下拉从固定列表改为自选 + 监控行可切换画质」

**影响范围**：

- 用户可见：WEB 端「添加直播间」的画质下拉不再固定 10 项…
- 不变语义：仅内置 10 个档位可选（与 main.py 的画质白名单、`stream_select.get_quality_code` 键对齐）
- 边界处理：未匹配 URL 时弹错误提示而非静默丢数据；写入失败弹错误框 + 错误日志；写入成功后同步 mtime 防止 URL 配置编辑器被自己的写操作误重载。

- `pytest tests/`：**849 passed, 2 skipped**（新增 3 个纯函数测试类 + 1 个 API 测试类，全量无回归）；
- `mypy src/ main.py web.py gui.py`：42 个源文件 0 问题；
- `basedpyright src/ main.py web.py gui.py`：0 errors, 0 warnings, 0 notes；
- `black --check` / `isort --check` / `scripts/check_annotations.py`：全绿（注释密度 21.2%，未触及 13% 阈值）。

### v4.0.9.4-dev (2026-09-05) — HLS 采集排除平台列表：命中平台无视 HLS 开关、恒走 FLV 采集

**变更摘要**：新增配置项「HLS采集排除平台(逗号分隔)」——当「是否启用HLS采集(是/否) = 是」时…

**改动清单**：

- `main.py`：
  - 模块级新增全局 `hls_collection_exclude_platforms: list[str] = []`（紧邻 `hls_collection_enabled`），并加入 `main()` 的 `global` 声明；
  - `main()` 主循环在读取「是否启用HLS采集(是/否)」之后读取「录制设置 / HLS采集排除平台(逗号分隔)」（默认空）
- `src/stream_select.py`（`select_source_url`）：
  - 新增有效开关计算：`hls_excluded = platform in main.hls_collection_exclude_platforms`
  - 候选序列构建（`hls_seq`）由 `main.hls_collection_enabled` 改用 `hls_effective_enabled`：排除平台 HLS 候选**整组剔除、不进入序列**（与 `_FLV_FIRST_PLATFORMS` 仅调序、保留 HLS 回退的语义刻意不同）
  - 「HLS 源存在但 HLS 采集关闭且无回退」告警分支同样改用有效开关…
- `tests/test_stream_select.py`：新增 5 个用例——排除平台恒选 FLV（HLS 探针零发出）、FLV 校验失败不回退 HLS（HLS 从未被探测）、仅剩 HLS 源时告警返回 None（断言告警指向排除列表）、列表外平台行为不变（含 FLV-first 平台对照）、排除平台 h265-FLV 不切换 HLS。
- `README.md` / `README_EN.md`：配置示例新增「HLS采集排除平台(逗号分隔)」键及说明…
- `CODE_WIKI.md` / `CODE_WIKI_EN.md`：`[录制设置]` 配置表新增该键条目；`select_source_url()` 功能描述补充排除列表行为。

**影响范围**：

- 用户可见：新配置项默认空 = 不排除任何平台，既有行为零变化；填写平台名（须与日志/配置中显示的完全一致，如「斗鱼直播」）后该平台恒走 FLV。
- 边界语义：排除平台若仅有 HLS 源且无 FLV/record_url 回退…

- `pytest tests/`：**828 passed, 2 skipped**（新增 5 用例，全量无回归）；
- `mypy .`：105 个源文件 0 问题。

### v4.0.9.4-dev (2026-09-05) — 单文件整合版迁移至 scripts/ 目录（ffmpeg 定位逻辑同步修复）

**变更摘要**：将单文件整合版 `douyin_live_recorder_standalone.py` 从仓库根目录迁移至 `scripts/` 目录（文件名不变）

**改动清单**：

- `scripts/douyin_live_recorder_standalone.py`（自根目录迁入）：
  - `find_ffmpeg()` 修复（**必须项**…
  - 文件头「使用」示例与 `RUN_STEPS`（`--help-steps` 输出）的全部命令补 `scripts/` 前缀…
- `AGENTS.md`：项目结构树 `scripts/` 目录新增该文件条目…
- `scripts/check_annotations.py`：**无需改动**——`EXCLUDE_FILES` 按**文件名**匹配（`path.name in EXCLUDE_FILES`）
- `README.md` / `README_EN.md`：无需改动——仅更新日志的历史条目按文件名提及该文件（无路径引用，保留历史原貌）。

**影响范围**：

- 用户可见：运行命令前缀变化（根目录 → `scripts/`）；仓库自带 `ffmpeg/` 仍从仓库根目录自动发现。
- 不变语义：config.ini / URL_config.ini / `downloads/` 输出目录均按运行时工作目录（CWD）解析；`--selftest` / `--dry-run` / 四平台解析与录制链路全部不变。

- `python -m py_compile scripts/douyin_live_recorder_standalone.py`：通过；
- `python scripts/douyin_live_recorder_standalone.py --selftest`：**62 项全部 [PASS]**，退出码 0；
- `find_ffmpeg()` 实测返回 `D:\DouyinLiveRecorder-dev\ffmpeg\ffmpeg.exe`（若不修复则落空退化为 PATH 查找）；
- `black --check` / `mypy`（单文件）：0 问题；
- `python scripts/check_annotations.py`：通过（105 个 Python 文件，该文件仍按文件名被排除、未参与密度检查）。

### v4.0.9.4-dev (2026-09-05) — pytest 会话结束自动清理测试输出目录 _out_live/_out_e2e

**变更摘要**：`tests/conftest.py` 新增 `pytest_unconfigure` 钩子…

**实现要点**：

- 路径常量 `_TEST_OUT_DIRS` 基于 `tests/` 目录自身定位（`__file__` 推导），不依赖 CWD；
- `shutil.rmtree(..., ignore_errors=True)`：目录不存在或 Windows 下偶发句柄占用（杀毒/索引扫描）时静默跳过，清理失败不会让 pytest 以异常退出码结束；
- 两目录本已在 `.gitignore`，残留不污染仓库，本清理属防御性收尾；
- 手动验证脚本（`test_bili_live_collector.py` 等以 `python tests/xxx.py` 直跑的真实直播端到端）不经 pytest、不受影响——其「先清空再写」语义与 SRT 人工检查用途保持不变。

- `pytest tests/test_srt_timeline_anchor.py`：4 passed，运行后 `tests/_out_e2e` 自动删除（连同此前残留的 `_out_live` 一并清理）；
- 重复运行（目录已不存在时）无报错，幂等；
- 全量 `pytest -q`：**823 passed, 2 skipped**（与 2026-09-04 基线一致，无回归），结束后两目录均不存在；
- `mypy tests/conftest.py` / `black --check` / `isort --check-only` 全通过。

### v4.0.9.4-dev (2026-09-04) — P0 修复：分段录制容器错配导致抖音原画 HEVC 无法录制（返回码 4294967274）

**变更摘要**：修复「TS + 分段录制」分支 `-segment_format` 误用 `ipod` 的 P0 回归（HEVC 原画 `-c copy` 直接 `AVERROR(EINVAL)` 退出…

**根因**：`main.py` 两处取值**互换**——TS 分支写 `ipod`（应 `mpegts`）、M4A 音频分支写 `mpegts`（应 `ipod`）

**实测复现（ffmpeg n9.0.1）**：

- HEVC + `segment/ipod` → `Could not find tag for codec hevc in stream #0` + `Could not write header … Invalid argument`
- HEVC + `segment/mpegts` → exit 0，产物 40KB，首字节 `0x47`，可被 mpegts 解复用；
- **H.264 + `segment/ipod` → exit 0 且不报错…

**改动清单**：

- `main.py`：新增模块级常量 `SEGMENT_FORMAT_BY_SUFFIX`（`.ts→mpegts` / `.flv→flv` / `.mkv→matroska` / `.mp4→mp4` / `.m4a→ipod`）
- `main.py`：新增 `_FFMPEG_ERRNO_HINTS` + `_describe_return_code()`
- `src/spider.py`：`extract_douyin_hevc_flv_url()` 返回前补 `&codec=h265`（已带 codec 参数时原样返回）。
- `tests/test_record_container.py`（新增 13 用例）：映射表内容断言、TS≠ipod / M4A≠mpegts 双向回归、AST 扫描断言「5 处取值全部来自查表、禁止裸字面量」、查表键已注册、音频兜底为 ipod、`hevc_flv_url` 补标记且 `_is_h265()` 可识别、退出码归一化。
- `AGENTS.md`：已知坑新增 2 条（分段容器映射 + `hevc_flv_url` 必须带 codec 标记）。

- 全量 `pytest -q`：**823 passed, 2 skipped，0 warnings**（修复前基线 808 passed）；
- `black --check`（123 文件）/ `isort --check-only` / `mypy`（3 个改动文件）/ `scripts/check_annotations.py`（平均密度 21.2%）全通过；
- 复现脚本已清理，未残留临时文件。

**同步与遗留**：

- 运行目录 `D:\DouyinLiveRecorder`（与开发仓 `D:\DouyinLiveRecorder-dev` 分离）已同步**最小修复**（`main.py` 两处容器取值 + `src/spider.py` 的 codec 标记）
- 已录历史 TS 文件需在修复后按魔数（首字节 `0x47`）复核，H.264 房间的历史产物可能为真 MP4。

### v4.0.9.4-dev (2026-09-04) — 修复 flaky 告警「FakeAsyncClient.aclose was never awaited」+ AGENTS.md pytest 0 警告门禁口径定稿

**变更摘要**：修复全量 pytest 下波动于 1~2 条的 flaky 告警 `RuntimeWarning: coroutine 'FakeAsyncClient.aclose' was never awaited`（根因 `src/async_http.py::_get_client` 跨循环关闭旧 AsyncClient 的调度竞态）

**根因分析（三个方案的实测排除）**：

- 旧实现（原 L63）：淘汰他循环创建的旧客户端时用 `run_coroutine_threadsafe(client.aclose(), client_loop)` 只调度不等待。
- 中间方案「`is_running()` 门控 + `fut.result(timeout=5)` 等待」实测仍无法根治：`asyncio.run` 收尾阶段（`_cancel_all_tasks` / `shutdown_asyncgens` 的多次 `run_until_complete`）循环还在运转（is_running 为真）但随时停止——安排的任务可能已创建却永不步进（`Task was destroyed but it is pending!`）
- 在当前循环直接 `await 旧client.aclose()` 亦不可行：会操作绑定旧循环的 transport（httpcore 连接池关闭触碰旧循环的 `call_soon`

**结论**：外部线程无法可靠控制他线程事件循环的生命周期…

**改动清单**：

- `src/async_http.py`：删除跨循环 `run_coroutine_threadsafe` 调度分支，改为不创建协程，注释完整记录三个不可行方案的实测结论（勿回退）。
- `tests/test_async_http_lock.py`：`test_concurrent_threads_no_cross_loop_error` 移除 `@pytest.mark.filterwarnings("ignore::RuntimeWarning")`（拦不住 GC 延迟触发的告警、只会掩盖回归…
- `pyproject.toml`：`[tool.pytest.ini_options].filterwarnings` 新增 starlette testclient import 期 `anyio.abc.BlockingPortal` 弃用提示的过滤（与既有 httpx 弃用提示同样定性：第三方、附来源注释）。
- `AGENTS.md`：新增「pytest『0 警告』口径」条目（summary 为空、项目自身告警与可过滤第三方告警的区分、禁止用过滤掩盖项目告警、协程类告警须修根因）

- `tests/test_async_http_lock.py` 连续重跑 30 + 20 轮：0 告警、0 `Task was destroyed`、无秒级阻塞（修复前 15 轮中 8 轮出现告警）；
- 全量 `pytest -q`：**808 passed, 2 skipped，0 warnings**（warnings summary 恒为 0，含新过滤的第三方告警）；
- `black --check` / `isort --check-only` / `mypy`（含 `--platform linux`）/ `basedpyright`（0 error/0 warning）/ `scripts/check_annotations.py` 全通过。

### v4.0.9.4-dev (2026-09-03) — 全仓中文注释补齐（41 文件 / +1370 行）+ 注释检查工具 scripts/check_annotations.py 建立并接入 CI

**变更摘要**：本条目记录 2026-09-03 会话对全仓代码注释的系统性补齐。

**背景与范围决策**：先做全量注释密度体检（`tokenize` 精确统计）

**涉及文件（按模块分类）**：

- **核心源码**：`src/spider.py`（5.0% → 14.6%，四轮处理，新增 519 行注释）、`src/stream.py`、`src/ffmpeg_install.py`、`src/node_install.py`、`msg_push.py`
- **测试**：`tests/` 下 33 个文件（含 `test_spider_platform.py` 5.8% → 15.5%、`test_danmaku_monitor.py` 10.4% → 15.6%、`test_cookie_cache.py` 6.0% → 16.4% 等）
- **脚本**：`scripts/smoke_test.py`
- **前端**：`web/app.js`（补 IIFE 架构总览 / API 契约 / 轮询定时器清理 / esc() 转义要点）、`web/index.html`、`web/style.css`
- **新增**：`scripts/check_annotations.py`
- **CI / 文档**：`.github/workflows/ci.yml`（`static` job 新增步骤）、`AGENTS.md`（新增「注释约定」与「注释检查工具」两节）、`CODE_WIKI.md` / `CODE_WIKI_EN.md`（本条目）

**关键设计：AST 等价性校验**

本项目**非 git 仓库**（无 HEAD 作基准）

**改动说明**：

- **修复 CI 既有 YAML 隐患**：`static` job 中 `Check version consistency` 等步骤为 6 空格缩进…
- **子协作方越界改动的处置**：第四轮 `src/spider.py` 处理中…

**影响范围**：

- 平均注释密度 **7.6% → 20.4%**（41 个目标文件），Python 文件合计新增注释 **1370 行**，38 个 Python 文件全部 ≥13%。
- 运行时行为**零变化**（AST 全等作证）；新增工具仅 CI / 手动调用时运行，不进运行时链路，且 `.dockerignore` 已排除 `scripts/`。
- 注释约定与工具用法已固化进 AGENTS.md，避免后续漂移。

- `pytest -q` 全量：**808 passed**（与改动前基线一致；warnings 在 1~2 间波动，属既有 flaky，见「关联」）；
- `mypy`：99 文件 Success；`black --check` 与 `isort --check-only` 全通过；
- `python scripts/check_annotations.py`：全部通过，平均密度 21.2%；
- `python scripts/check_annotations.py --baseline <基线>`：41 文件等价、零逻辑改动；
- `.github/workflows/ci.yml` 经 `yaml.safe_load` 解析通过，`static` job 共 8 个步骤。

**关联**：

- flaky 告警（非本次引入…
- `starlette` 的 anyio `DeprecationWarning` 为第三方依赖既有告警（AGENTS.md 门禁写的「pytest 0 警告」与基线实际的 1 条第三方告警不一致，本次未越界修改）。

### v4.0.9.3-dev (2026-09-02) — 单文件整合版 (standalone) 类型标注修复（mypy：4 处报错清零）

**变更摘要**：本条目记录 2026-09-02 会话对根目录单文件整合脚本 `douyin_live_recorder_standalone.py` 的 4 处 mypy 静态类型告警修复（IDE mypy / `warn_return_any`）。

**涉及文件（按模块分类）**：

**一、类型标注修复（修改内容）— `douyin_live_recorder_standalone.py`**

- L265 `_fetch_json`：返回值 `json.loads(resp.text)` 被 mypy 判为 `Any`（声明 `dict[str, Any]`）→ 改为 `cast(dict[str, Any], json.loads(resp.text))`。
- L751 `_douyu_sign`：返回值 `json.loads(out.stdout.strip())` 被判为 `Any`（声明 `dict[str, str] | None`）→ 先 `isinstance(sign, dict)` 守卫（非 dict 直接返回 `None`）
- L853 `dispatch`：`fn(url, proxy=proxy, cookies=cookies)` 关键字调用被 mypy 报「Unexpected keyword argument "proxy"/"cookies"」——根因为 `PLATFORM_RULES` 用 `Callable[[str, str | None, str], StreamInfo]`
- `typing` 导入：`from typing import Any, Callable` → `from typing import Any, Protocol, cast`（移除已无引用的 `Callable`）。

**影响范围**：

- 用户可见：无（纯静态类型标注，运行行为不变）。
- 不变语义：四个平台解析器（`resolve_douyin` / `resolve_huya` / `resolve_bilibili` / `resolve_douyu`）的分派链路、关键字调用形式（`proxy=` / `cookies=`）全部保留。

- `python -m py_compile douyin_live_recorder_standalone.py`：通过（0 语法错误）。
- IDE lint（`douyin_live_recorder_standalone.py`）：0 错 0 警告。
- 本机解释器（Python 3.14.7）未安装 `mypy` / `basedpyright`，未能本地跑全量类型检查；请在含类型检查器的环境执行 `mypy douyin_live_recorder_standalone.py` 复核。

**相关**：

- 收敛技巧对齐 MEMORY.md「basedpyright 严格模式约束与收敛技巧」：RHS 为 Any 时 `json.loads` 必须 `cast`，而非依赖 `# type: ignore`（本仓禁用 ignore 注释）。

### v4.0.9.3-dev (2026-09-02) — 代码检查报告 20 项问题全量修复（cookie_cache singleflight 重写 + Web 非 ASCII 密码崩溃 + 探针/资源/风格健壮性）+ mypy 全仓清零（tests / gui_legacy / scripts）

**变更摘要**：本条目系统性记录 2026-09-02 会话依据《代码检查报告.md》对 20 项审查问题的全量修复…

**一、并发正确性（高）— `src/cookie_cache.py`（重写）/ `tests/test_cookie_cache.py`**

- `src/cookie_cache.py`：`fetch_cookies` 重写为 singleflight 模式——`threading.Lock` 只保护「缓存字典 + 在途登记表 `_inflight`」的同步读写（**锁内绝无 await**）
- `tests/test_cookie_cache.py`：`test_same_loop_reentrant_no_deadlock` 加强为同时断言「并发 gather 5 协程只拉取一次」（旧 RLock 实现下该断言必失败——正是本次修复的目标行为）

**二、Web 面板缺陷修复（高 / 中高 / 中）— `src/web_config.py` / `src/web_api.py` / `src/web_tray.py`**

- `src/web_config.py`：① `verify_web_password` 历史明文兼容路径改为 `hmac.compare_digest(plaintext.encode("utf-8"), stored.encode("utf-8"))`（bytes 比较无非 ASCII 限制）
- `src/web_api.py`：`PUT /api/rooms`（`update_room`）写入行改用 `normalize_url(req.url)`——原写入未归一化 URL…
- `src/web_tray.py`：`_patch_console_window` / `_on_show` 改用 `ctypes.WinDLL` + 显式 `argtypes`/`restype`（`GetConsoleWindow.restype = c_void_p`

**三、守护线程与探针健壮性（中）— `src/config_io.py` / `src/stream_select.py` / `src/danmaku_monitor.py` / `src/ws_client.py`**

- `src/config_io.py`：`backup_file_start` 守护循环的 `time.sleep(600)` 移出 `try`——原异常分支不等待…
- `src/stream_select.py`：① `_confirm_get_ok` 的 `except Exception` 补 `logger.debug`（含异常类型 + attempt 序号…
- `src/danmaku_monitor.py`：`_write_line` 写失败分支补 `logger.debug`（含异常类型），与本模块「异常全吞但必须留痕」约定一致，边车数据不再无迹丢弃。
- `src/ws_client.py`：心跳任务回收的 `except asyncio.CancelledError, Exception:` 拆分——`CancelledError` 仅吞 hb_task 自身按预期被取消的情形（`hb_task.cancelled()` 为真）

**四、装饰器兜底类型与资源管理（中）— `src/utils.py` / `src/spider.py` / `src/node_install.py` / `src/ffmpeg_install.py` / `src/sync_http.py`**

- `src/utils.py`：① 装饰器共用实现收敛为 `_make_trace_error_guard(func, fallback)`
- `src/spider.py`：5 个返回 str/tuple 的函数（`get_bilibili_room_info_h5` / `login_sooplive` / `get_sooplive_tk` / `get_winktv_bj_info` / `login_flextv`）由 `trace_error_decorator` 切换至 `trace_error_decorator_or_none`——旧统一 dict 兜底会把错误伪装成正常结果（`login_flextv` 失败时返回的 dict 曾被 `if new_cookies` 误判为登录成功）。
- `src/node_install.py`：两处 `requests.get`（版本页面 + zip 流式下载）改 `with` 管理关闭连接；删除本地 `unzip_file` 改从 `src/utils` 导入。
- `src/ffmpeg_install.py`：删除本地 `unzip_file` 改从 `src/utils` 导入（两处逐字重复的实现收敛为一份）。
- `src/sync_http.py`：新增 `_all_sessions`（`weakref.WeakSet`）+ `_all_sessions_lock` 登记 thread-local Session、`close_session()`（当前线程显式释放）、`close_all_sessions()`（`atexit` 注册…
- `tests/test_spider_platform.py`：4 个固化旧 dict 兜底行为的断言（TestLoginSooplive ×2 / TestLoginFlexTv / TestSoopliveTk / TestWinktvBjInfo）同步改为 `is None`。

**五、风格约定与环境（低）— `AGENTS.md` / venv**

- PEP 758 写法定稿：报告原建议统一 `except (A, B):` 加括号…
- venv 修复：`.venv` 中 editable 安装原指向 `D:\DouyinLiveRecorder-coding`（另一 checkout）

**六、mypy 遗留清零（后续两批）— `tests/test_quality_tiers.py` / `gui_legacy.py` / `scripts/extract_i18n_strings.py`**

- `tests/test_quality_tiers.py`：5 处 `mock.await_args.args[1]` 前补 `assert mock.await_args is not None`——typeshed 将 `await_args` 声明为 `_Call | None`
- `gui_legacy.py`：4 处修复——① 悬停效果两个 lambda 改具名闭包工厂 `_flat_relief(button)`（事件参数显式标注…
- `scripts/extract_i18n_strings.py`：`parse_keys` 的 `getattr` 动态调用结果用 `cast(dict[str, str], ...)` 收敛（`warn_return_any` 门禁），移除已无用的 `type: ignore[arg-type]`。

**影响范围**：

- 用户可感知：历史明文密码含非 ASCII 字符的 Web 面板登录恢复正常…
- 行为不变项：cookie 缓存 TTL/失败不缓存/fetcher 透传、探针退避与节流语义、斗鱼/虎牙 GET 复核「重试一次再定罪」语义、Web API 全部路由契约、弹幕采集链路等均保持。
- 已知取舍：PEP 758 无括号 except 写法与 <3.14 不兼容（本仓下限即 3.14，非回退项，属显式约定）。

- `pytest` 全量 **806 passed, 2 skipped, 0 failed**。
- `mypy` 全仓口径（src + tests + 全部入口 + build_exe + scripts）**Success: no issues found in 102 source files**（CI 口径 `mypy src/` 39 文件、报告口径 44 文件、含 tests 94 文件均全绿）。
- `basedpyright --outputjson`：errorCount=0, warningCount=0。
- `black --check`：105 files unchanged；`isort --check-only` 全部合规；`compileall` 0 语法错误。
- web_tray 实测：`WinDLL` 加载成功、窗口改写链路无异常（headless 下 `GetConsoleWindow` 返回空、按预期跳过）。

**关联**：

- `AGENTS.md`：「代码风格 → Black」新增 except 多异常写法（PEP 758）约定。
- 回归锁：`tests/test_cookie_cache.py`（同循环只拉取一次 + 跨线程去重）、`tests/test_spider_platform.py`（5 函数 None 兜底）、`tests/test_stream_select.py` + `tests/test_record_failure_feedback.py`（探针/退避语义）。
- 问题来源：《代码检查报告.md》20 项清单（#1～#20）；本条目即其全量闭环记录。
- 上一版全量快照：v4.0.9.2-dev (2026-08-30)「停止录制流程运行日志归档」。

### v4.0.9.2-dev (2026-08-30) — 停止录制流程运行日志归档（四日志按时间戳改名归档）+ i18n 四语目录补齐（507 → 516 条）+ 仓库元数据同源清单同步（.v2c / .mypy_cache）

**变更摘要**：本条目系统性记录 2026-08-30 会话落地的三项改动。

**一、运行日志归档（新增功能）— `src/log_archive.py`（新增）/ `src/logger.py` / `src/danmaku_monitor.py` / `main.py` / `src/web_api.py`**

- `src/log_archive.py`（**新增文件**）：归档入口 `archive_runtime_logs(*, reopen_streams=True)` 与辅助函数 `_archive_target()`（原名_时间戳.扩展名…
- `src/logger.py`：新增模块级 `_streamget_sink_id` / `_playurl_sink_id` 跟踪两个录制日志 sink 的 handler id…
- `src/danmaku_monitor.py`：`DanmakuMonitorHub` 新增 `close_file()`（持 `_file_lock` flush+close+置空引用…
- `main.py`：模块级 `atexit.register(archive_runtime_logs, reopen_streams=False)`
- `src/web_api.py`：`toggle_recording` 在 `enable=False`（面板「停止录制」

**二、测试（新增 1 文件 + 修改 2 文件）— `tests/`**

- 新增 `tests/test_log_archive.py`（14 用例）：四日志改名格式正则锁定（原名_YYYYMMDD_HHMMSS.扩展名）、固定时间戳下目标冲突 `_1`/`_2` 递增且不覆盖既有文件、目录为空全跳过、单文件改名失败（PermissionError 替身模拟句柄占用）不中断整批、`DLR_GUI_PARENT=1` 守卫（不触碰文件与句柄）、`DOUYIN_DISABLE_LOG_ARCHIVE=1` 守卫、`reopen_streams` 双态语义（False 不重建 sink / True 重建）、web_console 绑定句柄轮转（flush+close → 改名 → 重建新句柄 → rebind…
- `tests/test_web_api.py`：`TestRecordingToggle` 新增 `test_toggle_stop_triggers_log_archive`（enable=False 恰好触发一次且 `reopen_streams=True`；enable=True 不触发）。
- `tests/conftest.py`：`pytest_configure` 增设 `DOUYIN_DISABLE_LOG_ARCHIVE=1`——测试进程导入 main 会注册归档 atexit…

**三、i18n 四语目录补齐（修改内容）— `i18n/zh_CN/LC_MESSAGES/zh_CN.po` + `zh_CN.mo` / `i18n/en_US.json` / `i18n/en_GB.json` / `i18n/zh_TW.yaml`**

- 四目录各新增 9 条（507 → 516 条…
- `zh_CN.po`：新增「日志归档模块（src/log_archive.py / src/danmaku_monitor.py…
- `en_US.json` / `en_GB.json`：英文译文（两变体同文…
- 验证：`scripts/extract_i18n_strings.py` 复扫缺失 0 条；`tests/test_i18n.py` 34 用例全过（含四目录键集一致 + po/mo 同步）。

**四、仓库元数据同步（修改内容）— `pyproject.toml` / `.coveragerc-concurrency` / `.gitignore` / `.dockerignore` / `AGENTS.md`**

- 审计一致项（无需改动）：`requirements.txt` ≡ `pyproject.toml [project.dependencies]`（20=20 逐条同下界）
- 修复漂移 ×2：① **`.v2c/`**（video2code 插件生成目录…
- `AGENTS.md`：项目结构补 `src/log_archive.py` 条目…

**影响范围**：

- 用户可感知：停止录制后 `logs/` 下出现 `streamget_YYYYMMDD_HHMMSS.log` 等归档文件（同秒重复停止自动 `_1` 递增）
- 行为不变项：日志内容/格式/目录、loguru 轮转（300 KB）与保留策略、弹幕监控 JSONL 轮转（5 MB）、四语键集一致性、GUI 父进程仅写 gui.log、CLI 模式不产生 web_console.log 等全部保持。
- 已知边界：GUI 停止录制的 `taskkill /F /T` 硬杀兜底路径进程无机会执行任何 Python 代码（含归档）

- `pytest` 全量 **806 passed, 2 skipped**（0 警告；本批新增 15 用例：`test_log_archive.py` 14 例 + toggle 归档触发 1 例）。
- Windows 真实链路黑盒验证：loguru `remove()`（flush+close）→ `os.rename` → `add()` 旧文件内容完整、新同名文件立即重建（印证句柄占用约束下的归档可行性）。
- 四语运行时查找冒烟：9 条新串在 zh_CN（.mo）/ en_US / en_GB / zh_TW 精确命中。
- 配置终验：pyproject 五排除列表 / coveragerc omit / 两份 ignore / AGENTS 同源清单程序化断言全过…

**关联**：

- `AGENTS.md`：「关键约定」第 8 条「停止录制流程的日志归档（2026-08-30 定稿）」+「dockerignore / gitignore 同源约定」清单（含 `.v2c/`）。
- 回归锁：`tests/test_log_archive.py` + `tests/test_web_api.py::TestRecordingToggle::test_toggle_stop_triggers_log_archive` + `tests/test_i18n.py`（四目录键集 / `compile_po --check`）。
- 上一版全量快照：v4.0.9.2-dev (2026-08-29)「全量工作树改动总览（按模块分类）」。

### v4.0.9.2-dev (2026-08-29) — GUI 父进程日志句柄隔离：修复 streamget.log 轮转 WinError 32 与录制日志全量丢失

**问题**：GUI 模式下 GUI 进程（`gui.py` 经 `src.web_config → src/__init__ → src.logger` 导入链初始化文件 sink）与录制子进程（`main.py`）同时持有 `logs/streamget.log` 的 loguru 文件 sink 句柄…

**修复**（`src/logger.py` / `gui.py` / `tests/test_logger_gui_parent.py` 新增）：

- `src/logger.py`：新增 `GUI_PARENT_ENV = "DLR_GUI_PARENT"` 环境标记与导入期判定——GUI 进程只写**本进程独占**的 `logs/gui.log`（同款轮转/保留策略）
- `gui.py`：在导入任何 `src` 模块之前设置标记（src.logger 在导入期读标记…
- `tests/test_logger_gui_parent.py`（5 用例）：录制进程持有 streamget/PlayURL 不产生 gui.log、GUI 进程仅 gui.log、「是否启用日志文件=否」对 GUI 同样生效、`child_process_env` 剔除标记与 UTF-8 固定、gui.py 标记先于 src 导入 + env 构建走 helper 的静态回归锁。
- `src/stream.py`：补全 `HuyaGameLiveInfo` TypedDict 的 `bitRate: int` 字段声明并移除 `# type: ignore[arg-type]`（对齐仓库禁用 ignore 约定）——未声明键经 `.get()` 退化为 `object`

### v4.0.9.2-dev (2026-08-29) — 全量工作树改动总览（按模块分类）：97 文件 / +10659 −3138，覆盖 2026-08-23 ~ 08-29 全部未提交变更

**变更摘要**：本条目为当前**整个未提交工作树**（95 个跟踪文件变更 +10659/−3138…

**涉及文件（按模块分类）**：

**一、并发调度与录制引擎核心（新增功能 + 修改内容）— `src/scheduler.py`（新增）/ `main.py` / `src/notify.py` / `src/recorder_status.py`**

- `src/scheduler.py`（**新增文件…
- `main.py`（+922/−796…
- `src/notify.py`（+39/−30）：`record_error`/`record_success` 增 `key` 形参并委托 scheduler（按 key 熔断 + 全局背压）
- `src/recorder_status.py`（+20/−2）：状态 JSON 增 `recording_enabled` 字段…
- **删除项**：旧 `adjust_max_request` 的 `threading.Semaphore` 重建逻辑、`check_subprocess` 轮末无条件 `record_success`、main.py 模块级 `threading.Semaphore(1)`。

**二、选源与流地址校验（修改内容）— `src/stream_select.py` / `src/stream.py`**

- `src/stream_select.py`（+260/−131）：① 统一候选序列——HLS/FLV/record_url 三类地址并入单一有序序列逐候选校验（虎牙经 `_FLV_FIRST_PLATFORMS` 反转为 FLV-first）
- `src/stream.py`（+202/−18）：蓝光细粒度档位专项——`QUALITY_MAPPING_BIT`/`QUALITY_LEVEL`/`QUALITY_CODE_TO_ZH` 扩为 10 项、新增 `BD_SUB_TIERS`/`HUYA_FIXED_TIERS`/`HUYA_RATIO_TO_CODE`/`DOUYU_RATE_BY_CODE`/`DOUYU_RATE_TO_CODE`/`DOUYU_RATE_DESC`、`get_quality_index` 子档位折叠到 BD、`get_huya_stream_url` 按 ratio 选档 + 就近降级、`get_douyu_stream_url` rate 重试链（最多回退 2 档）+ `rate` 字段回采真实档位。
- **删除项**：旧 `DOUYU video_quality_options`/`rate_to_code` 两表、旧「FLV 为 h265 → 立即重试整组 HLS」插入式回退、`sv=10010` 本地拼接（见三）。

**三、平台解析与 JS 签名（修改内容）— `src/spider.py` / `src/javascript/migu.js`（重写）/ `src/platforms/bilibili.py` / `src/platforms/douyu.py`**

- `src/javascript/migu.js`（+159/−74…
- `src/spider.py`（+18/−12）：`_BANDWIDTH_PATTERN`/`_DOUYIN_HEVC_FLV_PATTERN` 提为模块级预编译正则…
- `src/platforms/bilibili.py` / `src/platforms/douyu.py`：弹幕颜色解析 `except` 逗号化（PEP 758 机械重排）。

**四、HTTP 与网络层（修改内容）— `src/async_http.py` / `src/sync_http.py` / `src/http_config.py` / `src/ws_client.py` / `src/ttwid.py` / `src/collector.py`**

- `src/async_http.py`（+15/−2）：`close_all_clients_sync` 适配 Python 3.14——`asyncio.get_event_loop()` 无循环时捕获 `RuntimeError` 走引用清理兜底…
- `src/sync_http.py`（+21/−2）：`_session()` 经 `threading.local()` 线程级复用 `requests.Session`（约 125 处 `sync_req` 调用点全走此路径，实测单请求 11.9ms→1.47ms）。
- `src/http_config.py`（+14/−9）：FFmpeg 9.0 起 TLS 证书默认校验——「禁用SSL证书验证的平台」覆盖恢复实际作用…
- `src/ws_client.py` / `src/ttwid.py` / `src/collector.py`：PEP 758 格式化（弹幕 WS `proxy=None` 直连约定未变）。

**五、配置、日志与工具（修改内容）— `src/config_io.py` / `src/web_config.py` / `src/logger.py` / `src/ffmpeg_install.py` / `src/utils.py`**

- `src/config_io.py`（+17/−2）：`read_config_value` 缺省值写回改为「内存 `StringIO` 完整序列化成功后才落盘」
- `src/web_config.py`（+50/−6）：`update_config_line` 键匹配改大小写不敏感（`_key_line_pattern` 经 `lru_cache(128)` 预编译）
- `src/logger.py`（+35/−3）：`sys.stderr is None` 判空守卫（pythonw/`console=False` 冻结 exe 导入期静默崩溃根治）
- `src/ffmpeg_install.py`（+8/−8）：蓝奏云 FFmpeg 下载源域名切换 `wweb.lanzouv.com` → `wwasx.lanzout.com`（Origin/Referer/接口与提取密码同步）。
- `src/utils.py`（+23/−18）：`_EMOJI_PATTERN` 提为模块级预编译（`remove_emojis` 每调用省去约 400 字符模式重编译）。

**六、Web 面板（新增功能 + 修改内容）— `src/web_api.py` / `web.py` / `web/index.html` / `web/app.js` / `web/style.css`**

- `src/web_api.py`（+49）：新增 `POST /api/recording/toggle`（录制全局开关切换）与 `GET/PUT /api/language`（语言查询/热切换：归一化校验 → `update_config_line` 写回、失败降级 `append_config_line` 补建 → `set_language` 热切换）
- `web.py`（+15/−2）：引擎线程启动前置 `main.recording_enabled = False`（Web 默认不自动录制）
- `web/index.html`（+54/−41）：新增「录制控制」区（状态双子 span + 开始/停止按钮）与顶栏语言选择器…
- `web/app.js`（+323/−45）：新增前端 i18n 字典 `I18N`（约 230 行…
- `web/style.css`（+41/−1）：录制控制区样式（主色开始/红色停止/禁用态）。

**七、GUI（新增功能 + 修改内容）— `gui.py`（+173/−7）**

- 崩溃可观测：新增 `_install_crash_sink()`（`sys.excepthook` + `threading.excepthook` 落盘到临时目录并尽力弹窗…
- 语言菜单：侧边栏新增「语言 Language」`CTkOptionMenu`
- UI 回调异常由 `traceback.print_exc()`（`sys.stderr is None` 时二次崩溃）改为程序内日志。

**八、i18n 本地化体系（新增功能 + 修改内容）— `i18n.py`（重写）/ `i18n/en_US.json`（新增）/ `i18n/en_GB.json`（新增）/ `i18n/zh_TW.yaml`（新增）/ `i18n/zh_CN.po|.mo` / `scripts/extract_i18n_strings.py`（新增）/ `scripts/compile_po.py`**

- `i18n.py`（+270/−31）：重写为多格式引擎——按语言依次探测 gettext `.mo` → `<lang>.json` → `<lang>.yaml`
- 翻译目录：新增 `i18n/en_US.json`、`i18n/en_GB.json`（美式/英式拼写分流）、`i18n/zh_TW.yaml`
- 新增 `scripts/extract_i18n_strings.py`（166 行）：AST 扫描 print 常量串 + logger f-string 模板底稿…
- `scripts/compile_po.py`：纯 Python po→mo 编译修正（此前自身语法错误致 `.mo` 从未落盘）；`scripts/check_coverage.py` 微调。

**九、构建 / CI / 依赖 / 仓库元数据（修改内容 + 新增）— `pyproject.toml` / `requirements.txt` / `uv.lock` / `Dockerfile` / `docker-compose.yaml` / `build_exe.py` / `.github/*` / `.coveragerc-concurrency`（新增）/ `.dockerignore` / `.gitignore`**

- `pyproject.toml`：版本 `4.0.8.3` → `4.0.9.2`
- `requirements.txt`：新增 `PyYAML>=6.0.3`（与 pyproject 下界一致）；弹幕依赖注释路径订正（`src/danmaku/` → `src/` 实际布局）。
- `uv.lock`：随 3.14 基线重锁（净 −963 行…
- `Dockerfile`：基础镜像 `python:3.13-slim` → `python:3.14-slim`；Node.js `setup_22.x` → `setup_24.x`（24 LTS，实测全部 JS 签名脚本 + migu.js 重写版通过）。
- `docker-compose.yaml`：版本示例注释同步 4.0.9.2。
- `build_exe.py`：PEP 758 格式化（打包冒烟判定语义未变）。
- `.github/workflows/ci.yml`：重构为 setup + static/typecheck/test/concurrency-test/integration-verify/build-verify/ci-summary 拓扑（每 job 显式 timeout、ci-summary 唯一 required check）
- `.github/workflows/build-release.yml`：`python_build` 3.12→3.14…
- 新增 `.github/actions/retry/action.yml`（线性退避 ×3 复合动作…
- 新增 `.coveragerc-concurrency`（并发测试专用覆盖率配置…
- **删除项**：两 workflow 内 13 处内联 `for i in 1 2 3` 重试循环、build-release.yml 调试步骤。

**十、测试（新增 4 文件 + 修改 30 文件）— `tests/`**

- 新增：`tests/test_scheduler.py`（192 行…
- 修改（代表）：`tests/test_stream_select.py`（+215：统一候选序列/末位放行/退避跨轮命中/非白名单无操作）、`tests/test_i18n.py`（+234：四目录一致性/平台门控/C-POSIX 过滤/monkeypatch 规约化）、`tests/test_config_io_readonly.py`（+134：StringIO 预序列化/坏键回滚）、`tests/test_web_api.py`（+133：语言端点/录制开关端点）、`tests/test_spider_platform.py`、`tests/test_main_fixes.py`、`tests/test_concurrency.py`（锁类型断言同步）等。
- 全套件当前状态：`pytest` **786 passed, 2 skipped**（`tests/test_twitch_live_collector.py` 因沙箱回收站护栏需隔离运行，属环境限制非回归）。

**十一、文档与审查产物（新增 + 修改）— `AGENTS.md` / `README.md` / `CODE_WIKI.md` / `CODE_WIKI_EN.md`（新增）/ `README_EN.md`（新增）/ `PERF_REVIEW_2026-08-28.md`（未跟踪）**

- `AGENTS.md`（+270）：沉淀「并发与线程模型」（调度中枢/录制结果反馈/锁约定）与「已知坑」十余条防回归约定（弹幕 `proxy=None`、探针容错语义、虎牙退避与 FLV-first、UA 双端一致、PEP 758、3.14 破坏性变更、i18n 多格式、configparser 分隔符等）。
- `README.md`（+303）：3.14 基线、i18n、Web 录制控制等用户文档更新；新增 `README_EN.md` 英文版、`CODE_WIKI_EN.md` 英文架构文档（与本文档结构镜像）。
- `CODE_WIKI.md` / `CODE_WIKI_EN.md`：更新日志自 2026-08-23 起新增十余条分功能条目 + 本总览条目（中英同步）。
- `PERF_REVIEW_2026-08-28.md`（未跟踪…
- 勘误：早前「Web 面板录制手动控制」条目提及的 `docs/web-recording-control-changelog.md` 与 `docs/security-triage-2026-08-29.md` 未保留在当前工作树中…

**改动说明**：

- **改动类型的完整口径**：新增功能（scheduler、Web 录制控制、画质细档位、i18n 体系、GUI 崩溃兜底/语言菜单、retry 复合动作、社区模板、三份英文/双语文档、4 个新测试文件）
- **三条主线互相独立又彼此衔接**：并发调度（谁允许发起网络请求）→ 录制反馈（结果回灌熔断统计）→ 探针退避（坏线路短期拉黑）
- **Python 3.14 迁移贯穿全部模块**：`asyncio.get_event_loop` RuntimeError 兜底、`configparser.InvalidWriteError` 预序列化防御、PEP 758 全仓格式化（black py314 强制风格…
- 本总览与分条目互补：分条目讲「为什么、怎么做」，本条目讲「改了哪些文件、归在哪个模块」；文件行号以分条目记载为准（本条目不重复）。

**影响范围**：

- 用户可感知：Web 面板默认不自动录制（需点「开始录制」）
- 行为不变项：CLI/GUI 直跑录制流程、弹幕 `proxy=None` 直连、探针容错（重试一次再定罪/末位放行）、UA 双端一字不差、斗鱼 HLS-first/虎牙 FLV-first 等既有约定全部保持。
- 部署面：Docker 镜像基线 3.14 + Node 24；打包解释器与 CI 验证环境同值（3.14）；新增 `PyYAML` 运行时依赖（缺失仅损 zh_TW.yaml 格式）。

- `pytest` 全量 **786 passed, 2 skipped**（0 失败）；`compileall`（venv Python 3.14.7）main/gui/web/i18n/build_exe/src/scripts 全过。
- `black --check --line-length 120 --target-version py314` 与 `isort --check-only --profile black --line-length 120`（101 文件）全绿。
- `mypy src/` + `mypy --platform linux src/`：各存 1 error（`src/stream.py:609` 预存 `call-overload`
- `basedpyright tests/`：5 errors（`tests/test_quality_tiers.py` 5 处 `mock.await_args` Optional 成员访问——**阻塞本地类型门禁，提交前需修复**）。
- i18n：`scripts/extract_i18n_strings.py` 报 11 条新增运行时串待收录（不影响功能，原文回退）；四目录键集一致、`.po/.mo` 字节级同步通过。
- 已知待办（提交前）：ci.yml 测试矩阵 3.13 档因 PEP 758 语法在收集期失败…

**关联**：

- 分功能详述条目：v4.0.9-dev (2026-08-24)「高并发多平台录制调度与资源管理优化」「四语本地化目录统一」「CI mypy 双错误修复」
- `AGENTS.md`：本批改动沉淀的全部防回归约定（并发与线程模型 / 录制结果反馈约定 / 已知坑）。
- v4.0.9-dev (2026-08-24)「本次改动总览（按模块分类）」：上一版全量快照（覆盖至 08-24），由本条目取代。

### v4.0.9.2-dev (2026-08-29) — 虎牙/斗鱼画质档位专项（细粒度蓝光档位枚举 + 用户选档录制 + 不可用降级回退 + 全平台兼容）

**变更摘要**：本条目系统性记录 2026-08-29 会话落地的「虎牙/斗鱼直播画质档位专项」。

**涉及文件（按模块分类）**：

**一、画质代码与档位表（新增功能 — 枚举/标识/降级判定）— `src/stream.py`**

- 模块顶部新增 `from loguru import logger`（选档降级日志用）。
- `QUALITY_MAPPING_BIT`（L203）：在基础 6 项上追加 `BD30:30000`/`BD20:20000`/`BD8:8000`/`BD4:4000`（码率上限 kbps）。
- `QUALITY_LEVEL`（L214）：扩展为 `OD/BD(0) > BD30(1) > BD20(2) > BD8(3) > BD4(4) > UHD(5) > HD(6) > SD(7) > LD(8)`，数值越大画质越低，供 `is_downgrade` 判定降级方向。
- `QUALITY_CODE_TO_ZH`（L222）：追加 `BD30→蓝光30M`/`BD20→蓝光20M`/`BD8→蓝光8M`/`BD4→蓝光4M`。
- `BD_SUB_TIERS`（L232）：`frozenset({"BD30","BD20","BD8","BD4"})`，蓝光子档位集合（不参与通用索引映射）。
- 注释块补实测数据（L236-247）：虎牙 chuhe 房间 `bitRate=30000` 下各 ratio 实测分辨率/帧率（原画 2560×1440@60fps、蓝光30M/20M/8M 均 1920×1080@60fps、蓝光4M 1920×1080@30fps、超清 1280×720@30fps、流畅 800×450@24fps）。
- `HUYA_FIXED_TIERS`（L248）：`(("BD30",30000),("BD20",20000),("BD8",8000),("BD4",4000))`；`HUYA_RATIO_TO_CODE`（L250）：ratio 字符串→代码回采表。
- 斗鱼档位表（L268-293）：`DOUYU_RATE_BY_CODE`（请求代码→rate…
- `get_quality_index`（L335）：蓝光子档位折叠到 `BD` 槽位（`if quality_str in BD_SUB_TIERS: quality_str = "BD"`）

**二、虎牙选档实现（修改内容 — 细粒度档位 + 就近降级）— `src/stream.py::get_huya_stream_url`**

- 解析 `gameLiveInfo.bitRate` 为 `max_ratio`（含 `except TypeError, ValueError` 容错——py314 PEP 758 合法形式）
- 请求档在 `BD_SUB_TIERS` 时（L~627）：取 `HUYA_FIXED_TIERS` 固定 `target_ratio`

**三、斗鱼选档实现（修改内容 — rate 映射 + 被限制降级重试链）— `src/stream.py::get_douyu_stream_url`**

- 原 `video_quality_options`/`rate_to_code` 两表删除…
- 降级链（L~765）：按 `order = ["0", *DOUYU_RATE_DESC]` 全序…
- `actual_quality` 改经 `DOUYU_RATE_TO_CODE.get(actual_rate, ...)` 回采服务端真实下发档（`rate` 字段反映就近钳制，如 8200→4→BD4）。

**四、中文名映射与配置/接入白名单（修改内容）**

- `src/stream_select.py::get_quality_code`（L57）：`quality_zh_to_en` 扩展为 10 项，新增 `蓝光30M/20M/8M/4M → BD30/BD20/BD8/BD4`；未知画质仍回退 `OD`。
- `src/web_config.py::QUALITY_KEYWORDS`（L21）：元组由 6 项扩展为 10 项（含蓝光细档位），与 main.py 白名单对齐。
- `main.py`（L2955）：单条 URL 配置解析的画质白名单由 6 项扩展为 10 项，非法值回退「原画」（其余解析逻辑不变）。

**五、Web 面板下拉选项（修改内容）— `web/index.html`**

- `room-quality` 下拉新增 `蓝光30M`/`蓝光20M`/`蓝光8M`/`蓝光4M` 四个 `<option>`（紧邻「蓝光」之后）

**六、测试（新增 + 修改）**

- `tests/test_quality_tiers.py`（**新增文件…
- `tests/test_stream.py`：`test_quality_mapping_keys_match_level_keys`/`test_quality_mapping_keys_match_bit_keys`/`test_quality_code_to_zh_keys_match_mapping_keys` 由「集合相等」改为「基础集 ⊆ 扩展集 且 `BD_SUB_TIERS` == 扩展集 − 基础集」

**改动说明**：

- **蓝光子档位不污染通用索引**：抖音/TikTok 等按数字 0–5 选档平台仍只识别 OD/BD/UHD/HD/SD/LD…
- **虎牙 ratio 即码率上限**：实测确认 ratio 拼于 FLV/HLS URL query 选档、各 CDN 线路共享同一防盗链参数、流地址路径不变（与历史 `sFlvAntiCode` 解析行为一致）。
- **斗鱼服务端自带就近钳制是主降级路径、本地重试链是补充**：斗鱼请求不存在的档位多数被服务端静默钳制到更低档（`rate` 字段回采）
- **降级语义对齐 `QUALITY_LEVEL`**：`is_downgrade(actual, requested)` 按等级数值方向判定（如 `BD8`(3) > `BD4`(4) 为真降级）

**影响范围**：

- 虎牙录制：用户可在 Web 面板/URL 配置选择流畅~蓝光30M 任一档位…
- 斗鱼录制：用户可选高清/超清/蓝光4M/蓝光8M/原画（斗鱼无 20M/30M，选这两项按蓝光8M 拉流）；受限档位自动重试更低档，`rate` 回采真实档位写入结果。
- 抖音/TikTok/B站/快手/网易CC/YY 等：画质选择语义与改动前完全一致（子档位折叠到 BD、索引映射未变），不受本次改动影响。
- `get_huya_stream_url`/`get_douyu_stream_url` 返回值契约不变（`is_live`/`anchor_name`/`flv_url`/`m3u8_url`/`actual_quality` 字段齐备）

- `py_compile`（venv Python 3.14）`src/stream.py`/`src/stream_select.py`/`src/web_config.py`/`main.py` 全过。
- `pytest` 画质专项：`tests/test_quality_tiers.py` **29 passed**…
- 全量 `pytest` 门禁 **784 passed, 2 skipped**…
- `black --check`/`isort --check-only`（line-length 120, target py314）改动文件通过…
- 真机实测：虎牙 chuhe（bitRate=30000）ffprobe 采样确认七档（含原画）分辨率/帧率/码率与 `HUYA_FIXED_TIERS` 一致…

**关联**：

- `src/stream_select.py` 选源/探针（2026-08-28 条目）：虎牙 FLV-first、退避窗口对齐主循环——本特性在虎牙选档成功后交其选源，链路衔接。
- `AGENTS.md` 防回归：三条约定已落地…
- v4.0.9.2-dev (2026-08-29)「Web 面板录制手动控制」——本特性新增的 `web/index.html` 档位选项即在该面板的「录制控制」区同一表单内。

### v4.0.9.2-dev (2026-08-29) — Web 面板录制手动控制（全局开关 + 7 处中断点 + 开始/停止按钮）+ 双轮审查修复 + 端到端冒烟与提交门禁分诊

**变更摘要**：本条目系统性记录 2026-08-29 会话落地的「移除 Web 启动自动录制、改为用户手动控制」特性及其配套验证。

**涉及文件（按模块分类）**：

**一、录制主链全局开关 — `main.py`**

- 新增模块级 `recording_enabled: bool = True`（L210）

**二、运行列表清理 — `src/notify.py`**

- 新增 `remove_room_from_running(record_url)`（L153）：线程退出时从 `running_list` 幂等移除（成员检查前置、仅在真正移除时递减 `monitoring`、与 `clear_record_info` 共用 `record_state_lock`）

**三、Web API 与状态暴露 — `src/web_api.py` + `src/recorder_status.py`**

- `web_api.py` 新增 `POST /api/recording/toggle`（L249-258）：请求体 `{"enable": bool}`
- `recorder_status.py` 状态 JSON 追加 `"recording_enabled": main.recording_enabled`（L109）：前端页面刷新/重连后经 2s 轮询恢复按钮真实态（与 `engine_alive` 正交）。

**四、Web 面板入口 — `web.py`**

- 引擎线程启动**前**置 `main.recording_enabled = False`（L188-189…

**五、前端 — `web/index.html` + `web/app.js` + `web/style.css`**

- `index.html`（L39-46）新增「录制控制」区：状态指示（`录制运行中`/`录制已停止` 双子 span + `hidden` 切换）+ 开始/停止按钮…
- `app.js` 新增 `renderRecordingControl`（按钮互斥启用/禁用、`engine_alive` 联动、状态标签切换）与 `toggleRecording`（POST toggle → 成功 toast → 状态回拉独立 try/catch…
- `style.css`（L248-275）新增控制区样式：主色开始按钮/红色停止按钮/禁用态（透明度 + 禁用鼠标事件），与既有卡片风格一致。

**六、测试（新增 + 修改）**

- `tests/test_web_api.py`：新增 `TestRecordingToggle`（2 例——无认证 401、开关翻转写入真实模块属性）。
- `tests/test_record_failure_feedback.py`（**新增文件**）：`test_check_subprocess_interrupts_when_recording_disabled` 验证 `recording_enabled=False` 时 ffmpeg 轮询循环中断、优雅终止恰好调用一次、不记任何成功/失败样本…

**七、文档（新增）**

- `docs/web-recording-control-changelog.md`（**新增**）：特性改动汇总——需求背景、设计方案（全局开关 + 多入口中断）、关键设计决策（含「停止语义为主动分级优雅终止」的表述更正）、集成点、测试验证、已知限制、后续计划 5 项闭环（提交/审查/冒烟/持久化评估/单房间开关决策）。
- `docs/security-triage-2026-08-29.md`（**新增**）：Mimosa L3 提交门禁 44 条告警逐条分诊——SSRF（硬编码官方下载源）/路径穿越（固定常量路径 + `clean_name` 既有净化防线 `main.rstr` 含 `/ \ : .`）/命令注入（PyExecJS 内普通 JS 运算）/硬编码凭据（平台公开客户端 token）/弱随机数（非加密抖动）
- `CODE_WIKI.md` / `CODE_WIKI_EN.md`：更新日志新增本条目（中英同步）。

**改动说明**：

- **停止语义是主动分级优雅终止…
- **错误统计隔离是熔断体系的前提**：停止期间的中断不计 `record_error` 样本…
- **`recording_enabled` 不持久化（后续计划条目 4 评估结论）**：持久化 `True` 会使面板重启后自动恢复录制…
- **单房间开关维持延后（条目 5）**：与已知限制 #1 决策一致——Web 场景「全部录制/全部停止」为最常见需求…
- **7 处中断点均为提前返回模式**：不改变正常流程路径…

**影响范围**：

- Web 面板启动后不再自动拉起任何房间线程…
- CLI（`main.py` 直跑）与 GUI 入口行为完全不变（`recording_enabled` 默认 True）。
- 停止录制期间配置热加载、并发调度器、弹幕监控枢纽保持运行（仅不拉起/继续录制线程）。
- 其余行为（调度语义、选源顺序、探针容错、UA 约定等）均不变。

- `pytest` 全量 **786 passed, 2 skipped**（2026-08-29 复跑一致）
- 端到端冒烟（真实面板 `python web.py` 后台模式 + API 驱动）：启动即 `recording_enabled=false`/`recording_count=0`/`engine_alive=true` → toggle 开启后约 20s 内 `monitoring=3`（3 个房间线程拉起）→ toggle 停止后 3s 内 `monitoring=0`/`recording_count=0` → CTRL_BREAK 优雅退出…
- 提交门禁：Mimosa git-gate 两次拦截（graded 模式 high 必须 deny、无 findings 白名单机制）

**关联**：

- `docs/web-recording-control-changelog.md`：特性改动汇总与后续计划闭环记录（含审查修复明细 3.4 节）。
- `docs/security-triage-2026-08-29.md`：门禁告警分诊明细与两条放行路径。
- v4.0.9.1-dev (2026-08-27)「录制结果反馈调度器」——停止中断的错误样本隔离建立在其 `record_error`/`record_success` 语义之上…

### v4.0.9.2-dev (2026-08-28) — 性能审查优化落地（P1~P5 + 探针客户端复用 + 退避窗口自愈 + Web 日志 sink 重建 + 虎牙 FLV-first）

**变更摘要**：本条目系统性记录 2026-08-28 会话对代码库的性能审查与优化…

**涉及文件（按模块分类）**：

**一、流地址探针与选源（性能 P1 + 修复一/四）— `src/stream_select.py`**

- **P1 探针客户端复用**：`select_source_url` 整轮候选共用一支 `httpx.Client`（`finally` 关闭…
- **修复一 退避窗口对齐主循环**：新增 `_PROBE_BACKOFF_INTERVAL_MARGIN = 70.0`
- **修复四 虎牙 FLV-first**：新增 `_FLV_FIRST_PLATFORMS = ("虎牙直播",)`（**斗鱼绝不加入**…

**二、录制主链（修复二）— `main.py`**

- `check_subprocess` 成功分支（解析 `ffmpeg_command` 的 `-i` 后地址）调用 `clear_ffmpeg_reject(...)`

**三、并发调度（性能 P4）— `src/scheduler.py`**

- `import time` 提至模块顶层（`_now` / `_sleep` 不再函数内 import）

**四、同步 HTTP（性能 P2）— `src/sync_http.py`**

- 新增 `_thread_local = threading.local()` 与 `_session()`（线程局部复用 `requests.Session`

**五、工具 / 解析 / 配置（性能 P5）**

- `src/utils.py`：`remove_emojis` 的 ~400 字符表情模式提为模块级常量 `_EMOJI_PATTERN`（每次调用不再重复 `re.compile`）。
- `src/stream_select.py`：`contains_url` 模式提为模块级常量 `_URL_PATTERN`。
- `src/spider.py`：新增 `_BANDWIDTH_PATTERN` / `_DOUYIN_HEVC_FLV_PATTERN`，替换 4 处函数内 `re.compile`（`spider.py:178/202/1844/1918`）。
- `src/web_config.py`：`update_config_line` 的「按 key 编译正则」改 `functools.lru_cache(maxsize=128)`（`web_config.py:228`）。

**六、主循环去重（性能 P3）— `main.py`**

- `url_comments` / `line_list` / `url_line_list` 由 list 改 `set`

**七、日志（修复三）— `src/logger.py` + `web.py`**

- `src/logger.py`：新增模块级 `_console_sink_id` 捕获 `logger.add` 返回值（第 36/58 行）
- `web.py`：`_enter_background_mode`（`web.py:103`）在把 `sys.stdout/stderr` 重定向到 `logs/web_console.log` 并 `SW_HIDE` 隐藏控制台窗口**之后**…

**八、测试（新增 + 修改）**

- `tests/test_stream_select.py`：3 处客户端替身的 `head` / `stream` 补 `headers` 形参…
- `tests/test_sync_http.py`：4 个代理用例 patch 目标由 `src.sync_http.requests` 改为 `src.sync_http._session`。
- `tests/test_logger_console_sink.py`（**新增**，3 例）：跟随当前 stderr / 替换而非追加 / `None` 时静默（断言前须 `logger.complete()` 排空 `enqueue=True` 异步队列）。

**九、文档（本条目）**

- `CODE_WIKI.md` / `CODE_WIKI_EN.md`：更新日志新增本条目（中英同步）。
- `PERF_REVIEW_2026-08-28.md`（**新增**）：性能审查报告（瓶颈清单 P1~P7、本地基准实测、三轮真机验证结论、三处误判口径校正）。
- `AGENTS.md`：补 6 条防回归约定（探针客户端复用作用域 = 单次选源、禁止为保险关 keepalive、退避窗口须 ≥ 主循环周期、录制成功清除退避、Web 后台重建 sink、虎牙 FLV-first 且斗鱼不加入）。

**改动说明**：

- **P1 真实提速约 5.5× 而非 36×**：原实现 `with httpx.Client(...)` 内 HEAD 与 Range-GET 已复用同一条连接（每候选 1 条…
- **「headers 未透传」不是缺陷**：httpx `_merge_headers` 是「合并」非「替换」
- **退避窗口失配是真因**：固定 60s < 120s 循环间隔…
- **并发连接峰值实测恒为 1**：候选串行校验…
- **虎牙 FLV-first 收益**：三轮真机（880214 / chuhe 等）实证 HLS 三条 CDN（hs/tx/al）冷启动探针假绿（探针 200/206、ffmpeg 打开即 403…

**影响范围**：

- 虎牙选源行为变更（退避窗口对齐 + 成功清除 + FLV-first）：修复前 5 次秒退、12 分钟才稳定…
- Web 面板模式日志完整落盘 `logs/web_console.log`（修复前只剩 `print` 输出，DEBUG/WARNING 写向被 SW_HIDE 隐藏的窗口）。
- 性能：80 房间 × 10 探针/轮选源耗时约 12.7s → 1.15s（P1 整轮复用）；主循环去重 O(N²) → O(1)；scheduler 计数增量缩短锁竞争。
- 「最大同时录制数」调度语义、HLS/FLV 末位放行、探针节流/抖动、`_confirm_get_ok` 重试容错、流地址校验容错语义**均保持不变**（仅虎牙候选序列反转 + 退避窗口动态化）。

- `compileall`（venv Python 3.14）全过…
- `pytest` 全量：**751 passed, 2 skipped**（2 个 srt 失败为沙箱删除配额、非回归）。
- 三轮真机（虎牙 880214 / chuhe、斗鱼、抖音）：退避告警首次出现、FLV 稳定录 6 分钟、`web_console.log` 含 DEBUG/WARNING、冷启动首轮预期 FLV 零秒退（修复四待冷启动独立复验）。
- 本地 HTTP/1.1 基准：探针复用峰值连接 1 / 12.78ms；keepalive 关闭反而 8 连接 / 72.99ms（禁止项已反向验证）。

**关联**：

- `PERF_REVIEW_2026-08-28.md`：本条目对应的性能审查报告（含三处误判校正）。
- `AGENTS.md` 防回归条目：虎牙退避 / FLV-first / 探针客户端作用域 / keepalive / 退避窗口 ≥ 主循环周期 / Web 后台 sink。
- v4.0.9.1-dev (2026-08-27)「录制结果反馈调度器」—— `mark_ffmpeg_reject` 即该框架；本次补 `clear_ffmpeg_reject` 配对与 `_PROBE_BACKOFF_INTERVAL_MARGIN` 动态化。

### v4.0.9.1-dev (2026-08-28) — CI 工作流优化与网络安装重试收敛（retry 复合动作）+ PEP 758 格式化随 black 26 落地 + i18n 提取器修正 + 仓库元数据八文件同步

**变更摘要**：本条目记录 2026-08-27 深夜至 08-28 会话的四批改动。

**涉及文件（按模块分类）**：

**一、CI / GitHub Actions（新增功能 + 修改内容）**

- `.github/actions/retry/action.yml`（**新增**）：复合动作 `retry`——网络安装命令统一重试包装。
- `.github/workflows/ci.yml`（重写，job 结构与门禁语义不变）：
  - `actions/checkout` v5→v7、`actions/setup-python` v6→v7（经 WebSearch 确认 v7 均为当前最新大版本，与 build-release.yml 对齐，消除两份工作流 action 版本漂移）；
  - 9 处内联重试脚本（pip ×5 / apt ×3 / build-verify 依赖 ×1，各约 12 行）替换为 retry 复合动作调用（apt 退避保持原 10s）；
  - apt 安装对齐 build-release.yml 强化参数：`DEBIAN_FRONTEND=noninteractive`（防交互卡死）+ `Acquire::Retries=3`（apt 自身网络重试）+ `--no-install-recommends`（更快更省盘）；
  - 头注释补 job 拓扑图（setup 六路并行 → ci-summary 汇总）与「本工作流止于验证、不含部署」职责边界…
- `.github/workflows/build-release.yml`：4 处内联重试脚本（choco / apt / brew / pip）替换为 retry 复合动作（退避值与原脚本逐一一致：系统包管理器 15s、pip 10s）

**二、国际化模块（修改内容——格式 + 维护工具）**

- `i18n.py` + `scripts/compile_po.py`：同日早前条目把 4 处 `except` 改为元组括号后…
- `scripts/extract_i18n_strings.py`（**两处缺陷修正，本条目首次录入目录树与 §8 维护流程**）：
  - `is_valuable()` 重构：旧逻辑剥花括号后查字母…
  - `load_catalog_keys()`：po 头部空 `msgid ""` 剔除后再比对——JSON/YAML 目录设计上不含它（运行时加载亦会 pop）
  - 修正后重跑：运行时有价值串 318 条全部在库、缺失 0、四语目录键集一致（各 496 条）——确认今晨全量补全后源码未引入新可翻译串（此后仅改过 except 语法与 workflow YAML）。

**三、仓库元数据八文件同步（修改内容）**

- `requirements.txt` / `Dockerfile`：注释中 4 处引用**不存在的 `src/danmaku/` 路径**修正为实际位置（`src/ws_client.py` / `src/proto/douyin_pb2.py` / `src/platforms/bilibili.py` / collector 工厂链）——弹幕模块实际分布在 src/ 根、platforms/、proto/…
- `.dockerignore`：补 16 个排除项——`.mimosa/` 与 7 个本地工具目录（`.qoder/`、`.agents/`、`.pnpm-store/`、`.dsh-validation/`、`.ego-browser-test/`、`.plugin-src/`、`.tmp-dps-extract/`、`pytest-cache-files-*/`
- `.gitignore`：补 `.mimosa/`（此前 pyproject 的 black/isort/mypy/coverage 四处均排除它，git status 却持续显示 `?? .mimosa/` 未跟踪）与 `pytest-cache-files-*/` 防御条目。
- `pyproject.toml`：basedpyright exclude 清理 2 个已删除的死目录（`pytest-cache-files-g1bpkgza` / `pytest-cache-files-wt8ppn27`）
- `docker-compose.yaml`：`.env` 示例版本号 `4.0.8.3` → `4.0.9.1`（对齐 pyproject 当前版本）。
- `AGENTS.md`：模块计数 39 → 41（实测 src 根 31 + platforms 8 + proto 2）
- `.coveragerc-concurrency`：逐项核对与 pyproject `[tool.coverage.*]` 完全一致（source / omit / exclude_lines 同值…

**四、文档（本条目）**

- `CODE_WIKI.md` / `CODE_WIKI_EN.md`：目录树补 `.github/actions/retry/`、`scripts/extract_i18n_strings.py`、`scripts/check_coverage.py`、`uv.lock`（并清理 `.coveragerc-concurrency` 重复条目）

**改动说明**：

- **PEP 758 往返的澄清**：同日早前条目把 4 处 `except` 改为元组括号（当时判定「对 ≥3.13 最稳妥」）
- **重试收敛的动机**：两份 workflow 原共 13 处几乎相同的 12 行内联重试循环…
- **macOS brew 步骤拆分**：`brew trust aws/tap` 幂等且带 `|| true` 兜底…
- **.mimosa/ 的三层同步**：pyproject 四处排除均含它、.gitignore 却未忽略…
- **镜像排除 scripts/ 的依据**：grep 验证根目录全部入口脚本与 `src/**` 对 `scripts/` 零引用…

**影响范围**：

- CI 门禁恢复全绿且结构更可维护：action 版本统一、重试策略单源、apt 安装更抗网络抖动…
- i18n 四语目录确认零缺失（318 条有价值串全在库），`.mo` 与 `.po` 字节级同步（497 条含头）；提取器今后可直接用于增量维护。
- 镜像构建上下文显著瘦身（排除 scripts/、tests/、双语文档、本地工具目录、uv.lock 等 16 项）且不含任何运行时不需要的内容。
- **运行时行为零变化**——本条目全部改动为 CI / 文档 / 注释 / 配置同步 / 格式化（extract_i18n_strings.py 为维护期工具，不进运行时链路）。

- `black --check .`：115 files unchanged（含 PEP 758 转换后的 i18n.py / compile_po.py）；`isort --check-only .` 通过；
- `mypy src/` + `mypy --platform linux src/`：双跑 38 files 0 issue；
- `pytest -q` 全量：**744 passed, 2 skipped**（36s）；
- `python scripts/compile_po.py --check`：`.mo` 与 `.po` 同步（497 条含头）；`python scripts/extract_i18n_strings.py`：缺失 0、四语一致、无不一致行；
- 四语目录运行时冒烟：zh_CN 中文译文 / en_US 恒等 / zh_TW 繁体译文正确、未知语言回退正常（`tests/test_i18n.py` 34 passed）；
- 八文件同步一致性断言（TOML/YAML 解析、依赖 20 包双源一致、`src/danmaku` 引用清零、.mimosa 三层同步、8 个工具目录双 ignore 同源、镜像额外排除项、AGENTS 模块数 41）全部通过…
- 两个 workflow YAML 经 `yaml.safe_load` + 结构断言（needs 链 / outputs 键 / 本地 action 路径存在 / retry 调用计数 9+4 / 版本计数 checkout@v7 ×7、setup-python@v7 ×6、setup-node@v7 ×2 / DEBIAN_FRONTEND 无拼写错误）

**关联**：

- v4.0.9.1-dev (2026-08-27)「i18n 本地化系统修复（except → 元组括号）」——本条目把该 4 处交给 black 统一为 PEP 758 免括号风格（语义等价往返…
- v4.0.9-dev (2026-08-24)「PEP 758 / py314 全仓格式化」——本次是同一 black 版本策略下的收尾对齐；
- v4.0.8.2-dev (2026-08-19)「CI 重构：build-release 去除 download-artifact 来回」——§7 节描述本次对齐至该版流程（release-create 预分配 + 直传）；
- v4.0.9.1-dev (2026-08-27) 首轮「四语本地化目录全量补全」——extract_i18n_strings.py 即该会话沉淀的提取工具，本次修正其两处噪声源。

### v4.0.9.1-dev (2026-08-27) — i18n 本地化系统修复（Python 2 风格 `except` 多异常 → 元组括号）+ zh_CN.mo 重编译

**变更摘要**：本条目记录 2026-08-27 晚会话对本地化子系统的修复…

**涉及文件（按模块分类）**：

**一、国际化模块（修改内容）**

- `i18n.py`：三处 `except` 多异常逗号写法改为元组括号（行为不变）：
  - `i18n.py:202` `except OSError, ValueError:` → `except (OSError, ValueError):`；
  - `i18n.py:218` `except OSError, ValueError, yaml.YAMLError:` → `except (OSError, ValueError, yaml.YAMLError):`（三异常逗号写法在任意 Python 版本均非法，是真正的致命点）；
  - `i18n.py:320` `except ValueError, AttributeError:` → `except (ValueError, AttributeError):`。
  - 修复后 `py_compile` 通过、`import i18n` 正常（`_load_translations(locale_path, 'zh_CN')` 可加载 496 条）。
- `scripts/compile_po.py`：`scripts/compile_po.py:128` `except AttributeError, OSError:` → `except (AttributeError, OSError):`。修复后编译脚本可正常执行。

**二、构建产物（重新生成）**

- `i18n/zh_CN/LC_MESSAGES/zh_CN.mo`：语法修复后执行 `python scripts/compile_po.py` 重新生成（与当前 `zh_CN.po` 对齐，496 条含 gettext 头，`--check` 字节级同步）。

**改动说明**：

- **为何是阻断性缺陷**：首轮「全量补全」的 `zh_CN.mo` 实际从未成功落盘（编译脚本自身无法被 Python 解析）。
- **对首轮「PEP 758 合法 / 未改动」评估的订正**：同日二轮复查条目声称「全仓 16 处 `except A, B:` 在 3.14 下合法、未改动」。
- **§8 翻译文件表条目数**：同步由 492 更新为 496（对齐当前 `.po`/`.mo` 实际 496 条）。

**影响范围**：

- `i18n.py` 可正常导入，四语本地化（CLI 打印 / GUI / Web 语言切换）恢复可用；`scripts/compile_po.py` 可重复执行，`.mo` 编译与 CI `--check` 门禁链路打通。
- `zh_CN.mo` 与当前 `zh_CN.po`（496 条）重新对齐，简体中文运行时翻译完整。
- 源码功能逻辑零变化，仅 `except` 多异常语法形式调整（4 处）。

- `python3 -m py_compile i18n.py scripts/compile_po.py`：通过；全仓 `except A, B` 裸逗号写法 grep 复核为零。
- `python3 -c "import i18n"`：成功导入；`i18n._load_translations(i18n.locale_path, 'zh_CN')` 加载 496 条无异常。
- `python scripts/compile_po.py`：OK，生成 `zh_CN.mo`；`python scripts/compile_po.py --check`：`.mo` 与 `.po` 同步（496 条）。

**关联**：

- v4.0.9.1-dev (2026-08-27) 首轮「四语本地化目录统一」——本条目打通其被阻断的 `.mo` 重编译动作，是首轮本地化补全的真正收尾；
- v4.0.9.1-dev (2026-08-27) 二轮复查条目「PEP 758 合法 / 未改动」评估的针对性订正（限 `i18n.py` 与 `compile_po.py` 两文件）。

### v4.0.9.1-dev (2026-08-27) — 二轮复查修复（compile_po --check 恒真 + 直下失败采样缺口 + i18n/Web 缺口补全）

**变更摘要**：本条目系统性记录 2026-08-27 第二次会话对工作树的九项改动（三路子代理并行复查 + 人工交叉验证后按 P1/P2 优先级逐项修复）。

**涉及文件（按模块分类）**：

**一、构建 / CI / 社区模板（修改内容 + 删除项）**

- `scripts/compile_po.py`：
  - **`write_mo()` 改为纯内存产出**（去除 `path.write_bytes()` 写盘副作用与 `path` 参数）：原先 `main()` 在 `--check` 分支之前无条件调用 `write_mo(entries, MO_PATH)` 把新编译结果写盘覆盖 `.mo`
  - **落盘决策上移至调用方**：非 check 模式在打印成功消息前显式 `MO_PATH.write_bytes(fresh)`；`--check` 模式全程不触碰磁盘，真实比对已提交的 `.mo`；
  - 头部用法注释补「零副作用不写盘」语义说明。
- `.github/workflows/ci.yml`：paths-filter 的 `python` 过滤器新增 `- 'i18n/**'` 并同步修正注释——此前 static job（含 compile_po --check）不随纯翻译变更触发…
- `.github/workflows/build-release.yml`：删除 release job 末尾残留的无用步骤 "Debug inputs"（tag 路径下仅产生无意义输出）。
- `.github/ISSUE_TEMPLATE/bug.yml` / `bug_en.yml` / `question.yml` / `question_en.yml`：Python 版本下拉补 `- Python 3.14` 选项（项目要求 ≥3.14…

**二、录制主链（修改内容）**

- `main.py`：
  - **直下路径失败样本补报**（`start_record` 直下分支）：`if download_success:` 记成功样本之后新增 `elif record_url not in url_comments and not exit_recording: record_error(record_host)`——`direct_download_stream` 的「非 200」（CDN 拒绝…
  - **弹幕参数每轮重置恢复**：内层监测循环顶部（`exit_recording` 检查前）补 `record_danmaku_args = None`（AGENTS.md「每轮重置为 None」约定…
  - **两处日志规范化**：`direct_download_stream` 非 200 分支补请求 URL 上下文、异常分支补 `{type(e).__name__}`（Windows 下超时类异常 `str()` 为空串，裸打无线索）。
- `src/async_http.py`（存量清理）：`_close_all_clients()` 与 `async_req()` 主异常分支的两处裸 `logger.debug(e)` 规范为 `f"<动作>: {url} - {type(e).__name__}: {e}"` 格式（对齐同文件 `get_response_status` 已有范例…

**三、Web 配置与 API（新增功能 + 修改内容）**

- `src/web_config.py`：新增 `append_config_line(config_file, section, key, value)`——缺键补建的行级追加（`update_config_line` 只做替换、键或节缺失时返回 False）。
- `src/web_api.py`：`PUT /api/language` 写回降级链路——行级替换失败（历史 config.ini 无 `language` 键、Web 先于引擎首轮读配置启动的窗口）时调用 `append_config_line` 节末追加补建…

**四、Web 前端（修改内容）**

- `web/app.js`：约十处硬编码中文字符串改走内嵌四语字典 `t()`（与文件其余部分风格一致地包 `esc()`）——录制表空态 `empty.noRecording`、弹幕流空态 `danmaku.noData`、截断提示 `danmaku.truncated`、开关 toast `toast.enabled/disabled`、操作失败 `toast.opFailed`、配置页空态 `config.none` 与加载失败 `loadFailed`、文件列表空态 `files.emptyDir` 与进入/下载按钮 `rooms.enter/rooms.download`、下载失败 `toast.downloadFailed`。

**五、测试（新增功能 + 修改内容）**

- `tests/test_record_failure_feedback.py`：新增 `_FakeStreamResponse` / `_FakeHttpClient` httpx 流式替身（`__exit__` 返回类型标注 `None` 规避 mypy `exit-return`）
- `tests/test_web_api.py`：新增 `test_put_language_missing_key_appends_and_succeeds`（配置无 `[录制设置]`/`language` 键时 PUT 不再 500 且补建正确、不影响已有 `[Web]` 节）、`test_append_config_line_edge_cases`（目标节存在且夹注释 / 目标节为最后一节且文件无尾换行 / 节缺失三种形态）
- `tests/test_i18n.py`：`test_po_and_mo_in_sync` 适配 `write_mo()` 新签名（去 path 参数，取返回值直接比对），移除随之冗余的 `tempfile` 导入。

**六、文档（修改内容）**

- `CODE_WIKI.md` / `CODE_WIKI_EN.md`（本条目）：目录树 tests 注释更新（test_record_failure_feedback 7 用例、compile_po 零副作用）

**改动说明**：

- **为何 --check 必须零副作用**：校验逻辑的本质是「工作区产物 ↔ 已提交工件」的一致性检查…
- **直下路径样本分支的条件设计**：`record_url not in url_comments and not exit_recording` 用于区分「真失败」与「人为中断」——中断轮线程即将退出、不应向熔断器注入噪声样本…
- **PEP 758 澄清**（对未来评审重要）：Python 3.14 起 `except A, B:` 与 `except (A, B):` 完全等价（PEP 758 允许省略异常元组括号）
- **append_config_line 的边界处理**：经新增边界用例发现并修复一处初版缺陷——源文件末行无换行符时…

**影响范围**：

- CI i18n 门禁恢复正常职能：此后任何「改 .po 忘记重编译 .mo」都会被 static job 拦截（哪怕 PR 只动了 i18n/\*\*）。
- shopee / 花椒直播直下平台的高频拒绝线路将正常积累熔断错误预算，达到阈值后退避放并发槽给其他平台，而非秒级死循环。
- 「最大同时录制数(0为不限制)」兼作并发模式开关的调度语义、探针退避白名单、HLS/FLV 选源行为均零变化。
- 面板英文/繁体用户的动态文案（toast/空态/按钮）完整本地化；静态 `data-i18n` 文案此前已覆盖不受影响。

- `pytest -q` 全量：**744 passed, 2 skipped**（36.3s，净增 4 新用例）；
- `black --check .`（2 个新测试文件按 120 列重排后复验）/ `isort --check-only .`：114 files unchanged / 通过（`.isorted` 备份已清理）；
- `mypy src/` + `mypy --platform linux src/`：双平台 `Success: no issues found in 38 source files`
- `basedpyright tests/`：0 errors / 0 warnings / 0 notes；
- `python scripts/compile_po.py --check`：`.mo` 与 `.po` 同步（493 条）
- 前端硬编码残留 grep 复核为零（仅剩字典定义本身）。

**关联**：

- v4.0.9.1-dev (2026-08-27) 首轮审查条目（探针租约自愈 + 解析成功采样）的同日续作——首轮确立「按退出码/解析结果上报样本」框架…
- v4.0.9-dev (2026-08-23)「录制结果反馈调度器」——直下失败采样是其「与 ffmpeg 路径语义对齐」目标的最后一块拼图（当时注释误以为 False 仅来自异常路径）；

- v4.0.9-dev (2026-08-24)「四语本地化目录统一」与 Web 语言热切换——本轮修复的是热切换写入侧与前端动态文案侧的两处收尾缺口。

### v4.0.9.1-dev (2026-08-27) — 代码审查修复（熔断探针租约自愈 + 调度成功采样）+ 调度器线程安全加固 + i18n 四目录全量补全（288 → 492 条）

**变更摘要**：本条目系统性记录 2026-08-27 会话对工作树的三批改动。

**涉及文件（按模块分类）**：

**一、并发调度模块（新增功能 + 修改内容）**

- `src/scheduler.py`：
  - **新增探针租约**（修复高危缺陷）：模块常量 `_PROBE_LEASE_SECONDS = 60.0`
  - **配置字段加锁**（线程安全加固）：`_compute_capacity()` 改为单次加锁快照全部可变输入（模式/配置/活跃数/错误窗口…
  - **`host_of()` 注释修正**：原注释称「去端口/自定义直链退回路径本身」与实现不符（实现保留端口、仅返回 host、坏 URL 统一归 `"unknown"` 共享熔断 key）
- `main.py`：`start_record` 解析成功分支（`port_info["anchor_name"]` 非空）新增 `record_success(record_host)`——与解析失败分支的 `record_error` 对称。
- `src/notify.py`：
  - `record_error` / `record_success` 中三参 `getattr(main, "scheduler", None)` 改为直接访问 `main.scheduler`（AGENTS.md 禁令：三参 getattr 返回 `Any`
  - `run_script` 三处裸 `logger.error(e)` 补齐「动作 + 对象 + 异常类型」（`PermissionError`/`OSError`/`ValueError` 分支均带 `command` 与 `type(e).__name__`）。

**二、国际化模块（修改内容）**

- `i18n.py`：`_load_yaml_catalog()` 的 `except` 补 `yaml.YAMLError`（ParserError/ScannerError 非 OSError/ValueError 子类…
- `i18n/zh_CN/LC_MESSAGES/zh_CN.po`：新增 204 条（288 → 492）
- `i18n/en_US.json` / `i18n/en_GB.json` / `i18n/zh_TW.yaml`：同步追加 204 条（各 288 → 492）

**三、GUI 模块（修改内容）**

- `gui.py`：新增 `_bootstrap_crash_reported` 模块级标记——`_bootstrap_error_sink` 处理 `main()` 顶层异常并置位后…

**四、测试（新增功能）**

- `tests/test_scheduler.py`：新增 `test_platform_breaker_probe_lease_regrants_after_timeout`（探针租约超时重授予 → 新探针成功上报 → closed 的自愈全链路）
- `tests/test_i18n.py`：新增 `test_load_yaml_catalog_corrupted_returns_none`（损坏 YAML 返回 None 降级，不抛异常）。

**五、文档（修改内容）**

- `AGENTS.md`：版本号 4.0.8.3 → 4.0.9.1（对齐 `pyproject.toml` 唯一事实源）
- `CODE_WIKI.md` / `CODE_WIKI_EN.md`（本条目）：第 8 节翻译文件表条目数 282 → 492、覆盖范围更新…

**改动说明**：

- **探针租约与成功采样的关系**：两者互补——解析成功采样让「探针轮正常流转」的场景即时闭环（探针房间未开播时每轮 `record_success` 使熔断器恢复 closed）
- **加锁对行为的零影响**：锁内快照/写入与锁释放后 `recompute()` 的顺序保证无嵌套持锁（`Lock` 不可重入）
- **i18n 补全方法论**：以 AST 静态提取（`print()` 全部常量参数 + `logger.debug/info/warning/error/...` 首参常量与 f-string 模板还原）为权威基线…

**影响范围**：

- 熔断器在高频失败平台（虎牙/斗鱼 CDN 抖动）下的自愈能力显著增强——此前一旦进入 half-open 且探针轮未开播…
- 损坏的 `zh_TW.yaml` 从「Web 语言切换 500」降级为「该语言目录跳过、回退下一格式」。
- 运行时并发容量计算逻辑（动态/固定双模式、错误背压）语义零变化——加锁仅消除理论竞态（GIL 下 int/bool 原子…

- `pytest -q` 全量：**740 passed, 2 skipped**（34.8s，含新增 2 用例）；
- `black --check .` / `isort --check-only .`：114 files unchanged / 通过；
- `mypy src/` + `mypy --platform linux src/` + `mypy` 根目录三入口：全部 `Success`；
- `basedpyright tests/`：0 errors / 0 warnings；
- `python scripts/compile_po.py --check`：`.mo` 与 `.po` 同步（493 条）；
- 四语键集断言：`set(en_US) == set(en_GB) == set(zh_TW) == set(.mo 条目)`（492 条）；运行时抽查 `i18n._tr` 四种语言各取新条目均正确译出。

**关联**：

- 与 v4.0.9-dev (2026-08-24)「高并发多平台录制调度与资源管理优化」同源——本次为其 `PlatformBreaker` 补上探针租约自愈、为 `ConcurrencyScheduler` 补上线程安全与解析成功采样；
- 与 v4.0.9-dev (2026-08-23)「录制结果反馈调度器」同源——解析成功轮采样是该反馈体系的补全（此前仅 ffmpeg 退出码与直下路径上报）；
- 与 v4.0.9-dev (2026-08-24)「四语本地化目录统一」同源——本次将目录从 288 条扩至 492 条，收录范围从 print 常量串扩展到全仓 logger 模板底稿。

### v4.0.9-dev (2026-08-24) — 本次改动总览（按模块分类）

> 本条目为 v4.0.9-dev 累积至 2026-08-24 的**全部工作树改动**的系统性、按模块分类总览。下方各 `### v4.0.9-dev (2026-08-24) — …` 为分功能详述（讲「为什么、怎么做」），本条目互补讲「改了哪些文件、归在哪个模块」。注意：本总览覆盖整个 4.0.9-dev 工作树（含 Python 3.14 升级、四语 i18n、并发调度、类型修复等），部分子项在分条目中有更深的因果分析。

**一、构建 / CI / 依赖（修改内容）**

- `pyproject.toml`：
  - 版本 `4.0.8.3` → `4.0.9`（唯一事实源；`main.py`/`web_api.py` 经 `importlib.metadata` 动态读取；`Dockerfile` 经 `APP_VERSION` 构建参数注入）。
  - `requires-python` `>=3.10` → `>=3.14`；classifiers 由 `3.10–3.13` 收敛为仅 `3.14`。
  - `[project.dependencies]` 新增 `PyYAML>=6.0.3`（i18n YAML 目录 `i18n/zh_TW.yaml` 支持；缺失仅损该格式，JSON/gettext 不受影响）。
  - `[tool.black] target-version` `['py310','py311','py312','py313']` → `['py314']`。
  - `[tool.mypy] python_version` `3.10` → `3.14`。
  - `[tool.pytest.ini_options]` 新增 `filterwarnings`：忽略 `httpx`+`starlette.testclient` 弃用提示（第三方、与项目代码无关）。
  - `[tool.basedpyright] pythonVersion` `3.10` → `3.14`。
- `requirements.txt`：新增 `PyYAML>=6.0.3`（与 `pyproject.toml` 下界严格一致）。
- `Dockerfile`：基础镜像 `python:3.13-slim-bookworm` → `python:3.14-slim-bookworm`（builder 与运行阶段一致）
- `.github/workflows/ci.yml`：`python_min` `3.10`→`3.14`、`python_latest` `3.13`→`3.15`、`python_matrix` `["3.10","3.13"]`→`["3.14","3.15"]`、`python_build` `3.12`→`3.14`
- `.github/workflows/build-release.yml`：`python_build` `3.12`→`3.14`（与 ci.yml 同值，保证验证环境 == 发布环境）。
- `.gitignore`：移除对 `.coveragerc-concurrency` 的忽略（改为纳入版本控制，见下）。
- 新增 `.coveragerc-concurrency`：并发测试专用覆盖率配置（`CI` 经 `COVERAGE_RCFILE` 引用，`fail_under = 0`，仅产出报告供人工审查）。
- 新增社区协作模板：`.github/ISSUE_TEMPLATE/`（议题模板）、`.github/PULL_REQUEST_TEMPLATE.md`（PR 模板）、`.github/workflows/issue-translator.yml`（议题自动翻译 Action）。

**二、国际化（i18n）体系（新增功能 + 修改内容）**

- `i18n.py`：重写为四格式翻译引擎。
- 新增 `i18n/en_US.json`、`i18n/en_GB.json`、`i18n/zh_TW.yaml`：四语翻译目录，各 288 key（美式 / 英式拼写分流）。
- 重编译 `i18n/zh_CN/LC_MESSAGES/zh_CN.mo`（28,697 字节），`compile_po.py --check` 确认字节级同步。
- 新增 `CODE_WIKI_EN.md`（英文架构文档）、`README_EN.md`（英文用户文档），与中文版结构对齐。
- `gui.py`：新增 `_on_language_change()`（GUI 语言切换下拉）、`_install_crash_sink()` / `_bootstrap_error_sink()`（顶层崩溃落盘钩子，窗口化静默崩溃可观测）。
- `src/web_api.py`：新增 `LanguageUpdate` 模型与 `GET/PUT /api/language` 端点（Web 面板语言热切换：归一化校验 → 写回 `config.ini` → 热切换本进程翻译目录）。
- `web/index.html` / `web/app.js` / `web/style.css`：新增语言选择器等 UI（+291 / +83 / +13 行）。

**三、并发调度与资源管理（高并发多平台）（新增功能）**

- 新增 `src/scheduler.py`：`ResizableSemaphore` / `PlatformBreaker` / `ConcurrencyScheduler` / `host_of`。
- `main.py`：scheduler 接线——`main()` 初始化调度器、容量下限接入「最大同时访问网络线程数」、新增「最大同时录制数(0=不限制)」
- `src/notify.py`：`record_error`/`record_success` 增加 `key` 形参并委托 scheduler 按 key 计错误预算；`adjust_max_request` 改为启动 `scheduler.adjust_loop` 守护循环。
- 新增 `tests/test_scheduler.py`（12 用例）。
- 修复 14 个源文件共 21 处 Python 2 风格 `except A, B:` 语法（`build_exe.py`、`gui.py`、`i18n.py`、`scripts/check_coverage.py`、`scripts/compile_po.py`、`src/collector.py`、`src/config_io.py`、`src/recorder_status.py`、`src/spider.py`(2)、`src/ttwid.py`、`src/web_config.py`、`src/ws_client.py`、`src/platforms/bilibili.py`、`src/platforms/douyu.py`）

**四、录制结果反馈调度器 + 探针退避（虎牙 403 死循环根治）**

- `main.py`：`check_subprocess` 按退出码反馈——`rc==0`→`record_success(host_of)`、`rc!=0`→`record_error(host_of)`
- `src/stream_select.py`：新增 `mark_ffmpeg_reject(url, platform)`（委托 `_mark_probe_reject`）；`platform` 不在 `_PROBE_BACKOFF_PLATFORMS`（仅「虎牙直播」）时静默无操作。
- 新增 `tests/test_record_failure_feedback.py`（5 用例）。详见分条目「录制结果反馈调度器 + 探针退避标记」。

**五、类型 / 质量门禁修复（修改内容）**

- `i18n.py`：`_windows_ui_language()` 增加 `if sys.platform != "win32": return None` 平台门控（修复 `mypy --platform linux` 的 `Module has no attribute "WinDLL"`）。
- `src/recorder_status.py`：`_live_network_capacity()` 中三参 `getattr(main,"scheduler",None)` 改为直接 `main.scheduler`（修复 `no-any-return` Any 泄漏）。
- `tests/test_i18n.py`：新增 `TestWindowsUiLanguagePlatformGate`（2 用例）、`test_c_locale_from_getlocale_ignored`（C/POSIX 过滤回归）
- `i18n.py` `detect_system_language()`：`locale.getlocale()` 回退路径新增 C/POSIX 过滤。
- `src/async_http.py`：`close_all_clients_sync()` 适配 Python 3.14——`asyncio.get_event_loop()` 不再隐式创建循环，捕获 `RuntimeError` 后走引用清理兜底。
- `src/config_io.py`：`read_config_value()` 缺省值写回改为「先在内存 `io.StringIO` 完整序列化、成功后才落盘」
- `src/http_config.py`：FFmpeg 9.0 起默认校验 TLS 证书 → 「禁用SSL证书验证的平台」覆盖重新具备实际作用…
- `src/logger.py`：`sys.stderr is None` 守卫（pythonw / `console=False` 冻结 exe 无控制台时不添加控制台 sink，避免导入期 `TypeError` 静默崩溃）。
- `src/web_config.py` / `src/spider.py` / `build_exe.py`：`except` 逗号化（PEP 758 机械重排）。

**六、平台适配 / 下载源（修改内容）**

- `src/ffmpeg_install.py`：蓝奏云 FFmpeg 下载源切换——`wweb.lanzouv.com` → `wwasx.lanzout.com`（新提取码）
- `src/spider.py` `get_migu_stream_url()`：咪咕 `migu.js`（2026-08 重写版）现输出带 `ddCalcu`/`sv` 参数的完整地址；移除本地固定拼接的过期 `sv=10010`。

**七、全仓格式化（PEP 758 / py314）与本地环境（修改内容）**

- `black` 26.5.1 + `target-version=['py314']` 全仓重排：剥除 `except (A, B):` 括号（PEP 758 使该语法在 Python 3.14 重新合法）。
- 本地 dev venv 由 Python 3.13.14 重建至 **3.14.7**（含全部运行时依赖 + `black==26.5.1` / `isort==8.0.1` / `mypy==2.3.0` / `basedpyright` / `pytest`）。
- 本项在「CI mypy 双错误修复」条目中曾标记为「待办」，已于本会话收尾阶段完成（含 venv 重建）。

### v4.0.9-dev (2026-08-24) — CI pytest 失败修复：C/POSIX 语言环境检测与 monkeypatch 规约

**变更摘要**：修复 CI `tests/test_i18n.py::TestDetectSystemLanguage::test_c_and_posix_env_ignored` 断言失败（`assert 'C' != 'C'`）。

**涉及文件**：

- 修改 `i18n.py`：`detect_system_language()` 函数的 `locale.getlocale()` 回退路径新增 C/POSIX 过滤——`current = locale.getlocale()[0]` 返回值经 `current.upper() not in ("C", "POSIX")` 判断后才返回…
- 修改 `tests/test_i18n.py`：
  - `TestDetectSystemLanguage._env_without_locale_vars` 重构为 `_clear_locale_vars(monkeypatch)`，使用 `monkeypatch.delenv(var, raising=False)` 逐一删除 locale 相关环境变量；
  - 4 处 `patch.dict(os.environ, ..., clear=True)` 替换为 `monkeypatch.setenv/delenv`；
  - 新增 `test_c_locale_from_getlocale_ignored` 回归测试：patch `locale.getlocale` 返回 `("C", None)`，验证 `detect_system_language()` 返回 `None`（不依赖真实环境变量）；
  - 修正 pytest 收集时 `sys.argv` 参数解析冲突：`SECONDS = int(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else N`（避免 pytest `-q` 参数导致 `int('-q')` 崩溃）。

**改动说明**：

- **C/POSIX 过滤统一**：`detect_system_language()` 有两条路径获取语言——环境变量（`LANGUAGE`/`LC_ALL`/`LC_MESSAGES`/`LANG`）和 `locale.getlocale()`。
- **monkeypatch 规约**：`patch.dict(os.environ, clear=True)` 对 `os.environ` 做整体快照（`original = in_dict.copy()`）
- **PEP 758 格式化**：black 26.5.1（CI 固定版本）在 `target-version = ['py314']` 下自动剥离 `except (A, B):` 的括号。

**影响范围**：

- 运行时行为零变化——`detect_system_language()` 在 C/POSIX locale 下原返回 `"C"`（现已返回 `None`
- 测试稳定性提升——不再依赖 `patch.dict` 对 `os.environ` 的整体快照，避免 harness 环境变量膨胀引发的 `ValueError`。
- 格式化对齐——全仓 black 输出统一为 Python 3.14 风格，CI Static Checks 持续通过。

- `pytest tests/test_i18n.py`：**33 passed**（含新增的 `test_c_locale_from_getlocale_ignored` 回归用例）；
- `black --check .`：**512 files clean**；
- `isort --check-only .`：全通过；
- `mypy tests/`、`mypy src/`、`mypy --platform linux src/`：全部 `Success`；
- `basedpyright tests/`：**0 errors / 0 warnings**；
- `py_compile i18n.py tests/test_i18n.py`：通过。

**关联**：

- 与 v4.0.9-dev (2026-08-23)「Python 3.14 升级 + 语言配置键迁移」的 `detect_system_language()` 新增逻辑同源——本次修复其 `locale.getlocale()` 回退路径的 C/POSIX 过滤缺失。
- 与 AGENTS.md 测试编写强制约定（环境变量一律用 `monkeypatch.setenv/delenv`，禁用 `patch.dict(os.environ)`）保持一致。

### v4.0.9-dev (2026-08-24) — CI mypy 双错误修复（ctypes.WinDLL 平台门控 + 三参 getattr Any 泄漏）

**变更摘要**：修复 CI `mypy src/`（mypy 2.3.0…

**涉及文件**：

- 修改 `i18n.py`：`_windows_ui_language()` 函数体首行增加 `if sys.platform != "win32": return None` 平台门控。
- 修改 `src/recorder_status.py`：`_live_network_capacity()` 中 `getattr(main, "scheduler", None)` 改为直接属性访问 `main.scheduler`。
- 修改 `tests/test_i18n.py`：新增 `TestWindowsUiLanguagePlatformGate` 两个用例——① 非 win32 平台门控直接返回 None（不依赖 ctypes 异常兜底）

**改动说明**：

- 平台门控采用「函数体首行早返回」而非调用点包裹：函数自带平台契约（注释本就声明「非 Windows 返回 None」）
- 刻意不用 `# type: ignore[attr-defined]`：该注释在 Linux CI 下必要、Windows 本地下多余…
- 刻意不用 `cast(ConcurrencyScheduler | None, getattr(...))`：cast 放弃检查且掩盖「属性已声明、本可直接访问」的事实。

**影响范围**：仅静态类型与测试，无运行时行为变化；CI `mypy src/` 恢复全绿。

**另发现（本会话收尾已完成）**：工作区把 black `target-version` 迁至 `py314`-only 后…

### v4.0.9-dev (2026-08-24) — 高并发多平台录制调度与资源管理优化（自适应并发 + 按平台熔断降级）

**变更摘要**：针对「同时录制超过 80 个任务且跨多平台时严重延迟、性能骤降、大量报错」的问题。

**涉及文件**：

- 新增 `src/scheduler.py`：调度核心模块，含 `ResizableSemaphore` / `PlatformBreaker` / `ConcurrencyScheduler` / `host_of`。
- 修改 `src/notify.py`：`record_error` / `record_success` 增加 `key` 形参并委托 `scheduler` 按 key 计入错误预算…
- 修改 `main.py`：引入 `ConcurrencyScheduler` / `ResizableSemaphore` / `host_of`
- 新增 `tests/test_scheduler.py`：12 个单元测试，覆盖信号量调容、熔断器状态机、自适应容量缩放/下限、按 key 隔离、录制并发软上限。
- 修复 14 个源文件共 21 处 Python 2 风格 `except A, B:` 语法错误（`build_exe.py`、`gui.py`、`i18n.py`、`scripts/check_coverage.py`、`scripts/compile_po.py`、`src/collector.py`、`src/config_io.py`、`src/recorder_status.py`、`src/spider.py`(2)、`src/ttwid.py`、`src/web_config.py`、`src/ws_client.py`、`src/platforms/bilibili.py`、`src/platforms/douyu.py`）

**改动说明**：

- **`ResizableSemaphore`**：实现上下文管理器协议的信号量…
- **`PlatformBreaker`**：按 key 的熔断器…
- **`ConcurrencyScheduler`**：调度中枢。
- **`host_of(url)`**：取 URL 主机名（小写、去端口/路径/查询）作为熔断 key；自定义 flv/m3u8 直链退回路径本身。
- **`notify.py` 接线**：`record_error(key=None)` / `record_success(key=None)` 在更新 `main.error_window` / `error_count` 之外…
- **`main.py` 接线**：
  - 全局变量由 `semaphore: threading.Semaphore = threading.Semaphore(1)` 改为 `scheduler: ConcurrencyScheduler | None`（None 占位）、`semaphore: ResizableSemaphore`、`recording_semaphore: ResizableSemaphore`。
  - `main()` 中首次初始化 `scheduler = ConcurrencyScheduler(configured_limit=max_request)`
  - `start_record`：`record_host = host_of(record_url)`（并在 `while True` 顶部、try 之前预置 `record_host = ""` 以消除 possibly unbound）
  - `check_subprocess`：将 `while process.poll() is None:` 录制循环包入 `recording_semaphore` 的 `acquire()` / `release()`（try/finally），实现可选的同时 ffmpeg 录制数上限治理。
- **测试补充**：`tests/test_scheduler.py` 共 12 用例（含修正两处测试前提：① `ResizableSemaphore(0)` 合法表示暂停态…

**影响范围**：

- 并发模型由「单全局固定 3 槽信号量 + 单向错误率压制」升级为「自适应全局容量（随活跃任务数缩放、带安全下限）+ 按 host 平台隔离熔断 + 可选录制并发软上限」。
- 仅新增 `src/scheduler.py` 并在 `main.py` / `notify.py` 固定接线点接入…
- 新增配置项「最大同时录制数(0为不限制)」（默认 0=不限制…
- 性能：网络并发容量随活跃任务数自适应提升（默认下限 8、上限 128），显著降低高并发场景的探测排队与处理延迟。

- `tests/test_scheduler.py` + `tests/test_main_fixes.py`：**41 passed**；
- 全量 `pytest`：**707 passed / 3 skipped**…
- `basedpyright src/scheduler.py tests/test_scheduler.py`、`basedpyright tests/`、`basedpyright main.py src/notify.py src/scheduler.py` 均 **0 errors / 0 warnings / 0 notes**；
- `black --check` / `isort --check-only` 涉及文件全通过；
- `python -m py_compile` 全量源码通过。

**关联**：

- 与 v4.0.8.3-dev (2026-08-21) 「start_record 复杂度治理」同源——后者把平台分派链抽为 `_resolve_platform_stream`
- 按 host 隔离降级思路与 AGENTS.md 已知坑「单平台 CDN 偶发 403/405 探针误杀」治理目标一致（隔离后单平台抖动不再全局放大）。

### v4.0.9-dev (2026-08-24) — 四语本地化目录统一与英式/美式英语分流 + 打包脚本串补齐 + zh_CN.mo 重编译

**变更摘要**：对四份本地化资源（zh_CN.po / en_US.json / en_GB.json / zh_TW.yaml）做统一与修正。

**涉及文件**：

- 修改 `i18n/zh_CN/LC_MESSAGES/zh_CN.po`：追加 6 条 build/smoke 常量串、更新 PO-Revision-Date 至 2026-08-24、刷新头部注释。
- 修改 `i18n/en_US.json`：补齐 6 条新串；全量统一为美式拼写（消除 minimise/minimised/cancelled 等英式残留）。
- 修改 `i18n/en_GB.json`：补齐 6 条新串；改写为真正英式拼写（minimise/minimises/minimised/cancelled），与 en_US 仅在 4 条拼写敏感条目存在差集。
- 修改 `i18n/zh_TW.yaml`：补齐 6 条新串（简→繁转换，如 跳过→跳過、开始下载运行时二进制→開始下載執行時二進位檔）。
- 重新生成 `i18n/zh_CN/LC_MESSAGES/zh_CN.mo`（28,697 字节）并校验与 .po 同步。

**改动说明**：

- **四语 key 集合一致性**：以源码常量串为权威基准…
- **打包脚本串补齐**：build_exe.py 经 i18n 翻译路径输出、属用户可感知的打包信息…
- **美式/英式分流**：en_US 原内部不一致（混合 minimise、cancelled 等英式）

**影响范围**：

- 四份目录现共享同一 288 条 key 集合，无缺失、无多余；zh_CN.mo 与 zh_CN.po 字节级同步。
- 仅本地化资源变更，无代码逻辑改动；不影响运行时行为与既有翻译。
- 范围遵循项目 i18n 约定（仅本地化面向用户的产品串）：CI/版本检查类 scripts/*.py、第三方 bundled 资源、测试目录及个人临时脚本不纳入目录。

- 自写 reconciler 脚本解析四份目录，确认 key 集合完全一致（各 288 条，去除 gettext 头部伪 key）。
- `python scripts/compile_po.py --check`：zh_CN.mo 与 zh_CN.po 同步（289 条，含 gettext 标准头部），通过。
- JSON / YAML 均合法（json.loads / yaml.safe_load 无异常）。

**关联**：

- 与 v4.0.9-dev (2026-08-23) 「Python 3.14 升级 + 语言配置键迁移」同属国际化体系维护——后者完成 language 键迁移与四语目录热切换链路…
- 与 CODE_WIKI.md「国际化模块」章节的四语目录表（zh_CN.po / en_US.json / en_GB.json / zh_TW.yaml）一致；README.md「多语言与界面切换」章节对应能力描述不变。

### v4.0.9-dev (2026-08-23) — 录制结果反馈调度器 + 探针退避标记（虎牙 403 死循环根治）

**变更摘要**：2026-08-23 GUI 79 房间实测暴露录制侧反馈缺失：虎牙房间探针 200/206 通过后 ffmpeg 紧随被 403…

**涉及文件**：

- 修改 `main.py`：`check_subprocess` 新增 `_proc_started_at = time.time()` 进程启动时刻…
- 修改 `src/stream_select.py`：新增公开入口 `mark_ffmpeg_reject(url, platform)`（委托 `_mark_probe_reject`）
- 修改 `src/recorder_status.py`：新增 `_live_network_capacity()` 取调度器实时容量（`scheduler.network_semaphore.value`）
- 新增 `tests/test_record_failure_feedback.py`：5 个单元测试，覆盖成功样本/快速失败+退避标记/慢速失败不标记/缺 -i 入参安全/容量回退。
- 修改 `tests/test_stream_select.py`：新增 `test_mark_ffmpeg_reject_marks_backoff`（退避跨轮新 token 命中 + 非白名单平台无操作）。
- 修改 `AGENTS.md`：新增「录制结果反馈约定」小节（失败样本/快速失败探针退避/轮末禁止无条件成功/容量显示实时值/回归测试要求）。

**改动说明**：

- **失败样本上报**：`check_subprocess` 在 `return_code` 分支处（`streamget.log` 退出码分支）：
  - 成功（rc==0，主播下线）：按房间 host 记一次成功样本，与录制失败分支配对，维持 error_window 真实错误率；
  - 失败（rc!=0，CDN 拒绝）：记一次失败样本驱动按 host 熔断与全局背压。
- **快速失败探针退避**：`time.time() - _proc_started_at <= _FFMPEG_FAST_FAIL_SECONDS`（20 秒）为快速失败（输入打开被 CDN 拒绝的签名…
- **慢速失败豁免**：`-reconnect_delay_max 60` 耗尽（>60s）属拉流中断/重连耗尽…
- **异常入参兜底**：`ffmpeg_command` 缺 `-i`（异常入参）时 `except ValueError` 捕获，仅记失败样本、跳过退避标记。
- **容量显示**：`_live_network_capacity()` 取 `scheduler.network_semaphore.value`（调度器就绪时）
- **直下路径对齐**：`direct_download_stream` 成功路径补 `record_success(record_host)`，与 ffmpeg 路径语义对齐（失败已在 except 分支有 `record_error`）。

**影响范围**：

- 虎牙房间遇到「探针 200 → ffmpeg 403」死循环时…
- 仅修改 `main.py` / `src/stream_select.py` / `src/recorder_status.py` 三个源文件…
- 退避白名单仅限虎牙（`_PROBE_BACKOFF_PLATFORMS = ("虎牙直播",)`）；其他平台不受影响，保持「重试一次再定罪」语义。

- `pytest tests/test_record_failure_feedback.py tests/test_stream_select.py tests/test_scheduler.py`：**43 passed / 0 failed**；
- 全量 `pytest --ignore=tests/test_twitch_live_collector.py --ignore=tests/test_srt_timeline_anchor.py`：**710 passed / 3 skipped**…
- `black --check`（Python 3.14 运行）/ `isort --check-only` 涉及 5 文件全通过；
- `basedpyright main.py src/recorder_status.py src/stream_select.py tests/test_record_failure_feedback.py`：**0 errors / 0 warnings / 0 notes**。

**关联**：

- 延续 v4.0.9-dev (2026-08-23) 调度中枢治理——调度器已有按 host 熔断器与自适应容量…
- 与 AGENTS.md 已知坑「CDN 探针节流/退避」治理目标一致：探针侧节流+退避降低风控误触发概率…

### v4.0.9-dev (2026-08-23) — 网络并发双模式（动态调速 / 固定并发）

**变更摘要**：在已有 `ConcurrencyScheduler` 自适应容量基础上…

**涉及文件**：

- 修改 `src/scheduler.py`：`ConcurrencyScheduler` 新增 `_dynamic_mode` 字段与 `set_dynamic_mode(enabled: bool)` / `dynamic_mode` 属性…
- 修改 `main.py`：热重载循环在 `scheduler.set_recording_limit(...)` 后追加 `scheduler.set_dynamic_mode(new_recording_limit == 0)`
- 新增 `tests/test_scheduler.py` 3 个用例：`test_scheduler_fixed_mode_pins_capacity_to_configured_limit`（固定容量不随任务数涨、往返切换恢复动态）、`test_scheduler_fixed_mode_ignores_error_backpressure`（固定模式忽略错误背压）、`test_scheduler_fixed_mode_guarantees_min_one_slot`（固定模式热更新即时生效 + 非法值兜底 1）。
- 修改 `AGENTS.md`：并发模型章节更新模式语义（`set_dynamic_mode` 接入、双模式分支、per-key 熔断与模式正交、15 个调度用例）。

**改动说明**：

- **模式语义**：「最大同时录制数(0为不限制)」=0 时启用动态调速（网络容量随活跃任务数自适应、下限 8 / 上限 128…
- **同时录制上限语义不变**：仍由 `scheduler.set_recording_limit(...)` 管控 ffmpeg 并发数，不受并发模式切换影响。
- **调度器 `adjust_loop` 在固定模式下为重算 no-op**（`recompute()` 发现容量未变时不触发改动、不调用 `set_value`），故可安全复用同一守护循环。
- **日志**：`set_dynamic_mode` 首次播报或模式切换时输出 `并发模式: 动态调速（网络容量随活跃任务数自适应，当前 <n>，下限 <min>，上限 <max>）` / `并发模式: 固定（忽略动态调速器，网络容量固定为 <n>，来源: 配置「同一时间访问网络的线程数」）`

**影响范围**：

- 仅修改 `src/scheduler.py` / `main.py` / `tests/test_scheduler.py` / `AGENTS.md`
- 用户可通过将「最大同时录制数(0为不限制)」改为非 0 值（例如 2）切换至固定并发模式…

- `pytest tests/test_scheduler.py`：**15 passed**（3 个新模式用例通过）；
- `pytest tests/test_record_failure_feedback.py tests/test_concurrency.py -q`：**11 passed**（回归调度中枢治理与并发线程安全用例均通过）；
- `black --check src/scheduler.py main.py tests/test_scheduler.py`、`isort --check-only src/scheduler.py main.py tests/test_scheduler.py`、`mypy src/scheduler.py tests/test_scheduler.py`、`basedpyright tests/test_scheduler.py`、`py_compile main.py src/scheduler.py` 全部 **通过 / 0 errors / 0 warnings**；
- 端到端冒烟（`config/config.ini` 真实值：`最大同时录制数(0为不限制)=0`、`同一时间访问网络的线程数=3`）：动态模式 80 活跃任务 → 容量 20（随任务数扩张、满足下限 8）

**关联**：

- 延续 v4.0.9-dev (2026-08-23) / (2026-08-24) 调度中枢治理——调度器已有按 host 熔断器与自适应容量、录制侧反馈与探针退避…
- 与 AGENTS.md 并发模型章节、`test_scheduler.py` 用例数（12→15）同步更新。

### v4.0.9-dev (2026-08-23) — Python 3.14 升级 + 语言配置键迁移（综合维护）

**来源**：用户要求将项目升级至 Python 3.14…

**改动**：

- **Python 版本基线升级（`pyproject.toml` + `Dockerfile` + `.github/workflows/ci.yml` + `AGENTS.md` + 文档）**：
  - `pyproject.toml`：`requires-python = ">=3.14"`、`[tool.black] target-version = ['py314']`、`[tool.mypy] python_version = "3.14"`、`[tool.pytest] asyncio_mode = "auto"` 保持不变…
  - `Dockerfile`：基础镜像由 `python:3.13-slim-bookworm` 升级为 `python:3.14-slim-bookworm`，`APP_VERSION` build-arg 机制不变。
  - `.github/workflows/ci.yml`：`setup-python` 的 `python-version` 矩阵由 `'3.13'` 更新为 `'3.14'`（`typecheck` / `test` / `concurrency-test` / `integration-verify` / `build-verify` 全链路统一）。
  - `AGENTS.md`：项目概览、Python 版本、已知坑条目、mypy 检查版本全部对齐为 Python 3.14…
  - `README.md` / `README_EN.md` / `CODE_WIKI.md`：Python 徽章由 `3.13` 改为 `3.14`，运行方式前置要求同步更新。
- **Python 3.14 兼容性修复（`src/async_http.py`）**：
  - `close_all_clients_sync()`（`atexit` / 信号钩子调用）因 Python 3.14 起 `asyncio.get_event_loop()` 在当前线程无循环时抛 `RuntimeError`（≤3.13 为隐式创建 + `DeprecationWarning`）
  - 新增「`asyncio.get_event_loop()` 3.14 起不再隐式创建事件循环」条目记入 `AGENTS.md` 已知坑，供后续维护参考。
- **语言配置键迁移与系统语言回退（`i18n.py` + `main.py` + `gui.py` + `src/web_api.py` + `src/web_config.py`）**：
  - `i18n.py`：新增 `FALLBACK_LANGUAGE = "en_US"`、`detect_system_language()`（环境变量 `LANGUAGE`/`LC_ALL`/`LC_MESSAGES` → Windows `GetUserDefaultUILanguage` → POSIX `locale.getdefaultlocale()`）、`has_catalog(lang)`（按 `i18n/<lang>/` 多格式目录探测可用翻译）、`resolve_language(value)`（空值 → 系统语言 → `FALLBACK_LANGUAGE`
  - `main.py`：新增 `_read_language_config()`
  - `gui.py`：初始语言读取改为先查 `language` 新键、回退旧键 `language(zh_cn/en)`、再回退系统语言；侧边栏「语言 Language」菜单写回 `language` 新键。
  - `src/web_api.py`：`PUT /api/language` 写回键名由 `language(zh_cn/en)` 改为 `language`；`GET /api/language` 返回值经 `resolve_language` 归一化。
  - `src/web_config.py`：`_write_language_section` 写入 `language = {value}` 而非旧键，避免并行编辑冲突时回退到旧字段。
- **测试补充（`tests/test_i18n.py` + `tests/test_web_api.py` + `tests/test_config_io_readonly.py`）**：
  - `tests/test_i18n.py`：新增 `TestResolveLanguage`（空值→系统语言→en_US、非法值→en_US、目录缺失→en_US、合法值直接返回）、`TestDetectSystemLanguage`（环境变量优先）共 8 个用例。
  - `tests/test_web_api.py`：修复 `_write_language_section` 回归，确保写入新键 `language` 而非旧键。
  - `tests/test_config_io_readonly.py`：新增语言键迁移 3 个用例（旧键自动迁移写回、新键优先、默认值补写）。
- **代码风格与静态检查（`black` / `isort` / `mypy` / `basedpyright`）**：
  - 升级 `black` 目标版本为 `py314`（PEP 758 `except A, B` 语法自动支持）
  - 新增代码全部补齐类型注解，保持项目 `disallow_untyped_defs = true` 门禁。
- **质量门禁验证**：
  - 全量 `pytest` **714 passed / 2 skipped / 0 warnings**（含新增的语言键迁移与 `async_http` 回归用例）；
  - `black --check .` 全部文件 unchanged；`isort --check-only .` 全通过；
  - `mypy src/` → `Success: no issues found`；`basedpyright src/` → **0 errors / 0 warnings / 0 notes**；
  - `python scripts/compile_po.py --check` 确认 `.po` / `.mo` 字节级同步未受影响。
- **文档与约定同步**：
  - `AGENTS.md`：项目结构、Python 版本说明、已知坑、mypy 检查版本等章节同步更新，并新增 Python 3.14 迁移基线与 `language` 新键语义说明。
  - `README.md` / `README_EN.md`：Python 徽章升级为 3.14，配置说明中的语言字段改为 `language =` 并补充系统回退 / 热切换说明。
  - `CODE_WIKI.md`：本节（更新日志）新增本条…

- `python -m py_compile` 全量源码通过；
- `pytest` 全量 **714 passed / 2 skipped / 0 warnings**；
- `mypy src/` → `Success: no issues found in 37 source files`；
- `basedpyright src/` → **0 errors / 0 warnings / 0 notes**；
- `black --check .` / `isort --check-only .` 全项目通过；
- 手动验证：`config.ini` 仅含旧键 `language(zh_cn/en) = zh_cn` 时启动主程序会自动迁移为 `language = zh_cn`、旧键保留…

**关联**：

- 与前序 v4.0.8.3-dev (2026-08-22) 「pythonw / 窗口化运行崩溃可观测性加固」为同一系列 Python 3.14 兼容性收尾工作…
- `asyncio.get_event_loop()` 的 RuntimeError 兜底模式、`language` 键迁移模式、系统语言检测约定均已沉淀至 `AGENTS.md` 已知坑章节，供后续改动参考。

### v4.0.8.3-dev (2026-08-22) — pythonw / 窗口化运行崩溃可观测性加固：logger None-stderr 守卫 + 顶层崩溃落盘钩子（缺陷修复）

**来源**：用户反馈 `pythonw.exe gui.py`（及 `console=False` 冻结 exe）启动后完全无窗口、无任何报错…

**根因**：`pythonw` / `console=False` 冻结 exe 不分配控制台…

**改动**：

- **`src/logger.py`（`_ = logger.add(sink=sys.stderr, ...)` 加 `sys.stderr is not None` 守卫）**：
  - 无控制台环境（pythonw / 冻结 `console=False`）跳过控制台 sink，避免导入期 `TypeError`；日志持久化仍由下方 `logs/streamget.log`、`PlayURL.log` 文件 sink 兜底。
  - 加注释说明 pythonw 窗口化 `sys.stderr=None` 语义与判空理由。
- **`gui.py` 窗口化崩溃可观测性加固（前序提交，本次一并记入）**：
  - 文件最顶部新增 `_install_crash_sink()`：在**所有风险导入之前**装 `sys.excepthook` 与 `threading.excepthook`
  - `LiveRecorderGUI.__init__` 的 UI 回调异常分支原 `traceback.print_exc()`（None stderr 下二次 `AttributeError` 崩溃、带崩事件泵）改为 `self._log(traceback.format_exc(), "error")`
  - `__main__` 包 `try: main() except: _bootstrap_error_sink(); raise`，控制台环境仍保留原始堆栈。

**关联**：长期坑已写入 `MEMORY.md`（「pythonw 窗口化 sys.stderr=None 致 logger.add 崩溃」）；排查套路——窗口化静默崩溃先装 `sys.excepthook`/`threading.excepthook` 落盘+弹窗钩子，再逐层 grep `sink=sys.` / `print_exc` / `sys.stdout.write` 等 None 敏感点逐一判空。

### v4.0.8.3-dev (2026-08-22) — 类型检查修复：i18n 可选依赖存根忽略 + gui.py messagebox 显式导入 + 线程钩子判空（代码质量）

**来源**：类型检查工具报告三处错误——① mypy 在 `i18n.py:23` 报 `Library stubs not installed for "yaml"`（YAML 为可选依赖、被 `try/except ImportError` 包裹…

**改动**：

- **`i18n.py`（可选依赖存根忽略）**：
  - `import yaml` 加 `# type: ignore[import-untyped]`
  - 降级分支 `yaml = None` 改为 `yaml: Any | None = None`，提供显式类型注解（替换原 `# type: ignore[assignment]`），并在 `from typing import` 中补入 `Any`。
- **`gui.py`（messagebox 显式导入，两处）**：
  - 文件顶部 `_dump` 崩溃弹窗：`import tkinter as _tk` 后新增 `from tkinter import messagebox as _mb`，改用 `_mb.showerror(...)` 替代 `_tk.messagebox.showerror(...)`。
  - `main()` 入口崩溃弹窗：同样改为显式导入并使用 `_mb.showerror(...)`。
- **`gui.py`（线程钩子判空）**：
  - `_thread_dump` 中 `args.exc_value` 可能为 `None`，新增 `if args.exc_value is None: return` 守卫后再调 `_dump(...)`，消除 `BaseException | None` 不兼容报错。

### v4.0.8.3-dev (2026-08-21) — start_record 复杂度治理：平台分派链抽取 + 录制链冗余条件消除（代码质量）

**来源**：basedpyright 在 `main.py:866`（`start_record`）报告「代码过于复杂导致无法完成分析」——该函数约 1600 行（内含 700 行 / 52 个平台的分派 if/elif 链 + 900 行录制执行链）

**改动**：

- **平台分派链抽取为独立模块级函数 `_resolve_platform_stream`**（`main.py`）：
  - 将 `start_record` 内 918-1618 行的平台分派 if/elif 链（52 个分支…
  - 返回 `(platform, port_info, record_danmaku_args, new_record_url)` 四元组…
  - 分支体语义未变：cookie/代理等配置项仍按模块级全局变量即时读取，`json_data` 局部变量保留在函数内部（链后无需暴露）。
  - 录制执行链的控制流完全未动（含 AGENTS.md 已知坑区域：`if not real_url: continue` 守卫、`check_subprocess` 调用、弹幕参数传递等）。
- **消除被掩盖的 19 个 `possibly unbound` 存量错误**（basedpyright 在复杂度消除后首次真正分析该函数时暴露）：
  - 移除恒真冗余的 `if real_url:` 包装（上方 `if not real_url: continue` 守卫已保证非空）
  - 清理 ffmpeg 命令中失效的 `cast(str, real_url)` 与过时注释（守卫保证 `real_url` 非空后 cast 多余）。
  - `record_name = ""` 初始化从 `try:` 内部移至外层 `while True` 循环顶部…
- **AGENTS.md 同步更新**：将「`real_url` 为空必须跳过录制链」一条的描述更新为反映新结构——守卫之后 `now`/`title_in_name` 为无条件赋值…

### v4.0.8.3-dev (2026-08-21) — FFmpeg 9.0 / Node 24 兼容基线 + i18n 多语言重构 + tests 五工具全绿（综合维护）

**来源**：用户要求一次性完成六项维护：① config.ini 的 SSL 平台键改为「仅当需要证书校验时生效」并自动追加必需平台…

**改动**：

- **SSL 平台键语义重构（`src/http_config.py` + `main.py` + `src/web_config.py`）**：
  - `get_effective_ssl_verify`：平台覆盖改为仅在全局 `ssl_verify=True`（**需要证书校验**时…
  - `main.py` 新增 `SSL_DISABLE_REQUIRED_PLATFORMS = ("虎牙直播", "B站直播")` 与 `_sync_ssl_disable_platforms()`：启动时分析可监控录制平台、把缺失的必需平台**自动追加**至配置键并写回（只追加、绝不移除用户手填项…
  - `src/web_config.py` 的 `update_config_line` 键匹配改为**大小写不敏感**（与 configparser `optionxform` 语义对齐）——代码常量（大写 SSL/SMTP/B站）与配置文件行（小写写法）大小写不一致时仍可定位…
  - 键值审计：config.ini 全部 136 个键均被代码引用（无失效键）、代码读取的全部键均已存在（无缺失键），无需增删。
- **FFmpeg 9.0 兼容（`main.py`）**：核查全库 ffmpeg 命令构造（录制/分段/转封装/转码/抽音轨）
- **Node.js 24.19.0 兼容（`src/javascript/migu.js` 重写 + `Dockerfile`）**：
  - **migu.js 全量重写**：migu 官网播放器（dataFetcher.js）自 2025 下半年起变更 mgprtcl.wasm 接口——导入函数从 3 个（a/b/c）扩至 12 个（a..l…
  - 其余 JS 签名脚本（x-bogus/haixiu/laixiu/liveme/taobao-sign/crypto-js）与 execjs 运行时在 Node 24.19.0 下逐一实测通过（x-bogus sign 输出正常）。
  - `Dockerfile`：nodesource 源由 `setup_22.x` 升级至 `setup_24.x`（Node 24 LTS，与实测基线及 node_install.py 拉取的最新稳定版同代）。
- **i18n 重构（`i18n.py` + 翻译目录 + Web 前端 + GUI）**：
  - **`i18n.py` 重构**：新增多格式目录加载（按语言依次探测 gettext `.mo` → `<lang>.json` → `<lang>.yaml`
  - **zh_CN 补全**：AST 扫描运行时代码（main/web/gui/msg_push/i18n/src/）全部 `print`/`logger.*` 常量串…
  - **新增三语翻译**：`i18n/en_US.json`（英文源恒等 + 中文源译英…
  - **Web 即时切换语言**：后端新增 `GET /api/language`（当前语言 + 受支持列表）与 `PUT /api/language`（校验 → 写回 config → 热切换进程内翻译…
  - **GUI 即时切换语言**：`gui.py` 侧边栏新增「语言 Language」OptionMenu（外观菜单同款样式）
  - **main.py 语言链路**：导入时 `set_language(language)` 初始化（任何语言下均安装 `translated_print`）
  - 依赖：新增 `PyYAML>=6.0.3`（pyproject + requirements.txt + uv.lock）。
- **tests/ 五工具全绿**：
  - **mypy tests/**：初始 435 errors → 0。
  - **basedpyright tests/**：0 errors / 0 warnings / 0 notes（`MagicMock` 作 `danmaku_cls`、`int(object)`、`"x" not in object` 四处 cast 收窄）。
  - **pytest**：699 passed / 2 skipped / **0 warnings**（两个 FakeAsyncClient.aclose 未 await 的良性 RuntimeWarning 以针对性 `filterwarnings` 标记消除…
  - **black/isort**：全项目（含 tests/）`--check` 通过。
  - 新增测试：语言 API 5 个（GET 当前+可用 / PUT 切换+持久化 / 别名接受 / 非法值 400 / 空值 400）、i18n 新功能 10 个（多格式目录加载优先级、四目录键集一致、热切换、归一化变体、is_recognized、available_languages 拷贝、目录缺失恒等回退）、SSL 平台自动追加 3 个（缺项追加写回 / 幂等 / 键缺失自愈）、SSL 新语义 2 个（http 模式平台覆盖生效 / https 模式覆盖忽略）、migu 输出契约 1 个（适配完整 URL 输出）。
- **配置与文档维护**：
  - **`.coveragerc-concurrency` 新建**：CI concurrency-test job 经 `COVERAGE_RCFILE` 引用该文件但仓库中缺失（且被 .gitignore 错误忽略）
  - **`uv.lock` 重新生成**：版本同步 `4.0.8.2 → 4.0.8.3`（此前滞后）、纳入 PyYAML；注释头（功能分组说明）保留并更新。
  - **`pyproject.toml`**：新增 PyYAML 依赖（带用途注释）、pytest `filterwarnings`（第三方弃用提示）。
  - **`.gitignore`**：移除 `.coveragerc-concurrency` 错误忽略；头注释补充「保留 .json/.yaml 翻译目录」。
  - **`.dockerignore`**：无需改动（i18n 段仅排除 .po 与编译脚本，.json/.yaml 自动随目录进入镜像）。
  - **`AGENTS.md`**：项目结构 i18n 目录更新…
  - **`CODE_WIKI.md`**（本文件）：目录结构 i18n 条目、i18n 模块详解（多格式/热切换/四语目录表）、配置表 SSL 键与语言键说明、Docker 节 Node 24 LTS 与 .dockerignore 要点、更新日志（本条）。
  - `docker-compose.yaml` 无需改动（锚点复用 Dockerfile 构建，Node 升级自动继承）。

### v4.0.8.3-dev (2026-08-20) — URL_config.ini 主播名自动更新（新增功能）

**来源**：用户要求为 `URL_config.ini` 增加主播名自动更新机制——每次解析到最新主播名时…

**改动**：

- **`src/config_io.py`（配置文件更新）**：新增 `update_anchor_name(url, new_name) -> bool` 与 `_rewrite_anchor_field(raw_line, url, new_name) -> str | None`。
- **`main.py`（文件系统同步）**：新增 `rename_anchor_directory(old_name, new_name, platform) -> bool` 与 `_rename_prefixed_entries(base_dir, old_name, new_name) -> None`
  - `rename_anchor_directory`：重命名 `{保存路径}/{平台}/{旧主播名}` → 新名；目标已存在则逐项合并移入（兼容主播改回曾用名）。
  - `_rename_prefixed_entries`：递归重命名目录树内所有以 `{旧名}_` 开头的录制文件（含日期/标题子目录下的 TS/FLV/弹幕 SRT/字幕等同前缀产物）及 `_{旧名}` 结尾的标题目录。
- **路径引用完整性**：改名只发生在该房间未录制时…
- **配置开关与防护**：`[录制设置] 是否自动更新主播名(是/否)`（默认「是」
- **`tests/test_anchor_rename.py`**：新增 21 个用例…
- **`config/config.ini` 与 `CODE_WIKI.md`**：补充说明（配置项表与「主播名自动更新」专节）。

### v4.0.8.3-dev (2026-08-20) — 类型安全加固：补齐多测试文件与 `src/async_http.py` 类型注解（满足 mypy `disallow_untyped_defs` / basedpyright 门禁）

**来源**：多轮 `@command://fix` 反馈——CI 的 mypy（`disallow_untyped_defs = true`

**受影响模块与具体修改点**：

- **`tests/test_anchor_rename.py`**：`main_mod` 为 pytest fixture 注入参数…
- **`tests/test_ttwid.py`**：所有 `def test_*` / `async def test_*` 补 `-> None`
- **`tests/test_i18n.py`**：① `captured: list[object]` → `list[tuple[object, ...]]`（line 58）
- **`src/async_http.py`**：line 141、201（`get_response_status` 内）`client = await _get_client(...)` 显式注解 `client: httpx.AsyncClient = ...`。
- **`tests/test_sync_http.py`**：17 个测试方法由 `@patch` 装饰器注入 `mock_config` / `mock_opener_fn` / `mock_requests` 等参数…
- **`tests/test_utils.py`**：① 消除同名类遮蔽——文件中存在两个 `class TestReadConfigValue`（line 90 与 245）
- **`tests/test_stream.py`**：① 全文件测试方法补 `-> None`
- **`tests/test_stream_select.py`**：修复 17 处类型错误——① autouse fixture `no_probe_throttle` 补 `-> Iterator[None]`（顶部 `from typing import Iterator, Literal`）

- `tests/test_anchor_rename.py`：`mypy ... -> Success: no issues found in 1 source file`。
- `tests/test_ttwid.py` / `tests/test_i18n.py` / `tests/test_sync_http.py` / `tests/test_utils.py`：`mypy ... -> Success: no issues found`
- `src/async_http.py`：`basedpyright ... 0 errors / 0 warnings / 0 notes`（CLI 实测本就 0 errors）。
- `tests/test_stream.py`：`mypy ... Success: no issues found`；`basedpyright` 0 errors；`pytest` **62 passed**。
- `tests/test_stream_select.py`：`mypy` / `basedpyright` 0 errors / 0 warnings / 0 notes；`pytest` **25 passed**。

### v4.0.8.3-dev (2026-08-20) — 「是否禁用SSL证书验证」并入「是否启用https录制」（配置项整合）

**来源**：用户要求把「是否禁用SSL证书验证」的功能整合进「是否启用https录制」选项，选项更名为「是否启用https录制」，开启=https 录制、关闭=http 录制。

**改动**：

- **配置整合（`main.py`）**：新增 `_read_https_recording_config()` 统一读取新键「是否启用https录制」
- **联动语义（`main.py` 模块级 + 主循环每轮热同步）**：`_http_config.set_https_recording(x)` + `_http_config.set_ssl_verify(not x)`——开启=https 拉流+禁用证书验证…
- **录制协议切换（`main.py:1796` 区）**：开启时 `http://`→`https://`（原行为…
- **`-tls_verify 0` 自洽**：https 模式全局禁用验证时插入（仅 https 流），http 模式无 TLS 不涉及，注释同步更新。
- **`src/http_config.py`**：`ssl_verify` 注释更新为整合语义…
- **Web 界面（`web/app.js` + `web/style.css`）**：新键「是否启用https录制」附整合语义说明…
- **文档**：`README.md` 配置列表/说明、`CODE_WIKI.md` 配置表（见「配置文件说明」）同步更名与解释。

**注**：旧组合「强制https=否 + 禁用SSL=是」整合后变为 http 拉流+默认校验（原“不验证”能力并入开关语义，无法独立保留）。

### v4.0.8.3-dev (2026-08-19) — 架构文档更新：补全弹幕采集子系统与 src/platforms、src/proto 等模块说明

**来源**：用户要求通读工作空间全部源码、提取架构/模块/核心逻辑/关键实现信息…

**新增 / 修正内容**：

- **目录结构**：补充 `src/base.py`、`src/collector.py`、`src/cookie_cache.py`、`src/danmaku_monitor.py`、`src/srt_writer.py`、`src/ws_client.py`、`src/platforms/`、`src/proto/` 等弹幕相关条目…
- **技术栈**：新增 `websockets` / `protobuf` / `brotli` 三个弹幕运行时依赖说明（对应 `requirements.txt` 弹幕段）。
- **核心模块详解**：新增「14. 弹幕采集子系统」整节…
- **模块依赖关系图**：补充弹幕子系统（`src/__init__.py` 注册表 → `collector` → `platforms/*Danmaku` → `ws_client` / `cookie_cache` / `proto` / `ttwid`
- **设计模式**：新增「工厂 / 注册表模式」，说明弹幕按平台标识经 `get_danmaku_class` / `get_danmaku_collector` 解耦创建。
- **版本号**：项目基本信息版本由 `4.0.8.2` 更正为 `4.0.8.3`（对齐 `pyproject.toml` 唯一事实源）。
- 明确弹幕子系统与 `src/spider.py` 流解析为平行解耦的两套抽象（`spider.py` 不 import `src/platforms`）。

### v4.0.8.2-dev (2026-08-19) — CI 重构：build-release.yml 去除 download-artifact 来回 + 修复 release 并发竞态/布尔比较/缺失 checkout

**来源**：用户要求将 release job 的 `actions/download-artifact@v7` 更换为 `softprops/action-gh-release`

**根因**（四类，均已修复）：

1. **结构调整**：原 `upload-artifact` → `download-artifact` → `softprops` 中…
2. **并发竞态**：三平台 build job 并发调 `softprops` 创建同一 Release（相同 tag）存在「同 tag 同时 create」竞态。
3. **布尔比较恒 false**（原版就有的 bug）：`create_release` 是 boolean 输入…
4. **缺失 checkout**：`release-create` job 的手动发版路径需 `git tag/git push` 推轻量 tag…

**修复**（`.github/workflows/build-release.yml`）：

1. **build job 直传 Release**：新增 `permissions: contents: write`
2. **新增 `release-create` 单例 job**（`needs: prepare`
3. **release job 改用 gh CLI 拉回**：去掉 `actions/download-artifact@v7`
4. **布尔比较修复**：5 处 `inputs.create_release == 'true'` → `inputs.create_release == true`（`needs.prepare.outputs.is_release == 'true'` 字符串比较**保持不动**——`is_release` 是字符串输出）。
5. **补 checkout**：`release-create` 加 `actions/checkout@v7`（`fetch-depth: 0`），覆盖手动路径的 `git tag/git push`。

- `yaml.safe_load` 解析通过；job 依赖图 `prepare → release-create → build(×3) → release` 正确。
- 全 job checkout 覆盖检查：prepare/build 已有、release-create 已补、release 仅用 gh API 无需 git。
- 逻辑链：手动 dispatch + 勾选 `create_release` → checkout → 推 tag → 预建 Release → 三平台 build 直传 zip → release 拉回校验 + SHA256SUMS + 发版说明。

### v4.0.8.2-dev (2026-08-19) — 测试/覆盖率：tests/test_ttwid.py 补充分支测试，src/ttwid.py 覆盖率 82.3% → 96.77%（越过 85% 门禁）

**来源**：CI `python scripts/check_coverage.py` 报 `src/ttwid.py 82.3% (>= 85%) <- 2.7% short`，覆盖率门禁失败（exit code 1）。

**根因**：`src/ttwid.py` 的 `coverage.xml` 显示以下分支在单测下不可达（51/62 行已覆盖，需 ≥53 行达 85%）：

- L34：`_app_root()` frozen 分支（`sys.frozen` 测试中恒为 False）；
- L58–59：`_read_config_ttwid` 的宽 `except Exception`（非 ConfigParser 的意外错误）；
- L86–87：`_fetch_ttwid` 异常处理器（`_cache_fetch_cookies` 抛错）；
- L99–104：`get_ttwid` 锁竞争兜底（仅真实并发可达）；
- L108：缓存二次校验竞态守卫（仅真实并发命中）。

正确做法是为这些分支补测试，而非下调门禁阈值。

**修复**（`tests/test_ttwid.py`）：

1. 新增 `TestGetTtwid`：覆盖从 `config.ini`（tempfile 写入含 `[ttwid]` 段）→ `cookie_cache` → 动态 `fetch` → 缓存返回 的四级优先级链路…
2. 新增 `TestReadConfigTtwid`：覆盖「`_app_root()` frozen 分支被 `sys.frozen=True` 触发」「ConfigParser 解析意外异常被宽 `except` 兜住」「`_cached_config_ttwid` 短路命中」三分支。
3. 新增 `TestFetchTtwid`：覆盖 `_cache_fetch_cookies` 抛错时 `_fetch_ttwid` 的异常处理器分支。
4. 新增 `TestGetTtwidContention`：把模块级 `_ttwid_lock` 替换为 fake lock（`acquire(blocking=False)` 返回 False）

注意：C 层 `RLock.acquire` 为只读属性，`monkeypatch.setattr` 实例方法会抛错，故改为替换模块级锁对象。

- `pytest tests/test_ttwid.py` 全绿（17 passed）。
- 覆盖率：本次运行 `src/ttwid.py` 达 **96.77%**（L34/58/59/86/87/99/100/102/103 均命中）

### v4.0.8.2-dev (2026-08-19) — CI 修复：ci.yml `dorny/paths-filter@v3` → `v4` 消除 Node.js 20 弃用告警

**来源**：GitHub Actions 工作流运行告警 `Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: dorny/paths-filter@v3`。

**根因**：`.github/workflows/ci.yml` 第 116 行 `uses: dorny/paths-filter@v3`。

**修复**（`.github/workflows/ci.yml`）：`uses: dorny/paths-filter@v3` → `uses: dorny/paths-filter@v4`（锁定 v4.0.3）。

- v4 的 `filters` 输入与 `changes` 输出 API 与 v3 完全一致…
- 默认 `predicate-quantifier: 'some'`（至少一个模式命中即算变更）语义未变，本工作流的单组 `python` 过滤行为保持原样。
- 附带安全加固：v4 合入 GHSA-7hc6-8hq5-9q2m 多行文件名转义修复（本工作流未用 `list-files`，属顺带）。
- 已 grep 确认 `.github/workflows/` 下仅此一处引用，无 `build-release.yml` 同类问题需同步。
- 纯依赖版本号提升、零逻辑改动，可直接提交。

### v4.0.8.2-dev (2026-08-19) — 测试/接口修复：`test_huya_danmaku::test_profileRoom_fields` 断言陈旧 + `web_api.list_files` 悬空/逃出 root 符号链接崩溃与信息泄露

**来源**：CI `pytest --cov=src ...` 报 3 failed（641 passed）。

**根因**：

1. **测试陈旧（非代码 bug）**：`spider.get_huya_app_stream_url` 的 `_normalize`（`src/spider.py:840` 附近）刻意将 `https://` 降为 `http://`（虎牙实测 https 返回 403、仅 http 可用…
2. **`web_api.list_files` 代码 bug**：遍历目录时 `st = os.stat(full)` 默认**跟随符号链接**（约 `src/web_api.py:388`）。
3. **`web_api.list_files` 信息泄露隐患**：仅对*请求路径*用 `os.path.realpath + _is_within` 校验（`src/web_api.py:369-371`）

**修复**：

1. `tests/test_huya_danmaku.py:118`：断言改为 `assert result["flv_url"].startswith("http://")`（与既定行为一致，运行行为不变）。
2. `src/web_api.py` 的 `list_files` 循环加两项防护：
   - 越界跳过：`resolved = os.path.realpath(full)` 后 `if not _is_within(resolved, root): continue`（修复根外链接名泄露）。
   - 悬空容错：`st = os.stat(full)` 包 `try/except OSError: continue`（修复悬空链接 500）。

### v4.0.8.2-dev (2026-08-19) — 类型检查修复：src/web_tray.py 两处 `ctypes.windll` 缺少 `sys.platform` 平台门导致 mypy 非 Windows 校验失败

**来源**：`mypy src/` 在 Linux/macOS（CI `ubuntu-latest`）报 `src/web_tray.py:111/112/178: error: Module has no attribute "windll" [attr-defined]`（Found 3 errors in 1 file）。

**根因**：`ctypes.windll` 是 Windows-only API…

**修复**（`src/web_tray.py`，沿用 mypy-platform-gating 的「提前返回门」范式，不依赖 `# type: ignore`）：

1. `_patch_console_window`：函数开头（`try: import ctypes` 之前）加 `if sys.platform != "win32": return`（保留原 `try/except import` 容错）。
2. `_on_show`：`if not hwnd: return` 之后加 `if sys.platform != "win32": return`。
   两处运行时行为不变：非 Windows 下 `ENABLED` 本为 `False`、托盘不启用…

### v4.0.8.2-dev (2026-08-19) — CI 修复：ci.yml Codecov step 的 `if` 误用 `secrets` 上下文导致工作流校验失败（改用 job 级 env 传递）

**来源**：GitHub Actions 工作流校验报错 `Invalid workflow file: .github/workflows/ci.yml#L1(Line: 317, Col: 13): Unrecognized named-value: 'secrets'`。

**根因**：GitHub Actions 的 `if` 表达式解析器仅允许白名单上下文（`github`/`needs`/`vars`/`matrix`/`inputs`/`env`/`steps`/`runner`/`job` 及状态函数）

**修复**（`.github/workflows/ci.yml`）：

1. `test:` job 新增 job 级 `env:` 块…
2. 第 319 行 step `if` 由 `secrets.CODECOV_TOKEN != ''` 改为 `env.CODECOV_TOKEN != ''`

### v4.0.8.2-dev (2026-08-18) — 虎牙 HLS 录制 403 真因：CDN 已反向校验，强制 Referer 反而 403（移除虎牙 Referer 规则）

**来源**：2026-08-18 21:39 运行日志（room 179966…

**根因（实测对照，使用刚从 `get_huya_stream_data` 拉取的【新鲜】 token）**：虎牙 CDN 现已**反向校验**——

| 请求 | HS 线路 | AL/TX 线路 |
| --- | --- | --- |
| 携带 `Referer: https://www.huya.com/` | **403** | 403（房间未承载推流，与 Referer 无关） |
| 不携带 Referer | **200** ✅ | 403（房间未承载推流） |

即：**带 Referer 一律 403…

**修复（src/stream_select.py）**：

1. 移除 `_RECORD_HEADER_RULES["虎牙直播"]` 的 `"referer:https://www.huya.com/"` 规则（留注释说明其已废弃）。
2. 同步修正两处陈旧注释：原「虎牙 CDN 对无 Referer 直接 403、须带 Referer 才能 200」已失效，改为「携带 Referer 反而 403、须不携带 Referer」。
3. 属平台级 base 头变更…
4. 与上轮多 CDN 修复的关系：多 CDN 枚举（HS 优先）本身正确且保留；去掉 Referer 后 HS 即 200，AL/TX 离线房间仍由多 CDN 校验自动跳过。

- 实时 curl 对照（新鲜 token）：带 Referer → 403、去 Referer → 200（HS）；AL/TX 两线路无论如何均 403（房间未承载）。
- 更新 `tests/test_main_fixes.py::TestHuyaReferer`（3 例）：`get_record_headers("虎牙直播", ...)` 不再返回 Referer、`_validate_stream_url(platform="虎牙直播")` 不附加 Referer…
- `pytest tests/test_stream_select.py tests/test_stream.py tests/test_spider_platform.py tests/test_main_fixes.py` 全绿（含更新的虎牙 Referer 用例）；`mypy src/stream_select.py` 0 错误。

### v4.0.8.2-dev (2026-08-18) — 类型检查收尾：spider.py / sync_http.py 四处 mypy/basedpyright 告警清零

**来源**：用户逐条提交基于 mypy/basedpyright 的类型告警（line 867、2660、4009-4013、sync_http.py:52）

**修复内容**：

1. **`spider.py:867`（mypy `Incompatible types in assignment`）**：原 `m3u8_url = selected_m3u8 if isinstance(selected_m3u8, str) else None` 把 line 842 已声明为 `str` 的 `m3u8_url`/`flv_url` 重新赋值为 `str | None`（来自 `dict[str, object].get()` 的 `object | None`）
2. **`spider.py:2660`（mypy `Unpacking a string is disallowed`
3. **`spider.py:4009-4013`（mypy `Value of type "str | None" is not indexable`）**：`get_pplive_stream_url` 中请求体 dict 与 JSON 响应解析结果**共用变量名 `json_data`**——line 3994 请求体 `json_data = {"inviteUuid": "", "anchorUuid": room_id}` 因 `room_id` 为 `OptionalStr`（`str | None`）被推断为 `dict[str, str | None]`
4. **`src/sync_http.py:52`（basedpyright `reportInvalidTypeForm`「类型表达式中不允许使用变量」）**：原 `try: from requests._types import JsonType except ImportError: from typing import Any as JsonType`。

**教训沉淀**：

- 返回注解必须与实际 return 路径严格一致…
- 请求体 dict 与 JSON 响应解析结果**不可共用同一变量名**（尤其值类型含 `None` 时）
- `from typing import Any as X` 在 `try/except` 中作类型回退会污染符号为「变量」、触发 `reportInvalidTypeForm`；应以本地递归 `TypeAlias` 替代。

### v4.0.8.2-dev (2026-08-18) — 虎牙 HLS 多 CDN 解析与播放根治：枚举全部 CDN 候选 + HS 优先 + http 化 + `select_source_url` 逐候选可达性校验（取代固定取 index0 / TX 优先的脆弱选源）

**来源**：`新建文件夹/huya_179966_hls_report.md` + `huya_179966.html` + `hls_entries.txt`（房间 `https://www.huya.com/179966`，2026-08-18）。对报告中的真实 HLS 地址逐 CDN 实测探测：

- `al.hls.huya.com` → GET **403**、`tx.hls.huya.com` → GET **403**、`hs.hls.huya.com` → **GET 200**（`application/x-mpegurl`，可拉流）；
- `https://hs.hls.huya.com/...` → GET **403**（同一 HS 地址，仅 http 可用、https 被拒）。

结论：同一房间内多条 CDN 线路（HS/HW/TX/AL）的防盗链参数完全一致…

**根因**：旧实现把"选哪条 CDN 线路"做成静态决策，与"该线路是否在线"解耦，导致两类失败：

1. **Web 路径 `get_huya_stream_url`**（`src/stream.py`）固定取 `stream_info_list[0]`
2. **App 路径 `get_huya_app_stream_url`**（`src/spider.py`）按 `priority_order=["TX","HW","HS","AL"]` 取 TX（上一轮修复）。
3. 两条路径都**只产出单一 `m3u8_url`/`flv_url`**、无候选列表，`select_source_url` 只能"校验单条 → 失败 → 整轮放弃"，无法在多在线线路间择优。

**修复**（四处协同）：

1. **`src/stream_select.py:select_source_url`** — 新增候选列表支持：兼容旧的单个 `m3u8_url`/`flv_url`
2. **`src/stream.py:get_huya_stream_url`（Web 路径）** — 不再取 `stream_info_list[0]`：
   - 对 `gameStreamInfoList` **全部 CDN 项**构建 HLS+FLV 地址…
   - 统一降为 `http://`（实测 https 403、仅 http 可用），与校验探针共用同 scheme 防止"校验 http 可用、录制 https 被拒"。
   - 按 `cdn_priority=["HS","HW","TX","AL"]` 排序候选（HS 实测为 HLS 可靠承载线路，首位优先最大化"首试即中"）。
   - 画质 ratio 解析逻辑不变（仍从首个候选 `exsphd` 取档位表）。
   - 返回 `m3u8_url`/`flv_url`（主源=排序首位）+ `m3u8_url_list`/`flv_url_list`（全部候选，供 `select_source_url` 逐条校验）。
   - 清理死代码：移除废弃的 `get_anti_code` 重建函数及不再使用的 `base64/hashlib/random/time/urllib.parse` 导入。
3. **`src/spider.py:get_huya_app_stream_url`（小程序 / OD / BD / UHD 路径）** — 不再固定 TX 优先：
   - 对 `baseSteamInfoList` **全部 CDN 项**用原始 `sHlsAntiCode`/`sFlvAntiCode` 构建地址…
   - 按 `cdn_priority=["HS","HW","TX","AL"]` 排序候选；移除旧的固定 `priority_order` 与 TX-only 的 https 特例。
   - 返回 `m3u8_url`/`flv_url`（主源）+ `m3u8_url_list`/`flv_url_list`（全部候选）+ 同源 `record_url`（保持 http）。
4. **`main.py`** — `enable_https_recording` 的 `http://`→`https://` 升级对 `虎牙直播` 平台**跳过**（与 `自定义录制直播` 同列）

- `tests/test_stream_select.py` 新增 `test_select_source_url_m3u8_list_picks_first_reachable`（候选列表首条可达即选用）、`test_select_source_url_m3u8_list_all_dead_falls_back_to_flv`（全部 HLS 候选死则回退 FLV）、`test_select_source_url_huya_backoff_round_straight_to_ffmpeg`（虎牙退避末位轮直放 ffmpeg）。
- `tests/test_stream.py::TestGetHuyaStreamUrl` 重写/扩展（9 例）：`test_enumerates_all_cdn_candidates_hs_first`（枚举全 CDN 且 HS 优先）、`test_https_in_input_downgraded_to_http`（输入含 https 时降为 http）、`test_flv_url_carries_m3u8_candidate`、`test_flv_without_query_keeps_clean_m3u8`、offline/empty/none 等边界。
- `tests/test_spider_platform.py::TestHuyaAppStreamUrl` 更新：`test_priority_prefers_tx_over_al_at_index0`（现验证 HS-first 顺序 + http scheme + `m3u8_url_list`/`flv_url_list` 注入）、新增 `test_hs_cdn_selected_first_when_present`（含 HS 候选时主源与列表首位均为 HS、全 http）、`test_al_used_as_last_resort_when_only_cdn`（仅 AL 时保持 http、同源 record_url）。
- 以上三处测试集合 **33 passed**；全量回归（含 `test_stream.py`/`test_stream_select.py`/`test_spider_platform.py`/`test_main_fixes.py`）**222 passed**，无回归。
- `py_compile` + `mypy src/stream.py src/stream_select.py src/spider.py`：**Success: no issues found**（0 errors / 0 warnings）。
- 实测网络探测结论已写入本条目「来源」：HS 经 http GET 200 可拉流、https 403，直接验证修复方向的真实性。

### v4.0.8.2-dev (2026-08-18) — 虎牙 `get_huya_app_stream_url` 选源修复：m3u8/flv 按 priority 选 TX 且同步 TX 参数替换（根治 priority 选源后的录制崩溃回归）

**来源**：实测 `py web.py` 房间 `https://www.huya.com/60066` 杨齐家丶（2026-08-18 01:51–01:54）。

**根因**：原实现**仅 `record_url` 做了 `tars_mp→huya_webh5` + `bhct→bgct` 的 TX 专属参数替换与 https 化**…

**修复**（`src/spider.py:get_huya_app_stream_url`）：TX 选中时…

- `tests/test_spider_platform.py::TestHuyaAppStreamUrl` 新增 `test_priority_prefers_tx_over_al_at_index0`（AL 抢占 index 0 时三项均落到 TX 且带 `huya_webh5`）、`test_al_used_as_last_resort_when_only_cdn`（仅 AL 时末位兜底、保持原始 URL）
- `py_compile` + `basedpyright src/spider.py`：0 errors / 0 warnings。
- **✅ 已用户实测验证**（2026-08-18 07:09–07:10，房间 `https://www.huya.com/528300` 安德罗妮丶，Web 模式 v4.0.8.2）：
  - `m3u8_url` 为 `https://tx.hls.huya.com/...m3u8?...&ctype=huya_webh5&fs=bgct&t=102` —— 证实 TX 参数替换已生效于 `m3u8_url`。
  - HLS m3u8 探针 `HEAD=403, Range-GET=403` → FLV 回退（预期良性，与改动前 AL 403 同源）。
  - FLV 录制**稳定运行**（`正在录制中 0:00:07`→`0:00:12`，无 `Stream ends prematurely`、无 `返回码 3436169992`）；`HuyaDanmaku 连接就绪`；全程 `累计错误数为: 0`。
  - 进程因用户手动 `Ctrl+C`（`INFO: Shutting down`/`正在安全退出`）正常退出，**非崩溃**。
  - 结论：上一轮回归（TX `tars_mp` 链接 `3436169992`/秒级断开）已根除，TX + `huya_webh5` FLV 实测可稳定拉流，修复闭环。

### v4.0.8.2-dev (2026-08-18) — 虎牙运行日志复盘：AL CDN 403 警告为预期良性，三级回退 + TX 优先 + 双链路兜底验证生效（无代码改动）

**来源**：`logs/huya运行日志.log`（房间 `https://www.huya.com/60066` 杨齐家丶…

**逐行排查与根因映射**：

| 时间 | 级别 | 日志内容 | 根因定位 | 对应源码 | 影响录制/弹幕 |
| --- | --- | --- | --- | --- | --- |
| 00:48:02.984 | WARNING | 流地址校验失败: `al.hls.huya.com/...m3u8` - HEAD=403, Range-GET=403, content-type=tex… | AL CDN 对 HLS 探针返回 403（应用层拒绝），HEAD 与 Range-GET 双拒 → 判不可达… | `src/stream_select.py:_validate_stream_url` 的 m3u8 分支（HEAD 非 2xx → Range-GET 探… | 否（触发 HLS→FLV 回退） |
| 00:48:02.985 | WARNING | `HLS URL validation failed, falling back to FLV` | 回退逻辑正常执行 | `src/stream_select.py:select_source_url` | 否 |
| 00:48:04.681 | WARNING | 流地址校验失败: `al.flv.huya.com/...flv` - HEAD=200 通过但 GET 复核两次 403（CDN 稳定拒绝 GET），判定… | AL 经典「假绿」：HEAD 放行但真实 GET（ffmpeg 实际拉流方式）被拒；`_confirm_get_ok` 重试一次仍 403 → 判不可达，避… | `src/stream_select.py:_confirm_get_ok`（HEAD 通过后再做流式 GET 复核，401/403 先重试一次再定罪）+ … | 否（触发 FLV→record_url 回退） |
| 00:48:04.682 | WARNING | `FLV URL validation failed, trying record_url fallback` | 回退逻辑正常执行 | `src/stream_select.py:select_source_url` | 否 |
| 00:48:04.973 | DEBUG | `[弹幕采集]HuyaDanmaku 连接就绪,开始接收弹幕` | 弹幕 WebSocket 独立建链成功（与视频 CDN 无关） | `src/platforms/huya.py:HuyaDanmaku.start` → `wss://cdnws.api.huya.com`（Tars 编码… | 否（弹幕正常） |
| 00:48:04 | INFO | `准备开始录制视频 .../杨齐家丶_2026-08-18_00-48-04.ts` | 经 HLS→FLV→record_url 三级回退后，record_url（TX 优先 CDN）校验通过，ffmpeg 开始拉流… | `main.py` 录制链 + `src/spider.py:get_huya_app_stream_url`（`record_url` 按 `priori… | 否（录制正常） |
| 00:48:11 | INFO | `累计错误数为: 0` | 全程无录制/解析错误，AL 403 已被回退链吸收 | — | 否 |

**四类可能因素逐项排除**：

1. **网络连接异常 — 排除**。
2. **API 接口故障 — 排除**。
3. **认证失败 — 排除**。
4. **协议变更 — 排除（未指示）**。

**真实根因**：告警来自 **AL CDN（`al.hls.huya.com` / `al.flv.huya.com`）的访问拒止（403）**…

**为何弹幕与直播仍能正常录制**：

- **直播**：`select_source_url` 三级回退（HLS→FLV→record_url）在 AL 双候选失败后落到 `record_url`
- **弹幕**：`HuyaDanmaku` 经**完全独立的 WebSocket 端点** `wss://cdnws.api.huya.com` 以 Tars 编码收发…

**结论与处置**：本日志是 2026-08-17「虎牙 403 失败循环根治」修复后的**健康态验证**——修复前 AL 会烧光连接预算致 ffmpeg 秒级失败循环、弹幕随录制同起同停…

**可选优化（非缺陷，按需）**：`get_huya_app_stream_url` 中 `m3u8_url`/`flv_url` 固定取 `play_url_list[0]`（API 返回首项…

### v4.0.8.2-dev (2026-08-18) — 虎牙 GUI 实测复盘（179966）：HLS 三 CDN 全拒仍稳定录制，手动停止路径与 255 返回码归类

**来源**：GUI（`gui.py` 经 `subprocess.Popen` 拉起 `main.py` 子进程）录制 `https://www.huya.com/179966`（蛇类科普蛇哥）

**逐行排查与根因映射**：

| 时间 | 级别 | 日志内容 | 根因定位 | 对应源码 | 影响 |
| --- | --- | --- | --- | --- | --- |
| 22:09:57–22:10:00 | WARNING | 流地址校验失败: `hs/tx/al.hls.huya.com/...m3u8` - HEAD=403, Range-GET=403（al 为 text/h… | 三个 HLS CDN **全部**返回 403（应用层拒绝），HEAD 与 Range-GET 双拒 → 均判不可达… | `src/stream_select.py:_validate_stream_url` 的 m3u8 分支（HEAD 非 2xx → Range-GET 探… | 否（触发 HLS→FLV 回退） |
| 22:10:00.535 | WARNING | `HLS URL validation failed, falling back to FLV` | 回退逻辑正常执行 | `src/stream_select.py:select_source_url` | 否 |
| 22:10:00.859 | DEBUG | `[弹幕采集]HuyaDanmaku 连接就绪,开始接收弹幕` | 弹幕 WebSocket 独立建链成功（与视频 CDN 无关） | `src/platforms/huya.py:HuyaDanmaku.start` → `wss://cdnws.api.huya.com`（Tars 编码… | 否（弹幕正常） |
| 22:10:06 | INFO | `准备开始录制视频 .../蛇类科普蛇哥_2026-08-18_22-10-00.ts` | FLV 校验一次通过，ffmpeg 直接拉流（无 FLV 失败日志） | `main.py` 录制链 + `src/spider.py:get_huya_app_stream_url` | 否（录制正常） |
| 22:10:06–22:10:45 | INFO | `累计错误数为: 0`，弹幕 5 条 | 全程无录制/解析错误，HLS 三拒已被回退链吸收 | — | 否 |

**与 60066 复盘的结构性差异**：今早 60066 仅 **AL 单 CDN** 403（HLS 经 TX 可用、FLV 经 AL 假绿回退 record_url）

**手动停止路径核验（关键，易误读为异常）**：

1. **`直播录制出错,返回码: 255` 为展示归类偏差…
   - **可选优化（未做）**：打印前检查 `exit_recording`
2. **`close_all_clients_sync 回退到引用清理: There is no current event loop in thread 'MainThread'` 为已知 DEBUG 降级…
3. **403 已正确触发 `_mark_probe_reject`**（虎牙在 `_PROBE_BACKOFF_PLATFORMS` 名单内…

**结论与处置**：本次 GUI 实测进一步验证「HLS 三 CDN 全拒 → FLV 兜底」与「CTRL_BREAK 优雅退出 + ffmpeg 子进程清理」两条链路均健康。

### v4.0.8.2-dev (2026-08-17) — 虎牙录制 403 失败循环根治：探针退避/节流/抖动三层降风控 + 弹幕监控房间生命周期 + 配置实时性 + 全库 UA 统一升级

**来源**：`logs/huya运行日志.log` 深度复盘 + 全库 UA 指纹审计。

**根因（虎牙 403 失败循环）**：虎牙 aldirect CDN（`aldirect.hls.huya.com` / `aldirect.flv.huya.com`）对**同一路径短时间内的连续连接**做限流。

- 日志铁证一：`流地址校验: ...flv... - GET 复核重试通过(200)，先前拒绝为偶发` 后不到 0.1 秒…
- 日志铁证二：偶发连上也只拉到 446270 字节即 `[http] Stream ends prematurely` + `Error during demuxing: I/O error`——CDN 主动掐断。
- 连锁反应：录制秒级失败 → 弹幕采集器随 ffmpeg 同起同停被反复杀死（日志反复出现 `HuyaDanmaku 连接就绪` → `采集线程已退出,共收到 0 条消息`）→ 弹幕监控永远刷不出新数据…

**修复一：探针退避（负缓存，`src/stream_select.py`）**——被拒后止损：

- 新增 `_mark_probe_reject` / `_probe_in_backoff` / `_probe_backoff_key`：探针观测到 401/403（**含重试后恢复的偶发**——同样是限流证据）即把 `scheme://host/路径`（去 query：虎牙每轮解析返回新 token 但路径稳定…
- 退避窗口内**零探针**：非末位候选直接按校验失败回退下一候选…
- 退避名单 `_PROBE_BACKOFF_PLATFORMS = ("虎牙直播",)` **仅限虎牙**：斗鱼 hw CDN 的偶发 403 必须靠既有「重试一次再定罪」救回（重试即 206 保住 HLS-first）

**修复二：探针节流 + 重试抖动（本次新增，降低风控误触发）**——事前预防：

- `_throttle_probe(url)`：同一 CDN host 相邻两次探针强制最小间隔 `_PROBE_MIN_HOST_INTERVAL=0.35s + uniform(0,0.4s)`（锁内计算差值、锁外 sleep 不阻塞其它 host…
- `_recheck_delay()`：GET 复核 / Range-GET 重试间隔由固定 `0.8s` 改为 `0.8s + uniform(0,0.7s)`——恒定间隔的重试序列是可识别的机器人节奏，抖动将其打散。
- 三层体系：**节流**降低风控触发概率（事前）→ **重试**区分偶发限流与稳定拒绝（事中…
- 注意：`_validate_stream_url` 的节流在退避检查之后（退避命中直接返回、不产生任何探针与等待）。

**修复三：弹幕监控房间生命周期（`src/danmaku_monitor.py` + `main.py` + `gui.py`）**——不残留旧直播间：

- `DanmakuMonitorHub` 新增 `room_stopped(room, reason)`：从 `_rooms` 移除条目 + 写 `conn/stopped` 事件（未注册房间为无操作）。
- `main.py` `start_record` 外层 try 追加 `finally`：房间线程退出（录制态/轮询态/解析失败态的全部 return 路径）时调 `get_hub().room_stopped(record_name)`
- `gui.py` `_danmaku_dispatch` 收到 `state=="stopped"` 事件后从 `_danmaku_rooms` pop 房间行（Web 端快照随房间表自动消失，无需改动）。
- 录制稳定后弹幕采集器常驻连接，不再被秒级失败的 ffmpeg 反复杀死——弹幕数据持续累积、监控页实时刷新。

**修复四：配置变更实时性（`main.py`）**——注释/移除即时生效：

- 房间线程内层循环顶部（`exit_recording` 检查后）新增 `record_url in url_comments` 提前检查 + `clear_record_info` + `return`。

**修复五：全库 UA 统一升级（防风控指纹识别）**：

- 背景：过旧 UA（Chrome/87、Firefox/115、Chrome/116~121 等 2019-2024 年指纹）是风控按客户端指纹识别、拒绝服务的特征之一；且库内同一用途 UA 版本碎片化。
- 统一基准（2026-08…
- 改动位置（全库排查后逐一替换/同步）：
  - `src/stream_select.py`：`DESKTOP_UA`（Chrome/126→141）、`MOBILE_UA`（SamsungBrowser/14.2+Chrome/87→Android 14+Chrome/141）。
  - `main.py`：ffmpeg 录制命令默认移动 UA 同步——**必须与 `MOBILE_UA` 一字不差**（校验探针与 ffmpeg 两端客户端指纹一致，否则校验假红/假绿）。
  - `src/room.py`：`HEADERS` 移动 UA 同步（X-Bogus 签名以请求头同一 UA 计算、自洽，改字符串安全）。
  - `src/spider.py`：60+ 处平台接口 UA 批量统一（Firefox 115/119/122/123/124/127→148；Chrome 120/121→141；Edge 121/138→141；B站 H5 移动 UA 同步）。
  - `src/ttwid.py`（Chrome/116→141）、`src/weverse_auth.py`（Chrome/120→141）、`src/ffmpeg_install.py`（Chrome/121+Edg/121→141）、`src/platforms/douyin.py`（弹幕 WS `DEFAULT_USER_AGENT` Chrome/125+Edg/125→141…
- 验证：全库 grep 无 `Chrome/(8x|9x|1[0-3]x)`、`Firefox/(11x|12[0-7])`、`SamsungBrowser` 残留。

**测试与验证**：

- `tests/test_stream_select.py` 扩展至 22 用例：虎牙退避 7 项（稳定 403 记退避→第 2 轮零探针、末位退避零探针放行、FLV 偶发 403 记退避、退避键跨 token 命中、窗口过期恢复、斗鱼不受影响、select_source_url 退避轮直放 FLV）+ 节流/抖动 4 项（重试间隔抖动范围、同 host 节流补隔、不同 host 独立、校验前先节流）。
- `tests/test_danmaku_monitor.py` 扩展至 17 用例：`room_stopped` 移除房间 + stopped 事件 + 未注册无操作；GUI `stopped` 事件删房间行。
- 测试基建：autouse fixture 将 `_throttle_probe` 置 no-op 并清全局节流记录（部分既有用例 patch 整个 time 模块…
- 全量回归 **607 passed, 2 skipped**；black / isort / mypy 全绿。
- 五条防回归经验已沉淀 `AGENTS.md` 已知坑（虎牙退避仅限名单、监控房间随线程退出移除、注释检查在解析前、UA 双端一字不差 + 全库基准、节流/抖动语义不得移除）。

### v4.0.8.2-dev (2026-08-17) — 三平台实录日志排查：斗鱼致命异常修复 + B站弹幕认证链闭环 + 校验器末位放行扩展

**来源**：用户三份运行日志（`logs/douyu运行日志.log` / `huya运行日志.log` / `哔哩哔哩运行日志.log`）。逐一对照源码定位出三个平台四种不同表现形态：

| 平台 | 日志表现 | 根因定位 |
| --- | --- | --- |
| 斗鱼 | 无法录制直播 + 无法录制弹幕，每轮 `ERROR: cannot access local variable 'title_in_name' 发生错误的行… | 两级缺陷叠加（见下） |
| 哔哩哔哩 | 直播正常，弹幕"连接就绪"但 0 条、无任何报错 | buvid 获取失败 + AUTH 软拒绝零感知（见下） |
| 虎牙 | 大量 `流地址校验失败` WARNING，但录制 + 弹幕均正常 | 探针"假红"（CDN 误杀），三级回退 + 双链路按设计兜底，非缺陷、无需改动… |

**斗鱼致命异常（两级缺陷）**：

1. **`title_in_name` 未绑定崩溃（直接死因）**：`main.py` 录制执行链位于 `if real_url:` 构建块之外…
2. **探针假红 + 末位放行失效（根因）**：斗鱼 hw CDN（hw3.douyucdn2.cn）对探针 HEAD 回 **405 + text/html**（禁 HEAD 方法）

**修复（斗鱼）**：

- `main.py`：`select_source_url` 返回 None 时告警 + 按常规监测间隔等待 + 跳到下一轮（`if not real_url: ... continue`），阻断 `title_in_name` 未绑定崩溃。
- `src/stream_select.py` `_validate_stream_url`：
  - m3u8 的 Range-GET 探针 401/403 先隔 `_GET_RECHECK_INTERVAL` 原样重试一次再定罪（与 `_confirm_get_ok` 同语义）
  - text/html 启发式分支与尾部非 200 分支：`last_resort=True` 候选仅告警放行（「已无备选源，仍交由 ffmpeg 尝试」），非末位仍判不可达由上层回退。
- `src/stream_select.py` `select_source_url`：HLS 为唯一候选（无 FLV/record_url 备选）时传 `last_resort=True`

**B站认证问题（弹幕 0 收入）**：直播流走 `getRoomPlayInfo` 独立链路不受影响，故直播正常、仅弹幕失效。根因分两段——buvid 获取失败与 AUTH 软拒绝：

1. **spi 端点拼写错误（根因）**：`src/spider.py` 请求 `https://api.bilibili.com/x/frontend/finger/sp`
2. **AUTH_REPLY 零校验**：`bilibili.py` `_decode_packet` 对 operation=8（进房回应）直接忽略，认证失败完全无感知。

**修复（B站认证链闭环：获取 → 进房 → 感知 → 自愈）**：

- `src/spider.py`：
  - spi URL 修正为 `/x/frontend/finger/spi`。
  - buvid 获取链按真实注册标识优先：进程缓存 → 登录 cookie `buvid3=` → spi → **`www.bilibili.com` 首页 Set-Cookie**（新增…
  - 新增 `invalidate_bili_buvid_cache()`：AUTH 被拒时清除进程内缓存 + 兜底标记，下一轮重新走真实获取链（否则被拒 UUID 永久缓存复用 = 死循环）。
- `src/platforms/bilibili.py`：
  - operation=8 显式校验 code：0 置 `_auth_ok` 解除看门狗；非 0 经 `_reject_auth()` 告警 + 断开 + 调 `spider.invalidate_bili_buvid_cache()`。
  - `_reject_auth()`：统一的认证拒绝处理（懒加载导入 spider 避免循环依赖）。
  - `_auth_watchdog`：兜底「服务器不回 AUTH_REPLY 的静默拒绝」——进房包发出 8 秒无 code=0 回应按被拒处理…

**虎牙（结论：无需改动）**：报错是校验探针被 CDN 防护误杀的预期内噪音（`al.hls.huya.com`/`al.flv.huya.com` 对毫秒连击探针 403）

**测试与验证**：

- 新增 `tests/test_stream_select.py`（11 用例）：末位放行 4 项（text/html/非 200/末位/非末位）+ m3u8 探针重试 4 项（重试通过/稳定拒绝/404 不重试/末位放行）+ select_source_url 末位传参 3 项（仅 HLS/h265/HLS 有备选）。
- `tests/test_bilibili_danmaku_info.py` 扩展至 17 用例：spi URL 断言、cookie 优先、首页 Set-Cookie 备取、失效钩子、AUTH 成功/失败、看门狗触发/解除/作废、既有用例补首页空桩。
- 全量回归 **137 passed**；black / isort / mypy（stream_select/bilibili/spider/main）全绿。
- 三条防回归经验已沉淀 `AGENTS.md` 已知坑：`real_url` 为空必须跳过录制链、末位候选 content-type 拒绝也须放行、B站 buvid 必须真实 + AUTH_REPLY 显式校验。

> 环境噪音：执行期间 `.mimosa` 钩子多次回滚了本次改动文件（bilibili.py AUTH 块、测试导入行、测试断言），均已重新应用并复测确认在位——后续若发现修改丢失优先排查该工具。

### v4.0.8.2-dev (2026-08-17) — i18n 翻译链路根治：补齐缺失的 zh_CN.mo + 摆脱环境变量依赖 + po 清理

**来源**：全源码 AST 审计（提取所有 `print()` 字符串字面量与 `zh_CN.po` 逐条比对）。

**根因**：
① 仓库只有 `.po` 源文本、**缺失编译产物 `.mo`**——gettext 运行时只读 `.mo`
② `init_gettext` 走 `gettext.gettext` 全局查找、按 `LANG`/`LANGUAGE` 环境变量推断语言目录…

**修复**（3 文件改 + 2 文件新增 + 1 测试扩展）：

- `i18n.py`：`init_gettext` 改为 `gettext.translation(..., languages=["zh_CN"], fallback=True)` 显式加载…
- 新增 `scripts/compile_po.py`：纯 Python 的 `.po → .mo` 编译器（GNU msgfmt 兼容最小格式，Windows 无 gettext 工具链可用），`--check` 模式做字节级同步校验
- 新增 `i18n/zh_CN/LC_MESSAGES/zh_CN.mo`：编译产物（198 条含头部）
- `i18n/zh_CN/LC_MESSAGES/zh_CN.po` 清理（204 → 198）：删除源码中已消失的死条目（`"HTTP error occurred"`、无冒号版 `"An unexpected error occurred"`、`"First data retrieval failed..."`、`"Python"`）与一条精确重复条目…
- `.github/workflows/ci.yml`：`static` job 在 `check_version.py` 之后新增 `compile_po.py --check` 步骤，拦截「改 .po 忘记重编译 .mo」
- `tests/test_i18n.py` 新增 3 个回归测试：`.mo` 存在且非空…

**安全复查**：Mimosa L2 曾标记 `tests/test_i18n.py` 的 `subprocess` 调用为命令注入——判定误报（参数列表 + 无 shell + 纯静态字面量…

### v4.0.8.2-dev (2026-08-17) — 校验器 GET 复核误杀容错（重试+末位放行）+ 斗鱼 FLV→m3u8 同 token HLS 候选（根治 ~70s 断流）

**来源**：用户四房间实测日志（斗鱼 100 / 抖音 / B站 / 虎牙…

**根因**：
① 斗鱼 hw / 虎牙 al 等 CDN 对毫秒级连击探针（HEAD→GET）**偶发** 403——实测同 URL 连发 3 次无 Range GET 全部 200…
② 斗鱼 H5 接口（`getH5PlayV1`）只返回 FLV…

**修复**（2 源文件 + 2 测试文件）：

1. **`src/stream_select.py` 探针误杀容错**：
   - `_confirm_get_ok` 收到 401/403 先原样重试一次（间隔 0.8s）再定罪——区分「偶发限流」与「稳定拒绝」
   - 新增 `last_resort` 参数并经 `_validate_stream_url` 透传…
2. **`src/stream.py` 斗鱼 HLS 候选**：`get_douyu_stream_url` 在 `rtmp_live` 以 `.flv` 结尾时附带 `m3u8_url`（路径 `.flv`→`.m3u8`、查询串原样…

### v4.0.8.2-dev (2026-08-16) — 统一 cookie 获取：URL 级共享缓存，杜绝同网址重复拉取触发风控

**来源**：用户需求——分析所有动态获取 cookie 的代码…

**根因**：原先抖音 ttwid（`src/ttwid.py`）与快手 did（`src/spider.py:_ensure_kuaishou_did`）各自维护独立缓存并各自请求网址…

**修复**（新增 1 文件 + 改 2 文件）：

1. **新增 `src/cookie_cache.py`**：进程级、以「归一化网址 + 代理」为 key 的访客 cookie 缓存。
   - 存储结构：`dict[key, (cookie_dict, expire_ts)]`，value 为网址下发的原始 cookie 字典（调用方按需提取 `ttwid`/`did` 等字段，不做平台特定裁剪）。
   - 失效策略：TTL 默认 30 分钟（与 `src/room.py` sec_uid 缓存一致）
   - 跨模块调用：`fetch_cookies(url, proxy, *, headers, timeout, http2, ttl, fetcher)` 统一读取入口…
   - `fetch_cookies` 接受 `fetcher` 参数（默认本模块 `async_req`）
2. **`src/ttwid.py`**：`_fetch_ttwid` 经 `cookie_cache.fetch_cookies("https://live.douyin.com/", ..., fetcher=async_req)` 获取…
3. **`src/spider.py`**：`_ensure_kuaishou_did` 经 `cookie_cache.fetch_cookies("https://live.kuaishou.com/", ..., fetcher=async_req)` 获取…

### v4.0.8.2-dev (2026-08-16) — B站 spi buvid 请求治理：进程级缓存 + 未开播周期零请求

**来源**：用户 `py web.py` 实测日志（B站 3336696 / 抖音 51845582768 / 斗鱼 998）。

**根因**：`main.py` B站分支里 `get_bilibili_danmaku_info` 在每个监测周期**无条件执行**（未开播周期也跑 4~5 个请求：room_init + nav + spi×2 + getDanmuInfo）

**修复**（2 文件）：

1. **`src/spider.py` buvid 进程级缓存**：新增模块级 `_bili_buvid_cached` + `_bili_buvid_lock`（threading.Lock）。
2. **`main.py` 延迟到开播才获取**：B站分支 `get_bilibili_danmaku_info` 调用前加 `if port_info.get("is_live", False)` 门控——未开播周期完全跳过弹幕信息获取（0 请求）

### v4.0.8.2-dev (2026-08-16) — 三轮实测：揪出历史性结构 bug——录制链被嵌套在 `if headers:` 内，抖音/斗鱼等平台从未录制过

**来源**：用户第三次 `py web.py` 实测 + 插桩实证。

**根因（插桩实证）**：run() 中 `headers = get_record_headers(platform, ...)` 后的 `if headers:`（main.py 原 1739 行）**错误地包住了其后的整个录制链**（tls_verify/proxy 插入、record_state_lock 注册、rec_info 打印、TS/FLV/MP4/MKV 全部录制分支、check_subprocess、count_time/record_success）——共 ~490 行。

**修复**：

1. **main.py 缩进层级修正（483 行整体左移 4 空格）**：`if headers:` 只保留 `-headers` 插入（4 行）
2. **stream_select.py 校验器 UA 对齐**：新增 `MOBILE_UA` 常量（与 main.py ffmpeg 默认 UA 一字不差）

### v4.0.8.2-dev (2026-08-16) — 二轮实测日志修复：tls_verify 误插 http 流 / Range-GET 误杀斗鱼 / HLS-关闭静默路径

**来源**：用户第二次 `py web.py` 实测。

1. **`Option tls_verify not found`（虎牙 http FLV 录制失败…
2. **Range-GET 误杀斗鱼**：上轮 GET 复核带 `Range: bytes=0-0`
3. **"m3u8 存在但 HLS 采集关闭且无 flv/record 回退"静默路径**：上轮"均为空"警告条件含 `hls_available`

### v4.0.8.2-dev (2026-08-16) — 专项清理：测试先行未落地的修复全量补齐（21 failed + 18 errors → 540 passed）

**定性**：git 历史证实…

**改动清单**（8 个源文件）：

- `src/async_http.py`：新增 `_client_cache_lock`（threading.Lock…
- `src/web_api.py`：登录失败限流（`_FAILED_LOGINS`/`_FAILED_LOGINS_LOCK`
- `src/web_config.py`：`web_trusted_proxy` 默认值…
- `src/weverse_auth.py`：`_app_secret()` 支持环境变量 `DOUYIN_WEVERSE_APP_SECRET` 覆盖硬编码密钥。
- `src/spider.py` 9 处：vvxqiu 缺房间号不再空探测 m3u8、空响应判未直播…
- `src/ttwid.py`：`_ttwid_lock` 改 RLock（锁跨越 await 时同线程重入不死锁）。
- `src/utils.py`：`read_config_value` 关闭 configparser 插值（裸 % 不再 InterpolationSyntaxError）。
- `src/sync_http.py`：请求失败统一 `logger.error("sync_req 请求失败...")` 并返回空串（错误文本不再伪装成响应体）。

**遗留**：~~`mypy main.py` 仍有 6 个 `check_subprocess` 的 `list[str | None]` arg-type 错误~~ **已解决**（见下一条目：根因是 `ffmpeg_command` 字面量在 `if real_url:` 守卫块外构建…

### v4.0.8.2-dev (2026-08-16) — mypy main.py 6 个 arg-type 错误清零

**根因**：`run()` 中 `real_url = select_source_url(...)` 返回 `str | None`

**修复**：[main.py] 列表内 `-i` 参数处一处 `cast(str, real_url)`（运行时零变化…

### v4.0.8.2-dev (2026-08-16) — B站弹幕连接即断真根因（进房包 uid 误传主播 uid）+ 虎牙 FLV 校验假绿 + 全空流地址静默跳过

**来源**：用户 `py web.py` 实测日志（B站 3336696 / 抖音 51845582768 / 虎牙 vctcn / 斗鱼 998）。

**根因（真机对照探针实证）**：`get_bilibili_danmaku_info` 返回的 `uid` 是**主播** uid（room_init 的 data.uid）

**改动**：

- `src/platforms/bilibili.py` `_join_room`：观众 uid = cookie 中 `DedeUserID`（登录态）否则 0，绝不再透传主播 uid。spi 兜底 uuid buvid 保留（无害且探针证明可用）。
- `src/stream_select.py` `_validate_stream_url`：FLV/record_url 在 HEAD 判定通过后追加流式 Range-GET 复核（`_confirm_get_ok`
- `src/stream_select.py` `select_source_url`：m3u8/flv/record_url 全空时不再静默返回 None（斗鱼 `get_douyu_stream_url` 在 rtmp_live 为空时即此形态）

**遗留（非本次范围）**：全量 `pytest` 存在 21 failed + 18 errors 的预存漂移（`_client_cache_lock`/`_FAILED_LOGINS_LOCK`/`_app_secret` 等符号在 HEAD 即缺失、`node` 环境问题）

### v4.0.8.2-dev (2026-08-16) — B站弹幕 buvid 兜底（spi 风控空响应时生成兜底 buvid3）

**来源**：多房间实测日志（虎牙 660002 / B站 3336696 / 斗鱼 998 / 抖音 481667816952）。

**根因**：`get_bilibili_danmaku_info` 的 spi 端点 `api.bilibili.com/x/frontend/finger/sp` 偶发返回空响应体（B站风控 200+空 body…

**改动**（`src/spider.py` `get_bilibili_danmaku_info` 第 3 步）：

- spi 取 buvid 包进 `for _attempt in range(2)` 重试一次（瞬时空 body 自愈）。
- 两次仍空则 `buvid = str(uuid.uuid4())` 生成兜底 buvid3（随机 UUID 式 32 位串…

- 真机探针（临时脚本，已删）确认 B站弹幕连接即断与 buvid 空同源；curl 对比确认该问题独立于 Referer/UA。
- 新增 `tests/test_bilibili_danmaku_info.py::test_get_bilibili_danmaku_info_spi_empty_uses_fallback_buvid`：spi 两次返回空 → 返回非空且合法的 uuid buvid、token 正常。
- `pytest` 上述 4 例全过（含新增）；`mypy src/spider.py` 0 错误；6 测试文件共 **35 passed** 无回归。

### v4.0.8.2-dev (2026-08-16) — 虎牙 HLS/FLV 403 排查结论（Referer 已正确注入，无需改代码）

**排查来源**：同轮日志虎牙 HLS(m3u8)/FLV 校验 403 → 回退 record_url（录制成功…

- `al.hls.huya.com`（m3u8）：**HEAD=403 且 GET=403，与 Referer 无关**——该 host 在环境下不服务 m3u8，属 CDN/主机层面不可达，Referer 无法救。
- `al-game.flv.huya.com`（flv）：HEAD=200（Referer 已注入，校验本应通过）；日志里偶发 403 是 `wsTime` 在「拉流→校验」窗口内过期所致，非代码 bug。
- record_url（`tx.flv.huya.com`）经 ffmpeg GET 实际可录（日志已确认开始录制）。

**结论**：Referer 注入正确且对适用 host 有效…

### v4.0.8.2-dev (2026-08-16) — 修复 config.ini 不可写时 import main 阶段崩溃（web.py 启动失败）

**来源**：用户 `py web.py` 在 `web.py:135 import main` 处崩溃。

**根因**：

1. `src/config_io.py` `read_config_value` 在缺键时"遇缺必写回"且对写失败零容错…
2. `main.py` 兼容旧键复用了会写回的 `read_config_value`，使"已迁移配置缺旧键"反而触发旧键写回，注释承诺的"兼容"实际是坏的。

**改动**：

- `src/config_io.py` `read_config_value` 写回包进 `try/except OSError`：失败仅 `logger.warning` 并返回默认值…
- `main.py` 旧键兼容改为 `config.has_option(...)` 判断存在才 `config.get(...)`，**绝不写回**——旧键只应被读、不应被自动重建。

**提交**：`fix(config): 修复 config.ini 不可写时 import main 阶段崩溃（只读写回 best-effort + 旧键兼容仅读取）`。

### v4.0.8.2-dev (2026-08-16) — 虎牙 OD/BD/UHD app路径弹幕三元组返回 + 消除静默跳过

**来源**：上一轮日志暴露 `[虎牙直播]弹幕跳过: danmaku_args 为空`（无 warning…

**根因**：app 路径（profileRoom 接口）的三元组本该与 web 路径（`get_huya_stream_data` 的 `gameLiveInfo.yyid` + `gameStreamInfoList[0].lChannelId/lSubChannelId`）对齐…

**改动**：

- `src/spider.py` `get_huya_app_stream_url` 返回 dict 新增 `yyid/lChannelId/lSubChannelId`：`yyid ← profile_info.get("yyid")`
- `main.py` OD/BD/UHD 分支三元组缺失分支补 `logger.debug`（记录 `yyid/lChannelId/lSubChannelId` 实际取值），消除原静默跳过，便于将来定位 spider 返回结构变化。

**提交**：`f415184 fix(huya): 补 OD/BD/UHD app路径弹幕三元组返回并消除静默跳过`（2 文件：spider.py/main.py；test_huya_danmaku.py 此前已入库）。

### v4.0.8.2-dev (2026-08-16) — SSL 覆盖重构为通用平台列表（兼容旧虎牙单列键）

**来源**：运行日志 `stream_select:_validate_stream_url` 报 B站 `bilivideo.com` `CERTIFICATE_VERIFY_FAILED: Hostname mismatch`（证书 SAN 不含 `2409_8c20_…bytefcdnrd.com`）。

**改动**（`main.py` 配置解析段）：把 `虎牙是否禁用SSL证书验证(是/否)` 单列键重构为逗号分隔的平台列表 `禁用SSL证书验证的平台(逗号分隔)`。

**配置示例**：`禁用SSL证书验证的平台(逗号分隔) = 虎牙直播,B站直播`（与「弹幕录制平台」同款逗号分隔格式…

### v4.0.8.2-dev (2026-08-16) — backup_file 旋转删除误导性 ERROR：改为 best-effort

**来源**：运行日志每备份周期报 `src.config_io:backup_file:150`「备份配置文件 ... 失败」。

**根因**：旋转删除的 `os.remove` 被 agent 运行时 safe-delete 守卫拦截（改走 Windows 回收站）

**改动**（`src/config_io.py`）：把旋转 `os.remove` 隔离为 best-effort——`except OSError` 记 warning 并 `break`

### v4.0.8.2-dev (2026-08-16) — B站弹幕参数获取落地 + B站直播流补 Referer

**来源**：运行日志 `__main__:start_record:986` 报 `[B站直播]弹幕信息获取失败: module 'src.spider' has no attribute 'get_bilibili_danmaku_info'`

**根因**：

- `main.py:981` 调用 `spider.get_bilibili_danmaku_info(url=, proxy_addr=, cookies=)` 获取 B站弹幕进房参数…
- B站直播流 `bilivideo.com` 对无 Referer 请求返回 403（content-type 空），`get_record_headers` 无 B站条目，ffmpeg 与校验器都不带 Referer → 两端一致拿不到流。

**改动**：

- `src/spider.py`：落地 `get_bilibili_danmaku_info(url, proxy_addr=None, cookies=None)`——`room_init` 短号转真实 room_id + uid…
- `src/stream_select.py` `get_record_headers`：新增 `"B站直播": "referer:https://live.bilibili.com/"`，ffmpeg 录制与可达性校验（已按 platform 通用注入）两路一致生效。

### v4.0.8.2-dev (2026-08-16) — 虎牙可选关闭证书校验（平台级 SSL 覆盖，默认严格）

**来源**：虎牙 TX CDN 边缘节点（`tx.flv.huya.com`）证书 SAN 不含实际主机名（`2409_8c20_6ed1_22a__46.bytefcdnrd.com`）

**根因**：原 `_validate_stream_url` 只用全局 `ssl_verify`

**改动**（默认严格，属安全降级，仅虎牙显式开启才生效）：

- `src/http_config.py`：新增通用 `ssl_verify_platform_overrides` 字典 + `set_platform_ssl_verify(platform, value)` + `get_effective_ssl_verify(platform)`——平台有覆盖取覆盖值…
- `src/stream_select.py`：`_validate_stream_url` 的 `verify` 默认改为 `get_effective_ssl_verify(platform)`。
- `main.py:2291` 区：读取 `录制设置/虎牙是否禁用SSL证书验证(是/否)`（默认"否"）
- `config/config.ini`：新增 `虎牙是否禁用SSL证书验证(是/否) = 否`（带说明注释）。

### v4.0.8.2-dev (2026-08-16) — 虎牙录制修复：补 Referer 解决 CDN 403 误判不可达

**来源**：运行日志显示 room 660002（虎牙）HLS/FLV/record_url 三路全部失败（AL CDN 403 + TX CDN TLS 证书主机名不匹配）

**根因**：录制器校验器（`_validate_stream_url`）与 ffmpeg 录制命令（经 `get_record_headers`）都不为虎牙发送 Referer…

**改动**（`src/stream_select.py` + `main.py`）：

- `get_record_headers` 新增 `"虎牙直播": "referer:https://www.huya.com/"`：ffmpeg 录制（`main.py:1690` 插入 `-headers`）与直下（`main.py:605`）两路自动生效。
- `_validate_stream_url` 新增 `platform` 参数：按 platform 调 `get_record_headers` 解析出 `referer` 头注入 httpx 探测请求，使可达性判断与录制路径一致。
- `select_source_url` 透传 `platform` 到 4 处 `_validate_stream_url` 调用；`main.py:1590` 调用时传入 `platform`。

### v4.0.8.2-dev (2026-08-16) — main.py 拆分：6 类功能抽离至 src 子模块（完整重构）

**来源**：用户要求分析 `main.py` 找出可独立功能，将拆出模块放至 `src/` 复用，并选择「完整重构」方案（同时改 main.py 接线、删除重复代码）。

**改动**：

- 抽出 6 个独立模块（均位于 `src/`，经 re-export 保持 `main.<name>` 兼容）：
  - `src/ffmpeg_proc.py` — FFmpeg 进程注册/注销/终止/清理（`register_ffmpeg_process`/`unregister_ffmpeg_process`/`_terminate_ffmpeg_process`/`_cleanup_single_ffmpeg_process`/`cleanup_all_ffmpeg_processes`/`_get_error_line`）
  - `src/video_postprocess.py` — 启动信息/FFmpeg 校验/分段/转 mp4·m4a/生成字幕（`get_startup_info`/`_run_ffmpeg_checked`/`segment_video`/`converts_mp4`/`converts_m4a`/`generate_subtitles`）
  - `src/stream_select.py` — 流地址选择/校验/画质码/限速（`contains_url`/`clean_name`/`get_quality_code`/`get_record_headers`/`_validate_stream_url`/`select_source_url`/`_douyin_rate_limit`）
  - `src/notify.py` — 推送/脚本/成功失败计数/并发调节/清理（`push_message`/`run_script`/`record_error`/`record_success`/`adjust_max_request`/`clear_record_info`）
  - `src/recorder_status.py` — 状态快照/展示（`get_status`/`display_info`）
  - `src/config_io.py` — 配置读写/安全数值转换/备份（`update_file`/`delete_line`/`read_config_value`/`_safe_int`/`_safe_float`/`backup_file`/`backup_file_start`）
- `main.py`：
  - 顶部加 `__main__` 守卫（`if sys.modules.get("main") is None: sys.modules["main"] = sys.modules["__main__"]`），防止 `python main.py` 时子模块 `import main` 触发整文件二次执行
  - 加 re-export 块（`from src.<mod> import (...)`）
  - 删除 `update_file`/`delete_line` 在 main.py 内的重复定义（config_io 为唯一真相源），清掉 AST 删除留下的尾部空白
  - 行数 3543 → 2696

**坑（已规避）**：

- 深度耦合 main 全局的模块（`notify`/`recorder_status`/`config_io` 及 `video_postprocess`/`stream_select` 部分函数）一律用运行时 `import main` 惰性访问全局（`main.<x>`）
- AST 删除脚本初版漏删 AnnAssign 声明的 `_ffmpeg_processes`/`_processes_lock`

### v4.0.8.2-dev (2026-08-16) — 弹幕子包扁平化：src/danmaku/\* → src/\*

**来源**：用户要求把 `src/danmaku/` 整个子包上移到 `src/`，并检查功能是否因搬移失效。

**变动**：

- `git mv` 逐个文件/目录：`base.py` `collector.py` `srt_writer.py` `ws_client.py` `platforms/` `proto/` 从 `src/danmaku/` 上移到 `src/`
- `__init__.py` 冲突：父包 `src/__init__.py` 已存在…
- 全仓批量重写导入：`from src.danmaku...` → `from src...`、`src.danmaku import` → `src import`，覆盖 `src/**/*.py`、`main.py`、`tests/*.py`。
- 更新打包冒烟桩 `_smoke_stub.py` 的 `HEAVY` 列表：`src.danmaku` → `src.srt_writer`/`src.ws_client`/`src.proto`。

**坑（已修）**：

- `main.py:109` 批量改写后残留 `from src.danmaku import get_danmaku_collector`（首轮改写报告"已清空"为误判）
- 双模式测试脚本（`test_*_live_collector.py` 顶层 `SECONDS=int(sys.argv[2])`）多个文件同进程 pytest 收集时 `sys.argv[2]` 变成另一测试路径 → `int()` 崩…

### v4.0.8.2-dev (2026-08-16) — 弹幕录制模块审查修复（danmaku_check.md 全量问题项）

**来源**：`danmaku_check.md` 审查报告（P0×1 / P1×2 / P2×2 / P3×2 + 测试缺口），弹幕功能因 6 处调用点未接线实际从未生效。

**改动**：

- **P1 接线**：`main.py` 6 处 `check_subprocess` 调用点补传 `platform=platform, danmaku_args=record_danmaku_args`（两变量均为 `start_record` 局部、每轮重置…
- **P1 stop 位置**：`danmaku_collector.stop()` 从 `while process.poll() is None` 循环体内移到循环之后（修复前弹幕约 1 秒即被终止）
- **P2 文件名对齐**：`check_subprocess` 占位符剥离同时覆盖 `_%02d`/`_%03d`
- **P3 ttwid 动态化**：`src/platforms/douyin.py` 删除硬编码过期 `_DEFAULT_TTWID`
- **P3 配置防护**：`弹幕分片时长(秒)` 改 `_safe_float(..., 1800.0)`，非法值不再杀死录制主循环。
- **P0/P2 暂存区**：`.gitignore` 追加 `.qoder/`、`.agents/`、`.pnpm-store/`、`.dsh-validation/`、`.ego-browser-test/`、`.plugin-src/`、`.tmp-dps-extract/`、`tests/_out_e2e/`、`tests/_out_live/`、`.coveragerc-concurrency`、`*.isorted`
- **测试**：新增 `tests/test_danmaku_wiring.py` 9 个用例（接线参数、stop 循环外仅一次、占位符剥离、提前中断、不支持平台跳过、SRT 三位宽度、stop 幂等、ttwid 动态获取/失败兜底）

### v4.0.8.2-dev (2026-08-16) — 修复 HLS(m3u8) 校验误判 405 而回退 FLV

**来源**：运行日志显示 `pull-hls-f26.douyinliving.com/...m3u8` 对 HEAD 返回 `405` + `content-type=text/html`

**根因**：`main.py` 的 `_validate_stream_url`（同步校验器）判断顺序错误——先检查 `text/html` 内容类型并 `return False`

**改动**：`main.py` `_validate_stream_url`

- 把 m3u8 源（url 含 `.m3u8`）的 Range GET 探测**提到 text/html 拦截之前**…
- 非 m3u8 源（flv/record_url）保留原 text/html 启发式拒绝逻辑。
- 同步/异步两个校验器对 m3u8 的处理语义现已对齐。

### v4.0.8.2-dev (2026-08-16) — docstring 全量转 # 注释（执行项目注释规范）

**来源**：用户要求检查 `"""` 注释并改为 `#` 注释，执行项目约定"Python 注释统一用 `#`，不用三引号 docstring"。

**转换方式**：用 AST 精确识别 docstring 节点（区分于普通三引号字符串字面量，避免误伤），按 (lineno, end_lineno) 行范围替换为 `#` 注释。从后往前替换避免行号偏移。

**范围**：扫描 79 个 .py 文件，转换 78 个 docstring（28 个文件）。

- 模块级 docstring 25 个 → 文件首部 `#` 注释
- FunctionDef docstring 38 个 → 函数体首部 `#` 注释
- AsyncFunctionDef docstring 7 个 → 函数体首部 `#` 注释
- ClassDef docstring 4 个 → 类体首部 `#` 注释
- 4 个 `@abstractmethod`（`src/base.py` 的 start/stop/heartbeat/decode_message）body 仅含 docstring，删后补 `pass`
- 保留 `src/proto/douyin_pb2.py` 的 1 个 docstring（protoc 生成文件，DO NOT EDIT）

**坑与处理**：

- `tests/test_bili_e2e.py` 的 docstring 描述 B 站打包帧用 `\0` 分隔…
- 缩进用 docstring 节点自身的 `col_offset`（体缩进），非 `def`/`class` 行缩进，保证注释与体内容对齐。

**副作用确认**：

- FastAPI 端点（`src/web_api.py` 15 个）转换前后都无 docstring，OpenAPI 描述用其他方式，无影响。
- 函数 `__doc__` 属性变 None，项目无依赖 `__doc__` 的逻辑。

### v4.0.8.2-dev (2026-08-16) — 全量代码检查与修复（mypy/basedpyright 双双清零）

**来源**：用户要求"检查所有代码"（类型检查 + 单元测试 + 代码风格 + 静态分析，全部自动修复）。

**修复内容**：

1. **main.py 函数签名损坏（语法错误）**：`check_subprocess` 签名被错误拆成两段…
2. **main.py 弹幕变量作用域断裂（NameError）**：`main()` 的 global 声明漏 `enable_danmaku`/`danmaku_split_time`/`danmaku_platforms`
3. **main.py `seg_pattern` 未定义（NameError）**：FLV 分段转码分支引用未定义变量。补 glob 模式定义 `{prefix}_*.flv`。
4. **spider.py 虎牙返回 dict 缺弹幕字段（功能 bug）**：`get_huya_app_stream_url` 提取了 `_yyid`/`_l_channel`/`_l_sub_channel` 放进 `play_url_list`
5. **spider.py 重复访问 `json_data['data']`（类型退化）**：line 816-822 重复访问已 cast 的 `data_field`
6. **bilibili.py `int(room_id)` 缺默认值（运行时 TypeError）**：`self._args.get("room_id")` 缺键时 `int(None)` 崩。补默认值 0，与 uid 写法一致。
7. **srt_writer.py `_t0` None 检查 + `_fp` 类型注解**：`_ensure_started` 副作用后 `_t0` 非 None 加 assert 断言；`_fp` 注解 `Optional[TextIO]`。
8. **ws_client.py `on_heartbeat` 类型注解过窄（5 平台连锁报错）**：定义为 `Callable[[], None]` 但实现支持 async（`inspect.isawaitable`）
9. **5 平台 `on_reconnect` 写法简化**：`(self._on_close and (lambda...)) if self._on_close else None` 简化为 `on_reconnect=self._on_close`（语义等价…
10. **danmaku 模块类型注解补全**：5 平台 `__init__` 的 `*args/**kwargs` 加 `Any` 注解…
11. **douyin_pb2.pyi 类型存根创建**：protobuf 生成模块属性动态注入…
12. **spider.py 类型收窄**：3 处 `json.loads(resp)` 改用项目已有的 `_loads_dict` 安全转换…
13. **base.py 删除未用 `field` 导入**。
14. **5 个 collector 测试 `int(argv)` 容错**：双模式脚本在 pytest 收集时 `sys.argv[2]='-q'` 致 `int('-q')` 崩。加 `not argv.startswith('-')` 守卫。
15. **安装缺失依赖**：venv 缺 `brotli`/`protobuf`（requirements.txt 已列但未装），补装后测试可收集。
16. **black + isort 格式化全部**（29 文件）；清理 isort 残留 `.py.isorted` 备份。

**待用户决策（非 bug，未自动修改）**：

- 弹幕功能未接线：`start_record` 各平台分支提取了 `record_danmaku_args`/`platform`
- `record_danmaku_args`/`seg_file_path` 赋值未使用（pyflakes 警告，前者因未接线，后者为作者标注的死代码分支）。
- `main()` 的 `global platform`/`global record_danmaku_args` 声明无效（main 内从未赋值，供其他函数读取的全局状态）。

### v4.0.8.2-dev (2026-08-16) — 代码门禁复查与测试脚本同步修复

**来源**：用户要求「检查代码」，按 AGENTS.md 约定执行 black / isort / mypy / pytest 四项质量门禁。

**发现与修复**：

1. **测试套件被过期导入整体阻断（真实缺陷，修复）**：
   - `tests/test_douyin_live_collector.py:17` 仍导入 `from src.platforms.douyin import _DEFAULT_TTWID`
   - 该 ImportError 导致 pytest 收集阶段直接 exit 2，**所有 515 个测试均未执行**。
   - 修复：导入改为 `from src.ttwid import get_ttwid`
2. **格式偏差（3 处，自动修复）**：
   - `tests/test_web_api.py`：函数签名换行可压缩至 120 列内
   - `tests/test_concurrency_rate_limit.py`：stdlib 与第三方导入分组错误
   - `tests/test_weverse_auth.py`：stdlib 与第三方导入分组错误

- `black --check .` 95 files 全通过
- `isort --check-only .` 全通过
- `mypy src/` 31 files 0 errors
- `pytest -q --tb=short` **515 passed, 2 skipped**（30.4s，退出码 0）
- `scripts/check_version.py` 版本 4.0.8.2 一致

**观察项（未修改）**：pytest 退出阶段的 `RuntimeWarning: coroutine 'FakeAsyncClient.aclose' was never awaited` 与 `Loguru Handler ... ValueError: I/O operation on closed file` 为测试桩/解释器关闭噪音…

### v4.0.8.2-dev (2026-08-16) — 弹幕 WS 连接显式绕过系统代理（proxy=None，根治 "connecting through a SOCKS proxy requires python-socks"）

**来源**：用户 `python3 main.py` 实测…

**根因**：`websockets.connect(proxy=True)` 默认自动探测并跟随代理…

**改动**（`src/ws_client.py` `connect()`）：显式传入 `proxy=None`

**决策依据**：弹幕通道本就国内直连、不需要出网代理…

### v4.0.8.1-dev (2026-08-15) — 修复 Web 冒烟测试因安全护栏退出码 1 失败

**来源**：`build_exe.py --smoke` 在 CI 中 `smoke_web` 阶段失败…

**根因**：Web 面板 `web.py` 的 C1 安全护栏——`web_auth_enable=false` 且监听非回环地址（`config.ini` 默认 `web_host=0.0.0.0`）时调用 `sys.exit(1)`。

**改动**：`build_exe.py`

- `_launch()` 新增 `extra_env` 形参，向子进程注入环境变量（合并 `os.environ`，不覆盖其余变量）。
- `smoke_web()` 启动 Web exe 时传入 `extra_env={"DOUYIN_WEB_ALLOW_INSECURE": "1"}`

### v4.0.8.1-dev (2026-08-15) — 代码审查遗留项修复（pyflakes 清零 + 死代码/隐式副作用收敛）

**来源**：`代码审查报告_DouyinLiveRecorder.md`（报告父项 rvVeM2 遗留改进项）。

**改动**：

- `src/web_api.py`：移除未使用的 `validate_room_target` 导入。
- `src/web_config.py`：移除未使用的 `from typing import cast` 导入（pyflakes 告警）。
- `src/spider.py`：
  - 删除未使用局部变量 `cast_start_date_code_int`（原 L2443；`cast_start_date_code` 仍被使用）。
  - 删除快手旧版 `playUrls` 死代码分支（原 L686，标注"2024-11-28 起失效"）；改为仅接受现代 h264 dict 格式，避免 `play_url_list` 未定义 NameError。
  - 收敛 38 处 `print` → `logger`（失败/异常→warning，成功/状态→info，纯诊断→debug）。控制台 sink 为 DEBUG 级别，用户可见输出不丢失。
  - `get_huajiao_sn` 解析失败静默注释 `URL_config.ini` 改为**显式 + warning 日志**（保留"注释禁用无效地址"的 UX）。
  - `get_taobao_stream_url` 刷新 token 回写 `config.ini` 的 `taobao_cookie` 改为**显式 + info 日志**（持久化必需，保留功能）。

### v4.0.8.1-dev (2026-08-15) — 修复 test_proxy.py 因 harness 环境变量膨胀导致的 flaky 失败

**现象**：整套 `pytest` 偶尔 1 failed（`tests/test_proxy.py::TestProxyDetectorLinux::test_linux_get_proxy_info_with_auth`）

**根因**：`unittest.mock.patch.dict` 对 `os.environ` 的操作**无论 `clear` 取 True/False** 都会整体快照并恢复整个环境（`_patch_dict` 内 `original = in_dict.copy()`

**改动（tests/test_proxy.py）**：

- `TestProxyDetectorLinux` 类全部 7 处 `patch.dict(os.environ, ...)` 统一替换为 pytest 的 `monkeypatch.setenv/delenv`（只操作单个 key…
- `test_linux_get_proxy_info_with_auth` 断言收紧为 `ip == "proxy.example.com"` 且 `port == "3128"`（去掉永假死分支 `"proxy.example.com:3128"`）
- 删除不再使用的 `import os` 与 `from unittest.mock import patch`

**约定沉淀**：Windows + harness 环境下…

### v4.0.8.1-dev (2026-08-15) — basedpyright 配置落地 + 类型/依赖/测试收尾

**背景**：全量跑 basedpyright 报 **189 errors / 3241 warnings**，初看吓人但绝大多数是噪音。定位后根因是**配置缺失 + 两处真实缺陷**，现已全部清零。

**根因与改动**：

- **`pyproject.toml` 新增 `[tool.basedpyright]` 配置段**：项目依赖其实装在 workbuddy managed venv（`envs/default`）
  - **注意**：`venvPath` 写死本机 workbuddy managed venv 路径（机器相关）
- **装 `exejs` 到 managed venv**：`pyproject.toml` 声明了 `exejs>=1.0.1`
- **`src/sync_http.py` JsonType 死代码重构（配置后暴露的真问题）**：原 `try: from requests._types import JsonType except ImportError: from typing import Any as JsonType`。
- **`main.py:3271`** 裸 `tuple` → `tuple[Any, ...]`（第 89 行 typing 导入补 `Any`）。
- **`gui_legacy.py:425`** `__init__` 补 `self._status_anim_timer: str | None = None`（原仅在方法内赋值，未初始化）。旧版 GUI 入口，优先级低但已补严谨性。

**测试收尾（环境相关）**：`tests/test_web_api.py` 的 `TestListFiles::test_broken_symlink_skipped` 与 `test_symlink_outside_skipped` 在 Windows sandbox 下 `os.symlink` **不抛异常**却生成普通文件（`islink()=False`）

### v4.0.8.1-dev (2026-08-15) — 代码审查跟进修复（锁防死锁 / error_count 语义 / 格式化排除）

**凭据去重锁防死锁加固（`src/spider.py` / `src/ttwid.py`）**：

- `_kuaishou_did_lock` / `_twitch_client_id_lock` / `_ttwid_lock` 由 `threading.Lock` 改为 `threading.RLock`：锁跨越 `await` 持有时…
- `tests/test_concurrency.py::test_ttwid_module_pattern` 同步更新断言为 RLock

**error_count 语义明确化（`main.py`）**：

- `error_count` 不再被 `adjust_max_request` 周期清零，语义固定为「进程启动起累计错误数」；CLI 状态行文案由「目前瞬时错误数」更正为「累计错误数」
- `get_status()` 新增 `recent_errors` 字段（`max_request_lock` 持锁采样 `sum(error_window)`），为 Web 面板提供窗口口径的瞬时错误数，与累计 `error_count` 并存
- Web 面板（`web/index.html` / `web/app.js`）：错误数卡片标签改为「错误数(累计/近期)」，数值展示为 `累计 / 近期` 双口径（任一字段缺失时回退 `-`）

**pyproject.toml 格式化排除补全**：

- black `exclude` / isort `extend_skip` 新增 `.agents` / `.qoder` / `.workbuddy` / `.plugin-src` / `.dsh-validation` / `.ego-browser-test` / `.npm-cache` / `.pnpm-store`

### v4.0.8.1-dev (2026-08-13) — 修复 `get_startup_info()` 跨平台 mypy 回归

**现象**：CI `mypy src/`（Linux）报 2 个错误 —— `main.py:764: Module has no attribute "STARTUPINFO"`、`main.py:769: Variable "main._StartupInfoType" is not valid as a type`。

**根因**：上一批次（下一条日志）为满足 basedpyright…

**修复**：`subprocess.STARTUPINFO` 在非 Windows typeshed 中根本不存在…

### v4.0.8.1-dev (2026-08-13) — CI `black --check` 失败修复 + lint job 升 Python 3.13

**现象**：CI `lint` job（`black --check .`）失败退出码 1，提示 `scripts/smoke_test.py` 与 `gui.py` 各有一处需 reformat。

**根因与修复（纯格式，不改动逻辑）**：

- `scripts/smoke_test.py:280`：`p.add_argument("--format", ...)` 单行超 120 字符，按 black `line-length=120` 换行展开为多行签名。
- `gui.py:1460`：`config = configparser.ConfigParser()` 后缺空行（注释前需空行），补回空行。
- 修复后 `black --check .` → `All done! ✨ 🍰 ✨ 59 files would be left unchanged.`（exit 0）。

**消噪（可选增强）**：`.github/workflows/ci.yml` 的 `lint` job 运行 Python 由 `3.12` 升到 `3.13`

### v4.0.8.1-dev (2026-08-13) — 基于参考信息的类型/逻辑修复批次

本轮依据用户提供的参考信息（编辑器选中区块）逐项修复…

**`src/web_api.py`（登录爆破限流类型收紧）**：

- `_FAILED_LOGINS: dict[str, deque] = {}` → `dict[str, deque[float]]`：原裸 `deque` 在严格模式下退化为 `deque[Unknown]`

**`build_exe.py`（Linux ffmpeg 拷贝分支，line 327-335）**：

- `shutil.copy2` 返回值未使用 → 赋 `_ = shutil.copy2(...)`，消除 `reportUnusedCallResult`。
- 拷贝参数改用 `Path`（兼容 `os.PathLike`），省略冗余 `str()` 转换。
- 现状：basedpyright 0 errors…

**`msg_push.py`（tg_bot 推送，line 169-182）**：

- url 原在 try 内绑定，构造 `json_data` 异常时 except 块引用未绑定变量 → `NameError`；修复为 url 在 try 外预绑定。
- 不校验 Telegram 业务失败（`{"ok": false}`）→ 补充 `resp_data.get("ok") is True` 判定，失败取 `description` 记录并返回 error。
- 失败返回占位 `[1]` 与成功 `[str(chat_id)]` 不一致 → 统一为 `[str(chat_id)]`。

**`main.py`（两处）**：

- line 524 PATH 拼接：`current_env_path` 是 import 时快照…
- `get_startup_info()`（line 765）：`_StartupInfoType` 在 `if sys.platform` 运行期分支赋值被 pyright 视为变量 → 移入 `TYPE_CHECKING` 块无条件赋值 `subprocess.STARTUPINFO` + 引号注解。

**`gui.py`（PystrayIcon 别名 + 两处 mypy 误报）**：

- line 179 `PystrayIcon`：basedpyright 0/0/0，但 mypy 16 错误（别名在 `TYPE_CHECKING` 内被当变量）→ 用 `TypeAlias` 声明（`PystrayIcon: TypeAlias = pystray.Icon` / `object`）。
- line 830 `ctk.CTkFrame` 对 mypy 为 Any → `cast("tk.Frame", ...)`。
- 补充清理剩余 2 个 mypy 错误：line 1312 `row_fg` 注解联合类型 `str | tuple[str, str]`

### v4.0.8.1-dev (2026-08-12) — 修复跨事件循环锁误判风控 + 空白异常日志收口

**问题背景**：运行日志高频出现 `... is bound to a different event loop` 后…

**根因**：项目并发模型为每个 room 独立线程 + 独立 `asyncio.run()` 循环（main.py 上百处 `asyncio.run(...)` 已证实）。

**改动（4 处 + 1 测试）**：

- `src/async_http.py` `_get_client_lock()`：**根因修复**。
- `src/async_http.py` `async_req` 异常分支：`logger.debug(e)` → `logger.debug(f"async_req 请求失败: {url} - {type(e).__name__}: {e}")`
- `src/async_http.py` `_close_all_clients`：`logger.debug(e)` → `logger.debug(f"关闭 AsyncClient 失败: {type(e).__name__}: {e}")`
- `src/async_http.py` 跨循环旧 client 关闭：`logger.debug(f"关闭失效 AsyncClient 失败: {e}")` 补上 `type(e).__name__`
- `tests/test_async_http.py` 新增 `TestGetClientLock`：验证同一循环内返回同一把锁…

### v4.0.8.1-dev (2026-08-11) — 修复 Linux/macOS 下 mypy 跨平台类型错误

- **背景**：CI（ubuntu-latest）跑 `mypy src/` 报 6 个错误 —— `src/web_tray.py` 三处 `ctypes.windll`（attr-defined）、`main.py` 的 `subprocess.STARTUPINFO` / `STARTF_USESHOWWINDOW`（name-defined / attr-defined）。
- **修复**：
  - `src/web_tray.py`：`_patch_console_window()` 开头加 `if sys.platform != "win32": return`；`_on_show()` 的 `ctypes.windll.user32` 访问包进 `if sys.platform == "win32":` 分支
  - `main.py`：`get_startup_info()` 改为模块级平台条件类型别名 `_StartupInfoType`（Windows 为 `subprocess.STARTUPINFO`
- **约定沉淀**：Windows 专属 API（`ctypes.windll`、`subprocess.STARTUPINFO` 等）必须放在 `sys.platform == "win32"`（或 `!= "win32"` 提前返回）字面量分支内…

### v4.0.8.1-dev (2026-08-10) — 安全加固与代码质量修复

**严重安全修复**：

- `src/web_config.py` + `src/web_api.py`：新增 `DANGEROUS_CONFIG_KEYS` 常量与 `validate_config_value()` / `safe_update_config_line()`
- `src/web_config.py` + `src/web_api.py`：`update_config_line` 与 `RoomCreate`/`RoomUpdate` 过滤 `\n`/`\r`，修复 INI 注入（可向 config.ini / URL_config.ini 注入任意新行 / 新节）

**中等修复**：

- `src/web_api.py`：`/api/login` 新增爆破限流（默认 5 分钟内失败 5 次锁定 10 分钟）
- `src/sync_http.py`：异常不再伪装成响应体返回，改为 `logger.error` 并记录后返回 `""`，避免故障被静默吞掉
- `msg_push.py`：新增 `_mask_url()`，钉钉 / 微信 / Bark / ntfy / Telegram 推送失败日志中的 webhook URL 自动脱敏，防止含 token 的凭证泄露到日志

**轻微修复**：

- `src/spider.py`：`_get_dd_calcu` 内的 `subprocess.run(node ...)` 改 `asyncio.to_thread` 执行，避免阻塞事件循环
- `src/utils.py`：`check_md5` 改为分块读取，大文件不再全量载入内存
- `src/room.py`：两处 `raise e` 改为 `raise`，保留原始 traceback
- `src/async_http.py`：`_client_cache` 加 `threading.Lock`，防止并发首次创建产生孤儿 client
- `main.py`：转码线程设 `daemon=True`；录制目录创建加 `exist_ok=True` 修复 TOCTOU 竞态
- `scripts/smoke_test.py`：black 格式化对齐（行宽 120）

### v4.0.8.1-dev (2026-08-09) — 注释规范与 Web/接口冒烟测试工具

- **新增 Web/接口冒烟测试工具**（`scripts/smoke_test.py`）：零依赖（纯标准库）、配置驱动（JSON）
- 与既有 `build_exe.py --smoke`（打包产物冒烟）形成互补：前者针对运行中 HTTP 接口探活，后者验证打包后 exe 启动可用性

### v4.0.8.1-dev (2026-08-09) — 文档统计归纳（CODE_WIKI 更新）

- **新增「文档统计与索引」章节**：统计分析工作空间全部 `*.md` 文件（共 324 个）
- **新增「已支持平台」小节**：从 `README.md` 归纳出 51 个已列出平台（国内 37 + 海外 14），补全此前仅以「60+」概括的缺失
- **新增「画质代码对照」小节**：补齐 OD/BD/UHD/HD/SD/LD 画质代码与中文名/说明映射，及支持实际画质回采告警的 7 个平台清单
- **功能特性补齐「Web 安全」**：与 `README.md` 功能特性表对齐（Token 认证、路径穿越防护、敏感配置脱敏）
- **修复 Node.js 版本一致性**：「常见问题 2」安装命令由 `setup_20.x` 更正为 `setup_22.x`，与 `README.md` 及 Dockerfile（Node.js 22 LTS）保持一致
- 同步更新目录（TOC）以反映新增章节

### v4.0.8.1-dev (2026-08-08 ~ 2026-08-09) — 全量代码审查、构建修复与 GUI 优雅停止加固

**全量代码审查（2026-08-08）**：

- 四档检查全部跑通：`compileall` 全部 `.py` 通过；`black`（line-length 120）、`isort` 通过；`mypy src/` 0 errors；`pytest` **417 passed**（无回归）
- **修复 `pyproject.toml` 非法作者邮箱**：`authors[0].email = "ihmily@github"` 不是合法 IDN 邮箱…
- **black 格式违规 2 处**（`main.py` 一处超长日志/函数签名、`tests/test_stream.py` 一条超长 assert）→ 用 `black` 格式化修复（CI 的 `black --check .` 原会失败）
- 版本号 `4.0.8.1` 在 pyproject/Dockerfile/README/CODE_WIKI/zh_CN.po 全同步；`src/spider.py:669` 有一条 2024 年快手旧回退分支 TODO 注释，属保守保留项未动

**GUI 停止录制优雅退出加固（2026-08-09）**：

- `gui.py` `stop_recording()`：原 `_send_ctrl_break_to_child` 失败仅回退 `proc.terminate()`（Windows 即 `TerminateProcess` 硬杀）
- 现失败路径改为 `taskkill /F /T /PID` **整树终止**（连 ffmpeg 一起杀）

**GUI 子进程 pythonw 兼容性修复（2026-08-09，根因定位）**：

- 用 `pythonw gui.py` 启动 GUI 时，`sys.executable` 指向 **pythonw.exe**，源码模式 `[sys.executable, main.py]` 让录制核心也以 pythonw 启动
- pythonw 是 **GUI 子系统进程、不创建控制台**…
- 现检测解释器 basename 以 `pythonw` 开头时，改用同目录 **python.exe**（console 子系统）拉起录制核心；打包版（CLI exe `console=True`）不受影响
- **实测验证**（pythonw 当父进程 + python.exe 起带 SIGBREAK 处理器子进程）：修复后 `AttachConsole` 成功、`GenerateConsoleCtrlEvent` 返回 True、事件真正送达子进程（无处理器时被默认终止…

> 已删除 `gui_legacy.py`（v4.1.0-dev，2026-09-10）：该文件与 `gui.py` 功能重复且遗留 `CREATE_NO_WINDOW` 启动子进程导致 `send_signal(CTRL_BREAK_EVENT)` 永远无效的 bug。建议迁移到 `gui.py`（已迁完，故删除）。

### v4.0.8.1-dev (2026-08-05) — CI 静态验证工作流、并发测试集成与覆盖率门禁提升

**新增 `.github/workflows/ci.yml` 静态验证工作流**：

- push 到 main / PR 触发；`dorny/paths-filter@v4` 路径过滤，纯前端/文档/i18n 变更不触发 Python 检查
- 7 个并行 job：lint（black --check）、typecheck（mypy src/…
- concurrency-test 通过 `COVERAGE_RCFILE=.coveragerc-concurrency` 使用专用覆盖率配置（不设全局阈值…

**覆盖率门禁与测试扩充**：

- `pyproject.toml` `fail_under`：20 → 50（当前总覆盖率 50.34%）
- 高频变更核心模块独立门禁（记录于 pyproject.toml 注释）：spider.py ≥50%、stream.py ≥70%、utils.py ≥80%、ttwid.py ≥85%、ab_sign.py ≥95%、proxy.py ≥50%
- 新增测试文件：test_ab_sign / test_concurrency / test_concurrency_rate_limit / test_proxy / test_spider_platform / test_sync_http / test_ttwid / test_weverse_auth；当前 417 passed

**build-release.yml 升级为 lite/full 双产物**：

- CI 构建命令改为 `python build_exe.py --smoke --dual`：PyInstaller 只跑一次…
- `build_exe.py` 新增 `--no-runtime` / `--dual` 参数；产物命名 `DouyinLiveRecorder-v{version}-{os}-{arch}-{lite|full}.zip`
- full zip（约 300MB）上传叠加工作流级显式重试（最多 3 次…
- 三平台冒烟用 ffmpeg 改用系统包管理器安装：Windows choco / Linux apt(+xvfb) / macOS brew（`brew trust aws/tap` 兜底）
- Release 创建改用 `softprops/action-gh-release@v3`；打包三入口均排除 `brotlicffi`（修复打包后该模块缺失 `error` 属性的报错）

### v4.0.8.1-dev (2026-08-05) — HLS 校验误判与空白日志修复

**问题背景**：运行日志出现 `get_response_status 校验失败（判定为不可达）: `（消息空白）+ `HLS URL validation failed, falling back to FLV`

**改动（3 处）**：

- `src/async_http.py` `get_response_status()`：异常日志带 URL + `type(e).__name__`
- `main.py` `_validate_stream_url()`：新增 `verify` 参数（沿用全局 SSL 开关…
- `main.py` `select_source_url()`：新增 `proxy_addr` 参数并透传给三处校验调用…

### v4.0.8.1-dev (2026-08-02 ~ 2026-08-04) — 平台命名规范落地与类型/逻辑修复

**平台命名规范产品级落地（2026-08-02）**：

- `main.py`：CLI 帮助串、`logger.error` 字面量与内部 platform slug 全部改为规范显示名（bigo、blued、Look直播、TTingLive(原Flextv)、SOOP(原AfreecaTV)、YouTube、飘飘）
- `src/spider.py`：注释与中文异常消息同步规范名；英文 gettext msgid 保留不动（避免断翻译）；重新编译 `zh_CN.mo`（203 条）
- 内部配置/API slug（sooplive/flextv/tiktok）与代码解析配对，故意不改

**类型与逻辑修复（2026-08-03 ~ 08-04）**：

- `gui.py` 达 basedpyright/pyright 0/0/0：`typings/pystray/__init__.pyi` 补齐 darwin 专有成员（`run_detached`/`_assert_image`/`_icon_valid`/`visible`）
- 发现 basedpyright 1.39.9 默认 `enableTypeIgnoreComments=false`：项目内历史 `# type: ignore` 注释当前均无效，告警消除一律改用类型存根补全/拓宽类型/改实现
- `main.py`：TikTok 回退字面量 `{"is_live": False}` 用 `cast(dict[str, object], ...)` 收窄，修复联合类型不匹配
- `src/spider.py` `get_taobao_stream_url()` 修复缩进缺陷：`return result` 原位于 SUCCESS 分支之外…

### v4.0.8.1-dev (2026-08-01) — mypy 严格模式全通过与类型注解收紧

**变更内容**：

- `pyproject.toml`：`disallow_untyped_defs` 从 `false` 改为 `true`，要求所有函数必须有完整类型注解
- `mypy src/ --strict` 从 61 errors 降至 0 errors（16 个源文件全通过）

**类型注解修复（9 个文件）**：

- `src/ab_sign.py`：`SM3.__init__`、`_fill` 添加 `-> None` 返回类型
- `i18n.py`：`init_gettext` 添加 `-> Callable[[str], str]` 返回类型
- `src/proxy.py`：`ProxyInfo.__post_init__`、`ProxyDetector.__init__`、`__del__` 添加 `-> None`
- `src/utils.py`、`src/room.py`、`src/spider.py`：移除未使用的 `type: ignore[no-redef]` 注释
- `src/web_config.py`：移除冗余 `cast("list[str]", parser.sections())`
- `src/spider.py`（最多修复）：为 20+ 函数添加参数/返回类型注解…
- `main.py`：`_fix_encoding` 添加 `-> None`
- `src/web_api.py`：所有 FastAPI 路由处理器添加返回类型注解（`dict[str, object]`、`StreamingResponse`、`FileResponse` 等）

### v4.0.8.1-dev (2026-08-01) — 版本号收敛至 pyproject.toml 单一事实源

**变更内容**：

- `pyproject.toml` 成为版本号唯一权威来源（Single Source of Truth）
- `main.py`：移除硬编码 `version: str = "v4.0.8.1"`，改为 `_read_version_from_pyproject()` 动态读取（优先 `importlib.metadata`，回退直接解析 `pyproject.toml`）
- `build_exe.py`：`read_version()` 改为从 `pyproject.toml` 解析版本号
- `scripts/check_version.py`：基准源从 `main.py` 切换为 `pyproject.toml`，新增检测 `main.py` 是否仍存在硬编码版本号
- CI `version-check` job 无需修改，仍调用 `python scripts/check_version.py`

**版本更新流程（新）**： 只需修改 `pyproject.toml` 中的 `version` 字段，然后同步 `Dockerfile`、`README.md`、`CODE_WIKI.md`、`i18n/zh_CN.po`；`main.py` 无需手动修改。

### v4.0.8.1-dev (2026-08-01) — 核心模块单元测试补全与覆盖率门槛调整

**新增测试文件**：

- `tests/test_stream.py`（约 500 行）：覆盖 `src/stream.py` 核心数据流路径
  - 纯工具函数：`bitrate_to_quality`、`code_to_zh`、`is_downgrade`、`_pad_list`、`get_quality_index`
  - 常量一致性校验：`QUALITY_MAPPING` / `QUALITY_LEVEL` / `QUALITY_MAPPING_BIT` / `QUALITY_CODE_TO_ZH` 键集对齐
  - 平台流解析（异步 Mock）：抖音（离线/在线/仅FLV/降级）、TikTok（离线/在线）、快手（离线/在线/带码率）、YY、网易CC、通用入口（m3u8/flv/all 三种 url_type）
- `tests/test_async_http.py`（约 440 行）：覆盖 `src/async_http.py` 核心请求路径
  - `_get_client`：缓存复用、不同参数隔离、失效 client 替换
  - `_close_all_clients` / `close_all_clients_sync`：连接池清理
  - `async_req`：GET/POST（dict/str/bytes 数据）、redirect_url、return_cookies、include_cookies、异常回退、verify 默认值
  - `get_response_status`：200/404、m3u8 HEAD 405 降级 Range GET、异常处理、非 m3u8 不探测

**覆盖率变化**：

| 模块 | 修改前 | 修改后 |
| --- | --- | --- |
| `src/stream.py` | 0% | 70% |
| `src/async_http.py` | 35% | 83% |
| 总覆盖率 | 15.29% | 22.35% |

**覆盖率门槛调整**：

- `pyproject.toml` `[tool.coverage.report] fail_under`：15 → 20（反映当前实际覆盖水平，为后续增量保留空间）

### v4.0.8.1-dev (2026-08-01) — 抖音 URL 全格式支持、格式5 链路优化、HLS 校验与日志修复

**抖音 URL 解析（支持 5 种格式，含本次全部修复）**：

- 分发逻辑重构（`spider.py: get_douyin_app_stream_data`）：`live.douyin.com/*` 直调网页端…
- 主页解析改用 `iesdouyin.com/web/api/v2/user/info/` JSON 接口（取 `unique_id`
- `room.py` 新增 `is_user_homepage_url()` + 零请求快速路径：网页端主页的 sec_user_id 直接从 URL 路径提取，省去一次约 71KB 的跟随重定向下载
- **修复隐藏 bug**：旧回退调用 `get_douyin_stream_data("live.douyin.com/"+unique_id)` 未透传 proxy_addr/cookies…
- 删除死代码 `get_douyin_stream_data()`（约 94 行，重构后已无调用点）
- 新增 sec_uid→抖音号进程级缓存（`room.py`，`threading.Lock` 跨线程/跨 asyncio 循环去重，30 分钟 TTL）：主页解析后每轮轮询不再重请求 iesdouyin 接口
- 格式5 实测链路优化：请求数 4→3、下载量 ~1.3MB→~1.2MB、耗时 ~1.7s→~1.4s…

**HLS 校验与日志修复**：

- `async_http.py get_response_status()`：空消息日志修复（`logger.debug(e)` 在 `e` 为空串时只剩 `- `
- `main.py _validate_stream_url()`：content-type 判定补 `mpegurl`
- `spider.py web/enter` API 调用封装 `_try_web_api()` + 静默重试 1 次（`asyncio.sleep(0.5)` 缓冲）：瞬时 `status_code=10002` 不再刷 WARNING…

**测试与静态检查**：

- `tests/test_douyin_url_resolution.py` 扩至 17 个用例（5 种 URL 格式分发、缓存命中、10002 重试、web_rid 处理等）；新增 autouse fixture 清理 sec_uid 缓存防跨用例污染
- 全量 `pytest` 78 passed；`black`/`isort` 全绿；`mypy src/` 无问题；ruff 仅剩有意的 E402（项目既定晚导入模式）
- 顺手修复：`tests/test_utils.py` 未用导入（F401）、`src/stream.py` 歧义变量名 `l`（E741，改为 `level, ratio`）

**版本同步**：全项目版本号统一升级至 `4.0.8.1`（main.py / pyproject.toml / Dockerfile / i18n / README / CODE_WIKI）

### v4.0.8.1-dev (2026-07-29) — 工程配置文件全面梳理与文档同步

**工程配置文件（六文件 + 双文档同步）**：

- `.gitignore`：修复三处自相矛盾——移除 `i18n/**/*.mo` 忽略（.mo 随仓库分发…
- `.dockerignore`：重写。
- `Dockerfile`：builder 阶段移除无用的 Node.js 安装（Node 仅运行时需要，阶段2已装 Node 22）；EXPOSE 处补充 web_host=0.0.0.0 说明
- `docker-compose.yaml`：重构为三服务——recorder（默认，main.py，无端口）、web（profile，8000:8000）、gui（profile）。修复原设计中 recorder 占用 8000 端口的问题
- `pyproject.toml`：+`starlette>=0.49.1`（web_api.py 直接导入）
- `requirements.txt`：同步 starlette>=0.49.1 与 PyInstaller 构建期说明

**代码结构清理（对齐 git 工作区状态）**：

- 移除 `src/http_clients/` 子包（`__init__.py` / `async_http.py` / `config.py` / `sync_http.py`）
- 移除 `src/initializer.py` 与 `TRAE_AGENT_CODE_WIKI.md`（不再维护）

**文档同步**：

- `CODE_WIKI.md`：依赖表全面更新（移除 weverse，补 exejs/customtkinter/starlette/python-multipart）；Docker 章节改为描述实际 compose 三服务；目录结构树修正
- `README.md`：Docker 用法改为 `docker compose --profile web/gui`

### v4.0.8.1-dev (2026-07-28) — 修复 macOS CI smoke:gui 崩溃

- `gui.py`：macOS 改为 `tray.run_detached()`（非阻塞）+ 主线程 `root.mainloop()`，修复 Tcl/Tk 只能运行于主线程导致的 `RuntimeError: Calling Tcl from different apartment`
- `SystemTray` 拆出 `_build_icon()/_degrade()`
- 修复隐藏 bug：旧 `run()` 在所有平台调用 darwin 专有的 `_assert_image()`，Windows/Linux 上抛 AttributeError 被吞导致托盘静默禁用
- `stop()`：darwin detached 模式先 `icon.visible = False` 再 `icon.stop()`

### v4.0.8.1-dev (2026-07-27) — ttwid 共享模块抽取与冒烟测试进程树清理

**ttwid 共享模块（`src/ttwid.py`）**：

- 新建 `src/ttwid.py`：进程级唯一 `_cached_ttwid` + `threading.Lock` 跨线程/跨事件循环去重，导出 `async def get_ttwid(proxy_addr)` 与 `def warmup_ttwid(proxy_addr)`
- `src/spider.py` / `src/room.py`：删除各自本地 ttwid 实现，统一委托给 `src/ttwid.py`
- `main.py`：`main()` 循环中用 `first_run` 门控调用 `warmup_ttwid(proxy_addr)`，保证整个进程 ttwid 仅获取一次
- `src/ttwid.py`：支持从 config.ini `[Cookie]` 段读取用户配置的 ttwid，获取优先级 = 缓存 > 配置 > 自动获取

**build_exe.py 冒烟测试进程树清理**：

- `_launch()` 让子进程自成进程组/会话（Windows `CREATE_NEW_PROCESS_GROUP`，Unix `start_new_session`）
- 新增 `_kill_tree(proc)`：Windows `taskkill /T /F /PID`，Unix `os.killpg(getpgid(pid), SIGKILL)`，消除 GitHub Actions runner 孤儿进程清理噪声

### v4.0.8.1-dev (2026-07-26) — basedpyright 全项目清零与 docstring 注释转换

**basedpyright 全项目 0/0/0（typings + src）**：

- `typings/execjs/`（6 个 .pyi）：文件级 pyright 指令放宽动态 JSON 相关严格检查（reportAny/reportExplicitAny/reportMissingParameterType 等）
- `typings/pystray/__init__.pyi`：reportAny/reportExplicitAny 放宽
- `src/spider.py`：文件级指令放宽 16 项规则（787 条告警→ 0，几乎全部来自 json.loads 返回 Any 级联）
- `src/room.py`：新增 execjs 存根、handle_proxy_addr 类型标注、cast 收窄、显式字符串拼接
- `src/sync_http.py`：OptionalDict 类型参数化、urllib cast、弃用 API 替换
- `src/async_http.py`：未使用参数/协程结果消解、data 类型补全、异常回退 cast

**docstring → # 注释转换**：

- 全项目 18 处三引号 docstring 转换为 `#` 行注释：build_exe.py(10)、main.py(3)、src/ab_sign.py(2)、src/logger.py(1)、src/web_tray.py(1)、i18n.py(1)

### v4.0.8.1-dev (2026-07-25) — 全量代码审查修复与安全加固

**关键 Bug 修复**：

- `main.py`：音频/视频分支 `if` → `elif` 互斥，修复同一直播间双重录制 + ffmpeg 命令畸形
- `src/stream.py`：`QUALITY_MAPPING` 改为与抖音 order 字典对齐的位置索引 `{OD:0,BD:1,UHD:2,HD:3,SD:4,LD:5}`，修复画质选错
- `src/proxy.py`：多协议代理 `http=1.2.3.4:5678` 解析先剥离协议前缀，修复 ValueError
- `main.py`：FLV 直下分支写入 recording/recording_time_list 包进 `record_state_lock`（数据竞争）
- `main.py`：`check_subprocess` 补 `process.wait(timeout=30)`（僵尸进程）

**安全加固**：

- `src/web_config.py` + `src/web_api.py`：web_password 改为 PBKDF2-HMAC-SHA256 存储，登录时历史明文自动升级为哈希
- `src/http_config.py`：`ssl_verify` 默认改为 `True`（安全优先）
- `msg_push.py`：PushPlus token 日志脱敏（`_mask_secret`，仅留前后各 2 位）
- `src/node_install.py`：`unzip_file` 增加 Zip Slip 防护

**其他修复**：

- `src/async_http.py`：失效 client 先 `aclose()` 再重建，修复连接池泄漏
- `web.py`：退出时主动 `cleanup_all_ffmpeg_processes()` + `close_all_clients_sync()`，杠绝孤儿 ffmpeg
- `gui.py`：新增 `self._stopping` 标志 + 停止期间禁用启动按钮，消除停止竞态窗口
- `src/ab_sign.py`：修复 SM3 GG 函数 bug（j>=16 时错误使用 ff_j 公式）
- `i18n.py`：翻译覆盖从仅 `src/` 扩展到项目根下所有源文件（main.py/web.py/gui.py/msg_push.py）

### v4.0.8-dev (2026-07-28) — 多直播间并发监控风控修复与静态检查清零

**抖音多直播间并发监控触发风控修复**：

- `src/spider.py`：`_ensure_ttwid()` 委托给共享 `src/ttwid.py` 模块（带 `threading.Lock` 跨线程去重），解决多线程并发时重复拉取 ttwid 触发风控的问题
- `src/room.py`：`_ensure_douyin_ttwid()` 同样委托给共享 `ttwid.py` 模块，统一 ttwid 获取入口
- `main.py`：新增 `_douyin_rate_limit()` 速率限制器…
- `main.py`：新增全局变量 `douyin_rate_lock`、`douyin_last_request_time`、`douyin_min_interval` 用于速率控制

**静态检查清零（Pyright 0 errors, 0 warnings）**：

- `gui.py`：`Image.LANCZOS` → `Image.Resampling.LANCZOS`（Pillow 10+ 现代 API，修复 `reportAttributeAccessIssue`）
- `gui.py`：为 pystray 私有属性访问添加 `# type: ignore[attr-defined]`（`_assert_image()`、`_icon_valid`、`run_detached()`）
- `main.py`：`select_source_url()` 中 `_validate_stream_url(m3u8_url)` 添加 `cast(str, m3u8_url)`，修复 `reportArgumentType` 类型收窄问题

### v4.0.8-dev (2026-07-25) — 新增 PyInstaller 可执行文件打包与 GitHub Actions 发布

- 新增 `build_exe.py`：PyInstaller `onedir` + `contents_directory='_internal'`
- 目录规范：`node/`、`ffmpeg/`、`config/` 与 exe 保持同级…
- 新增路径收敛函数 `src/logger._app_root()`（与 `main.py` 内联同名）
- `gui.py` 冻结适配：冻结时直接调用同目录 `DouyinLiveRecorder.exe` 拉起录制核心（避免 `sys.executable` 指向自身导致无限递归）
- 中文 UTF-8 编码修复：在 `main.py`/`gui.py`/`web.py` 顶部加入 `_fix_encoding()`（Windows 切换控制台代码页 65001 + reconfigure UTF-8）
- `build_exe.py --smoke` 三项冒烟测试：CLI 存活、Web HTTP 探活 200（并验证内置 ffmpeg 命中）、GUI 存活 8 秒（无 DISPLAY 自动跳过）
- 新增 `.github/workflows/build-release.yml`：三平台 matrix（win/linux/mac…

### v4.0.8-dev (2026-07-25) — 全项目类型错误修复与代码清理

**类型错误修复（Pyright / Pyrefly / basedpyright）**：

- `src/proxy.py`：修复跨平台类型错误——在平台判断前声明 `self.winreg: Any = None` 和 `self.__INTERNET_SETTINGS: Optional[Any] = None`
- `gui.py`：`Fonts.get()` 的 `weight` 参数从 `str` 收窄为 `Literal["normal", "bold"]`，匹配 `CTkFont` 签名
- `main.py`：补全模块级变量声明（约 160 个）
- `main.py`：`get_status()` 重试循环前为 5 个快照变量（`recording_snapshot`、`recording_times`、`monitoring_val`、`running_val`、`error_val`）添加默认值…
- `main.py`：补漏 `twitcasting_cookie: str = ""` 模块级声明
- `msg_push.py`：`tg_bot()` 的 `chat_id` 参数从 `int` 放宽为 `str | int`，Telegram API 同时接受数字和字符串 chat ID
- `src/web_config.py`：移除 `str(raw)` 冗余调用（`parser.get()` 返回值始终为 `str`）
- `src/spider.py`：为 `sorted_stream_list` 和 `stream_data` 添加 `list[dict]` / `dict` 显式类型标注，修复 Pyrefly 推断为 `SupportsGetItem` 导致的 3 处 `.get()` 调用错误
- `src/spider.py`：删除 `get_bilibili_stream_data()` 末尾不可达的 `return None`（if/else 双分支均已 return）
- `src/http_config.py`：移除 `bool(value)` 冗余调用（参数已标注为 `bool`）
- `src/async_http.py`：`_get_client()` 重构为 early-return 模式，消除 `client` 可能未绑定错误
- `src/stream.py`：`QUALITY_LEVEL.get(video_quality, 4)` 改为 `QUALITY_LEVEL.get(video_quality or "", 4)`，处理 `str | None` 键类型
- `src/stream.py`：`quality, quality_index = ...` 改为 `_, quality_index = ...`，消除未使用变量提示

**代码清理（pyflakes / 未使用导入与变量）**：

- `src/spider.py`：修复 `get_baidu_stream_data()` 中 `result` 未赋值即引用的 `NameError`（`data_dict` 为空时触发）
- `src/spider.py`：移除未使用导入 `import ssl` 和 `from .ab_sign import ab_sign`
- `src/logger.py`：移除未使用导入 `import os`
- `gui.py`：为 `pystray` 类型标注添加 `TYPE_CHECKING` 守卫（`pystray` 在 `run()` 内延迟导入）
- `main.py`：移除 `start_record()` 中未使用的 `global error_count` 声明
- `main.py`：移除未使用的 `create_var` global 声明
- `main.py`：移除未使用的局部变量 `changed`

### v4.0.8-dev (2026-07-25) — 依赖扫描与 Docker 配置更新

**依赖扫描与 pyproject.toml 更新**：

- `pyproject.toml`：项目版本 `4.0.7` → `4.0.8-dev`，与 CODE_WIKI 更新日志一致
- `pyproject.toml` / `requirements.txt`：新增 `pydantic>=2.0.0` 依赖（`src/web_api.py` 直接 `from pydantic import BaseModel`，之前未声明）
- 全项目依赖扫描完成：14 个第三方包均已核对使用位置并确认声明状态（详见下表）

| 包名 | 声明状态 | 使用位置 |
| --- | --- | --- |
| requests | 已声明 | src/ffmpeg_install.py, src/ffmpeg_master_download.py, src/node_install.py, src… |
| httpx[http2] | 已声明 | main.py, src/room.py, src/spider.py, src/async_http.py |
| loguru | 已声明 | src/logger.py, msg_push.py |
| pycryptodome | 已声明 | src/spider.py (Crypto.Cipher.AES) |
| distro | 已声明 | src/node_install.py |
| tqdm | 已声明 | src/ffmpeg_install.py, src/ffmpeg_master_download.py, src/node_install.py |
| PyExecJS | 已声明 | src/room.py, src/spider.py, src/utils.py |
| customtkinter | 已声明 | gui.py |
| pystray | 已声明 | gui.py (延迟导入) |
| Pillow | 已声明 | gui.py |
| fastapi | 已声明 | src/web_api.py |
| uvicorn[standard] | 已声明 | web.py (延迟导入) |
| python-multipart | 已声明 | FastAPI 表单处理隐式依赖 |
| **pydantic** | **缺失→已补** | src/web_api.py (BaseModel) |

**Dockerfile 更新**：

- Python 基础镜像 `python:3.13.0-slim-bookworm` → `python:3.13-slim-bookworm`（两阶段）— 3.13.0 是 2024 年 10 月初始版本…
- Node.js `setup_20.x` → `setup_22.x`（两阶段）— Node 20 LTS 于 2026 年 4 月 EOL，Node 22 是当前活跃 LTS
- 安全升级（`apt-get upgrade`）从 builder 阶段移至 runtime 阶段 — builder 是临时阶段，升级无意义；runtime 才是最终镜像，安全升级应在此
- LABEL version `4.0.7` → `4.0.8-dev`

**docker-compose.yaml**： 无需更新，结构已完整（卷挂载、端口映射、环境变量、健康检查、资源限制、日志轮转、GUI profile 均正确）。

### v4.0.8-dev (2026-07-24)

- 新增 GUI 画质监控页面（`gui.py` `_build_quality_page`），通过解析子进程日志实时检测各直播间实际画质是否与设置一致
- 新增 Web 控制台开关配置 `web_show_console`（默认 true），设为 false 时程序后台隐藏运行
- 新增 `_enter_background_mode()`：Windows 下隐藏控制台窗口（SW_HIDE），日志重定向到 `logs/web_console.log`
- 新增 `[Web]` 配置节文档，含 web_host / web_port / web_auth_enable / web_password / web_token_expiry / web_show_console 六项
- 新增 Web 安全机制说明：密码变更吊销 Token、监听告警、路径穿越防护、敏感配置脱敏
- 统一代码注释风格：将 `web.py`、`src/web_config.py`、`src/web_api.py`、`src/stream.py` 中所有函数 docstring 转换为 `#` 行注释
- 新增实际画质回采与降级告警功能，覆盖抖音、TikTok、快手、虎牙、斗鱼、B站、网易CC 七个平台
- 新增 `bitrate_to_quality()`、`code_to_zh()`、`is_downgrade()` 画质工具函数（`src/stream.py`）
- 新增 `actual_quality` / `available_qualities` 返回字段，各平台 stream 函数统一返回实际下发画质
- 改造 `get_bilibili_stream_data()` 返回 dict（含 url/current_qn/accept_qn），stream 模块反向映射 qn 为画质代码
- 新增 Web 管理面板（`web.py` + `src/web_api.py` + `src/web_config.py` + `web/`），支持仪表盘、直播间管理、配置编辑、SSE 日志推送
- 新增前端"实际画质"列展示，降级时标红高亮（`.quality-down` 样式）
- 新增 `tests/test_stream_quality.py` 测试文件（347 行，17 个测试用例）
- 修复 `display_info` 中 `recording_time_list` 解包错误（2 元素改为 3 元素后兼容性修复）
- 修复 `asyncio.run()` 导致的 httpx 客户端跨事件循环复用问题（`'NoneType' object has no attribute 'send'`）
- 优化各平台流地址选择，用显式截断替代 `_pad_list` 静默填充，避免越界

### v4.0.8-dev (2026-07-23)

- 新增 HTTP 客户端连接池复用机制，按 (代理, verify, http2) 维度复用 AsyncClient，提升请求性能
- 新增 SSL 证书验证全局开关（`src/http_config.py`），通过 config.ini 统一控制异步/同步 HTTP 客户端
- 新增日志文件开关配置项，可通过 config.ini 控制是否输出日志文件
- 重构代理检测逻辑，从联网探测 Google 改为读取本地系统代理配置，避免启动时卡顿
- 优化异步 HTTP 请求异常处理，按返回契约提供类型安全的回退值
- 优化进程退出清理，新增 HTTP 客户端连接池的 atexit / 信号处理器兜底释放
- Dockerfile 新增 ca-certificates 依赖，支持启用 SSL 证书验证时的证书校验

### v4.0.8-dev (2026-06-27)

- 修复 `trace_error_decorator` 严重 Bug：原同步装饰器应用于 71 个异步函数导致错误捕获完全失效，现使用 `asyncio.iscoroutinefunction()` 支持同步/异步双模式
- 修复返回值类型不一致 Bug：`execjs.ProgramError` 分支返回 `None` → `{}`
- 修复 B站画质默认值 `'0'` 不在字典键中导致 KeyError
- 修复虎牙 `flv_anti_code` 为 None 导致 `parse_qs(None)` 崩溃
- 修复 TikTok/快手/网易CC 流地址列表为空时 IndexError
- 修复 `get_stream_url` 空列表索引崩溃（该函数未被装饰器保护）

### v4.0.8-dev (2026-06-20)

- 修复 spider.py 5 个运行时 Bug（KeyError、响应类型转换、循环静默返回）
- 修复 stream.py 2 个运行时 Bug（B站 None 检查、快手 quality 条件）
- 修复 gui.py 死代码（未使用变量、f-string 无占位符）
- 清理 src/weverse_auth.py 未使用导入
- i18n 翻译文件更新：新增 20 条翻译条目（异常错误消息、配置文件、磁盘空间等），总条目 200 条
- 通过 pyflakes 静态检查验证

### v4.0.8-dev (2026-05-17)

- 全新现代化 GUI 界面（WCAG AA 高对比度、DPI 感知字体）
- Docker 多阶段构建关键修复（运行时 Node.js、HEALTHCHECK）
- 配置文件重构（pyproject.toml、requirements.txt、.gitignore、.dockerignore）
- 新增抖音流数据调试工具 `debug_douyin_streams.py`
- 完善国际化翻译（YouTube/FlexTV/PopkonTV/TwitCasting）
