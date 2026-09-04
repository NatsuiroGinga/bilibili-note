# EAS 家族谱系调研 · 落盘笔记

日期：2026-09-04 · 代理：文献子代理（`opus`，effort 继承会话设置）

## 检索执行记录

| 步骤 | 工具与命令 | 结果 |
| --- | --- | --- |
| 1 | `literature_search status --json` | 索引存在，`140,184` 向量，`dim=384`，`mps:0`；**`stale=true`**（`source_added`、`source_changed`） |
| 2 | `query "safe screening" --scope local --mode hybrid` | Ogawa 两份笔记居首（`0.0328`／`0.0323`）；**家族其余五条本地全部缺失** |
| 3 | 同上，另四个查询式 | `safe feature elimination lasso`、`safe sample screening non-support vector`、`sparse backpropagation top-k gradient`、`screening rules lasso duality gap`——均只命中 Ogawa 与无关条目 |
| 4 | Zotero `semantic_search` / `search_items` | **`[Errno 61] Connection refused`**，桌面端本地 API 未运行；语义索引返回 15 个 key 但元数据全部取不回，相似度全负 |
| 5 | arXiv API `id_list` 逐个核验 | 五个 ID 全部可打开，题录见下 |
| 6 | 下载 4 篇 PDF → `tools/pdf_to_fulltext.sh --jobs 2`（MinerU extract） | **4/4 成功**，无失败 |

**JSON 结构坑**：该工具返回的结果数组键是 `local_results`，不是 `results`／`hits`。
首次用错键导致五个查询静默返回空，浪费一轮。**下次直接用 `local_results`。**

## 逐条题录核验（arXiv API，2026-09-04）

| arXiv ID | 题名 | 一作 | 发表 | 入库 |
| --- | --- | --- | --- | --- |
| 1009.4219v2 | Safe Feature Elimination for the LASSO... | El Ghaoui | v1 2010-09-21，v2 2011-05-18，注记「Submitted to JMLR in April 2011」 | ✔ 本轮 |
| 1912.02566v3 | Screening Data Points in ERM via Ellipsoidal Regions... | Mialon | comment 字段写明 AISTATS 2020 | ✔ 本轮 |
| 1706.06197v5 | meProp: Sparsified Back Propagation... | Sun | comment 字段写明 ICML 2017 | ✔ 本轮 |
| 2302.04852v1 | SparseProp: Efficient Sparse Backpropagation... | Nikdan | **无 `journal_ref`，会议归属未核验** | ✔ 本轮 |
| 2306.03725 | Towards Memory-Efficient Training... | Schultheis | DOI `10.1007/978-3-031-43418-1_41` 在 arXiv 元数据中 | 入库在先 |

**未编造任何题录。** 未取得全文的四条（Bonnefoy 1412.4080、Shibagaki 1602.02485、
Ndiaye 1611.05780、Narasimhan 1605.04337）在产出文件中一律标 `在线摘要`。

## 对抗性检索（§3 的核心）

arXiv API `all:` 字段（覆盖题名／摘要／注记，**不含全文**）：

零命中：`"safe screening"+ranking`、`+AUC`、`+pairwise`、`+"neural network"`、
`+"multiple instance"`、`"active set"+"pairwise ranking"`。

**零命中的有效性已验证**：对照检索 `"safe screening"+lasso` 返回 14 条正确结果，
`"safe screening"` 单独返回 15 条正确结果 —— 检索式与 AND 运算符工作正常。

唯一需处理的近邻：`1605.04337` Narasimhan & Agarwal，pAUC 的结构化 SVM ＋ 割平面。
**命中原因是摘要里的 “biometric screening”，与 safe screening 无关。**
但它是 BER 目标函数的凸祖先，割平面维护的约束活动集是家族外最接近的结构。
**待办：取其全文确认割平面活动集语义，否则正文「排序损失上无先例」有被反驳风险。**

OpenAlex 对同组查询无效——被生物医学的 “screening” 淹没，未提供补充。

## 关键裁决

1. **「首次在深度网络里做可证明精确的反传剔除」不成立**（Schultheis 已做）。
   EAS 文档 §6 的收窄正确，本轮独立复核确认。
2. **「安全筛除未用于成对／排序损失」目前成立**，但只有 arXiv 摘要级证据，须如此标注。
3. **EAS-full 所在格子空缺有结构性理由**：凸分支的「求解前判定」全靠对偶，
   深度分支没有对偶，故 Schultheis 只能退到前向之后并自陈仍需完整前向。
   **空白是因为难，不是因为没人想到——新颖性与失败风险同源。**
4. **meProp 提供一条反向警示**：其准确率不降反升，
   故**不得声称「精确优于近似」**；EAS 的卖点只能是工程确定性。
5. SparseProp **不属于 safe screening**（不做筛除判定），已在谱系表与笔记中显式说明。

## 交付

- 产出：`thesis/methods/第四章机制一-EAS家族谱系.md`
- 新增原件 4 篇：`raw/papers/methodology/training-efficiency/`
- 新增 MinerU 全文 4 份 ＋ 结构化笔记 4 份：`wiki/papers/methodology/training-efficiency/`
- `INDEX.md` 新建「凸问题的可证明安全筛除」小节，Ogawa 从稀疏反传节移入（无重复链接）
- 提交：`671906b`、`a05eb9a`、`4109c9d`、`91602de`、`e5c88f5`（分阶段落盘，未攒结果）

## 未关闭事项

- Zotero 不可用 → **本地 Zotero 是否已收录这四篇未能核实**（改以仓库目录去重）
- 本地混合索引 `stale=true`，未包含本轮新增全文（本轮结论不依赖索引完备性）
- `1605.04337` 全文未取（见上）
- El Ghaoui 与 SparseProp 的正式发表归属未核验，引用只写 arXiv 标识
