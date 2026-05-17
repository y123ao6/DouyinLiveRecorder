# DouyinLiveRecorder 项目架构文档

## 项目概述

DouyinLiveRecorder（抖音直播录制器）是一款功能强大的开源直播录制工具，基于 Python 和 FFmpeg 开发，支持国内外 60+ 直播平台的实时录制。项目采用模块化架构设计，支持命令行和 GUI 双模式运行，具备循环值守、消息推送、Docker 部署等企业级功能。

**项目地址**：https://github.com/ihmily/DouyinLiveRecorder

**技术栈**：Python 3.10+ | FFmpeg | Loguru | httpx | PyExecJS

---

## 目录结构

```
DouyinLiveRecorder/
├── config/                          # 配置文件目录
│   ├── config.ini                 # 主配置文件（录制设置、推送配置、Cookie 等）
│   └── URL_config.ini            # 直播间地址列表
├── src/                            # 核心源码包
│   ├── __init__.py               # 包初始化（Node.js 环境配置）
│   ├── spider.py                  # 直播数据获取（各平台 API 调用）
│   ├── stream.py                  # 直播流解析（URL 提取、画质选择）
│   ├── room.py                    # 直播间信息（URL 解析、房间 ID 获取）
│   ├── utils.py                   # 工具函数（配置读写、文件操作）
│   ├── logger.py                  # 日志配置（Loguru 集成）
│   ├── proxy.py                   # 代理检测（Windows/Linux 系统代理）
│   ├── ab_sign.py                 # 抖音签名算法（SM3、RC4、AES）
│   ├── initializer.py             # 环境初始化（Node.js 自动安装）
│   ├── weverse_auth.py            # Wevers 认证模块
│   ├── http_clients/             # HTTP 客户端封装
│   │   ├── async_http.py         # 异步 HTTP 请求
│   │   └── sync_http.py          # 同步 HTTP 请求
│   └── javascript/                # JavaScript 签名脚本
│       ├── crypto-js.min.js      # CryptoJS 库
│       ├── x-bogus.js            # 抖音 X-Bogus 签名算法
│       └── ...                    # 其他平台签名脚本
├── downloads/                      # 录制文件保存目录
├── logs/                          # 日志文件目录
├── i18n/                          # 国际化文件
│   ├── zh_CN/                    # 中文翻译
│   └── en/                       # 英文翻译
├── main.py                        # 命令行模式入口
├── gui.pyw                        # GUI 图形界面入口
├── msg_push.py                    # 消息推送模块
├── ffmpeg_install.py              # FFmpeg 安装脚本
├── i18n.py                        # 国际化实现
├── demo.py                        # 调用示例
├── requirements.txt               # Python 依赖
├── pyproject.toml                # Python 项目配置
├── Dockerfile                     # Docker 构建文件
└── docker-compose.yaml           # Docker Compose 配置
```

---

## 整体架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                │
│  ┌─────────────────┐              ┌─────────────────┐            │
│  │   main.py       │              │   gui.pyw       │            │
│  │  (命令行模式)    │              │  (图形界面模式)   │            │
│  └────────┬────────┘              └────────┬────────┘            │
└───────────┼──────────────────────────────┼───────────────────────┘
            │                              │
            ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        核心业务层                                │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                      main.py                             │    │
│  │  • 配置文件解析     • 多线程调度     • FFmpeg 进程管理     │    │
│  │  • 直播状态监控     • 录制流程控制     • 消息推送触发       │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  ┌─────────────┬─────────────┼─────────────┬─────────────┐      │
│  ▼             ▼             ▼             ▼             ▼      │
│ ┌────┐   ┌───────┐   ┌──────────┐  ┌─────────┐   ┌────────┐   │
│ │spider│  │stream │   │ msg_push │  │ utils   │   │logger  │   │
│ └────┘   └───────┘   └──────────┘  └─────────┘   └────────┘   │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        平台适配层                                │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                     spider.py                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │   │
│  │  │ 抖音/TikTok│ │  快手   │ │  虎牙   │ │   B站/斗鱼   │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        基础设施层                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │  HTTP 客户端 │  │  FFmpeg   │  │  Node.js  │  │  配置文件 │  │
│  │  (httpx)   │  │  (录制)    │  │  (签名)    │  │ (ini)    │  │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 数据流向

