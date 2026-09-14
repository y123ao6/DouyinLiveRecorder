#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import functools
import hashlib
import inspect
import json
import os
import random
import re
import shutil
import string
import subprocess
import threading
import traceback
import zipfile
from collections import OrderedDict
from collections.abc import Mapping
from pathlib import Path
from typing import Callable, ParamSpec, TypeVar, cast
from urllib.parse import parse_qs, urlparse

import i18n

# 工具函数模块 - 提供通用工具函数，包括配置文件读写、文件操作、字符串处理等


# URL scheme 白名单校验（2026-09-12 审查 6.3 从 src/spider.py 上移至此）：
# 仅放行 http(s) 与 ws(s)。防用户在 URL_config.ini 写入 file:// / gopher:// /
# ftp:// 等协议造成 SSRF——本项目虽无「服务端直接 fetch 用户 URL」的经典攻击面，
# 但 stream_select 的流地址校验与后续解析链路仍会按 URL 触发请求，收紧 scheme
# 边界是最低成本的防御。
# 上移原因：原先定义在 spider.py，而真正的请求入口（async_http / sync_http）在
# 依赖链更底层，无法反向 import spider（循环依赖）→ 函数零生产调用，退化成纸面
# 防御。放到 utils（无业务依赖的底层模块）后各层均可直接引用。
_SAFE_URL_SCHEMES = frozenset({"http", "https", "ws", "wss"})


def is_safe_http_url(url: str) -> bool:
    # 校验 URL 的 scheme 是否在白名单内；空串/缺 scheme 的相对路径一律拒绝。
    parsed = urlparse(url)
    return parsed.scheme in _SAFE_URL_SCHEMES


# ─────────────────────────────────────────────────────────────
# JS 执行（2026-09-12 审查 6.3）
#
# 背景：多个平台（LiveMe / 嗨秀 / 抖音 X-Bogus / 咪咕）需调用 node 子进程执行
# 签名脚本。原先各调用点直接在 async 协程里同步 `execjs.compile(...).call(...)`
# 或 `subprocess.run(["node", ...], timeout=30)`——execjs 内部就是起 node 子进程
# 并阻塞等待 stdout，在「每房间独立线程 + 独立事件循环」模型下会**冻结该房间的
# 整个事件循环**（咪咕最坏 30s，期间该房间的其它协程全部停摆）；且每次调用都
# 重新读文件 + compile，重复开销。
#
# 本组工具统一解决两点：
#   1. 按 (路径, mtime) 缓存编译产物，省去重复读文件与 compile；
#   2. run_js_async 把阻塞段整体丢进 asyncio.to_thread，协程侧只 await。
# ─────────────────────────────────────────────────────────────

# path -> (源文件 mtime, 编译产物)。mtime 参与键判定：脚本更新后自动重编译，
# 无需重启进程（开发期频繁改签名脚本场景）。
_js_compile_cache: dict[str, tuple[float, object]] = {}
_js_compile_lock = threading.Lock()

# ── 签名脚本完整性钉定（2026-09-12 修复 CODE_REVIEW_FIX_1 F-25）──
# src/javascript/ 下的脚本是各平台签名算法的混淆产物，内含 eval，经 execjs 交给
# node 执行。它们是**被执行的代码**，一旦被篡改（供应链投毒、误操作覆盖、下载
# 到错误版本）就会静默产出错误签名，表现为「某平台突然全部解析失败」且极难归因。
# 这里记录 2026-09-12 基线的 SHA256，供 get_compiled_js 比对。
#
# 默认**只告警不阻断**：平台改版时用户/维护者必须能自行更新脚本，强制校验会把
# 正当更新变成「程序不可用」。需要强约束的场景（CI、加固部署）可设环境变量
# DLR_JS_STRICT_HASH=1，届时哈希不符将拒绝执行。
# 更新脚本后请把新哈希同步到此处（并注明来源版本/日期）。
_JS_SHA256_EXPECTED: dict[str, str] = {
    "crypto-js.min.js": "769a555de553babc35a3338f344dd7aa16260c93cea2c7db290707c90484e7cc",
    "haixiu.js": "e8f13f4a4048f99fa12c44b26381d8711582ce81c902f523fbec0c668bbf83d7",
    "laixiu.js": "c08d9f7128d121d822068edc2956e8662787aed30c904815ffe9fc846290fc57",
    "liveme.js": "62199fc7847c157d2f0554e6a4f6447208b391ad19db8211251522d487e5d27d",
    "migu.js": "01bf22bdd4ce77457b441bb659271010fc6d99ccdd46ba986b6533db117b9a54",
    "taobao-sign.js": "c1ebd683b564ded7ee81a2135f3a9a7b2e4dde266c46441a9e02872685075528",
    "x-bogus.js": "12077d60606ee652ef218e21440db47d6604a9647517beaa05e6d262555badd0",
}


