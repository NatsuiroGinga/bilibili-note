---
title: "Scientific Machine Learning through Physics-Informed Neural Networks: Where we are and What's next"
authors:
  - Salvatore Cuomo
  - Vincenzo Schiano Di Cola
  - Fabio Giampaolo
  - Gianluigi Rozza
  - Maziar Raissi
  - Francesco Piccialli
year: 2022
date: 2026-07-17
journal: "Journal of Scientific Computing, 92(3), 88"
source_pdf: "[[raw/papers/pinn/paper_0dd9fd2db26952889e10293d9209c0bf.pdf]]"
tags:
  - 物理信息神经网络
  - 科学机器学习
  - 多任务学习
  - 硬约束
  - 类型/论文
aliases:
  - Cuomo2022-PINN-Survey
  - Scientific ML through PINNs
key_finding: "PINN 可统一理解为拟合数据、边界和方程残差的多任务学习；改进集中在激活函数、优化器、网络结构和损失结构，但收敛理论与最优训练仍未解决。"
method: "覆盖原始 PINN、PCNN、VPINN、CPINN、理论、工具和应用的系统综述"
baseline: "有限元等经典数值方法、原始 PINN 和多种物理约束神经网络变体"
---

# 通过 PINN 实现科学机器学习：现状与未来

> Cuomo 等 · Journal of Scientific Computing · 2022 · 92(3):88 · arXiv:2201.05624

## 一句话

**该文明确把 PINN 解释为多任务学习框架：数据拟合、边界条件和方程残差共同训练，而每一项是否存在取决于任务。**

## 统一目标

设 $u_\theta$ 为代理模型，$F$ 为控制方程，$B$ 为初边值条件，目标为：

$$
\theta^*=\arg\min_\theta
\left(
\omega_F\mathcal{L}_F(\theta)
+\omega_B\mathcal{L}_B(\theta)
+\omega_d\mathcal{L}_{\text{data}}(\theta)
\right).
$$

其中：

- $\mathcal{L}_F$ 在域内配点约束方程残差。
- $\mathcal{L}_B$ 约束初值或边界条件。
- $\mathcal{L}_{\text{data}}$ 拟合合成或实测数据，权重可反映测量质量。

正问题可在无观测数据时只靠方程与边界训练；逆问题通常需要观测以保证问题可解。约束可以是软损失，也可以编码进网络结构形成硬约束。

## 方法分类

- **原始 PINN**：配点残差加初边值/数据均方误差。
- **物理约束神经网络**：通过特定结构让初边值条件严格成立，再只优化方程残差。
- **变分 PINN**：采用弱形式或变分形式，降低高阶导数计算压力。
- **守恒 PINN 与域分解**：在子域接口显式保持通量或守恒关系，处理不连续和大域问题。
- **扩展物理损失**：只使用模型的最低限度信息，不必总是完整偏微分方程，但必须能形成可验证残差。

## 综述结论与局限

- 大多数研究通过修改激活函数、梯度优化、网络结构或损失结构定制 PINN。
- 自动微分并非唯一选择，但替代路径研究较少。
- 收敛分析、多方程联合求解和最优训练仍是开放问题。
- 物理信息可能来自观测值，也可能来自方程；真正发挥正则作用的是无标签配点上的物理残差。

## 与生成式恶意流量检测的连接

这篇综述支持把第一创新点定义为**多任务受约束生成训练**，而不是强行把大模型改造成 PDE 求解器：

$$
\mathcal{L}=\mathcal{L}_{\text{label/reason}}
+\lambda_1\mathcal{L}_{\text{algebraic}}
+\lambda_2\mathcal{L}_{\text{protocol}}
+\lambda_3\mathcal{L}_{\text{temporal}}.
$$

可以用硬约束保证输出 JSON 结构和类别集合合法，用软约束学习流量字段与时间窗一致性。这样能区分两种完全不同的“约束”：输出格式约束提高可用性，物理/协议残差才用于主张领域一致性。

论文还提示一个重要边界：只有约束在未标注样本上也能独立计算时，才真正带来类似 PINN 的数据效率优势。若残差依赖攻击标签，它只是另一种监督损失。

## 局限与审查边界

- 文献所说的物理模型通常有明确方程和边界，网络流量统计规则未必具有同等理论地位。
- 多任务损失相加只是框架，不自动构成创新；必须提出具体残差、权重机制与可验证假设。
- 综述覆盖范围广，但不提供恶意流量数据和生成式模型证据。
- 物理硬约束若设计错误，会永久排除真实但少见的流量模式。

## 待验证

- 哪些约束适合硬编码，哪些必须保留可学习容差。
- 无标签流量加入物理损失后，是否减少所需标注量。
- 变分/弱形式思想能否用于批次或时间窗聚合残差，降低逐样本噪声。

## 摘要要点（转述）

论文综述配点式 PINN 及其变体，重点分析网络、损失、优化、理论和工具，并指出理论保证与训练效率仍有明显缺口。

## 文献信息

- DOI：10.1007/s10915-022-01939-z
- arXiv：2201.05624
