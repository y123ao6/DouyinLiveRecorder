# -*- encoding: utf-8 -*-

"""
Author: Hmily
GitHub: https://github.com/ihmily
Date: 2023-07-15 23:15:00
Update: 2025-02-06 02:28:00
Copyright (c) 2023-2025 by Hmily, All Rights Reserved.
Function: Get live stream data.
"""
import base64
import hashlib
import json
import time
import random
import re
import urllib.parse
from .utils import trace_error_decorator
from .spider import (
    get_douyu_stream_data, get_bilibili_stream_data
)
from .http_clients.async_http import get_response_status

QUALITY_MAPPING = {"OD": 0, "BD": 0, "UHD": 1, "HD": 2, "SD": 3, "LD": 4}
QUALITY_MAPPING_BIT = {'OD': 99999, 'BD': 4000, 'UHD': 2000, 'HD': 1000, 'SD': 800, 'LD': 600}
DEFAULT_QUALITY = "OD"

_HUYA_SDK_VERSION = 2403051612
_HUYA_PARAMS_T = 100
_HUYA_UUID_MODULO = 4294967295
_HUYA_UID_MIN = 1400000000000
_HUYA_UID_MAX = 1400009999999
_HUYA_TIME_OFFSET_MS = 110624


def _pad_list(url_list: list, min_length: int = 5) -> list:
    if not url_list:
        return url_list
    padded = list(url_list)
    while len(padded) < min_length:
        padded.append(padded[-1])
    return padded


def get_quality_index(quality) -> tuple[str, int]:
    if not quality:
        return DEFAULT_QUALITY, QUALITY_MAPPING[DEFAULT_QUALITY]

    quality_str = str(quality).upper()
    if quality_str.isdigit():
        quality_int = int(quality_str)
        keys = list(QUALITY_MAPPING.keys())
        if quality_int >= len(keys):
            quality_int = quality_int % len(keys)
        quality_str = keys[quality_int]
    if quality_str not in QUALITY_MAPPING:
        quality_str = DEFAULT_QUALITY
    return quality_str, QUALITY_MAPPING[quality_str]


def _fallback_quality_index(quality_index: int, list_len: int) -> int:
    if quality_index < list_len - 1:
        return quality_index + 1
    return max(0, quality_index - 1)


def _build_offline_result(anchor_name, **extra) -> dict:
    result = {
        "anchor_name": anchor_name,
        "is_live": False,
    }
    result.update(extra)
    return result


@trace_error_decorator
async def get_douyin_stream_url(json_data: dict, video_quality: str | None = None, proxy_addr: str | None = None) -> dict:
    anchor_name = json_data.get('anchor_name')

    result = {
        "anchor_name": anchor_name,
        "is_live": False,
    }

    status = json_data.get("status", 4)

    if status == 2:
        stream_url = json_data.get('stream_url')
        if not stream_url:
            return result
        flv_url_dict = stream_url.get('flv_pull_url', {})
        flv_url_list: list = list(flv_url_dict.values())
        m3u8_url_dict = stream_url.get('hls_pull_url_map', {})
        m3u8_url_list: list = list(m3u8_url_dict.values())

        if not flv_url_list and not m3u8_url_list:
            return result

        flv_url_list = _pad_list(flv_url_list)
        m3u8_url_list = _pad_list(m3u8_url_list)

        video_quality, quality_index = get_quality_index(video_quality)
        quality_index = min(quality_index, len(m3u8_url_list) - 1, len(flv_url_list) - 1)
        m3u8_url = m3u8_url_list[quality_index]
        flv_url = flv_url_list[quality_index]
        ok = await get_response_status(url=m3u8_url, proxy_addr=proxy_addr)
        if not ok:
            index = _fallback_quality_index(quality_index, min(len(m3u8_url_list), len(flv_url_list)))
            m3u8_url = m3u8_url_list[index]
            flv_url = flv_url_list[index]
        result |= {
            'is_live': True,
            'title': json_data.get('title', ''),
            'quality': video_quality,
            'm3u8_url': m3u8_url,
            'flv_url': flv_url,
            'record_url': m3u8_url or flv_url,
        }
    return result


