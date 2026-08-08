# R2 QUIC 三协议物理旁路接入准备报告

> 日期：2026-08-03  
> 状态：**`integration_ready_split_and_estimator_pending`**  
> 边界：只完成 QUIC 物理辅助池的接入映射，不修改或重启正在运行的 TCP/UDP 先导

## 1. 结论

修复后 QUIC 先导 `build-a` 已按冻结的 100 毫秒窗口接入三协议先导合同。全部 `131,513` 个窗口均被保留，其中有效包窗口 `15,507` 个，空窗口 `116,006` 个。空窗口的共同八字段全部写为 `null` 并置 `_missing=1`，没有把空窗口伪装成数值零状态。

部署可观测共同字段与 qlog 训练期特权真值已拆成两个制品。部署制品不含 ACK、RTT、端点丢包、在途字节、拥塞窗口、包号或 qlog 事件；特权制品不作为分类输入，也没有读取标签、模型结果、旧 QUIC 候选或最终测试。由于本任务没有给出物理辅助池的训练/验证拆分规则，所有派生行保持 `split_id=physics-auxiliary-unassigned`，没有擅自把 16 条轨迹全部放入训练。

18 维旁路的字段顺序和每一维生产规则已全部定义，**结构映射覆盖率为 `18/18=100%`**。当前可直接物化的只有共享/TCP/UDP 专家掩码与协议置信度，**数值覆盖率为 `4/18=22.2222%`**。五个队列状态、四个队列残差和五个不确定性仍需下游估计器及校准接口，当前制品不能直接替代最终旁路 Parquet。

## 2. 冻结输入

唯一读取根目录：

`thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/quic/build-a/`

| 输入制品 | SHA-256 |
| --- | --- |
| `passive-windows.jsonl` | `5402d051354bd5c1b2fdf88ac83ac994f7403386126bb019bf150b58390eb4dd` |
| `privileged-truth.jsonl` | `e5b61b293571a50494ac1f6900b61fddb3e513a5846c83a0a49d02c226b265c3` |
| `schema.json` | `b139def4183fff6c89753a261e695ab014a8fdc30e3e443c02cfb2443b7d941a` |
| `manifest.json` | `2e388f84162e72efd1a24e585d5ddec4a58a0b3ba975095e25749a064d349339` |
| `input-lock.json` | `5cef05505293e97c6d8c3a113ca147d786d169451a3e041f4e2518ef444d8d11` |

本次依据的 QUIC 输入报告 SHA-256 为 `0e42dba6c3d793d3e61b1b8e7bd4a7f6fa2638b297e1ca0b560b242b7838f221`；ACK 语义修复独立复审报告 SHA-256 为 `02de96f66e77c2a0ccba2adb3760ae04d0903e08a89551ea640b0b84c1fe5eef`，复审结论为通过、严重问题 0 项、重要问题 0 项。

## 3. 窗口与稳定标识

- 基础窗口固定为 `100,000,000 ns`，不重叠，沿用每条轨迹首包对齐的完整时间轴。
- `window_id` 逐字保留源 `passive-windows.jsonl` 的 `sample_id`，共 `131,513` 个且全部唯一。
- `sample_id` 按非重叠 4 窗口、步长 4 生成，形式为 `quics:` 加稳定 SHA-256。
- 样本摘要载荷为 `namespace\0trace_id\0block_start\0window_duration_ns\04\04`。
- 共生成 `32,884` 个稳定样本，其中完整四窗样本 `32,871` 个，轨迹末尾部分样本 `13` 个。
- 末尾不足四窗的样本保持原长度并置 `sequence_complete=false`，没有丢弃窗口，也没有补零。
- 训练/验证轨迹分配尚未冻结，全部样本保持 `physics-auxiliary-unassigned`；下游拟合前必须先用与标签和结果无关的确定性规则完成拆分。

## 4. 共同八字段映射

共同字段只从 `passive-windows.jsonl` 派生。有效包窗口内八字段均有值；空窗口内八字段均为 `null` 且缺失掩码为 1。

