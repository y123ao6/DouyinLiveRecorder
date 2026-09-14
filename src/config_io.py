# -*- coding: utf-8 -*-
import configparser
import datetime
import io
import os
import re
import shutil
import time

from loguru import logger

import i18n
import main
from src import utils
from src.ffmpeg_proc import _get_error_line

# 配置文件与文件工具（独立模块）
#
# 负责：
# - 安全更新 URL 配置文件内容（update_file）
# - 从配置文件删除指定行（delete_line）
# - 按 URL 更新配置行主播名字段（update_anchor_name，主播名自动同步）
# - 从 config.ini 读取并兜底写回配置值（read_config_value）
# - 配置数值安全转换（_safe_int / _safe_float）
# - 配置文件备份（backup_file / backup_file_start）
#
# 需要读取/写入 main 的少量配置与文件锁全局变量
# （config_file / url_config_file / backup_dir / text_encoding / file_update_lock / ini_URL_content），
# 通过 `import main` 在运行时惰性读写，避免循环导入与 __main__ 二次执行。


# 段级精确替换（2026-09-12 审查 6.1）：old_str 仅在「等于整行（去行尾换行与首尾空白后）」
# 或「等于行内某个半角/全角逗号分隔段（strip 后）」时才替换为 new_str。返回重写后的
# 整行文本（保留原行尾与多逗号），未命中返回 None。
# 原实现为整行 substring 替换（str.replace），URL 前缀重叠时（如 .../room1 与 .../room12）
# 会把别的配置行静默改坏，滥用者只在下次“未生效”才会发现。
def _rewrite_line_by_match(text_line: str, old_str: str, new_str: str) -> str | None:
    raw = text_line.rstrip("\r\n")
    eol = text_line[len(raw) :]
    target = old_str.strip()
    if not target:
        return None
    # 整行匹配：raw.strip() 同时容忍首尾空白；new_str 的行尾须补 eol；
    # whole-line 与 segment 两种情况下都需 rstrip 掉 new_str 的潜在换行以免双换行
    cleaned_new = new_str.rstrip("\r\n")
    if raw.strip() == target:
        return f"{cleaned_new}{eol}"
    # 段级匹配：按半角/全角逗号切分，保留分隔符。new_str 可含逗号（“new_url,主播: 名称”）
    # 与原 substring 语义兼容，且不会误伤相似前缀行
    parts = re.split(r"([,，])", raw)
    hit = False
    for i in range(0, len(parts), 2):
        if parts[i].strip() == target:
            parts[i] = cleaned_new
            hit = True
    if not hit:
        return None
    return "".join(parts) + eol


# 把 file_path 中所有 old_str 替换为 new_str（start_str 非空时给命中行加该前缀，如 "#" 注释掉），
# 顺带去重相同行；返回实际生效的字符串（失败时返回 old_str）
def update_file(file_path: str, old_str: str, new_str: str, start_str: str | None = None) -> str | None:
    # 安全更新文件内容（加锁防止并发写入）
    if old_str == new_str and start_str is None:
        return old_str
    with main.file_update_lock:
        file_data: list[str] = []
        # 2026-09-12 审查（低危 6.1）：原 list 成员判定为 O(n)，80+ 房间场景退化为 O(N²)；
        # 换为 set 保持 O(1) 插入与判定，同时保留首次出现顺序（set 不保证，但「仅记录是否见过」
        # 的用法重放为顺序 + 去重即可）
        seen: set[str] = set()
        try:
            # newline=""：读/写均不做换行符翻译，保留文件原有的 \n / \r\n 行尾风格，
            # 配合下方的原子写实现字节级 round-trip（Windows 下的 CRLF 不会走 universal newlines
            # 被错误转换为 LF）
            with open(file_path, "r", encoding=main.text_encoding, newline="") as f:
                for text_line in f:
                    rewritten = _rewrite_line_by_match(text_line, old_str, new_str)
                    if rewritten is not None:
                        text_line = f"{start_str}{rewritten}" if start_str else rewritten
                    if text_line not in seen:
                        seen.add(text_line)
                        file_data.append(text_line)
        except (RuntimeError, UnicodeDecodeError) as e:
            logger.error(
                i18n.tr("错误信息: {e} 发生错误的行数: {get_error_line}", e=e, get_error_line=_get_error_line(e))
            )
            # 读取失败时尝试用初始内容恢复，避免文件被清空
            if main.ini_URL_content:
                _ = _atomic_write_text(file_path, main.ini_URL_content)
                return old_str
            return old_str
        if not file_data:
            return old_str
        joined = "".join(file_data)
        # 2026-09-12 审查 6.1：原 open(..., "w") 是 truncate+write 非原子，读方（主循环、GUI）
        # 可能在写入窗口内读到空/半写文件；改同目录临时文件 + os.replace 原子写
        if not _atomic_write_text(file_path, joined):
            return old_str
        # 更新快照为当前已落盘内容，使后续异常恢复只回滚到最近一次成功修改，而非整个循环开始时的旧内容
        main.ini_URL_content = joined
        return new_str


