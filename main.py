# -*- encoding: utf-8 -*-

"""
Author: Hmily
GitHub: https://github.com/ihmily
Date: 2023-07-17 23:52:05
Update: 2025-10-23 19:48:05
Copyright (c) 2023-2025 by Hmily, All Rights Reserved.
Function: Record live stream video.
"""
import os
import sys
import builtins
import subprocess
import signal
import threading
import time
import datetime
import urllib.request
from urllib.error import URLError, HTTPError
from pathlib import Path

from ffmpeg_install import check_ffmpeg, ffmpeg_path, current_env_path
from src.config_manager import ConfigManager, AppConfig
from src.state_manager import StateManager, state_manager
from src.file_manager import FileManager
from src.recorder_service import RecorderService
from src.platform_adapters import (
    AdapterFactory,
    DouyinAdapter, KuaishouAdapter, HuyaAdapter, DouyuAdapter, YYAdapter,
    BilibiliAdapter, XHSAdapter, BigoAdapter, BluedAdapter, NeteaseAdapter,
    QiandureboAdapter, MaoerfmAdapter, LookAdapter, TwitCastingAdapter,
    BaiduAdapter, WeiboAdapter, KugouAdapter, HuajiaoAdapter, LiuxingAdapter,
    AcfunAdapter, ChangliaoAdapter, YinboAdapter, InkeAdapter, ZhihuAdapter,
    HaixiuAdapter, VvxqiuAdapter, YiqiliveAdapter, LangliveAdapter,
    PpliveAdapter, SixRoomAdapter, LehaitvAdapter, HuamaoAdapter,
    TaobaoAdapter, JDAdapter, MiguAdapter, LianjieAdapter, LaixiuAdapter,
    CustomStreamAdapter,
    TikTokAdapter, SOOPAdapter, PandaTVAdapter, WinkTVAdapter,
    FlexTVAdapter, PopkonTVAdapter, TwitchAdapter, LiveMeAdapter,
    ShowRoomAdapter, CHZZKAdapter, ShopeeAdapter, YoutubeAdapter,
    FaceitAdapter, PicartoAdapter,
)
from src.proxy import ProxyDetector
from src.utils import logger, Color
from src import utils

version = "v4.0.7"
platforms = ("\n国内站点：抖音|快手|虎牙|斗鱼|YY|B站|小红书|bigo|blued|网易CC|千度热播|猫耳FM|Look|TwitCasting|百度|微博|"
             "酷狗|花椒|流星|Acfun|畅聊|映客|音播|知乎|嗨秀|VV星球|17Live|浪Live|漂漂|六间房|乐嗨|花猫|淘宝|京东|咪咕|连接|来秀"
             "\n海外站点：TikTok|SOOP|PandaTV|WinkTV|FlexTV|PopkonTV|TwitchTV|LiveMe|ShowRoom|CHZZK|Shopee|"
             "Youtube|Faceit|Picarto")

color_obj = Color()

script_path = os.path.split(os.path.realpath(sys.argv[0]))[0]
config_file = f'{script_path}/config/config.ini'
url_config_file = f'{script_path}/config/URL_config.ini'
backup_dir = f'{script_path}/backup_config'
default_path = f'{script_path}/downloads'
os.makedirs(default_path, exist_ok=True)

os.environ['PATH'] = ffmpeg_path + os.pathsep + (current_env_path or '')


def _register_adapters() -> None:
    AdapterFactory.clear()
    domestic_adapters = [
        DouyinAdapter(), KuaishouAdapter(), HuyaAdapter(), DouyuAdapter(),
        YYAdapter(), BilibiliAdapter(), XHSAdapter(), BigoAdapter(),
        BluedAdapter(), NeteaseAdapter(), QiandureboAdapter(), MaoerfmAdapter(),
        LookAdapter(), TwitCastingAdapter(), BaiduAdapter(), WeiboAdapter(),
        KugouAdapter(), HuajiaoAdapter(), LiuxingAdapter(), AcfunAdapter(),
        ChangliaoAdapter(), YinboAdapter(), InkeAdapter(), ZhihuAdapter(),
        HaixiuAdapter(), VvxqiuAdapter(), YiqiliveAdapter(), LangliveAdapter(),
        PpliveAdapter(), SixRoomAdapter(), LehaitvAdapter(), HuamaoAdapter(),
        TaobaoAdapter(), JDAdapter(), MiguAdapter(), LianjieAdapter(),
        LaixiuAdapter(), CustomStreamAdapter(),
    ]
    overseas_adapters = [
        TikTokAdapter(), SOOPAdapter(), PandaTVAdapter(), WinkTVAdapter(),
        FlexTVAdapter(), PopkonTVAdapter(), TwitchAdapter(), LiveMeAdapter(),
        ShowRoomAdapter(), CHZZKAdapter(), ShopeeAdapter(), YoutubeAdapter(),
        FaceitAdapter(), PicartoAdapter(),
    ]
    for adapter in domestic_adapters + overseas_adapters:
        AdapterFactory.register(adapter)


