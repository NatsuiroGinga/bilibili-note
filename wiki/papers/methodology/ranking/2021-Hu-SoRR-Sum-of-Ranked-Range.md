---
title: "Sum of Ranked Range Loss for Supervised Learning"
authors: [Shu Hu, Yiming Ying, Xin Wang, Siwei Lyu]
year: 2021
date: 2026-09-04
journal: "Journal of Machine Learning Research（JMLR），扩展自 NeurIPS 2020 会议版；arXiv:2106.03300"
source_pdf: "[[raw/papers/methodology/ranking/2021-Hu-SoRR-Sum-of-Ranked-Range-arXiv.pdf]]"
sha256: "37e1dc5e070f56a0abb24545506e3408b4190257b387abab3df374afb1e40be6"
tags:
  - 排序聚合
  - top-k损失
  - CVaR
  - 多层级聚合
  - 类型/论文
key_finding: "提出 SoRR（有序值域和）统一框架，把样本级聚合损失 AoRR 与标签级个体损失 TKML 组合为 TKML-AoRR；两个层级各自独立设置超参数（样本级 k、标签级 k′，及样本级下界 m），未要求两层共享同一聚合形状或参数，且实测样本层聚合方式的选择（average / AT_k / AoRR）显著影响标签噪声下的鲁棒性。"
method: "SoRR 定义为一组实数排序后连续区间 [m+1, k] 的和；样本层用 AoRR（top-k 均值减去 top-m 均值的差，可精确剔除已知比例的离群点）作为聚合损失，标签层用 TKML（top-k 多标签合页损失）作为个体损失，通过差凸算法（DCA）联合优化组合目标。"
baseline: "average 损失、maximum 损失、AT_k（top-k 均值）、TKML-Average、TKML-AT_k"
aliases:
  - SoRR
  - AoRR
  - TKML
  - TKML-AoRR
  - Hu2021-SoRR
---

# SoRR：有序值域和统一 top-k／CVaR 型聚合框架

> Hu, Ying, Wang, Lyu，2021/2022，JMLR（NeurIPS 2020 会议版扩展） · arXiv:2106.03300 · 44 个物理页

## 一句话

SoRR 把 max、average、top-k 均值（AT_k）、CVaR 统一为"排序后取连续值域区间求和/均值"的特例，并展示了一个**两层聚合组合的完整范例**：样本级用 AoRR（对训练样本的损失聚合，用于抗样本离群点）、标签级用 TKML（对多标签预测的个体损失，用于 top-k 标签命中），两层**各自独立设置超参数**，组合为单一目标 TKML-AoRR。

## 论文原结论

- 摘要／第 1 节（物理页 1）：聚合场景有两类——"aggregate loss"（跨训练样本聚合个体损失）与"multi-label 的 individual loss"（跨类别标签聚合预测分数）；average 对少数子群不敏感，maximum 对离群点敏感，AT_k（top-k 均值）是二者的折中但"稀释而非剔除"离群点影响。
- 第 2 节相关工作（物理页 2，原文引用 Rawat et al. 2020）："Rank-based losses are also popular to be used at the sample and label levels simultaneously... They use the average top-k methods both at the data sample and label levels to construct the final loss function."——即已有工作（doubly-stochastic mining, Rawat et al. 2020）在样本层与标签层**同时使用同一族算子（top-k 均值）**，但该工作"does not consider the outliers or noisy labels"，且"only works on multi-class problems"（不能处理多标签）。
- 第 5 节（物理页约 18–19，"TKML Loss for Multi-label Learning"）：标签层定义 TKML 个体损失，用超参数 `k`（多标签 top-k 命中阈值）。
- 第 6 节"Combination of AoRR and TKML"（物理页约 20，起始行原文）："The TKML individual loss applies to the multi-label learning problem at the label level. However, it may also be the case that the training samples for a multi-label learning problem include outliers. It is thus a natural idea to combine the TKML individual loss at the label level and the AoRR aggregate loss at the sample level to construct a more robust learning objective."——**两层组合的动机是两种不同的鲁棒性目标**：标签层要覆盖尽可能多真实标签（top-k 命中），样本层要抵御训练样本中的离群点。
- 同节明确记号区分："we use `k′` in the label level to distinguish `k` in the sample level"——**样本层 `k`（AoRR 的 top-k）与标签层 `k′`（TKML 的 top-k）显式使用不同符号、不同取值**，未要求二者相等或共享同一网格。
- 第 6.1 节实验（物理页约 21–22，Yeast 数据集，Table 10）：固定标签层 TKML 不变，比较三种样本层聚合——TKML-Average（样本层用普通均值）、TKML-AT_k（样本层用 top-k 均值）、TKML-AoRR（样本层用 AoRR）。结果：样本层聚合的选择对标签噪声下的鲁棒性有**实质性差异**（`k′=4` 时 TKML-AoRR 相对 TKML-Average 提升超过 10%；噪声水平从 0 升到 0.3 时，TKML-AT_k 性能下降近 10%，TKML-AoRR 只降约 1–1.2%）。

