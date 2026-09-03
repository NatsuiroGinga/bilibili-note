---
title: "Accelerating Deep Learning by Focusing on the Biggest Losers"
authors: [Angela H. Jiang, Daniel L.-K. Wong, Giulio Zhou, David G. Andersen, Jeffrey Dean, Gregory R. Ganger, Gauri Joshi, Michael Kaminksy, Michael Kozuch, Zachary C. Lipton, Padmanabhan Pillai]
year: 2019
date: 2026-09-02
journal: "arXiv:1910.00762 [cs.LG]"
source_pdf: "[[raw/papers/methodology/training-efficiency/2019-Jiang-Selective-Backprop-Biggest-Losers.pdf]]"
sha256: "97984faaf9a939b4e37b733204b2891b141d2301019df95b2e156b388838ab3c"
tags:
  - 训练效率
  - 样本选择
  - 重要性采样
  - 反向传播
  - 类型/论文
key_finding: "Selective-Backprop 用前向损失在最近 R 个样本经验分布中的分位数的 β 次方作为反传保留概率 P(L)=[CDF_R(L)]^β，概率性跳过低损失样本的反向传播；在 CIFAR10/100、SVHN 上比常规 SGD 快最多 3.5x 达到目标错误率，比在线重要性采样基线 Kath18 快 1.02–1.8x（第7页 Table 1；第11页 5.5 节）。"
method: "前向计算损失 → 按损失在最近 R 个样本经验 CDF 中的分位数的 β 次方作为保留概率 → 只保留被抽中样本参与反传，凑齐一个反传批次；Stale-SB 变体每 n 个 epoch 才刷新一次用于选择的损失。"
baseline: "Traditional（全量训练）、Kath18（Katharopoulos & Fleuret 2018 在线重要性采样）"
aliases:
  - Selective-Backprop
  - SB
  - Stale-SB
  - Jiang2019-选择性反传
related:
  - "[[2020-Jain-Checkmate最优张量重物化]]"
  - "[[2021-Kirisame-动态张量重物化]]"
  - "[[2014-Ogawa-SVM安全样本筛选]]"
---

# 用聚焦高损失样本加速深度学习训练

> Jiang, Wong, Zhou, Andersen, Dean, Ganger, Joshi, Kaminksy, Kozuch, Lipton, Pillai，2019，arXiv:1910.00762 · 14 页（正文 1–6 节 + 附录 A.1–A.4）

**本次核验范围**：全文 14/14 页完整核验，含摘要、正文第 1–6 节与附录 A.1–A.4（补充材料）。未发现无法定位的章节。

## 一句话

Selective-Backprop（SB）用前向传播算出的损失作为"这个样本值不值得反传"的廉价代理，按损失在最近 R 个样本经验 CDF 中的分位数的 β 次方设定保留概率，概率性跳过低损失样本的反传；在 CIFAR10/100、SVHN 图像分类上把训练到目标错误率所需的时间压缩到原来的 1/3.5，并比另一个在线重要性采样基线快 1.02–1.8 倍（Abstract；第 7 页 Table 1）。

## 背景：问题的演进

传统 SGD 对所有训练样本平均分配算力，无论其是否已被网络正确分类（Introduction 第 1 段，引 Hinton 2007）。已有重要性采样方法（Loshchilov & Hutter 2015、Johnson & Guestrin 2018 等）多需维护跨 epoch 的历史损失分布，要求先完整跑一遍数据集再构建采样分布，并依赖超参调节"陈旧历史"的影响（第 2 节 Related Work）。与本文最相关的工作 Katharopoulos & Fleuret (2018)（本文简称 Kath18）同样用在线前向损失做采样，不需要维护历史状态，但它预先固定每批被选样本数量，且依赖一个可变的起始条件（第 2 节倒数第 2 段）。本文提出 Selective-Backprop：仅用当前 forward pass 的损失做决策，不预先固定选中数量，是一个无状态、在线、轻量的采样机制。

## 方法核心

- 训练目标不变，仍是标准 minibatch SGD（含 AdaGrad/RMSprop/Adam 变体）的经验风险最小化（第 3.1 节，公式无编号）。
- 核心概率函数（式 1，第 4 页）：
  $$P(\mathcal{L}(f_w(x_i),y_i)) = [\mathrm{CDF}_R(\mathcal{L}(f_w(x_i),y_i))]^\beta$$
  其中 $\mathrm{CDF}_R$ 是最近 $R$ 个样本损失的经验分布（用有界队列/deque 实现），$\beta>0$ 控制选择性强弱：$\beta$ 越大越偏向高损失样本；$\beta=0$ 时所有样本保留概率恒为 1，退化为标准 minibatch SGD（第 4 页 3.2 节正文）。
