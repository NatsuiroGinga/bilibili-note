---
title: "2011-ElGhaoui-Safe-Feature-Elimination-LASSO"
date: 2026-09-04
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/training-efficiency/2011-ElGhaoui-Safe-Feature-Elimination-LASSO.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Safe Feature Elimination for the LASSO and Sparse Supervised Learning Problems

Laurent El Ghaoui Vivian Viallon Tarek Rabbani Department of EECS University of California Berkeley, CA 94720-1776, USA elghaoui@eecs.berkeley.edu viallon@eecs.berkeley.edu trabbani@berkeley.edu

Editor:

## Abstract

We describe a fast method to eliminate features (variables) in l1-penalized least-square regression (or LASSO) problems. The elimination of features leads to a potentially substantial reduction in running time, especially for large values of the penalty parameter. Our method is not heuristic: it only eliminates features that are guaranteed to be absent after solving the LASSO problem. The feature elimination step is easy to parallelize and can test each feature for elimination independently. Moreover, the computational efort of our method is negligible compared to that of solving the LASSO problem - roughly it is the same as single gradient step. Our method extends the scope of existing LASSO algorithms to treat larger data sets, previously out of their reach. We show how our method can be extended to general l1-penalized convex problems and present preliminary results for the Sparse Support Vector Machine and Logistic Regression problems.

Keywords: Sparse Regression, LASSO, Feature Elimination, SVM, Logistic Regression

## 1. Introduction

“Sparse” classification or regression problems, which involve an ℓ<sub>1</sub> norm regularization has attracted a lot of interest in the statistics (Tibshirani, 1996), signal processing (Chen et al., 2001), and machine learning communities. The $\ell _ { 1 }$ regularization leads to sparse solutions, which is a desirable property to achieve model selection, or data compression. For instance, consider the problem of $\ell _ { 1 }$ -regularized least square regression commonly referred to as the LASSO (Tibshirani, 1996). In this context, we are given a set of m observations $a _ { i } \in \mathbb { R } ^ { n } , i = 1 , \dots { }$ , m and a response vector $y \in \mathbb { R } ^ { m }$ . Denoting by $\bar { X } = ( a _ { 1 } , \ldots , a _ { m } ) ^ { T } \in \mathbb { R } ^ { m \times n }$ the feature matrix of observations, the LASSO problem is given by

$$
\mathcal {P} (\lambda): \phi (\lambda) := \min _ {w} \frac {1}{2} \| X w - y \| _ {2} ^ {2} + \lambda \| w \| _ {1},\tag{1}
$$

where λ is a regularization parameter and $w \in \mathbb { R } ^ { n }$ is the optimization variable. For large enough values of λ, any solution $w ^ { \star } \in \mathbb { R } ^ { n }$ of (1) is typically sparse, i.e. $w ^ { \star }$ has few entries that are non-zero, and therefore identifies the features in X (columns of X) that are useful to predict y.

Several eficient algorithms have been developed for the LASSO problem, including Efron et al. (2004); Kim et al. (2007); Park and Hastie (2007); Donoho and Tsaig (2008); Friedman et al. (2007); Becker et al. (2010); Friedman et al. (2010) and references therein. However, the complexity of these algorithms, when it is known, grows fast with the number of variables. While the LASSO problem i particularly appealing in presence of very high-dimensional problems, the available algorithms can be quite slow in such contexts. In some applications, the feature matrix is so big that it can not even be loaded and LASSO solvers cannot be used at all. Hence it is of paramount interest to be able to eficiently eliminate features in a pre-processing step, in order to reduce dimensionality and solve the optimization problem on a reduced matrix.

Assume that a sparse solution exists to (1) and that we were able to identify e zeros of w<sup>⋆</sup> a priori to solving the LASSO problem. Identifying e zeros in w<sup>⋆</sup> a priori to solving (1) is equivalent to removing e features (columns) from the feature matrix X. If e is large, we can obtain w<sup>⋆</sup> by solving (1) with a “small” feature matrix X.

In this paper we propose a “safe” feature elimination (SAFE) method that can identify zeros in the solution w<sup>⋆</sup> a priori to solving the LASSO problem. Once the zeros are identified we can safely remove the corresponding features and then solve the LASSO problem (1) on the reduced feature matrix.

Feature selection methods are often used to accomplish dimensionality reduction, and are of utmost relevance for data sets of massive dimension, see for example Fan and Lv (2010). These methods, when used as a pre-processing step, have been referred to in the literature as screening procedures (Fan and Lv, 2010, 2008). They typically rely on univariate models to score features, independently of each other, and are usually computationally fast. Classical procedures are based on correlation coeficients, two-sample t-statistics or chi-square statistics (Fan and Lv, 2010); see also Forman (2003) and the references therein for an overview in the specific case of text classification. Most screening methods might remove features that could otherwise have been selected by the regression or classification algorithm. However, some of them were recently shown to enjoy the socalled “sure screening” property (Fan and Lv, 2008): under some technical conditions, no relevant feature is removed, with probability tending to one.

Screening procedures typically ignore the specific classification task to be solved after feature elimination. In this paper, we propose to remove features based on the supervised learning problem considered, that is on both the structure of the loss function and the problem data. While we focus mainly on the LASSO problem here, we provide results for a large class of convex classification or regression problems. The features are eliminated according to a suficient, in general conservative, condition, which we call SAFE (for SAfe Feature Elimination). With SAFE, we never remove features unless they are guaranteed to be absent if one were to solve the full-fledged classification or regression problem.

An interesting fact is that SAFE becomes extremely aggressive at removing features for large values of the penalty parameter λ. The specific application we have in mind involves large data sets of text documents, and sparse matrices based on occurrence, or other score, of words or terms in these documents. We seek extremely sparse optimal coeficient vectors, even if that means operating at values of the penalty parameter that are substantially larger than those dictated by a pure concern for predictive accuracy. The fact that we need to operate at high values of this parameter opens the hope that, at least for the application considered, the number of features eliminated by using our fast test is high enough to allow a dramatic reduction in computing time and memory requirements. Our experimental results indicate that for many of these data sets, we do observe a dramatic reduction in the number of variables, typically by an order of magnitude or more. The method has two main advantages: for medium- to large-sized problem, it enables to reduce the computational time. More importantly, SAFE allows to tackle problems that are too huge to be even loaded in memory, thereby expanding the reach of current algorithms

The paper is organized as follows. In section 2, we derive the SAFE method for the LASSO problem. In section 3, we illustrate the use of SAFE and detail some relevant algorithms. In section 4, we extend the results of SAFE to general convex problems and derive preliminary SAFE results for the Sparse Support Vector Machine and Logistic regression problems. In section 5, we experiment the SAFE for LASSO method on synthetic data and on data derived from text classification sources. Numerical results demonstrate that SAFE provides a substantial reduction in problem size, and, as a result, it enables the LASSO algorithms to run faster and solve huge problems originally out of their reach.

Notation. We use 1 and 0 to denote a vector of ones and zeros, with size inferred from context, respectively. For a scalar $a , \ a _ { + }$ denotes the positive part of a. For a vector $^ { a , }$ this operation is component-wise, so that ${ \bf 1 } ^ { T } a _ { + }$ is the sum of the positive elements in a. We take the convention that a sum over an empty index sets, such as $\textstyle \sum _ { i = 1 } ^ { k } a _ { i }$ with $k \leq 0$ , is zero.

## 2. The SAFE method for the LASSO

The SAFE method crucially relies on duality and optimality conditions. We begin by reviewing the appropriate facts.

## 2.1 Dual problem and optimality conditions for the LASSO

A dual to the LASSO problem (1) (Kim et al., 2007) can be written as

$$
\mathcal {D} (\lambda): \phi (\lambda) := \max _ {\theta} G (\theta): \left| \theta^ {T} x _ {k} \right| \leq \lambda , k = 1, \ldots , n,\tag{2}
$$

with $x _ { k } \in \mathbb { R } ^ { m } , k = 1 , . . . , n$ , the k-th column of X and $\begin{array} { r } { G ( \theta ) = \frac { 1 } { 2 } \left\| y \right\| _ { 2 } ^ { 2 } - \frac { 1 } { 2 } \left\| \theta + y \right\| _ { 2 } ^ { 2 } } \end{array}$ . In this context, we call ${ \mathcal { P } } ( \lambda )$ the primal problem, w the primal variable, and $w ^ { \star }$ a primal optimal point. The dual problem $\mathcal { D } ( \boldsymbol { \lambda } )$ is a convex optimization problem with dual variable $\theta \in \mathbb { R } ^ { m }$ . We call θ dual feasible when it satisfies the constraints in $\mathcal { D } ( \boldsymbol { \lambda } )$ . Figure $1 ( \mathrm { a } )$ shows the geometry of the feasibility set in the dual space. The quantity $G ( \theta )$ gives a lower bound on the optimal value $\phi ( \lambda )$ for any dual feasible point θ, i.e. $G ( \theta ) \leq \phi ( \lambda ) , \ \left| \theta ^ { T } x _ { k } \right| \leq \lambda , k = 1 , \ldots , n$ . For the LASSO problem (1) strong duality holds and the optimal value of $\mathcal { D } ( \dot { \lambda } )$ achieves $\phi ( \lambda )$ at $\theta ^ { \star }$ the solution of (2) or the dual optimal point. Furthermore, the following relation holds at optimum: $\theta ^ { \star } = X w ^ { \star } - y .$

We consider the dual problem $\mathcal { D } ( \boldsymbol { \lambda } )$ because of an important property that helps us derive our SAFE method. Assuming $w ^ { \star }$ is sparse, knowledge of $\theta ^ { \star }$ allows us to identify the zeros in $w ^ { \star }$ by checking the optimality condition (Boyd and Vandenberghe, 2004):

$$
\left| \theta^ {\star T} x _ {k} \right| <   \lambda \Rightarrow (w ^ {\star}) _ {k} = 0.\tag{3}
$$

Figure 1(b) illustrates the geometric interpretation of the inequality test $\left| \theta ^ { \star T } x _ { k } \right| < \lambda$ in (3).

## 2.2 Basic idea

The basic idea behind SAFE is to use the optimality condition (3) with $\theta ^ { \star }$ in the inequality test replaced by a set Θ that contains the dual optimal point, i.e. $\left| \theta ^ { T } x _ { k } \right| < \lambda , \forall \theta \in \Theta$ and $\theta ^ { \star } \in \Theta$ . If the inequality test holds for the whole set Θ, then the k-th entry of $w ^ { \star }$ is zero, $( w ^ { \star } ) _ { k } = 0$

In the following sections, we show how to construct the set Θ using optimality conditions of the dual problem, and derive the corresponding SAFE test.

In our derivation, we assume that we have knowledge of a solution w<sup>⋆</sup> of $\mathcal { P } ( \lambda _ { 0 } )$ for some $\lambda _ { 0 } .$ , and we seek to apply SAFE for ${ \mathcal { P } } ( \lambda )$ with $\lambda \leq \lambda _ { 0 }$ . By default, we can choose $\lambda _ { 0 }$ to be large enough for $w _ { 0 } ^ { \star }$ to be identically zero. To find such a $\lambda _ { 0 }$ , we substitute $w _ { 0 } ^ { \star } = 0$ in (1) to obtain $\begin{array} { r } { \phi ( \lambda _ { 0 } ) = \frac { 1 } { 2 } \left\| y \right\| _ { 2 } ^ { 2 } } \end{array}$ By strong duality, $\mathcal { D } ( \lambda _ { 0 } )$ achieves a value of $\begin{array} { r } { \phi ( \lambda _ { 0 } ) = \frac { 1 } { 2 } \| y \| _ { 2 } ^ { 2 } } \end{array}$ at the unique solution $\theta _ { 0 } ^ { \star } = - y$ . The point $\theta _ { 0 } ^ { \star }$ is a dual feasible point and satisfies the constraints $\lambda _ { 0 } \geq \left| ( - y ) ^ { T } x _ { k } \right| , k = 1 , \ldots , n$ . Note that $\lambda _ { 0 }$ is not uniquely defined but we choose the smallest value above which $w _ { 0 } ^ { \star } = 0$ , that is $\begin{array} { r } { \lambda _ { 0 } = \operatorname* { m a x } _ { 1 \leq j \leq n } | y ^ { T } x _ { j } | = \| X ^ { T } y \| _ { \infty } } \end{array}$

## 2.3 Constructing Θ

We start by finding a set Θ that contains the dual optimal point $\theta ^ { \star }$ of $\mathcal { D } ( \boldsymbol { \lambda } )$ . We express $\Theta$ as the intersection of two sets $\Theta _ { 1 }$ and $\Theta _ { 2 } .$ , where each set corresponds to diferent optimality conditions.

![](images/96d0d9f55ec2577e4730c0952ed12002359857eb7014fa3c991bf9c81081c35c.jpg)  
(a)

![](images/08c375eec02d68e5fd80e5a6761eda332a14280eb7de452133e5fe2b9b91b3e1.jpg)  
(b)  
Figure 1: Geometry of the dual problem $\mathcal { D } ( \boldsymbol { \lambda } )$ . (a) Feasibility set of the dual problem. The grey shaded polytope shows the feasibility set of $\mathcal { D } ( \boldsymbol { \lambda } )$ . The feasibility set is the intersection of n slabs in the dual space corresponding to the n features $x _ { k } , k = 1 , \ldots , n .$ . The level set $G ( \theta ) = \gamma _ { 1 }$ , where $\gamma _ { 1 } = G ( \theta ^ { \star } )$ , corresponds to the optimal value of the dual function and is tangent to the feasibility set at the dual optimal point $\theta ^ { \star }$ . (b) Geometry of the inequality test in (3). The grey shaded region is the slab corresponding to feature $x _ { k }$ , i.e. $\left\{ \theta \mid \left| \theta ^ { T } x _ { k } \right| \leq \lambda \right\}$ . The test $| \theta ^ { \star T } x _ { k } | < \lambda$ is a strict inequality when the point $\theta ^ { \star }$ is in the    	  interior of the slab defined by the feature $x _ { k }$ . Thus if the dual optimal point is inside a slab defined by feature $x _ { k }$ , by optimality condition (3) the k-th entry of the primal optimal solution $w ^ { \star }$ is zero, i.e. $( w ^ { \star } ) _ { k } = 0$

We construct $\Theta _ { 1 }$ using the optimality condition of $\mathcal { D } ( \lambda ) \colon \theta ^ { \star }$ is a dual optimal point if $G ( \theta ^ { \star } ) \geq$ $G ( \theta )$ for all dual feasible points θ. Let $\theta _ { s }$ be a dual feasible point to $\mathcal { D } ( \boldsymbol { \lambda } )$ , and $\gamma : = G ( \theta _ { s } )$ . Obviously $G ( \theta ^ { \star } ) \geq \gamma$ and the set $\Theta _ { 1 } : = \{ \theta ~ | ~ G ( \theta ) \geq \gamma \}$ contains $\theta ^ { \star } , \mathrm { i . e . } \theta ^ { \star } \in \Theta _ { 1 }$

One way to obtain a lower bound γ is by dual scaling. We set $\theta _ { s }$ to be a scaled feasible dual point in terms of $\theta _ { 0 } ^ { \star } , \theta _ { s } : = s \theta _ { 0 } ^ { \star }$ with $s \in \mathbb R$ constrained so that $\theta _ { s }$ is a dual feasible point for $\mathcal { D } ( \boldsymbol { \lambda } )$ that is, $\| X ^ { T } \theta _ { s } \| _ { \infty } \leq \lambda$ or $| s | \le \lambda / \lambda _ { 0 }$ . We then set γ according to the convex optimization problem:

$$
\gamma = \max _ {s} \left\{G (s \theta_ {0} ^ {\star}): | s | \leq \frac {\lambda}{\lambda_ {0}} \right\} = \max _ {s} \left\{\beta_ {0} s - \frac {1}{2} s ^ {2} \alpha_ {0}: | s | \leq \frac {\lambda}{\lambda_ {0}} \right\},
$$