def _check_js_hash(js_path: str, raw: bytes) -> None:
    # 比对签名脚本哈希与钉定值；不符时按严格模式开关决定告警还是拒绝。
    name = os.path.basename(js_path)
    expected = _JS_SHA256_EXPECTED.get(name)
    if not expected:
        return  # 未登记的脚本（动态生成/第三方）不校验
    actual = hashlib.sha256(raw).hexdigest()
    if actual == expected:
        return
    strict = os.environ.get("DLR_JS_STRICT_HASH", "").strip().lower() in ("1", "true", "yes")
    if strict:
        raise RuntimeError(
            f"签名脚本 {name} 的 SHA256 与钉定值不符，已按 DLR_JS_STRICT_HASH=1 拒绝执行"
            f"（期望 {expected}，实际 {actual}）"
        )
    logger.warning(
        i18n.tr(
            "签名脚本 {name} 的 SHA256 与钉定值不符（期望 {expected}，实际 {actual}）；"
            "若你刚更新过该脚本请同步更新 utils._JS_SHA256_EXPECTED，否则请核查文件是否被篡改",
            name=name,
            expected=expected,
            actual=actual,
        )
    )


def get_compiled_js(js_path: str) -> object:
    # 读取并编译 JS 脚本，按 (路径, mtime) 缓存；被并发调用时由锁串行化。
    try:
        mtime = os.path.getmtime(js_path)
    except OSError:
        mtime = 0.0
    with _js_compile_lock:
        cached = _js_compile_cache.get(js_path)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        # 读字节再解码：哈希必须对原始字节计算（BOM / 换行形态都会影响摘要，
        # 用解码后的 str 反算会与文件实际内容不一致）
        with open(js_path, "rb") as f:
            raw = f.read()
        _check_js_hash(js_path, raw)
        source = raw.decode("utf-8")
        compiled = execjs.compile(source)
        _js_compile_cache[js_path] = (mtime, compiled)
        return compiled


async def run_js_async(js_path: str, func_name: str, *args: object) -> object:
    # 异步执行 JS 脚本中的 func_name（阻塞段整体丢线程池，事件循环不被冻结）。
    # 返回脚本调用结果（各平台脚本约定返回 str / dict，由调用方自行 cast）。
    def _sync_call() -> object:
        return cast(object, getattr(get_compiled_js(js_path), "call")(func_name, *args))

    return await asyncio.to_thread(_sync_call)


