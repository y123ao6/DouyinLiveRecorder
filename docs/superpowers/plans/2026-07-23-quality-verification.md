# 直播画质实际回采与校验告警 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 stream 模块主要平台返回实际下发的画质档位，main.py 记录并与设置比对，降级时告警，Web 面板显示"设置/实际"两列并在不一致时高亮。

**Architecture:** stream.py 各平台函数在返回的 result dict 增加 `actual_quality`（实际选中画质代码，如 "UHD"）与 `available_qualities`（可用画质代码列表）字段；移除 `_pad_list` 静默填充，改用 `min(index, len-1)` 显式截断并记录真实档位。main.py `start_record` 将 actual_quality 转中文存入 `recording_time_list`，与设置画质比较，降级时 `logger.warning`。`get_status()` 返回实际画质，前端"正在录制"表格新增"实际画质"列，不一致时单元格标红。

**Tech Stack:** Python (asyncio, configparser), FastAPI, 原生 HTML/CSS/JS

---

## 文件结构

| 文件 | 职责 | 改动类型 |
|---|---|---|
| `src/stream.py` | 各平台直播流获取；新增 actual_quality/available_qualities 字段 | 修改 7 个函数 + 新增辅助函数 |
| `src/spider.py` | B站数据获取；`get_bilibili_stream_data` 返回结构改为 dict | 修改 1 个函数 |
| `main.py` | `start_record` 记录实际画质并告警；`get_status` 返回实际画质 | 修改 3 处 |
| `web/index.html` | "正在录制"表头增加"实际画质"列 | 修改 |
| `web/style.css` | 降级标红样式 | 新增 |
| `web/app.js` | renderStatus 渲染实际画质列 + 降级高亮 | 修改 |
| `tests/test_stream_quality.py` | stream 模块画质回采单元测试 | 新建 |

## 画质代码与等级契约

```python
# 已有常量（src/stream.py 顶部）
QUALITY_MAPPING = {"OD": 0, "BD": 0, "UHD": 1, "HD": 2, "SD": 3, "LD": 4}
QUALITY_MAPPING_BIT = {'OD': 99999, 'BD': 4000, 'UHD': 2000, 'HD': 1000, 'SD': 800, 'LD': 600}
```

- 画质代码：`OD`(原画) / `BD`(蓝光) / `UHD`(超清) / `HD`(高清) / `SD`(标清) / `LD`(流畅)
- 画质等级值 = `QUALITY_MAPPING[code]`，**数值越大画质越低**
- 降级判定：`actual` 等级值 `>` 请求等级值（actual 更低 = 降级）；actual 更高视为异常不告警（理论上不发生）
- 代码→中文：`OD→原画, BD→蓝光, UHD→超清, HD→高清, SD→标清, LD→流畅`（对齐 `main.py:get_quality_code` 的反向）

---

### Task 1: 新增画质辅助函数与常量

**Files:**
- Modify: `src/stream.py` (顶部常量区，~line 25-26 之后)
- Test: `tests/test_stream_quality.py` (新建)

- [ ] **Step 1: 写失败测试**

创建 `tests/test_stream_quality.py`：
```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py -v`
Expected: FAIL (ImportError: cannot import name 'bitrate_to_quality')

- [ ] **Step 3: 实现辅助函数**

在 `src/stream.py` 的 `QUALITY_MAPPING_BIT` 定义之后（约 line 26 后）添加：
```python
# 画质等级值（数值越大画质越低），用于降级判定
QUALITY_LEVEL = {"OD": 0, "BD": 0, "UHD": 1, "HD": 2, "SD": 3, "LD": 4}

# 画质代码 → 中文名（对齐 main.py get_quality_code 的反向）
QUALITY_CODE_TO_ZH = {"OD": "原画", "BD": "蓝光", "UHD": "超清", "HD": "高清", "SD": "标清", "LD": "流畅"}

# 网易CC 画质名 → 统一代码
NETEASE_QUALITY_MAP = {"blueray": "OD", "ultra": "UHD", "high": "HD", "standard": "SD"}


def bitrate_to_quality(bitrate: int) -> str:
    """根据码率反查画质代码。返回码率上限 >= 给定值的最高档；0/未知回退 OD。"""
    if not bitrate or bitrate <= 0:
        return "OD"
    # QUALITY_MAPPING_BIT 按码率上限降序：OD>BD>UHD>HD>SD>LD
    for code in ("OD", "BD", "UHD", "HD", "SD", "LD"):
        if bitrate <= QUALITY_MAPPING_BIT[code]:
            return code
    return "OD"


def code_to_zh(code: str | None) -> str:
    """画质代码转中文；未知代码原样返回。"""
    if not code:
        return code or ""
    return QUALITY_CODE_TO_ZH.get(code, code)


def is_downgrade(requested: str | None, actual: str | None) -> bool:
    """判定是否降级：actual 画质等级值 > requested 等级值。None 不告警。"""
    if not requested or not actual:
        return False
    req_level = QUALITY_LEVEL.get(requested)
    act_level = QUALITY_LEVEL.get(actual)
    if req_level is None or act_level is None:
        return False
    return act_level > req_level
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: 提交**

```bash
cd /workspace && git add src/stream.py tests/test_stream_quality.py && git commit -m "feat(stream): add quality helper functions (bitrate_to_quality, code_to_zh, is_downgrade)"
```

---

### Task 2: 改造抖音 get_douyin_stream_url（保留 dict key 作为画质标签）

**Files:**
- Modify: `src/stream.py:56-101` (get_douyin_stream_url)
- Test: `tests/test_stream_quality.py`

**当前问题**：line 66-68 把 `flv_pull_url`/`hls_pull_url_map` 用 `.values()` 转成无标签 list，丢失画质名；`_pad_list` 静默填充。

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_stream_quality.py`：
```python
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
    """请求 UHD 但平台仅提供 OD → actual_quality == OD（降级）。"""
    import src.stream as stream_mod
    orig = stream_mod.get_response_status
    async def _ok(**kw): return True
    stream_mod.get_response_status = _ok
    try:
        result = asyncio.run(get_douyin_stream_url(_douyin_json_single(), "UHD"))
    finally:
        stream_mod.get_response_status = orig
    assert result["actual_quality"] == "OD"
    assert is_downgrade("UHD", result["actual_quality"]) is True
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py::test_douyin_actual_quality_match tests/test_stream_quality.py::test_douyin_actual_quality_downgrade -v`
Expected: FAIL (KeyError 'actual_quality')

