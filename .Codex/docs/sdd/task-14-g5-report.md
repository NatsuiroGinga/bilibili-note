# 任务十四 G5 工程实现报告

- **状态**：带关注项完成
- **日期**：2026-07-22
- **实现范围**：G5 独立协调器、一次可微 AdamW 跟随响应、停止反应梯度消融
- **未执行事项**：本机 pytest、服务器连接、训练、下载和 Git 提交

## 1. 结论

G5 已接入现有 G2-G4 统一训练入口。实现包含独立的 `A[2,7]`、`b[2]` 协调器，以 G4 安全权重为零点，在 G4 接受集合的子集上执行可微安全投影，并通过一次函数式 AdamW 模型响应从独立验证批次取得反应梯度。

`G5-STOP-RESPONSE` 已作为显式消融变体接入。该变体保持协调器逐位为零，直接使用 G4 权重和 G4 状态头基线梯度，并通过同一函数式 AdamW 路径提交模型更新。

当前关注项是本机系统 Python 和项目虚拟环境均未安装 `torch`。因此简报要求的固定小张量运行验证与 pytest 未在本机执行，必须在 GPU 服务器现有项目环境中完成后，才能启动两步冒烟。

## 2. 修改文件

### 生产源码

- `thesis/experiments/llm_probe/src/flow_probe/game_coordination.py`
- `thesis/experiments/llm_probe/src/flow_probe/game_train.py`

### 测试

- `thesis/experiments/llm_probe/tests/test_game_coordination.py`
- `thesis/experiments/llm_probe/tests/test_game_train.py`

### 报告

- `.Codex/docs/sdd/task-14-g5-report.md`

未新建额外源码文件，未修改配置、已有运行目录、模型权重或实验结果。

## 3. 数学接口

### 3.1 独立协调器

- `G5Coordinator.A` 固定为 `float32[2,7]`。
- `G5Coordinator.b` 固定为 `float32[2]`。
- 两个参数块全零初始化，与模型 LoRA 和状态头参数完全分离。
- 输入诊断固定为 `float32[7]`，顺序为 `C_gs`、`C_gp`、`C_sp`、物理有效比例、物理可靠性、G4 状态权重、G4 物理权重。
- 输入诊断必须停止梯度且全部有限。

### 3.2 安全投影

- `coordinate_g5_response` 先按门禁公式构造连续候选 `q`。
- 只枚举 G4 已接受辅助集合的全部子集，空集合始终提供纯生成可行候选。
- 每个固定子集使用长度为 3 的确定性活跃集解析投影。
- 候选按投影距离、生成权重、可靠性加权物理权重、状态权重依次确定性选择。
- 最终强制检查非负、和为 1、生成边际不低于 0.95、选中辅助边际非负。
- 协调器为零时通过直通锚定使前向权重逐位等于 G4，同时保留选中投影分支的非零雅可比。

### 3.3 状态头零点解释

现有 G4 的状态头私有梯度按接受集合、`lambda_state` 和可靠性缩放的 `lambda_physics` 构造，不等于门禁报告中协调权重绝对值乘归一化梯度的形式。简报同时禁止改变 G4，并要求停止响应逐张量等于 G4。

实现采用以下连续锚定满足这两个约束：

\[
h_i(w_i)=w_i\kappa_i g_i+s(t_i)\left(h_i^{G4}-\bar w_i\kappa_i g_i\right),
\]

其中 `t_i=clamp(w_i/\bar w_i,0,1)`，`s(t)=3t^2-2t^3`。因此：

- `w_i=\bar w_i` 时前向值严格为现有 G4 私有梯度。
- `w_i=0` 时被拒绝目标的私有梯度为零。
- 在 G4 零点处修正项导数为零，局部反应导数仍为门禁要求的 `kappa_i * g_i`。
- 停止响应路径直接复用 G4 基线梯度，不引入浮点重组。

### 3.4 函数式 AdamW

- `differentiable_clip_grad_norm` 对 LoRA 与状态头全部梯度执行一次联合全局二范数裁剪，并保留裁剪系数对协调权重的梯度。
- `functional_adamw_step` 从正式模型优化器参数组读取学习率、`betas`、`eps`、权重衰减和每个参数的当前动量状态。
- 函数式响应不修改模型参数、`.grad` 或优化器状态。
- `commit_functional_adamw_step` 在主导梯度计算后提交同一组虚拟参数和动量状态，不调用额外的模型 `optimizer.step()`。
- 明确拒绝 AMSGrad 和 `maximize` 模式，防止公式与真实优化器语义漂移。

### 3.5 独立验证响应

