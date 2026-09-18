# Implicit Rate-Constrained Optimization of Non-decomposable Objectives

Abhishek Kumar 1 Harikrishna Narasimhan 1 Andrew Cotter 1

## Abstract

We consider a popular family of constrained optimization problems arising in machine learning that involve optimizing a non-decomposable evaluation metric with a certain thresholded form, while constraining another metric of interest. Examples of such problems include optimizing the false negative rate at a fixed false positive rate, optimizing precision at a fixed recall, optimizing the area under the precision-recall or ROC curves, etc. Our key idea is to formulate a rate-constrained optimization that expresses the threshold parameter as a function of the model parameters via the Implicit Function theorem. We show how the resulting optimization problem can be solved using standard gradient based methods. Experiments on benchmark datasets demonstrate the effectiveness of our proposed method over existing state-of-theart approaches for these problems. The code for the proposed method is available at this url.

## 1. Introduction

In many modern machine learning applications, the performance of a model is evaluated using metrics that are complex and nuanced. For example, in retrieval systems, it is common to evaluate a scoring model based the area under the precision-recall curve, or the ROC curve, or on its precision at a certain recall value (Eban et al., 2017). Similarly, in many medical diagnostic applications, a model is required to yield low false positive rates while restricting its false negatives rate to be within an allowed limit (Rao et al., 2008), while in machine learning fairness applications one might be interested in imposing the “80% rule”, which requires a positive prediction rate of at least 80% on the minority class (Biddle, 2006; Zafar et al., 2017).

The above problems cannot be directly solved by minimizing a standard classification loss. In fact, prior work has found that doing so can result in inferior model performance (Joachims, 2005; Koyejo et al., 2014; Kar et al., 2014; Eban et al., 2017; Cotter et al., 2019a). Moreover, many of the metrics that we are interested in have a non-decomposable structure, i.e., they cannot be expressed directly in terms of an average over individual data points, making them hard to optimize using standard optimization tools. Much prior work has sought to address this problem, resulting in a range of methods targeting different classes of non-decomposable metrics (Yue et al., 2007; Narasimhan & Agarwal, 2013b; Kar et al., 2015; Yan et al., 2018).

In this paper, we consider a popular family of nondecomposable objectives that have a certain thresholded form. This includes metrics like the false negative rate (FNR) at a certain fixed false positive rate (FPR), precision at a fixed recall, precision@K, AUC-PR, and AUC-ROC, as well as more recent threshold-based fairness metrics (Hardt et al., 2016). The task of optimizing these metrics can naturally be written as a constrained optimization problem, wherein one seeks to optimize a quantity such as the model’s precision or false positive rate at one or more thresholds, subject to the model satisfying a set of rate constraints at those thresholds. The dominant approach for solving such rateconstrained problems has been to relax the constraints with surrogate losses, and to formulate an equivalent Lagrangianbased primal-dual problem (Eban et al., 2017). Follow-up work has improved upon this approach by using the surrogate relaxations only for the primal updates, but not the dual (Cotter et al., 2019b; Narasimhan et al., 2019a).

Our proposed optimization strategy departs significantly from the prior Lagrangian-based methods, and avoids explicitly solving the constrained optimization problem. Instead, we express the threshold variables in the optimization problem as an implicit function of the model parameters, and thus re-formulate the problem as an unconstrained optimization over the model parameters. By appealing to the Implicit Function Theorem (Tu, 2011), we show how to compute the gradients for the resulting unconstrained objective, despite not knowing the form of the implicit function, and then use them to perform standard gradient-based optimization (see Section 3). Although the Implicit Function Theorem makes a local statement about the existence of the implicit function (i.e., valid in a small neighborhood around current model parameters), we can still effectively use the theorem to make local gradient updates towards optimizing the objective.

We experiment with two image classification datasets and several UCI datasets, and show that our proposed method often performs significantly better than the state-of-the-art constrained optimization solvers in optimizing popular metrics such as FNR at fixed FPR, and the “partial” areas under the ROC and Precision-Recall curves evaluated at a selection range of FPR/recall values (see Section 5). We find our approach to be particularly effective when used to target extreme values of FPR or recall. We also discuss how our formulation can be extended to apply to more complex learning problems, such as query-based ranking, where standard constrained optimization techniques are known to have notable drawbacks (see Section 6).

## 2. Problem Formulation

We describe our formulation in a binary classification setting, with input space X and binary labels {0, 1}. Later, we will discuss how to extend our setup to multi-class classification problems. Our goal is to learn a scoring model $s ^ { \theta } : X {  } \bar { \mathbb { R } }$ , parameterized by $\theta \in \mathbb { R } ^ { p }$ , whose scores can be thresholded to make a binary prediction. We denote a scoring model thresholded at t by $s _ { t } ^ { \theta } ( x ) = \mathbf { 1 } ( s ^ { \theta } ( x ) >$ $t ) \in \{ 0 , 1 \}$ . We will use $\mathrm { T P } ( s _ { t } ^ { \theta } )$ , FP(sθt ) and $\mathrm { F N } ( s _ { t } ^ { \theta } )$ to denote the true positives, false positive and false negatives respectively for the thresholded classifier.

We are interested in solving constrained optimization problems of the form:

$$
\operatorname* { m i n } _ { \theta \in \mathbb { R } ^ { p } } f ( \theta , \lambda ) \quad \mathrm { s . t . } \quad g ( \theta , \lambda ) = \mathbf { 0 }\tag{1}
$$

where the objective $f : \mathbb { R } ^ { p } \times \mathbb { R } ^ { m } {  } \mathbb { R }$ maps the model parameters $\theta \in \mathbb { R } ^ { p }$ and a set of m thresholds $\lambda \in \mathbb { R } ^ { m }$ to a real value, and the constraints $g : \mathbb { R } ^ { p } \times \mathbb { R } ^ { m } {  } \mathbb { R } ^ { m }$ map $( \theta , \lambda )$ to m real numbers. We further assume θ stays in the feasible region, i.e., ∀θ, ∃λ s.t. $g ( \theta , \lambda ) = \mathbf { 0 }$ . We will further discuss how several commonly used constrained optimization problems of interest in machine learning satisfy this assumption of feasibility. We provide some popular examples of evaluation metrics below.

Example 1 (Precision at fixed recall). To maximize the model’s precision at the threshold $\lambda \in \mathbb { R }$ at which its recall is β, we will have:

$$
\begin{array} { r c l } { { f ( \theta , \lambda ) } } & { { = } } & { { \mathrm { - p r e c i s i o n } ( s _ { \lambda } ^ { \theta } ) = \displaystyle - \frac { \mathrm { T P } ( s _ { \lambda } ^ { \theta } ) } { \mathrm { T P } ( s _ { \lambda } ^ { \theta } ) + \mathrm { F P } ( s _ { \lambda } ^ { \theta } ) } ; } } \\ { { g ( \theta , \lambda ) } } & { { = } } & { { \mathrm { r e c a l l } ( s _ { \lambda } ^ { \theta } ) - \displaystyle \beta = \frac { \mathrm { T P } ( s _ { \lambda } ^ { \theta } ) } { \mathrm { T P } ( s _ { \lambda } ^ { \theta } ) + \mathrm { F N } ( s _ { \lambda } ^ { \theta } ) } - \beta . } } \end{array}
$$

Example 2 (FNR at fixed FPR). To minimize the model’s false negative rate at the threshold $\lambda \in \mathbb { R }$ at which its false

positive rate is $\beta \in [ 0 , 1 ]$ , we will have:

$$
\begin{array} { r c l } { f ( \theta , \lambda ) } & { = } & { { \mathrm { F N R } } ( s _ { \lambda } ^ { \theta } ) = \frac { { \mathrm { F N } } ( s _ { \lambda } ^ { \theta } ) } { { \mathrm { T N } } ( s _ { \lambda } ^ { \theta } ) + { \mathrm { F P } } ( s _ { \lambda } ^ { \theta } ) } ; } \\ { g ( \theta , \lambda ) } & { = } & { { \mathrm { F P R } } ( s _ { \lambda } ^ { \theta } ) = \frac { { \mathrm { F P } } ( s _ { \lambda } ^ { \theta } ) } { { \mathrm { T P } } ( s _ { \lambda } ^ { \theta } ) + { \mathrm { F N } } ( s _ { \lambda } ^ { \theta } ) } - \beta . } \end{array}
$$

Example 3 (Precision at k). To maximize the model’s precision at the threshold λ ∈ R at which it achieves a coverage $o f k ,$ we can set:

$$
\begin{array} { r c l } { { f ( \theta , \lambda ) } } & { { = } } & { { - \mathrm { p r e c i s i o n } ( s _ { \lambda } ^ { \theta } ) ; } } \\ { { g ( \theta , \lambda ) } } & { { = } } & { { \mathrm { T P } ( s _ { \lambda } ^ { \theta } ) + \mathrm { F P } ( s _ { \lambda } ^ { \theta } ) - k . } } \end{array}
$$

Example 4 (AUC-PR). To maximize the area under the Precision-Recall curve, following Eban et al. (2017), we use a Riemann approximation to the area: we divide the recall range into m equally-spaced values $\beta _ { 1 } , \ldots , \beta _ { m } \in [ 0 , 1 ]$ and evaluate the average precision that the model achieves when thresholded to match each of the target recalls. This can be written as a constrained optimization problem with m thresholds $\lambda _ { 1 } , \ldots , \lambda _ { m } \in \mathbb { R }$ , and with the objective and constraints set to:

$$
\begin{array} { r c l } { { f ( \theta , \lambda ) } } & { { = } } & { { \displaystyle - \frac { 1 } { m } \sum _ { i = 1 } ^ { m } \mathrm { p r e c i s i o n } ( s _ { \lambda _ { i } } ^ { \theta } ) } } \\ { { g _ { i } ( \theta , \lambda ) } } & { { = } } & { { \mathrm { r e c a l l } ( s _ { \lambda _ { i } } ^ { \theta } ) - \beta _ { i } , \forall i \in [ m ] . } } \end{array}
$$

One can similarly compute the “partial” area under the PR curve in any given range of recall (precision) targets by thresholding only at those particular recall (precision) values. This is particularly useful for excluding low recalls (precisions), since one is generally uninterested in the performance of the model at such thresholds.

Example 5 (AUC-ROC). To maximize the (partial) area under the Receiver Operator Characteristic (ROC) curve, we can again apply a Riemann approximation: we divide the FPR range into m values $\beta _ { 1 } , \ldots , \beta _ { m } ,$ and compute the average TPR at m thresholds $\lambda _ { 1 } , \ldots , \lambda _ { m } \in \mathbb { R }$ , chosen to satisfy the FPR targets:

$$
\begin{array} { r c l } { f ( \theta , \lambda ) } & { = } & { \displaystyle - \frac { 1 } { m } \sum _ { i = 1 } ^ { m } \mathrm { T P R } ( s _ { \lambda _ { i } } ^ { \theta } ) } \\ { g _ { i } ( \theta , \lambda ) } & { = } & { \mathrm { F P R } ( s _ { \lambda _ { i } } ^ { \theta } ) - \beta _ { i } , \forall i \in [ m ] . } \end{array}
$$

Example 6 (Fairness criterion). In a typical group fairness application (Hardt et al., 2016), each example belongs to one of m protected groups, and the goal is to constrain the model to have equitable performance across all groups. One way to enforce this requirement is to introduce a separate threshold λi for examples from each group, and to tune them to satisfy the fairness constraints. For example, the popular demographic parity constraint for two (disjoint)

groups, which requires equal positive prediction rates for both groups, can be encoded as:

$$
\begin{array} { r c l } { { g ( \theta , \lambda ) } } & { { = } } & { { \displaystyle \frac { 1 } { m _ { 1 } } \left( \mathrm { T P } _ { 1 } ( s _ { \lambda _ { 1 } } ^ { \theta } ) + \mathrm { F P } _ { 1 } ( s _ { \lambda _ { 1 } } ^ { \theta } ) \right) } } \\ { { } } & { { } } & { { \displaystyle - \frac { 1 } { m _ { 2 } } \left( \mathrm { T P } _ { 2 } ( s _ { \lambda _ { 2 } } ^ { \theta } ) + \mathrm { F P } _ { 2 } ( s _ { \lambda _ { 2 } } ^ { \theta } ) \right) , } } \end{array}
$$

