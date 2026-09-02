---
title: "Conflict-Averse Gradient Descent for Multi-task Learning"
authors:
  - Bo Liu
  - Xingchao Liu
  - Xiaojie Jin
  - Peter Stone
  - Qiang Liu
year: 2021
date: 2026-09-02
journal: "Advances in Neural Information Processing Systems 34 (NeurIPS 2021)"
source_pdf: "[[raw/papers/multi-task-gradient/arxiv-2110.14048.pdf]]"
doi: "10.48550/arxiv.2110.14048"
tags:
  - 类型/论文
  - 主题/多任务学习
  - 主题/梯度冲突
  - 主题/收敛性分析
aliases:
  - CAGrad
  - Liu2021-CAGrad
key_finding: "CAGrad 在以平均梯度为中心、半径正比于其范数的局部球内求解“最大化最差任务局部改进量”的方向，证明可控收敛到平均损失 L_0 的驻点（c∈[0,1) 时），并把普通梯度下降（c=0）与 MGDA（c→∞）纳为特例；MGDA 与 PCGrad 只保证收敛到帕累托集合中某个不可预知的点，论文用 CIFAR10 半监督实验实证 MGDA 可能几乎完全牺牲主任务（分类交叉熵损失几乎不下降）。"
method: "在以平均梯度 g_0 为中心、半径 c‖g_0‖ 的局部球约束内求解 max_d min_i⟨g_i,d⟩，转化为关于任务数维度权重 w 的对偶凸优化问题求解"
baseline: "普通梯度下降、MGDA、PCGrad、GradDrop、Cross-Stitch、MTAN（含等权重/不确定性加权/DWA）、GradNorm、ARML、Soft Modularization、CARE、独立训练"
---

# Conflict-Averse Gradient Descent for Multi-task Learning

> B. Liu, X. Liu, Jin, Stone, Q. Liu，2021，NeurIPS 2021（正文 8 页 + 附录 A–B，提取文本共 639 行）。

## 一句话

CAGrad 在平均梯度 $g_0$ 周围一个半径正比于 $\|g_0\|$ 的局部球内，求解"最大化所有任务中最差的局部改进量"这一 minimax 问题，得到的更新方向既能显式收敛到平均损失 $L_0$ 的驻点（当约束半径系数 $c\in[0,1)$ 时），又能通过调节 $c$ 连续地在普通梯度下降（$c=0$）与 MGDA（$c\to\infty$）之间插值；这与 MGDA、PCGrad 只能保证收敛到帕累托集合中某个不可控的点形成对比。

## 问题定义与记号

$K\ge2$ 个任务共享参数 $\theta\in\mathbb R^m$，各任务损失 $L_i(\theta)$，标准 MTL 目标是最小化平均损失（原文式 (1)）：

$$
\theta^*=\underset{\theta\in\mathbb R^m}{\arg\min}\left\{L_0(\theta)\triangleq\frac1K\sum_{i=1}^KL_i(\theta)\right\}\tag{1}
$$

记 $g_i=\nabla L_i(\theta)$，平均梯度 $g_0=\nabla L_0(\theta)=\frac1K\sum_ig_i$。当 $\exists i,\langle g_i,g_0\rangle<0$ 时称梯度冲突（2.1 节正文，无编号）。

## 方法核心

### 冲突度量与 CAGrad 优化问题（3.1 节）

论文用一阶泰勒近似定义最差局部改进率（式 (2)）：

$$
R(\theta,d)=\max_{i\in[K]}\left\{\frac1\alpha\big(L_i(\theta-\alpha d)-L_i(\theta)\big)\right\}\approx-\min_{i\in[K]}\langle g_i,d\rangle\tag{2}
$$

CAGrad 在每一步求解（式 (3)）：

$$
\max_{d\in\mathbb R^m}\min_{i\in[K]}\langle g_i,d\rangle\quad\text{s.t.}\quad\|d-g_0\|\le c\|g_0\|\tag{3}
$$

