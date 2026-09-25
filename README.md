![video_spider](https://socialify.git.ci/y123ao6/DouyinLiveRecorder/image?font=Inter&forks=1&language=1&owner=1&pattern=Circuit%20Board&stargazers=1&theme=Light)

简体中文&nbsp;&nbsp;|&nbsp;&nbsp;[**English**](README_EN.md)

## 💡 简介

[![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Supported Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg)](https://github.com/y123ao6/DouyinLiveRecorder)
[![GitHub issues](https://img.shields.io/github/issues/y123ao6/DouyinLiveRecorder.svg)](https://github.com/y123ao6/DouyinLiveRecorder/issues)
[![Latest Release](https://img.shields.io/github/v/release/y123ao6/DouyinLiveRecorder)](https://github.com/y123ao6/DouyinLiveRecorder/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/y123ao6/DouyinLiveRecorder/total)](https://github.com/y123ao6/DouyinLiveRecorder/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/y123ao6/DouyinLiveRecorder?style=flat-square)](https://github.com/y123ao6/DouyinLiveRecorder/stargazers)

一款**简易**的可循环值守的直播录制工具，基于 FFmpeg 实现多平台直播源录制，支持自定义配置录制以及直播状态推送。

上游项目：[ihmily/DouyinLiveRecorder](https://github.com/ihmily/DouyinLiveRecorder)

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🎯 **多平台支持** | 支持抖音、TikTok、YouTube、快手、虎牙、斗鱼、B站等 **51 个平台**（对外标称 60+，持续添加中） |
| 🔄 **循环值守** | 自动检测直播状态，开播自动录制，断播自动停止 |
| 🎬 **多种格式** | 支持 TS、MKV、FLV、MP4、MP3、M4A 等格式输出 |
| 🖥️ **三模式运行** | 命令行模式、GUI 图形界面模式、Web 管理面板模式 |
| 📊 **画质监控** | 实时检测各直播间实际画质，画质降级时自动告警 |
| 💬 **弹幕录制** | 抖音 / 斗鱼 / 虎牙 / B站 / TwitchTV 弹幕采集，按分片输出 SRT 字幕，与视频同起同停 |
| 👀 **弹幕监控** | 独立的弹幕实时查看模式（不落盘），GUI 与 Web 面板均可查看 |
| 🏷️ **主播名自动更新** | 主播改名后自动同步 `URL_config.ini` 并重命名录制目录与文件 |
| 📱 **消息推送** | 支持钉钉、微信、邮箱、TG、Bark、NTFY、PushPlus 等推送 |
| 🐳 **Docker 支持** | 支持 Docker 容器化部署，开箱即用 |
| 🌐 **国际化** | 内置简体中文 / English (US) / English (UK) / 繁體中文 四语，GUI 与 Web 面板**免重启热切换** |
| ⚙️ **灵活配置** | 支持按直播间自定义画质、格式、分段录制等，配置改动热加载 |
| 🔐 **Web 安全** | Token 认证、登录爆破限流、路径穿越防护、敏感配置脱敏、未认证写保护 |

## 🚀 快速开始

### 方式一：下载运行包（推荐新手）

1. 进入 [Releases](https://github.com/ihmily/DouyinLiveRecorder/releases) 下载最新发布的 zip 压缩包
2. 解压后，在 `config` 文件夹内的 `URL_config.ini` 中添加直播间地址
3. 运行 `DouyinLiveRecorder.exe` 开始录制

### 方式二：源码运行（推荐开发者）

```bash
# 克隆项目
git clone https://github.com/y123ao6/DouyinLiveRecorder.git
cd DouyinLiveRecorder

# 安装依赖（推荐使用 uv）
uv sync

# 或者使用 pip
pip install -r requirements.txt

# 运行程序
python main.py        # 命令行模式
python gui.py         # GUI 图形界面模式
python web.py         # Web 管理面板模式
```

### 方式三：Docker 运行

```bash
# 命令行录制模式（默认，不占用端口）
docker compose up -d

# Web 管理面板模式（浏览器访问 http://localhost:8000）
# 注意：需先在 config/config.ini 的 [Web] 节设置 web_host = 0.0.0.0，
#       并建议开启 web_auth_enable = true 配置访问密码
docker compose --profile web up -d

# 或本地构建并启动
docker build -t douyin-live-recorder .
docker run -d -v ./config:/app/config -v ./downloads:/app/downloads douyin-live-recorder
```

> 容器内 FFmpeg 与 Node.js 由镜像自带（apt 安装），无需挂载本地 `ffmpeg/`、`node/` 目录；
> `config/`、`downloads/`、`logs/`、`backup_config/` 通过卷挂载持久化。

### 手动安装 ffmpeg（Windows 用户指南）

Windows 版会在启动时自动从官方源 gyan.dev 下载 ffmpeg——**这是唯一的自动路径**（不设镜像兜底，
因为镜像产物没有可核对的官方摘要）。自动安装失败时（多为 gyan.dev 不可达、代理/防火墙拦截，
或 SHA256 基线校验被拒），照下面三步手动安装即可。

1. **下载官方 zip**：<https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip>
   需要自行核对来源时，比对该 zip 的官方摘要文档
   <https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip.sha256>（程序自动安装时校验用的就是这份）。
2. **把解压出来的 `bin` 文件夹放进程序目录并改名为 `ffmpeg`**：

   | 你的运行方式 | 放置结果（务必是这一层） |
   | --- | --- |
   | 下载的运行包（exe） | `DouyinLiveRecorder\ffmpeg\ffmpeg.exe` |
   | 源码运行 / 单文件版脚本 | `<项目根>\ffmpeg\ffmpeg.exe` |

   - **不要**保留成 `ffmpeg\bin\ffmpeg.exe`——程序只把 `ffmpeg\` 这一层目录加入查找路径，不会进子目录寻找。
   - 请把同目录下的 `ffprobe.exe` 一并放入（发布包出包自检要求 ffmpeg 与 ffprobe 都在且可执行）。
3. **验证**：在 `ffmpeg\` 目录里执行 `ffmpeg -version`，能打印版本号即成功。随后重启程序，
   日志（`logs\streamget.log`）中不再出现「未安装 ffmpeg。」即为生效。

也可以改用系统级安装（`winget install Gyan.FFmpeg`、Chocolatey，或任何你信任的构建）把它装进
系统 `PATH`——程序同样按 `PATH` 查找，两种放法等效。

**报错是 SHA256 基线校验被拒时**（日志会写出「请删除 …`_ffmpeg_official*.zip.sha256`… 后重试」）：
删除**程序目录**下匹配 `_ffmpeg_official*.zip.sha256` 的旁路文件，再重启程序。该文件记录的是首次
下载时核对到的摘要，而 gyan.dev 的下载链接是滚动地址——上游发布新构建后旧基线必然失配，删掉它等于
让程序按新构建重新记账。（其校验强度等同于该目录的写权限，不是独立的信任根，故不能替代官方摘要文档。）

> 适用范围：**full 版**发布包已内置 ffmpeg，一般无需任何安装；**lite 版**与单文件版不含，需自动安装
> 或按上文手动安装。macOS / Linux 的自动安装分别走 Homebrew / yum / apt，失败时按各自发行版方式手动安装。
> Apple Silicon 上「包内那份」与「系统原生那份」的取舍见下方常见问题。

## 🎈 已支持平台

**国内站点（37 个）**：抖音 | 快手 | 虎牙 | 斗鱼 | YY | B站 | 小红书 | bigo | blued | 网易CC | 千度热播 | 猫耳FM | Look直播 | TwitCasting | 百度 | 微博 | 酷狗 | 花椒 | 流星 | Acfun | 畅聊 | 映客 | 音播 | 知乎 | 嗨秀 | VV星球 | 17Live | 浪Live | 飘飘 | 六间房 | 乐嗨 | 花猫 | 淘宝 | 京东 | 咪咕 | 连接 | 来秀

**海外站点（14 个）**：TikTok | SOOP(原AfreecaTV) | PandaTV | WinkTV | TTingLive(原Flextv) | PopkonTV | TwitchTV | LiveMe | ShowRoom | CHZZK | Shopee | YouTube | Faceit | Picarto

> 合计 **51 个**平台（对外标称 60+，含持续添加中的平台）。各平台数据获取函数位于 `src/spider.py`，流地址解析位于 `src/stream.py`。

**弹幕录制支持（5 个平台）**：抖音直播 | 斗鱼直播 | 虎牙直播 | B站直播 | TwitchTV

**实际画质回采与降级告警（7 个平台）**：抖音 | TikTok | 快手 | 虎牙 | 斗鱼 | B站 | 网易CC

## 📁 项目结构

```
DouyinLiveRecorder/
├── config/                     # 配置文件目录
│   ├── config.ini             # 主配置文件
│   └── URL_config.ini         # 直播间地址列表
├── src/                        # 核心源码包
│   ├── __init__.py             # 包初始化 + Node.js 环境配置 + 弹幕平台注册表/工厂
│   ├── spider.py              # 直播流地址解析（60+ 平台，已抽离弹幕逻辑）
│   ├── stream.py              # 直播流录制编排（ffmpeg 命令/分段/格式）
│   ├── stream_select.py       # 流地址选源/可达性校验/探针退避
│   ├── scheduler.py           # 并发调度中枢（自适应容量 + 按平台熔断）
│   ├── room.py                # 直播间信息解析
│   ├── utils.py               # 工具函数库
│   ├── logger.py              # Loguru 日志配置
│   ├── proxy.py               # 代理检测
│   ├── ab_sign.py             # 抖音 A-Bogus 签名
│   ├── ttwid.py               # 抖音访客 ttwid 获取/缓存
│   ├── node_install.py        # Node.js 自动安装/初始化
│   ├── ffmpeg_install.py      # FFmpeg 安装脚本
│   ├── ffmpeg_master_download.py  # FFmpeg master 构建（按平台拉取并校验）
│   ├── ffmpeg_proc.py         # ffmpeg 子进程管理（抽离自 main.py）
│   ├── video_postprocess.py   # 录制后处理（转封装/转码）
│   ├── notify.py              # 直播状态消息推送（抽离自 main.py）
│   ├── recorder_status.py     # 录制状态跟踪（抽离自 main.py）
│   ├── config_io.py           # 配置读写/数值转换/备份（抽离自 main.py）
│   ├── config_bool.py         # 布尔配置解析（是/否 与 true/false/1/0/yes/no 等价，零依赖）
│   ├── cookie_cache.py        # 访客 Cookie 进程级共享缓存
│   ├── log_archive.py         # 运行日志归档（停止录制流程收尾：四日志按时间戳改名）
│   ├── http_config.py          # HTTP 客户端共享配置（SSL 验证开关）
│   ├── async_http.py          # 异步 HTTP 客户端 (httpx)
│   ├── sync_http.py           # 同步 HTTP 客户端
│   ├── web_api.py             # Web 管理面板 FastAPI 应用
│   ├── web_config.py          # Web 面板配置读写
│   ├── web_tray.py            # Web 模式系统托盘（最小化到托盘）
│   ├── base.py               # 弹幕采集基类（DanmakuBase / DanmakuMessage）
│   ├── collector.py           # 弹幕采集器（线程桥接主流程）
│   ├── danmaku_monitor.py     # 弹幕监控枢纽（DanmakuMonitorHub）
│   ├── srt_writer.py         # 弹幕时间字幕（SRT）写入
│   ├── ws_client.py          # WebSocket 传输层（弹幕直连、proxy=None）
│   ├── platforms/            # 弹幕平台实现（按平台标识经工厂注册）
│   │   ├── douyin.py         # 抖音弹幕（protobuf + _tars 心跳）
│   │   ├── douyu.py          # 斗鱼弹幕（STT 协议）
│   │   ├── huya.py           # 虎牙弹幕（WSP 协议）
│   │   ├── bilibili.py       # B站弹幕（WebSocket）
│   │   ├── twitch.py         # Twitch 弹幕（IRC/WS）
│   │   ├── _tars.py          # TARS 私有协议编解码
│   │   └── _xbogus.py        # X-Bogus 签名
│   ├── proto/                # 抖音弹幕 protobuf 定义
│   │   ├── douyin.proto      # protoc 源定义
│   │   ├── douyin_pb2.py      # protoc 生成（DO NOT EDIT）
│   │   └── douyin_pb2.pyi     # 类型存根
│   └── javascript/            # JavaScript 签名脚本
│       ├── crypto-js.min.js
│       ├── x-bogus.js
│       ├── haixiu.js
│       ├── liveme.js
│       └── migu.js
├── web/                        # Web 管理面板前端
│   ├── index.html              # 单页应用入口
│   ├── app.js                  # 前端逻辑（API、SSE、渲染）
│   └── style.css               # 样式表（主题、响应式）
├── typings/                    # 第三方库类型存根（静态检查用）
│   ├── customtkinter/          # customtkinter 存根
│   ├── execjs/                 # PyExecJS 存根
│   └── pystray/                # pystray 存根
├── scripts/                    # 工程辅助脚本
│   ├── smoke_test.py           # 通用 Web/接口冒烟测试（零依赖，配置驱动）
│   ├── smoke_web.json          # 冒烟测试示例用例（探活 Web 面板）
│   ├── compile_po.py           # .po → .mo 编译与同步校验（--check）
│   ├── check_coverage.py       # 逐模块覆盖率门禁（CI 使用）
│   ├── check_version.py        # 版本号「单一事实源」动态化校验
│   └── sync_version.py         # 版本号同步辅助
├── downloads/                  # 录制文件保存目录（运行时生成）
├── logs/                       # 日志文件目录（运行时生成，含 danmaku_monitor.jsonl）
├── i18n/                       # 国际化翻译目录（多语言多格式）
│   ├── zh_CN/LC_MESSAGES/      # 简体中文（gettext）
│   │   ├── zh_CN.po           # 中文翻译源（601 条）
│   │   └── zh_CN.mo           # 编译后翻译（运行时必需，随仓库分发）
│   ├── en_US.json              # English (US)（JSON 格式目录）
│   ├── en_GB.json              # English (UK)（英式拼写变体）
│   └── zh_TW.yaml              # 繁體中文（YAML 格式目录，需 PyYAML）
├── ffmpeg/                     # FFmpeg 目录（Windows）
├── node/                       # Node.js 目录（Windows）
├── main.py                     # 命令行入口
├── gui.py                      # GUI 图形界面入口
├── web.py                      # Web 管理面板入口
├── index.html                  # M3U8 视频播放器（独立工具页）
├── msg_push.py                 # 消息推送模块
├── i18n.py                     # 国际化实现
├── build_exe.py                # PyInstaller 打包脚本（CLI/GUI/Web 三入口）
├── requirements.txt            # Python 依赖
├── pyproject.toml             # Python 项目配置
├── Dockerfile                  # Docker 构建文件（多阶段）
├── docker-compose.yaml         # Docker Compose（recorder/web/gui 三服务）
├── .dockerignore               # Docker 构建上下文排除
├── .gitignore                  # Git 排除
├── StopRecording.vbs          # Windows 停止录制脚本
├── CODE_WIKI.md               # 项目架构文档
└── README.md                   # 项目说明文档
```

## ⚙️ 配置说明

### 基础配置 (config/config.ini)

```ini
[录制设置]
# 界面语言：zh_CN | en_US | en_GB | zh_TW（留空跟随系统语言；值支持 zh_cn/zh-CN/en/en-GB/zh-Hant 等写法，自动归一；对应语言文件缺失时回退 en_US）
language = zh_CN
# 是否跳过代理检测(是/否)
是否跳过代理检测(是/否) = 是
# 是否启用日志文件(是/否)
是否启用日志文件(是/否) = 是
# 直播保存路径(不填则默认 downloads/)
直播保存路径(不填则默认) =
# 主播改名时自动更新 URL_config.ini 并同步重命名录制目录/文件（默认 是）
是否自动更新主播名(是/否) = 是
# 保存文件夹是否以作者区分
保存文件夹是否以作者区分 = 是
# 保存文件夹是否以时间区分
保存文件夹是否以时间区分 = 否
# 保存文件夹是否以标题区分
保存文件夹是否以标题区分 = 否
# 保存文件名是否包含标题
保存文件名是否包含标题 = 否
# 是否去除名称中的表情符号
是否去除名称中的表情符号 = 是
# 视频保存格式 ts|mkv|flv|mp4|mp3音频|m4a音频
视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频 = ts
# 录制画质 原画|超清|高清|标清|流畅
原画|超清|高清|标清|流畅 = 原画
# 自定义画质选项(逗号分隔) - 用户自选画质子集，留空或全部非法时回退引擎内置全集（默认 空）；
# WEB 端增删画质 / GUI 端「切换画质」写回本项，选非默认画质按「画质,直播间地址」写回 config/URL_config.ini
自定义画质选项(逗号分隔) =
# 是否使用代理ip(是/否)
是否使用代理ip(是/否) = 否
# 代理地址
代理地址 =
# 同一时间访问网络的线程数
同一时间访问网络的线程数 = 3
# 最大同时录制数 - 全局并发录制上限，0 为不限制（默认 0）；改值后下一轮检测循环生效
最大同时录制数(0为不限制) = 0
# 循环时间(秒) - 直播状态检测间隔（默认 120）
循环时间(秒) = 120
# 排队读取网址时间(秒)
排队读取网址时间(秒) = 0
# 是否显示循环秒数
是否显示循环秒数 = 否
# 是否显示直播源地址
是否显示直播源地址 = 否
# 分段录制是否开启
分段录制是否开启 = 是
# 是否启用HLS采集(是/否) - 关闭则只走 FLV 等非 HLS 候选
是否启用HLS采集(是/否) = 是
# HLS采集排除平台(逗号分隔) - 命中平台无视「是否启用HLS采集」配置、恒按 FLV 采集
# （平台名须与日志/配置中显示的完全一致，如：斗鱼直播,虎牙直播；留空不排除任何平台）
HLS采集排除平台(逗号分隔) =
# 是否启用https录制 - 已整合原「是否强制启用https录制」与「是否禁用SSL证书验证(是/否)」：
# 开启 = 流地址以 https 拉流并跳过 SSL 证书校验；关闭 = 流地址以 http 拉流并恢复默认证书校验
# （旧键「是否强制启用https录制」的值会自动迁移继承；TikTok/YouTube 等 https-only 海外平台在关闭时保持原样）
是否启用https录制 = 否
# 禁用SSL证书验证的平台(逗号分隔) - 仅在「是否启用https录制 = 否」（http 模式、需证书校验）时生效。
# FFmpeg 9.0 起 TLS 证书验证默认开启，证书异常平台需在此豁免；启动时会自动追加必需平台
# （虎牙直播 / B站直播），只追加不移除用户手填项
禁用SSL证书验证的平台(逗号分隔) = 虎牙直播,B站直播
# 录制空间剩余阈值(gb)
录制空间剩余阈值(gb) = 1.0
# 视频分段时间(秒)（默认 1800）
视频分段时间(秒) = 1800
# 录制完成后自动转为mp4格式
录制完成后自动转为mp4格式 = 否
# mp4格式重新编码为h264
mp4格式重新编码为h264 = 否
# 追加格式后删除原文件
追加格式后删除原文件 = 是
# 生成时间字幕文件
生成时间字幕文件 = 否
# 是否录制完成后执行自定义脚本
是否录制完成后执行自定义脚本 = 否
# 自定义脚本执行命令
自定义脚本执行命令 =
# 使用代理录制的平台(逗号分隔)
使用代理录制的平台(逗号分隔) = tiktok, sooplive, pandalive, winktv, flextv, popkontv, twitch, liveme, showroom, chzzk, shopee, shp, youtu, faceit
# 额外使用代理录制的平台(逗号分隔)
额外使用代理录制的平台(逗号分隔) =
# 是否录制弹幕(是/否) - 开启后弹幕落为 SRT 字幕文件，与视频录制同起同停
是否录制弹幕(是/否) = 否
# 是否弹幕监控(是/否) - 仅实时查看弹幕、不写 SRT（与弹幕录制解耦，可单独开启）
是否弹幕监控(是/否) = 否
# 弹幕分片时长(秒) - SRT 分片粒度，建议与「视频分段时间(秒)」一致
弹幕分片时长(秒) = 1800
# 弹幕录制平台(逗号分隔) - 目前支持的 5 个平台
弹幕录制平台(逗号分隔) = 斗鱼直播,B站直播,虎牙直播,抖音直播,TwitchTV
```

### 推送配置 (config/config.ini)

```ini
[推送配置]
# 可选微信|钉钉|tg|邮箱|bark|ntfy|pushplus 可填多个
直播状态推送渠道 =
钉钉推送接口链接 =
微信推送接口链接 =
bark推送接口链接 =
bark推送中断级别 = active
bark推送铃声 =
钉钉通知@对象(填手机号) =
钉钉通知@全体(是/否) = 否
tgapi令牌 =
tg聊天id(个人或者群组id) =
smtp邮件服务器 =
是否使用SMTP服务SSL加密(是/否) =
SMTP邮件服务器端口 =
邮箱登录账号 =
发件人密码(授权码) =
发件人邮箱 =
发件人显示昵称 =
收件人邮箱 =
ntfy推送地址 = https://ntfy.sh/xxxx
ntfy推送标签 = tada
ntfy推送邮箱 =
pushplus推送token =
自定义推送标题 =
自定义开播推送内容 =
自定义关播推送内容 =
只推送通知不录制(是/否) = 否
直播推送检测频率(秒) = 1800
开播推送开启(是/否) = 是
关播推送开启(是/否) = 否
```

### Cookie 配置 (config/config.ini)

```ini
[Cookie]
# 录制抖音必填：请填入从浏览器 live.douyin.com 复制的有效 cookie（至少包含 ttwid）
# 留空将自动尝试获取访客 ttwid（可能触发风控，建议填写）
抖音cookie =
# 单独指定抖音 ttwid（留空则由 src/ttwid.py 自动获取并进程级缓存）
ttwid =
# 小红书 app 端接口的会话 sid（xy-common-params 头），留空则用内置缺省（可能已过期）
# 优先级：环境变量 XHS_SESSION_SID > 本键 > 内置缺省
xhs_session_sid =
快手cookie =
tiktok_cookie =
虎牙cookie =
斗鱼cookie =
yy_cookie =
b站cookie =
小红书cookie =
bigo_cookie =
# ... 共 51 个平台 cookie 键，其余详见 config.ini
```

> 访客类 cookie（抖音 ttwid、快手 did 等）由 `src/cookie_cache.py` 以「归一化网址 + 代理」为 key 做进程级共享缓存（默认 30 分钟 TTL），多直播间并发时不会重复拉取触发风控。

### 授权配置 (config/config.ini)

```ini
[Authorization]
# PopkonTV 登录后取得的 token（由账号密码自动登录后写回）
popkontv_token =
```

### 账号密码配置 (config/config.ini)

```ini
[账号密码]
sooplive账号 =
sooplive密码 =
flextv账号 =
flextv密码 =
popkontv账号 =
partner_code = P-00001
popkontv密码 =
twitcasting账号类型 = normal
twitcasting账号 =
twitcasting密码 =
```

### Web 管理面板配置 (config/config.ini)

```ini
[Web]
# Web 管理面板监听地址
web_host = 0.0.0.0
# Web 管理面板端口
web_port = 8000
# 是否启用密码登录（true/false）
web_auth_enable = false
# 访问密码（启用认证时必填）
web_password =
# token 有效期（秒）
web_token_expiry = 86400
# 是否显示控制台窗口（false 时后台运行，日志写入 logs/web_console.log）
web_show_console = true
# 控制台最小化到系统托盘（而非任务栏），仅 Windows 生效；
# 关闭按钮会被禁用，退出请使用托盘图标的「退出程序」
web_minimize_to_tray = true
# 受信任的反向代理来源（逗号分隔）。留空时不解析 X-Forwarded-For；
# 置于 Nginx/Caddy 之后时填入代理 IP，登录限流才能取到真实客户端 IP
web_trusted_proxy =
# 允许的 Host / Origin 白名单（逗号分隔）。仅在把 web_host 绑到 0.0.0.0/:: 且通过域名访问时需要；
# 未列出的多级域名 Host 会被拒绝，用于阻断 DNS 重绑定（attacker.tld → 127.0.0.1）
web_allowed_hosts =
```

> `web_host` 在仓库默认配置中为 `127.0.0.1`（仅本机可访问）。Docker 或需局域网/公网访问时改为 `0.0.0.0`，并务必同时开启 `web_auth_enable` 与 `web_password`。

### 直播间配置 (config/URL_config.ini)

抖音支持以下 5 种直播间/主页地址格式（其余平台格式见下方各平台示例）：

```
# 1) 网页端主播直播间（数字房间号）
https://live.douyin.com/745964462470

# 2) app端主播直播间（分享短链）
https://v.douyin.com/iQFeBnt/

# 3) 抖音号拼接（https://live.douyin.com/ + 抖音号，支持 VR 直播录制）
https://live.douyin.com/yall1102

# 4) app端主播主页（分享短链）
https://v.douyin.com/CeiU5cbX

# 5) 网页端主播主页（用户页地址）
https://www.douyin.com/user/MS4wLjABAAAA3kr2yA4aRD-sjf9cx8xkOH8Di3RjktpKcAvqIetpsF0
```

> 说明：
> - 格式 1/3/5 走网页端接口（支持 VR 直播）；格式 2/4 走 app 端接口
> - 格式 5（网页端主播主页 `www.douyin.com/user/<sec_uid>`）会直接从地址提取 `sec_user_id` 并解析出抖音号，按直播间地址走网页端接口录制，无需经过 app 端探测
> - 格式 4（app 端主页）等短链形态会先探测直播间地址，失败则自动回退到抖音号解析、再走网页端接口录制

```ini
# 指定画质（画质,直播间地址）
超清，https://live.douyin.com/745964462470

# 指定画质和主播名（画质,直播间地址,主播:名称）
高清，https://live.bilibili.com/123456，主播: B站主播

# 注释直播间（在地址前加 #）
# https://live.douyin.com/123456789
```

### 环境变量配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `PYTHONUNBUFFERED` | 实时输出日志 | `1` |
| `PYTHONDONTWRITEBYTECODE` | 不生成 .pyc 文件 | `1` |
| `PYTHONIOENCODING` | Python 输出编码 | `utf-8` |
| `TZ` | 时区设置 | `Asia/Shanghai` |
| `TERM` | 终端类型 | `xterm-256color` |

## 🎬 使用说明

### 命令行模式

```bash
python main.py
```

### GUI 图形界面模式

```bash
python gui.py
```

GUI 功能（侧边导航 5 页）：
- 📊 控制台 - 录制状态总览、启停控制
- 🎯 画质监控 - 实时检测各直播间实际画质是否与设置一致
- 💬 弹幕监控 - 实时查看各房间弹幕流，支持按房间/类型过滤
- 📝 URL 配置 - 直播间地址管理
- 📋 运行日志 - 子进程日志查看

侧边栏另提供**外观**（浅色/深色/跟随系统）与**语言 Language**（简体中文 / English (US) / English (UK) / 繁體中文）选择器，切换语言即时生效并写回 `config.ini`，无需重启。

系统托盘图标支持最小化到托盘后台运行。

### Web 管理面板模式

```bash
python web.py
```

启动后浏览器访问 `http://localhost:8000`。

功能：
- **仪表盘**：实时查看监测/录制数、错误数、磁盘剩余、录制中列表、日志流（SSE 推送）
- **直播间管理**：在线增删改查直播间地址、启用/禁用（自动热加载到录制主循环）
- **配置编辑**：在线编辑 config.ini 各项（录制设置/推送/Cookie 等），敏感配置项脱敏
- **文件浏览**：浏览 downloads 目录并下载录制文件
- **实际画质展示**：录制表格显示"设置画质/实际画质"，降级时标红高亮
- **弹幕查看**：读取弹幕监控枢纽快照，实时展示各房间弹幕事件
- **语言切换**：顶栏语言选择器，四语即时切换（写回配置并热切换进程内翻译，无需重启）

主要 API 路由（均需 Token，认证关闭时除外）：

| 路由 | 方法 | 功能 |
|------|------|------|
| `/api/login` | POST | 密码登录，返回 Token |
| `/api/status` | GET | 录制状态（含实际画质） |
| `/api/status/stream` | GET | 录制状态 SSE 流 |
| `/api/rooms` | GET/POST/PUT/DELETE | 直播间增删改查 |
| `/api/rooms/toggle` | POST | 启用 / 禁用直播间 |
| `/api/config` | GET/PUT | 读取 / 修改配置 |
| `/api/language` | GET/PUT | 查询 / 切换界面语言 |
| `/api/files`、`/api/files/download` | GET | 录制文件浏览与下载 |
| `/api/logs`、`/api/logs/stream` | GET | 日志查询 / SSE 实时推送 |
| `/api/danmaku` | GET | 弹幕监控快照 |

Web 模式与命令行模式共用同一录制引擎与配置文件，直播间地址的增删改会自动被录制主循环热加载。

后台运行模式：将 `web_show_console` 设为 `false`，Windows 下会隐藏控制台窗口，日志写入 `logs/web_console.log`，程序完全后台运行。

Windows 下控制台默认「最小化到系统托盘」（`web_minimize_to_tray = true`）：点击最小化后窗口不在任务栏显示，而是收起到系统托盘，双击托盘图标即可恢复；标题栏关闭按钮已禁用，需从托盘图标菜单的「退出程序」退出。

> ⚠️ **安全提示**：默认监听 0.0.0.0 且未启用认证，公网/局域网部署请务必开启 `web_auth_enable` 并设置强密码，或将 `web_host` 改为 `127.0.0.1`。

### 录制格式推荐

- **长时间录制**：推荐使用 `ts` 格式，实时写入，断电不易损坏
- **短时间录制**：推荐使用 `mp4` 或 `mkv` 格式，录制完成后直接可用
- **仅音频录制**：推荐使用 `mp3` 或 `m4a` 格式

### 画质说明

| 画质代码 | 中文名 | 说明 |
|---------|--------|------|
| OD | 原画 | Original Definition，最高画质 |
| BD | 蓝光 | Blu-ray，超高清 |
| UHD | 超清 | Ultra HD |
| HD | 高清 | High Definition |
| SD | 标清 | Standard Definition |
| LD | 流畅 | Low Definition，最低画质 |

支持平台：抖音、TikTok、快手、虎牙、斗鱼、B站、网易CC。当平台实际下发画质低于设置画质时，会自动告警并标记。

### 采集方式选择（HLS/FLV）

录制拉流源在 HLS（m3u8，逐段拉取）与 FLV（单条长连接）之间自动选择：默认优先 HLS、校验不可达时按序回退 FLV，最后兜底 `record_url`。由两个配置项共同控制：

| 配置项 | 作用 |
|--------|------|
| `是否启用HLS采集(是/否)` | 全局开关：开启（默认）时优先使用 HLS 源，不可达或源不存在时回退 FLV；关闭则所有平台只走 FLV 等非 HLS 候选 |
| `HLS采集排除平台(逗号分隔)` | 平台级排除列表：命中平台**无视全局开关、恒按 FLV 采集**（等效于仅对该平台关闭 HLS 采集，HLS 源不参与候选与回退） |

- **适用场景**：整体偏好 HLS 录制（HLS 逐段拉取免疫单条长连接被 CDN 掐断），但个别平台的 HLS 源不稳定或被风控，希望仅该平台强制走 FLV 时，将其加入排除列表即可——无需为此关闭全局 HLS 开关
- **填写格式**：平台名须与日志/配置文件中显示的**完全一致**（如 `斗鱼直播`，不能简写为 `斗鱼`）；多个平台逗号分隔（中英文逗号均可），如 `斗鱼直播,虎牙直播`；留空（默认）不排除任何平台，行为与旧版本完全一致
- **优先级语义**：排除列表优先于全局开关——即使「是否启用HLS采集(是/否) = 是」，命中平台也只走 FLV；列表外平台不受任何影响，仍按全局配置 HLS 优先
- **边界行为**：排除平台若解析结果仅有 HLS 源且无 FLV/record_url 可回退，本轮放弃录制并输出告警（日志会提示「可将该平台移出排除列表恢复 HLS 采集」）；h265 编码的 FLV 源不再触发切换 HLS（h265 FLV 录制自动改存 TS 格式的逻辑不受影响）
- **热更新**：主循环每轮重读配置，修改保存后无需重启程序，下一轮监测即生效

### 弹幕录制与弹幕监控

弹幕功能由两个**相互解耦**的开关控制，可单独或同时开启：

| 配置项 | 作用 |
|--------|------|
| `是否录制弹幕(是/否)` | 弹幕落盘为 SRT 字幕文件，与视频录制同起同停 |
| `是否弹幕监控(是/否)` | 仅实时查看弹幕，不写 SRT（GUI「弹幕监控」页 / Web `/api/danmaku`） |
| `弹幕分片时长(秒)` | SRT 分片粒度，建议与「视频分段时间(秒)」一致 |
| `弹幕录制平台(逗号分隔)` | 启用弹幕的平台白名单 |

- **支持平台（5 个）**：抖音直播、斗鱼直播、虎牙直播、B站直播、TwitchTV
- **输出文件**：SRT 与视频分片一一对应，命名为 `{基础名}_{分片序号:03d}.srt`（如 `_000.srt` 对应 `_000.ts`）；未分段时为 `{基础名}.srt`。时间轴以单调时钟为基准，与 ffmpeg `segment -reset_timestamps` 的 PTS 对齐，可直接被播放器加载
- **弹幕连接直连**：弹幕 WebSocket 显式不跟随系统代理，避免 SOCKS 代理环境下连接即断
- **监控边车日志**：弹幕监控事件同时写入 `logs/danmaku_monitor.jsonl`（5MB 轮转）
- 抖音弹幕在 Cookie 为空时会自动获取访客 ttwid；B站弹幕会自动获取真实 buvid（登录 cookie → spi 接口 → 首页 Set-Cookie → 随机兜底）

### 主播名自动更新

开启 `是否自动更新主播名(是/否)`（默认「是」）后，程序在每轮解析到最新主播名时，若与 `URL_config.ini` 中记录的名称不同，会自动完成两件事：

1. **重命名文件系统**：`{保存路径}/{平台}/{旧主播名}` → 新主播名目录；递归重命名目录树内所有以 `{旧名}_` 开头的录制产物（TS / FLV / SRT / 字幕）及以 `_{旧名}` 结尾的标题目录；若新名目录已存在则逐项合并移入（兼容主播改回曾用名）
2. **回写配置文件**：按 URL 段级精确匹配只替换该行的主播名字段，完整保留画质段、`#` 注释前缀与行尾换行风格；操作幂等

安全约束：

- 检测点位于「解析直播数据之后、录制启动之前」，此时该线程必然不在录制中，天然避开 ffmpeg 文件占用窗口
- **先文件系统、后配置文件，两者全部成功才切换本轮使用名**；任一失败则保持旧名并在下轮轮询自动重试
- 个别文件被后台转码/播放器占用时仅告警跳过，不阻塞整体
- 自动跳过自定义流地址（其主播名含每轮随机 UUID）与清洗后为空白的昵称
- 关闭该开关即保持手动名称不变

### 多语言与界面切换

内置四套翻译目录，加载时按 `gettext .mo → <lang>.json → <lang>.yaml` 依次探测：

| 语言码 | 显示名 | 目录文件 |
|--------|--------|----------|
| `zh_CN` | 简体中文 | `i18n/zh_CN/LC_MESSAGES/zh_CN.mo` |
| `en_US` | English (US) | `i18n/en_US.json` |
| `en_GB` | English (UK) | `i18n/en_GB.json` |
| `zh_TW` | 繁體中文 | `i18n/zh_TW.yaml` |

- 配置键 `language`：留空跟随系统语言；取值支持 `zh_cn` / `zh-CN` / `en` / `en-US` / `en-GB` / `zh-Hant` / `zh_CN.UTF-8` 等写法，自动归一化到规范语言码；键值不可识别或对应语言文件缺失时回退 `en_US`
- **热切换**：GUI 侧边栏语言选择器、Web 面板顶栏语言选择器、直接编辑 `config.ini` 三种途径均可切换；命令行主循环每轮检测配置变化并即时重载翻译，**无需重启进程**（录制中的 ffmpeg 子进程不受影响）
- 翻译不再依赖 `LANG` / `LANGUAGE` 环境变量（Windows 普遍未设置）
- `zh_TW.yaml` 需要 `PyYAML`；缺失时仅损失该语言，其余格式不受影响

### 停止录制

- **Windows**：执行 `StopRecording.vbs` 或在命令行按 `Ctrl+C`
- **Linux/macOS**：在命令行按 `Ctrl+C`
- **Docker**：执行 `docker-compose stop`

### 注意事项

1. 如需录制 TikTok、SOOP(原AfreecaTV) 等海外平台，请在配置中开启代理
2. 长时间挂机建议将循环时间设置长一些（如 60 秒），避免请求频繁被封 IP
3. 直播结束后会自动保存文件，无需手动停止
4. 如遇录制的视频文件损坏，建议使用 `ts` 格式录制
5. 录制抖音需要填写有效的 cookie（至少包含 ttwid），否则可能触发风控
6. 部分平台需要 Node.js 环境运行 JavaScript 签名脚本，Windows 下会自动安装

## 🐋 Docker 部署

### 前置要求

- 已安装 [Docker](https://docs.docker.com/get-docker/)
- 已安装 [Docker Compose](https://docs.docker.com/compose/install/)

### 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/y123ao6/DouyinLiveRecorder.git
cd DouyinLiveRecorder

# 2. 编辑配置文件
# 在 config/URL_config.ini 中添加直播间地址

# 3. 启动容器（默认命令行录制模式）
docker compose up -d

# 4. 查看日志
docker compose logs -f
```

### 切换运行模式

`docker-compose.yaml` 已内置三个服务（recorder / web / gui），通过 profile 切换，无需修改文件：

```bash
# 命令行录制模式（默认，不占用端口）
docker compose up -d

# Web 管理面板模式（映射 8000 端口，浏览器访问 http://localhost:8000）
docker compose --profile web up -d

# GUI 模式（需 X11 显示环境，先在宿主机执行 xhost +local:）
docker compose --profile gui up -d
```

> ⚠️ Web 模式注意：`web.py` 默认监听 `127.0.0.1`，容器内必须在 `config/config.ini`
> 的 `[Web]` 节设置 `web_host = 0.0.0.0` 才能从宿主机访问；同时建议开启
> `web_auth_enable = true` 并配置 `web_password`。

### 数据挂载

```yaml
volumes:
  - ./config:/app/config:rw          # 配置文件目录（必需）
  - ./downloads:/app/downloads:rw    # 录制文件下载目录（必需）
  - ./logs:/app/logs:rw              # 运行日志目录
  - ./backup_config:/app/backup_config:rw  # 配置备份目录
```

### 端口映射

仅 `web` 服务（Web 管理面板模式）映射端口，`recorder` / `gui` 服务不监听任何端口：

```yaml
ports:
  - "8000:8000"   # Web 管理面板端口（仅 --profile web 时生效）
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TZ` | 时区 | `Asia/Shanghai` |
| `PYTHONUNBUFFERED` | 实时输出 | `1` |
| `PYTHONDONTWRITEBYTECODE` | 不生成 .pyc 文件 | `1` |
| `PYTHONIOENCODING` | Python 输出编码 | `utf-8` |
| `TERM` | 终端类型 | `xterm-256color` |

### Docker 镜像特性

- **多阶段构建**：builder 阶段安装依赖到虚拟环境，runtime 阶段精简镜像
- **非 root 用户**：使用 `recorder` 用户运行，提升安全性
- **健康检查**：自动检测 `main.py` 或 `web.py` 进程是否存活
- **资源限制**：默认限制 2 CPU / 2G 内存（可在 docker-compose.yaml 调整）
- **日志轮转**：单文件 50MB，最多保留 3 份
- **内置 Node.js 24 LTS**：用于运行 JavaScript 签名脚本

## 🛠️ 开发指南

### 环境要求

- Python >= 3.14
- FFmpeg (Linux/macOS 需要手动安装)
- Node.js (Windows 下自动安装，Linux/macOS 需手动安装)

### 安装开发依赖

```bash
# 使用 uv（推荐）
uv sync --dev

# 或使用 pip
pip install -r requirements.txt
pip install pytest pytest-asyncio black isort mypy
```

### 代码规范

```bash
# 格式化代码（line-length = 120）
black .

# 排序导入
isort .

# 类型检查（CI 以 mypy 为准）
mypy .

# 类型检查（本地增强，可选）：basedpyright
# 已在 pyproject.toml 配置 [tool.basedpyright]，venvPath 指向工作区 .venv（相对路径，可移植）
# 首次需创建并安装依赖：python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
basedpyright .

# 运行测试
pytest
```

> **注释规范**：模块/函数说明统一使用 `#` 行注释，不使用三引号 `"""` 文档字符串；功能性多行字符串字面量（模板/SQL）改用单引号 + 换行拼接而非 `"""`。

> **五工具质量门禁**：本项目以 `mypy`（src + tests）/ `basedpyright`（tests）/ `pytest`（0 warnings）/ `black --check .` / `isort --check-only .` 五工具联合作为质量门禁，CI 全绿为合入前提。当前基线：**974 passed / 2 skipped / 0 warnings**。

> **测试说明**：`tests/test_web_api.py` 的符号链接相关用例（`TestListFiles::test_broken_symlink_skipped` / `test_symlink_outside_skipped`）在无法创建真实符号链接的环境（未开启开发者模式的 Windows、部分沙箱）会自动 `pytest.skip`，属正常现象，不代表代码缺陷。

### 项目文档

- [CODE_WIKI.md](CODE_WIKI.md) - 项目架构文档（详细的模块说明、依赖关系、设计模式）

### Web/接口冒烟测试

项目内置通用、零依赖的 Web/接口冒烟测试工具 `scripts/smoke_test.py`（纯标准库，无需安装第三方包），可对 Web 管理面板等**运行中 HTTP 接口**做轻量探活。

```bash
# 检查本机 Web 管理面板（默认 127.0.0.1:8000，示例配置见 scripts/smoke_web.json）
python scripts/smoke_test.py -c scripts/smoke_web.json

# 生成 HTML 报告
python scripts/smoke_test.py -c scripts/smoke_web.json -r smoke_report.html -f html
```

- 配置驱动（JSON）：`url` / `method` / `expected_status` / `timeout` / 请求头 / 请求体 / 响应应包含文本 / 期望 JSON 字段
- 支持 `base_url` 前缀拼接；控制台 / JSON / HTML 三种报告；失败时退出码非 0（可接入 CI）
- 与 `build_exe.py --smoke`（打包产物冒烟）不同，本工具针对**运行中的 HTTP 接口**做探活，两者互补
- 默认用例 `scripts/smoke_web.json` 探活 Web 面板 `/`（首页 200）与 `/health`（`{"status": "ok"}`，由 `src/web_api.py` 提供的公开探活端点，不受 `web_auth_enable` 支配）
- **已接入 CI**：`.github/workflows/ci.yml` 的 `test` job 在 pytest 之后受控启动 `python web.py`，就绪后跑 `scripts/smoke_web.json` 冒烟（经 `.github/actions/retry` 处理网络抖动、失败保留 `logs/web-smoke-*` 工件并使 job 变红），补齐「面板进程能否真正监听并应答」这条 TestClient 覆盖不到的链路

### 添加新平台支持

**视频录制平台：**

1. 在 `src/spider.py` 中添加平台流地址解析函数（参考现有平台实现）
2. 在 `src/stream.py` 中添加流地址解析函数，返回值包含 `actual_quality` 和 `available_qualities` 字段
3. 在 `main.py` 中添加平台识别逻辑（`PLATFORM_HOST` 列表和录制分支）
4. 更新 `README.md` 和 `CODE_WIKI.md`

**弹幕录制平台（如需支持弹幕）：**

1. 在 `src/platforms/` 下新建 `<平台>.py`，继承 `src/base.py` 的 `DanmakuBase`，实现连接/鉴权/消息解析
2. 在 `src/__init__.py` 的弹幕平台注册表中登记（平台名与 `main.py` 的 platform 标识一致），由 `get_danmaku_class` / `get_danmaku_collector` 工厂解耦创建
3. 在 `main.py` 的弹幕录制接线处补充平台分支（构造 `record_danmaku_args` 并传入 `check_subprocess`）
4. 更新 `README.md` 和 `CODE_WIKI.md`

> 注：弹幕子系统与 `src/spider.py`（视频流地址解析）是平行解耦的两套抽象，`spider.py` 不 import `src/platforms`。

## ❓ 常见问题

**Q: 录制时提示 "缺少 ffmpeg 无法进行录制"**

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows：full 版运行包已自带 ffmpeg，无需安装；
# lite 版 / 单文件版若自动安装失败，按「快速开始 → 手动安装 ffmpeg（Windows 用户指南）」放置
# 为 <程序目录>\ffmpeg\ffmpeg.exe（+ ffprobe.exe）即可，不要留在 ffmpeg\bin\ 子目录下。
```

**Q: Apple Silicon（M 系列芯片）Mac 上实际用的是哪一份 ffmpeg？**

发布包（full 版）内置的 macOS ffmpeg 是上游的 **x86_64 静态构建**（ffmpeg.org 官方只发布
「Static builds for macOS 64-bit」，**不提供 arm64 构建**），在 Apple Silicon 上经 **Rosetta 2**
转译执行。为避免它遮蔽用户自己安装的原生构建：当「macOS + arm64 + 系统 PATH 上已有另一份
ffmpeg」三条同时成立时，程序**优先使用系统那份**（例如 `brew install ffmpeg` 装上的原生
arm64 构建），不再把包内 `ffmpeg/` 目录前置到 `PATH`；其余情况（Intel Mac、Windows、Linux、
系统里没有 ffmpeg、或 PATH 上探到的其实就是包内那一份）维持原样，仍使用包内那份。
单文件版脚本 `douyin_live_recorder_standalone.py` 采用同一判据，只是表现为「`find_ffmpeg()` 直接
返回系统那份的路径」而不是调整 `PATH`。

确认当前生效的是哪一份：

```bash
ffmpeg -version          # Homebrew 安装的会带 --prefix=/opt/homebrew/...（Apple Silicon 原生）
                          # 包内的 evermeet 静态构建没有该前缀
which ffmpeg              # 指向包内 ffmpeg/ 目录 = 用的是包内那份
```

或查看 debug 日志（`config.ini` 中 `是否启用日志文件 = 是` 时写入 `logs/streamget.log`）里的
「FFmpeg PATH 优先级」一行，它会明确写出「让位于系统原生 ffmpeg <路径>」还是「仍前置包内目录 <路径>」。

> Docker 镜像不受此策略影响：镜像内的 ffmpeg 由 apt 安装，Apple Silicon 上按本机架构构建/运行
> Linux arm64 容器，本来就是原生执行。

**Q: 提示 "缺少 Node.js" 或 "execjs" 相关错误**

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
sudo apt-get install -y nodejs

# macOS
brew install node

# Windows
# 程序会自动下载安装到 node/ 目录
```

**Q: 提示 "IP 被禁止，请更换设备或网络"**

- 检查是否开启了代理
- 降低循环监测频率
- 等待一段时间后再尝试

**Q: 抖音风控无法获取数据**

- 在 `config.ini` 的 `[Cookie]` 节填入从浏览器 `live.douyin.com` 复制的有效 cookie（至少包含 `ttwid`）
- 降低循环监测频率（默认循环时间 120 秒已较保守，可酌情调大）
- 更换 IP 或使用代理
- 排查要点（实测结论）：
  - 抖音风控的典型信号是 **HTTP 200 + 空响应体**，而非 4xx 错误码；日志里看到 `web/enter` 返回 `status_code=10002 / unknown error` 后自动回退 HTML 抓取是**正常的容错链路**，不代表录制失败
  - 请求抖音接口必须使用**桌面端 User-Agent**，旧版移动端 UA 会被静默限流（返回空 body）
  - 主页类链接（格式 4/5）请直接填写完整地址；`iesdouyin.com/share/user/` 旧路径已变为反爬壳页，请勿使用

**Q: HLS 校验失败日志空白，总是回退到 FLV**

- 现象：日志出现 `get_response_status 校验失败（判定为不可达）: `（消息空白）后紧跟 `HLS URL validation failed, falling back to FLV`，且反复出现
- 原因（已修复于 2026-08-05）：
  - Windows 下 `socket.timeout` / `TimeoutError` 的 `str()` 为空，导致异常日志显示为空白，无法判断是超时、连接被拒还是证书问题
  - 流地址校验函数原先静默吞掉所有异常（`except Exception: return False`），回退 FLV 时无任何原因可查
  - m3u8 源 HEAD 探测原先未覆盖 404（抖音等 CDN 常对 HEAD 返回 404 而 GET 可正常拉流），且从 HLS 源选择到校验调用**未透传代理**，导致 TikTok 等需代理平台直连校验超时误判不可达
- 修复后表现：异常日志会带 URL 与异常类型；所有失败路径记录详细警告（含状态码 / content-type）；m3u8 HEAD 非 2xx（**含 404**）一律补 `Range: bytes=0-0` GET 探测；HLS 源选择正确透传代理。重新运行后若仍回退，日志会直接给出真实原因（如 `ConnectTimeout`、`HEAD=404, Range-GET=403`），此时多为 CDN 域名被墙或主播流地址失效等环境问题，而非代码误判

**Q: 录制的视频文件损坏**

- 推荐使用 `ts` 格式录制
- 检查磁盘空间是否充足
- 检查网络是否稳定

**Q: 如何只推送开播通知不录制？**

在 `config.ini` 的 `[推送配置]` 节设置 `只推送通知不录制(是/否) = 是`

**Q: Web 面板忘记密码怎么办？**

直接编辑 `config/config.ini` 中的 `web_password` 项，修改后重启 `web.py` 即可。密码变更后所有现有 Token 会自动失效，需重新登录。

## ❤️ 贡献者

<a href="https://github.com/y123ao6/DouyinLiveRecorder/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=y123ao6/DouyinLiveRecorder" />
</a>

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源，欢迎 Star 和 Fork！

## ⏳ 更新日志

### v4.3.0 (2026-09-16 ~ 2026-09-26) — P0 修复 ffmpeg master 构建下录制 100% 失败（`-thread_queue_size` 被上游收窄为输出专属选项）/ 布尔配置解析口径统一（`true/false` 致 8 项配置静默失效、9 个海外平台无法录制）/ 两轮全量代码审查（62 + 106 项分级修复）/ 供应链加固（官方哈希优先 + GPG 验签 + 删除蓝奏云兜底）/ Apple Silicon 的 ffmpeg PATH 让位策略 / 日志房间关联字段与 `/health` 探活端点 / 构建产物体积 −21.6% / 覆盖率 73.28% → 82.03%

> 本版本（v4.3.0，2026-09-16 ~ 09-26）为一次以「正确性 + 供应链安全」为主线的收敛周期。三处最值得注意：① **P0**：ffmpeg master 构建把 `-thread_queue_size` 收窄为输出专属选项，我们仍放在 `-i` 之前，导致该构建下**每一次录制都以 `-22 (EINVAL)` 退出、零字节产物**；② **布尔配置解析口径统一**：`config.ini` 写 `true/false` 曾被判为无效并**静默**回落硬编码兜底值（无告警无日志），实测致 8 项配置生效值漂移，其中最严重的一项使 9 个海外平台 100% 无法录制，现已统一为「`是/否` 与 `true/false`/`1/0`/`yes/no`/`on/off` 等价」；③ **两轮全量代码审查**（09-19 的 62 项：严重 12 / 中等 22 / 轻微 28；09-21 的 `CODE_REVIEW_2026-09-20` 106 项：严重 10 / 中等 70 / 轻微 26）把 SSRF、面板接管、凭据明文落盘、弹幕线程死循环等一批静默失效形态一次性清掉。**存在破坏性变更**，见下方专节。详细根因与验证见 [CODE_WIKI.md](CODE_WIKI.md)。

**🐛 修复的问题**
- **P0：ffmpeg master 构建下录制 100% 失败**：`-thread_queue_size` 被上游收窄为 muxer 专属选项，置于 `-i` 之前时 ffmpeg 以 `Option thread_queue_size … cannot be applied to input url … Error opening input files: Invalid argument`（返回码 -22）退出；与房间 / 平台 / CDN 无关，该构建下每次录制都失败。
- **P0：布尔配置解析口径统一**：散落四处的解析（原 `!= "否"` / `== "是"` / 前端 `=== '是'`）统一到 `src/config_bool.py::parse_config_bool`；修复后 `global_proxy` 不再被错误置 False，TikTok / SOOP / PandaTV / WinkTV / Flextv / PopkonTV / Twitch / LiveMe / Faceit 等 9 个海外平台恢复解析。
- **全量代码审查 62 项（09-19）**：GUI 空配置启动静默卡死；配置行多一个逗号致其后所有房间永久不录；Tars 解码缺边界校验致弹幕线程死循环；斗鱼弹幕被静默过滤（已修复项回归）；ffmpeg 挂起永久占用并发槽；零字节产物被判成功并撤销线路退避；`config.ini` 含凭据被明文复制到 `backup_config/`；Web 面板可被自身接口接管或锁死；房间 URL 零协议校验 → 盲 SSRF；脱敏黑名单漏掉「凭据嵌在值里」的 URL 型键；安装与打包链路零完整性校验。
- **`CODE_REVIEW_2026-09-20` 全轮落地 106 项（09-21）**：并发信号量把「可用许可数」当容量（网络并发上限实质失控）；`PUT /api/rooms` 绕过房间入口校验；内网地址拦截用字符串前缀黑名单（实测 7 条放行 5 条）；面板认证可被单个写请求热关闭、大小写变体绕过口令哈希 / 防自锁 / token 吊销；CRLF 配置下删除房间永久静默失效却回报 `{"ok": true}`；Shopee 站点后缀解析拼出非法域名；兜底装饰器与返回契约错配（故障伪装「未开播」）；录制看门狗「停滞」判据基准用错（容忍窗口实际只有 30 秒）；`only_flv` 分支缺 `flv_url` 致时间字幕线程死循环写盘；发布链运行时二进制哈希钉定表为空。
- **发布链与供应链**：macOS arm64 的 full 包**静默不含 ffmpeg**（上游无该产物，下载点已修复）；Windows 运行期 ffmpeg 主源经实测确认健康（gyan.dev 带 `.sha256` 文档，与发布期钉定互证）；官方 SHA256 钉定值回填 6/10 槽。
- **测试卫生（09-23）**：一处跨文件补丁泄漏（漏掉的 `undo()`）让同会话后续用例发出真实网络请求，造成 13 条失败里 11 条「全量红、单跑绿」的假失败。
- **P0：构建脚本污染测试会话（09-23）**：`build_exe._ensure_utf8_streams()` 裸 `reconfigure` 破坏 pytest 的 fd 捕获，表现为「GUI 启动失败」弹窗与无关用例被判 FAILED/ERROR（九个 CI job 全为 ubuntu，恒绿不复现）。

**✨ 新增功能 / 改进**
- **日志房间关联字段 `extra[room]`**：`src/logger.py` 新增 `ROOM_FIELD` / `set_room_context()` / `get_room_context()`（内部 `ContextVar` + patcher），多房间交织日志可按房间切出。
- **Web 面板 `/health` 探活端点**：`GET /health` 返回 `{"status": "ok", "version": …}`，并把内置冒烟工具 `scripts/smoke_test.py` 接通为 CI 可执行的真实 HTTP 探活。
- **W6：Apple Silicon 的 ffmpeg PATH 让位策略**：darwin + arm64 且系统 PATH 上另有原生 ffmpeg 时，不再无条件前置包内那份 x86_64 构建（需经 Rosetta 转译），五条判据全部成立才让位；其余平台逐字不变。
- **运行时二进制完整性**：`build_exe.py` 新增 `_PINNED_RUNTIME_SHA256` 钉定表 + `--require-pinned`，配套 `scripts/check_runtime_pins.py`（结构模式进门禁 / `--strict` 进发布 prepare / `--emit-env` 供 CI 注入）；运行期首装改为「官方公布哈希优先」，发布期增加 GPG 验签与 full 包产物自检。
- **构建产物体积优化（09-24）**：排除 `PIL._avif`、`pydantic.v1.mypy`（拖入整个 mypy）、uvicorn 可选实现、`i18n/*.po` 等运行期不可达模块 + zip `compresslevel=9`，lite 产物 **82.77MB → 64.88MB（−21.6%）**、zip **54.84MB → 42.19MB（−23.1%）**，并新增 `scripts/report_bundle_size.py` 度量脚本。
- **新增五类门禁**：`PYTHONUTF8=1` + 「告警即失败」（消灭 GBK locale 下 isort 静默跳文件且 rc=0）、装饰器契约 AST 锁、测试卫生 AST 锁（R1–R4 / R6「手工 MonkeyPatch 必须配对 undo」）、前端目录一致性锁（`data-i18n*` 键与四语内嵌目录逐一比对）、`deps-audit` job 与覆盖率无数据硬失败。
- **动态并发下限下调**：`ConcurrencyScheduler` 的 `min_capacity` 默认值 8 → 1。

**⚠️ 破坏性变更 / 行为变化**
- **Windows 运行期删除蓝奏云 ffmpeg 兜底**：自动安装只剩主源一条路（实测该直链为带人机验证的 HTML 页、伴生哈希文档全 404，不可用）；自动安装失败时改为给出明确的手动安装指引。**Windows 用户若原先依赖该兜底，需按 README 的「Windows 手动安装 ffmpeg」章节自行放置二进制。**
- **Apple Silicon 不再无条件前置包内 ffmpeg 目录**：已用 Homebrew 装原生 arm64 ffmpeg 的用户，录制子进程会改用系统那份（版本 / 编译选项可能不同）。
- **动态并发下限 8 → 1**：低负载场景下的网络并发额度不再被抬到 8。
- **布尔配置写法语义变化**：此前写 `true/false`、`1/0` 等被**静默忽略**（回落到兜底值）的键，升级后按其字面生效 —— 若你的配置依赖旧的错误兜底值，升级后生效值会改变，请在升级后核对 8 项相关配置。
- **运行时依赖 20 → 23 条**：新增显式声明 `urllib3>=2.7.0`（CVE-2026-44431）、`h2>=4.3.0` 与 `socksio>=1.0.0`（httpx 的 http2 / SOCKS 运行期依赖），`starlette` 下限 `>=0.49.1` → **`>=1.3.1`**（CVE-2026-48710 与 PYSEC-2026-2280/2281/248/249），`protobuf` 保持 `<8` 上限（gencode 兼容护栏）。
- **构建期**：`build-release.yml` prepare 以 `check_runtime_pins.py --strict` 拦下未钉定的运行时二进制。

**🛠️ 仓库维护与质量门禁**
- **测试覆盖率专项（09-21）**：`src/` 覆盖率 **73.28% → 82.03%**（仅动 `tests/`，产品代码零改动），并引入分层白名单（表默认空 + 到期即失败）。
- **四语目录持续补全与核验**：594 → **780 条**，四个目录键集逐条一致、无空值；`.mo` 随变更重编译。
- **元数据同源同步**：`AGENTS.md` 依赖条数与下限口径、`CODE_WIKI*.md` 依赖表（16 → 23 条）、`DouyinLiveRecorder.egg-info` 重建、`.dockerignore` 补 `_probe_*.py`、`config/config.ini` 补 `[Cookie] ttwid`。
- **类型存根与注释治理**：`typings/execjs/` 7 个 `.pyi` 补齐注解、两个抽象基类存根去 `six`（改 `metaclass=ABCMeta`）；全仓多批注释精炼（含 68 文件一轮），`scripts/check_annotations.py` 新增第三盲点（换行符形态）。
- **清理已删除模块残留**：`src/weverse_auth.py` / `tests/test_weverse_auth.py`（2026-09-23 删除）在目录树、依赖注释与四语目录中的 3 条孤儿译文一并清除。

**🧪 测试与验证**
- 全量 `pytest` **3199 passed / 13 skipped**；另有 1 条 `test_symlinked_system_hit_inside_bundled_dir_keeps_prepending` 在**本机 Windows** 恒红——该主机 `Path.symlink_to()` 不产生真正的重分析点（不抛异常但不解引用），场景无法复现，CI 的 Linux/macOS 环境正常。
- `black --check .` **169 files unchanged**；`isort --check-only .` 无重排；无参数 `mypy` **158 files 0 issues**（追加 `mypy --platform linux` 亦 0）；`basedpyright`（standard）**0 errors / 0 warnings / 0 notes**。
- `node --test tests/frontend/*.mjs` 通过；`scripts/check_version.py` 与 `scripts/check_runtime_pins.py` 均 rc=0。

### v4.2.0 (2026-09-12 ~ 2026-09-15) — 代码审查全量修复（~120 项·安全/并发/平台）+ 斗鱼「只出 SRT 无视频」根因定位与 HLS 分片层假绿探针 + 选源加固 + start_record 命令构造/平台分派单一定义点重构 + 仓库元数据同源同步与四语本地化一致性修复 + mypy 门禁扩面（范围下沉 `[tool.mypy].files`）与 6 处类型缺陷修复 + Linux CI 只读用例修复

> 本版本（v4.2.0，2026-09-12 ~ 09-15）为一次覆盖安全、并发、平台层与门禁的综合性修复与加固周期。核心修复：① 定位并修复斗鱼等平台「仅生成弹幕 SRT、无视频文件」——HLS 播放列表层恒返 200，但边缘节点媒体分片全 404，ffmpeg 零媒体段产出；弹幕链路仅依赖 `room_id` 与视频解耦，故 SRT 照常写出。新增 HLS 分片层探针 `_probe_hls_segment`（把「列表 200」与「可录制」解耦）与三方向选源加固（配置兜底 / 观测增强 / 同源 FLV 候选回退）。② 收敛 `start_record` 五路 ffmpeg 命令构造为单一定义点、平台分派由 53 层 `elif` 改为分发表驱动，行为零差异（黄金快照 + 分派快照逐字节/逐项比对）。③ 完成 `CODE_REVIEW_FIX_1`（F-01~F-25，22 项落地 + 3 项暂缓）与 09-12 代码审查全量修复（约 120 项：SHA256 钉定、原子写、解压炸弹防护、singleflight 并发、斗鱼粘包 / B站看门狗 / Shopee 等平台修复）。④ 仓库元数据（pyproject 排除目录 / .gitignore / .dockerignore / AGENTS.md）同源同步，并修复 en_GB 目录 21 条误填繁体中文，四语目录重校准至 594 条一致。⑤ mypy 门禁范围下沉到 `pyproject.toml [tool.mypy].files` 单一事实源（`src/` → 全量代码含根入口 / `build_exe.py` / `scripts` / `tests`），并修复 6 处此前长期逃逸的类型缺陷——其中 `gui.py` 子进程自然结束后的 UI 收尾路径**必抛 `NameError`**（除该收尾路径外无功能行为改动）；另修复 Linux CI 上「只读配置」用例因原子写 `os.replace` 只校验目录权限而失效的问题。**无破坏性变更**（运行时语义全部保持）。详细根因与验证见 [CODE_WIKI.md](CODE_WIKI.md)。

**🐛 修复的问题**
- **斗鱼「只出 SRT、无视频」根因定位 + HLS 分片层假绿探针**：HLS 播放列表层恒返 200…
- **选源加固（配置兜底 / 观测增强 / 同源候选）**：`_hls_selection_config()`（经 `getattr(main, "hls_collection_enabled"/"hls_collection_exclude_platforms", 默认)` 读取…
- **代码审查全量修复（09-12…
- **CODE_REVIEW_FIX_1 批量修复（F-01~F-25）**：main.py F-02 移除死 import（`converts_m4a`/`segment_video` 函数保留于 `video_postprocess.py`）、F-03 直下流 `finally` 仅当零字节才清理残留…
- **F-13 抖音 signature 保持不编码**：对照上游 `dart_simple_live` 确认其直接字符串拼接、不 `encodeComponent`
- **F-12 sync_http SSL 作用域收窄**：`CERT_NONE` 上下文与 opener 由 import 期常驻改为惰性构造…
- **check_annotations 违规修复**：`tests/test_start_record_command_golden.py` 的 `class _Cap:` 三引号 docstring 改为 `#` 行注释（符合「禁 docstring」约束）
- **mypy 门禁扩面 + 6 处类型缺陷修复（09-15）**：起于 CI typecheck 的 3 个报错…
- **Linux CI 只读用例修复（09-15…

**✨ 新增功能 / 改进**
- **start_record 命令构造与平台分派单一定义点（F-01）**：五路内联 `command=[]` 收敛为模块级 `_build_ffmpeg_output_args` / `_build_ffmpeg_input_args` / `_build_record_output_path` / `_ffmpeg_network_tuning`
- **JS 签名脚本哈希钉定（F-25）**：`get_compiled_js` 读原始字节比对 `_JS_SHA256_EXPECTED` 基线…
- **F-14 protobuf 兼容护栏**：本环境无 protoc…
- **mypy 门禁范围下沉为单一事实源（09-15）**：`pyproject.toml [tool.mypy].files` 固化为 `src` + 根入口（main / gui / web / i18n / msg_push）+ `build_exe.py` + `scripts` + `tests`

**🛠️ 仓库维护与质量门禁**
- **pyproject 排除目录同源补全**：`logs`/`backup_config` 原先只进部分工具——现已补齐到 black `.exclude`、isort `extend_skip`、mypy `exclude`、basedpyright `exclude`、coverage `omit`
- **.gitignore / .dockerignore 通配化**：移除已不存在的 `PERF_REVIEW_2026-08-28.md` 等逐文件名条目…
- **四语本地化一致性修复**：修复 `i18n/en_GB.json` 21 条值误填繁体中文（弹幕解析异常 7 条 + ffmpeg/Node 安装 SHA256 提示 14 条）
- **仓库元数据同步**：`AGENTS.md` / `docker-compose.yaml` 示例版本 `4.1.0`→`4.2.0`

**🧪 测试与验证**
- 全量 `pytest` **974 passed / 2 skipped / 0 failed**（909→929→944→974 递增）
- `black --check --line-length 120 --target-version py314 .` 134 文件全绿…
- 09-15 门禁扩面后：无参数 `mypy` **115 files 0 问题**（覆盖 src + 根入口 + `build_exe.py` + `scripts` + `tests`）

### v4.1.0 (2026-09-10 ~ 2026-09-11) — P0 修复 ffmpeg `-reconnect*` 缺值与 HLS 无限重连（直播只出字幕无视频）/ 代码审查 28 项修复 / 遗留 8+4 项推进 / i18n 形参日志 242 处全量迁移 / Web 面板窄视口修复 / 四语本地化补全

> 本版本（v4.1.0，2026-09-10 ~ 09-11）修复两处 P0 录制链路缺陷：① ffmpeg `-reconnect*` 选项移入 `-i` 之前时丢失布尔值 `1`，真实录制输入未打开即退出（返回码 -22）；② `-reconnect_at_eof 1` 对 HLS(m3u8) 输入在**播放列表层无限重连**，hls demuxer 永远拉不到媒体段——直播表现为「只产出了弹幕 SRT、无视频文件」。同期推进代码审查 28 项修复、遗留 8+4 项（hls.js 钉版 / TLS 拆流 / 音频容器对齐 / `gui_legacy.py` 删除 / 弹幕落盘移出事件循环 / i18n `tr()` 接口等）、242 处形参日志 f-string → `i18n.tr` 全量迁移、Web 面板窄视口错位修复，并完成八文件元数据同源同步与四语本地化补全（521 → 539 → 544 键）。**无破坏性变更**（录制/弹幕/网络/推送运行时语义全部保持）。详细根因与验证见 [CODE_WIKI.md](CODE_WIKI.md)。

**🐛 修复的问题**
- **P0 ffmpeg `-reconnect*` 缺值 → 录制启动即 -22（EINVAL）**：09-10 审查重构把 `-reconnect_delay_max 60 / -reconnect_streamed / -reconnect_at_eof` 从 `-i` 之后移至之前时…
- **P0 HLS(m3u8) 输入禁用 `-reconnect_at_eof` → 直播只出字幕无视频**：m3u8 播放列表文件本身的 HTTP 响应结束即 EOF…
- **代码审查 28 项修复（2026-09-10）**：ffmpeg 命令 `-reconnect*` 确立「位于 `-i` 之前且每个选项紧跟取值」
- **Web 面板直播间列表窄视口错位**：`table-layout: fixed` + 地址/名称列单行省略（悬停可见全 URL）+ ≤768px 横向滚动兜底…

**✨ 新增功能**
- **i18n `tr()` 形参接口 + 242 处全量迁移**：`i18n.tr(template, **kw)` 先查表再插值——修复 f-string 在查表**之前**完成插值、目录里含占位符键永远匹配不上、翻译静默退化为原文的根因…
- **Web API 鉴权加固**：中间件统一注入 `X-Content-Type-Options: nosniff` / `X-Frame-Options: DENY`；新增公开端点 `GET /api/auth/status` 暴露认证开关与警告文案。
- **hls.js 钉版 1.7.2**：`index.html` 的 `hls.js@latest` 钉到具体版本（jsdelivr CDN 供应链风险收敛，与 flv.js 钉版惯例对齐）。

**🛠️ 仓库维护与质量门禁**
- **遗留 8+4 项推进**：8 项决策类全部实施——hls.js 钉版、`http_config` TLS 校验拆「拉流专用 / 控制面通用」两路径、纯音频平台扩展名/容器/编码三方对齐（`.m4a`+aac+ipod / `.ts`+aac+mpegts）、notify 脚本 300s 超时 `kill` 兜底、Web 鉴权模型文档化、删除 `gui_legacy.py`、弹幕 SRT 落盘移出事件循环（`queue.SimpleQueue` + 独立写盘线程）、i18n `tr()` 接口…
- **元数据同源同步**：`uv.lock` 项目版本对齐 4.1.0（73 包依赖图未动）、`DouyinLiveRecorder.egg-info` 重新生成、`AGENTS.md` / `docker-compose.yaml` 等八文件版本与依赖核对无漂移、`scripts/check_version.py` PASS。
- **四语本地化补全**：经 `extract_i18n_strings.py` 补入修复期新增串…

**🧪 测试与验证**
- 全量 `pytest` **907 passed / 2 skipped / 0 warnings**（870 → 899 → 902 → 907 递增）
- `scripts/extract_i18n_strings.py` 缺失 0 条、四语目录零差异…

<details><summary>点击展开更多历史版本</summary>

### v4.0.9.4 (2026-09-03 ~ 2026-09-06) — HLS 采集排除平台列表 / 画质选项增删与行内切换 / P0 分段容器错配修复 / 打包缺陷修复 / 全仓注释补齐与元数据同源同步

> 本期（v4.0.9.4，2026-09-03 ~ 09-06）为多项一致性与质量收尾批次。新增 HLS 采集排除平台列表配置、画质选项用户可增删 + GUI/WEB 行内切换画质；修复两处高危问题——抖音原画 HEVC 因分段容器错配无法录制（P0）、`async_http` 跨循环协程告警导致 pytest 波动告警；修复 `pyproject.toml` 打包缺陷（子包未声明致 `pip install .` 发行包残缺）。同时完成全仓中文注释补齐（41 文件 / +1370 行）、八文件元数据同源同步、四语本地化目录补齐（516→521）。**无破坏性变更**（运行时语义全部保持；PEP 758 无括号 except 写法仅影响 <3.14，本仓下限即 3.14，属既定约定非回退）。详细根因与验证见 [CODE_WIKI.md](CODE_WIKI.md)。

**✨ 新增功能**
- **HLS 采集排除平台列表**：新增配置项 `HLS采集排除平台(逗号分隔)`——命中平台无视「是否启用HLS采集」开关、恒按 FLV 采集…
- **画质选项可增删 + 行内切换画质**：画质选项从引擎白名单固定 10 档改为用户自选子集（落 `config.ini` [录制设置] 自定义画质选项）
- **单文件整合版迁移至 `scripts/`**：`douyin_live_recorder_standalone.py` 自根目录迁入 `scripts/`

**🐛 修复的问题**
- **P0 分段录制容器错配**：抖音原画 HEVC 因 TS+分段分支 `-segment_format` 误用 `ipod` 容器…
- **flaky 告警根治**：`src/async_http.py` 删除跨循环 `run_coroutine_threadsafe(client.aclose(), ...)` 调度分支（根因：旧循环已停未关时协程永不 await、GC 报 "never awaited"）
- **GUI 画质切换三缺陷**：键格式不匹配（序号前缀导致反查表 miss）、持久化丢失（写回后编辑器仍持旧快照被整文件覆盖）、显示重置（表格取自子进程旧日志值）——切换后剥离序号前缀查表、写回后同步编辑器快照、显示以配置文件为准。
- **打包缺陷修复**：`pyproject.toml` 的 `[tool.setuptools].packages` 由 `["src"]` 改为 `["src", "src.platforms", "src.proto"]`

**🛠️ 仓库维护与质量门禁**
- **全仓中文注释补齐**：41 文件 / +1370 行（平均密度 7.6%→20.4%）
- **八文件元数据同源同步**：以 `pyproject.toml` 为单一事实源…
- **四语本地化目录补齐**：经 `extract_i18n_strings.py` 补入 5 条缺失串，四目录键集合重一致（各 521 条），`zh_CN.mo` 重编译（`--check` 字节级同步通过）。
- **测试残留自清理**：`tests/conftest.py` 新增 `pytest_unconfigure` 钩子，会话结束自动删除 `tests/_out_live` / `tests/_out_e2e`。

**🧪 测试与验证**
- 全量 `pytest` **858 passed / 2 skipped / 0 warnings**；`pytest tests/test_i18n.py` 34 passed（四目录键集合一致性）。
- `mypy` / `basedpyright`（0 error / 0 warning）/ `black --check` / `isort --check` / `scripts/check_annotations.py` 全绿…

### v4.0.9.3 (2026-09-02) — 代码审查 20 项问题全量修复（cookie 缓存并发去重 singleflight 重写 / Web 非 ASCII 密码登录崩溃 / 探针异常留痕与节流自清理 / 64 位 ctypes 句柄截断 / 连接资源生命周期）+ mypy 全仓类型清零（tests / gui_legacy / scripts / standalone）

> 本版本为《代码检查报告》20 项审查问题的全量闭环批次，并完成 mypy 静态类型检查全仓清零（102 个源文件 0 报错，首次覆盖 CI 口径之外的 tests / gui_legacy / scripts 与单文件整合版 standalone）。两项高优先级修复：① cookie 缓存并发去重按 singleflight 模式重写——原实现跨 `await` 持有线程亲和的 `threading.RLock`，同事件循环内的并发协程全部可重入该锁、互斥完全失效，多协程照样并发请求同一网址（恰是本模块要消除的风控触发源）；② Web 面板历史明文密码兼容路径对非 ASCII 密码直接抛 `TypeError`（`hmac.compare_digest` 不支持含中文的 str 比较，`/api/login` 直接 500）。中优先级八项覆盖 Web API 写入口径、备份守护线程紧循环、探针异常留痕与节流字典无界增长、64 位句柄截断、装饰器兜底值类型、HTTP 连接泄漏、重复实现收敛与 Session 生命周期；低优先级八项为冗余与风格清理。**无破坏性变更**（cookie 缓存 TTL / 失败不缓存 / 探针退避与节流 / Web API 路由契约等运行时语义全部保持）。详细根因与验证见 [CODE_WIKI.md](CODE_WIKI.md)。

**🍪 Cookie 缓存并发去重重写（高危修复）**
- **根因**：`fetch_cookies` 原实现跨 `await` 持有 `threading.RLock`——RLock 是线程亲和锁…
- **singleflight 重写**：`threading.Lock` 只保护「缓存字典 + 在途登记表 `_inflight`」的同步读写（**锁内绝无 await**）
- **健壮性**：拉取协程被取消（房间停止/进程退出）时在 `BaseException` 分支立即摘除登记并给等待者交付空结果…
- 效果：同平台多房间并发时对同一域名不再重复请求访客 cookie，风控触发概率进一步降低。

**🔐 Web 面板与系统托盘缺陷修复（高危 / 中高 / 中）**
- **非 ASCII 明文密码登录 500**：`verify_web_password` 历史明文兼容路径改为 `hmac.compare_digest` 的 UTF-8 bytes 比较（str 比较不支持非 ASCII…
- **Web API 写入口径统一**：`PUT /api/rooms` 写入行改用 `normalize_url`——原写入未归一化 URL…
- **64 位 ctypes 句柄截断**：`web_tray.py` 改用 `ctypes.WinDLL` + 全量 `argtypes`/`restype` 显式声明（`GetConsoleWindow.restype = c_void_p`）

**🛡️ 守护线程与探针健壮性（中）**
- **备份守护紧循环**：`config_io.py` 的 `time.sleep(600)` 移出 `try`——原异常分支不等待，check_md5/backup 持续失败时退化成紧循环空转、疯狂刷日志并空耗 CPU。
- **探针异常留痕与复核语义**：`stream_select.py` 的 `_confirm_get_ok` 补 `logger.debug`（含异常类型 + attempt 序号…
- **节流字典自清理**：`_throttle_probe` 写入时顺带剔除空闲超过 `_PROBE_MIN_HOST_INTERVAL × 10` 的旧 host…
- **弹幕边车留痕**：`danmaku_monitor.py` 的 `_write_line` 写失败分支补 `logger.debug`，与本模块「异常全吞但必须留痕」约定一致，边车数据不再无迹丢弃。
- **取消信号不再被吞**：`ws_client.py` 心跳任务回收的 `except asyncio.CancelledError, Exception:` 拆分——`CancelledError` 仅吞 hb_task 自身按预期被取消的情形…

**♻️ 资源管理与兜底类型（中）**
- **装饰器兜底值类型**：`utils.py` 装饰器共用实现收敛为 `_make_trace_error_guard(func, fallback)`
- **消除「错误伪装成正常结果」**：`spider.py` 5 个返回 str/tuple 的函数（`get_bilibili_room_info_h5` / `login_sooplive` / `get_sooplive_tk` / `get_winktv_bj_info` / `login_flextv`）由统一 dict 兜底切换至 `None` 兜底——旧实现中 `login_flextv` 失败返回的 dict 曾被 `if new_cookies` 误判为登录成功。
- **重复实现收敛**：`node_install.py` 与 `ffmpeg_install.py` 各自逐字重复的 `unzip_file()` 收敛至 `src/utils.py` 单一实现（含 Zip Slip 校验）
- **Session 生命周期**：`sync_http.py` 新增 `WeakSet` 登记线程级 Session、`close_session()`（当前线程显式释放）与 `close_all_sessions()`（`atexit` 注册…

**🧹 风格约定 / 环境修复（低）**
- **PEP 758 except 写法定稿**：实测 black 26.x 稳定风格就是无括号形式 `except A, B:`（加括号反而过不了格式门禁）
- **venv 幽灵问题修复**：`.venv` 中 editable 安装原指向另一 checkout（`D:\DouyinLiveRecorder-coding`）

**🧹 mypy 全仓清零**
- `tests/test_quality_tiers.py`：5 处 `mock.await_args.args[1]` 前补 `assert mock.await_args is not None`（typeshed 将 `await_args` 声明为 Optional…
- `gui_legacy.py`：4 处——悬停效果 lambda 改具名闭包工厂、`command` 参数补 `str | Callable[[], Any]` 注解、`optionxform` 改具名函数 + `setattr` 绕过（对齐 `gui.py` 惯例）、补 `collections.abc.Callable` 导入。
- `scripts/extract_i18n_strings.py`：动态 `getattr` 结果用 `cast` 收敛（`warn_return_any` 门禁），移除已无用的 `type: ignore`。
- **单文件整合版（standalone）**：`douyin_live_recorder_standalone.py` 4 处告警清零——`json.loads` 返回值 `cast`、`_douyu_sign` 补 `isinstance(sign, dict)` 守卫（非 dict 直接返回 `None`

**🧪 测试与验证**
- `tests/test_cookie_cache.py` 加强：`test_same_loop_reentrant_no_deadlock` 同时断言「并发 gather 5 协程只拉取一次」（旧 RLock 实现下该断言必失败——正是本次修复的目标行为）
- 全量 `pytest` **806 passed / 2 skipped / 0 failed**…
- web_tray 实测：`WinDLL` 加载成功、窗口改写链路无异常（headless 下 `GetConsoleWindow` 返回空、按预期跳过）。

### v4.0.9.2 (2026-08-28 ~ 2026-08-30) — Web 面板录制手动控制 / 虎牙·斗鱼蓝光细粒度画质档位 / 停止录制流程日志归档 / 性能审查优化落地（P1~P5）/ 探针退避窗口自愈与虎牙 FLV-first / Web 后台日志 sink 重建 / GUI 父进程日志句柄隔离

> 本版本沿「可控性、画质粒度、高并发性能、可运维性」四条主线：Web 面板移除启动自动录制、新增「开始/停止录制」手动控制（全局开关 + 录制主链 7 处中断点 + ffmpeg 分级优雅终止）；虎牙/斗鱼支持蓝光细粒度档位（蓝光4M/8M/20M/30M 的选档 → 拉流 → 不可用就近降级全链路）；性能审查落地 P1~P5 五项优化（80 房间选源探针耗时 12.7s → 1.15s），并经三轮真机验证根治虎牙冷启动「探针假绿 → ffmpeg 403」死循环（退避窗口对齐主循环 + 录制成功清除退避 + 虎牙 FLV-first）与 Web 后台模式日志写向被隐藏窗口的问题；08-30 起停止录制流程统一把四个运行日志按时间戳改名归档（冲突递增、缺失跳过、句柄先行关闭），GUI 父进程与录制子进程日志句柄隔离根治 `streamget.log` 轮转 WinError 32（录制日志全量静默丢失），i18n 四语目录补齐至 516 条并重编译 `zh_CN.mo`。**无破坏性变更**（配置项与运行时语义完全兼容；虎牙选源顺序反转为 FLV-first、斗鱼保持 HLS-first，属行为变更）。详细根因与验证见 [CODE_WIKI.md](CODE_WIKI.md)。

**🎥 Web 面板录制手动控制（新增功能）**
- 全局开关 `main.recording_enabled`（默认 True…
- 录制主链注入 **7 处中断点**：ffmpeg 轮询（1s 周期）、直下下载 chunk 级、房间线程入口、直下失败判定排除、循环等待期打断、主循环拉起新线程前、线程退出 finally 兜底（`remove_room_from_running` 幂等清理运行列表…
- 新增 `POST /api/recording/toggle` 切换端点（处于既有 Bearer 认证中间件覆盖内）与状态快照 `recording_enabled` 字段…
- **停止语义为主动分级优雅终止**：轮询命中开关关闭即按「stdin 写 'q'（写完文件尾…
- `recording_enabled` 为会话级运行时开关、不持久化：重启后面板回到停止态，避免从后门重新引入「启动即自动录制」。

**🎚️ 虎牙/斗鱼蓝光细粒度画质档位（新增功能）**
- 画质代码层扩展：`QUALITY_LEVEL` / `QUALITY_MAPPING_BIT` / `QUALITY_CODE_TO_ZH` 由 6 项扩为 10 项（新增 `BD30`/`BD20`/`BD8`/`BD4`）并新增 `BD_SUB_TIERS` 冻结集合…
- 虎牙：新增 `HUYA_FIXED_TIERS`（ratio 即码率上限 kbps…
- 斗鱼：新增 `DOUYU_RATE_BY_CODE` / `DOUYU_RATE_TO_CODE` / `DOUYU_RATE_DESC`
- Web 面板画质下拉新增 蓝光30M/20M/8M/4M 四个选项…

**📼 停止录制流程日志归档（新增功能）**
- 触发点两处：Web 面板「停止录制」**即时归档**（进程继续运行…
- 归档规则：四个运行日志（`streamget.log` / `PlayURL.log` / `danmaku_monitor.jsonl` / `web_console.log`）按「原名_YYYYMMDD_HHMMSS.扩展名」改名（时间戳取停止操作发生时刻）
- 句柄安全（Windows 下句柄未关 rename 必抛 WinError 32）：loguru 文件 sink 经 `remove()` 先 flush 异步队列再关句柄…
- 安全守卫：GUI 父进程（`DLR_GUI_PARENT=1`）与测试进程（`DOUYIN_DISABLE_LOG_ARCHIVE=1`）一律早返回，不改名录制子进程正在写或开发者工作副本中的真实日志。

**⚡ 性能优化（审查落地 P1~P5）**
- **P1 探针客户端整轮复用**：`select_source_url` 全部候选共用一支 `httpx.Client`（`finally` 关闭…
- **P2 `requests.Session` 线程级复用**：`sync_http` 经 `threading.local` 每线程一支 Session（125 个调用点全部受益），实测单请求 11.9ms → 1.47ms。
- **P3 主循环去重容器 set 化**：`url_comments` / `line_list` / `url_line_list` 由 list 改 set（成员检测 O(N²) → O(1)），`url_comments.discard` 取代每行整表重建。
- **P4 调度器计数增量**：熔断窗口与全局错误窗口改增量维护（O(1) 替代持锁下 O(40) 全量求和），缩短锁持有时间。
- **P5 高频正则提模块级常量**：表情模式（约 400 字符）、URL 片段、HLS 带宽、抖音 HEVC 等 5 处函数内 `re.compile` 上提为模块级常量…

**🐛 问题修复（真机验证衍生）**
- **探针退避窗口自愈（虎牙假绿死循环根因）**：原固定 60s 退避窗口小于主循环默认 120s 间隔——快速失败记入退避后下一轮 T+124s 才到、早已过期…
- **录制成功撤销探针退避**：新增 `clear_ffmpeg_reject()` 与失败侧 `mark_ffmpeg_reject` 配对——已恢复的线路不再被窗口内继续跳过、白白回退到次优线路。
- **虎牙选源反转为 FLV-first**：三轮真机实证 HLS 三条 CDN（hs/tx/al）冷启动探针假绿（探针 200/206、ffmpeg 打开即 403）
- **Web 后台模式日志 sink 重建**：loguru 的 sink 在 `add()` 时绑定具体对象、不随 `sys.stderr` 重定向而变——不重建则 DEBUG/WARNING 全部写向被 SW_HIDE 隐藏的控制台…
- **Web 录制控制双轮审查修复**：前端状态标签选择器缺陷（容器实为 class 却用 `#id` 选择器、状态永不切换，P1）等 3 处。
- **GUI 父进程日志句柄隔离**：GUI 进程（经 `src.web_config → src/__init__ → src.logger` 导入链初始化文件 sink）与录制子进程双开 `streamget.log`
- **类型修复**：`src/stream.py` 补全 `HuyaGameLiveInfo` TypedDict 的 `bitRate: int` 字段声明并移除 `# type: ignore`（新版 mypy 对未声明键退化类型报 `call-overload`）

**🔧 CI / 工程维护**
- **i18n 四语目录补齐（507 → 516 条）**：日志归档功能引入的 9 条新日志串补入 `zh_CN.po` / `en_US.json` / `en_GB.json` / `zh_TW.yaml`（繁体按既有语汇转换：日志→日誌、文件→檔案、归档→歸檔、句柄→控制代碼）
- **仓库元数据同源清单同步**：九配置文件（`AGENTS.md` / `docker-compose.yaml` / `requirements.txt` / `Dockerfile` / `.gitignore` / `.dockerignore` / `.coveragerc-concurrency` / `pyproject.toml` / `uv.lock`）一致性审计——依赖三处一致（20=20）、`uv lock --check` 同步、Dockerfile（python:3.14-slim + Node 24）≡ CI（python_build=3.14 / node_version=24）、版本链 `check_version.py` 全过…

**🧪 测试与验证**
- 日志归档专项：新增 `tests/test_log_archive.py`（14 用例：改名格式正则锁定、`_N` 序号去重不覆盖、缺失全跳过、单文件改名失败不中断整批、GUI/测试进程双守卫、`reopen_streams` 双态语义、web_console 绑定句柄轮转、hub `close_file` 后惰性重开、sink remove→add 往返幂等、main.py 归档 atexit 注册顺序静态锁）
- 新增 `tests/test_quality_tiers.py`（29 用例：子档位映射/索引折叠/虎牙就近降级/斗鱼重试链）、`tests/test_logger_console_sink.py`（3 用例：跟随当前 stderr / 替换而非追加 / None 静默）
- 全量 `pytest` **806 passed / 2 skipped**（0 警告…
- 三轮真机验证（虎牙 880214 / chuhe、斗鱼 3168536）：退避告警首次出现、FLV 稳定连录 6 分钟、`web_console.log` 恢复完整 DEBUG/WARNING…

### v4.0.9.1 (2026-08-27 ~ 2026-08-28) — 高并发调度加固 / 本地化系统修复 / 编译与熔断门禁修复 / CI 工作流优化与重试收敛

> 本版本为 4.0.9 调度体系的审查修复与加固批次，并收尾本地化子系统：全量质量门禁 + 并行代码审查发现并修复多个高危/中危缺陷，i18n 目录经全仓 AST 扫描全量补全至 496 条、解除 i18n 模块语法阻塞并重新编译 `zh_CN.mo`；08-28 追加 CI 工作流优化（重试收敛为复合动作）、PEP 758 格式化随 black 26 落地与仓库元数据八文件同步。**无破坏性变更**（配置项与运行时语义完全兼容）。详细根因与验证见 [CODE_WIKI.md](CODE_WIKI.md)。

**✨ 新增功能**
- **Web 配置行级追加 API**：`web_config.py` 新增 `append_config_line(config_file, section, key, value)`
- **语言切换写回降级**：`web_api.py` 的 `PUT /api/language` 写回在行级替换失败时自动调用 `append_config_line` 节末追加补建…
- **i18n 四目录全量补全（288 → 496 条）**：AST 扫描全仓运行时 `print()`/`logger.*()` 常量串（47 文件、355 串）
- **CI 网络安装重试复合动作（`.github/actions/retry`）**：新增复合动作统一包装 pip / apt / choco / brew 网络安装命令的线性退避重试（`command` / `label` / `attempts` / `backoff` 可参数化）

**🐛 问题修复**
- **i18n 本地化系统阻断（高危）**：`i18n.py`（3 处）与 `scripts/compile_po.py`（1 处）的 Python 2 风格 `except A, B:`（含一例三异常逗号）多异常写法改为 `except (A, B):`
- **CI black 门禁（PEP 758 格式化）**：上述 4 处元组括号随后按 black 26.5.1（`target-version=['py314']`
- **编译同步门禁恒真（P1）**：`scripts/compile_po.py` 的 `write_mo()` 改为纯内存产出（去除写盘副作用）
- **熔断探针租约自愈（高危）**：根治 `PlatformBreaker` half-open 探针泄漏——探针轮以 `continue` 结束且不上报样本时 `_probing` 标志永不复位、该 host 永久熔断直到进程重启…
- **调度成功采样缺口（中危）**：`start_record` 解析成功分支补报 `record_success(record_host)`（与失败分支对称）
- **直下路径熔断采样缺口（P1）**：`main.py` 直下下载分支「非 200 / 网络异常」失败原在函数内部消化为 `False`、调用方不上报样本…
- **调度器线程安全 + 类型/日志**：`ConcurrencyScheduler` 配置字段加锁（单次加锁快照 + 锁内写入）
- **直下日志缺失修复**：`main.py` 的 `direct_download_stream` 非 200 分支补请求 URL、异常分支补 `{type(e).__name__}`（Windows 超时类 `str()` 为空）
- **弹幕参数每轮重置恢复**：`main.py` 内层监测循环顶部恢复 `record_danmaku_args = None`（此前重构合并了轮内重置点）。
- **损坏 YAML 目录致 500**：`_load_yaml_catalog()` 补捕获 `yaml.YAMLError`（非 OSError/ValueError 子类），降级跳过到下一格式。
- **ISSUE_TEMPLATE 版本缺失**：`.github/ISSUE_TEMPLATE` 四个模板 Python 版本下拉补 `Python 3.14`。
- **i18n 提取器两处噪声源**：`scripts/extract_i18n_strings.py` 的 `is_valuable()` 改以花括号块之外的残渣判定（纯占位符模板如 `{color}{text}` 不再误报为缺失）、po 头部空 `msgid ""` 比对前剔除（消除四语一致性「少 1」假阳性）

**🎨 体验优化**
- **前端硬编码中文入翻译字典**：`web/app.js` 约十处硬编码中文字符串改走内嵌四语字典 `t()`（录制/弹幕空态、截断提示、开关/操作 toast、配置/文件列表空态、进入/下载按钮等）
- **GUI 崩溃弹窗去重**：`gui.py` 顶层异常不再双弹窗/日志双份堆栈，`_bootstrap_error_sink` 置位标记后 re-raise 触发的 excepthook 据此跳过。

**🔧 CI / 工程维护**
- **CI 工作流优化（ci.yml 重写…
- **仓库元数据八文件同步**：requirements.txt / Dockerfile 过时的 `src/danmaku/` 路径注释修正为实际模块位置…

**🧪 测试与验证**
- 新增 `tests/test_record_failure_feedback.py`（5 → 7 用例）、`tests/test_web_api.py` 缺键补建/边界用例…
- 全量 `pytest` **744 passed / 2 skipped**…

### v4.0.9 (2026-08-23 ~ 2026-08-24) — 高并发多平台录制调度优化 / 录制反馈闭环 / 并发双模式 / Python 3.14 升级与语言键迁移 / 四语本地化目录统一与英式美式分流 / 类型与 CI 质量门禁修复

> 本批改动聚焦高并发（80+ 任务）多平台录制的调度中枢治理、录制侧反馈闭环与 Python 3.14 基线升级。详细根因与验证见 [CODE_WIKI.md](CODE_WIKI.md)。

**🚀 高并发调度中枢（新增 src/scheduler.py）**
- 引入 `ResizableSemaphore`（运行期可重置容量）、`PlatformBreaker`（按 host 熔断器…
- 取代旧「全局固定 3 槽信号量 + 单向错误率压制」模型，支持 80+ 任务跨多平台录制、降低排队延迟；单平台接口抖动被隔离降级，不再连锁拖垮全局。
- 仅在 `main.py` / `notify.py` 固定接线点接入，未改写 50+ 平台分派/录制函数，向后兼容；新增配置项「最大同时录制数(0=不限制)」（默认 0=不限制）。

**🔁 录制结果反馈闭环（虎牙 403 死循环根治）**
- 修复录制侧反馈缺失：`check_subprocess` 此前按退出码既不上报失败样本、轮末还无条件上报成功…
- 现按退出码上报成功/失败样本（按 host）
- 控制台状态行改为显示调度器实时并发容量（`_live_network_capacity`），不再误显配置值。

**⚙️ 网络并发双模式（动态调速 / 固定并发）**
- 在自适应容量基础上新增「固定并发」模式：「最大同时录制数(0=不限制)」兼作模式开关——=0 启用动态调速（随活跃任务数自适应、下限 8/上限 128）
- 按 host 平台熔断与模式正交，两种模式下均生效；同时录制上限仍由 `scheduler.set_recording_limit` 管控，不受模式切换影响。

**🐍 Python 3.14 升级 + 语言配置键迁移（综合维护）**
- 项目基线由 Python 3.10 提升至 `>=3.14`（`pyproject.toml` / `Dockerfile` / CI 全链路）
- `config.ini` 语言键 `language(zh_cn/en)` 统一迁移为 `language`：留空跟随系统语言、非法值回退 en_US、GUI/Web 面板免重启热切换、启动自动迁移旧键。
- 修复 14 个源文件共 21 处 Python 2 风格 `except A, B:` 残留语法…

**🌐 四语本地化目录统一与英式/美式英语分流**
- 统一 zh_CN.po / en_US.json / en_GB.json / zh_TW.yaml 四份目录为同一 288 条 key 集合（原 282 条 + 补齐 build_exe.py 的 6 条打包/冒烟常量串）。
- 修正 en_US 内部混用的英式拼写（统一为美式 minimizes/minimized/canceled）
- 重新编译 zh_CN.po → zh_CN.mo（compile_po.py --check 确认字节级同步），不影响任何运行时逻辑。

**🧪 类型检查 / CI 质量门禁修复**
- 修复 CI `mypy src/` 两处报错：`i18n.py` 的 `ctypes.WinDLL` 平台门控（`sys.platform != "win32"` 早返回…
- 修复 CI `pytest` 在 C/POSIX locale 下 `detect_system_language()` 回退路径未过滤 `("C","POSIX")` 导致断言失败…
- 修复 `src/config_io.py` 的 `read_config_value()` 在 Python 3.14 下含分隔符键 `write()` 抛 `InvalidWriteError` 的写回崩溃（内存完整序列化成功后才落盘，坏键回滚）。
- 全仓 black 26.5.1 + `target-version=['py314']` 重排（剥除 PEP 758 `except (A, B):` 括号），本地 dev venv 升级至 3.14.7；四大门禁在 3.14 环境全绿。

**📦 构建 / 依赖 / 平台适配**
- 版本号 `4.0.8.3` → `4.0.9`（唯一事实源）；`requires-python` 升 `>=3.14`、classifiers 收敛为仅 3.14；新增 `PyYAML>=6.0.3` 依赖（i18n 的 zh_TW.yaml 支持）。
- `Dockerfile` 基础镜像升 `python:3.14-slim-bookworm`、Node.js 源 `setup_22.x` → `setup_24.x`；CI 矩阵同步升 3.14。
- `src/spider.py` 咪咕 `get_migu_stream_url()` 现采用重写版 `migu.js` 输出带 `ddCalcu`/`sv` 参数的完整地址（移除本地过期固定 `sv=10010`）

### v4.0.8.3 (2026-08-19 ~ 2026-08-22) — 主播名自动更新 / SSL 配置整合 / 四语国际化 / FFmpeg9·Node24 兼容 / 类型安全加固 / start_record 复杂度治理 / 窗口化崩溃加固 / 类型检查缺陷修复

> 本版本在 4.0.8.2 系列修复基础上补齐多项新增能力与底层兼容，并以 mypy / basedpyright / pytest(0 warnings) / black / isort 五工具门禁全绿收口。详细根因与验证见 [CODE_WIKI.md](CODE_WIKI.md)。

**👤 主播名自动更新（新增功能）**
- `URL_config.ini` 每次解析到最新主播名时…
- 新增 `src/config_io.py:update_anchor_name` + `main.py:rename_anchor_directory`

**🔒 SSL / HTTPS 配置整合**
- 旧「是否强制启用https录制」+「是否禁用SSL证书验证(是/否)」合并为单一「是否启用https录制」：开启 = https 拉流 + 跳过证书校验…
- 主循环每轮热同步 `set_https_recording` / `set_ssl_verify`；关闭时 `https://`→`http://`（TikTok/YouTube 等 https-only 海外平台保持原样，避免必然拉流失败）。
- 平台级覆盖 `禁用SSL证书验证的平台(逗号分隔)` 仅在 http 模式（需要证书校验时）生效…

**🌐 国际化四语重构 + 即时切换**
- `i18n.py` 重构：多格式目录加载（gettext `.mo` → `<lang>.json` → `<lang>.yaml`）、`SUPPORTED_LANGUAGES`（zh_CN/en_US/en_GB/zh_TW）、`normalize_language()` 别名归一、`set_language()` 热切换（无需重启）。
- zh_CN 目录补全至 282 条…

**⚙️ FFmpeg 9.0 / Node 24 兼容基线**
- 全库 ffmpeg 命令核查对齐 FFmpeg 9.0（2026-08-04 发布…
- `src/javascript/migu.js` 全量重写：适配咪咕播放器 mgprtcl.wasm 接口变更（导入函数 3→12、导出名重排、加密因子改由接口下发）

**🧪 类型安全加固（五工具全绿）**
- mypy tests/ 由 435 errors → 0（自动注解约 420 处 + 人工修复约 60 处真实类型问题）
- 新增测试覆盖：语言 API 5 个、i18n 新功能 10 个、SSL 平台自动追加 3 个、SSL 新语义 2 个、migu 输出契约 1 个、主播名自动更新 21 个。

**🧹 start_record 复杂度治理（代码质量）**
- `main.py:start_record`（原约 1600 行）的平台分派 if/elif 链（52 平台分支）抽取为独立模块级函数 `_resolve_platform_stream`

**🧩 类型检查缺陷修复（代码质量）**
- `i18n.py`：`import yaml` 加 `# type: ignore[import-untyped]` 忽略可选依赖缺失存根提示（保留「缺失仅损失 YAML 格式」的运行时降级语义…
- `gui.py`：`messagebox` 由属性式 `_tk.messagebox` 改为显式 `from tkinter import messagebox as _mb` 导入（两处崩溃弹窗）
- 验证：`mypy i18n.py` → `Success: no issues found`；`basedpyright gui.py` → 0 errors / 0 warnings / 0 notes；`black --check` / `isort --check-only` 通过；运行时行为不变。

**🪟 窗口化运行崩溃可观测性加固（缺陷修复）**
- 修复 `pythonw.exe`（及 `console=False` 冻结 exe）启动 GUI 时**完全无窗口、无任何报错**的问题：根因为 `src/logger.py` 在导入期 `logger.add(sink=sys.stderr, ...)` 遇 `sys.stderr=None` 抛 `TypeError: Cannot log to objects of type 'NoneType'`
- `gui.py` 顶部新增 `_install_crash_sink()`：在**所有风险导入之前**装 `sys.excepthook` / `threading.excepthook`
- 验证：模拟 `sys.stderr=None` 下 `import src.logger` 成功、注册 2 个文件 sink、不抛 `TypeError`；`py_compile` 与 `black --check` 均通过。

**📚 架构文档更新**
- `CODE_WIKI.md` 补全弹幕采集子系统（基类/采集器/5 平台客户端/监控枢纽/SRT/WS/访客 Cookie 缓存/protobuf）、`src/platforms` 与 `src/proto` 模块说明、模块依赖图与设计模式…

### v4.0.8.2 (2026-08-16 ~ 2026-08-18) — 录制/弹幕/国际化/类型检查 系列修复

> 本批改动集中解决了多个历史遗留的「能跑但录制/弹幕经常失败」类问题，并通过真机实测闭环验证。下分模块概述，详细根因与验证见 [CODE_WIKI.md](CODE_WIKI.md)。

**🎯 录制引擎核心修复（影响所有平台）**
- **致命结构 Bug**：录制主链曾被嵌套在 `if headers:` 条件内…
- **斗鱼崩溃修复**：`select_source_url` 返回空时不再触发 `UnboundLocalError`（标题变量未绑定）
- **流地址校验三层降风控**：新增「探针节流 + 重试抖动 + 被拒后退避（仅虎牙）」机制…
- **HTTPS/SSL 配置整合**：`是否启用https录制`（合并原 `是否强制启用https录制` 与 `是否禁用SSL证书验证(是/否)`）——开启 = https 拉流 + 跳过证书校验…

**🐯 虎牙专项（多 CDN 选源 + Referer 纠偏）**
- 改为**枚举全部 CDN 候选**（HS/HW/TX/AL）
- **Referer 规则已移除**：实测虎牙 CDN 现已反向校验——**带 Referer 一律 403…
- App 路径（`get_huya_app_stream_url`）TX 选中时与 `record_url` 一致地做 `tars_mp→huya_webh5`/`bhct→bgct` 参数替换…

**📺 B站弹幕认证链闭环**
- 修复 spi 端点拼写（`/finger/sp` → `/finger/spi`
- 弹幕进房包**观众 uid 误传主播 uid** 导致 AUTH 软拒绝（连接保持、0 弹幕）已修复…
- 弹幕三元组（OD/BD/UHD app 路径）返回补全，消除原静默跳过。

**🌐 国际化机制修复**
- 补齐缺失的 `zh_CN.mo` 编译产物并随仓库分发…

**🍪 访客 Cookie 统一缓存**
- 新增 `src/cookie_cache.py`：以「归一化网址 + 代理」为 key 的进程级共享缓存…

**🧩 架构与质量**
- `main.py` 拆分 6 类功能至 `src/` 子模块（ffmpeg_proc / video_postprocess / stream_select / notify / recorder_status / config_io）
- 配置健壮性：`config.ini` 不可写时 `import main` 阶段不再崩溃（读回 best-effort）；旧键兼容仅读取不写回；备份旋转删除改为 best-effort。
- 全库 UA 统一升级至 2026 基准（Chrome/141、Firefox/148、移动端 Android 14 Chrome/141），消除过旧指纹。

**🛡️ 平台兼容与运行健壮性**
- **跨事件循环锁误判风控根治**（`src/async_http.py`）：模块级单例 `asyncio.Lock()` 在首个 room 的 `asyncio.run()` 循环惰性绑定后…
- **空白异常日志收口**：`async_req` / `_close_all_clients` 及跨循环旧 client 关闭处原为 `logger.debug(e)`
- **平台兼容修复**：`web.py` 的 ctypes 3.13+ 兼容（`windll` 已移除）+ 64 位 `HWND` 截断导致控制台窗口隐藏失败…

**🧪 静态检查 / CI 加固**
- mypy / basedpyright 在 `src/` 与 `main.py` 全面清零（含 spider.py / sync_http.py / web_api.py `_FAILED_LOGINS` 补全 `deque` 类型参数消除 10 处级联告警）
- 脚本健壮性：`scripts/check_coverage.py` 修复全局覆盖率 < 50% 时门禁被跳过、临时文件残留、`subprocess.run` 缺 `encoding`（Windows 非 UTF-8 locale 崩溃）
- CI `lint` job 运行 Python 由 3.12 升到 3.13（与 `target-version` 最高值对齐，消除 AST 安全校验告警噪声），`black --check .` 格式违规已手工修复。
- 全量测试约 635 passed / 2 skipped（排除已知沙箱删除保护项）。

### v4.0.8.1 (2026-08-01 ~ 2026-08-09) — 注释规范 / 冒烟测试 / GUI 优雅退出 / 校验修复 整合

- 模块/函数说明统一使用 `#` 行注释，不再使用三引号 `"""` 文档字符串。
- 全量审查通过：`compileall` / `black`(行宽120) / `isort` / `mypy`(src/) / `pytest` 全绿（417 passed…
- ⚠️ **构建 Bug 修复（`pyproject.toml`）**：`email="ihmily@github"` 非合法 IDN 邮箱…

**新增 Web/接口冒烟测试工具**
- `scripts/smoke_test.py`（**零依赖、配置驱动**）：支持 GET/POST、`base_url` 拼接、期望状态码、文本/JSON 断言…

**GUI 停止录制优雅退出加固**
- **根因**：`pythonw.exe` 启 GUI 时 `sys.executable` 指向无控制台的 pythonw…
- CTRL_BREAK 失败改 `taskkill /F /T /PID` 整树终止（连同 ffmpeg 清理），日志如实区分「优雅退出」与「硬杀路径」。
- 实测：pythonw 父进程复现后 `AttachConsole` 成功、`SIGBREAK` 处理器触发（`signum=21`）
- ⚠️ **遗留（未改）**：旧 `gui_legacy.py` 用 `CREATE_NO_WINDOW` 启子进程…

**流地址校验修复（HLS/代理/日志）**
- 空白日志收口：`get_response_status` 异常日志现带 URL 与异常类型（如 `ConnectTimeout`/`TimeoutError`），消除 Windows 下 `socket.timeout` 的 `str()` 为空只打空白。
- m3u8 误判修复：HEAD 探测范围从 `400/401/403/405` 扩至**含 404 的所有非 2xx**…
- `_validate_stream_url` 新增 `verify` 参数沿用全局 SSL 开关，所有失败路径记 warning（URL + 异常类型/状态码/content-type）。
- `select_source_url` 新增 `proxy_addr` 并透传三处校验，修复 TikTok 等需代理平台直连校验超时误判不可达。

**抖音录制增强**
- 支持 5 种 URL 格式：网页/App 直播间、抖音号拼接（含 VR）、App/网页端主播主页。
- 主播主页（格式 5）直接提取 `sec_user_id` 跳重复下载…
- CDN 对 HEAD 返 4xx 时补 `Range` GET 探测…

### v4.0.8 (2026-07-30) — Web 面板 / 画质监控 / 代理与类型修复

- **新增 Web 管理面板**（`web.py`+`src/web_api.py`+`src/web_config.py`+`web/`）：仪表盘、直播间管理、配置编辑、SSE 日志推送。
- **新增 GUI 画质监控**：实时检测实际画质是否匹配设置，覆盖抖音/TikTok/快手/虎牙/斗鱼/B站/网易CC 七平台。
- **配置项新增**：`web_show_console`（后台隐藏运行）、SSL 证书验证全局开关（config.ini）、日志文件开关。
- **连接优化**：HTTP 客户端按 (代理, verify, http2) 维度复用连接池；代理检测从联网探测改为读本地系统代理配置。
- **缺陷修复**：`trace_error_decorator` 同步装饰器误用于 71 个异步函数致错误捕获失效…
- **凭据清理**：硬编码过期凭据改自动获取（抖音 ttwid、快手 did、Twitch Client-Id 等）。
- **构建/依赖**：Dockerfile 升 Node.js 22 LTS、非 root 运行；新增 `pydantic>=2.0.0` 依赖声明；全项目类型检查（Pyright/Pyrefly/basedpyright）清理。

### v4.0.7 (2025-10-24)

- 修复抖音风控无法获取数据问题
- 新增 soop.com 录制支持
- 修复 bigo 录制

### v4.0.6 (2025-01-27)

- 新增淘宝、京东、faceit 直播录制
- 修复小红书直播流录制以及转码问题
- 修复畅聊、VV星球、flexTV 直播录制
- 修复批量微信直播推送
- 新增 email 发送 ssl 和 port 配置
- 新增强制转 h264 配置
- 更新 ffmpeg 版本
- 重构包为异步函数！

### v4.0.5 (2024-11-30)

- 新增 shopee、youtube 直播录制
- 新增支持自定义 m3u8、flv 地址录制
- 新增自定义执行脚本，支持 python、bat、bash 等
- 修复 YY 直播、花椒直播和小红书直播录制
- 修复 b 站标题获取错误
- 修复 log 日志错误

### v4.0.4 (2024-10-30)

- 新增嗨秀直播、vv星球直播、17Live、浪Live、SOOP、畅聊直播、飘飘直播、六间房直播、乐嗨直播、花猫直播等 10 个平台直播录制
- 修复小红书直播录制，支持小红书作者主页地址录制直播
- 新增支持 ntfy 消息推送，以及新增支持批量推送多个地址
- 修复 Liveme 直播录制、twitch 直播录制
- 新增 Windows 平台一键停止录制 VB 脚本程序

### v4.0.3 (2024-10-05)

- 新增邮箱和 Bark 推送
- 新增直播注释停止录制
- 优化分段录制
- 重构部分代码

### v4.0.2 (2024-09-28)

- 新增知乎直播、CHZZK 直播录制
- 修复音播直播录制

### v4.0.1 (2024-09-03)

- 新增抖音双屏录制、音播直播录制
- 修复 PandaTV、bigo 直播录制

### v4.0.0 (2024-07-13)

- 新增映客直播录制

### 更多历史版本...

</details>

## 💬 有问题或者需求可以向我提 Issue，欢迎 Star 与 Fork

[![Star History Chart](https://api.star-history.com/svg?repos=y123ao6/DouyinLiveRecorder&type=Timeline)](https://star-history.com/#y123ao6/DouyinLiveRecorder&Timeline)