- [ ] **Step 3: 改造 get_douyin_stream_url**

将 `src/stream.py` 的 `get_douyin_stream_url`（line 56-101）中 line 63-100 替换为：
```python
    if status == 2:
        stream_url = json_data.get('stream_url', {})
        flv_pull_url: dict = stream_url.get('flv_pull_url', {}) or {}
        m3u8_pull_url: dict = stream_url.get('hls_pull_url_map', {}) or {}
        hevc_flv_url = stream_url.get('hevc_flv_url')

        # 保留画质标签：将 dict items 按画质等级降序（OD>BD>UHD>HD>SD>LD）排序
        def _sort_quality_items(d: dict) -> list[tuple[str, str]]:
            order = {"ORIGIN": 0, "OD": 0, "BD": 1, "UHD": 2, "HD": 3, "SD": 4, "LD": 5}
            return sorted(d.items(), key=lambda kv: order.get(kv[0].upper(), 99))

        flv_pairs = _sort_quality_items(flv_pull_url)
        m3u8_pairs = _sort_quality_items(m3u8_pull_url)

        # 可用画质档位（统一为代码：ORIGIN→OD）
        def _norm_code(name: str) -> str:
            return "OD" if name.upper() in ("ORIGIN",) else name.upper()
        available_qualities = [_norm_code(k) for k, _ in flv_pairs] if flv_pairs else [_norm_code(k) for k, _ in m3u8_pairs]

        video_quality, quality_index = get_quality_index(video_quality)
        # 显式截断而非 _pad_list 静默填充
        flv_idx = min(quality_index, len(flv_pairs) - 1) if flv_pairs else 0
        m3u8_idx = min(quality_index, len(m3u8_pairs) - 1) if m3u8_pairs else 0
        flv_quality_name, flv_url = flv_pairs[flv_idx] if flv_pairs else ("", "")
        m3u8_quality_name, m3u8_url = m3u8_pairs[m3u8_idx] if m3u8_pairs else ("", "")
        actual_quality = _norm_code(flv_quality_name or m3u8_quality_name)

        m3u8_codec = urllib.parse.parse_qs(urllib.parse.urlparse(m3u8_url or "").query).get('codec', [''])[0]
        m3u8_is_hevc = 'h265' in m3u8_codec.lower() or 'hevc' in m3u8_codec.lower()
        use_hevc_flv = quality_index == 0 and bool(hevc_flv_url) and not m3u8_is_hevc
        if use_hevc_flv:
            flv_url = hevc_flv_url
        ok = await get_response_status(url=m3u8_url, proxy_addr=proxy_addr)
        if not ok:
            index = flv_idx + 1 if flv_idx < len(flv_pairs) - 1 else max(flv_idx - 1, 0)
            if m3u8_pairs:
                m3u8_quality_name, m3u8_url = m3u8_pairs[index]
            if not use_hevc_flv and flv_pairs:
                flv_quality_name, flv_url = flv_pairs[index]
            actual_quality = _norm_code(flv_quality_name or m3u8_quality_name)
        result |= {
            'is_live': True,
            'quality': video_quality,
            'actual_quality': actual_quality,
            'available_qualities': available_qualities,
            'm3u8_url': m3u8_url,
            'flv_url': flv_url,
            'record_url': m3u8_url or flv_url,
        }
    return result
```

- [ ] **Step 4: 运行确认通过**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: 提交**

```bash
cd /workspace && git add src/stream.py tests/test_stream_quality.py && git commit -m "feat(stream): douyin return actual_quality from flv_pull_url keys, drop _pad_list"
```

---

### Task 3: 改造网易CC get_netease_stream_url（移除 _pad_list，加映射）