# 原子写文本：同目录临时文件写完后 os.replace 覆盖，读方只会看到旧/新完整内容。
# 返回是否成功落盘（False 表示在写临时文件 / replace 阶段发生 OSError）。
def _atomic_write_text(file_path: str, text: str) -> bool:
    tmp = f"{file_path}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding=main.text_encoding, newline="") as f:
            _ = f.write(text)
        os.replace(tmp, file_path)
    except OSError as e:
        logger.warning(
            i18n.tr(
                "原子写失败（已保留原文件）: {file_path} - {type_name}: {e}",
                file_path=file_path,
                type_name=type(e).__name__,
                e=e,
            )
        )
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False
    return True


# 将 URL 配置文件中指定 URL 所在行的主播名字段更新为 new_name（行内无主播名字段时追加），
# 保留画质段/注释前缀/行尾换行；返回是否发生了变更（未命中/已是目标名/写失败均返回 False）
def update_anchor_name(url: str, new_name: str) -> bool:
    # 主播名自动同步：按 URL 精确定位配置行（段级匹配，避免 URL 前缀相似的行误命中），
    # 持锁读写避免与录制线程的 update_file / Web API 写入并发半写
    if not url or not new_name:
        return False
    with main.file_update_lock:
        if not os.path.exists(main.url_config_file):
            return False
        try:
            # newline=""：读/写均不做换行符翻译，保留文件原有的 \n / \r\n 行尾风格
            with open(main.url_config_file, "r", encoding=main.text_encoding, newline="") as f:
                lines = f.readlines()
        except (RuntimeError, UnicodeDecodeError, OSError) as e:
            logger.error(i18n.tr("读取 URL 配置失败，跳过主播名更新: {e}", e=e))
            return False
        changed = False
        out_lines: list[str] = []
        for raw_line in lines:
            rewritten = _rewrite_anchor_field(raw_line, url, new_name)
            if rewritten is not None:
                changed = True
                out_lines.append(rewritten)
            else:
                out_lines.append(raw_line)
        if not changed:
            return False
        joined = "".join(out_lines)
        try:
            with open(main.url_config_file, "w", encoding=main.text_encoding, newline="") as f:
                _ = f.write(joined)
            # 更新快照为当前已落盘内容（与 update_file 保持一致的异常恢复基线）
            main.ini_URL_content = joined
        except OSError as e:
            logger.warning(i18n.tr("主播名写回 URL 配置失败（已忽略，下轮重试）: {e}", e=e))
            return False
        return True


