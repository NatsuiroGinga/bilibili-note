---
title: "Eagle and Finch: RWKV with Matrix-Valued States and Dynamic Recurrence"
authors: [Bo Peng, Daniel Goldstein, Quentin Anthony]
year: 2024
date: 2026-08-05
journal: "arXiv:2404.05892"
source_pdf: "[[raw/papers/rwkv/2024_Peng_Eagle_and_Finch_RWKV5_RWKV6.pdf]]"
tags: [RWKV, 线性递归, 类型/论文]
key_finding: "RWKV-5/6 以矩阵值状态和动态递归提高表达力，同时保留递归推理效率。"
---

# Eagle and Finch: RWKV with Matrix-Valued States and Dynamic Recurrence

## 论文原结论

论文提出 Eagle（RWKV-5）和 Finch（RWKV-6），并报告它们在语言建模与通用 NLP 基准中的结果。附录效率分析说明递归状态以随层和维度增长的有限状态保存，而不是 Transformer 的 KV 缓存。

## 本课题推论

矩阵值状态可作为研究长时流量状态编码的架构候选，但没有网络安全实验，不能称为加密流量检测有效。

## 可迁移机制

把连接级历史编码为递归状态，并将 PINN 的可微物理状态作为独立监督或门控输入，不能把隐藏状态本身冒充物理真值。

## 不可直接声称

不能把语言任务的性能、训练规模或上下文能力外推到 GeNIS、TQH-C2、ns-3 或 QUIC。

## 文献信息

- arXiv: https://arxiv.org/abs/2404.05892
- Zotero：`4B5F4H65`
