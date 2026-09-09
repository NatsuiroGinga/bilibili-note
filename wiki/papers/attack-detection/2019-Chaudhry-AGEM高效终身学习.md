---
title: "Efficient Lifelong Learning with A-GEM"
authors: [Arslan Chaudhry, Marc’Aurelio Ranzato, Marcus Rohrbach, Mohamed Elhoseiny]
year: 2019
date: 2026-09-09
journal: "ICLR 2019；arXiv:1812.00420v2"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2019-Chaudhry-A-GEM-Efficient-Lifelong-Learning.pdf]]"
tags:
  - 持续学习
  - 梯度约束
  - 类型/论文
key_finding: "A-GEM 用记忆样本的平均参考梯度约束当前更新，使记忆上的平均损失不增加，并以较低计算成本近似 GEM。"
method: "平均梯度参考、违反约束时的梯度投影"
baseline: "GEM、EWC、SI、Replay 等"
aliases: [A-GEM, Chaudhry2019]
---

# A-GEM：平均梯度约束

## 方法核心

- §4、公式（9）--（11）：用记忆批次得到参考梯度 `g_ref`，若当前梯度与参考梯度内积为负，则投影到不增加记忆平均损失的方向。
- 该约束是平均历史损失约束，不分别约束恶意旧正确决策和良性误报风险。
- 公式（10）--（11）在 `g^T g_ref<0` 时投影当前梯度，否则保持原梯度；它只保证参考梯度半空间意义上的平均约束。

## 对 LAMDA 的关系

- 是双侧风险约束修复候选的关键已有方法对照。
- 若新方法把恶意保护和良性误报代理分别建约束，必须证明其作用不等于重新实现 A-GEM 的单一平均梯度投影。

## 不能直接声称

- A-GEM 的通用持续学习结果不能证明 LAMDA FPR、FNR 或负向翻转改善。
- 原文附录 D.2 报告 CIFAR 上 GEM/A-GEM 平均准确率约 `61.2%/62.3%`；附录 E 的计时为 GEM `5238 s`、A-GEM `449 s`，均只属于原协议。

## 一句话

A-GEM 用记忆平均梯度作为参考，在当前梯度违反历史损失约束时进行投影。

## 背景：问题的演进

GEM 的多约束二次规划开销较高；A-GEM 用单个记忆参考梯度近似历史约束，以降低计算和内存成本。

## 我的理解

A-GEM 约束的是平均历史损失，不区分恶意旧正确决策和良性误报。因此它是双侧风险约束候选的必要基线，而不是目标算法本身。

## 与相关工作的关系

A-GEM 与 GSS 共享“梯度约束”视角，但前者约束更新、后者选择记忆；新方法必须说明与两者的不可约差异。

## 疑问 / 待验证

- 在同容量、同训练合同下，A-GEM 是否降低旧恶意负向翻转？
- 平均历史损失不增是否掩盖某一风险侧恶化？

## 原始摘要

摘要原文保留在本地 PDF 第 1 页；此处只记录结构化转述。

## 文献信息

- arXiv：https://arxiv.org/abs/1812.00420
- HTML：https://arxiv.org/html/1812.00420v2