其中 $c\in[0,1)$ 是控制收敛速度的超参数（收敛性质见 3.2 节）。该问题在以 $g_0$ 为中心的局部球内寻找同时最小化任务间冲突的最佳更新方向。

### 对偶问题推导

原始问题式 (3) 的决策变量 $d$ 维度等于参数量 $m$（可达百万级），直接求解不现实。论文推导其对偶问题只需在任务数维度 $w\in\mathbb R^K$ 上求解。记 $\mathcal W=\{w:\sum_iw_i=1,w_i\ge0\}$，$g_w=\sum_iw_ig_i$，$\phi=c^2\|g_0\|^2$。拉格朗日函数为（无编号）：

$$
\max_{d\in\mathbb R^m}\min_{\lambda\ge0,w\in\mathcal W}g_w^\top d-\lambda(\|g_0-d\|^2-\phi)/2
$$

由于对 $d$ 凹且约束线性，依 Slater 条件交换 min/max 得到对偶形式，最终关于 $w$ 的优化问题为：

$$
w^*=\underset{w\in\mathcal W}{\arg\min}\;g_w^\top g_0+\sqrt\phi\|g_w\|
$$

最优 $\lambda^*=\|g_{w^*}\|/\phi^{1/2}$，最优更新 $d^*=g_0+g_{w^*}/\lambda^*$（详细推导见附录 A.3 的 Lemma A.2，含式 (11)(12)）。$w$ 的维度等于任务数 $K$（通常 2 到数十），远小于模型参数量，因此实践中求解对偶问题。

### 完整算法（Algorithm 1，正文完整誊录）

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Conflict-averse Gradient Descent (CAGrad) for Multi-task Learning
Input: Initial model parameter vector θ_0, differentiable loss functions {L_i}_{i=1}^K, a constant c ∈ [0,1) and learning rate α ∈ R^+.
repeat
At the t-th optimization step, define g_0 = (1/K) Σ_{i=1}^K ∇L_i(θ_{t-1}) and φ = c²‖g_0‖².
Solve
min_{w∈W} F(w) := g_w^⊤ g_0 + √φ ‖g_w‖, where g_w = Σ_{i=1}^K w_i ∇L_i(θ_{t-1}).
Update θ_t = θ_{t-1} - α ( g_0 + φ^{1/2}/‖g_w‖ · g_w ).
until convergence
</div>

### 与 GD、MGDA 的特例关系（3.1 节 Remark）

当 $c=0$ 时，CAGrad 退化为标准梯度下降，$d=g_0$。当 $c\to\infty$ 时，最小化 $F(w)$ 等价于 $\min_w\|g_w\|$，与 MGDA（取梯度凸包中的最小范数向量作为更新方向）重合（原文明确"in theory it requires $c\to\infty$ to exactly recover MGDA"）。论文强调 CAGrad 与 MGDA 的关键区别：MGDA 在 0 向量周围搜索更新方向（附录式 (7) 的原始形式 $\max_{\|d\|\le1}\min_i\langle d,g_i\rangle$），而 CAGrad 在 $g_0$ 周围搜索，因此 MGDA 更保守，可能收敛到帕累托集合上任意一点（不可控），这也是论文解释"MGDA 实践中学得更慢"的原因。

### 实用加速：任务子采样（3.3 节，式 (4)）

为降低 $K$ 次反向传播的开销，论文提出只采样任务子集 $S\subseteq[K]$，计算其梯度 $\{g_i\mid i\in S\}$ 与平均梯度 $g_0$，再求解：

$$
\max_{d\in\mathbb R^m}\min\left(\left\langle\frac{Kg_0-\sum_{i\in S}g_i}{K-|S|},d\right\rangle,\ \min_{i\in S}\langle g_i,d\rangle\right)\quad\text{s.t.}\quad\|d-g_0\|\le c\|g_0\|\tag{4}
$$

