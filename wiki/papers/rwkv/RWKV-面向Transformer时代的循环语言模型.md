---
title: "RWKV：面向 Transformer 时代的循环语言模型"
authors:
  - Bo Peng
  - Eric Alcaide
  - Quentin Anthony
  - Alon Albalak
  - Samuel Arcadinho
  - Stella Biderman
  - Huanqi Cao
  - Xin Cheng
  - Michael Chung
  - Xingjian Du
  - Matteo Grella
  - Kranthi GV
  - Xuzheng He
  - Haowen Hou
  - Przemyslaw Kazienko
  - Jan Kocon
  - Jiaming Kong
  - Bartlomiej Koptyra
  - Hayden Lau
  - Jiaju Lin
  - Krishna Sri Ipsit Mantri
  - Ferdinand Mom
  - Atsushi Saito
  - Guangyu Song
  - Xiangru Tang
  - Bolun Wang
  - Johan S. Wind
  - Stanislaw Wozniak
  - Ruichong Zhang
  - Zhenyuan Zhang
  - Qihang Zhao
  - Peng Zhou
  - Qinghua Zhou
  - Jian Zhu
  - Rui-Jie Zhu
year: 2023
date: 2026-07-21
journal: "Findings of the Association for Computational Linguistics: EMNLP 2023"
source_pdf: "[[raw/papers/rwkv/2023_Peng_RWKV_Reinventing_RNNs_for_the_Transformer_Era.pdf]]"
tags:
  - RWKV
  - 循环神经网络
  - 高效大模型
  - 长序列
  - 类型/论文
key_finding: "RWKV 将可并行的时间混合训练形式改写为递归推理，使单步解码状态和计算不随历史长度增长，但单向压缩状态会削弱对超长上下文细节的回溯能力。"
method: "时间混合、通道混合、可递归 WKV 算子与自定义 CUDA 内核"
baseline: "Pythia、OPT、BLOOM、S4 及其他长序列模型"
aliases:
  - RWKV
  - Peng2023-RWKV
---

# RWKV：面向 Transformer 时代的循环语言模型

> Peng 等，2023，Findings of EMNLP 2023 · 30 页

## 一句话

RWKV 通过可并行训练、可递归推理的 WKV 算子兼顾大模型训练扩展性与固定大小推理状态，但不能从架构复杂度直接推出在恶意流量任务上的性能或物理一致性优势。

## 问题与动机

Transformer 能在训练时并行处理整个序列，但标准自注意力的上下文计算和键值缓存会随序列增长。传统 RNN 能用固定大小状态逐步解码，却很难在时间维并行训练并扩展到大参数模型。论文的目标是让同一组计算同时支持类 Transformer 的并行形式与类 RNN 的递归形式。

## 方法

### 时间混合与标记移位

每个 RWKV 残差块含时间混合和通道混合两个子块。当前标记与上一时刻输入通过可学习插值融合，例如：

$$
r_t=W_r\left(\mu_r\odot x_t+(1-\mu_r)\odot x_{t-1}\right),
$$

$$
k_t=W_k\left(\mu_k\odot x_t+(1-\mu_k)\odot x_{t-1}\right),
\qquad
v_t=W_v\left(\mu_v\odot x_t+(1-\mu_v)\odot x_{t-1}\right).
$$

其中 $\mu_r,\mu_k,\mu_v$ 为通道级可学习系数。这一设计提供局部时序归纳偏置，但不是网络流量的物理状态转移方程。

### WKV 算子

RWKV 用逐通道时间衰减 $w$ 对历史键值信息进行加权，并用独立的 $u$ 增强当前标记：

$$
\operatorname{wkv}_t=
\frac{
\sum_{i=1}^{t-1}e^{-(t-1-i)w+k_i}\odot v_i
+e^{u+k_t}\odot v_t
}{
\sum_{i=1}^{t-1}e^{-(t-1-i)w+k_i}
+e^{u+k_t}
}.
$$

这一表达可在训练时对批次和通道并行，也可通过保存前一时刻的分子、分母和数值稳定辅助量进行递归更新。

### 训练与推理形态

- 并行训练中，单层矩阵乘主导复杂度为 $O(BTd^2)$，WKV 扫描为 $O(BTd)$。
- 递归推理中，每个时刻只更新固定大小状态。论文的有限精度实现每层保存 5 个 $D$ 维向量，总状态规模为 $5DL$。
- “常数内存和计算”是指单步解码不随历史长度增长，不是说生成 $T$ 个标记的总时间与 $T$ 无关。

## 实验证据

- 论文训练了 169M 至 14B 的六个主要模型，并用 45 个不同规模的运行估计扩展律。
- 主模型在 The Pile 的 3300 亿标记上训练一轮，与 Pythia、OPT 和 BLOOM 执行近似算力对齐的零样本比较。
- 上下文长度通过 1024、2048、4096 和 8192 标记逐步微调，论文报告 The Pile 测试损失随长度增加而下降。
- Long Range Arena 中，RWKV 在五个数据集的平均结果仅次于 S4，但这不是恶意流量或开放集攻击证据。
- 论文报告累计生成时间对序列长度为线性，而标准 Transformer 因每步读取增长键值缓存而增长更快。

## 局限与失败边界

1. 历史信息被递归压缩到单向固定状态，对超长上下文中细节信息的精确回溯弱于完整自注意力。
2. 模型对提示词信息顺序更敏感。论文附录中重排提示词后的某些任务结果几乎翻倍，说明提示协议不是可忽略变量。
3. 递归架构的理论复杂度不保证现有 CUDA 实现在任意序列长度、批量和模型规模下都比成熟 Transformer 内核更快。
4. 原文没有恶意流量、物理残差、多目标协调、LoRA 微调或开放集攻击评估。

## 对当前课题的映射

### 可复用

- 作为方法冻结后跨基座验证的高效递归架构候选。
- 作为效率评估中“单步解码状态不随历史长度增长”的理论背景。
- 当未来输入由四窗口扩展到长时间流序列时，可作为长序列因果模型候选。

### 不可直接复用

- RWKV 的隐状态没有队列长度、到达量、离开量或丢包量的可观测语义，不能代替 PINN 物理状态。
- WKV 是序列聚合算子，不是队列守恒控制方程，不能通过更换符号写成物理残差。
- 原论文的性能结论不能用于证明 RWKV 在 GeNIS、DEDALE 或 ns-3 数据上优于 Qwen3。

## 疑问 / 待验证

1. 是否存在与 Qwen3-1.7B 规模、输出协议和中文能力接近的可复现 RWKV 指令模型？
2. 当输入仅四个物理窗口时，RWKV 的长序列优势是否足以抵消工具链和 LoRA 适配成本？
3. 三目标协调算法在 RWKV 递归状态上的梯度路径是否与 Transformer 基座等价？

## 摘要意译

论文提出 RWKV，将线性注意力写成可并行与可递归的两种等价形式，以类 Transformer 方式训练并以类 RNN 方式推理。作者将模型扩展至 140 亿参数，并报告与相近规模 Transformer 相当的语言建模性能以及更稳定的长序列推理内存占用。

## 文献信息

- 官方页：<https://aclanthology.org/2023.findings-emnlp.936/>
- DOI：<https://doi.org/10.18653/v1/2023.findings-emnlp.936>
- PDF SHA-256：`7b6bbe9abbf299f65031a146a960ecc9c7c669de7b845ad8dd434ea6e3525585`
