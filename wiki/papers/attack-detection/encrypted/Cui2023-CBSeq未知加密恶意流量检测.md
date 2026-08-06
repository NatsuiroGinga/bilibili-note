---
title: "CBSeq: A Channel-Level Behavior Sequence for Encrypted Malware Traffic Detection"
authors: [Susu Cui, Cong Dong, Meng Shen, Yuling Liu, Bo Jiang, Zhigang Lu]
year: 2023
date: 2026-08-06
journal: "IEEE Transactions on Information Forensics and Security"
source_pdf: "[[raw/papers/attack-detection/encrypted/2023-Cui-CBSeq-Encrypted-Malware.pdf]]"
tags:
  - 加密恶意流量检测
  - 未知恶意流量
  - 行为序列
  - 类型/论文
key_finding: "以通信信道为单位组合包数、到达间隔和端口行为序列，比单流统计特征更能保持未知恶意流量检测性能；未知集 AUC 为 0.889。"
method: "DBSCAN 聚合相似信道，Word2Vec 嵌入四类行为序列，MSFormer 多序列融合分类。"
baseline: "Joy、Joy-enhanced、CIC-Flow、DANTE、TCC；序列移除与单序列分析。"
zotero_key: "WI45ZNS8"
aliases:
  - Cui2023-CBSeq
---

# CBSeq: A Channel-Level Behavior Sequence for Encrypted Malware Traffic Detection

## 一句话

论文把单流提升为信道级行为序列，并在已知六类之外的恶意流量上测试，提供了比“跨加密协议”更直接的未知攻击论证路径。

## 问题与方法

- 用具有相似活动的通信信道作为检测对象，构造包数、到达间隔、源端口和目的端口四类序列。
- DBSCAN 聚合信道，Word2Vec 学习离散行为嵌入，MSFormer 的四个子编码器分别建模并融合分类。
- 对 IP、MAC 与时间戳做随机化处理，降低明显采集标识的影响。

## 数据与划分

- Benign-ALL：企业网络 28 台设备、45 GB、32,860 条信道流量。
- CTU-6：Zeus、Emotet、Miuref、Trickbot、Dridex、Downloadguide 六类已知恶意流量。
- CTU-ALL：其余 328 个恶意样本、75,781 条信道流量，用于未知恶意检测。
- 未知测试在 CTU-6 与 50% Benign-ALL 上训练，在 CTU-ALL 与另 50% Benign-ALL 上测试；同一信道只能位于训练或测试一侧。
- 各实验下采样为平衡数据，随机测试抽样重复十次取平均。
- 证据：PDF 第 8-9 页表 1 与第 5.A 节；第 11 页第 5.C 节。

## 主要结果

- 已知检测中 CBSeq 六类平均 AUC 0.994、平均 TPR 0.973、平均 FPR 0.016。
- 已知二分类 AUC 0.984，未知恶意检测 AUC 0.889±0.009；未知检测比 TCC 高 0.160。
- 移除任一行为序列都会以不同程度降低性能，说明四类序列提供互补信息。
- 证据：PDF 第 11 页表 2；第 12 页图 8；第 13 页表 3。

## 限制

- 未知恶意集与已知集来自同一长期项目，且论文未给出按捕获时间或基础设施严格隔离的证明。
- 平衡采样改变真实低基率部署条件。
- “跨协议”来自协议无关行为表示与混合协议数据，不是控制恶意框架后仅替换传输/加密协议的因果比较。
- 未知任务无法做交叉验证，结果依赖十次随机测试抽样。

## 与本课题的边界

- **论文原结论**：信道级行为序列在其已知与未知恶意检测设置中优于基线。
- **可迁移机制**：按信道分组防泄漏、已知/未知恶意分离、行为序列消融。
- **不可直接声称**：论文的未知检测不能被改写为纯粹的跨加密泛化。
- **仍需验证**：按采集日期、家族与基础设施共同分组后的性能，以及低基率精确率。

## 文献信息

- DOI：[10.1109/TIFS.2023.3300521](https://doi.org/10.1109/TIFS.2023.3300521)
- arXiv：[2307.09002](https://arxiv.org/abs/2307.09002)
- Zotero 条目键：`WI45ZNS8`

