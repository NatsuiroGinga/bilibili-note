---
schema: paper-note-search/v1
title: "GradNorm: Gradient Normalization for Adaptive Loss Balancing in Deep Multitask Networks"
title_zh: "GradNorm：深度多任务网络的自适应损失平衡梯度归一化"
authors: [Zhao Chen, Vijay Badrinarayanan, Chen-Yu Lee, Andrew Rabinovich]
year: 2018
date: 2026-09-08
journal: "Proceedings of the 35th International Conference on Machine Learning"
source_pdf: "[[raw/papers/methodology/auxiliary-learning/2018-Chen-GradNorm.pdf]]"
doi:
arxiv_id: "1711.02257"
fulltext_verified: true
tags:
  - 多任务学习
  - 损失平衡
  - 梯度范数
  - 类型/论文
tasks:
  - 深度多任务学习
  - 自适应任务损失平衡
datasets:
  - NYUv2
  - 合成多任务回归数据
methods:
  - GradNorm
  - 相对逆训练速率
  - 共享层梯度范数平衡
metrics:
  - 任务测试误差
  - 梯度范数
  - 相对训练速率
key_finding:
  - "GradNorm 根据各任务相对训练速率学习损失权重，使共享层上的任务梯度范数靠近动态目标；它解决量级与训练速率失衡，不处理梯度方向冲突，也不以目标任务验证泛化为目标。"
supports:
  - "可用任务相对训练速率动态学习损失权重并平衡共享层梯度范数"
  - "标量损失等权不保证任务梯度贡献或训练速率相等"
cannot_support:
  - "梯度范数平衡会自动改善任务梯度方向"
  - "GradNorm 能保证 DGA 跨 family 或跨年泛化"
related:
  - "[[2020-Yu-PCGrad梯度手术]]"
  - "[[2023-Jiang-ForkMerge辅助任务负迁移]]"
method: "在共享层测量各加权任务损失的梯度范数，以相对初始损失定义逆训练速率，用梯度损失更新任务权重，并在每步把权重和归一回任务数。"
baseline: "等权、单任务、静态权重、穷举权重与不确定性加权；NYUv2 多任务视觉模型"
aliases:
  - GradNorm
  - Chen2018-GradNorm
---

# GradNorm：按训练速率平衡梯度范数

## 一句话

GradNorm 是 DRIFT 三个辅助损失“标量相加但监督支持量不同”必须比较的量级平衡对照，不能替代方向或泛化诊断。

## 方法核心

原文物理第 3–4 页对任务损失

\[
L(t)=\sum_{i=1}^{K}w_i(t)L_i(t)
\]

定义共享层参数 (W) 上的任务梯度范数 (G_W^{(i)}(t))，以及相对初始损失得到的逆训练速率 (r_i(t))。目标范数为

\[
\bar G_W(t)\,[r_i(t)]^\alpha,
\]

并通过

\[
L_{\mathrm{grad}}=
\sum_i\left|G_W^{(i)}(t)-\bar G_W(t)[r_i(t)]^\alpha\right|_1
\]

更新 (w_i)。目标项求导时视为常数；每步把权重重新归一到 \(\sum_i w_i=K\)，避免把全局学习率一起改变。

## 论文可以支持

- \(\alpha\) 控制任务训练速率不对称程度；原文在不同实验采用不同值，不能把 NYUv2 的值直接移植到 DGA。
- 原文通常只在最后共享层测梯度以节省开销；这是近似位置，不证明全编码器梯度已经平衡。
- 范数平衡不消除负内积，也不直接优化单一主任务的验证泛化。

## 论文不能支持

- 梯度范数相等意味着任务更新方向一致。
- 原文的 NYUv2 超参数可以不经源侧核验移植到 DGA。
- GradNorm 能保证 family 宏风险、低误报或跨年指标改善。

## 实验结果与负证据

- 物理第 5–9 页在 NYUv2 及合成多任务上报告相对等权与不确定性加权的收益；没有 family、跨年或低误报证据。
- 物理第 8–9 页显示 \(\alpha\) 会显著改变任务权重分离程度，说明它不是可忽略的通用常数。

## 与本课题的关系

- DRIFT 的 MTP 仅在约 15% 掩码位置求交叉熵，TPP 在所有有效位置求交叉熵，TOV 在序列级求二分类交叉熵；三者标量等权不等于有效监督数或共享梯度贡献等权。
- 必须同时报告损失缩减方式、有效监督计数、共享编码器梯度范数与训练速率；否则不能区分“任务方向冲突”和“量级失衡”。
- 若 GradNorm 已取得与候选课程相同的源期 family 风险改善，则课程缺少验证反馈之外的不可约差量。

## 不可直接声称

- 三项损失数值接近就代表训练贡献相等。
- GradNorm 能自动选择对未来 family 有利的辅助任务。
- 平衡训练速率必然改善 FPR、FNR 或跨年泛化。

## 证据与题录

- PMLR 正式页：<https://proceedings.mlr.press/v80/chen18a.html>
- 正式全文：<https://proceedings.mlr.press/v80/chen18a/chen18a.pdf>
- arXiv：<https://arxiv.org/abs/1711.02257>
- 原件 SHA-256：`c298d1027a1dfcb845bc7867d64a2ec831f184a1cdc0e270124619aed9b506c1`
- Zotero：2026-09-08 精确题名检索无条目；按 arXiv 导入两次均超时，当前状态为“仓库已入库，Zotero 待重试”。
