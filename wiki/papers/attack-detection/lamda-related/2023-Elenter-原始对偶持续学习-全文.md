---
title: "2023-Elenter-原始对偶持续学习"
authors: "Elenter, Javier; NaderiAlizadeh, Nika; Javidi, Tara; Ribeiro, Alejandro"
year: 2023
date: 2026-10-15
journal: "arXiv:2310.00154（另有 OpenReview 版 GicZtgSlJW）"
source_pdf: "raw/papers/attack-detection/lamda-related/2023-Elenter-PrimalDualContinualLearning.pdf"
tags:
  - 类型/论文
  - 主题/持续学习
  - 主题/回放缓冲区
  - 主题/任务级预算分配
  - 主题/约束优化
  - attack-detection
key_finding: "检索到的唯一有理论支撑的任务级非均匀缓冲划分：把 CL 写成任务级不遗忘约束的优化问题，缓冲按对偶变量线性比例划分 n(t)=|B|·λ(t)/‖λ(t)‖₁ 加仿射保底（α=1/2 时每任务保底 |B|/2t）；Theorem 1 给对偶变量作为敏感度指标的偏差界。Fig.3 显示非均匀划分优于均匀划分。"
---

> 本文件为 MinerU 全文机械转换 + 结构化摘要头。公式与定理以原件 PDF 为准。

## 结构化摘要（检索任务：固定存储预算的任务级分配）

**问题形式化（P_t，§1）**：min 当前任务风险 s.t. 各旧任务平均损失 ≤ ε_k（任务级不遗忘约束）；缓冲 B_t = ∪_{k<t} B_k(t)，n_k(t)=|B_k(t)|。

**缓冲划分（§3.2 Adaptive Buffer Partition）**：

- `n(t) = |B| · λ(t)/‖λ(t)‖₁`：按对偶变量（= 任务难度/敏感度）线性比例分配。
- 仿射保底防零分配：α∈[0,1]，**α=1/2（实验取值）时每任务保底 |B|/2t——恰为均分配额的一半**；α=1 时保底 0。
- 当前任务的累计 slack 记入人工对偶 λ_t(t) 一并参与划分。

**理论（Theorem 1 + 附录 A.2/A.4）**：对偶变量是约束扰动的敏感度指标，附偏差界；模型容量越大界越紧，**缓冲越小 ζ(ñ,δ) 越大、对偶变量质量越差**（小缓冲退化，与 Chaudhry 2019 一致）。

**直接实验对照（Figure 3）**：按任务难度非均匀划分（PDCL）优于均匀划分（PDCL₀、ER Ring、AGEM）——这是任务级「等额 vs 按难度加权」最接近的直接对照，但按难度而非按任务规模。

**小缓冲边界（行 261）**：语音任务小缓冲下 PDCL 表现平平、样本选择无增益；部分设置下无方法显著超 ER（引 Zhou 2023）。

**本课题推论**：若要在文献中找「非均匀分配优于均分」的理论依据，PDCL 是最强的一条；但其分配信号 λ 是约束优化的副产物，等额是我们的基线规则，二者对照可在我们数据上以最小代价复现（见 report.md）。

**不可直接声称的内容**：Theorem 1 是敏感度/偏差界，**不是分配规则的最优性或遗憾界**；其凸性假设（Assumption 3：损失凸、函数空间凸、严格可行）在深度网络下不成立，只能作启发式移植。
# Primal Dual Continual Learning: Balancing Stability and Plasticity through Adaptive Memory Allocation

Juan Elenter University of Pennsylvania elenter@seas.upenn.edu

Tara Javidi University of California, San Diego tjavidi@ucsd.edu

Navid NaderiAlizadeh Duke University nnaderi@seas.upenn.edu

Alejandro Ribeiro University of Pennsylvania aribeiro@seas.upenn.edu

## Abstract

Continual learning is inherently a constrained learning problem. The goal is to learn a predictor under a no-forgetting requirement. Although several prior studies formulate it as such, they do not solve the constrained problem explicitly. In this work, we show that it is both possible and beneficial to undertake the constrained optimization problem directly. To do this, we leverage recent results in constrained learning through Lagrangian duality. We focus on memory-based methods, where a small subset of samples from previous tasks can be stored in a replay buffer. In this setting, we analyze two versions of the continual learning problem: a coarse approach with constraints at the task level and a fine approach with constraints at the sample level. We show that dual variables indicate the sensitivity of the optimal value of the continual learning problem with respect to constraint perturbations. We then leverage this result to partition the buffer in the coarse approach, allocating more resources to harder tasks, and to populate the buffer in the fine approach, including only impactful samples. We derive a deviation bound on dual variables as sensitivity indicators, and empirically corroborate this result in diverse continual learning benchmarks. We also discuss the limitations of these methods with respect to the amount of memory available and the expressiveness of the parametrization.

## 1 Continual Learning is a Constrained Learning Problem

In real-world settings, agents must adapt to a dynamic stream of observations they receive from their environment. This necessity has led to extensive research in continual learning, where the goal is to train agents to sequentially solve a diverse set of tasks (Thrun & Mitchell, 1995).

Given its sequential nature and the finite capacity of machine learning (ML) models, the primary challenge in continual learning lies in balancing the acquisition of new knowledge (plasticity) with the retention of previously integrated knowledge (stability). Mishandling the stability-plasticity balance can result in significant performance degradation on prior tasks. Avoiding this phenomenon, termed catastrophicforgetting, naturally leads to constrained optimization formulations, which have appeared extensively in the continual learning literature (Aljundi et al., 2019; Chaudhry et al., 2018; Lopez-Paz & Ranzato, 2017; Peng et al., 2023).

Most approaches do not solve this constrained optimization problem explicitly. Instead, they use gradient projections (Lopez-Paz & Ranzato, 2017; Chaudhry et al., 2018), promote proximity in the parameter space (Wang et al., 2021b; Kirkpatrick et al., 2017), or penalize deviations from a reference model. For instance, when fine-tuning a large language model (LLM) using RLHF, deviations from the pre-trained model are penalized to avoid degradation in text completion (Christiano et al., 2017).

This work demonstrates that it is both possible and beneficial to undertake the constrained learning problem directly (Contribution 1). To do this, we leverage recent advances in constrained learning through Lagrangian duality (Chamon et al., 2023) and build a framework that contemplates both task-level and instance-level forgetting.

State-of-the-art continual learning methods often include replay buffers, in which agents store a small subset of the previously seen instances. These methods have become ubiquitous, as they generally outperform their memoryless counterparts (Masana et al., 2022; Zhou et al., 2023; De Lange et al., 2021). The principled constrained learning framework proposed in this paper enables an adaptive and efficient management of the memory buffer. In this framework, the continual learning problem is viewed through the lens of constrained learning via Lagrangian duality. This perspective provides access to the sensitivity of the optimal value of the continual learning problem with respect to constraint perturbations, indicating how performance on the current task is influenced by the difficulty of not forgetting past tasks. At the task level, we leverage this result to partition the buffer, allocating more resources to harder tasks and using dual variables as adaptive regularization weights for the replay losses (Contribution 2). At the sample level, we use this sensitivity information to populate the buffer, including only impactful instances. These techniques provide a direct handle on the stability-plasticity trade-off incurred in the learning process (Contribution 3).

A continual learner aims to minimize the expected risk over a set of tasks,

$$
f _ {\theta} ^ {\star} = \underset {\theta \in \Theta} {\arg \min} \sum_ {t = 1} ^ {T} \mathbb {E} _ {\mathfrak {D} _ {t}} \left[ \ell (f _ {\theta} (x), y) \right],
$$

where $T$ is the number of tasks, ${ \mathfrak { D } } _ { t }$ is the data distribution associated to task t and $f _ { \theta } : \mathcal { X }  \mathcal { V }$ is the function associated with parameters $\theta \in \Theta \subseteq \mathbb { R } ^ { p }$ . The tasks and their corresponding data distributions are observed sequentially. That is, at time t, data from previous tasks $( \mathrm { i . e . , } \mathfrak { D } _ { 1 } , \cdot \cdot \cdot , \mathfrak { D } _ { t - 1 } )$ and from future tasks $( \mathrm { i } . \mathbf { e } . , \mathfrak { D } _ { t + 1 } , \cdot \cdot \cdot , \mathfrak { D } _ { T } )$ are not available. In this setting, the main issue that arises is catastrophic forgetting: if we sequentially fine-tune f on each incoming distribution, the performance on previous tasks could drop severely. A continual learner is one that is stable enough to retain acquired knowledge and malleable enough to gain new knowledge.

If the no-forgetting requirement is enforced at the task level, we can formulate the continual learning problem as minimizing the statistical risk on the current task without harming the performance of the model on previous tasks, i.e.,

$$
\begin{array}{l l} P _ {t} = \min _ {\theta \in \Theta} & \mathbb {E} _ {\mathfrak {D} _ {t}} [ \ell (f _ {\theta} (x), y) ], \\ \text {s.t.} & \mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (f _ {\theta} (x), y) ] \leq \epsilon_ {k}, \quad \forall   k \in \{1, \ldots , t - 1 \}, \end{array}\tag{\((P_{t})\}
$$

where $\epsilon _ { k } \in \mathbb { R }$ is the forgetting tolerance of task k, i.e., the worst average loss that is admissible in a certain task. In many cases, this is a design requirement, and not a tunable parameter. For instance, in medical applications, $\epsilon _ { k }$ can be tied to regulatory constraints. If the upper bound is set to the unconstrained minimum $\begin{array} { r } { ( \mathrm { i . e . , } \ \epsilon _ { k } = \operatorname* { m i n } _ { \theta \in \Theta } \mathbb { E } _ { \mathfrak { D } _ { k } } [ \ell ( f _ { \theta } ( x ) , y ) ] ) } \end{array}$ , then the solution to problem $( P _ { t } )$ corresponds to an ideal continual learner (Peng et al., 2023). However, we do not have access to ${ \mathfrak { D } } _ { k }$ for $k \neq t ,$ but only to a memory buffer $B _ { t } = \cup _ { k = 1 } ^ { t - 1 } B _ { k } ( t )$ , where $B _ { k } ( t )$ denotes the subset of the buffer allocated to task k while observing task t. When possible, we will obviate the dependence on the index t to ease the notation.

In this setting, the main questions that arise are: (i) When is the constrained learning problem (P<sub>t</sub>) solvable? (ii) How to solve it? (iii) How to partition the buffer B across the different tasks ? (iv) Which samples from each task should be stored in the buffer?

This paper is structured as follows: in Section 2, we present the duality framework used to undertake the constrained learning problem. In Section 3, we characterize the variations of the optimal value of the continual learning problem, which leads to the proposed buffer partition strategy. In Section 4, we discuss sample selection leveraging the information carried by dual variables; and in Section 5 we present numerical results in image, audio and medical datasets that validate these findings.

## 2 Continual Learning in the Dual Domain

For continual learning to be justified, tasks need to be similar. The following assumption characterizes this similarity in terms of the distance between the set of optimal predictors associated to each task.

Assumption 1. Let $\begin{array} { r } { \mathcal { F } _ { t } ^ { \star } = \{ \theta \in \Theta : \mathbb { E } _ { \mathfrak { D } _ { t } } [ \ell ( f _ { \theta } ( x ) , y ) ] = \operatorname* { m i n } _ { \theta \in \Theta } \mathbb { E } _ { \mathfrak { D } _ { t } } [ \ell ( f _ { \theta } ( x ) , y ) ] \} } \end{array}$ be the set of optimal predictors associated to task t. The pairwise distance between optimal sets is bounded as in

$$
d \left(\mathcal {F} _ {i} ^ {\star}, \mathcal {F} _ {j} ^ {\star}\right) \leq \delta , \quad \forall i, j \in \{1, \dots , T \}.
$$

Several task similarity assumptions have been proposed in the literature, most of which can be formulated as Assumption 1 with an appropriate choice of $d ( \cdot , \cdot )$ and δ. In this work, we use the standard (Haussdorf) distance between non-empty sets: $d ( X , Y ) = \operatorname* { m a x } \left\{ \operatorname* { s u p } _ { x \in X } d ( x , Y ) , \operatorname* { s u p } _ { y \in Y } d ( X , y ) \right\}$ Note that in over-parameterized settings, deep neural networks attain near-interpolation regimes and this assumption is not strict (Liu et al., 2022). This leads to the following proposition, which characterizes the feasibility of the continual learning problem. In particular, it suggests that for Problem $( P _ { t } )$ to be feasible, the forgetting tolerances $\bar { \{ \epsilon _ { k } \} } _ { k = 1 } ^ { T }$ need to match the task similarity δ.

Proposition 1. Let $m _ { k }$ be the unconstrained minimum associated to task k and let M be the Lipschitz constant ofthe loss $\ell ( \cdot , y )$ . Under Assumption $^ { l , }$ there exists $\theta \in \Theta$ such that,

$$
\mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (f _ {\theta} (x), y) ] \leq m _ {k} + \frac {T - 1}{T} M \delta , \quad \forall k \in \{1, \dots , T \}.
$$

For instance, if $\epsilon _ { k } = m _ { k } + M \delta$ for all $k ,$ then problem $( P _ { t } )$ is feasible at all iterations, and its solution is Mδ close to the optimum in terms of the expected loss on the current task.

However, the feasibility of problem $( P _ { t } )$ tells us nothing about how to solve it. Note that even if the loss $\ell ( f _ { \boldsymbol { \theta } } ( x ) , y )$ is convex in $( f _ { \theta } ( x ) , y )$ (such as MSE and cross-entropy loss), the function ℓ need not be convex in θ. This is the case, for instance, for typical modern ML models (e.g., if $f _ { \theta }$ is a convolutional neural network or a transformer-based language model). Hence, $( P _ { t } )$ is usually a non-convex optimization problem for which there is no straightforward way to project onto the feasibility set $( \mathrm { i . e . }$ , onto the set of no-forgetting models).

In light of these challenges, we turn to Lagrangian duality. $( P _ { t } )$ is a statistical constrained optimization problem, whose empirical dual can be written as

$$
D _ {t} = \max _ {\boldsymbol {\lambda} \in \mathbb {R} _ {+} ^ {t - 1}} \min _ {\theta \in \theta} \hat {\mathcal {L}} (\theta , \boldsymbol {\lambda}) := \frac {1}{n _ {t}} \sum_ {i = 1} ^ {n _ {t}} [ \ell (f _ {\theta} (x _ {i}), y _ {i}) ] + \sum_ {k = 1} ^ {t - 1} \lambda_ {k} \left(\frac {1}{n _ {k}} \sum_ {i = 1} ^ {n _ {k}} [ \ell (f _ {\theta} (x _ {i}), y _ {i}) ] - \epsilon_ {k}\right), (D _ {t})
$$

where $\hat { \mathcal { L } } ( \theta , \lambda )$ denotes the empirical Lagrangian, $n _ { k }$ denotes the number of samples from task k available at iteration $t ,$ and λ denotes the vector of dual variables corresponding to the task-level constraints. For a fixed $\lambda ,$ the Lagrangian ${ \hat { \mathcal { L } } } ( \theta , \lambda )$ is a regularized objective, where the losses on previous tasks act as regularizing functionals. Thus, the saddle point problem in $( D _ { t } )$ can be viewed as a two-player game, or as a regularized minimization, where the regularization weight λ is updated during the training procedure according to the degree of constraint satisfaction or violation. We elaborate on this iterative procedure when we present the primal-dual algorithm in Section 3.

