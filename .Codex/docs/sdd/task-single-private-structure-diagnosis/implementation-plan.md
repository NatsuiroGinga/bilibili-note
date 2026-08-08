# 单私有 LoRA 结构与优化归因实施计划

## 实施目标

在不改变基座、S3 检测适配器、私有 LoRA 参数量、数据顺序、批量和评测协议的前提下，为现有非对称训练器增加 D1、D2、D3 三种预注册模式，并形成可直接在 RTX 5090 上运行、追踪、评测和统计的固定入口。

## 任务 1：实现损失模式与固定学习率轨迹

**修改文件**：

- `thesis/experiments/llm_probe/src/flow_probe/asymmetric_physics_train.py`

**具体动作**：

1. 增加四个明确模式：兼容既有 D0 的 `joint_constant`、D1 的 `generation_only`、D2 的 `physics_only`、D3 的 `joint_warmup_cosine`。
2. 用不可变契约记录每个模式是否启用生成、状态和物理损失，以及采用常数还是预热余弦学习率。
3. 固定 D3 正式轨迹：第 1 步为 `2e-5`，第 20 步为 `2e-4`，第 21 至 202 步无重启余弦衰减，第 202 步为 `2e-5`。两步冒烟复用正式 202 步轨迹的前两步，不重新缩放调度。
4. 每个优化步开始前设置实际学习率；逐步指标继续记录 `train/learning_rate`。
5. D1 只执行子类生成反向传播；D2 只执行双锚点状态与有限队列物理反向传播；D3 执行三种损失。三种模式仍生成相同的样本顺序文件，并使用相同优化器参数组。
6. 未启用的损失以数值 `0.0` 写入逐步日志，同时额外记录三个损失开关，避免把缺失指标误判为记录失败。
7. 配置快照与训练摘要写入诊断模式、损失开关、调度端点、状态头是否获得训练梯度、实际样本吞吐和模式化模式版本。
8. 命令行增加 `--diagnostic-mode`，默认 `joint_constant`，保证旧 D0 包装器语义不变。

## 任务 2：建立固定配置与运行入口

**新增文件**：

- `thesis/experiments/llm_probe/configs/asymmetric_diagnostic_seed42.yaml`
- `thesis/experiments/llm_probe/configs/asymmetric_diagnostic_d1_seed42_eval300.yaml`
- `thesis/experiments/llm_probe/configs/asymmetric_diagnostic_d2_seed42_eval300.yaml`
- `thesis/experiments/llm_probe/configs/asymmetric_diagnostic_d3_seed42_eval300.yaml`
- `thesis/experiments/llm_probe/scripts/run_asymmetric_diagnostic.sh`
- `thesis/experiments/llm_probe/scripts/run_asymmetric_diagnostic_eval.sh`
- `thesis/experiments/llm_probe/scripts/run_asymmetric_diagnostic_analysis.sh`

**具体动作**：

1. 训练配置完全复用 D0 的种子 42、数据文件、LoRA、批量、损失权重与梯度上限，只改变追踪说明。
2. 三份评估配置复用 S3/D0 的 `eval300` 协议，只固定各自唯一输出目录、运行名和标签。
3. 训练包装器只接受 `d1`、`d2`、`d3`，映射到预注册模式；输出目录由调用者显式给出，以同时支持两步冒烟和正式目录。
4. 评估包装器将 `d1`、`d2`、`d3` 映射到固定评估配置，拒绝覆盖既有目录。
5. 统计包装器复用 `s3_s4_detection_analysis.py`，以固定 S3 评估与训练制品为参照，并为每个诊断写入独立比较目录。输出中的历史键名 `s4` 只表示候选，报告必须明确这一点。

## 任务 3：最小直接验证

**新增文件**：

- `thesis/experiments/llm_probe/tests/test_asymmetric_physics_train.py`

**具体动作**：

1. 实现完成后再添加直接测试，不采用测试驱动开发。
2. 只覆盖模式开关、非法模式拒绝、D3 四个关键学习率点以及单调性，不重跑无关测试。
3. 本地只做文档和 Shell 静态检查；Python 语法与精确测试统一在 GPU 服务器运行。
4. 服务器验证顺序固定为：`py_compile`、`bash -n`、单个新测试文件、D1/D2/D3 各两步真实模型冒烟。
5. 冒烟必须核验：两步指标齐全、损失开关正确、D1 状态头梯度恒为零、D2 生成样本计数为零、D3 前两步学习率与正式轨迹一致、S3 摘要与家族 logits 完全不变、SwanLab 有逐步指标。

## 任务 4：服务器同步与正式实验

**服务器根目录**：`/root/autodl-tmp/thesis/experiments/llm_probe`

**具体动作**：

1. 使用 `rsync` 仅同步本计划列出的源码、配置、脚本和测试文件。
2. 使用 `uv pip install --no-deps -e .` 刷新命令入口；禁止执行裸 `uv sync`。
3. D1 与 D2 冒烟通过后并行运行 202 步；若显存不足则改为串行，不改变任何配置。
4. D1、D2 完成训练后分别执行固定 `eval300` 和 2,000 次配对自助统计。
5. D3 冒烟通过后单独运行 202 步、`eval300` 和配对统计。
6. 只有 D3 九项原门槛全部通过才生成种子 43、44 的后续计划；否则按因果矩阵停止。

## 验收边界

- 实现验收不等于方法通过；实现只证明三种干预严格按合同执行。
- D1、D2 永远只作归因证据，不得写为第三章最终算法。
- 正式训练总上限为五次，第一阶段只有 D1、D2、D3 三次。
- 不增加秩、损失权重、预热比例、峰值学习率、最低学习率、门控或其他调度器扫描。
- 旧 D0 运行和制品不可覆盖，旧入口默认行为必须保持不变。
