# DouyinLiveRecorder 项目架构文档

## 项目概述

**DouyinLiveRecorder**（抖音直播录制器）是一款基于 Python 和 FFmpeg 的开源直播录制工具，支持 **60+ 国内外直播平台**的实时循环值守录制。项目采用模块化架构设计，支持命令行和 GUI 双模式运行，具备多平台适配、消息推送、Docker 部署等企业级功能。

| 属性 | 值 |
|------|------|
| 当前版本 | v4.0.7 |
| Python 版本 | `>= 3.10` |
| 项目地址 | https://github.com/ihmily/DouyinLiveRecorder |
| 许可证 | MIT |
| 包管理器 | pip / uv |

---

## 目录结构

```
DouyinLiveRecorder/
├── config/                              # 配置文件目录
│   ├── config.ini                     # 主配置文件（录制/推送/Cookie/账号）
│   └── URL_config.ini                 # 直播间地址列表
├── src/                                # 核心源码包
│   ├── __init__.py                    # 包初始化（Node.js 环境路径配置）
│   ├── spider.py                      # 直播数据获取（各平台异步 API 调用）
│   ├── stream.py                      # 直播流解析（URL 提取、画质选择）
│   ├── room.py                        # 直播间信息（URL 解析、房间 ID、签名）
│   ├── utils.py                       # 工具函数（配置读写、文件操作、字符串处理）
│   ├── logger.py                      # 日志配置（Loguru 集成）
│   ├── proxy.py                       # 代理检测（Windows 注册表 / Linux 环境变量）
│   ├── ab_sign.py                     # 抖音签名算法（SM3、RC4、A-Bogus）
│   ├── initializer.py                  # 环境初始化（Node.js 自动安装）
│   ├── weverse_auth.py                # Wevers 认证模块
│   ├── http_clients/                  # HTTP 客户端封装
│   │   ├── __init__.py
│   │   ├── async_http.py              # 异步 HTTP 请求（httpx）
│   │   └── sync_http.py               # 同步 HTTP 请求
│   └── javascript/                    # JavaScript 签名脚本
│       ├── crypto-js.min.js           # CryptoJS 加密库
│       ├── x-bogus.js                 # 抖音 X-Bogus 签名算法
│       ├── taobao-sign.js             # 淘宝签名算法
│       ├── migu.js                    # 咪咕签名脚本
│       └── liveme.js                  # LiveMe 签名脚本
├── downloads/                          # 录制文件保存目录
├── logs/                              # 日志文件目录
├── i18n/                              # 国际化文件（中文 / 英文）
│   ├── zh_CN/LC_MESSAGES/
│   │   ├── zh_CN.po                  # 中文翻译源文件
│   │   └── zh_CN.mo                  # 编译后的翻译文件
│   └── en/LC_MESSAGES/
├── main.py                            # 命令行模式入口（约 2370 行）
├── gui.py                             # GUI 图形界面入口（约 1172 行，现代化深色主题）
├── msg_push.py                        # 消息推送模块
├── ffmpeg_install.py                 # FFmpeg 安装脚本
├── demo.py                           # 调用示例
├── i18n.py                           # 国际化实现（gettext 封装）
├── requirements.txt                   # Python 依赖清单
├── pyproject.toml                    # Python 项目配置（setuptools + uv）
├── Dockerfile                        # Docker 多阶段构建文件
├── docker-compose.yaml               # Docker Compose 配置
├── StopRecording.vbs                 # Windows 停止录制 VB 脚本
├── .dockerignore                    # Docker 构建排除规则
└── .gitignore                       # Git 版本控制排除规则
```

---

## 整体架构

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                         用户交互层                                 │
│   ┌──────────────────┐          ┌──────────────────────┐         │
│   │   main.py        │          │   gui.py             │         │
│   │  命令行交互模式    │          │  现代化深色 GUI 界面   │         │
│   └────────┬─────────┘          └──────────┬───────────┘         │
└─────────────┼──────────────────────────────────┼──────────────────┘
              │                                  │
              ▼                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                         核心业务层                                 │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │                      main.py                              │   │
