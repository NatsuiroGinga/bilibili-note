# 任务十三实现简报

## 任务定位

任务十一已经证明物理项在稀疏状态监督下显著改善未观测状态与物理残差，但直接联合训练伤害生成目标。当前只实现不更新参数的三目标梯度可行性诊断，为 G2-G5 训练候选提供一阶筛选证据。

## 必读文件

1. .Codex/docs/2026-07-21-任务十三三目标梯度可行性诊断实施计划.md
2. thesis/experiments/llm_probe/src/flow_probe/gradient_conflict.py
3. thesis/experiments/llm_probe/src/flow_probe/physics_train.py
4. thesis/experiments/llm_probe/tests/test_gradient_conflict.py
5. thesis/experiments/llm_probe/configs/physics_sparse_seed42.yaml

## 强制规则

- 禁止读取或调用 test-driven-development 技能。
- 直接实现后运行目标测试，不补造红测历史。
- 只修改实施计划列出的源码、测试和 pyproject.toml。
- 不修改 output/第一创新点实验总控.md、论文正文、数据集或模型权重。
- 不启动 20 批次正式诊断；本任务最多运行 2 批次在线冒烟。
- 不执行裸 uv sync。刷新入口只使用 uv pip install --no-deps -e .，测试使用 uv run --no-sync。
- 本机到服务器只使用白名单 rsync，禁止 --delete，排除 .venv、runs、模型、数据和凭据。
- 不覆盖或回滚已有用户改动。

## 必须实现

1. 新建 gradient_feasibility.py，提供 DirectionSolution、Gram 校验、共同下降求解、生成保护求解和 G5 反应代理。
2. 扩展 gradient_conflict.py 的状态与物理梯度函数，使其可选接受状态监督掩码；无掩码时保持任务七原行为。
3. 新增命令 flow-probe-diagnose-gradient-feasibility。
4. 使用 GeNIS 训练、GeNIS 验证和 ns-3 物理三套独立样本顺序。
5. 状态损失使用 anchor0_only，物理损失使用完整预测状态。
6. 每步记录共同下降、生成否决、保护解权重与边际、双辅助参与、两类 G5 反应代理、运行时间和峰值显存。
7. 保存计划规定的十类制品，并确认 optimizer_updates=0、LoRA 参数没有持久 grad。
8. SwanLab 必须每步在线记录指标，项目固定为 mortiswang/malicious-traffic-llm。

## 服务器验收

目标测试：

uv run --no-sync pytest tests/test_gradient_feasibility.py tests/test_gradient_conflict.py tests/test_physics_train.py -q

2 批次冒烟输出：

runs/physics-gradient-feasibility/qwen3-1.7b-seed42-anchor0-smoke2-v1

冒烟必须退出 0，逐步指标恰好 2 行，制品完整，SwanLab 原始日志存在，GPU 无残留计算进程。

## 报告

完整报告写入 .Codex/docs/sdd/task-13-gradient-feasibility-report.md，至少记录：

- 修改文件。
- 服务器同步命令与返回状态。
- 目标测试命令、通过数量和日志路径。
- 冒烟命令、输出路径、SwanLab 运行编号与地址。
- 两批逐步指标和汇总。
- 峰值显存、运行时间、GPU 清理状态。
- 已知风险与未完成项。

返回消息只给出状态、测试摘要、冒烟摘要、报告路径和风险。