**Files:**
- Modify: `src/stream.py:381-404` (get_netease_stream_url)
- Test: `tests/test_stream_quality.py`

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_stream_quality.py`：
```python
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
    """请求 UHD 但仅 blueray(OD) → 降级到 OD。"""
    result = asyncio.run(get_netease_stream_url(_netease_json_single(), "UHD"))
    assert result["actual_quality"] == "OD"
    assert is_downgrade("UHD", result["actual_quality"]) is True
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py::test_netease_actual_quality_match tests/test_stream_quality.py::test_netease_actual_quality_downgrade -v`
Expected: FAIL (KeyError 'actual_quality')

- [ ] **Step 3: 改造 get_netease_stream_url**

将 `src/stream.py` line 388-404 替换为：
```python
    if json_data.get('stream_list'):
        stream_list = json_data['stream_list']['resolution']
        order = ['blueray', 'ultra', 'high', 'standard']
        sorted_keys = [key for key in order if key in stream_list]
        if not sorted_keys:
            return json_data
        video_quality, quality_index = get_quality_index(video_quality)
        # 显式截断，记录实际选中的画质名
        idx = min(quality_index, len(sorted_keys) - 1)
        selected_quality = sorted_keys[idx]
        actual_quality = NETEASE_QUALITY_MAP.get(selected_quality, video_quality)
        available_qualities = [NETEASE_QUALITY_MAP.get(k, k.upper()) for k in sorted_keys]
        flv_url_list = stream_list[selected_quality]['cdn']
        selected_cdn = list(flv_url_list.keys())[0]
        flv_url = flv_url_list[selected_cdn]
    else:
        actual_quality = None
        available_qualities = None

    return {
        "is_live": True, "anchor_name": json_data['anchor_name'], "title": json_data['title'],
        'quality': video_quality, 'actual_quality': actual_quality,
        'available_qualities': available_qualities,
        "m3u8_url": m3u8_url, "flv_url": flv_url, "record_url": flv_url or m3u8_url
    }
```

- [ ] **Step 4: 运行确认通过**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: 提交**

```bash
cd /workspace && git add src/stream.py tests/test_stream_quality.py && git commit -m "feat(stream): netease return actual_quality via NETEASE_QUALITY_MAP, drop _pad_list"
```

---

### Task 4: 改造虎牙 get_huya_stream_url（移除 _pad_list，缺档显式降级）

**Files:**
- Modify: `src/stream.py:289-318` (get_huya_stream_url 画质选择段)
- Test: `tests/test_stream_quality.py`

**当前问题**：line 295 `_pad_list(quality_list)` 把不足4档的 ratio 列表填充，导致 `video_quality_options["LD"]` 实际指向更高档 ratio；line 304-306 缺档时抛 ValueError 而非降级。

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_stream_quality.py`：
```python
from src.stream import get_huya_stream_url


def _huya_json_full():
    """虎牙全档位：exsphd 含4个 ratio。"""
    return {
        "data": [{"gameLiveInfo": {"nick": "虎牙主播", "introduction": "标题"},
                  "gameStreamInfoList": [{
                      "sFlvUrl": "http://flv", "sStreamName": "stream", "sFlvUrlSuffix": "flv",
                      "sHlsUrl": "http://hls", "sHlsUrlSuffix": "m3u8",
                      "sFlvAntiCode": "wsSecret=xxx&ctype=huya_web&exsphd=264_4000,264_2000,264_1000,264_800"
                  }]}]
    }


def _huya_json_partial():
    """虎牙仅2档：请求 LD 应降级到最低可用档。"""
    return {
        "data": [{"gameLiveInfo": {"nick": "虎牙主播", "introduction": "标题"},
                  "gameStreamInfoList": [{
                      "sFlvUrl": "http://flv", "sStreamName": "stream", "sFlvUrlSuffix": "flv",
                      "sHlsUrl": "http://hls", "sHlsUrlSuffix": "m3u8",
                      "sFlvAntiCode": "wsSecret=xxx&ctype=huya_web&exsphd=264_4000,264_2000"
                  }]}]
    }


def test_huya_actual_quality_match():
    result = asyncio.run(get_huya_stream_url(_huya_json_full(), "HD"))
    assert result["actual_quality"] == "HD"
    assert result["is_live"] is True


def test_huya_actual_quality_downgrade():
    """请求 LD 但仅 UHD/HD 两档 → 降级到 HD（最低可用）。"""
    result = asyncio.run(get_huya_stream_url(_huya_json_partial(), "LD"))
    assert result["actual_quality"] == "HD"
    assert is_downgrade("LD", result["actual_quality"]) is True
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py::test_huya_actual_quality_match tests/test_stream_quality.py::test_huya_actual_quality_downgrade -v`
Expected: FAIL (KeyError 'actual_quality' 或 ValueError)

- [ ] **Step 3: 改造 get_huya_stream_url 画质选择段**

将 `src/stream.py` line 289-318 替换为：
```python
        quality_list = flv_anti_code.split('&exsphd=')
        actual_quality = video_quality  # OD/BD 默认即请求值
        available_qualities = None
        if len(quality_list) > 1 and video_quality not in ["OD", "BD"]:
            pattern = r"(?<=264_)\d+"
            quality_list = list(re.findall(pattern, quality_list[1]))[::-1]
            if quality_list:
                # 不再 _pad_list；按实际可用档位构造 options
                labels = ["UHD", "HD", "SD", "LD"]
                video_quality_options = dict(zip(labels, quality_list))
                available_qualities = ["OD", "BD"] + list(video_quality_options.keys())
                if video_quality in video_quality_options:
                    ratio_val = video_quality_options[video_quality]
                    actual_quality = video_quality
                else:
                    # 请求档位不在可用列表：降级到最近的更低档，若无更低档则取最低可用档
                    req_level = QUALITY_LEVEL.get(video_quality, 4)
                    lower = [(l, r) for l, r in video_quality_options.items() if QUALITY_LEVEL.get(l, 0) >= req_level]
                    if lower:
                        actual_quality, ratio_val = lower[0]
                    else:
                        # 取最低可用档（列表最后一个）
                        actual_quality, ratio_val = list(video_quality_options.items())[-1]
                flv_url = flv_url + str(ratio_val)
                m3u8_url = m3u8_url + str(ratio_val)
        result |= {
            'is_live': True,
            'title': live_title,
            'quality': video_quality,
            'actual_quality': actual_quality,
            'available_qualities': available_qualities,
            'm3u8_url': m3u8_url,
            'flv_url': flv_url,
            'record_url': flv_url or m3u8_url
        }
    return result
```

