# -*- encoding: utf-8 -*-

"""
Author: DouyinLiveRecorder Contributors
Function: Browser-based live stream recorder with two modes:
  - FALLBACK: Capture stream URL via network interception (default)
  - SCREENCAST: Directly record browser-rendered video via screen capture
"""

import asyncio
import os
import time
import threading
from typing import Optional, Dict, List, Callable
from .logger import logger
from .utils import trace_error_decorator

OptionalStr = str | None
OptionalDict = Dict | None

BROWSER_MODE_FALLBACK = "fallback"
BROWSER_MODE_SCREENCAST = "screencast"

PLATFORM_STREAM_PATTERNS = {
    "douyin": {
        "url_patterns": [".m3u8", ".flv", "douyincdn.com", "bytecdn.cn", "bytegoofy.com", "bytetos.com", "volces.com"],
        "anchor_selectors": [
            '[data-e2e="live-room-anchor-name"]',
            '.anchor-name',
            '.DYLiveRoomAnchorName',
        ],
        "wait_time": 8000,
    },
    "tiktok": {
        "url_patterns": [".m3u8", ".flv", "tiktokcdn.com", "ttwstatic.com", "tiktokv.com"],
        "anchor_selectors": [
            '[data-e2e="live-room-anchor-name"]',
            '.anchor-name',
        ],
        "wait_time": 10000,
    },
    "bilibili": {
        "url_patterns": [".m3u8", ".flv", "bilivideo.com", "akamaized.net"],
        "anchor_selectors": [
            '.live-room-anchor-name',
            '.room-title',
            'h1.title',
        ],
        "wait_time": 8000,
    },
    "kuaishou": {
        "url_patterns": [".flv", ".m3u8", "ksapisrv.com", "kspkg.com", "kuaishou.com"],
        "anchor_selectors": [
            '.user-name',
            '.live-room-anchor',
        ],
        "wait_time": 8000,
    },
    "huya": {
        "url_patterns": [".flv", ".m3u8", "huya.com", "msedgecdn.net", "myqcloud.com"],
        "anchor_selectors": [
            '.host-name',
            '.room-title',
        ],
        "wait_time": 8000,
    },
    "douyu": {
        "url_patterns": [".flv", ".m3u8", "douyucdn.cn", "douyutvlbs.com", "douyucdn2.cn"],
        "anchor_selectors": [
            '.anchor-name',
            '.Title-anchorName',
        ],
        "wait_time": 8000,
    },
    "xiaohongshu": {
        "url_patterns": [".m3u8", ".flv", "xhscdn.com", "xiaohongshu.com"],
        "anchor_selectors": [
            '.user-name',
            '.anchor-name',
        ],
        "wait_time": 10000,
    },
    "youtube": {
        "url_patterns": [".m3u8", "googlevideo.com", "videoplayback"],
        "anchor_selectors": [
            'ytd-channel-name',
            '#owner-name',
        ],
        "wait_time": 12000,
    },
    "twitch": {
        "url_patterns": [".m3u8", "ttvnw.net", "jtvnw.net", "usher.ttvnw.net"],
        "anchor_selectors": [
            '[data-a-target="channel-display-name"]',
        ],
        "wait_time": 10000,
    },
    "default": {
        "url_patterns": [".m3u8", ".flv"],
        "anchor_selectors": [],
        "wait_time": 8000,
    },
}

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--autoplay-policy=no-user-gesture-required",
    "--disable-extensions",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--no-first-run",
    "--no-default-browser-check",
    "--use-fake-ui-for-media-stream",
    "--use-fake-device-for-media-stream",
]

SCREENCAST_LAUNCH_ARGS = LAUNCH_ARGS + [
    "--disable-gpu",
]


