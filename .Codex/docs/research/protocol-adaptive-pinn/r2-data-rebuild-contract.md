# R2 协议自适应数据重建合同

日期：2026-07-30  
合同状态：`review_pending`  
目标制品：`runs/data-frozen/dataset-candidate-r2-protocol-v0/`  
当前裁决：**NO-GO，本文档只冻结重建与验收要求，不授权启动数据构建或模型实验。**

## 1. 目的与不可变边界

本合同把现有共享 B0、GeNIS、TQH-C2 和 ns-3 数据整理为可审计的共同视图、协议可见视图、包序列视图和训练期物理真值视图，使 A/B/C/D 能区分协议直接信息、物理路由和标签捷径。

- 现有 `runs/data-frozen/dataset-v1/`、`runs/data-frozen/dataset-v1-shared-b0/` 及所有既有候选只读，不覆盖、不改名、不原位增列。
- 新制品使用独立协议版本 `flow_probe_r2_protocol_dataset_v0`，阶段固定为 `theory_selection`，状态固定为 `review_pending`。
- 候选主键、标签和既有分组只能通过有证据的确定性连接继承；不得按标签、协议或数据源重新抽样后悄悄改变 B0 候选。
- 模型输入不得包含地址、端口、采集配置、场景编号、文件路径、服务名、网址、密钥、明文、标签或任何可逆连接标识。
- QUIC 第一轮只作识别、校准与未知回退审计，不建立 QUIC 专属动力学专家。
- 所有不明单位、不可证明的一对一连接、跨划分重复或双构建不一致均为硬失败，不允许以填零、猜测单位或人工修表继续。

## 2. 冻结输入绑定

以下现有制品是重建起点，不是可修改目标：

| 输入 | 路径 | 已知 SHA-256 / 数量 | 合同角色 |
| --- | --- | --- | --- |
| 主记录 | `runs/data-frozen/dataset-v1/master_records.parquet` | `16458a4a191c51eefc58717e16609790b9914936a2470ef29099bdfbc70af703` | 冻结样本、来源、标签和现有分组引用 |
| 预算校验 | `runs/data-frozen/dataset-v1/manifests/budgets/budget_checksums.json` | `38883c7ef8b1e47ebd218514e71f95474cebaa8637df6b5203326802546a6c2e` | 预算身份绑定 |
| 约一万候选清单 | `runs/data-frozen/dataset-v1/manifests/budgets/train_candidate_approx10000.jsonl` | 10,000 条：GeNIS 3,973、TQH-C2 3,606、ns-3 2,421 | A/B/C/D 共同候选 |
| GeNIS 当前候选 | `runs/data-frozen/dataset-candidate-genis-v0/protocol/samples.parquet` | `2b0d8b49ef81db3a9f9338dfbabe185bab54c02512786c9f64f52718ee8c55a0` | 现有公共字段和样本引用 |
| GeNIS 验证清单 | `runs/data-frozen/dataset-candidate-genis-v0/protocol/splits/genis-family-development-validation.jsonl` | `52cce0c3b36273542e1fb05956e30876a8add1f6defd769ffa69b43bfaf19fca`；10,399 条 | 保留验证边界 |
| GeNIS 字典归档 | `raw/datasets/GeNIS-2025/0-info.zip` | `7ef636cc758586f18a5d9958e68eede9b85925610331283cce802f45542701bc` | 字段名称、类型和单位证据 |
| TQH-C2 当前候选 | `runs/data-frozen/dataset-candidate-tqhc2-abc-v0/protocol/samples.parquet` | `05cb0774f8197f07d842a21d3c22ce07c111289b7cabe6950023b689c6b51dac` | 聚合字段、序列哈希和分组引用 |
| TQH-C2 验证清单 | `runs/data-frozen/dataset-candidate-tqhc2-abc-v0/protocol/splits/tqhc2_cell_indomain-validation.jsonl` | `729860d24f6e6a400ec061077f0111d2fc8504eeb3c3700e21ab6641869d5997`；4,000 条 | 保留验证边界 |
| 历史 ns-3 序列 | `runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/{train,validation,test}.jsonl` | `d6a6ca23a985223401e1d650d619c2a50b255d2066769e2478cef72cc6239fa0`、`0bbbb4ea483867561c329c896cb4e7745a102cb90024c464654e0b7d673c8723`、`6e64d2ab290813a246ed8efcefd1bb19f1026c2de7b7904d111af67b4465ef94` | 仅作 UDP 历史对照，不得充当多协议真值 |

