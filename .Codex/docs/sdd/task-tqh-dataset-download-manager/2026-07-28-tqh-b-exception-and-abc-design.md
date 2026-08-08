# TQH-C2 B 受限门禁例外与 A/B/C 统一候选设计

## 状态与授权

- **状态**：已批准，待实现与独立审查。
- **授权时间**：2026-07-28。
- **适用输入**：TQH-C2 `1.0.1` 的 B/QUIC 12 个 cell。
- **禁止扩展**：不得把本设计解释为允许其他 profile、其他版本或任意 `gate.json=FAIL` 的输入进入派生流程。

## 问题定义

TQH-C2 B 的 12 个 `gate.json` 均保留旧统计脚本生成的总体 `FAIL`。独立逐行审计已确认标签、连接和 1.0.1 修订计数完整一致；旧门禁失败仅来自 QUIC 长流复用、类别比例和已解释的基础设施伪影。现有处理器在逐行审计前无条件拒绝所有 `FAIL`，因此无法区分已知的 B 版本修订与真实数据损坏。

## B 受限例外合同

处理器只在以下条件同时成立时接受源 gate 为 `FAIL` 的 cell：

1. 调用方声明的数据集版本严格等于 `1.0.1`。
2. cell 与 manifest 的 profile 严格等于 `B`。
3. `gate.json` 的失败硬检查集合只能是 `H1_c2_signal`、`H3_balance`、`H7_unknown_ratio` 的子集，且不得为空。
4. `H4_all_victims_present`、`H5_benign_gen_active`、`H6_no_invariant_violation` 必须存在且明确通过；其他未列入允许集合的硬检查也必须通过。
5. 标签 UID 与连接 UID 逐 cell 唯一且集合完全相等。
6. UID 连接后的源地址、源端口、目的地址、目的端口、传输协议五元组完全一致。
7. cell 名称、manifest、标签行中的 profile、interval、jitter 与 capture_id 完全一致。
8. 标签值全部属于固定合法集合。
9. `labeled.jsonl.counts.json` 与逐行标签重计完全一致，且 `invariant_violations=0`。
10. 修订后的 `flows_malicious_c2` 不低于 50；这只证明旧 H1 计数已被 1.0.1 修订，不放宽主任务标签定义。

任一条件失败都必须终止当前 cell，不得降级为告警。A 与 C 继续要求总体 gate 严格为 `PASS`。

## 审计输出

每个 B cell 的审计记录必须显式包含：

- `source_gate_status=FAIL`；
- 原始失败硬检查名与原始详情；
- `quality_acceptance=accepted_b_v1_0_1_revised_counts`；
- 受限例外原因；
- 修订计数来源 `labeled.jsonl.counts.json`；
- 逐行重计与修订计数是否一致；
- stale gate/manifest 计数与修订计数的差异；
- UID、五元组、元数据、标签合法性和不变量审计结果。

派生主任务仍只接受 `label_status=mapped` 的 `malicious_c2`、`benign` 与 `benign_external`。`unknown` 保持 `unresolved` 并排除，`malicious_recon` 与 `malicious_lateral` 保持辅助标签并排除。

## B 物化与验收

- 目标目录：`runs/data-frozen/dataset-v1-provisional/tqh-c2-B-20260728-v1/`。
- 原始 PCAP 与标签目录只读，不改名、不覆盖、不删除、不上传。
- 输出目录先写 `_INCOMPLETE`，全部制品与哈希完成后才能移除。
- 验收包括 12 个 cell、主键唯一、Parquet 可读、标签覆盖、包连接统计、字段泄漏、受限例外审计字段和全部登记哈希回读。
- B 阶段完成后立即更新任务报告、实验总控和防复发规则，再进入统一候选实现。

## A/B/C 统一候选结构

保留既有 `dataset-candidate-c-v0` 及其源码行为，不覆盖历史 C-only 产物。新增独立的统一候选物化入口，输入固定为三个已验收的暂定 profile 目录：

