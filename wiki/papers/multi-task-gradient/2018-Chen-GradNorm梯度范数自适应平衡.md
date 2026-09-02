---
title: "GradNorm: Gradient Normalization for Adaptive Loss Balancing in Deep Multitask Networks"
authors:
  - Zhao Chen
  - Vijay Badrinarayanan
  - Chen-Yu Lee
  - Andrew Rabinovich
year: 2018
date: 2026-09-02
journal: "Proceedings of the 35th International Conference on Machine Learning (ICML 2018)"
source_pdf: "[[raw/papers/multi-task-gradient/arxiv-1711.02257.pdf]]"
doi: "10.48550/arxiv.1711.02257"
tags:
  - 类型/论文
  - 主题/多任务学习
  - 主题/损失加权
  - 主题/梯度冲突
aliases:
  - GradNorm
  - Chen2018-GradNorm
key_finding: "GradNorm 通过一个额外的 L1 损失 L_grad，把每个任务在指定共享层上的梯度范数动态拉向“平均梯度范数 × 相对训练速度的 α 次方”这一目标，只调节梯度幅值（loss weight），不改变梯度方向；论文用玩具回归、NYUv2 和 MTFL 数据集证明它能匹配甚至超过昂贵网格搜索得到的静态权重，但全文未给出任何收敛性定理。"
method: "在指定共享层上定义任务梯度范数与相对训练速度，构造梯度范数目标并用额外损失 L_grad 的梯度更新 loss weight w_i(t)"
baseline: "各任务单独训练、等权重求和、Kendall 等 (2017) 不确定性加权、静态网格搜索权重"
---

# GradNorm: Gradient Normalization for Adaptive Loss Balancing in Deep Multitask Networks

> Chen, Badrinarayanan, Lee, Rabinovich，2018，ICML 2018（正文 8 页 + 附录，提取文本共 313+ 行，含补充材料）。

## 一句话

GradNorm 把多任务损失加权系数 $w_i(t)$ 本身当作可学习参数，用一个独立的 $L_1$ 损失 $L_{\mathrm{grad}}$ 把每个任务在指定共享层上的梯度范数拉向"平均梯度范数乘以该任务相对训练速度的 $\alpha$ 次方"这一目标，从而只调节各任务梯度的幅值（不触碰梯度方向），使各任务以相近的相对速度训练；论文全文是纯经验方法，没有给出收敛性或帕累托最优性定理。

## 问题定义与记号

多任务损失 $L(t)=\sum_i w_i(t)L_i(t)$，目标是学习函数 $w_i(t)$（正文 3.1 节）。论文先定义如下量：

- $W$：施加 GradNorm 的网络权重子集 $W\subset\mathcal W$，一般取"共享层的最后一层"以节省计算（原文脚注 1）。
- $G_W^{(i)}(t)=\left\|\nabla_W w_i(t)L_i(t)\right\|_2$：加权单任务损失关于 $W$ 的梯度 $L_2$ 范数。
- $\overline G_W(t)=E_{\mathrm{task}}\big[G_W^{(i)}(t)\big]$：所有任务在 $t$ 时刻的平均梯度范数。
- $\tilde L_i(t)=L_i(t)/L_i(0)$：任务 $i$ 的损失比率，是训练速度的反向度量（越小代表训练越快）。
- $r_i(t)=\tilde L_i(t)/E_{\mathrm{task}}[\tilde L_i(t)]$：任务 $i$ 的相对反向训练速度。

## 方法核心

### 目标梯度范数与 $L_{\mathrm{grad}}$（3.2 节）

理想目标是让每个任务的梯度范数达到（原文式 (1)）：

$$
G_W^{(i)}(t)\mapsto \overline G_W(t)\times[r_i(t)]^\alpha\tag{1}
$$

其中 $\alpha$ 是控制"拉回公共训练速度"强度的超参数：任务间复杂度差异越大，应使用越大的 $\alpha$；任务越对称（如玩具实验），$\alpha$ 应越小；$\alpha=0$ 会把所有任务的梯度范数拉到完全相等。

