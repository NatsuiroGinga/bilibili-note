---
title: "TabR: Tabular Deep Learning Meets Nearest Neighbors"
authors: [Yury Gorishniy, Ivan Rubachev, Nikolay Kartashev, Daniil Shlenskii, Akim Kotelnikov, Artem Babenko]
year: 2024
date: 2026-08-20
journal: "International Conference on Learning Representations 2024"
source_pdf: "[[raw/papers/methodology/tree-inspired/2024-Gorishniy-TabR.pdf]]"
arxiv: "2307.14338"
sha256: "feec976974e73b858466227a749375ac6c2ec9320f98006aca0678883469f0bd"
zotero_item_key: "9C95X4NU"
tags: [表格数据, 检索增强, 最近邻, 局部模型, 类型/论文]
aliases: [TabR, Tabular Deep Learning Meets Nearest Neighbors]
key_finding: "TabR 用可学习键空间中的近邻特征和源训练标签形成局部修正，在数百万样本基准上优于多种 GBDT；但 300 万样本默认训练超过 18 小时，冻结上下文后仍需 3 小时 15 分，按当前共同预算不能直接扩至 LSPR23。"
related: ["[[2021-Gorishniy-表格数据深度学习模型再审视]]", "[[2025-Gorishniy-TabM参数高效集成]]"]
---

# TabR：检索增强表格网络

## 论文原方法

- 对目标样本与全部训练候选使用共享编码器，在键空间以负平方距离选前 `m` 个邻居；值由邻居源标签嵌入与目标到邻居的差值修正组成（物理页 4 至 6，式 5）。
- 候选集合严格来自训练集；训练时移除样本自身，避免直接标签泄漏（物理页 3、附录实现说明）。
- 论文在公开数据上覆盖到数百万对象，且正式报告 TabR 在所用 GBDT-friendly 基准上平均超过 GBDT。

## 规模硬门

- 300 万以上对象的 Weather 全量数据默认训练超过 18 小时；上下文冻结后从 18 小时 9 分降到 3 小时 15 分（物理页 9，表 6）。
- LSPR23 有 1635 万流，候选库和反复编码至少是上述规模的约五倍；在当前 4.5 GPU 小时共同上限下没有直接可执行证据。
- 官方仓库 `yandex-research/tabular-dl-tabr`，MIT，HEAD `17baa9082506f8e7a0f8d11bb1e08212926a1507`；依赖 Faiss，并提供内存节省和候选分批编码路径。

## 当前裁决

- 源训练标签作为邻居值不违反目标年标签禁入，但实体和近重复样本可能制造泄漏；必须按实体不相交划分并排除同实体候选。
- 当前不进入前三个立即实验候选。只有先证明候选库压缩不读目标标签、检索成本进入共同预算且块级近邻不跨实体泄漏，才可恢复。
