# -*- encoding: utf-8 -*-
import datetime
import httpx
import os
import random
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

from src.config_manager import AppConfig
from src.ffmpeg_service import FFmpegService
from src.state_manager import StateManager, state_manager
from src.platform_adapters.adapter_factory import AdapterFactory
from src.platform_adapters.base_adapter import PlatformAdapter
from src.utils import logger, Color, get_query_params
from src.utils import remove_emojis

color_obj = Color()

_RSTR = r"[\/\\\:\*\？?\"\<\>\|&#.。,， ~！· ]"


def _get_error_line(e: BaseException) -> str:
    tb = e.__traceback__
    return str(tb.tb_lineno) if tb else "unknown"


def _clean_name(input_text: str, clean_emoji: bool = True) -> str:
    cleaned_name = re.sub(_RSTR, "_", input_text.strip()).strip('_')
    cleaned_name = cleaned_name.replace("（", "(").replace("）", ")")
    if clean_emoji:
        cleaned_name = remove_emojis(cleaned_name, '_').strip('_')
    return cleaned_name or '空白昵称'


def _get_quality_code(qn: str) -> str:
    quality_zh_to_en = {
        "原画": "OD", "蓝光": "BD", "超清": "UHD",
        "高清": "HD", "标清": "SD", "流畅": "LD"
    }
    return quality_zh_to_en.get(qn, '')


def _select_source_url(link: str, stream_info: Dict) -> Optional[str]:
    if any(i in link for i in ["douyin", "tiktok"]):
        flv_url = stream_info.get('flv_url')
        if flv_url:
            codec = get_query_params(flv_url, "codec")
            if codec and codec[0] == 'h265':
                logger.warning("FLV is not supported for h265 codec, use HLS source instead")
            else:
                return flv_url
    return stream_info.get('record_url')


