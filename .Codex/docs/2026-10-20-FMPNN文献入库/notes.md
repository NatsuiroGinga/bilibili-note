# FM/PNN 家族文献入库检查点

> 每完成一篇立即追加。证据分级：本地全文（原件 PDF 页码已核验）＞ Zotero 附件全文 ＞ 在线摘要 ＞ 仅题录。

## 0. 查重（本任务开始）

- 本地全文检索：`rg -il "factorization machines|product-based neural|xdeepfm" wiki/papers/ raw/papers/` → **零命中**。
- Zotero 检索（第一次）：
  - `zotero_search_items("Factorization Machines")` → 工具返回 “No items found”；
  - `zotero_search_items("Product-based Neural Networks")` → “No items found”；
  - `zotero_search_items("xDeepFM")` → “No items found”；
  - `zotero_search_items("1805.11843")` → “No items found”。
- **检索工具缺陷披露**：上述按题名检索返回零命中，但随后用 `zotero_search_items("Rendle")` 命中 3 条同题条目
  （`6RQSW2FV`、`H7MK7SZM`、`XT7UI4TS`），且 `zotero_get_collection_items(zqujm3ww)` 显示 PNN 已有条目 `9RFSEWUE`。
  即「按完整题名检索」在本 MCP 版本下不可靠，查重结论不能只依赖该通道。由此本任务**新增了两条重复条目**：
  - FM：`XT7UI4TS`（新建，无 PDF），与既有 `6RQSW2FV`、`H7MK7SZM` 重复；
  - PNN：`LR3KTQNA`（新建，**带 PDF**），与既有 `9RFSEWUE`（无 PDF）重复。
  建议主代理保留带 PDF 的 `LR3KTQNA` 合并 PNN；FM 三条均无 PDF，任选一条作 canonical。

## 1. Rendle, Factorization Machines（ICDM 2010）

- 查询式：DOI `10.1109/ICDM.2010.127` → `zotero_add_items_by_doi`。
- 工具返回：`✓ Factorization Machines → key XT7UI4TS — Imported as paper`；**PDF 未自动附加**。
- `zotero_find_and_attach_pdfs(["XT7UI4TS"])` → `✗ PDF not attached`。
- 元数据（工具返回）：Rendle, Steffen；2010-12；conferencePaper；DOI 10.1109/ICDM.2010.127。
- 全文状态：**仅题录**。Zotero 存储（`/Users/bilibili/Zotero/storage`）内 `*Factorization*.pdf` 只命中 Android FM 一篇；
  无 Rendle 原件。IEEE 付费墙，且本会话 WebFetch 对所有域名返回 “Unable to verify if domain … is safe to fetch”，
  无 shell 可尝试其他合法渠道。
- 阻塞登记：需主代理从 IEEE Xplore 或作者/机构合法公开副本取得 PDF，落 `raw/papers/methodology/2010-Rendle-FactorizationMachines.pdf`，
  再补 `wiki/papers/methodology/2010-Rendle-因子分解机.md` 与 SHA-256。**未写笔记，未从记忆补公式**。

## 2. Qu et al., PNN（arXiv:1611.00144）

- 查询式：`zotero_add_items_by_arxiv(["1611.00144"])`。
- 工具返回：`✓ Product-based Neural Networks for User Response Prediction → key LR3KTQNA — Imported as paper + PDF attached`。
- 元数据（arXiv API 经工具返回）：Yanru Qu, Han Cai, Kan Ren, Weinan Zhang, Yong Yu, Ying Wen, Jun Wang；
  2016-11-01；preprint；`https://arxiv.org/abs/1611.00144`。
- 原件：Zotero 存储 `/Users/bilibili/Zotero/storage/ETX7DZGA/Qu 等 - 2016 - Product-based Neural Networks for User Response Prediction.pdf`，6 个物理页。
- 证据等级：**本地全文**（PDF 逐页读取核验；公式 Eq. 1–14、表 I–III、图 2–5 均回到原页）。
- 关键页码：Eq. 1–5 与图 1 在第 2 页；Eq. 6–14 与复杂度推导在第 3 页；§D 与实验设置在页 4；
  表 I–III 与消融起点在页 5；图 4–5、激活函数与结论在页 6。
