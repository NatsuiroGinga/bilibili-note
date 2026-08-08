# TQH-C2 C 候选筛选协议物化计划

## 目标

从已验收的 C/HTTP+AES 暂定主记录与包观测生成 `dataset-candidate-c-v0`，供 HGB/XGBoost 等基线执行 `theory_selection`。该制品不是三源完整 `dataset-v1`，不得冻结最终超参数或支撑最终测试结论。

## 固定路径与标识

- 输入：`runs/data-frozen/dataset-v1-provisional/tqh-c2-C-20260724-v8/`
- 输出：`runs/data-frozen/dataset-candidate-c-v0/protocol/`
- 协议：`data-protocol-v1.0-rc1`
- 状态：`provisional`
- 阶段：`theory_selection`
- 套件：`tqhc2_c_development`
- 标签：`binary_label`
- 划分：`splits/tqhc2-c-development-{train,validation,test}.jsonl`

## 不可变边界

- 整个 C cell 是不可拆分 `allocation_group`；同一 cell 的样本只能属于一个 split。
- 只纳入 `label_status=mapped` 的 `malicious_c2`、`benign` 和 `benign_external`；`auxiliary` 与 `unresolved` 记录保留排除计数，不进入基线清单。
- 模型字段只由包方向、网络层长度、载荷长度、相邻间隔、传输族、TCP 标志、突发和掩码确定性聚合。
- `sample_id`、标签、地址、端口、路径、cell、profile、interval、jitter、capture 和来源哈希不得进入 `tree_flat_view`。
- 当前 train/validation/test 均属于开发域；其中 test 只作 `theory_selection` 的开发评价，不是最终测试。
- `final_tuning` 必须等待 A/B 完成及完整 `dataset-v1` 生成，在新的完整训练/验证清单上重新调参。
- 最终测试 cell、GeNIS `U_test` 和 TQH-C2 留一 profile 测试域不得参与 `theory_selection` 或 `final_tuning`。
- 输出目录已存在时拒绝覆盖；失败目录保留 `_INCOMPLETE` 标记。

## 产物

- `protocol.yaml`
- `samples.parquet`
- `groups.parquet`
- `field-roles.yaml`
- `source-artifacts.jsonl`
- 三个 split JSONL
- `audit/label-coverage.json`
- `audit/group-split-audit.json`
- `audit/field-budget.json`
- `audit/p0-subset.json`
- `audit/artifact-sha256.txt`

## 验收

- 主键全局唯一，全部清单行属于 `samples.parquet`，三 split 样本与 cell 均互斥且并集等于全部 mapped 样本。
- 12 个 cell 全部进入 `groups.parquet`；排除的 auxiliary/unresolved 数量与 C 原始审计一致。
- 所有树模型字段为有限数值，字段角色与 `samples.parquet` 列集合完全相等，敏感字段命中为零。
- 相同输入在两个新目录重跑，全部非自引用制品逐字节一致。
- 服务器使用显式 `expected_protocol_version=data-protocol-v1.0-rc1` 加载，并运行候选物化器与冻结加载器精确测试。
- 独立代码审查无严重或重要问题后，才能启动首批基线。

## 当前状态

- [x] C 暂定主记录、包观测、标签连接和哈希已验收。
- [x] 两阶段协议及候选路径已确认。
- [x] 实现物化器与固定夹具测试。
- [x] 生成候选制品并执行 P0 子集审计。
- [x] 服务器精确测试与加载冒烟。
- [x] 独立代码审查。

## 完成证据

- 本地与服务器正式路径：`runs/data-frozen/dataset-candidate-c-v0/protocol/`。
- 协议 SHA-256：`c779ef9ae5513262ddd1ce3a14b571d01ea5e6eff17c98d13f6a634d646030d9`。
- 样本与划分：`35,351`；训练/验证/开发测试为 `29,175/2,749/3,427`。
- 服务器精确测试：`7 passed in 0.96s`；暂存和正式目录均成功加载 3 份清单。
- 独立审查：初查 2 个重要问题已修复，最终复核严重 0、重要 0。
- 旧失效版本保留为 `protocol.invalid-review-20260724-1/`，不得用于实验。
