---
title: "Rank-K: Test-Time Reasoning for Listwise Reranking"
authors: [Eugene Yang, Andrew Yates, Kathryn Ricci, Orion Weller, Vivek Chari, Benjamin Van Durme, Dawn Lawrie]
year: 2025
date: 2026-08-31
journal: "arXiv 预印本 2505.14432（cs.IR/cs.CL），2025-05-20，标注 Preprint. Under review."
source_pdf: "[[raw/papers/methodology/retrieval-rag/2025-Yang-Rank-K-Test-Time-Reasoning-Listwise-Reranking-arXiv2505.14432.pdf]]"
sha256: "f4453ea2a1df37083143c734aad42a55b929795681eee605a32da40ebcb4f9d5"
sha256_prefix16: "f4453ea2a1df3708"
tags:
  - 列表式重排
  - 测试时推理
  - 跨语言检索
  - 倒数排名融合
  - 类型/论文
key_finding: "重排增益随一阶段强度单调衰减：同一模型在 BM25 上相对一阶段 +26%，在 SPLADE-v3 上只剩 +12%；而 RankZephyr 在强一阶段上是 −6%，弱重排器会主动损坏已经很好的排序。"
method: "由 QwQ-32B 微调，蒸馏 DeepSeek-R1 的推理轨迹；输入查询与带编号段落列表，输出允许并列的序号排列。"
baseline: "一阶段 BM25 与 SPLADE-v3；重排基线 RankZephyr、Rank1-32B、DeepSeek-R1 教师、Naive Rank-K。"
aliases:
  - Yang2025-Rank-K
  - Rank-K
---

# Rank-K：测试时推理的列表式重排

> Yang、Yates、Ricci、Weller、Chari、Van Durme、Lawrie（Johns Hopkins University），2025，arXiv 2505.14432 · 15 个物理页 · Zotero 条目 `EPDCN9PC`

## 论文原结论

- 物理第 4 页 3.3 节：由 QwQ 32B 用 LoRA 微调，学习复现 DeepSeek-R1 生成的推理轨迹与排名；训练 2 轮，批量 `128`，学习率 `1e-4`，用 `128` 张 AMD MI250X。物理第 3 页 3.1 节说明训练数据来自 MS MARCO v1，采样 `50k` 查询（约占去重后训练查询的 10%），构造 `100k` 个查询—段落集对，每个含 10 到 20 个段落。
- 物理第 4 页表 1：生成训练数据时每次调用平均输入 `1,024.65` token、输出 `2,408.85` token，即输出是输入的 `2.4` 倍，90 分位输出 `3,957` token；整批耗时约 `36` 小时、约 `1,900` 美元。
- 物理第 5 页表 2 给出评测集规模：TREC DL 2019（`43` 查询）、DL 2020（`54` 查询），共享 `8,841,823` 文档、平均长度 `334.79`；NeuCLIR 波斯语（`174` 查询 / `2,232,016` 文档）、俄语（`171` / `4,627,541`）、中文（`167` / `3,179,206`）。同页说明 NeuCLIR 主表用的是**译成英文的文档**，且所有重排实验把文档截断到 `450` token，重排一阶段的 top-20。
- 物理第 7 页表 3 主结果（`nDCG@10`，末列为五数据集均值与相对一阶段的增幅）：
  - `BM25` 一阶段 `0.416`；`RankZephyr` `0.424 (2%)`；`Rank1-32B` `0.506 (22%)`；`R1 Teacher` `0.543 (30%)`；`Naive Rank-K` `0.492 (18%)`；`Rank-K` `0.525 (26%)`
  - `SPLADE-v3` 一阶段 `0.571`；`RankZephyr` `0.539 (−6%)`；`Rank1-32B` `0.609 (7%)`；`R1 Teacher` `0.645 (13%)`；`Naive Rank-K` `0.621 (9%)`；`Rank-K` `0.642 (12%)`
