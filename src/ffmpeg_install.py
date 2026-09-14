#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import os
import platform
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import cast

import requests

# loguru 的 logger 为模块级单例，src.logger 对其做过的配置在此同样生效；
# 直接从此处导入可避免基于 basedpyright 的 "未从 src.logger 导出" 告警。
from loguru import logger
from tqdm import tqdm

import i18n

# 应用根目录复用 src.logger 公开导出的 script_path（等价原私有 _app_root() 的返回值）
from src.logger import script_path

# 解压实现与 node_install 共用同一份（原先两处逐字重复，见 src/utils.unzip_file）
from src.utils import unzip_file

# FFmpeg 自动安装模块 - 跨平台 FFmpeg 自动检测与安装
#
# 职责：检测系统是否已安装 ffmpeg（check_ffmpeg_installed），未安装则按平台自动拉取并安装
#   （Windows 官方源 gyan.dev 优先、蓝奏云备用；macOS 走 Homebrew；Linux 走 yum/apt）。
# 安装落点：execute_dir（冻结后指向 _internal/，与运行时资源同目录），装好后把 ffmpeg 目录
#   前置注入 os.environ["PATH"]，使同进程后续 subprocess 调用 `ffmpeg` 能直接命中。
# 校验约定：所有安装路径最后都跑一次 `ffmpeg -version`，returncode==0 才认成功，否则回退下一源/报错。
# 设计取舍：安装失败只返回 False、不抛异常（由调用方决定提示用户手动安装），避免中断主程序启动。


# 全局路径和环境变量
current_platform = platform.system()
execute_dir = script_path  # 冻结后指向 _internal/，与 __file__ 定位的资源收敛到同一处
# 安装时把新 ffmpeg 目录前缀拼回系统原 PATH；运行期 PATH 可能已被修改，先快照原始值避免重复嵌套。
current_env_path = os.environ.get("PATH")
# 安装目标子目录：ffmpeg 可执行文件最终位于 execute_dir/ffmpeg/bin/ffmpeg.exe（官方源）或平铺（蓝奏云）。
ffmpeg_path = os.path.join(execute_dir, "ffmpeg")


# 分块计算文件 SHA256（2026-09-12 审查 H-1）：用于二进制下载完整性校验。
# 单次 read 整个哈希文件对几百 MB 二进制来说会瞬时占用大量内存；分块保持内存恒定。
def _sha256_of_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_valid_zip(path: str | Path) -> bool:
    # 校验本地缓存的压缩包是否完整可用（2026-09-12 审查，低危）：
    # os.path.exists 只能证明文件存在，无法区分「下载完整」与「下载被中断的残缺文件」。
    # zipfile.is_zipfile 会读尾部 End Of Central Directory 记录，残缺包（无 EOCD）
    # 会返回 False——足以拦截最常见的中断残留形态，且开销极小（不解压全文）。
    try:
        return bool(zipfile.is_zipfile(path))
    except OSError, ValueError:
        return False


# 校验已下载 zip 的 SHA256（trust-on-first-use 模型）：
# - 首次下载完成后把哈希写到 <zip_path>.sha256 旁路文件
# - 再次下载/校验时若旁路文件存在则比对，不一致则拒绝安装（提示用户手动确认或清缓存重下）
# - gyan.dev 升级会变 SHA256，需用户主动删除旁路文件或重新下载
# 此机制不能消除 CDN 投毒（首次下载仍是 trust-on-first-use），但能把"篡改已缓存 zip"
# 阻断在重安装路径之外——历史上蓝奏云分享被替换的最大破坏面是已下载用户被静默替换。
_FFMPEG_HASH_FILE = "_ffmpeg_official.zip.sha256"


