---
title: "Towards Impartial Multi-task Learning"
authors:
  - Liyang Liu
  - Yi Li
  - Zhanghui Kuang
  - Jing-Hao Xue
  - Yimin Chen
  - Wenming Yang
  - Qingmin Liao
  - Wayne Zhang
year: 2021
date: 2026-09-02
journal: "ICLR 2021 Poster"
source_pdf: "[[raw/papers/multi-task-gradient/openreview-IMPnRXEWpvr-IMTL.pdf]]"
tags:
  - 多任务学习
  - 梯度平衡
  - 损失平衡
  - 尺度不变
  - 闭式解
  - 类型/论文
key_finding: "IMTL-G 用闭式解求缩放因子，使合成梯度在各任务原始梯度上的投影相等（几何上即角平分线），从而不偏向任何任务；IMTL-L 学习损失权重使各损失尺度可比。全文只有夹角恒定退化定理与尺度不变性定理，无收敛速率保证。"
---

# IMTL：无偏多任务学习

> Liu 等，ICLR 2021 Poster，21 页。OpenReview `IMPnRXEWpvr`，**无 arXiv 版本**。
> 原件 SHA-256 前 32 位 `8ce76d27ad1e3470d3262100c0b2bf21`。

## 一句话

多任务训练中各任务的损失尺度与梯度量级不同，导致部分任务被充分训练而另一些被忽略；
IMTL 用闭式解让合成梯度在各任务梯度上的投影相等（梯度平衡），并学习损失权重使各损失
尺度可比（损失平衡），二者互补且可组合。

## 论文原结论

### IMTL-G（梯度平衡，用于任务共享参数）

合成梯度 `g = Σ_t α_t g_t`，求 `{α_t}` 使 `g` 在各 `u_t = g_t/‖g_t‖` 上的**投影相等**：
`g u_t^T = C`，`∀t`。几何上等价于求各梯度的**角平分线**，有闭式解（附录 C 式(12)）。

**与其他方法的偏向对比**（Figure 1，论文自述）：

| 方法 | 偏向 |
| --- | --- |
| GradNorm | 梯度方向接近**平均方向**的任务 |
| MGDA | **梯度量级小**的任务 |
| PCGrad | **梯度量级大**的任务 |
| **IMTL-G** | **无偏** |

**Theorem 1**：若任意两梯度夹角恒定（`u_t u_τ^T = C_1 < 1`），IMTL-G 与 GradNorm
给出相同解，即 `α_t‖g_t‖ = C_3`（缩放后范数相等）。证明在附录 C.1。

**Theorem 2（尺度不变性）**：各损失被任意正因子 `{k_t > 0}` 缩放后，
新的合成梯度 `g' = λg`，方向不变。这是 IMTL 声称 scale-invariant 的依据。

### IMTL-L（损失平衡，用于任务专属参数）

学习每任务一个尺度参数 `s_t`，用 `e^{s_t} L_t − s_t` 作为加权损失，
可与网络参数端到端联合训练。**不需要任何分布假设**（对比 Kendall 2018 的
homoscedastic uncertainty 需要）。

### 组合

任务专属参数与 `{s_t}` 由 `{e^{s_t}L_t − s_t}` 更新；任务共享参数由
`Σ_t α_t(e^{s_t}L_t)` 更新，其中 `{α_t}` 由 IMTL-G 在缩放后的梯度上算出。

### 实验中的经验观察

- 闭式变体**不加** `{α_t ≥ 0}` 硬约束时结果与原迭代法相近，且闭式解**几乎总是**给出 `α_t ≥ 0`。
- GradNorm 对超参 `γ` 敏感：默认 `γ=1.5` 在 NYUv2 好、在 Cityscapes 差；最佳是 `γ=0`。
- MGDA 聚焦小梯度任务，导致其余任务难以收敛。
- **PCGrad 只比 uniform scaling 略好**，原因是「梯度夹角等于或小于 `π/2` 时其冲突投影不起作用」。

## 假设与边界

- **无收敛速率保证**。全文仅 Theorem 1（夹角恒定退化）与 Theorem 2（尺度不变），
  摘要中的 "can converge to similar results" 是**经验描述，不是定理**。
- Theorem 1 要求**任意两梯度夹角恒定**，这在实际训练中一般不成立，故该定理只说明
  IMTL-G 与 GradNorm 的关系，不构成对 IMTL-G 本身的保证。
- IMTL-L 假设存在**任务专属参数**；梯度平衡与损失平衡分别作用于共享参数与专属参数。

## 本课题推论（未验证）

- **两损失尺度差 641 倍**（`grad_norm_rank 825.010925` 对 `grad_norm_flow 1.286630`，
  C01 epoch 2 实测），Theorem 2 的尺度不变性正对该症状；而 CAGrad 的 `c` 与
  GradNorm 的 `γ` 都是须调的超参，IMTL-G 无超参。
- **CAGrad 的收敛保证对本课题不可用**（定理 3.2 要求所有损失梯度 `H`-Lipschitz，
  而 `L_rank` 在 top-k 并列边界非光滑）。故「IMTL 无收敛保证」在本课题语境下
  **不构成相对劣势**——两者在这一栏对本课题都是空的。
- 现有梯度控制器做的是**幅值相等**（`controlled_rank_step_norm` 逐位等于 `‖g_f‖`），
  IMTL-G 做的是**投影相等**。二者是不同的平衡准则，孰优须实验裁决。
- 论文称 PCGrad 在夹角 `≤ π/2` 时投影无效；本课题 epoch 2 余弦 `−0.197`（钝角），
  **落在投影会起作用的区间**。

## 不可直接声称

- 不得声称 IMTL-G 有收敛保证——全文没有。
- 不得把 Theorem 1 当作 IMTL-G 的性能保证，它的前提（夹角恒定）实际不成立。
- 不得据本笔记声称 IMTL 在本课题上有效——**零实验证据**。
- **IMTL-L 的适用性存疑**：它假设存在任务专属参数，而本课题两个损失**共用同一条
  逐流打分路径**，没有可分离的任务专属层。该结构假设是否成立**未核实**。

## 仍需实验验证的假设

- 两任务（`T = 2`）情形下 IMTL-G 的闭式解退化成什么形式？是否与现有控制器等价或相近？
- 在本课题的极端范数差（641 倍）下，「投影相等」是否会像 MGDA 那样倒向小梯度一侧？
  论文称 IMTL-G 无偏，但其实验中的范数差远小于本课题。
- 计算开销：论文称 negligible，但本课题排序损失的反传已因显存受限用 checkpoint 重算，
  额外开销的相对占比须实测。

## 文献信息

- OpenReview：`https://openreview.net/forum?id=IMPnRXEWpvr`（另有重复条目 `jXhjXOMTI-b`）
- PDF：`https://openreview.net/pdf?id=IMPnRXEWpvr`
- 原件：[[raw/papers/multi-task-gradient/openreview-IMPnRXEWpvr-IMTL.pdf]]
- 全文提取：`mineru-open-api extract`（标准 API，原件 41.7 MB 超出 flash 模式 10 MB 上限）