Note that the weighing ofthe replayed losses relative to the loss on the current task is determined by the dual variables λ, rather than by a hyperparameter or by the number of tasks seen so far (Buzzega et al., 2020a; Michieli & Zanuttigh, 2021). Albeit simple, this is a key difference concerning previous replay and knowledge distillation approaches. In the sequel, we show that optimal dual variables $\boldsymbol { \lambda ^ { \star } }$ indicate the sensitivity of the optimal value $P _ { t }$ as a function of the constraint levels $\{ \epsilon _ { k } \} _ { k = 1 } ^ { t - 1 }$ and can thus be used as indicators of task difficulty.

## 3 Primal Dual Continual Learning

Provided we have enough samples per task and the parameterization Θ is rich enough, $( D _ { t } )$ can approximate the constrained statistical problem $( P _ { t } )$ . More precisely, the empirical duality gap, defined as the difference between the optimal value $D _ { t }$ of the empirical dual and the statistical primal $P _ { t }$ , is bounded (Chamon et al., 2023, Theorem 1). Furthermore, the dual function

$$
\hat {g} (\pmb {\lambda}) = \min _ {\theta \in \theta} \hat {\mathcal {L}} (\theta , \pmb {\lambda})
$$

is the minimum of a family of affine functions on $\lambda ,$ and thus is concave, irrespective of whether $( P _ { t } )$ is convex. As such, though gˆ may not be differentiable, it can be equipped with supergradients that provide potential ascent directions. Explicitly, a vector $s \in \mathbb { R } ^ { m }$ is a supergradient of the concave function gˆ at a point $\lambda _ { 1 }$ i $\hat { \boldsymbol g } ( \lambda _ { 2 } ) - \hat { \boldsymbol g } ( \lambda _ { 1 } ) \ge s ^ { T } ( \lambda _ { 2 } - \lambda _ { 1 } )$ for all $\lambda _ { 2 }$ . The set of all supergradients of $\hat { g }$ at $\lambda _ { 1 }$ is called the superdifferential and is denoted $\partial { \widehat { g } } ( \lambda _ { 1 } )$ . When the loss ℓ is continuous, the superdifferential of gˆ admits a simple description (Shor, 2013), namely,

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Primal-Dual Continual Learning (PDCL)
1: Input: Num. Tasks T, primal (dual) learning rate  $\eta_{p}(\eta_{d})$ , Number of primal steps per dual step  $T_{p}$ , constraint levels  $\{\epsilon_{k}\}_{k=1}^{T}$ , number of iterations  $n_{iter}$ .
2: Initialize  $\theta$ 
3: for  $t = 1, \ldots, T$  do
4: Initialize  $\lambda$ 
5: for  $i = 1, \ldots, n_{iter}$  do
6:  $\theta \leftarrow \theta - \eta_{p} \nabla_{\theta} \mathcal{L}(\theta, \lambda) \quad (\times T_{p})$  // Update primal variables
7:  $s_{k} \leftarrow \frac{1}{n_{k}} \sum_{j=1}^{n_{k}} \ell(f_{\theta}(x_{j}), y_{j}) - \epsilon_{k}, \forall k \in \{1, \ldots, t-1\}$  // Evaluate constraint slacks
8:  $\lambda_{k} \leftarrow [\lambda_{k} + \eta_{d} s_{k}]_{+}, \forall k \in \{1, \ldots, t-1\}$  // Update dual variables
9: end for
10:  $n_{1}^{\star}, \ldots, n_{t}^{\star} \leftarrow PB(\lambda_{1}, \ldots, \lambda_{t-1})$  // Partition Buffer
11:  $B_{t} \leftarrow FB(B_{t-1}, D_{t}, \{n_{k}^{\star}\}_{k=1}^{t})$  // Fill Buffer
12: end for
13: Return:  $\theta, \lambda$ .
</div>

$$
\partial \hat {g} (\boldsymbol {\lambda}) = \operatorname{conv} \left[ L \left(f _ {\theta} (\boldsymbol {\lambda})\right): f _ {\theta} (\boldsymbol {\lambda}) \in \mathcal {F} _ {\theta} ^ {\star} (\boldsymbol {\lambda}) \right],
$$

where $\begin{array} { r } { L ( f ) : = \Big [ \frac { 1 } { n _ { k } } \sum _ { i = 1 } ^ { n _ { k } } [ \ell ( f _ { \theta } ( x _ { i } ) , y _ { i } ) ] - \epsilon _ { k } \Big ] _ { k = 1 } ^ { t - 1 } } \end{array}$ , conv(S) denotes the convex hull of the set $s$ and $\begin{array} { r } { \mathcal { F } _ { \theta } ^ { \star } ( \lambda ) = \arg \operatorname* { m i n } _ { \theta } \hat { \mathcal { L } } ( f _ { \theta } , \lambda ) } \end{array}$ is the set of Lagrangian minimizers $f _ { \theta } ( \lambda )$ associated to λ.

Consequently, the outer problem $( \mathrm { i . e . , m a x } _ { \lambda \succeq 0 } \hat { g } ( \lambda ) )$ corresponds to the maximization of a concave function and can be solved via super-gradient ascent (Nedic & Ozdaglar´ , 2009). The inner minimization, however, is generally non-convex, but there is ample empirical evidence that deep neural networks can attain good local minima when trained with stochastic gradient descent (Zhang et al., 2016). Hence, the saddle-point problem $( D _ { t } )$ can be undertaken by alternating the minimization with respect to θ (line 6 in Alg. 1) and the maximization with respect to λ (line 8 in $\mathrm { A l g }$ . 1) (K. J. Arrow & Uzawa, 1960; Shor, 2013). We refer to (Chamon et al., 2023) and (Elenter et ${ \mathrm { a l . , } }$ 2024) for a thorough analysis on the convergence and primal recovery properties of this procedure in the context of constrained learning.

An overview of the proposed primal-dual continual learning method (PDCL) is provided in Algorithm 1. Note that $\bar { P } B$ (Buffer Partition) denotes a generic procedure to compute the number of samples allocated to each task at time t given a vector of dual variables λ. Similarly, $F B$ (Fill Buffer) denotes a generic mechanism for populating the buffer given a specific memory partition $\{ n _ { 1 } , \cdots , n _ { t } \}$ . Recall that at iteration t, the only samples available are the ones from the current task and those stored in the buffer $B _ { t } = \cup _ { k = 1 } ^ { t - 1 } B _ { k } ( t )$ , with $n _ { k } ( t ) = | B _ { k } ( t )$ )|.

## 3.1 Dual Variables Capture the Stability-Plasticity Trade-off

The Buffer Partition method $( P B )$ takes as input the vector of dual variables λ because they indicate relative task difficulty. In this section, we formalize this result using tools from convex variational analysis. Specifically, we leverage the fact that, though non-convex and intricate, the continual learning problem $( P _ { t } )$ is the parametrized version of a benign functional optimization problem.

The unparametrized constrained learning problem is defined as

$$
\begin{array}{r l} \tilde {P} _ {t} = \min _ {\phi \in \mathcal {F}} & \mathbb {E} _ {\mathfrak {D} _ {t}} [ \ell (\phi (x), y) ], \\ \text {s.t.} & \mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\phi (x), y) ] \leq \epsilon_ {k}, \quad \forall   k \in \{1, \ldots , t - 1 \}, \end{array}\tag{\((\tilde{P}_{t})\}
$$

where $\mathcal { F }$ denotes a compact functional space satisfying $\| \phi \| _ { L _ { 2 } } \leq R$ for every $\phi \in { \mathcal { F } }$ . For instance, $\mathcal { F }$ can be a subset of the space of continuous functions on a compact set or a reproducing kernel Hilbert space (RKHS) and $\mathcal { F } _ { \theta } \overset { \cdot } { = } \left\{ f _ { \theta } : \theta \in \Theta \right\}$ can be induced by a neural network architecture with smooth activations or a finite linear combination of kernels. The smallest choice of $\mathcal { F }$ is in fact conv $( { \mathcal { F } } _ { \theta } )$

(closed convex hull of $\mathcal { F } _ { \boldsymbol { \theta } } )$ . Analogous to the definition from Section 2,

$$
\tilde {D} _ {t} = \max _ {\tilde {\boldsymbol {\lambda}} \in \mathbb {R} _ {+} ^ {\ell - 1}} \min _ {\phi \in \mathcal {F}} \mathcal {L} (\phi , \tilde {\boldsymbol {\lambda}}) := \mathbb {E} _ {\mathfrak {D} _ {t}} [ \ell (\phi (x), y) ] + \sum_ {k = 1} ^ {t - 1} \tilde {\lambda} _ {k} \left(\mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\phi (x), y) ] - \epsilon_ {k}\right),\tag{\((\tilde{D}_{t})\}
$$

is the unparametrized empirical dual problem. The only difference between problems $( P _ { t } )$ and $( \tilde { P } _ { t } )$ is the set over which the optimization is carried out. Thus, if the parametrization Θ is rich enough $( \mathrm { e . g . }$ ., deep neural networks such as large transformers), the set $\mathcal { F } _ { \theta }$ is essentially the same as $\mathcal { F }$ , and we should expect the properties of the solutions $\boldsymbol { \lambda ^ { \star } }$ and $\tilde { \lambda } ^ { \star }$ to problems $( D _ { t } )$ and $( \tilde { D } _ { t } )$ to be similar. This insight leads us to the ν−near universality of the parametrization assumption.

Assumption 2. For all $\phi \in { \mathcal { F } }$ , there exists $\theta \in \Theta$ such that $\| \phi - f _ { \theta } \| _ { L ^ { 2 } } \leq \nu .$

The constant ν in Assumption 2 is a measure of how well $\mathcal { F } _ { \theta }$ covers $\mathcal { F }$ . Consider, for instance, that $\mathcal { F }$ is the set of continuous functions on a compact set and $\mathcal { F } _ { \theta }$ the set of functions implementable with a two-layer neural network with sigmoid activations and $K$ hidden neurons. If the parametrization has 10 neurons in the hidden layer, it is considerably worse at representing elements in $\mathcal { F }$ than one with 1000 neurons. While determining the exact value of ν is, in general, not straightforward, any $\nu > 0$ can be achieved for a large enough number of neurons (Hornik, 1991). The same holds for the number of kernels and an RKHS (Berlinet & Thomas-Agnan, 2011).

![](images/40781f7abc0f98d821d6c7d62755e87a6c80ab97b5e5f30b21f2c8b646ae76df.jpg)  
Figure 1: Diagram of a ν−Universal Parametrization $\mathcal { F } _ { \Theta }$ of $\mathcal { F }$ .

To formalize the fact that $\boldsymbol { \lambda ^ { \star } }$ measures relative task difficulty, we combine two results. First, optimal duals $\tilde { \lambda } ^ { \star }$ of the unparametrized problem $( \tilde { D } _ { t } )$ capture the sensitivity of $\tilde { P } _ { t }$ with respect to constraint perturbations (see Appendix A.2) and second, dual variables $\boldsymbol { \lambda ^ { \star } }$ of the empirical parametrized problem $( D _ { t } )$ can not be too far from $\tilde { \lambda } ^ { \star }$ (see Appendix $\mathrm { A . 4 } )$ . We now state an assumption (specifically a constraint qualification) guaranteeing that the aforementioned results hold. Assumption 3. The loss ℓ is $M - \mathrm { I }$ Lipschitz and convex, the functional space $\mathcal { F }$ is convex, and there exists a strictly feasible solution $( \mathrm { i . e . , } \exists \phi \in \mathcal { F }$ such that $\mathbb { E } _ { \mathfrak { D } _ { k } } [ \ell ( f ( x ) , y ) ] < \epsilon _ { k } , \forall k )$

Note that we require convexity of the losses with respect to their functional arguments and not model parameters $\theta ,$ , which holds for most typical losses, $\mathrm { e . g . }$ , mean squared error and cross-entropy loss. Along with the boundedness of ${ \mathcal F } .$ , this assumption guarantees uniform convergence (Shalev-Shwartz et al., 2009, Theorem 5), implying that with probability at least $1 - \delta ,$ for all $\phi \in { \mathcal { F } }$ we have:

$$
\left| \mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (f (x), y) ] - \frac {1}{n _ {k}} \sum_ {i = 1} ^ {n _ {k}} \ell (f (x _ {i}), y _ {i}) \right| \leq \zeta (n _ {k}, \delta), \forall k = 1, \dots , T,\tag{1}
$$

where the sample complexity function $\zeta \left( n _ { k } , \delta \right)$ is of order $\mathcal { O } \left( R M \sqrt { d \log \left( n _ { k } \right) \log ( d / \delta ) } / \sqrt { n _ { k } } \right)$ Additionally, Assumption 3 characterizes the curvature $\mu$ of the unparametrized dual function $\tilde { g } ( \lambda ) = \operatorname* { m i n } _ { \phi \in \mathcal { F } } \mathcal { L } ( \phi , \tilde { \lambda } )$ , on which we elaborate in Appendix $_ { \mathrm { A . 6 . } }$ and leads to the following theorem.

Theorem 1. Under Assumptions 2 and 3, with probability at least $1 - t \delta , \lambda ^ { \star }$ belongs to the ω−subdifferential of $\tilde { P } _ { t } ( \epsilon )$ at ϵ. That is:

−λ<sup>⋆</sup> ∈ ∂<sub>ω</sub>P<sup>˜</sup><sub>t</sub>(ϵ), with the constant $\begin{array} { r } { \omega ^ { 2 } = \frac { 2 } { u } \left[ M \nu ( 1 + \| \lambda ^ { \star } \| _ { 1 } ) + 6 \zeta ( \tilde { n } , \delta ) ( 1 + \Delta ) \right] } \end{array}$ , the sensitivity parameter $\Delta = \mathrm { m a x } \{ \| \tilde { \lambda } ^ { \star } \| _ { 1 } , \| \lambda ^ { \star } \| _ { 1 } \}$ , and the sample complexity given by $\begin{array} { r } { { \tilde { n } } = \operatorname* { m i n } _ { i = 1 , \dots , T } n _ { i } ( T ) } \end{array}$

Theorem 1 implies that $\boldsymbol { \lambda ^ { \star } }$ yields a near global linear under-estimator of $\tilde { P } _ { t }$ at ϵ. In particular, the impact of a perturbation $\gamma _ { k } = [ 0 , \cdots , 0 , \gamma , 0 , \ldots , 0 ]$ of the forgetting tolerances ϵ is described by

$$
\tilde {P} _ {t} (\epsilon + \gamma_ {k}) - \tilde {P} _ {t} (\epsilon) \geq - \lambda_ {k} ^ {\star} \gamma - \omega .
$$

This means that the dual variable $- \lambda _ { k } ^ { \star }$ carries information about the relative difficulty of task $k .$ Specifically, tightening the constraint associated to task $k \left( \gamma < 0 \right)$ restricts the feasible set, causing a degradation of the optimal value of $( \tilde { P } _ { t } ) \left( \mathrm { i . e . } \right.$ , the performance on the current task) at a rate larger than $\lambda _ { k } ^ { \star } ,$ , with an offset of $\omega .$ In this sense, optimal dual variables reflect how hard it is to achieve good performance in the current task (plasticity), while maintaining the performance on a previous task (stability). Similarly, relaxing the constraint associated to a certain task k $( \mathrm { i } . \mathrm { e } . , \gamma > 0 )$ would expand the feasible set, leading to a potential improvement of the expected loss in the current task of at most $\lambda _ { k } ^ { \star } \gamma + \omega$ . In this sense, $\lambda _ { k } ^ { \star }$ captures the stability-plasticity trade-off associated to task k.

![](images/76c80f7857595ded85d4c2cc00920d6a287ff51f7935c617d9257281fe2ee612.jpg)

![](images/14148413d8af0b187ab053f99212d9477ed23c780201850303a545df6d03d9a4.jpg)  
Figure 2: Left: Dual variables indicate the sensitivity of the performance on the current task with respect to the no-forgetting requirement enforced on past tasks (Theorem 1). Right: Impact of minimum enforced partition size in speech classification (see Section 3.2).

