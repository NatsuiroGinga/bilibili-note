---
title: "FreeMOCA: Memory-Free Continual Learning for Malicious Code Analysis"
authors: [Zahra Asadi, Haeseung Jeon, Sohyun Han, Md Mahmuduzzaman Kamol, Se Eun Oh, Mohammad Saidur Rahman]
year: 2026
date: 2026-09-09
journal: "arXiv:2605.09664v2（2026-05-14）"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2026-Asadi-FreeMOCA-Memory-Free-Continual-Malicious-Code.pdf]]"
tags:
  - 恶意代码
  - 持续学习
  - 参数插值
  - 类型/论文
key_finding: "FreeMOCA 不保存回放样本，而是利用连续任务 warm-start 后的局部低损失路径做自适应逐层参数插值；其 Domain-IL 与 Class-IL 实验使用 EMBER/AZ，不是 LAMDA。"
method: "Warm-start、adaptive layer-wise interpolation、参数空间模式连通"
baseline: "Joint、Naive、ER、EWC、SI、LwF、CLeWI 等"
aliases: [FreeMOCA, Asadi2026]
---

# FreeMOCA：无记忆持续学习

## 方法核心

- §3.2--§3.4 论证连续任务 warm-start 使相邻任务最优点保持参数对应和局部低损失路径，并为每层设置插值权重。
- 算法 1 在不保存历史样本的情况下，对相邻任务更新后的参数做自适应逐层插值。
- §3.4 给出逐层插值形式：变化较大的层获得更保守的当前权重；“Memory-Free”仍需保存上一任务模型参数，不等于没有状态。

## 实验结果

- §4 使用 EMBER 和 Android AZ 数据，AZ 使用 2,381 维 Drebin 特征；Class-IL 表 1、Domain-IL 附录表 9 和遗忘表 10 是主要结果位置。
- 论文报告 AZ-Class 中 FreeMOCA 的平均准确率高于若干基线，但 Joint 仍是不同资源条件下的上界参考；它没有 LAMDA 4,561 维或同协议实验。
- AZ-Class 表 1 中，自适应逐层线性插值为 `66.1%`，固定 `lambda=0.6` 为 `63.7%`；表 2 的 `F=0`、`REM=1` 是聚合遗忘指标，不能解释为每个旧样本均未遗忘。

## 对 LAMDA 的关系

- 可作为“参数保持／无回放迁移”近邻，帮助区分 Replay 的样本记忆与参数路径保持。
- 若迁移到 LAMDA，必须与普通 warm-start、固定插值和等资源 Replay 对照，不能把无记忆方法直接称为 LAMDA 强基线。

## 不能直接声称

- AZ/EMBER 的结果不能证明 LAMDA 的跨年 FNR、FPR 或安全回归改善。

## 一句话

FreeMOCA 用 warm-start 后相邻任务参数的逐层插值替代回放样本，以较低记忆成本保持历史能力。

## 背景：问题的演进

持续保存历史样本会增加存储与训练成本，而只用新任务更新会遗忘旧知识；FreeMOCA 从参数空间局部低损失路径寻找无记忆保持方式。

## 我的理解

FreeMOCA 与 LAMDA 的标准 Replay 是不同的信息保持路线：前者保存参数路径，后者保存样本证据。它适合做迁移/参数保持近邻，不是 LAMDA 的同协议强基线。

## 与相关工作的关系

FreeMOCA 与 EWC、SI、LwF、ER 等持续学习方法比较；它的 AZ/EMBER 协议不能替代 LAMDA 的年度 Domain-IL 合同。

## 疑问 / 待验证

- warm-start 插值在 LAMDA 逐年更新中是否优于普通 warm-start？
- 不保存样本时能否保持恶意负向翻转和当前恶意修复的平衡？

## 原始摘要

摘要原文保留在本地 PDF 第 1 页；此处只记录结构化转述。

## 文献信息

- arXiv：https://arxiv.org/abs/2605.09664
- HTML：https://arxiv.org/html/2605.09664v2
