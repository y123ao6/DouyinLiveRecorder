# -*- coding: utf-8 -*-
import datetime
import os
import subprocess
import sys
import time

from loguru import logger

import i18n
import main
from src import utils

# 视频后处理（独立模块）：FFmpeg 分段 / 转封装 / 转码 / 时间字幕生成
#
# 说明：
# - 大部分函数仅依赖文件级参数与 ffmpeg 命令，不触碰 main 全局状态；
# - 仅 converts_mp4 / generate_subtitles 需要读取 main 的少量配置全局变量
#   （converts_to_h264 / color_obj / text_encoding / recording / record_state_lock），
#   通过 `import main` 在运行时惰性读取，避免循环导入与 __main__ 二次执行问题。


# Windows 下 subprocess.STARTUPINFO 仅存在于 Windows typeshed，Linux/macOS 上 mypy 无法解析该名字。
# 返回值类型用 object 而非具体 STARTUPINFO：该符号在非 Windows typeshed 中不存在，无法作为跨平台类型引用；
# 调用方仅将其透传给 subprocess 的 startupinfo 参数（typeshed 中本就是宽松类型），object | None 不损失实际类型安全。
# 按 system_type（os.name 取值）返回子进程启动参数：为 "nt" 时返回隐藏窗口的 STARTUPINFO，其他平台返回 None
def get_startup_info(system_type: str) -> object | None:
    # 获取平台启动信息（Windows 隐藏控制台窗口）。
    # 运行时只在 Windows（os.name == "nt"）构造 STARTUPINFO，其他平台恒返回 None；
    # mypy 依据 sys.platform 字面量分支跳过非当前平台代码，从而通过跨平台类型检查。
    if system_type != "nt":
        return None
    if sys.platform == "win32":
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return startup_info
    return None


# 同步执行 ffmpeg 命令 command（超过 timeout 秒则杀掉子进程并抛 TimeoutExpired）；
# 返回合并后的输出文本，返回码非 0 时抛 CalledProcessError
def _run_ffmpeg_checked(command: list[str], timeout: int = 600) -> str:
    # 执行 ffmpeg 命令并捕获输出；超时则终止子进程，防止转码卡死永久挂住线程。
    with subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=get_startup_info(main.os_type)
    ) as process:
        try:
            out, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            out, _ = process.communicate()
            raise
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command, output=out)
        return out.decode("utf-8", errors="replace")


# 用 ffmpeg 把 converts_file_path 按 segment_time 秒切分为 segment_format 容器，
# 输出到 segment_save_file_path（含编号占位符的模板）；is_original_delete=True 时删除源文件，无返回值
def segment_video(
    converts_file_path: str,
    segment_save_file_path: str,
    segment_format: str,
    segment_time: str,
    is_original_delete: bool = True,
) -> None:
    # 使用 FFmpeg 对视频进行分段录制
    try:
        if os.path.exists(converts_file_path) and os.path.getsize(converts_file_path) > 0:
            ffmpeg_command = [
                "ffmpeg",
                "-i",
                converts_file_path,
                "-c:v",
                "copy",
                "-c:a",
                "copy",
                "-map",
                "0",
                "-f",
                "segment",
                "-segment_time",
                segment_time,
                "-segment_format",
                segment_format,
                "-reset_timestamps",
                "1",
                "-movflags",
                "+frag_keyframe+empty_moov",
                segment_save_file_path,
            ]
            _ = _run_ffmpeg_checked(ffmpeg_command)
            if is_original_delete:
                time.sleep(1)
                if os.path.exists(converts_file_path):
                    os.remove(converts_file_path)
    except subprocess.TimeoutExpired as e:
        # 与「转码失败」「未知失败」区分：超时表明 ffmpeg 卡死，须告警用户主动排查；
        # 此前被 except Exception 兜底为「unknown error」丢失语义。
        logger.error(i18n.tr("ffmpeg 转封装/转码超时（{type_name}）: {e}", type_name=type(e).__name__, e=e))
    except subprocess.CalledProcessError as e:
        logger.error(i18n.tr("Error occurred during conversion: {e}", e=e))
    except Exception as e:
        logger.error(i18n.tr("An unknown error occurred: {e}", e=e))


