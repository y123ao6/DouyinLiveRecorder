# DouyinLiveRecorder 项目架构文档

## 项目概述

**DouyinLiveRecorder** 是一款基于 Python 和 FFmpeg 的开源直播录制工具，支持 **60+ 国内外直播平台**的实时循环值守录制。项目采用模块化架构，支持命令行和 GUI 双模式运行，具备多平台适配、消息推送、Docker 部署等企业级功能。

| 属性 | 值 |
|------|------|
| 当前版本 | v4.0.7 |
| Python 版本 | >= 3.10 |
| 项目地址 | https://github.com/ihmily/DouyinLiveRecorder |
| 许可证 | MIT |

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
│   │   ├── async_http.py              # 异步 HTTP 请求（httpx）
│   │   └── sync_http.py               # 同步 HTTP 请求
│   └── javascript/                    # JavaScript 签名脚本
│       ├── crypto-js.min.js           # CryptoJS 加密库
│       └── x-bogus.js                 # 抖音 X-Bogus 签名算法
├── downloads/                          # 录制文件保存目录
├── logs/                              # 日志文件目录
├── i18n/                              # 国际化文件（中文 / 英文）
├── main.py                            # 命令行模式入口
├── gui.pyw                           # GUI 图形界面入口（现代化深色主题）
├── msg_push.py                        # 消息推送模块
├── ffmpeg_install.py                 # FFmpeg 安装脚本
├── demo.py                           # 调用示例
├── i18n.py                           # 国际化实现
├── requirements.txt                   # Python 依赖清单
├── pyproject.toml                    # Python 项目配置（uv）
├── Dockerfile                        # Docker 构建文件
├── docker-compose.yaml               # Docker Compose 配置
└── StopRecording.vbs                 # Windows 停止录制脚本
```

---

## 整体架构

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                         用户交互层                                 │
│   ┌──────────────────┐          ┌──────────────────────┐         │
│   │   main.py        │          │   gui.pyw            │         │
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
│                         平台适配层                                 │
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

**核心职责**：
- 配置文件的读取、解析与热更新
- 多平台直播流的获取与解析
- FFmpeg 录制进程的管理
- 多线程并发录制控制（Semaphore 限流）
- 错误处理与动态并发调优
- 直播状态消息推送

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
| `url_comments` | list | 被注释掉的 URL 列表 |
| `exit_recording` | bool | 全局退出标志 |

**核心函数**：

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `start_record()` | url_data: tuple, count_variable: int | None | 启动单个直播间录制主循环 |
| `check_subprocess()` | record_name, record_url, ffmpeg_command, save_type, script_command | bool | 监控 FFmpeg 进程状态 |
| `display_info()` | 无 | None | 显示录制状态信息（5秒刷新） |
| `push_message()` | record_name, live_url, content | None | 触发多渠道消息推送 |
| `segment_video()` | converts_file_path, segment_save_file_path, segment_format, segment_time | None | FFmpeg 视频分段 |
| `converts_mp4()` | converts_file_path, is_original_delete | None | 转换为 MP4 格式 |
| `converts_m4a()` | converts_file_path, is_original_delete | None | 提取音频为 M4A |
| `generate_subtitles()` | record_name, ass_filename, sub_format | None | 生成时间字幕线程 |
| `adjust_max_request()` | 无 | None | 后台线程：动态调整并发数 |
| `direct_download_stream()` | source_url, save_path, record_name, live_url, platform | bool | 直接下载 FLV 流 |
| `run_script()` | command: str | None | 执行自定义脚本 |
| `safe_exit()` | signum, frame | None | 信号处理器：安全退出 |
| `register_ffmpeg_process()` | process | None | 注册 FFmpeg 进程 |
| `cleanup_all_ffmpeg_processes()` | 无 | None | 并行清理所有 FFmpeg 进程 |

**录制流程**（`start_record` 函数内层循环）：

```
while True:
    1. 平台识别 → 匹配 if/elif 分支 (60+ 平台)
    2. 异步获取直播数据 (asyncio.run + semaphore)
    3. 解析流地址 (stream.py)
    4. 判断 is_live:
       ├─ False: 打印"等待直播...", 检查关播推送
       └─ True:  构建 FFmpeg 命令 → check_subprocess()
                  ├─ 录制完成: 转码(可选) → 触发脚本(可选)
                  └─ 异常退出: error_count++ → 动态调优
    5. 随机延迟 (delay_default ± 5 秒)
    6. 循环检测
