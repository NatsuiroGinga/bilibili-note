# 优化器算法文献调研笔记（2026-10-15，随做随记）

工具清单（简报规定）：Skill `google-scholar`、`citation-verification`、`pdf-converter`（MinerU）、`literature-reviewer`；
MCP `zotero_semantic_search` / `zotero_search_items` / `zotero_get_item_fulltext` / `zotero_add_items_by_doi` / `zotero_add_items_by_arxiv`、
`mcp__990aea2c-…__search_papers`、`mcp__4cfe5157-…__discover_papers`、`mcp__6874b72c-…__search_literature`、`mcp__50ccb3c5-…__semanticSearch`、`mcp__d0a01844-…__search`。

证据等级：`本地全文` / `在线全文已下载` / `仅摘要` / `仅题录`。

---

## §0 本地查重（完成）

- `rg -il --no-ignore "AdaGrad|Adam\b|LazyAdam|sparse gradient|dead ReLU|warmup|He initialization|Kaiming" wiki/` → 命中文件均为**其他论文正文里顺带提到**（如 ET-BERT 用 Adam、TrafficFormer 有 lr warmup、GRPO 系列），**无一篇以优化器/稀疏梯度/初始化为主题**。
- `raw/papers/methodology/` 75 份原件中无优化器类；`fd -i "adam|adagrad|optim|relu|init|sparse"` 仅命中 `Convex-Optimization.pdf`、`Optimal-Stopping`、`Optimal-Transport`（同名单词，非本主题）。
- Zotero `zotero_semantic_search("adaptive optimizer sparse gradient AdaGrad Adam dead ReLU initialization warmup learning rate")` → 15 条相似度全部 ≤ 0.011（最高为 BASE Layers 0.011），实质**零相关**。
- **结论：本族在本库完全空白，12 篇入库均为新增。**

## §1 工具与限流记录

| 工具 | 状态 |
| --- | --- |
| `scholar` CLI（挂 `HTTPS_PROXY=http://127.0.0.1:7890`）| **全程 429 Too Many Requests**（与前序代理一致），未取到任何结果 |
| WebSearch | 可用；返回的是网页摘要，仅用于找线索，未作为论断证据 |
| OpenAlex REST API (`api.openalex.org`) | **可用且无代理**，用于取题录/DOI/OA 链接 |
| arXiv API (`export.arxiv.org/api/query`, https) | 可用；**注意 `arxiv.org/api/...` 会 302，须用 `export.arxiv.org`** |
| MinerU `extract`（pdf-converter）| 可用，12 篇全部成功解析（另有 1 篇失败，见下） |
| Zotero MCP | 可用（语义检索） |
| 简报所列 `mcp__990aea2c-…` 等 5 个检索 MCP | **本会话不可用**（工具列表中不存在），已如实记录并改走 OpenAlex/arXiv/WebSearch |
| `mcp__zotero__zotero_add_items_by_doi` 等写入工具 | 未使用（本任务只入库到 `raw/`+`wiki/`，未要求写 Zotero） |

**MinerU 解析失败 1 篇**：`ids_optimizer_ijacsa25.pdf`（IJACSA 2025「Optimizer Algorithms Analysis for Intrusion Detection System on Deep Neural Network」）两次 `extract` 均报 `parsing failed`，**未取全文**，只列为题录级线索（见报告「无法获取清单」）。

## §2 检索式清单（按问）

全程 PubMed 式短查询 + OpenAlex `search=` 全文检索，arXiv `all:`/`abs:`。列出实际产生有效候选的查询：

**Q1 稀疏梯度优化器**
- `adaptive subgradient methods for online learning and stochastic optimization` → Duchi 2011 ✅
- `Adam: A Method for Stochastic Optimization` → Kingma 2015 ✅
- `sparse gradients optimization adaptive` / `lazy Adam sparse update` → 无对口论文（LazyAdam 无学术原文，属框架实现）
- `Ad click prediction a view from the trenches` → McMahan 2013 ✅
- `Benchmarking Optimizers for MLPs in Tabular Deep Learning` → Gorishniy 2026 ✅（**本次最关键命中**）
- arXiv `all:"sparse Adam"`、`all:"lazy Adam"` → 无对口（仅 3DGS 等无关）

