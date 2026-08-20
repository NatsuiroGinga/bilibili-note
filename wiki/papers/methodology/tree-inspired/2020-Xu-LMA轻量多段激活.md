---
title: "Light Multi-segment Activation for Model Compression"
authors: [Zhenhui Xu, Guolin Ke, Jia Zhang, Jiang Bian, Tie-Yan Liu]
year: 2020
date: 2026-08-20
journal: "Proceedings of the AAAI Conference on Artificial Intelligence"
source_pdf: "[[raw/papers/methodology/tree-inspired/2019-Ke-DeepGBM.pdf]]"
arxiv: "1907.06870"
sha256: "af4bf76f588d7babd5cb5ce9153f01608774ab39049b0e6b987770d8c7b1696a"
zotero_item_key: "XS9LTRKE"
tags: [模型压缩, 多段激活, 知识蒸馏, 类型/论文]
aliases: [LMA, Light Multi-segment Activation]
key_finding: "该文以统计驱动的轻量多段激活提升压缩学生网络的分段线性表达能力，与 DeepGBM 无关；本次因错误 arXiv 映射误下载后按原件不可变规则保留，不进入表格骨干候选。"
---

# LMA：轻量多段激活

## 保留原因

检索结果错误地把 arXiv:1907.06870 映射为 DeepGBM，下载后逐页核验发现实际题名为本论文。`raw/` 原件不可删除或改名，因此保留原文件、记录真实题录并另行下载正确 DeepGBM 原件。

## 论文内容与边界

- LMA 用多个分段线性区域替代 ReLU，在知识蒸馏的压缩学生中提高表达能力，同时控制附加参数（物理页 1 至 4）。
- 实验面向图像分类与机器翻译，不含表格数据、树模型、实体聚合或网络攻击检测。
- 该论文不进入本次候选、证据矩阵或最小实验，仅作为错误下载处置收据。
