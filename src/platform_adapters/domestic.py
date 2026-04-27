# -*- encoding: utf-8 -*-
import asyncio
import uuid
from typing import Dict, Optional

from .base_adapter import PlatformAdapter
from src import spider, stream
from src.config_manager import CookieConfig, AccountConfig
from src.utils import logger


class DouyinAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "抖音直播"

    def supports_url(self, url: str) -> bool:
        return "douyin.com/" in url

    def is_flv_preferred(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        if 'v.douyin.com' not in url and '/user/' not in url:
            json_data = asyncio.run(spider.get_douyin_web_stream_data(
                url=url, proxy_addr=proxy, cookies=cookies))
        else:
            json_data = asyncio.run(spider.get_douyin_app_stream_data(
                url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(
            stream.get_douyin_stream_url(json_data, quality, proxy))
        return port_info


class KuaishouAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "快手直播"

    def supports_url(self, url: str) -> bool:
        return "live.kuaishou.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_kuaishou_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_kuaishou_stream_url(json_data, quality))
        return port_info


class HuyaAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "虎牙直播"

    def supports_url(self, url: str) -> bool:
        return "www.huya.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        if quality not in ['OD', 'BD', 'UHD']:
            json_data = asyncio.run(spider.get_huya_stream_data(
                url=url, proxy_addr=proxy, cookies=cookies))
            port_info = asyncio.run(stream.get_huya_stream_url(json_data, quality))
        else:
            port_info = asyncio.run(spider.get_huya_app_stream_url(
                url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class DouyuAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "斗鱼直播"

    def supports_url(self, url: str) -> bool:
        return "www.douyu.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_douyu_info_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_douyu_stream_url(
            json_data, video_quality=quality, cookies=cookies, proxy_addr=proxy))
        return port_info


class YYAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "YY直播"

    def supports_url(self, url: str) -> bool:
        return "www.yy.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_yy_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_yy_stream_url(json_data))
        return port_info


class BilibiliAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "B站直播"

    def supports_url(self, url: str) -> bool:
        return "live.bilibili.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_bilibili_room_info(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_bilibili_stream_url(
            json_data, video_quality=quality, cookies=cookies, proxy_addr=proxy))
        return port_info


class XHSAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "小红书直播"

    def supports_url(self, url: str) -> bool:
        return "xhslink.com/" in url or "www.xiaohongshu.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_xhs_stream_url(
            url, proxy_addr=proxy, cookies=cookies))
        return port_info


class BigoAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "Bigo直播"

    def supports_url(self, url: str) -> bool:
        return "www.bigo.tv/" in url or "slink.bigovideo.tv/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_bigo_stream_url(
            url, proxy_addr=proxy, cookies=cookies))
        return port_info


class BluedAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "Blued直播"

    def supports_url(self, url: str) -> bool:
        return "app.blued.cn/" in url

    def get_record_headers(self, url: str) -> Optional[str]:
        return 'referer:https://app.blued.cn'

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_blued_stream_url(
            url, proxy_addr=proxy, cookies=cookies))
        return port_info


class NeteaseAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "网易CC直播"

    def supports_url(self, url: str) -> bool:
        return "cc.163.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_netease_stream_data(
            url=url, cookies=cookies))
        port_info = asyncio.run(stream.get_netease_stream_url(json_data, quality))
        return port_info


class QiandureboAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "千度热播"

    def supports_url(self, url: str) -> bool:
        return "qiandurebo.com/" in url

    def get_record_headers(self, url: str) -> Optional[str]:
        return 'referer:https://qiandurebo.com'

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_qiandurebo_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class MaoerfmAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "猫耳FM直播"

    def supports_url(self, url: str) -> bool:
        return "fm.missevan.com/" in url

    def is_only_audio(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_maoerfm_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class LookAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "Look直播"

    def supports_url(self, url: str) -> bool:
        return "look.163.com/" in url

    def is_only_audio(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_looklive_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class TwitCastingAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "TwitCasting"

    def supports_url(self, url: str) -> bool:
        return "twitcasting.tv/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        account_config: Optional[AccountConfig] = kwargs.get('account_config')
        account_type = account_config.twitcasting_account_type if account_config else 'normal'
        username = account_config.twitcasting_username if account_config else ''
        password = account_config.twitcasting_password if account_config else ''

        json_data = asyncio.run(spider.get_twitcasting_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies,
            account_type=account_type, username=username, password=password
        ))
        port_info = asyncio.run(stream.get_stream_url(json_data, quality, spec=False))

        if port_info and port_info.get('new_cookies'):
            from src.utils import update_config
            from src.state_manager import state_manager
            config_file = kwargs.get('config_file', '')
            if config_file:
                update_config(config_file, 'Cookie', 'twitcasting_cookie', port_info['new_cookies'])

        return port_info


class BaiduAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "百度直播"

    def supports_url(self, url: str) -> bool:
        return "live.baidu.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_baidu_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_stream_url(json_data, quality))
        return port_info


class WeiboAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "微博直播"

    def supports_url(self, url: str) -> bool:
        return "weibo.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_weibo_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_stream_url(
            json_data, quality, hls_extra_key='m3u8_url'))
        return port_info


class KugouAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "酷狗直播"

    def supports_url(self, url: str) -> bool:
        return "kugou.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_kugou_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class HuajiaoAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "花椒直播"

    def supports_url(self, url: str) -> bool:
        return "www.huajiao.com/" in url

    def is_only_flv(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_huajiao_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class LiuxingAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "流星直播"

    def supports_url(self, url: str) -> bool:
        return "7u66.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_liuxing_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class AcfunAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "Acfun"

    def supports_url(self, url: str) -> bool:
        return "live.acfun.cn/" in url or "m.acfun.cn/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_acfun_stream_data(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_stream_url(
            json_data, quality, url_type='flv', flv_extra_key='url'))
        return port_info


class ChangliaoAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "畅聊直播"

    def supports_url(self, url: str) -> bool:
        return "live.tlclw.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_changliao_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class YinboAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "音播直播"

    def supports_url(self, url: str) -> bool:
        return "ybw1666.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_yinbo_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class InkeAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "映客直播"

    def supports_url(self, url: str) -> bool:
        return "www.inke.cn/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_yingke_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class ZhihuAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "知乎直播"

    def supports_url(self, url: str) -> bool:
        return "www.zhihu.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_zhihu_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class HaixiuAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "嗨秀直播"

    def supports_url(self, url: str) -> bool:
        return "www.haixiutv.com/" in url

    def get_record_headers(self, url: str) -> Optional[str]:
        return 'referer:https://www.haixiutv.com'

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_haixiu_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class VvxqiuAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "VV星球"

    def supports_url(self, url: str) -> bool:
        return "vvxqiu.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_vvxqiu_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class YiqiliveAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "17Live"

    def supports_url(self, url: str) -> bool:
        return "17.live/" in url

    def get_record_headers(self, url: str) -> Optional[str]:
        return 'referer:https://17.live/en/live/6302408'

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_17live_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class LangliveAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "浪Live"

    def supports_url(self, url: str) -> bool:
        return "www.lang.live/" in url

    def get_record_headers(self, url: str) -> Optional[str]:
        return 'referer:https://www.lang.live'

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_langlive_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class PpliveAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "漂漂直播"

    def supports_url(self, url: str) -> bool:
        return "m.pp.weimipopo.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_pplive_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class SixRoomAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "六间房直播"

    def supports_url(self, url: str) -> bool:
        return ".6.cn/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_6room_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class LehaitvAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "乐嗨直播"

    def supports_url(self, url: str) -> bool:
        return "lehaitv.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_haixiu_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class HuamaoAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "花猫直播"

    def supports_url(self, url: str) -> bool:
        return "h.catshow168.com/" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_pplive_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class TaobaoAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "淘宝直播"

    def supports_url(self, url: str) -> bool:
        return "tb.cn" in url or "tbzb.taobao.com" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        json_data = asyncio.run(spider.get_taobao_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        port_info = asyncio.run(stream.get_stream_url(
            json_data, quality,
            url_type='all', hls_extra_key='hlsUrl', flv_extra_key='flvUrl'
        ))
        return port_info


class JDAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "京东直播"

    def supports_url(self, url: str) -> bool:
        return "3.cn" in url or "m.jd.com" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_jd_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class MiguAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "咪咕直播"

    def supports_url(self, url: str) -> bool:
        return "www.miguvideo.com" in url or "m.miguvideo.com" in url

    def use_http_recording(self) -> bool:
        return True

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_migu_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class LianjieAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "连接直播"

    def supports_url(self, url: str) -> bool:
        return "show.lailianjie.com" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_lianjie_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class LaixiuAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "来秀直播"

    def supports_url(self, url: str) -> bool:
        return "www.imkktv.com" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = asyncio.run(spider.get_laixiu_stream_url(
            url=url, proxy_addr=proxy, cookies=cookies))
        return port_info


class CustomStreamAdapter(PlatformAdapter):
    def get_platform_name(self) -> str:
        return "自定义录制直播"

    def supports_url(self, url: str) -> bool:
        return ".m3u8" in url or ".flv" in url

    def get_stream_info(
        self, url: str, quality: str, proxy: Optional[str] = None,
        cookies: str = '', **kwargs
    ) -> Dict:
        port_info = {
            "anchor_name": self.get_platform_name() + '_' + str(uuid.uuid4())[:8],
            "is_live": True,
            "record_url": url,
        }
        if '.flv' in url:
            port_info['flv_url'] = url
        else:
            port_info['m3u8_url'] = url
        return port_info
