# R3 本地文献全集筛查

## 口径

- 盘点范围：`raw/papers/pinn/` 下全部 PDF。
- 盘点时间：2026-07-30。
- 总量：77 份文件，74 个唯一内容，3 组完全重复。第 77 份为缺口检索后补入的 TAILING 原件。
- 状态说明：`核心`表示能直接承担 R3 的可辨识性、网络演算边界或反证；`辅助`表示只承担梯度、失配、队列动力学、协议观测或不确定性机制；`背景`表示仅用于 PINN 定义和综述；`排除`表示与 R3 当前承重问题无直接关系；`重复`表示不再重复阅读和建笔记。
- 本表是题名、摘要与既有全文笔记的首轮筛查。核心条目仍须在最终合同中给出页码、公式或实验位置。

## 全量筛查表

| 序号 | 本地原件 | 状态 | R3 处理理由 |
| --- | --- | --- | --- |
| 1 | `1711.10561.pdf` | 重复 | 与序号 48 内容哈希相同，保留序号 48 对应主版本作 PINN 定义背景。 |
| 2 | `1711.10566.pdf` | 背景 | 数据驱动物理方程发现的奠基工作，不提供网络演算、服务可辨识性或校准机制。 |
| 3 | `2001.04536-PINN梯度病态.pdf` | 辅助 | 支撑复合损失的梯度失衡风险和训练诊断，不支撑网络物理公式本身。 |
| 4 | `2007.14527-PINN神经切线核.pdf` | 辅助 | 支撑 PINN 收敛与谱偏差分析，只用于解释物理损失可能不进入任务表征。 |
| 5 | `2016-Lee-非对称多任务学习.pdf` | 排除 | 多任务共享结构属于其他候选路线，不能回答网络演算边界是否可观测。 |
| 6 | `2018-Lee-深度非对称多任务特征学习.pdf` | 排除 | 同上，仅可用于共享－私有适配器路线。 |
| 7 | `2021-KarimiMahabadi-HyperFormer.pdf` | 排除 | 参数生成适配器与 R3 的物理边界承重问题无直接关系。 |
| 8 | `2021-Lewis-BASE-Layers.pdf` | 排除 | 稀疏专家路由属于结构探索，不构成网络演算或不确定性证据。 |
| 9 | `2021-Pfeiffer-AdapterFusion.pdf` | 排除 | 适配器组合不是 R3 的核心物理机制。 |
| 10 | `2022-Alayrac-Flamingo.pdf` | 排除 | 多模态交叉注意力不回答 R3 的字段、边界和可辨识条件。 |
| 11 | `2022-Dai-StableMoE.pdf` | 排除 | 专家稳定训练只服务其他结构路线。 |
| 12 | `2022-Fedus-Switch-Transformer.pdf` | 排除 | 专家路由基线，与网络演算物理定义无直接关系。 |
| 13 | `2022-Hu-APINN.pdf` | 辅助 | 可作为域分解和门控 PINN 的结构旁证，但不能替代服务曲线证据。 |
| 14 | `2023-Yan-辅助任务PINN.pdf` | 辅助 | 可用于物理辅助任务连接主任务的梯度设计，不证明边界正确。 |
| 15 | `2023-Zhang-ControlNet.pdf` | 排除 | 生成控制分支不是网络流量物理或校准一级证据。 |
| 16 | `2023-Zhang-LLaMA-Adapter.pdf` | 排除 | 语言模型适配器结构只属于实现背景。 |
| 17 | `2023-Zhao-Prototype-HyperAdapter.pdf` | 排除 | 超网络适配器不承担 R3 理论。 |
| 18 | `2024-Agiza-MTLoRA.pdf` | 排除 | 多任务低秩适配属于已分离的结构候选。 |
| 19 | `2024-Chalapathi-物理硬约束混合专家.pdf` | 辅助 | 可提示不同物理域的门控方式，但 R3 当前不以混合专家为必要组成。 |
| 20 | `2024-Dai-DeepSeekMoE.pdf` | 排除 | 通用专家结构不回答流量服务下界可辨识性。 |
| 21 | `2024-Kong-LoRA-Switch.pdf` | 排除 | 低秩专家切换属于模型适配路线。 |
| 22 | `2024-Li-MixLoRA.pdf` | 排除 | 同上。 |
| 23 | `2024-Lv-HyperLoRA.pdf` | 排除 | 同上。 |
| 24 | `2024-Ma-MoDULA.pdf` | 排除 | 同上。 |
| 25 | `2024-Panda-稠密反向传播路由.pdf` | 辅助 | 仅在未来边界专家路由需要连续梯度时作为训练旁证。 |
| 26 | `2024-Wang-LoRA-Flow.pdf` | 排除 | 低秩流形结构不承担 R3 物理边界。 |
| 27 | `2024-Wu-MoLE.pdf` | 排除 | 低秩专家组合与当前 R3 主问题无直接关系。 |
| 28 | `2105.00862-数据与物理帕累托前沿.pdf` | 辅助 | 支撑数据损失与物理损失不必同时改善，以及非劣判据的必要性。 |
| 29 | `2109.01050-PINN失败模式.pdf` | 辅助 | 支撑物理模型错误、训练病态和表面残差改善的失败边界。 |
| 30 | `2408.11104-ConFIG.pdf` | 辅助 | 可作为冲突梯度诊断或后续目标协调方法，不是 R3 网络演算定义。 |
| 31 | `2410.13228.pdf` | 背景 | 物理信息机器学习综述，用于定位方法族，不作为创新性承重证据。 |
| 32 | `2501.06572.pdf` | 排除 | PINN 进化调参综述与 R3 当前理论门槛无直接关系。 |
| 33 | `MDPI-ApplSci-2025-15-8092-PINN综述.pdf` | 背景 | PINN 应用综述，只用于术语和失败模式回溯。 |
| 34 | `algorithms-15-00447-交通网络PINN.pdf` | 辅助 | 证明交通网络稀疏状态可与守恒约束联合，但其道路流模型不能迁移成分组网络公式。 |
| 35 | `multiscale-observability-closure/2010-Habib-Queue-Inferencing.pdf` | 重复 | 与序号 53 内容哈希相同，保留序号 53 的队列反演笔记。 |
| 36 | `multiscale-observability-closure/2020-Raissi-HFM.pdf` | 辅助 | 支撑从稀疏观测反演隐藏物理状态，但其观测配置和流体方程不等于网络队列。 |
| 37 | `multiscale-observability-closure/2021-Yang-BPINN.pdf` | 辅助 | 贝叶斯 PINN 假定已知噪声模型，可用于不确定性对照，不能直接处理缺失服务字段。 |
| 38 | `multiscale-observability-closure/2022-Patel-cvPINN.pdf` | 辅助 | 有限控制体约束可启发累计量残差，但不提供网络演算服务下界。 |
| 39 | `multiscale-observability-closure/2022-Taghizadeh-Explicit-Closure.pdf` | 辅助 | 支撑显式闭合变量和可辨识性检查，需避免把不可观测服务状态当作真值。 |
| 40 | `multiscale-observability-closure/2023-McClenny-SA-PINN.pdf` | 辅助 | 自适应权重可用于训练诊断，不能解决物理语义缺失。 |
| 41 | `multiscale-observability-closure/2023-Perez-Adaptive-BPINN.pdf` | 辅助 | 支撑贝叶斯 PINN 的任务梯度平衡，不等于字段级可信度或分布外覆盖。 |
| 42 | `multiscale-observability-closure/2024-Cen-DFVM.pdf` | 辅助 | 可微有限体积思想可启发窗口累计约束，需自行推导网络版本。 |
| 43 | `multiscale-observability-closure/2024-Dolean-Multilevel-FBPINN.pdf` | 辅助 | 多尺度域分解可解释窗口层级，但不是网络演算可辨识性证据。 |
| 44 | `multiscale-observability-closure/2025-Raghunathan-QuASI.pdf` | 重复 | 与序号 64 内容哈希相同，保留序号 64 的集合可辨识性笔记。 |
| 45 | `paper_0dd9fd2db26952889e10293d9209c0bf.pdf` | 背景 | PINN 科学机器学习综述，不能承担 R3 的网络演算公式。 |
| 46 | `paper_390db51220335dc4b705f12f777ef9eb.pdf` | 背景 | PDE-PINN 综合综述，仅用于查找训练机制，不作网络证据。 |
| 47 | `paper_520fcb7d7e085e3081e0ab5f0c5b4dd5.pdf` | 背景 | PINN 技术、应用与挑战综述，缺少 R3 特定观测协议。 |
| 48 | `paper_b002d83866255ef3bd48ae3819cf2520.pdf` | 背景 | PINN 奠基第一部分的主保留副本，只用于定义可微物理残差范式。 |
| 49 | `paper_ced7ef2c6ebf5b388931d1671a9e9520.pdf` | 背景 | 流体力学 PINN 综述，不可把连续流体公式直接映射为分组网络演算。 |
| 50 | `pcap/1995-Paxson-广域流量非泊松性.pdf` | 核心反证 | 证明分组到达不具有普适泊松性，否决把单一到达分布当作公共数据物理定律。 |
| 51 | `pcap/2000-Misra-TCP-AQM流体模型.pdf` | 辅助 | 给出 TCP/AQM 平均动力学，但依赖协议、队列和反馈状态，不可覆盖 UDP/QUIC 或加密聚合流。 |
| 52 | `pcap/2003-Hohn-分组到达聚类过程.pdf` | 核心反证 | 支撑到达聚类和多尺度突发，要求采用条件包络而非单尺度均值约束。 |
| 53 | `pcap/2010-Habib-输出链路轨迹队列推断.pdf` | 核心 | 被动队列反演需要正确输出链路观测、容量或服务时间以及强到达假设，直接约束公开数据可辨识范围。 |
| 54 | `pcap/2018-DeVaere-QUIC-TCP被动时延测量.pdf` | 辅助 | 支撑不同协议的被动时延可见性差异，不能提供通用服务曲线。 |
| 55 | `pcap/2018-Vardoyan-TCP-CUBIC流体模型.pdf` | 辅助 | 只适用于明确 TCP CUBIC 语义，作为协议依赖的反例。 |
| 56 | `pcap/2022-Alaoui-二维TCP-AQM流体模型.pdf` | 辅助 | 同样依赖 TCP/AQM 隐状态，不可直接用于 TQH-C2 聚合 UDP。 |
| 57 | `pcap/2022-Ferriol-RouteNet-Erlang.pdf` | 辅助 | 支撑拓扑、路由、容量和流量矩阵对性能预测的重要性，反证仅靠五个统计量恢复服务状态。 |
| 58 | `pcap/2022-Lin-ET-BERT加密流量表征.pdf` | 排除 | 属于载荷或首部表征基线，当前共同字段预算不满足。 |
| 59 | `pcap/2023-Helm-网络演算辅助GNN.pdf` | 核心 | 网络演算界作为 GNN 输入能改善时延预测，但依赖已知拓扑、链路速率和流量参数，且边界不是训练残差。 |
| 60 | `pcap/2023-Zhang-网络演算增强时延预测.pdf` | 核心 | 同样把固定网络演算上界作为输入，依赖仿真真值字段，不能证明公开流量上的可微 PINN。 |
| 61 | `pcap/2023-Zhao-YaTC多层流量表征.pdf` | 排除 | 需要更丰富的原始流量视图，不能在当前共同字段预算中公平比较。 |
| 62 | `pcap/2024-Wang-NetMamba流量表征.pdf` | 排除 | 同上，属于外部架构基线而非 R3 物理依据。 |
| 63 | `pcap/2025-Du-PRED-DCTCP流体模型.pdf` | 辅助 | 可验证特定 DCTCP 条件下的动力学，但协议与队列假设不能推广到全部数据。 |
| 64 | `pcap/2025-Raghunathan-QuASI队列可辨识性.pdf` | 核心 | 粗粒度计数通常只确定一组兼容队列轨迹而非唯一轨迹，支持集合值边界而非伪造点估计。 |
| 65 | `protocol-adaptive/2020-Stiller-GatedPINN.pdf` | 辅助 | 支撑按局部物理可信度门控，但不提供网络演算字段合同。 |
| 66 | `protocol-adaptive/2021-Ahn-Nested-Mixture-of-Experts.pdf` | 排除 | 通用嵌套专家方法属于 R2 路由结构证据。 |
| 67 | `protocol-adaptive/2021-Poli-Neural-Hybrid-Automata.pdf` | 辅助 | 可支持离散协议状态与连续动力学混合，但 R3 不应扩大为完整协议自动机。 |
| 68 | `protocol-adaptive/2021-Qian-Latent-Hybridisation-Model.pdf` | 辅助 | 隐式混合动力学只能作为缺失物理的学习型残差旁证。 |
| 69 | `protocol-adaptive/2022-Bischof-MoE-PINN.pdf` | 辅助 | 分区专家可作多物理状态对照，不能解决服务侧信息不可观测。 |
| 70 | `protocol-adaptive/2023-Bajaj-Physics-Fails.pdf` | 核心反证 | 当物理模型错误时必须允许数据驱动偏离，支持不确定性门控与残差通路。 |
| 71 | `protocol-adaptive/2023-Luxemburk-QUIC-Classification.pdf` | 辅助 | 只支撑 QUIC 识别所需观测字段，不提供队列边界。 |
| 72 | `protocol-adaptive/2024-Gahtan-VisQUIC.pdf` | 辅助 | 支撑 QUIC 可见字段与被动观测限制，约束协议条件化输入。 |
| 73 | `protocol-adaptive/2025-Feng-RPLPO.pdf` | 核心反证 | 部分物理或错误物理需在线修正，支持 R3 设置显式退化和否决门槛。 |
| 74 | `protocol-adaptive/2025-Ghanem-Partial-Physics-Neural-ODE.pdf` | 辅助 | 支撑已知物理与学习残差组合，但不能把学习残差解释成可证明服务曲线。 |
| 75 | `wang24b-柯西问题PINN困难性.pdf` | 辅助 | 支撑 PINN 在特定问题上的理论困难和误差边界，不直接给网络演算方法。 |
| 76 | `基于物理信息的神经网络：最新进展与展望.pdf` | 背景 | 中文 PINN 综述用于章节背景，不作 R3 创新性或正确性依据。 |
| 77 | `network-calculus-boundary/2023-Luebben-TAILING-Delay-Quantiles.pdf` | 核心反证 | 历史分组时延可预测未来点式分位数，但要求到达－离开或往返时延观测，不提供样本路径网络演算保证。 |

