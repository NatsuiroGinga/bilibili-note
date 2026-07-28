---
title: "StelLA: Subspace Learning in Low-rank Adaptation using Stiefel Manifold"
authors:
  - Zhizhong Li
  - Sina Sajadmanesh
  - Jingtao Li
  - Lingjuan Lyu
year: 2025
date: 2026-07-22
journal: NeurIPS 2025 Spotlight
source_pdf: "[[raw/papers/manifold/2510.01938v2.pdf]]"
tags:
  - LoRA
  - Stiefel流形
  - 黎曼优化
  - 子空间学习
  - PEFT
  - 类型/论文
aliases:
  - StelLA
  - Stiefel子空间LoRA
key_finding: "StelLA 用 USV^T 三因子表示 LoRA，并把 U、V 约束在 Stiefel 流形上；它在语言和视觉任务的平均指标上普遍优于基线，但增加约 15% 训练时间、不同方法分别调学习率，且不唯一三因子表示与理论尺度稳定性问题仍然存在。"
method: "双 Stiefel 子空间因子、欧式优化器包装、切空间投影与极分解回缩"
baseline: "LoRA、DoRA、PiSSA、OLoRA、TriLoRA、MoSLoRA、ScaledAdamW"
---

# StelLA：Stiefel 子空间低秩适配

> 原始论文：[arXiv:2510.01938v2](https://arxiv.org/abs/2510.01938)，NeurIPS 2025 Spotlight，19 页。以下页码均指本地 PDF 页码。

## 方法

StelLA 将低秩增量写成（第 3--4 页）

\[
\Delta W=USV^\top,
\quad
U\in\mathrm{St}(r,m),
\quad
V\in\mathrm{St}(r,n),
\quad
S\in\mathbb R^{r\times r}.
\]

即 \(U^\top U=I\)、\(V^\top V=I\)，而中间矩阵 \(S\) 不受正交约束。相较 LoRA，每个适配层多出 \(r^2\) 个参数，总数为 \(r(m+n)+r^2\)（第 5 页）。

第 3 页给出 Stiefel 几何操作。对 \(Y\in\mathrm{St}(k,n)\)：

\[
\operatorname{grad}_Y f
=\nabla_Y f-Y\nabla_Y^\top f\,Y,
\]

\[
\pi_Y(\Delta)
=\Delta-Y\operatorname{sym}(Y^\top\Delta),
\qquad
\rho_Y(\Delta)=\operatorname{uf}(Y+\Delta).
\]

其中 \(\operatorname{uf}\) 取极分解的正交因子。算法把普通 AdamW 等欧式优化器产生的更新方向重新投影到切空间，再对 \(U,V\) 做极分解回缩；\(S\) 仍按欧式方式训练（第 4 页算法 1）。

## 实验结果

### 语言任务

第 6 页表 1 的常识推理结果均为 3 次运行平均：

| 主干       |    最强基线平均分 |    StelLA |
| ---------- | ----------------: | --------: |
| LLaMA-2-7B |        DoRA 81.00 | **82.33** |
| LLaMA-3-8B | ScaledAdamW 85.40 | **86.72** |

第 7 页表 2 的 LLaMA-2-7B 数学与代码生成平均分为：LoRA 37.76、DoRA 36.61、PiSSA 37.41、StelLA 39.30。StelLA 并非逐项最优：MATH 为 16.55，略低于 PiSSA 的 16.64。

### 视觉任务

- 第 7 页表 3：ViT-Base 平均准确率 91.20，ViT-Large 为 92.00，分别高于最强基线 0.25 与 0.17 个点；但若干单数据集只持平或低于基线。
- 第 8 页表 4：StelLA 的文本到图像 FID 多数更低，但 SD 2.0 的 BarbieCore 为 171.83，略差于 LoRA 的 171.68；ElementFire 为 194.71，略差于 LoRA 的 194.53。CLIP 分数也不是全部最优。

## 几何消融与负面证据

第 9 页表 5 的 LLaMA-3-8B 消融均为 3 次运行平均：

| 变体             | 平均分 |
| ---------------- | -----: |
| 默认 StelLA      |   86.7 |
| 欧式三因子       |   84.4 |
| 商流形版本       |   85.7 |
| 零初始化         |   86.5 |
| 伪零初始化       |   84.2 |
| SVD-major 初始化 |   86.7 |
| SVD-minor 初始化 |   86.6 |
| 不做梯度缩放     |   86.4 |
| 增加平行移动     |   86.5 |

这支持双 Stiefel 约束有益，但也给出三点边界：

1. \(USV^\top\) 的表示仍不唯一；论文专门实现商流形消除该等价关系，说明产品 Stiefel 形式本身并未“消除规范自由度”。
2. 平行移动没有增益，SVD-major 与默认初始化持平，几何组件不是每项都必要。
3. 第 10 页表 6 中，更昂贵的指数映射为 86.76，极分解回缩为 86.72，差异极小。

第 10 页的限制包括：未与 AdaLoRA 等秩调度方法组合，未验证 Mistral、LLaVA 和 70B 模型，且三因子、梯度转换和回缩均增加计算。

## 成本与复现边界

- 第 17--18 页：极分解以薄 SVD 实现，复杂度为 \(O(mr^2)\)。批量 SVD 相对逐个执行加速 14.46--24.94 倍。
- 第 19 页：单张 H100 上，LLaMA-3-8B 常识推理训练中，LoRA 约 4.5 小时，StelLA 约 5.2 小时，即慢约 15%。推理时可合并增量，不增加推理结构。
- 附录学习率表显示方法分别调参。常识推理中 StelLA 用 \(5\times10^{-4}\)，LoRA/DoRA 多为 \(10^{-4}\)；数学和代码中 StelLA 仍为 \(5\times10^{-4}\)，基线为 \(2\times10^{-4}\)。结果不能解释成同一优化超参数下的纯几何效应。
- 第 19 页尺度分析推导，前向和反向理论稳定所需的 \(\gamma\) 缩放分别依赖 \(\sqrt{m/r}\) 与 \(\sqrt{n/r}\)。实际仍采用 LoRA 的 \(\gamma=\alpha/r\)，作者明确承认这不保证理论尺度稳定，只靠任务调节 \(\alpha\)。

## 对当前课题的映射

### 可以支持

- 若物理投影采用 \(USV^\top\)，StelLA 提供了同时维护输入、输出低维子空间的实现方式。
- 正交误差、\(S\) 的奇异值、有效秩和墙钟开销可作为必要诊断。

### 不能支持

- 所有实验约束的是适配器权重因子，不是预测队列状态或样本相关物理表征。
- 论文没有恶意流量、PINN、物理状态、生成表征耦合或跨域实验，不能直接证明物理投影有效。
- 把 StelLA 用于物理分支必须与普通线性投影、普通 LoRA、软正交惩罚和仅单侧 Stiefel 做同预算消融。

## 结论

StelLA 是本轮“正交 LoRA/适配器”中最完整的双子空间证据，并给出了明确墙钟成本。它能支持一个待验证的几何实现方案，但不能支持“Stiefel 已经证明物理状态会更稳定地进入生成流”的结论。
