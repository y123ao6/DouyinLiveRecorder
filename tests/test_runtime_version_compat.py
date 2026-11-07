# -*- coding: utf-8 -*-
# 运行时兼容范围回归锁：Python 3.14 / 3.15 × Node.js 24.22.2 / 26.13.0。
#
# 背景：扩展支持新版本时最容易漏的是「只改一处数字」——依赖清单仍有 3.14 下限、CI 矩阵却只剩新版本，
# 或 Docker/CI 各写一份 Node 主版本、旧线悄悄掉出验证面。本锁把兼容范围收敛到 pyproject.toml 的
# [tool.douyin-live-recorder]，再逐面核对声明 / 测试矩阵 / 构建参数是否**同时**覆盖新旧两端。
#
# 判据全部静态、零网络、零 Docker 依赖：校验的是「配置声明了什么」，真实运行由 test job 的矩阵与
# 本机四组合验证承担，两者不可互相冒充（只改声明不改矩阵会被本锁抓到，只改矩阵不改声明同样会）。
# 不用 packaging.SpecifierSet：static job 不装 pytest 系列依赖，本锁必须只用标准库即可判定。

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any, cast

# PyYAML 是运行期依赖（i18n/zh_TW.yaml），test job 装齐 requirements.txt 后必然可用；
# 用它按 YAML 结构取 job/step，比全文正则更抗注释里出现的历史版本号。
import yaml

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
CI_FILE = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_FILE = ROOT / ".github" / "workflows" / "build-release.yml"
DOCKERFILE = ROOT / "Dockerfile"
PYRIGHT_CONFIG = ROOT / "pyrightconfig.json"

CONST_STEP_NAME = "Declare shared constants"
# 官方 NodeSource 脚本哈希的形状（值本身由 Dockerfile 单一持有，本锁不复制一份）
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _pyproject() -> dict[str, Any]:
    # 按字节读再解码：Path.read_text 会做通用换行翻译，行尾形态不该混进版本判据。
    return cast("dict[str, Any]", tomllib.loads(PYPROJECT.read_bytes().decode("utf-8")))


def _supported() -> dict[str, list[str]]:
    # 刻意不在此复制一份版本清单：这里只是「读事实源」，两端各写一遍正是本锁要防的漂移。
    return cast("dict[str, list[str]]", _pyproject()["tool"]["douyin-live-recorder"])


def _workflow(path: Path) -> dict[str, Any]:
    # 按字节读 + utf-8 解码：两份 workflow 都是纯 LF，避免通用换行翻译把 YAML 块标量改形。
    return cast("dict[str, Any]", yaml.safe_load(path.read_bytes().decode("utf-8")))


def _const_step_run(path: Path) -> str:
    # 按步骤名取 run 脚本体，不按行号、不做全文正则：consts 步骤里的历史注释会提到旧版本形态。
    jobs = cast("dict[str, Any]", _workflow(path)["jobs"])
    bodies: list[str] = []
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps") or []
        if not isinstance(steps, list):
            continue
        for step in steps:
            if isinstance(step, dict) and step.get("name") == CONST_STEP_NAME:
                run = step.get("run")
                assert isinstance(run, str) and run.strip(), f"{path.name} 的 {CONST_STEP_NAME} 步骤 run 为空"
                bodies.append(run)
    assert len(bodies) == 1, f"{path.name} 中 {CONST_STEP_NAME!r} 步骤应恰有一处，实际 {len(bodies)} 处"
    return bodies[0]


def _consts(path: Path) -> dict[str, str]:
    # echo "key=value" / echo 'key=["a","b"]' 两种形态统一收敛；值里的 JSON 引号不再被当成分隔符。
    out: dict[str, str] = {}
    for line in _const_step_run(path).splitlines():
        stripped = line.strip()
        if not stripped.startswith("echo "):
            continue
        # 矩阵值写作 echo 'python_matrix=["3.14","3.15"]'：外层单引号包住整段，
        # 只剥这一层，值内部的 JSON 双引号才不会被下面 partition("=") 之前的检查误切。
        payload = stripped[len("echo ") :].strip()
        if len(payload) >= 2 and payload[0] in "\"'" and payload[-1] == payload[0]:
            payload = payload[1:-1]
        key, sep, value = payload.partition("=")
        if sep and key.strip().isidentifier():
            out[key.strip()] = value.strip()
    assert out, f"{path.name} 的 consts 步骤未解析到任何 echo key=value（判据面为空即门禁失效）"
    return out


def _job(workflow: Path, name: str) -> dict[str, Any]:
    jobs = cast("dict[str, Any]", _workflow(workflow)["jobs"])
    job = jobs.get(name)
    assert isinstance(job, dict), f"{workflow.name} 缺少 job {name}"
    return cast("dict[str, Any]", job)


