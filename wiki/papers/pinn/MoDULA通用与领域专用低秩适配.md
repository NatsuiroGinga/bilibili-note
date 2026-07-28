---
title: "MoDULA: Mixture of Domain-Specific and Universal LoRA for Multi-Task Learning"
authors:
  - Yufei Ma
  - Zihan Liang
  - Huangyu Dai
  - Ben Chen
  - Dehong Gao
  - Zhuoran Ran
  - Zihan Wang
  - Linbo Jin
  - Wen Jiang
  - Guannan Zhang
  - Xiaoyan Cai
  - Libin Yang
year: 2024
date: 2026-07-22
journal: "Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing"
source_pdf: "[[raw/papers/pinn/2024-Ma-MoDULA.pdf]]"
tags:
  - 类型/论文
  - 主题/低秩适配
  - 主题/通用专用分支
  - 主题/阶段式训练
key_finding: "MoDULA 分阶段训练通用 LoRA、领域专用 LoRA 和路由器，并冻结已学模块，说明新增任务可在不重训既有专家的情况下扩展；其残差混合仍不保证原任务输出不变。"
method: "通用 LoRA、领域专用 LoRA、残差组合、三阶段训练"
baseline: "LoRA、MoLoRA、多任务微调"
aliases:
  - MoDULA
  - Ma2024-MoDULA
---

# MoDULA 通用与领域专用低秩适配

> Yufei Ma 等，2024，EMNLP · PDF 13 页

## 一句话

MoDULA 的阶段式冻结比自由联合训练更接近当前修复，但其“通用 + 专用 + 路由”用于领域能力扩展，不等于双锚点与队列残差的物理私有监督。

## 方法核心

论文先训练通用专家，再分别训练领域专用专家，最后冻结全部专家、只训练路由器。MoDULA-Res 以残差方式连接通用与专用专家，目的是保留通用能力并提高训练稳定性。新增领域时可以训练新专家并更新路由，而不从头重训全部专家。

## 实验结果

论文在多种大语言模型和数学、代码、通用任务上比较 LoRA 与低秩专家方法。作者报告 MoDULA-Res 在多任务综合性能上更优，并称渐进训练可减少超过 80% 的训练成本；该比例依赖论文的多领域训练流程。

## 我的理解

当前修复可采用同样的阶段纪律：S3 已完成通用检测阶段并冻结，随后只训练物理私有 LoRA 和状态头。但家族路径不应再经过学习路由或残差混合，而应固定关闭私有分支。

## 局限与不可外推结论

- 领域专用通常按数据域或任务标签定义，容易造成来源捷径；本课题禁止按数据集或攻击标签定义物理专家。
- 残差连接只利于保留通用能力，不构成逐样本输出不变性证明。
- 超过 80% 的成本下降不能外推到单物理分支的 202 步实验。

## 与相关工作的关系

- [[AdapterFusion非破坏式任务适配器组合]] 同样冻结既有模块后学习组合。
- [[DeepSeekMoE细粒度共享专家架构]] 使用始终激活共享专家，MoDULA 使用通用低秩专家。

## 原始摘要

> 摘要要点经全文第 1 页和 ACL Anthology 页面核验：论文以通用、领域专用 LoRA 和分阶段路由训练提高多任务扩展效率。此处为中文转述。

## 文献信息

- ACL Anthology：[2024.emnlp-main.161](https://aclanthology.org/2024.emnlp-main.161/)
- 页码：2758-2770
