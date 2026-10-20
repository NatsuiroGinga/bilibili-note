# 第二机制方向定向文献检索（任务计划）

- 日期：2026-10-20
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908`
- 代理角色：定向文献检索（只登记候选，不做存废裁决）

## 目标

为第四章第二机制的两个候选方向提供定向文献锚点：

- 方向 A「缺口加权集成容量调度」：按年度正例稀缺度调制集成容量／成员数／成员噪声。
- 方向 B「成员-年度锚定」：成员与年度（或年度组）显式绑定，利用回放缓冲的年度分块结构。

背景：TabM（BatchEnsemble 型参数高效集成，k=4）已在 LAMDA 12 年 Domain-IL 协议通过冻结判据。

## 任务边界

- 仅下载 BatchEnsemble 全文；其余只登记题录候选，不下载全文。
- 不改其他文件，不 commit。
- 所有题录经 arXiv API / Crossref / 检索 API 核实，禁止凭记忆。

## 文件所有权

- `.Codex/docs/2026-10-20-第二机制方向文献检索/task_plan.md`、`notes.md`
- `raw/papers/methodology/`（仅 BatchEnsemble PDF）
- `wiki/papers/methodology/`（BatchEnsemble 全文笔记 + INDEX.md 追加）

## 执行步骤

1. arXiv API 核实 BatchEnsemble 题录（arXiv ID、作者、标题、ICLR 2020 状态）。
2. 下载 PDF → `raw/papers/methodology/` → SHA-256 → MinerU 转换 → 全文笔记（八字段＋SHA）→ 更新 INDEX。
3. 组 1（方向 A）检索：本地混合索引优先，再 arXiv/Crossref/WebSearch 核实题录。
4. 组 2（方向 B）检索：同上。
5. 汇总锚点表与全文入库推荐。

## 验收

- notes.md 每个方向一张锚点表：论文、题录验证状态、证据等级、与方向关系、是否值得全文入库。
- 每组记录检索式与来源。
- 回报 ≤20 行。

## 状态

- [x] 任务目录建立
- [x] BatchEnsemble 题录核实（Zotero arXiv 导入 + PDF 页眉；arXiv:2002.06715v2，ICLR 2020，Wen/Tran/Ba）
- [~] BatchEnsemble 入库：笔记与 INDEX 已完成；**raw/ PDF、SHA-256、MinerU 未完成（本次会话无 Bash）**
- [x] 组 1 检索（5 条主查询 + 6 条题录追查）
- [x] 组 2 检索（4 条主查询 + 7 条题录追查）
- [x] 汇总锚点表与全文入库推荐

## 工具限制（必须向下传递）

本次会话未提供 Bash；`uv run ... literature_search` 与 PDF 复制/哈希/MinerU 均不可执行。
WebFetch 对 arxiv.org、export.arxiv.org、dblp.org、api.semanticscholar.org、api.openreview.net
均被域名安全策略拦截。实际使用：Zotero arXiv 导入（题录 E3）、WebSearch 多源交叉（E4/E5）、
Zotero 全文提取与 PDF 直读（E1）。
