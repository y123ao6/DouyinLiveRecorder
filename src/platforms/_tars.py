# 极简 Tars 编解码器（仅覆盖虎牙弹幕所需类型）。
#
# 参照 tars 官方协议：
# - 头字节：高4位 tag，低4位 type；tag==15 时下一字节为扩展 tag。
# - type: 0=INT1 1=INT2 2=INT4 3=INT8 4=FLOAT 5=DOUBLE 6=STRING1 7=STRING4
#  8=MAP 9=LIST 10=STRUCT_BEGIN 11=STRUCT_END 12=ZERO_TAG 13=SIMPLE_LIST
#
# 解码用 peek（不消费）判定字段，支持跳过低 tag 字段与未知 tag 字段（服务器会增减字段）。
# 编码仅用于虎牙 join 命令。

from __future__ import annotations

import struct
from typing import Any, Callable, Optional, Tuple

# Tars 字段类型编号（与模块头 type 枚举一一对应，供各 read/skip 分支判定用）
INT1, INT2, INT4, INT8, FLOAT, DOUBLE, STRING1, STRING4 = 0, 1, 2, 3, 4, 5, 6, 7
MAP, LIST, STRUCT_BEGIN, STRUCT_END, ZERO_TAG, SIMPLE_LIST = 8, 9, 10, 11, 12, 13


