---
title: "Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles"
authors: [Balaji Lakshminarayanan, Alexander Pritzel, Charles Blundell]
year: 2017
date: 2026-10-21
journal: "Advances in Neural Information Processing Systems 30（NeurIPS 2017）"
source_pdf: "[[raw/papers/methodology/2017-Lakshminarayanan-DeepEnsembles.pdf]]"
sha256: "835735938688c03e411b23ffd8fff172b3b2db3ad33e29e7d6b567c8b94694a0"
arxiv_id: "1612.01474v3"
tags:
  - 深度集成
  - 预测不确定性
  - 校准
  - 分布外检测
  - 概率预测
  - 类型/论文
key_finding: "把每个网络训练成概率预测器（回归用异方差高斯负对数似然，分类用 softmax 交叉熵），再用 $M=5$ 个独立随机初始化的网络做等权混合；回归的混合方差按全方差公式分解为成员平均方差加成员均值方差（物理第 5 页），在回归 NLL、分类校准与已知/未知类别熵上优于或持平 MC-dropout（物理第 6–9 页）。"
method: "proper scoring rule 训练 + 独立随机初始化集成（可选对抗训练平滑）；分类平均预测概率，回归用高斯混合的均值与方差"
baseline: "PBP、MC-dropout、单网络；分类含 MNIST/SVHN/ImageNet；分布外测试用 NotMNIST 与 CIFAR-10"
aliases:
  - DeepEnsembles
  - Lakshminarayanan2017
related:
  - "[[1995-Krogh-神经网络集成歧义分解]]"
  - "[[2020-Wen-BatchEnsemble高效集成与终身学习]]"
---

# 用深度集成做简单可扩展的预测不确定性估计

> Lakshminarayanan、Pritzel、Blundell，NeurIPS 2017，12 个物理页（正文 1–10 页 + 参考文献）。

## 一句话

这篇论文把「深度集成」从提升准确率的手段改造成预测不确定性的通用基线：每个成员用 proper scoring rule 训练成概率预测器，再用独立随机初始化的成员做等权混合；它给出的方差分解是「成员平均方差 + 成员均值方差」，而不是一条「集成必然把方差缩小 $1/M$」的定理。

## 题录与原件

- arXiv API `id_list=1612.01474` 返回 1 条：`arxiv:1612.01474v3`，
  题名 *Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles*，
  作者 Balaji Lakshminarayanan、Alexander Pritzel、Charles Blundell，
  `arxiv:comment` 为 `NIPS 2017`。**ID 假设成立。**
- NeurIPS 官方 proceedings 页：
  <https://papers.nips.cc/paper_files/paper/2017/hash/9ef2ed4b7fd2c810847ffa5fa85bce38-Abstract.html>；
  官方 camera-ready PDF：
  <https://proceedings.neurips.cc/paper_files/paper/2017/file/9ef2ed4b7fd2c810847ffa5fa85bce38-Paper.pdf>。
- 本地原件：`raw/papers/methodology/2017-Lakshminarayanan-DeepEnsembles.pdf`，12 个物理页；
  SHA-256 `835735938688c03e411b23ffd8fff172b3b2db3ad33e29e7d6b567c8b94694a0`。
- 本笔记以 **NeurIPS 官方 camera-ready** 为准；arXiv v3 用于题录核验，未逐页比对两版差异。
- 转换：MinerU `extract -l en`，转换稿 `/tmp/deepens-extract/2017-Lakshminarayanan-DeepEnsembles.md`；
  式 (1) 与混合方差公式已回到 PDF 物理页视觉复核（第 3、5 页）。

## 方法：训练概率网络，再做等权混合

### 1. 训练准则：proper scoring rule

论文主张用 proper scoring rule 训练每个网络，使预测分布校准（物理第 3 页）。对回归，网络输出均值 $\mu_\theta(\mathbf x)$ 与方差 $\sigma_\theta^2(\mathbf x)>0$，最小化异方差高斯的负对数似然（式 1，物理第 3 页）：

$$-\log p_\theta(y_n\mid\mathbf x_n)
=\frac{\log\sigma_\theta^2(\mathbf x)}{2}
+\frac{(y-\mu_\theta(\mathbf x))^2}{2\sigma_\theta^2(\mathbf x)}
+\text{constant}.$$

对方差施加正性约束（softplus），并加最小方差（如 $10^{-6}$）以保证数值稳定（物理第 3 页脚注 2）。分类则用 softmax 交叉熵，它也是 proper scoring rule；论文同时指出 Brier 分数等价于平方误差形式的 proper scoring rule（物理第 3 页）。

