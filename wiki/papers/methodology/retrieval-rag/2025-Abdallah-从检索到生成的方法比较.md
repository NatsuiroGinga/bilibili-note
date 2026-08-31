---
title: "From Retrieval to Generation: Comparing Different Approaches"
authors: [Abdelrahman Abdallah, Jamshid Mozafari, Bhawna Piryani, Mohammed Ali, Adam Jatowt]
year: 2025
date: 2026-08-31
journal: "arXiv 预印本 2502.20245（cs.CL），2025-02-27，注释为 work on progress，未定稿"
source_pdf: "[[raw/papers/methodology/retrieval-rag/2025-Abdallah-From-Retrieval-to-Generation-Comparing-Approaches-arXiv2502.20245.pdf]]"
sha256: "3ae7d8530e1d046b708197e5c1a99e24b9fbe17c2280bdbfa4ed7edfb3928766"
sha256_prefix16: "3ae7d8530e1d046b"
tags:
  - 检索与生成比较
  - 开放域问答
  - 重排
  - 证据不足
  - 类型/论文
key_finding: "全文没有稀疏、稠密与稀疏—稠密融合的干净三分对照；其所谓 hybrid 指的是检索加生成文档再加 LLM 重排，因此不能用本文论证混合检索本身有效。"
method: "在 ODQA、文档重排与语言建模三类任务上比较 BM25／DPR／MSS／MSS-DPR／Contriever、GenRead 生成式，以及 UPR 与 RankGPT 重排的各种组合。"
baseline: "BM25 与各稠密检索器；FiD、REALM、RAG 等阅读理解基线。"
aliases:
  - Abdallah2025-Retrieval-to-Generation
---

# 从检索到生成的方法比较

> Abdallah、Mozafari、Piryani、Ali、Jatowt（University of Innsbruck），2025，arXiv 2502.20245 · 17 个物理页 · Zotero 条目 `2T8HMMWX`

## 论文原结论

- 物理第 4 页 4.1 节给出数据：NQ（`79,168` 训练 / `8,757` 开发 / `3,610` 测试）、TriviaQA（`78,785` / `8,837` / `11,313`）、WebQ（`3,417` / `361` / `2,032`）；证据库为 2018-12 英文维基百科，每篇切成 100 词的不重叠段落，**超过 2,100 万段落**。检索评测另用 TREC-DL19（`43` 查询）、DL20（`54` 查询）与 BEIR（18 个任务），语言建模用 WikiText-103。
- 物理第 5 页表 1（Top-1 准确率，NQ / TriviaQA / WebQ）：无监督检索器 `MSS` `19.28 / 30.76 / 13.66`、`BM25` `22.11 / 46.30 / 18.90`、`Contriever` `22.16 / 34.16 / 19.98`；有监督 `DPR` `48.67 / 57.47 / 44.83`、`MSS-DPR` `50.17 / 61.64 / 44.24`；生成式 `GenRead` `45.76 / 69.41 / 51.03`。
- 物理第 6 页 5.2 节：`DPR` 的 NQ Top-10 从 `74.54%` 经 UPR 提到 `80.44%`；`MSS-DPR + RankGPT` 达 `81.47%`，无重排时为 `77.87%`。同节说明 RankGPT 的重排开销「costing over 1,500 for evaluations across NQ and WebQA」，因此 TriviaQA 上只用了 UPR。
- 物理第 7 页 5.3 节（LLaMA-3.3 8B，精确匹配）：`BM25` 仅检索 `14.90`、仅生成 `24.68`、`R+G` `25.51`；`BM25+RankGPT` 在 NQ 上 `28.45`、WebQA 上 `19.73`。
- 物理第 8 页表 5（`nDCG@10`，TREC 与 BEIR）：`BM25` 行的 BEIR 均值为 `43.42`，其中 DL19 `50.58`、DL20 `47.96`、Robust04 `40.70`；`BM25+RankGPT` BEIR 均值 `49.37`；`BM25+GenRead+RankGPT` BEIR 均值 `52.59`，Robust04 `58.48`。
- 物理第 8 页表 4：Llama 2-7B 在检索与生成文档上训练后，「Combine Document」得 NQ `57.4`、TriviaQA `75.7`、WebQ `53.6`，高于 FiD-xl 的 NQ `50.1`。
- 物理第 8 页第 6 节与第 12 页 A.2 节（语言建模困惑度）：GPT-2 Small 无增强 `37.5`、BM25 检索 `29.56`；GPT-2 XL 从 `20.0` 降到 `16.56`，仅生成反而升到 `24.91`；OPT-13B 从 `12.7` 降到 `10.83`。作者结论是语言建模上混合与生成都没有稳定超过纯检索。
- 物理第 9 页局限：混合模型计算复杂度随语料与文档长度增长；稠密检索器效果高度依赖训练语料质量与多样性；混合模型对检索与生成组件之间的配合敏感；评测局限于 NQ、BEIR 等标准基准，应扩展到医疗、法律等领域。