_PLATFORM_MAP = {
    "douyin.com": "douyin",
    "tiktok.com": "tiktok",
    "bilibili.com": "bilibili",
    "kuaishou.com": "kuaishou",
    "huya.com": "huya",
    "douyu.com": "douyu",
    "xiaohongshu.com": "xiaohongshu",
    "xhslink.com": "xiaohongshu",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "twitch.tv": "twitch",
}


def _get_platform_key(url: str) -> str:
    for domain, key in _PLATFORM_MAP.items():
        if domain in url:
            return key
    return "default"


def _parse_cookie_str(cookie_str: str, url: str) -> List[dict]:
    if not cookie_str or not cookie_str.strip():
        return []
    cookies = []
    domain = url.split("/")[2] if "/" in url else url
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            name, value = item.split("=", 1)
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": domain,
                "path": "/",
            })
    return cookies


class BrowserRecorder:
    _playwright = None
    _browser = None
    _lock = None
    _initialized = False

    def __init__(self):
        self._screencast_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        if not BrowserRecorder._initialized:
            BrowserRecorder._lock = asyncio.Lock()
            BrowserRecorder._initialized = True

    @classmethod
    async def _get_browser(cls, proxy_addr: OptionalStr = None, headless: bool = True):
        async with cls._lock:
            if cls._browser is not None and cls._browser.is_connected():
                return cls._browser
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                logger.error(
                    "playwright is not installed. "
                    "Run: pip install playwright && playwright install chromium"
                )
                return None
            cls._playwright = await async_playwright().start()
            proxy_config = {"server": proxy_addr} if proxy_addr else None
            args = LAUNCH_ARGS if not headless else SCREENCAST_LAUNCH_ARGS
            try:
                cls._browser = await cls._playwright.chromium.launch(
                    headless=headless,
                    args=args,
                    proxy=proxy_config,
                )
            except Exception as e:
                logger.error(f"Failed to launch browser: {e}")
                return None
            return cls._browser

    @classmethod
    async def close(cls):
        async with cls._lock:
            if cls._browser:
                try:
                    await cls._browser.close()
                except Exception:
                    pass
                cls._browser = None
            if cls._playwright:
                try:
                    await cls._playwright.stop()
                except Exception:
                    pass
                cls._playwright = None

    @trace_error_decorator
    async def extract_stream(
        self,
        url: str,
        platform: str = "",
        proxy_addr: OptionalStr = None,
        cookies: OptionalStr = None,
        timeout: int = 30,
    ) -> dict:
        """Fallback mode: capture stream URL via network interception"""
        platform_key = _get_platform_key(url) if not platform else platform
        config = PLATFORM_STREAM_PATTERNS.get(platform_key, PLATFORM_STREAM_PATTERNS["default"])

        browser = await self._get_browser(proxy_addr)
        if browser is None:
            return {"anchor_name": "", "is_live": False}

        context = await browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )

        if cookies:
            cookie_list = _parse_cookie_str(cookies, url)
            if cookie_list:
                try:
                    await context.add_cookies(cookie_list)
                except Exception as e:
                    logger.debug(f"Failed to add cookies: {e}")

        page = await context.new_page()

        captured_streams: List[dict] = []
        stream_found = asyncio.Event()

        _STREAM_CONTENT_TYPES = {"video/", "application/x-mpegurl", "application/vnd.apple.mpegurl", "application/octet-stream"}
        _NON_STREAM_EXTENSIONS = {".css", ".js", ".woff", ".ttf", ".eot", ".otf", ".png", ".jpg", ".gif", ".svg", ".ico"}

        async def on_response(response):
            resp_url = response.url
            status = response.status
            content_type = ""
            try:
                headers = await response.all_headers()
                if isinstance(headers, dict):
                    content_type = headers.get("content-type", "")
                elif isinstance(headers, list):
                    for h in headers:
                        if isinstance(h, (list, tuple)) and len(h) == 2:
                            if h[0].lower() == "content-type":
                                content_type = h[1]
                                break
            except Exception:
                pass

            is_stream_ct = any(ct in content_type.lower() for ct in _STREAM_CONTENT_TYPES) if content_type else False
            url_ext = resp_url.split("?")[0].rsplit(".", 1)[-1].lower() if "." in resp_url.split("?")[0] else ""
            is_non_stream_ext = f".{url_ext}" in _NON_STREAM_EXTENSIONS

            if is_non_stream_ext and not is_stream_ct:
                return

            patterns = config.get("url_patterns", [".m3u8", ".flv"])
            for pattern in patterns:
                if pattern in resp_url:
                    is_actual_stream = (
                        ".m3u8" in resp_url
                        or ".flv" in resp_url
                        or is_stream_ct
                        or status == 200
                    )
                    if is_actual_stream or pattern in (".m3u8", ".flv"):
                        captured_streams.append({
                            "url": resp_url,
                            "status": status,
                            "content_type": content_type,
                        })
                        if ".m3u8" in resp_url or ".flv" in resp_url:
                            if status == 200 or not stream_found.is_set():
                                stream_found.set()
                    break

        page.on("response", on_response)

        anchor_name = ""
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            wait_time = config.get("wait_time", 8000)
            try:
                await asyncio.wait_for(stream_found.wait(), timeout=wait_time / 1000)
            except asyncio.TimeoutError:
                pass

            anchor_name = await self._extract_anchor_name(page, config)
        except Exception as e:
            logger.debug(f"Browser page load error: {e}")
        finally:
            await context.close()

        result = {
            "anchor_name": anchor_name,
            "is_live": False,
        }

        if captured_streams:
            m3u8_urls = []
            flv_urls = []
            for stream in captured_streams:
                s_url = stream["url"]
                s_status = stream.get("status", 0)
                if ".m3u8" in s_url:
                    m3u8_urls.append((s_url, s_status))
                if ".flv" in s_url:
                    flv_urls.append((s_url, s_status))

            m3u8_urls.sort(key=lambda x: 0 if x[1] == 200 else 1)
            flv_urls.sort(key=lambda x: 0 if x[1] == 200 else 1)

            m3u8_url = m3u8_urls[0][0] if m3u8_urls else None
            flv_url = flv_urls[0][0] if flv_urls else None

            if m3u8_url or flv_url:
                result = {
                    "anchor_name": anchor_name,
                    "is_live": True,
                    "m3u8_url": m3u8_url,
                    "flv_url": flv_url,
                    "record_url": m3u8_url or flv_url,
                }

        return result

    @trace_error_decorator
    async def start_screencast(
        self,
        url: str,
        output_path: str,
        proxy_addr: OptionalStr = None,
        cookies: OptionalStr = None,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ) -> Callable:
        """Screencast mode: directly record browser-rendered video to file
        
        Also captures stream URL via network interception for audio extraction.
        After recording, merges video (from screencast) and audio (from stream URL)
        into the final output file using FFmpeg.
        
        Returns a stop function and a live-ended check function.
        Uses a background thread with a persistent event loop so the
        recording continues after the caller's event loop is closed.
        """
        browser = await self._get_browser(proxy_addr, headless=True)
        if browser is None:
            raise RuntimeError("Failed to launch browser")

        context = await browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            viewport={"width": width, "height": height},
            ignore_https_errors=True,
            record_video_dir=os.path.dirname(output_path) or ".",
            record_video_size={"width": width, "height": height},
        )

        if cookies:
            cookie_list = _parse_cookie_str(cookies, url)
            if cookie_list:
                try:
                    await context.add_cookies(cookie_list)
                except Exception as e:
                    logger.debug(f"Failed to add cookies: {e}")

        page = await context.new_page()

        captured_stream_urls: List[str] = []
        _STREAM_CONTENT_TYPES = {"video/", "application/x-mpegurl", "application/vnd.apple.mpegurl", "application/octet-stream"}
        _NON_STREAM_EXTENSIONS = {".css", ".js", ".woff", ".ttf", ".eot", ".otf", ".png", ".jpg", ".gif", ".svg", ".ico"}

        async def on_screencast_response(response):
            resp_url = response.url
            status = response.status
            if ".m3u8" in resp_url or ".flv" in resp_url:
                captured_stream_urls.append(resp_url)
                return
            content_type = ""
            try:
                headers = await response.all_headers()
                if isinstance(headers, dict):
                    content_type = headers.get("content-type", "")
                elif isinstance(headers, list):
                    for h in headers:
                        if isinstance(h, (list, tuple)) and len(h) == 2:
                            if h[0].lower() == "content-type":
                                content_type = h[1]
                                break
            except Exception:
                pass
            if content_type and any(ct in content_type.lower() for ct in _STREAM_CONTENT_TYPES):
                url_ext = resp_url.split("?")[0].rsplit(".", 1)[-1].lower() if "." in resp_url.split("?")[0] else ""
                if f".{url_ext}" not in _NON_STREAM_EXTENSIONS:
                    captured_stream_urls.append(resp_url)

        page.on("response", on_screencast_response)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
        except Exception as e:
            logger.error(f"Failed to load page: {e}")
            await context.close()
            raise

        stop_flag = threading.Event()
        finished_event = threading.Event()
        live_ended = threading.Event()
        audio_process = [None]
        audio_output_path = [None]

        base, ext = os.path.splitext(output_path)
        audio_output_path[0] = f"{base}_audio.aac"

        _LIVE_END_INDICATORS = [
            "直播已结束",
            "直播结束",
            "已离线",
            "未开播",
            "主播已离开",
            "live has ended",
            "offline",
            "not live",
        ]

        def _start_audio_recording(stream_url: str):
            import subprocess
            try:
                ffmpeg_path = "ffmpeg"
                try:
                    subprocess.run([ffmpeg_path, "-version"], capture_output=True, timeout=5)
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    logger.debug("FFmpeg not found, cannot record audio")
                    return

                cmd = [
                    ffmpeg_path, "-y",
                    "-headers", f"User-Agent: {DEFAULT_USER_AGENT}",
                    "-headers", "Referer: https://live.douyin.com/",
                    "-i", stream_url,
                    "-vn",
                    "-c:a", "aac",
                    "-f", "adts",
                    audio_output_path[0],
                ]
                logger.info(f"Starting audio recording from stream URL...")
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                audio_process[0] = proc
            except Exception as e:
                logger.debug(f"Failed to start audio recording: {e}")

        def _stop_audio_recording():
            proc = audio_process[0]
            if proc and proc.poll() is None:
                try:
                    proc.stdin.write(b'q')
                    proc.stdin.flush()
                except Exception:
                    pass
                try:
                    proc.wait(timeout=10)
                except Exception:
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                audio_process[0] = None

        def _bg_record():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _record():
                audio_started = False
                try:
                    check_count = 0
                    while not stop_flag.is_set():
                        await asyncio.sleep(1)
                        check_count += 1
                        if not audio_started and captured_stream_urls and check_count >= 3:
                            audio_url = None
                            for u in captured_stream_urls:
                                if ".flv" in u:
                                    audio_url = u
                                    break
                            if not audio_url:
                                for u in captured_stream_urls:
                                    if ".m3u8" in u:
                                        audio_url = u
                                        break
                            if not audio_url and captured_stream_urls:
                                audio_url = captured_stream_urls[-1]
                            if audio_url:
                                _start_audio_recording(audio_url)
                                audio_started = True
                        if check_count % 30 == 0 and not stop_flag.is_set():
                            try:
                                page_title = await page.title()
                                page_url = page.url
                                body_text = ""
                                try:
                                    body_text = await page.locator("body").inner_text(timeout=5000)
                                except Exception:
                                    pass
                                combined = f"{page_title} {body_text}"
                                is_ended = any(ind in combined for ind in _LIVE_END_INDICATORS)
                                if is_ended:
                                    logger.info(f"Live stream ended detected, stopping screencast: {page_title}")
                                    live_ended.set()
                                    stop_flag.set()
                                    break
                            except Exception:
                                pass
                    logger.info("Screencast recording stopped")
                except asyncio.CancelledError:
                    logger.info("Screencast recording cancelled")
                finally:
                    _stop_audio_recording()
                    video_path = None
                    try:
                        if page.video:
                            video_path = await page.video.path()
                            logger.info(f"Screencast video path: {video_path}")
                    except Exception as e:
                        logger.warning(f"Failed to get video path before close: {e}")
                    logger.info("Screencast closing context...")
                    try:
                        await asyncio.wait_for(context.close(), timeout=15)
                        logger.info("Screencast context closed")
                    except asyncio.TimeoutError:
                        logger.warning("Screencast context close timed out, forcing close")
                        try:
                            await context.close()
                        except Exception:
                            pass
                    except Exception:
                        pass
                    await asyncio.sleep(1)
                    logger.info(f"Screencast video_path={video_path}, exists={os.path.exists(video_path) if video_path else 'N/A'}")
                    if not video_path or not os.path.exists(video_path):
                        video_dir = os.path.dirname(output_path) or "."
                        logger.info(f"Screencast searching for video in: {video_dir}")
                        try:
                            for f in os.listdir(video_dir):
                                if f.startswith("page@") and f.endswith(".webm"):
                                    candidate = os.path.join(video_dir, f)
                                    if os.path.getmtime(candidate) > time.time() - 300:
                                        video_path = candidate
                                        logger.info(f"Screencast found video candidate: {candidate}")
                                        break
                        except Exception as e2:
                            logger.warning(f"Screencast video search error: {e2}")
                    if video_path and os.path.exists(video_path):
                        logger.info(f"Screencast renaming {video_path} -> {output_path}")
                        if os.path.exists(output_path):
                            try:
                                os.remove(output_path)
                            except Exception:
                                pass
                        try:
                            os.rename(video_path, output_path)
                            logger.info(f"Screencast saved to: {output_path}")
                        except Exception as e:
                            try:
                                import shutil
                                shutil.copy2(video_path, output_path)
                                logger.info(f"Screencast copied to: {output_path}")
                            except Exception as e2:
                                logger.error(f"Failed to move/copy screencast file: {e2}")

                        if captured_stream_urls and audio_output_path[0] and os.path.exists(audio_output_path[0]):
                            audio_size = os.path.getsize(audio_output_path[0])
                            if audio_size > 1000:
                                self._merge_audio_video(
                                    video_path=output_path,
                                    audio_path=audio_output_path[0],
                                    output_path=output_path,
                                )
                            else:
                                logger.info(f"Audio file too small ({audio_size} bytes), keeping video-only version")
                                try:
                                    os.remove(audio_output_path[0])
                                except Exception:
                                    pass
                    else:
                        logger.warning(f"Screencast video file not found, expected at: {output_path}")
                    finished_event.set()

            try:
                loop.run_until_complete(_record())
            except Exception as e:
                logger.error(f"Screencast background error: {e}")
                finished_event.set()
            finally:
                loop.close()

        bg_thread = threading.Thread(target=_bg_record, daemon=True)
        bg_thread.start()

        def stop():
            stop_flag.set()
            finished_event.wait(timeout=30)
            logger.info("Browser screencast stopped and resources released")

        def is_live_ended():
            return live_ended.is_set()

        return stop, is_live_ended

    @staticmethod
    def _merge_audio_video(video_path: str, audio_path: str, output_path: str):
        """Merge screencast video with separately recorded audio using FFmpeg.
        
        Outputs MKV container which supports both VP8 video and AAC audio.
        """
        import subprocess
        try:
            ffmpeg_path = "ffmpeg"
            try:
                subprocess.run([ffmpeg_path, "-version"], capture_output=True, timeout=5)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.warning("FFmpeg not found, skipping audio merge")
                return

            base, _ = os.path.splitext(output_path)
            merged_path = f"{base}_with_audio.mkv"

            cmd = [
                ffmpeg_path, "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "copy",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                merged_path,
            ]

            logger.info(f"Merging screencast video with audio...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0 and os.path.exists(merged_path):
                merged_size = os.path.getsize(merged_path)
                if merged_size > 0:
                    try:
                        os.remove(video_path)
                    except Exception:
                        pass
                    try:
                        os.remove(audio_path)
                    except Exception:
                        pass
                    try:
                        os.rename(merged_path, output_path)
                    except Exception:
                        try:
                            os.rename(merged_path, f"{base}.mkv")
                            output_new = f"{base}.mkv"
                            logger.info(f"Screencast merged (MKV): {output_new} ({merged_size} bytes)")
                            return
                        except Exception:
                            pass
                        import shutil
                        shutil.copy2(merged_path, output_path)
                        try:
                            os.remove(merged_path)
                        except Exception:
                            pass
                    logger.info(f"Screencast merged with audio: {output_path} ({merged_size} bytes)")
                else:
                    try:
                        os.remove(merged_path)
                    except Exception:
                        pass
                    logger.warning("Merged file is empty, keeping video-only version")
            else:
                logger.debug(f"FFmpeg merge failed: {result.stderr[-300:] if result.stderr else 'unknown'}")
                try:
                    if os.path.exists(merged_path):
                        os.remove(merged_path)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Audio merge error: {e}")

    async def _extract_anchor_name(self, page, config: dict) -> str:
        selectors = config.get("anchor_selectors", [])
        for selector in selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=2000):
                    text = await element.inner_text()
                    if text and text.strip():
                        return text.strip()
            except Exception:
                continue

        try:
            title = await page.title()
            if title:
                parts = title.split("-")
                if parts:
                    return parts[0].strip()
        except Exception:
            pass

        return ""


