---
title: "Understanding and Mitigating Gradient Flow Pathologies in Physics-Informed Neural Networks"
authors:
  - Sifan Wang
  - Yujun Teng
  - Paris Perdikaris
year: 2021
date: 2026-07-21
journal: "SIAM Journal on Scientific Computing 43(5)"
source_pdf: "[[raw/papers/pinn/2001.04536-PINN梯度病态.pdf]]"
tags:
  - PINN
  - 梯度病态
  - 自适应权重
  - 类型/论文
aliases:
  - Wang2021-梯度病态
key_finding: "PINN 复合损失会因数值刚性产生反向梯度失衡；梯度统计加权和改进网络结构可缓解，但不保证解决方向冲突。"
method: "梯度流分析、自适应损失平衡与改进全连接架构"
baseline: "标准 PINN 与固定权重训练"
---

# PINN 梯度流病态与自适应平衡

## 核心结论

- 方程残差与初边界损失可产生量级悬殊的反向梯度，使部分目标训练停滞。
- 论文用梯度统计动态调节损失贡献，并设计更抗梯度病态的网络结构。
- 梯度范数和训练速率应作为复合损失诊断量，而不能只观察标量损失。

## 适用边界

- 方法主要解决梯度量级失衡；持续负夹角属于方向冲突，单纯缩放不能保证共同改善。
- 理论与实验基于全连接 PINN，不能直接作为低秩适配大模型的收敛保证。

## 与任务九的关系

任务七显示物理梯度没有压倒生成梯度，但生成与物理在 `20/20` 批次中方向相反。因此本文支持保留梯度统计诊断，却不支持把动态范数平衡作为当前第一候选。

## 可证伪实验

若未来测试梯度缩放，必须同时记录缩放前后夹角和三个验证指标。若范数更平衡但负夹角、状态误差或生成损失不改善，则判定缩放不适用。

## 文献信息

- [出版社页面](https://doi.org/10.1137/20M1318043)
