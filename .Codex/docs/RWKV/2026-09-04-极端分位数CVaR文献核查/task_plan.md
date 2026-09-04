# 极端分位数 CVaR 阈值估计 文献核查 · 任务计划

<!-- RESEARCH_ROUTE=RWKV -->

- 日期：2026-09-04
- 任务性质：纯文献核查，**不跑任何实验**（本机与服务器均不占用）
- 唯一问题：**当 CVaR 的预算水平细到小批量在统计上分辨不出来时，文献里怎么估这个阈值？**
- 交付：`thesis/methods/第三章-极端分位数CVaR估计文献核查.md`

## 冻结前提（不重新推导）

- `N_pop = 121336`，`n_neg = 64`，`n_pos = 2`
- `K = [121, 606, 1213, 2426, 4853, 9706]`
- `K_eff = K·n_neg/N_pop = [0.0638, 0.3196, 0.6398, 1.2796, 2.5598, 5.1195]`
- `β = K/N_pop = [0.000997, 0.004994, 0.009997, 0.019994, 0.039996, 0.079993]`
- 当前 `ξ` 更新：子梯度 SGD，`lr = 1e-4`，`∂L/∂ξ ∝ (1 − n_active/K_eff)`
- 实测不对称度：空活动集降 `8.33e-6`；一个活动对上跳 `1.22e-4`（`14.7×`）；全活动 `1002×`
- 已否决且不得重提：（一）跨步水库分位数估计器；（二）`n_neg → 256`
- 既有根因判定：问题在批内采样规模，不在估计方法
  （`.Codex/docs/RWKV/2026-09-01-BER水库分位数修法裁决.md`，已读）

## 四问

1. 已发表的「批量下界 vs 目标分位数水平」可行性关系式？`β = 0.001` 需多大批量？
2. `β` 细于批量分辨率时别人怎么做？（RM 分位数追踪／重要性抽样／EVT-POT／
   多层嵌套 CVaR／pAUC 系列对 `β` 与批量的处理）
3. 有无报告阈值追踪 bang-bang／振荡现象及其处置？
4. 有无「直接放弃不可表示档位」的先例？

## 工具实况（如实记录，2026-09-04 本代理会话）

- **无 `Bash` 工具**：无法运行 `uv run --project scripts/literature_search ...` 本地混合索引 CLI，
  也无法 `git commit`。替代：用 `Glob`/`Grep` 直接检索 `wiki/papers/**`（同一批语料，
  只是走内置检索而非混合索引；**向量通道未运行**，须在结论中披露）。
- **无 `Skill` 工具**：`planning-with-files`／`literature-reviewer`／`citation-verification`／
  `pdf-converter` 无法作为技能调用。替代：按其工作流手工执行（本文件 + `notes.md` 即
  `planning-with-files` 的产物形态）；PDF 用 `Read` 的原生 PDF 通道读取（**不是** `pdftotext`，
  未违反禁令，但也**不是** MinerU，公式保真度低于 MinerU，须在引用公式时标注）。
- **无 `ToolSearch`**：任务简报列出的五个 MCP 检索工具（`990aea2c`／`4cfe5157`／`6874b72c`）
  不在本代理可用工具表内。Zotero 仅有 `zotero_search_items`／`zotero_get_item_fulltext`／
  `zotero_get_item_metadata` 等，**没有 `zotero_semantic_search`**。
- 可用：`Read`（含 PDF）、`Write`、`Grep`、`Glob`、`WebSearch`、`WebFetch`、Zotero 基础工具。

## 检索顺序（按可用工具调整后）

1. 本地 `wiki/papers/**` 与 `raw/papers/**`（Grep/Glob 代替混合索引 CLI）
2. Zotero `zotero_search_items`
3. 在线 `WebSearch` + `WebFetch`（arXiv/OpenReview/PMLR 全文优先）

## 执行阶段

- [x] P0 读裁决文件、建计划与笔记
- [x] P1 本地已有全文盘点（SOPA/LibAUC/SPOT/DRO/SoRR/HNS-OPAUC/MIL-TPAUC）
- [x] P2 逐篇提取 `β` 与批量的关系式、假设条件、页码
- [x] P3 在线补：CVaR 小批量偏差下界、RM 分位数追踪、IS、EVT 外推、MLMC
- [x] P4 Q3 bang-bang 专项（含零结果核查）
- [x] P5 Q4 放弃档位先例专项（含零结果核查）
- [x] P6 写交付文件，标证据等级与零结果声明
