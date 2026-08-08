# 任务 1 实现报告：共享低秩基底物理状态编码专家

## 状态

**DONE_WITH_CONCERNS：实现完成，待正式基线后进行服务器验证。**

本任务已按简报完成 7 个允许文件的新增、后置测试编写、本地格式化、静态检查和实现自审。未修改任何既有文件，未提交 Git，未连接服务器，未在本机运行 `pytest`。

## 新增文件

1. `thesis/experiments/llm_probe/src/flow_probe/physics_routed_experts.py`
2. `thesis/experiments/llm_probe/src/flow_probe/physics_routed_experts_train.py`
3. `thesis/experiments/llm_probe/src/flow_probe/physics_routed_experts_analysis.py`
4. `thesis/experiments/llm_probe/configs/physics_routed_experts_seed42.yaml`
5. `thesis/experiments/llm_probe/scripts/run_physics_routed_experts_probe.sh`
6. `thesis/experiments/llm_probe/tests/test_physics_routed_experts.py`
7. `.Codex/docs/sdd/task-physics-routed-experts-probe/task-1-report.md`

## 固定接口

- `RouteThresholds(growth: float, pressure: float)`：冻结路由的两个有限标量阈值。
- `calibrate_route_thresholds(predicted_state)`：唯一数据参数为 `[N,5]` 冻结预测状态，固定计算增长量和压力的 `2/3` 分位数。
- `route_predicted_state(predicted_state, thresholds)`：按“高增长优先、高压力其次、其余平稳”返回 `[B]` 的 `0/1/2`。
- `hadamard_expert_codes(rank=16)`：返回 3 条满支持、两两正交的 16 维非平凡 Hadamard 行码。
- `SharedBasisStateExpert(hidden_size=2048, rank=16, residual_ratio_cap=0.1)`：每层只有一组共享 `A/B` 和一个零初始化有界门。
- `PhysicsRoutedExpertRuntime`：支持训练前向、候选评分、自由生成、显式旁路、固定专家覆盖和对应专家移除。
- `train_physics_routed_expert_variant(..., variant: Literal["single", "routed"])`：只接受 2 步冒烟或 50 步方向探针。
- `analyze_physics_routed_experts(single_output, routed_output, output)`：生成逐项门槛、失败门槛列表和 `overall_pass`。

## 实现内容

### 共享基底与参数预算

- 第 24、25、26、27 层各注册一组 `A∈R^(16×2048)`、`B∈R^(2048×16)` 和一个标量门。
- 四层共享基底参数数为 `4 × (16×2048 + 2048×16) = 262,144`。
- 四个门参数数为 `4`。
- 可训练 `outcome_state_head` 参数数为 `2048×5 + 5 = 10,245`。
- 两个变体的预计可训练参数总数均为 `272,393`。
- 冻结 `router_state_head` 另有 `10,245` 个参数，不计入可训练预算。
- 单码对照和路由候选均计算完整 16 维下投影、通道调制和上投影；固定码是缓冲区，不是参数。
- 四层共享矩阵由局部固定随机生成器确定性初始化，门初值为 0；两个变体初始化一致。

### 路由与泄漏防护

- 路由状态只来自第 13 层提示末端和冻结 `router_state_head`。
- 路由纯函数只接收预测状态和冻结阈值，不接收状态真值、容量、通量、攻击标签、数据来源或场景号。
- 阈值校准批次只构造既有公开物理提示，不读取状态目标或监督通量；保存的校准制品只含预测增长量和压力的数量、最小值、最大值、均值及 `2/3` 分位数摘要，不保存原始预测或真值。
- 训练集显式拒绝 `unknown_attack`，阈值校准也拒绝未知攻击标签。
- 攻击大类行的 `expert_row_mask` 固定为假；运行时在整批掩码为空时直接返回原隐藏状态，保证专家不参与家族路径。
- 家族审计保存训练前后直接冻结 S3 与运行时路径的最大逻辑值差，以及 S3 检测适配器和冻结路由头的训练前后摘要。
- 配置和制品显式保存允许字段、拒绝字段、路由优先级和家族关闭约束。

### 梯度路径

- `router_state_head` 深复制自 S3 状态头后全程冻结，路由状态在无梯度上下文中从第 13 层隐藏状态计算。
- `outcome_state_head` 同样从 S3 状态头初始化，但保持可训练；它从第 27 层专家注入后的提示锚点隐藏状态输出五维状态。
- 双锚点状态损失与 `queue_balance_residual` 物理损失作用于 `outcome_state_head` 的预测，因此梯度可经过第 27 层回到四层共享低秩专家。
- 训练逐步记录共享 `A/B`、四个门和结果状态头的梯度范数及非零梯度步数。
- 三个专家没有独立参数，报告不声称“独立专家参数更新”。专家活性证据是在物理验证集中按条件组固定专家码，分别对四层共享 `A/B` 计算该专家条件联合损失的 `autograd.grad` 范数，制品名称为“专家条件梯度”。

### 训练、诊断与分析