```

**FFmpeg 命令构建策略**：

- 基础参数：`ffmpeg -y -v verbose -rw_timeout 15s -reconnect_delay_max 60`
- 海外平台（TikTok/YouTube 等）：延长超时至 50s
- 分段录制：`segment -segment_time {split_time} -segment_format {format}`
- 音频提取：`-map 0:a -c:a libmplame/aac -ab 320k`
- 录制完成自动转 MP4：`-c:v copy -c:a copy` 或重新编码为 H.264

**动态并发控制**（`adjust_max_request`）：

```
错误窗口(error_window)大小 = 10
错误阈值(error_threshold) = 5

if error_rate > 5:     max_request = max(1, max_request - 1)  # 降速
elif error_rate < 2.5: max_request += 1                        # 提速
```

---

### 2. src/spider.py - 直播数据获取模块

**文件路径**：`/workspace/src/spider.py`（约 1500+ 行）

**核心职责**：封装各平台直播 API，统一使用 `asyncio` + `httpx` 实现异步并发请求。

**核心异步函数**（按平台分组）：

| 函数名 | 平台 | 说明 |
|--------|------|------|
| `get_douyin_web_stream_data()` | 抖音 Web | 抖音网页端 API，支持 A-Bogus 签名 |
| `get_douyin_app_stream_data()` | 抖音 App | 抖音 APP 端接口（备用） |
| `get_tiktok_stream_data()` | TikTok | TikTok 直播 API |
| `get_kuaishou_stream_data()` | 快手 | 快手直播 API |
| `get_huya_stream_data()` | 虎牙 | 虎牙直播 API |
| `get_huya_app_stream_url()` | 虎牙 App | 虎牙 APP 端（高清） |
| `get_bilibili_room_info()` | B站 | 获取 B 站直播间信息 |
| `get_douyu_info_data()` | 斗鱼 | 斗鱼直播 API |
| `get_yy_stream_data()` | YY | YY 直播 API |
| `get_xhs_stream_url()` | 小红书 | 小红书直播 API |
| `get_bigo_stream_url()` | Bigo | Bigo 直播 API |
| `get_sooplive_stream_data()` | SOOP | SOOP 直播（需账号密码） |
| `get_twitchtv_stream_data()` | Twitch | Twitch 直播 API |
| `get_youtube_stream_url()` | YouTube | YouTube 直播 API |
| `get_taobao_stream_url()` | 淘宝 | 淘宝直播 API |
| `get_shopee_stream_url()` | Shopee | Shopee 直播 API |
| `get_faceit_stream_data()` | Faceit | Faceit 直播 API |
| `get_migu_stream_url()` | 咪咕 | 咪咕直播 API |
| `get_play_url_list()` | 通用 | 从 M3U8 播放列表提取所有清晰度 URL |

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

**关键设计**：
- 使用 `trace_error_decorator` 装饰所有异步函数，统一异常处理
- 支持 Cookie 注入，用于需要登录的平台
- 支持代理地址注入（`proxy_addr` 参数）
- 抖音使用 `ab_sign()` 生成 A-Bogus 签名绕过风控

---

### 3. src/stream.py - 直播流解析模块

**文件路径**：`/workspace/src/stream.py`（约 392 行）

**核心职责**：解析 spider 返回的原始数据，提取可用的直播流地址，支持画质选择和带宽排序。

**核心异步函数**：

| 函数名 | 平台 | 说明 |
|--------|------|------|
| `get_douyin_stream_url()` | 抖音 | 解析 FLV/HLS 流，计算质量索引 |
| `get_tiktok_stream_url()` | TikTok | 解析多码率流，按带宽排序 |
| `get_kuaishou_stream_url()` | 快手 | 解析 m3u8/flv URL |
| `get_huya_stream_url()` | 虎牙 | 重新计算 anti-code 签名 |
| `get_douyu_stream_url()` | 斗鱼 | 获取 RTMP 地址 |
| `get_yy_stream_url()` | YY | 获取 CDN 流地址 |
| `get_bilibili_stream_url()` | B站 | 获取 B 站直播流 URL |
| `get_netease_stream_url()` | 网易CC | 解析多清晰度流 |
| `get_stream_url()` | 通用 | 通用流解析（平台无关） |

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

QUALITY_MAPPING_BIT = {
    'OD': 99999, 'BD': 4000, 'UHD': 2000, 'HD': 1000, 'SD': 800, 'LD': 600
}
```