Theorem 1 indicates that, as the capacity of the model increases, the constant ν decreases and the quality of $\boldsymbol { \lambda ^ { \star } }$ as a sensitivity indicator improves. This emphasizes the importance of rich parametrizations in (constrained) learning, which has been established by (Arora et al., 2018; Safran et al., 2021; Elenter et al., 2024; Bubeck & Sellke, 2021), among others. Conversely, as we reduce the size of the memory buffer, potentially decreasing n˜, the sample complexity function $\zeta ( \tilde { n } , \delta )$ grows and degrades the information captured by $\boldsymbol { \lambda } ^ { \star }$ . This is not unlike other CL strategies that suffer in small budget regimes (Chaudhry et al., 2019), particularly in settings with low task similarity.

## 3.2 Adaptive Buffer Partition

In light of Theorem 1, it is sensible to partition the buffer across different tasks as an increasing function of $\boldsymbol { \lambda ^ { \star } }$ , allocating more resources to tasks with higher associated dual variable. That is, $\begin{array} { r } { { \pmb n } ( t ) = | \pmb { \mathcal { B } } | \frac { \pmb { \lambda } ( t ) } { \| \pmb { \lambda } ( t ) \| _ { 1 } } } \end{array}$ . To prevent the potential issue of allocating no samples to a task when $\lambda = 0$ we impose a lower bound on the partition size. This contemplates the fact that tasks deemed easy at a certain iteration t might eventually limit the performance of a future task $t ^ { \prime } .$ This leads to a buffer partition given by the following affine map on $\lambda ( t )$

$$
P B (\boldsymbol {\lambda} (t)) = | \mathcal {B} | \left(\alpha \frac {\boldsymbol {\lambda} (t)}{\| \boldsymbol {\lambda} (t) \| _ {1}} + \frac {1 - \alpha}{t}\right).\tag{PB}
$$

with $\alpha \in [ 0 , 1 ]$ . The larger the value of α the smaller the lower bound. For instance, setting $\alpha = 1 / 2$ (value used in experiments) guarantees a minimum partition size of $| B | / 2 t$ samples at iteration $t ,$ while $\alpha = 1$ gives a minimum partition size of 0. This strategy leads to a dynamic partition of the buffer that prioritizes sensitive tasks, as measured by how much they limit the performance on the current one. We track the accumulation of the slacks associated to the current task in an artificial dual $\lambda _ { t } ( t )$ (i.e, not associated to a constraint) and concatenate it to $\lambda ( t )$ to compute the partition of the current task. A more intricate partition strategy that contemplates both the sensitivity information provided by λ and the generalization gap is described in Appendix A.11.

![](images/f6f4acfbba6286ecdea33ea708995991bf55a9c674215392ed755962f46d7a90.jpg)

![](images/d4d48f47abc59937b18de49ae423910ce452be249fa0dafbcbe397c25f85ca76.jpg)

![](images/1cf0957591dbb9ee73dcc88911d5ad11b7ef633d8bd279c5252da53fdc13538f.jpg)  
Figure 3: Leveraging dual variables $\mathrm { ( P D C L _ { 0 } ) }$ to adaptively weight the replay losses provides an improvement over fixed regularization weights (ER Ring and Reservoir). Partitioning the buffer non-uniformly (PDCL) according to the task difficulty measured by λ improves over uniform $( \mathrm { P D C L _ { 0 } }$ ER Ring, AGEM) partitions. Gradient projections (AGEM) tend to perform worse than replays.

![](images/0d796550ced6d17da3027e2b45348038d3ecc1e48b7d6fcbcb45384569f6162a.jpg)

![](images/239f6a91614541a512cf18738c2f7cd6f1723014059571684a7a583fa9be16e8.jpg)

![](images/1516387b5fcea64659a0dfe8f68503e2fce8eeb38bf7fec08221a621d4e9cda9.jpg)  
Figure 4: Left: Evolution of non-uniform partitions obtained by (PDCL) in OrganA, and its distance from a uniform one. Center: If ϵ is set too loose, we allow larger forgetting. Conversely, if ϵ is too tight, $( P _ { t } )$ can become harder to solve due to the reduction of its feasible set. Right: For a tight $\epsilon ,$ we violate the constraint and the associated dual variable can grow indefinitely. For a loose $\epsilon , \lambda _ { 0 }  0$ indicating that the performance on task 0 is not limiting learning the current task.

## 4 Margin Aware Sample Selection

When filling the buffer by sampling uniformly at random from each observed dataset, there is no sampling bias. That is, the distributions $\mathfrak { B } _ { k } ( x , y )$ underlying the memory buffer and the data distributions $\mathfrak { D } _ { k } ( x , y )$ match. In this case, the solution of $( P _ { t } )$ has no-forgetting PAC learning guarantees; see e.g., (Peng et al., 2023, Theorem 1). Nevertheless, inducing a bias in the buffer distribution $\mathfrak { B } _ { k } ( x , y )$ by selecting which samples to store can be beneficial due to the following:

• The i.i.d. assumption may not hold, in which case sample selection has theoretical and empirical benefits, particularly as an outlier detection mechanism (Sun et al., 2021; Peng et al., 2023; Borsos et al., 2020).

• Random sampling is not optimal in terms of expected risk decrease rate, which is the main property exploited in active and curriculum learning (Settles, 2009; Gentile et al., 2022; Elenter et al., 2022). In particular, Hacohen et al. (2022) suggest that easy samples are preferred in low-budget regimes, while hard instances provide better results above a certain budget threshold.

## 4.1 Identifying Impactful Samples

Instead of task-level constraints, we can formulate continual learning as enforcing a no-forgetting requirement at the sample level. For a given tightness ϵ, this constraint is stricter than the tasklevel constraint and enables sample selection. This no-forgetting requirement can be written as:

$$
\begin{array}{l} S _ {t} = \min _ {\theta \in \Theta} \mathbb {E} _ {\mathfrak {D} _ {t}} [ \ell (f _ {\theta} (x), y) ], \\ \text { s.t. } \quad \ell (f _ {\theta} (x), y) \leq \epsilon_ {x, y}, \quad \mathfrak {B} _ {k} (t) \text {-a.e.} \quad \forall   k = 1, \ldots , t - 1, \end{array} \tag {S_{t}}
$$

![](images/85e156895872796753973f0e2e133690a9b20a78a9655c4aa198bfe7b4d7309e.jpg)

where $\cdot _ { \mathrm { a . c \vec { \mathbf { \psi } } } } ,$ (almost everywhere) means that the constraint should hold for all $( x , y )$ except possibly a set of $\mathfrak { B } _ { k } ( t )$ -measure 0. As described in the previous section, non-uniform sampling induces a bias in the buffer distribution. In what follows, we put forward a dual variable-based sampling strategy, in the same vein as the buffer partition strategy, that is beneficial in terms of expected risk reduction. We refer to (Farquhar et al., 2020) for a general theoretical analysis of the distributional bias induced by active sampling in the context of replay methods.

Figure 5: Class clusters with $\lambda _ { x , y }$ indicated by marker size. Large dual variables accumulate in the task decision boundary and edges cluster.

The dual update rule (Line 8) in the sample-wise version of Algorithm 1 is given by:

$$
\lambda_ {x, y} \leftarrow [ \lambda_ {x, y} + \eta_ {d} (\ell (f _ {\theta} (x), y) - \epsilon_ {x, y}) ] _ {+}.
$$

Thus, in this formulation, dual variables accumulate the sample-wise constraint slacks over the entire learning procedure. This allows dual variables to be used as a measure of sample informativeness, while at the same time affecting the local optimum to which the primal-dual algorithm converges. Similar ideas on monitoring the evolution of the loss—or training dynamics—for specific samples in order to recognize impactful instances have been used in generalization analyses (Toneva et al., 2019; Katharopoulos & Fleuret, 2018) and active learning (Wang et al., 2021a; Elenter et al., 2022). In this case, a similar sensitivity analysis as in Section 3.1 holds at the sample level:

![](images/3b7ecc1e00c4493d6a9143fcb135a1b2894da91abf6f79d93ba5f77d69a697b3.jpg)

![](images/c5217ed70b82c0555309ebaf70c02175a0820b73127b8bf8d51d5eeae81e7989.jpg)

![](images/cdf328048a2ca0008ce1aa28ff82a52d811d46ec9ab711f941e3abf325162390.jpg)

![](images/a7f5d8f5de72926307f769e27359ddd3abe6ac2ff328f3c1795ec71845603d5e.jpg)  
Figure 6: Top row shows mean accuracy (higher is better) and Bottom row average forgetting (lower is better) across tasks after the last iteration. For a given task i, its Forgetting (Chaudhry et al., 2018) after observing task j is the difference between the maximum performance level achieved in the past and the current one, i.e: Forgetting (j) = max<sub>l∈{1,··· ,j−1}</sub> (acc<sub>i</sub>(l) − acc<sub>i</sub>(j)).

Corollary 1. Let ${ \tilde { S } } _ { t }$ denote the unparametrized optimal value function of problem $S _ { t }$ . Under Assumptions 2 and 3, with probability at least $1 - t \delta , \lambda _ { x , y } ^ { \star }$ belongs to the ω−subdifferential of $\tilde { S } _ { t } ( \epsilon )$ at ϵ. That $i s , \ - \lambda _ { x , y } ^ { \star } \in \partial _ { \omega } \tilde { S } _ { t } ( \epsilon _ { x , y } )$ with ω(δ) as in Theorem 1 .

As in the task-level constraints, Corollary 1 implies that the constraint whose perturbation has the most potential impact on $S _ { t }$ is the constraint with the highest associated optimal dual variable. As such, infinitesimally tightening the constraint in a neighborhood $( x , y )$ would restrict the feasible set, causing an increase of the optimal value of $S _ { t }$ at a rate larger than $\lambda _ { x , y } .$ In that sense, the magnitude of dual variables can be used as a measure of informativeness of a training sample. Similarly to non-support vectors in SVMs, samples associated to inactive constraints $( \mathrm { i . e . , \bar { \{ } }  ( x , y ) : \lambda _ { x , y } ^ { \star } ( t ) = \mathbf { \bar { 0 } } \} )$ ), are considered uninformative. This notion of informativeness is illustrated in Figure 5.

## 4.2 Dual Variable Based Sample Selection

In Primal-Dual Continual Learning with Sample selection (PDCL-S), the buffer is filled by leveraging the per-sample dual variables $\lambda _ { x , y } ,$ which act as an informativeness score, indicating the sensitivity of the performance on current task with respect to each stored sample. We then interpret $\Delta ( t ) / \| \lambda ( \dot { t } ) \| _ { 1 }$ as a probability distribution over $\mathscr { X } \times \bar { \mathscr { y } }$ , where the probability of storing a pair $( x , y )$ is given by the magnitude of its dual variable $\lambda _ { x , y } ( t )$ . Specifically, given a buffer partition $n _ { 1 } , \cdots , n _ { t }$ , the generic mechanism FB for populating the buffer in Algorithm 1 is implemented by sampling without replacement from this discrete distribution. Thus, (PDCL-S) aims to match the buffer-induced distribution B(t) and the optimal dual variable function λ(t).

$$
\mathcal {B} _ {k} (t) \leftarrow F B (\boldsymbol {\lambda} (t), \boldsymbol {n} (t)) = \left\{\left(x _ {1}, y _ {1}\right), \dots , \left(x _ {n _ {k} (t)}, y _ {n _ {k} (t)}\right) \right\} \sim \frac {\boldsymbol {\lambda} _ {k} (t)}{\| \boldsymbol {\lambda} _ {k} (t) \| _ {1}}\tag{FB}
$$

where $\lambda _ { k } ( t ) = [ \lambda _ { x , y } ( t ) : ( x , y ) \in \mathcal { B } _ { k } ( t ) ]$ denotes the vector of dual variables associated to the samples in the $k ^ { t h }$ partition of the memory buffer. Observe that the procedure of defining informativeness scores (e.g, output entropy (Settles, 2009), gradient norm (Ash et al., 2019), expected risk reduction (Elenter et al., 2022)) to perform sample selection is ubiquitous in active learning.

## 5 Experimental Validation

We evaluate the proposed strategy in four continual learning benchmarks of diverse structures: An image classification task using Tiny-ImageNet (Le & Yang, 2015), a speech classification task with the SpeechCommands dataset (Warden, 2018), a medical image (Abdominal CT Scan) task (OrganA (Yang et al., 2021)) and the simpler sequential MNIST (LeCun & Cortes, 2010) dataset where we consider the online CL setting (Aljundi et al., 2019). We follow the Class Incremental Learning protocol (Van de Ven & Tolias, 2019), where datasets are split into disjoint sets, each containing a subset of the classes. MNIST, SpeechCommands, and OrganA are split into 2 class tasks, while Tiny-ImageNet is split into tasks with 4 classes. We follow (Buzzega et al., 2020a) and match the model complexity to the difficulty of the problem at hand. In MNIST, we use a three-layer MLP with ReLU activations. In Seq. SpeechCommands and OrganA, we use 1-D and 2-D CNN respectively, with ReLU activations, Batch Normalization and MaxPooling. In TinyImagenet, we use a ResNet-18 architecture (He et al., 2016). At each iteration t, models are trained using $f _ { t - 1 }$ as initialization. We adopt the baseline implementations of Mammoth<sup>1</sup>, as done in (Buzzega et al., 2020b), and use the reported hyperparameters for the baselines. We report the final average accuracy and forgetting across five different random seeds. Additional experimental details are provided in Appendix A.10.

We analyze three versions of our approach: (i) $\mathrm { P D C L _ { 0 } } \mathrm { . }$ which uses dual variables as regularization weights for the replay losses, (ii) PDCL: which incorporates adaptive buffer partitioning, and (iii) PDCL-S: which also performs sample selection. As baselines, we consider the continual learning strategies presented in Appendix A.1 that are most related to our work, namely, Experience Replay (Rolnick et al., 2018), X-DER (Boschini et al., 2022), A-GEM (Chaudhry et al., 2018), GSS(Aljundi et al., 2019). A-GEM and GSS are particularly relevant due to their similar constrained optimization perspective, and ER and X-DER are strong, standard baselines (Zhou et al., 2023). These numerical results, showcased in Figures 3, 4 and 6, aim to measure the impact of three factors:

• Adaptive weights (i.e., dual variables) as opposed to fixed hyper-parameters to regularize the replay losses $( \mathbf { E } \mathbf { R }  \mathbf { P } \mathbf { D } \mathbf { C } \mathbf { L } _ { 0 } )$ .

• Adaptive buffer partitioning as opposed to fixed or uniform partitions $\mathbf { ( P D C L _ { 0 } \to P D C L ) }$

• Dual variable-based sample selection as opposed to uniform sampling $\mathbf { ( P D C L \to P D C L { - } S ) }$

We observe that undertaking the continual learning problem with a primal-dual algorithm and leveraging the information provided by dual variables leads to comparatively high mean accuracy and low forgetting in almost all buffer sizes and benchmarks. Nevertheless, in the small buffer setting of the speech processing task (right column in Figure $^ { 6 ) , }$ the performance of PDCL is modest and sample selection does not provide an improvement. This is consistent with prior work on the effectiveness of sample selection (Araujo et al., 2022) and with the fact that small memory buffers can negatively impact the quality of $\boldsymbol { \lambda ^ { \star } }$ as a sensitivity indicator (see Theorem 1). The limited benefits of sample selection can also be attributed to the fact that, in constrained learning, problems with more constraints (sample-wise vs. task-wise) increase the condition number of the dual function, making its maximization harder (Elenter et al., 2024). Moreover, in some settings, no method outperforms ER by a significant margin, which is consistent with recent surveys (Zhou et al., 2023). As shown in Figure 5, large dual variables can correspond to both outliers and inliers. Indeed, informative samples and outliers (such as mislabeled samples) may be hard to distinguish. This supports recent empirical findings (Karamcheti et al., 2021) indicating that many active and continual learning algorithms consistently acquire samples that most models prefer not to learn.

