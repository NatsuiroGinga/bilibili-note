---
title: "Prioritized Training on Points that are Learnable, Worth Learning, and Not Yet Learnt (RHO-LOSS)"
authors: [Sören Mindermann, Jan Brauner, Muhammed Razzak, Mrinank Sharma, Andreas Kirsch, Winnie Xu, ...]
year: 2022
date: 2026-10-15
journal: "ICML 2022；arXiv:2206.07137"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2022-Mindermann-可约损失优先训练-ICML2022.pdf]]"
tags:
  - 持续学习
  - 可约损失
  - 优先训练
  - 类型/论文
key_finding: "ReL 信号 = 训练损失 − 不可约 holdout 损失，用小模型（21× 少参数、29× 少 FLOP）做参考即可；把单点高损失/高梯度范数信号的失效归因到「可约/不可约分解」，噪声点高 IL → 低 ReL。"
---

# Mindermann 2022：RHO-LOSS 可约损失优先训练（ICML 2022）

## 论文原结论

- **§3.2 Eq.(3)**：`RHO-LOSS = argmax L[y|x; D_t] − L[y|x; D_ho]`——「the **reducible holdout loss**—the difference between the training loss and the irreducible holdout loss (IL)」。
- **§3.2 三分论证**：i) 冗余点：已学会 → 低损失 → 低 ReL；ii) **噪声点**：「not all points with high loss are informative... The labels of such points cannot be predicted using the holdout set. **Such points have high IL and, consequently, low reducible loss**」；iii) 不相关点：低输入密度区域的点 IL 高 → 降优先级。
- **§4.1/4.2**：IL 模型可以很小（21× 少参数、29× 少 FLOP 的 LeNet 级 CNN），可跨目标架构复用摊销（一个 ResNet18 IL 模型服务 40 seeds × 5 架构）；也可无 holdout 数据训练（训练集对半互测）。
- **算法 1 第 7 行**：`RHOLOSS[i] ← Loss[i] − IrreducibleLoss[i]`。
- **§6 相关工作**：高损失/高不确定度选点族（含遗忘打分 Toneva 2018）同样受歧义标签误导；RHO-LOSS 的负 IL 基线避免之。

## 与 LAMDA 缺陷 2 的关系

- RHO-LOSS 是 Tong 2025 所用 ReL 的原始出处，提供「信号 = 两个模型输出的差」的通用构造：**同一批历史样本在参考模型与当前模型下的损失之差**。
- **移植公式**：`s_i = L(B_i; θ_ref) − L(B_i; θ_t)`（与 Tong 移植式相同，此处给出统计构造的原始出处）；θ_ref 可用**年初模型**或**上一决策点冻结快照**，IL 模型可小模型摊销（§4.1 证据：21× 参数、29× FLOP 的小 CNN 与 ResNet18 同效）——我们可用同架构年初快照或更小的模型做 θ_ref。
- Mindermann 的分解视角（可约 = 训练可消除部分）把「换单一信号」升级为「**信号 = 量测 − 基线**」，EMA 平滑做不到这一点（EMA 是同一噪声量的时间平滑，共模噪声不消）。

## 不能直接声称

- RHO-LOSS 的选点域是「训练集内部选点」（training data scheduling），不是「已入库历史样本的复用倍数分配」；移植须重测。
- 其噪声指标签噪声；我们的噪声是**批采样噪声**，机制不同，移植只借「差分共模抑制」结构。

## 待验证假设（可差分信号实验）

同 Tong 笔记的移植实验；补充一个**零成本诊断**：用已有 200 次重复只读框架，对同 200 条历史样本算 `s_i = L(B_i; θ_2013快照) − L(B_i; θ_t)` 在重抽批 vs 固定批下的 σ 比（差分量的批噪声远小于逐对夹角，因为求和消掉批内协方差项）。**门槛：信号方差占比 ≥ 50%**。成本：与前述只读诊断同量级。

## 文献信息

- arXiv: https://arxiv.org/abs/2206.07137
- 章节依据：本地 PDF §3.2 Eq.(3)、§4.1-4.2、算法 1；页码按 ICML 2022 版式以章节号为准。
- 本笔记属「噪声稳健分配信号」方法簇，与 [[2025-Tong-可约损失核心集选择-全文|Tong 2025]]、[[2020-Russo-贝叶斯最优臂识别-噪声测量分配-全文|Russo 2020]] 相互引用。