**统一返回格式**：

```python
{
    "anchor_name": "主播昵称",
    "is_live": True / False,
    "title": "直播标题",
    "quality": "OD/BD/UHD/HD/SD/LD",
    "m3u8_url": "...m3u8",     # HLS 流地址
    "flv_url": "...flv",        # FLV 流地址
    "record_url": "...",        # 实际录制使用的地址
}
```

---

### 4. src/room.py - 直播间信息模块

**文件路径**：`/workspace/src/room.py`

**核心职责**：解析直播间 URL，获取房间 ID、用户 secID 等信息。

**核心函数**：

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `get_sec_user_id()` | url, proxy_addr, headers | tuple | 获取抖音房间 webRid 和 secUserID |
| `get_unique_id()` | url, proxy_addr, headers | str | 获取抖音号 |
| `get_live_room_id()` | room_id, sec_user_id, ... | str | 获取直播间 webRid |
| `get_xbogus()` | url, headers | str | 计算 X-Bogus 签名 |

**异常类**：

```python
class UnsupportedUrlError(Exception):
    """不支持的 URL 格式异常"""
    pass
```

---

### 5. src/ab_sign.py - 抖音签名算法模块

**文件路径**：`/workspace/src/ab_sign.py`

**核心职责**：实现抖音 A-Bogus 签名算法（用于绕过风控），组合 SM3（国密哈希）、RC4（流加密）和自定义 Base64 编码。

**核心函数**：

| 函数名 | 说明 |
|--------|------|
| `ab_sign()` | 生成 A-Bogus 签名 |
| `generate_random_string()` | 生成随机字符串 |
| `generate_rc4_bb_str()` | 生成 RC4 加密字符串 |
| `rc4_encrypt()` | RC4 对称加密 |

**签名流程**：SM3 摘要 → RC4 加密 → 自定义 Base64 编码 → 生成最终签名参数

---

### 6. src/utils.py - 工具函数模块

**文件路径**：`/workspace/src/utils.py`

**核心类和函数**：

| 类/函数名 | 说明 |
|-----------|------|
| `Color` | 终端 ANSI 彩色输出（RED/GREEN/YELLOW/BLUE/MAGENTA/CYAN/WHITE） |
| `trace_error_decorator` | 统一异常处理装饰器，自动记录错误行号 |
| `check_md5()` | 计算文件 MD5 值 |
| `dict_to_cookie_str()` | Cookie 字典转字符串 |
| `read_config_value()` | 读取 INI 配置项 |
| `update_config()` | 更新 INI 配置项 |
| `get_file_paths()` | 递归获取目录下所有文件路径 |
| `remove_emojis()` | 正则移除 Unicode 表情符号 |
| `remove_duplicate_lines()` | 移除文件重复行 |
| `check_disk_capacity()` | 检查磁盘剩余空间（GB） |
| `handle_proxy_addr()` | 处理代理地址格式 |

---

### 7. src/logger.py - 日志配置模块

**文件路径**：`/workspace/src/logger.py`

**日志配置**（基于 Loguru）：

| 日志文件 | 级别 | 内容 | 轮转策略 |
|----------|------|------|----------|
| `logs/streamget.log` | DEBUG | 全部日志（排除 INFO） | 300KB 轮转，保留 1 份 |
| `logs/PlayURL.log` | INFO | 直播流 URL | 300KB 轮转，保留 1 份 |

**控制台格式**（彩色）：

```
<green>2025-01-15 10:23:45.678</green> | <level>DEBUG   </level> - <level>正在连接直播流...</level>
```

---

### 8. src/proxy.py - 代理检测模块

**文件路径**：`/workspace/src/proxy.py`

**核心类**：

| 类名 | 说明 |
|------|------|
| `ProxyInfo` | 代理信息数据类（frozen dataclass：ip, port） |
| `ProxyDetector` | 代理检测器 |