- 版本边界：本题录是 **arXiv v1 预印本**；文档所称 ICDM 2016 正式版未取得，不能断言两者逐字一致。
- 笔记：`wiki/papers/methodology/2016-Qu-乘积神经网络PNN.md`（已写）。

## 3. Li et al. 2018（arXiv:1805.11843）

- 查询式：`zotero_add_items_by_arxiv(["1805.11843"])`。
- **假设否决**：工具返回题名 “Android Malware Detection based on Factorization Machine”，
  作者 Chenglin Li, Keith Mills, Rui Zhu, Di Niu, Hongwen Zhang, Husam Kinawi；2018-05-30。
  **不是 xDeepFM，也不是 KDD 2018 论文**。文档本身第 71 行也把它记为 “Android FM”，与本次返回一致；
  父任务简报的 xDeepFM 猜测不成立。
- 原件：Zotero 存储 `/Users/bilibili/Zotero/storage/V7IGFACC/Li 等 - 2018 - Android Malware Detection based on Factorization Machine.pdf`，10 个物理页，v2（2019-08-13）。
- 证据等级：**本地全文**（Eq. 1–5、表 1–8 均回页核验）。
- 关键页码：特征抽取与 one-hot 在页 2–3；一阶模型局限与 Eq. 1–3 在页 4；FM 定义 Eq. 4–5 与 partial FM 在页 5；
  数据集表 2、Table 3/4/5 与超参在页 6；结果解释与 15×/50× 训练时间在页 7；族分类表 8 在页 8；结论在页 9–10。
- 笔记：`wiki/papers/methodology/2018-Li-安卓恶意软件因子分解机.md`（已写）。

## 4. Zotero 集合与后处理

- 三条目均已进入 `zqujm3ww`（methodology）：`XT7UI4TS`、`LR3KTQNA`、`KMI7KW38`；
  PNN 与 Android FM 的 PDF 附件键分别为 `ETX7DZGA`、`V7IGFACC`。
- 写入路径分歧：`zotero_add_items_by_arxiv` 落在**本地库**（web API 查 `LR3KTQNA` 返回 404），
  而 `zotero_add_items_by_doi` 落在 web 用户库（`users/21101662`）。因此
  `zotero_reconcile_collection_duplicates(zqujm3ww, dry_run=true)` 返回 `duplicate groups: 0`——
  web API 看不到本地条目，**该后处理对本集合无效**，不能据此认为无重复。
- 未执行真实合并：集合内还有大量与本任务无关的历史重复项，全局 reconcile 会越权改动。

## 5. 未完成项（交给主代理）

1. 将两个 Zotero 存储 PDF 复制到 `raw/papers/methodology/`（文件名见 task_plan）。
2. 对两份原件执行 `shasum -a 256`，回填两篇 wiki 笔记的 `sha256` 字段，并把 `source_pdf` 由 Zotero 路径改为 `raw/` 路径。
3. Rendle FM 全文获取（付费墙），取得后补第三篇笔记。
4. Zotero 重复条目合并：PNN 保留 `LR3KTQNA`；FM 三条 `6RQSW2FV`/`H7MK7SZM`/`XT7UI4TS` 合并为一条。
5. 本任务改动前未执行 `git status --short`（无 shell），提交前请核对目标文件快照。

## 6. 本次写入的文件

- `wiki/papers/methodology/2016-Qu-乘积神经网络PNN.md`（新建）
- `wiki/papers/methodology/2018-Li-安卓恶意软件因子分解机.md`（新建）
- `wiki/papers/methodology/INDEX.md`（新增「特征交互家族：FM / PNN」一节；既有正文按原文重写）
- `.Codex/docs/2026-10-20-FMPNN文献入库/task_plan.md`（新建）
- `.Codex/docs/2026-10-20-FMPNN文献入库/notes.md`（本文件）
