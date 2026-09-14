# -*- coding: utf-8 -*-
import hashlib
import os
import platform
import re
import subprocess
from pathlib import Path

import distro
import requests

# loguru 的 logger 为模块级单例，src.logger 对其做过的配置在此同样生效；
# 直接从此处导入可避免基于 basedpyright 的 "未从 src.logger 导出" 告警。
from loguru import logger
from tqdm import tqdm

import i18n

# 应用根目录复用 src.logger 公开导出的 script_path（等价原私有 _app_root() 的返回值）
from .logger import script_path

# 解压实现与 ffmpeg_install 共用同一份（原先两处逐字重复，见 src/utils.unzip_file）
from .utils import unzip_file

# Node.js 环境自动安装模块 - 跨平台的 Node.js 自动检测和安装功能
#
# 职责：检测 `node` 命令是否可用（check_nodejs_installed），不可用则按平台自动安装
#   （Windows 从 npmmirror 拉 zip 解压；Linux 按发行版走 yum/apt；macOS 走 Homebrew）。
# 安装落点：execute_dir（冻结后指向 _internal/），解压后把 node 目录前置注入 PATH，
#   使同进程后续 `node` 调用直接命中。所有路径最后 `node -v` 校验 returncode==0 才认成功。
# 设计取舍：安装失败只返 False、不抛异常，交由调用方提示用户手动安装，避免中断主程序启动。


current_platform = platform.system()
execute_dir = script_path  # 冻结后指向 _internal/，与 __file__ 定位的资源收敛到同一处
current_env_path = os.environ.get("PATH", "")


# 分块计算文件 SHA256（2026-09-12 审查 H-1）：用于二进制下载完整性校验。
def _sha256_of_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# SHA256 校验/记录一体化（trust-on-first-use，与 ffmpeg_install 同模式）。
_NODE_HASH_SUFFIX = ".sha256"


def _check_or_record_zip_sha256(zip_path: Path) -> bool:
    hash_file = Path(str(zip_path) + _NODE_HASH_SUFFIX)
    current_hash = _sha256_of_file(zip_path)
    if hash_file.exists():
        try:
            expected = hash_file.read_text(encoding="ascii").strip().lower()
        except OSError as e:
            logger.warning(i18n.tr("读取 SHA256 缓存失败，跳过校验: {e}", e=e))
            return True
        if expected != current_hash:
            logger.error(
                i18n.tr(
                    "Node.js zip SHA256 与上次记录不一致（{expected} vs {actual}）。"
                    "可能 CDN 被篡改或版本变更。请删除 {hash_file} 后重试，或手动下载校验。",
                    expected=expected,
                    actual=current_hash,
                    hash_file=str(hash_file),
                )
            )
            return False
        logger.debug("Node.js SHA256 校验通过")
        return True
    try:
        hash_file.write_text(current_hash, encoding="ascii")
        logger.debug(i18n.tr("首次下载 Node.js SHA256 已记录：{current_hash}", current_hash=current_hash))
    except OSError as e:
        logger.warning(i18n.tr("写入 SHA256 缓存失败（不影响本次安装）: {e}", e=e))
    return True


