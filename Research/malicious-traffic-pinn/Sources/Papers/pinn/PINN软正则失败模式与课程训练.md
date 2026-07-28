---
title: "Characterizing Possible Failure Modes in Physics-Informed Neural Networks"
authors:
  - Aditi S. Krishnapriyan
  - Amir Gholami
  - Shandian Zhe
  - Robert M. Kirby
  - Michael W. Mahoney
year: 2021
date: 2026-07-21
journal: "Advances in Neural Information Processing Systems 34"
source_pdf: "[[raw/papers/pinn/2109.01050-PINN失败模式.pdf]]"
tags:
  - PINN
  - 训练失败
  - 课程训练
  - 类型/论文
aliases:
  - Krishnapriyan2021-PINN失败模式
key_finding: "PINN 的软方程正则会使损失面更难优化；失败不一定来自网络表达能力，课程正则与短时序递推能缓解部分复杂动力学基准。"
method: "对流、反应和扩散方程失败模式分析，课程正则与序列到序列训练"
baseline: "标准 PINN、纯监督拟合和数值参考解"
---

# PINN 软正则失败模式与课程训练

## 核心结论

- 标准 PINN 在简单问题上有效，但轻微增加方程难度就可能训练失败。
- 失败主要来自软正则造成的优化病态，而非网络无法表达正确解。
- 论文的课程正则和序列到序列训练在所测基准上将误差降低一至两个数量级。

## 适用边界

- 证据来自偏微分方程坐标网络，不直接覆盖 Transformer 或生成式分类。
- 课程逐步增加的是方程难度或时间范围，不等于任意延迟物理损失都会有效。
- 物理模型错误、状态不可辨识或监督目标重复时，课程训练不能补充信息。

## 与任务九的关系

任务九完整覆盖后仍三项恶化，符合“软物理正则可能使优化更病态”的解释。它不支持继续增加曝光次数，也不支持把失败归因于 Qwen 表达能力不足。

## 可证伪实验

在每条队列序列只保留一个绝对边界锚点时，对比从第一步启用守恒残差与先学习边界、再启用残差。若课程只延缓退化，未标注锚点绝对误差仍不改善，则删除课程机制。

## 文献信息

- [会议原文](https://proceedings.neurips.cc/paper_files/paper/2021/file/df438e5206f31600e6ae4af72f2725f1-Paper.pdf)
