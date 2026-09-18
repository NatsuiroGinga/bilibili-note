---
title: "2021-Duchi-Namkoong-Uniform-Performance-DRO"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2021-Duchi-Namkoong-Uniform-Performance-DRO.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Learning Models with Uniform Performance via Distributionally Robust Optimization

John C. Duchi<sup>1</sup>

Hongseok Namkoong<sup>2</sup>

Departments of Statistics and Electrical Engineering, Stanford University<sup>1</sup>

Decision, Risk, and Operations Division, Columbia Business School<sup>2</sup>

jduchi@stanford.edu, hn2369@columbia.edu

## Abstract

A common goal in statistics and machine learning is to learn models that can perform well against distributional shifts, such as latent heterogeneous subpopulations, unknown covariate shifts, or unmodeled temporal efects. We develop and analyze a distributionally robust stochastic optimization (DRO) framework that learns a model providing good performance against perturbations to the data-generating distribution. We give a convex formulation for the problem, providing several convergence guarantees. We prove finite-sample minimax upper and lower bounds, showing that distributional robustness sometimes comes at a cost in convergence rates. We give limit theorems for the learned parameters, where we fully specify the limiting distribution so that confidence intervals can be computed. On real tasks including generalizing to unknown subpopulations, fine-grained recognition, and providing good tail performance, the distributionally robust approach often exhibits improved performance.

## 1 Introduction

In many applications of statistics and machine learning, we wish to learn models that achieve uni formly good performance over almost all input values. This is important for safety- and fairnesscritical systems such as medical diagnosis, autonomous vehicles, criminal justice and credit evaluations, where poor performance on the tails of the inputs leads to high-cost system failures. Methods that optimize average performance, however, often produce models that sufer low performance on the “hard” instances of the population. For example, standard regressors obtained from maximum likelihood estimation can lose predictive power on certain regions of covariates [70], and high average performance comes at the expense of low performance on minority subpopulations. In this work, we study a procedure that explicitly optimizes performance on tail inputs that sufer high loss.

Modern datasets incorporate heterogeneous (but often latent) subpopulations, and a natural goal is to perform well across all of these [70, 80, 25]. While many statistical models show strong average performance, their performance often deteriorates on minority groups underrepresented in the dataset. For example, speech recognition systems are inaccurate for people with minority accents [6]. In numerous other applications—such as facial recognition, automatic video captioning, language identification, academic recommender systems—performance varies significantly over diferent demographic groupings, such as race, gender, or age [48, 52, 22, 83, 96].

In addition to latent heterogeneity in the population, distributional shifts in covariates [89, 12] or unobserved confounding variables (e.g. unmodeled temporal efects [49]) can contribute to changes in the data generating distribution. Performance of machine learning models degrades significantly on domains that are diferent from what the model was trained on [49, 21, 31, 82, 97] and even when new test data are constructed following identical data construction procedures [76]. Domain adaptation [89, 12, 13] and multi-task learning methods [28] can be efective in situations where (potentially unlabeled) data points from the target domain are available. The reliance on a priori fixed target domains, however, is restrictive, as the shifted target distributions are usually unknown before test time and it is impossible to collect data from the targets.

To mitigate these challenges, we consider unknown distributional shifts, developing and analyzing a loss minimization framework that is explicitly robust to local changes in the data-generating distribution. Concretely, let $\Theta \subseteq \mathbb { R } ^ { d }$ be the parameter (model) space, $P _ { 0 }$ be the data generating distribution on the measure space $( \mathcal { X } , \mathcal { A } )$ , X be a random element of $\mathcal { X }$ , and $\ell : \Theta \times \mathcal { X } $ R be a loss function. Rather than minimizing the average loss $\mathbb { E } _ { P _ { 0 } } [ \ell ( \theta ; X ) ]$ , we study the distributionally robust problem

$$
\underset {\theta \in \Theta} {\text { minimize }} \left\{\mathcal {R} _ {f} (\theta ; P _ {0}) := \sup _ {Q \ll P _ {0}} \left\{\mathbb {E} _ {Q} [ \ell (\theta ; X) ]: D _ {f} (Q \| P _ {0}) \leq \rho \right\} \right\},\tag{1}
$$

where the hyperparameter $\rho > 0$ modulates the distributional shift. Here

$$
D _ {f} \left(Q \| P _ {0}\right) := \int f \left(\frac {d Q}{d P _ {0}}\right) d P _ {0}
$$

is the f-divergence [5, 30] between $Q$ and $P _ { 0 }$ , where $f : \mathbb { R } \to \overline { { \mathbb { R } } } _ { + } = \mathbb { R } _ { + } \cup \{ \infty \}$ is a convex function satisfying $f ( 1 ) = 0$ and $f ( t ) = + \infty$ for any $t < 0$

The worst-case risk (1) upweights regions of X with high losses $\ell ( \theta ; X )$ , and thus formulation (1) optimizes performance on the tails, as measured by the loss on “hard” examples. In our motivating scenarios of distribution shift or latent subpopulations, as long as the alternative distribution Q remains ρ-close to the data-generating distribution $P _ { 0 } .$ , the model $\theta ^ { \star } \in \Theta$ that minimizes the worstcase formulation (1) evidently guarantees that $\mathbb { E } _ { Q } [ \ell ( \theta ^ { \star } ; X ) ] \le \mathcal { R } _ { f } ( \theta ^ { \star } ; P _ { 0 } )$ and provides the smallest such bound; as we show shortly, this is equivalent to controlling the tail-performance under $P _ { 0 }$ . In our subsequent discussion, we refer to this behavior as uniform performance. Letting ${ \widehat { P } } _ { n }$ denote the empirical measure on $X _ { i } \stackrel { \mathrm { \scriptsize ~ i i d } } { \sim } P _ { 0 }$ , our approach to minimizing objective (1) is via the plug-in estimator

$$
\widehat {\theta} _ {n} \in \underset {\theta \in \Theta} {\operatorname{argmin}} \left\{\mathcal {R} _ {f} (\theta ; \widehat {P} _ {n}) := \sup _ {Q \ll \widehat {P} _ {n}} \left\{\mathbb {E} _ {Q} [ \ell (\theta ; X) ]: D _ {f} (Q \| \widehat {P} _ {n}) \leq \rho \right\} \right\}.\tag{2}
$$

To build intuition for the worst-case formulation (1), we begin our discussion (in Section 2) by showing that protection against distributional shifts is equivalent to controlling the tail-performance of a model. The modeler’s choice of $f$ determines the tail performance she wants to control, and this dual interpretation provides intuition for the appropriate choice of $f$ and $\rho .$ To concretely understand the types of distributional shifts the worst-case formulation (1) protects against, we provide (in Section 2.1) explicit calculations suggesting appropriate choices of f in some situations. Given nontrivial modeling freedom in choosing f and $\rho ,$ we begin our study in Section 3 with experiments that substantiate our intuitive explanations. Our experimental and theoretical work demonstrates that the distributionally robust estimator $\widehat { \theta } _ { n }$ trades performance on the tails of the data-generating distribution with average-case performance—which empirical risk minimization op timizes. Empirically, we observe in a number of scenarios that such gains in tail-performance (e.g. hard inputs) come at moderate degradation to the average-case performance, so that the robust estimator (2) achieves fairly low loss uniformly across the input space X. For non worst-case distribution shifts, the worst-case formulation (1) prima-facie does not guarantee better performance than empirical risk minimization; the duality between it and tail losses to come suggests that for light-tailed data, distributional robustness comes at little cost to typical-case performance. While work in finance and operations research [17] highlights the benefits of robustness, it is important to investigate the typical shifts one might expect in statistical learning scenarios. To this end, we see in our experiments that the robust estimator (2) sacrifices some average-case performance (which empirical risk minimization optimizes) for lower losses on dificult subpopulations, covariate shift, and other latent confounding.

Although we view a general theoretical characterization of the “right” choice of f and $\rho$ as an important open question, we provide two heuristics for this choice and evaluate their performance on simulation experiments in Section 3. First, as a general approach, we advocate splitting training data non-exchangeably into multiple validation sets, then using these to validate choices f and $\rho ;$ we will expand on this later in the paper with concrete examples and experiments. As brief examples, we may group data by its loss or, in supervised learning scenarios with outcome/label $Y .$ , by values of $Y ;$ when an auxiliary dataset on worse-than-average subpopulations is available, we could use this. The intuition is to use variability within the available data as a proxy for potential departures from the data-generating distribution.

Motivated by our empirical findings in Section 3, the main theoretical component of this work is to study finite sample and asymptotic properties of the plug-in estimator (2). We first provide an eficiently minimizable (finite-dimensional) dual formulation which also forms the basis of our above tail-performance interpretation of distributional robustness (Section 2). We give convergence guarantees for the plug-in estimator (2) (Section 4), and prove that it is rate optimal (Section 5), thereby providing finite-sample minimax bounds on the optimization problem (1). Because the formulation (1) protects against gross departures from the average loss, we observe a degradation in minimax convergence rates that is efectively a consequence of needing to estimate high moments of random variables. More quantitatively, our convergence guarantees show that for f-divergences with $f ( t ) \asymp t ^ { k }$ as $t \to \infty$ , where $k \in ( 1 , \infty )$ , the empirical minimizer $\widehat { \theta } _ { n }$ satisfies

$$
\mathcal {R} _ {f} (\widehat {\theta} _ {n}; P _ {0}) - \inf _ {\theta \in \Theta} \mathcal {R} _ {f} (\theta ; P _ {0}) = O _ {P} \left(n ^ {- \frac {1}{k _ {*} \vee 2}} \log n\right),
$$

where $\begin{array} { r } { k _ { * } ~ = ~ \frac { k } { k - 1 } } \end{array}$ (Section 4). We provide minimax lower bounds matching these rates in n up to log factors. These results quantify fundamental statistical costs for protecting against large distributional shifts (the worst-case region $\{ Q : D _ { f } \left( Q \| P _ { 0 } \right) \leq \rho \}$ becomes larger as $k  1$ , or $k _ { * } \to \infty )$

Since these minimax guarantees do not necessarily reflect the typical behavior of the estimators, we complete our theoretical analysis in Section 6 with an asymptotic analysis. The estimator $\widehat { \theta } _ { n }$ is consistent under mild (and standard) regularity conditions (Section 6.1). Under suitable diferentiability conditions on $\mathcal { R } _ { f } , \widehat { \theta } _ { n }$ is asymptotically normal at the typical $\scriptstyle { \sqrt { n } } - { \mathrm { r a t e } }$ , allowing us to obtain calibrated confidence intervals (Section 6.2).

Related Work Distributional shift arise in many guises across statistics, machine learning, applied probability, simulation, and optimization; we give a necessarily abridged survey of the many strains of work and their respective foci. Work in domain adaptation seeks models that receive data from one domain and are tested on a specified target; typical approach is to reweight the distribution $P _ { 0 }$ to make it “closer” to the known target distribution $P _ { \mathrm { t a r g e t } } \ [ 8 9 , 5 3 , 1 8 , 9 2 , 9 3 , 9 8 ]$ . In this vein, one interpretation of the worst-case formulation (1) is as importance-weighted loss mini mization without a known target domain—that is, without assuming even unlabeled data from the target domain. The formulation (1) is more conservative than most domain adaptation methods, as it considers shifts in the joint distribution of predictors X and target variable Y instead of covariate shifts.

Other scenarios naturally give rise to structural distributional changes. Time-varying efects are a frequent culprit [49], and time-varying-coeficient models are efective when time indices are available [40, 26]. When one believes there may be latent subpopulations, mixture model approaches can model latent membership directly [4, 41, 69, 27]. In contrast, our worst-case approach (1) does not directly represent (or require) such latent information, and—especially in the case of mixture models—can maintain convexity because of the focus on uniform performance guarantees.

When we know and can identify heterogeneous populations within the data, B¨uhlmann, Meinshausen, and colleagues connect methods that achieve good performance on all subpopulations with causal interventions. In this vein, they study maximin efects on heterogeneous datasets and learn linear models that maximize relative performance over the worst (observed) subgroup [70], which connects to minimax regret in linear models [38, 14, 80, 25, 81]. Without access to information about particular subpopulations, the worst-case formulation (1) is more conservative than their approaches, but can still achieve good performance, as we see in our experimental evaluation.

The idea to build predictors robust to perturbation of an underlying data-generating distribution has a long history across multiple fields. In dynamical systems and control, Petersen et al. [74] build worst-case optimal controllers for systems whose uncertain dynamics are described by Kullback-Leibler (KL) divergence balls. In econometrics, Hansen and Sargent [50] study systems in which rational agents dynamically make decisions assuming worst-case (dynamics) model misspecification, where the misspecification is bounded by an evolving KL-divergence quantity. There is also substantial work in characterizing worst-case sensitivity of risk measures to distributional misspecification [46, 10, 62, 37, 63, 45]. A common goal in such sensitivity calculations is an asymptotic expansion of a risk measure as the radius $\rho$ of the region of misspecification decreases to 0. In contrast, we study statistical properties of the worst-case formulation (1) given observations drawn from the data generating distribution $P _ { 0 }$ , so that we must both address statistical uncertainty and challenges of robustness.

In the optimization literature, a body of work studies distributionally robust optimization prob lems. Several authors investigate worst-case regions arising out of moment conditions on the data vector X [33, 57, 17]. Other work [15, 17, 36, 72, 62, 64] studies a scenario similar to our $f -$ divergence formulation (1). In this line of research, the empirical plug-in procedure (2) with radius $\rho / n$ provides a finite sample confidence set for the population objective $\mathbb { E } _ { P _ { 0 } } [ \ell ( \theta ; X ) ]$ ; the focus there is on the true distribution $P _ { 0 }$ and does not consider distributional shifts. Duchi et al. [36] and Lam and Zhou [64] show how such approximations correspond to generalized empirical likelihood [73] confidence bounds on $\mathbb { E } _ { P _ { 0 } } [ \ell ( \theta ; X ) ]$ . These procedures are identical to the plug-in (2) except that the radius decreases as $\rho / n$ . Thus, the magnitude of this radius depends on whether the modeler’s goal is good performance with respect to $\mathbb { E } _ { P _ { 0 } } [ \ell ( \theta ; X ) ]$ (radius shrinks as $\rho / n )$ , or—as is the case here—robustness under distributional shifts (radius $\rho$ is fixed).

An alternative to our f-divergence based sets $\{ Q : D _ { f } ( Q \| P _ { 0 } ) \leq \rho \}$ are Wasserstein balls [105, 75, 106, 84, 19, 20, 42, 39, 91, 68]. Such approaches are satisfying, as Wasserstein balls allow worst-case distributions with diferent support from the data-generating distribution $P _ { 0 }$ . This power, however, means that tractable reformulations are only available under restrictive scenarios [84, 39, 91], and they remain computationally challenging. Furthermore, most guarantees [20, 39, 84] for these problems also consider approximation only of the canonical (population) loss $\mathbb { E } _ { P _ { 0 } } [ \ell ( \theta ; X ) ]$ using shrinking radius $\rho _ { n } \to 0$ . In comparison, our f-divergence formulation is computationally eficient to solve, even in large-scale learning scenarios [71, 72].

Notation For a sequence of random variables $Z _ { 1 } , Z _ { 2 } , . . .$ . in a metric space ${ \mathcal { Z } } ,$ we say $Z _ { n } \stackrel { d } { \sim } Z$ if $\mathbb { E } [ h ( Z _ { n } ) ]  \mathbb { E } [ h ( Z ) ]$ for all bounded continuous functions $h ,$ and $Z _ { n } \ { \overset { p } { \to } } \ Z$ for convergence in probability. We let $\ell ^ { \infty } ( { \mathcal { Z } } )$ the space of bounded real-valued functions on $\mathcal { Z }$ equipped with the supremum norm. We let $\begin{array} { r } { D _ { \chi ^ { 2 } } \left( P \| Q \right) = \frac { 1 } { 2 } \int \left( d P / d Q - 1 \right) ^ { 2 } d Q } \end{array}$ be the $\chi ^ { 2 } \mathrm { - d i v e r g e n c e }$ . For $Z \sim P$ ess sup Z is its essential supremum. We make the dependence on the underlying measure explicit when we write expectations $\begin{array} { r l } { ( \mathrm { e . g . ~ } } & { { } \mathbb { E } _ { P } [ X ] ) } \end{array}$ , except for when $P = P _ { 0 }$ . For $k \in \mathsf { \Gamma } ( 1 , \infty )$ , we let $k _ { * } : = k / ( k - 1 )$ ). By $\nabla \ell ( \theta ; X )$ we mean diferentiation with respect to the parameter vector $\boldsymbol { \theta } \in \mathbb { R } ^ { d }$

## 2 Formulation

We begin our discussion by presenting dual reformulations for the worst-case objective $\mathcal { R } _ { f } ( \theta ; P _ { 0 } )$ deferring formulation in terms of worst subpopulations to Example 3 to come. The dual form gives a single convex minimization problem for computing the empirical plug-in estimator (2) in place of the minimax formulation, and it makes explicit the role that $t \mapsto f ( t )$ plays in defining such a risk-averse version of the usual average loss $\mathbb { E } _ { P _ { 0 } } [ \ell ( \theta ; X ) ]$ . This provides an equivalence between distributional robustness and tail-performance, which we draw on subsequently both statistical and computational reasons. Defining the uncertainty region

$$
\mathcal {U} _ {P} := \left\{Q: D _ {f} (Q \| P) \leq \rho \right\},
$$

we may use the likelihood ratio $L ( x ) : = d Q ( x ) / d P _ { 0 } ( x )$ to reformulate our distributionally robust problem (1) via

$$
\begin{array}{l} \mathcal {R} _ {f} (\theta ; P _ {0}) = \sup _ {P} \left\{\mathbb {E} _ {P} [ \ell (\theta ; X) ]: P \in \mathcal {U} _ {P _ {0}} \right\} \\ = \sup _ {L > 0} \left\{\mathbb {E} _ {P _ {0}} [ L (X) \ell (\theta ; X) ] \mid \mathbb {E} _ {P _ {0}} [ f (L (X)) ] \leq \rho , \mathbb {E} _ {P _ {0}} [ L (X) ] = 1 \right\}, \end{array}\tag{3}
$$

where the supremum is over measurable functions. We now recall Ben-Tal et al. [15] and Shapiro’s dual reformulation of the quantity (3), where $f ^ { * } ( s ) : = \operatorname* { s u p } _ { t } \{ s t - f ( t ) \}$ is the usual Fenchel conjugate.

Proposition 1 (Shapiro [87, Section 3.2]). Let P be a probability measure on $( \mathcal { X } , \mathcal { A } )$ and $\rho > 0$ Then

$$
\mathcal {R} _ {f} (\theta ; P) = \inf _ {\lambda \geq 0, \eta \in \mathbb {R}} \left\{\mathbb {E} _ {P} \left[ \lambda f ^ {*} \left(\frac {\ell (\theta ; X) - \eta}{\lambda}\right) \right] + \lambda \rho + \eta \right\}\tag{4}
$$

for all θ. Moreover, if the supremum on the left hand side is finite, there are finite $\lambda ( \theta ) \geq 0$ and $\eta ( \theta ) \in \mathbb { R }$ attaining the infimum on the right hand side.

For convex losses $\theta \mapsto \ell ( \theta ; X )$ , the dual form (4) is jointly convex in $( \theta , \eta , \lambda )$ . While interior point methods [24] are powerful tools for solving such problems, they may be slow in settings where $n ,$ the sample size, and $d ,$ the dimension of $\theta \in \Theta$ , are large. More direct methods can directly solve the primal form, including gradient descent or stochastic gradient algorithms [71, 72].

Divergence families Much of our development centers on two families of divergences. The R´enyi α-divergence [104] between distributions P and Q is

$$
D _ {\alpha} (P \| Q) := \frac {1}{\alpha - 1} \log \int \left(\frac {d P}{d Q}\right) ^ {\alpha} d Q,\tag{5}
$$

where the limit as $\alpha  1$ satisfies $D _ { 1 } ( P \| Q ) = D _ { \mathrm { k l } } \left( P \| Q \right)$ . For analytical reasons, we use the equivalent Cressie-Read family of f-divergences [29]. These are parameterized by $k \in ( - \infty , \infty ) \ \backslash$ $\begin{array} { r } { \{ 0 , 1 \} , k _ { * } = \frac { k } { k - 1 } } \end{array}$ , with

$$
f _ {k} (t) := \frac {t ^ {k} - k t + k - 1}{k (k - 1)} \quad \text { so } \quad f _ {k} ^ {*} (s) := \frac {1}{k} \left[ ((k - 1) s + 1) _ {+} ^ {k _ {*}} - 1 \right].\tag{6}
$$

We let $f _ { k } ( t ) = + \infty$ for $t < 0$ , and we define $f _ { 1 }$ and $f _ { 0 }$ as their respective limits as $k  0 , 1$ . The family of divergences (6) includes χ<sup>2</sup>-divergence $\left( k = 2 \right)$ , empirical likelihood $f _ { 0 } ( t ) = - \log t + t - 1$ and KL-divergence $f _ { 1 } ( t ) = t \log t - t + 1$ , and we frequently use the shorthand

$$
\mathcal {R} _ {k} (\theta ; P) := \sup _ {Q \ll P} \left\{\mathbb {E} _ {Q} [ \ell (\theta ; X) ]: D _ {f _ {k}} (Q \| P) \leq \rho \right\}.\tag{7}
$$

While most of our results generalize to other values of k, we focus temporarily on $k \in ( 1 , \infty )$ for ease of exposition (only our finite-sample guarantees in Section 4 require $k \in ( 1 , \infty ) )$ . By minimizing out $\lambda \geq 0$ in the dual form (4), we obtain a simplified formulation for the Cressie-Read family (6).

Lemma 1. For any probability P on $( \mathcal { X } , \mathcal { A } ) , k \in ( 1 , \infty ) , k _ { * } = k / ( k - 1 )$ , any $\rho > 0$ , and $c _ { k } ( \rho ) : =$ $( 1 + k ( k - 1 ) \rho ) ^ { \frac { 1 } { k } }$ , we have for all $\theta \in \Theta$

$$
\mathcal {R} _ {k} (\theta ; P) = \inf _ {\eta \in \mathbb {R}} \left\{c _ {k} (\rho) \mathbb {E} _ {P} \left[ (\ell (\theta ; X) - \eta) _ {+} ^ {k _ {*}} \right] ^ {\frac {1}{k _ {*}}} + \eta \right\}.\tag{8}
$$

See Section A.1 for the proof. The simplified dual form (8) shows that protecting against worstcase distributional shifts is equivalent to optimizing the tail-performance of a model; the worst-case objective $\mathcal { R } _ { k } ( \theta ; P )$ only penalizes losses above the optimal dual variable $\eta ^ { \star } ( \theta )$ . The $L ^ { k _ { * } } ( P )$ -norm upweights these tail values of $\ell ( \theta ; x )$ , giving a worst-case objective that focuses on “hard” regions of X. Eq. (8) also makes explicit the relationship between the growth $f _ { k }$ and the worst-case objective $\mathcal { R } _ { k } ( \theta ; P )$ : as growth of $f _ { k } ( t )$ for large t becomes steeper $( k \uparrow \infty )$ , the f-divergence ball $\{ Q : D _ { f _ { k } } \left( Q \| P \right) \leq \rho \}$ shrinks, and the risk measure $\mathcal { R } _ { k } ( \theta ; P )$ becomes less conservative (smaller). Since the dual form (8) quantifies this with the $L ^ { k _ { * } } ( P ) \mathrm { \bar { - n o r m } }$ of the loss above the quantile η, we see that $f _ { k }$ with $k \in ( 1 , \infty )$ is a possible choice if the loss has finite k -moments under the nominal distribution $P _ { 0 }$ . In contrast, the worst-case formulation (1) corresponding to the KL-divergence (k = 1) is finite only when the moment generating function of the loss exists [3].<sup>1</sup>

An extensive literature on coherent risk measures defines utility functions that exhibit “sensible” tail risk preference [8, 78, 60, 88]; there is a duality between distributionally robust optimization and coherent risk measures [e.g. 88, Thm. 6.4]. In this sense the distributionally robust problem (1) is a risk-averse formulation of the canonical stochastic optimization problem of minimizing $\mathbb { E } _ { P _ { 0 } } [ \ell ( \theta ; X ) ]$ Indeed, Krokhmal [60] proposes the dual form (8) as a higher order generalization of the classical conditional value-at-risk [78], which corresponds to $\mathcal { R } _ { k } ( \theta ; P )$ defined with $k = \infty ( \mathrm { o r } k _ { * } = 1 )$ in our notation.

## 2.1 Examples

While—as we note in the introduction—we do not provide precise recommendations for the choice of f-divergence, it is instructive to consider a few examples for motivation and to connect to our worst-case subpopulation considerations (Examples 3–5). We begin with a generic description and specialize subsequently, deferring heuristic procedures for choosing $f$ and $\rho$ (and empirical eficacy evaluations) to the next section.

Example 1 (Generic distributional shift): Consider data in pairs $( X , Y )$ , where X is a feature (covariate) vector and $Y$ is a dependent variable (e.g. label) we wish to model from X. Let U be a latent (unobserved) confounding variable, and assume that the pair $( X , Y )$ jointly follows $P _ { 0 } ( \cdot \mid$ $U = u )$ . For a marginal distribution $\mu$ on $U .$ , let $\begin{array} { r } { P _ { \mu } ( ( X , Y ) \in A ) : = \int P _ { 0 } ( ( X , Y ) \in A \mid U = u ) d \mu ( u ) } \end{array}$ We have the essentially tautological correspondence

$$
\left\{P \mid D _ {f} (P \| P _ {0}) \leq \rho \right\} = \left\{P _ {\mu} \mid \int f \left(\frac {d P _ {\mu} (x , y)}{d P _ {0} (x , y)}\right) d P _ {0} (x, y) \leq \rho \right\}.
$$

The robustness set is a family of distributional interventions on U. We leave characterizing the precise form of such interventions as an open question. 

For well-specified linear models, it is frequently the case that the robust parameter $\theta _ { \mathrm { d r o } } \in$ $\mathrm { a r g m i n } _ { \theta } \mathcal { R } _ { f } ( \theta ; P )$ minimizing the objective (1) coincides with the true parameter, though its plugin estimator may be less eficient than standard ordinary least-squares estimators (we do not discuss this eficiency here).

Example 2 (Regression and stochastic domination): To make things precise, recall stochastic orders [85]: for two R-valued random variables U and V, we say that V stochastically dominates U if $\mathbb { P } ( U \geq t ) \leq \mathbb { P } ( V \geq t )$ for all $t \in \mathbb { R }$ , written $U \preceq V !$ ; this is equivalent to the condition that $\mathbb { E } [ g ( U ) ] \leq \mathbb { E } [ g ( V ) ]$ for all nondecreasing $g .$ . For any problem with data in pairs $( X , Y )$ and a loss $\ell ( \theta ; X , Y )$ , if there exists a parameter $\theta _ { \star }$ such that $\ell ( \theta _ { \star } ; X , Y ) \preceq \ell ( \theta ; X , Y )$ for all θ, we then have $\theta _ { \star } \in \mathrm { { a r g m i n } } _ { \theta } \mathcal { R } _ { f } ( \theta ; P )$ for all f-divergences, as $\mathcal { R } _ { f }$ is a coherent risk measure [cf. 88, Ch. 6.3]. Existence of such $\theta _ { \star }$ is a strong condition, but holds in a few important cases.

For concreteness consider linear regression, where $( x , y ) \in \mathbb { R } ^ { d } \times$ R and $\begin{array} { r } { \ell ( \theta ; x , y ) = \frac { 1 } { 2 } ( \theta ^ { T } x - y ) ^ { 2 } } \end{array}$ First, we consider the case that the model is well-specified, so that $Y = X ^ { T } \theta _ { \star } { + } \varepsilon$ , where $\mathbb { E } [ \varepsilon \mid X ] = 0$ If the distribution of ε given $X = x$ is symmetric and log quasiconcave (unimodal), then Anderson’s theorem [7, 43, Thm. 11.1] implies that

$$
\mathbb {P} (| x ^ {T} \theta - Y | \geq t \mid X = x) = \mathbb {P} (| x ^ {T} (\theta - \theta_ {\star}) - \varepsilon | \geq t \mid X = x) \geq \mathbb {P} (| \varepsilon | \geq t \mid X = x),
$$

for all $t \in \mathbb { R }$ , and so $\ell ( \theta _ { \star } ; X , Y ) \preceq \ell ( \theta ; X , Y )$ for all $\theta ,$ , and $\theta _ { \star } \in \mathrm { a r g m i n } _ { \theta } \mathcal { R } _ { f } ( \theta ; P )$

In a diferent vein, we can consider the case that $X , Y$ are jointly Gaussian and mean zero,

$$
(X, Y) \sim \mathsf {N} \left(\mathbf {0}, \left[ \begin{array}{c c} \Sigma & \gamma \\ \gamma^ {T} & \sigma^ {2} \end{array} \right]\right).
$$

Then for any θ we have $( X ^ { T } \theta - Y ) \sim \mathsf { N } ( 0 , \theta ^ { T } \Sigma \theta - 2 \theta ^ { T } \gamma + \sigma ^ { 2 } )$ , and the ordinary least-squares solution $\theta _ { \mathrm { o l s } } = \Sigma ^ { - 1 } \gamma = \mathbb { E } [ X X ^ { T } ] ^ { - 1 } \mathbb { E } [ X Y ]$ evidently uniformly minimizes the variance of $( X ^ { T } \theta - Y )$ Once again, we thus have the stochastic dominance $\ell ( \theta _ { \mathrm { o l s } } ; X , Y ) \preceq \ell ( \theta ; X , Y )$ for all $\theta ,$ and so the robust solutions coincide with standard estimators. 

Example 3 (Worst-case minority performance and CVaR): For $0 \textless \alpha \leq 1$ , the conditional value-at-risk [78] (CVaR) is

$$
\mathrm{CVaR} _ {\alpha} (\theta ; P _ {0}) := \inf _ {\eta \in \mathbb {R}} \left\{\alpha^ {- 1} \mathbb {E} _ {P _ {0}} \left[ (\ell (\theta ; X) - \eta) _ {+} \right] + \eta \right\}.
$$

This corresponds to an uncertainty set arising out of limiting f- or R´enyi divergences. Recalling the R´enyi divergence (5), we have $\begin{array} { r } { D _ { \infty } ( P \| Q ) : = \operatorname* { l i m } _ { \alpha \to \infty } D _ { \alpha } ( P \| Q ) = } \end{array}$ ess sup log $\begin{array} { l } { { \frac { d { \breve { P } } } { d Q } } } \end{array}$ , and if we define $f _ { \infty , c } ( t ) = 0$ for $0 \leq t \leq c$ and $+ \infty$ otherwise, then the uncertainty region

$$
\begin{array}{l} \mathcal {U} _ {P _ {0}} := \left\{P \mid D _ {\infty} (P \| P _ {0}) \leq \log \frac {1}{\alpha} \right\} = \left\{P \mid D _ {f _ {\infty , \alpha^ {- 1}}} (P \| P _ {0}) \leq 1 \right\} \\ \qquad = \left\{P \mid \text { there exists } Q,   \beta \in [ \alpha , 1 ] \text { s.t. } P _ {0} = \beta P + (1 - \beta) Q \right\} \end{array}
$$

by a calculation [88, Example 6.19]. The uncertainty set corresponds to distributions with minority sub-populations of size at least α, and $\begin{array} { r } { \operatorname { C V a R } _ { \alpha } ( \theta ; P _ { 0 } ) = \operatorname* { s u p } _ { P \in \mathcal { U } _ { P _ { 0 } } } \mathbb { E } _ { P } [ \ell ( \theta ; X ) ] } \end{array}$ is the expected loss of the worst α-sized subpopulation. 

The Kusuoka representation [86, 61] of risk measures shows that the robust formulations (1) are worst-case CVaR mixtures, $\begin{array} { r } { \mathcal { R } _ { f } ( \theta ; P _ { 0 } ) = \operatorname* { s u p } _ { \mu \in \mathcal { M } _ { f } } \int _ { 0 } ^ { 1 } \mathrm { C V a R } _ { \alpha } ( \theta ; P _ { 0 } ) d \mu ( \alpha ) } \end{array}$ for a set $\mathcal { M } _ { f }$ of probability measures on [0, 1]. They thus correspond to drawing a random sub-population size α and measuring the loss of the worst subpopulation of $P _ { 0 }$ mass at least α. Precisely connecting the subpopulation size and robustness set $\{ P : D _ { f } \left( P \| P _ { 0 } \right) \le \rho \}$ is challenging.

We now consider two examples in which data comes from latent mixtures of populations, where within each subpopulation a model is well-specified, though it is not globally. In both of these cases—mean estimation and a linear regression problem—we see that as the robustness parameter $\rho \uparrow$ ∞ in the DRO formulation (1), the robust estimator converges to the minimax estimator minimizing the worst-case loss across all sub-populations. This recalls Meinshausen and B¨uhlmann [70], who consider min/max efects in heterogeneous regression problems with known group identities, but here the DRO estimator recovers a minimax estimator without such knowledge. The examples are stylized to give explicit limits, though they convey the intuition that the robust estimators seek to do well on unknown sub-populations in a reasonably precise way. In each example, we consider the conditional value at risk (Ex. 3) for simplicity; the results for higher-order robustness measures are similar but tedious.

Example 4 (Mixtures in mean estimation): Consider a finite number of distinct populations on $\mathbb { R } ^ { d }$ indexed by $v \in V$ , each appearing with probability $p _ { v } > 0$ , where under population v, we observe

$$
Y = \theta_ {v} + \varepsilon , \varepsilon \stackrel {\mathrm{iid}} {\sim} \mathsf {N} (0, I _ {d}).
$$

Letting the loss $\begin{array} { r } { \ell ( \theta ; y ) = \frac { 1 } { 2 } \left\| \theta - y \right\| _ { 2 } ^ { 2 } , } \end{array}$ we define the minimax estimator

$$
\theta_ {\text {minimax}} := \underset {\theta} {\operatorname{argmin}} \max _ {v \in V} \| \theta - \theta_ {v} \| _ {2} ^ {2} = \underset {\theta} {\operatorname{argmin}} \max _ {v \in V} \mathbb {E} _ {v} [ \| \theta - Y \| _ {2} ^ {2} ].
$$

The unique vector $\theta _ { \mathrm { m i n i m a x } }$ coincides with the Chebyshev center of the vectors $\{ \theta _ { v } \} ~ [ 2 4 , \mathrm { C h . ~ } 8 . 5 ] ;$ it also requires knowledge of the groups $v \in V$ . In Appendix B.1, we show that if $\theta _ { \alpha } = \operatorname { a r g m i n } _ { \theta } \operatorname { C V a R } _ { \alpha } ( \ell ( \theta ; Y ) )$ ， then

$$
\theta_ {1} = \sum_ {v} p _ {v} \theta_ {v} \text { and } \lim _ {\alpha \downarrow 0} \theta_ {\alpha} = \theta_ {\mathrm{minimax}}.
$$

Recalling from Ex. 3 that the parameter α is inversely proportional to the robustness in the DRO formulation, we see the expected behavior: as robustness increases, the DRO estimator converges to an estimator minimizing the worst sub-population expected loss. 

Example 5 (Mixtures in linear regression): We expand the previous example to allow covariates and potentially infinite subgroups. For groups indexed by $v \in V$ , we draw $v \in V$ according to a probability measure $\mu$ on V, and then conditional on v draw

$$
X \sim \mathsf {N} (0, \Sigma_ {v}), \varepsilon_ {v} \sim \mathsf {N} (0, \sigma_ {v} ^ {2}), Y = X ^ {T} \theta_ {v} + \varepsilon_ {v},\tag{9}
$$