async def run_node_script_async(script_path: str, *args: str, timeout: float = 30.0) -> str:
    # 异步执行 node 脚本（subprocess.run 阻塞段丢线程池，事件循环不被冻结）。
    # 咪咕签名等「整段脚本 + 命令行参数」形态走此入口。
    def _sync_run() -> str:
        proc = subprocess.run(
            ["node", script_path, *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        return proc.stdout.strip()

    return await asyncio.to_thread(_sync_run)


# 优先使用 exejs（PyExecJS 的活跃维护继任者），未安装时回退到 PyExecJS
try:
    import exejs as execjs

    ProgramError = execjs.ExejsProgramError
except ImportError:
    import execjs  # type: ignore[no-redef]
    from execjs import ProgramError  # type: ignore[no-redef]

import configparser

from .logger import logger

OptionalStr = str | None
OptionalDict = dict[str, object] | None

# 表情符号匹配模式（模块级编译一次）：原实现在 remove_emojis 内每次调用都拼接 10 段字符串
# 构造约 400 字符的模式再 re.compile——既产生临时字符串分配，又要对长模式串做哈希查表。
# 该函数经 clean_name 被每个房间每轮多次调用（80+ 房间场景下每秒可达数百次），
# 提为模块级常量后省去拼接与编译查表开销，匹配语义完全不变。
_EMOJI_PATTERN = re.compile(
    "["
    + "\U0001f1e0-\U0001f1ff"  # flags (iOS)
    + "\U0001f300-\U0001f5ff"  # symbols & pictographs
    + "\U0001f600-\U0001f64f"  # emoticons
    + "\U0001f680-\U0001f6ff"  # transport & map symbols
    + "\U0001f700-\U0001f77f"  # alchemical symbols
    + "\U0001f780-\U0001f7ff"  # Geometric Shapes Extended
    + "\U0001f800-\U0001f8ff"  # Supplemental Arrows-C
    + "\U0001f900-\U0001f9ff"  # Supplemental Symbols and Pictographs
    + "\U0001fa00-\U0001fa6f"  # Chess Symbols
    + "\U0001fa70-\U0001faff"  # Symbols and Pictographs Extended-A
    + "\U00002702-\U000027b0"  # Dingbats
    + "]+",
    flags=re.UNICODE,
)


class Color:
    # 终端彩色输出常量类
    RED: str = "\033[31m"
    GREEN: str = "\033[32m"
    YELLOW: str = "\033[33m"
    BLUE: str = "\033[34m"
    MAGENTA: str = "\033[35m"
    CYAN: str = "\033[36m"
    WHITE: str = "\033[37m"
    RESET: str = "\033[0m"

    @staticmethod
    def print_colored(text: str, color: str) -> None:
        # 打印彩色文本
        print(f"{color}{text}{Color.RESET}")


P = ParamSpec("P")
R = TypeVar("R")


def _make_trace_error_guard(func: Callable[P, R], fallback: R) -> Callable[P, R]:
    # 错误追踪装饰器的共用实现（支持同步和异步函数）：吞掉异常并返回 fallback，
    # 日志同时标注函数名与兜底值类型，便于定位「错误被伪装成正常结果」的现场
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # 异步函数包装器：捕获并记录异常，返回 fallback
            try:
                return cast(R, await func(*args, **kwargs))
            except ProgramError:
                logger.warning("Failed to execute JS code. Please check if the Node.js environment")
                return fallback
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__) if e.__traceback__ else None
                error_line = tb[-1].lineno if tb else "unknown"
                error_info = (
                    f"message: type: {type(e).__name__}, {str(e)} in function {func.__name__} at line: {error_line}"
                    f", fallback type: {type(fallback).__name__}"
                )
                logger.error(error_info)
                return fallback

        return cast(Callable[P, R], async_wrapper)

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # 同步函数包装器：捕获并记录异常，返回 fallback
        try:
            return func(*args, **kwargs)
        except ProgramError:
            logger.warning("Failed to execute JS code. Please check if the Node.js environment")
            return fallback
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__) if e.__traceback__ else None
            error_line = tb[-1].lineno if tb else "unknown"
            error_info = (
                f"message: type: {type(e).__name__}, {str(e)} in function {func.__name__} at line: {error_line}"
                f", fallback type: {type(fallback).__name__}"
            )
            logger.error(error_info)
            return fallback

    return wrapper


def trace_error_decorator(func: Callable[P, R]) -> Callable[P, R]:
    # 错误追踪装饰器：吞掉异常并返回 {"is_live": False}。绝大多数被装饰函数（各平台
    # get_xxx_stream_data）返回含 is_live 键的 dict，调用方据其判定未开播。
    # 返回 str/tuple/None 的函数必须改用 trace_error_decorator_or_none，否则调用方会
    # 静默拿到一个 dict，把错误伪装成正常结果。
    return _make_trace_error_guard(func, cast(R, {"is_live": False}))


def trace_error_decorator_or_none(func: Callable[P, R]) -> Callable[P, R]:
    # trace_error_decorator 的类型匹配变体：出错返回 None，供返回 str/tuple 等类型的
    # 函数（login_*、get_*_info、get_*_tk）使用，调用方按 falsy 处理失败。
    return _make_trace_error_guard(func, cast(R, None))


def check_md5(file_path: str | Path) -> str:
    # 计算文件的 MD5 值
    with open(file_path, "rb") as fp:
        file_md5 = hashlib.md5(fp.read()).hexdigest()
    return file_md5


