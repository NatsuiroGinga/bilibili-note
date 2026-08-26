---
title: "Toward Real-World IoT Security: Concept Drift-Resilient IoT Botnet Detection via Latent Space Representation Learning and Alignment"
authors: [Hassan Wasswa, Timothy Lynar]
year: 2025
date: 2026-08-26
journal: "arXiv 2512.22488v1（2025-12-27，未见会议/期刊出处）"
source_pdf: "[[raw/papers/attack-detection/2025-Wasswa-IoT-Botnet-Latent-Space-Alignment-Drift.pdf]]"
tags:
  - IoT僵尸网络
  - 概念漂移
  - 潜空间对齐
  - 变分自编码器
  - 图注意力网络
  - 表示层适应
  - 类型/论文
key_finding: "把抗漂移完全放在表示层：冻结历史分类器不动，只训练一个 MLP 对齐模型把新域潜向量的均值方差拉到历史潜空间（最小化对角高斯 2-Wasserstein 距离），跨域准确率从 59.82% 回到 96.56%；对本课题属正交路线，可用于论证「训练层聚合＋决策层前缀」这一组合未被表示层主流路线占用。"
method: "历史域 VAE 编码器 EH → kNN(k=3) 建图 → GAT 分类器 CH（冻结）；新域 VAE 编码器 ES → MLP 对齐模型（最小化 Wasserstein 距离）→ 送入 CH"
baseline: "无对齐的跨域直接分类（同一 CH）"
aliases:
  - Wasswa2025-LatentAlignment
related:
  - "[[2023-Layeghy-DI-NIDS跨域入侵检测]]"
  - "[[2023-Lai-ContexTDA上下文异常域适应]]"
---

# IoT 僵尸网络的潜空间表示学习与对齐抗漂移

> Wasswa & Lynar，2025，arXiv 2512.22488v1 · 6 页 · UNSW Canberra · SHA-256 `5d6d7e768ba7a16aaab41e577e173339e5c0ffa56e758238c525111aef296bf9`

## 证据等级

**E3 全文级（但引用强度须降档，理由见下）**。原件已下载（HTTP 200，382,509 字节），6 页全文逐节读完。

**本篇存在多处可核验的编辑与表述缺陷，引用时必须同时披露**：

1. PDF 元数据 `Title` 仍为 `Paper Title (use style: paper title)`，未替换 IEEE 模板占位符。
2. 第 II-A 节末尾残留整段 IEEE 模板说明文字（关于 A4 与 US letter 纸型的模板提示），夹在两段学术论述之间。
3. **表 1 的 Recall 公式印为 `TP / (TP + TN)`，正确应为 `TP / (TP + FN)`**。这解释了为何全文报告的 recall 与 accuracy 数值完全相同（对齐前 `59.82%`/`59.82%`，对齐后 `96.56%`/`96.56%`）——所报「recall」实际等同于加权平均准确率，不是召回率。
4. 正文引用编号与参考文献表系统性错位：正文写 ACI-IoT-2023 `[50]`、IoT-NID `[51]`、INSOMNIA `[48]`，但参考表 `[50]` 是 Cross-modal variational alignment、`[51]` 是 UASDAC、`[48]` 是 Cross-domain character recognition；两个数据集的真实条目在 `[58]`（DOI `10.21227/qacj-3x32`）与 `[59]`（DOI `10.21227/q70p-q449`），INSOMNIA 在 `[52]`。
5. 无同行评审出处、无多种子、无置信区间、无超参搜索说明、无对齐模型结构细节（只说是 MLP）。

结论：**本篇可用于证明「表示层对齐」这条路线的存在与大致效果量级，不可用于支撑任何精确数值比较或统计显著性论断。**

## 一句话

用一个轻量 MLP 把新域的潜空间分布（均值、标准差）拉到历史域潜空间，从而让冻结的历史分类器无需重训即可处理漂移后的流量；代价是抗漂移能力完全依赖对齐模型，而对齐模型本身仍需要新域数据来训练。

## 背景：问题的演进

