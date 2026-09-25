# -*- coding: utf-8 -*-
# HTTP 客户端共享运行时配置

# 控制面 SSL 证书验证开关：登录 / 取 Cookie / 推送 token / 平台 API 等非拉流请求。
# 默认启用（True，安全优先）。由 async_http / sync_http / spider 在发起请求时
# 按属性读取，故修改需通过 set_ssl_verify()。
# 安全边界：该开关**不再**与「是否启用https录制」联动。旧实现用
# set_ssl_verify(not enable_https_recording) 让「https 拉流」这个拉流侧选项顺带
# 关闭全站 TLS 校验——包括登录与凭据推送，等于用一个拉流开关放大成全局安全降级。
# 现在拉流豁免只落在 stream_ssl_verify，控制面恒按此处取值。
ssl_verify: bool = True

# 拉流侧 SSL 证书验证开关（流地址探测 / 校验 / 直下 / ffmpeg）。
# 与「是否启用https录制」联动：开启 https 录制 → 拉流豁免证书校验（保证 https
# 拉流不被 CDN 证书主机名不匹配等问题阻断）；关闭 → 拉流恢复严格校验。
# 读取一律走 get_effective_ssl_verify(platform)，保证校验器 / ffmpeg / 直下三路一致。
stream_ssl_verify: bool = True

# 平台级 SSL 证书验证覆盖。键为平台标识（如「虎牙直播」），值为是否校验。
# FFmpeg 9.0 起 TLS 证书验证默认开启（8.0 预告、9.0 落地），http 录制模式下
# https-only 流/接口也会被默认校验证书——「禁用SSL证书验证的平台」因此重新具备
# 实际作用：证书异常平台（虎牙 TX CDN 主机名不匹配等）经此列表跳过校验。
# 该覆盖只参与拉流侧裁决（stream_ssl_verify=True 时生效），不波及控制面请求。
ssl_verify_platform_overrides: dict[str, bool] = {}

# 「是否启用https录制」整合开关（合并原「是否强制启用https录制」与
# 「是否禁用SSL证书验证(是/否)」）：开启 = https 拉流 + 拉流侧禁用 SSL 证书验证；
# 关闭 = http 拉流 + 拉流侧恢复默认证书校验。运行时由主循环热更新。
# 注意：控制面（ssl_verify）不随之变化，详见 ssl_verify 处的安全边界说明。
https_recording_enabled: bool = False


def set_ssl_verify(value: bool) -> None:
    # 控制面开关的安全敏感性与「不与 https 录制联动」的边界见模块头 ssl_verify 注释
    global ssl_verify
    ssl_verify = value


def set_stream_ssl_verify(value: bool) -> None:
    global stream_ssl_verify
    stream_ssl_verify = value


def set_https_recording(value: bool) -> None:
    # 仅联动拉流侧 stream_ssl_verify；控制面 ssl_verify 保持独立（理由见模块头）
    global https_recording_enabled
    https_recording_enabled = value
    set_stream_ssl_verify(not value)


def set_platform_ssl_verify(platform: str, value: bool) -> None:
    # 设置某平台的 SSL 证书验证覆盖（True=校验 / False=跳过校验）。
    ssl_verify_platform_overrides[platform] = value


def get_effective_ssl_verify(platform: str | None = None) -> bool:
    # 返回拉流侧某平台实际应使用的 SSL 校验开关。「禁用SSL证书验证的平台」仅在 stream_ssl_verify=True
    # （http 录制模式、恢复默认严格校验）时参与裁决：命中禁用列表 → False（FFmpeg 9.0 起默认校验 TLS
    # 证书，靠此让证书异常平台仍可拉流）；stream_ssl_verify=False（https 录制、拉流已全局豁免）时平台
    # 覆盖无额外意义，一律继承 False。
    if stream_ssl_verify and platform and platform in ssl_verify_platform_overrides:
        return ssl_verify_platform_overrides[platform]
    return stream_ssl_verify
