# Notes: 本地文献混合检索精度

## 一、现有架构（读源码所得）

| 组件 | 实现 | 文件 |
| --- | --- | --- |
| 分块 | 按 Markdown 标题切节，再按 `chunk_max_chars=400` / `overlap=80` 开窗；每块前缀 `标题\n小节名\n` | `documents.py:chunk_note` |
| 词法 | SQLite FTS5，`tokenize='trigram'`，`content=''`；查询转成所有去重字符三元组的 OR；打分 `-bm25(chunks_fts,5.0,2.0,1.0)`（title/heading/text 权重） | `lexical.py`, `storage.py:initialize` |
| 向量 | `intfloat/multilingual-e5-small` 固定修订，`passage:`/`query:` 前缀，L2 归一化后点积；**全量线性扫描**，无 ANN | `embeddings.py`, `search.py:_vector_ranking` |
| 分块→笔记 | **取最高分单块**（max 池化），不做多块累加 | `ranking.py:aggregate_chunks` |
| 混合 | **RRF**，`k=60`，对两路**完整排序列表**融合（不截断） | `ranking.py:reciprocal_rank_fusion` |

## 二、实测诊断（`probe_index.py` / `dump_notes.py`）

### 2.1 frontmatter 被整体丢弃（已证实）

`documents.py:parse_frontmatter` 返回 `text[match.end():]`，把整个 frontmatter 从正文剥离；
且其字段正则 `^([A-Za-z_][\w-]*):\s*(.*)$` 要求值非空，YAML 列表（`tags:` 换行后 `  - x`）被丢弃。
只有 `title` 通过分块前缀幸存。

实测（OWAD 笔记 note_id=9）：
- 含标签词 `正常性漂移` 的分块 11 个（因正文本身反复出现）
- 含标签词 `网络入侵检测` 的分块 **0** 个
- 含标签词 `分布适应` 的分块 **0** 个
- 全库含 `key_finding:` / `authors:` / `venue:` / `tags:` 字面量的分块均为 **0**

覆盖率（525 篇）：`tags` 100.0%、`key_finding` 96.6%、`venue` 1.9%。
被排除在索引外的人工标注：tags 12,929 字符 + key_finding 43,499 字符 = **56,428 字符**。

### 2.2 MOC 导航页污染排序（已证实）

15 个 `INDEX.md` 汇总页与论文笔记同库索引，最大 9,597 字符，正文是论文标题清单，
因此几乎匹配所有主题查询的三元组，并靠 BM25 的 title 权重 5.0 与长度优势占据首位。

25 条查询基线实测：
- `INDEX.md` 占据第 1 名：**10 条（40.0%）**
- Top-5 位次中 `INDEX.md` 出现 22 次（**17.6%**）
- Top-10 位次中出现 32 次（12.8%）
- 而 `INDEX.md` 只占语料 15/525 = **2.9%**

即在第 1 名上超额表征约 14 倍，在 Top-5 上约 6 倍。

### 2.3 同义异写分裂（已证实）

"conformal" 在仓库中有两种中文译名并存且按目录分布：
- `wiki/papers/methodology/` 用「**保形**」：Angelopoulos、Farinhas、Tibshirani
- `wiki/papers/pinn/network-calculus-boundary/` 用「**共形**」：Gibbs、Podina、Stankeviciute、Yu

字符三元组词法检索无法跨越这个字面差异（「保形」与「共形」无共享三元组）。
测试集 M01 正是为此设计。

### 2.4 重复笔记的两种形态

- **重定向页**：如 `pinn/2024-Li-MixLoRA.md`（773 字，「本文件只是重定向入口」）
- **占位页**：如 `manifold/StelLA- Subspace Learning...md`（420 字，key_finding「待补充」，通用标签）
- **跳转页**：`rwkv/2024-Wang-NetMamba-网络流量分类.md`（78 字）

### 2.5 分块规模

6,961 块 / 525 篇 = 13.3 块/篇；平均 262.7 字符，最短 11，最长 451；单篇最多 93 块。
e5-small 上限 512 token，当前 400 字符窗口**远未用满**，属于偏碎的分块。

## 三、对照实验结果

测试集：`scripts/literature_search/evaluation_queries_real.json`，25 条，人工核验相关路径。

| 变体 | 笔记 | 分块 | Recall@5 | Recall@10 | MRR | nDCG@10 |
| --- | --- | --- | --- | --- | --- | --- |
| V0 基线 | 525 | 6961 | 0.8575 | 0.9226 | 0.7933 | 0.7958 |
| V1 排除导航页 | 510 | 6688 | 0.8905 | 0.9476 | 0.9800 | 0.9258 |
| V2 索引 frontmatter | 525 | 7583 | 0.9078 | 0.9506 | 0.8400 | 0.8431 |
| **V3 = V1+V2** | 510 | 7295 | **0.9332** | **0.9556** | **1.0000** | **0.9657** |

V3 相对 V0：Recall@5 **+0.0757（+8.8%）**、Recall@10 +0.0330（+3.6%）、
MRR **+0.2067（+26.1%）**、nDCG@10 **+0.1699（+21.4%）**。
V3 的 MRR=1.0000 已逐条核实：25 条查询全部在第 1 名命中相关笔记。

按意图（V0 → V3）：
- known_item（8）：nDCG@10 0.883 → 0.996
- topic_survey（3）：0.877 → 1.000
- citation_check（4）：0.723 → 1.000
- method_neighbor（10）：0.731 → 0.918

### V3 残留失败（全部为多文档召回）

| 查询 | 未召回 | 原因 |
| --- | --- | --- |
| M01 保形预测 | Gibbs-分布漂移下自适应共形推断、Stankeviciute-共形时间序列预测 | 「保形/共形」同义异写 + 笔记极短（358/416 字） |
| M03 Delta 规则 | 2026-Merrill-线性RNN为何更易并行 | 标题与正文用「线性 RNN」而非「Delta 规则」 |
| M04 词元级低秩专家 | 2024-Wang-LoRA-Flow（重定向页） | 重定向页正文信息量低 |
| M10 选择性预测 | 2022-Luxemburk-TLS细粒度服务分类与拒识 | 用「开集识别」而非「选择性预测」 |

四条残留失败全部是**词汇不匹配**，正是向量通道的目标场景。

## 四、向量通道状态

截至本次评测，索引 `vector_count=0`、`vector_dimension=0`。
并行的 litsearch_vector_fix 代理正在运行 `uv sync --project scripts/literature_search --locked`
（PID 24165，17:56 启动），`scripts/literature_search/.venv` 与 `.cache/literature-search/venv`
的 site-packages 均只有 `_virtualenv.pth`，尚未安装 sentence-transformers。
`~/.cache/huggingface/hub/models--intfloat--multilingual-e5-small` 仅 4.0K，模型权重也未下载。

因此本轮 vector / hybrid 基线**无法测量**，报告中标为「未测量」，不得以推演代替。

## 五、待办

- [ ] 向量可用后补测 vector / hybrid 三模式基线
- [ ] 调研嵌入模型替换、重排序、融合策略、分块、查询改写
- [ ] 写报告并提交