_browser_recorder: Optional[BrowserRecorder] = None


async def get_browser_recorder() -> BrowserRecorder:
    global _browser_recorder
    if _browser_recorder is None:
        _browser_recorder = BrowserRecorder()
    return _browser_recorder


async def browser_extract_stream(
    url: str,
    platform: str = "",
    proxy_addr: OptionalStr = None,
    cookies: OptionalStr = None,
    timeout: int = 30,
) -> dict:
    recorder = await get_browser_recorder()
    return await recorder.extract_stream(url, platform, proxy_addr, cookies, timeout)


async def browser_record(
    url: str,
    mode: str = BROWSER_MODE_FALLBACK,
    platform: str = "",
    proxy_addr: OptionalStr = None,
    cookies: OptionalStr = None,
    timeout: int = 30,
    output_path: OptionalStr = None,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
) -> dict:
    """Unified entry point that dispatches to fallback or screencast mode
    
    For fallback mode: returns stream info dict with record_url
    For screencast mode: starts browser recording, returns dict with stop_callback
    """
    if mode == BROWSER_MODE_SCREENCAST and output_path:
        recorder = await get_browser_recorder()
        stop_fn, is_live_ended_fn = await recorder.start_screencast(
            url=url,
            output_path=output_path,
            proxy_addr=proxy_addr,
            cookies=cookies,
            width=width,
            height=height,
            fps=fps,
        )
        return {
            "anchor_name": "",
            "is_live": True,
            "mode": BROWSER_MODE_SCREENCAST,
            "stop_callback": stop_fn,
            "is_live_ended_callback": is_live_ended_fn,
        }
    else:
        result = await browser_extract_stream(url, platform, proxy_addr, cookies, timeout)
        result["mode"] = BROWSER_MODE_FALLBACK
        return result


async def close_browser():
    global _browser_recorder
    if _browser_recorder:
        await _browser_recorder.close()
        _browser_recorder = None