│   │  配置解析 → 多线程调度 → FFmpeg 进程管理 → 录制流程控制    │   │
│   │  直播状态监控 → 消息推送触发 → 配置热更新 → 信号安全退出    │   │
│   └──────────────────────────────────────────────────────────┘   │
│                              │                                    │
│   ┌──────────┬──────────────┼──────────────┬──────────────┐    │
│   ▼          ▼              ▼              ▼              ▼       │
│ ┌────┐  ┌────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐   │
│ │spider│  │ stream │  │ msg_push │  │  utils  │  │  logger  │   │
│ └────┘  └────────┘  └──────────┘  └─────────┘  └──────────┘   │
└──────────────────────────────────────────────────────────────────┘
              │              │              │
              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────────┐
│                         平台适配层                                │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    spider.py                               │   │
│  │  抖音 │ TikTok │ 快手 │ 虎牙 │ B站 │ 斗鱼 │ YouTube │ ... │   │
│  └────────────────────────────────────────────────────────────┘   │
│                              │                                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    stream.py                                │   │
│  │  流地址解析 │ 画质映射 │ 码率排序 │ URL 选择策略             │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────────────┐
│                         基础设施层                                │
│  ┌───────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │ httpx      │  │ FFmpeg     │  │ Node.js    │  │ INI 配置  │  │
│  │ 异步 HTTP  │  │ 录制转码    │  │ JS 签名执行 │  │ 配置文件   │  │
│  └───────────┘  └────────────┘  └────────────┘  └──────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 数据流向

```
直播间 URL
    │
    ▼
┌────────────────────┐
│ URL 解析与平台识别   │ ──► 从 PLATFORM_HOST 匹配直播平台
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ spider.py          │ ──► asyncio + httpx 异步请求平台 API
│ (异步并发,Semaphore)│ ──► 获取主播名、直播状态、原始流数据
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ stream.py          │ ──► 解析流地址、选择画质、带宽排序
│ (统一返回格式)      │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ select_source_url  │ ──► 抖音/TikTok 优先 FLV，其他选 record_url
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ FFmpeg 录制进程    │ ──► 实时录制，支持分段、自动转码
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ 文件输出            │ ──► TS / MKV / FLV / MP4 / MP3 / M4A
│ (downloads/平台/)   │
└────────────────────┘
```

---

## 核心模块详解

### 1. main.py - 命令行主程序入口

**文件路径**：`/workspace/main.py`（约 2370 行）

**核心职责**：配置读取与热更新、多平台直播流获取解析、FFmpeg 录制进程管理、多线程并发控制（Semaphore 限流）、错误处理与动态并发调优、直播状态消息推送。

**全局状态变量**：

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `recording` | set | 正在录制的直播间名称集合 |
| `monitoring` | int | 当前监控的直播间数量 |
| `running_list` | list | 正在运行的 URL 列表 |
| `recording_time_list` | dict | 记录每个直播间的开始录制时间 |
| `error_count` | int | 当前错误计数（动态调优） |
| `max_request` | int | 同时访问网络的线程数（动态调整） |
| `url_tuples_list` | list | 解析后的 URL 配置列表 (画质, URL, 主播名) |
| `exit_recording` | bool | 全局退出标志 |

**核心函数**：

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `start_record()` | url_data: tuple, count_variable: int | None | 启动单个直播间录制主循环 |
| `check_subprocess()` | record_name, record_url, ffmpeg_command, save_type | bool | 监控 FFmpeg 进程状态 |
| `display_info()` | 无 | None | 显示录制状态信息（5秒刷新） |
| `push_message()` | record_name, live_url, content | None | 触发多渠道消息推送 |
| `segment_video()` | converts_file_path, segment_save_file_path, segment_format, segment_time | None | FFmpeg 视频分段 |
| `converts_mp4()` | converts_file_path, is_original_delete | None | 转换为 MP4 格式 |
| `generate_subtitles()` | record_name, ass_filename, sub_format | None | 生成时间字幕线程 |
| `adjust_max_request()` | 无 | None | 后台线程：动态调整并发数 |
| `safe_exit()` | signum, frame | None | 信号处理器：安全退出 |
| `register_ffmpeg_process()` | process | None | 注册 FFmpeg 进程 |
| `cleanup_all_ffmpeg_processes()` | 无 | None | 并行清理所有 FFmpeg 进程 |

### 2. src/spider.py - 直播数据获取模块

**文件路径**：`/workspace/src/spider.py`（约 1500+ 行）

