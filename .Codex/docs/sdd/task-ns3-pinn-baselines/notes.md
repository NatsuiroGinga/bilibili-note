# 星型 ns-3 同协议物理基线证据笔记

## 2026-07-24 输入与环境预检

### 数据路径与哈希

- 本地输入根目录：`thesis/experiments/llm_probe/runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/`。
- 服务端输入根目录：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/`。
- `train.jsonl`：`d6a6ca23a985223401e1d650d619c2a50b255d2066769e2478cef72cc6239fa0`。
- `validation.jsonl`：`0bbbb4ea483867561c329c896cb4e7745a102cb90024c464654e0b7d673c8723`。
- `test.jsonl`：`6e64d2ab290813a246ed8efcefd1bb19f1026c2de7b7904d111af67b4465ef94`。
- `split_manifest.json`：`3393d76e96b9104ea78a8a52bc73e72e2298798a4a4db29dbf76ef412eb88785`。
- 上述四个哈希已在本地与服务器逐项核对一致。

### 样本与组隔离

| 划分 | 唯一样本 | 唯一组 | 文件内 `split` |
| ---- | -------: | -----: | -------------- |
| 训练 |      807 |      7 | `train`        |
| 验证 |      807 |      7 | `validation`   |
| 测试 |      807 |      7 | `test`         |

- 训练－验证、训练－测试、验证－测试的 `sample_id` 交集均为 `0`。
- 训练－验证、训练－测试、验证－测试的 `group_id` 交集均为 `0`。
- 三个划分的组前缀唯一为 `star-bottleneck-v1`；本轮没有哑铃或停车场拓扑。
- 数据划分来源分别是 ns-3 生成种子 42、43、44；后续模型随机种子仍独立使用 42、43、44，不能把数据来源种子误写成模型三种子。

### 输入信息预算

全体 2,421 条样本的 `model_inputs` 键集合唯一且固定为：

1. `capacity_start_bps`
2. `capacity_end_bps`
3. `configured_capacity_integral_link_bytes`
4. `qdisc_received_l3_bytes`
5. `qdisc_received_packets`

标签、场景、拓扑、源路径、组号、种子、成功离开量、两类丢弃量、队列真值和保存的审计残差均不在 `model_inputs` 中。成功离开量与两类丢弃量只允许标准 PINN 在训练损失中构造守恒残差，不得进入前向输入。

### 现有代码回归基准

- 本地和服务端的 `physics_train.py`、`ns3_sequences.py`、`tracking.py`、两份相关测试、`pyproject.toml` 与 `uv.lock` 的 SHA-256 均一致。
- 服务端命令：`uv run --no-sync pytest -q tests/test_ns3_sequences.py tests/test_physics_train.py -W error::UserWarning`。
- 结果：`37 passed in 1.70s`。
- 现有实现已经提供五字段接口、`anchor0_plus_one` 组级掩码、五锚点非负状态头和可微有限队列守恒残差；当前缺口是常数基线、语义化三种子入口、严格的验证选择后测试和统一运行制品。

### 服务端资源

- 数据盘：总计约 50 GiB，已用 30 GiB，可用 21 GiB，使用率 59%，未触发空间告警。
- GPU：NVIDIA GeForce RTX 5090，显存 32,607 MiB；检查时显存占用 0 MiB、利用率 0%。
- 检查时没有 `screen` 会话，也没有基线训练进程。

## 2026-07-24 独立审查与修复证据

- 首轮独立审查结论为严重问题 `0`、重要问题 `4`。四项问题分别是测试内容在选择前物化、完成状态写入过早、SwanLab 最终指标步数可能回退、冒烟与正式运行身份不够明确。
- 输入处理已拆成两阶段：训练前只流式保留三个划分的 `sample_id`、`group_id` 和公共五字段审计结果；训练与验证内容随后物化；测试状态真值和通量只有在选择回调返回且选择结果类型通过校验后才物化。
- 运行状态现为 `running → finalizing → awaiting_tracking_verification`。只有人工确认云端指标点和图表可见、写入 `tracking_verification.json` 并再次完成本地制品校验后，单独的 `verify-tracking` 命令才会写入 `finished`。
- 最终 SwanLab 指标步骤固定为 `len(training_history) + 1`；常数基线固定为步骤 `1`，不会再按早于停止轮次的最佳轮次计算。
- 正式运行只允许写入 `runs/baselines/theory-selection/ns3-star-physics/review-pending-3393d76e-v1/<baseline>-seed<seed>`；冒烟运行只能写入 `runs/smoke/ns3-star-physics/` 的子目录。摘要、运行状态、SwanLab 元数据和标签均包含运行类型、有效最大轮数与协议完整性字段。
- 修复后最后一次服务器相关回归为 `41 passed in 2.06s`。不联网真实数据冒烟中，常数基线完成五维常数冻结，两种神经基线均完成两轮 CUDA 训练；三者都只在选择完成后物化 807 条测试样本。
- 在线 SwanLab 冒烟与九次正式矩阵仍未执行。安全审批明确要求先取得用户对上传配置、指标、日志和制品元数据的知情授权，未获授权前不得重试或绕过。

## 证据边界

- 本轮只建立星型 ns-3 物理机理基线，不是完整 `dataset-v1` 上的公共检测基线。
- 结果必须标记为 `theory_selection/review_pending`；完整 A/B/C、GeNIS 冻结清单和跨拓扑外测完成前，不得用于选择 R1、R2、R3 或冻结第三章算法。
