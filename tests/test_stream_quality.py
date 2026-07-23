import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.stream import bitrate_to_quality, QUALITY_LEVEL, code_to_zh, is_downgrade


def test_bitrate_to_quality():
    assert bitrate_to_quality(99999) == "OD"
    assert bitrate_to_quality(4000) == "BD"
    assert bitrate_to_quality(3500) == "BD"
    assert bitrate_to_quality(2000) == "UHD"
    assert bitrate_to_quality(1500) == "UHD"
    assert bitrate_to_quality(1000) == "HD"
    assert bitrate_to_quality(800) == "SD"
    assert bitrate_to_quality(600) == "LD"
    assert bitrate_to_quality(300) == "LD"
    assert bitrate_to_quality(0) == "OD"  # 0 或未知回退原画


def test_code_to_zh():
    assert code_to_zh("OD") == "原画"
    assert code_to_zh("BD") == "蓝光"
    assert code_to_zh("UHD") == "超清"
    assert code_to_zh("HD") == "高清"
    assert code_to_zh("SD") == "标清"
    assert code_to_zh("LD") == "流畅"
    assert code_to_zh("UNKNOWN") == "UNKNOWN"


def test_is_downgrade():
    # 等级值越大画质越低；actual 等级值 > 请求等级值 = 降级
    assert is_downgrade("UHD", "HD") is True   # 请求超清 实际高清 = 降级
    assert is_downgrade("UHD", "UHD") is False  # 一致
    assert is_downgrade("HD", "UHD") is False   # 实际更高，不告警
    assert is_downgrade("OD", "HD") is True     # 请求原画 实际高清 = 降级
    assert is_downgrade(None, "HD") is False    # actual 为 None（无法确定）不告警
    assert is_downgrade("UHD", None) is False   # 请求为 None 不告警


import asyncio
from src.stream import get_douyin_stream_url


def _douyin_json_full():
    """抖音全档位测试数据：flv_pull_url / hls_pull_url_map 的 key 是画质名。"""
    return {
        "anchor_name": "测试主播",
        "status": 2,
        "stream_url": {
            "flv_pull_url": {"ORIGIN": "http://flv/origin", "UHD": "http://flv/uhd", "HD": "http://flv/hd"},
            "hls_pull_url_map": {"ORIGIN": "http://hls/origin", "UHD": "http://hls/uhd", "HD": "http://hls/hd"},
        }
    }


def _douyin_json_single():
    """抖音仅原画一档：应降级到 OD 并标记 actual_quality。"""
    return {
        "anchor_name": "测试主播",
        "status": 2,
        "stream_url": {
            "flv_pull_url": {"ORIGIN": "http://flv/origin"},
            "hls_pull_url_map": {"ORIGIN": "http://hls/origin"},
        }
    }


def test_douyin_actual_quality_match():
    """请求 UHD 且平台提供 UHD → actual_quality == UHD。"""
    # mock get_response_status 返回 True 避免真实网络请求
    import src.stream as stream_mod
    orig = stream_mod.get_response_status
    async def _ok(**kw): return True
    stream_mod.get_response_status = _ok
    try:
        result = asyncio.run(get_douyin_stream_url(_douyin_json_full(), "UHD"))
    finally:
        stream_mod.get_response_status = orig
    assert result["actual_quality"] == "UHD"
    assert result["quality"] == "UHD"  # 请求值回显
    assert "OD" in result["available_qualities"]


def test_douyin_actual_quality_downgrade():
    """请求 UHD 但平台仅提供 OD → actual_quality == OD（请求未满足）。

    注：按 QUALITY_LEVEL 契约 OD(0) 画质高于 UHD(1)，is_downgrade 应为 False
    （actual 更高不告警）；此处 actual_quality != 请求值即表明请求未满足。
    """
    import src.stream as stream_mod
    orig = stream_mod.get_response_status
    async def _ok(**kw): return True
    stream_mod.get_response_status = _ok
    try:
        result = asyncio.run(get_douyin_stream_url(_douyin_json_single(), "UHD"))
    finally:
        stream_mod.get_response_status = orig
    assert result["actual_quality"] == "OD"
    assert result["actual_quality"] != "UHD"  # 请求 UHD 未被满足
    assert is_downgrade("UHD", result["actual_quality"]) is False  # OD 画质更高，按契约非降级


from src.stream import get_netease_stream_url


def _netease_json_full():
    return {
        "is_live": True, "anchor_name": "网易主播", "title": "测试",
        "m3u8_url": "http://m3u8/default",
        "stream_list": {"resolution": {
            "blueray": {"cdn": {"cdn1": "http://flv/blueray"}},
            "ultra": {"cdn": {"cdn1": "http://flv/ultra"}},
            "high": {"cdn": {"cdn1": "http://flv/high"}},
        }}
    }


def _netease_json_single():
    return {
        "is_live": True, "anchor_name": "网易主播", "title": "测试",
        "m3u8_url": "http://m3u8/default",
        "stream_list": {"resolution": {"blueray": {"cdn": {"cdn1": "http://flv/blueray"}}}}
    }


def test_netease_actual_quality_match():
    result = asyncio.run(get_netease_stream_url(_netease_json_full(), "UHD"))
    assert result["actual_quality"] == "UHD"  # ultra → UHD
    assert result["quality"] == "UHD"


def test_netease_actual_quality_downgrade():
    """请求 UHD 但仅 blueray(OD) → actual_quality == OD（请求未满足）。

    注：blueray 映射为 OD（原画/蓝光，画质最高），按 QUALITY_LEVEL 契约
    OD(0) 高于 UHD(1)，is_downgrade 为 False（actual 更高不告警）。
    """
    result = asyncio.run(get_netease_stream_url(_netease_json_single(), "UHD"))
    assert result["actual_quality"] == "OD"
    assert result["actual_quality"] != "UHD"  # 请求 UHD 未被满足
    assert is_downgrade("UHD", result["actual_quality"]) is False  # OD 画质更高，按契约非降级
