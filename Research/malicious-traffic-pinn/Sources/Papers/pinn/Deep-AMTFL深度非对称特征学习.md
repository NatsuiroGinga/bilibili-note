---
title: "Deep Asymmetric Multi-task Feature Learning"
authors:
  - Hae Beom Lee
  - Eunho Yang
  - Sung Ju Hwang
year: 2018
date: 2026-07-22
journal: "Proceedings of the 35th International Conference on Machine Learning"
source_pdf: "[[raw/papers/pinn/2018-Lee-深度非对称多任务特征学习.pdf]]"
tags:
  - 类型/论文
  - 主题/非对称多任务学习
  - 主题/负迁移
key_finding: "Deep-AMTFL 让可靠任务更多地重构共享特征、困难任务较少反向污染共享表征，提供深度非对称迁移先例，但仍是软作用而非分支不变性。"
method: "损失感知可靠性、非对称自编码重构、共享深层特征"
baseline: "STL、AMTL、Go-MTL、共享多任务神经网络"
aliases:
  - Deep-AMTFL
  - Lee2018-DeepAMTFL
---

# Deep-AMTFL 深度非对称特征学习

> Hae Beom Lee、Eunho Yang、Sung Ju Hwang，2018，ICML · PDF 9 页

## 一句话

论文把 AMTL 的不对称关系从任务参数图移到共享特征学习，使可靠任务主导表征；当前课题则需要更强的“家族不写入物理私有参数、物理也不写回冻结检测参数”。

## 方法核心

论文用任务预测重构共享潜特征，并以任务损失调节任务到特征的反馈强度。困难或不可靠任务对共享特征的影响较小，仍可从可靠任务形成的共享特征获益。深层版本把非对称自编码正则放在倒数第二层。

与 AMTL 的任务两两有向图相比，该方法随任务数增长更可扩展，但共享表示仍由多个任务共同优化。

## 实验结果

论文在合成数据、School、MNIST、CIFAR-100 与 Omniglot 等浅层和深层多任务场景比较对称与非对称方法，并报告 Deep-AMTFL 在困难任务和总体指标上降低负迁移。作者还用迁移实验说明其共享特征比普通深层网络更可复用。

## 我的理解

论文支持“成熟家族检测应成为可靠知识源，而不是继续被物理辅助任务改写”的方向。不过基于损失的连续可靠性仍需调权，无法满足当前预注册的家族下降不超过 0.01 的结构保证。

## 局限与不可外推结论

- 任务可靠性以训练损失近似，训练损失低可能来自捷径或数据泄漏。
- 共享特征仍可被所有任务间接影响，不保证逐样本输出不变。
- 实验不是生成式大模型、恶意流量或 PINN。

## 与本课题的关系

- 作为 [[AMTL非对称多任务学习]] 的深层扩展，支持非对称迁移动机。
- 当前修复应采用硬冻结与任务门控，而不是复现其自编码损失。

## 原始摘要

> 摘要要点经全文第 1 页核验：论文以非对称自编码项让可靠任务更多贡献于共享深层特征，降低困难任务造成的负迁移。此处为中文转述。

## 文献信息

- PMLR：[v80/lee18d](https://proceedings.mlr.press/v80/lee18d.html)
- 页码：2956-2964
