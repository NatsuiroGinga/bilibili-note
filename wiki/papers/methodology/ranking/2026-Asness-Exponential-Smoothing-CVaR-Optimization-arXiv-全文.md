---
title: "2026-Asness-Exponential-Smoothing-CVaR-Optimization-arXiv"
date: 2026-09-04
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/ranking/2026-Asness-Exponential-Smoothing-CVaR-Optimization-arXiv.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# EXPONENTIAL ADAPTIVE SMOOTHING AND IMPORTANCE SAMPLING FOR OPTIMIZATION OF THE CONDITIONAL VALUE-AT-RISK <sup>∗</sup>

WILL ASNESS<sup>†</sup>, BRENDAN KEITH<sup>†</sup>, BOYAN LAZAROV<sup>‡</sup>, ANTON MALANDII<sup>†</sup> <sup>§</sup>, AND STAN URYASEV<sup>§</sup>

Abstract. We present a novel method for solving conditional value-at-risk (CVaR) optimization problems based on the dual representation of CVaR, which is defined as the worst-case expectation over a risk envelope. The method is based on the Bregman proximal point algorithm and alternates between stochastic primal and dual stages. Every (inner) primal stage involves a subproblem solved by sampling from a probability distribution updated at each dual stage (outer iteration). The likelihood ratio of the dual probability distributions relative to the distribution underlying the original problem converges to the risk identifier of the solution’s CVaR. Thus, the dual distribution provides the algorithm with a built-in importance sampling mechanism that draws from the tail of the underlying distribution. Because only samples in the tail influence the CVaR, and samples outside the tail are drawn with decreasing probability, the algorithm delivers exceptional performance over other stochastic approximation methods. We prove the convergence of the algorithm for convex objective functions. Our numerical experiments target representative problems in financial mathematics and machine learning, focusing on portfolio optimization and support-vector machines, respectively.

Key words. Conditional value-at-risk, stochastic optimization, importance sampling, Bregman divergence, proximal point, financial mathematics, machine learning

AMS subject classifications. 65K05, 90C15, 90C47, 90C90, 91G70

1. Introduction and motivation. Decision-making under uncertainty arises across various disciplines, such as engineering design, defense planning, finance, and modern machine learning. In such settings, uncertainty is commonly modeled probabilistically, and its impact on system performance is quantified via risk measures [50, 47, 17]. Risk-averse optimization then seeks decisions that trade of average (risk-neutral) and worst-case (robust) performance across possible states (scenarios) [45, 50, 19].

Low-probability, high-consequence events are often modeled by specifying a confidence level $\alpha \in ( 0 , 1 )$ and optimizing the associated tail expectation; i.e., the conditional value-at-risk (CVaR) [46]. Two difi culties are central in CVaR optimization. First, CVaR is, in general, nonsmooth, which typically leads to subgradient-based algorithms [55] whose convergence can be slow in the sense of modern complexity theory [33]. Second, when the underlying distribution is accessed only through sampling, stochastic approximation schemes may produce high-variance subgradient estimates; the issue becomes particularly severe as α ↑ 1, since most samples contribute nothing to the tail expectation.

