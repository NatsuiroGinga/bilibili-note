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