## 与"聚合一致性"问题的关系（本课题检索目的）

本文是本课题四个检索问题中**证据强度最高、最直接相关**的全文来源：

1. **对 Q1/Q2（是否要求聚合算子一致）**：本文的 TKML-AoRR 组合是"同一目标函数内，两个不同层级/角色分别用不同聚合算子、独立设置超参数"的**已发表、有实验验证的先例**。这与本课题询问的"同一模型内多个损失项使用实体分数时是否要求聚合算子一致"结构相似（本课题是"底座 BCE 用聚合 A、排序损失 BER 内的 `S_e` 用聚合 B"两个角色）。**该先例明确支持"不要求一致"这一方向**，但组合方式是**嵌套复合**（样本层聚合套着标签层个体损失），不是本课题"两个独立可加损失项各自形成实体分数"的结构——适用时需注明这一结构差异。
2. **对 Q3（若允许不一致，理由是什么）**：本文给出的理由是**角色不同导致鲁棒性目标不同**——标签层要"尽量覆盖真实标签"（top-k 命中，非鲁棒性问题），样本层要"抵御训练样本离群点"（鲁棒统计问题）。这是**独立于本课题、有明确文献依据的理由类型**："不同损失项承担不同角色"可以证成聚合算子独立选择。
3. **对 Q4（不一致是否导致具体问题）**：本文**没有报告"两层聚合算子不一致"本身导致的负面后果**（如梯度冲突）；相反，其消融（Table 10）显示的是"样本层聚合方式选得不好"（如普通均值不抗离群点）会降低鲁棒性，这是"选错聚合"而非"两层不一致"的问题。**未检索到该论文或其引用网络中有工作明确警告或论证"聚合算子不一致"本身是风险**。
4. **对已被本课题设计文档引用的既有断言**：`thesis/methods/ETA-实体内尾部聚合方案.md` 第九节声称"ATk 全文笔记、SoRR 全文笔记：`wiki/papers/methodology/ranking/`"，但在本次核查前该目录下**不存在任何提及 SoRR 或 Sum of Ranked Range 的笔记**（`rg -l "Sum of Ranked Range|SoRR" wiki/` 零命中）。本笔记补齐这一缺口；ETA 文档中引用的"SoRR 物理页 14"（AoRR 超额泛化"很难建立"）对应本文第 4.2 节（Connection with Conditional Value at Risk），与本文 PDF 物理页码基本吻合，但此前该引用缺少可点击的全文笔记支撑，本次核查前处于"仅原始 PDF 页码、无结构化笔记"的状态。

## 证据记录

- 全文：arXiv 预印本 PDF，44 页；已用 `pdf-converter`（`mineru-open-api extract`）转换全文并检索定位摘要、引言、相关工作、第 5–6 节（TKML 与组合损失）、结论；未逐字精读第 3–4 节（SoRR 定义、AoRR 分类校准与 CVaR 联系的完整证明）与附录证明。
- 官方链接：<https://arxiv.org/abs/2106.03300>
- 证据强度：直接占用"两层聚合各自独立超参数化并组合"这一设计先例；不覆盖 MIL 场景（袋是实体而非训练样本/标签），不覆盖两个**独立可加损失项**（而非嵌套复合）各自聚合的场景。

## 疑问 / 待验证

- Rawat et al. (2020) doubly-stochastic mining 原文未获取全文，仅通过本文转述了解其"样本层与标签层同用 top-k 均值"的做法；若需要直接引用该文的参数设置细节，需单独下载核验。
- 本文未讨论"两个独立可加损失项（而非嵌套复合）各自聚合是否需要一致"这一本课题的具体问法，本笔记的"可迁移"部分属于结构类比，不是对该问法的直接实验回答。
