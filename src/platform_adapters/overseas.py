# -*- encoding: utf-8 -*-
import asyncio
from typing import Dict, Optional

from .base_adapter import PlatformAdapter
from src import spider, stream
from src.utils import logger, update_config


class TikTokAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "TikTok直播"

    def supports_url(self, url: str) -> bool:
        return "www.tiktok.com/" in url

    def needs_proxy(self) -> bool:
        return True

    def is_flv_preferred(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        global_proxy = kwargs.get('global_proxy', False)
        if not global_proxy and not proxy:
            logger.error("错误信息: 网络异常，请检查网络是否能正常访问TikTok平台")
            return {}
        json_data = asyncio.run(spider.get_tiktok_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(
            stream.get_tiktok_stream_url(json_data, quality, proxy))
        return port_info


class SOOPAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "SOOP"

    def supports_url(self, url: str) -> bool:
        return "sooplive.co.kr/" in url or "sooplive.com/" in url

    def needs_proxy(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        global_proxy = kwargs.get('global_proxy', False)
        if not global_proxy and not proxy:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问SOOP平台")
            return {}

        account_config = kwargs.get('account_config')
        username = account_config.sooplive_username if account_config else ''
        password = account_config.sooplive_password if account_config else ''

        json_data = asyncio.run(spider.get_sooplive_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies,
            username=username, password=password
        ))
        if json_data and json_data.get('new_cookies'):
            config_file = kwargs.get('config_file', '')
            if config_file:
                update_config(config_file, 'Cookie', 'sooplive_cookie', json_data['new_cookies'])

        port_info = asyncio.run(stream.get_stream_url(json_data, quality, spec=True))
        return port_info


class PandaTVAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "PandaTV"

    def supports_url(self, url: str) -> bool:
        return "www.pandalive.co.kr/" in url

    def needs_proxy(self) -> bool:
        return True

    def get_record_headers(self, url: str) -> Optional[str]:
        return 'origin:https://www.pandalive.co.kr'

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        global_proxy = kwargs.get('global_proxy', False)
        if not global_proxy and not proxy:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问PandaTV直播平台")
            return {}

        json_data = asyncio.run(spider.get_pandatv_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_stream_url(json_data, quality, spec=True))
        return port_info


class WinkTVAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "WinkTV"

    def supports_url(self, url: str) -> bool:
        return "www.winktv.co.kr/" in url

    def needs_proxy(self) -> bool:
        return True

    def get_record_headers(self, url: str) -> Optional[str]:
        return 'origin:https://www.winktv.co.kr'

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        global_proxy = kwargs.get('global_proxy', False)
        if not global_proxy and not proxy:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问WinkTV直播平台")
            return {}

        json_data = asyncio.run(spider.get_winktv_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_stream_url(json_data, quality, spec=True))
        return port_info


class FlexTVAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "FlexTV"

    def supports_url(self, url: str) -> bool:
        return "www.flextv.co.kr/" in url or "www.ttinglive.com/" in url

    def needs_proxy(self) -> bool:
        return True

    def get_record_headers(self, url: str) -> Optional[str]:
        return 'origin:https://www.flextv.co.kr'

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        global_proxy = kwargs.get('global_proxy', False)
        if not global_proxy and not proxy:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问FlexTV直播平台")
            return {}

        account_config = kwargs.get('account_config')
        username = account_config.flextv_username if account_config else ''
        password = account_config.flextv_password if account_config else ''

        json_data = asyncio.run(spider.get_flextv_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies,
            username=username, password=password
        ))
        if json_data and json_data.get('new_cookies'):
            config_file = kwargs.get('config_file', '')
            if config_file:
                update_config(config_file, 'Cookie', 'flextv_cookie', json_data['new_cookies'])

        if 'play_url_list' in json_data:
            port_info = asyncio.run(stream.get_stream_url(json_data, quality, spec=True))
        else:
            port_info = json_data
        return port_info


class PopkonTVAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "PopkonTV"

    def supports_url(self, url: str) -> bool:
        return "www.popkontv.com/" in url

    def needs_proxy(self) -> bool:
        return True

    def get_record_headers(self, url: str) -> Optional[str]:
        return 'origin:https://www.popkontv.com'

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        global_proxy = kwargs.get('global_proxy', False)
        if not global_proxy and not proxy:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问PopkonTV直播平台")
            return {}

        account_config = kwargs.get('account_config')
        access_token = account_config.popkontv_access_token if account_config else ''
        username = account_config.popkontv_username if account_config else ''
        password = account_config.popkontv_password if account_config else ''
        partner_code = account_config.popkontv_partner_code if account_config else 'P-00001'

        port_info = asyncio.run(spider.get_popkontv_stream_url(
            url=url, proxy_addr=proxy, access_token=access_token,
            username=username, password=password, partner_code=partner_code
        ))
        if port_info and port_info.get('new_token'):
            config_file = kwargs.get('config_file', '')
            if config_file:
                update_config(config_file, 'Authorization', 'popkontv_token', port_info['new_token'])

        return port_info


class TwitchAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "TwitchTV"

    def supports_url(self, url: str) -> bool:
        return "www.twitch.tv/" in url

    def needs_proxy(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        global_proxy = kwargs.get('global_proxy', False)
        if not global_proxy and not proxy:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问TwitchTV直播平台")
            return {}

        json_data = asyncio.run(spider.get_twitchtv_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_stream_url(json_data, quality, spec=True))
        return port_info


class LiveMeAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "LiveMe"

    def supports_url(self, url: str) -> bool:
        return "www.liveme.com/" in url

    def needs_proxy(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        global_proxy = kwargs.get('global_proxy', False)
        if not global_proxy and not proxy:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问LiveMe直播平台")
            return {}

        port_info = asyncio.run(spider.get_liveme_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class ShowRoomAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "ShowRoom"

    def supports_url(self, url: str) -> bool:
        return "showroom-live.com/" in url

    def needs_proxy(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_showroom_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_stream_url(json_data, quality, spec=True))
        return port_info


class CHZZKAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "CHZZK"

    def supports_url(self, url: str) -> bool:
        return "chzzk.naver.com/" in url

    def needs_proxy(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_chzzk_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_stream_url(json_data, quality, spec=True))
        return port_info


class ShopeeAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "shopee"

    def supports_url(self, url: str) -> bool:
        return "live.shopee" in url or "shp.ee/" in url

    def needs_proxy(self) -> bool:
        return True

    def is_only_flv(self) -> bool:
        return True

    def use_http_recording(self) -> bool:
        return True

    def get_record_headers(self, url: str) -> Optional[str]:
        live_domain = '/'.join(url.split('/')[0:3])
        return f'origin:{live_domain}'

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_shopee_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class YoutubeAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "Youtube"

    def supports_url(self, url: str) -> bool:
        return "www.youtube.com/" in url or "youtu.be/" in url

    def needs_proxy(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_youtube_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_stream_url(json_data, quality, spec=True))
        return port_info


class FaceitAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "faceit"

    def supports_url(self, url: str) -> bool:
        return "faceit.com/" in url

    def needs_proxy(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        global_proxy = kwargs.get('global_proxy', False)
        if not global_proxy and not proxy:
            logger.error("错误信息: 网络异常，请检查本网络是否能正常访问faceit直播平台")
            return {}

        json_data = asyncio.run(spider.get_faceit_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_stream_url(json_data, quality, spec=True))
        return port_info


class PicartoAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "Picarto"

    def supports_url(self, url: str) -> bool:
        return "www.picarto.tv" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_picarto_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info
