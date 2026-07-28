---
title: "Understanding the Difficulty of Solving Cauchy Problems with PINNs"
authors:
  - Tao Wang
  - Bo Zhao
  - Sicun Gao
  - Rose Yu
year: 2024
date: 2026-07-21
journal: "Proceedings of the 6th Annual Learning for Dynamics and Control Conference"
source_pdf: "[[raw/papers/pinn/wang24b-柯西问题PINN困难性.pdf]]"
tags:
  - PINN
  - 柯西问题
  - 可辨识性
  - 类型/论文
aliases:
  - Wang2024-柯西PINN
key_finding: "对论文研究的柯西问题，二范数方程残差与初值误差之和不足以保证恢复真实解；低残差不能替代状态正确性。"
method: "残差目标和神经网络逼近间隙的理论分析与数值实验"
baseline: "标准 PINN 与经典微分方程方法"
---

# PINN 柯西问题残差不足性

## 核心结论

- 低二范数残差和低初值误差不一定刻画真实动力学。
- 神经网络对奇异解的逼近间隙也会影响全局极小值与可达精度。
- 评价 PINN 必须使用独立真实状态误差，而不能只看训练残差。

## 适用边界

- 结论针对特定柯西问题，不表示所有残差方法均无效。
- 本任务是离散队列控制体，不可直接套用论文定理。

## 与任务九的关系

当前物理残差存在整体平移零空间。M2P 虽把残差降得很低，状态误差却显著恶化，正说明低残差不是正确绝对队列状态的充分证据。

## 可证伪实验

对稀疏监督模型同时报告未标注绝对锚点误差和残差。若残差改善但绝对误差无改善，应判定为零空间或平凡解失败。

## 文献信息

- [PMLR 原文](https://proceedings.mlr.press/v242/wang24b.html)
