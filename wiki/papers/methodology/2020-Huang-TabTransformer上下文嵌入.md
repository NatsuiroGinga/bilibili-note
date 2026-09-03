---
title: "TabTransformer: Tabular Data Modeling Using Contextual Embeddings"
authors: [Xin Huang, Ashish Khetan, Milan Cvitkovic, Zohar Karnin]
year: 2020
date: 2026-09-03
journal: "arXiv:2012.06678v1（Amazon AWS / PostEra，2020-12-15）"
source_pdf: "[[raw/papers/methodology/2020-Huang-TabTransformer-Contextual-Embeddings.pdf]]"
sha256: "cac9f73e400c2bf724c3b29d5c7c5648df411bdf79d6cb6cc4c01d4a9d1afb1e"
tags:
  - 表格数据
  - Transformer
  - 上下文嵌入
  - 半监督预训练
  - 训练协议
  - 类型/论文
key_finding: "TabTransformer 早于 FT-Transformer（2020 vs 2021），架构不同（仅类别特征过 Transformer，数值特征直接拼接，非逐字段数值 Token），但训练协议独立采用同一惯例：AdamW、全程常数学习率、早停耐心 15 个 epoch（物理页 10，附录 B.1），与 Gorishniy 2021 的选择相互印证而非因果关联。"
method: "类别特征经嵌入层后过 Transformer 编码得到上下文相关嵌入，与数值特征归一化后的向量拼接，共同输入 MLP 分类头；另设 RTD（替换词检测）与 MLM 两种半监督预训练目标"
baseline: "MLP、TabNet、VIB、稀疏 MLP（剪枝）、GBDT（LightGBM）"
aliases:
  - TabTransformer
  - Huang2020-TabTransformer
related:
  - "[[2021-Gorishniy-表格数据深度学习模型再审视]]"
  - "[[2023-Zhu-XTab跨表预训练]]"
---

# TabTransformer：基于上下文嵌入的表格数据建模

> Huang、Khetan、Cvitkovic、Karnin，arXiv:2012.06678v1，2020-12-15，物理页 1 至 17。

## 一句话

**本文架构与 FT-Transformer 不同**——只有类别特征经过 Transformer 层产生"上下文嵌入"，数值特征在归一化后直接与 Transformer 输出拼接送入 MLP，不是 FT-Transformer 那种"每个数值/类别特征各自一个 Token"的逐字段方案（第 2 节，物理页 2-3）；本文严格意义上**不是 FT-Transformer 的下游使用者**，而是同期、同问题域的独立架构。收录理由是核查"常数学习率是否为该研究谱系的共同惯例"，本文提供一个架构无关的独立数据点。

## 训练协议（本次核查重点，逐句带页码）

物理页 10，附录 B.1"Experiments Details and Hyper Parameters"：

> "As all the datasets are for binary classification, the cross entropy loss was used for both supervised and semi-supervised training... For all deep models, the AdamW optimizer (Loshchilov and Hutter 2017) was used to update the model parameters, **and a constant learning rate was applied throughout each training job**. All models used early stopping based on the performance on the validation set and the early stopping patience (the number of epochs) is set as 15."

即：AdamW、**全程常数学习率**（原文明确使用"constant"一词，非"不讨论调度器"式的省略）、早停耐心 15 epoch，对全部深度模型（含 TabTransformer 本身及各基线）统一适用。

同页续段给出调参搜索空间（未特别注明具体页内小节号，紧接引用段落之后）：学习率搜索空间 `{10^u, u∈U[-6,-3]}`，权重衰减 `{10^u, u∈U[-6,-1]}`——即学习率候选范围粗略为 `[1e-6, 1e-3]`，与 Gorishniy 2021 Table 13 的 `[1e-5,1e-3]`（group A）量级相近但下界更宽两个数量级，二者是独立设定，不构成同一调参协议。

## 训练不稳定性：未见报告

全文未检索到 instab/oscillat/diverg/unstable/schedul 等关键词的实质性讨论段落（仅优化器引用 Loshchilov and Hutter 2017 一处涉及"decay"，指 AdamW 本身的 decoupled weight decay，非学习率调度）。

## 证据等级

- 原件级别：完整论文，17 个物理页，MinerU flash-extract 全文转换 + 单页核验定位精确页码（物理页 10）。
- 可支撑："常数学习率 + AdamW + 早停"是本文（先于 FT-Transformer 一年、架构独立）采用的训练惯例，与 Gorishniy 2021 的选择相互印证但无引用关系（本文早于 FT-Transformer 发表，不可能引用后者）。
- 不可支撑：本文不能作为"使用 FT-Transformer 作骨干"的直接证据——架构不同，仅供训练协议惯例的旁证。
