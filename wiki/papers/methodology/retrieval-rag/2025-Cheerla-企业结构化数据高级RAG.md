---
title: "Advancing Retrieval-Augmented Generation for Structured Enterprise and Internal Data"
authors: [Chandana Cheerla]
year: 2025
date: 2026-08-31
journal: "arXiv 预印本 2507.12425（cs.CL/cs.AI/cs.CE/cs.IR），2025-07-16，IIT Roorkee，单作者，无会议信息"
source_pdf: "[[raw/papers/methodology/retrieval-rag/2025-Cheerla-Advancing-RAG-Structured-Enterprise-Data-arXiv2507.12425.pdf]]"
sha256: "f69bb3aef06e2bb99be171478448ed43fc6dd3c2bbe74994e435824f067ec047"
sha256_prefix16: "f69bb3aef06e2bb9"
tags:
  - 企业RAG
  - 混合检索
  - 评测协议缺陷
  - 反面教材
  - 类型/论文
key_finding: "评测协议的五项关键信息全部缺失（语料规模、查询条数、标注来源、显著性、通道消融），基线中没有任何词法检索，且正文对分块大小给出三个互相矛盾的数值；其 0.6/0.4 融合权重自称经验确定但全文无支撑数据。"
method: "递归字符切分＋Camelot 抽表＋spaCy NER 元数据＋all-mpnet-base-v2 稠密与 BM25 加权融合＋交叉编码器重排＋LLM 查询改写＋Mistral-7B 生成。"
baseline: "Direct LLM（无检索）与 Naive RAG（仅稠密、无重排）。"
aliases:
  - Cheerla2025-Enterprise-RAG
---

# 企业结构化数据的高级 RAG 框架

> Cheerla（IIT Roorkee），2025，arXiv 2507.12425 · 11 个物理页 · Zotero 条目 `7VSGIWHH`

## 论文原结论

- 物理第 5 页 3.3.3 节给出融合公式：`Score_combined = 0.6 × Score_dense + 0.4 × Score_sparse`，并称「This weighting was determined empirically to balance semantic and lexical relevance」。
- 物理第 4—5 页给出管线其余部分：pdfplumber 抽文本后用递归字符切分；Camelot 抽表为 JSON 并按行索引，失败时回退 pdfplumber；spaCy NER 标注实体元数据；稠密向量用 `all-mpnet-base-v2` 存入 FAISS HNSW（`M=32`、`efConstruction=200`、`efSearch=50`）；稀疏用 BM25；`ms-marco-MiniLM-L-12-v2` 交叉编码器重排；LLaMA 与 Mistral 做查询改写与扩展；`ConversationBufferMemory` 保留最近 10 轮。
- 物理第 8 页表 1 是全文唯一结果表：`Precision@5` 依次为 Direct LLM `62%`、Naive RAG `75%`、Advanced RAG `90%`；`Recall@5` `58% / 74% / 87%`；`MRR` `0.60 / 0.69 / 0.85`；Faithfulness `2.8 / 3.0 / 4.6`；Completeness `2.3 / 2.5 / 4.2`；Relevance `2.9 / 3.2 / 4.5`（后三项为 5 分李克特量表）。
- 物理第 7 页 4.3 节说明基线构成：Naive RAG 为「Recursive Character-Level Chunking」加「Dense Retrieval Only」，无重排、无过滤；Direct LLM 为检索块直接送 LLM 而不重排不过滤。**全文没有任何只用 BM25 的基线。**
- 物理第 9 页第 6 节局限：静态索引需全量重建；嵌套或层次表头的复杂表格处理不佳；反馈依赖用户显式点赞点踩；查询改写会误解意图或过度扩展；扩展到超大语料时检索延迟与内存有压力。

## 回原件核验发现的协议缺陷

以下为 2026-08-31 逐页核验的结果，每条都是「论文未报告」或「论文自相矛盾」，不是本代理的推断：

