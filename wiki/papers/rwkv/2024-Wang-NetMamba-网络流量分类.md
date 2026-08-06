---
title: "NetMamba: Efficient Network Traffic Classification via Pre-training Unidirectional Mamba"
authors: [Tongze Wang, Xiaohui Xie, Wenduo Wang]
year: 2024
date: 2026-08-05
journal: "arXiv:2405.11449"
source_pdf: "[[raw/papers/rwkv/2024_Wang_NetMamba_网络流量分类.pdf]]"
tags: [Mamba, 网络流量, 加密流量, 类型/论文]
key_finding: "单向 Mamba 与经偏差控制的流量表征结合，在多个公开流量任务中进行了分类、效率与少样本评估。"
---

# NetMamba: Efficient Network Traffic Classification

## 论文原结论

论文把线性时间的单向 Mamba、流量表征、掩码自编码预训练和分类微调结合，在六个公开数据集、三类流量分类任务上评估，并报告分类、效率和少样本结果。

## 本课题推论

它为线性递归模型进入流量任务提供直接相邻证据，但不是 RWKV，也未验证 PINN、生成式恶意检测、当前数据合同或最终测试协议。

## 可迁移机制

流量字节/统计历史在进入模型前应作匿名化、偏差与泄漏审计；长序列与在线流式面板是检验线性递归相对 Transformer 的预注册困难域。

## 不可直接声称

不得把论文在其数据集上的数字、速度或少样本增益迁移为本课题结果。

## 文献信息

- arXiv: https://arxiv.org/abs/2405.11449
- Zotero：本轮导入超时，未建立条目。
