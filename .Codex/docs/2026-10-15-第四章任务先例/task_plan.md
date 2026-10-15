# 任务计划：第四章研究任务先例核查

- 日期：2026-10-15
- 任务类型：文献检索与判读（只检索与判读，不跑任何实验）
- 委托方目的：**找同类任务**，确保该研究任务不是凭空编的；**不是**查占用（不是问「有没有人做过因而不能做」）

## 待核任务（原文照抄）

> 在**固定的存储预算**与**固定的标注预算**下，跨年度概念漂移的二分类检测中，把「**标什么**」（主动标注哪些未标注样本）与「**存什么**」（在存储受限的缓冲里保留哪些历史样本、复用几次）放进**同一个联合配置问题**。特别针对这样一种情形：某些年度的**已标注正例极度稀缺**（实测 2024 年训练分片正例率 1.64%、2025 年 0.05%），此时两个配置量都失去作用对象。

数据与协议：LAMDA 年度序列（12 个年度，4561 维二值特征，二分类），官方协议为 Domain-IL（年度顺序到达），每个年度 10 轮、批 1024、缓冲 200 条。

## 要回答的问题

1. 「标注预算」与「存储/记忆预算」同时受限、并被联合配置的持续学习工作（分 (a) 完全同构 / (b) 部分同构 / (c) 只有半边 三类）
2. 主动学习与持续学习/回放结合的主要文献；是否同时约束存储；是否处理标签极度不平衡
3. 「标注稀缺」或「正例稀缺」作为核心病灶的处理文献（长尾主动学习、imbalanced active learning、PU learning 流式/漂移版）
4. 恶意软件 / Android 漂移检测里把「标注获取」当一等公民的工作
5. 诚实结论：三选一 (a) 已被完整研究过；(b) 有大量相邻工作但该组合未见；(c) 未见任何相邻工作

## 检索策略（按序）

- [ ] P0 先读本地 CITADEL 全文（pdf-converter / MinerU），确认其协议
- [ ] P0 本地库清点：`raw/papers/attack-detection/lamda-related/` 53 篇 + `wiki/papers/attack-detection/lamda-related/` 全文笔记，先查本地避免重复入库
- [ ] P0 Zotero 语义检索：active continual learning / joint budget / imbalanced active learning
- [ ] P0 本地混合索引：scripts/literature_search（hybrid 模式）
- [ ] P1 Google Scholar（挂代理）：
  - "active learning" + "continual learning" + "memory budget"
  - "imbalanced active learning" / "long-tailed active learning"
  - "positive unlabeled learning" + drift / streaming
  - "label budget" + "memory budget" continual
  - active learning "concept drift" malware / android
  - "budgeted" continual learning annotation
- [ ] P1 arXiv 定位候选全文（按标题在 arXiv 重新定位 ID，核原文）
- [ ] P2 Faber (DSAA 2022) 原文获取尝试
- [ ] 入库：确认有用的 PDF → `raw/papers/attack-detection/lamda-related/`，笔记 → `wiki/papers/attack-detection/lamda-related/`，更新 INDEX.md；**不 git 提交**

## 落盘纪律

- 每 30 分钟更新 notes.md：已完成项、下一条查询、未关闭疑点、无法获取原文清单
- 报告文件名用中文（勿用 report.md，会被 hook 拦）

## 强制工具

- Google Scholar 挂代理：`HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 scholar search "<查询>" --json`
- 读 PDF 一律 pdf-converter 技能（MinerU），禁止 pdftotext
- Zotero 语义检索优先（避免重复入库）
- 本地混合索引：`uv run --project scripts/literature_search --locked python -m scripts.literature_search query "..." --scope local --mode hybrid --json`（从仓库根运行）
- 禁止 WebSearch 替代 scholar（实测 arXiv ID 幻觉率 4/4）
