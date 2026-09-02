---
title: "Multi-Task Learning as Multi-Objective Optimization"
authors:
  - Ozan Sener
  - Vladlen Koltun
year: 2018
date: 2026-09-02
journal: "Advances in Neural Information Processing Systems 31 (NeurIPS 2018)"
source_pdf: "[[raw/papers/multi-task-gradient/arxiv-1810.04650.pdf]]"
doi: "10.48550/arxiv.1810.04650"
tags:
  - 类型/论文
  - 主题/多任务学习
  - 主题/多目标优化
  - 主题/梯度冲突
aliases:
  - MGDA
  - MGDA-UB
  - Sener2018-MTLasMOO
key_finding: "把多任务学习显式建模为多目标优化，用多梯度下降算法（MGDA）求解满足 KKT 条件的帕累托驻点公共下降方向；并提出只需一次反向传播的表征空间上界近似 MGDA-UB，在满秩假设下证明其解要么已是帕累托驻点，要么是同时不增大任一任务损失的下降方向。"
method: "共享参数梯度的凸包最小范数点（Frank-Wolfe 求解），以及基于链式法则的表征空间上界近似"
baseline: "均匀标量化、单任务训练、网格搜索标量化、Kendall 等 (2018) 不确定性加权、GradNorm"
---

# Multi-Task Learning as Multi-Objective Optimization

> Sener & Koltun，2018，NeurIPS 2018（正文 8 页 + 附录，提取文本共 424 行）。

## 一句话

论文把多任务学习的共享参数更新显式建模为多目标优化问题，用多梯度下降算法（MGDA）求解满足 KKT 条件的帕累托驻点公共下降方向；由于原始 MGDA 需要对每个任务单独反向传播、且求解成本随共享参数维度增长，论文进一步提出基于链式法则的表征空间上界 MGDA-UB，只需一次反向传播即可求解，并证明在雅可比矩阵满秩假设下该近似解要么已是帕累托驻点，要么是同时不增大任一任务损失的下降方向。

## 问题定义与记号

设输入空间 $\mathcal X$、任务空间集合 $\{\mathcal Y^t\}_{t\in[T]}$，共享参数 $\theta^{sh}$、任务私有参数 $\theta^t$，任务损失 $\hat{\mathcal L}^t(\theta^{sh},\theta^t)$。常规做法是最小化加权和（原文式 (1)）：

$$
\min_{\theta^{sh},\theta^1,\ldots,\theta^T}\sum_{t=1}^T c^t\hat{\mathcal L}^t(\theta^{sh},\theta^t)\tag{1}
$$

论文指出该形式只有在任务不竞争时才合理，因为当两个解 $\theta,\bar\theta$ 在不同任务上互有优劣时，没有成对任务重要性就无法比较（第 3 节正文）。论文改用向量值损失（式 (2)）：

$$
\min_{\theta^{sh},\theta^1,\ldots,\theta^T}\mathbf L(\theta^{sh},\theta^1,\ldots,\theta^T)=\big(\hat{\mathcal L}^1(\theta^{sh},\theta^1),\ldots,\hat{\mathcal L}^T(\theta^{sh},\theta^T)\big)^\intercal\tag{2}
$$

并给出 **Definition 1（MTL 的帕累托最优性）**：(a) 解 $\theta$ 支配 $\bar\theta$ 当且仅当对所有任务 $t$ 有 $\hat{\mathcal L}^t(\theta)\le\hat{\mathcal L}^t(\bar\theta)$ 且向量损失不完全相等；(b) $\theta^\star$ 为帕累托最优当且仅当不存在支配它的解。帕累托最优解集合记为帕累托集 $\mathcal P_\theta$，其像为帕累托前沿 $\mathcal P_{\mathbf L}$。

## 方法核心

### KKT 条件与 MGDA 优化问题（3.1 节）

论文给出 MTL 的 KKT 条件（3.1 节正文，无编号但以项目符号列出）：存在 $\alpha^1,\ldots,\alpha^T\ge0$ 使得 $\sum_t\alpha^t=1$ 且 $\sum_t\alpha^t\nabla_{\theta^{sh}}\hat{\mathcal L}^t=0$；且对所有任务 $t$，$\nabla_{\theta^t}\hat{\mathcal L}^t=0$。满足这两条的点称为**帕累托驻点**；每个帕累托最优点都是帕累托驻点，反之不必成立。

Désidéri (2012) 证明求解如下二次规划（原文式 (3)，本课题笔记称为 MGDA-QP）：

$$
\min_{\alpha^1,\ldots,\alpha^T}\left\{\left\|\sum_{t=1}^T\alpha^t\nabla_{\theta^{sh}}\hat{\mathcal L}^t(\theta^{sh},\theta^t)\right\|_2^2\ \middle|\ \sum_{t=1}^T\alpha^t=1,\ \alpha^t\ge0\ \forall t\right\}\tag{3}
$$