def _check_ffmpeg_existence() -> bool:
    try:
        result = subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            print(lines[0])
            print(lines[1])
    except subprocess.CalledProcessError as e:
        logger.error(e)
    except FileNotFoundError:
        pass
    if check_ffmpeg():
        time.sleep(1)
        return True
    return False


def _display_info(recorder_service: RecorderService) -> None:
    start_display_time = datetime.datetime.now()
    time.sleep(5)
    clear_command = "cls" if os.name == 'nt' else "clear"
    cfg = recorder_service.record_config
    push_cfg = recorder_service.app_config.push

    while True:
        try:
            sys.stdout.flush()
            time.sleep(5)
            if Path(sys.executable).name != 'pythonw.exe':
                subprocess.run(clear_command, shell=True)
            print(f"\r共监测{state_manager.monitoring}个直播中", end=" | ")
            print(f"同一时间访问网络的线程数: {state_manager.max_request}", end=" | ")
            print(f"是否开启代理录制: {'是' if cfg.use_proxy else '否'}", end=" | ")
            if cfg.split_video_by_time:
                print(f"录制分段开启: {cfg.split_time}秒", end=" | ")
            else:
                print("录制分段开启: 否", end=" | ")
            if cfg.create_time_file:
                print("是否生成时间文件: 是", end=" | ")
            print(f"录制视频质量为: {cfg.video_record_quality}", end=" | ")
            print(f"录制视频格式为: {cfg.video_save_type}", end=" | ")
            print(f"目前瞬时错误数为: {state_manager.error_count}", end=" | ")
            now = time.strftime("%H:%M:%S", time.localtime())
            print(f"当前时间: {now}")

            if len(state_manager.recording) == 0:
                time.sleep(5)
                if state_manager.monitoring == 0:
                    print("\r没有正在监测和录制的直播")
                else:
                    print(f"\r没有正在录制的直播 循环监测间隔时间：{cfg.delay_default}秒")
            else:
                now_time = datetime.datetime.now()
                print("x" * 60)
                no_repeat_recording = state_manager.get_no_repeat_recording()
                print(f"正在录制{len(no_repeat_recording)}个直播: ")
                for recording_live in no_repeat_recording:
                    info = state_manager.recording_time_list.get(recording_live)
                    if info:
                        have_record_time = now_time - info.start_time
                        print(f"{recording_live}[{info.quality}] 正在录制中 {str(have_record_time).split('.')[0]}")
                print("x" * 60)
                start_display_time = now_time
        except Exception as e:
            logger.error(f"错误信息: {e} 发生错误的行数: {_get_error_line(e)}")


def _adjust_max_request() -> None:
    error_threshold = 5
    while True:
        time.sleep(5)
        with state_manager._max_request_lock:
            error_window = state_manager.error_window
            if error_window:
                error_rate = sum(error_window) / len(error_window)
            else:
                error_rate = 0

            max_request = state_manager.max_request
            pre_max_request = state_manager.pre_max_request

            if error_rate > error_threshold:
                max_request = max(1, max_request - 1)
            elif error_rate < error_threshold / 2 and max_request < pre_max_request:
                max_request += 1

            if pre_max_request != max_request:
                state_manager.pre_max_request = max_request
                logger.debug(f"同一时间访问网络的线程数动态改为 {max_request}")

            state_manager.max_request = max_request

        state_manager.append_error_window(state_manager.error_count)
        state_manager.reset_error_count()


def _get_error_line(e: BaseException) -> str:
    tb = e.__traceback__
    return str(tb.tb_lineno) if tb else "unknown"


def _signal_handler(_signal, _frame):
    sys.exit(0)


signal.signal(signal.SIGTERM, _signal_handler)


