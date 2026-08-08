# 任务 1 简报：共享低秩基底物理状态编码专家实现

## 任务位置

本任务实现一个独立的种子 42、50 步方向探针。它是当前有界物理条件注意力主线之外的备选验证，不得修改或改名 D0-D3、B0/B1、E1/E2。

## 必读设计

先完整读取：

- `.Codex/docs/sdd/task-physics-routed-experts-probe/design.md`
- `thesis/AGENTS.md`
- `thesis/experiments/llm_probe/AGENTS.md`
- `.Codex/docs/AGENTS.md`

## 只允许新增的文件

- `thesis/experiments/llm_probe/src/flow_probe/physics_routed_experts.py`
- `thesis/experiments/llm_probe/src/flow_probe/physics_routed_experts_train.py`
- `thesis/experiments/llm_probe/src/flow_probe/physics_routed_experts_analysis.py`
- `thesis/experiments/llm_probe/configs/physics_routed_experts_seed42.yaml`
- `thesis/experiments/llm_probe/scripts/run_physics_routed_experts_probe.sh`
- `thesis/experiments/llm_probe/tests/test_physics_routed_experts.py`
- `.Codex/docs/sdd/task-physics-routed-experts-probe/task-1-report.md`

不得修改 `pyproject.toml` 或任何既有源文件、配置、脚本、测试和运行目录。不要提交 Git，不要推送，不要连接服务器。

## 固定接口

- `RouteThresholds(growth: float, pressure: float)`。
- `calibrate_route_thresholds(predicted_state: Tensor) -> RouteThresholds`，唯一数据输入为 `[N,5]` 预测状态。
- `route_predicted_state(predicted_state: Tensor, thresholds: RouteThresholds) -> Tensor`，返回 `[B]` 的 `0/1/2`。
- `hadamard_expert_codes(rank: int = 16) -> Tensor`，返回 `[3,16]` 的固定满支持正交码。
- `SharedBasisStateExpert(hidden_size=2048, rank=16, residual_ratio_cap=0.1)`，候选与对照共享相同 A/B、秩、参数量和激活参数预算。
- `PhysicsRoutedExpertRuntime`，支持训练前向、候选评分、自由生成、显式旁路、固定专家覆盖和对应专家移除。
- `train_physics_routed_expert_variant(..., variant: Literal["single", "routed"])`，只接受 `2` 或 `50` 步。
- `analyze_physics_routed_experts(single_output, routed_output, output)`，生成逐项门槛和 `overall_pass`。

## 不可变结构

- 冻结 Qwen3-1.7B 和 S3 检测适配器。
- 第 13 层提示末端由冻结 `router_state_head` 产生路由状态。
- 第 24、25、26、27 层各有一组 rank 16 共享 A/B 和零初始化有界门。
- 可训练 `outcome_state_head` 从专家注入后的最终隐藏状态产生双锚点与物理损失状态。
- 单适配器使用全 1 码；路由候选使用三个无参数 Hadamard 非平凡行码。必须保存三个码的两两内积。
- 路由只使用预测增长 `q4-q0` 和预测压力 `mean(q)`。阈值由冻结预测状态的固定 `2/3` 分位数计算；高增长优先累积，其次高压力为饱和，其余平稳。
- 攻击大类行的专家掩码固定为假，家族路径必须与冻结 S3 在 `1e-6` 内等价。
- 状态和物理损失必须能反向到共享低秩专家与 `outcome_state_head`；路由头全程冻结。

## 固定训练与分析

- 种子 42；生成有效批量 `4 x 4`；物理批量 4；验证批量 8。
- 学习率 `2e-4`；双锚点；状态权重 `1.0`；物理权重 `0.01`；梯度裁剪 `1.0`。
- 只使用既有生成和 ns-3 文件；未知攻击标签不进入训练或阈值校准。
- 两个变体必须保存相同生成与物理样本顺序。
- 路由使用门槛：每专家使用率至少 `0.05`，归一化使用熵至少 `0.50`，每专家有非零梯度或更新。
- 专门化：物理验证集 `3 x 3` 条件联合损失矩阵每行对角最优，且移除对应专家后对应状态损失正向退化。
- 联合收益：子类生成验证损失相对单适配器至少改善 `1%`；未观测状态误差和物理残差至少一项改善 `1%`，另一项恶化不超过 `1%`；家族逻辑值等价。
- 任一门槛失败即 `overall_pass=false`，不提供调参或 202 步入口。

## 工程要求

- 复用 `physics_train` 的设置、样本调度、双锚点掩码、批次和 `queue_balance_residual`，以及 `bounded_physics_train.load_frozen_s3_model` 的加载方式；不得修改这些既有文件。
- 输出必须含配置、环境、输入哈希、样本顺序、路由阈值、允许/拒绝字段、码内积、逐步指标、结构权重、训练摘要、路由使用、专门化、家族等价、SwanLab 原始日志和制品清单。
- SwanLab 固定在线项目 `mortiswang/malicious-traffic-llm`。
- 包装器只接受 `single|routed`、唯一目录和 `2|50`，使用 `uv run --no-sync python -m`。
- 项目禁止测试驱动开发：先实现，再编写测试。不要在本机运行 pytest。
- 完成后对新增 Python 文件与测试运行 Black，一次 Ruff；对脚本运行 `bash -n`；解析 YAML；运行 `git diff --check`。如本机缺少工具，准确记录未运行，不下载依赖。

## 报告合同

将完整报告写入 `.Codex/docs/sdd/task-physics-routed-experts-probe/task-1-report.md`，至少包含：

- `DONE`、`DONE_WITH_CONCERNS`、`NEEDS_CONTEXT` 或 `BLOCKED`。
- 新增文件与接口。
- 实际执行的格式化、静态检查和结果。
- 未运行的服务器测试与原因。
- 参数预算实现、路由泄漏防护和梯度路径自审。
- 遗留风险。

返回消息只给出状态、文件数量、静态检查摘要和关注点，不粘贴完整报告。
