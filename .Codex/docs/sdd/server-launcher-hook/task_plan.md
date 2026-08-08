# 服务器启动器安全 Hook 计划

## 目标

用纯标准库 PreToolUse Hook 机械拒绝服务器启动命令中先启用 `nounset`、后加载 `~/.bashrc` 的危险顺序，同时保留现有 PreCompact Hook。

## 文件范围

- 新建：`.codex/hooks/server_launcher_guard.py`
- 新建：`.codex/hooks/tests/test_server_launcher_guard.py`
- 修改：`.codex/hooks.json`
- 新建：`.Codex/docs/2026-07-30-服务器启动器安全Hook说明.md`
- 本计划：`.Codex/docs/sdd/server-launcher-hook/task_plan.md`

## 阶段

- [x] 核对根规则、过程文档规则、三个指定技能及现有 PreCompact 配置。
- [x] 实现 Hook 输入提取、服务器启动识别、脚本读取和顺序判定。
- [x] 登记 PreToolUse，确保 PreCompact 原样保留。
- [x] 增加标准库单元测试和显式预检说明。
- [x] 执行 Black、一次 Ruff、`py_compile`、`unittest`、JSON 解析和 `git diff --check`。

## 决策

- 错误顺序输出结构化 `deny`；正确或无关命令只中性放行，不主动授予权限。
- 只分析服务器远程执行、同步或启动上下文；普通本地 Shell 不受影响。
- 对可安全解析的本地 `.sh`、`.bash`、`.zsh` 和 `.exp` 文件读取内容；不存在、越界或无法解析时中性放行。
- 当前会话不假定 Hook 热加载，验证依赖 `--file` 和标准输入模式；重启 Codex 后生效。

## 验收

- `source ~/.bashrc; set -u` 放行，`set -u; source ~/.bashrc` 拒绝。
- 同时覆盖 `set -o nounset`、内联 `screen`、无关命令、Hook 输入和文件预检。
- `.codex/hooks.json` 仍完整包含原 PreCompact 项。

## 当前状态

任务已完成。12 项单元测试、Python 编译、Hook JSON 与原 PreCompact 等值检查、任务差异空白检查均通过；未操作服务器或实验目录。当前会话不会热加载新增 Hook，需重启 Codex 生效。

## 验证记录

- Black：两个 Python 文件格式化通过。
- Ruff：按要求只运行一次；唯一报告为未使用的 `typing.Any`，已删除该导入且未重复运行 Ruff。
- `py_compile`：两个 Python 文件通过。
- `unittest`：12 项通过。
- JSON：`.codex/hooks.json` 可解析，原 PreCompact 项与修改前逐字段一致。
- 空白检查：普通 `git diff --check` 返回成功；因 `.Codex/` 被忽略，另对五个实际文件逐一执行 `git diff --no-index --check`，均无空白错误输出。

## 已处理问题

- 隐藏目录首次格式化受沙箱写权限限制：使用获批的同范围沙箱外 Black 重跑成功。
- 初次 `unittest` 文件路径被解析为空模块名：改用标准 `discover` 入口后测试正常执行。
- 首轮测试发现组合短选项和换行边界漏检：根因为正则只接受 `u` 位于末尾，已扩展为识别 `set -euo` 等形式。
- macOS 临时路径存在 `/var` 与 `/private/var` 规范化差异：测试按 `resolve()` 后路径核对。