where $\mathrm { T P _ { 1 } , T P _ { 2 } }$ are the true positives on examples belonging group 1 and 2 respectively, $\mathrm { F P _ { 1 } , F P _ { 2 } }$ are the false positives for the two groups, and $m _ { 1 }$ and m2 are the number of examples in the two groups.

Feasibility of constraints by tuning λ. Assuming that the model does not map two different training examples to same outputs, it is easy to see that for fixed model parameters θ, any of the aforementioned rate constraints $( e . g .$ , false positive rate, precision, recall, etc.) can be satisfied to any feasible value by tuning only the thresholds $\lambda _ { 1 } , \ldots , \lambda _ { m }$

All the rate based optimization objectives and constraints discussed above are non-smooth. To make the problem amenable to gradient based optimization, following earlier work (Eban et al., 2017; Cotter et al., 2019b; Narasimhan et al., 2019a) we replace $f$ and g with smooth differentiable surrogates $\tilde { f }$ and ${ \tilde { g } } ,$ and relax (1) into:

$$
\operatorname* { m i n } _ { \theta \in \mathbb { R } ^ { p } } \tilde { f } ( \theta , \lambda ) \quad \mathrm { s . t . } \quad \tilde { g } ( \theta , \lambda ) = \mathbf { 0 } .\tag{2}
$$

Surrogate losses. We use sigmoid and softplus functions, denoted as $\sigma ( \cdot )$ , as surrogates in our experiments. Specifically, we replace the innermost indicators with smooth surrogate σ. For example, if the objective f is $\mathrm { F N R } = \big ( \frac { \mathrm { F N } } { \mathrm { t o t a l ~ p o s i t i v e s } } \big )$ and $p _ { i }$ is the prediction (logit) for ith example, then we replace $\begin{array} { r } { \mathrm { F N } = \sum _ { i : y _ { i } = 1 } \mathbb { I } _ { p _ { i } < \lambda } } \end{array}$ with $\begin{array} { r } { \widetilde { \mathrm { F N } } = \sum _ { i : y _ { i } = 1 } \sigma _ { \tau } ( - ( p _ { i } - } \end{array}$ $\lambda ) )$ , yielding the surrogate $\begin{array} { r } { \tilde { f } = \frac { \widetilde { \mathrm { F N } } } { \mathrm { t o t a l p o s i t i v e s } } } \end{array}$ (where $\sigma _ { \tau } ( x ) =$ $\sigma ( \tau x )$ denotes a temperature scaled sigmoid or softplus function). We use similar surrogates for ratio based objectives such as precision and recall. For example, if f is precision $\big ( \frac { \mathrm { \bar { T P } } } { \mathrm { p r e d i c t e d ~ p o s i t i v e s } } \big )$ then we replace $\scriptstyle { \mathrm { T P } } = \sum _ { \scriptstyle i : y _ { i } = 1 } { \mathbb { I } } _ { p _ { i } > \lambda }$ with $\begin{array} { r } { \widetilde { \mathrm { T P } } = \sum _ { i : y _ { i } = 1 } \sigma _ { \tau } ( p _ { i } - \lambda ) } \end{array}$ and predicted-positives $= \sum _ { i } \mathbb { I } _ { p _ { i } > \lambda }$ with $\begin{array} { r } { \widetilde { \mathrm { P P } } = \sum _ { i } \sigma _ { \tau } ( p _ { i } - \lambda ) } \end{array}$ , yielding the surrogate $\begin{array} { r } { \tilde { f } = \frac { \widetilde \mathrm { T P } } { \widetilde \mathrm { P P } } } \end{array}$

## 3. Optimization with Implicit Thresholds

The canonical approach to solving the constrained optimization problem in (2) is to formulate a Lagrangian for the problem, and then perform gradient updates to maximize the Lagrangian over the mulitipliers and minimize it over θ and λ. Our key idea is to avoid explicitly solving the constrained problem by instead formulating an equivalent unconstrained problem in which we express the thresholds λ as an implicit function of the model parameters θ (within a neighborhood around θ).

To this end, we make use of the Implicit Function Theorem (Tu, 2011). Specifically, suppose the point $( { \theta } ^ { 0 } , { \lambda } ^ { 0 } ) \in \mathbb { R } ^ { p + m }$ satisfies the constraint, i.e., $\tilde { g } ( \theta ^ { 0 } , \lambda ^ { \bar { 0 } } ) = \mathrm { { \dot { 0 } } }$ . Then we can express the thresholds as $\lambda ^ { 0 } = \tilde { h } ( \theta ^ { 0 } )$ in a neighborhood around $\theta ^ { 0 }$ , for some implicit function h˜:

Theorem 1 (Implicit Function Theorem (Tu, 2011)). Let U be an open subset in $\mathbb { R } ^ { p } \times \mathbb { R } ^ { m }$ and $\tilde { g } : U \to \mathbb { R } ^ { m }$ a $C ^ { 1 }$ map. Write (θ, λ) for a point in U , with $\theta \in \mathbb { R } ^ { p } , \lambda \in$ $\mathbb { R } ^ { m }$ . At a point $( \mathcal { \theta } ^ { 0 } , \mathring { \lambda ^ { 0 } } ) \in \bar { U }$ where $\tilde { g } ( \theta ^ { 0 } , \lambda ^ { 0 } ) = 0$ and the determinant det $[ \partial \tilde { g } ^ { i } / \partial \lambda ^ { j } ( \theta ^ { 0 } , \lambda ^ { 0 } ) ]$ ] is nonzero, there exists a neighborhood $\mathbf { \bar { \Theta } } \Theta \times \Lambda o f ( \theta ^ { 0 } , \lambda ^ { 0 } )$ in U and a unique $C ^ { 1 }$ function $\tilde { h } : \Theta \to \Lambda$ such that in $\Theta \times \Lambda \subset U \subset \mathbb { R } ^ { p } \times \mathbb { R } ^ { m }$ ,

$$
\tilde { g } ( \theta , \lambda ) = 0 \quad \Longleftrightarrow \quad \lambda = \tilde { h } ( \theta )
$$

Using this theorem, we can write the implicit threshold as $\lambda = \tilde { h } ( \theta )$ within a neighborhood around $\mathbf { \bar { \theta } } ^ { 0 }$ , which enables us to turn problem (2) into the equivalent unconstrained problem of minimizing $\tilde { f } ( \theta , \tilde { h } ( \theta ) )$ .

## 3.1. Characterization of the implicit function

A differentiable function $\tilde { h } ( \theta ) \in \mathbb { R } ^ { m }$ that provides us with the m thresholds at which $\tilde { f } ( \theta , \tilde { h } ( \theta ) ) = \mathbf { 0 }$ may not always exist, and even if it does, it may be available in closedform only in some highly simplified settings.1 Nonetheless, under some assumptions, we can show that when $\tilde { h }$ exists, the resulting composite function $\tilde { f } ( \theta , \tilde { h } ( \theta ) )$ is convex in θ. Proposition 1. Let $m = 1$ . Suppose the objective $\tilde { f } ( \theta , \lambda )$ is jointly convex in (θ, λ) and is strictly increasing in $\lambda \in \mathbb { R }$ and the constraint g˜(θ, λ) is jointly convex in $( \theta , \lambda )$ and is strictly descreasing in $\lambda \in \mathbb { R } .$ . Suppose there exists a $C ^ { 1 }$ function $\tilde { h } : \mathbb { R } ^ { p } \to \mathbb { R }$ such that $\tilde { g } ( \theta , \tilde { h } ( \theta ) ) = 0 , \forall \theta$ . Then h˜ is convex in $\theta .$ Consequently, the composite objective $\tilde { f } ( \theta , \tilde { h } ( \theta ) )$ is convex in θ.

The proof adapts a result from Wurker (2001) and is given in Appendix A. The assumptions in the proposition hold for simple linear models, for example, when minimizing the FPR while constraining the FNR (see appendix for details).

## 3.2. Gradient computation

To compute a (local) derivative for $\tilde { f } ( \theta , \tilde { h } ( \theta ) )$ ) w.r.t. θ within the neighborhood of $\theta ^ { 0 }$ in Theorem 1, we use:

$$
\nabla _ { \boldsymbol { \theta } } \tilde { f } ( \boldsymbol { \theta } , \tilde { h } ( \boldsymbol { \theta } ) ) = \nabla _ { \boldsymbol { \theta } } \tilde { f } ( \boldsymbol { \theta } , \lambda ) + \frac { \partial \tilde { f } ( \boldsymbol { \theta } , \lambda ) } { \partial \lambda } \nabla _ { \boldsymbol { \theta } } \tilde { h } ( \boldsymbol { \theta } ) ,\tag{3}
$$

1For example, if the distribution of the instances $x \in \mathbb { R } ^ { p }$ conditioned on label $y = 1$ is a Gaussian distribution with mean $\boldsymbol { \mu } \in \mathbb { R } ^ { p }$ and covariance matrix $\Sigma \in \mathbb { R } ^ { p \times p }$ , and suppose we wish to constrain the false negative rate (FNR) for a linear model parameterized by $\theta \in \mathbb { R } ^ { p } .$ . Then the FNR at any threshold $\lambda \in \mathbb { R }$ is given by $\mathbb { P } _ { x \sim \mathcal { D } _ { + } } \left( \theta ^ { \top } x \le \lambda \right)$ , and the threshold λ at which the FNR is β is given by $\tilde { h } ( \theta ) = \Phi ^ { - 1 } ( \beta )$ , where Φ is the CDF of a normal distribution with mean $\theta ^ { \top } \mu$ and variance $\theta ^ { \top } \Sigma \theta$

Algorithm 1 Implicit Constrained Optimization (ICO)   
1: Hyper-parameters: OPT, $\tau \in \mathbb { N }$   
2: Intialize: $\theta ^ { 0 } , \lambda ^ { 0 }$   
3: For $t = 1$ to T :   
4: $\begin{array} { r } { \dot { H } ^ { t } = - \nabla _ { \theta } \tilde { g } ( \theta ^ { t } , \lambda ^ { t } ) / \frac { \partial \tilde { g } ( \theta ^ { t } , \lambda ^ { t } ) } { \partial \lambda } } \end{array}$   
5: $\begin{array} { r l } { G ^ { t } = \nabla _ { \theta } \tilde { f } ( \theta ^ { t } , \lambda ^ { t } ) + \frac { \partial \tilde { f } ( \theta ^ { t } , \lambda ^ { t } ) } { \partial \lambda } H ^ { t } } \end{array}$   
6: $\theta ^ { t + 1 } = { \bf O P T } ( \theta ^ { t } , \dot { G } ^ { t } )$ // optimizer step   
7: If t mod $N = 0 \colon$ // correction step   
8: Set $\lambda ^ { t + 1 } \mathrm { s . t . } g ( \theta ^ { t + 1 } , \lambda ^ { t + 1 } ) = \mathbf { 0 }$   
9: Else: // gradient based update for λ   
10: $\lambda ^ { t + 1 } = \lambda ^ { t } + \langle \nabla _ { \theta } \tilde { h } ( \theta ^ { t } ) , \theta ^ { t + 1 } - \theta ^ { t } \rangle$   
11: End If   
12: End For   
13: Return θ

where for simplicity we show the derivative for a scalar λ. We will further need the derivative of the implicit function h˜(·). Since $\tilde { g } ( \theta , \tilde { h } ( \theta ) ) = 0$ in this neighborhood, we have

$$
\begin{array} { c } { { \nabla _ { \boldsymbol { \theta } } \tilde { g } ( \boldsymbol { \theta } , \lambda ) + \frac { \partial \tilde { g } ( \boldsymbol { \theta } , \lambda ) } { \partial \lambda } \nabla _ { \boldsymbol { \theta } } \tilde { h } ( \boldsymbol { \theta } ) = 0 } } \\ { { \Longrightarrow \nabla _ { \boldsymbol { \theta } } \tilde { h } ( \boldsymbol { \theta } ) = - \frac { \nabla _ { \boldsymbol { \theta } } \tilde { g } ( \boldsymbol { \theta } , \lambda ) } { \frac { \partial \tilde { g } ( \boldsymbol { \theta } , \lambda ) } { \partial \lambda } } } } \end{array}\tag{4}
$$