@trace_error_decorator
async def get_tiktok_stream_url(json_data: dict | None, video_quality: str | None = None, proxy_addr: str | None = None) -> dict:
    if not json_data:
        return {"anchor_name": None, "is_live": False}

    def get_video_quality_url(stream, q_key) -> list:
        play_list = []
        for key in stream:
            url_info = stream[key]['main']
            sdk_params = url_info['sdk_params']
            sdk_params = json.loads(sdk_params)
            vbitrate = int(sdk_params['vbitrate'])
            v_codec = sdk_params.get('VCodec', '')

            play_url = ''
            if url_info.get(q_key):
                if url_info[q_key].endswith(".flv") or url_info[q_key].endswith(".m3u8"):
                    play_url = url_info[q_key] + '?codec=' + v_codec
                else:
                    play_url = url_info[q_key] + '&codec=' + v_codec

            resolution = sdk_params['resolution']
            if vbitrate != 0 and resolution:
                width, height = map(int, resolution.split('x'))
                play_list.append({'url': play_url, 'vbitrate': vbitrate, 'resolution': (width, height)})

        play_list.sort(key=lambda x: (-x['vbitrate'], -x['resolution'][0], -x['resolution'][1]))
        return play_list

    live_room = json_data['LiveRoom']['liveRoomUserInfo']
    user = live_room['user']
    anchor_name = f"{user['nickname']}-{user['uniqueId']}"
    status = user.get("status", 4)

    result = {
        "anchor_name": anchor_name,
        "is_live": False,
    }

    if status == 2:
        stream_data = live_room['liveRoom']['streamData']['pull_data']['stream_data']
        stream_data = json.loads(stream_data).get('data', {})
        flv_url_list = get_video_quality_url(stream_data, 'flv')
        m3u8_url_list = get_video_quality_url(stream_data, 'hls')

        flv_url_list = _pad_list(flv_url_list)
        m3u8_url_list = _pad_list(m3u8_url_list)
        video_quality, quality_index = get_quality_index(video_quality)
        quality_index = min(quality_index, len(flv_url_list) - 1, len(m3u8_url_list) - 1)
        flv_dict: dict = flv_url_list[quality_index]
        m3u8_dict: dict = m3u8_url_list[quality_index]

        check_url = m3u8_dict.get('url', '') or flv_dict.get('url', '')
        ok = await get_response_status(url=check_url, proxy_addr=proxy_addr, http2=False)

        if not ok:
            index = _fallback_quality_index(quality_index, min(len(flv_url_list), len(m3u8_url_list)))
            flv_dict = flv_url_list[index]
            m3u8_dict = m3u8_url_list[index]

        flv_url = flv_dict.get('url', '')
        m3u8_url = m3u8_dict.get('url', '')
        result |= {
            'is_live': True,
            'title': live_room['liveRoom'].get('title', ''),
            'quality': video_quality,
            'm3u8_url': m3u8_url,
            'flv_url': flv_url,
            'record_url': m3u8_url or flv_url,
        }
    return result


