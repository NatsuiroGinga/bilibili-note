---
title: "LoRA-Flow: Dynamic LoRA Fusion for Large Language Models in Generative Tasks"
authors:
  - Hanqing Wang
  - Bowen Ping
  - Shuo Wang
  - Xu Han
  - Yun Chen
  - Zhiyuan Liu
  - Maosong Sun
year: 2024
date: 2026-07-22
journal: "Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics"
source_pdf: "[[raw/papers/pinn/2024-Wang-LoRA-Flow.pdf]]"
tags:
  - 类型/论文
  - 主题/低秩适配
  - 主题/动态融合
  - 主题/生成任务
key_finding: "LoRA-Flow 根据生成前缀逐词元调整多个既有 LoRA 的融合权重，支持生成过程中的动态技能组合，但这会削弱物理路由的序列一致性和可解释性。"
method: "前缀条件门控、词元级 LoRA 融合、少样本组合"
baseline: "任务级固定融合、LoRA-Hub、单 LoRA"
aliases:
  - LoRA-Flow
  - Wang2024-LoRAFlow
---

# LoRA-Flow 词元级动态低秩融合

> Hanqing Wang 等，2024，ACL 长文 · PDF 12 页

## 一句话

论文证明生成任务可按词元动态组合 LoRA 技能，但当前流量样本的物理状态在整条结构化答案中不应随词元任意变化，序列级路由更合适。

## 方法核心

对第 $t$ 个生成词元，门控根据前缀 $y_{<t}$ 输出各 LoRA 的融合权重。融合门参数约为单个 LoRA 的 0.2%，作者称可用 200 个训练样本学习。各层可以得到不同权重。

## 实验结果

论文在六个生成任务上比较任务级固定融合，报告 LoRA-Flow 持续优于 LoRA-Hub 等基线。分析展示中文数学示例中，语言理解与数学计算阶段会偏向不同 LoRA。

## 我的理解

该机制适合答案内部技能切换，却不适合将物理状态解释为词元技能。当前候选路由应从四窗口流量观测一次计算序列级门控，并在家族任务固定为 0。

## 局限与不可外推结论

- 前缀门控可能学习输出格式或标签词捷径。
- 逐词元动态融合增加推理内核和延迟，参见 [[LoRA-Switch动态适配器切换]]。
- 论文没有物理状态监督、家族不变性或未知攻击协议。

## 与相关工作的关系

- [[MoLE分层低秩专家组合]] 按层组合既有 LoRA；本文进一步按生成步动态调整。
- [[MixLoRA词元级低秩专家混合]] 联合训练词元级专家，本文主要融合已有 LoRA。

## 原始摘要

> 摘要要点经全文第 1 页和 ACL Anthology 页面核验：论文以生成前缀条件门控逐词元融合既有 LoRA，并在六项生成任务验证。此处为中文转述。

## 文献信息

- DOI：[10.18653/v1/2024.acl-long.695](https://doi.org/10.18653/v1/2024.acl-long.695)
- ACL Anthology：[2024.acl-long.695](https://aclanthology.org/2024.acl-long.695/)