This gives us the derivative of the implicit function which can be plugged into Eq. (3) to get the final gradients for model parameters θ.

## 3.3. Updating thresholds

Having performed the gradient update on θ with:

$$
\theta ^ { t + 1 } = \theta ^ { t } - \eta \nabla _ { \theta } \tilde { f } ( \theta ^ { t } , \tilde { h } ( \theta ^ { t } ) ) ,
$$

where $\eta > 0$ is a step-size parameter, what remains is to update the threshold. Again appealing to the Implicit Function Theorem, in the neighborhood around the current iterate $\theta ^ { t }$ , we can approximate the new threshold as:

$$
\begin{array} { r c l } { \lambda ^ { t + 1 } } & { = } & { \widetilde { h } ( \theta ^ { t + 1 } ) = \widetilde { h } ( \theta ^ { t } + \Delta \theta ) } \\ & { \approx } & { \widetilde { h } ( \theta ^ { t } ) + \langle \nabla _ { \theta } \widetilde { h } ( \theta ^ { t } ) , \Delta \theta \rangle } \\ & { = } & { \lambda ^ { t } + \langle \nabla _ { \theta } \widetilde { h } ( \theta ^ { t } ) , \Delta \theta \rangle . } \end{array}
$$

As this is an approximation, we employ a correction step after every N minibatch iterations that sets the threshold to satisfy the constraint exactly based on k accumulated minibatches. Note that for all the metrics described in Examples 3–5, this correction step can be performed efficiently using a straight-forward line search.

## 3.4. Practical improvements

Algorithm 1 outlines our overall approach. In our experiments, we found it effective to use the unrelaxed (and nonsmooth) rates, instead of surrogates, for the correction step, i.e. we set $\lambda ^ { t + 1 } = h ( \theta ^ { t + 1 } )$ , where h computes the threshold at which the unrelaxed $g ( \theta ^ { t + 1 } , \lambda ^ { t + 1 } ) = \mathbf { 0 }$

Regularization. In some of our experiments, particularly with smaller UCI datasets, we also impose a regularizer on the model parameters that penalizes $\| d \widetilde { g } ( \theta , \lambda ) / d \lambda \| ^ { 2 }$ w.r.t. θ. This encourages the optimization to prefer model parameters for which the constraint function varies smoothly as a function of the threshold. We expect that this will help the model to generalize better on unseen examples.

Optimizing objective with multiple constraints. For optimizing objectives involving multiple constraints (and hence multiple thresholds $\lambda = [ \lambda _ { 1 } , \ldots , \lambda _ { m } ] \in \mathbb { R } ^ { m } )$ , such as (partial) PR-AUC or ROC-AUC, a naïve implementation would need multiple gradient computations w.r.t. θ as follows:

$$
\begin{array} { r } { \nabla _ { \theta } \tilde { f } ( \theta , h _ { 1 } ( \theta ) , . . . , h _ { m } ( \theta _ { m } ) ) = \nabla _ { \theta } \tilde { f } ( \theta , \lambda ) - } \\ { \sum _ { i } \frac { \partial \tilde { f } ( \theta , \lambda ) } { \partial \lambda _ { i } } \frac { \nabla _ { \theta } \tilde { g } ( \theta , \lambda _ { i } ) } { \frac { \partial \tilde { g } ( \theta , \lambda _ { i } ) } { \partial \lambda _ { i } } } } \end{array}\tag{5}
$$

It needs computation of $\nabla _ { \theta } \tilde { g } ( \theta , \lambda _ { i } )$ for all m constraints. We avoid this by first computing the partial derivatives of $\tilde { f } ( \theta , \lambda )$ and $\tilde { g } ( \theta , \lambda _ { i } )$ w.r.t. $\lambda _ { i }$ which are much cheaper to compute, and then treating their ratios as constants $r _ { i }$ (akin to using stop-gradient). Denoting $\begin{array} { r l } { h ( \theta ) } & { { } = } \end{array}$ $\{ h _ { 1 } ( \theta ) , \dots , h _ { m } ( \theta _ { m } ) \}$ }, we then rewrite the gradient computation as

$$
\nabla _ { \boldsymbol { \theta } } \tilde { f } ( \theta , h ( \theta ) ) = \nabla _ { \boldsymbol { \theta } } \tilde { f } ( \theta , \lambda ) - \nabla _ { \boldsymbol { \theta } } \sum _ { i } r _ { i } \tilde { g } ( \theta , \lambda _ { i } ) ,\tag{6}
$$

which again reduces to just two gradient computations. We also disable the gradient based updates for thresholds to avoid computing separate $\nabla _ { \boldsymbol { \theta } } \tilde { g } ( \boldsymbol { \theta } , \lambda _ { i } )$ for all i, and only rely on the correction step of Algorithm 1 every τ minibatches.

## 4. Related Work

The problem of training models to optimize a given nondecomposable metrics has received much attention in the literature. Early methods on this topic focused on constructing convex surrogates that closely approximate the metric of interest (Joachims, 2005; Yue et al., 2007; Narasimhan & Agarwal, 2013a; Kar et al., 2014; Mohapatra et al., 2014; Narasimhan et al., 2015a), often using structured support vector machines (Tsochantaridis et al., 2005). One of the drawbacks of these approaches is that they are not directly amenable to handling constraints on multiple rates, and may sometimes result in a loose approximation to the metric (Kar et al., 2015). More recent methods seek to directly optimize a given rate metric subject to constraints on multiple rate metrics (Goh et al., 2016; Eban et al., 2017; Narasimhan, 2018; Cotter et al., 2019a;b; Narasimhan et al., 2019a), and come with scalable gradient-based solvers. There has also been work on construction of structured surrogates (Fathony & Kolter, 2020; Bao & Sugiyama, 2020).

There is also a distinction between methods which handle classification metrics such as the F-measure (Koyejo et al., 2014; Narasimhan et al., 2014; Yan et al., 2018), where often tuning a threshold on a pre-trained class probability model results in a consistent estimator, and those that handle scoring metrics such as the precision-recall and AUC metrics we consider in this paper (Eban et al., 2017), where the focus is on learning a scoring model that performs well at one or more operating thresholds. Other techniques focus on optimizing specialized evaluation metrics that, for example, emphasize good top-k performance in ranking and classification tasks (Agarwal, 2011; Boyd et al., 2012; Fan et al., 2017; Lapin et al., 2017; Hiranandani et al., 2020).

Our approach is most closely related to the method of Eban et al. (2017), who encode the given metric as constraints on classification rates, relax the rates with differentiable surrogates, and perform gradient updates to minimize over the model parameters, and maximize over the Lagrangian multipliers for the constraints. The recent work of Cotter et al. (2019b) and Narasimhan et al. (2019a) improves upon their method by observing that the use of surrogates is only required when minimizing over the model parameters, while the maximization over the Lagrange multipliers can be performed with the original unrelaxed rates. The resulting min-max problem can be interpreted as a non-zero-sum game, for which the authors provide efficient gradient-based algorithms to find an equilibrium. This selective use of surrogates is incorporated into our proposal: we use surrogates only when we need to compute gradients for the objective $\tilde { f } ( \theta , \tilde { h } ( \theta ) )$ , whereas, as we mentioned in Section 3.4, we use the original unrelaxed rates while computing a correction for the threshold $\lambda = h ( \theta )$

Unlike these earlier papers, our method avoids explicitly solving a constrained optimization problem, and instead expresses the threshold as an implicit function of the model parameters. This proposal is similar in flavor to the approach taken by Mackey et al. (2018), who like us formulate an unconstrained objective, but do so by expressing the threshold as a quantile of the model scores.

Finally, the growing literature on fairness in machine learning has opened the door for many new applications for constrained optimization (Hardt et al., 2016; Agarwal et al., 2018), introducing many group-based fairness metrics that can be easily handled using the proposed approach.

## 5. Experiments

We evaluate our approach on five UCI classifications tasks, and two image classification tasks. A summary of the datasets used in the main text is provided in Table 1. We present additional experimental results in Appendices B, C and D.

Table 1. Summary of datasets.
<table><tr><td>Datasets</td><td>#Examples</td><td>#Features</td></tr><tr><td>CelebA</td><td>202,599</td><td> $3 2 \times 3 2 \times 3$ </td></tr><tr><td>BigEarthNet</td><td>590,326</td><td> $4 0 \times 4 0 \times 3$ </td></tr><tr><td>Letter</td><td>19,999</td><td>16</td></tr><tr><td>IJCNN1</td><td>49990</td><td>22</td></tr><tr><td>Adult</td><td>48,842</td><td>122</td></tr><tr><td>Spambase</td><td>4,601</td><td>57</td></tr><tr><td>Com. &amp; Crime</td><td>1,994</td><td>145</td></tr></table>

Baselines. We compare the proposed ICO approach with the state-of-the-art tools of Cotter et al. (2019a) and Narasimhan et al. (2019a) for constrained optimization, open-sourced as a part of the TensorFlow Constrained Optimization Library $( \mathrm { T F C O } ) ^ { 2 }$ . The prior technique of Eban et al. (2017) can be viewed as a special case of the functionality provided by this library. We also compare to the baseline approach of optimizing a standard cross-entropy (CE) loss.

Experimental protocol. For our experiments with Image datasets, we use a 6-layer neural network with 5 convolutional layers with 128, 256, 256, 512 and 512 filters respectively. We use ReLU activation functions and batch normalization layers in the network. We use a separate validation split for model selection in all our experiments. For all three methods (CE, TFCO, and ICO), we use the evaluation metric of interest on the validation set for model selection (e.g., FNR, ROC-AUC, PR-AUC). This makes the CE baseline further strong in our experiment. We do 5 random trials for each experiment and report the average value of the metric. Other details such as standard deviations for the random trials are reported in the Appendix.

## 5.1. Minimizing FNR at FPR β

First, we consider the task of minimizing false negative rate (FNR) at a given false positive rate (FPR) of β. This setting is particularly relevant for security sensitive applications where one wants to operate at a desired false positive rate. We experiment with the publicly available CelebA dataset (Liu et al., 2015), which contains 202,599 celebrity face images of size $3 2 \times 3 2 \times 3 .$ CelebA has 40 annotated binary attributes for every face image, of which we randomly choose 8 for our experiments. We use the standard train, validation, and test splits3 for CelebA, and train a binary classifier for each attribute.

Table 2. Minimizing false negative rate (FNR) at a given false positive rate (FPR) for CelebA. The mean FNR (in %) are reported over five random trials for cross-entropy/ TFCO/ ICO, respectively. Proposed ICO outperforms both CE and TFCO by a considerable margin. We report results on more attributes along with the std. errors in Appendix C. Lower values are better.
<table><tr><td>PPFR</td><td>High-cheekbones</td><td>Heavy-makeup</td><td>Wearing-lipstick</td><td>Smiling</td><td>Black-hair</td><td>Blond-hair</td></tr><tr><td>1%</td><td>53.5/ 49.0/46.9</td><td>57.0/57.0/49.6</td><td>44.0/ 42.6/ 37.5</td><td>37.4/35.9/33.7</td><td>69.3/64.4/63.2</td><td>40.4/ 38.6/ 36.8</td></tr><tr><td>2%</td><td>44.8/ 40.9/39.8</td><td>45.6/41.2/38.9</td><td>32.7/ 30.4/ 26.7</td><td>29.4/ 27.8/ 26.1</td><td>56.4/ 52.0/ 50.5</td><td>28.9/ 25.6/ 24.2</td></tr><tr><td>5%</td><td>32.9/30.1/28.5</td><td>28.2/ 25.4/23.1</td><td>16.3/ 14.9/13.1</td><td>18.7/ 17.0/16.9</td><td>36.7/ 32.4/32.5</td><td>13.4/11.6/10.8</td></tr><tr><td>10%</td><td>22.9/ 20.4/19.7</td><td>15.1/13.6/12.4</td><td>6.6/ 5.9/4.7</td><td>11.7/ 10.7/10.2</td><td>23.0/ 19.2/18.6</td><td>6.5/ 4.9/4.7</td></tr></table>

