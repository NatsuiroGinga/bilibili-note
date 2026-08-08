# R2 因果多窗口旁路修复数据可行性审计

日期：2026-08-03  
审计范围：只读核对本机 TQH-C2 开发试点输入、逐包制品、物化代码与字段合同  
实验边界：未连接服务器，未运行测试，未启动或修改实验，未读取最终测试清单

## 1. 结论

**开发训练 2,048 条和开发验证 512 条可以直接从本机现有逐包制品派生因果多窗口输入，不需要重新扫描 PCAP，也不需要从服务器回收数据。**

当前 2,560 个 `sample_id` 在本机双物化的 R2 TQH-C2 包表中全部命中，共关联 173,196 个包；`sample_id`、`profile`、标签、包数均无连接不一致，复合包键 `(sample_id, packet_index)` 无重复。建议冻结长度为 4 的非重叠因果包块：

```text
w0 = [0, 2)
w1 = [2, 4)
w2 = [4, 8)
w3 = [8, N_at_decision)
```

其中 `N_at_decision` 是分类决策时已经观测到的包数，不是标签、会话元数据或未来包数。前 3 个边界不依赖最终流长，最后一窗只聚合决策时已经到达的尾部。2,502/2,560 条样本拥有至少 10 个包，因此四窗均非空；余下 58 条短流必须保留原划分并用有效窗掩码表示，禁止删除、按标签补采或重复伪造窗口。

该结论只证明**包历史物化可行**，不证明物理旁路有效。TQH-C2 没有队列、容量、服务量、丢包、往返时延、拥塞窗口或在途字节真值，旧 ns-3 状态估计器也不能在输入语义改变后直接视为可复用模型。

## 2. 本机实际可用制品

### 2.1 当前试点输入

| 制品 | 本机路径 | 字节数 | SHA-256 | 状态 |
| --- | --- | ---: | --- | --- |
| 输入摘要 | `thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/input-summary.json` | 2,365 | `028d18d41d5703b3792f6440948716edea43b6f45ddf1ebb427f816ebd829462` | 开发试点 |
| 检测视图 | `thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-detection-view.parquet` | 197,167 | `6d8019dc15f2cd11abc2b4aa8a92ca81608b8000ef0c39eb83aae04607d9a126` | 2,048/512 冻结输入 |
| 静态 18 维旁路 | `thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-sidecar.parquet` | 174,746 | `56658ea8886a57cdefe1dba2268e658f9072e24a94b93d5bf7a3711db9de2553` | 旧 T-P 输入，不应原位覆盖 |
| 训练选择清单 | `thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-train-fit.jsonl` | 1,291,178 | `fc65e79932db4d9dece729478c5b4dd8b5b807697168af0be5db6cc6c49c937d` | 2,048 条 |
| 验证选择清单 | `thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-validation.jsonl` | 322,962 | `90298d6bb582b55f2149251a998a1c4948845db505748a8893a9cf4c2cbe6dd0` | 512 条 |
| 候选样本主表 | `thesis/experiments/llm_probe/runs/data-frozen/dataset-candidate-tqhc2-abc-v0/protocol/samples.parquet` | 约 8.6 MiB | `05cb0774f8197f07d842a21d3c22ce07c111289b7cabe6950023b689c6b51dac` | 含序列摘要与审计元数据 |

训练与验证选择由稳定 `sample_id` 哈希产生，输入摘要明确记录 `selection_used_labels=false`。当前划分和顺序应保持不变。

### 2.2 推荐读取的双物化包表

| 构建 | 本机路径 | 行数 | 列数 | 字节数 | SHA-256 |
| --- | --- | ---: | ---: | ---: | --- |
| 构建 A | `thesis/experiments/llm_probe/runs/data-frozen/r2-protocol-tqhc2-handoff-v0.build-a.partial/packet-observations.parquet` | 2,475,729 | 39 | 17,446,431 | `21168c943d7b9be043174a19cbde751c5cdb9c34b37e6902370998be88013991` |
| 构建 B | `thesis/experiments/llm_probe/runs/data-frozen/r2-protocol-tqhc2-handoff-v0.build-b.partial/packet-observations.parquet` | 2,475,729 | 39 | 17,446,431 | `21168c943d7b9be043174a19cbde751c5cdb9c34b37e6902370998be88013991` |

双构建比较回执位于 `thesis/experiments/llm_probe/runs/launchers/r2-tqhc2-double-materialization-compare-20260731/comparison.json`。四项制品比较状态为 `pass`，包表模式摘要为 `22d9478e1e20c495d2e3bb97903bfeb483312d761a52f09a36f2ab90f30ec37f`，载荷 Merkle 为 `51deee4da715e234763c63e0aa061d20afb29ec37e7ffcdd487e936ef8b329cf`。