1.1. Related work on adaptive importance sampling for CVaR optimization. The high variance of Monte Carlo and stochastic approximation estimators for tail-risk objectives has motivated a substantial line of work on importance sampling for VaR and CVaR estimation. Bardou, Frikha, and Pag\`es [2] proposed stochastic approximation schemes for estimating VaR and CVaR and combined them with adaptive unconstrained importance sampling. Their approach targets the estimation problem and uses recursive updates of the change of measure to reduce the variance of tail estimators. Related ideas also appear in risk-sensitive simulation and reinforcement learning. Prashanth [39] developed policy-gradient methods for CVaR-constrained Markov decision processes and incorporated importance-sampling-based variance reduction, while Tamar, Glassner, and Mannor [59] studied sampling-based optimization of CVaR and likelihoodratio estimators for CVaR gradients.

More recent work has further emphasized the dificulty of learning an eficient sampling distribution when the relevant tail region depends on an unknown optimizer. Deo and Murthy [15] developed blackbox importance-sampling procedures for VaR and CVaR estimation, where the sampling distribution is constructed adaptively from less rare samples. He, Jiang, Lam, and Fu [18] studied adaptive importance sampling for stochastic root finding and quantile estimation, highlighting the circular dependence between the target solution and an efective change of measure. Closest in spirit to the present work, Pieraccini and Vanzan [36] proposed an adaptive importance sampling algorithm for risk-averse optimization in which both the sample size and the sampling distribution are updated during the optimization process.

Our approach is complementary to this literature. Rather than constructing an external change of measure for the underlying uncertainty distribution, we exploit the dual representation of CVaR [48] and update a dual probability distribution over scenarios within the CVaR risk envelope. This distribution serves a twofold purpose: it defines the adaptive smoothing of the primal subproblem and induces an adaptive sampling mechanism that concentrates computational efort on tail-relevant scenarios. Thus, the sampling distribution is not learned as a separate variance-reduction device, but is coupled directly to the minimax structure of the CVaR objective.

Motivated by this perspective, this paper proposes a framework that addresses both dificulties (nonsmoothness of the CVaR and high-variance of its subgradient estimates) simultaneously by working with a dual representation of CVaR. At each outer iteration, we (i) solve an adaptively smoothed stochastic optimization subproblem in the decision variable, and (ii) update an adaptive sampling distribution that increasingly concentrates on tail scenarios. Thus, the sampling distribution is learned hand-in-hand with the decision variable rather than prescribed in advance.

1.2. Background. Let $( \varOmega , \mathcal { A } , \mathbb { P } )$ be a discrete probability space, where $\varOmega = \{ \omega _ { 1 } , \ldots , \omega _ { n } \}$ denotes the sample space, $\bar { \mathcal { A } } = 2 ^ { \varOmega }$ denotes the set of outcomes, and P denotes the probability measure with associated probability mass function $\pmb { p } = ( p _ { 1 } , \ldots , p _ { n } )$ having $p _ { i } : = \mathbb { P } ( \omega _ { i } )$ for each $i = 1 , \ldots , n$ . We consider the stochastic optimization problem

$$
\min _ {\boldsymbol {x} \in \mathcal {X}} \operatorname{CVaR} _ {\alpha} \bigl (F (\boldsymbol {x}, \omega) \bigr),\tag{1.1}
$$

where $\mathcal { X } \subseteq \mathbb { R } ^ { d }$ is closed, convex, and nonempty, $F : \mathcal { X } \times \mathcal { Q }  \mathbb { R }$ is convex in x for each $\omega \in { \mathcal { Q } } .$ and $\mathsf { C V a R } _ { \alpha }$ $L ^ { 1 } ( \varOmega )  ( - \infty , \infty ]$ denotes the CVaR risk measure at confidence leve $\alpha \in ( 0 , 1 )$ . For any distribution r on $( \varOmega , \var A )$ , we write

$$
\mathbb {E} _ {\boldsymbol {r}} [ F (\boldsymbol {x}, \omega) ] = \sum_ {i = 1} ^ {n} F (\boldsymbol {x}, \omega_ {i}) r _ {i} =: \sum_ {i = 1} ^ {n} F _ {i} (\boldsymbol {x}) r _ {i}.
$$

Rockafellar and Uryasev [46] showed that CVaR admits the primal representation

$$
\operatorname{CVaR} _ {\alpha} \left(F (\boldsymbol {x}, \omega)\right) = \min _ {t \in \mathbb {R}} \left\{t + \frac {1}{1 - \alpha} \mathbb {E} _ {\boldsymbol {p}} \left[ (F (\boldsymbol {x}, \omega) - t) _ {+} \right] \right\},\tag{1.2}
$$

where $( \cdot ) _ { + } = \operatorname* { m a x } \{ 0 , \cdot \}$ . This formulation is widely used in software packages [28, 38, 6] because it recasts the original problem as a standard (expectation-based) stochastic optimization problem, adding a single auxiliary scalar variable t to the original decision space X. However, two drawbacks — both associated with the partial moment function $\mathbb { E } _ { p } [ ( F ( \pmb { x } , \omega ) - t ) _ { + } ] - \mathrm { a r e }$ intrinsic to (1.2).

First, the partial moment function is nonsmooth in $( { \pmb x } , t )$ due to $( \cdot ) _ { + }$ . Thus, from the standpoint of algorithmic optimization theory, standard subgradient-based methods sufer from slow theoretical and practical convergence rates [33]. In practice, state-of-the-art variable-metric subgradient methods such as Shor’s r-algorithm [55] often exhibit substantially faster convergence than standard subgradient schemes on a variety of academic and practical problems. However, the convergence theory for these methods remains incomplete, while extensions to stochastic settings are limited and ineficient. Classical smoothing ideas [33] can significantly improve theoretical convergence rates in nonsmooth optimization, but the resulting smoothing mechanisms are typically nonadaptive and ambiguous, thereby limiting their practical appeal.

Second, when p is accessed only via sampling, the associated stochastic subgradients exhibit high variance. In particular, an increasing fraction of samples satisfy $F ( \pmb { x } , \omega ) \leq t$ as α approaches 1. Such samples neither contribute to the objective nor to its (sub)gradient, yet they still incur computational cost. This limits the eficiency of both sample-average approximation $( { \mathrm { S A A } } )$ and stochastic approximation (SA) schemes in high-confidence $( \mathrm { i . e . , } \alpha \ge 0 . 9 5 )$ CVaR optimization [42, 50]. Developing a general framework that mitigates both the nonsmoothness and sampling ineficiencies of the primal representation (1.2) is the main goal of this paper.

1.3. Contributions. Our principal contribution is an algorithmic framework that combines smoothing and adaptive importance sampling via a dual, saddle-point view of CVaR. Specifically, using the dual representation [48, 1],

$$
\mathsf {C V a R} _ {\alpha} \big (F (\boldsymbol {x}, \omega) \big) = \max _ {\boldsymbol {q} \in \mathcal {Q}} \mathbb {E} _ {\boldsymbol {q}} \big [ F (\boldsymbol {x}, \omega) \big ],\tag{1.3}
$$

where

$$
\mathcal {Q} := \left\{\boldsymbol {q} \in \mathcal {Q} _ {\alpha}: \mathbf {1} ^ {\top} \boldsymbol {q} = 1 \right\}, \quad \mathcal {Q} _ {\alpha} := \left\{\boldsymbol {q} \in \mathbb {R} ^ {n}: \boldsymbol {0} \leq \boldsymbol {q} \leq \frac {\boldsymbol {p}}{1 - \alpha} \right\},
$$

we rewrite (1.1) as the saddle-point problem

$$
\min _ {\boldsymbol {x} \in \mathcal {X}} \max _ {\boldsymbol {q} \in \mathcal {Q}} \mathbb {E} _ {\boldsymbol {q}} [ F (\boldsymbol {x}, \omega) ].\tag{1.4}
$$

The maximizer(s) ${ \pmb q } ^ { \star } = { \pmb q } ^ { \star } ( { \pmb x } )$ in (1.4), while usually expensive to compute, characterize the ideal tailfocused sampling distribution(s) associated to the decision variable x. These optimal distributions saturate the upper bound $p _ { i } / ( 1 - \alpha )$ in tail scenarios, with almost all other probabilities equal to zero.<sup>1</sup> This structure is useful for sample estimation but problematic for sampling during optimization. Indeed, the inherent sparsity of $\pmb q ^ { \star }$ can prevent exploration, leading to prematurely “locking $\mathrm { i n } ^ { \dag }$ to a potentially incorrect tail set and making it impossible to accurately update the iterates $\scriptstyle { \boldsymbol { { x } } } ^ { k }$ thereafter. A similar conclusion can be drawn if (1.4) is treated by quadratic epi-regularization, as proposed in [20, 21]. Therefore, a clear challenge (and objective) is ensuring that every sampling distribution $q ^ { k } \approx q ^ { \star } ( \mathbf { \vec { x } } ^ { k } )$ belongs to the interior of $\mathcal { Q } .$

We design an interior-preserving update rule for $q ^ { k }$ by applying a (block) Bregman proximal point method to (1.4), with a divergence tailored to the box constraints in Q. The divergence is generated by a generalized Fermi–Dirac entropy (introduced in Section 2), which acts as a weak barrier-like regularizer for ${ \mathcal { Q } } _ { \alpha }$ , always yielding iterates $\pmb q ^ { k } \in$ int Q.

Main contributions.

• Adaptive smoothing. We introduce a generalized Fermi–Dirac entropy and its associated Bregman divergence to regularize the CVaR envelope Q and keep $q ^ { k }$ in its interior. This regularization yields an adaptive CVaR smoothing mechanism within the Bregman proximal point framework.

• Adaptive importance sampling. At each outer iteration, we update $q ^ { \bar { k } }$ via a closed-form block Bregman proximal step. This produces an adaptive importance sampler for the inner subproblem that increasingly concentrates on tail scenarios, $q ^ { k } \to q ^ { \star }$

• Theory and practice. We establish convergence guarantees (including variants with inexact inner solves) and demonstrate performance on portfolio optimization, support vector classification, and topology optimization.

A compact version of the proposed Exponential Adaptive Smoothing and Importance Sampling Technique (EASIeST) is given in Algorithm 1. A full derivation with precise definitions of the block proximal operator and the smoothed subproblem appears in Section 2.

We briefly comment on Steps 1–2. The block-generation procedure (Step 1) is described in Subsection 3.1. For now, we note that the blocks are randomly generated by sampling from $q ^ { k }$ . This plays a central role in the method’s eficiency and convergence. Step 2 can be implemented using either the $\mathrm { S A }$ or the SAA methods, depending on the application and computational budget. The expression for the epismoothed CVaR is derived in Subsection 2.4. A variant of the SA scheme for computing $\boldsymbol { x } _ { k } ^ { \star }$ is provided in Subsection 3.1. Practical guidance (including importance sampling using $q ^ { k }$ and inexactness heuristics) is provided in Section 4.

1.4. Paper organization. Section 2 derives the method from a Bregman proximal point view of the saddle-point formulation and introduces the generalized Fermi–Dirac entropy and the resulting block proximal update. Section 3 establishes convergence guarantees. Section 4 discusses implementation details, including hyperparameter selection, adaptive step-size, and inexactness considerations. Section 5 reports numerical results in portfolio optimization, support vector classification, and topology optimization. Section 6 concludes.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1: EASIEST for CVaR optimization.

Input : initial  $q^{0} \in int Q, k = 0$ .

Output: an approximate saddle point ( $x^{\star}, q^{\star}$ ) ∈ X × Q.

repeat

Step 1. Generate a block  $B_{k} \subseteq \{1, \ldots, n\}$  with  $|B_{k}| \geq 2$ .

Step 2. Compute an (approximate) minimizer  $x_{k}^{\star}$  of the smoothed CVaR subproblem associated with ( $q^{k}, \gamma_{k}, B_{k}$ ) (cf. (2.38)).

Step 3. Update  $q^{k+1} = \text{prox}_{\gamma_{k}\varphi}^{B_{k}}(q^{k})$  (cf. (2.33)).

 $k \leftarrow k + 1$ .

until converged
</div>

2. Algorithm derivation. This section derives Algorithm 1. We begin by introducing the essential aspects of the Bregman proximal point method [8, 60] in the context of our CVaR optimization problem (Subsections 2.1 and 2.2). Next, we introduce the concept of Bregman epi-smoothing of CVaR (Subsection 2.3). Relying on the results derived in the aforementioned sections, we rewrite CVaR optimization as a maximization problem over scenario weights q on the set Q and derive a closed-form Bregman proximal step, which reduces each outer update to solving a smoothed CVaR subproblem in the primal variable x (Subsection 2.4).

2.1. Bregman divergences. Bregman divergences form a broad class of dissimilarity measures for n-dimensional vectors. Introduced by L.M. Bregman [5], these divergences generalize the squared Euclidean distance and have since become fundamental tools in a range of scientific and engineering disciplines. To define a Bregman divergence, we begin with its generating function.

Definition 2.1 (Legendre function). Let $\mathcal { P } \subset \mathbb { R } ^ { n }$ be closed convex with nonempty interior. Then a convex function $\psi : \mathbb { R } ^ { n }  ( - \infty , \infty ]$ with value +∞ outside $\mathcal { P }$ is Legendre if

(i) the restriction of ψ to P is continuous;

(ii) ψ is essentially smooth: continuously diferentiable on the interior of its domain, int $\mathcal { P } _ { i }$ , such that for all $p \in$ bd P and $\pmb q \in$ int $\mathcal { P } _ { \downarrow }$ ,

$$
\lim _ {t \to 0, t > 0} \bigl \langle \nabla \psi (\boldsymbol {p} + t (\boldsymbol {q} - \boldsymbol {p})), \boldsymbol {q} - \boldsymbol {p} \bigr \rangle = - \infty ;
$$

(iii) $\psi$ is strictly convex on the interior of its domain, int $\mathcal { P }$ .

For any such Legendre function ψ, the associated Bregman divergence $D _ { \psi } ( p , q )$ between two points $\pmb { p } \in \mathcal { P }$ and $\pmb q \in$ int P is defined as:

$$
D _ {\psi} (\boldsymbol {p}, \boldsymbol {q}) := \psi (\boldsymbol {p}) - \psi (\boldsymbol {q}) - \left\langle \nabla \psi (\boldsymbol {q}), \boldsymbol {p} - \boldsymbol {q} \right\rangle ,\tag{2.1}
$$

where $\langle \cdot , \cdot \rangle$ represents the inner product in $\mathbb { R } ^ { n }$ , and $D _ { \psi } ( p , q ) : = + \infty$ for all other $\pmb { p } , \pmb { q } \in \mathbb { R } ^ { n }$

One of the significant features of this divergence is its separable form,

$$
D _ {\psi} (\boldsymbol {p}, \boldsymbol {q}) = \sum_ {i = 1} ^ {n} \left[ \psi_ {i} (p _ {i}) - \psi_ {i} (q _ {i}) - \psi_ {i} ^ {\prime} (q _ {i}) (p _ {i} - q _ {i}) \right],\tag{2.2}
$$

that appears when $\textstyle \psi ( { \pmb q } ) : = \sum _ { i = 1 } ^ { n } \psi _ { i } ( q _ { i } )$ is defined as a sum of component functions $\psi _ { i } \colon { \mathbb { R } }  { \mathbb { R } }$ . For instance, the functions $\begin{array} { r } { \psi _ { i } ( x ) = \frac { 1 } { 2 } ( x - 1 ) ^ { 2 } . } \end{array}$ yield the one half the standard squared Euclidean distance

$$
D _ {\psi} (\pmb {p}, \pmb {q}) = \frac {1}{2} \sum_ {i = 1} ^ {n} (p _ {i} - q _ {i}) ^ {2}.\tag{2.3}
$$

Bregman distances have been extensively utilized and studied in optimization theory [31, 8, 12, 13, 22] in their general form (2.1). On the other hand, in information theory and statistics, they are typically considered in the separable form (2.2), where vectors p and q represent generalized distributions (finite discrete measures) [9, 10, 11]. As demonstrated below, we use the Bregman divergence to construct a distance function on a subset of a probability simplex, wherein the separable form is convenient for us. The next section utilizes a Bregman divergence within the framework of the proximal point method.

2.2. Bregman proximal point. Bregman proximal point generalizes the classical proximal point method of Martinet [27] and Rockafellar [44]. For a convex objective $\varphi : \mathcal { Q }  ( - \infty , \infty ]$ , it generates a sequence $\{ q ^ { k } \} _ { k \in \mathbb { N } }$ in Q via

$$
\boldsymbol {q} ^ {0} \in \mathrm{int}   \mathrm{dom}   \psi , \qquad \boldsymbol {q} ^ {k + 1} = \mathrm{prox} _ {\gamma_ {k} \varphi} (\boldsymbol {q} ^ {k}), \qquad k = 0, 1, \ldots ,\tag{2.4}
$$

where $\{ \gamma _ { k } \} \subset ( 0 , \infty )$ satisfies $\textstyle \sum _ { k = 0 } ^ { \infty } \gamma _ { k } = + \infty$ , and the (Bregman) proximal operator is

$$
\operatorname{prox} _ {\gamma \varphi} (\boldsymbol {r}) := \underset {\boldsymbol {q} \in \mathcal {Q}} {\arg \min} \left\{\gamma \varphi (\boldsymbol {q}) + D _ {\psi} (\boldsymbol {q}, \boldsymbol {r}) \right\}.\tag{2.5}
$$

When $\begin{array} { r } { \psi ( \pmb q ) = \frac { 1 } { 2 } \| \pmb q \| _ { 2 } ^ { 2 } \left( \mathrm { c f . ~ ( 2 . 3 ) } \right) } \end{array}$ , one recovers the classical proximal point method.

Property 1 (function-value convergence). The following standard estimate will be used repeatedly.

Theorem 2.2 (Theorem 3.4 in [8]). Assume $\varphi : \mathbb { R } ^ { n }  ( - \infty , \infty ]$ is proper, lower semicontinuous, and convex. Then the iterates (2.4) satisfy

$$
\varphi (\boldsymbol {q} ^ {k}) - \varphi (\boldsymbol {q} ^ {\star}) \leq \frac {D _ {\psi} (\boldsymbol {q} ^ {\star} , \boldsymbol {q} ^ {0})}{\sum_ {i = 0} ^ {k - 1} \gamma_ {i}},\tag{2.6}
$$

where $q ^ { \star } \in$ arg min $\varphi ( \pmb q )$ q∈Q

Proof sketch. The result follows from (i) optimality of $\pmb q ^ { k + 1 }$ in (2.5), (ii) the three-point identity for $D _ { \psi }$ , and (iii) the subgradient inequality for $\varphi ,$ yielding a telescoping bound on $D _ { \psi } ( q ^ { \star } , q ^ { k } )$ and hence (2.6). The full proof is included in Section A for completeness.

Definition 2.3 (Linear convergence rates). We say that a sequence $\{ \pmb { x } ^ { k } \} _ { k \in \mathbb { N } }$ converges to $\mathbf { \Delta } \mathbf { x } ^ { \star }$ with order $q \geq 1$ and rate $r \geq 0$ if

$$
\lim _ {k \to \infty} \frac {\| \boldsymbol {x} ^ {k + 1} - \boldsymbol {x} ^ {\star} \|}{\| \boldsymbol {x} ^ {k} - \boldsymbol {x} ^ {\star} \| ^ {q}} = r.
$$

$I f q = 1$ and $r \in ( 0 , 1 )$ , then $\scriptstyle { \boldsymbol { x } } ^ { k }$ converges Q-linearly to $x ^ { \star } . \ I f \| x ^ { k } - x ^ { \star } \| \leq \epsilon _ { k }$ for all $k ,$ , where $\epsilon _ { k }$ converges Q-linearly to $0 ,$ , then $\scriptstyle { \boldsymbol { x } } ^ { k }$ converges R-linearly to $\scriptstyle { \pmb x } ^ { \star }$

Corollary 2.4. If the step sizes grow geometrically, $i . e . , \gamma _ { k + 1 } = c \gamma ^ { k }$ for some $c > 0$ and $\gamma > 1$ , then the values $\varphi ( q ^ { k } )$ from (2.4) converge at least R-linearly to $\varphi ( q ^ { \star } )$ with rate $1 / \gamma$

Proof. Define $\epsilon _ { k } : = D _ { \psi } ( \pmb q ^ { \star } , \pmb q ^ { 0 } ) / \sum _ { i = 0 } ^ { k - 1 } \gamma _ { i }$ and recall $\textstyle \sum _ { j = 0 } ^ { k - 1 } \gamma ^ { j } = ( 1 - \gamma ^ { k } ) / ( 1 - \gamma )$ . Then for $\gamma _ { k + 1 } = c \gamma ^ { k }$

$$
\frac {\epsilon_ {k + 1}}{\epsilon_ {k}} = \frac {1 - \gamma^ {k}}{1 - \gamma^ {k + 1}} \rightarrow \frac {1}{\gamma} \quad \text { as } k \rightarrow \infty .
$$

Property 2 (interior iterates). If dom $\psi = \mathcal { Q }$ , then each iterate $q ^ { k }$ remains in int $\mathcal { Q } .$

Property 3 (convergence in iterates). One more key feature of the Bregman proximal point method is that the Bregman divergence generated by the Legendre function $\psi$ acts as a Lyapunov function along the iterates. In particular, if $\pmb q ^ { \star }$ is any minimizer of the target convex objective and $q ^ { k }$ is obtained from the Bregman proximal update, then the sequence $\{ D _ { \psi } ( \pmb q ^ { \star } , \pmb q ^ { \bar { k } } ) \} _ { k \geq 0 }$ is nonincreasing and strictly decreases whenever ${ \pmb q } ^ { k } \neq { \pmb q } ^ { \star }$ . This Fej´er-type monotonicity implies that $\left\{ q ^ { \overline { { k } } } \right\}$ is bounded and asymptotically regular $( \mathrm { i . e . , ~ } D _ { \psi } ( { \pmb q } ^ { k + 1 } , { \pmb q } ^ { k } )  0 )$ . Moreover, under the stronger assumption that $\psi$ is strongly convex with respect to the norm $\| \cdot \|$ used to define the geometry of the method, the corresponding Bregman divergence controls distances: $D _ { \psi } ( \pmb q , \pmb r ) \geq c \| \pmb q - \pmb r \| ^ { 2 }$ for some $c > 0$ on the relevant domain. Consequently, the Lyapunov decrease of $D _ { \psi } ( q ^ { \star } , q ^ { k } )$ yields $\| \pmb q ^ { k } - \pmb q ^ { \star } \|  0$ , i.e., convergence of iterates in the norm with respect to which $\psi$ is strictly convex.

Remark 2.1 (The choice of Legendre function). When the iterates are probability distributions $( e . g .$ $q ^ { k } \in \mathcal { Q } ) .$ , the choice of Legendre function ψ is not merely aesthetic: it determines the notion of proximity enforced by the proximal step and, consequently, the qualitative behavior of the iterates. A Euclidean choice such as $\begin{array} { r } { \psi ( \pmb q ) = \frac { 1 } { 2 } \| \pmb q \| _ { 2 } ^ { 2 } } \end{array}$ induces the $\ell _ { 2 }$ geometry, which can severely under-penalize redistributions of mass in high dimensions. Indeed, for

$$
\boldsymbol {q} = \Big (\frac {1}{n}, \dots , \frac {1}{n} \Big), \qquad \boldsymbol {r} = \Big (\underbrace {0 , \dots , 0} _ {\alpha n}, \frac {1}{(1 - \alpha) n}, \dots , \frac {1}{(1 - \alpha) n} \Big),
$$

one has $\begin{array} { r } { \frac 1 2 \| \pmb q - \pmb r \| _ { 1 } = \alpha , i . e . , r } \end{array}$ difers from q by moving an α-fraction of probability mass, which is a large perturbation in a distributional sense. However,

$$
\| \pmb {q} - \pmb {r} \| _ {2} = \sqrt {\frac {\alpha}{(1 - \alpha) n}},
$$

which becomes small as n grows $( e . g . , \ \lVert q - r \rVert _ { 2 } \approx 3 \times 1 0 ^ { - 3 }$ for $\alpha = 0 . 9$ and $n = 1 0 ^ { 6 } )$ . Thus, an $\ell _ { 2 } { - } b a s e d$ proximal term may treat dramatically diferent distributions as $\cdot \cdot c l o s e , \ '$ allowing large mass transfers at negligible Euclidean cost. In contrast, entropy-type Legendre functions $( e . g .$ , the generalized Fermi–Dirac entropy) generate Bregman divergences that are aligned with the simplex geometry and better reflect statistically meaningful discrepancies $( e . g .$ , via Pinsker-type controls [37, 62]). This is particularly important when the iterate $\pmb q ^ { \bar { k } }$ is employed as a sampling distribution (as done here): the natural geometry helps keep $q ^ { k }$ in the interior and prevents premature degeneracy of the sampler.

A potential drawback is that prox $\dot { \gamma } \varphi$ is not always eficiently computable. However, for our CVaR dual set $\mathcal { Q } _ { \alpha }$ and an appropriate choice of $\psi _ { : }$ we can derive a convenient proximal operator in closed-form.

2.3. Bregman epi-regularization of CVaR. Epi-smoothing (or epi-regularization) of extended real valued convex functions (or functionals) via infimal convolution (with suficiently smooth kernels) traces its origins to the foundational work of Moreau [30]. By choosing the squared Euclidean norm as a smoothing kernel, one recovers the Moreau envelope, also known as Moreau–Yosida regularization, a well-established tool in optimization and convex analysis. In optimization, Moreau–Yosida regularization gives rise to the proximal point algorithm, which plays a crucial role in our work.

Recently, Kouri and Surowiec [20] applied epi-smoothing to convex risk measures and investigated the properties of the resulting measures. In turn, we apply the same technique to smooth CVaR with an appropriately chosen Bregman divergence. Such a divergence (as a smoothing kernel) allows us to (i) smooth the CVaR adaptively; and $( i i )$ design an importance-sampling procedure, which is equally significant for optimization.

Epi-regularization in dual form. A coherent risk measure $\mathcal { R }$ admits a dual representation as a supremum of expectations over a convex set of densities/likelihood ratios (see, e.g., [47]). Epi-regularization adds a strongly convex penalty to this dual formulation. In our finite-sample setting, X is represented by a vector $( X _ { 1 } , \ldots , X _ { n } ) ^ { \top }$ and expectations reduce to weighted sums.

Concretely, let $\mathcal { P } \subset \mathbb { R } ^ { n }$ be a convex dual feasible set (for CVaR, $\mathscr { P } = \mathscr { Q } )$ . For a proper closed convex penalty ψ and $\gamma > 0$ , define the dual-smoothed functional

$$
\widetilde {\mathcal {R}} ^ {\gamma} (X) = \sup _ {\boldsymbol {q} \in \mathcal {P}} \left\{\mathbb {E} _ {\boldsymbol {q}} [ X ] - \frac {1}{\gamma} \psi (\boldsymbol {q}) \right\}.\tag{2.7}
$$

For CVaR, we will apply this construction first to the associated coherent regret [47] (which has a simpler dual set) and then recover the risk via the standard regret-to-risk formula [47]; we highlight this switch explicitly below.

Example 2.1 (Exponential smoothing of CVaR). Let ${ \mathcal { R } } _ { \alpha } ( X ) = { \mathrm { C V a R } } _ { \alpha } ( X )$ Then, cf. (1.3),

$$
\mathcal {R} _ {\alpha} (X) = \max _ {\boldsymbol {q} \in \mathcal {Q}} \mathbb {E} _ {\boldsymbol {q}} [ X ].\tag{2.8}
$$

Step 1. The coherent regret associated with CVaR is

$$
\mathcal {V} _ {\alpha} (X) = \frac {1}{1 - \alpha} \mathbb {E} _ {\boldsymbol {p}} [ X _ {+} ],
$$

and it admits the dual representation

$$
\mathcal {V} _ {\alpha} (X) = \max _ {\boldsymbol {q} \in \mathcal {Q} _ {\alpha}} \langle \boldsymbol {q}, X \rangle .\tag{2.9}
$$

Introduce the generalized Fermi–Dirac binary entropy

$$
\psi (\boldsymbol {q}) := \sum_ {i = 1} ^ {n} \left[ q _ {i} \ln q _ {i} + \left(\frac {p _ {i}}{1 - \alpha} - q _ {i}\right) \ln \left(\frac {p _ {i}}{1 - \alpha} - q _ {i}\right) \right],\tag{2.10}
$$

for $q \in \mathcal { Q } _ { \alpha }$ , and set $\psi ( q ) = + \infty$ otherwise.

Lemma 2.5 (Generalized Pinsker’s inequality). Let $\psi$ be the generalized Fermi–Dirac entropy and $D _ { \mathrm { K L } }$ denote the Kullback–Leibler divergence. Then $f o r$ any probability distributions $q , r \in$ int $\mathcal { Q } ,$ , the following chain of inequalities holds:

$$
D _ {\psi} (\boldsymbol {q}, \boldsymbol {r}) \geq D _ {\mathrm{KL}} (\boldsymbol {q}, \boldsymbol {r}) \geq \frac {1}{2} \| \boldsymbol {q} - \boldsymbol {r} \| _ {1} ^ {2},
$$

and in particular

$$
\psi (\boldsymbol {q}) \geq \psi (\boldsymbol {r}) + \langle \nabla \psi (\boldsymbol {r}), \boldsymbol {q} - \boldsymbol {r} \rangle + \frac {1}{2} \| \boldsymbol {q} - \boldsymbol {r} \| _ {1} ^ {2}.
$$

Proof. For $q , r \in$ int $\mathcal { Q } ,$ , define $D _ { \mathrm { K L } } ( \pmb { q } , \pmb { r } ) : = \sum _ { i = 1 } ^ { n } q _ { i } \ln \frac { q _ { i } } { r _ { i } }$ , then (cf. (2.17))

$$
\begin{array}{l} D _ {\psi} (\boldsymbol {q}, \boldsymbol {r}) = D _ {\mathrm{KL}} (\boldsymbol {q}, \boldsymbol {r}) + \sum_ {i = 1} ^ {n} \left(\frac {p _ {i}}{1 - \alpha} - q _ {i}\right) \ln \frac {p _ {i} / (1 - \alpha) - q _ {i}}{p _ {i} / (1 - \alpha) - r _ {i}} \\ \geq D _ {\mathrm{KL}} (\boldsymbol {q}, \boldsymbol {r}). \end{array}\tag{2.11}
$$

Therefore, applying Pinsker’s inequality to (2.11) completes the proof.

For $\gamma > 0 ,$ , define the epi-regularized regret

$$
\widetilde {\mathcal {V}} _ {\alpha} ^ {\gamma} (X) = \max _ {\boldsymbol {q} \in \mathbb {R} ^ {n}} \left\{\langle \boldsymbol {q}, X \rangle - \frac {1}{\gamma} \psi (\boldsymbol {q}) \right\}.\tag{2.12}
$$

Since $\psi ( q ) = + \infty$ outside $\mathcal { Q } _ { \alpha } , ( 2 . 1 2 )$ is an unconstrained concave maximization problem and the maximizer is unique. A straightforward calculation yields

(2.13)

$$
\tilde {\pmb {q}} ^ {\gamma} (X) = \nabla \psi^ {- 1} (\gamma X) = \frac {\pmb {p}}{1 - \alpha} \frac {\exp (\gamma X)}{1 + \exp (\gamma X)} \qquad (c o m p o n e n t - w i s e),\tag{2.14}
$$

$$
\widetilde {\mathcal {V}} _ {\alpha} ^ {\gamma} (X) = \frac {1}{\gamma (1 - \alpha)} \mathbb {E} _ {\pmb {p}} \ln \left(1 + \exp (\gamma X)\right) - \underbrace {\frac {1}{\gamma (1 - \alpha)} \mathbb {E} _ {\pmb {p}} \ln \frac {\pmb {p}}{1 - \alpha}} _ {\text {constant independent of} X}.
$$

Step 2. Therefore, the exponentially smoothed CVaR is

$$
\widetilde {\mathsf {C V a R}} _ {\alpha} ^ {\gamma} (X) = \min _ {t \in \mathbb {R}} \left\{t + \frac {1}{\gamma (1 - \alpha)} \mathbb {E} _ {\boldsymbol {p}} \ln \left(1 + \exp (\gamma (X - t))\right) + C _ {\alpha} ^ {\gamma , \boldsymbol {p}} \right\},\tag{2.15}
$$

where $C _ { \alpha } ^ { \gamma , { p } } = - \frac { 1 } { \gamma ( 1 - \alpha ) } \mathbb { E } _ { { p } } \ln \frac { { p } } { 1 - \alpha } ,$

Remark 2.2 (Adjusted exponentially smoothed CVaR). To remove the constant term $C _ { \alpha } ^ { \gamma , { p } }$ in (2.15), define

$$
\hat {\psi} (\pmb {q}) = \psi (\pmb {q}) + \sum_ {i = 1} ^ {n} \frac {p _ {i}}{1 - \alpha} \ln \frac {p _ {i}}{1 - \alpha},
$$

which yields

$$
\widetilde {\mathrm{CVaR}} _ {\alpha} ^ {\gamma} (X) = \min _ {t \in \mathbb {R}} \left\{t + \frac {1}{\gamma (1 - \alpha)} \mathbb {E} _ {\boldsymbol {p}} \ln \left(1 + \exp (\gamma (X - t))\right) \right\}.\tag{2.16}
$$

This type of smoothing is discussed in [50] from the primal perspective.

In this paper, we use an alternative smoothing that is relative to a reference distribution $\textbf { \textit { r } } \in$ int $\mathcal { Q } .$ Specifically, for such r we use the Bregman divergence generated by (2.10),

$$
D _ {\psi} (\boldsymbol {q}, \boldsymbol {r}) = \sum_ {i = 1} ^ {n} q _ {i} \ln \frac {q _ {i}}{r _ {i}} + \left(\frac {p _ {i}}{1 - \alpha} - q _ {i}\right) \ln \frac {\frac {p _ {i}}{1 - \alpha} - q _ {i}}{\frac {p _ {i}}{1 - \alpha} - r _ {i}},\tag{2.17}
$$

for $q \in { \mathcal { Q } } .$ and $D _ { \psi } ( q , r ) = + \infty$ otherwise.

We then define the epi-smoothed risk via the Bregman kernel $D _ { \psi } ( \cdot , r )$

$$
\widetilde {\mathcal {R}} ^ {\gamma , \boldsymbol {r}} (X) = \min _ {t \in \mathbb {R}} \Bigl \{t + \widetilde {\mathcal {V}} ^ {\gamma , \boldsymbol {r}} (X - t) \Bigr \},\tag{2.18}
$$

where

$$
\widetilde {\mathcal {V}} ^ {\gamma , \boldsymbol {r}} (X) := \max _ {\boldsymbol {q} \in \mathbb {R} ^ {n}} \left\{\langle \boldsymbol {q}, X \rangle - \frac {1}{\gamma} D _ {\psi} (\boldsymbol {q}, \boldsymbol {r}) \right\}.\tag{2.19}
$$

Proposition 2.6 (Bregman epi-smoothed CVaR). Let $D _ { \psi }$ be the Bregman divergence associated with the Fermi–Dirac entropy (2.10). Then for any $\pmb { r } \in$ int Q,

(2.20)

$$
\tilde {\pmb {q}} ^ {\gamma , \pmb {r}} (X) = \nabla \psi^ {- 1} \big (\nabla \psi (\pmb {r}) + \gamma X \big) \in \mathrm{int} \mathcal {Q} _ {\alpha},\tag{2.21}
$$

$$
\widetilde {\mathcal {V}} _ {\alpha} ^ {\gamma , \boldsymbol {r}} (X) = \frac {1}{\gamma (1 - \alpha)} \mathbb {E} _ {\boldsymbol {p}} \ln \Big (1 + \exp \big (\nabla \psi (\boldsymbol {r}) + \gamma X \big) \Big) + C _ {\alpha} ^ {\boldsymbol {p}, \boldsymbol {r}, \gamma},\tag{2.22}
$$

$$
\widetilde {\mathsf {C V a R}} _ {\alpha} ^ {\gamma , \boldsymbol {r}} (X) = \min _ {t \in \mathbb {R}} \left\{t + \frac {1}{\gamma (1 - \alpha)} \mathbb {E} _ {\boldsymbol {p}} \ln \left(1 + \exp \left(\nabla \psi (\boldsymbol {r}) + \gamma (X - t)\right)\right) + C _ {\alpha} ^ {\boldsymbol {p}, \boldsymbol {r}, \gamma} \right\},
$$

where

$$
C _ {\alpha} ^ {\boldsymbol {p}, \boldsymbol {r}, \gamma} := \frac {1}{\gamma (1 - \alpha)} \mathbb {E} _ {\boldsymbol {p}} \ln \frac {\boldsymbol {p} / (1 - \alpha) - \boldsymbol {r}}{\boldsymbol {p} / (1 - \alpha)}.
$$

Proof. Applying first-order optimality to (2.19) yields

$$
X - \frac {1}{\gamma} \big (\nabla \psi (\boldsymbol {q}) - \nabla \psi (\boldsymbol {r}) \big) = \mathbf {0} \quad \Longleftrightarrow \quad \boldsymbol {q} = \nabla \psi^ {- 1} \big (\nabla \psi (\boldsymbol {r}) + \gamma X \big),
$$

which proves (2.20). Substituting the optimizer into (2.19) gives (2.21). Finally, using (2.18) yields (2.22).

Corollary 2.7 (Optimal $t ^ { \star }$ in (2.22)). For the Bregman epi-smoothed CVaR (2.22), the minimizer $t ^ { \star }$ satisfies

$$
\mathbf {1} ^ {\top} \tilde {\boldsymbol {q}} ^ {\gamma , \boldsymbol {r}} (X - t ^ {\star}) = 1 \quad a n d \quad \tilde {\boldsymbol {q}} ^ {\gamma , \boldsymbol {r}} (X - t ^ {\star}) \in \operatorname{int} \mathcal {Q}.\tag{2.23}
$$

The next Subsection 2.4 provides the technical details and relevant aspects of this approach applied to (1.1). Here, we mention only that the Bregman smoothing method (2.22) is relative to a chosen distribution $\textbf { \textit { r } } \in$ int $\mathcal { Q } ,$ , which makes the smoothing adaptive in the Bregman proximal point method framework—something that classical exponential smoothing (2.15) lacks.

2.4. Bregman proximal point for CVaR optimization. Define

$$
\varphi (\boldsymbol {q}) := \left\{ \begin{array}{l l} - \min _ {\boldsymbol {x} \in \mathcal {X}} \mathbb {E} _ {\boldsymbol {q}} \big [ F (\boldsymbol {x}, \omega) \big ], & \text { if } \boldsymbol {1} ^ {\top} \boldsymbol {q} = 1, \\ + \infty , & \text { otherwise }, \end{array} \right.\tag{2.24}
$$

and rewrite (1.4) as the convex minimization problem

$$
\min _ {\boldsymbol {q} \in \mathcal {Q}} \varphi (\boldsymbol {q}).\tag{2.25}
$$

Here, $\varphi$ is convex as the negative pointwise minimum of linear functions in $\mathbf { \delta } \mathbf { q } .$ We apply the Bregman proximal point method with the Fermi–Dirac $\psi$ to (2.25). The next result gives the key closed-form proximal step and smoothed CVaR primal subproblem structure behind Algorithm 1.

For $\pmb { r } \in$ int $\mathcal { Q } , \gamma > 0 , { \pmb x } \in \mathcal { X } ,$ and $t \in \mathbb { R }$ , define

$$
\boldsymbol {q} _ {\gamma , \boldsymbol {r}} (\boldsymbol {x}, t) := \nabla \psi^ {- 1} \left(\nabla \psi (\boldsymbol {r}) + \gamma (F (\boldsymbol {x}, \omega) - t)\right).\tag{2.26}
$$

Proposition 2.8 (Bregman step for CVaR). Assume $F : \mathcal { X } \times \mathcal { Q } $ R is convex in $\mathbf { \boldsymbol { x } } \in \mathcal { X }$ for $a l l \omega \in \varOmega$ Then for all $\pmb { r } \in$ int Q,

$$
\mathrm{prox} _ {\gamma \varphi} (\boldsymbol {r}) = \boldsymbol {q} _ {\gamma , \boldsymbol {r}} (\overline {{\boldsymbol {x}}}, \bar {t}) \in \mathrm{int} \mathcal {Q},\tag{2.27a}
$$

where $\scriptstyle { \overline { { \mathbf { x } } } }$ solves the regularized subproblem

$$
\overline {{\boldsymbol {x}}} \in \underset {\boldsymbol {x} \in \mathcal {X}} {\arg \min} \widetilde {\mathrm{CVaR}} _ {\alpha} ^ {\gamma , \boldsymbol {r}} \big (F (\boldsymbol {x}, \omega) \big),\tag{2.27b}
$$

and $\bar { t }$ is chosen so that $\mathbf { 1 } ^ { \top } q _ { \gamma , r } ( \overline { { \mathbf { x } } } , \bar { t } ) = 1$

Proof. Using strong duality, we can write the proximal step as

$$
\min _ {\boldsymbol {x} \in \mathcal {X}, t \in \mathbb {R}} \max _ {\boldsymbol {q} \in \mathbb {R} ^ {n}} \frac {1}{\gamma} \mathcal {L} _ {\boldsymbol {r}} (\boldsymbol {q}, \boldsymbol {x}, t),\tag{2.28}
$$

where (setting a Lagrange multiplier $\lambda = \gamma t$ for the constrain $\mathbf { 1 } ^ { \top } \pmb q = 1 )$

$$
\mathcal {L} _ {\boldsymbol {r}} (\boldsymbol {q}, \boldsymbol {x}, t) = \gamma t + \gamma \langle \boldsymbol {q}, F (\boldsymbol {x}, \omega) - t \rangle - D _ {\psi} (\boldsymbol {q}, \boldsymbol {r}).
$$

Applying Theorem 2.6 to the inner maximization over q yields the optimizer $\pmb { q } = \nabla \psi ^ { - 1 } \mathopen { } \mathclose \bgroup \left( \nabla \psi ( \pmb { r } ) + \gamma \mathopen { } \mathclose \bgroup \left( F ( \pmb { x } , \omega ) - \aftergroup \egroup \right) \aftergroup \egroup \right)$ $t ) )$ , and the resulting reduced objective in x is precisely $\widetilde { \mathsf { C V a R } } _ { \alpha } ^ { \gamma , r } ( F ( \pmb { x } , \omega ) )$ up to constants (with implicit minimization in t). Minimizing over x gives (2.27b), and substituting the minimizers and applying Theorem 2.7 yields (2.27a). □

Remark 2.3 (Notation). For each $i = 1 , \ldots , n ,$ define

$$
h _ {i} (\boldsymbol {x}, t; \boldsymbol {r}) := \ln \left(1 + \exp \left(\nabla_ {i} \psi (r _ {i}) + \gamma (F _ {i} (\boldsymbol {x}) - t)\right)\right),\tag{2.29}
$$

and the vector form

$$
\boldsymbol {h} (\boldsymbol {x}, t; \boldsymbol {r}) := \ln \Big (1 + \exp \big (\nabla \psi (\boldsymbol {r}) + \gamma (F (\boldsymbol {x}) - t) \big) \Big),\tag{2.30}
$$

where $\nabla _ { i } \psi ( r _ { i } )$ denotes the scalar derivative of ψ<sub>i</sub> at $r _ { i \textrm { \scriptsize i } }$ , and all exponentials/logarithms are component-wise. We also denote

$$
\overline {{\boldsymbol {q}}} := \operatorname{prox} _ {\gamma \varphi} (\boldsymbol {r}) = \boldsymbol {q} _ {\gamma , \boldsymbol {r}} (\overline {{\boldsymbol {x}}}, \bar {t}).\tag{2.31}
$$

The full Bregman step in Theorem 2.8 updates all components of the dual probability vector q. While this is natural in the deterministic setting, it may be unnecessarily expensive when the number of scenarios is large or when the objective is accessed through stochastic estimates. We therefore introduce a block version of the Bregman step, in which only the components indexed by a subset $B \subseteq \{ 1 , \dots , n \}$ are updated, while the remaining components are kept fixed. This preserves the structure of the full Bregman update on th active block, but reduces the amount of information required at each iteration.

The block formulation is particularly useful in the stochastic setting, where only stochastic estimates of the relevant quantities (e.g., subgradient and objective) are available. The current dual probability vector can be used to select a block of scenarios and to define the corresponding importance-sampling weights. Thus, the method updates the dual distribution only on the sampled scenarios, while retaining the previous probabilities on the complement. Since the Bregman geometry keeps the dual probabilities in the interior of the risk envelope, all scenarios remain eligible for future sampling, which provides a natural exploration mechanism.

For $\textbf { \textit { r } } \in$ int $\mathcal { Q } , \gamma > 0 , \pmb { x } \in \mathcal { X } , t \in \mathbb { R }$ , and a block $B \subseteq \{ 1 , \dots , n \}$ , define the block dual update vector $\pmb { q } _ { \gamma , r } ^ { B } ( \pmb { x } , t )$ componentwise by

$$
\big [ \boldsymbol {q} _ {\gamma , \boldsymbol {r}} ^ {\mathcal {B}} (\boldsymbol {x}, t) \big ] _ {i} := \left\{ \begin{array}{l l} \nabla_ {i} \psi^ {- 1} \Big (\nabla_ {i} \psi (r _ {i}) + \gamma \big (F _ {i} (\boldsymbol {x}) - t \big) \Big), & i \in \mathcal {B}, \\ r _ {i}, & i \in \mathcal {B} ^ {c}. \end{array} \right.\tag{2.32}
$$

Corollary 2.9 (Block Bregman step for CVaR). Let the assumptions of Theorem 2.8 hold. Fix a block $B \subseteq \{ 1 , \ldots , n \}$ with $| B | \geq 2$ and let $B ^ { c } : = \{ 1 , \ldots , n \} \setminus B$ . Then, for every $\pmb { r } \in$ int $\mathcal { Q }$ and $\gamma > 0$ 2

$$
\mathrm{prox} _ {\gamma \varphi} ^ {\mathcal {B}} (\boldsymbol {r}) = \boldsymbol {q} _ {\gamma , \boldsymbol {r}} ^ {\mathcal {B}} (\hat {\boldsymbol {x}}, \hat {t}) \in \mathrm{int} \mathcal {Q},\tag{2.33}
$$

where $( \hat { \pmb x } , \hat { t } )$ solves

$$
(\hat {\boldsymbol {x}}, \hat {t}) \in \underset {\boldsymbol {x} \in \mathcal {X}, t \in \mathbb {R}} {\arg \min} \left\{t + \sum_ {i \in \mathcal {B} ^ {c}} r _ {i} \big (F _ {i} (\boldsymbol {x}) - t \big) + \frac {1}{\gamma (1 - \alpha)} \sum_ {i \in \mathcal {B}} p _ {i} h _ {i} (\boldsymbol {x}, t; \boldsymbol {r}) \right\}.\tag{2.34}
$$

Proof. Repeat the proof of Theorem 2.8, treating the coordinates $q _ { i } ~ = ~ r _ { i }$ for $i \in B ^ { c }$ as fixed and optimizing only over $\{ q _ { i } : i \in B \}$ □

Remark 2.4 (Block notation). Equation (2.33) defines the block Bregman proximal operator, denoted $\operatorname { p r o x } _ { \gamma \varphi } ^ { B } \colon$ it coincides with $\operatorname { p r o x } _ { \gamma \varphi }$ on B and is the identity on $B ^ { c }$ . Following (2.31), we write

$$
\overline {{\boldsymbol {q}}} ^ {\mathcal {B}} := \mathrm{prox} _ {\gamma \varphi} (\boldsymbol {r}) = \boldsymbol {q} _ {\gamma , \boldsymbol {r}} ^ {\mathcal {B}} (\hat {\boldsymbol {x}}, \hat {t}).
$$

Define the block logistic functions

(2.35)

$$
h _ {i} ^ {\mathcal {B}} (\boldsymbol {x}, t; \boldsymbol {r}) := \frac {1}{\gamma (1 - \alpha)} \frac {p _ {i}}{r _ {i}} h _ {i} (\boldsymbol {x}, t; \boldsymbol {r}), \qquad i \in \mathcal {B},\tag{2.36}
$$

$$
h _ {i} ^ {\mathcal {B}} (\pmb {x}, t; \pmb {r}) := F _ {i} (\pmb {x}) - t,
$$

and let $\pmb { h } ^ { B } ( \pmb { x } , t ; \pmb { r } )$ be the random variable taking values $h _ { i } ^ { B } ( { \pmb x } , t ; { \pmb r } )$ with probabilities $r _ { i } .$ . Then the objective in (2.34) can be written as

$$
f ^ {\mathcal {B}} (\boldsymbol {x}, t; \boldsymbol {r}) := t + \mathbb {E} _ {\boldsymbol {r}} \left[ \boldsymbol {h} ^ {\mathcal {B}} (\boldsymbol {x}, t; \boldsymbol {r}) \right].\tag{2.37}
$$

Finally, define the block-Bregman epi-smoothed CVaR as

$$
\widetilde {\mathrm{CVaR}} _ {\alpha , \mathcal {B}} ^ {\gamma , r} (F (\boldsymbol {x}, \omega)) := \min _ {t \in \mathbb {R}} f ^ {\mathcal {B}} (\boldsymbol {x}, t; \boldsymbol {r}).\tag{2.38}
$$

2.5. Optimality conditions. This section derives optimality conditions for minimizing the block-Bregman epi-smoothed CVaR (2.38), i.e.,

$$
\min _ {\boldsymbol {x} \in \mathcal {X}} \widetilde {\operatorname{CVaR}} _ {\alpha , \mathcal {B}} ^ {\gamma , \boldsymbol {r}} (F (\boldsymbol {x}, \omega)).\tag{2.39}
$$

We first treat the full-block case $B = \{ 1 , \ldots , n \}$

Proposition 2.10 (Optimality conditions). Under the assumptions of Theorem 2.8, any optimal decision variable x and the corresponding optimal multiplier t satisfy

(2.40a)

$$
\mathbf {1} ^ {\top} \overline {{\boldsymbol {q}}} = 1,\tag{2.40b}
$$

$$
- \mathbb {E} _ {\boldsymbol {q} ^ {+} (\overline {{\boldsymbol {x}}}, \bar {t})} \left[ g _ {F} (\overline {{\boldsymbol {x}}}, \omega) \right] \in \mathcal {N} _ {\mathcal {X}} (\overline {{\boldsymbol {x}}}),
$$

where $\mathcal { N } _ { \mathcal { X } } ( \overline { { \boldsymbol { x } } } )$ is the normal cone to X at x and $g _ { F } ( \overline { { \ b { x } } } , \omega ) \in \partial F ( \overline { { \ b { x } } } , \omega )$ is a (measurable) subgradient of F in x.

Proof. Equation (2.40a) restates the defining condition for ${ \bar { t } } .$ Given $\bar { t } ,$ the inclusion (2.40b) follows from first-order optimality for the convex problem (2.27b). □

Corollary 2.11 (Block optimality conditions). Under the assumptions of Theorem 2.9, any optimal xˆ and corresponding t<sup>ˆ</sup> satisfy

(2.41a)

$$
\mathbf {1} ^ {\top} \overline {{\boldsymbol {q}}} ^ {\beta} = 1,\tag{2.41b}
$$

$$
- \mathbb {E} _ {\boldsymbol {q} ^ {\mathcal {B} +} (\hat {\boldsymbol {x}}, \hat {t})} \left[ g _ {F} (\hat {\boldsymbol {x}}, \omega) \right] \in \mathcal {N} _ {\mathcal {X}} (\hat {\boldsymbol {x}}).
$$

Proof. The feasibility condition becomes $\begin{array} { r } { \sum _ { i \in \boldsymbol { \mathcal { B } } } \bar { q } _ { i } ^ { B } = \sum _ { i \in \boldsymbol { \mathcal { B } } } r _ { i } } \end{array}$ and the stationarity condition follows from first-order optimality for (2.34). □

Remark 2.5 (Size of the block B). The block size must sa $t i s f y \ | B | \geq 2$ . Indeed, (2.41a) is equivalent to $\begin{array} { r } { \sum _ { i \in \mathcal { B } } \bar { q } _ { i } ^ { \mathcal { B } } = \sum _ { i \in \mathcal { B } } \dot { r _ { i } } . \ I f \left| \mathcal { B } \right| = 1 } \end{array}$ , this forces $\bar { q } _ { i } ^ { B } = r _ { i }$ for the unique index in the block, hence $\mathrm { p r o x } _ { \gamma \varphi } ^ { \hat { B } } = \mathrm { I d }$ and the update is trivial.

3. Convergence analysis. This section establishes convergence guarantees for Algorithm 1. We begin in Subsection 3.1 by presenting the complete EASIeST scheme, including the outer randomized block Bregman updates and the inner routines used to solve the regularized subproblems.

The convergence analysis then proceeds in two steps. First, we analyze the stochastic inner subproblem routine (3.1)–(3.2) for a fixed dual distribution q and prove sublinear convergence for general convex objectives in Theorem 3.1. Second, we use these inner guarantees to analyze the outer randomized block Bregman updates in Algorithm 1, proving convergence in function values in Theorem 3.2 and almost sure convergence of the iterates in Theorem 3.3.

3.1. Complete EASIeST algorithm. The derivations in Subsections 2.1 through 2.5 lead to the EASIeST, summarized in Algorithm 1. At a high level, EASIeST alternates between: (i) a primal inner stage, which approximately solves a smoothed CVaR subproblem, and (ii) a dual outer stage, which updates the dual probability vector $q ^ { k }$ by a randomized block Bregman proximal step. We now describe the two main components of the method.

Step 1. Block generation. Block-coordinate and randomized coordinate methods have been extensively studied; see, for example, Chapter 5 of [52] and the references therein. Common block-selection strategies include cyclic rules, randomized selection from a fixed partition, uniform or nonuniform coordinate sampling [53, 54, 32, 40, 41, 34], importance sampling based on coordinate-wise smoothness constants [63, 64, 23], and greedy selection rules [61, 24, 7].

In our setting, however, a fixed-partition strategy is not appropriate. The block Bregman update preserves the total mass of the selected block (cf. Remark 2.5); hence, if the coordinates were partitioned into fixed blocks, the sequence $\{ q ^ { k } \} _ { k \in \mathbb { N } }$ would remain confined to a restricted subset of $\mathcal { Q } ,$ , which need not contain an optimal dual solution. We therefore sample a fresh block at every outer iteration.

Specifically, at iteration $k ,$ we choose a sampling distribution $\pi ^ { k }$ over $\{ 1 , \ldots , n \}$ with $\pi _ { i } ^ { k } > 0$ for all $i ,$ draw $m _ { k } \ge 2$ indices without replacement according to $\pi ^ { k }$ , and denote the resulting block by $\boldsymbol { B } _ { k }$ . Since every index has a positive probability of selection, the randomized block updates are not restricted by fixed block-mass constraints and can explore the full feasible region $\mathcal { Q } .$

For CVaR optimization, the natural choice is

$$
\boldsymbol {\pi} ^ {k} = \boldsymbol {q} ^ {k}.
$$

Indeed, the Bregman geometry guarantees $q ^ { k } \in \operatorname { i n t } { \mathcal { Q } } .$ , so $q _ { i } ^ { k } > 0$ for all $i = 1 , \ldots , n$ . Thus, $q ^ { k }$ is a valid block-sampling distribution. This choice is also consistent with the stochastic inner solver, which uses the same dual probability vector $q ^ { k }$ for importance sampling.

Remark 3.1. The choice $\pi ^ { k } = q ^ { k }$ relies on the fact that the Bregman update keeps the dual iterates in int $\mathcal { Q }$ . In contrast, a classical quadratic proximal update may produce sparse dual iterates with some zero components. Such iterates are not suitable as block-sampling distributions in the stochastic setting, since zero-mass scenarios would no longer be sampled. Although one could introduce a separate distribution $\pmb { \pi } ^ { k } \neq \pmb { q } ^ { k }$ , this would break the natural link between the outer dual update and the inner importance-sampling distribution.

Step 2. Subproblem solution. At each outer iteration $k ,$ the block Bregman step requires solving the regularized subproblem (2.34). We distinguish between deterministic and stochastic implementations of EASIeST. Here, the deterministic setting refers to either the case where full function values and full (sub)gradients with respect to all scenarios can be computed, or to the SAA setting, where a fixed finite scenario set is treated as the deterministic objective.

Deterministic subproblem solution. In the deterministic setting, (2.34) can be solved by any appropriate deterministic optimization method. The choice of the inner solver depends on the structure of $F .$ , the geometry of $x ,$ the dimension of the decision variable, and the cost of evaluating $F$ and its (sub)gradients. For example, if only the convexity of $F ( \cdot , \omega )$ is assumed, one may use a projected subgradient-type method. If F is smooth and the dimension is moderate, deterministic first-order, quasi-Newton, or second-order methods may be preferable. Thus, the deterministic version of EASIeST is not tied to a particular inner solver; the convergence analysis only requires that the regularized subproblems be solved to the prescribed accuracy.

Stochastic subproblem solution. In the stochastic setting, we solve (2.34) using a projected stochastic subgradient method with $q ^ { k }$ as the sampling distribution. Unlike Step 1, the inner routine uses mini-batch sampling with replacement: scenarios are sampled independently, and repetitions are allowed. As $\pmb q ^ { k }$ adapts over the outer iterations, this yields an adaptive importance-sampling mechanism.

Fix a mini-batch multiset ${ \mathcal { T } } \subseteq \{ 1 , \ldots , n \}$ with $| \mathcal { T } | \geq 1$ , where indices in $\mathcal { T }$ may repeat. For outer iteration k and inner iteration $j ,$ , we use

(3.1)

$$
t _ {k} ^ {j} = \underset {t \in \mathbb {R}} {\arg \min} f ^ {\mathcal {B} _ {k}} (\pmb {x} _ {k} ^ {j}, t; \pmb {q} ^ {k}),\tag{3.2}
$$

$$
\pmb {x} _ {k} ^ {j + 1} = \mathrm{proj} _ {\mathcal {X}} \left[ \pmb {x} _ {k} ^ {j} - \beta_ {j} G _ {\pmb {x}} (\pmb {x} _ {k} ^ {j}, t _ {k} ^ {j}; \mathcal {I}) \right],
$$

where $\{ \beta _ { j } \} _ { j \in \mathbb { N } }$ is a step-size sequence and $G _ { \pmb { x } } ( \pmb { x } _ { k } ^ { j } , t _ { k } ^ { j } ; \pmb { \mathcal { I } } )$ is an unbiased mini-batch stochastic subgradient of $f ^ { B _ { k } }$ with respect to ${ \pmb x } .$ . Convergence guarantees for (3.1)–(3.2) are given in Theorem 3.1.

3.2. Subproblem convergence for general convex functions. This subsection analyzes a specific stochastic routine for approximately solving the regularized subproblems generated by EASIeST. In particular, we focus on the projected stochastic subgradient scheme (3.1)–(3.2) under a fixed dual distribution $\mathbf { \delta } _ { \mathbf { q } } .$ This choice is convenient for the stochastic version of the method, but it is not intrinsic to the outer block Bregman framework. In deterministic implementations, or when the subproblem admits additional exploitable structure, one may replace this inner routine by any solver capable of producing the required approximate solution.

For a fixed $\pmb q \in \mathcal { Q }$ , consider the subproblem objective $f ^ { B } ( { \pmb x } , t ; { \pmb q } )$ and the update rule (3.1)–(3.2), where at iteration $j$ we take $\begin{array} { r } { t ^ { j } \in \arg \operatorname* { m i n } _ { t \in \mathbb { R } } f ^ { \mathcal { B } } ( \pmb { x } ^ { j } , t ; \pmb { q } ) } \end{array}$ and then perform a projected stochastic (sub)gradient step in x. Throughout this subsection, we view $t ^ { j }$ as exact minimizer given $\boldsymbol { x } ^ { j } ;$ this allows us to treat the method as projected stochastic subgradient descent on the reduced function

$$
\hat {f} ^ {\mathcal {B}} (\boldsymbol {x}; \boldsymbol {q}) := \min _ {t \in \mathbb {R}} f ^ {\mathcal {B}} (\boldsymbol {x}, t; \boldsymbol {q}), \quad \text { so   that } \quad \hat {f} ^ {\mathcal {B}} (\boldsymbol {x} ^ {j}; \boldsymbol {q}) = f ^ {\mathcal {B}} (\boldsymbol {x} ^ {j}, t ^ {j}; \boldsymbol {q}).
$$

Theorem 3.1 (Subproblem convergence). Let $\{ ( \pmb { x } ^ { j } , t ^ { j } ) \} _ { j = 0 } ^ { T }$ be generated by (3.1)–(3.2). Assume:

(i) ( Bounded second moment) For all $\mathbf { \boldsymbol { x } } \in \mathcal { X }$ and $t \in \mathbb { R } ,$

$$
\mathbb {E} \left[ \left\| G _ {\boldsymbol {x}} (\boldsymbol {x}, t; \mathcal {I}) \right\| _ {2} ^ {2} \right] \leq B ^ {2}.
$$

(ii) (Bounded domain) There exists $R < \infty$ such that $\| { \pmb x } - { \pmb x } ^ { \star } \| _ { 2 } ^ { 2 } \le R ^ { 2 }$ for all $\textbf { \em x } \in { \mathcal { X } } _ { \textrm { \textmu } }$ , where $\pmb { x } ^ { \star } \in$ $\arg \operatorname* { m i n } _ { \pmb { x } \in \mathcal { X } } \hat { f } ^ { \mathcal { B } } ( \pmb { x } ; \pmb { q } )$

Define the ergodic averages $\bar { \pmb x } ^ { T } : = \frac { 1 } { T } \sum _ { j = 0 } ^ { T - 1 } \pmb x ^ { j }$ and $\bar { t } ^ { T } : = \frac { 1 } { T } \sum _ { j = 0 } ^ { T - 1 } t ^ { j }$ . Then

$$
\mathbb {E} \left[ f ^ {\mathcal {B}} \left(\bar {\boldsymbol {x}} ^ {T}, \bar {t} ^ {T}; \boldsymbol {q}\right) - f _ {*} ^ {\mathcal {B}} \right] \leq \frac {R ^ {2}}{2 T \beta_ {T - 1}} + \frac {1}{2 T} \sum_ {j = 0} ^ {T - 1} \beta_ {j} B ^ {2},
$$

where $f _ { * } ^ { B } : = \operatorname* { m i n } _ { \substack { x \in \mathcal { X } , t \in \mathbb { R } } } f ^ { \mathcal { B } } ( \pmb { x } , t ; \pmb { q } )$

Proof. Let $g ^ { j } : = \mathbb { E } \big [ G _ { x } ( \boldsymbol { x } ^ { j } , t ^ { j } ; \mathcal { T } ) \ | \ \boldsymbol { x } ^ { j } , t ^ { j } \big ]$ and $\eta _ { j } : = G _ { \pmb { x } } ( \pmb { x } ^ { j } , t ^ { j } ; \pmb { \mathscr { T } } ) - g ^ { j }$ , so that $\mathbb { E } [ \eta _ { j } \mid \pmb { x } ^ { j } , t ^ { j } ] = 0$ . By the nonexpansiveness of the Euclidean projection,

$$
\begin{array}{l} \| \boldsymbol {x} ^ {j + 1} - \boldsymbol {x} ^ {\star} \| _ {2} ^ {2} = \left\| \operatorname{proj} _ {\mathcal {X}} \big (\boldsymbol {x} ^ {j} - \beta_ {j} G _ {\boldsymbol {x}} (\boldsymbol {x} ^ {j}, t ^ {j}; \mathcal {I}) \big) - \boldsymbol {x} ^ {\star} \right\| _ {2} ^ {2} \\ \qquad \leq \left\| \boldsymbol {x} ^ {j} - \beta_ {j} G _ {\boldsymbol {x}} (\boldsymbol {x} ^ {j}, t ^ {j}; \mathcal {I}) - \boldsymbol {x} ^ {\star} \right\| _ {2} ^ {2} \\ \qquad = \| \boldsymbol {x} ^ {j} - \boldsymbol {x} ^ {\star} \| _ {2} ^ {2} + \beta_ {j} ^ {2} \| G _ {\boldsymbol {x}} (\boldsymbol {x} ^ {j}, t ^ {j}; \mathcal {I}) \| _ {2} ^ {2} - 2 \beta_ {j} \langle \boldsymbol {x} ^ {j} - \boldsymbol {x} ^ {\star}, G _ {\boldsymbol {x}} (\boldsymbol {x} ^ {j}, t ^ {j}; \mathcal {I}) \rangle . \end{array}
$$

Taking conditional expectation given $\boldsymbol { \mathbf { \mathit { x } } } ^ { j } , t ^ { j }$ and using $\mathbb { E } [ \eta _ { j } \mid \pmb { x } ^ { j } , t ^ { j } ] = 0$ gives

$$
\begin{array}{c} \mathbb {E} \big [ \| \boldsymbol {x} ^ {j + 1} - \boldsymbol {x} ^ {\star} \| _ {2} ^ {2} \mid \boldsymbol {x} ^ {j}, t ^ {j} \big ] \leq \| \boldsymbol {x} ^ {j} - \boldsymbol {x} ^ {\star} \| _ {2} ^ {2} + \beta_ {j} ^ {2} \mathbb {E} \big [ \| G _ {\boldsymbol {x}} (\boldsymbol {x} ^ {j}, t ^ {j}; \mathcal {I}) \| _ {2} ^ {2} \mid \boldsymbol {x} ^ {j}, t ^ {j} \big ] \\ - 2 \beta_ {j} \langle \boldsymbol {x} ^ {j} - \boldsymbol {x} ^ {\star}, g ^ {j} \rangle . \end{array}
$$

Since $t ^ { j } \in$ arg min $f ^ { B } ( { \pmb x } ^ { j } , t ; { \pmb q } )$ , any expected x-(sub)gradient at $( \boldsymbol { \mathbf { \mathit { x } } } ^ { j } , t ^ { j } )$ is a valid subgradient of the reduced function $\hat { f } ^ { B } ( \cdot ; \pmb { q } )$ at $\mathbf { \boldsymbol { x } } ^ { j }$ , hence $g ^ { j } \in \partial \hat { f } ^ { B } ( { \pmb x } ^ { j } ; { \pmb q } )$ . By convexity of $\hat { f } ^ { \mathcal { B } } , \langle { \pmb x } ^ { j } - { \pmb x } ^ { \star } , { \pmb g } ^ { j } \rangle \geq \hat { f } ^ { \mathcal { B } } ( { \pmb x } ^ { j } ; { \pmb q } ) - \hat { f } ^ { \mathcal { B } } ( { \pmb x } ^ { \star } ; { \pmb q } ) =$ $f ^ { { \cal B } } ( { \bf x } ^ { j } , t ^ { j } ; { \pmb q } ) - f _ { \ast } ^ { { \cal B } }$ . Using Assumption (i) and rearranging yields

$$
\mathbb {E} \left[ f ^ {\mathcal {B}} \left(\boldsymbol {x} ^ {j}, t ^ {j}; \boldsymbol {q}\right) - f _ {*} ^ {\mathcal {B}} \right] \leq \frac {\mathbb {E} \left[ \| \boldsymbol {x} ^ {j} - \boldsymbol {x} ^ {\star} \| _ {2} ^ {2} \right] - \mathbb {E} \left[ \| \boldsymbol {x} ^ {j + 1} - \boldsymbol {x} ^ {\star} \| _ {2} ^ {2} \right]}{2 \beta_ {j}} + \frac {\beta_ {j}}{2} B ^ {2}.
$$

Summing over $j = 0 , \ldots , T - 1$ , using nonincreasing $\beta _ { j }$ to telescope with $\beta _ { T - 1 }$ , and then dividing by $T$ gives

$$
\frac {1}{T} \sum_ {j = 0} ^ {T - 1} \mathbb {E} \left[ f ^ {\mathcal {B}} \left(\boldsymbol {x} ^ {j}, t ^ {j}; \boldsymbol {q}\right) - f _ {*} ^ {\mathcal {B}} \right] \leq \frac {R ^ {2}}{2 T \beta_ {T - 1}} + \frac {1}{2 T} \sum_ {j = 0} ^ {T - 1} \beta_ {j} B ^ {2}.
$$

Finally, Jensen’s inequality and convexity of $f ^ { B } ( \cdot , \cdot ; \pmb { q } )$ imply

$$
f ^ {\mathcal {B}} (\bar {\boldsymbol {x}} ^ {T}, \bar {t} ^ {T}; \boldsymbol {q}) \leq \frac {1}{T} \sum_ {j = 0} ^ {T - 1} f ^ {\mathcal {B}} (\boldsymbol {x} ^ {j}, t ^ {j}; \boldsymbol {q}),
$$

completing the proof.

3.3. Convergence of the EASIeST. We now analyze the outer dual updates of Algorithm 1. Recall that $\varphi ( \pmb q )$ denotes the outer objective over $\mathcal { Q } ,$ and that $\psi$ is the Fermi–Dirac Legendre function used to define the Bregman divergence $D _ { \psi }$ . We assume the algorithm is initialized at $\pmb q ^ { 0 } \in$ int $\mathcal { Q } ;$ by construction of the Bregman proximal step with ψ, the iterates remain in int $\mathcal { Q } .$

Theorem 3.2 (EASIeST convergence in function values). Let $\{ q ^ { k } \} _ { k \in \mathbb { N } }$ be the sequence of iterates of the Algorithm 1 with step-sizes $\{ \gamma _ { k } \} _ { k \in \mathbb { N } }$ and random blocks $\{ B _ { k } \} _ { k \in \mathbb { N } }$

If each coordinate $i \in \{ 1 , \ldots , n \}$ is sampled (without replacement) with probability $\pi _ { i } ^ { k } > 0$ , then the sequence $\{ q ^ { k } \} _ { k \in \mathbb { N } } \subset$ int Q converges in function values as follows:

$$
\varphi (\boldsymbol {q} ^ {k}) - \varphi (\boldsymbol {q} ^ {\star}) \leq \frac {D _ {\psi} (\boldsymbol {q} ^ {\star} , \boldsymbol {q} ^ {0})}{\sum_ {j = 0} ^ {k - 1} \gamma_ {j}}.\tag{3.3}
$$

In particular, $\begin{array} { r } { i f \sum _ { k = 0 } ^ { \infty } \gamma _ { k } = + \infty , } \end{array}$ , then $\varphi ( \pmb q ^ { k } ) \downarrow \varphi ( \pmb q ^ { \star } )$

Proof. The proof here follows exactly that of Theorem 2.2, noting that at each iteration k the proximal operator acts only on the coordinate block $\boldsymbol { B } _ { k }$

Step 1. Since the Bregman divergence $D _ { \psi }$ is additive by definition, denote by $D _ { \psi } ^ { B _ { k } } ( q ^ { k + 1 } , q ^ { k } )$ the Bregman divergence between $q ^ { k }$ and $\pmb q ^ { k + 1 }$ on the block $\boldsymbol { B } _ { k }$ . Note that

$$
D _ {\psi} (\boldsymbol {q} ^ {k + 1}, \boldsymbol {q} ^ {k}) = D _ {\psi} ^ {\mathcal {B} _ {k}} (\boldsymbol {q} ^ {k + 1}, \boldsymbol {q} ^ {k}) + D _ {\psi} ^ {\mathcal {B} _ {k} ^ {c}} (\boldsymbol {q} ^ {k + 1}, \boldsymbol {q} ^ {k}).
$$

Moreover, since $\boldsymbol { q } _ { i } ^ { k + 1 } = \boldsymbol { q } _ { i } ^ { k }$ for $i \in B _ { k } ^ { c }$ , then $D _ { \psi } ^ { \mathcal { B } _ { k } ^ { c } } ( \pmb { q } ^ { k } , \pmb { q } ^ { k + 1 } ) = D _ { \psi } ^ { \mathcal { B } _ { k } ^ { c } } ( \pmb { q } ^ { k } , \pmb { q } ^ { k } ) = 0$ . With this, the monotonicity property $\varphi ( \pmb q ^ { k + 1 } ) \le \varphi ( \pmb q ^ { k } )$ ) holds by the same reasoning used in Step 1 of Section $\mathrm { A }$

Step 2. As in the previous step, observe that the Fermi–Dirac entropy $\psi$ is additive; we denote its value on block $\boldsymbol { B } _ { k }$ at $\scriptstyle q ^ { k + 1 }$ by $\psi ^ { B _ { k } } ( \pmb q ^ { k + 1 } )$ . Evidently,

$$
\psi (\boldsymbol {q} ^ {k + 1}) = \psi^ {\mathcal {B} _ {k}} (\boldsymbol {q} ^ {k + 1}) + \psi^ {\mathcal {B} _ {k} ^ {c}} (\boldsymbol {q} ^ {k + 1}),
$$

and since $\boldsymbol { q } _ { i } ^ { k + 1 } = \boldsymbol { q } _ { i } ^ { k }$ for $i \in \mathcal { B } _ { k } ^ { c } , \psi ^ { \mathcal { B } _ { k } ^ { c } } ( \pmb q ^ { k + 1 } ) = \psi ^ { \mathcal { B } _ { k } ^ { c } } ( \pmb q ^ { k } )$

Since each coordinate i of the decision variable $\pmb q$ has a a strictly positive sampling probability, the sequence of iterates $\{ q ^ { k } \} _ { k \in \mathbb { N } }$ is guaranteed to evolve within the int Q making $\pmb q ^ { \star } \in \mathcal { Q }$ feasible in the limit.

From here, the proof proceeds as in Step 2 of Section A.

Theorem 3.3 (EASIeST convergence in iterates). Let $\{ \pmb q ^ { k } \} _ { k \in \mathbb { N } } \subset$ int Q be the sequence of iterates of the Algorithm 1 with positive step-sizes $\{ \gamma _ { k } \} _ { k \in \mathbb { N } }$ such that $\textstyle \sum _ { k = 0 } ^ { \infty } \gamma _ { k } = + \infty$ , and random blocks $\{ B _ { k } \} _ { k \in \mathbb { N } }$ Assume that each coordinate $i \in \{ 1 , \ldots , n \}$ is sampled (without replacement) with probability $\pi _ { i } ^ { k } > 0$ and each subproblem is solved exactly (cf. Step 2 in Algorithm 1). Then there exists a (random) limit point $q ^ { \star } \in$ arg min $\varphi ( \pmb q )$ such that

(3.4)

$$
\| \boldsymbol {q} ^ {k} - \boldsymbol {q} ^ {\star} \| _ {1} \xrightarrow [ k \to \infty ]{} 0 \quad a. s.
$$

Proof. We break down the proof into 3 main steps.

(i) Supermartingale structure. First, we show that the stochastic sequence of Bregman divergences $\left\{ D _ { \psi } \big ( \pmb q ^ { \star } , \pmb q ^ { \bar { k } } \big ) \right\} _ { k \in \mathbb { N } }$ is quasi-Fej´er monotone. By the three-point identity and the block-optimality condition

$$
\begin{array}{r l} D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k + 1}) + D _ {\psi} (\boldsymbol {q} ^ {k + 1}, \boldsymbol {q} ^ {k}) & \leq D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k}) + \gamma_ {k} \langle g _ {\varphi} (\boldsymbol {q} ^ {k + 1}), \boldsymbol {q} ^ {\star} - \boldsymbol {q} ^ {k + 1} \rangle \\ \text { convexity   of } \varphi & \leq D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k}) + \gamma_ {k} (\varphi (\boldsymbol {q} ^ {\star}) - \varphi (\boldsymbol {q} ^ {k + 1})) \\ & \leq D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k}). \end{array}
$$

Thus,

$$
D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k + 1}) \leq D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k}) - D _ {\psi} (\boldsymbol {q} ^ {k + 1}, \boldsymbol {q} ^ {k})\tag{3.5}
$$

Denote $\Delta _ { k } : = D _ { \psi } ( \pmb q ^ { \star } , \pmb q ^ { k } ) , \delta _ { k } : = D _ { \psi } ( \pmb q ^ { k + 1 } , \pmb q ^ { k } )$ , and $\mathcal { F } _ { k } : = \sigma ( \pmb { q } ^ { k } , . . . , \pmb { q } ^ { 0 } )$ the filtration generated by the sequence if iterates $\{ q ^ { i } \} _ { i = 0 } ^ { k }$ . Then, taking the conditional expectation of both sides of (3.5) yields

$$
\begin{array}{l l} \mathbb {E} [ \varDelta_ {k + 1} | \mathcal {F} _ {k} ] \leq \varDelta_ {k} - \mathbb {E} [ \delta_ {k} | \mathcal {F} _ {k} ] \\ (\delta_ {k} \geq 0) & \leq \varDelta_ {k}. \end{array}
$$

Hence $\varDelta _ { k } \geq 0$ is a positive supermartingale and therefore by the Robbins–Siegmund theorem [43]

1. $\Delta _ { k } \ \xrightarrow [ k \to \infty ] { } \ \Delta _ { \infty } \ \geq 0 \ \mathrm { a . s . }$

$$
2. \sum_ {k = 0} ^ {\infty} \mathbb {E} [ \delta_ {k} \mid \mathcal {F} _ {k} ] <   \infty \quad \Longrightarrow \quad \delta_ {k} \to 0 \text {a.s.} \quad \Longrightarrow \quad D _ {\psi} (\boldsymbol {q} ^ {k + 1}, \boldsymbol {q} ^ {k}) \to 0 \text {a.s.}
$$

(ii) Cluster points. Since the iterates $\{ \pmb q ^ { k } \}$ lie in the compact set Q, by the Bolzano–Weierstraß theorem there exists a (random) subsequence $\{ q ^ { k _ { j } } \} _ { j \in \mathbb { N } }$ and a point $\pmb q ^ { \infty } \in \mathcal { Q }$ such that

$$
\boldsymbol {q} ^ {k _ {j}} \xrightarrow [ j \to \infty ]{} \boldsymbol {q} ^ {\infty} \quad \text { a.s. }
$$

We now show ${ \pmb q } ^ { \infty } \in \arg \operatorname* { m i n } { \pmb \varphi } ( { \pmb q } )$

(a) Convergence in function values. Since $\textstyle \sum _ { k = 0 } ^ { \infty } \gamma _ { k } = + \infty$ , then by Theorem 3.2 $\varphi ( \pmb q ^ { k } )  \varphi ( \pmb q ^ { \star } )$ as $k \to \infty$ for any $\pmb { q } ^ { \star } \in \arg \operatorname* { m i n } { \varphi ( \pmb { q } ) }$

(b) The limit. Since $\varphi ( \pmb { q } ^ { k } )  \varphi ( \pmb { q } ^ { \star } ) , \varphi ( \pmb { q } ^ { k _ { j } } )  \varphi ( \pmb { q } ^ { \star } )$ as $j  \infty$ , and so $\varphi ( q ^ { \infty } ) \leq \varphi ( q ^ { \star } )$ because $\varphi$ is lower semicontinuous. Thus Thus

$\pmb { q } ^ { \infty } \in \underset { \pmb { q } \in \mathcal { Q } } { \arg \operatorname* { m i n } } \varphi ( \pmb { q } )$

(iii) Bregman–Opial argument and convergence. Now, let us take a subsequence $\{ q ^ { k _ { j } } \} _ { j \in \mathbb { N } }$ and a point $\pmb q ^ { \star } \in \mathcal { Q }$ such that

$$
\boldsymbol {q} ^ {k _ {j}} \underset {j \to \infty} {\longrightarrow} \boldsymbol {q} ^ {\star} \quad \text { a.s. }
$$

From part (ii), we have that $\pmb { q } ^ { \star } \in \underset { \pmb { q } \in \mathcal { Q } } { \arg \operatorname* { m i n } } \varphi ( \pmb { q } )$ . Then, since Q is a polytope, [35, Theorem 1] implies that

$$
D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k _ {j}}) \xrightarrow [ j \to \infty ]{} D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {\star}) = 0 \text { a.s. }
$$

Therefore, since $\varDelta _ { k }  \varDelta _ { \infty }$ by (i) and $D _ { \psi } ( \pmb q ^ { \star } , \pmb q ^ { k _ { j } } )  0$ , we conclude that

$$
D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k}) \rightarrow 0 \text { a.s. as } k \rightarrow \infty .
$$

Finally, invoking Theorem 2.5 yields

$$
\| \boldsymbol {q} ^ {k} - \boldsymbol {q} ^ {\star} \| _ {1} \xrightarrow [ k \to \infty ]{} 0 \quad \text { a.s. }
$$

which concludes the proof.

4. Practical implementation. This section discusses the practical implementation of Algorithm 1. We consider two settings: (i) deterministic, where CVaR, smoothed CVaR, and their respective (sub)gradients are computed either exactly or via sample average approximation (SAA); and (ii) stochastic, where only stochastic (e.g., mini-batch) estimates of the relevant quantities are available. Our focus here is on the practical implementation of the proposed method. For completeness, the deterministic and stochastic baseline algorithms used for performance comparisons in Section 5, together with the corresponding CVaR subgradient constructions, are deferred to Section B.

4.1. Deterministic setting. We first describe the deterministic implementation of EASIeST. For numerical comparisons, we also use a deterministic baseline subgradient method with adaptive stepsize control based on [29]; its pseudocode and the explicit deterministic CVaR subgradient formula are given in Subsection B.1.

Inexact Bregman proximal point method. Before presenting Algorithm 2, we discuss a key practical aspect: inexactness. Recall $\varphi ( \pmb q )$ defined in (2.24). The (exact) Bregman proximal point method computes $q ^ { k + 1 }$ by solving

$$
\mathbf {0} \in \partial \varphi (\boldsymbol {q} ^ {k + 1}) + \frac {1}{\gamma_ {k}} \bigl (\nabla \psi (\boldsymbol {q} ^ {k + 1}) - \nabla \psi (\boldsymbol {q} ^ {k}) \bigr),
$$

equivalently,

$$
\boldsymbol {q} ^ {k + 1} \in \underset {\boldsymbol {q}} {\arg \min} \left\{\varphi (\boldsymbol {q}) + \frac {1}{\gamma_ {k}} D _ {\psi} (\boldsymbol {q}, \boldsymbol {q} ^ {k}) \right\},
$$

which in our case leads to the subproblem (2.27b) (or (2.34)). In practice, this subproblem is rarely solved exactly, and one therefore replaces the exact optimality condition by an inexact one. Two widely used criteria are due to Eckstein [16] and Solodov–Svaiter [56].

Eckstein-type inexactness. Eckstein models the inexactness as an additive error in the Bregman optimality relation:

$$
\boldsymbol {e} ^ {k} + \nabla \psi (\boldsymbol {q} ^ {k}) = \nabla \psi (\boldsymbol {q} ^ {k + 1}) + \gamma_ {k} \boldsymbol {g} ^ {k + 1}, \quad \boldsymbol {g} ^ {k + 1} \in \partial \varphi (\boldsymbol {q} ^ {k + 1}),
$$

together with summability conditions on the error sequence, e.g., $\begin{array} { r } { \sum _ { k = 1 } ^ { \infty } \| e ^ { k } \| _ { 2 } < \infty } \end{array}$ and $\textstyle \sum _ { k = 1 } ^ { \infty } \langle e ^ { k } , q ^ { k } \rangle < \infty$ Intuitively, $e ^ { k }$ quantifies the residual in the dual (mirror) variable $\nabla \psi ( q )$ : the method behaves like the exact Bregman proximal point method up to a perturbation whose total accumulated efect is finite, which is suficient for convergence of the outer iterates under standard assumptions.

Solodov–Svaiter relative error criterion. Solodov and Svaiter propose a constructive relative termination rule based on the Bregman geometry. Given a candidate subgradient $\pmb { g } ^ { k + 1 } \in \partial \varphi ( \pmb { q } ^ { k + 1 } )$ , define the exact Bregman-prox point associated with $( q ^ { k } , g ^ { k + 1 } )$ as

$$
\boldsymbol {r} := \nabla \psi^ {- 1} \left(\nabla \psi (\boldsymbol {q} ^ {k}) - \gamma_ {k} \boldsymbol {g} ^ {k + 1}\right).
$$

Then the inexactness requirement is

$$
D _ {\psi} (\boldsymbol {q} ^ {k + 1}, \boldsymbol {r}) \leq \rho^ {2} D _ {\psi} (\boldsymbol {q} ^ {k + 1}, \boldsymbol {q} ^ {k}), \quad \rho \in (0, 1).
$$

This condition enforces that $\pmb q ^ { k + 1 }$ is significantly closer (in Bregman distance) to the ideal mirror step r than to the previous iterate $q ^ { k }$ , i.e., the inner solve makes relative progress measured in the same divergence that defines the proximal regularization. As a result, one obtains a globally convergent inexact Bregman proximal point method without requiring absolute summability of residuals or preconstructed error sequences, making the criterion appealing for stopping rules in iterative inner solvers.

A computable Solodov–Svaiter-type criterion. We adopt a Solodov–Svaiter-type relative rule, but the original criterion is not directly implementable in our setting. Indeed, $\varphi$ is defined through an inner mini mization (cf. (2.24)),

$$
\varphi (\boldsymbol {q}) = - \min _ {\boldsymbol {x} \in \mathcal {X}} \mathbb {E} _ {\boldsymbol {q}} [ F (\boldsymbol {x}, \omega) ].
$$

Consequently, by Danskin’s theorem, see $\mathrm { e . g . , ~ [ 1 4 , ~ 4 ] }$ , evaluating (or selecting) $\pmb { g } ^ { k + 1 } \in \partial \varphi ( \pmb { q } ^ { k + 1 } )$ requires access to a minimizer of the auxiliary problem

$$
\min _ {\boldsymbol {x} \in \mathcal {X}} \mathbb {E} _ {\boldsymbol {q}} [ F (\boldsymbol {x}, \omega) ],
$$

which would either force an (almost) exact inner solve or introduce an additional auxiliary optimization that we aim to avoid.

To quantify the efect of reusing an inner solution obtained for a nearby probability vector, define<sup>2</sup>

$$
f _ {\boldsymbol {q}} (\boldsymbol {x}) := \mathbb {E} _ {\boldsymbol {q}} \big [ F (\boldsymbol {x}, \omega) \big ], \qquad \nabla f _ {\boldsymbol {q}} (\boldsymbol {x}) = \mathbb {E} _ {\boldsymbol {q}} \big [ \nabla_ {\boldsymbol {x}} F (\boldsymbol {x}, \omega) \big ],
$$

and, for any $\beta > 0$ , the projected gradient mapping

$$
\mathcal {G} _ {\beta} (\boldsymbol {x}; \boldsymbol {q}) := \frac {1}{\beta} \left(\boldsymbol {x} - \operatorname{proj} _ {\mathcal {X}} \left(\boldsymbol {x} - \beta \nabla f _ {\boldsymbol {q}} (\boldsymbol {x})\right)\right),
$$

where a small $\| \mathcal { G } _ { \beta } ( \pmb { x } ; \pmb { q } ) \| _ { 2 }$ certifies near-stationarity of x for $\mathrm { m i n } _ { x \in \mathcal { X } } f _ { \pmb { q } } ( x )$ . The following result quantifies how $\| \mathcal { G } _ { \beta } ( \pmb { x } ; \pmb { q } ) \| _ { 2 }$ changes when the probability vector q is perturbed.

Proposition 4.1. Let $F : \mathcal { X } \times \mathcal { Q }  \mathbb { R }$ be diferentiable in x for all $\omega \in { \mathcal { Q } }$ . Assume that the scenariogradient is essentially bounded uniformly over $\mathcal { X } , i . e .$ , there exists $G _ { \mathcal { X } } < \infty$ such that

$$
\operatorname * {e s s   s u p} _ {\omega \in \Omega} \| \nabla_ {\boldsymbol {x}} F (\boldsymbol {x}, \omega) \| _ {2} \leq G _ {\mathcal {X}}, \quad \forall   \boldsymbol {x} \in \mathcal {X}.\tag{4.1}
$$

Then, for any $\mathbfit { q } , \tilde { \mathbfit { q } } \in \mathcal { Q }$ , any $\beta > 0$ , and any $\mathbf { \boldsymbol { x } } \in \mathcal { X }$ 2

$$
\left\| \mathcal {G} _ {\beta} (\boldsymbol {x}; \boldsymbol {q}) \right\| _ {2} \leq \left\| \mathcal {G} _ {\beta} (\boldsymbol {x}; \tilde {\boldsymbol {q}}) \right\| _ {2} + G _ {\mathcal {X}} \sqrt {2 D _ {\psi} (\boldsymbol {q} , \tilde {\boldsymbol {q}})}.\tag{4.2}
$$

Proof. By the triangle inequality,

$$
\| \mathcal {G} _ {\beta} (\boldsymbol {x}; \boldsymbol {q}) \| _ {2} \leq \| \mathcal {G} _ {\beta} (\boldsymbol {x}; \tilde {\boldsymbol {q}}) \| _ {2} + \| \mathcal {G} _ {\beta} (\boldsymbol {x}; \boldsymbol {q}) - \mathcal {G} _ {\beta} (\boldsymbol {x}; \tilde {\boldsymbol {q}}) \| _ {2}.
$$

Using nonexpansiveness of the Euclidean projection proj<sub>X</sub>,

$$
\begin{array}{r l} & {\| \mathcal {G} _ {\beta} (\boldsymbol {x}; \boldsymbol {q}) - \mathcal {G} _ {\beta} (\boldsymbol {x}; \tilde {\boldsymbol {q}}) \| _ {2} = \frac {1}{\beta} \Big \| \mathrm{proj} _ {\mathcal {X}} \left(\boldsymbol {x} - \beta \nabla f _ {\boldsymbol {q}} (\boldsymbol {x})\right) - \mathrm{proj} _ {\mathcal {X}} \left(\boldsymbol {x} - \beta \nabla f _ {\tilde {\boldsymbol {q}}} (\boldsymbol {x})\right) \Big \| _ {2}} \\ & {\qquad \leq \frac {1}{\beta} \Big \| \big (\boldsymbol {x} - \beta \nabla f _ {\boldsymbol {q}} (\boldsymbol {x}) \big) - \big (\boldsymbol {x} - \beta \nabla f _ {\tilde {\boldsymbol {q}}} (\boldsymbol {x}) \big) \Big \| _ {2}} \\ & {\qquad = \| \nabla f _ {\boldsymbol {q}} (\boldsymbol {x}) - \nabla f _ {\tilde {\boldsymbol {q}}} (\boldsymbol {x}) \| _ {2}.} \end{array}
$$

In the finite-scenario setting, $\begin{array} { r } { \nabla f _ { q } ( { \pmb x } ) = \sum _ { i = 1 } ^ { n } q _ { i } \nabla F _ { i } ( { \pmb x } ) } \end{array}$ , hence

$$
\nabla f _ {\boldsymbol {q}} (\boldsymbol {x}) - \nabla f _ {\tilde {\boldsymbol {q}}} (\boldsymbol {x}) = \sum_ {i = 1} ^ {n} (q _ {i} - \tilde {q} _ {i}) \nabla F _ {i} (\boldsymbol {x}).
$$

Therefore, using $\begin{array} { r } { \| \nabla F _ { i } ( { \pmb x } ) \| _ { 2 } \leq \operatorname* { m a x } _ { j } \| \nabla F _ { j } ( { \pmb x } ) \| _ { 2 } \leq G _ { \mathcal { X } } , } \end{array}$

$$
\| \nabla f _ {\boldsymbol {q}} (\boldsymbol {x}) - \nabla f _ {\tilde {\boldsymbol {q}}} (\boldsymbol {x}) \| _ {2} \leq \sum_ {i = 1} ^ {n} | q _ {i} - \tilde {q} _ {i} | \| \nabla F _ {i} (\boldsymbol {x}) \| _ {2} \leq G _ {\mathcal {X}} \| \boldsymbol {q} - \tilde {\boldsymbol {q}} \| _ {1}.
$$

Finally, by Theorem 2.5, $\| \pmb { q } - \tilde { \pmb { q } } \| _ { 1 } \le \sqrt { 2 D _ { \psi } ( \pmb { q } , \tilde { \pmb { q } } ) }$ , which yields

$$
\| \mathcal {G} _ {\beta} (\boldsymbol {x}; \boldsymbol {q}) \| _ {2} \leq \| \mathcal {G} _ {\beta} (\boldsymbol {x}; \tilde {\boldsymbol {q}}) \| _ {2} + G _ {\mathcal {X}} \sqrt {2 D _ {\psi} (\boldsymbol {q} , \tilde {\boldsymbol {q}})}.
$$

Remark 4.1. Under the assumptions of Theorem 4.1, one also has

$$
\left\| \mathcal {G} _ {\beta} (\boldsymbol {x}; \boldsymbol {q}) \right\| _ {2} \leq \left\| \mathcal {G} _ {\beta} (\boldsymbol {x}; \tilde {\boldsymbol {q}}) \right\| _ {2} + G _ {\mathcal {X}} \sqrt {n} \| \boldsymbol {q} - \tilde {\boldsymbol {q}} \| _ {2},
$$

for any q, $\tilde { \pmb q } \in \mathcal { Q }$ , any $\beta > 0$ , and any $\boldsymbol { \mathbf { \mathit { \mathbf { \mathit { \mathbf { \Lambda } } } } } } \mathbf { \mathit { \mathbf { \Lambda } } } \mathbf { \boldsymbol { \mathbf { \Lambda } } } \mathbf { \Xi } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf { \Lambda } \mathbf \mathbf { \Lambda } \mathbf { \Lambda } \mathbf \mathbf { \Lambda } \mathbf { \Lambda } \mathbf \mathbf { \Lambda } \mathbf \mathbf { \Lambda } \mathbf \mathbf { \Lambda } \mathbf \Lambda \mathbf \Lambda \mathbf { } \mathbf \Lambda \mathbf \Lambda \Lambda \mathbf \Lambda \mathbf { } \mathbf \Lambda \mathbf \Lambda \Lambda \mathbf \Lambda \mathbf \Lambda \mathbf  \mathbf \mathbf \mathbf \mathbf \Lambda \mathbf \Lambda \mathbf \Lambda \mathbf \Lambda \mathbf \Lambda \mathbf \Lambda \mathbf \Lambda \mathbf \mathbf \Lambda \mathbf \Lambda \mathbf \Lambda \mathbf \mathbf \Lambda \mathbf \mathbf \Lambda \mathbf \mathbf \Lambda \mathbf \Lambda \mathbf \mathbf \mathbf \Lambda \mathbf \mathbf \Lambda \mathbf \Lambda \mathbf \mathbf \mathbf \Lambda \mathbf \mathbf \Lambda \mathbf \mathbf \mathbf \mathbf \Lambda \mathbf \mathbf \mathbf \Lambda \mathbf \mathbf \Lambda \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \Lambda \mathbf \mathbf \mathbf \mathbf \mathbf \Lambda \mathbf \mathbf \mathbf \mathbf \Lambda \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \Lambda \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf \mathbf $ . This follows from the estimate

$$
\| \nabla f _ {\boldsymbol {q}} (\boldsymbol {x}) - \nabla f _ {\tilde {\boldsymbol {q}}} (\boldsymbol {x}) \| _ {2} \leq G _ {\mathcal {X}} \| \boldsymbol {q} - \tilde {\boldsymbol {q}} \| _ {1} \leq G _ {\mathcal {X}} \sqrt {n} \| \boldsymbol {q} - \tilde {\boldsymbol {q}} \| _ {2}.
$$

Such a bound is important for controlling inexactness in the classical proximal point setup $[ 4 4 , 4 9 ] ,$ which leads to quadratic epi-regularization of the CVaR [21]. Note that the above bound depends explicitly on n. Consequently, the resulting estimate deteriorates with the dimension, which makes the bound in Theorem 4.1 based on the Bregman divergence more attractive.

At outer iteration $k ,$ applying the original Solodov–Svaiter (SS) test at an approximate proximal point q would require a subgradient $\pmb { \mathscr { g } } \in \partial \varphi ( \pmb { q } )$ and thus, by (2.24), solving the auxiliary problem min $\pmb { x } \in \mathcal { X } \operatorname { \mathbb { E } } _ { \pmb { q } } [ F ( \pmb { x } , \omega ) ]$ To avoid this extra solve, we generate two successive candidate pairs $( q _ { 1 } , x _ { 1 } )$ and $( q _ { 2 } , x _ { 2 } )$ from the same inner routine, where $( q _ { 2 } , x _ { 2 } )$ is a refinement of $( q _ { 1 } , x _ { 1 } )$ , and we accept $( q _ { 1 } , x _ { 2 } )$ only when two simultaneous conditions hold.

(i) Modified SS condition. We enforce the computable SS surrogate

$$
D _ {\psi} (\pmb {q} _ {1}, \pmb {q} _ {2}) \leq \rho_ {k} ^ {2} D _ {\psi} (\pmb {q} _ {1}, \pmb {q} ^ {k}), \quad \rho_ {k} \in (0, 1), \rho_ {k} \downarrow 0,
$$

which ensures that the refinement $\pmb { q } _ { 2 }$ is relatively close to $\pmb q _ { 1 }$ compared to the outer step size.

(ii) Gradient (stationarity) condition. We also require that the refined inner point $\mathbf { { x } } _ { 2 }$ satisfies the projectedgradient bound

$$
\left\| \mathcal {G} _ {\beta} (\boldsymbol {x} _ {2}; \boldsymbol {q} _ {2}) \right\| _ {2} \leq G _ {\mathcal {X}} \rho_ {k} \sqrt {2 D _ {\psi} (\boldsymbol {q} _ {1} , \boldsymbol {q} ^ {k})}.
$$

By Proposition 4.1, this implies

$$
\left\| \mathcal {G} _ {\beta} (\boldsymbol {x} _ {2}; \boldsymbol {q} _ {1}) \right\| _ {2} \leq \left\| \mathcal {G} _ {\beta} (\boldsymbol {x} _ {2}; \boldsymbol {q} _ {2}) \right\| _ {2} + G _ {\mathcal {X}} \sqrt {2 D _ {\psi} (\boldsymbol {q} _ {1} , \boldsymbol {q} _ {2})} \leq 2 G _ {\mathcal {X}} \rho_ {k} \sqrt {2 D _ {\psi} (\boldsymbol {q} _ {1} , \boldsymbol {q} ^ {k})}.
$$

Hence, if $\rho _ { k } \to 0 .$ , the projected-gradient residual associated with the auxiliary problem min $\textstyle \cdot x \in \mathcal { X } \operatorname { \mathbb { E } } _ { \pmb { q } _ { 1 } } \left[ F ( \ b { x } , \omega ) \right]$ is driven to zero asymptotically, recovering the auxiliary optimality conditions without explicitly solving that problem.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2: EASIEST for CVaR Optimization (“deterministic”)

Input :  $x^{0} \in X$  and  $s^{0} \in R^{n}$ ,  $q^{0} = \sigma(s^{0})$ .

Parameters:  $\gamma_{0}, \beta &gt; 0$ ,  $c_{\gamma} &gt; 1$ ,  $\varepsilon_{g}, \varepsilon_{TV}, \varepsilon_{q} &gt; 0$ ,  $\{\rho_{k}\} \in (0,1)$ ,  $|B| &gt; 1$ ,  $K, J \in N$ .

Define : Sigmoid map:  $\sigma_{i}(s) := \frac{p_{i}}{1 - \alpha} \frac{e^{s}}{1 + e^{s}}$ ; vector form  $\sigma(s)$ .

Output :  $x^{\star} \in X$ ,  $q^{\star} = \sigma(s^{\star}) \in Q$ , and  $\text{CVaR}_{\alpha}(F(x^{\star}, \omega)) = \mathbb{E}_{q^{\star}}[F(x^{\star}, \omega)]$ .

for  $k = 0, 1, 2, \ldots, K$  do // Outer loop

Step 0. Initialize  $x^{k,0} = x^{k}$ ,  $s^{k,0} = s^{k}$ ,  $q^{k,0} = q^{k}$ ;

Step 1. Generate  $B_{k} = BlockSampler(q^{k}, |B|)$  and set  $\delta_{k} = \sum_{i \in B_{k}} q_{i}^{k}$ ;

for  $j = 0, 1, 2, \ldots, J$  do // Inner loop

Step 2. Set  $(s^{k,j+1}, q^{k,j+1}) = \text{ProxUpdate}(x^{k,j}, s^{k}, q^{k}, B_{k}, \gamma_{k}, \delta_{k})$ ;

Step 3. Set  $I_{j} = \{i : q_{i}^{k,j+1} \geq \varepsilon_{q}\}$  and evaluate  $\{\nabla F_{i}(x^{k,j})\}_{i \in I_{j}}$ ;

Step 4. Compute  $g^{k,j} = \sum_{i \in I_{j}} q_{i}^{k,j+1} \nabla F_{i}(x^{k,j})$ ;

Step 5. Set  $G_{\chi}^{j} = \max_{i \in I_{j}} \| \nabla F_{i}(x^{k,j}) \|_{2}$  and  $D_{j} = \rho_{k}^{2} D_{\psi}(q^{k,j}, q^{k})$ ;

if  $\|G_{\beta}(x^{k,j}; q^{k,j+1}) \|_{2} \leq G_{\chi}^{j} \sqrt{2D_{j}}$  and  $D_{\psi}(q^{k,j}, q^{k,j+1}) \leq D_{j}$  then

Step break

Step 6. Set  $x^{k,j+1} = Update(x^{k,j}, g^{k,j}, solver parameters)$ ;

Step 7. If the inner loop terminates at Step 5 on index j, set  $s^{k+1} = s^{k,j+1}$ ,  $q^{k+1} = q^{k,j+1}$ , and  $x^{k+1} = x^{k,j}$ ; otherwise, set  $s^{k+1} = s^{k,j+1}$ ,  $q^{k+1} = q^{k,j+1}$ , and  $x^{k+1} = x^{k,j+1}$ ;

Step 8. Update  $\gamma_{k+1} = c_{\gamma} \gamma_{k}$ ;

if  $\|G_{\beta}(x^{k+1}; q^{k+1}) \|_{2} \leq \varepsilon_{g}$  and  $\frac{1}{2} \|q^{k+1} - q^{k} \|_{1} \leq \varepsilon_{TV}$  then

break

return  $x^{\star} \leftarrow x^{k+1}$ ,  $q^{\star} \leftarrow q^{k+1}$ , and  $CVaR_{\alpha}(F(x^{\star}, \omega)) = E_{q^{\star}}[F(x^{\star}, \omega)]$ .
</div>

Algorithm 2 is the practical version of Algorithm 1 in the deterministic setting. Each outer iteration k samples a block $\boldsymbol { B } _ { k }$ of scenarios according to the current dual distribution $q ^ { k }$ and updates only the corresponding logits $s _ { i } ^ { k } : = \nabla \psi ( q _ { i } ^ { k } )$ ) for $i \in \boldsymbol { B } _ { k }$ , while keeping $q _ { i } ^ { k }$ fixed for $i \notin \boldsymbol { B } _ { k }$ and preserving the block mass $\begin{array} { r } { \delta _ { k } = \bar { \sum _ { i \in B _ { k } } q _ { i } ^ { k } } } \end{array}$ via a scalar shift (cf. Algorithm 6). The primal variable is then updated by a user-specified routine $\pmb { x } ^ { k , j + 1 } = \mathrm { U p d a t e } ( \pmb { x } ^ { k , j } , \pmb { g } ^ { k , j } , \dots )$ (e.g., projected gradient, quasi-Newton, or any convex solver), so the algorithm can leverage problem structure and available inner solvers. Inexactness is controlled by two simultaneous stopping tests: a computable Solodov–Svaiter-type condition based on two consecutive dual iterates w.r.t. the Bregman distance and a projected-gradient stationarity test in x.

Remark 4.2. The definition of $\mathcal { G } _ { \beta } ( \pmb { x } ; \pmb { q } )$ above assumes that $F ( \cdot , \omega )$ is diferentiable, so that $\nabla f _ { q } ( { \pmb x } ) =$ $\mathbb { E } _ { q } [ \nabla _ { \pmb { x } } F ( \pmb { x } , \omega ) ]$ is well-defined. If $F ( \cdot , \omega )$ is convex but possibly nondiferentiable, we replace the projectedgradient mapping by a proximal-gradient (resolvent) stationarity measure.

Fix $\beta > 0$ and select any measurable subgradient field ${ \pmb g } _ { F } ( { \pmb x } , \omega ) \in \partial _ { { \pmb x } } F ( { \pmb x } , \omega )$ . Define

$$
\partial f _ {\boldsymbol {q}} (\boldsymbol {x}) = \mathbb {E} _ {\boldsymbol {q}} \big [ \partial_ {\boldsymbol {x}} F (\boldsymbol {x}, \omega) \big ] \quad a n d p i c k \quad \boldsymbol {v} _ {\boldsymbol {q}} (\boldsymbol {x}) \in \partial f _ {\boldsymbol {q}} (\boldsymbol {x}) (e. g., \boldsymbol {v} _ {\boldsymbol {q}} (\boldsymbol {x}) = \mathbb {E} _ {\boldsymbol {q}} [ \boldsymbol {g} _ {F} (\boldsymbol {x}, \omega) ]).
$$

We then define the proximal stationarity mapping

$$
\mathcal {P} _ {\beta} (\boldsymbol {x}; \boldsymbol {q}) := \frac {1}{\beta} \left(\boldsymbol {x} - \operatorname{prox} _ {\beta \delta_ {\mathcal {X}}} \left(\boldsymbol {x} - \beta \boldsymbol {v} _ {\boldsymbol {q}} (\boldsymbol {x})\right)\right) = \frac {1}{\beta} \left(\boldsymbol {x} - \operatorname{proj} _ {\mathcal {X}} \left(\boldsymbol {x} - \beta \boldsymbol {v} _ {\boldsymbol {q}} (\boldsymbol {x})\right)\right),
$$

where $\delta _ { X }$ is the indicator of X and $\operatorname { p r o x } _ { \beta \delta x } = \operatorname { p r o j } _ { x }$ . In particular, $\mathcal { P } _ { \beta } ( { \pmb x } ; { \pmb q } ) = { \bf 0 }$ if and only if

$$
\mathbf {0} \in \partial f _ {\boldsymbol {q}} (\boldsymbol {x}) + \mathcal {N} _ {\mathcal {X}} (\boldsymbol {x}),
$$

i.e., x is a (first-order) stationary point of $\begin{array} { r } { \operatorname* { m i n } _ { { \pmb x } \in { \mathcal X } } f _ { \pmb q } ( { \pmb x } ) } \end{array}$ in the standard convex-analytic sense. When $f _ { q }$ is diferentiable, choosing ${ \pmb v } _ { { \pmb q } } ( { \pmb x } ) = \nabla f _ { { \pmb q } } ( { \pmb x } )$ recovers the projected-gradient mapping $\mathcal { G } _ { \beta }$

4.2. Stochastic setting. We next consider the stochastic setting, where only mini-batch estimates of the relevant quantities are available. For numerical comparisons, we also use a stochastic adaptivesubgradient baseline based on [29]; its pseudocode and the corresponding mini-batch CVaR subgradient construction are deferred to Subsection B.2.

To define the stochastic stationarity tests used in Algorithm 3, let $\xi _ { 1 } , \ldots , \xi _ { m } \stackrel { \mathrm { i i d } } { \sim } q$ and define the minibatch estimator

$$
\widehat {\nabla} f _ {\boldsymbol {q}} ^ {(m)} (\boldsymbol {x}) := \frac {1}{m} \sum_ {r = 1} ^ {m} \nabla F _ {\xi_ {r}} (\boldsymbol {x}), \quad \text { so   that } \quad \mathbb {E} \Big [ \widehat {\nabla} f _ {\boldsymbol {q}} ^ {(m)} (\boldsymbol {x}) \Big ] = \nabla f _ {\boldsymbol {q}} (\boldsymbol {x}).
$$

We then define the mini-batch stochastic reduced (projected-gradient) mapping as

$$
\widehat {\mathcal {G}} _ {\beta} ^ {(m)} (\boldsymbol {x}; \boldsymbol {q}) := \frac {1}{\beta} \left(\boldsymbol {x} - \operatorname{proj} _ {\mathcal {X}} \left(\boldsymbol {x} - \beta \widehat {\nabla} f _ {\boldsymbol {q}} ^ {(m)} (\boldsymbol {x})\right)\right).
$$

If the batch is drawn from a reference distribution $\pmb { r } \in \mathcal { Q } \left( \mathrm { e . g . } \right.$ , fixed throughout an inner loop), an unbiased estimator of $\nabla f _ { q } ( { \pmb x } )$ is

$$
\widehat {\nabla} f _ {\boldsymbol {q}} ^ {(m)} (\boldsymbol {x} \mid \boldsymbol {r}) := \frac {1}{m} \sum_ {r = 1} ^ {m} \frac {q _ {\xi_ {r}}}{r _ {\xi_ {r}}} \nabla F _ {\xi_ {r}} (\boldsymbol {x}),
$$

and the corresponding certificate is

$$
\widehat {\mathcal {G}} _ {\beta} ^ {(m)} (\boldsymbol {x}; \boldsymbol {q} \mid \boldsymbol {r}) := \frac {1}{\beta} \left(\boldsymbol {x} - \operatorname{proj} _ {\mathcal {X}} \left(\boldsymbol {x} - \beta \widehat {\nabla} f _ {\boldsymbol {q}} ^ {(m)} (\boldsymbol {x} \mid \boldsymbol {r})\right)\right).
$$

Algorithm 3 is the practical version of Algorithm 1 in the stochastic setting. It mirrors the deterministic scheme, but replaces exact gradient information by mini-batch estimators and uses an importance-weighted stationarity certificate relative to the reference distribution $q ^ { k }$ . As in the deterministic case, the method combines a computable Solodov–Svaiter-type stopping condition in the dual variable with a stationarity test for the primal update.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3: EASIEST for CVaR Optimization (“stochastic”)

Input : $x^0 \in \mathcal{X}$ and $s^0 \in \mathbb{R}^n$, $q^0 = \sigma(s^0)$.

Parameters: $\gamma_0, \beta &gt; 0$, $c_\gamma &gt; 1$, $\varepsilon_g, \varepsilon_{TV}, \varepsilon_q &gt; 0$, $\{\rho_k\} \in (0,1)$, $|\mathcal{B}| &gt; 1$, $K, J, m \in \mathbb{N}$.

Define : Sigmoid map: $\sigma_i(s) := \frac{p_i}{1 - \alpha} \frac{e^s}{1 + e^s}$; vector form $\sigma(s)$.

Output : $x^\star \in \mathcal{X}$, $q^\star = \sigma(s^\star) \in \mathcal{Q}$, and $\text{CVaR}_\alpha(F(x^\star, \omega)) = \mathbb{E}_{q^\star}[F(x^\star, \omega)]$.

for $k = 0, 1, 2, \ldots, K$ do // Outer loop

Step 0. Initialize $x^{k,0} = x^k$, $s^{k,0} = s^k$, $q^{k,0} = q^k$;

Step 1. Generate $B_k = \text{BlockSampler}(q^k, |\mathcal{B}|)$ and set $\delta_k = \sum_{i \in B_k} q_i^k$;

for $j = 0, 1, 2, \ldots, J$ do // Inner loop

Step 2. Sample indices $\xi_1, \ldots, \xi_m \stackrel{\text{iid}}{\sim} q^k$ and construct index sets
$\Xi_j = \{\xi_1, \ldots, \xi_m\}$, $\Xi_j^{in} = \{i \in \Xi_j : i \in B_k \cap \Xi_j\}$, $\Xi_j^{out} = \{i \in \Xi_j : i \notin B_k \cap \Xi_j\}$ and
$w_i = \frac{\# of times index i \in \Xi_j repeats}{|\Xi_j|}$;

Step 3. Set $(s^{k,j+1}, q^{k,j+1}) = \text{ProxUpdate}(x^{k,j}, s^k, q^k, B_k, \gamma_k, \delta_k)$;

Step 4. Set $I_j = \{i \in \Xi_j^{in} : q_i^{k,j+1} \geq \varepsilon_q\}$ and evaluate $\{\nabla F_i(x^{k,j})\}_{i \in I_j \cup \Xi_j^{out}}$;

Step 5. Set $g^{k,j} = \sum_{i \in \Xi_j^{out}} w_i \nabla F_i(x^{k,j}) + \sum_{i \in I_j} w_i \frac{q_i^{k,j+1}}{q_i^k} \nabla F_i(x^{k,j})$;

Step 6. If $|I_j| \neq 0$ define $S = I_j$ else $S = \Xi_j^{out}$. Set $G_x^j = \max_{i \in S} \|V F_i(x^{k,j})\|_2$ and
$D_j = p_k^2 D_\psi(q^{k,j}, q^k)$;

if $\|G_{\beta}^{(m)}(x^{k,j}; q^{k,j+1} | q^k)\|_2 \leq G_x^j / 2D_j$ and $D_\psi(q^{k,j}, q^{k,j+1}) \leq D_j$ then
└ break

Step 7. Set $x^{k,j+1} = Update(x^{k,j}, g^{k,j}, solver parameters)$;

Step 8. If the inner loop terminates at Step 6 on index $j$, set $s^{k+1} = s^{k,j+1}$, $q^{k+1} = q^{k,j+1}$, and
$x^{k+1} = x^{k,j}$; otherwise, set $s^{k+1} = s^{k,j+1}$, $q^{k+1} = q^{k,j+1}$, and $x^{k+1} = x^{k,j+1}$;

Step 9. Update $y_{k+1} = c_y y_k$;

if $\|G_{\beta}^{(m)}(x^{k+1}; q^{k+1} | q^k)\|_2 \leq e_g$ and $1/2 \|q^{k+1} - q^k\|_1 \leq e_{TV}$ then
└ break

return $x^\star &lt; x^{k+1}$, $q^\star &lt; q^{k+1}$, and CVaR$_\alpha(F(x^\star, \omega)) = E_{q^\star}[F(x^\star, \omega)]$.
</div>

5. Numerical experiments. This section reports numerical experiments evaluating Algorithm 2 and Algorithm 3. We benchmark their performance against the corresponding deterministic and stochastic subgradient baselines with adaptive step sizes based on [29]; see Algorithms 4 and 5 in Section B. In the deterministic setting, we additionally compare against Shor’s r-algorithm [55] and with the EASIeST variant corresponding to the classical proximal point method proposed in [21], obtained by replacing the Bregman divergence term $D _ { \psi } ( q , r )$ with the quadratic term ${ \frac { 1 } { 2 } } \| q - r \| _ { 2 } ^ { 2 }$ . Because the underlying optimization problem is nonsmooth, we measure computational efort by first-order oracle complexity, i.e., the total number of oracle calls returning a function value and a (sub)gradient. Additionally, we report the suboptimality gap

$$
f (\pmb {x} ^ {k}) - f ^ {\star},
$$

where $f ^ { \star }$ denotes the reference optimal value, versus the cumulative number of per-scenario function evaluations and gradient evaluations separately. This distinction is important for certain classes of problems, such as PDE-constrained optimization.

5.1. Support Vector Classification. We consider binary classification with training samples $\{ ( y _ { i } , z _ { i } ) \} _ { i = 1 } ^ { n }$ , where $z _ { i } \in \mathbb { R } ^ { d }$ are feature vectors and $y _ { i } \in \{ - 1 , + 1 \}$ are class labels. Let the extended feature vector be $\bar { z } _ { i } : = ( 1 , z _ { i } ^ { \top } ) ^ { \top } \in \mathbb { R } ^ { d + 1 }$ , then define the decision vector

$$
\boldsymbol {x} := (x _ {0}, \ldots , x _ {d}) ^ {\top} \in \mathbb {R} ^ {d + 1}.
$$

Our goal is to learn a linear decision rule parameterized by $\pmb { x } \in \mathbb { R } ^ { d + 1 }$

$$
a (\boldsymbol {x}, \bar {\boldsymbol {z}}) := \mathrm{sign} (\boldsymbol {x} ^ {\top} \bar {\boldsymbol {z}}),
$$

which assigns to each observation i with extended feature vector $\bar { z } _ { i } \in \mathbb { R } ^ { d + 1 }$ a predicted class label $a ( \pmb { x } , \bar { \pmb { z } } _ { i } ) \in$ $\{ - 1 , + 1 \}$ . For each sample i, we define the signed margin loss

$$
F _ {i} (\boldsymbol {x}) := - y _ {i} \boldsymbol {x} ^ {\top} \bar {\boldsymbol {z}} _ {i}, \qquad i = 1, \ldots , n,
$$

and write $F ( \pmb { x } , \omega )$ as the random variable taking values $\{ F _ { i } ( { \pmb x } ) \} _ { i = 1 } ^ { n }$ under the baseline distribution ${ \textbf { \em p } } =$ $\left( p _ { 1 } , \ldots , p _ { n } \right)$ (in our experiments we take $p _ { i } = 1 / n )$ . To promote robustness to misclassified or low-margin points, we replace the mean loss with the tail risk $\mathrm { C V a R } _ { \alpha } ( F ( { \pmb x } , \omega ) )$ . With $\ell _ { 2 }$ regularization, the resulting CVaR-SVM model (cf. [58]) is

$$
\min _ {\boldsymbol {x} \in \mathbb {R} ^ {d + 1}} \Big \{f (\boldsymbol {x}) := \mathrm{CVaR} _ {\alpha} \left(F (\boldsymbol {x}, \omega)\right) + \frac {\lambda}{2} \sum_ {i - 1} ^ {d} x _ {i} ^ {2} \Big \},\tag{5.1}
$$

where $\lambda > 0$ controls regularization and is taken to be $1 0 ^ { - 3 }$ in the numerical experiments.

Data. In our numerical experiments, we fix a decision vector $\pmb { x } = ( 0 , x _ { 1 } , \ldots , x _ { d } ) \in \mathbb { R } ^ { d + 1 }$ with $d = 8 5$ and generate $n = 2 \times 1 0 ^ { 4 }$ feature vectors $z _ { i } \overset { \mathrm { i i d } } { \sim } \mathcal { N } ( \mathbf { 0 } , I _ { d } )$ . Let $\bar { z } _ { i } : = ( 1 , z _ { i } ^ { \top } ) ^ { \top } \in \mathbb { R } ^ { d + 1 }$ denote the extended feature vector. Given x and $\bar { z } _ { i }$ , the class label is assigned by

$$
y _ {i} = \mathrm{sign} (\pmb {x} ^ {\top} \bar {\pmb {z}} _ {i}).
$$

5.1.1. Deterministic case. In this setting, we solve the CVaR-SVM problem (5.1) using Algorithm 2, Shor’s r-algorithm (implemented following the recommendations in [57]), the baseline method Algorithm 4, and the variant corresponding to the classical proximal point method proposed in [21]. We abbreviate the latter by PD, short for primal-dual, following the terminology of [21]. However, rather than implementing that method exactly as in the original paper, we employ an implementation consistent with EASIeST, where a quadratic prox term replaces the Bregman prox term with necessary adjustments for handling inexactness (cf. Remark 4.1). We denote by $f _ { j } = f ( \pmb { x } ^ { j } )$ the objective value at iterate $j ,$ and as the optimal CVaR value $f ^ { \star } = f ( { \pmb x } ^ { \star } )$ , we use the value reported by the PSG solver van [38] with precision parameter 7.

Parameter settings for Algorithm 2 and PD. We set $\gamma _ { 0 } ~ = ~ 1 ( \gamma _ { 0 } ~ = ~ 1 0 ^ { - 4 } ~ \mathrm { f o r ~ P D } ) , ~ c _ { \gamma } ~ = ~ 1 . 0 8 , ~ \varepsilon _ { g } ~ =$ $1 0 ^ { - 6 } , \ \varepsilon _ { T V } = 1 0 ^ { - 5 } , \varepsilon _ { q } = 1 0 ^ { - 1 0 } , | \mathcal { B } | = n , \ K = 1 3 0 , \ J = 6 0 0 ,$

$$
\rho_ {k} ^ {2} = \left\{ \begin{array}{l l} 1 0 ^ {- 3} & \text { if } \alpha = 0. 9 \\ 3 \times 1 0 ^ {- 4} & \text { if } \alpha = 0. 9 5 \\ 1 0 ^ {- 4} & \text { if } \alpha = 0. 9 8 \end{array} \right.
$$

As the subproblem solver, we use Algorithm 2 (adaptive accelerated gradient descent heuristic) from [25].

Table 5.1  
Convergence in oracle calls at prescribed accuracy levels.

<table><tr><td rowspan="2">Gap</td><td colspan="4"> $\alpha = 0.90$ </td><td colspan="4"> $\alpha = 0.95$ </td><td colspan="4"> $\alpha = 0.98$ </td></tr><tr><td>EASIEST</td><td>r-alg</td><td>Baseline</td><td>PD</td><td>EASIEST</td><td>r-alg</td><td>Baseline</td><td>PD</td><td>EASIEST</td><td>r-alg</td><td>Baseline</td><td>PD</td></tr><tr><td> $10^{-1}$ </td><td>53</td><td>133</td><td>206</td><td>62</td><td>44</td><td>174</td><td>183</td><td>26</td><td>8</td><td>85</td><td>321</td><td>103</td></tr><tr><td> $10^{-2}$ </td><td>80</td><td>182</td><td>539</td><td>94</td><td>117</td><td>306</td><td>335</td><td>68</td><td>14</td><td>330</td><td>444</td><td>251</td></tr><tr><td> $10^{-3}$ </td><td>113</td><td>308</td><td>1454</td><td>137</td><td>196</td><td>450</td><td>616</td><td>208</td><td>71</td><td>473</td><td>880</td><td>510</td></tr><tr><td> $10^{-4}$ </td><td>192</td><td>465</td><td>&gt;3000</td><td>273</td><td>380</td><td>599</td><td>1486</td><td>447</td><td>314</td><td>632</td><td>—</td><td>1045</td></tr><tr><td> $10^{-5}$ </td><td>423</td><td>659</td><td>—</td><td>494</td><td>722</td><td>791</td><td>—</td><td>790</td><td>602</td><td>762</td><td>—</td><td>—</td></tr><tr><td> $10^{-6}$ </td><td>707</td><td>—</td><td>—</td><td>767</td><td>1290</td><td>—</td><td>—</td><td>987</td><td>684</td><td>809</td><td>—</td><td>—</td></tr></table>

Table 5.2  
Convergence in (per-scenario) function evaluations $( \times 1 0 ^ { 6 } )$ at prescribed accuracy levels.

<table><tr><td rowspan="2">Gap</td><td colspan="4"> $\alpha = 0.90$ </td><td colspan="4"> $\alpha = 0.95$ </td><td colspan="4"> $\alpha = 0.98$ </td></tr><tr><td>EASIEST</td><td>r-alg</td><td>Baseline</td><td>PD</td><td>EASIEST</td><td>r-alg</td><td>Baseline</td><td>PD</td><td>EASIEST</td><td>r-alg</td><td>Baseline</td><td>PD</td></tr><tr><td> $10^{-1}$ </td><td>1.06</td><td>2.66</td><td>4.12</td><td>1.24</td><td>0.8</td><td>3.5</td><td>3.7</td><td>0.52</td><td>0.16</td><td>1.7</td><td>6.42</td><td>2.06</td></tr><tr><td> $10^{-2}$ </td><td>1.6</td><td>3.64</td><td>10.8</td><td>1.88</td><td>2.3</td><td>6.1</td><td>6.7</td><td>1.36</td><td>0.28</td><td>6.6</td><td>8.88</td><td>5.02</td></tr><tr><td> $10^{-3}$ </td><td>2.2</td><td>6.2</td><td>29</td><td>2.74</td><td>3.7</td><td>9</td><td>12.3</td><td>4.16</td><td>1.42</td><td>9.46</td><td>17.6</td><td>10.2</td></tr><tr><td> $10^{-4}$ </td><td>3.02</td><td>9.3</td><td>—</td><td>5.46</td><td>5.07</td><td>11.98</td><td>29.7</td><td>8.94</td><td>3.36</td><td>12.6</td><td>—</td><td>20.9</td></tr><tr><td> $10^{-5}$ </td><td>3.7</td><td>13.2</td><td>—</td><td>9.88</td><td>5.73</td><td>15.82</td><td>—</td><td>15.8</td><td>3.77</td><td>15.2</td><td>—</td><td>—</td></tr><tr><td> $10^{-6}$ </td><td>4.3</td><td>—</td><td>—</td><td>15.34</td><td>6.36</td><td>—</td><td>—</td><td>19.74</td><td>3.82</td><td>16.2</td><td>—</td><td>—</td></tr></table>

Table 5.3

Convergence in (per-scenario) gradient evaluations $( \times 1 0 ^ { 6 } )$ at prescribed accuracy levels.

<table><tr><td rowspan="2">Gap</td><td colspan="4"> $\alpha = 0.90$ </td><td colspan="4"> $\alpha = 0.95$ </td><td colspan="4"> $\alpha = 0.98$ </td></tr><tr><td>EASIEST</td><td>r-alg</td><td>Baseline</td><td>PD</td><td>EASIEST</td><td>r-alg</td><td>Baseline</td><td>PD</td><td>EASIEST</td><td>r-alg</td><td>Baseline</td><td>PD</td></tr><tr><td> $10^{-1}$ </td><td>0.39</td><td>0.27</td><td>0.41</td><td>0.18</td><td>0.34</td><td>0.17</td><td>0.18</td><td>0.09</td><td>0.09</td><td>0.03</td><td>0.13</td><td>0.21</td></tr><tr><td> $10^{-2}$ </td><td>0.48</td><td>0.36</td><td>1.08</td><td>0.25</td><td>0.51</td><td>0.31</td><td>0.34</td><td>0.17</td><td>0.17</td><td>0.13</td><td>0.18</td><td>0.31</td></tr><tr><td> $10^{-3}$ </td><td>0.56</td><td>0.61</td><td>2.9</td><td>0.34</td><td>0.64</td><td>0.45</td><td>0.62</td><td>0.34</td><td>0.32</td><td>0.19</td><td>0.35</td><td>0.44</td></tr><tr><td> $10^{-4}$ </td><td>0.74</td><td>0.93</td><td>—</td><td>0.62</td><td>0.85</td><td>0.6</td><td>1.47</td><td>0.59</td><td>0.48</td><td>0.25</td><td>—</td><td>0.69</td></tr><tr><td> $10^{-5}$ </td><td>1.21</td><td>1.32</td><td>—</td><td>1.07</td><td>1.21</td><td>0.79</td><td>—</td><td>0.95</td><td>0.61</td><td>0.3</td><td>—</td><td>—</td></tr><tr><td> $10^{-6}$ </td><td>1.79</td><td>—</td><td>—</td><td>1.63</td><td>1.8</td><td>—</td><td>—</td><td>1.15</td><td>0.65</td><td>0.32</td><td>—</td><td>—</td></tr></table>

Across all three risk levels $\alpha \in \{ 0 . 9 0 , 0 . 9 5 , 0 . 9 8 \}$ , Table 5.1 shows that EASIeST, Shor’s r-algorithm, and PD all substantially outperform the Baseline method in terms of oracle calls. Overall, EASIeST is the most robust method, being the only one that reaches gap $1 0 ^ { - 6 }$ for all three values of α. For $\alpha = 0 . 9 0$ EASIeST is the best performer across all reported gap levels, requiring, for instance, 423 oracle calls to reach gap $1 0 ^ { - 5 }$ and 707 calls to reach gap $1 0 ^ { - 6 }$ , compared with 494 and 767 for PD, respectively. For $\alpha = 0 . 9 5$ PD is particularly competitive: it is the best performer at gaps $1 0 ^ { - 1 }$ and $1 0 ^ { - 2 }$ , requiring only 26 and 68 oracle calls, respectively, compared with 44 and 117 for EASIeST, and it also reaches gap $1 0 ^ { - 6 }$ in 987 calls, improving on the 1290 calls required by EASIeST. At the same time, EASIeST remains slightly better at the intermediate tighter levels $1 0 ^ { - 3 } – 1 0 ^ { - 5 }$ . For the most risk-averse $\mathrm { c a s e } ^ { 3 } ~ \alpha = 0 . 9 8$ , EASIeST clearly outperforms the competing methods across all reported gap levels, reaching gap $1 0 ^ { - 5 }$ in 602 oracle calls and gap $1 0 ^ { - 6 }$ in 684 calls, compared with 762 and 809 for the r-algorithm, while PD does not reach these tighter accuracies within the allotted budget. Taken together, these results indicate that, in terms of oracle calls, all methods (except the baseline) perform at a broadly comparable level, with diferences depending on the regime rather than revealing a uniformly superior method.

Tables 5.2 and 5.3 provide a more detailed view of this comparison in terms of cumulative (per-scenario) function and gradient evaluations (in units of $1 0 ^ { 6 } )$ . In terms of function evaluations, EASIeST is generally the most eficient method, especially at tighter accuracies. For $\alpha = 0 . 9 0$ , it requires fewer function evaluations than both PD and Shor’s r-algorithm at every reported gap level; for example, at gap $1 0 ^ { - 5 }$ the counts are 3.7 for EASIeST, 9.88 for PD, and 13.2 for the r-algorithm, and at gap $1 0 ^ { - 6 }$ they are 4.3 and 15.34 for EASIeST and PD, respectively. A similar pattern is observed for $\alpha = 0 . 9 8$ , where EASIeST substantially improves on the r-algorithm at the tightest reported levels (e.g., 3.77 vs. 15.2 at gap $1 0 ^ { - 5 }$ , and 3.82 vs. 16.2 at gap $1 0 ^ { - 6 } )$ . The main exception occurs for $\alpha = 0 . 9 5$ at coarse tolerances, where PD requires fewer function evaluations than EASIeST at gaps $1 0 ^ { - 1 }$ and $1 0 ^ { - 2 } \ : \ : ( 0 . 5 2 \ : \ : \mathrm { v s . } \ : \ : 0 . 8 .$ , and 1.36 vs. 2.3), although EASIeST becomes more eficient from gap $1 0 ^ { - 3 }$ onward. The lower function-evaluation counts of EASIeST are also partly explained by its block structure. Even in the present experiment, where the full block is used, EASIeST employs block sampling without replacement according to the current dual probability vector $q ^ { k }$ As the algorithm progresses, the probabilities $q _ { i } ^ { k }$ associated with non-tail scenarios become small and, in practice, these scenarios are no longer sampled. Consequently, they stop contributing to the cumulative function-evaluation count, whereas the competing methods continue to evaluate the full sample at each iteration. Therefore, the savings observed in Table 5.2 reflect not only convergence in oracle calls, but also the reduced efective evaluation cost induced by the sampling mechanism.

The gradient-evaluation counts present a more nuanced picture. PD is often quite competitive in this metric and, for $\alpha = 0 . 9 0$ and $\alpha = 0 . 9 5$ , it uses fewer gradient evaluations than EASIeST at many of the reported gap levels; for instance, at $\alpha = 0 . 9 5$ and $\mathrm { g a p ~ 1 0 ^ { - 6 } }$ the counts are 1.15 for PD and 1.8 for EASIeST. On the other hand, for $\alpha \ : = \ : 0 . 9 8$ the r-algorithm is the most economical in gradients, and EASIeST still improves on PD whenever both methods reach the same target level. Thus, the tables suggest a clear distinction between the two performance measures: EASIeST tends to be more eficient in function evaluations and more reliable at tighter accuracies, whereas PD is often competitive in gradient evaluations and can be very efective in oracle calls on some instances.

5.1.2. Stochastic case. This section solves the CVAR-SVM problem (5.1) using Algorithm 3 and the baseline Algorithm 5. Analogously to the previous section, as the optimal CVaR value $f ^ { * } = f ( x ^ { * } )$ , we use the value reported by the PSG solver van with precision 7. Note that, in the stochastic setting, PD does not admit the block-sampling mechanism used by EASIeST. The reason is that the iterates $\pmb q ^ { k }$ no longer remain in the interior of Q (cf. Remark 3.1). Therefore, we exclude PD from the stochastic experiments.

To facilitate a fair comparison, we consider a constant regime, where both Algorithm 3 and the baseline Algorithm 5 are executed with the same fixed stepsize. In both cases, we fix $\alpha = 0 . 9 5$ and define $N _ { \alpha } : =$ $( 1 - \alpha ) n$ . Both algorithms are then run with mini-batch size $\theta N _ { \alpha } .$ , with $\theta \in \{ 0 . 5 , 0 . 6 , 0 . 7 , 0 . 8 , 0 . 9 , 1 \}$ . In this way, the batch size is scaled relative to the efective tail sample size.

The constant stepsize used in the experiments was chosen according to the standard stochastic subgradient scaling (cf. the notation in Theorem 3.1)

$$
\beta = \frac {1}{C} \frac {R}{B \sqrt {T}}, \quad C \in [ 2, 3 ]\tag{5.2}
$$

where R is a problem-dependent distance scale, T is the prescribed iteration budget, and B is a bound on the second moment of the stochastic subgradients. In our implementation, we first computed $R = \| x ^ { 0 } - x ^ { \star } \| _ { 2 }$ and fixed the total number of iterations to $T = 4 4 0 0$ . We then estimated B empirically by means of a pilot run of the baseline algorithm: specifically, we ran the baseline method for 1000 iterations with constant stepsize $\beta = 0 . 1$ and batch size $N _ { \alpha } = ( 1 - \alpha ) n = 1 0 0 0$ , and computed B as the root mean square of the observed stochastic subgradient norms over this run. Substituting the resulting estimate of B into the above expression yielded the constant stepsize used in the reported experiments. The constant $C \in [ 2 , 3 ]$ is a stability factor introduced to make the nominal stepsize suficiently conservative for use with smaller batch sizes.

Parameter settings for Algorithm 3. We set $\gamma _ { 0 } = 1 , \ c _ { \gamma } = 1 . 0 8 , \ \varepsilon _ { g } = 1 0 ^ { - 6 } , \ \varepsilon _ { T V } = 1 0 ^ { - 5 } , \varepsilon _ { q } = 1 0 ^ { - 1 0 } , | \mathcal { B } | =$ 8500, $K = 2 0 , \ J = 2 2 0$ $m = \theta N _ { \alpha }$ $\rho _ { k } ^ { 2 } = 1 0 ^ { - 5 }$ . As the subproblem solver, we use (3.1)–(3.2) with $\beta _ { j } = \beta$ defined in (5.2).

The Figure 5.1 shows that EASIeST consistently achieves a faster decay of the suboptimality gap and attains a lower final objective gap than the baseline method for all tested batch sizes. The gain is especially pronounced for larger batches, indicating that the method is particularly efective at exploiting informative tail samples.

However, this improved convergence behavior is accompanied by a higher computational cost in terms of function and gradient evaluations. Since EASIeST allocates a larger fraction of samples to the tail, each iteration becomes more expensive than in the baseline scheme. Consequently, the improvement observed in oracle-call complexity should be interpreted together with this increased evaluation cost. This tradeof also suggests a natural improvement to the method in future work: adaptive batch-size selection. Such a mechanism could reduce computational efort in the early stages of the algorithm and reserve larger, more accurate batches for later iterations, where precise tail estimation becomes more critical.

The Figure 5.2 indicates that block size |B| significantly afects convergence. While the method converges for block sizes close to n, reducing the block size initially accelerates convergence, with the most favorable behavior occurring around $| B | \approx 0 .$ .4n. In contrast, excessively small blocks lead to noticeably slower convergence. This behavior suggests that block size should not be chosen statically, and motivates the development of adaptive block-size selection rules that could further improve the practical eficiency of the method. This observation also explains our choice of $| B | = 8 5 0 0$ in the experiments reported in Figure 5.1, as this value corresponds to an intermediate block size that provides a favorable trade-of between convergence speed and computational eficiency.

A possible explanation for this behavior is that moderate block sizes provide a better balance between adaptivity and stability in the update of the sampling distribution. When |B| is close to n, the update remains stable but may be overly conservative, since it distributes the correction across many scenarios, including those that are only weakly relevant to the active CVaR tail. In contrast, a moderately smaller block allows the method to adjust the distribution more selectively toward informative tail scenarios, which can accelerate convergence. If the block becomes too small, however, the update becomes excessively local and noisy, resulting in slower overall progress.

![](images/05c6f5e97c6d2202347be506c670397ad03e213eb74a21692283594672e1de38.jpg)  
Fig. 5.1. Comparison of the average suboptimality gap $f _ { j } - f ^ { \star }$ , averaged over 10 independent runs, versus oracle calls for “stochastic” EASIeST and the baseline method under diferent batch sizes, ranging from $0 . 5 N _ { \alpha }$ to $N _ { \alpha } , \ \alpha = 0 . 9 5$

![](images/a4492c4308750c52ed9e38044bbe7fd78c73e340d605e1b6cda31bac3c5a0fd2.jpg)  
Fig. 5.2. Efect of the block size |B| on the convergence of Algorithm 3. The figure reports the suboptimality gap $f _ { j } \ - \ f ^ { * }$ averaged over 10 independent runs, versus oracle calls for for “stochastic” EASIeST with block sizes $| B | \in$ $\left\{ { n , 0 . 9 n , 0 . 8 n , 0 . 7 n , 0 . 6 n , 0 . 5 n , 0 . 4 n , 0 . 3 n , 0 . 2 n , ( 1 - \alpha ) n } \right\}$ . In all experiments, the mini-batch size is fixed at $N _ { \alpha } , ~ \alpha = 0 . 9 5$

5.2. Minimum-CVaR portfolio Optimization. We consider a portfolio of d assets and a finite set of return scenarios $\{ z _ { i } \} _ { i = 1 } ^ { n }$ , where each $z _ { i } \in \mathbb { R } ^ { d }$ represents the vector of asset returns in scenario i. Let

$$
\boldsymbol {x} := \left(x _ {1}, \dots , x _ {d}\right) ^ {\top} \in \mathbb {R} ^ {d}
$$

denote the portfolio allocation vector, where $x _ { j }$ is the proportion of wealth invested in asset $j .$ . We restrict x to the simplex

$$
\mathcal {X} := \left\{\boldsymbol {x} \in \mathbb {R} _ {+} ^ {d}: \mathbf {1} ^ {\top} \boldsymbol {x} = 1 \right\},
$$

so that short selling is excluded and the budget constraint is satisfied.

For each scenario i, we define the portfolio loss

$$
F _ {i} (\boldsymbol {x}) := - \boldsymbol {x} ^ {\top} \boldsymbol {z} _ {i}, \qquad i = 1, \ldots , n,
$$

and write $F ( \pmb { x } , \omega )$ as the random variable taking values $\{ F _ { i } ( { \pmb x } ) \} _ { i = 1 } ^ { n }$ under the baseline distribution ${ \textbf { \em p } } =$ $\left( p _ { 1 } , \ldots , p _ { n } \right)$ (in our experiments we take $p _ { i } = 1 / n )$ . To control downside risk, we minimize the conditional value-at-risk of the portfolio loss. This leads to the minimum-CVaR portfolio optimization problem

$$
\min _ {\boldsymbol {x} \in \mathcal {X}} \left\{f (\boldsymbol {x}) := \operatorname{CVaR} _ {\alpha} \left(F (\boldsymbol {x}, \omega)\right) \right\}.\tag{5.3}
$$

Unlike the classical mean–CVaR model, formulation (5.3) does not impose a lower bound on the expected portfolio return; instead, it seeks a portfolio that minimizes tail risk subject only to the budget and nonneg ativity constraints.

Data. In our numerical experiments, we fix the number of assets at $p$ and generate n return scenarios $z _ { i } \in \mathbb { R } ^ { p } , i = 1 , \dots , n .$ , independently from a multivariate normal distribution

$$
\boldsymbol {z} _ {i} \stackrel {\mathrm{iid}} {\sim} \mathcal {N} (\boldsymbol {\mu}, \Sigma).
$$

The covariance matrix is constructed as

$$
\Sigma = A ^ {\top} A,
$$

where $A \in \mathbb { R } ^ { p \times p }$ is a random matrix with entries sampled independently from the uniform distribution on [0, 1]. The mean vector $\pmb { \mu } \in \mathbb { R } ^ { p }$ is generated componentwise from the uniform distribution on $[ - 0 . 1 , 1 0 ]$ . The resulting sample $\{ z _ { i } \} _ { i = 1 } ^ { n }$ is then used to define the portfolio loss scenarios in (5.3).

5.2.1. Deterministic case. This subsection studies the deterministic minimum-CVaR portfolio opti mization problem. This experiment has two objectives. First, it demonstrates the eficiency of the proposed method in the presence of explicit constraints. Second, it compares EASIeST with a block version of the classical proximal-point variant inspired by [21], obtained by replacing the Bregman divergence $D _ { \psi } ( q , r )$ with ${ \frac { 1 } { 2 } } \| q - r \| _ { 2 } ^ { 2 }$ while imposing the same block-sampling structure used by EASIeST in the full-block regime. We refer to this method as block PD (BPD).

As the previous experiments show, the two methods are broadly comparable in terms of oracle calls. Nevertheless, PD attains this performance only at the cost of full function evaluations. In contrast, EASIeST retains the computational advantage of its block structure even in the full-block case: once the probabilities of certain scenarios fall to the level of machine precision, these scenarios are no longer sampled and thus stop contributing to function evaluations. PD does not possess this property. The experiment below shows that, in such a setting, BPD is not practically viable. Although this conclusion is consistent with the underlying theory, it is also important to illustrate it numerically. As the optimal CVaR value $f ^ { \star } = f ( { \pmb x } ^ { \star } )$ , we use the value reported by the PSG solver van [38] with precision parameter 10.

Parameter settings for Algorithm 2 and BPD. We set $\gamma _ { 0 } = 1 ( \gamma _ { 0 } = 1 0 ^ { - 4 }$ for PD), $c _ { \gamma } = 1 . 0 8 , ~ \varepsilon _ { g } =$ $1 0 ^ { - 6 } , \varepsilon _ { T V } = 1 0 ^ { - 6 } , \varepsilon _ { q } = 1 0 ^ { - 1 0 } , | \mathcal { B } | = n , K = 1 0 0 , J = 5 0 0 , \rho _ { k } = 1 0 ^ { - 4 }$ . As the subproblem solver, we use Algorithm 3 (adaptive proximal gradient method) from [26].

Table 5.4 illustrates a limitation of BPD in the block-sampling setting. This behavior is consistent with the convergence theory developed in Theorems 3.2 and 3.3, where the block-sampling distribution is required to satisfy $\bar { \pi } _ { i } ^ { k } > 0$ for all scenarios i and all iterations k. In the case of EASIeST, this condition is naturally satisfied by taking $\pi _ { i } ^ { k } = q _ { i } ^ { k }$ , since the Bregman update preserves strict positivity of the dual weights. B contrast, in BPD the quadratic-prox update involves an $\ell _ { 2 } { \mathrm { - p r o j e c t i o n } }$ , which does not guarantee positivity; i.e., some weights may be projected exactly to zero. Once a scenario receives zero weight, it is excluded from subsequent sampling, so the method can no longer revisit or correct it. This violates the requirement underlying the convergence theory and explains why BPD cannot be reliably implemented with the same block-sampling mechanism.

Table 5.4  
Performance of BPD and EASIeST on the deterministic minimum-CVaR portfolio optimization problem $f o r \alpha = 0 . 9 9$ with $p = 1 0 0$ assets.

<table><tr><td rowspan="2">n</td><td colspan="2">BPD</td><td colspan="2">EASIEST</td></tr><tr><td>Best Gap</td><td>Total Calls</td><td>Best Gap</td><td>Total Calls</td></tr><tr><td>1000</td><td> $2.38 \times 10^{-3}$ </td><td>659</td><td> $4.82 \times 10^{-9}$ </td><td>1509</td></tr><tr><td>10000</td><td> $1.69 \times 10^{-6}$ </td><td>790</td><td> $4.13 \times 10^{-7}$ </td><td>892</td></tr><tr><td>50000</td><td> $1.68 \times 10^{-2}$ </td><td>47</td><td> $1.44 \times 10^{-9}$ </td><td>563</td></tr><tr><td>100000</td><td> $2.33 \times 10^{-2}$ </td><td>52</td><td> $5.18 \times 10^{-9}$ </td><td>502</td></tr></table>

In contrast, EASIeST remains compatible with the block-sampling framework. Since its weights stay strictly positive, the induced sampling distribution remains well-defined throughout the run and continues to satisfy the assumptions of Theorems 3.2 and 3.3. At the same time, scenarios whose probabilities become negligible up to machine precision efectively cease to contribute to the function-evaluation cost, so EASIeST retains the computational advantages of block sampling without losing convergence. This distinction is clearly reflected in Table 5.4: EASIeST continues to attain high accuracy across all tested values of n, whereas BPD stagnates at relatively large gaps when block sampling is imposed.

6. Conclusion. We presented EASIeST, a new framework for CVaR optimization based on the dual representation of CVaR and a Bregman proximal point scheme on its risk envelope. The proposed approach combines two desirable features within a single algorithmic mechanism: adaptive smoothing of the nonsmooth CVaR objective and adaptive importance sampling that progressively concentrates the sampling distribution on tail scenarios while preserving interior feasibility. This yields a method that is both theoretically grounded and practically tailored to the structure of CVaR problems.

On the theoretical side, we derived the method from a saddle-point formulation of CVaR and showed that the generalized Fermi–Dirac entropy induces a natural geometry for the dual probability updates. This geometry leads to closed-form block Bregman proximal steps, keeps the iterates in the interior of the feasible risk envelope, and provides a built-in tail-learning mechanism. For convex problems, we established convergence guarantees for the inner stochastic subproblem solver, convergence in function values for the outer method, and almost sure convergence of the dual iterates under exact subproblem solutions.

Our numerical experiments demonstrate that the proposed framework is efective across representative applications in machine learning and quantitative finance. In the deterministic support-vector classification benchmark, EASIeST consistently outperformed the baseline method and was broadly competitive with Shor’s r-algorithm in oracle calls, while requiring substantially fewer function evaluations at tighter accuracies. In the stochastic setting, EASIeST exhibited faster decay of the suboptimality gap than the baseline across all tested batch sizes, with especially strong performance for larger batches. At the same time, the experiments highlight an important tradeof: the improved tail-focused sampling may increase per-iteration function and gradient costs, reflecting the price of the smoothing and importance-sampling mechanism.

These observations point to several promising directions for future work. In particular, the stochastic experiments suggest that adaptive batch-size and block-size selection rules could further improve practical eficiency by balancing early-stage exploration with later-stage tail refinement; cf. [3].

Appendix A. Proof of Theorem 2.2.

Proof. We split the proof into two steps.

Step 1. Since $D _ { \psi } ( q ^ { k + 1 } , q ^ { k } ) \geq 0$ , we have

$$
\varphi (\boldsymbol {q} ^ {k + 1}) \leq \varphi (\boldsymbol {q} ^ {k + 1}) + \frac {1}{\gamma_ {k}} D _ {\psi} (\boldsymbol {q} ^ {k + 1}, \boldsymbol {q} ^ {k}).
$$

By optimality of $\pmb q ^ { k + 1 } = \mathrm { p r o x } _ { \gamma _ { k } \varphi } ( \pmb q ^ { k } )$ in (2.5),

$$
\varphi (\boldsymbol {q} ^ {k + 1}) + \frac {1}{\gamma_ {k}} D _ {\psi} (\boldsymbol {q} ^ {k + 1}, \boldsymbol {q} ^ {k}) \leq \varphi (\boldsymbol {q} ^ {k}) + \frac {1}{\gamma_ {k}} D _ {\psi} (\boldsymbol {q} ^ {k}, \boldsymbol {q} ^ {k}) = \varphi (\boldsymbol {q} ^ {k}),
$$

hence $\varphi ( \pmb q ^ { k + 1 } ) \leq \varphi ( \pmb q ^ { k } )$

Step 2. Using the three-point identity [8],

$$
D _ {\psi} (\boldsymbol {s}, \boldsymbol {q}) + D _ {\psi} (\boldsymbol {q}, \boldsymbol {r}) = D _ {\psi} (\boldsymbol {s}, \boldsymbol {r}) + \left\langle \nabla \psi (\boldsymbol {r}) - \nabla \psi (\boldsymbol {q}), \boldsymbol {s} - \boldsymbol {q} \right\rangle ,
$$

and the first-order optimality condition for (2.5),

$$
\left\langle \gamma g _ {\varphi} (\boldsymbol {q}) + \nabla \psi (\boldsymbol {q}) - \nabla \psi (\boldsymbol {r}), \boldsymbol {s} - \boldsymbol {q} \right\rangle \geq 0 \quad \text { for   all } \boldsymbol {s} \in \mathcal {Q},
$$

for some $g _ { \varphi } ( \pmb q ) \in \partial \varphi ( \pmb q )$ , we set $\gamma = \gamma _ { k } , \pmb q = \pmb q ^ { k + 1 } , r = \pmb q ^ { k } , s = \pmb q ^ { \star }$ to obtain

$$
D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k + 1}) + D _ {\psi} (\boldsymbol {q} ^ {k + 1}, \boldsymbol {q} ^ {k}) \leq D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k}) + \gamma_ {k} \langle g _ {\varphi} (\boldsymbol {q} ^ {k + 1}), \boldsymbol {q} ^ {\star} - \boldsymbol {q} ^ {k + 1} \rangle .
$$

By convexity of $\varphi , \langle g _ { \varphi } ( \pmb { q } ^ { k + 1 } ) , \pmb { q } ^ { \star } - \pmb { q } ^ { k + 1 } \rangle \leq \varphi ( \pmb { q } ^ { \star } ) - \varphi ( \pmb { q } ^ { k + 1 } )$ . Dropping the term $D _ { \psi } ( q ^ { k + 1 } , q ^ { k } ) \geq 0$ gives

$$
D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k + 1}) - D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {k}) \leq \gamma_ {k} \bigl (\varphi (\boldsymbol {q} ^ {\star}) - \varphi (\boldsymbol {q} ^ {k + 1}) \bigr).
$$

Summing from $k = 0$ to $N - 1$ and using Step 1 (non-increasing $\varphi ( \pmb q ^ { k } ) )$ yields

$$
D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {N}) - D _ {\psi} (\boldsymbol {q} ^ {\star}, \boldsymbol {q} ^ {0}) \leq \left(\varphi (\boldsymbol {q} ^ {\star}) - \varphi (\boldsymbol {q} ^ {N})\right) \sum_ {k = 0} ^ {N - 1} \gamma_ {k}.
$$

Rearranging and using $D _ { \psi } ( \pmb q ^ { \star } , \pmb q ^ { N } ) \geq 0$ proves (2.6).

Appendix B. Baseline algorithms and CVaR subgradient constructions. For completeness, we collect here the baseline methods used in the numerical experiments together with the corresponding CVaR subgradient constructions.

B.1. Deterministic baseline. For a given $\mathbf { \boldsymbol { x } } \in \mathcal { X }$ , let $t ^ { \star } ( { \pmb x } ) = \mathsf { V a R } _ { \alpha } ( F ( { \pmb x } , \omega ) )$ and recall that $F ( \pmb { x } , \omega )$ is represented by the n-dimensional vector $( F _ { 1 } ( { \pmb x } ) , \dots , F _ { n } ( { \pmb x } ) )$ . Define

$$
I _ {\diamond} (\boldsymbol {x}) := \left\{i: F _ {i} (\boldsymbol {x}) \diamond t ^ {\star} (\boldsymbol {x}) \right\}, \quad \diamond \in \{>, <  , = \}
$$

and

$$
q _ {i} (\boldsymbol {x}) = \left\{ \begin{array}{l l} \frac {p _ {i}}{1 - \alpha}, & i \in I _ {>} (\boldsymbol {x}), \\ \frac {\theta_ {i} p _ {i}}{1 - \alpha}, & i \in I _ {=} (\boldsymbol {x}), \\ 0, & i \in I _ {<  } (\boldsymbol {x}), \end{array} \right. \quad \text { so   that } \quad \sum_ {i = 1} ^ {n} q _ {i} (\boldsymbol {x}) = 1.
$$

Then

$$
\partial_ {\boldsymbol {x}} \mathrm{CVaR} _ {\alpha} (F (\boldsymbol {x}, \omega)) := \left\{g (\boldsymbol {x}) = \sum_ {i = 1} ^ {n} q _ {i} (\boldsymbol {x}) g _ {F _ {i} (\boldsymbol {x})} \text {   for   all   feasible   choices   of   } 0 \leq \theta_ {i} \leq 1 \right\},\tag{B.1}
$$

where $g _ { F _ { i } ( \pmb { x } ) } \in \partial F _ { i } ( \pmb { x } )$

B.2. Stochastic baseline. Let $\xi _ { 1 } , \ldots , \xi _ { m } \stackrel { \mathrm { i i d } } { \sim } p$ be scenario indices (sampled with replacement) and define

$$
F ^ {(m)} (\boldsymbol {x}) := \left(F _ {\xi_ {1}} (\boldsymbol {x}), \dots , F _ {\xi_ {m}} (\boldsymbol {x})\right) ^ {\top}.
$$

Define the empirical α-quantile

$$
t _ {m} ^ {\star} (\boldsymbol {x}) \in \arg \min _ {t \in \mathbb {R}} \left\{t + \frac {1}{(1 - \alpha) m} \sum_ {j = 1} ^ {m} \left(F _ {\xi_ {j}} (\boldsymbol {x}) - t\right) _ {+} \right\},
$$

equivalently, $t _ { m } ^ { \star } ( x )$ is an α-quantile of $\{ F _ { \xi _ { j } } ( \pmb { x } ) \} _ { j = 1 } ^ { m }$ . Define the batch index sets

$$
J _ {\diamond} (\boldsymbol {x}) := \left\{j \in \{1, \dots , m \}: F _ {\xi_ {j}} (\boldsymbol {x}) \diamond t _ {m} ^ {\star} (\boldsymbol {x}) \right\}, \quad \diamond \in \{>, <  , = \}.
$$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 4: The deterministic baseline.

Input : $x^0, x^{-1} \in \mathcal{X}$, $u &gt; 1$, $d \in (0,1)$, $\beta_0, \varepsilon &gt; 0$, $K \in \mathbb{N}$.

Output: an approximate solution $x^\star \in \mathcal{X}$.

for $k = 0, 1, 2, \ldots, K$ do

Step 1. Compute $g(x^k) \in \partial_x \text{CVaR}_\alpha(F(x^k, \omega))$; (cf. (B.1))

Step 2. Compute $Q_k = \beta_k \| g(x^k) \|_2$;

if $Q_k \leq \varepsilon$ then // termination
    break

Step 3. Compute $T_k = \langle g(x^k), x^{k-1} - x^k \rangle$;

Step 4. Adjust the stepsize

$\beta_{k+1} = \begin{cases} u\beta_k, &amp; \text{if } T_k &gt; 0, \\ d\beta_k, &amp; \text{if } T_k \leq 0. \end{cases}$

Step 5. Find the next approximation

$x^{k+1} = \text{proj}_\mathcal{X}\left[x^k - \beta_k g(x^k)\right]$.

return $x^\star \leftarrow x^k$, CVaR$_\alpha(F(x^\star, \omega))$
</div>

Set the batch weights

$$
\hat {q} _ {j} (\boldsymbol {x}) = \left\{ \begin{array}{l l} \frac {1}{(1 - \alpha) m}, & j \in J _ {>} (\boldsymbol {x}), \\ \frac {\theta_ {j}}{(1 - \alpha) m}, & j \in J _ {=} (\boldsymbol {x}), \\ 0, & j \in J _ {<  } (\boldsymbol {x}), \end{array} \right. \quad \text {so that} \quad \sum_ {j = 1} ^ {m} \hat {q} _ {j} (\boldsymbol {x}) = 1.
$$

Compute subgradients $g ( \pmb { x } ; \xi _ { j } ) \in \partial F _ { \xi _ { j } } ( \pmb { x } )$ . Then, a mini-batch stochastic CVaR subgradient is

$$
g (\boldsymbol {x}; \xi) \in \partial_ {\boldsymbol {x}} \mathsf {C V a R} _ {\alpha} ^ {(m)} \big (F (\boldsymbol {x}, \omega) \big), \qquad g (\boldsymbol {x}, \xi) = \sum_ {j = 1} ^ {m} \hat {q} _ {j} (\boldsymbol {x})   g (\boldsymbol {x}; \xi_ {j}),\tag{B.2}
$$

for any feasible choice of the weights $\{ \theta _ { j } \} _ { j \in J = ( \pmb { x } ) }$

Appendix C. Subroutines. The following subroutine Algorithm 6 is used in both the stochastic and deterministic versions of the algorithm.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 5: The stochastic baseline.

Input : $x^0, x^{-1} \in \mathcal{X}$, $u &gt; 1$, $d, D \in (0,1)$, $\beta_0, \varepsilon &gt; 0$, $K \in \mathbb{N}$, $A_0 = z_0 = 0$.

Output: an approximate solution $x^\star \in \mathcal{X}$.

for $k = 0, 1, 2, \ldots, K$ do

Step 1. Sample indices $\xi_1, \ldots, \xi_m \stackrel{\text{iid}}{\sim} p$;

Step 2. Compute $g(\boldsymbol{x}^k; \xi) = \sum_{j=1}^{m} \hat{q}_j(\boldsymbol{x}^k) g(\boldsymbol{x}^k; \xi_j)$; (cf. (B.2))

Step 3. Average the norm: $A_{k+1} = A_k + (\|g(\boldsymbol{x}^k; \xi)\|_2 - A_k)D$ and set $Q_k = \beta_k A_{k+1}$;

if $Q_k \leq \varepsilon$ then // termination
└ break

Step 4. Compute $T_k = \langle g(\boldsymbol{x}^k; \xi), \boldsymbol{x}^{k-1} - \boldsymbol{x}^k \rangle$;

Step 5. Average the inner product: $z_{k+1} = z_k + (T_k - z_k)D$;

Step 6. Adjust the stepsize

$\beta_{k+1} = \begin{cases} u\beta_k, &amp; \text{if } z_{k+1} &gt; 0, \\ d\beta_k, &amp; \text{if } z_{k+1} \leq 0. \end{cases}$

Step 7. Find the next approximation

$x^{k+1} = \text{proj}_{\mathcal{X}}[x^k - \beta_k g(x^k; \xi)]$.

return $x^\star \leftarrow x^k$, CVaR$_{\alpha}(F(x^\star, \omega))$
</div>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 6: PROXUPDATE

Input : $\boldsymbol{x}^{k,j} \in \mathcal{X}$, reference $\boldsymbol{s}^k \in \mathbb{R}^n$ and $\boldsymbol{q}^k \in \mathcal{Q}$, block $\mathcal{B}_k \subseteq \{1, \ldots, n\}$, stepsize $\gamma_k &gt; 0$, block mass $\delta_k = \sum_{i \in \mathcal{B}_k} q_i^k$.

Define : Sigmoid map: $\sigma_i(s) := \frac{p_i}{1 - \alpha} \frac{e^s}{1 + e^s}$.

Output: Updated logits $s^{k,j+1}$ and weights $q^{k,j+1}$.

Evaluate $\{F_i(\boldsymbol{x}^{k,j})\}_{i \in \mathcal{B}_k}$

Set

$\tilde{s}_i^{k,j+1} = \begin{cases} s_i^k + \gamma_k F_i(\boldsymbol{x}^{k,j}), &amp; i \in \mathcal{B}_k, \\ s_i^k, &amp; i \notin \mathcal{B}_k. \end{cases}$

Find $t \in \mathbb{R}$ such that

$\sum_{i \in \mathcal{B}_k} \sigma_i(\tilde{s}_i^{k,j+1} + t) = \delta_k.$

Set

$s_i^{k,j+1} = \begin{cases} \tilde{s}_i^{k,j+1} + t, &amp; i \in \mathcal{B}_k, \\ s_i^k, &amp; i \notin \mathcal{B}_k, \end{cases} \quad q_i^{k,j+1} = \begin{cases} \sigma_i(s_i^{k,j+1}), &amp; i \in \mathcal{B}_k, \\ q_i^k, &amp; i \notin \mathcal{B}_k. \end{cases}$

return $(\boldsymbol{s}^{k,j+1}, \boldsymbol{q}^{k,j+1})$
</div>

## REFERENCES

[1] P. Artzner, F. Delbaen, J-M. Eber, and D. Heath. Coherent Measures of Risk. Mathematical Finance, 9(3):203–228, 1999.

[2] Olivier Bardou, Noufel Frikha, and Gilles Pag‘es. Computing VaR and CVaR using stochastic approximation and adaptive unconstrained importance sampling. Monte Carlo Methods and Applications, 15(3):173–210, 2009.

[3] Florian Beiser, Brendan Keith, Simon Urbainczyk, and Barbara Wohlmuth. Adaptive sampling strategies for risk-averse stochastic optimization with constraints. IMA Journal of Numerical Analysis, 43(6):3729–3765, 2023.

[4] Dimitri P. Bertsekas. Nonlinear Programming. Athena Scientific, Belmont, MA, 2 edition, 1999.

[5] L. M. Bregman. The Relaxation Method of Finding the Common Point of Convex Sets and Its Application to the Solution of Problems in Convex Programming. USSR Computational Mathematics and Mathematical Physics, 7(3):200–217, 1967.

[6] D. Cajas. Riskfolio-Lib (6.2.0), 2024.

[7] Bo Chen, Shaohua He, Zhiping Li, and Shuzhong Zhang. Maximum Block Improvement and Polynomial Optimization. SIAM Journal on Optimization, 22(1):87–107, 2012.

[8] G. Chen and M. Teboulle. Convergence Analysis of a Proximal-Like Minimization Algorithm Using Bregman Functions. SIAM Journal on Optimization, 3(3):538–543, 1993.

[9] I. Csisz´ar. Why Least Squares and Maximum Entropy? An Axiomatic Approach to Inference for Linear Inverse Problems. Annals of Statistics, 19(4):2032–2066, 1991.

[10] I. Csisz´ar. Maximum Entropy and Related Methods. In Trans. 12th Prague Conf. Information Theory, Statistical Decision Functions and Random Processes, pages 58–62, Prague, Czech Acad. Sci., 1994.

[11] I. Csisz´ar. Generalized Projections for Non-Negative Functions. Acta Mathematica Hungarica, 68:161–186, 1995.

[12] I. Csisz´ar and F. Mat´uˇs. On Minimization of Entropy Functionals under Moment Constraints. In Proceedings of ISIT 2008, pages 2101–2105, Toronto, Canada, 2008.

[13] I. Csisz´ar and F. Mat´uˇs. On Minimization of Multivariate Entropy Functionals. In Proceedings of ITW 2009, pages 96–100, Volos, Greece, 2009.

[14] John M. Danskin. The Theory of Max-Min and Its Application to Weapons Allocation Problems, volume 5 of Econometrics and Operations Research. Springer, Berlin, Heidelberg, 1967.

[15] Anand Deo and Karthyek Murthy. Eficient black-box importance sampling for VaR and CVaR estimation. In Proceedings of the 2021 Winter Simulation Conference (WSC), pages 1–12. IEEE, 2021.

[16] Jonathan Eckstein. Approximate Iterations in Bregman-Function-Based Proximal Algorithms. Mathematical programming, 83(1):113–123, 1998.

[17] B. Grechuk, A. Malandii, R. T. Rockafellar, and S. Uryasev. The Risk Quadrangle in Optimization: An Overview with Recent Results and Extensions. EURO Journal on Computational Optimization, 14:100129, 2026.

[18] Shengyi He, Guangxin Jiang, Henry Lam, and Michael C. Fu. Adaptive importance sampling for eficient stochastic root finding and quantile estimation. Operations Research, 72(6):2612–2630, 2024.

[19] Anoop Kodakkal, Brendan Keith, Ustim Khristenko, Andreas Apostolatos, Kai-Uwe Bletzinger, Barbara Wohlmuth, and Roland W¨uchner. Risk-averse design of tall buildings for uncertain wind conditions. Computer Methods in Applied Mechanics and Engineering, 402:115371, 2022.

[20] D. P. Kouri and T. M. Surowiec. Epi-Regularization of Risk Measures. Mathematics of Operations Research, 45(2):774– 795, 2020.

[21] D. P. Kouri and T. M. Surowiec. A Primal–Dual Algorithm for Risk Minimization. Mathematical Programming, 193:337– 363, 2022.

[22] Emanuel Laude. All Roads Lead to Rome: Path-Following Augmented Lagrangian Methods via Bregman Proximal Regularization. arXiv preprint arXiv.2602.15710, 2026.

[23] Dennis Leventhal and Adrian S. Lewis. Randomized Methods for Linear Constraints: Convergence Rates and Conditioning Mathematics of Operations Research, 35(3):641–654, 2010.

[24] Zhi-Quan Luo and Paul Tseng. On the Convergence of the Coordinate Descent Method for Convex Diferentiable Mini mization. Journal of Optimization Theory and Applications, 72(1):7–35, 1992.

[25] Yura Malitsky and Konstantin Mishchenko. Adaptive Gradient Descent Without Descent. arXiv preprint arXiv:1910.09529, 2019.

[26] Yura Malitsky and Konstantin Mishchenko. Adaptive Proximal Gradient Method for Convex Optimization. Advances in Neural Information Processing Systems, 37:100670–100697, 2024.

[27] B. Martinet. R´egularisation d'in´equations variationnelles par approximations successives. Revue Fran¸caise d’Informatique et de Recherche Op´erationnelle. S´erie Rouge, 4(R–3):154–158, 1970.

[28] MathWorks Quant Team. CVaR Portfolio Optimization. MATLAB Central File Exchange, 2024. Retrieved July 12, 2024.

[29] F. Mirzoakhmedov and S. P. Uryasev. Adaptive Step Adjustment for a Stochastic Optimization Algorithm. USSR Computational Mathematics and Mathematical Physics, 23(6):20–27, 1983.

[30] J.-J. Moreau. Proximit´e et dualit´e dans un espace hilbertien. Bulletin de la Soci´et´e Math´ematique de France, 93:273–299, 1965.

[31] A. Nemirovski and D. Yudin. Problem Complexity and Method Eficiency in Optimization. Wiley, New York, 1983.

[32] Yurii Nesterov. Eficiency of Coordinate Descent Methods on Huge-Scale Optimization Problems. SIAM Journal on Optimization, 22(2):341–362, 2012.

[33] Yurii Nesterov. Lectures on Convex Optimization, volume 137. Springer, 2018.

[34] Adrian Patrascu and Ion Necoara. Eficient Random Coordinate Descent Algorithms for Large-Scale Structured Nonconvex Optimization. Journal of Global Optimization, 61(1):19–46, 2015.

[35] E. Pauwels. On the Nature of Bregman Functions. Operations Research Letters, 57:107183, 2024.

[36] Sandra Pieraccini and Tommaso Vanzan. An adaptive importance sampling algorithm for risk-averse optimization. Journal of Computational Physics, 547:114548, 2026.

[37] Mark S. Pinsker. Information and Information Stability of Random Variables and Processes. Holden-Day, San Francisco, 1964. Translated and edited by Amiel Feinstein.

[38] Portfolio Safeguard. Portfolio Safeguard Help Manual, 2026. (accessed: 2026-3-4).

[39] L. A. Prashanth. Policy gradients for CVaR-constrained MDPs. In Algorithmic Learning Theory, volume 8776 of Lecture

Notes in Computer Science, pages 155–169, Cham, 2014. Springer.

[40] Peter Richt´arik and Martin Tak´aˇc. Iteration Complexity of Randomized Block-Coordinate Descent Methods for Minimizing a Composite Function. Mathematical Programming, 144(1–2):1–38, 2014.

[41] Peter Richt´arik and Martin Tak´aˇc. On Optimal Probabilities in Stochastic Coordinate Descent Methods. Optimization Letters, 10(6):1233–1243, 2016.

[42] H. Robbins and S. Monro. A Stochastic Approximation Method. Annals of Mathematical Statistics, 22(3):400–407, September 1951.

[43] Herbert Robbins and David Siegmund. A Convergence Theorem for Nonnegative Almost Supermartingales and Some Applications. In T. L. Lai and D. Siegmund, editors, Herbert Robbins Selected Papers, pages 111–135. Springer, 1985.

[44] R. T. Rockafellar. Monotone Operators and the Proximal Point Algorithm. SIAM Journal on Control and Optimization 14(5):877–898, 1976.

[45] R. T. Rockafellar and J. O. Royset. Engineering Decisions under Risk Averseness. ASCE-ASME Journal of Risk and Uncertainty in Engineering Systems, Part A: Civil Engineering, 1(2):04015003, 2015.

[46] R. T. Rockafellar and S. Uryasev. Optimization of Conditional Value-at-Risk. Journal of Risk, 2:21–42, 2000.

[47] R. T. Rockafellar and S. Uryasev. The Fundamental Risk Quadrangle in Risk Management, Optimization and Statistical Estimation. Surveys in Operations Research and Management Science, 18(1-2):33–53, oct 2013.

[48] R. T. Rockafellar, S. Uryasev, and M. Zabarankin. Generalized Deviations in Risk Analysis. Finance and Stochastics, 10(1):51–74, 2006.

[49] R Tyrrell Rockafellar. Augmented Lagrangians and Applications of the Proximal Point Algorithm in Convex Programming. Mathematics of operations research, 1(2):97–116, 1976.

[50] J. O. Royset. Risk-Adaptive Approaches to Stochastic Optimization: A Survey. SIAM Review, 67(1):3–70, 2025.

[51] J. O. Royset and R. J-B. Wets. An Optimization Primer. Springer, 2021.

[52] E. K. Ryu and W. Yin. Large-Scale Convex Optimization: Algorithms & Analyses via Monotone Operators. Cambridge University Press, 2022.

[53] Shai Shalev-Shwartz and Ambuj Tewari. Stochastic Methods for ℓ<sub>1</sub> Regularized Loss Minimization. In Proceedings of the 26th Annual International Conference on Machine Learning (ICML), pages 929–936, Montreal, Quebec, Canada, 2009. ACM.

[54] Shai Shalev-Shwartz and Ambuj Tewari. Stochastic Methods for ℓ<sub>1</sub> Regularized Loss Minimization. Journal of Machine Learning Research, 12(52):1865–1892, 2011.

[55] Naum Z. Shor. Nondiferentiable Optimization and Polynomial Problems, volume 24 of Nonconvex Optimization and Its Applications. Springer, New York, NY, 1 edition, 1998.

[56] Mikhail V Solodov and Benar Fux Svaiter. An Inexact Hybrid Generalized Proximal Point Algorithm and Some New Results on the Theory of Bregman Functions. Mathematics of Operations Research, 25(2):214–230, 2000.

[57] P. I. Stetsyuk. Theory and Software Implementations of Shor’s r-Algorithms. Cybernetics and Systems Analysis, 53(5):692– 703, 2017.

[58] Akiko Takeda and Masashi Sugiyama. ν-Support Vector Machine as Conditional Value-at-Risk Minimization. In Proceedings of the 25th International Conference on Machine Learning, ICML ’08, page 1056–1063, New York, NY, USA, 2008. Association for Computing Machinery.

[59] Aviv Tamar, Yonatan Glassner, and Shie Mannor. Optimizing the CVaR via sampling. In Proceedings of the Twenty-Ninth AAAI Conference on Artificial Intelligence, pages 2993–2999. AAAI Press, 2015.

[60] M. Teboulle. A Simplified View of First-Order Methods for Optimization. Mathematical Programming, 170(1):67–96, 2018.

[61] Paul Tseng. Dual Ascent Methods for Problems with Strictly Convex Costs and Linear Constraints: A Unified Approach. SIAM Journal on Control and Optimization, 28(1):214–242, 1990.

[62] Alexandre B. Tsybakov. Introduction to Nonparametric Estimation. Springer Series in Statistics. Springer, New York, 2009.

[63] Tong Zhang. Solving Large-Scale Linear Prediction Problems Using Stochastic Gradient Descent Algorithms. In Proceedings of the 21st International Conference on Machine Learning (ICML). ACM, 2004.

[64] Yuchen Zhang and Lin Xiao. Stochastic Primal–Dual Coordinate Method for Regularized Empirical Risk Minimization. In Proceedings of the 32nd International Conference on Machine Learning (ICML), pages 353–361. JMLR Workshop and Conference Proceedings, 2015.