论文说明 Theorem 3.2 的收敛保证在式 (4) 下依然成立（约束未变，见附录 A.3），时间复杂度为 $\mathcal O(|S|N+T)$（$N$ 为一次反向传播耗时，$T$ 为优化耗时），少任务场景（$K<10$）下通常 $T\ll N$。当 $S=[K]$ 时退化为完整 CAGrad。

## 理论保证及其假设

**Definition 3.1**（帕累托最优与驻点）：$\theta$ 被 $\theta'$ 帕累托支配当且仅当对所有 $i$ 有 $L_i(\theta')\le L_i(\theta)$ 且损失向量不完全相等；不存在支配它的解则为帕累托最优；帕累托驻点定义为 $\min_{w\in\mathcal W}\|g_w(\theta)\|=0$，其中 $g_w(\theta)=\sum_iw_i\nabla L_i(\theta)$。局部帕累托最优点必为帕累托驻点（引用 Désidéri 2012 结论，反之不必成立）。

**Theorem 3.2**（CAGrad 收敛性，正文陈述；证明见附录 A.3 / Theorem A.4）：假设 $L_0,L_1,\ldots,L_K$ 在 $\mathbb R^m$ 上可微，梯度 $\nabla L_i(\theta)$ 对所有 $i=0,1,\ldots,K$ 都是 $H$-Lipschitz（$0\le H\le\infty$），且 $L_0^*=\inf_\theta L_0(\theta)>-\infty$。取固定步长 $0<\alpha\le1/H$，则：

1) 对任意 $c\ge1$，CAGrad 的所有不动点都是 $(L_0,L_1,\ldots,L_K)$ 的帕累托驻点。
2) 若取 $0\le c<1$，则

$$
\sum_{t=0}^T\|\nabla L_0(\theta_t)\|^2\le\frac{2(L_0(\theta_0)-L_0^*)}{\alpha(1-c^2)}
$$

即 $\min_{t\le T}\|g_0(\theta_t)\|^2=O(1/T)$，算法收敛到 $\nabla L_0$ 的驻点。

**提取文本核验说明**：附录 Theorem A.4 对同一定理的两部分做了略有不同的条件划分——"1) 若 $0\le c<1$，收敛到 $L_0$ 驻点，速率如上" "2) 对任意 $c\ge0$，CAGrad 的所有不动点都是 $(L_0,\ldots,L_K)$ 的帕累托驻点"。正文与附录对"哪一部分要求 $c\ge1$、哪一部分对任意 $c\ge0$ 成立"的表述不完全一致（正文把帕累托驻点结论限定在 $c\ge1$，附录把同一结论放宽到"任意 $c\ge0$"）。笔记如实记录这一表述差异，不擅自判定哪个版本"更准确"。

**Theorem A.5**（附录 A.4，$c\ge1$ 时的替代保证）：在同样的可微、Lipschitz、下有界假设下，若 $c\ge1$ 并采用满足 $\alpha_t\le\|g_{w_t^*}(\theta_t)\|/(H(c-1)\|g_0(\theta_t)\|)$ 的时变步长，则 CAGrad 的极限点要么是 $L_0$ 的驻点，要么是 $(L_1,\ldots,L_K)$ 的帕累托驻点（析取式保证，不能同时保证两者）。

**必需假设**：
- $L_0,L_1,\ldots,L_K$（共 $K+1$ 个函数，含平均损失本身）均可微，梯度均 $H$-Lipschitz（光滑性假设，比 PCGrad Theorem 1 的凸性假设更弱，但仍是深度网络训练中未必严格成立的假设）。
- $L_0$ 下有界。
- 步长满足 $\alpha\le1/H$（固定步长情形）或满足 Theorem A.5 给出的时变上界（$c\ge1$ 情形）。
- $c\in[0,1)$ 是获得"收敛到 $L_0$ 驻点、速率 $O(1/T)$"这一更强结论的必要条件；$c\ge1$ 时只能得到"极限点二选一"的较弱析取式保证。