### 2. 集成的训练与预测

训练配方（物理第 4–5 页；Algorithm 1，物理第 5 页）：

- 每个网络使用**全部训练数据**，随机初始化参数并随机打乱数据；论文报告 bagging 反而变差（物理第 4 页）。
- 成员独立训练，可并行；默认 $M=5$（Algorithm 1，物理第 5 页）。
- 可选对抗训练：以 $\mathbf x'=\mathbf x+\epsilon\,\mathrm{sign}(\nabla_{\mathbf x}\ell)$ 生成对抗样本，联合最小化原样本与对抗样本的损失；$\epsilon$ 取输入范围的 1%（Algorithm 1，物理第 5 页）。
- 预测时把集成视为**等权混合**（物理第 5 页）：

$$p(y\mid\mathbf x)=M^{-1}\sum_{m=1}^{M}p_{\theta_m}(y\mid\mathbf x,\theta_m).$$

分类时平均预测概率；回归时是高斯混合。为便于计算分位数，论文把混合近似为高斯，其均值与方差为（物理第 5 页）：

$$\mu_*(\mathbf x)=M^{-1}\sum_m\mu_{\theta_m}(\mathbf x),$$

$$\sigma_*^2(\mathbf x)
=M^{-1}\sum_m\left(\sigma_{\theta_m}^2(\mathbf x)+\mu_{\theta_m}^2(\mathbf x)\right)
-\mu_*^2(\mathbf x).$$

### 3. 「方差缩减」到底说了什么

把上式整理为：

$$\sigma_*^2(\mathbf x)
=\underbrace{M^{-1}\sum_m\sigma_{\theta_m}^2(\mathbf x)}_{\text{成员平均方差}}
+\underbrace{M^{-1}\sum_m\left(\mu_{\theta_m}(\mathbf x)-\mu_*(\mathbf x)\right)^2}_{\text{成员均值之间的方差}}.$$

这正是全方差公式：混合分布的方差 = 组内方差均值 + 组间均值方差。它说明：

- 集成预测方差有两个来源：成员自身的预测方差，以及成员均值之间的 disagreement。
- **成员越一致，第二项越小；成员越分散，第二项越大**。因此「集成方差一定比单成员小」并不由此式推出；它取决于两项的相对大小。
- 对**均值预测**，若成员近似独立同分布，平均值的方差约为单成员的 $1/M$，这是经典的方差缩减论证；但**本篇没有给出这条定理**，也没有把它作为主张。论文给出的是混合方差恒等式与经验结果。
- 论文的经验主张是：随着 $M$ 增加，NLL、Brier 分数与 OOD 熵等指标改善（物理第 7–8 页），而不是「方差按 $1/M$ 缩小」。

## 实验证据（自报数字与页码）

### 回归

- 协议：沿用 Hernández-Lobato & Adams 的数据集与网络（1 隐层、ReLU；小数据 50 单元，protein/MSD 100 单元），训练 40 epoch，集成 5 个网络（物理第 6 页）。
- Table 1（物理第 6 页）：NLL 多数优于或持平 PBP 与 MC-dropout；但 **RMSE 并非全面更好**，例如 Boston 3.28 vs PBP 3.01、Concrete 6.03 vs 5.23、Energy 2.09 vs 1.66、Yacht 1.58 vs 1.02。
- 作者的解释：方法优化的是 NLL（包含不确定性），不是 MSE；因此部分数据集 RMSE 略差（物理第 6 页）。这是原文自述，不是本笔记的推测。

### 分类与校准

- MNIST/SVHN（Figure 2，物理第 7 页）：集成在准确率、NLL、Brier 上显著优于同 $M$ 的 MC-dropout；对抗训练在 $M=1$ 时帮助明显，随 $M$ 增大增益下降。
- ImageNet（物理第 8 页表）：$M=1$ top-1 误差 22.166%、$M=5$ 19.104%、$M=10$ 18.675%；NLL 0.959/0.809/0.789；Brier $\times10^{-3}$ 0.317/0.280/0.275。$M=5$ 是推荐默认值，但该表显示到 $M=10$ 仍有小幅增益。
- 已知/未知类别（物理第 8 页）：MNIST→NotMNIST、SVHN→CIFAR-10；随 $M$ 增大，未知类别的预测熵上升，MC-dropout 在部分样本上仍过度自信。ImageNet 的 dogs/non-dogs 划分也报告类似趋势。
- 置信度—准确率（Figure 6，物理第 9 页）：深度集成在高置信度区间比 MC-dropout 更稳健。