def unzip_file(zip_path: str | Path, extract_to: str | Path, delete: bool = True) -> None:
    # 解压 ZIP 文件到指定目录（含 Zip Slip 目录穿越校验 + 解压炸弹防护）。
    # node_install / ffmpeg_install 共用同一份实现——原先两处逐字重复，
    # 任一处打安全补丁都会漏掉另一处
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    extract_root = os.path.realpath(extract_to)
    # 解压炸弹防护（2026-09-12 审查 H-1）：恶意压缩包可声明极小尺寸但解压后膨胀到磁盘满 / OOM。
    # 设置上限：单文件 4GB、累计 8GB、压缩比上限 100x（正常压缩比通常 <10x，FFmpeg 二进制 ~70MB）。
    # 上限宁可误拦合法大包（用户改 max_total_size 重试），不可放过炸弹。
    _MAX_ENTRY_SIZE = 4 * 1024 * 1024 * 1024
    _MAX_TOTAL_SIZE = 8 * 1024 * 1024 * 1024
    _MAX_RATIO = 100

    total_uncompressed = 0
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # 防止 Zip Slip 目录穿越攻击：校验每个成员解压后的真实路径
        for member in zip_ref.namelist():
            member_path = os.path.realpath(os.path.join(extract_root, member))
            if not member_path.startswith(extract_root + os.sep) and member_path != extract_root:
                raise ValueError(f"Unsafe path in zip file: {member}")
            info = zip_ref.getinfo(member)
            # 单文件大小校验
            if info.file_size > _MAX_ENTRY_SIZE:
                raise ValueError(f"Zip entry too large (bomb?): {member} declared {info.file_size} bytes")
            total_uncompressed += info.file_size
            # 压缩比校验：恶意包可仅写 1 字节并循环引用，未压缩累计总和炸出数 TB；
            # zip 物理大小阈值取磁盘占用超 10MB 才有意义（小包算压缩比误差大）
            if info.compress_size > 0 and info.file_size > 10 * 1024 * 1024:
                ratio = info.file_size / info.compress_size
                if ratio > _MAX_RATIO:
                    raise ValueError(
                        f"Zip compression ratio too high (bomb?): {member} ratio={ratio:.1f}x "
                        f"({info.compress_size} -> {info.file_size})"
                    )
            if total_uncompressed > _MAX_TOTAL_SIZE:
                raise ValueError(f"Zip total uncompressed size too large (bomb?): {total_uncompressed} bytes")
        zip_ref.extractall(extract_to)

    if delete and os.path.exists(zip_path):
        os.remove(zip_path)


def dict_to_cookie_str(cookies_dict: Mapping[str, object]) -> str:
    # 将 cookie 字典转换为字符串格式
    cookie_str = "; ".join([f"{key}={value}" for key, value in cookies_dict.items()])
    return cookie_str


def read_ini_value(file_path: str | Path, section: str, key: str) -> str | None:
    # 从配置文件读取指定配置项的值（按**文件路径**读取，每次调用重新解析文件）
    # 关闭插值：值中的裸 %（如 cookie、时间格式）不应触发 InterpolationSyntaxError
    #
    # 2026-09-12 重命名（CODE_REVIEW_FIX_1 F-16）：原名 `read_config_value`，与
    # `src/config_io.read_config_value(config_parser, section, option, default_value)`
    # **同名但签名与语义都不同**——后者接收已解析的 parser、缺键会补写默认值回
    # 配置文件并返回 str；本函数接收文件路径、不写回、缺键返回 None。
    # 两个同名函数在 main.py（约 70 处调用 config_io 版）与 spider.py 间混用，
    # 极易传错参数（kwargs 数量与首个参数类型都不同）。
    # 因 config_io 版调用点过多，改本侧（调用点仅 spider.py 一处 + 单测）。
    config = configparser.ConfigParser(interpolation=None)

    try:
        _ = config.read(file_path, encoding="utf-8-sig")
    except Exception as e:
        print(i18n.tr("Error occurred while reading the configuration file: {e}", e=e))
        return None

    if section in config:
        if key in config[section]:
            return config[section][key]
        else:
            print(i18n.tr("Key [{key}] does not exist in section [{section}].", key=key, section=section))
    else:
        print(i18n.tr("Section [{section}] does not exist in the file.", section=section))

    return None


# F-16 兼容别名：保留旧名以免外部脚本/插件突然失效。
# 新代码请用 read_ini_value（与 config_io.read_config_value 区分）。
def read_config_value(file_path: str | Path, section: str, key: str) -> str | None:
    return read_ini_value(file_path, section, key)


def update_config(file_path: str | Path, section: str, key: str, new_value: str) -> None:
    # 更新配置文件中指定配置项的值
    # 关闭插值以避免 cookie 等含 % 的值被 BasicInterpolation 转义/反解析
    config = configparser.ConfigParser(interpolation=None)

    try:
        _ = config.read(file_path, encoding="utf-8-sig")
    except Exception as e:
        print(i18n.tr("An error occurred while reading the configuration file: {e}", e=e))
        return

    if section not in config:
        print(i18n.tr("Section [{section}] does not exist in the file.", section=section))
        return

    config[section][key] = new_value

    try:
        with open(file_path, "w", encoding="utf-8-sig") as configfile:
            config.write(configfile)
        print(
            i18n.tr(
                "The value of {key} under [{section}] in the configuration file has been updated.",
                key=key,
                section=section,
            )
        )
    except Exception as e:
        print(i18n.tr("Error occurred while writing to the configuration file: {e}", e=e))


def get_file_paths(directory: str) -> list[str]:
    # 递归获取指定目录下所有文件的绝对路径
    file_paths: list[str] = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


