![video_spider](https://socialify.git.ci/ihmily/DouyinLiveRecorder/image?font=Inter&forks=1&language=1&owner=1&pattern=Circuit%20Board&stargazers=1&theme=Light)

## 简介

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Supported Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg)](https://github.com/ihmily/DouyinLiveRecorder)
[![Docker Pulls](https://img.shields.io/docker/pulls/ihmily/douyin-live-recorder?label=Docker%20Pulls&color=blue&logo=docker)](https://hub.docker.com/r/ihmily/douyin-live-recorder/tags)
![GitHub issues](https://img.shields.io/github/issues/ihmily/DouyinLiveRecorder.svg)
[![Latest Release](https://img.shields.io/github/v/release/ihmily/DouyinLiveRecorder)](https://github.com/ihmily/DouyinLiveRecorder/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/ihmily/DouyinLiveRecorder/total)](https://github.com/ihmily/DouyinLiveRecorder/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/ihmily/DouyinLiveRecorder?style=flat-square)](https://github.com/ihmily/DouyinLiveRecorder/stargazers)

一款简易的可循环值守的直播录制工具，基于 FFmpeg 实现多平台直播源录制，支持自定义配置录制以及直播状态推送。

## 功能特性

| 功能 | 说明 |
|------|------|
| 多平台支持 | 支持抖音、TikTok、YouTube、快手、虎牙、斗鱼、B站等 **60+ 平台** |
| 循环值守 | 自动检测直播状态，开播自动录制，断播自动停止 |
| 多种格式 | 支持 TS、MKV、FLV、MP4、MP3、M4A 等格式输出 |
| 双模式运行 | 支持命令行模式和 GUI 图形界面模式 |
| 消息推送 | 支持钉钉、微信、邮箱、TG、Bark、NTFY、PushPlus 等推送 |
| Docker 支持 | 支持 Docker 容器化部署，开箱即用 |
| 国际化 | 支持中文、英文等多语言界面 |
| 灵活配置 | 支持按直播间自定义画质、格式、分段录制等 |

## 快速开始

### 方式一：下载运行包（推荐新手）

1. 进入 [Releases](https://github.com/ihmily/DouyinLiveRecorder/releases) 下载最新发布的 zip 压缩包
2. 解压后，在 `config` 文件夹内的 `URL_config.ini` 中添加直播间地址
3. 运行 `DouyinLiveRecorder.exe` 开始录制

### 方式二：源码运行（推荐开发者）

```bash
# 克隆项目
git clone https://github.com/ihmily/DouyinLiveRecorder.git
cd DouyinLiveRecorder

# 安装依赖（推荐使用 uv）
uv sync

# 或者使用 pip
pip install -r requirements.txt

# 运行程序
python main.py       # 命令行模式
python gui.py        # GUI 模式
```

### 方式三：Docker 运行

```bash
# 快速启动
docker-compose up -d

# 或本地构建并启动
docker build -t douyin-live-recorder .
docker run -d douyin-live-recorder
```

## 已支持平台

- [x] 抖音
- [x] TikTok
- [x] 快手
- [x] 虎牙
- [x] 斗鱼
- [x] YY
- [x] B站
- [x] 小红书
- [x] bigo
- [x] blued
- [x] SOOP（原AfreecaTV）
- [x] 网易cc
- [x] 千度热播
- [x] PandaTV
- [x] 猫耳FM
- [x] Look直播
- [x] WinkTV
- [x] TTingLive（原Flextv）
- [x] PopkonTV
- [x] TwitCasting
- [x] 百度直播
- [x] 微博直播
- [x] 酷狗直播
- [x] TwitchTV
- [x] LiveMe
- [x] 花椒直播
- [x] 流星直播
- [x] ShowRoom
- [x] Acfun
- [x] 映客直播
- [x] 音播直播
- [x] 知乎直播
- [x] CHZZK
- [x] 嗨秀直播
- [x] vv星球直播
- [x] 17Live
- [x] 浪Live
- [x] 畅聊直播
- [x] 飘飘直播
- [x] 六间房直播
- [x] 乐嗨直播
- [x] 花猫直播
- [x] Shopee
- [x] YouTube
- [x] 淘宝
- [x] 京东
- [x] Faceit
- [x] 咪咕
- [x] 连接直播
- [x] 来秀直播
- [x] Picarto
- [ ] 更多平台正在更新中

## 项目结构

```
DouyinLiveRecorder/
├── config/                     # 配置文件目录
│   ├── config.ini             # 主配置文件（录制/推送/Cookie）
│   └── URL_config.ini         # 直播间地址列表
├── src/                        # 核心源码包
│   ├── __init__.py            # 包初始化（Node.js 环境配置）
│   ├── spider.py              # 直播数据获取（各平台异步 API）
│   ├── stream.py              # 直播流解析（URL 提取、画质选择）
│   ├── room.py                # 直播间信息（URL 解析、房间 ID）
│   ├── utils.py               # 工具函数（配置读写、文件操作）
│   ├── logger.py              # 日志配置（Loguru 集成）
│   ├── proxy.py               # 代理检测（Win 注册表 / Linux 环境变量）
│   ├── ab_sign.py             # 抖音签名算法（SM3、RC4、A-Bogus）
│   ├── initializer.py          # 环境初始化（Node.js 自动安装）
│   ├── weverse_auth.py        # Wevers 认证模块
│   ├── http_clients/          # HTTP 客户端
│   │   ├── __init__.py
│   │   ├── async_http.py      # 异步 HTTP（httpx）
│   │   └── sync_http.py       # 同步 HTTP
│   └── javascript/             # JavaScript 签名脚本
│       ├── crypto-js.min.js   # CryptoJS 库
│       └── x-bogus.js         # 抖音 X-Bogus 签名
├── downloads/                  # 录制文件保存目录
├── logs/                       # 日志文件目录
├── i18n/                       # 国际化文件
│   ├── zh_CN/LC_MESSAGES/
│   │   ├── zh_CN.po          # 中文翻译源文件
│   │   └── zh_CN.mo          # 编译后的翻译文件
│   └── en/LC_MESSAGES/
├── ffmpeg/                     # FFmpeg 目录（Windows 内置）
├── node/                       # Node.js 目录（Windows 内置）
├── main.py                     # 命令行入口
├── gui.py                      # GUI 图形界面入口
├── msg_push.py                 # 消息推送模块
├── ffmpeg_install.py           # FFmpeg 安装脚本
├── demo.py                     # 调用示例
├── i18n.py                     # 国际化实现
├── requirements.txt            # Python 依赖
├── pyproject.toml             # Python 项目配置
├── Dockerfile                  # Docker 构建文件
├── docker-compose.yaml         # Docker Compose 配置
├── StopRecording.vbs          # Windows 停止录制脚本
├── .dockerignore              # Docker 构建排除
├── .gitignore                 # Git 版控排除
├── CODE_WIKI.md               # 项目架构文档
├── CODE_CHANGES.md            # 代码改动记录
└── README.md                   # 项目说明文档
```

## 配置说明

### 基础配置 (config/config.ini)

```ini
[录制设置]
# 同时检测直播的线程数
同一时间访问网络的线程数 = 3

# 是否开启代理录制（是/否）
使用代理录制的平台 = tiktok,sooplive,youtube...

# 录制分段时长（秒），0 为不分段
视频分段时间(秒) = 0

# 是否开启分段录制（是/否）
分段录制是否开启 = 否

# 录制视频质量（原画/超清/高清/标清/流畅）
原画|超清|高清|标清|流畅 = 原画

# 录制视频格式（ts/mkv/flv/mp4/mp3音频/m4a音频）
视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频 = ts

# 下载保存路径
直播保存路径(不填则默认) =

# 循环监测间隔（秒）
循环时间(秒) = 300

# 是否仅推送开播通知（是/否）
只推送通知不录制(是/否) = 否
```

### 直播间配置 (config/URL_config.ini)

```
# 基础格式
https://live.douyin.com/745964462470

# 指定画质（画质,直播间地址）
超清，https://live.douyin.com/745964462470

# 指定画质和主播名（画质,直播间地址,主播:名称）
高清，https://live.bilibili.com/123456，主播: B站主播

# 注释直播间（在地址前加 #）
# https://live.douyin.com/123456789
```

### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `PYTHONUNBUFFERED` | 实时输出日志 | `1` |
| `PYTHONDONTWRITEBYTECODE` | 不生成 .pyc 文件 | `1` |
| `PYTHONIOENCODING` | Python 输出编码 | `utf-8` |
| `TZ` | 时区设置 | `Asia/Shanghai` |

## 使用说明

### 命令行模式

```bash
python main.py
```

### GUI 图形界面模式

```bash
python gui.py
```

### 录制格式推荐

- **长时间录制**：推荐使用 `ts` 格式，实时写入，断电不易损坏
- **短时间录制**：推荐使用 `mp4` 或 `mkv` 格式，录制完成后直接可用
- **仅音频录制**：推荐使用 `mp3` 或 `m4a` 格式

### 停止录制

- **Windows**：执行 `StopRecording.vbs` 或在命令行按 `Ctrl+C`
- **Linux/macOS**：在命令行按 `Ctrl+C`
- **Docker**：执行 `docker-compose stop`

### 注意事项

1. 如需录制 TikTok、AfreecaTV 等海外平台，请在配置中开启代理
2. 长时间挂机建议将循环时间设置长一些（如 60 秒），避免请求频繁被封 IP
3. 直播结束后会自动保存文件，无需手动停止
4. 如遇录制的视频文件损坏，建议使用 `ts` 格式录制
5. Docker 部署时请确保 `config/` 目录中的配置文件已正确填写

## Docker 部署

### 前置要求

- 已安装 [Docker](https://docs.docker.com/get-docker/)
- 已安装 [Docker Compose](https://docs.docker.com/compose/install/)

### 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/ihmily/DouyinLiveRecorder.git
cd DouyinLiveRecorder

# 2. 编辑配置文件（在 config/URL_config.ini 中添加直播间地址）

# 3. 启动容器
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

### 数据挂载

配置文件和数据通过卷挂载到宿主机：

```yaml
volumes:
  - ./config:/app/config         # 配置文件
  - ./downloads:/app/downloads   # 录制文件
  - ./logs:/app/logs             # 日志文件
  - ./backup_config:/app/backup_config  # 配置备份
```

## 开发指南

### 环境要求

- Python >= 3.10
- FFmpeg（Linux/macOS 需手动安装，Windows 已内置）
- Node.js（Windows 自动安装，Linux 需通过包管理器安装）

### 安装开发依赖

```bash
# 使用 uv（推荐）
uv sync --dev

# 或使用 pip
pip install -r requirements.txt
pip install pytest black isort mypy
```

### 代码规范

```bash
# 格式化代码
black .

# 排序导入
isort .

# 类型检查
mypy .

# 运行测试
pytest
```

### 项目文档

- [CODE_WIKI.md](CODE_WIKI.md) - 项目架构文档
- [CODE_CHANGES.md](CODE_CHANGES.md) - 代码改动记录

## 常见问题

**Q: 录制时提示 "缺少 ffmpeg 无法进行录制"**

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 程序已自带 ffmpeg，无需安装
```

**Q: 提示 "IP 被禁止，请更换设备或网络"**

- 检查是否开启了代理
- 降低循环监测频率
- 等待一段时间后再尝试

**Q: 录制的视频文件损坏**

- 推荐使用 `ts` 格式录制
- 检查磁盘空间是否充足
- 检查网络是否稳定

**Q: 如何只推送开播通知不录制？**

在 `config.ini` 中设置 `只推送通知不录制(是/否) = 是`

**Q: Docker 容器无法运行 / 报 Node.js 错误？**

新版本 Dockerfile 已自动在运行阶段包含 Node.js 运行时。如仍遇问题请使用最新镜像。

## 相关项目

- [StreamCap](https://github.com/ihmily/StreamCap) - 直播录制工具
- [streamget](https://github.com/ihmily/streamget) - 流媒体获取工具

## 贡献者

&ensp;&ensp; [![Hmily](https://github.com/ihmily.png?size=50)](https://github.com/ihmily)
[![iridescentGray](https://github.com/iridescentGray.png?size=50)](https://github.com/iridescentGray)
[![annidy](https://github.com/annidy.png?size=50)](https://github.com/annidy)
[![wwkk2580](https://github.com/wwkk2580.png?size=50)](https://github.com/wwkk2580)
[![missuo](https://github.com/missuo.png?size=50)](https://github.com/missuo)
<a href="https://github.com/xueli12" target="_blank"><img src="https://github.com/xueli12.png?size=50" alt="xueli12" style="width:53px; height:51px;" /></a>
<a href="https://github.com/kaine1973" target="_blank"><img src="https://github.com/kaine1973.png?size=50" alt="kaine1973" style="width:53px; height:51px;" /></a>
<a href="https://github.com/yinruiqing" target="_blank"><img src="https://github.com/yinruiqing.png?size=50" alt="yinruiqing" style="width:53px; height:51px;" /></a>
<a href="https://github.com/Max-Tortoise" target="_blank"><img src="https://github.com/Max-Tortoise.png?size=50" alt="Max-Tortoise" style="width:53px; height:51px;" /></a>
[![justdoiting](https://github.com/justdoiting.png?size=50)](https://github.com/justdoiting)
[![dhbxs](https://github.com/dhbxs.png?size=50)](https://github.com/dhbxs)
[![wujiyu115](https://github.com/wujiyu115.png?size=50)](https://github.com/wujiyu115)
[![zhanghao333](https://github.com/zhanghao333.png?size=50)](https://github.com/zhanghao333)
<a href="https://github.com/gyc0123" target="_blank"><img src="https://github.com/gyc0123.png?size=50" alt="gyc0123" style="width:53px; height:51px;" /></a>

&ensp;&ensp; [![HoratioShaw](https://github.com/HoratioShaw.png?size=50)](https://github.com/HoratioShaw)
[![nov30th](https://github.com/nov30th.png?size=50)](https://github.com/nov30th)
[![727155455](https://github.com/727155455.png?size=50)](https://github.com/727155455)
[![nixingshiguang](https://github.com/nixingshiguang.png?size=50)](https://github.com/nixingshiguang)
[![1411430556](https://github.com/1411430556.png?size=50)](https://github.com/1411430556)
[![Ovear](https://github.com/Ovear.png?size=50)](https://github.com/Ovear)
&emsp;

## 许可证

本项目基于 [MIT License](LICENSE) 开源，欢迎 Star 和 Fork！

## 更新日志

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
- 重构包为异步函数

### v4.0.5 (2024-11-30)

- 新增 shopee、youtube 直播录制
- 新增支持自定义 m3u8、flv 地址录制
- 新增自定义执行脚本，支持 python、bat、bash 等
- 修复 YY 直播、花椒直播和小红书直播录制
- 修复 b 站标题获取错误
- 修复 log 日志错误

<details><summary>点击展开更多历史版本</summary>

### v4.0.4 (2024-10-30)

- 新增嗨秀直播、vv星球直播、17Live、浪Live、SOOP、畅聊直播、飘飘直播、六间房直播、乐嗨直播、花猫直播等 10 个平台
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

</details>

&emsp;

## 问题反馈

有问题可以提 Issue，我会在这里持续添加更多直播平台的录制，欢迎 Star！

[![Star History Chart](https://api.star-history.com/svg?repos=ihmily/DouyinLiveRecorder&type=Timeline)](https://star-history.com/#ihmily/DouyinLiveRecorder&Timeline)