### 讨论

论文把不确定性来源分为两部分（物理第 9 页）：proper scoring rule 捕捉给定 $\mathbf x$ 下目标 $y$ 的歧义；集成捕捉模型不确定性；对抗训练提供局部平滑。作者明确这是**非贝叶斯**方法，并把 BMA（模型选择）与 ensemble（模型组合）区分开（物理第 2 页）。

## 与第四章「集成统计与隐式正则」家族的关系

- **现代锚点**：本篇是「集成统计作为隐式正则/不确定性来源」在深度学习中的标准引用。它把集成从「刷准确率」转向「校准与 OOD 不确定性」，并给出可直接复算的混合方差公式（物理第 5 页）。
- **可迁移的统计量**：如果第四章的年度成员输出概率或预测分布，可以按同一公式把预测方差拆成「成员内方差」与「成员间均值方差」。这为「年度成员是否真的不同」提供了一个不依赖标签的诊断量；但它是**预测分布**意义下的分解，不是 F1/AUC 的增益分解。
- **成员差异的来源不同**：本篇靠随机初始化与数据洗牌制造差异，不做显式多样性正则，也不做年度绑定；第四章若按年度训练成员，成员差异同时来自数据域与初始化，不能把本篇的 $M=5$ 经验直接套用。
- **OOD 不等于时间漂移**：本篇的已知/未知类别实验是静态数据集移位（MNIST→NotMNIST、SVHN→CIFAR-10、dogs→non-dogs），没有年度序列、没有未来年份外推。它可以支持「集成在静态 OOD 上表达更高不确定性」，不能支持「集成解决概念漂移」。
- **预算问题**：深度集成需要 $M$ 次独立训练；本篇没有讨论与单模型同预算的对照公平性，也没有报告训练总成本。第四章若与单模型基线比较，必须显式报告 $M$ 倍训练预算，不能把集成收益与预算差异混在一起。

## 不能支持的论断

- **不能声称本篇证明了「集成方差按 $1/M$ 缩小」**。论文给出的是混合方差恒等式与经验曲线；$1/M$ 是独立同分布平均的经典结论，不是本篇的定理，也不能无条件用于相关成员。
- **不能声称深度集成有校准保证**。NLL、Brier、熵与置信度—准确率都是经验指标；论文没有给出有限样本校准界。
- **不能声称对抗训练是必需的**。论文明确它是可选步骤，且在 $M$ 增大后增益下降（物理第 7 页）。
- **不能声称 $M=5$ 在所有任务上最优**。$M=5$ 是 Algorithm 1 的推荐默认值；ImageNet 表显示到 $M=10$ 仍有增益（物理第 8 页）。
- **不能把 OOD 结果外推到加密流量、年度漂移或对抗演化**。实验的移位类型是静态数据集替换，不是时间序列。
- **不能声称深度集成是贝叶斯推断**。作者明确将其定位为非贝叶斯方法（物理第 2、9 页）。
- **不能声称集成在回归 RMSE 上全面优于 PBP/MC-dropout**。Table 1 有多个数据集 RMSE 更差（物理第 6 页）。
- **不能把混合方差公式直接用于分类 F1/AUC 的误差分解**。该公式针对回归的高斯混合；分类只做了概率平均与经验评估。

## 证据等级

- **原件级别**：NeurIPS 2017 官方 camera-ready PDF，12 个物理页；arXiv `1612.01474v3` 题录经 API 核验；SHA-256 已记录。
- **已核验**：式 (1)（物理第 3 页）、Algorithm 1 与混合均值/方差公式（物理第 5 页）已视觉复核；Table 1（第 6 页）、Figure 2（第 7 页）、ImageNet 表（第 8 页）、置信度—准确率（第 9 页）的数字来自 PDF 正文。
- **未核验**：arXiv v3 与 NeurIPS camera-ready 的逐页差异；各数据集的随机种子与重复次数；训练总成本与能耗。
- **可支撑**：proper scoring rule 训练、等权混合、回归混合方差分解、$M$ 增大时 NLL/Brier/OOD 熵的经验改善。
- **实验待证**：在 LAMDA 年度序列、同训练预算与跨年度协议下，深度集成对本课题指标与不确定性的任何具体影响。
