# GRANDE LSPR24 零重训练描述性评价复用笔记

## 已核对的现有实现

- `tools/ch3_grande_protocol_a_source_q0.py`
  - `expected_candidates()` 固定 G-A 与 G-B 结构。
  - `build_model(candidate, feature_count)` 是当前冻结 GRANDE 核心构建入口。
  - 选中检查点路径为 `checkpoints/selected-G-A.pt` 和 `checkpoints/selected-G-B.pt`，权重字段为 `model`。
  - 单流前向语义为 `sigmoid(model(X_raw83))`，模型不消费序列历史。
  - 父 BF16 运行的 G-A/G-B 候选表、训练精度和 2,048 流微批均已冻结。

- `tools/ch3_full_mlp_s0_precision_aggregation_diagnostic.py`
  - `complete_tied_budget_curve()` 输出阈值、良性并列组大小、FP、实际 FPR 和 DR 的完整可达曲线。
  - `actual_reachable_readouts()` 在六档名义预算下选择不超过预算的最后一个完整并列组。
  - `common_integer_fp_budget_readouts()` 同时输出公共整数 FP 预算口径。
  - `ordered_exposures()` 按冻结流数组下标在实体内升序构建 1 基 `exposure_index`。
  - `first_alert_aggregate()` 只返回未告警率、曝光分位、实际首次告警 FPR 和按时检出聚合曲线，不落逐实体位置。

- `tools/ch3_full_mlp_complete_entity_lp_protocol_a_q0.py`
  - LSPR24 冻结数组数据规模为 20,227,356 条流、83 字段、47,115 个无向 IP 对实体、752 个正实体。
  - `s24/d24` 只用于构造无向实体键，原始 IP 不入模。
  - 目标年单次加载和每格单次打分已有可复用的身份收据模式。

## 实现决策

1. 不修改父 GRANDE 源年工具，避免把目标年语义回填到原源门。
2. 新工具只校验父运行身份、两个选择收据和检查点摘要；父 `source_gate` 否决只作历史事实，不是本任务的目标评价门。
3. GRANDE C00 的系统实体读数就是最大池化，因此 `entity_average_precision` 与 `maximum_entity_average_precision` 分字段并列报告，数值相同且显式登记同一语义，不伪造第二个聚合头。
4. 终端实体分数为全曝光最大值；首次告警路径为实体内前缀最大值，与 C00 决策语义一致。
5. 逐流分数在单结构指标完成后立即释放；运行根只保存聚合 JSON 和 NPZ。
6. 第三方 API 新鲜度门未触发：新工具只复用仓库内已有同构调用，不新增或猜测外部库签名。

## 已知边界

- 本轮只交付实现和静态收据，未读取真实父检查点、未执行 LSPR24 评价，所以不生成任何效果数字或科学结论。
- LSPR24 已被历史访问，输出只能标为描述性评价。
- 父运行的资源字段可作训练历史背景，本任务的工程资源主口径是目标前向和聚合的墙钟、吞吐、峰值 GPU 显存与峰值主存。
