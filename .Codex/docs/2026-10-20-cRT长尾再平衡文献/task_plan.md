# cRT / 延迟重加权 / 先验校正文献入库计划

> 任务日期：2026-10-20
> 目标：为 PAAT M2'（分类器再平衡／延迟重加权）补齐直接方法文献，回答 cRT 精确协议、DRW 精确调度、Balanced Softmax / Logit Adjustment 的 label shift 前提边界，以及是否存在「漂移 + 长尾」联合证据。
> 约束：不 commit；PDF 只用 MinerU `extract`；题录只取 arXiv/Crossref/Zotero 返回值；原件入 `raw/papers/methodology/`，笔记入 `wiki/papers/methodology/`。

## 第一优先（任务下达时给定的条目）

| 短名 | 任务给定标识 | 核验结果 | 实际标识 | PDF 落点 | wiki 笔记 | 状态 |
|---|---|---|---|---|---|---|
| BalancedSoftmax | arXiv:2007.10742 | **给定 ID 错误**（该 ID 是 Willmore 能量数学论文） | arXiv:2007.10740（NeurIPS 2020） | `raw/papers/methodology/2020-Ren-Balanced-Meta-Softmax.pdf` | `wiki/papers/methodology/2020-Ren-平衡元Softmax.md` | 进行中 |
| LogitAdjust | arXiv:2007.07314 | 正确（ICLR 2021） | arXiv:2007.07314 | `raw/papers/methodology/2021-Menon-Logit-Adjustment.pdf` | `wiki/papers/methodology/2021-Menon-对数几率调整.md` | 进行中 |
| LADE | arXiv:2103.17084 | **给定 ID 错误**（该 ID 是 DA-DETR 目标检测论文） | arXiv:2012.00321（CVPR 2021） | `raw/papers/methodology/2021-Hong-LADE-Label-Distribution-Disentangling.pdf` | `wiki/papers/methodology/2021-Hong-LADE标签分布解耦.md` | 进行中 |

## 第二优先（检索确认后再入库）

1. 长尾持续/在线学习（class-incremental with long-tailed distributions）的直接方法论文；
2. 概念漂移下的分类器再平衡/先验校正（drift + label shift）；
3. 把 cRT/DRW 用于时间漂移而非静态长尾的工作。

检索入口：arXiv API 题名/摘要检索（主）、Semantic Scholar / OpenAlex（补充）、Google Scholar CLI（≤3 条/主题）。任何进入库的条目必须有本地全文；仅摘要者只登记候选，不写入知识层结论。

## 必须回答的问题

1. cRT 精确协议：冻结哪些层、epoch、采样/损失、报告增益、与 NCM 的区别。
2. Balanced Softmax / Logit Adjustment 是否假设 label shift；`p(x|y)` 也漂移时前提是否成立。
3. DRW 精确调度：哪些 epoch 自然采样、哪些再平衡；160/200 阈值如何任务化到 10 epoch 年度协议。
4. 是否存在「漂移 + 长尾」联合证据；没有则写「未检得」。

## 执行步骤

1. arXiv API 核验题录（已完成，修正两个错误 ID）。
2. 下载 PDF 到 `raw/papers/methodology/`，不覆盖已有文件。
3. `mineru-open-api extract` 转 Markdown 到 `/tmp/2026-10-20-cRT长尾再平衡文献/md/`；读全文与页码锚点。
4. 写 wiki 笔记：八字段 frontmatter + 核心机制 + 与 PAAT M2' 关系 + 不可迁移边界 + 公式/页码锚点。
5. 更新 `wiki/papers/methodology/INDEX.md`。
6. Zotero 查重后按 arXiv 入库。
7. 第二优先检索；有合格全文则入库，否则在 notes 记录「未检得/候选不足」及查询式。
8. 在 `notes.md` 逐篇追加检查点；任务结束输出报告。不 commit。

## 验收

- 每篇 PDF 页数与 arXiv 一致，`source_pdf` 指向实际原件。
- 笔记中的协议数字（epoch、采样、冻结层、增益）能回指 PDF 物理页码。
- INDEX 每篇一行可点击链接 + 一句话说明。
- 报告明确区分「本地全文核验」与「仅题录/摘要」。
