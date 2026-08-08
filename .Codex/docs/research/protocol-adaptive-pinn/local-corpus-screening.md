# R2 本地 PINN 语料逐篇筛查清单

## 口径

- 当前目录：`raw/papers/pinn/`。
- 文件对象：76 个 PDF。
- SHA-256 唯一内容：73 篇。
- 已有精确 `source_pdf` wiki 映射：74/76 个文件。
- 用户所述“74 篇”与已有 wiki 映射数一致，但不等于当前文件数或唯一内容数；本清单按 76 个文件逐项留痕、按 73 篇唯一内容评审。
- 原件只读；重复文件不删除、不改名、不重复计入证据量。

## 状态定义

- **纳入全文**：直接支撑 R2 的方程、字段、可辨识性、梯度、路由或失败边界，需回到一级原文核验。
- **背景保留**：机制间接相关，可用于设计解释但不承担关键论断。
- **排除**：综述、纯适配器/语言模型工程、任务不相干或只有二手概述，不进入载荷证据矩阵。
- **重复**：SHA-256 相同，只核验规范路径的一份。
- **待筛查**：尚未完成题名/摘要/既有笔记与全文门禁。

## 字节级重复组

- `raw/papers/pinn/1711.10561.pdf` = `raw/papers/pinn/paper_b002d83866255ef3bd48ae3819cf2520.pdf`，SHA-256 `2a8db6776a110a4f36bd1e36af79cf31a2e74baa5af8f7ee3d9286a75fdc400d`。
- `raw/papers/pinn/multiscale-observability-closure/2010-Habib-Queue-Inferencing.pdf` = `raw/papers/pinn/pcap/2010-Habib-输出链路轨迹队列推断.pdf`，SHA-256 `a7756063a3a111334d7cbe216721bc925af1ff6542d1ba372c71fbc541871a0d`。
- `raw/papers/pinn/multiscale-observability-closure/2025-Raghunathan-QuASI.pdf` = `raw/papers/pinn/pcap/2025-Raghunathan-QuASI队列可辨识性.pdf`，SHA-256 `542313816aa297abe10f937d6419cee31298e453c72f83c4dd135022389fafea`。

## 逐文件清单

### 根目录 PINN、混合专家与适配器

