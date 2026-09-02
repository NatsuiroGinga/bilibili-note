---
title: "Dual-Balancing for Multi-Task Learning"
authors:
  - Baijiong Lin
  - Weisen Jiang
  - Feiyang Ye
  - Yu Zhang
  - Pengguang Chen
  - Ying-Cong Chen
  - Shu Liu
  - Ivor W. Tsang
  - James T. Kwok
year: 2023
date: 2026-09-02
journal: "arXiv 预印本 2308.12029（正文含 Abstract/Keywords 分节，版式似期刊投稿稿；提取文本未见明确期刊/会议名称，期刊归属未核验）"
source_pdf: "[[raw/papers/multi-task-gradient/arxiv-2308.12029.pdf]]"
doi: "10.48550/arxiv.2308.12029"
tags:
  - 类型/论文
  - 主题/多任务学习
  - 主题/梯度冲突
  - 主题/损失平衡
aliases:
  - DB-MTL
  - Lin2023-DB-MTL
  - Dual-Balancing Multi-Task Learning
key_finding: "DB-MTL 同时做损失尺度平衡（对每个任务损失取对数变换，证明与 IMTL-L 在最优点等价但无需额外参数）和梯度幅值平衡（把各任务梯度归一化到同一方向后，乘以各任务梯度范数中的最大值 α_k=max_t‖ĝ_{t,k}‖_2，而非最小值或均值），在 NYUv2/Cityscapes/QM9/Office-31/Office-Home 五个数据集上相对当时的 SOTA 方法（Nash-MTL、CAGrad、Aligned-MTL 等）取得最好的平均相对性能 Δp；论文全文没有给出收敛性定理，作者在结论中明确把“为该方法开发理论收敛保证”列为未来工作。"
method: "损失侧对每个任务损失取 log 变换（Proposition 3.1 证明其为 IMTL-L 在最优 s_t 处的极限简化形式）；梯度侧对 EMA 平滑后的各任务梯度做单位归一化再乘以全局尺度 α_k=max_{1≤t≤T}‖ĝ_{t,k}‖_2（式 2），任务专属参数不做任何缩放"
baseline: "EW、GLS、RLW、UW、DWA、IMTL-L、IGBv2、MGDA、GradNorm、PCGrad、GradDrop、GradVac、IMTL-G、CAGrad、MTAdam、Nash-MTL、MetaBalance、MoCo、Aligned-MTL、IMTL（20+ 基线，含 loss/gradient/hybrid 三类）、STL（单任务独立训练上界）"
---

# Dual-Balancing for Multi-Task Learning

> Lin, Jiang, Ye, Zhang, Chen, Chen, Liu, Tsang, Kwok，2023，arXiv:2308.12029（提取文本共 427 行，正文 1–7 节 + 参考文献）。

## 一句话

DB-MTL 用一个无参数的对数变换统一各任务损失尺度、再用"归一化到最大梯度范数" $\alpha_k=\max_{1\le t\le T}\|\hat{\mathbf g}_{t,k}\|_2$（而非最小值、均值或中位数）统一各任务梯度幅值，在五个基准数据集上相对二十余个基线取得最好的平均相对性能，但论文全文不含任何收敛性定理。

## 问题定义与记号

$T$ 个任务，任务共享参数 $\theta$，任务专属参数 $\{\psi_t\}_{t=1}^T$（第 2 节，如计算机视觉中 $\theta$ 为特征编码器、$\psi_t$ 为任务专属输出模块）。任务 $t$ 在数据 $\mathcal D_t$ 上的损失记为 $\ell_t(\mathcal D_t;\theta,\psi_t)$，标准 MTL 训练目标为 $\sum_{t=1}^T\gamma_t\ell_t(\mathcal D_t;\theta,\psi_t)$，等权重（EW）取 $\gamma_t=1$。论文把已有方法分为损失平衡（loss balancing）、梯度平衡（gradient balancing）、混合平衡（hybrid balancing）三类（2.1–2.3 节），并指出损失/梯度尺度差异会导致大尺度任务主导更新方向，造成"任务平衡问题"。