执行前还必须把下列原始输入写入 `source-artifacts.jsonl`：GeNIS 全部原始 CSV、TQH-C2 A/B/C 上游 `master_records.parquet` 与 `views/packet_observations.parquet`、对应 PCAP 和标签/审计清单、新 ns-3 每个配置及 CSV。每行至少含相对路径、角色、字节数和 SHA-256；任何缺项立即失败。

## 3. 发布目录与文件合同

唯一候选发布根为：

```text
runs/data-frozen/dataset-candidate-r2-protocol-v0/
├── master_records.parquet
├── views/
│   ├── common_features.parquet
│   ├── protocol_observations.parquet
│   ├── packet_observations.parquet
│   └── physics_targets.parquet
├── mappings/
│   └── source_row_map.parquet
├── splits/
│   ├── train-fit.jsonl
│   ├── calibration.jsonl
│   ├── validation.jsonl
│   ├── test.jsonl
│   ├── unseen-configuration.jsonl
│   └── open-protocol.jsonl
├── audits/
│   ├── join-audit.json
│   ├── unit-audit.json
│   ├── leakage-audit.json
│   ├── protocol-label-contingency.json
│   ├── duplicate-screen.json
│   └── deterministic-build-comparison.json
├── field-roles.yaml
├── schema.json
├── source-artifacts.jsonl
├── artifact-checksums.json
└── freeze-manifest.json
```

- Parquet 行按稳定主键排序，列顺序由 `schema.json` 固定，写入参数、压缩算法和库版本写入 `freeze-manifest.json`。
- 冻结文件不得含当前时间、绝对路径、主机名或随机生成标识；运行时间和主机信息只写发布目录外的运行回执。
- `artifact-checksums.json` 覆盖除自身外的全部发布文件；`freeze-manifest.json` 绑定源哈希、配置哈希、代码提交、模式哈希和制品哈希。
- 输出目录已存在即退出；只允许从同文件系统的 `.partial` 目录原子重命名发布。

## 4. 共同视图冻结

`views/common_features.parquet` 必须精确包含：

```text
sample_id, stable_order,
total_packets, total_bytes,
packet_length_mean, packet_length_min, packet_length_max,
iat_mean_ms, packet_rate, byte_rate,
total_packets_missing, total_bytes_missing,
packet_length_mean_missing, packet_length_min_missing,
packet_length_max_missing, iat_mean_ms_missing,
packet_rate_missing, byte_rate_missing
```

| 规范字段 | 规范单位 | GeNIS 来源 | TQH-C2 来源 | 新 ns-3 来源 |
| --- | --- | --- | --- | --- |
| `total_packets` | 包 | `TotPkts` | `packet_count` | 四窗口 `public_total_packets` 之和 |
| `total_bytes` | 网络层字节 | `TotBytes`，须先证明“事务字节”与规范层级一致 | `network_bytes_total` | 四窗口 `public_total_l3_bytes` 之和 |
| `packet_length_mean` | 网络层字节/包 | `TotBytes / TotPkts` | `network_bytes_mean` | 总网络层字节/总包数 |
| `packet_length_min` | 网络层字节 | `min(sMinPktSz,dMinPktSz)` | `network_bytes_min` | 四窗口可见包长最小值 |
| `packet_length_max` | 网络层字节 | `max(sMaxPktSz,dMaxPktSz)` | `network_bytes_max` | 四窗口可见包长最大值 |
| `iat_mean_ms` | 毫秒 | `SIntPkt`、`DIntPkt` 按方向包数加权 | `delta_time_us_mean / 1000` | 四窗口可见到达间隔按有效间隔数加权 |
| `packet_rate` | 包/秒 | `Rate` | `packet_count / flow_duration_s` | 总包数/四窗口跨度 |
| `byte_rate` | 字节/秒 | `Load / 8` | `network_bytes_total / flow_duration_s` | 总网络层字节/四窗口跨度 |