- [x] `raw/papers/pinn/1711.10561.pdf` | **纳入全文** | 标准 PINN 以连续状态、已知控制方程、初边值和无标签配点构造可微残差；只迁移机制，不迁移 PDE
- [x] `raw/papers/pinn/1711.10566.pdf` | **纳入全文** | 已知方程结构下可联合辨识少量参数，但参数可辨识依赖观测覆盖与噪声，不能从独立流记录自动发现协议定律
- [x] `raw/papers/pinn/2001.04536-PINN梯度病态.pdf` | **纳入全文** | 数值刚性造成复合损失梯度量级失衡；梯度统计调权只处理尺度，不保证解决方向冲突或不可辨识
- [x] `raw/papers/pinn/2007.14527-PINN神经切线核.pdf` | **纳入全文** | 神经切线核谱解释损失分量收敛速率差异，但无限宽全连接理论不能直接外推到低秩适配大模型
- [x] `raw/papers/pinn/2016-Lee-非对称多任务学习.pdf` | **背景保留** | 损失感知有向迁移说明知识流不必对称，但软正则不保证分支或路由输出严格不受分类任务影响
- [x] `raw/papers/pinn/2018-Lee-深度非对称多任务特征学习.pdf` | **背景保留** | 可靠任务可主导共享表征，仍是软作用而非分类梯度到物理路由的严格零梯度合同
- [x] `raw/papers/pinn/2021-KarimiMahabadi-HyperFormer.pdf` | **排除** | 按离散任务标识生成适配器，不处理逐样本协议可观测性、物理适用性或隐藏状态真值
- [x] `raw/papers/pinn/2021-Lewis-BASE-Layers.pdf` | **背景保留** | 线性指派可保证训练批次等负载，但推理改用贪心且专家可能按表面词法分工，反证负载均衡不等于物理语义
- [x] `raw/papers/pinn/2021-Pfeiffer-AdapterFusion.pdf` | **背景保留** | 先独立训练并冻结模块再学习组合提供阶段式隔离先例，但学习型融合仍无物理适用性保证
- [x] `raw/papers/pinn/2022-Alayrac-Flamingo.pdf` | **背景保留** | 零初始化门控条件旁路保证初始前向等价，可作安全初始化参考，不提供协议动力学证据
- [x] `raw/papers/pinn/2022-Dai-StableMoE.pdf` | **背景保留** | 同一样本训练中会反复换专家；路由蒸馏后冻结可稳定分配，但会牺牲适应性且不保证语义正确
- [x] `raw/papers/pinn/2022-Fedus-Switch-Transformer.pdf` | **背景保留** | Top-1 路由仍受容量、丢词元、负载和数值稳定约束；属于通用混合专家工程，不承担物理论断
- [x] `raw/papers/pinn/2022-Hu-APINN.pdf` | **背景保留** | 同一 PDE 上的可训练软域分解强依赖门控初始化，支持给路由明确物理先验而非自由发现协议
- [x] `raw/papers/pinn/2023-Yan-辅助任务PINN.pdf` | **背景保留** | 比较共享私有与专家结构并按梯度余弦筛辅助更新；支持结构隔离，但没有逐样本协议路由停止梯度
- [x] `raw/papers/pinn/2023-Zhang-ControlNet.pdf` | **背景保留** | 冻结主干与零初始化旁路保证第一步前向等价，完整复制编码器成本高且不解决数据可辨识性
- [x] `raw/papers/pinn/2023-Zhang-LLaMA-Adapter.pdf` | **排除** | 零门控提示注入是参数高效适配机制，没有协议方程、路由真值或状态评价
- [x] `raw/papers/pinn/2023-Zhao-Prototype-HyperAdapter.pdf` | **排除** | 任务原型和检索器生成任务级适配器，不是逐样本物理控制或协议置信度
- [x] `raw/papers/pinn/2024-Agiza-MTLoRA.pdf` | **背景保留** | 共享与任务专用低秩模块可作结构先例，但任务标识和监督目标不能替代协议适用硬掩码
- [x] `raw/papers/pinn/2024-Chalapathi-物理硬约束混合专家.pdf` | **背景保留** | 专家职责由预先划定物理域和局部硬约束决定，支持先定义职责再路由；不是不同协议方程混合
- [x] `raw/papers/pinn/2024-Dai-DeepSeekMoE.pdf` | **背景保留** | 始终激活共享专家支持共享/专属结构，但语言建模形成的专家专门化不等于可解释物理专门化
- [x] `raw/papers/pinn/2024-Kong-LoRA-Switch.pdf` | **排除** | 重点是动态低秩适配器的推理开销与内核融合，且正式录用状态未核验，不改变 R2 合同
- [x] `raw/papers/pinn/2024-Li-MixLoRA.pdf` | **背景保留** | 词元级低秩专家说明参数高效路由可行，但负载均衡不保证协议语义且会引入词元级路由漂移
- [x] `raw/papers/pinn/2024-Lv-HyperLoRA.pdf` | **排除** | 超网络生成低秩权重依赖教师参数和权重空间约束，不提供协议状态、置信度或守恒证据
- [x] `raw/papers/pinn/2024-Ma-MoDULA.pdf` | **背景保留** | 分阶段训练通用、领域专用模块和路由器支持冻结扩展，但残差混合不保证物理语义或主输出不变
- [x] `raw/papers/pinn/2024-Panda-稠密反向传播路由.pdf` | **背景保留** | 用未激活专家近似输出让任务梯度稠密训练路由器，恰与本课题禁止分类梯度塑造物理路由的隔离目标相反
- [x] `raw/papers/pinn/2024-Wang-LoRA-Flow.pdf` | **排除** | 生成前缀驱动逐词元融合会削弱序列级协议路由一致性，且没有物理或状态真值
- [x] `raw/papers/pinn/2024-Wu-MoLE.pdf` | **背景保留** | 冻结既有低秩专家并只训练逐层门控支持模块复用，但不支持联合学习物理专属分支
- [x] `raw/papers/pinn/2105.00862-数据与物理帕累托前沿.pdf` | **纳入全文** | 系统尺度和参数化会移动表观帕累托前沿；量纲归一只是必要条件，必须以状态与任务指标裁决
- [x] `raw/papers/pinn/2109.01050-PINN失败模式.pdf` | **纳入全文** | 软方程正则可使损失面病态；课程与短时序只缓解可辨识系统的优化，不能修复错误物理或缺真值
- [x] `raw/papers/pinn/2408.11104-ConFIG.pdf` | **纳入全文** | 可构造与多个损失梯度均为正投影的更新，但无共同下降时可能近零，消除一阶冲突不证明物理项有新增信息
- [x] `raw/papers/pinn/2410.13228.pdf` | **排除** | PINN 到 PIKAN 的宽综述仅作导航，关键论断均由本地一级原文承担
- [x] `raw/papers/pinn/2501.06572.pdf` | **排除** | 进化优化综述不提供协议方程、字段可观测性、路由隔离或队列真值
- [x] `raw/papers/pinn/MDPI-ApplSci-2025-15-8092-PINN综述.pdf` | **排除** | 方法演进综述不进入承重证据矩阵，避免用二手概述替代一级原文
- [x] `raw/papers/pinn/algorithms-15-00447-交通网络PINN.pdf` | **纳入全文** | 道路交通稀疏状态由路段动力学、绝对传感锚点和汇合分流守恒共同闭合；只迁移原则，不移植道路方程
- [x] `raw/papers/pinn/paper_0dd9fd2db26952889e10293d9209c0bf.pdf` | **排除** | 科学机器学习与 PINN 综述只作背景导航，不承担 R2 一手论断
- [x] `raw/papers/pinn/paper_390db51220335dc4b705f12f777ef9eb.pdf` | **排除** | 2025 年 PDE 综合综述只作背景导航，不承担 R2 一手论断
- [x] `raw/papers/pinn/paper_520fcb7d7e085e3081e0ab5f0c5b4dd5.pdf` | **排除** | 技术、应用与挑战综述不改变已冻结的字段、路由、梯度或真值合同
- [x] `raw/papers/pinn/paper_b002d83866255ef3bd48ae3819cf2520.pdf` | **重复** | 与 `raw/papers/pinn/1711.10561.pdf` 字节级相同
- [x] `raw/papers/pinn/paper_ced7ef2c6ebf5b388931d1671a9e9520.pdf` | **排除** | 流体力学 PINN 综述只作背景导航，不提供互联网传输协议或抓包可观测性证据
- [x] `raw/papers/pinn/wang24b-柯西问题PINN困难性.pdf` | **纳入全文** | 低二范数残差和初值误差不足以保证真实解，直接要求以独立隐藏状态评价残差方法
- [x] `raw/papers/pinn/基于物理信息的神经网络：最新进展与展望.pdf` | **排除** | 中文综述只作术语和引文导航，承重结论回到已核验一级原文

