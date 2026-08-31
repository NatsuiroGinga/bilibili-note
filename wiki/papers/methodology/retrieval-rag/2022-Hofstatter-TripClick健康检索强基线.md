---
title: "Establishing Strong Baselines for TripClick Health Retrieval"
authors: [Sebastian Hofstätter, Sophia Althammer, Mete Sertkan, Allan Hanbury]
year: 2022
date: 2026-08-31
journal: "ECIR 2022（arXiv 2201.00365，2022-01-02，TU Wien）"
source_pdf: "[[raw/papers/methodology/retrieval-rag/2022-Hofstatter-Establishing-Strong-Baselines-TripClick-ECIR-arXiv2201.00365.pdf]]"
sha256: "c7ec2f48feca939f03a8199b1dda1b196b09e5302ed53b4175cb38a69d45a2f0"
sha256_prefix16: "c7ec2f48feca939f"
tags:
  - 检索基线
  - 评测集构造
  - 稠密检索
  - 负采样
  - 类型/论文
key_finding: "原 TripClick 神经基线之所以弱，根因是负采样把未点击结果当负例产生大量假负例；换掉负采样策略后同一模型 MRR@10 从 .41 升到 .6，说明大幅提升可以完全来自修复评测与训练协议而非模型改进。"
method: "用 BM25 前 500 候选重做负采样生成 1000 万训练三元组，再训练 BERT_CAT、ColBERT、TK 重排与 BERT_DOT 稠密检索。"
baseline: "TripClick 原始发布的 BM25、ConvKNRM、TK 基线。"
aliases:
  - Hofstatter2022-TripClick
  - TripClick强基线
---

# TripClick 健康检索的强基线

> Hofstätter、Althammer、Sertkan、Hanbury（TU Wien），2022，ECIR 2022 · 9 个物理页 · Zotero 条目 `444M5V6T`

## 论文原结论

- 物理第 2 页 2.1 节给出集合规模：TripClick 含 `1.5M` 段落（平均 `259` 词）、`680` 千条点击训练查询（平均 `4.4` 词）、`3,525` 条测试查询；按查询频次分 Head、Torso、Tail 三个测试集，**每个 `1,175` 条**。Head 用 DCTR 点击模型构造相关性信号，Torso 与 Tail 用原始点击。
- 物理第 4 页 3.1 节给出弱基线的根因：「we discovered a flaw in the published negative sampling procedure, that non-clicked results – ranked above the clicked ones – are included as negative sampled passages. We hypothesize this leads to many false negatives in the training set, confusing the models during training」，并说明佐证是训练遥测显示逐对训练准确率低、`BERT_CAT` 打分间隔缺乏区分度。
- 物理第 4—5 页给出替换后的训练数据生成：每训练查询取 `500` 个 BM25 候选；每个「查询—相关段落」对无放回随机采样至多 `20` 个负候选；剔除相关池中的候选（不论相关等级）；丢弃位置信息；打乱后保存 `1000` 万三元组。
- **物理第 5 页给出 45–50% 的确切口径**：「Our new training set gave us a 45−50% improvement on MRR@10 (from .41 to .6) and nDCG@10 (from .21 to .30) for the HEAD **validation** queries using the same PubMedBERT_CAT model and setup.」即：同一模型、同一配置，只换训练数据；且这组数字是 **HEAD 验证集**上的，不在表 1 中。
- 物理第 5 页表 1（`nDCG@10` / `MRR@10`，Head / Torso / Tail）：
  - 原始基线：`BM25` `.140 .276` / `.206 .283` / `.267 .258`；`ConvKNRM` `.198 .420` / `.243 .347` / `.271 .265`；`TK` `.208 .434` / `.272 .381` / `.295 .280`
  - 本文重排（BM25 top-200）：`TK` `.232 .472` / `.300 .390` / `.345 .319`；`ColBERT`-PubMedBERT-Abstract `.278 .557` / `.340 .431` / `.387 .361`；`BERT_CAT`-BERT-Base `.287 .579` / `.349 .453` / `.396 .366`；`BERT_CAT`-PubMedBERT-Full `.298 .582` / `.365 .462` / `.412 .381`；三模型集成 `.303 .601` / `.370 .472` / `.420 .392`