# Tars 解码流：在 bytes 缓冲上按 tag 顺序读取各类字段，内部维护游标 _pos。
class TarsInputStream:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos = 0

    # ---- 基础 ----
    # CR-03 修复：统一的边界校验入口。旧实现把协议里的长度字段直接当游标增量使用，且只判
    # 「未越上界」不判负数——负长度使切片返回空、游标回退越过刚消费的头字节，而 _goto /
    # finish_struct / _skip_to_struct_end 都是 while True 且隐含「每轮至少前进 1 字节」的假设，
    # 于是回到同一字段头反复读到同一负值、反复回退，形成确定性死循环。更糟的是 _peek_field 只判
    # _pos >= len(data)，负下标走 Python 负索引合法读到缓冲区尾部字节，不会抛 IndexError 自曝，
    # 而是持续错解析——表现为弹幕线程 100% CPU 挂死且任何 try/except 都拦不住（它不是异常）。
    # 所有长度消费点必须经此校验，把不可恢复的死循环降级为可捕获的 ValueError。
    def _need(self, n: int) -> int:
        if n < 0 or self._pos + n > len(self._data):
            raise ValueError(f"bad tars length: pos={self._pos} len={n} total={len(self._data)}")
        return n

    # 统一的游标推进入口（含边界校验）：任何从协议里读出的长度都必须经此消费
    def _advance(self, n: int) -> None:
        self._pos += self._need(n)

    # 断言本轮循环确实推进了游标，防止 skip 逻辑在某些类型上原地不动而无限循环
    def _assert_progress(self, before: int) -> None:
        if self._pos <= before:
            raise ValueError(f"tars parse stuck: pos={self._pos} (no progress from {before})")

    # 预读下一个字段头但不移动游标，返回 (type, tag)；缓冲读完返回 None。
    def _peek_field(self) -> Optional[Tuple[int, int]]:
        # 本方法**不得**动 _pos：_goto / _skip_to_struct_end / finish_struct 三处 while 循环
        # 都靠「peek 后自行决定消费」前进。
        if self._pos >= len(self._data):
            return None
        b = self._data[self._pos]
        typ = b & 0x0F
        tag = (b & 0xF0) >> 4
        if tag == 15 and self._pos + 1 < len(self._data):
            # 官方 Tars 语义：头字节高4位为 15 时，tag 由下一字节整体替换（非累加）。
            # 2026-09-12 审查：原 tag += 写法在 tag≥15 字段上读出错误 tag，
            # 后续字段全部错位（虎牙当前 tag≤6 未触发，前向兼容修正）。
            tag = self._data[self._pos + 1]
        return typ, tag

    # 消费并返回下一个字段头 (type, tag)；tag==15 时再吃一个字节作为扩展 tag。
    def _take_head(self) -> Tuple[int, int]:
        b = self._data[self._pos]
        self._pos += 1
        typ = b & 0x0F
        tag = (b & 0xF0) >> 4
        if tag == 15:
            # 同 _peek_field：扩展 tag 为替换语义（非累加）
            tag = self._data[self._pos]
            self._pos += 1
        return typ, tag

    # 按类型 typ 跳过已消费头之后的字段体（容器类型递归跳过其元素）；未知类型抛 ValueError。
    def _skip(self, typ: int) -> None:
        if typ in (INT1,):
            self._advance(1)
        elif typ == INT2:
            self._advance(2)
        elif typ in (INT4, FLOAT):
            self._advance(4)
        elif typ in (INT8, DOUBLE):
            self._advance(8)
        elif typ == STRING1:
            n = self._data[self._pos]
            self._advance(1 + n)
        elif typ == STRING4:
            n = struct.unpack_from(">i", self._data, self._pos)[0]
            self._advance(4 + n)
        elif typ == SIMPLE_LIST:
            # 官方 Tars: 元素类型头(几乎总是 BYTE tag0) + 长度(自描述整数域, 非固定4字节)。
            # 本文件所有协议内长度（SIMPLE_LIST / LIST 的 size / 字符串与字节串长度）同此语义。
            self._take_head()
            n = self.read_int(0)
            self._advance(n)
        elif typ == LIST:
            n = self.read_int(0)
            # 每个元素至少占 1 字节，故元素数不可能超过剩余字节数——否则是损坏帧，
            # 直接拒绝而不是照着伪造的 size 空转数十亿次（旧实现会被恶意/损坏帧拖死）
            if n > len(self._data):
                raise ValueError(f"bad tars list size: {n}")
            for _ in range(n):
                t2, _ = self._take_head()
                self._skip(t2)
        elif typ == MAP:
            n = self.read_int(0)
            # 同理：每个键值对至少占 2 字节
            if n > len(self._data):
                raise ValueError(f"bad tars map size: {n}")
            for _ in range(n):
                t2, _ = self._take_head()
                self._skip(t2)
                t2, _ = self._take_head()
                self._skip(t2)
        elif typ == STRUCT_BEGIN:
            self._skip_to_struct_end()
        elif typ in (STRUCT_END, ZERO_TAG):
            pass
        else:
            raise ValueError(f"Unknown tars type: {typ}")

    # 跳过整个结构体体部，直到吃掉配对的 STRUCT_END（支持嵌套），无返回值。
    def _skip_to_struct_end(self) -> None:
        while True:
            f = self._peek_field()
            if f is None:
                return
            typ, _ = f
            if typ == STRUCT_END:
                self._take_head()
                return
            _before = self._pos
            self._take_head()
            self._skip(typ)
            # CR-03：本轮无任何推进即为解析卡死，抛错而非让调用方线程挂死
            self._assert_progress(_before)

    # ---- 字段读取 ----
    # 定位到目标 tag 字段并消费其头字节，返回 (type, tag)；
    # 沿途跳过更小 tag 的字段，遇 STRUCT_END/更大 tag/EOF 则返回 None 且不消费。
    def _goto(self, tag: int) -> Optional[Tuple[int, int]]:
        while True:
            f = self._peek_field()
            if f is None:
                return None
            typ, cur_tag = f
            if typ == STRUCT_END or cur_tag > tag:
                return None
            _before = self._pos
            self._take_head()
            if cur_tag == tag:
                return (typ, tag)
            self._skip(typ)
            # CR-03：本轮无任何推进即为解析卡死，抛错而非让调用方线程挂死
            self._assert_progress(_before)

    # 读取 tag 位置的整数（兼容 INT1/2/4/8 与 ZERO_TAG）；字段缺失或类型不符返回 default。
    def read_int(self, tag: int, default: Any = 0) -> Any:
        found = self._goto(tag)
        if found is None:
            return default
        typ, _ = found
        if typ == ZERO_TAG:
            return 0
        if typ == INT1:
            v = struct.unpack_from(">b", self._data, self._pos)[0]
            self._pos += 1
            return v
        if typ == INT2:
            v = struct.unpack_from(">h", self._data, self._pos)[0]
            self._pos += 2
            return v
        if typ == INT4:
            v = struct.unpack_from(">i", self._data, self._pos)[0]
            self._pos += 4
            return v
        if typ == INT8:
            v = struct.unpack_from(">q", self._data, self._pos)[0]
            self._pos += 8
            return v
        self._skip(typ)
        return default

    # 读取 tag 位置的字符串（STRING1 单字节长度 / STRING4 四字节长度），按 UTF-8 忽略错误解码；
    # 字段缺失或类型不符返回 default，ZERO_TAG 返回空串。
    def read_string(self, tag: int, default: str = "") -> str:
        found = self._goto(tag)
        if found is None:
            return default
        typ, _ = found
        if typ == ZERO_TAG:
            return ""
        if typ in (STRING1, STRING4):
            if typ == STRING1:
                self._need(1)
                n = self._data[self._pos]
                self._advance(1)
            else:
                self._need(4)
                n = struct.unpack_from(">i", self._data, self._pos)[0]
                self._advance(4)
            # CR-03：负长度下旧实现切片得到空串且游标回退，把死循环交给上层 while True
            self._need(n)
            s = self._data[self._pos : self._pos + n]
            self._advance(n)
            return s.decode("utf-8", errors="ignore")
        self._skip(typ)
        return default

    # 读取 tag 位置的二进制内容（SIMPLE_LIST 或 STRING1/STRING4 均视作字节串）；
    # 字段缺失或类型不符返回 default。
    def read_bytes(self, tag: int, default: bytes = b"") -> bytes:
        found = self._goto(tag)
        if found is None:
            return default
        typ, _ = found
        if typ == ZERO_TAG:
            return b""
        if typ == SIMPLE_LIST:
            # 元素类型头 + 自描述整数域长度（口径见 _skip 的 SIMPLE_LIST 分支）
            self._take_head()
            n = self.read_int(0)
            self._need(n)
            b = self._data[self._pos : self._pos + n]
            self._advance(n)
            return b
        if typ in (STRING1, STRING4):
            if typ == STRING1:
                self._need(1)
                n = self._data[self._pos]
                self._advance(1)
            else:
                self._need(4)
                n = struct.unpack_from(">i", self._data, self._pos)[0]
                self._advance(4)
            self._need(n)
            b = self._data[self._pos : self._pos + n]
            self._advance(n)
            return b
        self._skip(typ)
        return default

    # 读取 tag 位置的结构体：交由 parser 回调解析字段并消费 STRUCT_END，返回其结果；
    # 字段缺失、为 ZERO_TAG 或非 STRUCT_BEGIN 时返回 None。
    def read_struct(self, tag: int, parser: Callable[["TarsInputStream"], Any]) -> Any:
        found = self._goto(tag)
        if found is None:
            return None
        typ, _ = found
        if typ == ZERO_TAG:
            return None
        if typ != STRUCT_BEGIN:
            self._skip(typ)
            return None
        return parser(self)

    # 供 parser 收尾调用：吃掉剩余未读字段（parser 未读到的更高 tag）直至 STRUCT_END，
    # 使游标停在结构体之后，无返回值。
    def finish_struct(self) -> None:
        while True:
            f = self._peek_field()
            if f is None:
                return
            typ, _ = f
            if typ == STRUCT_END:
                self._take_head()
                return
            _before = self._pos
            self._take_head()
            self._skip(typ)
            # CR-03：同上，卡死即抛错而不是无限循环
            self._assert_progress(_before)