## 与本课题的关系

本节对照的是本仓库本地文献检索工具 `scripts/literature_search`。**本篇的结论是「证据不足以支持本项目的任何设计决定」，该否定结论与正面结论同等重要，不得在后续引用中淡化。**

- **全文没有稀疏／稠密／稀疏—稠密融合的干净三分对照**。这是本篇对本项目最关键的事实。表 5 中被称为 hybrid 的行是 `BM25+GenRead+RankGPT`，即「稀疏检索 ＋ LLM 生成的文档 ＋ LLM 重排」；表 1 与表 2 中 BM25 与稠密检索器只是并列报告，没有把两者的结果融合成一路再对照。因此 `43.42 → 52.59` 度量的是**加生成文档与加 LLM 重排**的收益，**不能**用来论证混合检索本身有效。
- **回原件时发现三处内部不一致，进一步降低其证据权重**（均为物理页码可查，表格字号较小，建议引用前再核一次）：
  1. 物理第 12 页 A.1 节称 TriviaQA 上「DPR achieves the highest Top-1 accuracy at 75.4%, significantly outperforming BM25, which achieves only 54.0%」，而物理第 5 页表 1 的同一组指标是 DPR `57.47`、BM25 `46.30`，两者差距很大且无法用 Top-5／Top-10 口径解释。
  2. 物理第 8 页第 7 节称「on Robust04 dataset, BM25+GEN+RankGPT achieves an nDCG@10 score of 58.48, compared to 43.42 for BM25」，但表 5 中 BM25 的 Robust04 是 `40.70`，`43.42` 是 BM25 的 BEIR 均值，该句把单数据集与跨集均值混用作对照。
  3. 物理第 8 页第 6 节称 LLaMA-3.3 70B 的 `R+G` 困惑度 `32.14`「compared to the retrieval-only model's 24.91」，而第 12 页 A.2 节把 `24.91` 明确写成 GPT-2 XL 的**仅生成**结果。
- **当前评测集能否检验**：不适用。本项目的检索工具是纯检索、不做生成，本篇一半以上内容（GenRead、上下文学习、困惑度）在本项目没有对应接口。
- **一条曾被本代理列为「弱旁证」的内容现予撤回**：上一轮曾把本文「纯 BM25 检索困惑度低于混合」当作本项目「向量通道更差」的同向旁证。主代理 2026-08-31 的中立查询实测已把通道次序反转为向量 `0.3250` 高于词法 `0.2250`（本代理未复现），该类比的前提不复存在；且语言建模困惑度与检索命中率本就是不同任务的不同指标，原类比过弱，予以撤回。
- **可保留的唯一用途**：作为「hybrid 一词在文献中被用于至少两种完全不同含义（稀疏—稠密融合，与检索—生成融合）」的实例。本项目在写任何涉及 hybrid 的表述时应明确限定为前者。

## 证据记录

- 全文：`raw/` 原件 17 个物理页，2026-08-31 读取第 1–12 页核验。已核验数据规模（第 4 页）、表 1 与表 2（第 5 页）、重排结果与成本（第 6 页）、表 3 与上下文学习（第 7 页）、表 4 与表 5 及语言建模（第 8 页）、局限（第 9 页）、附录 A.1 与 A.2（第 12 页）。第 13–17 页为参考文献续与附录表，未逐页核验。
- 首次抓取用 arXiv HTML；本次回原件核对，表 1 与表 5 的数字一致，**新增发现上述三处内部不一致，为 HTML 阶段未察觉**。
- arXiv：<https://arxiv.org/abs/2502.20245>
- Zotero 条目 `2T8HMMWX`。
- 原件 sha256 为 `3ae7d8530e1d046b708197e5c1a99e24b9fbe17c2280bdbfa4ed7edfb3928766`。
- 证据强度：完整全文（正文部分）；**证据权重低**，标注 work on progress 未定稿，存在内部不一致，只能作为术语辨析与背景引用，不得支撑本项目任何设计决定，不进入论文正文。