## 首轮结论

1. **本地直接承重文献很少。** 网络演算直接应用只有 Helm 与 Zhang 两篇，且均把离线计算的边界作为预测器输入，没有建立边界损失到检测模型参数的梯度路径。
2. **完整服务曲线存在可辨识性风险。** Habib 的被动反演需要输出链路位置、容量或服务时间和强到达假设；QuASI 进一步说明粗粒度计数通常只能约束兼容轨迹集合。
3. **R3 必须采用集合值或概率边界语义。** 公共数据上直接声称确定性服务曲线或最坏时延保证不成立；较诚实的候选是 ns-3 监督的有效服务下界，加上公共数据上的不确定性门控和到达包络退化路径。
4. **仍缺三组关键一级证据。** 需要补齐端到端服务曲线可辨识性、可微最大值或动态规划近似及误差界、分布漂移下的序列校准与物理边界覆盖。

## 去重记录

| 重复组 | 主保留版本 | 重复版本 |
| --- | --- | --- |
| PINN 第一部分 | `paper_b002d83866255ef3bd48ae3819cf2520.pdf` | `1711.10561.pdf` |
| 队列反演 | `pcap/2010-Habib-输出链路轨迹队列推断.pdf` | `multiscale-observability-closure/2010-Habib-Queue-Inferencing.pdf` |
| QuASI | `pcap/2025-Raghunathan-QuASI队列可辨识性.pdf` | `multiscale-observability-closure/2025-Raghunathan-QuASI.pdf` |
