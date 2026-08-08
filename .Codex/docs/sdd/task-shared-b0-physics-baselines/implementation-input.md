# shared B0 物理基线实施输入

## 1. 实施目标

在不改变普通 shared B0 Qwen B0 行为的前提下，实现两条可公平比较、可恢复、可审计的正式基线：

1. `state-supervision-only Qwen`
2. `standard PINN Qwen`

实现必须复用同一个 shared B0 分类训练清单和普通 Qwen 训练协议。物理字段仅通过独立旁路清单进入辅助损失，禁止进入 Qwen 提示词。

## 2. 实施前固定裁决

以下参数属于科学协议，不允许由实现者自行调整：

```yaml
seed: 42
max_steps: 200
generation_micro_batch_size: 2
generation_gradient_accumulation_steps: 2
effective_generation_batch_size: 4
hardware_fallback:
  generation_micro_batch_size: 1
  generation_gradient_accumulation_steps: 4
save_steps: 20
lambda_state: 1.0
lambda_physics:
  state_supervision: 0.0
  standard_pinn: 0.01
state_mask: anchor0_plus_one
physics_records: 2421
physics_micro_steps: 400
physics_usage: train_fit_diagnostic
```

两条基线必须共用：

- 同一生成清单和哈希。
- 同一生成样本顺序和哈希。
- 同一物理旁路清单和哈希。
- 同一物理样本顺序、批次边界和哈希。
- 同一状态头结构、参数初始化和初始化哈希。
- 同一优化器、调度器、梯度裁剪和检查点间隔。
- 同一公开检测评估清单和解码配置。

## 3. 数据设计

### 3.1 分类训练输入

直接绑定现有冻结文件：

```text
runs/data-frozen/dataset-v1-shared-b0/candidate/qwen_train.jsonl
```

实现不得：

- 修改或重新物化该文件。
- 为物理基线创建带额外提示词字段的副本。
- 过采样或重复插入 ns-3 记录。
- 按物理标签改变分类采样顺序。

### 3.2 新物理旁路输入

新增配置：

```text
configs/shared_b0_physics_sidecar_v1.yaml
```

新增物化器：

```text
src/flow_probe/shared_b0_physics_sidecar.py
```

固定输出：

```text
runs/data-frozen/dataset-v1-shared-b0-physics-v1/
├── candidate/ns3_physics_train.jsonl
├── dataset_manifest.json
├── source_manifest.json
├── join_audit.json
└── materialization_audit.json
```

`ns3_physics_train.jsonl` 每条记录至少需要：

```text
sample_id
group_id
stable_order
source_split
usage
anchor_times
state_targets
state_mask_inputs
capacity_by_anchor
received_bytes_by_anchor
received_packets_by_anchor
dequeued_bytes_by_anchor
dropped_bytes_by_anchor
normalization_scale
source_record_id
source_file_sha256
```

物化器必须执行以下预检：

- 旁路记录数严格等于 2421。
- `sample_id` 全部唯一。
- 旁路 `sample_id` 集合与分类清单中的 ns-3 `sample_id` 集合完全相等。
- 旁路字段均为有限数值，尺度严格为正。
- 五锚点长度一致，时间单调递增。
- `usage` 固定为 `train_fit_diagnostic`。
- 双次物化输出逐字节一致。
- 已冻结分类文件的前后哈希不变。

### 3.3 连接规则

- `train_sft.py` 的共享数据路径必须保留 `sample_id`。
- 训练时先按普通 shared B0 路径构造 Qwen 输入，再用 `sample_id` 查询物理旁路。
- 非 ns-3 生成样本可以没有物理记录；辅助物理批次由独立确定性调度提供。
- 不允许按行号、当前批次位置或提示词文本连接。
- Qwen 张量化前的可见字段白名单必须只包含已发布的 8 个共同观测字段和既有任务文本。

## 4. 训练器设计

### 4.1 公共训练器提取