Table 3. Maximizing area under the ROC curve for CelebA, in a given FPR range [0, β] for $\beta \in$ {1%, 2%, 5%, 10%, 20%}. The mean ROC-AUC are reported over five random trials for cross-entropy/ TFCO/ ICO, respectively. Last column shows the mean partial AUC over all 8 attributes. We report results on more attributes along with the std. errors in Appendix C. Higher values are better.
<table><tr><td> $\beta$ </td><td>High-cheekbones</td><td>Heavy-makeup</td><td>Wearing-lipstick</td><td>Smiling</td><td>Black-hair</td><td>Mean</td></tr><tr><td>1%</td><td>66.1/ 62.9/69.8</td><td>65.0/68.5/ 66.7</td><td>70.2/ 74.8/ 72.3</td><td>75.4/ 78.0/ 75.6</td><td>60.5/61.4/61.2</td><td>64.7/ 65.9/66.1</td></tr><tr><td>2%</td><td>70.8/ 74.9/ 73.2</td><td>68.8/ 73.4/ 71.6</td><td>75.4/ 79.3/ 78.4</td><td>78.4/81.5/ 79.8</td><td>64.5/66.5/ 66.1</td><td>68.6/ 70.8/ 70.5</td></tr><tr><td>5%</td><td>75.9/ 73.8/ 78.5</td><td>75.5/79.5/ 78.3</td><td>82.2/84.7/84.6</td><td>83.5/65.0/84.8</td><td>70.9/ 73.2/ 73.8</td><td>74.7/ 72.8/ 76.8</td></tr><tr><td>10%</td><td>80.1/74.1/82.7</td><td>81.5/85.0/84.4</td><td>87.7/89.3/89.7</td><td>86.7/73.8/88.8</td><td>78.0/ 79.9/80.2</td><td>79.7/77.9/81.8</td></tr><tr><td>20%</td><td>84.2/ 72.4/86.8</td><td>88.2/89.9/89.8</td><td>91.8/93.1/93.9</td><td>90.9/76.6/92.1</td><td>84.3/86.0/86.1</td><td>84.9/82.4/86.8</td></tr></table>

We use TFCO and ICO for optimizing FNR at four different FPR targets: 1%, 2%, 5% and 10%. For the cross-entropy baseline, we use Adam optimizer (Kingma & Ba, 2014) with a learning rate of 0.001. For TFCO, we use Adam for both the primal and dual updates; the primal learning rate is set to 0.001, while the dual learning rate is chosen from {0.1, 0.01} using the validation sample. We use the cross-entropy surrogate (softplus function for binary case) provided by the TFCO library to approximate the rates. For ICO, we again use Adam with a learning rate of 0.001. We approximate the rates for ICO with temperature-scaled sigmoid surrogates, and choose the temperature parameter from the range {0.001, 0.01, 0.1, 1.0} using the validation sample. We do not apply gradient regularization, and perform the correction step described in Section 3.4 once every 1000 mini-batch updates using data from next 10 mini-batches. All optimizers use a batch size of 512.

We present in Table 2 the test evaluation metrics. The proposed ICO method performs the best for all six prediction tasks and for all four FPR targets, with TFCO coming in second. Interestingly, the gap between ICO and the other methods is the larger for smaller FPR targets. This suggests that ICO is most advantageous when applied to metrics that are harder to optimize. Unsurprisingly, cross-entropy optimization often yields higher FNR values at the specified

Table 4. Maximizing area under the ROC curve for BigEarthNet, in a given FPR range [0, β] for $\beta \in \{ 5 \% , 1 0 \% , 2 0 \% \}$ The mean ROC-AUC are reported over five random trials for crossentropy/ TFCO/ ICO, respectively. We report results on more attributes along with the std. errors in Appendix D. Higher values are better.
<table><tr><td rowspan="2">Labels</td><td colspan="3"> $\beta$ </td></tr><tr><td>5%</td><td>10%</td><td>20%</td></tr><tr><td>BLF</td><td>66.2/66.4/69.9</td><td>71.0/71.7/73.9</td><td>75.4/76.2/77.9</td></tr><tr><td>CC</td><td>62.2/ 62.7/63.6</td><td>67.4/ 66.8/68.3</td><td>73.8/ 76.0/74.9</td></tr><tr><td>CF</td><td>71.9/71.5/74.7</td><td>78.6/ 80.0/80.7</td><td>84.8/86.6/86.0</td></tr><tr><td>DUF</td><td>69.8/71.8/ 73.9</td><td>75.1/77.2/78.0</td><td>78.8/81.4/81.8</td></tr><tr><td>ANV</td><td>58.8/58.8/60.4</td><td>62.7/63.9/64.4</td><td>67.8/69.1/69.0</td></tr><tr><td>Mean</td><td>65.8/66.2/68.5</td><td>71.0/71.9/73.1</td><td>76.1/77.9/77.9</td></tr></table>

FPR targets than the other methods, indicating that methods which directly optimize performance at the desired FPR do end up performing better at that target. Results on other attributes are reported in Appendix C. We also report timing comparisons of ICO and TFCO in Appendix B.

## 5.2. Maximizing ROC-AUC in FPR range [0, β]

Next, we consider the task of maximizing the (partial) area under the ROC curve in a select range [0, β] of FPRs. This metric is used in medical diagnostic tasks and biometric screening (Rao et al., 2008; Ricamato & Tortorella, 2011), where optimizing performance in a relevant FPR range may prove critical. We also compare with a pairwise loss baseline (Narasimhan & Agarwal, 2013b) which optimizes the objective $\begin{array} { r } { \frac { 1 } { N ^ { + } | S ^ { - } | } \mathop { \sum _ { i : y _ { i } = 1 } ^ { - } \sum _ { j \in S ^ { - } } \tilde { f } } ( s ^ { \theta } ( x _ { i } ) \bar { - } s ^ { \theta } ( x _ { j } ) ) } \end{array}$ , where $s ^ { \theta } ( x )$ denotes the score (e.g., logits) for example $x , N ^ { + }$ is the number of positive examples in the minibatch, $S ^ { - }$ is the subset of negative examples whose scores lie in the top $\beta$ fraction of all negative examples, and $\tilde { f }$ is the surrogate used for 0-1 loss (either softplus or sigmoid with a temperature hyperparameter as we used for the proposed method). We use the pairwise-loss, TFCO, and the proposed method to optimize this metric for five different value of $\beta \colon$ 1%, 2%, 5%, 10% and 20%. The results for the pairwise loss baseline are reported in the supplementary material. We experiment with CelebA and BigEarthNet (Sumbul et al., 2019) image datasets. BigEarthNet contains 590,326 Sentinel-2 image patches of size $1 2 0 \times 1 2 0 \times 3$ in RGB, which we downsize to $4 0 \times 4 0 \times 3$ , and 43 annotated binary labels, of which we choose 5 for our experiments. These lables are Broad-Leaved Forest (BLF), Complex Cultivation patterns (CC), Coniferous Forest (CF), Discontinuous Urban Fabric (DUF) and Agricultural with Natural Vegetation land (ANV). We split the dataset randomly into 70% for training, 15% for validation and 15% testing.

<!-- image-->

<!-- image-->  
(a) Wearing-lipstick attribute

<!-- image-->

<!-- image-->  
(b) Black-hair attribute

Figure 1. ROC curves for CelebA: (a) For attribute Wearing-lipstick and optimizing for partial area under the ROC curve with FPR ∈ [0, 0.2], (b): For attribute Black-hair and optimizing for partial area under the ROC curve with FPR ∈ [0, 0.05]. Left figures show full ROC curves while the right figures show the (zoomed-in) ROC curves in the respective target FPR ranges.  
<!-- image-->

<!-- image-->  
(a) Letter

<!-- image-->

<!-- image-->  
(b) IJCNN1  
Figure 2. Precision-Recall curves on the test set. Both TFCO and the proposed method seek to optimize PR-AUC in the recall range [0.95, 1]. The left plots for each dataset show the entire curve, while the right plots zoom in on the right-end of the curve.

For both datasets, we train the same convolutional neural network model as the previous experiment. Both TFCO and our method divide the specified FPR range [0, β] into

10 equally-spaced values, and optimize the average true positive rate (TPR) at those targets. We replicate the same parameter configurations used in the previous experiment, except that the update frequency for ICO is performed either once in every 100 updates or 1000 updates, based on which of the two choices yields the highest validation ROC-AUC. We do not use gradient regularization in this experiment.

We present in Table 3 the test evaluation metrics for different methods on CelebA, where we applied TFCO and ICO to optimize the partial ROC-AUC metric for five different values of β: 1%, 2%, 5%, 10% and 20%. We apply the standard McClish correction (McClish, 1989) to rescale the area between 0 and 100. On at least half the classification tasks, the proposed ICO method performs the best, with TFCO coming in second. On average across all six image attributes, ICO is considerably better than TFCO on three of the five values of FPR targets $\beta .$ We also show the ROC plots for a few specific cases in Figure 1. We present the results for BigEarthNet in Table 4, where we experiment with three values of β: 5%, 10%, 20%. For all five labels, the proposed ICO is seen to perform better than the baselines for the smaller false-positive ranges, i.e. for smaller $\beta ,$ thus demonstrating its effectiveness in optimizing performance in the initial portion of the ROC curve for this dataset. We also report timing comparisons of ICO and TFCO in Appendix B, observing that ICO can converge faster than TFCO in

Table 5. Maximizing (partial) PR-AUC in the recall range [0.95, 1] on UCI datasets. Proposed ICO performs better than the other methods on datasets with severe class imbalance. Higher values are better.
<table><tr><td></td><td>%Positives</td><td>Cross-entropy</td><td>TFCO</td><td>ICO</td></tr><tr><td>Letter</td><td>4%</td><td> $\overline { { 1 5 . 1 3 \pm 0 . 8 6 } }$ </td><td> $\overline { { 2 0 . 4 9 \pm 0 . 4 3 } }$ </td><td> $\overline { { 2 3 . 0 4 \pm 0 . 7 7 } }$ </td></tr><tr><td>IJCNN1</td><td>9.7%</td><td> $2 1 . 1 8 \pm 0 . 3 3$ </td><td> $2 6 . 1 4 \pm 0 . 5 7$ </td><td> ${ \bf 2 7 . 2 8 \pm 0 . 5 8 }$ </td></tr><tr><td>Adult</td><td>24%</td><td> $3 9 . 7 4 \pm 0 . 2 9$ </td><td> $4 0 . 2 1 \pm 0 . 3 8$ </td><td> ${ \bf 4 0 . 3 4 \pm 0 . 4 1 }$ </td></tr><tr><td>Spam</td><td>39%</td><td> $7 1 . 5 1 \pm 1 . 7 3$ </td><td> $7 3 . 0 8 \pm 1 . 7 0$ </td><td> ${ \bf 7 3 . 4 8 \pm 1 . 8 0 }$ </td></tr><tr><td>Com. &amp; Crime</td><td>30%</td><td> $4 7 . 0 0 \pm 0 . 9 4$ </td><td> $4 7 . 0 4 \pm 0 . 9 7$ </td><td> $4 7 . 0 3 \pm 1 . 0 8$ </td></tr></table>

terms of wall-clock time.

## 5.3. Maximizing PR-AUC in Recall Range [β, 1]

In our final set of experiments, we consider the task of maximizing the (partial) area under the Precision-Recall curve in a select range of recall values [β, 1]. This metric is relevant in retrieval applications, where the quality of the system is often evaluated at multiple recall targets. We experiment with the five smaller datasets in Table 1 obtained from the UCI repository (Frank & Asuncion, 2010). For the Letter dataset, we treat the most frequent letter as the positive example, and the rest as negative. For the Communities & Crime dataset, we seek to predict if a community in the US has a crime rate above the 70th percentile (Kearns et al., 2018). We trained a linear model in each case. We split the datasets into train, validation and test datasets in the ratios 50%:25%:25%.

