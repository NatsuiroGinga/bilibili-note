---
title: "Large-scale Robust Deep AUC Maximization: A New Surrogate Loss and Empirical Studies on Medical Image Classification"
authors:
  - Zhuoning Yuan
  - Yan Yan
  - Milan Sonka
  - Tianbao Yang
year: 2021
date: 2026-09-02
journal: "arXiv 预印本 2012.03173；提取文本参考文献 [42] 显示同课题组后续工作发表于 ICML 2021，本文自身的会议/期刊接收信息在提取文本中未见，出处未核验（文件名与 raw/ 目录暗示可能对应 ICCV 2021 版本，见文中代码仓库链接 `ICCV2021_DeepAUC`，但未见正文明确写出）"
source_pdf: "[[raw/papers/multi-task-gradient/arxiv-2012.03173.pdf]]"
doi: "10.48550/arxiv.2012.03173"
tags:
  - 类型/论文
  - 主题/AUC优化
  - 主题/排序损失
  - 主题/极小极大优化
  - 主题/类别不平衡
aliases:
  - DAM
  - AUC-Margin-Loss
  - Yuan2021-DeepAUCMax
  - PESG
key_finding: "本文提出 AUC min-max-margin 代理损失（简称 AUC margin loss，式 6），用带非负约束 α≥0 的合页函数替换已有 AUC square loss 中对齐正负类均值的平方项，证明其与一个极小极大问题严格等价（Theorem 1，附录 C 给出完整证明）。该改动在理论上（附录 D/E 的梯度分析）和实证上都缓解了 AUC square loss 的两个缺陷——对易分样本的负面梯度效应、对噪声标签的敏感性；用同一套 PESG 算法在 CheXpert 竞赛取得 2020-08-31 排行榜第一名（AUC 0.9305），在 Kaggle Melanoma 竞赛单模型上超过冠军队单模型。本文不含对 PESG 优化算法本身的收敛性证明，收敛性分析明确引用另外两篇论文（[15,28]）。"
method: "把 AUC square loss 重新表达为三项之和 A1+A2+A3（式 5，用凸共轭技巧 s²=max_α 2αs−α²），其中 A3 是一个平方项，用非负约束下的合页函数 max_{α≥0}{2α(m−a+b)−α²}=(m−a+b)²₊ 替换 A3 得到 AUC margin loss（式 6）；证明该损失与一个极小极大问题（式 7/8）严格等价（Theorem 1），沿用已有的 PESG（proximal epoch stochastic method）随机原始-对偶算法求解，只需把对偶变量 α 的更新加一个投影到非负象限的步骤"
baseline: "交叉熵损失（CE）、Focal loss、AUC square loss（AUC-S）；在 CheXpert 上另与 Stanford Baseline、YWW（弱监督病灶定位）、Hierarchical Learning（领域知识病灶层级）比较；在 Melanoma 竞赛上与冠军队方案比较"
---

# Large-scale Robust Deep AUC Maximization

> Yuan, Yan, Sonka, Yang，2021，arXiv:2012.03173（提取文本共 603 行，正文 1–6 节 + 参考文献 + 附录 A–H）。

## 一句话

AUC margin loss 用带非负约束的合页函数替换 AUC square loss 中"正负类均值差"这一项的平方形式，证明该替换后的损失与一个极小极大问题严格等价（Theorem 1），从而可以复用已有的可扩展随机原始-对偶算法（PESG），同时缓解了 AUC square loss 对易分样本产生负面梯度、对噪声标签过度敏感这两个已被本文用一维算例形式化揭示的缺陷。

## 问题定义与记号

训练集 $\mathcal S=\{(\mathbf x_1,y_1),\ldots,(\mathbf x_n,y_n)\}$，$y_i\in\{1,-1\}$，$h_{\mathbf w}(\mathbf x)$ 为待学习的神经网络预测。AUC 定义为正样本预测得分高于负样本的概率（式 1）：

