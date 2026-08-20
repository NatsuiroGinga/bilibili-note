---
title: "Maximum Likelihood with Bias-Corrected Calibration is Hard-To-Beat at Label Shift Adaptation"
authors:
  - Amr M. Alexandari
  - Anshul Kundaje
  - Avanti Shrikumar
year: 2020
date: 2026-08-19
journal: "Proceedings of the 37th International Conference on Machine Learning (ICML 2020), Vienna, Austria, PMLR 119；卷内页码原件未印，须回 PMLR 核定"
source_pdf: "[[raw/papers/methodology/2020-Alexandari-MLLS-Calibration.pdf]]"
tags:
  - 标签移位
  - 校准
  - 期望最大化
  - 类型/论文
key_finding: "把 Saerens 等 2002 的 EM 先验校正配上「偏差校正校准」后，在多样设置下同时胜过 BBSL 与 RLLS；论文明写 EM 路线 **既不需要重训也不需要调超参**（PDF p.2），而 BBSL 与 RLLS **需要用重要性权重重训模型**（p.1 摘要）。"
aliases:
  - MLLS
  - Alexandari2020-MLLS
related:
  - "[[2018-Lipton-BBSE标签移位]]"
  - "[[2019-Azizzadenesheli-RLLS标签移位正则化学习]]"
---

# MLLS：偏差校正校准下的极大似然标签移位适应

## 一句话

标签移位适应不必换算法，只要把分类器的概率输出校准准，最老的 EM 先验校正就足以打败 BBSL 与 RLLS。

## 题录与原件（全文核验）

- 原件：`raw/papers/methodology/2020-Alexandari-MLLS-Calibration.pdf`，11 页。
- 载体从原件 p.1 页脚核出：`Proceedings of the 37 th International Conference on Machine Learning,
  Vienna, Austria, PMLR 119, 2020. Copyright 2020 by the author(s).`
  **卷内页码原件未印，正式著录前须回 PMLR 卷 119 目录核定。**
- 证据等级：**同行评议正式发表**（ICML）。
- 本笔记补建缘由：该原件此前无 `wiki/papers/` 笔记（2026-08-19 轴二文献盘点发现）。

## 论文原结论（页级证据）

- p.1 摘要：标签移位指先验类概率 `p(y)` 在源与目标间变化而条件概率 `p(x|y)` 固定。
  给定模型输出的 `p(y|x)`，Saerens 等提出一个高效的极大似然算法来校正标签移位，
  该算法 `does not require model retraining`；但其限制性假设是 `p(y|x)` 已校准，
  而现代神经网络并不满足这一点。
- p.1 摘要续：BBSL 与 RLLS 是应对分类器输出未校准时标签移位的当前最好技术，
  但两者 `require model retraining with importance weights`，且都未与极大似然做过基准对比。
- p.1 摘要贡献：(1) 把极大似然与「偏差校正校准」结合后在多样设置下同时优于 BBSL 与 RLLS；
  (2) 提出对源域先验不敏感的改进，提高对差校准的稳健性。
- p.2 §1：Saerens 等 2002 提出一个简单的期望最大化（EM）过程来估计 `q(y)`，
  **无须估计 `p(x|y)`**；Lipton 等 2018 则另辟混淆矩阵路线。
- p.2：`EM requires neither retraining nor hyperparameter tuning`；
  但 EM 的限制在于其假设（`p(y|x)` 已校准）。

## 本课题推论（非论文原结论）

- 本文是标签移位族**内部的方法学重排**：把「换更复杂的估计器」这条路否掉，
  改为「先把校准做对」。它并没有放松该族的共同前提——
  仍然需要目标域的无标签样本来估计新的先验 `q(y)`。
- 本文是本仓库目前对 **Saerens 等 2002** 内容的**唯一二手可核来源**。
  骨架盘点指出 Saerens 原件本机缺失；在补到原件之前，
  正文若要提及 EM 先验校正的起点，只能写成「Alexandari 等转述的 Saerens 方法」，
  **不得直接著录 Saerens 2002 为已核验条目**。

## 不可直接声称的内容

- 不得据本笔记著录 Saerens, Latinne & Decaestecker 2002 的题录（作者、卷期页码）。
- 不得写成 MLLS 在网络流量任务上被验证。

## 与本课题的关系

- 落 1.2.2 段二（标签移位与先验校正子簇）。
- 短板证据：p.1 摘要「BBSL 与 RLLS 需要用重要性权重重训模型」，
  与 Ben-David 的理论结论、DANN 的目标样本前提共同构成段末短板。
