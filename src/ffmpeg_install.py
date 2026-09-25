#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Mapping
from pathlib import Path

import requests

# loguru 的 logger 为模块级单例，src.logger 对其做过的配置在此同样生效；
# 直接从此处导入可避免基于 basedpyright 的 "未从 src.logger 导出" 告警。
from loguru import logger
from tqdm import tqdm

import i18n

# 解压实现与 node_install 共用同一份（原先两处逐字重复，见 src/utils.unzip_file）
from src import utils

# 布尔环境开关的唯一解析入口（与全仓布尔配置同一识别集合，勿在别处再造第三套布尔判定）
from src.config_bool import parse_config_bool

# Windows ARM64 原生构建 / gyan.dev 不可达时的兜底下载器：BtbN master 滚动构建
# （上游不公布 latest 别名的 SHA256，只有 TOFU）。**默认不调用**——须 FFMPEG_MASTER_ALLOWED
# 显式取真才走该路径，判据与理由见 _master_source_allowed() 与 install_ffmpeg_windows()。
# 本模块不 import ffmpeg_install，故此处单向引入无循环依赖风险。
from src.ffmpeg_master_download import download_ffmpeg_master

# 应用根目录复用 src.logger 公开导出的 script_path（等价原私有 _app_root() 的返回值）
from src.logger import script_path
from src.utils import unzip_file

# FFmpeg 自动安装模块 - 跨平台 FFmpeg 自动检测与安装
#
# 职责：检测系统是否已安装 ffmpeg（check_ffmpeg_installed），未安装则按平台自动拉取并安装——
#   Windows 默认只有官方源 gyan.dev 一条自动路径（第二条源默认关闭，见「Windows 下载源现状」段），
#   macOS 走 Homebrew，Linux 走 yum/apt。
# 安装落点：execute_dir（冻结后指向 _internal/，与运行时资源同目录），装好后把 ffmpeg 目录
#   前置注入 os.environ["PATH"]，使同进程后续 subprocess 调用 `ffmpeg` 能直接命中。
# 校验约定：所有安装路径最后都跑一次 `ffmpeg -version`，returncode==0 才认成功，否则报错并返回 False。
# 设计取舍：安装失败只返回 False、不抛异常（由调用方决定提示用户手动安装），避免中断主程序启动。
#
# 完整性模型（P-1，2026-09-22 起）：**权威校验优先、TOFU 只作显式降级的兜底**。
#   ① 下载前向 gyan.dev 取官方公布的 <zip URL>.sha256 文档，与本地实算哈希比对——不符即拒绝安装；
#   ② 只有「取不到官方文档」（网络失败 / 非 200 / 文档形态变更）时才退回旁路基准 TOFU，
#      并 logger.warning 将降级显式写进日志。
#   为什么取文档而不是把哈希常量钉进源码：下载的是**滚动**地址，钉常量会在上游发新版后
#   永久失败（即历史坑 MID-59「自动安装永久死路」的成因）；取文档则每次都对应当前构建。
#   为什么 TOFU 不足以作为唯一防线：首次安装那一次没有任何可比对的期望值，
#   而那正是供应链投毒最有价值的窗口（发布后第一批用户必然命中）。
#   本模块属 AGENTS.md「三类钉定/校验」中的第②类（运行期自动安装，单机面），
#   与 build_exe.py 的发布期钉定（分发面）、utils._JS_SHA256_EXPECTED 的签名脚本层互不覆盖。
#
# Windows 下载源现状（2026-09-23 起）：gyan.dev 是**默认且唯一**的自动路径；失败且未开启
#   FFMPEG_MASTER_ALLOWED 时只给出手动安装提示（见 install_ffmpeg_windows）。
#   第二条源 BtbN master 滚动构建（src/ffmpeg_master_download.py）因上游不为 latest 别名公布
#   .sha256、只能落 TOFU，不满足第②类的准入判据，故显式门控且默认关闭；开启与跳过两条分支
#   都各落一条 warning，不静默。
#   [历史注] 2026-09-22 蓝奏云个人网盘兜底整体删除（直链需爬分享页内联签名、且无独立可信来源
#   可比对）；同日 master 源曾默认开启，2026-09-23 按 SEV-2218 收为默认关闭。
#
# PATH 优先级策略（W6，2026-09-22 起）：包内 ffmpeg 目录是否前置由
#   should_prepend_bundled_ffmpeg_dir() 单点裁决（判据、后果与日志口径见该函数注释）。
#   本模块自身的「安装成功后前置注入 PATH」（Windows 官方源一处）**不在**该判据范围内：
#   它只发生在「系统里本来就没有可用 ffmpeg」的自动安装分支，且仅 Windows 分支可达，
#   让位判据在 macOS/Linux 安装路径（brew / yum / apt）上根本不执行。