def install_nodejs_windows() -> bool:
    # 在 Windows 系统上安装 Node.js，从 npmmirror 下载最新稳定版
    try:
        logger.warning("Node.js is not installed.")
        logger.debug("Installing the stable version of Node.js for Windows...")
        # 两处下载响应均以 with 管理（页面 + zip 流式下载），关闭连接不泄漏
        # （与 ffmpeg_install 的写法保持一致）
        with requests.get("https://nodejs.cn/download/", timeout=30) as response:
            if response.status_code != 200:
                logger.error("Failed to retrieve the Node.js version page")
                return False
            # 从 nodejs.cn 下载页正则抠出 npmmirror 镜像直链；该页面 HTML 结构一旦变动，match 为空即安装失败，
            # 依赖上游文案稳定（魔改字符串来源）。
            match = re.search("https://npmmirror.com/mirrors/node/(v.*?)/node-(v.*?)-x64.msi", response.text)
        if not match:
            logger.error("Failed to retrieve the download URL for the latest version of Node.js...")
            return False
        version = match.group(1)
        # 2026-09-12 审查（低危）：原以 machine 是否含 "32" 判架构——
        # Windows on ARM 的 machine 为 "ARM64"（不含 "32"）会被误判成 x64，
        # 下载 x64 构建在 ARM 机器上无法运行（且错误表现为「装完仍找不到 node」，
        # 极难归因）。改为显式识别 arm64，其余按位宽回落。
        _machine = platform.machine().upper()
        if "ARM" in _machine or "AARCH" in _machine:
            system_bit = "arm64"
        elif "32" in _machine or "86" in _machine and "64" not in _machine:
            system_bit = "x86"
        else:
            system_bit = "x64"
        url = f"https://npmmirror.com/mirrors/node/{version}/node-{version}-win-{system_bit}.zip"

        full_file_name = url.rsplit("/", maxsplit=1)[-1]
        zip_file_path = Path(execute_dir) / full_file_name

        if Path(zip_file_path).exists():
            logger.debug("Node.js installation file already exists, start install...")
        else:
            with requests.get(url, stream=True, timeout=30) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("Content-Length", 0))
                block_size = 1024

                with tqdm(
                    total=total_size, unit="B", unit_scale=True, ncols=100, desc=f"Downloading Node.js ({version})"
                ) as t:
                    with open(zip_file_path, "wb") as f:
                        for data in response.iter_content(block_size):
                            _ = t.update(len(data))
                            _ = f.write(data)

        # H-1 修复：SHA256 校验/记录（trust-on-first-use，与 ffmpeg_install 同模式）
        if not _check_or_record_zip_sha256(zip_file_path):
            try:
                zip_file_path.unlink()
            except OSError:
                pass
            return False

        # 解压到 execute_dir；zip 内顶层目录名为 node-vX.Y.Z-win-x64，提取后整体改名为 "node" 目录以便固定 PATH 引用。
        unzip_file(zip_file_path, execute_dir)
        extract_dir_path = str(zip_file_path).rsplit(".", maxsplit=1)[0]
        new_extract_dir_path = Path(execute_dir) / "node"
        # 仅当解压出的原目录存在、且目标 "node" 目录尚不存在时才重命名；已存在则走下方验证分支（避免覆盖/重复）。
        if Path(extract_dir_path).exists() and not Path(new_extract_dir_path).exists():
            os.rename(extract_dir_path, new_extract_dir_path)
            os.environ["PATH"] = os.path.join(execute_dir, "node") + os.pathsep + current_env_path
            result = subprocess.run(["node", "-v"], capture_output=True)
            if result.returncode == 0:
                logger.debug("Node.js installation was successful. Restart for changes to take effect")
                return True
            else:
                logger.debug("Node.js installation failed")
                return False
        elif Path(new_extract_dir_path).exists():
            # 已有安装目录，验证可用性
            result = subprocess.run(["node", "-v"], capture_output=True)
            if result.returncode == 0:
                return True
            logger.debug("Node.js directory exists but not working")
            return False
        return False

    except Exception as e:
        logger.error(i18n.tr("type: {type_name}, Node.js installation failed {e}", type_name=type(e).__name__, e=e))
        return False


def install_nodejs_centos() -> bool:
    # 在 CentOS/RHEL 系统上通过 yum 安装 Node.js
    try:
        logger.warning("Node.js is not installed.")
        logger.debug("Installing the latest version of Node.js for CentOS...")
        result = subprocess.run(["yum", "install", "-y", "epel-release"], capture_output=True)
        if result.returncode != 0:
            logger.error("Failed to install EPEL repository")
            return False

        result = subprocess.run(["yum", "install", "-y", "nodejs"], capture_output=True)
        if result.returncode == 0:
            logger.debug("Node.js installation was successful. Restart for changes to take effect.")
            return True
        else:
            logger.error("Node.js installation failed")
            return False

    except Exception as e:
        logger.error(i18n.tr("type: {type_name}, Node.js installation failed {e}", type_name=type(e).__name__, e=e))
        return False


