---
title: "Why Are Linear RNNs More Parallelizable?"
authors:
  - William Merrill
  - Hongjian Jiang
  - Yanhong Li
  - Anthony Lin
  - Ashish Sabharwal
year: 2026
date: 2026-08-13
journal: "ICML 2026（Proceedings of the 43rd International Conference on Machine Learning, PMLR 306, Seoul）"
venue: "ICML 2026"
arxiv: "2603.03612v3"
doi: "未在原件中定位"
source_pdf: "[[raw/papers/rwkv/2026_线性RNN可并行性理论.pdf]]"
tags:
  - 线性RNN
  - RWKV7
  - DeltaNet
  - 表达力
  - 电路复杂度
  - 长度外推
  - 类型/论文
key_finding: "理论上 RWKV-7 与 DeltaNet（DPLR 类）达到 PNC1-完全，是线性 RNN 的表达力上界（第 8 页定理 5）；但第 9 页图 2(a) 的实测显示，在有序确定性图连通性任务上 RWKV-7、DeltaNet、Mamba 与 Transformer 在长度外推时都显著退化，只有非线性 RNN 保持近乎完美——表达力上界不等于可学到的长度泛化能力。"
aliases:
  - Merrill2026-Why-Linear-RNNs-Parallelizable
  - LRNN 并行性理论
related:
  - "[[2025-Peng-RWKV7-Goose]]"
  - "[[2024-Yang-并行DeltaNet]]"
  - "[[2025-Yang-门控DeltaNet]]"
---

# 为什么线性 RNN 更容易并行

> Merrill 等，ICML 2026（PMLR 306），arXiv:2603.03612v3（2026-06-01 版），原件 31 页

## 一句话

论文用电路复杂度把「表达力 ↔ 并行性」的权衡说死：线性 RNN（含 RWKV-7）整体落在 PNC1，可用近 log 深度电路模拟，因此几乎和 Transformer 一样好并行；非线性 RNN 能表达 P-完全/L-完全问题，因此在标准猜想下**不可能**被并行到同等深度。

## 背景：问题的演进

- 第 1 页：老式 RNN 非线性且高度串行，新架构改用线性状态更新以支持并行扫描（Blelloch 1990）。已有工作证明线性 RNN 相对 Transformer 有表达力优势，但线性与非线性 RNN 之间的比较、以及并行化的根本壁垒尚不清楚。

## 方法核心（关键定理与位置）

- **命题 1（第 5 页）**：poly 精度 RNN 的语言可被空间 `O(max{s, log n})`、时间 poly(n) 的图灵机识别。推论 1：poly 精度 RNN ⊆ P，log 精度 RNN ⊆ L。
- **推论 2（第 5 页）**：存在单层 MLP RNN，其语言在 FO 归约下是 **P-完全**。推论 3：若 NC ≠ P，存在非线性 RNN 对任意 k 都不能被深度 `O(log^k n)` 的 NC 电路模拟。
- **定理 2（第 6 页）**：存在单层 log 精度 MLP RNN 解「有序确定性图连通性」，这是一个 **L-完全**问题。推论 4：除非 L 中每个问题都有 `o(log² n)` 深度电路，非线性 RNN 相对 Transformer 的 `O(log n)` 深度代价无法消除。
- **定理 3（第 6—7 页）**：任何定义在 Q 上的 LRNN 的语言属于 **PNC1**。**推论 5（第 7 页）**：可被深度 `O(log n log* n)` 的 NC 电路族识别。第 5 页量化：序列长度 64K 到 1M 时，相对 NC1 的并行运行时开销因子只有 3。
- **定理 4（第 7 页）**：log 精度 LRNN 的语言属于 `AC0[ENC1]`（更紧的上界）。
- **定理 5（第 8 页）**：存在 **4 层 RWKV-7** 与 4 层 DeltaNet，可解 3×3 迭代矩阵乘（PNC1-完全）。**定理 6（第 8 页）**：对任意 n 状态 WFA，存在 4 层 RWKV-7 与 4 层 DeltaNet 计算 `f_A(w)`。附录第 16—17 页给出构造：定义 15 是 RWKV 式转移矩阵，引理 6 说明用 `2n` 次「点积覆写」可施加任意 n×n 矩阵，定理 9 给出 RWKV-7 模拟 Q 上 WFA 的完整结论。
- **定理 7（第 8 页）**：多层 PD（置换-对角）LRNN 属于 FO-uniform **NC1**，严格弱于 DPLR。**定理 8**：任意零阈值确定性 WFA 可被单层 PD LRNN 识别。

## 实验结果（第 8—9 页）

