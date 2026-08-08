# 任务 06Q：QUIC qlog 物理辅助池审计器独立复审

> 复审日期：2026-08-03  
> 复审方式：只读代码与制品审查  
> 复审裁决：**无严重问题，存在 2 项重要问题；工程验收暂不通过**

## 1. 结论

Rust 审计器的输入逐文件哈希、流式解析框架、十进制定点时间换算、内容摘要去重、PTO 缺失掩码、部署字段与训练期特权真值的角色声明，以及两次构建的确定性均有有效实现和制品证据。正式候选根与第二次验证根的 7 个文件逐一具有相同字节摘要；59 条候选的内容摘要和轨迹标识均唯一，16 条先导轨迹确实按候选内容 SHA-256 升序取得，未读取攻击标签或模型结果。

但是，当前实现没有完整执行计划规定的严格语义门禁。ACK、丢包和发送包之间的包号空间、包号归属和时间关系没有验证；解析过程中登记的核心字段、单位和 ACK 异常也没有进入候选裁决或输出制品。因此，现有 59 条轨迹可以继续作为**待修复的先导输入**，但不能升级为已经通过工程验收的正式 QUIC 物理辅助池。先导物化可以并行继续；在用这些真值形成实验结论前，必须完成最小修复并重新双构建。

## 2. 重要问题

### 2.1 ACK 与丢包只验证字段存在，未验证物理关系

**位置：**

- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:196`
- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:205`
- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:268`
- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:282`

`observe_ack_frame` 只确认 `acked_ranges` 的元素是一个或两个非负整数，并累计范围数量。它没有保留承载 ACK 帧的包号空间，也没有确认范围内的包号属于同一空间、由对向端点先前发送且发生在 ACK 之前。`observe_packet_lost` 同样只要求 `packet_type`、`packet_number` 和非空 `trigger`，没有确认丢失包属于本端先前发送的包集合或丢包事件晚于发送事件。候选门禁最终只检查这些计数是否大于零。

这意味着一条轨迹可以同时“拥有三个包号空间、某个 ACK 范围和某个丢包事件”而通过门禁，但这些证据不一定构成可用于 QUIC 动力学监督的同空间确认与丢包关系。计划要求的“ACK 范围或首次确认关系”和包号空间语义尚未被证明。

**最小修复要求：**

1. 按 `initial`、`handshake`、`application_data` 分别维护本观察端点已发送包号及发送时间。
2. 解析 ACK 时继承承载该 ACK 的包号空间，验证范围合法、属于对向已发送包集合，并记录首次确认时间；至少要求应用数据空间存在有效关系。
3. 对 `packet_lost` 验证同空间包号已由本端先前发送，且丢包事件时间不早于发送时间。
4. 在候选制品中输出分空间的有效 ACK、有效丢包和无法关联计数，不再用原始字段存在计数代替关系门禁。

### 2.2 已登记的核心语义异常没有进入门禁或审计制品

**位置：**

- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:115`
- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:151`
- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:205`
- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:242`
- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:282`
- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:822`

解析器会把事件时间量级异常、无法映射的包号空间、缺失包号或包长、非法 ACK 范围、无法解释的 RTT、缺失在途字节和拥塞窗口等写入 `TraceAudit.issues`。但是 `core_gate_failures` 没有检查 `issues`，`TraceManifestRow` 和排除制品也没有输出候选的异常数量或类型。

部分异常会被其他计数间接挡住，但不是全部。例如，只要至少存在一组完整 RTT、一个有效 ACK 范围及一个合法拥塞窗口，同一轨迹中的其他不可解释核心事件仍可被忽略而通过。事件时间超出声明的绝对 Unix 毫秒量级也只写入 `issues`，不会使候选失败。这与计划中“字段存在但单位、观察点或时序不可解释也要排除”的硬门禁不一致，也使现有制品无法证明 59 条候选没有被忽略的核心异常。

**最小修复要求：**

1. 将核心语义异常拆为硬失败与允许缺失两类；硬失败直接进入 `core_gate_failures`。
2. 对允许缺失的字段输出逐轨迹显式掩码和缺失计数，不得只输出轨迹级全真布尔值。
3. 在 `trace-manifest.jsonl` 或单独审计制品中保留候选的异常计数，确保“无被忽略硬异常”可以从制品复核。
4. 修复后重新执行两次全量审计并逐文件比较；候选数量如有变化必须如实记录。

## 3. 建议项

### 3.1 输入锁应把清单摘要和清单路径集合设为可执行断言

**位置：** `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:976`

