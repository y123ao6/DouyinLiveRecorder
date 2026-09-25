# Tests for src/ab_sign.py module - A-Bogus 签名算法.
#
# MID-67（2026-09-21）：原 test_known_hash 只断言 isinstance(str) + len == 64，
# 任何「输出 64 位 hex」的实现都能通过（把 SM3 整个删掉换成 sha256 也照样绿），
# 违反本仓「删掉生产实现就会失败」判据。现按 GB/T 32905-2016 的两条标准向量钉死，
# 并用 hashlib（OpenSSL）作独立裁判交叉核对——裁判不是本仓代码，故不构成自实现被测逻辑。
# 注意：审查记录里给出的两条期望值实为「正确前缀 + 错误后缀」（分别在
# 第 9 / 第 41 个十六进制字符处偏离标准值），已用 OpenSSL 与 GB/T 32905-2016 双向核对后
# 按标准值落定（见下方 _SM3_KAT_VECTORS）——生产实现本身是对的，未作改动。

import hashlib
import time
import types
from importlib import import_module
from types import ModuleType

import pytest

from src.ab_sign import (
    SM3,
    ab_sign,
    ff_j,
    gener_random,
    generate_random_str,
    generate_rc4_bb_str,
    get_long_int,
    get_t_j,
    gg_j,
    left_rotate,
    rc4_encrypt,
    result_encrypt,
)

# GB/T 32905-2016 附录 A 的两条示例，外加空串这一边界（三条均与 OpenSSL SM3 逐字符一致）
_SM3_KAT_VECTORS = [
    ("abc", "66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0"),
    (
        "abcd" * 16,
        "debe9ff92275b8a138604889c18e5a4d6fdb70e5387e5765293dcba39c0c5732",
    ),
    ("", "1ab21d8355cfa17f8e61194831e81a8f22bec8c728fefb747ed035eb5082aa2b"),
]

# src/__init__.py 里 `from .ab_sign import ab_sign` 把包属性 src.ab_sign 重绑成了**同名函数**，
# 于是 `from src import ab_sign` 拿到的是函数、没有 __name__ 之外的模块属性可 patch。
# 冻结时钟必须落到真正的模块对象上，故显式经 import_module 取 sys.modules 里的模块本体。
_AB_SIGN_MODULE: ModuleType = import_module("src.ab_sign")


def _module_shim(module: ModuleType) -> types.SimpleNamespace:
    # 浅拷贝替身（AGENTS.md 测试约定）：替换目标模块命名空间里的全局名，不改 stdlib 模块本体。
    return types.SimpleNamespace(**vars(module))


class TestRc4Encrypt:
    # Test RC4 加密/解密.

    def test_encrypt_decrypt_roundtrip(self) -> None:
        # RC4 加密后再解密应还原原文.
        key = "test_key"
        plaintext = "Hello, World!"
        encrypted = rc4_encrypt(plaintext, key)
        decrypted = rc4_encrypt(encrypted, key)
        assert decrypted == plaintext

    def test_empty_plaintext(self) -> None:
        # 空字符串加密返回空字符串.
        assert rc4_encrypt("", "key") == ""

    def test_different_keys_produce_different_output(self) -> None:
        # 不同密钥产生不同密文.
        plaintext = "test"
        assert rc4_encrypt(plaintext, "key1") != rc4_encrypt(plaintext, "key2")

    def test_known_value(self) -> None:
        # 教材版 RC4（KSA + PRGA，无丢弃字节）在 key="Key"/明文="Plaintext" 下的字节序列。
        # 这是**回归快照**而非外部标准向量（本函数是 A-Bogus 与上游 JS 的互操作件，
        # 真正的外部一致性由线上签名成功率兜底）；关键是不再像旧断言那样「任何 3 字符输出都行」。
        # 旧断言 isinstance(str) + len == 3 把整个 rc4_encrypt 删掉换成 "xxx" 也照样绿。
        assert rc4_encrypt("Plaintext", "Key").encode("latin-1").hex() == "bbf316e8d940af0ad3"
        # 自解密是本仓实际用法（bb 串加密后再解回来），单独保留一条对称性断言
        assert rc4_encrypt("abc", "key") == "\x6a\x0e\x57"


class TestLeftRotate:
    # Test 32位循环左移.

    def test_basic_rotation(self) -> None:
        assert left_rotate(1, 1) == 2

    def test_rotation_overflow(self) -> None:
        # 超过32位的高位被截断.
        result = left_rotate(0x80000000, 1)
        assert result == 1

    def test_zero_rotation(self) -> None:
        # 移动0位等于不移动.
        assert left_rotate(0xDEADBEEF, 0) == 0xDEADBEEF

    def test_full_rotation(self) -> None:
        # 移动32位等于不移动.
        assert left_rotate(0xDEADBEEF, 32) == 0xDEADBEEF


