---
title: "Are We Really Making Much Progress? A Worrying Analysis of Recent Neural Recommendation Approaches"
authors: [Maurizio Ferrari Dacrema, Paolo Cremonesi, Dietmar Jannach]
year: 2019
date: 2026-08-13
journal: "RecSys '19（Thirteenth ACM Conference on Recommender Systems），ACM，10 页"
source_pdf: "[[raw/papers/methodology/2019-Dacrema-Are-We-Really-Making-Much-Progress.pdf]]"
sha256: "772fd88ba7ae952415e34e5c3e89eced1bd77dfa2d2222a8c36440d6729bc9dd"
tags:
  - 负面结果
  - 可复现性
  - 弱基线
  - 评价方法论
  - 类型/论文
key_finding: "18 篇顶会深度推荐论文中仅 7 篇可复现，其中 6 篇被调优后的近邻或图启发式基线击败（摘要，第 1 页；表 1，第 3 页）。"
method: "系统检索 2015–2018 年 KDD/SIGIR/WWW/RecSys 长文，重构原实现使评价代码与训练代码分离，再用贝叶斯搜索（35 次采样）调优简单基线"
baseline: "TopPopular、UserKNN、ItemKNN、ItemKNN-CBF、ItemKNN-CFCBF、P3α、RP3β、SLIM"
aliases:
  - Dacrema2019-进步幻觉
  - Are We Really Making Much Progress
related:
  - "[[2021-Wu-Keogh-时序异常检测基准缺陷]]"
  - "[[2022-Audibert-深度网络是否有助于多变量时序异常检测]]"
  - "[[2022-Kim-时序异常检测的严谨评价]]"
---

# 神经推荐方法的“进步幻觉”

> Ferrari Dacrema, Cremonesi, Jannach, 2019, RecSys '19 · 10 页

## 一句话

在同一评价流程下把简单基线调优后重跑，18 篇顶会神经推荐论文只有 7 篇可复现，其中 6 篇在至少部分数据集上被近邻/图/线性基线击败；作者把这种现象归因于弱基线、基线未调参和数据划分错误，而不是方法本身失效。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：Are We Really Making Much Progress? A Worrying Analysis of Recent Neural Recommendation Approaches
- 会议：RecSys '19，2019 年 9 月 16–20 日，哥本哈根
- DOI：10.1145/3298689.3347058（第 1 页 ACM Reference Format）
- arXiv：1907.06902v3（第 1 页左侧竖排标记）
- 原件：`raw/papers/methodology/2019-Dacrema-Are-We-Really-Making-Much-Progress.pdf`

## 核心方法

- 复现判据（第 2 页，2.1 节）：源码可用或只需极小修改、至少一个原数据集可得、原训练测试划分公开或可按论文描述重建；只给骨架代码或只用私有数据均判为不可复现。
- 评价方式（第 2–3 页，2.2 节）：不统一重写评价协议，而是重构原实现，把训练、调参、预测与评价代码分离，再让基线走同一套评价代码，从而复刻原论文的度量与切分。
- 基线调参（第 4 页）：对所有基线用 Scikit-Optimize 贝叶斯搜索 35 次（前 5 次随机），邻域 k∈[5,800]，收缩项 h∈[0,1000]，α、β∈[0,2]。被复现方法直接沿用原论文报告的最优超参。

## 关键数字（含页码/表号）