def install_nodejs_ubuntu() -> bool:
    # 在 Ubuntu/Debian 系统上通过 apt 安装 Node.js
    # Ubuntu/Debian：直接 apt 装 nodejs（未先 apt update，依赖已就新的包索引；装失败即返 False 提示手动）。
    try:
        logger.warning("Node.js is not installed.")
        logger.debug("Installing the latest version of Node.js for Ubuntu...")
        install_command = ["apt", "install", "-y", "nodejs"]
        result = subprocess.run(install_command, capture_output=True)
        if result.returncode == 0:
            logger.debug("Node.js installation was successful. Restart for changes to take effect.")
            return True
        else:
            logger.error("Node.js installation failed")
            return False
    except Exception as e:
        logger.error(i18n.tr("type: {type_name}, Node.js installation failed, {e}", type_name=type(e).__name__, e=e))
        return False


def install_nodejs_mac() -> bool:
    # 在 macOS 系统上通过 Homebrew 安装 Node.js
    logger.warning("Node.js is not installed.")
    logger.debug("Installing the latest version of Node.js for macOS...")
    try:
        result = subprocess.run(["brew", "install", "node"], capture_output=True)
        if result.returncode == 0:
            logger.debug("Node.js installation was successful. Restart for changes to take effect.")
            return True
        else:
            logger.error("Node.js installation failed")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(i18n.tr("Failed to install Node.js using Homebrew. {e}", e=e))
        logger.error("Please install Node.js manually or check your Homebrew installation.")
        return False
    except Exception as e:
        logger.error(i18n.tr("An unexpected error occurred: {e}", e=e))
        return False


def get_package_manager() -> str:
    # 检测 Linux 发行版类型，返回包管理器标识
    # distro.id() 为小写发行版标识；仅上述 RHEL 系走 yum，其余（含 alpine/suse/arch 等）一律归 DBS(apt)。
    # 对无 apt 的发行版最终会 apt 不存在而失败，需用户手动安装——列表即"支持的包管理器白名单"。
    # 仅上述 RHEL 系发行版走 yum；其余（含 alpine/suse/arch 等无 apt 的）一律归 DBS，最终会因 apt 缺失而失败，需用户手动。
    dist_id = distro.id()
    if dist_id in ["centos", "fedora", "rhel", "amzn", "oracle", "scientific", "opencloudos", "alinux"]:
        return "RHS"
    else:
        return "DBS"


def install_nodejs() -> bool:
    # 跨平台安装 Node.js 的主入口函数
    if current_platform == "Windows":
        return install_nodejs_windows()
    elif current_platform == "Linux":
        os_type = get_package_manager()
        if os_type == "RHS":
            return install_nodejs_centos()
        else:
            return install_nodejs_ubuntu()
    elif current_platform == "Darwin":
        return install_nodejs_mac()
    else:
        logger.debug(
            i18n.tr(
                "Node.js auto installation is not supported on this platform: {current_platform}. Please install Node.js manually.",
                current_platform=current_platform,
            )
        )
        return False


def check_nodejs_installed() -> bool:
    # 仅校验 `node` 命令存在即视为已安装；不检查 npm。若 Node 存在但 npm 缺失，
    # 依赖 npm 的下游功能仍会失败，此处不感知（false positive）。
    try:
        result = subprocess.run(["node", "-v"], capture_output=True)
        version = result.stdout.strip()
        if result.returncode == 0 and version:
            return True
    # 命令不存在（FileNotFoundError）即视为未安装、静默返 False 触发自动安装；其它异常也吞掉返 False。
    except FileNotFoundError:
        pass
    return False


def check_node() -> bool:
    # 检查并确保 Node.js 已安装，未安装则自动安装
    if not check_nodejs_installed():
        return install_nodejs()
    return True