GradNorm 用一个 $L_1$ 损失衡量实际梯度范数与目标之间的差距（原文式 (2)）：

$$
L_{\mathrm{grad}}(t;w_i(t))=\sum_i\left|G_W^{(i)}(t)-\overline G_W(t)\times[r_i(t)]^\alpha\right|_1\tag{2}
$$

对 $L_{\mathrm{grad}}$ 求导时，目标项 $\overline G_W(t)\times[r_i(t)]^\alpha$ 被当作固定常数（stop-gradient），只对 $w_i(t)$ 求导，避免 $w_i(t)$ 被错误地拉向零。每次更新后重新归一化 $\sum_i w_i(t)=T$，使梯度归一化与全局学习率解耦。

### 玩具例子中的损失形式（4 节，式 (3)）

$$
f_i(\mathbf x)=\sigma_i\tanh\big((B+\epsilon_i)\mathbf x\big)\tag{3}
$$

其中 $B,\epsilon_i$ 为随机常数矩阵，$\sigma_i$ 控制第 $i$ 个任务的输出尺度，用于构造"损失尺度不同但任务本身对称"的可控实验。

### 完整算法（Algorithm 1，正文完整誊录）

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Training with GradNorm

Initialize w_i(0) = 1 ∀i

Initialize network weights W

Pick value for α > 0 and pick the weights W (usually the final layer of weights which are shared between tasks)

for t = 0 to max_train_steps do

Input batch x_i to compute L_i(t) ∀i and L(t) = Σ_i w_i(t) L_i(t)  [standard forward pass]

Compute G_W^{(i)}(t) and r_i(t) ∀i

Compute Ḡ_W(t) by averaging the G_W^{(i)}(t)

Compute L_grad = Σ_i |G_W^{(i)}(t) - Ḡ_W(t) × [r_i(t)]^α|_1

Compute GradNorm gradients ∇_{w_i} L_grad, keeping targets Ḡ_W(t) × [r_i(t)]^α constant

Compute standard gradients ∇_W L(t)

Update w_i(t) ↦ w_i(t+1) using ∇_{w_i} L_grad

Update W(t) ↦ W(t+1) using ∇_W L(t)  [standard backward pass]

Renormalize w_i(t+1) so that Σ_i w_i(t+1) = T

end for
</div>

## 理论保证及其假设

**全文未包含任何形式化定理或收敛性证明**（已核验：提取文本从摘要到结论、附录均无 "Theorem" "Proof" "Lemma" 字样的章节）。GradNorm 是纯经验设计，其正当性论证停留在类比和直觉层面：

- 与批归一化的类比：论文称 GradNorm 与批归一化（Ioffe & Szegedy, 2015）相似，区别是"跨任务而非跨批次归一化"，并以速度平衡作为归一化目标（引言部分）。这是设计动机的类比说明，不是收敛性证明。
- $r_i(t)$ 作为"相对反向训练速度"的代理，隐含假设各回归任务的损失是二次型：原文 5.1 节明确写道"注意所有回归任务都是二次损失（表面法向量用的余弦损失在主导阶也是二次的），这使我们可以用 $r_i(t)$ 直接代理每个任务的相对反向训练速度"。这是论文自陈的适用条件，不满足二次损失形状时 $r_i(t)$ 与"训练速度"的对应关系没有理论保证。
- $\alpha$ 的选择依赖经验调参：论文报告 NYUv2 上 $\alpha\approx1.5$ 最优、玩具实验用 $\alpha=0.12$，且"几乎所有 $0<\alpha<3$ 的取值都能提升性能"（5.4 节），但没有给出选择 $\alpha$ 的理论准则，也报告了 $\alpha$ 过大（如 VGG16 骨干上 $\alpha>2$）会导致权重数值不稳定（附录 7.1，Figure 7 图注）。
- $W$ 通常选共享部分的最后一层（脚注 1，仅出于计算成本考虑），论文没有证明该层的梯度范数能代表任务竞争的完整信息，也没有讨论选择更深或更浅共享层是否会改变结论。
- 补充材料报告了一个已知失效模式：当某任务的分类器提前收敛到多数类分类器（"stuck"，如 MTFL 数据集的 glasses、pose 任务）时，GradNorm 会持续增大该任务权重而无法修正（7.2 节），论文明确承认这是待解决问题，留作未来工作。

