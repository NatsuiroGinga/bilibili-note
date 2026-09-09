---
title: "MADAR: Efficient Continual Learning for Malware Analysis with Diversity-Aware Replay"
authors: [Mohammad Saidur Rahman, Scott Coull, Qi Yu, Matthew Wright]
year: 2025
date: 2026-09-09
journal: "arXiv:2502.05760v1（2025-02-09）"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2025-Mohamed-MADAR-Diversity-Aware-Replay.pdf]]"
tags:
  - 恶意软件
  - 持续学习
  - 多样性感知回放
  - 类型/论文
key_finding: "MADAR 针对恶意软件家族高度多样的问题，在持续学习记忆中按家族预算保留代表性与异常样本；其历史池和预算合同不同于 LAMDA 全程总容量 200。"
method: "家族预算、代表性样本与异常样本的多样性感知回放，覆盖 Domain-IL、Class-IL、Task-IL"
baseline: "Naive、Replay、Joint 以及多种持续学习方法"
aliases: [MADAR, MADAR2025]
related:
  - "[[2026-Haque-LAMDA-Android恶意软件长期漂移基准]]"
---

# MADAR：恶意软件多样性感知回放

## 方法核心

- §IV-D、算法 1 在 Domain-IL 中按恶意软件家族分配预算，并在家族内保留代表性样本和异常样本；家族预算与历史数据池共同决定记忆构成。
- 论文分析指出恶意软件家族分布和内部变化高度多样，单纯按总体分布采样可能无法覆盖稳健表征所需的变体。
- 文中还区分 MADAR 的回放变体，并以全局平均准确率（论文记作平均准确率）评估，不应误读成 Average Precision。
- 算法 1 维护历史池 `P` 并追加当前任务数据；家族预算既可按比例分配，也可均匀分配，家族内部再结合代表性与异常性选择。历史池规模与回放子集预算必须分开记账。

## 实验结果

- §VI-A 算法 1 和 §VI-B 的实验覆盖 EMBER、Android 等恶意软件设置，使用逐任务平均准确率和遗忘等持续学习指标。
- 论文报告在有限数据预算下接近完整重训，但历史池会随任务增长；这与本课题严格的全程总容量 200 不同。
- EMBER Domain-IL、预算 10,000 时，论文表 II 报告 GRS `94.1±1.3%`、MADAR-R `94.7±0.1%`；该指标是平均准确率，不是本课题的 average precision。

## 对 LAMDA 的关系

- 可作为“家族／条件覆盖记忆”的强近邻和消融对照。
- 若迁移到 LAMDA，必须把历史池裁成全程 200，并只使用当时可用的家族或时间信息；不能把未来家族目录倒灌到记忆分配。
- 仅把 reservoir 换成家族配额不能单独构成第三章创新，应与同配额随机记忆比较。

## 不能直接声称

- MADAR 未在 LAMDA 上验证；其家族预算和历史池规模不能直接移植。
- 论文的平均准确率不是本课题的 AP；不能比较数值大小。

## 一句话

MADAR 针对恶意软件家族内部和家族之间的高度多样性，按家族预算和代表性保留回放样本。

## 背景：问题的演进

通用持续学习回放策略通常按总体样本流工作，但恶意软件家族变化和内部变体会使总体分布代表性不足；MADAR 因此把家族结构纳入记忆构造。

## 我的理解

MADAR 的核心不是“多保存困难样本”，而是把家族覆盖与异常代表性结合起来。不过它的历史池会增长，不能直接复制到 LAMDA 的全程 200 槽位合同。

## 与相关工作的关系

CBRS 是类别平衡先例，GSS 是梯度多样性先例，MIR 是干扰检索先例；MADAR 提供恶意软件家族覆盖的直接近邻。

## 疑问 / 待验证

- LAMDA 家族标签在每个年度更新时是否满足部署可用性？
- 在固定总容量 200、同回放暴露量下，家族/时间条件记忆是否优于同配额随机记忆？

## 原始摘要

摘要原文保留在本地 PDF 第 1 页；此处只记录结构化转述。

## 文献信息

- arXiv：https://arxiv.org/abs/2502.05760
- HTML：https://arxiv.org/html/2502.05760v1