# 重写单行配置的主播名字段；行不匹配 URL 或已是目标名时返回 None（无需变更）
def _rewrite_anchor_field(raw_line: str, url: str, new_name: str) -> str | None:
    # 行格式: [画质,]URL[,主播: 名称]，# 前缀表示注释（禁用）——重写时全部保留
    stripped = raw_line.rstrip("\r\n")
    eol = raw_line[len(stripped) :]
    # 分离注释前缀（保留原有 # 数量）
    comment_prefix = ""
    body = stripped
    if body.lstrip().startswith("#"):
        idx = body.find("#")
        comment_prefix = body[: idx + 1]
        body = body[idx + 1 :]
    if not body.strip():
        return None
    # 段级 URL 匹配：防止 URL 前缀相似（如 /1 与 /12）导致误改他行
    segments = [seg.strip() for seg in re.split(r"[,，]", body)]
    if url not in segments:
        return None
    # 定位主播名字段：取最后一个「主播:」/「主播：」之后的尾段整体替换（名字可含空格）；
    # 全角冒号行统一重写为半角格式（与 main.py 的行解析约定一致）
    idx = max(body.rfind("主播:"), body.rfind("主播："))
    if idx >= 0:
        head = body[:idx].rstrip()
        if body[idx + 3 :].strip() == new_name:
            return None  # 已是目标名，幂等跳过
        rebuilt = f"{head}主播: {new_name}"
    else:
        # 行内无主播名字段：在行尾追加（URL 段原样保留）
        rebuilt = f"{body.rstrip()},主播: {new_name}"
    return f"{comment_prefix}{rebuilt}{eol}"


# 从 file_path 中删除与 del_line 完全相同的行，delete_all=True 时删除全部匹配行；无返回值
def delete_line(file_path: str, del_line: str, delete_all: bool = False) -> None:
    # 从文件中删除指定行
    # delete_all=False 时仅删除第一个匹配行
    with main.file_update_lock:
        try:
            with open(file_path, "r", encoding=main.text_encoding) as f:
                lines = f.readlines()
        except (OSError, UnicodeDecodeError) as e:
            logger.error(i18n.tr("读取 URL 配置失败，跳过删除: {e}", e=e))
            return
        deleted_one = False
        out: list[str] = []
        for txt_line in lines:
            if del_line == txt_line and (delete_all or not deleted_one):
                deleted_one = True
                continue
            out.append(txt_line)
        if not deleted_one:
            return
        # 2026-09-12 审查 6.5：原 r+truncate 式写中途崩溃会清空整个 URL_config.ini；
        # 改临时文件 + os.replace 原子写（读方只见旧/新完整内容）
        if not _atomic_write_text(file_path, "".join(out)):
            return
        # 同步更新 URL 配置快照，与 update_file 保持一致的异常恢复基线
        if file_path == main.url_config_file:
            main.ini_URL_content = "".join(out)


def read_config_value(
    config_parser: configparser.RawConfigParser, section: str, option: str, default_value: str | int | float | bool = ""
) -> str:  # 从 config_parser 读取 section/option 的配置值；缺节或缺键时用 default_value 补写回配置文件
    # 并返回该默认值；返回值一律为字符串
    # 读取配置文件指定节键值
    try:
        if "录制设置" not in config_parser.sections():
            config_parser.add_section("录制设置")
        if "推送配置" not in config_parser.sections():
            config_parser.add_section("推送配置")
        if "Cookie" not in config_parser.sections():
            config_parser.add_section("Cookie")
        if "Authorization" not in config_parser.sections():
            config_parser.add_section("Authorization")
        if "账号密码" not in config_parser.sections():
            config_parser.add_section("账号密码")
        return config_parser.get(section, option)
    except configparser.NoSectionError, configparser.NoOptionError:
        # 兜底创建 section（白名单外的 section 直接 set 会抛 NoSectionError），
        # 并持 file_update_lock 写回，避免与录制线程的 update_config 并发半写。
        with main.file_update_lock:
            if section not in config_parser.sections():
                config_parser.add_section(section)
            config_parser.set(section, option, str(default_value))
            # 写回失败（瞬时占用 / 并发进程 / 编辑器锁 / 只读挂载）仅记 warning 并返回默认值，
            # 不再抛出——避免「任何缺键 + 配置不可写」导致整个 app 在 import 阶段崩溃。
            # 与 backup_file 的 best-effort 模式保持一致。
            # 先在内存完整序列化、成功后才落盘：键名含 = / : 等 configparser 分隔符时
            # write() 会抛 InvalidWriteError（Python 3.13+），直接写文件会把配置截断损坏；
            # 失败时回滚内存态，避免坏键滞留解析器导致后续缺键写回连环失败。
            try:
                buffer = io.StringIO()
                config_parser.write(buffer)
                # 2026-09-12 审查 6.5：原 open(...,"w") 是 truncate+write 非原子；
                # 改临时文件 + os.replace 原子写（与 update_file / delete_line 保持一致）
                if not _atomic_write_text(main.config_file, buffer.getvalue()):
                    _ = config_parser.remove_option(section, option)
            except (OSError, configparser.Error) as e:
                logger.warning(
                    i18n.tr(
                        "配置项 {section}/{option} 缺省值写回失败（已忽略）: {type_name}: {e}",
                        section=section,
                        option=option,
                        type_name=type(e).__name__,
                        e=e,
                    )
                )
                _ = config_parser.remove_option(section, option)
        return str(default_value)


