# AGENTS.md 渐进拆分 P0/P1 计划

## 目标

在不触碰 Skills、Hook、实验代码和 `output/` 恢复文档的前提下，完成 AGENTS 拆分 P0 与 P1，使 `llm_probe` 和 `scripts` 的项目规则链均低于默认 32,768 字节，并保留完整回滚证据。

## 阶段

- [x] P0：记录版本、信任状态、既有差异、三种启动目录的理论与实际活动链。
- [x] P0：保存根、`thesis`、`llm_probe` 原始规则快照、哈希和回滚说明。
- [x] P1：建立父规则到 `scripts/AGENTS.md` 的逐条迁移映射。
- [x] P1：先创建局部规则并完成 65,536 字节诊断验收。
- [x] P1：从父级删除已迁移原文，保留最小路由与共同启动器规则。
- [x] P1：执行默认预算新进程验收、Prettier 与 `git diff --check`。
- [x] 交付：生成阶段补丁、历史说明和实施报告，然后停止，不进入 P2 及以后。

## 文件边界

- 可修改：`thesis/experiments/llm_probe/AGENTS.md`。
- 可创建：`thesis/experiments/llm_probe/scripts/AGENTS.md`、`.Codex/docs/agents-split/` 下的计划、快照、补丁和报告。
- 禁止修改：Skills、Hook、实验代码、配置、测试、`output/` 下全部文件。

## 验收命令

- `prettier --write`，仅处理本任务 Markdown 文件。
- `git diff --check`。
- `codex --cd <目录> debug prompt-input`，核对默认预算下的实际注入哨兵。
- `codex --cd <目录> --config project_doc_max_bytes=65536 debug prompt-input`，仅用于中间诊断。
- 默认预算下重新核算逐文件字节数与合计。

## 决策

- 将调研已审计的 `llm_probe/AGENTS.md` 当前工作树版本作为 P0 基线；其相对 `HEAD` 的 19 条既有新增规则全部纳入快照，不丢弃、不回滚。
- 新增局部规则后先验收，再迁出父级原文；最终不得依赖 65,536 字节覆盖。
- P1 完成后停止，等待主代理与用户验收。

## 已遇错误

- 沙箱内创建 `.Codex/docs/agents-split/` 返回 `Operation not permitted`；已按权限流程在获批的沙箱外创建目录。
- 沙箱内运行 `codex debug prompt-input` 返回 `Operation not permitted`；已按权限流程使用只读沙箱外子进程。
- 普通沙箱中的 Prettier 无法写入两份 `.Codex/docs/` 文件；已按权限流程只对这两份文件在沙箱外重跑并通过。

## 状态

P0 与 P1 已完成并通过验收。任务停止于 P1，等待主代理与用户检查。
