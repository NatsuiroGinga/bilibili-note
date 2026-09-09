---
title: "Gradient based sample selection for online continual learning"
authors: [Rahaf Aljundi, Min Lin, Baptiste Goujaud, Yoshua Bengio]
year: 2019
date: 2026-09-09
journal: "NeurIPS 2019；arXiv:1903.08671v5"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2019-Wei-GSS-Gradient-Sample-Selection-Online-Continual-Learning.pdf]]"
tags:
  - 持续学习
  - 样本选择
  - 梯度多样性
  - 类型/论文
key_finding: "GSS 把固定回放记忆视为约束压缩问题，用样本梯度方向的多样性近似保留约束集合；梯度多样性并非新的未占用机制。"
method: "GSS-IQP 与 GSS-Greedy 梯度空间样本选择"
baseline: "Reservoir、随机选择、基于特征或梯度的选择策略"
aliases: [GSS, GSS-Greedy]
---

# GSS：梯度样本选择

## 方法核心

- §3.2--§3.4 将样本保留解释为约束选择：固定大小的记忆应尽量近似全部历史样本给出的可行梯度约束。
- 算法 1 使用整数二次规划，算法 2 给出更便宜的贪心版本；选择依据是归一化样本梯度之间的多样性。
- 论文明确讨论了计算成本：精确梯度选择较重，贪心方法降低了在线选择成本。
- §3.3 的代理目标最小化记忆样本间归一化梯度内积；它最大化的是梯度方向多样性，不是直接最小化翻转率。

## 对 LAMDA 的关系

- 若第三章声称“梯度多样性记忆”，GSS-Greedy 是不可跳过的直接对照。
- GSS 只能说明记忆覆盖和约束压缩，不自动实现旧恶意保护、恶意修复或良性误报控制；这些风险需要单独观测。

## 不能直接声称

- GSS 在视觉在线持续学习上的结果不能外推到 LAMDA；其梯度计算预算也必须与本课题 200 容量和训练暴露量单独记账。
- Disjoint MNIST、容量 500 的表 1 中，Rand 为 `57.9±4.1%`、GSS-Greedy 为 `84.8±1.8%`；Rand 是合并后随机保留对照，不等同于本课题标准 reservoir。

## 一句话

GSS 把固定记忆看作历史梯度约束的压缩，用梯度方向多样性选择保留样本。

## 背景：问题的演进

在线持续学习无法保存全部历史样本，需要在有限记忆中保留最能约束后续更新的样本；GSS 将记忆选择形式化为约束减少问题。

## 我的理解

GSS 解释了“多样性记忆”为什么可能有效，但它优化的是梯度约束覆盖，不是 LAMDA 的恶意保护、恶意修复或良性误报风险。

## 与相关工作的关系

GSS 是角色记忆或风险反馈记忆的直接样本选择对照；如果新机制使用梯度多样性，必须明确超出 GSS 的作用面。

## 疑问 / 待验证

- LAMDA 的固定 MLP 梯度多样性选择是否优于同配额随机记忆？
- 额外梯度计算是否改变公平的训练预算？

## 原始摘要

摘要原文保留在本地 PDF 第 1 页；此处只记录结构化转述。

## 文献信息

- arXiv：https://arxiv.org/abs/1903.08671
- HTML：https://arxiv.org/html/1903.08671v5