**Q2 初始化 / 死 ReLU / ln2**
- `dying ReLU and initialization theory numerical examples` → Lu 2020 ✅
- `Trainability of ReLU networks and data-dependent initialization` → Shin 2020 ✅
- `Delving Deep into Rectifiers` → He 2015 ✅
- `Understanding the difficulty of training deep feedforward neural networks` → Glorot 2010（**未取全文**，仅题录）
- `data-dependent Initializations of Convolutional Neural Networks` → Krähenbühl 2016（**未取全文**，仅题录）
- `All you need is a good init`（LSUV）、`GradInit`、`Fixup Initialization`、`AutoInit` → 仅题录（相关家族，见报告）
- `binary cross entropy stuck at log 2 constant predictor` / `neural network trapped in trivial constant function initialization` → **零对口论文**（见报告「ln2 现象无专门文献」）
- `spectral bias of neural networks` → Rahaman 2018（仅题录）

**Q3 调度与预热**
- `Accurate Large Minibatch SGD` → Goyal 2017 ✅
- `Why Warmup the Learning Rate Underlying Mechanisms` → Kalra 2024 ✅
- `A Loss Curvature Perspective on Training Instability` → Gilmer 2021（仅题录）
- `On the Adequacy of Untuned Warmup for Adaptive Optimization` → Ma & Yarats 2021 ✅
- `The Break-Even Point on Optimization Trajectories` → Jastrzębski 2020 ✅
- `The large learning rate phase of deep learning the catapult mechanism` → Lewkowycz 2020 ✅
- `Saddle-to-Saddle Dynamics in Deep Linear/Diagonal Networks`（Jacot 2021、Pesme 2023）→ 仅题录

**Q4 恶意软件/入侵检测应用**
- `malware detection adaptive optimizer deep neural network comparison Adam` → 无「稀疏二值 + 自适应优化器」对口论文
- `intrusion detection Adam SGD optimizer comparison neural network` → IJACSA 2025（**解析失败**，题录级）
- `encrypted traffic classification optimizer Adam` → 仅题录（ET-BERT 等库内已有，非本主题）
- `malware detection binary features gradient boosting comparison` → 仅题录

## §3 证据等级与候选表

见 `报告.md` §候选与证据等级表（同一份数据，避免重复维护）。

## §4 入库清单（12 篇，全部 `raw/papers/methodology/` + `wiki/papers/methodology/`）

| # | 笔记 | 原件 | 等级 |
| - | --- | --- | --- |
| 1 | `2026-Gorishniy-表格深度学习MLP优化器基准` | 2026-Gorishniy-…pdf | 在线全文已下载→本地全文 |
| 2 | `2020-Lu-死ReLU与初始化` | 2020-Lu-…pdf | 同上 |
| 3 | `2020-Shin-ReLU可训练性与数据依赖初始化` | 2020-Shin-…pdf | 同上 |
| 4 | `2011-Duchi-自适应次梯度AdaGrad` | 2011-Duchi-…pdf | 同上 |
| 5 | `2015-Kingma-Adam` | 2015-Kingma-…pdf | 同上 |
| 6 | `2013-McMahan-广告点击预估FTRL逐坐标学习率` | 2013-McMahan-…pdf | 同上 |
| 7 | `2024-Kalra-为什么要预热学习率` | 2024-Kalra-…pdf | 同上 |
| 8 | `2020-Jastrzebski-优化轨迹盈亏平衡点` | 2020-Jastrzebski-…pdf | 同上 |
| 9 | `2015-He-深入研究整流器He初始化` | 2015-He-…pdf | 同上 |
| 10 | `2017-Goyal-大minibatchSGD预热` | 2017-Goyal-…pdf | 同上 |
| 11 | `2020-Lewkowycz-大学习率相与弹射机制` | 2020-Lewkowycz-…pdf | 同上 |
| 12 | `2021-Ma-自适应优化免调预热充分性` | 2021-Ma-…pdf | 同上 |

`wiki/papers/methodology/INDEX.md` 已新增「优化器、稀疏梯度与训练动力学（2026-10-15 新增）」一节登记全部 12 篇。

## §5 协议事实核对

- `official-src/domain_il_experiment.py:194` 硬编码 `torch.optim.SGD(lr=0.01, momentum=0.9, weight_decay=1e-6)`；`:21` `--epochs` 默认 10；`:22` `batch_size` 默认 1024。**换优化器/加预热＝改训练脚本，不改数据合同与 200 条存储预算、不改每年度 10 轮**。
- 库内 `wiki/papers/malware/LAMDA-2026-原论文与时间漂移相关工作综述.md` 第 238 行明确记载：**「原论文 MLP 只有四层，未报告梯度谱、残差坍缩、深层信号传播或优化不稳定」**——即 LAMDA 原论文**未报告也未解释**本课题观测到的首年不收敛，本现象属本课题自身实测。