- 复用 `_build_settings`、固定生成和物理样本调度、双锚点掩码、既有批次构造、`queue_balance_residual` 和 `load_frozen_s3_model`。
- 训练固定种子 42、生成有效批量 `4×4`、物理批量 4、验证批量 8、学习率 `2e-4`、状态权重 1.0、物理权重 0.01、梯度裁剪 1.0。
- 两个变体按相同种子生成样本顺序，并在摘要中保存两类顺序文件的 SHA-256，分析器要求完全一致。
- 路由使用制品分别保存子类生成验证集和物理验证集的三专家数量、使用率、最小使用率和归一化熵。
- 专门化制品保存物理验证集 `3×3` 条件联合损失矩阵、逐行对角优势和对应专家移除后的状态损失退化。
- 分析器逐项执行正式 50 步、同种子、预算相等、样本顺序相等、无泄漏、码正交、使用率、条件梯度、专门化、家族等价和联合收益门槛；任一门槛失败即 `overall_pass=false`，并给出停止且不调参、不扩展 202 步的动作。
- 包装器只接受 `single|routed`、唯一输出目录和 `2|50`，使用 `uv run --no-sync python -m flow_probe.physics_routed_experts_train`，文件权限为 `755`。

## 后置测试

新增测试覆盖：

- 固定 `2/3` 分位数校准和高增长优先级。
- 非法预测状态拒绝。
- Hadamard 三码的形状、满支持、正交性和确定性。
- 单层共享参数预算、零门严格等价、相对残差上界和 `A/B` 梯度。
- 运行时冻结路由头、可训练结果头、共享基底梯度和冻结模型无梯度。
- 家族行全关、显式旁路、候选评分、固定专家、对应专家移除和缓存自由生成。
- 分析器全部门槛通过、输出拒绝覆盖以及任一使用率门槛失败时的一票否决。

根据仓库规则和任务简报，**未在本机运行 `pytest`**。服务器行为测试亦因主控暂停而未运行。

## 格式化与静态检查

### 已执行并通过

1. 语法预检：
   - `python -m py_compile src/flow_probe/physics_routed_experts.py src/flow_probe/physics_routed_experts_train.py src/flow_probe/physics_routed_experts_analysis.py tests/test_physics_routed_experts.py`
   - Black 前后均通过，无语法错误。
2. Black：
   - `uv run --no-sync black src/flow_probe/physics_routed_experts.py src/flow_probe/physics_routed_experts_train.py src/flow_probe/physics_routed_experts_analysis.py tests/test_physics_routed_experts.py`
   - 4 个文件均已格式化。
3. Ruff：
   - `uv run --no-sync ruff check src/flow_probe/physics_routed_experts.py src/flow_probe/physics_routed_experts_train.py src/flow_probe/physics_routed_experts_analysis.py tests/test_physics_routed_experts.py`
   - 一次检查通过，无报告项。
4. Shell 语法：
   - `bash -n scripts/run_physics_routed_experts_probe.sh`
   - 通过。
5. YAML 解析：
   - 使用 `yaml.safe_load` 解析 `configs/physics_routed_experts_seed42.yaml`，并断言种子 42、正式步数 50、秩 16。
   - 通过。
6. 差异空白检查：
   - `git diff --check`
   - 通过。
7. 范围检查：
   - `git status --short -- <7 个允许路径>` 仅显示本任务新增文件；报告写入前显示其余 6 个新增文件。
   - 未修改任何既有文件。

### 检查过程说明

- 全局 `black` 不在 `PATH` 中。
- 首次尝试通过项目 `uv` 查询 Black 时，沙箱禁止访问用户缓存目录；随后仅获准使用项目现有 `uv` 环境执行 Black 和 Ruff，均未同步或下载依赖。

## 未运行项

- 未运行本机 `pytest`：仓库局部规则明确禁止 Python 变更在本机运行 `pytest`。
- 未运行服务器 `pytest`、GPU 两步冒烟、50 步正式训练、配对分析或 SwanLab 云端复核：任务简报禁止连接服务器，主控同时明确暂停服务器验证。
- 未生成运行制品：只有真实服务器运行后才会产生配置快照、环境、输入摘要、样本顺序、阈值、逐步指标、结构权重、路由使用、专门化、家族等价、SwanLab 原始日志和制品清单。

## 遗留风险

1. 实际 Qwen3-1.7B 与 PeftModel 的第 13、24 至 27 层挂钩路径尚未经过服务器行为测试；本地测试只使用后置伪模型测试，且未执行。
2. BF16、4 位量化和 RTX 5090 环境中的梯度贯通、显存峰值、自由生成缓存路径与训练吞吐尚未验证。
3. 三个预测潜态在真实验证集中的覆盖率未知；任一组缺样本、使用率低于 0.05 或归一化熵低于 0.50 会按设计直接否决。
4. 共享基底是否形成严格对角专门化、对应移除是否产生正向退化，以及联合收益是否达到 1% 均属于待实验裁决事实，当前实现不预设通过。
5. 两个独立运行的冻结预测阈值和样本顺序必须完全一致；分析器会拒绝任何不一致，服务器运行前仍需核对输入制品哈希。

## 结论

实现和本地静态门禁已完成，当前不具备行为验收或方法有效性结论。下一状态是：**待正式基线可用后，在服务器依次执行两个 2 步冒烟、两个种子 42 的 50 步运行及配对分析，再依据 `overall_pass` 裁决是否保留该方向。**

