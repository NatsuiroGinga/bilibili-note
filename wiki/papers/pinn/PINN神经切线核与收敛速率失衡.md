---
title: "When and Why PINNs Fail to Train: A Neural Tangent Kernel Perspective"
authors:
  - Sifan Wang
  - Xinling Yu
  - Paris Perdikaris
year: 2022
date: 2026-07-21
journal: "Journal of Computational Physics 449:110768"
source_pdf: "[[raw/papers/pinn/2007.14527-PINN神经切线核.pdf]]"
tags:
  - PINN
  - 神经切线核
  - 收敛速率
  - 类型/论文
aliases:
  - Wang2022-PINN神经切线核
key_finding: "PINN 不同损失分量可具有显著不同的收敛速率，神经切线核能够解释并指导自适应权重，但其理论假设不能直接外推到 Transformer。"
method: "无限宽网络神经切线核分析与核特征值引导加权"
baseline: "标准固定权重 PINN"
---

# PINN 神经切线核与收敛速率失衡

## 核心结论

- 方程、边界和初值损失的核谱差异会造成收敛速率不一致。
- 自适应权重可在论文偏微分方程基准上缓解这种失衡。
- 损失数值相近不代表共享参数收到相容或同速的训练信号。

## 适用边界

- 分析建立在无限宽全连接网络及特定方程假设上。
- 核特征值加权处理速率，不自动解决语义上互相竞争的目标。

## 与任务九的关系

当前四档固定权重均失败，说明只凭标量损失设权重不足。任务七已有真实梯度夹角证据，后续应优先验证目标是否含新增信息，而不是直接实现神经切线核权重。

## 可证伪实验

只有在稀疏状态监督下物理项先表现出独立增益后，才比较固定权重与收敛速率平衡；若平衡后未标注状态和生成指标无共同改善，则不保留该机制。

## 文献信息

- [出版社页面](https://doi.org/10.1016/j.jcp.2021.110768)