**核心职责**：封装各平台直播 API，统一使用 `asyncio` + `httpx` 实现异步并发请求。

**核心异步函数**（按平台分组）：

| 函数名 | 平台 | 说明 |
|--------|------|------|
| `get_douyin_web_stream_data()` | 抖音 Web | 网页端 API，支持 A-Bogus 签名 |
| `get_douyin_app_stream_data()` | 抖音 App | APP 端接口（备用） |
| `get_tiktok_stream_data()` | TikTok | TikTok 直播 API |
| `get_kuaishou_stream_data()` | 快手 | 快手直播 API |
| `get_huya_stream_data()` | 虎牙 | 虎牙直播 API |
| `get_bilibili_room_info()` | B站 | B 站直播间信息 |
| `get_douyu_info_data()` | 斗鱼 | 斗鱼直播 API |
| `get_yy_stream_data()` | YY | YY 直播 API |
| `get_xhs_stream_url()` | 小红书 | 小红书直播 API |
| `get_bigo_stream_url()` | Bigo | Bigo 直播 API |
| `get_sooplive_stream_data()` | SOOP | 韩国 SOOP 直播（需账号密码） |
| `get_youtube_stream_url()` | YouTube | YouTube 直播 API |
| `get_taobao_stream_url()` | 淘宝 | 淘宝直播 API |
| `get_shopee_stream_url()` | Shopee | Shopee 直播 API |
| `get_twitchtv_stream_data()` | Twitch | Twitch 直播 API |

**统一返回数据格式**：
```python
{
    "anchor_name": "主播昵称",
    "is_live": True / False,
    "title": "直播标题",           # 可选
    "stream_url": {...},           # 原始流数据
    "play_url_list": [...],        # 通用格式
}
```

### 3. src/stream.py - 直播流解析模块

**文件路径**：`/workspace/src/stream.py`（约 392 行）

**核心职责**：解析 spider 返回的原始数据，提取可用直播流地址，支持画质选择和带宽排序。

**画质映射常量**：
```python
QUALITY_MAPPING = {
    "OD": 0,    # 原画 (Original)
    "BD": 0,    # 蓝光 (Blue-ray)
    "UHD": 1,   # 超清 (Ultra HD)
    "HD": 2,    # 高清 (HD)
    "SD": 3,    # 标清 (SD)
    "LD": 4     # 流畅 (Low Definition)
}
```

**核心异步函数**：

| 函数名 | 平台 | 说明 |
|--------|------|------|
| `get_douyin_stream_url()` | 抖音 | 解析 FLV/HLS 流，计算质量索引 |
| `get_tiktok_stream_url()` | TikTok | 解析多码率流，按带宽排序 |
| `get_kuaishou_stream_url()` | 快手 | 解析 m3u8/flv URL |
| `get_huya_stream_url()` | 虎牙 | 重新计算 anti-code 签名 |
| `get_douyu_stream_url()` | 斗鱼 | 获取 RTMP 地址 |
| `get_bilibili_stream_url()` | B站 | 获取直播间流 URL |
| `get_stream_url()` | 通用 | 平台无关的通用流解析 |

### 4. src/room.py - 直播间信息模块

**核心职责**：解析直播间 URL，获取房间 ID、用户 secID 等信息。

**核心函数**：

| 函数名 | 参数 | 说明 |
|--------|------|------|
| `get_sec_user_id()` | url, proxy_addr, headers | 获取抖音房间 webRid 和 secUserID |
| `get_unique_id()` | url, proxy_addr, headers | 获取抖音号 |
| `get_live_room_id()` | room_id, sec_user_id, ... | 获取直播间 webRid |
| `get_xbogus()` | url, headers | 计算 X-Bogus 签名 |
| `get_kuaishou_stream_headers()` | None | 获取快手请求头 |
| `process_hls_url()` | url, platform | 处理不同平台的 HLS 流地址 |

**异常类**：
- `UnsupportedUrlError` — 不支持的 URL 格式异常

### 5. src/ab_sign.py - 抖音签名算法模块

**核心职责**：实现抖音 A-Bogus 签名算法，组合 SM3（国密哈希）、RC4（流加密）和自定义 Base64 编码。

**核心函数**：

