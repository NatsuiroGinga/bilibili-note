# 第四章架构机制文献调研：检查点笔记

**日期**：2026-10-20
**任务计划**：同目录 `task_plan.md`
**状态**：进行中

## 0. 工具链状态（开始时记录）

- **本地混合索引**：`scripts/literature_search status --json` 返回 `exists: false`；尝试查询触发自动构建，构建在 `_write_vectors` 处抛 `TypeError: EmbeddingBackend.__init__() got an unexpected keyword argument 'device'`（`scripts/literature_search/build.py:89`），构建失败。**判定：混合索引不可用（工具缺陷），降级本地 `rg -il` 全文检索 `wiki/papers/`，并向主代理披露混合索引未使用。**
- **Zotero MCP**：可用（`zotero_semantic_search` / `zotero_search_items`）。
- **scholar CLI**：主代理实测 `curl https://scholar.google.com` 返回 000、无代理变量，`scholar` 连接失败。**判定：外部 Scholar 检索阻塞**，按 task_plan §五停止条件处理，不重试。
- **WebSearch**：可用（API 通道），作备用。

## 1. 检索纪律

- 每条引用的题名/作者/年份/venue 必须来自工具返回（Zotero 条目 / WebSearch 摘要 / 本地文件题录），在本文登记来源。
- 证据等级：本地全文 > 在线摘要/仅题录。
- 本任务只做候选发现，不裁决机制存废。

## 2. 本地语料盘点（rg 全文检索 `wiki/papers/`，807 个 md）

`rg -il` 关键词命中确认：本地已有下列家族的全文级笔记（证据等级：本地全文）：

- **A 表格 Transformer**：`2020-Huang-TabTransformer上下文嵌入.md`、`2021-Gorishniy-表格数据深度学习模型再审视.md`（FT-Transformer 出处）、`2023-Zhu-XTab跨表预训练.md`、`2026-Li-FT-Transformer物联网攻击检测.md`（域内应用）、`ft-mechanisms/` 4 篇序列表格 Transformer（TabFormer/FATA-Trans/Fieldy/STEP）。
- **B 表格专用正则/集成**：`2025-Gorishniy-TabM参数高效集成.md`、`2021-Gorishniy-再审视`（ResNet-tabular 出处）、`2026-Gorishniy-表格深度学习MLP优化器基准.md`、`2022-ShwartzZiv-表格数据深度学习并非必需.md`。
- **C 检索/近邻混合**：`tree-inspired/2024-Gorishniy-TabR检索增强表格网络.md`。
- **F 可微树**：`tree-inspired/`：NODE（2020）、GRANDE（2024）、DeepGBM（2019）、LMA（2020，无关保留）。
- **G 恶意软件域**：`2016-Bartos-优化不变表示检测未见恶意软件变种.md`（USENIX Sec'16，本地全文）；DREBIN/MalBERT 仅在他文笔记被提及，无专篇笔记。
- **H 理论/实证**：`2022-Grinsztajn-树模型为何优于表格深度学习.md`、`2022-ShwartzZiv`；TabReD 无专篇笔记。
- **D 特征嵌入/交互**、**E 序列模型强加于特征集**：本地零命中（DeepFM/DCN/AutoInt/PNN 无笔记；"tabular-as-sequence" 无专篇），需外部检索。

各笔记 frontmatter 均含 title/authors/year/journal/source_pdf/sha256，部分含 `zotero_item_key`/`bibtex_key`（Gorishniy 2021 `N4MRAEZF`、TabM `Y4ICR5KF`、TabR `9C95X4NU`、NODE `D4KH9JT8`、GRANDE `4L4MLPEB`、DeepGBM `UTS5MJAS`）。

## 3. 家族检查点

### 家族 A：表格 Transformer（本地部分，2026-10-20）

| 锚点 | 题录来源 | 证据等级 | 与候选关系 |
|---|---|---|---|
| TabTransformer | 本地笔记 frontmatter（Huang et al., 2020, arXiv:2012.06678, sha256 cac9f73e…） | 本地全文 | 仅类别特征过 Transformer、数值直拼——提示对 4561 维全二值特征可整体 token 化，无数值/类别分叉问题 |
| FT-Transformer | 本地笔记（Gorishniy et al., NeurIPS 2021, arXiv:2106.11959, zotero N4MRAEZF） | 本地全文 | 逐字段 token＋注意力交互＝特征交互建模对照上限；训练协议 AdamW/lr=1e-4/wd=1e-5 已核查（thesis/methods/FT-Transformer训练协议核查.md） |
| XTab | 本地笔记（Zhu et al., ICML 2023, arXiv:2305.06090） | 本地全文 | 跨表共享骨干＋数据集专属轻量适配——跨年复用骨干的先例 |
| FT-Transformer IoT 攻击检测 | 本地笔记（Li, Tao & Qu, Electronics 2026, sha256 57b36678…） | 本地全文 | 域内先例：流级统计特征＋FT-Transformer 二分类，跨数据集泛化协议；仅摘要级关联本章病灶 |
| SAINT | **未检得本地专篇**，待外部（Zotero/WebSearch） | — | — |

