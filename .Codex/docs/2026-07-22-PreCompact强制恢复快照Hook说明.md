# PreCompact 强制恢复快照 Hook 说明

## 用途

该项目级 Hook 在 Codex 执行手动或自动上下文压缩前，更新以下两份文档中的唯一自动快照区块：

- `output/开题改进交接文档.md`
- `output/第一创新点实验总控.md`

Hook 只复制活动计划已经写入的 `## 当前状态`，并记录触发时间、来源修改时间和强制恢复顺序。它不访问网络、GPU 服务器、SSH、凭据或 SwanLab，也不调用 `codex exec`。因此它不能替代实验代理及时写回活动计划。

## 文件

- Hook 注册：`.codex/hooks.json`
- Hook 脚本：`.codex/hooks/precompact_snapshot.py`
- 活动计划配置：`.codex/precompact_snapshot.json`
- 样例输入：`.codex/hooks/tests/precompact-input.json`
- 隔离测试：`.codex/hooks/tests/test_precompact_snapshot.py`

## 版本与真实契约

本实现按本机 `codex-cli 0.144.5` 和 OpenAI 官方同版本源码核验：

- `PreCompact` 是原生事件，匹配值为 `manual` 或 `auto`。
- 命令 Hook 从标准输入接收 JSON。
- 输出字段为 `continue`、`stopReason`、`suppressOutput` 和 `systemMessage`。
- 项目 `.codex/hooks.json` 由项目配置层发现。
- 命令处理器超时设置为 8 秒；正常更新输出 `continue: true`，不会阻止压缩。
- 写入失败或来源缺失时输出 `systemMessage`，仍以 `continue: true` 继续压缩，并保留原文档。

官方核验入口：

- [Hook 配置结构](https://github.com/openai/codex/blob/rust-v0.144.5/codex-rs/config/src/hook_config.rs)
- [PreCompact 输入与运行行为](https://github.com/openai/codex/blob/rust-v0.144.5/codex-rs/hooks/src/events/compact.rs)
- [PreCompact 输入模式](https://github.com/openai/codex/blob/rust-v0.144.5/codex-rs/hooks/schema/generated/pre-compact.command.input.schema.json)
- [PreCompact 输出模式](https://github.com/openai/codex/blob/rust-v0.144.5/codex-rs/hooks/schema/generated/pre-compact.command.output.schema.json)
- [项目 Hook 发现与信任](https://github.com/openai/codex/blob/rust-v0.144.5/codex-rs/hooks/src/engine/discovery.rs)

## 首次启用

1. 结束并重新启动 Codex。Hook 注册表在会话创建时加载，当前会话不会自动采用新建的 `.codex/hooks.json`。
2. 在新会话中运行 `/hooks`。
3. 找到项目来源的 `PreCompact` Hook，核对命令为 `python3 .codex/hooks/precompact_snapshot.py`，然后批准信任。
4. 若整个项目尚未被 Codex 信任，还需先按启动提示信任当前项目；未信任项目不会加载项目级配置与 Hook。
5. 再次通过 `/hooks` 确认 Hook 状态为已启用且已信任。

Codex 0.144.5 的信任哈希覆盖标准化 Hook 配置身份，不覆盖被调用脚本或活动计划内容。因此修改 Hook 脚本后必须人工复核代码；仅依赖 `/hooks` 的“已信任”状态不能发现脚本内容变化。

## 切换活动计划

修改 `.codex/precompact_snapshot.json` 中的 `active_plan`：

```json
{
  "enabled": true,
  "active_plan": ".Codex/docs/sdd/task-18-example/task_plan.md"
}
```

路径必须是项目内相对路径，目标必须包含且只能包含一个 `## 当前状态` 章节。该配置由脚本在每次执行时读取，切换后无需重启 Codex。

## 手动测试

运行隔离测试：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 .codex/hooks/tests/test_precompact_snapshot.py
```

使用真实样例输入更新两份恢复文档一次：

```bash
python3 .codex/hooks/precompact_snapshot.py < .codex/hooks/tests/precompact-input.json
```

检查快照区块数量：

```bash
rg 'PRECOMPACT_SNAPSHOT_(START|END)' output/开题改进交接文档.md output/第一创新点实验总控.md
```

运行 `/compact` 后，可在 `/hooks` 和 Hook 执行提示中确认 `PreCompact` 是否实际触发。需要更详细的运行诊断时，重启时为 Codex 设置日志目录并检查 Hook 开始、完成或失败事件。

## 禁用与恢复

无需删除文件。将 `.codex/precompact_snapshot.json` 的 `enabled` 改为 `false` 即可立即停用写入：

```json
{
  "enabled": false,
  "active_plan": ".Codex/docs/sdd/task-17-observability/task_plan.md"
}
```

也可以通过 `/hooks` 禁用该处理器。后者会把状态写入用户级 Codex 配置；重新启用时仍通过 `/hooks` 管理。修改 `.codex/hooks.json` 后应重启 Codex。

## 运行限制

- 快照只反映活动计划磁盘上的 `## 当前状态`，不会检查服务器实时状态。
- 两份文档分别采用同目录临时文件、刷新和 `os.replace` 原子替换；并发触发由项目级文件锁串行化。
- 写入前会同时读取并验证两份文档。边界标记缺失一半、重复或来源缺失时均不写入。
- 两文件系统不存在真正的跨文件原子事务。第二个替换失败时脚本会尽力用原内容原子回滚第一个文件，并通过 `systemMessage` 报告。
- Hook 仅适用于提供 `fcntl` 的类 Unix 环境；当前 macOS 环境满足该条件。
- 当前机器的 Codex Doctor 报告既有 SQLite 状态库完整性失败。本实现已使用隔离状态目录完成 `hooks/list` 发现验证，但首次重启和 `/hooks` 批准仍需以真实会话结果为准；本任务未擅自移动或重建用户状态库。
