---
title: "Towards Reliable Model Selection for Unsupervised Domain Adaptation: An Empirical Study and A Certified Baseline"
authors: [Dapeng Hu, Mi Luo, Jian Liang, Chuan-Sheng Foo]
year: 2024
date: 2026-08-12
journal: "NeurIPS 2024 数据集与基准赛道"
source_pdf: "[[raw/papers/methodology/2024-Hu-EnsV-Reliable-UDA-Model-Selection.pdf]]"
zotero_key: AR53AZ34
zotero_key: AR53AZ34
tags: [无监督域适应, 无标签选模, 负迁移, 集成, 类型/论文]
key_finding: "EnsV 以无标签目标预测集成选择候选，并只保证负对数似然集成优于最差成员；多数类共识可能掩盖稀有恶意排序退化。"
method: "目标预测集成角色模型与预测相似度选择"
baseline: "八种无监督验证方法、十二种域适应方法"
aliases: [EnsV, Hu2024-EnsV]
related: ["[[LHXXHB-EnsV官方源码]]", "[[2024-Yang-无标签迁移分数]]"]
---

# EnsV：无标签域适应选模

## 论文原结论

论文命题在负对数似然、成员预测映射不完全相同的条件下，由 Jensen 不等式推出预测集成损失小于成员平均损失，因而小于最差成员。EnsV 以候选模型在目标样本上的预测集成为角色模型，选择目标预测最相似的候选，不使用目标标签、源数据或额外训练。

## 可迁移机制

把共同 XGBoost 强锚纳入候选池，EnsV 相似度可作为停机/回滚的一项观测；计算只依赖已有目标前缀预测矩阵。

## 本课题推论

低基率二分类中，多个模型对良性的共识会支配距离。门禁必须联合源恶意排序保持、传输未匹配质量、目标前缀扰动稳定性与预测率包络。

## 不可直接声称

理论不保证所选候选优于 XGBoost、改善 PR-AUC 或接近最佳成员。正文还列出集成本身次优、好模型被多个坏模型淹没、成员过于相似和候选池差模型占多数等失败条件。

## 待验证

在预注册的无害/有害适应网格中，门禁需用锁定后的目标标签侧车评价回滚检出率与误拒率；标签不能反向参与选择。

## 补充材料

补充 PDF：`raw/papers/methodology/2024-Hu-EnsV-Reliable-UDA-Model-Selection-Supplement.pdf`，与正文合计只计一篇论文。

## 文献信息

- NeurIPS：https://papers.nips.cc/paper_files/paper/2024/hash/f50cebc22663df45ce619645bfabb3b3-Abstract-Datasets_and_Benchmarks_Track.html
- DOI：10.52202/079017-4316