这两份目录仍带 `.partial`，不能写成已正式发布的数据版本。开发试点可以在配置中绑定构建 A 的固定哈希并保持 `review_pending`；构建 B 只作一致性证据，不应重复进入模型。若实施计划禁止消费 `.partial`，本机仍有下列三份上游 14 列包表可直接派生，不需要服务器数据：

| `profile` | 本机路径 | 总行数 | 字节数 | SHA-256 |
| --- | --- | ---: | ---: | --- |
| A | `thesis/experiments/llm_probe/runs/data-frozen/dataset-v1-provisional/tqh-c2-A-20260728-v1/views/packet_observations.parquet` | 15,761,376 | 161,878,279 | `2366a25dc3a3c847ecb3549c4d79d131e172a17aa53b709dd65949a26647a32f` |
| B | `thesis/experiments/llm_probe/runs/data-prepared/tqh-c2-b-v101-provisional-20260728/views/packet_observations.parquet` | 9,857,089 | 101,019,345 | `97e736d28920702c3fab72cf86040a3258d4f0dcd8ea6a2c9db31d4b60a2f108` |
| C | `thesis/experiments/llm_probe/runs/data-frozen/dataset-v1-provisional/tqh-c2-C-20260724-v8/views/packet_observations.parquet` | 396,271 | 3,897,491 | `44547ce8421015ebfe5efead5fac4638ad5169137db735955e550c800fd4ef86` |

## 3. 可用逐包字段

### 3.1 本轮应使用的 14 个基础字段

| 字段 | 物理类型 | 本轮角色 | 约束 |
| --- | --- | --- | --- |
| `sample_id` | `string` | 连接与审计 | 不进入模型数值向量 |
| `packet_index` | `int32` | 唯一因果顺序 | 每样本从 0 连续递增 |
| `relative_time_ns` | `int64` | 只作质量审计 | 当前试点并非全部单调，不能作为唯一排序键 |
| `delta_time_us` | `int64` | 窗口间隔与因果时钟 | 非负；按 `packet_index` 累加 |
| `direction` | `int8` | 可选被动观测 | 仅 `-1/1`，不进入本轮最小八字段修复 |
| `network_length_bytes` | `int32` | 包数、字节、包长与速率聚合 | 非负网络层字节 |
| `payload_length_bytes` | `int32` 可空 | 可选被动观测 | 必须与观测掩码共同解释 |
| `transport_family` | `string` | 物理路由与审计 | 不直接拼入分类文本或共同数值视图 |
| `tcp_flags` | `int16` 可空 | 可选 TCP 观测 | 本轮不增加到共同分类信息预算 |
| `burst_id` | `int32` | 可选方向突发审计 | 本轮不作为必要窗口字段 |
| `is_first_packet` | `bool` | 序列不变量 | 每样本恰一条首包 |
| `payload_length_observed` | `bool` | 缺失掩码 | 不得以数值零替代缺失 |
| `tcp_flags_applicable` | `bool` | 适用掩码 | 与 TCP 传输族一致 |
| `truncation_mask` | `bool` | 抓包质量审计 | 当前选中包为 0 截断，但合同仍须保留 |

为了隔离“真实时间历史”而不是扩大信息预算，最小多窗口模型只应从 `packet_index`、`delta_time_us` 和 `network_length_bytes` 计算现有八个共同字段及缺失掩码：

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

`transport_family` 只用于停止梯度的物理专家适用性；其余逐包字段可保留在源表和泄漏审计中，但不在本轮悄然加入分类器或原始历史基线。

### 3.2 暂不进入本轮的 25 个 QUIC 线图像字段

39 列包表还包含以下字段组及其 `observed/applicable` 掩码：

- 长短首部形式：`quic_header_form`。
- QUIC 版本：`quic_version_u32`。
- QUIC v1 长首部类型：`quic_v1_packet_type`。
- 固定位与旋转位：`quic_fixed_bit`、`quic_spin_bit`。
- 源、目的连接标识长度：`quic_src_cid_length_bytes`、`quic_dst_cid_length_bytes`。
- 连接标识变化：`quic_cid_changed`。
- 解析器版本：`quic_parser_version`。

这些字段本机真实存在，但进入本轮会改变信息预算。若物理分支或等信息历史基线读取它们，所有受影响基线必须获得相同字段并重跑；不能再把旧 `T-A` 当作同信息对照。

## 4. 2,048/512 样本关联审计

### 4.1 覆盖与一致性