**该方法没有保证什么**：不保证收敛到任何驻点或帕累托意义下的最优解；不保证梯度范数被拉平后任务间不再存在方向冲突（GradNorm 只调节幅值，完全不涉及梯度方向，这与 MGDA、PCGrad、CAGrad 处理"方向冲突"的机制正交）；不保证对所有任务类型（尤其非二次损失或提前饱和的分类任务）都有效。

## 计算开销

- 每步需要为每个任务计算 $G_W^{(i)}(t)$，即对指定层 $W$ 的部分反向传播；论文建议把 $W$ 限定在共享部分的最后一层以降低这部分开销（脚注 1），但**未给出该部分反向传播相对全量反向传播的具体百分比或时间数字**。
- $L_{\mathrm{grad}}$ 对 $w_i(t)$ 的梯度计算独立于对 $W$（网络主体权重）的标准反向传播，两者在 Algorithm 1 中顺序执行。
- **全文核验：未发现任何 wall-clock 训练时间对比表**（不同于 MGDA 论文的 Table 2），提取文本中搜索 "overhead"、"training time"、"wall clock" 等关键词均未命中除脚注 1 之外的计算成本讨论。因此计算开销只能定性描述为"部分反向传播 + 一次额外的 loss-weight 更新"，无法引用论文自身的定量耗时证据。

## 实验与基线

- **基线**：单任务训练（Depth/Seg/Normals/Kpt Only）、等权重（Equal Weights，$w_i=1$）、Kendall 等 (2017) 不确定性加权、GradNorm Static（用 GradNorm 训练过程的时间平均权重 $E_t[w_i(t)]$ 重新静态训练）。
- **玩具回归**（4 节，$T=2$ 和 $T=10$）：$T=2$ 时 $(\sigma_0,\sigma_1)=(1.0,100.0)$，等权重训练下高尺度任务压制低尺度任务，GradNorm 通过增大 $w_0(t)$ 纠正该失衡；$T=10$ 时效果更明显。两种设置下 GradNorm 都优于不确定性加权（后者权重增长过快导致训练后期恶化）。
- **NYUv2+seg**（Table 1，VGG SegNet 骨干，深度/分割/法向量三任务）：GradNorm $\alpha=1.5$ 的深度 RMS 误差 0.925、分割误差（100−IoU）67.8、法向量误差 0.174，相对等权重基线（0.944/70.1/0.192）全面提升，且达到或超过对应单任务网络水平。
- **NYUv2+kpts**（Table 2，ResNet 与 VGG 两种骨干，深度/关键点/法向量三任务）：ResNet 骨干下 GradNorm $\alpha=1.5$ 为 0.663/7.32/0.155，优于等权重两次重复实验（0.697/7.80/0.172 与 0.702/7.96/0.182）及 GradNorm Static（0.695/7.63/0.156）；VGG 骨干下 GradNorm 为 0.629/7.73/0.139。
- **网格搜索对比**（5.3 节，Figure 4）：训练 100 个随机静态权重网络，其性能与到 GradNorm 时间平均权重 $E_t[w_i(t)]$ 的 $L_2$ 距离呈强负相关；在距离 $\sim3$ 处，网格搜索网络平均误差接近 GradNorm 网络的两倍，说明 GradNorm 单次训练即可逼近网格搜索的最优静态权重。
- **MTFL 补充实验**（附录 7.2，Table 3）：40×40 与 160×160 两种分辨率下，GradNorm 在性别与微笑分类上明显优于等权重与不确定性加权基线，但在眼镜与姿态两个任务上所有方法都收敛到多数类分类器，是论文明确承认的失效案例。

