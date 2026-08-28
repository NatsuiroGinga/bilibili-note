# XGBoost 版 CPA–ELP 文献审计研究笔记

- **日期**：2026-08-18
- **代理映射**：`xgboost_cpa_elp_literature_sol_max → gpt-5.6-sol → effort=max`
- **研究路线**：`RESEARCH_ROUTE=RWKV`
- **完成状态**：六阶段完成；方法效果均为“实验待证”。
- **筛选计数**：筛选 16 篇论文／正式全文，核心 11 篇，边界或排除 5 篇；另核验 4 个 XGBoost 官方文档页面。
- **全文计数**：11 篇核心论文全部有全文位置，其中 8 篇有本地原件，3 篇使用作者／会议正式开放全文；没有摘要支撑强结论的情况。

## 一、检索台账

### 1.1 本地原件与结构化笔记

- 先用 `fd` 盘点 `raw/papers` 与 `wiki/papers`，再用 `rg` 核对题名、作者、年份、原件路径、页码、公式和既有证据边界。
- 定向核验了 Lee 与 Stolfo、Bilge 等、Gülçehre 等、Pevný 与 Somol、Revaud 等、Grinsztajn 等、Gehri 等、Dijk 等的本地原件与全文笔记。
- 同时完整读取第三章 CPA–ELP 的方法、算法与理论边界：
  - `thesis/chapters/第三章-CPA-ELP/3.3-方法框架.md`
  - `thesis/chapters/第三章-CPA-ELP/3.4-算法实现.md`
  - `thesis/chapters/第三章-CPA-ELP/3.5-理论分析.md`
- 既有神经 CPA 的精确语义为：无向 2-IP 分组、按开始时间排序、每 128 条非重叠切段、段内对 `i≤t` 的隐藏表示取含当前流的前缀均值，再与当前隐藏表示拼接。ELP 在推理时跨实体全部流聚合，不受 CPA 切段影响。

### 1.2 Zotero 只读查询

- **状态**：Zotero Desktop 9.0.6，本地接口与连接器可用；本轮只读，未创建、删除或改写条目。
- `Learned-Norm Pooling...`：条目键 `FDF4HPJI`，无子附件；强结论使用仓库本地原件。
- `Learning with Average Precision...`：主条目 `JMWPSGXB`，另有重复导入残留 `HYETU4UY`；本轮未擅自去重。
- `GeM + Smooth-AP`：条目 `W7FTP9TU` 与 `7CPF6R3Q`；`W7FTP9TU` 的子项 `ZP36CCDA` 是元数据摘要，不冒充论文全文。
- `Dijk 2026`：条目 `U4ZMBMEK`，子项只有笔记 `67CNWY34`，无附件；强结论使用本地 `ssrn-6597680.pdf`。
- `Leoste 2025`：条目 `M8EZZ9S9`。
- Lee 与 Stolfo、Bilge 等、Gehri 等及 XGBoost 官方论文没有在本轮精确题名检索中得到可确认条目；不得写成“已入 Zotero”。

### 1.3 联网直接同构查询

| 轮次 | 查询式 | 新增核心全文 | 结果与处理 |
| --- | --- | ---: | --- |
| 联网 1 | `XGBoost causal prefix aggregation network flows intrusion detection entity power mean pooling`；`tree based intrusion detection rolling temporal host aggregation flow features XGBoost`；`multiple instance learning gradient boosted trees generalized mean pooling network traffic`；`source domain validation power mean hyperparameter selection network intrusion detection` | 0 | 命中各部件论文与常规 XGBoost 入侵检测应用，没有完整组合。 |
| 联网 2 | `"flow aggregation" XGBoost intrusion detection host entity`；`"historical features" XGBoost network intrusion detection flow`；`"rolling window" XGBoost network traffic anomaly detection`；`"power mean" XGBoost "multiple instance"` | 1 | 新增 Hindy 等 2021 正式全文；它把全流束聚合特征回填到每条流，但会使用整束后续流，且分类器是人工神经网络。 |
| 联网 3 | `"causal" "flow aggregation" intrusion detection XGBoost`；`"prefix" "flow features" XGBoost intrusion detection`；`"generalized mean pooling" network intrusion detection`；`"power mean pooling" network traffic detection` | 0 | 未新增核心全文；幂平均命中主要来自视觉、声音与图学习，不具备网络实体语义。 |
| 联网 4 | `"same host" rolling statistics XGBoost intrusion detection`；`"entity-level" XGBoost flow scores pooling intrusion`；`"source-only" exponent selection generalized mean pooling`；`"host-level aggregation" gradient boosting intrusion detection` | 0 | Slips 与 M-GRAD 被保留为外围边界：前者是主机时间窗证据系统，后者是 XGBoost 节点窗分类后做 IP 风险汇总；均无 2-IP 流级严格前缀和幂平均选阶。 |

