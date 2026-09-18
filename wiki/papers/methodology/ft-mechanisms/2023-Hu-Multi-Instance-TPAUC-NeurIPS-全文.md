---
title: "2023-Hu-Multi-Instance-TPAUC-NeurIPS"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/ft-mechanisms/2023-Hu-Multi-Instance-TPAUC-NeurIPS.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Non-Smooth Weakly-Convex Finite-sum Coupled Compositional Optimization

Quanqi Hu Department of Computer Science Texas A&M University College Station, TX 77843 quanqi-hu@tamu.edu

Dixian Zhu Department of Genetics Stanford University Stanford, CA 94305 dixian-zhu@stanford.edu

Tianbao Yang Department of Computer Science Texas A&M University College Station, TX 77843 tianbao-yang@tamu.edu

## Abstract

This paper investigates new families of compositional optimization problems, called non-smooth weakly-convex finite-sum coupled compositional optimization (NSWC FCCO). There has been a growing interest in FCCO due to its wide-ranging applications in machine learning and AI, as well as its ability to address the shortcomings of stochastic algorithms based on empirical risk minimization. However, current research on FCCO presumes that both the inner and outer functions are smooth, limiting their potential to tackle a more diverse set of problems. Our research expands on this area by examining non-smooth weakly-convex FCCO, where the outer function is weakly convex and non-decreasing, and the inner function is weakly-convex. We analyze a single-loop algorithm and establish its complexity for finding an ϵ-stationary point of the Moreau envelop of the objective function. Additionally, we also extend the algorithm to solving novel non-smooth weakly-convex tri-level finite-sum coupled compositional optimization problems, which feature a nested arrangement of three functions. Lastly, we explore the applications of our algorithms in deep learning for two-way partial AUC maximization and multi-instance two-way partial AUC maximization, using empirical studies to showcase the effectiveness of the proposed algorithms.

## 1 Introduction

In this paper, we consider two classes of non-convex compositional optimization problems. The first class is formulated as following:

$$
\min _ {\mathbf {w} \in \mathbb {R} ^ {d}} F (\mathbf {w}) := \frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {i} (\mathbb {E} _ {\xi \sim \mathcal {D} _ {i}} [ g _ {i} (\mathbf {w}; \xi) ]),\tag{1}
$$

where S denotes a finite set of n items and $\mathcal { D } _ { i }$ denotes a distribution that could depend on i. The second class is given by:

$$
\min _ {\mathbf {w} \in \mathbb {R} ^ {d}} F (\mathbf {w}) := \frac {1}{n _ {1}} \sum_ {i \in \mathcal {S} _ {1}} f _ {i} \left(\frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (\mathbb {E} _ {\xi \sim \mathcal {D} _ {i, j}} [ h _ {i, j} (\mathbf {w}; \xi) ])\right),\tag{2}
$$

where $S _ { 1 }$ denotes a finite set of $n _ { 1 }$ items and $S _ { 2 }$ denotes a finite set of $n _ { 2 }$ items and $\mathcal { D } _ { i j }$ denotes a distribution that could depend on $( i , j )$ . For simplicity of discussion, we denote by $g _ { i } ( \mathbf { w } ) =$ $\mathbb { E } _ { \xi \sim \mathcal { D } _ { i } } [ g _ { i } ( \mathbf { w } ; \xi ) ] : \mathbb { R } ^ { d }  \mathbb { R } ^ { d _ { 1 } }$ and by $h _ { i , j } ( \mathbf { w } ) = \mathbb { E } _ { \boldsymbol { \xi } \sim \mathcal { D } _ { i , j } } [ h _ { i , j } ( \mathbf { w } ; \boldsymbol { \xi } ) ] : \mathbb { R } ^ { d }  \mathbb { R } ^ { d _ { 2 } }$ . For both classes of problems, we focus our attention on non-convex $F$ with non-smooth non-convex functions $f _ { i }$ and $g _ { i }$ , which, to the best of our knowledge, has not been studied in any prior works.

The first problem (1) with smooth functions $f _ { i }$ and $g _ { i }$ has been explored in previous works [26, 15, 21, $3 3 ] ,$ which is known as finite-sum coupled compositional optimization (FCCO). It is subtly different from standard stochastic compositional optimization (SCO) [27] and conditional stochastic optimiza tion (CSO) [13]. FCCO has been successfully applied to optimizing a wide range of X-risks [33] with convergence guarantee, including smooth surrogate losses of areas under the curves [20] and ranking measures [21], listwise losses [21], and contrastive losses [36]. The second problem (2) is a novel class and is referred to as tri-level finite-sum coupled compositional optimization (TCCO). Both problems differ from traditional two-level or multi-level compositional optimization due to the coupling of variables $i , \xi$ in (1) or the coupling of variables $i , j , \xi$ in (2) at the inner most level.

One limitation of prior works about non-convex FCCO is that their convergence analysis heavily rely on the smoothness conditions of $f _ { i }$ and $g _ { i }$ [26, 15]. This raises a concern about whether existing techniques can be leveraged for solving non-smooth non-convex FCCO problems with non-asymptotic convergence guarantee. Non-smooth non-convex FCCO and TCCO problems have important applications in ML and AI, e.g., group distributionally robust optimization [4] and two-way partial AUC maximization for deep learning [44]. We defer discussions and formulations of these problems to Section 5. The difficulty for solving smooth FCCO lies at high costs of computing a stochastic gradient $\nabla g _ { i } ( \mathbf { w } ) \nabla f _ { i } ( g _ { i } ( \dot { \mathbf { w } } ) )$ for a randomly sampled i and the overall gradient $\bar { \nabla } F ( \bar { \bf w } )$ To approximate the stochastic gradient, a variance-reduced estimator of $g _ { i } ( \mathbf { w } _ { t } )$ denoted by $u _ { i , t }$ is usually maintained and updated for sampled data in the mini-batch $i \in \boldsymbol { B } _ { t }$ . As a result, the stochastic gradient can be approximated by $\nabla g _ { i } ( \mathbf { \bar { w } } _ { t } ; \xi _ { t } ) \nabla f _ { i } ( u _ { i , t } )$ , where $\xi _ { t } \sim D _ { i }$ is a random sample. The overall gradient can be estimated by averaging the stochastic gradient estimator over the mini-batch or using variance-reduction techniques. A key insight of the convergence analysis for smooth FCCO is to bound the following error using the L-smoothness of $f _ { i } .$ , which reduces to bounding the error of $u _ { i , t }$ for estimating $g _ { i } ( \mathbf { w } _ { t } )$

$$
\| \nabla g _ {i} (\mathbf {w} _ {t}; \xi_ {t}) \nabla f _ {i} (u _ {i, t}) - \nabla g _ {i} (\mathbf {w} _ {t}; \xi_ {t}) \nabla f _ {i} (g _ {i} (\mathbf {w} _ {t})) \| ^ {2} \leq \| \nabla g _ {i} (\mathbf {w} _ {t}; \xi_ {t}) \| ^ {2} L \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2}.
$$

A central question to be addressed in this paper is “Can these gradient estimators be used in stochastic optimization for solving non-smooth non-convex FCCO with provable convergence guarantee"? To address this question we focus our attention on a specific class of FCCO/TCCO called non-smooth weakly-convex (NSWC) FCCO/TCCO. This approach aligns with many established works on NSWC optimization [6–9]. Nevertheless, NSWC FCCO/TCCO is more complex than a standard weakly-convex optimization problem because an unbiased stochastic subgradient is not readily accessible. In addition, the convergence measure in terms of the gradient norm of smooth non-convex objectives is not applicable to weakly convex optimization, which will complicate the analysis involving the biased stochastic gradient estimator $\mathbf { \dot { \gamma } } \partial g _ { i } ( \mathbf { w } _ { t } ; \xi _ { t } ) \partial f _ { i } ( u _ { i } ^ { t } ) ^ { \mathbf { \gamma } 1 }$

Contributions. A major contribution of this paper is to present novel convergence analysis of singleloop stochastic algorithms for solving NSWC FCCO/TCCO problems, respectively. In particular,

• For non-smooth FCCO, we analyze the following single-loop updates:

$$
\mathbf {w} _ {t + 1} = \mathbf {w} _ {t} - \eta \frac {1}{B} \sum_ {i \in \mathcal {B} _ {t}} \partial g _ {i} (\mathbf {w} _ {t}; \xi_ {t}) \partial f _ {i} (u _ {i, t}),\tag{3}
$$

where $B _ { t }$ is a random mini-batch of B items, and $u _ { i , t }$ is an appropriate variance-reduced estimator of $g _ { i } ( \mathbf { w } _ { t } )$ that is updated only for $i \in \boldsymbol { B } _ { t }$ at the t-th iteration. To overcome the non-smoothness, we adopt the tool of Moreau envelop of the objective as in previous works [6, 7]. The key difference of our convergence analysis from previous ones for smooth FCCO is that we bound the inner product $\langle \mathbb { E } _ { i } \partial \bar { g _ { i } } ( \mathbf { w } ) \partial f _ { i } ( \bar { u _ { i , t } } ) , \widehat { \mathbf { w } } _ { t } - \mathbf { w } _ { t } \rangle$ , where $\widehat { \mathbf { w } } _ { t }$ is the solution of the proximal mapping of the objective at $\mathbf { w } _ { t }$ . To this end, specific conditions of $f _ { i } , g _ { i }$ are imposed, $\mathrm { i } . \mathrm { e } . , f _ { i }$ is weakly convex and non-decreasing and $g _ { i } ( \mathbf { w } )$ is weakly convex, under which we establish an iteration complexity of $T = \mathcal { O } ( \epsilon ^ { - 6 } )$ for finding an ϵ-stationary point of the Moreau envelope of $F ( \cdot )$

• For non-smooth TCCO, we analyze the following single-loop updates:

$$
\mathbf {w} _ {t + 1} = \mathbf {w} _ {t} - \eta \frac {1}{B _ {1}} \sum_ {i \in \mathcal {B} _ {1} ^ {t}} \left[ \frac {1}{B _ {2}} \sum_ {j \in \mathcal {B} _ {2} ^ {t}} \partial h _ {i, j} (\mathbf {w} _ {t}; \xi_ {t}) \partial g _ {i} (v _ {i, j, t}) \right] \partial f _ {i} (u _ {i, t}),\tag{4}
$$

Table 1: Comparison with prior works for solving (1) and (2). In the monotonicity column, notation ↑ means the given function is required to be non-decreasing. If not specified, the given function is only required to be monotone.

<table><tr><td>Method</td><td>Objective</td><td>Smoothness</td><td>Weak Convexity</td><td>Monotonicity</td><td>Complexity</td></tr><tr><td>SOX [26]</td><td>(1)</td><td> $f_i, g_i$ </td><td>none</td><td>none</td><td> $\mathcal{O}(\epsilon^{-4})$ </td></tr><tr><td>MSVR [15]</td><td>(1)</td><td> $f_i, g_i$ </td><td>none</td><td>none</td><td> $\mathcal{O}(\epsilon^{-3})$ </td></tr><tr><td>SONX (Ours)</td><td>(1)</td><td>none</td><td> $f_i, g_i$ </td><td> $f_i \uparrow$ </td><td> $\mathcal{O}(\epsilon^{-6})$ </td></tr><tr><td>SONT (Ours)</td><td>(2)</td><td>none</td><td> $f_i, g_i, h_{i,j}$ </td><td> $f_i \uparrow, g_i \uparrow$ </td><td> $\mathcal{O}(\epsilon^{-6})$ </td></tr><tr><td>SONT (Ours)</td><td>(2)</td><td> $h_{i,j}$ </td><td> $f_i, g_i$ </td><td> $f_i \uparrow, g_i$ </td><td> $\mathcal{O}(\epsilon^{-6})$ </td></tr></table>

where $B _ { t } ^ { 1 }$ and $B _ { t } ^ { 2 }$ are random mini-batches of $B _ { 1 }$ and $B _ { 2 }$ items, respectively, and $u _ { i , t }$ is an appropriate variance-reduced estimator of $\begin{array} { r } { \frac { 1 } { n _ { 2 } } \sum _ { j \in { \cal S } _ { 2 } } g _ { i } \big ( h _ { i j } \big ( { { \bf w } _ { t } } \big ) \big ) } \end{array}$ that is updated only for $i \in  { \boldsymbol { B } } _ { t } ^ { 1 }$ and $v _ { i , j , t }$ is an appropriate variance-reduced estimator of $h _ { i , j } ( \mathbf { w } _ { t } )$ that is updated only for $i \in$ $B _ { t } ^ { 1 } , j \in B _ { t } ^ { 2 }$ . To prove the convergence, we impose conditions of $f _ { i } , g _ { i } , h _ { i , j } , \mathbf { i . e . , } f _ { i }$ is weakly convex and non-decreasing and $g _ { i } { \bar { ( \cdot ) } }$ is weakly convex and non-decreasing (or monotonic), $h _ { i j }$ is weakly convex (or smooth), and establish an iteration complexity of $T = \mathcal { O } \left( \epsilon ^ { - 6 } \right)$ for finding an ϵ-stationary point of the Moreau envelope of $F ( \cdot )$

• We extend the above algorithms to solving (multi-instance) two-way partial AUC maximization for deep learning, and conduct extensive experiments to verify the effectiveness of the both algorithms.

## 2 Related work

Smooth SCO. There are many studies about two-level smooth SCO [27, 38, 10, 19, 3, 28] and multi-level smooth SCO [32, 32, 1, 39]. The complexities of finding an ϵ-stationary point for twolevel smooth SCO have been improved from $O ( \epsilon ^ { - 5 } )$ [27] to $O ( \epsilon ^ { - 3 } )$ [19], and that for multi-level smooth SCO have been improved from a level-dependent complexity of $O ( \epsilon ^ { - ( 7 + K ) / 2 } )$ [32] to a level-independent complexity of $O ( \epsilon ^ { - 3 } )$ [32], where K is the number of levels. The improvements mostly come from using advanced variance reduction techniques for estimating each level function or its Jacobian and for estimating the overall gradient. Two stochastic algorithms have been developed in [13] for CSO but suffer a limitation of requiring large batch sizes.

Smooth FCCO. FCCO was first introduced in [20] for optimizing average precision. Its algorithm and convergence analysis was improved in [26] and [15]. The former work [26] proposed an algorithm named SOX by using moving average (MA) to estimate the inner function values and the overall gradient. In the smooth non-convex setting, SOX is proved to achieve an iteration complexity of $\bar { \mathcal { O } } ( \epsilon ^ { - 4 } )$ . The latter work [15] proposed a novel multi-block-single-probe variance reduced (MSVR) estimator for estimating the inner function values, which helps achieve a lower iteration complexity $\mathcal { O } ( \epsilon ^ { - 3 } )$ . Recently, [11] proposed an extrapolation based estimator for the inner function, which yields a method with a complexity that matches MSVR when $n \leq \epsilon ^ { 2 / 3 }$ . These techniques have been employed for optimizing various X-risks, including contrastive losses [36], ranking measures and listwise losses [21], and other objectives [26, 15]. However, all of these prior works assume the smoothness of $f _ { i }$ and $g _ { i }$ . Hence, their analysis is not applicable to NSWC FCCO problems. Our novel analysis of a simple algorithm for NSWC FCCO problems yields an iteration complexity of $O ( \epsilon ^ { - 6 } )$ for using the MSVR estimators of the inner functions. The comparison with [26, 15] is shown in Table 1.

Non-smooth Weakly Convex Optimization. Analysis of weakly convex optimization with unbiased stochastic subgradients was pioneered by [6, 7]. Optimization of compositional functions that are weakly convex have been tackled in earlier works [8, 9], where the inner function is deterministic or does not involve coupling between two random variables. A closely related work to our NSWC FCCO is weakly-convex concave minimax optimization [22]. Assuming $f _ { i }$ is convex, (1) can be written as: min $\begin{array} { r } { \mathbf { \dot { \mathbf { \sigma } } } _ { \mathbf { w } } \operatorname* { m a x } _ { \pi \in \mathbb { R } ^ { n } } \frac { 1 } { n } \sum _ { i \in \mathcal { S } } \langle \pi _ { i } , g _ { i } ( \mathbf { w } ) \rangle - f _ { i } ^ { * } ( \pi _ { i } ) } \end{array}$ , where $f _ { i } ^ { * } ( \cdot )$ is the convex conjugate of $f _ { i }$ . It can be solved using existing methods [22, 31, 41, 43, 17] but with several limitations: (i) the algorithms in [22, 31, 41, 43] have a comparable complexity of $\bar { O } ( 1 / \epsilon ^ { 6 } )$ but have unnecessary double loops which require setting the number of iterations for the inner loop; (ii) the algorithm in [17] is single loop but has a worse complexity of $\mathcal { O } ( 1 / \epsilon ^ { 8 } )$ ; (iii) these existing algorithms and analysis does not account for complexity of updating all coordinates of $\pi ,$ which could be prohibitive in many applications; iv) these approaches are not applicable to NSWC FCCO/TCCO with weakly convex $f _ { i }$ . In fact, the double loop algorithm has been leveraged and extended to solving the two-way partial AUC maximization problem, a special case of NSWC FCCO [44], by sampling and updating a batch of coordinates of π at each iteration. However, it is less practical thus not implemented and its analysis did not explicitly show the convergence rate dependency on $n _ { + } , n _ { - }$ and the block batch size.

A special case of NSWC SCO problem was considered in [46], which is given by

$$
\min _ {x \in \mathcal {X}} f (x, g (x)), \text {   with   } f (x, u) = \mathbb {E} _ {\zeta} [ u + \varkappa \max (0, g (x; \zeta) - u) ], \quad g (x) = \mathbb {E} _ {\xi} [ g (x; \xi) ].
$$

They proposed two methods, SCS for smooth $g ( x )$ and SCS with SPIDER for non-smooth $g ( x )$ . For both proposed methods, they proved a sample complexity of $\mathcal { O } ( 1 / \epsilon ^ { 6 } )$ for achieving an ϵ-stationary point of the objective’s Moreau envelope <sup>2</sup>. We would like to remark that the above problem with a non-smooth $g ( x )$ is a special case of NSWC FCCO with only a convex outer function, one block and no coupled structure. Nevertheless, their algorithm for non-smooth $g ( \cdot )$ suffers a limitation of requiring a large batch size in the order of ${ \cal O } ( 1 / \bar { \epsilon } ^ { 2 } )$ for achieving the same convergence.

Finally, we would like to mention that non-smooth convex or strongly convex SCO problems have been considered in [27, 42, 26], which, however, are out of scope of the present work.

## 3 Preliminaries

Let ∥ · ∥ be the Euclidean norm of a vector and spectral norm of a matrix. We use $\Pi _ { C } [ \cdot ]$ to denote the Euclidean projection onto $\{ v \in \mathbb { R } ^ { m } : \| v \| \leq C \}$ . For vectors, inequality notations including $\leq , \geq , > , <$ are used to denote element-wise inequality. For an expectation function $f ( \cdot ) = \mathbb { E } _ { \xi } [ f ( \cdot ; \xi ) ]$ let $\begin{array} { r } { f ( \cdot ; B ) = { \frac { 1 } { | B | } } \sum _ { \xi \in B } f ( \cdot ; \xi ) } \end{array}$ be its stochastic unbiased estimator evaluated on a sample batch B. A stochastic unbiased estimator is said to have bounded variance $\sigma ^ { 2 } \operatorname { i f } \mathbb { E } _ { \xi } [ \| f ( \cdot ) - f ( \cdot ; \xi ) \| ^ { 2 } ] \leq \sigma ^ { 2 }$ . The Jacobian matrix of function $f : \mathbb { R } ^ { m _ { 1 } }  \mathbb { R } ^ { m _ { 2 } }$ is in dimension $\mathbb { R } ^ { m _ { 1 } \times m _ { 2 } }$ . We recall the definition of general subgradient and subdifferential following [6, 24].

Definition 3.1 (subgradient and subdifferential). Consider a function $f : \mathbb { R } ^ { n }  \mathbb { R } \cup \{ \infty \}$ and a point with $f ( x )$ finite. A vector $v \in \mathbb { R } ^ { n }$ is a general subgradient of f at x, if

$$
f (y) \geq f (x) + \langle v, y - x \rangle + o (\| y - x \|), \quad \text { as } y \rightarrow x.
$$

The subdifferentia $\partial f ( x )$ is the set of subgradients of f at point x.

For simplicity, we abuse the notation and also use $\partial f ( x )$ to denote one subgradient from the corresponding subgradient set when no confusion could be caused. We use $\partial f ( x ; B )$ to represent a stochastic unbiased estimator of the subgradient $\partial f ( x )$ that is evaluated on a sample batch B. A function is called $C ^ { 1 }$ -smooth if it is continuously differentiable. A function $f = \bar { ( } f _ { 1 } , \ldots , f _ { m _ { 2 } } )$ $\mathbb { R } ^ { m _ { 1 } } \to \mathbb { R } ^ { m _ { 2 } }$ is called monotone $\mathrm { i f } \ \forall i \in \{ 1 , \ldots , \overline { { \ } } , f _ { i } : \mathbb { R } ^ { m _ { 1 } } \ $ R is monotone with respect to each element of the input. Note that if a Lipschitz continuous function $f : O \to \mathbb { R } ^ { m _ { 2 } }$ is assumed to be non-increasing (resp. non-decreasing), where the domain $O \subset \mathbb { R } ^ { m _ { 1 } }$ <sup>1</sup> is open, then all subgradients of f are element-wise non-positive (resp. non-negative). We refer the details to Appendix D.1.

A function f is C-Lipschitz continuous if $\| f ( x ) - f ( y ) \| \leq C \| x - y \| ,$ . A differentiable function f is L-smooth if $\| \nabla f ( x ) - \nabla f ( y ) \| \leq L \| x - y \| . \mathrm { A }$ function $f : \mathbb { R } ^ { d }  \mathbb { R } \cup \{ \infty \}$ is ρ-weakly-convex if the function $f ( \cdot ) + \frac { \rho } { 2 } \| \cdot \| ^ { 2 }$ is convex. A vector-valued function $f : \mathbb { R } ^ { d }  \{ \mathbb { R } \cup \{ \infty \} \} ^ { m }$ is called ρ-weakly-convex if it is ρ-weakly-convex for each output. It is difficult sometimes impossible to find an ϵ-stationary point of a non-smooth weakly-convex function F, i.e., dist $( 0 , \partial F ( \mathbf { w } ) ) \leq \epsilon .$ For example, an ϵ-stationary point of function $f ( x ) { \dot { = } } | x |$ does not exist for $0 \leq \epsilon < 1$ unless it is the optimal solution. To tackle this issue, [6] proposed to use the stationarity of the problem’s Moreau envelope as the convergence metric, which has become a standard metric for solving weakly-convex problems [7, 22, 31, 41, 43, 17]. Given a weakly-convex function $\varphi : \mathbb { R } ^ { m }  \mathbb { R }$ , its Moreau envelope and proximal map with $\lambda > 0$ are constructed as

$$
\varphi_ {\lambda} (x) := \min _ {y} \{\varphi (y) + \frac {1}{2 \lambda} \| y - x \| ^ {2} \}, \quad \operatorname{prox} _ {\lambda \varphi} (x) := \underset {y} {\arg \min} \{\varphi (y) + \frac {1}{2 \lambda} \| y - x \| ^ {2} \}.
$$

The Moreau envelope is an implicit smoothing of the original problem. Thus it attains a continuous differentiation. As a formal statement, the following lemma follows from standard results [6, 18].

Lemma 3.2. Given a ρ-weakly-convexfunction $\varphi$ and $\lambda < \rho ^ { - 1 }$ , the envelope $\varphi _ { \lambda }$ is $C ^ { 1 }$ -smooth with gradient given by $\nabla \varphi _ { \lambda } ( x ) = \lambda ^ { - 1 } ( x - p r o x _ { \lambda \varphi } ( \dot { x } ) )$ .

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Stochastic Optimization algorithm for Non-smooth FCCO (SONX)

1: Initialization:  $w_{0}, \{u_{i,0} : i \in S\}$ .
2: for  $t = 0, \ldots, T - 1$  do
3: Draw sample batches  $B_{1}^{t} \sim S$ , and  $B_{2,i}^{t} \sim D_{i}$  for each  $i \in B_{1}^{t}$ .
4:  $u_{i,t+1} = \begin{cases}(1 - \tau)u_{i,t} + \tau g_i(\mathbf{w}_t; \mathcal{B}_{2,i}^t) + \gamma(g_i(\mathbf{w}_t; \mathcal{B}_{2,i}^t) - g_i(\mathbf{w}_{t-1}; \mathcal{B}_{2,i}^t)), &amp; i \in \mathcal{B}_1^t \\ u_{i,t}, &amp; i \notin \mathcal{B}_1^t\end{cases}$ 
5: Compute  $G_t = \frac{1}{B_1} \sum_{i \in B_1^t} \partial g_i(\mathbf{w}_t; \mathcal{B}_{2,i}^t) \partial f_i(u_{i,t})$ 
6: Update  $w_{t+1} = w_t - \eta G_t$ 
7: end for

Moreover, for any point  $x \in R^m$ , the proximal point  $\hat{x} := \text{prox}_{\lambda\varphi}(x)$  satisfies [6]
 $\| \hat{x} - x \| = \lambda \| \nabla \varphi_{\lambda}(x) \|, \quad \varphi(\hat{x}) \leq \varphi(x), \quad \text{dist}(0, \partial \varphi(\hat{x})) \leq \| \nabla \varphi_{\lambda}(x) \|$ .

Thus if  $\| \nabla \varphi_{\lambda}(x) \| \leq \epsilon$ , we can say x is close to a point  $\hat{x}$  that is  $\epsilon$ -stationary, which is called nearly  $\epsilon$ -stationary solution of  $\varphi(x)$ .
</div>

## 4 Algorithms and Convergence

## 4.1 Non-Smooth Weakly-Convex FCCO

In this section, we assume the following conditions hold for the FCCO problem (1).

Assumption 4.1. For all $i \in S .$ , we assume that

• $f _ { i }$ is $\rho _ { f }$ -weakly-convex, $C _ { f }$ -Lipschitz continuous and non-decreasing;

$g _ { i } ( \cdot )$ is $\rho _ { g }$ -weakly-convex and $g _ { i } ( \cdot ; \xi )$ is $C _ { g ^ { - \underline { { \mathbf { L } } } } }$ ipschitz continuous;

• Stochastic gradient estimators $g _ { i } ( \mathbf { w } ; \boldsymbol { \xi } )$ and $\partial g _ { i } ( \mathbf { w } ; \pmb { \xi } )$ have bounded variance $\sigma ^ { 2 }$

Proposition 4.2. Under Assumption 4.1, $F ( \mathbf { w } )$ in (1) is $\rho _ { F }$ weakly convex with $\rho _ { F } = \sqrt { d _ { 1 } } \rho _ { g } C _ { f } +$ $\rho _ { f } C _ { g } ^ { 2 } .$

One challenge in solving FCCO is the lack of access to unbiased estimation of the subgradients $\begin{array} { r } { \frac { 1 } { n } \sum _ { i \in \mathcal { S } } \partial g _ { i } \bar { ( } \mathbf { w } ) \partial f _ { i } ( g _ { i } ( \bar { \mathbf { w } } ) ) } \end{array}$ due to the expectation form of $g _ { i } ( \mathbf { w } )$ inside a non-linear function $f _ { i \cdot } \operatorname { A }$ common solution in existing works for solving smooth FCCO is to maintain function value estimators $\{ u _ { i } : i \in S \}$ for $\{ g _ { i } ( \mathbf { w } ) \mathbf { \bar { \Psi } } : i \in \mathcal { S } \}$ , and approximate the true gradient by a stochastic version $\begin{array} { r } { \frac { \bar { 1 } } { B _ { 1 } } \sum _ { i \in \mathcal { B } _ { 1 } } \partial \bar { g } _ { i } ( \mathbf { w } ; \bar { B _ { 2 } } ) \partial f _ { i } ( u _ { i } ) } \end{array}$ [26, 15], where $\textstyle B _ { 1 } , B _ { 2 }$ are sampled mini-batches. Simply using a mini-batch estimator of $g _ { i }$ inside $f _ { i }$ does not ensure convergence if mini-batch size is small.

Inspired by existing algorithms of smooth FCCO, a simple method for solving non-smooth FCCO is presented in Algorithm 1 referred to as SONX. A key step is the step 4, which uses the multiblock-single-probe variance reduced (MSVR) estimator proposed in [15] to update $\{ u _ { i } : i \in S \}$ in a block-wise manner. It is an advanced variance reduced update strategy for multi-block variable inspired by STORM [5]. In the update of MSVR estimator, for each sampled $i \in B _ { 1 } ^ { t } , u _ { i , t }$ is updated following a STORM-like rule with a specialized parameter $\begin{array} { r } { \gamma = \frac { n - B _ { 1 } } { B _ { 1 } ( 1 - \tau ) } + ( 1 - \tau ) } \end{array}$ for the error correction term. For the unsampled $i \notin B _ { 1 } ^ { t }$ , no update for $u _ { i , t }$ is needed. When $\gamma = 0$ , the estimator becomes the moving average estimator analyzed in [26] for smooth FCCO, which is also analyzed in the Appendix. With the function values of $\{ g _ { i } ( \mathbf { w } _ { t } ) : i \in \mathcal { S } \}$ well-estimated, the gradient can be approximated by $G _ { t }$ in step 5. Next, we directly update $\mathbf { w } _ { t }$ by subgradient descent using the stochastic gradient estimator $G _ { t }$ . Note that unlike existing works on smooth FCCO that often maintain a moving average estimator [26] or a STORM estimator [15] for the overall gradient to attain better rates, this is not possible in the non-smooth case as those variance reduction techniques for the overall gradient critically rely on the Lipschitz continuity of $\nabla F .$ , i.e., the smoothness of $F$

## 4.2 Non-Smooth Weakly-Convex TCCO

In this section, we consider non-smooth TCCO problem and aim to extend Algorithm 1 to solve it. First of all, for convergence analysis and to ensure the weak convexity of $F ( \mathbf { w } )$ in $( 2 )$ , we make the following assumptions.

Assumption 4.3. For all $( i , j ) \in S _ { 1 } \times S _ { 2 }$ , we assume that

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 Stochastic Optimization algorithm for Non-smooth TCCO (SONT)

1: Initialization:  $w_{0}, \{u_{i,0} : i \in S_{1}\}$ ,  $v_{i,j,0} = h_{i,j}(w_{0}; B_{3,i,j}^{0})$  for all  $(i,j) \in S_{1} \times S_{2}$ .

2: for  $t = 0, \ldots, T - 1$  do

3: Sample batches  $B_{1}^{t} \subset S_{1}$ ,  $B_{2}^{t} \subset S_{2}$ , and  $B_{3,i,j}^{t} \subset D_{i,j}$  for  $i \in B_{1}^{t}$  and  $j \in B_{2}^{t}$ .

4:  $v_{i,j,t+1} = \begin{cases} \Pi_{\tilde{C}_{h}}[(1 - \tau_{1})v_{i,j,t} + \tau_{1}h_{i,j}(w_{t}; B_{3,i,j}^{t}) + \gamma_{1}(h_{i,j}(w_{t}; B_{3,i,j}^{t}) - h_{i,j}(w_{t-1}; B_{3,i,j}^{t}))], \\ (i,j) \in B_{1}^{t} \times B_{2}^{t} \\ v_{i,j,t}, (i,j) \notin B_{1}^{t} \times B_{2}^{t} \end{cases}$ 

5:  $u_{i,t+1} = \begin{cases} (1 - \tau_{2})u_{i,t} + \frac{1}{B_{2}}\sum_{j \in B_{2}^{t}}[\tau_{2}g_{i}(v_{i,j,t}) + \gamma_{2}(g_{i}(v_{i,j,t}) - g_{i}(v_{i,j,t-1})], &amp; i \in B_{1}^{t} \\ u_{i,t}, i \notin B_{1}^{t} \end{cases}$ 

6:  $G_{t} = \frac{1}{B_{1}}\sum_{i \in B_{1}^{t}}\left[\left(\frac{1}{B_{2}}\sum_{i \in B_{2}^{t}}\nabla h_{i,j}(w_{t}; B_{3,i,j}^{t})\partial g_{i}(v_{i,j,t})\right)\partial f_{i}(u_{i,t})\right]$ 

7: Update  $w_{t+1} = w_{t} - \eta G_{t}$ 

8: end for
</div>

• $f _ { i }$ is C<sub>f</sub>-Lipschitz continuous, $\rho _ { f } .$ -weakly-convex and non-decreasing;

• $g _ { i }$ is $\rho _ { g }$ -weakly-convex and $C _ { g ^ { - 1 } }$ ipschitz continuous. $h _ { i , j } ( \cdot ; \xi )$ is $C _ { h }$ -Lipschitz continuous.

• Either $g _ { i }$ is non-decreasing, $h _ { i , j }$ is $L _ { h } .$ -weakly-convex or $g _ { i }$ is monotone, $h _ { i , j }$ is $L _ { h }$ -smooth.

• Stochastic estimators $h _ { i , j } ( \mathbf { w } , \boldsymbol { \xi } )$ and $\partial h _ { i , j } ( \mathbf { w } , \boldsymbol { \xi } )$ have bounded variance $\sigma ^ { 2 } .$ , and $\| h _ { i , j } ( \mathbf { w } ) \| \leq \tilde { C } _ { h }$ $\begin{array} { r } { \mathbb { E } _ { i } \| g _ { i } ( v ) - \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \bar { g _ { i } } ( v ) \| ^ { 2 } \leq \sigma ^ { 2 } } \end{array}$ for any v.

The weak convexity of $F ( \mathbf { w } )$ in (2) is guaranteed by the following Proposition.

Proposition 4.4. Under Assumption 4.3, $F ( \mathbf { w } )$ in (2) is $\rho _ { F }$ -weakly-convex with $\begin{array} { r l } { \rho _ { F } } & { { } = } \end{array}$ $\sqrt { \bar { d _ { 1 } } } ( \sqrt { d _ { 2 } } L _ { h } C _ { g } + \rho _ { g } C _ { h } ^ { 2 } ) C _ { f } + \rho _ { f } \bar { C } _ { g } ^ { 2 } C _ { h } ^ { 2 } .$

We extend SONX to Algorithm 2 for (2), which is referred to as SONT. For dealing with the extra layer of compositional problem, we maintain another multi-block variable to track the extra layer of function value estimation. To understand this, we first write down the true subgradient:

$$
\partial F (\mathbf {w}) = \frac {1}{n _ {1}} \sum_ {i \in \mathcal {S} _ {1}} \left[ \left(\frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} \nabla h _ {i, j} (\mathbf {w}) \partial g _ {i} (h _ {i, j} (\mathbf {w}))\right) \partial f _ {i} \left(\frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (h _ {i, j} (\mathbf {w}))\right) \right].
$$

To approximate this subgradient, we need the estimations of $\begin{array} { r } { \frac { 1 } { n _ { 2 } } \sum _ { j \in { \cal S } _ { 2 } } g _ { i } \big ( h _ { i , j } ( { \bf w } ) \big ) } \end{array}$ and $h _ { i , j } ( \mathbf { w } )$ which can be tracked by using MSVR estimators denoted by $\{ u _ { i , t } : i \in S _ { 1 } \}$ and $\{ v _ { i , j , t } : ( i , j ) \in$ $S _ { 1 } \times S _ { 2 } \}$ , respectively. As a result, a stochastic estimation of $\partial F ( \mathbf { w } _ { t } )$ is computed in step 6 of Algorithm 2, and the model parameter is updated similarly as before.

## 4.3 Convergence Analysis

In this section, we present the proof sketch of the convergence guarantee for Algorithm 1. The analysis for Algorithm 2 follows in a similar manner. The detailed proofs can be found in Appendix A (please refer to the supplement). Before starting the proof, we define a constant $M ^ { 2 } \geq C _ { f } ^ { 2 } \dot { C } _ { g } ^ { 2 }$ so that under Assumption 4.1 we have $\mathbb { E } _ { t } [ \| G _ { t } \| ^ { 2 } ] \le M ^ { 2 }$ . Then we start by giving the error bound of the MSVR estimator in Algorithm 1. The following norm bound of the estimation error follows from the squared-norm error bound in Lemma 1 from [15], whose proof is given in Appendix D.3.

Lemma 4.5. Consider the update for $\{ u _ { i , t } : i \in S \}$ in Algorithm 1. Assume $g _ { i }$ is C<sub>g</sub>-Lipshitz for all $i \in S .$ . With $\begin{array} { r } { \gamma = \frac { n - B _ { 1 } } { B _ { 1 } ( 1 - \tau ) } + ( 1 - \tau ) , \tau \leq \frac { 1 } { 2 } , } \end{array}$ , we have

$$
\mathbb {E} \left[ \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| \right] \leq (1 - \frac {B _ {1} \tau}{2 n}) ^ {t + 1} \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| + \frac {2 \tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 n C _ {g} M \eta}{B _ {1} \tau^ {1 / 2}}.
$$

For simplicity, denote by $\hat { \mathbf { w } } _ { t } : = \mathrm { p r o x } _ { F / \bar { \rho } } \big ( \mathbf { w } _ { t } \big )$ . Then using the definition of Moreau envelope and the update rule of $\mathbf { w } _ { t } .$ , we can obtain a bound for the change in the Moreau envelope,

$$
\mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}) ] \leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) + \bar {\rho} \eta \langle \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}, \mathbb {E} _ {t} [ G _ {t} ] \rangle + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2}.\tag{5}
$$

where $\begin{array} { r } { \mathbb { E } _ { t } [ G _ { t } ] = \frac { 1 } { n } \sum _ { i \in S _ { 1 } } \partial g _ { i } ( \mathbf { w } _ { t } ) \partial f _ { i } ( u _ { i , t } ) } \end{array}$ is the subgradient approximation based on the MSVR estimator $u _ { i , t }$ of the inner function value. This is a standard result in weakly-convex optimization [6].

To bound the inner product $\left. \hat { \mathbf { w } } _ { t } - \mathbf { w } _ { t } , \mathbb { E } _ { t } [ G _ { t } ] \right.$ on the right-hand-side of (5), we apply the assumptions that $f _ { i }$ is weakly-convex, Lipschitz continuous and non-decreasing, and $g _ { i }$ is weakly-convex. Its upper bound is given as follows.

$$
(\hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}) ^ {\top} \mathbb {E} _ {t} [ G _ {t} ] \leq F (\hat {\mathbf {w}} _ {t}) - F (\mathbf {w} _ {t}) + \frac {1}{n} \sum_ {i \in \mathcal {S}} [ f _ {i} (g _ {i} (\mathbf {w} _ {t})) - f (u _ {i, t}) - \partial f (u _ {i, t}) ^ {\top} (g _ {i} (\mathbf {w} _ {t}) - u _ {i, t})
$$

$$
+ \rho_ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} \| ^ {2} + (\frac {\rho_ {g} C _ {f}}{2} + \rho_ {f} C _ {g} ^ {2}) \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} ].\tag{6}
$$

Due to the $\rho _ { F }$ -weak convexity of $F ( \mathbf { w } )$ , we have $( \bar { \rho } - \rho _ { F } )$ -strong convexity of $\mathbf { w } \mapsto F ( \mathbf { w } ) + \textstyle \frac { \bar { \rho } } { 2 } \| \mathbf { w } _ { t } -$ $\mathbf { w } \Vert ^ { 2 }$ . Then it follows $\begin{array} { r } { F ( \hat { \mathbf { w } } _ { t } ) - F ( \mathbf { w } _ { t } ) \leq \big ( \frac { \rho _ { F } } { 2 } - \bar { \rho } \big ) \| \mathbf { w } _ { t } - \hat { \mathbf { w } } _ { t } \| ^ { 2 } } \end{array}$ . Combining this with inequalities (5), (6), and setting $\bar { \rho }$ sufficiently large we have

$$
\mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}) ] \leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2} + \frac {\bar {\rho} \eta}{n} \sum_ {i \in \mathcal {S}} [ - \frac {\bar {\rho}}{2} \| \mathbf {w} _ {t} - \hat {\mathbf {w}} _ {t} \| ^ {2}\tag{7}
$$

$$
\left. + f _ {i} \left(g _ {i} \left(\mathbf {w} _ {t}\right)\right) - f \left(u _ {i, t}\right) - \partial f _ {i} \left(u _ {i, t}\right) ^ {\top} \left(g _ {i} \left(\mathbf {w} _ {t}\right) - u _ {i, t}\right) + \rho_ {f} \| g _ {i} \left(\mathbf {w} _ {t}\right) - u _ {i, t} \| ^ {2} \right].
$$

Recall Lemma 3.2, we have $\begin{array} { r } { \| { \bf w } _ { t } - \hat { \bf w } _ { t } \| ^ { 2 } = \frac { 1 } { \bar { \varrho } ^ { 2 } } \| \nabla F _ { 1 / \bar { \rho } } ( { \bf w } _ { t } ) \| ^ { 2 } } \end{array}$ . Moreover, the last three terms on the R.H.S of inequality (7) can be bounded using the Lipschitz continuity of $f _ { i }$ and the error bound given in Lemma 4.5. Then we can conclude the complexity of SONX with the following theorem.

Theorem 4.6. Under Assumption 4.1 with $\begin{array} { r } { \gamma = \frac { n - B _ { 1 } } { B _ { 1 } ( 1 - \tau ) } + ( 1 - \tau ) , \tau = \mathcal { O } ( B _ { 2 } \epsilon ^ { 4 } ) \leq \frac { 1 } { 2 } , \eta = } \end{array}$ $\mathcal { O } ( \frac { B _ { 1 } B _ { 2 } ^ { 1 / 2 } \epsilon ^ { 4 } } { n } )$ , and $\bar { \rho } = \rho _ { F } + \rho _ { g } C _ { f } + 2 \rho _ { f } C _ { g } ^ { 2 }$ , Algorithm 1 converges to an ϵ-stationary point ofthe Moreau envelope $F _ { 1 / \bar { \rho } }$ in $\begin{array} { r } { T = \mathcal { O } ( \frac { n } { B _ { 1 } B _ { 2 } ^ { 1 / 2 } } \epsilon ^ { - \tilde { 6 } } ) } \end{array}$ iterations.

Remark. Similar to the complexity for smooth FCCO problems [26, 15], Theorem 4.6 guarantees that SONX for NSWC FCCO has a parallel speed-up in terms of the batch size $B _ { 1 }$ and linear dependency on n. The dependency of the complexity on the batch size $B _ { 2 }$ is due to the use of MSVR estimator, which matches the results in [15]. If the MSVR estimator in SONX is replaced by moving average estimator, the complexity becomes $\mathcal { O } ( \frac { n } { B _ { 1 } B _ { 2 } } \epsilon ^ { - 8 } )$ (cf. Appendix B).

Following a similar proof strategy, the convergence guarantee of Algorithm 2 is given below.

Theorem 4.7. (Informal) Under Assumption 4.3, with appropriate values $o f \gamma _ { 1 } , \gamma _ { 2 } , \tau _ { 1 } , \tau _ { 2 } , \eta$ and a proper constant ρ¯, Algorithm 2 converges to an ϵ-stationary point ofthe Moreau envelope $F _ { 1 / \bar { \rho } }$ in

$$
T = \mathcal {O} \left(\max \left\{\frac {1}{B _ {3} ^ {1 / 2}}, \frac {n _ {1} ^ {1 / 4}}{B _ {1} ^ {1 / 4} n _ {2} ^ {1 / 4}}, \frac {n _ {1} ^ {1 / 2}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2}} \right\} \frac {n _ {1} n _ {2}}{B _ {1} B _ {2}} \epsilon^ {- 6}\right) i t e r a t i o n s.
$$

Remark. In the worst case, the complexity has a worse dependency on $n _ { 1 } / B _ { 1 } , \mathrm { i . e . , } \mathcal { O } ( n _ { 1 } ^ { 3 / 2 } / B _ { 1 } ^ { 3 / 2 } )$ This is caused by the two layers of block-sampling update for $\{ u _ { i , t } , i \in \mathcal { S } _ { 1 } \}$ and $\{ v _ { i , j , t } : ( i , \bar { j } ) \in$ $S _ { 1 } \times S _ { 2 } \}$ . When $n _ { 1 } = B _ { 1 } = 1$ and $B _ { 3 } \leq \sqrt { n _ { 2 } }$ , the complexity of SONT becomes similar as SONX, which is understandable as the inner two levels in TCCO is the same as FCCO.

## 5 Applications

NSWC FCCO finds important applications in group distributionally robust optimization (group DRO) and two-way partial AUC (TPAUC) maximization.

Consider N groups with different distributions. Each group k has an averaged loss $L _ { k } ( w ) =$ $\begin{array} { r } { \frac { 1 } { n _ { k } } \sum _ { i = 1 } ^ { n _ { k } } \ell ( f _ { w } ^ { \mathbf { \bar { \alpha } } } ( x _ { i } ^ { k } ) , y _ { i } ^ { k } ) } \end{array}$ , where w is the the model parameter and $( x _ { i } ^ { k } , y _ { i } ^ { k } )$ is a data point. It has been shown in previous study [23] that the group DRO problem can be formulated into

$$
\min _ {w} \min _ {s} F (w, s) = \frac {1}{K} \sum_ {k = 1} ^ {N} [ L _ {k} (w) - s ] _ {+} + s.
$$

This formulation can be mapped into non-smooth weakly-convex FCCO under certain assumptions. Due to space limitation, we defer the comprehensive discussion of group DRO to Appendix E. The rest of this section focuses on TPAUC maximization.

Let X denote an input example and $h _ { \mathbf { w } } ( X )$ denote a prediction of a parameterized deep net on data X. Denote by $S _ { + }$ <sub>+</sub> the set of $n _ { + }$ positive examples and by $\smash { \mathcal { S } _ { - } }$ the set of $n _ { - }$ <sub>−</sub> negative examples. TPAUC measures the area under $\mathbf { R O C }$ curve where the true positive rate (TPR) is higher than α and the false positive rate (FPR) is lower than an upper bound $\beta .$ . A surrogate loss for optimizing TPAUC

with $\mathrm { F P R } \leq \beta , \mathrm { T P R } \geq \alpha$ is given by [34]:

$$
\min _ {\mathbf {w}} \frac {1}{n _ {+}} \frac {1}{n _ {-}} \sum_ {X _ {i} \in \mathcal {S} _ {+} ^ {\uparrow} [ 1, k _ {1} ]} \sum_ {X _ {j} \in \mathcal {S} _ {-} ^ {\downarrow} [ 1, k _ {2} ]} \ell (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})),\tag{8}
$$

where $\ell ( \cdot )$ is a convex, monotonically non-decreasing surrogate loss of the indicator function $\mathbb { I } ( h _ { \mathbf { w } } ( X _ { j } ) \geq h _ { \mathbf { w } } ( X _ { i } ) ) , \mathcal { S } _ { + } ^ { \uparrow } [ 1 , k _ { 1 } ]$ is the set of positive examples with $k _ { 1 } = \lfloor n _ { + } \alpha \rfloor$ smallest scores, and $S _ { - } ^ { \downarrow } [ 1 , k _ { 2 } ]$ is the set of negative examples with $k _ { 2 } = \lfloor n _ { - } \beta \rfloor$ largest scores. To tackle the challenge of selecting examples from $S _ { + } ^ { \uparrow } [ 1 , k _ { 1 } ]$ and $S _ { - } ^ { \downarrow } [ 1 , k _ { 2 } ]$ , the above problem is cast into the following [44]: $\begin{array} { r } { \underset { \mathbf { w } , \mathbf { s } ^ { \prime } , \mathbf { s } } { \operatorname* { m i n } } \frac { 1 } { n _ { + } } \sum _ { X _ { i } \in { \mathcal { S } _ { + } } } f _ { i } ( \psi _ { i } ( \mathbf { w } , s _ { i } ) , s ^ { \prime } ) } \end{array}$ 2 (9)

where $f _ { i } ( g , s ^ { \prime } ) = s ^ { \prime } + \frac { ( g - s ^ { \prime } ) _ { + } } { \alpha } , \psi _ { i } ( { \bf w } , s _ { i } ) = \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in \mathcal { S } _ { - } } s _ { i } + \frac { ( \ell ( h _ { \mathbf { w } } ( X _ { j } ) - h _ { \mathbf { w } } ( X _ { i } ) ) - s _ { i } ) _ { + } } { \beta } .$ where $\mathbf { s } = ( s _ { 1 } , \ldots , s _ { n _ { + } } )$ . We will consider two scenarios, namely regular learning scenario where $X _ { i } \in \mathbb { R } ^ { d _ { 0 } }$ is an instance, and multi-instance learning (MIL) scenario where $X _ { i } = \{ \mathbf { x } _ { i } ^ { 1 } , \ldots , \mathbf { x } _ { i } ^ { m _ { i } } \in$ $\mathbb { R } ^ { d _ { 0 } } \}$ contains multiple instances (e.g., one patient has hundreds of high-resolution CT images). $\mathbf { A }$ challenge in MIL is that the number of instances $m _ { i }$ for each data might be large such that it is difficult to load all instances into the memory for mini-batch training. It becomes more nuanced especially because MIL involves a pooling operation that aggregates the predicted information of individual instances into a single prediction, which can be usually written as a compositional function with the inner function being an average over instances from X. For simplicity of exposition, below we consider the mean pooling $\begin{array} { r } { h _ { \mathbf { w } } ( X ) = \frac { 1 } { | X | } \sum _ { \mathbf { x } \in X } e ( \mathbf { w } _ { e } ; \mathbf { x } ) ^ { \top } \mathbf { w } _ { c } . } \end{array}$ , where $e ( \mathbf { w } _ { e } , \mathbf { x } )$ is the encoded feature representation of instance x with a parameter $\mathbf { w } _ { e } ,$ and ${ \bf w } _ { c }$ is the parameter of the classifier. We will map the regular learning problem as NSWC FCCO and the MIL problem as NSWC TCCO.

The problem (9) is slightly more complicated than (1) or (2) due to the presence of $s ^ { \prime } , \mathbf { s }$ . In order to understand the applicability of our analysis and results to (9), we ignore $s ^ { \prime } { \mathrm { . } }$ s for a moment. In the regular learning setting when $h _ { \mathbf { w } } ( X ) \bar { = } e ( \mathbf { w } _ { e } , X ) ^ { \top } \mathbf { w } _ { c }$ can be directly computed, we can map the problem into NSWC FCCO, where $f _ { i } ( g , s ^ { \prime } )$ is non-smooth, convex, and non-decreasing in terms of $^ { g , }$ and $g _ { i } ( \mathbf { w } , s _ { i } ) = \psi _ { i } ( \mathbf { w } , s _ { i } )$ is non-smooth, and is proved to be weakly when $\ell ( \cdot )$ is convex and $h _ { \mathbf { w } } ( X )$ is smooth in terms of w. In the MIL setting with mean pooling, we can map the problem into NSWC TCCO by defining $\begin{array} { r } { h _ { i } ( \mathbf { w } ) = \frac { 1 } { | X _ { i } | } \sum _ { \mathbf { x } \in X _ { i } } e ( \mathbf { w } _ { e } ; \mathbf { x } ) ^ { \top } \mathbf { w } _ { c } , h _ { i j } ( \mathbf { w } ) = h _ { j } ( \mathbf { w } ) - h _ { i } ( \mathbf { w } ) } \end{array}$ and $\begin{array} { r } { g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) = s _ { i } + \frac { ( \ell ( h _ { i , j } ( \mathbf { w } ) ) - s _ { i } ) _ { + } } { \beta } } \end{array}$ , and $\begin{array} { r } { f _ { i } ( g _ { i } , s ^ { \prime } ) = s ^ { \prime } + \frac { ( g _ { i } - s ^ { \prime } ) _ { + } } { \alpha } } \end{array}$ , where $f _ { i }$ is non-smooth, convex, and non-decreasing in terms of $g _ { i } ,$ , and $g _ { i } ( h _ { i j } ( \mathbf { w } ) , s _ { i } )$ is non-smooth, convex, monotonic in terms of $h _ { i j } ( \mathbf { w } )$ when $\ell ( \cdot )$ is convex and monotonically non-decreasing, and $g _ { i } ( h _ { i j } ( \mathbf { w } ) , s _ { i } )$ is weakly convex in terms of w when $h _ { i j } ( \mathbf { w } )$ is smooth and Lipchitz continuous in terms of w. Hence, the problem (9) satisfies the conditions in Assumption 4.1 for the regular learning setting and that in Assumption 4.3 for the MIL with mean pooling under mild regularity conditions of the neural network. We present full details in Appendix C.1 for interested readers.

To compute the gradient estimator w.r.t $\mathbf { w } , u _ { i , t }$ will be maintained for tracking $g _ { i } ( \mathbf { w } , s _ { i } )$ in the regular setting $\begin{array} { r } { \mathrm { o r } \ \frac { 1 } { n _ { - } } \sum _ { X _ { i } \in { \mathcal { S } } _ { - } } g _ { i } \big ( h _ { i , j } ( \mathbf { w } ) , s _ { i } \big ) } \end{array}$ in the MIL setting, $v _ { i , t }$ will be maintained for tracking $h _ { i } ( \mathbf { w } )$ in the MIL setting, which are updated similar to that in SONX and SONT. One difference from SONT is that $v _ { i , j , t }$ is decoupled into $v _ { i , t }$ and $v _ { j , t }$ due to that $h _ { i , j }$ can be decoupled. In terms of the extra variable $s ^ { \prime } , \mathbf { s } .$ , the objective function is convex w.r.t both s<sup>′</sup> and s, which allows us to simply update $s ^ { \prime }$ by SGD using the stochastic gradient estimator $\begin{array} { r } { \frac { 1 } { B _ { 1 } } \sum _ { i \in { \mathcal { B } _ { 1 } ^ { t } } } \partial _ { s ^ { \prime } } f _ { i } \left( u _ { i , t } , s _ { t } ^ { \prime } \right) } \end{array}$ and we update $s _ { i }$ by SGD using the stochastic gradient estimator $\begin{array} { r } { \left\lceil \frac { 1 } { B _ { 2 } } \sum _ { j \in \mathcal { B } _ { 2 } ^ { t } } \partial _ { s _ { i } } g _ { i } \big ( \boldsymbol { v } _ { j , t } - \boldsymbol { v } _ { i , t } , \boldsymbol { s } _ { i , t } \big ) \right\rceil \partial _ { u } f _ { i } \big ( \boldsymbol { u } _ { i , t } , \boldsymbol { s } _ { t } ^ { \prime } \big ) } \end{array}$ Detailed updates are presented in Algorithm 5 and Algorithm 6 in Appendix C.2. We can extend the convergence analysis of SONX and SONT to the two learning settings of TPAUC maximization, which is included in Appendix C.4. Finally, it is worth mentioning that we can also extend the results to other pooling operations, including smoothed max pooling and attention-based pooling [45]. Due to limit of space, we include discussions in Appendix C.3 as well.

## 6 Experimental Results

We justify the effectiveness of the proposed SONX and SONT algorithms for TPAUC Maximization in the regular learning setting and MIL setting [14, 45].

Table 2: Testing TPAUC on molecule datasets (top) and on MIL datasets (bottom). The two numbers in parentheses of the second line refers to the lower bound of TPR and the upper bound of FPR for evaluating TPAUC. The two numbers of each method refers to the mean TPAUC and its std.

<table><tr><td></td><td colspan="2">moltox21 (t0)</td><td colspan="2">molmuv (t1)</td><td colspan="2">molpcba (t0)</td></tr><tr><td>Method</td><td>(0.6, 0.4)</td><td>(0.5, 0.5)</td><td>(0.6, 0.4)</td><td>(0.5, 0.5)</td><td>(0.6, 0.4)</td><td>(0.5, 0.5)</td></tr><tr><td>CE</td><td>0.067 (0.001)</td><td>0.208 (0.001)</td><td>0.161 (0.034)</td><td>0.469 (0.018)</td><td>0.095 (0.001)</td><td>0.264 (0.001)</td></tr><tr><td>AUC-SH</td><td>0.064 (0.008)</td><td>0.217 (0.014)</td><td>0.260 (0.130)</td><td>0.444 (0.128)</td><td>0.140 (0.003)</td><td>0.312 (0.003)</td></tr><tr><td>AUC-M</td><td>0.066 (0.009)</td><td>0.209 (0.01)</td><td>0.114 (0.079)</td><td>0.433 (0.053)</td><td>0.142 (0.009)</td><td>0.313 (0.003)</td></tr><tr><td>MB</td><td>0.067 (0.015)</td><td>0.215 (0.023)</td><td>0.173 (0.153)</td><td>0.426 (0.118)</td><td>0.095 (0.002)</td><td>0.262 (0.003)</td></tr><tr><td>AW-poly</td><td>0.064 (0.01)</td><td>0.206 (0.025)</td><td>0.172 (0.144)</td><td>0.393 (0.123)</td><td>0.110 (0.001)</td><td>0.281 (0.002)</td></tr><tr><td>SOTA-s</td><td>0.068 (0.018)</td><td>0.23 (0.021)</td><td>0.327 (0.164)</td><td>0.526 (0.122)</td><td>0.143 (0.001)</td><td>0.314 (0.002)</td></tr><tr><td>SONX</td><td>0.07 (0.035)</td><td>0.252 (0.025)</td><td>0.347 (0.175)</td><td>0.575 (0.122)</td><td>0.158 (0.006)</td><td>0.335 (0.006)</td></tr><tr><td></td><td colspan="3">MUSK2</td><td colspan="3">Fox</td></tr><tr><td>Method</td><td>(0.5, 0.5)</td><td>(0.3, 0.7)</td><td>(0.1, 0.9)</td><td>(0.5, 0.5)</td><td>(0.3, 0.7)</td><td>(0.1, 0.9)</td></tr><tr><td>AUC-M (att)</td><td>0.675 (0.1)</td><td>0.783 (0.067)</td><td>0.867 (0.036)</td><td>0.032 (0.03)</td><td>0.253 (0.098)</td><td>0.444 (0.118)</td></tr><tr><td>MIDAM (smx)</td><td>0.525 (0.2)</td><td>0.667 (0.149)</td><td>0.8 (0.097)</td><td>0.048 (0.059)</td><td>0.265 (0.119)</td><td>0.449 (0.113)</td></tr><tr><td>MIDAM (att)</td><td>0.6 (0.215)</td><td>0.717 (0.135)</td><td>0.819 (0.092)</td><td>0.016 (0.032)</td><td>0.249 (0.125)</td><td>0.509 (0.065)</td></tr><tr><td>SOTAs (att)</td><td>0.6 (0.267)</td><td>0.683 (0.178)</td><td>0.819 (0.097)</td><td>0.024 (0.032)</td><td>0.278 (0.059)</td><td>0.477 (0.046)</td></tr><tr><td>SONT (att)</td><td>0.7 (0.1)</td><td>0.8 (0.067)</td><td>0.867 (0.036)</td><td>0.12 (0.131)</td><td>0.343 (0.176)</td><td>0.578 (0.119)</td></tr><tr><td></td><td colspan="3">Colon</td><td colspan="3">Lung</td></tr><tr><td>Method</td><td>(0.5, 0.5)</td><td>(0.3, 0.7)</td><td>(0.1, 0.9)</td><td>(0.5, 0.5)</td><td>(0.3, 0.7)</td><td>(0.1, 0.9)</td></tr><tr><td>AUC-M (att)</td><td>0.576 (0.1)</td><td>0.739 (0.061)</td><td>0.803 (0.038)</td><td>0.32 (0.181)</td><td>0.609 (0.113)</td><td>0.744 (0.082)</td></tr><tr><td>MIDAM (smx)</td><td>0.646 (0.083)</td><td>0.787 (0.04)</td><td>0.863 (0.026)</td><td>0.43 (0.195)</td><td>0.68 (0.128)</td><td>0.824 (0.055)</td></tr><tr><td>MIDAM (att)</td><td>0.548 (0.253)</td><td>0.738 (0.149)</td><td>0.826 (0.102)</td><td>0.544 (0.261)</td><td>0.716 (0.189)</td><td>0.815 (0.129)</td></tr><tr><td>SOTAs (att)</td><td>0.772 (0.124)</td><td>0.862 (0.073)</td><td>0.911 (0.045)</td><td>0.539 (0.153)</td><td>0.745 (0.077)</td><td>0.841 (0.049)</td></tr><tr><td>SONT (att)</td><td>0.8 (0.166)</td><td>0.875 (0.099)</td><td>0.916 (0.065)</td><td>0.639 (0.137)</td><td>0.779 (0.041)</td><td>0.865 (0.028)</td></tr></table>

Baselines. For regular TPAUC maximization, we compare SONX with the following competitive methods: 1) Cross Entropy (CE) loss minimization; 2) AUC maximization with squared hinge loss (AUC-SH); 3) AUC maximization with min-max margin loss (AUC-M) [37]; 4) Mini-Batch based heuristic loss (MB) [16]; 5) Adhoc-Weighting based method with polynomial function (AWpoly) [35]; 5) a single-loop algorithm (SOTAs) for optimizing a smooth surrogate for TPAUC [44]. For MIL TPAUC maximization, we consider the following baselines: 1) AUC-M with attention-based pooling (AUC-M [att]); 2) SOTAs with attention-based pooling, which is a natural combination between advanced TPAUC optimization and MIL pooling technique; 3) the recently proposed provable multi-instance deep AUC maximization methods with stochastic smoothed-max pooling and attention-based pooling (MIDAM [smx] and MIDAM [att]) [45]. The first two baselines use naive mini-batch pooling for computing the loss function in AUC-M and SOTAs. We implement SONT for MIL TPAUC maximization with attention-based pooling, which is referred to as SONT (att).

Datasets. For regular TPAUC maximization, we use three molecule datasets as in [44], namely moltox21 (the No.0 target), molmuv (the No.1 target) and molpcba (the No.0 target) [29]. For MIL TPAUC maximization, we use four MIL datasets, including two tabular datasets MUSK2 and Fox, and two medical image datasets Colon and Lung. MUSK2 and Fox are two tabular datasets that have been widely adopted for MIL benchmark study [14]. Colon and Lung are two histopathology (medical image) datasets that have large image size (512×512) but local interests for classification [2]. For Colon dataset, the adenocarcinoma is regarded as positive label and benign is negative; for Lung dataset, we treat adenocarcinoma as positive and squamous cell carcinoma as negative <sup>3</sup>. For both of the histopathology datasets, we uniformly randomly sample 100 positive and 1000 negative data for experiments. For all MIL datasets, we uniformly randomly split 10% as the testing and the remaining as the training and validation. The statistics for all used datasets are summarized in Table 3and Table 4 in Appendix F.

Experiment Settings. For regular TPAUC maximization, we use the same setting as in [44]. The adopted backbone Graph Nueral Network (GNN) model is Graph Isomorphism Network (GIN), which has 5 mean-pooling layers with 64 number of hidden units and dropout rate 0.5 [30]. We utilize the sigmoid function for the final output layer to generate the prediction score, and set the surrogate loss ℓ(·) as squared hinge loss with a margin parameter. We follow the setups for model training and tuning exactly the same as the prior work [44]. Essentially, the model is trained by 60 epochs and the learning rate is decreased by 10-fold after every 20 epochs. The model is initialized as a pretrained model from CE loss on the training datasets. We fix the learning rate of SONX as 1e-2 and moving average parameter τ as 0.9; tune the parameter γ in {0, 1e-1,1e-2,1e-3}, the parameter α, β in {0.1,0.3,0.5} and fix the margin parameter of the surrogate loss ℓ as 1.0, which cost the same tuning effort as the other baselines. The weight decay is set as the same value (2e-4) with the other baselines. For baselines, we directly use the results reported in [44] since we use the same setting.

![](images/df59ba47088be0a0d318215cfe1e4284c2f9108b20ef2892c10f7bcf9457cbf2.jpg)  
(a) molmuv (t1)

![](images/90c2470e31dee232f48561f0915860493700e0f5dc9df9349acaeb0f91a9454c.jpg)  
(b) molpcba (t0)

![](images/a9ca45e46bafc69eb1407e5c8e9459f66964efeebc90c010e4bb7e950282294c.jpg)  
(c) MUSK2

![](images/25672098042e0688df7af46e2b82b7a2616b0eb2b721b397d93279ce74627dc6.jpg)  
(d) Fox  
Figure 1: Training Curves of SONX (left two) and SONT (right two) for TPAUC maximization with different γ. The y-axis is the TPAUC (0.5, 0.5).

For MIL TPAUC maximization, we train a simple Feed Forward Neural Network (FFNN) with one hidden layer (the number of neurons equals to data dimension) for the two tabular datasets and ResNet20 for the two medical image datasets. Sigmoid transformation is adopted for the output layer to generate prediction score. The training epoch number is fixed as 100 epochs for all methods; the bag batch size is fixed as 16 (resp. 8) and the number of sampled instances per bag is fixed as 4 (resp. 128) for tabular (resp. medical image) datasets; the learning rate is tuned in {1e-2, 1e-3, 1e-4} and decreased by 10 folds at the end of 50-th and 75-th epoch for all baselines. For SONT (att), we set moving average parameter $\tau _ { 1 } = \tau _ { 2 }$ as 0.9; tune the parameter $\gamma _ { 1 } = \gamma _ { 2 } = \gamma$ in {0, 1e-1,1e-2,1e-3} and fix the margin parameter of the surrogate loss ℓ as 0.5, and the parameter $\alpha , \beta$ in {0.1,0.5,0.9}. Similar parameters in baselines are set the same or tuned similarly. For all experiments, we utilize 5-fold-cross-validation to evaluate the testing performance based on the best validation performance with possible early stopping choice.

Results. The testing results for the regular and MIL TPUAC maximization with different TPAUC measures are summarized in the Table 2. From Table 2, we observe that our method SONX achieves the best performance for regular TPAUC maximization. It is better than the state-of-the-art method SOTAs for TPAUC maximization. We attribute the better performance of SONX to the fact that the objective of SONX is an exact estimator of TPAUC while the smoothed objective of SOTAs is an inexact estimator of TPAUC. We also observe that SONT (att) achieves the best performance in all cases, which is not surprising since it is the only one that directly optimizes the TPAUC surrogate. In contrast, other baselines either optimizes a different objective (MIDAM) or does not ensure convergence due to the use of mini-batch pooling (AUC-M, SOTAs).

Ablation Study. We conduct ablation studies to demonstrate the effect of the error correction term on the training convergence by varying the γ value for SONX and SONT, where $\gamma _ { 1 } = \gamma _ { 2 } = \gamma$ is set as the same value in SONT. The training convergence results are presented in Figure 1. We can see that an appropriate value of $\gamma > 0$ can yield a faster convergence than $\gamma = 0 .$ , which verifies the faster convergence of using MSVR estimators than using moving average estimators. However, we do observe a gap between theory and practice, as setting a large value of $\gamma > 1$ as in the theory might not yield convergence. This phenomenon is also observed in [12]. We conjecture that the gap could be fixed by considering convex objectives [40], which is left as future work.

## 7 Conclusions

In this paper, we have considered non-smooth weakly-convex two-level and tri-level finite-sum coupled compositional optimization problems. We presented novel convergence analysis of two stochastic algorithms and established their complexity. Applications in deep learning for two-way partial AUC maximization was considered and great performance of proposed algorithms were demonstrated through experiments on multiple datasets. A future work is to prove the convergence of both algorithms for convex objectives.

## Acknowledgements

We thank anonymous reviewers for constructive comments. Q. Hu, D. Zhu and T. Yang were partially supported by NSF Career Award 2246753, NSF Grant 2246757, 2246756 and 2306572.

## References

[1] Krishnakumar Balasubramanian, Saeed Ghadimi, and Anthony Nguyen. Stochastic multilevel composition optimization algorithms with level-independent convergence rates. SIAM Journal on Optimization, 32(2):519–544, 2022.

[2] Andrew A Borkowski, Marilyn M Bui, L Brannon Thomas, Catherine P Wilson, Lauren A DeLand, and Stephen M Mastorides. Lung and colon cancer histopathological image dataset (lc25000). arXiv preprint arXiv:1912.12142, 2019.

[3] Tianyi Chen, Yuejiao Sun, and Wotao Yin. Solving stochastic compositional optimization is nearly as easy as solving stochastic optimization. IEEE Transactions on Signal Processing, 69:4937–4948, 2021.

[4] Sebastian Curi, Kfir Y. Levy, Stefanie Jegelka, and Andreas Krause. Adaptive sampling for stochastic risk-averse learning. In H. Larochelle, M. Ranzato, R. Hadsell, M.F. Balcan, and H. Lin, editors, Advances in Neural Information Processing Systems, volume 33, pages 1036–1047. Curran Associates, Inc., 2020.

[5] Ashok Cutkosky and Francesco Orabona. Momentum-based variance reduction in non-convex sgd. In H. Wallach, H. Larochelle, A. Beygelzimer, F. d'Alché-Buc, E. Fox, and R. Garnett, editors, Advances in Neural Information Processing Systems, volume 32. Curran Associates, Inc., 2019.

[6] Damek Davis and Dmitriy Drusvyatskiy. Stochastic model-based minimization of weakly convex functions, 2018.

[7] Damek Davis and Benjamin Grimmer. Proximally guided stochastic subgradient method for nonsmooth, nonconvex problems. SIAM Journal on Optimization, 29(3):1908–1930, 2019.

[8] Dmitriy Drusvyatskiy and Courtney Paquette. Efficiency of minimizing compositions of convex functions and smooth maps. Math. Program., 178(1-2):503–558, 2019.

[9] John C. Duchi and Feng Ruan. Stochastic methods for composite and weakly convex optimiza tion problems. SIAM Journal on Optimization, 28(4):3229–3259, 2018.

[10] S. Ghadimi, Andrzej Ruszczy’nski, and Mengdi Wang. A single timescale stochastic approximation method for nested stochastic optimization. SIAM J. Optim., 30:960–979, 2020.

[11] Lie He and Shiva Prasad Kasiviswanathan. Debiasing conditional stochastic optimization, 2023.

[12] Quanqi Hu, Zi-Hao Qiu, Zhishuai Guo, Lijun Zhang, and Tianbao Yang. Blockwise stochastic variance-reduced methods with parallel speedup for multi-block bilevel optimization. In Proceedings ofthe 39th International Conference on Machine Learning, 2023.

[13] Yifan Hu, Siqi Zhang, Xin Chen, and Niao He. Biased stochastic first-order methods for conditional stochastic optimization and applications in meta learning. Advances in Neural Information Processing Systems, 33, 2020.

[14] Maximilian Ilse, Jakub Tomczak, and Max Welling. Attention-based deep multiple instance learning. In Jennifer Dy and Andreas Krause, editors, Proceedings ofthe 35th International Conference on Machine Learning, volume 80 of Proceedings ofMachine Learning Research, pages 2127–2136. PMLR, 10–15 Jul 2018.

[15] Wei Jiang, Gang Li, Yibo Wang, Lijun Zhang, and Tianbao Yang. Multi-block-single-probe variance reduced estimator for coupled compositional optimization, 2022.

[16] Purushottam Kar, Harikrishna Narasimhan, and Prateek Jain. Online and stochastic gradient methods for non-decomposable loss functions. In Proceedings of the 27th International Conference on Neural Information Processing Systems - Volume 1, NIPS’14, page 694–702, Cambridge, MA, USA, 2014. MIT Press.

[17] Tianyi Lin, Chi Jin, and Michael Jordan. On gradient descent ascent for nonconvex-concave minimax problems. In Hal Daumé III and Aarti Singh, editors, Proceedings ofthe 37th International Conference on Machine Learning, volume 119 of Proceedings of Machine Learning Research, pages 6083–6093. PMLR, 13–18 Jul 2020.

[18] J.J. Moreau. Proximité et dualité dans un espace hilbertien. Bulletin de la Société Mathématique de France, 93:273–299, 1965.

[19] Qi Qi, Zhishuai Guo, Yi Xu, Rong Jin, and Tianbao Yang. An online method for a class of distributionally robust optimization with non-convex objectives. Advances in Neural Information Processing Systems, 34, 2021.

[20] Qi Qi, Youzhi Luo, Zhao Xu, Shuiwang Ji, and Tianbao Yang. Stochastic optimization of area under precision-recall curve for deep learning with provable convergence. In Advances in neural information processing systems, volume abs/2104.08736, 2021.

[21] Zi-Hao Qiu, Quanqi Hu, Yongjian Zhong, Lijun Zhang, and Tianbao Yang. Large-scale stochastic optimization of NDCG surrogates for deep learning with provable convergence. In Kamalika Chaudhuri, Stefanie Jegelka, Le Song, Csaba Szepesvari, Gang Niu, and Sivan Sabato, editors, Proceedings ofthe 39th International Conference on Machine Learning, volume 162 of Proceedings ofMachine Learning Research, pages 18122–18152. PMLR, 17–23 Jul 2022.

[22] Hassan Rafique, Mingrui Liu, Qihang Lin, and Tianbao Yang. Weakly-convex–concave min–max optimization: provable algorithms and applications in machine learning. Optimization Methods and Software, 37(3):1087–1121, 2022.

[23] R. T. Rockafellar and S. Uryasev. Optimization of conditional valueat-risk. Journal ofRisk, 2(3), 1999.

[24] R.T. Rockafellar, M. Wets, and R.J.B. Wets. Variational Analysis. Grundlehren der mathematis chen Wissenschaften. Springer Berlin Heidelberg, 2009.

[25] Shiori Sagawa, Pang Wei Koh, Tatsunori B. Hashimoto, and Percy Liang. Distributionally robust neural networks for group shifts: On the importance of regularization for worst-case generalization, 2020.

[26] Bokun Wang and Tianbao Yang. Finite-sum coupled compositional stochastic optimization: Theory and applications. In Kamalika Chaudhuri, Stefanie Jegelka, Le Song, Csaba Szepesvari, Gang Niu, and Sivan Sabato, editors, Proceedings of the 39th International Conference on Machine Learning, volume 162 of Proceedings ofMachine Learning Research, pages 23292– 23317. PMLR, 17–23 Jul 2022.

[27] Mengdi Wang, Ethan X Fang, and Han Liu. Stochastic compositional gradient descent: algorithms for minimizing compositions of expected-value functions. Mathematical Programming, 161(1-2):419–449, 2017.

[28] Mengdi Wang, Ji Liu, and Ethan X. Fang. Accelerating stochastic composition optimization, 2016.

[29] Zhenqin Wu, Bharath Ramsundar, Evan N Feinberg, Joseph Gomes, Caleb Geniesse, Aneesh S Pappu, Karl Leswing, and Vijay Pande. MoleculeNet: a benchmark for molecular machine learning. Chemical science, 9(2):513–530, 2018.

[30] Keyulu Xu, Weihua Hu, Jure Leskovec, and Stefanie Jegelka. How powerful are graph neural networks? In 7th International Conference on Learning Representations, 2019.

[31] Yan Yan, Yi Xu, Qihang Lin, Wei Liu, and Tianbao Yang. Optimal epoch stochastic gradient descent ascent methods for min-max optimization. In Advances in Neural Information Processing Systems 33 (NeurIPS), 2020.

[32] Shuoguang Yang, Mengdi Wang, and Ethan X. Fang. Multi-level stochastic gradient methods for nested composition optimization, 2018.

[33] Tianbao Yang. Algorithmic foundation of deep x-risk optimization. CoRR, abs/2206.00439, 2022.

[34] Tianbao Yang and Yiming Ying. AUC maximization in the era of big data and AI: A survey. ACM Comput. Surv., 55(8):172:1–172:37, 2023.

[35] Zhiyong Yang, Qianqian Xu, Shilong Bao, Yuan He, Xiaochun Cao, and Qingming Huang. When all we need is a piece of the pie: A generic framework for optimizing two-way partial auc. In Marina Meila and Tong Zhang, editors, Proceedings ofthe 38th International Conference on Machine Learning, volume 139 of Proceedings of Machine Learning Research, pages 11820–11829. PMLR, 18–24 Jul 2021.

[36] Zhuoning Yuan, Yuexin Wu, Zi-Hao Qiu, Xianzhi Du, Lijun Zhang, Denny Zhou, and Tianbao Yang. Provable stochastic optimization for global contrastive learning: Small batch does not harm performance. In Kamalika Chaudhuri, Stefanie Jegelka, Le Song, Csaba Szepesvari, Gang Niu, and Sivan Sabato, editors, Proceedings ofthe 39th International Conference on Machine Learning, volume 162 of Proceedings of Machine Learning Research, pages 25760–25782. PMLR, 17–23 Jul 2022.

[37] Zhuoning Yuan, Yan Yan, Milan Sonka, and Tianbao Yang. Large-scale robust deep auc maximization: A new surrogate loss and empirical studies on medical image classification, 2021.

[38] Junyu Zhang and Lin Xiao. A stochastic composite gradient method with incremental variance reduction. In Advances in Neural Information Processing Systems, pages 9075–9085, 2019.

[39] Junyu Zhang and Lin Xiao. Multilevel composite stochastic optimization via nested variance reduction. SIAM J. Optim., 31(2):1131–1157, 2021.

[40] Xuan Zhang, Necdet Serhat Aybat, and Mert Gurbuzbalaban. Robust accelerated primal-dual methods for computing saddle points. 2021.

[41] Xuan Zhang, Necdet Serhat Aybat, and Mert Gurbuzbalaban. Sapd+: An accelerated stochastic method for nonconvex-concave minimax problems, 2023.

[42] Zhe Zhang and Guanghui Lan. Optimal algorithms for convex nested stochastic composite optimization, 2022.

[43] Renbo Zhao. A primal-dual smoothing framework for max-structured non-convex optimization, 2022.

[44] Dixian Zhu, Gang Li, Bokun Wang, Xiaodong Wu, and Tianbao Yang. When AUC meets DRO: Optimizing partial AUC for deep learning with non-convex convergence guarantee. In Kamalika Chaudhuri, Stefanie Jegelka, Le Song, Csaba Szepesvari, Gang Niu, and Sivan Sabato, editors, Proceedings ofthe 39th International Conference on Machine Learning, volume 162 of Proceedings ofMachine Learning Research, pages 27548–27573. PMLR, 17–23 Jul 2022.

[45] Dixian Zhu, Bokun Wang, Zhi Chen, Yaxing Wang, Milan Sonka, Xiaodong Wu, and Tianbao Yang. Provable multi-instance deep auc maximization with stochastic pooling. In International Conference on Machine Learning. PMLR, 2023.

[46] Landi Zhu, Mert Gürbüzbalaban, and Andrzej Ruszczynski. Distributionally robust learning´ with weakly convex losses: Convergence rates and finite-sample guarantees, 2023.

## A Proofs of Theorem 4.6 and Theorem 4.7

In this section, we provide the detailed proofs for Theorem 4.6 and Theorem 4.7. We first give a basic property for weakly-convex functions.

Proposition A.1 (Proposition 2.1 in [7]). Suppose function $g ~ : ~ \mathbb { R } ^ { d } ~  ~ \mathbb { R } \cup \{ \infty \}$ is lowersemicontinuous. Then g is ρ-weakly-convex ifand only if

$$
g (y) \geq g (x) + \langle v, y - x \rangle - \frac {\rho}{2} \| y - x \| ^ {2}\tag{10}
$$

holds for all vectors $v \in \partial g ( x )$ and $x , y \in \mathbb { R } ^ { d }$

## A.1 Proof of Theorem 4.6

Note that the proof of Lemma 4.5 also implies the following squared-norm error bound,

$$
\mathbb {E} \left[ \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| ^ {2} \right] \leq (1 - \frac {B _ {1} \tau}{2 n}) ^ {t + 1} \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| ^ {2} + \frac {4 \tau \sigma^ {2}}{B _ {2}} + \frac {1 6 n ^ {2} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau}.
$$

Proof of Theorem 4.6. Define $\hat { \mathbf { w } } _ { t } : = \mathrm { p r o x } _ { F / \bar { \rho } } ( \mathbf { w } _ { t } )$ . For a given $i \in S$ , we have

$$
\begin{array}{r l} & f _ {i} (g _ {i} (\hat {\mathbf {w}} _ {t})) - f _ {i} (u _ {i, t}) \\ & \overset {(a)} {\geq} \partial f _ {i} (u _ {i, t}) ^ {\top} (g _ {i} (\hat {\mathbf {w}} _ {t}) - u _ {i, t}) - \frac {\rho_ {f}}{2} \| g _ {i} (\hat {\mathbf {w}} _ {t}) - u _ {i, t} \| ^ {2} \\ & \geq \partial f _ {i} (u _ {i, t}) ^ {\top} (g _ {i} (\hat {\mathbf {w}} _ {t}) - u _ {i, t}) - \rho_ {f} \| g _ {i} (\hat {\mathbf {w}} _ {t}) - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} - \rho_ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} \| ^ {2} \\ & \geq \partial f _ {i} (u _ {i, t}) ^ {\top} (g _ {i} (\hat {\mathbf {w}} _ {t}) - u _ {i, t}) - \rho_ {f} C _ {g} ^ {2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} - \rho_ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} \| ^ {2} \\ & \overset {(b)} {\geq} \partial f _ {i} (u _ {i, t}) ^ {\top} \biggl [ g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} + \partial g _ {i} (\mathbf {w} _ {t}) ^ {\top} (\hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}) - \frac {\rho_ {g}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} \biggr ] \\ & \quad - \rho_ {f} C _ {g} ^ {2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} - \rho_ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} \| ^ {2} \\ & \overset {(c)} {\geq} \partial f _ {i} (u _ {i, t}) ^ {\top} (g _ {i} (\mathbf {w} _ {t}) - u _ {i, t}) + \partial f _ {i} (u _ {i, t}) ^ {\top} \partial g _ {i} (\mathbf {w} _ {t}) ^ {\top} (\hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}) - (\frac {\rho_ {g} C _ {f}}{2} + \rho_ {f} C _ {g} ^ {2}) \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} \\ & \quad - \rho_ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} \| ^ {2} \end{array}
$$

where (a) follows from the ρ<sub>f</sub>-weak-convexity of $f _ { i } , ( \mathsf { b } )$ follows from that $f _ { i } ( \cdot )$ is non-decreasing and the weak convexity of $g _ { i } , \left( \mathrm { c } \right)$ is due to $0 \leq \partial f _ { i } ( u _ { i , t } ) \leq C _ { f }$ . Then it follows

$$
\begin{array}{r l} & {\frac {1}{n} \sum_ {i \in \mathcal {S}} \partial f _ {i} (u _ {i, t}) ^ {\top} \partial g _ {i} (\mathbf {w} _ {t}) ^ {\top} (\hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t})} \\ & {\leq \frac {1}{n} \sum_ {i \in \mathcal {S}} \left[ f _ {i} (g _ {i} (\hat {\mathbf {w}} _ {t})) - f _ {i} (u _ {i, t}) - \partial f _ {i} (u _ {i, t}) ^ {\top} (g _ {i} (\mathbf {w} _ {t}) - u _ {i, t}) + (\frac {\rho_ {g} C _ {f}}{2} + \rho_ {f} C _ {g} ^ {2}) \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} \right.} \\ & {\quad \left. + \rho_ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} \| ^ {2} \right]} \end{array}\tag{11}
$$

Now we consider the change in the Moreau envelope:

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}) ] = \mathbb {E} _ {t} \left[ \underset {\tilde {\mathbf {w}}} {\min} F (\tilde {\mathbf {w}}) + \frac {\bar {\rho}}{2} \| \tilde {\mathbf {w}} - \mathbf {w} _ {t + 1} \| ^ {2} \right]} \\ & {\quad \leq \mathbb {E} _ {t} \left[ F (\hat {\mathbf {w}} _ {t}) + \frac {\bar {\rho}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t + 1} \| ^ {2} \right]} \\ & {\quad = F (\hat {\mathbf {w}} _ {t}) + \mathbb {E} _ {t} \left[ \frac {\bar {\rho}}{2} \| \hat {\mathbf {w}} _ {t} - (\mathbf {w} _ {t} - \eta G _ {t}) \| ^ {2} \right]} \\ & {\quad \leq F (\hat {\mathbf {w}} _ {t}) + \frac {\bar {\rho}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \bar {\rho} \mathbb {E} _ {t} [ \eta \langle \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}, G _ {t} \rangle ] + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2}} \\ & {\quad = F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) + \bar {\rho} \eta \langle \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}, \mathbb {E} _ {t} [ G _ {t} ] \rangle + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2}} \end{array}\tag{12}
$$

where

$$
\mathbb {E} _ {t} [ G _ {t} ] = \frac {1}{n} \sum_ {i \in \mathcal {S}} \partial g _ {i} (\mathbf {w} _ {t}) \partial f _ {i} (u _ {i, t}),
$$

and the second inequality uses the bound of $\mathbb { E } [ \| G _ { t } \| ^ { 2 } ]$ , which follows from the Lipschitz continuity and bounded variance assumptions and is denoted by M.

Combining inequality 29 and 30 yields

$$
\begin{array}{l} \mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}) ] \\ \leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2} + \frac {\bar {\rho} \eta}{n} \sum_ {i \in \mathcal {S}} \bigg [ f _ {i} (g _ {i} (\hat {\mathbf {w}} _ {t})) - f _ {i} (u _ {i, t}) \\ \quad - \partial f _ {i} (u _ {i, t}) ^ {\top} (g _ {i} (\mathbf {w} _ {t}) - u _ {i, t}) + (\frac {\rho_ {g} C _ {f}}{2} + \rho_ {f} C _ {g} ^ {2}) \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \rho_ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} \| ^ {2} \bigg ] \\ = F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2} + \frac {\bar {\rho} \eta}{n} \sum_ {i \in \mathcal {S}} \bigg [ F _ {i} (\hat {\mathbf {w}} _ {t}) - F _ {i} (\mathbf {w} _ {t}) + f _ {i} (g _ {i} (\mathbf {w} _ {t})) - f _ {i} (u _ {i, t}) \\ \quad - \partial f _ {i} (u _ {i, t}) ^ {\top} (g _ {i} (\mathbf {w} _ {t}) - u _ {i, t}) + (\frac {\rho_ {g} C _ {f}}{2} + \rho_ {f} C _ {g} ^ {2}) \|   \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}   \| ^ {2} + \rho_ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t}   \| ^ {2} \bigg ] \end{array}\tag{13}
$$

Due to the $\rho _ { F ^ { - } }$ weak convexity of $F _ { i } ( \mathbf { w } )$ , we have $( \bar { \rho } - \rho _ { F } )$ -strong convexity of $\mathbf { w } \mapsto F _ { i } ( \mathbf { w } ) +$ $\frac { \bar { \rho } } { 2 } \| \mathbf { w } _ { t } - \mathbf { w } \| ^ { 2 }$ . Then it follows

$$
\begin{array}{r l} & F _ {i} (\hat {\mathbf {w}} _ {t}) - F _ {i} (\mathbf {w} _ {t}) = \left[ F _ {i} (\hat {\mathbf {w}} _ {t}) + \frac {\bar {\rho}}{2} \| \mathbf {w} _ {t} - \hat {\mathbf {w}} _ {t} \| ^ {2} \right] - \left[ F _ {i} (\mathbf {w} _ {t}) + \frac {\bar {\rho}}{2} \| \mathbf {w} _ {t} - \mathbf {w} _ {t} \| ^ {2} \right] - \frac {\bar {\rho}}{2} \| \mathbf {w} _ {t} - \hat {\mathbf {w}} _ {t} \| ^ {2} \\ & \qquad \leq (\frac {\rho_ {F}}{2} - \bar {\rho}) \| \mathbf {w} _ {t} - \hat {\mathbf {w}} _ {t} \| ^ {2} \end{array}\tag{14}
$$

Plugging inequality 32 into inequality 31 yields

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}) ] \leq \mathbb {E} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) ] + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2} + \frac {\bar {\rho} \eta}{n} \sum_ {i \in \mathcal {S}} \bigg [ (\frac {\rho_ {F}}{2} - \bar {\rho}) \| \mathbf {w} _ {t} - \hat {\mathbf {w}} _ {t} \| ^ {2}} \\ & {\qquad + f _ {i} (g _ {i} (\mathbf {w} _ {t})) - f _ {i} (u _ {i, t}) - \partial f _ {i} (u _ {i, t}) ^ {\top} (g _ {i} (\mathbf {w} _ {t}) - u _ {i, t})} \\ & {\qquad + (\frac {\rho_ {g} C _ {f}}{2} + \rho_ {f} C _ {g} ^ {2}) \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \rho_ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} \| ^ {2} \bigg ]} \end{array}\tag{15}
$$

Set $\bar { \rho } = \rho _ { F } + \rho _ { g } C _ { f } + 2 \rho _ { f } C _ { g } ^ { 2 }$ . We have

$$
\begin{array}{l} \mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}) ] \leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2} + \frac {\bar {\rho} \eta}{n _ {+}} \sum_ {i \in \mathcal {S}} \bigg [ - \frac {\bar {\rho}}{2} \| \mathbf {w} _ {t} - \hat {\mathbf {w}} _ {t} \| ^ {2} + f _ {i} (g _ {i} (\mathbf {w} _ {t})) - f _ {i} (u _ {i, t}) \\ \qquad - \partial f _ {i} (u _ {i, t}) ^ {\top} (g _ {i} (\mathbf {w} _ {t}) - u _ {i, t}) + \rho_ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} \| ^ {2} \bigg ] \\ \stackrel {(a)} {\leq} F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2} - \frac {\eta}{2} \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} + \frac {\bar {\rho} \eta}{n} \sum_ {i \in \mathcal {S}} \bigg [ f _ {i} (g _ {i} (\mathbf {w} _ {t})) - f _ {i} (u _ {i, t}) \\ \qquad - \partial f _ {i} (u _ {i, t}) ^ {\top} (g _ {i} (\mathbf {w} _ {t}) - u _ {i, t}) + \rho_ {f} \| g _ {i} (\mathbf w _ {t}) - u _ {i, t} \| ^ {2} \bigg ] \end{array}
$$

where inequality (a) follows from Lemma 3.2.

Using the Lipschitz continuity of $f _ { i } ,$ we have

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}) ] \leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2} - \frac {\eta}{2} \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} + \frac {\bar {\rho} \eta}{n} \sum_ {i \in \mathcal {S}} 2 C _ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} \|} \\ & {\qquad + \frac {\bar {\rho} \eta}{n} \sum_ {i \in \mathcal {S}} \rho_ {f} \| g _ {i} (\mathbf {w} _ {t}) - u _ {i, t} \| ^ {2}} \end{array}
$$

By Lemma 4.5, the error bound of the MSVR update gives

$$
\begin{array}{r l} & {\mathbb {E} \bigg [ \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| \bigg ] \leq (1 - \mu) ^ {t} \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| + R _ {1},} \\ & {\mathbb {E} \bigg [ \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} \bigg ] \leq (1 - \mu) ^ {t} \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| ^ {2} + R _ {2},} \end{array}
$$

where

$$
\mu = \frac {B _ {1} \tau}{2 n}, R _ {1} = \frac {2 \tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 n C _ {g} M \eta}{B _ {1} \tau^ {1 / 2}}, R _ {2} = \frac {4 \tau \sigma^ {2}}{B _ {2}} + \frac {1 6 n ^ {2} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau}
$$

Then

$$
\begin{array}{l} \mathbb {E} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}) ] \leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2} - \frac {\eta}{2} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} ] \\ \qquad + 2 C _ {f} \bar {\rho} \eta \left((1 - \mu) ^ {t} \frac {1}{n} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \| + R _ {1}\right) \\ \qquad + C \rho_ {f} \bar {\rho} \eta \left((1 - \mu) ^ {t} \frac {1}{n} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \| ^ {2} + R _ {2}\right) \end{array}\tag{16}
$$

Taking summation from $t = 0$ to $T - 1$ yields

E $\left[ F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { T } ) \right]$

$$
\begin{array}{r l} & {\leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}) + \frac {\eta^ {2} \bar {\rho} M ^ {2} T}{2} - \frac {\eta}{2} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} ]} \\ & {\quad + 2 C _ {f} \bar {\rho} \eta \left(\sum_ {t = 0} ^ {T - 1} (1 - \mu) ^ {t} \frac {1}{n} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \| + R _ {1} T\right)} \\ & {\quad + C \rho_ {f} \bar {\rho} \eta \left((1 - \mu) ^ {t} \frac {1}{n} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \| ^ {2} + R _ {2} T\right)} \\ & {\overset {(a)} {\leq} F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}) + \frac {\eta^ {2} \bar {\rho} M ^ {2} T}{2} - \frac {\eta}{2} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) | ^ {2} ]} \\ & {\quad + \frac {2 C _ {f} \bar {\rho} \eta}{n \mu} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \| + 2 C _ {f} \bar {\rho} \eta R _ {1} T + \frac {\rho_ {f} \bar {\rho} \eta}{n \mu} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \| ^ {2} + 2 \rho_ {f} \bar {\rho} \eta R _ {2} T,} \end{array}
$$

where (a) uses $\textstyle \sum _ { t = 0 } ^ { T - 1 } ( 1 - \mu ) ^ { t } \leq { \frac { 1 } { \mu } }$

(17)

Lower bounding the left-hand-side by min ${ \bf \nabla } _ { \bf w } F ( { \bf w } )$ , we obtain

$$
\begin{array}{r l} & {\frac {1}{T} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} ]} \\ & {\leq \frac {2}{\eta T} \bigg [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}) - \underset {\mathbf {w}} {\min} F (\mathbf {w}) + \frac {\eta^ {2} \bar {\rho} M ^ {2} T}{2} + \frac {2 C _ {f} \bar {\rho} \eta}{n} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \| + 2 C _ {f} \bar {\rho} \eta R _ {1} T} \\ & {\quad + \frac {\rho_ {f} \bar {\rho} \eta}{n} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \| ^ {2} + \rho_ {f} \bar {\rho} \eta R _ {2} T \bigg ]} \\ & {\leq \frac {2 \Delta}{\eta T} + \eta \bar {\rho} M ^ {2} + \frac {4 C _ {f} \bar {\rho}}{\mu T n} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \| + 4 C _ {f} \bar {\rho} R _ {1} + \frac {2 \rho_ {f} \bar {\rho}}{\mu T n} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \| ^ {2} + 2 \rho_ {f} \bar {\rho} R _ {2}} \\ & {\leq \frac {C}{T} (\frac {1}{\eta} + \frac {1}{\mu}) + C (\eta + R _ {1} + R _ {2})} \end{array}
$$

$$
F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}, \mathbf {s} _ {0}, s _ {0} ^ {\prime}) - \min _ {\mathbf {w}, \mathbf {s}, s ^ {\prime}} F (\mathbf {w}, \mathbf {s}, s ^ {\prime}) \leq \Delta
$$

$$
C = \max \{8 \Delta , 1 2 \bar {\rho} M ^ {2}, \frac {1 6 C _ {f} \bar {\rho}}{n} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \|, \frac {8 \rho_ {f} \bar {\rho}}{n} \sum_ {i \in \mathcal {S}} \| g _ {i} (\mathbf {w} _ {0}) - u _ {i, 0} \| ^ {2}, 1 6 C _ {f} \bar {\rho}, 8 \rho_ {f} \bar {\rho} \}.
$$

Thus

$$
\begin{array}{l} \frac {1}{T} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} ] \\ \leq \frac {C}{T} (\frac {1}{\eta} + \frac {2 n}{B _ {1} \tau}) + C (\eta + \frac {2 \tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 n C _ {g} M \eta}{B _ {1} \tau^ {1 / 2}} + \frac {4 \tau \sigma^ {2}}{B _ {2}} + \frac {1 6 n ^ {2} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau}) \\ = \mathcal {O} \left(\frac {1}{T} (\frac {1}{\eta} + \frac {n}{B _ {1} \tau}) + (\eta + \frac {\tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {n \eta}{B _ {1} \tau^ {1 / 2}} + \frac {\tau \sigma^ {2}}{B _ {2}} + \frac {n ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau})\right) \end{array}
$$

Setting

$$
\tau = \mathcal {O} (B _ {2} \epsilon^ {4}), \quad \eta = \mathcal {O} \left(\frac {B _ {1} B _ {2} ^ {1 / 2} \epsilon^ {4}}{n}\right)
$$

To reach an ϵ-stationary point, we need

$$
T = \mathcal {O} \left(\frac {n}{B _ {1} B _ {2} ^ {1 / 2} \epsilon^ {6}}\right)
$$

## A.2 Proof of Theorem 4.7

A formal statement in given below.

Theorem A.2. Under Assumption 4.3, with $\begin{array} { r } { \gamma _ { 1 } \ = \ \frac { n _ { 1 } n _ { 2 } - B _ { 1 } B _ { 2 } } { B _ { 1 } B _ { 2 } ( 1 - \tau _ { 1 } ) } + ( 1 - \tau _ { 1 } ) , \ \gamma _ { 2 } \ = \ \frac { n _ { 1 } - B _ { 1 } } { B _ { 1 } ( 1 - \tau _ { 2 } ) } \ + \ } \end{array}$ $\begin{array} { r l r l r l r l r l } { ( 1 - \mathrm {  ~ \tau ~ } _ { 2 } ) , \mathrm {  ~ \tau ~ } _ { 1 } } & { = } & { \mathcal { O } \left( \operatorname* { m i n } \{ B _ { 3 } , \frac { B _ { 1 } ^ { 1 / 2 } n _ { 2 } ^ { 1 / 2 } } { n _ { 1 } ^ { 1 / 2 } } \} \epsilon ^ { 4 } \right) } & { \leq } & { \frac { 1 } { 2 } , \mathrm {  ~ \tau ~ } _ { 2 } } & { = } & { \mathcal { O } ( B _ { 2 } \epsilon ^ { 4 } ) } & { \leq } & { \frac { 1 } { 2 } , \eta } & { = } & { \mathcal { O } ( \epsilon ^ { 4 } ) } \end{array}$ $\begin{array} { r } { \mathcal { O } \left( \operatorname* { m i n } \left\{ B _ { 3 } ^ { 1 / 2 } , \frac { B _ { 1 } ^ { 1 / 4 } n _ { 2 } ^ { 1 / 4 } } { n _ { 1 } ^ { 1 / 4 } } , \frac { B _ { 1 } ^ { 1 / 2 } n _ { 2 } ^ { 1 / 2 } } { n _ { 1 } ^ { 1 / 2 } } \right\} \frac { B _ { 1 } B _ { 2 } } { n _ { 1 } n _ { 2 } } \epsilon ^ { 4 } \right) } \end{array}$ , and $\bar { \rho } = \rho _ { F } + 4 \rho _ { f } C _ { g } ^ { 2 } + 2 \rho _ { g } C _ { f } C _ { h } ^ { 2 } + C _ { f } C _ { g } L _ { h }$ Algorithm 2 converges to an ϵ-stationary point of the Moreau envelope $F _ { 1 / \bar { \rho } }$ in $T =$ $\begin{array} { r } { \mathcal { O } \left( \operatorname* { m a x } \left\{ \frac { 1 } { B _ { 3 } ^ { 1 / 2 } } , \frac { n _ { 1 } ^ { 1 / 4 } } { B _ { 1 } ^ { 1 / 4 } n _ { 2 } ^ { 1 / 4 } } , \frac { n _ { 1 } ^ { 1 / 2 } } { B _ { 1 } ^ { 1 / 2 } n _ { 2 } ^ { 1 / 2 } } \right\} \frac { n _ { 1 } n _ { 2 } } { B _ { 1 } B _ { 2 } } \epsilon ^ { - 6 } \right) } \end{array}$ iterations.

We first define constant $\begin{array} { r } { M ^ { 2 } \geq \operatorname* { m a x } \{ \frac { 3 C _ { f } ^ { 2 } C _ { g } ^ { 2 } \sigma ^ { 2 } } { B _ { 3 } } + \frac { 3 C _ { f } ^ { 2 } C _ { g } ^ { 2 } C _ { h } ^ { 2 } } { B _ { 2 } } + \frac { 3 C _ { f } ^ { 2 } C _ { g } ^ { 2 } C _ { h } ^ { 2 } } { B _ { 1 } } , \tilde { C } _ { h } ^ { 2 } + \sigma ^ { 2 } \} } \end{array}$ so that $\mathbb { E } _ { t } [ \left. G _ { t } \right. ^ { 2 } ] \leq$ $M ^ { 2 }$ and $\| v _ { i , j , t } \| ^ { 2 } \leq M ^ { 2 }$ for all $i \in \mathcal { S } _ { 1 } , j \in \mathcal { S } _ { 2 }$ and t. Then to prove Theorem A.2, we need the following Lemmas.

Lemma A.3. Consider MSVR updatefor v. Assume $h _ { i , j } ( \mathbf { w } ; \boldsymbol { \xi } )$ is $C _ { h }$ -Lipshitzfor all $( i , j ) \in S _ { 1 } \times S _ { 2 }$ , and $\mathbb { E } [ \| G _ { t } \| ^ { 2 } ] \le M ^ { 2 }$ . With $\begin{array} { r } { \gamma _ { 1 } = \frac { n _ { 1 } n _ { 2 } - B _ { 1 } B _ { 2 } } { B _ { 1 } B _ { 2 } ( 1 - \tau _ { 1 } ) } + ( 1 - \tau _ { 1 } ) } \end{array}$ , and $\tau _ { 1 } \leq \frac { 1 } { 2 }$ , we have

$$
\begin{array}{r l} & {\mathbb {E} \bigg [ \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} \| v _ {i, j, t + 1} - h _ {i, j} (\mathbf {w} _ {t + 1}) \| \bigg ]} \\ & {\leq (1 - \frac {B _ {1} B _ {2} \tau_ {1}}{2 n _ {1} n _ {2}}) ^ {t + 1} \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} \| v _ {i, j, 0} - h _ {i, j} (\mathbf {w} _ {0}) \| + \frac {2 \tau_ {1} ^ {1 / 2} \sigma}{B _ {3} ^ {1 / 2}} + \frac {4 n _ {1} n _ {2} C _ {h} M \eta}{B _ {1} B _ {2} \tau_ {1} ^ {1 / 2}}} \\ & {\mathbb {E} \bigg [ \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} \| v _ {i, j, t + 1} - h _ {i, j} (\mathbf {w} _ {t + 1}) \| ^ {2} \bigg ]} \\ & {\leq (1 - \frac {B _ {1} B _ {2} \tau_ {1}}{2 n _ {1} n _ {2}}) ^ {2 (t + 1)} \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} \| v _ {i, j, 0} - h _ {i, j} (\mathbf {w} _ {0}) \| ^ {2} + \frac {4 \tau_ {1} \sigma^ {2}}{B _ {3}} + \frac {1 6 n _ {1} ^ {2} n _ {2} ^ {2} C _ {h} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} B _ {2} ^ {2} \tau_ {1}}} \end{array}
$$

Lemma A.4. Consider MSVR update for u. Assume $g _ { i } ( \cdot )$ is $C _ { g } – L i p s h i t z$ for all $i \in S _ { 1 }$ <sub>1</sub>. With $\begin{array} { r } { \gamma _ { 2 } = \frac { n _ { + } - B _ { 1 } } { B _ { 1 } ( 1 - \tau _ { 2 } ) } + ( 1 - \tau _ { 2 } ) } \end{array}$ and $\begin{array} { r } { \tau _ { 2 } \leq \frac { 1 } { 2 } , } \end{array}$ , we have

$$
\begin{array}{l} \mathbb {E} \left[ \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, t + 1}) \| \right] \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {1}}) ^ {t + 1} \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, 0}) \| + \frac {2 \tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {C _ {2} n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} \tau_ {1}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}} + \frac {C _ {2} n _ {1} ^ {3 / 2} n _ {2} ^ {1 / 2} \eta}{B _ {1} ^ {3 / 2} B _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}} \end{array}
$$

where $C _ { 2 }$ is a constant defined in the proof.

Proof of Theorem A.2. Consider the change in the Moreau envelope:

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}) ] = \mathbb {E} _ {t} \left[ \underset {\tilde {\mathbf {w}}} {\min} F (\tilde {\mathbf {w}}) + \frac {\bar {\rho}}{2} \| \tilde {\mathbf {w}} - \mathbf {w} _ {t + 1} \| ^ {2} \right]} \\ & {\qquad \leq \mathbb {E} _ {t} \left[ F (\hat {\mathbf {w}} _ {t}) + \frac {\bar {\rho}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t + 1} \| ^ {2} \right]} \\ & {\qquad = F (\hat {\mathbf {w}} _ {t}) + \mathbb {E} _ {t} \left[ \frac {\bar {\rho}}{2} \| \hat {\mathbf {w}} _ {t} - (\mathbf {w} _ {t} - \eta G _ {t}) \| ^ {2} \right]} \\ & {\qquad \leq F (\hat {\mathbf {w}} _ {t}) + \frac {\bar {\rho}}{2} \left(\| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2}\right) + \bar {\rho} \mathbb {E} _ {t} [ \eta \langle \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}, G _ {t} \rangle ] + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2}} \\ & {\qquad = F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) + \bar {\rho} \mathbb {E} _ {t} [ \eta \langle \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}, G _ {t} \rangle ] + \frac {\eta^ {2} \bar {\rho} M ^ {2}}{2}} \end{array}\tag{18}
$$

Note that

$$
\mathbb {E} _ {t} [ G _ {t} ] = \frac {1}{n _ {1}} \sum_ {i = 1} ^ {n _ {1}} \left[ \frac {1}{n _ {2}} \sum_ {j = 1} ^ {n _ {2}} \nabla h _ {i, j} (\mathbf {w} _ {t}) \partial g _ {i} (v _ {i, j, t}) \right] \partial f _ {i} (u _ {i, t}),
$$

and the second inequality uses the bound of $\mathbb { E } [ \| G _ { t } \| ^ { 2 } ] ,$ , which follows from the Lipschitz continuity and bounded variance assumptions and is denoted by M.

Define $\hat { \mathbf { w } } _ { t } : = \mathrm { p r o x } _ { F / \bar { \rho } } \big ( \mathbf { w } _ { t } \big )$ . For a given $i \in \{ 1 , \ldots , m \}$ , we have

$$
\begin{array} { l } \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } f _ { i } ( \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( h _ { i , j } ( \hat { \mathbf { w } } _ { t } ) ) ) - \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } f _ { i } ( u _ { i , t } ) \\ \overset { ( a ) } { \geq } \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \partial f _ { i } ( u _ { i , t } ) ^ { \top } ( \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( h _ { i , j } ( \hat { \mathbf { w } } _ { t } ) ) - u _ { i , t } ) - \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { \rho _ { f } } { 2 } \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( h _ { i , j } ( \hat { \mathbf { w } } _ { t } ) ) - u _ { i , t } \| ^ { 2 } \\ \geq \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \partial f _ { i } ( u _ { i , t } ) ^ { \top } ( \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( h _ { i , j } ( \hat { \mathbf {w } } _ { t } ) ) - u _ { i , t } ) \\ - \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \rho _ { f } \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( h _ { i , j } ( \hat { \mathbf { w } } _ { t } ) ) - \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t}) \| ^ { 2 } - \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \rho _ { f } \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t} ) - u _ { i , t } \| \\ \geq \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \partial f _ { i } ( u _ { i , t } ) ^ { \top } ( \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( h _ { i , j } ( \hat { {\mathbf w } } _ { t} ) ) - u _ { i , t} ) - \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \rho _ { f} C _ { g } ^ { 2} \| h _ { i , j } ( \hat { {\mathbf w} } _ { t} ) - v _ { i , j , t} \| ^ { 2} \\ - \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \rho _ { f } \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t}) - u _ { i , t} \| ^ { 2 } \\ \overset { ( b ) } {\geq} \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \partial f _ { i } ( u _ { i , t }) ^ { \top } [ \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t}) - u _ { i , t } + \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \partial g _ { i } ( v _ { i , j , t}) ^ { \top } ( h _ { i , j} ( \hat {\mathbf w} _ { t} ) - v _ { i , j , t} ) \\ - \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \frac {\rho _ { g }}{ 2} \| h _ { i , j} ( \hat {\mathbf w} _ { t} ) - v _ { i , j , t} \| ^ { 2} ] - \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } 2 \rho _ { f} C _ { g } ^ { 2} \| h _ { i , j} (\mathbf w _ { t}) - v _ { i , j , t} \| ^ { 2} \\ - 2 \rho _ { f} C _ { g } ^ { 2} \| \hat {\mathbf w} _ { t} - \mathbf w _ { t} \| ^ { 2} - \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \rho _ { f } \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t}) - u _ { i , t} \| ^ { 2} \\ \overset {( c )} {\geq} \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \partial f _ { i } ( u _ { i , t}) ^ {\top} [ \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t}) - u _ { i , t} ] \\ + \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { 1 } { n _ { 2 }} \sum _ { j \in S _ { 2 }} [ \underbrace {\langle d f _ {{i}} ( u {{i} , t}) ^ {\top} d g {{i}} ( v {{i} , j , t}) ^ {\top}} ] [ h {i}, {{\hat {\mathbf w}}} ] A {_ 1} \\ - \frac {}{} [ n ] \sum_ {{i > S}} \sum_ {{i <  }} \sum_ {{j > S}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sum_ {{j <  }}} {\sigma_ {{f}}} ] [ h {i}, {{\hat {\mathbf w}}} ] - v {i}, {{\hat {\mathbf w}}} ] A {_ 3} \\ - 2 p r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o r c o l e m a x e s e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e b e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l y e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l z e a l s e s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s s   | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
| + \frac {}{} [ n ] \sum_ {{i > S}} \sum_ {{i <  }} \sum_ {{i <  }} \sum_ {{i <  }} \sum_ {{i <  }} \sum_ {{i <  }} \sum_ {{i <  }} \sum_ {{i <  }} \sum_ {{i <  }} {\sum_ {{i <  }} {\sum_ {{i <  }} {\sum_ {{i <  }} {\sum_ {{i <  }} {\sum_ {{i <  }} {\sum_ {{i <  }} {\sum_ {{i <  }} {\tau}}}}}}}} ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ], [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ] [ n ][ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ N ], [ M ], [ M ], {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M }, {[ M },[[ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [[ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [ M ] , [{M ] , {[M] }} ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M] ;[M]\( ^a,b,c,d,f,g,h,i,j,k,l,m,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,\\ ^c,d,f,g,h,i,j,k,l,m,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,n,\( ^c,d,f,g,h,i,j,k,l,m,m,n,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,m,mm,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,q,p,s,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,t,|t| = q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q :|t| = Q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q / q /q/ p :|t| = Q / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p /p :|t| = Q / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p / p .\\ +\frac{1}{n_{1}}\sum_\substack{i,j,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k,l,k;l}\left(\left|\partial f_{i}(u_{i,j})^{\top}\right|\left|\partial f_{i}(u_{i,j})^{\top}\right|\left|\partial f_{i}(u_{i,j})^{\top}\right|\left|\partial f_{i}(u_{i,j})^{\top}\right|\left|\partial f_{i}(u_{i,j})^{\top}\right|\left|\partial f_{i}(u_{i,j})^{\top}\right|\left|\partial f_{i}(u_{j,j})^{\top}\right|\left|\partial f_{i}(u_{j,j})^{\top}\right|\left|\partial f_{i}(u_{j,j})^{\top}\right|\left|\partial f_{i}(u_{j,j})^{\top}\right|\left|\partial f_{i}(u_{j,j})^{\top}\right|\left|\partial f_{i}(u_{j,j})^{\top}\right|\left|v_i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,a,b,c,d,f,g,h,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,l,i,j,k,|p| = Q[p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|p|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|q:|
+Q[p|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|m\tag{19}
$$

where (a) follows from the convexity of $f _ { i } , ( \mathsf { b } )$ uses the assumption that $f _ { i } ( \cdot )$ is non-decreasing and $g _ { i }$ is weak convex, (c) is due to $0 \leq \mathrm { \dot { \partial } } f _ { i } ( u _ { i , t } ) \leq C _ { f }$

The $L _ { h }$ -smoothness assumption of $h _ { i , j } ( \mathbf { w } )$ (or weakly-convexity of $h _ { i , j } ( \mathbf { w } )$ , then only the second inequality holds) for all i, w implies

$$
\begin{array}{r l} & h _ {i, j} (\hat {\mathbf {w}} _ {t}) \leq h _ {i, j} (\mathbf {w} _ {t}) + \nabla h _ {i, j} (\mathbf {w} _ {t}) ^ {\top} (\hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}) + \frac {L _ {h}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2}, \\ & h _ {i, j} (\hat {\mathbf {w}} _ {t}) \geq h _ {i, j} (\mathbf {w} _ {t}) + \nabla h _ {i, j} (\mathbf {w} _ {t}) ^ {\top} (\hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}) - \frac {L _ {h}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2}. \end{array}\tag{20}
$$

We first assume that $g _ { i } ( \cdot )$ is non-increasing. Since $\partial f _ { i } ( u _ { i , t } ) \geq 0$ and $\partial g _ { i } ( v _ { i , j , t } ) \leq 0$ , we bound $A _ { 1 }$ as following

$$
\begin{array}{l} A _ {1} = \partial f _ {i} (u _ {i, t}) \partial^ {\top} g _ {i} (v _ {i, j, t}) ^ {\top} (h _ {i, j} (\hat {\mathbf {w}} _ {t}) - v _ {i, j, t}) \\ \stackrel {(a)} {\geq} \langle \partial f _ {i} (u _ {i, t}) ^ {\top} \partial g _ {i} (v _ {i, j, t}) ^ {\top} (h _ {i, j} (\mathbf {w} _ {t}) - v _ {i, j, t}) + \partial f _ {i} (u _ {i, t}) ^ {\top} \partial g _ {i} (v _ {i, j, t}) ^ {\top} \nabla h _ {i, j} (\mathbf {w} _ {t}) ^ {\top} (\hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}) \\ \quad + \partial f _ {i} (u _ {i, t}) ^ {\top} \partial g _ {i} (v _ {i, j, t}) ^ {\top} \frac {L _ {h}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} \rangle \\ \stackrel {(b)} {\geq} - C _ {f} C _ {g} \| h _ {i, j} (\mathbf {w} _ {t}) - v _ {i, j, t} \| + \partial f _ {i} (u _ {i, t}) ^ {\top} \partial g _ {i} (v _ {i, j, t}) ^ {\top} \nabla h _ {i, j} (\mathbf {w} _ {t}) ^ {\top} (\hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}) \\ \quad - \frac {C _ {f} C _ {g} L _ {h}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} \end{array}\tag{21}
$$

where inequality (a) follows from the first inequality in (20), (b) follows from the Lipschitz continuity and monotone assumptions on $f _ { i } , g _ { i } , h _ { i , j }$ . On the other hand, if we assume $g _ { i } ( \cdot )$ is non-decreasing, we may use the second inequality in (20) and obtain the same result as (21). Now plugging the new formulation of $A _ { 1 }$ back to inequality 19 yields

$$
\begin{array}{l} \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} f _ {i} (\frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (h _ {i, j} (\hat {\mathbf {w}} _ {t}))) - \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} f _ {i} (u _ {i, t}) \\ \geq \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \partial f _ {i} (u _ {i, t}) ^ {\top} \left[ \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, t}) - u _ {i, t} \right] + \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} - C _ {f} C _ {g} \| h _ {i, j} (\mathbf {w} _ {t}) - v _ {i, j, t} \| \\ + \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} \partial f _ {i} (u _ {i, t}) ^ {\top} \partial g _ {i} (v _ {i, j, t}) ^ {\top} \nabla h _ {i, j} (\mathbf {w} _ {t}) ^ {\top} (\hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}) - \frac {C _ {f} C _ {g} L _ {h}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} \\ - \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} (2 \rho_ {f} C _ {g} ^ {2} + \rho_ {g} C _ {f}) \| h _ {i, j} (\mathbf {w} _ {t}) - v _ {i, j, t} \| ^ {2} \\ - (2 \rho_ {f} C _ {g} ^ {2} + \rho_ {g} C _ {f} C _ {h} ^ {2}) \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} - \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \rho_ {f} \left\| \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, t}) - u _ {i, t} \right\| ^ {2} \\ \geq \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} - C _ {f} \left\| \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, t}) - u _ {i, t} \right\| + \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} - C _ {f} C _ {g} \| h _ {i, j} (\mathbf {w} _ {t}) - v _ {i, j, t} \| \\ + \langle \mathbb E _ {t} [ G _ {t} ], \hat {\mathbf w} _ {t} - \mathbf w _ {t} \rangle - \frac 1{n _ {1}} \sum_ {i \in S _ {1}} \frac 1{n _ {2}} \sum_ {j \in S _ {2}} (2 \rho_ {f} C _ {g} ^ {2} + \rho_ {g} C _ {f}) \| h _ {i, j} (\mathbf w _ {t}) - v _ {i, j, t} \| ^ {2} \\ - (2 \rho_ {f} C _ {g} ^ {2} + \rho_ {g} C _ {f} C _ {h} ^ {2} + \frac C{} + \frac C{} + \frac C{} + 2) \| \hat {\mathbf w} _ {t} - \mathbf w _ {t} \| ^ {2} - \frac 1{n _ {1}} \sum_ {{i \in S_{1}}} \rho_ {{f}} {\left\| {\frac 1{n _ {2}}} {\sum_ {{j \in S_{2}}} g _ {{i}} (v _ {{i}, j, t}) - u _ {{i}, t}} \right\| ^ {2}}. \end{array}
$$

It follows

$$
\begin{array}{l} \langle \mathbb {E} _ {t} [ G _ {t} ], \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \rangle \\ \leq \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} f _ {i} (\frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (h _ {i, j} (\hat {\mathbf {w}} _ {t}))) - \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} f _ {i} (u _ {i, t}) + \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} C _ {f} \bigg \| \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, t}) - u _ {i, t} \bigg \| \\ + \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} C _ {f} C _ {g} \| h _ {i, j} (\mathbf {w} _ {t}) - v _ {i, j, t} \| + \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} (2 \rho_ {f} C _ {g} ^ {2} + \rho_ {g} C _ {f}) \| h _ {i, j} (\mathbf {w} _ {t}) - v _ {i, j, t} \| ^ {2} \\ + (2 \rho_ {f} C _ {g} ^ {2} + \rho_ {g} C _ {f} C _ {h} ^ {2} + \frac {C _ {f} C _ {g} L _ {h}}{2}) \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \rho_ {f} \bigg \| \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, t}) - u _ {i, t} \bigg \| ^ {2} \end{array}\tag{22}
$$

Combining inequality 22 and 18 yields

$$
\begin{array} { r l } &  \mathbb { E } _ { t } [ F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t + 1 } ) ] \\ & { \leq F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } ) + \frac { \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } + \bar { \rho } \eta \biggl \{ \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \biggl [ f _ { i } ( \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( h _ { i , j } ( \hat { \mathbf { w } } _ { t } ) ) ) - f _ { i } ( u _ { i , t } ) } \\ & { \quad + C _ { f } \biggl \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t } ) - u _ { i , t } \biggr \| + \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } C _ { f } C _ { g } \| h _ { i , j } ( \mathbf { w } _ { t } ) - v _ { i , j , t } \| ^ { 2 } } \\ & { \quad + \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } ( 2 \rho _ { f } C _ { g } ^ { 2 } + \rho _ { g } C _ { f } ) \| h _ { i , j } ( \mathbf { w } _ { t } ) - v _ { i , j , t } \| ^ { 2 } } \\ &  \quad + ( 2 \rho _ { f } C _ { g } ^ { 2 } + \rho _ { g } C _ { f } C _ { h } ^ { 2 } + \frac { C _ { f } C _ { g } L _ { h } } { 2 } ) \| \hat { \mathbf { w } } _ { t } - \mathbf { w } _ { t } \| ^ { 2 } + \rho _ { f } \biggl \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t } ) - u _ { i , t } \biggr \| ^ { 2 } \biggr ] \biggr \} \\ &  \leq F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } ) + \frac { \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } + \bar {\rho} \eta \biggl \{ \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \biggl [ F _ { i } ( \hat { \mathbf { w } } _ { t } ) - F _ { i } ( \mathbf { w } _ { t } ) + F _ { i } ( \mathbf { w } _ { t } ) - f _ { i } ( \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t} ) ) - f _ { i } ( v _ { i , t }, t ) - v _ { i , t }, t ) - v _ { i , t }, t ) - v _ { i , t }, t ) - v _ { i , t }, t ) - v _ { i , t }, t ) - v _ { i , t }, t ) - v _ { i , t }, t ) - v _ { i , t }, t ) - v _ { i , t }, t ) - v _ { i , t }, t ) = c . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . c m a x : c o n s e d e r e f f o r e q u a l l e a n d e r e f f o r e q u a l l e a n d e r e f f o r e q u a l l e a n d e r e f f o r e q u a l l e a n d e r e f f o r e q u a l l e a n d e r e f f o r e q u a l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e b a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l l e a n d e r e f f o r e q u a l l | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
$$

where (a) follows from the Lipschitz continuity of $f _ { i } , g _ { i } , h _ { i , j }$

Due to the $\rho _ { F }$ -weak convexity of $F _ { i } ( \mathbf { w } )$ , we have $( \bar { \rho } - \rho _ { F } )$ -strong convexity of $\mathbf { w } \mapsto F _ { i } ( \mathbf { w } ) +$ $\frac { \bar { \rho } } { 2 } \| \mathbf { w } _ { t } - \mathbf { w } \| ^ { 2 }$ . Then it follows

$$
\begin{array}{l} F _ {i} (\hat {\mathbf {w}} _ {t}) - F _ {i} (\mathbf {w} _ {t}) = \left[ F _ {i} (\hat {\mathbf {w}} _ {t}) + \frac {\bar {\rho}}{2} \| \mathbf {w} _ {t} - \hat {\mathbf {w}} _ {t} \| ^ {2} \right] - \left[ F _ {i} (\mathbf {w} _ {t}) + \frac {\bar {\rho}}{2} \| \mathbf {w} _ {t} - \mathbf {w} _ {t} \| ^ {2} \right] - \frac {\bar {\rho}}{2} \| \mathbf {w} _ {t} - \hat {\mathbf {w}} _ {t} \| ^ {2} \\ \leq (\frac {\rho_ {F}}{2} - \bar {\rho}) \| \mathbf {w} _ {t} - \hat {\mathbf {w}} _ {t} \| ^ {2} \end{array}\tag{23}
$$

Plugging inequality 23 back into A.2, we obtain

$$
\begin{array} { l } \mathbb { E } _ { t } [ F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t + 1 } ) ] \\ \leq F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } ) + \frac { \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } + \bar { \rho } \eta \biggl \{ \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \biggl [ ( \frac { \rho _ { F } } { 2 } - \bar { \rho } ) \| \mathbf { w } _ { t } - \hat { \mathbf { w } } _ { t } \| ^ { 2 } + 2 C _ { f } \biggr \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t } ) - u _ { i , t } \biggr \| \\ + \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } 2 C _ { f } C _ { g } \| h _ { i , j } ( \mathbf { w } _ { t } ) - v _ { i , j , t } \| + \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } ( 2 \rho _ { f } C _ { g } ^ { 2 } + \rho _ { g } C _ { f } ) \| h _ { i , j } ( \mathbf { w } _ { t } ) - v _ { i , j , t } \| ^ { 2 } \\ + ( 2 \rho _ { f } C _ { g } ^ { 2 } + \rho _ { g } C _ { f } C _ { h } ^ { 2 } + \frac { C _ { f } C _ { g } L _ { h } } { 2 } ) \| \hat { \mathbf { w } } _ { t } - \mathbf { w } _ { t } \| ^ { 2 } + \rho _ { f } \biggr \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t } ) - u _ { i , t } \biggr \| ^ { 2 } \biggr ] \biggr \} \\ \stackrel { ( a ) } { \leq } F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } ) + \frac { \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } + \bar { \rho } \eta \biggl \{ \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \biggl [ - \frac { \bar { \rho } } { 2 } \| \mathbf { w } _ { t } - \hat { \mathbf { w } } _ { t } \| ^ { 2 } + C _ { 1 } \biggr \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t } ) - u _ { i , t } \biggr \| \\ + \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } C _ { 1 } \| h _ { i , j } ( \mathbf { w } _ { t } ) - v _ { i , j , t } \| + \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } C _ { 1 } \| h _ { i , j } ( \mathbf { w } _ { t } ) - v _ { i , j , t } \| ^ { 2} \\ + C _ { 1 } \biggl \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t}) - u _ { i , t } \biggr \| ^ { 2 } \biggr ] \biggr \} \\ \stackrel {( b )} = F _ { 1 / \bar {\rho} } ( \mathbf { w } _ { t } ) + \frac { \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } - \frac { \eta}{ 2} \| \nabla F _ { 1 / \bar {\rho} } ( \mathbf { w } _ { t} ) \| ^ { 2 } + C _ { 1 } \bar {\rho} \eta \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \biggl \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t}) - u _ { i , t } \biggr \| \\ + C _ { 1 } \bar {\rho} \eta \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \| h _ { i , j } ( \mathbf { w } _ { t} ) - v _ { i , j , t} \| + C _ { 1 } \bar {\rho} \eta \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \| h _ { i , j } ( \mathbf { w } _ { t} ) - v _ { i , j , t } \| ^ { 2} \\ + C _ { 1 } \bar {\rho} \eta \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \biggl \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t}) - u _ { i , t} \biggr \| ^ { 2} \\ \end{array}
$$

where in inequality (a) we use $\bar { \rho } ~ = ~ \rho _ { F } + 4 \rho _ { f } C _ { g } ^ { 2 } + 2 \rho _ { g } C _ { f } C _ { h } ^ { 2 } + C _ { f } C _ { g } L _ { h }$ and $\begin{array} { r l } { C _ { 1 } } & { { } = } \end{array}$ max $\{ 2 C _ { f } C _ { g } , 2 C _ { f } , ( 2 \rho _ { f } C _ { g } ^ { 2 } + \rho _ { g } C _ { f } ) , \rho _ { f } \}$ , and equality (b) uses Lemma 3.2.

With general error bounds

$$
\begin{array} { l } \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \mathbb { E } [ \| h _ { i , j } ( \mathbf { w } _ { t } ) - v _ { i , j , t } \| ] \leq ( 1 - \mu _ { 1 } ) ^ { t } \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \| h _ { i , j } ( \mathbf { w } _ { 0 } ) - v _ { i , j , 0 } \| + R _ { 1 } , \\ \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \mathbb { E } [ \| h _ { i , j } ( \mathbf { w } _ { t } ) - v _ { i , j , t } \| ^ { 2 } ] \leq ( 1 - \mu _ { 1 } ) ^ { t } \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \| h _ { i , j } ( \mathbf { w } _ { 0 } ) - v_{ i , j , 0 } \| ^ { 2 } + R _ { 2 } , \\ \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \mathbb { E } \bigg [ \bigg \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t } ) - u _ { i , t } \bigg \| \bigg ] \leq ( 1 - \mu _ { 2 } ) ^ { t } \frac { 1 } { n _ { + } } \sum _ { i \in S _ { + } } \bigg \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , 0 } ) - u _ { i , 0 } \bigg \| + R _ { 3 } , \\ \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \mathbb { E } \bigg [ \bigg \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , t } ) - u _ { i , t } \bigm \| ^ { 2 } \bigg ] \leq ( 1 - \mu _ { 2 } ) ^ { t } \frac { 1 } { n _ { + } } \sum _ { i \in S _ { + } } \bigg \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , 0 } ) -u _ { i , 0 } \bigg \| ^ { 2 } + R _ { 4 } , \\ \textbf{we have}\\ \mathbb { E } [ F _ { 1 / \bar {\rho} } ( \mathbf { w } _ { t + 1 } ) ] \\ \leq \mathbb { E } [ F _ { 1 / \bar {\rho} } ( \mathbf { w } _ { t } ) ] + \frac { \eta ^ { 2 } \bar {\rho} M ^ { 2 } } { 2 } - \frac { \eta}{ 2} \mathbb { E } [ \| \nabla F _ { 1 / \bar {\rho} } ( \mathbf { w } _ { t} ) \| ^ { 2 } ] + C _ { 1 } \bar {\rho} \eta ( 1 - \mu _ { m i n} ) ^ { t } \bigg [ \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \bigg \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , 0} ) - u _ { i , 0} \bigg \| \\ + \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \bigg \| \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } g _ { i } ( v _ { i , j , 0} ) - u _ { i , 0} \bigg \| ^ { 2 } + \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \| h _ { i , j } ( \mathbf w ) - v _ { i , j , 0} \| \\ + \frac { 1 } { n _ { 1 } } \sum _ { i \in S _ { 1 } } \frac { 1 } { n _ { 2 } } \sum _ { j \in S _ { 2 } } \| h _ { i , j} ( \mathbf w ) - v _ { i , j , 0} \| ^ { 2} \bigg ] + C _ { 1 } \bar {\rho} \eta ( R _ { 1 } + R _ { 2 } + R _ { 3 } + R _ { 4 }) , \\ w h e r e ~ \mu _ { m i n} = m i n   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |   | |    . \\ \end{array}
$$

Taking summation from $t = 0$ to $T - 1$ yields

$$
\begin{array}{l} \leq \mathbb {E} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}) ] + \frac {\eta^ {2} \bar {\rho} M ^ {2} T}{2} - \frac {\eta}{2} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} ] + C _ {1} \bar {\rho} \eta \sum_ {t = 0} ^ {T - 1} (1 - \mu_ {m i n}) ^ {t} \Delta_ {0} \\ \quad + T C _ {1} \bar {\rho} \eta (R _ {1} + R _ {2} + R _ {3} + R _ {4}) \\ \leq \mathbb {E} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}) ] + \frac {\eta^ {2} \bar {\rho} M ^ {2} T}{2} - \frac {\eta}{2} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}}, (\mathbf {w} _ {t}) \| ^ {2} ] + \frac {C _ {1} \bar {\rho} \eta \Delta_ {0}}{\mu_ {m i n}} + T C _ {1} \bar {\rho} \eta (R _ {1} + R _ {2} + R _ {3} + R _ {4}) \end{array}
$$

where we use $\begin{array} { r } { \sum _ { t = 0 } ^ { T - 1 } ( 1 - \mu _ { m i n } ) ^ { t } \leq \frac { 1 } { \mu _ { m i n } } } \end{array}$ and define constant $\Delta _ { 0 }$ such that

$$
\begin{array}{r l} & {\left[ \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \left\| \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, 0}) - u _ {i, 0} \right\| + \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \left\| \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, 0}) - u _ {i, 0} \right\| ^ {2} \right.} \\ & {\left. + \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} \| h _ {i, j} (\mathbf {w} _ {0}) - v _ {i, j, 0} \| + \frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} \| h _ {i, j} (\mathbf {w} _ {0}) - v _ {i, j, 0} \| ^ {2} \right] \leq \Delta_ {0}.} \end{array}
$$

Then it follows

$$
\begin{array}{l} \frac {1}{T} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} ] \\ \leq \frac {2}{\eta T} \bigg [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}) - \mathbb {E} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {T}) ] + \frac {\eta^ {2} \bar {\rho} M ^ {2} T}{2} + \frac {C _ {1} \bar {\rho} \eta \Delta_ {0}}{\mu_ {m i n}} + T C _ {1} \bar {\rho} \eta (R _ {1} + R _ {2} + R _ {3} + R _ {4}) \bigg ] \\ \leq \frac {2 \Delta}{\eta T} + \eta \bar {\rho} M ^ {2} + \frac {2 C _ {1} \bar {\rho} \Delta_ {0}}{\mu_ {m i n} T} + 2 C _ {1} \bar {\rho} (R _ {1} + R _ {2} + R _ {3}) \\ = \mathcal {O} (\frac {1}{T} (\frac {1}{\eta} + \frac {1}{\mu_ {m i n}}) + \eta + R _ {1} + R _ {2} + R _ {3} + R _ {4}) \end{array}
$$

where we define constant $\Delta$ such that $\begin{array} { r } { F _ { 1 / \bar { \rho } } ( \mathbf w _ { 0 } , \mathbf s _ { 0 } , s _ { 0 } ^ { \prime } ) - \mathbb { E } [ F _ { 1 / \bar { \rho } } ( \mathbf w _ { T } , \mathbf s _ { T } , s _ { T } ^ { \prime } ) ] \le \Delta . } \end{array}$

With MSVR updates for $v _ { i , j , t }$ and $u _ { i , t }$ , following from Lemma A.3 and Lemma A.4, we have

$$
\begin{array}{r l} & {\mu_ {1} = \frac {B _ {1} B _ {2} \tau_ {1}}{2 n _ {1} n _ {2}}, \quad \mu_ {2} = \frac {B _ {1} \tau_ {2}}{2 n _ {1}}, \quad R _ {1} = \frac {2 \tau_ {1} ^ {1 / 2} \sigma}{B _ {3} ^ {1 / 2}} + \frac {4 n _ {1} n _ {2} \sqrt {C _ {h}} M \eta}{B _ {1} B _ {2} \tau_ {1} ^ {1 / 2}}} \\ & {R _ {2} = \frac {4 \tau_ {1} \sigma^ {2}}{B _ {3}} + \frac {1 6 n _ {1} ^ {2} n _ {2} ^ {2} C _ {h} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} B _ {2} ^ {2} \tau_ {1}}, \quad R _ {3} = \frac {2 \tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {C _ {2} n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} \tau_ {1}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}} + \frac {C _ {2} n _ {1} ^ {3 / 2} n _ {2} ^ {1 / 2} \eta}{B _ {1} ^ {3 / 2} B _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}},} \\ & {R _ {4} = \frac {4 \tau_ {2} \sigma^ {2}}{B _ {2}} + \frac {C _ {2} ^ {2} n _ {1} B _ {2} \tau_ {1} ^ {2}}{B _ {1} n _ {2} \tau_ {2}} + \frac {C _ {2} ^ {2} n _ {1} ^ {3} n _ {2} \eta^ {2}}{B _ {1} ^ {3} B _ {2} \tau_ {2}}.} \end{array}
$$

Then

$$
\begin{array}{r l} & {\frac {1}{T} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} ]} \\ & {\leq \mathcal {O} \bigg (\frac {1}{T} (\frac {1}{\eta} + \frac {1}{\mu_ {m i n}}) + \eta + \frac {\tau_ {1} ^ {1 / 2}}{B _ {3} ^ {1 / 2}} + \frac {\tau_ {1}}{B _ {3}} + \frac {\tau_ {2} ^ {1 / 2}}{B _ {2} ^ {1 / 2}} + \frac {\tau_ {2}}{B _ {2}}} \\ & {\quad + \frac {n _ {1} n _ {2} \eta}{B _ {1} B _ {2} \tau_ {1} ^ {1 / 2}} + \frac {n _ {1} ^ {2} n _ {2} ^ {2} \eta^ {2}}{B _ {1} ^ {2} B _ {2} ^ {2} \tau_ {1}} + \frac {n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} \tau_ {1}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}} + \frac {n _ {1} ^ {3 / 2} n _ {2} ^ {1 / 2} \eta}{B _ {1} ^ {3 / 2} B _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}} + \frac {n _ {1} B _ {2} \tau_ {1} ^ {2}}{B _ {1} n _ {2} \tau_ {2}} + \frac {n _ {1} ^ {3} n _ {2} \eta^ {2}}{B _ {1} ^ {3} B _ {2} \tau_ {2}} \bigg)} \\ & {\leq \mathcal {O} \bigg (\frac {1}{T} (\frac {1}{\eta} + \frac {1}{\mu_ {m i n}}) + \frac {\tau_ {1} ^ {1 / 2}}{B _ {3} ^ {1 / 2}} + \frac {\tau_ {2} ^ {1 / 2}}{B _ {2} ^ {1 / 2}} + \frac {n _ {1} n _ {2} \eta}{B _ {1} B _ {2} \tau_ {1} ^ {1 / 2}} + \frac {n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} \tau_ {1}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}} + \frac {n _ {1} ^ {3 / 2} n _ {2} ^ {1 / 3} \eta}{B _ {1} ^ {3 / 2} B _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}} \bigg).} \end{array}
$$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3 Stochastic Optimization algorithm for Non-smooth FCCO with coordinate moving average
1: Initialization:  $w_{0}, \{u_{i,0} : i \in S\}$ .
2: for  $t = 0, \ldots, T - 1$  do
3: Draw sample batches  $B_{1}^{t} \sim S$ , and  $B_{2,i}^{t} \sim D_{i}$  for each  $i \in B_{1}^{t}$ .
4:  $u_{i,t+1} = \begin{cases}(1 - \tau)u_{i,t} + \tau g_i(\mathbf{w}_t; \mathcal{B}_{2,i}^t), &amp; i \in \mathcal{B}_1^t \\ u_{i,t}, &amp; i \notin \mathcal{B}_1^t\end{cases}$ 
5: Compute  $G_t = \frac{1}{B_1} \sum_{i \in B_1^t} \partial g_i(\mathbf{w}_t; \mathcal{B}_{2,i}^t) \partial f_i(u_{i,t})$ 
6: Update  $w_{t+1} = w_t - \eta G_t$ 
7: end for
8: return  $w_{\bar{t}}$  with uniformly sampled  $\bar{t} \in \{0, T - 1\}$ .
</div>

Setting

$$
\tau_ {1} = \mathcal {O} \left(\min \{B _ {3}, \frac {B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2}}{n _ {1} ^ {1 / 2}} \} \epsilon^ {4}\right), \quad \tau_ {2} = \mathcal {O} (B _ {2} \epsilon^ {4}),
$$

$$
\eta = \mathcal {O} \left(\min \left\{\frac {B _ {1} B _ {2}}{n _ {1} n _ {2}} \tau_ {1} ^ {1 / 2} \epsilon^ {2}, \frac {B _ {1} ^ {3 / 2} B _ {2} ^ {1 / 2}}{n _ {1} ^ {3 / 2} n _ {2} ^ {1 / 2}} \tau_ {2} ^ {1 / 2} \right\}\right)
$$

$$
= \mathcal {O} \left(\min \left\{B _ {3} ^ {1 / 2}, \frac {B _ {1} ^ {1 / 4} n _ {2} ^ {1 / 4}}{n _ {1} ^ {1 / 4}}, \frac {B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2}}{n _ {1} ^ {1 / 2}} \right\} \frac {B _ {1} B _ {2}}{n _ {1} n _ {2}} \epsilon^ {4}\right),
$$

then with

$$
T = \mathcal {O} \left(\max \left\{\frac {1}{B _ {3} ^ {1 / 2}}, \frac {n _ {1} ^ {1 / 4}}{B _ {1} ^ {1 / 4} n _ {2} ^ {1 / 4}}, \frac {n _ {1} ^ {1 / 2}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2}} \right\} \frac {n _ {1} n _ {2}}{B _ {1} B _ {2}} \epsilon^ {- 6}\right),
$$

we have

$$
\frac {1}{T} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} ] \leq \epsilon^ {2}
$$

## B Solving Non-smooth FCCO and TCCO with Coordinate Moving Average

In this section we consider solving non-smooth weakly-convex FCCO and TCCO without variance reduction method. To be specific, we use coordinate moving average updates for function values estimations instead of MSVR. This allows us to weaken the assumption on the Lipschitz continuity, i.e. the Lipschitz continuity of the stochastic function value estimation is not required, and can be replaced by the Lipschitz continuity of the function value. Moreover, compared with MSVR, coordinate moving average update does not need the stochastic evaluation from the previous iteration, and thus has a simpler implementation. However, as a result of not using variance reduction technique, the algorithms suffer from worse convergence rates in terms of $\epsilon .$

## B.1 Solving Non-smooth FCCO with Coordinate Moving Average

We first assume the followings assumptions hold.

Assumption B.1. For all $i \in S ,$ we assume that

$f _ { i } ( \cdot )$ is $\rho _ { f }$ -weakly-convex, $C _ { f }$ -Lipschitz continuous and non-decreasing;

$g _ { i } ( \cdot )$ is $\rho _ { g }$ -weakly-convex and $C _ { g }$ -Lipschitz continuous;

• Stochastic gradient estimators $g _ { i } ( \mathbf { w } ; \boldsymbol { \xi } )$ and $\partial g _ { i } ( \mathbf { w } ; \pmb { \xi } )$ have bounded variance $\sigma ^ { 2 }$

With coordinate moving average update, we present the following lemma of error bound.

Lemma B.2. Consider the coordinate moving average updatefor $\{ u _ { i , t } : i \in S _ { 1 } \}$ in Algorithm 3, assume $g _ { i } ( \mathbf { w } )$ is $C _ { g }$ -Lipschitz continuousfor all $i \in \mathcal { S } _ { 1 }$ and $\tau \leq 1$ , then we have

$$
\begin{array}{r l} & {\mathbb {E} [ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| ] \leq (1 - \frac {B _ {1} \tau}{4 n _ {1}}) ^ {t + 1} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| + \frac {2 \sqrt {2} \tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 \sqrt {2} n _ {1} C _ {g} M \eta}{B _ {1} \tau},} \\ & {\mathbb {E} [ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| ^ {2} ] \leq (1 - \frac {B _ {1} \tau}{4 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| ^ {2} + \frac {8 \tau \sigma^ {2}}{B _ {2}} + \frac {3 2 n _ {1} ^ {2} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau^ {2}}.} \end{array}
$$

Then we have a convergence analysis similar to Theorem 4.6.

Theorem B.3. Consider non-smooth weakly-convex FCCO problem, under Assumption B.1, setting $\tau = \mathcal { O } ( B _ { 2 } \epsilon ^ { 4 } ) \le 1 , \eta = \mathcal { O } ( \frac { B _ { 1 } B _ { 2 } } { n _ { 1 } } \epsilon ^ { 6 } )$ , Algorithm 3 converges to an ϵ-stationary point ofthe Moreau envelope $F _ { 1 / \bar { \rho } }$ in $\begin{array} { r } { T = \mathcal { O } ( \frac { n _ { 1 } } { B _ { 1 } B _ { 2 } } \overleftarrow { } \epsilon ^ { - 8 } ) } \end{array}$ iterations.

ProofofTheorem B.3. Since the only difference between SONX and Algorithm 3 is the update for $\{ u _ { i , t } : i \in S _ { 1 } \}$ , the proof of Theorem 4.6 still holds with the error bound replaced by Lemma B.2, i e

$$
\mathbb {E} \left[ \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| \right] \leq (1 - \mu) ^ {t + 1} \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| + R _ {1},
$$

$$
\mathbb {E} \bigg [ \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| ^ {2} \bigg ] \leq (1 - \mu) ^ {t + 1} \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| ^ {2} + R _ {2},
$$

$$
\mu = \frac {B _ {1} \tau}{4 n _ {1}}, R _ {1} = \frac {2 \sqrt {2} \tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 \sqrt {2} n _ {1} C _ {g} M \eta}{B _ {1} \tau}, R _ {2} = \frac {8 \tau \sigma^ {2}}{B _ {2}} + \frac {3 2 n _ {1} ^ {2} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau^ {2}}.
$$

Then proof proceeds to

$$
\begin{array}{c} \frac {1}{T} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} ] \leq \mathcal {O} \left(\frac {1}{T} (\frac {1}{\eta} + \frac {1}{\mu}) + \eta + R _ {1} + R _ {2}\right) \\ = \mathcal {O} \left(\frac {1}{T} (\frac {1}{\eta} + \frac {n _ {1}}{B _ {1} \tau}) + \eta + \frac {\tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {n _ {1} \eta}{B _ {1} \tau} + \frac {\tau \sigma^ {2}}{B _ {2}} + \frac {n _ {1} ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau^ {2}}\right). \end{array}
$$

Setting

$$
\tau = \mathcal {O} (B _ {2} \epsilon^ {4}), \quad \eta = \mathcal {O} (\frac {B _ {1} B _ {2}}{n _ {1}} \epsilon^ {6}),
$$

then to reach a nearly ϵ-stationary point, Algorithm 3 needs

$$
T = \mathcal {O} (\frac {n _ {1}}{B _ {1} B _ {2}} \epsilon^ {- 8})
$$

iterations.

## B.2 Solving Non-smooth TCCO with Coordinate Moving Average

We first assume the following assumptions hold.

Assumption B.4. For all $( i , j ) \in S _ { 1 } \times S _ { 2 }$ , we assume that

• $f _ { i } ( \cdot )$ is $\rho _ { f } .$ -weakly-convex, $C _ { f } .$ -Lipschitz continuous and non-decreasing;

$g _ { i } ( \cdot )$ is $\rho _ { g }$ -weakly-convex and $C _ { g ^ { - } }$ Lipschitz continuous. $h _ { i , j } ( \cdot )$ is differentiable and $C _ { h ^ { - 1 } }$ Lipschitz continuous.

• Either $g _ { i }$ is monotone and $h _ { i , j } ( \cdot )$ is $L _ { h }$ -smooth, or $g _ { i }$ is non-decreasing and $h _ { i , j } ( \cdot )$ is $L _ { h }$ -weaklyconvex.

• Stochastic estimators $h _ { i , j } ( \mathbf { w } , \boldsymbol { \xi } ) , \ \partial h _ { i , j } ( \mathbf { w } , \boldsymbol { \xi } )$ and $g _ { i } ( v _ { i , j } )$ have bounded variance $\sigma ^ { 2 }$ , and $\| h _ { i , j } ( \mathbf { w } ) \| \leq \tilde { C } _ { h }$

With coordinate moving average update, we present the following lemmas of error bounds.

Algorithm 4 Stochastic Optimization algorithm for Non-smooth TCCO with coordinate moving average

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
1: Initialization:  $w_{0}, \{u_{i,0} : i \in S_{1}\}$ ,  $v_{i,j,0} = h_{i,j}(w_{0}; \mathcal{B}_{3,i,j}^{0})$  for all  $(i,j) \in S_{1} \times S_{2}$ .
2: for  $t = 0, \ldots, T - 1$  do
3: Sample batches  $B_{1}^{t} \subset S_{1}$ ,  $B_{2}^{t} \subset S_{2}$ , and  $B_{3,i,j}^{t} \subset D_{i,j}$  for  $i \in B_{1}^{t}$  and  $j \in B_{2}^{t}$ .
4:  $v_{i,j,t+1} = \begin{cases}(1 - \tau_1)v_{i,j,t} + \tau_1h_{i,j}(w_t; B_{3,i,j}^t), &amp; (i,j) \in B_1^t \times B_2^t \\ v_{i,j,t}, &amp; (i,j) \notin B_1^t \times B_2^t\end{cases}$ 
5:  $u_{i,t+1} = \begin{cases}(1 - \tau_2)u_{i,t} + \frac{1}{B_2}\sum_{j \in B_2^t}\tau_2g_i(v_{i,j,t}), &amp; i \in B_1^t \\ u_{i,t}, &amp; i \notin B_1^t\end{cases}$ 
6:  $G_t = \frac{1}{B_1}\sum_{i \in B_1^t}\left[\left(\frac{1}{B_2}\sum_{i \in B_2^t}\nabla h_{i,j}(w_t; B_{3,i,j}^t)\partial g_i(v_{i,j,t})\right)\partial f_i(u_{i,t})\right]$ 
7: Update  $w_{t+1} = w_t - \eta G_t$ 
8: end for
9: return  $w_{\bar{t}}$  with uniformly sampled  $\bar{t} \in \{0, T - 1\}$ .
</div>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Lemma B.5. Consider the coordinate moving average update for $\{v_{i,j,t}:(i,j)\in S_1\times S_2\}$ in Algorithm 4, assume $h_{i,j}(\mathbf{w})$ is $C_h$-Lipschitz continuous for all $(i,j)\in S_1\times S_2$ and $\tau_1\leq 1$, then we have $\mathbb{E}\left[\frac{1}{n_1n_2}\sum_{i\in S_1}\sum_{j\in S_2}\| v_{i,j,t + 1} - h_{i,j}(\mathbf{w}_{t + 1})\|\right]$ $\leq (1 - \frac{B_1B_2\tau_1}{4n_1n_2})^{t + 1}\frac{1}{n_1n_2}\sum_{i\in S_1}\sum_{j\in S_2}\| v_{i,j,0} - h_{i,j}(\mathbf{w}_0)\| +\frac{2\sqrt{2}\tau_1^{1 / 2}\sigma}{B_3^{1 / 2}} +\frac{4\sqrt{2} n_1n_2C_hM\eta}{B_1B_2\tau_1},$ $\mathbb{E}\left[\frac{1}{n_1n_2}\sum_{i\in S_1}\sum_{j\in S_2}\| v_{i,j,t + 1} - h_{i,j}(\mathbf{w}_{t + 1})\|^2\right]$ $\leq (1 - \frac{B_1B_2\tau_1}{4n_1n_2})^{2(t + 1)}\frac{1}{n_1n_2}\sum_{i\in S_1}\sum_{j\in S_2}\| v_{i,j,0} - h_{i,j}(\mathbf{w}_0)\|^2 +\frac{8\tau_1\sigma^2}{B_3} +\frac{32n_1^2n_2^2C_h^2M^2\eta^2}{B_1^2B_2^2\tau_1^2}.$
</div>

Lemma B.6. Consider the coordinate moving average updatefor $\{ u _ { i , t } : i \in S _ { 1 } \}$ in Algorithm 4, assume $g _ { i } ( \cdot )$ is $C _ { g }$ -Lipschitz continuousfor all $i \in S _ { 1 }$ and $\tau _ { 2 } \leq 1$ , then we have

$$
\mathbb {E} \left[ \frac {1}{n _ {1}} \sum_ {i \in \mathcal {S} _ {1}} \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| \right]
$$

$$
\leq (1 - \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) ^ {t + 1} \frac {1}{n _ {1}} \sum_ {i \in \mathcal {S} _ {1}} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, 0}) \| + \frac {2 \sqrt {2} \tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 \sqrt {2} C _ {g} M n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} \tau_ {1}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2} \tau_ {2}},
$$

$$
\leq (1 - \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) ^ {2 (t + 1)} \frac {1}{n _ {1}} \sum_ {i \in \mathcal {S} _ {1}} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, 0}) \| ^ {2} + \frac {8 \tau_ {2} \sigma^ {2}}{B _ {2}} + \frac {3 2 C _ {g} ^ {2} M ^ {2} n _ {1} B _ {2} \tau_ {1} ^ {2}}{B _ {1} n _ {2} \tau_ {2} ^ {2}}.
$$

Then we have a convergence analysis similar to Theorem A.2.

Theorem B.7. Consider non-smooth weakly-convex TCCO problem, under Assumption B.4, setting $\begin{array} { r l r l r } { \tau _ { 1 } } & { = } & { \mathcal { O } \left( \operatorname* { m i n } \left\{ B _ { 3 } \epsilon ^ { 4 } , \frac { B _ { 1 } ^ { 1 / 2 } n _ { 2 } ^ { 1 / 2 } } { n _ { 1 } ^ { 1 / 2 } B _ { 2 } ^ { 1 / 2 } } B _ { 2 } \epsilon ^ { 6 } \right\} \right) } & { \leq } & { 1 , ~ \tau _ { 2 } } & { = } & { \mathcal { O } ( B _ { 2 } \epsilon ^ { 4 } ) ~ \leq ~ 1 , ~ \eta ~ = } \end{array}$ $\begin{array} { r } { \mathcal { O } \left( \operatorname* { m i n } \left\{ B _ { 3 } \epsilon ^ { 4 } , \frac { B _ { 1 } ^ { 1 / 2 } \overset { \cdot } { n } _ { 2 } ^ { 1 / 2 } } { n _ { 1 } ^ { 1 / 2 } B _ { 2 } ^ { 1 / 2 } } \overset { \cdot } { B _ { 2 } } \epsilon ^ { 6 } \right\} \frac { B _ { 1 } B _ { 2 } } { n _ { 1 } n _ { 2 } } \epsilon ^ { 2 } \right) } \end{array}$ , Algorithm 4 converges to an ϵ-stationary point of the Moreau envelope $\begin{array} { r } { F _ { 1 / \bar { \rho } } i n T = \mathcal { O } \left( \operatorname* { m a x } \left\{ \frac { 1 } { B _ { 3 } } , \frac { n _ { 1 } ^ { 1 / 2 } } { B _ { 1 } ^ { 1 / 2 } B _ { 2 } ^ { 1 / 2 } n _ { 2 } ^ { 1 / 2 } } \epsilon ^ { - 2 } \right\} \frac { n _ { 1 } n _ { 2 } } { B _ { 1 } B _ { 2 } } \epsilon ^ { - 8 } \right) } \end{array}$ iterations.

ProofofTheorem B.7. Since the only difference between SONT and Algorithm 4 is the update for $\big \{ u _ { i , t } : \dot { i } \in \mathcal { S } _ { 1 } \big \}$ and $\{ v _ { i , j , t } : ( i , j ) \in \mathbf { \dot { S } } _ { 1 } \times S _ { 2 } \}$ , the proof of Theorem A.2 still holds with the error bound replaced by Lemma B.5 and Lemma B.6, i.e.,

$$
\frac {1}{n _ {1} n _ {2}} \sum_ {i \in S _ {1}} \sum_ {j \in S _ {2}} \mathbb {E} [ \| h _ {i, j} (\mathbf {w} _ {t}) - v _ {i, j, t} \| ] \leq (1 - \mu_ {1}) ^ {t} \frac {1}{n _ {1} n _ {2}} \sum_ {i \in S _ {1}} \sum_ {j \in S _ {2}} \| h _ {i, j} (\mathbf {w} _ {0}) - v _ {i, j, 0} \| + R _ {1},
$$

$$
\frac {1}{n _ {1} n _ {2}} \sum_ {i \in S _ {1}} \sum_ {j \in S _ {2}} \mathbb {E} [ \| h _ {i, j} (\mathbf {w} _ {t}) - v _ {i, j, t} \| ^ {2} ] \leq (1 - \mu_ {1}) ^ {t} \frac {1}{n _ {1} n _ {2}} \sum_ {i \in S _ {1}} \sum_ {j \in S _ {2}} \| h _ {i, j} (\mathbf {w} _ {0}) - v _ {i, j, 0} \| ^ {2} + R _ {2},
$$

$$
\frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \mathbb {E} \bigg [ \bigg \| \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, t}) - u _ {i, t} \bigg \| \bigg ] \leq (1 - \mu_ {2}) ^ {t} \frac {1}{n _ {+}} \sum_ {i \in S _ {+}} \bigg \| \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, 0}) - u _ {i, 0} \bigg \| + R _ {3},
$$

$$
\frac {1}{n _ {1}} \sum_ {i \in S _ {1}} \mathbb {E} \left[ \left\| \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, t}) - u _ {i, t} \right\| ^ {2} \right] \leq (1 - \mu_ {2}) ^ {t} \frac {1}{n _ {+}} \sum_ {i \in S _ {+}} \left\| \frac {1}{n _ {2}} \sum_ {j \in S _ {2}} g _ {i} (v _ {i, j, 0}) - u _ {i, 0} \right\| ^ {2} + R _ {4},
$$

with

$$
\begin{array}{r l} & {\mu_ {1} = \frac {B _ {1} B _ {2} \tau_ {1}}{4 n _ {1} n _ {2}}, \quad \mu_ {2} = \frac {B _ {1} \tau_ {2}}{4 n _ {1}}, \quad R _ {1} = \frac {2 \sqrt 2 \tau_ {1} ^ {1 / 2} \sigma}{B _ {3} ^ {1 / 2}} + \frac {4 \sqrt 2 n _ {1} n _ {2} C _ {h} M \eta}{B _ {1} B _ {2} \tau_ {1}}} \\ & {R _ {2} = \frac {8 \tau_ {1} \sigma^ {2}}{B _ {3}} + \frac {3 2 n _ {1} ^ {2} n _ {2} ^ {2} C _ {h} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} B _ {2} ^ {2} \tau_ {1} ^ {2}}, \quad R _ {3} = \frac {2 \sqrt 2 \tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 \sqrt 2 C _ {g} M n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} \tau_ {1}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2} \tau_ {2}},} \\ & {R _ {4} = \frac {8 \tau_ {2} \sigma^ {2}}{B _ {2}} + \frac {3 2 C _ {g} ^ {2} M ^ {2} n _ {1} B _ {2} \tau_ {1} ^ {2}}{B _ {1} n _ {2} \tau_ {2} ^ {2}}} \end{array}
$$

Then the proof proceeds to

$$
\begin{array}{l} \frac {1}{T} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}) \| ^ {2} ] \\ \leq \mathcal {O} \left(\frac {1}{T} (\frac {1}{\eta} + \frac {1}{\mu_ {m i n}}) + \eta + R _ {1} + R _ {2} + R _ {3} + R _ {4}\right) \\ \leq \mathcal {O} \bigg (\frac {1}{T} (\frac {1}{\eta} + \frac {1}{\mu_ {m i n}}) + \eta + \frac {\tau_ {1} ^ {1 / 2} \sigma}{B _ {3} ^ {1 / 2}} + \frac {\tau_ {1} \sigma^ {2}}{B _ {3}} + \frac {\tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {\tau_ {2} \sigma^ {2}}{B _ {2}} + \frac {n _ {1} n _ {2} \eta}{B _ {1} B _ {2} \tau_ {1}} + \frac {n _ {1} ^ {2} n _ {2} ^ {2} \eta^ {2}}{B _ {1} ^ {2} B _ {2} ^ {2} \tau_ {1} ^ {2}} \\ \quad + \frac {n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} \tau_ {1}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2} \tau_ {2}} + \frac {n _ {1} B _ {2} \tau_ {1} ^ {2}}{B _ {1} n _ {2} \tau_ {2} ^ {2}} \bigg) \\ \leq \mathcal {O} \bigg (\frac {1}{T} (\frac {1}{\eta} + \frac {1}{\mu_ {m i n}}) + \frac {\tau_ {1} ^ {1 / 2} \sigma}{B _ {3} ^ {1 / 2}} + \frac {\tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {n _ {1} n _ {2} \eta}{B _ {1} B _ {2} \tau_ {1}} + \frac {n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} \tau_ {1}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2} \tau_ {2}} \bigg). \end{array}
$$

Setting

$$
\begin{array}{l} \tau_ {1} = \mathcal {O} \left(\min \left\{B _ {3} \epsilon^ {4}, \frac {B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2}}{n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2}} B _ {2} \epsilon^ {6} \right\}\right), \quad \tau_ {2} = \mathcal {O} (B _ {2} \epsilon^ {4}), \\ \eta = \mathcal {O} \left(\min \left\{B _ {3} \epsilon^ {4}, \frac {B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2}}{n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2}} B _ {2} \epsilon^ {6} \right\} \frac {B _ {1} B _ {2}}{n _ {1} n _ {2}} \epsilon^ {2}\right), \end{array}
$$

then to reach a nearly ϵ-stationary point, Algorithm 4 need

$$
T = \mathcal {O} \left(\max \left\{\frac {1}{B _ {3}}, \frac {n _ {1} ^ {1 / 2}}{B _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} n _ {2} ^ {1 / 2}} \epsilon^ {- 2} \right\} \frac {n _ {1} n _ {2}}{B _ {1} B _ {2}} \epsilon^ {- 1 0}\right)
$$

iterations.

## C Details for TPAUC Maximization

## C.1 Assumption Verification

We first present two lemmas about the weak convexity of the objective in the regular learning setting and in the multi-instance learning setting with mean pooling.

Lemma C.1. Consider the formulation in problem $( 9 )$ in the regular learning setting and assume that function $\ell ( \cdot )$ is non-decreasing, $C _ { \ell }$ Lipschitz continuous and ρ<sub>ℓ</sub>-weakly-convex, and function $h _ { \mathbf { w } } ( X _ { i } )$ is $C _ { h }$ Lipschitz continuous and $\rho _ { h } – w e a k l y$ -convex. then the following statements are true:

$f _ { i } ( g , s ^ { \prime } )$ is convex and $C _ { f }$ -Lipschitz continuous w.r.t. $( g , s ^ { \prime } )$ , and non-decreasing w.r.t. $g .$

$\psi _ { i } ( \mathbf { w } , s _ { i } )$ is $\rho _ { \psi } .$ -weakly-convex w.r.t. $\left( \mathbf { w } , s _ { i } \right)$ , and the stochastic estimator ofthefinite sum function value $\psi _ { i } ( \mathbf { w } , s _ { i } )$ is $C _ { \psi } – L i p s c h i t z$ continuous w.r.t. $\left( \mathbf { w } , s _ { i } \right)$

$\begin{array} { r } { \frac { 1 } { n _ { + } } \sum _ { i \in { \mathcal { S } _ { + } } } f _ { i } \big ( \psi _ { i } ( \mathbf { w } , s _ { i } ) , s ^ { \prime } \big ) } \end{array}$ is ρ<sub>F</sub>-weakly-convex w.r.t. $( \mathbf { w } , \mathbf { s } , s ^ { \prime } )$

Lemma C.2. Consider the formulation in problem (9) in the multi-instance learning setting with mean pooling, and assume that function $\begin{array} { r } { h _ { i } ( \mathbf { w } ) = \frac { 1 } { | X _ { i } | } \sum _ { \mathbf { x } \in X _ { i } } e ( \mathbf { w } _ { e } ; \mathbf { x } ) ^ { \top } \mathbf { w } _ { c } } \end{array}$ is ${ \tilde { L } } _ { h }$ -smooth and is bounded by ${ \tilde { C } } _ { h } ,$ , and $h _ { i } ( \mathbf { w } ; \boldsymbol { \xi } ) = e ( \mathbf { w } _ { e } ; \boldsymbol { \xi } ) ^ { \top } \mathbf { w } _ { c }$ is C -Lipschitz continuous and has bounded variance $\sigma ^ { 2 } ,$ , ℓ is non-decreasing and L<sub>ℓ</sub>-weakly-convex, then thefollowings are true:

$f _ { i } ( g , s ^ { \prime } )$ is convex and C<sub>f</sub>-Lipschitz-continuous w.r.t. $( g , s ^ { \prime } )$ , and non-decreasing w.r.t. $g ;$

$\begin{array} { r } { g _ { i } ( v , s _ { i } ) = s _ { i } + \frac { ( \ell ( v ) - s _ { i } ) _ { + } } { \beta } } \end{array}$ is $\rho _ { g }$ -weakly convex and non-decreasing w.r.t. $v ,$ convex w.r.t. $s _ { i } ,$ and $C _ { g }$ -Lipschitz continuous w.r.t. $( v , s _ { i } )$ ;

$h _ { i , j } ( \mathbf { w } ) = h _ { j } ( \mathbf { w } ) - h _ { i } ( \mathbf { w } )$ is L<sub>h</sub>-weakly-convex, and $h _ { i , j } ( \mathbf { w } ; \boldsymbol { \xi } , \boldsymbol { \zeta } )$ ) is C -Lipschitz continuous;

$\begin{array} { r } { \frac { 1 } { n _ { + } } \sum _ { \boldsymbol { X } _ { i } \in \mathcal { S } _ { + } } f _ { i } \big ( g _ { i } \big ( h _ { i , j } ( \mathbf { w } ) , s _ { i } \big ) , \boldsymbol { s } ^ { \prime } \big ) } \end{array}$ is ρ<sub>F</sub>-weakly-convex w.r.t. $( \mathbf { w } , \mathbf { s } , s ^ { \prime } )$

## C.1.1 Proof of Lemma C.1

ProofofLemma C.1. The convexity of $f _ { i } ( g , s ^ { \prime } )$ with respect to $( g , s ^ { \prime } )$ follows from the convexity definition. With subgradients $\begin{array} { r } { \partial _ { s ^ { \prime } } f _ { i } ( \bar { g } , s ^ { \prime } ) \in [ 1 - \frac { 1 } { \alpha } , 1 ] , \partial _ { g } \bar { f } _ { i } ( g , s ^ { \prime } ) \in [ 0 , \frac { 1 } { \alpha } ] } \end{array}$ , we can see that $f _ { i } ( g , s ^ { \prime } )$ is ${ \frac { 1 } { \alpha } } - \mathrm { L }$ ipschitz continuous w.r.t. $( g , s ^ { \prime } )$ , and non-decreasing w.r.t. u.

We first show that $\ell ( h _ { \mathbf { w } } ( X _ { j } ) - h _ { \mathbf { w } } ( X _ { i } ) )$ ) is weakly-convex w.r.t. w.

$$
\begin{array}{r l} & {\ell (h _ {\tilde {\mathbf {w}}} (X _ {j}) - h _ {\tilde {\mathbf {w}}} (X _ {i}))} \\ & {\geq \ell (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})) + \langle \partial \ell (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})), (h _ {\tilde {\mathbf {w}}} (X _ {j}) - h _ {\tilde {\mathbf {w}}} (X _ {i})) - (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})) \rangle} \\ & {\quad + \frac {\rho_ {\ell}}{2} \| (h _ {\tilde {\mathbf {w}}} (X _ {j}) - h _ {\tilde {\mathbf {w}}} (X _ {i})) - (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})) \| ^ {2}} \\ & {\overset {(a)} {\geq} \ell (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})) + \langle \partial \ell (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})), \langle \nabla h _ {\mathbf {w}} (X _ {j}) - \nabla h _ {\mathbf {w}} (X _ {i}), \tilde {\mathbf {w}} - \mathbf {w} \rangle \rangle} \\ & {\quad + 2 \rho_ {\ell} C _ {h} ^ {2} \| \tilde {\mathbf {w}} - \mathbf {w} \| ^ {2}} \end{array}
$$

where (a) uses the weak-convexity of $h _ { \mathbf { w } } ( X _ { i } )$ and $h _ { \mathbf { w } } ( X _ { j } )$ ),

$$
\begin{array}{r l} & h _ {\tilde {\mathbf {w}}} (X _ {j}) - h _ {\mathbf {w}} (X _ {j}) \geq \langle \nabla h _ {\mathbf {w}} (X _ {j}), \tilde {\mathbf {w}} - \mathbf {w} \rangle - \frac {\rho_ {h}}{2} \| \tilde {\mathbf {w}} - \mathbf {w} \| ^ {2}, \\ & - h _ {\tilde {\mathbf {w}}} (X _ {i}) + h _ {\mathbf {w}} (X _ {i}) \geq - \langle \nabla h _ {\mathbf {w}} (X _ {i}), \tilde {\mathbf {w}} - \mathbf {w} \rangle + \frac {\rho_ {h}}{2} \| \tilde {\mathbf {w}} - \mathbf {w} \| ^ {2}. \end{array}
$$

Thus $\ell ( h _ { \mathbf { w } } ( X _ { j } ) - h _ { \mathbf { w } } ( X _ { i } ) )$ is $4 \rho _ { \ell } C _ { h } ^ { 2 }$ -weakly-convex w.r.t. w.

By convexity of $\begin{array} { r } { ( \ell , s _ { i } ) \mapsto s _ { i } + \frac { ( \ell - s _ { i } ) _ { + } } { \beta } } \end{array}$ , we have

$$
\begin{array}{r l} & {\psi_ {i} (\tilde {\mathbf {w}}, \tilde {s} _ {i})} \\ & {\geq \psi_ {i} (\mathbf {w}, s _ {i}) + \langle \partial_ {\ell} \psi_ {i} (\mathbf {w}, s _ {i}), \ell (h _ {\tilde {\mathbf {w}}} (X _ {j}) - h _ {\tilde {\mathbf {w}}} (X _ {i})) - \ell (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})) \rangle + \langle \partial_ {s _ {i}} \psi_ {i} (\mathbf {w}, s _ {i}), \tilde {s} _ {i} - s _ {i} \rangle} \\ & {\overset {(a)} {\geq} \psi_ {i} (\mathbf {w}, s _ {i}) + \partial_ {\ell} \psi_ {i} (\mathbf {w}, s _ {i}) \bigg [ \partial \ell (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})) \langle \nabla h _ {\mathbf {w}} (X _ {j}) - \nabla h _ {\mathbf {w}} (X _ {i}), \tilde {\mathbf {w}} - \mathbf {w} \rangle \rangle - 2 \rho_ {\ell} C _ {h} ^ {2} \| \tilde {\mathbf {w}} - \mathbf {w} \| ^ {2} \bigg ]} \\ & {\quad + \langle \partial_ {s _ {i}} \psi_ {i} (\mathbf {w}, s _ {i}), \tilde {s} _ {i} - s _ {i} \rangle} \\ & {\overset {(b)} {\geq} \psi_ {i} (\mathbf {w}, s _ {i}) + \partial_ {\ell} \psi_ {i} (\mathbf {w}, s _ {i}) \partial \ell (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})) \langle \nabla h _ {\mathbf {w}} (X _ {j}) - \nabla h _ {\mathbf {w}} (X _ {i}), \tilde {\mathbf {w}} - \mathbf {w} \rangle \rangle} \\ & {\quad + \langle \partial_ {s _ {i}} \psi_ {i} (\mathbf {w}, s _ {i}), \tilde {s} _ {i} - s _ {i} \rangle - \frac {2 \rho_ {\ell} C _ {h} ^ {2}}{\beta} \| \tilde {\mathbf {w}} - \mathbf {w} \| ^ {2}} \end{array}
$$

where (a) follows from the monotonicity of $\psi _ { i }$ w.r.t. ℓ and weak-convexity of $\ell ( h _ { \mathbf { w } } ( X _ { j } ) - h _ { \mathbf { w } } ( X _ { i } ) )$ and (b) is due to the Lipschitz continuity of $\begin{array} { r } { ( \ell , s _ { i } ) \mapsto s _ { i } + \frac { ( \ell - s _ { i } ) _ { + } } { \beta } } \end{array}$ w.r.t. ℓ. Thus $\psi _ { i }$ is $\frac { 4 \rho _ { \ell } C _ { h } ^ { 2 } } { \beta } \mathrm { - w e a k l y } .$ convex w.r.t. $\left( \mathbf { w } , s _ { i } \right)$

With a similar argument using the convexity and Lipschitz continuity of $f _ { i } ( g , s ^ { \prime } )$ w.r.t. $( g , s ^ { \prime } )$ and the weak-convexity of $\psi _ { i } ( \mathbf { w } , s _ { i } )$ , we can show that $f _ { i } ( \psi _ { i } ( \mathbf { w } , s _ { i } ) , s ^ { \prime } )$ is $\frac { 4 \rho _ { \ell } C _ { h } ^ { 2 } } { \beta }$ -weakly-convex w.r.t. $\big ( \mathbf { w } , s _ { i } , s ^ { \prime } \big )$ . Thus, $F ( \mathbf { w } , s _ { i } , s ^ { \prime } )$ is $\begin{array} { r } { \rho _ { F } = \frac { 4 \rho _ { \ell } C _ { h } ^ { 2 } } { \beta } } \end{array}$ -weakly-convex w.r.t. $( \mathbf { w } , \mathbf { s } , s ^ { \prime } )$

Now we show the Lipschitz continuity of $\psi _ { i } ( \mathbf { w } , s _ { i } ; X _ { j } )$ ), i.e. an unbiased stochastic estimator of $\psi _ { i } ( \mathbf { w } , s _ { i } )$ . We have

$$
\begin{array}{r l} & {\| \psi_ {i} (\mathbf {w}, s _ {i}; X _ {j}) - \psi_ {i} (\tilde {\mathbf {w}}, \tilde {s} _ {i}; X _ {j}) \| ^ {2}} \\ & {= \left\| (s _ {i} + \frac {(\ell (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})) - s _ {i}) _ {+}}{\beta}) - (\tilde {s} _ {i} + \frac {(\ell (h _ {\tilde {\mathbf {w}}} (X _ {j}) - h _ {\tilde {\mathbf {w}}} (X _ {i})) - \tilde {s} _ {i}) _ {+}}{\beta}) \right\| ^ {2}} \\ & {\leq 2 \| s _ {i} - \tilde {s} _ {i} \| ^ {2} + 2 \left\| \frac {(\ell (h _ {\mathbf {w}} (X _ {j}) - h _ {\mathbf {w}} (X _ {i})) - s _ {i}) _ {+}}{\beta} - \frac {(\ell (h _ {\tilde {\mathbf {w}}} (X _ {j}) - h _ {\tilde {\mathbf {w}}} (X _ {i})) - \tilde {s} _ {i}) _ {+}}{\beta} \right\| ^ {2}} \\ & {\leq 2 \| s _ {i} - \tilde {s} _ {i} \| ^ {2} + \frac {2}{\beta^ {2}} (8 C _ {\ell} ^ {2} C _ {h} ^ {2} \| \tilde {\mathbf {w}} - \mathbf {w} \| ^ {2} + 2 \| \tilde {s} _ {i} - s _ {i} \| ^ {2})} \\ & {\leq (2 + \frac {4 + 1 6 C _ {\ell} ^ {2} C _ {h} ^ {2}}{\beta^ {2}}) (\| \tilde {\mathbf {w}} - \mathbf {w} \| ^ {2} + \| \tilde {s} _ {i} - s _ {i} \| ^ {2}).} \end{array}
$$

Thus $\begin{array} { r } { \psi _ { i } ( \mathbf { w } , s _ { i } ; X _ { j } ) \mathrm { i s } ( 2 + \frac { 4 + 1 6 C _ { \ell } ^ { 2 } C _ { h } ^ { 2 } } { \beta ^ { 2 } } ) ^ { 1 / 2 } . } \end{array}$ -Lipschitz continuous w.r.t. $\left( \mathbf { w } , s _ { i } \right)$

## C.1.2 Proof of Lemma C.2

ProofofLemma C.2. First of all, the convexity of $f _ { i } ( u , s ^ { \prime } )$ w.r.t. $( u , s ^ { \prime } )$ and the convexity of $g _ { i } ( v _ { i j } , s _ { i } )$ w.r.t. $( \ell , s _ { i } )$ directly follows from the convexity definition. Moreover, one can see from the formulation that $\begin{array} { r } { \partial _ { s ^ { \prime } } f _ { i } ( g , s ^ { \prime } ) \in [ 1 - \frac { 1 } { \alpha } , 1 ] , \partial _ { u } f _ { i } ( g , \hat { s ^ { \prime } } ) \in [ 0 , \frac { 1 } { \alpha } ] , \partial _ { \ell } g _ { i } ( v _ { i j } , s _ { i } ) \in [ 1 - \frac { 1 } { \beta } , 1 ] } \end{array}$ $\begin{array} { r } { \partial _ { s _ { i } } g _ { i } ( v _ { i j } , s _ { i } ) \in [ 0 , \frac { 1 } { \beta } ] } \end{array}$ . Thus $f _ { i }$ is $\begin{array} { r } { C _ { f } = \frac { 1 } { \alpha } \mathbf { - } \mathbf { L } } \end{array}$ ipschitz continuous w.r.t. $( u , s ^ { \prime } )$ and non-decreasing w.r.t. $u , g _ { i }$ is $\scriptstyle { \frac { 1 } { \beta } } - \mathrm { I }$ Lipschitz continuous w.r.t. $( \ell , s _ { i } )$ and non-decreasing w.r.t. ℓ. Since $\ell ( \cdot )$ is nondecreasing, $g _ { i } ( v _ { i j } , s _ { i } )$ is non-decreasing w.r.t. $v _ { i j }$ . As a result of Proposition 4.2, $g _ { i } ( v _ { i j } , s _ { i } )$ is $\begin{array} { r } { \rho _ { g } = \frac { 1 } { \beta } L _ { \ell } . } \end{array}$ -weakly-convex w.r.t. $v _ { i j }$ . Due to the composition structure and the Lipschitz continuity of $g _ { i }$ and $\ell ,$ one can see that $g _ { i } ( v _ { i j } , s _ { i } )$ is $\begin{array} { r } { C _ { g } = \frac { 1 } { \beta } C _ { \ell } . } \end{array}$ -Lipschitz continuous w.r.t. $( v _ { i j } , s _ { i } )$

The $L _ { h } = 2 { \tilde { L } } _ { h }$ -weakly-convexity of $h _ { i , j } ( \mathbf { w } )$ and $C _ { h } = 2 \tilde { C } _ { h }$ -Lipschitz continuity of $h _ { i , j } ( \mathbf { w } ; \boldsymbol { \xi } , \boldsymbol { \zeta } )$ directly follows from the ${ \tilde { L } } _ { h }$ -smoothness of $h _ { i } ( \mathbf { w } )$ and $\tilde { C } _ { h }$ -Lipschitz continuity of $h _ { i } ( \mathbf { w } ; \boldsymbol { \xi } )$ . Finally, we show the weakly-convexity of $f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , s ^ { \prime } )$

$$
\begin{array} { r l } & f _ { i } ( g _ { i } ( h _ { i , j } ( \tilde { \mathbf { w } } ) , \tilde { s } _ { i } ) \tilde { s } ^ { \prime } ) \\ & \overset { ( a ) } { \geq } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , s ^ { \prime } ) + \langle \partial _ { s ^ { \prime } } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , s ^ { \prime } ) , \tilde { s } ^ { \prime } - s ^ { \prime } \rangle \\ & \quad + \langle \partial _ { u } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , s ^ { \prime } ) , g _ { i } ( h _ { i , j } ( \tilde { \mathbf { w } } ) , \tilde { s } _ { i } ) - g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) \rangle \\ & \overset { ( b ) } { \geq } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , s ^ { \prime } ) + \langle \partial _ { s ^ { \prime } } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , s ' ) , \tilde { s } ^ { \prime } - s ^ { \prime } \rangle \\ & \quad + \langle \partial _ { u } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , s ^ { \prime } ) , \langle \partial _ { \ell } g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , \ell ( h _ { i , j } ( \tilde { \mathbf { w } } ) ) - \ell ( h _ { i , j } ( \mathbf { w } ) ) \rangle \rangle \\ & \quad + \langle \partial _ { u } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) s ^ { \prime } ) , \langle \partial _ { s _ { i } } g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , \tilde { s } _ { i } - s _ { i } \rangle \rangle \\ & \overset { ( c ) } { \geq } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , s ^ { \prime } ) + \langle \partial _ { s ^ { \prime } } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , s^ {\prime} ) , \tilde { s } ^ { \prime } - s ^ { \prime } \rangle \\ & \quad + \langle \partial _ { u } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , s ^ { \prime} ) \partial _ { \ell } g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) \partial \ell ( h _ { i , j } ( \mathbf { w } ) ) , h _ { i , j } ( \tilde { \mathbf { w } } ) - h _ { i , j } ( \mathbf { w } ) \rangle \\ & \quad - \frac { C _ { f } C _ { g } L _ { \ell } } 2 \| h _ { i , j } ( \tilde { \mathbf { w } } ) - h _ { i , j } ( \mathbf { w } ) \| ^ { 2 } + \langle \partial _ { u } f _ { i } ( s ^ { \prime } , g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i} ) ) \partial _ { s _ { i }} g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i} ) , \tilde { s } _ { i } - s _ { i } \rangle \\ & \overset { ( d ) } { \geq } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i} ) , s ^ { \prime } ) + \langle \partial _ { s ^ { \prime } } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i} ) , s ^ {\prime} ) , \tilde { s } ^ { \prime } - s ^ { \prime } \rangle \\ & \quad + \langle \partial _ { u } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w} ) , s _ { i} ) , s ^ { \prime} ) \partial _ { \ell } g _ { i } ( h _ { i , j } ( \mathbf { w} ) , s _ { i} ) \partial \ell ( h _ { i , j } ( \mathbf { w} ) ) | | h | | e t a r e d o n t a r e d o n t a r e d o n t a r e d o n t a r e d o n t a r e d o n t a r e d o n t a r e d o n t a r e d o n t a r e d o n t a r e d o n t a r e d o n t a r e d o n t a r e d o n t a r e d o n t e d o n t a r e d o n t a r e d o n t e d o n t a r e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n t e d o n l e m a x p l y . \\ & + (\partial_ {\mu} f) [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ g ] [ 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 ] [ 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 . ] [ 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 ] [ | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
\end{array}
$$

where (a) uses the convexity of $f _ { i } , ( \mathsf { b } )$ uses the monotonicity of $f _ { i }$ w.r.t. u and convexity of $g _ { i } ( \ell , s _ { i } )$ w.r.t. $( \ell , s _ { i } ) , ( \mathrm { c } )$ uses monotonicity of $f _ { i }$ w.r.t. u, monotonicity of g<sub>i</sub> w.r.t. ℓ and $L _ { \ell ^ { - } }$ weak-convexity of $\ell , ( \mathrm { d } )$ uses the smoothness of $h _ { i , j }$ . Thus $f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , \bar { s ^ { \prime } } )$ is $\rho _ { F } = ( C _ { f } C _ { g } C _ { h } ^ { 2 } L _ { \ell } + C _ { f } C _ { g } L _ { h } ) \mathrm { . }$ weakly-convex w.r.t. $\big ( \mathbf { w } , s _ { i } , s ^ { \prime } \big )$ . Therefore, $\begin{array} { r } { \frac { 1 } { n _ { + } } \sum _ { i \in \mathcal { S } + } f _ { i } ( g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } ) , s ^ { \prime } ) } \end{array}$ is ρ<sub>F</sub>-weakly-convex w.r.t. $( \mathbf { w } , \mathbf { s } , s ^ { \prime } )$ □

## C.2 Algorithms for TPAUC and Multi-instance TPAUC Maximization

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 5 SONX for TPAUC
1: Initialization: $\mathbf{w}_0$, $\{u_{i,0}: i \in \mathcal{S}_+\}$, $\{s_{i,0}: i \in \mathcal{S}_+\}$, $s_0'$
2: for $t = 0, \ldots, T - 1$ do
3:    Sample batches $\mathcal{B}_1^t \subset S_+$ and $\mathcal{B}_2^t \subset S_-$.
4:    $u_{i,t+1} = \begin{cases}(1 - \tau)u_{i,t} + \tau \psi_i(\mathbf{w}_t, s_{i,t}; \mathcal{B}_2^t) + \gamma(\psi_i(\mathbf{w}_t, s_{i,t}; \mathcal{B}_2^t) - \psi_i(\mathbf{w}_{t-1}, s_{i,t-1}; \mathcal{B}_2^t)), &amp; i \in \mathcal{B}_1^t \\ u_{i,t}, \quad i \notin \mathcal{B}_1^t\end{cases}$
5:    $s_{i,t+1} = \begin{cases}s_{i,t} - \eta \frac{1}{B_1} \partial_s \psi_i(\mathbf{w}_t, s_{i,t}; \mathcal{B}_2^t) \partial_u f(u_{i,t}, s'_t), \quad i \in \mathcal{B}_1^t \\ s_{i,t}, \quad i \notin \mathcal{B}_1^t\end{cases}$
6:    $s'_{t+1} = s'_t - \eta \frac{1}{B_1} \sum_{i \in \mathcal{B}_1^t} \partial_{s'} f(u_{i,t}, s'_t)$
7:    Compute $G_t = \frac{1}{B_1} \sum_{i \in \mathcal{B}_1^t} \partial_w \psi_i(\mathbf{w}_t, s_{i,t}; \mathcal{B}_2^t) \partial_u f(u_{i,t}, s'_t)$
8:    Update $\mathbf{w}_{t+1} = \mathbf{w}_t - \eta G_t$
9: end for
10: return $\mathbf{w}_{\bar{t}}$ with $\bar{t}$ uniformly sampled from $\{0, \ldots, T - 1\}$.
</div>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 6 SONT for Multi-instance TPAUC
1: Initialization: $\mathbf{w}_0$, $\{u_{i,0}: i \in \mathcal{S}_+\}$, $\{s_{i,0}: i \in \mathcal{S}_+\}$, $s_0'$, $\{v_{i,j,0}: (i,j) \in \mathcal{S}_+\times \mathcal{S}_-\}$
2: for $t = 0, \ldots, T-1$ do
3: Sample batches $\mathcal{B}_1^t \subset S_+$, $\mathcal{B}_2^t \subset S_-$, and $\mathcal{B}_{3,i}^t \subset X_i$ for $i \in \mathcal{B}_1^t \cup \mathcal{B}_2^t$.
4: $v_{i,t+1} = \begin{cases} \Pi_{\tilde{C}_h}[(1 - \tau_1)v_{i,t} + \tau_1h_i(\mathbf{w}_t; \mathcal{B}_{3,i}^t) + \gamma_1(h_i(\mathbf{w}_t; \mathcal{B}_{3,i}^t) - h_i(\mathbf{w}_{t-1}; \mathcal{B}_{3,i}^t))], &amp; i \in \mathcal{B}_1^t \\ \Pi_{\tilde{C}_h}[(1 - \tau_1)v_{i,t} + \tau_1h_i(\mathbf{w}_t; \mathcal{B}_{3,i}^t) + \gamma_2(h_i(\mathbf{w}_t; \mathcal{B}_{3,i}^t) - h_i(\mathbf{w}_{t-1}; \mathcal{B}_{3,i}^t))], &amp; i \in \mathcal{B}_2^t \\ v_{i,t}, i \notin \mathcal{B}_1^t and i \notin \mathcal{B}_2^t \end{cases}$
5: $u_{i,t+1} = \begin{cases} (1 - \tau_2)u_{i,t} + \frac{1}{B_2}\sum_{j \in \mathcal{B}_2^t}[\tau_2g(v_{j,t} - v_{i,t}, s_{i,t}) + \gamma_3(g(v_{j,t} - v_{i,t}, s_{i,t}) - g(v_{j,t-1} - v_{i,t-1}, s_{i,t-1}))], &amp; i \in \mathcal{B}_1^t \\ u_{i,t}, &amp; i \notin \mathcal{B}_1^t \end{cases}$
6: $s_{i,t+1} = \begin{cases} s_{i,t} - \eta_1\frac{1}{B_1}\left[\frac{1}{B_2}\sum_{j \in \mathcal{B}_2^t}\partial_{s_i}g(v_{j,t} - v_{i,t}, s_{i,t})\right]\partial_u f(s'_t, u_{i,t}), &amp; i \in \mathcal{B}_1^t \\ s_{i,t}, &amp; i \notin \mathcal{B}_1^t \end{cases}$
7: $s'_{t+1} = s'_t - \eta_2\frac{1}{B_1}\sum_{i \in \mathcal{B}_1^t}\partial_{s'}f(u_{i,t}, s'_t)$
8: $G_t = \frac{1}{B_1}\sum_{i \in \mathcal{B}_1^t}\partial_u f(u_{i,t}, s'_t)$
9: $\left[\frac{1}{B_2}\sum_{j \in \mathcal{B}_2^t}\left(\nabla h_j(\mathbf{w}_t; \mathcal{B}_{3,j}^t) - \nabla h_i(\mathbf{w}_t; \mathcal{B}_{3,i}^t)\right)\partial_v g(v_{j,t} - v_{i,t}, s_{i,t})\right]$
10: Update $\mathbf{w}_{t+1} = \mathbf{w}_t - \eta G_t$
11: end for
12: return $\mathbf{w}_{\bar{t}}$ with $\bar{t}$ uniformly sampled from $\{0, \ldots, T-1\}$.
</div>

## C.3 TPAUC in MIL with smoothed-max pooling and attention-based pooling

We can extend our results to smoothed-max pooling and attention-based pooling.

Smoothed-max Pooling. The smoothed-max pooling can be written as [45]:

$$
h _ {\mathbf {w}} (X) = \tau \log \left(\frac {1}{| X |} \sum_ {\mathbf {x} \in X} \exp (\phi (\mathbf {w}; \mathbf {x}) / \tau)\right),\tag{24}
$$

where $\tau > 0$ is a hyperparameter and $\phi ( \mathbf { w } ; \mathbf { x } ) = e ( \mathbf { w } _ { e } , \mathbf { x } ) ^ { \top } \mathbf { w } _ { c }$ is the prediction score for instance x. We can see that $h _ { \mathbf { w } } ( X )$ itself is a compositional function. To map the problem into TCCO, we define $\begin{array} { r } { h _ { i } ( \mathbf { w } ) = \frac { 1 } { | X _ { i } | } \sum _ { \mathbf { x } \in X _ { i } } \exp ( \phi ( \mathbf { w } ; \mathbf { x } ) / \bar { \tau } ) + C } \end{array}$ , where $C > 0$ is a constant. Then the objective function becomes

$$
\begin{array}{l} \min _ {\mathbf {w}, \mathbf {s} ^ {\prime}, \mathbf {s}} \frac {1}{n _ {+}} \sum_ {X _ {i} \in \mathcal {S} _ {+}} f _ {i} (\psi_ {i} (\mathbf {w}, s _ {i}), s ^ {\prime}), \\ \text {where} f _ {i} (g, s ^ {\prime}) = s ^ {\prime} + \frac {(g - s ^ {\prime}) _ {+}}{\alpha}, \\ \psi_ {i} (\mathbf {w}, s _ {i}) = \frac {1}{n _ {-}} \sum_ {X _ {j} \in \mathcal {S} _ {-}} s _ {i} + \frac {(\ell (\tau \log h _ {j} (\mathbf {w}) - \tau \log h _ {i} (\mathbf {w})) - s _ {i}) _ {+}}{\beta}, \end{array}\tag{25}
$$

In this case we define $\begin{array} { r } { g _ { i } ( \ell ( \mathbf { v } ) , s _ { i } ) = s _ { i } + \frac { ( \ell ( \tau \log v _ { 1 } - \tau \log v _ { 2 } ) - s _ { i } ) _ { + } } { \beta } } \end{array}$ and $h _ { i , j } ( \mathbf { w } ) = [ h _ { i } ( \mathbf { w } ) , h _ { j } ( \mathbf { w } ) ]$ We can still prove that $g _ { i } ( \ell ( \mathbf { v } ) , s _ { i } )$ is monotone w.r.t to each component of v. It is not difficult to prove that $\ell ( \tau \log v _ { 1 } - \tau \log v _ { 2 } )$ is weakly convex w.r.t v because τ log $v _ { 1 } - \tau$ log v<sub>2</sub> is a smooth mapping of v due to $\mathbf { v } \geq C$ and ℓ is a convex function [8]. As a result, since $g _ { i } ( \ell , s _ { i } )$ is non-decreasing and convex w.r.t to $\ell ,$ it is easy to prove that $g _ { i } ( \ell ( \mathbf { v } ) , s _ { i } )$ is weakly convex w.r.t v and is monotone (either non-decreasing or non-increasing) w.r.t to each component of v. Hence, assuming $h _ { i } ( \mathbf { w } )$ is a smooth and Lipchitz continuous function, we can prove that $g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } )$ is weakly convex w.r.t. to w.

Attention-based Pooling. Attention-based pooling was recently introduced for deep MIL [14], which aggregates the feature representations using attention, i.e.,

$$
E (\mathbf {w}; X) = \sum_ {\mathbf {x} \in X} \frac {\exp (g (\mathbf {w} ; \mathbf {x}))}{\sum_ {\mathbf {x} ^ {\prime} \in X} \exp (g (\mathbf {w} ; \mathbf {x} ^ {\prime}))} e (\mathbf {w} _ {e}; \mathbf {x})\tag{26}
$$

where $g ( \mathbf { w } ; \mathbf { x } )$ is a parametric function, $\mathbf { e . g . , } \ g ( \mathbf { w } ; \mathbf { x } ) = \mathbf { w } _ { a } ^ { \top } \mathrm { t a n h } ( V e ( \mathbf { w } _ { e } ; \mathbf { x } ) ) + C$ , where $V \in$ $\mathbb { R } ^ { m \times d _ { o } }$ and $\mathbf { w } _ { a } \in \mathbb { R } ^ { m }$ . Based on the aggregated feature representation, the bag level prediction can be computed by

$$
\begin{array}{l} h _ {\mathbf {w}} (\mathbf {w}, X) = (\mathbf {w} _ {c} ^ {\top} E (\mathbf {w}; X)) \\ \qquad = \left(\sum_ {\mathbf {x} \in X} \frac {\exp (g (\mathbf {w} ; \mathbf {x})) \delta (\mathbf {w} ; \mathbf {x})}{\sum_ {\mathbf {x} ^ {\prime} \in X} \exp (g (\mathbf {w} ; \mathbf {x} ^ {\prime}))}\right), \end{array}\tag{27}
$$

where $\delta ( \mathbf { w } ; \mathbf { x } ) = \mathbf { w } _ { c } ^ { \top } e ( \mathbf { w } _ { e } ; \mathbf { x } )$

We can see that $h _ { \mathbf { w } } ( X )$ itself is a compositional function. To map the problem into TCCO, we define $\begin{array} { r } { h _ { i } ^ { 1 } ( \mathbf { w } ) = \frac { 1 } { | X _ { i } | } \sum _ { \mathbf { x } \in X _ { i } } \exp ( g ( \mathbf { w } ; \mathbf { x } ) ) \delta ( \mathbf { w } ; \mathbf { x } ) } \end{array}$ , and $\begin{array} { r } { h _ { i } ^ { 2 } ( \mathbf { w } ) = \frac { 1 } { | X _ { i } | } \sum _ { \mathbf { x ^ { \prime } } \in X _ { i } } ^ { \cdot } \exp ( g ( \mathbf { w } ; \mathbf { x ^ { \prime } } ) ) } \end{array}$ . Assume $| \mathbf { w } _ { a } ^ { \top } \mathrm { t a n h } ( V e ( \mathbf { w } _ { e } ; \mathbf { x } ) ) | \le C _ { b }$ then $h _ { i } ^ { 2 } ( \mathbf { w } ) \geq \exp ( C - C _ { b } )$ . Then the objective function becomes

$$
\min _ {\mathbf {w}, \mathbf {s} ^ {\prime}, \mathbf {s}} \frac {1}{n _ {+}} \sum_ {X _ {i} \in \mathcal {S} _ {+}} f _ {i} (\psi_ {i} (\mathbf {w}, s _ {i}), s ^ {\prime}),
$$

$$
\text { where } f _ {i} (g, s ^ {\prime}) = s ^ {\prime} + \frac {(g - s ^ {\prime}) _ {+}}{\alpha}, \quad \psi_ {i} (\mathbf {w}, s _ {i}) = \frac {1}{n _ {-}} \sum_ {X _ {j} \in \mathcal {S} _ {-}} s _ {i} + \frac {(\ell (\frac {h _ {j} ^ {1} (\mathbf {w})}{h _ {j} ^ {2} (\mathbf {w})} - \frac {h _ {i} ^ {1} (\mathbf {w})}{h _ {i} ^ {2} (\mathbf {w})}) - s _ {i}) _ {+}}{\beta},\tag{28}
$$

In this case we define $\begin{array} { r l r } { g _ { i } ( \ell ( { \bf v } ) , s _ { i } ) } & { { } = } & { s _ { i } + \frac { ( \ell ( \frac { v _ { 3 } } { v _ { 4 } } - \frac { v _ { 1 } } { v _ { 2 } } ) - s _ { i } ) + } { \beta } } \end{array}$ and $\begin{array} { r l } { h _ { i , j } ( \mathbf { w } ) } & { { } = } \end{array}$ $[ h _ { i } ^ { 1 } ( { \bf w } ) , h _ { i } ^ { 2 } ( { \bf w } ) , h _ { j } ^ { 1 } ( { \bf w } ) , h _ { j } ^ { 2 } ( { \bf w } ) ]$ We can still prove that $g _ { i } ( \ell ( \mathbf { v } ) , s _ { i } )$ is monotone w.r.t to each component of v. It is not difficult to prove that $\begin{array} { r } { \ell \big ( \frac { v _ { 3 } } { v _ { 4 } } - \frac { v _ { 1 } } { v _ { 2 } } \big ) } \end{array}$ is weakly convex w.r.t v because $\begin{array} { r } { \frac { v _ { 3 } } { v _ { 4 } } \sim \frac { v _ { 1 } } { v _ { 2 } } } \end{array}$ is a smooth mapping of v when $v _ { 2 } , v _ { 4 }$ are lower bounded and ℓ is a convex function [8]. As a result, since $g _ { i } ( \ell , s _ { i } )$ is non-decreasing and convex w.r.t to $\ell ,$ it is easy to prove that $g _ { i } ( \ell ( \mathbf { v } ) , s _ { i } )$ is weakly convex w.r.t v and is monotone (either non-decreasing or non-increasing) w.r.t to each component of v. Hence, assuming $h _ { i } ^ { 1 } ( \mathbf { w } ) , h _ { i } ^ { 2 } ( \mathbf { w } )$ are smooth and Lipchitz continuous, we can prove that $g _ { i } ( h _ { i , j } ( \mathbf { w } ) , s _ { i } )$ is weakly convex w.r.t. to w.

## C.4 Convergence Analysis of TPAUC Maximization

## C.4.1 Convergence analysis for Algorithm 5

We first consider TPAUC maximization in the regular learning setting. Define $F ( \mathbf { w } , \mathbf { s } , s ^ { \prime } ) : =$ $\begin{array} { r } { \frac { 1 } { n _ { + } } \sum _ { { X _ { i } } \in { \mathcal { S } _ { + } } } f _ { i } ( \psi _ { i } ( \mathbf { w } , s _ { i } ) , s ^ { \prime } ) } \end{array}$ . Due to the weak-convexity of $F ( \mathbf { w } , \mathbf { s } , s ^ { \prime } )$ w.r.t. $( \mathbf { w } , \mathbf { s } , s ^ { \prime } )$ , we consider the following Moreau envelope and proximal map defined as

$$
F _ {\lambda} (\mathbf {w}, \mathbf {s}, s ^ {\prime}) = \min _ {\tilde {\mathbf {w}}, \tilde {\mathbf {s}}, \tilde {s} ^ {\prime}} F (\tilde {\mathbf {w}}, \tilde {\mathbf {s}}, \tilde {s} ^ {\prime}) + \frac {1}{2 \lambda} \left(\| \tilde {\mathbf {w}} - \mathbf {w} \| ^ {2} + \| \tilde {\mathbf {s}} - \mathbf {s} \| ^ {2} + \| \tilde {s} ^ {\prime} - s ^ {\prime} \| ^ {2}\right),
$$

$$
\mathrm{prox} _ {\lambda F} (\mathbf {w}, \mathbf {s}, s ^ {\prime}) = \underset {\tilde {\mathbf {w}}, \tilde {\mathbf {s}}, \tilde {s} ^ {\prime}} {\arg \min} F (\tilde {\mathbf {w}}, \tilde {\mathbf {s}}, \tilde {s} ^ {\prime}) + \frac {1}{2 \lambda} \left(\| \tilde {\mathbf {w}} - \mathbf {w} \| ^ {2} + \| \tilde {\mathbf {s}} - \mathbf {s} \| ^ {2} + \| \tilde {s} ^ {\prime} - s ^ {\prime} \| ^ {2}\right).
$$

Following the same proof of Lemma 4.5, we have the following error bound

Lemma C.3. Consider the update for $\begin{array} { c c c c } { { \{ u _ { i , t } } } & { { : } } & { { X _ { i } } } & { { \in } } & { { S _ { + } \} } } \end{array}$ in Algorithm 5. Assume $\psi _ { i } ( \mathbf { w } , s _ { i } )$ is $C _ { \psi } { - } L i p s h i t z$ continuous for all $X _ { i } ~ \in ~ S _ { + }$ . Assume $\begin{array} { r } { \mathbb { E } _ { t } \bar { [ \| G _ { t } \| ^ { 2 } ] } ~ \le ~ M ^ { 2 } } \end{array}$ and $\begin{array} { r } { \mathbb { E } _ { t } \big [ \| \frac { 1 } { B _ { 1 } } \sum _ { X _ { i } \in \mathcal { B } _ { 1 } ^ { t } } \partial _ { s } \psi _ { i } \big ( \mathbf { w } _ { t } , s _ { i , t } ; \mathcal { B } _ { 2 } ^ { t } \big ) \partial _ { u } f \big ( u _ { i , t } , s _ { t } ^ { \prime } \big ) e _ { i } \| ^ { 2 } \big ] \leq M ^ { 2 } } \end{array}$ , where $e _ { i }$ is the $n _ { + }$ -dimensional vector with 1 at the i-th entry and 0 everywhere else. With $\begin{array} { r } { \gamma = \frac { n _ { + } - B _ { 1 } } { B _ { 1 } ( 1 - \tau ) } + ( 1 - \tau ) } \end{array}$ and $\tau \leq \frac { 1 } { 2 }$ , we have

$$
\mathbb {E} \bigg [ \frac {1}{n _ {+}} \sum_ {X _ {i} \in \mathcal {S} _ {+}} \| u _ {i, t + 1} - \psi_ {i} (\mathbf {w} _ {t + 1}, s _ {i, t + 1}) \| \bigg ]
$$

$$
\leq (1 - \frac {B _ {1} \tau}{2 n _ {1}}) ^ {t + 1} \frac {1}{n} \sum_ {X _ {i} \in \mathcal {S} _ {+}} \| u _ {i, 0} - \psi_ {i} (\mathbf {w} _ {0}, s _ {i, 0}) \| + \frac {2 \tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {8 n _ {+} C _ {\psi} M \eta}{B _ {1} \tau^ {1 / 2}}.
$$

Then we have following convergence guarantee.

Theorem C.4. Under the assumptions given in Lemma C.1, with $\begin{array} { r } { \gamma = \frac { n _ { + } - B _ { 1 } } { B _ { 1 } ( 1 - \tau ) } + ( 1 - \tau ) , \tau = } \end{array}$ $\begin{array} { r } { \mathcal { O } ( B _ { 2 } \epsilon ^ { 4 } ) \le \frac { 1 } { 2 } , \eta = \mathcal { O } ( \frac { B _ { 1 } B _ { 2 } ^ { 1 / 2 } \epsilon ^ { 4 } } { n _ { + } } ) } \end{array}$ , and $\bar { \rho } = \rho _ { F } + \rho _ { \psi } C _ { f }$ , Algorithm 5 converges to an ϵ-stationary point of the Moreau envelope $\begin{array} { r } { F _ { 1 / \bar { \rho } } i n T = \mathcal { O } ( \frac { n _ { + } } { B _ { 1 } B _ { 2 } ^ { 1 / 2 } } \epsilon ^ { - 6 } ) } \end{array}$ iterations.

ProofofTheorem C.4. Define $\begin{array} { r } { \left( \hat { \mathbf { w } } _ { t } , \hat { \mathbf { s } } _ { t } , \hat { s } _ { t } ^ { \prime } \right) : = \operatorname { p r o x } _ { F / \bar { \rho } } ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) } \end{array}$ . For a given $X _ { i } \in S _ { + }$ , we have f<sub>i</sub>(ψ<sub>i</sub>(wˆ <sub>t</sub>, sˆ<sub>i,t</sub>), sˆ<sup>′</sup><sub>t</sub>) − f<sub>i</sub>(u<sub>i,t</sub>, s<sup>′</sup><sub>t</sub>)

$$
\begin{array}{r l} & f _ {i} (\psi_ {i} (\hat {\mathbf {w}} _ {t}, \hat {s} _ {i, t}), \hat {s} _ {t} ^ {\prime}) - f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \\ & \overset {(a)} {\geq} \partial_ {s ^ {\prime}} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) (\hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime}) + \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) (\psi_ {i} (\hat {\mathbf {w}} _ {t}, \hat {s} _ {i, t}) - u _ {i, t}) \\ & \overset {(b)} {\geq} \partial_ {s ^ {\prime}} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) (\hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime}) + \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \bigg [ \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}) - u _ {i, t} + \langle \partial_ {w} \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}), \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \rangle \\ & \quad - \frac {\rho_ {\psi}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \langle \partial_ {s _ {i}} \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}), \hat {s} _ {i, t} - s _ {i, t} \rangle - \frac {\rho_ {\psi}}{2} \| \hat {s} _ {i, t} - s _ {i, t} \| ^ {2} \bigg ] \\ & \overset {(c)} {\geq} \partial_ {s ^ {\prime}} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) (\hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime}) + \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) [ \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}) - u _ {i, t} ] + \langle \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {w} \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}), \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \rangle \\ & \quad + \langle \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {s _ {i}} \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}), \hat {s} _ {i, t} - s _ {i, t} \rangle - \frac {\rho_ {\psi} C _ {f}}{2} \left(\| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \| \hat {s} _ {i, t} - s _ {i, t} \| ^ {2}\right) \end{array}
$$

where (a) follows from the convexity of $f _ { i } , ( \mathsf { b } )$ follows from the monotonicity of $f _ { i } ( \cdot , s ^ { \prime } )$ and weak convexity of $\psi _ { i } , ( \mathrm { c } )$ is due to $0 \leq \partial _ { u } \dot { f } _ { i } ( \dot { u _ { i , t } } , s _ { t } ^ { \prime } ) \leq C _ { f }$ . Then it follows

$$
\begin{array}{l} \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \bigg [ \partial_ {s ^ {\prime}} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) (\hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime}) + \langle \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {w} \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}), \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \rangle \\ \quad + \langle \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {s _ {i}} \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}), \hat {s} _ {i, t} - s _ {i, t} \rangle \bigg ] \\ \leq \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \bigg [ f _ {i} (\psi_ {i} (\hat {\mathbf {w}} _ {t}, \hat {s} _ {i, t}), \hat {s} _ {t} ^ {\prime}) - f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) - \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \big [ \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}) - u _ {i, t} \big ] \\ \quad + \frac {\rho_ {\psi} C _ {f}}{2} \left(\| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \| \hat {s} _ {i, t} - s _ {i, t} \| ^ {2}\right) \bigg ] \end{array}\tag{29}
$$

Now we consider the change in the Moreau envelope:

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}, \mathbf {s} _ {t + 1}, s _ {t + 1} ^ {\prime}) ]} \\ & {= \mathbb {E} _ {t} \left[ \min _ {\tilde {\mathbf {w}}, \tilde {\mathbf {s}}, \tilde {s} ^ {\prime}} F (\tilde {\mathbf {w}}, \tilde {\mathbf {s}} _ {t}, \tilde {s} _ {t} ^ {\prime}) + \frac {\bar {\rho}}{2} \left(\| \tilde {\mathbf {w}} - \mathbf {w} _ {t + 1} \| ^ {2} + \| \tilde {\mathbf {s}} - \mathbf {s} _ {t + 1} \| ^ {2} + \| \tilde {s} ^ {\prime} - \mathbf {s} _ {t + 1} ^ {\prime} \| ^ {2}\right) \right]} \\ & {\leq \mathbb {E} _ {t} \left[ F (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) + \frac {\bar {\rho}}{2} \left(\| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t + 1} \| ^ {2} + \| \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t + 1} \| ^ {2} + \| \hat {s} _ {t} ^ {\prime} - s _ {t + 1} ^ {\prime} \| ^ {2}\right) \right]} \\ & {= F (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) + \mathbb {E} _ {t} \bigg [ \frac {\bar {\rho}}{2} \big (\| \hat {\mathbf {w}} _ {t} - (\mathbf {w} _ {t} - \eta G _ {t}) \| ^ {2} + \| \hat {\mathbf {s}} _ {t} - (\mathbf {s} _ {t} - \eta G _ {t} ^ {1}) \| ^ {2}} \\ & {\quad + \| \hat {s} _ {t} ^ {\prime} - (s _ {t} ^ {\prime} - \eta G _ {t} ^ {2}) \| ^ {2} \big) \bigg ]} \\ & {\leq F (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {\mathbf {t}}, \hat {s} _ {t} ^ {\prime}) + \frac {\bar {\rho}}{2} \left(\| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \| \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t} \| ^ {2} + \| \hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime} \| ^ {2}\right)} \\ & {\quad + \bar {\rho} \mathbb {E} _ {t} [ \eta \langle \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}, G _ {t} \rangle + \eta \langle \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t}, G _ {t} ^ {1} \rangle + \eta \langle \hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime}, G _ {t} ^ {2} \rangle ] + \frac {3 \eta^ {2} \bar {\rho} M ^ {2}}{2}} \\ & {= F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) + \bar {\rho} \mathbb {E} _ {t} [ \eta \langle \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}, G _ {t} \rangle + \eta \langle \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t}, G _ {t} ^ {1} \rangle + \eta \langle \hat {s _ {t}} ^ {\prime} - s _ {t} ^ {\prime}, G _ {t} ^ {2} \rangle ]} \\ & {\quad + \frac {3 \eta^ {2} \bar {\rho} M ^ {2}}{2}} \end{array}\tag{30}
$$

where for simplicity we denote $\begin{array} { r } { \begin{array} { r c l l } { G _ { t } ^ { 1 } } & { = } & { \frac { 1 } { B _ { 1 } } \sum _ { X _ { i } \in \mathcal { B } _ { 1 } ^ { t } } \partial _ { u } f _ { i } ( u _ { i , t } , s _ { t } ^ { \prime } ) \partial _ { \mathbf { s } } \psi _ { i } ( \mathbf { w } _ { t } , s _ { i , t } ; \mathcal { B } _ { 2 } ^ { t } ) } \end{array} } \end{array}$ and $G _ { t } ^ { 2 } \ =$ $\begin{array} { r } { \frac { 1 } { B _ { 1 } } \sum _ { X _ { i } \in { \mathcal { B } } _ { 1 } ^ { t } } \partial _ { s ^ { \prime } } f _ { i } \left( u _ { i , t } , s _ { t } ^ { \prime } \right) } \end{array}$ . The second inequality in the above derivation uses the bounds of $\mathbb { E } [ \| G _ { t } \| ^ { 2 } ] , \dot { \mathbb { E } } [ \| G _ { t } ^ { 1 } \| ^ { 2 } ]$ and $\mathbb { E } [ \| G _ { t } ^ { 2 } \| ^ { 2 } ]$ , which follow from the Lipschitz continuity and bounded variance assumptions and are denoted by M. Moreover, we have

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ \eta \langle \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}, G _ {t} \rangle + \eta \langle \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t}, G _ {t} ^ {1} \rangle + \eta \langle \hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime}, G _ {t} ^ {2} \rangle ]} \\ & {\quad = \eta \langle \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}, \mathbb {E} _ {t} [ G _ {t} ] \rangle + \eta \langle \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t}, \mathbb {E} _ {t} [ G _ {t} ^ {1} ] \rangle + \eta \langle \hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime}, \mathbb {E} _ {t} [ G _ {t} ^ {2} ] \rangle ,} \end{array}
$$

and

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ G _ {t} ] = \frac {1}{n _ {+}} \sum_ {X _ {i} \in \mathcal {S} _ {+}} \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {w} \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t})} \\ & {\mathbb {E} _ {t} [ G _ {t} ^ {1} ] = \frac {1}{n _ {+}} \sum_ {X _ {i} \in \mathcal {S} _ {+}} \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {\mathbf {s}} \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t})} \\ & {\mathbb {E} _ {t} [ G _ {t} ^ {2} ] = \frac {1}{n _ {+}} \sum_ {X _ {i} \in \mathcal {S} _ {+}} \partial_ {s ^ {\prime}} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}).} \end{array}
$$

Combining inequality 29 and 30 yields

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}, \mathbf {s} _ {t + 1}, s _ {t + 1} ^ {\prime}) ]} \\ & {\leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) + \frac {3 \eta^ {2} \bar {\rho} M ^ {2}}{2} + \frac {\bar {\rho} \eta}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \bigg [ f _ {i} (\psi_ {i} (\hat {\mathbf {w}} _ {t}, \hat {s} _ {i, t}), \hat {s} _ {t} ^ {\prime}) - f _ {i} (u _ {i, t}, s _ {t} ^ {\prime})} \\ & {- \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) [ \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}) - u _ {i, t} ] + \frac {\rho_ {\psi} C _ {f}}{2} \left(\| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \| \hat {s} _ {i, t} - s _ {i, t} \| ^ {2}\right) \bigg ]} \\ & {\leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) + \frac {3 \eta^ {2} \bar {\rho} M ^ {2}}{2} + \bar {\rho} \eta (F (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) - F (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}))} \\ & {+ \frac {\bar {\rho} \eta}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \bigg [ f _ {i} (\psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}), s _ {t} ^ {\prime}) - f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) - \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) [ \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}) - u _ {i, t} ]} \\ & {+ \frac {\rho_ {\psi} C _ {f}}{2} \left(\| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \| \hat {s} _ {i, t} - s _ {i, t} \| ^ {2}\right) \bigg ]} \end{array}\tag{31}
$$

Due to the ρ<sub>F</sub>-weak convexity of $F ( \mathbf { w } , \mathbf { s } , s ^ { \prime } )$ , we have $( \bar { \rho } - \rho _ { F } )$ -strong convexity of $\left( \mathbf { w } , \mathbf { s } , s ^ { \prime } \right) \mapsto$ $\begin{array} { r } { F ( \mathbf { w } , \mathbf { s } , s ^ { \prime } ) + \frac { \bar { \rho } } { 2 } \| ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) - ( \mathbf { w } , \mathbf { s } , s ^ { \prime } ) \| ^ { 2 } } \end{array}$ . Then it follows

$$
\begin{array}{r l} & F (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) - F (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) = \bigg [ F (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) + \frac {\bar {\rho}}{2} \| (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) - (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) \| ^ {2} \bigg ] \\ & \qquad - \bigg [ F (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) + \frac {\bar {\rho}}{2} \| (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) - (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} \bigg ] \\ & \qquad - \frac {\bar {\rho}}{2} \| (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) - (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) \| ^ {2} \\ & \qquad \leq (\frac {\rho_ {F}}{2} - \bar {\rho}) \| (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) - (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) \| ^ {2} \end{array}\tag{32}
$$

Plugging inequality 32 into inequality 31 yields

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}, \mathbf {s} _ {t + 1}, s _ {t + 1} ^ {\prime}) ]} \\ & {\leq \mathbb {E} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) ] + \frac {3 \eta^ {2} \bar {\rho} M ^ {2}}{2} + \bar {\rho} \eta (\frac {\rho_ {F}}{2} - \bar {\rho}) \| (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) - (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) \| ^ {2}} \\ & {\quad + \frac {\bar {\rho} \eta}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \bigg [ f _ {i} (\psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}), s _ {t} ^ {\prime}) - f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) - \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \big [ \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}) - u _ {i, t} \big ]} \\ & {\quad + \frac {\rho_ {\psi} C _ {f}}{2} \left(\| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \| \hat {s} _ {i, t} - s _ {i, t} \| ^ {2}\right) \bigg ]} \end{array}\tag{33}
$$

Set $\bar { \rho } = \rho _ { F } + \rho _ { \psi } C _ { f }$ . We have

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}, \mathbf {s} _ {t + 1}, s _ {t + 1} ^ {\prime}) ]} \\ & {\leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) + \frac {3 \eta^ {2} \bar {\rho} M ^ {2}}{2} - \frac {\bar {\rho} ^ {2} \eta}{2} \| (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) - (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) \| ^ {2}} \\ & {\quad + \frac {\bar {\rho} \eta}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \bigg [ f _ {i} (\psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}), s _ {t} ^ {\prime}) - f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) - \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) [ \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}) - u _ {i, t} ] \bigg ]} \\ & {\overset {(a)} {\leq} F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) + \frac {3 \eta^ {2} \bar {\rho} M ^ {2}}{2} - \frac {\eta}{2} \| \nabla \varphi_ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2}} \\ & {\quad + \frac {\bar {\rho} \eta}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \bigg [ f _ {i} (\psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}), s _ {t} ^ {\prime}) - f _ {i} (u _ {{i, t}}, s _ {{t}} ^ {\prime}) - \partial_ {u} f _ {i} (u _ {{i, t}}, s _ {{t}} ^ {\prime}) [ \psi_ {i} (\mathbf {w} _ {t}, s _ {{i, t}}) - u _ {{i, t}} ] \bigg ]} \end{array}
$$

where inequality (a) follows from Lemma 3.2.

Using the Lipschitz continuity of $f ,$ , we have

$$
\begin{array}{l} \mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}, \mathbf {s} _ {t + 1}, s _ {t + 1} ^ {\prime}) ] \\ \leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) + \frac {3 \eta^ {2} \bar {\rho} M ^ {2}}{2} - \frac {\eta}{2} \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} \\ \quad + \frac {\bar {\rho} \eta}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} 2 C _ {f} \| \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}) - u _ {i, t} \| \end{array}\tag{34}
$$

With the error bound from Lemma C.3, we have

$$
\begin{array}{l} \mathbb {E} \left[ \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| \psi_ {i} (\mathbf {w} _ {t}, s _ {i, t}) - u _ {i, t} \| \right] \leq (1 - \mu) ^ {t} \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| \psi_ {i} (\mathbf {w} _ {0}, s _ {i, 0}) - u _ {i, 0} \| + R \\ \text {with} \mu = \frac {B _ {1} \tau}{2 n _ {+}}, R = \frac {2 \tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 n _ {+} C _ {\psi} M \eta}{B _ {1} \tau^ {1 / 2}} + \frac {4 n _ {+} ^ {1 / 2} C _ {\psi} M \eta}{B _ {1} \tau^ {1 / 2}}. \text {Then} \\ \mathbb {E} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}, \mathbf {s} _ {t + 1}, s _ {t + 1} ^ {\prime}) ] \\ \leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) + \frac {3 \eta^ {2} \bar {\rho} M ^ {2}}{2} - \frac {\eta}{2} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} ] \\ + 2 C _ {f} \bar {\rho} \eta \left((1 - \mu) ^ {t} \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| \psi_ {i} (\mathbf {w} _ {0}, s _ {i, 0}) - u _ {i, 0} \| + R\right) \end{array}\tag{35}
$$

Taking summation from $t = 0$ to $T - 1$ yields

$$
\begin{array}{l} \mathbb {E} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {T}, \mathbf {s} _ {T}, s _ {T} ^ {\prime}) ] \\ \leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}, \mathbf {s} _ {0}, s _ {0} ^ {\prime}) + \frac {3 \eta^ {2} \bar {\rho} M ^ {2} T}{2} - \frac {\eta}{2} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} ] \\ \quad + 2 C _ {f} \bar {\rho} \eta \left(\sum_ {t = 0} ^ {T - 1} (1 - \mu) ^ {t} \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| \psi_ {i} (\mathbf {w} _ {0}, s _ {i, 0}) - u _ {i, 0} \| + R T\right) \\ \stackrel {(a)} {\leq} F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}, \mathbf {s} _ {0}, s _ {0} ^ {\prime}) + \frac {3 \eta^ {2} \bar {\rho} M ^ {2} T}{2} - \frac {\eta}{2} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nablate \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} ] \\ \quad + \frac {4 C _ {f} \bar {\rho} \eta}{\mu} \sum_ {X _ {i} \in S _ {+}} \frac {1}{n _ {+}} \| \psi_ {i} (\mathbf {w} _ {0}, s _ {i, 0}) - u _ {i, 0} \| + 2 C _ {f} \bar {\rho} \eta R T \end{array}\tag{36}
$$

where (a) uses $\textstyle \sum _ { t = 0 } ^ { T - 1 } ( 1 - \mu ) ^ { t } \leq { \frac { 1 } { \mu } }$

Lower bounding the left-hand-side by min ${ \bf { \omega } } _ { \bf { w } , s , } { \boldsymbol { s } } ^ { \prime } F _ { 1 / \bar { \rho } } ( { \bf { w } } , { \bf { s } } , s ^ { \prime } )$ , we obtain

$$
\begin{array}{l} \frac {1}{T} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} ] \\ \leq \frac {2}{\eta T} \bigg [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}, \mathbf {s} _ {0}, s _ {0} ^ {\prime}) - \min _ {\mathbf {w}, \mathbf {s}, s ^ {\prime}} F _ {1 / \bar {\rho}} (\mathbf {w}, \mathbf {s}, s ^ {\prime}) + \frac {3 \eta^ {2} \bar {\rho} M ^ {2} T}{2} \\ \quad + \frac {4 C _ {f} \bar {\rho} \eta}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| \psi_ {i} (\mathbf {w} _ {0}, s _ {i, 0}) - u _ {i, 0} \| + 2 C _ {f} \bar {\rho} \eta R T \bigg ] \\ \leq \frac {2 \Delta}{\eta T} + 3 \eta \bar {\rho} M ^ {2} + \frac {8 C _ {f} \bar {\rho}}{\mu T n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| \psi_ {i} (\mathbf {w} _ {0}, s _ {i, 0}) - u _ {i, 0} \| + 4 C _ {f} \bar {\rho} R \\ \leq \frac {C}{T} (\frac {1}{\eta} + \frac {1}{\mu}) + C (\eta + R) \end{array}
$$

where we assume $\begin{array} { r } { F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { 0 } , \mathbf { s } _ { 0 } , s _ { 0 } ^ { \prime } ) - \operatorname* { m i n } _ { \mathbf { w } , \mathbf { s } , s ^ { \prime } } F _ { 1 / \bar { \rho } } ( \mathbf { w } , \mathbf { s } , s ^ { \prime } ) \leq \Delta } \end{array}$ and

$$
C = \max \{8 \Delta , 1 2 \bar {\rho} M ^ {2}, 3 2 C _ {f} \bar {\rho} \sum_ {X _ {i} \in S _ {+}} \| \psi_ {i} (\mathbf {w} _ {0}, s _ {i, 0}) - u _ {i, 0} \|, 1 6 C _ {f} \bar {\rho} \}.
$$

Plugging the expression of µ and R yields

$$
\begin{array}{l} \frac {1}{T} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} ] \\ \leq \mathcal {O} \left(\frac {1}{T} (\frac {1}{\eta} + \frac {n _ {+}}{B _ {1} \tau}) + (\frac {\tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {n _ {+} \eta}{B _ {1} \tau^ {1 / 2}})\right) \end{array}
$$

Setting $\tau = \mathcal { O } ( B _ { 2 } \epsilon ^ { 4 } )$ and $\begin{array} { r } { \eta = \mathcal { O } ( \frac { B _ { 1 } B _ { 2 } ^ { 1 / 2 } } { n _ { + } } \epsilon ^ { 4 } ) } \end{array}$ , with $\begin{array} { r } { T = \mathcal { O } ( \frac { n _ { + } } { B _ { 1 } B _ { 2 } ^ { 1 / 2 } } \epsilon ^ { - 6 } ) } \end{array}$ iterations, we have

$$
\frac {1}{T} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} ] \leq \epsilon^ {2}.
$$

## C.4.2 Convergence analysis for Algorithm 6

We now consider MIL TPAUC maximization with mean pooling. Define $F ( \mathbf { w } , \mathbf { s } , s ^ { \prime } ) : =$ $\begin{array} { r } { \frac { 1 } { n _ { + } } \sum _ { X _ { i } \in { \mathcal S } _ { + } } f _ { i } ( g _ { i } ( h _ { j } ( \mathbf { w } ) - h _ { i } ( \mathbf { w } ) , s _ { i } ) , s ^ { \prime } ) } \end{array}$ . Due to the weak-convexity of $F ( \mathbf { w } , \mathbf { s } , s ^ { \prime } )$ w.r.t. $( \mathbf { w } , \mathbf { s } , s ^ { \prime } )$ we consider the following Moreau envelope and proximal map defined as

$$
\begin{array}{r l} & F _ {\lambda} (\mathbf {w}, \mathbf {s}, s ^ {\prime}) = \underset {\tilde {\mathbf {w}}, \tilde {\mathbf {s}}, \tilde {s} ^ {\prime}} {\min} F (\tilde {\mathbf {w}}, \tilde {\mathbf {s}}, \tilde {s} ^ {\prime}) + \frac {1}{2 \lambda} \left(\| \tilde {\mathbf {w}} - \mathbf {w} \| ^ {2} + \| \tilde {\mathbf {s}} - \mathbf {s} \| ^ {2} + \| \tilde {s} ^ {\prime} - s ^ {\prime} \| ^ {2}\right), \\ & \mathrm{prox} _ {\lambda F} (\mathbf {w}, \mathbf {s}, s ^ {\prime}) = \underset {\tilde {\mathbf {w}}, \tilde {\mathbf {s}}, \tilde {s} ^ {\prime}} {\arg \min} F (\tilde {\mathbf {w}}, \tilde {\mathbf {s}}, \tilde {s} ^ {\prime}) + \frac {1}{2 \lambda} \left(\| \tilde {\mathbf {w}} - \mathbf {w} \| ^ {2} + \| \tilde {\mathbf {s}} - \mathbf {s} \| ^ {2} + \| \tilde {s} ^ {\ast} - s ^ {\ast} \| ^ {2}\right). \end{array}
$$

Following the same proofs of Lemma A.3 and Lemma A.4, we have the following error bounds

Lemma C.5. Consider the update for $\{ v _ { i , t } : X _ { i } \in S _ { + } \cup S _ { - } \}$ in Algorithm 6. Assume $h _ { i } ( \mathbf { w } ; \boldsymbol { \xi } )$ is $C _ { h } { - } L i p s h i t z$ for all $X _ { i } \in S _ { + } \cup S _ { - }$ <sub>−</sub>, and $\mathbb { E } [ \| G _ { t } \| ^ { 2 } ] \ \leq \ M ^ { 2 }$ . With $\begin{array} { r } { \gamma _ { 1 } = \frac { n _ { + } - B _ { 1 } } { B _ { 1 } ( 1 - \tau _ { 1 } ) } + ( 1 - \tau _ { 1 } ) } \end{array}$

$$
\begin{array}{l} \gamma_ {2} = \frac {n _ {-} - B _ {2}}{B _ {2} (1 - \tau_ {1})} + (1 - \tau_ {1}) a n d \tau_ {1} \leq \frac {1}{2}, w e h a v e \\ \mathbb {E} \bigg [ \frac {1}{n _ {+}} \sum_ {X _ {i} \in \mathcal {S} _ {+}} \| v _ {i, t + 1} - h _ {i} (\mathbf {w} _ {t + 1}) \| \bigg ] \leq (1 - \frac {B _ {1} \tau_ {1}}{2 n _ {+}}) ^ {t + 1} \sum_ {X _ {i} \in \mathcal {S} _ {+}} \| v _ {i, 0} - h _ {i} (\mathbf {w} _ {t}) \| + 2 \tau_ {1} ^ {1 / 2} \sigma + \frac {4 n _ {+} C _ {h} M \eta}{B _ {1} \tau_ {1} ^ {1 / 2}} \\ \mathbb {E} \bigg [ \frac {1}{n _ {-}} \sum_ {X _ {j} \in \mathcal {S} _ {-}} \| v _ {j, t + 1} - h _ {j} (\mathbf {w} _ {t + 1}) \| \bigg ] \leq (1 - \frac {B _ {1} \tau_ {1}}{2 n _ {-}}) ^ {t + 1} \frac {1}{n _ {-}} \sum_ {X _ {j} \in \mathcal {S} _ {-}} \| v _ {j, 0} - h _ {j} (\mathbf {w} _ {t}) \| + 2 \tau_ {1} ^ {1 / 2} \sigma + \frac {4 n _ {-} C _ {h} M \eta}{B _ {1} \tau_ {1} ^ {1 / 2}} \\ \mathbb {E} \bigg [ \frac {1}{n _ {+}} \sum_ {X _ {i} \in \mathcal {S} _ {+}} \| v _ {i, t + 1} - h _ {i} (\mathbf {w} _ {t + 1}) \| ^ {2} \bigg ] \leq (1 - \frac {B _ {1} \tau_ {1}}{2 n _ {+}}) ^ {2 (t + 1)} \frac {1}{n _ {+}} \sum_ {X _ {i} \in \mathcal {S} _ {+}} \| v _ {i, 0} - h _ {i} (\mathbf {w} _ {t}) \| ^ {2} + 4 \tau_ {1} \sigma^ {2} + \frac {1 6 n _ {+} ^ {2} C _ {h} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau_ {1}} \\ \mathbb {E} \bigg [ \frac {1}{n _ {-}} \sum_ {X _ {j} \in \mathcal {S} _ {-}} \| v _ {j, t + 1} - h _ {j} (\mathbf {w} _ {t + 1}) \| ^ {2} \bigg ] \leq (1 - \frac {B _ {1} \tau_ {1}}{2 n _ {-}}) ^ {2 (t + 1)} \frac {1}{n _ {-}} \sum_ {X _ {j} \in \mathcal {S} _ {-}} \| v _ {j, 0} - h _ {j} (\mathbf {w} _ {t}) \| ^ {2} + 4 \tau_ {1} \sigma^ {2} + \frac {1 6 n _ {-} ^ {2} C _ {h} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau_ {1}}. \end{array}
$$

Lemma C.6. Consider update for $\{ u _ { i , t } : X _ { i } \in S _ { + } \}$ in Algorithm 6. Assume $g _ { i } ( v _ { i j } , s _ { i } )$ is $C _ { g ^ { - } }$ Lipshitz w.r.t. $( v _ { i j } , s _ { i } )$ for all $X _ { i } \in S _ { + }$ and $X _ { j } \in S _ { - }$ . With $\begin{array} { r } { \gamma _ { 3 } = \frac { n _ { + } - B _ { 1 } } { B _ { 1 } ( 1 - \tau _ { 2 } ) } + ( 1 - \tau _ { 2 } ) } \end{array}$ and $\begin{array} { r } { \tau _ { 2 } \leq \frac { 1 } { 2 } } \end{array}$ , we have

$$
\begin{array}{l} \mathbb {E} \left[ \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| u _ {i, t + 1} - \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (v _ {j, t + 1} - v _ {i, t + 1}, s _ {i, t + 1}) \| \right] \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {+}}) ^ {t + 1} \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| u _ {i, 0} - \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (v _ {j, 0} - v _ {i, 0}, s _ {i, 0}) \| + 2 \tau_ {2} ^ {1 / 2} \sigma \\ \quad + C _ {2} \frac {n _ {+}}{B _ {1}} (\frac {B _ {1} ^ {1 / 2}}{n _ {+} ^ {1 / 2}} + \frac {B _ {2} ^ {1 / 2}}{n _ {-} ^ {1 / 2}}) \frac {\tau_ {1}}{\tau_ {2} ^ {1 / 2}} + C _ {2} \frac {n _ {+}}{B _ {1}} (\frac {n _ {+} ^ {1 / 2}}{B _ {1} ^ {1 / 2}} + \frac {n _ {-} ^ {1 / 2}}{B _ {2} ^ {1 / 2}}) \frac {\eta}{\tau_ {2} ^ {1 / 2}} + C _ {2} \frac {n _ {+} ^ {1 / 2} \eta}{B _ {1} \tau_ {2} ^ {1 / 2}} \end{array}
$$

where $C _ { 2 }$ is a constant defined in the proof.

Then we have the following covnergence guarantee.

$$
(1 - \tau_ {1}), \quad \gamma_ {2} = \frac {n _ {2} - B _ {2}}{B _ {2} (1 - \tau_ {1})} + (1 - \tau_ {1}), \quad \gamma_ {3} = \frac {n _ {1} - B _ {1}}{B _ {1} (1 - \tau_ {2})} + (1 - \tau_ {2}), \quad \tau_ {1} =
$$

$$
\gamma_ {1} = \frac {n _ {1} - B _ {1}}{B _ {1} (1 - \tau_ {1})} +
$$

$$
T \geq \mathcal {O} \left(\max \left\{\max \{\frac {n _ {+}}{B _ {1}}, \frac {n _ {-}}{B _ {2}} \} \max \{\frac {1}{B _ {3} ^ {1 / 2}}, \frac {n _ {+} ^ {1 / 2}}{B _ {1} ^ {1 / 2}} \max \{\frac {B _ {1} ^ {1 / 4}}{n _ {+} ^ {1 / 4}}, \frac {B _ {2} ^ {1 / 4}}{n _ {-} ^ {1 / 4}} \} \frac {1}{B _ {2} ^ {1 / 4}} \}, \frac {n _ {+}}{B _ {1}} \max \{\frac {n _ {+} ^ {1 / 2}}{B _ {1} ^ {1 / 2}}, \frac {n _ {-} ^ {1 / 2}}{B _ {2} ^ {1 / 2}} \} \frac {1}{B _ {2} ^ {1 / 2}} \right\} \epsilon^ {- 6}\right)
$$

iterations, Algorithm 6 gives ϵ-stationary point to the Moreau envelope, i.e.,

$$
\frac {1}{T} \sum_ {t = 0} ^ {T - 1} \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} \leq \epsilon^ {2}.
$$

where $\bar { \rho } = \rho _ { F } + \rho _ { g } C _ { f } + 8 \rho _ { g } C _ { f } C _ { h } + C _ { f } C _ { g } L _ { h } .$

Proof of Theorem C.7. Consider the change in the Moreau envelope:

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {t + 1}, \mathbf {s} _ {t + 1}, s _ {t + 1} ^ {\prime}) ]} \\ & {= \mathbb {E} _ {t} \left[ \min _ {\tilde {\mathbf {w}}, \tilde {\mathbf {s}}, \tilde {s} ^ {\prime}} F (\tilde {\mathbf {w}}, \tilde {\mathbf {s}} _ {t}, \tilde {s} _ {t} ^ {\prime}) + \frac {\bar {\rho}}{2} \left(\| \tilde {\mathbf {w}} - \mathbf {w} _ {t + 1} \| ^ {2} + \| \tilde {\mathbf {s}} - \mathbf {s} _ {t + 1} \| ^ {2} + \| \tilde {s} ^ {\prime} - \mathbf {s} _ {t + 1} ^ {\prime} \| ^ {2}\right) \right]} \\ & {\leq \mathbb {E} _ {t} \left[ F (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) + \frac {\bar {\rho}}{2} \left(\| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t + 1} \| ^ {2} + \| \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t + 1} \| ^ {2} + \| \hat {s} _ {t} ^ {\prime} - s _ {t + 1} ^ {\prime} \| ^ {2}\right) \right]} \\ & {= F (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) + \mathbb {E} _ {t} \bigg [ \frac {\bar {\rho}}{2} \big (\| \hat {\mathbf {w}} _ {t} - (\mathbf {w} _ {t} - \eta G _ {t}) \| ^ {2} + \| \hat {\mathbf {s}} _ {t} - (\mathbf {s} _ {t} - \eta G _ {t} ^ {1}) \| ^ {2}} \\ & {\quad + \| \hat {s} _ {t} ^ {\prime} - (s _ {t} ^ {\prime} - \eta G _ {t} ^ {2}) \| ^ {2} \big) \bigg ]} \\ & {\leq F (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {\mathbf {t}}, \hat {s} _ {t} ^ {\prime}) + \frac {\bar {\rho}}{2} \left(\| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} + \| \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t} \| ^ {2} + \| \hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime} \| ^ {2}\right)} \\ & {\quad + \bar {\rho} \mathbb {E} _ {t} [ \eta \langle \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}, G _ {t} \rangle + \eta \langle \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t}, G _ {t} ^ {1} \rangle + \eta \langle \hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime}, G _ {t} ^ {2} \rangle ] + \frac {3 \eta^ {2} \bar {\rho} M ^ {2}}{2}} \\ & {= F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) + \bar {\rho} \mathbb {E} _ {t} [ \eta \langle \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}, G _ {t} \rangle + \eta \langle \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t}, G _ {t} ^ {1} \rangle + \eta \langle \hat {s _ {t}} ^ {\prime} - s _ {t} ^ {\prime}, G _ {t} ^ {2} \rangle ]} \\ & {\quad + \frac {3 \eta^ {2} \bar {\rho} M ^ {2}}{2}} \end{array}\tag{37}
$$

where for simplicity we denote $\begin{array} { r } { G _ { t } ^ { 2 } = \frac { 1 } { B _ { 1 } } \sum _ { i \in \mathcal { B } _ { 1 } ^ { t } } \partial _ { s ^ { \prime } } f _ { i } ( u _ { i , t } , s _ { t } ^ { \prime } ) } \end{array}$ , and $G _ { t } ^ { 1 }$ is a $n _ { + }$ -dimensional vector whose i-th coordinate is defined as

$$
\left\{ \begin{array}{l l} \frac {1}{B _ {1}} \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \left[ \frac {1}{B _ {2}} \sum_ {X _ {j} \in \mathcal {B} _ {2} ^ {t}} \partial_ {s _ {i}} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) \right], & X _ {i} \in \mathcal {B} _ {1} ^ {t} \\ 0, & X _ {i} \not \in \mathcal {B} _ {1} ^ {t} \end{array} \right..
$$

The second inequality in the above derivation uses the bounds of $\mathbb { E } [ \| G _ { t } \| ^ { 2 } ] , \mathbb { E } [ \| G _ { t } ^ { 1 } \| ^ { 2 } ]$ and $\mathbb { E } [ \| G _ { t } ^ { 2 } \| ^ { 2 } ]$ which follow from the Lipschitz continuity and bounded variance assumptions and are denoted by M.

Note that

$$
\begin{array}{l} \text {that} \\ \mathbb {E} _ {t} [ G _ {t} ] \\ = \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \left[ \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \partial_ {v} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) (\nabla h _ {i} (\mathbf {w}) - \nabla h _ {j} (\mathbf {w})) \right] \\ \mathbb {E} _ {t} [ G _ {t} ^ {1} ] = \frac {1}{n _ {+}} \sum_ {X _ {i} \in \mathcal {S} _ {+}} \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \left[ \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \partial_ {\mathbf {s}} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) \right] \\ \mathbb {E} _ {t} [ G _ {t} ^ {2} ] = \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \partial_ {s ^ {\prime}} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \end{array}
$$

Define $\begin{array} { r } { \big ( \hat { \mathbf { w } } _ { t } , \hat { \mathbf { s } } _ { t } , \hat { s } _ { t } ^ { \prime } \big ) : = \operatorname { p r o x } _ { F / \bar { \rho } } \big ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } \big ) } \end{array}$ . For a given $i \in \{ 1 , \ldots , m \}$ , we have

$$
\begin{array} { l } f _ { i } ( \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } g _ { i } ( h _ { j } ( \hat { \mathbf { w } } _ { t } ) - h _ { i } ( \hat { \mathbf { w } } _ { t } ) , \hat { s } _ { i , t } ) , \hat { s } _ { t } ^ { \prime } ) - f _ { i } ( u _ { i , t } , s _ { t } ^ { \prime } ) \\ \overset { ( a ) } { \geq } \partial _ { s ^ { \prime } } f _ { i } ( u _ { i , t } , s _ { t } ^ { \prime } ) ( \hat { s } _ { t } ^ { \prime } - s _ { t } ^ { \prime } ) + \partial _ { u } f _ { i } ( u _ { i , t } , s _ { t } ^ { \prime } ) ( \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } g _ { i } ( h _ { j } ( \hat { \mathbf { w } } _ { t } ) - h _ { i } ( \hat { \mathbf { w } } _ { t } ) , \hat { s } _ { i , t } ) - u _ { i , t } ) \\ \overset { ( b ) } { \geq } \partial _ { s ^ { \prime } } f _ { i } ( u _ { i , t } , s _ { t } ^ { \prime } ) ( \hat { s } _ { t } ^ { \prime } - s _ { t } ^ { \prime } ) + \partial _ { u } f _ { i } ( u _ { i , t } , s _ { t } ^ { \left( 1 / 2 \right) } ) \Big [ \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } g _ { i } ( v _ { j , t } - v _ { i , t } , s _ { i , t}) - u _ { i , t } \\ + \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } \langle \partial _ { v } g _ { i } ( v _ { j , t } - v _ { i , t } , s _ { i , t} ) , ( h _ { j } ( \hat { \mathbf { w } } _ { t } ) - h _ { i } ( \hat { \mathbf { w } } _ { t} ) ) - ( v _ { j , t } - v _ { i , t} ) ) \rangle \\ - \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } \frac {\rho _ { g }}{ 2} \| ( h _ { j } ( \hat { \mathbf { w } } _ { t } ) - h _ { i } ( \hat { \mathbf { w } } _ { t} ) ) - ( v _ { j , t} - v _ { i , t} ) ) \| ^ { 2} \\ + \langle \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } \partial _ { s _ { i }} g _ { i } ( v _ { j , t } - v _ { i , t} ) , s _ { i , t} , \hat { s } _ { i , t} - s _ { i , t} \rangle - \frac {\rho _ { g }}{ 2} \| \hat { s } _ { i , t} - s _ { i , t} \| ^ { 2 } \Big ] \\ \overset { ( c ) } { \geq } \partial _ { s ^ { \prime } } f _ { i } ( u _ { i , t } , s _ { t } ^ { \prime }) ( \hat { s } _ { t } ^ { \prime } - s _ { t } ^ { \prime } ) + \partial _ { u } f _ { i } ( u _ { i , t } , s _ { t } ^ { \prime }) \Big [ \frac { 1 } { n _ {-} } \sum _ { X _ { j } \in S _ {-} } g _ { i } ( v _ { j , t } - v _ { i , t} , s _ { i , t}) - u _ { i , t } \Big ] \\ + \frac { 1 } { n _ {-} } \sum _ { X _ { j } \in S _ {-} } \underbrace {\langle \partial _ { u } f _ { i } ( u _ { i , t} , s _ { t } ^ { \prime }) \partial _ { v } g _ { i } ( v _ { j , t} - v _ { i , t} , s _ { i , t}) , ( h _ { j } ( \hat { \mathbf { w } } _ { t } ) - h _ { i } ( \hat { \mathbf { w } } _ { t} ) ) - ( v _ { j , t} - v _ { i , t} ) ) \rangle} _ A _ 1 \\ + \frac { 1 } { n _ {-} } \sum _ { X _ { j } \in S _ {-} } \langle \partial _ { u } f _ { i } ( u _ { i , t} , s _ { t } ^ { \prime }) \partial _ { s _ { i }} g _ { i } ( v _ { j , t} - v _ { i , t} , s _ { i , t}) , \hat { s } _ { i , t} - s _ { i , t} \rangle \\ - \frac 1{n_{-}}\sum_ {\substack{X_{j}\in S_{-}\\ }}\frac {\rho_{ g} C_{f}}{2}\| (h_{j} (\hat {\mathbf{w}}_{t}) - h_{i} (\hat {\mathbf{w}}_{t})) - (v_{j,t}- v_{i,t}) \| ^{ 2}-\frac {\rho_{ g} C_{f}}{2}\| \hat{s}_{i,t}-s_{i,t}\| ^{ 2} \\ \end{array}\tag{38}
$$

where (a) follows from the convexity of $f _ { i } , ( \mathfrak { b } )$ follows from the monotonicity of $f _ { i } ( \cdot , s ^ { \prime } )$ and weak convexity of $g _ { i } , \left( \mathrm { c } \right)$ is due to $0 \leq \partial _ { u } \cdot { \bf \dot { f } } _ { i } ( u _ { i , t } , s _ { t } ^ { \prime } ) \leq C _ { f }$

The L -smoothness assumption of $h _ { i } ( \mathbf { w } ) - h _ { j } ( \mathbf { w } )$ for all i, w implies

$$
\begin{array}{l} h _ {i} (\hat {\mathbf {w}} _ {t}) - h _ {j} (\hat {\mathbf {w}} _ {t}) \\ \geq h _ {i} (\mathbf {w} _ {t}) - h _ {j} (\mathbf {w} _ {t}) + \langle (\nabla h _ {i} (\mathbf {w} _ {t}) - \nabla h _ {j} (\mathbf {w} _ {t})), \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \rangle - \frac {L _ {h}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} \end{array}\tag{39}
$$

$$
\begin{array}{l} \text {Since} \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {v} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) \geq 0, \text {we bound} A _ {1} \text {as following} \\ A _ {1} = \langle \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {v} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}), (h _ {j} (\hat {\mathbf {w}} _ {t}) - h _ {i} (\hat {\mathbf {w}} _ {t})) - (v _ {j, t} - v _ {i, t})) \rangle \\ \overset {(a)} {\geq} \langle \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {v} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}), (h _ {i} (\mathbf {w} _ {t}) - h _ {j} (\mathbf {w} _ {t})) - (v _ {j, t} - v _ {i, t})) \rangle \\ - \langle \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {v} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}), \frac {L _ {h}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} \rangle \\ + \langle \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {v} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) (\nabla h _ {i} (\mathbf {w} _ {t}) - \nabla h _ {j} (\mathbf {w} _ {t})), \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \rangle \\ \overset {(b)} {\geq} - C _ {f} C _ {g} [ \| h _ {i} (\mathbf {w} _ {t}) - v _ {i, t} \| + \| h _ {j} (\mathbf {w} _ {t}) - v _ {j, t} \| ] - \frac {C _ {f} C _ {g} L _ {h}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} \\ + \langle \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {\ell} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) (\nabla h _ {i} (\mathbf {w} _ {t}) - \nabla h _ {j} (\mathbf {w} _ {t})), \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \rangle \end{array}
$$

where inequality (a) follows from inequality 39, (b) follows from the Lipschitz continuity and monotone assumptions on $f _ { i } , g _ { i } , h _ { i } , h _ { j }$ . Then plugging the new formulation of $A _ { 1 }$ back to inequality 38

yields

$$
\begin{array}{l} f _ {i} (\frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (h _ {j} (\hat {\mathbf {w}} _ {t}) - h _ {i} (\hat {\mathbf {w}} _ {t}), \hat {s} _ {i, t}), \hat {s} _ {t} ^ {\prime}) - f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \\ \geq \partial_ {s ^ {\prime}} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) (\hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime}) + \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \left[ \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) - u _ {i, t} \right] \\ + \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} [ - C _ {f} C _ {g} [ \| h _ {i} (\mathbf {w} _ {t}) - v _ {i, t} \| + \| h _ {j} (\mathbf {w} _ {t}) - v _ {j, t} \| ] ] - \frac {C _ {f} C _ {g} L _ {h}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2} \\ + \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \langle \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {v} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) (\nabla h _ {i} (\mathbf {w} _ {t}) - \nabla h _ {j} (\mathbf {w} _ {t})), \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \rangle \\ + \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \langle \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \partial_ {s _ {i}} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}), \hat {s} _ {i, t} - s _ {i, t} \rangle \\ - \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \frac {\rho_ {g} C _ {f}}{2} \| (h _ {j} (\hat {\mathbf {w}} _ {t}) - h _ {i} (\hat {\mathbf {w}} _ {t})) - (v _ {j, t} - v _ {i, t}) \| ^ {2} - \frac {\rho_ {g} C _ {f}}{2} \| \hat {s} _ {i, t} - s _ {i, t} \| ^ {2} \end{array}
$$

Taking average over i ∈ S<sub>+</sub> gives

$$
\begin{array}{r l} & {\frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} f _ {i} (\frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (h _ {j} (\hat {\mathbf {w}} _ {t}) - h _ {i} (\hat {\mathbf {w}} _ {t}), \hat {s} _ {i, t}), \hat {s} _ {t} ^ {\prime}) - f _ {i} (u _ {i, t}, s _ {t} ^ {\prime})} \\ & {\geq \langle \mathbb {E} _ {t} [ G _ {t} ^ {2} ], \hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime} \rangle + \langle \mathbb {E} _ {t} [ G _ {t} ], \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \rangle + \langle \mathbb {E} _ {t} [ G _ {t} ^ {1} ], \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t} \rangle} \\ & {\quad + \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \bigg [ \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) - u _ {i, t} \bigg ]} \\ & {\quad - C _ {f} C _ {g} \left[ \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| h _ {i} (\mathbf {w} _ {t}) - v _ {i, t} \| + \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \| h _ {j} (\mathbf {w} _ {t}) - v _ {j, t} \| \right] - \frac {C _ {f} C _ {g} L _ {h}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2}} \\ & {\quad - \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \frac {\rho_ {g} C _ {f}}{2} \| (h _ {j} (\hat {\mathbf {w}} _ {t}) - h _ {i} (\hat {\mathbf {w}} _ {t})) - (v _ {j, t} - v _ {i, t}) \| ^ {2} - \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \frac {\rho_ {g} C _ {f}}{2} \| \hat {s} _ {i, t} - s _ {i, t} \| ^ {2}} \end{array}
$$

It follows

$$
\begin{array}{r l} & {\langle \mathbb {E} _ {t} [ G _ {t} ^ {2} ], \hat {s} _ {t} ^ {\prime} - s _ {t} ^ {\prime} \rangle + \langle \mathbb {E} _ {t} [ G _ {t} ], \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \rangle + \langle \mathbb {E} _ {t} [ G _ {t} ^ {1} ], \hat {\mathbf {s}} _ {t} - \mathbf {s} _ {t} \rangle} \\ & {\leq \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \bigg [ f _ {i} (\frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (h _ {j} (\hat {\mathbf {w}} _ {t}) - h _ {i} (\hat {\mathbf {w}} _ {t}), \hat {s} _ {i, t}), \hat {s} _ {t} ^ {\prime}) - f _ {i} (u _ {i, t}, s _ {t} ^ {\prime})} \\ & {\quad - \partial_ {u} f _ {i} (u _ {i, t}, s _ {t} ^ {\prime}) \bigg [ \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) - u _ {i, t} \bigg ]} \\ & {\quad + \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \frac {\rho_ {g} C _ {f}}{2} \| (h _ {j} (\hat {\mathbf {w}} _ {t}) - h _ {i} (\hat {\mathbf {w}} _ {t})) - (v _ {j, t} - v _ {i, t}) \| ^ {2} + \frac {\rho_ {g} C _ {f}}{2} \| \hat {s} _ {i, t} - s _ {i, t} \| ^ {2} \bigg ]} \\ & {\quad + C _ {f} C _ {g} \bigg [ \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| h _ {i} (\mathbf {w} _ {t}) - v _ {i, t} \| + \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \| h _ {j} (\mathbf {w} _ {t}) - v _ {j, t} \| \bigg ] + \frac {C _ {f} C _ {g} L _ {h}}{2} \| \hat {\mathbf {w}} _ {t} - \mathbf {w} _ {t} \| ^ {2}} \end{array}\tag{40}
$$

Combining inequality 37 and 40 yields

$$
\begin{array} { l } \mathbb { E } _ { t } [ F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t + 1 } , \mathbf { s } _ { t + 1 } , s _ { t + 1 } ^ { \prime } ) ] \\ = F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) + \bar { \rho } \eta \left[ \langle \hat { \mathbf { w } } _ { t } - \mathbf { w } _ { t } , \mathbb { E } _ { t } [ G _ { t } ] \rangle + \langle \hat { \mathbf { s } } _ { t } - \mathbf { s } _ { t } , \mathbb { E } _ { t } [ G _ { t } ^ { 1 } ] \rangle + \langle \hat { s } _ { t } ^ { \prime } - s _ { t } ^ { \prime } , \mathbb { E } _ { t } [ G _ { t } ^ { 2 } ] \rangle \right] \\ + \frac { 3 \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } \\ \stackrel { ( a ) } { \leq } F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) + \frac { 3 \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } + \bar { \rho } \eta \Bigg \{ \frac { 1 } { n _ { + } } \sum _ { X _ { i } \in S _ { + } } \bigg [ F _ { i } ( \hat { s } _ { t } ^ { \prime } , \hat { \mathbf { w } } _ { t } , \hat { s } _ { i , t } ) - F _ { i } ( s _ { t } ^ { \prime } , \mathbf { w } _ { t } , s _ { i , t } ) \\ + C _ { f } C _ { g } \frac { 1 } { n _ {-} } \sum _ { X _ { j } \in S _ {-} } \left[ \| h _ { i } ( \mathbf { w } _ { t } ) - v _ { i , t } \| + \| h _ { j } ( \mathbf { w } _ { t} ) ) - v _ { j , t } \| \right] \\ + C _ { f } \bigg \| \frac { 1 } { n _ {-} } \sum _ { X _ { j } \in S _ {-} } g _ { i } ( v _ { j , t } - v _ { i , t } , s _ { i , t}) - u _ { i , t } \bigg \| + C _ { f } \bigg \| \frac { 1 } { n _ {-} } \sum _ { X _ { j } \in S _ {-} } g _ { i } ( v _ { j , t } - v _ { i , t } , s _ { i , t}) - u _ { i , t } \bigg \| \\ + \frac { 1 } { n _ {-} } \sum _ { X _ { j } \in S _ {-} } \rho _ { g } C _ { f } \big [ \| ( h _ { i } ( \hat { \mathbf { w } } _ { t } ) - v _ { i , t } \| ^ { 2 } + \| h _ { j } ( \hat { \mathbf { w } } _ { t} ) ) - v _ { j , t } \| ^ { 2 } \big ] + \frac {\rho _ { g } C _ { f }}{ 2} \| \hat { s } _ { i , t } - s _ { i , t } \| ^ { 2 } \\ + C _ { f } C _ { g } \bigg [ \frac { 1 } { n _ { +} } \sum _ { X _ { i } \in S _ { +} } \| h _ { i } ( \mathbf { w } _ { t } ) - v _ { i , t } \| + \frac { 1 } { n _ {-} } \sum _ { X _ { j } \in S _ {-} } \| h _ { j } ( \mathbf { w } _ { t } ) - v _ { j , t } \| \bigg ] + \frac { C _ { f } C _ { g } L _ { h }}{ 2} \| \hat {\mathbf { w }} _ { t } - \mathbf { w } _ { t } \| ^ { 2} \\ = F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) + \frac { 3 \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } + \bar { \rho } \eta ( F ( \hat {\mathbf { w }} _ { t } , \hat {\mathbf { s }} _ { t } , \hat {\mathbf {\Delta}} s _ { t} ^ {\prime} ) - F ( \mathbf {{ w }} _ { t }, \mathbf {{ s }} _ { t }, s _ { t} ^ {\prime})) \\ +   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]    ] ] ] ] \\ +   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   ]     .     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]     ]    ]    ]    ] ] ] \\ +   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   ]     .     ]     ]     ]     ]     ]     ]     ]     ]     ]     |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |      |    |
] . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
$$

where (a) follows from the Lipschitz continuity of $f _ { i } , g _ { i } , h _ { i } , h _ { j }$ and inequality 40.

(41)

Due to the $\rho _ { F ^ { - } }$ weak convexity of $F ( \mathbf { w } , \mathbf { s } _ { i } , s ^ { \prime } )$ , we have $( \bar { \rho } - \rho _ { F } )$ -strong convexity of $\left( \mathbf { w } , s _ { i } , s ^ { \prime } \right) \mapsto$ $\begin{array} { r } { F ( \mathbf { w } , \mathbf { s } , s ^ { \prime } ) + \frac { \bar { \rho } } { 2 } \| ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) - ( \mathbf { w } , \mathbf { s } , s ^ { \prime } ) \| ^ { 2 } } \end{array}$ . Then it follows

$$
\begin{array}{r l} & F (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) - F _ {i} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) = \bigg [ F _ {i} (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) + \frac {\bar {\rho}}{2} \| (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) - (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) \| ^ {2} \bigg ] \\ & \qquad - \bigg [ F _ {i} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) + \frac {\bar {\rho}}{2} \| (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) - (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} \bigg ] \\ & \qquad - \frac {\bar {\rho}}{2} \| (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) - (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) \| ^ {2} \\ & \qquad \leq (\frac {\rho_ {F}}{2} - \bar {\rho}) \| (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) - (\hat {\mathbf {w}} _ {t}, \hat {\mathbf {s}} _ {t}, \hat {s} _ {t} ^ {\prime}) \| ^ {2} \end{array}\tag{42}
$$

Plugging inequality 42 back into 41, we obtain

$$
\begin{array} { r l } & { \mathbb { E } _ { t } [ F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t + 1 } , \mathbf { s } _ { t + 1 } , s _ { t + 1 } ^ { \prime } ) ] } \\ & { \leq F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) + \frac { 3 \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } + \bar { \rho } \eta \Bigg \{ \frac { 1 } { n _ { + } } \sum _ { X _ { i } \in S _ { + } } \bigg [ ( \frac { \rho _ { F } } { 2 } - \bar { \rho } ) \| ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) - ( \hat { \mathbf { w } } _ { t } , \hat { \mathbf { s } } _ { t } , \hat { s } _ { t } ^ { \prime } ) \| ^ { 2 } } \\ & { + \frac { 2 C _ { f } C _ { g } } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } \big [ \| h _ { i } ( \mathbf { w } _ { t } ) - v _ { i , t } \| + \| h _ { j } ( \mathbf { w } _ { t } ) - v _ { j , t } \| \big ] } \\ & { + \frac { 2 \rho _ { g } C _ { f } } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } \big [ \| h _ { i } ( \mathbf { w } _ { t } ) - v _ { i , t } \| ^ { 2 } + \| h _ { j } ( \mathbf { w } _ { t } ) - v _ { j , t } \| ^ { 2 } \big ] } \\ &  + 2 C _ { f } \bigg \| \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } g _ { i } ( v _ { j , t } - v _ { i , t } , s _ { i , t } ) - u _ { i , t } \bigg \| + \frac { \rho _ { g } C _ { f } } { 2 } \| \hat { s } _ { i , t } - s _ { i , t } \| ^ { 2 } \bigg ] + ( 4 \rho _ { g } C _ { f } C _ { h } + \frac { C _ { f } C _ { g } L _ { h } } { 2 } ) \| \hat { \mathbf { w } } _ { t } - \mathbf { w } _ { t } \| ^ { 2 } \Bigg \} \\ &  \leq F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) + \frac { 3 \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } + \bar { \rho } \eta \bigg \{ \frac { 1 } { n _ { + } } \sum _ { X _ { i } \in S _ { + } } \bigg [ - \frac { \bar { \rho } } { 2 } \| ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) - ( \hat { \mathbf { w } } _ { t } , \hat { \mathbf { s } } _ { t } , \hat { s } _ { t } ^ { \prime} ) \| ^ { 2 } \\ &  + \frac { C _ { 1 } } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } \big [ \| h _ { i } ( \mathbf { w } _ { t } ) - v _ { i , t } \| + \| h _ { j } ( \mathbf { w } _ { t } ) - v _ { j , t } \| + \| h _ { i } ( \mathbf { w } _ { t } ) - v _ { i , t } \| ^ { 2 } + \| h _ { j } ( \mathbf { w } _ { t} ) - v _ { j , t} \| ^ { 2 } \big ] \\ &  + C _ { 1 } \bigg \| \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } g _ { i } ( v _ { j , t } - v _ { i , t} , s _ { i , t} ) - u _ { i , t} \| \bigg ] \Bigg \} \\ & {\overset {(b)} {\leq} F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } , \mathbf { s} _ { t} , s _ { t} ^ { \prime} ) + \frac { 3 \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } - \frac { \eta}{ 2} \| \nabla F _ { 1 / \bar {\rho} } ( \mathbf { w} _ { t }, \mathbf { s} _ { t} , s _ { t} ^ {\prime} ) \| ^ { 2 }} \\ & \quad + \frac {\bar {\rho} \eta C _ { 1 }}{ n _ { + n - }} \sum _ { X _ { i} \in S _ { + }} \sum _ { X _ { j} \in S _ {-} } [ \| h _ { i } ( \mathbf { w} _ { t} ) - v _ { i , t} \| + \| h _ { j } ( \mathbf { w} _ { t} ) - v _ { j , t} \| + \| h _ { i } ( \mathbf { w} _ { t} ) - v _ { i , t} \| ^ { 2 } + \| h _ { j } ( \mathbf { w} _ { t} ) - v _ { j , t} \| ^ { 2 } ] \\ & {\quad + \frac {\bar {\rho} \eta C _ { 1}}{ n _ { + }} \sum _ { X _ { i} \in S _ {\pm+}} \bigg \| \frac 1{n_ {-}} \sum_ {\substack X _ {\pm} \\ X_{\pm}}} g _ {\boldsymbol i} (v _ {\boldsymbol j, t} - v _ {\boldsymbol i, t}, s _ {\boldsymbol i, t}) - u _ {\boldsymbol i, t} \| . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
$$

where in inequality (a) we use $\begin{array} { r c l } { \bar { \rho } } & { = } & { \rho _ { F } + \rho _ { g } C _ { f } + 8 \rho _ { g } C _ { f } C _ { h } + C _ { f } C _ { g } L _ { h } } \end{array}$ and C<sub>1</sub> = max $\{ 2 C _ { f } C _ { g } , \bar { 2 } \rho _ { g } C _ { f } ^ { ' } , 2 C _ { f } \}$ }, and inequality (b) uses Lemma 3.2.

With general error bounds

$$
\begin{array}{l} \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \mathbb {E} [ \| h _ {i} (\mathbf {w} _ {t}) - v _ {i, t} \| ] \leq (1 - \mu_ {1}) ^ {t} \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| h _ {i} (\mathbf {w} _ {0}) - v _ {i, 0} \| + R _ {1}, \\ \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \mathbb {E} [ \| h _ {j} (\mathbf {w} _ {t}) - v _ {j, t} \| ] \leq (1 - \mu_ {2}) ^ {t} \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \| h _ {j} (\mathbf {w} _ {0}) - v _ {j, 0} \| + R _ {2}, \\ \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \mathbb {E} [ \| h _ {i} (\mathbf {w} _ {t}) - v _ {i, t} \| ^ {2} ] \leq (1 - \mu_ {1}) ^ {t} \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| h _ {i} (\mathbf {w} _ {0}) - v _ {i, 0} \| ^ {2} + R _ {3}, \\ \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \mathbb {E} [ \| h _ {j} (\mathbf {w} _ {t}) - v _ {j, t} \| ^ {2} ] \leq (1 - \mu_ {2}) ^ {t} \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \| h _ {j} (\mathbf {w} _ {0}) - v _ {j, 0} \| ^ {2} + R _ {4}, \\ \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \mathbb {E} \bigg [ \bigg \| \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) - u _ {i, t} \bigg \| \bigg ] \\ \leq (1 - \mu_ {3}) ^ {t} \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \bigg \| \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (v _ {i, 0} - v _ {j, 0}, s _ {i, 0}) - u _ {i, 0} \bigg \| + R _ {5}, \end{array}
$$

we have

$$
\begin{array} { r l } & \text {we have} \\ & \mathbb { E } [ F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t + 1 } , \mathbf { s } _ { t + 1 } , s _ { t + 1 } ^ { \prime } ) ] \\ & \leq \mathbb { E } [ F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) ] + \frac { 3 \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } - \frac { \eta } { 2 } \mathbb { E } [ \| \nabla F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) \| ^ { 2 } ] \\ & \quad + \bar { \rho } \eta C _ { 1 } \bigg [ ( 1 - \mu _ { 1 } ) ^ { t } \frac { 1 } { n _ { + } } \sum _ { X _ { i } \in S _ { + } } \| h _ { i } ( \mathbf { w } _ { 0 } ) - v _ { i , 0 } \| + ( 1 - \mu _ { 2 } ) ^ { t } \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } \| h _ { j } ( \mathbf { w } _ { 0 } ) - v _ { j , 0 } \| \\ & \quad + ( 1 - \mu _ { 1 } ) ^ { t } \frac { 1 } { n _ { + } } \sum _ { X _ { i } \in S _ { + } } \| h _ { i } ( \mathbf { w } _ { 0 } ) - v _ { i , 0 } \| ^ { 2 } + ( 1 - \mu _ { 2 } ) ^ { t } \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } \| h _ { j } ( \mathbf { w } _ { 0 } ) - v _ { j , 0 } \| ^ { 2 } \\ & \quad + ( 1 - \mu _ { 3 } ) ^ { t } \frac { 1 } { n _ { + } } \sum _ { X _ { i } \in S _ { + } } \left\| \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } g _ { i } ( v _ { i , 0 } - v _ { j , 0 } , s _ { i , 0 } ) - u _ { i , 0 } \right\| + R _ { 1 } + R _ { 2 } + R _ { 3 } + R _ { 4 } + R _ { 5 } \bigg ] \\ & \leq \mathbb { E } [ F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) ] + \frac { 3 \eta ^ { 2 } \bar { \rho } M ^ { 2 } } { 2 } - \frac { \eta } {2 } \mathbb { E } [ \| \nabla F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , s _ { t } ^ { \prime } ) \| ^ { 2 } ] \\ & \quad + \bar { \rho } \eta C _ { 1 } \bigg [ ( 1 - \mu _ { m i n } ) ^ { t } \bigg ( \frac { 1 } { n _ { + } } \sum _ { X _ { i } \in S _ { + } } \| h _ { i } ( \mathbf { w } _ { 0 } ) - v _ { i , 0 } \| + \frac { 1 } { n _ { - } } \sum _ { X _ { j } \in S _ { - } } \| h _ { j } ( \mathbf { w } _ { 0 } ) - v _ { j , 0 } \| \\ & \quad + \frac { 1 } { n _ { + } } \sum _ { X _ { i } \in S _ { + } } \| h _ { i } ( \mathbf { w } _ { 0 } ) - v _ { i , 0 } \| ^ { 2 } + \frac { 1 } { n _ {-} } \sum _ { X _ { j } \in S _ {-} } \| h _ { j } ( \mathbf { w } _ { 0 } ) - v _ { j , 0 } \| ^ { 2 } \\ & \quad + \frac { 1 } { n _ { +} }\sum _ { X _ { i } \in S _ { + } }\left\| \frac { 1}{ n _ {-} }\sum _ { X _ { j } \in S _ {-} }\left. g _ { i }( v _ { i , 0} - v _ { j , 0 }, s _ { i , 0 }) - u _ { i , 0 }\right\|\right) + R _ { 1 } + R _ { 2 } + R _ { 3 } + R _ { 4 } + R _ { 5 }\bigg ] . \end{array}
$$

where $\mu _ { m i n } = \operatorname* { m i n } \{ \mu _ { 1 } , \mu _ { 2 } , \mu _ { 3 } \}$

Taking summation from $t = 0$ to $T - 1$ yields

$$
\begin{array}{l} \mathbb {E} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {T}, \mathbf {s} _ {T}, s _ {T} ^ {\prime}) ] \\ \leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}, \mathbf {s} _ {0}, s _ {0} ^ {\prime}) + \frac {3 \eta^ {2} \bar {\rho} M ^ {2} T}{2} - \frac {\eta}{2} \sum_ {t = 0} ^ {T - 1} \mathbb {E} [ \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} ] \\ \quad + \bar {\rho} \eta C _ {1} \bigg [ \sum_ {t = 0} ^ {T - 1} (1 - \mu_ {m i n}) ^ {t} \bigg (\frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| h _ {i} (\mathbf {w} _ {0}) - v _ {i, 0} \| + \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \| h _ {j} (\mathbf {w} _ {0}) - v _ {j, 0} \| \\ \quad + \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| h _ {i} (\mathbf {w} _ {0}) - v _ {i, 0} \| ^ {2} + \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \| h _ {j} (\mathbf {w} _ {0}) - v _ {j, 0} \| ^ {2} \\ \quad + \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \left\| \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (v _ {i, 0} - v _ {j, 0}, s _ {i, 0}) - u _ {i, 0} \right\| \bigg) + T (R _ {1} + R _ {2} + R _ {3} + R _ {4} + R _ {5}) \bigg ] \\ \leq F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}, \mathbf {s} _ {0}, s _ {0} ^ {\prime}) + \frac {3 \eta^ {2} \bar {\rho} M ^ {2} T}{2} - \frac {\eta}{2} \sum_ {t = 0} ^ {T - 1} \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} \\ \quad + \bar {\rho} \eta C _ {1} \bigg [ \frac {\Delta_ {0}}{\mu_ {m i n}} + T (R _ {1} + R _ {2} + R _ {3} + R _ {4} + R _ {5}) \bigg ] \\ w h e r e w e u s e \sum_ {t = 0} ^ {T - 1} (1 - \mu_ {m i n}) ^ {t} \leq \frac {1}{\mu_ {m i n}} a n d d e f i n e c o n s t a n t \Delta_ {0} s u c h t h a t \\ \quad \Bigg (\frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| h _ {i} (\mathbf {w} _ {0}) - v _ {i, 0} \| + \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \| h _ {j} (\mathbf {w} _ {0}) - v _ {j. 0} \| \\ \quad + \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \| h _ {i} (\mathbf {w} _ {0}) - v _ {i, 0} \| ^ {2} + \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} \| h _ {j} (\mathbf {W} _ {0}) - v _ {j. 0} \| ^ {2} \\ \quad + \frac {1}{n _ {+}} \sum_ {X _ {i} \in S _ {+}} \left\| \frac {1}{n _ {-}} \sum_ {X _ {j} \in S _ {-}} g _ {i} (v _ {i, 0} - v _ {j, 0}, s _ {i, 0}) - u_{i, 0} \right\| \Bigg) \leq \Delta_ {0}. \end{array}
$$

Then it follows

$$
\begin{array}{l} \frac {1}{T} \sum_ {t = 0} ^ {T - 1} \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} \\ \leq \frac {2}{\eta T} \left[ F _ {1 / \bar {\rho}} (\mathbf {w} _ {0}, \mathbf {s} _ {0}, s _ {0} ^ {\prime}) - \mathbb {E} [ F _ {1 / \bar {\rho}} (\mathbf {w} _ {T}, \mathbf {s} _ {T}, s _ {T} ^ {\prime}) ] + \frac {3 \eta^ {2} \bar {\rho} M ^ {2} T}{2} \right. \\ \quad + \bar {\rho} \eta C _ {1} \left[ \frac {\Delta_ {0}}{\mu_ {m i n}} + T (R _ {1} + R _ {2} + R _ {3} + R _ {4} + R _ {5}) \right] \\ \leq \frac {2 \Delta}{\eta T} + (2 + \frac {n _ {+}}{B _ {1}}) \eta \bar {\rho} M ^ {2} + \frac {2 \bar {\rho} C _ {1} \Delta_ {0}}{\mu_ {m i n} T} + 2 \bar {\rho} C _ {1} (R _ {1} + R _ {2} + R _ {3} + R _ {4} + R _ {5}) \\ = \mathcal {O} \left(\frac {1}{T} (\frac {1}{\eta} + \frac {1}{\mu_ {m i n}}) + \eta + R _ {1} + R _ {2} + R _ {3} + R _ {4} + R _ {5}\right) \end{array}
$$

where we define constant $\Delta$ such that $F _ { 1 / \bar { \rho } } ( \mathbf w _ { 0 } , \mathbf s _ { 0 } , s _ { 0 } ^ { \prime } ) - \mathbb { E } [ F _ { 1 / \bar { \rho } } ( \mathbf { w } _ { T } , \mathbf { s } _ { T } , s _ { T } ^ { \prime } ) ] \le \Delta$

With MSVR updates for $v _ { i , t }$ and $u _ { i , t } ,$ following from Lemma C.5 and Lemma $\mathrm { C } . 6 ,$ , we have

$$
\begin{array}{r l} & {\mu_ {1} = \frac {B _ {1} \tau_ {1}}{2 n _ {+}}, \quad \mu_ {2} = \frac {B _ {1} \tau_ {1}}{2 n _ {-}}, \quad \mu_ {3} = \frac {B _ {1} \tau_ {2}}{2 n _ {+}}} \\ & {R _ {1} = \frac {2 \tau_ {1} ^ {1 / 2} \sigma}{B _ {3} ^ {1 / 2}} + \frac {4 n _ {+} C _ {h} M \eta}{B _ {1} \tau_ {1} ^ {1 / 2}}, \quad R _ {2} = \frac {2 \tau_ {1} ^ {1 / 2} \sigma}{B _ {3} ^ {1 / 2}} + \frac {4 n _ {-} C _ {h} M \eta}{B _ {2} \tau_ {1} ^ {1 / 2}}} \\ & {R _ {3} = \frac {4 \tau_ {1} \sigma^ {2}}{B _ {3}} + \frac {1 6 n _ {+} ^ {2} C _ {h} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau_ {1}}, \quad R _ {4} = \frac {4 \tau_ {1} \sigma^ {2}}{B _ {3}} + \frac {1 6 n _ {-} ^ {2} C _ {h} ^ {2} M ^ {2} \eta^ {2}}{B _ {2} ^ {2} \tau_ {1}}} \\ & {R _ {5} = \frac {2 \tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + C _ {2} \frac {n _ {+}}{B _ {1}} (\frac {B _ {1} ^ {1 / 2}}{n _ {+} ^ {1 / 2}} + \frac {B _ {2} ^ {1 / 2}}{n _ {-} ^ {1 / 2}}) \frac {\tau_ {1}}{\tau_ {2} ^ {1 / 2}} + C _ {2} \frac {n _ {+}}{B _ {1}} (\frac {n _ {+} ^ {1 / 2}}{B _ {1} ^ {1 / 2}} + \frac {n _ {-} ^ {1 / 2}}{B _ {2} ^ {1 / 2}}) \frac {\eta}{\tau_ {2} ^ {1 / 2}} + C _ {2} \frac {n _ {+} ^ {1 / 2} \eta}{B _ {1} \tau_ {2} ^ {1 / 2}}} \end{array}
$$

Then we have

$$
\begin{array}{r l} & {\frac {1}{T} \sum_ {t = 0} ^ {T - 1} \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2}} \\ & {\quad \leq \mathcal {O} \Bigg (\frac {1}{T} (\frac {1}{\eta} + \frac {1}{\mu_ {m i n}}) + (\frac {\tau_ {1} ^ {1 / 2}}{B _ {3} ^ {1 / 2}} + \frac {\tau_ {2} ^ {1 / 2}}{B _ {2} ^ {1 / 2}}) \sigma} \\ & {\qquad + \frac {n _ {+} \eta}{B _ {1} \tau_ {1} ^ {1 / 2}} + \frac {n _ {-} \eta}{B _ {2} \tau_ {1} ^ {1 / 2}} + \frac {n _ {+}}{B _ {1}} \max \{\frac {B _ {1} ^ {1 / 2}}{n _ {+} ^ {1 / 2}}, \frac {B _ {2} ^ {1 / 2}}{n _ {-} ^ {1 / 2}} \} \frac {\tau_ {1}}{\tau_ {2} ^ {1 / 2}} + \frac {n _ {+}}{B _ {1}} \max \{\frac {n _ {+} ^ {1 / 2}}{B _ {1} ^ {1 / 2}}, \frac {n _ {-} ^ {1 / 2}}{B _ {2} ^ {1 / 2}} \} \frac {\eta}{\tau_ {2} ^ {1 / 2}} \Bigg)} \\ & {\mathrm{Setting}} \\ & {\tau_ {1} = \mathcal {O} \left(\min \left\{B _ {3}, \frac {B _ {1}}{n _ {+}} \min \{\frac {n _ {+} ^ {1 / 2}}{B _ {1} ^ {1 / 2}}, \frac {n _ {-} ^ {1 / 2}}{B _ {2} ^ {1 / 2}} \} B _ {2} ^ {1 / 2} \right\} \epsilon^ {4}\right), \quad \tau_ {2} = \mathcal {O} (B _ {2} \epsilon^ {4}),} \\ & {\eta = \mathcal {O} \left(\min \left\{\min \{\frac {B _ {1}}{n _ {+}}, \frac {B _ {2}}{n _ {-}} \} \min \{B _ {3} ^ {1 / 2}, \frac {B _ {1} ^ {1 / 2}}{n _ {+} ^ {1 / 2}} \min \{\frac {n _ {+} ^ {1 / 4}}{B _ {1} ^ {1 / 4}}, \frac {n _ {-} ^ {1 / 4}}{B _ {2} ^ {1 / 4}} \} B _ {2} ^ {1 / 4} \}, \frac {B _ {1}}{n _ {+}} \min \{\frac {B _ {1} ^ {1 / 2}}{n _ {+} ^ {1 / 2}}, \frac {B _ {2} ^ {1 / 2}}{n _ {-} ^ {1 / 2}} \} B _ {3} ^ {1 / 2} \right\} \epsilon^ {4}\right),} \\ & {\mathrm{Thenwith}} \\ & T \geq \mathcal {O} \left(\max \left\{\max \{\frac {n _ {+}}{B _ {1}}, \frac {n _ {-}}{B _ {2}} \} \max \{\frac {1}{B _ {3} ^ {1 / 2}}, \frac {n _ {+} ^ {1 / 2}}{B _ {1} ^ {1 / 2}} \max \{\frac {B _ {1} ^ {1 / 4}}{n _ {+} ^ {1 / 4}}, \frac {B _ {2} ^ {1 / 4}}{n _ {-} ^ {1 / 4}} \} \frac {1}{B _ {2} ^ {1 / 4}} \}, \frac {n _ {+}}{B _ {1}} \max \{\frac {n _ {+} ^ {1 / 2}}{B _ {1} ^ {1 / 2}}, \frac {n _ {-} ^ {1 / 2}}{B _ {2} ^ {1 / 2}} \} \frac {1}{B _ {2} ^ {1 / 2}} \right\} \epsilon^ {- 6}\right). \end{array}
$$

iterations, we have

$$
\frac {1}{T} \sum_ {t = 0} ^ {T - 1} \| \nabla F _ {1 / \bar {\rho}} (\mathbf {w} _ {t}, \mathbf {s} _ {t}, s _ {t} ^ {\prime}) \| ^ {2} \leq \epsilon^ {2}.
$$

## D Proofs of Lemmas and Propositions

## D.1 Additional Proposition

Proposition D.1. Consider a Lipschitz continuousfunction $f : O \to \mathbb { R }$ where $O \subset \mathbb { R } ^ { d }$ is an open set. Assume f to be non-increasing (resp. non-decreasing) with respect to each element in the input, then all subgradients of f are element-wise non-positive (resp. non-negative).

ProofofProposition D.1. Let $D$ be the subset of O where f is differentiable. By Theorem 9.60 in [24], a Lipschitz continuous function $f : O \to \mathbb { R }$ , where $\check { O } \subset \mathbb { R } ^ { d }$ is an open set, is differentiable almost everywhere, i.e., D is dense in $O .$ Then by Theorem 9.61 in [24], the subdifferential of $f$ at x is defined as

$$
\partial f (x) = \operatorname{con} \left\{v \mid \exists x _ {k} \rightarrow x \text {   with   } x _ {k} \in D, \nabla f (x _ {k}) \rightarrow v \right\},
$$

where con denotes the convex hull. If we assume that $f$ is non-increasing with respect to each element in the input, then $\nabla f ( x ) \leq 0$ (element-wise) for all differentiable points $x \in D$ . It implies that the all vectors in $\{ v \vert \exists x _ { k } \ \stackrel { } { \to } \ x$ with $x _ { k } \in D , \nabla f ( x _ { k } ) \to v \}$ are element-wise non-positive. Therefore, all subgradients of $f$ are element-wise non-positive. On the other hand, if we assume that $f$ is non-decreasing, one may follow the same argument and conclude that all subgradients of $f$ are element-wise non-negative. □

For functions $f : O  \mathbb { R } ^ { m }$ where $O \subset \mathbb { R } ^ { d }$ is an open set, one may write $f = ( f _ { 1 } , \dots , f _ { m } )$ and apply the above proposition for each $f _ { k } , k = 1 , \ldots , m$

## D.2 Proofs of Proposition 4.2 and Proposition 4.4

To prove Proposition 4.2 and Proposition 4.4, we first present the following proposition on the weak-convexity of composition functions.

Proposition D.2. Assume $f : \mathbb { R } ^ { d }  \mathbb { R }$ is $\rho _ { 1 }$ -weakly-convex and C<sub>1</sub>-Lipschitz continuous, $g : \mathbb { R } ^ { d } $ $\mathbb { R } ^ { d }$ is C<sub>2</sub>-Lipschitz continuous, and either ofthefollowings holds:

$f ( \cdot )$ is monotone and $g ( \cdot )$ is $L _ { 2 }$ -smooth;

$f ( \cdot )$ is non-decreasing and $g ( \cdot )$ is L<sub>2</sub>-weakly-convex,

then f ◦ g is ρ˜-weakly-convex with $\tilde { \rho } = \sqrt { d } L _ { 2 } C _ { 1 } + \rho _ { 1 } C _ { 2 } ^ { 2 } .$

Proof of Proposition D.2. The weak convexity of $f$ implies

$$
\begin{array}{c} f (g (y)) \geq f (g (x)) + v ^ {\top} (g (y) - g (x)) - \frac {\rho_ {1}}{2} \| g (y) - g (x) \| ^ {2} \\ \geq f (g (x)) + v ^ {\top} (g (y) - g (x)) - \frac {\rho_ {1} C _ {2} ^ {2}}{2} \| x - y \| ^ {2} \end{array}
$$

where $v \in \partial f ( g ( x ) )$ . Moreover, due to the smoothness of $g ( \cdot )$ (or weakly-convexity of $g ( \cdot )$ , then only the second inequality holds), we have

$$
\begin{array}{l} g (y) - g (x) \leq \nabla g (x) ^ {\top} (y - x) + \mathbf {v} \left(\frac {L _ {2}}{2} \| x - y \| ^ {2}\right), \\ g (y) - g (x) \geq \nabla g (x) ^ {\top} (y - x) - \mathbf {v} \left(\frac {L _ {2}}{2} \| x - y \| ^ {2}\right). \end{array}\tag{43}
$$

where ${ \bf v } ( e )$ denotes a d-dimensional vector with value e on each dimensions. We first assume that $f$ is non-increasing, then we may use the first inequality in (43) and the Lipschitz continuity of $g$ to get

$$
\begin{array}{r l} & f (g (y)) \geq f (g (x)) + v ^ {\top} \left[ \nabla g (x) ^ {\top} (y - x) + \mathbf {v} \left(\frac {L _ {2}}{2} \| x - y \| ^ {2}\right) \right] - \frac {\rho_ {1} C _ {2} ^ {2}}{2} \| x - y \| ^ {2} \\ & \quad \geq f (g (x)) + v ^ {\top} \nabla g (x) ^ {\top} (y - x) + v ^ {\top} \mathbf {v} \left(\frac {L _ {2}}{2} \| x - y \| ^ {2}\right) - \frac {\rho_ {1} C _ {2} ^ {2}}{2} \| x - y \| ^ {2} \\ & \quad \geq f (g (x)) + \langle v ^ {\top} \nabla g (x) ^ {\top} (y - x) - \frac {\sqrt {d} L _ {2} C _ {1} + \rho_ {1} C _ {2} ^ {2}}{2} \| x - y \| ^ {2}. \end{array}
$$

On the other hand, if we assume $f$ is non-decreasing, the same result follows from the second inequality in (43). Thus $f \circ g$ is $\tilde { \rho } \cdot$ -weakly-convex with $\tilde { \rho } _ { g } = \sqrt { d } L _ { 2 } C _ { 1 } + \rho _ { 1 } C _ { 2 } ^ { 2 }$ □

Proof of Proposition 4.2. Under Assumption 4.1, Proposition D.2 directly implies the $\rho _ { F } \mathrm { - w e a k \mathrm { - } }$ convexity of $F ( \mathbf { w } )$ with $\rho _ { F } = \sqrt { d _ { 1 } } \rho _ { g } C _ { f } ^ { - } + \rho _ { f } C _ { g } ^ { 2 }$ □

ProofofProposition 4.4. Under Assumption 4.3, we first apply Proposition D.2 to the composite function $g _ { i } \big ( h _ { i , j } ( \cdot ) \big )$ ) and obtain its $\rho _ { \tilde { g } } = \sqrt { d _ { 2 } } L _ { h } C _ { g } + \rho _ { g } C _ { h } ^ { 2 }$ -weak-convexity. To show it Lipschitz continuity, we use the Lipschitz continuity of $g _ { i }$ and $h _ { i , j }$ to obtain

$$
\left\| g _ {i} \left(h _ {i, j} (\mathbf {w})\right) - g _ {i} \left(h _ {i, j} (\tilde {\mathbf {w}})\right) \right\| ^ {2} \leq C _ {g} ^ {2} C _ {h} ^ {2} \| \mathbf {w} - \tilde {\mathbf {w}} \| ^ {2}.
$$

Thus $g _ { i } ( h _ { i , j } ( \mathbf { w } ) )$ is $C _ { \tilde { g } } = C _ { g } C _ { h }$ -Lipschitz-continuous

Since we assume $f _ { i } ( \cdot )$ is non-decreasing, $\rho _ { f } \mathrm { - w e a k l y - c o n v e x }$ and $C _ { f ^ { - } } \mathbf { I }$ Lipschitz continuous, and $g _ { i } ( h _ { i , j } ( \cdot ) )$ is $\rho _ { \tilde { g } } - \mathbf { \bar { v } }$ eakly-convex and $C _ { \tilde { g } ^ { - \mathbf { L } } }$ ipschitz-continuous, we apply Proposition D.2 again to conclude that $F ( \cdot )$ is $\rho _ { F } = \sqrt { d _ { 1 } } \rho _ { \tilde { g } } C _ { f } + \rho _ { f } C _ { \tilde { g } } ^ { 2 }$ -weakly-convex. □

## D.3 Proof of Lemma 4.5

ProofofLemma 4.5. With $\begin{array} { r } { \gamma = \frac { n _ { 1 } - B _ { 1 } } { B _ { 1 } ( 1 - \tau ) } + ( 1 - \tau ) , \tau \leq \frac { 1 } { 2 } } \end{array}$ , MSVR update gives recursive error bound [15]

$$
\begin{array}{r l} & {\mathbb {E} [ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau}{n _ {1}}) \mathbb {E} [ \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} ] + \frac {2 \tau^ {2} B _ {1} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {8 n _ {1} C _ {g} ^ {2}}{B _ {1}} \mathbb {E} [ \| \mathbf {w} _ {t} - \mathbf {w} _ {t + 1} \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau}{n _ {1}}) \mathbb {E} [ \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} ] + \frac {2 \tau^ {2} B _ {1} \sigma^ {2}}{n _ {1} B _ {\mathrm{2}}} + \frac {8 n _ {1} C _ {g} ^ {2}}{B _ {\mathrm{1}}} \eta^ {2} \mathbb {E} [ \| G _ {t} \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau}{2 n _ {1}}) ^ {2} \mathbb {E} [ \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} ] + \frac {2 \tau^ {2} B _ {1} \sigma^ {2}}{n _ {1} B _ {\mathrm{2}}} + \frac {8 n _ {1} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {\mathrm{1}}}} \end{array}
$$

Applying this inequality recursively, we obtain

$$
\begin{array}{l} \mathbb {E} [ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| ^ {2} ] \\ \leq (1 - \frac {B _ {1} \tau}{2 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| ^ {2} + \sum_ {j = 0} ^ {t} (1 - \frac {B _ {1} \tau}{2 n _ {1}}) ^ {2 (t - j)} \left(\frac {2 \tau^ {2} B _ {1} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {8 n _ {+} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1}}\right) \\ \leq (1 - \frac {B _ {1} \tau}{2 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| ^ {2} + \frac {4 \tau \sigma^ {2}}{B _ {2}} + \frac {1 6 n _ {1} ^ {2} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau} \end{array}
$$

where we use $\begin{array} { r } { \sum _ { j = 0 } ^ { t } ( 1 - \frac { B _ { 1 } \tau } { 2 n _ { 1 } } ) ^ { 2 ( t - j ) } \leq \frac { 2 n _ { 1 } } { B _ { 1 } \tau } } \end{array}$

It follows

$$
\begin{array}{l} \mathbb {E} \left[ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| \right] ^ {2} \\ \leq \mathbb {E} [ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| ^ {2} ] \\ \leq (1 - \frac {B _ {1} \tau}{2 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| ^ {2} + \frac {4 \tau \sigma^ {2}}{B _ {2}} + \frac {1 6 n _ {1} ^ {2} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau} \\ \leq \left[ (1 - \frac {B _ {1} \tau}{2 n _ {1}}) ^ {t + 1} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| + \frac {2 \tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 n _ {1} C _ {g} M \eta}{B _ {1} \tau^ {1 / 2}} \right] ^ {2} \end{array}
$$

Thus

$$
\begin{array}{l} \mathbb {E} \bigg [ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| \bigg ] \\ \leq (1 - \frac {B _ {1} \tau}{2 n _ {1}}) ^ {t + 1} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| + \frac {2 \tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 n _ {1} C _ {g} M \eta}{B _ {1} \tau^ {1 / 2}} \end{array}
$$

Taking summation over $i \in S ,$ we obtain the desired result

$$
\begin{array}{l} \mathbb {E} \bigg [ \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| \bigg ] \\ \leq (1 - \frac {B _ {1} \tau}{2 n _ {1}}) ^ {t + 1} \frac {1}{n} \sum_ {i \in \mathcal {S}} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| + \frac {2 \tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 n C _ {g} M \eta}{B _ {1} \tau^ {1 / 2}} \end{array}
$$

## D.4 Proof of Lemma C.6

Proof of Lemma C.6. With $\begin{array} { r } { \gamma _ { 3 } = \frac { n _ { + } - B _ { 1 } } { B _ { 1 } ( 1 - \tau _ { 2 } ) } + ( 1 - \tau _ { 2 } ) } \end{array}$ and $\tau _ { 2 } \leq \frac { 1 } { 2 }$ , MSVR update gives the following recursive error bound [15]

$$
\begin{array}{l} \mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {j, t + 1} - v _ {i, t + 1}, s _ {i, t + 1}) \| ^ {2} ] \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{n _ {+}}) \mathbb {E} [ \| u _ {i, t} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) \| ^ {2} ] + \frac {2 \tau_ {2} ^ {2} B _ {1} \sigma^ {2}}{n _ {+} B _ {2}} \\ \quad + \frac {8 n _ {+} C _ {g} ^ {2}}{B _ {1}} \mathbb {E} [ \| (v _ {j, t} - v _ {i, t}, s _ {i, t}) - (v _ {j, t + 1} - v _ {i, t + 1}, s _ {i, t + 1}) \| ^ {2} ] \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{n _ {+}}) \mathbb {E} [ \| u _ {i, t} - \frac {1}{n _ {-}} \sum_ {j \in S -} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) \| ^ {2} ] + \frac {2 \tau_ {2} ^ {2} B _ {1} \sigma^ {2}}{n _ {+} B _ {2}} \\ \quad + \frac {1 6 n _ {+} C _ {g} ^ {2}}{B _ {1}} \mathbb {E} [ \| v _ {i, t} - v _ {i, t + 1} \| ^ {2} + \| v _ {j, t} - v _ {j, t + 1} \| ^ {2} ] + \frac {8 C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1}} \end{array}\tag{44}
$$

It remains to bound $\mathbb { E } [ \| v _ { i , t } - v _ { i , t + 1 } \| ^ { 2 } ]$ and $\mathbb { E } [ \| v _ { j , t } - v _ { j , t + 1 } \| ^ { 2 } ]$ . We bound the former, and the latter’s bound naturally follows. Consider the update of $v _ { i , t + 1 }$ and we have

$$
\begin{array}{r l} & {\mathbb {E} [ \| v _ {i, t} - v _ {i, t + 1} \| ^ {2} ]} \\ & {\leq \mathbb {E} \left[ \frac {B _ {1}}{n _ {+}} \| \tau_ {1} v _ {i, t} - \tau_ {1} h ^ {(i)} (\mathbf {w} _ {t}; \mathcal {B} _ {3, i} ^ {t}) - \gamma_ {1} (h ^ {(i)} (\mathbf {w} _ {t}; \mathcal {B} _ {3, i} ^ {t}) - h ^ {(i)} (\mathbf {w} _ {t - 1}; \mathcal {B} _ {3, i} ^ {t})) \| ^ {2} \right]} \\ & {\leq \mathbb {E} \left[ \frac {2 B _ {1} \tau_ {1} ^ {2}}{n _ {+}} \| v _ {i, t} - h ^ {(i)} (\mathbf {w} _ {t}; \mathcal {B} _ {3, i} ^ {t}) \| ^ {2} + \frac {2 B _ {1} \gamma_ {1} ^ {2}}{n _ {+}} \| h ^ {(i)} (\mathbf {w} _ {t}; \mathcal {B} _ {3, i} ^ {t}) - h ^ {(i)} (\mathbf {w} _ {t - 1}; \mathcal {B} _ {3, i} ^ {t}) \| ^ {2} \right]} \\ & {\leq \mathbb {E} \left[ \frac {2 B _ {1} \tau_ {1} ^ {2}}{n _ {+}} \| v _ {i, t} - h ^ {(i)} (\mathbf {w} _ {t}; \mathcal {B} _ {3, i} ^ {t}) \| ^ {2} + \frac {2 B _ {\mathrm{1}} \gamma_ {\mathrm{1}} ^ {\mathrm{2}} C _ {\mathrm{h}}}{n _ {+}} \| \mathbf {w} _ {t} - \mathbf {w} _ {t - 1} \| ^ {2} \right]} \\ & {\overset {(a)} {\leq} \frac {8 B _ {\mathrm{1}} \tau_ {\mathrm{1}} ^ {\mathrm{2}} M ^ {\mathrm{2}}}{n _ {+}} + \frac {8 n _ {+} C _ {\mathrm{h}} ^ {\mathrm{2}} \eta^ {\mathrm{2}} M ^ {\mathrm{2}}}{B _ {\mathrm{1}}}} \end{array}
$$

where inequality (a) uses $\tau _ { 1 } \leq 1 / 2$ and $\begin{array} { r } { \gamma _ { 1 } = \frac { n _ { + } - B _ { 1 } } { B _ { 1 } ( 1 - \tau _ { 1 } ) } + ( 1 - \tau _ { 1 } ) \le \frac { 2 n _ { + } } { B _ { 1 } } } \end{array}$ . Plugging the above inequality back into inequality 44 gives

$$
\begin{array}{r l} & {\mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {j, t + 1} - v _ {i, t + 1}, s _ {i, t + 1}) \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau_ {2}}{n _ {+}}) \mathbb {E} [ \| u _ {i, t} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) \| ^ {2} ] + \frac {2 \tau_ {2} ^ {2} B _ {1} \sigma^ {2}}{n _ {+} B _ {2}}} \\ & {\quad + \frac {1 6 n _ {+} C _ {g} ^ {2}}{B _ {1}} \bigg (8 \tau_ {1} ^ {2} M ^ {2} (\frac {B _ {1}}{n _ {+}} + \frac {B _ {2}}{n _ {-}}) + 8 C _ {h} ^ {2} \eta^ {2} M ^ {2} (\frac {n _ {+}}{B _ {1}} + \frac {n _ {-}}{B _ {2}}) \bigg) + \frac {8 C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1}}} \\ & {\leq (1 - \frac {B _ {1} \tau_ {2}}{n _ {+}}) \mathbb {E} [ \| u _ {i, t} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {j, t} - v _ {i, t}, s _ {i, t}) \| ^ {2} ]   + \frac {2 \tau_ {2} ^ {2} B _ {1} \sigma^ {2}}{n _ {+} B _ {2}}} \\ & {\quad + 1 2 8 C _ {g} ^ {2} M ^ {2} \frac {n _ {+}}{B _ {1}} (\frac {B _ {1}}{n _ {+}} + \frac {B _ {2}}{n _ {-}}) \tau_ {1} ^ {2} + 1 2 8 C _ {g} ^ {2} C _ {h} ^ {2} M ^ {2} \frac {n _ {+}}{B _ {1}} (\frac {n _ {+}}{B _ {1}} + \frac {n _ {-}}{B _ {2}}) \eta^ {2} + \frac {8 C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1}}} \end{array}
$$

Applying this inequality recursively, we obtain

$$
\begin{array}{l} \mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {j, t + 1} - v _ {i, t + 1}, s _ {i, t + 1}) \| ^ {2} ] \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {+}}) ^ {2 (t + 1)} \| u _ {i, 0} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {i, 0} - v _ {j, 0}, s _ {i, 0}) \| ^ {2} + \sum_ {j = 0} ^ {t} (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {+}}) ^ {2 (t - j)} \left(\frac {2 \tau_ {2} ^ {2} B _ {1} \sigma^ {2}}{n _ {+} B _ {2}} \right. \\ \quad \left. + 1 2 8 C _ {g} ^ {2} M ^ {2} \frac {n _ {+}}{B _ {1}} (\frac {B _ {1}}{n _ {+}} + \frac {B _ {2}}{n _ {-}}) \tau_ {1} ^ {2} + 1 2 8 C _ {g} ^ {2} C _ {h} ^ {2} M ^ {2} \frac {n _ {+}}{B _ {1}} (\frac {n _ {+}}{B _ {1}} + \frac {n _ {-}}{B _ {2}}) \eta^ {2} + \frac {8 C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1}}\right) \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {+}}) ^ {2 (t + 1)} \| u _ {i, 0} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {i, 0} - v _ {j, 0}, s _ {i, 0}) | | ^ {2} + \frac {4 \tau_ {2} \sigma^ {2}}{B _ {2}} \\ \quad + 2 5 6 C _ {g} ^ {2} M ^ {2} \frac {n _ {+} ^ {2}}{B _ {1} ^ {2}} (\frac {B _ {1}}{n _ {+}} + \frac {B _ {2}}{n _ {-}}) \frac {\tau_ {1} ^ {2}}{\tau_ {2}} + 2 5 6 C _ {g} ^ {2} C _ {h} ^ {2} M ^ {2} \frac {n _ {+} ^ {2}}{B _ {1} ^ {2}} (\frac {n _ {+}}{B _ {1}} + \frac {n _ {-}}{B _ {2}}) \frac {\eta^ {2}}{\tau_ {2}} + \frac {1 6 n _ {+} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau_ {2}} \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {+}}) ^ {2 (t + 1)} \| u _ {i, 0} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {i, 0} - v _ {j, 0}, s _ {i, 0}) || ^ {2} + \frac {4 \tau_ {2} \sigma^ {2}}{B _ {2}} + C _ {2} ^ {2} \frac {n _ {+} ^ {2}}{B _ {1} ^ {2}} (\frac {B _ {1}}{n _ {+}} + \frac {B _ {2}}{n _ {-}}) \frac {\tau_ {1} ^ {2}}{\tau_ {2}} \\ \quad + C _ {2} ^ {2} \frac {n _ {+} ^ {2}}{B _ {1} ^ {2}} (\frac {n _ {+}}{B _ {1}} + \frac {n _ {-}}{B _ {2}}) \frac {\eta^ {2}}{\tau_ {2}} + C _ {2} ^ {2} \frac {n _ {+} \eta^ {2}}{B _ {1} ^ {2} \tau_ {2}} \end{array}
$$

where we use $\begin{array} { r l r l r l r } { \sum _ { j = 0 } ^ { t } ( 1 } & { { } - } & { \frac { B _ { 1 } \tau _ { 2 } } { 2 n _ { + } } ) ^ { 2 ( t - j ) } } & { } & { { } \le } & { } & { { } } & { \frac { 2 n _ { + } } { B _ { 1 } \tau _ { 1 } } } \end{array}$ and denotes $\begin{array} { r l } { C _ { 2 } ^ { 2 } } & { { } = } \end{array}$ 2 max{256C<sup>2</sup>M<sup>2</sup>, 256C $\gamma _ { g } ^ { 2 } C _ { h } ^ { 2 } M ^ { 2 }$ , 16C<sup>2</sup>M<sup>2</sup>}. Taking average over $\textit { i } \in \ S _ { + }$ gives the squarednorm error bound.

To derive the norm error bound, we derive

$$
\begin{array}{l} \mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {j, t + 1} - v _ {i, t + 1}, s _ {i, t + 1}) \| ] ^ {2} \\ \leq \mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {j, t + 1} - v _ {i, t + 1}, s _ {i, t + 1}) \| ^ {2} ] \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {+}}) ^ {2 (t + 1)} \| u _ {i, 0} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {i, 0} - v _ {j, 0}, s _ {i, 0}) \| ^ {2} + \frac {4 \tau_ {2} \sigma^ {2}}{B _ {2}} + C _ {2} ^ {2} \frac {n _ {+} ^ {2}}{B _ {1} ^ {2}} (\frac {B _ {1}}{n _ {+}} + \frac {B _ {2}}{n _ {-}}) \frac {\tau_ {1} ^ {2}}{\tau_ {2}} \\ \quad + C _ {2} ^ {2} \frac {n _ {+} ^ {2}}{B _ {1} ^ {2}} (\frac {n _ {+}}{B _ {1}} + \frac {n _ {-}}{B _ {2}}) \frac {\eta^ {2}}{\tau_ {2}} + C _ {2} ^ {2} \frac {n _ {+} \eta^ {2}}{B _ {1} ^ {2} \tau_ {2}} \\ \leq \left[ (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {+}}) ^ {t + 1} \| u _ {i, 0} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {i, 0} - v _ {j, 0}, s _ {i, 0}) \| + \frac {2 \tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + C _ {2} \frac {n _ {+}}{B _ {1}} (\frac {B _ {1} ^ {1 / 2}}{n _ {+} ^ {1 / 2}} + \frac {B _ {2} ^ {1 / 2}}{n _ {-} ^ {1 / 2}}) \frac {\tau_ {1}}{\tau_ {2} ^ {1 / 2}} \right. \\ \quad \left. + C _ {2} \frac {n _ {+}}{B _ {1}} (\frac {n _ {+} ^ {1 / 2}}{B _ {1} ^ {1 / 2}} + \frac {n _ {-} ^ {1 / 2}}{B _ {2} ^ {1 / 2}}) \frac {\eta}{\tau_ {2} ^ {1 / 2}} + C _ {2} \frac {n _ {+} ^ {1 / 2} \eta}{B _ {1} \tau_ {2} ^ {1 / 2}} \right] ^ {2} \\ \textbf {{T h u s}} \\ \mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {j, t + 1} - v _ {i, t + 1}, s _ {i, t + 1}) \| ] \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {+}}) ^ {t + 1} \| u _ {i, 0} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {i, 0} - v _ {j, 0}, s _ {i, 0}) \| + \frac {2 {\tau_ {\mathrm{e}}} ^ {\mathrm{i/2}}}{{B _ {\mathrm{e}}} ^ {\mathrm{i/2}}} + C _ {\mathrm{e}} \frac {{n _ {\mathrm{e}}} ^ {\mathrm{i/2}}}{{B _ {\mathrm{e}}} ^ {\mathrm{i/2}}} (\frac {{B _ {\mathrm{e}}} ^ {\mathrm{i/2}}}{{n _ {\mathrm{e}}} ^ {\mathrm{i/2}}} + \frac {{B _ {\mathrm{e}}} ^ {\mathrm{i/2}}}{{n _ {-}}} ^ {\mathrm{i/2}}) \frac {{\tau_ {\mathrm{e}}} ^ {\mathrm{i/2}}}{{\tau_ {\mathrm{e}}} ^ {\mathrm{i/2}}} \\ \quad + C _ {\mathrm{e}} \frac {{n _ {\mathrm{e}}} ^ {\mathrm{i/2}}}{{B _ {\mathrm{e}}} ^ {\mathrm{i/2}}} (\frac {{n _ {\mathrm{e}}} ^ {\mathrm{i/2}}}{{B _ {\mathrm{e}}} ^ {\mathrm{i/2}}} + \frac {{n _ {-}}}{{B _ {\mathrm{e}}} ^ {\mathrm{i/2}}} ^ {\mathrm{i/2}}) \frac {{\eta}}{{\tau_ {\mathrm{e}}} ^ {\mathrm{i/2}}} + C _ {\mathrm{e}} \frac {{n _ {\mathrm{e}}} ^ {\mathrm{i/2}}}{{B _ {\mathrm{e}}} ^ {\mathrm{i/2}}} ^ {\mathrm{i/2}} \end{array}
$$

Taking average over $i \in S _ { + }$ , we obtain the norm error bound

$$
\begin{array}{l} \mathbb {E} \left[ \frac {1}{n _ {+}} \sum_ {i \in S _ {+}} \| u _ {i, t + 1} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {j, t + 1} - v _ {i, t + 1}, s _ {i, t + 1}) \| \right] \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {+}}) ^ {t + 1} \frac {1}{n _ {+}} \sum_ {i \in S _ {+}} \| u _ {i, 0} - \frac {1}{n _ {-}} \sum_ {j \in S _ {-}} g _ {i} (v _ {i, 0} - v _ {j, 0}, s _ {i, 0}) \| + \frac {2 \tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} \\ + C _ {2} \frac {n _ {+}}{B _ {1}} (\frac {B _ {1} ^ {1 / 2}}{n _ {+} ^ {1 / 2}} + \frac {B _ {2} ^ {1 / 2}}{n _ {-} ^ {1 / 2}}) \frac {\tau_ {1}}{\tau_ {2} ^ {1 / 2}} + C _ {2} \frac {n _ {+}}{B _ {1}} (\frac {n _ {+} ^ {1 / 2}}{B _ {1} ^ {1 / 2}} + \frac {n _ {-} ^ {1 / 2}}{B _ {2} ^ {1 / 2}}) \frac {\eta}{\tau_ {2} ^ {1 / 2}} + C _ {2} \frac {n _ {+} ^ {1 / 2} \eta}{B _ {1} \tau_ {2} ^ {1 / 2}} \end{array}
$$

## D.5 Proof of Lemma A.3

Proof of Lemma A.3. With $\begin{array} { r } { \gamma _ { 1 } = \frac { n _ { 1 } n _ { 2 } - B _ { 1 } B _ { 2 } } { B _ { 1 } B _ { 2 } ( 1 - \tau _ { 1 } ) } + \left( 1 - \tau _ { 1 } \right) \mathrm { a n d } \tau _ { 1 } \le \frac { 1 } { 2 } } \end{array}$ , MSVR update has the following recursive error bound [15][15]

$$
\begin{array}{r l} & {\mathbb {E} [ \| v _ {i, j, t + 1} - h _ {i, j} (\mathbf {w} _ {t + 1}) \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} B _ {2} \tau_ {1}}{n _ {1} n _ {2}}) \mathbb {E} [ \| v _ {i, j, t} - h _ {i, j} (\mathbf {w} _ {t}) \| ^ {2} ] + \frac {2 \tau_ {1} ^ {2} B _ {1} B _ {2} \sigma^ {2}}{n _ {1} n _ {2} B _ {3}} + \frac {8 n _ {1} n _ {2} C _ {h} ^ {2}}{B _ {1} B _ {2}} \mathbb {E} [ \| \mathbf {w} _ {t} - \mathbf {w} _ {t + 1} \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} B _ {2} \tau_ {1}}{2 n _ {1} n _ {2}}) ^ {2} \mathbb {E} [ \| v _ {i, j, t} - h _ {i, j} (\mathbf {w} _ {t}) \| ^ {2} ] + \frac {2 \tau_ {1} ^ {2} B _ {1} B _ {2} \sigma^ {2}}{n _ {1} n _ {2} B _ {3}} + \frac {8 n _ {1} n_{2} C_{h} ^{2} M^{2}\eta^{2}}{B_{1} B_{2}}} \end{array}
$$

Applying this inequality recursively, we obtain

$$
\begin{array}{l} \mathbb {E} [ \| v _ {i, j, t + 1} - h _ {i, j} (\mathbf {w} _ {t + 1}) \| ^ {2} ] \\ \leq (1 - \frac {B _ {1} B _ {2} \tau_ {1}}{2 n _ {1} n _ {2}}) ^ {2 (t + 1)} \| v _ {i, j, 0} - h _ {i, j} (\mathbf {w} _ {0}) \| ^ {2} + \sum_ {j = 0} ^ {t} (1 - \frac {B _ {1} B _ {2} \tau_ {1}}{2 n _ {1} n _ {2}}) ^ {2 (t - j)} (\frac {2 \tau_ {1} ^ {2} B _ {1} B _ {2} \sigma^ {2}}{n _ {1} n _ {2} B _ {3}} + \frac {8 n _ {1} n _ {2} C _ {h} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} B _ {2}}) \\ \leq (1 - \frac {B _ {1} B _ {2} \tau_ {1}}{2 n _ {1} n _ {2}}) ^ {2 (t + 1)} \| v _ {i, j, 0} - h _ {i, j} (\mathbf {w} _ {0}) \| ^ {2} + \frac {4 \tau_ {1} \sigma^ {2}}{B _ {3}} + \frac {1 6 n _ {1} ^ {2} n _ {2} ^ {2} C _ {h} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} B _ {2} ^ {2} \tau_ {1}} \end{array}
$$

where we use $\begin{array} { r } { \sum _ { j = 0 } ^ { t } ( 1 - \frac { B _ { 1 } B _ { 2 } \tau _ { 1 } } { 2 n _ { 1 } n _ { 2 } } ) ^ { 2 ( t - j ) } \leq \frac { 2 n _ { 1 } n _ { 2 } } { B _ { 1 } B _ { 2 } \tau _ { 1 } } } \end{array}$ . Taking average over $( i , j ) \in S _ { 1 } \times S _ { 2 }$ gives the squared-norm error bound.

To derive the norm error bound, we derive

$$
\begin{array}{l} \mathbb {E} [ \| v _ {i, j, t + 1} - h _ {i, j} (\mathbf {w} _ {t + 1}) \| ] ^ {2} \\ \leq \mathbb {E} [ \| v _ {i, j, t + 1} - h _ {i, j} (\mathbf {w} _ {t + 1}) \| ^ {2} ] \\ \leq (1 - \frac {B _ {1} B _ {2} \tau_ {1}}{2 n _ {1} n _ {2}}) ^ {2 (t + 1)} \| v _ {i, j, 0} - h _ {i, j} (\mathbf {w} _ {0}) \| ^ {2} + \frac {4 \tau_ {1} \sigma^ {2}}{B _ {3}} + \frac {1 6 n _ {1} ^ {2} n _ {2} ^ {2} C _ {h} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} B _ {2} ^ {2} \tau_ {1}} \\ \leq \left[ (1 - \frac {B _ {1} B _ {2} \tau_ {1}}{2 n _ {1} n _ {2}}) ^ {t + 1} \| v _ {i, j, 0} - h _ {i, j} (\mathbf {w} _ {0}) \| + \frac {2 \tau_ {1} ^ {1 / 2} \sigma}{B _ {3} ^ {1 / 2}} + \frac {4 n _ {1} n _ {2} C _ {h} M \eta}{B _ {1} B _ {2} \tau_ {1} ^ {1 / 2}} \right] ^ {2} \end{array}
$$

Thus

$$
\begin{array}{l} \mathbb {E} [ \| v _ {i, j, t + 1} - h _ {i, j} (\mathbf {w} _ {t + 1}) \| ] \\ \leq (1 - \frac {B _ {1} B _ {2} \tau_ {1}}{2 n _ {1} n _ {2}}) ^ {t + 1} \| v _ {i, j, 0} - h _ {i, j} (\mathbf {w} _ {0}) \| + \frac {2 \tau_ {1} ^ {1 / 2} \sigma}{B _ {3} ^ {1 / 2}} + \frac {4 n _ {1} n _ {2} C _ {h} M \eta}{B _ {1} B _ {2} \tau_ {1} ^ {1 / 2}} \end{array}
$$

Taking average over $( i , j ) \in S _ { 1 } \times S _ { 2 }$ , we obtain the norm error bound

$$
\begin{array}{l} \mathbb {E} \bigg [ \frac {1}{n _ {1}} \sum_ {i \in \mathcal {S} _ {1}} \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} \| v _ {i, j, t + 1} - h _ {i, j} (\mathbf {w} _ {t + 1}) \| \bigg ] \\ \leq (1 - \frac {B _ {1} B _ {2} \tau_ {1}}{2 n _ {1} n _ {2}}) ^ {t + 1} \frac {1}{n _ {1}} \sum_ {i \in \mathcal {S} _ {1}} \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} \| v _ {i, j, 0} - h _ {i, j} (\mathbf {w} _ {0}) \| + \frac {2 \tau_ {1} ^ {1 / 2} \sigma}{B _ {3} ^ {1 / 2}} + \frac {4 n _ {1} n _ {2} C _ {h} M \eta}{B _ {1} B _ {2} \tau_ {1} ^ {1 / 2}}. \end{array}
$$

## D.6 Proof of Lemma A.4

ProofofLemma A.4. With $\begin{array} { r } { \gamma _ { 2 } = \frac { n _ { 1 } - B _ { 1 } } { B _ { 1 } ( 1 - \tau _ { 2 } ) } + ( 1 - \tau _ { 2 } ) } \end{array}$ and $\tau _ { 2 } \leq \frac { 1 } { 2 }$ , MSVR update has the following recursive error bound [15]

$$
\begin{array}{r l} & {\mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau_ {2}}{n _ {1}}) \mathbb {E} [ \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} ] + \frac {2 \tau_ {2} ^ {2} B _ {1} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {8 n _ {1} C _ {g} ^ {2}}{B _ {1}} \mathbb {E} [ \| v _ {i, j, t + 1} - v _ {i, j, t} \| ^ {2} ]} \end{array}\tag{45}
$$

It remains to bound $\mathbb { E } [ \| v _ { i , j , t + 1 } - v _ { i , j , t } \| ^ { 2 } ]$ , which is done as following

$$
\begin{array}{r l} & {\leq \mathbb {E} \left[ \frac {B _ {1} B _ {2}}{n _ {1} n _ {2}} \| \tau_ {1} v _ {i, j, t} - \tau_ {1} h _ {i, j} (\mathbf {w} _ {t}; \mathcal {B} _ {3, i, j} ^ {t}) - \gamma_ {1} (h _ {i, j} (\mathbf {w} _ {t}; \mathcal {B} _ {3, i, j} ^ {t}) - h _ {i, j} (\mathbf {w} _ {t - 1}; \mathcal {B} _ {3, i, j} ^ {t})) \| ^ {2} \right]} \\ & {\leq \mathbb {E} \left[ \frac {2 B _ {1} B _ {2} \tau_ {1} ^ {2}}{n _ {1} n _ {2}} \| v _ {i, j, t} - h _ {i, j} (\mathbf {w} _ {t}; \mathcal {B} _ {3, i, j} ^ {t}) \| ^ {2} + \frac {2 B _ {1} B _ {2} \gamma_ {1} ^ {2}}{n _ {1} n _ {2}} \| h _ {i, j} (\mathbf {w} _ {t}; \mathcal {B} _ {3, i, j} ^ {t}) - h _ {i, j} (\mathbf {w} _ {t - 1}; \mathcal {B} _ {3, i, j} ^ {t}) \| ^ {2} \right]} \\ & {\leq \mathbb {E} \left[ \frac {2 B _ {1} B _ {2} \tau_ {1} ^ {2}}{n _ {1} n _ {2}} \| v _ {i, j, t} - h _ {i, j} (\mathbf {w} _ {t}; \mathcal {B}  ^ {t}) \| ^ {2} + \frac {2 B _ {1} B _ {2} \gamma_ {1} ^ {2} C _ {h}}{n _ {1} n _ {2}} \| \mathbf {w} _ {t} - \mathbf {w} _ {t - 1} \| ^ {2} \right]} \end{array}
$$

$$
\stackrel {(a)} {\leq} \frac {8 B _ {1} B _ {2} \tau_ {1} ^ {2} M ^ {2}}{n _ {1} n _ {2}} + \frac {8 n _ {1} n _ {2} C _ {h} ^ {2} \eta^ {2} M ^ {2}}{B _ {1} B _ {2}}
$$

where inequality (a) uses $\tau _ { 1 } \leq 1 / 2$ and $\begin{array} { r } { \gamma _ { 1 } = \frac { n _ { 1 } n _ { 2 } - B _ { 1 } B _ { 2 } } { B _ { 1 } B _ { 2 } ( 1 - \tau _ { 1 } ) } + ( 1 - \tau _ { 1 } ) \le \frac { 2 n _ { 1 } n _ { 2 } } { B _ { 1 } B _ { 2 } } } \end{array}$ . Plugging the above inequality back into inequality 45 gives

$$
\begin{array}{r l} & {\mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau_ {2}}{n _ {1}}) \mathbb {E} [ \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} ] + \frac {2 \tau_ {2} ^ {2} B _ {1} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {8 n _ {1} C _ {g} ^ {2}}{B _ {1}} \left(\frac {8 B _ {1} B _ {2} \tau_ {1} ^ {2} M ^ {2}}{n _ {1} n _ {2}} + \frac {8 n _ {1} n _ {2} C _ {h} ^ {2} \eta^ {2} M ^ {2}}{B _ {1} B _ {2}}\right)} \\ & {\leq (1 - \frac {B _ {1} \tau_ {2}}{n _ {1}}) \mathbb {E} [ \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} ] + \frac {2 \pi_ {2} ^ {2} B _ {1} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {6 4 B _ {2} \tau_ {1} ^ {2} M ^ {2} C _ {g} ^ {2}}{n _ {2}} + \frac {6 4 n _ {1} ^ {2} n _ {2} C _ {h} ^ {2} \eta^ {2} M ^ {2} C _ {g} ^ {2}}{B _ {1} ^ {2} B _ {2}}} \end{array}
$$

Applying this inequality recursively, we obtain

$$
\begin{array}{l} \mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| ^ {2} ] \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, 0}) \| ^ {2} + \sum_ {j = 0} ^ {t} (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {1}}) ^ {t - j} \left(\frac {2 \tau_ {2} ^ {2} B _ {1} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {6 4 B _ {2} \tau_ {1} ^ {2} M ^ {2} C _ {g} ^ {2}}{n _ {2}} \right. \\ \left. + \frac {6 4 n _ {1} ^ {2} n _ {2} C _ {h} ^ {2} \eta^ {2} M ^ {2} C _ {g} ^ {2}}{B _ {1} ^ {2} B _ {2}}\right) \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, 0}) \| ^ {2} + \frac {4 \tau_ {2} \sigma^ {2}}{B _ {2}} + \frac {1 2 8 n _ {1} B _ {2} \tau_ {1} ^ {2} M ^ {2} C _ {g} ^ {2}}{B _ {1} n _ {2} \tau_ {2}} + \frac {1 2 8 n _ {1} ^ {3} n _ {2} C _ {h} ^ {2} \eta^ {2} M ^ {2} C _ {g} ^ {2}}{B _ {1} ^ {3} B _ {2} \tau_ {2}} \end{array}
$$

where we use $\begin{array} { r } { \sum _ { j = 0 } ^ { t } ( 1 - \frac { B _ { 1 } \tau _ { 2 } } { 2 n _ { 1 } } ) ^ { 2 ( t - j ) } \leq \frac { 2 n _ { 1 } } { B _ { 1 } \tau _ { 1 } } } \end{array}$ . Taking average over $i \in S _ { 1 }$ gives the squared-norm error bound.

To derive the norm error bound, we derive

$$
\begin{array}{r l} & {\mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| ] ^ {2}} \\ & {\leq \mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, 0}) \| ^ {2} + \frac {4 \tau_ {2} \sigma^ {2}}{B _ {2}} + \frac {1 2 8 n _ {1} B _ {2} \tau_ {1} ^ {2} M ^ {2} C _ {g} ^ {2}}{B _ {1} n _ {2} \tau_ {2}} + \frac {1 2 8 n _ {1} ^ {3} n _ {2} C _ {h} ^ {2} \eta^ {2} M ^ {2} C _ {g} ^ {2}}{B _ {1} ^ {3} B _ {2} \tau_ {2}}} \\ & {\leq \left[ (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {1}}) ^ {t + 1} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, 0}) \| + \frac {2 \tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {8 \sqrt 2 n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} \tau_ {1} M C _ {g}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}} + \frac {8 \sqrt 2 n _ {1} ^ {3 / 2} n _ {2} ^ {1 / 2} C _ {h} \eta M C _ {g}}{B _ {1} ^ {3 / 2} B _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}} \right] ^ {2}} \end{array}
$$

Taking squared root on both sides and taking average over $i \in S _ { 1 }$ , we obtain the norm error bound

$$
\begin{array}{l} \mathbb {E} \left[ \frac {1}{n _ {1}} \sum_ {i \in \mathcal {S} _ {1}} \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| \right] \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {1}}) ^ {t + 1} \frac {1}{n _ {1}} \sum_ {i \in \mathcal {S} _ {1}} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, 0}) \| + \frac {2 \tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {C _ {2} n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} \tau_ {1}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}} + \frac {C _ {2} n _ {1} ^ {3 / 2} n _ {2} ^ {1 / 2} \eta}{B _ {1} ^ {3 / 2} B _ {2} ^ {1 / 2} \tau_ {2} ^ {1 / 2}} \\ \text { where } C _ {2} = \max \{8 \sqrt {2} M C _ {g}, 8 \sqrt {2} C _ {h} M C _ {g} \}. \end{array}
$$

## D.7 Proof of Lemma B.2

Proof of Lemma B.2. Define

$$
\tilde {u} _ {i, t} = (1 - \tau) u _ {i, t} + \tau g _ {i} (\mathbf {w} _ {t}; \mathcal {B} _ {2, i} ^ {t})
$$

Then we have

$$
\begin{array}{r l} & {\mathbb {E} _ {\mathcal {B} _ {2, i} ^ {t}} [ \| \tilde {u} _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} ]} \\ & {= \mathbb {E} _ {\mathcal {B} _ {2, i} ^ {t}} [ \| (1 - \tau) (u _ {i, t} - g _ {i} (\mathbf {w} _ {t})) + \tau (g _ {i} (\mathbf {w} _ {t}; \mathcal {B} _ {2, i} ^ {t}) - g _ {i} (\mathbf {w} _ {t})) \| ^ {2} ]} \\ & {= \mathbb {E} _ {\mathcal {B} _ {2, i} ^ {t}} [ (1 - \tau) ^ {2} \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} + \tau^ {2} \| g _ {i} (\mathbf {w} _ {t}; \mathcal {B} _ {2, i} ^ {t}) - g _ {i} (\mathbf {w} _ {t}) \| ^ {2}} \\ & {\quad + 2 (1 - \tau) \tau \langle u _ {i, t} - g _ {i} (\mathbf {w} _ {t}), g _ {i} (\mathbf {w} _ {t}; \mathcal {B} _ {2, i} ^ {t}) - g _ {i} (\mathbf {w} _ {t}) \rangle ]} \\ & {\leq (1 - \tau) ^ {2} \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} + \frac {\tau^ {2} \sigma^ {2}}{B _ {2}}} \end{array}
$$

It follows

$$
\begin{array}{r l} & {\mathbb {E} _ {\mathcal {B} _ {2, i} ^ {t}} \mathbb {E} _ {\mathcal {B} _ {1} ^ {t}} [ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} ]} \\ & {= \frac {B _ {1}}{n _ {1}} \mathbb {E} _ {\mathcal {B} _ {2, i} ^ {t}} [ \| \tilde {u} _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} ] + (1 - \frac {B _ {1}}{n _ {1}}) \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2}} \\ & {\leq \frac {B _ {1}}{n _ {1}} (1 - \tau) ^ {2} \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} + \frac {B _ {1} \tau^ {2} \sigma^ {2}}{n _ {1} B _ {2}} + (1 - \frac {B _ {1}}{n _ {1}}) \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2}} \\ & {\leq (1 - \frac {B _ {1} \tau}{2 n _ {1}}) ^ {2} \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} + \frac {B _ {1} \tau^ {2} \sigma^ {2}}{n _ {1} B _ {2}}} \end{array}
$$

where we use

$$
\begin{array}{r l} & {\frac {B _ {1}}{n _ {1}} (1 - \tau) ^ {2} + (1 - \frac {B _ {1}}{n _ {1}}) = \frac {B _ {1}}{n _ {1}} (1 - 2 \tau + \tau^ {2}) + 1 - \frac {B _ {1}}{n _ {1}}} \\ & {\qquad = 1 - 2 \tau \frac {B _ {1}}{n _ {1}} + \tau^ {2} \frac {B _ {1}}{n _ {1}}} \\ & {\qquad \leq 1 - \tau \frac {B _ {1}}{n _ {1}}} \\ & {\qquad \leq 1 - \tau \frac {B _ {1}}{n _ {1}} + (\frac {\tau B _ {1}}{2 n _ {1}}) ^ {2} = (1 - \frac {\tau B _ {1}}{2 n _ {1}}) ^ {2}} \end{array}
$$

Then

$$
\begin{array}{r l} & {\mathbb {E} _ {t} [ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| ^ {2} ]} \\ & {\leq \mathbb {E} _ {t} \left[ (1 + \frac {B _ {1} \tau}{4 n _ {1}}) \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} + (1 + \frac {4 n _ {1}}{B _ {1} \tau}) \| g _ {i} (\mathbf {w} _ {t}) - g _ {i} (\mathbf {w} _ {t + 1}) \| ^ {2} \right]} \\ & {\leq (1 + \frac {B _ {1} \tau}{4 n _ {1}}) (1 - \frac {B _ {1} \tau}{2 n _ {1}}) ^ {2} \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} + (1 + \frac {B _ {1} \tau}{4 n _ {1}}) \frac {B _ {1} \tau^ {2} \sigma^ {2}}{n _ {1} B _ {2}}} \\ & {\quad + (1 + \frac {4 n _ {1}}{B _ {1} \tau}) C _ {g} ^ {2} \mathbb {E} _ {t} \| \mathbf {w} _ {t} - \mathbf {w} _ {t + 1} \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau}{4 n _ {1}}) ^ {2} \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} + \frac {2 B _ {1} \tau^ {2} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {8 n _ {1}}{B _ {1} \tau} C _ {g} ^ {2} \mathbb {E} _ {t} \| \mathbf {w} _ {t} - \mathbf {w} _ {t + 1} \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau}{4 n _ {1}}) ^ {2} \| u _ {i, t} - g _ {i} (\mathbf {W}) \| ^ {2} + \frac {2 B _ {1} \tau^ {2} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {8 n _ {1} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} \tau}} \end{array}
$$

where we use $\begin{array} { r } { \frac { B _ { 1 } \tau } { 4 n _ { 1 } } \leq 1 } \end{array}$ . Applying this inequality recursively, we obtain

$$
\begin{array}{l} \mathbb {E} [ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| ^ {2} ] \\ \leq (1 - \frac {B _ {1} \tau}{4 n _ {1}}) ^ {2} \mathbb {E} [ \| u _ {i, t} - g _ {i} (\mathbf {w} _ {t}) \| ^ {2} ] + \frac {2 B _ {1} \tau^ {2} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {8 n _ {1} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} \tau} \\ \leq (1 - \frac {B _ {1} \tau}{4 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| ^ {2} + \sum_ {j = 0} ^ {t} (1 - \frac {B _ {1} \tau}{4 n _ {1}}) ^ {2 (t - j)} \left[ \frac {2 B _ {1} \tau^ {2} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {8 n _ {1} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} \tau} \right] \\ \leq (1 - \frac {B _ {1} \tau}{4 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| ^ {2} + \frac {8 \tau \sigma^ {2}}{B _ {2}} + \frac {3 2 n _ {1} ^ {2} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau^ {2}} \end{array}
$$

where we use $\begin{array} { r } { \sum _ { j = 0 } ^ { t } ( 1 - \frac { B _ { 1 } \tau } { 4 n _ { 1 } } ) ^ { 2 ( t - j ) } \leq \frac { 4 n _ { 1 } } { B _ { 1 } \tau } } \end{array}$

To obtain the absolute bound, we derive

$$
\begin{array}{r l} & {\mathbb {E} [ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| ] ^ {2} \leq \mathbb {E} [ \| u _ {i, t + 1} - g _ {i} (\mathbf {w} _ {t + 1}) \| ^ {2} ]} \\ & {\qquad \leq (1 - \frac {B _ {1} \tau}{4 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| ^ {2} + \frac {8 \tau \sigma^ {2}}{B _ {2}} + \frac {3 2 n _ {1} ^ {2} C _ {g} ^ {2} M ^ {2} \eta^ {2}}{B _ {1} ^ {2} \tau^ {2}}} \\ & {\qquad \leq \left[ (1 - \frac {B _ {1} \tau}{4 n _ {1}}) ^ {t + 1} \| u _ {i, 0} - g _ {i} (\mathbf {w} _ {0}) \| + \frac {2 \sqrt {2} \tau^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 \sqrt {2} n _ {1} C _ {g} M \eta}{B _ {1} \tau} \right] ^ {2}} \end{array}
$$

The desired result follows by taking squared root on both sides.

## D.8 Proof of Lemma B.5

ProofofLemma B.5. The proof of Lemma B.5 is the same as Lemma B.2.

## D.9 Proof of Lemma B.6

Proof of Lemma B.6. Define

$$
\begin{array}{c} \tilde {u} _ {i, t} = (1 - \tau_ {2}) u _ {i, t} + \tau_ {2} \frac {1}{B _ {2}} \sum_ {j \in \mathcal {B} _ {2, i} ^ {t}} g _ {i} (v _ {i, j, t}) \\ \text {then we have} \\ \mathbb {E} _ {\mathcal {B} _ {2} ^ {t}} [ \| \tilde {u} _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} ] \\ = \mathbb {E} _ {\mathcal {B} _ {2} ^ {t}} [ \| (1 - \tau_ {2}) (u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t})) + \tau_ {2} (\frac {1}{B _ {2}} \sum_ {j \in \mathcal {B} _ {2} ^ {t}} g _ {i} (v _ {i, j, t}) - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t})) \| ^ {2} ] \\ = \mathbb {E} _ {\mathcal {B} _ {2} ^ {t}} [ (1 - \tau_ {2}) ^ {2} \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} + \tau_ {2} ^ {2} \| \frac {1}{B _ {2}} \sum_ {j \in \mathcal {B} _ {2} ^ {t}} g _ {i} (v _ {i, j, t}) - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} \\ + 2 (1 - \tau_ {2}) \tau_ {2} \langle u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}), \frac {1}{B _ {2}} \sum_ {j \in \mathcal {B} _ {2} ^ {t}} g _ {i} (v _ {i, j, t}) - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \rangle ] \\ \leq (1 - \tau_ {2}) ^ {2} \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} + \frac {\tau_ {2} ^ {2} \sigma^ {2}}{B _ {2}} \end{array}
$$

It follows

$$
\begin{array}{l} \mathbb {E} _ {\mathcal {B} _ {2, i} ^ {t}} \mathbb {E} _ {\mathcal {B} _ {1} ^ {t}} [ \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} ] \\ = \frac {B _ {1}}{n _ {1}} \mathbb {E} _ {\mathcal {B} _ {2} ^ {t}} [ \| \tilde {u} _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} ] + (1 - \frac {B _ {1}}{n _ {1}}) \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} \\ \leq \frac {B _ {1}}{n _ {1}} (1 - \tau_ {2}) ^ {2} \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} + \frac {B _ {1} \tau_ {2} ^ {2} \sigma^ {2}}{n _ {1} B _ {2}} + (1 - \frac {B _ {1}}{n _ {1}}) \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} \\ \leq (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {1}}) ^ {2} \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} + \frac {B _ {1} \tau^ {2} \sigma^ {2}}{n _ {1} B _ {2}} \end{array}
$$

where we use

$$
\frac {B _ {1}}{n _ {1}} (1 - \tau_ {2}) ^ {2} + (1 - \frac {B _ {1}}{n _ {1}}) \leq (1 - \frac {\tau_ {2} B _ {1}}{2 n _ {1}}) ^ {2}
$$

$$
\begin{array}{r l} & {\mathrm{Then}} \\ & {\mathbb {E} _ {t} [ \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| ^ {2} ]} \\ & {\leq \mathbb {E} _ {t} \left[ (1 + \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} + (1 + \frac {4 n _ {1}}{B _ {1} \tau_ {2}}) \| \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| ^ {2} \right]} \\ & {\leq (1 + \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) (1 - \frac {B _ {1} \tau_ {2}}{2 n _ {1}}) ^ {2} \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} + (1 + \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) \frac {B _ {1} \tau_ {2} ^ {2} \sigma^ {2}}{n _ {1} B _ {2}}} \\ & {\quad + (1 + \frac {4 n _ {1}}{B _ {1} \tau_ {2}}) C _ {g} ^ {2} \mathbb {E} _ {t} [ \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} \| v _ {i, j, t} - v _ {i, j, t + 1} \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) ^ {2} \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} + \frac {2 B _ {1} \tau_ {2} ^ {2} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {8 C _ {g} ^ {2} M ^ {2} B _ {2} \tau_ {1} ^ {2}}{n _ {2} \tau_ {2}}} \end{array}
$$

where we use $\begin{array} { r } { \frac { B _ { 1 } \tau _ { 2 } } { 4 n _ { 1 } } \leq 1 } \end{array}$ , and

$$
\mathbb {E} _ {t} [ \| v _ {i, j, t} - v _ {i, j, t + 1} \| ^ {2} ] = \frac {B _ {1} B _ {2}}{n _ {1} n _ {2}} \mathbb {E} _ {\mathcal {B} _ {3, i, j} ^ {t}} \| \tau_ {1} v _ {i, j, t} - \tau_ {1} h _ {i, j} (\mathbf {w} _ {t}; \mathcal {B} _ {3, i, j} ^ {t}) \| ^ {2} \leq \frac {B _ {1} B _ {2} \tau_ {1} ^ {2} M ^ {2}}{n _ {1} n _ {2}}.
$$

Applying this inequality recursively, we obtain

$$
\begin{array}{r l} & {\mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) ^ {2} \mathbb {E} [ \| u _ {i, t} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t}) \| ^ {2} ] + \frac {2 B _ {1} \tau_ {2} ^ {2} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {8 C _ {g} ^ {2} M ^ {2} B _ {2} \tau_ {1} ^ {2}}{n _ {2} \tau_ {2}}} \\ & {\leq (1 - \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, 0}) \| ^ {2} + \sum_ {j = 0} ^ {t} (1 - \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) ^ {2 (t - j)} \left[ \frac {2 B _ {1} \tau_ {2} ^ {2} \sigma^ {2}}{n _ {1} B _ {2}} + \frac {8 C _ {g} ^ {2} M ^ {2} B _ {2} \tau_ {1} ^ {2}}{n _ {2} \tau_ {2}} \right]} \\ & {\leq (1 - \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, 0}) \| ^ {2} + \frac {8 \tau_ {2} \sigma^ {2}}{B _ {2}} + \frac {3 2 C _ {g} ^ {2} M ^ {2} n _ {1} B _ {2} \tau_ {1} ^ {2}}{B _ {1} n _ {2} \tau_ {2} ^ {2}}} \end{array}
$$

where we use $\begin{array} { r } { \sum _ { j = 0 } ^ { t } ( 1 - \frac { B _ { 1 } \tau _ { 2 } } { 4 n _ { 1 } } ) ^ { 2 ( t - j ) } \leq \frac { 4 n _ { 1 } } { B _ { 1 } \tau _ { 2 } } } \end{array}$

To obtain the absolute bound, we derive

$$
\begin{array}{r l} & {\mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| ] ^ {2}} \\ & {\leq \mathbb {E} [ \| u _ {i, t + 1} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, t + 1}) \| ^ {2} ]} \\ & {\leq (1 - \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) ^ {2 (t + 1)} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, 0}) \| ^ {2} + \frac {8 \tau_ {2} \sigma^ {2}}{B _ {2}} + \frac {3 2 C _ {g} ^ {2} M ^ {2} n _ {1} B _ {2} \tau_ {1} ^ {2}}{B _ {1} n _ {2} \tau_ {2} ^ {2}}} \\ & {\leq \left[ (1 - \frac {B _ {1} \tau_ {2}}{4 n _ {1}}) ^ {t + 1} \| u _ {i, 0} - \frac {1}{n _ {2}} \sum_ {j \in \mathcal {S} _ {2}} g _ {i} (v _ {i, j, 0}) \| + \frac {2 \sqrt 2 \tau_ {2} ^ {1 / 2} \sigma}{B _ {2} ^ {1 / 2}} + \frac {4 \sqrt 2 C _ {g} M n _ {1} ^ {1 / 2} B _ {2} ^ {1 / 2} \tau_ {1}}{B _ {1} ^ {1 / 2} n _ {2} ^ {1 / 2} \tau_ {2}} \right] ^ {2}} \end{array}
$$

The desired result follows by taking squared root on both sides.

## E Group Distributionally Robust Optimization

NSWC FCCO finds an important application in group distributionally robust optimization (group DRO), particularly valuable in addressing distributional shift [25]. Consider N groups with different distributions. Each group k has an averaged loss $\begin{array} { r } { L _ { k } ( w ) = \frac { \mathrm { i } } { n _ { k } } \dot { \sum _ { i = 1 } ^ { n _ { k } } } \ell ( f _ { w } ( x _ { i } ^ { k } ) , y _ { i } ^ { k } ) } \end{array}$ , where w is the the model parameter and $( x _ { i } ^ { k } , y _ { i } ^ { k } )$ is a data point. For robust optimization, we assign different weights to different groups and form the following robust loss minimization problem:

$$
\min _ {w} \max _ {p \in \Omega} \sum_ {k = 1} ^ {N} p _ {k} L _ {k} (w),
$$

where $\Omega \subset \Delta$ and $\Delta$ denotes a simplex. A common choice for Ω is $\Omega = \{ \mathbf { p } \in \Delta , p _ { i } \leq 1 / K \}$ where K is an integer, resulting in the so-called CVaR losses, i.e., average of top-K group losses. Consequently, the above problem can be equivalently reformulated as [23]:

$$
\min _ {w} \min _ {s} F (w, s) = \frac {1}{K} \sum_ {k = 1} ^ {N} [ L _ {k} (w) - s ] _ {+} + s.
$$

This formulation can be mapped into non-smooth weakly-convex FCCO when the loss function $\ell ( \cdot , \cdot )$ is weakly convex in terms of w. In comparison to directly solving the min-max problem, solving the above FCCO problem avoids the need of dealing with the projection onto the constraint Ω and expensive sampling as in existing works [4].

## F More Information for Experiments

## F.1 Dataset Statistics

Table 3: Datasets Statistics. The percentage in parenthesis represents the proportion of positive samples.

<table><tr><td>Dataset</td><td>Train</td><td>Validation</td><td>Test</td></tr><tr><td>moltox21(t0)</td><td>5834 (4.25%)</td><td>722 (4.01%)</td><td>709 (4.51%)</td></tr><tr><td>molmuv(t1)</td><td>11466 (0.18%)</td><td>1559 (0.13%)</td><td>1709 (0.35%)</td></tr><tr><td>molpcba(t0)</td><td>120762 (9.32%)</td><td>19865 (11.74%)</td><td>20397 (11.61%)</td></tr></table>

Table 4: Data statistics for the MIL datasets. $D _ { + } / D$ is the positive/negative bag number.

<table><tr><td>Data Format</td><td>Dataset</td><td> $D_{+}$ </td><td> $D_{-}$ </td><td>average bag size</td><td>#features</td></tr><tr><td rowspan="2">Tabular</td><td>MUSK2</td><td>39</td><td>63</td><td>64.69</td><td>166</td></tr><tr><td>Fox</td><td>100</td><td>100</td><td>6.6</td><td>230</td></tr><tr><td>Histopathological</td><td>Lung</td><td>100</td><td>1000</td><td>256</td><td>32x32x3</td></tr><tr><td>Image</td><td>Lung</td><td>100</td><td>1000</td><td>256</td><td>32x32x3</td></tr></table>

## F.2 Illustration for Histopathology Dataset on MIL Task

![](images/934191436fc1c8494906815918b841f7993185fdf9473fde835d494c38775231.jpg)  
Figure 2: Illustration for Histopathology Dataset on MIL Task. Ade. is abbreviated for adenocarcinoma and SCC is short for squamous cell carcinoma. In this work, each RGB image is separated by 32×32 non-overlapped patches, which constitute the bag.