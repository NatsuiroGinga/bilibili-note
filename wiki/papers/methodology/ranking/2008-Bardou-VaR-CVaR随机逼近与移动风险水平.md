---
title: "Computing VaR and CVaR using Stochastic Approximation and Adaptive Unconstrained Importance Sampling"
authors: [Olivier Bardou, Noufel Frikha, Gilles Pagès]
year: 2008
date: 2026-09-04
journal: "Monte Carlo Methods and Applications 15(3): 173–210, 2009（arXiv:0812.3381，提交于 2008-12-17）"
source_pdf: "[[raw/papers/methodology/ranking/2008-Bardou-VaR-CVaR-Stochastic-Approximation-arXiv.pdf]]"
sha256: "2cbec03308826fa2d6acc3858a563604e87098448acafd023d5a0f9d32b7d451"
tags:
  - CVaR
  - Robbins-Monro
  - 重要性抽样
  - 移动风险水平
  - 类型/论文
key_finding: "基于 Rockafellar-Uryasev 恒等式给出联合估计 VaR 与 CVaR 的 Robbins-Monro 随机逼近过程，并证明其满足高斯中心极限定理；指出该朴素过程的瓶颈是『只在罕见事件上才更新』（P(φ(X)>VaR_α)=1-α≈0），因此叠加自适应无约束重要性抽样加速收敛；为防止 IS 参数在初期『冻结』，用分段常数的移动置信水平 α_n（三段：50%→80%→目标 α）替代目标水平 α 加速 IS 初始化阶段，证明该改动不改变原有中心极限定理且能加快收敛。"
method: "把 VaR/CVaR 的联合估计写成同一凸优化问题（Rockafellar-Uryasev 恒等式）的解与值，用 Robbins-Monro 算法递归估计；叠加自适应无约束（无投影）重要性抽样降低方差；引入分段常数移动置信水平序列 α_n 加速 IS 参数向临界风险区域收敛的初始化阶段。"
baseline: "朴素蒙特卡洛估计（未加方差削减）、基于经验分布反函数的分位数估计"
aliases:
  - Bardou2009-VaRCVaRStochasticApprox
  - Bardou-Frikha-Pages
---

# 用随机逼近与自适应无约束重要性抽样计算 VaR 与 CVaR

> Bardou, Frikha, Pagès，2008/2009，Monte Carlo Methods and Applications 15(3): 173–210 · arXiv:0812.3381 · 正文约 30 物理页

## 一句话

给出联合估计 VaR 与 CVaR 的 Robbins-Monro 随机逼近算法，指出其固有瓶颈是"只在罕见事件上才更新"，据此设计自适应重要性抽样叠加**分段常数的移动置信水平**（先在低置信水平如 50% 训练重要性抽样参数，再逐步提高到目标水平）加速初始化，并证明该改动不破坏原有收敛性质的中心极限定理。

## 论文原结论

- 摘要：提出基于 Rockafellar-Uryasev 恒等式的第一个 Robbins-Monro（RM）过程，收敛速率满足高斯中心极限定理；为加速该初始过程，提出递归自适应重要性抽样（IS）过程，显著降低 VaR 与 CVaR 过程的方差；最后为加速 IS 算法的初始化阶段，**用缓慢移动的风险水平替代 VaR 原始置信水平**，证明所得过程的弱收敛速率由带最小方差的中心极限定理支配。
- 第 494 行（**瓶颈的正式表述**）：`In practice, the convergence of the algorithm will be chaotic. The bottleneck of this algorithm is that it is only updated on rare events since it tries to measure the tail distribution of φ(X): P(φ(X)>VaR_α)=1-α≈0.`
- 第 600 节起（**引入移动置信水平的动机**）：随算法演进，满足 `φ(X_k)>ξ_{k-1}` 的样本越来越少，`α≈1` 时越来越难高效计算 VaR/CVaR 估计；IS 参数可能在算法初期"卡住"（freeze），因为不知道该如何扭曲 `φ(X)` 的分布。为此引入非递减序列 `α_n` 在算法初期缓慢收敛到目标 `α`，只修改 VaR 分量过程（CVaR 分量过程本身不显式依赖 `α`）。
- **第 846–850 行（本课题此前未取得的解析调度式，本次全文核验补齐）**：实际实现分两阶段，**Phase I**（方差削减参数估计）用**三段分段常数**的移动置信水平：`α_n = 50%`（`1≤n≤M/3`）→ `α_n = 80%`（`M/3<n≤2M/3`）→ `α_n = α`（目标值，`2M/3<n≤M`），其中 `M≈15000`（典型取 `M≈N/100`，`N` 为总迭代数）。**Phase II** 用固定目标 `α` 按 Cesàro 平均产生最终 VaR/CVaR 估计，期间持续自适应更新 IS 参数。
- 数值实验（§5）：在能源与期权组合上验证方差削减效果，置信水平取 `α=95%, 99%, 99.5%`。

