---
schema: paper-note-search/v1
title: "Balanced Meta-Softmax for Long-Tailed Visual Recognition"
title_zh: "平衡元 Softmax：面向长尾识别的标签分布偏移校正"
authors: [Jiawei Ren, Cunjun Yu, Shunan Sheng, Xiao Ma, Haiyu Zhao, Shuai Yi, Hongsheng Li]
year: 2020
date: 2026-10-20
journal: "Advances in Neural Information Processing Systems 33 (NeurIPS 2020)；arXiv:2007.10740"
arxiv_id: "2007.10740"
evidence_level: "本地全文（MinerU extract）"
source_pdf: "raw/papers/methodology/2020-Ren-Balanced-Meta-Softmax.pdf"
tags:
  - 长尾识别
  - 标签分布偏移
  - 先验校正
  - 平衡Softmax
  - 元采样
  - 分类器再平衡
  - 类型/论文
key_finding:
  - '把长尾识别写成**标签分布偏移**：训练与测试共享 \(p(x\mid y)\)，仅 \(p(y)\) 不同；若平衡测试后验由标准 Softmax 表示，则不平衡训练后验为 \(\hat\phi_j=n_j e^{\eta_j}/\sum_i n_i e^{\eta_i}\)（Theorem 1，Eq. 3–4，物理第 3 页）。'
  - '**Balanced Softmax 损失**为 \(\hat\ell(\theta)=-\log\!\left(n_y e^{\eta_y}/\sum_i n_i e^{\eta_i}\right)\)（Eq. 4，第 3 页）；二分类下等价于给正类 logit 加 \(\log n_+-\log n_-\) 的先验偏移。'
  - '泛化界给出的最优间隔为 \(\gamma_j^*\propto n_j^{-1/4}\)（Eq. 8，第 4 页），但作者实测把指数取 1（即 Eq. 4）最好，\(n^{1/4}\) 变体 Eq. 10 反而更差（第 4、9 页）。'
  - '**Meta Sampler** 用双层元学习学习各类采样率 \(\pi_\psi\)，缓解 Balanced Softmax 与类平衡采样叠加造成的 **over-balance**（\(1/n_j^2\) 效应，Eq. 11–12，第 5 页）。'
  - "CIFAR-10-LT（不平衡因子 200）Top-1：Softmax `71.2`、cRT `76.6`、LWS `78.1`、BALMS `81.5`；CIFAR-100-LT `41.0`→`45.5`（Table 2，第 7 页）。"
  - "Places-LT：cRT `36.7`、BALMS `38.7`；LVIS 稀有类 mask AP `19.6` 对次优 `14.6`（Table 3–4，第 7–8 页）。"
  - "**表示学习阶段仍以自然采样特征更好**：Softmax 预训练特征在解耦重训中普遍优于 Balanced Softmax 预训练特征（Table 8，附录第 20 页）。"
method: 'Balanced Softmax（按训练类频 \(n_j\) 校正 softmax 分母）+ Meta Sampler（元学习采样率）；可端到端或解耦训练'
baseline: "Softmax、CBW、CBS、Focal、Class-Balanced、LDAM、Equalization Loss、cRT、LWS"
metrics: [top-1 accuracy, many/medium/few split accuracy, LVIS AP]
related:
  - "[[2021-Menon-对数几率调整|Logit Adjustment：加性先验偏移与 Fisher 一致性]]"
  - "[[2021-Hong-LADE标签分布解耦|LADE：任意目标先验的后处理校正]]"
  - "[[2020-Kang-长尾解耦表示与分类器|cRT/NCM：冻结表示后重训分类器]]"
  - "[[2019-Cao-LDAM标签分布感知间隔|LDAM：延迟再平衡]]"
  - "[[INDEX|方法论论文索引]]"
---

# 平衡元 Softmax：面向长尾识别的标签分布偏移校正

> **证据等级**：本地全文（MinerU `extract`，`raw/papers/methodology/2020-Ren-Balanced-Meta-Softmax.pdf`，24 页）。
> 页码为 PDF 物理页。**注意：任务下达时给出的 arXiv:2007.10742 不是本文**（该 ID 是一篇 Willmore 能量数学论文）；本文实际为 arXiv:2007.10740。

## 核心机制

### 1. 标签分布偏移的建模（§3.1，第 3 页）

设 \(k\) 类、训练类频 \(n_j\)。作者明确假设训练集与测试集来自同一 \(p(x\mid y=j)\)，差异只在标签分布 \(p(y)\)：

\[
\phi_j=p(y=j\mid x)=\frac{p(x\mid y=j)}{p(x)}\frac{1}{k}
\quad\text{(平衡测试后验)},
\]
\[
\hat\phi_j=\hat p(y=j\mid x)=\frac{p(x\mid y=j)}{\hat p(x)}\frac{n_j}{\sum_i n_i}
\quad\text{(不平衡训练后验)}.
\]

若 \(\phi\) 由标准 Softmax \(\phi_j=e^{\eta_j}/\sum_i e^{\eta_i}\) 表示，则训练后验可写成