| 函数名 | 说明 |
|--------|------|
| `ab_sign(url_search_params, user_agent)` | 生成 A-Bogus 签名 |
| `generate_random_string()` | 生成随机字符串 |
| `generate_rc4_bb_str()` | 生成 RC4 加密字符串 |
| `rc4_encrypt(plaintext, key)` | RC4 对称加密 |

**签名流程**：SM3 摘要 → RC4 加密 → 自定义 Base64 编码 → 生成最终签名

### 6. src/utils.py - 工具函数模块

| 类/函数名 | 说明 |
|-----------|------|
| `Color` | 终端 ANSI 彩色输出（RED/GREEN/YELLOW/BLUE 等） |
| `trace_error_decorator` | 统一异常处理装饰器，自动记录错误行号 |
| `check_md5()` | 计算文件 MD5 值 |
| `read_config_value()` | 读取 INI 配置项 |
| `update_config()` | 更新 INI 配置项 |
| `remove_emojis()` | 正则移除 Unicode 表情符号 |
| `check_disk_capacity()` | 检查磁盘剩余空间（GB） |
| `handle_proxy_addr()` | 处理代理地址格式 |

### 7. src/logger.py - 日志配置模块

基于 Loguru，双文件输出。`streamget.log`（DEBUG 级，排除 INFO）用于调试，`PlayURL.log`（INFO 级）仅记录直播流 URL。支持 300KB 轮转保留 1 份。

### 8. src/proxy.py - 代理检测模块

`ProxyDetector` 类检测系统代理：Windows 读注册表，Linux 读 `http_proxy` / `https_proxy` 环境变量。`ProxyInfo` 为 frozen dataclass。

### 9. src/initializer.py - 环境初始化模块

自动检测并安装 Node.js。Windows 从官网下载安装包，Ubuntu/CentOS/macOS 通过包管理器安装。

### 10. src/http_clients/ - HTTP 客户端模块

`async_http.py` 基于 httpx 的异步客户端，支持代理、自定义 headers、JSON 数据。全局连接池限制 `max_connections=100`。`sync_http.py` 为同步版本。

### 11. msg_push.py - 消息推送模块

支持钉钉、微信（Server 酱）、邮箱、Telegram Bot、Bark、NTFY、PushPlus 共 7 种渠道。统一返回 `{"success": [...], "error": [...]}`。触发时机：开播 / 关播 / 仅推送模式。

### 12. gui.py - GUI 图形界面

基于 Tkinter 的现代化深色主题界面。核心组件：`Colors` 配色方案（高对比度 WCAG AA）、`CardFrame` 卡片容器、`GradientBanner` 渐变标题、`StatusIndicator` 状态指示灯、`ModernTextWidget` 圆角文本框、`SystemTray` 系统托盘。

---

## JavaScript 签名脚本

位于 `src/javascript/`，通过 PyExecJS（Node.js 驱动）在 Python 中执行：

| 文件名 | 平台 | 说明 |
|--------|------|------|
| `crypto-js.min.js` | 通用 | CryptoJS 加密库 |
| `x-bogus.js` | 抖音 | X-Bogus 签名算法 |
| `taobao-sign.js` | 淘宝 | 淘宝签名算法 |
| `migu.js` | 咪咕 | 咪咕签名脚本 |
| `liveme.js` | LiveMe | LiveMe 签名脚本 |

---

## 依赖关系

### Python 依赖（requirements.txt）

| 包 | 版本 | 用途 |
|----|------|------|
| requests | >=2.28.0 | HTTP 请求库 |
| httpx[http2] | >=0.25.0 | 异步 HTTP 客户端 |
| loguru | >=0.7.0 | 日志库 |
| pycryptodome | >=3.15.0 | 加密库（SM3、RC4） |
| distro | >=1.8.0 | Linux 发行版检测 |
| tqdm | >=4.65.0 | 终端进度条 |
| PyExecJS | >=1.5.1 | JavaScript 执行引擎 |
| pystray | >=0.19.4 | 系统托盘（GUI） |
| Pillow | >=10.0.0 | 图像处理（GUI） |
| weverse | >=0.9.0 | Wevers 定位 API |

### 外部依赖

| 依赖 | 说明 | 安装方式 |
|------|------|----------|
| FFmpeg | 音视频录制转码 | Windows 已内置，Linux/macOS 包管理器 |
| Node.js | JS 签名脚本运行 | Windows 自动安装，Linux/macOS 包管理器 |

