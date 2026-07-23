# 任务 2 简报：E1/E2 训练闭环

## 前置条件

任务 1 已通过独立复核。先读取任务 1 的核心模块、测试、报告以及本任务的完整实施计划；不得重写任务 1 已通过的接口。

## 允许修改

- 新建 `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_train.py`。
- 新建 `thesis/experiments/llm_probe/configs/bounded_physics_conditioning_seed42.yaml`。
- 新建 `thesis/experiments/llm_probe/scripts/run_bounded_physics_conditioning.sh`。
- 新建 `thesis/experiments/llm_probe/tests/test_bounded_physics_train.py`。
- 修改 `thesis/experiments/llm_probe/pyproject.toml`，只增加训练入口。
- 写入 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-2-report.md`。

## 固定契约

- `ConditioningVariantContract` 只接受 `structure_only` 与 `combined`；Shell 只接受 `e1` 与 `e2`。
- 两组加载相同冻结 Qwen、S3 和同形状新结构，使用同一数据顺序和学习率。
- E1：只计算生成反向传播，状态和物理损失记录为 `0.0`，五维输出只称条件潜变量。
- E2：`L_gen + 1.0 L_state + 0.01 L_physics`，五维输出称预测队列状态。
- 两组都使用 202 步预热余弦：第 1 步 `2e-5`、第 20 步 `2e-4`、第 202 步 `2e-5`；两步冒烟取正式轨迹前两步。
- 参数白名单仅包括状态头、共享条件编码器、四层交叉注意力和四个门。
- 物理损失只更新状态头，不直接更新条件编码器、交叉注意力、Qwen、S3 或 LoRA。

## 必须复用

`PhysicsTrainingSettings`、`_generation_batch`、`_state_batch`、`build_state_supervision_masks`、`masked_state_target_loss`、`queue_balance_residual`、物理样本调度、输入清单、环境清单、控制台捕获、SwanLab 和制品清单。

## 输出与诊断

- 每步记录生成/状态/物理损失、学习率、四层门值、最大残差比例、注意力熵、参数组梯度和三条结构路径调用计数。
- 第一步记录生成到门非零、生成到状态和注入器为零；第二步记录生成到状态、条件编码器和交叉注意力非零。
- E2 记录物理到状态非零、物理到注入器和基座为零。
- 保存 `structure_config.json`、`structure_state.pt`、`base_binding.json`、`gradient_path.json`、`runtime_path_audit.json`、`bypass_equivalence.json`、样本顺序、逐步指标、训练摘要、环境、输入哈希、控制台、SwanLab 和制品清单。
- 输出目录必须由调用者显式给出且预先不存在。

## 测试与验证

- 实现后补直接测试：模式拒绝、损失开关、四个学习率关键点、参数白名单、物理梯度隔离、首步/次步路径、制品键和严格加载。
- 禁止测试驱动开发；不运行本地 pytest。
- 只运行 Black、Ruff、`bash -n` 和 `git diff --check`。
- 不执行 git commit，不改无关文件。