class RecorderService:
    def __init__(
        self,
        app_config: AppConfig,
        state: StateManager = state_manager,
        ffmpeg_service: Optional[FFmpegService] = None,
        default_path: str = '',
        config_file: str = '',
    ):
        self.app_config = app_config
        self.record_config = app_config.record
        self.state = state
        self.ffmpeg = ffmpeg_service or FFmpegService()
        self.default_path = default_path
        self.config_file = config_file

    def _resolve_proxy(self, record_url: str) -> Optional[str]:
        proxy_address = self.record_config.proxy_addr
        if proxy_address:
            proxy_address = None
            if self.record_config.enable_proxy_platform_list:
                for platform in self.record_config.enable_proxy_platform_list:
                    if platform and platform.strip() in record_url:
                        proxy_address = self.record_config.proxy_addr
                        break

        if not proxy_address:
            if self.record_config.extra_enable_proxy_platform_list:
                for pt in self.record_config.extra_enable_proxy_platform_list:
                    if pt and pt.strip() in record_url:
                        proxy_address = self.record_config.proxy_addr_bak or None

        return proxy_address

    def _get_cookie_for_adapter(self, adapter: PlatformAdapter) -> str:
        cookie_cfg = self.app_config.cookie
        name_map = {
            'DouyinAdapter': cookie_cfg.dy_cookie,
            'KuaishouAdapter': cookie_cfg.ks_cookie,
            'TikTokAdapter': cookie_cfg.tiktok_cookie,
            'HuyaAdapter': cookie_cfg.hy_cookie,
            'DouyuAdapter': cookie_cfg.douyu_cookie,
            'YYAdapter': cookie_cfg.yy_cookie,
            'BilibiliAdapter': cookie_cfg.bili_cookie,
            'XHSAdapter': cookie_cfg.xhs_cookie,
            'BigoAdapter': cookie_cfg.bigo_cookie,
            'BluedAdapter': cookie_cfg.blued_cookie,
            'SOOPAdapter': cookie_cfg.sooplive_cookie,
            'NeteaseAdapter': cookie_cfg.netease_cookie,
            'QiandureboAdapter': cookie_cfg.qiandurebo_cookie,
            'PandaTVAdapter': cookie_cfg.pandatv_cookie,
            'MaoerfmAdapter': cookie_cfg.maoerfm_cookie,
            'WinkTVAdapter': cookie_cfg.winktv_cookie,
            'FlexTVAdapter': cookie_cfg.flextv_cookie,
            'LookAdapter': cookie_cfg.look_cookie,
            'TwitCastingAdapter': cookie_cfg.twitcasting_cookie,
            'BaiduAdapter': cookie_cfg.baidu_cookie,
            'WeiboAdapter': cookie_cfg.weibo_cookie,
            'KugouAdapter': cookie_cfg.kugou_cookie,
            'TwitchAdapter': cookie_cfg.twitch_cookie,
            'LiveMeAdapter': cookie_cfg.liveme_cookie,
            'HuajiaoAdapter': cookie_cfg.huajiao_cookie,
            'LiuxingAdapter': cookie_cfg.liuxing_cookie,
            'ShowRoomAdapter': cookie_cfg.showroom_cookie,
            'AcfunAdapter': cookie_cfg.acfun_cookie,
            'ChangliaoAdapter': cookie_cfg.changliao_cookie,
            'YinboAdapter': cookie_cfg.yinbo_cookie,
            'InkeAdapter': cookie_cfg.yingke_cookie,
            'ZhihuAdapter': cookie_cfg.zhihu_cookie,
            'CHZZKAdapter': cookie_cfg.chzzk_cookie,
            'HaixiuAdapter': cookie_cfg.haixiu_cookie,
            'VvxqiuAdapter': cookie_cfg.vvxqiu_cookie,
            'YiqiliveAdapter': cookie_cfg.yiqilive_cookie,
            'LangliveAdapter': cookie_cfg.langlive_cookie,
            'PpliveAdapter': cookie_cfg.pplive_cookie,
            'SixRoomAdapter': cookie_cfg.six_room_cookie,
            'LehaitvAdapter': cookie_cfg.lehaitv_cookie,
            'HuamaoAdapter': cookie_cfg.huamao_cookie,
            'ShopeeAdapter': cookie_cfg.shopee_cookie,
            'YoutubeAdapter': cookie_cfg.youtube_cookie,
            'TaobaoAdapter': cookie_cfg.taobao_cookie,
            'JDAdapter': cookie_cfg.jd_cookie,
            'FaceitAdapter': cookie_cfg.faceit_cookie,
            'MiguAdapter': cookie_cfg.migu_cookie,
            'LianjieAdapter': cookie_cfg.lianjie_cookie,
            'LaixiuAdapter': cookie_cfg.laixiu_cookie,
            'PicartoAdapter': cookie_cfg.picarto_cookie,
        }
        adapter_class_name = adapter.__class__.__name__
        return name_map.get(adapter_class_name, '')

    def _build_save_path(
        self,
        platform: str,
        anchor_name: str,
        now: str,
        live_title: str = '',
        port_info: Optional[Dict] = None,
    ) -> str:
        cfg = self.record_config
        full_path = f'{self.default_path}/{platform}'

        if len(cfg.save_path) > 0:
            if not cfg.save_path.endswith(('/', '\\')):
                full_path = f'{cfg.save_path}/{platform}'
            else:
                full_path = f'{cfg.save_path}{platform}'

        full_path = full_path.replace("\\", '/')
        if cfg.folder_by_author:
            full_path = f'{full_path}/{anchor_name}'
        if cfg.folder_by_time:
            full_path = f'{full_path}/{now[:10]}'
        if cfg.folder_by_title and port_info and port_info.get('title'):
            if cfg.folder_by_time:
                full_path = f'{full_path}/{live_title}_{anchor_name}'
            else:
                full_path = f'{full_path}/{now[:10]}_{live_title}'

        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return full_path

    def _direct_download_stream(
        self,
        source_url: str,
        save_path: str,
        record_name: str,
        live_url: str,
    ) -> bool:
        try:
            with open(save_path, 'wb') as f:
                client = httpx.Client(timeout=None)
                headers = {}
                adapter = AdapterFactory.get_adapter(live_url)
                if adapter:
                    header_params = adapter.get_record_headers(live_url)
                    if header_params:
                        key, value = header_params.split(":", 1)
                        headers[key] = value

                with client.stream('GET', source_url, headers=headers, follow_redirects=True) as response:
                    if response.status_code != 200:
                        logger.error(f"请求直播流失败，状态码: {response.status_code}")
                        return False

                    for chunk in response.iter_bytes(1024 * 16):
                        if live_url in self.state.url_comments or self.state.exit_recording:
                            color_obj.print_colored(
                                f"[{record_name}]录制时已被注释或请求停止,下载中断", color_obj.YELLOW)
                            self.state.clear_record_info(record_name, live_url)
                            return False
                        if chunk:
                            f.write(chunk)
                    print()
                    return True
        except Exception as e:
            logger.error(f"FLV下载错误: {e} 发生错误的行数: {_get_error_line(e)}")
            return False

    def _generate_subtitles(self, record_name: str, ass_filename: str, sub_format: str = 'srt') -> None:
        index_time = 0
        today = datetime.datetime.now()
        re_datatime = today.strftime('%Y-%m-%d %H:%M:%S')

        def transform_int_to_time(seconds: int) -> str:
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        while True:
            index_time += 1
            txt = (str(index_time) + "\n" + transform_int_to_time(index_time) + ',000 --> '
                   + transform_int_to_time(index_time + 1) + ',000' + "\n" + str(re_datatime) + "\n\n")

            with open(f"{ass_filename}.{sub_format.lower()}", 'a', encoding='utf-8-sig') as f:
                f.write(txt)

            if record_name not in self.state.recording:
                return
            time.sleep(1)
            today = datetime.datetime.now()
            re_datatime = today.strftime('%Y-%m-%d %H:%M:%S')

    def _check_subprocess(
        self,
        record_name: str,
        record_url: str,
        ffmpeg_command: List[str],
        save_type: str,
        script_command: Optional[str] = None,
    ) -> bool:
        save_file_path = ffmpeg_command[-1]
        process = self.ffmpeg.start_process(ffmpeg_command)

        subs_file_path = save_file_path.rsplit('.', maxsplit=1)[0]
        cfg = self.record_config
        if cfg.create_time_file and not cfg.split_video_by_time and '音频' not in save_type:
            t = threading.Thread(target=self._generate_subtitles, args=(record_name, subs_file_path))
            t.daemon = True
            t.start()

        while process.poll() is None:
            if record_url in self.state.url_comments or self.state.exit_recording:
                color_obj.print_colored(f"[{record_name}]录制时已被注释,本条线程将会退出", color_obj.YELLOW)
                self.state.clear_record_info(record_name, record_url)
                self.ffmpeg.stop_process(process)
                return True
            time.sleep(1)

        return_code = process.returncode
        stop_time = time.strftime('%Y-%m-%d %H:%M:%S')
        if return_code == 0:
            if cfg.converts_to_mp4 and save_type == 'TS':
                if cfg.split_video_by_time:
                    from src.utils import get_file_paths
                    file_paths = get_file_paths(os.path.dirname(save_file_path))
                    prefix = os.path.basename(save_file_path).rsplit('_', maxsplit=1)[0]
                    for path in file_paths:
                        if prefix in path:
                            threading.Thread(
                                target=FFmpegService.converts_mp4,
                                args=(path, cfg.delete_origin_file, cfg.converts_to_h264)
                            ).start()
                else:
                    threading.Thread(
                        target=FFmpegService.converts_mp4,
                        args=(save_file_path, cfg.delete_origin_file, cfg.converts_to_h264)
                    ).start()
            print(f"\n{record_name} {stop_time} 直播录制完成\n")

            if script_command:
                logger.debug("开始执行脚本命令!")
                self._run_script(record_name, save_file_path, save_type, script_command)
                logger.debug("脚本命令执行结束!")
        else:
            color_obj.print_colored(
                f"\n{record_name} {stop_time} 直播录制出错,返回码: {return_code}\n", color_obj.RED)

        self.state.remove_recording(record_name)
        return False

    def _run_script(
        self,
        record_name: str,
        save_file_path: str,
        save_type: str,
        script_command: str,
    ) -> None:
        cfg = self.record_config
        if "python" in script_command:
            params = [
                f'--record_name "{record_name}"',
                f'--save_file_path "{save_file_path}"',
                f'--save_type {save_type}',
                f'--split_video_by_time {cfg.split_video_by_time}',
                f'--converts_to_mp4 {cfg.converts_to_mp4}',
            ]
        else:
            params = [
                f'"{record_name.split(" ", maxsplit=1)[-1]}"',
                f'"{save_file_path}"',
                save_type,
                f'split_video_by_time:{cfg.split_video_by_time}',
                f'converts_to_mp4:{cfg.converts_to_mp4}'
            ]
        full_command = script_command.strip() + ' ' + ' '.join(params)
        try:
            process = subprocess.Popen(
                full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                startupinfo=self.ffmpeg.startup_info
            )
            stdout, stderr = process.communicate()
            if stdout and stdout.decode('utf-8').strip():
                print(stdout.decode('utf-8'))
            if stderr and stderr.decode('utf-8').strip():
                print(stderr.decode('utf-8'))
        except PermissionError as e:
            logger.error(e)
            logger.error('脚本无执行权限!, 若是Linux环境, 请先执行:chmod +x your_script.sh 授予脚本可执行权限')
        except OSError as e:
            logger.error(e)
            logger.error('Please add `#!/bin/bash` at the beginning of your bash script file.')

    def start_record(self, url_data: tuple, count_variable: int = -1) -> None:
        cfg = self.record_config

        while True:
            try:
                record_finished = False
                run_once = False
                start_pushed = False
                new_record_url = ''
                count_time = time.time()
                record_quality_zh, record_url, anchor_name = url_data
                record_quality = _get_quality_code(record_quality_zh)
                proxy_address = self._resolve_proxy(record_url)
                platform = '未知平台'

                while True:
                    try:
                        adapter = AdapterFactory.get_adapter(record_url)
                        if not adapter:
                            logger.error(f'{record_url} {platform}直播地址')
                            return

                        platform = adapter.get_platform_name()
                        cookies = self._get_cookie_for_adapter(adapter)

                        if self.state.semaphore is not None:
                            with self.state.semaphore:
                                port_info = adapter.get_stream_info(
                                    url=record_url,
                                    quality=record_quality,
                                    proxy=proxy_address,
                                    cookies=cookies,
                                    global_proxy=self._global_proxy,
                                    account_config=self.app_config.account,
                                    config_file=self.config_file,
                                )
                        else:
                            port_info = adapter.get_stream_info(
                                url=record_url,
                                quality=record_quality,
                                proxy=proxy_address,
                                cookies=cookies,
                                global_proxy=self._global_proxy,
                                account_config=self.app_config.account,
                                config_file=self.config_file,
                            )

                        if not port_info:
                            port_info = {}

                        if anchor_name:
                            if '主播:' in anchor_name:
                                anchor_split: list = anchor_name.split('主播:')
                                if len(anchor_split) > 1 and anchor_split[1].strip():
                                    anchor_name = anchor_split[1].strip()
                                else:
                                    anchor_name = port_info.get("anchor_name", '')
                        else:
                            anchor_name = port_info.get("anchor_name", '')

                        if not port_info.get("anchor_name", ''):
                            print(f'序号{count_variable} 网址内容获取失败,进行重试中...获取失败的地址是:{url_data}')
                            self.state.increment_error()
                            self.state.append_error_window(1)
                        else:
                            anchor_name = _clean_name(anchor_name, cfg.clean_emoji)
                            record_name = f'序号{count_variable} {anchor_name}'

                            if record_url in self.state.url_comments:
                                print(f"[{anchor_name}]已被注释,本条线程将会退出")
                                self.state.clear_record_info(record_name, record_url)
                                return

                            if not url_data[-1] and run_once is False:
                                if new_record_url:
                                    self.state.need_update_line_list.append(
                                        f'{record_url}|{new_record_url},主播: {anchor_name.strip()}')
                                    self.state.not_record_list.append(new_record_url)
                                else:
                                    self.state.need_update_line_list.append(
                                        f'{record_url}|{record_url},主播: {anchor_name.strip()}')
                                run_once = True

                            push_at = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                            if port_info.get('is_live') is False:
                                print(f"\r{record_name} 等待直播... ")
                                if start_pushed:
                                    if self.app_config.push.over_show_push:
                                        from src.notification_service import NotificationService
                                        push_content = "直播间状态更新：[直播间名称] 直播已结束！时间：[时间]"
                                        if self.app_config.push.over_push_message_text:
                                            push_content = self.app_config.push.over_push_message_text
                                        push_content = (push_content.replace('[直播间名称]', record_name).
                                                        replace('[时间]', push_at))
                                        ns = NotificationService(self.app_config)
                                        threading.Thread(
                                            target=ns.push_message,
                                            args=(record_name, record_url,
                                                  push_content.replace(r'\n', '\n')),
                                            daemon=True
                                        ).start()
                                    start_pushed = False
                            else:
                                print(f"\r{record_name} 正在直播中...")

                                if self.app_config.push.live_status_push and not start_pushed:
                                    if self.app_config.push.begin_show_push:
                                        from src.notification_service import NotificationService
                                        push_content = "直播间状态更新：[直播间名称] 正在直播中，时间：[时间]"
                                        if self.app_config.push.begin_push_message_text:
                                            push_content = self.app_config.push.begin_push_message_text
                                        push_content = (push_content.replace('[直播间名称]', record_name).
                                                        replace('[时间]', push_at))
                                        ns = NotificationService(self.app_config)
                                        threading.Thread(
                                            target=ns.push_message,
                                            args=(record_name, record_url,
                                                  push_content.replace(r'\n', '\n')),
                                            daemon=True
                                        ).start()
                                    start_pushed = True

                                if self.app_config.push.disable_record:
                                    time.sleep(self.app_config.push.push_check_seconds)
                                    continue

                                self._do_record(
                                    adapter, port_info, record_url, record_name,
                                    anchor_name, record_quality_zh, proxy_address,
                                    platform
                                )
                                count_time = time.time()

                    except Exception as e:
                        logger.error(f"错误信息: {e} 发生错误的行数: {_get_error_line(e)}")
                        self.state.increment_error()
                        self.state.append_error_window(1)

                    num = random.randint(-5, 5) + cfg.delay_default
                    if num < 0:
                        num = 0
                    x = num

                    if self.state.error_count > 20:
                        x = x + 60
                        color_obj.print_colored("\r瞬时错误太多,延迟加60秒", color_obj.YELLOW)

                    if record_finished:
                        count_time_end = time.time() - count_time
                        if count_time_end < 60:
                            x = 30
                        record_finished = False
                    else:
                        x = num

                    while x:
                        x = x - 1
                        if cfg.loop_time:
                            print(f'\r{anchor_name}循环等待{x}秒 ', end="")
                        time.sleep(1)
                    if cfg.loop_time:
                        print('\r检测直播间中...', end="")

            except Exception as e:
                logger.error(f"错误信息: {e} 发生错误的行数: {_get_error_line(e)}")
                self.state.increment_error()
                self.state.append_error_window(1)
                time.sleep(2)

    def _do_record(
        self,
        adapter: PlatformAdapter,
        port_info: Dict,
        record_url: str,
        record_name: str,
        anchor_name: str,
        record_quality_zh: str,
        proxy_address: Optional[str],
        platform: str,
    ) -> None:
        cfg = self.record_config
        real_url = _select_source_url(record_url, port_info)

        if not real_url:
            return

        now = datetime.datetime.today().strftime("%Y-%m-%d_%H-%M-%S")
        live_title = port_info.get('title', '')
        title_in_name = ''
        if live_title:
            live_title = _clean_name(live_title, cfg.clean_emoji)
            title_in_name = live_title + '_' if cfg.filename_by_title else ''

        full_path = self._build_save_path(platform, anchor_name, now, live_title, port_info)

        if platform != '自定义录制直播':
            if cfg.enable_https_recording and real_url.startswith("http://"):
                real_url = real_url.replace("http://", "https://")
            if adapter.use_http_recording():
                real_url = real_url.replace("https://", "http://")

        headers = adapter.get_record_headers(record_url)
        ffmpeg_command = self.ffmpeg.build_base_command(
            stream_url=real_url,
            proxy_address=proxy_address,
            headers=headers,
            record_url=record_url,
            enable_https=cfg.enable_https_recording,
            platform=platform,
        )

        if cfg.show_url:
            re_plat = ('WinkTV', 'PandaTV', 'ShowRoom', 'CHZZK', 'Youtube')
            if platform in re_plat:
                logger.info(f"{platform} | {anchor_name} | 直播源地址: {port_info.get('m3u8_url')}")
            else:
                logger.info(f"{platform} | {anchor_name} | 直播源地址: {real_url}")

        only_flv_record = adapter.is_only_flv()
        only_audio_record = adapter.is_only_audio()
        record_save_type = cfg.video_save_type

        if adapter.is_flv_preferred() and port_info.get('flv_url'):
            codec = get_query_params(port_info['flv_url'], "codec")
            if codec and codec[0] == 'h265':
                logger.warning("FLV is not supported for h265 codec, use TS format instead")
                record_save_type = "TS"

        self.state.add_recording(record_name, record_quality_zh)

        rec_info = f"\r{anchor_name} 准备开始录制视频: {full_path}"

        if only_audio_record or any(i in record_save_type for i in ['MP3', 'M4A']):
            self._record_audio(
                ffmpeg_command, record_save_type, record_name, record_url,
                anchor_name, title_in_name, now, full_path
            )
        elif only_flv_record:
            self._record_flv_direct(
                port_info, record_name, record_url, anchor_name,
                title_in_name, now, full_path, rec_info
            )
        elif record_save_type == "FLV":
            self._record_flv(
                ffmpeg_command, record_name, record_url, anchor_name,
                title_in_name, now, full_path, rec_info
            )
        elif record_save_type == "MKV":
            self._record_mkv(
                ffmpeg_command, record_name, record_url, anchor_name,
                title_in_name, now, full_path, rec_info
            )
        elif record_save_type == "MP4":
            self._record_mp4(
                ffmpeg_command, record_name, record_url, anchor_name,
                title_in_name, now, full_path, rec_info
            )
        else:
            self._record_ts(
                ffmpeg_command, record_name, record_url, anchor_name,
                title_in_name, now, full_path, rec_info
            )

    def _record_audio(
        self, ffmpeg_command, save_type, record_name, record_url,
        anchor_name, title_in_name, now, full_path
    ) -> None:
        cfg = self.record_config
        try:
            now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            extension = "mp3" if "m4a" not in save_type.lower() else "m4a"
            name_format = "_%03d" if cfg.split_video_by_time else ""
            save_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now}{name_format}.{extension}"

            if cfg.split_video_by_time:
                print(f'\r{anchor_name} 准备开始录制音频: {save_file_path}')

            command = self.ffmpeg.build_audio_command(save_type, cfg.split_video_by_time, cfg.split_time, save_file_path)
            ffmpeg_command.extend(command)
            comment_end = self._check_subprocess(
                record_name, record_url, ffmpeg_command, save_type, cfg.custom_script)
            if comment_end:
                return

        except subprocess.CalledProcessError as e:
            logger.error(f"错误信息: {e} 发生错误的行数: {_get_error_line(e)}")
            self.state.increment_error()
            self.state.append_error_window(1)

    def _record_flv_direct(
        self, port_info, record_name, record_url, anchor_name,
        title_in_name, now, full_path, rec_info
    ) -> None:
        cfg = self.record_config
        logger.info(f"Use Direct Downloader to Download FLV Stream: {record_url}")
        filename = anchor_name + f'_{title_in_name}' + now + '.flv'
        save_file_path = f'{full_path}/{filename}'
        print(f'{rec_info}/{filename}')

        subs_file_path = save_file_path.rsplit('.', maxsplit=1)[0]
        if cfg.create_time_file:
            t = threading.Thread(target=self._generate_subtitles, args=(record_name, subs_file_path))
            t.daemon = True
            t.start()

        try:
            flv_url = port_info.get('flv_url')
            if flv_url:
                self.state.add_recording(record_name, '')
                download_success = self._direct_download_stream(
                    flv_url, save_file_path, record_name, record_url)
                if download_success:
                    print(f"\n{anchor_name} {time.strftime('%Y-%m-%d %H:%M:%S')} 直播录制完成\n")
                self.state.remove_recording(record_name)
            else:
                logger.debug("未找到FLV直播流，跳过录制")
        except Exception as e:
            self.state.clear_record_info(record_name, record_url)
            color_obj.print_colored(
                f"\n{anchor_name} {time.strftime('%Y-%m-%d %H:%M:%S')} 直播录制出错,请检查网络\n",
                color_obj.RED)
            logger.error(f"错误信息: {e} 发生错误的行数: {_get_error_line(e)}")
            self.state.increment_error()
            self.state.append_error_window(1)

    def _record_flv(
        self, ffmpeg_command, record_name, record_url, anchor_name,
        title_in_name, now, full_path, rec_info
    ) -> None:
        cfg = self.record_config
        filename = anchor_name + f'_{title_in_name}' + now + ".flv"
        print(f'{rec_info}/{filename}')
        save_file_path = full_path + '/' + filename

        try:
            if cfg.split_video_by_time:
                now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                save_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now}_%03d.flv"

            command = self.ffmpeg.build_flv_command(cfg.split_video_by_time, cfg.split_time, save_file_path)
            ffmpeg_command.extend(command)
            comment_end = self._check_subprocess(
                record_name, record_url, ffmpeg_command, "FLV", cfg.custom_script)
            if comment_end:
                return
        except subprocess.CalledProcessError as e:
            logger.error(f"错误信息: {e} 发生错误的行数: {_get_error_line(e)}")
            self.state.increment_error()
            self.state.append_error_window(1)

        try:
            if cfg.converts_to_mp4:
                seg_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now}_%03d.mp4"
                if cfg.split_video_by_time:
                    FFmpegService.segment_video(
                        save_file_path, seg_file_path,
                        segment_format='mp4', segment_time=cfg.split_time,
                        is_original_delete=cfg.delete_origin_file
                    )
                else:
                    threading.Thread(
                        target=FFmpegService.converts_mp4,
                        args=(save_file_path, cfg.delete_origin_file, cfg.converts_to_h264)
                    ).start()
            else:
                seg_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now}_%03d.flv"
                if cfg.split_video_by_time:
                    FFmpegService.segment_video(
                        save_file_path, seg_file_path,
                        segment_format='flv', segment_time=cfg.split_time,
                        is_original_delete=cfg.delete_origin_file
                    )
        except Exception as e:
            logger.error(f"转码失败: {e} ")

    def _record_mkv(
        self, ffmpeg_command, record_name, record_url, anchor_name,
        title_in_name, now, full_path, rec_info
    ) -> None:
        cfg = self.record_config
        filename = anchor_name + f'_{title_in_name}' + now + ".mkv"
        print(f'{rec_info}/{filename}')
        save_file_path = full_path + '/' + filename

        try:
            if cfg.split_video_by_time:
                now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                save_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now}_%03d.mkv"

            command = self.ffmpeg.build_mkv_command(cfg.split_video_by_time, cfg.split_time, save_file_path)
            ffmpeg_command.extend(command)
            comment_end = self._check_subprocess(
                record_name, record_url, ffmpeg_command, "MKV", cfg.custom_script)
            if comment_end:
                return
        except subprocess.CalledProcessError as e:
            logger.error(f"错误信息: {e} 发生错误的行数: {_get_error_line(e)}")
            self.state.increment_error()
            self.state.append_error_window(1)

    def _record_mp4(
        self, ffmpeg_command, record_name, record_url, anchor_name,
        title_in_name, now, full_path, rec_info
    ) -> None:
        cfg = self.record_config
        filename = anchor_name + f'_{title_in_name}' + now + ".mp4"
        print(f'{rec_info}/{filename}')
        save_file_path = full_path + '/' + filename

        try:
            if cfg.split_video_by_time:
                now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                save_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now}_%03d.mp4"

            command = self.ffmpeg.build_mp4_command(cfg.split_video_by_time, cfg.split_time, save_file_path)
            ffmpeg_command.extend(command)
            comment_end = self._check_subprocess(
                record_name, record_url, ffmpeg_command, "MP4", cfg.custom_script)
            if comment_end:
                return
        except subprocess.CalledProcessError as e:
            logger.error(f"错误信息: {e} 发生错误的行数: {_get_error_line(e)}")
            self.state.increment_error()
            self.state.append_error_window(1)

    def _record_ts(
        self, ffmpeg_command, record_name, record_url, anchor_name,
        title_in_name, now, full_path, rec_info
    ) -> None:
        cfg = self.record_config
        if cfg.split_video_by_time:
            now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            filename = anchor_name + f'_{title_in_name}' + now + ".ts"
            print(f'{rec_info}/{filename}')

            try:
                save_file_path = f"{full_path}/{anchor_name}_{title_in_name}{now}_%03d.ts"
                command = self.ffmpeg.build_ts_command(cfg.split_video_by_time, cfg.split_time, save_file_path)
                ffmpeg_command.extend(command)
                comment_end = self._check_subprocess(
                    record_name, record_url, ffmpeg_command, "TS", cfg.custom_script)
                if comment_end:
                    if cfg.converts_to_mp4:
                        from src.utils import get_file_paths
                        file_paths = get_file_paths(os.path.dirname(save_file_path))
                        prefix = os.path.basename(save_file_path).rsplit('_', maxsplit=1)[0]
                        for path in file_paths:
                            if prefix in path:
                                try:
                                    threading.Thread(
                                        target=FFmpegService.converts_mp4,
                                        args=(path, cfg.delete_origin_file, cfg.converts_to_h264)
                                    ).start()
                                except subprocess.CalledProcessError as e:
                                    logger.error(f"转码失败: {e} ")
                    return
            except subprocess.CalledProcessError as e:
                logger.error(f"错误信息: {e} 发生错误的行数: {_get_error_line(e)}")
                self.state.increment_error()
                self.state.append_error_window(1)
        else:
            filename = anchor_name + f'_{title_in_name}' + now + ".ts"
            print(f'{rec_info}/{filename}')
            save_file_path = full_path + '/' + filename

            try:
                command = self.ffmpeg.build_ts_command(False, cfg.split_time, save_file_path)
                ffmpeg_command.extend(command)
                comment_end = self._check_subprocess(
                    record_name, record_url, ffmpeg_command, "TS", cfg.custom_script)
                if comment_end:
                    threading.Thread(
                        target=FFmpegService.converts_mp4,
                        args=(save_file_path, cfg.delete_origin_file, cfg.converts_to_h264)
                    ).start()
                    return
            except subprocess.CalledProcessError as e:
                logger.error(f"错误信息: {e} 发生错误的行数: {_get_error_line(e)}")
                self.state.increment_error()
                self.state.append_error_window(1)

    @property
    def _global_proxy(self) -> bool:
        return getattr(self, '_global_proxy_value', False)

    @_global_proxy.setter
    def _global_proxy(self, value: bool) -> None:
        self._global_proxy_value = value