def _check_or_record_zip_sha256(zip_path: Path) -> bool:
    # SHA256 校验/记录一体化；返回 True 表示校验通过或首次记录。False 表示哈希不一致拒绝安装。
    hash_file = zip_path.parent / _FFMPEG_HASH_FILE
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
                    "ffmpeg 官方源 zip SHA256 与上次记录不一致（{expected} vs {actual}）。"
                    "可能 CDN 被篡改或版本变更。请删除 {hash_file} 后重试，或手动下载校验。",
                    expected=expected,
                    actual=current_hash,
                    hash_file=str(hash_file),
                )
            )
            return False
        logger.debug("ffmpeg SHA256 校验通过")
        return True
    # 首次记录
    try:
        hash_file.write_text(current_hash, encoding="ascii")
        logger.debug(i18n.tr("首次下载 SHA256 已记录：{current_hash}", current_hash=current_hash))
    except OSError as e:
        logger.warning(i18n.tr("写入 SHA256 缓存失败（不影响本次安装）: {e}", e=e))
    return True


def download_ffmpeg_official(url: str, dest_dir: str) -> bool:
    # 从官方源下载并安装 FFmpeg (Windows)
    try:
        zip_file_path = Path(dest_dir) / "ffmpeg_official_temp.zip"

        # 下载文件（带进度条）
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            # Content-Length 可能缺失（分块传输）为 0，tqdm 进度条退化为未知总量，仅影响显示不影响下载。
            total_size = int(response.headers.get("Content-Length", 0))

            with tqdm(
                total=total_size, unit="B", unit_scale=True, ncols=100, desc="Downloading ffmpeg (official)"
            ) as t:
                with open(zip_file_path, "wb") as f:
                    for data in response.iter_content(chunk_size=1024):
                        _ = t.update(len(data))
                        _ = f.write(data)

        # H-1 修复：下载完后 SHA256 校验/记录（trust-on-first-use），
        # 已在 _check_or_record_zip_sha256 内部说明
        if not _check_or_record_zip_sha256(zip_file_path):
            try:
                zip_file_path.unlink()
            except OSError:
                pass
            return False

        # 解压并提取 bin 目录
        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(zip_file_path, "r") as zf:
                zf.extractall(tmp_dir)

            # 查找 bin 目录（含 ffmpeg.exe）
            bin_dir = None
            for root, _dirs, files in os.walk(tmp_dir):
                if os.path.basename(root) == "bin":
                    if "ffmpeg.exe" in files:
                        bin_dir = root
                        break

            if bin_dir is None:
                logger.error("ffmpeg.exe not found in official package")
                return False

            # 复制到目标位置
            ffmpeg_target = os.path.join(dest_dir, "ffmpeg")
            if os.path.exists(ffmpeg_target):
                shutil.rmtree(ffmpeg_target)

            _ = shutil.copytree(bin_dir, ffmpeg_target)

        # 清理临时文件
        if zip_file_path.exists():
            zip_file_path.unlink()

        # 更新 PATH 并验证安装
        # 把 ffmpeg 目录前置注入 PATH，本进程及子进程后续 `ffmpeg` 调用都命中新装文件（覆盖系统其它同名项）。
        # 先注入再校验，校验失败也保留注入——无副作用（该目录即安装产物）。
        os.environ["PATH"] = ffmpeg_path + os.pathsep + (current_env_path or "")
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=30)
        if result.returncode == 0:
            logger.debug("ffmpeg (official) installation was successful")
            return True
        else:
            logger.error("ffmpeg official installation verification failed")
            return False

    except requests.RequestException as e:
        logger.warning(i18n.tr("Official ffmpeg download failed (network error): {e}", e=e))
        return False
    except Exception as e:
        logger.error(i18n.tr("Official ffmpeg installation failed: {type_name} - {e}", type_name=type(e).__name__, e=e))
        return False


def install_ffmpeg_official_windows() -> bool:
    # Windows: 从官方源 gyan.dev 安装 FFmpeg
    official_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    return download_ffmpeg_official(official_url, execute_dir)


