---
title: "Bi-level Unbalanced Optimal Transport for Partial Domain Adaptation"
authors: [Zi-Ying Chen, Chuan-Xian Ren, Hong Yan]
year: 2025
date: 2026-08-12
journal: "Pattern Recognition 174，2026；arXiv 预印本 2025"
source_pdf: "[[raw/papers/methodology/2025-Chen-BUOT-Bilevel-Unbalanced-Optimal-Transport.pdf]]"
zotero_key: LHAIR4ZV
zotero_key: LHAIR4ZV
tags: [部分域适应, 非平衡最优传输, 伪标签, 类别不平衡, 类型/论文]
key_finding: "BUOT 以样本与类别双层传输缓解单层权重缺陷，但仍可能用低成本质量丢弃稀有恶意样本，并依赖目标伪标签。"
method: "样本—类别双层非平衡传输、标签感知成本、双层边缘重加权"
baseline: "普通 OT/UOT、单层权重和对齐消融"
aliases: [BUOT, Chen2025-BUOT]
related: ["[[2025-Naram-WARMPOT部分域适应]]", "[[2025-Xue-PROTOCOL不平衡部分传输]]"]
---

# BUOT：样本—类别双层非平衡传输

## 论文原结论

BUOT 让样本传输计划 `Γ_1` 与类别传输计划 `Γ_2` 互相引导，以非平衡边缘降低离群样本质量。公式（9）的标签感知成本区分同类与异类预测关系；定理 1 把四阶运算转为矩阵运算，两个更新复杂度分别为 `O(nK²)` 与 `O(n²K)`。恢复的双层边缘形成源权重，联合加权源交叉熵和目标熵训练。

## 可迁移机制

样本层和类/环境层的耦合可诊断条件错配；论文的“权重—对齐—联合”消融可转化为本任务递进对照。

## 本课题推论

低基率二分类下，边缘放松会优先保留廉价良性匹配并丢掉源恶意质量。第一候选必须增加源恶意真标签质量下限、支持拒绝、XGBoost 叶/分数锚与无标签停机。

## 不可直接声称

BUOT、普通 UOT 和双层耦合本身都不是原创。论文的部分域目标是丢弃源私有类，和同名二分类下保护稀有恶意质量的方向相反；目标伪标签错误仍会污染标签感知成本。

## 待验证

比较普通 UOT、BUOT 式双层耦合、恶意质量保护的非对称传输；若双层通用方法已同等有效，任务改造的独立贡献不成立。

## 文献信息

- arXiv：2506.08020
- DOI：10.1016/j.patcog.2025.112998