| 共同字段 | 被动来源 | 映射状态 | 有值窗口 |
| --- | --- | --- | ---: |
| `total_packets` | `packet_count` | 精确 | 15,507 |
| `total_bytes` | `byte_count` | 包长层级待闭合 | 15,507 |
| `packet_length_mean` | `mean(packet_lengths_bytes)` | 包长层级待闭合 | 15,507 |
| `packet_length_min` | `min(packet_lengths_bytes)` | 包长层级待闭合 | 15,507 |
| `packet_length_max` | `max(packet_lengths_bytes)` | 包长层级待闭合 | 15,507 |
| `iat_mean_ms` | 已观测 `packet_interarrival_ns` 均值除以 `1e6` | 精确 | 15,507 |
| `packet_rate` | `packet_rate_per_second` | 精确 | 15,507 |
| `byte_rate` | `byte_rate_per_second` | 包长层级待闭合 | 15,507 |

当前 qlog 包长的协议层范围尚未证明与正式共同字段要求的 `network_layer_bytes` 完全一致。因此字节数、包长统计和字节速率已保留为可追溯的暂定映射，不得在单位接口闭合前宣称与 TCP/UDP 的 L3 字节量逐项同义。

## 5. 特权真值覆盖

qlog 字段只进入 `training-privileged-targets.jsonl`。缺失值保持 `null`，掩码保持布尔值；没有前向填充、插值或零填充。

| 特权真值 | 观测窗口 | 占全部窗口 | 占有效包窗口 |
| --- | ---: | ---: | ---: |
| 有效包 | 15,507 | 11.7912% | 100.0000% |
| 包号/包号空间 | 15,507 | 11.7912% | 100.0000% |
| ACK | 15,066 | 11.4559% | 97.1561% |
| 可用 ACK 延迟 | 15,061 | 11.4521% | 97.1239% |
| RTT | 13,118 | 9.9747% | 84.5941% |
| 在途字节 | 13,118 | 9.9747% | 84.5941% |
| 拥塞窗口 | 13,118 | 9.9747% | 84.5941% |
| 端点丢包事件 | 519 | 0.3946% | 3.3469% |
| 显式 PTO | 0 | 0.0000% | 0.0000% |

完整 ACK 范围、包号数组、丢包事件和指标更新不重复复制；下游按 `window_id` 与 `source_privileged_row_stable_order` 回查冻结 `build-a/privileged-truth.jsonl`。这保留了既有 Rust 物化制品作为事实来源。

## 6. 18 维旁路目标

冻结顺序与现有正式消费者一致：

| 维度 | 字段组 | QUIC 当前生产规则 |
| ---: | --- | --- |
| 0-4 | `estimated_queue_q0` 至 `estimated_queue_q4` | 待共享/QUIC 状态估计器输出；qlog BIF 不得替代瓶颈 L3 队列占用 |
| 5-8 | `normalized_queue_residual_w0` 至 `normalized_queue_residual_w3` | 待五锚点估计和四窗口队列动力学接口输出；ACK/端点丢包不得替代队列通量 |
| 9-13 | `state_uncertainty_q0` 至 `state_uncertainty_q4` | 待只依赖被动输入的校准估计器输出 |
| 14 | `shared_expert_mask` | `1.0` |
| 15 | `tcp_expert_mask` | `0.0` |
| 16 | `udp_expert_mask` | `0.0`，不得把 QUIC 伪装成普通 UDP |
| 17 | `protocol_confidence` | `1.0`，来源为已审计 qlog |

覆盖口径：

- 字段生产规则：`18/18=100%`。
- 当前直接数值：每个样本 `4/18=22.2222%`。
- 当前已物化数值单元：`131,536 / 591,912`。
- qlog 可直接提供的队列状态真值：`0/5`。
- qlog 可直接提供的队列守恒残差真值：`0/4`。

在途字节是发送端传输状态，拥塞窗口是发送端控制状态，均不是瓶颈队列占用。RTT、ACK 和端点丢包也不能补出缺失的链路容量、入队、出队或队列丢弃量。因此这些 qlog 字段只可用于训练期辅助监督、校准评价或诊断，不直接填入 18 维队列状态和残差。

## 7. 协议掩码与不确定性

QUIC 路由固定为：

```text
shared_expert_mask = 1
tcp_expert_mask = 0
udp_expert_mask = 0
quic_expert_mask = 1
protocol_confidence = 1.0
```

`quic_expert_mask` 属于三协议先导路由元数据，但不在现有正式 18 维向量中。正式消费者接口闭合前，QUIC 只能走共享专家；不能借用 `udp_expert_mask`。

五个状态不确定性遵守以下规则：

