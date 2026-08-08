# R1 本地全文语料筛查清单

## 筛查口径

- 盘点范围：`raw/papers/pinn/` 下全部 PDF，包括已有 R2、R3 子目录与本轮目标目录。
- 当前盘点结果：110 个 PDF 文件，按 SHA-256 为 97 份唯一全文；13 组各含一个字节级重复副本。初筛后由并行协议任务新增的 7 份唯一材料和扩展批次累计 10 个规范副本也已补登记。
- 状态含义：`核心纳入` 表示首轮核心论文已完成 R1 逐页证据与 Zotero 回链；`扩展纳入` 表示扩展候选已按同一门槛完成全文复核；`扩展候选` 表示可能新增承重机制或失败条件，必须严格每批两篇复核；`停止核验候选` 表示一级原始工作，但预期只确认既有边界；`排除` 表示题名、全文首屏或已有逐页笔记显示不改变 R1 证据合同；`重复` 表示与规范路径文件 SHA-256 相同。
- 综述只用于发现线索，不支撑最终公式、实验数字或裁决。已有 R2、R3 逐页笔记可用于初筛，但 R1 的承重结论仍回到对应 PDF。

## 根目录语料

| PDF | 状态 | 筛查理由 |
| --- | --- | --- |
| `raw/papers/pinn/1711.10561.pdf` | 停止核验候选 | 标准连续/离散时间 PINN 原始工作；用于确认完整坐标、已知方程和共享梯度是基线前提，预期不新增闭合或尺度门。 |
| `raw/papers/pinn/1711.10566.pdf` | 停止核验候选 | 标准方程发现原始工作；有限维参数发现依赖时空观测，预期只确认“参数辨识不等于自由闭合辨识”。 |
| `raw/papers/pinn/2001.04536-PINN梯度病态.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2021-Wang-Gradient-Pathologies.pdf` SHA-256 完全一致；原件保留。 |
| `raw/papers/pinn/2007.14527-PINN神经切线核.pdf` | 排除 | 核谱收敛分析与梯度病态同属优化层；对 Transformer 与离散闭合不可直接外推，优先核验更直接的梯度流论文。 |
| `raw/papers/pinn/2016-Lee-非对称多任务学习.pdf` | 排除 | 通用多任务迁移，不定义尺度、守恒、队列状态或闭合可辨识性。 |
| `raw/papers/pinn/2018-Lee-深度非对称多任务特征学习.pdf` | 排除 | 通用共享/私有表示，不提供 R1 的时间控制体和状态真值合同。 |
| `raw/papers/pinn/2021-KarimiMahabadi-HyperFormer.pdf` | 排除 | 任务条件超网络适配器，与物理尺度选择和不可观测通量无直接对应。 |
| `raw/papers/pinn/2021-Lewis-BASE-Layers.pdf` | 排除 | 稀疏专家负载平衡，不保证专家具有物理尺度或队列语义。 |
| `raw/papers/pinn/2021-Pfeiffer-AdapterFusion.pdf` | 排除 | 冻结适配器组合属于任务复用，不提供状态闭合或跨尺度守恒。 |
| `raw/papers/pinn/2022-Alayrac-Flamingo.pdf` | 排除 | 零初始化条件注入只支持前向不变性，不支持 R1 可辨识性。 |
| `raw/papers/pinn/2022-Dai-StableMoE.pdf` | 排除 | 稳定路由解决专家切换，不决定物理尺度是否可观测。 |
| `raw/papers/pinn/2022-Fedus-Switch-Transformer.pdf` | 排除 | 稀疏语言模型路由与容量因子不是网络队列容量或时间尺度证据。 |
| `raw/papers/pinn/2022-Hu-APINN.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2023-Hu-APINN.pdf` SHA-256 完全一致；原件保留。 |
| `raw/papers/pinn/2023-Yan-辅助任务PINN.pdf` | 排除 | 比较共享/专家多任务结构，但不提供时间窗重聚合或未知通量真值；结构证据已由主线基线覆盖。 |
| `raw/papers/pinn/2023-Zhang-ControlNet.pdf` | 排除 | 条件旁路的恒等初始化不解决队列状态与闭合项零空间。 |
| `raw/papers/pinn/2023-Zhang-LLaMA-Adapter.pdf` | 排除 | 低秩条件注入与 R1 物理变量、尺度和真值合同无直接关系。 |
| `raw/papers/pinn/2023-Zhao-Prototype-HyperAdapter.pdf` | 排除 | 样本原型生成适配器，不是由可见时间历史选择守恒尺度。 |
| `raw/papers/pinn/2024-Agiza-MTLoRA.pdf` | 排除 | 多任务低秩参数隔离不提供闭合可辨识性。 |
| `raw/papers/pinn/2024-Chalapathi-物理硬约束混合专家.pdf` | 排除 | 物理子域专家由已知域职责划分，不是缺测历史驱动的时间尺度门；与 APINN/GatedPINN 证据重复。 |
| `raw/papers/pinn/2024-Dai-DeepSeekMoE.pdf` | 排除 | 通用稀疏专家架构，不保证物理职责与状态真值。 |
| `raw/papers/pinn/2024-Kong-LoRA-Switch.pdf` | 排除 | 动态适配器切换关注解码效率，不涉及物理控制体。 |
| `raw/papers/pinn/2024-Li-MixLoRA.pdf` | 排除 | 词元级低秩专家混合没有守恒或可辨识合同。 |
| `raw/papers/pinn/2024-Lv-HyperLoRA.pdf` | 排除 | 任务说明条件化参数生成不能作为推理可见物理历史。 |
| `raw/papers/pinn/2024-Ma-MoDULA.pdf` | 排除 | 通用/领域 LoRA 分阶段训练不定义状态闭合。 |
| `raw/papers/pinn/2024-Panda-稠密反向传播路由.pdf` | 排除 | 只改善稀疏路由梯度，不验证尺度语义和队列状态。 |
| `raw/papers/pinn/2024-Wang-LoRA-Flow.pdf` | 排除 | 逐词元技能融合可能产生格式捷径，不能支撑物理尺度选择。 |
| `raw/papers/pinn/2024-Wu-MoLE.pdf` | 排除 | 层级低秩专家组合与 R1 闭合/守恒责任不匹配。 |
| `raw/papers/pinn/2105.00862-数据与物理帕累托前沿.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2023-Rohrhofer-Apparent-Pareto-Front.pdf` SHA-256 完全一致；原件保留。 |
| `raw/papers/pinn/2109.01050-PINN失败模式.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2021-Krishnapriyan-PINN-Failure-Modes.pdf` SHA-256 完全一致；原件保留。 |
| `raw/papers/pinn/2408.11104-ConFIG.pdf` | 排除 | 多目标共同下降方向是优化器方案，不修复不可观测状态的结构多解；梯度责任由 2001.04536 与帕累托论文优先覆盖。 |
| `raw/papers/pinn/2410.13228.pdf` | 排除 | PINN/PIKAN 综述，只作线索，不作为最终一级证据。 |
| `raw/papers/pinn/2501.06572.pdf` | 排除 | 进化优化综述/观点文，超出约一万条、200 步最小路线且无 R1 队列证据。 |
| `raw/papers/pinn/MDPI-ApplSci-2025-15-8092-PINN综述.pdf` | 排除 | 综述，不支撑承重公式或实证。 |
| `raw/papers/pinn/algorithms-15-00447-交通网络PINN.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2022-Usama-Traffic-Network-PINN.pdf` SHA-256 完全一致；原件保留。 |
| `raw/papers/pinn/paper_0dd9fd2db26952889e10293d9209c0bf.pdf` | 排除 | 科学机器学习/PINN 综述，只用于线索发现。 |
| `raw/papers/pinn/paper_390db51220335dc4b705f12f777ef9eb.pdf` | 排除 | 2025 年 PDE PINN 综述，不作为一级承重证据。 |
| `raw/papers/pinn/paper_520fcb7d7e085e3081e0ab5f0c5b4dd5.pdf` | 排除 | 通用 PINN 技术、应用与挑战综述，不替代原始论文。 |
| `raw/papers/pinn/paper_b002d83866255ef3bd48ae3819cf2520.pdf` | 重复 | 与 `raw/papers/pinn/1711.10561.pdf` SHA-256 完全一致。 |
| `raw/papers/pinn/paper_ced7ef2c6ebf5b388931d1671a9e9520.pdf` | 排除 | 流体 PINN 综述；HFM 与显式闭合原始论文已提供更直接证据。 |
| `raw/papers/pinn/wang24b-柯西问题PINN困难性.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2024-Wang-Cauchy-PINN-Difficulty.pdf` SHA-256 完全一致；原件保留。 |
| `raw/papers/pinn/基于物理信息的神经网络：最新进展与展望.pdf` | 排除 | 中文综述，只用于术语与线索，不支撑最终裁决。 |