## 6 Conclusion

This work demonstrates that directly addressing the constrained optimization problem in continual learning via Lagrangian duality is both feasible and beneficial. Leveraging this framework, we develop adaptive methods for managing replay buffers at both the task and sample levels, mitigating catastrophic forgetting and balancing the stability-plasticity trade-off. Our results show that dual variables capture sensitivity information about the optimization problem, enabling us to partition the buffer by allocating more resources to harder tasks and selecting the most impactful samples. These strategies lead to improved performance across diverse benchmarks. However, the quality of dual variables as sensitivity indicators degrades in small budget regimes and when the richness of the parameterization is insufficient relative to the problem’s difficulty. Future work could explore several promising directions. For instance, in the context of large language models, constrained formulations of continual learning remain, for the most part, unexplored. Additionally, developing a pre-training method that yields non-uniform, feasible, and informative constraint upper bounds could significantly improve the performance of the proposed approach. Further research into the conditions under which sample selection is provably beneficial would also be valuable.

## References

Rahaf Aljundi, Min Lin, Baptiste Goujaud, and Yoshua Bengio. Online continual learning with no task boundaries. CoRR, abs/1903.08671, 2019. URL http://arxiv.org/abs/1903.08671. (Cit. on p. 1, 9, 15)

Vladimir Araujo, Helena Balabin, Julio Hurtado, Alvaro Soto, and Marie-Francine Moens. How relevant is selective memory population in lifelong language learning? arXiv preprint arXiv:2210.00940, 2022. (Cit. on p. 9)

Sanjeev Arora, Nadav Cohen, and Elad Hazan. On the optimization of deep networks: Implicit acceleration by overparameterization. In International conference on machine learning, pp. 244– 253. PMLR, 2018. (Cit. on p. 6)

Jordan T Ash, Chicheng Zhang, Akshay Krishnamurthy, John Langford, and Alekh Agarwal. Deep batch active learning by diverse, uncertain gradient lower bounds. In International Conference on Learning Representations, 2019. (Cit. on p. 8)

Alain Berlinet and Christine Thomas-Agnan. Reproducing kernel Hilbert spaces in probability and statistics. Springer Science & Business Media, 2011. (Cit. on p. 5)

Paul T Boggs and Jon W Tolle. Sequential quadratic programming. Acta numerica, 4:1–51, 1995. (Cit. on p. 23)

J. Frédéric Bonnans and Alexander Shapiro. Optimization problems with perturbations: A guided tour. SIAM Review, 40(2):228–264, 1998. ISSN 00361445. URL http://www.jstor.org/stable/2653333. (Cit. on p. 16)

Zalán Borsos, Mojmir Mutny, and Andreas Krause. Coresets via bilevel optimization for continual learning and streaming. Advances in neural information processing systems, 33:14879–14890, 2020. (Cit. on p. 7)

Matteo Boschini, Lorenzo Bonicelli, Pietro Buzzega, Angelo Porrello, and Simone Calderara. Class incremental continual learning into the extended der-verse. IEEE Transactions on Pattern Analysis and Machine Intelligence, 45(5):5497–5512, 2022. (Cit. on p. 9, 15)

Sébastien Bubeck and Mark Sellke. A universal law of robustness via isoperimetry. Advances in Neural Information Processing Systems, 34:28811–28822, 2021. (Cit. on p. 6)

Pietro Buzzega, Matteo Boschini, Angelo Porrello, Davide Abati, and Simone Calderara. Dark experience for general continual learning: a strong, simple baseline. Advances in neural information processing systems, 33:15920–15930, 2020a. (Cit. on p. 3, 9, 15)

Pietro Buzzega, Matteo Boschini, Angelo Porrello, Davide Abati, and Simone Calderara. Dark experience for general continual learning: a strong, simple baseline, 2020b. (Cit. on p. 9, 15)

Luiz F. O. Chamon, Santiago Paternain, Miguel Calvo-Fullana, and Alejandro Ribeiro. Constrained learning with non-convex losses. IEEE Transactions on Information Theory, 69(3):1739–1760, 2023. doi: 10.1109/TIT.2022.3187948. (Cit. on p. 2, 3, 4)

Arslan Chaudhry, Marc’Aurelio Ranzato, Marcus Rohrbach, and Mohamed Elhoseiny. Efficient lifelong learning with a-gem. In International Conference on Learning Representations, 2018. (Cit. on p. 1, 8, 9, 15)

Arslan Chaudhry, Marcus Rohrbach, Mohamed Elhoseiny, Thalaiyasingam Ajanthan, Puneet K Dokania, Philip HS Torr, and Marc’Aurelio Ranzato. On tiny episodic memories in continual learning. arXiv preprint arXiv:1902.10486, 2019. (Cit. on p. 6)

Paul F Christiano, Jan Leike, Tom Brown, Miljan Martic, Shane Legg, and Dario Amodei. Deep reinforcement learning from human preferences. Advances in neural information processing systems, 30, 2017. (Cit. on p. 1)

Matthias De Lange, Rahaf Aljundi, Marc Masana, Sarah Parisot, Xu Jia, Aleš Leonardis, Gregory Slabaugh, and Tinne Tuytelaars. A continual learning survey: Defying forgetting in classification tasks. IEEE transactions on pattern analysis and machine intelligence, 44(7):3366–3385, 2021. (Cit. on p. 2, 15)

Juan Elenter, Navid NaderiAlizadeh, and Alejandro Ribeiro. A lagrangian duality approach to active learning. Advances in Neural Information Processing Systems, 35:37575–37589, 2022. (Cit. on p. 7, 8, 21, 22)

Juan Elenter, Luiz F. O. Chamon, and Alejandro Ribeiro. Near-optimal solutions of constrained learning problems. In International Conference on Learning Representations ICLR, 2024. (Cit. on p. 4, 6, 9)

Beyza Ermis, Giovanni Zappella, Martin Wistuba, Aditya Rawal, and Cedric Archambeau. Memory efficient continual learning with transformers. Advances in Neural Information Processing Systems, 35:10629–10642, 2022. (Cit. on p. 15)

Sebastian Farquhar, Yarin Gal, and Tom Rainforth. On statistical bias in active learning: How and when to fix it. In International Conference on Learning Representations, 2020. (Cit. on p. 7)

Claudio Gentile, Zhilei Wang, and Tong Zhang. Fast rates in pool-based batch active learning, 2022. (Cit. on p. 7)

Philip E Gill and Elizabeth Wong. Sequential quadratic programming methods. In Mixed integer nonlinear programming, pp. 147–224. Springer, 2011. (Cit. on p. 24)

Vincent Guigues. Inexact stochastic mirror descent for two-stage nonlinear stochastic programs, 2020. (Cit. on p. 21)

Yiduo Guo, Bing Liu, and Dongyan Zhao. Online continual learning through mutual information maximization. In International Conference on Machine Learning, pp. 8109–8126. PMLR, 2022. (Cit. on p. 15)

Guy Hacohen, Avihu Dekel, and Daphna Weinshall. Active learning on a budget: Opposite strategies suit high and low budgets. In International Conference on Machine Learning, pp. 8175–8195. PMLR, 2022. (Cit. on p. 7)

Raia Hadsell, Dushyant Rao, Andrei A Rusu, and Razvan Pascanu. Embracing change: Continual learning in deep neural networks. Trends in cognitive sciences, 24(12):1028–1040, 2020. (Cit. on p. 15)

Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep residual learning for image recognition. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), June 2016. (Cit. on p. 9)

Kurt Hornik. Approximation capabilities of multilayer feedforward networks. Neural networks, 4(2): 251–257, 1991. (Cit. on p. 5)

Ignacio Hounie, Alejandro Ribeiro, and Luiz FO Chamon. Resilient constrained learning. Advances in Neural Information Processing Systems, 36, 2024. (Cit. on p. 19)

L. Hurwicz K. J. Arrow and H. Uzawa. Studies in linear and non-linear programming, by k. j. arrow, l. hurwicz and h. uzawa. stanford university press, 1958. 229 pages. Canadian Mathematical Bulletin, 3(3):196–198, 1960. doi: 10.1017/S0008439500025522. (Cit. on p. 4)

Siddharth Karamcheti, Ranjay Krishna, Li Fei-Fei 0001, and Christopher D. Manning. Mind your outliers! investigating the negative impact of outliers on active learning for visual question answering. In Chengqing Zong, Fei Xia, Wenjie Li 0002, and Roberto Navigli (eds.), Proceedings ofthe 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing, ACL/IJCNLP 2021, (Volume 1: Long Papers), Virtual Event, August 1-6, 2021, pp. 7265–7281. Association for Computational Linguistics, 2021. ISBN 978-1-954085-52-7. URL https://aclanthology.org/2021.acl-long.564. (Cit. on p. 9)

Angelos Katharopoulos and François Fleuret. Not all samples are created equal: Deep learning with importance sampling. In International conference on machine learning, pp. 2525–2534. PMLR, 2018. (Cit. on p. 8)

Zixuan Ke, Haowei Lin, Yijia Shao, Hu Xu, Lei Shu, and Bing Liu. Continual training of language models for few-shot learning. In Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing, pp. 10205–10216, 2022. (Cit. on p. 15)

Diederik P Kingma and Jimmy Ba. Adam: A method for stochastic optimization. arXiv preprint arXiv:1412.6980, 2014. (Cit. on p. 22)

B Ravi Kiran, Ibrahim Sobh, Victor Talpaert, Patrick Mannion, Ahmad A Al Sallab, Senthil Yogamani, and Patrick Pérez. Deep reinforcement learning for autonomous driving: A survey. IEEE Transactions on Intelligent Transportation Systems, 23(6):4909–4926, 2021. (Cit. on p. 15)

James Kirkpatrick, Razvan Pascanu, Neil Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei A Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, et al. Overcoming catastrophic forgetting in neural networks. Proceedings ofthe national academy ofsciences, 114 (13):3521–3526, 2017. (Cit. on p. 1, 15)

Igor Kononenko. Machine learning for medical diagnosis: history, state of the art and perspective. Artificial Intelligence in medicine, 23(1):89–109, 2001. (Cit. on p. 15)

Dieter Kraft. A software package for sequential quadratic programming. Forschungsbericht- Deutsche Forschungs- und Versuchsanstaltfur Luft- und Raumfahrt, 1988. (Cit. on p. 23)

Andrew J Kurdila and Michael Zabarankin. Convexfunctional analysis. Springer Science & Business Media, 2006. (Cit. on p. 20)

Ya Le and Xuan S. Yang. Tiny imagenet visual recognition challenge. 2015. (Cit. on p. 8)

Yann LeCun and Corinna Cortes. MNIST handwritten digit database. 2010. URL http://yann.lecun. com/exdb/mnist/. (Cit. on p. 8)

Chaoyue Liu, Libin Zhu, and Mikhail Belkin. Loss landscapes and optimization in over-parameterized non-linear systems and neural networks. Applied and Computational Harmonic Analysis, 59: 85–116, 2022. (Cit. on p. 3)

David Lopez-Paz and Marc’Aurelio Ranzato. Gradient episodic memory for continual learning. Advances in neural information processing systems, 30, 2017. (Cit. on p. 1, 15)

Arun Mallya and Svetlana Lazebnik. Packnet: Adding multiple tasks to a single network by iterative pruning. In Proceedings of the IEEE conference on Computer Vision and Pattern Recognition, pp. 7765–7773, 2018. (Cit. on p. 15)

Marc Masana, Xialei Liu, Bartłomiej Twardowski, Mikel Menta, Andrew D Bagdanov, and Joost Van De Weijer. Class-incremental learning: survey and performance evaluation on image classification. IEEE Transactions on Pattern Analysis and Machine Intelligence, 45(5):5513–5533, 2022. (Cit. on p. 2, 15)

Umberto Michieli and Pietro Zanuttigh. Knowledge distillation for incremental learning in semantic segmentation. Computer Vision and Image Understanding, 205:103167, 2021. ISSN 1077-3142. doi: https://doi.org/10.1016/j.cviu.2021.103167. URL https://www.sciencedirect.com/science/ article/pii/S1077314221000114. (Cit. on p. 3)

Angelia Nedic and Asuman Ozdaglar. Approximate primal solutions and rate analysis for dual´ subgradient methods. SIAM Journal on Optimization, 19(4):1757–1780, 2009. doi: 10.1137/ 070708111. URL https://doi.org/10.1137/070708111. (Cit. on p. 4)

Liangzu Peng, Paris Giampouras, and René Vidal. The ideal continual learner: An agent that never forgets. In International Conference on Machine Learning, pp. 27585–27610. PMLR, 2023. (Cit. on p. 1, 2, 7, 15)

Sylvestre-Alvise Rebuffi, Alexander Kolesnikov, and Christoph H. Lampert. icarl: Incremental classifier and representation learning. CoRR, abs/1611.07725, 2016. URL http://arxiv.org/abs/ 1611.07725. (Cit. on p. 15)

R Tyrrell Rockafellar. Convex analysis, volume 11. Princeton university press, 1997. (Cit. on p. 16)

David Rolnick, Arun Ahuja, Jonathan Schwarz, Timothy P. Lillicrap, and Greg Wayne. Experience replay for continual learning. CoRR, abs/1811.11682, 2018. URL http://arxiv.org/abs/1811.11682. (Cit. on p. 9, 15)

Itay M Safran, Gilad Yehudai, and Ohad Shamir. The effects of mild over-parameterization on the optimization landscape of shallow relu neural networks. In Conference on Learning Theory, pp. 3889–3934. PMLR, 2021. (Cit. on p. 6)

Burr Settles. Active learning literature survey. 2009. (Cit. on p. 7, 8)

Shai Shalev-Shwartz, Ohad Shamir, Nathan Srebro, and Karthik Sridharan. Stochastic convex optimization. In COLT, volume 2, pp. 5, 2009. (Cit. on p. 5, 17, 21, 23)

N.Z. Shor. Nondifferentiable Optimization and Polynomial Problems. Nonconvex Optimization and Its Applications. Springer US, 2013. ISBN 9781475760156. URL https://books.google.com/ books?id=\_L\_VBwAAQBAJ. (Cit. on p. 4)

Shagun Sodhani, Mojtaba Faramarzi, Sanket Vaibhav Mehta, Pranshu Malviya, Mohamed Abdelsalam, Janarthanan Janarthanan, and Sarath Chandar. An introduction to lifelong supervised learning. arXiv preprint arXiv:2207.04354, 2022. (Cit. on p. 15)

Shengyang Sun, Daniele Calandriello, Huiyi Hu, Ang Li, and Michalis Titsias. Information-theoretic online memory selection for continual learning. In International Conference on Learning Representations, 2021. (Cit. on p. 7)

Sebastian Thrun and Tom Mitchell. Lifelong robot learning. Robotics and Autonomous Systems, 15 (1):25 – 46, July 1995. (Cit. on p. 1)

Mariya Toneva, Alessandro Sordoni, Remi Tachet des Combes, Adam Trischler, Yoshua Bengio, and Geoffrey J. Gordon. An empirical study of example forgetting during deep neural network learning. In International Conference on Learning Representations, 2019. URL https://openreview. net/forum?id=BJlxm30cKm. (Cit. on p. 8)

Gido M Van de Ven and Andreas S Tolias. Three scenarios for continual learning. arXiv preprint arXiv:1904.07734, 2019. (Cit. on p. 9)