- [ ] **Step 4: 运行确认通过**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py -v`
Expected: PASS (10 tests)

- [ ] **Step 5: 提交**

```bash
cd /workspace && git add src/stream.py tests/test_stream_quality.py && git commit -m "feat(stream): huya return actual_quality, drop _pad_list, degrade explicitly"
```

---

### Task 5: 改造斗鱼 get_douyu_stream_url（rate 反查）

**Files:**
- Modify: `src/stream.py:322-343` (get_douyu_stream_url)
- Test: `tests/test_stream_quality.py`

**当前问题**：line 339 `quality: video_quality` 只回显请求值；平台实际下发的 rate 在 `flv_data_inner.get('rate')`，未读取。

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_stream_quality.py`：
```python
from src.stream import get_douyu_stream_url


def _douyu_json():
    return {"is_live": True, "anchor_name": "斗鱼主播", "room_id": 12345}


def test_douyu_actual_quality_from_rate():
    """平台下发 rate=3（UHD）→ actual_quality == UHD。"""
    import src.stream as stream_mod
    async def _fake_douyu_data(rid, rate, **kw):
        return {"data": {"rtmp_url": "http://flv", "rtmp_live": "live.flv?rate=3", "rate": 3}}
    orig = stream_mod.get_douyu_stream_data
    stream_mod.get_douyu_stream_data = _fake_douyu_data
    try:
        result = asyncio.run(get_douyu_stream_url(_douyu_json(), "UHD", cookies=""))
    finally:
        stream_mod.get_douyu_stream_data = orig
    assert result["actual_quality"] == "UHD"


def test_douyu_actual_quality_downgrade():
    """请求 UHD(rate=3) 但平台下发 rate=0(OD) → 降级。"""
    import src.stream as stream_mod
    async def _fake_douyu_data(rid, rate, **kw):
        return {"data": {"rtmp_url": "http://flv", "rtmp_live": "live.flv", "rate": 0}}
    orig = stream_mod.get_douyu_stream_data
    stream_mod.get_douyu_stream_data = _fake_douyu_data
    try:
        result = asyncio.run(get_douyu_stream_url(_douyu_json(), "UHD", cookies=""))
    finally:
        stream_mod.get_douyu_stream_data = orig
    assert result["actual_quality"] == "OD"
    assert is_downgrade("UHD", result["actual_quality"]) is True
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py::test_douyu_actual_quality_from_rate tests/test_stream_quality.py::test_douyu_actual_quality_downgrade -v`
Expected: FAIL (KeyError 'actual_quality')

- [ ] **Step 3: 改造 get_douyu_stream_url**

将 `src/stream.py` line 329-343 替换为：
```python
    video_quality_options = {"OD": '0', "BD": '0', "UHD": '3', "HD": '2', "SD": '1', "LD": '1'}
    # 反向映射：rate 值 → 画质代码（多对一取最高档）
    rate_to_code = {'0': 'OD', '3': 'UHD', '2': 'HD', '1': 'SD'}

    rid = str(json_data["room_id"])
    rate = video_quality_options.get(video_quality or '', '0')
    flv_data = await get_douyu_stream_data(rid, rate, cookies=cookies, proxy_addr=proxy_addr)
    flv_data_inner = flv_data.get('data') or {}
    rtmp_url = flv_data_inner.get('rtmp_url')
    rtmp_live = flv_data_inner.get('rtmp_live')
    # 平台实际下发的 rate
    actual_rate = str(flv_data_inner.get('rate', ''))
    actual_quality = rate_to_code.get(actual_rate, video_quality)

    result = {"anchor_name": json_data.get('anchor_name'), "is_live": True, "quality": video_quality,
              "actual_quality": actual_quality}
    if rtmp_live:
        flv_url = f'{rtmp_url}/{rtmp_live}'
        result |= {'flv_url': flv_url, 'record_url': flv_url}
    return result
```