### 多尺度、可观测性与闭合

- [x] `raw/papers/pinn/multiscale-observability-closure/2010-Habib-Queue-Inferencing.pdf` | **重复** | 与 `raw/papers/pinn/pcap/2010-Habib-输出链路轨迹队列推断.pdf` 字节级相同
- [x] `raw/papers/pinn/multiscale-observability-closure/2020-Raissi-HFM.pdf` | **纳入全文** | 部分观测恢复依赖已知方程、充分时空覆盖与可辨识边界；不能把普通流级聚合类比为可恢复隐藏场
- [x] `raw/papers/pinn/multiscale-observability-closure/2021-Yang-BPINN.pdf` | **背景保留** | 已知高斯传感噪声的贝叶斯后验不等于字段缺失；支持显式缺失掩码，但不提供协议置信度
- [x] `raw/papers/pinn/multiscale-observability-closure/2022-Patel-cvPINN.pdf` | **纳入全文** | 控制体守恒可学习未知通量，但守恒本身可收敛到违反熵条件的错误激波，必须有独立状态与物理可实现性评价
- [x] `raw/papers/pinn/multiscale-observability-closure/2022-Taghizadeh-Explicit-Closure.pdf` | **纳入全文** | 闭合项由 16,384 次微观仿真监督后冻结并嵌入宏观求解器；支持先取得闭合真值，反对用自由修正项吸收残差
- [x] `raw/papers/pinn/multiscale-observability-closure/2023-McClenny-SA-PINN.pdf` | **背景保留** | 自适应权重强调高残差配点，属于难度注意而非观测置信度，直接用于噪声字段可能放大错误
- [x] `raw/papers/pinn/multiscale-observability-closure/2023-Perez-Adaptive-BPINN.pdf` | **背景保留** | 按训练任务梯度方差调权并在预热后冻结，不是逐样本协议校准，不能替代缺失与适用性掩码
- [x] `raw/papers/pinn/multiscale-observability-closure/2024-Cen-DFVM.pdf` | **背景保留** | 固定局部控制体与自适应采样支持有界弱残差，但物理损失收敛仍不能替代独立状态误差
- [x] `raw/papers/pinn/multiscale-observability-closure/2024-Dolean-Multilevel-FBPINN.pdf` | **背景保留** | 固定粗细域的多层通信可缓解谱偏差，但不提供学习尺度、协议路由、闭合或缺测机制
- [x] `raw/papers/pinn/multiscale-observability-closure/2025-Raghunathan-QuASI.pdf` | **重复** | 与 `raw/papers/pinn/pcap/2025-Raghunathan-QuASI队列可辨识性.pdf` 字节级相同

