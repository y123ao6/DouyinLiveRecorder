# Linux 取数端点约束

> **约束事实源**: dlr-dev-playbook `references/known-pitfalls.md`「构建产物、依赖与运行时基线」下的
> 「发布链运行时二进制必须 fail-closed 钉定」。约束变更以 AGENTS.md 为准。

## Linux 取数端点约束

- **必须是 `releases/tags/<月末 autobuild 标签>`，不得用 `releases/latest` 或日更 autobuild 标签**。
- `latest` 是滚动别名（同名资产被上游重发即换 digest）。
- 日更标签上游只保留约两周（钉它等于预埋一次 404）。
- 月末标签才是 URL 与 digest 双双不可变的组合。
- 回归锁：`tests/test_build_exe.py::test_linux_ffmpeg_urls_pin_an_immutable_release_tag`。
