---
schema: paper-note-search/v1
title: "Maintaining Plasticity in Deep Continual Learning"
title_zh: "在深度持续学习中维持可塑性"
authors: [Shibhansh Dohare, J. Fernando Hernandez-Garcia, Parash Rahman, A. Rupam Mahmood, Richard S. Sutton]
year: 2023
date: 2026-10-15
journal: "arXiv 预印本 `2306.13812`（2023-06-23）；同期工作正式版为 Dohare et al., Nature 632:768–774, 2024, doi:10.1038/s41586-024-07711-7"
doi: "10.1038/s41586-024-07711-7"
arxiv_id: "2306.13812"
evidence_level: "在线全文已下载"
source_pdf: "raw/papers/methodology/2023-Dohare-Maintaining-Plasticity-Deep-Continual-Learning.pdf"
tags:
  - 持续学习
  - 可塑性丧失
  - 持续反向传播
  - 单元重初始化
  - L2正则
  - 类型/论文
key_finding:
  - "**可塑性丧失（loss of plasticity）**：深度网络在持续学习下会**失去学新样本的能力**，不只是遗忘旧样本；ImageNet 二分类准确率从早期任务 `89%` 降到第 2000 个任务的 `77%`（约等于线性网络）。"
  - "**发生在「很宽范围的深度网络架构、优化器、激活函数、批归一化、dropout」下**——即 **不是某一优化器的特有现象**；L2 正则（尤其配权重扰动）能显著缓解。"
  - "提出 **continual backpropagation**：微改反向传播，每个样本后**重初始化一小部分低效用的隐藏单元**，可让可塑性**无限期维持**。"
  - "**机制归属：网络单元，不是优化器状态。**"
method: "持续反向传播——为每个隐藏单元维护贡献效用（激活幅度 × 输出权重的滑动平均），按替换率 ρ 重初始化最低效用单元（入权重重采样、出权重清零）；对照 L2 正则 / 权重扰动"
baseline: "标准反向传播（BP）；L2 正则；有/无权重扰动"
metrics: [ImageNet 二分类准确率随任务序号, MNIST 持续学习准确率]
related:
  - "[[2024-Dohare-Loss-of-Plasticity-Nature|Dohare et al. 2024 Nature：可塑性丧失正式版]]"
  - "[[2024-Shin-DASH-Warm-Starting|DASH：暖启动下的可塑性丧失与方向感知收缩]]"
  - "[[INDEX|方法论论文索引]]"
---

# 在深度持续学习中维持可塑性

> **证据等级**：在线全文已下载（`raw/papers/methodology/2023-Dohare-Maintaining-Plasticity-Deep-Continual-Learning.pdf`）。
> 本笔记依据摘要与逐节核验；页码待补（本笔记以章节号锚定）。

## 核心结论

- **可塑性丧失的定义**：不只忘记旧样本，而是**失去学习新样本的能力**。
- **实证**：MNIST 与 ImageNet 被改造成**任务序列**做持续学习。ImageNet 二分类性能从早期任务 `89%` 降到**第 2000 个任务**的 `77%`，约等于线性网络水平。
- **发生的范围**：**宽范围的深度网络架构、优化器、激活函数、批归一化、dropout** 都会发生；
  `L2 正则`能显著缓解，尤其与**权重扰动**结合时。
- **对策**：**continual backpropagation (CBP)**——轻微修改常规反向传播，**每个样本后重初始化一小部分使用较少的单元**，似可无限期维持可塑性。

## 与本提案（年度边界重置优化器状态）的关系

- **同族问题、不同机制**：本工作把「历史造成的适应能力下降」定位在**单元/权重的饱和与休眠**，
  而不是优化器矩缓冲。**它的对策（单元重初始化）不是优化器层改动**。
- **对本提案的关键削弱**：摘要明说可塑性丧失在**各种优化器**下都出现——
  这**反对**「优化器状态是历史危害的唯一或主要载体」的强主张；
  但**不反对**「优化器状态是载体之一」的弱主张。
- **对固定小回放恶意软件设定的可迁移性**：CBP 需要改动网络内部（单元级操作），
  在**四层 MLP**上可运行（无特殊架构假设）；但它是**结构性改动**，与「年度边界重置动量」不是同一干预。