@trace_error_decorator
async def get_kuaishou_stream_url(json_data: dict, video_quality: str | None = None) -> dict:
    anchor_name = json_data.get('anchor_name', '')

    if json_data.get('type') == 1 and not json_data.get("is_live"):
        return _build_offline_result(anchor_name)

    live_status = json_data.get('is_live', False)

    result = {
        "type": 2,
        "anchor_name": anchor_name,
        "is_live": live_status,
    }

    if not live_status:
        return result

    video_quality, quality_index = get_quality_index(video_quality)

    if 'm3u8_url_list' in json_data and json_data['m3u8_url_list']:
        m3u8_url_list = json_data['m3u8_url_list'][::-1]
        m3u8_url_list = _pad_list(m3u8_url_list)
        safe_index = min(quality_index, len(m3u8_url_list) - 1)
        m3u8_url = m3u8_url_list[safe_index].get('url', '')
        result['m3u8_url'] = m3u8_url

    if 'flv_url_list' in json_data and json_data['flv_url_list']:
        flv_url_list = json_data['flv_url_list']
        if flv_url_list and 'bitrate' in flv_url_list[0]:
            flv_url_list = sorted(flv_url_list, key=lambda x: x['bitrate'], reverse=True)
            quality_str = str(video_quality).upper()
            if quality_str.isdigit():
                video_quality, quality_index_bitrate_value = list(QUALITY_MAPPING_BIT.items())[int(quality_str)]
            else:
                quality_index_bitrate_value = QUALITY_MAPPING_BIT.get(quality_str, 99999)
                video_quality = quality_str
            quality_index = next(
                (i for i, x in enumerate(flv_url_list) if x['bitrate'] <= quality_index_bitrate_value), None)
            if quality_index is None:
                quality_index = len(flv_url_list) - 1
            flv_url = flv_url_list[quality_index].get('url', '')

            result['flv_url'] = flv_url
            result['record_url'] = flv_url
        else:
            flv_url_list = json_data['flv_url_list'][::-1]
            flv_url_list = _pad_list(flv_url_list)
            safe_index = min(quality_index, len(flv_url_list) - 1)
            flv_url = flv_url_list[safe_index].get('url', '')
            result |= {'flv_url': flv_url, 'record_url': flv_url}

    result['is_live'] = True
    result['quality'] = video_quality

    if 'record_url' not in result:
        result['record_url'] = result.get('m3u8_url') or result.get('flv_url', '')

    return result


def _build_huya_anti_code(old_anti_code: str, stream_name: str) -> str:
    params_t = _HUYA_PARAMS_T
    sdk_version = _HUYA_SDK_VERSION

    t13 = int(time.time()) * 1000
    sdk_sid = t13

    init_uuid = (int(t13 % 10 ** 10 * 1000) + int(1000 * random.random())) % _HUYA_UUID_MODULO
    uid = random.randint(_HUYA_UID_MIN, _HUYA_UID_MAX)
    seq_id = uid + sdk_sid

    target_unix_time = (t13 + _HUYA_TIME_OFFSET_MS) // 1000
    ws_time = f"{target_unix_time:x}".lower()

    url_query = urllib.parse.parse_qs(old_anti_code)
    fm_value = url_query.get('fm', [''])[0]
    ctype_value = url_query.get('ctype', [''])[0]
    fs_value = url_query.get('fs', [''])[0]

    if not fm_value:
        return old_anti_code

    ws_secret_pf = base64.b64decode(urllib.parse.unquote(fm_value).encode()).decode().split("_")[0]
    ws_secret_hash = hashlib.md5(f'{seq_id}|{ctype_value}|{params_t}'.encode()).hexdigest()
    ws_secret = f'{ws_secret_pf}_{uid}_{stream_name}_{ws_secret_hash}_{ws_time}'
    ws_secret_md5 = hashlib.md5(ws_secret.encode()).hexdigest()

    anti_code = (
        f'wsSecret={ws_secret_md5}&wsTime={ws_time}&seqid={seq_id}&ctype={ctype_value}&ver=1'
        f'&fs={fs_value}&uuid={init_uuid}&u={uid}&t={params_t}&sv={sdk_version}'
        f'&sdk_sid={sdk_sid}&codec=264'
    )
    return anti_code