def remove_emojis(text: str, replace_text: str = "") -> str:
    # 从文本中移除表情符号（模式为模块级常量 _EMOJI_PATTERN，此处不再重复编译）
    return _EMOJI_PATTERN.sub(replace_text, text)


def remove_duplicate_lines(file_path: str | Path) -> None:
    # 移除文件中的重复行
    unique_lines: OrderedDict[str, None] = OrderedDict()
    text_encoding = "utf-8-sig"
    try:
        with open(file_path, "r", encoding=text_encoding) as input_file:
            for line in input_file:
                unique_lines[line.strip()] = None
    except UnicodeDecodeError:
        # 非 UTF-8 编码（如 GBK/UTF-16）时回退到系统默认编码读取
        with open(file_path, "r", encoding=None) as input_file:
            for line in input_file:
                unique_lines[line.strip()] = None
    with open(file_path, "w", encoding=text_encoding) as output_file:
        for line in unique_lines:
            _ = output_file.write(line + "\n")


def check_disk_capacity(file_path: str | Path, show: bool = False) -> float:
    # 检查指定文件所在磁盘的剩余空间（GB）
    absolute_path = os.path.abspath(file_path)
    directory = os.path.dirname(absolute_path)
    disk_usage = shutil.disk_usage(directory)
    disk_root = Path(directory).anchor
    free_space_gb = disk_usage.free / (1024**3)
    if show:
        print(
            f"{disk_root} Total: {disk_usage.total / (1024 ** 3):.2f} GB "
            + f"Used: {disk_usage.used / (1024 ** 3):.2f} GB "
            + f"Free: {free_space_gb:.2f} GB\n"
        )
    return free_space_gb


def handle_proxy_addr(proxy_addr: str | None) -> str | None:
    # 处理代理地址，自动添加 http 前缀
    # 已有协议前缀（http/https/socks 等）的地址不再二次添加
    if proxy_addr:
        if "://" not in proxy_addr:
            proxy_addr = "http://" + proxy_addr
    else:
        proxy_addr = None
    return proxy_addr


def generate_random_string(length: int) -> str:
    # 生成指定长度的随机字符串（大写字母 + 数字）
    characters = string.ascii_uppercase + string.digits
    random_string = "".join(random.choices(characters, k=length))
    return random_string


def jsonp_to_json(jsonp_str: str) -> OptionalDict:
    # 将 JSONP 格式字符串转换为 JSON 对象
    # re.DOTALL 支持跨行内容；回调名允许含点号（如 a.b(...)）
    pattern = r"([\w.]+)\((.*)\);?\s*$"
    match = re.search(pattern, jsonp_str, re.DOTALL)

    if match:
        _, json_str = match.groups()
        json_obj: dict[str, object] = cast(dict[str, object], json.loads(json_str))
        return json_obj
    else:
        raise Exception("No JSON data found in JSONP response.")


def replace_url(file_path: str | Path, old: str, new: str) -> None:
    # 替换文件中的 URL
    # 逐行匹配整行内容，避免子串替换误伤包含相同 URL 片段的其他行
    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()
    with open(file_path, "w", encoding="utf-8-sig") as f:
        for line in lines:
            if line.strip() == old:
                _ = f.write(new + "\n")
            elif old in line:
                _ = f.write(line.replace(old, new))
            else:
                _ = f.write(line)


def get_query_params(url: str, param_name: OptionalStr) -> dict[str, list[str]] | list[str]:
    # 从 URL 中获取查询参数
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    if param_name is None:
        return query_params
    else:
        values = query_params.get(param_name, [])
        return values


# 脱敏 URL / 代理地址中的凭据后再写日志：logs 下的日志会轮转保留多份，把带
# user:pass 的代理地址或带 signature/token 的直链直接写进去等于凭据长期落盘。
# 只抹凭据，保留 host/path 与其余查询参数，便于定位问题。
_PROXY_CREDENTIAL_RE = re.compile(r"(?i)(://)[^/@\s]+@")
_SECRET_QUERY_RE = re.compile(
    r"(?i)((?:signature|token|access_token|apikey|api_key|secret|key|x-bogus|a-bogus|a_bogus|ms_token|nonce|sid)=)[^&\s]*"
)


def mask_credentials(text: str) -> str:
    # 抹去代理凭据（scheme://user:pass@ → scheme://***@）与查询串里的签名/token 类参数值
    masked = _PROXY_CREDENTIAL_RE.sub(r"\1***@", text)
    return _SECRET_QUERY_RE.sub(r"\1***", masked)