assuming implicitly that all parameters are v-measurable. (To show the result in the most straightforward way, we make the simplifying assumptions that $0 < \mathrm { i n f } _ { v } \sigma _ { v } ^ { 2 } \leq \mathrm { s u p } _ { v } \sigma _ { v } ^ { 2 } < \infty$ , that the eigenvalues of $\Sigma _ { v }$ are finite and bounded away from 0 uniformly in $v ,$ that sup $) _ { v } \| \theta _ { v } \| < \infty$ , and we also assume that for each $\boldsymbol { \theta } \in \mathbb { R } ^ { d }$ , we have ess sup ${ \bf \nabla } _ { v } ( \theta - \theta _ { v } ) ^ { T } \Sigma _ { v } ( \theta - \theta _ { v } ) + \sigma _ { v } ^ { 2 } = \operatorname* { s u p } _ { v } ( \theta - \theta _ { v } ) ^ { T } \Sigma _ { v } ( \theta - \theta _ { v } ) + \sigma _ { v } ^ { 2 } .$ Each of these assumptions is trivial when there are a finite number of groups.)

Letting $\mathbb { E } _ { v }$ denote expectation according to the model (9), let $\ell ( \theta ; x , y ) = \textstyle { \frac { 1 } { 2 } } ( x ^ { T } \theta - y ) ^ { 2 }$ be the standard squared error and consider the conditional value at risk

$$
\mathrm{CVaR} _ {\alpha} (\ell (\theta ; X, Y)) = \inf _ {\eta} \left\{\frac {1}{\alpha} \int \mathbb {E} _ {v} \left[ (\ell (\theta ; X, Y) - \eta) _ {+} \right] d \mu (v) + \eta \right\}.
$$

We define the minimax estimator to minimize the worst sub-population risk

$$
\theta_ {\mathrm{minimax}} = \underset {\theta} {\operatorname{argmin}} \sup _ {v \in V} \left\{\mathbb {E} _ {v} [ (\theta^ {T} X - Y) ^ {2} ] = (\theta - \theta_ {v}) ^ {T} \Sigma_ {v} (\theta - \theta_ {v}) + \sigma_ {v} ^ {2} \right\}.
$$

In this case, for the distributionally robust parameter $\begin{array} { r } { \theta _ { \alpha } : = \operatorname { a r g m i n } _ { \theta } \operatorname { C V a R } _ { \alpha } ( \ell ( \theta ; X , Y ) ) } \end{array}$ ) and ordinary least squares solution θ<sub>ols</sub> = argmin $ \mathbb { E } [ \ell ( \theta ; X , Y ) ]$ , we show in Appendix B.2 that

$$
\theta_ {\mathrm{ols}} = \theta_ {1} = \int \theta_ {v} d \mu (v) \quad \mathrm{and} \quad \lim _ {\alpha \downarrow 0} \theta_ {\alpha} = \theta_ {\mathrm{minimax}}.
$$

We again see the interpolation from an average parameter to one that minimizes the worst-case subpopulation risk as the robustness increases (i.e. α ↓ 0). 

## 3 Empirical analysis, validation, and choice of uncertainty set

As this paper proposes and argues for alternatives to empirical risk minimization and standard Mestimation—workhorses of much of machine learning and statistics [102, 103, 55]—it is important that we justify our approach. To that end, we first provide a number of experiments that illustrate the empirical properties of the distributionally robust formulation (1). We test our plug-in estimator (2) on a variety of tasks involving real and simulated data, and compare its performance with the standard empirical risk minimizer

$$
\widehat {\theta} _ {n} ^ {\mathrm{erm}} \in \operatorname * {a r g m i n} _ {\theta \in \Theta} \mathbb {E} _ {\widehat {P} _ {n}} [ \ell (\theta ; X) ].
$$

For concreteness, we focus on the Cressie-Read (equivalently R´enyi) divergence family (6) with $k \in ( 1 , \infty )$ , experimenting on three related challenges:

1. Domain adaptation and distributional shifts, in which we fit predictors on a training distribution difering from the test distribution

2. Performance on tail losses, where we measure quantiles of a model’s loss rather than its expected losses

3. Data coming from multiple heterogeneous subpopulations, where we study performance on each subpopulation (or worst-case subpopulations).

If our intuition on the distributionally robust risk is accurate, we expect results of roughly the following form: as we decrease k in the Cressie-Read divergence (6), $f _ { k } ( t ) \propto t ^ { k } - 1$ , the solutions should exhibit more robustness while trading against average-case empirical performance, as the set $\{ Q ~ : ~ D _ { f } ( Q \| P _ { 0 } ) ~ \leq ~ \rho \}$ gets larger. Thus, such models should have better tail behavior or generalization on rare or dificult subpopulations compared to standard average-case procedures. We expect increasing $\rho$ to exhibit similar efects, and we shall see the ways this intuition bears out in our experiments.

Since the choice of $f$ and $\rho$ governs the trade-of between average and tail performance, we propose two heuristics for choosing $\rho$ and $k ,$ evaluating their performance on simulated examples. Our heuristics aim to provide uniform performance over dificult inputs by considering proxy subpopulations constructed from the training data, though to be clear, the only formal guarantees on robustness they provide is robustness to shifts contained in specified by $f _ { k }$ for the chosen and k (the duality relationships (4) and (8) makes the robustness less sensitive to $\rho )$ . Our first heuristic splits the training dataset into s equi-sized groups based on the values of the response variable $Y$ where Y has highest values in the first group, and the lowest values in the last sth group. We split each of the s groups into 80%/20% training/validation splits, and re-unify all of the 80% splits to give a new training dataset with 80% of the original data. We train our robust models (2) (varying $\rho$ and k) on the new training dataset, evaluating these models on the unused data from each group (20%), giving s diferent empirical losses for a given model. A model’s score is then its empirical loss on the worst of the s held-out sets. We use $s = 5$ groups since this consistently gives a good selection procedure across diferent settings. As our second heuristic, we consider scenarios where more is known about the problem. If a small auxiliary dataset collected from a worse-than-average subpopulation is available, we tune $\rho$ and k on this auxiliary dataset so that heuristically, the resulting model performs uniformly well against all subpopulations of a similar size (the worst-case formulation (2) optimizes performance only over large enough subpopulations e.g. Example 3). Empirically, we observe that the second heuristic performs well even on rare subgroups that are far from the subpopulation generating the auxiliary dataset. On simulation examples, we observe good worst-case subpopulation performance for both procedures, with moderate degradation in the average-case performance.

We begin with simulation experiments that touch on all three of above challenges in Section 3.1. To investigate these challenges on diferent real-world datasets, in Section 3.2 we study domain adaptation in the context of predictors trained to recognize handwritten digits, then test them to recognize typewritten digits. In Section 3.3, we study tail prediction performance in a crime prediction problem. In our final experiment, in Section 3.4, we study a fine-grained recognition problem, where a classifier must label images as one of 120 diferent dog breeds; this highlights a combination of items 2 and 3 on tail performance and subpopulation performance.

To eficiently solve the empirical worst-case problem (2) for the Cressie-Read family (6), we employ two approaches. For small datasets (small n and d), we solve the dual form (8) directly using a conic interior point solver; we extended the open-source Julia package convex.jl to implement power cone solvers [100] (the package now contains our implementation). For larger datasets $( \mathrm { e . g . ~ } n \approx 1 0 ^ { 3 } - 1 0 ^ { 5 }$ and $d \approx 1 0 ^ { 2 } - 1 0 ^ { 4 } )$ , we apply gradient descent with backtracking Armijo line-searches [24]. The probability vector $Q ^ { * } = \{ q _ { i } ^ { * } \} _ { i = 1 } ^ { n } \in \mathbb { R } _ { + } ^ { n }$ achieving the supremum in the definition (7) is unique as long as the loss vector $[ \ell ( \theta ; X _ { i } ) ] _ { i = 1 } ^ { n }$ is non-constant, which it is in all of our applications, so $\mathcal { R } _ { k }$ is diferentiable [51, Theorem VI.4.4.2] with

![](images/172ee525fd6fec502034bad8c2e2961d3475c45d69e0ab3a4e23f80a249f172f.jpg)  
(a) Classification

![](images/ddc164ab9471db81a1eaa08983abe46e990e9026875235f3e5091713b59f3441.jpg)  
(b) Regression  
Figure 1. (a) Hinge losses (average and 90th percentile in solid and dashed lines, respectively) under distributional shifts from $\theta _ { 0 } ^ { \star }$ to $\theta _ { t } ^ { \star } = \theta _ { 0 } ^ { \star }$ ·cos t+v ·sin t. The horizontal axis indexes perturbation t. (b) Losses on minority group (solid-line) and majority group (dotted-line) under the distribution (11). We define the minority group as those with $X ^ { 1 } \leq z _ { . 9 5 }$

$$
\nabla \mathcal {R} _ {k} (\theta , \widehat {P} _ {n}) = \sum_ {i = 1} ^ {n} q _ {i} ^ {*} \nabla \ell (\theta ; X _ {i}) \text {and} Q ^ {*} = \underset {Q: D _ {f _ {k}} (Q \| \widehat {P} _ {n}) \leq \rho} {\operatorname{argmax}} \left\{\sum_ {i = 1} ^ {n} q _ {i} \ell (\theta ; X _ {i}) \right\}.
$$

We use a fast bisection method $[ 7 2 ]$ to compute $Q ^ { * }$ at every iteration of our first-order method; see https: $\gamma / \mathtt { g i }$ thub.com/hsnamkoong/robustopt for the implementation.

## 3.1 Simulation

Our first experiments use simulated data, where we fit linear models for binary classification and prediction of a real-valued signal. We train our models with diferent values of f-divergence power k and tolerance $\rho ,$ testing them on perturbations of the data-generating distribution.

## 3.1.1 Domain adaptation and distributional shifts

We investigate distributional shifts via a binary classification experiment using the hinge loss $\ell ( \theta ; ( x , y ) ) = \left( 1 - y x ^ { \top } \theta \right) _ { + }$ , where $y \in \{ \pm 1 \}$ and $\boldsymbol { x } \in \mathbb { R } ^ { d }$ with $d = 5$ . We choose a vector $\theta _ { 0 } ^ { \star } \in \mathbb { R } ^ { 5 }$ uniformly on the unit sphere and generate data