```
直播间 URL
    │
    ▼
┌─────────────────┐
│  URL 解析与识别   │ ──► 识别直播平台类型
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  spider.py       │ ──► 调用平台 API 获取直播数据
│  (异步 HTTP)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  stream.py       │ ──► 解析流地址、选择画质
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FFmpeg 录制进程  │ ──► 实时录制直播流
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  文件输出        │ ──► TS/MP4/FLV/MKV/MP3 格式
│  (downloads/)   │
└─────────────────┘
```

---

## 核心模块详解

### 1. main.py - 主程序入口

**文件路径**：`/workspace/main.py`

**功能职责**：作为命令行模式的主入口，协调整个录制流程。

**核心变量**：

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `recording` | set | 正在录制的直播间集合 |
| `monitoring` | int | 正在监控的直播间数量 |
| `running_list` | list | 正在运行的 URL 列表 |
| `error_count` | int | 当前错误计数 |
| `max_request` | int | 同时访问网络的线程数 |
| `url_tuples_list` | list | 解析后的 URL 配置列表 |

**核心函数**：

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `start_record()` | url_data: tuple, count_variable: int | None | 启动单个直播间录制 |
| `check_subprocess()` | record_name, record_url, ffmpeg_command, save_type | bool | 监控 FFmpeg 进程 |
| `display_info()` | 无 | None | 显示录制状态信息 |
| `push_message()` | record_name, live_url, content | None | 发送状态通知 |
| `segment_video()` | converts_file_path, segment_save_file_path, segment_format, segment_time | None | 视频分段处理 |
| `converts_mp4()` | converts_file_path, is_original_delete | None | 转换为 MP4 格式 |

**录制流程**（`start_record` 函数）：

1. **URL 识别**：通过 URL 匹配识别直播平台
2. **数据获取**：调用对应平台的 spider 模块获取直播信息
3. **流解析**：调用 stream 模块解析实际流地址
4. **状态检测**：判断直播间是否开播
5. **录制执行**：启动 FFmpeg 进程进行录制
6. **状态推送**：开播/关播时触发消息推送
7. **循环监控**：定时检测直播状态，断播后等待重连

---

### 2. src/spider.py - 直播数据获取模块

**文件路径**：`/workspace/src/spider.py`

**功能职责**：封装各平台直播 API，实现异步 HTTP 请求，统一返回直播数据。

**核心异步函数**：

| 函数名 | 平台 | 说明 |
|--------|------|------|
| `get_douyin_web_stream_data()` | 抖音 Web | 获取抖音网页版直播数据 |
| `get_douyin_app_stream_data()` | 抖音 App | 获取抖音 App 直播数据 |
| `get_tiktok_stream_data()` | TikTok | 获取 TikTok 直播数据 |
| `get_kuaishou_stream_data()` | 快手 | 获取快手直播数据 |
| `get_huya_stream_data()` | 虎牙 | 获取虎牙直播数据 |
| `get_bilibili_room_info()` | B站 | 获取 B 站直播间信息 |
| `get_douyu_info_data()` | 斗鱼 | 获取斗鱼直播信息 |
| `get_yy_stream_data()` | YY | 获取 YY 直播数据 |
| `get_xhs_stream_url()` | 小红书 | 获取小红书直播地址 |
| `get_bigo_stream_url()` | Bigo | 获取 Bigo 直播地址 |
| `get_shopee_stream_url()` | Shopee | 获取 Shopee 直播地址 |
| `get_youtube_stream_url()` | YouTube | 获取 YouTube 直播地址 |

**返回数据格式**（统一）：

```python
{
    "anchor_name": "主播昵称",
    "is_live": True/False,           # 是否正在直播
    "title": "直播标题",              # 可选
    "quality": "原画",                # 可选
    "stream_url": {                   # 直播流地址
        "flv_pull_url": {...},       # FLV 流地址
        "hls_pull_url_map": {...}     # HLS 流地址
    }
}
```

---

### 3. src/stream.py - 直播流解析模块

