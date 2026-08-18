---
title: "E-GraphSAGE: A Graph Neural Network based Intrusion Detection System for IoT"
authors: [Wai Weng Lo, Siamak Layeghy, Mohanad Sarhan, Marcus Gallagher, Marius Portmann]
year: 2021
date: 2026-08-13
journal: "IEEE/IFIP Network Operations and Management Symposium (NOMS)，布达佩斯，2022 年 4 月（第 1 页录用声明）；arXiv 2103.16329v8 [cs.NI]，2022 年 1 月 11 日"
source_pdf: "[[raw/papers/methodology/multiple-instance/2021-Lo-EGraphSAGE-GNN-NIDS.pdf]]"
sha256: "85a5330e9339c7c9ffd8432fc3fb4700bbe27f675a23dc831b3d6a27d31c7833"
doi: "arXiv:2103.16329；DOI 未在原件中定位"
tags:
  - 图神经网络
  - 入侵检测
  - NetFlow
  - 邻域聚合
  - 实体级上下文
  - 类型/论文
aliases:
  - Lo2021-E-GraphSAGE
  - E-GraphSAGE
  - 边特征GraphSAGE入侵检测
key_finding: "把 NetFlow 记录建成「端点为节点、流为边」的图，用均值聚合把邻域边特征汇入节点嵌入，再把两端节点嵌入拼接成边嵌入做流分类：二分类在四个数据集上 F1 为 1.00 / 0.97 / 0.99 / 1.00（表 II 与表 III，第 7 页）；但同一模型在多分类下大幅退化，NF-BoT-IoT 加权 DR 仅 78.16%、NF-ToN-IoT 仅 67.16%，且 NF-ToN-IoT 的 DoS 与 XSS 两类检出率为 0.00%（表 IV、表 V，第 7 页）。"
method: "扩展 GraphSAGE：输入改为边特征，节点特征初始化为全 1 向量，邻域聚合函数改为对邻接边特征求均值（K=2 跳），最终边嵌入为两端节点嵌入的拼接，经 softmax 做边（流）分类"
baseline: "各数据集文献最优结果：BoT-IoT 上 XGBoost（F1 0.99）、NF-BoT-IoT 与 NF-ToN-IoT 上 Extra Tree Classifier（0.97 / 1.00）、ToN-IoT 上集成方法（0.95）"
related:
  - "[[2026-ElMahdaouy-上下文感知NetFlow入侵检测综述]]"
  - "[[2016-Pevny-树结构多示例判别模型]]"
  - "[[2023-Layeghy-DI-NIDS跨域入侵检测]]"
  - "[[2019-Pendlebury-TESSERACT时空实验偏置与AUT]]"
---

# E-GraphSAGE：面向 IoT 入侵检测的边特征图神经网络

> Lo、Layeghy、Sarhan、Gallagher、Portmann（昆士兰大学），IEEE/IFIP NOMS 2022，9 页。

## 一句话

把「一条流」放回它所处的通信图中，用邻居边的均值给端点造上下文，再用两端上下文拼接来判定这条流——这是本课题「实体级聚合」在图形式下的对应物；但论文的评估协议（随机 70/30 划分、极端类别倾斜、无跨数据集测试）决定了它的高分不能当作迁移能力的证据。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：E-GraphSAGE: A Graph Neural Network based Intrusion Detection System for IoT
- 单位：University of Queensland，信息技术与电气工程学院，布里斯班（第 1 页）
- 会议：第 1 页声明「This paper has been accepted for publication in IEEE/IFIP Network Operations and Management Symposium, Budapest, Hungary, April 2022」；arXiv 2103.16329v8 [cs.NI]
- 原件：`raw/papers/methodology/multiple-instance/2021-Lo-EGraphSAGE-GNN-NIDS.pdf`

## 核心方法

