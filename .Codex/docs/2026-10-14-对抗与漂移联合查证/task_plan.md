# 任务计划：对抗与漂移联合框架查证

- 日期：2026-10-14
- 代理：`查证-对抗与漂移联合框架`（opus / medium）
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908`
- 产出目录：`.Codex/docs/2026-10-14-对抗与漂移联合查证/`
- 只读边界：不跑训练、不启动 MPS 任务；只读另一工作树 `ch3-drift-20260908`（检索入口），绝不写。

## 封闭问题

- Q1 已发表工作：恶意软件对抗鲁棒性 × 时间/概念漂移的**联合**研究存在吗？（A 联合 / B 分开 / C 全无）
- Q2 「PAD 2023（TDSC）」的威胁模型、攻击、给出的保证类型；其「收敛」是否涉及分布漂移。
- Q3 特征空间攻击在二值静态特征（Drebin 式 / LAMDA 4,561 维 0-1）上是否可实施、是否被接受；有无已发表的 realizable/constrained 特征空间攻击评价。
- Q4 LAMDA 数据集上有无对抗评价（有 / 没有 / 不确定，给检索途径）。

## 检索顺序（强制）

1. 本地混合索引：`cd ch3-drift-20260908 && uv run --project scripts/literature_search --locked python -m scripts.literature_search query "<查询>" --scope local --mode hybrid --json`
2. Zotero：`mcp__zotero__zotero_semantic_search`、`zotero_search_items`
3. 在线：`google-scholar` 技能、WebSearch、arXiv API（直连）；被重置站点用 `curl -sS -x http://127.0.0.1:7890`

## 步骤

- [x] S0 建立任务目录与计划文件
- [ ] S1 本地混合索引跑 Q1–Q4 检索式，逐条落盘
- [ ] S2 Zotero 语义检索补漏，落盘
- [ ] S3 在线检索（Google Scholar / arXiv / WebSearch），落盘
- [ ] S4 Q2 回原件核 PAD 2023 原文（威胁模型/攻击/保证类型/是否涉漂移）
- [ ] S5 Q3 回原件核特征空间攻击可实现性文献页码
- [ ] S6 写 report.md（四问逐条）+ evidence-index.md
- [ ] S7 每节完成后 git commit

## 停止条件

- 四问各有「结论＋证据等级＋页码（或检索途径）」即完成；
- 找到 Q1 的 A 类（联合）论文即收窄 S3 的扩展检索；
- 不下最终裁决，不扩大范围。