# 把 converts_file_path 转封装为同名 .mp4（全局 converts_to_h264 开启时重编码为 h264）；
# is_original_delete=True 时删除源文件，无返回值
def converts_mp4(converts_file_path: str, is_original_delete: bool = True) -> None:
    # 将录制文件转换为 MP4 格式
    try:
        if os.path.exists(converts_file_path) and os.path.getsize(converts_file_path) > 0:
            if main.converts_to_h264:
                main.color_obj.print_colored("正在转码为MP4格式并重新编码为h264\n", main.color_obj.YELLOW)
                # 2026-09-12 审查 6.1：补 `-n`（覆盖同名 .mp4 不询问）。
                # 原无 `-n`：输出已存在时 ffmpeg 写盘前提示 "File 'xxx.mp4' already exists.
                # Overwrite? [y/N]"（无 stdin → read EOF → 等同 N），communicate(timeout=600)
                # 走满 600s 超时后才被回收。开弹幕 + 分段 + 转码组合下每个分段都触发
                # 一次 600s 挂死，严重占满转码线程。`converts_m4a` 已正确加 `-n`，本函数
                # 与之对齐。
                ffmpeg_command = [
                    "ffmpeg",
                    "-i",
                    converts_file_path,
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "23",
                    "-vf",
                    "format=yuv420p",
                    "-c:a",
                    "copy",
                    "-f",
                    "mp4",
                    "-n",
                    converts_file_path.rsplit(".", maxsplit=1)[0] + ".mp4",
                ]
            else:
                main.color_obj.print_colored("正在转码为MP4格式\n", main.color_obj.YELLOW)
                ffmpeg_command = [
                    "ffmpeg",
                    "-i",
                    converts_file_path,
                    "-c:v",
                    "copy",
                    "-c:a",
                    "copy",
                    "-f",
                    "mp4",
                    "-n",
                    converts_file_path.rsplit(".", maxsplit=1)[0] + ".mp4",
                ]
            _ = _run_ffmpeg_checked(ffmpeg_command)
            if is_original_delete:
                time.sleep(1)
                if os.path.exists(converts_file_path):
                    os.remove(converts_file_path)
    except subprocess.TimeoutExpired as e:
        # 与下两类错误区分：ffmpeg 卡死须告警（与「格式不对」语义不同），
        # 否则被 except Exception 兜底为 unknown error 丢失语义。
        logger.error(i18n.tr("ffmpeg 转 MP4 超时（{type_name}）: {e}", type_name=type(e).__name__, e=e))
    except subprocess.CalledProcessError as e:
        logger.error(i18n.tr("Error occurred during conversion: {e}", e=e))
    except Exception as e:
        logger.error(i18n.tr("An unknown error occurred: {e}", e=e))


# 把 converts_file_path 抽取音轨转为同名 320k .m4a；is_original_delete=True 时删除源文件，无返回值
def converts_m4a(converts_file_path: str, is_original_delete: bool = True) -> None:
    # 将录制文件转换为 M4A 音频格式
    try:
        if os.path.exists(converts_file_path) and os.path.getsize(converts_file_path) > 0:
            m4a_command = [
                "ffmpeg",
                "-i",
                converts_file_path,
                "-n",
                "-vn",
                "-c:a",
                "aac",
                "-bsf:a",
                "aac_adtstoasc",
                "-ab",
                "320k",
                converts_file_path.rsplit(".", maxsplit=1)[0] + ".m4a",
            ]
            _ = _run_ffmpeg_checked(m4a_command)
            if is_original_delete:
                time.sleep(1)
                if os.path.exists(converts_file_path):
                    os.remove(converts_file_path)
    except subprocess.TimeoutExpired as e:
        logger.error(i18n.tr("ffmpeg 抽音频超时（{type_name}）: {e}", type_name=type(e).__name__, e=e))
    except subprocess.CalledProcessError as e:
        logger.error(i18n.tr("Error occurred during conversion: {e}", e=e))
    except Exception as e:
        logger.error(i18n.tr("An unknown error occurred: {e}", e=e))


# 后台逐秒追加写"时间字幕"：record_name 用于判断该房间是否仍在录制（不在则结束），
# ass_filename 为不含扩展名的输出路径前缀，sub_format 为字幕扩展名；无返回值
def generate_subtitles(record_name: str, ass_filename: str, sub_format: str = "srt") -> None:
    # 生成字幕文件（SRT/ASS/VTT 格式）
    index_time = 0
    today = datetime.datetime.now()
    re_datetime = today.strftime("%Y-%m-%d %H:%M:%S")

    # 内部工具：把 seconds 秒转为 "HH:MM:SS" 形式的字符串
    def transform_int_to_time(seconds: int) -> str:
        # 将整数秒数转为时间戳字符串
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    while True:
        index_time += 1
        txt = (
            str(index_time)
            + "\n"
            + transform_int_to_time(index_time)
            + ",000 --> "
            + transform_int_to_time(index_time + 1)
            + ",000"
            + "\n"
            + re_datetime
            + "\n\n"
        )

        with open(f"{ass_filename}.{sub_format.lower()}", "a", encoding=main.text_encoding) as f:
            _ = f.write(txt)

        with main.record_state_lock:
            still_recording = record_name in main.recording
        if not still_recording:
            return
        time.sleep(1)
        today = datetime.datetime.now()
        re_datetime = today.strftime("%Y-%m-%d %H:%M:%S")