**文件路径**：`/workspace/src/stream.py`

**功能职责**：解析 spider 返回的原始数据，提取可用的直播流地址，支持画质选择。

**核心函数**：

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `get_douyin_stream_url()` | json_data, video_quality, proxy_addr | dict | 解析抖音直播流 |
| `get_tiktok_stream_url()` | json_data, video_quality, proxy_addr | dict | 解析 TikTok 直播流 |
| `get_kuaishou_stream_url()` | json_data, video_quality | dict | 解析快手直播流 |
| `get_huya_stream_url()` | json_data, video_quality | dict | 解析虎牙直播流 |
| `get_bilibili_stream_url()` | json_data, video_quality, proxy_addr, cookies | dict | 解析 B 站直播流 |
| `get_stream_url()` | json_data, video_quality, url_type, spec | dict | 通用流解析函数 |

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

---

### 4. src/room.py - 直播间信息模块

**文件路径**：`/workspace/src/room.py`

**功能职责**：解析直播间 URL，获取房间 ID、用户 secID 等信息。

**核心函数**：

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `get_sec_user_id()` | url, proxy_addr, headers | tuple | 获取抖音房间 ID 和 secUserID |
| `get_unique_id()` | url, proxy_addr, headers | str | 获取抖音号 |
| `get_live_room_id()` | room_id, sec_user_id, proxy_addr, params, headers | str | 获取直播间 webRid |
| `get_xbogus()` | url, headers | str | 计算 X-Bogus 签名 |

**异常类**：

```python
class UnsupportedUrlError(Exception):
    """不支持的 URL 格式异常"""
    pass
```

---

### 5. src/ab_sign.py - 签名算法模块

**文件路径**：`/workspace/src/ab_sign.py`

**功能职责**：实现抖音 A-Bogus 签名算法，用于绕过风控验证。

**核心算法**：

| 算法 | 说明 |
|------|------|
| SM3 | 国密哈希算法，用于数据摘要 |
| RC4 | 对称加密算法，用于流加密 |
| result_encrypt | 自定义 Base64 编码变体 |
| ab_sign() | 组合以上算法生成签名 |

**核心函数**：

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `ab_sign()` | url_search_params, user_agent | str | 生成 A-Bogus 签名 |
| `rc4_encrypt()` | plaintext, key | str | RC4 加密 |
| `generate_rc4_bb_str()` | url_search_params, user_agent, window_env_str | str | 生成加密字符串 |
| `generate_random_str()` | 无 | str | 生成随机字符串 |

---

### 6. src/utils.py - 工具函数模块

**文件路径**：`/workspace/src/utils.py`

**功能职责**：提供通用工具函数，包括配置读写、文件操作、字符串处理等。

**核心类和函数**：

| 类/函数名 | 说明 |
|-----------|------|
| `Color` | 终端彩色输出类（RED/GREEN/YELLOW/BLUE 等） |
| `trace_error_decorator` | 错误追踪装饰器 |
| `check_md5()` | 计算文件 MD5 值 |
| `read_config_value()` | 读取配置文件 |
| `update_config()` | 更新配置文件 |
| `get_file_paths()` | 递归获取目录文件列表 |
| `remove_emojis()` | 移除文本中的表情符号 |
| `remove_duplicate_lines()` | 移除文件重复行 |
| `check_disk_capacity()` | 检查磁盘剩余空间 |
| `handle_proxy_addr()` | 处理代理地址格式 |

---

### 7. src/logger.py - 日志配置模块

**文件路径**：`/workspace/src/logger.py`

**功能职责**：使用 Loguru 配置日志系统，实现分级存储和彩色输出。

**日志配置**：

| 日志文件 | 级别 | 说明 |
|----------|------|------|
| `streamget.log` | DEBUG+ | 调试信息（排除 INFO） |
| `PlayURL.log` | INFO | 仅记录直播流 URL |

**日志格式**：

```
控制台：<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> - <level>{message}</level>
文件：{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}
```

---

### 8. src/proxy.py - 代理检测模块

**文件路径**：`/workspace/src/proxy.py`

**功能职责**：检测系统代理配置，支持 Windows 注册表和 Linux 环境变量。