### 家族 B：表格专用正则/集成（本地部分，2026-10-20）

| 锚点 | 题录来源 | 证据等级 | 与候选关系 |
|---|---|---|---|
| TabM | 本地笔记（Gorishniy et al., ICLR 2025, arXiv:2410.24210, zotero Y4ICR5KF） | 本地全文 | 共享主权重＋成员专属低开销适配的多 MLP 集成；对"2.69M 参数小 MLP 基座"是低成本强化来源 |
| ResNet-tabular | 本地笔记（Gorishniy et al., NeurIPS 2021，同 FT-Transformer 出处） | 本地全文 | 两线性层残差 MLP 是 MLP 基座的最近结构近邻 |
| MLP 优化器基准 | 本地笔记（Gorishniy et al., arXiv:2604.15297, 2026） | 本地全文 | 15 优化器 × 17 数据集：SGD+动量多数数据集劣于 AdamW——与本课题基座优化器选择直接相关 |
| MixUp 类表格正则 | 待外部 | — | — |

### 家族 C：检索/近邻混合（本地部分，2026-10-20）

| 锚点 | 题录来源 | 证据等级 | 与候选关系 |
|---|---|---|---|
| TabR | 本地笔记（Gorishniy et al., ICLR 2024, arXiv:2307.14338, zotero 9C95X4NU） | 本地全文 | 可学习键空间近邻＋源训练标签局部修正；末期年度正例稀缺（1.6%/0.05%）的机制来源；笔记已记录预算约束（300 万样本 >18h） |
| 第二锚点 | 待外部（kNN+DL 混合或检索增强表格另一篇） | — | — |

### 家族 F：可微树/混合（本地，2026-10-20）

| 锚点 | 题录来源 | 证据等级 | 与候选关系 |
|---|---|---|---|
| NODE | 本地笔记（Popov, Morozov & Babenko, ICLR 2020, arXiv:1909.06312, zotero D4KH9JT8） | 本地全文 | 可微遗忘树＋entmax；HIGGS 1050 万样本；显存低效自述、跨基准稳健性弱于 XGBoost（Shwartz-Ziv 实测劣化 14.21%） |
| GRANDE | 本地笔记（Marton et al., ICLR 2024, arXiv:2309.17130, zotero 4L4MLPEB） | 本地全文 | 直通估计硬轴对齐分裂，归纳偏置最接近 XGBoost；最大数据集仅 96,320 样本 |
| DeepGBM | 本地笔记（Ke et al., KDD 2019, doi:10.1145/3292500.3330858, zotero UTS5MJAS） | 本地全文 | GBDT 蒸馏可在线更新网络；Criteo 4580 万样本；许可证不明排除 |
| TabNet | 待外部（Arik & Pfister 2021 无本地专篇） | — | — |

### 家族 H：理论/实证基线（本地，2026-10-20）

| 锚点 | 题录来源 | 证据等级 | 与候选关系 |
|---|---|---|---|
| Grinsztajn 2022 | 本地笔记（arXiv:2207.08815） | 本地全文 | 45 数据集 × 400 随机搜索/学习器 × 20,000 小时：树模型对所有预算优于 MLP/ResNet/FT-Transformer/SAINT——「该格式利好谁」的直接证据；**注意其未覆盖超高维稀疏二值与年度分布漂移** |
| Shwartz-Ziv & Armon 2022 | 本地笔记（arXiv:2106.03253） | 本地全文 | 四个深度表格模型跨数据集退化，XGBoost 在 11 数据集中 8 个最优（p<0.005）——NODE 14.21%/TabNet 10.51% 劣化 |
| TabReD | 待外部 | — | — |

### 家族 G：恶意软件域骨干（本地部分，2026-10-20）

| 锚点 | 题录来源 | 证据等级 | 与候选关系 |
|---|---|---|---|
| Bartoš et al. 2016 | 本地笔记（USENIX Security 2016, 印刷页 807–822） | 本地全文 | 特征值直方图＋自相似矩阵直方图表示，未见 32 家族泛化 90%P/67%R——域内「表示不变性优先于骨干」先例 |
| DREBIN / MalBERT / 深度恶意软件骨干 | 待外部（仅在他文笔记被引用） | — | — |

### 家族 D：特征嵌入/交互（推荐系统系，外部题录，2026-10-20）