Jeffrey S Vitter. Random sampling with a reservoir. ACM Transactions on Mathematical Software (TOMS), 11(1):37–57, 1985. (Cit. on p. 15)

Haonan Wang, Wei Huang, Andrew Margenot, Hanghang Tong, and Jingrui He. Deep active learning by leveraging training dynamics. CoRR, abs/2110.08611, 2021a. URL https://arxiv.org/abs/2110. 08611. (Cit. on p. 8)

Shipeng Wang, Xiaorong Li, Jian Sun, and Zongben Xu. Training networks in null space of feature covariance for continual learning. In 2021 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 184–193. IEEE, 2021b. (Cit. on p. 1)

Pete Warden. Speech commands: A dataset for limited-vocabulary speech recognition. CoRR, abs/1804.03209, 2018. URL http://arxiv.org/abs/1804.03209. (Cit. on p. 8)

Jiancheng Yang, Rui Shi, Donglai Wei, Zequan Liu, Lin Zhao, Bilian Ke, Hanspeter Pfister, and Bingbing Ni. Medmnist v2: A large-scale lightweight benchmark for 2d and 3d biomedical image classification. CoRR, abs/2110.14795, 2021. URL https://arxiv.org/abs/2110.14795. (Cit. on p. 8)

Friedemann Zenke, Ben Poole, and Surya Ganguli. Continual learning through synaptic intelligence. In International conference on machine learning, pp. 3987–3995. PMLR, 2017. (Cit. on p. 15)

Chiyuan Zhang, Samy Bengio, Moritz Hardt, Benjamin Recht, and Oriol Vinyals. Understanding deep learning requires rethinking generalization. In International Conference on Learning Representations, 2016. (Cit. on p. 4)

Da-Wei Zhou, Qi-Wei Wang, Zhi-Hong Qi, Han-Jia Ye, De-Chuan Zhan, and Ziwei Liu. Deep class-incremental learning: A survey, 2023. (Cit. on p. 2, 9, 15)

## A Appendix

## A.1 Related Work

Machine learning systems have become increasingly integrated into our daily lives, reaching critical applications from medical diagnostics (Kononenko, 2001) to autonomous driving (Kiran et al., 2021). Consequently, the development of machine learning models that can adapt to dynamic environments and data distributions has become a pressing concern. A myriad of strategies for continual learning, also referred to as lifelong or incremental learning, have been proposed in recent years (Ke et al., 2022; Guo et al., 2022; Aljundi et al., 2019; Chaudhry et al., 2018; Ermis et al., 2022; Rebuffi et al., 2016; Rolnick et al., 2018; Buzzega et al., 2020b;a). In what follows, we describe some of the approaches most connected to our work. For a more extensive survey we refer to (De Lange et al., 2021; Hadsell et al., 2020).

Two popular continual learning scenarios are task-incremental and class-incremental learning (Sodhani et al., 2022). In task-incremental learning, the model observes a sequence of task with known task identities. These task identities have disjoint label spaces and are provided both in training and testing. This is not the case for the class-incremental setting, where task identities must be inferred by the model to make predictions. Therefore, class-incremental learning is a considerably more challenging setting (Masana et al., 2022). Continual learning methods typically fit into one of three categories: regularization-based, memory-based (also called replay methods) or architecture-based. Regularization methods (Kirkpatrick et al., 2017; Zenke et al., 2017) augment the loss in order to prevent drastic changes in model parameters, consolidating previous knowledge. Moreover, architec ture based methods (Mallya & Lazebnik, 2018) isolate or freeze a subset of the model parameters for each new observed task. In this work, we will focus on Memory-based methods, which store a small subset of the previously seen instances,(Rolnick et al., 2018; Chaudhry et al., 2018; Aljundi et al., 2019) and usually outperform their memoryless counterparts Zhou et al. (2023).

What mainly differentiates memory-based methods is the way in which the buffer is managed. In order to avoid forgetting, Experience Replay (Rolnick et al., 2018) modifies the training procedure by averaging the gradients of the current samples and the replayed samples. To manage the buffer, this method has two main variants: Reservoir sampling and Ring sampling. In Reservoir sampling (Vitter, 1985), a sample is stored with probability $B \bar { / } N$ , where $B$ is the memory budget and N the number of samples observed so far. This is particularly useful when the input stream has unknown length, and attempts to match the distribution of the memory buffer with that of the data distribution. The Ring strategy method prioritizes uniformity among classes, and performs class-wise FIFO sampling (Chaudhry et al., 2018).

To select the stored instances, iCARL Rebuffi et al. (2016) samples a set whose mean approximates the class mean in the feature space. During training, iCARL uses knowledge distillation and in inference, the nearest mean-of-exemplar classification strategy is performed. Some continual learning methods formulate it as a constrained optimization problem. For instance, (Aljundi et al., 2019) tries to find the subset of constraints that best approximate the feasible region of the original forgetting requirements. This is shown to be equivalent to a diversity strategy for sample selection. Another example is GEM Lopez-Paz & Ranzato (2017) (or its more efficient variant AGEM (Chaudhry et al., 2018)), where the constrained formulation leads to projecting gradients so that model updates do not interfere with the performance on past tasks. Lastly, X-DER (Boschini et al., 2022) is a variant of (Buzzega et al., 2020b), usually considered a strong baseline which uses both replay and regularization strategies. X-DER promotes consistency with its past by matching the model’s logits throughout the optimization trajectory. Lastly, (Peng et al., 2023) introduced the general theoretical framework of ideal continual learners, which leads to the general constrained learning formulation.

## A.2 Sensitivity of $\tilde { P } _ { t }$

Lemma 1. Under Assumption 3, we have

$$
- \tilde {\lambda} ^ {\star} \in \partial \tilde {P} _ {t} (\epsilon)\tag{2}
$$

where $\partial \tilde { P } _ { t } ( \epsilon )$ denotes the sub-differential of $\tilde { P } _ { t }$ with respect to $\epsilon ,$ and $\tilde { \lambda } ^ { \star }$ is an optimal dual variable associated to problem $( \tilde { D } _ { t } )$

Proof. We start by viewing the optimal value of problem $\tilde { P } _ { t }$ as a function of the constraint tightness (or forgetting tolerance) $\epsilon _ { k }$ associated to task k. Let $\epsilon = [ \epsilon _ { 1 } , \dots , \epsilon _ { k } , \dots , \epsilon _ { t } ]$

$$
\begin{array}{l} \tilde {P} _ {t} (\epsilon) = \min _ {\phi \in \mathcal {F}} \mathbb {E} _ {\mathfrak {D} _ {t}} [ \ell (\phi (x), y) ], \\ \quad \text {s.t.} \quad \mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\phi (x), y) ] \leq \epsilon_ {k}, \quad \forall   k \in \{1, \ldots , t - 1 \}, \end{array}\tag{\((\tilde{P}_{t})\}
$$

The Lagrangian $\mathcal { L } ( \phi , \tilde { \lambda } ; \epsilon )$ associated to this problem can be written as

$$
\mathcal {L} (\phi , \tilde {\boldsymbol {\lambda}}; \epsilon) = \mathbb {E} _ {\mathfrak {D} _ {t}} [ \ell (\phi (x), y) ] + \sum_ {k = 1} ^ {t} \tilde {\lambda} _ {k} \left(\mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\phi (x), y) ] - \epsilon_ {k}\right)
$$

where the dependence on ϵ is explicitly shown. From Assumption 3, we have that problem $\tilde { P } _ { t }$ is strongly dual (i.e: $\tilde { P } _ { t } = \operatorname* { m a x } _ { \tilde { \lambda } } \operatorname* { m i n } _ { \phi } \mathcal { L } ( \phi , \tilde { \lambda } ) )$ ). This is because it is a functional program satisfiying Slater’s constraint qualification (Rockafellar, 1997). Then, following the definition of $\tilde { P } _ { t } ( \epsilon )$ and using strong duality, we have

$$
\tilde {P} _ {t} (\epsilon) = \min _ {\phi} \mathcal {L} (\phi , \tilde {\boldsymbol {\lambda}} ^ {\star} (\epsilon); \epsilon) \leq \mathcal {L} (\phi , \tilde {\boldsymbol {\lambda}} ^ {\star} (\epsilon); \epsilon)
$$

with the inequality being true for any function $\phi \in { \mathcal { F } }$ , and where the dependence of $\tilde { \lambda } ^ { \star }$ on ϵ is also explicitly shown. Now, consider an arbitrary $\epsilon ^ { \prime } = [ \epsilon _ { 1 } , \dots , \epsilon _ { k } ^ { \prime } , \dots , \epsilon _ { t } ]$ which matches ϵ at all indices but $k ,$ and the respective primal function $\bar { \phi ^ { \star } } ( \cdot ; \epsilon ^ { \prime } )$ which minimizes its corresponding Lagrangian. Plugging $\phi ^ { \star } ( \cdot ; \epsilon ^ { \prime } )$ into the above inequality, we have

$$
\begin{array}{l} P _ {t} ^ {\star} (\epsilon) \leq \mathcal {L} (\phi^ {\star} (\cdot ; \epsilon^ {\prime}), \tilde {\lambda} ^ {\star} (\epsilon); \epsilon) \\ = \mathbb {E} _ {\mathfrak {D} _ {t}} [ \ell (\phi^ {\star} (x; \epsilon^ {\prime}), y) ] + \sum_ {k = 1} ^ {t} \tilde {\lambda} _ {k} ^ {\star} (\epsilon) (\mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\phi^ {\star} (x; \epsilon^ {\prime}), y) ] - \epsilon_ {k}) \end{array}
$$

Now, since $\phi ^ { \star } ( \cdot ; \epsilon ^ { \prime } )$ is optimal for constraint bounds given by $\epsilon ^ { \prime }$ and complementary slackness holds, we have:

$$
\mathbb {E} _ {\mathfrak {D} _ {t}} [ \ell (\phi^ {\star} (x; \epsilon^ {\prime}), y) ] = P _ {t} ^ {\star} (\epsilon^ {\prime}).
$$

Moreover, $\phi ^ { \star } ( \cdot ; \epsilon ^ { \prime } )$ is, by definition, feasible for constraint bounds given by $\epsilon { ' } .$ . In particular,

$$
\mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\phi^ {\star} (x; \epsilon^ {\prime}), y) ] \leq \epsilon_ {k} ^ {\prime}
$$

This implies that,

$$
\begin{array}{l} \mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\phi^ {\star} (x; \epsilon^ {\prime}), y) ] - \epsilon_ {k} \\ = \mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\phi^ {\star} (x; \epsilon^ {\prime}), y) ] - \epsilon_ {k} + \epsilon_ {k} ^ {\prime} - \epsilon_ {k} ^ {\prime} \\ = \alpha + (\epsilon_ {k} ^ {\prime} - \epsilon_ {k}) \quad \text { with } \alpha \leq 0 \end{array}
$$

Combining the above, we get

$$
P _ {t} ^ {\star} (\epsilon) \leq P _ {t} ^ {\star} (\epsilon^ {\prime}) + \tilde {\lambda} _ {k} ^ {\star} (\epsilon) (\epsilon^ {\prime} - \epsilon_ {k})
$$

where we used that for all $i \neq k , \epsilon _ { i } ^ { \prime } = \epsilon _ { i }$ and thus $\tilde { \lambda } _ { i } ^ { \star } ( \epsilon ) \left( \mathbb { E } _ { \mathfrak { D } _ { k } } [ \ell ( \phi ^ { \star } ( x ; \epsilon ^ { \prime } ) , y ) ] - \epsilon _ { i } \right) \le 0$ . Equivalently,

$$
P _ {t} ^ {\star} (\epsilon^ {\prime}) \geq P _ {t} ^ {\star} (\epsilon) - \tilde {\lambda} _ {k} ^ {\star} (\epsilon) (\epsilon_ {k} ^ {\prime} - \epsilon_ {k}),
$$

which matches the definition of the sub-differential, completing the proof. This result stems from a sensitivity analysis on the constraint of problem $( P _ { t } )$ and more general versions of it are well-known in the convex optimization literature (see $\mathrm { e . g . }$ Bonnans & Shapiro (1998)).

## A.3 Distance between dual functions $g ( \lambda )$ and $\tilde { g } ( \lambda )$

Lemma 2. The point-wise distance between the dualfunctions $g ( \lambda ) = \operatorname* { m i n } _ { \theta \in \theta } { \mathcal { L } } ( \theta , \lambda )$ and $\tilde { g } ( \lambda ) =$ mi $\Omega _ { \phi \in { \mathcal { F } } } { \mathcal { L } } ( \phi , \lambda )$ is bounded asfollows:

$$
0 \leq g (\boldsymbol {\lambda}) - \tilde {g} (\boldsymbol {\lambda}) \leq M \nu (1 + \| \boldsymbol {\lambda} \| _ {1}) \quad \forall \quad \lambda \succeq 0\tag{3}
$$

Proof. To alleviate the notation, we denote the statistical risks by $L _ { k } ( \phi ) : = \mathbb { E } _ { \mathfrak { D } _ { k } } [ \ell ( \phi ( x ) , y ) ]$ and the functional $L ( \phi ) : = [ L _ { 1 } ( \phi ) , \ldots , L _ { t - 1 } ( \phi ) ]$ collects the risks associated to past tasks. The Lagrangian can thus be written as:

$$
\mathcal {L} (\phi , \boldsymbol {\lambda}) = L _ {0} (\phi) + \boldsymbol {\lambda} ^ {T} L (\phi).
$$

Recall that $\begin{array} { r } { \phi ( \pmb { \lambda } ) = \arg \operatorname* { m i n } _ { \phi } \mathcal { L } ( \phi , \pmb { \lambda } ) } \end{array}$ denotes the Lagrangian minimizer associated to the multiplier λ.

By the near-universality assumption $2 , \exists \tilde { \theta } \in \Theta$ such that $\| \phi ( \lambda ) - f _ { \widetilde { \theta } } \| _ { L ^ { 2 } } \leq \nu .$ . Note that,

$$
\begin{array}{l} \mathcal {L} (f _ {\tilde {\theta}}, \boldsymbol {\lambda}) - \mathcal {L} (\phi (\boldsymbol {\lambda}), \boldsymbol {\lambda}) = L _ {0} (f _ {\tilde {\theta}}) - L _ {0} (\phi (\boldsymbol {\lambda})) + \boldsymbol {\lambda} ^ {T} \left(L (f _ {\tilde {\theta}}) - L (\phi (\boldsymbol {\lambda}))\right) \\ \qquad \qquad \qquad \leq \| L _ {0} (f _ {\tilde {\theta}}) - L _ {0} (\phi (\boldsymbol {\lambda})) \| _ {2} + \sum_ {i = 1} ^ {m} [ \boldsymbol {\lambda} ] _ {i} \| L (f _ {\tilde {\theta}}) - L (\phi (\boldsymbol {\lambda})) \| _ {2} \end{array}
$$

where we used the triangle inequality twice. Then, using the $M { - } \mathbf { I }$ Lipschitz continuity of the losses and the fact that $\lVert \phi ( \lambda ) - f _ { \tilde { \theta } } \rVert _ { 2 } \stackrel { \cdot } { \le } \nu ,$ we obtain:

$$
\begin{array}{l} \mathcal {L} (f _ {\tilde {\theta}}, \lambda) - \mathcal {L} (\phi (\boldsymbol {\lambda}), \boldsymbol {\lambda}) \leq M \| f _ {\tilde {\theta}} - \phi (\boldsymbol {\lambda}) \| _ {L _ {2}} + M \sum_ {i = 1} ^ {m} [ \lambda ] _ {i} \| f _ {\tilde {\theta}} - \phi (\lambda) \| _ {L _ {2}} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \leq M \nu + M \nu \sum_ {i = 1} ^ {m} [ \lambda ] _ {i} = M \nu (1 + \| \boldsymbol {\lambda} \| _ {1}) \end{array}
$$

