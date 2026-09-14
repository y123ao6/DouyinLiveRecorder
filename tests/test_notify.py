# -*- coding: utf-8 -*-
# 通知模块单测
#
# 覆盖 run_script 的超时保护：用户脚本挂起时必须被强制终止并回收管道，
# 不能让 communicate() 无 timeout 永久占用调用线程。
#
# 备注：项目用 loguru 记录错误，loguru 默认不桥接 stdlib logging，
# 故 caplog 抓不到——测试自带 InMemorySink 捕获消息文本。

import io
import sys
import time
from collections.abc import Generator
from pathlib import Path

import pytest
from loguru import logger

# 通知模块的 run_script 通过 import main 读写运行时全局；
# 测试需先把 main 引入，才能加载 src.notify
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main  # noqa: E402  必须在 src.notify 之前
import src.notify as notify  # noqa: E402


@pytest.fixture
def short_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    # 把超时压到 1 秒，让测试快速断言「超时后被 kill」而不是等满 300 秒
    monkeypatch.setattr(notify, "_SCRIPT_TIMEOUT_SECONDS", 1.0)


@pytest.fixture
def log_capture() -> Generator[io.StringIO, None, None]:
    # 内存 sink：直接接管 loguru 消息（不依赖 caplog / stdlib logging 桥接），
    # 退出 fixture 时自动 remove 不污染全局 handler
    buf = io.StringIO()
    sink_id = logger.add(buf, format="{message}", level="DEBUG")
    try:
        yield buf
    finally:
        try:
            logger.remove(sink_id)
        except ValueError:
            pass


def test_run_script_normal_completion(capsys: pytest.CaptureFixture[str]) -> None:
    # 正常完成的脚本：stdout 应原样打印到当前 stdout
    notify.run_script("python -c \"print('hello-from-script')\"")
    captured = capsys.readouterr()
    assert "hello-from-script" in captured.out


def test_run_script_timeout_kills_process(
    short_timeout: None,
    log_capture: io.StringIO,
) -> None:
    # 挂起脚本（sleep 30）必须在 1 秒超时后被 kill，且 log 记超时
    started = time.monotonic()
    notify.run_script('python -c "import time; time.sleep(30)"')
    elapsed = time.monotonic() - started
    # 超时 1 秒 + kill + 二次 communicate 回收管道；留出 4 秒余量
    assert elapsed < 4.0, f"超时未被强制回收: elapsed={elapsed:.2f}s"
    log_text = log_capture.getvalue()
    assert "执行自定义脚本超时" in log_text


def test_run_script_bad_command_logs_oserror(log_capture: io.StringIO) -> None:
    # 不存在的命令应被 shlex.Popen 触发 OSError 路径（Windows FileNotFoundError / Linux [Errno 2]）
    notify.run_script("__definitely_not_a_real_binary_42__")
    log_text = log_capture.getvalue()
    # 不强求精确匹配 "FileNotFoundError" / "No such file"：跨平台文案差异大
    # 仅要求确实进入 OSError 分支并记录了失败
    assert "执行自定义脚本失败" in log_text


def test_run_script_uses_safe_split_not_shell(log_capture: io.StringIO) -> None:
    # 验证 run_script 不走 shell=True：传入明显会触发 shell 展开的字符串时，
    # 子进程 Popen 收到的应是 list[str]（来自 shlex.split），若 shlex 解析失败应被 except ValueError 接住
    # 这里用一个会被 shlex 报 ValueError 的非闭合引号
    notify.run_script('echo "unterminated')
    log_text = log_capture.getvalue()
    assert "脚本命令解析失败" in log_text
