---
title: "AdapterFusion: Non-Destructive Task Composition for Transfer Learning"
authors:
  - Jonas Pfeiffer
  - Aishwarya Kamath
  - Andreas Rücklé
  - Kyunghyun Cho
  - Iryna Gurevych
year: 2021
date: 2026-07-22
journal: "Proceedings of the 16th Conference of the European Chapter of the Association for Computational Linguistics"
source_pdf: "[[raw/papers/pinn/2021-Pfeiffer-AdapterFusion.pdf]]"
tags:
  - 类型/论文
  - 主题/适配器
  - 主题/任务组合
  - 主题/参数冻结
key_finding: "AdapterFusion 先独立训练并冻结任务适配器，再学习目标任务的融合层，支持非破坏式复用已有能力；但学习型融合并不自动保证未选分支输出不变。"
method: "两阶段任务适配器训练、查询键值融合、冻结源适配器"
baseline: "全量微调、单任务适配器、多任务适配器"
aliases:
  - AdapterFusion
  - Pfeiffer2021-AdapterFusion
---

# AdapterFusion 非破坏式任务适配器组合

> Jonas Pfeiffer 等，2021，EACL · PDF 17 页

## 一句话

论文最直接支持“先冻结已验证检测适配器，再单独训练组合或私有参数”，但本课题要获得家族不变性，还必须让家族计算图完全绕过新增融合层。

## 背景

顺序微调会遗忘旧任务，多任务联合训练又依赖数据采样与任务平衡。AdapterFusion 将“知识提取”和“知识组合”拆成两个阶段，避免为了新目标重新修改所有源任务参数。

## 方法核心

第一阶段分别训练每个任务适配器，预训练模型保持冻结。第二阶段冻结预训练模型和所有已训练适配器，只为目标任务训练融合层。每一 Transformer 层以当前隐藏状态构造查询，以各适配器输出构造键和值，并用注意力权重组合。

因此，“非破坏式”具体指源适配器参数不被覆盖，而不是任意目标任务输出都与未加融合前逐位相同。

## 实验结果

- 实验覆盖 16 个自然语言理解任务。
- 单任务适配器相对全量微调平均提高 0.66%，显示小型适配器也可能有正则化作用。
- 以单任务适配器为源时，AdapterFusion 对 15/16 个任务保持或改善，其中 10/16 明确改善；相对多任务适配器，11/16 改善。
- 小数据任务收益更明显，例如 RTE 和 MRPC 分别提高约 6.5% 与 5.64%；总体平均改善约 1.27%。

## 我的理解

该论文给当前修复提供了清楚的训练纪律：S3 检测 LoRA 是已经提取出的稳定知识，应被冻结；物理私有 LoRA 和状态头属于第二阶段新增参数。与 AdapterFusion 不同，当前修复不需要对家族任务学习融合权重，而应固定 $g_F=0$。

子类和开放集可以读取 $h_{S3}+g_t\Delta h_{phy}$，但未知攻击标签仍只能用于评估。新增分支由已知子类监督、双锚点状态监督和队列残差训练。

## 局限与不可外推结论

- 论文是 BERT 编码器分类，不是自回归生成和量化 LoRA。
- 冻结源适配器只保证其参数未变，不保证加入融合层后的最终预测不变。
- 论文没有物理残差、状态头或开放集标签纪律。
- 多源融合的收益不能替代同参数预算单私有适配器对照。

## 与相关工作的关系

- 与 [[MoLE分层低秩专家组合]] 一样组合已训练模块，但 AdapterFusion 使用适配器输出注意力，MoLE 使用逐层 LoRA 门控。
- 与 [[MoDULA通用与领域专用低秩适配]] 一样强调阶段式训练和冻结。
- 与 [[Domain Separation Networks共享私有域分解]] 相比，它直接把多个适配器输出送入目标表示。

## 疑问与待验证

- 在当前实现中，家族路径是否绕过了新增状态头、私有 LoRA、融合和任何共享归一化统计？

## 原始摘要

> 摘要要点经全文第 1 页核验：论文分离任务知识提取与组合，以冻结适配器和单独融合层缓解遗忘及多任务数据平衡问题。此处为中文转述。

## 文献信息

- DOI：[10.18653/v1/2021.eacl-main.39](https://doi.org/10.18653/v1/2021.eacl-main.39)
- ACL Anthology：[2021.eacl-main.39](https://aclanthology.org/2021.eacl-main.39/)
- arXiv：[2005.00247](https://arxiv.org/abs/2005.00247)
