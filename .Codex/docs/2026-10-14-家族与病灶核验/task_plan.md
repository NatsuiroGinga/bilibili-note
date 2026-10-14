# 任务计划：七方法家族 × 病灶对口核验

任务目录：`.Codex/docs/2026-10-14-家族与病灶核验/`
工作树：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908`
日期：2026-10-14
执行代理：Claude Code（文献综述子代理）

## 工具可用性（本会话实测，先记录）

- **无 Bash 工具**（本次派发未提供）。因此：
  - 本地 `uv run ... literature_search` 子命令**无法执行**，改用 `Grep`（ripgrep 内核）直接扫 `wiki/papers/`、`raw/papers/` 的可读文本与结构化笔记。
  - `curl`（OpenAlex / arXiv）**无法执行**，改用 `WebFetch` 访问 OpenAlex REST JSON 与 arXiv abs 页。
  - 未提交改动：见文末「未提交清单」。
- Zotero MCP 可用（`zotero_search_items` / `zotero_get_item_fulltext` / `zotero_add_items_by_identifier`）。
- `WebSearch`、`WebFetch` 可用。

## 任务范围

核验七个方法家族能否作为本课题机制来源，逐族回答五问：
1. 「空」是否真实（恶意软件/安全 + 时间漂移域是否已引入；若已引入给最接近全文）
2. 形式化供给（定理类型 + 原始出处）
3. 对口病灶（P1–P4；区分概念对口 vs 实测支撑）
4. 可组合性（与哪些族共享形式化底座）
5. 接口可行性（模型无关，能否挂 MLP + GBDT 双骨干）

## 待核验家族

| # | 家族 | 变体 |
| --- | --- | --- |
| F1 | 分布鲁棒优化 | Group DRO, CVaR, Wasserstein DRO, χ²-DRO |
| F2 | 不变性学习 | IRM, VREx, IB-IRM, 及对 IRM 的批评 |
| F3 | 课程学习 | self-paced, 难度调度, 连续性课程 |
| F4 | 核心集/剪枝 | coreset selection, data pruning |
| F5 | 保形预测/分布无关风险控制 | conformal, NP 分类, selective risk |
| F6 | 博弈论 | Stackelberg, minimax, 对偶（含 M2/J06 数学否决边界） |
| F7 | 平坦极小值 | SAM, sharpness-aware, flat minima |

## 已实测病灶（对口判据，不得替换/改写）

- **P1** 未来年份分布未知且逐年变：静态源期模型逐年 AUROC 0.5712(2017)–0.9610(2022)。
  制品：`thesis/experiments/llm_probe/runs/diagnostics/ch3-lamda-preflight-e1-threshold-transfer-v1/metrics.json` 的 `per_year`
- **P2** 正例率崩塌：51.35%(2013) → 1.64%(2024) → 0.05%(2025)。
  制品：`.../ch3-lamda-e3-label-reliability-v1/metrics.json` 的 `pos_rate`
- **P3** 固定误报预算下漏检失控：源标定阈值过保守迁移；自校准降 FNR 11–30 点但仍高。
  制品：E1 `per_year` 的 `group_a`/`group_b`
- **P4** 标签正例共识随时间下降：vt_count 中位数 12(2016)→5(2024)；恰在阈值上占比 6.8%→48.1%；与 AUROC Spearman +0.737 (p=0.015, n=10)。**最弱证据，需独立复核。**
  制品：E3 metrics.json

## 执行顺序

1. 本地 Grep 扫现有 115+ 结构化笔记 + raw 全文本，逐族取本地命中
2. Zotero 语义/关键词检索，排重与补全
3. WebFetch OpenAlex `filter=title_and_abstract.search` + `sort=publication_year:desc`，逐族在线候选
4. 逐族立即落 `notes.md`（查询式/URL/证据等级/命中/纳排理由）
5. 关键族取全文（WebFetch / Zotero fulltext / arXiv PDF），入 `raw/papers/` + `wiki/papers/` 结构化笔记
6. 汇总 `report.md`：七族 × 五问矩阵 + 判读

## 边界

- 不下选题裁决；只交事实与可核验判读。
- 不改 `raw/` 原件、不改 `wiki/papers/attack-detection/*全文.md`。
- 结论写「未发现」而非「不存在」，注明检索覆盖面。

## 未提交清单

（任务执行中更新）
