---
title: "MTLoRA: A Low-Rank Adaptation Approach for Efficient Multi-Task Learning"
authors:
  - Ahmed Agiza
  - Marina Neseem
  - Sherief Reda
year: 2024
date: 2026-07-22
journal: "Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition"
source_pdf: "[[raw/papers/pinn/2024-Agiza-MTLoRA.pdf]]"
tags:
  - 类型/论文
  - 主题/低秩适配
  - 主题/共享私有参数
  - 主题/多任务学习
key_finding: "MTLoRA 同时设置任务无关与任务专用低秩模块，在共享骨干一次前向中兼顾共享和专用特征，是当前单私有物理 LoRA 最直接的低秩结构先例之一。"
method: "任务无关 LoRA、任务专用 LoRA、共享多任务骨干"
baseline: "全量多任务微调、单任务微调、多种参数高效微调"
aliases:
  - MTLoRA
  - Agiza2024-MTLoRA
---

# MTLoRA 共享与任务专用低秩适配

> Ahmed Agiza、Marina Neseem、Sherief Reda，2024，CVPR · PDF 10 页

## 一句话

MTLoRA 证明共享低秩参数与任务专用低秩参数可在同一骨干中协同，但其所有任务联合训练，不能自动保证某个分支保持原模型输出。

## 方法核心

论文将 Transformer 中的低秩增量分为任务无关模块和任务专用模块：前者提取跨任务共同特征，后者处理各下游任务差异。多任务损失仍是各任务损失的加权和；扩展版 MTLoRA+ 还在分层视觉 Transformer 的补丁合并层加入低秩模块。

## 实验结果

在 PASCAL 多任务密集预测上，MTLoRA 的综合下游准确度高于全量多任务微调，同时训练参数减少约 3.6 倍。论文还展示不同秩下的准确度与参数量帕累托关系。

## 我的理解

当前结构可对应为：冻结的 S3 检测 LoRA 承担已验证检测能力，新增任务专用物理 LoRA 只服务子类与开放集。与 MTLoRA 不同，S3 不再联合更新，家族任务固定关闭私有分支。

## 局限与不可外推结论

- 实验是视觉编码器多头密集预测，不是自回归生成。
- 任务专用参数仍通过联合目标训练，没有家族输出不变性定理。
- 3.6 倍是相对论文全量多任务微调的训练参数，不是当前模型的显存或延迟结论。

## 与相关工作的关系

- [[对抗式多任务文本分类共享私有表征]] 提供共享与私有表示共同进入输出的先例。
- [[MoDULA通用与领域专用低秩适配]] 进一步采用阶段式训练与冻结。

## 原始摘要

> 摘要要点经全文第 1 页和 CVF 正式页面核验：论文以任务无关和任务专用低秩模块高效适配多任务视觉模型。此处为中文转述。

## 文献信息

- CVF：[CVPR 2024 正式页面](https://openaccess.thecvf.com/content/CVPR2024/html/Agiza_MTLoRA_Low-Rank_Adaptation_Approach_for_Efficient_Multi-Task_Learning_CVPR_2024_paper.html)
- 页码：16196-16205