$$
\mathrm{AUC}(\mathbf w)=\Pr(h_{\mathbf w}(\mathbf x)\ge h_{\mathbf w}(\mathbf x')\mid y=1,y'=-1)\tag{1}
$$

直接优化基于指示函数的定义不可微，常见做法是用凸代理损失 $\ell$ 替换指示函数，得到逐对（pairwise）目标（式 2）：

$$
\min_{\mathbf w\in\mathbb R^d}\frac1{N_+N_-}\sum_{\mathbf x\in\mathcal S_+}\sum_{\mathbf x'\in\mathcal S_-}\ell(h_{\mathbf w}(\mathbf x)-h_{\mathbf w}(\mathbf x'))\tag{2}
$$

该式复杂度 $O(n^2)$（$O(n^2)$ 个正负样本对），不可扩展到大规模数据。

## 方法核心

### 3.1 节：AUC square loss 及其极小极大等价形式

已有工作（Ying 等 [41]）用平方损失 $\ell(h_{\mathbf w}(\mathbf x)-h_{\mathbf w}(\mathbf x'))=(1-h_{\mathbf w}(\mathbf x)+h_{\mathbf w}(\mathbf x'))^2$ 作代理损失，并证明其等价于极小极大问题（式 3）：

$$
\min_{\substack{\mathbf w\in\mathbb R^d\\(a,b)\in\mathbb R^2}}\max_{\alpha\in\mathbb R}f(\mathbf w,a,b,\alpha):=\mathbb E_{\mathbf z}[F(\mathbf w,a,b,\alpha;\mathbf z)]\tag{3}
$$

其中（式 4，$p=\Pr(y=1)$）：

$$
\begin{aligned}
F(\mathbf w,a,b,\alpha;\mathbf z)={}&(1-p)(h_{\mathbf w}(\mathbf x)-a)^2\mathbb I_{[y=1]}+p(h_{\mathbf w}(\mathbf x)-b)^2\mathbb I_{[y=-1]}-p(1-p)\alpha^2\\
&+2\alpha\big(p(1-p)+ph_{\mathbf w}(\mathbf x)\mathbb I_{[y=-1]}-(1-p)h_{\mathbf w}(\mathbf x)\mathbb I_{[y=1]}\big)
\end{aligned}\tag{4}
$$

该目标在样本上可分解（不需要显式构造正负样本对），从而可用高效的原始-对偶随机算法求解，扩展到数十万样本规模。

### 3.2 节：AUC square loss 的两个缺陷（形式化分析）

论文用一维/线性模型场景下的随机梯度更新推导，逐字论证两个缺陷：

**对易分样本的负面效应**：给定一对易分正负样本（$h_{\mathbf w}(\mathbf x)-h_{\mathbf w}(\mathbf x')>1$），平方损失的随机梯度更新为 $\mathbf w_+=\mathbf w-\eta2(1-h_{\mathbf w}(\mathbf x)+h_{\mathbf w}(\mathbf x'))(-\mathbf x+\mathbf x')$；由于此时 $1-h_{\mathbf w}(\mathbf x)+h_{\mathbf w}(\mathbf x')<0$，更新会把正样本得分推低、负样本得分推高，**恶化**分类能力（3.2 节，附录 D 给出极小极大形式下的等价分析）。

