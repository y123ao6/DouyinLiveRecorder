# -*- encoding: utf-8 -*-
import configparser
import os
import sys
from dataclasses import dataclass, field
from typing import Any, List, Optional

from .logger import logger

_BOOL_OPTIONS = {"是": True, "否": False}
_TEXT_ENCODING = 'utf-8-sig'


@dataclass
class RecordConfig:
    save_path: str = ""
    folder_by_author: bool = True
    folder_by_time: bool = False
    folder_by_title: bool = False
    filename_by_title: bool = False
    clean_emoji: bool = True
    video_save_type: str = "TS"
    video_record_quality: str = "原画"
    use_proxy: bool = False
    proxy_addr: Optional[str] = None
    proxy_addr_bak: str = ""
    max_request: int = 3
    delay_default: int = 120
    local_delay_default: int = 0
    loop_time: bool = False
    show_url: bool = False
    split_video_by_time: bool = False
    enable_https_recording: bool = False
    disk_space_limit: float = 1.0
    split_time: str = "1800"
    converts_to_mp4: bool = False
    converts_to_h264: bool = False
    delete_origin_file: bool = False
    create_time_file: bool = False
    is_run_script: bool = False
    custom_script: Optional[str] = None
    enable_proxy_platform: str = (
        'tiktok, soop, pandalive, winktv, flextv, popkontv, twitch,'
        ' liveme, showroom, chzzk, shopee, shp, youtu, faceit'
    )
    enable_proxy_platform_list: List[str] = field(default_factory=list)
    extra_enable_proxy: str = ""
    extra_enable_proxy_platform_list: List[str] = field(default_factory=list)
    language: str = "zh_cn"
    skip_proxy_check: bool = False


@dataclass
class PushConfig:
    live_status_push: str = ""
    dingtalk_api_url: str = ""
    xizhi_api_url: str = ""
    bark_msg_api: str = ""
    bark_msg_level: str = "active"
    bark_msg_ring: str = "bell"
    dingtalk_phone_num: str = ""
    dingtalk_is_atall: bool = False
    tg_token: str = ""
    tg_chat_id: str = ""
    email_host: str = ""
    open_smtp_ssl: bool = True
    smtp_port: str = ""
    login_email: str = ""
    email_password: str = ""
    sender_email: str = ""
    sender_name: str = ""
    to_email: str = ""
    ntfy_api: str = ""
    ntfy_tags: str = "tada"
    ntfy_email: str = ""
    pushplus_token: str = ""
    push_message_title: str = "直播间状态更新通知"
    begin_push_message_text: str = ""
    over_push_message_text: str = ""
    disable_record: bool = False
    push_check_seconds: int = 1800
    begin_show_push: bool = True
    over_show_push: bool = False


@dataclass
class CookieConfig:
    dy_cookie: str = ""
    ks_cookie: str = ""
    tiktok_cookie: str = ""
    hy_cookie: str = ""
    douyu_cookie: str = ""
    yy_cookie: str = ""
    bili_cookie: str = ""
    xhs_cookie: str = ""
    bigo_cookie: str = ""
    blued_cookie: str = ""
    sooplive_cookie: str = ""
    netease_cookie: str = ""
    qiandurebo_cookie: str = ""
    pandatv_cookie: str = ""
    maoerfm_cookie: str = ""
    winktv_cookie: str = ""
    flextv_cookie: str = ""
    look_cookie: str = ""
    twitcasting_cookie: str = ""
    baidu_cookie: str = ""
    weibo_cookie: str = ""
    kugou_cookie: str = ""
    twitch_cookie: str = ""
    liveme_cookie: str = ""
    huajiao_cookie: str = ""
    liuxing_cookie: str = ""
    showroom_cookie: str = ""
    acfun_cookie: str = ""
    changliao_cookie: str = ""
    yinbo_cookie: str = ""
    yingke_cookie: str = ""
    zhihu_cookie: str = ""
    chzzk_cookie: str = ""
    haixiu_cookie: str = ""
    vvxqiu_cookie: str = ""
    yiqilive_cookie: str = ""
    langlive_cookie: str = ""
    pplive_cookie: str = ""
    six_room_cookie: str = ""
    lehaitv_cookie: str = ""
    huamao_cookie: str = ""
    shopee_cookie: str = ""
    youtube_cookie: str = ""
    taobao_cookie: str = ""
    jd_cookie: str = ""
    faceit_cookie: str = ""
    migu_cookie: str = ""
    lianjie_cookie: str = ""
    laixiu_cookie: str = ""
    picarto_cookie: str = ""