硬门禁：

- 既有 `shared_b0_view_v1` 的字段顺序和换算是兼容起点；R2 不得改变 A/B/C/D 的共同输入。
- GeNIS 官方字典把 `TotBytes` 称为“事务字节”，而 TQH-C2 与 ns-3 明确使用网络层字节。重建前必须从官方提取器定义或原始包复算证明层级等价；不能证明则 `unit-audit.json` 记为失败并停止发布。
- 分母为零、无有效间隔或来源确实不提供的值写 `null`，对应 `*_missing=1`；不得用数值零表示缺失。
- 缺失掩码的含义固定为“来源中不可得或不可定义”，不能编码数据源或标签规则。

## 5. 协议可见视图

`views/protocol_observations.parquet` 以 `sample_id` 为唯一主键，包含规范化数值、类别编码和逐字段缺失/适用掩码。字段角色只能是 `router_or_physics_input`、`audit_only` 或 `blocked_pending_semantics`。

### 5.1 共同协议身份

| 字段 | 类型/取值 | 来源与规则 |
| --- | --- | --- |
| `transport_family` | `TCP/UDP/ICMP/SCTP/DCCP/ESP/OTHER/UNKNOWN` | GeNIS `Proto`；TQH 包传输族一致性；ns-3 配置真值 |
| `transport_family_observed` | 布尔 | 原始字段或包解析是否直接可见 |
| `quic_evidence_class` | `NONE/V1_LONG_HEADER/CONTEXT_BOUND_SHORT_HEADER/AMBIGUOUS` | 只由可见 QUIC 线图像和同连接上下文产生 |
| `protocol_target` | 同上并含 `QUIC` | 训练期协议真值，只能进入协议识别损失和评价，不得进入攻击分类输入 |
| `protocol_confidence` | `[0,1]` | 校准集拟合后的输出；不是原始字段，不得由攻击分类损失更新 |

GeNIS `Proto` 和 ns-3 配置可形成硬传输族身份。TQH 的 UDP 只能说明 UDP 承载，不能自动改写为 QUIC；`profile=B` 永远是 `split_metadata`，禁止参与协议识别。

### 5.2 GeNIS 扩展字段

| 规范字段 | 原字段 | 单位与处理 | 第一轮角色 |
| --- | --- | --- | --- |
| `loss_packets` | `Loss` | 包；保留非负整数，原始缺失显式掩码 | 路由/物理输入，B/D 同时可见 |
| `retrans_packets` | `Retrans` | 包；仅 TCP 解释为 TCP 重传，其他协议保留值但适用掩码为 0 | TCP 物理输入，B/D 同时可见 |
| `tcp_rtt_ms` | `TcpRtt` | 官方字典未声明单位；配置必须给出一手单位证据和换算，否则停止 | `blocked_pending_semantics`，通过单位门禁后转物理输入 |
| `src_window_bytes` | `SrcWin` | 官方字典未声明单位/缩放语义；不得默认等于有效拥塞窗口 | `blocked_pending_semantics` |
| `dst_window_bytes` | `DstWin` | 同上 | `blocked_pending_semantics` |

`SrcWin`/`DstWin` 是通告接收窗口，不等于拥塞窗口 `cwnd`。即使单位门禁通过，也只能作为可见辅助量，不能作为 ns-3 `cwnd` 真值替代品。

### 5.3 TQH-C2 现有聚合字段