with $\alpha _ { 0 } : = \theta _ { 0 } ^ { \star T } \theta _ { 0 } ^ { \star } > 0 , \beta _ { 0 } : = | y ^ { T } \theta _ { 0 } ^ { \star } |$ . We obtain

$$
\gamma = \frac {\beta_ {0} ^ {2}}{2 \alpha_ {0}} \left(1 - \left(1 - \frac {\alpha_ {0}}{\beta_ {0}} \frac {\lambda}{\lambda_ {0}}\right) _ {+} ^ {2}\right).\tag{4}
$$

We construct $\Theta _ { 2 }$ by applying a first order optimality condition on $\mathcal { D } ( \lambda _ { 0 } ) \colon \theta _ { 0 } ^ { \star }$ is a dual optimal point if $g ^ { T } ( \theta _ { 0 } - \theta _ { 0 } ^ { \star } ) \leq 0$ for every dual point $\theta _ { 0 }$ that is feasible for $\mathcal { D } ( \lambda _ { 0 } )$ , where $g : = \nabla G ( \theta _ { 0 } ^ { \star } ) = \theta _ { 0 } ^ { \star } + y$ For $\lambda \leq \lambda _ { 0 }$ , any dual point θ feasible for $\mathcal { D } ( \boldsymbol { \lambda } )$ is also dual feasible for $\mathcal { D } ( \lambda _ { 0 } ) \left( | \theta ^ { T } x _ { k } | \leq \lambda \leq \lambda _ { 0 } k = \right.$ $1 , \ldots , n )$ . Since $\theta ^ { \star }$ is dual feasible for $\mathcal { D } ( \lambda _ { 0 } )$ , we conclude $\theta ^ { \star } \in \Theta _ { 2 } : = \left\{ \theta \mid g ^ { T } ( \theta - \theta _ { 0 } ^ { \star } ) \leq 0 \right\}$

Figure 2(a) shows the geometry of $\Theta _ { 1 } , \Theta _ { 2 }$ and Θ in the dual space; Figure $2 ( \mathrm { b } )$ shows the geometric interpretation of the inequality test when it is applied to the set Θ.

## 2.4 SAFE-LASSO theorem

Our criterion to identify the k-th zero in $w ^ { \star }$ and thus remove the k-th feature (column) from the feature matrix X in problem ${ \mathcal { P } } ( \lambda )$ becomes

$$
\lambda > \left| \theta^ {T} x _ {k} \right| = \max (\theta^ {T} x _ {k}, - \theta^ {T} x _ {k}): \theta \in \Theta .\tag{5}
$$

An equivalent formulation of condition (5) is

$$
\lambda > \max (P (\gamma , x _ {k}), P (\gamma , - x _ {k})),
$$

where $P ( \gamma , x _ { k } )$ is the optimal value of a convex optimization problem with constraints $\theta \in \Theta .$ <sub>1</sub> and $\theta \in \Theta _ { 2 } ;$

$$
P (\gamma , x _ {k}) := \max _ {\theta} x _ {k} ^ {T} \theta : G (\theta) \geq \gamma , g ^ {T} \left(\theta - \theta_ {0} ^ {\star}\right) \geq 0.\tag{6}
$$

It turns out that the above problem is simple enough to admit a closed-form solution (see Appendix $\mathrm { A } )$ . The resulting test can be summarized as follows.

Theorem (SAFE-LASSO) Consider the $L A S S O$ problem ${ \mathcal { P } } ( \lambda )$ in $( 1 )$ . Let $\lambda _ { 0 } \geq \lambda$ be a value for which an optimal solution $w _ { 0 } ^ { \star } \in \mathbb { R } ^ { n }$ is known. Denote by $x _ { k }$ the k-th feature (column) of the matrix X. Define

