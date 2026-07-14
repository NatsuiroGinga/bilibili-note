---
title: "mHC: Manifold-Constrained Hyper-Connections"
authors:
  - Zhenda Xie
  - Yixuan Wei
  - Huanqi Cao
  - Zizheng Pan
  - Xihui Lin
  - Chongyi Zheng
  - Jing Huo
  - Yifan Li
  - Jiarui Fang
  - Chi Zhang
  - Wenbin Wang
  - Wangding Zeng
  - Zhibo Yang
  - Xihao Xu
  - Weiwei Deng
  - Damai Dai
  - Xiaokang Chen
  - Yuxuan Sun
  - Zihan Qiu
  - Wenfeng Liang
year: 2025
date: 2025-12-31
journal: arXiv preprint
doi: "arXiv:2512.24880"
source_pdf: "[[raw/papers/2512.24880v2.pdf]]"
tags:
  - 深度学习
  - 架构设计
  - 残差连接
  - 大模型训练
  - DeepSeek
  - 类型/论文
aliases:
  - mHC
  - 流形约束超连接
  - Xie2025-mHC
key_finding: "在 HC 的可学习连接矩阵上施加流形约束（Stiefel 流形 + Birkhoff 多面体），从动力系统角度恢复信号传播的稳定性——训练 27B Dense 不崩溃，且扩展到 671B MoE 取得实际收益。额外开销仅 0.6%"
method: "Stiefel 流形约束（半正交矩阵，谱范数 = 1）+ Birkhoff 多面体约束（双重随机矩阵，行/列和为 1）；融合 CUDA kernel 将开销压缩至 0.6%"
baseline: "Pre-Norm 残差连接、原始 Hyper-Connections (HC)"
---

# mHC: Manifold-Constrained Hyper-Connections

> DeepSeek，2025-12-31（v1）· 2026-01-05（v2）
> arXiv:2512.24880 · 20 位作者（含梁文锋）· 19 页

---

## 一句话

不给 HC 的连接矩阵完全自由——将其严格约束在 **Stiefel 流形**（半正交矩阵）和 **Birkhoff 多面体**（双重随机矩阵）的交集上，从动力系统的 Lyapunov 稳定性角度保证信号传播有界。额外开销仅 0.6%，27B Dense 稳定训练 + 671B MoE 实际收益。

---

## 背景：残差 → HC → 问题 → mHC

### 残差连接的作用

论文将残差连接统一为 ODE 视角：

```
x_{l+1} = x_l + F(x_l, θ_l)    ← 显式 Euler 步，步长固定 = 1
```

关键属性：**当 F → 0 时，退化为恒等映射 x_{l+1} = x_l**。这意味着即使深层网络的 F 训练不充分，信号仍然可以无损穿透。这就是「恒等映射属性」。

### HC 的贡献和问题

HC 将单流残差扩展为 **n 流超连接**：

```
x_{l+1} = x_l · W_l + F(x_l, θ_l) · B_l
```

其中 W_l 和 B_l 是 **可学习的 n × n 矩阵**。贡献是给了残差流之间可学习的交互权重。问题是：

1. **破坏了恒等映射**：W_l ≠ I 时，即使 F → 0，x_{l+1} ≠ x_l
2. **理论缺陷**：HC 初衷是模仿显式 Euler 方法动态调整步长，但可学习 W_l **未约束步长**——h_l 可以无界增长，违背了数值方法的稳定性要求
3. **训练跷跷板**：n 条流互相竞争，loss 震荡，模型稍大就崩

### mHC 的思路

**不给 W 完全自由，将其限制在恒等映射附近的流形上。** 具体选了两种流形：

---

## 方法：两种流形约束

### 约束 A：Stiefel 流形（mHC-S）

**定义**：半正交矩阵的集合——W^T W = I（当 n ≤ d 时）或 WW^T = I（当 n ≥ d 时）。

**动力系统含义**：
- 谱范数 ∥W∥₂ = 1（半正交矩阵的所有奇异值均为 1）
- 信号沿深度传播时，范数保持不变：∥x_{l+1}∥ = ∥x_l∥（F = 0 时）
- Lyapunov 指数 = 0 —— 既不爆炸也不消失

**实现**：通过 Cayley 变换或 QR 分解将自由参数映射到 Stiefel 流形上。论文用了一种高效的 Cayley 参数化避免 QR 分解的 O(n³) 开销。

