# 任务 2A 快速独立复审：E1/E2 训练核心

## 结论

- **规格符合性：通过。** 原重要问题已关闭；严格加载现在会验证训练完成状态、完整跟踪制品清单、SwanLab 原始日志以及当前 S3 的目录和内存参数绑定。
- **代码质量：通过。** 修复保持加载校验职责集中，并补充了原问题各触发路径的直接测试；未发现仍会阻塞任务 2B 或服务器实验的严重、重要问题。

## 问题分级

- 严重问题：无。
- 重要问题：无。

## 原重要问题复核

### 严格加载未验证运行完成状态和 S3 内容绑定：已关闭

**位置：**

- `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_train.py:868`
- `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_train.py:906`
- `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_train.py:933`
- `thesis/experiments/llm_probe/tests/test_bounded_physics_train.py:535`
- `thesis/experiments/llm_probe/tests/test_bounded_physics_train.py:567`
- `thesis/experiments/llm_probe/tests/test_bounded_physics_train.py:591`

复核结果：

- `load_bounded_structure_artifacts` 首先通过 `BoundedRunLayout` 执行全部强制制品存在性检查，不再接受只含三个结构文件的部分运行。
- `training_summary.json` 必须同时满足固定架构版本和 `status=finished`，并与结构变体、基座路径、S3 路径及冻结参数计数一致。
- `artifact_manifest.json` 必须满足跟踪清单版本、`status=finished`、固定训练阶段、非空 SwanLab 运行编号和完整制品键；对应 SwanLab 原始日志目录必须存在且非空。
- 当前 S3 目录会重新生成完整文件清单并与训练时保存值比较，文件内容、大小、路径或摘要变化都会拒绝加载。
- 训练前后 S3 参数摘要必须一致，当前运行时内存中的 S3 参数摘要还必须与训练后保存摘要相同。
- 结构状态只在上述校验全部通过后调用任务 1B 的 `strict=True` 接口加载。

新增直接测试覆盖完整运行成功加载、缺失清单、训练摘要失败态、跟踪清单失败态、缺失制品键、缺失 S3 清单、同路径 S3 文件变化和内存参数变化。原问题的成功路径与失败路径均已有对应断言。

## 已通过的重点核对

- E1 只反向传播生成损失，关闭的状态和物理损失记录为数值 `0.0`；E2 使用 `L_gen + 1.0 L_state + 0.01 L_physics`。
- 学习率函数满足第 1、20、21、202 步的固定预热余弦轨迹，训练循环在每次更新前写入对应学习率。
- 4 位模型准备显式传入 `use_gradient_checkpointing=False`，随后关闭并审计模型与子模块的检查点标志。
- 参数白名单冻结全部 Qwen、S3 和既有 LoRA，仅开放状态头、共享条件编码器、四层交叉注意力及四个门。
- 物理损失直接由预测状态构造，只对状态头求得非零梯度；条件编码器、交叉注意力、门和冻结基座未进入该损失的参数梯度路径。
- 生成梯度在第一次更新前仅到达门；门更新后第二步要求状态头、条件编码器、交叉注意力和门四类梯度均非零。
- 旧训练工具对生成批次、物理批次、双锚点掩码、状态损失、有限队列残差、样本调度、输入清单和 SwanLab 记录的复用与当前 E1/E2 契约一致。

## 验证边界

- 本次只做静态复审，未运行 `pytest`，未调用 `test-driven-development`，未修改生产源码或测试。
- 实现方已报告 Black、Ruff 和 `git diff --check` 通过；本次复核仍按任务约束不运行本地测试，新增直接测试须由 GPU 服务器执行。