| 检查 | 结果 |
| --- | ---: |
| 检测试点行数 | 2,560 |
| 开发训练 | 2,048 |
| 开发验证 | 512 |
| 命中的逐包样本 | 2,560 |
| 命中的逐包行 | 173,196 |
| 缺失 `sample_id` | 0 |
| 额外 `sample_id` | 0 |
| 重复 `(sample_id, packet_index)` | 0 |
| `profile` 连接不一致 | 0 |
| 标签连接不一致 | 0 |
| 包数连接不一致 | 0 |

按 `profile` 的覆盖为：A 857 条、73,685 包；B 887 条、90,671 包；C 816 条、8,840 包。重新从逐包记录计算八个共同字段，与当前检测视图逐样本比较均为 0 个不一致；浮点最大绝对误差仅来自等价运算顺序，`byte_rate` 为 `5.96e-08`、`packet_rate` 为 `9.31e-10`。

推荐连接链为：

```text
检测清单 sample_id
  -> samples.parquet 的 sample_id + observation_sequence_sha256
  -> packet-observations.parquet 的 (sample_id, packet_index)
```

`profile` 只能在物化进程中定位 A/B/C 上游源或做审计，输出模型视图后必须删除。每个新序列还应绑定原 `observation_sequence_sha256`、包表 SHA-256 和确定性窗口模式版本。

### 4.2 长度与持续时间

全部 2,560 条样本的包数分位数为：最小 1、10% 为 10、25% 为 10、中位数 30、75% 为 88、90% 为 148、95% 为 259、最大 1,307。按包数阈值统计：

| 至少包数 | 样本数 | 覆盖率 |
| ---: | ---: | ---: |
| 1 | 2,560 | 100.00% |
| 2 | 2,524 | 98.59% |
| 4 | 2,502 | 97.73% |
| 8 | 2,502 | 97.73% |
| 10 | 2,502 | 97.73% |
| 16 | 1,672 | 65.31% |
| 32 | 1,230 | 48.05% |

流持续时间跨域差异很大：总体中位数 46.61 ms，75% 为 471.57 ms，95% 为 8.05 s，最大约 1,952.42 s；C 的中位数只有 1.96 ms，A/B 的中位数分别约 343.40/305.93 ms。因此统一固定 `0.1 s × 4` 会把大量 C 样本压到单一窗口，并截断长尾 B 流，不适合作为本轮 TQH-C2 主定义。

## 5. 窗口定义冻结建议

### 5.1 主定义

固定 `W=4`，按 `packet_index` 构造：

| 窗口 | 包索引范围 | 边界性质 |
| --- | --- | --- |
| `w0` | `[0, 2)` | 固定，最多 2 包 |
| `w1` | `[2, 4)` | 固定，最多 2 包 |
| `w2` | `[4, 8)` | 固定，最多 4 包 |
| `w3` | `[8, N_at_decision)` | 决策时已观测尾部 |

该定义保留完整已观测流，又避免用最终总包数反向确定早期窗口边界。禁止使用“按整条流四等分包数”作为因果主定义，因为早期边界会依赖尚未到达的最终包数；也禁止按标签、`profile` 或模型预测选择窗口。

每窗输出现有八个共同字段、八个 `*_missing`、`window_valid`、`window_packet_count` 和 `window_duration_us`。其中：

- 顺序唯一使用 `packet_index`。
- `causal_elapsed_us` 由非负 `delta_time_us` 累加，不用 `relative_time_ns` 重排。
- `iat_mean_ms` 对窗内对应 `delta_time_us` 求均值；窗口首包的间隔保留其相对前一包的已观测间隔，使四窗按包数加权后可重构整流均值。
- `packet_rate` 与 `byte_rate` 的分母使用窗内 `delta_time_us` 之和；分母为 0 时写空并置缺失掩码，不填 0。
- 空窗所有连续值写空，物化后按训练期冻结的缺失规则转数值并保留 `window_valid=0`；不得复制上一窗或把整流统计重复四次。
- 八字段跨窗必须满足包数、总字节可加重构；包长均值和到达间隔均值按有效计数加权重构。

### 5.2 时间顺序异常

现有 2,560 条试点中有 54 条流、75 个相邻位置出现 `relative_time_ns` 回退，最小回退为 `-290,000 ns`；A/B/C 分别影响 4/49/1 条流。生产提取器对负原始间隔已记录审计并把 `delta_time_us` 截为 0，所以：

