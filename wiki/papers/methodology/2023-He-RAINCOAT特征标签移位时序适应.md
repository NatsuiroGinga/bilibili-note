---
title: "Domain Adaptation for Time Series Under Feature and Label Shifts"
authors: [Huan He, Owen Queen, Teddy Koker, Consuelo Cuevas, Theodoros Tsiligkaridis, Marinka Zitnik]
year: 2023
date: 2026-08-12
journal: "ICML 2023，PMLR 202"
source_pdf: "[[raw/papers/methodology/2023-He-RAINCOAT-Time-Series-Domain-Adaptation.pdf]]"
zotero_key: RVX6ZR6X
zotero_key: RVX6ZR6X
tags: [时间序列, 无监督域适应, 标签移位, 最优传输, 类型/论文]
key_finding: "RAINCOAT 已覆盖时间—频率表示、Sinkhorn 对齐与目标私有类纠正的两阶段组合；普通时频适应不能作为本课题原创。"
method: "时间—频率编码、Sinkhorn 散度、先对齐后纠正"
baseline: "AdaTime 域适应基线与组件消融"
aliases: [RAINCOAT, He2023-RAINCOAT]
related: ["[[mims-harvard-Raincoat官方源码]]", "[[2024-Liu-ACON时频互学习域适应]]"]
---

# RAINCOAT：特征与标签移位下的时序适应

## 论文原结论

论文针对源有标签、目标无标签的时间序列域适应，同时考虑动态特征变化和类别集合变化。正文第 5.1—5.6 节以时间编码和频率编码组成联合表示，以公式（6）的 Sinkhorn 散度进行对齐，再根据目标样本对源原型的对齐前后位移执行纠正；算法 1 给出两阶段流程，表 2 分离频率编码、Sinkhorn 和纠正步骤。

## 可迁移机制

- 部分或拒绝传输可避免目标私有支持被强制搬到源原型。
- 对齐前后原型距离变化可作为支持错配诊断，而非直接当作性能证明。
- 时间—频率特征必须由真实数据证明适用，不能因传感器任务有效就迁入表格流量。

## 本课题推论

LSPR23/24 的二分类标签名相同不代表攻击族支持相同。若采用传输，应在 XGBoost 叶/分数空间加入源恶意质量下限、局部支持拒绝与目标前缀门禁。该推论尚属实验待证。

## 不可直接声称

论文使用完整目标数据离线适应，未研究低基率攻击污染、因果前缀或固定告警预算；不能据此声称 RAINCOAT 或其改造会提高本任务 PR-AUC。

## 待验证

1. 叶表示中的攻击支持是否比良性漂移更远。
2. 频域特征在当前 77 个工程字段上是否有独立信号；候选 B 的负结果使该方向暂缓。

## 文献信息

- PMLR：https://proceedings.mlr.press/v202/he23b.html
- arXiv：2302.03133