最小修改：

```text
src/flow_probe/train_sft.py
tests/test_train_sft.py
```

从 `train_sft.py` 提取可供新训练器调用的稳定构建函数：

- 模型与量化配置构建。
- LoRA 配置与挂载。
- 聊天样本构建与截断。
- `SFTTrainer` 参数构建。
- 检查点发现、训练绑定和自动恢复。
- 普通 Qwen 使用的优化器与调度器设置。

约束：

- 原命令行入口、配置含义、默认值和制品路径不变。
- 原普通 Qwen 测试必须继续通过。
- 对固定小样本，重构前后聊天模板输出、令牌序列、标签掩码和训练参数逐项相等。
- 不在公共文件中写死物理基线配置。

### 4.2 新训练入口

新增：

```text
src/flow_probe/shared_b0_physics_train.py
configs/shared_b0_physics_baselines_seed42_200_v1.yaml
tests/test_shared_b0_physics_train.py
```

建议命令行：

```text
flow-probe-train-shared-b0-physics \
  --config <配置> \
  --baseline state_supervision|standard_pinn \
  [--preflight-only] \
  [--resume auto|never|<检查点>]
```

使用语义化的 `--baseline`，不要暴露历史 M1/M2 编号作为正式接口。

### 4.3 状态头

直接导入并复用：

- `physics_train.ContinuousQueueStateHead`
- `physics_train.build_state_supervision_masks`
- `qwen_physics_gradient.select_last_token_hidden`

状态头要求：

- 两条基线结构完全相同。
- 在相同随机数状态下初始化。
- 初始化后立即保存参数树哈希。
- 输入只取普通 Qwen 前向产生的最后有效令牌隐藏状态。
- 输出五锚点连续队列状态。

### 4.4 损失

共同生成损失沿用普通 Qwen。

状态监督基线：

```text
loss = generation_loss + 1.0 * state_loss
```

标准 PINN 基线：

```text
loss = generation_loss + 1.0 * state_loss + 0.01 * physics_residual_loss
```

实现要求：

- 状态损失按有效掩码逐元素归约，分母为有效监督元素数。
- 物理损失导入 `physics_train.queue_balance_residual`，不得复制公式。
- 物理系数仅在标准 PINN 分支读取。
- 状态监督分支即使旁路文件包含物理系数，也必须在字段访问层拒绝读取。
- 所有损失分量、有效元素数、梯度范数和非有限数检查逐步记账。
- 任一非有限损失或梯度立即失败，不得跳过批次。

### 4.5 物理调度

为 400 个生成微步冻结一个物理调度：

- 21 个物理批次大小为 7。
- 379 个物理批次大小为 6。
- 2421 条记录各出现一次。
- 固定种子、稳定排序键、完整顺序和边界写入 `physics_schedule.json`。
- 两条基线运行前核对同一调度文件哈希。

归约采用逐样本等权方案。若使用批均值，必须乘以：

```text
actual_physics_batch_size / (2421 / 400)
```

### 4.6 检查点与恢复

每 20 个优化步保存一次。每个检查点至少包含：

- LoRA 适配器。
- 状态头参数。
- 优化器状态。
- 调度器状态。
- 梯度缩放器状态，如适用。
- 生成样本游标。
- 物理调度游标。
- Python、NumPy、PyTorch 和 CUDA 随机数状态。
- 当前优化步和微步。
- 配置、数据、生成顺序、物理调度和初始化哈希。
- 基线身份和损失权重。

恢复门禁：

- 配置或数据哈希不一致时拒绝恢复。
- 基线身份不一致时拒绝恢复。
- 已完成运行默认拒绝覆盖。
- 连续 4 步与 2 步保存后恢复到 4 步的参数、游标和指标必须在容差内一致。

## 5. 评估设计

### 5.1 公开检测评估

新增配置：