### PCAP、队列与网络动力学

- [x] `raw/papers/pinn/pcap/1995-Paxson-广域流量非泊松性.pdf` | **纳入全文** | 分组到达在多时间尺度显著突发，否定把泊松到达写成跨协议、跨场景通用物理规律
- [x] `raw/papers/pinn/pcap/2000-Misra-TCP-AQM流体模型.pdf` | **纳入全文** | 给出 TCP 窗口、反馈时延、丢包与瓶颈队列耦合方程；依赖长流、AQM、容量和不可公开观测的窗口/延迟状态
- [x] `raw/papers/pinn/pcap/2003-Hohn-分组到达聚类过程.pdf` | **背景保留** | 流到达和流内包过程构成统计点过程，不是可直接训练的控制方程或队列真值
- [x] `raw/papers/pinn/pcap/2010-Habib-输出链路轨迹队列推断.pdf` | **纳入全文** | 单服务台 FIFO 输出端口上由离开时刻和已知容量估计忙期内期望等待/队列分布；仅在泊松或缓慢变化指数到达等假设下成立，不是实际队列轨迹真值
- [x] `raw/papers/pinn/pcap/2018-DeVaere-QUIC-TCP被动时延测量.pdf` | **纳入全文** | 2018 草案依赖端点显式旋转位和 2 位有效边计数器；无可见协作位或端点日志时，QUIC 抓包不能声称可观测往返时延
- [x] `raw/papers/pinn/pcap/2018-Vardoyan-TCP-CUBIC流体模型.pdf` | **纳入全文** | Reno/CUBIC 时滞模型需要容量、反馈时延、丢包、丢包前窗口与距上次丢包时间；必须与具体拥塞控制实现匹配
- [x] `raw/papers/pinn/pcap/2022-Alaoui-二维TCP-AQM流体模型.pdf` | **背景保留** | 双时间基和多内部状态提高观测与计算负担，且原文主要验证局部稳定控制，不能作为最小协议残差
- [x] `raw/papers/pinn/pcap/2022-Ferriol-RouteNet-Erlang.pdf` | **背景保留** | 数据驱动数字孪生依赖拓扑、路由、容量、缓冲、调度和业务模型描述，普通公共抓包不满足输入合同
- [x] `raw/papers/pinn/pcap/2022-Lin-ET-BERT加密流量表征.pdf` | **背景保留** | 突发与报文字节预训练支持序列表征基线，但掩码和同源突发任务不是物理残差且可能保留实现指纹
- [x] `raw/papers/pinn/pcap/2023-Helm-网络演算辅助GNN.pdf` | **背景保留** | 令牌桶与速率-时延曲线的最坏界只作为图模型输入，并依赖测试床拓扑、服务曲线和交叉流量
- [x] `raw/papers/pinn/pcap/2023-Zhang-网络演算增强时延预测.pdf` | **背景保留** | OMNeT++ 数据上的端到端网络演算上界仍是附加输入，不是可微残差；公共流记录缺每跳服务合同
- [x] `raw/papers/pinn/pcap/2023-Zhao-YaTC多层流量表征.pdf` | **背景保留** | 地址随机化、端口置零与保留方向提供去偏先例；载荷字节和预训练表征不提供动力学状态
- [x] `raw/papers/pinn/pcap/2024-Wang-NetMamba流量表征.pdf` | **背景保留** | 线性复杂度状态空间编码适合长序列，但只解决表征效率与偏差，不提供物理方程或隐藏状态真值
- [x] `raw/papers/pinn/pcap/2025-Du-PRED-DCTCP流体模型.pdf` | **背景保留** | DCTCP/RED 稳态关系依赖交换机队列、容量、传播时延和并发流计数，适合可编程数据平面控制而非普通 PCAP 瞬态残差
- [x] `raw/papers/pinn/pcap/2025-Raghunathan-QuASI队列可辨识性.pdf` | **纳入全文** | 端口区间计数只能判定是否存在相容包轨迹，不能唯一恢复队列；共享流字段也不满足其交换机端口语义

### 协议自适应核心十篇

