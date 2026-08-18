---
title: "Boosting Transferability and Discriminability for Time Series Domain Adaptation"
authors: [Mingyang Liu, Xinyang Chen, Yang Shu, Xiucheng Li, Weili Guan, Liqiang Nie]
year: 2024
date: 2026-08-12
journal: "NeurIPS 2024"
source_pdf: "[[raw/papers/methodology/2024-Liu-ACON-Time-Series-Domain-Adaptation.pdf]]"
zotero_key: 7JVIMR49
zotero_key: 7JVIMR49
tags: [时间序列, 无监督域适应, 时频表示, 域对抗, 类型/论文]
key_finding: "ACON 已覆盖多周期频率表示、时频双向互学习和相关子空间域对抗，压缩了通用时频迁移的原创空间。"
method: "多周期频率编码、双向知识蒸馏、时频相关子空间对抗"
baseline: "八个时序数据集的域适应基线与逐组件消融"
aliases: [ACON, Liu2024-ACON]
related: ["[[iLearn-Lab-ACON官方源码]]", "[[2023-He-RAINCOAT特征标签移位时序适应]]"]
---

# ACON：时频互学习域适应

## 论文原结论

第 4.1 节学习多周期频率特征；第 4.2 节以双向蒸馏增强源时间特征判别性和目标频率特征可迁移性；第 4.3 节在时间—频率外积相关子空间进行域对抗。表 4 和表 9 给出逐组件消融。作者同时报告大方差序列上的稳定性限制。

## 可迁移机制

域对抗可以作用于结构化相关子空间，而非原始表示；但是域不可分不等于恶意排序被保存，仍需类敏感排序诊断。

## 本课题推论

当前 XGBoost PR-AUC `0.03890259`，而所有小型序列模型最高不超过 `0.01920596`。因此不应先以完整 ACON 替换强树排序器；时频分支只在后续真实可观测量支持时重新考虑。

## 不可直接声称

普通域对抗、时频编码和互学习均已有先例；论文未处理目标攻击污染、标签先验变化、无标签选模或固定预算召回，不能证明本任务有效。

## 待验证

目标前缀上的频率特征是否比时间字段更稳定，以及这种稳定是否保留源恶意—困难良性相对次序。

## 文献信息

- NeurIPS：https://proceedings.neurips.cc/paper_files/paper/2024/hash/b61da4f02b271cb7b5e3d538e2b78fb9-Abstract-Conference.html
- DOI：10.52202/079017-3187
