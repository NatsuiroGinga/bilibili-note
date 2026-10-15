# task_plan：RGA（Rank-Gated Acquisition）文献核实

- 日期：2026-10-15
- 任务类型：文献检索与判读（只检索，不跑实验）
- 研究对象：第四章候选机制 RGA（排序门控获取），服务于 LAMDA 跨年度 Android 恶意软件检测（Domain-IL 逐年到达，12 年度，4561 维二值特征，二分类）
- RGA 核心命题：当且仅当模型在「排序头部」有 lift（$\alpha^{\max} > 1$）时，主动获取才带来正收益；临界标注量 $\ell_c(s) = 1/(\alpha_s p_s)$

## 目标问题

1. 「排序头部质量作为主动获取可行性的门」有无文献先例？（原文/页码/公式）
2. RGA 两个分支（主动获取侧／排序侧）各自成熟家族与可引用代表作
3. 直接近邻：同时做「预算受限主动标注」与「存储受限持续学习/回放」的工作（重点：CITADEL 2025 Haque、Faber DSAA 2022）
4. 诚实结论：任务化改造 / 已被做过 / 无先例三选一

## 阶段

- [x] 建目录、task_plan.md、notes.md
- [ ] 本地查重：Zotero 语义检索 + 本地混合索引（避免重复调研）
- [ ] 在线检索（scholar CLI 挂代理）：按问题分支组织查询
- [ ] 原文定位与获取（arXiv/出版社主站；pdf-converter 转换）
- [ ] Faber DSAA 2022 全文获取（本地未取得，尽力）
- [ ] 入库：PDF → raw/papers/attack-detection/lamda-related/；笔记 → wiki/papers/attack-detection/lamda-related/；更新 INDEX.md
- [ ] 报告落盘（中文文件名）
- [ ] 回报：模型名、检索式、入库清单、一句话裁决

## 边界

- 不跑任何实验；在线结果只作候选，核原文须在 arXiv/出版社主站重新定位
- 不 git 提交（工作树有并行任务改动）
- 只操作本任务文件
- 未取得原文的条目明确标注「仅题录/在线摘要」，不得冒充全文证据
