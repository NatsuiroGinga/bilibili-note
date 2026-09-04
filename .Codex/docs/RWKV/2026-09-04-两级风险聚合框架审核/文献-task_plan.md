# 文献审核 task_plan（插值式软 top-k 算子的先例核查）

<!-- RESEARCH_ROUTE=RWKV -->

- 建立时间：2026-09-04
- 代理：literature-reviewer（Claude Code）
- 交付：`.Codex/docs/RWKV/2026-09-04-两级风险聚合框架审核/文献核查.md`
- 过程记录：本文件 + `文献-notes.md`

## 待审对象（原文照录，不重新论证）

设逐流分数降序 `s_1 ≥ s_2 ≥ … ≥ s_m`，`t = clamp(α·m, 1, m)`，`k = ⌊t⌋`，`f = t − k`：

```
S_e = ( Σ_{i<k} s_i  +  f · s_k ) / t
```

## 四问

| 编号 | 问题 | 状态 |
| --- | --- | --- |
| Q1 | 插值式软 top-k / 连续分位数有无成熟先例？与 RU 的 CVaR 离散样本估计是否同一个东西？ | 已完成 |
| Q2 | 先例报告过什么已知问题（梯度偏差/方差、平台区、稀疏梯度、数值稳定性）？ | 已完成 |
| Q3 | 「两级风险聚合、级间参数需相容」有无先例？ | 已完成 |
| Q4 | 可学风险水平参数退化到端点（α→0/1）有无报告？ | 已完成 |

## 工具实况（影响可复现性，开工即登记）

本代理**没有** `Bash`、`Skill`、`ToolSearch` 工具。故：

| 规定路径 | 实际执行 |
| --- | --- |
| `uv run --project scripts/literature_search ... query --mode hybrid` | **无法执行**（无 Bash）。改用内置 `Grep`/`Glob` 检索 `wiki/papers/**`、`thesis/**`，等价 lexical 通道，**向量通道未运行** |
| `Skill` 调 `google-scholar`／`pdf-converter` | **无法调用**。在线检索用 `WebSearch`+`WebFetch`；PDF 用 `Read` 的原生 PDF 通道（**非 `pdftotext`**，未违反禁令） |
| `ToolSearch` 加载五个 MCP 检索服务 | **不在可用工具表内**。Zotero MCP 工具可直接调用（`semantic_search`／`search_items`／`get_item_fulltext`） |
| 分阶段 `git commit` | **无法执行**（无 Bash）。已分阶段落盘文件，**需主代理补提交** |

## 执行顺序

1. [x] 读仓库已有两份文献核查（避免重复劳动）
2. [x] 本地语料 lexical 检索（Grep/Glob）
3. [x] Zotero 语义检索 + 全文
4. [x] 在线检索 Q1（CVaR 离散估计、Hyndman-Fan、soft top-k、NeuralSort/SoftSort/OT 排序）
5. [x] 在线检索 Q2（已知问题）
6. [x] 在线检索 Q3（nested/multi-level risk）
7. [x] 在线检索 Q4（可学参数跑到端点）
8. [x] 写 `文献核查.md`

## 落盘纪律

每完成一问立即写入 `文献-notes.md` 与 `文献核查.md` 对应节，不等全部完成。
无法 `git commit`（无 Bash），**主代理须补提交**，Conventional Commits，禁 Co-Authored-By。
