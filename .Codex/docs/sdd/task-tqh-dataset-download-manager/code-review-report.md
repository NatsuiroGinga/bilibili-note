# TQH-C2 C 候选协议独立代码审查报告

- **审查日期**：2026-07-24
- **审查结论**：批准修复后的候选协议用于 `theory_selection`
- **最终问题数**：严重 `0`，重要 `0`
- **范围限制**：不得用于最终超参数冻结或最终测试结论；不得操作或改变 TQH-C2 A/B 下载

## 1. 审查范围

- `thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate.py`
- `thesis/experiments/llm_probe/tests/test_tqh_c2_candidate.py`
- 修复后独立物化目录：
  - `/tmp/tqh-candidate-c-reviewfix-a-20260724/`
  - `/tmp/tqh-candidate-c-reviewfix-b-20260724/`
- 正式发布目录：`thesis/experiments/llm_probe/runs/data-frozen/dataset-candidate-c-v0/protocol/`

重点检查标签映射、完整 cell 划分、跨划分泄漏、`sample_id` 字段预算、`tcp_flags_applicable` 掩码、合法空值、辅助与未解析标签排除、原子发布、哈希绑定和确定性。

## 2. 初次审查发现

初次审查发现严重问题 `0`、重要问题 `2`，因此当时未批准发布或启动基线。

### 重要问题 1：标签映射未按行强制执行

原实现只确认映射样本最终同时出现 `benign` 与 `malicious`，没有逐行验证 `native_label -> binary_label -> label_status`。交换个别良性与恶意标签后，两类集合仍然完整，错误样本仍可能进入训练清单；同时审计文件会写入固定映射并标记为通过。

### 重要问题 2：TCP 标志派生未显式服从适用掩码

原实现只拒绝“掩码为真但 `tcp_flags` 为空”的记录。特征聚合先把空值填零，再仅依据传输族解释 TCP 标志，没有使用 `tcp_flags_applicable` 门控。掩码为假的 TCP 记录若残留非零标志，可能污染 SYN、ACK、FIN、RST 和 PSH 特征。

初次审查同时核验了当时的真实 C 输入。35,351 条候选样本的实际标签映射正确；396,041 个 TCP 包的适用掩码均为真，230 个 UDP 包的适用掩码均为假且 `tcp_flags` 为空。因此两项问题属于实现契约缺陷，没有发现既有真实数据已被污染。

## 3. 修复与回归覆盖

### 标签契约

- 新增固定 `LABEL_CONTRACT`。
- 对每条主记录逐行核对原生标签、二元标签和标签状态。
- 拒绝未知原生标签和任意不符合固定契约的组合。
- 只有 `mapped` 记录进入候选样本；`auxiliary` 与 `unresolved` 记录继续排除。

### TCP 标志掩码

- 要求适用掩码非空。
- 要求 `tcp_flags_applicable` 与 TCP 传输族一致。
- 校验 TCP 标志位于 9 位字段范围内。
- 掩码为假时拒绝非零 TCP 标志。
- 派生 TCP 位特征时显式使用 `tcp_flags_applicable` 门控。

### 新增测试

- 良性样本被错误映射为恶意时必须拒绝。
- 标签状态被错误改为辅助标签时必须拒绝。
- 原生标签与二元标签、标签状态不匹配时必须拒绝。
- 掩码为假却携带非零 TCP 标志时必须拒绝。
- 正向夹具使用非 TCP `tcp_flags=null`，覆盖真实输入中的 230 个合法空值。
- 输入失败后保留 `_INCOMPLETE`，成功后移除该标记。

## 4. 本地独立复核

### 稳定哈希

- 生产源码 SHA-256：`62b1c38e0539a7c824b1c4c57e027fdb192f020e6c54151deb1415c820aea4df`
- 测试源码 SHA-256：`349b5872dfa5eacac626a466e1c969ae8a8cda8ad90cc0e8e7788d6e85bc9972`
- 协议 SHA-256：`c779ef9ae5513262ddd1ce3a14b571d01ea5e6eff17c98d13f6a634d646030d9`

两份 `source-artifacts.jsonl` 均绑定上述生产源码哈希。

### 确定性与完整性

- A/B 两份修复候选执行 `diff -qr`，退出码为 `0`。
- A/B 各自执行 `shasum -a 256 -c audit/artifact-sha256.txt`，12 个非自引用制品全部为 `OK`。
- 本地正式目录与修复 A 执行 `diff -qr`，退出码为 `0`。
- 正式目录不存在 `_INCOMPLETE`。
- Black 检查通过，两个文件无需改动。
- Ruff 检查通过。
- 两个 Python 文件的抽象语法树解析通过。

### 数据协议核验

- 候选样本数：35,351。
- 完整 cell 数：12。
- 划分样本数：训练 29,175，验证 2,749，开发测试 3,427。
- 跨划分 `allocation_group_id` 数：0。
- 候选中非 `mapped` 样本数：0。
- 原生标签映射：`benign -> benign` 9,378 条，`benign_external -> benign` 13,169 条，`malicious_c2 -> malicious` 12,804 条。
- 模型输入字段数：37；`sample_id` 不在模型视图中；模型字段均非空且有限。
- TCP 传输族与适用掩码错配数：0。
- 掩码为假且 TCP 标志非零数：0。
- 非 TCP 且 TCP 标志为空数：230。

## 5. 服务器与正式发布验收

服务器恢复后完成了此前待执行的门禁：

- 服务器生产源码与测试源码 SHA-256 均与本地稳定哈希一致。
- `tests/test_tqh_c2_candidate.py` 精确回归结果为 `7 passed in 0.96s`。
- 服务器修复候选暂存目录的 12 个非自引用制品哈希全部为 `OK`。
- 服务器暂存目录与原子发布后的正式目录均可加载 35,351 条样本和 3 份划分清单。
- 服务器正式协议 SHA-256 为 `c779ef9ae5513262ddd1ce3a14b571d01ea5e6eff17c98d13f6a634d646030d9`，与本地一致。
- 本地和服务器均已完成原子发布；旧的未通过审查目录不再作为实验输入。

## 6. 残余边界

- 协议状态仍为 `provisional`，阶段仅为 `theory_selection`，且明确禁止最终调参与最终测试结论。
- A/B profile 尚未并入完整 TQH-C2 数据协议，本候选不能替代完整 `dataset-v1`。
- 精确观测序列筛查发现 53 个跨划分极短流哈希，共 260 条样本；标签一致、来源采集独立，且均为一包或两包流。基线报告必须增加剔除这些哈希后的敏感性分析。
- 当前筛查不替代完整 `dataset-v1` 的近重复距离审计。

## 7. 最终裁决

修复后的实现、测试、双份物化结果、服务器回归和原子发布均通过审查。最终严重问题为 `0`，重要问题为 `0`。

**批准 `dataset-candidate-c-v0` 在固定字段、固定划分和固定哈希下用于 `theory_selection` 阶段的 HGB 与 XGBoost 基线。不得据此冻结最终超参数、形成最终测试结论或绕过后续完整 P0 门禁。**