## 本轮核心目录

| PDF | 状态 | 筛查理由 |
| --- | --- | --- |
| `raw/papers/pinn/multiscale-observability-closure/2008-Liebeherr-Bandwidth-Estimation.pdf` | 扩展纳入 | 多时间尺度服务曲线反演至少需要成对累计到达/离开轨迹或受控主动探测；低负载欠激励、高负载扰动及非线性 FIFO 共同限定可辨识性。 |
| `raw/papers/pinn/multiscale-observability-closure/2010-Habib-Queue-Inferencing.pdf` | 核心纳入 | 强观测条件下输出端口忙期队列条件期望反演及其泊松边界。 |
| `raw/papers/pinn/multiscale-observability-closure/2012-Bouillard-Hidden-Anomaly.pdf` | 扩展纳入 | 仅有有序消息到达时间时可用逐层仿射包络检测短期至长期到达异常，但不得解释为队列、服务或容量恢复，且周期流可能不收敛。 |
| `raw/papers/pinn/multiscale-observability-closure/2020-Stiller-GatedPINN.pdf` | 扩展纳入 | 坐标条件 Top-1 路由主要减少条件计算；总损失更低但解析状态误差略差，不能把门图或低残差当作尺度真值。 |
| `raw/papers/pinn/multiscale-observability-closure/2020-Raissi-HFM.pdf` | 核心纳入 | 已知方程和充分标量覆盖下的部分可观测隐状态恢复及零空间。 |
| `raw/papers/pinn/multiscale-observability-closure/2021-Krishnapriyan-PINN-Failure-Modes.pdf` | 扩展纳入 | 已知方程系数课程热启动和固定短时间推进可缓解困难损失景观，但都不是观测驱动尺度选择，也没有未知闭合。 |
| `raw/papers/pinn/multiscale-observability-closure/2021-Wang-Gradient-Pathologies.pdf` | 扩展纳入 | 梯度统计退火可缓解损失幅值失衡，但不解决梯度方向冲突；速度—压力算例证明结构性硬约束不能由优化重加权替代。 |
| `raw/papers/pinn/multiscale-observability-closure/2021-Yang-BPINN.pdf` | 核心纳入 | 已知噪声模型下的后验不确定性与错误近似后验反证。 |
| `raw/papers/pinn/multiscale-observability-closure/2022-Patel-cvPINN.pdf` | 核心纳入 | 控制体弱守恒、结构化未知通量与自由闭合退化解。 |
| `raw/papers/pinn/multiscale-observability-closure/2022-Taghizadeh-Explicit-Closure.pdf` | 核心纳入 | 直接数值真值监督的显式无量纲闭合及尺度分离边界。 |
| `raw/papers/pinn/multiscale-observability-closure/2022-Usama-Traffic-Network-PINN.pdf` | 扩展纳入 | 已知拓扑上的逐链接状态网络与交界通量守恒提供可微耦合证据；离散平均观测与点式守恒冲突构成新增失败边界。 |
| `raw/papers/pinn/multiscale-observability-closure/2023-McClenny-SA-PINN.pdf` | 核心纳入 | 逐点残差权重与缺测可靠性、尺度选择的概念边界。 |
| `raw/papers/pinn/multiscale-observability-closure/2023-Hu-APINN.pdf` | 扩展纳入 | 门由人工 XPINN/MPINN 分区预训练且明显受初始化捕获；专家分解非唯一、更多子域可更差，不支持自由时间尺度发现。 |
| `raw/papers/pinn/multiscale-observability-closure/2023-Perez-Adaptive-BPINN.pdf` | 核心纳入 | 多任务梯度尺度平衡与字段缺测不确定性的边界。 |
| `raw/papers/pinn/multiscale-observability-closure/2023-Rohrhofer-Apparent-Pareto-Front.pdf` | 扩展纳入 | 域长度、特征时间和方程系数会移动训练可达前沿；无量纲化是多窗口比较前提，但不能决定理想权重或闭合状态。 |
| `raw/papers/pinn/multiscale-observability-closure/2024-Cen-DFVM.pdf` | 核心纳入 | 固定控制体局部弱形式、自适应采样与自适应尺度的边界。 |
| `raw/papers/pinn/multiscale-observability-closure/2024-Dolean-Multilevel-FBPINN.pdf` | 核心纳入 | 固定多层域分解的粗细信息交换及学习窗口缺口。 |
| `raw/papers/pinn/multiscale-observability-closure/2024-Wang-Cauchy-PINN-Difficulty.pdf` | 扩展纳入 | 紧致域零残差和零初值误差仍可任意偏离真实柯西解；缺失边界、域外信息、正则性和间断表示能力构成结构否决门。 |
| `raw/papers/pinn/multiscale-observability-closure/2025-Du-PRED.pdf` | 扩展纳入 | 基于 RTT 的快并发稳定器与慢 A/B 队列调节器形成受限双时间尺度白盒控制，但依赖端口队列、五元组、容量、RTT 和协议反馈。 |
| `raw/papers/pinn/multiscale-observability-closure/2025-Raghunathan-QuASI.pdf` | 核心纳入 | 粗粒度计数下相容轨迹集合、存在性查询和唯一真值缺口。 |