**该定理没有保证什么**：
- 只保证收敛到**驻点**（一阶必要条件 $\nabla L_0=0$ 或帕累托驻点），不保证全局最优，这与 MGDA、PCGrad 的一阶保证性质相同，是非凸优化理论的共同局限。
- 收敛目标是**平均损失 $L_0$** 的驻点，不是每个任务损失 $L_i$ 各自收敛到其驻点；"冲突规避"只体现在每一步更新方向的局部约束（式 3 的球约束），不是对每个任务损失单调下降的逐步保证。
- $H$-Lipschitz 假设需要对所有 $K+1$ 个损失函数（含 $L_0$）同时成立，论文没有提供在深度网络上验证该假设的方法，只是标准优化理论的技术条件。
- 附录 A.2 中，论文自己指出 PCGrad "没有清晰的每步优化目标，这使得难以一般性地分析其收敛保证"（"PCGrad does not have a clear optimization objective at each step, which makes it hard to analyze PCGrad's convergence guarantee in general"）——这是 CAGrad 论文对 PCGrad 的批评性表述，笔记如实转述为论文原观点，不代表本课题独立核实的结论。

## 计算开销

- 求解式 (3) 的对偶问题需要 $K$ 次反向传播获取各任务梯度 $g_i$（与无近似版 MGDA 同阶），额外的对偶优化（在 $K$ 维空间上，用标准凸优化库如 CVXPY 求解）相对反向传播成本可忽略，因为 $K$ 通常远小于参数量 $m$（3.1 节正文明确引用 CVXPY [Diamond & Boyd, 2016]）。
- **式 (4) 的任务子采样加速**：只对子集 $S\subseteq[K]$ 计算梯度，时间复杂度 $\mathcal O(|S|N+T)$，$N$ 为一次反向传播时间，$T$ 为优化时间；少任务时 $T\ll N$。
- **实测计时（附录 B.3，Table 7，Meta-World MT10/MT50，每次更新步的训练时间，单位秒）**：

| 方法 | MT10 | MT50 |
| --- | --- | --- |
| PCGrad | 9.7 | 59.8 |
| CAGrad | 10.3 | 27.8 |
| CAGrad-Fast | 4.8 | 11.4 |

论文解释：理论上 PCGrad 与 CAGrad 时间复杂度同阶，但 PCGrad 按随机任务顺序做逐对投影（Algorithm 2 的双重 for 循环），任务数大时循环开销显著（MT50 上 PCGrad 明显慢于 CAGrad）；CAGrad-Fast（子采样 4/8 个任务）相对 PCGrad 取得约 2×（MT10）和 5×（MT50）加速，同时性能相当或更优（对照 Table 3）。

## 实验与基线