- 物理第 5 页 4.1 节指出原始基线的分布问题：原基线在 Head 上最多提升 `6` 个 `nDCG@10` 点，但在 Tail 上只有 `1−3` 点差距，「This is a pressing issue, as those queries make up **83%** of all Trip searches」。
- 物理第 6 页表 2（仅 Head，稠密检索）：`BM25` `J@10 31%`、`nDCG@10 .140`、`MRR@10 .276`、`R@100 .499`、`R@200 .621`、`R@1K .834`；`BERT_DOT`-SciBERT `41%`、`.243`、`.530`、`.562`、`.640`、`.793`；`BERT_DOT`-PubMedBERT `40%`、`.235`、`.509`、`.582`、`.673`、`.828`。
- 物理第 6 页 4.2 节的结论与保留：稠密检索在 top-10 精度与各召回截断上都显著超过 BM25，**唯独 `R@1K` 例外**（BM25 `.834` 仍为该列最高）；作者还写道「surprisingly, the coverage for dense retrieval increases compared to BM25. Future annotation campaigns should explore the robustness of these click-based evaluation results.」
- 物理第 2 页脚注承认边界：TripDatabase 允许用户按流行度、来源质量、纯相关性等不同排序方案检索并按分面过滤，这些信息不在公开数据中。

## 与本课题的关系

本节对照的是本仓库本地文献检索工具 `scripts/literature_search`。

- **最直接的可迁移点：评测装置本身会决定结论**。本文的 `45–50%` 提升完全来自修复训练数据构造（物理第 5 页），与模型改进无关。本项目 2026-08-31 发生的是同一类问题的镜像：主代理发现旧评测的查询取自笔记自身字段，而 `title` 被加进每个分块前缀、`key_finding` 等六个字段被并入正文，查询文本字面存在于被索引内容中，系统性偏袒词法通道，使词法虚高到饱和（本代理未复现该诊断，仅记录主代理结论）。两者根因同类：**先怀疑测量装置，再怀疑方法**。
- **可迁移：判定覆盖率随系统而变是已知风险**。物理第 6 页表 2 的 `J@10` 显示 BM25 为 `31%`、稠密为 `39–41%`，作者明确提示点击式评测结果的稳健性需要后续标注活动检验。本项目用论文摘要作中立查询时，同样存在「哪些笔记被判为正确命中」依赖于构造方式的问题，应当把判定口径与覆盖率一并记录，而不是只报命中率。
- **可迁移且当前可检验：分截断报告，而不是只报单一截断**。本文稠密检索在 `nDCG@10` 与 `R@100`／`R@200` 上胜过 BM25，却在 `R@1K` 上输给 BM25。对应到本项目，词法通道在浅截断上弱（主代理实测命中率@10 为 `0.2250`，低于向量 `0.3250`）并不等于它在深截断上也弱；若深截断仍有互补召回，就构成保留词法通道参与融合的理由。这是当前中立评测集**可以直接检验**的一条，成本只是多报几个截断。
- **可迁移：按难度分层评测**。本文用 Head/Torso/Tail 各 `1,175` 条把单一评测集拆成三档，并指出 Tail 占全部检索的 `83%`。本项目的 200 条中立查询目前是单一池，分层后可以看出增益集中在哪一档。分层本身不产生难查询，需要在构造查询时就引入分档依据。
- **不可迁移**：`BERT_CAT`／`ColBERT`／领域预训练这条路线。其训练依赖 `1000` 万三元组和 `680` 千条点击查询，本项目既无点击日志也无相关性标注。
- **不可直接比较的地方**：表 1 中 BM25 在 Head 上的 `nDCG@10`（`.140`）低于 Tail（`.267`），但两档的相关性信号构造方式不同（Head 用 DCTR 点击模型，Torso/Tail 用原始点击），跨档绝对值不可直接比较，只能在同一档内比较系统。

## 证据记录

- 全文：`raw/` 原件 9 个物理页，2026-08-31 逐页读取核验。已核验集合规模与分档（第 2 页）、模型族说明（第 3 页）、负采样缺陷与新数据生成（第 4 页）、表 1 与 45–50% 口径（第 5 页）、表 2 与稠密检索结论（第 6 页）。第 7–9 页为参考文献。
- 首次抓取用 ar5iv HTML，本次回原件页码复核。**HTML 阶段未能确定 45–50% 对应哪组配置，本次已在物理第 5 页确认为 HEAD 验证集、同一 PubMedBERT_CAT 模型与配置**，该未关闭疑点已关闭。
- arXiv：<https://arxiv.org/abs/2201.00365>；代码 <https://github.com/sebastian-hofstaetter/tripclick>
- Zotero 条目 `444M5V6T`。
- 原件 sha256 为 `c7ec2f48feca939f03a8199b1dda1b196b09e5302ed53b4175cb38a69d45a2f0`。
- 证据强度：完整全文；构成本项目**评测集构造与评价纪律**的对照来源，不构成本课题效果证据，不进入论文正文。
