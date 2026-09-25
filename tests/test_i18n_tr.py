# -*- coding: utf-8 -*-
# i18n.tr() 帮手回归：先查表再插值，避免 f-string 在查表前先替换模板。
#
# 旧实现：f"[{record_name}] xxx" 先被 Python 求值为 "[房间A] xxx"，
#         目录里的 msgid 是 "[{record_name}] xxx"，查不到 → 翻译静默退化为原文。
# 新实现：tr("[{record_name}] xxx", record_name=record_name)
#         模板先查表（带占位符的模板原样查），命中后再 .format(**kwargs)。

import i18n


def test_tr_passes_through_when_no_translation() -> None:
    # 未命中目录时按原文格式（恒等映射 + format 二次插值）
    assert i18n.tr("plain text {x}", x=1) == "plain text 1"


def test_tr_with_placeholder_passes_through_correctly() -> None:
    # 含占位符但目录无翻译的模板：仍能正常 format
    assert i18n.tr("[{room}] hello", room="A") == "[A] hello"


def test_tr_with_format_expression_via_kwarg() -> None:
    # f-string 的 {type(e).__name__} 不能直接当 .format 占位符，
    # tr() 强制调用方预求值——这里 type_name=type(e).__name__ 演示等价效果
    try:
        raise ValueError("boom")
    except ValueError as e:
        out = i18n.tr("caught {type_name}: {e}", type_name=type(e).__name__, e=e)
    assert out == "caught ValueError: boom"


def test_tr_missing_kwarg_falls_back_to_template() -> None:
    # MI-23 修复后语义：占位符未传对应 kwarg 时**不再抛异常**，降级为原文模板。
    # 旧测试断言「必须 KeyError」，锁定的正是会导致错误分支二次崩溃的前提：
    # i18n.tr() 的调用点大量位于 except 分支内，而译文是外部可编辑数据（译者可能把
    # {e} 写成 {err}）。二次异常会顶掉原始异常，把「网络失败」升级成崩溃并掩盖真实故障。
    # 现在保证 tr() 永不抛——拼写错误仍可通过「日志里出现未插值的花括号」识别。
    assert i18n.tr("hello {name}") == "hello {name}"


def test_tr_translates_then_formats() -> None:
    # 注入临时目录键后：tr() 翻译命中、占位符按 .format 二次插值
    saved = i18n._tr
    try:
        i18n._tr = lambda template: {
            "Hello {name}, you are {age}": "你好 {name},你 {age} 岁",
        }.get(template, template)
        out = i18n.tr("Hello {name}, you are {age}", name="张三", age=18)
        assert out == "你好 张三,你 18 岁"
    finally:
        i18n._tr = saved


def test_tr_does_not_match_substituted_form() -> None:
    # 反向回归：f-string 求值后用 tr() 查带占位符的目录键必须 miss（恒等回退）
    # ——这正是旧实现的「翻译静默失效」失败模式，新接口通过文档约束规避
    saved = i18n._tr
    try:
        i18n._tr = lambda template: {
            "[{record_name}] template": "已翻译",
        }.get(template, template)
        out_runtime = i18n.tr("[房间A] template")  # 已插值的字符串查模板键
        # 翻译命中的是模板键 "[{record_name}] template"，已插值的「[房间A] template」miss
        assert out_runtime == "[房间A] template"
    finally:
        i18n._tr = saved