class TestGetTj:
    # Test 常量 Tj 计算.

    def test_first_range(self) -> None:
        assert get_t_j(0) == 2043430169
        assert get_t_j(15) == 2043430169

    def test_second_range(self) -> None:
        assert get_t_j(16) == 2055708042
        assert get_t_j(63) == 2055708042

    def test_invalid_j(self) -> None:
        with pytest.raises(ValueError, match="invalid j"):
            get_t_j(64)
        with pytest.raises(ValueError, match="invalid j"):
            get_t_j(-1)


class TestFfJ:
    # Test 布尔函数 FF.

    def test_first_range(self) -> None:
        # j < 16: XOR.
        assert ff_j(0, 0xFF, 0x0F, 0xF0) == (0xFF ^ 0x0F ^ 0xF0) & 0xFFFFFFFF

    def test_second_range(self) -> None:
        # j >= 16: majority.
        result = ff_j(16, 0xFF, 0x0F, 0xF0)
        expected = ((0xFF & 0x0F) | (0xFF & 0xF0) | (0x0F & 0xF0)) & 0xFFFFFFFF
        assert result == expected

    def test_invalid_j(self) -> None:
        with pytest.raises(ValueError):
            ff_j(64, 0, 0, 0)


class TestGgJ:
    # Test 布尔函数 GG.

    def test_first_range(self) -> None:
        # j < 16: XOR.
        assert gg_j(0, 0xFF, 0x0F, 0xF0) == (0xFF ^ 0x0F ^ 0xF0) & 0xFFFFFFFF

    def test_second_range(self) -> None:
        # j >= 16: (x&y)|(~x&z).
        result = gg_j(16, 0xFF, 0x0F, 0xF0)
        expected = ((0xFF & 0x0F) | ((~0xFF & 0xFFFFFFFF) & 0xF0)) & 0xFFFFFFFF
        assert result == expected

    def test_invalid_j(self) -> None:
        with pytest.raises(ValueError):
            gg_j(-1, 0, 0, 0)


class TestSM3:
    # Test SM3 哈希算法.

    @pytest.mark.parametrize(("message", "digest"), _SM3_KAT_VECTORS)
    def test_known_hash(self, message: str, digest: str) -> None:
        # GB/T 32905-2016 标准摘要值逐字符比对（MID-67：旧断言只查长度，任何 64 位 hex 都过）。
        # 判据「删掉生产实现就会失败」：换成 sha256/随机 hex 立刻不等。
        assert SM3().sum(message, output_format="hex") == digest

    def test_known_hash_matches_openssl_reference(self) -> None:
        # 独立裁判：hashlib('sm3') 由 OpenSSL 提供（非本仓实现），逐条核对标准向量。
        # 该 OpenSSL 构建/发行版禁用 SM3 时（FIPS provider）本条 skip——标准向量那条仍在守。
        try:
            hashlib.new("sm3")
        except Exception as exc:  # ValueError: unsupported hash type / Provider 禁用
            pytest.skip(f"本机构建无 SM3 参考实现: {type(exc).__name__}")
        for message, digest in _SM3_KAT_VECTORS:
            assert hashlib.new("sm3", message.encode("utf-8")).hexdigest() == digest
            assert SM3().sum(message, output_format="hex") == digest

    def test_empty_string(self) -> None:
        # 空字符串的 SM3 哈希.
        sm3 = SM3()
        result = sm3.sum("", output_format="hex")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_byte_array_output(self) -> None:
        # 字节数组格式输出.
        sm3 = SM3()
        result = sm3.sum("test")
        assert isinstance(result, list)
        assert len(result) == 32  # 256 bits = 32 bytes

    def test_deterministic(self) -> None:
        # 相同输入产生相同输出.
        sm3 = SM3()
        r1 = sm3.sum("hello", output_format="hex")
        r2 = sm3.sum("hello", output_format="hex")
        assert r1 == r2

    def test_different_inputs(self) -> None:
        # 不同输入产生不同输出.
        sm3 = SM3()
        r1 = sm3.sum("abc", output_format="hex")
        r2 = sm3.sum("def", output_format="hex")
        assert r1 != r2

    def test_long_input(self) -> None:
        # 长输入（超过64字节分块）.
        sm3 = SM3()
        result = sm3.sum("a" * 200, output_format="hex")
        assert len(result) == 64

    def test_write_incremental(self) -> None:
        # 分次写入数据.
        sm3 = SM3()
        sm3.write("ab")
        sm3.write("c")
        result1 = sm3.sum(output_format="hex")
        result2 = sm3.sum("abc", output_format="hex")
        assert result1 == result2

    def test_compress_error(self) -> None:
        # 数据不足64字节时 _compress 抛异常.
        sm3 = SM3()
        with pytest.raises(ValueError, match="not enough data"):
            sm3._compress([0] * 32)