current_platform = platform.system()
execute_dir = script_path  # 冻结后指向 _internal/，与 __file__ 定位的资源收敛到同一处
# 安装时把新 ffmpeg 目录前缀拼回系统原 PATH；运行期 PATH 可能已被修改，先快照原始值避免重复嵌套。
current_env_path = os.environ.get("PATH")
# 安装目标子目录：ffmpeg 可执行文件最终位于 execute_dir/ffmpeg/bin/ffmpeg.exe。
ffmpeg_path = os.path.join(execute_dir, "ffmpeg")


# 下面两个薄封装：实现已于 2026-09-18（CR-11）下沉到 src.utils，保留本模块别名供既有调用点与测试
# 继续引用（与 spider._is_safe_http_url 同一处置）。原状是两处逐字重复、node_install 那份还只判
# exists——打补丁必漏一处，故收敛到唯一实现。
# _sha256_of_file 分块读取：整读几百 MB 二进制会瞬时占用大量内存，分块保持内存恒定（H-1）。
def _sha256_of_file(path: str | Path) -> str:
    return utils.sha256_of_file(path)


def _is_valid_zip(path: str | Path) -> bool:
    return utils.is_valid_zip(path)


# 校验已下载 zip 的 SHA256（trust-on-first-use 模型）：
# - 首次下载完成后把哈希写到旁路文件
# - 再次下载/校验时若旁路文件存在则比对，不一致则拒绝安装
#
# MID-59（避免「自动安装永久死路」）：旁路文件**按构建标识命名**而不是按滚动 URL 的固定 zip 名——
#   gyan.dev 的 ffmpeg-release-essentials.zip 是滚动地址、上游每次出新构建内容（SHA）必变，旧命名
#   _ffmpeg_official.zip.sha256 一旦记录某构建，下次自动安装拿到新构建就**永远不等** → 官方源拒绝 →
#   用户只剩一行 logger.error 和「请手动安装 ffmpeg」。按构建标识（响应头 Last-Modified / ETag /
#   Content-Length 的摘要）命名后，「版本轮转」表现为「为新构建记录新基准」、「同一构建内容变了」仍
#   是硬失败——篡改检测强度不降。（默认下 gyan.dev 是唯一自动路径，此「死路」论断成立；用户自开 master
#   开关时不成立，而那时他已看过写明 TOFU 强度的 warning。）
#   [历史注] 旧版本此处把失败链写成「官方源拒绝 → 转蓝奏云 → 蓝奏云亦拒绝」，该兜底源于 2026-09-22 删除，
#   链尾现为「官方源拒绝 → 直接只剩手动安装」。
#
# 防护强度边界（勿据此高估）：
#   1) 本机制不能消除 CDN 投毒（首次下载始终是 trust-on-first-use），只阻断「已缓存 zip 被静默
#      替换」这条重安装路径；P-1 之后优先走官方哈希文档，TOFU 只在取不到文档时才生效，已收窄；
#   2) 旁路文件与 zip 同在 execute_dir（冻结后为 _internal/），能写该目录者可同时替换产物与基准
#      文件，故其强度**等同目录权限**，不是独立的信任根；
#   3) 官方哈希文档（_fetch_official_sha256）与产物**同主机、同一 HTTPS 通道**，期望值与实际文件
#      同源，故它只是一次**同源一致性校验**（防传输截断、防 CDN/代理缓存污染、防把挑战页当产物），
#      **不构成来源认证**——宿主或 CDN 被整体替换时，文档与产物会被一并换掉，校验归零。
#      gyan.dev 不提供 detached 签名，故 Windows 运行期目前只能到这一档；真要加来源认证得换一个
#      「文档与产物异源」的取法（对比 src/node_install.py 刻意换宿主取 SHASUMS256.txt 的做法，
#      以及 build_exe.py 的发布期钉定，见 AGENTS.md「三类钉定/校验」②）。
_FFMPEG_HASH_FILE = "_ffmpeg_official.zip.sha256"  # 旧版（不随构建轮转）命名，仅作只读兼容
_HASH_SUFFIX = ".zip.sha256"