def _step_runs(job: dict[str, Any]) -> str:
    # 只拼 run 脚本体：uses 步骤的 with 里也有版本号，混进来会让「命令里有没有 py315」误判成恒真。
    return "\n".join(
        str(step.get("run") or "") for step in cast("list[Any]", job.get("steps") or []) if isinstance(step, dict)
    )


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def _spec_allows(spec: str, version: str) -> bool:
    # 只认本仓会用到的 >= <= == != < > 片段；出现无法判定的形态一律断言失败，不许静默放行。
    # 自己写迷你求值器而非引第三方：这条判据要能在只装 black/isort 的 static 环境里也跑得起来。
    target = _version_tuple(version)
    allowed = True
    for raw in spec.split(","):
        item = raw.strip()
        matched = re.fullmatch(r"(>=|<=|==|!=|<|>)\s*(\d+(?:\.\d+)*)", item)
        assert matched, f"requires-python 出现本锁无法判定的片段 {item!r}"
        op, bound_text = matched.group(1), matched.group(2)
        bound = _version_tuple(bound_text)
        length = max(len(target), len(bound))
        left, right = target + (0,) * (length - len(target)), bound + (0,) * (length - len(bound))
        checks = {
            ">=": left >= right,
            "<=": left <= right,
            "==": left == right,
            "!=": left != right,
            "<": left < right,
            ">": left > right,
        }
        allowed = allowed and checks[op]
    return allowed


# ───────────────────────── 声明面：pyproject 是兼容范围的唯一事实源 ─────────────────────────


def test_pyproject_declares_both_python_and_node_versions() -> None:
    supported = _supported()
    assert supported["python_versions"] == ["3.14", "3.15"], "Python 兼容范围必须逐字同时含 3.14 / 3.15"
    assert supported["node_versions"] == ["24.22.2", "26.13.0"], "Node.js 兼容范围必须逐字同时含两条 LTS 版本"

    project = cast("dict[str, Any]", _pyproject()["project"])
    spec = str(project["requires-python"])
    # 兼容范围不是「把下限抬成 3.15」：两条线都必须被 spec 放行，3.13 仍必须被挡住。
    for version in supported["python_versions"]:
        assert _spec_allows(spec, version), f"requires-python={spec!r} 把受支持版本 {version} 排除在外"
    assert not _spec_allows(spec, "3.13"), "3.13 解析不了 PEP 758 无括号多异常语法，下限不得回退"

    classifiers = [str(item) for item in cast("list[Any]", project["classifiers"])]
    for version in supported["python_versions"]:
        assert f"Programming Language :: Python :: {version}" in classifiers, f"classifiers 缺 Python {version}"


def test_formatter_targets_both_but_type_check_stays_on_minimum() -> None:
    tool = cast("dict[str, Any]", _pyproject()["tool"])
    targets = [str(item) for item in cast("list[Any]", tool["black"]["target-version"])]
    assert "py314" in targets and "py315" in targets, "black 目标版本必须同时钉住下限与上限"
    # 类型检查继续按**最低**支持版本裁决：改成 3.15 等于放弃 3.14 语义面；3.15 由 CI 追加一趟 mypy 覆盖。
    assert tool["mypy"]["python_version"] == "3.14", "mypy 基准版本被抬走会丢掉 3.14 的类型语义"
    assert tool["basedpyright"]["pythonVersion"] == "3.14", "basedpyright 基准版本被抬走会丢掉 3.14 的类型语义"
    # pyrightconfig.json 是 JSONC（允许整行 // 注释），先按行剥注释再交给 json；
    # 它若单独抬到 3.15，IDE 红线就与 basedpyright 的 3.14 基准分成两套尺度。
    pyright = cast(
        "dict[str, Any]", json.loads(re.sub(r"^\s*//.*$", "", PYRIGHT_CONFIG.read_text("utf-8"), flags=re.M))
    )
    assert pyright["pythonVersion"] == "3.14", "pyrightconfig 必须与 basedpyright 同值（既有同源锁）"


def test_version_predicate_actually_bites() -> None:
    # 判据自检：只断言「恒真表达式」的锁等于没锁。上界把 3.15 排除、下限抬到 3.15 两种漂移都必须被抓。
    assert _spec_allows(">=3.14", "3.15")
    assert not _spec_allows(">=3.14,<3.15", "3.15"), "自检漏抓：上界排除 3.15"
    assert not _spec_allows(">=3.15", "3.14"), "自检漏抓：下限抬到 3.15 会丢掉旧版"


# ───────────────────────── CI 面：测试矩阵与静态检查真的覆盖两端 ─────────────────────────


