---
title: "Regression-aware Continual Learning for Android Malware Detection"
authors: [Daniele Ghiani, Daniele Angioni, Giorgio Piras, Angelo Sotgiu, Luca Minnei, Srishti Gupta, Maura Pintor, Fabio Roli, Battista Biggio]
year: 2025
date: 2026-09-09
journal: "arXiv:2507.18313v2（2026-07-10；作者备注称已获 IEEE TIFS 接收）"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2025-Ghiani-Regression-Aware-Continual-Learning-Android-Malware.pdf]]"
tags:
  - Android恶意软件
  - 持续学习
  - 安全回归
  - 负向翻转
  - 类型/论文
key_finding: "把旧样本从更新前正确变成更新后错误的安全回归单独建模，并用 Positive Congruent Training（PCT）抑制负向翻转；PCT+Replay 在 TESSERACT 上降低恶意负向翻转，但 Recall 也下降。"
method: "负向翻转/正向翻转度量、PCT 正则、Naive/Replay/EWC/SI/A-GEM 对照"
baseline: "Naive、Replay、LwF、EWC、SI、A-GEM，以及各方法与 PCT 的组合"
aliases: [Regression-aware CL, Ghiani2025-PCT]
related:
  - "[[2026-Haque-LAMDA-Android恶意软件长期漂移基准]]"
  - "[[2020-Chrysakis-CBRS不平衡在线持续学习]]"
---

# Regression-aware Continual Learning for Android Malware Detection

> 全文原件已入库；以下页码按 PDF 物理页核对。该文不是 LAMDA 实验，不能把其数值直接当作 LAMDA 结果。

## 方法核心

- §III 将安全回归定义为更新前正确、更新后错误的样本级变化，并区分负向翻转率（NFR）与正向翻转率（PFR）。公式（2）--（7）说明，在同一评价集合和同一分母下，准确率变化满足 `ΔFNR = NFR_mal - PFR_mal` 的同类分解关系。
- §IV 介绍 PCT：在分类损失上加入对更新前正确样本的预测一致性正则；公式（8）--（10）给出正则形式和权重。
- PCT 不是只蒸馏旧正确恶意样本，也不是对测试集 FPR 的形式化保证；它仍需与当前监督目标共同训练。
- 原文式（2）将 NFR 分母定义为评价集合全部样本数，不是“旧模型判对样本数”；PCT 的基础蒸馏项覆盖全部样本，旧正确样本只获得额外权重。

## 实验结果

- §V-B 表 I 的 TESSERACT backward 结果：PCT+Replay 的恶意 NFR 为 `1.33±0.89%`，Recall 为 `81.40±2.85%`；报告明确显示降低 NFR 可能伴随 Recall/F1 下降。
- ELSA 表 I 中，Replay 加 PCT 后恶意 NFR 为 `1.00±0.44%`、Recall 为 `81.86±1.49%`；这些是该文 ELSA 结果，不是 LAMDA 结果。
- 文中在 ELSA、TESSERACT、AZ-Class 上比较多种持续学习策略，使用 Precision、Recall、F1、NFR 等指标；PCT 是可插入已有持续学习流程的安全回归基线。

## 对 LAMDA 的关系

- 必须作为阶段 B 的直接基线，排除“当前候选只是已有 PCT 的改名”。
- 本课题应同时记录旧恶意负向翻转、恶意正向修复、FNR、FPR、AP 和 Brier，不能只报告 NFR。
- 本课题当前安全记忆实现与配置中“上一冻结模型正确恶意集合”的定义不完全一致，因此不能称为该文 PCT 复现。

## 不能直接声称

- 该文没有在 LAMDA 上给出结果；TESSERACT 的 Recall/NFR 取舍不能证明 LAMDA 上必然同向。
- PCT 降低 NFR 不等于低 FPR，也不等于修复当前年度恶意漏报。

## 一句话

该文把持续学习中的样本级安全回归从平均遗忘中分离出来，并用 PCT 约束更新后旧正确样本的预测一致性。

## 背景：问题的演进

恶意软件检测需要持续更新；仅观察旧任务平均性能会掩盖单个恶意样本从正确变为漏报的风险。该文因此引入负向翻转与正向翻转的配对分析。

## 我的理解

PCT 更像“保持旧正确决策”的稳定性正则，而不是新错误修复器。它能降低负向翻转，但可能牺牲当前恶意召回，正好对应本课题阶段 A/B 观察到的保持—适应取舍。

## 与相关工作的关系

该文是 LAMDA 安全回归候选的直接方法近邻；A-GEM 只约束平均历史梯度，Replay 只提供样本记忆，二者都不等于分别控制恶意负向翻转和良性误报。

## 疑问 / 待验证

- PCT 在 LAMDA 的当前 MLP、总容量 200 和年度更新合同下是否仍降低 NFR？
- PCT 是否继续造成 FNR 或 FPR 代价？必须同时报告 PFR、NFR、FNR、FPR、AP。

## 原始摘要

摘要原文保留在本地 PDF 第 1 页；此处只记录结构化转述，避免重复长引文。

## 文献信息

- arXiv：https://arxiv.org/abs/2507.18313
- HTML：https://arxiv.org/html/2507.18313v2