- [ ] **Step 4: 运行确认通过**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py -v`
Expected: PASS (12 tests)

- [ ] **Step 5: 提交**

```bash
cd /workspace && git add src/stream.py tests/test_stream_quality.py && git commit -m "feat(stream): douyu return actual_quality from server rate field"
```

---

### Task 6: 改造快手 get_kuaishou_stream_url + TikTok get_tiktok_stream_url（bitrate/vbitrate 反查）

**Files:**
- Modify: `src/stream.py:188-230` (get_kuaishou_stream_url), `src/stream.py:104-184` (get_tiktok_stream_url)
- Test: `tests/test_stream_quality.py`

**当前问题**：
- 快手 flv 带 bitrate 分支（line 205-222）用码率挑选但未回填 actual_quality；m3u8/无bitrate 分支用 `_pad_list`。
- TikTok 的 play_list 项含 vbitrate 但 line 156-175 只取 url，丢弃 vbitrate。

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_stream_quality.py`：
```python
from src.stream import get_kuaishou_stream_url, get_tiktok_stream_url


def _kuaishou_json_flv_bitrate():
    return {
        "type": 2, "is_live": True, "anchor_name": "快手主播",
        "flv_url_list": [{"url": "http://flv/2000", "bitrate": 2000}, {"url": "http://flv/1000", "bitrate": 1000}]
    }


def test_kuaishou_actual_quality_from_bitrate():
    """请求 UHD，flv_list 含 bitrate 2000(UHD) → actual_quality == UHD。"""
    result = asyncio.run(get_kuaishou_stream_url(_kuaishou_json_flv_bitrate(), "UHD"))
    assert result.get("actual_quality") == "UHD"


def test_kuaishou_actual_quality_downgrade():
    """请求 LD 但最高码率仅 1000(HD) → 降级到 HD。"""
    result = asyncio.run(get_kuaishou_stream_url({
        "type": 2, "is_live": True, "anchor_name": "快手主播",
        "flv_url_list": [{"url": "http://flv/1000", "bitrate": 1000}]
    }, "LD"))
    assert result.get("actual_quality") == "HD"
    assert is_downgrade("LD", result["actual_quality"]) is True


def _tiktok_json_full():
    return {
        "LiveRoom": {"liveRoomUserInfo": {"user": {"nickname": "TT", "uniqueId": "1", "status": 2},
                     "liveRoom": {"title": "t", "streamData": {"pull_data": {"stream_data": json.dumps({
                         "data": {"flv": {"main": {"flv": "http://flv/uhd", "sdk_params": json.dumps({"vbitrate": 2000, "resolution": "1920x1080", "VCodec": "h264"})}},
                         "hls": {"main": {"hls": "http://hls/uhd", "sdk_params": json.dumps({"vbitrate": 2000, "resolution": "1920x1080", "VCodec": "h264"})}}
                     })}}}}}
    }


def test_tiktok_actual_quality_from_vbitrate():
    import src.stream as stream_mod
    async def _ok(**kw): return True
    orig = stream_mod.get_response_status
    stream_mod.get_response_status = _ok
    try:
        result = asyncio.run(get_tiktok_stream_url(_tiktok_json_full(), "UHD"))
    finally:
        stream_mod.get_response_status = orig
    assert result.get("actual_quality") == "UHD"
```

注意：测试文件顶部需 `import json`（若未导入）。

- [ ] **Step 2: 运行确认失败**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py -k kuaishou or tiktok -v`
Expected: FAIL (KeyError 'actual_quality')

- [ ] **Step 3: 改造 get_kuaishou_stream_url**

将 `src/stream.py` line 196-229（`if live_status:` 块）替换为：
```python
    if live_status:
        quality, quality_index = get_quality_index(video_quality)
        actual_quality = None
        available_qualities = None
        if 'm3u8_url_list' in json_data:
            m3u8_url_list = json_data['m3u8_url_list'][::-1]
            idx = min(quality_index, len(m3u8_url_list) - 1)
            m3u8_url = m3u8_url_list[idx]['url']
            result['m3u8_url'] = m3u8_url

        if 'flv_url_list' in json_data:
            if 'bitrate' in json_data['flv_url_list'][0]:
                flv_url_list = json_data['flv_url_list']
                flv_url_list = sorted(flv_url_list, key=lambda x: x['bitrate'], reverse=True)
                quality_str = video_quality.upper() if video_quality else 'OD'
                if quality_str.isdigit():
                    bit_items = list(QUALITY_MAPPING_BIT.items())
                    q_idx = min(int(quality_str[0]), len(bit_items) - 1)
                    video_quality, quality_index_bitrate_value = bit_items[q_idx]
                else:
                    quality_index_bitrate_value = QUALITY_MAPPING_BIT.get(quality_str, 99999)
                    video_quality = quality_str
                quality_index = next(
                    (i for i, x in enumerate(flv_url_list) if x['bitrate'] <= quality_index_bitrate_value), None)
                if quality_index is None:
                    quality_index = len(flv_url_list) - 1
                selected = flv_url_list[quality_index]
                actual_quality = bitrate_to_quality(selected['bitrate'])
                available_qualities = [bitrate_to_quality(x['bitrate']) for x in flv_url_list]
                result['flv_url'] = selected['url']
                result['record_url'] = selected['url']
            else:
                flv_url_list = json_data['flv_url_list'][::-1]
                idx = min(quality_index, len(flv_url_list) - 1)
                result['flv_url'] = flv_url_list[idx]['url']
                result['record_url'] = result['flv_url']
        result['quality'] = video_quality
        result['actual_quality'] = actual_quality
        result['available_qualities'] = available_qualities
    return result
```

- [ ] **Step 4: 改造 get_tiktok_stream_url**

在 `src/stream.py` 的 `get_tiktok_stream_url`（line 104-184）中，将 line 176-183（`result |= {...}`）替换为：
```python
        # 实际选中项的 vbitrate → 画质代码
        actual_quality = bitrate_to_quality(flv_dict.get('vbitrate', 0)) if flv_dict else video_quality
        available_qualities = [bitrate_to_quality(x.get('vbitrate', 0)) for x in flv_url_list if x] if flv_url_list else None
        result |= {
            'is_live': True,
            'title': live_room['liveRoom']['title'],
            'quality': video_quality,
            'actual_quality': actual_quality,
            'available_qualities': available_qualities,
            'm3u8_url': m3u8_url,
            'flv_url': flv_url,
            'record_url': m3u8_url or flv_url,
        }
    return result
```

- [ ] **Step 5: 运行确认通过**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py -v`
Expected: PASS (15 tests)

- [ ] **Step 6: 提交**

```bash
cd /workspace && git add src/stream.py tests/test_stream_quality.py && git commit -m "feat(stream): kuaishou+tiktok return actual_quality from bitrate/vbitrate"
```

---

### Task 7: 改造 B站 spider + stream（返回 current_qn/accept_qn）

