# PreCompact 强制恢复快照 Hook 核验笔记

## 本机事实

- Codex 版本：`codex-cli 0.144.5`。
- `codex features list` 显示 `hooks` 为稳定且启用状态。
- 官方同版本源码归档：`/tmp/codex-rust-v0.144.5/`。

## 已确认接口

- `PreCompact` 和 `PostCompact` 均存在于同版本配置模式与运行时。
- `PreCompact` 请求由运行时构造，包含会话、轮次、工作目录、转录路径、模型和 `manual|auto` 触发原因。
- 命令处理器支持 `command`、可选 `commandWindows`、`timeout`、`statusMessage` 和 `async`。
- Hook 运行受信任哈希控制，项目级来源与用户级来源分开标识。

## 官方 0.144.5 结论

- 项目配置层的 `.codex` 目录会自动查找 `hooks.json`，外层结构必须是 `description` 与 `hooks`。
- `PreCompact` 的匹配目标是 `manual` 或 `auto`；省略匹配器表示全部，本任务显式使用 `manual|auto`。
- 标准输入必填字段为 `session_id`、`turn_id`、`transcript_path`、`cwd`、`hook_event_name`、`model` 和 `trigger`；子代理上下文可额外包含 `agent_id` 与 `agent_type`。
- 合法标准输出只允许 `continue`、`stopReason`、`suppressOutput` 和 `systemMessage`。本任务失败时仍返回 `continue: true`。
- Hook 默认为同步执行，命令超时由 Codex 强制实施；本任务配置为 8 秒。
- 未受信任或配置修改后的 Hook 不进入实际处理器列表。`/hooks` 将当前配置哈希写入用户级 `hooks.state`。
- 信任哈希由标准化 Hook 配置生成，不包含脚本文件内容；脚本变更需要人工代码复核。
- 项目本身未获信任时，项目级配置和 Hook 会被配置层禁用。

## 实现决定

- Hook 脚本从自身位置推导项目根目录，不信任输入中的 `cwd` 作为写入根目录。
- 活动计划只能通过小型配置文件切换，恢复文档路径固定在脚本中，防止配置将写入目标改到其他文件。
- 每个目标采用同目录临时文件和 `os.replace`；并发调用通过 `/tmp` 中按项目路径散列的文件锁串行化。
- 任一前置校验失败时不写入任何目标；提交中途失败时尽力回滚已替换文件。

## 验证结果

- Python 隔离测试 6 项全部通过，覆盖样例输入、临时副本文档、人工正文保留、重复触发、来源缺失、损坏边界和配置禁用。
- 真实两份恢复文档各更新一次，每份均只有一个起始和一个结束边界，Hook 输出为 `{"continue":true,"suppressOutput":true}`。
- 使用 Codex 0.144.5 官方输入与输出 JSON Schema 验证样例和成功输出，均通过。
- 使用隔离 `CODEX_HOME` 调用 Codex 0.144.5 App Server 的 `hooks/list`，成功发现一个项目级 `preCompact` 命令处理器；命令、匹配器、8 秒超时和状态消息均与配置一致，`warnings` 与 `errors` 为空。
- 新 Hook 当前为 `untrusted`，这是预期状态；必须重启会话后在 `/hooks` 中人工核对并批准。
- 本机真实用户状态库的 Codex Doctor 完整性检查失败，独立 App Server 因此无法使用真实状态库启动。本任务没有移动、重建或修改该状态库。
