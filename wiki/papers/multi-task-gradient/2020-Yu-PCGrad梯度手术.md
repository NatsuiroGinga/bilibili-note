---
title: "Gradient Surgery for Multi-Task Learning"
authors:
  - Tianhe Yu
  - Saurabh Kumar
  - Abhishek Gupta
  - Sergey Levine
  - Karol Hausman
  - Chelsea Finn
year: 2020
date: 2026-09-02
journal: "Advances in Neural Information Processing Systems 33 (NeurIPS 2020)"
source_pdf: "[[raw/papers/multi-task-gradient/arxiv-2001.06782.pdf]]"
doi: "10.48550/arxiv.2001.06782"
tags:
  - 类型/论文
  - 主题/多任务学习
  - 主题/梯度冲突
  - 主题/梯度手术
aliases:
  - PCGrad
  - Yu2020-GradientSurgery
key_finding: "PCGrad 提出“悲剧三要素”（梯度冲突、梯度主导、高曲率）作为多任务优化困难的成因假说，并用梯度手术（把冲突任务的梯度投影到另一任务梯度的法平面上）同时改变梯度方向与幅值；论文的严格收敛定理（定理 1、2、3、4）全部限定在两任务设定，非凸/多任务设定只有实验证据。论文 2.3 节散文公式的投影分母与算法 1 第 7 行不一致，笔记按要求誊录两处原文而不擅自统一。"
method: "两两梯度余弦相似度检测冲突，冲突时把一个任务梯度投影到另一任务梯度的法平面上（梯度手术），随机顺序遍历批次中出现的其他任务"
baseline: "等权重、不确定性加权、DWA、Cross-Stitch、MTAN、GradNorm、Sener & Koltun (MGDA-UB)、routing networks、独立训练、CosReg"
---

# Gradient Surgery for Multi-Task Learning

> Yu, Kumar, Gupta, Levine, Hausman, Finn，2020，NeurIPS 2020（正文 8 页 + 广泛附录 A–J，提取文本共约 700+ 行）。

## 一句话

论文假设多任务优化困难源于"悲剧三要素"——梯度冲突（余弦相似度为负）、梯度幅值差异过大（一个任务主导更新）、以及优化地形高曲率——三者共现时会导致主导任务的改善被高估、被主导任务的退化被低估；PCGrad 用"梯度手术"直接改写梯度：当两个任务梯度冲突时，把其中一个投影到另一个的法平面上，同时改变梯度的方向与幅值，且该操作与具体模型架构和优化器无关。

## 问题定义与记号

多任务学习目标为 $\min_\theta\mathbb E_{\mathcal T_i\sim p(\mathcal T)}[\mathcal L_i(\theta)]$，记多任务损失 $\mathcal L(\theta)=\sum_i\mathcal L_i(\theta)$，各任务梯度 $\mathbf g_i=\nabla\mathcal L_i(\theta)$（2.1 节正文，无编号）。

## 方法核心

### 悲剧三要素的形式化定义（2.2 节）

**Definition 1**（冲突梯度）：记 $\phi_{ij}$ 为两任务梯度 $\mathbf g_i,\mathbf g_j$ 的夹角，当 $\cos\phi_{ij}<0$ 时称两梯度冲突。

**Definition 2**（梯度幅值相似度）：

$$
\Phi(\mathbf g_i,\mathbf g_j)=\frac{2\|\mathbf g_i\|_2\|\mathbf g_j\|_2}{\|\mathbf g_i\|_2^2+\|\mathbf g_j\|_2^2}
$$

幅值相等时该值为 1，幅值差异越大越趋近 0。

**Definition 3**（多任务曲率）：

$$
\mathbf H(\mathcal L;\theta,\theta')=\int_0^1\nabla\mathcal L(\theta)^\top\nabla^2\mathcal L\big(\theta+a(\theta'-\theta)\big)\nabla\mathcal L(\theta)\,da
$$

即 $\mathcal L$ 沿多任务梯度方向从 $\theta$ 到 $\theta'$ 之间的平均曲率；当该量大于某个大正常数 $C$ 时，论文称该处优化地形为"高曲率"。

### PCGrad 更新规则（2.3 节，Algorithm 1 完整誊录）

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 PCGrad Update Rule
Require: Model parameters θ, task minibatch {T_k}
1: g_k ← ∇_θ L_k(θ) ∀k
2: g_k^PC ← g_k ∀k
3: for T_i ∈ B do
4:   for T_j uniformly ∼ B\T_i in random order do
5:     if g_i^PC · g_j < 0 then
6:       // Subtract the projection of g_i^PC onto g_j
7:       Set g_i^PC = g_i^PC − (g_i^PC·g_j / ||g_j||^2) g_i
8: return update Δθ = g^PC = Σ_i g_i^PC
</div>