Since $f _ { \theta } ( \lambda ) \in { \mathcal { F } } _ { \theta } ^ { \star } ( \lambda )$ is a Lagrangian minimizer, we know that $L ( f _ { \theta } ( \lambda ) , \lambda ) \leq L ( f _ { \widetilde { \theta } } , \lambda )$ . Thus,

$$
0 \leq \mathcal {L} (f _ {\theta} (\boldsymbol {\lambda}), \boldsymbol {\lambda}) - \mathcal {L} (\phi (\boldsymbol {\lambda}), \boldsymbol {\lambda}) \leq \mathcal {L} (f _ {\tilde {\theta}}, \lambda) - \mathcal {L} (\phi (\boldsymbol {\lambda}), \boldsymbol {\lambda})
$$

where the non-negativity comes from the fact that ${ \mathcal { F } } _ { \Theta } \subseteq { \mathcal { F } }$ . This implies:

$$
0 \leq g (\boldsymbol {\lambda}) - \tilde {g} (\boldsymbol {\lambda}) \leq M \nu (\| \boldsymbol {\lambda} \| _ {1} + 1) \quad \forall \quad \boldsymbol {\lambda} \succeq 0
$$

which conludes the proof.

## A.4 Distance between dual iterates $\tilde { \lambda } ^ { \star }$ and $\lambda ^ { \star }$

The sensitivity result in Lemma 1 holds for the optimal statistical dual variables $\tilde { \lambda } ^ { \star }$ of problem $( P _ { t } )$ However, in practice, we access the empirical parameterized dual variables $\boldsymbol { \lambda ^ { \star } }$ of problem $( D _ { t } )$ . In this section, we characterize the distance between these two quantities, showing that, under mild assumptions, $\lambda ^ { \star } \in \arg \operatorname* { m a x } \hat { g } ( \lambda )$ is not far from $\tilde { \lambda } ^ { \star } \in \arg \operatorname* { m a x } \tilde { g } ( \tilde { \lambda } )$ . This result depends on the curvature $\mu$ of the dual function $\begin{array} { r } { \tilde { g } ( \tilde { \lambda } ) = \operatorname* { m i n } _ { \phi \in \mathcal { F } } \mathcal { L } ( \phi , \tilde { \lambda } ) } \end{array}$ of Problem $( \tilde { P } _ { t } )$ , whose characterization can be found in Appendix $_ { \mathrm { A . 6 . } }$

Proposition 2. Let $\boldsymbol { B } _ { \lambda }$ denote the segment connecting $\tilde { \lambda } ^ { \star }$ and $\boldsymbol { \lambda ^ { \star } }$ and let $\mu$ denote the strong concavity constant $o f \tilde { g } ( \lambda )$ in $B _ { \lambda }$ . Under Assumptions 2 and 3, with probability at least $1 - t \delta _ { \mathrm { { i } } }$ , we have:

$$
\left\| \boldsymbol {\lambda} ^ {\star} - \tilde {\boldsymbol {\lambda}} ^ {\star} \right\| _ {2} ^ {2} \leq \frac {2}{\mu} \left[ M \nu (1 + \left\| \boldsymbol {\lambda} ^ {\star} \right\| _ {1}) + 6 \zeta (\tilde {n}, \delta) (1 + \Delta) \right],
$$

where $\begin{array} { r } { \Delta = \operatorname* { m a x } \{ \| \tilde { \mathbf { \lambda } } ^ { \star } \| _ { 1 } , \| \mathbf { \lambda } ^ { \star } \| _ { 1 } \} , \tilde { n } = \operatorname* { m i n } _ { i = 1 , \ldots , t } n _ { i } } \end{array}$ and the sample complexityfunction $\zeta \left( \tilde { n } , \delta \right) =$ $\mathcal { O } \left( R M \sqrt { d \log { \left( \tilde { n } \right) } \log ( d / \delta ) } / \sqrt { \tilde { n } } \right)$ approaches zero as n˜ grows.

Proof. We recall the definition of the dual function $g ( \lambda ) = \operatorname* { m i n } _ { \theta \in \Theta } \mathcal { L } ( \theta , \lambda )$ and its statistical unparametrized version $\begin{array} { r } { \tilde { g } ( \tilde { \lambda } ) = \operatorname* { m i n } _ { \phi \in \mathcal { F } } \mathcal { L } ( \phi , \tilde { \lambda } ) } \end{array}$ . We denote by $\hat { g } ( \lambda )$ the parametrized empirical dual function: min $\hat { \mathcal { L } } ( \boldsymbol { \theta } , \lambda ) = \hat { L } _ { 0 } ( \boldsymbol { f } _ { \boldsymbol { \theta } } ) + \lambda ^ { T } \hat { L } ( \boldsymbol { f } _ { \boldsymbol { \theta } } )$

Along with the boundedness of ${ \mathcal F } ,$ , assumption 3 guarantees uniform convergence (Shalev-Shwartz et al., 2009, Theorem 5), implying that with probability at least $1 - \delta .$ , for all $f _ { \boldsymbol { \theta } } \in \mathcal { F }$ we have:

$$
| L _ {i} (f _ {\theta}) - \hat {L} _ {i} (f _ {\theta}) | \leq \mathcal {O} \left(\frac {M R \sqrt {d \log (n _ {i}) \log (| \Theta | / \delta)}}{\sqrt {n _ {i}}}\right) := \zeta (n _ {i}, \delta)
$$

with probability at least $1 - \delta$ over a sample of size $n _ { i }$ (see Shalev-Shwartz et al. (2009)).

From the µ−strong concavity of $\tilde { g } ( \lambda )$ in $B _ { u }$ , we have that:

$$
\tilde {g} (\lambda) \leq \tilde {g} (\tilde {\boldsymbol {\lambda}} ^ {\star}) + \nabla \tilde {g} (\tilde {\boldsymbol {\lambda}} ^ {\star}) ^ {T} (\lambda - \tilde {\boldsymbol {\lambda}} ^ {\star}) - \frac {\mu}{2} \| \lambda - \tilde {\boldsymbol {\lambda}} ^ {\star} \| ^ {2} \quad \forall \lambda \in \mathcal {B} _ {u}
$$

Evaluating at $\boldsymbol { \lambda ^ { \star } }$ and using that $\nabla \tilde { g } ( \tilde { \lambda } ^ { \star } ) = L ( f ( \tilde { \lambda } ^ { \star } ) )$ ):

$$
\tilde {g} (\boldsymbol {\lambda} ^ {\star}) \leq \tilde {g} (\tilde {\boldsymbol {\lambda}} ^ {\star}) + L (f (\tilde {\boldsymbol {\lambda}} ^ {\star})) ^ {T} (\boldsymbol {\lambda} ^ {\star} - \tilde {\boldsymbol {\lambda}} ^ {\star}) - \frac {\mu}{2} \| \boldsymbol {\lambda} ^ {\star} - \tilde {\boldsymbol {\lambda}} ^ {\star} \| ^ {2}
$$

By complementary slackness, $L ( f ( \tilde { \lambda } ^ { \star } ) ) ^ { T } \tilde { \lambda } ^ { \star } = 0 .$ . Then, since $f ( \tilde { \lambda } ^ { \star } )$ is feasible and $\lambda ^ { \star } \geq 0 ;$ $L ( f ( \tilde { \lambda } ^ { \star } ) ) ^ { T } \lambda ^ { \star } \leq 0$ . Thus,

$$
\tilde {g} (\boldsymbol {\lambda} ^ {\star}) \leq \tilde {g} (\tilde {\boldsymbol {\lambda}} ^ {\star}) - \frac {\mu}{2} \| \boldsymbol {\lambda} ^ {\star} - \tilde {\boldsymbol {\lambda}} ^ {\star} \| ^ {2}
$$

Then, using Proposition $^ { 2 , }$ we have that:

$$
\begin{array}{c} \frac {\mu}{2} \| \boldsymbol {\lambda} ^ {\star} - \tilde {\boldsymbol {\lambda}} ^ {\star} \| ^ {2} \leq \tilde {g} (\tilde {\boldsymbol {\lambda}} ^ {\star}) - g (\boldsymbol {\lambda} ^ {\star}) + M \nu (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) \\ = \tilde {g} (\tilde {\boldsymbol {\lambda}} ^ {\star}) \pm g (\boldsymbol {\lambda} ^ {\dagger}) - g (\boldsymbol {\lambda} ^ {\star}) + M \nu (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) \end{array}\tag{4}
$$

where $\lambda ^ { \dagger } \in$ arg max $g ( \lambda )$ . Observe that $\tilde { g } ( \tilde { \lambda } ^ { \star } ) - g ( \lambda ^ { \dagger } ) \leq 0 \mathrm { s i n c e } \tilde { g } ( \lambda ) - g ( \lambda ) \leq 0$ ∀λ. Therefore,

$$
\frac {\mu}{2} \| \boldsymbol {\lambda} ^ {\star} - \tilde {\boldsymbol {\lambda}} ^ {\star} \| ^ {2} \leq g (\boldsymbol {\lambda} ^ {\dagger}) - g (\boldsymbol {\lambda} ^ {\star}) + M \nu (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1})
$$

Since $\boldsymbol { \lambda ^ { \star } }$ maximizes its corresponding dual function, we have that $\hat { g } ( \lambda ^ { \dagger } ) \leq \hat { g } ( \lambda ^ { \star } )$ . Then,

$$
\begin{array}{c} \frac {\mu}{2} \| \boldsymbol {\lambda} ^ {\star} - \tilde {\boldsymbol {\lambda}} ^ {\star} \| ^ {2} \leq g (\boldsymbol {\lambda} ^ {\dagger}) \pm \hat {g} (\boldsymbol {\lambda} ^ {\dagger}) - g (\boldsymbol {\lambda} ^ {\star}) + M \nu (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) \\ \leq g (\boldsymbol {\lambda} ^ {\dagger}) - \hat {g} (\boldsymbol {\lambda} ^ {\dagger}) + \hat {g} (\boldsymbol {\lambda} ^ {\star}) - g (\boldsymbol {\lambda} ^ {\star}) + M \nu (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) \end{array}\tag{5}
$$

To conclude the derivation we state the following lemma, whose proof can be found in Appendix $\mathrm { A } . 7$ Lemma 3. Under assumptions $^ { 3 , }$ any empirical dualfunction maximizer $\lambda ^ { \star } \in \arg \operatorname* { m a x } _ { \lambda \succeq 0 } \hat { g } ( \lambda )$ satisfies:

$$
\begin{array}{l} | g (\boldsymbol {\lambda} ^ {\dagger}) - \hat {g} (\boldsymbol {\lambda} ^ {\dagger}) | \leq 3 \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\dagger} \| _ {1}) \qquad a n d \\ | g (\boldsymbol {\lambda} ^ {\star}) - \hat {g} (\boldsymbol {\lambda} ^ {\star}) | \leq 3 \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) \end{array}\tag{6}
$$

Applying Lemma 3 in equation 5, we obtain:

$$
\frac {\mu}{2} \| \boldsymbol {\lambda} ^ {\star} - \tilde {\boldsymbol {\lambda}} ^ {\star} \| ^ {2} \leq 3 \zeta (\tilde {n}, \delta) (2 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1} + \| \boldsymbol {\lambda} ^ {\dagger} \| _ {1}) + M \nu (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1})\tag{7}
$$

which concludes the proof.

## A.5 Proof of Theorem 1: Information captured by dual variables

The proof of Theorem 1 stems from a straightforward instantiation of the results in Lemma 1 and Proposition 2. For completeness, we recall the statement of Theorem 1, which shows that dual variables $\boldsymbol { \lambda ^ { \star } }$ can be used as a measure of relative task difficulty.

Under Assumptions 2 and 3, with probability at least $1 - t \delta , \lambda ^ { \star }$ belongs to the ω−subdifferential of $\tilde { P } _ { t } ( \epsilon )$ at ϵ. That is:

$$
- \boldsymbol {\lambda} ^ {\star} \in \partial_ {\omega} \tilde {P} _ {t} (\epsilon)
$$

with the constant $\begin{array} { r l r } { \omega } & { { } = } & { \frac { 2 } { \mu } \left[ M \nu ( 1 + \| \pmb { \lambda } ^ { \star } \| _ { 1 } ) + 6 \zeta ( \tilde { n } , \delta ) ( 1 + \Delta ) \right] } \end{array}$ , the sensitivity parameter $\Delta = \mathrm { m a x } \{ \| \tilde { \lambda } ^ { \star } \| _ { 1 } , \| \lambda ^ { \star } \| _ { 1 } \}$ , and the sample complexity given by $\begin{array} { r } { { \tilde { n } } = \operatorname* { m i n } _ { i = 1 , \dots , T } n _ { i } ( T ) } \end{array}$

Proof. From Lemma 1 we have that $- \tilde { \lambda } ^ { \star } \in \partial \tilde { P } _ { t } ( \epsilon )$ which means that for any perturbation γ of the forgetting tolerances ϵ such that $\gamma + \epsilon \in \mathrm { d o m } ( \tilde { P } _ { t } )$

$$
\begin{array}{l} \tilde {P} _ {t} (\epsilon + \gamma) - \tilde {P} _ {t} (\epsilon) \geq \langle - \tilde {\boldsymbol {\lambda}} ^ {\star}, \gamma \rangle \\ \qquad = - \langle \tilde {\boldsymbol {\lambda}} ^ {\star} \pm \boldsymbol {\lambda} ^ {\star}, \gamma \rangle \\ \qquad = - \left(\langle \tilde {\boldsymbol {\lambda}} ^ {\star} - \boldsymbol {\lambda} ^ {\star}, \gamma \rangle + \langle \boldsymbol {\lambda} ^ {\star}, \gamma \rangle\right) \end{array}\tag{8}
$$

Then, from Proposition 2 we know that $\lambda ^ { \star } \in$ arg max $\hat { g } ( \lambda )$ is not far from $\tilde { \lambda } ^ { \star } \in \arg \operatorname* { m a x } \tilde { g } ( \tilde { \lambda } )$ Specifically, with probability at least $1 - t \delta$ , we have:

$$
\left\| \boldsymbol {\lambda} ^ {\star} - \tilde {\boldsymbol {\lambda}} ^ {\star} \right\| _ {2} ^ {2} \leq \frac {2}{\mu} \left[ M \nu (1 + \left\| \boldsymbol {\lambda} ^ {\star} \right\| _ {1}) + 6 \zeta (\tilde {n}, \delta) (1 + \Delta) \right],\tag{9}
$$

where $\begin{array} { r } { \Delta = \operatorname* { m a x } \{ \| \tilde { \mathbf { \lambda } } ^ { \star } \| _ { 1 } , \| \mathbf { \lambda } ^ { \star } \| _ { 1 } \} , \tilde { n } = \operatorname* { m i n } _ { i = 1 , \dots , t } n _ { i } } \end{array}$ and the sample complexity function $\zeta \left( \tilde { n } , \delta \right) =$ $\mathcal { O } \left( R M \sqrt { d \log { \left( \tilde { n } \right) } \log ( d / \delta ) } / \sqrt { \tilde { n } } \right)$

Let $\begin{array} { r } { \omega ^ { 2 } = \gamma _ { \mu } ^ { 2 } \left[ M \nu ( 1 + \| \lambda ^ { \star } \| _ { 1 } ) + 6 \zeta ( \tilde { n } , \delta ) ( 1 + \Delta ) \right] } \end{array}$ .Plugging in equation 9 in 8 and using Cauchy-Schwarz we obtain

