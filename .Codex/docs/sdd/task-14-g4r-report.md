# 任务十四 G4R 私有锚点修正版实现报告

## 状态

**带关注项完成。** G4R 独立变体、私有状态锚点修正和逐步指标已实现；按仓库规则，本机未运行 pytest，服务器目标测试与在线冒烟仍是行为门禁。

## 修改文件

- 修改 `thesis/experiments/llm_probe/src/flow_probe/game_train.py`
- 修改 `thesis/experiments/llm_probe/tests/test_game_train.py`
- 新建 `.Codex/docs/sdd/task-14-g4r-report.md`

未修改 `game_coordination.py`、`test_game_coordination.py`、物理残差、数据顺序、状态掩码、评价、制品布局或 G5 协调器实现。

## 实现内容

### 独立变体

- `GAME_VARIANTS` 新增 `G4R`，命令行 `--variant G4R` 可直接解析。
- `GameTrainingSettings.variant` 保留独立值 `G4R`，且 `uses_g5_response=False`。
- G4R 沿用 2 步冒烟或 202 步正式预算、0.02 单纯形网格和 0.95 生成边际底线。

### 共享 LoRA 契约

- G4R 在 `_select_solution` 中与 G4 一样落入现有 `solve_reliability_protected_available` 路由。
- 物理可靠性、生成保护、生成否决、辅助活跃集合、协调权重、边际和生成梯度范数尺度恢复均未增加 G4R 特殊分支。
- 相同输入梯度与有效样本比例下，G4 和 G4R 的 `GameGradientDiagnostics` 及最终 LoRA 梯度逐字段相同。

### 私有状态头契约

- 原始 G4 保持不变：共享协调解拒绝状态时，不写入私有状态梯度。
- G4R 先按整个状态头状态梯度序列判断非零；只要序列范数大于零，就写入 `lambda_state * state_gradient`，不受 `solution.accepts_state` 控制。
- G4R 私有物理梯度仍只在 `solution.accepts_physics` 为真时写入。
- G4R 私有物理梯度尺度保持为 `lambda_physics * physics_reliability`。
- G2、G3、G4、G5 和 `G5-STOP-RESPONSE` 的原有私有梯度分支未改变；G5 训练仍在两处显式以 `variant="G4"` 构造基线共享与私有梯度。

### 指标

- `GAME_STEP_METRIC_KEYS` 新增 `coordination/private_state_anchor_forced`。
- G4R 每步记录 `1.0`。
- G2、G3、G4、G5 和 `G5-STOP-RESPONSE` 每步记录 `0.0`。
- 指标继续通过原有 `record_game_step_metrics` 同步写入本地 JSONL 和 SwanLab。

## 实现后测试

在生产实现完成后新增以下最小测试，未在本机执行：

- `test_g4_rejected_state_keeps_private_state_gradient_empty`
- `test_g4r_forces_private_state_anchor_when_shared_state_is_rejected`
- `test_g4r_private_physics_remains_accepted_and_reliability_scaled`
- `test_g4r_private_physics_remains_rejected_when_solution_rejects_it`
- `test_g4r_and_g4_share_exact_lora_coordination_solution`
- `test_private_state_anchor_metric_only_marks_g4r`
- `test_settings_accept_independent_g4r_variant`

## 本地验证

### Black

```bash
uv run --offline --group dev black src/flow_probe/game_train.py tests/test_game_train.py
```

结果：通过；`game_train.py` 被格式化，`test_game_train.py` 无需修改。

### Python 语法

```bash
env PYTHONPYCACHEPREFIX=/tmp/flow-probe-task14-g4r-pycache .venv/bin/python -m py_compile src/flow_probe/game_train.py tests/test_game_train.py
```

结果：项目 Python 语法检查通过。

### 未执行项

- 未运行 Ruff；本轮没有额外 Ruff 结果。
- **未在本机运行 pytest。** 所有 pytest 等待服务器项目环境执行。
- 未连接服务器、未启动在线冒烟或正式训练、未执行 Git 提交。

## 服务器最小测试

```bash
source ~/.bashrc
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q \
  tests/test_game_train.py::test_g4_rejected_state_keeps_private_state_gradient_empty \
  tests/test_game_train.py::test_g4r_forces_private_state_anchor_when_shared_state_is_rejected \
  tests/test_game_train.py::test_g4r_private_physics_remains_accepted_and_reliability_scaled \
  tests/test_game_train.py::test_g4r_private_physics_remains_rejected_when_solution_rejects_it \
  tests/test_game_train.py::test_g4r_and_g4_share_exact_lora_coordination_solution \
  tests/test_game_train.py::test_private_state_anchor_metric_only_marks_g4r \
  tests/test_game_train.py::test_settings_accept_independent_g4r_variant \
  tests/test_game_train.py::test_g5_stop_response_follower_gradients_equal_g4 \
  tests/test_game_train.py::test_g5_step_metrics_require_complete_reaction_fields
```

## G4R 两步冒烟

同步白名单文件、核对 SHA-256 并执行 `uv pip install --no-deps -e .` 后运行：

```bash
uv run --no-sync flow-probe-train-game \
  --config configs/physics_sparse_seed42.yaml \
  --variant G4R \
  --output-dir runs/game-coordination/g4r-smoke-seed42-20260722 \
  --run-name qwen3-1.7b-g4r-smoke-seed42-20260722 \
  --max-steps 2 \
  --validation-limit 8 \
  --model-path /root/autodl-tmp/thesis/models/Qwen3-1.7B
```

验收重点：两次模型更新、两行逐步 JSONL、`coordination/private_state_anchor_forced` 每步为 1、共享权重与相同输入下 G4 一致、SwanLab 点可见、制品清单状态为 `finished`。

## G4R 202 步正式运行

```bash
uv run --no-sync flow-probe-train-game \
  --config configs/physics_sparse_seed42.yaml \
  --variant G4R \
  --output-dir runs/game-coordination/g4r-seed42-202steps-20260722 \
  --run-name qwen3-1.7b-g4r-seed42-202steps-20260722 \
  --max-steps 202 \
  --model-path /root/autodl-tmp/thesis/models/Qwen3-1.7B
```

正式运行前必须先通过服务器最小测试和两步在线冒烟。正式结束后需核对 202 行逐步指标、202 次有效模型更新、SwanLab 云端指标、最终适配器、状态头与制品清单。

## 关注项

- 本机未执行行为测试，服务器 pytest 是首个行为门禁。
- G4R 只裁决私有状态锚点是否应与共享状态方向解耦，不改变 G4 的共享协调机制；不得用 G4R 结果覆盖原始 G4 消融证据。
- G4R 正式运行后应重点比较 G4 的已观测状态误差 `0.509243`、未观测状态误差 `0.516625`，同时确认生成损失与物理残差未退化。