- **图构建**（第 5 页 IV.B.1）：用 4 个流字段定义边——源 IP、源端口、目的 IP、目的端口；前两个构成源节点，后两个构成目的节点，其余字段全部作为**边特征**。由于 NIDS 数据集只有流特征、没有节点特征，节点特征初始化为**全 1 向量**，维度等于边特征数（算法 1 第 1 行）。
- **防标签泄漏的处理**（第 5 页）：把原始源 IP 随机映射到 172.16.0.1–172.31.0.1 区间，理由是很多 NIDS 数据集中攻击只来自少数几个源 IP，不随机化会让源 IP 成为「无意的标签」。
- **边特征邻域聚合**（公式 (4)(6)，第 4–5 页）：h^k_{N(v)} = mean{ e^{k-1}_{uv} : u ∈ N(v), uv ∈ E }，即对节点 v 的邻接**边**特征取均值；再与上一层节点嵌入拼接、过权重矩阵与 ReLU 得到 h^k_v。这是对原始 GraphSAGE 只用节点特征的关键改动。
- **边嵌入与分类**（公式 (5)，第 5 页；第 6 页）：z_{uv} = CONCAT(z_u, z_v)。实现中 K=2、每层 128 隐单元，故边嵌入为 256 维；ReLU、两层间 dropout 0.2、交叉熵损失、Adam lr=0.001，采用全邻域采样。
- **复杂度**（第 5 页 IV.A.2）：时间复杂度上界 O(eKnd²)，空间复杂度 O(beKd + Kd²)，b 为 batch size。

## 关键数字（含页码/表号）

- **数据集（第 6 页 V）**：BoT-IoT 共 3,668,522 条流，其中良性仅 **477 条（0.01%）**、攻击 3,668,045 条（99.99%）；ToN-IoT 共 22,339,021 条流，良性 796,380 条（3.56%）、攻击 21,542,641 条（96.44%）；NF-ToN-IoT 共 1,379,274 条流（攻击 80.4%、良性 19.6%）；NF-BoT-IoT 共 600,100 条流（攻击 97.69%、良性 2.31%）。
- **划分（第 7 页 VI.A）**：**每个数据集随机取 70% 训练、30% 测试**；ToN-IoT 因体量太大只用随机抽样的 10% 子集。
- **二分类结果（表 II，第 7 页）**：BoT-IoT 准确率 99.99%、精确率 1.00、F1 1.00、DR 99.99%、FAR 0.00%；NF-BoT-IoT 93.57% / 1.00 / 0.97 / 93.43% / 0.38%；ToN-IoT 97.87% / 1.00 / 0.99 / 97.86% / 1.92%；NF-ToN-IoT 99.69% / 1.00 / 1.00 / 99.85% / 0.15%。
- **与文献最优对比（表 III，第 7 页）**：BoT-IoT F1 1.00 对 XGBoost 0.99；ToN-IoT 0.99 对集成方法 0.95；NF-BoT-IoT 0.97 与 Extra Tree 持平；NF-ToN-IoT 1.00 与 Extra Tree 持平。即**只在两个数据集上超过最优基线，另两个持平**。
- **多分类退化（表 IV、表 V，第 7 页）**：BoT-IoT 加权平均 DR 99.99%、F1 1.00，但同源的 NetFlow 版 NF-BoT-IoT 只有 **78.16% / 0.81**，其中 DDoS 检出率 40.82%、DoS 57.13%；ToN-IoT 加权 86.78% / 0.87，NF-ToN-IoT 仅 **67.16% / 0.63**，其中 **DoS 0.00%、XSS 0.00%**、Scanning 15.32%、Password 19.92%；而原始 ToN-IoT 上 Backdoor 检出率仅 **5.06%**（F1 0.08）。
- **作者对特征集敏感性的说明（第 7 页）**：原始数据集与其 NetFlow 版本描述的是同一批网络事件，但由于特征集不同，分类器性能可能显著不同（引自 Sarhan 等）。
- **未给出的项**：全文没有 AP / PR-AUC、没有固定误报率下的检出率、没有时间序划分、没有跨数据集或跨年度评测、没有多次种子的方差或置信区间。

## 与本课题（LSPR23→LSPR24 加密恶意流量跨年度迁移）的关系

第 1 条是论文原结论，第 2–5 条是本课题推论。