### 约束 B：Birkhoff 多面体（mHC-B）

**定义**：双重随机矩阵的集合——所有元素 ≥ 0，行和 = 列和 = 1。

**动力系统含义**：
- 每层输出是上层所有流的**凸组合**（convex combination）
- 组合闭包性：两个双重随机矩阵的乘积仍是双重随机矩阵 → 多层叠加后保证信号始终在有界区域内
- 可解释性：每层的 W 直接告诉你「流 A 对输出贡献了 30%，流 B 贡献了 70%」

**实现**：用 Sinkhorn 算法将自由参数迭代投影到 Birkhoff 多面体。

### 两种约束的取舍

| | mHC-S (Stiefel) | mHC-B (Birkhoff) |
|---|---|---|
| 约束强度 | 谱范数 = 1（等于恒等映射的范数） | 凸组合（比恒等映射弱，因为凸组合可以混合改变信号） |
| 表示能力 | 更强（允许正交变换 ≈ 旋转） | 较弱（仅允许插值） |
| 训练稳定性 | ✅ | ✅ |
| 计算开销 | 较低（Cayley 参数化） | 稍高（需 Sinkhorn 迭代） |
| 论文首选 | ✅ 主推方案 | 消融对比 |

**论文的核心选择是 mHC-S**。

---

## 理论分析：从动力系统视角看为什么有效

论文第 4 节做了严格的理论分析（Section 4: Theoretical Analysis，非常精彩）：

### 对比三种架构的 ODE 类比

| 架构 | 前向传播 | ODE 类比 | 步长 |
|------|---------|---------|------|
| Pre-Norm 残差 | x_{l+1} = x_l + F(Norm(x_l)) | 显式 Euler 法 | h = 1（固定） |
| HC | x_{l+1} = x_l · W_l + F(·) · B_l | 类比 Euler 但 W_l 无约束 | h_l = ?（无界！） |
| mHC-S | x_{l+1} = x_l · W_l + F(·) · B_l，W_l ∈ Stiefel | **投影 Euler 法** | ∥W_l∥ = 1（有界） |

关键洞察：**HC 的「超参数 h_l × 显式 Euler」类比是错的**——可学习的 W_l 根本不保证 h_l 在合理范围内，步长可以任意大。mHC-S 修复了这一点：Stiefel 约束确保每步的缩放因子恰好为 1，真正实现了恒定的数值步长。

论文通过 Lyapunov 函数分析证明了 mHC-S 的全局稳定性（Proposition 4.1–4.3），这是一般残差连接论文不提供的理论基础。

---

## 系统优化：0.6% 的额外开销怎么做到的

论文不仅做理论，而且做了扎实的系统工程（Section 5）：

- **融合 CUDA kernel**：将流形投影（Cayley 参数化 / Sinkhorn 迭代）与后续的矩阵乘法和激活函数融合到一个 kernel
- **内存访问优化**：mHC 的连接矩阵 W 很小（n × n，n 通常是 2~4），直接放到 shared memory，不额外读写 global memory
- **最终开销**：相比 Pre-Norm 残差基线，仅 **+0.6%** 的前向/反向时间

这是一个非常重要的工程结果——如果投影开销很大，再漂亮的数学也没法实际用。

---

## 实验结果

### Dense 模型（27B，300B tokens）

| 架构 | 训练稳定性 | PPL | 额外开销 |
|------|:----:|:----:|:----:|
| Pre-Norm 残差 | ✅ | 基线 | 0% |
| HC | ❌ 27B 崩溃 | — | — |
| mHC-S | ✅ | **优于基线** | 0.6% |
| mHC-B | ✅ | 优于基线但不如 mHC-S | 稍高 |

**关键点**：HC 在 7B 时正常，升到 27B 就崩。mHC-S 在 27B 上不仅不崩，PPL 还优于标准 Pre-Norm 残差。

### MoE 模型（671B）

论文将 mHC 部署到了 **671B MoE** 的生产训练中，报告了实际训练收益——在同样的算力预算下，mHC 比 Pre-Norm 残差取得了更低的训练 loss。

### 设计选择消融

- **n（流数）**：n=4 是性价比甜点，n 更大会有边际收益递减
- **Stiefel vs Birkhoff**：Stiefel 表现更好，表达力更强
- **只约束 W 还是同时约束 W 和 B**：只约束 W（混合矩阵）就足够，约束 B（F 的输入权重）没有额外收益
- **初始化**：W 初始化为单位矩阵 I（保证初始状态就是标准残差连接）

