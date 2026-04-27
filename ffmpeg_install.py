# -*- coding: utf-8 -*-

"""
Author: Hmily
GitHub: https://github.com/ihmily
Copyright (c) 2024 by Hmily, All Rights Reserved.
"""

import functools
import os
import re
import subprocess
import sys
import platform
import zipfile
from pathlib import Path
from typing import Any, Callable

import requests
from tqdm import tqdm
from src.logger import logger

current_platform = platform.system()
execute_dir = os.path.split(os.path.realpath(sys.argv[0]))[0]
current_env_path = os.environ.get('PATH', '')
ffmpeg_path = os.path.join(execute_dir, 'ffmpeg')

_SUBPROCESS_TIMEOUT = 120


def unzip_file(zip_path: str | Path, extract_to: str | Path, delete: bool = True) -> None:
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    if delete and os.path.exists(zip_path):
        os.remove(zip_path)


def get_lanzou_download_link(url: str, password: str | None = None) -> str | None:
    try:
        headers = {
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Origin': 'https://wweb.lanzouv.com',
            'Referer': 'https://wweb.lanzouv.com/iXncv0dly6mh',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
        }
        response = requests.get(url, headers=headers, timeout=30)
        sign_match = re.search("var skdklds = '(.*?)';", response.text)
        if not sign_match:
            logger.error("Failed to extract sign from lanzou page")
            return None
        sign = sign_match.group(1)
        data = {
            'action': 'downprocess',
            'sign': sign,
            'p': password,
            'kd': '1',
        }
        response = requests.post('https://wweb.lanzouv.com/ajaxm.php', headers=headers, data=data, timeout=30)
        json_data = response.json()
        download_url = json_data['dom'] + "/file/" + json_data['url']
        response = requests.get(download_url, headers=headers, timeout=30)
        return response.url
    except Exception as e:
        logger.error(f"Failed to obtain ffmpeg download address. {e}")
        return None


def install_ffmpeg_windows():
    zip_file_path = None
    try:
        logger.warning("ffmpeg is not installed.")
        logger.debug("Installing the latest version of ffmpeg for Windows...")
        ffmpeg_url = get_lanzou_download_link('https://wweb.lanzouv.com/iHAc22ly3r3g', 'eots')
        if ffmpeg_url:
            full_file_name = 'ffmpeg_latest_build_20250124.zip'
            version = 'v20250124'
            zip_file_path = Path(execute_dir) / full_file_name
            if Path(zip_file_path).exists():
                logger.debug("ffmpeg installation file already exists, start install...")
            else:
                response = requests.get(ffmpeg_url, stream=True, timeout=120)
                total_size = int(response.headers.get('Content-Length', 0))
                block_size = 1024

                with tqdm(total=total_size, unit="B", unit_scale=True,
                          ncols=100, desc=f'Downloading ffmpeg ({version})') as t:
                    with open(zip_file_path, 'wb') as f:
                        for data in response.iter_content(block_size):
                            t.update(len(data))
                            f.write(data)

            unzip_file(zip_file_path, execute_dir)
            os.environ['PATH'] = ffmpeg_path + os.pathsep + current_env_path
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=_SUBPROCESS_TIMEOUT)
            if result.returncode == 0:
                logger.debug('ffmpeg installation was successful')
                return True
            else:
                logger.error('ffmpeg installation failed. Please manually install ffmpeg by yourself')
                return False
        else:
            logger.error("Please manually install ffmpeg by yourself")
    except requests.RequestException as e:
        logger.error(f"Network error during ffmpeg download: {e}")
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg version check timed out after installation")
    except Exception as e:
        logger.error(f"type: {type(e).__name__}, ffmpeg installation failed {e}")
    finally:
        if zip_file_path and Path(zip_file_path).exists() and not check_ffmpeg_installed():
            try:
                os.remove(zip_file_path)
                logger.debug("Cleaned up incomplete ffmpeg installation file")
            except OSError:
                pass
    return False


