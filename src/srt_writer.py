# SRT 字幕写入器。
#
# 按固定时长（segment_seconds）分片输出 SRT 文件，文件名与录像分片对齐：
#  {base}_{seg:03d}.srt  （对应录像 {base}_{seg:03d}.flv）
# 单文件模式（segment_seconds<=0 或 None）输出 {base}.srt。
#
# 时间轴基准：默认以 start() 锚定时刻（collector 启动 ≈ 录像起点）为 T0，
# 并立即创建 SRT 文件；未调 start() 时兜底以首条弹幕到达为 T0。每片内时间轴
# 重置为 0，保证与 ffmpeg segment + reset_timestamps 的视频 PTS 对齐（秒级）。

from __future__ import annotations

import threading
import time
from typing import Optional, TextIO

import i18n
from src.logger import logger

# WD-03：SRT 文件句柄打开失败后的重试间隔（秒）。目录被删/磁盘满等瞬时故障恢复后
# 需要自愈，否则本片（默认 30 分钟）内的弹幕会被静默丢弃。
_OPEN_RETRY_INTERVAL = 10.0
# WD-03：close() 等待写锁的超时（秒）。见 close() 说明。
_CLOSE_LOCK_TIMEOUT = 5.0
# MIN-2236③：close() 成功后写入器进入终态（self._closed），此后到达的弹幕一律丢弃、
# 不再重开句柄。终态判定放在唯一的开句柄入口 _open_segment()，原因见该处注释。