## 与本课题的关系

本课题为跨年度加密恶意流量检测，第三章用 FT-Transformer 骨干（924,283 参数），训练目标为逐流 BCE 与多预算 CVaR-pAUC 排序损失之和，二者共享同一套骨干参数。

**可迁移**：
- GradNorm 处理的正是"任务损失尺度不一致导致训练被某一项支配"这一现象，这与 BCE（逐样本对数损失，数值范围通常在 0 附近的小量级）和 CVaR-pAUC（尾部排序损失，数值尺度和 CVaR 分位数、样本对数量强相关）之间可能存在的尺度失衡是同构问题。GradNorm 的"相对反向训练速度"概念可作为诊断工具：分别记录 BCE 和 CVaR-pAUC 相对各自初始值的下降比例 $\tilde L_i(t)$，观察两者是否同步下降。
- Algorithm 1 的核心机制（额外维护可学习标量权重 $w_i(t)$，用一个独立的 $L_1$ 损失驱动其更新）工程实现简单，只需在共享骨干的某一层（如 FT-Transformer 的最后一个 Transformer block 输出）上计算两个损失的梯度范数，改造成本低于 MGDA/PCGrad/CAGrad 这类需要修改梯度合成规则的方法。

**不可直接声称**：
- GradNorm 完全不处理梯度方向冲突，只调节幅值；如果 BCE 与 CVaR-pAUC 的梯度在骨干参数空间中存在方向对抗（余弦相似度为负），GradNorm 无法缓解这一问题，需要与 PCGrad/CAGrad 等方向类方法区分角色，不能把 GradNorm 的结果解释为"解决了梯度冲突"。
- $r_i(t)$ 作为训练速度代理的理论前提是回归任务的二次损失；本课题的 BCE 是对数似然损失、CVaR-pAUC 是排序损失，均非二次型，论文自陈的适用条件在本课题不成立，$r_i(t)$ 能否仍然合理反映相对训练速度**未经验证**，需要先做实测（比较 $r_i(t)$ 与人工观察的训练曲线是否一致）再决定是否采用。
- 论文的"提前收敛到多数类"失效模式（7.2 节）提示：若本课题的某个损失项（例如某个误报预算下的 CVaR-pAUC）出现类似的提前饱和，GradNorm 可能持续错误增大其权重，这是论文自己报告的未解决问题，不能假设本课题不会遇到。
- 论文全部实验为计算机视觉任务（回归+分类混合），损失类型为交叉熵、MSE、余弦损失，未出现排序损失或不平衡二分类场景，GradNorm 在本课题损失组合下的效果需要实测验证，不能从视觉任务结果外推。

## 局限与不可外推结论

- 论文全篇没有收敛性、帕累托最优性或任何形式化定理，所有结论均来自经验实验，外推到新任务组合时应视为待验证假设而非已证明的性质。
- 论文自身承认的失效模式（分类器提前收敛到多数类时权重持续增大）尚无解决方案，作者在结论中明确列为未来工作方向。
- $\alpha$ 需要按数据集经验调参（NYUv2 上 1.5，玩具实验上 0.12），论文没有给出与任务数、任务异质性程度相关的选择公式，本课题若采用该方法需要独立做超参数搜索。
- 论文未报告计算开销的定量数字，因此不能引用论文数据来论证 GradNorm 比其他方向类方法（如需要多次反向传播的 MGDA）更省算力，只能引用论文关于"$W$ 通常取最后共享层以省计算"的定性设计动机。

## 文献信息

- arXiv：https://arxiv.org/abs/1711.02257
- DOI：10.48550/arxiv.1711.02257
- 提取全文：`/tmp/mtl-pdf-extract/arxiv-1711.02257.md`（会话临时目录，非仓库内容）