def get_lanzou_download_link(url: str, password: str | None = None) -> str | None:
    # 从蓝奏云获取 FFmpeg 真实下载链接
    try:
        headers = {
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Origin": "https://wwasx.lanzout.com",
            "Referer": "https://wwasx.lanzout.com/b00hryv9ch",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",
        }
        # 蓝奏云下载直链由页面内联动态签名 sign 保护：先 GET 页面提取 sign，再 POST ajaxm.php 换取，
        # 不能直接构造 URL（会得到 403/已过期）。headers 里的 Referer/Origin 为接口硬校验项。
        with requests.get(url, headers=headers, timeout=30) as response:
            sign_match = re.search("var skdklds = '(.*?)';", response.text)
        if not sign_match:
            logger.error("Failed to extract sign from lanzou page")
            return None
        sign = sign_match.group(1)

        # 请求下载地址
        data = {
            "action": "downprocess",
            "sign": sign,
            "p": password,
            "kd": "1",
        }
        with requests.post("https://wwasx.lanzout.com/ajaxm.php", headers=headers, data=data, timeout=30) as response:
            json_data = cast(dict[str, str], response.json())
        download_url = json_data.get("dom", "") + "/file/" + json_data.get("url", "")
        if not download_url or download_url == "/file/":
            logger.error("Failed to build download URL from lanzou response")
            return None

        # 获取最终重定向地址
        with requests.get(download_url, headers=headers, timeout=30) as response:
            return response.url
    except Exception as e:
        logger.error(i18n.tr("Failed to obtain ffmpeg download address. {e}", e=e))
    return None


def _install_ffmpeg_lanzou() -> bool:
    # Windows: 从蓝奏云备用源安装 FFmpeg
    # H-1 修复（2026-09-12 审查）：蓝奏云源是第三方个人网盘分发渠道，分享内容
    # 被替换即使用户机器静默执行任意代码，无法做受信哈希校验。按 review 建议降级：
    # 1) 启动时显著警告"非官方源风险"
    # 2) SHA256 校验支持：若环境变量 FFMPEG_LANZOU_SHA256 预填期望哈希，则强制校验
    #    一致才解压；未填则记录当前哈希供用户后续比对（trust-on-first-use，安全性与
    #    官方源相同——首次下载始终是 trust-on-first-use，但蓝奏云分发的"已知快照"
    #    已有 commit 化的 SHA256 用户可在 release notes 比对）
    try:
        logger.warning("蓝奏云为非官方个人分发源，建议优先使用 gyan.dev 官方源。")
        logger.debug("Installing the latest version of ffmpeg from lanzou for Windows...")
        ffmpeg_url = get_lanzou_download_link("https://wwasx.lanzout.com/b00hryv9ch", "eh7o")
        if not ffmpeg_url:
            logger.error("Failed to obtain ffmpeg download address from lanzou")
            return False

        # 蓝奏云直链不暴露版本号，文件名/版本号写死为快照常量，仅用于展示与本地去重文件名；
        # 实际下载始终取 latest 构建，升级不会因版本号写死而失效。
        full_file_name = "ffmpeg_latest_build_20250124.zip"
        version = "v20250124"
        zip_file_path = Path(execute_dir) / full_file_name

        # 如果已下载则直接安装
        # 2026-09-12 审查（低危）：原只判 exists()，下载被中断留下的残缺 zip
        # 会被当成"已下载"反复走安装分支——解压必失败且本地缓存永不清空，
        # 表现为「每次启动都报安装失败且无法自愈」。改为先做 zip 完整性校验，
        # 非有效 zip 即删除重下（覆盖进程被杀/磁盘满/网络中断三种残留形态）。
        if Path(zip_file_path).exists() and _is_valid_zip(zip_file_path):
            logger.debug("ffmpeg installation file already exists, start install...")
        else:
            if Path(zip_file_path).exists():
                logger.warning("检测到残缺的 ffmpeg 压缩包缓存，删除后重新下载")
                try:
                    Path(zip_file_path).unlink()
                except OSError as e:
                    logger.warning(i18n.tr("删除残缺压缩包失败: {e}", e=e))
            # 下载文件
            with requests.get(ffmpeg_url, stream=True, timeout=60) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("Content-Length", 0))
                block_size = 1024

                with tqdm(
                    total=total_size, unit="B", unit_scale=True, ncols=100, desc=f"Downloading ffmpeg ({version})"
                ) as t:
                    with open(zip_file_path, "wb") as f:
                        for data in response.iter_content(block_size):
                            _ = t.update(len(data))
                            _ = f.write(data)

        # H-1 修复：SHA256 校验（环境变量预填期望值则强制比对）
        lanzou_hash = _sha256_of_file(zip_file_path)
        logger.debug(i18n.tr("蓝奏云 ffmpeg SHA256: {lanzou_hash}", lanzou_hash=lanzou_hash))
        expected = os.environ.get("FFMPEG_LANZOU_SHA256", "").strip().lower()
        if expected:
            if expected != lanzou_hash:
                logger.error(
                    i18n.tr(
                        "蓝奏云 ffmpeg SHA256 与 FFMPEG_LANZOU_SHA256 不一致（{expected} vs {actual}）。拒绝安装。",
                        expected=expected,
                        actual=lanzou_hash,
                    )
                )
                return False
            logger.debug("蓝奏云 SHA256 校验通过")

        # 解压并验证
        unzip_file(zip_file_path, execute_dir)
        # 解压到 execute_dir（与官方源落点一致），随后同样注入 PATH 并 `ffmpeg -version` 校验。
        # 把 ffmpeg 目录前置注入 PATH，使后续 `ffmpeg` 调用命中新装文件。
        os.environ["PATH"] = ffmpeg_path + os.pathsep + (current_env_path or "")
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=30)
        if result.returncode == 0:
            logger.debug("ffmpeg (lanzou) installation was successful")
            return True
        else:
            logger.error("ffmpeg lanzou installation verification failed")
            return False
    except Exception as e:
        logger.error(i18n.tr("ffmpeg lanzou installation failed: {type_name} - {e}", type_name=type(e).__name__, e=e))
        return False