- **物理第 6 页给出本文最重要的方法论判断**：「RankZephyr failed to improve the first-stage ranking on TREC NeuCLIR, resulting in a macro-average only 2% improvement and even 6% *degradation* in nDCG@10 over the first-stage ranking produced by either BM25 and SPLADE-v3, respectively. Such differences in reranking BM25 and SPLADE-v3 signifies **the importance of evaluating with a strong first-stage retriever**, both because it is a more challenging task to distinguish passages that are all likely to be relevant and because reranking a strong retriever like SPLADE-v3 is a more realistic setting for users.」
- 物理第 6 页 5 节还写明：DL 2019/2020 上改进很小，因为这两个基准「have been heavily exposed in hyperparameter tuning」。
- 物理第 7 页表 4（BRIGHT，`nDCG@10`，12 子集宏平均）：`BM25` `14.8`；`BM25 on GPT-4o CoT` `26.5`；`ReasonIR on GPT-4o CoT` `30.6`；重排 top-20 时 `RankZephyr 7B` `21.1`、`Rank-K 单次调用` `30.1`；重排 top-100 时 `RankZephyr 7B` `21.3`、`Rank1-32B` `29.4`、`Rank-K 滑窗` `33.3`。物理第 6 页 5.1 节据此称相对 RankZephyr 提升 `42.7%`（`21.1 → 30.1`）。
- 物理第 7 页表 5 与第 8 页正文：把重排后的列表与初始列表用**倒数排名融合**（RRF）合并可以进一步提升，`Rank-K 滑窗` `31.9` → `+ ReasonIR with RRF` `33.5`；作者强调这不增加额外计算，因为初始排名列表本来就存在。
- **物理第 8 页表 6 与 5.2 节是跨语言零样本迁移**：英文查询检索母语文档（波斯语／俄语／中文），译文与母语两种设定。`Rank-K` 中文译文 `0.447`、母语 `0.449`；俄语 `0.434 / 0.439`；波斯语 `0.440 / 0.441`。作者结论：「Despite only being fine-tuned for the reranking task with English data, Rank-K can effectively rerank non-English passages based on English queries」，两种设定差异可忽略。同表 `RankZephyr` 中文译文 `0.274`、母语 `0.367`，波动远大于 Rank-K。
- 物理第 9 页 5.3 节：Rank-K 只对 `38%` 的查询一次生成最终排名，近三分之二的查询需要先产生多个部分排名再合并；作者承认推理轨迹过长、计算昂贵，把缩短轨迹留作未来工作。

## 与本课题的关系

本节对照的是本仓库本地文献检索工具 `scripts/literature_search`。

- **本批中与本项目设定最接近的一篇**。主代理 2026-08-31 的中立查询实测是英文摘要（ASCII 占比 `98.7%`）检索中文笔记，属于跨语言、字面不重叠的检索；本文物理第 8 页表 6 正是英文查询检索母语中文文档的公开先例（本代理未复现该实测，仅作对照前提）。
- **可迁移的判据一：用最强的一阶段来评价新增组件**。物理第 6 页明确写出这一点。对应到本项目，评价任何新增通道或重排时，参照系应当是当前最好的单通道（主代理实测中的向量 `0.3250`），而不是最弱的词法 `0.2250`；否则会把「补齐弱通道」误读成「方法有效」。
- **可迁移的判据二：不匹配的重排器是负收益**。`RankZephyr` 在 NeuCLIR 上相对一阶段是 `−6%`（表 3 与第 6 页正文）。本项目若引入未针对中文或跨语言训练的重排器，必须先验证它不会低于现有单通道，而不是默认它只会更好。
- **可迁移的判据三：RRF 与初始列表合并是有公开先例的增益来源**（物理第 8 页、表 5）。本项目已经在用 RRF，主代理观察到当前 `rrf_constant=60` near-worst、`k=5` 升到 `0.3700`。本文只证明「融合初始列表可以更好」，**没有**研究 RRF 常数的取值，因此常数选择在本项目属于待验证，必须由本项目自己的扫描实验裁决，不能引用本文为某个常数背书。
- **当前评测集能否检验**：能。主代理的中立评测命中率在 `0.2250`–`0.3700` 区间，远未饱和，具备区分能力。这一条相对本代理上一轮的判断已经改变——上一轮依据的是被污染的旧评测（查询取自被索引字段，词法虚高到饱和），该前提已被主代理推翻。
- **不可迁移**：Rank-K 方法本体。32B 参数、每查询平均输出 `2,408.85` token、近三分之二查询需要多轮部分排名，对一个 510 篇笔记规模的本地检索工具是数量级失配的成本。
- **引用纪律**：本文摘要里的 `23%` 与 `19%` 是相对 **RankZephyr** 的提升，表 3 括号里的 `26%` 与 `12%` 是相对**一阶段检索器**的提升，两组数字口径不同，不得混用。

## 证据记录

- 全文：`raw/` 原件 15 个物理页，2026-08-31 读取第 1–10 页核验。已核验训练配方（第 3–4 页）、表 1（第 4 页）、表 2（第 5 页）、强一阶段论断（第 6 页）、表 3 与表 4（第 7 页）、表 5 与表 6 及跨语言结论（第 8 页）、生成行为统计（第 9 页）。第 11–15 页为相关工作续、参考文献与附录，未逐页核验。
- 首次抓取用 arXiv HTML，本次回原件页码复核，数字一致，无修正。
- arXiv：<https://arxiv.org/abs/2505.14432>；代码 <https://github.com/hltcoe/rank-k>
- Zotero 条目 `EPDCN9PC`。
- 原件 sha256 为 `f4453ea2a1df37083143c734aad42a55b929795681eee605a32da40ebcb4f9d5`。
- 证据强度：完整全文（正文部分）；构成本项目**检索工具选型**的跨语言对照与评价纪律来源，不构成本课题效果证据，不进入论文正文。
