---
title: "DI-NIDS: Domain Invariant Network Intrusion Detection System"
authors: [Siamak Layeghy, Mahsa Baktashmotlagh, Marius Portmann]
year: 2023
date: 2026-08-12
journal: "Knowledge-Based Systems 273"
source_pdf: "[[raw/papers/attack-detection/2022-Layeghy-DI-NIDS-Domain-Invariant.pdf]]"
zotero_key: UCJ2SKNL
zotero_key: UCJ2SKNL
tags: [网络入侵检测, 域适应, 域对抗, 一类分类, 类型/论文]
key_finding: "DI-NIDS 以 DANN 表示接一类支持向量机，跨数据集方向结果高度非对称，说明域不可分不等于恶意排序保留。"
method: "DANN 域不变表示与一类支持向量机"
baseline: "跨 NFv2-CIC-2018 与 NFv2-UNSW-NB15 双向检测"
aliases: [DI-NIDS, Layeghy2023-DINIDS]
---

# DI-NIDS：跨域网络入侵检测

## 论文原结论

第 3 节先用有标签源域和无标签目标域训练 DANN，再在域不变表示上训练一类支持向量机；公式（6）为源分类与域判别的对抗目标，公式（9）为一类支持向量机。表 5、6 的双向跨数据集结果高度不对称，普通 DANN 在两个方向分别为 17.31% 和 61.94% F1。

## 可迁移机制

DANN 加一类检测可列为安全领域强基线；域判别准确率只能作为表示漂移观测，必须同时监测源恶意排序方向和目标预算告警结构。

## 本课题推论

普通 DANN/CORAL/MMD 不能作为原创。类条件错配、支持不重叠和恶意低基率会让边缘域对齐压掉关键排序信号。

## 不可直接声称

论文使用完整目标数据而非严格前缀，只报告 F1，不报告 PR-AUC、固定预算召回或校准，也没有污染门和负迁移回滚。

## 待验证

把普通 DANN 与 XGBoost 强锚、普通 OT 和第一候选在相同预算下比较；不得削弱树基线。

## 文献信息

- DOI：10.1016/j.knosys.2023.110626
- arXiv：2210.08252