**核心类**：

| 类名 | 说明 |
|------|------|
| `ProxyInfo` | 代理信息数据类（frozen dataclass） |
| `ProxyDetector` | 代理检测器 |

**核心方法**：

| 方法名 | 说明 |
|--------|------|
| `is_proxy_enabled()` | 检查代理是否启用 |
| `get_proxy_info()` | 获取代理 IP 和端口 |

---

### 9. src/initializer.py - 环境初始化模块

**文件路径**：`/workspace/src/initializer.py`

**功能职责**：自动检测并安装 Node.js 环境（Windows 平台自动下载安装）。

**核心函数**：

| 函数名 | 说明 |
|--------|------|
| `check_node()` | 检查并初始化 Node.js |
| `check_nodejs_installed()` | 检测 Node.js 是否已安装 |
| `install_nodejs()` | 根据系统自动选择安装方式 |
| `install_nodejs_windows()` | Windows 安装脚本 |
| `install_nodejs_ubuntu()` | Ubuntu 安装脚本 |
| `install_nodejs_centos()` | CentOS 安装脚本 |
| `install_nodejs_mac()` | macOS 安装脚本 |

---

### 10. src/http_clients/ - HTTP 客户端模块

**文件路径**：`/workspace/src/http_clients/`

**async_http.py** - 异步 HTTP 客户端：

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `async_req()` | url, proxy_addr, headers, data, json_data, timeout 等 | str/dict/tuple | 异步 GET/POST 请求 |
| `get_response_status()` | url, proxy_addr, timeout 等 | bool | 检查 URL 可访问性 |

**全局配置**：

```python
_httpx_limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
```

---

### 11. msg_push.py - 消息推送模块

**文件路径**：`/workspace/msg_push.py`

**功能职责**：封装多种消息推送渠道，实现直播状态通知。

**支持的推送渠道**：

| 渠道 | 函数名 | 说明 |
|------|--------|------|
| 钉钉 | `dingtalk()` | 群机器人 Webhook |
| 微信 | `xizhi()` | Server 酱/酷推 |
| 邮箱 | `send_email()` | SMTP 协议 |
| Telegram | `tg_bot()` | Bot API |
| Bark | `bark()` | iOS 通知 |
| NTFY | `ntfy()` | 跨平台通知服务 |
| PushPlus | `pushplus()` | 推送加平台 |

**返回格式**（统一）：

```python
{
    "success": [...成功列表...],
    "error": [...失败列表...]
}
```

---

### 12. gui.pyw - GUI 图形界面

**文件路径**：`/workspace/gui.pyw`

**功能职责**：基于 Tkinter 的图形用户界面，提供可视化操作。

**依赖**：`pystray`, `Pillow`

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

这些脚本通过 `PyExecJS` 在 Python 中执行，用于生成各平台所需的签名参数。

---

## 依赖关系

### Python 依赖

```
requirements.txt
├── requests>=2.28.0           # HTTP 请求库
├── loguru>=0.7.0              # 日志库
├── pycryptodome>=3.15.0       # 加密库
├── distro>=1.8.0               # Linux 发行版检测
├── tqdm>=4.65.0               # 进度条
├── httpx[http2]>=0.25.0        # 异步 HTTP 客户端
├── PyExecJS>=1.5.1            # JavaScript 执行
├── pystray>=0.19.4            # 系统托盘图标
├── Pillow>=10.0.0             # 图像处理
└── weverse>=0.9.0             # Wevers SDK
```

### 外部依赖

| 依赖 | 说明 | 安装方式 |
|------|------|----------|
| FFmpeg | 音视频处理 | Windows 内置，Linux 需安装 |
| Node.js | JavaScript 执行 | Windows 自动安装，其他系统需安装 |

---

## 配置文件说明

### config/config.ini

**录制设置**：

```ini
[录制设置]
language(zh_cn/en) = zh_cn              # 语言设置
直播保存路径(不填则默认) =               # 保存路径
视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频 = ts  # 录制格式
原画|超清|高清|标清|流畅 = 原画           # 画质选择
同一时间访问网络的线程数 = 3              # 并发数
循环时间(秒) = 300                       # 检测间隔
分段录制是否开启 = 是                    # 是否分段
视频分段时间(秒) = 3600                  # 分段时间
录制完成后自动转为mp4格式 = 否            # 自动转码
生成时间字幕文件 = 否                    # SRT 字幕
```

