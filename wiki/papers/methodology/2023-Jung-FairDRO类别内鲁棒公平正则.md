---
title: "基于类别内鲁棒优化的重加权群体公平正则"
authors: [Sangwon Jung, Taeeon Park, Sanghyuk Chun, Taesup Moon]
year: 2023
date: 2026-09-07
journal: "ICLR 2023"
source_pdf: "[[raw/papers/methodology/2023-Jung-FairDRO-Classwise-Robust-Optimization.pdf]]"
tags: [分布鲁棒优化, 类别条件风险, 群体公平, 重加权, 类型/论文]
key_finding: "FairDRO式（6）已对每个类别分别执行组内DRO再跨类别平均，因此双类别对手不是空白；其公平目标、准概率卡方球和可负权重又不同于DRIFT的低误报与未见生成器任务。"
aliases: [FairDRO, Jung2023-FairDRO]
---

# 基于类别内鲁棒优化的重加权群体公平正则

## 一句话

FairDRO 已发表“每个类别一个组内鲁棒内层”的核心结构；DRIFT 候选必须把它列为来源组件和强近邻，但可以通过安全任务特定的组、信息边界、低误报约束及不可分联合结构形成待验证差量。

## 题录与版本

- 题名：*Re-weighting Based Group Fairness Regularization via Classwise Robust Optimization*。
- 作者：Sangwon Jung、Taeeon Park、Sanghyuk Chun、Taesup Moon。
- 发表：ICLR 2023 主会论文；arXiv `2303.00442v1`。
- 本地 PDF：23 个物理页，SHA-256 `8ea4e65ceec4da6940a36d89b4d457aa9595145e3aabcac47bce4a17d3257788`。
- Zotero：父项 `RIFNP8H9`，PDF 附件 `55T2X4X9`，全文索引 `81161` 字符。

## 方法与公式

### GroupDRO 与准概率卡方球

物理第 4 页，§4.2，式（3）先回顾标准 GroupDRO：

$$
\theta^{\mathrm{GDRO}}
=\arg\min_\theta\max_{q\in\Delta^{|\mathcal A|}}
\sum_{a\in\mathcal A}q_a\mathcal L(\theta,\mathcal D_a).
$$

同页式（4）定义以均匀组质量为中心、半径为 $\rho$ 的 $\chi^2$ 散度球 $\mathcal Q_\rho$。它只约束权重和为 1 与散度，不要求 $q_a\ge 0$，所以可包含负分量的准概率。式（5）把内层最大化等价为组均衡平均损失加组损失方差根正则。

### 式（6）：逐类别独立鲁棒内层

物理第 5 页，§4.3，FairDRO 核心目标是：

$$
\theta^{\mathrm{FairDRO}}
=\arg\min_\theta\frac{1}{|\mathcal Y|}
\sum_{y\in\mathcal Y}
\max_{q^y\in\mathcal Q_\rho}
\sum_{a\in\mathcal A}q_a^y\mathcal L(\theta,\mathcal D_a^y).
$$

这不是把 $(y,a)$ 全部扔进一个共同最坏组，而是对每个类别 $y$ 单独最大化，再做等权类别平均。因此，“良性一个对手、恶意一个对手”的结构层已被直接覆盖。

物理第 5 页式（8）给出 $q_a^{y*}$ 的闭式解。半径 $\rho$ 与组数共同决定权重范围，且权重可为负；论文把这种性质用于更积极地惩罚高准确率组，以实现类别条件准确率差异正则。

### 求解

物理第 6 页，§4.4，论文指出指数梯度不适用于可负的准概率集合，转而用平滑迭代最佳响应：外层按重加权损失下降，内层闭式最优权重通过随训练衰减的步长平滑更新，见式（9）–（10）和算法 1。实践中外层用交叉熵，内层更新用 0-1 组损失，并且组权重更新需要全训练集组损失。

## 对双类别对手原创性的影响

### 已有标准组件

- 每个类别分别建立组权重向量和鲁棒内层。
- 跨类别等权汇总。
- 组损失方差正则、卡方球半径、闭式权重和平滑最佳响应。

### DRIFT 可保留的任务化差量

- 组不是敏感属性公平组，而是仅由源期合法信息定义的形态、family 歧义敏感性和后续生成器等价组。
- 目标不是 DCA 公平，而是固定源阈值下良性 FPR、恶意 FNR、未见生成器与最坏年共同向量。
- FairDRO 的同一 $\rho$、等权类别平均与可负权重不能未经证据直接搬用；DRIFT 的两侧集合和运营约束需要独立定义。
- 当前四长度组硬最大资格探针已失败，只否决标准 GroupDRO 近邻，不等于 FairDRO 或最终任务化集合有效。

### 章级主创新门

FairDRO 的存在不要求 N02/N09 各自发明全新 DRO 原理。候选仍可从已知家族做实质任务化改造，但联合主方法必须给出不能约化为式（6）的任务定义、约束或耦合，并由来源组件消融、严格 2×2 和 DRIFT 真实实验支持。

## 最小实验影响

1. 必须增加 FairDRO 式（6）同分组对照，而不只比较普通 GroupDRO。
2. 分别比较非负概率权重与 FairDRO 准概率权重；权重符号是实质差异，不可省略。
3. 比较等权类别平均与固定低误报约束；若后者收益只来自类别系数变化，不构成新联合机制。
4. 若任务化联合目标可逐项分离为两个式（6）内层之和，章级主创新主张失败；只有额外约束或耦合的删减消融有独立增量，才可保留。

## 不能直接声称

- 不能把 FairDRO 的公平性实验外推为 DGA 时间漂移或低误报效果。
- 不能把准概率负权重默认解释为安全可接受；它可能降低某些组权重，必须报告组构成和双侧护栏。
- 不能因 FairDRO 已有就整体否决 N02/N09；应按“来源归属—任务化差量—联合创新”三层审查。

## 与本课题制品的关系

标准四长度组硬最大 C10/C01 均有 `23438` 个多组活动步但触发低误报或另一侧护栏，见[[结果裁决]]。该结果说明简单类别内最坏组不足，不证明 FairDRO 的卡方球、平滑最佳响应或任何未运行方案有效。

## 文献信息

- arXiv：<https://arxiv.org/abs/2303.00442>
- ICLR：<https://openreview.net/forum?id=Q-WfHzmiG9m>