$$
\begin{array}{c} \tilde {P} _ {t} (\epsilon + \gamma) - \tilde {P} _ {t} (\epsilon) \geq \langle \boldsymbol {\lambda} ^ {\star} - \tilde {\boldsymbol {\lambda}} ^ {\star}, \gamma \rangle - \langle \boldsymbol {\lambda} ^ {\star}, \gamma \rangle \\ \geq - \omega | \gamma | - \langle \boldsymbol {\lambda} ^ {\star}, \gamma \rangle \end{array}\tag{10}
$$

with probability at least $1 - t \delta$ , which completes the proof.

## A.6 Curvature $\mu$ of the dual function $\tilde { g } ( \tilde { \lambda } )$

Since the dual function g˜ is the minimum of a family of affine functions on $\tilde { \lambda } ,$ it is concave, irrespective of the non-convexity of problem $\tilde { P } _ { t }$ . In constrained learning, it is standard to use weight decay (i.e, L2 regularization) in the dual domain (see $\mathrm { e . g . }$ (Hounie et al., 2024)). In this case, the dual objective min $\begin{array} { r } { \mathsf { \ i } _ { \phi } \mathsf { \bar { L } } ( \phi ) + \lambda ^ { T } L ( \phi ) - \frac { \kappa } { 2 } \| \pmb { \lambda } \| _ { 2 } ^ { 2 } } \end{array}$ becomes strongly concave, with a strong concavity constant equal to the L2 regularization parameter $\kappa ,$ , which is typically in the order of 1.0.

If no regularization is done in the dual domain, additional assumptions are needed to guarantee the strong concavity of the dual function. For instance, it is sufficient for the loss to be $\mu _ { 0 } \cdot$ −strongly convex and $\beta -$ smooth and the Linear Independence Constraint Qualification (LICQ) to hold. LICQ is standard in constrained optimization and means full-rankness of the constraint Jacobian $D _ { \phi } L ( \phi ( \tilde { \lambda } ^ { \star } ) )$ at the optimum, i.e: $\exists \sigma > 0$ such that $\begin{array} { r } { \operatorname* { i n f } _ { \| \pmb { \lambda } \| = 1 } \| \pmb { \lambda } ^ { T } D _ { f } \pmb { L } ( \tilde { \pmb { \lambda } } ^ { \star } ) ) \| _ { 2 } \geq \sigma } \end{array}$

Under these conditions, the dual function $\tilde { g }$ is µ−strongly concave with constant

$$
\mu = \frac {\mu_ {0} \sigma^ {2}}{\beta^ {2} (1 + \Delta) ^ {2}}\tag{11}
$$

where $\Delta = \mathrm { m a x } \{ \| \tilde { \lambda } ^ { \star } \| _ { 1 } , \| \lambda ^ { \star } \| _ { 1 } \}$

Proof. For completeness we recall two basic definitions of functional analysis used in the proof. Definition 1. We say that a functional $L _ { i } : \mathcal { F }  \mathbb { R }$ is Fréchet differentiable at $\phi ^ { 0 } \in { \mathcal { F } }$ if there exists an operator $D _ { \phi } L _ { i } ( \dot { \phi ^ { 0 } } ) \in \mathfrak { B } ( \mathcal { F } , \mathbb { R } )$ such that:

$$
\lim _ {h \to 0} \frac {\left| L _ {i} (\phi^ {0} + h) - L _ {i} (\phi^ {0}) - \langle D _ {\phi} L _ {i} (\phi^ {0}) , h \rangle \right|}{\| h \| _ {L _ {2}}} = 0
$$

where ${ \mathfrak { B } } ( { \mathcal { F } } , \mathbb { R } )$ denotes the space of bounded linear operators from $\mathcal { F }$ to R.

The space ${ \mathfrak { B } } ( { \mathcal { F } } , \mathbb { R } )$ , algebraic dual of ${ \mathcal { F } } ,$ , is equipped with the corresponding dual norm:

$$
\| B \| _ {L _ {2}} = \sup \left\{\frac {| \langle B , \phi \rangle |}{\| \phi \| _ {L _ {2}}}: \phi \in \mathcal {F}, \| \phi \| _ {L _ {2}} \neq 0 \right\}
$$

which coincides with the L −norm through Riesz’s Representation Theorem: there exists a unique $g \in { \mathcal { F } }$ such that $B ( \phi ) = \langle \phi , g \rangle$ for all $\phi$ and $\| B \| _ { L _ { 2 } } = \| g \| _ { L _ { 2 } }$

The unparametrized Lagrangian $\mathcal { L }$ has a unique minimizer $\phi ( { \tilde { \lambda } } )$ for each $\tilde { \lambda } \in \mathbb { R } _ { + } ^ { m }$ . Let $\tilde { \lambda } _ { 1 } , \tilde { \lambda } _ { 2 } \in B _ { \lambda }$ and $\phi _ { 1 } = \phi ( \tilde { \lambda } _ { 1 } ) , \phi _ { 2 } = \phi ( \tilde { \lambda } _ { 2 } )$

By convexity of the functions $L _ { i } : \mathcal { F } $ R for $i = 1 , \ldots , m$ , we have:

$$
\begin{array}{l} L _ {i} (\phi_ {2}) \geq L _ {i} (\phi_ {1}) + \langle D _ {\phi} L _ {i} (\phi_ {1}), \phi_ {2} - \phi_ {1} \rangle , \\ L _ {i} (\phi_ {1}) \geq L _ {i} (\phi_ {2}) + \langle D _ {\phi} L _ {i} (\phi_ {2}), \phi_ {1} - \phi_ {2} \rangle \end{array}
$$

Multiplying the above inequalities by $[ \tilde { \lambda } _ { 1 } ] _ { i } \geq 0$ and $[ \tilde { \lambda } _ { 2 } ] _ { i } \geq 0$ respectively and adding them, we obtain:

$$
- \langle L (\phi_ {2}) - L (\phi_ {1}), \tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1} \rangle \geq \langle \tilde {\boldsymbol {\lambda}} _ {1} ^ {T} D _ {\phi} L (\phi_ {1}) - \tilde {\boldsymbol {\lambda}} _ {2} ^ {T} D _ {\phi} L (\phi_ {2}), \phi_ {2} - \phi_ {1} \rangle\tag{12}
$$

Since $\nabla \tilde { g } ( \tilde { \lambda } ) = L ( \phi ( \tilde { \lambda } ) )$ , we have that:

$$
- \langle \nabla \tilde {g} (\tilde {\boldsymbol {\lambda}} _ {2}) - \nabla \tilde {g} (\tilde {\boldsymbol {\lambda}} _ {2}), \tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1} \rangle \geq \langle \tilde {\boldsymbol {\lambda}} _ {1} ^ {T} D _ {\phi} L (\phi_ {1}) - \tilde {\boldsymbol {\lambda}} _ {2} ^ {T} D _ {\phi} L (\phi_ {2}), \phi_ {2} - \phi_ {1} \rangle\tag{13}
$$

Moreover, first order optimality conditions yield:

$$
\begin{array}{l} D _ {\phi} L _ {0} (\phi_ {1}) + \lambda_ {1} ^ {T} D _ {\phi} L (\phi_ {1}) = 0, \\ D _ {\phi} L _ {0} (\phi_ {2}) + \lambda_ {2} ^ {T} D _ {\phi} L (\phi_ {2}) = 0 \end{array}\tag{14}
$$

where $0$ denotes the null-opereator from $\mathcal { F }$ to R (see e.g: (Kurdila & Zabarankin, 2006) Theorem 5.3.1).

Combining equations 13 and 14 we obtain:

$$
\begin{array}{c} - \langle \nabla \tilde {g} (\tilde {\boldsymbol {\lambda}} _ {2}) - \nabla \tilde {g} (\tilde {\boldsymbol {\lambda}} _ {2}), \tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1} \rangle \geq \langle D _ {\phi} L _ {0} (\phi_ {2}) - D _ {\phi} L _ {0} (\phi_ {1}), \phi_ {2} - \phi_ {1} \rangle \\ \geq \mu_ {0} \| \phi_ {2} - \phi_ {1} \| _ {L _ {2}} ^ {2} \end{array}\tag{15}
$$

where we used the µ<sub>0</sub>−strong convexity of the operator $L _ { 0 }$

We will now obtain a lower bound on $\left\| \phi _ { 2 } - \phi _ { 1 } \right\| _ { L _ { 2 } }$ , starting from the β−smoothness of $L _ { 0 }$ :

$$
\begin{array}{r l} & {\| \phi_ {2} - \phi_ {1} \| _ {2} \geq \frac {1}{\beta} \| D _ {\phi} L _ {0} (\phi_ {2}) - D _ {\phi} L _ {0} (\phi_ {1}) \| _ {L _ {2}}} \\ & {\quad = \frac {1}{\beta} \| \lambda_ {2} ^ {T} D _ {\phi} \ell (\phi_ {2}) - \lambda_ {1} ^ {T} D _ {\phi} L (\phi_ {1}) \| _ {L _ {2}}} \\ & {\quad = \frac {1}{\beta} \| (\tilde {\pmb {\lambda}} _ {2} - \tilde {\pmb {\lambda}} _ {1}) ^ {T} D _ {\phi} \ell (\phi_ {2}) - \tilde {\pmb {\lambda}} _ {1} ^ {T} (D _ {\phi} L (\phi_ {1}) - D _ {\phi} L (\phi_ {2})) \| _ {L _ {2}}} \end{array}\tag{16}
$$

Then, second term in the previous equality can be characterized using the LICQ assumption

$$
\left\| \left(\tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1}\right) ^ {T} D _ {\phi} L \left(\phi_ {2}\right) \right\| _ {L _ {2}} \geq \sigma \| \tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1} \| _ {2}\tag{17}
$$

For the second term, using the β−smoothness of $L _ { i }$ we can derive:

$$
\begin{array}{l} \| \tilde {\boldsymbol {\lambda}} _ {1} ^ {T} (D _ {\phi} L (\phi_ {1}) - D _ {\phi} L (\phi_ {2})) \| _ {L _ {2}} = \| \sum_ {i = 1} ^ {m} [ \tilde {\boldsymbol {\lambda}} _ {1} ] _ {i} (D _ {\phi} L _ {i} (\phi_ {1}) - D _ {\phi} L _ {i} (\phi_ {2})) \| _ {L _ {2}} \\ \qquad \leq \sum_ {i = 1} ^ {m} [ \tilde {\boldsymbol {\lambda}} _ {1} ] _ {i} \| D _ {\phi} L _ {i} (\phi_ {1}) - D _ {\phi} L _ {i} (\phi_ {2}) \| _ {L _ {2}} \\ \qquad \leq \sum_ {i = 1} ^ {m} [ \tilde {\boldsymbol {\lambda}} _ {1} ] _ {i} \beta \| \phi_ {1} - \phi_ {2} \| _ {L _ {2}} \\ \qquad = \beta \| \tilde {\boldsymbol {\lambda}} _ {1} \| _ {1} \| \phi_ {1} - \phi_ {2} \| _ {L _ {2}} \end{array}\tag{18}
$$

Then, using the reverse triangle inequality:

$$
\begin{array}{l} \| (\tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1}) ^ {T} D _ {\phi} L (\phi_ {2}) - \tilde {\boldsymbol {\lambda}} _ {1} ^ {T} (D _ {\phi} L (\phi_ {1}) - D _ {\phi} L (\phi_ {2})) \| _ {L _ {2}} \\ \qquad \qquad \qquad \geq \| (\tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1}) ^ {T} D _ {\phi} L (\phi_ {2}) \| _ {L _ {2}} - \| \lambda_ {1} ^ {T} (D _ {\phi} \ell (\phi_ {1}) - D _ {\phi} L (\phi_ {2})) \| _ {L _ {2}} \\ \qquad \qquad \qquad \geq \sigma \| \tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1} \| _ {2} - \beta \| \tilde {\boldsymbol {\lambda}} _ {1} \| _ {1} \| \phi_ {2} - \phi_ {1} \| _ {L _ {2}} \end{array}\tag{19}
$$

Combining this with equation 16 we obtain:

$$
\begin{array}{l} \| \phi_ {2} - \phi_ {1} \| _ {2} \geq \frac {1}{\beta} \left(\sigma \| \tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1} \| _ {2} - \beta \| \tilde {\boldsymbol {\lambda}} _ {1} \| _ {1} \| \phi_ {2} - \phi_ {1} \| _ {L _ {2}}\right) \\ \longrightarrow \| \phi_ {2} - \phi_ {1} \| _ {L _ {2}} \geq \frac {\sigma}{\beta (1 + \| \tilde {\boldsymbol {\lambda}} _ {1} \| _ {1})} \| \tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1} \| _ {2} \end{array}\tag{20}
$$

This means that we can write equation $1 5$ as:

$$
- \langle \nabla \tilde {g} (\tilde {\boldsymbol {\lambda}} _ {2}) - \nabla \tilde {g} (\tilde {\boldsymbol {\lambda}} _ {1}), \tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1} \rangle \geq \frac {\mu_ {0} \sigma^ {2}}{\beta^ {2} (1 + \| \tilde {\boldsymbol {\lambda}} _ {1} \| _ {1}) ^ {2}} \| \tilde {\boldsymbol {\lambda}} _ {2} - \tilde {\boldsymbol {\lambda}} _ {1} \| _ {2} ^ {2}
$$

Letting $\tilde { \lambda } _ { 2 } = \tilde { \lambda } ^ { \star }$ , we obtain that the strong concavity constant of $\tilde { g }$ in $\boldsymbol { B } _ { \lambda }$ is $\mu ~ =$ 2 $\begin{array} { r l } & { \frac { \mu _ { 0 } \ \sigma ^ { - } } { \beta ^ { 2 } ( 1 + \operatorname* { m a x } \{ \| \tilde { \mathbf { \lambda } } ^ { \star } \| _ { 1 } , \| \mathbf { \lambda } \^ { \star } \| _ { 1 } \} ) ^ { 2 } } } \\ & { 2 0 2 0 ) . } \end{array}$ . A similar proof in the finite dimensional case can be found in (Guigues,

## A.7 Proof of Lemma 3

Let $\lambda ^ { \star } \in \arg \operatorname* { m a x } _ { \lambda \succ 0 } \hat { g } ( \lambda )$ be an empirical dual function maximizer. We want to show that:

$$
\begin{array}{l} | g (\boldsymbol {\lambda} ^ {\star}) - \hat {g} (\boldsymbol {\lambda} ^ {\star}) | \leq 3 \zeta (N, \delta) (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) \quad \text { and } \\ | g (\boldsymbol {\lambda} ^ {\dagger}) - \hat {g} (\boldsymbol {\lambda} ^ {\dagger}) | \leq 3 \zeta (N, \delta) (1 + \| \boldsymbol {\lambda} ^ {\dagger} \| _ {1}) \end{array}\tag{21}
$$

Along with the boundedness of ${ \mathcal F } ,$ , assumption 3 guarantees uniform convergence (Shalev-Shwartz et al., 2009, Theorem 5), implying that with probability at least $1 - \delta .$ , for all ${ \dot { f } } _ { \theta } \in { \mathcal { F } }$ we have:

$$
| L _ {i} (f _ {\theta}) - \hat {L} _ {i} (f _ {\theta}) | \leq \mathcal {O} \left(\frac {M R \sqrt {d \log (n _ {i}) \log (| \Theta | / \delta)}}{\sqrt {n _ {i}}}\right) := \zeta (n _ {i}, \delta)
$$

with probability at least $1 - \delta$ over a sample of size $n _ { i }$ (see Shalev-Shwartz et al. (2009)). Combining this with Holder’s inequality, we obtain:

$$
| \langle \boldsymbol {\lambda}, L (f _ {\theta}) - \hat {L} (f _ {\theta}) \rangle | \leq \| \boldsymbol {\lambda} \| _ {1} \| L (f _ {\theta}) - \hat {L} (f _ {\theta}) \| _ {\infty} \leq \| \boldsymbol {\lambda} \| _ {1} \zeta (\tilde {n}, \delta)\tag{22}
$$

with probability at least $1 - t \delta$ , where $\begin{array} { r } { \tilde { n } = \operatorname* { m i n } _ { i = 1 , \cdots , t } n _ { i } . } \end{array}$

For conciseness, we will denote ${ \hat { f } } _ { \theta } \in \arg \operatorname* { m i n } _ { \theta } { \hat { \mathcal { L } } } ( f , \lambda )$ an empirical Lagrangian minimizer associated to the multiplier λ and by f ∈ arg min L(f, λ) a statistical Lagrangian minimizer associated to λ. Evaluating 22 at $( f _ { \theta } ( \lambda ^ { \star } ) , \lambda ^ { \star } )$ and $( \hat { f } _ { \theta } ( \lambda ^ { \star } ) , \lambda ^ { \star } )$ we obtain:

$$
\begin{array}{l} - \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) \leq \mathcal {L} (f _ {\theta} (\boldsymbol {\lambda} ^ {\star}), \boldsymbol {\lambda} ^ {\star}) - \hat {\mathcal {L}} (f _ {\theta} (\boldsymbol {\lambda} ^ {\star}), \boldsymbol {\lambda} ^ {\star}) \leq \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) \\ - \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) \leq \mathcal {L} (\hat {f} _ {\theta} (\boldsymbol {\lambda} ^ {\star}), \boldsymbol {\lambda} ^ {\star}) - \hat {\mathcal {L}} (\hat {f} _ {\theta} (\boldsymbol {\lambda} ^ {\star}), \boldsymbol {\lambda} ^ {\star}) \leq \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) \end{array}\tag{23}
$$