- **基线集合**：普通梯度下降（GD）、MGDA（Sener & Koltun）、PCGrad、GradDrop、Cross-Stitch、MTAN（等权重/不确定性加权/DWA 三种加权方案）、GradNorm、ARML（半监督基线）、Soft Modularization、CARE（引入任务元数据的专家混合方法）、独立训练。
- **玩具优化例子与消融**（5.1 节）：5 个初始点中 GD 在 2 个点上卡住，其余方法均收敛到帕累托集合；CAGrad 取 $c=0$ 精确复现 GD，取 $c=10$ 很好地近似 MGDA（理论上需要 $c\to\infty$ 才精确等价）。
- **Multi-Fashion+MNIST**（缩小版 LeNet，5.1 节）：CAGrad（$c=0.2$）取得三次独立运行中最低的平均训练损失；PCGrad 与 MGDA 分别偏向只优化其中一个任务。
- **NYU-v2 三任务**（Table 1，MTAN 骨干，3 随机种子）：CAGrad（最优 $c=0.4$）取得 mIoU 39.79、像素准确率 65.49、深度绝对误差 0.5486、相对误差 0.2250、法向量角度均值 26.31/中位数 21.58、within-$t°$ 25.61/52.36/65.58，相对单任务独立训练的平均性能降幅 $\Delta m\%=0.20$，是所有多任务方法中最接近零降幅的（对照：Cross-Stitch 6.96、MTAN 5.59、MGDA 1.38、PCGrad 3.97、GradDrop 3.58）。论文用双尾 Student's t 检验（不等方差假设，$p=0.1$）标注基线方法相对 CAGrad 的显著差异。
- **CityScapes 二任务**（Table 2）：CAGrad 的 $\Delta m\%=11.64$（$c=0.4$），优于 Cross-Stitch（90.02）、MTAN（22.60）、MGDA（44.14）、PCGrad（18.29）、GradDrop（23.73）。
- **Meta-World MT10/MT50 强化学习**（Table 3，SAC 底层算法，10 次独立运行）：CAGrad 成功率 $0.83\pm0.045$（MT10）/$0.52\pm0.023$（MT50），CAGrad-Fast 为 $0.82\pm0.039$/$0.50\pm0.016$；均优于 Multi-task SAC（$0.49\pm0.073$/$0.36\pm0.013$）、Multi-task SAC+Task Encoder（$0.54\pm0.047$/$0.40\pm0.024$）、Multi-headed SAC（$0.61\pm0.036$/$0.45\pm0.064$）、PCGrad（$0.72\pm0.022$/$0.50\pm0.017$）、Soft Modularization（$0.73\pm0.043$/$0.50\pm0.035$）；仅次于引入额外任务元数据的 CARE（$0.84\pm0.051$/$0.54\pm0.031$）；单任务 SAC 上界为 $0.90\pm0.032$/$0.74\pm0.041$。
- **CIFAR10 半监督辅助任务**（ARML 框架，Table 4，500/1000/2000 标签）：ARML+CAGrad 在三种标签量下均取得最佳平均测试准确率（$68.25\pm0.37$/$74.37\pm0.42$/$82.81\pm0.48$），优于 ARML+PCGrad（$67.49$/$73.23$/$81.91$）与 ARML 基线（$67.05$/$73.22$/$81.35$）；**ARML+MGDA 明显劣化**（$49.27$/$60.11$/$60.78$），论文将其归因于 MGDA "显著忽视了主分类任务"。与 GradNorm 结合的对照实验结论相似（GradNorm+CAGrad 最佳：$67.53$/$74.72$/$83.15$；GradNorm+MGDA 最差：$36.99$/$57.94$/$59.12$）。
- **训练损失分解**（Table 8，2000 标签，最后一轮）：MGDA 的主任务交叉熵损失 $L_{CE}=0.407\pm0.018$（其余方法均为 $0.0\pm0.0$，即主任务损失几乎未被优化），但在辅助任务 2 上取得最小损失 $-0.4980\pm0.0007$，论文据此论证"MGDA 找到了帕累托前沿上的次优解"；CAGrad 取得最优的平均损失 $L_0=-0.4507\pm0.0058$。

## 与本课题的关系

本课题为跨年度加密恶意流量检测，第三章用 FT-Transformer 骨干（924,283 参数），训练目标为逐流 BCE 与多预算 CVaR-pAUC 排序损失之和，二者共享同一套骨干参数，天然对应 $K=2$ 的平均（或加权和）损失场景。