## 与本课题的关系（本课题检索目的：BER 训练期预算档退火/移动风险水平的文献核验，补齐既有核查文档的证据缺口）

- `thesis/methods/第三章-极端分位数CVaR估计文献核查.md` 第 2.4 节（预算水平退火）引用本文"we make the confidence level slowly increase from a low level (say 50%) to α"的定性描述，但明确标注 **Z6：该核查文档抓取到的正文未给出 `α_n` 的解析式，须取全文核**。**本次已下载官方 PDF 并全文精读，取得了该核查文档缺失的具体调度式**（见上文"论文原结论"第四条：三段分段常数、`M≈15000`），**补齐了该核查文档的 Z6 零结果条目**——答案是**分段常数**而非连续解析函数，且第一段确实恰好从 50% 起步，与该核查文档定性引用的"say 50%"完全一致。
- 该核查文档把本文的移动风险水平与 Ordered SGD 的 `q` 退火表并列为"预算档退火"的两条独立文献证据（第 2.4 节结尾："两条互不相关的文献在同一件事上收敛：不要从第一步就用极端预算，从宽到窄退火"），并纳入"六、可执行动作"表 A4（预算档退火，未开工，标注"待验证"）。本文给出的**三段式**具体调度可作为 A4 若要落地时的一个可参照的最简具体实现（而非该核查文档此前只能引用的定性描述）。
- **不可直接迁移**：本文的"罕见事件重要性抽样"机制（自适应无约束 RM 算法调整 IS 参数）与 BER 现用的 SOPA 式截断 CVaR 训练在优化范式上不同（本文是金融风险度量的蒙特卡洛估计场景，样本可重复模拟；BER 是深度学习训练场景，样本来自固定训练集小批量）。移动置信水平这一"做法"可类比，但重要性抽样机制本身需要独立设计才能迁移到 BER 场景（该核查文档 A5 行同样标注"换机制、等于新候选"）。

## 证据记录

- 全文：期刊发表版对应的 arXiv 预印本 PDF（2008-12-17 提交，正式发表于 Monte Carlo Methods and Applications 15(3), 2009），正文约 30 物理页；已用 `pdf-converter`（`mineru-open-api extract`）全文转换，定位并核对第 494 行瓶颈表述与第 842–852 行移动置信水平的具体调度式。
- 官方链接：<https://arxiv.org/abs/0812.3381>；期刊正式发表 Monte Carlo Methods and Applications 15(3): 173–210, 2009。
- 证据强度：原为该核查文档标注的 `L3`（定向抽取，未通读全文，Z6 明确记录"须取全文核"）；**本次下载官方 PDF 并全文精读后升级为本地全文 `L1`，且直接解决了该核查文档遗留的 Z6 缺口**。

## 疑问 / 待验证

- 本文的重要性抽样机制（`θ_n`、`μ_n` 参数化的自适应无约束 RM 过程）迁移到深度学习训练场景（而非本文的金融蒙特卡洛模拟场景）的具体实现方式未经推导，属独立于本文献核验的机制设计任务。
- 数值实验部分（§5）的具体方差削减因子数字未在本笔记中转录，如需引用应回到原文对应表格核对。
