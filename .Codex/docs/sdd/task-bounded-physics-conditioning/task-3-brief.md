# 任务 3 简报：正式评估与统计入口

## 前置条件

任务 1、任务 2 已通过独立复核。读取其模块、测试和报告，保持训练保存加载契约不变。

## 允许修改

- 新建 `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_evaluation.py`。
- 新建 `thesis/experiments/llm_probe/configs/bounded_physics_conditioning_seed42_eval300.yaml`。
- 新建 `thesis/experiments/llm_probe/scripts/run_bounded_physics_conditioning_eval.sh`。
- 新建 `thesis/experiments/llm_probe/scripts/run_bounded_physics_conditioning_analysis.sh`。
- 新建 `thesis/experiments/llm_probe/tests/test_bounded_physics_evaluation.py`。
- 修改 `thesis/experiments/llm_probe/pyproject.toml`，只增加评估入口。
- 写入 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-3-report.md`。

## 固定评估协议

- 六分区固定为 `family_test`、`subtype_validation`、`subtype_test`、`ood_dos_icmp`、`ood_dos_pushack`、`ood_dos_udp`。
- 每标签 300 条；阈值只用 `subtype_validation` 校准；未知攻击标签不进入训练或校准。
- 自由生成和候选完成评分都必须通过同一个 `PhysicsConditionedRuntime`；禁止直接绕回裸 `model.generate` 或裸 `model(...).logits`。
- 候选评分显式传入 `completion_start`；相同提示的候选条件差超过 `1e-6` 判运行无效。
- 同时保存结构启用预测与旁路预测；旁路与 S3 的 12 个既有预测文件逐样本一致。
- 公开推理拒绝队列真值、状态目标、ns-3 场景号、攻击真值和未知攻击标记。
- 记录自由生成与候选评分的吞吐、词元数、峰值显存、延迟第 50/95 百分位。

## 统计协议

- 分析脚本调用既有 `s3_s4_detection_analysis.analyze`，不修改九项门槛。
- 固定 2,000 次、种子 42、按真实标签分层的配对自助法。
- 输出中的历史 `s4` 键只解释为当前 E1/E2 候选。
- 统计前要求 S3 与候选的 `selected_samples_manifest.json` 完全一致。

## 测试与验证

- 实现后测试训练前向、缓存生成、候选评分均调用结构；旁路恢复、候选无泄漏、六分区、预测文件和效率字段齐全。
- 禁止测试驱动开发；不运行本地 pytest。
- 只运行 Black、Ruff、`bash -n` 和 `git diff --check`。
- 不执行 git commit，不改无关文件。