- Algorithm 1（第 4 页）：每个 epoch 遍历打乱后的全部样本，对每个样本做前向传播算损失，按 $P(\mathcal{L})$ 概率决定是否放入反传批次；凑够一个批次大小就执行一次反向传播并更新参数。
- Algorithm 2（第 4 页）：概率计算逻辑，用有界队列维护最近 $R$ 个损失形成经验 CDF，取该样本损失对应分位数的 $\beta$ 次方。
- 梯度相似性实验（第 4 页 3.2 节，图 5）：只用最高损失的 10% 样本计算的梯度，与全批次梯度相比，余弦相似度更高、超过 80% 权重的梯度符号与全批次一致，均优于随机子采样同等比例样本。
- Stale-SB 变体（第 4–5 页 3.3 节）：每 $n$ 个 epoch 才重新执行一次"用于选择的前向传播"（selection pass），中间 $(n-1)$ 个 epoch 复用上一次算出的损失来决定是否选中该样本；但被选中样本训练时仍需一次基于当前参数的前向传播（保证梯度不是基于陈旧参数计算）。$n=3$ 时把"选择用前向传播"耗时降低约三分之二（第 10 页 5.3 节）。
- 实现开销：SB 筛选逻辑本身（不含选择用前向传播）只占训练总时间约 3%（第 6 页第 4 节）。作者列出但未实现的优化方向：复用选择 pass 的激活避免重复前向、选择批次大小大于训练批次大小（第 6 页第 4 节"Future implementation optimizations"）。

## 实验结果

- Table 1（第 7 页）：达到 Traditional 最终误差的 1.1x/1.2x/1.4x 目标时，SB/Stale-SB/Kath18 相对 Traditional 的加速比。CIFAR10 上 SB 1.2–1.5x、Stale-SB 最高 2.0x；SVHN 上 SB 3.4–3.5x、Stale-SB 最高 5.0x；CIFAR100 上收益明显更小（SB 约 1.2x，Stale-SB 在 1.4x 误差目标下 1.6x，在 1.2x 目标下反而是 1.0x）。
- Stale-SB（$n=3$）平均比 SB 快 26%（Abstract；第 10 页 5.3 节）。
- Pareto 最优点占比（第 11 页 5.5 节）：CIFAR10/CIFAR100/SVHN 上 SB+Stale-SB 分别占 Pareto 前沿的 72%/47%/80%；Kath18 占 10%/8%/14%；Traditional 占 10%/43%/6%（大训练时间预算下 Traditional 反超）。
- 标签噪声鲁棒性（第 10 页 5.4 节，图 12）：CIFAR10 人为翻转 1%、10% 标签时 SB 仍加速且最终精度相当；翻转 20% 时 SB 会过拟合到错误标签，最终测试误差上升——原文措辞是"SB is robust to modest amounts of label error"，但"most effective on relatively clean, validated datasets"。
- 选择性 β 的权衡（第 10 页 5.4 节，图 13）：更高选择性加速训练但可能提高最终误差；CIFAR10 在 20% 选择率下与 Traditional 最终误差相差 0.92%，CIFAR100 在 25% 选择率下相差 2.54%。全文观察到的有效选择率区间是 20–65%。
- 硬件相关背景数据（附录 A.4，第 14 页）：在多种 GPU（K20、GTX-1070、TitanV）上，反传耗时最多为前传的 2.5 倍。

## 我的理解

SB 的关键洞察是"hinge loss 式直觉"：损失接近零的样本梯度范数也小，对参数更新贡献有限，所以可以用前向损失（比反传便宜得多）做代理，概率性跳过这些样本的反传。它不改变损失函数或优化目标，只改变了"哪些样本参与本轮梯度估计"，本质是一种有偏但方差可控的在线重要性采样，通过实验（余弦相似度、符号一致率）而非解析证明来支持"跳过低损失样本影响很小"这一假设。Stale-SB 进一步把"判断值不值得反传"这件事本身的开销也降下来，用的是"隔几步复用一次判断结果"的思路。

## 与本课题（BER 训练效率／第四章候选）的关系

### 论文原结论
- SB 是启发式、概率性的样本级采样：跳过的样本梯度并非精确为零，只是被赋予较低的选中概率，理论上仍可能被选中；论文没有给出梯度精确为零的解析证明，"suppressing gradient updates for low-loss examples has surprisingly little impact"是实验观察（第 4 页图 5），不是定理。
- 作用粒度是整个训练样本（跳过则该样本完全不参与本轮反传），不是网络内部某个算子、某组张量或某类实体。

