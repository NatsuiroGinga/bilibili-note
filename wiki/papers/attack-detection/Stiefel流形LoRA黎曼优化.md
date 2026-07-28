---
title: "Riemannian Optimization for LoRA on the Stiefel Manifold"
authors:
  - Juneyoung Park
  - Minjae Kang
  - Seongbae Lee
  - Haegang Lee
  - Seongwan Kim
  - Jaeho Lee
year: 2025
date: 2026-07-22
journal: Findings of EMNLP 2025
source_pdf: "[[raw/papers/attack-detection/2508.17901.pdf]]"
tags:
  - LoRA
  - Stiefel流形
  - 黎曼优化
  - PEFT
  - 正交约束
  - 类型/论文
aliases:
  - Stiefel-LoRA
  - Park2025-Stiefel流形LoRA
key_finding: "把 LoRA 的 B 因子约束为列正交并用切空间投影与 QR 回缩更新，可保持满有效秩并在多项 LLaMA 微调任务上优于 AdamW；但固定随机 A 时明显失效，且论文没有物理状态、恶意流量或投影耦合实验。"
method: "LoRA B 因子的 Stiefel 约束、黎曼梯度与 QR 回缩"
baseline: "AdamW 优化的 LoRA 与 DoRA"
---

# Stiefel 流形上的 LoRA 黎曼优化

> 原始论文：[arXiv:2508.17901](https://arxiv.org/abs/2508.17901)，15 页。以下页码均指本地 PDF 页码。

## 研究问题

普通 LoRA 将权重增量写为 \(\Delta W=BA\)。作者认为，欧式优化会让 \(B\) 的列方向相关，降低低秩更新的有效秩。论文固定参数量不变，只改变 \(B\) 的可行域和优化器：

\[
\min_{A,B} f(W_0+BA),
\qquad
B\in\mathrm{St}(d,r)
=\{B\in\mathbb R^{d\times r}:B^\top B=I_r\}.
\]

约束对象是 **LoRA 权重因子**，不是输入物理状态、隐藏状态或物理投影输出（第 4 页）。

## 核心优化

对欧式梯度 \(M'_B\)，论文先投影到 Stiefel 切空间：

\[
\xi=M'_B-B\,\operatorname{sym}(B^\top M'_B),
\qquad
\operatorname{sym}(X)=\frac{X+X^\top}{2}.
\]

随后用 QR 回缩保持列正交：

\[
Y'=B-\alpha\xi,
\qquad
B^+=\operatorname{qf}(Y').
\]

算法正文见第 4--5 页，完整伪代码和优化器细节见第 13--14 页。\(A\) 仍按普通欧式优化更新，因此方法并未把整个低秩更新限制为正交矩阵。

## 实验结果

### 下游性能

第 5 页表 1 的常识推理平均分显示，Stiefel 优化对三个 LLaMA 规模均有增益：

| 主干         | 方法 | AdamW | Stiefel |
| ------------ | ---- | ----: | ------: |
| LLaMA-3.2-1B | LoRA |  47.6 |    59.7 |
| LLaMA-3.2-1B | DoRA |  52.3 |    59.9 |
| LLaMA-3.2-3B | LoRA |  78.9 |    82.4 |
| LLaMA-3.2-3B | DoRA |  81.1 |    84.5 |
| LLaMA-3.1-8B | LoRA |  80.4 |    84.2 |
| LLaMA-3.1-8B | DoRA |  82.9 |    86.6 |

第 6 页表 2 的阅读理解结果同样提高。例如 8B 的 BoolQ、SQuAD 与 QuAC 分别从 84.3、74.6、65.8 提高到 88.1、79.7、69.7。第 6 页表 3 的数学任务也多数提高，例如 8B 的 GSM8K 从 54.7 提高到 58.8，但 MATH 仅从 19.3 提高到 22.5。

### 正交性与有效秩

- 第 7 页图 2：Stiefel 训练的列间余弦相似度为 0；AdamW 的均值虽接近 0，但标准差为 0.5143，列方向仍高度分散。
- 第 7 页图 3：秩 \(r=16\) 时，Stiefel 的有效秩保持 16，AdamW 平均约 12。
- 第 15 页表 9：从 \(r=4\) 到 \(64\)，Stiefel 基本维持满秩；1B 的 AdamW 有效秩仅为 2.8、5.4、12.1、23.8、49.7。

这些结果支持“列正交可避免 LoRA 基向量冗余”，但不证明正交性本身一定改善任意任务。

## 负面结果与边界

第 8 页表 4 是关键反例：固定随机 \(A\)，只训练 \(B\) 时，Stiefel 平均分为 50.1，低于 AdamW 的 57.1；PIQA、ARC-Easy 和 ARC-Challenge 分别为 52.1、46.1、23.9，明显低于 AdamW 的 68.3、63.3、38.5。只有 BoolQ 和 OpenBookQA 更好。这说明正交 \(B\) 必须与可学习的 \(A\) 协同，不能独立保证性能。

论文第 8 页还列出以下限制：

- 只验证 LLaMA 系列，未覆盖指令微调模型和其他架构。
- 没有定性生成分析，也没有自适应秩实验。
- 主表采用方法各自选择的学习率；附录第 12 页中 AdamW 常用 \(10^{-4}\)，Stiefel 使用 0.1 或 0.3，因此结果包含优化器调参差异，不能解释成同学习率的纯几何效应。
- 论文承认 QR 回缩有额外计算，但没有报告墙钟时间、吞吐、峰值显存或统一硬件成本。

## 对当前课题的映射

### 可以支持

- 若新增的物理投影本身采用低秩分解，本方法提供了一个可实现的列正交更新方式。
- 有效秩和列间余弦相似度可作为“物理子空间是否塌缩”的诊断量。

### 不能支持

- 论文没有恶意流量、物理状态、PINN、跨域迁移或显式物理表征注入实验。
- \(B\) 是模型参数，不是样本相关的物理状态投影；因此不能直接声称该方法已经验证“物理投影保持”或 \(\partial\hat y/\partial\hat q\neq0\)。
- 把它用于物理分支属于新的工程假设，必须与普通投影、软正交和无约束 LoRA 做同预算消融。

## 结论

本文是“正交低秩因子可保持有效秩”的直接 PEFT 证据，适合作为实现背景和诊断依据。固定随机 \(A\) 的失败结果说明，不能把 Stiefel 约束写成独立于任务和耦合结构的普遍增益定理。