**推送配置**：

```ini
[推送配置]
直播状态推送渠道 =                       # 渠道列表
钉钉推送接口链接 =                       # Webhook URL
微信推送接口链接 =                       # Server 酱 URL
开播推送开启(是/否) = 是                 # 开播通知
关播推送开启(是/否) = 否                 # 关播通知
只推送通知不录制(是/否) = 否              # 仅推送模式
```

**Cookie 配置**：

```ini
[Cookie]
抖音cookie =                            # 抖音 Cookie（必填）
快手cookie =                            # 快手 Cookie
tiktok_cookie =                         # TikTok Cookie
...
```

### config/URL_config.ini

**格式示例**：

```
# 基础格式
https://live.douyin.com/745964462470

# 指定画质（画质,直播间地址）
超清，https://live.douyin.com/745964462470

# 指定主播名（画质,直播间地址,主播:名称）
高清，https://live.bilibili.com/123456，主播: B站主播

# 注释直播间（在地址前加 #）
# https://live.douyin.com/123456789
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
| 短时间录制 | MP4/MKV | 录制完成后直接可用 |
| 仅音频录制 | MP3/M4A | 体积小，便于存储 |
| 网络不稳定 | TS | 支持流式写入 |

---

## 关键设计模式

### 1. 异步并发模式

项目使用 `asyncio` + `httpx` 实现异步 HTTP 请求，配合信号量控制并发数：

```python
semaphore = threading.Semaphore(max_request)

with semaphore:
    json_data = await spider.get_douyin_web_stream_data(...)
```

### 2. 动态并发控制

根据错误率动态调整并发数：

```python
def adjust_max_request():
    while True:
        error_rate = sum(error_window) / len(error_window)
        if error_rate > error_threshold:
            max_request = max(1, max_request - 1)
        elif error_rate < error_threshold / 2:
            max_request += 1
```

### 3. 平台适配器模式

通过 URL 模式匹配分发到对应平台处理器：

```python
if record_url.find("douyin.com/") > -1:
    json_data = await spider.get_douyin_web_stream_data(...)
elif record_url.find("kuaishou.com/") > -1:
    json_data = await spider.get_kuaishou_stream_data(...)
```

### 4. FFmpeg 进程管理

使用信号量注册/注销机制管理进程生命周期：

```python
def register_ffmpeg_process(process):
    with _processes_lock:
        _ffmpeg_processes.append(process)

def cleanup_all_ffmpeg_processes():
    # 并行清理所有进程
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_cleanup_single_ffmpeg_process, proc) 
                   for proc in _ffmpeg_processes]
```

---

## 错误处理机制

### 1. 装饰器追踪

```python
@trace_error_decorator
async def get_douyin_stream_url(json_data, ...):
    ...
```

### 2. 错误计数窗口

```python
error_window = []
error_window_size = 10
error_threshold = 5

with max_request_lock:
    error_count += 1
    error_window.append(1)
```

### 3. 自动重试

- 录制出错后自动重连
- 支持多级画质降级
- 指数退避延迟策略

---

## 安全考虑

1. **签名算法**：抖音 A-Bogus 签名用于绕过风控
2. **Cookie 管理**：支持各平台独立 Cookie 配置
3. **代理支持**：支持 HTTP/SOCKS 代理录制海外平台
4. **信号处理**：安全退出，清理所有子进程

---

## 扩展开发指南

### 添加新平台支持

1. 在 `spider.py` 中添加获取直播数据的函数
2. 在 `stream.py` 中添加解析流地址的函数
3. 在 `main.py` 的 `start_record` 中添加 URL 匹配逻辑
4. 在 `PLATFORM_HOST` 列表中添加域名
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
```

---

## 版本信息

- **当前版本**：v4.0.7
- **Python 要求**：>= 3.10
- **最后更新**：2025-10-24

---

*本文档由 Code Wiki 自动生成*
