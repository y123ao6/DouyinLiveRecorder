![video_spider](https://socialify.git.ci/y123ao6/DouyinLiveRecorder/image?font=Inter&forks=1&language=1&owner=1&pattern=Circuit%20Board&stargazers=1&theme=Light)

English&nbsp;&nbsp;|&nbsp;&nbsp;[简体中文](/README.md)

## 💡 Introduction

[![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Supported Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg)](https://github.com/y123ao6/DouyinLiveRecorder)
[![GitHub issues](https://img.shields.io/github/issues/y123ao6/DouyinLiveRecorder.svg)](https://github.com/y123ao6/DouyinLiveRecorder/issues)
[![Latest Release](https://img.shields.io/github/v/release/y123ao6/DouyinLiveRecorder)](https://github.com/y123ao6/DouyinLiveRecorder/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/y123ao6/DouyinLiveRecorder/total)](https://github.com/y123ao6/DouyinLiveRecorder/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/y123ao6/DouyinLiveRecorder?style=flat-square)](https://github.com/y123ao6/DouyinLiveRecorder/stargazers)

A **lightweight** loop-monitoring live-stream recording tool that uses FFmpeg to record live sources from multiple platforms, supporting custom recording configuration and live-status notifications.

Upstream project: [ihmily/DouyinLiveRecorder](https://github.com/ihmily/DouyinLiveRecorder)

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **Multi-platform support** | Supports 51 platforms including Douyin, TikTok, YouTube, Kuaishou, Huya, Douyu, Bilibili, etc. (marketed as 60+, more being added) |
| 🔄 **Loop monitoring** | Automatically detects live status — starts recording when live and stops when offline |
| 🎬 **Multiple formats** | Supports TS, MKV, FLV, MP4, MP3, M4A and other output formats |
| 🖥️ **Three run modes** | CLI mode, GUI mode, and Web management panel mode |
| 📊 **Quality monitoring** | Real-time detection of each room's actual quality, with automatic alerts on quality degradation |
| 💬 **Danmaku recording** | Captures danmaku from Douyin / Douyu / Huya / Bilibili / TwitchTV, outputting SRT subtitles per segment, synced with video start/stop |
| 👀 **Danmaku monitoring** | Standalone real-time danmaku viewer (not persisted to disk); viewable in both GUI and Web panel |
| 🏷️ **Auto anchor-name update** | When an anchor renames, automatically syncs `URL_config.ini` and renames the recording directory and files |
| 📱 **Message push** | Supports DingTalk, WeChat, email, Telegram, Bark, NTFY, PushPlus, etc. |
| 🐳 **Docker support** | Supports Docker containerized deployment, ready to use out of the box |
| 🌐 **Internationalization** | Built-in Simplified Chinese / English (US) / English (UK) / Traditional Chinese, with restart-free hot switching in GUI and Web panel |
| ⚙️ **Flexible config** | Per-room customization of quality, format, segmented recording, etc., with hot-reload of config changes |
| 🔐 **Web security** | Token auth, login brute-force rate limiting, path-traversal protection, sensitive-config masking, unauthenticated write protection |

## 🚀 Quick Start

### Method 1: Download the release package (recommended for beginners)

1. Go to [Releases](https://github.com/ihmily/DouyinLiveRecorder/releases) and download the latest released zip archive
2. After extracting, add live-room URLs to `URL_config.ini` inside the `config` folder
3. Run `DouyinLiveRecorder.exe` to start recording

### Method 2: Run from source (recommended for developers)

```bash
# Clone the project
git clone https://github.com/y123ao6/DouyinLiveRecorder.git
cd DouyinLiveRecorder

# Install dependencies (uv is recommended)
uv sync

# Or use pip
pip install -r requirements.txt

# Run the program
python main.py        # CLI mode
python gui.py         # GUI mode
python web.py         # Web management panel mode
```

### Method 3: Run with Docker

```bash
# CLI recording mode (default, no port used)
docker compose up -d

# Web management panel mode (access via browser at http://localhost:8000)
# Note: you must first set web_host = 0.0.0.0 in the [Web] section of config/config.ini,
#       and it is recommended to enable web_auth_enable = true to set an access password
docker compose --profile web up -d

# Or build locally and start
docker build -t douyin-live-recorder .
docker run -d -v ./config:/app/config -v ./downloads:/app/downloads douyin-live-recorder
```

> Inside the container, FFmpeg and Node.js are provided by the image itself (installed via apt) — no need to mount the local `ffmpeg/`, `node/` directories;
> `config/`, `downloads/`, `logs/`, and `backup_config/` are persisted via volume mounts.

### Installing ffmpeg manually (Windows user guide)

On Windows the app downloads ffmpeg from the official gyan.dev source at startup — **that is the only
automatic route** (no mirror fallback is offered, because mirror artefacts have no official digest to check
against). If the automatic install fails (usually gyan.dev unreachable, a proxy/firewall blocking it, or a
SHA256 baseline mismatch), install it yourself in three steps:

1. **Download the official zip**: <https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip>
   To verify it yourself, compare against the official digest document for that same zip,
   <https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip.sha256> (this is exactly what the
   automatic installer checks).
2. **Take the `bin` folder out of the zip, put it in the app directory and rename it to `ffmpeg`**:

   | How you run the app | Required final layout |
   | --- | --- |
   | Downloaded release package (exe) | `DouyinLiveRecorder\ffmpeg\ffmpeg.exe` |
   | From source / single-file script | `<project root>\ffmpeg\ffmpeg.exe` |

   - **Do not** leave it as `ffmpeg\bin\ffmpeg.exe` — the app adds only the `ffmpeg\` directory itself to the
     lookup path and does not search sub-directories.
   - Put `ffprobe.exe` from the same folder in there too (the release-package self-check requires both
     ffmpeg and ffprobe to be present and runnable).
3. **Verify**: run `ffmpeg -version` inside that `ffmpeg\` directory — a version banner means it works.
   Restart the app; the install took effect once `logs\streamget.log` no longer reports "ffmpeg is not installed.".

Installing system-wide works equally well (`winget install Gyan.FFmpeg`, Chocolatey, or any build you trust) —
the app also looks the binary up on `PATH`.

**When the error is a SHA256 baseline rejection** (the log says to delete something matching
`_ffmpeg_official*.zip.sha256` and retry): delete those sidecar files **in the app directory** and restart.
The sidecar records the digest seen on first download, while the gyan.dev URL is a rolling address — once
upstream ships a new build the old baseline necessarily mismatches, and removing it lets the app re-record a
baseline for the new build. (Its strength equals the write permissions of that directory, so it is not an
independent trust root and does not replace the official digest document.)

> Scope: **full** release packages already bundle ffmpeg, so normally nothing has to be installed; **lite**
> packages and the single-file script do not, and need either the automatic install or the steps above.
> On macOS/Linux the automatic install uses Homebrew / yum / apt respectively — install manually through your
> distribution if that fails. For the Apple Silicon choice between the bundled build and a native one, see the FAQ below.

## 🎈 Supported Platforms

**Domestic sites (37)**: Douyin | Kuaishou | Huya | Douyu | YY | Bilibili | Xiaohongshu | bigo | blued | NetEase CC | Qiandu Rebo | MaoerFM | Look Live | TwitCasting | Baidu | Weibo | Kugou | Huajiao | Liuxing | Acfun | Changliao | Inke | Yinbo | Zhihu | Haixiu | VV Planet | 17Live | LangLive | Piaopiao | 6Rooms | Lehai | Huamao | Taobao | JD | Migu | Lianjie | Laixiu

**Overseas sites (14)**: TikTok | SOOP (formerly AfreecaTV) | PandaTV | WinkTV | TTingLive (formerly Flextv) | PopkonTV | TwitchTV | LiveMe | ShowRoom | CHZZK | Shopee | YouTube | Faceit | Picarto

> Total of **51** platforms (marketed as 60+, including platforms being added). Platform data-fetching functions are in `src/spider.py`, and stream-URL parsing is in `src/stream.py`.

**Danmaku recording support (5 platforms)**: Douyin Live | Douyu Live | Huya Live | Bilibili Live | TwitchTV

**Actual quality re-sampling and degradation alerts (7 platforms)**: Douyin | TikTok | Kuaishou | Huya | Douyu | Bilibili | NetEase CC

## 📁 Project Structure

```
DouyinLiveRecorder/
├── config/                     # config file directory
│   ├── config.ini             # main config file
│   └── URL_config.ini         # live room URL list
├── src/                        # core source package
│   ├── __init__.py             # package init + Node.js env config + danmaku platform registry/factory
│   ├── spider.py              # live stream URL parsing (60+ platforms, danmaku logic extracted)
│   ├── stream.py              # live stream recording orchestration (ffmpeg commands/segmentation/format)
│   ├── stream_select.py       # stream source selection / reachability check / probe backoff
│   ├── scheduler.py           # concurrency scheduler hub (adaptive capacity + per-platform circuit breaker)
│   ├── room.py                # live room info parsing
│   ├── utils.py               # utility function library
│   ├── logger.py              # Loguru logging config
│   ├── proxy.py               # proxy detection
│   ├── ab_sign.py             # Douyin A-Bogus signature
│   ├── ttwid.py               # Douyin visitor ttwid fetch/cache
│   ├── node_install.py        # Node.js auto-install/init
│   ├── ffmpeg_install.py      # FFmpeg install script
│   ├── ffmpeg_master_download.py  # FFmpeg master builds (per-platform fetch + verification)
│   ├── ffmpeg_proc.py         # ffmpeg subprocess management (extracted from main.py)
│   ├── video_postprocess.py   # post-recording processing (remux/transcode)
│   ├── notify.py              # live-status message push (extracted from main.py)
│   ├── recorder_status.py     # recording status tracking (extracted from main.py)
│   ├── config_io.py           # config read/write / value conversion / backup (extracted from main.py)
│   ├── config_bool.py         # boolean config parsing (是/否 equals true/false/1/0/yes/no; dependency-free)
│   ├── cookie_cache.py        # visitor Cookie process-level shared cache
│   ├── log_archive.py         # runtime log archiving (on recording stop: four logs renamed with timestamp)
│   ├── http_config.py          # HTTP client shared config (SSL verify toggle)
│   ├── async_http.py          # async HTTP client (httpx)
│   ├── sync_http.py           # sync HTTP client
│   ├── web_api.py             # Web management panel FastAPI app
│   ├── web_config.py          # Web panel config read/write
│   ├── web_tray.py            # Web-mode system tray (minimize to tray)
│   ├── base.py               # danmaku collector base class (DanmakuBase / DanmakuMessage)
│   ├── collector.py           # danmaku collector (thread bridge to main flow)
│   ├── danmaku_monitor.py     # danmaku monitor hub (DanmakuMonitorHub)
│   ├── srt_writer.py         # danmaku time subtitle (SRT) writer
│   ├── ws_client.py          # WebSocket transport layer (danmaku direct connect, proxy=None)
│   ├── platforms/            # danmaku platform implementations (factory-registered by platform id)
│   │   ├── douyin.py         # Douyin danmaku (protobuf + _tars heartbeat)
│   │   ├── douyu.py          # Douyu danmaku (STT protocol)
│   │   ├── huya.py           # Huya danmaku (WSP protocol)
│   │   ├── bilibili.py       # Bilibili danmaku (WebSocket)
│   │   ├── twitch.py         # Twitch danmaku (IRC/WS)
│   │   ├── _tars.py          # TARS private protocol codec
│   │   └── _xbogus.py        # X-Bogus signature
│   ├── proto/                # Douyin danmaku protobuf definitions
│   │   ├── douyin.proto      # protoc source definition
│   │   ├── douyin_pb2.py      # protoc-generated (DO NOT EDIT)
│   │   └── douyin_pb2.pyi     # type stub
│   └── javascript/            # JavaScript signature scripts
│       ├── crypto-js.min.js
│       ├── x-bogus.js
│       ├── haixiu.js
│       ├── liveme.js
│       └── migu.js
├── web/                        # Web management panel frontend
│   ├── index.html              # SPA entry
│   ├── app.js                  # frontend logic (API, SSE, rendering)
│   └── style.css               # stylesheet (theme, responsive)
├── typings/                    # third-party lib type stubs (for static checks)
│   ├── customtkinter/          # customtkinter stub
│   ├── execjs/                 # PyExecJS stub
│   └── pystray/                # pystray stub
├── scripts/                    # engineering helper scripts
│   ├── smoke_test.py           # generic Web/API smoke test (zero-dep, config-driven)
│   ├── smoke_web.json          # smoke test sample cases (probe Web panel)
│   ├── compile_po.py           # .po → .mo compile and sync check (--check)
│   ├── check_coverage.py       # per-module coverage gate (used by CI)
│   ├── check_version.py        # version "single source of truth" dynamization check
│   └── sync_version.py         # version sync helper
├── downloads/                  # recording output dir (generated at runtime)
├── logs/                       # log dir (generated at runtime, includes danmaku_monitor.jsonl)
├── i18n/                       # i18n translation dirs (multilingual, multi-format)
│   ├── zh_CN/LC_MESSAGES/      # Simplified Chinese (gettext)
│   │   ├── zh_CN.po           # Chinese translation source (601 entries)
│   │   └── zh_CN.mo           # compiled translation (required at runtime, shipped with repo)
│   ├── en_US.json              # English (US) (JSON catalog)
│   ├── en_GB.json              # English (UK) (British spelling variant)
│   └── zh_TW.yaml              # Traditional Chinese (YAML catalog, requires PyYAML)
├── ffmpeg/                     # FFmpeg dir (Windows)
├── node/                       # Node.js dir (Windows)
├── main.py                     # CLI entry
├── gui.py                      # GUI entry
├── web.py                      # Web management panel entry
├── index.html                  # M3U8 video player (standalone tool page)
├── msg_push.py                 # message push module
├── i18n.py                     # i18n implementation
├── build_exe.py                # PyInstaller packaging script (CLI/GUI/Web three entries)
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Python project config
├── Dockerfile                  # Docker build file (multi-stage)
├── docker-compose.yaml         # Docker Compose (recorder/web/gui three services)
├── .dockerignore               # Docker build-context exclude
├── .gitignore                  # Git exclude
├── StopRecording.vbs           # Windows stop-recording script
├── CODE_WIKI.md                # project architecture doc
└── README.md                   # project README doc
```

## ⚙️ Configuration

### Basic config (config/config.ini)

```ini
[录制设置]
# UI language: zh_CN | en_US | en_GB | zh_TW (empty = follow system language; values such as zh_cn/zh-CN/en/en-GB/zh-Hant are also accepted and auto-normalized; falls back to en_US if the language file is missing)
language = zh_CN
# Whether to skip proxy detection (yes/no)
是否跳过代理检测(是/否) = 是
# Whether to enable log files (yes/no)
是否启用日志文件(是/否) = 是
# Live save path (defaults to downloads/ if empty)
直播保存路径(不填则默认) =
# When the anchor renames, automatically update URL_config.ini and rename the recording directory/files (default: yes)
是否自动更新主播名(是/否) = 是
# Whether to separate save folders by author
保存文件夹是否以作者区分 = 是
# Whether to separate save folders by time
保存文件夹是否以时间区分 = 否
# Whether to separate save folders by title
保存文件夹是否以标题区分 = 否
# Whether to include the title in the save file name
保存文件名是否包含标题 = 否
# Whether to strip emoji from names
是否去除名称中的表情符号 = 是
# Video save format ts|mkv|flv|mp4|mp3 audio|m4a audio
视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频 = ts
# Recording quality 原画|超清|高清|标清|流畅
原画|超清|高清|标清|流畅 = 原画
# Custom quality options (comma-separated) — the user-selected quality subset; when empty or all entries are invalid it falls back to the engine's built-in full set (default: empty);
# the WEB-side add/remove and the GUI-side "switch quality" write back here; choosing a non-default quality writes "quality,live-room address" into config/URL_config.ini
自定义画质选项(逗号分隔) =
# Whether to use a proxy IP (yes/no)
是否使用代理ip(是/否) = 否
# Proxy address
代理地址 =
# Number of threads accessing the network at the same time
同一时间访问网络的线程数 = 3
# Max concurrent recordings — global concurrency cap, 0 means unlimited (default 0); changes take effect on the next check cycle
最大同时录制数(0为不限制) = 0
# Loop interval (seconds) — live-status check interval (default 120)
循环时间(秒) = 120
# Queue read URL time (seconds)
排队读取网址时间(秒) = 0
# Whether to show the loop countdown
是否显示循环秒数 = 否
# Whether to show the live source URL
是否显示直播源地址 = 否
# Whether segmented recording is enabled
分段录制是否开启 = 是
# Whether HLS capture is enabled (yes/no) — if disabled, only non-HLS candidates such as FLV are used
是否启用HLS采集(是/否) = 是
# HLS capture exclusion platforms (comma-separated) — listed platforms ignore the "是否启用HLS采集" setting and always use FLV capture
# (platform names must exactly match those shown in logs/config, e.g. 斗鱼直播,虎牙直播; leave empty to exclude nothing)
HLS采集排除平台(逗号分隔) =
# Whether https recording is enabled — consolidates the former "是否强制启用https录制" and "是否禁用SSL证书验证(是/否)":
# enabled = stream pulled over https and SSL cert verification skipped; disabled = stream pulled over http and default cert verification restored
# (the value of the old key "是否强制启用https录制" is auto-migrated and inherited; https-only overseas platforms like TikTok/YouTube keep their original form when disabled)
是否启用https录制 = 否
# Platforms exempt from SSL cert verification (comma-separated) — only takes effect when "是否启用https录制 = 否" (http mode, cert verification required).
# Since FFmpeg 9.0, TLS cert verification is on by default; platforms with cert anomalies must be exempted here; required platforms are auto-appended at startup
# (Huya Live / Bilibili Live), with only appends and no removal of user-entered items
禁用SSL证书验证的平台(逗号分隔) = 虎牙直播,B站直播
# Recording free-space threshold (gb)
录制空间剩余阈值(gb) = 1.0
# Video segment duration (seconds) (default 1800)
视频分段时间(秒) = 1800
# Automatically convert to mp4 format after recording completes
录制完成后自动转为mp4格式 = 否
# Re-encode mp4 format to h264
mp4格式重新编码为h264 = 否
# Delete the original file after appending format
追加格式后删除原文件 = 是
# Generate a timestamp subtitle file
生成时间字幕文件 = 否
# Whether to run a custom script after recording completes
是否录制完成后执行自定义脚本 = 否
# Custom script execution command
自定义脚本执行命令 =
# Platforms recorded using a proxy (comma-separated)
使用代理录制的平台(逗号分隔) = tiktok, sooplive, pandalive, winktv, flextv, popkontv, twitch, liveme, showroom, chzzk, shopee, shp, youtu, faceit
# Additional platforms recorded using a proxy (comma-separated)
额外使用代理录制的平台(逗号分隔) =
# Whether to record danmaku (yes/no) — when enabled, danmaku is written to SRT subtitle files, synced with video start/stop
是否录制弹幕(是/否) = 否
# Whether danmaku monitoring is enabled (yes/no) — real-time danmaku viewing only, no SRT written (decoupled from danmaku recording, can be enabled separately)
是否弹幕监控(是/否) = 否
# Danmaku segment duration (seconds) — SRT segment granularity, recommended to match "视频分段时间(秒)"
弹幕分片时长(秒) = 1800
# Danmaku recording platforms (comma-separated) — the 5 currently supported platforms
弹幕录制平台(逗号分隔) = 斗鱼直播,B站直播,虎牙直播,抖音直播,TwitchTV
```

### Push config (config/config.ini)

```ini
[推送配置]
# Optional: 微信|钉钉|tg|邮箱|bark|ntfy|pushplus — multiple values allowed
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

### Cookie config (config/config.ini)

```ini
[Cookie]
# Required for recording Douyin: fill in a valid cookie copied from the browser at live.douyin.com (must at least include ttwid)
# Leaving it empty will auto-attempt to fetch a visitor ttwid (may trigger risk control; filling it in is recommended)
抖音cookie =
# Specify Douyin ttwid separately (left empty, it is fetched and process-level cached by src/ttwid.py)
ttwid =
# XHS (Xiaohongshu) app-side session sid carried in the xy-common-params header;
# left empty the built-in default is used (it may already have expired).
# Priority: environment variable XHS_SESSION_SID > this key > built-in default
xhs_session_sid =
快手cookie =
tiktok_cookie =
虎牙cookie =
斗鱼cookie =
yy_cookie =
b站cookie =
小红书cookie =
bigo_cookie =
# ... a total of 51 platform cookie keys; see config.ini for the rest
```

> Visitor-type cookies (Douyin ttwid, Kuaishou did, etc.) are process-level shared-cached by `src/cookie_cache.py` keyed by "normalized URL + proxy" (default 30-minute TTL), so concurrent rooms do not repeatedly fetch and trigger risk control.

### Authorization config (config/config.ini)

```ini
[Authorization]
# Token obtained from PopkonTV after login (written back after auto-login with account/password)
popkontv_token =
```

### Account/password config (config/config.ini)

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

### Web management panel config (config/config.ini)

```ini
[Web]
# Web management panel listen address
web_host = 0.0.0.0
# Web management panel port
web_port = 8000
# Whether password login is enabled (true/false)
web_auth_enable = false
# Access password (required when auth is enabled)
web_password =
# Token validity period (seconds)
web_token_expiry = 86400
# Whether to show the console window (when false, runs in background; logs written to logs/web_console.log)
web_show_console = true
# Minimize the console to the system tray (instead of the taskbar); Windows only;
# the close button is disabled — exit via the tray icon's "Exit program" menu
web_minimize_to_tray = true
# Trusted reverse-proxy sources (comma-separated). Left empty, X-Forwarded-For is not parsed;
# when behind Nginx/Caddy, fill in the proxy IP so login rate-limiting can obtain the real client IP
web_trusted_proxy =
# Allowed Host / Origin allowlist (comma-separated). Only needed when web_host is bound to
# 0.0.0.0/:: and the panel is reached via a domain name; any unlisted multi-label domain Host is
# rejected to block DNS rebinding (attacker.tld → 127.0.0.1)
web_allowed_hosts =
```

> `web_host` is `127.0.0.1` in the repo's default config (localhost access only). For Docker or LAN/public access, change it to `0.0.0.0`, and be sure to also enable `web_auth_enable` and set `web_password`.

### Live-room config (config/URL_config.ini)

Douyin supports the following 5 live-room / profile URL formats (formats for other platforms are shown in the per-platform examples below):

```
# 1) Web anchor live room (numeric room id)
https://live.douyin.com/745964462470

# 2) App anchor live room (share short link)
https://v.douyin.com/iQFeBnt/

# 3) Douyin-id concatenation (https://live.douyin.com/ + Douyin id, supports VR live recording)
https://live.douyin.com/yall1102

# 4) App anchor profile (share short link)
https://v.douyin.com/CeiU5cbX

# 5) Web anchor profile (user page address)
https://www.douyin.com/user/MS4wLjABAAAA3kr2yA4aRD-sjf9cx8xkOH8Di3RjktpKcAvqIetpsF0
```

> Notes:
> - Formats 1/3/5 use the web endpoint (support VR live); formats 2/4 use the app endpoint
> - Format 5 (web anchor profile `www.douyin.com/user/<sec_uid>`) directly extracts `sec_user_id` from the address and resolves the Douyin id, then records via the web endpoint as a live-room address — no app-endpoint probing needed
> - Short-link forms such as format 4 (app profile) first probe the live-room address; on failure they automatically fall back to Douyin-id resolution and then record via the web endpoint

```ini
# Specify quality (quality, live-room address)
超清，https://live.douyin.com/745964462470

# Specify quality and anchor name (quality, live-room address, anchor: name)
高清，https://live.bilibili.com/123456，主播: B站主播

# Comment out a live room (prefix the address with #)
# https://live.douyin.com/123456789
```

### Environment variable config

| Variable | Description | Example |
|----------|-------------|---------|
| `PYTHONUNBUFFERED` | Output logs in real time | `1` |
| `PYTHONDONTWRITEBYTECODE` | Do not generate .pyc files | `1` |
| `PYTHONIOENCODING` | Python output encoding | `utf-8` |
| `TZ` | Timezone setting | `Asia/Shanghai` |
| `TERM` | Terminal type | `xterm-256color` |

## 🎬 Usage

### CLI mode

```bash
python main.py
```

### GUI mode

```bash
python gui.py
```

GUI features (5 sidebar pages):
- 📊 Console — recording-status overview, start/stop control
- 🎯 Quality monitoring — real-time check of whether each room's actual quality matches the setting
- 💬 Danmaku monitoring — real-time view of each room's danmaku stream, with filtering by room/type
- 📝 URL config — live-room address management
- 📋 Run logs — subprocess log viewer

The sidebar also provides an **Appearance** selector (light/dark/follow system) and a **Language** selector (Simplified Chinese / English (US) / English (UK) / Traditional Chinese); switching language takes effect immediately and is written back to `config.ini`, with no restart needed.

The system tray icon supports minimizing to the tray for background running.

### Web management panel mode

```bash
python web.py
```

After startup, open `http://localhost:8000` in a browser.

Features:
- **Dashboard**: real-time view of monitored/recording counts, error count, remaining disk, recording list, and log stream (SSE push)
- **Room management**: online CRUD of live-room addresses, enable/disable (auto hot-loaded into the recording main loop)
- **Config editor**: edit each config.ini item online (recording settings/push/Cookie, etc.); sensitive config items are masked
- **File browser**: browse the downloads directory and download recording files
- **Actual quality display**: the recording table shows "set quality / actual quality", highlighted in red on degradation
- **Danmaku viewer**: reads the danmaku monitor hub snapshot and shows each room's danmaku events in real time
- **Language switch**: top-bar language selector, instant four-language switching (writes back config and hot-switches in-process translations, no restart needed)

Main API routes (all require a Token, except when auth is disabled):

| Route | Method | Function |
|-------|--------|----------|
| `/api/login` | POST | Password login, returns Token |
| `/api/status` | GET | Recording status (incl. actual quality) |
| `/api/status/stream` | GET | Recording-status SSE stream |
| `/api/rooms` | GET/POST/PUT/DELETE | Live-room CRUD |
| `/api/rooms/toggle` | POST | Enable / disable a live room |
| `/api/config` | GET/PUT | Read / modify config |
| `/api/language` | GET/PUT | Query / switch UI language |
| `/api/files`, `/api/files/download` | GET | Recording file browse and download |
| `/api/logs`, `/api/logs/stream` | GET | Log query / SSE real-time push |
| `/api/danmaku` | GET | Danmaku monitor snapshot |

The Web mode shares the same recording engine and config file with CLI mode; CRUD of live-room addresses is auto hot-loaded by the recording main loop.

Background mode: set `web_show_console` to `false`; under Windows the console window is hidden, logs are written to `logs/web_console.log`, and the program runs fully in the background.

Under Windows the console defaults to "minimize to system tray" (`web_minimize_to_tray = true`): after clicking minimize the window disappears from the taskbar and collapses to the system tray; double-click the tray icon to restore; the title-bar close button is disabled — exit via the tray icon menu's "Exit program".

> ⚠️ **Security note**: listening on 0.0.0.0 by default without auth enabled — for public/LAN deployment be sure to enable `web_auth_enable` and set a strong password, or change `web_host` to `127.0.0.1`.

### Recommended recording formats

- **Long recordings**: `ts` is recommended — written in real time, resilient to corruption on power loss
- **Short recordings**: `mp4` or `mkv` is recommended — directly usable after recording completes
- **Audio-only recording**: `mp3` or `m4a` is recommended

### Quality notes

| Quality code | Chinese name | Description |
|--------------|--------------|-------------|
| OD | 原画 | Original Definition, highest quality |
| BD | 蓝光 | Blu-ray, ultra-high definition |
| UHD | 超清 | Ultra HD |
| HD | 高清 | High Definition |
| SD | 标清 | Standard Definition |
| LD | 流畅 | Low Definition, lowest quality |

Supported platforms: Douyin, TikTok, Kuaishou, Huya, Douyu, Bilibili, NetEase CC. When a platform's actually delivered quality is lower than the configured quality, an automatic alert and flag are raised.

### Source selection (HLS/FLV)

The recording stream source is automatically selected between HLS (m3u8, pulled segment by segment) and FLV (a single long connection): by default HLS is preferred, falling back to FLV in order when validation fails, with `record_url` as the final fallback. It is controlled by two config items together:

| Config item | Effect |
|-------------|--------|
| `是否启用HLS采集(是/否)` | Global switch: when enabled (default), the HLS source is preferred and falls back to FLV when unreachable or absent; when disabled, all platforms use only non-HLS candidates such as FLV |
| `HLS采集排除平台(逗号分隔)` | Platform-level exclusion list: listed platforms **ignore the global switch and always use FLV capture** (equivalent to disabling HLS capture for that platform only — HLS sources take no part in candidates or fallback) |

- **Use case**: you prefer HLS recording overall (HLS pulls segment by segment and is immune to a single long connection being cut off by the CDN), but an individual platform's HLS source is unstable or risk-controlled, and you want only that platform forced onto FLV — just add it to the exclusion list, without having to turn off the global HLS switch
- **Fill format**: platform names must **exactly match** what the logs/config file show (e.g. `斗鱼直播`, not `斗鱼`); separate multiple platforms with commas (Chinese or English commas both work), e.g. `斗鱼直播,虎牙直播`; leave empty (default) to exclude nothing — behavior stays identical to previous versions
- **Priority semantics**: the exclusion list takes precedence over the global switch — even with "是否启用HLS采集(是/否) = 是" (yes), a listed platform only uses FLV; platforms outside the list are completely unaffected and keep HLS priority per the global config
- **Boundary behavior**: if an excluded platform's parsed result contains only an HLS source with no FLV/record_url fallback, the round is abandoned with a warning (the log suggests "remove the platform from the exclusion list to restore HLS capture"); an h265-encoded FLV source no longer triggers a switch to HLS (the logic that auto-saves h265 FLV recordings as TS format is unaffected)
- **Hot reload**: the main loop re-reads the config every round — save your changes and the next monitoring round picks them up, no restart needed

### Danmaku recording and danmaku monitoring

The danmaku features are controlled by two **mutually decoupled** toggles, which can be enabled separately or together:

| Config item | Effect |
|-------------|--------|
| `是否录制弹幕(是/否)` | Danmaku is written to SRT subtitle files, synced with video start/stop |
| `是否弹幕监控(是/否)` | Real-time danmaku viewing only, no SRT written (GUI "Danmaku monitoring" page / Web `/api/danmaku`) |
| `弹幕分片时长(秒)` | SRT segment granularity, recommended to match "视频分段时间(秒)" |
| `弹幕录制平台(逗号分隔)` | Whitelist of platforms with danmaku enabled |

- **Supported platforms (5)**: Douyin Live, Douyu Live, Huya Live, Bilibili Live, TwitchTV
- **Output files**: SRT corresponds one-to-one with video segments, named `{base name}_{segment index:03d}.srt` (e.g. `_000.srt` corresponds to `_000.ts`); when not segmented, `{base name}.srt`. The timeline is based on a monotonic clock, aligned with ffmpeg's `segment -reset_timestamps` PTS, and can be loaded directly by players
- **Danmaku direct connect**: the danmaku WebSocket explicitly does not follow the system proxy, avoiding immediate disconnection under a SOCKS proxy
- **Monitor sidecar log**: danmaku monitor events are also written to `logs/danmaku_monitor.jsonl` (5MB rotation)
- Douyin danmaku auto-fetches a visitor ttwid when the cookie is empty; Bilibili danmaku auto-fetches a real buvid (login cookie → spi endpoint → homepage Set-Cookie → random fallback)

### Auto anchor-name update

With `是否自动更新主播名(是/否)` enabled (default "yes"), whenever the latest anchor name is resolved each round and differs from the name recorded in `URL_config.ini`, the program automatically does two things:

1. **Rename the filesystem**: `{save path}/{platform}/{old anchor name}` → new anchor-name directory; recursively rename all recording artifacts (TS / FLV / SRT / subtitles) in the directory tree that start with `{old name}_`, and title directories ending with `_{old name}`; if the new-name directory already exists, items are merged and moved in one by one (compatible with an anchor reverting to a former name)
2. **Write back the config file**: precisely match by URL segment and replace only that line's anchor-name field, fully preserving the quality segment, the `#` comment prefix, and the line-ending style; the operation is idempotent

Safety constraints:

- The detection point is located "after live data is parsed, before recording starts", at which time the thread is necessarily not recording — naturally avoiding the ffmpeg file-occupancy window
- **Filesystem first, then config file; the name used this round is switched only after both succeed**; on any failure, the old name is kept and retried automatically on the next poll round
- When an individual file is occupied by background transcoding/a player, only a warning is skipped past — it does not block the whole process
- Custom stream addresses (whose anchor name contains a per-round random UUID) and nicknames that become blank after cleaning are automatically skipped
- Disabling this toggle keeps manual names unchanged

### Multi-language and UI switching

Four translation catalogs are built in, probed at load time in the order `gettext .mo → <lang>.json → <lang>.yaml`:

| Language code | Display name | Catalog file |
|---------------|--------------|-------------|
| `zh_CN` | Simplified Chinese | `i18n/zh_CN/LC_MESSAGES/zh_CN.mo` |
| `en_US` | English (US) | `i18n/en_US.json` |
| `en_GB` | English (UK) | `i18n/en_GB.json` |
| `zh_TW` | Traditional Chinese | `i18n/zh_TW.yaml` |

- The config key `language`: leave it empty to follow the system language; values such as `zh_cn` / `zh-CN` / `en` / `en-US` / `en-GB` / `zh-Hant` / `zh_CN.UTF-8` are accepted and auto-normalized to the canonical language code; unrecognized values or missing language files fall back to `en_US`
- **Hot switching**: switchable via three paths — the GUI sidebar language selector, the Web panel top-bar language selector, or directly editing `config.ini`; the CLI main loop checks for config changes each round and reloads translations immediately, **no process restart needed** (the running ffmpeg subprocess is unaffected)
- Translations no longer depend on the `LANG` / `LANGUAGE` environment variables (generally unset on Windows)
- `zh_TW.yaml` requires `PyYAML`; if missing, only that language is lost, other formats are unaffected

### Stop recording

- **Windows**: run `StopRecording.vbs` or press `Ctrl+C` in the terminal
- **Linux/macOS**: press `Ctrl+C` in the terminal
- **Docker**: run `docker-compose stop`

### Notes

1. To record overseas platforms such as TikTok or SOOP (formerly AfreecaTV), enable the proxy in the config
2. For long uptime, set a longer loop interval (e.g. 60 seconds) to avoid frequent requests getting your IP banned
3. Files are saved automatically after the live stream ends — no manual stop needed
4. If a recorded video file is corrupted, `ts` format recording is recommended
5. Recording Douyin requires a valid cookie (at least containing ttwid), otherwise risk control may be triggered
6. Some platforms need a Node.js environment to run JavaScript signature scripts, which is auto-installed under Windows

## 🐋 Docker Deployment

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed

### Quick start

```bash
# 1. Clone the project
git clone https://github.com/y123ao6/DouyinLiveRecorder.git
cd DouyinLiveRecorder

# 2. Edit the config file
# Add live-room addresses in config/URL_config.ini

# 3. Start the container (default CLI recording mode)
docker compose up -d

# 4. View logs
docker compose logs -f
```

### Switch run mode

`docker-compose.yaml` has three built-in services (recorder / web / gui) that you switch via profile without editing the file:

```bash
# CLI recording mode (default, no port used)
docker compose up -d

# Web management panel mode (maps port 8000, access via browser at http://localhost:8000)
docker compose --profile web up -d

# GUI mode (requires an X11 display environment; run xhost +local: on the host first)
docker compose --profile gui up -d
```

> ⚠️ Web-mode note: `web.py` listens on `127.0.0.1` by default; inside the container you must set `web_host = 0.0.0.0` in the `[Web]` section of `config/config.ini` to access it from the host; it is also recommended to enable `web_auth_enable = true` and set `web_password`.

### Data mounts

```yaml
volumes:
  - ./config:/app/config:rw          # config directory (required)
  - ./downloads:/app/downloads:rw    # recording download directory (required)
  - ./logs:/app/logs:rw              # runtime log directory
  - ./backup_config:/app/backup_config:rw  # config backup directory
```

### Port mapping

Only the `web` service (Web management panel mode) maps ports; the `recorder` / `gui` services listen on no ports:

```yaml
ports:
  - "8000:8000"   # Web management panel port (only takes effect with --profile web)
```

### Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TZ` | Timezone | `Asia/Shanghai` |
| `PYTHONUNBUFFERED` | Real-time output | `1` |
| `PYTHONDONTWRITEBYTECODE` | Do not generate .pyc files | `1` |
| `PYTHONIOENCODING` | Python output encoding | `utf-8` |
| `TERM` | Terminal type | `xterm-256color` |

### Docker image features

- **Multi-stage build**: the builder stage installs dependencies into a virtualenv; the runtime stage is a slim image
- **Non-root user**: runs as the `recorder` user for improved security
- **Health check**: automatically detects whether the `main.py` or `web.py` process is alive
- **Resource limits**: defaults to 2 CPU / 2G memory (adjustable in docker-compose.yaml)
- **Log rotation**: single file 50MB, up to 3 retained
- **Built-in Node.js 24 LTS**: for running JavaScript signature scripts

## 🛠️ Development Guide

### Environment requirements

- Python >= 3.14
- FFmpeg (manual install required on Linux/macOS)
- Node.js (auto-installed on Windows, manual install required on Linux/macOS)

### Install dev dependencies

```bash
# Use uv (recommended)
uv sync --dev

# Or use pip
pip install -r requirements.txt
pip install pytest pytest-asyncio black isort mypy
```

### Code conventions

```bash
# Format code (line-length = 120)
black .

# Sort imports
isort .

# Type check (CI uses mypy as the standard)
mypy .

# Type check (local enhancement, optional): basedpyright
# Configured in pyproject.toml under [tool.basedpyright], venvPath points to the workspace .venv (relative path, portable)
# First time: create and install deps: python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
basedpyright .

# Run tests
pytest
```

> **Comment convention**: module/function docs uniformly use `#` line comments, not triple-quoted `"""` docstrings; functional multiline string literals (templates/SQL) use single quotes + line concatenation instead of `"""`.

> **Five-tool quality gate**: this project uses `mypy` (src + tests) / `basedpyright` (tests) / `pytest` (0 warnings) / `black --check .` / `isort --check-only .` jointly as a quality gate; all-green in CI is a prerequisite for merging. Current baseline: **974 passed / 2 skipped / 0 warnings**.

> **Test note**: `tests/test_web_api.py`'s symlink-related cases (`TestListFiles::test_broken_symlink_skipped` / `test_symlink_outside_skipped`) auto-`pytest.skip` in environments where real symlinks cannot be created (Windows without Developer Mode, some sandboxes) — this is normal and does not indicate a code defect.

### Project documentation

- [CODE_WIKI.md](CODE_WIKI.md) - project architecture doc (detailed module descriptions, dependencies, design patterns)

### Web/API smoke testing

The project ships a generic, zero-dependency Web/API smoke-test tool `scripts/smoke_test.py` (pure standard library, no third-party packages needed), which can do lightweight liveness probes against **running HTTP interfaces** such as the Web management panel.

```bash
# Check the local Web management panel (default 127.0.0.1:8000; sample config in scripts/smoke_web.json)
python scripts/smoke_test.py -c scripts/smoke_web.json

# Generate an HTML report
python scripts/smoke_test.py -c scripts/smoke_web.json -r smoke_report.html -f html
```

- Config-driven (JSON): `url` / `method` / `expected_status` / `timeout` / request headers / request body / response text that should be included / expected JSON fields
- Supports `base_url` prefix concatenation; console / JSON / HTML report formats; non-zero exit code on failure (can be wired into CI)
- Unlike `build_exe.py --smoke` (packaging-artifact smoke test), this tool probes **running HTTP interfaces** for liveness — the two complement each other
- The default case `scripts/smoke_web.json` probes the Web panel `/` (home page 200) and `/health` (`{"status": "ok"}`, a public liveness endpoint provided by `src/web_api.py`, not gated by `web_auth_enable`)
- **Wired into CI**: the `test` job in `.github/workflows/ci.yml` starts `python web.py` in a controlled way after pytest, then runs the `scripts/smoke_web.json` smoke test once it is ready (network flakiness handled via `.github/actions/retry`; on failure it keeps the `logs/web-smoke-*` artifacts and turns the job red), covering the "can the panel process really bind and respond" path that TestClient cannot

### Add a new platform

**Video recording platform:**

1. Add a platform stream-URL parsing function in `src/spider.py` (refer to existing platform implementations)
2. Add a stream-URL parsing function in `src/stream.py`, with the return value containing `actual_quality` and `available_qualities` fields
3. Add platform identification logic in `main.py` (the `PLATFORM_HOST` list and the recording branch)
4. Update `README.md` and `CODE_WIKI.md`

**Danmaku recording platform (if danmaku support is needed):**

1. Create `<platform>.py` under `src/platforms/`, inheriting `DanmakuBase` from `src/base.py`, implementing connect/auth/message parsing
2. Register it in the danmaku platform registry in `src/__init__.py` (platform name must match the `platform` id in `main.py`); decoupled creation via the `get_danmaku_class` / `get_danmaku_collector` factory
3. Add the platform branch at the danmaku-recording wiring in `main.py` (construct `record_danmaku_args` and pass it to `check_subprocess`)
4. Update `README.md` and `CODE_WIKI.md`

> Note: the danmaku subsystem and `src/spider.py` (video stream-URL parsing) are two parallel, decoupled abstractions; `spider.py` does not import `src/platforms`.

## ❓ FAQ

**Q: Recording shows "ffmpeg missing, cannot record"**

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# The program ships with ffmpeg, no install needed
```

**Q: Which ffmpeg is actually used on an Apple Silicon (M-series) Mac?**

The macOS ffmpeg bundled in the full release package is upstream's **x86_64 static build**
(ffmpeg.org only publishes "Static builds for macOS 64-bit" and **no arm64 build**), so on
Apple Silicon it runs through **Rosetta 2** translation. To keep it from shadowing a native
build the user installed themselves: when "macOS + arm64 + another ffmpeg already exists on the
system PATH" all hold, the program **prefers the system one** (e.g. what `brew install ffmpeg`
installs, a native arm64 build) and no longer prepends the bundled `ffmpeg/` directory to `PATH`.
In every other case (Intel Mac, Windows, Linux, no ffmpeg on the system, or the PATH hit turns
out to be the bundled copy itself) the previous behaviour is kept and the bundled build is used.
The single-file script `douyin_live_recorder_standalone.py` applies the same criteria; there it
shows up as `find_ffmpeg()` returning the system build's path instead of reordering `PATH`.

How to confirm which copy is in effect:

```bash
ffmpeg -version          # a Homebrew build carries --prefix=/opt/homebrew/... (native on Apple Silicon)
                          # the bundled evermeet static build has no such prefix
which ffmpeg              # points into the bundled ffmpeg/ directory => the bundled copy is in use
```

Or look for the "FFmpeg PATH priority" line in the debug log (written to `logs/streamget.log`
when `config.ini` has `是否启用日志文件 = 是`), which states explicitly whether the program is
"yielding to the native system ffmpeg <path>" or "still prepending the bundled directory <path>".

> Docker is unaffected by this policy: the image installs ffmpeg via apt, and on Apple Silicon
> the Linux arm64 container is built/run for the host architecture, so it is native already.

**Q: Shows "Node.js missing" or "execjs"-related errors**

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
sudo apt-get install -y nodejs

# macOS
brew install node

# Windows
# The program auto-downloads and installs into the node/ directory
```

**Q: Shows "IP banned, please change device or network"**

- Check whether the proxy is enabled
- Lower the loop monitoring frequency
- Wait a while and try again

**Q: Douyin risk control prevents data retrieval**

- Fill `config.ini`'s `[Cookie]` section with a valid cookie copied from the browser at `live.douyin.com` (must at least include `ttwid`)
- Lower the loop monitoring frequency (the default 120-second loop is already conservative; you may increase it as appropriate)
- Change IP or use a proxy
- Key troubleshooting points (verified conclusions):
  - The typical signal of Douyin risk control is **HTTP 200 + empty response body**, not a 4xx error code; seeing `web/enter` return `status_code=10002 / unknown error` then auto-falling back to HTML scraping is a **normal fault-tolerant path**, not a recording failure
  - Douyin API requests must use a **desktop User-Agent**; the old mobile UA is silently throttled (returns empty body)
  - For profile-type links (formats 4/5), fill in the complete address directly; the old `iesdouyin.com/share/user/` path has become an anti-scraping shell page — do not use it

**Q: HLS check log is blank and always falls back to FLV**

- Symptom: the log shows `get_response_status check failed (judged unreachable): ` (blank message) immediately followed by `HLS URL validation failed, falling back to FLV`, repeating
- Cause (fixed on 2026-08-05):
  - Under Windows, `socket.timeout` / `TimeoutError`'s `str()` is empty, causing exception logs to show blank — impossible to tell whether it was a timeout, connection refused, or a cert issue
  - The stream-URL check function used to silently swallow all exceptions (`except Exception: return False`), so when falling back to FLV there was no cause to inspect
  - The m3u8 source HEAD probe did not cover 404 (Douyin and other CDNs often return 404 for HEAD while GET pulls fine), and from HLS source selection to the check call the **proxy was not forwarded**, causing TikTok and other proxy-required platforms to time out on direct-connect checks and be misjudged unreachable
- Behavior after the fix: exception logs include the URL and exception type; all failure paths log detailed warnings (with status code / content-type); m3u8 HEAD non-2xx (**including 404**) always gets a `Range: bytes=0-0` GET probe; HLS source selection correctly forwards the proxy. If it still falls back after re-running, the log will directly give the real cause (e.g. `ConnectTimeout`, `HEAD=404, Range-GET=403`) — at that point it is usually an environmental issue such as the CDN domain being blocked or the anchor's stream URL expiring, not a code misjudgment

**Q: Recorded video file is corrupted**

- `ts` format recording is recommended
- Check that disk space is sufficient
- Check that the network is stable

**Q: How to push live-start notifications only, without recording?**

Set `只推送通知不录制(是/否) = 是` in the `[推送配置]` section of `config.ini`

**Q: Forgot the Web panel password?**

Directly edit the `web_password` item in `config/config.ini`; after changing it, restart `web.py`. After a password change, all existing Tokens are invalidated and require re-login.

## ❤️ Contributors

<a href="https://github.com/y123ao6/DouyinLiveRecorder/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=y123ao6/DouyinLiveRecorder" />
</a>

## 📄 License

This project is open-sourced under the [MIT License](LICENSE). Stars and Forks are welcome!

## ⏳ Changelog

### v4.3.0 (2026-09-16 ~ 2026-09-26) — P0 fix for 100% recording failure on ffmpeg master builds (`-thread_queue_size` narrowed upstream to an output-only option) / boolean config parsing unified (`true/false` silently broke 8 settings and blocked 9 overseas platforms) / two full code-review rounds (62 + 106 graded fixes) / supply-chain hardening (official hashes first + GPG verification + Lanzou fallback removed) / Apple Silicon ffmpeg PATH yield policy / per-room log correlation field & `/health` probe endpoint / build artifact size −21.6% / coverage 73.28% → 82.03%

> This release (v4.3.0, 2026-09-16 ~ 09-26) is a convergence cycle focused on **correctness and supply-chain safety**. Three items matter most: ① **P0**: ffmpeg master builds narrowed `-thread_queue_size` to an output-only option, while we still placed it before `-i` — so on such a build **every single recording exited with `-22 (EINVAL)` and produced zero bytes**; ② **boolean config parsing unified**: writing `true/false` in `config.ini` used to be treated as invalid and **silently** fall back to a hardcoded default (no warning, no log), which measurably drifted the effective value of 8 settings — the worst one leaving 9 overseas platforms 100% unable to record; it is now unified so that `是/否`, `true/false`, `1/0`, `yes/no` and `on/off` are all equivalent; ③ **two full code-review rounds** (62 items on 09-19: 12 severe / 22 medium / 28 minor; 106 items from `CODE_REVIEW_2026-09-20` on 09-21: 10 severe / 70 medium / 26 minor) cleared a batch of silent-failure modes at once — SSRF, panel takeover, credentials written to disk in plaintext, danmaku thread livelock, and more. **There are breaking changes** — see the dedicated section below. Full root-cause analysis and verification are in [CODE_WIKI.md](CODE_WIKI.md).

**🐛 Fixes**
- **P0: 100% recording failure on ffmpeg master builds**: `-thread_queue_size` was narrowed upstream to a muxer-only option; placed before `-i`, ffmpeg exits with `Option thread_queue_size … cannot be applied to input url … Error opening input files: Invalid argument` (return code -22). Unrelated to room / platform / CDN — on that build *every* recording fails.
- **P0: boolean config parsing unified**: the scattered parsers (previously `!= "否"`, `== "是"`, and the front-end `=== '是'`) are unified into `src/config_bool.py::parse_config_bool`; as a result `global_proxy` is no longer wrongly forced to False, restoring resolution for TikTok / SOOP / PandaTV / WinkTV / Flextv / PopkonTV / Twitch / LiveMe / Faceit and other overseas platforms.
- **Full code review, 62 items (09-19)**: GUI silent hang on empty config; one extra comma in a config line permanently skipping every room after it; missing bounds checks in Tars decoding causing a danmaku-thread livelock; Douyu danmaku silently filtered out (regression of an earlier fix); a hung ffmpeg permanently holding a concurrency slot; zero-byte output judged as success and cancelling circuit-breaker backoff; `config.ini` (with credentials) copied in plaintext into `backup_config/`; the Web panel being take-over-able or lockable through its own API; zero protocol validation on room URLs → blind SSRF; the masking blacklist missing every "credential embedded in the value" URL-type key; zero integrity verification in the install/packaging chain.
- **`CODE_REVIEW_2026-09-20` landed in full, 106 items (09-21)**: the concurrency semaphore treating "available permits" as capacity (the network concurrency cap effectively out of control); `PUT /api/rooms` bypassing room-entry validation; intranet blocking via a string-prefix blacklist (5 of 7 probe addresses passed); panel auth being hot-disabled by a single write request, with case variants bypassing the password hash / self-lock guard / token revocation; deleting a room on CRLF configs failing permanently while still reporting `{"ok": true}`; Shopee site-suffix parsing producing an illegal domain; fallback decorators mismatched with return contracts (failures disguised as "not live"); the recording watchdog using the wrong baseline for its "stalled" verdict (the real tolerance window was only 30 seconds); the `only_flv` branch missing `flv_url`, causing the time-subtitle thread to spin and write to disk in a loop; an empty runtime-binary hash pinning table in the release chain.
- **Release chain & supply chain**: macOS arm64 full packages **silently shipped without ffmpeg** (no such artifact upstream — the download point is fixed); the Windows runtime ffmpeg primary source verified healthy by measurement (gyan.dev ships a `.sha256` document that cross-confirms the release-time pin); official SHA256 pins backfilled for 6 of 10 slots.
- **Test hygiene (09-23)**: one cross-file patch leak (a missing `undo()`) let later tests in the same session issue real network requests, producing 11 "red in full run, green alone" false failures out of 13.
- **P0: build script polluting the test session (09-23)**: the bare `reconfigure` in `build_exe._ensure_utf8_streams()` broke pytest's fd capture, surfacing as a "GUI failed to start" dialog plus unrelated tests marked FAILED/ERROR (all nine CI jobs run ubuntu and stayed green — never reproduced).

**✨ New Features / Improvements**
- **Per-room log correlation field `extra[room]`**: `src/logger.py` gains `ROOM_FIELD` / `set_room_context()` / `get_room_context()` (internal `ContextVar` + patcher), so interleaved multi-room logs can be sliced per room.
- **Web panel `/health` probe endpoint**: `GET /health` returns `{"status": "ok", "version": …}`, and the built-in smoke tool `scripts/smoke_test.py` is wired into CI as a real HTTP probe.
- **W6: Apple Silicon ffmpeg PATH yield policy**: on darwin + arm64 with another native ffmpeg already on `PATH`, the bundled x86_64 build (which only runs through Rosetta translation) is no longer unconditionally prepended; yielding requires all five criteria to hold. Other platforms are unchanged, byte for byte.
- **Runtime binary integrity**: `build_exe.py` gains the `_PINNED_RUNTIME_SHA256` table plus `--require-pinned`, backed by `scripts/check_runtime_pins.py` (structure mode in the local gate / `--strict` in the release prepare job / `--emit-env` for CI injection); first-time runtime installs now prefer officially published hashes, and release builds add GPG verification plus a full-package self-check.
- **Build artifact size optimization (09-24)**: excluded runtime-unreachable modules (`PIL._avif`, `pydantic.v1.mypy` which drags in all of mypy, uvicorn's optional implementations, `i18n/*.po`, …) plus zip `compresslevel=9` — the lite artifact went from **82.77MB to 64.88MB (−21.6%)** and the zip from **54.84MB to 42.19MB (−23.1%)**, with a new measurement script `scripts/report_bundle_size.py`.
- **Five new gates**: `PYTHONUTF8=1` + "any warning fails" (kills the mode where isort silently skips files with Chinese comments under a GBK locale and still exits 0); a decorator-contract AST lock; a test-hygiene AST lock (R1–R4 / R6 "manual MonkeyPatch must pair with undo"); a front-end catalog consistency lock (`data-i18n*` keys compared one-by-one against the four embedded catalogs); a `deps-audit` job and hard failure when coverage data is missing.
- **Dynamic concurrency floor lowered**: `ConcurrencyScheduler`'s `min_capacity` default changed from 8 to 1.

**⚠️ Breaking Changes / Behavior Changes**
- **Lanzou ffmpeg fallback removed on Windows at runtime**: automatic installation now has a single primary source (measurement showed that direct link serves a JS-challenge HTML page with all companion hash documents returning 404, i.e. unusable); when automatic installation fails, an explicit manual-install guide is emitted instead. **Windows users who relied on that fallback must place the binary themselves, following the "manual ffmpeg installation on Windows" section of this README.**
- **The bundled ffmpeg directory is no longer unconditionally prepended on Apple Silicon**: users who installed a native arm64 ffmpeg (e.g. via Homebrew) will now have recording subprocesses use that system copy instead (its version / build options may differ).
- **Dynamic concurrency floor 8 → 1**: the network concurrency allowance is no longer lifted to 8 under low load.
- **Boolean config semantics changed**: keys previously written as `true/false`, `1/0`, … were **silently ignored** (falling back to a default); after upgrading they take effect literally — if your config depended on the old wrong fallback value, the effective value changes. Please re-check the 8 affected settings after upgrading.
- **Runtime dependencies 20 → 23**: newly declared explicitly — `urllib3>=2.7.0` (CVE-2026-44431), `h2>=4.3.0` and `socksio>=1.0.0` (httpx runtime deps for HTTP/2 and SOCKS); `starlette` lower bound `>=0.49.1` → **`>=1.3.1`** (CVE-2026-48710 plus PYSEC-2026-2280/2281/248/249); `protobuf` keeps its `<8` cap (gencode compatibility guardrail).
- **Build time**: the `build-release.yml` prepare job now blocks unpinned runtime binaries via `check_runtime_pins.py --strict`.

**🛠️ Repo Maintenance & Quality Gates**
- **Test coverage push (09-21)**: `src/` coverage **73.28% → 82.03%** (tests only, zero product-code changes), plus a layered allowlist (table empty by default, fails when it expires).
- **Four-language catalogs kept complete and verified**: 594 → **780 entries**, with all four catalogs matching key by key and no empty values; the `.mo` is recompiled whenever they change.
- **Metadata single-source sync**: `AGENTS.md` dependency count and lower-bound wording, the `CODE_WIKI*.md` dependency tables (16 → 23 entries), `DouyinLiveRecorder.egg-info` regenerated, `_probe_*.py` added to `.dockerignore`, and `[Cookie] ttwid` added to `config/config.ini`.
- **Type stubs & comment governance**: 7 `.pyi` files under `typings/execjs/` got complete annotations and two abstract-base stubs dropped `six` (switched to `metaclass=ABCMeta`); multiple repo-wide comment-refinement batches (including one 68-file round), and `scripts/check_annotations.py` gained a third blind spot (newline form).
- **Leftovers of deleted modules cleaned up**: `src/weverse_auth.py` / `tests/test_weverse_auth.py` (deleted 2026-09-23) were removed from structure trees and dependency notes, and their 3 orphan translations were dropped from the four catalogs.

**🧪 Tests & Verification**
- Full `pytest`: **3199 passed / 13 skipped**; one more case, `test_symlinked_system_hit_inside_bundled_dir_keeps_prepending`, is permanently red on **this Windows host** — `Path.symlink_to()` there does not create a real reparse point (it raises nothing but does not dereference), so the scenario cannot be reproduced; CI on Linux/macOS is fine.
- `black --check .` **169 files unchanged**; `isort --check-only .` no reordering; parameterless `mypy` **158 files, 0 issues** (`mypy --platform linux` likewise 0); `basedpyright` (standard) **0 errors / 0 warnings / 0 notes**.
- `node --test tests/frontend/*.mjs` green; `scripts/check_version.py` and `scripts/check_runtime_pins.py` both rc=0.

### v4.2.0 (2026-09-12 ~ 2026-09-15) — full code-review fix (~120 items: security/concurrency/platform) + Douyu "SRT only, no video" root cause & HLS segment-layer false-green probe + source-selection hardening + start_record command-construction / platform-dispatch single-source-of-truth refactor + repo metadata sync & four-language catalog consistency fix + mypy gate expansion (scope pushed down to `[tool.mypy].files`) with 6 type-defect fixes + Linux CI read-only test fix

> This release (v4.2.0, 2026-09-12 ~ 09-15) is a comprehensive fix-and-hardening cycle spanning security, concurrency, and the platform layer plus quality gates. Core fixes: ① root-caused and fixed the "only danmaku SRT produced, no video file" issue on Douyu and similar platforms — the HLS playlist layer always returns 200, but the edge node serving the media segments returns 404 for all of them, so ffmpeg pulls zero media segments and produces zero bytes; the danmaku pipeline depends only on `room_id` and is decoupled from the video pipeline, so the SRT is still written. Added the HLS segment-layer probe `_probe_hls_segment` (decoupling "playlist 200" from "recordable") and three directions of source-selection hardening (config fallback / observability / same-origin FLV fallback). ② Collapsed the five inline ffmpeg `command=[]` lists in `start_record` into a single source of truth and replaced the 53-level `elif` chain in platform dispatch with a dispatch table, with zero behavioral difference (byte-level golden snapshots + item-by-item dispatch snapshots). ③ Closed `CODE_REVIEW_FIX_1` (F-01~F-25, 22 landed + 3 deferred) and the 09-12 full code review (~120 items: SHA256 pinning, atomic writes, zip-bomb protection, singleflight concurrency, Douyu packet-boundary / Bilibili watchdog / Shopee fixes). ④ Synced repo metadata (pyproject exclude dirs / .gitignore / .dockerignore / AGENTS.md) from a single source of truth, and fixed 21 entries in en_GB mistakenly filled with Traditional Chinese, re-aligning the four-language catalogs to 594 entries each. ⑤ The mypy gate scope was pushed down to a single source of truth in `pyproject.toml [tool.mypy].files` (`src/` → the whole codebase, including root entry points / `build_exe.py` / `scripts` / `tests`), fixing 6 long-escaping type defects — among them the `gui.py` UI finalization path after a subprocess exits naturally, which **always raised `NameError`** (apart from that finalization path there is no functional behavior change); also fixed a Linux-CI "read-only config" test that stopped working because atomic-write `os.replace` only checks the directory permission. **No breaking changes** (all runtime semantics preserved). See [CODE_WIKI.md](CODE_WIKI.md) for full root-cause analysis and verification.

**🐛 Fixes**
- **Douyu "SRT only, no video" root cause + HLS segment-layer false-green probe**: the HLS playlist layer always returns 200, but the media segments land on another edge node and all return 404 → ffmpeg pulls zero media segments and produces zero bytes…
- **Source-selection hardening (config fallback / observability / same-origin candidate)**: `_hls_selection_config()` (reads `hls_collection_enabled`/`hls_collection_exclude_platforms` via `getattr(main, ..., default)`, defaults reachable, tolerates comma strings, no longer `AttributeError`-crashes on missing/type errors)…
- **Full code review (09-12, ~120 items)**: H-1 SHA256 pinning (`ffmpeg_install`/`node_install` `_sha256_of_file`/`_check_or_record_zip_sha256`, Lanzou `FFMPEG_LANZOU_SHA256`)…
- **CODE_REVIEW_FIX_1 batch (F-01~F-25)**: main.
- **F-13 Douyin signature kept unencoded**: cross-checked upstream `dart_simple_live` and confirmed it concatenates directly without `encodeComponent`, matching this repo byte-for-byte…
- **F-12 sync_http SSL scope narrowed**: `CERT_NONE` context and opener changed from import-time globals to lazy construction…
- **check_annotations violation fixed**: the triple-quoted docstring on `class _Cap:` in `tests/test_start_record_command_golden.py` was changed to a `#` line comment (conforming to the "no docstring" rule)…
- **mypy gate expansion + 6 type-defect fixes (09-15)**: triggered by 3 errors from the CI typecheck, which revealed that the gate only covered `src/` — root entry points and `tests/` had never been checked.
- **Linux CI read-only test fix (09-15, tests & docs only)**: `test_read_config_value_missing_key_readonly_ok` used `cfg.chmod(0o444)` to make the file "unwritable", but the write-back in `read_config_value` had been changed to `_atomic_write_text` (temp file in the same dir + `os.replace`) — `os.replace` only checks the write permission of the **containing directory**, not the target file's permission bits (and root bypasses them entirely), so on Linux the write-back still succeeded…

**✨ New Features / Improvements**
- **start_record command construction & platform dispatch single source of truth (F-01)**: the five inline `command=[]` lists were collapsed into module-level `_build_ffmpeg_output_args` / `_build_ffmpeg_input_args` / `_build_record_output_path` / `_ffmpeg_network_tuning`, with all container mapping going through `SEGMENT_FORMAT_BY_SUFFIX` (no raw literals)…
- **JS-signature-script hash pinning (F-25)**: `get_compiled_js` reads raw bytes and compares against the `_JS_SHA256_EXPECTED` baseline, warning by default and rejecting execution when `DLR_JS_STRICT_HASH=1`, closing the runtime surface for tampered signature scripts.
- **F-14 protobuf compatibility guardrail**: this environment has no protoc, so `douyin_pb2.py` is not regenerated (generated file is DO NOT EDIT)…
- **mypy gate scope pushed down to a single source of truth (09-15)**: `pyproject.toml [tool.mypy].files` is now pinned to `src` + root entry points (main / gui / web / i18n / msg_push) + `build_exe.py` + `scripts` + `tests`

**🛠️ Repo Maintenance & Quality Gates**
- **pyproject exclude dirs single-source completion**: `logs`/`backup_config` were previously only in some tools — now completed across black `.exclude`, isort `extend_skip`, mypy `exclude`, basedpyright `exclude`, and coverage `omit`, all with a unified "runtime-product dirs (maintained with .
- **.
- **Four-language catalog consistency fix**: fixed 21 en_GB entries whose values were mistakenly Traditional Chinese (7 danmaku-parse errors + 14 ffmpeg/Node install SHA256 prompts), re-filled with British English per the "en_GB differs from en_US only in spelling" rule…
- **Repo metadata sync**: `AGENTS.md` / `docker-compose.yaml` example version `4.1.0`→`4.2.0`

**🧪 Tests & Verification**
- Full `pytest` **974 passed / 2 skipped / 0 failed** (climbing 909→929→944→974)…
- `black --check --line-length 120 --target-version py314 .` 134 files green…
- After the 09-15 gate expansion: parameterless `mypy` **115 files, 0 issues** (covering src + root entry points + `build_exe.py` + `scripts` + `tests`)…

### v4.1.0 (2026-09-10 ~ 2026-09-11) — P0 fixes for missing ffmpeg `-reconnect*` values and HLS infinite reconnect (live recording yields subtitles but no video) / 28 code-review fixes / 8 decision + 4 machine-validation items / migration of 242 parameterized logs to i18n.tr / Web-panel narrow-viewport fix / four-language catalog completion

> This release (v4.1.0, 2026-09-10 ~ 09-11) fixes two P0 defects in the recording pipeline: ① moving the ffmpeg `-reconnect*` options before `-i` dropped the boolean value `1`, so real recording failed at input open with exit code -22; ② `-reconnect_at_eof 1` with an HLS(m3u8) input reconnects **infinitely at the playlist layer**, so the hls demuxer never pulls a single media segment — live recording looked like "only the danmaku SRT was produced, no video file". Also shipped 28 code-review fixes, the remaining 8 production-decision + 4 machine-validation items (hls.js pinning / TLS split-stream / audio-container alignment / `gui_legacy.py` removal / danmaku SRT off-loaded off the event loop / i18n `tr()` API, etc.), a full migration of 242 parameterized logs from f-string to `i18n.tr`, the Web-panel narrow-viewport fix, and an eight-file metadata sync plus four-language catalog completion (521 → 539 → 544 keys). **No breaking changes** (all recording/danmaku/network/push runtime semantics preserved). See [CODE_WIKI.md](CODE_WIKI.md) for full root-cause analysis and verification.

**🐛 Fixes**
- **P0 missing ffmpeg `-reconnect*` values → recording fails at startup with -22 (EINVAL)**: when the 09-10 review refactor moved `-reconnect_delay_max 60 / -reconnect_streamed / -reconnect_at_eof` from after `-i` to before it, the boolean values `1` of the last two options were dropped, so ffmpeg parsed the next option name as the value (`Unable to parse ... as boolean`) and failed before the input opened…
- **P0 disable `-reconnect_at_eof` for HLS(m3u8) inputs → live recording yields subtitles but no video**: the end of the HTTP response of an m3u8 playlist is itself an EOF, so the option makes the http layer reconnect infinitely right after the playlist is fully downloaded (measured signature: consecutive `Will reconnect at <size> in N second(s), error=End of file`, 1/3/7/15/31s backoff, no retry cap)…
- **28 code-review fixes (2026-09-10)**: `-reconnect*` established as "before `-i`, each option directly followed by its value"
- **Web-panel rooms-list narrow-viewport misalignment**: `table-layout: fixed` + single-line ellipsis on the URL/name columns (full URL visible on hover) + horizontal-scroll fallback at ≤768px, eliminating vertical header stacking, controls overflowing the card, and long-URL wrapping on narrow windows / high-DPI scaling.

**✨ New Features**
- **i18n `tr()` parameterized API + full migration of 242 sites**: `i18n.tr(template, **kw)` looks up first, then interpolates — fixing the root cause where f-string interpolation completed **before** the catalog lookup so placeholder keys could never match and translation silently fell back to the source text…
- **Web API auth hardening**: middleware now injects `X-Content-Type-Options: nosniff` / `X-Frame-Options: DENY`
- **hls.js pinned to 1.7.2**: `index.html` pins `hls.js@latest` to a concrete version (jsdelivr CDN supply-chain risk mitigation, aligned with the existing flv.js pinning convention).

**🛠️ Repo Maintenance & Quality Gates**
- **Remaining 8 production-decision + 4 machine-validation items**: all 8 decisions implemented — hls.
- **Metadata sync**: `uv.lock` project version aligned to 4.
- **Four-language catalog completion**: new strings added via `extract_i18n_strings.py`

**🧪 Tests & Verification**
- Full `pytest` **907 passed / 2 skipped / 0 warnings** (climbing 870 → 899 → 902 → 907)…
- `scripts/extract_i18n_strings.py`: 0 missing, zero four-language key-set differences…

<details><summary>Click to expand more historical versions</summary>

### v4.0.9.4 (2026-09-03 ~ 2026-09-06) — HLS capture exclusion list / quality-option add-drop & inline switching / P0 segmented-container mismatch fix / packaging defect fix / repo-wide comment completion & metadata sync

> This cycle (v4.0.9.4, 2026-09-03 ~ 09-06) is a consistency and quality wrap-up batch. New: an HLS capture exclusion-platform list config, and user-addable/droppable quality options with inline quality switching in GUI/WEB. Two high-severity issues fixed — Douyin original-quality HEVC was unrecordable due to a segmented-container mismatch (P0), and a cross-loop coroutine warning made pytest warnings fluctuate; also fixed a `pyproject.toml` packaging defect (undeclared sub-packages made `pip install .` emit an incomplete distribution). Also completed repo-wide Chinese comment completion (41 files / +1370 lines), eight-file metadata sync, and four-language catalog completion (516→521). **No breaking changes** (all runtime semantics preserved; the PEP 758 parenthesis-free `except` form only affects <3.14 — this repo's floor is 3.14, an established convention rather than a regression). See [CODE_WIKI.md](CODE_WIKI.md) for full root-cause analysis and verification.

**✨ New Features**
- **HLS capture exclusion-platform list**: new config key `HLS采集排除平台(逗号分隔)` — listed platforms ignore the "是否启用HLS采集" (enable HLS capture) switch and always use FLV capture…
- **Quality-option add/drop + inline switching**: quality options changed from a fixed 10-tier engine whitelist to a user-selected subset (stored in `config.ini` [录制设置] custom quality options)…
- **Standalone single-file build moved to `scripts/`**: `douyin_live_recorder_standalone.py` relocated from the repo root into `scripts/`, so the run command gains a `scripts/` prefix…

**🐛 Fixes**
- **P0 segmented-recording container mismatch**: Douyin original-quality HEVC was unrecordable because the TS+segment branch used the `ipod` container for `-segment_format`, causing `-c copy` to exit with `AVERROR(EINVAL)` (Windows exit code 4294967274)…
- **Flaky warning root-caused**: `src/async_http.py` dropped the cross-loop `run_coroutine_threadsafe(client.aclose(), ...)` dispatch branch (root cause: when the old loop had stopped but not closed, the coroutine was never awaited and GC raised "never awaited")…
- **GUI quality-switch three defects**: key-format mismatch (serial-number prefix caused the lookup table to miss), persistence loss (the editor still held the pre-write snapshot and got overwritten on save), and display reset (the table read stale subprocess log values) — after switching, the serial-number prefix is stripped before lookup, the editor snapshot is synced after write-back, and the display follows the config file.
- **Packaging defect fix**: `pyproject.toml`'s `[tool.setuptools].packages` changed from `["src"]` to `["src", "src.platforms", "src.proto"]`, fixing the `ModuleNotFoundError` at runtime when `pip install .` omitted `src/platforms` (per-platform danmaku collectors) and `src/proto` (Douyin protobuf).

**🛠️ Repo Maintenance & Quality Gates**
- **Repo-wide Chinese comment completion**: 41 files / +1370 lines (average density 7.
- **Eight-file metadata sync**: using `pyproject.toml` as the single source of truth, corrected version / path / directory-list / dependency drift across `AGENTS.md`, `docker-compose.yaml`, `requirements.txt`, `Dockerfile`, `.gitignore`, `.dockerignore`, and `.coveragerc-concurrency`.
- **Four-language catalog completion**: 5 missing strings added via `extract_i18n_strings.py`, all four catalogs re-aligned (521 entries each), `zh_CN.mo` recompiled (`--check` passes byte-level).
- **Test-output self-cleanup**: `tests/conftest.py` gained a `pytest_unconfigure` hook that deletes `tests/_out_live` / `tests/_out_e2e` after each session.

**🧪 Tests & Verification**
- Full `pytest` **858 passed / 2 skipped / 0 warnings**; `pytest tests/test_i18n.py` 34 passed (four-catalog key-set consistency).
- `mypy` / `basedpyright` (0 error / 0 warning) / `black --check` / `isort --check` / `scripts/check_annotations.py` all green…

### v4.0.9.3 (2026-09-02) — Full fixes for all 20 code-review findings (cookie-cache singleflight rewrite / Web non-ASCII password login crash / probe exception logging & throttle self-cleanup / 64-bit ctypes handle truncation / connection-resource lifecycle) + repo-wide mypy type-clean (tests / gui_legacy / scripts / standalone)

> This version is the full closure batch for the 20 findings of the Code Review Report, plus a repo-wide mypy static-type clean-up (0 issues across 102 source files, for the first time covering tests / gui_legacy / scripts and the standalone single-file build beyond the CI scope). Two high-priority fixes: ① the cookie cache's concurrent dedup was rewritten in singleflight style — the old implementation held a thread-affine `threading.RLock` across `await`, so concurrent coroutines in the same event loop could all re-enter the lock and mutual exclusion was completely void, with coroutines still hammering the same URL (precisely the risk-control trigger this module exists to eliminate); ② the Web panel's legacy plaintext-password compatibility path raised `TypeError` on non-ASCII passwords (`hmac.compare_digest` cannot compare str containing Chinese, making `/api/login` return a hard 500). The eight medium-priority items cover the Web API write path, the backup daemon's tight loop, probe exception logging and unbounded throttle dictionaries, 64-bit handle truncation, decorator fallback types, HTTP connection leaks, duplicate-implementation consolidation, and Session lifecycle; the eight low-priority items are redundancy and style cleanups. **No breaking changes** (runtime semantics such as cookie-cache TTL / no-cache-on-failure / probe backoff and throttling / Web API route contracts are all preserved). For detailed root cause and verification, see [CODE_WIKI.md](CODE_WIKI.md).

**🍪 Cookie-cache concurrent-dedup rewrite (high-priority fix)**
- **Root cause**: `fetch_cookies` originally held a `threading.RLock` across `await` — an RLock is thread-affine, and concurrent coroutines inside the same event loop all belong to one thread and could re-enter the lock, so mutual exclusion was completely void…
- **Singleflight rewrite**: a `threading.Lock` now protects only the synchronous reads/writes of the cache dict plus the in-flight registry `_inflight` (**never awaiting while holding the lock**)…
- **Robustness**: when the fetching coroutine is cancelled (room stopped / process exit), the `BaseException` branch immediately deregisters and delivers an empty result to waiters…
- Effect: with multiple rooms of the same platform recording concurrently, the visitor cookie for the same domain is no longer requested repeatedly, further lowering risk-control trigger probability.

**🔐 Web panel & system-tray defect fixes (high / medium-high / medium)**
- **Non-ASCII plaintext-password login 500**: the legacy plaintext compatibility path of `verify_web_password` now compares UTF-8 bytes via `hmac.compare_digest` (the str comparison does not support non-ASCII — a legacy plaintext password containing Chinese made `/api/login` return a hard 500)…
- **Unified Web API write path**: `PUT /api/rooms` now writes rows through `normalize_url` — the old write did not normalize the URL, inconsistent with the dedup criteria of add/delete/toggle, so a row written back by PUT could never be matched again in the next round.
- **64-bit ctypes handle truncation**: `web_tray.py` switches to `ctypes.WinDLL` with full explicit `argtypes`/`restype` declarations (`GetConsoleWindow.restype = c_void_p`), fixing HWND/HMENU truncation by the default `c_int` on 64-bit…

**🛡️ Daemon-thread & probe robustness (medium)**
- **Backup daemon tight loop**: in `config_io.py`, `time.sleep(600)` is moved out of `try` — the old exception branch did not wait, so persistent check_md5/backup failures degraded into a tight loop spinning hot, flooding logs and burning CPU.
- **Probe exception logging & recheck semantics**: `_confirm_get_ok` in `stream_select.py` gains `logger.debug` (with exception type + attempt number — no more silent swallowing), and an attempt-0 exception retries once after `_recheck_delay()` per the "retry before convicting" semantics, giving up the recheck only if both attempts raise (the HEAD conclusion stays "pass").
- **Throttle-dictionary self-cleanup**: `_throttle_probe` now evicts hosts idle for more than `_PROBE_MIN_HOST_INTERVAL × 10` while writing, so `_probe_last_seen` no longer grows unboundedly (mirroring the expiry-cleanup strategy of `_probe_backoff`
- **Danmaku sidecar logging**: the write-failure branch of `_write_line` in `danmaku_monitor.py` gains `logger.debug`, consistent with the module's "swallow all exceptions but always leave a trace" convention — sidecar data is no longer dropped without a trace.
- **Cancellation no longer swallowed**: the heartbeat-task reaper's `except asyncio.CancelledError, Exception:` in `ws_client.py` is split — `CancelledError` is only swallowed when hb_task itself is cancelled as expected…

**♻️ Resource management & fallback types (medium)**
- **Decorator fallback types**: the shared decorator implementation in `utils.py` is consolidated into `_make_trace_error_guard(func, fallback)`, adding `trace_error_decorator_or_none` (returns `None` on error), with error logs now naming both the function and the fallback value type.
- **Eliminating "errors disguised as normal results"**: 5 str/tuple-returning functions in `spider.py` (`get_bilibili_room_info_h5` / `login_sooplive` / `get_sooplive_tk` / `get_winktv_bj_info` / `login_flextv`) switch from the uniform dict fallback to the `None` fallback — the dict returned by a failed `login_flextv` was once misjudged as a successful login by `if new_cookies`.
- **Duplicate-implementation consolidation**: the verbatim-duplicate `unzip_file()` in `node_install.py` and `ffmpeg_install.py` is consolidated into the single `src/utils.py` implementation (with Zip Slip validation)…
- **Session lifecycle**: `sync_http.py` gains a `WeakSet` registry of thread-local Sessions, `close_session()` (explicit release for the current thread), and `close_all_sessions()` (registered with `atexit`, gracefully closing all connection pools on process exit).

**🧹 Style conventions / environment fixes (low)**
- **PEP 758 except style finalized**: real-machine testing showed black 26.
- **venv ghost problem fixed**: the editable install in `.venv` originally pointed at another checkout (`D:\DouyinLiveRecorder-coding`)…

**🧹 Repo-wide mypy clean-up**
- `tests/test_quality_tiers.py`: 5 sites gain `assert mock.await_args is not None` before `.args` access (typeshed declares `await_args` as Optional…
- `gui_legacy.py`: 4 fixes — hover-effect lambdas converted to named closure factories, the `command` parameter annotated `str | Callable[[], Any]`, `optionxform` assigned via a named function + `setattr` (following the `gui.py` convention), and the `collections.abc.Callable` import added.
- `scripts/extract_i18n_strings.py`: dynamic `getattr` results narrowed with `cast` (the `warn_return_any` gate), removing the now-useless `type: ignore`.
- **Standalone single-file build**: 4 warnings cleared in `douyin_live_recorder_standalone.py` — `cast` on `json.loads` return values, an `isinstance(sign, dict)` guard in `_douyu_sign` (non-dict returns `None` directly, eliminating a runtime crash), and a new `PlatformResolver` Protocol so the `PLATFORM_RULES` dispatch table supports `proxy=`/`cookies=` keyword calls…

**🧪 Tests and verification**
- `tests/test_cookie_cache.py` strengthened: `test_same_loop_reentrant_no_deadlock` now also asserts "5 coroutines gathered concurrently fetch exactly once" (the assertion necessarily fails under the old RLock implementation — exactly the target behavior of this fix)…
- Full `pytest`: **806 passed / 2 skipped / 0 failed**…
- web_tray live check: `WinDLL` loads successfully and the window-patching chain runs without exceptions (under headless, `GetConsoleWindow` returns empty and is skipped as expected).

### v4.0.9.2 (2026-08-28 ~ 2026-08-30) — Web panel manual recording control / Huya & Douyu fine-grained Blu-ray quality tiers / runtime log archiving on recording stop / performance review optimizations landed (P1~P5) / probe-backoff window self-healing & Huya FLV-first / Web background log-sink rebuild / GUI parent-process log-handle isolation

> This version advances four main lines — controllability, quality granularity, high-concurrency performance, and operability: the Web panel drops auto-start recording and gains manual "Start/Stop recording" control (a global switch + 7 interrupt points in the recording chain + tiered graceful ffmpeg termination); Huya/Douyu gain fine-grained Blu-ray tiers (BD4M/8M/20M/30M with a full select → pull → nearest-downgrade chain); the performance review landed five optimizations P1~P5 (per-round source-probe time for 80 rooms cut from 12.7s to 1.15s), and three rounds of real-machine verification root-fixed the Huya cold-start "probe false-green → ffmpeg 403" dead loop (backoff window aligned to the main loop + clear-on-success + Huya FLV-first) plus the issue of Web background-mode logs going to the hidden console window; as of 08-30 the stop-recording flow uniformly archives the four runtime logs by renaming them with a timestamp (conflicts get increments, missing files are skipped, handles are closed first), GUI parent-process and recorder-child log-handle isolation root-fixes the `streamget.log` rotation WinError 32 (silent total loss of recorder logs), and the i18n catalogs were replenished to 516 entries with `zh_CN.mo` recompiled. **No breaking changes** (config items and runtime semantics fully compatible; flipping Huya's candidate order to FLV-first is a behavior change, while Douyu keeps HLS-first). For detailed root cause and verification, see [CODE_WIKI.md](CODE_WIKI.md).

**🎥 Web panel manual recording control (new feature)**
- Global switch `main.recording_enabled` (defaults to True…
- **7 interrupt points** injected into the recording chain: the ffmpeg poll (1s period), chunk-level direct download, room-thread entry, direct-download failure classification exclusion, wait-period interruption, the pre-spawn check in the main loop, and the thread-exit finally fallback (`remove_room_from_running` idempotently cleans the running list so a room can be spawned again after restart).
- New `POST /api/recording/toggle` endpoint (inside the existing Bearer auth middleware) and a `recording_enabled` field in the status snapshot…
- **Stop semantics are active tiered graceful termination**: when the poll observes the switch off, ffmpeg is terminated via a three-level escalation "stdin 'q' (flushes the file trailer so TS/FLV/segments stay intact) → terminate → kill" (30s total window)…
- `recording_enabled` is a session-level runtime switch and is not persisted: the panel returns to the stopped state after restart, avoiding re-introducing "auto-record on startup" through the back door.

**🎚️ Huya/Douyu fine-grained Blu-ray quality tiers (new feature)**
- Quality-code layer expansion: `QUALITY_LEVEL` / `QUALITY_MAPPING_BIT` / `QUALITY_CODE_TO_ZH` grow from 6 to 10 items (adding `BD30`/`BD20`/`BD8`/`BD4`) plus the frozen `BD_SUB_TIERS` set…
- Huya: new `HUYA_FIXED_TIERS` (ratio = bitrate ceiling in kbps, appended to the FLV/HLS URL query for tier selection without changing the URL path)…
- Douyu: new `DOUYU_RATE_BY_CODE` / `DOUYU_RATE_TO_CODE` / `DOUYU_RATE_DESC`
- The Web panel's quality dropdown gains the BD30M/BD20M/BD8M/BD4M options…

**📼 Runtime log archiving on recording stop (new feature)**
- Two trigger points: the Web panel's "Stop Recording" **archives immediately** (the process keeps running…
- Archiving rules: the four runtime logs (`streamget.log` / `PlayURL.log` / `danmaku_monitor.jsonl` / `web_console.log`) are renamed to "originalname_YYYYMMDD_HHMMSS.
- Handle safety (on Windows, renaming a file with an open handle raises WinError 32): loguru file sinks are closed via `remove()`, which first flushes the async queue…
- Safety guards: the GUI parent process (`DLR_GUI_PARENT=1`) and test processes (`DOUYIN_DISABLE_LOG_ARCHIVE=1`) always return early, never renaming logs the recorder child is writing or the developer's real working-copy logs.

**⚡ Performance optimizations (review landed P1~P5)**
- **P1 probe-client reuse across the whole selection round**: all candidates in `select_source_url` share one `httpx.Client` (closed in `finally`, with UA/Referer/Cookie sent per-request)…
- **P2 thread-local `requests.Session` reuse**: `sync_http` keeps one Session per thread via `threading.local` (all 125 call sites benefit), measured 11.9ms → 1.47ms per request.
- **P3 set-based dedup containers in the main loop**: `url_comments` / `line_list` / `url_line_list` switch from list to set (membership checks O(N²) → O(1)), with `url_comments.discard` replacing the per-line whole-list rebuild.
- **P4 incremental scheduler counting**: the breaker window and the global error window are maintained incrementally (O(1) instead of an O(40) full sum under lock), shortening lock hold time.
- **P5 hot regexes hoisted to module-level constants**: five in-function `re.compile` sites (~400-char emoji pattern, URL fragments, HLS bandwidth, Douyin HEVC, etc.

**🐛 Bug fixes (derived from real-machine verification)**
- **Probe-backoff window self-healing (root cause of the Huya false-green dead loop)**: the original fixed 60s backoff window was shorter than the main loop's default 120s interval — after a fast failure was recorded into the backoff, the next round arrived at T+124s when the window had long expired, so the "CDN probe backoff" warning never once appeared in historical logs…
- **Clear probe backoff on recording success**: new `clear_ffmpeg_reject()` pairs with the failure-side `mark_ffmpeg_reject` — a recovered link is no longer skipped within the window, falling back to a worse line for nothing.
- **Huya flips to FLV-first**: three rounds of real-machine runs proved that all three HLS CDNs (hs/tx/al) probe false-green on cold start (probe 200/206, ffmpeg gets 403 on open) while FLV is stable every round (up to 6 minutes of continuous recording) — Huya's candidate order becomes FLV → HLS → record_url, cutting cold-start false-green losses from ~2 minutes to 0 (Douyu is never added: its guest-mode FLV is cut by the CDN after ~70s and must stay HLS-first)…
- **Web background-mode log-sink rebuild**: a loguru sink binds to the concrete object at `add()` time and does not follow a later `sys.stderr` reassignment — without a rebuild, all DEBUG/WARNING goes to the SW_HIDE-hidden console and `web_console.log` keeps only print output (this once led to misreading "probe false-green" as "validation never ran")…
- **Two-pass review fixes for the recording control**: the frontend state-label selector defect (the container is a class but an `#id` selector was used, so the label never toggled, P1) and 2 more.
- **GUI parent-process log-handle isolation**: the GUI process (which initializes file sinks via the `src.web_config → src/__init__ → src.logger` import chain) and the recorder child process both held `streamget.log` open — whichever side crossed the 300 KB rotation threshold had to rename first, and the other's open handle raised `PermissionError: [WinError 32]`, so rotation never succeeded and the recorder child's file logs were silently lost in full (measured: stuck at 300031 bytes, the GUI panel flooded with Logging errors)…
- **Type fix**: `src/stream.py` completes the `bitRate: int` field declaration of the `HuyaGameLiveInfo` TypedDict and removes the `# type: ignore` (newer mypy reports `call-overload` on the degraded type of an undeclared key) — zero runtime semantics change, `mypy src/` back to fully green.

**🔧 CI / engineering maintenance**
- **i18n four-language catalog completion (507 → 516 entries)**: the 9 new log strings introduced by the archiving feature were added to `zh_CN.po` / `en_US.json` / `en_GB.json` / `zh_TW.yaml` (Traditional Chinese following the existing vocabulary conventions: 日志→日誌, 文件→檔案, 归档→歸檔, 句柄→控制代碼), with `zh_CN.po` gaining a "Log Archive Module" section and `zh_CN.mo` recompiled (`--check` byte-level sync)…
- **Repo metadata sync-list alignment**: a consistency audit of the nine config files (`AGENTS.md` / `docker-compose.yaml` / `requirements.txt` / `Dockerfile` / `.gitignore` / `.dockerignore` / `.coveragerc-concurrency` / `pyproject.toml` / `uv.lock`) — dependencies identical in all three places (20=20), `uv lock --check` in sync, Dockerfile (python:3.

**🧪 Tests and verification**
- Archiving-specific: new `tests/test_log_archive.py` (14 cases: regex lock on the rename format, `_N` sequence dedup without overwriting, empty directory skips all, a single failed rename doesn't interrupt the batch, GUI/test-process guards, both `reopen_streams` semantics, web_console bound-handle rotation, lazy reopen after hub `close_file`, sink remove→add round-trip idempotency, and a static lock on main.
- Added `tests/test_quality_tiers.py` (29 cases: sub-tier mapping / index folding / Huya nearest-downgrade / Douyu retry chain) and `tests/test_logger_console_sink.py` (3 cases: follow current stderr / replace not append / silent on None)…
- Full `pytest`: **806 passed / 2 skipped** (0 warnings…
- Three rounds of real-machine verification (Huya 880214 / chuhe, Douyu 3168536): the backoff warning appears for the first time, FLV records steadily for 6 minutes, `web_console.log` regains full DEBUG/WARNING…

### v4.0.9.1 (2026-08-27 ~ 2026-08-28) — High-concurrency scheduler hardening / localization system fixes / compile & circuit-breaker gate fixes / CI workflow optimization and retry consolidation

> This version is a review-fix and hardening batch for the 4.0.9 scheduling system, plus a wrap-up of the localization subsystem: full quality gates and parallel code review uncovered and fixed several high/medium-severity defects, the i18n catalogs were fully replenished to 496 entries via a repo-wide AST scan, the i18n module syntax block was removed, and `zh_CN.mo` was recompiled; on 08-28 a CI workflow optimization (retries consolidated into a composite action), PEP 758 formatting landed via black 26, and an eight-file repository metadata sync were appended. **No breaking changes** (config items and runtime semantics are fully compatible). For detailed root cause and verification, see [CODE_WIKI.md](CODE_WIKI.md).

**✨ New features**
- **Web config line-append API**: `web_config.py` gains `append_config_line(config_file, section, key, value)`, a line-level append that builds a missing key/section (complementing the existing `update_config_line`), enabling safe writes to key-less configs.
- **Language-switch write-back degradation**: `web_api.py`'s `PUT /api/language` write-back now calls `append_config_line` to append at section end when line-level replacement fails, so a missing `language` key in historical config.
- **Full i18n catalog replenishment (288 → 496 entries)**: AST-scanned all runtime `print()`/`logger.*()` constant strings (47 files, 355 strings) and added 204+ translations (concurrency-scheduling logs, the full stream-URL validation set, the Bilibili buvid auth chain, danmaku capture/monitoring, seven-channel push-failure branches, ffmpeg/Node.
- **CI network-install retry composite action (`.github/actions/retry`)**: a new composite action uniformly wraps pip / apt / choco / brew network-install commands with linear-backoff retries (`command` / `label` / `attempts` / `backoff` parameterizable), replacing 13 nearly identical inline retry scripts across the two workflows (9 in ci.

**🐛 Bug fixes**
- **i18n localization system block (high-severity)**: `i18n.py` (3 sites) and `scripts/compile_po.py` (1 site) had Python 2-style `except A, B:` multi-except clauses (one with three-exception commas) changed to `except (A, B):`, removing the Python 3 hard `SyntaxError` that previously prevented `i18n` from being imported, blocked `.mo` compilation, and disabled CLI/GUI/Web localization…
- **CI black gate (PEP 758 formatting)**: those 4 tuple-parenthesized sites were then unified back to the bare-comma form by black 26.
- **Always-true compile-sync gate (P1)**: `scripts/compile_po.py`'s `write_mo()` now produces output purely in memory (removed the write-to-disk side effect), with the flush decision moved up to the caller, so `--check` no longer writes then reads back and compares against itself (previously always true) and now really compares against the committed `.mo`
- **Circuit-breaker probe-lease self-healing (high-severity)**: root fix for the `PlatformBreaker` half-open probe leak — when the probe round ends via `continue` without reporting a sample, the `_probing` flag never resets and the host stays permanently circuit-broken until restart…
- **Scheduler success-sampling gap (medium-severity)**: the parse-success branch of `start_record` now reports `record_success(record_host)` (symmetric with the failure branch), so other rooms on the same host no longer starve while a half-open probe room is in a long recording.
- **Direct-download circuit-breaker sampling gap (P1)**: in `main.py`, the direct-download branch's "non-200 / network exception" failures were previously swallowed inside the function as `False` and the caller reported no sample, so bad links bypassed per-host circuit-breaking and were retried forever…
- **Scheduler thread-safety + type/logging**: `ConcurrencyScheduler` config fields are now locked (single-lock snapshot + in-lock write), eliminating the theoretical race between the main thread and the `adjust_loop` daemon…
- **Missing direct-download logs**: `main.py`'s `direct_download_stream` now logs the request URL on the non-200 branch and `{type(e).__name__}` on the exception branch (on Windows, `str()` of timeout exceptions is empty)…
- **Per-round danmaku-arg reset restored**: the inner monitor loop in `main.py` again resets `record_danmaku_args = None` at the top (a prior refactor had merged the in-round reset points).
- **Corrupted YAML catalog causing 500**: `_load_yaml_catalog()` now also catches `yaml.YAMLError` (not an OSError/ValueError subclass), degrading to the next format.
- **Missing ISSUE_TEMPLATE version**: the Python-version dropdown in all four `.github/ISSUE_TEMPLATE` files adds `Python 3.14`.
- **Two i18n extractor noise sources**: `scripts/extract_i18n_strings.py`'s `is_valuable()` now judges by the residue outside brace blocks (pure-placeholder templates like `{color}{text}` are no longer falsely reported as missing), and the po header empty `msgid ""` is excluded before comparison (removing the "missing 1" false positive in the four-language consistency check)…

**🎨 UX optimizations**
- **Frontend hardcoded Chinese moved into the translation dictionary**: `web/app.js` ~10 hardcoded Chinese strings now go through the inline four-language dictionary `t()` (recording/danmaku empty states, truncation hint, toggle/action toasts, config/file-list empty states, enter/download buttons, etc.
- **GUI crash-dialog dedup**: top-level exceptions in `gui.py` no longer produce double dialogs / doubly-stacked logs…

**🔧 CI / engineering maintenance**
- **CI workflow optimization (ci.
- **Eight-file repository metadata sync**: corrected the stale `src/danmaku/` path comments in requirements.

**🧪 Tests and verification**
- Added `tests/test_record_failure_feedback.py` (5 → 7 cases) and `tests/test_web_api.py` missing-key-build/edge cases…
- Full `pytest`: **744 passed / 2 skipped**…

### v4.0.9 (2026-08-23 ~ 2026-08-24) — High-concurrency multi-platform recording scheduler optimization / recording-feedback loop / dual concurrency modes / Python 3.14 upgrade and language-key migration / four-language catalog unification and British-American split / type and CI quality-gate fixes

> This batch focuses on the scheduling-hub governance for high-concurrency (80+ tasks) multi-platform recording, the recording-side feedback loop, and the Python 3.14 baseline upgrade. For detailed root cause and verification, see [CODE_WIKI.md](CODE_WIKI.md).

**🚀 High-concurrency scheduling hub (new src/scheduler.py)**
- Introduces `ResizableSemaphore` (runtime-resizable capacity), `PlatformBreaker` (per-host circuit breaker with closed→open→half-open state machine), `ConcurrencyScheduler` (adaptive global concurrency capacity, default floor 8 / ceiling 128, gently throttling under high error rate but never below the safe floor), and `host_of(url)`.
- Replaces the old "global fixed 3-slot semaphore + one-way error-rate suppression" model, supporting 80+ concurrent cross-platform recordings with reduced queueing latency…
- Wired in only at fixed integration points in `main.py` / `notify.py`, leaving the 50+ platform dispatch/recording functions untouched (backward compatible)…

**🔁 Recording-result feedback loop (root-cause fix for the Huya 403 retry loop)**
- Fixed missing recording-side feedback: `check_subprocess` previously neither reported a failure sample by exit code nor (at round end) unconditionally reported success, diluting the per-host circuit-breaker stats so they never tripped — Huya rooms infinitely re-hit the dead "probe 200 → ffmpeg 403" route.
- Now reports success/failure samples by host by exit code…
- The console status line now shows the scheduler's real-time concurrency capacity (`_live_network_capacity`) instead of the misleading static config value.

**⚙️ Dual network-concurrency modes (dynamic / fixed)**
- Adds a "fixed concurrency" mode on top of adaptive capacity: "最大同时录制数(0=不限制)" also acts as a mode switch — =0 enables dynamic throttling (capacity adapts to active task count, floor 8 / ceiling 128)…
- Per-host platform circuit breaking is orthogonal to the mode and works under both; the simultaneous-recording cap is still governed by `scheduler.set_recording_limit` and unaffected by mode switching.

**🐍 Python 3.14 upgrade + language-key migration (general maintenance)**
- Project baseline raised from Python 3.
- `config.ini` language key `language(zh_cn/en)` unified into `language`: empty follows system language, illegal values fall back to en_US, GUI/Web panels hot-switch without restart, and old keys are auto-migrated at startup.
- Fixed 21 Python 2-style `except A, B:` legacy syntax errors across 14 source files so the project imports/tests under Python 3…

**🌐 Four-language catalog unification and British/American split**
- Unified zh_CN.po / en_US.json / en_GB.json / zh_TW.yaml to the same 288-key set (original 282 + 6 build/smoke constant strings added from build_exe.py).
- Fixed en_US's internally mixed British spellings (now consistently American: minimizes/minimized/canceled)…
- Recompiled zh_CN.po → zh_CN.mo (compile_po.py --check confirms byte-level sync), with no runtime-logic changes.

**🧪 Type-check / CI quality-gate fixes**
- Fixed two CI `mypy src/` errors: `i18n.py`'s `ctypes.WinDLL` platform gate (`sys.platform != "win32"` early return, clean on both ends), and `src/recorder_status.py`'s three-arg `getattr` changed to direct attribute access (eliminating the `no-any-return` leak).
- Fixed CI `pytest` assertion failure under C/POSIX locale where `detect_system_language()`'s `locale.getlocale()` fallback did not filter `("C", "POSIX")`
- Fixed `src/config_io.py`'s `read_config_value()` write-back crash where Python 3.
- Repo-wide black 26.

**📦 Build / dependencies / platform adaptation**
- Version bump `4.0.8.3` → `4.0.9` (single source of truth); `requires-python` raised to `>=3.14`, classifiers narrowed to 3.14 only; added `PyYAML>=6.0.3` dependency (for i18n's zh_TW.yaml support).
- `Dockerfile` base image upgraded to `python:3.14-slim-bookworm`, Node.js source `setup_22.x` → `setup_24.x`; CI matrix synced to 3.14.
- `src/spider.py`'s Migu `get_migu_stream_url()` now uses the rewritten `migu.js` that outputs the complete URL with `ddCalcu`/`sv` params (dropping the local stale fixed `sv=10010`)…

### v4.0.8.3 (2026-08-19 ~ 2026-08-22) — Auto anchor-name update / SSL config consolidation / four-language i18n / FFmpeg9·Node24 compatibility / type-safety hardening / start_record complexity governance / windowed-crash hardening / type-check defect fixes

> This version builds on the 4.0.8.2 fixes with several new capabilities and low-level compatibility, closing out with all five quality gates (mypy / basedpyright / pytest (0 warnings) / black / isort) green. For detailed root cause and verification, see [CODE_WIKI.md](CODE_WIKI.md).

**👤 Auto anchor-name update (new feature)**
- Each time `URL_config.ini` resolves the latest anchor name, if it differs from the config, the config file is auto-written back…
- Added `src/config_io.py:update_anchor_name` + `main.py:rename_anchor_directory`

**🔒 SSL / HTTPS config consolidation**
- The old "是否强制启用https录制" + "是否禁用SSL证书验证(是/否)" are merged into a single "是否启用https录制": enabled = https pull + skip cert verification, disabled = http pull + default strict verification.
- The main loop hot-syncs `set_https_recording` / `set_ssl_verify` each round…
- The platform-level override `禁用SSL证书验证的平台(逗号分隔符)` only takes effect in http mode (when cert verification is needed)…

**🌐 Four-language i18n rebuild + instant switching**
- `i18n.py` rebuilt: multi-format catalog loading (gettext `.mo` → `<lang>.json` → `<lang>.yaml`), `SUPPORTED_LANGUAGES` (zh_CN/en_US/en_GB/zh_TW), `normalize_language()` alias normalization, `set_language()` hot switch (no restart).
- The zh_CN catalog is completed to 282 entries…

**⚙️ FFmpeg 9.0 / Node 24 compatibility baseline**
- Repo-wide ffmpeg command audit aligned to FFmpeg 9.
- `src/javascript/migu.js` fully rewritten: adapts to Migu player mgprtcl.

**🧪 Type-safety hardening (all five tools green)**
- mypy tests/ went from 435 errors → 0 (auto-annotation of ~420 sites + manual fix of ~60 real type issues)…
- New test coverage: 5 language API, 10 new i18n features, 3 SSL platform auto-append, 2 new SSL semantics, 1 migu output contract, 21 auto anchor-name update.

**🧹 start_record complexity governance (code quality)**
- The platform-dispatch if/elif chain (52 platform branches) in `main.py:start_record` (originally ~1600 lines) is extracted into a standalone module-level function `_resolve_platform_stream`

**🧩 Type-check defect fixes (code quality)**
- `i18n.py`: `import yaml` gets a `# type: ignore[import-untyped]` to suppress the optional-dependency missing-stub hint (preserving the runtime degrade "missing only loses YAML format" semantics per AGENTS.
- `gui.py`: `messagebox` changed from attribute-style `_tk.messagebox` to an explicit `from tkinter import messagebox as _mb` import (two crash popups), eliminating `reportAttributeAccessIssue`

**🪟 Windowed-run crash observability hardening (defect fix)**
- Fixed the problem where running the GUI via `pythonw.exe` (and the `console=False` frozen exe) produced **no window and no error at all**: root cause was `src/logger.py` calling `logger.add(sink=sys.stderr, ...)` at import time, which throws `TypeError: Cannot log to objects of type 'NoneType'` when `sys.stderr=None`, silently exiting on the import chain.
- `gui.py` adds `_install_crash_sink()` at the top: before **all risky imports**, install `sys.excepthook` / `threading.excepthook` to write the full stack of uncaught exceptions (including import-time failures) to `%TEMP%/douyin_recorder_gui_error.log` and best-effort show an error box, root-causing the silent windowed death…

**📚 Architecture doc update**
- `CODE_WIKI.md` completed with the danmaku collection subsystem (base class / collector / 5 platform clients / monitor hub / SRT / WS / visitor Cookie cache / protobuf), `src/platforms` and `src/proto` module descriptions, module dependency graph, and design patterns…

### v4.0.8.2 (2026-08-16 ~ 2026-08-18) — Recording/danmaku/i18n/type-check series of fixes

> This batch concentrated on fixing several long-standing "runs but recording/danmaku often fail" issues, verified via real-device end-to-end testing. Outlined by module below; detailed root cause and verification in [CODE_WIKI.md](CODE_WIKI.md).

**🎯 Recording engine core fixes (affects all platforms)**
- **Fatal structural bug**: the recording main chain was nested inside the `if headers:` condition, causing platforms without dedicated request headers (Douyin/Douyu, etc.
- **Douyu crash fix**: when `select_source_url` returns empty, no more `UnboundLocalError` (title variable unbound) — it warns and waits for the next round…
- **Three-layer stream-URL check risk reduction**: added "probe throttling + retry jitter + backoff after rejection (Huya only)" to eliminate the 403 failure loop caused by CDN fingerprinting the bot-pace rhythm…
- **HTTPS/SSL config consolidation**: `是否启用https录制` (merging the old `是否强制启用https录制` and `是否禁用SSL证书验证(是/否)`) — enabled = https pull + skip cert verification, disabled = http pull + default cert verification.

**🐯 Huya specifics (multi-CDN source selection + Referer correction)**
- Changed to **enumerate all CDN candidates** (HS/HW/TX/AL) instead of always taking the first or always preferring TX…
- **Referer rule removed**: Huya CDN now validates in reverse — **with a Referer it always returns 403…
- The App path (`get_huya_app_stream_url`) does the same `tars_mp→huya_webh5`/`bhct→bgct` param substitution as `record_url` when TX is selected, root-causing the regression where "after priority source selection, TX still carried the original `tars_mp` causing second-level stream drops".

**📺 Bilibili danmaku auth chain closed**
- Fixed the spi endpoint spelling (`/finger/sp` → `/finger/spi`, the missing trailing `i` caused 200+empty body)…
- The danmaku room-entry packet **passing the anchor uid as the viewer uid** (causing AUTH soft-rejection — connection kept, 0 danmaku) is fixed…
- The danmaku triple (OD/BD/UHD app paths) returns are completed, eliminating the original silent skip.

**🌐 i18n mechanism fix**
- Supplied the missing `zh_CN.mo` compiled artifact and ships it with the repo…

**🍪 Unified visitor Cookie cache**
- Added `src/cookie_cache.py`: a process-level shared cache keyed by "normalized URL + proxy", so common visitor cookies like Douyin ttwid and Kuaishou did are reused across modules/rooms from a single copy, **eliminating repeated fetches of the same URL triggering risk control**.

**🧩 Architecture and quality**
- `main.py` split 6 categories of functionality into `src/` submodules (ffmpeg_proc / video_postprocess / stream_select / notify / recorder_status / config_io), kept compatible via re-export…
- Config robustness: when `config.ini` is not writable, the `import main` stage no longer crashes (best-effort read-back)…
- Repo-wide UA uniformly upgraded to the 2026 baseline (Chrome/141, Firefox/148, mobile Android 14 Chrome/141), eliminating stale fingerprints.

**🛡️ Platform compatibility and runtime robustness**
- **Cross-event-loop lock misjudged as risk control, root-caused** (`src/async_http.py`): the module-level singleton `asyncio.Lock()` lazily bound to the first room's `asyncio.run()` loop, so when later rooms started new loops and awaited it again, it threw `bound to a different event loop`, which `async_req` swallowed and returned an empty string, causing `spider.py` to misjudge "risk-control empty response" and cascade into failed HTML-scrape fallback.
- **Blank exception log containment**: `async_req` / `_close_all_clients` and the old cross-loop client-close sites originally used `logger.debug(e)`, which under Windows prints blank logs when the exception's `str()` is empty and cannot be located…
- **Platform compatibility fixes**: `web.py` ctypes 3.

**🧪 Static check / CI hardening**
- mypy / basedpyright fully cleared in `src/` and `main.py` (including spider.
- Script robustness: `scripts/check_coverage.py` fixed global coverage < 50% silently skipping the gate, temp-file leftovers, and `subprocess.run` missing `encoding` (crash on Windows non-UTF-8 locale)…
- CI `lint` job Python upgraded from 3.12 to 3.13 (aligned with the highest `target-version`, eliminating AST safety-check warning noise); `black --check .` format violations manually fixed.
- Full test run ~635 passed / 2 skipped (excluding known sandbox delete-protection items).

### v4.0.8.1 (2026-08-01 ~ 2026-08-09) — Comment convention / smoke testing / GUI graceful exit / check fixes, consolidated

**Comment convention and quality baseline**
- Module/function docs uniformly use `#` line comments, no longer triple-quoted `"""` docstrings.
- Full audit passed: `compileall` / `black` (line-width 120) / `isort` / `mypy` (src/) / `pytest` all green (417 passed, no regression…
- ⚠️ **Build bug fix (`pyproject.toml`)**: `email="ihmily@github"` is not a valid IDN email, so new setuptools refuses to build and `pip install .` always fails…

**New Web/API smoke-test tool**
- `scripts/smoke_test.py` (**zero-dependency, config-driven**): supports GET/POST, `base_url` concatenation, expected status code, text/JSON assertions…

**GUI stop-recording graceful-exit hardening**
- **Root cause**: when `pythonw.exe` launches the GUI, `sys.executable` points to the console-less pythonw, so the recording subprocess it spawns is also console-less → `AttachConsole` must fail, CTRL_BREAK structurally unreachable…
- CTRL_BREAK failure falls back to `taskkill /F /T /PID` whole-tree termination (with ffmpeg cleanup); logs honestly distinguish "graceful exit" from "hard-kill path".
- Verified: after reproducing the pythonw parent process, `AttachConsole` succeeds and the `SIGBREAK` handler fires (`signum=21`)…
- ⚠️ **Leftover (unchanged)**: the old `gui_legacy.py` launches subprocesses with `CREATE_NO_WINDOW`, so `send_signal(CTRL_BREAK_EVENT)` is silently ineffective and graceful stop never worked (always waited 15s then force-killed)…

**Stream-URL check fixes (HLS/proxy/log)**
- Blank-log containment: `get_response_status` exception logs now include the URL and exception type (e.
- m3u8 misjudgment fix: HEAD probe range extended from `400/401/403/405` to **all non-2xx including 404**…
- `_validate_stream_url` adds a `verify` param honoring the global SSL toggle, with all failure paths logging warnings (URL + exception type/status code/content-type).
- `select_source_url` adds `proxy_addr` and forwards it to the three check sites, fixing TikTok and other proxy-required platforms being mis-judged unreachable on direct-connect timeout.

**Douyin recording enhancements**
- Supports 5 URL formats: web/app live room, Douyin-id concatenation (incl. VR), app/web anchor profile.
- The anchor profile (format 5) directly extracts `sec_user_id` to skip redundant downloads, cutting requests 4→3…
- When the CDN returns 4xx to HEAD, a `Range` GET probe is added…

### v4.0.8 (2026-07-30) — Web panel / quality monitoring / proxy and type fixes

- **New Web management panel** (`web.py`+`src/web_api.py`+`src/web_config.py`+`web/`): dashboard, room management, config editor, SSE log push.
- **New GUI quality monitoring**: real-time check of whether actual quality matches the setting, covering Douyin/TikTok/Kuaishou/Huya/Douyu/Bilibili/NetEase CC, seven platforms.
- **New config items**: `web_show_console` (hide and run in background), global SSL cert-verification toggle (config.ini), log-file toggle.
- **Connection optimization**: HTTP client reuses connection pools by (proxy, verify, http2); proxy detection changed from network probing to reading local system proxy config.
- **Defect fixes**: `trace_error_decorator` sync decorator misused on 71 async functions causing error capture to fail…
- **Credential cleanup**: hardcoded expired credentials changed to auto-fetch (Douyin ttwid, Kuaishou did, Twitch Client-Id, etc.).
- **Build/deps**: Dockerfile upgraded to Node.js 22 LTS, non-root run; added `pydantic>=2.0.0` dependency declaration; repo-wide type-check (Pyright/Pyrefly/basedpyright) cleanup.

### v4.0.7 (2025-10-24)

- Fixed Douyin risk control preventing data retrieval
- Added soop.com recording support
- Fixed bigo recording

### v4.0.6 (2025-01-27)

- Added Taobao, JD, faceit live recording
- Fixed Xiaohongshu live-stream recording and transcoding issues
- Fixed Changliao, VV Planet, flexTV live recording
- Fixed batch WeChat live push
- Added email SSL and port config
- Added forced h264 transcode config
- Updated ffmpeg version
- Refactored the package into async functions!

### v4.0.5 (2024-11-30)

- Added shopee, youtube live recording
- Added support for custom m3u8, flv address recording
- Added custom execution scripts, supporting python, bat, bash, etc.
- Fixed YY Live, Huajiao Live, and Xiaohongshu Live recording
- Fixed Bilibili title fetch error
- Fixed log errors

### v4.0.4 (2024-10-30)

- Added 10 platform live recordings: Haixiu Live, VV Planet Live, 17Live, LangLive, SOOP, Changliao Live, Piaopiao Live, 6Rooms Live, Lehai Live, Huamao Live
- Fixed Xiaohongshu Live recording, supporting recording from Xiaohongshu author profile addresses
- Added ntfy message push support, plus batch push to multiple addresses
- Fixed Liveme Live and Twitch Live recording
- Added a one-click Windows stop-recording VB script

### v4.0.3 (2024-10-05)

- Added email and Bark push
- Added live-comment stop-recording
- Optimized segmented recording
- Refactored parts of the code

### v4.0.2 (2024-09-28)

- Added Zhihu Live and CHZZK Live recording
- Fixed Yinbo Live recording

### v4.0.1 (2024-09-03)

- Added Douyin dual-screen recording and Yinbo Live recording
- Fixed PandaTV and bigo Live recording

### v4.0.0 (2024-07-13)

- Added Inke Live recording

### More historical versions...

</details>

## 💬 For questions or requests, please open an Issue. Stars and Forks are welcome

[![Star History Chart](https://api.star-history.com/svg?repos=y123ao6/DouyinLiveRecorder&type=Timeline)](https://star-history.com/#y123ao6/DouyinLiveRecorder&Timeline)
