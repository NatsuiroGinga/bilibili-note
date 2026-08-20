---
title: "Domain-Adversarial Training of Neural Networks"
authors:
  - Yaroslav Ganin
  - Evgeniya Ustinova
  - Hana Ajakan
  - Pascal Germain
  - Hugo Larochelle
  - François Laviolette
  - Mario Marchand
  - Victor Lempitsky
year: 2016
date: 2026-08-19
journal: "Journal of Machine Learning Research, 2016, 17: 1-35"
source_pdf: "[[raw/papers/methodology/2016-Ganin-Domain-Adversarial-Training.pdf]]"
tags:
  - 域适应
  - 对抗训练
  - 不变表示
  - 类型/论文
key_finding: "用一个梯度反转层把标签预测器与域判别器耦合在同一个特征提取器上，使特征在保留标签判别力的同时对源目标域不可分；其理论依据是 Ben-David 等的 H-散度界，训练时**必须能取到目标域的无标签样本 T**（PDF p.7 起 §3 形式化）。"
aliases:
  - DANN
  - Ganin2016-DANN
related:
  - "[[2010-Ben-David-域适应不可能性定理]]"
  - "[[2023-Layeghy-DI-NIDS跨域入侵检测]]"
---

# DANN：神经网络的域对抗训练

## 一句话

把「源目标特征分布不可分」写成一个可反向传播的对抗目标，实现方式只是在标准网络里插一个梯度反转层。

## 题录与原件（全文核验）

- 原件：`raw/papers/methodology/2016-Ganin-Domain-Adversarial-Training.pdf`，35 页。
- 题录逐项从原件首页页眉核出：`Journal of Machine Learning Research 17 (2016) 1-35`，
  `Submitted 5/15; Published 4/16`。**卷期页码原件可读，无须联网。**
- 证据等级：**同行评议正式发表**（JMLR）。
- 本笔记补建缘由：该原件此前无 `wiki/papers/` 笔记（2026-08-19 轴二文献盘点发现）。

## 论文原结论（页级证据）

- 摘要与 §1（PDF p.1-3）：网络含三部分——特征提取器、标签预测器、域判别器。
  训练时最小化标签分类损失、**最大化**域判别损失；
  后者「与域判别器对抗地更新，从而鼓励在优化过程中出现域不变的特征」。
- 实现（PDF p.3）：唯一的非标准组件是一个「相当平凡的梯度反转层」，前向不改变输入，反向取负。
  整个模型仍可用标准反向传播训练。
- 理论依据（PDF p.7-9 §3）：基于 Ben-David 等 2006/2010 的 H-散度；
  该类方法的直觉性依据是「源与目标的表示应当不可区分」这一简单假设。
- **前提（PDF p.7）**：形式化中显式要求一个从目标分布独立同分布抽取的
  `unlabeled target sample T drawn i.i.d. from DT`。
- 实验：Amazon 评论情感数据、MNIST 等图像数据集，并与 mSDA 等对照。

## 本课题推论（非论文原结论）

- DANN 是段二「不变表示」子簇的规范出处。它的前提有两条对本课题不成立：
  1. 训练阶段必须取到目标域（次年）的无标签样本；本课题跨年度零样本设置不允许。
  2. 目标样本须与目标分布独立同分布；跨年度演习的攻击序列有强时间相关，i.i.d. 抽样不成立。

## 不可直接声称的内容

- 不得写成 DANN 在网络流量或跨年度任务上被验证有效。原文实验为情感分析与图像。
  网络入侵检测域的实测见 DI-NIDS（预印本），其结论是这类方法在 NIDS 上「收效有限」。

## 与本课题的关系

- 落 1.2.2 段二（域适应与不变表示子簇）。
- 短板证据：PDF p.7 的 `unlabeled target sample T` 是段末共同短板「必须取到目标域样本」的直接出处。