**提取文本原样核验说明（重要，按证据纪律逐字誊录，不擅自修正）**：
1. **论文自身的公式不一致**（题目要求必须记录的一例）：正文 2.3 节的散文描述给出的投影公式是
   $$
   \mathbf g_i=\mathbf g_i-\frac{\mathbf g_i\cdot\mathbf g_j}{\|\mathbf g_i\|^2}\mathbf g_j
   $$
   分母为 $\|\mathbf g_i\|^2$；而 Algorithm 1 第 7 行的分母是 $\|\mathbf g_j\|^2$。几何上，"把 $\mathbf g_i$ 投影到 $\mathbf g_j$ 的法平面"对应的标准投影公式应使用 $\|\mathbf g_j\|^2$ 作分母（减去 $\mathbf g_i$ 在 $\mathbf g_j$ 方向上的分量），即算法框的写法在几何上正确，散文公式的分母有误。
2. **本次提取文本另有一处可能的转录瑕疵，与上述作者原文不一致是两回事**：Algorithm 1 第 7 行末尾变量在提取文本中写作 "$g_i$"（即 "... − (g_i^PC·g_j / ‖g_j‖²) gi"），但按注释"Subtract the projection of $g_i^{PC}$ onto $g_j$"及标准投影公式，被减去的应是 $\mathbf g_j$ 的倍数而非 $\mathbf g_i$ 本身。该行在原文中以纯文本表格（非结构化算法框）形式被提取，怀疑是 PDF 转 Markdown 过程中的下标丢失，**本笔记不能排除此为提取误差，也不能排除是原文另一处印刷问题**，只如实记录提取文本的字面内容，不代入原文影印核验。

论文正文用自然语言重申了以 $\mathbf g_j$ 为法平面基准的版本："we replace $\mathbf g_i$ by its projection onto the normal plane of $\mathbf g_j$"，随后遍历批次中出现的所有其他任务，得到 $\mathbf g_i^{\mathrm{PC}}$；未冲突时梯度不变。

### 理论分析的记号（2.4 节）

**Definition 4**：两任务目标 $\mathcal L(\theta)=\mathcal L_1(\theta)+\mathcal L_2(\theta)$，$\mathbf g_1=\nabla\mathcal L_1$，$\mathbf g_2=\nabla\mathcal L_2$，$\mathbf g=\mathbf g_1+\mathbf g_2$。

**Definition 5**（多任务曲率界定量 $\xi$）：提取文本在此处出现明显的排版错乱（"$\xi(\mathbf g_1,\mathbf g_2)=0$" 后紧跟单独一行 "$\cos^2\phi_{12})\frac{\|\mathbf g_1-\mathbf g_2\|_2^2}{\|\mathbf g_1+\mathbf g_2\|_2^2}$"），按其余上下文（Theorem 2 条件 (b) 中 $\xi(\mathbf g_1,\mathbf g_2)\le1$ 的用法）可推断其数学含义为：

$$
\xi(\mathbf g_1,\mathbf g_2)=(1-\cos^2\phi_{12})\,\frac{\|\mathbf g_1-\mathbf g_2\|_2^2}{\|\mathbf g_1+\mathbf g_2\|_2^2}
$$

**本次提取未能确认该式开头系数是否确为 "1−"，标注为待核验，不作为确定原文誊录**，仅作为理解 Theorem 2 的辅助。

## 理论保证及其假设

论文的所有严格收敛定理都限定在**两任务设定**（Definition 4），非凸或多任务（$T>2$）情形只有实验证据，没有对应定理。

**Theorem 1**（2.4 节，凸情形收敛性；证明见附录 A.1）：假设 $\mathcal L_1,\mathcal L_2$ 凸且可微，$\mathcal L$ 的梯度 $L$-Lipschitz（$L>0$）。则步长 $t\le1/L$ 的 PCGrad 更新规则收敛到以下两者之一：(1) 优化地形中 $\cos(\phi_{12})=-1$ 的位置，或 (2) 最优值 $\mathcal L(\theta^\ast)$。

