---
title: "Flamingo: a Visual Language Model for Few-Shot Learning"
authors:
  - Jean-Baptiste Alayrac
  - Jeff Donahue
  - Pauline Luc
  - Antoine Miech
  - Iain Barr
  - Yana Hasson
  - Karel Lenc
  - Arthur Mensch
  - Katie Millican
  - Malcolm Reynolds
  - Roman Ring
  - Eliza Rutherford
  - Serkan Cabi
  - Tengda Han
  - Zhitao Gong
  - Sina Samangooei
  - Marianne Monteiro
  - Jacob Menick
  - Sebastian Borgeaud
  - Andrew Brock
  - Aida Nematzadeh
  - Sahand Sharifzadeh
  - Mikolaj Binkowski
  - Ricardo Barreira
  - Oriol Vinyals
  - Andrew Zisserman
  - Karen Simonyan
year: 2022
date: 2026-07-23
journal: "arXiv 预印本"
source_pdf: "[[raw/papers/pinn/2022-Alayrac-Flamingo.pdf]]"
tags:
  - 类型/论文
  - 主题/条件生成
  - 主题/交叉注意力
  - 主题/恒等旁路
key_finding: "Flamingo 在冻结语言模型层之间插入零初始化双曲正切门控的交叉注意力残差块，使条件模型在初始化时严格复现原语言模型；移除该门控会使综合得分下降 4.2% 并出现训练不稳定。"
method: "冻结语言模型、条件交叉注意力、零初始化双曲正切门控、残差旁路"
baseline: "无零初始化门控、普通交叉注意力、后置融合"
aliases:
  - Flamingo
  - Alayrac2022-Flamingo
---

# Flamingo 零初始化门控交叉注意力

## 一句话

这篇论文提供了当前最直接的结构先例：冻结原生成模型，通过带恒等旁路的条件交叉注意力逐步注入新增信息，而不是让新增条件从第一步起覆盖原有表征。

## 论文原方法

Flamingo 把视觉表示作为键和值，把语言隐状态作为查询，在冻结语言模型层之间插入可训练的交叉注意力与前馈块。PDF 第 5 页图 4 和伪代码给出的核心更新为：

$$
y' = y + \tanh(\alpha_{\mathrm{xattn}})\operatorname{Attn}(Q=y,K=V=x),
$$

随后再以同类门控接入新增前馈块。每层门控参数从 $0$ 初始化，因此初始时 $\tanh(\alpha)=0$，条件模型输出与冻结语言模型一致。

## 全文证据

- PDF 第 5 页明确说明冻结原语言模型，只训练新增条件块；零初始化门控使初始输出与原模型相同。
- PDF 第 9 页消融显示，移除零初始化双曲正切门控后综合得分下降 `4.2%`，并出现训练不稳定。
- 论文还比较交叉注意力插入频率，说明条件块位置影响表达能力与计算成本，不能默认“越多越好”。

## 对本课题的可迁移机制

可把五个预测队列锚点与有限队列残差编码为少量物理条件词元，以检测隐状态为查询做受限交叉注意力。与已失败的直接门控投影不同，每个生成词元可以按查询选择不同物理锚点，原检测表示仍有显式恒等旁路。

本课题仍需自主增加相对隐藏状态范数的残差上界，才能把“初始化等价”扩展为可分析的训练期扰动界。该上界不是 Flamingo 的原结论。

## 不可直接声称

- 零初始化只保证训练开始时等价，不保证训练结束后检测指标不下降。
- 论文处理视觉条件和大规模多模态预训练，没有恶意流量、开放集召回、校准或物理残差实验。
- 论文中的 `4.2%` 是其多模态综合得分变化，不能作为本课题预期提升。

## 待验证假设

多物理词元交叉注意力比单向量加法投影更具选择性；在冻结检测主干、零初始化门控和残差范数上界同时存在时，物理梯度可能降低对开放集边界的覆盖。

## 文献信息

- arXiv：[2204.14198](https://arxiv.org/abs/2204.14198)