其解要么为 0（此时已满足 KKT 条件），要么给出一个同时改善所有任务的下降方向。式 (3) 等价于求共享参数梯度集合凸包内的最小范数点。

### 两任务闭式解与 Frank-Wolfe 求解（3.2 节）

当 $T=2$ 时式 (3) 是关于 $\alpha\in[0,1]$ 的一维二次函数，闭式解为原文式 (4)：

$$
\hat\alpha=\left[\frac{\big(\nabla_{\theta^{sh}}\hat{\mathcal L}^2-\nabla_{\theta^{sh}}\hat{\mathcal L}^1\big)^\intercal\nabla_{\theta^{sh}}\hat{\mathcal L}^2}{\left\|\nabla_{\theta^{sh}}\hat{\mathcal L}^1-\nabla_{\theta^{sh}}\hat{\mathcal L}^2\right\|_2^2}\right]_{+,\frac1\tau}\tag{4}
$$

其中 $[\cdot]_{+,\frac1\tau}$ 表示裁剪到 $[0,1]$。这一闭式解被用作 Frank-Wolfe 求解器的一维线搜索子程序（对应正文引用的 "Algorithm 1"）。**提取文本核验说明**：Algorithm 1 本身（该二点最小范数解析解的算法框）未在提取文本中以完整算法框形式出现，只在 Figure 1 图题旁残留了两行 OCR 片段（“$\gamma=(\bar\theta-\theta)^\intercal\bar\theta/\|\theta-\bar\theta\|_2^2$”“end if”），以及 Algorithm 2 第 11 行显式写明"Using Algorithm 1"；可推断其内容即式 (4) 的算法化表达，但笔记不据此臆造完整伪代码。

任务数大于 2 时，论文使用 Frank-Wolfe 算法求解式 (3)，完整算法为原文 **Algorithm 2**（完整誊录）：

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 Update Equations for MTL
1: for t = 1 to T do
2:    θ^t = θ^t - η∇_{θ^t} L̂^t(θ^{sh}, θ^t)   ▷ Gradient descent on task-specific parameters
3: end for
4:  α^1,…,α^T = FRANKWOLFESOLVER(θ)   ▷ Solve (3) to find a common descent direction
5:  θ^{sh} = θ^{sh} - η Σ_{t=1}^T α^t ∇_{θ^{sh}} L̂^t(θ^{sh}, θ^t)   ▷ Gradient descent on shared parameters
6: procedure FRANKWOLFESOLVER(θ)
7: Initialize α = (α^1,…,α^T) = (1/T,…,1/T)
8: Precompute M s.t. M_{i,j} = (∇_{θ^{sh}} L̂^i(θ^{sh}, θ^i))^⊤ (∇_{θ^{sh}} L̂^j(θ^{sh}, θ^j))
9: repeat
10:  î = argmin_r Σ_t α^t M_{rt}
11:  γ̂ = argmin_γ ((1-γ)α + γ e_î)^⊤ M ((1-γ)α + γ e_î)   ▷ Using Algorithm 1
12:  α = (1-γ̂)α + γ̂ e_î
13: until γ̂ ~ 0 or Number of Iterations Limit
14: return α^1,…,α^T
15: end procedure
</div>

### 表征空间上界 MGDA-UB（3.3 节）

对编码器-解码器架构 $f^t(\mathbf x;\theta^{sh},\theta^t)=f^t(g(\mathbf x;\theta^{sh});\theta^t)$（式 (5)），设共享表征 $\mathbf Z=(\mathbf z_1,\ldots,\mathbf z_N)$，链式法则给出上界（式 (6)）：

$$
\left\|\sum_{t=1}^T\alpha^t\nabla_{\theta^{sh}}\hat{\mathcal L}^t\right\|_2^2\le\left\|\frac{\partial\mathbf Z}{\partial\theta^{sh}}\right\|_2^2\left\|\sum_{t=1}^T\alpha^t\nabla_{\mathbf Z}\hat{\mathcal L}^t\right\|_2^2\tag{6}
$$

因 $\left\|\partial\mathbf Z/\partial\theta^{sh}\right\|_2^2$ 与 $\alpha$ 无关，可从优化目标中丢弃，得到近似问题（原文标记为 **MGDA-UB**）：

$$
\min_{\alpha^1,\ldots,\alpha^T}\left\{\left\|\sum_{t=1}^T\alpha^t\nabla_{\mathbf Z}\hat{\mathcal L}^t(\theta^{sh},\theta^t)\right\|_2^2\ \middle|\ \sum_{t=1}^T\alpha^t=1,\ \alpha^t\ge0\ \forall t\right\}\tag{MGDA-UB}
$$

