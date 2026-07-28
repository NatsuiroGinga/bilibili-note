---
title: "Parameter-efficient Multi-task Fine-tuning for Transformers via Shared Hypernetworks"
authors:
  - Rabeeh Karimi Mahabadi
  - Sebastian Ruder
  - Mostafa Dehghani
  - James Henderson
year: 2021
date: 2026-07-23
journal: "ACL-IJCNLP 2021"
source_pdf: "[[raw/papers/pinn/2021-KarimiMahabadi-HyperFormer.pdf]]"
tags:
  - 类型/论文
  - 主题/超网络
  - 主题/适配器
  - 主题/多任务学习
key_finding: "HyperFormer++ 用跨任务与跨层共享的超网络按任务、层和适配器位置生成参数，在 T5-Base 上每任务仅训练 0.29% 参数并取得多任务增益；其条件是离散任务标识而非逐样本物理状态。"
method: "共享超网络、条件适配器、条件层归一化、任务与层嵌入"
baseline: "全量多任务微调、独立适配器、非共享 HyperFormer"
aliases:
  - HyperFormer++
  - KarimiMahabadi2021-HyperFormer
---

# HyperFormer 共享超网络适配器

## 一句话

论文证明超网络可以按条件生成层级适配参数并减少任务间干扰，但没有样本级动态参数、物理状态或恒等保护机制。

## 方法核心

PDF 第 3 页公式（6）以任务嵌入 $I_\tau$ 生成第 $l$ 层适配器参数：

$$
(U_\tau^l,D_\tau^l)=h_A^l(I_\tau).
$$

HyperFormer++ 进一步把超网络跨层共享，并把任务、层编号和适配器位置嵌入组合成条件输入。

## 全文证据

- PDF 第 2 至 4 页给出超网络、适配器和条件层归一化结构。
- PDF 第 5 页表 1 中，T5-Base 的 HyperFormer++ 多任务平均分为 `86.48`，高于同表全量多任务微调的 `85.47`，每任务训练参数为 `0.29%`。
- PDF 第 7 至 8 页给出少样本域迁移实验，说明共享超网络可向相关任务转移，但并非所有数据点都优于独立适配器。

## 对本课题的可迁移机制

可把离散任务嵌入替换为物理状态编码，并只生成固定低秩基底的缩放向量，避免为每个样本生成完整 LoRA 矩阵。这样形成样本条件化动态适配，而不是 D3 的全样本静态私有 LoRA。

## 不可直接声称

- 论文按任务生成参数，不能证明逐样本物理条件稳定。
- 它没有零初始化恒等旁路，也不保证未知攻击召回和校准。
- T5 编码器解码器结果不能直接外推到量化 Qwen 解码器。

## 文献信息

- DOI：[10.18653/v1/2021.acl-long.47](https://doi.org/10.18653/v1/2021.acl-long.47)
- ACL Anthology：[2021.acl-long.47](https://aclanthology.org/2021.acl-long.47/)