- [x] `raw/papers/pinn/protocol-adaptive/2020-Stiller-GatedPINN.pdf` | **纳入全文** | 核心十篇已完成页级证据、Zotero 和 wiki 门禁
- [x] `raw/papers/pinn/protocol-adaptive/2021-Ahn-Nested-Mixture-of-Experts.pdf` | **纳入全文** | 核心十篇已完成页级证据、Zotero 和 wiki 门禁
- [x] `raw/papers/pinn/protocol-adaptive/2021-Poli-Neural-Hybrid-Automata.pdf` | **纳入全文** | 核心十篇已完成页级证据、Zotero 和 wiki 门禁
- [x] `raw/papers/pinn/protocol-adaptive/2021-Qian-Latent-Hybridisation-Model.pdf` | **纳入全文** | 核心十篇已完成页级证据、Zotero 和 wiki 门禁
- [x] `raw/papers/pinn/protocol-adaptive/2022-Bischof-MoE-PINN.pdf` | **纳入全文** | 核心十篇已完成页级证据、Zotero 和 wiki 门禁
- [x] `raw/papers/pinn/protocol-adaptive/2023-Bajaj-Physics-Fails.pdf` | **纳入全文** | 核心十篇已完成页级证据、Zotero 和 wiki 门禁
- [x] `raw/papers/pinn/protocol-adaptive/2023-Luxemburk-QUIC-Classification.pdf` | **纳入全文** | 核心十篇已完成页级证据、Zotero 和 wiki 门禁
- [x] `raw/papers/pinn/protocol-adaptive/2024-Gahtan-VisQUIC.pdf` | **纳入全文** | 核心十篇已全文核验；与既有 datasets 原件同哈希并复用既有笔记
- [x] `raw/papers/pinn/protocol-adaptive/2025-Feng-RPLPO.pdf` | **纳入全文** | 核心十篇已完成页级证据、Zotero 和 wiki 门禁
- [x] `raw/papers/pinn/protocol-adaptive/2025-Ghanem-Partial-Physics-Neural-ODE.pdf` | **纳入全文** | 核心十篇已完成页级证据、Zotero 和 wiki 门禁

## 优先筛查批次

1. P0：TCP/AQM/CUBIC/DCTCP、队列反演、QuASI、QUIC/TCP 被动时延与共享到达过程。
2. P0：APINN、物理硬约束混合专家、StableMoE、稠密反向路由、辅助任务 PINN。
3. P1：cvPINN、HFM、显式闭合、贝叶斯缺测/噪声、多层 FBPINN、局部弱形式。
4. P1：PINN 梯度病态、帕累托前沿、ConFIG、残差不足性。
5. P1：ET-BERT、YaTC、NetMamba、网络演算与 RouteNet-Erlang。
6. P2：适配器、低秩专家、通用混合专家与综述；只保留能改变冻结合同的新机制。

## 饱和记录

- 批次 0：核心十篇完成。新增机制为“条件专家、硬适用边界、错误物理、隐藏状态真值、定向物理梯度、QUIC 加密可观测与漂移”；合同仍变化，未饱和。
- 批次 1：多尺度与闭合 8 篇唯一原件完成。新增边界为“守恒不保证熵解、闭合必须有微观真值、部分观测须先证明可辨识、梯度权重不等于观测置信度”；数据合同新增独立状态评价，未饱和。
- 批次 2：PCAP、队列与网络动力学 15 篇完成。新增边界为“TCP 方程绑定具体实现和隐藏状态、输出抓包反演不是轨迹真值、粗计数只给相容集、网络演算依赖服务合同、加密流量论文只支持表征与去偏”；QUIC 当前规范状态仍待一手补证，未饱和。
- 批次 3：根目录 40 篇唯一内容完成。训练理论与路由架构没有改变数据门禁；新增的唯一合同约束是“多目标调权与无冲突更新必须后置于信息增量验证，路由稳定/冻结不等于路由正确，任务梯度训练路由与物理语义隔离冲突”。连续两批没有出现可替代独立状态真值的新机制，除 QUIC 当前规范与协议校准外，本地机制证据达到饱和。
- 批次 4：只为剩余两处缺口补入 RFC 8999、9000、9001、9287、9312 与 Guo 2017、Ovadia 2019 七份一手原件。新增边界为“旋转位可选且随机禁用、固定位可随机化、当前线图像不能被动测量丢包、同分布事后校准不能保证跨源可靠”。这些证据强化未知回退与跨源校准门禁，没有产生可启动 QUIC 专属专家的新机制；文献筛查达到证据饱和。