# 官方哈希文档的后缀（gyan.dev 对每个构建产物都公布 `<产物名>.sha256`，内容就是裸 64 位十六进制）。
# 与上面的 _HASH_SUFFIX（本地旁路基准文件名的后缀，含 .zip）刻意不同名，勿混用。
_OFFICIAL_DOC_SUFFIX = ".sha256"
# 哈希文档只有 64 字节，用与 300MB 压缩包相同的 30s 超时会在上游故障时把启动拖慢一倍；
# 取不到即降级为 TOFU，不值得为它多等。
_OFFICIAL_DOC_TIMEOUT_SECONDS = 15
# 官方文档的合法形态：整篇剥掉空白后必须**正好**是 64 位小写十六进制。
# 判据必须严格：gyan.dev 在前置代理/WAF 介入时会回 200 + 一段 HTML 挑战页，
# 「长度看着像」的宽松判定会把挑战页当成期望哈希，从而把可用源判成篡改。
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


# 把官方哈希文档正文解析为小写十六进制摘要；形态不符（HTML 错误页、截断、含文件名前缀等）返回 ""。
def _parse_official_sha256(text: str) -> str:
    candidate = text.strip().lower()
    return candidate if _SHA256_RE.fullmatch(candidate) else ""


# 向上游取官方公布的 SHA256。返回 ""=未取得（调用方据此显式降级到 TOFU）。
# 失败绝不抛异常：本函数的定位是「能拿到就更强、拿不到就退回原有防线」，
# 若让网络故障把整条安装链路打成异常，等于用一个可选加固换掉本来能成功的自动安装。
#
# 2026-09-22 实测形态：文档端点回 303 → /ffmpeg/builds/packages/ffmpeg-<ver>-essentials_build.zip.sha256，
# 最终正文是**裸 64 位小写十六进制**（无换行、无文件名），与滚动别名两个端点互相印证。
# 因此这里**必须保持 requests 的默认 allow_redirects=True**：把它改成 False（或换成 HEAD）
# 会永远只看到 303 + 空正文 → 恒降级为 TOFU，且日志里只是一句「未取得文档」，极易误判成上游故障。
def _fetch_official_sha256(doc_url: str) -> str:
    try:
        with requests.get(doc_url, timeout=_OFFICIAL_DOC_TIMEOUT_SECONDS) as response:
            response.raise_for_status()
            text = response.text
    except Exception as e:
        logger.warning(
            i18n.tr(
                "未取得 ffmpeg 官方 SHA256 文档: {masked_url} - {type_name}: {err}",
                masked_url=utils.mask_credentials(doc_url),
                type_name=type(e).__name__,
                err=e,
            )
        )
        return ""
    parsed = _parse_official_sha256(text)
    if not parsed:
        logger.warning(
            i18n.tr(
                "ffmpeg 官方 SHA256 文档内容不是合法的 64 位十六进制摘要（上游形态可能已变更）: {masked_url}",
                masked_url=utils.mask_credentials(doc_url),
            )
        )
    return parsed


