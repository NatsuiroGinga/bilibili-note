# 生成式训练与评测运行时加速实施计划

> **执行要求：** 使用 `superpowers:subagent-driven-development` 按任务实施；实现代理可针对本任务使用一次 `superpowers:test-driven-development`，但不得在同一任务重复调用。

**目标：** 在不改变冻结样本、标签合同、贪心解码语义和科学超参数的前提下，为 Qwen 训练与评测增加批量生成、长度分桶、增量落盘、断点续评及可审计注意力后端。

**架构：** 评测运行参数与科学配置分离，默认值保持现有单条评测兼容；批量执行按输入长度排序，但最终结果按冻结记录顺序还原。每批预测先持久化到部分结果文件，恢复时以已落盘 `sample_id` 为准跳过已完成样本；完成后再原子发布最终预测和摘要。训练只增加显式注意力后端与可选长度分组，不自动修改微批量、有效批量或学习率。

**技术栈：** Python、PyTorch、Transformers、TRL、PEFT、JSONL、SwanLab、uv。

## 全局约束

- 当前正在运行的 `evaluation-tqhc2-fixed-v1` 不得停止、覆盖或同步新代码。
- 不修改 GeNIS、TQH-C2、ns-3 的冻结数据、顺序、标签或哈希。
- 默认配置必须保持现有行为；加速参数只在新运行配置中显式启用。
- 贪心解码保持 `do_sample=False`；批量结果必须与单条结果逐样本比较。
- 本机不运行 `pytest`；目标测试只在服务器 `uv run --no-sync` 环境执行。
- 服务器同步只使用 `rsync` 白名单，且必须等待当前评测结束。

---

### 任务 1：评测运行参数与确定性批次规划

**文件：**
- 修改：`thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py`
- 修改：`thesis/experiments/llm_probe/tests/test_evaluate_model.py`

**接口：**
- `EvaluationSettings`：`batch_size`、`length_bucket`、`flush_every_batches`、`resume`、`attention_backend`。
- `build_evaluation_settings(mapping)`：严格校验正整数和 `auto|sdpa|flash_attention_2`。
- `plan_length_bucketed_batches(lengths, batch_size, enabled)`：返回覆盖全部原始索引且无重复的批次。

**验收：** 默认批量为 `1`；长度分桶不丢样、不重复；非法配置在模型加载前失败。

### 任务 2：增量预测日志与断点续评

**文件：**
- 修改：`thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py`
- 修改：`thesis/experiments/llm_probe/tests/test_evaluate_model.py`

**接口：**
- `build_evaluation_binding(...)`：绑定测试文件 SHA-256、记录数、模型、适配器、标签合同和运行参数。
- `EvaluationJournal`：校验既有绑定，读取唯一已完成 `sample_id`，逐批追加并刷新部分预测，原子更新进度；完成后按原始索引发布 `predictions.jsonl`。

**验收：** 崩溃恢复只处理未完成样本；绑定不一致、重复或损坏行在模型加载前拒绝；每批完成后已有预测可见。

### 任务 3：批量生成、指标与 SwanLab 进度

**文件：**
- 修改：`thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py`
- 修改：`thesis/experiments/llm_probe/tests/test_evaluate_model.py`

**行为：** 分词器左侧填充并批量调用 `model.generate`；输入令牌按注意力掩码统计；输出排除填充；每批记录完成数、吞吐、延迟和峰值显存；最终结果按冻结顺序发布。

**验收：** 假模型证明批量与单条输出、标签解析及最终顺序一致；中断恢复摘要与一次完成一致；保留结构化输出有效率。

### 任务 4：训练运行时配置

**文件：**
- 修改：`thesis/experiments/llm_probe/src/flow_probe/train_sft.py`
- 修改：`thesis/experiments/llm_probe/tests/test_train_sft.py`

**行为：** `TrainingSettings` 增加默认 `auto` 的 `attention_backend` 与默认 `False` 的 `group_by_length`；注意力后端传给模型加载，长度分组传给 `SFTConfig`；两者进入训练绑定与 SwanLab 配置。

**验收：** 现有配置行为不变；非法配置拒绝；新字段改变时绑定哈希改变；不得自动修改有效批量。

### 任务 5：最小验证与服务器候选基准

- 本地集中运行一次 Black、一次 Ruff、`py_compile` 和 `git diff --check`。
- 独立代码审查只审本任务差异。
- 当前评测结束后白名单同步并在服务器只运行 `test_evaluate_model.py` 与 `test_train_sft.py`。
- 在非最终测试样本上比较批大小 `1/8/16/32/64` 的预测、吞吐、显存和延迟；不使用最终测试选择批大小。
- 只有预测一致且无内存溢出的批大小才能进入新运行配置。

## 状态

- [x] 计划冻结
- [x] 任务 1：运行参数与批次规划
- [x] 任务 2：增量日志与恢复
- [x] 任务 3：批量生成与进度
- [x] 任务 4：训练运行时配置
- [ ] 任务 5：验证、审查与候选基准
