---
title: "Provable Multi-instance Deep AUC Maximization with Stochastic Pooling"
authors: [Dixian Zhu, Bokun Wang, Zhi Chen, Yaxing Wang, Milan Sonka, Xiaodong Wu, Tianbao Yang]
year: 2023
date: 2026-08-13
journal: "Proceedings of the 40th International Conference on Machine Learning（ICML 2023），PMLR 202:43205–43227"
source_pdf: "[[raw/papers/methodology/multiple-instance/2023-Zhu-MIDAM-Stochastic-Pooling-ICML.pdf]]"
sha256: "3b0b6d177057430dda190132bb5209b373e27c1ec625d94c674964360a657e87"
tags:
  - 多示例学习
  - 随机池化
  - AUC最大化
  - 类型/论文
key_finding: "指出把随机小包直接代入平滑最大或注意力池化会产生不可忽略的偏差，并提出逐包移动状态的方差降低随机池化与 MIDAM 收敛算法。"
method: "把平滑最大／注意力池化写成内层均值加非线性外层，逐包维护内层状态，再与深度 AUC 极小极大目标联合更新。"
baseline: "完整包 DAM、交叉熵下的均值／最大／平滑最大／注意力池化，以及多示例 AUC 方法"
aliases:
  - MIDAM
  - VRSP
  - Zhu2023-MIDAM
---

# MIDAM：大包多示例 AUC 的随机池化

> Zhu 等，2023，ICML · 23 个物理页 · Zotero `N3WQX553`

## 论文原结论

- 第 3 页公式（1）给出平滑最大池化，并同时列出均值池化与注意力池化；本文重点处理前两种非线性池化。
- 第 4 页说明直接在随机小包上计算平滑最大池化不是完整包池化的无偏估计，并会留下随小包大小控制但不可忽略的优化误差。
- 第 4—5 页把池化写成内层平均 `f1` 与非线性 `f2` 的复合，公式（7）—（8）按包维护移动状态；第 5 页算法 1给出统一 MIDAM。
- 第 6 页定理 1在有界、利普希茨、光滑及步长条件下给出驻点复杂度，并保证平均内层状态误差降至给定量级。

## 与本课题的关系

- **可迁移机制**：大实体随机抽流不能把“小包分数”自动称为“完整实体分数”；非线性池化需要状态跟踪或明确偏差界。
- **关键差异**：本课题拟排序的 `M_e=n_e^{-1}Σs^p` 本身是线性有限总体均值，因此固定分数下可无偏；但后续实体 AP 仍是非线性复合。MIDAM 优化 AUROC，且未使用实体均匀测度、Horvitz–Thompson 权重或 AP。
- **不可直接声称**：首次解决随机大包反向传播、首次提出随机池化、或“随机 K 流就等于完整实体训练”。
- **实验待证**：因果跨流编码下先抽流再重编码是否改变有限总体值；若改变，连 `M_e` 的无偏结论也不成立。

## 证据记录

- 全文：PMLR 正式 PDF，23 页；关键位置为物理第 3—6 页。
- 官方页：<https://proceedings.mlr.press/v202/zhu23l.html>
- 证据强度：直接占用大包随机池化与误差跟踪；不占用本课题完整两级实体 AP 设计。