def main() -> None:
    print("-----------------------------------------------------")
    print("|                DouyinLiveRecorder                 |")
    print("-----------------------------------------------------")
    print(f"版本号: {version}")
    print("GitHub: https://github.com/ihmily/DouyinLiveRecorder")
    print(f'支持平台: {platforms}')
    print('.....................................................')

    if not _check_ffmpeg_existence():
        logger.error("缺少ffmpeg无法进行录制，程序退出")
        sys.exit(1)

    os.makedirs(os.path.dirname(config_file), exist_ok=True)

    _register_adapters()

    file_manager = FileManager(config_file, url_config_file, backup_dir)
    t3 = threading.Thread(target=file_manager.backup_file_start, args=(), daemon=True)
    t3.start()
    utils.remove_duplicate_lines(url_config_file)

    config_manager = ConfigManager(config_file)
    app_config = config_manager.load()

    language = app_config.record.language
    skip_proxy_check = app_config.record.skip_proxy_check
    if language and 'en' not in language.lower():
        from i18n import translated_print
        builtins.print = translated_print

    global_proxy = False
    try:
        if skip_proxy_check:
            global_proxy = True
        else:
            print('系统代理检测中，请耐心等待...')
            response_g = urllib.request.urlopen("https://www.google.com/", timeout=15)
            global_proxy = True
            print('\r全局/规则网络代理已开启√')
            pd = ProxyDetector()
            if pd.is_proxy_enabled():
                proxy_info = pd.get_proxy_info()
                print("System Proxy: http://{}:{}".format(proxy_info.ip, proxy_info.port))
    except HTTPError as err:
        print(f"HTTP error occurred: {err.code} - {err.reason}")
    except URLError:
        color_obj.print_colored(
            "INFO：未检测到全局/规则网络代理，请检查代理配置（若无需录制海外直播请忽略此条提示）",
            color_obj.YELLOW)
    except Exception as err:
        print("An unexpected error occurred:", err)

    recorder_service = RecorderService(
        app_config=app_config,
        state=state_manager,
        default_path=default_path,
        config_file=config_file,
    )
    recorder_service._global_proxy = global_proxy

    state_manager.semaphore = threading.Semaphore(app_config.record.max_request)
    state_manager.max_request = app_config.record.max_request
    state_manager.pre_max_request = app_config.record.max_request

    while True:
        try:
            if not os.path.isfile(config_file):
                with open(config_file, 'w', encoding='utf-8-sig') as file:
                    pass

            if os.path.isfile(url_config_file):
                with open(url_config_file, 'r', encoding='utf-8-sig') as file:
                    ini_content = file.read().strip()
                if not ini_content.strip():
                    input_url = input('请输入要录制的主播直播间网址（尽量使用PC网页端的直播间地址）:\n')
                    with open(url_config_file, 'w', encoding='utf-8-sig') as file:
                        file.write(input_url)
        except OSError as err:
            logger.error(f"发生 I/O 错误: {err}")

        app_config = config_manager.load()
        recorder_service.app_config = app_config
        recorder_service.record_config = app_config.record

        check_path = app_config.record.save_path or default_path
        if utils.check_disk_capacity(check_path, show=state_manager.first_run) < app_config.record.disk_space_limit:
            state_manager.exit_recording = True
            if not state_manager.recording:
                logger.warning(
                    f"Disk space remaining is below {app_config.record.disk_space_limit} GB. "
                    f"Exiting program due to the disk space limit being reached.")
                sys.exit(-1)

        try:
            url_tuples_list, url_comments = file_manager.parse_url_config(
                url_comments=state_manager.url_comments,
                running_list=state_manager.running_list,
                need_update_line_list=state_manager.need_update_line_list,
            )

            state_manager.url_comments.clear()
            state_manager.url_comments.extend(url_comments)

            text_no_repeat_url = list(set(url_tuples_list))

            if len(text_no_repeat_url) > 0:
                create_var = locals()
                for url_tuple in text_no_repeat_url:
                    monitoring = len(state_manager.running_list)

                    if url_tuple[1] in state_manager.not_record_list:
                        continue

                    if url_tuple[1] not in state_manager.running_list:
                        print(f"\r{'新增' if not state_manager.first_start else '传入'}地址: {url_tuple[1]}")
                        monitoring += 1
                        args = [url_tuple, monitoring]
                        create_var[f'thread_{monitoring}'] = threading.Thread(
                            target=recorder_service.start_record, args=args)
                        create_var[f'thread_{monitoring}'].daemon = True
                        create_var[f'thread_{monitoring}'].start()
                        state_manager.add_running_url(url_tuple[1])
                        time.sleep(app_config.record.local_delay_default)

            state_manager.first_start = False

        except Exception as err:
            logger.error(f"错误信息: {err} 发生错误的行数: {_get_error_line(err)}")

        if state_manager.first_run:
            t = threading.Thread(target=_display_info, args=(recorder_service,), daemon=True)
            t.start()
            t2 = threading.Thread(target=_adjust_max_request, args=(), daemon=True)
            t2.start()
            state_manager.first_run = False

        time.sleep(3)


if __name__ == '__main__':
    main()
