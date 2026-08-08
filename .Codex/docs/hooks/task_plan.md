# Hook-P0 实施计划

## 目标

在不扩展守卫范围、不修改实验代码和 `AGENTS.md` 的前提下，使现有项目钩子在 Codex CLI 0.144.5 中使用受支持的输出协议，并能从三个目标工作目录稳定定位脚本。

## 任务边界

- 允许修改：`.codex/hooks.json`、`.codex/hooks/server_launcher_guard.py`、必要的钩子测试、`.Codex/docs/hooks/` 记录。
- 仅在路径验证确有需要时修改 `.codex/hooks/precompact_snapshot.py`。
- 禁止修改：实验代码、实验配置、`AGENTS.md`、服务器状态、Git 历史。
- 不新增守卫规则，不处理审计报告中的 P1 及以后候选。

## 阶段

- [x] 阶段一：读取审计、各级规则和钩子技能，核对 Codex CLI 版本及官方契约。
- [x] 阶段二：建立当前失败反例并完成最小协议与路径修复。
- [x] 阶段三：运行单元测试、格式化、静态检查和三目录集成验证。
- [x] 阶段四：写实施报告并复核变更范围。

## 验收命令

- `python3 -m unittest discover -s .codex/hooks/tests -p 'test_*.py'`
- `black --check .codex/hooks/server_launcher_guard.py .codex/hooks/precompact_snapshot.py .codex/hooks/tests/test_server_launcher_guard.py .codex/hooks/tests/test_precompact_snapshot.py`
- `python3 -m py_compile .codex/hooks/server_launcher_guard.py .codex/hooks/precompact_snapshot.py`
- `prettier --check .codex/hooks.json`
- 从仓库根、`thesis/experiments/llm_probe` 和 `thesis/experiments/llm_probe/scripts` 分别执行配置中的命令，覆盖中性放行、明确拒绝和隔离副本中的 `PreCompact` 快照。
- 在安全可控且不执行远程命令的前提下，尝试一次真实 Codex 子进程拒绝验证；若机制或环境阻塞，则明确记录为未验证。

## 根因与单一假设

- 根因一：`PreToolUse` 返回了 `continue` 和 `suppressOutput`，Codex CLI 0.144.5 会把该钩子标记失败并继续工具调用。
- 根因二：钩子命令使用 `.codex/hooks/...` 相对路径，命令以会话 `cwd` 运行，从子目录启动时找不到脚本。
- 假设：中性分支改为退出码 0 且无标准输出，拒绝分支只返回受支持的 `hookSpecificOutput`；配置按 Git 根解析脚本后，三目录均能得到相同结果。

## 当前状态

**已完成**：最小修复、三目录验证和实施报告均已落盘。

## 错误记录

- 沙箱拒绝直接创建 `.Codex/docs/hooks`，经限定路径授权后已创建；未扩大写入范围。
- 首次完整目标测试为 `21` 项，其中 `12` 项失败、`3` 项错误；失败准确覆盖旧输出字段和子目录相对路径，错误另暴露系统 Python 3.9 不支持 `zip(..., strict=True)`。
- 首次真实 Codex 子进程命令把全局 `--ask-for-approval` 放在 `exec` 之后，CLI 在启动前拒绝参数；按帮助信息移到顶层后成功启动。
- 第二次真实 Codex 子进程从 `scripts` 目录加载了项目钩子并进入模型回合，但外部 WebSocket 和多个 MCP 连接异常，模型只输出执行意图，未发出工具调用；因此不能把这一项记为真实拒绝通过。
