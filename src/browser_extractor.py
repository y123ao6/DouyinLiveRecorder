# -*- encoding: utf-8 -*-

"""
Author: DouyinLiveRecorder Contributors
Function: Browser-based live stream recorder with two modes:
  - FALLBACK: Capture stream URL via network interception (default)
  - SCREENCAST: Directly record browser-rendered video via screen capture
"""

import asyncio
import os
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
        "url_patterns": [".m3u8", ".flv", "douyincdn.com", "bytecdn.cn", "bytedance.com"],
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

        async def on_response(response):
            if stream_found.is_set():
                return
            resp_url = response.url
            patterns = config.get("url_patterns", [".m3u8", ".flv"])
            for pattern in patterns:
                if pattern in resp_url:
                    captured_streams.append({"url": resp_url})
                    if ".m3u8" in resp_url or ".flv" in resp_url:
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
            m3u8_url = None
            flv_url = None
            for stream in captured_streams:
                s_url = stream["url"]
                if ".m3u8" in s_url and not m3u8_url:
                    m3u8_url = s_url
                if ".flv" in s_url and not flv_url:
                    flv_url = s_url

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
        
        Returns a stop function to call when recording should end.
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

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
        except Exception as e:
            logger.error(f"Failed to load page: {e}")
            await context.close()
            raise

        stop_flag = threading.Event()
        finished_event = threading.Event()

        def _bg_record():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _record():
                try:
                    while not stop_flag.is_set():
                        await asyncio.sleep(0.5)
                    logger.info("Screencast recording stopped")
                except asyncio.CancelledError:
                    logger.info("Screencast recording cancelled")
                finally:
                    try:
                        video_path = await page.video.path() if page.video else None
                    except Exception:
                        video_path = None
                    try:
                        await context.close()
                    except Exception:
                        pass
                    if video_path and os.path.exists(video_path):
                        if os.path.exists(output_path):
                            try:
                                os.remove(output_path)
                            except Exception:
                                pass
                        try:
                            os.rename(video_path, output_path)
                            logger.info(f"Screencast saved to: {output_path}")
                        except Exception as e:
                            logger.error(f"Failed to move screencast file: {e}")
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

        return stop

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
        stop_fn = await recorder.start_screencast(
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