$$
\mathcal {E} = \left\{k \mid \lambda > \max (P (\gamma , x _ {k}), P (\gamma , - x _ {k}) \right\},\tag{7}
$$

where

$$
P (\gamma , x _ {k}) = \left\{ \begin{array}{l l} \theta_ {0} ^ {\star T} x _ {k} + \Psi_ {k} \tilde {D} (\gamma) & \| g \| _ {2} ^ {2}   \| x _ {k} \| _ {2} \geq D (\gamma) x _ {k} ^ {T} g, \\ - y ^ {T} x _ {k} + \| x _ {k} \| _ {2}   D (\gamma) & \| g \| _ {2} ^ {2}   \| x _ {k} \| _ {2} \leq D (\gamma) x _ {k} ^ {T} g, \end{array} \right.\tag{8}
$$

with

$$
\theta_ {0} ^ {\star} = X w _ {0} ^ {\star} - y, g := \theta_ {0} ^ {\star} + y, \alpha_ {0} := \theta_ {0} ^ {\star T} \theta_ {0} ^ {\star}, \beta_ {0} := | y ^ {T} \theta_ {0} ^ {\star} |, \gamma := \frac {\beta_ {0} ^ {2}}{2 \alpha_ {0}} \left(1 - \left(1 - \frac {\alpha_ {0}}{\beta_ {0}} \frac {\lambda}{\lambda_ {0}}\right) _ {+} ^ {2}\right),
$$

$$
D (\gamma) = \left(\| y \| _ {2} ^ {2} - 2 \gamma\right) ^ {1 / 2}, \tilde {D} (\gamma) = \left(D (\gamma) ^ {2} - \| g \| _ {2} ^ {2}\right) ^ {1 / 2}, \Psi_ {k} := \left(\| x _ {k} \| _ {2} ^ {2} - \frac {\left(x _ {k} ^ {T} g\right) ^ {2}}{\| g \| _ {2} ^ {2}}\right) ^ {1 / 2}.
$$

![](images/00e024fd5938cdd5b21d310cb9d0e5e3b307abffc8224b6d41cbcfdcb6cc9ff4.jpg)  
(a)

![](images/f7ae172da8122ff546fa062cde998fc10df0e7f2595236728b418bcdd17c850d.jpg)  
(b)  
Figure 2: (a) Sets containing $\theta ^ { \star }$ in the dual space. The set $\Theta _ { 1 } : = \{ \theta ~ | ~ G ( \theta ) \geq \gamma \}$ shown in red corresponds to a ball in the dual space with center $- y .$ . The set $\begin{array} { r } { \Theta _ { 2 } : = \big \{ { \theta \mid g ^ { T } ( \theta - \theta _ { 0 } ^ { \star } ) \leq 0 } \big \} } \end{array}$ with $g : = \nabla G ( \theta _ { 0 } ^ { \star } )$  	shown in yellow corresponds to a half space with supporting hyperplane passing through $\theta _ { 0 } ^ { \star }$ and normal to $\nabla G ( \theta _ { 0 } ^ { \star } )$ . The set $\Theta = \Theta _ { 1 } \cap \Theta _ { 2 }$ shown in orange contains the dual optimal point $\theta ^ { \star }$ . (b) Geometry of the inequality test $\left| \theta ^ { T } x _ { k } \right| < \lambda$ $\forall \theta \in \Theta$ . The grey shaded region is the slab corresponding to feature $x _ { k }$ , i.e. $\left\{ \theta \mid \theta ^ { \dot { T } } x _ { k } \leq \lambda \right\}$ . The test $\vert \theta ^ { T } x _ { k } \vert < \lambda$ , θ $\in \Theta$  	 is a strict inequality when the entire set Θ (shown in orange) is inside the slab defined by the feature $x _ { k }$ . In such case, the dual optimal point $\theta ^ { \star } \in \Theta$ is also inside the slab and by (3) we conclude $( w ^ { \star } ) _ { k } = 0$

Then, for every index $e \in { \mathcal { E } } ,$ the e-th entry of $w ^ { \star }$ is zero, i.e. $( w ^ { \star } ) _ { e } = 0 _ { : }$ , and feature $x _ { e }$ can be $\mathit { s a f e l y }$ eliminated from X a priori to solving the LASSO problem $( 1 )$

When we don’t have access to a solution $w _ { 0 } ^ { \star }$ of $\mathcal { P } ( \lambda _ { 0 } )$ , we can set $w _ { 0 } ^ { \star } = 0$ and $\lambda _ { 0 } = \lambda _ { \mathrm { m a x } } : =$ $\| X ^ { T } y \| _ { \infty }$ . In this case, the inequality test $\lambda > \operatorname* { m a x } ( P ( \gamma , x _ { k } ) , P ( \gamma , - x _ { k } )$ ) in the SAFE-LASSO theorem takes the form $\lambda > \rho _ { k } \lambda _ { \mathrm { m a x } }$ , with

$$
\rho_ {k} = \frac {\| y \| _ {2} \| x _ {k} \| _ {2} + | y ^ {T} x _ {k} |}{\| y \| _ {2} \| x _ {k} \| _ {2} + \lambda_ {\mathrm{max}}}.
$$

In the case of scaled data sets, for which $\| y \| _ { 2 } = 1 { \mathrm { ~ a n d ~ } } \| x _ { k } \| _ { 2 } = 1$ for every $k , \rho _ { k }$ has a convenient geometrical interpretation:

$$
\rho_ {k} = \frac {1 + | \cos \alpha_ {k} |}{1 + \max _ {1 \leq j \leq n} | \cos \alpha_ {j} |},
$$

where $\alpha _ { k }$ is the angle between the k-th feature and the response vector y. Our test then consists in eliminating features based on how closely they are aligned with the response, relative to the most closely aligned feature. For scaled data sets, our test is very similar to standard correlation-based feature selection (Fan and Lv, 2008); in fact, for scaled data sets, the ranking of features it produces is then exactly the same. The big diference here is that our test is not heuristic, as it only eliminates features that are guaranteed to be absent when solving the full-fledged sparse supervised learning problem.

## 2.5 SAFE for LASSO with intercept problem

The SAFE-LASSO theorem can be applied to the LASSO with intercept problem

$$
\mathcal {P} _ {\mathrm{int}} (\lambda): \phi (\lambda) := \min _ {w, \nu} \frac {1}{2} \| X w + \nu - y \| _ {2} ^ {2} + \lambda \| w \| _ {1},
$$

with $\nu \in \mathbb { R } ^ { m }$ the intercept term, by using a simple transformation. Taking the derivative of the objective function of $\mathcal { P } _ { \mathrm { i n t } } ( \lambda )$ w.r.t ν and setting it to zero, we obtain $\nu = \bar { y } - \bar { X } ^ { T } w$ with $\bar { y } =$ $( 1 / m ) { \bf 1 } ^ { T } y , \bar { X } = ( 1 / m ) X { \bf 1 }$ and $\mathbf { 1 } \in \mathbb { R } ^ { m }$ the vector of ones . Using the expression of $\nu , \mathcal { P } _ { \mathrm { i n t } } ( \lambda )$ can be expressed as

$$
\mathcal {P} _ {\mathrm{int}} (\lambda): \phi (\lambda) := \min _ {w} \frac {1}{2} \| X _ {\mathrm{cent}} w - y _ {\mathrm{cent}} \| _ {2} ^ {2} + \lambda \| w \| _ {1},
$$

with $X _ { \mathrm { c e n t } } : = X - { \bar { X } } \mathbf { 1 } ^ { T }$ and $y _ { \mathrm { c e n t } } = y - { \bar { y } } { \bf 1 }$ . Thus the SAFE-LASSO theorem can be applied to ${ \mathcal { P } } _ { \mathrm { i n t } }$ and eliminate features (columns) from $X _ { \mathrm { c e n t } }$

## 2.6 SAFE for elastic net

The elastic net problem

$$
\mathcal {P} _ {\text { elastic }} (\lambda): \phi (\lambda) := \min _ {w} \frac {1}{2} \| X w - y \| _ {2} ^ {2} + \lambda \| w \| _ {1} + \frac {1}{2} \epsilon \| w \| _ {2} ^ {2},
$$

can be expressed in the form of $\mathcal { P } ( \lambda )$ by replacing X and $y$ of (1) with $X _ { \mathrm { e l a s t i c } } = \left( X ^ { T } , \sqrt { \epsilon } I \right) ^ { T }$ and $y _ { \mathrm { e l a s t i c } } = \left( y ^ { T } , \mathbf { 0 } ^ { T } \right) ^ { T }$ . This transformation allows us to apply the SAFE-LASSO theorem on $\mathcal { P } _ { \mathrm { e l a s t i c } } ( \lambda )$   and eliminate features from $X _ { \mathrm { e l a s t i c } }$

## 3. Using SAFE

In this section we illustrate the use of SAFE and detail the relevant algorithms.

## 3.1 SAFE for reducing memory limit problems

SAFE can extend the reach of LASSO solvers to larger size problems than what they could originally handle. In this section, we are interested in solving for $\boldsymbol { w } _ { d } ^ { \star }$ the solution of $\mathcal { P } ( \lambda _ { d } )$ under a memory constraint of loading only M features. We can compute $\boldsymbol { w } _ { d } ^ { \star }$ by solving a sequence of problems, where each problem has a number of features less than our memory limit M. We start by finding an appropriate λ where our SAFE method can eliminate at least $n - M$ features, we then solve a reduced size problem with $L _ { F } \leq M$ features, where $L _ { F } = \left| \mathcal { E } ^ { c } \right|$ is the number of features left after SAFE and $\mathcal { E } ^ { c } = \{ 1 , \ldots , n \} \backslash \mathcal { E }$ is the complement of the set in the SAFE-LASSO theorem. We proceed to the next stage as outlined in algorithm 1.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 SAFE for reducing memory limit problems
given a feature matrix $X \in \mathbb{R}^{m \times n}$, response $y \in \mathbb{R}^m$, penalty parameter $\lambda_d$, memory limit $M$ and LASSO solver: LASSO, i.e. $w^\star = \text{LASSO}(X, y, \lambda)$.
initialize $\lambda_0 = \|X^T y\|_\infty$, $w_0^\star = 0 \in \mathbb{R}^n$,
repeat
    1. Use SAFE to search for a $\lambda$ with $LF \leq M$. Obtain $\lambda$ and $\mathcal{E}$. \% $L_F$ is the number of features left after SAFE and $\mathcal{E}$ is the set defined in the SAFE-LASSO theorem.
    2. if $\lambda &lt; \lambda_d$ then $\lambda = \lambda_d$, apply SAFE to obtain $\mathcal{E}$ end if.
    3. Compute the solution $w^\star$. $w^\star(\mathcal{E}^c) = \text{LASSO}(X(\mathcal{E}^c, :), y, \lambda)$, $w^\star(\mathcal{E}) = 0$; \% $w^\star(\mathcal{E}^c)$ and $X(\mathcal{E}^c, :)$ are the elements and columns of $w^\star$ and $X$ defined by the set $\mathcal{E}^c$, respectively. $\mathcal{E}^c = \{1, \ldots, n\} \setminus \mathcal{E}$ is the complement of the set $\mathcal{E}$.
    4. $\lambda_0 := \lambda$, $w_0^\star = w^\star$.
until $\lambda_0 = \lambda_d$
We use a bisection method to find an appropriate value of $\lambda$ for which SAFE leaves $L_F \in [M - \epsilon_F, M]$ features, where $\epsilon_F$ is a number of feature tolerance. The bisection method on $\lambda$ is outlined in algorithm 2.
</div>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 Bisection method on $\lambda$.

given a feature matrix $X \in \mathbb{R}^{m \times n}$, response $y \in \mathbb{R}^m$, penalty parameter $\lambda_0$ with LASSO solution $w_0^\star$, tolerance $\epsilon_F &gt; 0$ and memory limit $M$.

initialize $l = 0$, and $u = \lambda_0$.

repeat

1. Set $\lambda := (l + u) / 2$.

2. Use the SAFE-LASSO theorem to obtain $\mathcal{E}$.

3. Set $L_F = |\mathcal{E}^c|$.

4. if $L_F &gt; M$ then set $l := \lambda$ else set $u := \lambda$ end if

until $M - L_F \leq \epsilon_F$ and $L_F \leq M$.
</div>

## 3.2 SAFE for LASSO run-time reduction

In some applications like Gawalt et al. (2010), it is of interest to solve a sequence of problems $\mathcal { P } ( \lambda _ { 1 } ) , . . . \mathcal { P } ( \lambda _ { s } )$ for decreasing values of the penalty parameters, i.e. $\lambda _ { 1 } \geq . . . \geq \lambda _ { s }$ . The computational complexities of LASSO solvers depend on the number of features and using SAFE might result in run-time improvements. For each problem in the sequence, we can use SAFE to reduce the number of features a priori to using our LASSO solver as shown in algorithm 3.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3 Recursive SAFE for the Lasso

given a feature matrix  $X \in R^{m \times n}$ , response  $y \in R^{m}$ , a sequence of penalty parameters  $\lambda_{s} \leq \ldots \leq \lambda_{1} \leq \|X^{T}y\|_{\infty}$ , and LASSO solver: LASSO.

initialize  $\lambda_{0} = \|X^{T}y\|_{\infty}$ ,  $w_{0}^{\star} = 0 \in R^{n}$ .

for i = 1 until i = s do

1. Set  $\lambda_{0} = \lambda_{i-1}$ , and  $\lambda = \lambda_{i}$ .

2. Use the SAFE-LASSO theorem to obtain E.

3. Compute the solution  $w^{\star}$ .  $w^{\star}(\mathcal{E}^{c}) = \text{LASSO}(X(\mathcal{E}^{c}, :), y, \lambda)$ ,  $w^{\star}(\mathcal{E}) = 0$ . %  $w^{\star}(\mathcal{E}^{c})$  and  $X(\mathcal{E}^{c}, :)$  are the elements and columns of  $w^{\star}$  and X defined by the set  $E^{c}$ , respectively.  $E^{c} = \{1, \ldots, n\} \setminus E$  is the complement of the set E.

4. Set  $w_{0}^{\star} = w^{*}$ .

end for
</div>

## 4. SAFE applied to general ℓ<sub>1</sub>-regularized convex problems

The SAFE-LASSO result presented in section 2.4 for the LASSO problem (1) can be adapted to a more general class of $l _ { 1 } -$ regularized convex problems. We consider the family of problems

$$
\mathcal {P} (\lambda): \phi (\lambda) := \min _ {w, \nu} \sum_ {i = 1} ^ {m} f (a _ {i} ^ {T} w + b _ {i} v + c _ {i}) + \lambda \| w \| _ {1},\tag{9}
$$

where $f$ is a closed convex function, and non-negative everywhere, $a _ { i } \in \mathbb { R } ^ { n } , i = 1 , \dots , m , b , c \in \mathbb { R } ^ { m }$ are given. The LASSO problem (1) is a special case of (9) with $f ( \zeta ) = ( 1 / 2 ) \zeta ^ { 2 } , a _ { i } \in \mathbb { R } ^ { n } , i = 1 , \dots , m$ the observations, $c = - y$ is the (negative) response vector, and $b = 0 ,$ . Hereafter, we refer to the LASSO problem as $\mathcal { P } _ { \mathrm { L A S S O } } ( \lambda )$ and to the general class of l<sub>1</sub>-regularized problems as ${ \mathcal { P } } ( \lambda )$ . In this section, we outline the steps necessary to derive a SAFE method for the general problem ${ \mathcal { P } } ( \lambda )$ We show some preliminary results for deriving SAFE methods when $f ( \zeta )$ is the hing loss function, $f _ { \mathrm { h i } } ( \zeta ) = ( 1 - \zeta ) _ { + }$ , and the logistic loss function $f _ { \log } ( \xi ) = \log ( 1 + e ^ { - \xi } )$

## 4.1 Dual Problem

The first step is to devise the dual of problem (9), which is

$$
\mathcal {D} (\lambda): \phi (\lambda) = \max _ {\theta} G (\theta): \theta^ {T} b = 0, | \theta^ {T} x _ {k} | \leq \lambda , k = 1, \dots , n,\tag{10}
$$

where

$$
G (\theta) := c ^ {T} \theta - \sum_ {i = 1} ^ {m} f ^ {*} (\theta_ {i})\tag{11}
$$

with $f ^ { * } ( \vartheta ) = \mathrm { m a x } _ { \xi } \ \xi \vartheta - f ( \xi )$ the conjugate of the loss function $f ( \zeta )$ , and $x _ { k }$ the k-th column or feature of the feature matrix $\boldsymbol { X } = \left( a _ { 1 } , \ldots , a _ { m } \right) ^ { T } \in \mathbb { R } ^ { m \times n }$ . G(θ) is the dual function, which is, by construction, concave. We assume that strong duality holds and primal and dual optimal points are attained. Due to the optimality conditions for the problem (see Boyd and Vandenberghe (2004)), constraints for which $| \theta ^ { T } x _ { k } | < \lambda$ at optimum correspond to a zero element in the primal variable: $( w ^ { \star } ) _ { k } = 0 , \mathrm { i . e }$

$$
\left| \theta^ {\star T} x _ {k} \right| <   \lambda \Rightarrow (w ^ {\star}) _ {k} = 0.\tag{12}
$$

## 4.2 Optimality set Θ

For simplicity, we consider only the set $\Theta : = \{ \theta | G ( \theta ) \geq \gamma \}$ which contains $\theta ^ { \star }$ the dual optimal point of $\mathcal { D } ( \boldsymbol { \lambda } )$ . One way to get a lower bound $\gamma$ is to find a dual point $\theta _ { s }$ that is feasible for the dual problem $\mathcal { D } ( \boldsymbol { \lambda } )$ , and then set $\gamma = G ( \theta _ { s } )$

To obtain a dual feasible point, we can solve the problem for a higher value $\lambda _ { 0 } ~ \geq ~ \lambda$ of the penalty parameter. (In the specific case examined below, we will see how to set $\lambda _ { 0 }$ so that the vector $w _ { 0 } ^ { \star } = 0$ at optimum.) This provides a dual point $\theta _ { 0 } ^ { \star }$ that is feasible for $\mathcal { D } ( \lambda _ { 0 } )$ , which satisfies $\lambda _ { 0 } = \| X { \bar { \theta } } _ { 0 } \| _ { \infty }$ . In turn, $\theta _ { 0 } ^ { \star }$ can be scaled so as to become feasible for $\mathcal { D } ( \boldsymbol { \lambda } )$ . Precisely, we set $\theta _ { s } = s \theta _ { 0 }$ with $\| X \theta _ { s } \| _ { \infty } \leq \lambda$ equivalent to $| s | \le \lambda / \lambda _ { 0 }$ . In order to find the best possible scaling factor s, we solve the one-dimensional, convex problem

$$
\gamma (\lambda) := \max _ {s} G (s \theta_ {0}): | s | \leq \frac {\lambda}{\lambda_ {0}}.\tag{13}
$$

Under mild conditions on the loss function $f ,$ the above problem can be solved by bisection in $O ( m )$ time. By construction, $\gamma ( \lambda )$ is a lower bound on $\phi ( \lambda )$ . We can generate an initial point $\theta _ { 0 } ^ { \star }$ by solving $\mathcal { P } ( \lambda _ { 0 } )$ with $w _ { 0 } = 0$ . We get

$$
\min _ {v _ {0}} \sum_ {i = 1} ^ {m} f (b _ {i} v _ {0} + c _ {i}) = \min _ {v _ {0}} \max _ {\theta_ {0}} \theta_ {0} ^ {T} (b v _ {0} + c) - \sum_ {i = 1} ^ {m} f ^ {*} ((\theta_ {0}) _ {i}) = \max _ {\theta_ {0}: b ^ {T} \theta_ {0} = 0} G (\theta_ {0}).
$$

Solving the one-dimensional problem above can be often done in closed-form, or by bisection, in $O ( m )$ . Choosing $\theta _ { 0 } ^ { \star }$ to be any optimal for the corresponding dual problem (the one on the righthand side) generates a point that is dual feasible for it, that is, $G ( \theta _ { 0 } ^ { \star } )$ is finite, and $b ^ { T } \theta _ { 0 } = 0$

The point $\theta _ { 0 } ^ { \star }$ satisfies all the constraints of problem $\mathcal { D } ( \boldsymbol { \lambda } )$ , except perhaps for the constraint $\| X \theta \| _ { \infty } \leq \lambda$ , i.e. $\| X \theta _ { 0 } ^ { \star } \| _ { \infty } > \lambda$ . Hence, if $\lambda \ge \lambda _ { 0 } : = \| X \theta _ { 0 } ^ { \star } \| _ { \infty }$ , then $\theta _ { 0 } ^ { \star }$ is dual optimal for $\mathcal { D } ( \boldsymbol { \lambda } )$ and by the optimality condition (12) we have $w ^ { \star } = 0$ . Note that, since $\theta _ { 0 } ^ { \star }$ may not be uniquely defined, $\lambda _ { 0 }$ may not necessarily be the smallest value for which $w ^ { \star } = 0$ is optimal for the primal problem.

## 4.3 SAFE method

Assume that a lower bound $\gamma$ on the optimal value of the learning problem $\phi ( \lambda )$ is known: $\gamma \leq \phi ( \lambda )$ ). (Without loss of generality, we can assume that $\begin{array} { r } { 0 \leq \gamma \leq \sum _ { i = 1 } ^ { m } f ( c _ { i } ) ) } \end{array}$ . The test

$$
\lambda > \max (P (\gamma , x _ {k}), P (\gamma , - x _ {k})),
$$

allows to eliminate the k-th feature from the feature matrix $X$ , where $P ( \gamma , x _ { k } )$ is the optimal value of a convex optimization problem with two constraints:

$$
P (\gamma , x _ {k}) := \max _ {\theta} \theta^ {T} x _ {k}: G (\theta) \geq \gamma , \theta^ {T} b = 0.\tag{14}
$$

Since $P ( \gamma , x _ { k } )$ decreases when $\gamma$ increases, the closer $\phi ( \lambda )$ is to its lower bound $\gamma ,$ the more aggressive (accurate) our test is.

By construction, the dual function $G$ is decomposable as a sum of functions of one variable only. This particular structure allows to solve problem (14) very eficiently, using for example interiorpoint methods, for a large class of loss functions $f .$ Alternatively, we can express the problem in dual form as a convex optimization problem with two scalar variables:

$$
P (\gamma , x _ {k}) = \min _ {\mu > 0, \nu} - \gamma \mu + \mu \sum_ {i = 1} ^ {m} f \left(\frac {(x _ {k}) _ {i} + \mu c _ {i} + \nu b _ {i}}{\mu}\right).\tag{15}
$$

Note that the expression above involves the perspective of the function $f ,$ which is convex (see Boyd and Vandenberghe (2004)). For many loss functions $f ,$ the above problem can be eficiently solved using a variety of methods for convex optimization, in (close to) $O ( m )$ time. We can also set the variable $\nu = 0$ , leading to a simple bisection problem over $\mu .$ This amounts to ignore the constraint $\theta ^ { T } b = 0$ in the definition of $P ( \gamma , x )$ , resulting in a more conservative test. More generally, any pair $( \mu , \nu )$ with $\mu > 0$ generates an upper bound on $P ( \gamma , x )$ , which in turn corresponds to a valid, perhaps conservative, test.

## 4.4 SAFE for Sparse Support Vector Machine

We turn to the sparse support vector machine classification problem:

$$
\mathcal {P} _ {\mathrm{hi}} (\lambda): \phi (\lambda) := \min _ {w, v} \sum_ {i = 1} ^ {m} (1 - y _ {i} (z _ {i} ^ {T} w + v)) _ {+} + \lambda \| w \| _ {1},\tag{16}
$$

where $z _ { i } \in \mathbb { R } ^ { n } , i = 1 , . . . , m$ are the data points, and $y \in \{ - 1 , 1 \} ^ { m }$ is the label vector. The above is a special case of the generic problem (9), where $f ( \zeta ) : = ( 1 - \xi ) _ { + }$ is the hinge loss, $b = y , c = 0 ,$ , and the feature matrix $X$ is given by $X = [ y _ { 1 } z _ { 1 } , \dots , y _ { m } z _ { m } ] ^ { T }$ , so that $x _ { k } = [ y _ { 1 } z _ { 1 } ( k ) , \dots , y _ { m } z _ { m } ( k ) ] ^ { T }$

We denote by $\mathcal { T } _ { + } , \mathcal { T } _ { - }$ the set of indicies corresponding to the positive and negative classes, respectively, and denote by $m _ { \pm } = | \pmb { \mathcal { T } } _ { \pm } |$ the associated cardinalities. We define $\underline { { m } } : = \operatorname* { m i n } ( m _ { + } , m _ { - } )$ Finally, for a generic data vector x, we set $x ^ { \pm } = ( x _ { i } ) _ { i \in \mathbb { Z } _ { \pm } } \in \mathbb { R } ^ { m \pm } , \ k \ = \ 1 , \ldots , n .$ , the vectors corresponding to each one of the classes.

The dual problem takes the form

$$
\mathcal {D} _ {h i} (\lambda): \phi (\lambda) := \max _ {\theta} G _ {\mathrm{hi}} (\theta): - \mathbf {1} \leq \theta \leq 0, \theta^ {T} y = 0, | \theta^ {T} x _ {k} | \leq \lambda , k = 1, \dots , n.\tag{17}
$$

with $G _ { \mathrm { h i } } ( \theta ) = \mathbf { 1 } ^ { T } \theta$

## 4.4.1 Test, γ given

Let $\gamma$ be a lower bound on $\phi ( \lambda )$ . The optimal value obtained upon setting $w = 0$ in (16) is given by

$$
\min _ {v} \sum_ {i = 1} ^ {m} (1 - y _ {i} v) _ {+} = 2 \min (m _ {+}, m _ {-}) := \gamma_ {\max}.\tag{18}
$$

Hence, without loss of generality, we may assume $0 \leq \gamma \leq \gamma _ { \mathrm { m a x } }$

The feature elimination test hinges on the quantity

$$
\begin{array}{r c l} P _ {\mathrm{hi}} (\gamma , x) & = & \max _ {\theta} \theta^ {T} x: \mathbf {1} ^ {T} \theta \geq \gamma , \theta^ {T} y = 0, - \mathbf {1} \leq \theta \leq 0 \\ & = & \min _ {\mu > 0, \nu} - \gamma \mu + \mu \sum_ {i = 1} ^ {m} f _ {\mathrm{hi}} \left(\frac {x _ {i} - \nu y _ {i}}{\mu}\right) \\ & = & \min _ {\mu > 0, \nu} - \gamma \mu + \sum_ {i = 1} ^ {m} (\mu + \nu y _ {i} - x _ {i}) _ {+}. \end{array}\tag{19}
$$

In appendix C.1, we show that for any $x ,$ the quantity $P ( \gamma , x )$ is finite if and only if $0 \leq \gamma \leq \gamma$ <sub>max</sub>, and can be computed in $O ( m \log m )$ , or less with sparse data, via a closed-form expression. That expression is simpler to state for $P _ { \mathrm { h i } } ( \gamma , - x )$ :

$$
\begin{array}{r c l} P _ {\mathrm{hi}} (\gamma , - x) & = & \sum_ {j = 1} ^ {\lfloor \gamma / 2 \rfloor} \bar {x} _ {j} - (\frac {\gamma}{2} - \lfloor \frac {\gamma}{2} \rfloor) (\bar {x} _ {\lfloor \gamma / 2 \rfloor + 1}) _ {+} + \sum_ {j = \lfloor \gamma / 2 \rfloor + 1} ^ {\underline {{m}}} (\bar {x} _ {j}) _ {+}, 0 \leq \gamma \leq \gamma_ {\max} = 2 \underline {{m}}, \\ & & \bar {x} _ {j} := x _ {[ j ]} ^ {+} + x _ {[ j ]} ^ {-}, j = 1, \ldots , \underline {{m}}, \end{array}
$$

with $x _ { [ j ] }$ the $j \mathrm { - t h }$ largest element in a vector x, and with the convention that a sum over an empty index set is zero. Note that in particular, since $\gamma _ { \mathrm { m a x } } = 2 \underline { { m } } \mathrm { : }$

$$
P _ {\mathrm{hi}} (\gamma_ {\max}, - x) = \sum_ {i = 1} ^ {\underline {{m}}} (x _ {[ j ]} ^ {+} + x _ {[ j ]} ^ {-}).
$$

## 4.4.2 SAFE-SVM theorem

Following the construction proposed in section 4.2 for the generic case, we select $\gamma = G _ { \mathrm { h i } } ( \theta )$ , where the point θ is feasible for (17), and can found by the scaling method outlined in section 4.2, as follows. The method starts with the assumption that there is a value $\lambda _ { 0 } \geq \lambda$ for which we know the optimal value $\gamma _ { 0 }$ of $\mathcal { P } _ { \mathrm { h i } } ( \lambda _ { 0 } )$

Specific choices for $\lambda _ { 0 } , \gamma _ { 0 }$ . Let us first detail how we can find such values $\lambda _ { 0 } , \gamma _ { 0 }$

We can set a value $\lambda _ { 0 }$ such that $\lambda > \lambda _ { 0 }$ ensures that $w = 0$ is optimal for the primal problem (16). The value that results in the least conservative test is $\lambda _ { 0 } = \lambda _ { \operatorname* { m a x } }$ , where $\lambda _ { \mathrm { m a x } }$ is the smallest value of λ above which $w = 0$ is optimal:

$$
\lambda_ {\max} := \min _ {\theta} \| X \theta \| _ {\infty}: - \theta^ {T} \mathbf {1} \geq \gamma_ {\max}, \theta^ {T} y = 0, - \mathbf {1} \leq \theta \leq 0.\tag{20}
$$

Since $\lambda _ { \mathrm { m a x } }$ may be relatively expensive to compute, we can settle for an upper bound $\overline { { \lambda } } _ { \mathrm { m a x } }$ on $\lambda _ { \operatorname* { m a x } } .$ One choice for $\overline { { \lambda } } _ { \mathrm { m a x } }$ is based on the test derived in the previous section: we ask that it passes for all the features when $\lambda = \overline { { \lambda } } _ { \mathrm { m a x } }$ and $\gamma = \gamma _ { \mathrm { m a x } }$ . That is, we set

$$
\begin{array}{r c l} \overline {{\lambda}} _ {\max} & = & \max _ {1 \leq k \leq n} \max \left(P _ {\mathrm{hi}} (\gamma_ {\max}, x _ {k}), P _ {\mathrm{hi}} (\gamma_ {\max}, - x _ {k})\right) \\ & = & \max _ {1 \leq k \leq n} \max \left(\sum_ {i = 1} ^ {m} (x _ {k} ^ {+}) _ {[ j ]} + (x _ {k} ^ {-}) _ {[ j ]}, \sum_ {i = 1} ^ {m} (- x _ {k} ^ {+}) _ {[ j ]} + (- x _ {k} ^ {-}) _ {[ j ]}\right). \end{array}\tag{21}
$$

By construction, we have $\overline { { \lambda } } _ { \mathrm { m a x } } \geq \lambda _ { \mathrm { m a x } } .$ in fact:

$$
\begin{array}{r c l} \overline {{\lambda}} _ {\max} & = & \max _ {1 \leq k \leq n} \max _ {\theta} | x _ {k} ^ {T} \theta |: - \theta^ {T} \mathbf {1} \geq \gamma_ {\max}, \theta^ {T} y = 0, - \mathbf {1} \leq \theta \leq 0 \\ & = & \max _ {\theta} \| X \theta \| _ {\infty}: - \theta^ {T} \mathbf {1} \geq \gamma_ {\max}, \theta^ {T} y = 0, - \mathbf {1} \leq \theta \leq 0, \end{array}
$$

The two values $\lambda _ { \operatorname* { m a x } } , \overline { { \lambda } } _ { \operatorname* { m a x } }$ coincide if the feasible set is a singleton, that is, when $m _ { + } = m _ { - }$ . On the whole interval $\lambda _ { 0 } \in [ \lambda _ { \operatorname* { m a x } } , \overline { { \lambda } } _ { \operatorname* { m a x } } ]$ , the optimal value of problem $\mathcal { P } _ { \mathrm { h i } } ( \lambda _ { 0 } )$ is $\gamma _ { \mathrm { m a x } } .$

Dual scaling. The remainder of our analysis applies to any value $\lambda _ { 0 }$ for which we know the optimal value $\gamma _ { 0 } \in [ 0 , \gamma _ { \operatorname* { m a x } } ]$ of the problem $\mathcal { P } _ { \mathrm { h i } } ( \lambda _ { 0 } )$

Let $\theta _ { 0 }$ be a corresponding optimal dual point (as seen shortly, the value of $\theta _ { 0 }$ is irrelevant, as we will only need to know $\gamma _ { 0 } = \mathbf { 1 } ^ { T } \theta _ { 0 } )$ . We now scale the point $\theta _ { 0 }$ to make it feasible for $\mathcal { P } _ { \mathrm { h i } } ( \lambda )$ ), where $\lambda \left( 0 \leq \lambda \leq \lambda _ { 0 } \right)$ is given. The scaled dual point is obtained as $\theta = s \theta _ { 0 }$ , with s solution to (13). We obtain the optimal scaling $s = \lambda / \lambda _ { 0 }$ , and since $\gamma _ { 0 } = - \mathbf { 1 } ^ { T } \theta _ { 0 }$ , the corresponding bound is

