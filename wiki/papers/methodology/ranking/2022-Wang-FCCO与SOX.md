---
title: "Finite-Sum Coupled Compositional Stochastic Optimization: Theory and Applications"
authors: [Bokun Wang, Tianbao Yang]
year: 2022
date: 2026-08-13
journal: "Proceedings of the 39th International Conference on Machine Learning（ICML 2022），PMLR 162:23292–23317"
source_pdf: "[[raw/papers/methodology/ranking/2022-Wang-FCCO-SOX-ICML.pdf]]"
sha256: "902dbdcac4f36b7a683243cbb1dec460525a35775ca4650c4cea526a50a3b62f"
tags:
  - 耦合复合优化
  - 平均精确率
  - 随机优化
  - 类型/论文
key_finding: "形式化外层有限和索引与各自内层比较集耦合的 FCCO，并提出按外层索引维护内层状态和梯度动量的 SOX；AP、p-norm push 与列表排序都已被列为该框架实例。"
method: "SOX 对被抽中的外层索引选择性更新内层移动状态，再用状态化复合梯度和动量更新模型。"
baseline: "有偏随机梯度下降、SOAP、MOAP、SCGD、NASA"
aliases:
  - FCCO
  - SOX
  - Wang2022-FCCO
---

# FCCO 与 SOX：有限和耦合复合随机优化

> Wang 与 Yang，2022，ICML · 26 个物理页 · Zotero `XJVCGLYL`

## 论文原结论

- 第 1 页公式（1）把目标写成 `n` 个外层项的平均，每个外层样本拥有自己的大内层集合，并假设可抽样得到内层函数与其梯度的无偏估计。
- 第 2 页明确把 AP、`p`-norm push、ListNet、ListMLE 和 NDCG 等列为 FCCO 应用。
- 第 2—3 页把直接把小批内层均值代入外层梯度的方法称为有偏随机梯度下降，并指出理论上需要不现实的大内层批量。
- 第 3—4 页公式（2）及算法 1按外层索引维护内层移动状态；SOX 还维护梯度动量。其贡献是复合误差控制和收敛复杂度，不是声称插件式梯度逐步无偏。

## 与本课题的关系

- **可迁移机制**：实体是外层有限索引，实体间排序比较是内层集合，结构上属于 FCCO；SOX 是比裸 SOAP 更一般的算法母体。
- **本课题推论**：实体内抽流形成额外一层有限总体估计，当前候选实际上是“实体内矩估计＋实体间 AP 复合”的至少两级随机问题，不能只引用 SOX 后省略新一层的误差证明。
- **不可直接声称**：首次提出耦合复合 AP 优化、首次用两层采样优化排名指标、或 AP 与 `p` 范数首次联合出现。
- **实验待证**：按实体长度和标签分层抽样后，状态更新、逆概率权重与有限总体修正能否同时保持稳定。

## 证据记录

- 全文：PMLR 正式 PDF，26 页；关键位置为物理第 1—4 页及算法 1。
- 官方页：<https://proceedings.mlr.press/v162/wang22ak.html>
- 证据强度：直接占用通用 FCCO／SOX 优化框架；不包含实体包内无放回矩抽样或网络流量任务。

### 2026-09-01 引用核实：本篇与「Hu 2023」是两篇不同论文

`.Codex/docs/RWKV/2026-09-01-第三章公式来源与改造实质盘点.md` 第 4.2 节曾登记一处
「引用不一致待核」，怀疑可行性调研报告把本篇的作者年份写错成 Hu 2023。**核实结论：
不是笔误，是两篇不同的真实论文，且都属 FCCO 家族。**

- 本篇：Bokun Wang 与 Tianbao Yang，*Finite-Sum Coupled Compositional Stochastic
  Optimization: Theory and Applications*，ICML 2022，PMLR v162，Zotero `XJVCGLYL`。
  提出 FCCO 框架与 SOX 算法；式(1) 在物理页 1，式(2) 与算法 1 在物理页 3–4。
  **本篇没有物理页 8 式(8)–(9)**。
- 「Hu 2023」：Quanqi Hu、Dixian Zhu 与 Tianbao Yang，*Non-Smooth Weakly-Convex
  Finite-sum Coupled Compositional Optimization*，NeurIPS 2023，arXiv:2310.03234，
  56 物理页。是同一资深作者 Tianbao Yang 的**非光滑弱凸扩展**，题名字面即含
  「Finite-sum Coupled Compositional Optimization」。笔记见
  `wiki/papers/methodology/ft-mechanisms/2023-Hu-多示例双向部分AUC.md`，
  原件 `raw/papers/methodology/ft-mechanisms/2023-Hu-Multi-Instance-TPAUC-NeurIPS.pdf`
  （SHA-256 `3854226246c4a9364f4b88096a4e221d74c915086f494cff87c03d08c72bcb3c`，已实测比对一致）。
- **页码与公式编号核验通过**（2026-09-01 用 `mineru-open-api extract --pages 8-8`
  单页提取核对）：Hu 2023 物理页 8 确含式(8) 的 TPAUC 代理损失
  `min_w (1/n_+)(1/n_−) Σ_{X_i∈S_+^↑[1,k_1]} Σ_{X_j∈S_-^↓[1,k_2]} ℓ(h_w(X_j) − h_w(X_i))`，
  其中 `k_1 = ⌊n_+ α⌋`、`k_2 = ⌊n_− β⌋`；式(9) 为其 FCCO 改写
  `min_{w,s',s} (1/n_+) Σ_{X_i∈S_+} f_i(ψ_i(w, s_i), s')`。同一物理页 8 还给出
  多示例袋定义 `X_i = {x_i^1,…,x_i^{m_i}}`、均值池化
  `h_w(X) = (1/|X|) Σ_{x∈X} e(w_e;x)^⊤ w_c`，以及可扩展到平滑最大池化与注意力池化的声明。
- **本篇的「不可直接声称」三条不受影响**，仍然有效。需要额外注意的是：
  「袋级池化 ∘ 部分 AUC」这一具体复合的正式来源是 **Hu 2023**，不是本篇；
  正文引用时必须区分，不得把本篇写成该复合的出处。

相关笔记：[[wiki/papers/methodology/ranking/2017-Fan-ATk平均顶k损失|ATk]]、
[[wiki/papers/methodology/ranking/2022-Hu-SoRR排序区间和损失|SoRR / AoRR]]。