# 把相对秒数 seconds 格式化为 SRT 时间戳字符串 "HH:MM:SS,mmm"；负数按 0 处理，毫秒四舍五入并逐级进位。
def _format_ts(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    if ms == 1000:  # 四舍五入进位
        ms = 0
        s += 1
        if s == 60:
            s = 0
            m += 1
            if m == 60:
                m = 0
                h += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# 清洗弹幕文本，避免污染 SRT 结构：user_name/message 均为外部可控输入，换行会截断字幕块、
# "-->" 会被解析器当成新的时间轴行（可伪造任意字幕）；替换为可见字符而非直接删除，保留可读性。
def _sanitize_srt_text(text: str) -> str:
    return text.replace("\r", " ").replace("\n", " ").replace("-->", "->")


# SRT 字幕写入器：线程安全地按分片时长切换输出文件，并把弹幕按片内相对时间写成 SRT 条目。
class SrtWriter:
    # 初始化写入器：base_filename 为录像文件去掉扩展名后的前缀（如 .../主播名_2026-08-12_21-00-00），
    # segment_seconds 为分片时长（<=0/None 为单文件模式），display_duration 为单条弹幕最小显示秒数
    # （避免播放器瞬闪）；只做字段与锁初始化，不创建文件。
    def __init__(
        self,
        base_filename: str,
        segment_seconds: Optional[float] = 1800.0,
        display_duration: float = 1.5,
    ) -> None:
        self._base = base_filename
        self._seg_seconds = segment_seconds if segment_seconds and segment_seconds > 0 else None
        self._display_duration = display_duration

        self._lock = threading.Lock()
        self._t0: Optional[float] = None  # monotonic 基准（start() 锚定的录像起点）
        self._current_seg = -1
        self._index = 0  # 当前片内序号
        self._fp: Optional[TextIO] = None
        self._last_end: Optional[float] = None  # 上一条结束时间，用于密集弹幕错开
        self._last_open_attempt = 0.0  # WD-03：句柄打开失败的退避基准（monotonic）
        # MIN-2236③：close() 之后不再接受任何写入（终态位），_discarded_after_count
        # 只在首条丢弃时留一条 debug，避免高频房间刷屏
        self._closed = False
        self._discarded_after_count = 0

    # 锚定时间轴 T0（录像起点）并立即创建第 0 片 SRT 文件（哪怕尚无弹幕）；
    # now 为 time.monotonic()，不传则内部取。幂等：已锚定则忽略。
    # 未调用时 write() 以首条弹幕为 T0 兜底（旧行为，兼容直接写调用的测试）。
    def start(self, now: Optional[float] = None) -> None:
        if now is None:
            now = time.monotonic()
        with self._lock:
            if self._t0 is not None:
                return
            self._t0 = now
            self._current_seg = 0
            self._index = 0
            self._open_segment(0)

    # 兜底初始化（需持锁调用）：未调用过 start() 时以 now 作为 T0 并打开第 0 片文件，无返回值。
    def _ensure_started(self, now: float) -> None:
        if self._t0 is None:
            self._t0 = now
            self._current_seg = 0
            self._index = 0
            self._open_segment(0)

    # 以追加模式打开第 seg 片 SRT 文件（UTF-8），并重置片内序号与上一条结束时间，无返回值。
    # WD-03：失败时不再向上抛（见 write 中的节流重试），故此处捕获 OSError 并保持 _fp 为 None。
    def _open_segment(self, seg: int) -> None:
        # MIN-2236③：终态位判定放在这个**唯一的开句柄入口**，而不是只放在 write() 里——
        # 三条路径（start() / 分片切换 / WD-03 的节流重试）全部在此收口。
        # close() 之后重开同一文件的后果不是「写坏了字幕」而是**块号回卷**：
        # 本方法会把 self._index 归 0，而文件以追加模式打开、旧内容还在，
        # 于是同一个 .srt 里出现 1,2,…,N,1,2,… —— 直接违反 MIN-24① 确立的
        # 「块号单调不回卷」不变量（SRT 规范要求块序号递增，播放器会错乱/截断）。
        if self._closed:
            self._fp = None
            return
        path = self._segment_path(seg)
        # 追加模式：若文件已存在（如重连后继续），保留已有内容续写
        try:
            self._fp = open(path, "a", encoding="utf-8")
        except OSError:
            # 目录被删/权限不足/磁盘满：保持 _fp 为 None，由 write() 按间隔重试。原实现让异常冒泡到
            # 调用方，而 _open_segment 只在分片切换时被调用——于是本片剩余时间（默认 1800s）内再不
            # 会重试，write 里的 `if self._fp is not None` 把整片弹幕静默跳过，且只在首次失败时有 1 条 warning。
            self._fp = None
        self._index = 0
        self._last_end = None

    # 根据分片序号 seg 返回 SRT 文件路径：单文件模式为 "{base}.srt"，否则为 "{base}_{seg:03d}.srt"
    # （与 ffmpeg 分段模板 _%03d 落盘的录像文件 _000/_001… 对齐）。
    def _segment_path(self, seg: int) -> str:
        if self._seg_seconds is None:
            return f"{self._base}.srt"
        return f"{self._base}_{seg:03d}.srt"

    # 写入一条弹幕 "user_name: message"：按 now（monotonic，缺省内部取）算出片号并按需切片，
    # 生成片内起止时间戳后立即 flush 落盘；全程持锁保证多线程安全，无返回值。
    def write(self, user_name: str, message: str, now: Optional[float] = None) -> None:
        if now is None:
            now = time.monotonic()
        with self._lock:
            if self._closed:
                # MIN-2236③：close() 之后再写一律丢弃（终态判定与块号回卷后果见 _open_segment）。
                # 只 debug 不外抛：调用方是采集线程的 on_message 回调，抛出会污染录制主流程。
                self._discarded_after_count += 1
                if self._discarded_after_count == 1:
                    logger.debug(i18n.tr("[弹幕采集]SRT 文件已关闭，后续到达的弹幕一律丢弃"))
                return
            self._ensure_started(now)
            assert self._t0 is not None  # _ensure_started 保证已初始化
            rel = now - self._t0  # 距 T0 总秒数
            if self._seg_seconds is not None:
                seg = int(rel // self._seg_seconds)
                if seg != self._current_seg:
                    self._close_locked()
                    self._current_seg = seg
                    self._open_segment(seg)
                start = rel - seg * self._seg_seconds  # 片内时间
            else:
                start = rel

            # MIN-24① 修复：句柄缺失时的「节流重试开片」必须发生在**生成条目之前**——_open_segment()
            # 会把片内状态清零（_index=0 / _last_end=None），旧顺序是先自增 _index 并拼好 line、再重试
            # 开片 → 计数被清零而已拼好的行仍带着清零前的序号，同一个 .srt 内因此出现重复块号与非单调
            # 时间轴（SRT 规范要求块序号递增）。前置后：重试成功 → 本片首条从 1 开始；重试仍失败 →
            # 本条按原逻辑丢弃（_fp 为 None 时不写），序号也不会被凭空跳大。
            if self._fp is None:
                # WD-03：句柄缺失（首次 open 失败 / 写入中被关闭）时按间隔重试打开，否则本片剩下的
                # 弹幕会被静默丢弃且无任何提示。
                _now = time.monotonic()
                if _now - self._last_open_attempt >= _OPEN_RETRY_INTERVAL:
                    self._last_open_attempt = _now
                    self._open_segment(self._current_seg)

            # 计算结束时间：至少 display_duration，且不与上一条重叠过紧
            end = start + self._display_duration
            if self._last_end is not None and end <= self._last_end:
                end = self._last_end + self._display_duration
            # 片内上界：末条弹幕的 end 不得越过本片时长，否则会与片边界及下一片首条
            # 时间轴重叠（下一片 _open_segment 会把片内时间轴归 0 重算）。
            # max(start, ...) 兜底保证 start <= end，不产生非法区间。
            if self._seg_seconds is not None:
                end = max(start, min(end, float(self._seg_seconds)))
            self._last_end = end

            self._index += 1
            # 弹幕原文与用户名均为外部可控：换行会破坏 SRT 块结构、"-->" 会被解析成
            # 伪时间轴行，必须先清洗再拼行。
            line = (
                f"{self._index}\n"
                f"{_format_ts(start)} --> {_format_ts(end)}\n"
                f"{_sanitize_srt_text(user_name)}: {_sanitize_srt_text(message)}\n\n"
            )
            if self._fp is not None:
                self._fp.write(line)
                self._fp.flush()

    # 需持锁调用的内部关闭：flush 并关闭当前文件句柄后置空，异常忽略，无返回值。
    def _close_locked(self) -> None:
        if self._fp is not None:
            try:
                self._fp.flush()
                self._fp.close()
            except Exception:
                # 吞没即正确：调用点是「切片」与「close()」两条收尾路径，句柄已不可用
                # （磁盘满/文件被外部删除）时再抛错只会让录制线程收到弹幕写失败的异常，
                # 而 _fp 随后一律置空、内容已由 flush 尽力落盘，无进一步可恢复动作。
                pass
            self._fp = None

    # 对外关闭接口：加锁后落盘并关闭当前 SRT 文件，可重复调用，无返回值。
    # WD-03：加锁带超时。调用方是录制线程（collector.stop）；若写线程正持锁卡在
    # 阻塞式 flush()（网络盘/USB 掉线等），无超时的 acquire 会把录制线程无限期挂住——
    # 那比丢几条弹幕严重得多。超时即放弃本轮关闭（句柄由进程结束回收），并留一条告警。
    def close(self) -> None:
        if not self._lock.acquire(timeout=_CLOSE_LOCK_TIMEOUT):
            logger.warning(
                i18n.tr(
                    "[弹幕采集]SRT 关闭等待锁超时（{seconds}s），跳过本次关闭以免阻塞录制线程",
                    seconds=_CLOSE_LOCK_TIMEOUT,
                )
            )
            return
        try:
            self._close_locked()
            # MIN-2236③：只有真正拿到锁、完成关闭的那一轮才置终态位。
            # 上面的超时分支刻意不置位——那次关闭作废（句柄仍被写线程持有），
            # 调用方仍可再次 close()，「可重复调用」的既有契约不变。
            self._closed = True
        finally:
            self._lock.release()