第一轮允许复用以下现有确定性字段：`tcp_packet_fraction`、`udp_packet_fraction`、`icmp_packet_fraction`、`other_transport_packet_fraction`、`tcp_syn_packet_fraction`、`tcp_ack_packet_fraction`、`tcp_fin_packet_fraction`、`tcp_rst_packet_fraction`、`tcp_psh_packet_fraction`、`payload_observed_fraction`、`tcp_flags_applicable_fraction` 和 `truncation_fraction`。

- 四种传输族比例必须与包级 `transport_family` 重算完全一致。
- TCP 标志比例只在 TCP 适用掩码为 1 时解释；非 TCP 样本不得用填零伪装成观测值。
- 若 C/D 物理分支读取其中任一字段，B/D 分类器必须获得同一字段和同一掩码。

### 5.4 QUIC 可见字段与禁用解释

TQH PCAP 新增解析只允许物化：`quic_header_form`、`quic_version_u32`、`quic_v1_packet_type`、`quic_fixed_bit`、`quic_spin_bit`、源/目的连接标识长度、连接标识是否变化，以及各自的 `observed/applicable/parser_version` 字段。原始连接标识值不得写入任何发布视图。

- RFC 8999 只保证有限的版本无关线图像；版本字段非零后，其余解释必须绑定具体 QUIC 版本。
- RFC 9000 的旋转位是可选信号，端点可随机禁用；不得把单个旋转位值当成 RTT 真值或硬协议身份。
- RFC 9287 允许固定位随机化；固定位只能作弱观测，不能作为硬识别规则。
- RFC 9001 只允许把 Initial 的可公开派生保护边界用于解析验证；密钥、解密内容、服务器名称指示、证书和网址均禁止进入模型输入。
- RFC 9312 明确不支持从当前线图像被动测量丢包，并指出五元组或连接标识不稳定等价于完整连接。不得由 PCAP 补造丢包、确认范围、在途字节或迁移后连接真值。
- 第一轮所有 QUIC、无法识别的 UDP、未知版本和低置信样本均关闭 TCP/UDP 专属专家，只保留共享守恒。

## 6. 包序列视图

`views/packet_observations.parquet` 仅物化推理时可见字段，TQH-C2 先精确复用已有模式：

| 字段 | 类型 | 不变量 |
| --- | --- | --- |
| `sample_id` | 字符串 | 必须存在于主记录 |
| `packet_index` | `int32` | 每个样本从 0 连续递增，不重复、不回退 |
| `relative_time_ns` | `int64` | 非负且不回退 |
| `delta_time_us` | `int64` | 非负；首包规则写入模式 |
| `direction` | `int8` | 只能为 `-1` 或 `1` |
| `network_length_bytes` | `int32` | 非负网络层长度 |
| `payload_length_bytes` | 可空 `int32` | 仅在 `payload_length_observed=1` 时非空 |
| `transport_family` | 字符串 | 只允许受支持枚举 |
| `tcp_flags` | 可空 `int16` | 0 至 `0x1FF`；只在 TCP 适用 |
| `burst_id` | `int32` | 非负、确定性分段 |
| `is_first_packet` | 布尔 | 每个样本恰一条首包 |
| `payload_length_observed` | 布尔 | 与载荷长度空值一致 |
| `tcp_flags_applicable` | 布尔 | 与 `transport_family=TCP` 一致 |
| `truncation_mask` | 布尔 | 明确记录抓包截断 |

QUIC 新字段附加在该表，但必须遵守第 5.4 节。每个样本按上述字段的规范 JSON 表示计算 `observation_sequence_sha256`；聚合字段必须从该序列重算，不得同时信任两套来源。

GeNIS 没有包序列时不伪造序列；`master_records.parquet` 写 `packet_view_available=0`。模型若使用序列编码，A/B/C/D 必须具有相同的可用性掩码和同维度无协议统一分支，防止把“是否有序列”直接当作数据源标签。

## 7. ns-3 多协议物理真值