---

## 我的理解

这篇工作是 DeepSeek 在架构层面的延续推进。之前读 HC 时最大的疑惑就是「为什么可学习 W 不会崩」——事实证明，**在小模型上确实不会崩，到大模型就崩了**。

mHC 的方法本质上是**给 W 装了一个数学安全笼**：

- 传统残差：W = I，固定不变（最安全，但缺乏灵活性）
- HC：W 完全自由（最灵活，但不安全）
- mHC：W ∈ Stiefel 流形（灵活性与安全性的平衡点）

**数学上的美感**：Stiefel 流形恰好是在「保持范数不变」的约束下最大的自由度。它允许 W 做任意旋转（正交变换），但不允许拉伸/压缩。这相当于说：你可以让 n 条残差流以任何方式「合作」，但不能让任何一条流被放大或压制。从信息论角度看，这保证了信号能量沿深度守恒。

**工程上的务实**：0.6% 的额外开销是「白嫖」的水平。一般来说这种带约束的方法至少 5~10% 开销，融合 kernel 的工程功力值得关注——类似的工程技巧（Cayley 参数化避免 SVD/QR + shared memory + kernel fusion）在其他需要矩阵约束的场景也能复用。

**一个被论文低调处理的发现**：消融实验显示 HC 的跷跷板效应不是因为 W 可以任意取值，而是因为 W 的**自由度太大导致优化困难**（非凸性加剧），而不是因为 W 真的跑到了极端值。这说明问题在优化动力学，不在表示能力——mHC 通过缩小搜索空间间接解决了优化问题，而不是通过限制表示能力。

---

## 与相关工作的关系

- **Pre-Norm 残差 (Vaswani et al. 2017 / Xiong et al. 2020)**：mHC 的直接对比基线
- **原始 HC (DeepSeek, 2024)**：mHC 的前身，27B 崩塌的直接原因
- **Stiefel 流形优化**：mHC-S 的数学基础，但此前主要用在 RNN 的正交权重约束，这是第一次在大规模 Transformer 的残差连接中应用
- **Neural ODE / 动力系统视角**：mHC 的理论分析框架，Lyapunov 稳定性分析将架构设计放到了严格数学基础上——这比大多数「试试看能不能 work」的架构论文高一个层次
- **DeepSeek-V3 / DeepSeek-R1**：mHC 被部署到的实际生产模型
- **Liger-Kernel**：社区已跟进做融合 kernel（[GitHub #1066](https://github.com/linkedin/Liger-Kernel/issues/1066)）

---

## 疑问 / 待验证

- Stiefel 流形约束将所有奇异值强制为 1——是否有场景需要小于 1 的奇异值来做信号衰减（例如门控机制）？论文的消融暗示有 B 矩阵就够了，但这个论证是否在所有架构上都成立？
- n=4 是实验甜点，但论文没有解释为什么——是否和 Transformer 内部的 4 头注意力分组有隐含关联？
- 论文的 Lyapunov 分析假设 W 精确落在 Stiefel 流形上，但 Cayley 参数化的数值精度在 float16 下是否有退化？
- mHC 在 RL（如 GRPO）下的表现如何？DeepSeek-R1 的训练管线是否已经用了 mHC？

---

## 原始摘要

> Hyper-connections (HC), which expand the width of residual streams and allow the connection weights to be learnable, have recently demonstrated notable performance improvements. However, HC's success comes at the cost of disrupting the identity mapping property, which is essential for signal and gradient propagation in deep neural networks. This disruption degrades training stability substantially and limits the scalability of deep models. In this paper, we tackle the training stability issue from a dynamical system perspective, introducing manifold-constrained hyper-connections (mHC). By projecting the connection matrix onto the Stiefel manifold or the Birkhoff polytope, we restore the identity mapping property within the framework of hyper-connections. Meticulous system optimizations reduce the associated overhead to a negligible 0.6%. Extensive experiments demonstrate that mHC achieves stable training at a 27B dense scale, where HC fails, and delivers consistent improvements when scaled up to 671B Mixture-of-Experts. These results establish mHC as a stable, scalable, and efficient drop-in replacement for standard residual connections.

---

## 文献信息

- arXiv: [2512.24880](https://arxiv.org/abs/2512.24880)（v1: 2025-12-31, v2: 2026-01-05）
- 页数：19 页
- 代码：未公开（论文提交时）