当前代码逐项核对清单中的文件哈希、文件数和总字节数，实际固定提交与清单摘要也与报告一致。但工具没有把预期清单 SHA-256 作为输入断言，也没有拒绝清单中的重复相对路径或核对清单路径集合与固定提交的普通文件集合完全一致。建议在后续最小修复中加入预期清单摘要、路径唯一性和 Git 树集合核对，避免输入清单被替换后仍依赖总数与总字节碰巧相同。

### 3.2 被排除 qlog 的非 qlog 内容别名没有登记

**位置：** `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs:771`

别名登记只在 qlog 通过核心门禁后执行。因此，被排除的 `QUIC_1K_IT.qlog` 对应 `.json` 内容别名没有进入 `excluded-traces.jsonl`；当前 35 行排除制品由 30 条 qlog 与 5 条候选的非 qlog 别名组成。该问题不造成候选重复计权，但会使“所有逻辑路径均有去重映射”的审计记录不完整。

## 4. 已通过核验

1. **输入锁现状：** 本地固定提交为 `f237a20360b83868a197488c5b557f53e4b7e53c`；源清单 SHA-256 为 `ad4924be38968925ea0532d32e643709b40f7f852c863108cbd165addf4ecd61`，与报告一致。
2. **流式解析：** 使用 Serde 自定义访问器逐 trace、逐 event 解析；每次事件只实例化当前 `data`，没有把完整 qlog 载入 `Value`。
3. **时间换算：** 毫秒十进制定点值最多保留 6 位小数并乘 `1,000,000` 转为整数纳秒，没有经过二进制浮点。
4. **内容去重：** 59 条候选的 `content_sha256` 与 `trace_id` 均为 59 个唯一值；现有重复组均为 `.qlog` 与非 qlog 内容别名，候选未重复计权。
5. **先导选择：** 16 条先导的摘要严格升序，排名为 1 至 16；选择过程在通过门禁后只按内容摘要排序，路径仅作为摘要相同时的次级排序，而候选摘要当前无重复。
6. **角色隔离：** 59 条候选的 `malicious_label` 全部为 `null`，观察点全部为 `server`；PTO 真值全部保持缺失，没有从丢包或时间间隔推断。
7. **双构建：** 正式候选根与 `r2-quic-mednetcom-v0.build-b-verified` 的 7 个对应文件 SHA-256 逐一相同，且与任务报告登记值一致。
8. **代码锁：** `Cargo.toml`、`Cargo.lock`、`src/main.rs` 的 SHA-256 分别为 `d685999b2badb8866c166c169268133d71b7ae52c659a8ac1f337d74675de74a`、`f49c0f8905c7216302182fd60cdd7592ae90687d91f3454f58667f5f56d3296b` 和 `57137964833637462e36cd8fc5aa860bd5b95da784dda1d4436cd86ece9df309`，与报告一致。

## 5. 验证边界

- 本次没有修改生产代码、计划、候选制品或原始数据。
- 按任务要求，没有运行格式化、构建、Clippy、Pyright、Ruff、pytest、冒烟或 `git diff`。
- 执行的只读核验包括文件读取、行数统计、SHA-256 复算、固定提交查询和 JSONL 结构汇总。
- 当前结论只审查任务 06Q，不扩大到后续窗口物化、物理旁路模型或 R2 大模型训练。

## 6. 后续修复状态

本报告中的裁决针对 `src/main.rs` 旧摘要 `57137964833637462e36cd8fc5aa860bd5b95da784dda1d4436cd86ece9df309` 及其 59 条旧候选。旧候选目录已经添加失效标记并保留为历史证据。

2026-08-03 已按本报告两项重要问题完成最小修复。修复版 `src/main.rs` 摘要为 `aba88b492c0fce0604d9a7e0cbc595fcdcc7c6f7db8850786a378fd43633abb8`；修复后双全量审计仍得到 59 条候选和 16 条先导，候选有效 ACK 关系 1,421,638 条、有效丢包关系 3,777 条，无法关联关系和核心异常均为 0。新制品位于：

- `thesis/experiments/llm_probe/runs/data-audit/r2-quic-mednetcom-v1-ack-semantics-gate-review-pending.build-a/`
- `thesis/experiments/llm_probe/runs/data-audit/r2-quic-mednetcom-v1-ack-semantics-gate-review-pending.build-b/`

上述新结果的数据门禁为 GO，但本报告没有复审修复后的代码；其工程状态继续标记为 `review_pending`，应由新的独立代理复审，不得把本节视为复审通过。