- 复现率（表 1，第 3 页）：KDD 3/4（75%）、RecSys 1/7（14%）、SIGIR 1/3（30%）、WWW 2/4（50%），总计 7/18（39%）。
- CMN（表 2，第 4 页）：CiteULike-a 上 RP3β HR@5=0.8226 高于 CMN 0.8069；Epinions 上非个性化 TopPopular HR@5=0.5429，高于 CMN 0.4195。作者同时报告 Epinions 的 Gini 系数 0.69 对比 CiteULike-a 的 0.37（第 4 页正文）。
- MCRec（表 3，第 5 页）：MovieLens100k 上 ItemKNN PREC@10=0.3327 高于 MCRec 0.3077，REC@10 与 NDCG@10 同样占优。
- CVAE（表 4，第 5 页）：CiteULike-a REC@50 上 ItemKNN-CFCBF=0.1837，CVAE=0.0772；只有在列表长度 100 以上 CVAE 才在两个数据集上反超。
- CDL（表 5，第 5 页）：REC@50 上 ItemKNN-CBF=0.2135，CDL=0.0543。
- NCF（表 6，第 6 页）：Pinterest 上 RP3β HR@5=0.7105 高于 NeuMF 0.7024；MovieLens1M 上 NeuMF HR@5=0.5486 优于全部近邻基线，但线性方法 SLIM 达 0.5589 反超。
- SpectralCF（表 7 与图 1，第 6–7 页）：使用作者提供的 MovieLens 划分时 SpectralCF 的 Recall@20 比最好基线高约 50%；改用论文所述随机划分自行切分后，SpectralCF REC@20=0.1843 低于 TopPopular 0.1853。原划分测试集的 Gini 系数为 0.92，而随机划分约 0.79（第 7 页正文）。
- Mult-VAE（表 8–9，第 7 页）：Netflix 上 Mult-VAE NDCG@100=0.3756 与 SLIM 0.3745 几乎相同，Recall@100 上 Mult-VAE 0.5476 高于 SLIM 0.5289；这是唯一一个稳定超过所有简单基线的方法（第 7 页正文）。
- 方法学缺陷（第 5、6 页）：MCRec 与 NCF 的公开代码显示作者依据测试集选择 epoch；MCRec 使用非常规 NDCG 实现且论文未说明。

## 与本课题（LSPR23→LSPR24 加密恶意流量跨年度迁移）的关系

- 支持“共同预算强基线”纪律：本课题逐流 XGBoost 全量 AP=0.2244 高于逐流 MLP 0.1590 与完整 RWKV-7 状态递归，属于该论文所描述的典型情形——复杂模型未必胜过被认真调优的简单方法。引用本文可为“必须先把树模型与简单聚合基线调到最优再比较”提供方法论依据。
- 支持“数据划分本身可制造虚假提升”的论证：SpectralCF 案例（表 7，第 7 页）说明划分分布异常可让一个方法凭空领先 50%，这与本课题坚持跨年度划分、禁止用目标年标签选参的做法直接对应。
- 可迁移的操作：基线与候选方法共用同一评价代码路径；对每个基线执行同等预算的超参搜索并公开最终参数。

## 局限（不可直接声称的内容）

- 论文只覆盖 top-n 推荐任务，数据为评分/隐式反馈矩阵，没有网络流量、类别极不平衡、时间外推或跨年度分布漂移的证据。
- 论文没有度量分布偏移下的模型退化，也没有实体级聚合与逐流预测的对比，不能用来支持本课题“实体级聚合优于逐流”的具体结论。
- 论文自陈（第 9 页）分析仅限特定会议系列，且未把矩阵分解类传统方法全面纳入基线。

## 可引用的逐字原文（≤15 词）

- “progress is often claimed by comparing a complex neural model against another neural model”（第 8 页，4.2 节）
- “most of the reviewed works can be outperformed … by conceptually and computationally simpler algorithms”（第 9 页，第 5 节，中间省略号为节略）

## 证据记录

- 来源类型：完整论文（10 页全文，`pdftotext -layout` 抽取并逐页核对）
- 支持：弱基线与调参不足会造成“幻影进步”；简单方法在多数据集上可击败复杂神经模型
- 限制：无分布漂移、无安全数据、无实体级聚合证据
- 论断强度：有支持（评价方法论）/ 推论（迁移到加密流量检测）

## 文献信息

- ACM DL：<https://doi.org/10.1145/3298689.3347058>
- arXiv：<https://arxiv.org/abs/1907.06902>
- 代码（第 3 页脚注 5）：<https://github.com/MaurizioFD/RecSys2019_DeepLearning_Evaluation>