- **该定理没有保证什么**：情形 (1) 是一个可能的次优收敛点——当两任务梯度方向恰好完全相反（$\cos\phi_{12}=-1$）时，PCGrad 投影后梯度为零，更新停滞。论文正文承认这一点，并辩称由于 SGD 的噪声估计使得 minibatch 梯度余弦相似度精确等于 $-1$ 的概率很低，但也承认"理论上若 $\cos\phi_{12}$ 长期徘徊在 $-1$ 附近，收敛可能变慢"，只是"实践中未观察到"（引用附录 B 的分任务学习曲线作为经验支持，不是理论排除）。
- **前提假设**：$\mathcal L_1,\mathcal L_2$ 凸且可微；深度网络（包括本课题的 FT-Transformer 骨干）训练目标通常非凸，该定理的凸性前提在实际应用中不成立，只能作为"合理性检验"（论文原话："verify that the PCGrad update corresponds to a sensible optimization procedure under simplifying assumptions"），不能作为深度网络训练的收敛保证。

**Theorem 2**（2.4 节，单步损失下降的充分条件；证明见附录 A.2）：假设 $\mathcal L$ 可微且梯度 $L$-Lipschitz，$\theta^{MT}$、$\theta^{PCGrad}$ 分别为标准多任务梯度 $\mathbf g$ 和 PCGrad 修正梯度 $\mathbf g^{PC}$ 做一步更新（步长 $t>0$）后的参数，并假设多任务曲率下界 $\mathbf H(\mathcal L;\theta,\theta^{MT})\ge\ell\|\mathbf g\|_2^2$（常数 $\ell\le L$）。则当以下三条同时成立时 $\mathcal L(\theta^{PCGrad})\le\mathcal L(\theta^{MT})$：(a) $\cos\phi_{12}\le-\Phi(\mathbf g_1,\mathbf g_2)$；(b) $\ell\ge\xi(\mathbf g_1,\mathbf g_2)L$；(c) $t\ge\dfrac{2}{\ell-\xi(\mathbf g_1,\mathbf g_2)L}$。

论文将这三条直接对应悲剧三要素：(a) 冲突程度与幅值差异需要同时足够大；(b) 曲率需要足够大；(c) 学习率需要足够大以体现高曲率带来的性能高估/低估。

- **该定理没有保证什么**：只是"单步更新后损失下降"的**充分条件**，不是必要条件，也不是多步训练收敛到最优的保证；曲率下界假设 $\ell\le L$ 本身依赖问题结构，论文没有给出如何独立验证 $\ell$ 是否存在的构造性方法，实验中只用 Taylor 展开数值估计曲率（5.3 节公式 $\mathbf H(\mathcal L;\theta^t,\theta^{t+1})=2[\mathcal L(\theta^{t+1})-\mathcal L(\theta^t)-\nabla_{\theta^t}\mathcal L(\theta^t)^\top(\theta^{t+1}-\theta^t)]$）作为事后诊断，不是训练前可验证的假设。

**Theorem 3**（附录 A.3，充要条件）：论文声明在 Theorem 2 的充分条件之外，进一步给出 PCGrad 单步损失下降的**充分且必要条件**。**提取文本核验限制**：本次核验只确认了 Theorem 3 的前提陈述（与 Theorem 2 相同的可微、Lipschitz、曲率下界假设），条件本身的具体不等式在提取文本中因跨行截断未被完整捕获，**笔记不据此臆造具体条件表达式**，只记录该定理存在且位于附录 A.3。

**Theorem 4**（附录 A.4，动量方法下的收敛性）：假设 $\mathcal L_1,\mathcal L_2$ 分别是 $\mu_1$-、$\mu_2$-强凸且 $L_1$-、$L_2$-光滑（$\mu_1,\mu_2,L_1,L_2>0$），定义逐迭代的夹角 $\phi_{12}^k$、幅值比 $R_k=\|\mathbf g_1(\theta_k)\|/\|\mathbf g_2(\theta_k)\|$ 及相应的加权强凸常数 $\mu_k$、光滑常数 $L_k$。则采用重球法（heavy ball method）、按特定步长 $\alpha_k$ 与动量系数 $\beta_k$ 公式的 PCGrad 更新会线性收敛到 (1) $\cos(\phi_{12}^k)=-1$ 的位置或 (2) 最优值 $\mathcal L(\theta^\ast)$。

- **该定理没有保证什么**：强凸假设比 Theorem 1 的普通凸性更强，深度网络几乎必然不满足；且该定理针对的是经典重球动量法，不直接覆盖论文实验中实际使用的 Adam 优化器（论文正文承认 PCGrad 可与 Adam 结合使用，但 Adam 场景下的收敛性没有对应定理，只有实验验证）。

## 计算开销