\[
\hat\phi_j=\frac{n_j e^{\eta_j}}{\sum_i n_i e^{\eta_i}}. \tag{3}
\]

这就是 Balanced Softmax 的全部统计内容：**它只校正标签先验，不建模 \(p(x\mid y)\) 的变化**。二分类时 \(n_+e^{\eta_+}/(n_+e^{\eta_+}+n_-e^{\eta_-})\) 等价于给正类 logit 加 \(\log(n_+/n_-)\)，即一次阈值/截距平移。

### 2. Balanced Softmax 损失（Eq. 4，第 3 页）

\[
\hat\ell(\theta)=-\log\hat\phi_y
=-\log\!\left(\frac{n_y e^{\eta_y}}{\sum_{i=1}^{k} n_i e^{\eta_i}}\right).
\tag{4}
\]

与 Class-Balanced / LDAM 的差别：它把类频放进 **softmax 的分母与分子**，而不是乘在损失外或改间隔；与 Logit Adjustment 的 Eq. 10 在形式上同源（加性 log-prior 偏移）。

### 3. 泛化界与 \(n^{-1/4}\) 变体（第 4 页）

作者给出平衡测试误差界

\[
err_{bal}(t)\lesssim \frac{1}{k}\sum_{j=1}^{k}
\left(\frac{1}{\gamma_j}\sqrt{\frac{C}{n_j}}+\frac{\log n}{\sqrt{n_j}}\right),
\qquad
\gamma_j^*=\frac{\beta n_j^{-1/4}}{\sum_i n_i^{-1/4}}. \tag{8}
\]

若严格按该界构造间隔，得到 Eq. 10 的 \(n_j^{1/4}\) 变体；但作者实测 **把指数取 1（Eq. 4）最好**，并明确说 Eq. 8 的界“不一定紧”（第 4 页末段；Table 5 第 9 页对比 (2) 与 (3)）。因此不能把 \(n^{1/4}\) 当作本文的推荐配方。

### 4. Meta Sampler（§3.2，第 5–6 页）

类平衡采样（CBS）与 Balanced Softmax 叠加会产生 **over-balance**：在损失收敛时，梯度条件近似把有效权重从 \(1/n_j\) 变成 \(1/n_j^2\)（Eq. 12，第 5 页）。Meta Sampler 用双层优化学习类采样率：

\[
\pi_\psi^*=\arg\min_\psi L_{D_{meta}}(\theta^*(\pi_\psi)),
\quad
\theta^*(\pi_\psi)=\arg\min_\theta \hat L_{D_{q(x,y;\pi_\psi)}}(\theta). \tag{13}
\]

内层用学习到的采样分布训练分类器，外层在**从训练集类平衡采样得到的 meta set** 上更新采样率。它只在解耦训练中使用，且**没有延迟启动**（附录 C.3，第 20 页：“start them at the beginning of the decoupled training with no deferment”）。

## 实验结果（本地全文核验）

| 设置 | 方法 | 结果 | 位置 |
|---|---|---|---:|
| CIFAR-10-LT, IF=200 | Softmax / cRT / LWS / BALMS | `71.2` / `76.6` / `78.1` / `81.5` | Table 2，第 7 页 |
| CIFAR-10-LT, IF=100 | Softmax / cRT / LWS / BALMS | `77.4` / `82.0` / `83.7` / `84.9` | Table 2，第 7 页 |
| CIFAR-100-LT, IF=200 | Softmax / cRT / LWS / BALMS | `41.0` / `44.5` / `45.3` / `45.5` | Table 2，第 7 页 |
| ImageNet-LT, ResNet-10 | cRT / BALMS | `41.8` / `41.8` | Table 3，第 7 页 |
| Places-LT, ResNet-152 | cRT / LWS / BALMS | `36.7` / `37.6` / `38.7` | Table 3，第 7 页 |
| LVIS, mask AP | BALMS / 次优 | `19.6` / `14.6`（rare） | Table 4，第 8 页 |

- **增益来源拆分**：Table 5（第 8–9 页）显示 Balanced Softmax 与 cRT/LWS 是正交组件；在 CIFAR-10-LT IF=200 上，端到端 Balanced Softmax `79.0`，解耦 Balanced Softmax `78.6`，再加 Meta Sampler `81.5`。
- **表示质量**：附录 Table 8（第 20 页）比较“用 Softmax 特征 vs 用 Balanced Softmax 特征”再重训分类器；Softmax 预训练特征普遍更好（例如 Softmax 特征 + Balanced Softmax 分类器 `78.53`，Balanced Softmax 特征 + Balanced Softmax 分类器 `77.04`）。这与 Kang et al. 的“自然采样学表示、分类器再平衡”结论一致。

## 与 PAAT M2'（分类器再平衡／延迟重加权）的可迁移点

- **M2' 的最便宜损失级替代**：PAAT 的二分类 BCE 下，Balanced Softmax 退化为

  \[
  \text{logit}_+ \leftarrow \text{logit}_+ + \log n_+ - \log n_-,
  \]

  等价于把 0.5 阈值向负类方向平移。它**不需要改采样器、不需要额外 epoch、不需要冻结表示**，可直接作为一个后处理/损失基线臂。