### 本课题推论（原文未给出，本课题基于原文外推）
- SB"用前向代理判断是否值得反传"的直觉与候选一 ASB（活动集稀疏反传）表面相似，但机制性质完全不同：ASB 依赖 CVaR hinge 在非活动集上梯度**解析精确为零**（可用 `torch.equal` 逐位核验 `loss`/`xi.grad`/`g_rank` 相等），是等价重写；SB 是近似采样，跳过样本的梯度只是"贡献小"，不是"为零"。二者不能共享同一份"精确等价"证据，若 BER 排序头引入类似 SB 的近似跳过机制，必须单独做收敛性与最终指标的消融，不能援引 ASB 的精确等价论证来豁免这类实验——本条为本课题推论，原文未涉及。
- Stale-SB 的"降低选择开销"思路（复用前几步的判断结果，隔 n 步才刷新）对候选一/二中"每步都要重新判断哪些实体处于活动集/需要梯度"这一开销，是可类比的降频思路：若活动集判断本身有不可忽视的代价，可以考虑隔若干训练步复用一次活动集划分。但这是本课题外推，原文只在样本级选择场景验证过，未在梯度稀疏化或激活重计算场景验证，效果未知。

### 可迁移机制
- "用前向代理（损失/分位数）替代精确判据来降低决策开销"这一设计模式本身可迁移，但迁移后必须重新证明代理判据与真实判据（如精确活动集）的一致性，不能默认成立。

### 不可直接声称的内容
- 不能声称"跳过低损失样本对最终精度零代价"：原文在 20% 标签噪声、或选择性 β 较大时均报告了精度损失（第 10 页 5.4 节）；且 CIFAR100（类别多、每类样本少，冗余度低）上收益明显小于 CIFAR10/SVHN，暗示数据集/任务冗余度决定收益上限。BER 中实体级正负样本的冗余度未知，不能直接套用 CIFAR 系列结论估计收益。
- 不能声称该方法已在 Transformer/大模型或本课题的 CVaR-pAUC 排序损失场景中验证过——原文全部实验为图像分类 CNN（Wide ResNet、ResNet18、DenseNet、MobileNetV2），未覆盖排序损失或序列模型。

### 仍需实验验证的假设
- Stale-SB 式"降频判断"应用到 BER 排序头的活动集/梯度判断上，能否保持近似等价的最终指标——待验证。
- SB 的"跳过样本"策略若用于跳过 BER 中损失接近零的负实体（而非整条训练样本），是否会像候选一那样引发优化轨迹偏移——待验证。

## 与相关工作的关系

本文与 Katharopoulos & Fleuret (2018) 的在线重要性采样、Loshchilov & Hutter (2015) 的 online batch selection、Lin et al. (2017) 的 focal loss、Shrivastava et al. (2016) 的 hard example mining 同属"按难度/损失重加权训练样本"谱系（第 2 节 Related Work，第 356 行前后引用列表）。与本课题内 [[2014-Ogawa-SVM安全样本筛选]] 的关系是对照：后者对"可安全丢弃的样本"给出解析可证明的判据，前者只给出启发式经验证据，二者代表"可证明筛除"与"启发式采样"两类不同保证强度的样本级加速手段。

## 疑问 / 待验证

- 论文未报告 SB 在 Transformer / 序列模型 / 排序损失上的行为，是否存在与 CNN 分类任务不同的失效模式，原文未涉及。
- β 的最优值高度依赖数据集与目标误差（第 10 页），迁移到新任务前需要重新调参，原文未给出可迁移的选β经验法则。

## 原始摘要

> This paper introduces Selective-Backprop, a technique that accelerates the training of deep neural networks (DNNs) by prioritizing examples with high loss at each iteration. Selective-Backprop uses the output of a training example's forward pass to decide whether to use that example to compute gradients and update parameters, or to skip immediately to the next example. By reducing the number of computationally-expensive backpropagation steps performed, Selective-Backprop accelerates training. Evaluation on CIFAR10, CIFAR100, and SVHN, across a variety of modern image models, shows that Selective-Backprop converges to target error rates up to 3.5x faster than with standard SGD and between 1.02–1.8x faster than a state-of-the-art importance sampling approach. Further acceleration of 26% can be achieved by using stale forward pass results for selection, thus also skipping forward passes of low priority examples.

## 文献信息

- arXiv:1910.00762 [cs.LG]
- 原件：`raw/papers/methodology/training-efficiency/2019-Jiang-Selective-Backprop-Biggest-Losers.pdf`
- 代码：https://bit.ly/SelectiveBackpropAnon（第 1 页摘要末尾、第 12 页 A.1）
