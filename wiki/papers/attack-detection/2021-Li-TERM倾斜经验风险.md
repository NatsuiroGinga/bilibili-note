---
title: "Tilted Empirical Risk Minimization"
authors: [Tian Li, Ahmad Beirami, Maziar Sanjabi, Virginia Smith]
year: 2021
date: 2026-09-09
journal: "ICLR 2021；arXiv:2007.01162"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2021-Li-TERM-Tilted-Empirical-Risk-Minimization.pdf]]"
tags:
  - 风险敏感学习
  - 持续学习
  - 类型/论文
key_finding: "TERM 用倾斜参数 t 对逐样本损失做指数重加权，在平均损失、最大损失和分位损失之间提供平滑取舍；它不是 FPR 约束。"
method: "t-tilted empirical risk 与层次多目标倾斜"
baseline: "ERM、鲁棒回归、类别不平衡和公平学习方法"
aliases: [TERM, Tilted-ERM, Li2021-TERM]
---

# Tilted Empirical Risk Minimization

> Li 等，2021，ICLR；全文 44 页。本文依据 MinerU 分页提取和原 PDF 核对。

## 一句话

TERM 将 ERM 的平均损失改成带倾斜参数的对数矩母函数，从而连续调节高损失样本与低损失样本的权重。

## 方法核心

主目标位于第 1 节公式（2）：

\[
\widetilde R(t;\theta)=\frac{1}{t}\log\left(\frac{1}{N}\sum_{i=1}^{N}\exp\left(t f(x_i;\theta)\right)\right).
\]

当 `t→0` 时恢复平均损失；`t>0` 增大高损失样本权重，趋向 max-loss；`t<0` 抑制高损失样本，趋向 min-loss。第 2 节引理 1、公式（3）给出倾斜梯度：

\[
\nabla_\theta \widetilde R(t;\theta)=\sum_i w_i(t;\theta)\nabla_\theta f(x_i;\theta),\qquad
w_i=\frac{\exp(t f_i)}{\sum_j\exp(t f_j)}.
\]

第 3 节公式（4）扩展为组级与样本级的层次倾斜，可同时处理类别不平衡和异常样本。第 4 节算法 1 给出批量求解，附录 H 的算法 2/4 给出随机小批量求解。

## 实验结果

- 第 5 节覆盖鲁棒回归、噪声分类、公平性和类别不平衡；作者报告 TERM 在多种任务上与专用方法竞争。
- 第 5 节实现细节说明正倾斜参数在验证集上搜索 `{0.1, 0.5, 1, 5, 10, 50, 100, 200}`；负倾斜实验固定 `t=-2`。这些是原论文设置，不是 LAMDA 配置依据。
- 作者公开报告随机 TERM 求解器的迭代成本约为 ERM 的同量级，附录 H 讨论了小批量归一化。

## 与 LAMDA 的关系

- TERM 可作为“风险敏感重加权”后置对照，检验缺口修复是否只是通用 hard-example weighting。
- `t>0` 可能强调高损失良性样本并抬高 FPR；论文没有提供 LAMDA 的 FPR 可行性保证。
- 当前不进入双玩家首轮：双玩家首先要约束 FPR 与旧恶意回归，TERM 不能替代可行性约束。
- 若后续运行 TERM，`t` 必须只用来源／开发层冻结，不能访问封印年；需要报告 FPR、FNR、旧恶意负向翻转和恶意正向修复，而不只报告平均 AP/F1。

## 不可直接声称

- 其他数据集的 TERM 增益不能转述为 LAMDA 结果。
- TERM 的 tilt 不是 FPR hard constraint，也不是双玩家安全预算。
- `t=-2` 或正 tilt 网格不能直接移植为 LAMDA 最优配置。

## 文献信息

- arXiv：https://arxiv.org/abs/2007.01162
- 关键位置：第 1 节公式（2）—（3）；第 3 节公式（4）；第 4 节算法 1；第 5 节实验；附录 H 算法 2/4。