$$
X \stackrel {{\text {iid}}} {{\sim}} \mathsf {N} (0, I _ {d}) \quad \text {and} \quad Y \mid X = \left\{ \begin{array}{l l} \text {sign} (X ^ {\top} \theta_ {0} ^ {\star}) & \quad \text {w.p.} 0. 9 \\ - \text {sign} (X ^ {\top} \theta_ {0} ^ {\star}) & \quad \text {w.p.} 0. 1. \end{array} \right.\tag{10}
$$

(Our below observations still hold when varying these probabilities.) We train our models on $n _ { \mathrm { t r a i n } } = 1 0 0$ training data points, where we use $\rho = . 5$ and vary values of $k \in \{ 1 . 5 , 2 , 4 \}$ for our distributionally robust procedure (2). To simulate distributional shift, we take a uniformly random vector $v \perp \theta _ { 0 } ^ { \star } , v \in \mathbb { S } ^ { d - 1 }$ , and for $s \in [ 0 , \pi ]$ define $\theta _ { s } ^ { \star } = \theta _ { 0 } ^ { \star }$ · cos s + v · sin s, so that $\theta _ { \pi } ^ { \star } = - \theta _ { 0 } ^ { \star }$ . For each perturbation, we generate $n _ { \mathrm { t e s t } } = 1 0 0 , 0 0 0$ test examples using the same scheme (10) with $\theta _ { t } ^ { \star }$ replacing $\theta _ { 0 } ^ { \star }$

We measure both average and 90%-quantile losses for our problems. Based on our intuition, we expect that the lower k is (recall that $f _ { k } ( t ) \propto t ^ { k } )$ , the better the fitted model should perform on high quantiles of the loss, with potentially worse average performance. Moreover, for $s = 0$ , we should see that ERM and large k solutions exhibit the best average performance, with growing s reversing this behavior. In Figure 1(a), we plot the average loss (solid line) and the 90%-quantile of the losses (dotted line) on the shifted test sets, where the horizontal axis displays the rotation $s \in [ 0 , \pi ]$ . The plot bears out our intuition: the distributionally robust solution $\widehat { \theta } _ { n }$ has worse mean loss on the original distribution than empirical risk minimization (ERM) while achieving significantly smaller loss on the distributional shifts. The ordering of the mean performance of the diferent solutions inverts as the perturbation grows: under no perturbation $( s = 0 )$ , the least robust method (ERM) has the best performance, while the most robust method (corresponding to $\begin{array} { r } { k = \frac { 3 } { 2 } ) } \end{array}$ performs the best under large distributional perturbations (s large).

## 3.1.2 Tail performance

We transition now to regression, investigating performance on rare examples, where the goal is to predict $y \in \mathbb { R }$ from $\boldsymbol { x } \in \mathbb { R } ^ { d }$ and we use loss $\begin{array} { r } { \ell ( \theta ; ( x , y ) ) = \frac { 1 } { 2 } ( y - x ^ { \top } \theta ) ^ { 2 } } \end{array}$ . In this case, we take $d = 5$ and generate data $X \overset { \mathrm { i i d } } { \sim } N ( 0 , I _ { d } ) , \varepsilon \sim N ( 0 , . 0 1 )$ ,

$$
Y = \left\{ \begin{array}{l l} X ^ {\top} \theta^ {\star} + \varepsilon & \text {if} X ^ {1} \leq z _ {. 9 5} = 1. 6 4 5 \\ X ^ {\top} \theta^ {\star} + X ^ {1} + \varepsilon & \text {otherwise,} \end{array} \right.\tag{11}
$$

where we choose $\theta ^ { \star }$ uniformly on the unit sphere $\mathbb { S } ^ { d - 1 }$ and $X ^ { 1 }$ denotes the first coordinate of $X$ (We use very small noise to highlight the more precise transition between average-case and higher percentiles.) As the efect of $X ^ { 1 }$ changes only 5% of the time (when it is above $z _ { . 9 5 } )$ , we expect ERM to have poor performance on rare events when $X ^ { 1 } \geq 1 . 6 4 5$ , or in the tails generally. In addition, a fully robust solution is $\theta ^ { \mathrm { r o b } } = \theta ^ { \star } + \textstyle \frac { 1 } { 2 } e _ { 1 }$ , as this minimizes worst-case expected loss across the two cases (11); we expect that for high robustness parameters $( \rho$ large) the robust model should have worse average performance but about half of the losses at higher quantiles. We simulate $n _ { \mathrm { t r a i n } } = 2 0 0 0$ training data points, and train the distributionally robust solution (2) with $\rho \in \{ . 0 0 1 , . 0 1 , . 1 , . 5 , 4 . 5 \}$ , and $k \in \{ 1 . 5 , 2 , 4 \}$ . In Figure 1(b), we plot the mean loss under the data generation scheme (11) as solid lines and the 90%-quantile as a dotted line. We see once again that the robust solutions trade tail performance for average-case performance. The tail performance (90%-quantile loss) improve with increasing robustness level $\rho ,$ with slight degradation in average case performance.

## 3.1.3 Performance on diferent subpopulations

For our final small-scale simulation, we study item 3 (subpopulation performance) by considering a two-dimensional regression problem with heterogeneous subpopulations. We consider two scenarios: a two-group setting and an infinite number of groups. In each scenario, we demonstrate the performance of our heuristic procedure for choosing $\rho$ and $k ;$ these subpopulation scenarios are appropriate for succinctly characterizing the trade-of between average and tail subpopulations. Our tuning procedure provides good performance on the (latent) worst-case subpopulation even when the proxy subpopulation for tuning $\rho$ and k is far from the rare subpopulation. In what follows, we denote by “YSplit” our first proposal that chooses $\rho$ and k based on sorted values of $Y$ .

![](images/cfc804c867459a712ab8b78253f983ff6b1e3b2155eab9b8afcd83648f355bad.jpg)  
(a) Average loss

![](images/596951eeca41f0ded2eef21e51c0fb4746a6fbcd9fe5f9fbdc5a4c1c3a7df7d0.jpg)  
(b) Loss on minority group  
Figure 2. Two groups: Figures (a) and (b) plots average and minority group losses under the distribution (13). “YSplit” is the performance of the model whose $\rho$ and $k$ was chosen based on groups formed by sorted values of $Y$ .

Two groups In our first scenario, for $\theta _ { 0 } ^ { \star } = ( 1 , . 1 ) , \ \theta _ { 1 } ^ { \star } = ( 1 , 1 )$ , we generate

$$
Y = X ^ {\top} ((1 - G) \theta_ {0} ^ {\star} + G \theta_ {1} ^ {\star}) + \varepsilon\tag{12}
$$

where $X \sim { \cal N } ( 0 , I _ { 2 } ) , \varepsilon \sim \mathsf { N } ( 0 , . 0 1 )$ , and $G \in [ 0 , 1 ]$ indicates a random latent group. We assume that X, G and ε are mutually independent. Both the distributionally robust procedure (2) and ERM are oblivious to the label $G ,$ , where we think of $G = 1$ as the majority group, and $G = 0$ as the minority group. We simulate $n _ { \mathrm { t r a i n } } = 1 0 0 0$ training data points, and train ERM and robust models (2) on varying values of k and $\rho .$ . We let

$$
G = \left\{ \begin{array}{l l} 0 & \text {with probability .1 (minority)} \\ 1 & \text {with probability .9 (majority)} \end{array} \right.\tag{13}
$$

In this two-group setting, we also consider the maximin efects estimator [70]

$$
\widehat {\theta} _ {n} ^ {\mathrm{maximin}} = \operatorname * {a r g m a x} _ {\theta} \min _ {g = 0, 1} \left\{2 \theta^ {\top} \widehat {\Sigma} _ {n, g} \theta_ {g} ^ {\star} - \theta^ {\top} \widehat {\Sigma} _ {n, g} \theta \right\}
$$

as a benchmark, where ${ \widehat \Sigma } _ { n , g }$ is the empirical covariance matrix of the $X _ { i }$ with $G _ { i } = g$ , which maximizes the explained variance for each group [70]. The oracle estimator ${ \widehat { \theta } } _ { n } ^ { \mathrm { { m a x i m i n } } }$ requires knowledge of the labels $G _ { i }$ and the group-specific regressors $\theta _ { g } ^ { \star }$ for $g = 0 , 1$

In Figure $2 ( \mathrm { a } )$ and (b), we plot the average and minority group losses for the diferent methods, respectively. Here the robust methods interpolate between the empirical risk minimizing (ERM) solution—which has the best average loss and worst minority group loss—and the maximin estimator $\widehat { \theta } _ { n } ^ { \mathrm { m a x i m i n } }$ , which sacrifices performance on the average loss for strong minority group performance. The distributionally robust estimators $\widehat { \theta } _ { n }$ exhibit tradeofs between the two regimes, improving performance on the minority population at smaller degradation in the average loss. The parameters $\rho$ and k allow flexibility in achieving these tradeofs, though they of course must be set appropriately in applications. Our first heuristic $\left( \mathrm { ^ { 6 6 } Y S p l i t ^ { 3 7 } } \right)$ chooses $\rho$ and k based on groups formed by sorted values of $Y$ , and improves minority performance while sacrificing very little average-case performance.

![](images/e6b4796ec9474d077479e5c618e9808cda840c4e2aa16632466cdf23d331285c.jpg)  
(a) Average loss

![](images/637155d844039b2b5291f3d356c77cc36bebf54539b98e53c440aab82e7baf5c.jpg)  
(b) Loss on minority group  
Figure 3. Infinite groups: Figures (a) and (b) plot average and minority group losses under the distribution (14). $\mathrm { \Delta ^ { * } Y S p l i t { ? } }$ is the performance of the model whose $\rho$ and $k$ was chosen based on groups formed by sorted values of $Y$ , and $^ { 6 6 } G = . 5 ^ { 3 }$ chose $k$ and $\rho$ based on auxiliary data with intervention $G = 0 . 5$

Infinite groups For our last scenario, we again generate X and Y following the equation (12), but with

$$
G \sim P _ {G} \text { with   density } p _ {G} (g) \propto (1 - g) ^ {- \frac {1}{3}},\tag{14}
$$

so small values of $G$ again correspond to rare minority subpopulations. To study how k and $\rho$ can be tuned if a small auxiliary dataset is available, we generate a small auxiliary dataset from the distribution (12) with group $G = . 5$ , which we interpret as a particular group intervention; we simulate $n _ { \mathrm { a u x i l i a r y } } = 1 0 0$ observations from $G = . 5$ , which is small compared to $n _ { \mathrm { t r a i n } } = 1 0 0 0$ training examples. We refer to choosing k and $\rho$ with the least prediction error on this auxiliary validation data as the $^ { 6 6 } G = 0 . 5 ^ { 3 }$ method.

As earlier, we plot in Figure $\mathrm { 3 ( a ) }$ and (b) the average and minority group $( G = 0 )$ losses for the diferent methods. The minority group $G = 0$ now never appears in the training set, and small values of $G$ are rare under the distribution (14). Our first heuristic $\mathrm { \Delta ^ { 6 6 } Y S p l i t { ? } }$ chooses a model that balance average and minority performance, although it is somewhat conservative. Our second proposal, the $G = 0 . 5$ method, achieves good performance on the rare minority group while sacrificing little average performance, despite the fact that the auxiliary data was collected from the group $G = 0 . 5$ that is far from the minority group $G = 0$

## 3.2 Domain generalization for classification and digit recognition

![](images/1e956dbe7aab31e07fdb7cb1c43f01ce712b5716c4cc4001a79e911fdcece1e0.jpg)  
(a) MNIST hand-written Digits

![](images/53023c6180d9c11e3e1ca09bd050c29a80228e09d606028f448332a6b5360e2e.jpg)  
(b) All type-written Digits

![](images/b3f3a26331483f21e38019f61c885c8ec3df67d1c907e31e4aaebfdca0727926.jpg)  
(c) Type-written Digit 3 (easy class)

![](images/6998126b5dd84551605982d88776d355a51655991fd7e77ec4051642c5697511.jpg)  
(d) Type-written Digit 9 (hard class)  
Figure 4. (a) Test error on the hand-written digits (MNIST test dataset). (b)–(d) Test errors on type-written digits. Models were trained on data consisting of MNIST hand-written digits with 0–10% replaced by type-written digits. The horizontal axis of each plot denotes percentage of type-written digits (relative to handwritten) in training. Each of the six lines represents a diferent value of ρ used in training, where $\rho = 0$ corresponds to empirical risk minimization (ERM). (b) Classification error on entire test set of type-written digits. (c) Classification error on digit 3 of the type-written digits. (d) Classification errors for digit 9 of the type-written digits.

In this first of our real experiments, we consider a multi-class digit classification example, investigating domain generalization, though we conflate this with item 3 (multiple subpopulations). We construct our training set as a mixture of MNIST hand-written digits [34] (majority population) and type-written digits consisting of diferent fonts [32] (minority population). We fix the number of training examples, and vary the minority proportions of type-written digits from 0–10% of the training data. In the MNIST hand-written training dataset comprising of $n _ { \mathrm { t r a i n } } = 6 0 , 0 0 0$ digits, we replace $n \in \{ 0 , 6 , 1 0 , 6 0 , 1 0 0 , 6 0 0 \}$ images per digit by randomly drawn digits from the type-written dataset (with the same label).

<table><tr><td rowspan="2">Minority proportion</td><td colspan="2">All Digits</td><td colspan="2">Digit 9 (hard)</td><td colspan="2">Digit 6 (hard)</td><td colspan="2">Digit 3 (easy)</td></tr><tr><td>ERM</td><td> $\rho = 50$ </td><td>ERM</td><td> $\rho = 50$ </td><td>ERM</td><td> $\rho = 50$ </td><td>ERM</td><td> $\rho = 50$ </td></tr><tr><td>0</td><td>17.35</td><td>16.78</td><td>30.12</td><td>25.98</td><td>35.63</td><td>38.39</td><td>6.69</td><td>6.69</td></tr><tr><td>0.1</td><td>12.14</td><td>10.4</td><td>21.95</td><td>17.03</td><td>21.06</td><td>14.27</td><td>6.89</td><td>6.99</td></tr><tr><td>0.17</td><td>11.05</td><td>9.48</td><td>19</td><td>10.83</td><td>19.69</td><td>12.8</td><td>6.89</td><td>7.19</td></tr><tr><td>1</td><td>6.01</td><td>5.18</td><td>10.73</td><td>5.81</td><td>7.97</td><td>7.97</td><td>4.92</td><td>3.54</td></tr><tr><td>1.67</td><td>5.07</td><td>3.82</td><td>9.35</td><td>4.13</td><td>6.59</td><td>5.91</td><td>4.63</td><td>3.54</td></tr><tr><td>10</td><td>2.1</td><td>0.61</td><td>3.44</td><td>0.59</td><td>1.77</td><td>0.39</td><td>2.66</td><td>0.69</td></tr></table>

Table 1: Test error on type-written digits (%)

Our classifiers have no knowledge of whether an image is hand-written or type-written, and our goal is to learn models that perform uniformly well across both majority (hand-written) and minority (type-written) subpopulations. We compare our procedure (2) with k = 2 against the ERM solution ${ \widehat { \theta } } _ { n } ^ { \mathrm { e r m } }$ , where we vary $\rho$ and the latent minority proportion. We evaluate our classifiers on both hand- and type-written digits on held-out test sets.

For $y \in \{ 0 , \ldots , 9 \}$ and x $\mathbf { \mu } \in \mathbb { R } ^ { d }$ , we use the multi-class logistic loss $\begin{array} { r } { \ell ( \theta ; ( x , y ) ) = \log ( \sum _ { i = 0 } ^ { k } \exp ( ( \theta _ { i } - } \end{array}$ $\theta _ { y } ) ^ { \top } x ) )$ , where $\theta _ { i } \in \mathbb { R } ^ { d }$ . For our feature vector X, we use the d = 4509-dimensional output of the final fully connected layer of LeNet [66] after $1 0 ^ { 4 }$ stochastic gradient steps on the training dataset (see [56] for detailed hyper-parameter settings). We constrain our parameter matrix $[ \theta _ { 0 } , \ldots , \theta _ { 9 } ]$ to lie in the Frobenius norm ball of radius $r = 5$ , chosen by cross validation on ERM $( \rho = 0 )$

Returning to the justification for our development, we expect our robust models to exhibit better performance on rare and dificult test data when compared against ERM models. This prediction is mostly consistent with our observations, though the efects are not always strong. We suspect this is because the test data we construct is diferent from the worst-case scenario; the procedure (2) can be conservative as it guarantees uniform performance by optimizing the worstcase performance. In Figure 4, we plot the classification errors over the minority proportion as we vary $\rho$ (so that $\rho = 0$ corresponds to ERM), summarizing the classification errors in Table 1. In Figure 4(a), we observe virtually the same performance on the hand-written test set (majority) across diferent radii $\rho$ (error below 1%, with a decrease in accuracy of at most .1–.2%). On a test set of all typed digits (Figure 4(b)), the robust solutions exhibit a 1–2% improvement over the non-robust (ERM) solution in each mixture of typewritten digits (minority proportions) into the training data, which is larger than the persistent .1–.2% degradation on handwritten recognition. The trend of robust improvements on typewritten digits is more pronounced on the harder classes: the gap between ${ \widehat { \theta } } _ { n } ^ { \mathrm { { e r m } } }$ and $\widehat { \theta } _ { n }$ widens up to 9% on the digit 9 (see Table 1 and Fig. 4(d)). We observe that $\widehat { \theta } _ { n }$ consistently performs well on the latent minority (type-written) subpopulation by virtue of upweighting the hard instances in the training set.

## 3.3 Tail performance in a regression problem

We consider a linear regression problem using the communities and crime dataset [77, 9], studying the performance of distributionally robust methods on tail losses. Given a 122-dimensional attribute vector X describing a community, the goal is to predict per capita violent crimes Y (see [77]). We use the absolute loss $\ell ( \theta ; ( x , y ) ) = | \theta ^ { \top } x - y |$ and compare method (2) with constrained forms of lasso, ridge, and elastic net regularization [108], taking constraints of the form

![](images/2529ac34359633546381c85e19db69b97b64f323568b298b91971bdf3328245a.jpg)  
(a) Median training loss

![](images/4801fc935d64e59bbe6b6f366c9cff628ae5c80ea9a7739d917ae39acafeb9d7.jpg)  
(b) Median test loss

![](images/cce8419d57bb5da8a53190476688f62bb9f079ab5336ca748d4f7d71c0f92ecc.jpg)  
(c) Maximal training loss

![](images/e5c6169b1bffc4af488c07ea503493a49e8ff9855450da05eb229928c2cd0d4a.jpg)  
(d) Maximal test loss  
Figure 5. Median and maximal loss $| Y - Z ^ { \top } \theta |$ evaluated on training and test datasets. Values of the x-axis corresponds to diferent indices for the values of $\rho$ and $r ,$ so that $^ { * } x { \mathrm { - a x i s } } = 1 ^ { * }$ for the \` -constrained problem corresponds to $r = 5$ , and for the distributionally robust method (2) it corresponds to $\rho = . 0 0 1$ . Error bars correspond to standard error.

$$
\Theta = \left\{\theta \in \mathbb {R} ^ {d}: a _ {1} \| \theta \| _ {1} + a _ {2} \| \theta \| _ {2} \leq r \right\}.
$$

We vary $a _ { 1 } , \ a _ { 2 }$ , and $r \colon$ for \`<sub>1</sub>-constraints we take $a _ { 1 } = 1 , a _ { 2 } = 0$ and vary $r _ { 1 } \in \{ . 0 5 , . 1 , . 5 , 1 , 5 \}$ ; for \` -constraints we take $a _ { 1 } = 0 , a _ { 2 } = 1$ and vary $r _ { 2 } \in \{ . 5 , 1 , 5 , 1 0 , 5 0 \}$ ; for elastic net we take $a _ { 1 } = 1 , a _ { 2 } = 1 0$ and set $r = r _ { 1 } + r _ { 2 }$ . We compare these regularizers with the distributionally robust procedure (2) with $k = 2$ , and the same procedure coupled with the \` -constraint $( a _ { 1 } = 1 , a _ { 2 } = 0 )$ with $r = . 0 5$ , where we vary $\rho \in \{ . 0 0 1 , . 0 1 , . 1 , 1 , 1 0 \}$

In Figure 5, we plot the quantiles of the training and test losses with respect to diferent values of regularization or $\rho .$ The horizontal axis in each figure indexes our choice of regularization value. We observe that $\widehat { \theta } _ { n }$ shows very diferent behavior than other regularizers; $\widehat { \theta } _ { n }$ attains median losses similar or slightly higher than the regularized ERM solutions, and achieves much smaller loss on the tails of the inputs. As $\rho$ grows, the robust solution exhibits increasing median loss— though slowly—and decreasing maximal loss. To validate our experiments, we made 50 independent random partitions of our dataset with $n = 2 1 1 8$ samples. For each random partition, we divide the dataset into training set with $n _ { \mathrm { t r a i n } } = 1 8 0 0$ and a test set with $n _ { \mathrm { t e s t } } = 3 1 8$

![](images/fbed3c86eeb8cc4cbc0c76c6d61df442ab7ef59e05ef3e274df1fa647d8302e2.jpg)  
(a) Overall top-5 accuracy

![](images/f5860600e888c8d6fca452247f7ef6e0d947f4c2d760e15ae105a184959d1038.jpg)  
(b) Standard deviation of top-5 accuracy

![](images/b77b88fed1360912bde87ee7a89386ba326960501dbdcdcc774a32ab43f8f3c8.jpg)  
(c) Test top-5 on worst c classes

![](images/168466a00a58af611162baf555a2ae748a07ee4a6ee88ab69538e917695073b1.jpg)  
(d) Test top-5 accuracy on worst ERM classes  
Figure 6. (a) Top-5 error against $\rho$ on train and test. (b) Standard deviation of top-5 accuracy across 120 diferent classes against ρ. (c) Test top-5 accuracy on the worst-c classes under each model, i.e. c classes with lowest accuracy under each model. (d) Test top-5 accuracy on the worst-c classes ordered by accuracy of ERM model $( \rho = 0 )$ .

## 3.4 Fine-grained recognition and challenging sub-groups

Finally, we consider the fine-grained recognition task of the Stanford Dogs dataset [58], where the goal is to classify an image of a dog into one of 120 diferent breeds. There are 20,580 images, $n _ { \mathrm { t r a i n } } = 1 2 { , } 0 0 0$ training examples, with 100 training examples for each class. We use the default histogram of SIFT features in the dataset [101], resulting in vectors $\boldsymbol { x } \in \mathbb { R } ^ { d }$ with $d = 1 2 , 0 0 0$

We train 120 one-versus-rest classifiers, one each class, and combine their predictions by taking the k predictions with largest scores for a given example x. For each binary classification problem, we use the binary logistic loss, regularized with lasso (in constrained form) so that $\Theta _ { \mathrm { o n e - v s - r e s t } } =$ $\left. \theta \in \mathbb { R } ^ { d } : \left\| \theta \right\| _ { 1 } \leq r \right.$ . Thus, for each class i, we represent a pair $( x , y )$ by $y = 1$ if x is of breed $i ,$ and −1 otherwise, fitting a binary classifier $\theta _ { i }$ for each class. We use $r = 1 . 0$ for all of our methods based on cross-validation for ERM $( \rho = 0 )$ . As we predict using the m highest scores, we measure performance with respect to top-m accuracy, which counts the number of test examples in which the true label was among these m predictions. As $\rho$ grows larger, we expect better performance on challenging classes, sacrificing performance on easier classes, and due to uniform performance, for the variance in the class-wise accuracies to be smaller, though we do not necessarily expect that average accuracies should improve as $\rho$ increases.

In Figure 6, we present top-5 accuracies; top-1 and top-3 accuracies are similar. Overall accuracy improves moderately as $\rho$ grows (Figure 6(a)), and the standard deviation of the top-5 accuracy across the classes decreases as $\rho$ increases (Figure 6(b)), consistent with our hypothesis that the robust formulations should yield more uniform performance across diferent subpopulations. In Figure $6 ( \mathrm { c ) }$ , we plot the accuracy averaged over c-classes that sufer the lowest accuracy under each model, varying c on the horizontal axis; the accuracy at $c = 1 2 0$ is simply the average top-5 accuracy of the models. For c small, meaning for classes on which the respective models perform most poorly, we observe that the ensemble of one-vs-rest ${ \widehat { \theta } } _ { n } \mathrm { { ' s } }$ outperform the ensemble of ERM solutions ${ \widehat { \theta } } _ { n } ^ { \mathrm { e r m } } \mathrm { s }$ . In Figure $6 ( \mathrm { d } )$ , we plot the accuracy averaged over the first c-classes that have the lowest accuracy under the ERM model. We see that robust solutions $\widehat { \theta } _ { n }$ improve performance on classes that ERM does poorly on; such tail-performance improves monotonically with $\rho$ up to $\rho = 1 0 ;$ we conjecture the degradation for higher $\rho$ is a consequence of overly conservative estimates. Figure $6 ( \mathrm { c ) }$ shows that the gap between the robust classifier performance and non-robust classifier goes from .17 vs. .03 (hardest class accuracy) to .38 vs. .28 (overall accuracy), so that relative performance gains of the robust approach seem largest on the hardest classes. Although it is hard to draw conclusions from this experiment due to improved overall performance when increasing $\rho ,$ we conjecture that is due to the regularization efect for relatively small values of $\rho$ described b many previous authors [47, 62, 36, 64, 72].

## 4 Convergence Guarantees

Our empirical experiments in the previous section evidence the potential statistical benefits of the distributionally robust estimator (2). As a consequence, we view it as important to develop some of its theoretical properties, so we investigate its performance under a variety of conditions on the f-divergence, providing finite sample convergence guarantees for f-divergences with $f ( t ) \asymp t ^ { k }$ with $k \in ( 1 , \infty )$ . Recalling the definition (7) of worst-case risk $\mathcal { R } _ { k } ( \theta ; P _ { 0 } )$ for the Cressie-Read divergences (6), we show that the empirical minimizer $\widehat { \theta } _ { n }$ for the plug-in (2) satisfies $\mathcal { R } _ { f } ( \widehat { \theta } _ { n } ; P _ { 0 } ) \ : -$ $\begin{array} { r } { \operatorname* { i n f } _ { \theta \in \Theta } \mathcal { R } _ { f } ( \theta ; P _ { 0 } ) \le C n ^ { - \frac { 1 } { k _ { * } \vee 2 } } } \end{array}$ with high probability, where $\begin{array} { r } { k _ { * } = \frac { k } { k - 1 } } \end{array}$ and C is a problem dependent constant. As we show in Section 5, the $n ^ { - 1 / ( k _ { * } \vee 2 ) }$ rate is optimal in n. The departure from parametric rates as the uncertainty set becomes large, meaning $k \downarrow 1$ or $\begin{array} { r } { k _ { * } ~ = ~ \frac { k } { k - 1 } ~ { \uparrow } ~ \infty } \end{array}$ , is a consequence of the fact that in the worst case, it is challenging to estimate L<sup>k∗</sup>-norms of random variables X for $k _ { * } > 2 ;$ that is, the minimax rate for such estimation is $n ^ { - 1 / k _ { * } }$ for $k _ { * } > 2$

Throughout this section, we assume that for any $\theta \in \Theta$ and $x \in \mathcal { X }$ , we have $\ell ( \theta ; x ) \in [ 0 , M ]$ for some $M \geq 1$ , and restrict attention to the Cressie-Read family of divergences (6) with $k \in ( 1 , \infty )$ We first show pointwise concentration of the finite sample objective $\textstyle \mathcal { R } _ { k } ( \theta ; \widehat { P } _ { n } )$ to its population counterpart $\mathcal { R } _ { k } ( \theta ; P _ { 0 } ) $ we use convex concentration inequalities [23, 95] to show concentration of $\mathcal { R } _ { k } ( \theta ; \widehat { P } _ { n } )$ to $\mathbb { E } [ \mathcal { R } _ { k } ( \theta ; \widehat { P } _ { n } ) ]$ , and then carefully bound the bias of $\mathbb { E } [ \mathcal { R } _ { k } ( \theta ; \widehat { P } _ { n } ) ]$ in estimating the population risk $\mathcal { R } _ { k } ( \theta ; P _ { 0 } )$

Theorem 2. Assume that $\ell ( \theta ; x ) \in [ 0 , M ]$ for all $\theta \in \Theta$ and $x \in \mathcal { X } .$ , and define $c _ { k } ( \rho ) : = ( k ( k -$ $1 ) \rho + 1 ) ^ { 1 / k }$ . For a fixed $\theta \in \Theta$ and $t > 0$ , whenever $n \geq k \vee 3$ , with probability at least $1 - 2 e ^ { - t }$

$$
\left| \mathcal {R} _ {k} (\theta ; \widehat {P} _ {n}) - \mathcal {R} _ {k} (\theta ; P _ {0}) \right| \leq 1 0 n ^ {- \frac {1}{k _ {*} \vee 2}} c _ {k} (\rho) ^ {2} M \left(\frac {c _ {k} (\rho)}{c _ {k} (\rho) - 1} \vee 2\right) \left(\frac {1}{k} + \sqrt {t + 2 \log n}\right).
$$

See Section C.1 for the proof. Relaxing the boundedness assumption $\ell ( \theta ; x ) \ \in \ [ 0 , M ]$ to sub-Gaussian or sub-exponential tails, or providing similar finite-sample guarantees for general $f -$ divergences are topics of future research.

Given the pointwise concentration result (Theorem 2), we can use a simple covering argument to obtain its uniform counterpart. Our uniform guarantees rely on covering numbers for the model class $\left\{ \ell ( \theta ; \cdot ) : \theta \in \Theta \right\} ( \mathrm { e . g . ~ } [ 1 0 3 ] )$ . A collection $v _ { 1 } , \ldots , v _ { N }$ is an -cover of a set $V$ in norm $\lVert \cdot \rVert$ if for each $v \in \mathcal V$ , there exists $v _ { i }$ such that $\lVert \boldsymbol { v } - \boldsymbol { v } _ { i } \rVert \leq \epsilon$ . The covering number is

$N ( V , \epsilon , \lVert \cdot \rVert ) : = \operatorname* { i n f } \left\{ N \in \mathbb { N } \right|$ there is an -cover of V with respect to $\| \cdot \| \}$

For $\mathcal { F } : = \{ \ell ( \theta , \cdot ) : \theta \in \Theta \}$ equipped with sup-norm $\| h \| _ { L ^ { \infty } ( \mathcal { X } ) } : = \operatorname* { s u p } _ { x \in \mathcal { X } } | h ( x ) |$ , a covering argument gives a uniform concentration result, where we use

$$
\epsilon_ {t, n, k} (\rho) := n ^ {- \frac {1}{k _ {*} \vee 2}} c _ {k} (\rho) ^ {2} \left(\frac {c _ {k} (\rho)}{c _ {k} - 1} \vee 2\right) \left(\frac {1}{k} + \sqrt {t + 2 \log n}\right).
$$

Corollary 1. Let $\ell ( \theta ; x ) \in [ 0 , M ]$ for all $\theta \in \Theta$ and $x \in \mathcal { X }$ . Then for any $t > 0$ , whenever $n \geq k \vee 3 .$ with probability at least $\begin{array} { r } { 1 - 2 N ( \mathcal { F } , \frac { \epsilon _ { t , n , k } ( \rho ) } { 3 } , \| \cdot \| _ { L ^ { \infty } ( \mathcal { X } ) } ) e ^ { - t } } \end{array}$

$$
\sup _ {\theta \in \Theta} \left| \mathcal {R} _ {k} (\theta ; \widehat {P} _ {n}) - \mathcal {R} _ {k} (\theta ; P _ {0}) \right| \leq 3 0 M \epsilon_ {t, n, k} (\rho).
$$

See Section C.2 for the proof. From Corollary 1, we immediately get below.

Corollary 2. Let $\ell ( \theta ; x ) \in [ 0 , M ]$ for all $\theta \in \Theta$ and $x \in \mathcal { X }$ . Then for any $t > 0$ , whenever $n \geq k \vee 3$ with probability at least $\begin{array} { r } { 1 - 2 N ( \mathcal { F } , \frac { \epsilon _ { t , n } } { 3 } , \| \cdot \| _ { L ^ { \infty } ( \mathcal { X } ) } ) e ^ { - t } } \end{array}$

$$
\mathcal {R} _ {k} (\widehat {\theta} _ {n}; P _ {0}) \leq \inf _ {\theta \in \Theta} \mathcal {R} _ {k} (\theta ; P _ {0}) + 6 0 n ^ {- \frac {1}{k _ {*} \vee 2}} c _ {k} ^ {2} M \left(\frac {c _ {k}}{c _ {k} - 1} \vee 2\right) \left(\frac {1}{k} + \sqrt {t + 2 \log n}\right).
$$

As an example, let $\theta \mapsto \ell ( \theta ; x )$ be L-Lipschitz for all $x \in \mathcal { X }$ , with respect to some norm $\lVert \cdot \rVert$ on Θ. Assuming $D : = \mathrm { s u p } _ { \theta , \theta ^ { \prime } \in \Theta } \| \theta - \theta ^ { \prime } \| < \infty$ , a standard bound [103, Chapter 2.7.4] is

$$
N \left(\mathcal {F}, \epsilon , \| \cdot \| _ {L ^ {\infty} (\mathcal {X})}\right) \leq N \left(\Theta , \frac {\epsilon}{L}, \| \cdot \|\right) \leq \left(1 + \frac {D L}{\epsilon}\right) ^ {d}.
$$

If there exists $\theta _ { 0 } \in \Theta$ and $M _ { 0 } > 0$ such that $| \ell ( \theta _ { 0 } ; x ) | \le M _ { 0 }$ for all $x \in \mathcal { X }$ , we have $| \ell ( \theta ; X ) | \leq$ $L D + M _ { 0 }$ , and Corollary 2 implies that

$$
\mathcal {R} _ {k} (\widehat {\theta} _ {n}; P _ {0}) \leq \inf _ {\theta \in \Theta} \mathcal {R} _ {k} (\theta ; P _ {0}) + 6 0 n ^ {- \frac {1}{k _ {*} \vee 2}} c _ {k} ^ {2} (L D + M _ {0}) \left(\frac {c _ {k}}{c _ {k} - 1} \vee 2\right) \left(\frac {1}{k} + \sqrt {t + 2 d \log (2 n)}\right)
$$

with probability at least $1 - 2 \exp ( - t )$ . Replacing covering numbers in the above guarantees with Rademacher averages or their localized variants [11] and leveraging Rademacher contraction inequalities [67] remain open.

## 5 Lower Bounds

To complement our uniform upper bounds, we provide minimax lower bounds showing they are rate optimal, though developing optimal dimension-dependent bounds remains open. For a collection $\mathcal { P }$ of distributions and f-divergence $f ,$ , we define the minimax risk

$$
\mathfrak {M} _ {n} (\mathcal {P}, f, \ell) := \inf _ {\widehat {\theta} _ {n}} \sup _ {P _ {0} \in \mathcal {P}} \mathbb {E} _ {P _ {0} ^ {n}} \left[ \mathcal {R} _ {f} \left(\widehat {\theta} _ {n} (X _ {1} ^ {n}); P _ {0}\right) - \inf _ {\theta \in \Theta} \mathcal {R} _ {f} \left(\theta ; P _ {0}\right) \right]\tag{15}
$$

where the outer infimum is over all $( X _ { 1 } , \ldots , X _ { n } )$ -measurable functions and the inner supremum is over probability measures in ${ \mathcal { P } } _ { : }$ , where the loss is implicit in the risk $\mathcal { R } _ { f }$ . Whenever $f ( t ) \lesssim t ^ { k }$ as $t \uparrow$ $\infty ,$ we show there exist losses for which $n ^ { - 1 / ( k _ { * } \vee 2 ) }$ is a lower bound on the minimax distributionally robust risk (15) where $k _ { * } = k / ( k - 1 )$ . Thus there is a necessary transition from parametric $\sqrt { n } { - } \mathrm { t y p e }$ rates to $n ^ { 1 / k _ { * } }$ when k is small—that is, when we seek protection against large distributional shifts.

It is of interest both to estimate the value of the risk $\mathcal { R } _ { f }$ —see the literature on risk measures we reference in the introduction—and to minimize it. Consequently, we divide our lower bounds into estimation rates on the value $\mathcal { R } _ { f } ( \theta ; P _ { 0 } )$ and on the actual minimax risk (15) for the optimization problem (1), which build out of these results (Sections 5.1 and 5.2, respectively). Within each section, we initially present our results for the Cressie-Read family (6) with $k \in ( 1 , \infty )$ , allowing explicit constants, then provide lower bounds for general f-divergences using the same techniques. The rough intuition for our approach is as follows: we consider Bernoulli variables $Z \in \{ 0 , M \}$ where the probability that $Z = M$ is small, though this probability has substantial influence on the risk $\mathcal { R } _ { f }$ . This highlights the reason for the potentially slow rates of convergence: one must sometimes observe rarer events to estimate or optimize the risk $\mathcal { R } _ { f }$

## 5.1 Lower bounds on estimation of the robust risk value

For the rest of this subsection, we fix any $\theta \in \Theta .$ , and consider $Z ( x ) : = \ell ( \theta ; x )$ , abusing notation by writing $\begin{array} { r } { \mathcal { R } _ { f } ( Z ) : = \operatorname* { s u p } _ { D _ { f } ( Q \parallel P _ { 0 } ) \le \rho } \mathbb { E } _ { Q } [ Z ] } \end{array}$ and $\mathcal { R } _ { k } ( Z ) : = \mathcal { R } _ { f } ( Z ) \mathrm { ~ i f ~ } f = f _ { k }$ is a Cressie-Read divergence (6). We are interested here in the minimax error for estimating the robust risk $\mathcal { R } _ { f } ( Z )$ itself, rather than any optimization over $\theta$ (justifying our abuse $Z ( x ) = \ell ( \theta ; x ) )$ , studying

$$
\mathfrak {M} _ {n} (\mathcal {P}, f) := \inf _ {\widehat {R}} \sup _ {P _ {0} \in \mathcal {P}} \mathbb {E} _ {P _ {0} ^ {n}} \left| \widehat {R} (Z _ {1} ^ {n}) - \mathcal {R} _ {f} (Z) \right|,\tag{16}
$$

where $Z \sim P _ { 0 }$ and $Z _ { 1 } ^ { n } \stackrel { \mathrm { i i d } } { \sim } P _ { 0 } ,$ , and the outer infimum is over ${ \widehat { R } } : \{ 0 , M \} ^ { n } \to { \mathbb R }$ . Throughout this section, we let $\mathcal { P }$ be the collection of distributions on $Z \in \{ 0 , M \}$ for a fixed $M > 0$

We first establish a lower bound for estimating $\mathcal { R } _ { k } ( Z ) = \mathcal { R } _ { k } ( \theta ; P _ { 0 } )$ under the Cressie-Read family $f _ { k } ~ ( 6 ) ;$ see Section D.1 for the proof. Our proof uses Le Cam’s method [107, 65], by noting that if Z takes two values $z _ { 1 } < z _ { 2 }$ , then $\mathcal { R } _ { k } ( Z ) = z _ { 2 }$ holds if and only if $P _ { 0 }$ places enough mass $z _ { 2 } ;$ we compute the precise threshold at which the worst-case region contains a point mass, quantifying the fundamental dificulty in estimating $\mathcal { R } _ { k } ( Z )$

Theorem 3. Let $\rho > 0$ be arbitrary but fixed. Define $c _ { k } ( \rho ) : = ( 1 + k ( k - 1 ) \rho ) ^ { 1 / k } , p _ { k } : = ( 1 + k ( k - 1$

$1 ) \rho ) ^ { - 1 / ( k - 1 ) }$ , and $\begin{array} { r } { \beta _ { k } = \frac { k ( k - 1 ) \rho } { 2 ( 1 + k ( k - 1 ) \rho ) } } \end{array}$ . Then

$$
\begin{array}{c} \mathfrak {M} _ {n} (\mathcal {P}, f _ {k}) \geq M \max \Bigg \{\frac {1}{8 k _ {*} p _ {k}} \left(\sqrt {\frac {p _ {k} (1 - p _ {k})}{8 n}} \wedge \frac {1}{2} (1 - p _ {k}) \wedge p _ {k}\right), \\ \frac {1}{8} \beta_ {k} ^ {\frac {1}{k}} c _ {k} (\rho) \left(\frac {1}{4 n} \wedge p _ {k} \wedge (1 - (1 - \beta_ {k}) ^ {1 - k _ {*}} p _ {k})\right) ^ {\frac {1}{k _ {*}}} \Bigg \}. \end{array}
$$

For general f-divergences we can provide a similar result, showing that the growth of the function $f$ defining the divergence $D _ { f }$ fundamentally determines worst-case rates of convergence; when $f ( t )$ grows slowly as $t \uparrow \infty$ , the robust formulation (1) is conservative, so rates of convergence are slower. First, we give canonical $\Omega ( n ^ { - 1 / 2 } )$ lower bounds. We assume that $f$ is strictly convex at $t = 1$ , meaning that $f ( \lambda t _ { 0 } + ( 1 - \lambda ) t _ { 1 } ) < \lambda f ( t _ { 0 } ) + ( 1 - \lambda ) f ( t _ { 1 } )$ whenever $t _ { 0 } < 1 < t _ { 1 }$ . To state our results, we define the binary divergence

$$
h _ {f} (q; p) := p f \left(\frac {q}{p}\right) + (1 - p) f \left(\frac {1 - q}{1 - p}\right).
$$

As $f$ is strictly convex at $t = 1$ , for $q \geq p$ the function $q \mapsto h _ { f } ( q ; p )$ is strictly increasing on its domain and continuous, so there exists a unique

$$
q (p) := \sup _ {q \geq p} \{q: h _ {f} (q; p) \leq \rho \}.\tag{17}
$$

(Moreover, $q$ is nondecreasing and concave in p, so it is a.e. diferentiable.) We then have the following $\Omega ( n ^ { - 1 / 2 } )$ lower bound.

Proposition 4. Let $f : ( 0 , \infty ) \to \mathbb { R } \cup \{ + \infty \}$ be strictly convex at $t = 1$ . Assume there exists $p \in ( 0 , 1 )$ such that f is ${ \mathcal { C } } ^ { 1 }$ in a neighborhood $o f \ { \frac { q ( p ) } { p } }$ and $\frac { 1 - q ( p ) } { p }$ . Then for any such $p ,$

$$
\liminf _ {n \to \infty} \sqrt {n} \mathfrak {M} _ {n} (\mathcal {P}, f) \geq M \frac {\sqrt {p (1 - p)}}{8} \frac {- \partial_ {p} h _ {f} (q (p) ; p)}{\partial_ {q} h _ {f} (q (p) ; p)} > 0.
$$

See Section D.2 for the proof. The final ratio is positive, as the (strict) convexity of $f$ and joint convexity of $h _ { f }$ imply $\partial _ { q } h _ { f } ( q ( p ) ; p ) > 0 \in \partial _ { q } h _ { f } ( p ; p )$ and $\partial _ { p } h _ { f } ( q ( p ) ; p ) < 0 \in \partial _ { p } h _ { f } ( q ( p ) ; q ( p ) )$

If the asymptotic growth of $f$ is at most $t ^ { k } { } _ { ; }$ , we can give an $\Omega ( n ^ { - 1 / k _ { * } } )$ lower bound, which we prove in Section D.3. Letting $f ^ { - 1 } ( s ) : = \operatorname* { i n f } \{ t \in [ 0 , 1 ] : f ( t ) \leq s \}$ and $m > 0$ , define

$$
C _ {f, \rho , m} := \frac {m}{\rho} \left(1 \wedge \left(\frac {\rho}{2 m}\right) ^ {- k _ {*}} \left(1 - f ^ {- 1} \left(\frac {\rho}{2}\right)\right) ^ {k _ {*}}\right) ^ {- 1}.\tag{18}
$$

Proposition 5. Let $m > 0$ and $k \in ( 1 , \infty )$ $I f f ( t ) \leq m t ^ { k }$ for $t \geq \{ ( n \vee C _ { f , \rho , m } ) \rho m ^ { - 1 } \} ^ { \frac { 1 } { k } }$ , then

$$
\mathfrak {M} _ {n} (\mathcal {P}, f) \geq \frac {M}{1 6} \left(\frac {\rho}{m}\right) ^ {\frac {1}{k}} \left(\frac {1}{n \vee C _ {f , \rho , m}}\right) ^ {\frac {1}{k _ {*}}}.
$$

## 5.2 Lower bounds on optimization

Our lower bounds on optimization build on those for estimating $\mathcal { R } _ { f }$ . We consider linear losses, which makes the situation closest to the estimation of the risk results in the previous section (as we must still estimate kth norms of random variables), providing analogous lower bounds for optimizing the worst-case objective $\mathscr { R } _ { f } ( \cdot ; P _ { 0 } )$ . Using a standard notion of distance for proving lower bounds in stochastic optimization $[ 2 , 3 5 ]$ , we construct a reduction from distributionally robust optimization to hypothesis testing. Throughout, we let $\mathcal { P }$ be the set of distributions with $x \in [ - 1 , 1 ]$ almost surely. We begin by considering the lower bound for the Cressie-Read family (6) f , whose proof we give in Section D.4.

Theorem 6. Let $\ell ( \theta ; x ) = \theta x$ where $\theta \in \Theta = [ - M , M ]$ . Define $c _ { k } ( \rho ) : = ( 1 + k ( k - 1 ) \rho ) ^ { 1 / k }$ $p _ { k } : = ( 1 + k ( k - 1 ) \rho ) ^ { - 1 / ( k - 1 ) }$ , and $\begin{array} { r } { \beta _ { k } = \frac { k ( k - 1 ) \rho } { 2 ( 1 + k ( k - 1 ) \rho ) } } \end{array}$ . Then

$$
\begin{array}{c} \mathfrak {M} _ {n} (\mathcal {P}, f _ {k}, \ell) \geq M \max \bigg \{\frac {1}{1 6 k _ {*} p _ {k}} \left(\sqrt {\frac {p _ {k} (1 - p _ {k})}{n}} \wedge \frac {1}{2} (1 - p _ {k}) \wedge (1 - 2 p _ {k}) \wedge p _ {k}\right), \\ \frac {1}{1 6} \beta_ {k} ^ {\frac {1}{k}} c _ {k} (\rho) \left(\frac {1}{4 n} \wedge p _ {k} \wedge (1 - p _ {k}) \wedge (1 - (1 - \beta_ {k}) ^ {1 - k _ {*}} p _ {k})\right) ^ {\frac {1}{k _ {*}}} \bigg \}. \end{array}
$$

For general f-divergences, we can show a similar standard $\Omega ( n ^ { - 1 / 2 } )$ lower bound for optimization. We defer the proof of this result to Section D.5.

Proposition 7. Let $\ell ( \theta ; x ) = \theta x$ where $\theta \in \Theta = [ - M , M ]$ and $X \in [ - 1 , 1 ]$ . If the conditions on f of Proposition 4 hold,

$$
\liminf _ {n \to \infty} \sqrt {n} \mathfrak {M} _ {n} (\mathcal {P}, f, \ell) \geq M \frac {\sqrt {p (1 - p)}}{1 6 q (p)} \frac {- \partial_ {p} h _ {f} (q (p) ; p)}{\partial_ {q} h _ {f} (q (p) ; p)} > 0.
$$

For f-divergences with $f ( t ) = O ( t ^ { k } ) \mathrm { ~ a s ~ } t  \infty ,$ , we can again prove a $\Omega ( n ^ { - 1 / k _ { * } } )$ lower bound on optimizing $\mathscr { R } _ { f } ( \cdot ; P _ { 0 } )$ . Recalling the definition (18) of $C _ { f , \rho , m }$ , we obtain the following result, whose proof we give in Section D.6.

Proposition 8. Let $\ell ( \theta ; x ) = \theta ;$ x where $\theta \in \Theta = [ - M , M ]$ and $X \in [ - 1 , 1 ]$ . If the conditions on f of Proposition 5 hold,

$$
\mathfrak {M} _ {n} (\mathcal {P}, f, \ell) \geq \frac {M}{1 6} \left(\frac {\rho}{m}\right) ^ {\frac {1}{k}} \left\{\left(\frac {1}{n \vee C _ {f , \rho , m}}\right) ^ {\frac {1}{k _ {*}}} \wedge \left(\frac {\rho}{2 m}\right) ^ {\frac {1}{k _ {*}}} \left(\left(\frac {2}{3}\right) ^ {k - 1} \wedge \left(\frac {1}{2}\right) ^ {\frac {1}{k _ {*}}} \frac {2 m}{\rho}\right) \right\}.
$$

In terms of rates in $n ,$ there is a tradeof between convergence rates and robustness, as measured by the asymptotic growth of the function f defining the robustness set $\{ P : D _ { f } ( P \| P _ { 0 } ) \le \rho \}$ . In this sense, our finite sample convergence guarantees of Section 4 are sharp. All results in this section can be stated in a probabilistic form that matches our high probability guarantees in the previous section; see the remark in the beginning of Section D.

## 6 Asymptotics

In the previous two sections, we studied convergence properties for the robust formulation (1) that hold uniformly over collections of data generating distributions $P _ { 0 }$ , showing that robustness can incur nontrivial statistical cost. In this section, by contrast, we turn to pointwise asymptotic properties of the empirical plug-in (2), applying to a fixed distribution $P _ { 0 }$ . This allows two contributions. First, we prove a general consistency result for convex losses. Second, while the minimax convergence rates in the previous section exhibit a departure from classical parametric rates, we show that under appropriate regularity conditions the typical $\scriptstyle { \sqrt { n } } - { \mathrm { r a t e s } }$ of convergence and asymptotic normality guarantees are possible.

## 6.1 Consistency

In this section, we give a general set of convergence results, relying on the powerful theory of epiconvergence [79, 59]. Our first results shows that $\mathcal { R } _ { f } ( \theta ; \widehat { P } _ { n } )$ is pointwise consistent for its population counterpart $\mathcal { R } _ { f } ( \theta ; P _ { 0 } )$ . See Section E.1 for the proof.

Proposition 9. Let f be finite on $( t _ { 0 } , \infty )$ for some $t _ { 0 } < 1$ . For any $\theta \in \Theta , \ i f \operatorname { \mathbb { E } } [ f ^ { * } ( | \ell ( \theta ; X ) | ) ] < \infty$ then $\mathscr { R } _ { f } ( \theta ; \widehat { P } _ { n } ) \stackrel { a . s . } { \longrightarrow } \mathscr { R } _ { f } ( \theta ; P _ { 0 } ) < \infty$

We now provide suficient conditions for parameter consistency in the distributionally robust estimation problem (2). The main assumption is that the loss functions are closed and the nonrobust population risk is coercive. (Weaker suficient conditions are possible, but in our view, a bit esoteric.)

Assumption A (Coercivity). For each $x \in \mathcal { X }$ , the function $\theta \mapsto \ell ( \theta ; x )$ is closed and convex, and $\mathbb { E } _ { P _ { 0 } } [ \ell ( \theta ; X ) ] + { \mathbf I } \left( \theta \in \Theta \right)$ is coercive.

It is possible to replace the convexity assumption with a Glivenko-Cantelli property on the collection $\{ f ^ { * } ( \ell ( \theta ; \cdot ) ) \} _ { \theta \in \Theta } ;$ for example, if $\theta \mapsto \ell ( \theta ; X )$ is continuous and Θ is compact, then a similar consistency result holds, though computation of the plug-in (2) may be dificult. Coercivity guarantees the existence and compactness of the set of optima for $\mathcal { R } _ { f } ( \theta ; P _ { 0 } )$ .

Define the inclusion distance, or the deviation, from a set A to B as

$$
d _ {\subset} (A, B) := \sup _ {y \in A} \operatorname{dist} (y, B) = \inf _ {\epsilon} \left\{\epsilon \geq 0: A \subset \left\{y: \operatorname{dist} (y, B) \leq \epsilon \right\} \right\}.
$$

This is an one-sided notion of the Hausdorf distance $d _ { H } ( A , B ) = \operatorname* { m a x } \{ d _ { \subset } ( A , B ) , d _ { \subset } ( B , A ) \}$ . For any $\varepsilon \geq 0$ and distribution $P ,$ , define the set of ε-approximate minimizers

$$
S _ {P} (\Theta , \varepsilon) := \left\{\theta \in \Theta \mid \mathcal {R} _ {f} (\theta ; P) \leq \inf _ {\theta \in \Theta} \mathcal {R} _ {f} (\theta ; P) + \varepsilon \right\},
$$

where we let $S _ { P } ( \Theta ) = S _ { P } ( \Theta , 0 )$ for shorthand. The following consistency result shows that approximate empirical optimizers are eventually nearly in the population optima $S _ { P _ { 0 } } ( \Theta )$ ; we provide its proof in Section E.2.

Proposition 10. Let f be finite on $( t _ { 0 } , \infty )$ for some $t _ { 0 } < 1$ , and assume $\mathbb { E } [ f ^ { * } ( | \ell ( \theta ; X ) | ) ] < \infty$ on a neighborhood of $S _ { P _ { 0 } } ( \Theta )$ . Under Assumption A,

$$
\inf _ {\theta \in \Theta} \mathcal {R} _ {f} (\theta ; \widehat {P} _ {n}) \stackrel {{a. s.}} {{\to}} \inf _ {\theta \in \Theta} \mathcal {R} _ {f} (\theta ; P _ {0}),
$$

and for any sequence $\varepsilon _ { n } \downarrow 0 ,$ with probability 1 we have $S _ { \widehat { P } _ { n } } ( \Theta , \varepsilon _ { n } ) \not = \emptyset$ eventually and $d _ { \mathsf { C } } \left( S _ { \widehat { P } _ { n } } ( \Theta , \varepsilon _ { n } ) , S _ { P _ { 0 } } ( \Theta ) \right) \to$ 0.

## 6.2 Asymptotic normality

The worst-case minimax results are sometimes pessimistic, so we provide a central limit result for the empirical optimizer $\widehat { \theta } _ { n } \in \mathrm { a r g m i n } _ { \theta \in \mathbb { R } ^ { d } } \mathcal { R } ( \theta ; \widehat { P } _ { n } )$ to the population optimizer $\begin{array} { r } { \theta ^ { \star } = \operatorname * { a r g m i n } _ { \theta \in \mathbb { R } ^ { d } } \mathcal { R } ( \theta ; \widehat { P } _ { n } ) } \end{array}$ under appropriate smoothness conditions on the risk. Given that in the general formulation of our problem, the supremum over distributions P near $P _ { 0 }$ act as nuisance parameters, it seems challenging to give the most generic conditions under which asymptotic normality of $\widehat { \theta } _ { n }$ should hold. Accordingly, we assume simpler conditions that allow an essentially classical treatment with a brief proof, based on the dual formulation (4).

Throughout this section, we assume that the population optimizer $\begin{array} { r } { \theta ^ { \star } = \operatorname * { a r g m i n } _ { \theta \in \mathbb { R } ^ { d } } \mathcal { R } ( \theta ; \widehat { P } _ { n } ) } \end{array}$ is unique. We begin with a smoothness assumption.

Assumption B (Smoothness and growth). For some $k > 1$ , the function f satisfies lim in $\mathrm { f } _ { t \to \infty } f ( t ) / t ^ { k } >$ 0. There exists a neighborhood U of $\theta ^ { \star } \ s . t$

1. There exists $L : \mathcal { X } \to \mathbb { R } _ { + }$ such that $| \ell ( \theta _ { 0 } ; x ) - \ell ( \theta _ { 1 } ; x ) | \leq L ( x ) \left\| \theta _ { 0 } - \theta _ { 1 } \right\| _ { 2 }$ for all $\theta _ { i } \in U$ , where $\mathbb { E } [ L ( X ) ^ { 2 k _ { * } } ] < \infty$ (we again use $\begin{array} { r } { k _ { * } = \frac { k } { k - 1 } ) } \end{array}$

2. E $[ | \ell ( \theta ^ { \star } ; X ) | ^ { 2 k _ { * } } ] < \infty$ , and the function $\theta \mapsto \ell ( \theta ; x )$ is diferentiable on U.

Recalling the dual (4), for shorthand define

$$
g _ {P} (\theta , \lambda , \eta) := \lambda \mathbb {E} _ {P} \left[ f ^ {*} \left(\frac {\ell (\theta ; X) - \eta}{\lambda}\right) \right] + \rho \lambda + \eta .
$$

Assumption C (Strong identifiability). The objective $g _ { P _ { 0 } }$ is $\mathcal { C } ^ { 2 }$ near $( \theta ^ { \star } , \lambda ^ { \star } , \eta ^ { \star } ) = \operatorname * { a r g m i n } g _ { P _ { 0 } } ( \theta , \lambda , \eta )$ with positive definite Hessian, and $P _ { 0 } ( \ell ( \theta ^ { \star } ; X ) - \eta ^ { \star } > 0 ) > 0$

The second condition of Assumption C guarantees $\lambda ^ { \star } > 0$ . For Cressie-Read divergences (6), a suficient condition for uniqueness of $( \eta ^ { \star } , \lambda ^ { \star } )$ follows.

Lemma 2. Let f be the Cressie-Read divergence (6) with parameter $k \in ( 1 , \infty )$ , and $\theta _ { 0 } \in \Theta$ . If $\ell ( \theta _ { 0 } ; X )$ is non-constant under P and $\mathbb { E } _ { P } [ | \ell ( \theta ; X ) | ^ { k _ { * } } ] < \infty$ near $\theta _ { 0 }$ , then $\begin{array} { r } { ( \lambda _ { 0 } , \eta _ { 0 } ) = \mathrm { a r g m i n } _ { \lambda \ge 0 , \eta } g _ { P _ { 0 } } ( \theta _ { 0 } , \lambda , \eta ) } \end{array}$ is unique.

See Appendix F.1 for a proof. Suficient conditions for diferentiability are similar to the classical conditions for asymptotic normality of quantile estimators [102]; for example, if $\ell ( \cdot ; X )$ is $\mathcal { C } ^ { 2 }$ near some $\theta _ { 0 }$ and $P ( \ell ( \theta ; X ) = \eta ) = 0$ for $\theta , \eta$ near $\theta _ { 0 } , \eta _ { 0 }$ , then the dual formulation $g _ { P _ { 0 } }$ is $\mathcal { C } ^ { 2 }$ in a neighborhood of $( \theta _ { 0 } , \eta _ { 0 } , \lambda _ { 0 } )$ whenever $\lambda _ { 0 } ~ > ~ 0$ . With this brief discussion, we now provide an asymptotic normality result.

Theorem 11. Let Assumptions B and C hold. Let $\widehat { \theta } _ { n }$ be any sequence of approximate optimizers to the empirical plug-in satisfying $\textstyle \mathcal { R } _ { f } ( \widehat { \theta } _ { n } ; \widehat { P } _ { n } ) \leq \operatorname* { i n f } _ { \theta } \mathcal { R } _ { f } ( \theta ; \widehat { P } _ { n } ) + o _ { P } ( 1 / n )$ . Then

$$
\sqrt {n} \left(\widehat {\theta} _ {n} - \theta^ {\star}\right) \stackrel {{d}} {{\rightsquigarrow}} \mathsf {N} \left(0, V \operatorname{Cov} \left(f ^ {* \prime} \left(\frac {\ell (\theta^ {\star} ; X) - \eta^ {\star}}{\lambda^ {\star}}\right) \nabla \ell (\theta^ {\star}; X)\right) V\right)\tag{19}
$$

where V is the first d-by-d block of $\left( \nabla ^ { 2 } g _ { P _ { 0 } } ( \theta ^ { \star } , \lambda ^ { \star } , \eta ^ { \star } ) \right) ^ { - 1 } \in \mathbb { R } ^ { ( d + 2 ) \times ( d + 2 ) }$

See Section F.2 for the proof. Under the same assumptions, it is straightforward to see that plug-in estimators for V and $\operatorname { \dot { C } o v } ( f ^ { * \prime } ( \frac { \ell ( \theta ^ { \star } ; X ) - \eta ^ { \star } } { \lambda ^ { \star } } ) \nabla \ell ( \theta ^ { \star } ; X ) )$ are consistent. Combining these estimators with Theorem 11 gives an asymptotically pivotal confidence region for $\theta ^ { \star }$ by Slutsky’s lemmas.

We can relax the assumption that $\nabla ^ { 2 } g _ { P _ { 0 } } ( \theta ^ { \star } , \lambda ^ { \star } , \eta ^ { \star } ) \succ 0$ in Assumption C to positive definiteness of the Hessian of the map $( \eta , \theta ) \mapsto c _ { k } ( \mathbb { E } _ { P _ { 0 } } [ ( \ell ( \theta ; X ) - \eta ) _ { + } ^ { k _ { * } } ] ) ^ { \frac { 1 } { k _ { * } } } + \eta$ at $( \theta ^ { \star } , \eta ^ { \star } )$ , which is the dual objective $g _ { k }$ with λ minimized out. We omit the proof with this relaxed condition for brevity, as it is quite involved. Letting $B = ( \ell ( { \theta } ^ { \star } ; X ) - { \eta } ^ { \star } ) _ { + }$ , under Assumption B and the randomness conditions of Lemma 2, this relaxed condition holds if

$$
\begin{array}{c} (k - 1) \mathbb {E} B ^ {k _ {*} - 2} \left(\mathbb {E} B ^ {k _ {*}} \mathbb {E} B ^ {k _ {*} - 2} - (\mathbb {E} B ^ {k _ {*} - 1}) ^ {2}\right) \mathbb {E} [ B ^ {k _ {*} - 1} \nabla^ {2} \ell (\theta^ {\star}; X) ] \\ - \left(\mathbb {E} B ^ {k _ {*} - 1}\right) ^ {2} \mathbb {E} [ B ^ {k _ {*} - 2} \nabla \ell (\theta^ {\star}; X) ] \mathbb {E} [ B ^ {k _ {*} - 2} \nabla \ell (\theta^ {\star}; X) ] ^ {\top} \succ 0, \end{array}\tag{20}
$$

and $k \in ( 1 , 2 )$ . For $k = 2 .$ , the relaxed condition holds if in addition to the bound (20), there is a neighborhood of $( \theta ^ { \star } , \eta ^ { \star } )$ such that $\mathbb { P } ( \ell ( \theta ; X ) = \eta ) = 0$ . Assumption C also requires identifiability of nuisance variables $\lambda ^ { \star } , \eta ^ { \star }$ . Whether directly analyzing the primal formulation (1)—rather than our proof via the dual (4)—can relax this assumption remains open.

## 7 Discussion and further work

We have presented a collection of statistical problems that arise out of a distributionally robust formulation of M-estimation, whose purpose is to obtain uniformly small loss and protect against rare but large losses. While our results give convergence guarantees, and our experimental results suggest the potential of these approaches in a number of prediction problems, numerous questions remain.

In our view, the most important limitation is guidance in the choices of the robustness set, that is, $\{ Q : D _ { f } \left( Q \| P _ { 0 } \right) \leq \rho \}$ . The analytic consequences of our choices are nice in that they allow explicit dual calculations and algorithmic development; in the case in which the radius $\rho$ is instead shrinking with as $\rho / n$ , asymptotic and non-asymptotic considerations [72, 36, 15, 62, 64] show that the robustness provides a type of regularization by variance of the loss when $f$ is smooth, no matter what choice of $f .$ In our setting, such limiting similarity is not the case, and it may be unrealistic to assume a user of the approach can justify the appropriate choice of $f .$ Although we provide heuristics for choosing $f$ and $\rho$ in Section 3, a principled understanding of these adaptive procedures is an important future direction of research.

The minimax guarantees demonstrate tradeofs in terms of the robustness we provide, in the sense that larger robustness sets yield more dificult estimation and optimization problems. Our upper and lower bounds match up to rates in n of $n ^ { - 1 / k }$ <sup>∗</sup> (up to logarithmic factors), though not in dimension dependence, so our understanding of higher-dimensional robustness is limited. Obtaining convergence guarantees (Section 4) with scale-sensitive model complexity terms such as Rademacher complexity and its localized variants [11] is also a topic of future research. In our asymptotic results (Section 6), we require an identifiability assumption on the dual formulation, and it is open whether this assumption can be relaxed by analyzing the primal problem directly.

The robust formulation (1) and its empirical formulation (2) are complementary to traditional robustness approaches in statistics arising out of Huber’s work [54, 55]. In the classical notions of Huber robustness, one wishes to obtain an estimate of a parameter $\theta$ of a distribution $P _ { 0 }$ contaminated by some $Q ;$ in our case, in contrast, we wish to obtain a parameter that performs well for all contaminations Q, at least contaminations nearby in some f-divergence ball. Developing a deeper understanding of the connections and contrasts between classical contamination model and distributional robustness approaches will likely yield fruit.

Two related issues arise when we consider problems with covariates X and a outcome Y. The distributionally robust formulation (1) considers shifts in the joint distribution $( X , Y ) \sim P _ { 0 }$ . Traditional domain adaptation approaches, in contrast, take a fixed conditional distribution $P _ { 0 , Y \mid X } ( y \mid x )$ and consider shifts to the marginal distribution $P _ { 0 , X }$ (covariate shift). In causal data analyses, one wishes to perturb only the distribution of the covariates X, observing the efect of such interventions on Y . Connecting these ideas and developing variants of the formulation (1) that only protect against covariate shift or structural shifts on X may be useful in many scenarios.

## Acknowledgments

JCD and HN were partially supported by the SAIL-Toyota Center for AI Research and HN was partially supported Samsung Fellowship. JCD was also partially supported by the National Science Foundation award NSF-CAREER-1553086 and the Ofice of Naval Research Young Investigator award N00014-19-2288.

## References

[1] M. Abramowitz and I. Stegun, editors. Handbook of Mathematical Functions: with Formulas, Graphs, and Mathematical Tables. Dover, 1965.

[2] A. Agarwal, P. L. Bartlett, P. Ravikumar, and M. J. Wainwright. Information-theoretic lower bounds on the oracle complexity of convex optimization. IEEE Transactions on Information Theory, 58(5):3235–3249, 2012.

[3] A. Ahmadi-Javid. Entropic value-at-risk: A new coherent risk measure. Journal of Optimization Theory and Applications, 155(3):1105–1123, 2012.

[4] M. Aitkin and D. B. Rubin. Estimation and hypothesis testing in finite mixture models. Journal of the Royal Statistical Society, Series B, pages 67–75, 1985.

[5] S. M. Ali and S. D. Silvey. A general class of coeficients of divergence of one distribution from another. Journal of the Royal Statistical Society, Series B, 28:131–142, 1966.

[6] D. Amodei, S. Ananthanarayanan, R. Anubhai, J. Bai, E. Battenberg, C. Case, J. Casper, B. Catanzaro, Q. Cheng, and G. Chen. Deep speech 2: end-to-end speech recognition in English and Mandarin. In Proceedings of the 33rd International Conference on Machine Learning, pages 173–182, 2016.

[7] T. W. Anderson. The integral of a symmetric unimodal function over a symmetric convex set and some probability inequalities. Proceedings of the American Mathematical Society, 6 (2):170–176, 1955.

[8] P. Artzner, F. Delbaen, J.-M. Eber, and D. Heath. Coherent measures of risk. Mathematical Finance, 9(3):203–228, 1999.

[9] A. Asuncion and D. J. Newman. UCI machine learning repository, 2007. URL http://www. ics.uci.edu/ mlearn/MLRepository.html.

[10] R. Atar, K. Chowdhary, and P. Dupuis. Robust bounds on risk-sensitive functionals via R´enyi divergence. SIAM/ASA Journal on Uncertainty Quantification, 3(1):18–33, 2015.

[11] P. L. Bartlett, O. Bousquet, and S. Mendelson. Local Rademacher complexities. Annals of Statistics, 33(4):1497–1537, 2005.

[12] S. Ben-David, J. Blitzer, K. Crammer, and F. Pereira. Analysis of representations for domain adaptation. In Advances in Neural Information Processing Systems 20, pages 137–144, 2007.

[13] S. Ben-David, J. Blitzer, K. Crammer, A. Kulesza, F. Pereira, and J. Vaughan. A theory of learning from diferent domains. Machine Learning, 79:151–175, 2010.

[14] A. Ben-Tal, L. E. Ghaoui, and A. Nemirovski. Robust Optimization. Princeton University Press, 2009.

[15] A. Ben-Tal, D. den Hertog, A. D. Waegenaere, B. Melenberg, and G. Rennen. Robust solutions of optimization problems afected by uncertain probabilities. Management Science, 59(2):341–357, 2013.

[16] D. P. Bertsekas. Stochastic optimization problems with nondiferentiable cost functionals. Journal of Optimization Theory and Applications, 12(2):218–231, 1973.

[17] D. Bertsimas, V. Gupta, and N. Kallus. Data-driven robust optimization. Mathematical Programming, Series A, 167(2):235–292, 2018. URL http://arxiv.org/abs/1401.0212.

[18] S. Bickel, M. Br¨uckner, and T. Schefer. Discriminative learning for difering training and test distributions. In Proceedings of the 24th International Conference on Machine Learning, 2007.

[19] J. Blanchet and K. Murthy. Quantifying distributional model risk via optimal transport. Mathematics of Operations Research, 44(2):565–600, 2019.

[20] J. Blanchet, Y. Kang, and K. Murthy. Robust Wasserstein profile inference and applications to machine learning. Journal of Applied Probability, 56(3):830–857, 2019.

[21] J. Blitzer, R. McDonald, and F. Pereira. Domain adaptation with structural correspondence learning. In Proceedings of the 2006 conference on empirical methods in natural language processing, pages 120–128. Association for Computational Linguistics, 2006.

[22] S. L. Blodgett, L. Green, and B. O’Connor. Demographic dialectal variation in social media: A case study of African-American English. In Proceedings of Empirical Methods for Natural Language Processing, pages 1119–1130, 2016.

[23] S. Boucheron, G. Lugosi, and P. Massart. Concentration Inequalities: a Nonasymptotic Theory of Independence. Oxford University Press, 2013.

[24] S. Boyd and L. Vandenberghe. Convex Optimization. Cambridge University Press, 2004.

[25] P. B¨uhlmann and N. Meinshausen. Magging: maximin aggregation for inhomogeneous largescale data. Proceedings of the IEEE, 104(1):126–135, 2016.

[26] Z. Cai, J. Fan, and R. Li. Eficient estimation and inferences for varying-coeficient models. Journal of the American Statistical Association, 95(451):888–902, 2000.

[27] O. Capp´e, E. Moulines, and T. Ryd´en. Inference in Hidden Markov Models. Springer, 2005.

[28] R. Caruana. Multitask learning. In Learning to Learn, pages 95–133. Springer, 1998.

[29] N. Cressie and T. R. Read. Multinomial goodness-of-fit tests. Journal of the Royal Statistical Society, Series B, pages 440–464, 1984.

[30] I. Csisz´ar. Information-type measures of diference of probability distributions and indirect observation. Studia Scientifica Mathematica Hungary, 2:299–318, 1967.

[31] H. Daume III and D. Marcu. Domain adaptation for statistical classifiers. Journal of artificial

Intelligence research, 26:101–126, 2006.

[32] T. E. de Campos, B. R. Babu, and M. Varma. Character recognition in natural images. In Proceedings of the Fourth International Conference on Computer Vision Theory and Applications, February 2009.

[33] E. Delage and Y. Ye. Distributionally robust optimization under moment uncertainty with application to data-driven problems. Operations Research, 58(3):595–612, 2010.

[34] J. S. Denker, W. R. Gardner, H. P. Graf, D. Henderson, R. E. Howard, W. Hubbard, L. D. Jackel, H. S. Baird, and I. Guyon. Neural network recognizer for hand-written zip code digits. In Advances in Neural Information Processing Systems 1, 1988.

[35] J. C. Duchi. Introductory lectures on stochastic convex optimization. In The Mathematics of Data, IAS/Park City Mathematics Series. American Mathematical Society, 2018.

[36] J. C. Duchi, P. W. Glynn, and H. Namkoong. Statistics of robust optimization: A generalized empirical likelihood approach. arXiv:1610.03425 [stat.ML], 2016.

[37] P. Dupuis, M. A. Katsoulakis, Y. Pantazis, and P. Plech´ac. Path-space information bounds for uncertainty quantification and sensitivity analysis of stochastic dynamics. SIAM/ASA Journal on Uncertainty Quantification, 4(1):80–111, 2016.

[38] Y. C. Eldar, A. Ben-Tal, and A. Nemirovski. Linear minimax regret estimation of deterministic parameters with bounded data uncertainties. IEEE Transactions on Signal Processing, 52(8):2177–2188, 2004.

[39] P. M. Esfahani and D. Kuhn. Data-driven distributionally robust optimization using the wasserstein metric: Performance guarantees and tractable reformulations. Mathematical Programming, Series A, 171(1–2):115–166, 2018.

[40] J. Fan and W. Zhang. Statistical estimation in varying coeficient models. Annals of Statistics, 27(5):1491–1518, 1999.

[41] M. A. T. Figueiredo and A. K. Jain. Unsupervised learning of finite mixture models. IEEE Transactions on Pattern Analysis and Machine Intelligence, 24(3):381–396, 2002.

[42] R. Gao and A. J. Kleywegt. Distributionally robust stochastic optimization with wasserstein distance. arXiv:1604.02199 [math.OC], 2016.

[43] R. J. Gardner. The Brunn-Minkowski inequality. Bulletin of the American Mathematical Society, 39(3):355–405, 2002.

[44] W. Gautschi. The Incomplete Gamma Functions since Tricomi, volume 147 of Atti dei Convegni Lincei. Accademia Nazionale dei Lincei, 1997.

[45] S. Ghosh and H. Lam. Robust analysis in stochastic simulation: Computation and performance guarantees. Operations Research, 2019.

[46] P. Glasserman and X. Xu. Robust risk measurement and model risk. Quantitative Finance, 14(1):29–58, 2013.

[47] J.-y. Gotoh, M. J. Kim, and A. Lim. Robust empirical optimization is almost the same as mean-variance optimization. Available at SSRN 2827400, 2015.

[48] P. J. Grother, G. W. Quinn, and P. J. Phillips. Report on the evaluation of 2d still-image face recognition algorithms. NIST Interagency/Internal Reports (NISTIR), 7709, 2010.

[49] D. J. Hand. Classifier technology and the illusion of progress. Statistical Science, 21(1):1–14, 2006.

[50] L. P. Hansen and T. J. Sargent. Robustness. Princeton University Press, 2008.

[51] J. Hiriart-Urruty and C. Lemar´echal. Convex Analysis and Minimization Algorithms I & II. Springer, New York, 1993.

[52] D. Hovy and A. Søgaard. Tagging performance correlates with author age. In Proceedings of the 53rd Annual Meeting of the Association for Computational Linguistics (Short Papers), volume 2, pages 483–488, 2015.

[53] J. Huang, A. Gretton, K. M. Borgwardt, B. Sch¨olkopf, and A. J. Smola. Correcting sample selection bias by unlabeled data. In Advances in Neural Information Processing Systems 20, pages 601–608, 2007.

[54] P. J. Huber. Robust Statistics. John Wiley and Sons, New York, 1981.

[55] P. J. Huber and E. M. Ronchetti. Robust Statistics. John Wiley and Sons, second edition, 2009.

[56] Y. Jia, E. Shelhamer, J. Donahue, S. Karayev, J. Long, R. Girshick, S. Guadarrama, and T. Darrell. Cafe: Convolutional architecture for fast feature embedding. arXiv:1408.5093 [cs.CV], 2014.

[57] R. Jiang and Y. Guan. Data-driven chance constrained stochastic program. Mathematical Programming, 158(1-2):291–327, 2016.

[58] A. Khosla, N. Jayadevaprakash, B. Yao, and F.-F. Li. Novel dataset for fine-grained image categorization. In First Workshop on Fine-Grained Visual Categorization, IEEE Conference on Computer Vision and Pattern Recognition, volume 2, page 1, 2011.

[59] A. J. King and R. J. Wets. Epi-consistency of convex stochastic programs. Stochastics and Stochastic Reports, 34(1-2):83–92, 1991.

[60] P. A. Krokhmal. Higher moment coherent risk measures. Quantitative Finance, 7(4):373–387, 2007.

[61] S. Kusuoka. On law invariant coherent risk measures. In Advances in Mathematical Economics, pages 83–95. Springer, 2001.

[62] H. Lam. Robust sensitivity analysis for stochastic systems. Mathematics of Operations Research, 41(4):1248–1275, 2016.

[63] H. Lam. Sensitivity to serial dependency of input processes: A robust approach. Management Science, 64(3):1311–1327, 2017.

[64] H. Lam and E. Zhou. The empirical likelihood approach to quantifying uncertainty in sample average approximation. Operations Research Letters, 45(4):301–307, 2017.

[65] L. Le Cam and G. L. Yang. Asymptotics in Statistics: Some Basic Concepts. Springer, 2000.

[66] Y. LeCun, B. Boser, J. S. Denker, D. Henderson, R. E. Howard, W. Hubbard, and L. D. Jackel. Backpropagation applied to handwritten zip code recognition. Neural computation, 1 (4):541–551, 1989.

[67] M. Ledoux and M. Talagrand. Probability in Banach Spaces. Springer, 1991.

[68] J. Lee and M. Raginsky. Minimax statistical learning and domain adaptation with Wasserstein distances. arXiv:1705.07815 [cs.LG], 2017.

[69] G. McLachlan and D. Peel. Finite Mixture Models. John Wiley & Sons, 2004.

[70] N. Meinshausen and P. B¨uhlmann. Maximin efects in inhomogeneous large-scale data. The Annals of Statistics, 43(4):1801–1830, 2015.

[71] H. Namkoong and J. C. Duchi. Stochastic gradient methods for distributionally robust optimization with f-divergences. In Advances in Neural Information Processing Systems 29, 2016.

[72] H. Namkoong and J. C. Duchi. Variance regularization with convex objectives. In Advances in Neural Information Processing Systems 30, 2017.

[73] A. Owen. Empirical likelihood ratio confidence regions. The Annals of Statistics, 18(1): 90–120, 1990.

[74] I. R. Petersen, M. R. James, and P. Dupuis. Minimax optimal control of stochastic uncertain systems with relative entropy constraints. IEEE Transactions on Automatic Control, 45(3): 398–412, 2000.

[75] G. Pflug and D. Wozabal. Ambiguity in portfolio selection. Quantitative Finance, 7(4): 435–442, 2007.

[76] B. Recht, R. Roelofs, L. Schmidt, and V. Shankar. Do ImageNet classifiers generalize to ImageNet? In Proceedings of the 36th International Conference on Machine Learning, 2019.

[77] M. Redmond and A. Baveja. A data-driven software tool for enabling cooperative information sharing among police departments. European Journal of Operational Research, 141(3):660– 678, 2002.

[78] R. T. Rockafellar and S. Uryasev. Optimization of conditional value-at-risk. Journal of Risk, 2:21–42, 2000.

[79] R. T. Rockafellar and R. J. B. Wets. Variational Analysis. Springer, New York, 1998.

[80] D. Rothenh¨ausler, N. Meinshausen, and P. B¨uhlmann. Confidence intervals for maximin efects in inhomogeneous large-scale data. In Statistical Analysis for High-Dimensional Data, pages 255–277. Springer, 2016.

[81] D. Rothenh¨ausler, P. B¨uhlmann, N. Meinshausen, and J. Peters. Anchor regression: heterogeneous data meets causality. arXiv:1801.06229 [stat.ME], 2018.

[82] K. Saenko, B. Kulis, M. Fritz, and T. Darrell. Adapting visual category models to new domains. In Proceedings of the European Conference on Computer Vision, pages 213–226. Springer, 2010.

[83] P. Sapiezynski, V. Kassarnig, and C. Wilson. Academic performance prediction in a genderimbalanced environment. In Proceedings of the Eleventh ACM Conference on Recommender Systems, volume 1, pages 48–51, 2017.

[84] S. Shafieezadeh-Abadeh, P. M. Esfahani, and D. Kuhn. Distributionally robust logistic regression. In Advances in Neural Information Processing Systems 28, pages 1576–1584, 2015.

[85] M. Shaked and J. G. Shanthikumar. Stochastic Orders. Springer Series in Statistics. Springer, 2007.

[86] A. Shapiro. On Kusuoka representation of law invariant risk measures. Mathematics of Operations Research, 38(1):142–152, 2013.

[87] A. Shapiro. Distributionally robust stochastic programming. SIAM Journal on Optimization, 27(4):2258–2275, 2017.

[88] A. Shapiro, D. Dentcheva, and A. Ruszczy´nski. Lectures on Stochastic Programming: Modeling and Theory. SIAM and Mathematical Programming Society, 2009.

[89] H. Shimodaira. Improving predictive inference under covariate shift by weighting the log-

likelihood function. Journal of Statistical Planning and Inference, 90(2):227–244, 2000.

[90] M. Simon and M.-S. Alouini. Digital Communication Over Fading Channels: A Unified Approach to Performance Analysis. John Wiley & Sons, New York, 2000.

[91] A. Sinha, H. Namkoong, and J. C. Duchi. Certifiable distributional robustness with principled adversarial training. arXiv:1710.10571 [stat.ML], 2017.

[92] M. Sugiyama, M. Krauledat, and K.-R. M¨uller. Covariate shift adaptation by importance weighted cross validation. Journal of Machine Learning Research, 8:985–1005, 2007.

[93] M. Sugiyama, S. Nakajima, H. Kashima, P. V. Buenau, and M. Kawanabe. Direct importance estimation with model selection and its application to covariate shift adaptation. In Advances in Neural Information Processing Systems 21, pages 1433–1440, 2008.

[94] Y. Sun, Arp´ad Baricz, and S. Zhou. On the monotonicity, log-concavity and tight bounds of <sup>´</sup> the generalized Marcum and Nuttall Q-functions. IEEE Transactions on Information Theory, 56(3):1166–1186, 2010.

[95] M. Talagrand. A new look at independence. Annals of Probability, 24(1):1–34, 1996.

[96] R. Tatman. Gender and dialect bias in YouTube’s automatic captions. In First Workshop on Ethics in Natural Langauge Processing, volume 1, pages 53–59, 2017.

[97] A. Torralba and A. A. Efros. Unbiased look at dataset bias. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pages 1521–1528. IEEE, 2011.

[98] Y. Tsuboi, H. Kashima, S. Hido, S. Bickel, and M. Sugiyama. Direct density ratio estimation for large-scale covariate shift adaptation. Journal of Information Processing, 17:138–155, 2009.

[99] A. B. Tsybakov. Introduction to Nonparametric Estimation. Springer, 2009.

[100] M. Udell, K. Mohan, D. Zeng, J. Hong, S. Diamond, and S. Boyd. Convex optimization in Julia. In First Workshop on High Performance Technical Computing in Dynamic Languages, pages 18–28. IEEE, 2014.

[101] Y. Usui and K. Kondo. The sift image feature reduction method using the histogram intersection kernel. In International Symposium on Intelligent Signal Processing and Communication Systems (ISPACS), pages 517–520. IEEE, 2009.

[102] A. W. van der Vaart. Asymptotic Statistics. Cambridge Series in Statistical and Probabilistic Mathematics. Cambridge University Press, 1998.

[103] A. W. van der Vaart and J. A. Wellner. Weak Convergence and Empirical Processes: With Applications to Statistics. Springer, New York, 1996.

[104] T. van Erven and P. Harremo¨es. R´enyi divergence and Kullback-Leibler divergence. IEEE Transactions on Information Theory, 60(7):3797–3820, 2014.

[105] A. Wald. Statistical decision functions which minimize the maximum risk. Annals of Mathematics, 46(2):265–280, 1945.

[106] D. Wozabal. A framework for optimization under ambiguity. Annals of Operations Research, 193(1):21–47, 2012.

[107] B. Yu. Assouad, Fano, and Le Cam. In Festschrift for Lucien Le Cam, pages 423–435. Springer-Verlag, 1997.

[108] H. Zou and T. Hastie. Regularization and variable selection via the elastic net. Journal of the Royal Statistical Society, Series B, 67(2):301–320, 2005.

## A Proof of Duality Results

## A.1 Proof of Lemma 1

First, we compute the Fenchel conjugate for Cressie-Read family of divergences $f _ { k }$

Lemma 3.

$$
f _ {k} ^ {*} (s) = \frac {1}{k} ((k - 1) s + 1) _ {+} ^ {k ^ {*}} - \frac {1}{k}\tag{21}
$$

Proof Consider the supremum $f ^ { * } ( s ) = \operatorname* { s u p } _ { t } \{ s t - f ( t ) \}$ . Then for $t \geq 0$ , we have

$$
\frac {\partial}{\partial t} \left[ s t - f _ {k} (t) \right] = s - \frac {1}{k - 1} (t ^ {k - 1} - 1).
$$

If $s < 0 ,$ , then the supremum is attained at $t = 0$ , as the derivative above is $< 0$ at $t = 0$ . If $s \geq - \frac { 1 } { k - 1 }$ , then we solve $\begin{array} { r l } { { \frac { \partial } { \partial t } } \left[ s t - f _ { k } ( t ) \right] = } \end{array}$ to find $t = ( ( k - 1 ) s + 1 ) ^ { 1 / ( k - 1 ) }$ , and substituting gives

$$
s t - f (t) = \frac {1}{k} \left((k - 1) s + 1\right) ^ {\frac {k}{k - 1}} - \frac {1}{k}
$$

which is our desired result as $1 - 1 / k = 1 / k _ { * }$

From the dual formulation (4), we have

$$
\begin{array}{l} \sup _ {P \ll P _ {0}} \left\{\mathbb {E} _ {P} [ Z ] \text {s.t.} D _ {f} (P \| P _ {0}) \leq \rho \right\} = \inf _ {\lambda \geq 0, \eta} \left\{\lambda \mathbb {E} _ {P _ {0}} f ^ {*} \left(\frac {Z - \eta}{\lambda}\right) + \lambda \rho + \eta \right\} \\ = \inf _ {\lambda \geq 0, \eta} \left\{\frac {(k - 1) ^ {k _ {*}}}{k} \lambda^ {1 - k _ {*}} \mathbb {E} _ {P _ {0}} \left(Z - \eta + \frac {\lambda}{k - 1}\right) _ {+} ^ {k _ {*}} + \lambda (\rho - \frac {1}{k}) + \eta \right\} \\ = \inf _ {\lambda \geq 0, \tilde {\eta}} \left\{(k - 1) ^ {k _ {*}} k ^ {- 1} \mathbb {E} _ {P _ {0}} (Z - \tilde {\eta}) _ {+} ^ {k _ {*}} \lambda^ {1 - k _ {*}} + \left(\rho + \frac {1}{k (k - 1)}\right) \lambda + \tilde {\eta} \right\} \end{array}
$$

where the last line followed by setting $\begin{array} { r } { \widetilde { \eta } : = \eta - \frac { \lambda } { k - 1 } } \end{array}$ . Taking derivatives with respect to λ to infimize the preceding expression, we have (noting that $( \bar { k } _ { * } - 1 ) / k _ { * } = 1 / k )$

$$
\lambda = (k - 1) (k (k - 1) \rho + 1) ^ {- \frac {1}{k _ {*}}} \left(\mathbb {E} _ {P _ {0}} (Z - \tilde {\eta}) _ {+} ^ {k _ {*}}\right) ^ {\frac {1}{k _ {*}}}\tag{22}
$$

By substituting into the preceding expression, we find that the supremum is

$$
\inf _ {\tilde {\eta}} \left(k (k - 1) \rho + 1\right) ^ {\frac {1}{k}} \left(\mathbb {E} _ {P _ {0}} \left(Z - \tilde {\eta}\right) _ {+} ^ {k _ {*}}\right) ^ {1 / k _ {*}} + \tilde {\eta}.
$$

## A.2 Moments and duality

We discuss the norm-like behavior of the robust risk $\mathcal { R } _ { f }$ when $f$ behaves asymptotically as $t ^ { k }$ for some $k \in \mathsf { \Gamma } ( 1 , \infty )$ ; we treat $c _ { j }$ and $C _ { j }$ as constants whose values may change from line to line. For simplicity we assume that $f$ is diferentiable, though subdiferential calculus [51] allows immediate extension to the non-diferentiable case. Assume that $0 ~ <$ lim inf $\mathop { t \to \infty } f ( t ) / t ^ { k } \leq$ lim $\textstyle \operatorname* { s u p } _ { t \to \infty } f ( t ) / t ^ { k } < \infty$ . Then as $t \mapsto f ^ { \prime } ( t )$ is non-decreasing, there exist $0 < c _ { 0 } \le c _ { 1 } < \infty$ such that $c _ { 0 } t ^ { k - 1 } \leq f ^ { \prime } ( t ) \leq c _ { 1 } t ^ { k - 1 }$ for all large enough t. Then for all large s the t solving $f ^ { \prime } ( t ) = s$ satisfies $c _ { 0 } t ^ { k - 1 } \leq s \leq c _ { 1 } t ^ { k - 1 }$ , that is, $( s / c _ { 1 } ) ^ { \frac { 1 } { k - 1 } } \leq ( f ^ { \prime } ) ^ { - 1 } ( s ) \leq ( s / c _ { 0 } ) ^ { \frac { 1 } { k - 1 } }$ . Recall that the conjugate $f ^ { * } ( s ) : = \operatorname* { s u p } _ { t } \{ s t - f ( t ) \}$ satisfies the duality $( f ^ { \prime } ) ^ { - 1 } ( s ) = ( f ^ { \ast } ) ^ { \prime } ( s )$ , and as dom $f \subset \mathbb { R } _ { + } , f ^ { * }$ is non-decreasing [51]. Then there are constants $C _ { 0 } , C _ { 1 }$ such that for all large s, we evidently have

$$
C _ {0} s ^ {\frac {1}{k - 1}} \leq (f ^ {*}) ^ {\prime} (s) \leq C _ {1} s ^ {\frac {1}{k - 1}},
$$

and so by an integration argument

$$
C _ {0} s ^ {k _ {*}} \leq f ^ {*} (s) \leq C _ {1} s ^ {k _ {*}} \text { for   large } s.
$$

In particular, for some threshold $\tau _ { f }$ depending on $f ,$ if we define the shorthand $Z = \ell ( \theta ; X )$ then the dual (4) satisfies

$$
\begin{array}{l}\inf _ {\lambda \geq 0, \eta \in \mathbb {R}} \left\{C _ {0} \lambda^ {1 - k _ {*}} \mathbb {E} \left[ (Z - \eta) _ {*} ^ {k} \mathbf {1} \left\{Z \geq \lambda \tau_ {f} \right\} \right] + \lambda \mathbb {E} \left[ f ^ {*} \left(\frac {Z - \eta}{\lambda}\right) \mathbf {1} \left\{Z <   \lambda \tau_ {f} \right\} \right] + \eta + \lambda \rho \right\}\\\leq \mathcal {R} _ {f} (\theta ; P _ {0})\\\leq \inf _ {\lambda \geq 0, \eta \in \mathbb {R}} \left\{ \right.C _ {1} \lambda^ {1 - k _ {*}} \mathbb {E} \left[ (Z - \eta) _ {*} ^ {k} \mathbf {1} \left\{Z \geq \lambda \tau_ {f} \right\}\right] + \lambda \mathbb {E} \left[ \right. f ^ {*} \left(\frac {Z - \eta}{\lambda}\right) \mathbf {1} \left.\left\{Z <   \lambda \tau_ {f} \right\}\right] + \eta + \lambda \rho \left. \right\}.\end{array}
$$

That $\begin{array} { r } { \operatorname* { i n f } _ { \lambda \geq 0 } \{ \lambda \rho + C \lambda ^ { 1 - k _ { * } } \} = ( k _ { * } - 1 ) ^ { 1 / k _ { * } } ( 1 + \frac { 1 } { k _ { * } } ) \rho ^ { 1 / k } C ^ { 1 / k _ { * } } } \end{array}$ shows that once again, we have the dependence of $\mathcal { R } _ { f }$ on $k _ { * } \mathrm { t h }$ moments of the loss.

## B Proofs of Examples

## B.1 Proof of Example 4

That $\begin{array} { r } { \theta _ { 1 } = \sum _ { v } p _ { v } \theta _ { \imath } } \end{array}$ is immediate. For the second claim, we begin with a characterization of the Chebyshev center and a few of its properties. We have

$$
\theta_ {\mathrm{minimax}} = \sum_ {v} s _ {v} \theta_ {v} \quad \text { where } \mathbf {1} ^ {T} s = 1, s \succeq 0,
$$

and by the KKT conditions for optimality, $s _ { v } > 0$ only if max $w { \in } V \| \theta _ { \mathrm { m i n i m a x } } - \theta _ { w } \| _ { 2 } = \| \theta _ { v } - \theta _ { w } \| _ { 2 }$ We recall that a function $h$ is c-strongly if $\begin{array} { r l } { \langle \nabla h ( \theta ) - \nabla h ( \tau ) , \theta - \tau \rangle \geq c \| \theta - \tau \| _ { 2 } ^ { 2 } . } \end{array}$ , and $\theta ^ { \star }$ minimizes h over Θ if and only if for some $g \in \partial h ( \theta ^ { \star } )$ we have $\left. g , \theta - \theta ^ { \star } \right. \ge 0$ for all $\theta \in \Theta$ . Let $h ( \theta ) =$ $\begin{array} { r } { \frac 1 2 \operatorname* { m a x } _ { v \in V } \| \theta - \theta _ { v } \| _ { 2 } ^ { 2 } . } \end{array}$ . Then letting $\theta \ne \theta _ { \mathrm { { m i n i m a x } } }$ , we immediately see that for any $v \in V$ for which $\begin{array} { r } { \left\| \theta - \theta _ { v } \right\| _ { 2 } = \operatorname* { m a x } _ { w \in V } \left\| \theta - \theta _ { w } \right\| _ { 2 } . } \end{array}$ , we have for $g = \theta - \theta _ { v } \in \partial h ( \theta )$ and $g ^ { \prime } \in \partial h ( \theta _ { \mathrm { m i n i m a x } } )$ that

$$
\begin{array}{r l} \langle \theta - \theta_ {v}, \theta - \theta_ {\mathrm{minimax}} \rangle & = \langle g, \theta - \theta_ {\mathrm{minimax}} \rangle \\ & \geq \big \langle g ^ {\prime}, \theta - \theta_ {\mathrm{minimax}} \big \rangle + \| \theta - \theta_ {\mathrm{minimax}} \| _ {2} ^ {2} \geq \| \theta - \theta_ {\mathrm{minimax}} \| _ {2} ^ {2}. \end{array}\tag{23}
$$

Fix $\boldsymbol { \theta } \in \mathbb { R } ^ { d }$ with $\theta \neq \theta _ { \mathrm { { m i n i m a x } } }$ . For fixed $\eta > 0$ , consider the objectives $h _ { v } ( \cdot ; \eta ) : \mathbb { R } \to \mathbb { R }$ 2

$$
h _ {v} (t; \eta) := \mathbb {E} \left[ \left((1 / 2) \| (1 - t) \theta + t \theta_ {\mathrm{minimax}} - \theta_ {v} - \varepsilon \| _ {2} ^ {2} - \eta\right) _ {+} \right].
$$

By the continuity of the density of $\varepsilon , h _ { v }$ is diferentiable in $t ,$ and we have

$$
h _ {v} ^ {\prime} (t; \eta) = \mathbb {E} \left[ \mathbf {1} \left\{\| (1 - t) \theta + t \theta_ {\mathrm{minimax}} - \theta_ {v} - \varepsilon \| _ {2} ^ {2} \geq 2 \eta \right\} \langle \theta_ {\mathrm{minimax}} - \theta , (1 - t) \theta + t \theta_ {\mathrm{minimax}} - \theta_ {v} - \varepsilon \rangle \right]
$$

and

$$
h _ {v} ^ {\prime} (0; \eta) = \mathbb {E} \left[ \mathbf {1} \left\{\| \theta - \theta_ {v} - \varepsilon \| _ {2} ^ {2} \geq 2 \eta \right\} \langle \theta_ {\mathrm{minimax}} - \theta , \theta - \theta_ {v} - \varepsilon \rangle \right].\tag{24}
$$

For any vector $\mu \in \mathbb { R } ^ { d }$ , define the constant $c ( \eta ; \mu ) > 0$ such that

$$
\mathbb {E} [ \mathbf {1} \left\{\| \mu + \varepsilon \| _ {2} ^ {2} \geq 2 \eta \right\} (\mu + \varepsilon) ] = c (\eta ; \mu) \mu ,
$$

which must exist by the rotational symmetry of the Gaussian. Now we claim that for any $\mu _ { 1 } , \mu _ { 2 }$ with $\left\| \mu _ { 1 } \right\| _ { 2 } > \left\| \mu _ { 2 } \right\| _ { 2 }$ 2

$$
\lim _ {\eta \to \infty} \frac {c (\eta ; \mu_ {1})}{c (\eta ; \mu_ {2})} = \infty .\tag{25}
$$

Deferring the proof of the claim (25), let us see how it yields the theorem.

We shall show that for $\theta \neq \theta _ { \mathrm { { m i n i m a x } } }$ , if we define

$$
R (t; \eta) := \sum_ {v} p _ {v} \mathbb {E} \left[ \left((1 / 2) \| (1 - t) \theta + t \theta_ {\mathrm{minimax}} - \theta_ {v} - \varepsilon \| _ {2} ^ {2} - \eta\right) _ {+} \right],
$$

then for all large $\eta ,$ we have $R ^ { \prime } ( 0 ; \eta ) < 0$ , so $\theta$ cannot minimize $\begin{array} { r } { \sum _ { v } p _ { v } \mathbb { E } [ \big ( ( 1 / 2 ) \| \theta - \theta _ { v } - \varepsilon \| _ { 2 } ^ { 2 } - \eta \big ) _ { + } ] } \end{array}$ That this gives the theorem is nearly immediate, because for all $0 < \alpha \leq 1$ , the η minimizing the CVaR risk $\alpha ^ { - 1 } \mathbb { E } [ ( \ell ( \theta ; Y ) - \eta ) _ { + } ] + \eta$ is the $1 - \alpha$ quantile of $\ell ( \theta ; Y )$ , which for our setting evidently tends to ∞ as $\alpha \downarrow 0$ . Thus, if $\begin{array} { r } { \eta ( \theta , \alpha ) = \mathrm { a r g m i n } _ { \eta } \{ \alpha ^ { - 1 } \mathbb { E } [ ( \ell ( \theta ; Y ) - \eta ) _ { + } ] + \eta \} } \end{array}$ , we have $\eta ( \theta , \alpha )  \infty$ uniformly in θ as α $\downarrow 0$ , and so $R ^ { \prime } ( 0 ; \eta ) < 0$ implies that θ cannot minimize $\operatorname { C V a R } _ { \alpha } ( \ell ( \theta ; Y ) )$ . To see that $R ^ { \prime } ( 0 ; \eta ) < 0$ , simply note that

$$
R ^ {\prime} (0; \eta) = \sum_ {v} p _ {v} c (\eta ; \| \theta - \theta_ {v} \| _ {2}) \langle \theta_ {\mathrm{minimax}} - \theta , \theta - \theta_ {v} \rangle
$$

by Eq. (24). Let $V ^ { \star } = \left\{ v : \left\| \theta - \theta _ { v } \right\| _ { 2 } = \operatorname* { m a x } _ { w } \left\| \theta - \theta _ { w } \right\| _ { 2 } \right\}$ . Then inequality (23) implies that

$$
\begin{array}{l} R ^ {\prime} (0; \eta) \leq - \bigg (\sum_ {v \in V ^ {\star}} p _ {v} c (\eta ; \| \theta - \theta_ {v} \| _ {2}) \bigg) \| \theta - \theta_ {\text {minimax}} \| _ {2} ^ {2} \\ \quad + \sum_ {v \not \in V ^ {\star}} p _ {v} c (\eta ; \| \theta - \theta_ {v} \| _ {2}) c (\eta ; \| \theta - \theta_ {v} \| _ {2})   \langle \theta_ {\text {minimax}} - \theta , \theta - \theta_ {v} \rangle  . \end{array}
$$

In particular, for any $v \in V ^ { \star }$ we have

$$
\frac {1}{c (\eta ; \| \theta - \theta_ {v} \| _ {2})} R ^ {\prime} (0; \eta) \leq - \left(\sum_ {v \in V ^ {\star}} p _ {v}\right) \| \theta - \theta_ {\text { minimax }} \| _ {2} ^ {2} + o (1)
$$

as $\eta  \infty$ , giving the theorem.

Finally, we return to prove the claim (25), note that $\| \mu + \varepsilon \| _ { 2 } ^ { 2 }$ follows a non-central $\chi ^ { 2 }$ distribution with $\mathbb { P } ( \| \mu + \varepsilon \| _ { 2 } ^ { 2 } \geq t ) = Q _ { d / 2 } ( \| \mu \| _ { 2 } , \sqrt { t } )$ for Q the Marcum Q-function. Letting Φ be the standard Gaussian CDF, the Marcum Q-function satisfies the asymptotics (e.g. [90, p. 81] or [94, Eq. (4)]) that as $t \to \infty$

$$
Q _ {k} (a, t) = (1 + o (1)) \left(\frac {t}{a}\right) ^ {k - 1 / 2} (1 - \Phi (t - a)) = (1 + o (1)) \frac {1}{t - a} \exp \left(- \frac {(t - a) ^ {2}}{2}\right) \left(\frac {t}{a}\right) ^ {k - 1 / 2}.
$$

Thus we obtain

$$
\begin{array}{c} \frac {\mathbb {P} (\| \mu_ {1} + \varepsilon \| _ {2} ^ {2} \geq t ^ {2})}{\mathbb {P} (\| \mu_ {2} + \varepsilon \| _ {2} ^ {2} \geq t ^ {2})} = (1 + o (1)) \left(\frac {\| \mu_ {2} \| _ {2}}{\| \mu_ {1} \| _ {2}}\right) ^ {\frac {d - 1}{2}} \exp \left(- \frac {(t - \| \mu_ {1} \| _ {2}) ^ {2}}{2} + \frac {(t - \| \mu_ {2} \| _ {2}) ^ {2}}{2}\right) \\ = (1 + o (1)) \left(\frac {\| \mu_ {2} \| _ {2}}{\| \mu_ {1} \| _ {2}}\right) ^ {\frac {d - 1}{2}} \exp \left(t (\| \mu_ {1} \| _ {2} - \| \mu_ {2} \| _ {2}) + \frac {1}{2} (\| \mu_ {2} \| _ {2} ^ {2} - \| \mu_ {1} \| _ {2} ^ {2})\right) \to \infty \end{array}
$$

as $t \to \infty$ , giving the claim (25).

## B.2 Proof of Example 5

That $\begin{array} { r } { \theta _ { \mathrm { o l s } } = \theta _ { 1 } = \int \theta _ { v } d \mu ( v ) } \end{array}$ is immediate.

We begin with a technical lemma on the expectations of Gaussian variables whose proof we defer to Sec. B.2.1.

Lemma 4. Let $Z \sim \mathsf { N } ( 0 , 1 )$ . Then

$$
\mathbb {E} \left[ (Z ^ {2} - t) _ {+} \right] = \sqrt {\frac {2}{\pi}} (t - 1 + O (t ^ {- 1})) e ^ {- \frac {1}{2} t ^ {2}}.
$$

Defining the shorthand $\tau _ { v } ^ { 2 } ( \theta ) : = ( \theta - \theta _ { v } ) ^ { T } \Sigma _ { v } ( \theta - \theta _ { v } ) + \sigma _ { v } ^ { 2 }$ , for $Z \sim { \mathsf { N } } ( 0 , 1 )$ we evidently have

$$
\mathrm{CVaR} _ {\alpha} (\ell (\theta ; X, Y)) = \inf _ {\eta} \left\{\frac {1}{2 \alpha} \int \mathbb {E} \left[ \left(\tau_ {v} ^ {2} (\theta) Z ^ {2} - 2 \eta\right) _ {+} \right] d \mu (v) + \eta \right\}.\tag{26}
$$

For large η, Lemma 4 gives

$$
\begin{array}{r l} & {\mathbb {E} \left[ \left(\tau_ {v} ^ {2} (\theta) Z ^ {2} - 2 \eta\right) _ {+} \right] = \tau_ {v} ^ {2} (\theta) \mathbb {E} \left[ \left(Z ^ {2} - 2 \eta / \tau_ {v} ^ {2} (\theta)\right) _ {+} \right]} \\ & {\qquad = C (1 + O (\tau_ {v} ^ {2} (\theta) / \eta)) \eta \exp \left(- \frac {2 \eta^ {2}}{\tau_ {v} ^ {4} (\theta)}\right)} \end{array}\tag{27}
$$

uniformly in $\tau _ { v } ^ { 2 } ( \theta )$ , where $C = 2 { \sqrt { 2 / \pi } }$ is a fixed constant.

We now compute normalized asymptotics of the mixture CVaR (26). For a measure µ on V and measurable $g : V \to \mathbb { R }$ , we define the quantile quan $\mathfrak { t } _ { p } ( g , \mu ) : = \operatorname* { i n f } \{ t \in \mathbb { R } : p \le \mu ( g ^ { - 1 } ( ( - \infty , t ] ) ) \}$ }, which gives the following.

Lemma 5. Let $\epsilon > 0$ and let ess sup $, g ( v ) = \operatorname* { i n f } \{ t \mid \mu ( \{ v : g ( v ) > t \} ) = 0 \}$ be the essential supremum of g. Then for all $t > 0$ ,

$$
t \mathsf {q u a n t} _ {1 - \epsilon} (g, \mu) - \log \frac {1}{\epsilon} \leq \log \left(\int e ^ {t g (v)} d \mu (v)\right) \leq t \operatorname * {e s s   s u p} _ {v \in V} g (v).
$$

Proof Clearly log $\begin{array} { r } { \int e ^ { t g ( v ) } d \mu ( v ) \le t \mathrm { e s s } \operatorname* { s u p } _ { v \in V } g ( v ) } \end{array}$ . For the lower bound, letting $q = \mathsf { q u a n t } _ { 1 - \epsilon } ( g , \mu )$ ， we have log $\begin{array} { r } { \int e ^ { t g ( v ) } \dot { d \mu } ( v ) \ge \log \int e ^ { t q } { \bf 1 } \left\{ g ( v ) \ge q \right\} d \mu ( v ) \ge \log \epsilon + t q . } \end{array}$ □

For $\boldsymbol { \theta } \in \mathbb { R } ^ { d }$ and $\eta > 0$ define the normalized logarithmic risk

$$
R (\theta ; \eta) := \frac {1}{2 \eta^ {2}} \log \int \mathbb {E} _ {v} \left[ \left(\tau_ {v} ^ {2} (\theta) Z ^ {2} - 2 \eta\right) _ {+} \right] d \mu (v),
$$

which by Lemma 5 satisfies

$$
\begin{array}{r l} & {\mathsf {q u a n t} _ {1 - \epsilon} \left(- \frac {1}{\tau_ {v} ^ {4} (\theta)}, \mu\right) - \frac {\log \frac {1}{\epsilon}}{2 \eta^ {2}} + \frac {\log \left(C (1 + O (1 / \eta)) \eta\right)}{2 \eta^ {2}}} \\ & {\qquad \leq R (\theta ; \eta) \leq \sup _ {v} \left\{- \frac {1}{\tau_ {v} ^ {4} (\theta)} \right\} + \frac {\log \left(C (1 + O (1 / \eta)) \eta\right)}{2 \eta^ {2}},} \end{array}
$$

where we have used the boundedness assumptions on $\Sigma _ { v } , \sigma _ { v } ,$ and $\theta _ { v }$ .

Assume now that $\theta \ne \theta _ { \mathrm { { m i n i m a x } } } .$ . Then ${ \mathrm { s u p } } _ { v } \tau _ { v } ( \theta ) > { \mathrm { s u p } } _ { v } \tau _ { v } ( \theta _ { \mathrm { m i n i m a x } } )$ because $\Sigma _ { v } \succ 0$ and so $\theta _ { \mathrm { m i n i m a x } }$ must be unique. By the assumption that the essential suprema and suprema over v are equal, $\mathsf { q u a n t } _ { 1 - \epsilon } ( - 1 / \tau _ { v } ^ { 4 } ( \theta ) ) \to \operatorname* { s u p } _ { v } \{ - 1 / \tau _ { v } ^ { 4 } ( \theta ) \}$ as $\epsilon  0 .$ , for all large enough η we have

$$
R (\theta_ {\mathrm{minimax}}; \eta) <   R (\theta ; \eta).
$$

Notably, if $\theta _ { \eta } \in \mathrm { a r g m i n } _ { \theta } R ( \theta ; \eta )$ , then evidently $\theta _ { \eta }  \theta _ { \mathrm { { m i n i m a x } } }$

Finally, we consider the quantity

$$
\eta_ {\alpha} (\theta) := \underset {\eta} {\operatorname{argmin}} \left\{\frac {1}{\alpha} \int \mathbb {E} _ {v} \left[ (\ell (\theta ; X, Y) - \eta) _ {+} \right] d \mu (v) + \eta \right\}.
$$

By definition, we have

$$
\underset {\theta} {\operatorname{argmin}} \mathrm{CVaR} _ {\alpha} (\ell (\theta ; X, Y)) = \underset {\theta} {\operatorname{argmin}} \int \mathbb {E} _ {v} [ (\ell (\theta ; X, Y) - \eta_ {\alpha} (\theta)) _ {+} ] d \mu (v),
$$

and moreover, $\eta _ { \alpha } ( \theta ) = \mathsf { q u a n t } _ { 1 - \alpha } ( \ell ( \theta ; X , Y ) )$ , where the quantile is computed jointly over $v \sim \mu$ and $( X , Y )$ . As by assumption inf ${ \dot { \cdot } } _ { v } \sigma _ { v } ^ { 2 } > 0 .$ , it is evident that lim $\begin{array} { r } { \operatorname* { i n f } _ { \alpha \downarrow 0 } \operatorname* { i n f } _ { \theta } \eta _ { \alpha } ( \theta ) = \infty } \end{array}$ . In particular, for all small enough $\alpha > 0$ , we obtain $R ( \theta _ { \mathrm { m i n i m a x } } , \eta _ { \alpha } ( \theta ) ) < R ( \theta , \eta _ { \alpha } ( \theta ) )$ , or

$$
\int \mathbb {E} _ {v} \left[ (\ell (\theta_ {\mathrm{minimax}}; X, Y) - \eta_ {\alpha} (\theta)) _ {+} \right] <   \int \mathbb {E} _ {v} \left[ (\ell (\theta ; X, Y) - \eta_ {\alpha} (\theta)) _ {+} \right],
$$

giving the result we claim in Example 5.

## B.2.1 Proof of Lemma 4

Let $\Phi ( t ) = \mathbb { P } ( Z \leq t )$ be the standard normal CDF and $\textstyle \Gamma ( a , x ) = \int _ { x } ^ { \infty } z ^ { a - 1 } e ^ { - z } d z$ be the incomplete Gamma function. For $t \geq 0$ we have

$$
\begin{array}{r l} & {\mathbb {E} [ (Z ^ {2} - t) _ {+} ] = \sqrt {\frac {2}{\pi}} \int_ {t} ^ {\infty} (z ^ {2} - t) e ^ {- \frac {1}{2} z ^ {2}} d z} \\ & {\stackrel {(i)} {=} \frac {2}{\sqrt {\pi}} \int_ {t ^ {2} / 2} ^ {\infty} u ^ {1 / 2} e ^ {- u} d u - 2 t (1 - \Phi (t))} \\ & {= \frac {2}{\sqrt {\pi}} \Gamma \left(\frac {3}{2}, \frac {t ^ {2}}{2}\right) - 2 t (1 - \Phi (t))} \end{array}
$$

where inequality (i) is via the substitution $u = z ^ { 2 } / 2$ . Now we use asymptotics of the normal CDF and incomplete Gamma function to approximate the preceding display for large t. By standard normal approximations [1, Eq. (7.1.13)], we have for $t \geq 0$ that

$$
\frac {t}{t ^ {2} + 1} e ^ {- \frac {1}{2} t ^ {2}} \leq \frac {2}{t + \sqrt {t ^ {2} + 4}} e ^ {- \frac {1}{2} t ^ {2}} \leq \sqrt {2 \pi} (1 - \Phi (t)) \leq \frac {2}{t + \sqrt {t ^ {2} + 8 / \pi}} e ^ {- \frac {1}{2} t ^ {2}} \leq \frac {1}{t} e ^ {- \frac {1}{2} t ^ {2}}.
$$

As $\sqrt { t ^ { 2 } + c } = t + c / 2 t + O ( t ^ { - 2 } )$ for any constant $^ { c , }$ we have

$$
\left(1 - \Phi (t)\right) = \frac {1}{\sqrt {2 \pi}} \left(t ^ {- 1} - O (1) t ^ {- 3}\right) e ^ {- \frac {1}{2} t ^ {2}},
$$

while we also have the well-known asymptotic expansion

$$
\Gamma (a + 1, x) = \frac {e ^ {- x} x ^ {a + 1}}{x - a} \left[ 1 - \frac {a}{(x - a) ^ {2}} + \frac {2 a}{(x - a) ^ {3}} + O \left(\frac {a ^ {2}}{(x - a) ^ {4}}\right) \right]
$$

as $\sqrt { a } / ( x - a )  0 [ 4 4 , \mathrm { E q . ~ ( 2 . 1 2 ) } ]$

Substituting these above (with $x = t ^ { 2 } / 2$ and $a = 1 / 2 )$ yields for large t that

$$
\begin{array}{r l} & {\sqrt {\pi / 2} e ^ {\frac {1}{2} t ^ {2}} \mathbb {E} \left[ (Z ^ {2} - t) _ {+} \right] = \frac {t ^ {3}}{t ^ {2} - 1} \left[ 1 - \frac {2}{(t ^ {2} - 1) ^ {2}} + O (t ^ {- 6}) \right] - t \left(\frac {1}{t} - \frac {O (1)}{t ^ {3}}\right)} \\ & {\qquad = t - 1 + O (t ^ {- 1}),} \end{array}
$$

giving the lemma.

## C Proof of Upper Bounds

## C.1 Proof of Theorem 2

To ease notation, for any fixed $\theta \in \Theta$ , let $Z ( x ) = \ell ( \theta ; x )$ and

$$
g _ {k} (\eta ; P) := c _ {k} \left(\mathbb {E} _ {P} [ (Z - \eta) _ {+} ^ {k _ {*}}\right) ^ {\frac {1}{k _ {*}}} + \eta
$$

so that $\begin{array} { r } { \mathcal { R } _ { k } ( Z ; P ) = \operatorname* { i n f } _ { \eta } g _ { k } ( \eta ; P ) } \end{array}$ from Proposition 1. We begin by showing pointwise concentration of $g _ { k } ( \eta ; \widehat { P } _ { n } )$ to $g _ { k } ( \eta ; P _ { 0 } )$ for each bounded η. First, we begin by recalling a standard convex Lipschitz concentration inequality for bounded random variables.

Lemma 6 (Boucheron et al. 2013, Theorem 6.10). Let $h : \mathbb { R } ^ { n }  \mathbb { R }$ be convex or concave and L-Lipschitz with respect to the $\ell _ { 2 } { - } n o r m$ . Let $Z _ { i }$ be independent random variables with $Z _ { i } \in [ a , b ]$ For $t \geq 0$ 2

$$
\mathbb {P} (| h (Z _ {1} ^ {n}) - \mathbb {E} [ h (Z _ {1} ^ {n}) ] | \geq t) \leq 2 \exp \left(- \frac {t ^ {2}}{2 L ^ {2} (b - a) ^ {2}}\right).
$$

To apply Lemma $6 ,$ we verify that $g _ { k } ( \eta ; \widehat { P } _ { n } )$ is Lipschitz in the data vector $Z _ { 1 } ^ { n }$ by using the following elementary result.

Lemma 7. The map $\begin{array} { r } { \mathbb { R } ^ { n } \ni y \mapsto \left( \frac { 1 } { n } \sum _ { i = 1 } ^ { n } | y _ { i } | ^ { k _ { * } } \right) ^ { \frac { 1 } { k _ { * } } } } \end{array}$ is $n ^ { - \frac { 1 } { 2 \vee k * } } - L$ ipschitz with respect to the $\left\| \cdot \right\| _ { 2 } - n o r m$

Proof of Lemma We denote $\begin{array} { r } { \| Y \| _ { L ^ { p } ( \widehat { P } _ { n } ) } = \left( \frac { 1 } { n } \sum _ { i = 1 } ^ { n } | y _ { i } | ^ { p } \right) ^ { \frac { 1 } { p } } } \end{array}$ to ease notation. Noting that

$$
\| \psi_ {n} (y) \| _ {2} = n ^ {- \frac {1}{2}} \left(\frac {\| Y \| _ {L ^ {2 (k _ {*} - 1)} (\widehat {P} _ {n})}}{\| Y \| _ {L ^ {k _ {*}} (\widehat {P} _ {n})}}\right) ^ {k _ {*} - 1},
$$

we proceed in two cases. If $k _ { * } \leq 2$ , the result follows from $\left\| Y \right\| _ { L ^ { 2 ( k _ { * } - 1 ) } ( \widehat { P } _ { n } ) } \leq \left\| Y \right\| _ { L ^ { k _ { * } } ( \widehat { P } _ { n } ) }$ . If $k _ { * } \ge 2$ $\begin{array} { r } { \left( \sum _ { i = 1 } ^ { n } | y _ { i } | ^ { 2 ( k _ { * } - 1 ) } \right) ^ { \frac { 1 } { 2 ( k _ { * } - 1 ) } } \le \left( \sum _ { i = 1 } ^ { n } | y _ { i } | ^ { k _ { * } } \right) ^ { \frac { 1 } { k _ { * } } } } \end{array}$ implies

$$
\left\| Y \right\| _ {L ^ {2 (k _ {*} - 1)} (\widehat {P} _ {n})} \leq n ^ {- \frac {1}{k _ {*}} + \frac {1}{2 (k _ {*} - 1)}} \left\| Y \right\| _ {L ^ {k _ {*}} (\widehat {P} _ {n})},
$$

which gives the result.

Lemma 7 implies $g _ { k } ( \eta ; \widehat { P } _ { n } )$ is $\mathrm { ~ a ~ } c _ { k } n ^ { - \frac { 1 } { 2 \vee k _ { * } } }$ -Lipschitz function of the data vector $Z _ { 1 } ^ { n }$ with respect to the $\lVert \cdot \rVert _ { 2 } \mathrm { - n o r m }$ . Applying Lemma 6, for any fixed $\eta \in [ - \frac { 1 } { c _ { k } - 1 } M , M ]$

$$
\left| g _ {k} \left(\eta ; \widehat {P} _ {n}\right) - \mathbb {E} _ {P _ {0}} \left[ g _ {k} \left(\eta ; \widehat {P} _ {n}\right) \right] \right| \leq \sqrt {2 t} c _ {k} \left(\frac {c _ {k}}{c _ {k} - 1} \vee 2\right) M n ^ {- \frac {1}{k * \vee 2}}\tag{28}
$$

with probability at least $1 - 2 e ^ { - t }$

To establish pointwise concentration of $g _ { k } ( \eta ; \widehat { P } _ { n } )$ to $g _ { k } ( \eta ; P _ { 0 } )$ , it remains to see that $\mathbb { E } _ { P _ { 0 } } [ g _ { k } ( \eta ; \widehat { P } _ { n } ) ]$ and $g _ { k } ( \eta ; P _ { 0 } )$ are close. We use the following lemma, whose proof we defer to Section C.1.1.

Lemma 8. Let $k _ { * } \in [ 1 , \infty )$ and let $Y _ { i }$ be an i.i.d. sequence of random variables satisfying $\mathbb { E } [ | Y | ^ { 2 k _ { * } } ] \le$ $C ^ { k _ { * } } \mathbb { E } [ | Y | ^ { k _ { * } } ]$ for some $C \in \mathbb { R } _ { + }$ . For any $k _ { * } \in [ 1 , \infty )$ , we have

$$
\mathbb {E} \left[ \left(\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {k _ {*}}\right) ^ {\frac {1}{k _ {*}}} \right] \geq \mathbb {E} [ | Y | ^ {k _ {*}} ] ^ {\frac {1}{k _ {*}}} - \frac {2}{k} \sqrt {C} n ^ {- \frac {1}{k _ {*} \vee 2}}\tag{29}
$$

Since $\begin{array} { r } { \mathbb { E } \bigg [ \bigg ( \frac { 1 } { n } \sum _ { i = 1 } ^ { n } | Y _ { i } | ^ { k _ { * } } \bigg ) ^ { \frac { 1 } { k _ { * } } } \bigg ] \leq \mathbb { E } [ | Y | ^ { k _ { * } } ] ^ { \frac { 1 } { k _ { * } } } } \end{array}$ by Jensen’s inequality, Lemma 8 implies

$$
\left| \mathbb {E} _ {P _ {0}} [ g _ {k} (\eta ; \widehat {P} _ {n}) ] - g _ {k} (\eta ; P _ {0}) \right| \leq \frac {2 c _ {k}}{k} \sqrt {\left(\frac {c _ {k}}{c _ {k} - 1} \vee 2\right) M} n ^ {- \frac {1}{k _ {*} \vee 2}}
$$

for any fixed $\eta \in \bigl [ - \frac { 1 } { c _ { k } - 1 } M , M \bigr ]$ . Combining the bound with the concentration result (28), we conclude that with probability at least $1 - 2 e ^ { - 2 t }$

$$
\left. \left| g _ {k} (\eta ; \widehat {P} _ {n}) - g _ {k} (\eta ; P _ {0}) \right] \right| \leq n ^ {- \frac {1}{k * \vee 2}} M c _ {k} \left(\frac {c _ {k}}{c _ {k} - 1} \vee 2\right) \left(\sqrt {2 t} + \frac {2}{k}\right) =: \epsilon_ {t}.\tag{30}
$$

We now show uniform concentration by using a simple covering argument. The following lemma restricts the domain of η to a compact set, which is essential to this argument.

Lemma 9. If $Z \in [ 0 , M ]$ , then for any distribution P

$$
\inf _ {\eta \in \mathbb {R}} g (\eta ; P) = \inf _ {\eta} \left\{g (\eta ; P): \eta \in \left[ - \frac {1}{c _ {k} - 1} M, M \right] \right\}.
$$

Proof of Lemma By definition, $g ( \eta ; P ) = \eta$ for $\eta \geq M$ , and

$$
g \left(- \frac {1}{c _ {k} - 1} M; P\right) \geq c _ {k} \frac {M}{c _ {k} - 1} - \frac {M}{c _ {k} - 1} = M = g (M; P).
$$

Since $\eta \mapsto g ( \eta ; P )$ is convex, this implies the result.

Recalling the shorthand $\begin{array} { r } { \epsilon _ { t , n } : = n ^ { - \frac { 1 } { k _ { * } \vee 2 } } M c _ { k } \left( \frac { c _ { k } } { c _ { k } - 1 } \vee 2 \right) \left( \sqrt { 2 t } + \frac { 2 } { k } \right) } \end{array}$ , define the sequence

$$
\eta_ {i} := - (c _ {k} - 1) ^ {- 1} M + i \epsilon_ {t, n}
$$

for nonnegative integers $\begin{array} { r } { i \le \frac { c _ { k } } { c _ { k } - 1 } \frac { M } { \epsilon _ { t , n } } } \end{array}$ . Then, for any $\eta \in [ - ( c _ { k } - 1 ) ^ { - 1 } M , M ]$ , there exists $1 \leq i ( \eta ) \leq$ $\frac { c _ { k } } { c _ { k } - 1 } \frac { M } { \epsilon _ { t , n } }$ such that $| \eta - \eta _ { i ( \eta ) } | \leq \epsilon _ { t , n } .$

$$
\begin{array}{l} \sup _ {\eta \in [ - (c _ {k} - 1) ^ {- 1} M, M ]} | g (\eta ; \widehat {P} _ {n}) - g (\eta ; P _ {0}) | \\ \leq \sup _ {\eta \in [ - (c _ {k} - 1) ^ {- 1} M, M ]} \Big \{| g (\eta ; \widehat {P} _ {n}) - g (\eta_ {i (\eta)}; \widehat {P} _ {n}) | + | g (\eta_ {i (\eta)}; \widehat {P} _ {n}) - g (\eta_ {i (\eta)}; P _ {0}) | + | g (\eta_ {i (\eta)}; P _ {0}) - g (\eta ; P _ {0}) | \Big \} \\ \leq \max _ {1 \leq i \leq \frac {c _ {k}}{c _ {k} - 1} \frac {M}{\epsilon_ {t , n}}} | g (\eta_ {i (\eta)}; \widehat {P} _ {n}) - g (\eta_ {i (\eta)}; P _ {0}) | + 2 (1 + c _ {k}) \epsilon_ {t, n} \end{array}
$$

where we used $\left( 1 + c _ { k } \right)$ -Lipschitzness of $\eta \mapsto g ( \eta ; P _ { 0 } )$ and $\eta \mapsto g ( \eta ; \widehat { P } _ { n } )$ in the last inequality. Taking the union bound over the pointwise concentration result (30) with $\eta = \eta _ { i }$ , conclude from Lemma 9

$$
\begin{array}{l} \left| \mathcal {R} _ {k} (Z; \widehat {P} _ {n}) - \mathcal {R} _ {k} (Z; P _ {0}) \right| = \left| \inf _ {\eta} g _ {k} (\eta ; \widehat {P} _ {n}) - \inf _ {\eta} g _ {k} (\eta ; P _ {0}) \right| \\ = \left| \inf _ {\eta \in [ - (c _ {k} - 1) ^ {- 1} M, M ]} g _ {k} (\eta ; \widehat {P} _ {n}) - \inf _ {\eta \in [ - (c _ {k} - 1) ^ {- 1} M, M ]} g _ {k} (\eta ; P _ {0}) \right| \\ \leq \sup _ {\eta \in [ - (c _ {k} - 1) ^ {- 1} M, M ]} | g (\eta ; \widehat {P} _ {n}) - g (\eta ; P _ {0}) | \\ \leq (2 c _ {k} + 3) \epsilon_ {t, n} \end{array}
$$

with probability at least $\begin{array} { r } { 1 - 2 \exp \left( - t + \log \frac { c _ { k } } { c _ { k } - 1 } \frac { M } { \epsilon _ { t , n } } \right) } \end{array}$ . Doing a change of variables $t ( s ) = s +$ $\left( { \frac { 1 } { k _ { * } \vee 2 } } + 1 \right) \log n$ , we obtain the final result.

## C.1.1 Proof of Lemma 8

First, we claim that it sufices to show

$$
\begin{array}{l} \mathbb {E} [ | Y | ^ {q} ] ^ {1 / q} \geq \mathbb {E} \left[ \left(\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}\right) ^ {1 / q} \right] \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \geq \mathbb {E} [ | Y | ^ {q} ] ^ {1 / q} - 2 \frac {q - 1}{q} \left\{ \begin{array}{l l} (C ^ {q / 2} \vee 1) \cdot n ^ {- 1 / q} & \text {if q\geq 2} \\ (C \vee C ^ {1 - q / 2}) \cdot n ^ {- 1 / 2} & \text {if q <   2}. \end{array} \right. \end{array}\tag{31}
$$

where the last inequality holds for $n \geq C ^ { q }$ when $q \geq 2$ . To see how our desired bound (29) follows from (31), we use a quick scaling argument. Let $\alpha > 0$ , and note that ${ \mathbb E } [ | \alpha Y | ^ { 2 q } ] \leq ( C \alpha ^ { 2 } ) ^ { q } { \mathbb E } [ | Y | ^ { q } ]$ by assumption. Let $\sigma _ { n } : = \mathbb { E } [ ( { \textstyle \frac { 1 } { n } } \sum _ { i = 1 } ^ { n } | Y _ { i } | ^ { q } ) ^ { 1 / q } ]$ and $\sigma = \mathbb { E } [ | Y | ^ { q } ] ^ { 1 / q }$ for shorthand. First, if $q \geq 2$ , we have $( \alpha ^ { 2 } C ) ^ { q / 2 } \geq 1$ if $\alpha \geq C ^ { - \frac { 1 } { 2 } }$ , and we obtain

$$
\alpha \sigma_ {n} \geq \alpha \sigma - 2 \frac {q - 1}{q} \alpha^ {q} C ^ {q / 2} n ^ {- 1 / q} \text {or} \sigma_ {n} \geq \sigma - 2 \frac {q - 1}{q} C ^ {q / 2} \alpha^ {q - 1} n ^ {- 1 / q}.
$$

Choosing $\alpha = C ^ { - \frac { 1 } { 2 } }$ gives the result (29) when $q \geq 2$ . For $q < 2$ , we similarly obtain that $C \alpha ^ { 2 } \geq$ $( C \alpha ^ { 2 } ) ^ { 1 - q / 2 }$ for $\alpha \geq C ^ { - { \frac { 1 } { 2 } } }$ , whence we have the lower bound

$$
\alpha \sigma_ {n} \geq \alpha \sigma - 2 \frac {q - 1}{q} C \alpha^ {2} n ^ {- 1 / 2} \mathrm{or} \sigma_ {n} \geq \sigma - 2 \frac {q - 1}{q} C \alpha n ^ {- 1 / 2}
$$

for $\alpha \geq C ^ { - { \frac { 1 } { 2 } } }$ . Choosing $\alpha = C ^ { - \frac { 1 } { 2 } }$ thus gives the desired result (29).

Now, we proceed to show the bound (31). Let

$$
\gamma_ {n} = \underset {\gamma \geq 0} {\operatorname{argmin}} \left\{\frac {1}{(q - 1)} \frac {\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}}{\gamma^ {q - 1}} + \gamma \right\} = \left(\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}\right) ^ {1 / q}
$$

so that

$$
\frac {1}{q} \frac {\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}}{\gamma_ {n} ^ {q - 1}} + \frac {(q - 1) \gamma_ {n}}{q} = \left(\frac {1}{q} + \frac {q - 1}{q}\right) \left(\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}\right) ^ {1 / q} = \left(\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}\right) ^ {1 / q}.
$$

For any $\gamma \geq 0$ we have by the first order inequality for convexity (as the function $\gamma \mapsto 1 / \gamma ^ { q - 1 } + \gamma$ is convex for $\gamma \geq 0 )$ that

$$
\begin{array}{l} \left(\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}\right) ^ {1 / q} = \frac {\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}}{q \gamma_ {n} ^ {q - 1}} + \frac {q - 1}{q} \gamma_ {n} \\ \qquad \qquad \qquad \geq \frac {\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}}{q \gamma^ {q - 1}} + \frac {q - 1}{q} \gamma + \left(\frac {q - 1}{q} - \frac {(q - 1) \frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}}{q \gamma^ {q}}\right) (\gamma_ {n} - \gamma). \end{array}\tag{32}
$$

We now show how to provide a bound on magnitude of the final term in expression (32).

Let $\sigma ^ { q } = \mathbb { E } [ | Y | ^ { q } ]$ , and choose $\gamma ^ { q } = \operatorname* { m a x } \{ n ^ { - \alpha } , \sigma ^ { q } \}$ , where $\alpha \geq 0$ is a power to be chosen. Then

$$
\begin{array}{r l r} & & {\mathbb {E} \left[ \left(\frac {q - 1}{q} - \frac {(q - 1) \frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}}{q \gamma^ {q}}\right) ^ {2} \right] = \left(\frac {q - 1}{q}\right) ^ {2} \mathbb {E} \left[ \left(1 - \frac {\sigma^ {q}}{\gamma^ {q}} + \frac {\sigma^ {q}}{\gamma^ {q}} - \frac {\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}}{\gamma^ {q}}\right) ^ {2} \right]} \\ & & {= \left(\frac {q - 1}{q}\right) ^ {2} \left[ (1 - \sigma^ {q} / \gamma^ {q}) ^ {2} + \frac {1}{\gamma^ {2 q} n} \mathrm{Var} (| Y | ^ {q}) \right],} \end{array}
$$

and noting that $\mathrm { V a r } ( | Y | ^ { q } ) \leq \mathbb { E } [ | Y | ^ { 2 q } ] \leq C ^ { q } \mathbb { E } [ | Y | ^ { q } ] = C ^ { q } \sigma ^ { q }$ , we have

$$
\frac {1}{\gamma^ {2 q} n} \mathrm{Var} (| Y | ^ {q}) \leq \frac {1}{n} \frac {C ^ {q} \sigma^ {q}}{\max \{n ^ {- 2 \alpha} , \sigma^ {2 q} \}} = C ^ {q} \min \left\{\frac {\sigma^ {q}}{n ^ {1 - 2 \alpha}}, \frac {1}{n \sigma^ {q}} \right\}.
$$

and

$$
1 - \frac {\sigma^ {q}}{\gamma^ {q}} = 1 - \min \left\{n ^ {\alpha} \sigma^ {q}, 1 \right\} = (1 - n ^ {\alpha} \sigma^ {q}) _ {+}.
$$

Now we provide an upper bound on the $( \gamma _ { n } \mathrm { ~ - ~ } \gamma )$ term in the product in inequality (32). By inspection, we have

$$
\begin{array}{l} (\gamma_ {n} - \gamma) ^ {2} = \left(\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}\right) ^ {\frac {2}{q}} - 2 \gamma \gamma_ {n} + \max \left\{n ^ {- \alpha}, \sigma^ {q} \right\} ^ {\frac {2}{q}} \\ \leq \left(\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}\right) ^ {\frac {2}{q}} + \max \left\{n ^ {- \alpha}, \sigma^ {q} \right\} ^ {\frac {2}{q}}. \end{array}\tag{33}
$$

We now state a useful intermediate lemma and consequential inequality, deferring its proof to Section C.1.2.

Lemma 10. Let $q \in [ 1 , 2 ]$ and $a \in [ 1 , 2 ]$ . Then for any random variable $X \geq 0$

$$
\mathbb {E} [ X ^ {a q} ] \leq \mathbb {E} [ X ^ {q} ] ^ {2 - a} \mathbb {E} [ X ^ {2 q} ] ^ {a - 1}.
$$

As an immediate consequence of Lemma 10, we see that for $q \in [ 1 , 2 ]$ and non-negative random variables X, we have that if $\mathbb { E } [ X ^ { 2 q } ] \le C ^ { q } \sigma ^ { q }$ , where $\mathbb { E } [ X ^ { q } ] = \sigma ^ { q }$ , then

$$
\mathbb {E} [ X ^ {2} ] \leq C ^ {2 - q} \sigma^ {q}.\tag{34}
$$

To see this, substitute $a = 2 / q \in [ 1 , 2 ]$ in Lemma 10, which yields

$$
\mathbb {E} [ X ^ {2} ] = \mathbb {E} [ X ^ {a q} ] \leq \mathbb {E} [ X ^ {q} ] ^ {2 - \frac {2}{q}} \mathbb {E} [ X ^ {2 q} ] ^ {\frac {2}{q} - 1} \leq \sigma^ {2 q - 2} (C ^ {q} \sigma^ {q}) ^ {\frac {2}{q} - 1} = C ^ {2 - q} \sigma^ {q}.
$$

Returning to our bound on $( \gamma _ { n } - \gamma )$ , we find via inequality (34) that

$$
\begin{array}{l} \mathbb {E} [ (\gamma_ {n} - \gamma) ^ {2} ] \leq \mathbb {E} [ | Y | ^ {2} ] + \max \{n ^ {- 2 \alpha / q}, \sigma^ {2} \} \\ \qquad \leq \left\{ \begin{array}{l l} \sigma^ {2} + \max \{n ^ {- 2 \alpha / q}, \sigma^ {2} \} & \text {if q\geq 2} \\ C ^ {2 - q} \sigma^ {q} + \max \{n ^ {- 2 \alpha / q}, \sigma^ {2} \} & \text {if q <   2} \end{array} \right. \\ \qquad \leq 2 \left\{ \begin{array}{l l} \max \{n ^ {- 2 \alpha / q}, \sigma^ {2} \} & \text {if q\geq 2} \\ \max \{C ^ {2 - q} \sigma^ {q}, n ^ {- 2 \alpha / q} \} & \text {if q <   2}, \end{array} \right. \end{array}
$$

where we have used that for $q < 2$ we have

$$
\sigma^ {2} = \mathbb {E} [ Y ^ {q} ] ^ {2 / q} \leq \mathbb {E} [ Y ^ {2} ] \leq C ^ {2 - q} \sigma^ {q}.
$$

In particular, we have by H¨older’s inequality that

$$
\begin{array}{l} \mathbb {E} \left[ \left(1 - \frac {\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}}{\gamma^ {q}}\right) (\gamma_ {n} - \gamma) \right] ^ {2} \leq \mathbb {E} \left[ \left(1 - \frac {\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}}{\gamma^ {q}}\right) ^ {2} \right] \mathbb {E} [ (\gamma_ {n} - \gamma) ^ {2} ] \\ \qquad \leq 2 \left((1 - n ^ {\alpha} \sigma^ {q}) _ {+} ^ {2} + C ^ {q} \min \left\{\frac {\sigma^ {q}}{n ^ {1 - 2 \alpha}}, \frac {1}{n \sigma^ {q}} \right\}\right) \cdot \left\{ \begin{array}{l l} \max \{n ^ {- 2 \alpha / q}, \sigma^ {2} \} & \text {if q\geq 2} \\ \max \{n ^ {- 2 \alpha / q}, C ^ {2 - q} \sigma^ {q} \} & \text {if q <   2}. \end{array} \right. \end{array}\tag{35}
$$

We now state a lemma, whose proof we defer to Section C.1.3, which gives us our desired result. Lemma 11. For any $\sigma \geq 0$ , we have

$$
(1 - n ^ {\alpha} \sigma^ {q}) _ {+} ^ {2} \cdot \left\{ \begin{array}{l l} \max \{n ^ {- 2 \alpha / q}, \sigma^ {2} \} & i f q \geq 2 \\ \max \{n ^ {- 2 \alpha / q}, C ^ {2 - q} \sigma^ {q} \} & i f q <   2. \end{array} \right. \leq \left\{ \begin{array}{l l} n ^ {- 2 \alpha / q} & i f q \geq 2 \\ C ^ {2 - q} \min \{\sigma^ {q}, n ^ {- \alpha} \} & i f q <   2. \end{array} \right.\tag{36a}
$$

and

$$
C ^ {q} \min \left\{\frac {\sigma^ {q}}{n ^ {1 - 2 \alpha}}, \frac {1}{n \sigma^ {q}} \right\} \cdot \left\{ \begin{array}{l l} \max \{n ^ {- 2 \alpha / q}, \sigma^ {2} \} & i f q \geq 2 \\ \max \{n ^ {- 2 \alpha / q}, C ^ {2 - q} \sigma^ {q} \} & i f q <   2. \end{array} \right. \leq \left\{ \begin{array}{l l} C ^ {q} \frac {1}{n ^ {1 - \alpha + 2 \alpha / q}} & i f q \geq 2 \\ \max \left\{\frac {C ^ {2}}{n}, \frac {C ^ {q}}{n ^ {1 - \alpha + 2 \alpha / q}} \right\} & i f q <   2. \end{array} \right.\tag{36b}
$$

We now use Lemma 11 to give the remainder of the proof. First, consider the case that $q \geq 2$ Then choosing $\alpha = 1$ we have $\gamma ^ { q } = \operatorname* { m a x } \{ n ^ { - 1 } , \sigma ^ { q } \}$ , and

$$
\left| \mathbb {E} \left[ \left(1 - \frac {\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}}{\gamma^ {q}}\right) (\gamma_ {n} - \gamma) \right] \right| ^ {2} \leq 2 \left[ C ^ {q} n ^ {(1 - 2 / q) \alpha - 1} + n ^ {- (2 / q) \alpha} \right] = \frac {2 (1 + C ^ {q})}{n ^ {2 / q}} \leq 4 \frac {C ^ {q} \vee 1}{n ^ {2 / q}}.
$$

When $q < 2$ , we similarly choose $\alpha = 1$ , which yields

$$
\left| \mathbb {E} \left[ \left(1 - \frac {\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}}{\gamma^ {q}}\right) (\gamma_ {n} - \gamma) \right] \right| ^ {2} \leq 2 \max \left\{\frac {C ^ {2}}{n}, \frac {C ^ {q}}{n ^ {2 / q}} \right\} + 2 \frac {C ^ {2 - q}}{n}.
$$

(Asymptotically, then, we obtain 4 max $\{ C ^ { 2 } , C ^ { 2 - q } \} / n . )$ Referring to inequality (32), we thus have

$$
\mathbb {E} \left[ \left(\frac {1}{n} \sum_ {i = 1} ^ {n} | Y _ {i} | ^ {q}\right) ^ {1 / q} \right] \geq \mathbb {E} [ | Y | ^ {q} ] ^ {1 / q} - 2 \frac {q - 1}{q} \left\{ \begin{array}{l l} (C ^ {q / 2} \vee 1) \cdot n ^ {- 1 / q} & \text {if} q \geq 2 \\ (C \vee C ^ {1 - q / 2}) \cdot n ^ {- 1 / 2} & \text {if} q <   2, \end{array} \right.
$$

which was the desired result.

## C.1.2 Proof of Lemma 10

For any random variable X, we know that for $\gamma \in [ 0 , 1 ]$ and any conjugates $p , q \geq 1$ , that is, $1 / p + 1 / q = 1$ , we have by H¨older’s inequality that

$$
\mathbb {E} [ X ] = \mathbb {E} [ X ^ {\gamma} X ^ {1 - \gamma} ] \leq \mathbb {E} [ X ^ {\gamma p} ] ^ {1 / p} \mathbb {E} [ X ^ {(1 - \gamma) q} ] ^ {1 / q}.
$$

Now, let $X = Y ^ { a q }$ , and take $1 / p = 2 - a$ and $1 / q = a - 1$ . Then we have for any $\gamma \in [ 0 , 1 ]$ that

$$
\mathbb {E} [ Y ^ {a q} ] \leq \mathbb {E} [ Y ^ {\frac {\gamma a q}{2 - a}} ] ^ {2 - a} \mathbb {E} [ Y ^ {\frac {(1 - \gamma) a q}{a - 1}} ] ^ {a - 1}.
$$

If we take $\textstyle \gamma = { \frac { 2 - a } { a } } \in [ 0 , 1 ]$ , then we obtain

$$
\frac {\gamma a}{2 - a} = 1 \text {and} (1 - \gamma) \frac {a}{a - 1} = \frac {2 (a - 1)}{a} \frac {a}{a - 1} = 2.
$$

This gives the result of the lemma.

## C.1.3 Proof of Lemma 11

We begin with inequality (36a). If $\sigma ^ { q } \geq n ^ { - \alpha }$ , the result is trivial, as $\left( 1 - n ^ { \alpha } \sigma ^ { q } \right) _ { + } = 0$ . So we assume that $\sigma ^ { q } < n ^ { - \alpha }$ , which implies that $\sigma ^ { 2 } \ge n ^ { - 2 \alpha / q }$ , and we know that (for $q < 2 ) \ C ^ { 2 - q } \sigma ^ { q } \geq \sigma ^ { 2 }$ . Thus, when $q < 2$ , we have max $\{ n ^ { - 2 \alpha / q } , C ^ { 2 - q } \sigma ^ { q } \} = C ^ { 2 - q } \sigma ^ { q } \leq C ^ { 2 - q } n ^ { - \alpha }$ . If $q \geq 2$ and $\sigma ^ { q } \leq n ^ { - \alpha }$ , then $\sigma ^ { 2 } \le n ^ { - 2 \alpha / q }$ , so that max $\{ { \stackrel { \cdot } { \sigma } } ^ { 2 } , n ^ { - 2 \alpha / q } \} = n ^ { - 2 \alpha / q }$

Now we turn to inequality (36b). First, let us assume that $q \geq 2$ . In this case, we have that if $\sigma ^ { q } \leq n ^ { - \alpha }$ , then the left-hand expression of (36b) has bound

$$
C ^ {q} \min \left\{\frac {\sigma^ {q}}{n ^ {1 - 2 \alpha}}, \frac {1}{n \sigma^ {q}} \right\} n ^ {- 2 \alpha / q} = C ^ {q} \frac {\sigma^ {q}}{n ^ {1 - 2 \alpha + 2 \alpha / q}} \leq C ^ {q} \frac {1}{n ^ {1 - \alpha + 2 \alpha / q}}.
$$

On the other hand, for $\sigma ^ { q } \ge n ^ { - \alpha }$ , we have

$$
C ^ {q} \min \left\{\frac {\sigma^ {q}}{n ^ {1 - 2 \alpha}}, \frac {1}{n \sigma^ {q}} \right\} \sigma^ {2} = C ^ {q} \frac {\sigma^ {2}}{n \sigma^ {q}} = C ^ {q} \frac {1}{n \sigma^ {q - 2}} \leq C ^ {q} \frac {1}{n ^ {1 - \alpha + 2 \alpha / q}},
$$

as $q \geq 2$ and $\sigma \ge n ^ { - \alpha / q }$ . In the case that $q < 2$ in inequality (36b), we are left bounding

$$
\min \left\{\frac {\sigma^ {q}}{n ^ {1 - 2 \alpha}}, \frac {1}{n \sigma^ {q}} \right\} \max \{n ^ {- 2 \alpha / q}, C ^ {2 - q} \sigma^ {q} \}.
$$

Assume first that $n ^ { - 2 \alpha / q } \geq C ^ { 2 - q } \sigma ^ { q }$ , or $\sigma ^ { q } \le C ^ { q - 2 } n ^ { - 2 \alpha / q }$ . In this case, the σ maximizing the left minimum is $\sigma ^ { q } = \operatorname* { m i n } \{ n ^ { - \alpha } , C ^ { q - 2 } n ^ { - 2 \alpha / q } \}$ , which gives

$$
\min \left\{\frac {\sigma^ {q}}{n ^ {1 - 2 \alpha}}, \frac {1}{n \sigma^ {q}} \right\} \max \{n ^ {- 2 \alpha / q}, C ^ {2 - q} \sigma^ {q} \} \leq \frac {1}{n ^ {1 - \alpha + 2 \alpha / q}}.
$$

On the other hand, when $C ^ { 2 - q } \sigma ^ { q } \geq n ^ { - 2 \alpha / q }$ , we obtain that we must maximize (over σ) the quantity

$$
C ^ {2} \min \left\{\frac {\sigma^ {2 q}}{n ^ {1 - 2 \alpha}}, \frac {1}{n} \right\} \leq C ^ {2} \frac {1}{n}.
$$

This gives the desired result.

## C.2 Proof of Corollary 1

Let ${ \mathcal { F } } : = \{ \ell ( \theta ; \cdot ) : \mathcal { X } \to \mathbb { R }$ for $\theta \ \in \ \Theta \}$ be our function class. Fix $t ~ > ~ 0$ and let $N =$ $\begin{array} { r } { N ( \frac { \epsilon _ { t , n } } { 3 } , \mathcal { F } , \| \cdot \| _ { L ^ { \infty } ( \mathcal { X } ) } ) } \end{array}$ to ease notation, so there exists $\{ \theta _ { 1 } , \cdot \cdot \cdot , \theta _ { N } \} \subset { \Theta }$ such that $\{ \ell ( \theta _ { 1 } ; \cdot ) , \cdot \cdot \cdot , \ell ( \theta _ { N } ; \cdot ) \}$ is a $\frac { \epsilon _ { t , n } } { 3 }$ -cover of $\mathcal { F }$ . For any $\theta \in \Theta$ , let $i ( \theta )$ be such that $\begin{array} { r } { \left. \ell ( \theta ; \cdot ) - \ell ( \theta _ { i ( \theta ) } ; \cdot ) \right. _ { L ^ { \infty } ( \mathcal { X } ) } \le \frac { \epsilon _ { t , n } } { 3 } } \end{array}$ . We have

$$
\begin{array}{r l} & {\underset {\theta \in \Theta} {\sup} \left| \mathcal {R} _ {k} (\theta ; \widehat {P} _ {n}) - \mathcal {R} _ {k} (\theta ; P _ {0}) \right|} \\ & {\leq \underset {\theta \in \Theta} {\sup} \left\{\left| \mathcal {R} _ {k} (\theta ; \widehat {P} _ {n}) - \mathcal {R} _ {k} (\theta_ {i (\theta)}; \widehat {P} _ {n}) \right| + \left| \mathcal {R} _ {k} (\theta_ {i (\theta)}; \widehat {P} _ {n}) - \mathcal {R} _ {k} (\theta_ {i (\theta)}; P _ {0}) \right| + \left| \mathcal {R} _ {k} (\theta_ {i (\theta)}; P _ {0}) - \mathcal {R} _ {k} (\theta ; P _ {0}) \right| \right\}} \\ & {\leq \underset {i = 1, \ldots , N} {\max} \left| \mathcal {R} _ {k} (\theta_ {i}; \widehat {P} _ {n}) - \mathcal {R} _ {k} (\theta_ {i}; P _ {0}) \right| + \frac {2 \epsilon_ {t , n}}{3},} \end{array}
$$

where we have used that $\{ \ell ( \theta _ { i } ; \cdot ) \} _ { i = 1 } ^ { N }$ is a $\epsilon _ { t , n } / 3$ cover of F. A union bound now implies

$$
\mathbb {P} \left(\sup _ {\theta \in \Theta} \left| \mathcal {R} _ {k} (\theta ; \widehat {P} _ {n}) - \mathcal {R} _ {k} (\theta ; P _ {0}) \right| \geq \epsilon_ {t, n}\right) \leq N \max _ {i = 1, \dots , N} \mathbb {P} \left(\left| \mathcal {R} _ {k} (\theta_ {i}; \widehat {P} _ {n}) - \mathcal {R} _ {k} (\theta_ {i}; P _ {0}) \right| \geq \epsilon_ {t, n} / 3\right).
$$

Applying Theorem 2 to each $\theta _ { i } ,$ , we obtain the desired result.

## D Proof of Lower Bounds

All results in Section 5 can be alternatively stated as a probabilistic lower bound on the estimation or optimization error

$$
P _ {0} \left(\left| \widehat {R} (Z _ {1} ^ {n}) - \mathcal {R} _ {f} (Z) \right| \geq n ^ {- \frac {1}{2 \vee k _ {*}}}\right), \text {or} P _ {0} \left(\mathcal {R} _ {f} \left(\widehat {\theta} (X _ {1} ^ {n}); P _ {0}\right) - \inf _ {\theta \in \Theta} \mathcal {R} _ {f} (\theta ; P _ {0}) \geq n ^ {- \frac {1}{2 \vee k _ {*}}}\right).
$$

These results follow by using the below identical proofs by noting that

$$
\inf _ {\widehat {\theta} (X _ {1} ^ {n})} \sup _ {P _ {0} \in \mathcal {P}} P _ {0} \left(| \widehat {R} (Z _ {1} ^ {n}) - \mathcal {R} _ {f} (Z) | \geq \delta\right) \geq \frac {1}{2} \left(1 - \| P _ {1} ^ {n} - P _ {2} ^ {n} \| _ {\mathrm{TV}}\right)
$$

whenever $| \mathcal { R } _ { f } ( Z _ { 1 } ) - \mathcal { R } _ { f } ( Z _ { 2 } ) | \ge 2 \delta$ for $Z _ { 1 } \sim P _ { 1 }$ and $Z _ { 2 } \sim P _ { 2 }$ (and similarly for the optimization error).

In the coming proofs related to Section 5.1, we define

$$
\mathfrak {M} _ {n} (\mathcal {P}, f) := \inf _ {\widehat {R}} \sup _ {P _ {0} \in \mathcal {P}} \mathbb {E} _ {P _ {0}} \left[ \left| \widehat {R} (Z _ {1} ^ {n}) - \mathcal {R} _ {k} (Z) \right| \right]
$$

for shorthand, and use it without comment.

## D.1 Proof of Theorem 3

Consider the canonical two point hypothesis testing problem between distributions $P _ { 0 }$ and $P _ { 1 }$ : nature first chooses $v \in \{ 0 , 1 \}$ , then conditioned on v draws $Z _ { 1 } , \ldots , Z _ { n } \stackrel { \mathrm { i i d } } { \sim } P _ { v }$ . Assuming that $| \mathcal { R } _ { k } ( P _ { 0 } ) - \mathcal { R } _ { k } ( P _ { 1 } ) | \ge 2 \delta > 0$ for some $\delta ,$ Le Cam’s classical reduction from estimation to testing [65, 107] yields that

$$
\mathfrak {M} _ {n} (\mathcal {P}, f) \geq \frac {\delta}{2} \left(1 - \| P _ {0} ^ {n} - P _ {1} ^ {n} \| _ {\mathrm{TV}}\right).\tag{37}
$$

We use the bound (37) to give the lower bound by choosing $P _ { 0 }$ and $P _ { 1 }$ so that $\| P _ { 0 } ^ { n } - P _ { 1 } ^ { n } \| _ { \mathrm { T V } } \leq \frac { 1 } { 2 }$ and δ is as large as possible.

First, we show the $O ( n ^ { - \frac { 1 } { 2 } } )$ lower bound. We begin with a technical

Lemma 12. Let $c _ { k } = ( 1 + k ( k - 1 ) \rho ) ^ { \frac { 1 } { k } } , p _ { k } = c _ { k } ^ { - k / ( k - 1 ) }$ , and $\beta _ { k } : = \textstyle \frac 1 2 ( 1 - c _ { k } ^ { - k } )$ . For a pair $z _ { \mathrm { 0 } } \le z _ { \mathrm { 1 } }$ let Z be such that

$$
Z = \left\{ \begin{array}{l l} z _ {0} & w. p. 1 - p \\ z _ {1} & w. p. p. \end{array} \right.
$$

$I f p \geq p _ { k }$ , we have $\mathcal { R } _ { k } ( Z ) = z _ { 1 }$ , and $i f p \le p _ { k }$ , we have $\mathcal { R } _ { k } ( Z ) \leq c _ { k } p ^ { \frac { 1 } { k _ { * } } } z _ { 1 } + ( 1 - c _ { k } p ^ { \frac { 1 } { k _ { * } } } ) z _ { 0 }$ . Further, if $\displaystyle { \dot { } p \leq p _ { k } \wedge ( 1 - ( 1 - \beta ) ^ { 1 - k _ { * } } p _ { k } ) }$ for some $\beta \in ( 0 , 1 )$ , then $\mathcal { R } _ { k } ( Z ) \geq \beta ^ { \frac { 1 } { k } } c _ { k } p ^ { \frac { 1 } { k _ { * } } } z _ { 1 } + ( 1 - \beta ^ { \frac { 1 } { k } } c _ { k } p ^ { \frac { 1 } { k _ { * } } } ) z _ { 0 }$ See Section D.1.1 for a proof.

Now, consider the two distributions $Z _ { 1 } \sim P _ { 1 } , Z _ { 2 } \sim P _ { 2 }$

$$
Z _ {1} = \left\{ \begin{array}{l l} 0 & \text { w.p. } 1 - p _ {k} - \delta \\ M & \text { w.p. } p _ {k} + \delta \end{array} \right., \qquad Z _ {2} = \left\{ \begin{array}{l l} 0 & \text { w.p. } 1 - p _ {k} + \delta \\ M & \text { w.p. } p _ {k} - \delta \end{array} \right.
$$

for some $0 < \delta \leq p _ { k } \land ( 1 - p _ { k } )$ to be chosen later. Note that $p _ { k } = c _ { k } ^ { - k _ { * } } < 1$ as $c _ { k } > 1$ . We use the version of $Z _ { 1 }$ and $Z _ { 2 }$ such that $Z _ { 1 } ( \cdot )$ and $Z _ { 2 } ( \cdot )$ are upper semi-continuous.

From Lemma 12, we have that $\mathcal { R } _ { k } ( Z _ { 1 } ) = M$ and $\mathcal { R } _ { k } ( Z _ { 2 } ) \leq M c _ { k } ( p _ { k } - \delta ) ^ { \frac { 1 } { k _ { * } } }$ . Consequently, $P _ { 1 }$ and $P _ { 2 }$ are separated in the robust objective

$$
| \mathcal {R} _ {k} (Z _ {1}) - \mathcal {R} _ {k} (Z _ {2}) | \geq M (1 - c _ {k} (p _ {k} - \delta) ^ {\frac {1}{k _ {*}}}) \geq \frac {c _ {k} ^ {k _ {*}}}{k _ {*}} M \delta
$$

where we used Taylor’s theorem

$$
c _ {k} (p _ {k} - \delta) ^ {\frac {1}{k _ {*}}} = c _ {k} (c _ {k} ^ {- k _ {*}} - \delta) ^ {\frac {1}{k _ {*}}} \leq c _ {k} \left(c _ {k} ^ {- 1} - \frac {1}{k _ {*}} c _ {k} ^ {\frac {k _ {*}}{k}} \delta\right) = 1 - \frac {1}{k _ {*}} c _ {k} ^ {k _ {*}} \delta .
$$

It sufices to show that $\begin{array} { r } { \| P _ { 1 } ^ { n } - P _ { 2 } ^ { n } \| _ { \mathrm { T V } } \leq \frac { 1 } { 2 } } \end{array}$ for $\begin{array} { r } { \delta = \sqrt { \frac { p _ { k } ( 1 - p _ { k } ) } { 8 n } } \wedge \frac { 1 } { 2 } ( 1 - p _ { k } ) \wedge p _ { k } } \end{array}$ . By Pinsker’s inequality, we have $\begin{array} { r } { \| P _ { 1 } ^ { n } - P _ { 2 } ^ { n } \| _ { \mathrm { T V } } ^ { 2 } \leq \frac { n } { 2 } D _ { \mathrm { k l } } \left( P _ { 2 } \| P _ { 1 } \right) } \end{array}$ so it is enough to show $\begin{array} { r } { D _ { \mathrm { k l } } \left( P _ { 2 } \| P _ { 1 } \right) \le \frac { 1 } { n } } \end{array}$ for the given value of $\delta .$ To this end, we note that for $\begin{array} { r } { \delta \le \frac 1 2 ( 1 - p _ { k } ) } \end{array}$ ，

$$
D _ {\mathrm{kl}} \left(P _ {2} \| P _ {1}\right) = (1 - p _ {k} + \delta) \log \frac {1 - p _ {k} + \delta}{1 - p _ {k} - \delta} + (p _ {k} - \delta) \log \frac {p _ {k} - \delta}{p _ {k} + \delta} \leq \frac {8 \delta^ {2}}{p _ {k} (1 - p _ {k})}.
$$

Setting $\begin{array} { r } { \delta = \sqrt { \frac { p _ { k } ( 1 - p _ { k } ) } { 8 n } } \wedge \frac { 1 } { 2 } ( 1 - p _ { k } ) \wedge p _ { k } } \end{array}$ , we then have that $\begin{array} { r } { D _ { \mathrm { k l } } \left( P _ { 2 } \| P _ { 1 } \right) \le \frac { 1 } { n } } \end{array}$

For the second $O ( n ^ { - \frac { 1 } { k _ { * } } } )$ bound, consider the random variables $Z _ { 1 } \sim P _ { 1 }$ and $Z _ { 2 } \sim P _ { 2 }$ with

$$
Z _ {1} \equiv 0, \qquad Z _ {2} = \left\{ \begin{array}{l l} 0 & \text {w.p.} 1 - \delta \\ M & \text {w.p.} \delta \end{array} \right.
$$

for some $\delta > 0$ to be choosen later. We have $\mathcal { R } _ { k } ( Z _ { 1 } ) = 0$ trivially, and since $1 - ( 1 - \beta ) ^ { 1 - k _ { * } } p _ { k } >$ $0 \equiv 1 - c _ { k } ^ { - k } > \beta$ holds for $\beta _ { k } = \textstyle { \frac { 1 } { 2 } } ( 1 - c _ { k } ^ { - k } )$ , we have

$$
\mathcal {R} _ {k} (Z _ {2}) \geq M \beta_ {k} ^ {\frac {1}{k}} c _ {k} \delta^ {\frac {1}{k _ {*}}}
$$

for $0 < \delta \leq p _ { k } \land ( 1 - ( 1 - \beta _ { k } ) ^ { 1 - k _ { * } } p _ { k } )$ by Lemma 12. This gives the the separation $| \mathcal { R } _ { k } ( P _ { 1 } ) - \mathcal { R } _ { k } ( P _ { 2 } ) | \geq$ $M \beta _ { k } ^ { \frac { 1 } { k } } c _ { k } \delta ^ { \frac { 1 } { k _ { * } } }$

Noting that

$$
D _ {\mathrm{kl}} \left(P _ {1} \| P _ {2}\right) = - \log (1 - \delta) \leq \frac {\delta}{1 - \delta} \leq 2 \delta
$$

for $\delta \leq { \frac { 1 } { 2 } }$ , we obtain

$$
\mathfrak {M} _ {n} (\mathcal {P}, f) \geq \frac {1}{4} M \beta_ {k} ^ {\frac {1}{k}} c _ {k} \delta^ {\frac {1}{k _ {*}}} \left(1 - \sqrt {\frac {n}{2} D _ {\mathrm{kl}} \left(P _ {1} \| P _ {2}\right)}\right) \geq \frac {1}{8} M c _ {k} \beta_ {k} ^ {\frac {1}{k}} \delta^ {\frac {1}{k _ {*}}}
$$

where in the first inequality we used the reduction (37) and Pinsker’s inequality as before. The desired result follows by setting $\begin{array} { r } { \delta = \frac { 1 } { 4 n } \wedge p _ { k } \wedge ( 1 - ( 1 - \beta _ { k } ) ^ { 1 - k _ { * } } p _ { k } ) } \end{array}$

## D.1.1 Proof of Lemma 12

Define the objective function in the dual representation (8) as

$$
g (\eta) := c _ {k} \left((1 - p) (z _ {0} - \eta) _ {+} ^ {k _ {*}} + p (z _ {1} - \eta) _ {+} ^ {k _ {*}}\right) ^ {\frac {1}{k _ {*}}} + \eta .
$$

Taking subgradients, we obtain

$$
\partial g (\eta) = \left\{ \begin{array}{l l} 1 & \text {if} \eta > z _ {1} \\ [ 1 - c _ {k} p ^ {\frac {1}{k _ {*}}}, 1 ] & \text {if} \eta = z _ {1} \\ 1 - c _ {k} p ^ {\frac {1}{k _ {*}}} & \text {if} z _ {0} \leq \eta <   z _ {1} \\ 1 - c _ {k} \frac {(1 - p) (z _ {0} - \eta) ^ {\frac {1}{k - 1}} + p (z _ {1} - \eta) ^ {\frac {1}{k - 1}}}{((1 - p) (z _ {0} - \eta) ^ {k _ {*}} + p (z _ {1} - \eta) ^ {k _ {*}}) ^ {\frac {1}{k}}} & \text {if} \eta <   z _ {0}. \end{array} \right.
$$

If $c _ { k } p ^ { \frac { 1 } { k _ { * } } } \geq 1$ then $\eta ^ { * } = \mathrm { a r g m i n } _ { \eta } g ( \eta )$ is attained at $z _ { 1 }$ by convexity, and $R ( P ) = g ( \eta ^ { * } ) = z _ { 1 }$ . If $c _ { k } p ^ { \frac { 1 } { k _ { * } } } < 1$ , we have $\eta ^ { * } \leq z _ { 0 }$ so that

$$
g (\eta^ {*}) \leq g (z _ {0}) = c _ {k} p ^ {\frac {1}{k _ {*}}} z _ {1} + (1 - c _ {k} p ^ {\frac {1}{k _ {*}}}) z _ {0},
$$

which gives the second claim.

For the second inequality, noting that

$$
\mathcal {R} _ {k} (Z) = z _ {0} + \left(z _ {1} - z _ {0}\right) \sup \left\{q \in [ 0, 1 ]: (1 - p) ^ {1 - k} (1 - q) ^ {k} + p ^ {1 - k} q ^ {k} \leq c _ {k} ^ {k} \right\},
$$

it sufices to show that $q = \beta ^ { \frac { 1 } { k } } c _ { k } p ^ { \frac { 1 } { k _ { * } } }$ is feasible when $p \leq 1 - ( 1 - \beta ) ^ { 1 - k _ { * } } p _ { k }$ . Indeed, we have

$$
(1 - p) ^ {1 - k} (1 - \beta^ {\frac {1}{k}} c _ {k} p ^ {\frac {1}{k _ {*}}}) ^ {k} + p ^ {1 - k} (\beta^ {\frac {1}{k}} c _ {k} p ^ {\frac {1}{k _ {*}}}) ^ {k} \leq (1 - p) ^ {1 - k} + \beta c _ {k} ^ {k} \leq c _ {k} ^ {k}
$$

where we used $( 1 - p ) ^ { 1 - k } \leq ( 1 - \beta ) c _ { k } ^ { k }$ in the last inequality.

## D.2 Proof of Proposition 4

We proceed by LeCam’s method as in Theorem 3. Let $Z _ { 1 } \sim P _ { 1 } , Z _ { 2 } \sim P _ { 2 }$ have distribution

$$
Z _ {1} = \left\{ \begin{array}{l l} 0 & \text {w.p.} 1 - p \\ M & \text {w.p.} p, \end{array} \right. \quad Z _ {2} = \left\{ \begin{array}{l l} 0 & \text {w.p.} 1 - p - \delta \\ M & \text {w.p.} p + \delta \end{array} \right.
$$

for some $\delta \in ( 0 , 1 )$ to be chosen later. As before, we show that $\mathcal { R } _ { f } ( Z _ { 1 } )$ and $\mathcal { R } _ { f } ( Z _ { 2 } )$ are wellseparated but $P _ { 1 }$ and $P _ { 2 }$ are close in total variation distance.

By definition, we have

$$
\mathcal {R} _ {f} (Z _ {1}) = \sup \left\{q M: h _ {f} (q; p) \leq \rho , q \in [ 0, 1 ] \right\} = M q (p)
$$

and similarly, $\mathcal { R } _ { f } ( Z _ { 2 } ) = M q ( p + \delta )$ . For δ small enough, the implicit function theorem applies to $h _ { f } ( q ( p ) , p ) = 0$ by our hypothesis. Consequently, we $q ( \cdot )$ is continuously diferentiable on a neighbhorhood of $p$ with

$$
q ^ {\prime} (p) = - \frac {\partial_ {p} h _ {f} (q (p) ; p)}{\partial_ {q} h _ {f} (q (p) ; p)} > 0,
$$

where strict positivity follows by the strict convexity the we assume in the proposition. Taylor’s theorem implies

$$
\mathcal {R} _ {f} (Z _ {2}) - \mathcal {R} _ {f} (Z _ {1}) = q (p + \delta) - q (p) = q ^ {\prime} (p) \delta + o (\delta)
$$

as $\delta \to 0$

We now pick δ such that $\| P _ { 1 } ^ { n } - P _ { 2 } ^ { n } \| _ { \mathrm { T V } } \leq \frac { 1 } { 2 }$ . By Pinsker’s inequality and standard KL vs. χ<sup>2</sup>-divergence inequalities [99, Lemmas 2.5–2.7], we have $\begin{array} { r } { \| P _ { 1 } ^ { n } - P _ { 2 } ^ { n } \| _ { \mathrm { T V } } ^ { 2 } \le \frac { n } { 2 } D _ { \mathrm { k l } } \left( P _ { 1 } \| P _ { 2 } \right) } \end{array}$ ; we will choose δ such that $\begin{array} { r } { D _ { \mathrm { k l } } \left( P _ { 1 } \| P _ { 2 } \right) \le \frac { 1 } { n } } \end{array}$ . For $\delta \in [ 0 , p ]$ , Lemma 2.7 of [99] yields

$$
D _ {\mathrm{kl}} \left(P _ {1} \| P _ {2}\right) \leq \frac {\delta^ {2}}{p} + \frac {\delta^ {2}}{1 - p} = \frac {\delta^ {2}}{p (1 - p)}.
$$

Setting $\delta _ { n } = { \textstyle \sqrt { \frac { p ( 1 - p ) } { n } } }$ , we obtain from the reduction from estimation to hypothesis testing (37) that

$$
\mathfrak {M} _ {n} (\mathcal {P}, f) \geq \frac {M}{8} q ^ {\prime} (p) \sqrt {\frac {p (1 - p)}{n}} + o \left(\frac {1}{\sqrt {n}}\right),
$$

which gives the result.

## D.3 Proof of Proposition 5

We use LeCam’s method and proceed similarly as in the second part of Section D.1. Consider the two distributions $Z _ { 1 } \sim P _ { 1 } , Z _ { 2 } \sim P _ { 2 }$ with

$$
Z _ {1} \equiv 0, \qquad Z _ {2} = \left\{ \begin{array}{l l} 0 & \text {w.p.} 1 - \delta \\ M & \text {w.p.} \delta , \end{array} \right.
$$

where we set $\begin{array} { r } { \delta = \frac { 1 } { 2 ( n \vee C _ { f , \rho , m } ) } } \end{array}$ . Then $\mathcal { R } _ { f } ( Z _ { 1 } ) = 0$ , and to show separation of $\mathcal { R } _ { f } ( Z _ { 2 } )$ , we require a bit of work, beginning with the following lemma.

Lemma 13. For $\begin{array} { r } { \delta = \frac { 1 } { 2 ( n \vee C _ { f , \rho , m } ) } } \end{array}$ , define Q by $\begin{array} { r } { Q ( Z = M ) = \left( \frac { \rho } { 2 m } \right) ^ { \frac { 1 } { k } } \delta ^ { \frac { 1 } { k _ { * } } } } \end{array}$ and $Q ( Z = 0 ) = 1 - Q ( Z =$ M). Then $\begin{array} { r } { D _ { f } \left( Q \| P _ { 2 } \right) \le \rho . } \end{array}$

Proof We have

$$
\begin{array}{l} \delta f \left(\frac {\left(\frac {\rho}{2 m}\right) ^ {\frac {1}{k}} \delta^ {\frac {1}{k _ {*}}}}{\delta}\right) + (1 - \delta) f \left(\frac {1 - \left(\frac {\rho}{2 m}\right) ^ {\frac {1}{k}} \delta^ {\frac {1}{k _ {*}}}}{1 - \delta}\right) \\ \stackrel {(a)} {\leq} \delta f \left(\left(\frac {\rho}{2 m}\right) ^ {\frac {1}{k}} \delta^ {- \frac {1}{k}}\right) + (1 - \delta) f \left(1 - \left(\frac {\rho}{2 m}\right) ^ {\frac {1}{k}} \delta^ {\frac {1}{k _ {*}}}\right) \stackrel {(b)} {\leq} \delta f \left(\left(\frac {\rho}{2 m}\right) ^ {\frac {1}{k}} \delta^ {- \frac {1}{k}}\right) + \frac {\rho}{2} \end{array}
$$

where in step (a), we used that $f$ is non-increasing on (0, 1) along with $\frac { 1 - \left( \frac { \rho } { 2 m } \right) ^ { 1 / k } \delta ^ { 1 / k _ { * } } } { 1 - \delta } \in \left( 0 , 1 \right)$ , and in step (b), we used the definition of $f ^ { - 1 } ( s )$ = inf $\{ t \in [ 0 , 1 ] : f ( t ) \leq s \}$

$$
\left(\frac {\rho}{2 m}\right) ^ {\frac {1}{k}} \delta^ {- \frac {1}{k}} \geq \left\{(n \vee C _ {f, \rho , m}) \rho m ^ {- 1} \right\} ^ {\frac {1}{k}}
$$

$$
f ((\frac {\rho}{2 m}) ^ {1 / k} \delta^ {- 1 / k}) \leq \frac {\rho}{2 \delta}
$$

$$
D _ {f} \left(Q \| P _ {2}\right) \leq \rho
$$

$$
\delta .
$$

As a consequence of Lemma 13, we have $\mathcal { R } _ { f } ( Z _ { 2 } ) \geq M ( \frac { \rho } { 2 m } ) ^ { 1 / k } \delta ^ { 1 / k _ { * } }$ . As $\mathcal { R } _ { f } ( Z _ { 1 } ) = 0$ , we have $\begin{array} { r } { | \mathcal { R } _ { f } ( Z _ { 1 } ) - \mathcal { R } _ { f } ( Z _ { 2 } ) | \ge M ( \frac { \rho } { 2 m } ) ^ { 1 / k } \delta ^ { 1 / k _ { * } } } \end{array}$ . Proceeding similarly as in the last paragraph of Section D.1 we obtain the result.

## D.4 Proof of Theorem 6

Define the optimization distance between two distributions $P _ { 0 }$ and $P _ { 1 }$ (cf. [2, 35]) by

$$
\mathrm{d} _ {\mathrm{opt}} (P _ {0}, P _ {1}; f) := \sup \left\{\delta \geq 0: \begin{array}{l} \mathcal {R} _ {f} (\theta ; P _ {0}) \leq \mathcal {R} _ {f} (\theta_ {0} ^ {*}; P _ {0}) + \delta \quad \text {implies} \mathcal {R} _ {f} (\theta ; P _ {1}) \geq \mathcal {R} _ {f} (\theta_ {1} ^ {*}; P _ {1}) + \delta \\ \mathcal {R} _ {f} (\theta ; P _ {1}) \leq \mathcal {R} _ {f} (\theta_ {1} ^ {*}; P _ {1}) + \delta \text {implies} \mathcal {R} _ {f} (\theta ; P _ {0}) \geq \mathcal {R} _ {f} (\theta_ {0} ^ {*}; P _ {0}) + \delta \end{array} \right\}
$$

where $\theta _ { v } \in \mathrm { a r g m i n } _ { \theta \in \Theta } \mathcal { R } _ { f } ( \theta ; P _ { v } )$ . With this result, we have the following standard lemma, which is a reduction of optimization to testing.

We have the following reduction from distributionally robust optimization to hypothesis testing, which is based on Le Cam’s two-point hypothesis testing reduction.

Lemma 14 (Duchi [35, Chs. 5.1–5.2]). If $P _ { 1 } , P _ { 2 } \in \mathcal { P }$ are such that $d _ { \mathrm { o p t } } ( P _ { 1 } , P _ { 2 } ; f ) \ge \delta$ , then

$$
\begin{array}{r l} & {\mathfrak {M} _ {n} (\mathcal {P}, f, \ell) \geq \delta \inf _ {\widehat {\theta} _ {n}} \sup _ {P _ {0} \in \mathcal {P}} P _ {0} \left(\mathcal {R} _ {f} \left(\widehat {\theta} _ {n} (X _ {1} ^ {n}); P _ {0}\right) - \inf _ {\theta \in \Theta} \mathcal {R} _ {f} (\theta ; P _ {0}) \geq \delta\right)} \\ & {\qquad \qquad \qquad \qquad \qquad \qquad \geq \frac {\delta}{2} \left(1 - \| P _ {1} ^ {n} - P _ {2} ^ {n} \| _ {\mathrm{TV}}\right).} \end{array}
$$

With this inequality in hand, we proceed by We first show the $\Omega ( n ^ { - \frac { 1 } { 2 } } )$ lower bound. Consider the two distributions $X _ { 1 } \sim P _ { 1 } , X _ { 2 } \sim P _ { 2 }$ with

$$
X _ {1} = \left\{ \begin{array}{l l} - 1 & \text {w.p.} 1 - p _ {k} - \delta \\ \epsilon & \text {w.p.} p _ {k} + \delta , \end{array} \right. \qquad X _ {2} = \left\{ \begin{array}{l l} - 1 & \text {w.p.} 1 - p _ {k} + \delta \\ \epsilon & \text {w.p.} p _ {k} - \delta \end{array} \right.
$$

where $\begin{array} { r } { \epsilon = \frac { \delta } { 2 k _ { * } p _ { k } } } \end{array}$ for some $0 < \delta \leq p _ { k } \land ( 1 - p _ { k } )$ to be choosen later. Note that

$$
\mathcal {R} _ {k} (\theta ; P) = \left\{ \begin{array}{l l} \theta \sup _ {Q \ll P} \{\mathbb {E} _ {Q} [ X ]: D _ {f}   (Q \| P) \leq \rho \} & \text { if } \theta \geq 0 \\ \theta \inf _ {Q \ll P} \{\mathbb {E} _ {Q} [ X ]: D _ {f}   (Q \| P) \leq \rho \} & \text { if } \theta <   0. \end{array} \right.
$$

For $\delta \leq 1 - 2 p _ { k }$ , we from Lemma 12 that $\mathcal { R } _ { k } ( \theta ; P _ { 1 } ) = - \theta { \bf 1 } \left\{ \theta < 0 \right\} + \epsilon \theta { \bf 1 } \left\{ \theta \ge 0 \right\}$ and $\mathcal { R } _ { k } ( \theta ; P _ { 2 } ) = - \theta$ when $\theta < 0$ . Now, we have $\mathcal { R } _ { k } ( \theta ; P _ { 2 } ) \le - \epsilon \theta$ when $\theta \ge 0$ since

$$
\sup _ {Q \ll P _ {2}} \{\mathbb {E} _ {Q} [ X _ {2} ]: D _ {f} (Q \| P _ {2}) \leq \rho \} \leq \epsilon c _ {k} (p _ {k} - \delta) ^ {\frac {1}{k _ {*}}} + (c _ {k} (p _ {k} - \delta) ^ {\frac {1}{k _ {*}}} - 1)
$$

$$
\leq \epsilon c _ {k} (p _ {k} - \delta) ^ {\frac {1}{k _ {*}}} - \frac {\delta}{k _ {*} p _ {k}} \leq \epsilon - \frac {\delta}{k _ {*} p _ {k}} = - \epsilon .\tag{38}
$$

Here, we used Taylor’s theorem

$$
c _ {k} (p _ {k} - \delta) ^ {\frac {1}{k _ {*}}} = c _ {k} (c _ {k} ^ {- k _ {*}} - \delta) ^ {\frac {1}{k _ {*}}} \leq c _ {k} \left(c _ {k} ^ {- 1} - \frac {1}{k _ {*}} c _ {k} ^ {\frac {k _ {*}}{k}} \delta\right) = 1 - \frac {1}{k _ {*}} c _ {k} ^ {k _ {*}} \delta .
$$

If we let $\begin{array} { r } { \theta _ { i } ^ { \star } : = \mathrm { a r g m i n } _ { \theta \in \Theta } \mathcal { R } _ { k } ( \theta ; P _ { i } ) } \end{array}$ for $i = 1 , 2 .$ we have $\theta _ { 1 } ^ { \star } = 0 , \theta _ { 2 } ^ { \star } = M$ and $\mathcal { R } _ { k } ( \theta _ { 1 } ^ { \star } ; P _ { 1 } ) = 0$ 2 $\mathcal { R } _ { k } ( \theta _ { 2 } ^ { \star } ; P _ { 2 } ) \le - M \epsilon$ . We then have the following lemma.

Lemma 15. Let the above conditions hold. Then $\begin{array} { r } { d _ { \mathrm { o p t } } ( P _ { 1 } , P _ { 2 } ; f _ { k } ) \ge \frac { \epsilon } { 2 } M } \end{array}$

Proof Let $\theta \in [ - M , M ]$ be such that $\mathcal { R } _ { k } ( \theta ; P _ { 1 } ) \leq \mathcal { R } _ { k } ( \theta _ { 1 } ^ { \star } ; P _ { 1 } ) + M \kappa$ for some $\kappa \in [ 0 , \frac { \epsilon } { 2 } ]$ ]. From $\mathcal { R } _ { k } ( \boldsymbol { \theta } ; P _ { 1 } ) - \mathcal { R } _ { k } ( \boldsymbol { \theta } _ { 1 } ^ { \star } ; P _ { 1 } ) = \mathcal { R } _ { k } ( \boldsymbol { \theta } ; P _ { 1 } ) = - \boldsymbol { \theta } { \mathbf 1 } \{ \boldsymbol { \theta } < 0 \} + \epsilon \boldsymbol { \theta } { \mathbf 1 } \{ \boldsymbol { \theta } > 0 \} \le M \kappa$ , we have $\begin{array} { r } { - \kappa \leq \frac { \theta } { M } \leq \frac { \kappa } { \epsilon } } \end{array}$ Applying this bound, we obtain

$$
\begin{array}{r l} & {\mathcal {R} _ {k} (\theta ; P _ {2}) - \mathcal {R} _ {k} (\theta_ {2} ^ {\star}; P _ {2}) = \left\{ \begin{array}{l l} (\theta - M) \sup _ {Q \ll P _ {2}} \{\mathbb {E} _ {Q} [ X _ {2} ]: D _ {f} (Q \| P _ {2}) \leq \rho \} & \text {if} \theta \geq 0 \\ - \theta - M \sup _ {Q \ll P _ {2}} \{\mathbb {E} _ {Q} [ X _ {2} ]: D _ {f} (Q \| P _ {2}) \leq \rho \} & \text {if} \theta <   0 \end{array} \right.} \\ & {\quad \geq - \theta \mathbf {1} \{\theta <   0 \} - \epsilon \theta \mathbf {1} \{\theta \geq 0 \} + M \epsilon} \\ & {\quad \geq - \theta \mathbf {1} \{\theta <   0 \} - M \kappa \mathbf {1} \{\theta \geq 0 \} + M \epsilon \geq \frac {M \epsilon}{2} \geq M \kappa} \end{array}
$$

where we used the bound (38) to get the second inequality.

On the other hand, assume $\mathcal { R } _ { k } ( \theta ; P _ { 2 } ) \le \mathcal { R } _ { k } ( \theta _ { 2 } ^ { \star } ; P _ { 2 } ) + M \kappa$ . In this case, we claim that $\theta \geq 0$ necessarily. Indeed, if $\theta < 0$ , then using the bound (38),

$$
\mathcal {R} _ {k} (\theta ; P _ {2}) = - \theta \leq \mathcal {R} _ {k} \left(\theta_ {2} ^ {\star}; P _ {2}\right) + M \kappa \leq - M \epsilon + M \kappa = - M (\epsilon - \kappa) <   0
$$

which yields a contradiction. Now, from $\theta \ge 0$ and $\mathcal { R } _ { k } ( \theta ; P _ { 2 } ) \le \mathcal { R } _ { k } ( \theta _ { 2 } ^ { \star } ; P _ { 2 } ) + M \kappa$ , we again obtain from the bound (38)

$$
M \kappa \geq (\theta - \theta_ {2} ^ {\star}) \sup _ {Q \ll P _ {2}} \left\{\mathbb {E} _ {Q} [ X ]: D _ {f} (Q \| P _ {2}) \leq \rho \right\} \geq \epsilon (M - \theta).
$$

Hence, we have $\textstyle { \theta \geq M \left( 1 - { \frac { \kappa } { \epsilon } } \right) }$ , and

$$
\mathcal {R} _ {k} (\theta ; P _ {1}) = \epsilon \theta \geq \epsilon M \left(1 - \frac {\kappa}{\epsilon}\right) = M (\epsilon - \kappa) \geq \frac {M \epsilon}{2} \geq \mathcal {R} _ {k} (\theta_ {1} ^ {\star}; P _ {1}) + M \kappa
$$

for $\kappa \in [ 0 , \frac { \epsilon } { 2 } ]$ . We conclude that the claimed separation in $d _ { \mathrm { o p t } }$ holds.

Now, we argue as in the proof of Theorem 3. Noting that $\begin{array} { r } { D _ { \mathrm { k l } } \left( P _ { 1 } \| P _ { 2 } \right) \le \frac { \delta ^ { 2 } } { p _ { k } \left( 1 - p _ { k } \right) } } \end{array}$ (e.g. [99, Lemma 2.7]) for $0 \leq \delta \leq \left( 1 - p _ { k } \right)$ , let $\delta = \sqrt { \textstyle { \frac { p _ { k } ( 1 - p _ { k } ) } { 2 n } } } \wedge { \textstyle { \frac { 1 } { 2 } } } ( 1 - p _ { k } ) \wedge ( 1 - 2 p _ { k } ) \wedge p _ { k }$ . Then Lemma 14 yields

$$
\mathfrak {M} _ {n} (\mathcal {P}, f _ {k}, \ell) \geq \frac {M \epsilon}{4} \left(1 - \sqrt {\frac {n}{2} D _ {\mathrm{kl}} \left(P _ {1} ^ {\prime} \| P _ {2} ^ {\prime}\right)}\right) \geq \frac {M \delta}{8 k _ {*} p _ {k}},
$$

which gives the first result of the theorem.

Next, we show the second $\Omega ( n ^ { - \frac { 1 } { k _ { * } } } )$ lower bound. Consider the distributions $X _ { 1 } \sim P _ { 1 } , X _ { 2 } \sim P _ { 2 }$

$$
X _ {1} \equiv - \epsilon , \qquad X _ {2} = \left\{ \begin{array}{l l} - \epsilon & \text {w.p.} 1 - \delta \\ 1 & \text {w.p.} \delta \end{array} \right.
$$

where $\begin{array} { r } { \epsilon : = \frac { 1 } { 2 } \beta _ { k } ^ { \frac { 1 } { k } } c _ { k } \delta ^ { \frac { 1 } { k _ { * } } } } \end{array}$ for some $0 < \delta \leq p _ { k } \land ( 1 - p _ { k } ) \land ( 1 - ( 1 - \beta _ { k } ) ^ { 1 - k _ { * } } p _ { k } )$ to be choosen later. Now, we again show that $\begin{array} { r } { \mathrm { d } _ { \mathrm { o p t } } ( P _ { 1 } , P _ { 2 } ; f _ { k } ) \ge \frac { \epsilon } { 2 } } \end{array}$ . To this end, first observe that $\mathcal { R } _ { k } ( \theta ; P _ { 1 } ) = - \epsilon \theta$ . From the first part of Lemma 12, we have $\mathcal { R } _ { k } ( \bar { \theta } ; \mathcal { P } _ { 2 } ) = - \epsilon \theta \ge 0$ when $\theta < 0$ . For $\theta \ge 0$ , the last inequality in Lemma 12 gives

$$
\mathcal {R} _ {k} (\theta ; P _ {2}) \geq \beta_ {k} ^ {\frac {1}{k}} c _ {k} \delta^ {\frac {1}{k _ {*}}} \theta - (1 - \beta_ {k} ^ {\frac {1}{k}} c _ {k} \delta^ {\frac {1}{k _ {*}}}) \epsilon \theta = \left((1 + \epsilon) \beta_ {k} ^ {\frac {1}{k}} c _ {k} \delta^ {\frac {1}{k _ {*}}} - \epsilon\right) \theta \geq \epsilon \theta
$$

since $\begin{array} { r } { \epsilon = \frac { 1 } { 2 } \beta _ { k } ^ { \frac { 1 } { k } } c _ { k } \delta ^ { \frac { 1 } { k _ { * } } } } \end{array}$ . Denoting $\begin{array} { r } { \theta _ { i } ^ { \star } : = \mathrm { a r g m i n } _ { \theta \in \Theta } \mathcal { R } _ { k } ( \theta ; P _ { i } ) } \end{array}$ again, we consequently obtain $\theta _ { 1 } ^ { \star } = M$ $\theta _ { 2 } ^ { \star } = 0$ with $\ddot { \mathcal { R } } _ { k } ( \theta _ { 1 } ^ { \star } ; P _ { 1 } ) = - M \epsilon , \mathcal { R } _ { k } ( \theta _ { 2 } ^ { \star } ; P _ { 2 } ) = \bar { 0 }$

Next, we show $\begin{array} { r } { \mathrm { d } _ { \mathrm { o p t } } ( P _ { 1 } , P _ { 2 } ; f _ { k } ) \ge \frac { M \epsilon } { 2 } } \end{array}$ . Assume that $\theta \in [ - M , M ]$ satisfies $\mathcal { R } _ { k } ( \theta ; P _ { 1 } ) \le \mathcal { R } _ { k } ( \theta _ { 1 } ^ { \star } ; P _ { 1 } ) +$ $\begin{array} { r } { M \kappa = - M \epsilon + M \kappa \equiv \theta \geq M \left( 1 - \frac { \kappa } { \epsilon } \right) } \end{array}$ for some $\kappa \in [ 0 , \frac { \epsilon } { 2 } ]$ . This implies

$$
\mathcal {R} _ {k} (\theta ; P _ {2}) \geq M \epsilon \left(1 - \frac {\kappa}{\epsilon}\right) \geq M \frac {\epsilon}{2} = \mathcal {R} _ {k} (\theta_ {2} ^ {\star}; P _ {2}) + \frac {M \epsilon}{2} \geq \mathcal {R} _ {k} (\theta_ {2} ^ {\star}; P _ {2}) + M \kappa .
$$

On the other hand, if $\mathcal { R } _ { k } ( \theta ; P _ { 2 } ) \le \mathcal { R } _ { k } ( \theta _ { 2 } ^ { \star } ; P _ { 2 } ) + M \kappa$ then $\epsilon | \theta | \leq { \mathcal { R } } _ { k } ( \theta ; P _ { 2 } ) \leq M \kappa$ so that $\begin{array} { r } { | \theta | \le \frac { M \kappa } { \epsilon } } \end{array}$ Consequently, we have

$$
\begin{array}{r l} & {\mathcal {R} _ {k} (\theta ; P _ {1}) = - \epsilon \theta \geq - M \kappa = M (- \epsilon + \epsilon - \kappa)} \\ & {\qquad \geq M \left(- \epsilon + \frac {\epsilon}{2}\right) = \mathcal {R} _ {k} (\theta_ {1} ^ {\star}; P _ {1}) + \frac {M \epsilon}{2} \geq \mathcal {R} _ {k} (\theta_ {1} ^ {\star}; P _ {1}) + M \kappa} \end{array}
$$

and we conclude $\begin{array} { r } { \mathrm { d } _ { \mathrm { o p t } } ( P _ { 1 } , P _ { 2 } ; f _ { k } ) \ge \frac { M \epsilon } { 2 } } \end{array}$

Proceeding as in the proof of the second part of Theorem $^ { 3 , }$ we note that $D _ { \mathrm { k l } } \left( P _ { 1 } \Vert P _ { 2 } \right) \leq 2 \delta$ when $\delta \leq { \frac { 1 } { 2 } }$ . Setting $\begin{array} { r } { \delta = \frac { 1 } { 4 n } \wedge p _ { k } \wedge ( 1 - ( 1 - \beta _ { k } ) ^ { 1 - k _ { * } } p _ { k } ) } \end{array}$ , we conclude

$$
\mathfrak {M} _ {n} (\mathcal {P}, f, \ell) \geq \frac {M}{1 6} \beta_ {k} ^ {\frac {1}{k}} c _ {k} \delta^ {\frac {1}{k _ {*}}} = \frac {M}{1 6} \beta_ {k} ^ {\frac {1}{k}} c _ {k} \left(\frac {1}{4 n} \wedge p _ {k} \wedge (1 - (1 - \beta_ {k}) ^ {1 - k _ {*}} p _ {k})\right) ^ {\frac {1}{k _ {*}}}.
$$

## D.5 Proof of Proposition 7

For p given by hypothesis, recall the definition (17) of $q ( p )$ . Following the same logic as in the proof of Proposition 4, the implicit function theorem implies that $q ( \cdot )$ is continuously diferentiable near $p$ with

$$
q ^ {\prime} (p) = \frac {- \partial_ {p} h _ {f} (q (p) ; p)}{\partial_ {q} h _ {f} (q (p) ; p)} > 0,
$$

where $\begin{array} { r } { h _ { f } ( q ; p ) = p f ( \frac { q } { p } ) + ( 1 - p ) f ( \frac { 1 - q } { 1 - p } ) } \end{array}$ as before. From Taylor’s theorem, we then have

$$
q (p + \delta) = q (p) + q ^ {\prime} (p) \delta + r (\delta)
$$

for a remainder $r ( \delta ) = o ( \delta )$ as $\delta \to 0$ . For small $\delta > 0$ , define

$$
\epsilon_ {\delta} := \left(q (p) + \frac {1}{2} \left(q ^ {\prime} (p) \delta + r (\delta)\right)\right) ^ {- 1} - 1 > 0.
$$

We use the reduction from robust optimization to testing of Lemma 14. For some $\delta \in ( 0 , q ( p ) - p )$ to be choosen later, consider the two distributions $X _ { 1 } \sim P _ { 1 } , X _ { 2 } \sim P _ { 2 }$ with

$$
X _ {1} = \left\{ \begin{array}{l l} - 1 & \text {w.p.} 1 - p \\ \epsilon_ {\delta} & \text {w.p.} p, \end{array} \right. \qquad X _ {2} = \left\{ \begin{array}{l l} - 1 & \text {w.p.} 1 - p - \delta \\ \epsilon_ {\delta} & \text {w.p.} p + \delta . \end{array} \right.
$$

For $\ell ( \theta ; X ) = \theta X$ , we show that $\theta \mapsto \mathscr { R } _ { f } ( \theta ; P _ { 1 } )$ and $\theta \mapsto \mathscr { R } _ { f } ( \theta ; P _ { 2 } )$ are well-separated in the distance $\mathrm { d _ { o p t } } ( \cdot , \cdot )$ , but $P _ { 1 }$ and $P _ { 2 }$ are close in total variation distance. By definition

$$
\mathcal {R} _ {f} (\theta ; P _ {1}) = \left\{ \begin{array}{l l} - \theta (1 - (1 + \epsilon_ {\delta}) q (p)) & \text {if} \theta \geq 0 \\ - \theta (- \epsilon_ {\delta} + (1 + \epsilon_ {\delta}) q (1 - p)) & \text {otherwise}, \end{array} \right.
$$

and similarly,

$$
\mathcal {R} _ {f} (\theta ; P _ {2}) = \left\{ \begin{array}{l l} - \theta (1 - (1 + \epsilon_ {\delta}) q (p + \delta)) & \text {if} \theta \geq 0 \\ - \theta (- \epsilon_ {\delta} + (1 + \epsilon_ {\delta}) q (1 - p - \delta)) & \text {otherwise.} \end{array} \right.
$$

By our choice of $\epsilon _ { \delta } .$ observe

$$
1 - (1 + \epsilon_ {\delta}) q (p) > 0, \quad \text { but } \quad 1 - (1 + \epsilon_ {\delta}) q (p + \delta) \leq 0,
$$

and $q ( p ) > p$ so that $q ( p ) > p + \delta$ for small $\delta ,$ and similarly $q ( 1 - p - \delta ) + \delta > 1 - p$ . Consequently, $\begin{array} { r } { 1 + \epsilon _ { \delta } < \frac { 1 } { q ( p ) } < \frac { 1 } { p + \delta } < \frac { 1 } { 1 - q ( 1 - p - \delta ) } } \end{array}$ , and so

$$
- \epsilon_ {\delta} + (1 + \epsilon_ {\delta}) q (1 - p) \geq - \epsilon_ {\delta} + (1 + \epsilon_ {\delta}) q (1 - p - \delta) > 0.
$$

Thus, we have $\mathcal { R } _ { f } ^ { \prime } ( \theta ; P _ { 1 } ) < 0$ for all θ, while $\mathcal { R } _ { f } ^ { \prime } ( \theta ; P _ { 2 } ) > 0$ for $\theta > 0$ and $\mathcal { R } _ { f } ^ { \prime } ( \theta ; P _ { 2 } ) < 0$ for $\theta < 0$ We conclude that $\begin{array} { r } { \theta _ { i } ^ { \star } : = \mathrm { a r g m i n } _ { \theta \in [ - M , M ] } \mathcal { R } _ { f } ( \theta ; \dot { P } _ { i } ) } \end{array}$ satisfies $\theta _ { 1 } ^ { \star } = M$ and $\theta _ { 2 } ^ { \star } = 0$

We now show $\mathrm { d } _ { \mathrm { o p t } } ( P _ { 1 } , P _ { 2 } ) \geq \dot { M } \Delta _ { \delta }$ , where

$$
\Delta_ {\delta} := \frac {q ^ {\prime} (p) \delta + r (\delta)}{4 \left(q (p) + \frac {1}{2} (q ^ {\prime} (p) \delta + r (\delta)\right)} = \frac {1}{4} (1 + \epsilon_ {\delta}) \left(q ^ {\prime} (p) \delta + r (\delta)\right).
$$

In the sequel, we use the following identities to simplify computation:

$$
2 \Delta_ {\delta} = 1 - (1 + \epsilon_ {\delta}) q (p), \quad \text { and } \quad - 2 \Delta_ {\delta} = 1 - (1 + \epsilon_ {\delta}) q (p + \delta).
$$

First, for any $\kappa \in [ 0 , \Delta _ { \delta } ]$ , consider θ such that

$$
\mathcal {R} _ {f} (\theta ; P _ {1}) \leq \mathcal {R} _ {f} (\theta_ {1} ^ {\star}; P _ {1}) + M \kappa .
$$

Assume for contradiction that $\theta < 0$ : the above bound implies

$$
\begin{array}{r l} & {\theta \geq \frac {M}{- \epsilon_ {\delta} + (1 + \epsilon_ {\delta}) q (1 - p)} (1 - (1 + \epsilon_ {\delta}) q (p) - \kappa)} \\ & {\quad = \frac {M}{- \epsilon_ {\delta} + (1 + \epsilon_ {\delta}) q (1 - p)} (2 \Delta_ {\delta} - \kappa) \geq 0.} \end{array}
$$

For $\theta \ge 0$ , the optimality bound implies

$$
\theta \geq M \left(1 - \frac {\kappa}{1 - (1 + \epsilon_ {\delta}) q (p)}\right) = M \left(1 - \frac {\kappa}{2 \Delta_ {\delta}}\right).
$$

Using this bound, we obtain

$$
\begin{array}{c} \mathcal {R} _ {f} (\theta ; P _ {2}) - \mathcal {R} _ {f} (\theta_ {2} ^ {\star}; P _ {2}) = \mathcal {R} _ {f} (\theta ; P _ {2}) = - (1 - (1 + \epsilon_ {\delta}) q (p + \delta)) \theta = 2 M \Delta_ {\delta} \left(1 - \frac {\kappa}{2 \Delta_ {\delta}}\right) \\ \geq M \left(2 \Delta_ {\delta} - \kappa\right) \geq M \kappa . \end{array}
$$

Next, for any $\kappa \in [ 0 , \Delta _ { \delta } ]$ , consider θ such that

$$
\mathcal {R} _ {f} (\theta ; P _ {2}) \leq \mathcal {R} _ {f} (\theta_ {2} ^ {\star}; P _ {2}) + M \kappa = M \kappa ,
$$

which implies $\begin{array} { r } { \theta \leq - \frac { M \kappa } { 1 - ( 1 + \epsilon _ { \delta } ) q ( p + \delta ) } ~ \mathrm { i f } ~ \theta \geq 0 } \end{array}$ , and $\begin{array} { r } { \theta \geq \frac { M \kappa } { - \epsilon _ { \delta } + ( 1 + \epsilon _ { \delta } ) q ( 1 - p - \delta ) } } \end{array}$ if $\theta < 0$ . When $\theta \ge 0$ , we then obtain

$$
\mathcal {R} _ {f} (\theta ; P _ {1}) - \mathcal {R} _ {f} (\theta_ {1} ^ {\star}; P _ {1}) = (1 - (1 + \epsilon_ {\delta}) q (p)) (M - \theta) \geq 2 M \Delta_ {\delta} \left(1 + \frac {\kappa}{2 \Delta_ {\delta}}\right) \geq M \kappa .
$$

When $\theta < 0$ , we get

$$
\mathcal {R} _ {f} (\theta ; P _ {1}) - \mathcal {R} _ {f} (\theta_ {1} ^ {\star}; P _ {1}) \geq M \kappa \left(\frac {- \epsilon_ {\delta} + (1 + \epsilon_ {\delta}) q (1 - p)}{- \epsilon_ {\delta} + (1 + \epsilon_ {\delta}) q (1 - p - \delta)} + 2\right) \geq M \kappa .
$$

We thus conclude that $\mathrm { d } _ { \mathrm { o p t } } ( P _ { 1 } , P _ { 2 } ) \geq M \Delta _ { \delta }$ as claimed.

We now pick δ such that $\| P _ { 1 } ^ { n } - P _ { 2 } ^ { n } \| _ { \mathrm { T V } } \leq \frac { 1 } { 2 }$ . By Pinsker’s inequality, we have $\| P _ { 1 } ^ { n } - P _ { 2 } ^ { n } \| _ { \mathrm { T V } } ^ { 2 } \leq$ ${ \begin{array} { r l } { { \frac { n } { 2 } } D _ { \mathrm { k l } } \left( P _ { 1 } \| P _ { 2 } \right) } \end{array} }$ , and letting $\delta _ { n } \ = \ { \sqrt { \frac { p ( 1 - p ) } { n } } }$ , we get $\begin{array} { r } { D _ { \mathrm { k l } } \left( P _ { 1 } \| P _ { 2 } \right) \le \frac { 1 } { n } } \end{array}$ as for $\delta \in [ 0 , p ]$ , we have as usual that $\begin{array} { r } { D _ { \mathrm { k l } } \left( P _ { 1 } \| P _ { 2 } \right) \le \frac { \delta ^ { 2 } } { p ( 1 - p ) } } \end{array}$ . From the reduction from distributionally robust optimization to hypothesis testing (Lemma 14), we conclude

$$
\mathfrak {M} _ {n} (\mathcal {P}, f, \ell) \geq \frac {M}{4} \Delta_ {\delta_ {n}}.
$$

Multiplying both sides by $\sqrt { n }$ and taking $n \to \infty$ , we obtain the result.

## D.6 Proof of Proposition 8

We proceed as in the second part of Section D.4. We use Lemma 14 on the distributions $X _ { 1 } \sim P _ { 1 }$ $X _ { 2 } \sim P _ { 2 }$

$$
X _ {1} \equiv - \epsilon , \qquad X _ {2} = \left\{ \begin{array}{l l} - \epsilon & \text { w.p. } 1 - \delta \\ 1 & \text { w.p. } \delta \end{array} \right.
$$

where $\begin{array} { r } { \epsilon : = \left( \frac { \rho } { 2 m } \right) ^ { \frac { 1 } { k } } \delta ^ { \frac { 1 } { k _ { * } } } } \end{array}$ for some

$$
0 <   \delta \leq \frac {1}{2 C _ {f , \rho , m}} \wedge \frac {\rho}{2 m} \left(\left(\frac {2}{3}\right) ^ {k} \wedge \frac {1}{2} \left(\frac {\rho}{2 m}\right) ^ {- k _ {*}}\right)
$$

to be choosen later. Now, we again show that $\mathrm { d _ { o p t } } ( P _ { 1 } , P _ { 2 } ; f ) \ge { \frac { \epsilon } { 2 } }$ . To this end, first observe that $\mathcal { R } _ { f } ( \theta ; P _ { 1 } ) = - \epsilon \theta$ . When $\theta < 0$ , we have $\begin{array} { r } { \mathcal { R } _ { f } ( \theta ; P _ { 2 } ) \ge \theta \mathbb { E } [ X _ { 2 } ] \ge - \theta ( \epsilon ( 1 - \delta ) - \delta ) \ge 0 \mathrm { ~ a s ~ } \epsilon \le } \end{array}$ $\epsilon \leq \frac { 1 } { 2 }$ in the given range of δ. When $\theta \geq 0$ , recall that Q such that $\begin{array} { l } { \displaystyle { Q ( Z = M ) = \left( \frac { \rho } { 2 m } \right) ^ { \frac { 1 } { k } } \delta ^ { \frac { 1 } { k _ { * } } } } } \end{array}$ and $Q ( Z = 0 ) = 1 - Q ( Z = M )$ , satisfies $D _ { f } \left( Q \| P _ { 2 } \right) \leq \rho$ by Lemma 13. Hence, we have for $\theta \ge 0$

$$
\mathcal {R} _ {f} (\theta ; P _ {2}) \geq \epsilon \theta .
$$

Denoting $\begin{array} { r } { \theta _ { i } ^ { \star } : = \operatorname * { a r g m i n } _ { \theta \in \Theta } \mathcal { R } _ { f } ( \theta ; P _ { i } ) } \end{array}$ again, we consequently obtain $\theta _ { 1 } ^ { \star } = M , \theta _ { 2 } ^ { \star } = 0$ with $\mathcal { R } _ { f } ( \theta _ { 1 } ^ { \star } ; P _ { 1 } ) =$ $- M \epsilon , \mathcal { R } _ { f } ( \theta _ { 1 } ^ { \star } ; P _ { 2 } ) = 0$

Using an identical argument as in the second part of Section D.4, we can show $\operatorname { d } _ { \mathrm { o p t } } ( P _ { 1 } , P _ { 2 } ; f ) \ge$ $\frac { M \epsilon } { 2 }$ . Setting

$$
\delta = \frac {1}{2 (n \vee C _ {f , \rho , m})} \wedge \frac {\rho}{2 m} \left(\left(\frac {2}{3}\right) ^ {k} \wedge \frac {1}{2} \left(\frac {\rho}{2 m}\right) ^ {- k _ {*}}\right)
$$

and using the same argument as in Section D.4, we obtain the result.

## E Proofs of Consistency

We begin this section with a brief review of the theory of epi-convergence [59, 79], which governs convergence of solutions to optimization problems, so we consequently use its tools to develop our consistency results.

We begin with some necessary set-valued analysis.

Definition 1. Let $\left\{ A _ { n } \right\}$ be a sequence of subsets of $\mathbb { R } ^ { d }$ . The limit supremum (or limit exterior or outer limit) and limit infimum (limit interior or inner limit) of the sequence $\left\{ A _ { n } \right\}$ are

$$
\begin{array}{l} \underset {n} {\limsup} A _ {n} := \left\{v \in \mathbb {R} ^ {d} \mid \underset {n \to \infty} {\liminf} \operatorname{dist} (v, A _ {n}) = 0 \right\} \quad a n d \\ \underset {n} {\liminf} A _ {n} := \left\{v \in \mathbb {R} ^ {d} \mid \underset {n \to \infty} {\limsup} \operatorname{dist} (v, A _ {n}) = 0 \right\}. \end{array}
$$

Recall that the epigraph of a function $h : \mathbb { R } ^ { d }  \mathbb { R } \cup \{ + \infty \}$ is

$$
\operatorname{epi} h := \{(x, t) \in \mathbb {R} ^ {d} \times \mathbb {R} \mid h (x) \leq t \}.
$$

Based on Definition 1 of limits of sets, we say that lim $1 _ { n } A = A _ { \infty }$ if lim $\operatorname* { s u p } _ { n } A _ { n } = \operatorname* { l i m } \operatorname* { i n f } _ { n } A _ { n } =$ $A _ { \infty } \subset \mathbb { R } ^ { d }$ , and we have the following notion of convergence of functions in terms of their epigraphs.

Definition 2. A sequence of functions $h _ { n }$ epi-converges to a function h, denoted $h _ { n } \stackrel { \mathrm { e p i } } {  } h , i f$

$$
\operatorname{epi} h = \liminf _ {n \to \infty} \operatorname{epi} h _ {n} = \limsup _ {n \to \infty} \operatorname{epi} h _ {n}.\tag{39}
$$

If dom $h \neq \emptyset$ , meaning that h is proper, epigraphical convergence (39) for closed convex functions has the following equivalent characterizations.

Lemma 16 (Theorem 7.17, Rockafellar and Wets [79]). Let $h _ { n } : \mathbb { R } ^ { d }  \overline { { \mathbb { R } } } , h : \mathbb { R } ^ { d }  \overline { { \mathbb { R } } }$ be closed convex and proper. Then $h _ { n } \stackrel { \mathrm { e p i } } {  } h$ is equivalent to either of the following two conditions.

(i) There exists a dense set $A \subset  { \mathbb { R } } ^ { d }$ such that $h _ { n } ( v )  h ( v )$ for all $v \in A$

(ii) For all compact $C \subset$ dom h not containing a boundary point of dom h,

$$
\lim _ {n \to \infty} \sup _ {v \in C} | h _ {n} (v) - h (v) | = 0.
$$

Importantly for our development, epigraphical convergence implies the infimal value convergence, and under additional conditions, convergence of solution sets.

Lemma 17 (Theorem 7.31, Rockafellar and Wets [79]). Let $h _ { n } : \mathbb { R } ^ { d }  \overline { { \mathbb { R } } } , h : \mathbb { R } ^ { d }  \overline { { \mathbb { R } } }$ satisfy $h _ { n } \stackrel { \mathrm { e p i } } {  } h$ and $- \infty <$ inf $h < \infty$ . Let $S _ { n } ( \varepsilon ) = \{ \theta \mid h _ { n } ( \theta ) \leq \operatorname* { i n f } h _ { n } + \varepsilon \}$ and $S ( \varepsilon ) = \{ \theta \mid h ( \theta ) \leq$ inf $h + \varepsilon \}$ Then lim su $) _ { n } S _ { n } ( \varepsilon ) \subset S ( \varepsilon )$ for all $\varepsilon \geq 0$ , and lim $\operatorname* { s u p } _ { n } S _ { n } ( \varepsilon _ { n } ) \subset S ( 0 )$ whenever $\varepsilon _ { n } \downarrow 0$

Lemma 18 (Proposition 7.33, Rockafellar and Wets [79]). Let $h _ { n } : \mathbb { R } ^ { d }  \overline { { \mathbb { R } } } , h : \mathbb { R } ^ { d }  \overline { { \mathbb { R } } }$ be closed and proper. $H h _ { n }$ has bounded sublevel sets and $h _ { n } \stackrel { \mathrm { e p i } } {  } h$ , then inf $\dot { \cdot } _ { v } h _ { n } ( v )  \operatorname* { i n f } _ { v } h ( v )$

## E.1 Proof of Proposition 9

To ease notation, we fix $\theta \in \Theta$ and denote $Z ( x ) : = \ell ( \theta ; x )$ , and we typically omit the dependence of R on θ (as it is fixed), writing $\mathcal { R } _ { f } ( P )$ and $\mathcal { R } _ { k } ( P )$ . The proof builds out of the epi-convergence theory we outline in the beginning of Section E.

By Proposition 1, strong duality (4) holds for both $P = P _ { 0 }$ and $\boldsymbol { P } = \boldsymbol { \widehat { P } } _ { n }$ . For a probability measure $P _ { \mathrm { : } }$ , define the dual objective

$$
g _ {f, P} (\lambda , \eta) := \left\{ \begin{array}{l l} \mathbb {E} _ {P} \left[ \lambda f ^ {*} \left(\frac {Z - \eta}{\lambda}\right) \right] + \rho \lambda + \eta & \text {if} \lambda \geq 0 \\ \infty & \text {otherwise}, \end{array} \right.
$$

where by convention we use the closure of the perspective $( \lambda , t ) \mapsto \lambda f ^ { * } ( t / \lambda )$ (cf. [87, Sec. 3.2] and [51, Prop. IV.2.2.2]). Using that $f ^ { * } ( s ) \geq 0$ for $s \geq 0$ and our assumption that $\mathbb { E } [ f ^ { * } ( | Z | ) ] < \infty$ 2 the strong law of large numbers implies that

$$
\mathcal {E} := \left\{\lim _ {n \to \infty} g _ {f, \widehat {P} _ {n}} (\lambda , \eta) = g _ {f, P _ {0}} (\lambda , \eta) \text {for all} \lambda \in \mathbb {Q}, \eta \in \mathbb {Q} \right\}
$$

has P<sub>0</sub>-measure 1. We now show that the functions $g _ { f }$ are both closed. To that end, note that standard conjugacy calculations [51, Prop. I.6.1.2] imply $1 \in \partial f ^ { * } ( 0 )$ = argmax $\{ - f ( t ) \}$ , as $f ( 1 ) =$ $0 , t = 1$ minimizes $f ,$ and $f ^ { * } ( 0 ) = 0$ . Thus we have $f ^ { * } ( s ) \geq f ^ { * } ( 0 ) + s$ for all $s ,$ so that

$$
\lambda f ^ {*} \left(\frac {z - \eta}{\lambda}\right) - (z - \eta) \geq 0.
$$

Fatou’s lemma then implies that for $v = \left( \eta , \lambda \right)$ and $v _ { 0 } = \left( \eta _ { 0 } , \lambda _ { 0 } \right)$ we have

$$
\begin{array}{l} \underset {v \to v _ {0}} {\liminf} \left\{\mathbb {E} _ {P} \left[ \lambda f ^ {*} \left(\frac {Z - \eta}{\lambda}\right) - (Z - \eta) \right] + \rho \lambda + \eta \right\} \\ \geq \mathbb {E} _ {P} \left[ \underset {v \to v _ {0}} {\liminf} \left\{\lambda f ^ {*} \left(\frac {Z - \eta}{\lambda}\right) - (Z - \eta) \right\} \right] + \rho \lambda_ {0} + \eta_ {0} \\ \geq \mathbb {E} _ {P} \left[ \lambda_ {0} f ^ {*} \left(\frac {Z - \eta_ {0}}{\lambda_ {0}}\right) - (Z - \eta_ {0}) \right] + \rho \lambda_ {0} + \eta_ {0}, \end{array}
$$

where the last inequality follows by the lower semicontinuity of the closure of the perspective. Using Lebesgue’s dominated convergence theorem on $( Z - \eta )$ , using the dominating function $| Z | + | \eta |$ we have thus shown that both $g _ { f , \widehat { P } _ { n } }$ and $g _ { f , P _ { 0 } }$ are lower semicontinuous. Lemma 16 implies that $g _ { f , \widehat { P } _ { n } } \stackrel { \mathrm { e p i } } {  } g _ { f , P _ { 0 } }$ with probability 1.

Finally, we would like to apply Lemma 18; to do so, we must show that $g _ { f , \widehat { P } _ { n } }$ is (eventually) coercive. For this, we note that $\begin{array} { r } { \lambda f ^ { * } \big ( \frac { Z - \eta } { \lambda } \big ) - Z + \eta \ge 0 } \end{array}$ as above, so that $g _ { f , P } ( \eta , \lambda ) \ge \rho \lambda + \mathbb { E } _ { P } [ Z ]$ and thus for any $P$ for which $\mathbb { E } _ { P } [ Z ]$ exists, lim $\begin{array} { r } { \mathrm { { \iota } } _ { \lambda \to \infty } \operatorname* { i n f } _ { \eta } g _ { f , P } ( \eta , \lambda ) = \infty } \end{array}$ . To show coercivity of ${ \mathit { g } } _ { f , P }$ as $\| ( \eta , \lambda ) \|  \infty$ , we thus need only consider limits taken as $\lambda$ remains bounded. Now, we claim that under the conditions of the lemma,

$$
\limsup _ {s \to - \infty} \frac {f ^ {*} (s)}{s} = \epsilon <   1 \text { and } \operatorname * {l i m i n f} _ {s \to \infty} \frac {f ^ {*} (s)}{s} = \infty .\tag{40}
$$

Deferring the proof of the claims (40), let us show how they imply that ${ { g } _ { f , { { P } _ { 0 } } } }$ is coercive. Assume that $0 \leq \lambda \leq \Lambda < \infty$ . For any constant $K < \infty , K > \Lambda$ , there exist $b , c < \infty$ such that $| z | \leq b$ and $\eta < - c$ imply that $f ^ { * } \big ( \frac { z - \eta } { \lambda } \big ) \ge K | \eta | / \Lambda$ , and similarly, $\eta > c$ implies $\begin{array} { r } { \lambda f ^ { * } ( \frac { z - \eta } { \lambda } ) \ge - \frac { 1 + \epsilon } { 2 } \eta } \end{array}$ . For $\eta < - c ,$ then, we have

$$
g _ {f, P} (\eta , \lambda) \geq P (| Z | \leq b) \left[ \frac {K | \eta |}{\Lambda} + \rho \lambda + \eta \right] + P (| Z | > b) \rho \lambda + \mathbb {E} _ {P} [ \mathbf {1} \{| Z | > b \} Z ],
$$

and for $\eta > c$ we similarly have

$$
g _ {f, P} (\eta , \lambda) \geq P (| Z | \leq b) \left[ \rho \lambda + \frac {\epsilon \eta}{2} \right] + P (| Z | > b) \rho \lambda + \mathbb {E} _ {P} [ \mathbf {1} \{| Z | > b \} Z ].
$$

Whenever $\mathbb { E } _ { P } [ | Z | ] < \infty$ , we see that lim $\vert \eta \vert {  } { \infty } \mathrm { i n f } _ { \lambda \in [ 0 , \Lambda ] } g _ { f , P } ( \eta , \lambda ) = { \infty }$ , so that ${ \mathit { g } } _ { f , P }$ is coercive. Consequently, the claim (40), coupled with our assumption that $\mathbb { E } _ { P _ { 0 } } [ | Z | ] < \infty$ , implies that $g _ { f , P _ { 0 } }$ is coercive. Because $g _ { f , \widehat { P } _ { n } } \stackrel { \mathrm { e p i } } {  } g _ { f , P _ { 0 } }$ , we have uniform convergence of $g _ { f , \widehat { P } _ { n } }$ to $g _ { f , P _ { 0 } }$ on compacta (Lemma 16), and thus $g _ { f , \widehat { P } _ { n } }$ is eventually coercive. Lemma 18 thus implies the result.

Finally, we return to the claim (40). For the first claim, we have for $s < 0$ that

$$
\frac {1}{s} \sup _ {t \geq 0} \{s t - f (t) \} = \inf _ {t \geq 0} \left\{t + \frac {f (t)}{| s |} \right\},
$$

which is decreasing as $s \downarrow - \infty$ , and letting $t _ { 0 } < 1$ be any value for which $f ( t _ { 0 } ) < \infty$ (as $f$ is finite near $t = 1 )$ , we have lim su $\begin{array} { r } { \mathrm { p } _ { s \to - \infty } \frac { 1 } { s } f ^ { * } ( s ) \leq t _ { 0 } < 1 } \end{array}$ as desired. For the second claim of inequalities (40), use that $f ( t ) < \infty$ for all $t \geq 1$ ; for each $n \in \mathbb N$ , then, there exists $s < \infty$ such that $f ( n ) / s \leq 2$ , so that $\begin{array} { r } { \frac { 1 } { s } f ^ { * } ( s ) = \operatorname* { s u p } _ { t \geq 0 } \{ t - f ( t ) / s \} \geq n - 2 } \end{array}$ . Taking $n \to \infty$ gives the claim.

## E.2 Proof of Proposition 10

The epi-convergence theory of the beginning of Section E, combined with Proposition 9, gives most of the results. First, we know that $\mathcal { R } _ { f } ( \theta ; \widehat { P } _ { n } )$ and $\mathcal { R } _ { f } ( \theta ; P _ { 0 } )$ are lower semicontinuous in $\theta ,$ as each is the supremum of closed convex functions $\textstyle \theta \mapsto \int \ell ( \theta ; x ) d P ( x )$ . Combined with Proposition 9, we have that $\mathcal { R } _ { f } ( \cdot ; \widehat { P } _ { n } ) \overset { \mathrm { e p i } } {  } \mathcal { R } _ { f } ( \cdot ; P _ { 0 } )$ with $P _ { \mathrm { 0 - p r o b a b i l i t y } } 1$ . Using the coercivity of $\mathscr { R } _ { f } ( \cdot ; P _ { 0 } )$ and that $\mathcal { R } _ { f } ( \theta ; P _ { 0 } ) \ <$ ∞ on an open set containing $S _ { P _ { 0 } } ( \Theta , 0 )$ , we take any compact set $C ~ \subset ~ \mathbb { R } ^ { d }$ containing $S _ { P _ { 0 } } ( \Theta , 0 )$ with $\mathcal { R } _ { f } ( \theta ; P _ { 0 } ) < \infty$ on $C ,$ and we obtain sup $ \ L _ { \ ) \in C } | \mathcal { R } _ { f } ( \theta ; P _ { 0 } ) - \mathcal { R } _ { f } ( \theta ; \widehat { P } _ { n } ) | \overset { a . s . } {  } 0$ by Lemma 16. The convexity of $\mathscr { R } _ { f } ( \cdot ; \widehat { P } _ { n } )$ then implies that $\mathscr { R } _ { f } ( \cdot ; \widehat { P } _ { n } )$ is coercive eventually, so that it has bounded sublevel sets, and Lemma 18 implies that inf $\begin{array} { r } { \operatorname { \dot { \theta } } _ { \in \Theta } \mathcal { R } _ { f } ( \theta ; \widehat { P } _ { n } ) \overset { a . s . } {  } \operatorname* { i n f } _ { \theta \in \Theta } \mathcal { R } _ { f } ( \theta ; P _ { 0 } ) } \end{array}$

For the second result, we use that for any sequence $\varepsilon _ { n } \geq 0 .$ , eventually the set $S _ { \widehat { P } _ { n } } ( \Theta , \varepsilon _ { n } )$ is non-empty by coercivity, and then Lemma 17 implies that

$$
\limsup _ {n} S _ {\widehat {P} _ {n}} (\Theta , \varepsilon_ {n}) \subset S _ {P _ {0}} (\Theta , 0).
$$

In turn, this yields that lim $\mathfrak { i } _ { n } d _ { \mathsf { C } } ( S _ { \widehat { P } _ { n } } ( \Theta , \varepsilon _ { n } ) ) = 0 \mathrm { ~ a s ~ } S _ { P _ { 0 } } ( \Theta , 0 )$ is compact by the coercivity assumption.

## F Proof of Limit Theorems

## F.1 Proof of Lemma 2

To ease notation, let $Z = \ell ( \theta _ { 0 } ; X )$ , and recall from Lemma 1 (and its proof in Section A.1) that we may rewrite the dual as

$$
g _ {P} (\theta , \lambda , \eta) = \frac {1}{\lambda^ {k _ {*} - 1}} \frac {(k - 1) ^ {k _ {*}}}{k} \mathbb {E} _ {P} \left[ (Z - \eta) _ {+} ^ {k _ {*}} \right] + \left(\rho + \frac {1}{k (k - 1)}\right) \lambda + \eta .
$$

In this case, it is clear that the minimizing λ is unique as in Eq. (22), with

$$
g _ {P} (\eta) := \inf _ {\lambda \geq 0} g _ {P} (\theta , \lambda , \eta) = c _ {k} \mathbb {E} _ {P} \left[ (Z - \eta) _ {+} ^ {k _ {*}} \right] ^ {1 / k _ {*}} + \eta ,
$$

where $c _ { k } = ( k ( k - 1 ) \rho + 1 ) ^ { 1 / k } > 1$ . It is evident that $g _ { P }$ is convex and coercive in $\eta .$ . Now, for all $\eta \geq$ ess sup $Z$ we have $g _ { P } ( \eta ) = \eta$ , so that $g _ { P }$ is strictly increasing in $\eta \geq$ ess sup Z. On the set $( - \infty , \mathrm { e s s } \operatorname* { s u p } Z )$ , we claim that $g _ { P }$ is strictly convex in $\eta$ . Indeed, for $\eta _ { 1 } \neq \eta _ { 2 } \in ( - \infty , \operatorname { e s s s s u p } Z )$ and $\alpha \in ( 0 , 1 )$ , we have

$$
\begin{array}{l} g _ {P} (\alpha \eta_ {1} + (1 - \alpha) \eta_ {2}) \\ \stackrel {(i)} {\leq} c _ {k} \left\| \alpha (Z - \eta_ {1}) _ {+} + (1 - \alpha) (Z - \eta_ {2}) _ {+} \right\| _ {k _ {*}, P} + \alpha \eta_ {1} + (1 - \alpha) \eta_ {2} \\ \stackrel {(i i)} {<  } c _ {k} \alpha \left\| (Z - \eta_ {1}) _ {+} \right\| _ {k _ {*}, P} + c _ {k} (1 - \alpha) \left\| (Z - \eta_ {2}) _ {+} \right\| _ {k _ {*}, P} + \alpha \eta_ {1} + (1 - \alpha) \eta_ {2} \\ = \alpha g _ {P} (\eta_ {1}) + (1 - \alpha) g _ {P} (\eta_ {2}), \end{array}
$$

where step (i) follows by convexity and that the norm $\lVert \cdot \rVert$ is increasing in positive arguments, while inequality (ii) follows because equality in Minkowski’s inequality $\left\| Y _ { 1 } + Y _ { 2 } \right\| _ { k _ { * } } \le \left\| Y _ { 1 } \right\| _ { k _ { * } } + \left\| Y _ { 2 } \right\| _ { k _ { * } }$ for $k _ { * } \in ( 1 , \infty )$ holds if and only if there exists $c \in \mathbb { R } _ { + }$ such that $Y _ { 1 } = c Y _ { 2 }$ with probability one.

## F.2 Proof of Theorem 11

We use a powerful result on asymptotic normality that we show applies in our setting. To state the result, we require a bit of (temporary) notation. First, recall the definition of bracketing numbers for a collection of functions.

Definition 3. Let $\lVert \cdot \rVert$ be a (semi-)norm on H. For functions $l , u : \mathcal { X }  \mathbb { R }$ with $l \leq u$ , the bracket $[ l , u ]$ is the set of functions $h : \mathcal { X }  \mathbb { R }$ such that $l \leq h \leq u$ , and $[ l , u ]$ is an -bracket $i f \parallel l - u \parallel \leq \epsilon$ Brackets $\{ [ l _ { i } , u _ { i } ] \} _ { i = 1 } ^ { m }$ cover H if for all $h \in \mathcal H$ , there is some bracket i such that $h \in [ l _ { i } , u _ { i } ]$ . The bracketing number $N _ { \lceil \rceil } ( \epsilon , \mathcal { H } , \| \cdot \| )$ is the minimum number of -brackets needed to cover H.

Now, let $\nu \subset \mathbb { R } ^ { d }$ be a convex set and $H : \mathcal { V } \times \mathcal { X } \to \mathbb { R }$ be a collection of criterion functions, where $\begin{array} { r } { \widehat { v } _ { n } = \operatorname { a r g m i n } _ { v \in \mathcal { V } } \mathbb { E } _ { \widehat { P } _ { n } } [ H ( v ; X ) ] } \end{array}$ . Assume that $\begin{array} { r } { v ^ { \star } = \operatorname * { a r g m i n } _ { v \in \mathcal { V } } \mathbb { E } _ { P _ { 0 } } [ H ( v ; X ) ] } \end{array}$ exists and is unique, and for $\epsilon > 0$ , define the localized function classes

$$
\mathcal {H} _ {\epsilon} := \left\{x \mapsto H (v; x) - H \left(v ^ {\star}; x\right): \| v - v ^ {\star} \| \leq \epsilon \right\}.
$$

We say that $M _ { \epsilon } : \mathcal { X }  \mathbb { R } _ { + }$ is an envelope for H<sub></sub> if $h \in { \mathcal { H } } _ { \epsilon }$ implies $| h ( x ) | \leq M _ { \epsilon } ( x )$ ; without further mention we take $M _ { \epsilon } ( x ) : = \mathrm { s u p } _ { \| v - v ^ { \star } \| \le \epsilon } | H ( v ; x ) - H ( v ^ { \star } ; x ) |$ . With these definitions, we have the following result.

Lemma 19 ([103, Theorem 3.2.10]). Let the conditions above hold, and assume that $\mathcal { H } _ { \epsilon }$ has envelope $M _ { \epsilon }$ with $\mathbb { E } [ M _ { \epsilon } ^ { 2 } ] < \infty$ . Assume additionally that

(i) The function $v \mapsto R ( v ) : = \mathbb { E } [ H ( v ; X ) ]$ is C<sup>2</sup> near v<sup>?</sup> and $\nabla ^ { 2 } R ( v ^ { \star } ) \succ 0$

(ii) The bracketing integral of ${ \mathcal { H } } _ { \epsilon }$ is uniformly bounded as $\epsilon  0$ : for some $\epsilon _ { 0 } > 0$ 2

$$
\int_ {0} ^ {\infty} \sup _ {\epsilon <   \epsilon_ {0}} \sqrt {\log N _ {[ ]} \left(\delta \left\| M _ {\epsilon} \right\| _ {P _ {0} , 2} , \mathcal {H} _ {\epsilon} , L _ {2} (P _ {0})\right)} d \delta <   \infty .\tag{41}
$$

(iii) There exists $C < \infty$ such that $\mathbb { E } [ M _ { \epsilon } ( X ) ^ { 2 } ] \le C \epsilon ^ { 2 }$ for all small .

(iv) There exists a centered Gaussian process $G$ on $\mathbb { R } ^ { d }$ where $G ( v ) = G ( v ^ { \prime } )$ P<sub>0</sub>-almost surely only if $\boldsymbol { v } = \boldsymbol { v } ^ { \prime }$ such that for every $c , K > 0$ 0,

$$
\lim _ {\epsilon \to 0} \epsilon^ {- 2} \mathbb {E} [ M _ {\epsilon} (X) ^ {2} \mathbf {1} \left\{M _ {\epsilon} (X) > c \right\} ] = 0,\tag{42a}
$$

$$
\lim _ {\epsilon \to 0} \operatorname * {l i m s u p} _ {\delta \to 0} \sup _ {\| u _ {1} - u _ {2} \| <   \epsilon , \| u _ {1} \| \vee \| u _ {2} \| \leq K} \delta^ {- 2} \mathbb {E} [ (H (v ^ {\star} + \delta u _ {1}; X) - H (v ^ {\star} + \delta u _ {2}; X)) ^ {2} ] = 0\tag{42b}
$$

$$
\lim _ {\delta \to 0} \delta^ {- 2} \mathbb {E} [ (H (v ^ {\star} + \delta u _ {1}; X) - H (v ^ {\star} + \delta u _ {2}; X)) ^ {2} ] = \mathbb {E} [ (G (u _ {1}) - G (u _ {2})) ^ {2} ].\tag{42c}
$$

Then, there exists a version of G with bounded, uniformly continuous sample paths on compacta. Further, $i f \widehat { v } _ { n } \in \nu$ satisfies $\begin{array} { r } { \mathbb { E } _ { \widehat { P } _ { n } } [ H ( \widehat { v } _ { n } ; X ) ] \leq \operatorname* { i n f } _ { v \in \mathcal { V } } \mathbb { E } _ { \widehat { P } _ { n } } [ H ( v ; X ) ] + O _ { P } ( 1 / n ) } \end{array}$ and $\widehat { v } _ { n } \stackrel { a . s . } {  } v ^ { \star }$ , then $\sqrt { n } (  { \widehat { v } } _ { n } - v ^ { \star } )$ converges in distribution to the unique maximizer of the process

$$
u \mapsto G (u) + \frac {1}{2} u ^ {T} \nabla^ {2} R (v ^ {\star}) u.
$$

We now show how under the conditions specified in Theorem 11, our problem satisfies the conditions of Lemma 19. We first provide notation and a few additional definitions for shorthand. Define

$$
H (\theta , \lambda , \eta ; X) := \lambda f ^ {*} \left(\frac {\ell (\theta ; X) - \eta}{\lambda}\right) + \rho \lambda + \eta ,
$$

so that $g _ { P } ( \theta , \lambda , \eta ) = \mathbb { E } _ { P } [ H ( \theta , \lambda , \eta ; X ) ]$ . Let $( { \widehat { \theta } } _ { n } , { \widehat { \lambda } } _ { n } , { \widehat { \eta } } _ { n } )$ be the empirical minimizer

$$
(\widehat {\theta} _ {n}, \widehat {\lambda} _ {n}, \widehat {\eta} _ {n}) \in \underset {\theta , \lambda \geq 0, \eta} {\operatorname{argmin}} \mathbb {E} _ {\widehat {P} _ {n}} [ H (\theta , \lambda , \eta ; X) ].
$$

For $\epsilon > 0$ , define the collection

$$
\mathcal {H} _ {\epsilon} := \left\{x \mapsto H (\theta , \lambda , \eta ; x) - H \left(\theta^ {\star}, \lambda^ {\star}, \eta^ {\star}; x\right): \| \theta - \theta^ {\star} \| + | \lambda - \lambda^ {\star} | + | \eta - \eta^ {\star} | \leq \epsilon \right\}.\tag{43}
$$

We claim that the envelope $M _ { \epsilon }$ exists for the set (43). First, we note that ∇H exists with probability 1: by our Assumption C that $g _ { P _ { 0 } }$ is $\mathcal { C } ^ { 2 }$ near $( \theta ^ { \star } , \lambda ^ { \star } , \eta ^ { \star } )$ , we know that $g _ { P _ { 0 } }$ is continuously diferentiable. Then For $h ( t , x )$ an arbitrary function, convex in $\begin{array} { r } { t , \int h ( t , x ) d P ( x ) } \end{array}$ is diferentiable at some $t _ { 0 }$ if and only if $t \mapsto h ( t , x )$ is diferentiable at $t _ { 0 }$ for P-almost all x [16]. Consequently, for P -almost all x we have $\nabla H ( \cdot ; x )$ exists in a neighborhood of $( \theta ^ { \star } , \lambda ^ { \star } , \eta ^ { \star } )$ , and

$$
\nabla H (\theta , \lambda , \eta ; x) = \left[ \begin{array}{c} f ^ {* \prime} \left(\frac {\ell (\theta ; x) - \eta}{\lambda}\right) \nabla \ell (\theta ; x) \\ - f ^ {* \prime} \left(\frac {\ell (\theta ; x) - \eta}{\lambda}\right) + 1 \\ f ^ {*} \left(\frac {\ell (\theta ; x) - \eta}{\lambda}\right) - \frac {1}{\lambda} f ^ {* \prime} \left(\frac {\ell (\theta ; x) - \eta}{\lambda}\right) (\ell (\theta ; x) - \eta) + \rho \end{array} \right]\tag{44}
$$

for $( \theta , \lambda , \eta )$ near $( \theta ^ { \star } , \lambda ^ { \star } , \eta ^ { \star } )$ . We begin with a simple technical lemma.

Lemma 20. Let f satisfy the conditions of Theorem 11 and $\begin{array} { r } { k _ { * } = \frac { k } { k - 1 } } \end{array}$ . Then lim su $\mathrm { l p } _ { s \to \infty } f ^ { * } ( s ) / s ^ { k _ { * } } <$ $\infty ,$ and for any $t ( s ) \in \partial f ^ { * } ( s ) , t ( s ) \geq 0$ and lim $\mathrm { s u p } _ { s \to \infty } t ( s ) / s ^ { \frac { 1 } { k - 1 } } < \infty$

Proof We begin with the first claim, recalling the assumption that lim in $\mathrm { f } _ { t  \infty } f ( t ) / t ^ { k } > 0$ , so that for some $t _ { 0 } < \infty$ there exists $c > 0$ such that $f ( t ) \geq c t ^ { k }$ for all $t \geq t _ { 0 }$ . Thus for $s \geq 0$ , we have

$$
f ^ {*} (s) = \sup _ {t \geq 0} \{s t - f (t) \} \leq \sup _ {t \in [ 0, t _ {0} ]} \{s t - f (t) \} \vee \sup _ {t \geq t _ {0}} \{s t - f (t) \} \leq s t _ {0} \vee \sup _ {t \geq t _ {0}} \{s t - c t ^ {k} \} \leq s t _ {0} \vee C s ^ {k *}.
$$

Now we show the second claim. To see this, recall the standard conjugacy result [51] that $t ( s ) \in$ argmax $\{ s t - f ( t ) \}$ , so that $t ( s ) \geq 0$ always, and let $\hat { t } = ( s / k c ) ^ { \frac { 1 } { k - 1 } }$ . Assume that s is large enough that $f ( t ) \geq c t ^ { k }$ for $t > \hat { t }$ . Then for $t > { \hat { t } } ,$ we have

$$
s t - f (t) \leq s t - c t ^ {k} <   s \hat {t} - c \hat {t} ^ {k},
$$

as $\hat { t }$ uniquely maximizes st $- c t ^ { k }$ . Thus t cannot belong to $\partial f ^ { * } ( s )$ , giving the result.

With Lemma 20 in hand, the next lemma follows.

Lemma 21. There exists a constant $C < \infty$ and a neighborhood U $o f \left( \theta ^ { \star } , \lambda ^ { \star } , \eta ^ { \star } \right)$ such that $M ( x ) : =$ $\operatorname { s u p } _ { ( \theta , \lambda , \eta ) \in U } \| \nabla H ( \theta , \lambda , \eta ; x ) \|$ satisfies

$$
M (x) \leq C \left[ \frac {| \ell (\theta^ {\star} ; x) | ^ {k _ {*}} + | \eta^ {\star} | ^ {k _ {*}}}{\lambda^ {\star k _ {*}}} + L (x) ^ {k _ {*}} \right],
$$

and $M _ { \epsilon } ( x ) : = M ( x ) \cdot \epsilon$ is an envelope for ${ \mathcal { H } } _ { \epsilon }$ .

Proof The result is a standard algebraic exercise, coupled with the fact that a convex function h is Lipschitz in an -neighborhood of a point $t _ { 0 }$ with constant $\mathrm { s u p } _ { t } \{ \| \partial h ( t ) \| _ { 2 } \mid \| t - t _ { 0 } \| \}$ (cf. [51]). Thus, we bound the components of ∇H from Eq. (44); we only bound $\nabla _ { \boldsymbol { \theta } } H$ as the others are completely similar. For $( \theta , \lambda , \eta )$ in a neighborhood U of $( \theta ^ { \star } , \lambda ^ { \star } , \eta ^ { \star } )$ , we have for constants $C < \infty$ that may change from line to line

$$
\begin{array}{l} \| \nabla_ {\theta} H (\theta , \lambda , \eta ; x) \| = f ^ {* \prime} \left(\frac {\ell (\theta ; x) - \eta}{\lambda}\right) \| \nabla \ell (\theta ; x) \| \\ \stackrel {(i)} {\leq} C \left| \frac {\ell (\theta ; x) - \eta}{\lambda} \right| ^ {\frac {1}{k - 1}} \| \nabla \ell (\theta ; x) \| \\ \stackrel {(i i)} {\leq} C \left| \frac {\ell (\theta ; x) - \eta}{\lambda} \right| ^ {\frac {k}{k - 1}} + C \| \nabla \ell (\theta ; x) \| ^ {k _ {*}} \\ \stackrel {(i i i)} {\leq} C \frac {| \eta | ^ {k _ {*}}}{\lambda^ {k _ {*}}} + C \frac {| \ell (\theta^ {\star} ; x) | ^ {k _ {*}}}{\lambda^ {k _ {*}}} + C L (x) ^ {k _ {*}}, \end{array}
$$

where inequality (i) follows from Lemma 20, (ii) follows by the Fenchel-Young inequality that $a b \leq ( 1 / k ) | a | ^ { k } + ( 1 / k _ { * } ) | b | ^ { k _ { * } }$ , while inequality (iii) is a consequence of Assumption B.1. The remainder of the derivation follows from straightforward algebra once we note that $\lambda / \lambda ^ { \star }$ is bounded for λ near $\lambda ^ { \star }$ □

Finally, we show that each of the conditions of Lemma 19 holds for our problem. That $\mathbb { E } [ M _ { \epsilon } ( X ) ^ { 2 } ] <$ ∞ is immediate by Assumption B on the moments of \` and $\nabla \ell .$ . For condition (i), we have Assumption C. For the bracketing integral condition (41), From a standard bound on bracketing numbers for Lipschitz functions [103, Theorem 2.7.11], we have

$$
\log N _ {[ ]} \left(\delta \| M _ {\epsilon} \|, \mathcal {H} _ {\epsilon}, L _ {2} (P _ {0})\right) \leq (d + 2) \log \left(1 + \frac {2}{\delta}\right)
$$

for  small enough, so that the bracketing integral is bounded. Each of the quantities (42) follows by Lebesgue’s dominated convergence theorem. For condition (42a), we have $M _ { \epsilon } ( x ) ^ { 2 } { \mathbf 1 } \left\{ M _ { \epsilon } ( x ) > c \right\} / \epsilon ^ { 2 } =$ $M ( x ) ^ { 2 } \mathbf { 1 } \{ M ( x ) > c / \epsilon \}  0 { \mathrm { ~ a s ~ } } \epsilon  0$ , and it is dominated by $M ( x )$ . For condition (42b), we have for $v ^ { \star } = ( \theta ^ { \star } , \lambda ^ { \star } , \eta ^ { \star } )$ that

$$
| H (v ^ {\star} + \delta u _ {1}; x) - H (v ^ {\star} + \delta u _ {2}; x) | \leq \sup _ {v \text { near} v ^ {\star}} \| \nabla H (v; x) \|   \delta   \| u _ {1} - u _ {2} \| \leq M (x) \delta   \| u _ {1} - u _ {2} \|
$$

by Lemma 21. Thus the dominated convergence theorem again implies the convergence (42b). For the covariance condition (42c), we use the diferentiability of H as in Eq. (44) to see that with $v ^ { \star }$ as above, $\begin{array} { r } { \frac { 1 } { \delta } ( H ( v ^ { \star } + \delta u _ { 1 } ; x ) - H ( v ^ { \star } + \delta u _ { 2 } ; x ) )  \langle \nabla H ( v ^ { \star } ; x ) , u _ { 1 } - u _ { 2 } \rangle } \end{array}$ and it is dominated by $M ( x ) \left\| u _ { 1 } - u _ { 2 } \right\|$ . Thus, we may take

$$
G (u) := \langle W, u \rangle \text { for } W \sim \mathsf {N} \left(0, \operatorname{Cov} (\nabla H (\theta^ {\star}, \lambda^ {\star}, \eta^ {\star}; X))\right)
$$

as our Gaussian process. The theorem is then an immediate consequence of Lemma 19.