```text
configs/shared_b0_state_supervision_seed42_genis_batch16_v1.yaml
configs/shared_b0_state_supervision_seed42_tqhc2_batch16_v1.yaml
configs/shared_b0_standard_pinn_seed42_genis_batch16_v1.yaml
configs/shared_b0_standard_pinn_seed42_tqhc2_batch16_v1.yaml
```

新增薄封装：

```text
src/flow_probe/shared_b0_physics_evaluation.py
tests/test_shared_b0_physics_evaluation.py
```

薄封装应调用 `evaluate_model.py`，只补充：

- 基线身份。
- 训练绑定哈希。
- 适配器目录树哈希。
- 状态头哈希。
- 分类数据与评估数据哈希。
- 对已完成评估的幂等检查。

评估配置继续使用：

- 批量 `16`。
- 不启用长度分桶。
- `SDPA`。
- 批级记账与恢复。
- 与普通 Qwen 相同的 GeNIS 和 TQH-C2 文件。

### 5.2 物理诊断

当前只允许产生：

```text
evaluation_scope=train_fit_diagnostic
```

至少报告：

- 状态均方误差和平均绝对误差。
- 各锚点误差。
- 掩码覆盖率和有效元素数。
- 队列平衡残差均方误差。
- 非有限数计数。
- 逐组汇总，但不得称为未见组泛化。

禁止使用的表述：

- 未见物理测试。
- 外部物理泛化。
- 对新拓扑有效。
- 对未见配置有效。

最终物理泛化需要新增冻结清单，来源至少应覆盖与当前训练不相交的配置、哑铃拓扑或停车场场景。该清单不是当前工程实现的训练启动前置条件，但属于论文物理泛化结论的前置条件。

## 6. 精确文件范围

### 6.1 新建文件

```text
thesis/experiments/llm_probe/configs/shared_b0_physics_sidecar_v1.yaml
thesis/experiments/llm_probe/configs/shared_b0_physics_baselines_seed42_200_v1.yaml
thesis/experiments/llm_probe/configs/shared_b0_state_supervision_seed42_genis_batch16_v1.yaml
thesis/experiments/llm_probe/configs/shared_b0_state_supervision_seed42_tqhc2_batch16_v1.yaml
thesis/experiments/llm_probe/configs/shared_b0_standard_pinn_seed42_genis_batch16_v1.yaml
thesis/experiments/llm_probe/configs/shared_b0_standard_pinn_seed42_tqhc2_batch16_v1.yaml
thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py
thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_train.py
thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_evaluation.py
thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py
thesis/experiments/llm_probe/tests/test_shared_b0_physics_train.py
thesis/experiments/llm_probe/tests/test_shared_b0_physics_evaluation.py
thesis/experiments/llm_probe/tests/test_run_shared_b0_physics_baselines_wrapper.py
thesis/experiments/llm_probe/scripts/run_shared_b0_physics_baselines.sh
thesis/experiments/llm_probe/scripts/run_shared_b0_physics_evaluation.sh
```

### 6.2 最小修改文件

```text
thesis/experiments/llm_probe/src/flow_probe/train_sft.py
thesis/experiments/llm_probe/tests/test_train_sft.py
thesis/experiments/llm_probe/pyproject.toml
```

`pyproject.toml` 新增三个入口：

```text
flow-probe-build-shared-b0-physics-sidecar
flow-probe-train-shared-b0-physics
flow-probe-evaluate-shared-b0-physics
```

### 6.3 明确不修改

```text
thesis/experiments/llm_probe/src/flow_probe/shared_b0_view.py
thesis/experiments/llm_probe/configs/shared_b0_view_v1.yaml
thesis/experiments/llm_probe/src/flow_probe/physics_train.py
thesis/experiments/llm_probe/src/flow_probe/evaluate_model.py
thesis/experiments/llm_probe/scripts/run_qwen_physics_m012.sh
runs/data-frozen/dataset-v1-shared-b0/**
任何历史 runs/** 制品
```

