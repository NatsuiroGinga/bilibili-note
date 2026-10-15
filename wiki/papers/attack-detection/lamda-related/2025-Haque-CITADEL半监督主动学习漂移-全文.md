---
title: "CITADEL：连续分布漂移下的半监督主动学习恶意软件检测"
authors: "Md Ahsanul Haque, Md Mahmuduzzaman Kamol, Suresh Kumar Amalapuram, Vladik Kreinovich, Mohammad Saidur Rahman"
year: 2025
date: 2026-10-15
journal: "arXiv preprint arXiv:2511.11979"
source_pdf: "raw/papers/attack-detection/lamda-related/2025-Haque-CITADEL-Semi-Supervised-Active-Learning-Drift.pdf"
tags: [主动学习, 半监督, 概念漂移, Android恶意软件, LAMDA, 标注预算]
key_finding: "半监督主动学习在 LAMDA 12 年序列上以固定标注预算（50–400/期）选样：多判据不确定性 top-k 选择，预算外生固定，从不检验获取是否值得，也不含存储受限回放（CL 明确 out of scope）"
---

# CITADEL：连续分布漂移下的半监督主动学习恶意软件检测

题录与原件：Haque、Kamol、Amalapuram、Kreinovich、Rahman，arXiv:2511.11979，2025，共 21 页。本地原件经 MinerU extract 全文转换（2026-10-15）。

## 论文原结论

- 设置（§3.1）：每一时间步收到小标注集与大无标签池，$n_t \ll m_t$；检测器在漂移联合分布 $\mathcal{P}_t(X,Y)$ 下学习 $P(y=1|x)$。
- 样本选择（§4，Algorithm 2）：多判据统一打分——softmax margin 取反、$L_p$ 范数距离、低置信度取反——求和后**取 top-k 供标注**（原文第 11 行：`Q ← top-k samples in D_u by score(·)`）。预算 $k$ 是外生给定量（50/100/200/400）。
- 主结果（§5，Table 5）：LAMDA 上 budget 400 达 F1 77.7%，较 Chen-AL 提升 34 个百分点以上；APIGraph/Chen-AZ/MaMaDroid 依次 93.5/82.7/44.9。
- 训练侧：FixMatch 式一致性正则（Bernoulli bit flip 与 feature mask 两种针对二值特征的增强）+ 监督对比损失改善边界样本分离。

## 与本课题（RGA）的关系

- 覆盖「**预算受限的主动标注**」一侧：确实在受限标注预算下做漂移适应，且明确以 LAMDA 12 年序列为基准，是 RGA 主动获取分支的直接近邻。
- **不含「排序头部质量作为获取可行性的门」**：其预算是外生固定量，从不检验「获取是否值得」；多判据打分针对逐样本不确定性，不是对排序头部 lift $\alpha_s$ 的检验，也没有 $\ell_c(s)=1/(\alpha_s p_s)$ 一类的临界标注量形式化。
- **不含存储受限回放**：原文相关工作（§2）明文「CL addresses a different problem setting and is out of the scope of this work」。RGA 所在的「标注×存储」双预算组合不在其范围内。

## 不可直接声称的内容

- CITADEL 的多判据选择与 RGA 的排序门不可混同：前者回答「在预算内选哪些样本」，后者回答「预算应不应该花在这个年度」。
- 其 LAMDA F1 数字依赖其特征与划分实现，未经本仓库复现前不得引用为 LAMDA 协议基准。

## 证据等级

E2（本地全文已转换，MinerU extract；无本仓库复现实验）。
