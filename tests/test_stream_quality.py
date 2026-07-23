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
