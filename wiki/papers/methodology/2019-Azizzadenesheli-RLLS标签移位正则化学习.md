---
title: "Regularized Learning for Domain Adaptation under Label Shifts"
authors:
  - Kamyar Azizzadenesheli
  - Anqi Liu
  - Fanny Yang
  - Animashree Anandkumar
year: 2019
date: 2026-08-19
journal: "International Conference on Learning Representations (ICLR) 2019；原件首页印 Published as a conference paper at ICLR 2019；arXiv:1903.09734v1"
source_pdf: "[[raw/papers/methodology/2019-Azizzadenesheli-RLLS-arXiv1903.09734.pdf]]"
tags:
  - 标签移位
  - 域适应
  - 重要性权重
  - 泛化界
  - 类型/论文
key_finding: "先用有标签源数据与无标签目标数据估计重要性权重 q(y)/p(y)，再在加权源样本上训练分类器；论文自述这是标签移位问题上第一个「目标域标签不可得」条件下的泛化界（PDF p.1 摘要），并针对小样本区提出正则化权重估计器。"
aliases:
  - RLLS
  - Azizzadenesheli2019-RLLS
related:
  - "[[2018-Lipton-BBSE标签移位]]"
  - "[[2020-Alexandari-MLLS校准]]"
---

# RLLS：标签移位下域适应的正则化学习

## 一句话

RLLS 承接 BBSE 的黑盒重要性权重路线，补上两件事：小样本下权重估计误差的正则化控制，以及最终分类器的泛化界。

## 题录与原件（全文核验）

- 原件：`raw/papers/methodology/2019-Azizzadenesheli-RLLS-arXiv1903.09734.pdf`，26 页。
- 首页第一行印 `Published as a conference paper at ICLR 2019`，第二行 `arXiv:1903.09734v1 [cs.LG] 22 Mar 2019`。
  **载体从原件核出，非二手来源。** ICLR 无卷期页码。
- 获取：https://arxiv.org/pdf/1903.09734 ，2026-08-19 下载。
- 证据等级：**同行评议正式发表**（ICLR 2019 会议论文）。

## 入库缘由（重要）

本仓库既有 `raw/papers/methodology/2019-Azizzadenesheli-RLLS.pdf`（346,638 字节）**文件损坏**，
`pdfinfo` 报 `Invalid XRef entry 0 / Couldn't read xref table`，无法抽取任何文本，因而无法全文核验。
按 `raw/AGENTS.md` 原件层「只增不改」，本轮**不覆盖、不删除**损坏件，
另存可读副本为 `2019-Azizzadenesheli-RLLS-arXiv1903.09734.pdf`。
正式引用一律以本可读副本为准。

## 论文原结论（页级证据）

- PDF p.1 摘要：提出 Regularized Learning under Label shifts（RLLS）；
  先用有标签源数据与无标签目标数据估计重要性权重，再在加权源样本上训练分类器；
  推导出的泛化界 `is the first generalization bound for the label-shift problem where
  the labels in the target domain are not available`。
- PDF p.1-2 §1：区分两类移位——协变量移位（`p(x)` 变而 `p(y|x)` 不变）与
  标签移位（`p(y)` 变而 `p(x|y)` 不变）；并指出标签移位在计算上比协变量移位更可处理。
- PDF p.2：明确前作 Lipton 等（BBSE）用混淆矩阵估计权重，可容忍黑盒分类器有偏、未校准、不准确；
  但遗留三个问题——低样本下如何估权、泛化保证是什么、以及相应的实践方法。
- 贡献：(1) 指出既有权重估计在小样本下方差可任意大；
  (2) 提出正则化方法补偿低目标样本量下的高估计误差；
  (3) 给出 RLLS 分类器的泛化界。
- 实验：CIFAR-10 与 MNIST。大目标样本量与大移位下全量施加正则权重效果最好；
  小样本下部分施加正则权重也能带来至少 10% 的准确率提升（PDF p.2）。

## 本课题推论（非论文原结论）

- RLLS 与 BBSE、MLLS 同属「先估 `q(y)/p(y)` 再重加权」路线，
  三者都**要求能取到目标域的无标签样本**，且都假设 `p(x|y)` 在源与目标间不变。
- 本课题跨年度任务中，次年演习的攻击实现与网络布局都变了，`p(x|y)` 不变这一条并不显然成立；
  这是标签移位族在本任务上的第一处前提风险。

## 不可直接声称的内容

- 不得写成 RLLS 在网络流量或安全任务上被验证过。原文实验只有 CIFAR-10 与 MNIST。
- 不得据本笔记声称 Saerens 等 2002 的内容——本仓库尚无该原件。

## 与本课题的关系

- 落 1.2.2 段二（标签移位与先验校正子簇）。
- 短板证据：PDF p.1 摘要与 §1，其全部方法链条都以「取得目标域无标签样本」为输入。