# 由下载响应头推导「构建标识」：无任何可用头时返回 ""（退化为旧命名，保持有校验而非静默放行）。
def _build_identity(headers: Mapping[str, str] | None) -> str:
    if not headers:
        return ""
    try:
        bits = [
            str(headers.get("Last-Modified") or "").strip().strip('"'),
            str(headers.get("ETag") or "").strip().strip('"'),
            str(headers.get("Content-Length") or "").strip(),
        ]
    except Exception:  # 非 Mapping 形态（测试桩）不影响主流程
        return ""
    raw = "|".join(b for b in bits if b)
    if not raw:
        return ""
    # 取摘要前 12 位：头里含冒号 / 空格 / 逗号，直接拼进文件名在 Windows 上非法
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


# 旁路文件基名：有构建标识 → _ffmpeg_official.<id>.zip.sha256；无标识 → 旧名。
def _hash_file_name(build_id: str) -> str:
    return f"_ffmpeg_official.{build_id}{_HASH_SUFFIX}" if build_id else _FFMPEG_HASH_FILE


# 把本次实算哈希写进旁路基准（TOFU 的「记录」侧，原先内联在 _check_or_record_zip_sha256 里）。
# 权威校验通过时同样记录：官方文档不可达的那次运行（离线 / 上游故障）需要它才有可比对基准。
def _record_zip_sha256(zip_path: Path, hash_file: Path, current_hash: str) -> None:
    # 本构建标识首次记录。若目录里已存在其它基准文件，说明上游发布了新构建（旧基准随之失效），
    # 显式告警并列出被取代的基准，便于用户复核两次哈希是否来自可信渠道。
    stale = sorted(p.name for p in zip_path.parent.glob(f"_ffmpeg_official*{_HASH_SUFFIX}") if p.name != hash_file.name)
    try:
        hash_file.write_text(current_hash, encoding="ascii")
        if stale:
            logger.warning(
                i18n.tr(
                    "ffmpeg 官方源已发布新构建，已为新构建记录 SHA256 基准：{hash_file}（{actual}）。"
                    "旧基准 {stale} 不再参与校验，确认无误后可删除。",
                    hash_file=str(hash_file),
                    actual=current_hash,
                    stale=", ".join(stale),
                )
            )
        else:
            logger.debug(i18n.tr("首次下载 SHA256 已记录：{current_hash}", current_hash=current_hash))
    except OSError as e:
        logger.warning(i18n.tr("写入 SHA256 缓存失败（不影响本次安装）: {e}", e=e))


# 完整性判定入口：**官方公布的哈希优先**，取不到才退回旁路基准 TOFU（原行为）。
# 返回 True = 校验通过或（首次/新构建）记录成功；返回 False 一律意味着「同一构建标识下内容与
# 期望值不符」——真篡改形态，调用方必须删包且不执行。
def _check_or_record_zip_sha256(
    zip_path: Path, build_id: str = "", official_hash: str = "", source_url: str = ""
) -> bool:
    hash_file = zip_path.parent / _hash_file_name(build_id)
    current_hash = _sha256_of_file(zip_path)
    masked_url = utils.mask_credentials(source_url) if source_url else "unknown"
    if official_hash:
        # 权威分支：官方文档就是当前构建的期望值，旁路基准至多是第二道记录，不得反过来否决它
        # （否则 MID-59 的「版本轮转即永久拒装」在官方文档可达时仍会复现）。
        if official_hash != current_hash:
            logger.error(
                i18n.tr(
                    "ffmpeg 官方源 zip 与官方公布的 SHA256 不一致，拒绝安装（官方 {official} vs 实际 {actual}）："
                    "{masked_url}。可能是 CDN/中间人替换，或下载期间上游又发了新构建（稍后重试即可）。",
                    official=official_hash,
                    actual=current_hash,
                    masked_url=masked_url,
                )
            )
            return False
        logger.debug(i18n.tr("ffmpeg zip 已通过官方公布 SHA256 校验: {masked_url}", masked_url=masked_url))
        _record_zip_sha256(zip_path, hash_file, current_hash)
        return True
    # 降级分支（P-1 的显式降级点）：官方文档拿不到 → 只能沿用首次信任，必须让日志说清强度回落了。
    logger.warning(
        i18n.tr(
            "未能取得 ffmpeg 官方公布的 SHA256，本次退回旁路基准/首次信任（TOFU）: {masked_url}",
            masked_url=masked_url,
        )
    )
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
    _record_zip_sha256(zip_path, hash_file, current_hash)
    return True