## 方法核心

### 3.1 节：损失尺度平衡（对数变换）

对每个任务损失做变换 $\ell_t\mapsto\log\ell_t(\mathcal D_t;\theta,\psi_t)$，再最小化 $\sum_{t=1}^T\log\ell_t(\mathcal D_t;\theta,\psi_t)$。论文用 **Proposition 3.1** 证明其与 IMTL-L（Liu 等提出的可学习尺度 $e^{s_t}\ell_t-s_t$）的关系：

$$
\text{对 } x>0,\quad \log(x)=\min_s\; e^s x-s-1
$$

证明（正文完整誊录）：定义辅助函数 $f(s)=e^sx-s-1$，$\frac{\mathrm df(s)}{\mathrm ds}=e^sx-1$，$\frac{\mathrm d^2f(s)}{\mathrm ds^2}=e^sx>0$，故 $f$ 凸；由一阶最优条件令 $e^{s^\star}x-1=0$ 解得 $s^\star=-\log(x)$，代入得 $f(s^\star)=e^{-\log(x)}x+\log(x)-1=\log(x)$，证毕。据此，对数变换是 IMTL-L 在 $s_t$ 取逐迭代精确最小值时的等价形式，但**不需要额外可学习参数、不需要每步梯度下降求解 $s_t$**（3.1 节最后一段，"the logarithm transformation is simpler and more effective than IMTL-L"）。

### 3.2 节：梯度幅值平衡（归一化 + 最大范数缩放）

mini-batch 梯度 $\mathbf g_{t,k}=\nabla_{\theta_k}\log\ell_t(B_{t,k};\theta_k,\psi_{t,k})$（Algorithm 1 第 6 行）先做 EMA 平滑（式 1）：

$$
\hat{\mathbf g}_{t,k}=\beta\hat{\mathbf g}_{t,k-1}+(1-\beta)\mathbf g_{t,k}\tag{1}
$$

$\beta\in(0,1)$ 控制遗忘率。聚合梯度为式 2：

$$
\tilde{\mathbf g}_k=\alpha_k\sum_{t=1}^T\frac{\hat{\mathbf g}_{t,k}}{\|\hat{\mathbf g}_{t,k}\|_2}\tag{2}
$$

其中缩放因子取 $\alpha_k=\max_{1\le t\le T}\|\hat{\mathbf g}_{t,k}\|_2$。论文给出的论证（3.2 节正文，直接对应本课题调研文档 1.5 节引用）：当部分任务梯度范数大、部分小时，前者"has not yet converged"、后者"has almost converged"，此时当前解 $\theta_k$ 是不理想的，故 $\alpha_k$ 应当**大**以逃离该解；只有当所有任务梯度范数都小时，模型已接近所有任务的驻点，$\alpha_k$ 才应当小；因此选择 $\alpha_k=\max_t\|\hat{\mathbf g}_{t,k}\|_2$——"$\alpha_k$ 小当且仅当所有任务梯度范数都小"。任务共享参数更新为 $\theta_{k+1}=\theta_k-\eta\tilde{\mathbf g}_k$（第 10 行）；**任务专属参数**更新为 $\psi_{t,k+1}=\psi_{t,k}-\eta\nabla_{\psi_{t,k}}\log\ell_t(B_{t,k};\theta_k,\psi_{t,k})$（第 11–13 行），论文明确说明其更新只依赖对应任务梯度，"do not suffer from the gradient scaling issue"（3.2 节最后一段原文，逐字核验）。

