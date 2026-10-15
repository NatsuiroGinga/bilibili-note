# 任务计划：优化器状态／动量在年度边界携带历史的文献调研

**日期**：2026-10-15
**工作树**：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908`
**边界**：不跑实验、不改生产代码、不改 `thesis/`

## 提案（纯推演，无本地文献支撑）

年度序列概念漂移下，SGD momentum=0.9 的 `momentum_buffer` 会把上一年的梯度方向带进当前年度训练；
跨年边界时方向已属漂移后的分布，可能拖累适应。候选机制：**年度边界对优化器状态做衰减／重置**。

## 四问

1. （最高）优化器状态在任务／分布边界携带历史造成危害的直接工作；optimizer reset / warm start vs cold start / momentum under distribution shift。
2. 可塑性丧失（loss of plasticity）直接文献；核验 Dohare et al. Nature 2024 是否存在；其机制是网络单元还是优化器状态；对固定小回放恶意软件设定是否可迁移。
3. 非平稳优化的收敛理论——动量在时变分布下的偏差／遗憾界（决定理论家族能否写）。
4. 上述任一机制用在恶意软件／入侵检测年度／时间漂移上的工作。

## 每篇的可用性三问

1. 能否在固定 200 条存储预算、每年度 10 轮协议下运行？
2. 能否挂四层 MLP（无架构假设）？
3. 有无公开代码？

## 执行顺序

- [x] 本地查重（wiki/papers + Zotero 语义检索）
- [ ] 问 1 在线检索（scholar / WebSearch / OpenAlex / arXiv）
- [ ] 问 2 在线检索（Dohare Nature 2024 核验）
- [ ] 问 3 在线检索（非平稳优化理论）
- [ ] 问 4 在线检索（恶意软件年度漂移 + 上述机制）
- [ ] 入库（PDF + 笔记 + INDEX）
- [ ] 写报告

## 工具与限流记录

- scholar CLI：需 `HTTPS_PROXY=http://127.0.0.1:7890`，查询词短，已知前序代理 429。
- 本地混合索引坏了（`scripts/literature_search/build.py:89`），不修，改用 rg + Zotero 语义检索。