def download_ffmpeg_official(url: str, dest_dir: str) -> bool:
    # 从官方源下载并安装 FFmpeg (Windows)
    try:
        zip_file_path = Path(dest_dir) / "ffmpeg_official_temp.zip"

        # P-1：下载**前**先取官方公布的期望哈希。放在前面而不是后面，是为了在上游文档已不可达 /
        # 已被替换时少拉一次几百 MB；比对对象仍是同一 URL 的当前构建（上游版本轮转的窗口
        # 在两种顺序下都存在，区别只是「白下载一次」与「白等一次」）。
        official_hash = _fetch_official_sha256(url + _OFFICIAL_DOC_SUFFIX)

        # 下载文件（带进度条）
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            # Content-Length 可能缺失（分块传输）为 0，tqdm 进度条退化为未知总量，仅影响显示不影响下载。
            total_size = int(response.headers.get("Content-Length", 0))
            # MID-59：在读取响应头仍可用的作用域内固化「构建标识」，供旁路文件命名。
            build_id = _build_identity(response.headers)

            with tqdm(
                total=total_size, unit="B", unit_scale=True, ncols=100, desc="Downloading ffmpeg (official)"
            ) as t:
                with open(zip_file_path, "wb") as f:
                    for data in response.iter_content(chunk_size=1024):
                        _ = t.update(len(data))
                        _ = f.write(data)

        # 加固（2026-09-22）：先判「拿到的到底是不是压缩包」，再进哈希校验/记账。
        # 成因不是假想：CDN / 前置代理 / 被改指的 URL 都会以 **200 + text/html** 回一段挑战页
        # （实测形态：某镜像站的人机验证 PoW 页，正文 10KB、且不带 Content-Length / ETag /
        # Last-Modified）。三个头全缺 → _build_identity 返回 "" → 旁路基准落到**旧文件名**
        # _ffmpeg_official.zip.sha256；若不在此拦住，_check_or_record_zip_sha256 会在 TOFU 分支
        # 把这段 HTML 的哈希当成「可信基准」写下去，而真正的失败要等到 unzip_file 才暴露，
        # 日志只剩一句「不是 zip」——基准已被污染，下次拿到真包反倒可能被判成篡改。
        # 判序必须是「形态 → 哈希 → 解压」：三者校验的都是同一个产物文件。
        if not _is_valid_zip(zip_file_path):
            logger.error(
                i18n.tr(
                    "ffmpeg 下载产物不是有效的 zip 压缩包，拒绝校验与安装"
                    "（内容可能是人机验证页 / 错误页，而非构建产物）: {masked_url}",
                    masked_url=utils.mask_credentials(url),
                )
            )
            try:
                zip_file_path.unlink()
            except OSError:
                pass
            return False

        if not _check_or_record_zip_sha256(zip_file_path, build_id, official_hash, source_url=url):
            try:
                zip_file_path.unlink()
            except OSError:
                pass
            return False

        # 解压并提取 bin 目录
        # CR-11 修复：官方源原走 zf.extractall，绕过了 unzip_file 的解压炸弹防护
        # （单文件 4GB / 累计 8GB / 压缩比 100x 上限）与 Zip Slip 校验，与同期的蓝奏云路径
        # （现已删除）防护强度不一致。损坏或被投毒的 zip 可撑爆磁盘。统一走唯一实现。
        with tempfile.TemporaryDirectory() as tmp_dir:
            unzip_file(zip_file_path, tmp_dir, delete=False)

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


# 第二条 Windows 运行期 ffmpeg 源（BtbN master 滚动构建）的显式开关，默认关闭（SEV-2218）。
# 为什么必须默认关：AGENTS.md「三类钉定/校验」② 的红线是「Windows 运行期只有 gyan.dev 一条
# 自动路径，新增任何第二条前必须先满足『官方公布哈希』判据」。master-latest 是**滚动别名**，
# BtbN 与 fyhub 镜像都不为它公布可核对的 .sha256（后者该文档实测 404），故该源只能落在
# TOFU（首次信任）强度上——恰恰不满足该判据，因此不得成为默认路径。
# 与被删除的蓝奏云兜底同一处置口径：要使用，就得用户显式承担未校验安装的后果。
_FFMPEG_MASTER_ENV = "FFMPEG_MASTER_ALLOWED"