**Files:**
- Modify: `src/spider.py:981-1056` (get_bilibili_stream_data)
- Modify: `src/stream.py:362-377` (get_bilibili_stream_url)
- Test: `tests/test_stream_quality.py`

**当前问题**：`get_bilibili_stream_data` 返回 `OptionalStr`（纯URL字符串），丢弃 `current_qn`/`accept_qn`。`get_bilibili_stream_url` line 377 `quality: video_quality` 只回显请求值。

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_stream_quality.py`：
```python
from src.stream import get_bilibili_stream_url


def _bili_json():
    return {"anchor_name": "B站主播", "live_status": 1, "room_url": "https://live.bilibili.com/123"}


def test_bili_actual_quality_from_qn():
    """spider 返回 current_qn=250(UHD) → actual_quality == UHD。"""
    import src.stream as stream_mod
    async def _fake_bili_data(url, **kw):
        return {"url": "http://m3u8/uhd", "current_qn": "250", "accept_qn": ["10000", "400", "250"]}
    orig = stream_mod.get_bilibili_stream_data
    stream_mod.get_bilibili_stream_data = _fake_bili_data
    try:
        result = asyncio.run(get_bilibili_stream_url(_bili_json(), "UHD"))
    finally:
        stream_mod.get_bilibili_stream_data = orig
    assert result["actual_quality"] == "UHD"
    assert "UHD" in result["available_qualities"]


def test_bili_actual_quality_downgrade():
    """请求 UHD(250) 但 spider 返回 current_qn=80(LD) → 降级。"""
    import src.stream as stream_mod
    async def _fake_bili_data(url, **kw):
        return {"url": "http://m3u8/ld", "current_qn": "80", "accept_qn": ["10000", "80"]}
    orig = stream_mod.get_bilibili_stream_data
    stream_mod.get_bilibili_stream_data = _fake_bili_data
    try:
        result = asyncio.run(get_bilibili_stream_url(_bili_json(), "UHD"))
    finally:
        stream_mod.get_bilibili_stream_data = orig
    assert result["actual_quality"] == "LD"
    assert is_downgrade("UHD", result["actual_quality"]) is True
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py -k bili -v`
Expected: FAIL

- [ ] **Step 3: 改造 spider.py get_bilibili_stream_data**

将 `src/spider.py` line 981-1056 函数签名与返回值改为返回 dict：
```python
async def get_bilibili_stream_data(url: str, qn: str = '10000', platform: str = 'web', proxy_addr: OptionalStr = None,
                             cookies: OptionalStr = None) -> dict | None:
    # 获取 B站直播流数据（多清晰度），返回 {url, current_qn, accept_qn}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'origin': 'https://live.bilibili.com',
        'referer': 'https://live.bilibili.com/26066074',
    }
    if cookies:
        headers['Cookie'] = cookies

    room_id = _safe_extract_id(url)
    params = {'cid': room_id, 'qn': qn, 'platform': platform}
    play_api = f'https://api.live.bilibili.com/room/v1/Room/playUrl?{urllib.parse.urlencode(params)}'
    json_str = await async_req(play_api, proxy_addr=proxy_addr, headers=headers)
    json_str = _get_str_response(json_str)
    json_data = json.loads(json_str)
    if json_data and json_data['code'] == 0:
        durl_list = json_data['data'].get('durl', [])
        if not durl_list:
            return None
        # playUrl 接口无 qn 元信息，current_qn 取请求值，accept_qn 未知
        target_url = None
        for i in durl_list:
            if 'd1--cn-gotcha' in i.get('url', ''):
                target_url = i['url']
                break
        if not target_url:
            target_url = durl_list[-1].get('url')
        return {"url": target_url, "current_qn": qn, "accept_qn": [qn]}
    else:
        params = {
            "room_id": room_id, "protocol": "0,1", "format": "0,1,2", "codec": "0,1,2",
            "qn": qn, "platform": "web", "ptype": "8", "dolby": "5", "panorama": "1", "hdr_type": "0,1"
        }
        api = f'https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo?{urllib.parse.urlencode(params)}'
        json_str = await async_req(api, proxy_addr=proxy_addr, headers=headers)
        json_str = _get_str_response(json_str)
        json_data = json.loads(json_str)
        if json_data['data']['live_status'] == 0:
            print("The anchor did not start broadcasting.")
            return None
        playurl_info = json_data['data']['playurl_info']
        stream_list = playurl_info['playurl'].get('stream', [])
        if not stream_list:
            return None
        format_list = stream_list[0].get('format', [])
        if not format_list:
            return None
        stream_data_list = format_list[0].get('codec', [])
        if not stream_data_list:
            return None
        sorted_stream_list = sorted(stream_data_list, key=itemgetter("current_qn"), reverse=True)
        video_quality_options = {'10000': 0, '400': 1, '250': 2, '150': 3, '80': 4}
        qn_count = len(sorted_stream_list)
        select_stream_index = min(video_quality_options.get(qn, 0), qn_count - 1)
        stream_data = sorted_stream_list[select_stream_index]
        base_url = stream_data['base_url']
        url_info = stream_data.get('url_info', [])
        if not url_info:
            return None
        host = url_info[0].get('host', '')
        extra = url_info[0].get('extra', '')
        m3u8_url = host + base_url + extra
        current_qn = str(stream_data.get('current_qn', qn))
        accept_qn = [str(s.get('current_qn')) for s in sorted_stream_list]
        return {"url": m3u8_url, "current_qn": current_qn, "accept_qn": accept_qn}
    return None