$$
\gamma (\lambda) = \mathbf {1} ^ {T} (s \theta_ {0}) = s \gamma_ {0} = \gamma_ {0} \frac {\lambda}{\lambda_ {0}}.
$$

Our test takes the form

$$
\lambda > \max \left(P _ {\mathrm{hi}} (\gamma (\lambda), x), P _ {\mathrm{hi}} (\gamma (\lambda), - x)\right).
$$

Let us look at the condition $\lambda > P _ { \mathrm { h i } } ( \gamma ( \lambda ) , - x )$

$$
\exists \mu \geq 0, \nu : \lambda > - \gamma (\lambda) \mu + \sum_ {i = 1} ^ {m} (\mu + \nu y _ {i} + x _ {i}) _ {+},
$$

which is equivalent to:

$$
\lambda > \min _ {\mu \geq 0, \nu} \frac {\sum_ {i = 1} ^ {m} (\mu + \nu y _ {i} + x _ {i}) _ {+}}{1 + (\gamma_ {0} / \lambda_ {0}) \mu}.
$$

The problem of minimizing the above objective function over variable ν has a closed-form solution. In appendix C.2, we show that for any vectors $x ^ { \pm } \in \mathbb { R } ^ { m \pm }$ , we have

$$
\Phi (x ^ {+}, x ^ {-}) := \min _ {\nu} \sum_ {i = 1} ^ {m _ {+}} (x _ {i} ^ {+} + \nu) _ {+} + \sum_ {i = 1} ^ {m _ {-}} (x _ {i} ^ {-} - \nu) _ {+} = \sum_ {i = 1} ^ {\underline {{m}}} (x _ {[ i ]} ^ {+} + x _ {[ i ]} ^ {-}) _ {+},
$$

with $x _ { [ j ] }$ the $j \mathrm { - t h }$ largest element in a vector x. Thus, the test becomes

$$
\lambda > \min _ {\mu \geq 0} \frac {\sum_ {i = 1} ^ {m} (2 \mu + x _ {[ i ]} ^ {+} + x _ {[ i ]} ^ {-}) _ {+}}{1 + (\gamma_ {0} / \lambda_ {0}) \mu}.
$$

Setting $\kappa = \lambda _ { 0 } / ( \lambda _ { 0 } + \gamma _ { 0 } \mu )$ , we obtain the following formulation for our test:

$$
\lambda > \min _ {0 \leq \kappa \leq 1} \sum_ {i = 1} ^ {\underline {{m}}} ((1 - \kappa) \frac {2 \lambda_ {0}}{\gamma_ {0}} + \kappa (x _ {[ i ]} ^ {+} + x _ {[ i ]} ^ {-})) _ {+} = \frac {2 \lambda_ {0}}{\gamma_ {0}} G (\frac {\gamma_ {0}}{2 \lambda_ {0}} \overline {{x}}),\tag{22}
$$

where $\overline { { x } } _ { i } : = x _ { [ i ] } ^ { + } + x _ { [ i ] } ^ { - } , i = 1 , \ldots , \underline { { m } }$ , and for $z \in \mathbb { R } ^ { m }$ , we define

$$
G (z) := \min _ {0 \leq \kappa \leq 1} \sum_ {i = 1} ^ {m} (1 - \kappa + \kappa z _ {i}) _ {+}.
$$

We show in appendix C.3 that $G ( z )$ admits a closed-form expression, which can be computed in $O ( d \log d )$ , where d is the number of non-zero elements in vector z. By construction, the test removes all the features if we set $\lambda _ { 0 } = \lambda _ { \mathrm { m a x } } , \gamma _ { 0 } = \gamma _ { \mathrm { m a x } } .$ , and when $\lambda > \lambda _ { \mathrm { m a x } } .$

Theorem (SAFE-SVM) Consider the SVM problem $\mathcal { P } _ { \mathrm { h i } } ( \lambda )$ in $( 1 6 )$ . Denote by $x _ { k }$ the k-th row of the matrix $\left[ y _ { 1 } z _ { 1 } , \dots , y _ { m } z _ { m } \right]$ , and let ${ \mathcal { T } } _ { \pm } : = \{ i : y _ { i } = \pm 1 \}$ $m _ { \pm } : = | \pmb { \mathbb { I } } _ { \pm } |$ , m := min $( m _ { + } , m _ { - } )$ 2 and $\gamma _ { \mathrm { m a x } } : = 2 \underline { { m } }$ . Let $\lambda _ { 0 } \geq \lambda$ be a value for which the optimal value $\gamma _ { 0 } \in [ 0 , \gamma _ { \operatorname* { m a x } } ]$ of $\mathcal { P } _ { \mathrm { s q } } ( \lambda _ { 0 } )$ is known. The following condition allows to remove the k-th feature vector $x _ { k }$

$$
\lambda > \frac {2 \lambda_ {0}}{\gamma_ {0}} \max \left(G (\frac {\gamma_ {0}}{2 \lambda_ {0}} \overline {{x}} _ {k}), G (\frac {\gamma_ {0}}{2 \lambda_ {0}} \underline {{x}} _ {k})\right),\tag{23}
$$

where $( \overline { { x } } _ { k } ) _ { i } : = ( x _ { k } ) _ { [ i ] } ^ { + } + ( x _ { k } ) _ { [ i ] } ^ { - } , ( \underline { { x } } _ { k } ) _ { i } : = ( - x _ { k } ) _ { [ i ] } ^ { + } + ( - x _ { k } ) _ { [ i ] } ^ { - } , i = 1 , \ldots , \underline { { m } }$ , and for $z \in \mathbb { R } ^ { m }$

$$
G (z) = \min _ {z} \frac {1}{1 - z} \sum_ {i = 1} ^ {p} (z _ {i} - z) _ {+}: z \in \{- \infty , 0, (z _ {j}) _ {j: z _ {j} <   0} \}
$$

A specific choice $f o r \lambda _ { 0 }$ is $\overline { { \lambda } } _ { \mathrm { m a x } }$ given by $( 2 1 )$ , with corresponding optimal value $\gamma _ { 0 } = \gamma _ { \mathrm { m a x } }$

## 4.5 SAFE for Sparse Logistic Regression

We now consider the sparse logistic regression problem:

$$
\mathcal {P} _ {\mathrm{lo}} (\lambda): \phi (\lambda) := \min _ {w, v} \sum_ {i = 1} ^ {m} \log \left(1 + \exp (- y _ {i} (z _ {i} ^ {T} w + v))\right) + \lambda \| w \| _ {1},\tag{24}
$$

with the same notation as in section 4.4. The dual problem takes the form

$$
\mathcal {D} _ {\mathrm{lo}} (\lambda) : \phi (\lambda) := \max _ {\theta} \sum_ {i = 1} ^ {m} \left(\theta_ {i} \log (- \theta_ {i}) - (1 + \theta_ {i}) ^ {T} \log (1 + \theta_ {i})\right) : \begin{array}{l} - \mathbf {1} \leq \theta \leq 0, \theta^ {T} y = 0, \\ | \theta^ {T} x _ {k} | \leq \lambda , k = 1, \ldots , n. \end{array}\tag{25}
$$

## 4.5.1 Test, γ given

Assume that we know a lower bound on the problem, $\gamma \leq \phi ( \lambda )$ . Since $0 \le \phi ( \lambda ) \le m$ log 2, we may assume that $\gamma \in [ 0 ,$ , m log 2] without loss of generality. We proceed to formulate problem (15). For given $x \in \mathbb { R } ^ { m }$ , and $\gamma \in \mathbb { R }$ , we have

$$
P _ {\log} (\gamma , x) = \min _ {\mu > 0, \nu} - \gamma \mu + \mu \sum_ {i = 1} ^ {m} f _ {\log} \left(\frac {x _ {i} + y _ {i} \nu}{\mu}\right),\tag{26}
$$

which can be computed in $O ( m )$ by two-dimensional search, or by the dual interior-point method described in appendix. (As mentioned before, an alternative, resulting in a more conservative test, is to fix $\nu ,$ for example $\nu = 0 . )$ Our test to eliminate the k-th feature takes the form

$$
\lambda > T _ {\log} (\gamma , x _ {k}) := \max (P _ {\log} (\gamma , x _ {k}), P _ {\log} (\gamma , - x _ {k})).
$$

$\operatorname { I f } \gamma$ is known, the complexity of running this test through all the features is $O ( n m )$ . (In fact, the terms in the objective function that correspond to zero elements of x are of two types, involving $f _ { \mathrm { l o g } } ( \pm \nu / \mu )$ . This means that the efective dimension of problem (26) is the cardinality d of vector $x ,$ which in many applications is much smaller than m.)

## 4.5.2 Obtaining a dual feasible point

We can construct dual feasible points based on scaling one obtained by choice of a primal point (classifier weight) $w _ { 0 }$ . This in turn leads to other possible choices for the bound $\gamma$ .

For $w _ { 0 } \in \mathbb { R } ^ { n }$ given, we solve the one-dimensional, convex problem

$$
v _ {0} := \arg \min _ {b} \sum_ {i = 1} ^ {m} f _ {\log} (y _ {i} x _ {i} ^ {T} w _ {0} + y _ {i} b).
$$

This problem can be solved by bisection in $O ( m )$ time Kim et al. (2007). At optimum, the derivative of the objective is zero, hence $y ^ { T } \theta _ { 0 } = 0$ , where

$$
\theta_ {0} (i) := - \frac {1}{1 + \exp (y _ {i} x _ {i} ^ {T} w _ {0} + y _ {i} v _ {0})}, i = 1, \ldots , m.
$$

Now apply the scaling method seen before, and set $\gamma$ by solving problem (13).

## 4.5.3 A specific example of a dual point

A convenient, specific choice in the above construction is to set $w _ { 0 } = 0$ . Then, the intercept $v _ { 0 }$ can be explicitly computed, as $v _ { 0 } = \log ( m _ { + } / m _ { - } )$ , where $m _ { \pm } = | \{ i : y _ { i } = \pm 1 \}$ are the class cardinalities. The corresponding dual point $\theta _ { 0 }$ is