- 数值范围固定为 `[0,1]`。
- 有足够被动观测的锚点由训练拟合与校准分区冻结的估计器输出。
- 锚点所需相邻窗口存在空窗口时，最终物化必须强制最大不确定性 `1.0`。
- 当前目标制品输出 `uncertainty_forced_max_mask`，估计器发布前不伪造五个不确定性数值。
- qlog RTT、ACK、丢包、BIF 或 cwnd 的可用性不得作为部署不确定性输入，避免训练期特权信息泄漏。

锚点支持窗口固定为：`q0←[w0]`、`q1←[w0,w1]`、`q2←[w1,w2]`、`q3←[w2,w3]`、`q4←[w3]`。

## 8. 输出与哈希

输出根目录：

`thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/quic-integration/`

| 制品 | 行数 | SHA-256 |
| --- | ---: | --- |
| `build_integration.py` | - | `772648dc55d5d009ee91788b91b891f4644edb335c7bb484a40d7a775275ea9a` |
| `deployment-common-windows.jsonl` | 131,513 | `018bbdf686fab243759e8c7f7f7deeb772099229c6f5271e2fb937e32e79669a` |
| `training-privileged-targets.jsonl` | 131,513 | `a0b071eb3cc67c8d8eea9367b2043e5256b7b7448e6695526b94bf7d4988b6ce` |
| `sidecar-sample-targets.jsonl` | 32,884 | `0a99b3c370e5577663f714da5eed109c5c1feca1594df20bdfc559735d262078` |
| `sidecar-target-map.json` | - | `de7edf31d644f0cf2bcb71b778cee39453411796994a64b527a7f052812aa03a` |
| `schema.json` | - | `da3a8ea90f60b0c490883d302fcf11f121ff6115d7876d18e558ebc799090b3a` |
| `manifest.json` | - | `75ecce1382ea2ab5784717211694c676af0acd334bcbb6709fa7c16905dca135` |

## 9. 验证与未变更范围

物化器在一次流式读取中完成以下运行时断言：

- 五个 `build-a` 输入 SHA-256 与冻结值一致。
- 部署行与特权行的 `sample_id`、轨迹、排名、稳定顺序和窗口序号逐行一致。
- 16 条轨迹内窗口从 0 连续编号，窗口起止严格按 100 毫秒对齐。
- 包数组、收发计数、ACK 范围、确认包数、丢包事件和指标掩码一致。
- 输出窗口数、稳定窗口标识数和稳定样本标识数分别精确匹配。
- 禁止字段未出现在读取模式中；没有读取标签、模型结果、旧候选或最终测试。

随后使用 `wc -l` 复核三份 JSONL 行数，并使用 `shasum -a 256` 独立复算全部输出摘要，结果与清单一致。

按任务边界未运行格式化、Pyright、Ruff、pytest、Git 差异命令、GPU 或 SwanLab。未修改 `inputs/materialize_pilot_inputs.py`、`inputs/contracts/pilot-input-contract.json`、`inputs/ns3/`、`inputs/tqhc2/`、TCP/UDP 先导入口、配置或实验输出。

## 10. 尚缺接口

1. **物理辅助拆分缺口**：16 条 QUIC 轨迹的训练/验证确定性拆分尚未冻结，当前全部保持未分配，不能直接启动状态拟合。
2. **正式协议路由缺口**：三协议先导合同含 `quic_expert_mask`，现有 18 维正式消费者不含该字段。
3. **状态估计器缺口**：尚未发布能从共同被动字段和掩码为 QUIC 产生五个队列锚点及五个校准不确定性的估计器。
4. **残差接口缺口**：qlog 没有容量、入队、出队和队列丢弃真值，四维队列守恒残差只能依赖 ns-3 训练的动力学接口，不能由 ACK 或端点丢包直接构造。
5. **字节单位缺口**：qlog 包长的协议层范围与正式 `network_layer_bytes` 尚未完成证据绑定。
6. **最终物化缺口**：当前 18 维目标仍含 14 个 `null`，不能直接送入只接受有限数值的正式旁路消费者；需由状态估计器完成最终 Parquet 物化并绑定就绪回执。

在上述接口闭合前，本次状态只能解释为“QUIC 输入和目标映射已准备、拆分与估计器待接入”，不能解释为三协议物理旁路已经完成训练或产生增量检测结论。