### 完整算法（Algorithm 1，正文完整誊录）

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Dual-Balancing Multi-Task Learning.
Require: numbers of iterations K, learning rate η, tasks {D_t}_{t=1}^T, ε=10^-8, β;
1: randomly initialize θ_0, {ψ_{t,0}}_{t=1}^T;
2: initialize ĝ_{t,-1} = 0, for all t;
3: for k = 0,...,K-1 do
4:   for t = 1,...,T do
5:     sample a mini-batch dataset B_{t,k} from D_t;
6:     g_{t,k} = ∇_{θ_k} log(ℓ_t(B_{t,k}; θ_k, ψ_{t,k}) + ε);
7:     compute ĝ_{t,k} = β ĝ_{t,k-1} + (1-β) g_{t,k};
8:   end for
9:   compute g̃_k = α_k Σ_{t=1}^T ĝ_{t,k} / (‖ĝ_{t,k}‖_2 + ε), where α_k = max_{1≤t≤T} ‖ĝ_{t,k}‖_2;
10:  update task-sharing parameter by θ_{k+1} = θ_k - η g̃_k;
11:  for t = 1,...,T do
12:    ψ_{t,k+1} = ψ_{t,k} - η ∇_{ψ_{t,k}} log(ℓ_t(B_{t,k}; θ_k, ψ_{t,k}) + ε);
13:  end for
14: end for
15: Return θ_K, {ψ_{t,K}}_{t=1}^T.
</div>

注：正文 Algorithm 1 第 6/9/12 行的 $\log(\cdot+\epsilon)$、$\|\cdot\|_2+\epsilon$ 带数值稳定项 $\epsilon=10^{-8}$，而 3.1/3.2 节正文散文与式 (1)(2) 未写 $\epsilon$；提取文本核验：算法伪代码与正文公式在是否带 $\epsilon$ 上存在细微不一致，笔记如实记录，不代表两者矛盾（$\epsilon$ 仅为数值稳定项，不影响方法语义）。

### 与 GradNorm 的区别（3.2 节末段）

论文指出 GradNorm 也学习任务权重使梯度范数接近，但存在两个问题：一是交替更新模型参数与任务权重，不能保证每一迭代步梯度幅值真正相等；二是 $\alpha_k$ 的取值方式（GradNorm 完全不显式选择 $\alpha_k$）对性能影响显著（对应 Figure 6 消融），而 GradNorm 未考虑这一点。

## 理论保证及其假设

**无形式化定理。** 全文（含附录，本文无独立附录章节，Section 1–5 + 参考文献）未给出任何命题、引理或定理来证明 DB-MTL 的收敛性、最优性或帕累托性质；唯一的形式化陈述是 Proposition 3.1（对数变换与 IMTL-L 的等价关系，见上），其证明只涉及标量凸函数的一阶最优条件，与多任务优化的收敛性无关。论文结论第 5 节明确写道（原文逐字）："develop theoretical analysis to provide convergence guarantees and optimality conditions for our method" 被列为未来工作，即**作者自陈当前版本没有收敛性理论**。

因此，与 MGDA（帕累托驻点）、PCGrad（两任务凸/强凸收敛定理）、CAGrad（$H$-Lipschitz 光滑性下的 $O(1/T)$ 收敛速率）等同索引下的其他三篇论文相比，DB-MTL 是**纯经验方法**，其有效性完全由第 4 节的大规模实验支撑，不存在"该定理保证什么/不保证什么"的分析对象。

## 计算开销

- **每迭代步反向传播次数**：与 MGDA、GradNorm、PCGrad、CAGrad 等梯度平衡方法同阶——需要对每个任务分别计算梯度（Algorithm 1 第 6 行在 $t$ 循环内），因此每步需要 $T$ 次反向传播。
- **额外计算**：EMA 更新（式 1）与归一化 + 缩放（式 2）均为逐元素/范数运算，相对反向传播成本可忽略；不需要像 CAGrad 那样求解额外的凸优化问题，也不需要像 GradNorm 那样维护并反传一个额外的 $L_1$ 损失。
- **实测每 epoch 训练时间**（4.6 节，Figure 7，NYUv2，单张 RTX 3090，100 epoch 均值，仅描述图示定性结论，提取文本为图片未含具体数值表格）：DB-MTL 与其他梯度平衡方法（MGDA、GradNorm、PCGrad、GradVac、IMTL-G、CAGrad、MTAdam、MetaBalance、MoCo、Aligned-MTL）及 IMTL 用时相近，均慢于纯损失平衡方法（因为损失平衡方法不需要在每次迭代中为每个任务分别计算梯度）。论文原话："DB-MTL has a similar running time as gradient balancing methods... but is larger than the loss balancing methods because each task's gradient is computed in every iteration"。**提取受限说明**：Figure 7 为柱状图图片，提取文本未还原具体秒数，只能转述图注文字结论，无法给出精确数字。

