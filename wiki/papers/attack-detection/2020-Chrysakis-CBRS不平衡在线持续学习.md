---
title: "Online Continual Learning from Imbalanced Data"
authors: [Aristotelis Chrysakis, Marie-Francine Moens]
year: 2020
date: 2026-09-09
journal: "ICML 2020, PMLR 119"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2020-Chrysakis-CBRS-Online-Continual-Learning-Imbalanced-Data.pdf]]"
tags:
  - 不平衡学习
  - 持续学习
  - reservoir
  - 类型/论文
key_finding: "CBRS 在未知类别先验、时间相关且严重不平衡的数据流中用类别平衡 reservoir 保持各类样本，区分记忆人口与回放训练。"
method: "Class-Balancing Reservoir Sampling（CBRS）"
baseline: "Reservoir、GSS 等记忆人口方法与回放训练组合"
aliases: [CBRS, Chrysakis2020]
---

# CBRS：类别平衡 reservoir

## 方法核心

- §2.2、算法 1：当类别尚未填满其记忆份额时优先保留，随后在类内执行 reservoir 选择；设计目标是在未知先验下使记忆尽量平衡。
- §3.1--§3.6 将记忆人口策略与回放训练策略分开比较，说明类别平衡、抽样和损失混合不能混成一个因素。
- 算法 1 使用类内计数 `m_c/n_c` 控制替换，并对持续被视为最大类的类别设置 `full` 状态；该历史计数语义不能直接替换成会随模型更新改变的决策角色。

## 对 LAMDA 的关系

- 是类别条件记忆的直接先例和必要对照。
- LAMDA 必须固定全程总容量 200；不能把 CBRS 的类别份额解释为每年新增 200 条，也不能使用未来全期类别频率。

## 不能直接声称

- CBRS 的平衡优势不能直接说明恶意类 FNR 下降且 FPR 不变；类别权重变化本身可能造成风险交换。
- 表 1 的 CIFAR-100、容量 1,000 对照中，Reservoir `28.1±1.2%`、CBRS `40.2±1.0%`；表 3 还显示加权回放并非所有数据集都更好。

## 一句话

CBRS 在不知道未来类别先验的情况下，用类别平衡 reservoir 应对时间相关且严重不平衡的数据流。

## 背景：问题的演进

传统 reservoir 追随总体流分布，在长尾流中可能丢失少数类别；CBRS 将记忆人口和后续回放训练拆开研究。

## 我的理解

CBRS 的关键贡献是记忆人口规则，不是风险约束。迁移到 LAMDA 时必须保持全程总容量 200，不能把“每类配额”变成额外内存。

## 与相关工作的关系

CBRS 是 LAMDA 条件覆盖记忆的基础先例，ECBRS 是其面向严重不平衡的扩展；MADAR 则进一步引入家族代表性。

## 疑问 / 待验证

- 类别平衡是否降低 LAMDA 的 FNR 而同时抬高 FPR？
- 与同配额随机记忆相比，收益来自覆盖还是正类暴露权重变化？

## 原始摘要

摘要原文保留在本地 PDF 第 1 页；此处只记录结构化转述。

## 文献信息

- PMLR：https://proceedings.mlr.press/v119/chrysakis20a.html
- PDF：https://proceedings.mlr.press/v119/chrysakis20a/chrysakis20a.pdf