## 网络演算与不确定性子目录

| PDF | 状态 | 筛查理由 |
| --- | --- | --- |
| `raw/papers/pinn/network-calculus-boundary/2002-Burchard-Statistical-Service-Guarantees.pdf` | 排除 | 统计有效服务曲线给违约概率下界，但不从 R1 冻结字段反演服务；R3 已逐页核验。 |
| `raw/papers/pinn/network-calculus-boundary/2008-Liebeherr-System-Theoretic-Bandwidth-Estimation.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2008-Liebeherr-Bandwidth-Estimation.pdf` SHA-256 完全一致；原件保留。 |
| `raw/papers/pinn/network-calculus-boundary/2010-Luebben-Foundation-Stochastic-Bandwidth.pdf` | 排除 | 多档主动探测与重复测量不在当前三源合同；可辨识结论由 Liebeherr 更直接覆盖。 |
| `raw/papers/pinn/network-calculus-boundary/2012-Bouillard-Hidden-Anomaly-Network-Calculus.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2012-Bouillard-Hidden-Anomaly.pdf` SHA-256 完全一致；原件保留。 |
| `raw/papers/pinn/network-calculus-boundary/2014-Luebben-Stochastic-Bandwidth-Random-Service.pdf` | 排除 | 随机服务分位数仍要求主动测量，重复 2008/2010 的观测门槛。 |
| `raw/papers/pinn/network-calculus-boundary/2017-Cuturi-Soft-DTW.pdf` | 排除 | 可微软最小动态规划的温度近似属于 R3 数值实现，不证明 R1 闭合可辨识。 |
| `raw/papers/pinn/network-calculus-boundary/2018-Mensch-Differentiable-Dynamic-Programming.pdf` | 排除 | 强凸平滑递推给可微近似界，但不是队列真值或尺度选择证据。 |
| `raw/papers/pinn/network-calculus-boundary/2019-Geyer-DeepTMA.pdf` | 排除 | 学习合法网络演算操作选择，依赖完整拓扑与流量矩阵；共享 B0 不具备。 |
| `raw/papers/pinn/network-calculus-boundary/2019-Geyer-Robustness-DeepTMA.pdf` | 排除 | 同建模域规模外推不等于跨 GeNIS/TQH-C2/ns-3 可迁移性。 |
| `raw/papers/pinn/network-calculus-boundary/2021-Gibbs-Adaptive-Conformal-Shift.pdf` | 排除 | 分布漂移下长期错覆盖属于校准层，不修复闭合状态结构多解。 |
| `raw/papers/pinn/network-calculus-boundary/2021-Jacobs-Network-Calculus-Anomaly-Detection.pdf` | 排除 | 网络演算特征连接异常检测，但实验参数预设且不学习不可观测队列。 |
| `raw/papers/pinn/network-calculus-boundary/2021-Stankeviciute-Conformal-Time-Series.pdf` | 排除 | 时间序列共形分区原则可作为评价纪律，但当前公开数据没有同一控制体序列。 |
| `raw/papers/pinn/network-calculus-boundary/2023-Luebben-TAILING-Delay-Quantiles.pdf` | 排除 | 需要到达/离开或往返时延历史，冻结共享 B0 不满足输入合同。 |
| `raw/papers/pinn/network-calculus-boundary/2024-Jiang-Network-Calculus-Revisit.pdf` | 排除 | 分组化反例针对网络演算服务曲线，R1 已要求包/字节/容量量纲审计；不新增闭合机制。 |
| `raw/papers/pinn/network-calculus-boundary/2024-Podina-Conformalized-PINN.pdf` | 排除 | 拆分共形校准依赖独立可交换校准集，不提供公开数据队列真值。 |
| `raw/papers/pinn/network-calculus-boundary/2025-Jiang-Packetization-Impact.pdf` | 排除 | 继续细化分组化边界，属于 R3 服务保证而非 R1 最小状态闭合。 |
| `raw/papers/pinn/network-calculus-boundary/2025-Yu-Conformal-PINN.pdf` | 排除 | 局部共形处理异方差但不解决部分观测闭合和跨域漂移。 |

