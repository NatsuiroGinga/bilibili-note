# 任务十四 G4R 私有锚点修正版简报

## 目标

新增独立变体 `G4R`，验证原始 G4 的状态误差是否由“共享状态目标被拒绝时，私有状态头锚点梯度也被错误停止”造成。不得覆盖原始 G4 结果，不得改变 G2、G3、G4、G5 已有行为。

## 当前证据

- G4 在 202 步中拒绝共享状态目标 157 次。
- G4 已观测状态误差为 `0.509243`，未观测状态误差为 `0.516625`。
- 生成损失 `0.018361`、物理残差 `0.000989`，说明共享生成保护和物理机制已有正证据。
- 状态头参数只服务状态与物理目标，不直接影响生成输出，因此私有锚点梯度不需要随共享 LoRA 状态方向一起被否决。

## 文件范围

- 修改 `thesis/experiments/llm_probe/src/flow_probe/game_train.py`
- 修改 `thesis/experiments/llm_probe/tests/test_game_train.py`
- 仅在接口确实需要时修改 `game_coordination.py` 与对应测试
- 报告 `.Codex/docs/sdd/task-14-g4r-report.md`

## 强制行为

1. 增加 CLI 和训练契约变体 `G4R`。
2. G4R 的共享 LoRA 协调方向、物理可靠性、0.95 生成底线、生成否决和辅助活跃集合必须与同批次 G4 完全一致。
3. G4R 状态头每一步只要状态梯度非零，就始终累加 `lambda_state * state_gradient`，不受 `solution.accepts_state` 控制。
4. G4R 状态头物理梯度仍仅在 `solution.accepts_physics` 时参与，并继续乘 `lambda_physics * physics_reliability`。
5. 原始 G4 的私有状态头行为保持不变，用作消融对照。
6. 增加逐步指标 `coordination/private_state_anchor_forced`，G4R 为 1，其余变体为 0。
7. 不改变有效模型更新预算、数据顺序、状态掩码、评价和制品协议。
8. 当前源码已经包含尚未同步服务器的 G5 实现；不得删除、覆盖或重写 G5 代码。

## 验证

- 禁止测试驱动开发；实现后补最小测试。
- 本机不运行 pytest，只执行必要 Black、一次 Ruff、语法与差异检查。
- 测试必须覆盖：G4 拒绝状态时私有状态梯度为空；G4R 在相同解下仍写入状态梯度；G4 与 G4R 的共享协调解逐字段一致；新增指标正确。
- 不连接服务器、不启动训练、不提交 Git。

## 输出

报告写入 `.Codex/docs/sdd/task-14-g4r-report.md`，给出修改文件、验证结果、服务器最小测试节点和 G4R 两步/202 步命令。

