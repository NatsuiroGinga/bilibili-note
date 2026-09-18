# 恢复卡状态感知提示 Hook 实施计划

## 目标与边界

- 目标：在 Codex 原生 `UserPromptSubmit`、`PreCompact`、`Stop` 与 `SubagentStop` 生命周期事件中，发现路线恢复卡相对受管状态源滞后时，以短 `additionalContext` 提醒主代理核验并委派文档代理写回。
- 不自动修改恢复卡，不输出阻断决策，不影响工具、实验或普通命令。
- 路线一次只解析一个。当前只配置 DRIFT、RWKV；无法唯一判定或缺规范恢复卡时静默跳过。

## 官方兼容性核验

- 官方 Codex Hooks 文档确认：项目 Hook 发现位置为 `<repo>/.codex/hooks.json`；命令 Hook 支持；`prompt` 与 `agent` 处理器会被解析但跳过。
- `UserPromptSubmit` 和 `PreCompact` 的 JSON 输出允许 `hookSpecificOutput.additionalContext`；`Stop` 与 `SubagentStop` 仅落状态收据，不以 `decision:block` 延续或阻断会话。
- 本工作树在 macOS 大小写不敏感文件系统上，`.Codex/` 与 `.codex/` 指向同一实际目录；现有 Codex 状态记录也指向 `<repo>/.codex/hooks.json`。

## 文件所有权

- 新增 `.Codex/hooks/recovery_card_state_reminder.py`。
- 新增 `.Codex/hooks/recovery_card_routes.json`。
- 最小追加 `.Codex/hooks.json`；若并发改动未获确认则暂不编辑。
- 仅当现有 Claude 配置的同构入口可安全复用时最小追加 `.claude/settings.json`；否则在报告中说明不同步。
- 新增本目录的实施报告。

## 检测算法

1. 由 `cwd` 是否属于项目和 `prompt`、`last_assistant_message` 的字面路线哨兵确定唯一 DRIFT/RWKV 路线；双命中、无命中均不注入。
2. 读取配置化恢复卡、方法文档与诊断运行根。扫描受管 `status.json`/`result.json` 的新终态、关键方法文档 hash/mtime、恢复卡 hash/mtime；可用 payload 中的 goal 字段变化和子代理最终消息哈希也记录为状态源。
3. 将仅含路径相对名、哈希、mtime、事件种类的摘要原子写入本目录 `state.json` 与 `events.jsonl`。不写 prompt 原文、域名、凭据、令牌或实验载荷。
4. 以状态签名加事件类型做去重。无变化不输出；有变化仅输出不超过数行的核验及文档委派提醒。`PreCompact` 可作为压缩兜底；`Stop`/`SubagentStop` 只更新收据。
5. 所有异常只以异常类型写入脱敏诊断并返回成功，不输出阻断 JSON。

## 代理命名附加审计

- 检查 `agent_dispatch_guard.py` 的匹配器与当前 Codex `collaboration.spawn_agent` 实际工具名/输入字段是否一致。
- 若原 Hook 无法观察协作工具，追加非阻断 `PreToolUse` 命令 Hook 或可执行 preflight 包装；对非法旧名给出真实负例验证，不触碰实验入口。

## 验收

```bash
python3 -m py_compile .Codex/hooks/recovery_card_state_reminder.py
jq empty .Codex/hooks.json
python3 .Codex/hooks/recovery_card_state_reminder.py < <事件JSON>
python3 -m py_compile .Codex/hooks/agent_dispatch_guard.py
git diff --check -- <本任务文件>
```

另执行真实命令 Hook 入口验证：无状态静默、受管非敏感 mtime 差单次提醒、重复去重、DRIFT/RWKV 路由切换、无恢复卡静默、异常不阻断、敏感 prompt 不落盘和协作代理非法命名负例。

## 技能收据

- `hook-development`：`/Users/bilibili/.agents/skills/hook-development/SKILL.md`，SHA-256 `3db8b26f91d0023caeee6e6e22de896067312423f24f55fbc914260e0247ca06`，读取时刻 `2026-09-08T14:05:25+0800`。
- `codex-hook-emulation`：`/Users/bilibili/.codex/skills/codex-hook-emulation/SKILL.md`，SHA-256 `84011df1cfed6e231a29f4c410c3b57c37531add2db662af1742f7f173470be9`，读取时刻 `2026-09-08T14:05:25+0800`。
- `openai-docs`：`/Users/bilibili/.codex/skills/.system/openai-docs/SKILL.md`，SHA-256 `7cb8fa1b2a0c635b5c61ffe1da7b8594a7ea0fce5b71e8d523e2025d88b2a05e`，读取时刻 `2026-09-08T14:05:25+0800`。
