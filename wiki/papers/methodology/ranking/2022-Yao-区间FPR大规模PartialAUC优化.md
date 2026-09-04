---
title: "Large-scale Optimization of Partial AUC in a Range of False Positive Rates"
authors: [Yao Yao, Qihang Lin, Tianbao Yang]
year: 2022
date: 2026-09-04
journal: "arXiv preprint arXiv:2203.01505（NeurIPS 2022；University of Iowa / Texas A&M University）"
source_pdf: "[[raw/papers/methodology/ranking/2022-Yao-Large-Scale-Partial-AUC-FPR-Range-arXiv.pdf]]"
sha256: "f3b17d276e26c936aa9753fe4882ee5f7cc13a59575a3df516c926dcff9d7e5c"
tags:
  - Partial AUC
  - 差凸规划
  - Moreau包络平滑
  - SoRR
  - 类型/论文
key_finding: "把区间 FPR∈[α,β] 的 Partial AUC 优化写成非光滑差凸（DC）规划，用 Moreau 包络平滑技术给出近似梯度下降法，配合随机块坐标更新提升大数据效率，建立 Õ(1/ε⁶) 复杂度的近 ε-临界解；该算法同时可用于求解此前缺乏高效求解器的 sum of ranked range（SoRR）损失最小化。将 FPR 限定在 [α,β]（α>0）的动机是『ROC 空间中某些应用下部分 FPR 区间没有实际相关性』，不是『低 FPR 段估计不准』。"
method: "把非凸区间 PAUC 目标转化为差凸（difference-of-convex）规划，对任意光滑预测函数（含深度网络）用 Moreau 包络平滑非光滑项，得到近似梯度下降算法；引入随机块坐标更新处理大规模数据。"
baseline: "既有区间 FPR PAUC 优化算法（原文称不可扩展到大数据、不适用于深度学习）"
aliases:
  - Yao2022-PAUCRangeFPR
---

# 区间假阳性率下的大规模 Partial AUC 优化

> Yao, Lin, Yang，2022，arXiv:2203.01505（NeurIPS 2022）· 正文约 35 物理页（含附录）

## 一句话

把 FPR 限定在区间 `[α,β]`（`α>0`）的 Partial AUC 优化问题转化为非光滑差凸规划，用 Moreau 包络平滑给出可扩展到深度学习的近似梯度算法，同一算法框架还能求解此前缺乏高效求解器的 sum of ranked range（SoRR）损失。

## 论文原结论

- 摘要：AUC 汇总了 ROC 空间全部 FPR 上的 TPR，但**"which may include the FPRs with no practical relevance in some applications"**（某些应用下部分 FPR 区间没有实际相关性）；Partial AUC 只汇总特定 FPR 区间上的 TPR，是更合适的度量。既有区间 FPR 的 PAUC 优化算法不可扩展到大数据、不适用于深度学习。
- 方法：把问题转化为对任意光滑预测函数（含深度网络）成立的非光滑差凸（DC）规划，受近期非光滑 DC 优化进展启发，用 Moreau 包络平滑技术给出高效近似梯度下降法；引入随机块坐标更新提升大数据处理效率。
- 复杂度：建立寻找近 `ε`-临界解的 `Õ(1/ε⁶)` 复杂度。
- 该算法可直接用于最小化 sum of ranked range（SoRR）损失（同样此前缺乏高效求解器），并在线性模型与深度网络上数值验证了区间 FPR 下 PAUC 最大化与 SoRR 损失最小化的有效性。

## 与本课题的关系（本课题检索目的：核查"低 FPR 段被放弃"是否有已发表先例）

本文是 `thesis/methods/第三章-极端分位数CVaR估计文献核查.md` **Q4.3（一处需要澄清的非先例）的证据来源**：

- 该核查文档明确指出：本文摘要给出的动机是**"低 FPR 段无实际相关性"**，**不是"低 FPR 段估不准"**。**该文不能被引用为"因不可表示而放弃档位"的先例**——这是一处需要澄清、避免误引的反例，而非本课题可直接采用的处置依据。本次全文核验确认摘要原文措辞（"no practical relevance"）与该核查文档的引用一致，未发现摘要之外有相反表述（该核查文档此前标注"正文是否另有论述未核"，本次已核对全文，第 1 节引言部分同样延续摘要的"实际相关性"表述，未发现"估计不准"这一动机的正面陈述）。
- 本文与已入库的 `wiki/papers/methodology/ranking/2021-Hu-SoRR-Sum-of-Ranked-Range.md`（SoRR）构成同一优化目标族的求解器工作——本文提出的 DC 规划 + Moreau 包络平滑求解器可直接用于 SoRR 损失最小化，是"排序类损失通用求解框架"的一个例证，但与本课题极端分位数 CVaR/BER 训练的批量下界问题无直接方法论重叠（本文关注的是**区间约束的算法可扩展性**，不涉及批内负样本数不足导致的梯度不可表示问题）。

## 证据记录

- 全文：arXiv 预印本 PDF / NeurIPS 2022 会议论文，正文约 35 物理页（含附录）；已用 `pdf-converter`（`mineru-open-api extract`）全文转换，核对摘要动机措辞、方法框架与复杂度结论。
- 官方链接：<https://arxiv.org/abs/2203.01505>；NeurIPS 2022 正式发表。
- 证据强度：原为该核查文档标注的 `L3`（仅摘要，未通读全文）；**本次下载官方 PDF 并全文精读后升级为本地全文 `L1`**，确认"无实际相关性"动机贯穿摘要与引言，未发现"估计不准"的替代动机表述。

## 疑问 / 待验证

- 本笔记未逐条核验 Moreau 包络平滑的具体推导与 `Õ(1/ε⁶)` 复杂度证明的完整细节，仅核对了方法框架与结论陈述。
- 未核实本文与 SoRR 原论文（Hu et al. 2021）在求解器层面的具体技术差异，两者关系仅基于本文摘要与引言的自述。