@trace_error_decorator
async def get_huya_stream_url(json_data: dict, video_quality: str | None = None) -> dict:
    game_live_info = json_data['data'][0]['gameLiveInfo']
    live_title = game_live_info.get('introduction', '')
    stream_info_list = json_data['data'][0].get('gameStreamInfoList', [])
    anchor_name = game_live_info.get('nick', '')

    result = {
        "anchor_name": anchor_name,
        "is_live": False,
    }

    if not stream_info_list:
        return result

    select_cdn = stream_info_list[0]
    flv_url = select_cdn.get('sFlvUrl', '')
    stream_name = select_cdn.get('sStreamName', '')
    flv_url_suffix = select_cdn.get('sFlvUrlSuffix', '')
    hls_url = select_cdn.get('sHlsUrl', '')
    hls_url_suffix = select_cdn.get('sHlsUrlSuffix', '')
    flv_anti_code = select_cdn.get('sFlvAntiCode', '')

    if not flv_anti_code:
        return result

    new_anti_code = _build_huya_anti_code(flv_anti_code, stream_name)
    flv_url = f'{flv_url}/{stream_name}.{flv_url_suffix}?{new_anti_code}&ratio='
    m3u8_url = f'{hls_url}/{stream_name}.{hls_url_suffix}?{new_anti_code}&ratio='

    quality_list = flv_anti_code.split('&exsphd=')
    if len(quality_list) > 1 and video_quality not in ["OD", "BD"]:
        pattern = r"(?<=264_)\d+"
        quality_list = list(re.findall(pattern, quality_list[1]))[::-1]
        quality_list = _pad_list(quality_list)

        video_quality_options = {
            "UHD": quality_list[0],
            "HD": quality_list[1],
            "SD": quality_list[2],
            "LD": quality_list[3]
        }

        if video_quality not in video_quality_options:
            raise ValueError(
                f"Invalid video quality. Available options are: {', '.join(video_quality_options.keys())}")

        flv_url = flv_url + str(video_quality_options[video_quality])
        m3u8_url = m3u8_url + str(video_quality_options[video_quality])

    result |= {
        'is_live': True,
        'title': live_title,
        'quality': video_quality,
        'm3u8_url': m3u8_url,
        'flv_url': flv_url,
        'record_url': flv_url or m3u8_url
    }
    return result


@trace_error_decorator
async def get_douyu_stream_url(json_data: dict, video_quality: str | None = None, cookies: str = '',
                               proxy_addr: str | None = None) -> dict:
    anchor_name = json_data.get("anchor_name")
    if not json_data.get("is_live"):
        return _build_offline_result(anchor_name)

    video_quality_options = {
        "OD": '0',
        "BD": '0',
        "UHD": '3',
        "HD": '2',
        "SD": '1',
        "LD": '1'
    }

    rid = str(json_data.get("room_id", ''))
    video_quality, _ = get_quality_index(video_quality)
    rate = video_quality_options.get(video_quality, '0')
    flv_data = await get_douyu_stream_data(rid, rate, cookies=cookies, proxy_addr=proxy_addr)
    rtmp_url = flv_data.get('data', {}).get('rtmp_url', '')
    rtmp_live = flv_data.get('data', {}).get('rtmp_live', '')

    result = {
        "anchor_name": anchor_name,
        "is_live": True,
        "quality": video_quality,
    }
    if rtmp_live:
        flv_url = f'{rtmp_url}/{rtmp_live}'
        result |= {'flv_url': flv_url, 'record_url': flv_url}
    return result


@trace_error_decorator
async def get_yy_stream_url(json_data: dict) -> dict:
    anchor_name = json_data.get('anchor_name', '')
    result = {
        "anchor_name": anchor_name,
        "is_live": False,
    }
    if 'avp_info_res' in json_data:
        stream_line_addr = json_data['avp_info_res'].get('stream_line_addr', {})
        if not stream_line_addr:
            return result
        cdn_info = list(stream_line_addr.values())[0]
        flv_url = cdn_info.get('cdn_info', {}).get('url', '')
        if not flv_url:
            return result
        result |= {
            'is_live': True,
            'title': json_data.get('title', ''),
            'quality': 'OD',
            'flv_url': flv_url,
            'record_url': flv_url
        }
    return result


