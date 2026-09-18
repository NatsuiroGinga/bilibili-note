# 恢复卡状态感知提示 Hook 实现报告

## 结论

已新增可由 Codex 原生命令 Hook 调用的恢复卡状态检测器和配置化路由表。它只写待处理状态收据，并在 `UserPromptSubmit` 或 `PreCompact` 的确有新状态时返回短 `additionalContext`；不自动修改恢复卡、不返回阻断决策。

本轮未修改 `.Codex/hooks.json` 或 `.claude/settings.json`，因为二者在接手前已经是其他工作未提交修改。最小注册补丁已列于本报告，待主代理合并。

## 新增文件

- `.Codex/hooks/recovery_card_state_reminder.py`
- `.Codex/hooks/recovery_card_routes.json`
- `implementation-plan.md`
- 本报告。

## 行为

1. 由 `cwd` 与当前 payload 内的 `RESEARCH_ROUTE=DRIFT`、`DRIFT`、`DGA`、`RESEARCH_ROUTE=RWKV` 或 `RWKV` 哨兵确定唯一路线。双命中、无命中、非项目 cwd、缺恢复卡均静默跳过。
2. 读取受管 `status.json`/`result.json` 的终态、`thesis/methods` 的更新、可用的 goal 字段摘要、`SubagentStop` 最终消息摘要，并比较恢复卡 hash/mtime。
3. 仅在新终态、目标变化、子代理交付、方法文档更新或恢复卡滞后时提示。签名包含路线和完整状态快照，重复状态在 300 秒冷却期内不重复注入；同一原因的新 mtime 会重新触发。
4. 状态写入 `.Codex/docs/2026-09-08-恢复卡自动更新Hook/runtime-state/`。收据只保存相对路径、hash、mtime、终态和事件理由；不保存 prompt、原始实验样本或凭据。
5. `Stop` 和 `SubagentStop` 只更新收据，不使用 `decision:block` 延续或阻断会话。所有异常脱敏记录并以退出码 0 放行。

## Codex 兼容性

已核对官方 Codex Hooks 文档：项目 Hook 的规范发现位置为 `<repo>/.codex/hooks.json`；命令 Hook 支持，`prompt`/`agent` 处理器会被跳过；`UserPromptSubmit` 和 `PreCompact` 支持 `hookSpecificOutput.additionalContext`。本机配置状态已记录 `<repo>/.codex/hooks.json` 的信任项；macOS 上 `.Codex` 与 `.codex` 为同一实际目录。

## 最小注册补丁建议

待当前 `.Codex/hooks.json` 的其他修改落定后，在其 `hooks` 对象追加以下两个事件组。不要加入 `Stop` 阻断处理器。

```json
"UserPromptSubmit": [{
  "hooks": [{
    "type": "command",
    "command": "python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/recovery_card_state_reminder.py\"",
    "timeout": 3,
    "additionalContextLimit": 800,
    "statusMessage": "检查恢复卡状态"
  }]
}],
"PreCompact": [{
  "matcher": "manual|auto",
  "hooks": [{
    "type": "command",
    "command": "python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/recovery_card_state_reminder.py\"",
    "timeout": 3,
    "additionalContextLimit": 800,
    "statusMessage": "核对恢复卡状态"
  }]
}]
```

未同步 Claude：现有 `.claude/settings.json` 同样存在他人未提交的路径恢复改动；且本轮目标是核验并采用 Codex 原生事件与输出契约。待其所有者确认后，可将同一命令作为 Claude 的 `UserPromptSubmit` 与 `PreCompact` 非阻断处理器追加。

## 代理命名 Hook P0 审计

- 系统旧名：`drift_condmem_engineering_audit`。
- 当前职责别名：恢复卡提示注入与代理命名 Hook 实现（Terra，高强度）。
- 非法 `auxhead_baseline_code_review` 绕过的直接原因：`.Codex/hooks/agent_dispatch_guard.py` 未在当前 `.Codex/hooks.json` 注册，故运行时没有调用它；不是正则、模型或 effort 校验失效。
- 官方 Codex 文档说明 `spawn_agent` 经本地函数 Hook 路径以 `Agent` 匹配。guard 的 `AGENT_TOOL_NAMES` 已含 `Agent`、`spawn_agent`、`collaboration.spawn_agent`，而现有配置没有任何 `matcher: "Agent"` 处理器。
- 对真实 Codex 兼容 payload 的手工入口验证：`tool_name="Agent"` 加非法旧名输出 `ADG-NAME` 拒绝；合法 `drift_state_audit_terra_high` 通过既有 `--preflight`，输出 `{"valid":true,"violations":[]}`。
- 当前协作 `collaboration.spawn_agent` 是否进入本地 Hook 路径无运行收据；本次非法实际创建本身表明它未被项目 guard 拦截。不得声称自动覆盖协作工具。
- 已有可调用兜底：`python3 .Codex/hooks/agent_dispatch_guard.py --preflight` 从标准输入接收真实兼容 payload，违规退出 2。主代理应在调用 `collaboration.spawn_agent` 前执行该预检，直到实际 Hook 注册收据证明覆盖。

建议待配置冲突解除后，在 `PreToolUse` 追加：

```json
{
  "matcher": "Agent",
  "hooks": [{
    "type": "command",
    "command": "python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/agent_dispatch_guard.py\"",
    "timeout": 3,
    "statusMessage": "校验代理任务名与简报"
  }]
}
```

若此注册后协作工具仍无 Hook 收据，则保留上述显式 preflight，不能将其描述为已拦截。

## 已执行验证

- `/opt/miniconda3/envs/rwkv/bin/python -m py_compile .Codex/hooks/recovery_card_state_reminder.py` 通过。
- `jq empty .Codex/hooks/recovery_card_routes.json` 通过。
- 使用受管非敏感临时项目调用真实脚本入口：无路线输入无输出；DRIFT mtime 滞后输出一次 `additionalContext`；重复调用无输出；RWKV 在 `PreCompact` 输出一次；更新受管 `status.json` mtime 后只再输出一次；无效 JSON 退出 0；状态文件搜索不到敏感 prompt 标记。
- `agent_dispatch_guard.py` 的实际兼容 `Agent` 负例拒绝和正例 `--preflight` 通过。

## 风险

- 路线/状态脚本尚未注册到冲突中的 hooks 配置，因而需主代理合并补丁并在 `/hooks` 完成 Codex 信任后才会自动生效。
- 当前 Hook payload 未保证提供 Goal 字段；脚本仅在字段实际出现时观察其摘要，不能伪称已读取 Codex 内部 Goal 状态。
