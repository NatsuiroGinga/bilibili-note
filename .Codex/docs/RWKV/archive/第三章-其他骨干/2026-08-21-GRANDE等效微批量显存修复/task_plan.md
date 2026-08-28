# GRANDE G-B 等效微批量显存修复实施计划

> **执行要求：**本计划由已分派的 Codex 实现代理逐项执行；仓库禁止人工测试夹具、自动格式化和本轮服务器实验，因此验收限于语法、导入、帮助、配置、启动器与数学归一化静态核验。

**目标：**在不改变 GRANDE G-B 模型、数据、有效批、训练步数或选择指标的前提下，以流级 FP32 微批量和梯度累积消除完整展平批次的反向传播显存溢出，并建立可恢复的新运行身份。

**架构：**新运行只读迁移旧运行已经完成的 G-A 选择收据、检查点、完整预算曲线、梯度门和资源收据，不重训 G-A。G-B 每个原始 64 序列优化步固定一次采样，按最多 2048 个有效流分块，以各微批二元交叉熵总和除以本步全部有效流数后反向传播，最后只执行一次梯度裁剪和优化器更新。

**技术栈：**Python、PyTorch、JSON、Bash、固定 GRANDE PyTorch 核心。

**规格：**父任务消息与 `.Codex/docs/RWKV/2026-08-20-GRANDE运行上限撤销说明.md`。

## 全局约束

- 新运行身份固定为 `ch3-grande-c00-protocolA-source-q0-seed42-v1-rerun1`；旧失败运行只读。
- G-A 的选择收据、曲线、检查点和身份逐字节迁移并记录源、目标 SHA-256，不重新训练。
- G-B 保持深度 5、1024 棵树、64 序列有效批、20 周期、每周期 1000 个优化步。
- FP32 微批是正式默认；BF16 仅为显式工程候选，不得与旧 FP32 G-A 混合选优。
- 激活检查点默认关闭；只有 FP32 微批仍显存溢出时才允许显式开启 `use_reentrant=False` 分支。
- 不访问服务器、不启动实验、不读取目标年数组、不修改指标或停止门、不恢复已撤销时长上限。

## 任务一：冻结配置和迁移边界

**文件：**

- 新建：`thesis/experiments/llm_probe/configs/ch3-grande-c00-protocol-a-source-q0-seed42-v1-rerun1.json`
- 修改：`thesis/experiments/llm_probe/tools/ch3_grande_protocol_a_source_q0.py`

**接口：**

- 消费：旧运行根中的 G-A 完成制品。
- 产出：`g-a-migration-receipt.json` 和新运行根内逐字节相同的 G-A 制品。

- [x] 配置固定新运行身份、旧运行根、微批、精度和恢复合同。
- [x] 准备阶段机械核验旧 G-A 的身份、20 周期、20000 步、检查点和曲线摘要。
- [x] 原子复制所需 G-A 制品并写迁移收据，目标已存在时只允许相同摘要。

## 任务二：实现等效流级微批训练

**文件：**

- 修改：`thesis/experiments/llm_probe/tools/ch3_grande_protocol_a_source_q0.py`
- 必要时最小修改：`thesis/experiments/llm_probe/vendor/grande/core.py`

**接口：**

- 消费：一个原始优化步固定采样得到的全部有效流。
- 产出：与完整批次 `BCEWithLogitsLoss(reduction="mean")` 数学等价的累计梯度。

- [x] 在采样后确定 `total_valid_flows`，每步只调用一次 `zero_grad(set_to_none=True)`。
- [x] 对每个流微批计算 `BCEWithLogitsLoss(reduction="sum") / total_valid_flows` 并逐次反向传播。
- [x] 全部微批结束后只执行一次有限性检查、梯度裁剪和 `optimizer.step()`。
- [x] 记录微批数、峰值已分配/保留 CUDA 显存、有效流吞吐和正式精度。
- [x] 提供显式 CUDA BF16 autocast 候选，保持参数、优化器、二元交叉熵和诊断为 FP32，不启用 GradScaler。
- [x] 提供默认关闭的非重入激活检查点分支，禁止静默回退。

## 任务三：实现优化步原子恢复

**文件：**

- 修改：`thesis/experiments/llm_probe/tools/ch3_grande_protocol_a_source_q0.py`

**接口：**

- 消费：当前模型、优化器、最佳模型、历史、计数、全部随机数状态和固定采样位置。
- 产出：优化步开始边界的原子检查点；微批中断后从该边界重放完整优化步。

- [x] 在 `zero_grad` 后、首个微批前原子保存完整优化步起点。
- [x] 恢复时区分周期完成检查点与优化步起点检查点。
- [x] 优化步起点恢复时复用已封印采样位置和随机数状态，不加载或保存半梯度。
- [x] 周期完成后继续保存原有选择历史和最佳检查点状态。

## 任务四：新启动器与静态验收

**文件：**

- 新建：`thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_grande_c00_protocol_a_source_q0_seed42_v1_rerun1.sh`
- 更新：`.Codex/docs/RWKV/2026-08-21-GRANDE等效微批量显存修复/notes.md`

**接口：**

- 消费：新配置和共享 GRANDE 工具。
- 产出：只执行 G-A 迁移、G-B 训练、聚合和发布的新运行入口。

- [x] 启动器禁止调用 G-A 训练阶段，检查迁移收据后才进入 G-B。
- [x] 资源监控继续记录外部 `nvidia-smi` 峰值、主存和墙钟时间。
- [x] 执行一次 `py_compile`、导入、`--help`、`--validate-config`、`bash -n` 和损失归一化静态核验。
- [x] 检查共享暂存区；非空时不提交。