设置（第 8—9 页）：训练集 70K 样本，`N ∈ [1, 100]`；验证集 20K 同分布；三个测试划分各 10K，取自 `[1,100]`、`[101,200]`、`[201,300]`。全部用 `BCEWithLogitsLoss`，AdamW，学习率 1e−4，权重衰减 1e−4，batch 64，梯度裁剪范数 1.0，同分布准确率连续三次达 100% 或 60K 步早停。对比模型：非线性 RNN、RWKV-7、DeltaNet、Mamba、Transformer。

- **图 2(a) 有序确定性图连通性**：所有模型同分布高准确率；长度外推时「Transformer、RWKV-7、Mamba 与 DeltaNet 随图规模增大出现显著退化」，只有非线性 RNN 在所有区间保持近乎完美。
- **图 2(b) Zm 上迭代矩阵乘**：RWKV-7、非线性 RNN、DeltaNet 同分布接近满分，OOD 只中度退化；Transformer 与 Mamba 在所有长度上都差。
- **图 2(c) 无界整数迭代矩阵乘**：RWKV-7、非线性 RNN、DeltaNet 在 ID/OOD 都保持完美或接近完美；Mamba 随长度增加有改善但仍明显落后；Transformer 超出训练长度后急剧退化。

原件第 9 页图 2 只给柱状图，**未在正文或图中标注具体准确率数值**，因此本笔记不给出精确百分比（未在原件中定位）。

## 与本课题的关系

- **对应证据类 (b)：分布/长度外推下模型退化的受控测量。** 图 2(a) 是同一训练分布、同一超参、只改变测试规模的严格对照，结论是 RWKV-7 与 DeltaNet 在 OOD 规模上会显著退化。这对本课题「LSPR23→LSPR24 零样本迁移中完整 RWKV-7 状态递归反而更差」提供了一个**机制层面的旁证**：线性 RNN 的表达力上界虽高，但其在训练分布之外的算法泛化并不稳健。注意任务完全不同（合成算法任务 vs 加密流量检测），只能作为机制类比，不能作为同任务证据。
- **对表达力叙事的纠偏（重要）**：第 8 页定理 5/6 常被引用来论证「RWKV-7 表达力强」，但同一篇论文第 9 页的实验说明这种理论表达力在长度外推上不自动兑现。本课题若在正文引用 RWKV-7 的表达力优势，**必须同时引用此处的经验退化结果**，否则构成选择性引用。
- 第 8 页定理 7 的 PD ⊂ NC1 vs DPLR = PNC1-完全给出一条可用的架构选择依据：如果本课题的任务不需要 PNC1 级别的状态跟踪（逐流特征聚合大概率不需要），那么 RWKV-7 相对更简单的对角衰减状态并没有表达力上的必要性。这是本课题推论，论文未针对任何检测任务论证。

## 不可直接声称的内容

- 论文没有任何网络流量、异常检测或真实分布漂移实验；三个任务都是合成算法任务。
- 「非线性 RNN 更好」只在长度外推的图连通性上成立，且代价是第 6 页推论 4 的 `Θ(log n)` 并行时间开销；不能推为「本课题应改用非线性 RNN」。
- 定理 5/6 的构造是**存在性**结果（存在 4 层 RWKV-7），不保证梯度训练能学到该构造。

## 可引用的逐字原文

> "Transformer, RWKV-7, Mamba, and DeltaNet exhibit substantial degradation as graph size increases"（第 9 页 Sorted Deterministic Graph Connectivity）

## 局限

- 第 9 页结论段自陈：非线性 RNN 的额外表达力在实践中是否值得 `Θ(log n)` 并行开销仍是开放问题。
- 所有分离结果依赖标准复杂度猜想（NC ≠ P、PNC1 ≠ L 等），不是无条件下界。
- 实验只报告准确率柱状图，无种子数、无置信区间、无参数量对齐说明。

## 疑问 / 待验证

- 图 2(a) 中 RWKV-7 与 DeltaNet 的退化幅度是多少？原件未给数值，需要查其附录或代码（本次未核验）。
- PD vs DPLR 的理论差距是否在图 2 的三个任务上表现为可测差距？论文实验未包含 PD 类模型的独立对照。

## 文献信息

- ICML 2026，PMLR 306，Seoul, South Korea。arXiv:2603.03612v3 [cs.LG]，2026-06-01。
- 原件：`raw/papers/rwkv/2026_线性RNN可并行性理论.pdf`，31 页，SHA-256 `24ed4db3cf9a72565d4aaca87ded8b8e42791ce4d28ea0806a120632f8030e88`。
- DOI：未在原件中定位。