Both TFCO and ICO divide the specified recall range [β, 1] into five equally-spaced values, and optimize the average precision at those targets. We use Adam for the crossentropy baseline and for TFCO, and Adagrad for the proposed ICO. For cross-entropy optimization, we tune the learning rate from the range $\mathrm { \dot { \{ 1 0 ^ { - 3 } , 1 0 ^ { - 2 } , 1 0 ^ { - 1 } , 1 \} } }$ , picking the one with maximum PR-AUC metric on the validation sample. For TFCO, we tune the learning rate and dual scale parameters from the range {0.01, 0.1, 1.0} and {0.1, 1.0, 10.0} respectively. We approximated the rates for TFCO using the cross-entropy surrogate loss provided by the library. For the proposed ICO, we use a fixed learning rate of 0.1, and approximate the rates with a temperaturescaled sigmoid surrogates, with the temperature parameter for the surrogate chosen from {0.5, 1.0, 5.0}. We also apply the gradient regularizer described in Section 3.4, with the regularization strength parameter chosen from the range {0, 0.05, 0.1}. We perform the correction step once every 10 updates. All optimizers perform full gradient updates.

We first evaluate the performance of different methods at very high recall values. For this, we run both TFCO and ICO to optimize average precision in the recall range [0.95, 1]. Table 5 presents the test PR-AUC metric values in the range [0.95, 1] for the different methods. We find that on the Letter and IJCNN1 datasets, which have severe class imbalance, the proposed approach performs significantly better than the two baselines. On these datasets, cross-entropy optimization performs poorly. On the datasets where the classes are reasonably balanced, all three baselines perform similarly. On the Communities & Crime dataset, we find our approach yielding better metric values than the other methods on the training sample, but because of the small data size, does not generalize as well to the test set.

In Figure 2, we show the Precision-Recall cuves for the different methods for the the Letter and IJCNN1 datasets. Notice that while cross-entropy optimization yields higher precision for lower recall values, it does not fair well in the recall range that matters [0.95, 1]. Clearly, there is notable benefit to directly optimizing for the recall range that we care about instead of using an off-the-shelf loss function. Moreover, the proposed ICO method outperforms TFCO at high recall values. We also apply the methods to optimize PR-AUC in recall ranges [β, 1], for varying values of β. In the results shown in Figure 3 for the Letter and IJCNN1 datasets, one can see that the benefit offered by ICO is the most benefit over the two baselines is most notable for higher β values.

## 6. Discussion and Future Work

We proposed an approach for optimizing popular constrained optimization problems arising in machine learning that involve non-decomposable rate metrics, such as false positive rate, true positive rate, areas under the precisionrecall or ROC curves, etc.. Our approach deviates significantly from the existing methods based on Lagrange multipliers, and uses Implicit Function Theorem to express the classifier thresholds as a function of model parameters. Our experiments showed considerable improvements on optimizing several common evaluation metrics (such as FNR at a fixed FPR, areas under (partial) precision-recall and ROC curves) over existing state-of-the-art methods (Cotter et al., 2019a; Narasimhan et al., 2019a) that are part of open-source tools. In this work, we primarily focused on the straightforward setting where the classifier thresholds are expressed as a function of all model parameters but it is also possible to consider an alternative setting where the thresholds are expressed as a function of only a subset of model parameters $( e . g .$ , last few layers of the neural network). We leave this as a direction for future work.

<!-- image-->

(a) Letter  
<!-- image-->  
(b) IJCNN1  
Figure 3. Plot of PR-AUC in [β, 1] as a function of $\beta$ on the Letter and IJCNN1 datasets. The proposed method is often advantageous for very high β values. Higher values are better.

We close by highlighting how our proposal can be extended to handle more complex settings and constraints.

## 6.1. Inequality constraints

All the constrained metrics we described are defined as equality constraints. In our current implementation, we handle inequality constraints by searching for thresholds that satisfy the original non-smooth inequality constraints (during the correction step in Algorithm 1 and finally at the end of training). However, we can easily extend our proposal to handle inequality constraints of the form $\tilde { g } ( \theta , \lambda ) \leq \mathbf { 0 }$ in a more principled manner. In this case, one can introduce m auxiliary slack variables $\xi _ { 1 } , \ldots , \xi _ { m } \in \mathbb { R } _ { + }$ , and rewrite the inequality-constrained problem as one with equality constraints:

$$
\operatorname* { m i n } _ { \theta \in \mathbb { R } ^ { p } , \xi \in \mathbb { R } _ { + } ^ { m } } \tilde { f } ( \theta , \lambda ) \quad \mathrm { s . t . } \tilde { g } ( \theta , \lambda ) + \xi = \mathbf { 0 } .\tag{7}
$$

We can now apply Algorithm 1 to solve the re-written problem by treating the model parameters and auxiliary variables $( \theta , \xi ) \in \mathbb { R } ^ { p } \times \mathbb { R } _ { + } ^ { m }$ together as the optimization variables, with an additional projection step in the gradient descent procedure to ensure non-negativity of the $\xi _ { i } \mathbf { s }$ . We did not experiment with this version of the algorithm for the sake of implementation simplicity.

## 6.2. Multi-class metrics

In our experiments, we handled binary classification tasks. The extension to multi-class metrics requires some effort as in this case we are allowed to predict only one among m labels. As with the binary classification setting, we work with a model $s ^ { \theta } : X {  } \mathbb { R } ^ { m }$ that outputs m scores, and we will maintain one parameter $\lambda _ { i }$ for each class $i \in [ m ]$ . The parameters $\lambda _ { i } \mathbf { \bar { s } }$ would then be used to post-shift the model via a weighted or shifted argmax to predict the final class:

$$
s _ { \lambda } ^ { \theta } ( x ) \in \mathop { \mathrm { a r g } } \operatorname* { m a x } _ { i \in [ m ] } ( s _ { i } ^ { \theta } ( x ) - \lambda _ { i } ) .
$$

Computing the parameters λs so that the resulting classifier satisfies the specified constraints is not straightforward, but can still be performed efficiently with, $e . g .$ ., the methods in Narasimhan et al. (2015b). While it isn’t clear if a feasible λ exists for general rate constraints, it certainly does for constraints like “coverage” (Cotter et al., 2019a), which require that the model makes a certain percentage of predictions from each class.

## 6.3. Ranking metrics

Perhaps, the most interesting extension of our approach is to query-based ranking problems (Schütze et al., 2008), where each example contains a query and a list of documents, and the goal is to rank the documents based on the relevance to the query. Popular ranking metrics such as Precision@K or Recall@K seek to measure performance in the top ranked documents (Lapin et al., 2017). Unfortunately, writing these metrics out as an explicit constrained optimization problem would require one constraint per query, with the number of constraints growing with the size of the training set. Consequently, standard constrained optimization approaches, when applied to optimize these metrics, would need to maintain one Lagrange multiplier for each query, making it impractical to use them with large datasets. Recently, (Narasimhan et al., 2019b) propose solving such heavily-constrained problems with lower-dimensional representations of Lagrange multipliers. In contrast, our method offers an alternate route which does not require explicitly handling the large number of constraints, through implicit modeling of the per-query thresholds. We look forward to future work comparing our implicit thresholding approach with the state-of-the-art methods for these ranking metrics (e.g. Kar et al. (2015); Lapin et al. (2017)).

## References

Agarwal, A., Beygelzimer, A., Dudik, M., Langford, J., and Wallach, H. A reductions approach to fair classification. In International Conference on Machine Learning, pp. 60–69, 2018.

Agarwal, S. The infinite push: A new support vector ranking

algorithm that directly optimizes accuracy at the absolute top of the list. In Proceedings of the 2011 SIAM International Conference on Data Mining, pp. 839–850. SIAM, 2011.

Bao, H. and Sugiyama, M. Calibrated surrogate maximization of linear-fractional utility in binary classification. In International Conference on Artificial Intelligence and Statistics, pp. 2337–2347. PMLR, 2020.

Biddle, D. Adverse impact and test validation: A practitioner’s guide to valid and defensible employment testing. Gower Publishing, Ltd., 2006.

Boyd, S., Cortes, C., Mohri, M., and Radovanovic, A. Accuracy at the top. In Advances in Neural Information Processing Systems, 2012.

Cotter, A., Jiang, H., Gupta, M. R., Wang, S., Narayan, T., You, S., and Sridharan, K. Optimization with nondifferentiable constraints with applications to fairness, recall, churn, and other goals. Journal of Machine Learning Research, 20(172):1–59, 2019a.

Cotter, A., Jiang, H., and Sridharan, K. Two-player games for efficient non-convex constrained optimization. In Algorithmic Learning Theory, pp. 300–332. PMLR, 2019b.

Eban, E., Schain, M., Mackey, A., Gordon, A., Rifkin, R., and Elidan, G. Scalable learning of non-decomposable objectives. In Artificial intelligence and statistics, pp. 832–840. PMLR, 2017.

Fan, Y., Lyu, S., Ying, Y., and Hu, B.-G. Learning with average top-k loss. arXiv preprint arXiv:1705.08826, 2017.

Fathony, R. and Kolter, Z. Ap-perf: Incorporating generic performance metrics in differentiable learning. In International Conference on Artificial Intelligence and Statistics, pp. 4130–4140. PMLR, 2020.

Frank, A. and Asuncion, A. UCI machine learning repository. URL: http://archive.ics.uci.edu/ml, 2010.

Goh, G., Cotter, A., Gupta, M., and Friedlander, M. P. Satisfying real-world goals with dataset constraints. In Advances in Neural Information Processing Systems, pp. 2415–2423, 2016.

Hardt, M., Price, E., and Srebro, N. Equality of opportunity in supervised learning. In Advances in neural information processing systems, pp. 3315–3323, 2016.

Hiranandani, G., Vijitbenjaronk, W., Koyejo, S., and Jain, P. Optimization and analysis of the pap@ k metric for recommender systems. In International Conference on Machine Learning, pp. 4260–4270. PMLR, 2020.

Joachims, T. A support vector method for multivariate performance measures. In Proceedings of the 22nd international conference on Machine learning, pp. 377–384. ACM, 2005.

Kar, P., Narasimhan, H., and Jain, P. Online and stochastic gradient methods for non-decomposable loss functions. arXiv preprint arXiv:1410.6776, 2014.

Kar, P., Narasimhan, H., and Jain, P. Surrogate functions for maximizing precision at the top. In International Conference on Machine Learning, pp. 189–198. PMLR, 2015.

Kearns, M., Neel, S., Roth, A., and Wu, Z. Preventing fairness gerrymandering: Auditing and learning for subgroup fairness. In ICML, 2018.

Kingma, D. P. and Ba, J. Adam: A method for stochastic optimization. ICLR, 2014.

Koyejo, O. O., Natarajan, N., Ravikumar, P. K., and Dhillon, I. S. Consistent binary classification with generalized performance metrics. In NIPS, pp. 2744–2752, 2014.

Lapin, M., Hein, M., and Schiele, B. Analysis and optimization of loss functions for multiclass, top-k, and multilabel classification. IEEE transactions on pattern analysis and machine intelligence, 40(7):1533–1554, 2017.

Liu, Z., Luo, P., Wang, X., and Tang, X. Deep learning face attributes in the wild. In Proceedings of the IEEE International Conference on Computer Vision, pp. 3730– 3738, 2015.

Mackey, A., Luo, X., and Eban, E. Constrained classification and ranking via quantiles. arXiv preprint arXiv:1803.00067, 2018.

McClish, D. K. Analyzing a portion of the roc curve. Medical Decision Making, 9(3):190–195, 1989.

Mohapatra, P., Jawahar, C., and Kumar, M. P. Efficient optimization for average precision SVM. In NIPS-Advances in Neural Information Processing Systems, 2014.

Narasimhan, H. Learning with complex loss functions and constraints. In International Conference on Artificial Intelligence and Statistics, pp. 1646–1654, 2018.

Narasimhan, H. and Agarwal, S. A structural svm based approach for optimizing partial auc. In International Conference on Machine Learning, pp. 516–524. PMLR, 2013a.

Narasimhan, H. and Agarwal, S. Svmpauctight: a new support vector method for optimizing partial auc based on a tight convex upper bound. In Proceedings of the 19th ACM SIGKDD international conference on Knowledge discovery and data mining, pp. 167–175, 2013b.

Narasimhan, H., Vaish, R., and Agarwal, S. On the statistical consistency of plug-in classifiers for non-decomposable performance measures. In Advances in Neural Information Processing Systems, pp. 1493–1501, 2014.

Narasimhan, H., Kar, P., and Jain, P. Optimizing nondecomposable performance measures: A tale of two classes. In International Conference on Machine Learning, pp. 199–208. PMLR, 2015a.