1. **可直接引用**：把流数据建成「端点为节点、流为边」的图并用邻域聚合引入上下文的具体算法（算法 1 与公式 (4)(5)(6)，第 4–5 页）；源 IP 随机化以避免 IP 成为无意标签（第 5 页）；同一批网络事件在不同特征集下分类性能可显著不同（第 7 页）。
2. **与本课题实体定义的直接关系**：本课题的实体是「2-IP 无向对」，本文的节点是「IP+端口」二元组、边是流。**本文的均值邻域聚合与本课题的实体级平均在数学形式上几乎相同**——都是对与某实体关联的所有流特征取均值——差别只在本文把聚合结果用于**恢复单条流的判定**，而本课题直接在实体层出结论。因此本文可作为「邻域/实体均值聚合」这一机制的正式文献坐标。
3. **本课题应当补的对照**：本文提供了一个现成的、开销可接受的强化版聚合形式（两跳邻域 + 两端拼接）。本课题目前只做一跳、只对 2-IP 对内取均值。**「两跳邻域聚合是否再涨 AP」是可执行的最小实验**，但要注意本课题是跨年度零样本，图结构在 LSPR24 上完全重建，**不能沿用 LSPR23 的节点嵌入**。
4. **本文的数字不能作为性能参照，理由有三**（均可在原件核实）：① 随机 70/30 划分，无时间顺序，按 [[2026-ElMahdaouy-上下文感知NetFlow入侵检测综述]] 第 12 页的清单属明确的评估缺陷；② 类别比例极端且方向与本课题相反（BoT-IoT 良性仅 0.01%，攻击占 99.99%），F1 与准确率在这种比例下几乎无判别力；③ 多分类结果显示同一模型在特征集变化后崩塌（NF-ToN-IoT 上两类检出率为 0.00%），说明其高分强依赖具体数据集。
5. **对「(b) 分布漂移下的退化」的间接价值**：表 IV 与表 V 的「原始格式 vs NetFlow 格式」对比（99.99% → 78.16%，86.78% → 67.16%）是一次**非受控的特征域偏移测量**——同样的网络事件、不同的特征提取管线，加权检出率掉 20 个百分点以上。这可作为本课题主张「特征/采集口径变化本身就会造成大幅退化」的辅助引证，但**它不是时间漂移，也没有控制其他变量**，只能作为旁证。

## 局限（不可直接声称的内容）

- 随机划分、无时间序切分、无跨数据集验证，因此**不能声称该方法具备跨域或跨年度泛化能力**；论文自己用的措辞是在四个数据集上都表现稳健，属同分布内的结论。
- 只报告准确率、精确率、F1、召回与 FAR，缺少不平衡场景更合适的 AP / PR-AUC 与固定 FPR 下的检出率。
- 无重复实验与方差报告，单次结果。
- ToN-IoT 只用了 10% 随机子集，抽样方式对图结构的影响未讨论。
- 节点特征取全 1 向量意味着**节点本身不携带信息，全部信息来自边特征的邻域平均**；论文未做「不聚合（纯逐流 MLP）」的同架构消融，因此无法从本文判断聚合本身贡献了多少。

## 可引用的逐字原文（≤15 词）

- 「flow endpoints are mapped to graph nodes, and network traffic flows are mapped to the graph edges」（第 1 页）
- 「The random mapping avoids the potential problem of the source IP addresses providing an unintentional label」（第 5 页）

## 证据记录

- 来源类型：完整论文（`pdftotext -layout` 抽取 9 页全文，逐页核对页码；表 II–V 数值从原件表格抄录）
- 支持：边特征邻域聚合算法；端点建图方式；源 IP 随机化的必要性；特征集变化引起的性能落差
- 限制：随机划分、无跨数据集/跨时间评测、指标不适配极端不平衡、无聚合消融、单次实验
- 论断强度：有支持（机制与算法）/ 旁证（特征域偏移下的退化）/ 不可引用（作为迁移性能参照）

## 文献信息

- IEEE/IFIP NOMS 2022（第 1 页录用声明）；arXiv：<https://arxiv.org/abs/2103.16329>
- DOI：未在原件中定位
- 本地 PDF SHA-256：`85a5330e9339c7c9ffd8432fc3fb4700bbe27f675a23dc831b3d6a27d31c7833`
