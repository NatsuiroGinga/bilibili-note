---
title: "PROTOCOL: Partial Optimal Transport-enhanced Contrastive Learning for Imbalanced Multi-view Clustering"
authors: [Xuqian Xue, Yiming Lei, Qi Cai, Hongming Shan, Junping Zhang]
year: 2025
date: 2026-08-12
journal: "ICML 2025，PMLR 267"
source_pdf: "[[raw/papers/methodology/2025-Xue-PROTOCOL-Imbalanced-Partial-Optimal-Transport.pdf]]"
zotero_key: GL8RQF4U
zotero_key: GL8RQF4U
tags: [部分最优传输, 类别不平衡, 无监督聚类, 少数类, 类型/论文]
key_finding: "PROTOCOL 已将渐进部分质量、非平衡类别边缘和尾类再平衡组合，故质量约束或少数类再平衡本身不构成本课题原创。"
method: "渐进 POT 自标注、虚拟簇、两级类别再平衡对比学习"
baseline: "九种多视图聚类方法与 Base/POT/POT+CLR 消融"
aliases: [PROTOCOL, Xue2025-PROTOCOL]
related: ["[[Scarlett125-PROTOCOL官方源码]]", "[[2025-Chen-BUOT双层非平衡传输]]"]
---

# PROTOCOL：不平衡聚类中的渐进部分传输

## 论文原结论

公式（15）以预测负对数代价、类别边缘加权 KL 和总质量构造 POT 自标注；公式（16）用 S 形日程逐渐增加传输质量，虚拟簇吸收未分配质量，公式（17）—（18）及附录算法 2 给出缩放求解。第二机制以 POT 伪标签驱动特征级对数几率调整和类别级类别敏感对比学习。表 5 分离 Base、POT 和 POT+CLR。

## 可迁移机制

虚拟拒绝质量和头/中/尾类分面是可复用诊断；但渐进质量按训练进度增加，不等于由跨年支持证据决定。

## 本课题推论

候选一的独立性必须落在：源恶意真标签质量下限、源/目标非对称支持拒绝、固定 XGBoost 强排序锚和目标前缀无标签停机，而非宽泛的渐进 POT 或少数类再平衡。

## 不可直接声称

论文研究单数据集多视图无监督聚类，没有源—目标域、攻击污染、目标前缀因果性或 PR-AUC。完整网络还需要多阶段长训练，不能证明树叶空间的轻量传输有效。

## 待验证

新增硬消融：普通 POT、渐进 POT、恶意质量保护的非对称 POT、后者加停机；渐进 POT 若已达到同等增益，恶意质量保护未获支持。

## 文献信息

- PMLR：https://proceedings.mlr.press/v267/xue25c.html
- arXiv：2506.12408