当前 `domain_randomized_queue_scenario.cc` 已提供 TCP/UDP 开关、`0.1 s` 窗口、共同公开观测和队列守恒列，可复用为脚手架；现有已发布四窗口数据仍是 UDP-only，且新脚手架尚未提供 TCP 内部状态真值。

### 7.1 固定实验矩阵

- 传输协议恰为 TCP 与普通 UDP；同一负载、拓扑、队列、容量、丢包、到达过程和种子形成配对配置。
- 每次运行 12 秒、窗口 `0.1 s`；序列长度 4，完整运行组不得跨划分。
- TCP 拥塞控制实现必须写出 ns-3 类型和版本。第一轮只允许一个预注册实现；不同实现不得混写为同一 `TCP` 状态。
- TCP/UDP 在良性/攻击、恒定/突发、队列模型和负载区间上配平；协议不得由攻击标签或配置编号唯一决定。
- 配置清单必须在生成 CSV 前冻结并哈希；任何失败配置保留失败回执，不得仅删除难例。

### 7.2 每窗公开观测

新 ns-3 必须直接写出与共同视图同语义的 `public_total_packets`、`public_total_l3_bytes`、包长均值/最小/最大、`public_iat_mean_ms`、`public_packet_rate_pps` 和 `public_byte_rate_Bps`。模型输入只能读取这些公开列及第 5 节允许的协议可见列。

### 7.3 每窗训练期真值

`views/physics_targets.parquet` 至少包含：

- 共享队列：窗起/窗末队列的网络层字节和包数、进入队列、入队、出队、入队前丢弃、出队后丢弃、下游错误丢失、接收端收到量、容量积分及包/字节守恒残差。
- TCP：`cwnd_bytes`、`bytes_in_flight`、平滑或采样 RTT、已确认字节/包、重传字节/包、发送字节/包；每项写出 trace source、聚合规则和适用掩码。无法从当前 ns-3 版本稳定追踪的字段应从模式中删除，不得用估算值充真值。
- UDP：应用计划发送字节/包、实际发送字节/包、发送速率和突发开关状态；UDP 不得伪造 `cwnd`、确认或重传状态。
- 环境参数、攻击模式、协议身份和队列配置只作训练期真值、分组或审计，不得进入攻击分类输入。

共享守恒同时以包和网络层字节复核，二者不得混用：

$$
q_{t+1}=q_t+a_t-s_t-d_t.
$$

每个窗口的精确整数残差必须为 0；非零即拒绝该运行及其所有四窗口序列。

## 8. 连接、分组与划分

### 8.1 一对一连接

- `source_row_map.parquet` 只保存新旧 `sample_id`、源制品 SHA-256、不可逆行引用、连接状态和记录哈希，不保存地址、端口或原始连接标识。
- GeNIS 必须由冻结样本引用回到同一官方 CSV 行；新旧标签、来源、分组和八个公共字段逐行复算一致。重复、缺失或多对一命中均停止。
- TQH 必须以 `sample_id` 和 `observation_sequence_sha256` 同时绑定包序列；任何序列哈希变化必须解释为明确的新解析版本，不能静默覆盖。
- ns-3 以配置哈希、种子、运行号和窗口序号形成主键；同一完整运行的全部窗口只属于一个划分。

### 8.2 分组切分

- GeNIS：至少以现有 `group_id` 所指源文件/采集单元整体分组；同一采集单元不得跨 `train-fit/calibration/validation/test`。
- TQH-C2：以 `capture_group_id` 和父会话整体分组；`profile`、`interval_s`、`jitter_pct` 只作切分和审计。
- ns-3：以完整配置配对组和种子分组；同一负载条件下的 TCP/UDP 配对进入同一划分。
- 保留现有验证/测试边界；从原训练组按冻结哈希算法划出独立 `calibration`，不得查看标签后调整。
- 另建 `unseen-configuration` 与 `open-protocol`；未知协议、未知 QUIC 版本和低置信样本不得混入校准拟合。