**对噪声标签的敏感性**：给定一对标签被翻转的样本（真实正样本被标为负、真实负样本被标为正），论文推导出对应的 SGD 更新式，证明当预测已经"足够自信"（$h_{\mathbf w}(\mathbf x)$ 足够大或 $h_{\mathbf w}(\mathbf x')$ 足够小）时，更新会把参数朝错误方向移动（3.2 节）。

### 3.3 节：AUC margin loss 的构造

论文先用凸共轭技巧 $s^2=\max_\alpha2\alpha s-\alpha^2$ 把 AUC square loss 重写为三项之和（式 5，推导见附录 B）：

$$
A_S(\mathbf w)=\underbrace{\mathbb E[(h_{\mathbf w}(\mathbf x)-a(\mathbf w))^2\mid y=1]}_{A_1(\mathbf w)}+\underbrace{\mathbb E[(h_{\mathbf w}(\mathbf x')-b(\mathbf w))^2\mid y'=-1]}_{A_2(\mathbf w)}+\underbrace{(1-a(\mathbf w)+b(\mathbf w))^2}_{A_3(\mathbf w)}\tag{5}
$$

$A_1,A_2$ 分别最小化正/负类预测得分的方差；$A_3$ 把正负类均值得分推远。论文指出 $A_3$ 中的平方形式正是两个缺陷的根源。解决方案：用带非负约束的合页函数替换 $A_3$：$\max_{\alpha\ge0}\{2\alpha(m-a(\mathbf w)+b(\mathbf w))-\alpha^2\}=(m-a(\mathbf w)+b(\mathbf w))_+^2$，$m$ 为margin超参数，得到 AUC margin loss（式 6）：

$$
A_M(\mathbf w)=A_1(\mathbf w)+A_2(\mathbf w)+\max_{\alpha\ge0}2\alpha(m-a(\mathbf w)+b(\mathbf w))-\alpha^2\tag{6}
$$

论文特别说明：若去掉 $\alpha\ge0$ 约束，该损失退化为带可调 margin 参数的平方损失（3.3 节段末）。

### Theorem 1（正文陈述，证明见附录 C，本笔记转录关键推导步骤）

> Minimizing the AUC margin loss (6) is equivalent to the following min-max optimization:
>
> $$
> \min_{\substack{\mathbf w\in\mathbb R^d\\(a,b)\in\mathbb R^2}}\max_{\alpha\ge0}\mathbb E_{\mathbf z}[F_M(\mathbf w,a,b,\alpha;\mathbf z)]\tag{7}
> $$
>
> 其中
>
> $$
> \begin{aligned}
> F_M(\mathbf w,a,b,\alpha;\mathbf z)={}&(1-p)(h_{\mathbf w}(\mathbf x)-a)^2\mathbb I_{[y=1]}+p(h_{\mathbf w}(\mathbf x)-b)^2\mathbb I_{[y=-1]}-p(1-p)\alpha^2\\
> &+2\alpha\big(p(1-p)m+ph_{\mathbf w}(\mathbf x)\mathbb I_{[y=-1]}-(1-p)h_{\mathbf w}(\mathbf x)\mathbb I_{[y=1]}\big)
> \end{aligned}\tag{8}
> $$

**证明要点（附录 C 完整推导，本笔记誊录关键步骤而非逐行公式）**：把式 8 的期望按正/负类条件期望展开，代入 $a,b$ 的最优值（$a=\mathbb E[h_{\mathbf w}(\mathbf x)\mid y=1]$，$b=\mathbb E[h_{\mathbf w}(\mathbf x)\mid y=-1]$，见附录 A 推导），得到

$$
\min_{a,b}\max_{\alpha\ge0}\mathbb E_{\mathbf z}[F_M]=\max_{\alpha\ge0}p(1-p)\Big[\mathbb E[(h_{\mathbf w}(\mathbf x)-a(\mathbf w))^2\mid y=1]+\mathbb E[(h_{\mathbf w}(\mathbf x)-b(\mathbf w))^2\mid y=-1]-\alpha^2+2\alpha(m+b(\mathbf w)-a(\mathbf w))\Big]
$$

对 $\alpha\ge0$ 取最大值即得 $p(1-p)A_M(\mathbf w)$，从而 $\min_{\mathbf w,a,b}\max_{\alpha\ge0}\mathbb E_{\mathbf z}[F_M(\mathbf w,a,b,\alpha;\mathbf z)]=p(1-p)A_M(\mathbf w)$，即极小极大问题的解与 AUC margin loss 的解相差一个正常数 $p(1-p)$，不影响 $\arg\min_{\mathbf w}$。

### 算法（Algorithm 1，PESG，正文完整誊录）

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 PESG for optimizing the AUC margin loss
Require: η, γ, λ, T
1: Initialize v_1, α_1 ≥ 0
2: for t = 1,...,T do
3:   Compute ∇_v F_M(v_t, α_t; z_t) and ∇_α F_M(v_t, α_t; z_t).
4:   Update primal variables
      v_{t+1} = v_t - η(∇_v F_M(v_t, α_t; z_t) + γ(v_t - v_ref)) - λη v_t
5:   Update α_{t+1} = [α_t + η ∇_α F_M(v_t, α_t; z_t)]_+
6:   Decrease η by a factor and update v_ref periodically
7: end for
</div>

$\mathbf v=(\mathbf w,a,b)$ 为全部原始变量；$\lambda$ 为标准权重衰减；$\gamma>0$ 为算法正则化参数（改善泛化）；$\mathbf v_{\mathrm{ref}}$ 是周期性用前一阶段（衰减学习率之前）$\mathbf v_t$ 的累积平均更新的参照解；对偶变量 $\alpha$ 的更新在梯度上升后投影到非负象限 $[\cdot]_+$。**论文明确说明该算法的收敛性分析不在本文内**（4 节末段原文："We refer the readers to [28, 15] for more discussion and convergence analysis of this algorithm"，[28] 为 Liu, Yuan, Ying, Yang 2019 arXiv:1908.10831，[15] 为 Guo, Yuan, Yan, Yang 2020 arXiv:2006.06889）。

### 3.4 节：两阶段训练框架

作者从初步实验观察到：直接从头优化 AUC margin loss 在简单数据集（CIFAR）上可行，但在复杂任务（CheXpert、Melanoma）上有困难，猜测原因是直接优化 AUC 学到的特征提取层不如先用交叉熵预训练；因此对困难医学影像任务采用两阶段框架：先用标准交叉熵预训练，再用 AUC 代理损失（随机初始化最后一层分类器）微调全部层。

## 理论保证及其假设

**唯一的形式化定理是 Theorem 1**，其保证内容严格限定为：**AUC margin loss（式 6）与极小极大问题（式 7/8）在最优值上相差一个正常数 $p(1-p)$ 的等价关系**——这是一个纯粹的**代数等价性证明**（不涉及统计一致性、泛化界或优化算法收敛性），依赖凸共轭恒等式 $s^2=\max_yy(2s-y)$ 及正负类独立性假设（附录 B 的 (e2) 步骤，"due to the independence of the positive and negative samples"）。

**该定理没有证明什么**：
- **不证明 PESG 算法收敛**——算法的收敛性分析被显式排除在本文之外，引用另外两篇论文 [15,28]；本笔记未核验该外部收敛性结论是否同样适用于 AUC margin loss（非凸-强凹）版本，还是仅针对 AUC square loss 版本证明。
- **不证明 AUC margin loss 是 AUC 分数的一致（consistent）代理损失**——论文没有给出统计一致性证明，只有经验证据（Figure 1 玩具例子、Table 1 等基准实验）。
- **不证明对噪声标签或易分样本的鲁棒性有量化界**——3.2/3.3 节及附录 D/E 的分析都是**具体数值算例下的梯度方向推导**（如 $\mathbf w=1$，$\mathbf x_1=1,\mathbf x_2=-1$，$a=0.5,b=-0.5$ 的一维算例），说明"在此特定场景下会/不会发生负面更新"，不是对任意数据分布成立的一般性鲁棒性界。
- 非负约束 $\alpha\ge0$ 与 margin 参数 $m$ 缓解两个缺陷的论证同样是**基于最优 $\alpha$ 取值的梯度符号分析**（3.3 节"Robust to Easy Data""Robust to Noisy Data"两段），不是形式化的鲁棒性定理。

## 计算开销

- AUC margin loss 与 AUC square loss 在可扩展性上"enjoy the same benefit"（3.3 节，两者都可分解到样本级、避免显式构造 $O(n^2)$ 样本对），论文强调"one line change of the code"即可从优化 AUC square loss 切换到 AUC margin loss（1 节引言）。
- Algorithm 1（PESG）每步只需计算原始变量 $\mathbf v=(\mathbf w,a,b)$ 的梯度和对偶变量 $\alpha$ 的梯度，均为标准反向传播 + 少量标量运算，额外开销可忽略；论文未提供逐方法定量运行时对比表。
- CheXpert 实验：预训练阶段 2 epoch（batch size 32），AUC 微调阶段 2 epoch（4.2.1 节）；论文未报告绝对训练时长。

## 实验与基线

- **基准数据集（Table 1，imratio=1%，DenseNet121/ResNet20）**：AUC-M 在全部 8 个数据集×网络组合上优于 CE、Focal、AUC-S；例如 C10(D) 上 AUC-M $0.760\pm0.006$ vs AUC-S $0.745\pm0.010$ vs CE $0.698\pm0.017$；S10(D) 上 AUC-M $0.703\pm0.030$ vs AUC-S $0.669\pm0.070$（AUC-S 方差明显更大）。论文总结"AUC-M performs better in most cases, especially in the extremely imbalanced setting with imratio=1%"。
- **CheXpert 竞赛（Table 3）**：DAM（本文方法）测试 AUC $0.9305$，NRBC（超过 3 名放射科医生中的几名）$2.8$，排名第 1（对照：Stanford Baseline $0.9065$/排名 85；YWW $0.9289$/排名 5；Hierarchical Learning $0.9299$/排名 2）；论文并指出同课题组另一篇用 AUC square loss 的工作（[15]）在同数据集上只取得 $0.922$，**是论文用于证明 margin loss 优于 square loss 的一条跨论文对照证据**（非本文内部消融）。
- **Melanoma 竞赛（Table 4，EfficientNet-B5）**：AUC-M（Meta，即融合患者元数据）取得 public/private（w/ TTA）$0.9520/0.9423$，优于 AUC-S(Meta) 的 $0.9501/0.9409$、CE 的 $0.9447/0.9345$；最终提交（10 模型集成）取得 $0.9685/0.9438$，private AUC 排名 42/33 位（3314 支队伍），**单模型**表现（$0.9423$）超过冠军队单模型（$0.9167$，同配置对照）。
- **DDSM+ / PatchCamelyon（Table 5）**：AUC-M 在两个数据集上均优于 CE/Focal/AUC-S（DDSM+：$0.9544$ vs $0.9469$/$0.9495$/$0.9392$；PatchCamelyon：$0.8896$ vs $0.8703$/$0.8556$/$0.8394$）。
- **消融——批量得分归一化（BSN，5.1 节，Figure 3）**：图示定性结论，加入 BSN 提升性能，提取文本未还原具体数值。
- **消融——鲁棒性对易分/噪声数据（5.2 节，Figure 4/5）**：人工构造 1%/5% 噪声标签数据、10%/20% 易分数据加入训练集后，AUC-M 相对 AUC-S 保持大幅领先（图示定性结论，"All results clearly show that AUC-M outperforms AUC-S by a large margin"，无具体数值表）。
- **消融——$\alpha\ge0$ 约束（5.2 节，Figure 4 下半部分）**：固定 margin $m=0.1$，在含 40% 易分样本 + 1% 噪声样本的数据上比较有/无非负约束，有约束版本性能更好，且约束防止 $\alpha$ 在训练初期跌入"坏区域"（图示定性结论）。

## 与本课题的关系

本课题为跨年度加密恶意流量检测，第三章用 FT-Transformer 骨干（924,283 参数），训练目标为逐流 BCE（梯度 $g_f$，$\|g_f\|=1.286630$）与多预算 CVaR-pAUC 排序损失（梯度 $g_r$，$\|g_r\|=825.010925$）之和，两者共享骨干参数，余弦 $-0.197056$。本文与其他三篇（DB-MTL/Gama-Grassi/SAM-GS）**主题不同**——它不处理多任务梯度冲突，而是聚焦**单任务** AUC 排序目标本身的代理损失设计，是本课题排序损失（CVaR-pAUC）这一支的方法学背景候选来源，而非梯度控制器候选。

**本课题推论（需独立核实，非论文直接结论）**：本文的核心极小极大结构（原始变量 $\mathbf w,a,b$ + 对偶变量 $\alpha$，Algorithm 1 的 PESG）与"多预算 CVaR-pAUC 排序损失"这一表述在方法学谱系上**很可能相关**——CVaR（条件风险价值）本身就是用对偶变量刻画分位数阈值的极小极大/极小极小结构，与本文用 $\alpha$ 刻画正负类均值间隔的极小极大结构在数学形式上同源（都是"用一个标量对偶变量把一个非光滑/分段的鲁棒目标转化为可随机梯度优化的光滑极小极大问题"）。**但本课题实际使用的 CVaR-pAUC 损失公式本笔记未读取、未核验**，此处只是基于本文结构与"CVaR-pAUC 排序损失"命名的合理推测，不能作为已核实的方法学溯源，需要核对本课题实际代码或对应的 CVaR-pAUC 原始论文（原件目录中另有 `2022-Zhu-pAUC-DRO-ICML.pdf`，可能是更直接的方法学来源，本次任务范围未包含该文献的笔记撰写）。

**可迁移**：
- 本文用一维/线性模型的具体数值算例（附录 D/E）逐步推导"易分样本/噪声样本导致梯度方向错误"的方法论，是一种严谨的、可复用的梯度行为诊断手段——本课题若需要诊断 CVaR-pAUC 排序损失在真实数据上是否存在类似的"对易分流量/噪声标签的不良梯度效应"，可借鉴该数值算例式的诊断方法。
- Algorithm 1 中对偶变量 $\alpha$ 的更新采用与原始变量 $\mathbf w,a,b$ **不同的更新规则**（对偶上升 + 非负投影，而非普通梯度下降），且 $\alpha$ 的量纲/更新幅度由 $p(1-p)$、margin $m$ 等因子决定，与原始变量的梯度尺度天然不同——这为理解"本课题排序损失梯度 $g_r$ 为何比逐流 BCE 梯度 $g_f$ 大 641 倍"提供了一个可能的结构性解释方向（若 CVaR-pAUC 确实包含类似的对偶变量放大机制），但**这是待验证假设，需要核对本课题排序损失的实际实现**，不能仅凭本文的结构类比下结论。
- 非负约束 $\alpha\ge0$ 加合页函数替代平方项的设计思路（式 6），作为"用约束优化替代无约束平方项以获得鲁棒性"的通用技巧，可能对本课题排序损失的鲁棒性改进（如果存在噪声标签或极端类别不平衡问题——本课题"加密恶意流量检测"场景与本文"医学影像类别不平衡"场景在数据不平衡本质上类似）有参考价值。

**不可直接声称**：
- 本文的 Theorem 1 只是**代数等价性**，不提供收敛性或泛化保证；即使本课题的 CVaR-pAUC 损失确实采用类似结构，也不能直接引用本文的理论结果作为本课题损失函数的收敛性依据——本文自己都把 PESG 的收敛性分析外包给另外两篇论文。
- 本文全部实验为**单任务**二分类 AUC 最大化（图像分类），不涉及多任务梯度聚合、方向冲突或幅值平衡问题，**不能**为本课题"BCE 与 CVaR-pAUC 两个损失如何联合优化"这一多任务问题提供任何直接方法或理论支持；它至多是理解 $g_r$ 内部结构的背景材料，不是梯度控制器候选。
- 本文用医学影像数据（imratio 1%–20.21%）验证方法有效性，本课题为加密恶意流量检测，数据模态（表格特征 vs 图像）、损失组合（单一 AUC 代理损失 vs BCE+CVaR-pAUC 联合损失）、模型架构（DenseNet/EfficientNet vs FT-Transformer）均不同，本文报告的具体性能提升数值不能外推到本课题。

## 局限与不可外推结论

- 本文未提供优化算法（PESG）自身的收敛性证明，收敛性依赖外部引用文献，且这两篇引用文献是否覆盖 AUC margin loss（而非仅 AUC square loss）版本的收敛性，本笔记未核验。
- 鲁棒性论证（对易分/噪声数据）建立在具体数值算例和小规模消融实验（Figure 4/5）上，不是统计意义上的一般性鲁棒性界，样本外泛化能力未经理论刻画。
- 两阶段训练框架（先 CE 预训练、再 AUC 微调）是基于"初步观察"（3.4 节，"From our preliminary studies... we conjecture"）采用的工程经验解决方案，论文未提供该现象的理论解释，只是实用主义的应对措施。
- 全部医学影像实验的类别不平衡比例（1%–20.21%）与具体损失数值增益不能直接套用到加密恶意流量检测这一不同模态、不同任务结构的场景。
- 部分消融实验（BSN、噪声/易分数据鲁棒性、$\alpha$ 约束效果）只以图示形式呈现，提取文本未能还原具体数值表格，相关增益幅度需要回原始 PDF 图像核验。

## 文献信息

- arXiv：https://arxiv.org/abs/2012.03173
- DOI：10.48550/arxiv.2012.03173
- 代码：https://github.com/Optimization-AI/ICCV2021_DeepAUC（论文正文提供，本次未核验代码仓库内容）
- 提取全文：`/tmp/mtl-pdf-extract/arxiv-2012.03173.md`（会话临时目录，非仓库内容）