def test_ci_constants_and_matrices_cover_both_ends() -> None:
    consts = _consts(CI_FILE)
    supported = _supported()
    py_min, py_max = supported["python_versions"]
    # setup-node 按主版本装，故由完整版本号取首段；点号版本仍留在 pyproject 那一节做事实源。
    node_majors = [version.partition(".")[0] for version in supported["node_versions"]]
    assert consts["python_min"] == py_min
    assert consts["python_latest"] == py_max
    assert consts["python_build"] == py_min, "发布打包解释器仍应固定在最低支持版本"
    assert consts["node_version"] == node_majors[0], "Node 最低线不得从 24 抬走"
    assert consts["node_latest"] == node_majors[-1]
    assert json.loads(consts["python_matrix"]) == supported["python_versions"]
    assert json.loads(consts["node_matrix"]) == node_majors

    test_job = _job(CI_FILE, "test")
    matrix = cast("dict[str, Any]", cast("dict[str, Any]", test_job["strategy"])["matrix"])
    assert "python_matrix" in str(matrix["python-version"]), "test 矩阵未引用 python_matrix 常量"
    assert "node_matrix" in str(matrix["node-version"]), "test 矩阵必须按 Node 主版本展开，否则 26 永远没跑过 pytest"
    integration = _job(CI_FILE, "integration-verify")
    int_matrix = cast("dict[str, Any]", cast("dict[str, Any]", integration["strategy"])["matrix"])
    assert "node_matrix" in str(int_matrix["node-version"]), "运行时探测必须在两条 Node LTS 上都验证"


def test_ci_static_and_type_checks_exercise_python_315() -> None:
    static_runs = _step_runs(_job(CI_FILE, "static"))
    assert (
        "--target-version py314" in static_runs and "--target-version py315" in static_runs
    ), "static 的 black 必须显式传两个目标版本（门禁约定不隐式继承 pyproject）"
    typecheck_runs = _step_runs(_job(CI_FILE, "typecheck"))
    assert "--python-version 3.15" in typecheck_runs, "缺 3.15 语义的 mypy 复核趟"
    assert re.search(r"(?m)^\s*mypy\s*$", typecheck_runs), "最低版本基准趟（无参 mypy）不可被顶掉"


def test_issue_templates_offer_both_python_versions() -> None:
    # 用户报障时选不到 3.15，等于把新版支持藏起来：四个模板（bug/question × 中英）都要列全。
    # 与 CI 常量同源，仍从 pyproject 那一节取受支持版本，不在本锁里再抄一份清单。
    names = ("bug.yml", "bug_en.yml", "question.yml", "question_en.yml")
    wanted = {f"Python {version}" for version in _supported()["python_versions"]}
    assert len(names) == 4
    for name in names:
        path = ROOT / ".github" / "ISSUE_TEMPLATE" / name
        assert path.is_file(), f"缺少 issue 模板 {name}"
        doc = cast("dict[str, Any]", yaml.safe_load(path.read_bytes().decode("utf-8")))
        # 只认「选项里本来就有 Python 3.x」的那个下拉，避免把系统/浏览器下拉的选项混进来凑够数。
        groups: list[set[str]] = []
        for item in cast("list[Any]", doc.get("body") or []):
            if item.get("type") != "dropdown":
                continue
            attrs = cast("dict[str, Any]", item.get("attributes") or {})
            options = {str(option) for option in cast("list[Any]", attrs.get("options") or [])}
            if any(option.startswith("Python 3.") for option in options):
                groups.append(options)
        assert len(groups) == 1, f"{name} 应恰有一个 Python 版本下拉，实际 {len(groups)} 个"
        assert wanted <= groups[0], f"{name} 的 Python 版本下拉缺 {sorted(wanted - groups[0])}"


def test_release_workflow_keeps_shared_constants_identical() -> None:
    # scripts/check_workflow_constants.py 只钉 python_build / node_version；本锁补一条同等口径的仓库内断言，
    # 防止「CI 扩了矩阵、发布流却还按另一套常量」却无人察觉。
    ci, release = _consts(CI_FILE), _consts(RELEASE_FILE)
    for key in ("python_build", "node_version"):
        assert ci[key] == release[key], f"{key} 跨 workflow 漂移（check_workflow_constants.py 会把 CI 判红）"


# ───────────────────────── 镜像面：两个运行时版本都有可构建、已钉定的入口 ─────────────────────────


def test_dockerfile_can_build_with_either_runtime() -> None:
    # 本机无 docker，故这里只能静态验「两条线都有入口且都钉住」；真实构建交回 CI/用户。
    # 哈希的值不复制进本锁：Dockerfile 是唯一持有者，本锁只认 64 位小写十六进制的形状。
    text = DOCKERFILE.read_bytes().decode("utf-8")
    assert "ARG PYTHON_VERSION=3.14" in text, "基础镜像版本必须可切，且默认仍是最低支持版本"
    assert text.count("FROM python:${PYTHON_VERSION}-slim-bookworm") == 2, "多阶段两段 FROM 必须共用同一版本变量"
    assert "ARG NODE_MAJOR=24" in text, "Node 主版本默认仍须是 24（旧线不降级）"
    for major in ("24", "26"):
        assert f"setup_{major}.x" in text, f"缺 Node {major} 的 NodeSource 源"
        pin = re.search(rf"ARG NODESOURCE_SETUP_SHA256_{major}=([0-9a-f]{{64}})", text)
        assert pin, f"Node {major} 的 NodeSource 脚本必须钉 64 位小写十六进制"
        assert _SHA256_RE.fullmatch(pin.group(1)), f"Node {major} 的钉定值形状非法"
    assert "exit 1" in text, "未登记的 NODE_MAJOR 必须 fail-closed，不得静默回落到某个版本"
