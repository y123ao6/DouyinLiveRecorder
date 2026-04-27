# -*- encoding: utf-8 -*-
import os
import signal
import subprocess
import time
from typing import Dict, List, Optional

from src.utils import logger
from src.utils import Color

color_obj = Color()
_os_type = os.name


def _get_startup_info(system_type: str):
    if system_type == 'nt':
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        startup_info = None
    return startup_info


_OVERSEAS_PLATFORM_HOST = [
    'www.tiktok.com',
    'play.sooplive.co.kr',
    'm.sooplive.co.kr',
    'www.sooplive.com',
    'm.sooplive.com',
    'www.pandalive.co.kr',
    'www.winktv.co.kr',
    'www.flextv.co.kr',
    'www.ttinglive.com',
    'www.popkontv.com',
    'www.twitch.tv',
    'www.liveme.com',
    'www.showroom-live.com',
    'chzzk.naver.com',
    'm.chzzk.naver.com',
    'live.shopee.',
    '.shp.ee',
    'www.youtube.com',
    'youtu.be',
    'www.faceit.com',
]


class FFmpegService:
    def __init__(self):
        self.startup_info = _get_startup_info(_os_type)

    def build_base_command(
        self,
        stream_url: str,
        proxy_address: Optional[str] = None,
        headers: Optional[str] = None,
        record_url: str = '',
        enable_https: bool = False,
        platform: str = '',
    ) -> List[str]:
        rw_timeout = "15000000"
        analyzeduration = "20000000"
        probesize = "10000000"
        bufsize = "8000k"
        max_muxing_queue_size = "1024"

        for pt_host in _OVERSEAS_PLATFORM_HOST:
            if pt_host in record_url:
                rw_timeout = "50000000"
                analyzeduration = "40000000"
                probesize = "20000000"
                bufsize = "15000k"
                max_muxing_queue_size = "2048"
                break

        user_agent = (
            "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 ("
            "KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile "
            "Safari/537.36"
        )

        command = [
            'ffmpeg', "-y",
            "-v", "verbose",
            "-rw_timeout", rw_timeout,
            "-loglevel", "error",
            "-hide_banner",
            "-user_agent", user_agent,
            "-protocol_whitelist", "rtmp,crypto,file,http,https,tcp,tls,udp,rtp,httpproxy",
            "-thread_queue_size", "1024",
            "-analyzeduration", analyzeduration,
            "-probesize", probesize,
            "-fflags", "+discardcorrupt",
            "-re", "-i", stream_url,
            "-bufsize", bufsize,
            "-sn", "-dn",
            "-reconnect_delay_max", "60",
            "-reconnect_streamed", "-reconnect_at_eof",
            "-max_muxing_queue_size", max_muxing_queue_size,
            "-correct_ts_overflow", "1",
            "-avoid_negative_ts", "1"
        ]

        if headers:
            command.insert(11, "-headers")
            command.insert(12, headers)

        if proxy_address:
            command.insert(1, "-http_proxy")
            command.insert(2, proxy_address)

        return command

    def build_audio_command(
        self,
        save_type: str,
        split_video: bool,
        split_time: str,
        save_file_path: str,
    ) -> List[str]:
        extension = "mp3" if "m4a" not in save_type.lower() else "m4a"

        if split_video:
            if "MP3" in save_type:
                command = [
                    "-map", "0:a",
                    "-c:a", "libmp3lame",
                    "-ab", "320k",
                    "-f", "segment",
                    "-segment_time", split_time,
                    "-reset_timestamps", "1",
                    save_file_path,
                ]
            else:
                command = [
                    "-map", "0:a",
                    "-c:a", "aac",
                    "-bsf:a", "aac_adtstoasc",
                    "-ab", "320k",
                    "-f", "segment",
                    "-segment_time", split_time,
                    "-segment_format", 'mpegts',
                    "-reset_timestamps", "1",
                    save_file_path,
                ]
        else:
            if "MP3" in save_type:
                command = [
                    "-map", "0:a",
                    "-c:a", "libmp3lame",
                    "-ab", "320k",
                    save_file_path,
                ]
            else:
                command = [
                    "-map", "0:a",
                    "-c:a", "aac",
                    "-bsf:a", "aac_adtstoasc",
                    "-ab", "320k",
                    "-movflags", "+faststart",
                    save_file_path,
                ]

        return command

    def build_flv_command(
        self,
        split_video: bool,
        split_time: str,
        save_file_path: str,
    ) -> List[str]:
        if split_video:
            command = [
                "-map", "0",
                "-c:v", "copy",
                "-c:a", "copy",
                "-bsf:a", "aac_adtstoasc",
                "-f", "segment",
                "-segment_time", split_time,
                "-segment_format", "flv",
                "-reset_timestamps", "1",
                save_file_path
            ]
        else:
            command = [
                "-map", "0",
                "-c:v", "copy",
                "-c:a", "copy",
                "-bsf:a", "aac_adtstoasc",
                "-f", "flv",
                "{path}".format(path=save_file_path),
            ]
        return command

    def build_mkv_command(
        self,
        split_video: bool,
        split_time: str,
        save_file_path: str,
    ) -> List[str]:
        if split_video:
            command = [
                "-flags", "global_header",
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0",
                "-f", "segment",
                "-segment_time", split_time,
                "-segment_format", "matroska",
                "-reset_timestamps", "1",
                save_file_path,
            ]
        else:
            command = [
                "-flags", "global_header",
                "-map", "0",
                "-c:v", "copy",
                "-c:a", "copy",
                "-f", "matroska",
                "{path}".format(path=save_file_path),
            ]
        return command

    def build_mp4_command(
        self,
        split_video: bool,
        split_time: str,
        save_file_path: str,
    ) -> List[str]:
        if split_video:
            command = [
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0",
                "-f", "segment",
                "-segment_time", split_time,
                "-segment_format", "mp4",
                "-reset_timestamps", "1",
                "-movflags", "+frag_keyframe+empty_moov",
                save_file_path,
            ]
        else:
            command = [
                "-map", "0",
                "-c:v", "copy",
                "-c:a", "copy",
                "-f", "mp4",
                save_file_path,
            ]
        return command

    def build_ts_command(
        self,
        split_video: bool,
        split_time: str,
        save_file_path: str,
    ) -> List[str]:
        if split_video:
            command = [
                "-c:v", "copy",
                "-c:a", "copy",
                "-map", "0",
                "-f", "segment",
                "-segment_time", split_time,
                "-segment_format", 'mpegts',
                "-reset_timestamps", "1",
                save_file_path,
            ]
        else:
            command = [
                "-c:v", "copy",
                "-c:a", "copy",
                "-map", "0",
                "-f", "mpegts",
                save_file_path,
            ]
        return command

    def start_process(
        self,
        ffmpeg_command: List[str],
    ) -> subprocess.Popen:
        process = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            startupinfo=self.startup_info
        )
        return process

    def stop_process(self, process: subprocess.Popen) -> None:
        if os.name == 'nt':
            if process.stdin:
                process.stdin.write(b'q')
                process.stdin.close()
        else:
            process.send_signal(signal.SIGINT)
        process.wait()

    @staticmethod
    def converts_mp4(converts_file_path: str, is_original_delete: bool = True,
                     converts_to_h264: bool = False) -> None:
        try:
            if os.path.exists(converts_file_path) and os.path.getsize(converts_file_path) > 0:
                if converts_to_h264:
                    color_obj.print_colored("正在转码为MP4格式并重新编码为h264\n", color_obj.YELLOW)
                    ffmpeg_command = [
                        "ffmpeg", "-i", converts_file_path,
                        "-c:v", "libx264",
                        "-preset", "veryfast",
                        "-crf", "23",
                        "-vf", "format=yuv420p",
                        "-c:a", "copy",
                        "-f", "mp4", converts_file_path.rsplit('.', maxsplit=1)[0] + ".mp4",
                    ]
                else:
                    color_obj.print_colored("正在转码为MP4格式\n", color_obj.YELLOW)
                    ffmpeg_command = [
                        "ffmpeg", "-i", converts_file_path,
                        "-c:v", "copy",
                        "-c:a", "copy",
                        "-f", "mp4", converts_file_path.rsplit('.', maxsplit=1)[0] + ".mp4",
                    ]
                _output = subprocess.check_output(
                    ffmpeg_command, stderr=subprocess.STDOUT,
                    startupinfo=_get_startup_info(_os_type)
                )
                if is_original_delete:
                    time.sleep(1)
                    if os.path.exists(converts_file_path):
                        os.remove(converts_file_path)
        except subprocess.CalledProcessError as e:
            logger.error(f'Error occurred during conversion: {e}')
        except Exception as e:
            logger.error(f'An unknown error occurred: {e}')

    @staticmethod
    def converts_m4a(converts_file_path: str, is_original_delete: bool = True) -> None:
        try:
            if os.path.exists(converts_file_path) and os.path.getsize(converts_file_path) > 0:
                _output = subprocess.check_output([
                    "ffmpeg", "-i", converts_file_path,
                    "-n", "-vn",
                    "-c:a", "aac", "-bsf:a", "aac_adtstoasc", "-ab", "320k",
                    converts_file_path.rsplit('.', maxsplit=1)[0] + ".m4a",
                ], stderr=subprocess.STDOUT, startupinfo=_get_startup_info(_os_type))
                if is_original_delete:
                    time.sleep(1)
                    if os.path.exists(converts_file_path):
                        os.remove(converts_file_path)
        except subprocess.CalledProcessError as e:
            logger.error(f'Error occurred during conversion: {e}')
        except Exception as e:
            logger.error(f'An unknown error occurred: {e}')

    @staticmethod
    def segment_video(
        converts_file_path: str,
        segment_save_file_path: str,
        segment_format: str,
        segment_time: str,
        is_original_delete: bool = True,
    ) -> None:
        try:
            if os.path.exists(converts_file_path) and os.path.getsize(converts_file_path) > 0:
                ffmpeg_command = [
                    "ffmpeg",
                    "-i", converts_file_path,
                    "-c:v", "copy",
                    "-c:a", "copy",
                    "-map", "0",
                    "-f", "segment",
                    "-segment_time", segment_time,
                    "-segment_format", segment_format,
                    "-reset_timestamps", "1",
                    "-movflags", "+frag_keyframe+empty_moov",
                    segment_save_file_path,
                ]
                _output = subprocess.check_output(
                    ffmpeg_command, stderr=subprocess.STDOUT,
                    startupinfo=_get_startup_info(_os_type)
                )
                if is_original_delete:
                    time.sleep(1)
                    if os.path.exists(converts_file_path):
                        os.remove(converts_file_path)
        except subprocess.CalledProcessError as e:
            logger.error(f'Error occurred during conversion: {e}')
        except Exception as e:
            logger.error(f'An unknown error occurred: {e}')
