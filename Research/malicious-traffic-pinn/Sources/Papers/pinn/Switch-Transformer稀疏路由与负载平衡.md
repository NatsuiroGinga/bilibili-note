---
title: "Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity"
authors:
  - William Fedus
  - Barret Zoph
  - Noam Shazeer
year: 2022
date: 2026-07-22
journal: "Journal of Machine Learning Research"
source_pdf: "[[raw/papers/pinn/2022-Fedus-Switch-Transformer.pdf]]"
tags:
  - 类型/论文
  - 主题/混合专家
  - 主题/Top-1路由
  - 主题/训练稳定性
key_finding: "Switch 将每个词元只路由到一个专家以简化稀疏模型，但容量因子、丢词元、负载均衡和低精度稳定性仍需专门处理。"
method: "Top-1 路由、容量因子、辅助负载均衡、选择性精度"
baseline: "T5、稀疏门控混合专家、mT5"
aliases:
  - Switch Transformer
  - Fedus2022-Switch
---

# Switch Transformer 稀疏路由与负载平衡

> William Fedus、Barret Zoph、Noam Shazeer，2022，JMLR · PDF 39 页

## 一句话

Switch 证明稀疏激活可扩大容量并降低每词元计算，但也系统展示了动态路由需要容量、均衡和数值稳定措施；这不是小数据物理专家的免费增益。

## 方法核心

每个词元只选择概率最高的一个专家。专家容量定义为

$$
\text{capacity}=\frac{\text{batch tokens}}{\text{experts}}\times\text{capacity factor}.
$$

路由过于集中时，超过容量的词元会绕过专家；提高容量因子能减少溢出，但增加计算和通信。论文还使用辅助负载均衡、缩小初始化和路由局部高精度计算提高稳定性。

## 实验结果

基于 T5-Base/T5-Large 的模型在相同资源下最高获得约 7 倍预训练速度提升；超大设置相对 T5-XXL 报告约 4 倍速度提升，并覆盖 101 种语言。论文还讨论将稀疏教师蒸馏为小型密集模型的质量损失。

## 我的理解

本课题数据量和参数规模远小于 Switch 的预训练场景。当前单私有适配器无需路由。多专家备选若启用，必须记录专家占比、溢出、路由熵和坍缩，而不能只报告最终 F1。

## 局限与不可外推结论

- 速度来自大规模分布式预训练，不能外推到单卡 LoRA。
- Top-1 可能丢弃专家计算，物理残差样本不能无记录地绕过私有分支。
- 均衡专家不等于物理语义正确。

## 原始摘要

> 摘要要点经全文第 1 页核验：论文用 Top-1 路由简化混合专家，并以稳定训练技巧扩展到万亿参数。此处为中文转述。

## 文献信息

- JMLR：[第 23 卷第 120 篇](https://www.jmlr.org/papers/v23/21-0998.html)
