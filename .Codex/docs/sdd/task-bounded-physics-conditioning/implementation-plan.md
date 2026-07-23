# 有界物理条件交叉注意力实施计划

> **代理执行要求：** 使用 `subagent-driven-development` 按任务执行；禁止使用 `test-driven-development`。测试在实现后补充，只在 GPU 服务器运行。

## 实施目标

在冻结 Qwen3-1.7B 与既有 S3 检测适配器的前提下，实现零初始化、恒等旁路、相对范数受限的物理条件交叉注意力，形成 `E1-结构单支柱` 与 `E2-PINN 组合` 两个固定种子 42 实验，并复用 S3、S4 组成四组消融。

## 固定架构

- 模型：28 个解码层、隐藏维度 2048。
- 状态源：第 13 层提示末端表示，经现有 `ContinuousQueueStateHead(2048, 5)` 产生五个非负锚点。
- 条件词元：五个状态锚点加四个相邻状态增量，共 9 个。
- 注入位置：第 24、25、26、27 层输入前。
- 交叉注意力：每层独立参数，瓶颈 256、4 头；状态编码器跨层共享。
- 保护机制：每层独立标量门 `alpha_l=0` 初始化；逐令牌修正固定为 `0.1*tanh(alpha_l)*stopgrad(||h||)*z/(||z||+1e-6)`。
- 模型与环境：Qwen3-1.7B 4 位 NF4、`bfloat16`、梯度检查点关闭、贪心单束生成。

## 全局约束

- 基座路径固定为 `/root/autodl-tmp/thesis/models/Qwen3-1.7B`。
- S3 固定为 `runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1/final_adapter`。
- Qwen、S3 和全部既有 LoRA 参数冻结；不增加第二个 LoRA。
- E1 仅启用生成损失；E2 启用生成、双锚点状态和有限队列物理损失。
- E1/E2 均采用 D3 的固定轨迹：第 1 步 `2e-5`、第 20 步 `2e-4`、第 202 步 `2e-5`。
- 状态损失权重 `1.0`、物理损失权重 `0.01`、梯度裁剪 `1.0`。
- 数据、样本顺序、批量、未知攻击隔离、六分区评估、九项门槛和 2,000 次配对自助统计均不修改。
- 不修改 D0/D1/D2/D3、B0/B1、S3/S4 的源码语义和既有制品。
- 不扫描层位、词元、瓶颈、头数、残差上限、损失权重、学习率或锚点。
- 服务器只使用 `uv run --no-sync` 或 `uv pip install --no-deps -e .`，禁止裸 `uv sync`。

## 任务 1：核心条件结构与运行时

### 文件

- 新建 `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_conditioning.py`。
- 新建 `thesis/experiments/llm_probe/tests/test_bounded_physics_conditioning.py`。

### 必须实现的接口

- `ConditioningSpec`：不可变配置并严格校验固定架构值。
- `ConditioningDiagnostics`：记录四层门值、注意力熵、最大残差比例、挂钩次数、预填充次数和缓存解码次数。
- `PhysicalConditionEncoder`：把 `[B,5]` 状态和 `[B,4]` 差分编码为 `[B,9,256]`。
- `BoundedPhysicsCrossAttention`：接收 `[B,T,2048]` 与 `[B,9,256]`，输出受限修正和诊断量。
- `PhysicsConditionedRuntime`：注册第 13 层输出挂钩与第 24 至 27 层前向预挂钩，提供训练 `forward`、缓存式 `generate`、显式 `bypass`、严格保存加载接口。
- `resolve_conditioning_layers(28)`：只返回源层 `13` 和目标层 `(24,25,26,27)`；其他层数拒绝执行。

### 行为契约

1. 训练前向从 `labels` 得到提示边界和注入掩码。
2. 自由生成只在预填充计算一次状态，缓存解码复用同一条件；`try/finally` 清理会话，拒绝嵌套和 `num_beams != 1`。
3. 候选评分显式接收 `completion_start`，禁止完成文本参与状态预测。
4. 门为零时结构启用与旁路函数等价；旁路不捕获状态、不执行注入。
5. 在门乘法前拒绝非有限状态或注意力输出，避免 `0*NaN` 破坏恒等性。
6. 实现完成后添加直接测试，覆盖形状、9 个词元、四层挂钩、零门恒等、`0.1` 幅值界、首步门梯度、次步状态梯度、缓存生成、候选无泄漏、旁路和保存加载。

### 交付

