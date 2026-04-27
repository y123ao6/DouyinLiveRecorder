# -*- encoding: utf-8 -*-
from .base_adapter import PlatformAdapter
from .adapter_factory import AdapterFactory
from .domestic import (
    DouyinAdapter, KuaishouAdapter, HuyaAdapter, DouyuAdapter, YYAdapter,
    BilibiliAdapter, XHSAdapter, BigoAdapter, BluedAdapter, NeteaseAdapter,
    QiandureboAdapter, MaoerfmAdapter, LookAdapter, TwitCastingAdapter,
    BaiduAdapter, WeiboAdapter, KugouAdapter, HuajiaoAdapter, LiuxingAdapter,
    AcfunAdapter, ChangliaoAdapter, YinboAdapter, InkeAdapter, ZhihuAdapter,
    HaixiuAdapter, VvxqiuAdapter, YiqiliveAdapter, LangliveAdapter,
    PpliveAdapter, SixRoomAdapter, LehaitvAdapter, HuamaoAdapter,
    TaobaoAdapter, JDAdapter, MiguAdapter, LianjieAdapter, LaixiuAdapter,
    CustomStreamAdapter,
)
from .overseas import (
    TikTokAdapter, SOOPAdapter, PandaTVAdapter, WinkTVAdapter,
    FlexTVAdapter, PopkonTVAdapter, TwitchAdapter, LiveMeAdapter,
    ShowRoomAdapter, CHZZKAdapter, ShopeeAdapter, YoutubeAdapter,
    FaceitAdapter, PicartoAdapter,
)

__all__ = [
    'PlatformAdapter', 'AdapterFactory',
    'DouyinAdapter', 'KuaishouAdapter', 'HuyaAdapter', 'DouyuAdapter',
    'YYAdapter', 'BilibiliAdapter', 'XHSAdapter', 'BigoAdapter',
    'BluedAdapter', 'NeteaseAdapter', 'QiandureboAdapter', 'MaoerfmAdapter',
    'LookAdapter', 'TwitCastingAdapter', 'BaiduAdapter', 'WeiboAdapter',
    'KugouAdapter', 'HuajiaoAdapter', 'LiuxingAdapter', 'AcfunAdapter',
    'ChangliaoAdapter', 'YinboAdapter', 'InkeAdapter', 'ZhihuAdapter',
    'HaixiuAdapter', 'VvxqiuAdapter', 'YiqiliveAdapter', 'LangliveAdapter',
    'PpliveAdapter', 'SixRoomAdapter', 'LehaitvAdapter', 'HuamaoAdapter',
    'TaobaoAdapter', 'JDAdapter', 'MiguAdapter', 'LianjieAdapter',
    'LaixiuAdapter', 'CustomStreamAdapter',
    'TikTokAdapter', 'SOOPAdapter', 'PandaTVAdapter', 'WinkTVAdapter',
    'FlexTVAdapter', 'PopkonTVAdapter', 'TwitchAdapter', 'LiveMeAdapter',
    'ShowRoomAdapter', 'CHZZKAdapter', 'ShopeeAdapter', 'YoutubeAdapter',
    'FaceitAdapter', 'PicartoAdapter',
]
