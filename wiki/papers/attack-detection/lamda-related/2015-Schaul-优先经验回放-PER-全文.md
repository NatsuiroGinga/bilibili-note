---
title: "Prioritized Experience Replay"
authors: [Tom Schaul, John Quan, Ioannis Antonoglou, David Silver]
year: 2016
date: 2026-10-15
journal: "ICLR 2016；arXiv:1511.05952"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2015-Schaul-优先经验回放-PER.pdf]]"
tags: [持续学习, 经验回放, 偏差校正, 类型/论文]
key_finding: "贪心优先化对噪声尖峰敏感（rewards 随机时 TD 误差是差估计），rank-based 变体对离群不敏感，随机优先化+重要性采样校正偏差。"
---

# Schaul 2016：优先经验回放 PER（ICLR 2016）

## 论文原结论

- **§2**：TD 误差作为优先化信号在 rewards 有噪声时是差估计：「The TD-error can be a poor estimate in some circumstances as well, e.g. when rewards are noisy」（原文附录 A 讨论替代量）。
- **§3.1**：贪心 TD 误差优先化的三大问题：对噪声尖峰敏感（噪声尖峰被 bootstrapping 放大）；低误差样本长期不被重访；贪心集中回放小子集导致过拟合与多样性丢失。
- **§3.1 两变体**：proportional `p_i = |δ_i| + ε`；rank-based `p_i = 1/rank(i)`（按 |δ| 排序的幂律分布）。原文：两分布都对 |δ| 单调，但 rank-based「is likely to be more robust, as it is insensitive to outliers」。
- **§6**：秩变换的代价：盲于相对误差尺度（丢失幅度信息），但「not affected by outliers nor error magnitudes」。
- **§5 Table 1**：Atari 57 游戏，rank-based 中位 106% vs DQN 48%（归一化中位分）。

数字引自 MinerU 全文转换（临时目录，任务后即弃）。

## 与 LAMDA 缺陷 2 的关系

- PER 是「**信号噪声大时如何分配回放预算**」的 RL 侧直接先例：作者承认信号（TD 误差）在随机奖励下噪声大，仍要据此分配，因此用三道防护：①秩变换（对离群稳健、丢幅度信息）；②随机优先化（不贪心 argmax，按优先级分布采样）；③重要性采样加权校正引入的偏差（β 从 0→1 退火）。
- **移植公式（秩变换分配）**：对每步测得的 ρ 不用原始值映射 m_r，而是把最近 W 步的 ρ 测量值按秩变换后再映射：`m_r(t) = 1 + 39 · rank(ρ_t)/W`。秩变换消掉重抽批噪声的幅度部分（离群 ρ 不再支配 m_r），保留序信息。
- **与 EMA 的区别**：EMA 平滑幅度、保留序；秩变换消幅度、保留序。两者正交，可组合（先秩后 EMA 或先 EMA 后秩——须实验裁定）。

## 不能直接声称

- PER 的信号是 TD 误差（标量、每条转移的「学习进展」），我们的 ρ 是批级梯度夹角；秩变换的收益不能外推，须实测。
- PER 的偏差校正（β）服务于 RL 的值函数估计无偏性，与我们的分配问题结构不同，只借「随机优先化+校正」的结构。

## 待验证假设（可证伪实验）

在 m200 執行 per-step ρ 上做秩变换映射 m_r，与 EMA70、原始 ρ 臂同种子对比 11 年平均 F1。**门槛：≥2 种子方向一致为正**。成本：每臂 10–15 分钟（服务器，同 m200_rho 臂实测 8–17 秒/年×11 年）。

## 文献信息

- arXiv: https://arxiv.org/abs/1511.05952
- 章节依据：本地 PDF §2、§3.1、§5 Table 1、§6；页码按 arXiv v3 版式以章节号为准。
- 与 [[2020-Russo-贝叶斯最优臂识别-噪声测量分配-全文|Russo 2020]]（后验比例分配）互补：Russo 软化响应，PER 秩变换+随机化。
