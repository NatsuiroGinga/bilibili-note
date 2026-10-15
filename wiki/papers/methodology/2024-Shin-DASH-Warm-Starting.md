---
schema: paper-note-search/v1
title: "DASH: Warm-Starting Neural Network Training in Stationary Settings without Loss of Plasticity"
title_zh: "DASH：在平稳设定下无塑性损失的神经网络暖启动训练"
authors: [Baekrok Shin, Junsoo Oh, Hanseul Cho, Chulhee Yun]
year: 2024
date: 2026-10-15
journal: "NeurIPS 2024；arXiv:2410.23495（2024-10-30）"
doi: null
arxiv_id: "2410.23495"
evidence_level: "在线全文已下载"
source_pdf: "raw/papers/methodology/2024-Shin-DASH-Warm-Starting-Plasticity.pdf"
tags:
  - 可塑性丧失
  - 暖启动
  - 冷启动
  - 噪声记忆
  - 权重收缩
  - 类型/论文
key_finding:
  - "**暖启动（用旧权重初始化）会导致可塑性丧失**，即使数据分布**平稳**；其主因是**噪声记忆（noise memorization）**。"
  - "提出 **DASH（Direction-Aware SHrinking）**：按权重与负梯度的余弦相似度**逐神经元收缩**——相似度高（学到了特征）保留，相似度低（记忆了噪声）大幅收缩。"
  - "**对照结论**：冷启动遗忘噪声但训练慢；暖启动学不到特征；DASH 多数情况**超过冷启动与 S&P**。"
  - "**为「平稳设定下的可塑性丧失」做出反直觉归因**：即使分布不变，重复训练也会因过拟合新数据中的噪声而丧失可塑性。"
method: "DASH：新数据到来时计算训练损失的负梯度，按权重与该负梯度的余弦相似度逐神经元收缩权重（超参 λ 最小收缩阈值、α 梯度 EMA 系数）；只在新数据引入时施加一次"
baseline: "冷启动、暖启动、Shrink & Perturb (S&P)、L2 INIT、Reset；骨干 ResNet-18 / VGG-16 / **三层 MLP**；优化器 **SGD** 与 SAM"
metrics: [测试准确率, 收敛所需步数]
related:
  - "[[2023-Dohare-Maintaining-Plasticity|Dohare：持续学习中的可塑性丧失与持续反向传播]]"
  - "[[2024-Dohare-Loss-of-Plasticity-Nature|Dohare et al. 2024 Nature]]"
  - "[[INDEX|方法论论文索引]]"
---

# DASH：平稳设定下无塑性损失的暖启动

> **证据等级**：在线全文已下载（`raw/papers/methodology/2024-Shin-DASH-Warm-Starting-Plasticity.pdf`）。

## 核心结论

- **现象**：暖启动（旧权重初始化）即使**数据分布平稳**也会**可塑性丧失**，泛化反而不如从零训练。
- **理论归因**：图像数据 = **标签相关特征** + **标签无关噪声**。暖启动会让模型**记忆新数据里的噪声**而非学特征；
  冷启动通过遗忘噪声而学到更多特征，但训练更慢。**理想方法：保留已学特征、丢弃记忆的噪声。**
- **DASH**：计算负梯度，按权重与负梯度的**余弦相似度**逐神经元收缩——
  高相似度（特征）少收缩，低相似度（噪声）多收缩。**只施加一次**。
- **实验**：CIFAR-10/100、Tiny-ImageNet、SVHN，骨干 ResNet-18 / VGG-16 / **三层 MLP**，优化器 **SGD 与 SAM**。
  DASH 多数情况**超过冷启动与 S&P**；为非平稳设定设计的方法（L2 INIT、Reset、层归一化）在平稳设定下**无效**。

## 与本提案的关系

- **同族但不同干预点**：它同样研究「历史（旧权重）造成适应能力下降」，
  但**对策在权重空间（收缩），不在优化器状态**。这是「可塑性丧失」线的**第三个机制分支**（单元 / 权重 / 优化器）。
- **对本提案的启发**：DASH 说明**平稳**设定也能发生可塑性丧失，
  所以「年度概念漂移」**不是**这类现象的**必要条件**——若本课题观察到适应受损，
  **不能默认归因到漂移**，须与「单纯暖启动下的噪声记忆」区分开（这是本提案的关键混淆变量）。
- **可用性三问**：
  1. 固定 200 条预算 / 每年度 10 轮：**部分适用**——它是「数据分块到达、扩展式训练」的设定，接近年度序列，但预算语义不同。
  2. 四层 MLP：**可以**——论文**明确用了三层 MLP**，无架构假设（本文比其余候选更接近本课题骨干）。
  3. 公开代码：**未确认**（本次检索未取到仓库链接，标为「代码未确认」）。