@trace_error_decorator
async def get_bilibili_stream_url(json_data: dict, video_quality: str | None = None,
                                  proxy_addr: str | None = None, cookies: str = '') -> dict:
    anchor_name = json_data.get("anchor_name")
    if not json_data.get("live_status"):
        return _build_offline_result(anchor_name)

    room_url = json_data.get('room_url', '')

    video_quality_options = {
        "OD": '10000',
        "BD": '400',
        "UHD": '250',
        "HD": '150',
        "SD": '80',
        "LD": '80'
    }

    video_quality, _ = get_quality_index(video_quality)
    select_quality = video_quality_options.get(video_quality, '0')
    play_url = await get_bilibili_stream_data(
        room_url, qn=select_quality, platform='web', proxy_addr=proxy_addr, cookies=cookies)
    return {
        'anchor_name': anchor_name,
        'is_live': True,
        'title': json_data.get('title', ''),
        'quality': video_quality,
        'record_url': play_url
    }


@trace_error_decorator
async def get_netease_stream_url(json_data: dict, video_quality: str | None = None) -> dict:
    anchor_name = json_data.get('anchor_name', '')
    if not json_data.get('is_live'):
        return _build_offline_result(anchor_name)

    m3u8_url = json_data.get('m3u8_url', '')
    flv_url = None
    if json_data.get('stream_list'):
        stream_list = json_data['stream_list'].get('resolution', {})
        order = ['blueray', 'ultra', 'high', 'standard']
        sorted_keys = [key for key in order if key in stream_list]
        sorted_keys = _pad_list(sorted_keys)
        video_quality, quality_index = get_quality_index(video_quality)
        safe_index = min(quality_index, len(sorted_keys) - 1)
        selected_quality = sorted_keys[safe_index]
        flv_url_list = stream_list[selected_quality].get('cdn', {})
        if flv_url_list:
            selected_cdn = list(flv_url_list.keys())[0]
            flv_url = flv_url_list[selected_cdn]

    return {
        "is_live": True,
        "anchor_name": anchor_name,
        "title": json_data.get('title', ''),
        'quality': video_quality,
        "m3u8_url": m3u8_url,
        "flv_url": flv_url,
        "record_url": flv_url or m3u8_url
    }


@trace_error_decorator
async def get_stream_url(json_data: dict, video_quality: str | None = None, url_type: str = 'm3u8', spec: bool = False,
                         hls_extra_key: str | None = None, flv_extra_key: str | None = None) -> dict:
    if not json_data.get('is_live'):
        return _build_offline_result(json_data.get('anchor_name'))

    play_url_list = json_data.get('play_url_list', [])
    play_url_list = _pad_list(play_url_list)

    video_quality, selected_quality = get_quality_index(video_quality)
    safe_quality = min(selected_quality, len(play_url_list) - 1)
    data = {
        "anchor_name": json_data.get('anchor_name'),
        "is_live": True
    }

    def get_url(key):
        play_url = play_url_list[safe_quality]
        return play_url.get(key, play_url) if key else play_url

    if url_type == 'all':
        m3u8_url = get_url(hls_extra_key)
        flv_url = get_url(flv_extra_key)
        data |= {
            "m3u8_url": json_data.get('m3u8_url') if spec else m3u8_url,
            "flv_url": json_data.get('flv_url') if spec else flv_url,
            "record_url": m3u8_url
        }
    elif url_type == 'm3u8':
        m3u8_url = get_url(hls_extra_key)
        data |= {"m3u8_url": json_data.get('m3u8_url') if spec else m3u8_url, "record_url": m3u8_url}
    else:
        flv_url = get_url(flv_extra_key)
        data |= {"flv_url": flv_url, "record_url": flv_url}
    data['title'] = json_data.get('title')
    data['quality'] = video_quality
    return data
