---
title: "Prototype-based HyperAdapter for Sample-Efficient Multi-task Tuning"
authors:
  - Hao Zhao
  - Jie Fu
  - Zhaofeng He
year: 2023
date: 2026-07-23
journal: "Conference on Empirical Methods in Natural Language Processing"
source_pdf: "[[raw/papers/pinn/2023-Zhao-Prototype-HyperAdapter.pdf]]"
tags:
  - 类型/论文
  - 主题/超网络
  - 主题/原型表示
  - 主题/少样本适配
key_finding: "原型 HyperAdapter 用实例检索器形成任务原型，再由共享超网络生成适配器；消融证明原型与检索器均有贡献，但生成单位仍是任务模块，不是逐样本物理控制。"
method: "实例密集检索器、任务原型、共享超网络、适配器生成"
baseline: "Adapter、HyperFormer++、HyperDecoder、全量微调"
aliases:
  - PHA
  - Zhao2023-PrototypeHyperAdapter
---

# 原型 HyperAdapter 样本高效条件适配

## 一句话

论文说明实例集合可以先压缩为稳定原型，再驱动超网络生成适配器；这比直接从单个噪声样本生成完整权重更稳，但仍依赖任务簇可分。

## 方法核心

PDF 第 2 至 4 页先用实例密集检索器把同任务样本聚集，再形成任务原型 $k_i$，由超网络生成模块参数：

$$
\phi=h_w(I).
$$

新任务通过检索与已有原型的相似度构造条件表示，而不是直接为每个输入重新训练适配器。

## 全文证据

- PDF 第 1 页图 1 和第 3 至 4 页给出检索、原型与超网络计算图。
- PDF 第 2 页称在每任务仅 100 个 GLUE 样本时相对普通适配器提高 `8.0%`；该口径只属于其多任务协议。
- PDF 第 7 页表 3 中，同时使用原型和检索器的 GLUE 分数为 `85.5`，去掉两者为 `84.0`；分别移除也会下降。
- 论文可视化显示检索器使任务簇更分离，但没有证明簇对应物理状态。

## 对本课题的可迁移机制

如果物理状态条件化超网络成为后续备选，可先把多窗口状态编码映射到少量连续原型，再生成低秩缩放系数，避免逐样本完整权重抖动。

## 不可直接声称

- 任务原型不等于队列状态原型；按攻击标签或数据集来源聚类会产生捷径。
- 任务十七已经证明公开五字段对状态的辨识效应很弱，不能假设原型检索自然可靠。
- 本文没有恒等旁路、物理残差、生成式开放集检测或校准实验。

## 文献信息

- DOI：[10.18653/v1/2023.emnlp-main.280](https://doi.org/10.18653/v1/2023.emnlp-main.280)
- ACL Anthology：[2023.emnlp-main.280](https://aclanthology.org/2023.emnlp-main.280/)