## 实验与基线

- **基线集合（20+ 种，4.1 节列出）**：EW、GLS（几何平均损失）、RLW（随机任务权重）；损失平衡类 UW、DWA、IMTL-L、IGBv2；梯度平衡类 MGDA、GradNorm、PCGrad、GradDrop、GradVac、IMTL-G、CAGrad、MTAdam、Nash-MTL、MetaBalance、MoCo、Aligned-MTL；混合平衡类 IMTL；另含单任务学习基线 STL。全部基线基于开源 LibMTL 库实现（同一作者组的工具库），统一用硬参数共享（HPS）架构。
- **相对性能指标 $\Delta_p$**（式 3）：

$$
\Delta_{\mathrm p}(\mathcal A)=\frac1T\sum_{t=1}^T\Delta_{\mathrm p,t}(\mathcal A),\qquad
\Delta_{\mathrm p,t}(\mathcal A)=100\%\times\frac1{N_t}\sum_{i=1}^{N_t}(-1)^{s_{t,i}}\frac{M_{t,i}^{\mathcal A}-M_{t,i}^{\mathrm{STL}}}{M_{t,i}^{\mathrm{STL}}}
$$

$N_t$ 为任务 $t$ 的指标数，$M_{t,i}^{\mathcal A}$ 为方法 $\mathcal A$ 在任务 $t$ 第 $i$ 个指标上的值，$s_{t,i}=0$ 表示该指标越大越好、$1$ 表示越小越好（式与其后一行未单独编号，紧跟式 3）。
- **NYUv2（3 任务：语义分割/深度估计/表面法向，Table 1）**：DB-MTL 取得全表最优 $\Delta_p=+1.15\pm0.16$，是唯一在表面法向预测任务上与 STL 相当、同时在另两任务保持优势的方法（其余基线普遍在表面法向任务上大幅下降）。
- **Cityscapes（2 任务，Table 2）**：DB-MTL $\Delta_p=+0.20\pm0.40$，是所有 MTL 基线中唯一在全部任务上都优于 STL 的方法（其余基线的 $\Delta_p$ 均为负）。
- **QM9（11 任务分子性质回归，Table 3）**：DB-MTL 在全部 MTL 方法中 $\Delta_p$ 最高（$-58.10\pm3.89$），但**仍劣于 STL**（$\Delta_p$ 定义下 STL 为 0），论文明确指出 QM9 上"none of the MTL methods performs better than STL"，DB-MTL 相对次优方法 Nash-MTL（$-73.92\pm2.12$）有较大提升但未逆转"MTL 整体劣于单任务"的现象。
- **Office-31 / Office-Home（图像分类，Table 4）**：DB-MTL 取得两数据集最优 $\Delta_p$（$+1.05\pm0.20$ / $+0.17\pm0.44$），是极少数在 Office-Home 上也优于 STL 的方法。
- **消融（Table 5，4.4 节）**：在 NYUv2/Cityscapes/Office-31/Office-Home/QM9 五数据集上比较四种组合——EW（都不用，即两项均为 0，Δp 为负或很负）、只用损失平衡、只用梯度平衡、两者都用（DB-MTL）。以 NYUv2 为例：EW $-1.78\pm0.45$ → 只损失平衡 $+0.06\pm0.09$ → 只梯度平衡 $+0.76\pm0.25$ → 两者都用 $+1.15\pm0.16$，两个组件均有增益且叠加后最优，五个数据集上该单调改善模式一致成立（QM9 上为 $-146.3\to-74.40\to-65.73\to-58.10$，同样单调改善但仍为负值）。
- **对数变换的可迁移性（Figure 1，4.4 节）**：把对数变换叠加到 PCGrad、GradVac、IMTL-G、CAGrad、Nash-MTL、Aligned-MTL 上均带来一致增益，且叠加后仍不及完整 DB-MTL——说明对数变换是通用增益模块，但 DB-MTL 的梯度侧设计（最大范数缩放）仍有独立贡献。
- **$\alpha_k$ 取值消融（Figure 6，4.5 节）**：比较常数、最小值、最大值、均值、中位数五种 $\alpha_k$ 设定，"the maximum-norm strategy performs much better"——**这是论文对"取 max 而非 min"这一设计选择的唯一直接实证依据**，为图示定性结论，提取文本未还原具体数值。
- **EMA 遗忘率 $\beta$ 消融（Figure 5，4.5 节）**：在 Office-31 上网格搜索 $\beta\in\{0,0.1,\ldots,0.9\}\cup\{0.1/\sqrt k,\ldots,0.9/\sqrt k\}$，$\Delta_p$ 在 $\{0.1/\sqrt k,\ldots,0.9/\sqrt k\}$ 较大范围内不敏感，且优于不用 EMA（$\beta=0$）的版本。
- **骨干网络泛化（Table 6，SegNet；Figure 4，Cross-stitch/MTAN 架构）**：DB-MTL 在 SegNet 骨干上取得全表最优 $\Delta_p=+8.91$；在 Cross-stitch 与 MTAN 架构上同样优于 GLS、IGBv2 等强基线。
- **梯度冲突分析（Figure 10，4.8 节，Office-31）**：DB-MTL 相对 EW 的梯度余弦相似度上升更快且训练过程中保持正值，论文据此定性论证 DB-MTL 能降低梯度冲突、改善任务平衡（图示定性结论，无具体数值表格）。