第 I 节的问题链：IoT 僵尸网络检测模型多假设平稳流量，而真实 IoT 环境中攻击脚本演化与设备异构导致概念漂移（第 I 节引 `[35]`）。已有自适应方法（`[34, 40, 42]`）靠频繁重训，带来灾难性遗忘、模型不稳定与高计算成本。此外，多数模型把每个攻击实例视为独立，忽略了 IoT 僵尸网络（尤其来自多个僵尸节点的 DDoS）的实例间关系，故引入 GNN。

第 II-B 节梳理漂移应对的既有工作，值得注意的三条定位：`[41]` 只分析漂移不给缓解方案；`[34]` 用 Kafka-Spark-MongoDB 管线在致漂移实例上重训，准确率从 `97.8%` 提到 `99.46%`，但重训昂贵且只在有限攻击变体上验证；`[35]` 用 PCA 漂移检测＋Hedge 加权在线 DNN，只在单一数据集 DS2OS 上评估。作者的定位是：**只更新对齐模型，不更新分类器**。

## 方法核心（第 III 节）

四步流程（图 1）：

1. 在历史 IoT 僵尸网络流量上训练 VAE，用其编码器 `EH` 把高维数据投到低维潜空间。
2. 用 **kNN（`n_neighbors=3`，欧氏距离）** 把低维历史数据集转成图结构，训练 **GAT** 做节点（流量）分类，得到分类器 `CH`。
3. 在新域（异构网络、含漂移）流量上训练第二个 VAE，用其编码器 `ES` 降维。
4. 训练对齐模型，把新域潜向量对齐到历史潜向量。

部署时：新流量 → `ES` → 对齐 → 建图 → `CH` 分类。**`CH` 全程不重训。**

### 对齐目标（第 III-A 节，式 (1)）

对齐模型是一个 MLP，训练目标是最小化两个潜空间分布之间的 Wasserstein 距离：

```
Wd = ( ||µH − µS||² + ||σH − σS||² )^(1/2)        式 (1)
```

其中 `µH, σH` 是历史潜空间分布的均值与标准差，`µS, σS` 是新数据潜空间分布的均值与标准差。

技术核对：该式正是**对角协方差高斯之间 2-Wasserstein 距离**的闭式解，形式无误。但它只约束一阶与二阶边缘矩，不约束潜空间的相关结构，这是该对齐的机制上界——论文未讨论这一点。

全部实验的潜空间维度固定为 `8`（第 IV-B 节）。

## 数据集与实验设置（第 IV 节）

二分类（Normal / Attack），两个公开数据集：

- **ACI-IoT-2023**（Army Cyber Institute，模拟家庭 IoT，Home Assistant 管理，有线＋无线段，5 天记录，含侦察、DDoS、欺骗、暴力破解）。
- **IoT-NID / IoT Network Intrusion Dataset**（无线 IoT 环境，监听模式无线网卡抓包，42 个 pcap 文件，含 ARP 欺骗、SYN 洪泛、侦察扫描、Mirai 式 UDP 洪泛与 HTTP 暴力破解）。

预处理（第 IV-A 节）：清洗异常、重复、缺失与错误值；**剔除 `Flow ID`、`Src IP`、`Dst IP`、`Timestamp` 四列**，理由是不贡献有意义模式且可能引入偏置。

漂移演示实验（第 IV-B 节）：在 ACI-IoT-2023 上训 `CH`，用 `EH` 把 IoT-NID2024 测试样本投到低维后**不做对齐**直接送 `CH`；再把两数据集角色互换重复一次。

对齐实验（第 IV-C 节）：ACI-IoT-2023 作历史域，IoT-NID2024 作当前域，按上述四步执行。

## 主要数字结果（第 V 节，精确抄录）

**同源（无漂移）基线**：

- 训练与测试均来自 ACI-IoT-2023：准确率 `98.46%`
- 训练与测试均来自 IoT-NID：准确率 `97.93%`

**跨域（漂移）退化**：

- ACI-IoT 训练 → IoT-NID 测试：准确率 `59.82%`
- IoT-NID 训练 → ACI-IoT 测试：准确率 `53.11%`

**潜空间对齐后（ACI-IoT 训练 → IoT-NID 测试）**：

| 指标 | 对齐前 | 对齐后 |
| --- | --- | --- |
| Accuracy | 59.82% | **96.56%** |
| Precision | 70.65% | **96.57%** |
| Recall（按论文口径，实为加权准确率） | 59.82% | **96.56%** |
| F1-score | 54.83% | **96.56%** |

