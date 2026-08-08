# PreCompact Hook 修复报告

- **日期**：2026-08-04
- **结论**：旧单私有计划、D1/D2 和重复恢复顺序的回写路径已移除。当前活动计划显式指向 R2 最终物理旁路正式实验计划；计划无法可靠读取时，快照写入“未设置”，不扫描最近修改文件，也不回退到历史计划。

## 1. 根因

1. `.Codex/precompact_snapshot.json` 的 `active_plan` 一直保留 `.Codex/docs/sdd/task-single-private-structure-diagnosis/task_plan.md`。该文件仍存在，因此旧脚本的文件存在性检查持续通过。
2. `.Codex/hooks/precompact_snapshot.py` 无条件读取配置指向计划中唯一的 `## 当前状态`。旧计划的该章节仍描述 D1、D2 正式训练，因而每次 PreCompact 都会把该状态重新写入两份恢复文档。
3. 生成模板静态拼接“### 强制恢复顺序”，与 `AGENTS.md` 和恢复正文重复。该内容不是来自两份恢复正文，也不是由当前实验状态推导得到。

修复前已在 `/tmp/precompact-root-cause.ylERMi` 隔离复现：Hook 返回成功后，两份文档副本分别命中旧计划路径、D1/D2 和“强制恢复顺序”，每份共 3 个禁用词命中。

## 2. 修改内容

### `.Codex/precompact_snapshot.json`

- 将 `active_plan` 显式更新为 `.Codex/docs/2026-08-04-R2最终物理旁路正式实验计划.md`。

### `.Codex/hooks/precompact_snapshot.py`

- 自动快照只生成触发时间、当前活动计划、当前执行态摘要和“服务器事实需实时核验”声明。
- 删除触发方式、三个文件修改时间及整段“强制恢复顺序”。
- 不按文件修改时间或目录顺序猜测活动计划。
- `active_plan` 缺失、为 `null`、为空、非法、目标不存在或无法提取唯一 `## 当前状态` 时，计划和执行态均写为“未设置”。
- 保留原有双文档原子替换、并发锁、边界标记唯一性检查和失败时保留原文的行为。

### `.Codex/hooks.json`

- 将说明和状态提示改为“活动计划快照”，不再暗示 Hook 负责重复注入恢复协议。
- PreCompact 事件、匹配器、命令和超时未改变。

### 两份恢复文档

- 真实运行一次 Hook 后，仅自动标记区块发生变化。
- `output/开题改进交接文档.md` 和 `output/第一创新点实验总控.md` 的人工主体未手工修改。

## 3. 隔离试运行

修复后先在 `/tmp/precompact-dry-run.3jmKnL` 复制两份恢复文档、活动计划和配置，再通过 `--project-root` 执行隔离试运行：

- Hook 输出：`{"continue":true,"suppressOutput":true}`。
- `task-single-private-structure-diagnosis|D1、D2|强制恢复顺序`：两份副本均为 0 命中。
- `PRECOMPACT_SNAPSHOT_START|PRECOMPACT_SNAPSHOT_END`：每份副本共 2 个标记，即一对起止标记。
- 快照时间为 `2026-08-04T13:06:33+08:00`。
- 当前活动计划为 `.Codex/docs/2026-08-04-R2最终物理旁路正式实验计划.md`。
- 当前执行态摘要来自该计划唯一的 `## 当前状态`。

另在 `/tmp/precompact-unset.kLnpZU` 不复制活动计划，用同一显式配置验证不可读路径：

- 两份副本均写入“当前活动计划：未设置”和“当前执行态摘要：未设置”。
- 三个禁用词仍为 0 命中，没有回退到旧计划。

## 4. 真实运行

- 运行前副本：`/tmp/precompact-real-before.6sdMvp/`。
- Hook 输出：`{"continue":true,"suppressOutput":true}`。
- 真实快照时间：`2026-08-04T13:09:08+08:00`。
- 两份真实文档的三个禁用词均为 0 命中。
- 两份真实文档各保留一对快照边界标记。
- 与运行前副本执行逐文件统一差异检查，差异仅位于文件顶部的自动快照标记区块；标记区块后的人工主体无变化。

## 5. 最小验证

| 检查 | 结果 |
| --- | --- |
| `PYTHONPYCACHEPREFIX=/tmp/precompact-hook-pycache python3 -m py_compile .Codex/hooks/precompact_snapshot.py` | 通过，退出码 0 |
| `python3 -m json.tool .Codex/hooks.json` | 通过，退出码 0 |
| `python3 -m json.tool .Codex/precompact_snapshot.json` | 通过，退出码 0 |
| `rg 'task-single-private-structure-diagnosis\|D1、D2\|强制恢复顺序' output/开题改进交接文档.md output/第一创新点实验总控.md` | 0 命中，`rg` 退出码 1 |
| `rg -c 'PRECOMPACT_SNAPSHOT_START\|PRECOMPACT_SNAPSHOT_END' output/开题改进交接文档.md output/第一创新点实验总控.md` | 两份文档均为 2，即各一对标记 |
| `/tmp` 隔离试运行与真实文件运行 | 均返回成功对象 |

按任务边界未运行格式化工具、代码风格检查、单元测试框架、全仓检查或 Git 命令；没有运行 Prettier、pytest 或服务器操作。除修复前的预期症状复现外，没有意外失败。

## 6. 未来显式切换

1. 将 `.Codex/precompact_snapshot.json` 中的 `active_plan` 改为已经核验的项目内相对路径。
2. 目标计划必须包含且只包含一个 `## 当前状态`，该章节就是快照的当前执行态摘要来源。
3. 当前没有可靠活动计划时，将 `active_plan` 设为 `null`；下一次 Hook 会明确写入“未设置”。
4. Hook 不会按最近修改时间、文件名日期或目录顺序自动选择计划。切换研究任务时必须显式更新该配置。

## 7. 变更与边界

已变更：

- `.Codex/hooks.json`
- `.Codex/hooks/precompact_snapshot.py`
- `.Codex/precompact_snapshot.json`
- `.Codex/docs/2026-08-04-PreCompact-Hook修复报告.md`
- `output/开题改进交接文档.md` 的自动快照区块
- `output/第一创新点实验总控.md` 的自动快照区块

未变更：

- 实验代码、配置、测试和运行制品
- 两份恢复文档的人工主体
- 数据制品、服务器状态和实验结果
- `AGENTS.md` 与各级规则文件

## 8. 风险与生效条件

- 项目 Hook 在会话启动时加载；修改后的 Hook 配置需要新会话重新加载，并可能需要重新确认变更后的 Hook 哈希。
- 活动计划和其 `## 当前状态` 仍需人工维护。Hook 只忠实读取显式配置，不判断实验结论是否已落后。
- 自动快照不访问服务器；其中任何服务器相关事实都必须按恢复协议实时核验。