def install_ffmpeg_windows() -> bool:
    # Windows FFmpeg 安装（官方源优先，蓝奏云备用）
    # Windows 安装顺序：官方源 gyan.dev 优先，失败（网络/被墙）再回退蓝奏云备用源；两者皆败提示手动安装。
    # 单源失败不抛异常，让另一源有机会补救，最大化自动安装成功率。
    logger.warning("ffmpeg is not installed.")

    logger.debug("Trying to install ffmpeg from official source (gyan.dev)...")
    if install_ffmpeg_official_windows():
        return True

    logger.warning("Official source unavailable, falling back to lanzou download...")
    if _install_ffmpeg_lanzou():
        return True

    logger.error("All download methods failed. Please manually install ffmpeg by yourself.")
    return False


def install_ffmpeg_mac() -> bool:
    # macOS: 使用 Homebrew 安装 FFmpeg
    logger.warning("ffmpeg is not installed.")
    logger.debug("Installing the stable version of ffmpeg for macOS...")
    try:
        result = subprocess.run(["brew", "install", "ffmpeg"], capture_output=True, timeout=600)
        if result.returncode == 0:
            logger.debug("ffmpeg installation was successful. Restart for changes to take effect.")
            return True
        else:
            logger.error("ffmpeg installation failed")
    except subprocess.CalledProcessError as e:
        logger.error(i18n.tr("Failed to install ffmpeg using Homebrew. {e}", e=e))
        logger.error("Please install ffmpeg manually or check your Homebrew installation.")
    except Exception as e:
        logger.error(i18n.tr("An unexpected error occurred: {e}", e=e))
    return False


