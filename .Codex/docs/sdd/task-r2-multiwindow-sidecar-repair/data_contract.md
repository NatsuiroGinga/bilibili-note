# R2 因果多窗口物理旁路修复数据合同

- **冻结日期**：2026-08-04
- **合同版本**：`r2-multiwindow-data-contract-v1`
- **适用范围**：TQH-C2 开发训练 2,048 条、开发验证 512 条
- **状态**：任务 1 已冻结，可进入任务 2；仍为开发试点，不是论文最终数据版本

## 1. 裁决边界

本合同只裁决严格因果的多窗口物理变换能否在开发验证集上提供超过纯文本、等信息量原始历史、置换旁路和随机旁路的检测增量。TQH-C2 不含队列、容量、服务量、丢包、往返时延、拥塞窗口或在途字节真值，因此不得报告 TQH-C2 物理状态误差，也不得把冻结辅助物理代理称为真实队列估计器。

所有组使用相同的 2,048/512 样本、`sample_id` 顺序、文本、标签、DistilBERT、编码器结构、可训练参数量、种子、优化器和 192 步训练预算。最终测试不可见，固定 `final_test_visible=false`。

## 2. 输入制品与摘要绑定

| 制品 | 只读路径 | SHA-256 | 用途 |
| --- | --- | --- | --- |
| 检测视图 | `thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-detection-view.parquet` | `6d8019dc15f2cd11abc2b4aa8a92ca81608b8000ef0c39eb83aae04607d9a126` | 文本、标签与稳定顺序 |
| 开发训练清单 | `thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-train-fit.jsonl` | `fc65e79932db4d9dece729478c5b4dd8b5b807697168af0be5db6cc6c49c937d` | 2,048 条训练样本 |
| 开发验证清单 | `thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-validation.jsonl` | `90298d6bb582b55f2149251a998a1c4948845db505748a8893a9cf4c2cbe6dd0` | 512 条验证样本 |
| 候选样本主表 | `thesis/experiments/llm_probe/runs/data-frozen/dataset-candidate-tqhc2-abc-v0/protocol/samples.parquet` | `05cb0774f8197f07d842a21d3c22ce07c111289b7cabe6950023b689c6b51dac` | 绑定观测序列摘要 |
| 包观测构建 A | `thesis/experiments/llm_probe/runs/data-frozen/r2-protocol-tqhc2-handoff-v0.build-a.partial/packet-observations.parquet` | `21168c943d7b9be043174a19cbde751c5cdb9c34b37e6902370998be88013991` | 唯一消费的逐包源 |
| 协议审计构建 A | `thesis/experiments/llm_probe/runs/data-frozen/r2-protocol-tqhc2-handoff-v0.build-a.partial/protocol.parquet` | `1c48b3437d5c17b0eb1524bc22856b1803b9dbb5d29b13b4f0593a7542b3560c` | 只作路由结果审计 |

构建 B 只证明双物化一致，不作为第二份训练输入。物化绑定上述字节摘要、2,560 个 `sample_id` 的稳定顺序摘要、`observation_sequence_sha256` 集合摘要、窗口合同版本及语义源码摘要。任何不一致均硬失败，不静默重算或覆盖旧制品。

## 3. 严格因果窗口

唯一排序键是 `packet_index`。固定四个非重叠窗口：

```text
w0 = [0, 2)
w1 = [2, 4)
w2 = [4, 8)
w3 = [8, N_at_decision)
```

`N_at_decision` 只表示分类决策时已经到达的包数。禁止按最终流长四等分、读取未来包或用标签、`profile`、模型输出选择窗口。`relative_time_ns` 只作回退审计；因果时钟按 `packet_index` 顺序累加 `max(delta_time_us, 0)`。

短流不得删除或补造。有效窗口必须构成非空前缀；空窗连续值为空、缺失位为 1、`window_valid=0`，张量化后连续位置填 0。窗口首包保留其相对上一包的已观测 `delta_time_us`。速率分母为本窗 `delta_time_us` 总和，分母为 0 时记缺失，不填数值零。

每窗只从 `packet_index`、`delta_time_us`、`network_length_bytes` 派生：

```text
total_packets
total_bytes
packet_length_mean
packet_length_min
packet_length_max
iat_mean_ms
packet_rate
byte_rate
```

