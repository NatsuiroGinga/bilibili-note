# 任务计划：第三章当代对照补查（2026-10-15）

## 目标
补第三章「当代对照方法」段。本文第三章 13 篇引用中位年份 2020，近两年仅 3 篇（LAMDA/FreeMOCA/Seo 2025），其中只有 Seo 2025 与机制直接竞争。
**要解决的是「基线刻度尺」问题：让审稿人看到我们和当前最强方法比过。**

## 两问
- **问 1**：2024–2026 固定/受限存储预算下的持续学习方法代表作（固定总容量、缓冲选样/回放分配竞争族：多样性选样、梯度/干扰感知、类平衡、重要性抽样）。
- **问 2**：2024–2026 恶意软件/Android 持续学习检测，特别是已在 **LAMDA** 上评测的。

## 每篇三问（核心产出）
1. 能否在固定存储预算 **200 条**下运行（还是需增长式缓冲/额外模型副本）？
2. 能否挂 **MLP**（有无架构假设）？
3. 有无**公开代码**（决定能否真跑基线）？

## 本文第三章设定（决定什么方法能当对照）
- 数据 LAMDA，Android，12 年度顺序到达（Domain-IL），4,561 维二值特征，二分类
- 协议：每年度 10 轮、批 1024、SGD(lr=0.01,mom=0.9,wd=1e-6)、BCELoss、阈值 0.5
- **固定存储预算 200 条**；骨干四层 MLP（2,687,293 参数）
- 本文方法：按年度等额配额 ＋ 年内标签分层 ＋ 按正例数亏空加权复用倍数
- 现有对照：朴素更新、经验回放、联合训练（上界）、逐参数位移插值、EWC、LwF

## 执行步骤
1. [x] 建 task_plan.md / notes.md
2. [ ] 本地查重：rg 扫 wiki/papers/**.md ＋ Zotero 语义检索（本地混合索引坏了，见下）
3. [ ] 在线检索：scholar CLI（挂代理）＋ WebSearch/WebFetch ＋ Zotero MCP
4. [ ] 对最有价值的新论文取全文（MinerU）→ 入库 raw/ ＋ wiki/
5. [ ] 写报告.md（三张表＋入库/无法获取/检索式/故障记录＋一句话裁决）

## 已知边界
- 本地混合索引坏（`scripts/literature_search/build.py:89` `device` kwarg），**不修**；本地查重用 rg ＋ Zotero 语义检索
- 库内已有相关件（不重复入库）：FOREVER 2026、MADAR 2025、Ghiani 2025、Chen 2023、Krawczyk 2024、Seo 2025 等
- 不跑实验、不改生产代码、不改 thesis/、不 git 提交

## 可用工具实况（2026-10-15 实测）
- 有：`mcp__zotero__*`、`mcp__research-knowledge__*`、`Skill`（google-scholar / pdf-converter / citation-verification）、Bash（scholar CLI）、WebSearch、WebFetch
- **无**：ToolSearch、任务简报提到的 `mcp__990aea2c-*`/`mcp__4cfe5157-*`/`mcp__6874b72c-*`/`mcp__50ccb3c5-*`/`mcp__d0a01844-*`（不在本代理工具表）