## 与本课题的关系

本课题为跨年度加密恶意流量检测，第三章用 FT-Transformer 骨干（924,283 参数），训练目标为逐流 BCE（梯度 $g_f$）与多预算 CVaR-pAUC 排序损失（梯度 $g_r$）之和，二者共享同一套骨干参数；实测 epoch 2：$\|g_f\|=1.286630$、$\|g_r\|=825.010925$（范数比 641 倍）。现有梯度控制器已被核实等价于"PCGrad 式投影 + 重归一化到 $\|g_f\|$"。

**对调研文档 1.5 节的核验结论（全文核验后）**：1.5 节引用的式 2（$\tilde{\mathbf g}_k=\alpha_k\sum_t\hat{\mathbf g}_{t,k}/\|\hat{\mathbf g}_{t,k}\|_2$，$\alpha_k=\max_t\|\hat{\mathbf g}_{t,k}\|_2$）与本笔记核验的原文式 2 逐字一致；其转述的"论文对为何取 max 的论证"（未收敛任务应给大权重、已收敛任务应给小权重）与 3.2 节正文原话（"has not yet converged"/"has almost converged"）逐字对应，**1.5 节的核心论断成立**。1.5 节"三条不可跳过的限定"中第 3 条引用的"任务专属参数更新 do not suffer from the gradient scaling issue"同样在 3.2 节末段逐字核实。**结论：1.5 节的摘要级判断在全文核验后成立，未发现表述偏差。**

**可迁移**：
- $\alpha_k=\max$ 而非 $\min$ 的论证方向与本课题的具体数字直接相关：现有控制器取 $\alpha=\|g_f\|=1.29$（两者中较小者），按 DB-MTL 的论证逻辑，这对应"$g_r$ 尚未收敛、$g_f$ 已接近收敛"时选择了较小的 $\alpha$，即**该论证认为现有控制器的选择方向与其建议相反**。但 DB-MTL 全文的 $\alpha_k=\max$ 消融（Figure 6）没有报告具体数值增益，只有图示定性结论"max 明显更好"，因此该判断在本课题上的实际效果需要独立实验验证，不能直接套用论文的相对增益幅度。
- 对数变换（Proposition 3.1）是无参数、零额外计算成本的损失尺度平衡手段，且论文的可迁移性实验（Figure 1）证明它能独立改善其他梯度平衡方法（含与本课题控制器机制上最接近的 PCGrad）的性能，是成本最低的候选诊断/改进工具。
- Table 5 消融显示损失平衡与梯度平衡两个组件的收益方向一致且可叠加，为本课题设计"先做损失尺度诊断、再做梯度幅值诊断"的分步消融提供了方法论参照（但数值不可迁移）。

