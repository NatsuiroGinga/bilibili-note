---
title: "Adaptive Sampling for Stochastic Risk-Averse Learning"
authors: [Sebastian Curi, Kfir Y. Levy, Stefanie Jegelka, Andreas Krause]
year: 2020
date: 2026-09-04
journal: "arXiv preprint arXiv:1910.12511（v3，2020-11-06；ETH Zurich / MIT / Technion）"
source_pdf: "[[raw/papers/methodology/ranking/2019-Curi-Adaptive-Sampling-Risk-Averse-Learning-arXiv.pdf]]"
sha256: "5079436ce08352595b306edf49904c5b5d6d86bc5d275224984570529012b8a6"
tags:
  - CVaR
  - 分布鲁棒优化
  - 罕见事件采样
  - 类型/论文
key_finding: "证明截断型 CVaR（TRUNC-CVAR）梯度要么为 0 要么是 MEAN 梯度的 1/α 倍，导致数值溢出与训练不稳定，且实测 TRUNC-CVAR 训练准确率始终未超过 70%；提出 ADA-CVAR，把低 α 下的 CVaR 训练重新表述为零和博弈中的自适应稀有事件采样（k-DPP 边缘分布 + EXP3 型乘性更新），使梯度量级与 MEAN 相当，7 个 epoch 即达 85% 训练准确率（MEAN 需 9、SOFT-CVAR 需 21、TRUNC-CVAR 从未达到）。"
method: "把 CVaR 的 DRO 内层不确定集 Q^α={q: 0≤q_i≤1/k, Σq_i=1}（k=⌊αN⌋）写成零和博弈；q-玩家用对角核 k-DPP 的边缘分布作决策变量，按乘性权重更新 w_{t+1,i_t}=w_{t,i_t}·exp(η_s·k·L_{t,i_t}/q_{t,i_t}) 自适应学习采样分布 Q*，每步只需采一个点或一个小批。"
baseline: "MEAN（无风险敏感）、TRUNC-CVAR（硬截断经验 CVaR）、SOFT-CVAR（Nemirovski-Shapiro 型 log-sum-exp 平滑松弛）"
aliases:
  - Curi2020-ADACVAR
  - ADA-CVAR
---

# ADA-CVAR：随机风险规避学习的自适应采样

> Curi, Levy, Jegelka, Krause，2020，arXiv:1910.12511（v3）· 正文约 9 物理页（不含附录）

## 一句话

低 `α` 的 CVaR 训练在梯度层面等价于罕见事件蒙特卡洛估计问题（"拒绝采样"）；作者把内层不确定集优化写成零和博弈，用 k-DPP 边缘分布自适应学习"该往哪里采样"，从根本上避免了硬截断 CVaR 梯度量级的病态不对称。

## 论文原结论

- 第 3 页：把低 `α` 的 CVaR 训练明确归类为**罕见事件蒙特卡洛问题**——"Problem (3) can be interpreted as a form of rejection sampling – samples with losses smaller than ℓ are rejected. ... Monte Carlo estimation of rare events suffers from high variance"，据此提出**自适应学习采样分布 `Q*`** 的算法。
- 机制：DRO 内层不确定集 `Q^α = {q | 0≤q_i≤1/k, Σq_i=1}`（`k = ⌊αN⌋`，`N` 为数据集规模）写成零和博弈；`q`-玩家用对角核 k-DPP 的边缘分布作决策变量，按 `w_{t+1,i_t} = w_{t,i_t}·exp(η_s·k·L_{t,i_t}/q_{t,i_t})` 做 EXP3 型乘性更新，每步只采一个点（或一个小批），采样器保证采到的即为尾部点；脚注明确"we do **not** use any importance sampling correction"。
- **第 8 页（梯度病态的核心证据）**：TRUNC-CVAR 的梯度"either 0 or 1/α times larger" than MEAN 梯度，同类但被平滑的现象也出现在 SOFT-CVAR 上，导致"exploding gradients and noisier gradient estimates"，相同学习率下常出现数值溢出，需要"considerably smaller learning rates"来稳定训练，但这又"increased the number of iterations required for convergence"。**ADA-CVAR 不受此影响，梯度量级与 MEAN 相同。**
- 第 8 页实测数字：达到 85% 训练准确率所需 epoch 数——ADA-CVAR 7、MEAN 9、SOFT-CVAR 21、**TRUNC-CVAR 从未超过 70% 训练准确率**。
- Proposition 1（第 3–4 页，较松界）：CVaR 估计误差界 `(1/α)·√(log(2|H|/δ)/N)`——是本课题文献核查中与 arXiv:2512.01213 紧泛化界对照的一条较松参照界。

## 与本课题的关系（本课题检索目的：BER 极端分位数 CVaR 训练不稳定的文献核验）

本文是 `thesis/methods/第三章-极端分位数CVaR估计文献核查.md` **Q3（阈值追踪振荡现象）的主体证据来源**：

- 该文档第三节引用本文第 8 页原文，与本课题实测数字对照——本课题最低档 `1/β = 1/0.000997 = 1003`，实测全活动时的不对称比 `1002`，与原文"要么 0、要么 `1/α` 倍"的表述**数值吻合**。据此该核查文档判定：BER 现用（Rockafellar-Uryasev 截断型）实现出现梯度量级不对称是**该类 formulation 的固有性质，不是实现缺陷**。
- 本文给出的三条处置按效果排序：调小学习率（可直接执行，与 SOPA `η₁=O(βε²)` 同向）、平滑化（SOFT-CVAR，缓解但未消除）、自适应采样（ADA-CVAR，改动最大但效果最好）——已被吸收进该核查文档"六、可执行动作"表的 A2/A3/A5 三项（均标注"待验证"，未开工）。
- **不可直接声称**：ADA-CVAR 的"7 epoch 达 85%"是在其自身实验设置（数据集、模型、`α` 取值）下的结果，不能直接断言 ADA-CVAR 移植到 BER 场景会有同等改善幅度；`k = ⌊αN⌋` 中的 `N` 是数据集规模（本课题对应 `k=K`，六档合法），但采样器改动本身即是"换机制、等于新候选"（该核查文档 A5 行明确标注需要独立实验判据）。

## 证据记录

- 全文：arXiv 预印本 PDF（v3，2020-11-06），正文约 9 物理页；已用 `pdf-converter`（`mineru-open-api extract`）全文转换，并结合 `thesis/methods/第三章-极端分位数CVaR估计文献核查.md` 已核验的页码/原文引用交叉核对。
- 官方链接：<https://arxiv.org/abs/1910.12511>；NeurIPS 2020 会议论文。
- 证据强度：原为该核查文档标注的 `L2`（在线全文已读、原件未入库）；**本次下载官方 PDF 入库后升级为本地全文 `L1`**。

## 疑问 / 待验证

- 本笔记未独立核验 Proposition 1 的完整证明与其在附录中的推导细节，仅核对了正文陈述的界与数值。
- ADA-CVAR 的 k-DPP 边缘分布采样在本课题实体级排序（BER）场景下的具体适配方式（如何定义"点"、如何与实体级聚合 `S_e` 交互）未经推导，仍属该核查文档标注的"待验证"动作 A5 范畴。