## PCAP 与网络动力学子目录

| PDF | 状态 | 筛查理由 |
| --- | --- | --- |
| `raw/papers/pinn/pcap/1995-Paxson-广域流量非泊松性.pdf` | 扩展纳入 | 固定小时泊松只适用于部分用户会话；包到达、机器生成连接和 FTP 数据连接簇的多尺度突发直接否决普适忙期泊松闭合。 |
| `raw/papers/pinn/pcap/2000-Misra-TCP-AQM流体模型.pdf` | 排除 | TCP/AQM 时滞流体状态依赖拥塞窗口、往返时延和丢包概率；三源共享输入和 UDP-only ns-3 不具备。 |
| `raw/papers/pinn/pcap/2003-Hohn-分组到达聚类过程.pdf` | 扩展纳入 | 簇过程分离小尺度流内结构与大尺度重尾，同时证明简单更新过程可产生伪缩放、流内速率可平移尺度轴，否决把波谱膝点当作尺度真值。 |
| `raw/papers/pinn/pcap/2010-Habib-输出链路轨迹队列推断.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2010-Habib-Queue-Inferencing.pdf` SHA-256 完全一致；原件保留。 |
| `raw/papers/pinn/pcap/2018-DeVaere-QUIC-TCP被动时延测量.pdf` | 排除 | 讨论加密协议旁路时延可观测性，主要服务 R2；不提供 R1 队列闭合真值。 |
| `raw/papers/pinn/pcap/2018-Vardoyan-TCP-CUBIC流体模型.pdf` | 排除 | 协议专属隐藏状态和反馈时延均不可见，且当前 ns-3 仅 UDP。 |
| `raw/papers/pinn/pcap/2022-Alaoui-二维TCP-AQM流体模型.pdf` | 排除 | 双时间基 TCP/AQM 模型需要更强协议状态，计算与观测合同均不满足。 |
| `raw/papers/pinn/pcap/2022-Ferriol-RouteNet-Erlang.pdf` | 排除 | 监督网络性能模型依赖拓扑、路由和业务矩阵，不学习受约束不可观测通量。 |
| `raw/papers/pinn/pcap/2022-Lin-ET-BERT加密流量表征.pdf` | 排除 | 包序列自监督表征不是物理残差或队列真值。 |
| `raw/papers/pinn/pcap/2023-Helm-网络演算辅助GNN.pdf` | 排除 | 仅把解析上界作为图模型输入特征，不提供闭合头梯度或状态辨识。 |
| `raw/papers/pinn/pcap/2023-Zhang-网络演算增强时延预测.pdf` | 排除 | 依赖拓扑、到达曲线和服务曲线，超出现有共享 B0；属于 R3 边界。 |
| `raw/papers/pinn/pcap/2023-Zhao-YaTC多层流量表征.pdf` | 排除 | 多层流量表征的“层”不是物理时间尺度或控制体。 |
| `raw/papers/pinn/pcap/2024-Wang-NetMamba流量表征.pdf` | 排除 | 长序列状态空间编码不定义队列守恒或闭合真值。 |
| `raw/papers/pinn/pcap/2025-Du-PRED-DCTCP流体模型.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2025-Du-PRED.pdf` SHA-256 完全一致；原件保留。 |
| `raw/papers/pinn/pcap/2025-Raghunathan-QuASI队列可辨识性.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2025-Raghunathan-QuASI.pdf` SHA-256 完全一致；原件保留。 |