def install_ffmpeg_linux() -> bool:
    # Linux: 自动选择 yum/apt 安装 FFmpeg
    is_RHS = True

    # 尝试 yum (RHEL/CentOS)
    try:
        logger.warning("ffmpeg is not installed.")
        logger.debug("Trying to install the stable version of ffmpeg")
        # 2026-09-12 修复（CODE_REVIEW_FIX_1 F-17）：移除 `yum -y update`。
        # 该命令是**全量系统升级**——会一并升级内核、glibc、systemd 等，副作用远超
        # 「装一个 ffmpeg」，可能改变用户环境行为甚至要求重启；且原本 update 失败即
        # return False，把「yum 源暂时不可用」误判成 RHEL 系不可用、连 apt 回退都不给。
        # `yum install` 自身会刷新仓库元数据，无需前置 update。
        # 移除后 install 失败不再 return，会自然落到下方 apt 分支（回退链路反而更稳）。
        result = subprocess.run(["yum", "install", "-y", "ffmpeg"], capture_output=True, timeout=300)
        if result.returncode == 0:
            logger.debug("ffmpeg installation was successful using yum. Restart for changes to take effect.")
            return True
        logger.error(result.stderr.decode("utf-8", errors="replace").strip())
    except FileNotFoundError:
        logger.debug("yum command not found, trying to install using apt...")
        is_RHS = False
    except Exception as e:
        logger.error(i18n.tr("An error occurred while trying to install ffmpeg using yum: {e}", e=e))

    # 尝试 apt (Debian/Ubuntu)
    if not is_RHS:
        try:
            logger.debug("Trying to install the stable version of ffmpeg for Linux using apt...")
            result = subprocess.run(["apt", "update"], capture_output=True, timeout=300)
            if result.returncode != 0:
                logger.error("Failed to update package lists using apt")
                return False

            result = subprocess.run(["apt", "install", "-y", "ffmpeg"], capture_output=True, timeout=300)
            if result.returncode == 0:
                logger.debug("ffmpeg installation was successful using apt. Restart for changes to take effect.")
                return True
            else:
                logger.error(result.stderr.decode("utf-8", errors="replace").strip())
        except FileNotFoundError:
            logger.error("apt command not found, unable to install ffmpeg. Please manually install ffmpeg by yourself")
        except Exception as e:
            logger.error(i18n.tr("An error occurred while trying to install ffmpeg using apt: {e}", e=e))
    logger.error("Manual installation of ffmpeg is required. Please manually install ffmpeg by yourself.")
    return False


def install_ffmpeg() -> bool:
    # 根据当前平台选择对应的 FFmpeg 安装方法
    # 按 current_platform 分发到对应平台的安装器；未知平台仅记录不支持并返 False（不抛异常）。
    if current_platform == "Windows":
        return install_ffmpeg_windows()
    elif current_platform == "Linux":
        return install_ffmpeg_linux()
    elif current_platform == "Darwin":
        return install_ffmpeg_mac()
    else:
        logger.debug(
            i18n.tr(
                "ffmpeg auto installation is not supported on this platform: {current_platform}. Please install ffmpeg manually.",
                current_platform=current_platform,
            )
        )
    return False


def check_ffmpeg_installed() -> bool:
    # 检查 FFmpeg 是否已安装并可用
    try:
        # 2026-09-12 审查（低危）：原无 timeout——ffmpeg 可执行档存在但卡住时
        # （PATH 命中损坏/被占用的 ffmpeg、网络文件系统上的可执行档、杀毒软件
        # 拦截扫描等）subprocess.run 会无限阻塞，把整个启动流程挂死。
        # 版本探测是毫秒级操作，给 15 秒已远超正常耗时。
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=15)
        version = result.stdout.strip()
        if result.returncode == 0 and version:
            return True
    # FileNotFoundError：系统 PATH 中无 ffmpeg 可执行文件，静默返回 False 触发自动安装；
    # OSError 通常是 script_path/ffmpeg 残留了损坏目录但 PATH 找到的是它，提示删除重装以避免反复失败。
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        logger.warning(
            i18n.tr(
                "ffmpeg -version 执行超时（15 秒），按未安装处理: {ffmpeg_path}",
                ffmpeg_path=shutil.which("ffmpeg") or "unknown",
            )
        )
    except OSError as e:
        logger.warning(
            i18n.tr(
                "OSError occurred: {e}. ffmpeg may not be installed correctly or is not available in the system PATH.",
                e=e,
            )
        )
        logger.warning("Please delete the ffmpeg and try to download and install again.")
    except Exception as e:
        logger.error(i18n.tr("An unexpected error occurred: {e}", e=e))
    return False


def check_ffmpeg() -> bool:
    # 主入口：检查 FFmpeg，未安装则自动安装
    if not check_ffmpeg_installed():
        return install_ffmpeg()
    return True