论文只报告了 ACI→IoT-NID 这一个方向的对齐结果；**反方向（IoT-NID→ACI，退化到 `53.11%`）的对齐结果全文未给出**。

第 VI 节自陈局限：当前框架**没有集成漂移检测工具**，即无法判断何时需要更新对齐模型；未来工作是引入漂移检测并研究对齐模型的自适应更新策略。

## 与本课题的关系

### ① 它的漂移应对机制放在哪一层？

**纯表示层。** 分类器 `CH`（GAT）与其训练目标全程冻结不动，唯一被更新的对象是位于编码器与分类器之间的 MLP 对齐模块。决策层（阈值、打分方式、告警逻辑）没有任何改动；训练流程层刻意不动（论文全篇的卖点就是「避免分类器重训」）。

附带说明：论文的 kNN 建图（`k=3`，欧氏距离）是**特征空间近邻图**，不是网络实体交互图，与 MalMoE 的 IP 交互图性质完全不同，也**不构成实体级聚合**。

### ② 对「实体级聚合在训练层＋因果前缀统计量在决策层」是支持、矛盾还是无关？

**无关（正交），但有一处间接的负面参照价值。**

**无关的依据**：本篇的机制落点（表示层对齐）与本课题的两个落点（训练层聚合、决策层前缀统计量）不重叠。它既没有把聚合放进训练目标，也没有在决策层引入任何统计量。它甚至主动删掉了时间戳列（第 IV-A 节），因此**从数据准备阶段就排除了任何时序或前缀机制的可能**。它不支持也不反驳本课题的机制假设。

**正交路线的用途**：本篇与 MalMoE 一起，说明近期漂移文献的机制主流确实是「表示层对齐 / 表示层鲁棒化」。本课题把改造放在训练层与决策层，是这条主流之外的空间。这条论断此前在 `notes.md` 第三节只有题录级支撑，现在两篇全文可以把它升到全文级——但表述必须限定为「本次检索所及的 4 篇近期漂移工作中未出现」，不能写成「文献中不存在」。

**间接负面参照**：本篇的漂移是**跨数据集/跨网络配置**的域漂移（ACI 家庭 IoT 实验床 vs. IoT-NID 无线环境），不是同一环境的跨时间漂移。它把两个不同来源的数据集当作「历史」与「当前」，这在方法学上把域差异与时间漂移混为一谈。本课题的 LSPR23→LSPR24 是**同一演习系列的跨年**，时间语义明确，反而比本篇更干净。引用时不宜把本篇的 `59.82%` 塌缩当作「跨年漂移导致的退化」证据，只能当作「跨网络配置导致的退化」证据。

## 疑问 / 待验证

- 对齐模型的训练需要新域数据，那么在漂移刚发生、新域样本尚少时如何对齐？论文未讨论，且自陈缺漂移检测器，意味着「何时对齐」这一决策悬空。
- 只对齐一阶与二阶边缘矩（式 (1)），当漂移改变的是潜空间的相关结构而非边缘分布时，对齐应当失效。论文没有构造这类反例。
- 对齐后四个指标几乎相同（`96.56 / 96.57 / 96.56 / 96.56`）在类别不均衡的二分类中不寻常，结合表 1 的 Recall 公式错误，很可能全部是加权平均口径。不要在本课题正文中引用其单个指标数值。

## 原始摘要

> ... this paper proposes a scalable framework for adaptive IoT threat detection that eliminates the need for continuous classifier retraining. The proposed approach trains a classifier once on latent-space representations of historical traffic, while an alignment model maps incoming traffic to the learned historical latent space prior to classification...

## 文献信息

- arXiv：[2512.22488](https://arxiv.org/abs/2512.22488)（v1，2025-12-27 提交，primary cs.LG）
- 机构：University of New South Wales, Canberra
- 相关前作（同一作者组）：Knowledge-Based Systems (2025) 114749 "Latent space alignment for robust detection of IoT botnet attacks in non-stationary environments"（参考文献 `[47]`，本篇为其会议短版或衍生）
- 本地原件：`raw/papers/attack-detection/2025-Wasswa-IoT-Botnet-Latent-Space-Alignment-Drift.pdf`