def install_ffmpeg_mac():
    logger.warning("ffmpeg is not installed.")
    logger.debug("Installing the stable version of ffmpeg for macOS...")
    try:
        result = subprocess.run(["brew", "install", "ffmpeg"], capture_output=True, timeout=300)
        if result.returncode == 0:
            logger.debug('ffmpeg installation was successful. Restart for changes to take effect.')
            return True
        else:
            logger.error("ffmpeg installation failed")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install ffmpeg using Homebrew. {e}")
        logger.error("Please install ffmpeg manually or check your Homebrew installation.")
    except subprocess.TimeoutExpired:
        logger.error("Homebrew ffmpeg installation timed out")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return False


def install_ffmpeg_linux():
    is_RHS = True

    try:
        logger.warning("ffmpeg is not installed.")
        logger.debug("Trying to install the stable version of ffmpeg")
        result = subprocess.run(['yum', '-y', 'update'], capture_output=True, timeout=_SUBPROCESS_TIMEOUT)
        if result.returncode != 0:
            logger.error("Failed to update package lists using yum.")
            return False

        result = subprocess.run(['yum', 'install', '-y', 'ffmpeg'], capture_output=True, timeout=_SUBPROCESS_TIMEOUT)
        if result.returncode == 0:
            logger.debug("ffmpeg installation was successful using yum. Restart for changes to take effect.")
            return True
        logger.error(result.stderr.decode('utf-8').strip())
    except FileNotFoundError:
        logger.debug("yum command not found, trying to install using apt...")
        is_RHS = False
    except subprocess.TimeoutExpired:
        logger.error("yum operation timed out")
        return False
    except Exception as e:
        logger.error(f"An error occurred while trying to install ffmpeg using yum: {e}")

    if not is_RHS:
        try:
            logger.debug("Trying to install the stable version of ffmpeg for Linux using apt...")
            result = subprocess.run(['apt', 'update'], capture_output=True, timeout=_SUBPROCESS_TIMEOUT)
            if result.returncode != 0:
                logger.error("Failed to update package lists using apt")
                return False

            result = subprocess.run(['apt', 'install', '-y', 'ffmpeg'], capture_output=True, timeout=_SUBPROCESS_TIMEOUT)
            if result.returncode == 0:
                logger.debug("ffmpeg installation was successful using apt. Restart for changes to take effect.")
                return True
            else:
                logger.error(result.stderr.decode('utf-8').strip())
        except FileNotFoundError:
            logger.error("apt command not found, unable to install ffmpeg. Please manually install ffmpeg by yourself")
        except subprocess.TimeoutExpired:
            logger.error("apt operation timed out")
        except Exception as e:
            logger.error(f"An error occurred while trying to install ffmpeg using apt: {e}")
    logger.error("Manual installation of ffmpeg is required. Please manually install ffmpeg by yourself.")
    return False


def install_ffmpeg() -> bool:
    if current_platform == "Windows":
        return install_ffmpeg_windows()
    elif current_platform == "Linux":
        return install_ffmpeg_linux()
    elif current_platform == "Darwin":
        return install_ffmpeg_mac()
    else:
        logger.debug(f"ffmpeg auto installation is not supported on this platform: {current_platform}. "
                     f"Please install ffmpeg manually.")
    return False


def ensure_ffmpeg_installed(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not check_ffmpeg_installed():
            install_ffmpeg()
        if not check_ffmpeg_installed():
            raise RuntimeError("ffmpeg is not installed.")
        return func(*args, **kwargs)

    return wrapper


def check_ffmpeg_installed() -> bool:
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=10)
        version = result.stdout.strip()
        if result.returncode == 0 and version:
            return True
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg version check timed out. ffmpeg may not be installed correctly.")
    except PermissionError:
        logger.warning("ffmpeg exists but is not executable. Please check file permissions.")
    except OSError as e:
        logger.warning(f"OSError occurred: {e}. ffmpeg may not be installed correctly or is not available in the system PATH.")
        logger.warning("Please delete the ffmpeg and try to download and install again.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return False


def check_ffmpeg() -> bool:
    if not check_ffmpeg_installed():
        return install_ffmpeg()
    return True