## 协议自适应子目录

| PDF | 状态 | 筛查理由 |
| --- | --- | --- |
| `raw/papers/pinn/protocol-adaptive/2017-Guo-Neural-Network-Calibration.pdf` | 排除 | 通用分类器置信度校准不定义队列状态、控制体、物理闭合或尺度真值；可靠性边界由 R1 的后验与字段缺测论文直接覆盖。 |
| `raw/papers/pinn/protocol-adaptive/2019-Ovadia-Uncertainty-Dataset-Shift.pdf` | 排除 | 通用数据集偏移不确定性基准没有守恒方程或不可观测通量，只能服务跨域检测校准而不能支撑 R1 闭合。 |
| `raw/papers/pinn/protocol-adaptive/2020-Stiller-GatedPINN.pdf` | 重复 | 与本轮规范副本 `multiscale-observability-closure/2020-Stiller-GatedPINN.pdf` SHA-256 完全一致；原件保留。 |
| `raw/papers/pinn/protocol-adaptive/2021-Ahn-Nested-Mixture-of-Experts.pdf` | 排除 | 竞争物理模式与白盒/黑盒专家用于 R2 协议责任，不定义细粗控制体一致性。 |
| `raw/papers/pinn/protocol-adaptive/2021-Poli-Neural-Hybrid-Automata.pdf` | 排除 | 离散动力学模式恢复要求顺序轨迹和分段真值，当前共享 B0 不具备；属于 R2。 |
| `raw/papers/pinn/protocol-adaptive/2021-Qian-Latent-Hybridisation-Model.pdf` | 排除 | 单个正确专家 ODE 嵌入潜在模型，不处理多尺度队列闭合。 |
| `raw/papers/pinn/protocol-adaptive/2021-RFC8999-QUIC-Invariants.pdf` | 排除 | QUIC 长首部与版本协商不变量规定协议可观测字段，但不提供网络队列状态、服务过程或跨尺度守恒；属于 R2 标准证据。 |
| `raw/papers/pinn/protocol-adaptive/2021-RFC9000-QUIC-Transport.pdf` | 排除 | QUIC 传输标准定义端点协议状态，不等于路径设备队列真值，且共享 B0 不含其完整时序字段；属于 R2。 |
| `raw/papers/pinn/protocol-adaptive/2021-RFC9001-QUIC-TLS.pdf` | 排除 | QUIC 的 TLS 加密边界约束协议分类可观测性，不给出输出端口服务、丢弃计数或队列闭合监督；属于 R2。 |
| `raw/papers/pinn/protocol-adaptive/2022-Bischof-MoE-PINN.pdf` | 排除 | 坐标门控多个同方程 PINN，专家数增加可退化；与 APINN/GatedPINN 证据重复。 |
| `raw/papers/pinn/protocol-adaptive/2022-RFC9287-QUIC-Bit-Greasing.pdf` | 排除 | QUIC 位保留与可扩展性规则影响协议指纹稳定性，但不改变 R1 的控制体状态或闭合可辨识性；属于 R2。 |
| `raw/papers/pinn/protocol-adaptive/2022-RFC9312-QUIC-Manageability.pdf` | 排除 | QUIC 可管理性文档讨论被动测量限制，却不提供当前三源缺失的设备服务轨迹和队列真值；其直接责任属于 R2。 |
| `raw/papers/pinn/protocol-adaptive/2023-Bajaj-Physics-Fails.pdf` | 排除 | 错误物理导致低残差错误状态的重要边界已由 2109.01050 与柯西困难性论文更直接覆盖。 |
| `raw/papers/pinn/protocol-adaptive/2023-Luxemburk-QUIC-Classification.pdf` | 排除 | 闭集 QUIC 服务分类和漂移属于协议可观测性，不提供队列状态真值。 |
| `raw/papers/pinn/protocol-adaptive/2024-Gahtan-VisQUIC.pdf` | 排除 | 受控解密标签估计应用响应数，不恢复拥塞或队列状态。 |
| `raw/papers/pinn/protocol-adaptive/2025-Feng-RPLPO.pdf` | 排除 | 连续部分观测高分辨状态恢复仍使用同一完整 PDE；HFM 已覆盖可观测性，且其隐藏状态误差反证与柯西论文重复。 |
| `raw/papers/pinn/protocol-adaptive/2025-Ghanem-Partial-Physics-Neural-ODE.pdf` | 排除 | 交替估计隐状态和有限维未知参数，依赖顺序测量与正确耦合；HFM/显式闭合已覆盖该边界。 |