旧模块只允许导入经过测试的纯组件，不通过本任务重写历史实现。

## 7. 测试清单

### 7.1 `test_shared_b0_physics_sidecar.py`

- 2421 条计数、唯一性和集合相等。
- 分类清单与旁路按 `sample_id` 正确连接。
- 缺失、重复、额外或错配标识立即失败。
- 五锚点长度、时间顺序、有限数和正尺度预检。
- 双次物化逐字节一致。
- 分类冻结文件哈希不变。
- 用途固定为 `train_fit_diagnostic`。

### 7.2 `test_train_sft.py`

- 公共构建函数提取前后普通 Qwen 行为等价。
- 固定样本的聊天文本、令牌、标签掩码和截断结果一致。
- 优化器、调度器、有效批量、保存与恢复参数一致。
- 普通入口不会加载状态头或旁路清单。

### 7.3 `test_shared_b0_physics_train.py`

- 有效生成批量严格为 `4`；`2 x 2` 与 `1 x 4` 合法，其他组合拒绝。
- 200 优化步映射到 400 微步和 800 个生成样本位置。
- 2421 条物理样本各出现一次，批次为 21 个 7 和 379 个 6。
- 两条基线的生成顺序、物理顺序和状态头初始化哈希相同。
- `state_supervision` 不读取残差字段。
- `standard_pinn` 只增加 `0.01 * physics_residual_loss`。
- 物理字段不进入提示词或令牌。
- 掩码状态损失与手算结果一致。
- 残差与现有 `queue_balance_residual` 一致。
- 残差梯度到达状态头和 LoRA 参数。
- 变批物理批次的逐样本权重一致。
- 非有限损失和梯度立即失败。
- 连续运行与中断恢复等价。
- 配置、数据或基线身份不一致时拒绝恢复。

### 7.4 `test_shared_b0_physics_evaluation.py`

- 适配器、状态头、训练绑定和评估清单哈希完整。
- 调用公共评估器时不改变提示词和解码参数。
- 已完成评估幂等，未完成评估可恢复。
- 训练拟合诊断不会被标为未见测试。

### 7.5 `test_run_shared_b0_physics_baselines_wrapper.py`

- 脚本只允许 `smoke|formal` 和两个语义化基线名。
- 冒烟与正式运行目录隔离。
- 已完成正式目录拒绝覆盖。
- 正式模式强制 200 步、每 20 步保存和自动恢复。
- 启动前执行数据、批量、调度和绑定预检。
- 命令失败时保留原始退出码。

## 8. 本地验收命令

以下命令供后续实现任务执行，本次审计未运行：

```bash
cd /Users/bilibili/personal/note/thesis/experiments/llm_probe

uv run --no-sync pytest -q \
  tests/test_shared_b0_physics_sidecar.py \
  tests/test_shared_b0_physics_train.py \
  tests/test_shared_b0_physics_evaluation.py \
  tests/test_run_shared_b0_physics_baselines_wrapper.py \
  tests/test_train_sft.py \
  tests/test_evaluate_model.py \
  -W error::UserWarning

black \
  src/flow_probe/shared_b0_physics_sidecar.py \
  src/flow_probe/shared_b0_physics_train.py \
  src/flow_probe/shared_b0_physics_evaluation.py \
  src/flow_probe/train_sft.py \
  tests/test_shared_b0_physics_sidecar.py \
  tests/test_shared_b0_physics_train.py \
  tests/test_shared_b0_physics_evaluation.py \
  tests/test_run_shared_b0_physics_baselines_wrapper.py \
  tests/test_train_sft.py

prettier --write \
  configs/shared_b0_physics_sidecar_v1.yaml \
  configs/shared_b0_physics_baselines_seed42_200_v1.yaml \
  configs/shared_b0_state_supervision_seed42_genis_batch16_v1.yaml \
  configs/shared_b0_state_supervision_seed42_tqhc2_batch16_v1.yaml \
  configs/shared_b0_standard_pinn_seed42_genis_batch16_v1.yaml \
  configs/shared_b0_standard_pinn_seed42_tqhc2_batch16_v1.yaml

bash -n scripts/run_shared_b0_physics_baselines.sh
bash -n scripts/run_shared_b0_physics_evaluation.sh

uv run --no-sync python -m compileall -q src/flow_probe tests
```