最后一次新增核心全文是联网 2 的 Hindy 等。联网 3 与联网 4 连续两轮没有新增核心全文，各关键部件也均有强证据和边界证据，故停止扩展检索。

## 二、候选文献与全文状态

| 编号 | 文献 | 类别 | 全文与证据位置 | Zotero | 裁决 |
| --- | --- | --- | --- | --- | --- |
| C01 | Lee 与 Stolfo，2000，*A Framework for Constructing Features and Models for Intrusion Detection Systems* | 因果历史特征 | 本地 PDF；第 4.2 节、印刷第 238–239 页，表 VIII、印刷第 243 页 | 未确认 | 核心：历史同主机／同服务统计的直接来源。 |
| C02 | Bilge 等，2012，*DISCLOSURE* | 实体聚合＋树模型 | 本地 PDF；第 3–4 页 | 未确认 | 核心：NetFlow 按服务器聚合成树模型输入，但不是逐流前缀。 |
| C03 | Gülçehre 等，2014，*Learned-Norm Pooling...* | 幂平均／可学习阶数 | 本地 PDF；式（3）第 3 页，重参数化第 4 页，特例第 5 页 | `FDF4HPJI`，无附件 | 核心：归一化 Lp 公式和梯度学习阶数。 |
| C04 | Pevný 与 Somol，2017 arXiv 版，*Discriminative Models for Multi-instance Problems with Tree-structure* | 安全领域层次多示例 | 本地 PDF；第 3–5 页、图 3 | 未确认 | 核心：流→域名→计算机的均值／最大池化；非树模型、非幂平均。 |
| C05 | Revaud 等，2019，*Learning with Average Precision...* | GeM＋排序目标 | 本地 PDF；第 3–7 页，尤其第 6 页 | `JMWPSGXB`；重复项 `HYETU4UY` | 核心：可学习 GeM 与平均精确率目标联合训练已有先例。 |
| C06 | Gulrajani 与 Lopez-Paz，2020 arXiv／ICLR 2021，*In Search of Lost Domain Generalization* | 源域模型选择 | [正式全文](https://arxiv.org/html/2007.01434)，第 3 节 | 未确认 | 核心：模型选择是学习协议的一部分；目标域选择是 oracle，不是合法基准。 |
| C07 | Hindy 等，2021，*Utilising Flow Aggregation to Classify Benign Imitating Attacks* | 原始流聚合特征 | [正式全文](https://arxiv.org/pdf/2103.04208)，物理第 6–8 页 | 未确认 | 核心边界：聚合特征回填逐流已有先例，但整束回填不是因果前缀，模型是神经网络。 |
| C08 | Grinsztajn 等，2022，*Why Do Tree-based Models Still Outperform Deep Learning on Tabular Data?* | 树模型强基线 | 本地 PDF；第 3–8 页、图 1–6 | 未确认 | 核心基线：统一预算下树模型是强表格基线；明确排除流式／时序和不平衡任务。 |
| C09 | Gehri 等，2023，*Towards Generalizing Machine Learning Models to Detect C2 Attack Traffic* | 流分数到主机告警 | 本地 PDF；第 6.2 节、第 13–15 页 | 未确认 | 核心：随机森林逐流预测后按主机恶意流计数；不是幂平均或可学习选阶。 |
| C10 | Dijk 等，2026，*Flow Sequence Construction...* | 同数据集 XGBoost 与序列构造 | 本地 `ssrn-6597680.pdf`；第 11–16、24、31–33 页 | `U4ZMBMEK`，只有笔记 | 核心：2-IP／128 流构造有来源，但 XGBoost 只用 OP 原始逐流输入。 |
| C11 | Chen 与 Guestrin，2016，*XGBoost: A Scalable Tree Boosting System* | XGBoost 算法与系统 | [正式全文](https://arxiv.org/pdf/1603.02754)，第 1、3–5 页，第 3–4 节 | 未确认 | 核心工程来源：近似分裂、加权分位数草图、并行和外存谱系；不含现代 CUDA 接口。 |
| B01 | Ilse 等，2018，*Attention-based Deep Multiple Instance Learning* | 多示例替代池化 | 本地 PDF | 未核 | 边界：均值、最大与注意力池化；没有网络流、树或源年选阶。 |
| B02 | Yao 等，2023，GeM＋Smooth-AP | GeM 复现近邻 | 本地 PDF | `W7FTP9TU`、`7CPF6R3Q` | 边界：文字称可训练，但实验固定 `p=3`；不用于“学到 p”的最强证据。 |
| B03 | Leoste，2025，LSPR23→LSPR24 随机森林与一维卷积网络 | 同数据跨年树基线 | 本地 PDF | `M8EZZ9S9` | 边界：随机森林使用原始流特征，无 CPA／ELP。 |
| B04 | Garcia 等，2026，*Slips: Behavioral Evidence Aggregation for Network Security* | 主机时间窗证据汇总 | [正式全文](https://arxiv.org/abs/2608.11979)，第 2.1–2.3 节 | 未核 | 排除核心：系统级多模块证据累积，不是原始特征 XGBoost 或幂平均。 |
| B05 | Ates 等，2026，*M-GRAD* | XGBoost＋IP 风险后处理 | [会议正式页面](https://www.ieee-codit2026.com/event/codit-2026-1/track/session-v-11-computational-intelligence-82)，第 III-E、III-F、IV 节 | 未核 | 排除核心：输入已是节点－时间窗异构日志，后处理是置信度×严重度再跨窗汇总。 |

## 三、核心全文证据摘录

### 3.1 Lee 与 Stolfo 2000

- 原件：`raw/papers/methodology/multiple-instance/2000-Lee-Stolfo-Framework-Constructing-Features-Models-IDS-TISSEC.pdf`。
- 第 4.2 节把同一参照特征下、过去 `w` 秒内的连接转换为 `count`、`percent`、`average` 三类统计特征；表 VIII 给出过去 2 秒的同主机／同服务实例。
- 这是“只用已经发生的连接统计构造当前分类特征”的直接先例，足以否定“因果跨流上下文本身从未出现”的说法。
- 它使用固定时间窗、目的主机／服务键和 RIPPER；没有无向 2-IP 全前缀、隐藏表示、XGBoost 或幂平均。

### 3.2 Bilge 等 2012

- 原件：`raw/papers/methodology/multiple-instance/2012-Bilge-DISCLOSURE-Botnet-C2-NetFlow-ACSAC.pdf`。
- 第 3–4 页把全部 NetFlow 按服务器 `IP+端口` 聚成一个样本，计算流量均值、标准差、自相关、客户端到达间隔和时间模式，再交给随机森林。
- 它直接支撑“原始流统计聚合后交给树模型”这一总体范式。
- 聚合使用观测窗口内服务器的整体流集合，不为每条流产生随时间增长的严格前缀；也没有逐流原始／上下文两格对照或跨年度选阶。

### 3.3 Gülçehre 等 2014

- 原件：`raw/papers/methodology/multiple-instance/2014-Gulcehre-Learned-Norm-Pooling-ECMLPKDD.pdf`。
- 式（3），第 3 页：`u=((1/N)Σ|a_i-c_i|^p)^(1/p)`；第 4 页用 `p=1+softplus(ρ)` 保证 `p≥1`；第 5 页说明 `p=1`、`p=2`、`p→∞` 对应绝对值均值、均方根和最大值的关系。
- 论文直接占据“归一化 Lp 池化＋反向传播学习阶数”的公式和训练方式。
- 它不处理实体恶意分数、不使用树模型，也不支持 `0<p<1` 仍被称为范数。当前第三章的 `p=exp(p_log)>0` 比该来源范围更宽。

### 3.4 Pevný 与 Somol 2017 arXiv 版

- 原件：`raw/papers/methodology/multiple-instance/2016-Pevny-Discriminative-Models-Tree-Structure-MIL-AISec.pdf`；仓库文件名保留 2016，原件 arXiv 标记为 2017。
- 第 3–4 页把流先按目标域名池化成子袋，再按计算机池化成实体；使用均值或最大池化，只有计算机级感染标签。
- 它证明安全流量的实体级、层次多示例聚合并非空白，也给出均值与最大值的机制边界。
- 它是神经网络、固定池化且用 5 分钟袋；不能支撑 XGBoost 前缀特征或非梯度选 `p`。

### 3.5 Revaud 等 2019

- 原件：`raw/papers/methodology/ranking/2019-Revaud-AP-GeM-ICCV.pdf`；[CVF 正式页](https://openaccess.thecvf.com/content_ICCV_2019/html/Revaud_Learning_With_Average_Precision_Training_Image_Retrieval_With_a_Listwise_ICCV_2019_paper.html)。
- 第 6 页明确把 GeM 幂次与网络参数一起反向传播，且用可微平均精确率目标训练。
- 它占据“可学习广义均值＋平均精确率导向训练”的宽泛组合。
- 聚合对象是图像空间描述子，不是网络实体内的树模型分数；不能支撑源年离散网格选择。

### 3.6 Gulrajani 与 Lopez-Paz 2020／2021

- [正式全文第 3 节](https://arxiv.org/html/2007.01434)把超参数、检查点和架构选择都视为学习问题的一部分。
- 第 3.1 节的训练域验证法只在训练域内划分训练／验证子集并选择超参数；目标域验证被明确列为 oracle，不能作为有效基准。
- 因此，只用 LSPR23 合法验证区从冻结 `p` 网格选择，属于有来源的非 oracle 模型选择协议。
- 该论文没有幂平均或 XGBoost；训练域验证还假设训练与测试分布具有相似性。只有一个源年度时不能冒充多源域留一域交叉验证，源年选出的 `p` 也不保证目标年最优。

### 3.7 Hindy 等 2021

- [正式全文](https://arxiv.org/pdf/2103.04208)，物理第 6 页第 3 节：先把双向流分成流束，计算“流数量”和“源端口差”；第 6–7 页再把整束特征回填给束内每条流；第 8 页使用人工神经网络分类。
- 这说明“跨多条原始流提特征并附加到逐流分类行”已有非常直接的先例。
- 由于早期流得到的是整束最终流数和使用全部端口算出的差值，它不是 `i≤t` 的在线前缀。在本任务的因果合同下，照搬这种回填会构成未来信息使用。

### 3.8 Grinsztajn 等 2022

- 原件：`raw/papers/methodology/2022-Grinsztajn-Why-Tree-Based-Models-Outperform-Deep-Learning-Tabular.pdf`。
- 45 个数据集、统一随机搜索预算下，XGBoost／梯度提升树／随机森林是中等规模异质表格数据的强基线；第 5–8 页分析无信息特征、非平滑目标和旋转不变性。
- 第 3 页明确排除时间序列与流式数据，并把分类任务平衡化。因此它只能支持“XGBoost 应作为强表格基线”，不能支持跨流上下文或跨年度有效性。

### 3.9 Gehri 等 2023

- 原件：`raw/papers/datasets/locked-shields-related/2023-Gehri-Towards-Generalizing-ML-C2-Detection-CyCon.pdf`。
- 第 6.2 节、第 13–15 页把随机森林逐流预测按主机统计“预测为恶意的流数”，阈值扫描 `n∈{1,5,10,100}`；这是流分数到主机告警的直接安全领域先例。
- 它支持实体后处理的必要比较，但算子是计数阈值，不是归一化幂平均，`n` 也没有在源域按预注册协议选择。

### 3.10 Dijk 等 2026

- 原件：`raw/papers/datasets/LSPR24/ssrn-6597680.pdf`；DOI：[10.2139/ssrn.6597680](https://doi.org/10.2139/ssrn.6597680)。
- 第 11–16 页给出按开始时间排序、2-IP 无向对分组和最长 128 流切块；第 24 页（页内编号 23）给出 XGBoost 配置。
- 关键边界是：XGBoost 只在 OP 原始逐流表示上训练，2-IP／序列上下文仅供 GRU 与 Transformer。因此同一数据上的“上下文原始特征 XGBoost”没有被该论文实现。
- 该论文可支撑分组、排序、切块来源和原始 XGBoost 强基线，不能支撑把 CPA 移植到 XGBoost 后的效果。

### 3.11 Chen 与 Guestrin 2016

- [正式全文](https://arxiv.org/pdf/1603.02754)第 3 节给出近似分裂、加权分位数草图与直方图统计，第 4 节给出并行、缓存感知和外存系统设计。
- 它是 XGBoost 算法与可扩展系统的来源，但发表于现代 CUDA `hist`、`QuantileDMatrix` 和 `ExtMemQuantileDMatrix` 接口之前。
- 现代接口、显存格式和版本边界必须引用当前官方文档，不能从 2016 论文倒推出具体参数签名。

## 四、组件级综合

### 4.1 因果前缀跨流聚合

- **有全文依据的部分**：按同一实体或参照键汇集历史连接，计算计数、比例、均值等统计量，再作为当前连接的分类特征（Lee 与 Stolfo）；按实体汇总多流统计后交给树模型（Bilge 等）。
- **最接近的反例边界**：Hindy 等会把整束聚合值回填到每条流，说明“逐流附加跨流原始特征”不是新概念，同时展示了必须禁止的未来回填。
- **任务特定适配**：无向 2-IP 键、稳定时间排序、128 条边界、`i≤t` 且含当前流、只在合法原始数值字段上取前缀统计、与当前行拼接后交给 XGBoost，以及地址只分组不入模。没有全文把这些组成一次性放进 XGBoost。
- **尚待主方案冻结**：上下文究竟只取前缀均值，还是还暴露计数、差值、方差；是否严格保留 128 条重置。每多一个统计量都增加新适配，不能借 CPA 名称自动取得来源。

### 4.2 实体／主机级交通聚合与树模型上下文特征

- Bilge 等提供“实体聚合原始 NetFlow＋随机森林”的强证据；Gehri 等提供“逐流随机森林＋主机级计数后处理”的强证据。
- Dijk 等提供同一 LSPR 数据上的原始逐流 XGBoost 基线与 2-IP 序列构造，但二者没有相交。
- M-GRAD 是“XGBoost＋IP 风险汇总”的更晚边界，但输入单位已是 IP－窗口节点，聚合是严重度加权跨窗汇总，不能作为完整同构。

### 4.3 广义均值、幂平均与可学习范数池化

- 对非负逐流分数 `s_f`，实体幂平均为 `M_p(e)=((1/n_e)Σs_f^p)^(1/p)`；`p=1` 是算术均值，`p→∞` 是最大值。
- Gülçehre 等直接支撑 `p≥1` 的归一化 Lp 与反向传播学习阶数；Revaud 等支撑 GeM 与平均精确率目标联合学习；二者均不处理树模型实体分数。
- 当前第三章用 `p=exp(p_log)>0`。若 XGBoost 网格含 `0<p<1`，应称“幂平均”而非“Lp 范数”，并把该范围扩展标为任务特定选择。
- `p=∞` 应作为精确最大值分支，不应以任意大有限数冒充；若输入是 XGBoost 原始对数几率，负值会使非整数幂无定义，故 ELP 合同必须明确使用非负概率分数。

### 4.4 源年度非梯度幂指数选择

- 对骨干分支 `b∈{raw,context}` 的冻结源年验证分数，可写成：

  `p_b*=argmax_{p∈P} J_src-val(M_p(s^(b)))`。

- 这是有限超参数网格的训练域验证，不是梯度学习。相同选择目标、候选集、实体单位和并列裁决必须预先冻结；LSPR24 标签不得参与。
- 两个分支可用同一“选择算法”而得到不同 `p_raw*` 与 `p_context*`，仍不增加 XGBoost 拟合；若主方案要求两个分支共用一个数值，也必须在看目标年之前写死。
- 现有 `p=1.223554` 是从神经方案借给 XGBoost 分数的固定值。它可以作为“迁移固定指数”辅助锚点，但在没有独立源年选择收据时不能代表 XGBoost 版 ELP。
- 只有一个源年度时，选择协议应称“源年验证选择”，不能称多源域留一域选择。源年选择避免目标标签泄漏，但不保证跨年最优。

### 4.5 XGBoost GPU `hist` 与 `QuantileDMatrix`

- 2026-08-18 查阅的稳定文档版本为 3.4.1。[GPU 支持页](https://xgboost.readthedocs.io/en/stable/gpu/)给出的基本路径是 `device="cuda"`、`tree_method="hist"` 与 `QuantileDMatrix`。
- GPU `hist` 把量化数据存为压缩 ELLPACK；官方称通常约为浮点 CSR 空间的四分之一，但实际取决于特征数与每行非零数差异，不能把该比例当显存保证。
- [`QuantileDMatrix`](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.QuantileDMatrix)直接从输入生成量化数据以减少中间存储；验证／测试矩阵必须以训练矩阵作为 `ref`，`max_bin` 必须与训练参数一致。
- 当前 Dijk 配置的 `max_bin=256` 与官方默认相同。为公平对照，raw 与 context 必须用同一设备、树方法、`max_bin`、随机种子、行／列采样和拟合轮数；不能用历史 CPU 值充当唯一正式对照。

### 4.6 `DataIter`、外存与单卡并行

- [`DataIter`](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.DataIter)可服务量化矩阵、分布式和外存路径；跨批类别编码必须一致。
- [`ExtMemQuantileDMatrix`](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.ExtMemQuantileDMatrix)自 3.0 加入，官方仍标为实验性。GPU 外存默认把缓存放在主存，迭代器输入须在 GPU；磁盘后备可能让 GPU 比 CPU 更慢。
- [外存教程](https://xgboost.readthedocs.io/en/stable/tutorials/external_memory.html)明确指出当前重点是 NVLink-C2C 设备；PCIe 带宽会限制训练。因此优先顺序应为：内存内 `QuantileDMatrix` → `DataIter` 构造容量路径 → 只有内存门禁失败才评估外存，且先做版本与吞吐小样核验。
- `nthread` 控制 CPU 线程，不是“一张 GPU 同时训练两个模型”的开关；`num_parallel_tree` 会改变为每轮构造多棵树的增强随机森林语义，不能拿来并行两次冻结拟合。
- 官方多 GPU 入口是 Dask、Spark 和 PySpark 的分布式训练。单张 GPU 上两个独立进程并发没有官方加速保证，可能因显存、主存、PCIe 与上下文争用变慢或失败。
- 因而“尽可能 GPU 与并行”的可审计解释是：raw 与 context 两次拟合都使用相同 CUDA `hist`；只有联合显存与控制组内存门禁及实际吞吐门禁通过时才并发，否则串行 GPU 拟合，同时并行不争用显存的 CPA 物化、`p` 网格后处理和指标计算。这一调度结论是由官方接口边界推得的工程建议，不是官方性能保证。

### 4.7 两次拟合与四格映射

- `B0` 与 `ELP` 共享 raw XGBoost 的同一份逐流分数。
- `CPA` 与 `CPA+ELP` 共享 context XGBoost 的同一份逐流分数。
- ELP 只在冻结分数上做实体聚合和源年选阶，不反向改变树，也不要求第三、第四次 XGBoost 拟合。
- 四格是两份设计矩阵、两次模型拟合和四种评价映射；把它写成四次训练会错误放大预算并破坏公平性。

### 4.8 完整同构近邻

- 在上述四轮查询、2018—2026 直接近邻重点范围以及经典引用链中，**未检索到**同时满足下列五项的公开全文：
  1. 原始逐流表格特征；
  2. 同一网络实体内的严格 `i≤t` 前缀上下文；
  3. 上下文作为 XGBoost 的附加输入；
  4. 逐流分数用幂平均汇成实体分数；
  5. 幂指数只在源年度以非梯度协议选择。
- 最近邻分别只覆盖交集的一部分：Lee 与 Stolfo覆盖因果历史统计；Hindy 等覆盖原始跨流特征回填；Bilge 等覆盖聚合原始流＋树；Gehri 等覆盖树分数＋主机后处理；M-GRAD 覆盖 XGBoost＋IP 风险汇总；Gülçehre／Revaud 覆盖可学习幂平均；Gulrajani 与 Lopez-Paz 覆盖源域选择。
- 该结论只表示“在记录的查询式、数据库与日期内未命中”，不能写成绝对不存在或据此单独宣称原创。

## 五、仍需由冻结方案明确的选择

以下项目没有被现有全文唯一规定，必须在看目标年结果前写入冻结合同；它们是设计选择，不是文献事实：

1. **CPA 字段集**：仅取合法数值原始字段的前缀均值，还是同时加入前缀计数、当前值减前缀均值、方差等。新增任一统计量都应单列字段和消融。
2. **128 条边界**：Dijk 等给出最长 128 流的序列构造，但没有证明 XGBoost 上必须每 128 条重置。若保留，必须冻结稳定排序、同时间戳次序和重置语义；若取消，则属于新的长历史版本。
3. **幂指数搜索合同**：冻结候选集 `P`、源年验证目标 `J_src-val`、并列时的确定性规则、`p=∞` 精确分支，以及 raw／context 是否允许分别选择 `p`。
4. **选阶数据**：必须使用训练流程内独立的源年验证预测，不能在拟合样本的原位预测上选择 `p`，更不能查询 LSPR24 标签或目标分布统计。
5. **运行时版本**：当前证据对应 XGBoost 稳定文档 3.4.1；实施前须核验目标机实际版本、`QuantileDMatrix`／`ExtMemQuantileDMatrix` 签名、CUDA 可用性与训练／验证 `ref` 合同。
6. **单卡并发门禁**：是否并发 raw 与 context 两次拟合必须由联合峰值显存、主存和实测吞吐裁决。串行运行不改变科学设计，并发失败也不构成方法失败。

## 六、缺失全文与后续入库建议

- **付费墙阻塞：无。** 没有影响公式或原创边界裁决、却无法合法取得全文的论文，因此无需用户补充全文。
- 以下三篇核心来源使用正式开放全文完成核验，但受本任务独占输出边界限制，没有写入 `raw/wiki/Zotero`；后续如统一入库，建议文件名如下：
  - `2021-Hindy-Flow-Aggregation-Benign-Imitating-Attacks.pdf`，DOI：[10.3390/s21051761](https://doi.org/10.3390/s21051761)，[正式全文](https://arxiv.org/pdf/2103.04208)。
  - `2021-Gulrajani-LopezPaz-Lost-Domain-Generalization.pdf`，arXiv：[2007.01434](https://arxiv.org/abs/2007.01434)。
  - `2016-Chen-Guestrin-XGBoost-KDD.pdf`，arXiv：[1603.02754](https://arxiv.org/abs/1603.02754)。
- Zotero 只读核验没有发现上述三篇的可确认全文附件；这不等同于声称库中绝对不存在同题异名条目。

## 七、检查点

- **2026-08-18 初始检查点**：冻结研究范围、三份制品和全文门槛；随后先盘点本地原件、既有全文笔记与 Zotero。
- **2026-08-18 工程边界检查点**：补查 GPU `hist`、量化矩阵、外存／批量接口和单卡并行；不实施。四格固定为两次拟合加 ELP 后处理。
- **2026-08-18 全文检查点**：11 篇核心论文均取得可定位全文证据；8 篇有本地原件，3 篇由作者／会议正式开放全文核验；另有 5 篇作为边界或排除项。
- **2026-08-18 停止检查点**：最后一次新增核心全文后连续两轮直接同构复检没有新增核心全文；各关键部件已有强证据与边界证据，停止扩展检索。
- **2026-08-18 交付检查点**：结论限定为“部件有来源、组合为任务特定适配、当前检索未见完整同构”；所有效果判断保持“实验待证”。