Narasimhan, H., Ramaswamy, H., Saha, A., and Agarwal, S. Consistent multiclass algorithms for complex performance measures. In ICML, pp. 2398–2407, 2015b.

Narasimhan, H., Cotter, A., and Gupta, M. Optimizing generalized rate metrics with three players. In Advances in Neural Information Processing Systems, pp. 10747– 10758, 2019a.

Narasimhan, H., Cotter, A., Zhou, Y., Wang, S., and Guo, W. Approximate heavily-constrained learning with lagrange multiplier models. In Advances in Neural Information Processing Systems, pp. 10747–10758, 2019b.

Rao, R. B., Yakhnenko, O., and Krishnapuram, B. Kdd cup 2008 and the workshop on mining medical data. ACM SIGKDD Explorations Newsletter, 10(2):34–38, 2008.

Ricamato, M. T. and Tortorella, F. Partial auc maximization in a linear combination of dichotomizers. Pattern Recognition, 44(10-11):2669–2677, 2011.

Schütze, H., Manning, C. D., and Raghavan, P. Introduction to information retrieval, volume 39. Cambridge University Press Cambridge, 2008.

Sumbul, G., Charfuelan, M., Demir, B., and Markl, V. Bigearthnet: A large-scale benchmark archive for remote sensing image understanding. In IGARSS 2019-2019 IEEE International Geoscience and Remote Sensing Symposium, pp. 5901–5904. IEEE, 2019.

Tsochantaridis, I., Joachims, T., Hofmann, T., Altun, Y., and Singer, Y. Large margin methods for structured and interdependent output variables. Journal of machine learning research, 6(9), 2005.

Tu, L. W. An introduction to manifolds. second, 2011.

Wurker, U. Convexity properties of some implicit functions. Journal of Convex Analysis, 2001.

Yan, B., Koyejo, S., Zhong, K., and Ravikumar, P. Binary classification with karmic, threshold-quasi-concave metrics. In International Conference on Machine Learning, pp. 5531–5540. PMLR, 2018.

Yue, Y., Finley, T., Radlinski, F., and Joachims, T. A support vector method for optimizing average precision. In Proceedings of the 30th annual international ACM SIGIR conference on Research and development in information retrieval, pp. 271–278, 2007.

Zafar, M. B., Valera, I., Rogriguez, M. G., and Gummadi, K. P. Fairness constraints: Mechanisms for fair classification. In Artificial Intelligence and Statistics, pp. 962–970. PMLR, 2017.

We provide more details, in particular:

Appendix A: Proof of Proposition 1.

Appendix B: Run-time comparisons, i.e. progress in terms of the evaluation metric on the validation and test sets as a function of training time.

Appendix C: More experiments on CelebA.

Appendix D: More experiments on BigEarthNet.

## A. Proof of Proposition 1

The assumption in Proposition 1 holds, for example, when we seek to minimize the FPR subject to $\mathrm { F N R } = \beta .$ . In this case, the FPR objective can be approximated by $\tilde { f } ( \theta , \lambda ) =$ $\mathbb { E } _ { x \sim D _ { 0 } } \left[ \ell \left( - 1 , \bar { \theta ^ { \top } } x + \lambda \right) \right]$ and the FNR constraint can be approximated by $\begin{array} { r } { \tilde { g } ( \theta , \lambda ) \overset {  } { = } \mathbb { E } _ { x \sim \mathcal { D } _ { 1 } } [ \ell ( + 1 , \theta ^ { \top } x + \lambda ) ] - } \end{array}$ $\beta ,$ where $\ell ( y , z ) = \log ( 1 + e ^ { - y z } )$ is the standard logistic loss, and $\mathcal { D } _ { 0 }$ and $\mathcal { D } _ { 1 }$ are respectively the class-conditional distributions over examples with labels 0 and 1. Note that $\tilde { f } ( \theta , \lambda )$ is jointly convex in $( \theta , \lambda )$ and is strictly increasing in $\lambda ,$ while $\tilde { g } ( \theta , \lambda )$ is jointly convex in $( \theta , \lambda )$ and is strictly decreasing in λ.

Proof of Proposition 1. From the joint convexity of ${ \tilde { g } } ,$ , we have for any (θ, λ) and $( \theta ^ { \prime } , \lambda ^ { \prime } )$

$$
\langle \nabla _ { \theta } \tilde { g } ( \theta ^ { \prime } , \lambda ^ { \prime } ) , \theta - \theta ^ { \prime } \rangle + \frac { \partial \tilde { g } ( \theta ^ { \prime } , \lambda ^ { \prime } ) } { \partial \lambda } ( \lambda - \lambda ^ { \prime } ) \leq \tilde { g } ( \theta , \lambda ) - \tilde { g } ( \theta ^ { \prime } , \lambda ^ { \prime } ) .
$$

Therefore this also holds for $( \theta , { \tilde { h } } ( \theta ) )$ and $\left( \theta ^ { \prime } , \tilde { h } ( \theta ^ { \prime } ) \right)$

$$
\langle \nabla _ { \theta } \tilde { g } ( \theta ^ { \prime } , \tilde { h } ( \theta ^ { \prime } ) ) , \theta - \theta ^ { \prime } \rangle + \frac { \partial \tilde { g } ( \theta ^ { \prime } , \tilde { h } ( \theta ^ { \prime } ) ) } { \partial \lambda } ( \tilde { h } ( \theta ) - \tilde { h } ( \theta ^ { \prime } ) ) \leq \tilde { g } ( \theta , \tilde { h } ( \theta \beta ) ) \underset { \mathrm { t e r m s ~ o f ~ t r a i n i m } } { \operatorname* { i n e s } } ~
$$

Because $g$ is strictly decreasing in $\begin{array} { r } { \lambda , \frac { \partial \tilde { g } ( \theta ^ { \prime } , \tilde { h } ( \theta ^ { \prime } ) ) } { \partial \lambda } < 0 } \end{array}$ , and therefore we can rewrite the above inequality as:

$$
\frac { 1 } { \frac { \partial \tilde { g } ( \theta ^ { \prime } , \tilde { h } ( \theta ^ { \prime } ) ) } { \partial \lambda } } \langle \nabla _ { \theta } \tilde { g } ( \theta ^ { \prime } , \tilde { h } ( \theta ^ { \prime } ) ) , \theta - \theta ^ { \prime } \rangle + \tilde { h } ( \theta ) - \tilde { h } ( \theta ^ { \prime } ) \geq 0 ,
$$

Using the fact that $\begin{array} { r } { \nabla _ { \boldsymbol { \theta } } \tilde { h } ( \boldsymbol { \theta } ^ { \prime } ) = - \frac { \nabla _ { \boldsymbol { \theta } } \tilde { g } ( \boldsymbol { \theta } ^ { \prime } , \tilde { h } ( \boldsymbol { \theta } ^ { \prime } ) ) } { \frac { \partial \tilde { g } ( \boldsymbol { \theta } ^ { \prime } , \tilde { h } ( \boldsymbol { \theta } ^ { \prime } ) ) } { \partial \lambda } } } \end{array}$ (see (4) in the main text), we have:

$$
\langle \nabla _ { \theta } \tilde { h } ( \theta ^ { \prime } ) , \theta ^ { \prime } - \theta \rangle \geq \tilde { h } ( \theta ^ { \prime } ) - \tilde { h } ( \theta ) ,
$$

or

$$
\tilde { h } ( \theta ) \geq \tilde { h } ( \theta ^ { \prime } ) + \langle \nabla _ { \theta } \tilde { h } ( \theta ^ { \prime } ) , \theta - \theta ^ { \prime } \rangle .
$$

This shows that $\tilde { h }$ is convex in $\theta .$ The convexity of $\tilde { f } ( \theta , \tilde { h } ( \theta ) )$ follows from the convexity of $\tilde { f }$ and $\tilde { h } .$ , and from the fact that $\tilde { f }$ is monotonically increasing in its second argument.

## B. Timing comparisons

We monitor the performance of TFCO and ICO in terms of value of the evaluation metric as the training proceeds. At the end of every training epoch, we record the best value of metric seen so far on the validation set, and use the same model (that yields the best validation metric) to score the test set.

<!-- image-->

<!-- image-->

Figure 4. Minimizing false negative rate (FNR) at a fixed false positive rate (FPR) of 0.05 for CelebA: FNR as a function of training epochs for TFCO and the proposed ICO.  
<!-- image-->

<!-- image-->  
Figure 5. Minimizing false negative rate (FNR) at a fixed false positive rate (FPR) of 0.05 for CelebA: FNR as a function of wall-clock time for TFCO and the proposed ICO.

For the problem of optimizing false negative rate (FNR) at a fixed false positive rate (FPR) on CelebA, Figures 4 and 5 show these FNR values for the attribute High_Cheekbones n and test sets as the training proceeds in ng epochs and actual wall-clock time, respectively. We observe that while TFCO converges to a much lower FNR at the end of the first epoch (the first data point shown in Figure 4), the proposed ICO eventually achieves a lower FNR on both validation and test sets. Both TFCO and ICO were trained for 40 epochs in these experiments and TFCO was about 1.3x faster in terms of wall-clock time.

We repeat similar experiment for the problem of optimizing the partial area under the ROC curve for FPR in the range of [0, 0.1], again for CelebA. Figure 6 and 7 show the ROC-AUC on validation and test sets for the High_Cheekbones attributes as the training proceeds in terms of epochs and wall-clock time, respectively. We observe similar behavior as in the earlier experiment and TFCO converges to a much better ROC-AUC early on in the training at the end of first epoch (first data point in the plots). However, the proposed ICO eventually achieves a better ROC-AUC both on validation and test sets. Both TFCO and ICO were trained for 25 epochs in this experiment and ICO is about 5x faster than TFCO in terms of wall-clock time. This is due to the fact that optimizing ROC-AUC is a problem with multiple constraints (10 in this case) and we do not optimize the thresholds using gradients in ICO and only rely on the ted in the main text due to space constraints. We also compare with the pairwise loss baseline for partial AUC as described earlier. The proposed ICO outperforms crossentropy and pairwise loss baselines in all the cases, and also outperforms TFCO for most cases.

<!-- image-->

<!-- image-->

Figure 6. Maximizing partial area under the ROC curve (for FPR ∈ [0, 0.1]) for CelebA: ROC-AUC as a function of training epochs for TFCO and the proposed ICO.  
<!-- image-->

<!-- image-->  
Figure 7. Maximizing partial area under the ROC curve (for FPR $\in [ 0 , 0 . 1 ] ) f o r$ CelebA: ROC-AUC as a function of wall-clock time for TFCO and the proposed ICO.

threshold correction step after every 100 minibatches. On the other hand, TFCO training time per minibatch slows down due to multiple constraints.

## C. CelebA results

We report results on more CelebA attributes for the two problems considered in the main text: (i) Minimizing false negative rate (FNR) at a fixed false positive rate (FPR) for $\mathrm { F P R s } \in \{ 1 \% , 2 \% , 5 \% , 1 0 \% \}$ (Table 6), and (ii) Maximizing partial area under the ROC curve (ROC-AUC) for FPR in the range $[ 0 , \beta ]$ for $\beta \in \{ 1 \% , 2 \% , 5 \% , 1 0 \% , 2 0 \% \}$ (Table 7). These results also show the standard deviation over five random trials which were omitted in the main text due to space constraints. For partial AUC in the FPR range $[ 0 , \beta ]$ , we also compare with a pairwise loss baseline (Narasimhan & Agarwal, 2013b) which optimizes the objective $\begin{array} { r } { \frac { 1 } { N ^ { + } | S ^ { - } | } \sum _ { i : y _ { i } = 1 } \sum _ { j \in S ^ { - } } \tilde { f } ( s ^ { \theta } ( x _ { i } ) - s ^ { \theta } ( x _ { j } ) ) } \end{array}$ , where $s ^ { \theta } ( x )$ denotes the score (e.g., logits) for example $x , N ^ { + }$ is the number of positive examples in the minibatch, $S ^ { - }$ is the subset of negative examples whose scores lie in the top $\beta$ fraction of all negative examples, and $\tilde { f }$ is the surrogate used for 0-1 loss (either softplus or sigmoid with a temperature hyperparameter as we used for the proposed method).

## D. BigEarthNet results

