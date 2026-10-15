# 任务计划：第四章鲁棒家族文献补查

日期：2026-10-15
工作树：`.worktrees/ch3-lamda-20260908`（第四章候选：以年度为组的最坏组风险训练目标）

## 目标

为第四章「以年度为组的 group 级最坏风险训练（GroupDRO 家族）」补查 2023–2026 文献，重点三问：

- **问 1（最高优先）**：对「域泛化/不变性方法打不过 ERM」批评（Gulrajani & Lopez-Paz, ICLR 2021）的后续进展（新协议/新方法/修正或反驳）。
- **问 2**：非平稳／持续域泛化（non-stationary / continual DG）2023–2026 成熟家族。
- **问 3**：按时间/组分组的 DRO 进展；DRO 用于年度序列恶意软件/入侵检测的工作。

## 边界

- 不跑实验、不改生产代码、不改 `thesis/`。
- 只用检索、判读、入库。
- 不 git 提交。

## 检索顺序（强制）

本地查重（`rg` 扫 `wiki/papers/**/*.md` + Zotero 语义检索）→ 在线检索 → 取全文入库。
本地混合索引已坏（`build.py:89` EmbeddingBackend device 参数），**不修**，用 rg + Zotero 替代。

## 阶段

- [ ] P0 环境与本地盘点（PDF/工具/wiki 结构）
- [ ] P1 读本地全文：Pham nonstationary DG、Feng Wasserstein-DRO
- [ ] P2 问 1：ERM vs DG 批评的后续（benchmark/SWAD/综述）
- [ ] P3 问 2：non-stationary / continual DG
- [ ] P4 问 3：时序 DRO / group-DRO 变体 / 恶意软件年度 DRO
- [ ] P5 入库：PDF → raw/papers，笔记 → wiki/papers，更新 INDEX
- [ ] P6 报告落盘

## 工具

- scholar CLI（须 `HTTPS_PROXY=http://127.0.0.1:7890`，短查询）
- MCP：zotero_semantic_search 等、搜索类 MCP
- pdf-converter（MinerU）读 PDF