Re-arranging and summing the previous inequalities yields:

$$
\begin{array}{l} - 2 \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) + \hat {\mathcal {L}} (f _ {\theta} (\boldsymbol {\lambda} ^ {\star}), \boldsymbol {\lambda} ^ {\star}) - \mathcal {L} (\hat {f} _ {\theta} (\boldsymbol {\lambda} ^ {\star}), \boldsymbol {\lambda} ^ {\star}) \leq g (\boldsymbol {\lambda} ^ {\star}) - \hat {g} (\boldsymbol {\lambda} ^ {\star}) \\ 2 \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) + \hat {\mathcal {L}} (f _ {\theta} (\boldsymbol {\lambda} ^ {\star}), \boldsymbol {\lambda} ^ {\star}) - \mathcal {L} (\hat {f} _ {\theta} (\boldsymbol {\lambda} ^ {\star}), \boldsymbol {\lambda^ {\star}}) \geq g (\boldsymbol {\lambda^ {\star}}) - \hat {g} (\boldsymbol {\lambda^ {\star}}) \end{array}\tag{24}
$$

Using that $f _ { \theta } ( \lambda ^ { \star } )$ and $\hat { f } _ { \theta } ( \lambda ^ { \star } )$ minimize the statistical and empirical Lagrangians respectively, we can write: $\hat { \mathcal { L } } ( f _ { \theta } ( \lambda ^ { \star } ) , \lambda ^ { \star } ) \ge \hat { \mathcal { L } } ( \hat { f } _ { \theta } ( \lambda ^ { \star } ) , \lambda ^ { \star } )$ and $\mathcal { L } ( \hat { f } _ { \theta } ( \lambda ^ { \star } ) , \lambda ^ { \star } ) \geq \mathcal { L } ( f _ { \theta } ( \lambda ^ { \star } ) , \lambda ^ { \star } )$ . Which implies:

$$
- 2 \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) + \hat {\mathcal {L}} (\hat {f} _ {\theta} (\boldsymbol {\lambda} ^ {\star}), \boldsymbol {\lambda} ^ {\star}) - \mathcal {L} (\hat {f} _ {\theta} (\boldsymbol {\lambda} ^ {\star}), \boldsymbol {\lambda} ^ {\star}) \leq g (\boldsymbol {\lambda} ^ {\star}) - \hat {g} (\boldsymbol {\lambda} ^ {\star})\tag{25}
$$

$$
2 \zeta (\tilde {n}, \delta) (1 + \| \pmb {\lambda} ^ {\star} \| _ {1}) + \hat {\mathcal {L}} (f _ {\theta} (\pmb {\lambda} ^ {\star}), \pmb {\lambda} ^ {\star}) - \mathcal {L} (f _ {\theta} (\pmb {\lambda} ^ {\star}), \pmb {\lambda} ^ {\star}) \geq g (\pmb {\lambda} ^ {\star}) - \hat {g} (\pmb {\lambda} ^ {\star})
$$

Then, using 22 we obtain:

$$
- 3 \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1}) \leq g (\boldsymbol {\lambda} ^ {\star}) - \hat {g} (\boldsymbol {\lambda} ^ {\star}) \leq 3 \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\star} \| _ {1})\tag{26}
$$

The same steps applied to $( f _ { \theta } ( \lambda ^ { \dagger } ) , \lambda ^ { \dagger } )$ and $( \hat { f } _ { \theta } ( \lambda ^ { \dagger } ) , \lambda ^ { \dagger } )$ yield:

$$
| g (\boldsymbol {\lambda} ^ {\dagger}) - \hat {g} (\boldsymbol {\lambda} ^ {\dagger}) | \leq 3 \zeta (\tilde {n}, \delta) (1 + \| \boldsymbol {\lambda} ^ {\dagger} \| _ {1})\tag{27}
$$

which concludes the proof.

## A.8 Corollary 1

Corollary 1 is an instation of Theorem 1 for a problem with a constraint per-sample, as opposed to one constraint per task. The proof folllows the same steps as in Theorem 1, accounting for the dimensionality of the associated dual variables. We refer to the proof in (Elenter et al., 2022, Theorem 3.2).

## A.9 Proof of Proposition 1

Consider the average predictor $\begin{array} { r } { \bar { f } ( x ) : = \frac { 1 } { T } \sum _ { i = 1 } ^ { T } f _ { i } ( x ) } \end{array}$ . Let $m _ { k }$ be the uncosntrained minimum associated to a given task k. Then, we can write the expected loss of $\bar { f }$ as:

$$
\mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\bar {f} (x), y) ] = \mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\bar {f} (x), y) ] \pm m _ {k}\tag{28}
$$

$$
= m _ {k} + \mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\bar {f} (x), y) ] - \mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (f _ {k} ^ {\star} (x), y) ]\tag{29}
$$

$$
\leq m _ {k} + \mathbb {E} _ {\mathfrak {D} _ {k}} [ M d (\bar {f} (x), f _ {k} ^ {\star} (x)) ]\tag{30}
$$

$$
\leq m _ {k} + \mathbb {E} _ {\mathfrak {D} _ {k}} \left[ \frac {M}{T} \sum_ {i = 1} ^ {T} d (f _ {i} (x), f _ {k} ^ {\star} (x)) \right]\tag{31}
$$

Then, using that $f _ { i } \in \mathcal { F } _ { i } ^ { \star }$ and $f _ { k } ^ { \star } \in \mathcal { F } _ { k } ^ { \star }$ , and that the Haussdorf distance between these two sets is bounded by δ, we can write:

$$
\mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (\bar {f} (x), y) ] \leq m _ {k} + \frac {T - 1}{T} M \delta\tag{32}
$$

where we used that for $i = k ,$ we can set $f _ { i } = f _ { k } ^ { \star } \in \mathcal { F } _ { k } ^ { \star }$ and thus, that term does not contribute to the loss.

## A.10 Additional Experimental Details

At iteration t, models are initialized using $f _ { t - 1 }$ , except for iteration 0, where the default PyTorch initialization for each layer (e.g, Xavier in 1D Convolutional Layers) is used. We adopt the baseline implementations of Mammoth<sup>2</sup>, and use the reported hyperparameters for the baselines. All models are trained with Adam (Kingma & Ba, 2014) and, when available, we use the tuned learning rates reported.

<table><tr><td></td><td> $\eta_p$ </td><td> $\eta_d$ </td><td></td></tr><tr><td>Tiny-ImageNet</td><td>0.01</td><td>0.05</td><td></td></tr><tr><td>SpeechCommands</td><td>0.001</td><td>0.01</td><td></td></tr><tr><td>OrganA</td><td>0.005</td><td>0.01</td><td></td></tr><tr><td>MNIST</td><td>0.01</td><td>0.1</td><td></td></tr></table>

Dual learning rates $\eta _ { d }$ are set at about an order of magnitude larger than their primal counterparts, which is standard in other constrained learning setups (Elenter et al., 2022). More complex dual learning schedules such as decaying step sizes (e.g, summable but not square summable) can be explored in future works.

In SpeechCommands, audio signals are resampled to 8 kHz. We use the PyTorch implementation of 1D convolutions with kernel sizes: 80 (and a stride of 16), 3, 3, 3. The original Speech Commands dataset has 35 categories, out of which 10 are used in the reduced version. In Tiny-Imagenet, we follow the experimental setup of Mammoth and normalize the images, use Random Cropping and Random Horizontal Flips as an augmentation pipleine. We also limit the number of tasks to 10, with 4 classes each. We do not use data augmentation in SpeechCommands, OrganA or MNIST.

The forgetting tolerances ϵ correspond to the worst average loss that one requires of a past task. In many cases, this is a design requirement, and not a tunable parameter. For large values of epsilon, constraint slacks become negative and dual variables quickly go to zero (analogous to an unconstrained problem), which makes them uniformative. On the other hand, extremely low values of ϵ might also be inadequate, since the tightness of these constraints can make the problem infeasible and make dual variables diverge (see Figure 4). The proposed method is not overly sensitive to this parameter ϵ (see Figure 4) and our experiments suggest that values close to 1.1m<sub>k</sub>, where $m _ { k }$ is the average loss observed when training the model without constraints, work well in practice. By performing a grid search we select 0.08, 0.02, 0.05 and 0.005 in Tiny ImageNet, SpeechCommands,

OrganA and MNIST respectively. The per-sample upper bound $\epsilon _ { x , y } ,$ which enforces an stricter requirement than the task level constraint, is set 10 % larger than $\epsilon _ { k } .$ The analysis of more complex heuristics, such as unsupervised pre-training or the use of slack variables to adjust $\epsilon _ { x , y }$ is a subject of future work. The minimum buffer partition parameter α is set to 0.5 (see ablation in Figure 2).

## A.11 Generalization Aware Buffer Partition

To alleviate the notation, we denote the statistical risks by $L _ { k } ( \phi ) : = \mathbb { E } _ { \mathfrak { D } _ { k } } [ \ell ( \phi ( x ) , y ) ]$ and the empirical risks by $\begin{array} { r } { } { \hat { L } _ { k } ( f ) \ : = \ \frac { 1 } { n _ { k } } \sum _ { i = 1 } ^ { n _ { k } } \ell ( f ( x _ { i } ) , y _ { i } ) } \end{array}$ Similarly, the functional $L ( \phi ) : =$ F $[ L _ { 1 } ( \phi ) , \dots , L _ { t - 1 } ( \phi ) ]$ and $\hat { L } ( f ) = [ \hat { L } _ { 1 } ( f ) , \dots , \hat { L } _ { t - 1 } ( f ) ]$ collects the risks associated to past tasks. Along with the boundedness of ${ \mathcal { F } } _ { : }$ , assumption $^ 3$ guarantees uniform convergence (Shalev-Shwartz et al., 2009, Theorem 5), implying that with probability at least $1 - \delta .$ , for all $f _ { \theta } \in { \mathcal { F } }$ we have:

$$
| L _ {i} (f _ {\theta}) - \hat {L} _ {i} (f _ {\theta}) | \leq \mathcal {O} \left(\frac {M R \sqrt {d \log (n _ {i}) \log (| \Theta | / \delta)}}{\sqrt {n _ {i}}}\right) := \zeta (n _ {i}, \delta)
$$

with probability at least $1 - \delta$ over a sample of size $n _ { i }$ (see Shalev-Shwartz et al. (2009)). Applying this bound, the generalization gap associated with the Lagrangian can be written as:

$$
\left| \sum_ {k = 1} ^ {t} \lambda_ {k} \mathbb {E} _ {\mathfrak {D} _ {k}} [ \ell (f (x), y) ] - \sum_ {k = 1} ^ {t} \frac {\lambda_ {k}}{n _ {k}} \sum_ {i = 1} ^ {n _ {k}} \ell (f (x _ {i}), y _ {i}) \right| \leq \sum_ {k = 1} ^ {t} \lambda_ {k} \zeta (n _ {k}).\tag{33}
$$

where for task t, we replace $\lambda _ { t } \gets 1$ , so as to express the Lagrangian as a single sum. Therefore, we can find the buffer partition that minimizes an upper bound on the Lagrangian generalization gap by solving the following non-linear constrained optimization problem,

$$
\begin{array}{r l} n _ {1} ^ {\star}, \ldots , n _ {t} ^ {\star} = \underset {n _ {1}, \ldots , n _ {t}} {\arg \min} & \sum_ {k = 1} ^ {t} \lambda_ {k}   \zeta (n _ {k}), \\ \text {s.t.} & \sum_ {k = 1} ^ {t} n _ {k} = | \mathcal {B} |. \\ \text {where} \zeta (n _ {k}) = O \left(\frac {R M \sqrt {d \log (n _ {k}) \log (d / \delta)}}{\sqrt {n _ {k}}}\right). \end{array}\tag{BP}
$$

Since the difficulty of a task can be assessed through its corresponding dual variable, in this problem we minimize the sum of task sample complexities, weighting each one by its corresponding dual variable and restricting the total number of samples to the memory budget.

As seen in the curvature of $\zeta$ (illustrated in Figure 7), if $n _ { \mathrm { m i n } } = 0$ problem BP has a trivial, undesirable solution. This solution is allocating all samples to the task with highest dual variable and setting all other $n _ { k }$ to 0. This is easily fixable, by imposing that buffer partitions should be greater than $n _ { \mathrm { { m i n } } } ,$ which corresponds to number of samples $n _ { k }$ where $\sqrt { \frac { \log ( n _ { k } ) } { n _ { k } } }$ starts decreasing. Since $\zeta$ describes a limiting behaviour, setting a lower bound on its input is reasonable. Removing multiplicative constants that do not change the optimal argument, the buffer partition problem can be equivalently written as:

$$
\begin{array}{l l} n _ {1} ^ {\star}, \ldots , n _ {t} ^ {\star} = \underset {n _ {1}, \ldots , n _ {t} \geq n _ {\min}} {\arg \min} & \sum_ {k = 1} ^ {t} \lambda_ {k} \sqrt {\frac {\log (n _ {k})}{n _ {k}}}, \\ \text {s.t.} & \sum_ {k = 1} ^ {t} n _ {k} = | \mathcal {B} |. \end{array}
$$

![](images/93b8225cd4d88bf111b1393c757934ada161f5d5973818d4172f15c05637a4b9.jpg)  
Figure 7: Aspect of $\zeta$ function.

(BP)

In this problem, the objective adaptively weights each sample complexity $\zeta ( n _ { k } )$ by the relative difficulty $\lambda _ { k } ^ { * }$ of task k. To solve this version of (BP), we can use Sequential Quadratic Programming (SQP) Boggs & Tolle (1995), as implemented in Kraft (1988). The main idea in SQP is to approximate the original problem by a Quadratic Programming Subproblem at each iteration, in a similar vein to quasi-Newton methods. An extensive description of this algorithm can be found in (Gill & Wong, 2011)