We also report results on more BigEarthNet labels for the problem of maximizing partial area under the ROC curve (ROC-AUC) for FPR in the range $[ 0 , \beta ]$ for $\beta \ \in$ {5%, 10%, 20%} (Table 8). These results also show the standard deviation over five random trials which were omit-

Table 6. Minimizing false negative rate (FNR) at a given false positive rate (FPR) for CelebA. The mean FNR (in %) are reported over five random trials, along with std. deviations, for cross-entropy (CE), TFCO and ICO. Proposed ICO outperforms both CE and TFCO by a considerable margin in most cases. Lower values are better. We also list the hyperparameters for ICO: surrogate function for both objective and constraint is taken to be softplus; correction step in Alg. 1 is applied every 1000 minibatch steps (N = 1000) using data from next 10 minibatches (k = 10); the temperature hyperparameter τ for softplus is provided in the Table below.
<table><tr><td>Attributes</td><td>FPR</td><td>CE</td><td>TFCO</td><td>ICO</td><td>ICO hyperparameter T</td></tr><tr><td rowspan="4">High-cheekbones</td><td>1%</td><td>53.52 (1.71)</td><td>49.09 (1.56)</td><td>46.96 (0.55)</td><td>0.01</td></tr><tr><td>2%</td><td>44.82 (1.23)</td><td>40.89 (0.82)</td><td>39.84 (0.49)</td><td>0.01</td></tr><tr><td>5%</td><td>32.87 (0.83)</td><td>30.11 (0.67)</td><td>28.54 (0.30)</td><td>0.01</td></tr><tr><td>10%</td><td>22.88 (0.43)</td><td>20.37 (0.65)</td><td>19.66 (0.36)</td><td>0.01</td></tr><tr><td rowspan="4">Heavy-makeup</td><td>1%</td><td>57.00 (0.84)</td><td>52.07 (1.24)</td><td>49.65 (0.81)</td><td>1</td></tr><tr><td>2%</td><td>45.59 (1.24)</td><td>41.23 (1.41)</td><td>38.89 (0.80)</td><td>0.001</td></tr><tr><td>5%</td><td>28.22 (0.80)</td><td>25.43 (0.97)</td><td>23.11 (0.70)</td><td>0.001</td></tr><tr><td>10%</td><td>15.12 (0.44)</td><td>13.61 (0.77)</td><td>12.36 (0.19)</td><td>0.01</td></tr><tr><td rowspan="4">Wearing-lipstick</td><td>1%</td><td>44.00 (1.28)</td><td>42.64 (1.29)</td><td>37.47 (0.97)</td><td>1</td></tr><tr><td>2%</td><td>32.74 (0.88)</td><td>30.44 (1.51)</td><td>26.74 (0.50)</td><td>0.01</td></tr><tr><td>5%</td><td>16.33 (0.43)</td><td>14.97 (0.77)</td><td>13.05 (0.25)</td><td>0.001</td></tr><tr><td>10%</td><td>6.61 (0.27)</td><td>5.92 (0.21)</td><td>4.78 (0.12)</td><td>0.001</td></tr><tr><td rowspan="4">Smiling</td><td>1%</td><td>37.40 (1.30)</td><td>35.93 (1.37)</td><td>33.74 (0.71)</td><td>0.01</td></tr><tr><td>2%</td><td>29.44 (0.76)</td><td>27.80 (1.23)</td><td>26.10 (0.57)</td><td>0.01</td></tr><tr><td>5%</td><td>18.73 (0.53)</td><td>17.04 (0.80)</td><td>16.88 (0.25)</td><td>0.01</td></tr><tr><td>10%</td><td>11.78 (0.20)</td><td>10.74 (0.29)</td><td>10.23 (0.25)</td><td>0.01</td></tr><tr><td rowspan="4">Black-hair</td><td>1%</td><td>69.32 (1.78)</td><td>64.47 (1.55)</td><td>63.23 (1.19)</td><td>0.001</td></tr><tr><td>2%</td><td>56.48 (1.48)</td><td>52.00 (1.10)</td><td>50.50 (0.67)</td><td>0.001</td></tr><tr><td>5%</td><td>36.72 (1.61)</td><td>32.41 (0.60)</td><td>32.48 (0.66)</td><td>0.001</td></tr><tr><td>10%</td><td>22.97 (1.87)</td><td>19.16 (1.22)</td><td>18.62 (0.43)</td><td>0.001</td></tr><tr><td rowspan="4">Blond-hair</td><td>1%</td><td>40.49 (1.18)</td><td>38.62 (1.17)</td><td>36.85 (0.58)</td><td>0.01</td></tr><tr><td>2%</td><td>28.89 (1.17)</td><td>25.64 (1.20)</td><td>24.20 (0.72)</td><td>0.001</td></tr><tr><td>5%</td><td>13.44 (1.01)</td><td>11.64 (0.76)</td><td>10.81 (0.24)</td><td>0.001</td></tr><tr><td>10%</td><td>6.54 (0.46)</td><td>4.91 (0.22)</td><td>4.68 (0.20)</td><td>0.001</td></tr><tr><td rowspan="4">Brown-hair</td><td>1%</td><td>80.75 (1.82)</td><td>77.16 (0.74)</td><td>76.34 (0.78)</td><td>0.001</td></tr><tr><td>2%</td><td>69.69 (1.77)</td><td>66.10 (1.04)</td><td>65.74 (1.28)</td><td>0.001</td></tr><tr><td>5%</td><td>52.41 (2.55)</td><td>45.83 (0.92)</td><td>46.43 (0.51)</td><td>0.001</td></tr><tr><td>10%</td><td>35.92 (2.71)</td><td>29.94 (0.87)</td><td>30.02 (0.67)</td><td>0.001</td></tr><tr><td rowspan="4">Wavy-hair</td><td>1%</td><td>85.04 (0.80)</td><td>84.42 (0.95)</td><td>83.54 (0.69)</td><td>0.001</td></tr><tr><td>2%</td><td>78.91 (1.20)</td><td>77.02 (1.47)</td><td>76.07 (0.90)</td><td>0.001</td></tr><tr><td>5%</td><td>65.79 (1.77)</td><td>61.81 (0.92)</td><td>60.71 (1.01)</td><td>0.001</td></tr><tr><td>10%</td><td>50.52 (1.41)</td><td>47.49 (0.98)</td><td>45.95 (1.12)</td><td>0.001</td></tr></table>

Table 7. Maximizing area under the ROC curve for CelebA, in a given FPR range [0, β] for $\beta \in \{ 1 \% , 2 \% , 5 \% , 1 0 \% , 2 0 \% \}$ The mean ROC-AUC are reported over five random trials, along with std. deviations, for cross-entropy (CE), Pairwise-loss, TFCO and ICO. Higher values are better. We also list the hyperparameters for ICO: surrogate function for both objective and constraint is taken to be sigmoid; the correction step in Alg. 1 is applied every N minibatch steps using data from next k minibatches. The values of N, k, and the temperature hyperparameter τ for sigmoid are selected on the validation set and are provided in the Table below.
<table><tr><td>Attributes</td><td>FPR</td><td>CE</td><td>Pairwise-loss</td><td>TFCO</td><td>ICO</td><td>ICO hyperparameters</td></tr><tr><td rowspan="5">High-cheekbones</td><td>1%</td><td>66.10 (1.14)</td><td>68.18 (2.01)</td><td>62.96 (10.45)</td><td>69.83 (0.84)</td><td>τ = 1, N = 1000, k = 100</td></tr><tr><td>2%</td><td>70.87 (0.91)</td><td>72.85 (0.28)</td><td>74.98 (0.20)</td><td>73.17 (0.84)</td><td>τ = 1, N = 1000, k = 100</td></tr><tr><td>5%</td><td>75.89 (1.26)</td><td>78.13 (0.36)</td><td>73.83 (11.30)</td><td>78.45 (0.53)</td><td>τ = 1, N = 1000, k = 100</td></tr><tr><td>10%</td><td>80.15 (1.02)</td><td>81.51 (0.57)</td><td>74.07 (12.13)</td><td>82.67 (0.49)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td>20%</td><td>84.26 (0.74)</td><td>85.70 (0.33)</td><td>72.44 (17.48)</td><td>86.82 (0.30)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td rowspan="5">Heavy-makeup</td><td>1%</td><td>65.03 (0.92)</td><td>66.33 (1.41)</td><td>68.55 (0.83)</td><td>66.75 (0.31)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>2%</td><td>68.82 (0.61)</td><td>71.13 (0.80)</td><td>73.43 (0.13)</td><td>71.57 (0.80)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>5%</td><td>75.48 (1.44)</td><td>77.78 (0.40)</td><td>79.54 (0.09)</td><td>78.32 (0.33)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td>10%</td><td>81.53 (1.10)</td><td>82.85 (0.75)</td><td>85.00 (0.12)</td><td>84.39 (0.47)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td>20%</td><td>88.22 (0.40)</td><td>88.68 (0.36)</td><td>89.93 (0.11)</td><td>89.81 (0.19)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td rowspan="5">Wearing-lipstick</td><td>1%</td><td>70.24 (1.13)</td><td>71.77 (0.70)</td><td>74.82 (0.33)</td><td>72.29 (0.77)</td><td> $\tau = 0 . 0 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td>2%</td><td>75.42 (0.68)</td><td>77.21 (0.39)</td><td>79.28 (0.22)</td><td>78.44 (0.28)</td><td>τ = 1, N = 1000, k = 100</td></tr><tr><td>5%</td><td>82.19 (0.37)</td><td>83.42 (0.97)</td><td>84.68 (0.19)</td><td>84.56 (0.28)</td><td>τ = 0.01, N = 100, k = 100</td></tr><tr><td>10%</td><td>87.70 (0.89)</td><td>88.44 (0.25)</td><td>89.35 (0.18)</td><td>89.73 (0.27)</td><td>τ = 0.01, N = 100, k = 100</td></tr><tr><td>20%</td><td>91.88 (0.44)</td><td>93.00 (0.20)</td><td>93.19 (0.12)</td><td>93.93 (0.15)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td rowspan="5">Smiling</td><td>1%</td><td>75.39 (0.51)</td><td>75.87 (0.63)</td><td>78.03 (0.42)</td><td>75.59 (0.76)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>2%</td><td>78.44 (0.41)</td><td>79.85 (0.52)</td><td>81.51 (0.20)</td><td>79.80 (0.55)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>5%</td><td>83.48 (0.68)</td><td>84.50 (0.54)</td><td>64.97 (17.24)</td><td>84.81 (0.41)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>10%</td><td>86.76 (0.84)</td><td>88.06 (0.22)</td><td>73.79 (18.63)</td><td>88.80 (0.30)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td>20%</td><td>90.88 (0.52)</td><td>91.46 (0.11)</td><td>76.61 (18.69)</td><td>92.08 (0.09)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td rowspan="5">Black-hair</td><td>1%</td><td>60.53 (0.86)</td><td>57.73 (1.11)</td><td>61.44 (0.44)</td><td>61.24 (0.26)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>2%</td><td>64.48 (0.45)</td><td>63.93 (1.10)</td><td>66.53 (0.44)</td><td>66.07 (0.61)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>5%</td><td>70.87 (1.01)</td><td>71.85 (0.25)</td><td>73.19 (0.29)</td><td>73.79 (0.45)</td><td> $\tau = 0 . 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>10%</td><td>78.04 (0.71)</td><td>78.49 (0.56)</td><td>79.88 (0.11)</td><td>80.19 (0.07)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td>20%</td><td>84.33 (0.54)</td><td>85.45 (0.37)</td><td>86.00 (0.09)</td><td>86.09 (0.30)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td rowspan="5">Blond-hair</td><td>1%</td><td>71.36 (0.62)</td><td>70.38 (0.89)</td><td>73.11 (0.46)</td><td>72.11 (0.37)</td><td> $\tau = 0 . 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>2%</td><td>76.50 (0.91)</td><td>76.25 (0.66)</td><td>79.01 (0.16)</td><td>78.06 (0.54)</td><td> $\tau = 0 . 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>5%</td><td>84.74 (0.69)</td><td>84.21 (0.37)</td><td>86.18 (0.13)</td><td>85.76 (0.25)</td><td> $\tau = 0 . 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>10%</td><td>89.39 (0.59)</td><td>89.75 (0.73)</td><td>90.63 (0.15)</td><td>90.49 (0.21)</td><td> $\tau = 0 . 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>20%</td><td>93.30 (0.33)</td><td>93.56 (0.38)</td><td>94.24 (0.10)</td><td>94.27 (0.14)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td rowspan="5">Brown-hair</td><td>1%</td><td>55.40 (0.54)</td><td>52.65 (0.56)</td><td>56.09 (0.28)</td><td>56.61 (0.41)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>2%</td><td>58.82 (0.38)</td><td>54.62 (1.34)</td><td>59.68 (0.21)</td><td>60.10 (0.40)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>5%</td><td>64.87 (0.63)</td><td>61.21 (2.25)</td><td>66.71 (0.11)</td><td>67.13 (0.40)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>10%</td><td>69.74 (1.14)</td><td>70.05 (0.34)</td><td>73.23 (0.27)</td><td>73.01 (0.25)</td><td>τ = 1, N = 1000, k = 100</td></tr><tr><td>20%</td><td>77.67 (1.03)</td><td>78.25 (0.51)</td><td>80.09 (0.16)</td><td>80.06 (0.23)</td><td> $\tau = 0 . 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td rowspan="5">Wavy-hair</td><td>1%</td><td>54.03 (0.28)</td><td>50.91 (0.23)</td><td>52.36 (1.31)</td><td>54.33 (0.09)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>2%</td><td>55.85 (0.78)</td><td>52.08 (0.50)</td><td>52.64 (2.14)</td><td>57.02 (0.31)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>5%</td><td>60.16 (0.73)</td><td>54.17 (2.30)</td><td>53.70 (2.98)</td><td>61.30 (0.38)</td><td> $\tau = 1 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>10%</td><td>64.42 (0.37)</td><td>56.70 (2.09)</td><td>57.16 (4.32)</td><td>65.34 (0.48)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr><tr><td>20%</td><td>69.26 (1.03)</td><td>68.56 (0.49)</td><td>66.47 (5.60)</td><td>71.48 (0.32)</td><td> $\tau = 0 . 1 , N = 1 0 0 , k = 1 0 0$ </td></tr></table>