- G5 为生成验证集和物理验证集分别预生成独立固定样本顺序，并写入 `sample_order.json`。
- 生成训练与验证、物理训练与验证会按 `sample_id` 检查交集。
- 主导代价由更新后的生成验证损失、未观测状态误差和物理残差构成，并用更新前值停止梯度归一化。
- 验证状态掩码强制为第 0 列不参与、第 1 至第 4 列参与未观测误差。
- 使用 `torch.func.functional_call` 在虚拟 LoRA 和状态头参数上计算主导代价，验证标签不会写入模型 `.grad`。
- 完整反应梯度只写入协调器；协调器先更新，已评价的模型响应随后原子提交，新协调器参数从下一步生效。

## 4. 预算、指标与制品

### 4.1 更新计数

G5 新增并逐步记录：

- `model_optimizer_updates`
- `state_head_updates`
- `coordinator_optimizer_updates`
- `virtual_response_evaluations`
- `validation_forwards`
- `extra_model_optimizer_steps`

训练结束前强制检查模型更新数等于 2 或 202 的固定预算，额外模型优化器步数固定为 0。

### 4.2 逐步指标

保留全部既有 G2-G4 指标键，并为 G5 增加：

- G4 基线权重、协调响应、选中辅助子集和投影距离。
- 投影雅可比范数、主导代价和三项相对验证损失。
- 直接梯度范数、完整反应梯度范数、状态与物理反应代理。
- 反应梯度有限标志、反应门禁失败标志和停止响应标志。
- 六类独立更新与评价计数。

### 4.3 汇总与制品

- G2-G4 继续使用 `flow_probe_game_coordination_v1`，原有行为和字段保持不变。
- G5 使用 `flow_probe_game_coordination_g5_v1`。
- G5 配置快照记录协调器形状、学习率 `2e-4`、权重衰减 0、默认 `betas=[0.9,0.999]`、`eps=1e-8`、一次展开和验证样本种子偏移。
- G5 汇总记录反应非零步数、门禁失败步数、平均反应梯度、平均投影雅可比和三项平均相对验证损失。
- 新增 `coordinator.pt`，保存协调器参数和协调器优化器状态，并加入制品清单与完成门禁。
- G5 样本顺序使用 `flow_probe_game_sample_order_g5_v1`，同时记录训练与独立验证批次；G2-G4 仍使用原有样本顺序结构。

## 5. 新增测试

### 协调器测试

- 固定 `A[2,7]`、`b[2]` 形状、精度和零初始化。
- 零响应逐位返回 G4 权重且投影雅可比非零。
- 停止响应逐位返回 G4 权重且雅可比为零。

### 训练工具测试

- G5 停止响应配置与两步预算解析。
- 函数式 AdamW 与真实单步 AdamW 的参数和动量逐张量一致。
- G5 停止响应跟随梯度与 G4 LoRA、状态头梯度逐张量一致。
- 联合全局裁剪保留对协调权重的导数。
- 两步函数式提交与真实 AdamW 基线的参数和动量逐张量一致。
- G5 逐步指标必须包含完整反应字段。

## 6. 本地验证

### 已执行

1. Black：

```bash
thesis/experiments/llm_probe/.venv/bin/black \
  thesis/experiments/llm_probe/src/flow_probe/game_coordination.py \
  thesis/experiments/llm_probe/src/flow_probe/game_train.py \
  thesis/experiments/llm_probe/tests/test_game_coordination.py \
  thesis/experiments/llm_probe/tests/test_game_train.py
```

结果：3 个文件重格式化，1 个文件无需修改。系统全局 `black` 不存在，实际成功命令使用项目虚拟环境。

2. Ruff：

```bash
thesis/experiments/llm_probe/.venv/bin/ruff check \
  thesis/experiments/llm_probe/src/flow_probe/game_coordination.py \
  thesis/experiments/llm_probe/src/flow_probe/game_train.py \
  thesis/experiments/llm_probe/tests/test_game_coordination.py \
  thesis/experiments/llm_probe/tests/test_game_train.py
```

结果：报告 2 个未使用导入和 3 个导入排序项，没有语法或执行结构错误。两个未使用导入已做最小删除；按仓库规则未重复运行 Ruff，导入排序提示不触发额外格式改动。

3. 最终语法检查：

```bash
PYTHONPYCACHEPREFIX=/tmp/task14-g5-pycache-final2 python -m py_compile \
  thesis/experiments/llm_probe/src/flow_probe/game_coordination.py \
  thesis/experiments/llm_probe/src/flow_probe/game_train.py \
  thesis/experiments/llm_probe/tests/test_game_coordination.py \
  thesis/experiments/llm_probe/tests/test_game_train.py
```

结果：通过。

函数式 AdamW 的零方差有限导数修复后，另以 `/tmp/task14-g5-pycache-final3` 对 `game_train.py` 执行同类最小语法复核，结果通过。

4. 差异与空白检查：