检索通道：arXiv 导出 API（`export.arxiv.org/api/query`）＋ Crossref API；Zotero 语义检索未命中 DeepFM/DCN/AutoInt/PNN。证据等级：**仅题录**（未取全文，不得支撑正文论断）。

| 锚点 | 题录来源 | 证据等级 | 与候选关系 |
|---|---|---|---|
| FM 原始出处 | Crossref：Rendle, *Factorization Machines*, 2010 IEEE ICDM, DOI 10.1109/icdm.2010.127 | 仅题录 | 二值特征共现的二阶交互建模正源 |
| DeepFM | arXiv API：Guo, Tang, Ye, Li, He，arXiv:1703.04247（2017-03-13） | 仅题录 | FM＋MLP 共享嵌入；正式 venue 未在工具返回中，标 arXiv |
| DCN | arXiv API：Wang, Fu, Fu, Wang，arXiv:1708.05123，AdKDD 2017（comment 字段） | 仅题录 | 显式多项式交叉层 |
| AutoInt | arXiv API：Song, Shi, Xiao, Duan, Xu, Zhang, Tang，arXiv:1810.11921，CIKM 2019（comment 字段） | 仅题录 | 自注意力特征交互＋残差 |
| PNN | arXiv API：Qu, Cai, Ren, Zhang, Yu, Wen, Wang，arXiv:1611.00144，ICDM 2016（comment 字段） | 仅题录 | 内积/外积乘积层 |
| Android FM | arXiv API：Li, Mills, Zhu, Niu, Zhang，arXiv:1805.11843（2018-05-30） | 仅题录 | **域内桥接**：摘要明言「app 的数值特征表示是长而高度稀疏的向量，特征交互对揭示恶意行为模式至关重要」，DREBIN 数据集 100.00% 精确率——直接挂本课题稀疏病灶 |
| 数值嵌入 | Zotero：Gorishniy, Rubachev, Babenko，*On Embeddings for Numerical Features in Tabular Deep Learning*，2022-03-10，zotero `5P6Q2HX2` | Zotero 条目（摘要） | 逐特征嵌入的证据基础；本课题全二值，嵌入≈可学习查找表 |

### 家族 E：序列模型强加于特征集（2026-10-20）

| 锚点 | 题录来源 | 证据等级 | 与候选关系 |
|---|---|---|---|
| Mamba | arXiv API：Gu & Dao，*Mamba: Linear-Time Sequence Modeling with Selective State Spaces*，arXiv:2312.00752（2023-12-01） | 仅题录 | SSM 机制出处 |
| RWKV-5/6 | Zotero：Peng et al.，*Eagle and Finch: RWKV with Matrix-Valued States and Dynamic Recurrence*，2024-04-08，zotero `4B5F4H65`（`WKUSNUYR` 为重复条目） | Zotero 条目（摘要） | 本地另有 RWKV/INDEX 全套全文笔记（RWKV 原论文、RWKV-7、时序线 8 篇） |
| TP-BERTa | arXiv API：Yan, Zheng, Xu, Zhu, Chen, Sun, Wu, Chen，*Making Pre-trained Language Models Great on Tabular Prediction*，ICLR 2024 spotlight（comment 字段，openreview anzIzGZuLi） | 仅题录 | **字段 token 化＋语言模型预训练**的「tabular-as-sequence」正锚点 |
| TransTab | arXiv API：Wang & Sun，*TransTab: Learning Transferable Tabular Transformers Across Tables*，NeurIPS 2022（comment 字段） | 仅题录 | 列语义 token 化、跨表迁移 |
| TabLLM | arXiv API：Hegselmann, Buendia, Lang, Agrawal, Jiang, Sontag，*TabLLM: Few-shot Classification of Tabular Data with Large Language Models*（2022-10-19） | 仅题录 | 少样本序列化先例，挂末期正例稀缺 |
| NetMamba（域内） | 本地笔记：Wang, Xie, Wang, Wang, Zhao, Cui，arXiv:2405.11449 | 本地全文 | Mamba 进流量分类的直接相邻证据，但输入是真序列（字节/包），非特征集 |

**「未检得」记录（重要）**：arXiv API 检索 `ti:"TabLLM" OR ti:"Tabular data as sequence"` 及既有本地语料均**未检得**「把静态特征集当序列喂 SSM/Mamba/RWKV 做分类」的文献线；现有 tabular-as-sequence 线全部以 Transformer/LLM 承载，Mamba/SSM 线的输入均为真序列（时序、字节流、图）。该空白是文献事实，不构成本课题机制的可行性证据。

### 家族 G：恶意软件域骨干（2026-10-20）