---

## 配置文件说明

### config/config.ini（主配置）

| 区块 | 说明 |
|------|------|
| `[录制设置]` | 录制参数（画质/格式/并发/分段/代理/路径） |
| `[推送配置]` | 推送渠道和 API 配置 |
| `[Cookie]` | 各平台登录 Cookie（60+ 平台） |
| `[Authorization]` | 特殊平台认证 Token |
| `[账号密码]` | 须登录的平台（如 SOOP）账号密码 |

### config/URL_config.ini（直播地址）

支持格式：基础 URL / `画质,URL` / `画质,URL,主播:名称`，以 `#` 开头为注释。

---

## 运行方式

| 方式 | 命令 |
|------|------|
| 命令行 | `python main.py` |
| GUI | `python gui.py` |
| Docker | `docker-compose up -d` |
| 安装后 | `douyin-recorder` / `douyin-recorder-gui` |

---

## 录制格式推荐

| 场景 | 格式 | 原因 |
|------|------|------|
| 长时间录制 | TS | 实时写入，断电不易损坏 |
| 短时间录制 | MP4/MKV | 录制完成直接可用 |
| 仅音频录制 | MP3/M4A | 体积小 |
| 网络不稳定 | TS | 支持流式写入 |

---

## 关键设计模式

### 1. 异步并发模式

`asyncio` + `httpx` + `threading.Semaphore(max_request)` 实现三层并发控制。

### 2. 动态并发控制

`adjust_max_request()` 后台线程根据错误率（error_window/error_threshold）自动调整并发数。

### 3. 平台适配器模式

`start_record()` 中通过 URL 模式匹配（`if/elif` 分支）分发到对应平台的 spider/stream 函数。

### 4. FFmpeg 进程管理

注册（`register_ffmpeg_process`）+ 并行清理（`ThreadPoolExecutor`）+ 信号处理（SIGINT/SIGTERM）实现安全生命周期管理。

### 5. 安全退出机制

注册信号处理器 → 清理 FFmpeg 子进程 → `sys.exit(0)`，退出前按 3 级策略终止：优雅退出 → SIGTERM → SIGKILL。

---

## 错误处理机制

- `@trace_error_decorator` 统一捕获 `execjs.ProgramError`（Node.js 缺失）和通用异常
- 错误计数窗口（大小=10，阈值=5），超出后降低并发
- 多级画质降级（OD→BD→UHD→HD→SD→LD）
- 指数退避延迟（error_count > 20 时额外延迟 +60 秒）

---

## 扩展开发指南

添加新平台支持需要改动 5 个文件：

1. `src/spider.py` — 添加获取直播数据的异步函数
2. `src/stream.py` — 添加解析流地址的异步函数
3. `main.py` — 在 `start_record()` 添加 URL 匹配分支
4. `main.py` — 在 `PLATFORM_HOST` 列表添加域名
5. `src/javascript/` — 如需签名脚本，放入此目录

---

## Docker 构建说明

使用多阶段构建：builder 阶段安装 Node.js + Python 依赖，runtime 阶段安装 FFmpeg + 从 builder 复制 Node.js 和 Python 依赖。通过 `docker-compose.yaml` 挂载 `config/`、`downloads/`、`logs/` 目录。

`healthcheck` 使用 `pgrep` 检测 `python main.py` 进程是否存活。资源限制为 2 CPU / 2GB 内存。

---

## 版本历史

| 版本 | 日期 | 关键变更 |
|------|------|----------|
| v4.0.7 | 2025-10-24 | 修复抖音风控、新增 soop.com、修复 bigo |
| v4.0.6 | 2025-01-27 | 新增淘宝/京东/Faceit、重构为异步函数 |
| v4.0.5 | 2024-11-30 | 新增 Shopee/YouTube、自定义脚本 |
| v4.0.4 | 2024-10-30 | 新增 10 个平台、NTFY 推送 |
| v4.0.3 | 2024-10-05 | 邮箱/Bark 推送、分段优化 |
| v4.0.2 | 2024-09-28 | 知乎/CHZZK 直播 |
| v4.0.1 | 2024-09-03 | 双屏录制、音播直播 |
| v4.0.0 | 2024-07-13 | 映客直播 |

---

*本文档由 Code Wiki 自动生成，基于 v4.0.7 版本*