Table 8. Maximizing area under the ROC curve for BigEarthNet, in a given FPR range [0, β] for $\beta \in \{ 5 \% , 1 0 \% , 2 0 \% \}$ The mean ROC-AUC are reported over five random trials, along with std. deviations, for cross-entropy, Pairwise-loss, TFCO, ICO. Higher values are better.
<table><tr><td>Labels</td><td>FPR</td><td>CE</td><td>Pairwise-loss</td><td>TFCO</td><td>ICO</td></tr><tr><td rowspan="3">Broad-Leaved Forest (BLF)</td><td>5%</td><td>66.20 (0.59)</td><td>52.07 (0.35)</td><td>66.43 (1.86)</td><td>69.90 (0.53)</td></tr><tr><td>10%</td><td>71.00 (0.80)</td><td>53.78 (1.34)</td><td>71.72 (0.78)</td><td>73.91 (0.66)</td></tr><tr><td>20%</td><td>75.42 (0.67)</td><td>57.94 (0.81)</td><td>76.20 (0.61)</td><td>77.91 (0.77)</td></tr><tr><td rowspan="3">Complex Cultivation patterns (CC)</td><td>5%</td><td>62.19 (0.48)</td><td>52.44 (0.26)</td><td>62.71 (2.19)</td><td>63.61 (0.12)</td></tr><tr><td>10%</td><td>67.46 (0.25)</td><td>54.71 (0.62)</td><td>66.75 (0.82)</td><td>68.35 (0.42)</td></tr><tr><td>20%</td><td>73.81 (0.83)</td><td>59.34 (0.64)</td><td>76.01 (0.77)</td><td>74.88 (0.43)</td></tr><tr><td rowspan="3">Coniferous Forest (CF)</td><td>5%</td><td>71.93 (0.66)</td><td>59.00 (0.56)</td><td>71.49 (3.44)</td><td>74.70 (0.62)</td></tr><tr><td>10%</td><td>78.62 (0.59)</td><td>77.66 (2.22)</td><td>79.98 (1.26)</td><td>80.76 (0.94)</td></tr><tr><td>20%</td><td>84.82 (0.68)</td><td>85.84 (0.31)</td><td>86.62 (0.62)</td><td>86.02 (0.29)</td></tr><tr><td rowspan="3">Discontinuous Urban Fabric (DUF)</td><td>5%</td><td>69.80 (1.45)</td><td>55.33 (0.98)</td><td>71.76 (1.89)</td><td>73.94 (0.39)</td></tr><tr><td>10%</td><td>75.13 (0.86)</td><td>59.15 (2.17)</td><td>77.20 (0.87)</td><td>78.03 (0.32)</td></tr><tr><td>20%</td><td>78.86 (1.19)</td><td>78.89 (0.38)</td><td>81.45 (0.62)</td><td>81.83 (0.57)</td></tr><tr><td rowspan="3">Land principally occupied by Agri- culture, with significant areas of Nat- ural Vegetation (ANV)</td><td>5%</td><td>58.79 (0.49)</td><td>51.23 (0.16)</td><td>58.80 (0.77)</td><td>60.46 (0.17)</td></tr><tr><td>10%</td><td>62.72 (0.46)</td><td>52.65 (0.56)</td><td>63.89 (0.98)</td><td>64.38 (0.32)</td></tr><tr><td>20%</td><td>67.77 (0.34)</td><td>54.36 (0.63)</td><td>69.17 (0.52)</td><td>68.97 (0.76)</td></tr><tr><td rowspan="3">Mixed Forest (MF)</td><td>5%</td><td>64.48 (0.76)</td><td>54.59 (0.60)</td><td>65.50 (0.30)</td><td>65.93 (0.60)</td></tr><tr><td>10%</td><td>71.05 (0.47)</td><td>60.41 (0.28)</td><td>72.06 (0.33)</td><td>71.89 (0.48)</td></tr><tr><td>20%</td><td>77.56 (0.69)</td><td>76.44 (0.26)</td><td>78.83 (0.14)</td><td>79.20 (0.26)</td></tr><tr><td rowspan="3">Non-Irrigated Arable Land (NIAL</td><td>5%</td><td>70.07 (0.27)</td><td>55.10 (0.28)</td><td>72.67 (0.19)</td><td>71.45 (0.48)</td></tr><tr><td>10%</td><td>75.29 (0.37)</td><td>59.62 (2.37)</td><td>77.30 (0.12)</td><td>76.78 (0.76)</td></tr><tr><td>20%</td><td>79.97 (0.67)</td><td>80.23 (0.17)</td><td>82.05 (0.09)</td><td>81.72 (0.56)</td></tr><tr><td rowspan="3">Pastures</td><td>5%</td><td>72.70 (0.46)</td><td>59.41 (0.85)</td><td>74.16 (0.29)</td><td>73.61 (0.55)</td></tr><tr><td>10%</td><td>75.95 (0.55)</td><td>74.78 (0.29)</td><td>78.04 (0.31)</td><td>77.85 (0.65)</td></tr><tr><td>20%</td><td>80.31 (0.87)</td><td>80.42 (0.66)</td><td>82.38 (0.17)</td><td>82.10 (0.18)</td></tr><tr><td rowspan="3">Transitional Woodland/Shrub (TWS)</td><td>5%</td><td>57.12 (0.32)</td><td>51.30 (0.32)</td><td>58.21 (0.08)</td><td>59.64 (0.27)</td></tr><tr><td>10%</td><td>60.24 (0.21)</td><td>52.45 (0.61)</td><td>61.82 (0.13)</td><td>62.82 (0.61)</td></tr><tr><td>20%</td><td>64.98 (0.92)</td><td>55.47 (0.31)</td><td>67.15 (0.26)</td><td>67.24 (1.10)</td></tr><tr><td rowspan="3">Water Bodies (WB)</td><td>5%</td><td>76.52 (0.59)</td><td>54.29 (1.35)</td><td>77.47 (0.48)</td><td>78.71 (0.33)</td></tr><tr><td>10%</td><td>80.81 (0.69)</td><td>57.23 (0.73)</td><td>81.76 (0.34)</td><td>82.79 (0.35)</td></tr><tr><td>20%</td><td>85.27 (0.39)</td><td>86.11 (0.25)</td><td>85.46 (0.19)</td><td>86.66 (0.31)</td></tr></table>

Table 9. Maximizing area under the ROC curve for BigEarthNet, in a given FPR range $[ 0 , \beta ] \mathrm { f o r } \beta \in \{ 5 \% , 1 0 \% , 2 0 \% \}$ : hyperparameters for ICO selected using the validation set. Surrogate function for both objective and constraint is taken to be softplus; the correction step in Alg. 1 is applied every N minibatch steps using data from next k minibatches. The values of N, k, and the temperature hyperparameter τ for sigmoid are selected on the validation set and are provided in the Table below.
<table><tr><td>Labels</td><td>FPR</td><td>ICO hyperparameters</td></tr><tr><td rowspan="3">Broad-Leaved Forest (BLF)</td><td>5%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 5 0$ </td></tr><tr><td>10%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 5 0$ </td></tr><tr><td>20%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 5 0$ </td></tr><tr><td rowspan="3">Complex Cultivation patterns (CC)</td><td>5%</td><td> $\tau = 1 , N = 1 0 0 , k = 5 0$ </td></tr><tr><td>10%</td><td> $\tau = 0 . 0 0 1 , N = 1 0 0 , k = 1 0$ </td></tr><tr><td>20%</td><td> $\tau = 0 . 0 0 1 , N = 1 0 0 , k = 1 0$ </td></tr><tr><td rowspan="3">Coniferous Forest (CF)</td><td>5%</td><td> $\tau = 0 . 0 0 1 , N = 1 0 0 , k = 1 0$ </td></tr><tr><td>10%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>20%</td><td> $\tau = 0 . 0 0 1 , N = 1 0 0 , k = 5 0$ </td></tr><tr><td rowspan="3">Discontinuous Urban Fabric (DUF) Land principally occupied by Agri-</td><td>5%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>10%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 5 0$ </td></tr><tr><td>20%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td rowspan="3">culture, with significant areas of Nat- ural Vegetation (ANV)</td><td>5%</td><td> $\tau = 1 , N = 1 0 0 , k = 5 0$ </td></tr><tr><td>10% 20%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 5 0$   $\tau = 5 , N = 1 0 0 0 , k = 1 0$ </td></tr><tr><td></td><td></td></tr><tr><td rowspan="3">Mixed Forest (MF)</td><td>5%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 1 0 0$   $\tau = 5 , N = 1 0 0 0 , k = 1 0$ </td></tr><tr><td>10% 20%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 1 0$ </td></tr><tr><td></td><td></td></tr><tr><td rowspan="3">Non-Irrigated Arable Land (NIAL</td><td>5%</td><td> $\tau = 1 , N = 1 0 0 , k = 5 0$ </td></tr><tr><td>10% 20%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 5 0$   $\tau = 5 , N = 1 0 0 0 , k = 5 0$ </td></tr><tr><td></td><td></td></tr><tr><td rowspan="3">Pastures</td><td>5% 10%</td><td> $\tau = 1 , N = 1 0 0 0 , k = 5 0$ </td></tr><tr><td>20%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 5 0$ </td></tr><tr><td></td><td> $\tau = 5 , N = 1 0 0 0 , k = 5 0$ </td></tr><tr><td rowspan="3">Transitional Woodland/Shrub (TWS)</td><td>5%</td><td> $\tau = 5 , N = 1 0 0 , k = 5 0$ </td></tr><tr><td>10%</td><td> $\tau = 5 , N = 1 0 0 , k = 5 0$ </td></tr><tr><td>20%</td><td> $\tau = 5 , N = 1 0 0 , k = 5 0$ </td></tr><tr><td rowspan="3">Water Bodies (WB)</td><td>5% 10%</td><td> $\tau = 5 , N = 1 0 0 0 , k = 5 0$   $\tau = 5 , N = 1 0 0 0 , k = 1 0 0$ </td></tr><tr><td>20%</td><td></td></tr><tr><td></td><td> $\tau = 5 , N = 1 0 0 0 , k = 5 0$ </td></tr></table>