- A：`tqh-c2-A-20260728-v1`；
- B：`tqh-c2-B-20260728-v1`；
- C：`tqh-c2-C-20260724-v8`。

候选目标目录为 `runs/data-frozen/dataset-candidate-tqhc2-abc-v0/protocol/`，状态保持 `provisional`、`theory_selection`、`review_pending`。它不是完整三来源 `dataset-v1`，不得形成最终测试结论。

### 样本与字段

- `samples.parquet` 每个 `sample_id` 只保存一次，保持全局唯一。
- 四套实验协议只通过划分清单表达成员关系；同一样本可出现在不同 suite，但在同一 suite 内不得跨划分。
- 候选沿用已审查的 37 个无敏感信息树模型字段与固定标签映射。
- `unknown`、`malicious_recon`、`malicious_lateral` 不进入二分类候选。
- `samples.parquet` 不把某一 suite 或 split 写成样本固有属性；suite 与 split 是清单级元数据。
- 所有划分清单绑定同一个 `samples.parquet` SHA-256。

### 四套划分

1. `tqhc2_cell_indomain`：36 个完整 cell 按 `28/4/4` 分为训练、验证、测试。验证和测试各覆盖 A/B/C 三个 profile 与 30/300/1800/3600 四个 interval，并在可行时扩大 jitter 覆盖；在满足硬覆盖后确定性最小化样本比例相对 `80/10/10` 的偏差。
2. `tqhc2_leave_one_profile_out_A`：A 的 12 个 cell 全部作为测试；B/C 的 24 个 cell 按 `20/4` 分为训练/验证，验证覆盖 B/C 与四个 interval。
3. `tqhc2_leave_one_profile_out_B`：B 的 12 个 cell 全部作为测试；A/C 的 24 个 cell 按 `20/4` 分为训练/验证，验证覆盖 A/C 与四个 interval。
4. `tqhc2_leave_one_profile_out_C`：C 的 12 个 cell 全部作为测试；A/B 的 24 个 cell 按 `20/4` 分为训练/验证，验证覆盖 A/B 与四个 interval。

每套划分必须同时保证 cell 不跨划分、训练与验证包含良性和恶意标签、测试不参与选择或拟合。

## 可扩展物化策略

A 包观测有 1,576 万余行，统一候选不得把三个 profile 的包表一次性加载进内存。实现采用 Parquet row group 流式读取，并以主记录中的 `capture_group_id` 验证每个 row group 只属于一个 cell；同一 cell 的相邻 row group 合并后复用既有聚合与序列哈希逻辑。若 row group 混入多个 cell、cell 顺序回退、包样本不在主表、样本跨 cell 或包计数不一致，立即失败并保留 `_INCOMPLETE`。

## 复现与发布门禁

- 先在两个新的临时目录分别物化，比较全部非自引用制品逐字节一致。
- 每个 suite 分别执行身份、标签、组互斥、划分覆盖、重复签名、字段预算、清单绑定和可加载性审计。
- 新生产代码先运行服务器精确测试、Black 与 Ruff，再由新的审查代理检查严重和重要问题。
- 审查通过后才把其中一份原子发布到正式候选路径；不得覆盖既有目录。
- 原始 PCAP 永不上传。派生制品是否同步服务器须在本地验收后另行执行白名单 `rsync` 与远端哈希回读。

## 被拒绝的替代方案

- **删除 B**：违反用户保留 B 与 36 cell 完整候选的决定。
- **允许任意 gate FAIL**：会掩盖真实身份、不变量或数据完整性错误。
- **直接修改源 gate/manifest**：会破坏原始证据与可追溯性。
- **覆盖 C-only 候选**：会让已发布实验的构建器和哈希失去历史对应关系。
- **一次性读取全部包观测**：A/B 规模下存在不必要的内存峰值和失败风险。
