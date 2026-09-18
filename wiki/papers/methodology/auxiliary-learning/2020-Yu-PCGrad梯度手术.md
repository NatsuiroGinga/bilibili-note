---
schema: paper-note-search/v1
title: "Gradient Surgery for Multi-Task Learning"
title_zh: "多任务学习的梯度手术"
authors: [Tianhe Yu, Saurabh Kumar, Abhishek Gupta, Sergey Levine, Karol Hausman, Chelsea Finn]
year: 2020
date: 2026-09-08
journal: "Advances in Neural Information Processing Systems 33"
source_pdf: "[[raw/papers/methodology/auxiliary-learning/2020-Yu-PCGrad-Gradient-Surgery-MTL.pdf]]"
doi:
arxiv_id: "2001.06782"
fulltext_verified: true
tags:
  - 多任务学习
  - 梯度冲突
  - 梯度手术
  - 类型/论文
tasks:
  - 多任务监督学习
  - 多任务强化学习
datasets:
  - CIFAR-100 多任务划分
  - NYUv2
  - Multi-MNIST
  - Meta-World
methods:
  - PCGrad 冲突梯度投影
  - 多任务梯度下降
metrics:
  - 分类准确率
  - 多任务相对性能
  - 强化学习平均回报
  - 梯度余弦
key_finding:
  - "PCGrad 只在任务梯度内积为负时投影掉冲突分量；原文同时指出冲突需与梯度量级失衡和高正曲率共同出现才构成其主要优化病灶，因此负余弦本身不能证明负迁移。"
supports:
  - "负内积任务梯度可以通过投影移除冲突分量"
  - "梯度冲突、量级失衡和高曲率共同刻画 PCGrad 的局部适用条件"
cannot_support:
  - "负梯度余弦必然导致辅助任务负迁移"
  - "PCGrad 能改善 DGA 跨 family 泛化或低误报性能"
related:
  - "[[2018-Chen-GradNorm梯度归一化]]"
  - "[[2023-Jiang-ForkMerge辅助任务负迁移]]"
method: "逐任务求梯度；随机遍历其他任务；当内积为负时从当前任务梯度减去其在对方梯度方向上的投影，再汇总修改后的梯度交给原优化器。"
baseline: "等权多任务优化、单任务模型、GradNorm、MTAN，以及多任务监督学习和强化学习基线"
aliases:
  - PCGrad
  - Yu2020-PCGrad
---

# PCGrad：多任务梯度手术

## 一句话

PCGrad 是“只处理一阶梯度方向冲突”的标准直接近邻；它不读取目标验证泛化，也不保证负余弦一定有害。

## 方法核心

原文物理第 2–3 页把两任务梯度内积小于零定义为冲突，并指出有害干扰通常由三项共同出现：负内积、梯度量级差异和高正曲率。对任务 (i) 与 (j)，若 (g_i^\top g_j<0)，则执行

\[
g_i^{\mathrm{PC}}=g_i-\frac{g_i^\top g_j}{\lVert g_j\rVert_2^2}g_j.
\]

算法对每个任务按随机顺序遍历其他任务，最后汇总修改后的梯度；无冲突时不修改。原文物理第 3 页说明该更新可与 Adam、SGD 等优化器组合。

## 论文可以支持

- 物理第 3–4 页的收敛与单步优势结论主要针对两任务、光滑性等条件；当两梯度完全反向时，投影后可能得到零更新。
- 单步优于普通多任务更新还要求冲突强度、梯度量级失衡、曲率与步长满足充分条件，不能从负余弦单独推出。

## 论文不能支持

- 负梯度余弦必然造成最终测试负迁移。
- PCGrad 能自动选择对未来 family 有利的自监督任务。
- 论文结果可外推到 DGA、时间漂移或低误报部署。

## 实验结果与负证据

- 物理第 5–8 页在多任务 CIFAR、NYUv2 和强化学习任务报告收益；没有 DGA、时间漂移、低误报或未见 family 证据。
- 物理第 4 页的理论允许两梯度完全反向时投影为零；PCGrad 不是无条件共同下降保证。

## 与本课题的关系

- 作为 MTP／TPP／TOV 梯度诊断后的标准梯度手术对照。
- 诊断必须同时记录原始梯度范数、成对余弦、投影激活率和源期 family／良性验证风险；只看到投影激活不能宣称辅助任务负迁移。
- 如果 PCGrad 已解释拟议课程的全部源期收益，则课程只能被解释为已知梯度手术的任务应用，不能承担独立算法差量。

## 不可直接声称

- MTP、TPP 或 TOV 的负余弦必然降低未来 family 检出。
- PCGrad 能改善 FPR／FNR 取舍或跨年泛化。
- 三任务的不同标量损失等权就是不同梯度范数等权。

## 证据与题录

- NeurIPS 正式全文：<https://proceedings.neurips.cc/paper_files/paper/2020/file/3fe78a8acf5fda99de95303940a2420c-Paper.pdf>
- arXiv：<https://arxiv.org/abs/2001.06782>
- 原件 SHA-256：`229c46e194927d3763495e03faf5d1dc5e16341b7e94e5103bcc4ba2f306a7bc`
- Zotero：2026-09-08 精确题名检索无条目；按 arXiv 导入两次均超时，当前状态为“仓库已入库，Zotero 待重试”。
