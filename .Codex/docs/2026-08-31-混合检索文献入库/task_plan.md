# 混合检索／RAG 六篇文献入库任务计划

> 日期：2026-08-31
> 任务来源：主代理指派，为本仓库本地文献检索工具 `scripts/literature_search` 的通道对照实测寻找外部对照文献。
> 状态：**已完成**（原件已落盘、页码核验已做、五篇笔记与索引已写入）

## 任务边界

- 只做外部文献的检索、全文阅读、相关性裁决与入库。
- 不修改 `scripts/literature_search` 下任何代码或配置。
- 不重建索引、不运行检索评测。
- 本任务的结论只针对**检索工具选型**，不进入论文正文，也不改变加密恶意流量检测的研究边界。

## 完成情况

**原件（主代理下载，5 篇，第 6 篇按裁决排除）**，落点 `raw/papers/methodology/retrieval-rag/`：

| arXiv | 文件名 | 页数 | sha256 前 16 位 | Zotero key |
| --- | --- | ---: | --- | --- |
| `2201.00365` | `2022-Hofstatter-Establishing-Strong-Baselines-TripClick-ECIR-arXiv2201.00365.pdf` | 9 | `c7ec2f48feca939f` | `444M5V6T` |
| `2502.20245` | `2025-Abdallah-From-Retrieval-to-Generation-Comparing-Approaches-arXiv2502.20245.pdf` | 17 | `3ae7d8530e1d046b` | `2T8HMMWX` |
| `2507.12425` | `2025-Cheerla-Advancing-RAG-Structured-Enterprise-Data-arXiv2507.12425.pdf` | 11 | `f69bb3aef06e2bb9` | `7VSGIWHH` |
| `2510.16393` | `2025-Nardini-Blending-LTR-Dense-Representations-Cascades-arXiv2510.16393.pdf` | 5 | `e1f7684f95243552` | `IEMPD9VB` |
| `2505.14432` | `2025-Yang-Rank-K-Test-Time-Reasoning-Listwise-Reranking-arXiv2505.14432.pdf` | 15 | `f4453ea2a1df3708` | `EPDCN9PC` |

**笔记（5 篇）**，落点 `wiki/papers/methodology/retrieval-rag/`：
`2025-Nardini-学习排序与稠密表示混合级联.md`、`2025-Yang-Rank-K测试时推理列表重排.md`、
`2022-Hofstatter-TripClick健康检索强基线.md`、`2025-Abdallah-从检索到生成的方法比较.md`、
`2025-Cheerla-企业结构化数据高级RAG.md`。

**索引**：`wiki/papers/methodology/INDEX.md` 新增「混合检索、重排与级联（2026-08-31 新增）」一节，五条链接均带别名与一句话说明，并注明该簇不进入论文正文。

## 证据等级更新（本节取代 notes.md 的全局告警）

`notes.md` 写于原件落盘之前，其开头声明「所有数字来自 arXiv HTML 二次提取、待回原件复核」。
**该告警现已失效**：2026-08-31 已用 `Read` 工具按物理页读取全部五篇 PDF 并逐表核验，
核验结果写入上述五篇 wiki 笔记，笔记中的每个数字都带物理页码与表号。
以 wiki 笔记为准；`notes.md` 保留为过程记录，不再作为引用来源。

HTML 阶段的两个未关闭疑点均已关闭：

1. `2510.16393` 的 `+11%`：物理第 4 页 A1 节原文给出，口径为 `STAR` 1,000 probes 在 Dev 上
   `0.3684 → 0.4089`，相对**稠密一阶段**而非词法基线。此前为本代理自行折算，现为作者原文。
2. `2201.00365` 的 `45–50%`：物理第 5 页原文给出，口径为 **HEAD 验证集**、同一 `PubMedBERT_CAT`
   模型与配置、仅替换训练数据（`MRR@10` `.41 → .6`，`nDCG@10` `.21 → .30`），该组数字不在表 1 中。

回原件另新增两处 HTML 阶段未察觉的发现，已写入对应笔记：

- `2507.12425` 对分块大小给出三个互相矛盾的数值（物理第 4 页 `2000` 字符、第 7 页 `700` 字符、
  第 2 页 `700` token）。
- `2502.20245` 有三处内部数字不一致（附录 A.1 与表 1 的 TriviaQA Top-1；第 7 节把 BM25 的 BEIR
  均值当作 Robust04 对照；第 6 节把 GPT-2 XL 的仅生成困惑度写成 retrieval-only）。

## 遗留事项（需要 shell，本代理无法执行）

1. **五篇笔记的 `sha256` 字段为 `待补全`**，仅填了主代理提供的前 16 位到 `sha256_prefix16`。
   需执行 `shasum -a 256 raw/papers/methodology/retrieval-rag/*.pdf` 后回填完整值。
2. **本代理无法运行 `git status` 与 `git commit`**（无 Bash 工具）。提交前请自行做快照检查，
   并用 pathspec 形式提交，禁止 `git add .`：
   ```
   git status --short -- raw/papers/methodology/retrieval-rag wiki/papers/methodology/retrieval-rag wiki/papers/methodology/INDEX.md
   git commit -- raw/papers/methodology/retrieval-rag wiki/papers/methodology/retrieval-rag wiki/papers/methodology/INDEX.md
   ```
   建议提交信息：`docs(kb): add hybrid retrieval and reranking reference papers`
3. `wiki/papers/methodology/INDEX.md` 由本代理整文件重写（无 Edit 工具），
   改动仅为在 `## 相关索引` 之前插入一节。提交前建议 `git diff` 确认没有误改既有条目。

## 决策记录

- **入库 5 篇，排除 1 篇**。排除的是 `2603.24012`（伊斯兰继承法 QIAS 2026 系统论文），
  排除理由见 `notes.md` 第 6 条：检索侧无任何标准 IR 指标、无组件消融、领域完全错配。
- 目录选 `methodology/retrieval-rag/`，沿用 `methodology/soc-alert-operations/`（2026-08-18 新增）
  的既有做法：成体系的新主题簇单独建子目录并在 `INDEX.md` 增加带日期的小节。
  未并入 `methodology/ranking/`，因为该目录现有内容是 AP／GeM 一类的排序目标函数与评价，
  与本批的文本检索系统与级联工程不是同一问题。
- **前提修正**：本代理第一轮曾据旧评测（词法 `MRR 1.0000`、三法饱和）判断
  「这批论文方向上支持 hybrid 零提升」。主代理其后用中立查询重跑，发现旧评测的查询取自
  被索引字段因而系统性偏袒词法，该前提已被推翻。五篇笔记均按修正后的事实撰写，
  并在 `2502.20245` 的笔记中显式撤回了一条基于旧前提的弱旁证。

## 规则冲突声明

`raw/AGENTS.md` 规定「凡是检索到并在汇报中提及的论文，一律下载全文入库」，
而本次任务书授权对第六篇「判为不相关就跳过」。二者冲突。
处理方式：第六篇不下载，但其完整书目、摘要、消融事实与排除理由已记入本目录 `notes.md`，
后续会话可检索到、可复查、可一条命令补下。
如需严格执行根规则，补下命令为
`curl -L -o raw/papers/methodology/retrieval-rag/2026-Swaileh-CVPD-QIAS-RAG-Islamic-Inheritance-arXiv2603.24012.pdf https://arxiv.org/pdf/2603.24012v2`。