class TestResultEncrypt:
    # Test 魔改 base64 编码.

    def test_output_length(self) -> None:
        # 输出长度为 ceil(n/3)*4.
        result = result_encrypt("abc")
        assert len(result) == 4

    def test_different_scales(self) -> None:
        # 不同 num 参数产生不同输出.
        text = "test"
        r1 = result_encrypt(text, "s0")
        r2 = result_encrypt(text, "s4")
        assert r1 != r2

    def test_deterministic(self) -> None:
        # 相同输入确定性输出.
        assert result_encrypt("hello", "s4") == result_encrypt("hello", "s4")


class TestGetLongInt:
    # Test 字节序列转长整型.

    def test_basic(self) -> None:
        assert get_long_int(0, "abc") == (ord("a") << 16) | (ord("b") << 8) | ord("c")

    def test_padding_with_zeros(self) -> None:
        # 超出字符串长度时用0填充.
        result = get_long_int(0, "a")
        assert result == (ord("a") << 16)

    def test_round_number_offset(self) -> None:
        # round_num 按3字节步进.
        result = get_long_int(1, "abcdef")
        assert result == (ord("d") << 16) | (ord("e") << 8) | ord("f")


class TestGenerRandom:
    # Test 随机字节序列生成.

    def test_output_length(self) -> None:
        # 输出固定4字节.
        result = gener_random(12345, [3, 45])
        assert len(result) == 4

    def test_deterministic(self) -> None:
        # 相同输入确定性输出.
        assert gener_random(100, [1, 2]) == gener_random(100, [1, 2])

    def test_different_inputs(self) -> None:
        # 不同输入产生不同输出.
        assert gener_random(100, [1, 2]) != gener_random(200, [1, 2])


class TestGenerateRandomStr:
    # Test 随机字符串生成.

    def test_returns_string(self) -> None:
        result = generate_random_str()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_deterministic(self) -> None:
        # F-19 后改为真随机：两次调用应产生不同前缀（极小概率碰撞，12 字节可忽略）。
        # 固定值回退路径由 DLR_AB_SIGN_FIXED_RANDOM=1 覆盖（见 generate_random_str 注释）。
        r1 = generate_random_str()
        r2 = generate_random_str()
        assert r1 != r2

    def test_fixed_random_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 回退开关：DLR_AB_SIGN_FIXED_RANDOM=1 时恢复旧固定值行为（两次调用结果一致），
        # 用于个别平台对随机段有值域校验时的定位与兼容。
        monkeypatch.setenv("DLR_AB_SIGN_FIXED_RANDOM", "1")
        r1 = generate_random_str()
        r2 = generate_random_str()
        assert r1 == r2


class TestGenerateRc4BbStr:
    # Test RC4 bb 字符串生成.

    def test_returns_string(self) -> None:
        result = generate_rc4_bb_str("param=value", "Mozilla/5.0", "env_str")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_deterministic(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # MID-67：旧用例名为「确定性」、实际只断两条非空 str，注释还自认「时间戳不同，两次
        # 结果可能不同」——等于什么都没测。generate_rc4_bb_str 里唯一的时间来源是模块全局
        # time.time()（start_time/end_time 会进 bb 串），冻结后必须逐字节相等。
        # 冻结一律走浅拷贝替身挂到 src.ab_sign 命名空间，绝不 setattr 到 stdlib time 本体。
        frozen = _module_shim(time)
        frozen.time = lambda: 1_700_000_000.0
        monkeypatch.setattr(_AB_SIGN_MODULE, "time", frozen)

        r1 = generate_rc4_bb_str("p=1", "ua", "env")
        r2 = generate_rc4_bb_str("p=1", "ua", "env")
        assert r1 == r2, "冻结时钟后两次调用必须逐字节一致"
        assert isinstance(r1, str) and len(r1) > 0

        # 反向断言：时间戳确实被吃进了 bb 串，否则「相等」只是因为该值根本没参与计算
        frozen.time = lambda: 1_700_000_001.0
        assert generate_rc4_bb_str("p=1", "ua", "env") != r1


class TestAbSign:
    # Test A-Bogus 签名算法主入口.

    def test_returns_string_with_equals(self) -> None:
        # 签名结果以 '=' 结尾.
        result = ab_sign("aid=6383&test=1", "Mozilla/5.0")
        assert isinstance(result, str)
        assert result.endswith("=")
        assert len(result) > 10

    def test_different_params(self) -> None:
        # 不同参数产生不同签名.
        r1 = ab_sign("aid=6383&a=1", "UA1")
        r2 = ab_sign("aid=6383&a=2", "UA1")
        assert r1 != r2