如果项目已配置专用静态检查入口，应在上述检查后追加执行，不得以 `compileall` 替代项目静态检查。

## 9. 物化与预检命令

以下命令供后续实现任务执行，本次审计未运行：

```bash
cd /Users/bilibili/personal/note/thesis/experiments/llm_probe

uv run --no-sync flow-probe-build-shared-b0-physics-sidecar \
  --config configs/shared_b0_physics_sidecar_v1.yaml \
  --verify-double-materialization

uv run --no-sync flow-probe-train-shared-b0-physics \
  --config configs/shared_b0_physics_baselines_seed42_200_v1.yaml \
  --baseline state_supervision \
  --preflight-only

uv run --no-sync flow-probe-train-shared-b0-physics \
  --config configs/shared_b0_physics_baselines_seed42_200_v1.yaml \
  --baseline standard_pinn \
  --preflight-only
```

预检输出至少应显示：

- 分类清单路径、记录数与哈希。
- 物理旁路路径、2421 条记录与哈希。
- 有效生成批量 `4`。
- 200 个优化步、400 个微步、800 个生成样本位置。
- 物理调度为 21 个 7 和 379 个 6。
- 提示词字段白名单。
- 基线损失权重。
- 预计运行目录。

## 10. 同步命令

同步必须使用受管单文件入口，禁止直接调用 `ssh`、`scp` 或 `rsync`。每个文件使用唯一收据，先生成计划，复核后再加 `--apply`。

命令模板：

```bash
cd /Users/bilibili/personal/note/thesis/experiments/llm_probe

python3 scripts/guarded_rsync.py \
  --source <仓库内相对文件> \
  --destination <服务器项目根内相对文件> \
  --receipt runs/hook-receipts/shared-b0-physics-<文件标识>-plan-v1.json

python3 scripts/guarded_rsync.py \
  --source <仓库内相对文件> \
  --destination <服务器项目根内相对文件> \
  --receipt runs/hook-receipts/shared-b0-physics-<文件标识>-apply-v1.json \
  --apply
```

逐一同步第 6.1 节的新文件与第 6.2 节的修改文件。同步收据必须证明：

- `status=completed`。
- `applied=true`。
- 本地与远端 SHA-256 相同。
- 目标位于服务器固定项目根内。
- 没有 `--delete` 或目录级覆盖。

数据旁路产物优先在同一冻结源上确定性物化，不建议从本机直接同步大型运行目录。若必须同步产物，也必须逐文件受管同步并核对整个清单哈希。

## 11. 服务器验收命令

以下命令仅供后续经受管远程入口执行。本次审计未执行服务器命令。

### 11.1 最小测试

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe

uv run --no-sync pytest -q \
  tests/test_shared_b0_physics_sidecar.py \
  tests/test_shared_b0_physics_train.py \
  tests/test_shared_b0_physics_evaluation.py \
  tests/test_run_shared_b0_physics_baselines_wrapper.py \
  tests/test_train_sft.py \
  tests/test_evaluate_model.py \
  -W error::UserWarning