# Tars 编码流：把各类字段按 tag 追加进内部字节缓冲，仅覆盖虎牙 join 命令所需类型。
class TarsOutputStream:
    def __init__(self) -> None:
        self._buf = bytearray()

    # 写入一个字段头字节：高4位放 tag、低4位放 type（此处 tag 均 <15，无需扩展 tag）。
    def _write_head(self, typ: int, tag: int) -> None:
        self._buf.append((tag << 4) | typ)

    # 写入整数字段：0 用 ZERO_TAG 压缩，能放进 int32 用 INT4，否则用 INT8。
    def write_int(self, value: int, tag: int) -> None:
        if value == 0:
            self._write_head(ZERO_TAG, tag)
            return
        if -(2**31) <= value <= 2**31 - 1:
            self._write_head(INT4, tag)
            self._buf.extend(struct.pack(">i", value))
        else:
            # ayyuid/uid 等可能超 int32,超出时写 int64
            self._write_head(INT8, tag)
            self._buf.extend(struct.pack(">q", value))

    # 写入布尔字段：False 用 ZERO_TAG，True 用 INT1 值 1。
    def write_bool(self, value: bool, tag: int) -> None:
        if not value:
            self._write_head(ZERO_TAG, tag)
            return
        self._write_head(INT1, tag)
        self._buf.append(1)

    # 写入字符串字段：UTF-8 编码后按长度选 STRING1（<=255）或 STRING4，再追加内容。
    def write_string(self, value: str, tag: int) -> None:
        data = value.encode("utf-8")
        if len(data) > 255:
            self._write_head(STRING4, tag)
            self._buf.extend(struct.pack(">i", len(data)))
        else:
            self._write_head(STRING1, tag)
            self._buf.append(len(data))
        self._buf.extend(data)

    # 写入字节串字段：以 SIMPLE_LIST 落盘——元素类型头(BYTE tag0) + 长度(Tars 自描述整数域，非固定4字节) + 内容。
    def write_bytes(self, value: bytes, tag: int) -> None:
        self._write_head(SIMPLE_LIST, tag)
        self._write_head(INT1, 0)
        self.write_int(len(value), 0)
        self._buf.extend(value)

    # 导出编码结果：返回当前缓冲的不可变 bytes 副本。
    def to_bytes(self) -> bytes:
        return bytes(self._buf)