| 锚点 | 题录来源 | 证据等级 | 与候选关系 |
|---|---|---|---|
| DREBIN | Crossref：Arp, Spreitzenbarth, Hübner, Gascon, Rieck，*Drebin: Effective and Explainable Detection of Android Malware in Your Pocket*，NDSS 2014，DOI 10.14722/ndss.2014.23247 | 仅题录（Crossref） | 本课题 4561 维静态特征格式的原始出处 |
| MalBERT | WebSearch（IEEE Xplore/arXiv 摘要）：Romano, Zhang, Barsallo Y., Sloan, Ram，*MalBERT: Static Android Malware Detection Using Transformer Models*，IEEE SW 2020，DOI 10.1109/SW51321.2020.00016，arXiv:2007.06140 | 在线摘要 | BERT 式 token 化静态特征骨干的域内先例 |
| TESSERACT | Zotero：Pendlebury, Pierazzi, Jordaney, Kinder, Cavallaro，*TESSERACT: Eliminating Experimental Bias in Malware Classification across Space and Time*，2018-07-20，zotero `F6KINRCT` | Zotero 条目（摘要） | 空时偏置评价纪律；本课题年度协议的域内对照 |
| LAMDA | 本地笔记：Haque et al.，*LAMDA: A Longitudinal Android Malware Benchmark for Concept Drift Analysis*，ICLR 2026，arXiv:2505.18551 | 本地全文 | 本课题数据集原文：静态 Drebin 式特征，LightGBM F1 IID 97.49%→FAR 47.24%（表 7） |
| Bartoš 2016 | 本地笔记：USENIX Security 2016，印刷页 807–822 | 本地全文 | 表示不变性优先于骨干的域内先例 |
| McNdroid / DRMD | 本地笔记：Kamol et al.，arXiv:2605.06894（2026）；McFadden et al.，AAAI 2026，arXiv:2508.18839 | 本地全文 | 域内最新漂移基线（占位登记，不排序） |

首次尝试 DREBIN 时 WebSearch 返回模型记忆（工具自述无实时检索），该输出**未用作题录**；改 Crossref API 取得上述字段。dblp 被反爬页拦截（HTTP 200 但返回 "Oh noes!" Anubis 页），Semantic Scholar API 429 限流——均记录在案。

### 家族 H：补充外部锚点（2026-10-20）

| 锚点 | 题录来源 | 证据等级 | 与候选关系 |
|---|---|---|---|
| TabReD | Zotero：Rubachev, Kartashev, Gorishniy, Babenko，*TabReD: Analyzing Pitfalls and Filling the Gaps in Tabular Deep Learning Benchmarks*，2024-06-27，zotero `NSDDSPKC` | Zotero 条目（摘要） | 工业表格基准的「时间漂移＋数据集规模」陷阱分析 |
| Cai & Ye 2025 | Zotero：*Understanding the Limits of Deep Tabular Methods with Temporal Shift*，2025-02-27，zotero `WABQ5RAJ` | Zotero 条目（摘要） | **最对题**：时序分布漂移下深度表格方法极限的直接实证 |

### 全局「未检得」记录（2026-10-20 收口）

1. **SAINT** 本地无专篇笔记；外部题录已取得（arXiv API），但 WebSearch 同步提示其基准可比性存在社区争议（GitHub issue），**引用时须带此标注**。
2. **MixUp 类表格专用正则**：arXiv API 检索 `all:"mixup" AND all:"tabular data"` 未返回表格分类专篇（命中 MixupE 2022、G-Mixup 2022 两篇邻接文献）；本地语料亦无。家族 B 以 TabM/ResNet-tabular/优化器基准/Shwartz-Ziv 四锚点收口。
3. **tabular 特征当序列喂 SSM/Mamba/RWKV**：未检得（见家族 E）。
4. **scholar CLI**：主代理实测网络不可达（curl 000），本轮全部外部检索改 arXiv 导出 API＋Crossref API＋WebSearch＋Zotero MCP；dblp 反爬拦截、Semantic Scholar API 429 均记录在案。
5. **kNN+DL 表格混合第二专篇**（家族 C）：scholar 阻塞后未执行 kNN 专查，记为缺口。

### 最终状态（2026-10-20）

- 报告已落盘：`thesis/methods/第四章-架构机制文献调研.md`（142 行，§0–§11：病灶、检索声明、家族 A–H 锚点表、5 项材料性探针清单、未检得总表）。40 个题录关键串（Zotero key、arXiv ID、DOI）经 `rg -F` 逐一校验在场。
- **过程披露**：本会话输出在长内容写入时出现多次字符级损坏（错字、表行碎片），已按「短块追加＋rg 全量校验＋定点修复」流程清理；40 项关键串校验通过，无残留占位符。建议主代理验收时对报告题录做一次抽查（对照 notes.md 各家族表）。