**检测策略**：
- Windows：读取注册表 `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings`
- Linux：读取环境变量 `http_proxy` / `https_proxy`

---

### 9. src/initializer.py - 环境初始化模块

**文件路径**：`/workspace/src/initializer.py`

**核心职责**：自动检测并安装 Node.js 环境（Windows 平台自动下载）。

**核心函数**：

| 函数名 | 说明 |
|--------|------|
| `check_node()` | 主入口：检测并初始化 Node.js |
| `check_nodejs_installed()` | 检测 Node.js 是否已安装 |
| `install_nodejs()` | 根据系统自动选择安装方式 |
| `install_nodejs_windows()` | Windows 下载安装脚本 |
| `install_nodejs_ubuntu()` | Ubuntu 安装脚本 |
| `install_nodejs_centos()` | CentOS 安装脚本 |
| `install_nodejs_mac()` | macOS 安装脚本 |

---

### 10. src/http_clients/ - HTTP 客户端模块

**文件路径**：`/workspace/src/http_clients/`

**async_http.py** - 异步 HTTP 客户端：

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `async_req()` | url, proxy_addr, headers, data, json_data, timeout 等 | str / dict / tuple | 异步 GET/POST 请求 |
| `get_response_status()` | url, proxy_addr, timeout, http2 | bool | 检查 URL 可访问性 |

**全局配置**：

```python
_httpx_limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
```

---

### 11. msg_push.py - 消息推送模块

**文件路径**：`/workspace/msg_push.py`

**支持的推送渠道**：

| 渠道 | 函数名 | 说明 |
|------|--------|------|
| 钉钉 | `dingtalk()` | 群机器人 Webhook |
| 微信 | `xizhi()` | Server 酱 / WeChat |
| 邮箱 | `send_email()` | SMTP 协议（支持 SSL） |
| Telegram | `tg_bot()` | Bot API |
| Bark | `bark()` | iOS 通知 |
| NTFY | `ntfy()` | 跨平台通知服务 |
| PushPlus | `pushplus()` | 推送加平台 |

**统一返回格式**：

```python
{
    "success": [成功渠道列表],
    "error": [失败渠道列表]
}
```

**触发时机**：
- `begin_show_push`：开播时推送
- `over_show_push`：关播时推送
- `disable_record`：仅推送模式（不录制）

---

### 12. gui.pyw - GUI 图形界面

**文件路径**：`/workspace/gui.pyw`（约 1172 行）

**设计风格**：现代化深色主题（GitHub Dark 风格），基于 Tkinter 构建。

**核心组件**：

| 组件名 | 说明 |
|--------|------|
| `Theme` | 配色方案类（GitHub Dark 色值） |
| `ModernStyles` | 样式配置（跨平台字体回退、按钮样式） |
| `CardFrame` | 圆角卡片容器 |
| `GradientBanner` | Canvas 绘制的蓝色渐变标题横幅 |
| `StatusIndicator` | Canvas 绘制的状态指示灯（运行=绿/停止=红） |
| `ModernTextWidget` | 圆角边框文本控件（自适应尺寸） |
| `SystemTray` | 系统托盘图标和菜单 |
| `AdvancedSettingsWindow` | config.ini 编辑窗口 |

**性能优化策略**：
- 日志批量写入队列，每 200ms 刷新一次
- 按需调度定时器（日志队列空闲时停止）
- 进程状态通过 `threading.Lock` 线程安全访问
- 配置文件 mtime 缓存避免重复读取

---

## JavaScript 签名脚本

**目录**：`/workspace/src/javascript/`

| 文件名 | 平台 | 说明 |
|--------|------|------|
| `crypto-js.min.js` | 通用 | CryptoJS 加密库 |
| `x-bogus.js` | 抖音 | X-Bogus 签名算法 |
| `taobao-sign.js` | 淘宝 | 淘宝签名算法 |
| `migu.js` | 咪咕 | 咪咕签名脚本 |
| `liveme.js` | LiveMe | LiveMe 签名脚本 |

这些脚本通过 `PyExecJS` 在 Python 中执行，用于生成各平台 API 所需的签名参数。

---

## 依赖关系

### Python 依赖

