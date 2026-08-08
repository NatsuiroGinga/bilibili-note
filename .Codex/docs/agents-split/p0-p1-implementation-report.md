# AGENTS.md 渐进拆分 P0/P1 实施报告

日期：2026-07-30

## 结论

AGENTS.md 拆分 P0 与 P1 已完成。P0 建立了可核验快照、活动链基线和回滚证据；P1 已把远程启动、环境、`rsync`、`screen`、服务器能力、`fd`/`rg`/`uv`、真实换行、Shell 引用、`tee`、`pipefail`/`PIPESTATUS`、重启恢复与脚本语法门禁从实验父级迁出。

最终 `llm_probe` 项目链为 30,693 字节，`scripts` 自动注入项目链为 32,334 字节，均低于默认 32,768 字节。P2、P3、P4 及以后未执行。

## 变更内容

### 规则文件

- 修改根 `AGENTS.md`：只增加一条 `scripts/AGENTS.md` 深层路由，不复制细则。
- 修改 `thesis/experiments/llm_probe/AGENTS.md`：保留凭据边界、统一启动器共同要求和脚本路由；删除已迁移的远程、同步、环境、恢复与 Shell 原文。
- 新建 `thesis/experiments/llm_probe/scripts/AGENTS.md`：加入 `NOTE_LLM_PROBE_SCRIPTS` 哨兵，常驻统一启动器、真实换行、能力预检、`rsync`、`screen`、`tee`/`PIPESTATUS` 和 `bash -n` 关键门禁。

### 过程制品

- `.Codex/docs/agents-split/20260730-130222/P0/`：三份原始规则快照、既有差异、基线和回滚说明。
- `.Codex/docs/agents-split/20260730-130222/P1/`：迁移映射、仅新增补丁、最终阶段补丁、验证记录和回滚说明。
- `.Codex/docs/agents-split/remote-script-execution-contract.md`：6,857 字节完整可执行合同。
- `.Codex/docs/agents-split/remote-script-rule-history.md`：能力、换行、管道和重启故障背景。
- `.Codex/docs/agents-split/task_plan.md` 与 `notes.md`：计划、决策和错误记录。

## 语义保留

父级完成约定迁移后，三层链已经占 30,693 字节，脚本层只剩 2,075 字节。把完整合同直接塞入子文件会再次超限。为避免提前实施 P2/P4 或删除规则，采用两级加载：

1. `scripts/AGENTS.md` 在启动时自动注入 1,641 字节关键门禁。
2. 任何脚本修改、同步或运行前，局部规则强制完整读取 `remote-script-execution-contract.md`。

完整合同保存迁移规则的全部条件、阈值、命令和故障门禁；历史说明单独归档，不进入常驻链。数据合同、训练科学变量、模型视图、生成式评测、SwanLab、Git 和 Python 测试选择规则未迁移。

## 验证情况

- Codex 版本：`codex-cli 0.144.5`；仓库信任状态为 `trusted`。
- P0 默认预算复现：`llm_probe` 与 P1 前 `scripts` 链均在 32,768 字节处实际截断；65,536 一次性诊断可见完整三层。
- P1 仅新增诊断：四个哨兵及日志、严格 Shell、`PIPESTATUS`、`fd`、`rg`、`uv` 规则全部可见。
- P1 最终默认诊断：根、`llm_probe`、`scripts` 三个新进程均获得预期哨兵，父级与脚本尾部完整可见。
- 模型行为验证：从 `llm_probe` 处理明确的脚本任务时，正确指出必须先读取 `scripts/AGENTS.md`。
- Prettier：本任务 Markdown 文件已格式化。
- `git diff --check`：通过。
- `git apply -R --check .../P1/stage.patch`：通过。
- P0 快照哈希复核：通过。

未运行代码测试、编译或服务器实验，因为本任务只修改 Markdown 规则和过程文档。

## 未修改范围

- 未修改 Skills、插件、Hook、`.codex/` 配置、实验源码、配置、测试或运行脚本。
- 未修改 `output/开题改进交接文档.md` 和 `output/第一创新点实验总控.md`；两者在任务开始前已有其他工作树改动，本任务没有覆盖。
- 未删除任何历史证据，未提交或推送 Git。

## 风险与停止点

- `scripts` 自动注入链只剩 434 字节余量。后续向根、`thesis`、实验父级或脚本局部文件增加规则前必须重新核算，不得依赖截断。
- 完整执行合同采用强制按需读取，而非全部常驻。若未来批准 P4 或项目 Skill，可再把长合同迁到更正式的渐进加载机制；本阶段不实施。
- P1 到此停止。P2、P3、P4 或 Hook、Skills 治理必须重新取得用户明确批准。