# 把配置项 value 安全转为 int；为空或非法时打印告警并返回 default
def _safe_int(value: str | None, default: int) -> int:
    # 配置数值安全转换：非法值记录告警并回退默认，避免 main() 主循环因 ValueError 崩溃
    try:
        return int(str(value).strip())
    except TypeError, ValueError:
        logger.warning(i18n.tr("配置项数值非法: {value}，使用默认值 {default}", value=repr(value), default=default))
        return default


# 把配置项 value 安全转为 float；为空或非法时打印告警并返回 default
def _safe_float(value: str | None, default: float) -> float:
    # 配置数值安全转换（浮点版）
    try:
        return float(str(value).strip())
    except TypeError, ValueError:
        logger.warning(i18n.tr("配置项数值非法: {value}，使用默认值 {default}", value=repr(value), default=default))
        return default


# 备份配置文件到 backup_config 目录；异常内部吞掉，无返回值
def backup_file(file_path: str, backup_dir_path: str, limit_counts: int = 6) -> None:
    # 备份配置文件到 backup_config 目录
    try:
        if not os.path.exists(backup_dir_path):
            os.makedirs(backup_dir_path)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file_name = os.path.basename(file_path) + "_" + timestamp
        backup_file_path = os.path.join(backup_dir_path, backup_file_name).replace("\\", "/")
        _ = shutil.copy2(file_path, backup_file_path)

        files = os.listdir(backup_dir_path)
        _files = [f for f in files if f.startswith(os.path.basename(file_path))]
        _files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir_path, x)))

        while len(_files) > limit_counts:
            oldest_file = _files[0]
            try:
                os.remove(os.path.join(backup_dir_path, oldest_file))
            except OSError as e:
                # 旋转删除为尽力而为：删除失败（沙箱回收站不可用 / 文件被占用）不应使备份整体失败
                logger.warning(i18n.tr("清理过期备份 {oldest_file} 失败（已保留）：{e}", oldest_file=oldest_file, e=e))
                break
            _files = _files[1:]

    except Exception as e:
        logger.error(i18n.tr("\r备份配置文件 {file_path} 失败：{e}", file_path=file_path, e=e))


# 守护线程主体：每 10 分钟比对 config.ini / URL_config.ini 的 MD5，仅在内容变化时备份；无入参，死循环不返回
def backup_file_start() -> None:
    # 启动时备份文件（首次运行触发）
    config_md5 = ""
    url_config_md5 = ""

    while True:
        try:
            if os.path.exists(main.config_file):
                new_config_md5 = utils.check_md5(main.config_file)
                if new_config_md5 != config_md5:
                    backup_file(main.config_file, main.backup_dir)
                    config_md5 = new_config_md5

            if os.path.exists(main.url_config_file):
                new_url_config_md5 = utils.check_md5(main.url_config_file)
                if new_url_config_md5 != url_config_md5:
                    backup_file(main.url_config_file, main.backup_dir)
                    url_config_md5 = new_url_config_md5
        except Exception as e:
            logger.error(i18n.tr("备份配置文件失败, 错误信息: {e}", e=e))
        # sleep 必须在 try 外：否则 check_md5/backup 持续失败时异常分支不等待，
        # 守护线程退化成紧循环空转，疯狂刷日志并空耗 CPU
        time.sleep(600)