## 当前扩展批次队列

| 批次 | 两篇全文 | 证据责任 |
| --- | --- | --- |
| 六（已完成） | APINN；GatedPINN | 软门控域分解不是时间尺度；新增初始化捕获、专家非唯一及低残差错误状态三项失败条件。 |
| 七（已完成） | 梯度流病态；数据与物理帕累托前沿 | 新增幅值平衡不解决方向冲突/结构非唯一，以及系统量纲移动表观前沿两项失败边界。 |
| 八（已完成） | PINN 失败模式；柯西问题残差不足性 | 新增已知难度课程热启动与固定短窗推进这一受限机制；新增缺失边界或域外信息时零残差仍可任意错误，以及间断目标有限精度不可达两类失败边界。 |
| 九（已完成） | PRED；道路交通网络 PINN | 新增 RTT/硬件绑定双时间尺度白盒控制与分链接交界守恒；同时新增完整端口遥测/协议状态输入门槛和离散平均观测与点式守恒冲突。 |
| 十（已完成） | Liebeherr 服务反演；Bouillard 隐藏异常 | 新增服务反演的成对累计到达/离开或主动探测字段门，并限定只有到达时间时只能降级为多尺度到达包络异常指标。 |
| 十一（已完成） | Paxson 非泊松性；Hohn 聚类过程 | 新增伪缩放与速率引起的尺度轴平移失败条件，并把忙期泊松从默认假设降为按协议、层级和时段检验的条件合同。 |
| 十二 | 原始 PINN 求解；原始 PINN 发现 | 核验完整坐标、已知方程与有限维参数基线；若无新增，记为无新增批次二并触发停止条件。 |

## 当前计数

- 文件路径筛查：110/110。
- 唯一全文：97。
- 核心纳入：10。
- 扩展纳入：12。
- 扩展候选：0。
- 停止核验候选：2。
- 字节级重复：13 个副本，对应 13 组。
- 初筛排除：73 份唯一全文。
- 停止条件：第 11 批新增伪缩放和速率平移失败条件，连续无新增批次数仍为 `0`；无论该计数是否达到 `2`，第 12 批结束后均按用户硬上限停止扩展。