$$
\theta_ {0} (i) = \left\{ \begin{array}{l l} - \frac {m _ {-}}{m} & (y _ {i} = + 1) \\ - \frac {m _ {+}}{m} & (y _ {i} = - 1), \end{array} \right. i = 1, \ldots , m.\tag{27}
$$

The corresponding value of $\lambda _ { 0 }$ is (see Kim et al. (2007)):

$$
\lambda_ {0} := \| X ^ {T} \theta_ {0} \| _ {\infty} = \max _ {1 \leq k \leq n} | \theta_ {0} ^ {T} x _ {k} |.
$$

We now compute $\gamma ( \lambda )$ by solving problem (13), which expresses as

$$
\gamma (\lambda) = \max _ {| s | \leq \lambda / \lambda_ {0}} G _ {\log} (s \theta_ {0}) = \max _ {| s | \leq \lambda / \lambda_ {0}} - m _ {+} f _ {\log} ^ {*} (- s \frac {m _ {-}}{m}) - m _ {-} f _ {\log} ^ {*} (- s \frac {m _ {+}}{m}).\tag{28}
$$

The above can be solved analytically: it can be shown that $s = \lambda / \lambda _ { 0 }$ is optimal.

## 4.5.4 Solving the bisection problem

In this section, we are given $c \in \mathbb { R } ^ { m } , \gamma \in ( 0 , m \log 2 )$ , and we consider the problem

$$
F ^ {*} := \min _ {\mu > 0} F (\mu) := - \gamma \mu + \mu \sum_ {i = 1} ^ {m} f _ {\log} (c (i) / \mu).\tag{29}
$$

Problem (29) corresponds to the problem (26), with ν set to a fixed value, and $c ( i ) = y _ { i } x _ { i } , i =$ $1 , \ldots , m$ . We assume that $c ( i ) \neq 0$ for every $i ,$ and that $\kappa : =$ m log $2 - \gamma > 0$ . Observe that $\begin{array} { r } { F ^ { * } \le F _ { 0 } : = \operatorname* { l i m } _ { \mu \to 0 ^ { + } } F ( \mu ) = \mathbf { 1 } ^ { T } c _ { + } } \end{array}$ , where $c _ { + }$ is the positive part of vector c.

To solve this problem via bisection, we initialize the interval of confidence to be $[ 0 , \mu _ { u } ]$ , with $\mu _ { u }$ set as follows. Using the inequality log $( 1 + e ^ { - x } ) \geq \log 2 - ( 1 / 2 ) x _ { + }$ , which is valid for every x, we obtain that for every $\mu > 0$ :

$$
F (\mu) \geq - \gamma \mu + \mu \sum_ {i = 1} ^ {m} \left(\log 2 - \frac {(c (i)) _ {+}}{2 \mu}\right) = \kappa \mu - \frac {1}{2} \mathbf {1} ^ {T} c _ {+}.
$$

We can now identify a value $\mu _ { u }$ such that for every $\mu \geq \mu _ { u }$ , we have $F ( \mu ) \geq F _ { 0 } { : }$ : it sufices to ensure $\kappa \mu - ( 1 / 2 ) \mathbf { 1 } ^ { T } c _ { + } \geq F _ { 0 }$ , that is,

$$
\mu \geq \mu_ {u} := \frac {(1 / 2) \mathbf {1} ^ {T} c _ {+} + F _ {0}}{\kappa} = \frac {3}{2} \frac {\mathbf {1} ^ {T} c _ {+}}{m \log 2 - \gamma}.
$$

## 4.5.5 Algorithm summary

An algorithm to check if a given feature can be removed from a sparse logistic regression problem works as follows.

$$
\text { Given: } \lambda , k (1 \leq k \leq n), f _ {\log} (x) = \log (1 + e ^ {- x}), f _ {\log} ^ {*} (\vartheta) = (- \vartheta) \log (- \vartheta) + (\vartheta + 1) \log (\vartheta + 1).
$$

1. Set $\lambda _ { 0 } ~ = ~ \operatorname* { m a x } _ { 1 \leq k \leq n } | \theta _ { 0 } ^ { T } x _ { k } |$ , where $\theta _ { 0 } ( i ) = - m _ { - } / m ( y _ { i } = + 1 ) , \theta _ { 0 } ( i ) = - m _ { + } / m ( y _ { i } = - 1 ) ,$ $i = 1 , \ldots , m$

2. Set

$$
\gamma (\lambda) := - m _ {+} f _ {\log} ^ {*} (- \frac {\lambda}{\lambda_ {0}} \frac {m _ {-}}{m}) - m _ {-} f _ {\log} ^ {*} (- \frac {\lambda}{\lambda_ {0}} \frac {m _ {+}}{m}).
$$

3. Solve via bisection a pair of one-dimensional convex optimization problems

$$
P _ {\epsilon} = \min _ {\mu > 0} - \gamma (\lambda) \mu + \mu \sum_ {i = 1} ^ {m} f _ {\log} \left(\epsilon y _ {i} \left(x _ {k}\right) _ {i} / \mu\right) (\epsilon = \pm 1),
$$

each with initial interval $[ 0 , \mu _ { u } ]$ , with

$$
\mu_ {u} = \frac {3}{2} \frac {\sum_ {i = 1} ^ {m} (\epsilon y _ {i} (x _ {k}) _ {i}) _ {+}}{m \log 2 - \gamma}.
$$

4. If $\lambda > \operatorname* { m a x } ( P _ { + } , P _ { - } )$ , the k-th feature can be safely removed.

## 5. Numerical results

In this section we explore the benefits of SAFE by running numerical experiments<sup>1</sup> with diferent LASSO solvers. We present two kinds of experiments to highlight the two main benefits of SAFE. One kind, in our opinion the most important, shows how memory limitations can be reduced, by allowing to treat larger data sets. The other focuses on measuring computational time reduction when using SAFE a priori to the LASSO solver.

We have used a variety of available algorithms for solving the LASSO problem. We use acronyms to refer to the following methods: IPM stands for the Interior-Point Method for LASSO described in Kim et al. (2007); GLMNET corresponds to the Generalized Linear Model algorithm described in Friedman et al. (2010); TFOCS corresponds to Templates for First-Order Conic Solvers described in Becker et al. (2010); FISTA and Homotopy stand for the Fast Iterative Shrinkage-Thresholding Algorithm and homotopy algorithm, described and implemented in Yang et al. (2010), respectively. Some methods (like IPM, TFOCS) do not return exact zeros in the final solution of the LASSO problem and the issue arises in evaluating the its cardinality. In appendix E, we discuss some issue related to the thresholding of the LASSO solution.

In our experiments, we use data sets derived from text classification sources in Frank and Asuncion (2010). We use medical journal abstracts from PubMed represented in a bag-of-words format, where stop words have been eliminated and capitalization removed. The dimensions of the feature matrix X we use from PubMed is m = 1, 000, 000 abstracts and n = 127, 025 features (words). There is a total of 82, 209, 586 non-zeros in the feature matrix, with an average of about 645 non-zeros per feature (word). We also use data-sets derived from the headlines of The New York Times, (NYT) spanning a period of about 20 years (from 1985 to 2007). The number of headlines in the entire NYT data-set is m = 3, 241, 260 and the number of features (words) is $n = 1 5 9 , 9 4 3$ . There is a total of 14, 083, 676 non-zeros in the feature matrix, with an average of about 90 non-zeros per feature.

In some applications such as Gawalt et al. (2010), the goal is to learn a short list of words that are predictive of the appearance of a given query term (say, “lung” or “china”) in the abstracts of medical journals or NYT news. The LASSO problem can be used to produce a summarization of the query term across the many abstracts or headlines considered. To be manageable by a human reader, the list of predictive terms should be very short (say at most 100 terms) with respect to the size of the dictionary n. To produce such a short list, we solve the LASSO problem (1) with diferent penalty parameters λ, and choose the appropriate penalty λ that would generate enough non-zeros in the LASSO solution (around 100 non-zeros in our case).

## 5.1 SAFE for reducing memory limit problems

We experiment with PubMed data-set which is too large to be loaded into memory, and thus not amenable to current LASSO solvers. As described before, we are interested in solving the LASSO problem for a regularization parameter that would result in about 100 non-zeros in the solution. We implement algorithm 1 with a memory limit M = 1, 000 features, where we have observed that for the PubMed data loading more than 1, 000 features causes memory problems in the machine and platform we are using. The memory limit is approximately two orders of magnitudes less than the original number of features n, i.e. $M \approx 0 . 0 1 n$ . Using algorithm 1, we were able to solved the LASSO problem for $\lambda = 0 . 0 4 \lambda _ { m a x }$ using a sequence of 25 LASSO problem with each problem having a number of features less than $M = 1 , 0 0 0$ . Figure 3 shows the simulation result for the PubMed data-set.

![](images/3055b2e0486784248503189847f423276f99ecff73c9bb921563d3b244d6e40f.jpg)  
Figure 3: A LASSO problem solved for the PubMed data-set and $\lambda = 0 . 0 4 \lambda _ { m a x }$ using a sequence of 25 smaller size problems. Each LASSO problem in the sequence has a number of features $L _ { F }$ that satisfies the memory limit $M = 1 , 0 0 0$ , i.e $L _ { F } \leq 1 , 0 0 0$

![](images/b3375654a4d12772cc9576cbec439cda71ae2532ce465ad8f459b66c7effd2bd.jpg)  
(a)

![](images/e7b427bcc78b9b447acf7e52d0b6182530908e25bd3cb15bec4fffacfe47d055.jpg)  
(b)  
Figure 4: (a) Computational time savings. (b) Lasso solution for the sequence of problem between $0 . 0 3 \lambda _ { m a x }$ and $\lambda _ { m a x }$ . The green line shows the number of features we used to solve the LASSO problem after using algoirthm 3.

## 5.2 SAFE for LASSO run-time reduction

We have used a portion of the NYT data-set corresponding to all headlines in year 1985, the corresponding feature matrix has dimensions $n = 3 8 , 3 7 7$ features and $m = 1 9 2$ , 182 headlines, with an average of 21 non-zero per feature. We solved the plain LASSO problem and the LASSO problem with SAFE as outlined in algoirthm 3 for a sequence of λ logarithmically distributed between $0 . 0 3 \lambda _ { m a x }$ and $\lambda _ { m a x }$ . We have used four LASSO solvers, IPM, TFOCS, FISTA and Homotopy to solve the LASSO problem. Figure 4(a)shows the computational time saving when using SAFE. Figure 4(b) shows the number of features we used to solve the LASSO problem when using SAFE, and the number of non-zeros in the solution. We realize that when using algorithm 3 we solve problem with a number of features at most 10, 000 instead of $n = 3 8$ , 377 features, this reduction has a direct impact on the solving time of the LASSO problem as demonstrated in figure 4(a).

## 5.3 SAFE for LASSO with intercept problem

We return to the LASSO with intercept problem discussed in section 2.5. We generate a feature matrix $\boldsymbol { X } \in \mathbb { R } ^ { m \times n }$ with $m = 5 0 0 , n = 1 0 ^ { 6 }$ . The entries of X has a $\mathcal { N } ( 0 , 1 )$ normal distributed and sparsity density $d = 0 . 1$ . We also generate a vector of coeficients ω $\in \mathbb { R } ^ { n }$ with 50 non-zero entries. The response y is generated by setting $y = X \omega + 0 . 0 1 \eta$ , where η is a vector in $\mathbb { R } ^ { m }$ with $\mathcal { N } ( 0 , 1 )$ distribution. We use GLMNET implemented in R to solve the LASSO problem with intercept. The generated data, X and y can be loaded into R , yet memory problems occur when we try to solve the LASSO problem. We use algorithm 1 with memory limit $M = 1 0 , 0 0 0$ features and $\lambda = 0 . 3 3 \lambda _ { m a x } .$ Figure 5 shows the number of non-zeros in the solution of the 352 sequence of problems used to obtain the solution at $\lambda = 0 . 3 3 \lambda _ { m a x }$

![](images/c7023233317e0b41c0052aa467fb7c727e005367cd1ea45e94886fabc7e5466b.jpg)  
Figure 5: A LASSO problem with intercept solved for randomly generated data-set and $\lambda \ =$ $0 . 3 3 \lambda _ { m a x }$ using a sequence of 352 smaller size problems. Each LASSO problem in the sequence has a number of features $L _ { F }$ that satisfies the memory limit M = 10, 000, i.e $L _ { F } \leq 1 0 0 0$

## Appendix A. Expression of $P ( \gamma , x _ { k } )$ (LASSO)

We can express problem (6) in dual form as a convex optimization problem with two scalar variables, $\mu _ { 1 }$ and $\mu _ { 2 } { : }$

$$
\begin{array}{r c l} P (\gamma , x _ {k}) & = & \min _ {\mu_ {1}, \mu_ {2} \geq 0} \max _ {\theta} x _ {k} ^ {T} \theta + \mu_ {1} (G (\theta) - \gamma) + \mu_ {2} g ^ {T} (\theta - \theta_ {0} ^ {\star}) \\ & = & \min _ {\mu_ {1}, \mu_ {2} \geq 0} - \mu_ {1} \gamma - \mu_ {2} g ^ {T} \theta_ {0} ^ {\star} + \max _ {\theta} x _ {k} ^ {T} \theta + \mu_ {1} G (\theta) + \mu_ {2} g ^ {T} \theta \\ & = & \min _ {\mu_ {1}, \mu_ {2} \geq 0} - \mu_ {1} \gamma - \mu_ {2} g ^ {T} \theta_ {0} ^ {\star} + \mu_ {1} \max _ {\theta} \left(\frac {x _ {k} ^ {T} - \mu_ {1} y ^ {T} + \mu_ {2} g ^ {T}}{\mu_ {1}} \theta - \frac {1}{2} \| \theta \| _ {2} ^ {2}\right) \end{array}
$$

We obtain:

$$
P (\gamma , x _ {k}) = \min _ {\mu_ {1}, \mu_ {2} \geq 0} L (\mu_ {1}, \mu_ {2})\tag{30}
$$

with

$$
L (\mu_ {1}, \mu_ {2}) = - x _ {k} ^ {T} y + \frac {\mu_ {1}}{2} D ^ {2} + \frac {1}{2 \mu_ {1}} \| x _ {k} \| _ {2} ^ {2} + \frac {\mu_ {2} ^ {2}}{2 \mu_ {1}} \| g \| _ {2} ^ {2} + \frac {\mu_ {2}}{\mu_ {1}} x _ {k} ^ {T} g - \mu_ {2} \| g \| _ {2} ^ {2},\tag{31}
$$

and $D : = \left( \Vert y \Vert _ { 2 } ^ { 2 } - 2 \gamma \right) ^ { 1 / 2 }$

To solve (30), we take the derivative of (31) w.r.t $\mu _ { 2 }$ and set it to zero:

$$
\mu_ {2} \left\| g \right\| _ {2} ^ {2} + x _ {k} ^ {T} g - \mu_ {1} \left\| g \right\| _ {2} ^ {2} = 0.
$$

This implies that $\begin{array} { r } { \mu _ { 2 } = \operatorname* { m a x } ( 0 , \mu _ { 1 } - \frac { x _ { k } ^ { T } g } { \| g \| _ { 2 } ^ { 2 } } ) } \end{array}$ . When $\begin{array} { r } { \mu _ { 1 } \leq \frac { x _ { k } ^ { T } g } { \| g \| _ { 2 } ^ { 2 } } } \end{array}$ , we have $\begin{array} { r } { \mu _ { 2 } = 0 , \mu _ { 1 } = \frac { \| x _ { k } \| _ { 2 } } { D } } \end{array}$ and $P ( \gamma , x _ { k } )$ takes the value:

$$
P (\gamma , x _ {k}) = - y ^ {T} x _ {k} + \| x _ {k} \| _ {2} D.
$$

On the other hand, when $\begin{array} { r } { \mu _ { 1 } \geq \frac { x _ { k } ^ { T } g } { \| g \| _ { 2 } ^ { 2 } } } \end{array}$ , we take the derivative of (31) w.r.t $\mu _ { 1 }$ and set it to zero:

$$
\tilde {D} ^ {2} \mu_ {1} ^ {2} = \Psi_ {k} ^ {2},
$$

with $\begin{array} { r } { \Psi _ { k } = \bigg ( \| x _ { k } \| _ { 2 } ^ { 2 } - \frac { \big ( x _ { k } ^ { T } g \big ) ^ { 2 } } { \| g \| _ { 2 } ^ { 2 } } \bigg ) ^ { 1 / 2 } } \end{array}$ and $\tilde { D } = \left( D ^ { 2 } - \left. g \right. _ { 2 } ^ { 2 } \right) ^ { 1 / 2 }$ . Substituting $\mu _ { 1 }$ and $\mu _ { 2 } \mathrm { i n } ( 3 0 ) , P ( \gamma , x _ { k } )$ takes the value:

$$
P (\gamma , x _ {k}) = \theta_ {0} ^ {\star T} x _ {k} + \Psi_ {k} \tilde {D}.
$$

## Appendix B. Expression of $P ( \gamma , x )$ , general case

We show that the quantity $P ( \gamma , x )$ defined in (14) can be expressed in dual form (15). This is a simple consequence of duality:

$$
\begin{array}{l l} P (\gamma , x) & = \max _ {\theta} \theta^ {T} x: G (\theta) \geq \gamma , \theta^ {T} b = 0 \\ & = \max _ {\theta} \min _ {\mu > 0, \nu} \theta^ {T} x + \mu (G (\theta) - \gamma) - \nu \theta^ {T} b \\ & = \min _ {\mu > 0, \nu} \max _ {\theta} \theta^ {T} x + \mu (- y ^ {T} \theta - \sum_ {i = 1} ^ {m} f ^ {*} (\theta (i)) - \gamma) - \nu \theta^ {T} b \\ & = \min _ {\mu > 0, \nu} - \gamma \mu + \max _ {\theta} \theta^ {T} (x - \mu y - \nu z) - \mu \sum_ {i = 1} ^ {m} f ^ {*} (\theta (i)) \\ & = \min _ {\mu > 0, \nu} - \gamma \mu + \mu \left(\max _ {\theta} \frac {1}{\mu} \theta^ {T} (x - \mu y - \nu z) - \sum_ {i = 1} ^ {m} f ^ {*} (\theta (i))\right) \\ & = \min _ {\mu > 0, \nu} - \gamma \mu + \mu \sum_ {i = 1} ^ {m} f \left(\frac {x _ {i} - \mu y (i) - \nu b _ {i}}{\mu}\right). \end{array}
$$

## Appendix C. SAFE test for SVM

In this section, we examine various optimization problems involving polyhedral functions in one or two variables, which arise in section 4.4.1 for the computation of $P _ { \mathrm { h i } } ( \gamma , x )$ as well as in the SAFE-SVM theorem of section 4.4.2.

## C.1 Computing $P _ { \mathrm { h i } } ( \gamma , x )$

We first focus on the specific problem of computing the quantity defined in (19). To simplify notation, we will consider the problem of computing $P _ { \mathrm { h i } } ( \gamma , - x )$ , that is:

$$
P _ {\mathrm{hi}} (\gamma , - x) = \min _ {\mu \geq 0, \nu} - \gamma \mu + \sum_ {i = 1} ^ {m} (\mu + \nu y _ {i} + x _ {i}) _ {+},\tag{32}
$$

where $y \in \{ - 1 , 1 \} ^ { m } , x \in \mathbb { R } ^ { m }$ and γ are given, with $0 \leq \gamma \leq \gamma _ { 0 } : = 2 \operatorname* { m i n } ( m _ { + } , m _ { - } )$ . Here, $\mathcal { T } _ { \pm } : = \{ i \ :$ $y _ { i } = \pm 1 \}$ , and $x ^ { + } = ( x _ { i } ) _ { i \in \mathbb { Z } _ { + } } , x ^ { - } = ( x _ { i } ) _ { i \in \mathbb { Z } _ { - } } , m _ { \pm } = | \mathbb { Z } _ { \pm } |$ , and $\underline { { m } } = \operatorname* { m i n } ( m _ { + } , m _ { - } )$ . Without loss of generality, we assume that both $x ^ { + } , x ^ { - }$ are both sorted in descending order: $x _ { 1 } ^ { \pm } \geq \ldots \geq x _ { m \pm } ^ { \pm }$

Using $\alpha = \mu + \nu , \beta = \mu - \nu .$ we have

$$
\begin{array}{r c l} P _ {\mathrm{hi}} (\gamma , - x) & = & \min _ {\alpha + \beta \geq 0} - \frac {\gamma}{2} (\alpha + \beta) + \sum_ {i = 1} ^ {m _ {+}} (x _ {i} ^ {+} + \alpha) _ {+} + \sum_ {i = 1} ^ {m _ {-}} (x _ {i} ^ {-} + \beta) _ {+} \\ & = & \min _ {\alpha ,   \beta} \max _ {t \geq 0} - \frac {\gamma}{2} (\alpha + \beta) + \sum_ {i = 1} ^ {m _ {+}} (x _ {i} ^ {+} + \alpha) _ {+} + \sum_ {i = 1} ^ {m _ {-}} (x _ {i} ^ {-} + \beta) _ {+} - t (\alpha + \beta) \\ & = & \max _ {t \geq 0} \min _ {\alpha ,   \beta} - (\frac {\gamma}{2} + t) (\alpha + \beta) + \sum_ {i = 1} ^ {m _ {+}} (x _ {i} ^ {+} + \alpha) _ {+} + \sum_ {i = 1} ^ {m _ {-}} (x _ {i} ^ {-} + \beta) _ {+} \\ & = & \max _ {t > 0} F (\frac {\gamma}{2} + t, x ^ {+}) + F (\frac {\gamma}{2} + t, x ^ {-}), \end{array}\tag{33}
$$

where, for $h \in \mathbb { R }$ and $x \in \mathbb { R } ^ { p } , x _ { 1 } \geq . . . \geq x _ { p } ,$ , we set

$$
F (h, x) := \min _ {z} - h z + \sum_ {i = 1} ^ {p} (z + x _ {i}) _ {+},\tag{34}
$$

Expression of the function F. If $h > p ,$ then with $z  + \infty$ we obtain $F ( h , x ) = - \infty$ . Similarly, if $h < 0$ , then $z  - \infty$ yields $F ( h , x ) = - \infty$ . When $0 \leq h \leq p$ , we proceed by expressing $F$ in dual form:

$$
F (h, x) = \max _ {u} u ^ {T} x: 0 \leq u \leq \mathbf {1}, u ^ {T} \mathbf {1} = h.
$$

If $h = p ,$ then the only feasible point is $u = { \bf 1 }$ , so that $F ( p , x ) = \mathbf { 1 } ^ { T } x$ . If $0 \leq h < 1$ , choosing $u _ { 1 } = h , u _ { 2 } = \ldots = u _ { p } = 0 \quad$ , we obtain the lower bound $F ( h , x ) \geq h x _ { 1 }$ , which is attained with $z = - x _ { 1 }$

Assume now that $1 \leq h < p$ . Let $h = q + r ,$ with $q = \lfloor h \rfloor$ the integer part of $h ,$ and $0 \leq r < 1$ Choosing $u _ { 1 } = \ldots = u _ { q } = 1 , u _ { q + 1 } = r ,$ , we obtain the lower bound

$$
F (h, x) \geq \sum_ {j = 1} ^ {q} x _ {j} + r x _ {q + 1},
$$

which is attained by choosing $z = - x _ { q + 1 }$ in the expression (34).

To summarize:

$$
F (h, x) = \left\{ \begin{array}{l l} h x _ {1} & \text { if } 0 \leq h <   1, \\ \sum_ {j = 1 \atop p} ^ {\lfloor h \rfloor} x _ {j} + (h - \lfloor h \rfloor) x _ {\lfloor h \rfloor + 1} & \text { if } 1 \leq h <   p, \\ \sum_ {j = 1} ^ {p} x _ {j} & \text { if } h = p, \\ - \infty & \text { otherwise. } \end{array} \right.\tag{35}
$$

A more compact expression, valid for $0 \leq h \leq p$ if we set $x _ { p + 1 } = x _ { p }$ and assume that a sum over an empty index sets is zero, is

$$
F (h, x) = \sum_ {j = 1} ^ {\lfloor h \rfloor} x _ {j} + (h - \lfloor h \rfloor) x _ {\lfloor h \rfloor + 1}, 0 \leq h \leq p.
$$

Note that $F ( \cdot , x )$ is the piece-wise linear function that interpolates the sum of the h largest elements of x at the integer break points $h = 0 , \ldots , p$

Expression of $P _ { \mathrm { h i } } ( \gamma , - x )$ . We start with the expression found in (33):

$$
P _ {\mathrm{hi}} (\gamma , - x) = \max _ {t \geq 0} F (\frac {\gamma}{2} + t, x ^ {+}) + F (\frac {\gamma}{2} + t, x ^ {-}).
$$

Since the domain of $F ( \cdot , x ^ { + } ) + F ( \cdot , x ^ { - } )$ is $[ 0 , \underline { m } ]$ , and with $0 \leq \gamma / 2 \leq \gamma _ { 0 } / 2 = \underline { { m } } .$ , we get

$$
P _ {\mathrm{hi}} (\gamma , - x) = \max _ {\gamma / 2 \leq h \leq \underline {{m}}} G (h, x ^ {+}, x ^ {-}) := F (h, x ^ {+}) + F (h, x ^ {-}).
$$

Since $F ( \cdot , x )$ with $x \in \mathbb { R } ^ { p }$ is a piece-wise linear function with break points at $0 , \ldots , p ,$ , a maximizer of $G ( \cdot , x ^ { + } , x ^ { - } )$ over $[ \gamma / 2$ , m] lies in $\{ \gamma / 2 , \lfloor \gamma / 2 \rfloor + 1 , . . . , \underline { { { m } } } \}$ . Thus,

$$
P _ {\mathrm{hi}} (\gamma , - x) = \max \left(G (\frac {\gamma}{2}, x ^ {+}, x ^ {-}), \max _ {h \in \{\lfloor \gamma / 2 \rfloor + 1, \dots , \underline {{m}} \}} G (h, x ^ {+}, x ^ {-})\right).
$$

Let us examine the second term, and introduce the notation $\bar { x } _ { j } : = x _ { j } ^ { + } + x _ { j } ^ { - } , j = 1 , \ldots , \underline { { { m } } } \colon$

$$
\begin{array}{r c l} \max _ {h \in \{\lfloor \gamma / 2 \rfloor + 1, \ldots , \underline {{m}} \}} G (h, x ^ {+}, x ^ {-}) & = & \max _ {h \in \{\lfloor \gamma / 2 \rfloor + 1, \ldots , \underline {{m}} \}} \sum_ {j = 1} ^ {h} (x _ {j} ^ {+} + x _ {j} ^ {-}) \\ & = & \sum_ {j = 1} ^ {\lfloor \gamma / 2 \rfloor + 1} \bar {x} _ {j} + \sum_ {j = \lfloor \gamma / 2 \rfloor + 2} ^ {\underline {{m}}} (\bar {x} _ {j}) _ {+}, \end{array}
$$

with the convention that sums over empty index sets are zero. Since

$$
G (\frac {\gamma}{2}, x ^ {+}, x ^ {-}) = \sum_ {j = 1} ^ {\lfloor \gamma / 2 \rfloor} \bar {x} _ {j} + (\frac {\gamma}{2} - \lfloor \frac {\gamma}{2} \rfloor) \bar {x} _ {\lfloor \gamma / 2 \rfloor + 1},
$$

we obtain

$$
P _ {\mathrm{hi}} (\gamma , - x) = \sum_ {j = 1} ^ {\lfloor \gamma / 2 \rfloor} \bar {x} _ {j} + \max \left((\frac {\gamma}{2} - \lfloor \frac {\gamma}{2} \rfloor) \bar {x} _ {\lfloor \gamma / 2 \rfloor + 1}, \bar {x} _ {\lfloor \gamma / 2 \rfloor + 1} + \sum_ {j = \lfloor \gamma / 2 \rfloor + 2} ^ {\underline {{m}}} (\bar {x} _ {j}) _ {+}\right).
$$

An equivalent expression is:

$$
\begin{array}{r c l} P _ {\mathrm{hi}} (\gamma , - x) & = & \sum_ {j = 1} ^ {\lfloor \gamma / 2 \rfloor} \bar {x} _ {j} - (\frac {\gamma}{2} - \lfloor \frac {\gamma}{2} \rfloor) (- \bar {x} _ {\lfloor \gamma / 2 \rfloor + 1}) _ {+} + \sum_ {j = \lfloor \gamma / 2 \rfloor + 1} ^ {\underline {{m}}} (\bar {x} _ {j}) _ {+}, 0 \leq \gamma \leq 2 \underline {{m}}, \\ & & \bar {x} _ {j} := x _ {j} ^ {+} + x _ {j} ^ {-}, j = 1, \ldots , \underline {{m}}. \end{array}
$$

The function $P _ { \mathrm { h i } } ( \cdot , - x )$ linearly interpolates the values obtained for $\gamma \ = \ 2 q$ with q integer in $\{ 0 , \ldots , \underline { { m } } \}$

$$
P _ {\mathrm{hi}} (2 q, - x) = \sum_ {j = 1} ^ {q} \bar {x} _ {j} + \sum_ {j = q + 1} ^ {\underline {{m}}} (\bar {x} _ {j}) _ {+}.
$$

## C.2 Computing $\Phi ( x ^ { + } , x ^ { - } )$

Let us consider the problem of computing

$$
\Phi (x ^ {+}, x ^ {-}) := \min _ {\nu} \sum_ {i = 1} ^ {m _ {+}} (x _ {i} ^ {+} + \nu) _ {+} + \sum_ {i = 1} ^ {m _ {-}} (x _ {i} ^ {-} - \nu) _ {+},
$$

with $x ^ { \pm } \in \mathbb { R } ^ { m \pm } , x _ { 1 } ^ { \pm } \geq . . . \geq x _ { m \pm } ^ { \pm }$ , given. We can express $\Phi ( x ^ { + } , x ^ { - } )$ in terms of the function F defined in (34):

$$
\begin{array}{r c l} \Phi (x ^ {+}, x ^ {-}) & = & \min _ {\nu_ {+}, \nu_ {-}} \sum_ {i \in \mathcal {I} _ {+}} (x _ {i} ^ {+} + \nu^ {+}) _ {+} + \sum_ {i \in \mathcal {I} _ {-}} (x _ {i} ^ {-} - \nu^ {-}) _ {+}: \nu^ {+} = \nu^ {-} \\ & = & \max _ {h} \min _ {\nu^ {+}, \nu^ {-}} - h (\nu^ {+} - \nu^ {-}) + \sum_ {i \in \mathcal {I} _ {+}} (x _ {i} ^ {+} + \nu^ {+}) _ {+} + \sum_ {i \in \mathcal {I} _ {-}} (x _ {i} ^ {-} - \nu^ {-}) _ {+} \\ & = & \max _ {h} \min _ {\nu^ {+}, \nu^ {-}} - h \nu^ {+} + \sum_ {i \in \mathcal {I} _ {+}} (x _ {i} ^ {+} + \nu^ {+}) _ {+} + h \nu^ {-} + \sum_ {i \in \mathcal {I} _ {-}} (x _ {i} ^ {-} - \nu^ {-}) _ {+} \\ & = & \max _ {h} \left(\min _ {\nu} - h \nu + \sum_ {i \in \mathcal {I} _ {+}} (x _ {i} ^ {+} + \nu) _ {+}\right) + \left(\min _ {\nu} - h \nu + \sum_ {i \in \mathcal {I} _ {-}} (x _ {i} ^ {-} + \nu) _ {+}\right) (\nu_ {+} = - \nu_ {-} = \nu) \\ & = & \max _ {h} F (h, x ^ {+}) + F (h, x ^ {-}) \\ & = & \max _ {0 \leq h \leq m} F (h, x ^ {+}) + F (h, x ^ {-}) \\ & = & \max (A, B, C), \end{array}
$$

where $F$ is defined in (34), and

$$
A = \max _ {0 \leq h <   1} F (h, x ^ {+}) + F (h, x ^ {-}), B := \max _ {1 \leq h <   \underline {{m}}} F (h, x ^ {+}) + F (h, x ^ {-})), C = F (\underline {{m}}, x ^ {+}) + F (\underline {{m}}, x ^ {-}).
$$

We have

$$
A := \max _ {0 \leq h <   1} F (h, x ^ {+}) + F (h, x ^ {-}) = \max _ {0 \leq h <   1} h (x _ {1} ^ {+} + x _ {1} ^ {-}) = (x _ {1} ^ {+} + x _ {1} ^ {-}) _ {+}.
$$

Next:

$$
\begin{array}{r c l} B & = & \max _ {1 \leq h <   \underline {{m}}} F (h, x ^ {+}) + F (h, x ^ {-}) \\ & = & \max _ {q \in \{1, \ldots , \underline {{m}} - 1 \}, r \in [ 0, 1 [} \sum_ {i = 1} ^ {q} (x _ {i} ^ {+} + x _ {i} ^ {-}) + r (x _ {q + 1} ^ {+} + x _ {q + 1} ^ {-}) \\ & = & \max _ {q \in \{1, \ldots , \underline {{m}} - 1 \}} \sum_ {i = 1} ^ {q} (x _ {i} ^ {+} + x _ {i} ^ {-}) + (x _ {q + 1} ^ {+} + x _ {q + 1} ^ {-}) _ {+} \\ & = & (x _ {1} ^ {+} + x _ {1} ^ {-}) + \sum_ {i = 2} ^ {\underline {{m}}} (x _ {i} ^ {+} + x _ {i} ^ {-}) _ {+}. \end{array}
$$

Observe that

$$
B \geq C = \sum_ {i = 1} ^ {\underline {{m}}} (x _ {i} ^ {+} + x _ {i} ^ {-}).
$$

Moreover, if $( x _ { 1 } ^ { + } + x _ { 1 } ^ { - } ) \ge 0$ , then $\begin{array} { r } { B = \sum _ { i = 1 } ^ { m } ( x _ { i } ^ { + } + x _ { i } ^ { - } ) _ { + } \geq A } \end{array}$ . On the other hand, if $x _ { 1 } ^ { + } + x _ { 1 } ^ { - } \leq 0$ then $x _ { i } ^ { + } + x _ { i } ^ { - } \overset { - } { \leq } 0$ for $2 \leq j \leq \underline { m }$ , and $\begin{array} { r } { A = \bar { \sum _ { i = 1 } ^ { m } } ( x _ { i } ^ { + } + x _ { i } ^ { - } ) _ { + } \geq x _ { 1 } ^ { + } + x _ { 1 } ^ { - } = B } \end{array}$ . In all cases,

$$
\Phi (x ^ {+}, x ^ {-}) = \max (A, B, C) = \sum_ {i = 1} ^ {m} (x _ {i} ^ {+} + x _ {i} ^ {-}) _ {+}.
$$

## C.3 SAFE-SVM test

Now we consider the problem that arises in the SAFE-SVM test (22):

$$
G (z) := \min _ {0 \leq \kappa \leq 1} \sum_ {i = 1} ^ {p} (1 - \kappa + \kappa z _ {i}) _ {+},
$$

where $z \in \mathbb { R } ^ { p }$ is given. (The SAFE-SVM condition (22) involves $z _ { i } = \gamma _ { 0 } / ( 2 \lambda _ { 0 } ) ( x _ { \lceil i \rceil } ^ { + } + x _ { \lceil i \rceil } ^ { - } ) , \ i =$ $1 , \ldots , p : = { \underline { { m } } } . )$ We develop an algorithm to compute the quantity $G ( z )$ , the complexity of which grows as $O ( d \log d )$ , where d is (less than) the number of non-zero elements in z.

$$
\text { Define } \mathcal {I} _ {\pm} = \{i: \pm z _ {i} > 0 \}, k := | \mathcal {I} _ {+} |, h := | \mathcal {I} _ {-} |, l = \mathcal {I} _ {0}, l := | \mathcal {I} _ {0} |.
$$

If $k = 0 , \mathcal { T } _ { + }$ is empty, and $\kappa = 1$ achieves the lower bound of 0 for $G ( z )$ . If $k > 0$ and $h = 0$ ， that is, $k + l = p$ , then $\mathcal { T } _ { - }$ is empty, and an optimal κ is attained in $\{ 0 , 1 \}$ . In both cases $( \mathcal { T } _ { + } \ \mathrm { o r } \ \mathcal { T } _ { - }$ empty), we can write

$$
G (z) = \min _ {\kappa \in \{0, 1 \}} \sum_ {i = 1} ^ {p} (1 - \kappa + \kappa z _ {i}) _ {+} = \min \left(p, S _ {+}\right), S _ {+} := \sum_ {i \in \mathcal {I} _ {+}} z _ {i},
$$

with the convention that a sum over an empty index set is zero.

Next we proceed with the assumption that $k \neq 0$ and h $\neq 0 .$ Let us re-order the elements of $\mathcal { T } _ { - }$ in decreasing fashion, so that $z _ { i } > 0 = z _ { k + 1 } = . . . = z _ { k + l } > z _ { k + l + 1 } \geq . . . \geq z _ { p }$ , for every $i \in \mathcal { Z } _ { + }$ (The case when $\mathcal { T } _ { 0 }$ is empty is handled simply by setting $l = 0$ in our formula.) We have

$$
G (z) = k + l + \min _ {0 \leq \kappa \leq 1} \left\{\kappa \alpha + \sum_ {i = k + l + 1} ^ {p} (1 - \kappa + \kappa z _ {i}) _ {+} \right\},
$$

where, $\alpha : = S _ { + } - k - l$ . The minimum in the above is attained at $\kappa = 0 ,$ 1 or one of the break points $1 / ( 1 - z _ { j } ) \in ( 0 , 1 )$ , where $j \in \{ k + l + 1 , . . . , p \} . \mathrm { A t } \kappa = 0 , 1$ , the objective function of the original problem takes the values $S _ { + } , p$ , respectively. The value of the same objective function at the break point $\kappa = 1 / ( 1 - z _ { j } ) , j = k + l + 1 , \ldots , p ,$ is $k + l + G _ { j } ( z )$ , where

$$
\begin{array}{l l} G _ {j} (z) & := \frac {\alpha}{1 - z _ {j}} + \sum_ {i = k + l + 1} ^ {p} \left(\frac {z _ {i} - z _ {j}}{1 - z _ {j}}\right) _ {+} \\ & = \frac {\alpha}{1 - z _ {j}} + \frac {1}{1 - z _ {j}} \sum_ {i = k + l + 1} ^ {j - 1} (z _ {i} - z _ {j}) \\ & = \frac {1}{1 - z _ {j}} \left(\alpha - (j - k - l - 1) z _ {j} + \sum_ {i = k + l + 1} ^ {j - 1} z _ {i}\right) \\ & = \frac {1}{1 - z _ {j}} \left(S _ {+} - (j - 1) z _ {j} - (k + l) (1 - z _ {j}) + \sum_ {i = k + l + 1} ^ {j - 1} z _ {i}\right) \\ & = - (k + l) + \frac {1}{1 - z _ {j}} \left(\sum_ {i = 1} ^ {j - 1} z _ {i} - (j - 1) z _ {j}\right). \end{array}
$$

This allows us to write

$$
G (z) = \min \left(p, \sum_ {i = 1} ^ {k} z _ {i}, \min _ {j \in \{k + l + 1, \dots , p \}} \frac {1}{1 - z _ {j}} \left(\sum_ {i = 1} ^ {j - 1} z _ {i} - (j - 1) z _ {j}\right)\right).
$$

The expression is valid when $k + l = p \ ( h = 0 , \mathcal { T } _ { - }$ is empty), $l = 0 \ (  { T _ { \mathrm { 0 } } }$ is empty), or $k = 0 \ ( \mathbb { Z } _ { + }$ is empty) with the convention that the sum (resp. minimum) over an empty index set is $0 \ ( \mathrm { r e s p . } + \infty )$

We can summarize the result with the compact formula:

$$
G (z) = \min _ {z} \frac {1}{1 - z} \sum_ {i = 1} ^ {p} (z _ {i} - z) _ {+}: z \in \{- \infty , 0, (z _ {j}) _ {j: z _ {j} <   0} \}.
$$

Let us detail an algorithm for computing $G ( z )$ . Assume $h > 0$ . The quantity

$$
\underline {{G}} (z) := \min _ {k + l + 1 \leq j \leq p} \left(G _ {j} (z)\right)
$$

can be evaluated in less than $O ( h )$ , via the following recursion:

$$
\begin{array}{r c l} G _ {j + 1} (z) & = & \frac {1 - z _ {j}}{1 - z _ {j + 1}} G _ {j} (z) - j \frac {z _ {j + 1} - z _ {j}}{1 - z _ {j + 1}}    ,    j = k + l + 1, \ldots , p, \\ \underline {{G}} _ {j + 1} (z) & = & \min (\underline {{G}} _ {j} (z), G _ {j + 1} (z)) \end{array}\tag{36}
$$

with initial values

$$
G _ {k + l + 1} (z) = \underline {{G}} _ {k + l + 1} (z) = \frac {1}{1 - z _ {k + l + 1}} \left(\sum_ {i = 1} ^ {k + l} z _ {i} - (k + l) z _ {k + l + 1}\right).
$$

On exit, $\underline { G } ( z ) = \underline { G } _ { p }$

Our algorithm is as follows.

Algorithm for the evaluation of $G ( z )$

1. Find the index sets $\mathcal { T } _ { + } , \mathcal { T } _ { - } , \mathcal { T } _ { 0 }$ , and their respective cardinalities $k , h , l$

2. If $k = 0 .$ , set $G ( z ) = 0$ and exit.

3. Set $\begin{array} { r } { S _ { + } = \sum _ { i = 1 } ^ { k } z _ { i } . } \end{array}$

4. If $h = 0 ,$ , set $G ( z ) = \operatorname* { m i n } ( p , S _ { + } )$ , and exit.

5. If $h > 0$ , order the negative elements of $z ,$ and evaluate $\underline { { G } } ( z )$ by the recursion (36). Set $G ( z ) = \operatorname* { m i n } ( p , S _ { + } , \underline { { G } } ( z ) )$ and exit.

The complexity of evaluating $G ( z )$ thus grows in $O ( k + h \log h )$ , which is less than $O ( d \log d )$ , where $d = k + h$ is the number of non-zero elements in z.

## Appendix D. Computing $P _ { \log } ( \gamma , x )$ via an interior-point method

We consider the problem (26) which arises with the logistic loss. We can use a generic interiorpoint method Boyd and Vandenberghe (2004), and exploit the decomposable structure of the dual function $G _ { \mathrm { l o g } }$ . The algorithm is based on solving, via a variant of Newton’s method, a sequence of linearly constrained problems of the form

$$
\min _ {\theta} \tau x ^ {T} \theta + \log (G _ {\log} (\theta) - \gamma) + \sum_ {i = 1} ^ {m} \log (- \theta - \theta^ {2}): z ^ {T} \theta = 0,
$$

where $\tau > 0$ is a parameter that is increased as the algorithm progresses, and the last terms correspond to domain constraints $\theta \in [ - 1 , 0 ] ^ { m }$ . As an initial point, we can take the point θ generated by scaling, as explained in section 4.2. Each iteration of the algorithm involves solving a linear system in variable δ, of the form $H \delta = h$ with H is a rank-two modification to the Hessian of the objective function in the problem above. It is easily verified that the matrix H has a “diagonal plus rank-two” structure, that is, it can be written as $\dot { H } = { D } - { g g ^ { T } } - v v ^ { T }$ , where the $m \times m$ matrix D is diagonal and $g , v \in \mathbb { R } ^ { m }$ are computed in $O ( m )$ ). The matrix H can be formed, as the associated linear system solved, in $O ( m )$ time. Since the number of iterations for this problem with two constraints grows as $\log ( 1 / \epsilon ) O ( 1 )$ , the total complexity of the algorithm is $\log ( 1 / \epsilon ) O ( m )$ (ǫ is the absolute accuracy at which the interior-point method computes the objective). We note that memory requirements for this method also grow as $O ( m )$

## Appendix E. On thresholding methods for LASSO

Sparse classification algorithms may return a classifier vector w with many small, but not exactly zero, elements. This implies that we need to choose a thresholding rule to decide which elements to set to zero. In this section, we discuss an issue related to the thresholding rule originally proposed for the interior point method for Logistic algorithm in Koh et al. (2007), and propose a new thresholding rule.

The KKT thresholding rule. Recall that the primal problem for LASSO is

$$
\phi (\lambda) = \min _ {w} \frac {1}{2} \| X ^ {T} w - y \| _ {2} ^ {2} + \lambda \| w \| _ {1}.\tag{37}
$$

Observing that the KKT conditions imply that, at optimum, $( X ( X ^ { T } w - y ) ) _ { k } = \lambda \mathrm { s i g n } ( w _ { k } )$ , with the convention sign $( 0 ) \in [ - 1 , 1 ]$ ], and following the ideas of Koh et al. (2007), the following thresholding rule can be proposed: at optimum, set component $w _ { k }$ to 0 whenever

$$
\left| \left(X \left(X ^ {T} w - y\right)\right) _ {k} \right| \leq 0. 9 9 9 9 \lambda .\tag{38}
$$

We refer to this rule as the $\mathrm { ^ { 6 6 } K K T ^ { 5 } }$ rule.

The IPM-LASSO algorithm takes as input a “duality $\mathrm { g a p } ^ { \mathrm { , } \mathrm { , } }$ parameter ǫ, which controls the relative accuracy on the objective. When comparing the IPM code results with other algorithms such as GLMNET, we observed chaotic behaviors when applying the KKT rule, especially when the duality gap parameter ǫ was not small enough. More surprisingly, when this parameter is not small enough, some components $w _ { k }$ with absolute values not close to 0 can be thresholded. This suggests that the KKT rule should only be used for problems solved with a small enough duality gap ǫ. However, setting the duality gap to a small value can dramatically slow down computations. In our experiments, changing the duality gap from $\epsilon = 1 0 ^ { - 4 }$ to $1 0 ^ { - 6 }$ (resp. $1 0 ^ { - 8 } )$ increased the computational time by 30% to 40% (resp. 50 to $1 0 0 \% )$

An alternative method. We propose an alternative thresholding rule, which is based on controlling the perturbation of the objective function that is induced by thresholding.

Assume that we have solved the LASSO problem above, with a given duality gap parameter ǫ. If we denote by $w ^ { * }$ the classifier vector delivered by the IPM algorithm, $w ^ { * }$ is ǫ-sub-optimal, that is, achieves a value

$$
\phi^ {*} = \frac {1}{2} \| X w ^ {*} - y \| _ {2} ^ {2} + \lambda \| w ^ {*} \| _ {1},
$$

with $0 \leq \phi ^ { * } - \phi ( \lambda ) \leq \epsilon \phi ( \lambda )$

For a given threshold $\tau > 0$ , consider the thresholded vector $\tilde { w } ( \tau )$ defined as

$$
\tilde {w} _ {k} (\tau) = \left\{ \begin{array}{l l} 0 & \text { if } | w _ {k} ^ {*} | \leq \tau , \\ w _ {k} ^ {*} & \text { otherwise }, \end{array} \right. k = 1, \ldots , n.
$$

We have $\tilde { w } ( \tau ) = w ^ { * } + \delta ( \tau )$ where the vector of perturbation $\delta ( \tau )$ is such that

$$
\delta_ {k} (\tau) = \left\{ \begin{array}{l l} - w _ {k} ^ {*} & \text { if } | w _ {k} ^ {*} | \leq \tau , \\ 0 & \text { otherwise }, \end{array} \right. k = 1, \ldots , n.
$$

Note that, by construction, we have $\| w ^ { * } \| _ { 1 } = \| w ^ { * } + \delta \| _ { 1 } + \| \delta \|$ <sub>1</sub>. Also note that if $w ^ { * }$ is sparse, so is $\delta .$

Let us now denote by $\phi _ { \tau }$ the LASSO objective that we obtain upon replacing the optimum classifier $w ^ { * }$ with its thresholded version $\tilde { w } ( \tau ) = w ^ { * } + \delta ( \tau )$

$$
\phi_ {\tau} := \frac {1}{2} \| X (w ^ {*} + \delta (\tau)) - y \| _ {2} ^ {2} + \lambda \| w ^ {*} + \delta (\tau) \| _ {1}.
$$

Since $w ( \tau )$ is (trivially) feasible for the primal problem, we have $\phi _ { \tau } \geq \phi ( \lambda )$ ). On the other hand,

$$
\begin{array}{r c l} \phi_ {\tau} & = & \frac {1}{2} \| X w ^ {*} - y \| _ {2} ^ {2} + \lambda \| w ^ {*} + \delta (\tau) \| _ {1} + \frac {1}{2} \| X \delta (\tau) \| _ {2} ^ {2} + \delta (\tau) ^ {T} X ^ {T} (X w ^ {*} - y) \\ & \leq & \frac {1}{2} \| X w ^ {*} - y \| _ {2} ^ {2} + \lambda \| w ^ {*} \| _ {1} + \frac {1}{2} \| X \delta (\tau) \| _ {2} ^ {2} + \delta (\tau) ^ {T} X ^ {T} (X w ^ {*} - y). \end{array}
$$

For a given $\alpha > 1$ , the condition

$$
\mathcal {C} (\tau) := \frac {1}{2} \| X \delta (\tau) \| _ {2} + \delta (\tau) ^ {T} X ^ {T} (X w ^ {*} - y) \leq \kappa \phi^ {*}, \kappa := \frac {1 + \alpha \epsilon}{1 + \epsilon} - 1 \geq 0,\tag{39}
$$

allows to write

$$
\phi (\lambda) \leq \phi_ {\tau} \leq (1 + \alpha \epsilon) \phi (\lambda).
$$

The condition (39) then implies that the thresholded classifier is sub-optimal, with relative accuracy $\alpha \epsilon$

Our proposed thresholding rule is based on the condition (39). Precisely, we choose the parameter $\alpha > 0$ , then we set the threshold level $\tau$ by solving, via line search, the largest threshold τ allowed by condition (39):

$$
\tau_ {\alpha} = \arg \max _ {\tau \geq 0} \left\{\tau : \| X \delta (\tau) \| _ {2} \leq \left(\sqrt {\frac {1 + \alpha \epsilon}{1 + \epsilon}} - 1\right) \| X w ^ {*} - y \| _ {2} \right\}.
$$

The larger α is, the more elements the rule allows to set to zero; at the same time, the more degradation in the objective will be observed: precisely, the new relative accuracy is bounded by αǫ. The rule also depends on the duality gap parameter ǫ. We refer to the thresholding rule as $\operatorname { T R } ( \alpha )$ in the sequel. In practice, we observe that the value $\alpha = 2$ works well, in a sense made more precise below.

The complexity of the rule is $O ( m n )$ . More precisely, the optimal dual variable $\theta ^ { * } = X w ^ { * } - y$ is returned by IPM-LASSO. The matrix $X \theta ^ { * } = X ( X ^ { T } w ^ { * } - y )$ is computed once for all in $O ( m n )$ We then sort the optimal vector $w ^ { * }$ so that $| w _ { ( 1 ) } ^ { * } | \leq \ldots \leq | w _ { ( n ) } ^ { * } |$ , and set $\tau = \tau _ { 0 } = | w _ { ( n ) } ^ { * } |$ , so that $\delta _ { k } ( \tau _ { 0 } ) = - w _ { k } ^ { * }$ and $\tilde { w } _ { k } ( \tau _ { 0 } ) = 0$ for all $k = 1 , \dots , n .$ . The product $\dot { X } \delta ( \tau _ { 0 } )$ is computed in $O ( { \dot { m } } n )$ , while the product $\stackrel { \cdot \cdot } { \delta } ( \tau _ { 0 } ) ^ { T } ( X ^ { T } \theta ^ { * } )$ is computed in $O ( n )$ . If the quantity $\begin{array} { r } { \mathcal { C } ( \tau _ { 0 } ) = \frac { 1 } { 2 } \| X \delta ( \tau _ { 0 } ) \| _ { 2 } + \delta ( \tau _ { 0 } ) ^ { T } ( X ^ { T } \theta ^ { * } ) } \end{array}$ is greater than $\kappa \phi ^ { \star }$ , then we set $\tau = \tau _ { 1 } = | w _ { ( n - 1 ) } ^ { * } |$ . We have $\delta _ { k } ( \tau _ { 1 } ) = \mathbf { \bar { \delta } } \delta _ { k } ( \tau _ { 0 } )$ for any $k \neq ( n )$ and $\delta _ { ( n ) } ( \tau _ { 1 } ) = 0$ . Therefore, $\mathcal { C } ( \tau _ { 1 } )$ can be deduced from $\mathcal { C } ( \tau _ { 0 } )$ in $O ( n )$ We proceed by successively setting $\tau _ { k } = | w _ { ( n - k ) } ^ { * } |$ until we reach a threshold $\tau _ { k }$ such that ${ \mathcal C } ( \tau _ { k } ) \le \kappa \phi ^ { * }$

Simulation study. We conducted a simple simulation study to evaluate our proposal and compare it to the KKT thresholding rule. Both methods were further compared to the results returned by the glmnet R package. The latter algorithm returns hard zeros in the classifier coeficients, and we have chosen the corresponding sparsity pattern as the “ground truth”, which the IPM should recover.

We first experimented with synthetic data. We generated samples of the pair $( X , y )$ for various values of $( m , n )$ . We present the results for $( m , n ) \ : = \ : ( 5 0 0 0 , 2 5 0 0 )$ and $( m , n ) \ : = \ : ( 1 0 0 , 5 0 0 )$ . The number s of relevant features was set to mi $_ 1 ( m , n / 2 )$ Features were drawn from independent $\mathcal { N } ( 0 , 1 )$ distributions and y was computed as $y = X ^ { T } w + \xi$ , where $\xi \sim \mathcal { N } ( 0 , 0 . 2 )$ and $w$ is a vector of $\mathbb { R } ^ { n }$ with first s components equal to $0 . 1 + 1 / s$ and remaining $n - s$ components set to 0. Because glmnet includes an unpenalized intercept while IPM method does not, both y and X were centered before applying either methods to make their results comparable.

Results are presented on Figures 6. First, the KKT thresholding rule was observed to be very chaotic when the duality gap was set to $\epsilon = 1 0 ^ { - 4 }$ (we recall here that the default value for the duality gap in IPM MATLAB implementation is $\epsilon = 1 0 ^ { - 3 } )$ , while it was way better when duality gap was set to $\epsilon = 1 0 ^ { - 8 }$ (somehow justifying our choice of considering the sparsity pattern returned by glmnet as the ground truth). Therefore, for applications where computational time is not critical, running IPM method and applying KKT thresholding rule should yield appropriate results. However, when computational time matters, passing the duality gap from, say, $1 0 ^ { - 4 }$ to $1 0 ^ { - 8 }$ , is not a viable option. Next, regarding our proposal, we observed that it was significantly better than KKT thresholding rule when the duality gap was set to $1 0 ^ { - 4 }$ and equivalent to KKT thresholding rule for a duality gap of $1 0 ^ { - 8 }$ . Interestingly, setting $\alpha = 1 . 5$ in (39) generally enabled to achieved very good results for low values of $\lambda ,$ but lead to irregular results for higher values of λ (in the case $m = 1 0 0$ , results were unstable for the whole range of λ values we considered). Overall, the choices $\alpha = 2 .$ , 3 and 4 lead to acceptable results. A little irregularity remained with $\alpha = 2$ for high values of $\lambda ,$ but this choice of α performed the best for lower values of λ. As for choices $\alpha = 3$ and $\alpha = 4 ,$ , it is noteworthy that the results were all the better as the dimension n was low.

## E.1 Real data examples

We also applied our proposal and compared it to KKT rule (38) on real data sets arising in text classification. More precisely, we used the New York Times headlines data set presented in the Numerical results Section. For illustration, we present here results we obtained for the topic $^ { 1 1 } \mathrm { C h i n a } ^ { 1 1 }$ and the year 1985. We successively ran IPM-LASSO method with duality gap set to $1 0 ^ { - 4 }$ and $1 0 ^ { - 8 }$ and compare the number of active features returned after applying KKT thresholding rule (38) and TR (1.5), TR (2), TR (3) and TR (4). Results are presented on Figure 7. Because we could not applied glmnet on this data set, the ground truth was considered as the result of KKT rule, when applied to the model returned by IPM-LASSO ran with duality gap set to $1 0 ^ { - 1 0 }$ . Applying KKT rule on the model built with a duality gap of $1 0 ^ { - 4 }$ lead to very misleading results again, especially for low values of λ. In this very high-dimensional setting $( n = 3 8 3 7 7 { \mathrm { ~ h e r e } } )$ , our rule generally resulted in a slight "underestimation" of the true number of active features for the lowest values of λ when the duality gap was set to $1 0 ^ { - 4 }$ . This suggests that the “optimal” α for our rule might depend on both n and λ when the duality gap is not small enough. However, we still observed that our proposal significantly improved upon KKT rule when the duality gap was set to $1 0 ^ { - 4 }$

![](images/1c77e14e29c92ad21a7feabfdd9b93f9eff6da501afe5b4ac110faf429e23215.jpg)

![](images/9d0af7a19ba8588299199219e42666d7548e1307d4394d9f7399149118ba5ee6.jpg)

![](images/476b1a21fef4d9b208b386cef2119816fd4b7c34e07df62ac559a9234f9d673c.jpg)

![](images/53ea2e56d826bd3cc8e2171959cef78ad0ccd035841d5546031d1903e32da66e.jpg)  
Figure 6: Comparison of several thresholding rules on synthetic data: the case $m = 5 0 0 0 , n = 1 0 0$ (top panel) and $m = 1 0 0$ , n = 500 (bottom panel) with duality gap in IPM method set to (i) $1 0 ^ { - 4 }$ (left panel) and (iii) $1 0 ^ { - 8 }$ (right panel). The curves represent the diferences between the number of active features returned after each thresholding method and the one returned by glmnet (this diference is further divided by the total number of features n). The graphs present the results attached to six thresholding rules: the one proposed by Koh et al. (2007) and five versions of our proposal, corresponding to setting α in (39) to 1.5, 2, 3, 4 and 5 respectively. Overall, these results suggest that by setting $\alpha \in ( 2 , 5 )$ ， our rule is less sensitive to the value of the duality gap parameter in IPM-LASSO than is the rule proposed by Koh et al. (2007).

![](images/6440031b96b84c5a7a1e81c9528b8796d86049e68144768e7602db0b95548aff.jpg)

![](images/69bd5857852adfc564b6c25a2efc37402761c3678ffc3b17235179895f1dc3e2.jpg)  
Figure 7: Comparison of several thresholding rules on the NYT headlines data set for the topic "China" and year 1985. Duality gap in IPM-LASSO was successively set to $1 0 ^ { - 4 } ( l e f t$ panel) and $1 0 ^ { - 8 }$ (right panel). The curves represent the diferences between the number of active features returned after each thresholding method and the one returned by the KKT rule when duality gap was set to $1 0 ^ { - 1 0 }$ . The graphs present the results attached to five thresholding rules: the KKT rule and four versions of our rule, corresponding to setting α in (39) to 1.5, 2, 3 and 4 respectively. Results obtained following our proposal appear to be less sensitive to the value of the duality gap used in IPM-LASSO. For instance, for the value $\lambda = \lambda _ { \mathrm { m a x } } / 1 0 0 0$ , the KKT rule returns 1758 active feature when the duality gap is set to $1 0 ^ { - 4 }$ while it returns 2357 features for a duality gap of $1 0 ^ { - 8 }$

## References

S.R. Becker, E.J. Candes, and M. Grant. Templates for convex cone problems with applications to sparse signal recovery. Stanford University Technical Report, 2010.

Stephen Boyd and Lieven Vandenberghe. Convex Optimization. Cambridge University Press, New York, NY, USA, 2004. ISBN 0521833787.

S.S. Chen, D.L. Donoho, and M.A. Saunders. Atomic decomposition by basis pursuit. SIAM review, 43:129, 2001.

David L. Donoho and Yaakov Tsaig. Fast solution of l\_1-norm minimization problems when the solution may be sparse. IEEE Trans. Inform. Theory, 54(11):4789–4812, 2008.

Bradley Efron, Trevor Hastie, Iain Johnstone, and Robert Tibshirani. Least angle regression (with discussion). Ann. Statist., 32:407–499, 2004.

Jianqing Fan and Jinchi Lv. Sure independence screening for ultrahigh dimensional feature space. J. Roy. Statist. Soc. Ser. B, 70(5):849–911, 2008.

Jianqing Fan and Jinchi Lv. A selective overview of variable selection in high dimensional feature space. Statist. Sinica, 20:101–148, 2010.

George Forman. An extensive empirical study of feature selection metrics for text classification. J. Mach. Learn. Res., 3:1289–1305, 2003.

A. Frank and A. Asuncion. UCI machine learning repository, 2010. URL http://archive.ics.uci.edu/ml.

Jerome Friedman, Trevor Hastie, Holger Höfling, and Robert Tibshirani. Pathwise coordinate optimization. Ann. Appl. Statist., 1(2):302–332, 2007.

Jerome Friedman, Trevor Hastie, and Robert Tibshirani. Regularization paths for generalized linear models via coordinate descent. Journal of Statistical Software, 33(1):1–22, 2010. URL http://www.jstatsoft.org/v33/i01/.

Brian Gawalt, Jinzhu Jia, Luke Miratrix, Laurent El Ghaoui, Bin Yu, and Sophie Clavier. Discovering word associations in news media via feature selection and sparse classification. In MIR ’10: Proceedings of the international conference on Multimedia information retrieval, pages 211–220, 2010.

Seung-Jean Kim, Kwangmoo Koh, Michael Lustig, Stephen Boyd, and Dimitry Gorinevsky. An interior-point method for large-scale l\_1-regularized least squares. IEEE J. Select. Top. Sign. Process., 1(4):606–617, 2007.

Kwangmoo Koh, Seung-Jean Kim, and Stephen Boyd. An interior-point method for large-scale l\_1-regularized logistic regression. JMLR, 8:1519–1555, 2007.

Mee Young Park and Trevor Hastie. L\_1-regularization path algorithm for generalized linear models. J. R. Stat. Soc. Ser. B Stat. Methodol., 69(4):659–677, 2007.

R. Tibshirani. Regression shrinkage and selection via the lasso. Journal of the Royal Statistical Society. Series B (Methodological), 58(1):267–288, 1996. ISSN 0035-9246.

A. Yang, A. Ganesh, Z. Zhou, S. Sastry, and Y. Ma. Fast l1-minimization algorithms and an application in robust face recognition: a review. University of California at Berkeley Technical report UCB/EECS-2010-13, 2010.