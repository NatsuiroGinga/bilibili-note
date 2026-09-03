---
title: "Enhancing FT-Transformer With a Matérn-Driven Kolmogorov-Arnold Feature Tokenizer for Tabular Data-Based In-Bed Posture Classification"
authors: [Bing Zhou, Weiwei Chen]
year: 2025
date: 2026-09-03
journal: "IEEE Access，DOI:10.1109/ACCESS.2025.3586365，2025-07-10 出版"
source_pdf: "[[raw/papers/methodology/2025-Zhou-Matern-KAN-FeatureTokenizer-InBedPosture.pdf]]"
sha256: "fea7800042b32776bb2e7c87ecc66a01bf11f1353934753fec17ee7e8e33ee1c"
tags:
  - FT-Transformer
  - Kolmogorov-Arnold网络
  - 特征标记器
  - 训练协议
  - 类型/论文
key_finding: "本文直接改造 FT-Transformer 的特征标记器（提出 Matérn 驱动 KAN 特征标记器 MKAFT），基线 FT-T 沿用 Gorishniy 2021 的结构默认值（3 块/192 维/8 头）与训练惯例（批量 2048、初始学习率 1e-4、Adam 默认参数、早停耐心 16），全文未提及学习率调度器（物理页 7，§IV.B.2）；同时报告基线 FT-T 在极小数据集 Pmat‡ 上出现测试准确率震荡，明确归因于数据集规模过小而非优化器设置（物理页 8，§IV.D 图 4 讨论）。"
method: "把 Matérn 核引入 Kolmogorov-Arnold 网络（KAN）替代原版 B 样条基，构造 Matérn 驱动 KAN；将其用于 FT-Transformer 的特征标记器阶段（MKAFT），提升特征表示能力并加速收敛"
baseline: "FT-Transformer（FT-T，原版特征标记器）、KAFT-T（普通 KAN 特征标记器，无 Matérn 核）、MLP、SNN、AutoInt"
aliases:
  - MKAFT-T
  - Matern-KAN FT-Transformer
  - Zhou2025-MKAFT
related:
  - "[[2021-Gorishniy-表格数据深度学习模型再审视]]"
---

# 用 Matérn 驱动 KAN 特征标记器增强 FT-Transformer（在床姿态分类）

> Zhou、Chen，IEEE Access，2025-07-10，DOI:10.1109/ACCESS.2025.3586365，物理页 1 至 15。

## 一句话

本文是"直接改造 FT-Transformer"的工作（题名即含 FT-Transformer），其基线 FT-T 使用与 Gorishniy 2021 论文默认配方几乎一致的结构超参（3 块、192 维嵌入、8 头），训练协议为批量 2048、初始学习率 1e-4（与 Gorishniy 2021 Table 12 默认值同量级）、Adam 默认动量参数、早停耐心 16（与 Gorishniy 2021 patience=16 一致），全文未提及任何学习率调度器；但优化器用的是**朴素 Adam**（原文写 "ADAM optimizer"），非 Gorishniy 2021 明确要求的 AdamW，这是与原论文配方的一处偏离。

## 训练协议（本次核查重点，逐句带页码）

物理页 7，§IV.B.2 "Implementation Details"：

> "The Transformer architecture consists of 3 blocks, with each feature embedded into a 192-dimensional space and multi-head attention applied using 8 heads... Training is conducted with a batch size of 2048 and an initial learning rate of 1×10⁻⁴, utilizing the ADAM optimizer in its default configuration (β₁=0.9, β₂=0.999, ε=10⁻⁸). To enhance performance and prevent overfitting, early stopping is implemented with a patience of 16 epochs."

- 结构：3 块、192 维嵌入、8 头——与 Gorishniy 2021 Table 12 默认值（物理页 18）完全一致。
- 优化器：**朴素 Adam**（非 AdamW），批量 2048，初始学习率 1e-4，早停耐心 16 epoch。
- 全文检索 schedul/warmup/cosine/decay rate/gamma 等学习率调度相关关键词**零命中**——本文未使用学习率调度器。

## 训练稳定性：报告了一处震荡，但归因于数据规模而非优化器设置

物理页 8，§IV.D"Faster Convergence and Training"讨论 FIGURE 4（训练/测试损失曲线、准确率进程）时明确写道：

> "On the Pmat‡ dataset, however, test accuracy is highly unstable, showing minor fluctuations throughout the training process. **This instability is largely due to the extremely small size of the Pmat‡ dataset**, as previously discussed. The limited data makes the model more sensitive to individual samples during evaluation, which leads to inconsistent results."

**这是本次核查中唯一一篇明确报告 FT-Transformer 基线训练期准确率震荡的文献**，但作者的归因是**数据集规模极小**（Pmat‡ 是全文最小的数据切分之一），不是学习率调度缺失；论文全篇没有做"加/不加调度器"的消融，因此**本文不能用于支持或反驳"缺少学习率衰减导致震荡"这一假设**，只能确认"FT-Transformer 训练期震荡"这一现象在其他工作中确实被观察到过，且发生在小数据集上（与本课题 C00-half 的规模、震荡出现在训练后期而非全程等特征均不同，不能直接类比）。

## 证据等级

- 原件级别：完整论文，15 个物理页，MinerU flash-extract 全文转换 + 单页核验定位精确页码（物理页 7、8）。
- 可支撑：本文基线 FT-T 的结构超参与 Gorishniy 2021 一致；训练协议未使用学习率调度器；本文独立报告过一次 FT-Transformer 训练期准确率震荡现象。
- 不可支撑：不能用本文的"数据规模归因"来解释或排除本课题 C00-half 的后期震荡——两者的数据规模、震荡阶段（本文未区分早期/后期，仅泛指"throughout the training process"）均不可比，且本文无消融实验。
