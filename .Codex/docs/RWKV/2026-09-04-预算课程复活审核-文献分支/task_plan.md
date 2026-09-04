# Task Plan: 预算课程调度候选复活审核（文献分支·证伪立场）

代理：`budget_curriculum_literature_falsification_opus`，模型 `opus`（`model: opus` 参数生效），
effort **继承会话设置**（Claude Code 的 Agent 工具无 `effort` 入参，提示词中的「高强度」措辞不是已生效参数）。

工作目录：`/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819`（分支 `exp/eta-ber-20260904`）

## Goal

用文献证据检验主代理 2026-09-04 的主张：「单水平退火**有**成熟先例；多档 staging **仍无**先例；
若本候选改走单水平退火形态，文献支撑立即成立」。立场是**证伪**，不是找支持。

## 三条待判

- [x] 判一：Bardou `(α_n)` 与 Ordered SGD `q` 退火，是否真是「单水平」？有没有哪一篇实际上就是多水平？
- [x] 判二：把「六档并列」映射到「单水平退火」，本身是否就是一次没有先例的任务化改造？
- [x] 判三：补检索邻近先例（multi-quantile / non-crossing / spectral risk / multi-level CVaR /
      multi-budget pAUC / curriculum over quantile levels），裁断「有先例／无先例／有邻近但不对位」

## Phases

- [x] P0 建立检查点文件（本文件 + notes.md），提交
- [x] P1 读主代理待审文档（`thesis/methods/机制一候选-预算课程调度-先验裁决.md` §7.1、
      `机制一候选-预算课程调度.md` §7.2）与既有笔记
- [x] P2 判一：回 Bardou / Kawaguchi **原件正文**核实（全文笔记 + 必要时 pdf-converter 重转），给页码/公式号
- [x] P3 判二：裁断映射代价；检索文献中是否讨论「单水平退火 vs 多水平并列」的关系
- [x] P4 判三：本地混合索引 → Zotero → 在线（google-scholar / MCP），补检索六个方向
- [x] P5 写 `裁断.md`，提交

## Key Questions

1. Bardou 的 `(α_n)` 是「一个 α 沿时间移动」还是算法内部同时维护多个水平（IS 辅助水平、多 VaR/CVaR 并存）？
2. Ordered SGD 的 `q` 是否等价于一个风险水平？退火时旧 `q` 是否仍在损失中？有无「多个 q 并列」讨论？
3. 谱风险测度（对 α 加权积分＝多水平连续极限）的文献里，有没有「按水平逐步引入」或「粗到细水平网格」？
4. non-crossing quantile 文献与「六个 ξ 的次序与间距」是否同一数学问题？其训练是否分阶段？

## Decisions Made

（随进度追加）

## Errors Encountered

（随进度追加）

## Status

**已完成** — 三条判断全部出结论，`裁断.md` 已落盘。判一/判二基于本地全文；判三仅到在线摘要，入库为阻断项。