包数与总字节必须跨窗精确重构整流值；包长均值和到达间隔均值必须按有效计数加权重构。方向、载荷长度、TCP 标志、突发编号和 QUIC 线图像字段不进入本轮模型。

## 4. 最终张量维数与字段顺序

### 4.1 原始历史张量

```text
raw_sequence: float32 [N, 4, 18]
  0:8   八个连续原始历史字段，顺序与第 3 节一致
  8:16  对应八个 *_missing，1 表示缺失
  16:18 两个恒零保留位
window_valid: bool [N, 4]
```

### 4.2 物理历史张量

```text
physics_sequence: float32 [N, 4, 18]
  0 estimated_queue_start
  1 estimated_queue_end
  2 normalized_enqueued
  3 normalized_dequeued
  4 normalized_conservation_residual
  5 normalized_boundary_residual
  6 state_uncertainty_start
  7 state_uncertainty_end
  8:16  对应八个 *_missing
  16:18 两个恒零保留位
physics_valid: bool [N, 4]
physics_uncertainty: float32 [N, 4]，未做 TQH 张量标准化且严格位于 [0,1]
```

最终每窗固定 **18 个字段位置**，每样本固定 **4×18=72 个浮点位置**。训练入口另接收 4 个有效窗布尔位和 1 个停止梯度融合门，因此旁路模型接口每样本共 77 个标量位置；`physics_uncertainty` 只在离线阶段计算该门，不额外输入模型。两个保留位必须在物化、加载和模型入口三处断言精确为零。

## 5. 路由合同

路由只能使用部署时可被动观测的 `transport_family`，且停止梯度：

```text
transport_family == TCP  -> tcp_expert
其他全部                -> shared_only
```

当前试点 2,400 条 TCP 走共享与 TCP 专家固定混合；68 条 ICMP 和 92 条 UDP 承载全部走 `shared_only`。这 92 条 UDP 承载在协议审计表中均为 `protocol_target=UNKNOWN`，不得启用 UDP 或 QUIC 专家。`protocol_target`、QUIC 线图像、`profile`、标签、采集配置、场景和来源路径只能审计，不能参与路由、旁路张量或分类输入。UDP 专家只保留辅助物理池证据，QUIC 专家在本试点中关闭。

## 6. 三套互不混用的尺度

### 6.1 ns-3 物理代理目标尺度

仅用 ns-3 十二个辅助拟合组冻结一个全局常量：

```text
auxiliary_target_scale = max(1, 辅助拟合组全部窗口的 truth_capacity_integral_link_bytes 最大值)
```

队列起点、队列终点、入队量和出队量都除以该常量。四个前缀预测器共同使用此常量，禁止逐样本、逐窗口或按完整四窗最大值缩放。该尺度不读取四个辅助校准组、TQH-C2、开发验证或最终测试，因此不含样本未来依赖。

冻结物理代理读取共同原始单位的 `proxy_raw_sequence_unscaled [N,4,16]`，窗口前缀输入维数固定为 `16/32/48/64`；不得读取 TQH 张量缩放后的值或两个保留位。

### 6.2 ns-3 不确定性校准尺度

不确定性只用四个独立辅助校准组的状态误差和共享/适用专家分歧计算，并截断到 `[0,1]`。它不等同于 `auxiliary_target_scale`，也不使用 TQH 标签。`shared_only` 的专家分歧固定为 0。

### 6.3 TQH 模型张量尺度

原始历史与未标准化物理历史分别拟合独立缩放器；二者都只能使用 2,048 条开发训练样本，四窗共享每字段一组统计：

```text
非负量: log1p(x)
有符号残差: sign(x) * log1p(abs(x))
z = clip((x_transformed - train_median) / train_iqr, -8, 8)
```

`train_iqr < 1e-6` 时该字段冻结为常量并输出 0。缺失位、有效窗和两个保留位不缩放。验证集不得拟合中位数、四分位距、缺失规则、阈值或不确定性尺度。禁止让物理代理读取 TQH 缩放值，也禁止让原始历史使用 ns-3 目标尺度。

## 7. 五组固定语义与同信息预算

