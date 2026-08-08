# Hook-P0 调查笔记

## 环境证据

- 本机版本：`codex-cli 0.144.5`。
- 三个目标工作目录执行 `git rev-parse --show-toplevel` 均返回 `/Users/bilibili/personal/note`。
- 当前配置以 `python3 .codex/hooks/...` 调用脚本，因命令工作目录随会话变化而不稳定。
- 本机钩子命令解析到系统 Python 3.9；快照脚本的 `zip(..., strict=True)` 会在该解释器上抛出 `TypeError`，使快照静默保留旧文档。

## 官方契约

来源：<https://learn.chatgpt.com/docs/hooks>

- 命令钩子以会话 `cwd` 运行；仓库钩子应通过 `$(git rev-parse --show-toplevel)` 定位。
- `PreToolUse` 只支持顶层 `systemMessage` 以及专用的 `hookSpecificOutput`。
- `continue`、`stopReason`、`suppressOutput` 和 `permissionDecision: ask` 在 `PreToolUse` 中不受支持；返回这些字段会使钩子失败，并继续原工具调用。
- 中性放行的确定性形式是退出码 0 且不输出内容。
- 明确拒绝使用 `hookSpecificOutput.hookEventName=PreToolUse`、`permissionDecision=deny` 和 `permissionDecisionReason`。
- `PreCompact` 支持公共输出字段，因此本轮不因相同字段名改写其输出协议。

## 调查裁决

- `hook-development` 技能仍含提示型钩子、旧环境变量和通用输出示例，与当前版本冲突；实施以官方版本行为和仓库审计为准。
- `codex-hook-emulation` 适用于没有原生钩子的场景；本仓库已有原生钩子，本轮不增加第二套仿真机制。
- 本轮不扩展远程守卫检测范围，只修复已有守卫的执行可靠性。
- 为满足现有解释器兼容性，快照脚本只移除无必要的 `zip(..., strict=True)` 参数；两侧序列均由固定的两份恢复文档生成，不改变业务语义。

## 验证结论

- 配置中的两条命令从三个目标工作目录均能解析到同一仓库脚本。
- `PreToolUse` 正确顺序分支退出码为零且标准输出为空；错误顺序分支只输出受支持的拒绝对象。
- `PreCompact` 在隔离项目副本中从三个目标工作目录均能写入且重复更新单一快照区块，未触碰真实恢复文档。
- 真实 Codex 子进程因外部连接异常未产生工具调用；当前只能证明配置被加载，不能证明 Codex 运行时实际执行了拒绝。
- `.gitignore` 的 `.Codex/` 规则在当前大小写不敏感文件系统上同时忽略 `.codex/`；本轮文件不出现在普通 `git status` 中。该事实不影响本机运行，但会影响 Git 持久化，本轮按任务边界未改 `.gitignore`。