def _master_source_allowed() -> bool:
    # 取值口径一律走 src/config_bool.parse_config_bool（是/否、true/false、1/0、yes/no、
    # on/off、t/f，大小写与首尾空白均不敏感），**不得**再写 `== "1"` / `in ("true","1")`
    # 这类第三套布尔判定——「同一份配置在不同模块语义不同」的老坑（见 AGENTS.md 第 9 条）。
    # 未设置该变量时 parse_config_bool(None, False) 返回默认值 False。
    return parse_config_bool(os.environ.get(_FFMPEG_MASTER_ENV), False)


def install_ffmpeg_windows() -> bool:
    # Windows FFmpeg 安装入口：按「架构 × FFMPEG_MASTER_ALLOWED 开关」分流（master 门禁理由见
    # _FFMPEG_MASTER_ENV 上方注释）。x86_64 只走 gyan.dev 官方源（带官方 SHA256 校验），失败时**仅当**
    # FFMPEG_MASTER_ALLOWED 取真才回落 BtbN master（无官方 .sha256、仅 TOFU）；ARM64 因 gyan.dev 只发
    # x86_64（可经 x64 模拟跑、非原生）、原生 arm64 只能来自 master，故未开启时用官方 x86_64 模拟、开启后
    # 先试原生 arm64 master 再退官方 x86_64 保底。两条分支在「开启」与「因未开启而跳过」时各落一条 warning、
    # 绝不静默；失败不抛异常，由调用方决定后续提示（与既有契约一致）。
    logger.warning("ffmpeg is not installed.")
    is_arm64 = platform.machine().lower() in ("arm64", "aarch64")
    master_allowed = _master_source_allowed()
    if master_allowed:
        logger.warning(
            i18n.tr(
                "{env} 已开启：允许使用 BtbN master 构建作为 ffmpeg 兜底源。该源上游不公布 latest 别名的 "
                "SHA256，本次完整性仅为首次信任（TOFU，等同未校验安装），请在可信网络环境下核对产物。",
                env=_FFMPEG_MASTER_ENV,
            )
        )
    else:
        logger.warning(
            i18n.tr(
                "{env} 未开启：跳过 BtbN master 兜底源（因其无官方公布的 SHA256，默认不作为自动安装路径）。"
                "Windows 仍只使用 gyan.dev 一条官方自动路径{arm_note}",
                env=_FFMPEG_MASTER_ENV,
                arm_note="；ARM64 宿主上该官方构建经 x64 模拟运行" if is_arm64 else "",
            )
        )

    if is_arm64:
        if master_allowed:
            logger.debug(
                "Windows on ARM detected; gyan.dev ships x86_64 only — trying native arm64 master build (TOFU) ..."
            )
            if download_ffmpeg_master(execute_dir, arch="winarm64"):
                return True
            # 原生失败退回官方 x86_64（经模拟运行），至少可用
            logger.warning(
                "Native arm64 ffmpeg unavailable, falling back to official x86_64 build (emulated under x64) ..."
            )
        if install_ffmpeg_official_windows():
            return True
    else:
        logger.debug("Trying to install ffmpeg from official source (gyan.dev)...")
        if install_ffmpeg_official_windows():
            return True
        # x86_64 官方源失败的兜底：BtbN master 构建（来自 ffmpeg-windows-builds 官方发布通道；
        # latest 别名不公布 .sha256，故仅 TOFU，完整性弱于官方 SHA256），受上面的 master_allowed
        # 门禁、未开启时走不到这一行。它是「gyan.dev 慢/被阻」时的可用性兜底。
        if master_allowed:
            logger.warning("Official gyan.dev source failed; trying BtbN master build fallback (TOFU, unverified) ...")
            if download_ffmpeg_master(execute_dir, arch="win64"):
                return True

    # 全部失败：给出手动安装提示。
    # MID-59：官方源被「哈希基准」拒时用户只剩「手动安装」这一句无指向性的提示。
    # 把可执行的自救步骤（删过期基准）与旁路文件的真实防护强度（与产物同目录 →
    # 等同目录权限）一并说明；master 路径的 TOFU 基准（_ffmpeg_master*）同理。
    logger.error("All download methods failed. Please manually install ffmpeg by yourself.")
    logger.warning(
        i18n.tr(
            "若因 SHA256 基准校验被拒，请删除 {files} 后重试（该旁路文件与安装包同目录，"
            "其校验强度等同于目录权限；官方源用 _ffmpeg_official*，master 源用 _ffmpeg_master*）。",
            files=os.path.join(execute_dir, "_ffmpeg_official*") + " / " + os.path.join(execute_dir, "_ffmpeg_master*"),
        )
    )
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
        # 2026-09-12 修复（CODE_REVIEW_FIX_1 F-17）：移除 `yum -y update`——它是**全量系统升级**（一并升
        # 内核 / glibc / systemd，副作用远超「装一个 ffmpeg」、甚至要求重启），且 `yum install` 自身会刷新
        # 仓库元数据、无需前置 update；旧实现 update 失败即 return False，还会把「yum 源暂不可用」误判成
        # RHEL 系不可用、连 apt 回退都不给。
        # [2026-09-20 MIN-24④ 修订] 本块旧末句「移除 update 后 install 失败会自然落到下方 apt 分支」与实现不符：
        # is_RHS 原本只在 FileNotFoundError 分支置 False，「yum 在位但装不上」（RHEL 未启用 EPEL 的常态）遂
        # 直接落到「请手动安装」——真正的回退置位在下方 returncode!=0 分支（其语义见该处注释）。
        result = subprocess.run(["yum", "install", "-y", "ffmpeg"], capture_output=True, timeout=300)
        if result.returncode == 0:
            logger.debug("ffmpeg installation was successful using yum. Restart for changes to take effect.")
            return True
        logger.error(result.stderr.decode("utf-8", errors="replace").strip())
        # MIN-24④：is_RHS 的语义是「还要不要试 apt」。yum 存在但装不上（仓库里没有 ffmpeg）
        # 时不能就此放弃——继续走 apt 分支；apt 也不存在时由它的 FileNotFoundError 分支
        # 给出「请手动安装」，不会静默成功。
        is_RHS = False
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