**可迁移**：
- CAGrad 的 Theorem 3.2 对任务数 $K\ge2$ 一般成立，不像 PCGrad 的严格定理那样局限于两任务特化推导；本课题 $K=2$ 的设置落在 CAGrad 理论覆盖范围内，且不需要像 PCGrad 那样单独验证"两任务专用定理"是否适用于超过两个损失的未来扩展。
- CAGrad 明确以**平均损失 $L_0$（对应本课题的 BCE+CVaR-pAUC 组合目标）本身的下降**为优化目标，并证明收敛到其驻点；这与本课题"训练目标就是两个损失之和"的设定语义上更贴合——本课题真正关心的收敛对象正是组合损失，而不是某个抽象的帕累托集合上的任意点。相比之下，MGDA/PCGrad 只保证到达帕累托集合中某处，不保证该处对组合目标本身表现良好（Table 4 的 MGDA 案例是直接的反面例证：可能几乎放弃主任务）。
- $c=0$ 与 $c\to\infty$ 分别退化为普通梯度下降与 MGDA，这一性质提供了一个可解释的消融维度：本课题可以把 $c$ 作为超参数扫描，观察从"完全不做冲突规避"到"完全追随 MGDA 式最小范数方向"之间性能如何变化，而不需要分别实现三套独立代码。
- 计算开销上，$K=2$ 时对偶优化问题维度极低（$w\in\mathbb R^2$），论文验证过的 CVXPY 求解或简单解析方法都足够快；这意味着本课题若采用 CAGrad，额外开销主要来自两次反向传播（与不做任何冲突处理的基线相比多一次），而不会像 PCGrad 在多任务场景中出现的"随机顺序遍历导致的循环开销"问题（Table 7 现象，$K=2$ 时该问题本就不明显）。

**不可直接声称**：
- Theorem 3.2 要求 $L_0,L_1,\ldots,L_K$（含平均损失）梯度 $H$-Lipschitz；FT-Transformer 骨干上 BCE 与 CVaR-pAUC 的组合损失是否满足光滑性假设**未经本课题验证**，不能预先假定成立，需要用训练中梯度范数变化的经验诊断作为间接证据。
- $c\in[0,1)$ 是一个需要按任务组合经验调参的超参数，论文在监督学习任务上搜索得到的最优值集中在 $0.2\sim0.6$，强化学习任务上则用到 $0.9$；论文没有给出与损失类型或任务异质性相关的选择公式，本课题不能直接沿用论文报告的 $c$ 值，必须独立做超参数搜索。
- 论文全部实验为计算机视觉多任务、机器人操作强化学习、半监督图像分类，损失类型为交叉熵、MSE、余弦损失、策略梯度目标，均未出现排序类损失（CVaR-pAUC）与二分类损失的组合；CAGrad 在该组合下的效果、以及"平均损失驻点"是否对应本课题真正关心的尾部风险改善，需要本课题实测，不能从视觉/RL 任务结果外推。
- 论文关于"MGDA 会显著牺牲主任务"的结论（Table 4、Table 8）来自特定的 ARML 半监督分类实验配置，不能直接断言 MGDA 在本课题的 BCE+CVaR-pAUC 组合下也会出现同样的主任务牺牲现象，这需要独立复现。

## 局限与不可外推结论

- 收敛定理的核心假设（$K+1$ 个损失均 $H$-Lipschitz 光滑、$L_0$ 下有界）在深度非凸网络上属于标准但未经逐案验证的技术假设，论文没有提供在实际深度网络训练中验证该假设是否成立的实证方法。
- 正文 Theorem 3.2 与附录 Theorem A.4 在"帕累托驻点结论适用的 $c$ 范围"上表述不完全一致（正文限定 $c\ge1$，附录称"任意 $c\ge0$"），笔记已如实记录，不代表笔者能够判定哪个版本是印刷错误、哪个是修订后的更精确表述，需要进一步核对原文 PDF 排版或作者勘误。
- $c$ 的选择依赖网格搜索（论文在 $\{0.1,\ldots,0.9\}$ 上搜索），没有理论指导的默认值，是额外的超参数调优成本。
- 论文关于"CAGrad 优于 MGDA/PCGrad"的实证结论均建立在特定架构（SegNet+MTAN、SAC、WRN-28-2）与特定数据集上，不能作为本课题预期收益的定量参照，只能作为方法选型的定性参考。

## 文献信息

- arXiv：https://arxiv.org/abs/2110.14048
- DOI：10.48550/arxiv.2110.14048
- 代码：https://github.com/Cranial-XIX/CAGrad（论文正文提供，本次未核验代码仓库内容）
- 提取全文：`/tmp/mtl-pdf-extract/arxiv-2110.14048.md`（会话临时目录，非仓库内容）
