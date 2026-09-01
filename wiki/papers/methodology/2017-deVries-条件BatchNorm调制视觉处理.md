---
title: "Modulating early visual processing by language"
authors: [Harm de Vries, Florian Strub, Jérémie Mary, Hugo Larochelle, Olivier Pietquin, Aaron Courville]
year: 2017
date: 2026-09-01
journal: "NeurIPS 2017；本地原件为 arXiv:1707.00683"
source_pdf: "[[raw/papers/methodology/2017-deVries-Conditional-BatchNorm-Modulating-Visual.pdf]]"
sha256: "ee492d4707843b09208e77b7b58bc256e50af186d961686935f762e948bcc774"
arxiv_id: "1707.00683"
tags:
  - 条件归一化
  - 条件化
  - 类型/论文
key_finding: "条件 BatchNorm（CBN）用单隐层 MLP 从条件嵌入 e_q 预测归一化仿射参数的增量（物理第 4 页式 4–5：Δβ=MLP(e_q)、Δγ=MLP(e_q)，β̂=β+Δβ、γ̂=γ+Δγ），冻结主干、只学增量，从零均值小方差初始化保证起点等价于原模型。"
method: "在预训练 ResNet 的 BatchNorm 上按语言条件预测 (Δγ, Δβ)，调制早期视觉特征"
aliases:
  - CBN
  - 条件BatchNorm
  - deVries2017-CBN
related:
  - "[[2018-Perez-FiLM通用条件化层]]"
---

# 条件 BatchNorm：小 MLP 从条件向量出仿射增量

> de Vries, Strub, Mary, Larochelle, Pietquin, Courville，NeurIPS 2017。

## 全文证据（物理页码）

- 第 4 页式 (4)：`Δβ = MLP(e_q)`，`Δγ = MLP(e_q)`；式 (5)：`β̂_c = β_c + Δβ_c`，`γ̂_c = γ_c + Δγ_c`。
- 同页设计动机：预测**增量**而非绝对值，使零初始化时模型与原网络严格一致——「条件缺失/初始时刻退化为基线」这一构造在 2017 年已发表。

## 与本课题的关系

M-E 的「小 MLP 从 2 维实体统计出门控」与 CBN 的「单隐层 MLP 从条件嵌入出仿射增量」同构；M-E 的零门退化设计与 CBN 的零初始化等价起点设计属于同一工程约定。进一步削弱 M-E 把零门退化作为理论贡献的空间。

## 边界

- 视觉+语言域，BatchNorm 挂载点；无漂移、无表格。仅作算子谱系证据。