- 不能宣称当前上游 `relative_time_ns` 全部非递减。
- 不能按时间戳重新排序，否则会改变冻结 `packet_index`、方向突发和序列摘要。
- 本轮用 `packet_index` 保持抓包因果顺序，用非负 `delta_time_us` 累积新时钟。
- 回退次数只写审计制品，不作为模型特征，避免暴露采集实现捷径。

## 6. 泄漏与路由审计

### 6.1 禁止进入模型的字段

下列字段只允许连接、划分或审计，不能进入多窗口特征、旁路投影、分类文本或分类数值向量：

```text
binary_label
profile
capture_group_id
allocation_group_id
parent_session_id
capture_id
interval_s
jitter_pct
selection_hash
selection_rank
split_id
source_dataset
source_path
native_label
family_label
subtype_label
```

`sample_id` 只作连接，`observation_sequence_sha256` 只作绑定。开发验证只能用于冻结后评价和早停，不能拟合归一化器、窗口阈值、不确定性尺度或协议阈值。最终测试清单继续完全不可见。

### 6.2 协议与标签捷径

当前试点的传输族与标签存在明显关联：

| 传输族 | 良性 | 恶意 |
| --- | ---: | ---: |
| TCP | 1,904 | 496 |
| ICMP | 31 | 37 |
| UDP 承载 | 14 | 78 |

双物化 `protocol.parquet` 与试点 `sample_id` 一对一连接后显示：2,400 条为 `protocol_target=TCP`，68 条为 `protocol_target=ICMP`，92 条 UDP 承载全部为 `protocol_target=UNKNOWN`；其中 78 条恶意样本具有 `V1_LONG_HEADER` 证据，14 条良性样本为 `NONE`。因此：

- 不能把 `profile=B` 当作 QUIC 身份。
- 不能把 UDP 承载自动当作普通 UDP 动力学。
- 当前静态 T-P 对 92 条 UDP 承载设置 `udp_expert_mask=1`，不符合冻结 R2 的未知协议回退合同。
- 本轮最小修复应令这 92 条样本只走共享/未知路径；没有 qlog 真值时不得启用 QUIC 动力学专家。
- 按协议或协议置信度分层的结果必须配套“共享路径全掩码”“同信息原始历史”“同划分同路由置换”和协议-标签匹配子集，不能只比较 T-P 与 T-A。

`profile × label` 也不平衡：A 为 729/128、B 为 772/115、C 为 448/368。`profile` 可以用于独立泄漏审计和负对照分层，但不能出现在模型读取的 Parquet 投影中。

## 7. 当前旁路与归一化问题

旧 `fit_state_sidecar.py` 没有读取 TQH-C2 逐包表。它把整流 `packet_rate` 与 `byte_rate` 乘 `0.1 s`，构造四个完全相同的稳态伪窗口，再由 ns-3 的固定四窗树回归器生成 18 维旁路。只读统计显示：

- 2,560 行静态旁路只有 877 个不同向量；1,922 行属于重复向量组。
- 队列估计范围约为 `0` 至 `0.06598`。
- 归一化残差范围约为 `-0.03218` 至 `0.02547`。
- 不确定性范围约为 `0.21388` 至 `1.22589`，并非严格 `[0,1]` 校准概率。
- 掩码和协议置信度为 `0/1`，量级显著大于大多数队列与残差值。
- DistilBERT 探针把这些原始值直接送入无偏置线性投影，未见训练集统计标准化。

这说明静态旁路同时存在时间信息丢失、低熵重复和尺度不均衡，足以解释其干扰分类表征的风险。多窗口修复必须重新生成派生物，不能把旧 18 维向量复制为四步序列。

归一化建议固定为：

1. 对每窗非负计数、字节、到达间隔和速率先做 `log1p`。
2. 只用 2,048 条开发训练样本拟合每字段中位数和四分位距；四分位距为 0 时硬失败或转为常量掩码，不从验证集补尺度。
3. 四个窗口共享同一组字段尺度，禁止逐样本用整流最大值归一化早期窗口，因为这会使用未来幅度。
4. 缺失与有效窗掩码不缩放；连续值先按训练统计变换，再把缺失位置置为约定的 0。
5. 物理状态、残差和不确定性分别标准化，不把 0/1 路由掩码与小量级状态直接混入同一未缩放投影。
6. 不确定性必须在物理辅助池的独立校准组上变换到 `[0,1]` 并截断；开发验证标签不能参与校准。
7. 保存字段顺序、变换类型、训练统计、适用掩码、输入样本顺序摘要和 SHA-256。

## 8. 最小新物化制品

建议在新的只读派生根中生成下列制品，不修改当前检测视图、旧 18 维旁路或双物化源表：