```

- [ ] **Step 4: 改造 stream.py get_bilibili_stream_url**

将 `src/stream.py` line 372-377 替换为：
```python
    select_quality = video_quality_options.get((video_quality or 'OD').upper(), '10000')
    play_url = await get_bilibili_stream_data(
        room_url, qn=select_quality, platform='web', proxy_addr=proxy_addr, cookies=cookies)
    if not play_url:
        return {"anchor_name": anchor_name, "is_live": False}
    # qn → 画质代码 反向映射
    qn_to_code = {v: k for k, v in video_quality_options.items()}
    actual_quality = qn_to_code.get(str(play_url.get('current_qn', '')), video_quality)
    accept_qn = play_url.get('accept_qn') or []
    available_qualities = [qn_to_code.get(str(q), q) for q in accept_qn] or None
    return {'anchor_name': json_data['anchor_name'], 'is_live': True, 'title': json_data['title'],
            'quality': video_quality, 'actual_quality': actual_quality,
            'available_qualities': available_qualities, 'record_url': play_url['url']}
```

- [ ] **Step 5: 运行确认通过**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py -v`
Expected: PASS (17 tests)

- [ ] **Step 6: 提交**

```bash
cd /workspace && git add src/spider.py src/stream.py tests/test_stream_quality.py && git commit -m "feat(stream): bilibili spider returns current_qn/accept_qn, stream returns actual_quality"
```

---

### Task 8: main.py 记录实际画质并降级告警，get_status 返回实际画质

**Files:**
- Modify: `src/stream.py` (新增 import 到 main 可用的导出，无新代码)
- Modify: `main.py:927-928` (start_record 解析 actual_quality), `main.py:1577`, `main.py:1695` (recording_time_list 写入), `main.py:2132-2184` (get_status)
- Test: `tests/test_stream_quality.py`

**当前问题**：line 1577/1695 `recording_time_list[record_name] = [start_record_time, record_quality_zh]` 只存设置画质；get_status line 2181 `quality` 只返回设置值。

- [ ] **Step 1: 写失败测试**

追加到 `tests/test_stream_quality.py`：
```python
def test_get_status_returns_actual_quality():
    """get_status 返回的 recording 项含 actual_quality 字段。"""
    import main
    # 临时设置 recording_time_list
    import datetime
    old = dict(main.recording_time_list)
    main.recording_time_list.clear()
    main.recording.add("序号1 测试主播")
    main.recording_time_list["序号1 测试主播"] = [datetime.datetime.now(), "超清", "高清"]
    try:
        s = main.get_status()
        assert len(s["recording"]) == 1
        rec = s["recording"][0]
        assert rec["quality"] == "超清"
        assert rec["actual_quality"] == "高清"
    finally:
        main.recording.discard("序号1 测试主播")
        main.recording_time_list.clear()
        main.recording_time_list.update(old)
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py::test_get_status_returns_actual_quality -v`
Expected: FAIL (KeyError 'actual_quality')

- [ ] **Step 3: 改造 main.py start_record 解析 actual_quality**

在 `main.py` 的 `start_record` 函数中，line 927-928 之后添加（解析 port_info 中的 actual_quality）：
```python
            record_quality_zh, record_url, anchor_name = url_data
            record_quality = get_quality_code(record_quality_zh)
            # 真实下发的画质代码（由 stream 模块回采，可能为 None）
            from src.stream import code_to_zh, is_downgrade as _is_downgrade
```

然后在 line 1574-1577（第一处 recording_time_list 写入）替换为：
```python
                                with record_state_lock:
                                    recording.add(record_name)
                                    start_record_time = datetime.datetime.now()
                                    actual_quality_code = port_info.get('actual_quality')
                                    actual_quality_zh = code_to_zh(actual_quality_code) if actual_quality_code else ''
                                    # 降级告警：实际画质低于设置时记录日志
                                    if actual_quality_code and _is_downgrade(record_quality, actual_quality_code):
                                        logger.warning(
                                            f"{record_name} 画质降级：设置 {record_quality_zh}({record_quality}) "
                                            f"实际 {actual_quality_zh}({actual_quality_code})")
                                    recording_time_list[record_name] = [start_record_time, record_quality_zh, actual_quality_zh]
```

在 line 1693-1695（第二处 recording_time_list 写入，direct_download 分支）替换为：
```python
                                            recording.add(record_name)
                                            start_record_time = datetime.datetime.now()
                                            actual_quality_code = port_info.get('actual_quality')
                                            actual_quality_zh = code_to_zh(actual_quality_code) if actual_quality_code else ''
                                            if actual_quality_code and _is_downgrade(record_quality, actual_quality_code):
                                                logger.warning(
                                                    f"{record_name} 画质降级：设置 {record_quality_zh}({record_quality}) "
                                                    f"实际 {actual_quality_zh}({actual_quality_code})")
                                            recording_time_list[record_name] = [start_record_time, record_quality_zh, actual_quality_zh]
```

- [ ] **Step 4: 改造 main.py get_status 返回 actual_quality**

在 `main.py` get_status（line 2145-2154）替换为：
```python
                recording_snapshot = list(recording)
                recording_times = {}
                for _name, _info in recording_time_list.items():
                    if _info:
                        # 兼容旧格式 [start, quality] 和新格式 [start, quality, actual_quality]
                        actual_q = _info[2] if len(_info) > 2 else ''
                        recording_times[_name] = {
                            "start_time": _info[0].strftime("%Y-%m-%d %H:%M:%S"),
                            "quality": _info[1],
                            "actual_quality": actual_q,
                            "duration": str(now - _info[0]).split(".")[0],
                        }
                    else:
                        recording_times[_name] = {"start_time": "", "quality": "", "actual_quality": "", "duration": "0:00:00"}
```