```
requirements.txt
├── requests>=2.28.0           # HTTP 请求库
├── loguru>=0.7.0              # 日志库
├── pycryptodome>=3.15.0        # 加密库（RC4、SM3）
├── distro>=1.8.0              # Linux 发行版检测
├── tqdm>=4.65.0               # 进度条
├── httpx[http2]>=0.25.0       # 异步 HTTP 客户端
├── PyExecJS>=1.5.1            # JavaScript 执行引擎
├── pystray>=0.19.4            # 系统托盘图标
├── Pillow>=10.0.0             # 图像处理（PIL）
└── weverse>=0.9.0            # Wevers SDK
```

### 外部依赖

| 依赖 | 说明 | 安装方式 |
|------|------|----------|
| **FFmpeg** | 音视频录制和转码 | Windows 自带，Linux/macOS 需安装 |
| **Node.js** | JavaScript 签名执行 | Windows 自动安装，其他系统需预装 |

---

## 配置文件说明

### config/config.ini

**四大配置区块**：

| 区块 | 说明 |
|------|------|
| `[录制设置]` | 录制参数（画质/格式/并发/分段/代理/路径等） |
| `[推送配置]` | 推送渠道和 API 配置 |
| `[Cookie]` | 各平台登录 Cookie（60+ 平台） |
| `[Authorization]` | 特殊平台认证 Token |
| `[账号密码]` | 需登录的平台账号密码 |

**关键配置项**：

```ini
[录制设置]
同一时间访问网络的线程数 = 3          # 并发数
循环时间(秒) = 300                    # 检测间隔
分段录制是否开启 = 否                   # 启用后按 segment_time 分段
视频分段时间(秒) = 1800               # 每段时长
录制完成后自动转为mp4格式 = 否          # 录制结束后转码
生成时间字幕文件 = 否                  # 生成 .srt 字幕
使用代理录制的平台 = tiktok,sooplive...  # 海外平台自动代理
录制空间剩余阈值(gb) = 1.0            # 低于此值退出程序

[推送配置]
直播状态推送渠道 = 微信,钉钉,邮箱        # 可填多个
开播推送开启(是/否) = 是
关播推送开启(是/否) = 否
只推送通知不录制(是/否) = 否             # 监控模式
自定义开播推送内容 = [直播间名称]正在直播中
```

### config/URL_config.ini

**地址格式**（逗号分隔的三元组）：

```
# 基础格式（画质=原画, URL, 主播名=空）
https://live.douyin.com/745964462470

# 指定画质
超清，https://live.douyin.com/745964462470

# 指定画质和主播名
高清，https://live.bilibili.com/123456，主播: B站主播

# 注释直播间（在地址前加 #）
# https://live.douyin.com/123456789

# 支持自定义 m3u8 / flv 地址
https://example.com/stream.m3u8
```

---

## 运行方式

### 方式一：命令行模式

```bash
# 克隆项目
git clone https://github.com/ihmily/DouyinLiveRecorder.git
cd DouyinLiveRecorder

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

### 方式二：GUI 图形界面

```bash
python gui.pyw
```

### 方式三：Docker 部署

```bash
# 快速启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 方式四：打包运行（Windows）

1. 下载 Releases 中的 zip 包
2. 解压后编辑 `config/URL_config.ini`
3. 运行 `DouyinLiveRecorder.exe`

---

## 录制格式推荐

| 场景 | 推荐格式 | 原因 |
|------|----------|------|
| 长时间录制 | TS | 实时写入，断电不易损坏 |
| 短时间录制 | MP4 / MKV | 录制完成直接可用 |
| 仅音频录制 | MP3 / M4A | 体积小，便于存储 |
| 网络不稳定 | TS | 支持流式写入 |

---

## 关键设计模式

### 1. 异步并发模式

使用 `asyncio` + `httpx` 实现异步 HTTP 请求，配合 `threading.Semaphore` 控制并发数：

```python
semaphore = threading.Semaphore(max_request)  # 动态调整

with semaphore:
    json_data = await spider.get_douyin_web_stream_data(...)
    port_info = await stream.get_douyin_stream_url(json_data, ...)
```

### 2. 动态并发控制

根据错误率自动调整并发数：

```python
# adjust_max_request() 后台线程
if error_rate > error_threshold:       # > 5
    max_request = max(1, max_request - 1)
elif error_rate < error_threshold / 2: # < 2.5
    max_request += 1
```

