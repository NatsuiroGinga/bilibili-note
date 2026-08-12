---
title: "保形风险控制"
authors: [Anastasios N. Angelopoulos, Stephen Bates, Adam Fisch, Lihua Lei, Tal Schuster]
year: 2024
date: 2026-08-11
journal: "ICLR 2024"
source_pdf: "[[raw/papers/methodology/2024-Angelopoulos-Conformal-Risk-Control.pdf]]"
tags: [保形预测, 风险控制, 校准, 类型/论文]
key_finding: "将保形校准从集合覆盖推广到关于阈值单调的有界损失期望控制；基本保证依赖交换性。"
---

# 保形风险控制

## 全文核验结论

本文用校准集选择阈值参数，使有界、单调损失的测试风险期望受控。核心校准在经验风险上加入一个有限样本修正项。官方 OpenReview 全文已逐项核验；本地 PDF 有效，但文本层编码不完整，因此未把本地抽取失败误报为缺全文。

## 公式族

典型选择为满足 `n/(n+1)·R_hat_n(λ)+B/(n+1)≤α` 的最小可行 `λ`，其中 `B` 是损失上界。交换性使测试点与校准点可对称处理。

## LSPR 边界

它可用于源域阈值或风险校准，但 LSPR23 与 LSPR24 非交换，基本定理不能直接迁移。必须与加权协变量移位和非交换扩展一起使用，不能单独作为跨年保证。

## 最小证伪实验

冻结同一分数，比较源经验分位数、基本保形风险控制和移位扩展；若目标风险失控，只能说明交换性破坏，不应事后调整目标阈值。

## 证据记录

- 全文状态：完成官方全文逐项核验。
- 官方入口：OpenReview `33XGfHLtZg`。
- Zotero：`2CNV4CKE`。
- 课题角色：备选路线二的交换基准。