### 8.3 泄漏与捷径门禁

- 对 `protocol × binary_label × source/profile/split` 生成完整列联表；任一主评价单元缺协议内正例或负例时，该单元不得支撑检测收益结论。
- TQH 必做协议字段置换、协议字段全掩码、去握手前缀、留一 `profile`、协议—标签匹配子集和仅地址/端口审计基线；地址和端口基线只能在隔离审计进程中运行，结果保留，字段不得发布。
- QUIC 协议标签可由受控解密或实验配置产生，但只作训练期真值；密钥和解密派生的服务/网址/响应标签不得进入输入。
- 对所有模型输入字段执行禁止词、唯一值、标签互信息和数据源可预测性审计；高数据源可预测性不自动删除字段，但必须触发跨源与留配置评价。
- 对包序列哈希、共同特征哈希和源记录哈希执行跨划分重复检查；有标签冲突或非独立重复即停止。

## 9. 协议置信度校准

- 协议识别器只用 `train-fit` 的协议真值训练，温度缩放只在独立 `calibration` 组拟合一个或预注册的分层温度；测试组永不参与选择。
- 校准输出经 `stopgrad` 进入物理软强度；攻击分类损失对识别器与校准参数的梯度必须精确为 0。
- 同时报告准确率、宏平均 F1、负对数似然、Brier 分数、期望校准误差、覆盖率—风险曲线和按来源/协议分层结果。
- Guo 2017 的温度缩放假定校准与测试分布一致；Ovadia 2019 表明分布漂移下事后校准可失效。因此必须分别在同分布、留采集配置、跨源和开放协议上评价，不得用同分布期望校准误差替代未知拒识。
- 低于预注册阈值、预测分歧过大或开放集分数越界的样本固定进入 `UNKNOWN`；不得按最大概率强制激活专家。

## 10. A/B/C/D 数据视图与公平性

| 组别 | 分类头可见 | 物理分支可见 | 训练期真值 |
| --- | --- | --- | --- |
| A | `x_common` | 无协议统一残差分支 | 与 C 相同的 ns-3 真值预算 |
| B | `x_common + x_proto` | 无协议统一残差分支 | 与 D 相同 |
| C | `x_common` | `x_proto`、固定硬掩码、停止梯度的校准置信度 | 与 A 相同 |
| D | `x_common + x_proto` | 与 C 完全相同 | 与 B 相同 |

- `x_proto` 是 C/D 物理分支实际读取的全部推理可见字段及掩码；B/D 必须获得逐位相同向量。
- A/B 的统一残差网络与 C/D 的 TCP、UDP 专家总参数量匹配；任务头、候选、划分、种子、步数和停止规则一致。
- 所有组使用同一个 `sample_id` 顺序哈希、共同特征哈希、标签哈希和划分哈希；任一不一致则比较无效。
- 新字段或新样本会改变所有受影响基线的数据合同，必须重跑 Qwen、HGB、XGBoost、DistilBERT、现有统一物理基线及 A/B/C/D；旧 B0 分数只作历史参照。

## 11. 双构建与发布算法

实现后固定两个入口：

```bash
python -m flow_probe.r2_protocol_rebuild \
  --config configs/r2_protocol_data_v1.yaml \
  --output runs/data-frozen/dataset-candidate-r2-protocol-v0.build-a.partial

python -m flow_probe.r2_protocol_rebuild \
  --config configs/r2_protocol_data_v1.yaml \
  --output runs/data-frozen/dataset-candidate-r2-protocol-v0.build-b.partial

python -m flow_probe.r2_protocol_validate \
  --left runs/data-frozen/dataset-candidate-r2-protocol-v0.build-a.partial \
  --right runs/data-frozen/dataset-candidate-r2-protocol-v0.build-b.partial
```

上述模块与配置当前尚未实现，**不得执行这些示例命令冒充已完成重建**。实现必须遵循：

