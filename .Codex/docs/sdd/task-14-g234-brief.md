# 任务十四 G2–G4 实现简报

## 目标

实现 G2 对称合作议价、G3 固定非对称合作议价和 G4 物理可靠性与生成否决的纯数学协调器及统一训练入口。

## 必读

- `.Codex/docs/2026-07-22-任务十四G0-G5同预算训练设计.md`
- `thesis/experiments/llm_probe/src/flow_probe/physics_train.py`
- `thesis/experiments/llm_probe/src/flow_probe/gradient_feasibility.py`
- `thesis/experiments/llm_probe/src/flow_probe/gradient_conflict.py`

## 文件范围

- 新建 `thesis/experiments/llm_probe/src/flow_probe/game_coordination.py`
- 新建 `thesis/experiments/llm_probe/src/flow_probe/game_train.py`
- 修改 `thesis/experiments/llm_probe/pyproject.toml`
- 新建 `thesis/experiments/llm_probe/tests/test_game_coordination.py`
- 新建 `thesis/experiments/llm_probe/tests/test_game_train.py`
- 报告 `.Codex/docs/sdd/task-14-g234-report.md`

## 强制接口

- `solve_symmetric_bargaining(gram, resolution) -> CoordinationSolution`
- `solve_asymmetric_bargaining(gram, powers, resolution) -> CoordinationSolution`
- `solve_reliability_protected(gram, reliability, generation_floor, resolution) -> CoordinationSolution`
- `train_game_variant(probe, settings, tracking, raw_config) -> dict[str, object]`
- 命令入口 `flow-probe-train-game`

## 实现约束

- 禁止调用测试驱动开发技能；先实现，再运行最小目标测试。
- 复用任务十三 Gram 校验、单纯形和边际函数，不复制求解逻辑。
- 不修改物理残差、数据划分、状态掩码或模型基座。
- 共享 LoRA 参数使用协调方向并以生成梯度范数恢复尺度。
- 状态头作为任务私有参数，只根据被接受的状态和物理目标更新。
- G2 最大化等权对数边际；G3 议价权固定为 `(0.6,0.2,0.2)`。
- G4 生成边际不低于 0.95，并允许双辅助、单辅助或纯生成退化。
- 逐步指标必须写本地 JSONL 并调用 SwanLab 在线记录。
- 不执行裸 `uv sync`，不连接服务器，不启动正式训练。

## 验证与报告

实现完成后运行新模块与直接复用接口的最小测试。Black 和 Ruff 对修改文件各运行一次；Ruff 无语法或结构问题后不得重复。报告记录文件、命令、结果、遗留风险和建议服务器冒烟命令。返回状态只能是完成、带关注项完成、需要上下文或阻塞。

