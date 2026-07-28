---
title: "Physics Informed Deep Learning (Part I): Data-driven Solutions of Nonlinear Partial Differential Equations"
authors:
  - Maziar Raissi
  - Paris Perdikaris
  - George Em Karniadakis
year: 2017
date: 2026-07-17
journal: "arXiv 预印本（cs.AI）"
source_pdf: "[[raw/papers/pinn/1711.10561.pdf]]"
duplicate_sources:
  - "[[raw/papers/pinn/paper_b002d83866255ef3bd48ae3819cf2520.pdf]]"
tags:
  - 物理信息神经网络
  - 偏微分方程
  - 自动微分
  - 约束学习
  - 类型/论文
aliases:
  - PINN Part I
  - Raissi2017-PINN-Solution
key_finding: "把偏微分方程残差作为与数据误差并列的训练损失，能用少量初边值数据和无标签配点学习连续、可微且满足控制方程的代理解。"
method: "连续时间 PINN 与基于 Runge-Kutta 的离散时间 PINN"
baseline: "高斯过程方法与解析解；论文明确不把 PINN 视为经典数值方法的通用替代品"
---

# Physics Informed Deep Learning（Part I）

> Raissi、Perdikaris、Karniadakis · 2017 · arXiv:1711.10561 · 约 20 页

## 一句话

**PINN 的关键不是网络结构，而是把控制方程变成可微残差，并在无标签配点上与数据误差联合最小化。**

## 问题与机制

论文研究已知非线性偏微分方程时，如何从少量初值、边界值或观测数据恢复完整解。通式为：

$$
u_t + \mathcal{N}[u] = 0,\quad x\in\Omega,\ t\in[0,T].
$$

神经网络 $u_\theta(t,x)$ 逼近状态，自动微分构造物理残差：

$$
f_\theta(t,x)=\partial_tu_\theta+\mathcal{N}[u_\theta].
$$

连续时间模型的基本训练目标是：

$$
\mathcal{L}=\mathrm{MSE}_u+\mathrm{MSE}_f,
$$

$$
\mathrm{MSE}_u=\frac{1}{N_u}\sum_{i=1}^{N_u}|u_\theta(t_i^u,x_i^u)-u_i|^2,
\qquad
\mathrm{MSE}_f=\frac{1}{N_f}\sum_{i=1}^{N_f}|f_\theta(t_i^f,x_i^f)|^2.
$$

$\mathrm{MSE}_f$ 在无标签配点上排除违反控制方程的候选解，因此既是物理约束，也是结构化正则项。离散时间模型则把高阶隐式 Runge-Kutta 关系编码进网络输出，使模型能跨越较大时间步预测。

## 实验结论

- 连续时间 Burgers 方程使用 100 个初边值点和 10,000 个配点，报告相对 $L_2$ 误差 $6.7\times10^{-4}$；单张 NVIDIA Titan X 训练约 60 秒。
- Schrödinger 方程报告相对 $L_2$ 误差 $1.97\times10^{-3}$。
- 离散时间 Burgers 方程从 $t=0.1$ 单步预测到 $t=0.9$，报告相对 $L_2$ 误差 $8.2\times10^{-4}$。
- Allen-Cahn 方程报告相对 $L_2$ 误差 $6.99\times10^{-3}$。
- 论文用解析解作参照，重点验证少量有标签数据加大量物理配点的可行性，并非通用分类任务。

## 与生成式恶意流量检测的连接

可以迁移的是**训练目标的构造原则**，不能直接搬用 PDE 形式：

$$
\mathcal{L}_{\text{total}}
=\mathcal{L}_{\text{gen}}
+\lambda_{\text{proto}}\mathcal{L}_{\text{proto}}
+\lambda_{\text{cons}}\mathcal{L}_{\text{cons}}.
$$

- $\mathcal{L}_{\text{gen}}$：生成式大模型输出攻击类别及理由的监督损失。
- $\mathcal{L}_{\text{proto}}$：协议合法性、字段范围、方向关系等约束残差。
- $\mathcal{L}_{\text{cons}}$：包数、字节数、速率与持续时间之间的代数一致性残差。
- 若约束作用在连续辅助头或隐藏状态上，可以像 PINN 一样直接反向传播；若只对离散生成文本评分，应改造成序列级奖励或可微代理损失，不能声称使用了原始 PINN 自动微分机制。

对第一创新点最有价值的实验范式是：固定同一基座模型，比较纯生成损失、固定权重物理损失、自适应权重物理损失，并同时报告分类性能、约束违反率和跨数据集性能。

## 局限与审查边界

- 论文的“物理”是明确控制方程、初值和边界条件；通用流量表格只有统计恒等式时，更准确的名称是“物理一致性约束”或“领域约束学习”。
- 论文没有处理离散文本生成、类别不平衡、跨数据集协议漂移和恶意流量检测。
- 训练目标是多项损失的简单求和，尚未解决梯度尺度失衡与权重选择。
- 作者明确指出 PINN 不应被视为有限元、谱方法等经典数值方法的普遍替代方案，且当时未提供不确定性量化。

## 待验证

- 当前数据集是否含足够字段，使约束残差可以从原始流直接计算，而不是由标签反推。
- 物理约束能否在不泄露类别标签的情况下改善跨数据集宏平均 F1。
- 约束违反率下降是否与检测性能提升一致，还是只产生更“规整”但不更准确的输出。

## 摘要要点（转述）

论文提出连续与离散两类物理信息神经网络，用少量数据和偏微分方程先验学习非线性动力系统的连续代理解。

## 文献信息

- arXiv：1711.10561
- 重复文件校验：`paper_b002d...pdf` 与主文件 SHA-256 完全一致。