@dataclass
class AccountConfig:
    sooplive_username: str = ""
    sooplive_password: str = ""
    flextv_username: str = ""
    flextv_password: str = ""
    popkontv_username: str = ""
    popkontv_partner_code: str = "P-00001"
    popkontv_password: str = ""
    twitcasting_account_type: str = "normal"
    twitcasting_username: str = ""
    twitcasting_password: str = ""
    popkontv_access_token: str = ""


@dataclass
class AppConfig:
    record: RecordConfig = field(default_factory=RecordConfig)
    push: PushConfig = field(default_factory=PushConfig)
    cookie: CookieConfig = field(default_factory=CookieConfig)
    account: AccountConfig = field(default_factory=AccountConfig)


class ConfigManager:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self._config = configparser.RawConfigParser()
        self._ensure_sections()

    def _ensure_sections(self) -> None:
        self._config.read(self.config_file, encoding=_TEXT_ENCODING)
        for section in ('录制设置', '推送配置', 'Cookie', 'Authorization', '账号密码'):
            if section not in self._config.sections():
                self._config.add_section(section)

    def _get_value(self, section: str, option: str, default: Any) -> str:
        try:
            self._config.read(self.config_file, encoding=_TEXT_ENCODING)
            return self._config.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self._config.set(section, option, str(default))
            with open(self.config_file, 'w', encoding=_TEXT_ENCODING) as f:
                self._config.write(f)
            return str(default)

    def _get_bool(self, section: str, option: str, default: bool) -> bool:
        value = self._get_value(section, option, "是" if default else "否")
        return _BOOL_OPTIONS.get(value, default)

    def _get_int(self, section: str, option: str, default: int) -> int:
        value = self._get_value(section, option, str(default))
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _get_float(self, section: str, option: str, default: float) -> float:
        value = self._get_value(section, option, str(default))
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def load(self) -> AppConfig:
        record = self._load_record_config()
        push = self._load_push_config()
        cookie = self._load_cookie_config()
        account = self._load_account_config()
        return AppConfig(record=record, push=push, cookie=cookie, account=account)

    def _load_record_config(self) -> RecordConfig:
        cfg = RecordConfig()
        cfg.language = self._get_value('录制设置', 'language(zh_cn/en)', "zh_cn")
        cfg.skip_proxy_check = self._get_bool('录制设置', '是否跳过代理检测(是/否)', False)
        cfg.save_path = self._get_value('录制设置', '直播保存路径(不填则默认)', "")
        cfg.folder_by_author = self._get_bool('录制设置', '保存文件夹是否以作者区分', True)
        cfg.folder_by_time = self._get_bool('录制设置', '保存文件夹是否以时间区分', False)
        cfg.folder_by_title = self._get_bool('录制设置', '保存文件夹是否以标题区分', False)
        cfg.filename_by_title = self._get_bool('录制设置', '保存文件名是否包含标题', False)
        cfg.clean_emoji = self._get_bool('录制设置', '是否去除名称中的表情符号', True)
        cfg.video_save_type = self._get_value('录制设置', '视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频', "ts")
        cfg.video_record_quality = self._get_value('录制设置', '原画|超清|高清|标清|流畅', "原画")
        cfg.use_proxy = self._get_bool('录制设置', '是否使用代理ip(是/否)', False)
        cfg.proxy_addr_bak = self._get_value('录制设置', '代理地址', "")
        cfg.proxy_addr = None if not cfg.use_proxy else cfg.proxy_addr_bak
        cfg.max_request = self._get_int('录制设置', '同一时间访问网络的线程数', 3)
        cfg.delay_default = self._get_int('录制设置', '循环时间(秒)', 120)
        cfg.local_delay_default = self._get_int('录制设置', '排队读取网址时间(秒)', 0)
        cfg.loop_time = self._get_bool('录制设置', '是否显示循环秒数', False)
        cfg.show_url = self._get_bool('录制设置', '是否显示直播源地址', False)
        cfg.split_video_by_time = self._get_bool('录制设置', '分段录制是否开启', False)
        cfg.enable_https_recording = self._get_bool('录制设置', '是否强制启用https录制', False)
        cfg.disk_space_limit = self._get_float('录制设置', '录制空间剩余阈值(gb)', 1.0)
        cfg.split_time = str(self._get_value('录制设置', '视频分段时间(秒)', "1800"))
        cfg.converts_to_mp4 = self._get_bool('录制设置', '录制完成后自动转为mp4格式', False)
        cfg.converts_to_h264 = self._get_bool('录制设置', 'mp4格式重新编码为h264', False)
        cfg.delete_origin_file = self._get_bool('录制设置', '追加格式后删除原文件', False)
        cfg.create_time_file = self._get_bool('录制设置', '生成时间字幕文件', False)
        cfg.is_run_script = self._get_bool('录制设置', '是否录制完成后执行自定义脚本', False)
        cfg.custom_script = self._get_value('录制设置', '自定义脚本执行命令', "") if cfg.is_run_script else None
        cfg.enable_proxy_platform = self._get_value(
            '录制设置', '使用代理录制的平台(逗号分隔)',
            'tiktok, soop, pandalive, winktv, flextv, popkontv, twitch, liveme, showroom, chzzk, shopee, shp, youtu, faceit'
        )
        cfg.enable_proxy_platform_list = (
            cfg.enable_proxy_platform.replace('，', ',').split(',')
            if cfg.enable_proxy_platform else []
        )
        cfg.extra_enable_proxy = self._get_value('录制设置', '额外使用代理录制的平台(逗号分隔)', '')
        cfg.extra_enable_proxy_platform_list = (
            cfg.extra_enable_proxy.replace('，', ',').split(',')
            if cfg.extra_enable_proxy else []
        )

        valid_types = ("FLV", "MKV", "TS", "MP4", "MP3音频", "M4A音频", "MP3", "M4A")
        if cfg.video_save_type and cfg.video_save_type.upper() in valid_types:
            cfg.video_save_type = cfg.video_save_type.upper()
        else:
            cfg.video_save_type = "TS"

        return cfg

    def _load_push_config(self) -> PushConfig:
        cfg = PushConfig()
        cfg.live_status_push = self._get_value('推送配置', '直播状态推送渠道', "")
        cfg.dingtalk_api_url = self._get_value('推送配置', '钉钉推送接口链接', "")
        cfg.xizhi_api_url = self._get_value('推送配置', '微信推送接口链接', "")
        cfg.bark_msg_api = self._get_value('推送配置', 'bark推送接口链接', "")
        cfg.bark_msg_level = self._get_value('推送配置', 'bark推送中断级别', "active")
        cfg.bark_msg_ring = self._get_value('推送配置', 'bark推送铃声', "bell")
        cfg.dingtalk_phone_num = self._get_value('推送配置', '钉钉通知@对象(填手机号)', "")
        cfg.dingtalk_is_atall = self._get_bool('推送配置', '钉钉通知@全体(是/否)', False)
        cfg.tg_token = self._get_value('推送配置', 'tgapi令牌', "")
        cfg.tg_chat_id = self._get_value('推送配置', 'tg聊天id(个人或者群组id)', "")
        cfg.email_host = self._get_value('推送配置', 'SMTP邮件服务器', "")
        cfg.open_smtp_ssl = self._get_bool('推送配置', '是否使用SMTP服务SSL加密(是/否)', True)
        cfg.smtp_port = self._get_value('推送配置', 'SMTP邮件服务器端口', "")
        cfg.login_email = self._get_value('推送配置', '邮箱登录账号', "")
        cfg.email_password = self._get_value('推送配置', '发件人密码(授权码)', "")
        cfg.sender_email = self._get_value('推送配置', '发件人邮箱', "")
        cfg.sender_name = self._get_value('推送配置', '发件人显示昵称', "")
        cfg.to_email = self._get_value('推送配置', '收件人邮箱', "")
        cfg.ntfy_api = self._get_value('推送配置', 'ntfy推送地址', "")
        cfg.ntfy_tags = self._get_value('推送配置', 'ntfy推送标签', "tada")
        cfg.ntfy_email = self._get_value('推送配置', 'ntfy推送邮箱', "")
        cfg.pushplus_token = self._get_value('推送配置', 'pushplus推送token', "")
        cfg.push_message_title = self._get_value('推送配置', '自定义推送标题', "直播间状态更新通知")
        cfg.begin_push_message_text = self._get_value('推送配置', '自定义开播推送内容', "")
        cfg.over_push_message_text = self._get_value('推送配置', '自定义关播推送内容', "")
        cfg.disable_record = self._get_bool('推送配置', '只推送通知不录制(是/否)', False)
        cfg.push_check_seconds = self._get_int('推送配置', '直播推送检测频率(秒)', 1800)
        cfg.begin_show_push = self._get_bool('推送配置', '开播推送开启(是/否)', True)
        cfg.over_show_push = self._get_bool('推送配置', '关播推送开启(是/否)', False)
        return cfg

    def _load_cookie_config(self) -> CookieConfig:
        cfg = CookieConfig()
        cfg.dy_cookie = self._get_value('Cookie', '抖音cookie', '')
        cfg.ks_cookie = self._get_value('Cookie', '快手cookie', '')
        cfg.tiktok_cookie = self._get_value('Cookie', 'tiktok_cookie', '')
        cfg.hy_cookie = self._get_value('Cookie', '虎牙cookie', '')
        cfg.douyu_cookie = self._get_value('Cookie', '斗鱼cookie', '')
        cfg.yy_cookie = self._get_value('Cookie', 'yy_cookie', '')
        cfg.bili_cookie = self._get_value('Cookie', 'B站cookie', '')
        cfg.xhs_cookie = self._get_value('Cookie', '小红书cookie', '')
        cfg.bigo_cookie = self._get_value('Cookie', 'bigo_cookie', '')
        cfg.blued_cookie = self._get_value('Cookie', 'blued_cookie', '')
        cfg.sooplive_cookie = self._get_value('Cookie', 'sooplive_cookie', '')
        cfg.netease_cookie = self._get_value('Cookie', 'netease_cookie', '')
        cfg.qiandurebo_cookie = self._get_value('Cookie', '千度热播_cookie', '')
        cfg.pandatv_cookie = self._get_value('Cookie', 'pandatv_cookie', '')
        cfg.maoerfm_cookie = self._get_value('Cookie', '猫耳fm_cookie', '')
        cfg.winktv_cookie = self._get_value('Cookie', 'winktv_cookie', '')
        cfg.flextv_cookie = self._get_value('Cookie', 'flextv_cookie', '')
        cfg.look_cookie = self._get_value('Cookie', 'look_cookie', '')
        cfg.twitcasting_cookie = self._get_value('Cookie', 'twitcasting_cookie', '')
        cfg.baidu_cookie = self._get_value('Cookie', 'baidu_cookie', '')
        cfg.weibo_cookie = self._get_value('Cookie', 'weibo_cookie', '')
        cfg.kugou_cookie = self._get_value('Cookie', 'kugou_cookie', '')
        cfg.twitch_cookie = self._get_value('Cookie', 'twitch_cookie', '')
        cfg.liveme_cookie = self._get_value('Cookie', 'liveme_cookie', '')
        cfg.huajiao_cookie = self._get_value('Cookie', 'huajiao_cookie', '')
        cfg.liuxing_cookie = self._get_value('Cookie', 'liuxing_cookie', '')
        cfg.showroom_cookie = self._get_value('Cookie', 'showroom_cookie', '')
        cfg.acfun_cookie = self._get_value('Cookie', 'acfun_cookie', '')
        cfg.changliao_cookie = self._get_value('Cookie', 'changliao_cookie', '')
        cfg.yinbo_cookie = self._get_value('Cookie', 'yinbo_cookie', '')
        cfg.yingke_cookie = self._get_value('Cookie', 'yingke_cookie', '')
        cfg.zhihu_cookie = self._get_value('Cookie', 'zhihu_cookie', '')
        cfg.chzzk_cookie = self._get_value('Cookie', 'chzzk_cookie', '')
        cfg.haixiu_cookie = self._get_value('Cookie', 'haixiu_cookie', '')
        cfg.vvxqiu_cookie = self._get_value('Cookie', 'vvxqiu_cookie', '')
        cfg.yiqilive_cookie = self._get_value('Cookie', '17live_cookie', '')
        cfg.langlive_cookie = self._get_value('Cookie', 'langlive_cookie', '')
        cfg.pplive_cookie = self._get_value('Cookie', 'pplive_cookie', '')
        cfg.six_room_cookie = self._get_value('Cookie', '6room_cookie', '')
        cfg.lehaitv_cookie = self._get_value('Cookie', 'lehaitv_cookie', '')
        cfg.huamao_cookie = self._get_value('Cookie', 'huamao_cookie', '')
        cfg.shopee_cookie = self._get_value('Cookie', 'shopee_cookie', '')
        cfg.youtube_cookie = self._get_value('Cookie', 'youtube_cookie', '')
        cfg.taobao_cookie = self._get_value('Cookie', 'taobao_cookie', '')
        cfg.jd_cookie = self._get_value('Cookie', 'jd_cookie', '')
        cfg.faceit_cookie = self._get_value('Cookie', 'faceit_cookie', '')
        cfg.migu_cookie = self._get_value('Cookie', 'migu_cookie', '')
        cfg.lianjie_cookie = self._get_value('Cookie', 'lianjie_cookie', '')
        cfg.laixiu_cookie = self._get_value('Cookie', 'laixiu_cookie', '')
        cfg.picarto_cookie = self._get_value('Cookie', 'picarto_cookie', '')
        return cfg

    def _load_account_config(self) -> AccountConfig:
        cfg = AccountConfig()
        cfg.sooplive_username = self._get_value('账号密码', 'sooplive账号', '')
        cfg.sooplive_password = self._get_value('账号密码', 'sooplive密码', '')
        cfg.flextv_username = self._get_value('账号密码', 'flextv账号', '')
        cfg.flextv_password = self._get_value('账号密码', 'flextv密码', '')
        cfg.popkontv_username = self._get_value('账号密码', 'popkontv账号', '')
        cfg.popkontv_partner_code = self._get_value('账号密码', 'partner_code', 'P-00001')
        cfg.popkontv_password = self._get_value('账号密码', 'popkontv密码', '')
        cfg.twitcasting_account_type = self._get_value('账号密码', 'twitcasting账号类型', 'normal')
        cfg.twitcasting_username = self._get_value('账号密码', 'twitcasting账号', '')
        cfg.twitcasting_password = self._get_value('账号密码', 'twitcasting密码', '')
        cfg.popkontv_access_token = self._get_value('Authorization', 'popkontv_token', '')
        return cfg