```

### 11.2 冒烟运行

```bash
bash scripts/run_shared_b0_physics_baselines.sh smoke state_supervision
bash scripts/run_shared_b0_physics_baselines.sh smoke standard_pinn
```

冒烟验收：

- 两条均完成至少 2 个优化步。
- 生成、状态和物理损失符合各自分支定义。
- 状态监督运行没有访问物理残差字段。
- 标准 PINN 的残差梯度非零且有限。
- 适配器、状态头、运行状态和日志均可加载。
- 冒烟目录不得作为正式目录恢复源。

### 11.3 恢复等价检查

```bash
bash scripts/run_shared_b0_physics_baselines.sh recovery-check state_supervision
bash scripts/run_shared_b0_physics_baselines.sh recovery-check standard_pinn
```

若脚本不提供 `recovery-check` 模式，则测试模块必须独立完成同等的 4 步连续运行与 2 步恢复对比。恢复等价检查未通过时不得启动正式运行。

### 11.4 正式运行

```bash
bash scripts/run_shared_b0_physics_baselines.sh formal state_supervision
bash scripts/run_shared_b0_physics_baselines.sh formal standard_pinn
```

正式运行目录固定为：

```text
runs/baselines/shared-b0-qwen-state-supervision-seed42-200-v1/
runs/baselines/shared-b0-qwen-standard-pinn-seed42-200-v1/
```

### 11.5 公开检测评估

```bash
bash scripts/run_shared_b0_physics_evaluation.sh state_supervision genis
bash scripts/run_shared_b0_physics_evaluation.sh state_supervision tqhc2
bash scripts/run_shared_b0_physics_evaluation.sh standard_pinn genis
bash scripts/run_shared_b0_physics_evaluation.sh standard_pinn tqhc2
```

## 12. 正式运行制品门禁

每个正式运行目录至少包含：

```text
resolved_config.yaml
environment.json
capabilities.json
training_binding.json
run_state.json
generation_order.json
physics_schedule.json
state_mask_audit.json
step_metrics.jsonl
checkpoints/checkpoint-000020/
checkpoints/checkpoint-000040/
...
checkpoints/checkpoint-000200/
adapter/
state_head/
train_summary.json
physics_train_fit_diagnostic.json
artifact_manifest.json
console.log
swanlog/
```

`artifact_manifest.json` 必须覆盖全部关键制品的相对路径、大小和 SHA-256。训练完成判定必须同时满足：

- `run_state.status=completed`。
- 最终优化步为 200。
- 400 个微步完整。
- 生成样本位置为 800。
- 物理样本消费数为 2421，重复数和遗漏数均为 0。
- 每 20 步检查点完整。
- 最终适配器和状态头可重新加载。
- 无非有限损失或梯度。
- 两条基线的共同绑定字段完全一致。
- 唯一差异为基线身份、`lambda_physics` 和由此产生的指标与参数。

## 13. 实施顺序

### P0

1. 建立正式实施计划，冻结本文件中的科学协议和文件范围。
2. 实现旁路物化器、清单和双次物化测试。
3. 提取普通 Qwen 公共训练构建路径，并通过行为等价回归测试。
4. 实现共同状态头训练路径、严格字段隔离和物理调度。
5. 实现完整检查点、双游标恢复与恢复等价测试。

### P1

1. 实现评估薄封装和适配器树哈希。
2. 实现受管启动脚本与脚本测试。
3. 完成本地全量目标测试、格式化和静态检查。
4. 逐文件受管同步并核对收据。
5. 服务器最小测试、两条冒烟和恢复等价检查。
6. 门禁全部通过后依次启动两个唯一正式运行。

### P2

1. 生成并冻结真正不相交的物理外部测试场景。
2. 在不重训两条基线的前提下追加外部物理评估。
3. 将最终公开检测结果与物理诊断写入实验总控。

## 14. 放行状态

```text
ready_for_planning=true
ready_for_implementation_after_plan=true
ready_for_training=false
classification_manifest_blocked=false
physics_sidecar_blocked=true
trainer_parity_blocked=true
checkpoint_resume_blocked=true
external_physics_claim_blocked=true
```

在旁路清单、训练器等价、字段隔离、共同调度和恢复等价五项门禁通过前，不得启动 200 步正式训练。
