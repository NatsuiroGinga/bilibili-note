---
title: "Data vs. Physics: The Apparent Pareto Front of Physics-Informed Neural Networks"
authors:
  - Franz M. Rohrhofer
  - Stefan Posch
  - Clemens Gößnitzer
  - Bernhard C. Geiger
year: 2024
date: 2026-07-21
journal: "arXiv:2105.00862v2"
source_pdf: "[[raw/papers/pinn/2105.00862-数据与物理帕累托前沿.pdf]]"
tags:
  - PINN
  - 多目标优化
  - 帕累托前沿
  - 类型/论文
aliases:
  - Rohrhofer2024-数据与物理
key_finding: "系统尺度、计算域和方程参数会改变数据损失与物理损失的相对缩放及梯度可达的表观 Pareto 前沿，固定权重对参数化敏感。"
method: "系统参数对多目标标量化的理论分析与表观 Pareto 前沿可视化"
baseline: "不同固定损失权重的标准 PINN"
---

# PINN 数据与物理表观帕累托前沿

## 核心结论

- 数据拟合与物理一致性是具有折中的多目标问题。
- 特征尺度、时间尺度和方程系数会分别缩放残差，改变固定权重的有效区间。
- 改变参数化可扩大训练成功的权重范围，但不消除目标冲突本身。

## 适用边界

- 论文讨论偏微分方程 PINN，不证明任何权重适用于恶意流量大模型。
- Pareto 前沿上的低损失点仍需以真实状态或任务性能裁决。

## 与任务九的关系

当前残差已经容量归一，但四档固定权重仍失败，说明量纲一致只是必要条件。停止继续扫描固定权重符合本文对参数敏感性的认识。

## 可证伪实验

在边界锚定稀疏监督下，以未标注状态误差、生成损失和物理残差绘制同预算折中。如果所有物理配置均被无物理基线支配，则当前残差没有可用 Pareto 增量。

## 文献信息

- [arXiv 原文](https://arxiv.org/abs/2105.00862)