在 get_status 返回的 recording 列表（line 2170-2178）替换为：
```python
        "recording": [
            {
                "name": _n,
                "start_time": recording_times.get(_n, {}).get("start_time", ""),
                "quality": recording_times.get(_n, {}).get("quality", ""),
                "actual_quality": recording_times.get(_n, {}).get("actual_quality", ""),
                "duration": recording_times.get(_n, {}).get("duration", "0:00:00"),
            }
            for _n in recording_snapshot
        ],
```

- [ ] **Step 5: 运行确认通过**

Run: `cd /workspace && python -m pytest tests/test_stream_quality.py tests/test_web_api.py tests/test_web_config.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
cd /workspace && git add main.py tests/test_stream_quality.py && git commit -m "feat(main): record actual_quality, warn on downgrade, get_status returns actual_quality"
```

---

### Task 9: 前端显示"实际画质"列并降级高亮

**Files:**
- Modify: `web/index.html:44-47` (录制表头与空行)
- Modify: `web/style.css` (新增 .quality-down 样式)
- Modify: `web/app.js:194-210` (renderStatus 渲染实际画质)

- [ ] **Step 1: 修改 index.html 表头**

将 `web/index.html` line 45-46 的表头与空行：
```html
                <thead><tr><th>名称</th><th>画质</th><th>开始时间</th><th>已录时长</th></tr></thead>
                <tbody id="recording-tbody"><tr><td colspan="4" class="empty">暂无录制</td></tr></tbody>
```
改为：
```html
                <thead><tr><th>名称</th><th>设置画质</th><th>实际画质</th><th>开始时间</th><th>已录时长</th></tr></thead>
                <tbody id="recording-tbody"><tr><td colspan="5" class="empty">暂无录制</td></tr></tbody>
```

- [ ] **Step 2: 修改 style.css 新增降级样式**

在 `web/style.css` 的 `.data-table .empty` 规则之后添加：
```css
.data-table td.quality-down { color: var(--danger); font-weight: 600; }
```

- [ ] **Step 3: 修改 app.js renderStatus**

将 `web/app.js` 的 renderStatus（约 line 194-210）替换为：
```javascript
        var tbody = $('recording-tbody');
        var rec = s.recording || [];
        if (!rec.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty">暂无录制</td></tr>';
            return;
        }
        var html = '';
        for (var i = 0; i < rec.length; i++) {
            var r = rec[i];
            // 降级判定：实际画质非空且与设置不同 → 标红（actual 为空表示无法回采，不标红）
            var downClass = '';
            if (r.actual_quality && r.quality && r.actual_quality !== r.quality) {
                downClass = ' class="quality-down"';
            }
            var actualDisplay = r.actual_quality ? esc(r.actual_quality) : '-';
            html += '<tr>'
                + '<td>' + esc(r.name) + '</td>'
                + '<td>' + esc(r.quality) + '</td>'
                + '<td' + downClass + '>' + actualDisplay + '</td>'
                + '<td>' + esc(r.start_time) + '</td>'
                + '<td>' + esc(r.duration) + '</td>'
                + '</tr>';
        }
        tbody.innerHTML = html;
```

- [ ] **Step 4: 验证前端**

```bash
cd /workspace && node -c web/app.js 2>&1 || echo "node 不可用，跳过语法检查"
cd /workspace && python -m pytest tests/ -q 2>&1 | tail -5
```
Expected: 语法 OK；全量测试通过。

- [ ] **Step 5: 提交**

```bash
cd /workspace && git add web/index.html web/style.css web/app.js && git commit -m "feat(web): show actual_quality column with downgrade highlight"
```

---

### Task 10: 集成验收

**Files:** 无修改，仅验证

- [ ] **Step 1: 全量测试**

```bash
cd /workspace && python -m pytest tests/ -v 2>&1 | tail -30
```
Expected: 全部通过（原有 53 + 新增 stream_quality 测试）。

- [ ] **Step 2: 端到端冒烟**

```bash
cd /workspace
pkill -f 'python web.py' 2>/dev/null; sleep 1
python web.py > /tmp/web_q.log 2>&1 &
WEB_PID=$!
sleep 4
echo "=== /api/status ==="
curl -s -m 5 http://localhost:8000/api/status | python -c "import sys,json; d=json.load(sys.stdin); print('recording fields:', list(d.get('recording',[])[0].keys()) if d.get('recording') else 'no recording')"
echo "=== index ==="
curl -s -m 5 -o /dev/null -w "%{http_code}\n" http://localhost:8000/
kill $WEB_PID 2>/dev/null
wait 2>/dev/null
pkill -f 'python web.py' 2>/dev/null
```
Expected: `recording fields` 含 `actual_quality`；index 200。

- [ ] **Step 3: 恢复运行时文件**

```bash
cd /workspace && git checkout -- config/URL_config.ini logs/PlayURL.log logs/streamget.log 2>/dev/null; git status --short
```
Expected: 工作树干净（仅可能的 __pycache__）。

- [ ] **Step 4: 最终提交（如有未提交的清理）**

```bash
cd /workspace && git status --short
```
若无未提交项则跳过。提交格式：
```bash
git add -A && git commit -m "test: quality verification integration acceptance" 2>/dev/null || echo "nothing to commit"
```
