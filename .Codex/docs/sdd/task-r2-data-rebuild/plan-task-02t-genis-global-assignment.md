# 任务 02T：GeNIS 全记录全局唯一包序列分配实施计划

> **执行代理要求：** 使用 `subagent-driven-development` 执行本计划；本任务不使用测试驱动开发，不运行格式化、Pyright、pytest、冒烟或无关 Git 检查。

**目标：** 在不使用 `Dur`、`TotBytes`、标签或测试结果选择包序列的前提下，为 3,973 条冻结 GeNIS 候选建立全记录全局唯一包序列身份，并在身份锁定后按 Argus/HERA 逆像区间验收 `Dur`。

**架构：** Rust 工具按每个 10 秒流成员加载全部流记录和对应 PCAPNG 包，先按规范化五元组、记录顺序、粗时间窗及包数约束求连接内互斥分段，再对冻结候选提取唯一身份。`Dur` 只在身份锁定后参与表示链验收，绝不参与分段选择。

**技术栈：** Rust 发布构建、现有 `r2_genis_totbytes_verifier`、官方 GeNIS ZIP、确定性 JSON/Parquet 审计输出。

## 全局约束

1. 官方归档、冻结候选、标签、候选比例和最终测试不得修改或读取后反向调参。
2. 包序列分配不得使用 `Dur`、`TotBytes`、类别标签、攻击名称或模型结果。
3. 同一包不能被多个流记录消费；零解和多解均失败，不允许最近邻兜底。
4. `Dur` 按“微秒端点差 → `float32` → 六位输出 → Pandas 重写”的样本级逆像区间验收，不设置固定 1,000 纳秒容差。
5. 任一候选身份缺失、多义、逆像为空或实际跨度不在合法区间，整体保持 `NO-GO`。
6. 运行中使用 `.partial` 目录；只有全部门禁通过才原子发布审计结果。

## 文件范围

- 修改：`thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/flow.rs`
- 条件修改：同一 Rust 工具内承载新增证据字段所必需的模型或输出模块
- 禁止修改：官方 ZIP、冻结清单、标签、候选生成器、TQH-C2、ns-3 和训练代码
- 新增报告：`.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-02t-genis-global-assignment.md`
- 正式审计根：`thesis/experiments/llm_probe/runs/data-audit/r2-genis-global-assignment-v0/`

## 执行步骤

- [x] 读取任务 02S 报告、现有 Rust 数据结构和真实输入参数，记录修改前源码 SHA-256。
- [x] 将成员读取从“仅候选流记录”改为“同一成员全部 10 秒流记录”，保留原始记录顺序和来源行号。
- [x] 按规范化五元组建立连接组，并生成不依赖 `Dur`、`TotBytes` 和标签的可行包分段。
- [x] 对连接组执行全局互斥分配，显式区分唯一、缺失和多义身份。
- [x] 身份唯一后计算发布 `Dur` 的逆像候选集合与合法跨度区间，并验收实际首末包跨度。
- [x] 输出至少包含 `all_rows_loaded`、`candidate_identity_unique`、`candidate_identity_missing`、`candidate_identity_ambiguous`、`dur_inverse_empty`、`dur_interval_match`、`dur_interval_mismatch` 和 `repeated_flow_id_candidate_count`。
- [x] 保留总包数、双向包数、五元组、二层字节和网络层字节的逐条审计；身份失败与时长失败分开计数。
- [x] 执行一次 `cargo build --release`；编译失败只修复直接编译错误，不扩大范围。
- [x] 从官方输入全量运行全部 3,973 条候选，记录 11 个成员、包总数、耗时、峰值内存、输入与输出 SHA-256。
- [x] 仅当 `candidate_identity_unique == 3973`、身份失败均为 0、`dur_interval_match == 3973` 且所有既有包/字节门禁通过时裁决本任务 `GO`；否则保留失败制品并裁决 `NO-GO`。
- [x] 写入任务报告，明确结果只解除 GeNIS 身份与 `Dur` 门禁，不自动代表 R2 总数据门禁通过。

## 当前状态

**已完成，裁决 `NO-GO`。** 最终有效扫描完成且无结构性错误；`3973` 条候选中身份唯一 `3810`、缺失 `163`、歧义 `0`，身份唯一样本中 `Dur` 区间匹配 `3716`、不匹配 `94`。正式结果见 `thesis/experiments/llm_probe/runs/data-audit/r2-genis-global-assignment-v0/`，完整证据见 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-02t-genis-global-assignment.md`。本任务不再继续修补或重扫。
