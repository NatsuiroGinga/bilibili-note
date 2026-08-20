---
title: "INSOMNIA: Towards Concept-Drift Robustness in Network Intrusion Detection"
authors:
  - Giuseppina Andresini
  - Feargus Pendlebury
  - Fabio Pierazzi
  - Corrado Loglisci
  - Annalisa Appice
  - Lorenzo Cavallaro
year: 2021
date: 2026-08-19
journal: "Proceedings of the 14th ACM Workshop on Artificial Intelligence and Security (AISec '21), November 15, 2021, Virtual Event, Republic of Korea. ACM. DOI 10.1145/3474369.3486864"
source_pdf: "[[raw/papers/attack-detection/drift/2021-Andresini-INSOMNIA-Concept-Drift-NIDS-AISec.pdf]]"
tags:
  - 概念漂移
  - 网络入侵检测
  - 主动学习
  - 半监督
  - 时间一致划分
  - 类型/论文
key_finding: "把 TESSERACT 的时间一致划分搬到网络入侵检测域后，不做更新的深度 NIDS 与 Kitsune 在 3 天测试数据上 F1 分别只有 0.0019% 与 0.0113%，几乎检不出任何攻击（PDF p.7 表 1）；恢复到 F1 约 80% 需要对 50% 的新流量做主动学习查询并由最近质心分类器给出伪标签。"
aliases:
  - INSOMNIA
  - Andresini2021-INSOMNIA
related:
  - "[[2019-Pendlebury-TESSERACT时空实验偏置与AUT]]"
  - "[[2021-Yang-CADE漂移样本检测与解释]]"
  - "[[2017-Jordaney-TRANSCEND漂移检测与共形评价]]"
---

# INSOMNIA：面向概念漂移鲁棒的网络入侵检测

## 一句话

INSOMNIA 把 TESSERACT 的时间一致评价协议引入网络入侵检测，先证明不更新的 NIDS 在时间外推下几乎归零，再用主动学习加伪标签把更新成本压下来。

## 题录与原件（全文核验）

- 原件：`raw/papers/attack-detection/drift/2021-Andresini-INSOMNIA-Concept-Drift-NIDS-AISec.pdf`，
  12 页，Royal Holloway 机构库 camera-ready 版。
- 题录取自原件第 1 页 `ACM Reference Format` 与版权块：AISec '21，November 15, 2021，
  Virtual Event, Republic of Korea；ACM, New York, NY, USA, 12 pages；
  `ACM ISBN 978-1-4503-8657-9/21/11`；`https://doi.org/10.1145/3474369.3486864`。
- **印刷卷内页码在 camera-ready 中未印**（ACM DL 著录为 pp. 111-122，
  本轮未打开 ACM DL 页面，**该页码须在正式著录前回 ACM DL 核定**）。
- 获取：https://pure.royalholloway.ac.uk/ws/files/43612548/insomnia_camera_ready.pdf ，2026-08-19 下载。
- 证据等级：**同行评议正式发表**（ACM 研讨会论文，与主会论文的评审强度不同，著录时应写明是 Workshop）。

## 论文原结论（页级证据）

- PDF p.1 摘要：用主动学习降低模型更新延迟，用标签估计降低标注开销，用可解释 AI 理解模型对分布变化的反应；
  为评价 INSOMNIA，作者**扩展 TESSERACT** 到网络入侵检测域。
- PDF p.1-2 动机：把两种近期方法（含自编码器族）用到修订版 CICIDS2017 上，
  这些方法假设数据独立同分布且不含缓解漂移的机制，
  结果 `identify almost zero attacks across the 3 days of test data (Table 1)`。
- PDF p.2 方法：以 DNN 为核心分类器，用主动学习只挑选新样本中的一部分；
  与「人工 oracle 标注」不同，INSOMNIA 是半监督的，用**最近质心邻居分类器**（Nearest Centroid, NC）
  为所选样本估计标签，从而在更新中避免人工标注。
- PDF p.2 与 §4：TESSERACT 的关键是保证时间一致的数据划分，训练数据严格早于测试数据；
  把它搬到网络流量域并不直接（攻击发生的时间粒度不同）。
- **PDF p.7 表 1（实测抄录）**，指标为 `F1(%)`、`AUT(F1)`、`TIME(min)`：

  | 选取比例 σ | 方法 | F1 (%) | AUT(F1) | TIME (min) |
  | --- | --- | ---: | ---: | ---: |
  | — | No-Update | **0.0019** | 0.035 | — |
  | — | Kitsune | **0.0113** | 0.009 | — |
  | 20% | US+Oracle | 74.57 | 32.73 | 445.24 |
  | 20% | INSOMNIA | 69.83 | 41.64 | 262.25 |
  | 50% | US+Oracle | 81.62 | 36.10 | 517.92 |
  | 50% | INSOMNIA | 80.88 | 42.39 | 428.39 |
  | 70% | US+Oracle | 90.85 | 44.99 | 587.96 |
  | 70% | INSOMNIA | 64.90 | 29.10 | 502.41 |

- 评价指标（PDF p.6）：除 F1 外使用 `AUT(F1)`，即 TESSERACT 提出的时间感知指标。

## 本课题推论（非论文原结论）

- 表 1 的 `No-Update` 行是本课题 1.2.2 段一最强的一条量化证据：
  **在时间一致划分下，不更新的深度 NIDS 检出率实际上归零**，而不是「有所下降」。
- 但同一张表也界定了 INSOMNIA 的适用前提：所有非零结果都以能在测试期取到 20%-70% 的新流量、
  并对其估计标签为条件。本课题跨年度零样本设置不满足该前提。
- σ=70% 时 INSOMNIA 反而低于 σ=50%（64.90 对 80.88），说明伪标签质量随查询量增大而恶化；
  这一非单调性是伪标签路线的固有风险，可在正文中作为「更新类方法不稳定」的证据，
  但须注明是单数据集单次实验。

## 不可直接声称的内容

- 不得把 `No-Update` 的 0.0019% 直接类比到 LSPR 跨年度任务。数据集（CICIDS2017 修订版）、
  攻击构成、时间粒度与本课题不同，只能作为**同类现象在另一数据集上的独立观测**。
- 不得写成「INSOMNIA 解决了 NIDS 的漂移问题」。它降低的是更新成本，不是取消更新。

## 与本课题的关系

- 落 1.2.2 段一（时间一致评价下的退化实证）与段二（更新类方法的代价）。
- 短板证据：PDF p.7 表 1 的全部非零行都绑定 σ>0，即必须取得测试期样本。