| 制品 | 最小内容 | 预计规模 |
| --- | --- | ---: |
| `tqhc2-pilot-causal-windows.parquet` | 10,240 行；`sample_id × 4`、窗口边界、八字段、缺失与有效掩码、训练/验证顺序 | 约 1 至 3 MiB |
| `tqhc2-pilot-causal-window-scalers.json` | 仅训练集拟合的变换和字段顺序 | 小于 100 KiB |
| `tqhc2-pilot-multiwindow-sidecar.parquet` | 2,560 条固定长度状态序列、残差、不确定性、适用掩码 | 约 1 至 4 MiB |
| `materialization-audit.json` | 源哈希、2,048/512、173,196 包、重构误差、短流与时间回退审计、禁止字段检查 | 小于 200 KiB |
| `artifact-sha256.json` | 全部非自指制品的字节数和 SHA-256 | 小于 100 KiB |

等信息量原始历史基线直接读取第一项的四窗八字段及相同掩码；物理旁路读取同一输入后产生状态序列。两者必须使用相同 `sample_id` 顺序、窗口、归一化统计和有效窗掩码。

按本机只读审计观察，读取双物化包表并过滤 2,560 条样本约需数秒。考虑正式源摘要重算、两次独立派生、重构检查和写入，预计单次物化小于 1 分钟，双物化与比较约 1 至 3 分钟；新增持久化空间预计小于 10 MiB，临时内存约 30 至 80 MiB。该数字是开发排期估计，不是论文效率结果。实现与独立审查预计另需 2 至 4 小时。无需读取约 98 GiB 原始 PCAP。

新建的数据热路径应遵守项目规则优先采用 Rust；若复用现有 PyArrow 仅做 2,560 条开发派生，必须在实施计划中明确说明这是低规模一次性试点，并保留确定性双物化与逐字段重构门禁。

## 9. 不能承诺的边界

1. TQH-C2 逐包数据只提供部署时可见的包长、时间、方向、载荷可见性、传输族和有限标志信息，不提供队列或拥塞真值。
2. 当前 2,560 条样本没有可监督的 TQH UDP 动力学目标；92 条 UDP 承载均是未知协议目标，其中 78 条只有被动 QUIC 长首部证据。
3. 本轮不能建立 QUIC 动力学专家，不能从线图像推断确认范围、丢包、在途字节、可靠往返时延、拥塞窗口或 PTO。
4. 现有 ns-3 辅助数据按固定 `0.1 s` 窗口组织，而建议的 TQH 窗口按包索引组织。旧树状态估计器不能不经重新建模和输入语义审计直接复用；窗口可物化不等于跨域状态辨识已成立。
5. 双物化 R2 包表仍位于 `.partial` 目录，开发修复可绑定哈希使用，但不能称作正式冻结发布数据。
6. 本报告没有读取任何最终测试样本，也不能据此保证 T-P 会超过 T-A；唯一可支持的结论是开发集因果历史数据已经具备且可以无 PCAP 重扫派生。

## 10. 代码与合同依据

| 路径 | 本次核对责任 |
| --- | --- |
| `thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/inputs/materialize_pilot_inputs.py` | 当前 2,048/512 稳定哈希选择、八个共同流级字段和禁止覆盖规则 |
| `thesis/experiments/llm_probe/runs/r2-physics-sidecar-pilot/experiments/tcp-udp-v0/fit_state_sidecar.py` | 四个相同伪窗口、ns-3 状态估计与旧 18 维旁路生成逻辑 |
| `thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py` | 14 列基础逐包物化和负时间间隔截断语义 |
| `thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate.py` | 14 列合同、整流聚合公式与模型字段预算 |
| `thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate_abc_fixed.py` | A/B/C 固定预算、包表过滤和稳定连接 |
| `thesis/experiments/llm_probe/src/flow_probe/r2_protocol_tqhc2.py` | 39 列双物化、QUIC 线图像字段、稳定主键与序列审计 |
| `.Codex/docs/research/protocol-adaptive-pinn/r2-data-rebuild-contract.md` | 推理可观测性、禁止字段、未知协议回退与 A/B/C/D 公平合同 |

## 11. 审计状态

- 已完成本机文件存在性、字节数和关键 SHA-256 核对。
- 已完成 Parquet 模式、行数、主键、样本覆盖、包数、时间顺序、八字段重构和协议-标签列联只读审计。
- 首次汇总命令仅在打印阶段因元组键无法序列化而退出，未写文件；修正输出键后同一只读审计完成。
- 未执行格式化、静态检查、单元测试、训练、远程同步或服务器命令。
- 除本报告外未修改任何代码、配置、数据或实验制品。
