---
title: 长度分层 Tong 证书定向文献调研计划
date: 2026-08-26
tags:
  - 类型/计划
  - RWKV/第四章
  - 风险控制
---

# 长度分层 Tong 证书 — 定向文献调研计划

> 代理：`stratified_risk_control_literature_opus`
> 模型：claude-opus-5[1m]，effort：默认（高）
> 任务目录：`.Codex/docs/RWKV/2026-08-26-分层风险控制定向文献/`

## 目标

为第四章「长度分层 Tong 证书」机制核清**机制来源**与**本课题新颖性差量**。
不泛读，只做三束定向检索。

## 研究语境（判断相关性用，不写进论文）

- 加密恶意流量实体级告警，LSPR23 源年校准，实体误报预算 `q=4%`。
- 现状：Tong 式有限样本证书（Clopper-Pearson 上界 + `δ` 均分）控制池化路径最大风险。
- 新机制：按实体流数长度桶分层的条件证书（组条件 FPR 控制）。

## 三束检索

| 束 | 主题 | 要回答的问题 |
|---|---|---|
| A | 组条件 / Mondrian 保形与条件风险控制 | 组条件有限样本 FPR 控制的标准做法与保证形式？`δ` 在组×方向上的分裂有无既有方案？ |
| B | 分层多重检验预算分配 | 桶级预算与池化预算并存时的既有分配理论？ |
| C | 安全告警预算的分面控制 | 实体长度分面误报预算在安全域有无直接近邻？没有也是结论（研究空白证据） |

## 流程门禁

1. **本地优先**：`literature_search status --json` → 按束 `query --scope paper --mode hybrid --json`（504 篇论文笔记）。
2. **索引状态**：初始 `stale=true`（`source_added`/`source_changed`），`vector_count=0`。已启动 `build --offline` 全量重建；重建完成前的检索一律标为 lexical 通道，向量通道未运行。
3. **在线补充**：本地不足才用 WebSearch / OpenAlex / alphaxiv；在线结果只是题录候选，不得升级为全文证据。
4. **载荷级入库**：最直接的 3–6 篇下 PDF 到 `raw/papers/`，全文笔记写 `wiki/papers/`，Zotero 按 arXiv/DOI 导入并附 PDF。只给题名或链接算未完成。
5. **检查点**：每完成一束或一篇全文立即落盘到 `notes.md`（查询式、URL、原件路径、证据等级、页码、纳入/排除理由、Zotero 状态）。

## 证据等级约定

- **题录级**：只有题名/作者/年份/DOI。
- **摘要级**：读过摘要，未见全文。
- **E3 全文级**：`raw/` 有原件 + `wiki/` 有基于全文的结构化笔记 + 关键论断标注页码或公式号。

只有 E3 才能支撑正文论断。

## 边界措辞

结论一律写「**本次检索所及**」，不得写成「文献中不存在」。

## 待办

- [x] 读取 `raw/AGENTS.md`、`wiki/AGENTS.md`、`SCHEMA.md`
- [x] 索引状态核查 + 重建（向量通道已起，`vector_count=38245`，`papers` 集合零差异）
- [x] 束 A 检索与裁决 — 机制正源为 Vovk 2012 条件 ICP
- [x] 束 B 检索与裁决 — 最强近邻为 Barber & Ramdas 2017 p-filter
- [x] 束 C 检索与裁决 — CALIBURN 与 Transcendent 各缺一半，空白成立
- [x] 6 篇载荷级入库（PDF + 全文笔记 + Zotero，全部 `lint --strict` 零错）
- [x] 新颖性差量表（9 行，见 `notes.md` §4）
- [x] 负面结果核查 — 不可能性定理**不阻断**本机制（Barber 物理第 11 页式 (7)）

**任务完成**。交付见 `notes.md`；未关闭疑点 8 项列于 `notes.md` §7，其中疑点 1（`δ` 二维分裂最优性）与疑点 3（Gibbs／Kandinsky 未入全文）建议下一轮优先。
