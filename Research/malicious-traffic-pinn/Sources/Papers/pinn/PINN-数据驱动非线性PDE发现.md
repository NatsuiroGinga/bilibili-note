---
title: "Physics Informed Deep Learning (Part II): Data-driven Discovery of Nonlinear Partial Differential Equations"
authors:
  - Maziar Raissi
  - Paris Perdikaris
  - George Em Karniadakis
year: 2017
date: 2026-07-17
journal: "arXiv 预印本（cs.AI）"
source_pdf: "[[raw/papers/pinn/1711.10566.pdf]]"
tags:
  - 物理信息神经网络
  - 系统辨识
  - 逆问题
  - 偏微分方程发现
  - 类型/论文
aliases:
  - PINN Part II
  - Raissi2017-PINN-Discovery
key_finding: "把控制方程中的未知参数与网络参数共同训练，PINN 能从稀疏且含噪的时空观测中同时恢复状态场和方程参数。"
method: "连续时间参数辨识与基于 Runge-Kutta 的两快照离散时间辨识"
baseline: "正确方程参数、含噪观测和高斯过程辨识结果"
---

# Physics Informed Deep Learning（Part II）

> Raissi、Perdikaris、Karniadakis · 2017 · arXiv:1711.10566 · 约 18 页

## 一句话

**Part I 固定方程求状态，Part II 把方程参数也设为可训练变量，从而把 PINN 变成受物理结构约束的系统辨识器。**

## 方法核心

参数化控制方程写为：

$$
u_t+\mathcal{N}[u;\lambda]=0.
$$

网络 $u_\theta(t,x)$ 与未知物理参数 $\lambda$ 共同定义：

$$
f_{\theta,\lambda}(t,x)=u_t+\mathcal{N}[u_\theta;\lambda].
$$

以 Burgers 方程为例：

$$
f=u_t+\lambda_1uu_x-\lambda_2u_{xx},
\qquad
\mathcal{L}=\mathrm{MSE}_u+\mathrm{MSE}_f.
$$

连续时间模型使用散布在完整时空域的观测；离散时间模型只使用两个时间快照，并把 Runge-Kutta 阶段关系写入网络约束。训练结果同时给出场变量 $u_\theta$ 与未知系数 $\lambda$。

## 实验结论

- Burgers 方程使用 2,000 个散点和 9 层、每层 20 个神经元的网络；在 1% 无关噪声下仍准确恢复两个系数。
- 论文报告噪声提高到 10% 时仍能得到合理辨识结果，但不同训练样本数下黏性系数误差可达到约 6%，说明稳健性不是无条件成立。
- KdV 方程只用两个时间快照，也能恢复非线性项和三阶导数项系数；1% 噪声下辨识系数仍接近真值。
- 还验证了 Navier-Stokes、非线性浅水波等问题，表明同一框架可处理不同已知结构的逆问题。

## 与生成式恶意流量检测的连接

这篇论文启发的不只是“加约束”，而是**让部分约束参数由数据辨识**。在恶意流量中，不宜人工固定所有阈值，可以令：

$$
r_k(x;\phi)=g_k(x)-c_k(x;\phi),
$$

其中 $g_k$ 是可观测统计关系，$\phi$ 是数据集、协议或业务场景相关的容差/尺度参数。训练时联合学习模型参数与 $\phi$，再限制 $\phi$ 的可解释范围。

可落地的候选机制：

- 从良性流量估计各协议下包速率、字节速率、方向比的正常参数区间。
- 用物理残差辅助头预测下一时间窗统计量，同时学习场景相关系数。
- 用外层验证集约束参数，避免模型把所有异常吸收到过宽的“正常物理范围”中。

这为第一创新点增加了一层理论深度：**固定协议恒等式加可学习场景参数**，比单纯手工加权更接近 PINN 逆问题。

## 局限与审查边界

- 方程结构 $\mathcal{N}$ 在论文中是预先已知的，学习的是少量参数；它不支持从任意网络流量中自动发现可信“物理定律”。
- 方程参数可辨识性依赖观测覆盖、噪声和模型设定；参数可训练不等于参数有唯一物理意义。
- 恶意流量的类别标签不是动力系统参数，不能把分类器权重解释成物理量。
- 若数据只有独立流记录而无连续时间窗、拓扑或双向会话信息，系统辨识路线会缺少必要观测。

## 待验证

- 在 GeNIS、HIKARI 与 CICIoT2023 中，哪些字段能形成跨数据集统一的可学习约束参数。
- 只从良性训练集估计约束参数，能否避免标签泄漏并提高未知攻击检测能力。
- 参数学习相较固定阈值是否带来显著收益，且是否增加训练方差和计算成本。

## 摘要要点（转述）

论文用连续与离散时间 PINN 从稀疏、可能含噪的观测中辨识非线性偏微分方程参数，覆盖守恒律、不可压缩流和非线性浅水波等基准。

## 文献信息

- arXiv：1711.10566