- 论文明确说明监督学习场景下的实现方式（3 节正文）：先对当前批次中出现的每个任务预计算梯度 $\nabla_\theta\mathcal L_i(\theta)$（即标准的逐任务反向传播，数量等于批次中出现的任务数），并预计算所有梯度两两之间的余弦相似度；随后**梯度手术本身完全基于这些已预计算好的梯度向量做投影运算，不需要重新计算任务梯度，也不需要对网络做额外反向传播**（原文："we can obtain the PCGrad update by following Algorithm 1, without re-computing task gradients nor backpropagating into the network"）。
- 因此 PCGrad 的额外开销主要是 $O(T^2)$ 次梯度向量间的点积与范数计算（$T$ 为批次中出现的任务数），相对反向传播成本可忽略；但仍然需要 $T$ 次独立反向传播来获得逐任务梯度，这一点与 MGDA 的无近似版本相同，不具备 MGDA-UB 式的单次反向传播优势。
- **全文核验：未发现任何 wall-clock 训练时间或显存开销的定量报告**（已用关键词 "backward pass" "backprop" "computational cost" "compute overhead" "wall-clock" "runtime" "extra computation" 检索提取文本，除上述定性描述外未命中其他数字）。方法被称为"model-agnostic"且"只需修改梯度应用步骤"，但这是定性设计声明，不是实测数字。

## 实验与基线

- **基线集合**：等权重、Kendall 等 (2018) 不确定性加权、DWA（动态权重平均）、Cross-Stitch、MTAN、GradNorm（Chen 等）、Sener & Koltun（MGDA-UB）、routing networks + WPL、独立训练、CosReg（Suteu & Guo，把梯度余弦相似度正则化到 0）。
- **NYUv2 三任务**（Table 1，分割/深度/表面法向量）：MTAN + PCGrad（不确定性加权）取得 mIoU 20.17、像素准确率 56.65、深度绝对误差 0.5904、相对误差 0.2467、法向量角度均值 30.01/中位数 24.83，在与 Cross-Stitch、MTAN 各三种加权方案的对比中，MTAN+PCGrad 在 9 项指标（3 任务 × 3 类指标）中的 8 项取得最优。
- **CIFAR-100（20 任务，Table 2）**：PCGrad 单独使用达到 71% 准确率，优于 task-specific（42%/49%）、cross-stitch（53%）、独立训练（67.7%）；与 routing networks + WPL 结合后达到 77.5%，比单独 routing + WPL（74.7%）提升 2.8 个绝对百分点。
- **CelebA（40 任务，Table 3）**：PCGrad 平均分类误差 8.69，优于 Sener & Koltun（MGDA-UB）的 8.95。
- **MultiMNIST（附录 E，Table 4）**：PCGrad 相对 Sener & Koltun 在左/右数字分类准确率上分别提升 0.13% 和 0.55%（论文原话给出的是相对提升百分比，未在提取文本中给出两方法各自的绝对准确率数值，笔记不代入猜测的绝对值）。
- **CityScapes（附录 E，Table 5）**：PCGrad + MTAN 在四项指标中的三项优于 MTAN，并在语义分割的 mIoU 和像素准确率两项都取得最优（具体数值未在本次提取的正文摘录范围内，需要查表格原始数字时应另行核验 Table 5/7）。
- **Meta-World 多任务强化学习（MT10/MT50，5.2 节）**：PCGrad + SAC 以最佳数据效率学完全部任务，在 MT10 中解决全部 10 个任务，在 MT50 中解决约 70% 的任务；单一 SAC 策略和多头策略均无法学会一半以上任务；独立训练的 SAC 智能体虽最终能解决全部/约 70% 任务，但比 PCGrad + SAC 分别多需要约 200 万（MT10）和 1500 万（MT50）样本。摘要与引言中称"在多任务强化学习问题上取得超过 30% 的绝对提升"。
- **消融实验（Figure 3 最右图）**：分别只保留 PCGrad 修正的梯度方向、只保留修正的梯度幅值两种变体，均劣于完整 PCGrad；仅幅值变体的表现与 GradNorm 相近，论文据此论证"必须同时修改方向与幅值"。
- **悲剧三要素的经验验证**（5.3 节，Figure 4）：在 Meta-World 的 reach 与 press-button-top 两任务上，训练全程多任务曲率保持正值且递增（支持 Theorem 2 条件 (b) 的曲率下界在经验上成立）；条件 (a)（冲突）在任务 2 尚未学会时高频成立，PCGrad 开始学会任务 2 后，条件 (a) 成立比例随之下降——论文将此解读为"悲剧三要素是 PCGrad 在实践中带来性能增益的决定性因素"这一结论的支持证据，但这是相关性观察，不是因果证明。

## 与本课题的关系