1. 启动时核验全部源 SHA-256、配置模式、输出不存在和可用磁盘。
2. A/B 两次构建使用同一源、配置、代码提交和分组密钥标识，但独立进程和空输出目录。
3. 两次构建的行数、列顺序、数据类型、主键、样本顺序、划分、每个非自指文件 SHA-256 和目录 Merkle 摘要必须完全相同。
4. `deterministic-build-comparison.json` 记录逐文件比较；任何差异均停止，不选取“看起来正确”的一份。
5. 全部门禁通过后，只把 build-a 原子重命名为唯一发布根；build-b 的处置留到人工复核后，不得在构建脚本中无条件删除。

## 12. 必须自动化的验收门禁

### P0：发布前全部通过

- 源哈希、代码提交和配置哈希完整，旧制品未变。
- 10,000 条共同候选及各验证清单与冻结身份绑定；任何增删有独立变更清单和用户批准。
- 所有表主键唯一、连接基数符合合同、标签与分组不变、包索引连续。
- 八个共同字段的名称、单位、语义和换算均通过；GeNIS 事务字节层级、`TcpRtt` 和窗口单位无未决项。
- TQH 包聚合重算、序列哈希、协议比例和截断掩码一致。
- 新 ns-3 同时具有 TCP/UDP 配对运行、精确队列守恒和至少一个可验证 TCP 内部状态；UDP 不携带伪 TCP 状态。
- `profile`、地址、端口、服务、网址、密钥、明文、配置编号和攻击标签不在任何模型视图。
- 协议识别校准集独立，开放协议拒识存在，分类梯度到路由器/校准器为 0。
- A/B/C/D 的输入哈希、候选、划分、容量与训练预算合同一致。
- 双构建所有发布文件字节一致，原子发布路径不存在。

### P1：实验启动前通过

- 协议—标签匹配子集、留采集配置、去握手和字段置换负对照均可生成且非空。
- 物理状态真值在 TCP/UDP、良性/攻击和各划分均有充分覆盖；具体最小量在看到结果前写入配置。
- 校准、开放集、状态误差和检测指标的阈值、种子数、置信区间及非劣界已预注册。
- Qwen、HGB、XGBoost、DistilBERT 和统一物理基线均能读取新冻结视图。

## 13. 立即停止条件

出现任一项，重建或实验保持 **NO-GO**：

- GeNIS 原始字段无法与冻结样本一对一回接，或关键字段单位仍靠猜测。
- GeNIS `TotBytes` 与网络层字节语义无法统一，却仍合并为同一共同字段。
- TQH 只能用 `profile` 区分 QUIC，或协议与标签没有共同支持集。
- 新 ns-3 没有 TCP 内部状态真值、仍只有 UDP，或 TCP/UDP 配置不配对。
- QUIC 被动抓包被错误解释为丢包、确认范围、在途字节或可靠 RTT 真值。
- 任一禁止字段进入模型视图，或分类损失能更新路由器/协议校准器。
- 双构建哈希不一致、发布目录已存在、旧冻结制品发生变化。

## 14. 当前执行裁决

截至 2026-07-30：

- 共同 B0 的 8 字段、列顺序、既有输入路径和哈希已经核准。
- TQH-C2 包级顺序字段、聚合算法、序列哈希和敏感字段隔离已有可复用实现。
- GeNIS 官方字段存在性已核准，但 R2 扩展字段尚未回接；`TcpRtt`、`SrcWin`、`DstWin` 单位/语义仍未闭合，`TotBytes` 的跨源层级一致性仍需证明。
- ns-3 已有 TCP/UDP 配置脚手架和共享队列真值列，但尚无经验证的新制品，也缺 TCP 内部状态追踪。
- QUIC 现行 RFC 已闭合“可见但不稳定、不能被动恢复关键隐藏状态”的边界；第一轮继续未知回退。

因此数据合同已冻结为可实现规范，但所有 P0 门禁尚未通过，**禁止启动 R2 主实验，最终状态为 NO-GO**。