1. **未报告语料规模**。物理第 7 页 4.1 节只说数据集由「publicly available HR policies」与企业报告构成，另提到 data.gov.in、UCI Adult 与某 HR Analytics GitHub 仓库；全文无文档数、无分块数。
2. **未报告评测查询条数**。表 1 的 `Precision@5`／`Recall@5`／`MRR` 是在多少条查询上算出来的，全文没有给出。
3. **未说明相关性标注来源**。物理第 8 页 4.6 节只说定性指标由「human annotators」按 5 分量表评分，并补充「And also we use LLMs as an another evaluator」；对三项检索指标所依据的相关性判定，全文未说明由谁、按什么标准产生，也无标注者人数与一致性统计。
4. **无显著性检验、无方差、无多次运行**。表 1 只有单点数值，无置信区间、无随机种子说明。
5. **无通道消融**。全文没有 BM25-only、稠密-only 与融合的对照。物理第 8 页 4.8 节声称「Each enhancement—hybrid retrieval, cross-encoder reranking, and query refinement—provided incremental improvements」，但**全文未给出任何逐组件的数值**，该论断无数据支撑。
6. **分块大小三处互相矛盾**。物理第 4 页 3.1.1 节写「chunk size of 2000 characters and a 500-character overlap」；物理第 7 页 4.3 节写实验了 `500`、`700`、`1000` 字符且「approximately 700 characters yielded optimal performance」；物理第 2 页贡献列表写「empirically tuned chunk sizes (700 tokens)」。字符与 token 单位混用，且 2000 与 700 无法同时成立。

## 与本课题的关系

本节对照的是本仓库本地文献检索工具 `scripts/literature_search`。**本篇的结论是「不得作为本项目任何设计依据」，只保留为反面教材。该否定结论与正面结论同等重要，不得在后续引用中淡化。**

- **`0.6 / 0.4` 融合权重不得被本项目采用**。按仓库根 `AGENTS.md` 的魔法数字门禁，融合权重属于必须建立可追溯依据的数值；本文只写「empirically determined」而无任何支撑实验、无消融、无搜索范围，机制依据与本数据可行性核验两项都不满足。本项目若要设定融合参数（含当前的 `rrf_constant`），必须用不接触最终评测标签的自有诊断实验确定，并登记依据台账。
- **其提升与本项目关心的问题无关**。`90%` 对 `75%` 的对照是「完整管线」对「仅稠密无重排」，基线中没有词法检索，因此这组数字不回答「混合相对单通道是否更好」。
- **当前评测集能否检验**：不适用，且不值得检验。
- **保留的唯一用途**：与 [[2022-Hofstatter-TripClick健康检索强基线]] 构成一正一反的对照样本——后者示范了如何定位并修复基线缺陷，前者示范了在基线缺失、协议缺失的条件下报出大幅提升。两者共同支撑本项目的一条口径要求：**报告任何融合增益时，必须同时给出各单通道在同一评测集、同一截断下的数值**。
- **一处仍成立的观察**：本文用固定权重的加权求和融合，本项目用固定常数的 RRF，两者都属于「不学习的融合」。本文没有提供任何证据说明加权求和优于或劣于 RRF，因此**不能**据本文考虑更换融合方式。

## 证据记录

- 全文：`raw/` 原件 11 个物理页，2026-08-31 逐页读取核验。已核验摘要与贡献（第 1–2 页）、方法各节（第 4–5 页）、架构图（第 6 页）、数据与基线（第 7 页）、评测指标与表 1（第 8 页）、局限（第 9 页）、参考文献（第 10–11 页）。
- 首次抓取用 arXiv HTML 并做过一次定向协议核验；本次回原件逐页复核，表 1 数字一致，**新增发现第 6 条分块大小三处矛盾，为 HTML 阶段未察觉**。
- arXiv：<https://arxiv.org/abs/2507.12425>
- Zotero 条目 `7VSGIWHH`。
- 原件 sha256 为 `f69bb3aef06e2bb99be171478448ed43fc6dd3c2bbe74994e435824f067ec047`。
- 证据强度：完整全文；**不构成任何可用证据**。仅作为评测协议缺陷的反面样本保留，不支撑本项目设计决定，不进入论文正文。