| 组 | 固定输入 | 融合门 |
| --- | --- | --- |
| `T-A` | 全零 `[4,18]`，保留真实非空前缀有效窗 | 恒为 0 |
| `T-H` | 与样本正确配对的标准化原始历史 | 存在有效窗时为 1 |
| `T-P` | 由同一原始历史派生且正确配对的标准化物理历史 | `clip(1-有效窗未缩放不确定性均值,0,1)` |
| `T-S` | 严格分层后整段错配的物理历史 | 随序列移动后按未缩放不确定性计算 |
| `T-R` | 仅由开发训练池生成的随机物理历史 | 从抽样的原始 `[0,1]` 不确定性重新计算 |

五组张量形状、编码器、参数量、文本、样本、顺序、标签、划分和训练预算完全相同。`T-S/T-R` 的有效与缺失模式可按负对照合同变化，但不得获得额外字段或标签信息。旧静态 v0 结果不能代替任一新组。

## 8. 置换与随机负对照

### 8.1 `T-S`

按 `(source_dataset, transport_family, routing_class, split_id)` 分层，对完整 `physics_sequence [4,18]`、`physics_valid [4]` 和未缩放 `physics_uncertainty [4]` 一起做确定性循环错位。供体与受体 `sample_id` 必须不同；每层少于 2 条时硬失败。置换键和种子不含标签或 `profile`。

### 8.2 `T-R`

开发训练与开发验证的随机旁路都只能使用开发训练池，且顺序固定：

1. 在同一 `(source_dataset, transport_family, routing_class)` 层抽取一个开发训练供体的完整四窗 `physics_valid` 与 `8` 字段缺失模式，保证有效窗仍为非空前缀。
2. 对目标模式中每个有效且非缺失坐标，从 `(source_dataset, transport_family, routing_class, window_index, field)` 对应的开发训练池独立抽取**未标准化**值；值池只包含 `physics_valid=1` 且该字段 `missing=0` 的值。
3. 无效或缺失坐标保持空值，禁止把缺失占位零作为有效随机值。
4. 对完整未标准化随机表应用已经冻结的 TQH 物理缩放器，随后补缺失位与恒零保留位。
5. 从抽到的未标准化 `state_uncertainty_start/end` 重新计算窗口不确定性和样本融合门；禁止从标准化不确定性反推。

随机生成器固定为 `numpy.random.Generator(PCG64)`；种子取 `SHA-256("r2-multiwindow-random-v1\0<seed>\0<split>")` 的前 64 位。清单必须登记模式池、各坐标值池和输出张量摘要。任一必需层或值池为空时硬失败，不得扩大到标签、`profile` 或验证池。

## 9. 标签隔离与运行时门禁

`binary_label` 只由冻结检测视图在 `sample_id` 一一连接完成后交给分类损失。下列信息不得进入窗口派生、缩放器、物理代理、路由、置换、随机池、旁路张量或分类输入：标签及其派生字段、`profile`、采集单元、场景、来源路径、选择排名和最终测试身份。

正式入口在加载模型前至少断言：2,048/512 且无其他划分；2,560 个 ID 一一对应；173,196 个包且复合键唯一；四窗和前缀有效掩码合法；两个张量均为 `[N,4,18]`；保留位全零；92 条 UNKNOWN UDP 全部 `shared_only`；缩放器与随机池只绑定开发训练；五组文本、标签、顺序和预算摘要一致；`final_test_visible=false`。任一失败均终止当前组并保留证据。

## 10. 输出与 SHA-256 合同

新派生根固定为：

```text
thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/tqhc2-multiwindow-v1/
```

至少生成 `detection-view.parquet`、`raw-history.parquet`、`physics-history.parquet`、`normalization.json`、`input-summary.json` 和 `artifact-manifest.json`。窗口表精确为 10,240 行，并按 `stable_order, window_index` 唯一排序。

`artifact-manifest.json` 登记所有非自指制品的相对路径、字节数、字节 SHA-256、模式摘要和稳定顺序逻辑载荷摘要；同时登记输入摘要、字段顺序、窗口版本、三套尺度、路由计数、随机命名空间和源码摘要。探索性物化只执行一次，不要求 Parquet 容器逐字节双物化；同配置重建时逻辑载荷摘要必须一致。

## 11. 当前阻塞

任务 1 无数据合同阻塞。任务 2 可以在本机无卡模式下实现并物化，不需要扫描 PCAP，也不需要 GPU。进入训练前仍须完成任务 2 至任务 4 的实现和正式入口运行时门禁；本合同不保证 `T-P` 优于对照。