# 包内 ffmpeg 目录是否应当前置到 PATH —— **主程序侧**判据的唯一事实源（W6，2026-09-22）。
# 孪生副本：`scripts/douyin_live_recorder_standalone.py` 里同名同语义函数（该文件按设计不 import
# src/，可独立单文件分发）。**改判据必须两处同改**（同 src/scheduler.py 的副本先例），
# 行为等价性由 tests/test_ffmpeg_path_preference.py 的 TestTwinEquivalence 锁住。
# 返回 True  = 维持既有行为（把包内目录前置）；False = 不前置，让系统 PATH 上已有的那份生效。
#
# 为什么要让位：full 包内置的 macOS ffmpeg 是 evermeet 的 **x86_64** 静态构建
#   （ffmpeg.org 官方 macOS 条目只列「Static builds for macOS 64-bit」，上游不发布 arm64 构建，
#   arm64 端点实测 404），在 Apple Silicon 上只能经 Rosetta 2 转译执行。而 main.py 原先
#   **无条件**把包内目录前置，于是「已用 Homebrew 装了原生 arm64 ffmpeg」的用户会被包内那份
#   遮蔽，白付转译开销——重编码路径最明显（src/video_postprocess.py 的 libx264、
#   main.py 的 libmp3lame），因为转译对纯 copy 拉流影响小、对软件编码影响大。
#
# 为什么判据保守（任一不成立即维持现状）：PATH 优先级是全局副作用，误判一次会让全部录制
#   子进程改用用户机器上的另一份 ffmpeg（版本/编译选项都可能不同）。故只在「darwin + arm64 +
#   包内目录存在 + 注入前的 PATH 上另有 ffmpeg + 那份不是包内自身」五条同时成立时才让位；
#   Windows / Linux / Intel Mac 的行为逐字不变——改它们的 PATH 优先级会破坏既有语义
#   （Windows 的自动安装分支本身就靠前置生效，见模块头「PATH 优先级策略」段）。
def should_prepend_bundled_ffmpeg_dir(bundled_dir: str, current_path: str) -> bool:
    # 判据 1（平台门控必须用 sys.platform 字面量）：非 darwin 一律恒前置。
    # mypy 在 --platform linux / win32 下都会把该分支当常量处理，但不影响可达性判定
    # （本仓未开 warn_unreachable），故这里不写 `# type: ignore`。
    if sys.platform != "darwin":
        return True

    # 判据 2（架构）：只有 arm64 宿主才存在「包内是转译构建」这回事。
    # 已知边界：Python 解释器自身跑在 Rosetta 下时 platform.machine() 报 "x86_64"，
    # 判据不成立 → 维持现状前置。这是刻意选择的**漏判方向**（宁可继续用包内那份，
    # 也不要在架构信息不可信时改用系统那份）。
    if platform.machine().lower() != "arm64":
        return True

    # 判据 3：包内目录不存在时谈不上「遮蔽」，行为保持不变（照旧前置；后续 ffmpeg 查找
    # 自然落到系统 PATH，与改动前完全一致）。
    if not os.path.isdir(bundled_dir):
        return True

    # 判据 4：注入**前**的 PATH 上确实有一个可执行的 ffmpeg。必须用 current_path 而不是
    # 默认的 os.environ["PATH"]——调用点（main.py）正是在前置之前取好的快照，
    # 否则本函数会探测到「刚被自己前置进来的那一份」，判据恒成立、让位永不发生。
    system_ffmpeg = shutil.which("ffmpeg", path=current_path) if current_path else None

    # 判据 5：探到的这份不能就是包内那一份。用户把包内目录永久写进了自己的 PATH 时，
    # 「让位」只是不再前置、命中的仍是同一份 x86_64 构建——日志却会承诺原生 arm64，
    # 即自我遮蔽下的假绿。realpath 归一后再比目录前缀，覆盖符号链接（/usr/local/bin 常见）
    # 与嵌套落点两种形态。
    if system_ffmpeg:
        candidate_real = os.path.realpath(system_ffmpeg)
        bundle_real = os.path.realpath(bundled_dir)
        if candidate_real == bundle_real or candidate_real.startswith(bundle_real + os.sep):
            logger.debug(
                i18n.tr(
                    "FFmpeg PATH 优先级：Apple Silicon 上系统 PATH 探测到的 {system_ffmpeg} "
                    "就是包内目录自身，仍前置包内目录 {bundled_dir}（没有原生 arm64 构建可让位）",
                    system_ffmpeg=utils.mask_credentials(system_ffmpeg),
                    bundled_dir=utils.mask_credentials(bundle_real),
                )
            )
            return True
    else:
        logger.debug(
            i18n.tr(
                "FFmpeg PATH 优先级：Apple Silicon 上系统 PATH 未探测到 ffmpeg，"
                "仍前置包内目录 {bundled_dir}（包内为 x86_64 构建，需经 Rosetta 运行）",
                bundled_dir=utils.mask_credentials(os.path.realpath(bundled_dir)),
            )
        )
        return True

    # 五条判据全部成立：让位。只打印两个候选路径，不打印整条 PATH
    # （那会把用户全部个人目录写进会轮转留存的日志，超出排查所需）。
    logger.debug(
        i18n.tr(
            "FFmpeg PATH 优先级：让位于系统原生 ffmpeg {system_ffmpeg}，不再前置包内目录 "
            "{bundled_dir}（包内为 x86_64 构建，Apple Silicon 需经 Rosetta 转译）",
            system_ffmpeg=utils.mask_credentials(system_ffmpeg),
            bundled_dir=utils.mask_credentials(os.path.realpath(bundled_dir)),
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
