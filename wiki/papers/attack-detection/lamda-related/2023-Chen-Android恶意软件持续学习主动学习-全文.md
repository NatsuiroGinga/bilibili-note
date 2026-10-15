---
title: "Continuous Learning for Android Malware Detection"
authors: "Yizheng Chen, Zhouxing Ding, David Wagner"
year: 2023
date: 2026-10-15
journal: "32nd USENIX Security Symposium (USENIX Security 23)"
source_pdf: "raw/papers/attack-detection/lamda-related/2023-Chen-Continuous-Learning-Android-Malware.pdf"
tags: [主动学习, 概念漂移, Android恶意软件, 对比学习, 不确定性选样]
key_finding: "层级对比学习+伪损失不确定性选样做主动学习，每月固定标注量，预算外生；存储侧样本退休明确 out of scope——主动标注与存储管理在文献中被当作两个问题"
---

# Continuous Learning for Android Malware Detection（Chen 2023）

题录与原件：Chen、Ding、Wagner，USENIX Security 2023，共 19 页。本地原件经 MinerU extract 全文转换（2026-10-15）。

## 论文原结论

- 漂移证据（摘要）：在一年数据上训练的 Android 恶意软件分类器，部署 6 个月后 F1 从 0.99 降至 0.76。
- 机制：层级对比学习（同家族恶意样本强相似、异家族弱相似）+ **伪损失不确定性**（对测试样本构造与训练样本的对比对，取平均对比损失作不确定性分数）选样供分析师标注。
- 运行方式：每月固定标注量（如 200/月），warm start 重训；标注预算是外生固定量，从不检验「获取是否值得」。
- 结果：FNR 从 14% 降至 9%，FPR 从 0.86% 降至 0.48%；维持同等性能时标注人力降为约 1/8。

## 与本课题（RGA）的关系

- Android 恶意软件主动学习对抗漂移的代表作（SOTA 基线之一，CITADEL 与后续工作均以其为对照），覆盖 RGA「主动获取」分支的任务场景。
- **无排序门**：选样是逐样本不确定性 top-k，不是「先检验排序头部 lift 再决定是否获取」。
- **关键原文证据（存储侧分界）**：相关工作末段明文引 Rahman et al. 研究存储与训练限制下的持续学习方法，随后写「**Retiring training samples is out of scope in this paper**」——即「标什么」与「存什么」在现有 Android 恶意软件文献里被明确当作两个分开的问题，这正是 RGA 双预算命题的空白所在。

## 不可直接声称的内容

- 其标注量（如 200/月）是外生实验设定，不是可行性推导；不得引为「标注预算已解决」的依据。
- 层级对比损失的家族标签在 LAMDA 4561 维二值特征上的可用性未经本仓库复现。

## 证据等级

E2（本地全文已转换，MinerU extract；无本仓库复现实验）。
