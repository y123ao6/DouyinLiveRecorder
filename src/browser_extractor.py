# -*- encoding: utf-8 -*-

"""
Author: DouyinLiveRecorder Contributors
Function: Browser-based live stream URL extractor using Playwright.
"""

import asyncio
from typing import Optional, Dict, List
from .logger import logger
from .utils import trace_error_decorator

OptionalStr = str | None
OptionalDict = Dict | None

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
    "--disable-gpu",
    "--mute-audio",
    "--autoplay-policy=no-user-gesture-required",
    "--disable-extensions",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--no-first-run",
    "--no-default-browser-check",
]


def _get_platform_key(url: str) -> str:
    platform_map = {
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
    for domain, key in platform_map.items():
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


class BrowserStreamExtractor:
    _playwright = None
    _browser = None
    _lock = None

    def __init__(self):
        pass

    @classmethod
    def _get_lock(cls):
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    @classmethod
    async def _get_browser(cls, proxy_addr: OptionalStr = None):
        async with cls._get_lock():
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
            try:
                cls._browser = await cls._playwright.chromium.launch(
                    headless=True,
                    args=LAUNCH_ARGS,
                    proxy=proxy_config,
                )
            except Exception as e:
                logger.error(f"Failed to launch browser: {e}")
                return None
            return cls._browser

    @classmethod
    async def close(cls):
        async with cls._get_lock():
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
    async def extract(
        self,
        url: str,
        platform: str = "",
        proxy_addr: OptionalStr = None,
        cookies: OptionalStr = None,
        timeout: int = 30,
    ) -> dict:
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

        async def on_response(response):
            resp_url = response.url
            patterns = config.get("url_patterns", [".m3u8", ".flv"])
            for pattern in patterns:
                if pattern in resp_url:
                    try:
                        raw_headers = await response.all_headers()
                        headers = {}
                        if isinstance(raw_headers, dict):
                            headers = raw_headers
                        elif isinstance(raw_headers, (list, tuple)):
                            for item in raw_headers:
                                if isinstance(item, (list, tuple)) and len(item) == 2:
                                    headers[item[0]] = item[1]
                        captured_streams.append({
                            "url": resp_url,
                            "headers": headers,
                            "content_type": headers.get("content-type", ""),
                        })
                    except Exception:
                        captured_streams.append({"url": resp_url, "headers": {}})
                    break

        page.on("response", on_response)

        anchor_name = ""
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            wait_time = config.get("wait_time", 8000)
            await page.wait_for_timeout(wait_time)

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


_browser_extractor: Optional[BrowserStreamExtractor] = None


async def get_browser_extractor() -> BrowserStreamExtractor:
    global _browser_extractor
    if _browser_extractor is None:
        _browser_extractor = BrowserStreamExtractor()
    return _browser_extractor


async def browser_extract_stream(
    url: str,
    platform: str = "",
    proxy_addr: OptionalStr = None,
    cookies: OptionalStr = None,
    timeout: int = 30,
) -> dict:
    extractor = await get_browser_extractor()
    return await extractor.extract(url, platform, proxy_addr, cookies, timeout)


async def close_browser():
    global _browser_extractor
    if _browser_extractor:
        await _browser_extractor.close()
        _browser_extractor = None