### 3. 平台适配器模式

通过 URL 模式匹配分发到对应平台处理器：

```python
if record_url.find("douyin.com/") > -1:
    json_data = await spider.get_douyin_web_stream_data(...)
elif record_url.find("kuaishou.com/") > -1:
    json_data = await spider.get_kuaishou_stream_data(...)
# ... 60+ 平台分支
```

### 4. FFmpeg 进程管理

使用注册/注销机制和信号量管理进程生命周期，支持多级退出策略（优雅退出 → SIGTERM → SIGKILL）：

```python
# 注册
register_ffmpeg_process(process)

# 并行清理
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(_cleanup_single_ffmpeg_process, proc)
               for proc in _ffmpeg_processes]
```

### 5. 安全退出机制

注册 SIGINT / SIGTERM / SIGBREAK 信号处理器，确保退出时清理所有 FFmpeg 子进程：

```python
signal.signal(signal.SIGINT, safe_exit)
signal.signal(signal.SIGTERM, safe_exit)

def safe_exit(signum, frame):
    cleanup_all_ffmpeg_processes()
    sys.exit(0)
```

---

## 错误处理机制

### 1. 统一装饰器追踪

```python
@trace_error_decorator
async def get_douyin_stream_url(...):
    ...

# 装饰器自动捕获：
# - execjs.ProgramError → Node.js 环境缺失警告
# - 其他异常 → 记录错误类型、消息、函数名、行号
```

### 2. 错误计数窗口

```python
error_window = []  # 大小 = 10
error_threshold = 5  # 阈值

error_window.append(1)
error_count += 1
```

### 3. 自动重试与降级

- 录制出错后自动重连
- 支持多级画质降级（OD → BD → UHD → HD → SD → LD）
- 指数退避延迟策略（`error_count > 20` 时延迟 +60 秒）

---

## 扩展开发指南

### 添加新平台支持

1. 在 `spider.py` 中添加获取直播数据的异步函数
2. 在 `stream.py` 中添加解析流地址的异步函数
3. 在 `main.py` 的 `start_record` 中添加 URL 匹配分支
4. 在 `PLATFORM_HOST` 列表中添加平台域名
5. 如需签名脚本，放在 `src/javascript/` 目录

**示例模板**：

```python
# spider.py
@trace_error_decorator
async def get_newplatform_stream_data(url, proxy_addr=None, cookies=None) -> dict:
    headers = {...}
    json_str = await async_req(url, proxy_addr=proxy_addr, headers=headers)
    # 解析返回数据...
    return {
        "anchor_name": anchor_name,
        "is_live": is_live,
        "play_url_list": [...]
    }

# stream.py
@trace_error_decorator
async def get_newplatform_stream_url(json_data, video_quality=None, ...) -> dict:
    # 解析流地址...
    return {
        "anchor_name": ...,
        "is_live": ...,
        "record_url": ...
    }

# main.py (start_record 函数内)
elif record_url.find("newplatform.com/") > -1:
    platform = '新平台'
    with semaphore:
        json_data = await spider.get_newplatform_stream_data(
            url=record_url, proxy_addr=proxy_address, cookies=cookie)
        port_info = await stream.get_newplatform_stream_url(
            json_data, record_quality, proxy_addr=proxy_address)
```

---

## 版本信息

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v4.0.7 | 2025-10-24 | 修复抖音风控无法获取数据，新增 soop.com 支持 |
| v4.0.6 | 2025-01-27 | 新增淘宝/京东/Faceit 录制，包重构为异步函数 |
| v4.0.5 | 2024-11-30 | 新增 Shopee/YouTube 录制，支持自定义 m3u8/flv 地址 |
| v4.0.4 | 2024-10-30 | 新增嗨秀/VV星球/17Live 等 10 个平台，新增 NTFY 推送 |
| v4.0.3 | 2024-10-05 | 新增邮箱和 Bark 推送，新增直播注释停止录制 |
| v4.0.2 | 2024-09-28 | 新增知乎直播/CHZZK 直播录制 |
| v4.0.1 | 2024-09-03 | 新增抖音双屏录制，新增音播直播录制 |
| v4.0.0 | 2024-07-13 | 新增映客直播录制 |

---

*本文档由 Code Wiki 自动生成，基于 v4.0.7 版本*
