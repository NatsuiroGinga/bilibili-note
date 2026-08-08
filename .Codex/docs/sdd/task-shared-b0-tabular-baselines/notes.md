# 共享 B0 树模型基线实施笔记

## 已核验事实

- 候选公共特征：`candidate/common_features.parquet`。
- 候选标签来源：`candidate/bert_train.parquet`。
- GeNIS 验证特征与标签的实际文件名为 `validation/genis_common_features.parquet` 和 `validation/genis_bert.parquet`。
- TQH-C2 验证特征与标签的实际文件名为 `validation/tqhc2_common_features.parquet` 和 `validation/tqhc2_bert.parquet`。
- 公共特征列为 `sample_id`、`stable_order`、8 个公共数值字段及其 8 个缺失掩码。
- 标签文件的 `input_text` 不允许进入树模型特征。
- 现有 `tabular_baselines.py` 已实现 HGB、XGBoost、平衡样本权重、统一评价、预测文件、成本记录和 SwanLab，可复用其执行层。

## 已实现

- `shared_b0_tabular_baselines.py` 验证发布状态固定为 `theory_selection/review_pending`。
- 入口验证 `freeze_manifest.json` 对 `checksums.json` 的绑定，并逐个复核训练与两套验证所用六个 Parquet 的登记大小和 SHA-256。
- 公共 Parquet 的列和顺序必须严格等于 `sample_id`、`stable_order`、8 个公共数值字段及 8 个缺失掩码。
- 标签 Parquet 只投影读取 `sample_id`、`stable_order` 和 `label`；`text`、`input_text` 和 `label` 均不会进入特征矩阵。
- 每对公共/标签视图分别验证主键唯一、`stable_order` 从 0 连续，并逐行核对主键顺序；训练、GeNIS、TQH-C2 三者还验证样本集合互斥。
- 模型构建、平衡权重、HGB/XGBoost 拟合、评价、预测和成本统计直接复用 `tabular_baselines`；正式跟踪复用现有 `tracking` 生命周期。
- 正式包装器固定输出到 `runs/baselines/shared-b0-tabular-seed42-theory-selection-review-pending-v1`，任一运行或启动制品已存在时拒绝覆盖。

## 待服务器验证

- 在服务器项目环境运行 `uv run pytest tests/test_shared_b0_tabular_baselines.py -q`。
- 测试通过后，以 `bash scripts/run_shared_b0_tabular_baselines.sh` 启动一次正式 CPU 基线。
- 正式运行在独立审查完成前保持 `review_pending`，不得写成论文结论。

## 风险

- 仅按行位置拼接会在任一文件重排后静默错配标签，必须逐行核对 `sample_id` 和 `stable_order`。
- 共享视图仍为候选阶段，结果不能写成最终论文结论。
- 工作树包含其他任务的未提交改动，本任务不得覆盖 `pyproject.toml`、生成式评测或共享视图物化代码。
- 新入口为满足白名单而调用 `tabular_baselines` 的内部准备后执行函数；若该模块后续重命名内部符号，需要同步更新本入口并重跑直接测试。