本课题为跨年度加密恶意流量检测，第三章用 FT-Transformer 骨干（924,283 参数），训练目标为逐流 BCE 与多预算 CVaR-pAUC 排序损失之和，二者共享同一套骨干参数。

**可迁移**：
- 本课题恰好是**两损失**场景，而 PCGrad 论文的全部严格定理（Theorem 1–4）都专门针对两任务设定（Definition 4），这是本文献相对 MGDA、GradNorm 而言与本课题理论适配度最高的一点——不需要像多任务（$T>2$）场景那样只能依赖实验证据，可以直接对照两任务定理的假设逐条核验适用性。
- Algorithm 1 在两任务下高度简化：批次中每个任务只有一个"其他任务"可比较，不需要随机顺序遍历多个任务，工程实现比论文描述的通用多任务版本更简单。
- Theorem 2 提供的诊断框架（条件 a：冲突程度是否足够大；条件 b：曲率是否有下界；条件 c：学习率是否足够大）可直接迁移为本课题的**实验诊断协议**：在真实训练轨迹中估计 BCE 与 CVaR-pAUC 梯度的余弦相似度分布、用论文式的 Taylor 展开曲率估计公式（5.3 节）估计多任务曲率，判断"悲剧三要素"是否在本课题的训练动态中同样出现，这是可执行、可证伪的最小实验，而非空想。
- 消融结论（必须同时改变方向与幅值，仅调幅值效果接近 GradNorm）为本课题提供了一个可比较的候选设计维度：若后续要在 GradNorm（只调幅值）与 PCGrad（方向+幅值）之间选择，可复现该消融的思路，在真实两损失设置上重新验证，而不是照搬论文在视觉/强化学习任务上的结论。

**不可直接声称**：
- Theorem 1 需要 $\mathcal L_1,\mathcal L_2$ 凸，Theorem 4 需要强凸+光滑；FT-Transformer 骨干上的 BCE 与 CVaR-pAUC 损失关于骨干参数几乎必然非凸，因此论文的收敛定理不能作为本课题训练收敛性的理论保证，只能作为"合理性检验"的参照（这也是论文自己对 Theorem 1 的定位）。
- Theorem 2 的曲率下界假设 $\ell\le L$ 及其具体取值，论文没有给出可在训练前独立验证的构造性方法，只能训练中事后估计；本课题若要引用该定理判断"PCGrad 单步下降"，必须先做经验测量，不能预先假定条件成立。
- 论文全部监督学习实验（MultiMNIST、CIFAR-100、CelebA、NYUv2、CityScapes）损失类型为交叉熵、MSE、余弦损失，强化学习实验为策略梯度/SAC，均未出现排序损失（如 CVaR-pAUC）与二分类损失的组合，PCGrad 在该组合下的效果需要本课题实测，不能从视觉/强化学习任务结果外推。
- 论文的性能提升数字（CIFAR-100、CelebA、NYUv2、Meta-World 各项）均来自特定网络架构与数据集组合，不能直接作为本课题预期收益的定量参照。

## 局限与不可外推结论

- 论文声明的两处理论/实现不一致（2.3 节散文分母 $\|\mathbf g_i\|^2$ vs Algorithm 1 分母 $\|\mathbf g_j\|^2$）已按要求记录；几何上正确的是算法框的写法，实现该方法时应以 Algorithm 1（及正文对"投影到 $\mathbf g_j$ 法平面"的自然语言描述）为准，不应照抄 2.3 节散文公式。
- Definition 5（$\xi$ 的定义）在本次提取文本中存在排版错乱，笔记给出的复原表达式属于**推断**，不是确认无误的原文誊录，引用该式前应查阅原始 PDF 图像核实。
- Theorem 3 的具体充要条件未能从提取文本完整获取，笔记只确认其存在于附录 A.3，不据此展开论证。
- 论文的所有强收敛保证限定在两任务凸/强凸情形，多任务（$T>2$）和非凸情形只有实验支持，不能把两任务定理的结论直接套用到多任务场景，即使本课题当前只有两个损失，未来若扩展为三个及以上损失，需要重新评估哪些理论保证仍然适用。
- 论文未报告任何计算开销的定量数字，因此"model-agnostic 且开销可忽略"是论文的定性设计目标陈述，不是实测证据，本课题若要论证 PCGrad 的工程成本可接受，需要独立计时。

## 文献信息

- arXiv：https://arxiv.org/abs/2001.06782
- DOI：10.48550/arxiv.2001.06782
- 提取全文：`/tmp/mtl-pdf-extract/arxiv-2001.06782.md`（会话临时目录，非仓库内容）