- 不运行本地 pytest；只执行 Black、Ruff 和 `git diff --check`。
- 报告写入 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-1-report.md`。

## 任务 2：E1/E2 训练闭环

### 文件

- 新建 `src/flow_probe/bounded_physics_train.py`。
- 新建 `configs/bounded_physics_conditioning_seed42.yaml`。
- 新建 `scripts/run_bounded_physics_conditioning.sh`。
- 新建 `tests/test_bounded_physics_train.py`。
- 修改 `pyproject.toml`，增加 `flow-probe-train-bounded-physics = flow_probe.bounded_physics_train:main`。

### 行为契约

1. `ConditioningVariantContract` 只接受 `structure_only` 与 `combined`；包装器只接受 `e1` 与 `e2`。
2. 两组使用同形状结构、同训练样本顺序和同学习率；关闭的损失写为数值零。
3. 复用 `PhysicsTrainingSettings`、生成/物理批次、状态掩码、`masked_state_target_loss`、`queue_balance_residual`、输入清单和 SwanLab 记录。
4. 参数白名单仅包含状态头、条件编码器、四层交叉注意力和四个门，发现其他可训练参数立即失败。
5. E2 的物理损失只更新状态头：`physics_to_state_head_gradient_norm` 非零，`physics_to_injector_gradient_norm` 和 `physics_to_base_gradient_norm` 为零。
6. 第一步生成损失只允许门获得新增结构梯度；第一次更新后第二步生成损失必须到达状态头、条件编码器和四层交叉注意力。
7. 保存 `structure_config.json`、`structure_state.pt`、`base_binding.json`、`gradient_path.json`、`runtime_path_audit.json`、`bypass_equivalence.json` 及通用制品。
8. 实现后测试模式拒绝、损失开关、四个学习率关键点、参数冻结、梯度隔离、制品键和严格加载。

### 交付

- 不运行本地 pytest；只执行 Black、Ruff、`bash -n` 和 `git diff --check`。
- 报告写入 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-2-report.md`。

## 任务 3：正式评估与统计入口

### 文件

- 新建 `src/flow_probe/bounded_physics_evaluation.py`。
- 新建 `configs/bounded_physics_conditioning_seed42_eval300.yaml`。
- 新建 `scripts/run_bounded_physics_conditioning_eval.sh`。
- 新建 `scripts/run_bounded_physics_conditioning_analysis.sh`。
- 新建 `tests/test_bounded_physics_evaluation.py`。
- 修改 `pyproject.toml`，增加 `flow-probe-evaluate-bounded-physics = flow_probe.bounded_physics_evaluation:main`。

### 行为契约

1. 复用六分区、每类 300 条、阈值校准、标签解析和指标函数，但自由生成和候选评分都必须通过 `PhysicsConditionedRuntime`。
2. 同一提示的全部候选保存 `candidate_condition_repeat_max_diff`，超过 `1e-6` 判评估无效。
3. 同时保存结构启用与旁路预测；旁路与 S3 的 12 个预测文件逐样本一致。
4. 保留自由生成和候选评分的吞吐、词元数、延迟第 50/95 百分位和峰值显存字段。
5. 公开推理接口拒绝状态真值、场景号、攻击真值或未知攻击标记。
6. 统计包装器复用 `s3_s4_detection_analysis.analyze` 的九项门槛和 2,000 次配对自助法。
7. 实现后测试三条路径启用、旁路恢复、候选无泄漏、六分区与效率字段。

### 交付

- 不运行本地 pytest；只执行 Black、Ruff、`bash -n` 和 `git diff --check`。
- 报告写入 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-3-report.md`。

## 任务 4：服务器验收与实验

### 同步与目标测试

1. 使用 `rsync` 白名单同步新增源码、配置、脚本、测试和 `pyproject.toml`，禁止 `--delete`。
2. 服务端运行 `uv pip install --no-deps -e .`，再执行 `py_compile`、三个新增测试文件和新增脚本的 `bash -n`，不重跑无关测试。

### 两步冒烟

- E1：`runs/bounded-physics-conditioning/qwen3-1.7b-seed42-e1-structure-only-smoke2-v1`。
- E2：`runs/bounded-physics-conditioning/qwen3-1.7b-seed42-e2-pinn-combined-smoke2-v1`。

必须通过：初始化 logits 差不超过 `1e-6`；第一步门梯度非零且生成到状态梯度为零；第二步生成到状态和注入器梯度非零；E2 物理到状态梯度非零且物理到注入器梯度为零；状态置零、置换和扰动改变 logits；训练、生成、评分三路径启用；生成只有一次完整提示预填充；六分区旁路恢复 S3；SwanLab 指标完整。

### 固定种子 42 正式运行

两步冒烟通过后允许两个进程并行：

- E1：`runs/bounded-physics-conditioning/qwen3-1.7b-seed42-e1-structure-only-full202-v1`。
- E2：`runs/bounded-physics-conditioning/qwen3-1.7b-seed42-e2-pinn-combined-full202-v1`。

随后分别执行固定 `eval300` 和以 S3 为参照的 2,000 次配对自助统计。并行运行的吞吐和显存不进入正式效率结论。

### 最终门槛

1. E2 必须通过原九项门槛。
2. E2 相对 E1 的未观测状态误差和物理残差均至少改善 `10%`。
3. E2 相对 E1 至少一个检测主指标的配对自助置信区间不跨零，其他原门槛不得失败。
4. 若 E2 再次失败于未知攻击召回或校准，立即否决首选，不调整结构或训练常数。
5. 只有 E2 全部门槛通过才规划种子 43、44。

## 状态

- [x] 文献六阶段门禁。
- [x] 代码接口审计。
- [x] 首选架构审计。
- [ ] 任务 1：核心结构与运行时。
- [ ] 任务 2：E1/E2 训练闭环。
- [ ] 任务 3：正式评估与统计入口。
- [ ] 任务 4：服务器验收与实验。

## 已遇到错误

- 首次写计划时目标目录不存在；创建 `.Codex/docs/sdd/task-bounded-physics-conditioning/` 后重试，未产生部分文件。