实现上即对表征 $\mathbf Z$（而非对全部共享参数）求梯度，一次反向传播即可得到所有任务在 $\mathbf Z$ 处的梯度，再用 Algorithm 2 求解权重。

## 理论保证及其假设

**Theorem 1**（原文陈述）：假设 $\partial\mathbf Z/\partial\theta^{sh}$ 满秩。若 $\alpha^{1,\ldots,T}$ 是 MGDA-UB 的解，则以下二者之一成立：
(a) $\sum_t\alpha^t\nabla_{\theta^{sh}}\hat{\mathcal L}^t=0$，当前参数是帕累托驻点；
(b) $\sum_t\alpha^t\nabla_{\theta^{sh}}\hat{\mathcal L}^t$ 是同时降低所有目标的下降方向。

证明思路（附录 A，式 (7)–(12)）：满秩条件下 $\mathbf M=(\partial\mathbf Z/\partial\theta^{sh})^\intercal(\partial\mathbf Z/\partial\theta^{sh})$ 正定，MGDA-UB 与原始 MGDA-QP（式 3）在帕累托驻点判定上完全等价（双向），且 MGDA-UB 的 KKT 条件（式 11–12，拉格朗日乘子 $\lambda\ge0$）直接给出 $\left(\sum_t\alpha^t\nabla_{\mathbf Z}\hat{\mathcal L}^t\right)^\intercal\nabla_{\mathbf Z}\hat{\mathcal L}^{t'}=\lambda/2\ge0$ 对所有 $t'$ 成立，经 $\mathbf M$ 正定传递到共享参数空间梯度的非负内积。

**必需假设**：
- $\partial\mathbf Z/\partial\theta^{sh}$（表征对共享参数的雅可比）满秩。论文的合理性论证是：若该雅可比奇异，意味着各任务梯度线性相关，不存在真正的权衡需要处理（正文 3.3 节末段）。
- KKT 条件本身要求各任务损失可微。
- 定理只在“给定当前 $\alpha$ 解”这一个更新步骤内成立，是逐步的一阶性质，不是对整个训练轨迹的全局保证。

**该定理没有保证什么**（笔记明确标注，原文未直接反驳但也未声称）：
- 不保证收敛到的帕累托驻点是帕累托最优点——非凸情形下帕累托驻点集合严格大于帕累托最优集合（3.1 节正文原话：“每个帕累托最优点都是帕累托驻点，反之不必成立”）。
- 不保证任一特定任务（例如某个被认为更重要的主任务）的绝对性能不下降，只保证该次更新方向对所有任务的一阶导数非负（式 8–10），即“不增大”而非“充分下降”。
- 不覆盖满秩假设失效的退化情形（重复任务、任务梯度高度线性相关）。
- 未在附录之外提供该定理在随机梯度（mini-batch 估计误差）下仍然成立的严格证明；4.4 节只用启发式的稳定性论证（误差项 $\mathbf e^t$ 的 $l_2$ 范数与维度关系）解释了近似版本反而更稳定的实验现象，这是经验解释而非定理。

## 计算开销

- 未使用 MGDA-UB 近似时，需对每个任务分别执行一次反向传播（共 $T$ 次），训练时间随任务数线性增长（3.3 节正文）。
- 使用 MGDA-UB 近似后，只需对表征 $\mathbf Z$ 求一次梯度，附加开销可忽略。
- 表 2（Table 2）实测：三任务场景理解（Cityscapes）训练时间从无近似版本的 38.6 小时降到近似版本的 23.3 小时（正文称"reduced by 40%"）；四十任务多标签分类（CelebA）从 429.9 小时降到 16.1 小时（正文称"accelerates learning by a factor of 25"）。
- 精度上，近似版本在所有实验中都与无近似版本相近甚至略优（Table 2：Cityscapes mIoU 66.13→66.63，CelebA 平均误差 8.33→8.25），论文将其归因于随机梯度误差在低维表征空间中范数更小（4.4 节）。

## 实验与基线

- **基线**：均匀标量化（uniform scaling）、单任务训练（single task）、网格搜索标量化（grid search）、Kendall 等 (2018) 不确定性加权、GradNorm（Chen 等，2018）。
- **MultiMNIST**（Table 3，2 任务）：本文方法左/右数字准确率 97.26%/95.90%，与单任务基线 97.23%/95.90% 基本持平，明显优于均匀标量化 96.46%/94.99%、不确定性加权 96.47%/95.29%、GradNorm 96.27%/94.84%。论文强调网格搜索在该任务上也无法逼近本文方法（4.1 节正文）。
- **CelebA 多标签分类**（Table 1，40 任务）：平均误差本文方法 8.25，单任务 8.77，均匀标量化 9.62，不确定性加权 9.53，GradNorm 8.44。
- **Cityscapes 场景理解**（Table 4，3 任务：语义分割 mIoU、实例分割误差、视差误差）：本文方法 66.63% / 10.25px / 2.54px，全面优于单任务（60.68/11.34/2.78）、均匀标量化（54.59/10.38/2.96）、不确定性加权（64.21/11.54/2.65）、GradNorm（64.81/11.31/2.57）。
- 论文未报告统一的多种子重复实验协议细节（提取文本中未见对每个数据集的种子数或置信区间说明），本次全文核验未发现关于统计显著性检验的段落。

## 与本课题的关系

本课题为跨年度加密恶意流量检测，第三章用 FT-Transformer 骨干（924,283 参数），训练目标为逐流 BCE 与多预算 CVaR-pAUC 排序损失之和，二者共享同一套骨干参数，输出都来自骨干的同一预测头（不是论文默认的编码器+多个独立任务解码器结构）。

**可迁移**：
- 本课题只有两个损失项（BCE、CVaR-pAUC），恰好落在论文式 (4) 的两任务闭式解适用范围内——不需要 Frank-Wolfe 迭代或凹凸过程，可直接用闭式 $\hat\alpha$ 求解公共方向权重，工程实现成本很低。
- MGDA-UB 的核心洞察（把梯度求解从参数空间搬到表征空间以换取单次反向传播）在结构上要求“损失都是某个共享中间表征 $\mathbf Z$ 的函数”，这一前提在本课题中大概率成立：若把骨干最后一层输出视为 $\mathbf Z$，BCE 和 CVaR-pAUC 都可以写成 $\mathbf Z$ 的函数。这是可迁移的机制类比，但**未经本课题实验验证**，需要先确认两个损失的计算图是否真的只经过同一个 $\mathbf Z$ 节点分叉，而不存在只影响其中一个损失的额外中间层。
- 满秩假设的检验方式（论文未展开，只给出定性论证）可迁移为一种诊断思路：若本课题两个损失的梯度长期高度共线，说明其中一个损失提供的信息量可能接近冗余，这与论文“奇异意味着任务线性相关、无需权衡”的论证方向一致。

**不可直接声称**：
- 本课题的两个损失共享同一个输出头，而非论文假设的“共享编码器 + 各任务独立解码器”架构（式 5 中的 $f^t(\cdot;\theta^t)$）。论文的 K 任务框架显式允许每个任务有私有参数 $\theta^t$（Algorithm 2 第 2 行对 $\theta^t$ 单独做梯度下降），本课题若没有任务私有参数，则 Algorithm 2 第 1–3 行不适用，只保留第 4–5 行的共享参数更新逻辑，这一简化尚未在论文中被验证过。
- 帕累托驻点性质不保证 CVaR-pAUC 关注的尾部误报预算区间性能优于单独优化 BCE 或单独优化 CVaR-pAUC 的结果；论文的收敛结论只针对训练损失的一阶帕累托驻点，不涉及测试集尾部风险指标。
- 论文全部实验证据来自计算机视觉任务（MultiMNIST、CelebA、Cityscapes），损失类型为交叉熵、MSE、余弦相似度，未出现表格型数据或排序类损失（如 CVaR-pAUC）的实验，因此 MGDA 在排序损失与逐样本二分类损失组合下的经验效果仍需实测，不能从视觉任务结果外推。
- 论文的“单次反向传播”优势建立在深度编码器场景（ResNet-50/ResNet-18/LeNet）反向传播成本远高于前向传播的前提上；FT-Transformer 骨干参数量（924,283）远小于论文实验的模型规模，两次反向传播（不用 MGDA-UB 近似）的额外开销是否仍然显著，需要本课题实测计时，不能直接套用论文 Table 2 的 40%/25× 加速比。

## 局限与不可外推结论

- 满秩假设、KKT 条件与帕累托驻点框架均为一阶局部性质，深度网络训练中的非凸性使这些理论结论只能提供局部保证，不能保证全局最优或跨任务泛化性能。
- 论文的编码器-解码器架构假设（独立任务头）与本课题的单头多损失结构存在结构差异，本笔记只标注了迁移的可能性，尚未做代码层面或计算图层面的核验，这条属于**待验证假设**，不属于论文原结论。
- 论文的计算开销数字（Table 2）来自视觉骨干（ResNet-50、ResNet-18）与对应任务数（3、40），不能直接套用到 FT-Transformer 骨干与 2 损失场景；本课题若要引用加速比，必须重新实测。
- 论文没有涉及类别不平衡、CVaR 尾部风险或排序损失的实验，其“方法在 2 到 40 个任务范围内均有效”的结论是论文原结论，不能外推为“对任意损失函数组合都有效”。

## 文献信息

- arXiv：https://arxiv.org/abs/1810.04650
- DOI：10.48550/arxiv.1810.04650
- 提取全文：`/tmp/mtl-pdf-extract/arxiv-1810.04650.md`（会话临时目录，非仓库内容）