- **与 M2 的对照关系**：M2 是“改采样分布”（全程 1:1 平衡回合），Balanced Softmax 是“改损失/先验”。本课题已实测 M2 在 12 年平均 F1 上为 **−0.27 pp**（`m2` 相对 `base` 的 `delta_mean_f1=-0.0027387`，制品 `thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-paat-pilot/paat-comparison.json`），因此 M2' 应优先测试不改变表示学习分布的方案。
- **年度先验的可得性**：\(n_+\) 在训练年度内是可观测的；2024 年 \(n_+=159\)、2025 年 \(n_+=5\) 的量级会使 \(\log(n_+/n_-)\) 分别约为 `−4.1` 与 `−7.6`（**本文按公式推算，不是论文实验，也不是 PAAT 实测**）。极端年度的偏移很大，必须先做数值稳定性与阈值扫描，不能直接照搬。
- **不要重复 over-balance**：如果把 Balanced Softmax 与 PAAT 的平衡回合同时使用，本文的 Eq. 12 预警会叠加成 \(1/n_j^2\) 级偏置。M2' 若采用 Balanced Softmax，应**关闭**平衡采样，作为两条互斥路径分别测。

## 不可迁移边界（label shift 前提）

- **核心假设是 \(p(x\mid y)\) 不变、只有 \(p(y)\) 变**（第 3 页原文：“Assuming that all instances in the training dataset and the test dataset are generated from the same process \(p(x\mid y=j)\)”）。本课题的年度概念漂移若改变 \(p(x\mid y)\)，则 Theorem 1 的前提不成立，\(n_j\) 校正无法吸收特征分布的变化。
- **本课题已实测 33.5× 采样噪声**：在这类量级下，\(n_j\) 的经验估计与类条件分布本身都不稳定；先验校正只能处理“类比例变化”，不能处理“同类样本特征变了”。因此本文只标为 **“可迁移为基线/诊断，不可迁移为机制主张”**。
- **评测口径不同**：本文全部在**类别平衡**的测试集上报告 top-1；PAAT 报告自然年度分布下的 F1（2024 正例率约 1.64%，2025 约 0.05%）。把先验推向 1:1 会改变 0.5 阈值下的正例率，未必最大化 F1。
- **Meta Sampler 的 meta set 来自训练集类平衡采样**，在 PAAT 中等于用训练年度的正例构造一个平衡验证集；末期正例只有 5 个时，meta set 的方差极大，不能直接照搬。
- **视觉骨干与大数据**：ResNet/ResNeXt + 数十万图像；PAAT 是行为特征上的小模型，迁移需实测。

## 关键公式与页码锚点

| 内容 | 位置 |
|---|---|
| 标签分布偏移假设与 Bayes 分解 | §3.1，物理第 3 页 |
| Theorem 1 / Eq. (3) 训练后验 | §3.1，物理第 3 页 |
| Balanced Softmax 损失 Eq. (4) | §3.1，物理第 3 页 |
| Theorem 2 / Eq. (8) 泛化界与 \(\gamma_j^*\) | §3.1，物理第 4 页 |
| \(n^{1/4}\) 变体 Eq. (10) 及“取 1 更好” | §3.1，物理第 4 页 |
| Meta Sampler 双层目标 Eq. (13) | §3.2，物理第 5 页 |
| over-balance 分析 Eq. (11)–(12) | §3.2，物理第 5 页 |
| Table 2（CIFAR-10/100-LT） | §4.2，物理第 7 页 |
| Table 3（ImageNet-LT / Places-LT） | §4.2，物理第 7 页 |
| Table 4（LVIS） | §4.3，物理第 8 页 |
| Table 5（组件分析） | §4.4，物理第 8–9 页 |
| Table 8（特征来源对比） | 附录 F.1，物理第 20 页 |
| 训练细节（13K/2K iterations、无延迟） | 附录 C.3，物理第 20 页 |

## 与相关工作的关系

- 与 [[2021-Menon-对数几率调整|Logit Adjustment]]：两者都把类频转成加性 logit 偏移；LA 给出 Fisher 一致性证明并允许 post-hoc \(\tau\)，BSM 给出 Balanced Softmax + Meta Sampler 的组合。LA 的 Table 1 明确把“weight normalisation”列为不一致、把 logit adjustment 列为一致。
- 与 [[2021-Hong-LADE标签分布解耦|LADE]]：LADE 明确说 Balanced Softmax 是 \(\alpha=0\) 的特例，但 BSM 只覆盖**均匀目标先验**，LADE 覆盖任意目标先验。
- 与 [[2020-Kang-长尾解耦表示与分类器|Decoupling]]：BSM 的 Table 8 复现了“自然采样特征更好”的结论；cRT 是“冻结表示 + 平衡采样重训”，BSM 是“不冻结、只改损失”，两者是 M2' 的两条不同干预路径。

## 原始摘要要点

> "We show that the Softmax function ... gives a biased gradient estimation under the long-tailed setup. This paper presents Balanced Softmax, an elegant unbiased extension of Softmax, to accommodate the label distribution shift between training and testing."
