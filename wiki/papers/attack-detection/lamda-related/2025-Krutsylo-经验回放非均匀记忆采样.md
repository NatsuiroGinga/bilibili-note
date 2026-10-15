---
title: "Non-Uniform Memory Sampling in Experience Replay（经验回放中的非均匀记忆采样）"
authors: "Andrii Krutsylo"
year: 2025
date: 2025-02-16
journal: "arXiv preprint（arXiv:2502.11305v1，波兰科学院计算机科学研究所）"
source_pdf: "raw/papers/attack-detection/lamda-related/2025-Krutsylo-经验回放非均匀记忆采样.pdf"
tags:
  - 持续学习
  - 经验回放
  - 记忆采样
  - 固定缓冲
  - 类型/论文
key_finding: "在缓冲内容固定的前提下，非均匀回放采样（随机权重）在缓冲 200/500/1000 上一致优于均匀采样（CIFAR-10 +2.33~4.68%、Imagenette +2.37~3.54%，配对 t 检验 p<0.01）；采样概率与损失/梯度范数只有弱相关（Spearman ρ≈0.28/0.32），提示高损失优先并非最优，非均匀复用权重本身可带来增益。"
---

# Non-Uniform Memory Sampling in Experience Replay

## 证据等级
**在线全文已下载并 MinerU 精读**（arXiv 2502.11305v1，本地 PDF：`raw/papers/attack-detection/lamda-related/2025-Krutsylo-经验回放非均匀记忆采样.pdf`）。公开代码：`https://github.com/DentonJC/memory-sampling`。

## 方法与设定（原文页码/章节）
- 设定：**在线类增量（online Class-IL）**，五任务各两类，CIFAR-10（3 层 CNN）与 Imagenette（MobileNet-v3-small）。
- 冻结缓冲内容，仅改变**从缓冲采样回放的各样本概率**（§3 实验设计）。
- 缓冲规模 {200, 500, 1000}；每轮 50 个随机非均匀权重分布 + 1 个均匀基线，5 个随机种子。
- 结论（§4 表 1）：非均匀最好分布一致优于均匀；CIFAR-10 200/500/1000 为 `35.97→38.30 / 41.26→45.94 / 46.05→49.77`；Imagenette `76.01→79.42 / 82.21→84.58 / 83.47→87.01`。
- 相关性（§4）：采样概率 vs 损失 ρ=0.2813；vs 梯度范数 ρ=0.3157——**都不是强相关**；高表现组平均损失反而更低（0.742 vs 0.815，Mann-Whitney p=0.00377）。

## 三问
1. **能否在固定 200 条预算下运行？** **能**。原文缓冲 200 即为一档实验设定，且是"固定缓冲内容 + 改变采样概率"的纯读取侧机制，不增加存储。
2. **能否挂 MLP？** **能**。机制与架构无关（只改回放采样概率），原文 CNN/MobileNet 只是载体。
3. **有无公开代码？** **有**：`https://github.com/DentonJC/memory-sampling`（原文摘要明示）。

## 与本文第三章的关系
- 本文机制含"按正例数亏空加权的**复用倍数**"，即改变历史样本被回放的频次。**该文正是"复用频次/采样权重"这一轴上的 2025 年直接先例**：它证明即使随机非均匀权重也优于均匀。
- 划界点：该文是**实证研究（empirical study）**，不提出命名方法，也不给出可复用的权重规则；它只证明"非均匀优于均匀"，并明说"如何 principled 地学出权重仍是开放问题"（§5）。本文的"亏空加权复用倍数"恰是对该开放问题的具体回答之一——**可作动机引用与最简 ablate 对照（uniform vs 该文式非均匀）**。
- 原文明确把"存什么（buffer selection）"与"怎么采（replay distribution）"列为尚未统一的框架（§5 末）。

## 不能直接声称
- 不能把该文的 CIFAR-10/Imagenette 增益直接搬到 LAMDA；其数据为图像、设定为在线 Class-IL，本文为 Domain-IL 二分类表格。
- 该文的"随机权重"不是可用方法，仅证明上界空间存在。
