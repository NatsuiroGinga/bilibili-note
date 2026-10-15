---
title: "Online Coreset Selection for Rehearsal-based Continual Learning (OCS)"
authors: [Jaehong Yoon, Divyam Madaan, Eunho Yang, Sung Ju Hwang]
year: 2022
date: 2026-10-15
journal: "ICLR 2022；arXiv:2106.01085"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2021-Yoon-在线核心集选择-OCS.pdf]]"
tags:
  - 持续学习
  - 核心集选择
  - 多信号合成
  - 类型/论文
key_finding: "明言单一梯度相似度准则不足以选核心集，用 minibatch similarity + sample diversity + coreset affinity 三准则合成；三个准则全部是梯度余弦族信号，是「同类信号合成优于单信号」的直接先例。"
---

# Yoon 2022：在线核心集选择 OCS（ICLR 2022）

## 论文原结论

- **§1/§3**：OCS 从每个 minibatch 中选出「promote current task adaptation while minimizing catastrophic forgetting」的子集，用三个梯度余弦族准则：
  - **Definition 1（Minibatch similarity）**：样本梯度与批平均梯度的余弦 `S(b|B) = cos(∇f(b), ∇̄f(B))`；
  - **Definition 2（Sample diversity）**：批内平均不相似度（负余弦均值，值域 [−1,0]）；
  - **Definition 3（Coreset affinity）**：样本梯度与 coreSet 随机子集平均梯度的余弦。
- **§3 明文**：「similarity criterion is **not sufficient** to select the representative coreset... hence, we propose diversity and coreset affinity criteria」——**单信号不足的明文陈述**。
- **§4.1（行 74 附近）**：minibatch 是数据集的近似，「We empirically validate that our approximation generally holds across various datasets, network structures, and minibatch sizes in Appendix B and Figure B.9」——minibatch 梯度统计作为整体统计近似的验证先例（附录 B、Fig.B.9）。
- **§5 Table 2**：噪声实例比例升高时 OCS 对强基线保持优势（5 独立 run 均值±标准差）。

## 与 LAMDA 缺陷 2 的关系

- OCS 是「**梯度余弦族信号合成**」的最近先例：三个准则全部是梯度余弦，合成后对噪声实例稳健。这与 aL-SAR A.8（单信号有害→合成显著）同方向。
- **移植公式（合成信号）**：在 ρ 之外加入正交信号合成，例如
  `s_i = w_1·ρ̂_i + w_2·(1 − ‖g_i‖/max_j‖g_j‖) + w_3·freq_i`
  或先做秩归一化再加权求和。合成所用正交信号从本仓库既有机制里选：使用频率（aL-SAR 已证单用有害、折扣后有效）、损失值、范数。
- **与 EMA 的区别**：合成改变的是**信号维度**（加入独立噪声源的信号），不改变单信号的噪声结构；EMA 失败不能否决它。合成权重 w 需按「各分量信号方差占比」选取——只有方差占比高的分量给高权重。

## 不能直接声称

- OCS 的合成是「选样」(哪些样本进缓冲)，不是「复用倍数分配」(样本以多少倍权重参与训练)；移植只能借结构。
- 其合成权重是手工设定，没有给出噪声感知的权重选取规则；「按方差占比定权」是本课题的自创部分，须明标推论。

## 待验证假设（可证伪实验)

与差分信号实验并联：在 m200 基线上把 m_r 映射从单 ρ 改为合成信号 softmax 映射，**门槛：≥2 种子方向一致为正**；先跑只读诊断测各分量信号方差占比（同 Liu 笔记的门槛 ≥50%）。

## 文献信息

- arXiv: https://arxiv.org/abs/2106.01085（arXiv comment 明示 ICLR 2022）
- 章节依据：本地 PDF §3 Def.1-3、§4.1、§5 Table 2；页码按 ICLR 2022 版式以章节号为准。