**不可直接声称**：
- DB-MTL **全文无收敛性定理**，不能像 CAGrad 或 PCGrad 那样为本课题的梯度控制策略提供任何理论保证；其有效性完全依赖经验实验，且实验全部在计算机视觉多任务分类/回归/QM9 分子属性回归场景，**未出现排序类损失（CVaR-pAUC）与二分类损失（BCE）的组合**，$\alpha_k=\max$ 策略在该组合下是否仍然最优需要本课题独立实验。
- DB-MTL 的架构假设是"任务共享参数 $\theta$ + 各任务独立的任务专属参数 $\psi_t$"（如独立的任务头），且明确说明任务专属参数更新不受梯度缩放问题影响；本课题 BCE 与 CVaR-pAUC 两个损失是否存在类似的"任务专属参数"结构（还是完全共用同一条打分路径、无独立头）**未在本课题验证**，若为后者，DB-MTL 关于 $\psi_t$ 更新独立性的论证不适用。
- QM9 实验（11 任务回归）表明即使是当前最优的 DB-MTL，在困难任务组合下仍可能整体劣于单任务训练（$\Delta_p<0$）；这提示"专用多任务方法不保证优于基线"，需要与本课题的固定权重/无控制器基线做共同预算对照，不能预设 DB-MTL 式设计必然带来增益。
- 论文全部实验使用 Adam 优化器（4.1/4.2/4.3 节均写明），但**未讨论自适应优化器的逐坐标二阶矩归一化是否会削弱全局尺度 $\alpha_k$ 选择（max vs min）的实际影响**——这正是调研文档 1.5 节第 1 条限定所指出的、需要本课题独立核实的问题，DB-MTL 论文本身未提供任何相关分析或消融。

## 局限与不可外推结论

- 全文没有收敛性、最优性或帕累托性质的形式化证明，是纯经验驱动的方法，效果完全依赖大规模基准实验的一致性，不提供"为什么一定收敛/收敛到哪里"的理论解释。
- 每迭代步仍需对每个任务分别计算梯度（$T$ 次反向传播），训练时间与 MGDA/PCGrad/CAGrad 等经典梯度平衡方法同阶，慢于纯损失平衡方法；论文未提供如 CAGrad 式的任务子采样加速方案。
- $\alpha_k=\max$ 策略的实证依据（Figure 6）仅为图示定性比较，未给出具体数值表格，也未讨论该策略在任务数 $T$ 很大或任务梯度范数长期极端失衡（如本课题 641 倍量级差）时是否仍然稳定——所有实验的任务数在 2–11 之间，梯度范数比量级未知，不能预设适用于本课题的 641 倍量级差场景。
- $\beta$（EMA 遗忘率）与全部基线的超参数均通过网格搜索确定，论文未给出与任务类型或损失异质性相关的选择公式，本课题若采用需独立调参。
- 消融实验（Figure 1、Figure 2、Figure 3、Figure 6）均以图片形式呈现，提取文本无法还原具体数值，只能转述图注定性结论，相关增益幅度需要回原始 PDF 图像核验，本笔记未做该核验（超出文本提取范围）。

## 文献信息

- arXiv：https://arxiv.org/abs/2308.12029
- DOI：10.48550/arxiv.2308.12029
- 提取全文：`/tmp/mtl-pdf-extract/arxiv-2308.12029.md`（会话临时目录，非仓库内容）