```bash
git diff --check
rg '[[:blank:]]+$' \
  thesis/experiments/llm_probe/src/flow_probe/game_coordination.py \
  thesis/experiments/llm_probe/src/flow_probe/game_train.py \
  thesis/experiments/llm_probe/tests/test_game_coordination.py \
  thesis/experiments/llm_probe/tests/test_game_train.py
```

结果：`git diff --check` 通过，四个修改文件无尾随空白。

### 未执行

- 未运行本机 pytest，遵守简报与仓库约束。
- 未运行固定小张量测试，因为系统 Python 与项目 `.venv` 均报 `ModuleNotFoundError: No module named 'torch'`。
- 未连接 GPU 服务器，因此新增测试节点和两步冒烟尚未取得运行结果。

## 7. 服务器最小测试命令

以下命令仅供后续服务器验证，本任务未执行：

```bash
source ~/.bashrc >/dev/null 2>&1
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest \
  tests/test_game_coordination.py::test_g5_coordinator_has_fixed_zero_initialized_parameter_blocks \
  tests/test_game_coordination.py::test_g5_zero_response_returns_g4_weights_with_nonzero_projection_jacobian \
  tests/test_game_coordination.py::test_g5_stop_response_is_exact_g4_value_and_has_zero_jacobian \
  tests/test_game_train.py::test_functional_adamw_matches_real_single_step_tensor_by_tensor \
  tests/test_game_train.py::test_g5_stop_response_follower_gradients_equal_g4 \
  tests/test_game_train.py::test_differentiable_global_clip_preserves_weight_gradient \
  tests/test_game_train.py::test_two_step_functional_commit_matches_real_adamw_stop_baseline \
  tests/test_game_train.py::test_g5_step_metrics_require_complete_reaction_fields
```

通过门槛：全部节点通过；正常响应路径投影雅可比非零；函数式 AdamW 与真实更新逐张量一致；停止响应梯度与 G4 逐张量一致。

## 8. 两步在线冒烟命令

必须先通过第 7 节最小测试，再运行以下命令。本任务未执行。

### G4 对照

```bash
uv run --no-sync flow-probe-train-game \
  --config configs/physics_sparse_seed42.yaml \
  --variant G4 \
  --output-dir runs/game-coordination/qwen3-1.7b-seed42-g4-g5compare-smoke2-v1 \
  --run-name qwen3-1.7b-seed42-g4-g5compare-smoke2-v1 \
  --max-steps 2 \
  --validation-limit 8 \
  --model-path /root/autodl-tmp/thesis/models/Qwen3-1.7B
```

### G5 正常响应

```bash
uv run --no-sync flow-probe-train-game \
  --config configs/physics_sparse_seed42.yaml \
  --variant G5 \
  --output-dir runs/game-coordination/qwen3-1.7b-seed42-g5-smoke2-v1 \
  --run-name qwen3-1.7b-seed42-g5-smoke2-v1 \
  --max-steps 2 \
  --validation-limit 8 \
  --model-path /root/autodl-tmp/thesis/models/Qwen3-1.7B
```

### G5 停止响应

```bash
uv run --no-sync flow-probe-train-game \
  --config configs/physics_sparse_seed42.yaml \
  --variant G5-STOP-RESPONSE \
  --output-dir runs/game-coordination/qwen3-1.7b-seed42-g5-stop-response-smoke2-v1 \
  --run-name qwen3-1.7b-seed42-g5-stop-response-smoke2-v1 \
  --max-steps 2 \
  --validation-limit 8 \
  --model-path /root/autodl-tmp/thesis/models/Qwen3-1.7B
```

冒烟门禁：

- G5 两步完整反应梯度有限且非零，投影雅可比非零，模型更新数为 2，额外模型更新为 0。
- G5 停止响应的协调器更新数为 0，协调器参数逐位为零。
- G5 停止响应与 G4 的两步 LoRA、状态头、模型优化器状态和最终评价逐张量一致。
- 两组 G5 均保存 `coordinator.pt`、独立验证样本顺序、新增逐步指标、训练汇总和 SwanLab 原始日志。

## 9. 遗留风险

- 本机缺少 `torch`，所有张量行为断言尚未实际执行。
- `torch.func.functional_call` 与 Qwen3-1.7B 的 PEFT LoRA 参数覆盖兼容性必须由服务器最小测试或两步冒烟确认。
- 函数式 AdamW 与 CUDA/BF16 下真实 AdamW 的逐张量等价性尚未获得服务器证据。
- 正常 G5 在安全约束切换点使用框架单侧导数；实际运行必须检查投影雅可比和完整反应梯度是否持续非零。
- Ruff 首次检查的导入排序提示未复跑确认，不影响语法检查，但提交前可由审查任务统一处理。
