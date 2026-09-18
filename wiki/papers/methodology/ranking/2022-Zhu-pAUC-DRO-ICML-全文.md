---
title: "2022-Zhu-pAUC-DRO-ICML"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/ranking/2022-Zhu-pAUC-DRO-ICML.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# When AUC meets DRO: Optimizing Partial AUC for Deep Learning with Non-Convex Convergence Guarantee

Dixian Zhu <sup>\*</sup> <sup>1</sup> Gang Li <sup>\*</sup> <sup>1</sup> Bokun Wang <sup>1</sup> Xiaodong Wu <sup>2</sup> Tianbao Yang <sup>1</sup>

## Abstract

In this paper, we propose systematic and efficient gradient-based methods for both one-way and two-way partial AUC (pAUC) maximization that are applicable to deep learning. We propose new formulations of pAUC surrogate objectives by using the distributionally robust optimization (DRO) to define the loss for each individual positive data. We consider two formulations of DRO, one of which is based on conditionalvalue-at-risk (CVaR) that yields a non-smooth but exact estimator for pAUC, and another one is based on a KL divergence regularized DRO that yields an inexact but smooth (soft) estimator for pAUC. For both one-way and two-way pAUC maximization, we propose two algorithms and prove their convergence for optimizing their two formulations, respectively. Experiments demonstrate the effectiveness of the proposed algorithms for pAUC maximization for deep learning on various datasets. The proposed methods are implemented with tutorials in our open-sourced library LibAUC (www.libauc.org).

## 1. Introduction

AUC, short for the area under the ROC curve, is a performance measure of a model, where the ROC curve is a curve of true positive rate (TPR) vs false positive rate (FPR) for all possible thresholds. AUC maximization in machine learning has a long history dating back to early 2000s (Herbrich et al., 1999). It has four ages in the twenty-years history, full-batch based methods in the first age, online methods in the second age, stochastic methods in the third age, and deep learning methods in the recent age. The first three ages focus on learning linear models or kernelized models. In each age, there have been seminal works in rigorous optimization algorithms that play important roles in the evolution of AUC maximization methods. Recent advances in non-convex optimization (in particular non-convex min-max optimization) (Liu et al., 2020) has driven large-scale deep AUC maximization to succeed in real-world tasks, e.g., medical image classification (Yuan et al., 2020) and molecular properties prediction (Wang et al., 2021).

Nevertheless, the research on efficient optimization algorithms for partial AUC (pAUC) lag behind. In many applications, there are large monetary costs due to high false positive rates (FPR) and low true positive rates (TPR), e.g., in medical diagnosis. Hence, a measure of primary interest is the region of the curve corresponding to low FPR and/or high TPR, i.e., pAUC. There are two commonly used versions of pAUC, namely one-way pAUC (OPAUC) (Dodd & Pepe, 2003) and two-way pAUC (TPAUC) (Yang et al., 2019), where OPAUC puts a restriction on the range of FPR, i.e., FPR∈ [α, β] (Figure 1 middle) and TPAUC puts a restriction on the lower bound of TPR and the upper bound of FPR, i.e., TPR≥ α, FPR≤ β (Figure 1 right). Compared with standard AUC maximization, pAUC maximization is more challenging since its estimator based on training examples involves selection of examples whose prediction scores are in certain ranks.

To the best of our knowledge, there are few rigorous and efficient algorithms developed for pAUC maximization for deep learning. Some earlier works have focused on pAUC maximization for learning linear models. For example, Narasimhan & Agarwal (2017) have proposed a structured SVM approach for one-way pAUC maximization, which is guaranteed to converge for optimizing the surrogate objective of pAUC. However, their approach is not efficient for big data and is not applicable to deep learning, which needs to evaluate the prediction scores of all examples and sort them at each iteration. There are some heuristic approaches, e.g., updating the model parameters according to the gradient of surrogate pAUC computed based on a mini-batch data (Kar et al., 2014) or using an ad-hoc weighting function for each example for computing the stochastic gradient (Yang et al., 2021). However, such approaches are either not guaranteed to converge or could suffer a large approximation error.

![](images/1a601a693899efe773a86916554bac7b953e0662bf51a40836055186ab00bc3f.jpg)  
Figure 1. From left to right: AUC, one-way pAUC, two-way pAUC

In this paper, we propose more systematic and rigorous optimization algorithms for pAUC maximization with convergence guarantee, which are applicable to deep learning. We consider both OPAUC maximization and TPAUC maximization, where for OPAUC we focus on maximizing pAUC in the region where $\mathrm { F P R } \in [ 0 , \beta ]$ and for TPAUC we focus on maximizing $\mathsf { p A U C }$ in the region where $\mathrm { F P R } \le \beta$ and $\mathrm { T P R } \geq \alpha$ for some $\alpha , \beta \in ( 0 , 1 )$ . In order to tackle the challenge of computing unbiased stochastic gradients of the surrogate objective of pAUC, we propose new formulations based on distributionally robust optimization (DRO), which allows us to formulate the problem into weakly convex optimization, and novel compositional optimization problems, and to develop efficient stochastic algorithms with convergence guarantee. We summarize our contributions below.

imbalanced data. We compare with heuristic and adhoc approaches for pAUC maximization and multiple baseline methods, and observe superior performance of the proposed algorithms.

• For OPAUC maximization, for each positive example, we define a loss over all negative examples based on DRO. We consider two special formulations of DRO, with one based on the conditional-value-at-risk (CVaR) function that yields an exact estimator of the surrogate objective of OPAUC, and another one based on Kullback–Leibler (KL) divergence regularized DRO that yields a soft estimator of the surrogate objective.

• We propose efficient stochastic algorithms for optimizing both formulations of OPAUC and establish their convergence guarantee and complexities for finding a (nearly) stationary solution. We also demonstrate that the algorithm for optimizing the soft estimator based on the KL divergence regularized DRO can enjoy parallel speed-up.

• For TPAUC maximization, we apply another level of DRO with respect to the positive examples on top of OPAUC formulations, yielding both exact and soft estimators for TPAUC. We also provide two rigorous stochastic algorithms with provable convergence for optimizing both the exact and soft estimator of TPAUC, with the latter problem formulated as a novel threelevel compositional stochastic optimization problem.

• We conduct extensive experiments for deep learning on image classification and graph classification tasks with

To the best our knowledge, this work is the first one that provides rigorous stochastic algorithms and convergence guarantee for pAUC maximization that are efficient and applicable to deep learning. We expect the proposed novel formulations for OPAUC and TPAUC will allow researchers to develop even faster algorithms than the proposed algorithms in this paper.

## 2. Related Work

In this section, we provide a brief overview of related work for pAUC maximization.

Earlier works have considered indirect methods for pAUC maximization (Rudin, 2009; Agarwal, 2011; Rakotomamonjy, 2012; Li et al., 2014; Wu et al., 2008). They did not directly optimize the surrogate objective of pAUC but instead some objectives that have some relationship to the right corner of ROC curve, e.g., p-norm push (Rudin, 2009), infinite-push (Agarwal, 2011; Rakotomamonjy, 2012; Li et al., 2014), and asymmetric SVM objective (Wu et al., 2008). Nevertheless, none of these studies propose algorithms that are scalable and applicable for deep learning.

In (Kar et al., 2014), the authors proposed mini-batch based stochastic methods for pAUC maximization. At each iteration, a gradient estimator is simply computed based on the pAUC surrogate function of the mini-batch data. However, this heuristic approach is not guaranteed to converge for minimizing the pAUC objective and its error scales as $O ( 1 / { \sqrt { B } } )$ , where B is the mini-batch size. Narasimhan & Agarwal (2013b;a; 2017) developed rigorous algorithms for optimizing pAUC with FPR restricted in a range $( \alpha , \beta )$ based on the structured SVM formulation. However, their algorithms are only applicable to learning linear models and are not efficient for big data due to per-iteration costs proportional to the size of training data. Recently, Yang et al. (2021) considered optimizing two-way partial AUC with FPR less than $\beta$ and TPR larger than $\alpha .$ . Their paper focuses on simplifying the optimization problem that involves selection of top ranked negative examples and bottom ranked positive examples. They use ad-hoc weight functions for each positive and negative examples to relax the objective function into decomposable over pairs. The weight function is designed such that the larger the scores of negative examples the higher are their weights, the smaller the scores of positive examples the higher are their weights. Nevertheless, their objective function might have a large approximation error for the pAUC estimator.

There are also some studies about partial AUC maximization without providing rigorous convergence guarantee on their methods, including greedy methods (Wang & Chang, 2011; Ricamato & Tortorella, 2011) and boosting methods (Komori & Eguchi, 2010; Takenouchi et al., 2012). Some works also use pAUC maximization for learning non-linear neural networks (Ueda & Fujino, 2018; Iwata et al., 2020). However, it is unclear how the optimization algorithms were designed as there were no discussion on the algorithm design and convergence analysis. Finally, it was brought to our attention that a recent work (Yao et al., 2022) also considered partial AUC maximization with a non-convex objective. The difference between this work and (Yao et al., 2022) is that: (i) they focus on optimizing one-way pAUC with FPR in a certain range $( \alpha , \beta )$ where $\alpha > 0 ;$ ; in contrast we consider optimizing both one-way pAUC and two-way pAUC, but for one-way pAUC we only consider FPR in a range of $( 0 , \beta )$ ; (ii) the second difference is that the proposed algorithms in this paper for one-way pAUC maximization has a better complexity than that established in (Yao et al., 2022).

## 3. Preliminaries

In this section, we present some notations and preliminaries. Let ${ \cal { S } } = \{ ( { \bf { x } } _ { 1 } , y _ { 1 } ) , \dots , ( { \bf { x } } _ { n } , y _ { n } ) \}$ denote a set of training data, where $\mathbf { x } _ { i }$ represents an input training example (e.g., an image), and $\mathbf { y } _ { i } \in \{ 1 , - 1 \}$ denotes its corresponding label $( \mathrm { e . g . }$ , the indicator of a certain disease). Let $h _ { \mathbf { w } } ( \mathbf { x } ) =$ $h ( \mathbf { w } , \mathbf { x } )$ denote the score function of the neural network on an input data x, where $\mathbf { w } \in \mathbb { R } ^ { d }$ denotes the parameters of the network. Denote by $\mathbb { I } ( \cdot )$ an indicator function of a predicate, and by $[ s ] _ { + } = \operatorname* { m a x } ( s , 0 )$ . For a set of given training examples $s ,$ , let $S _ { + }$ and S be the subsets of $s$ with only positive and negative examples, respectively, with $n _ { + } = | S _ { + } |$ and $n _ { - } = | S _ { - } |$ . Let $\bar { S } ^ { \downarrow } [ k _ { 1 } , k _ { 2 } ] \subset S$ be the subset of examples whose rank in terms of their prediction scores in the descending order are in the range of $[ k _ { 1 } , k _ { 2 } ]$ where $k _ { 1 } \leq k _ { 2 }$ . Similarly, let $S ^ { \uparrow } [ k _ { 1 } , k _ { 2 } ] \subset \mathcal { \bar { S } }$ denote the subset of examples whose rank in terms of their prediction scores in the ascending order are in the range of $[ k _ { 1 } , k _ { 2 } ]$ where $k _ { 1 } ~ \leq ~ k _ { 2 }$ We denote by $\operatorname { E } _ { \mathbf { x } \sim s }$ the average over $\mathbf { x } \in S$ . Let $\mathbf { x } _ { + } \sim \mathbb { P } _ { + }$ denote a random positive example and $\smash { \mathbf { x } _ { - } \sim \mathbb { P } _ { - } }$ <sub>−</sub> denote a random negative example. We use $\Delta$ to denote a simplex of a proper dimension.

A function $F ( \mathbf { w } )$ is weakly convex if there exists $C > 0$ such that $\begin{array} { r } { F ( \mathbf { w } ) + \frac { C } { 2 } \| \mathbf { w } \| ^ { 2 } } \end{array}$ is a convex function. A function $F ( \mathbf { w } )$ is L-smooth if its gradient is Lipchitz continuous, i.e., $\| \nabla F ( \mathbf { w } ) - \nabla F ( \mathbf { w } ^ { \prime } ) \| \leq L \| \mathbf { w } - \mathbf { w } ^ { \prime } \|$

pAUC and its non-parametric estimator. For a given threshold t and a score function $h ( \cdot )$ , the TPR can be written as $\mathrm { T P R } ( t ) = \mathrm { P r } ( h ( \mathbf { x } ) \geq t | y = 1 )$ , and the FPR can be written as $\mathrm { F P R } ( t ) = \mathrm { P r } ( h ( \mathbf { x } ) > t | y = - 1 )$ . For a given $u \in [ 0 , 1 ]$ , let FPR $\mathbf { \Phi } ^ { - 1 } ( u ) \ : = \ : \operatorname* { i n f } \{ t \in \mathbb { R } \ : : \ : \mathrm { F P R } ( t ) \ : \leq \ : u \}$ and $\mathrm { T P R } ^ { - 1 } ( u ) \ = \ \operatorname* { i n f } \{ t \ \in \ \mathbb { R } \ : \ \mathrm { T P R } ( t ) \ \leq \ u \}$ The ROC curve defined as $\{ u , \mathsf { R O C } ( u ) \}$ , where $u \in [ 0 , 1 ]$ and $\mathrm { R O C } ( u ) = \mathrm { T P R } ( \mathrm { F P R } ^ { - 1 } ( u ) )$ . OPAUC (non-normalized) with FRP restricted in the range $\left( \alpha _ { 0 } , \alpha _ { 1 } \right)$ ) is equal to (Dodd & Pepe, 2003)

$$
\operatorname{OPAUC} (h, \alpha_ {0}, \alpha_ {1}) = \int_ {\alpha_ {0}} ^ {\alpha_ {1}} \operatorname{ROC} (u) d u =\tag{1}
$$

$$
\operatorname * {P r} (h (\mathbf {x} _ {+}) > h (\mathbf {x} _ {-}), h (\mathbf {x} _ {-}) \in [ \mathrm{FPR} ^ {- 1} (\alpha_ {1}), \mathrm{FPR} ^ {- 1} (\alpha_ {0}) ]).
$$

where $h ( \mathbf { x } _ { - } ) \in [ \mathrm { F P R } ^ { - 1 } ( \alpha _ { 1 } ) , \mathrm { F P R } ^ { - 1 } ( \alpha _ { 0 } ) ]$ means that only negative examples whose prediction scores are in certain quantiles are considered. As a result, we have the following non-parametric estimator of OPAUC:

$$
\begin{array}{l} \widehat {\mathrm{OPAUC}} (h, \alpha_ {0}, \alpha_ {1}) = \\ \frac {1}{n _ {+}} \frac {1}{n _ {-}} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} \sum_ {\mathbf {x} _ {j} \in \mathcal {S} _ {-} ^ {\downarrow} [ k _ {1} + 1, k _ {2} ]} \mathbb {I} (h (\mathbf {x} _ {i}) > h (\mathbf {x} _ {j})), \end{array}\tag{2}
$$

where $k _ { 1 } = { \lceil n _ { - } \alpha _ { 0 } \rceil } , k _ { 2 } = { \lfloor n _ { - } \alpha _ { 1 } \rfloor }$ . In this work, we will focus on optimizing ${ \widetilde { \mathrm { O P A U C } } } ( h , 0 , \beta )$ for some $\beta \in ( 0 , 1 )$ Similarly, a non-parametric estimator of TPAUC with FPR $\leq \beta , \mathrm { T P R } \geq \alpha$ is given by

$$
\widehat {\mathrm{TPAUC}} (h, \alpha , \beta) = \frac {1}{n _ {+}} \frac {1}{n _ {-}} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+} ^ {\uparrow} [ 1, k _ {1} ]} \sum_ {\mathbf {x} _ {j} \in \mathcal {S} _ {-} ^ {\downarrow} [ 1, k _ {2} ]} \mathbb {I} (h (\mathbf {x} _ {i}) > h (\mathbf {x} _ {j})), \tag {3}
$$

where $k _ { 1 } = \lfloor n _ { + } \alpha \rfloor , k _ { 2 } = \lfloor n _ { - } \beta \rfloor .$

Distributionally Robust Optimization (DRO). For a set of random loss functions $\ell _ { 1 } ( \cdot ) , \ldots , \ell _ { n } ( \cdot )$ , a DRO loss can be written as

$$
\hat {L} _ {\phi} (\cdot) = \max _ {\mathbf {p} \in \Delta} \sum_ {j} p _ {j} \ell_ {j} (\cdot) - \lambda D _ {\phi} (\mathbf {p}, 1 / n),\tag{4}
$$

where $\begin{array} { r } { D _ { \phi } ( \mathbf { p } , 1 / n ) = \frac { 1 } { n } \sum _ { i } \phi ( n p _ { i } ) } \end{array}$ is a divergence measure, and $\lambda > 0$ is a parameter. The idea of the DRO loss is to assign an importance weight $p _ { i }$ to each individual loss and take the uncertainty into account by maximization over $\mathbf { p } \in \Delta$ with a proper constraint/regularization on p. In the literature, several divergence measures have been considered (Levy et al., 2020). In this paper, we will consider two special divergence measures that are of most interest for our purpose, i.e., the KL divergence $\phi _ { k l } ( t ) = t \log t - t + 1$ , which gives $\begin{array} { r } { D _ { \phi } ( \mathbf { p } , 1 / n ) = \sum _ { i } p _ { i } } \end{array}$ log(np ), and the CVaR divergence $\phi _ { c } ( t ) = \mathbb { I } ( 0 < t \leq 1 / \gamma )$ with a parameter $\gamma \in ( 0 , 1 )$ , which gives $D _ { \phi } ( { \bf p } , 1 / n ) = 0 \mathrm { i f } p _ { i } \le 1 / ( n \gamma )$ and infinity otherwise. The following lemma gives the closed form of $\hat { L } _ { \phi }$ for $\phi _ { c }$ and $\phi _ { k l }$

Lemma 1. By using KL divergence measure, we have

$$
\hat {L} _ {k l} (\cdot ; \lambda) = \lambda \log \left(\frac {1}{n} \sum_ {i = 1} ^ {n} \exp \left(\frac {\ell_ {i} (\cdot)}{\lambda}\right)\right).\tag{5}
$$

By using the CVaR divergence $\phi _ { c } ( t )$ for some γ such that nγ is an integer, we have,

$$
\hat {L} _ {c v a r} (\cdot ; \gamma) = \frac {1}{n \gamma} \sum_ {i = 1} ^ {n \gamma} \ell_ {[ i ]} (\cdot),\tag{6}
$$

where $\ell _ { [ i ] } ( \cdot )$ denotes the i-th largest value in $\{ \ell _ { 1 } , \ldots , \ell _ { n } \}$

The estimator in (6) is also known as the estimator of conditional-value-at-risk (Rockafellar et al., 2000).

## 4. AUC meets DRO for OPAUC Maximization

Since the non-parametric estimator of OPAUC in (2) is noncontinuous and non-differentiable, a continuous surrogate objective for $\mathrm { O P A U C } ( h _ { \mathbf { w } } , 0 , \beta )$ is usually defined by using a continuous pairwise surrogate loss $L ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) =$ $\ell ( h _ { \mathbf { w } } ( \mathbf { x } _ { i } ) - h _ { \mathbf { w } } ( \mathbf { x } _ { j } ) )$ , resulting in the following problem:

$$
\min _ {\mathbf {w}} \frac {1}{n _ {+}} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} \frac {1}{n _ {-} \beta} \sum_ {\mathbf {x} _ {j} \in \mathcal {S} _ {-} ^ {\downarrow} [ 1, n _ {-} \beta ]} L (\mathbf {w}; \mathbf {x} _ {i}, \mathbf {x} _ {j}),\tag{7}
$$

where we assume $n _ { - } \beta$ is an positive integer for simplicity of presentation. For the surrogate loss $\ell ( \cdot )$ , we assume it satisfies the following properties.

Assumption 1. We assume $\ell ( \cdot )$ is a convex, differentiable and monotonically decreasingfunction when $\ell ( \cdot ) > 0 ,$ , and $\ell ^ { \prime } { \left( 0 \right) } < 0 .$

It is notable that the above condition is a sufficient condition to ensure that the surrogate $\ell ( \cdot )$ is consistent for AUC maximization (Gao & Zhou, 2015). There are many surrogate loss functions that have the above properties, $\mathrm { e . g . }$ , squared hinge loss $\ell ( s ) ~ = ~ ( c - s ) _ { + } ^ { 2 }$ , logistic loss $\ell ( s ) = \log ( 1 + \exp ( - s / c ) )$ where $c > 0$ is a parameter.

The challenge of optimizing a surrogate objective of pAUC in (7) lies at tackling the selection of top ranked negative examples from $\mathcal { S } _ { - } , \mathrm { i . e . , } \mathcal { S } _ { - } ^ { \downarrow } [ 1 , k ]$ for some fixed k. It is impossible to compute an unbiased stochastic gradient of the objective in (7) based on a mini-batch of examples that include only a part of negative examples.

## 4.1. AUC meets DRO for OPAUC

To address the above challenge, we define new formulations for OPAUC maximization by leveraging the DRO. In particular, we define a robust loss for each positive data by

$$
\hat {L} _ {\phi} (\mathbf {w}; \mathbf {x} _ {i}) = \max _ {\mathbf {p} \in \Delta} \sum_ {\mathbf {x} _ {j} \in \mathcal {S} _ {-}} p _ {j} L (\mathbf {w}; \mathbf {x} _ {i}, \mathbf {x} _ {j}) - \lambda D _ {\phi} (\mathbf {p}, 1 / n _ {-}).
$$

Then we define the following objective for OPAUC maximization:

$$
\min _ {\mathbf {w}} \frac {1}{n _ {+}} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} \hat {L} _ {\phi} (\mathbf {w}; \mathbf {x} _ {i}).\tag{8}
$$

When $\phi ( \cdot ) = \phi _ { c } ( \cdot )$ , we refer to the above estimator $( \mathrm { i . e . }$ the objective function) as CVaR-based OPAUC estimator; and when $\phi ( \cdot ) = \phi _ { k l } ( \cdot )$ , we refer to the above estimator as KLDRO-based OPAUC estimator. Below, we present two theorems to state the equivalent form of the objective, and the relationship between the two estimators and the surrogate objective in (7) of OPAUC.

Theorem 1. By choosing $\phi ( \cdot ) = \phi _ { c } ( \cdot ) = \mathbb { I } ( \cdot \in ( 0 , 1 / \beta ] )$ then the problem (8) is equivalent to

$$
\min _ {\mathbf {s} \in \mathbb {R} ^ {n +}} F (\mathbf {w}, \mathbf {s}) = \frac {1}{n _ {+}} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} \left(s _ {i} + \frac {1}{\beta} \psi_ {i} (\mathbf {w}, s _ {i})\right)\tag{9}
$$

where $\begin{array} { r } { \psi _ { i } ( \mathbf { w } , s _ { i } ) = \frac { 1 } { n _ { - } } \sum _ { \mathbf { x } _ { j } \in \mathcal { S } _ { - } } ( L ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) - s _ { i } ) _ { + } . \ I f \ell } \end{array}$ is a monotonically decreasing function for $\ell ( \cdot ) > 0$ , then the objective in (8) is equivalent to (7) of OPAUC.

Remark: The above theorem indicates that CVaR-based OPAUC estimator is an exact estimator of OPAUC, which is consistent for OPAUC maximization. The variable $s _ { i }$ can be considered as the threshold variable to select the top-ranked negative examples for each positive data.

Theorem 2. By choosing $\phi ( \cdot ) = \phi _ { k l } ( \cdot )$ , then the problem (8) becomes

$$
\min _ {\mathbf {w}} \frac {1}{n _ {+}} \sum_ {\mathbf {x} _ {i} \sim \mathcal {S} _ {+}} \lambda \log \mathrm{E} _ {\mathbf {x} _ {j} \in \mathcal {S} _ {-}} \exp (\frac {L (\mathbf {w} ; \mathbf {x} _ {i} , \mathbf {x} _ {j})}{\lambda}).\tag{10}
$$

$I f \ell ( \cdot )$ is a monotonically decreasing function for $\ell ( \cdot ) >$ 0, when $\lambda ~ = ~ 0 ,$ , the above objective is a surrogate of $\widehat { O P A U C } ( h _ { \mathbf { w } } , 0 , \frac { 1 } { n _ { - } } ) ;$ and when $\lambda = + \infty ,$ , the above objective is a surrogate of $\widehat { O P A U C } ( h _ { \mathbf { w } } , 0 , 1 )$ , i.e., the AUC.

Remark: Theorem 2 indicates that KLDRO-based OPAUC estimator is a soft estimator, which interpolates between $\mathrm { O P A U C } ( h _ { \mathbf { w } } , 0 , 1 / n _ { - } )$ and $\mathrm { O P A U C } ( h _ { \mathbf { w } } , 0 , 1 )$ by varying λ. It is also notable that when $\beta = 1 / n _ { - }$ in CVaR-based estimator, the objective in (8) becomes the infinite-push (or top-push) objective considered in the literature (Agarwal, 2011; Rakotomamonjy, 2012; Li et al., 2014), and hence our algorithm for solving (9) can be also used for solving the infinite-push objective for deep learning. In contrast, the previous works for the infinite-push objective focus on learning linear models. Similarly, when $\lambda = 0$ in KLDRObased estimator, the objective in (10) becomes the infinitepush objective. Nevertheless, our algorithm for optimizing KLDRO-based estimator is not exactly applicable to optimizing the infinite-push objective as we focus on the cases $\lambda > 0$ , which yields a smooth objective function under proper conditions of $\ell ( \cdot )$ and $h ( \cdot ; \mathbf { x } )$ . As a result, we could have stronger convergence by optimizing the KLDRO-based estimator as indicated by our convergence results in next subsection.

## 4.2. Optimization Algorithms and Convergence Results

In this subsection, we present the optimization algorithms for solving both (9) and (10), and then present their convergence results for finding a nearly stationary solution. The key to our development is to formulate the two optimization problems into known non-convex optimization problems that have been studied in the literature, and then to develop stochastic algorithms by borrowing the existing techniques.

Optimizing CVaR-based estimator. We first consider optimizing the CVaR-based estimator, which is equivalent to (9). A benefit for solving (9) is that an unbiased stochastic subgradient can be computed in terms of $\mathbf { \Psi } ( \mathbf { w } , \mathbf { s } )$ . However, this problem is still challenging because the objective function $F ( \mathbf { w } , \mathbf { s } )$ is non-smooth non-convex. In order to develop a stochastic algorithm with convergence guarantee, we prove that $F ( \mathbf { w } , \mathbf { s } )$ is weakly convex in terms of $( \mathbf { w } , \mathbf { s } )$ , which allows us to borrow the techniques of optimizing weakly convex function (Davis & Drusvyatskiy, 2018) for solving our problem and to establish the convergence. We first establish the weak convexity of $F ( \mathbf { w } , \mathbf { s } )$

Lemma 2. $I f L ( \cdot ; \mathbf { x } _ { i } , \mathbf { x } _ { j } )$ is a $L _ { s } .$ -smoothfunctionfor any $\mathbf { x } _ { i } , \mathbf { x } _ { j } ,$ , then $F ( \mathbf { w } , \mathbf { s } )$ is ρ-weakly convex with $\rho = L _ { s } / \beta .$

Another challenge for optimizing $F ( \mathbf { w } , \mathbf { s } )$ is that s is of high dimensionality and computing the gradient for all entries in s at each iteration is expensive. Therefore, we develop a tailored stochastic algorithm for solving (9), which is shown in Algorithm 1. This algorithm uses stochastic gradient descent (SGD) updates for updating w and stochastic coordinate gradient descent (SCGD) updates for updating s. We refer to the algorithm as SOPA. A key feature of SOPA is that the stochastic gradient estimator for w is a weighted average gradient of the pairwise losses for all pairs in the mini-batch, i.e., step 6. The hard weights $p _ { i j }$ (either 0 or 1) are dynamically computed by step 4, which compares the pairwise loss $( \ell ( h ( \mathbf { w } _ { t } , \mathbf { x } _ { i } ) - h ( \mathbf { w } _ { t } , \mathbf { x } _ { j } ) )$ with the threshold variable $s _ { i } ^ { t } ,$ which is also updated by a SGD step.

Optimizing KLDRO-based estimator of OPAUC. Next, we consider optimizing the KLDRO-based estimator, which is equivalent to (10). A nice property of the objective function is that it is smooth under a proper condition as stated in Assumption 2. However, the challenge for solving (10) is that an unbiased stochastic gradient is not readily computed. To highlight the issue, the problem (10) can be written as

$$
\min _ {\mathbf {w}} F (\mathbf {w}) = \frac {1}{n _ {+}} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} f (g _ {i} (\mathbf {w})),\tag{11}
$$

where $\begin{array} { r l r } { g _ { i } ( { \bf w } ) } & { { } = } & { { \mathrm E } _ { { \bf x } _ { j } \sim { \mathcal S } _ { - } } \exp ( \frac { L ( { \bf w } ; x _ { i } , { \bf x } _ { j } ) } { \lambda } ) } \end{array}$ and $\begin{array} { r l } { f ( \cdot ) } & { { } = } \end{array}$ $\lambda \log ( \cdot ) . \mathrm { ~ A ~ }$ similar optimization problem has been studied in (Qi et al., 2021) for maximizing average precision, which is referred to as finite-sum coupled compositional stochastic optimization, where $f ( g _ { i } ( \mathbf { w } ) )$ is a compositional function and $g _ { i } ( \mathbf { w } )$ depends on the index i for the outer summation. A full gradient of $f ( g _ { i } ( \mathbf { w } ) )$ is given by $f ^ { \prime } ( g _ { i } ( \mathbf { w } ) ) \nabla g _ { i } ( \mathbf { w } )$ With a mini-batch of samples, $g _ { i } ( \mathbf { w } )$ can be estimated by an unbiased estimator $\hat { g } _ { i } ( \mathbf { w } )$ . However, $f ^ { \prime } ( \hat { g } _ { i } ( \mathbf { w } ) ) \nabla \hat { g } _ { i } ( \mathbf { w } )$ is a biased estimator due to the compositional form. To address this challenge, Qi et al. (2021) proposed a novel stochastic algorithm that maintains a moving average estimator for $g _ { i } ( \mathbf { w } )$ denoted by $u _ { i } .$ Recently, Wang & Yang (2022) has also studied the finite-sum coupled compositional optimization problem comprehensively and proposed a similar algorithm (SOX) and derived better convergence results than that in (Qi et al., 2021). Hence, we employ the same algorithm in (Wang & Yang, 2022) for solving (10), which is in shown in Algorithm 2 and is referred to as SOPA-s.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 SOPA
1: Set $s^1 = 0$ and initialize w
2: for $t = 1, \ldots, T$ do
3:    Sample two mini-batches $\mathcal{B}_+ \subset \mathcal{S}_+, \mathcal{B}_- \subset \mathcal{S}_-$
4:    Let $p_{ij} = \mathbb{I}(\ell(h(\mathbf{w}_t, \mathbf{x}_i) - h(\mathbf{w}_t, \mathbf{x}_j)) - s_i^t &gt; 0)$
5:    Update $s_i^{t+1} = s_i^t - \frac{\eta_2}{n_+}(1 - \frac{\sum_j p_{ij}}{\beta|\mathcal{B}_-|})$ for $\mathbf{x}_i \in \mathcal{B}_+$
6:    Compute a gradient estimator $\nabla_t$ by
$\nabla_t = \frac{1}{\beta|\mathcal{B}_+||\mathcal{B}_-|} \sum_{\mathbf{x}_i \in \mathcal{B}_+} \sum_{\mathbf{x}_j \in \mathcal{B}_-} p_{ij} \nabla_{\mathbf{w}} L(\mathbf{w}_t; \mathbf{x}_i, \mathbf{x}_j)$
7:    Update $\mathbf{w}_{t+1} = \mathbf{w}_t - \eta_1 \nabla_t$
8: end for
</div>

There are two key differences between SOPA-s and SOPA. First, the pairwise weights $p _ { i j }$ in SOPA-s (step 5) are soft weights between 0 and 1, in contrast to the hard weights $p _ { i j } \in \{ 0 , 1 \}$ in SOPA. Second, the update for $\mathbf { w } _ { t + 1 }$ is a momentum-based update where $\gamma _ { 1 } \in ( 0 , 1 )$ . We can also use an Adam-style update, which shares similar convergence as the momentum-based update (Guo et al., 2021).

## 4.3. Convergence Analysis

For convergence analysis, we make the following assumption about h and ℓ(·).

Assumption 2. Assume $h ( \cdot ; \mathbf { x } )$ is Lipschitz continuous, smooth and bounded, $\ell ( \cdot )$ is a smooth function and has a bounded gradient for a bounded argument.

A bounded smooth score function $h ( \cdot ; \mathbf { x } )$ is ensured if the activation function of the neural network is smooth and the output layer uses a bounded and smooth activation function. For example, let $\hat { h } ( \mathbf { w } ; \mathbf { x } )$ denote the plain output of the neural network, then the score function $h ( \mathbf { w } ; \mathbf { x } ) =$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 SOPA-s
1: Set $\mathbf{u}^1 = 0$ and initialize $\mathbf{w}$
2: for $t = 1, \ldots, T$ do
3:    Sample two mini-batches $\mathcal{B}_+ \subset \mathcal{S}_+, \mathcal{B}_- \subset \mathcal{S}_-$
4:    For each $\mathbf{x}_i \in \mathcal{B}_+$, update $u_i^{t+1} = (1 - \gamma_0) u_i^t + \gamma_0 \frac{1}{|\mathcal{B}_-|} \sum_{\mathbf{x}_j \in \mathcal{B}_-} \exp\left(\frac{L(\mathbf{w}_t; \mathbf{x}_i, \mathbf{x}_j)}{\lambda}\right)$
5:    Let $p_{ij} = \exp(L(\mathbf{w}_t; \mathbf{x}_i, \mathbf{x}_j)/\lambda)/u_i^t$
6:    Compute a gradient estimator $\nabla_t$ by
$\nabla_t = \frac{1}{|\mathcal{B}_+|} \frac{1}{|\mathcal{B}_-|} \sum_{\mathbf{x}_i \in \mathcal{B}_+} \sum_{\mathbf{x}_j \in \mathcal{B}_-} p_{ij} \nabla L(\mathbf{w}_t; \mathbf{x}_i, \mathbf{x}_j)$
7:    Update $\mathbf{v}_t = (1 - \gamma_1) \mathbf{v}_{t-1} + \gamma_1 \nabla_t$
8:    Update $\mathbf{w}_{t+1} = \mathbf{w}_t - \eta \mathbf{v}_t$ (or Adam-style)
9: end for
</div>

$1 / ( 1 + \exp ( - \hat { h } ( \mathbf { w } ; \mathbf { x } ) )$ is bounded and smooth. The Lipschitz continuity of $h ( \mathbf { w } ; \mathbf { x } )$ can be guaranteed if w is bounded.

We first consider the analysis of SOPA. Since $F ( \mathbf { w } , \mathbf { s } )$ is non-smooth, for presenting the convergence result, we need to introduce a convergence measure based on the Moreau envelope of $F ( \mathbf { w } , \mathbf { s } )$ given below for some ${ \hat { \rho } } > \rho \colon$

$$
F _ {\hat {\rho}} (\mathbf {w}, \mathbf {s}) = \min _ {\mathbf {w}, \mathbf {s}} F (\mathbf {w}, \mathbf {s}) + \frac {\hat {\rho}}{2} (\| \mathbf {w} \| ^ {2} + \| \mathbf {s} \| ^ {2}).
$$

It is guaranteed that $F _ { \hat { \rho } } ( \mathbf { w } , \mathbf { s } )$ is a smooth function (Drusvyatskiy & Paquette, 2019). A point $( \mathbf { w } , \mathbf { s } )$ is called an ϵ- nearly stationary solution to $F ( \mathbf { w } , \mathbf { s } )$ if $\| \nabla F _ { \hat { \rho } } ( \mathbf { w } , \mathbf { s } ) \| \leq \epsilon$ for some $\hat { \rho } > \rho ,$ where $\rho$ is the weak convexity parameter of $F .$ . This convergence measure has been widely used for weakly convex optimization problems (Davis & Drusvyatskiy, 2018; Rafique et al., 2020; Chen et al., 2019). Then we establish the following convergence guarantee for SOPA.

Theorem 3. Under Assumption 2, Algorithm 1 ensures that after $T = { \cal O } ( 1 / ( \beta \epsilon ^ { 4 } ) )$ ) iterations we can find an ϵ nearly stationary solution of $F ( \mathbf { w } , \mathbf { s } )$ , i.e., $\begin{array} { r } { \mathrm { E } \| \nabla F _ { \hat { \rho } } ( \mathbf { w } _ { \tau } , \mathbf { s } _ { \tau } ) \| ^ { 2 } \leq } \end{array}$ $\epsilon ^ { 2 }$ for a randomly selected $\tau \in \{ 1 , \ldots , T \}$ and $\hat { \rho } = 1 . 5 \rho .$

Next, we establish the convergence of SOPA-s. Under ${ \bf A } { \bf s } -$ sumption 2, we can show that $F ( \mathbf { w } )$ in (11) is smooth. Hence, we use the standard convergence measure in terms of gradient norm of $F ( \mathbf { w } )$

Theorem 4. Under Assumption 2, Algorithm 2 with $\begin{array} { r c l r c l } { { \gamma _ { 0 } } } & { { = } } & { { O ( B _ { - } \epsilon ^ { 2 } ) , } } & { { \gamma _ { 1 } } } & { { = } } & { { O ( \mathrm { m i n } \{ B _ { - } , B _ { + } \} \epsilon ^ { 2 } ) , } } \end{array}$ $\begin{array} { r l r } { \eta } & { { } = } & { O ( \operatorname* { m i n } \{ \gamma _ { 0 } B _ { 1 } / n _ { + } , \gamma _ { 1 } \} ) } \end{array}$ ensures that after $\begin{array} { r } { T = O ( \frac { 1 } { \operatorname* { m i n } ( B _ { + } , B _ { - } ) \epsilon ^ { 4 } } + \frac { n _ { + } } { B _ { + } B _ { - } \epsilon ^ { 4 } } ) } \end{array}$ iterations we canfind an ϵ-stationary solution of $F ( \mathbf { w } ) , i . e .$ $\begin{array} { r } { \mathrm { E } [ \| \nabla F ( \mathbf { w } _ { \tau } ) \| ^ { 2 } ] \leq \epsilon ^ { 2 } } \end{array}$ for a randomly selected $\tau \in \{ 1 , \ldots , T \}$ , where $B _ { + } = | \boldsymbol { B } _ { + } |$ and $B _ { - } = | \boldsymbol { B } _ { - } | .$

Remark: The convergence analysis of Algorithm 2 follows directly from that in (Wang & Yang, 2022). Compared with that in Theorem 3 for SOPA, the convergence of SOPA-s is stronger than that of SOPA in several aspects: (i) the convergence measure of SOPA-s is stronger than that of SOPA due to that Theorem 4 guarantees the convergence in terms of gradient norm of the objective, while Theorem 3 guarantees the convergence on a weaker convergence measure namely the gradient norm of the Moreau envelope of the objective; (ii) the complexity of SOPA-s enjoys a parallel speed-up by using a mini-batch of data. However, it is also notable that the complexity of SOPA does not depend on the number of positive data as that of SOPA-s.

## 5. AUC meets DRO for TPAUC Maximization

In this section, we propose estimators for the surrogate objective of TPAUC and stochastic algorithms with convergence guarantee for optimizing the estimators. To this end, we apply another level of DRO on top of $\hat { L } _ { \phi } ( \mathbf { x } _ { i } , \mathbf { w } ) , \mathbf { x } _ { i } \in$ $S _ { + }$ and define the following estimator of TPAUC:

$$
F (\mathbf {w}; \phi , \phi^ {\prime}) = \max _ {\mathbf {p} \in \Delta} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} p _ {i} \hat {L} _ {\phi} (\mathbf {x} _ {i}, \mathbf {w}) - \lambda^ {\prime} D _ {\phi^ {\prime}} (\mathbf {p}, \frac {1}{n _ {+}}).
$$

Next, we focus on optimizing the soft estimator of TPAUC defined by using $\phi = \phi ^ { \prime } = \phi _ { k l }$ . First, we have the following form for the estimator.

Lemma 3. When $\phi = \phi ^ { \prime } = \phi _ { k l }$ , we have

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
$F(\mathbf{w};\phi_{kl},\phi_{kl})$ $= \lambda^{\prime}\log \mathrm{E}_{\mathbf{x}_i\sim \mathcal{S}_+}\left(\mathrm{E}_{\mathbf{x}_j\sim \mathcal{S}_-}\exp (\frac{\ell(\mathbf{w};\mathbf{x}_i,\mathbf{x}_j)}{\lambda})\right)^{\frac{\lambda}{\lambda'}}.$
</div>

For minimizing this function, we formulate the problem as a novel three-level compositional stochastic optimization:

$$
\min _ {\mathbf {w}} f _ {1} (\frac {1}{n _ {+}} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} f _ {2} (g _ {i} (\mathbf {w}))),
$$

where $f _ { 1 } ( s ) = \lambda ^ { \prime } \log ( s ) , f _ { 2 } ( g ) = g ^ { \lambda / \lambda ^ { \prime } }$ and $g _ { i } ( \mathbf { w } ) \ =$ $\mathrm { E } _ { { \bf x } _ { j } \sim { \cal S } _ { - } } \exp ( L ( { \bf w } ; { \bf x } _ { i } , { \bf x } _ { j } ) / \lambda )$ . We propose a novel stochastic algorithm for solving the above problem, which is shown in Algorithm $^ { 3 , }$ to which we refer as SOTAs. Note that the problem is similar to multi-level compositional optimization (Balasubramanian et al., 2021) but also has subtle difference. The function inside $f _ { 1 }$ has a form similar to that in (11). Hence, we use similar technique to SOPA-s by maintaining and updating $u ^ { i }$ to track $g _ { i } ( \mathbf { w } )$ in step 4. Besides, we need to maintain and update $v _ { t + 1 }$ <sub>1</sub> to track $\begin{array} { r } { \frac { 1 } { n _ { + } } \sum _ { \mathbf { x } _ { i } \in \mathcal { S } _ { + } } f _ { 2 } ( g _ { i } ( \mathbf { w } _ { t } ) ) } \end{array}$ in step 5. Then the gradient estimator in step 7 is computed by $\begin{array} { r } { \nabla f _ { 1 } ( v _ { t + 1 } ) \frac { 1 } { | \mathcal { B } _ { + } | } \sum _ { \mathbf { x } _ { i } \in \mathcal { B } _ { + } } \nabla \hat { g } _ { i } ( \mathbf { w } _ { t } ) \nabla \bar { f } _ { 2 } ( u _ { t } ^ { i } ) } \end{array}$ where $\hat { g } _ { i } ( \mathbf { w } ) = \mathrm { E } _ { \mathbf { x } _ { j } \sim \mathcal { B } _ { - } } \exp ( L ( \mathbf { w } _ { t } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) / \lambda )$ . Then we update the model parameter by the momentum-style or Adam-style update.

Theorem 5. Under Assumption 2, Algorithm 3 with $\gamma _ { 0 } =$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3 SOTA-s
1: Set $\mathbf{u}_0 = 0, v_0 = 0, \mathbf{m}_0 = 0$ and initialize $\mathbf{w}$
2: for $t = 1, \ldots, T$ do
3: Sample two mini-batches $\mathcal{B}_+ \subset \mathcal{S}_+, \mathcal{B}_- \subset \mathcal{S}_-$
4: For each $\mathbf{x}_i \in \mathcal{B}_+$ compute $u_t^i = (1 - \gamma_0) u_{t-1}^i + \gamma_0 \frac{1}{|B_-|} \sum_{\mathbf{x}_j \in \mathcal{B}_-} L(\mathbf{w}_t; \mathbf{x}_i, \mathbf{x}_j)$
5: Let $v_t = (1 - \gamma_1) v_{t-1} + \gamma_1 \frac{1}{|\mathcal{B}_+|} \sum_{\mathbf{x}_i \in \mathcal{B}_+} f_2(u_{t-1}^i)$
6: Let $p_{ij} = (u_{t-1}^i)^{\lambda/\lambda'-1} \exp(L(\mathbf{w}_t, \mathbf{x}_i, \mathbf{x}_j)/\lambda)/v_t$
7: Compute a gradient estimator $\nabla_t$ by
$\nabla_t = \frac{1}{|\mathcal{B}_+} \frac{1}{|\mathcal{B}_-|} \sum_{\mathbf{x}_i \in \mathcal{B}_+} \sum_{\mathbf{x}_j \in \mathcal{B}_-} p_{ij} \nabla L(\mathbf{w}_t; \mathbf{x}_i, \mathbf{x}_j)$
8: Update $\mathbf{m}_t = (1 - \gamma_2) \mathbf{m}_{t-1} + \gamma_2 \nabla_t$
9: Update $\mathbf{w}_{t+1} = \mathbf{w}_t - \eta \mathbf{m}_t$ (or Adam-style)
10: end for
</div>

$O ( B _ { - } \epsilon ^ { 2 } ) , \ \gamma _ { 1 } \ = \ O ( B _ { + } \epsilon ^ { 2 } ) , \ \gamma _ { 2 } \ = \ O ( \operatorname * { m i n } \{ B _ { - } , B _ { + } \} \epsilon ^ { 2 } )$ $\eta \ = \ O ( \operatorname* { m i n } \{ \gamma _ { 0 } B _ { 1 } / n _ { + } , \gamma _ { 1 } , \gamma _ { 2 } \} )$ ensures that $a f t e r \ T \ =$ $\begin{array} { r } { O ( \frac { 1 } { \operatorname* { m i n } ( B _ { + } , B _ { - } ) \epsilon ^ { 4 } } + \frac { n _ { + } } { B _ { + } B _ { - } \epsilon ^ { 4 } } ) } \end{array}$ iterations we can find an ϵ nearly stationary solution of $F ( \mathbf { w } )$ , where $B _ { + } = | \boldsymbol { B } _ { + } |$ and $B _ { - } = | \boldsymbol { B } _ { - } | .$

Remark: It is notable that SOTA-s has an iteration complexity in the same order of SOPA-s for OPAUC maximization.

Finally, we discuss how to optimize the exact estimator of TPAUC defined by $F ( \mathbf { w } ; \phi _ { c } , \phi _ { c } ^ { \prime } )$ , where $\phi _ { c } ( t ) = \mathbb { I } ( 0 \leq t \leq$ $1 / \beta )$ and $\phi _ { c } ^ { \prime } ( t ) = \mathbb { I } ( 0 \leq t \leq 1 / \alpha )$ with $K _ { 2 } = n _ { - } \beta$ and $K _ { 1 } = n _ { + } \alpha$ being integers. Lemma 7 in the supplement shows that if $\ell ( \cdot )$ is monotonically decreasing for $\ell ( \cdot ) > 0$

$$
\begin{array}{l} F (\mathbf {w}; \phi_ {c}, \phi_ {c} ^ {\prime}) = \\ \frac {1}{K _ {1} K _ {2}} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+} ^ {\uparrow} [ 1, K _ {1} ]} \sum_ {\mathbf {x} _ {j} \in \mathcal {S} _ {-} ^ {\downarrow} [ 1, K _ {2} ]} L (\mathbf {w}; \mathbf {x} _ {i}, \mathbf {x} _ {j}), \end{array}
$$

is a consistent surrogate function of TPAUC for $\mathrm { T P R } \geq \alpha$ and $\mathrm { F P R } \le \beta$ in view of the estimator TPAUC given in (<sup>\</sup> 3). Similar to Theorem 1, we can show that $F ( \mathbf { w } ; \phi _ { c } , \phi _ { c } ^ { \prime } )$ is equivalent to:

$$
\min _ {s ^ {\prime} \in \mathbb {R}, \mathbf {s} \in \mathbb {R} ^ {n +}} s ^ {\prime} + \frac {1}{n _ {+} \alpha} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} (s _ {i} + \frac {1}{\beta} \psi_ {i} (\mathbf {w}; s _ {i}) - s ^ {\prime}) _ {+}.
$$

Like $F ( \mathbf { w } , \mathbf { s } )$ in (9), we can prove the inner function is weakly convex in terms of $( \mathbf { w } , \mathbf { s } , s ^ { \prime } )$ . However, computing an unbiased stochastic gradient in terms of w and $s _ { i }$ is also impossible due to that $\psi _ { i } ( \mathbf { w } ; s _ { i } )$ is inside a hinge function. To solve this problem, we can use the conjugate form of the hinge function to convert the minimization of $F ( \mathbf { w } ; \phi _ { c } , \phi _ { c } ^ { \prime } )$ into a weakly-convex concave min-max problem (Rafique et al., 2020) and we can develop a stochastic algorithm but only with ${ \cal O } ( 1 / \epsilon ^ { 6 } )$ iteration complexity for finding a nearly stationary solution. We present the algorithm and analysis in the supplement for interested readers.

## 6. Experiments

Datasets. We consider binary classification tasks on two types of datasets, namely image datasets and molecular datasets. For image datasets, we use CIFAR-10, CIFAR-100, Melanoma for experiments. For CIFAR-10 and CIFAR-100 (Krizhevsky et al., 2009), we construct imbalanced versions of the datasets by randomly removing some positive samples following (Yuan et al., 2020). Specifically, we take first half of classes as the negative class and last half of classes as the positive class, and then remove 80% samples from the positive class to make it imbalanced. The Melanoma dataset is a naturally imbalanced medical dataset which is released on Kaggle (Rotemberg et al., 2021). For molecular datasets, we use ogbg-moltox21 (the No.0 target), ogbg-molmuv (the No.1 target) and ogbg-molpbca (the No.0 target) for experiments, which are from the Stanford Open Graph Benchmark (OGB) website (Hu et al., 2020). The task on these molecular datasets is to predict certain property of molecules. The statistics for the datasets are presented in Table 5 in the supplement.

Deep Models. For image datasets, we learn convolutional neural network (CNN) and use ResNet18 (He et al., 2016) for CIFAR-10, CIFAR100 and Melanoma. For molecular datasets, we learn graph neural network (GNN) and use Graph Isomorphism Network (GIN) as the backbone model on all datasets (Xu et al., 2018), which has 5 mean-pooling layers with 64 number of hidden units and dropout rate 0.5.

Baselines. We will compare our methods with different baselines for both training performance and testing performance. For comparison of training convergence, we consider different methods for optimizing the same objective, i.e., partial AUC. We compare with 2 baselines, i.e., the naive mini-batch based method (Kar et al., 2014), to which we refer as MB, and a recently proposed ad-hoc weight based method (Yang et al., 2021), to which we refer as AWpoly. MB that optimizes OPAUC only considers the top negative samples in the mini-batch; and MB that optimizes TPAUC considers the top negative samples and bottom positive samples in the mini-batch. For AW-poly, we use the polynomial weight function according to their paper. It is notable that AW-poly was originally proposed for optimizing TPAUC. But it can be easily modified for optimizing OPAUC with FPR in $( 0 , \beta )$ . For comparison of testing performance, we compare different methods for optimizing different objectives, including the cross-entropy loss (CE), the pair-wise squared hinge loss for AUC maximization (AUC-SH), the AUC min-max margin loss (AUC-M) (Yuan et al., 2021), p-norm push (P-push) (Rudin, 2009). For optimizing CE and AUC-SH, we use the standard Adam optimizer. For optimizing AUC-M, we use their proposed optimizer PESG. For P-push, we use a stochastic algorithm with an Adam-style update similar to that proposed in (Qi et al., 2021). For our methods, we use $\ell ( t ) = ( 1 - t ) _ { + } ^ { 2 }$ and also use the Adam-style update unless specified explicitly. Similar to (Yuan et al., 2021; Qi et al., 2021), we use a pretraining step that optimizes the base model by optimizing CE loss with an Adam optimizer, and then re-initialize the classifier layer and fine-tune all layers by different methods.

![](images/f85d2ef27e19bfb3f8e2a2846051131c4c9d57ed575ee15be623ed6c91fa154c.jpg)  
Figure 2. Training Convergence Curves on image and molecular datasets; Top for OPAUC maximization, bottom for TPAUC maximization.

Target Measures. For OPAUC maximization, we evaluate OPAUC with two FPR upper bounds, i.e., $\mathrm { F P R \le 0 . 3 }$ and $\mathrm { F P R } \leq 0 . 5$ separately. For TPAUC maximization, we evaluate TPAUC with two settings, i.e, $\mathrm { F P R \le 0 . 4 }$ and $\mathrm { T P R } \geq 0 . 6$ and $\mathrm { F P R } \leq 0 . 5$ and $\mathrm { T P R } \geq 0 . 5$

Parameter Tuning. The learning rate of all methods is tuned in {1e-3, 1e-4, 1e-5}, except for PESG which is tuned at {1e-1, 1e-2, 1e-3} because it favors a larger learning rate. Weight decay is fixed as $2 \mathrm { e } { \cdot } 4 .$ . Each method is run 60 epochs in total and learning rate decays 10-fold after every 20 epochs. The mini-batch size is 64. For AUC-M, we tune the hyperparameter γ that controls consecutive epochregularization in {100, 500, 1000}. For P-push, we tune the polynomial power hyper-parameter in {2, 4, 6}. For MB that optimizes OPAUC, we tune the top proportion of negative samples in {10%, 30%, 50%}, and for MB that optimizes TPAUC we tune the top proportion of negative samples in {30%, 40%, 50%}, and tune the bottom proportion of positive samples in the range {30%, 40%, 50%}. For AW-poly, we follow (Yang et al., 2021) and tune its parameter γ in {101, 34, 11}. For SOPA, we tune the truncated FPR i.e. $\beta$ in {0.1, 0.3, 0.5}. For SOPA-s, we fix $\gamma _ { 0 } = 0 . 9$ and tune the KL-regularization parameter λ in {0.1, 1.0, 10}, and for SOTA-s, we fix $\gamma _ { 0 } = \gamma _ { 1 } = 0 . 9$ , and tune both λ and $\lambda ^ { \prime }$ in {0.1, 1.0, 10}. The momentum parameter for updating $\mathbf { v } _ { t }$ in $\mathrm { S O P A - s } \left( \mathrm { i . e . , 1 - \gamma _ { 1 } } \right)$ and $\mathrm { S O T A - s } \left( \mathrm { i . e . , 1 - \gamma _ { 2 } } \right)$ is set to the default value as in the Adam optimizer, i.e., 0.1. For comparison of training convergence, the parameters are tuned according to the training performance. For comparison of testing performance, the parameters are tuned according to the validation performance. For each experiment, we repeat multiple times with different train/validation splits and random seeds, then report average and standard deviation over multiple runs.

Results. We show the plots of training convergence in Figure 2 on two image datasets (CIFAR-10, -100) and on two molecular datasets (moltox21, molpcba). From the results, we can see that SOPA-s (SOTA-s) converge always faster than MB and AW-poly for OPAUC (TPAUC) maximization. For OPAUC maximization, SOPA-s is usually faster than SOPA. More results are included in the supplement on other datasets with similar observations. The testing performance on all six datasets are shown in Table 1, 2, 3 and 4. In most cases, the proposed methods are better than the baselines. In particular, dramatic improvements have been observed on Melanoma and ogbg-molmuv datasets, which are two datasets with the highest imbalance ratios. In addition, we see that AUC maximization methods (AUC-M, AUC-SH) are not necessarily good for pAUC maximization.

Accuracy of KLDRO-based estimator. Of independent interest, we conduct simple experiments to verify the accuracy of KLDRO-based estimator of OPAUC. To this end, we compute the relative error (RE) of KLDRO-based estimator compared with the exact estimator (i.e., CVaR-based estimator). For a given upper bound of FRP we vary λ for 100 independently randomly generated model parameters w, and the results are shown in the following figure on moltox21-t0 data (please refer to the experiments section for more information of the dataset), which demonstrates that for a given FPR there exists λ such that KLDRO estimator is close to the exact estimator.

Ablation Study. We also conduct some ablation study to understand the proposed algorithm SOPA-s and SOTA-s. In particular for both algorithms, we verify that tuning $\gamma _ { 0 }$ in SOPA-s and $\gamma _ { 0 } , \gamma _ { 1 }$ in SOTA-s can help further improve the performance. The results are included in the supplement.

Table 1. One way partial AUC on testing data of three image datasets

<table><tr><td></td><td colspan="2">CIFAR-10</td><td colspan="2">CIFAR-100</td><td colspan="2">Melanoma</td></tr><tr><td>Methods</td><td>FPR≤0.3</td><td>FPR≤0.5</td><td>FPR≤0.3</td><td>FPR≤0.5</td><td>FPR≤0.3</td><td>FPR≤0.5</td></tr><tr><td>CE</td><td>0.8446(0.0018)</td><td>0.8777(0.0014)</td><td>0.7338(0.0047)</td><td>0.7787(0.0044)</td><td>0.7651(0.0135)</td><td>0.8151(0.0028)</td></tr><tr><td>AUC-SH</td><td>0.8657(0.0056)</td><td>0.8948(0.0036)</td><td>0.7467(0.0047)</td><td>0.7930(0.0027)</td><td>0.7824(0.0138)</td><td>0.8176(0.0160)</td></tr><tr><td>AUC-M</td><td>0.8678(0.0016)</td><td>0.8934(0.0022)</td><td>0.7371(0.0031)</td><td>0.7828(0.0005)</td><td>0.7788(0.0068)</td><td>0.8249(0.0141)</td></tr><tr><td>P-push</td><td>0.8610(0.0007)</td><td>0.8889(0.0021)</td><td>0.7445(0.0025)</td><td>0.7930(0.0029)</td><td>0.7440(0.0130)</td><td>0.8028(0.0170)</td></tr><tr><td>MB</td><td>0.8690(0.0016)</td><td>0.8931(0.0015)</td><td>0.7487(0.0017)</td><td>0.7930(0.0014)</td><td>0.7683(0.0303)</td><td>0.8184(0.0278)</td></tr><tr><td>AW-poly</td><td>0.8664(0.0052)</td><td>0.8915(0.0075)</td><td>0.7490(0.0058)</td><td>0.7909(0.0068)</td><td>0.7936(0.0238)</td><td>0.8355(0.0067)</td></tr><tr><td>SOPA</td><td>0.8766(0.0034)</td><td>0.9028(0.0031)</td><td>0.7551(0.0044)</td><td>0.7999(0.0028)</td><td>0.8093(0.0248)</td><td>0.8585(0.0210)</td></tr><tr><td>SOPA-s</td><td>0.8691(0.0036)</td><td>0.8961(0.0036)</td><td>0.7468(0.0056)</td><td>0.7877(0.0053)</td><td>0.7775(0.0076)</td><td>0.8401(0.0206)</td></tr></table>

Table 2. Two way partial AUC on testing data of three image datasets; $( \alpha , \beta )$ represents TPR≥ α and $\mathrm { F P R } \leq \beta .$

<table><tr><td></td><td colspan="2">CIFAR-10</td><td colspan="2">CIFAR-100</td><td colspan="2">Melanoma</td></tr><tr><td>Methods</td><td>(0.6,0.4)</td><td>(0.5,0.5)</td><td>(0.6,0.4)</td><td>(0.5,0.5)</td><td>(0.6,0.4)</td><td>(0.5,0.5)</td></tr><tr><td>CE</td><td>0.4981(0.0078)</td><td>0.6414(0.0080)</td><td>0.2178(0.0136)</td><td>0.4011(0.0118)</td><td>0.3399(0.0135)</td><td>0.5150(0.0038)</td></tr><tr><td>AUC-SH</td><td>0.5622(0.0064)</td><td>0.6923(0.0071)</td><td>0.2599(0.0061)</td><td>0.4397(0.0062)</td><td>0.3640(0.0354)</td><td>0.5291(0.0312)</td></tr><tr><td>AUC-M</td><td>0.5691(0.0021)</td><td>0.6907(0.0125)</td><td>0.2336(0.0041)</td><td>0.4153(0.0022)</td><td>0.3665(0.0646)</td><td>0.5404(0.0545)</td></tr><tr><td>P-push</td><td>0.5477(0.0077)</td><td>0.6781(0.0055)</td><td>0.2623(0.0042)</td><td>0.4417(0.0092)</td><td>0.3317(0.0304)</td><td>0.4870(0.0443)</td></tr><tr><td>MB</td><td>0.5404(0.0041)</td><td>0.6724(0.0011)</td><td>0.2207(0.0033)</td><td>0.4017(0.0149)</td><td>0.3330(0.0258)</td><td>0.4981(0.0252)</td></tr><tr><td>AW-poly</td><td>0.5536(0.0196)</td><td>0.6814(0.0203)</td><td>0.2489(0.0166)</td><td>0.4342(0.0112)</td><td>0.3878(0.0292)</td><td>0.5216(0.0288)</td></tr><tr><td>SOTA-s</td><td>0.5799(0.0202)</td><td>0.7074(0.0145)</td><td>0.2708(0.0055)</td><td>0.4528(0.0069)</td><td>0.4198(0.0825)</td><td>0.5865(0.0664)</td></tr></table>

Table 3. One way partial AUC on testing data of three molecular datasets

<table><tr><td></td><td colspan="2">moltox21(t0)</td><td colspan="2">molmuv(t1)</td><td colspan="2">molpcba(t0)</td></tr><tr><td>Methods</td><td>FPR≤0.3</td><td>FPR≤0.5</td><td>FPR≤0.3</td><td>FPR≤0.5</td><td>FPR≤0.3</td><td>FPR≤0.5</td></tr><tr><td>CE</td><td>0.6671(0.0009)</td><td>0.6954(0.005)</td><td>0.8008(0.0090)</td><td>0.8201(0.0061)</td><td>0.6802(0.0002)</td><td>0.7169(0.0002)</td></tr><tr><td>AUC-SH</td><td>0.7161(0.0043)</td><td>0.7295(0.0036)</td><td>0.7880(0.0382)</td><td>0.8025(0.0437)</td><td>0.6939(0.0009)</td><td>0.7350(0.0015)</td></tr><tr><td>AUC-M</td><td>0.6866(0.0048)</td><td>0.7080(0.0020)</td><td>0.7960(0.0123)</td><td>0.8076(0.0175)</td><td>0.6985(0.0016)</td><td>0.7399(0.0005)</td></tr><tr><td>P-push</td><td>0.6946(0.0107)</td><td>0.7160(0.0073)</td><td>0.7832(0.0220)</td><td>0.7940(0.0321)</td><td>0.6841(0.0007)</td><td>0.7293(0.0043)</td></tr><tr><td>MB</td><td>0.7398(0.0131)</td><td>0.7329(0.0099)</td><td>0.7672(0.0563)</td><td>0.7772(0.0547)</td><td>0.6899(0.0002)</td><td>0.7253(0.0006)</td></tr><tr><td>AW-poly</td><td>0.7227(0.0024)</td><td>0.7271(0.0112)</td><td>0.7754(0.0372)</td><td>0.7883(0.0431)</td><td>0.6975(0.0006)</td><td>0.7350(0.0015)</td></tr><tr><td>SOPA</td><td>0.7209(0.0063)</td><td>0.7318(0.0084)</td><td>0.8187(0.0319)</td><td>0.8245(0.0312)</td><td>0.6989(0.0022)</td><td>0.7371(0.0011)</td></tr><tr><td>SOPA-s</td><td>0.7309(0.0151)</td><td>0.7330(0.0073)</td><td>0.8449(0.0399)</td><td>0.8412(0.0447)</td><td>0.7027(0.0018)</td><td>0.7416(0.0006)</td></tr></table>

Table 4. Two way partial AUC on testing data of three molecular datasets; $( \alpha , \beta )$ represents $\mathrm { T P R } \geq $ α and $\mathrm { F P R } \leq \beta .$

<table><tr><td></td><td colspan="2">moltox21(t0)</td><td colspan="2">molmuv(t1)</td><td colspan="2">molpcba(t0)</td></tr><tr><td>Methods</td><td>(0.6,0.4)</td><td>(0.5,0.5)</td><td>(0.6,0.4)</td><td>(0.5,0.5)</td><td>(0.6,0.4)</td><td>(0.5,0.5)</td></tr><tr><td>CE</td><td>0.0674(0.0014)</td><td>0.2082(0.0011)</td><td>0.1613(0.0337)</td><td>0.4691(0.0183)</td><td>0.0949(0.0006)</td><td>0.2639(0.0006)</td></tr><tr><td>AUC-SH</td><td>0.0640(0.0080)</td><td>0.2170(0.0140)</td><td>0.2600(0.1300)</td><td>0.4440(0.1280)</td><td>0.1400(0.0030)</td><td>0.3120(0.0030)</td></tr><tr><td>AUC-M</td><td>0.0660(0.0090)</td><td>0.2090(0.0100)</td><td>0.1140(0.0790)</td><td>0.4330(0.0530)</td><td>0.1420(0.0090)</td><td>0.3130(0.0030)</td></tr><tr><td>P-push</td><td>0.0610(0.0180)</td><td>0.2070(0.0120)</td><td>0.1860(0.1520)</td><td>0.4170(0.1080)</td><td>0.1350(0.0020)</td><td>0.3000(0.0120)</td></tr><tr><td>MB</td><td>0.0670(0.0150)</td><td>0.2150(0.0230)</td><td>0.1730(0.1530)</td><td>0.4260(0.1180)</td><td>0.0950(0.0020)</td><td>0.2620(0.0030)</td></tr><tr><td>AW-poly</td><td>0.0640(0.0100)</td><td>0.2060(0.0250)</td><td>0.1720(0.1440)</td><td>0.3930(0.1230)</td><td>0.1100(0.0010)</td><td>0.2810(0.0020)</td></tr><tr><td>SOTA-s</td><td>0.0680(0.0180)</td><td>0.2300(0.0210)</td><td>0.3270(0.1640)</td><td>0.5260(0.1220)</td><td>0.1430(0.0010)</td><td>0.3140(0.0020)</td></tr></table>

![](images/11b92b388ea726dbd9d109c22eec0a3555242c8a7e11649fe23e57631135ec78.jpg)

![](images/3d887e66333cfab0d5698a36b2916248c007deaf432f9af95dd254989d8f42cf.jpg)  
Figure 3. Relative error (RE) for KLDRO-based estimator for OPAUC on moltox21-t0 dataset with FPR={0.3, 0.5}.

## 7. Conclusions

In this paper, we have proposed new formulations for partial AUC maximization by using distributionally robust optimization. We propose two formulations for both one-way and two-way partial AUC, and develop stochastic algorithms with convergence guarantee for solving the two formulations, respectively. Extensive experiments on image and molecular graph datasets verify the effectiveness of the proposed algorithms.

## 8. Acknowledgements

This work is partially supported by NSF Grant 2110545, NSF Career Award 1844403, and NSF Grant 1933212. D. Zhu and X. Wu was partially supported by NSF grant CCF-1733742. We also thank anonymous reviewers for constructive comments.

## References

Agarwal, S. The infinite push: A new support vector ranking algorithm that directly optimizes accuracy at the absolute top of the list. In SDM, 2011.

Balasubramanian, K., Ghadimi, S., and Nguyen, A. Stochastic multi-level composition optimization algorithms with level-independent convergence rates. ArXiv e-prints, arXiv:2008.10526, 2021.

Chen, Z., Yuan, Z., Yi, J., Zhou, B., Chen, E., and Yang, T. Universal stagewise learning for non-convex problems with convergence on averaged solutions. In 7th International Conference on Learning Representations (ICLR), 2019.

Davis, D. and Drusvyatskiy, D. Stochastic subgradient method converges at the rate o(k<sup>−1/4</sup>) on weakly convex functions. CoRR, /abs/1802.02988, 2018.

Dodd, L. and Pepe, M. Partial auc estimation and regression. Biometrics, 59:614–23, 10 2003. doi: 10.1111/ 1541-0420.00071.

Drusvyatskiy, D. and Paquette, C. Efficiency of minimizing compositions of convex functions and smooth maps. Mathematical Programming, pp. 1–56, 2019.

Gao, W. and Zhou, Z.-H. On the consistency of auc pairwise optimization. In Proceedings of the 24th International Conference on Artificial Intelligence, IJCAI’15, pp. 939–945. AAAI Press, 2015. ISBN 9781577357384.

Guo, Z., Xu, Y., Yin, W., Jin, R., and Yang, T. On stochastic moving-average estimators for non-convex optimization. ArXiv e-prints, arXiv:2104.14840, 2021.

He, K., Zhang, X., Ren, S., and Sun, J. Deep residual learning for image recognition. In Proceedings of the IEEE conference on computer vision and pattern recognition, pp. 770–778, 2016.

Herbrich, R., Graepel, T., and Obermayer, K. Large Margin Rank Boundaries for Ordinal Regression. In Advances in Large Margin Classifiers, chapter 7, pp. 115–132. The MIT Press, 1999. URL http://www.herbrich. me/papers/nips98\_ordinal.pdf.

Hu, W., Fey, M., Zitnik, M., Dong, Y., Ren, H., Liu, B., Catasta, M., and Leskovec, J. Open graph benchmark: Datasets for machine learning on graphs. arXiv preprint arXiv:2005.00687, 2020.

Iwata, T., Fujino, A., and Ueda, N. Semi-supervised learning for maximizing the partial auc. In AAAI, 2020.

Kar, P., Narasimhan, H., and Jain, P. Online and stochastic gradient methods for non-decomposable loss functions. In Proceedings of the 27th International Conference on Neural Information Processing Systems - Volume 1, NIPS’14, pp. 694–702, Cambridge, MA, USA, 2014. MIT Press.

Komori, O. and Eguchi, S. A boosting method for maximizing the partial area under the roc curve. BMC Bioinformatics, 11:314 – 314, 2010.

Krizhevsky, A., Hinton, G., et al. Learning multiple layers of features from tiny images. 2009.

Levy, D., Carmon, Y., Duchi, J. C., and Sidford, A. Largescale methods for distributionally robust optimization. Advances in Neural Information Processing Systems, 33, 2020.

Li, N., Jin, R., and Zhou, Z.-H. Top rank optimization in linear time. In NIPS, 2014.

Liu, M., Yuan, Z., Ying, Y., and Yang, T. Stochastic AUC maximization with deep neural networks. In 8th International Conference on Learning Representations (ICLR), 2020.

Narasimhan, H. and Agarwal, S. Svmpauctight: A new support vector method for optimizing partial auc based on a tight convex upper bound. In Proceedings of the 19th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, KDD ’13, pp. 167–175, New York, NY, USA, 2013a. Association for Computing Machinery. ISBN 9781450321747. doi: 10. 1145/2487575.2487674. URL https://doi.org/ 10.1145/2487575.2487674.

Narasimhan, H. and Agarwal, S. A structural SVM based approach for optimizing partial auc. In Dasgupta, S. and McAllester, D. (eds.), Proceedings of the 30th International Conference on Machine Learning, volume 28 of Proceedings of Machine Learning Research, pp. 516– 524, Atlanta, Georgia, USA, 17–19 Jun 2013b. PMLR. URL https://proceedings.mlr.press/v28/ narasimhan13.html.

Narasimhan, H. and Agarwal, S. Support vector algorithms for optimizing the partial area under the roc curve. Neural Computation, 29:1919–1963, 2017.

Ogryczak, W. and Tamir, A. Minimizing the sum of the k largest functions in linear time. Information Processing Letters, 85:117–122, 02 2003. doi: 10.1016/ S0020-0190(02)00370-8.

Qi, Q., Luo, Y., Xu, Z., Ji, S., and Yang, T. Stochastic optimization of area under precision-recall curve

for deep learning with provable convergence. In Advances in neural information processing systems, volume abs/2104.08736, 2021. URL https://arxiv.org/ abs/2104.08736.

Rafique, H., Liu, M., Lin, Q., and Yang, T. Non-convex minmax optimization: Provable algorithms and applications in machine learning. Optimization Methods and Software, 2020.

Rakotomamonjy, A. Sparse support vector infinite push. In ICML, 2012.

Ricamato, M. T. and Tortorella, F. Partial auc maximization in a linear combination of dichotomizers. Pattern Recognit., 44:2669–2677, 2011.

Rockafellar, R. T., Uryasev, S., et al. Optimization of conditional value-at-risk. Journal ofrisk, 2:21–42, 2000.

Rotemberg, V., Kurtansky, N., Betz-Stablein, B., Caffery, L., Chousakos, E., Codella, N., Combalia, M., Dusza, S., Guitera, P., Gutman, D., et al. A patient-centric dataset of images and metadata for identifying melanomas using clinical context. Scientific data, 8(1):1–8, 2021.

Rudin, C. The p-norm push: A simple convex ranking algorithm that concentrates at the top of the list. Journal of Machine Learning Research, 10(78):2233– 2271, 2009. URL http://jmlr.org/papers/ v10/rudin09b.html.

Takenouchi, T., Komori, O., and Eguchi, S. An extension of the receiver operating characteristic curve and aucoptimal classification. Neural computation, 24:2789–824, 06 2012. doi: 10.1162/NECO a 00336.

Ueda, N. and Fujino, A. Partial auc maximization via nonlinear scoring functions. ArXiv, abs/1806.04838, 2018.

Wang, B. and Yang, T. Finite-sum coupled compositional stochastic optimization: Theory and applications. In Proceedings ofthe International Conference on Machine Learning, pp. –, 2022.

Wang, Z. and Chang, Y.-C. I. Marker selection via maximizing the partial area under the roc curve of linear risk scores. Biostatistics, 12 2:369–85, 2011.

Wang, Z., Liu, M., Luo, Y., Xu, Z., Xie, Y., Wang, L., Cai, L., Qi, Q., Yuan, Z., Yang, T., and Ji, S. Advanced graph and sequence neural networks for molecular property prediction and drug discovery, 2021.

Wu, S.-H., Lin, K.-P., Chen, C.-M., and Chen, M.-S. Asymmetric support vector machines: Low false-positive learning under the user tolerance. In Proceedings of the 14th ACM SIGKDD International Conference on

Knowledge Discovery and Data Mining, KDD ’08, pp. 749–757, New York, NY, USA, 2008. Association for Computing Machinery. ISBN 9781605581934. doi: 10. 1145/1401890.1401980. URL https://doi.org/ 10.1145/1401890.1401980.

Xu, K., Hu, W., Leskovec, J., and Jegelka, S. How powerful are graph neural networks? arXiv preprint arXiv:1810.00826, 2018.

Yang, H., Lu, K., Lyu, X., and Hu, F. Two-way partial auc and its properties. Statistical methods in medical research, 28(1):184–195, 2019.

Yang, Z., Xu, Q., Bao, S., He, Y., Cao, X., and Huang, Q. When all we need is a piece of the pie: A generic framework for optimizing two-way partial auc. In Meila, M. and Zhang, T. (eds.), Proceedings of the 38th International Conference on Machine Learning, volume 139 of Proceedings of Machine Learning Research, pp. 11820–11829. PMLR, 18–24 Jul 2021. URL https://proceedings.mlr.press/ v139/yang21k.html.

Yao, Y., Lin, Q., and Yang, T. Large-scale optimization of partial auc in a range of false positive rates. arXiv preprint, 2022.

Yuan, Z., Yan, Y., Sonka, M., and Yang, T. Robust deep AUC maximization: A new surrogate loss and empirical studies on medical image classification. In Interntional Conference on Computer Vision, volume abs/2012.03173, 2020. URL https://arxiv.org/ abs/2012.03173.

Yuan, Z., Guo, Z., Xu, Y., Ying, Y., and Yang, T. Federated deep AUC maximization for hetergeneous data with a constant communication complexity. In Meila, M. and Zhang, T. (eds.), Proceedings of the 38th International Conference on Machine Learning, ICML 2021, 18-24 July 2021, Virtual Event, volume 139 of Proceedings of Machine Learning Research, pp. 12219–12229. PMLR, 2021. URL http://proceedings.mlr.press/ v139/yuan21a.html.

## A. More Experimental Results

Table 5. Datasets Statistics. The percentage in parenthesis represents the proportion of positive samples.

<table><tr><td>Dataset</td><td>Train</td><td>Validation</td><td>Test</td></tr><tr><td>CIFAR-10</td><td>24000 (16.67%)</td><td>6000 (16.67%)</td><td>6000 (16.67%)</td></tr><tr><td>CIFAR-100</td><td>24000 (16.67%)</td><td>6000 (16.67%)</td><td>6000 (16.67%)</td></tr><tr><td>Melanoma</td><td>26500 (1.76%)</td><td>3313 (1.78%)</td><td>3313 (1.75%)</td></tr><tr><td>moltox21(t0)</td><td>5834 (4.25%)</td><td>722 (4.01%)</td><td>709 (4.51%)</td></tr><tr><td>molmuv(t1)</td><td>11466 (0.18%)</td><td>1559 (0.13%)</td><td>1709 (0.35%)</td></tr><tr><td>molpcba(t0)</td><td>120762 (9.32%)</td><td>19865 (11.74%)</td><td>20397 (11.61%)</td></tr></table>

## A.1. Additional plots for training convergence

We present more training convergence plots on Melanoma dataset and molmuv dataset at Figure 4. For OPAUC maximization, We can observe that both our proposed SOPA-s and SOPA converge much better than AW-poly and MB method under different settings, i.e., $\mathrm { F P R \le 0 . 3 }$ and $\mathrm { F P R } \leq 0 . 5$ . And our proposed SOTA-s converge higher by a noticeable margin than AW-poly and MB method for TPAUC maximization all the time.

![](images/b41b7330427dda82ec8798f31968676a4a1cb78eb461cebd799c44227cbab641.jpg)

![](images/fcf1fc3119d26a219f3bad91ffa16270737e85d2d99f9cb8fa6e4de4d8741ba0.jpg)

![](images/36e3c26c3445d693f52be9320b9836a06d316b769c09e71835fdb687e00352b9.jpg)

![](images/edf13a72d985cea9e1a1591bb115d67ef05f16cf42c128adc9d09d1d2a32e9f0.jpg)

![](images/5b06daaac872c7c96ce139ac7842a0e739b49c04a6de95cb9113ff0d8abd9390.jpg)

![](images/f09e377660fb4c3399e4e328f44710e70761986d8cd1046b0d70c415e05531c2.jpg)

![](images/c4809097bd1b20e8c567b9be329d49162fe396a26defa27a2cc99ceae2182703.jpg)

![](images/ba62263c62880b483a36486221493fe94e6c0b2da418d4235a0a826c55266dd5.jpg)  
Figure 4. Training Convergence Curves on Melanoma and molmuv datasets; Top for OPAUC maximization, bottom for TPAUC maxi mization.

## A.2. Ablation study for $\gamma _ { 0 }$ in SOPA-s and $\gamma _ { 0 } , \gamma _ { 1 }$ in SOTA-s

We conduct extensive ablation study for understanding the extra hyper-parameters $\gamma _ { 0 }$ in SOPA-s and $\gamma _ { 0 } , \gamma _ { 1 }$ in SOTA-s algorithms. We fix it as 0.9 for all of our experiments in the main content. But in practice, the performance would be further improved if we tune those hyper-parameters as well.

For image datasets, we conduct experiments on CIFAR-10 and CIFAR-100; for molecule datasets, we conduct experiments on ogbg-moltox21 and ogbg-molmuv. For each dataset, we first fix the best learning rate and other hyper-parameters based on our previous results in the paper. Then, for SOPA-s, we investigate $\gamma _ { 0 }$ at {1.0, 0.9, 0.7, 0.5, 0.3, 0.1}; for SOTA-s, we investigate both $\gamma _ { 0 }$ and $\gamma _ { 1 }$ at {1.0, 0.9, 0.7, 0.5, 0.3, 0.1}

For training aspect, we include the comparisons for SOPA-s at Figure $5 ;$ we include the comparisons for SOTA-s at Figure $^ { 6 . }$ From Figure 5, we can see that better training performance could be achieved by tuning the parameter $\gamma _ { 0 }$ in SOPA-s, compared with fixing it as 0.9; the similar result for SOTA-s can be also observed from Figure 6.

For testing aspect, we include the testing pAUC results at Table 6 for SOPA-s; Table 7 for SOTA-s. Both verify that tuning these parameters can further improve the performance.

![](images/45212862ceea469b5ae892940d59858011e6026925187324430c12359fc6964e.jpg)  
Figure 6. Top-6 choices of $\gamma _ { 0 }$ and $\gamma _ { 1 }$ for SOTA-s from training perspective.

Table 6. Test pAUC for SOPA-s on different $\gamma _ { 0 } .$

<table><tr><td>Dataset</td><td>Metric</td><td> $\gamma_0=1.0$ </td><td> $\gamma_0=0.9$ </td><td> $\gamma_0=0.7$ </td><td> $\gamma_0=0.5$ </td><td> $\gamma_0=0.3$ </td><td> $\gamma_0=0.1$ </td></tr><tr><td rowspan="2">CIFAR-10</td><td>FPR≤0.3</td><td>0.8721(0.0049)</td><td>0.8691(0.0036)</td><td>0.8682(0.0048)</td><td>0.8697(0.0032)</td><td>0.8674(0.0045)</td><td>0.8725(0.0012)</td></tr><tr><td>FPR≤0.5</td><td>0.8989(0.0051)</td><td>0.8961(0.0036)</td><td>0.8946(0.0040)</td><td>0.8980(0.0037)</td><td>0.8947(0.0028)</td><td>0.8996(0.0021)</td></tr><tr><td rowspan="2">CIFAR-100</td><td>FPR≤0.3</td><td>0.7464(0.0012)</td><td>0.7460(0.0068)</td><td>0.7482(0.0031)</td><td>0.7508(0.0038)</td><td>0.7494(0.0048)</td><td>0.7514(0.0018)</td></tr><tr><td>FPR≤0.5</td><td>0.7888(0.0016)</td><td>0.7877(0.0053)</td><td>0.7936(0.0040)</td><td>0.7961(0.0063)</td><td>0.7922(0.0059)</td><td>0.7954(0.0015)</td></tr><tr><td rowspan="2">moltox21</td><td>FPR≤0.3</td><td>0.7242(0.0170)</td><td>0.7288(0.0125)</td><td>0.7274(0.0087)</td><td>0.7274(0.0062)</td><td>0.7158(0.0069)</td><td>0.7340(0.0079)</td></tr><tr><td>FPR≤0.5</td><td>0.7245(0.0194)</td><td>0.7266(0.0111)</td><td>0.7280(0.0066)</td><td>0.7358(0.0079)</td><td>0.7249(0.0090)</td><td>0.7360(0.0123)</td></tr><tr><td rowspan="2">molmuv</td><td>FPR≤0.3</td><td>0.8692(0.0116)</td><td>0.8376(0.0340)</td><td>0.8642(0.0214)</td><td>0.8735(0.0070)</td><td>0.8732(0.0104)</td><td>0.8496(0.0392)</td></tr><tr><td>FPR≤0.5</td><td>0.8773(0.0186)</td><td>0.8616(0.0355)</td><td>0.8747(0.0053)</td><td>0.8996(0.0228)</td><td>0.8918(0.0232)</td><td>0.8622(0.0415)</td></tr></table>

## B. Proofs

We next present several lemmas. The first lemma is straightforward.

Lemma 4. For $\hat { L } _ { k l } ( \cdot ; \lambda )$ , when $\lambda = 0 \ i t$ reduces to the maximal value of $\begin{array} { r } { \{ \ell _ { 1 } ( \cdot ) , \ldots , \ell _ { n } ( \cdot ) \} , i . e . , \hat { L } _ { k l } ( \cdot , 0 ) = \operatorname* { m a x } _ { i } \ell _ { i } ( \cdot ) , } \end{array}$ and when $\lambda = \infty ,$ , it reduces to the average value of $\begin{array} { r } { \{ \ell _ { 1 } , \ldots , \ell _ { n } \} , i . e . , \hat { L } _ { k l } ( \cdot ; \infty ) = \frac { 1 } { n } \sum _ { i = 1 } ^ { n } \ell _ { i } ( \cdot ) . } \end{array}$

Lemma 5. [Lemma 1 (Ogryczak & Tamir, 2003)] Assume $\gamma = k / n$ for some integer $k \in [ n ] ,$ , we have $\hat { L } _ { c v a r } ( \cdot ; \gamma ) =$ $\begin{array} { r } { \operatorname* { m i n } _ { s } s + \frac { 1 } { n \gamma } \sum _ { i = 1 } ^ { n } [ \ell _ { i } ( \cdot ) - s ] _ { + } } \end{array}$

A major difference between $\hat { L } _ { k l } ( \cdot ; \lambda )$ and $\hat { L } _ { c v a r } ( \cdot ; \gamma )$ that has an impact on optimization is that $\hat { L } _ { c v a r } ( \cdot ; \gamma )$ is a non-smooth function, and $\hat { L } _ { k l } ( \cdot ; \lambda )$ is a smooth function for $\lambda > 0$ when $\ell _ { i } ( \cdot )$ is smooth and bounded as indicated by the following lemma.

Table 7. Test pAUC for SOTA-s on different γ<sub>0</sub> and γ<sub>1</sub>.

<table><tr><td>CIFAR-10</td><td>(0.4, 0.6)</td><td> $\gamma_1=1.0$ </td><td> $\gamma_1=0.9$ </td><td> $\gamma_1=0.7$ </td><td> $\gamma_1=0.5$ </td><td> $\gamma_1=0.3$ </td><td> $\gamma_1=0.1$ </td></tr><tr><td rowspan="6"></td><td> $\gamma_0=1.0$ </td><td>0.5731(0.0069)</td><td>0.5744(0.0083)</td><td>0.5668(0.0048)</td><td>0.5686(0.0089)</td><td>0.5678(0.0070)</td><td>0.5739(0.0135)</td></tr><tr><td> $\gamma_0=0.9$ </td><td>0.5802(0.0081)</td><td>0.5839(0.0116)</td><td>0.5693(0.0072)</td><td>0.5743(0.0131)</td><td>0.5688(0.0048)</td><td>0.5760(0.0095)</td></tr><tr><td> $\gamma_0=0.7$ </td><td>0.5755(0.0098)</td><td>0.5715(0.0032)</td><td>0.5684(0.0131)</td><td>0.5797(0.0036)</td><td>0.5718(0.0095)</td><td>0.5695(0.0111)</td></tr><tr><td> $\gamma_0=0.5$ </td><td>0.5743(0.0058)</td><td>0.5706(0.0025)</td><td>0.5641(0.0094)</td><td>0.5819(0.0077)</td><td>0.5725(0.0109)</td><td>0.5739(0.0068)</td></tr><tr><td> $\gamma_0=0.3$ </td><td>0.5767(0.0121)</td><td>0.5638(0.0144)</td><td>0.5617(0.0075)</td><td>0.5644(0.0099)</td><td>0.5595(0.0028)</td><td>0.5768(0.0100)</td></tr><tr><td> $\gamma_0=0.1$ </td><td>0.5608(0.0075)</td><td>0.5689(0.0134)</td><td>0.5699(0.0096)</td><td>0.5685(0.0056)</td><td>0.5583(0.0101)</td><td>0.5756(0.0135)</td></tr><tr><td>CIFAR-10</td><td>(0.5, 0.5)</td><td> $\gamma_1=1.0$ </td><td> $\gamma_1=0.9$ </td><td> $\gamma_1=0.7$ </td><td> $\gamma_1=0.5$ </td><td> $\gamma_1=0.3$ </td><td> $\gamma_1=0.1$ </td></tr><tr><td rowspan="6"></td><td> $\gamma_0=1.0$ </td><td>0.7022(0.0054)</td><td>0.6999(0.0076)</td><td>0.6922(0.0076)</td><td>0.6969(0.0087)</td><td>0.6982(0.0046)</td><td>0.6981(0.0074)</td></tr><tr><td> $\gamma_0=0.9$ </td><td>0.7051(0.0083)</td><td>0.7047(0.0072)</td><td>0.6987(0.0034)</td><td>0.7008(0.0103)</td><td>0.6964(0.0048)</td><td>0.7003(0.0064)</td></tr><tr><td> $\gamma_0=0.7$ </td><td>0.7027(0.0046)</td><td>0.6999(0.0031)</td><td>0.6959(0.0099)</td><td>0.7043(0.0056)</td><td>0.6988(0.0099)</td><td>0.6914(0.0110)</td></tr><tr><td> $\gamma_0=0.5$ </td><td>0.7012(0.0050)</td><td>0.6988(0.0008)</td><td>0.6944(0.0067)</td><td>0.7044(0.0067)</td><td>0.7014(0.0047)</td><td>0.7031(0.0088)</td></tr><tr><td> $\gamma_0=0.3$ </td><td>0.7024(0.0099)</td><td>0.6940(0.0085)</td><td>0.6901(0.0060)</td><td>0.6981(0.0047)</td><td>0.6908(0.0025)</td><td>0.6977(0.0129)</td></tr><tr><td> $\gamma_0=0.1$ </td><td>0.6934(0.0068)</td><td>0.7009(0.0060)</td><td>0.6972(0.0088)</td><td>0.6946(0.0037)</td><td>0.6891(0.0098)</td><td>0.7027(0.0082)</td></tr><tr><td>CIFAR-100</td><td>(0.4, 0.6)</td><td> $\gamma_1=1.0$ </td><td> $\gamma_1=0.9$ </td><td> $\gamma_1=0.7$ </td><td> $\gamma_1=0.5$ </td><td> $\gamma_1=0.3$ </td><td> $\gamma_1=0.1$ </td></tr><tr><td rowspan="6"></td><td> $\gamma_0=1.0$ </td><td></td><td>0.2650(0.0052)</td><td>0.2528(0.0061)</td><td>0.2573(0.0129)</td><td>0.2587(0.0096)</td><td>0.2613(0.0046)</td></tr><tr><td> $\gamma_0=0.9$ </td><td></td><td>0.2708(0.0055)</td><td>0.2698(0.0117)</td><td>0.2586(0.0116)</td><td>0.2562(0.0032)</td><td>0.2663(0.0056)</td></tr><tr><td> $\gamma_0=0.7$ </td><td></td><td>0.2624(0.0065)</td><td>0.2577(0.0045)</td><td>0.2664(0.0051)</td><td>0.2634(0.0090)</td><td>0.2626(0.0144)</td></tr><tr><td> $\gamma_0=0.5$ </td><td></td><td>0.2591(0.0026)</td><td>0.2552(0.0068)</td><td>0.2530(0.0069)</td><td>0.2656(0.0089)</td><td>0.2594(0.0052)</td></tr><tr><td> $\gamma_0=0.3$ </td><td></td><td>0.2542(0.0076)</td><td>0.2517(0.0111)</td><td>0.2599(0.0184)</td><td>0.2580(0.0191)</td><td>0.2631(0.0081)</td></tr><tr><td> $\gamma_0=0.1$ </td><td></td><td>0.2532(0.0050)</td><td>0.2745(0.0029)</td><td>0.2529(0.0060)</td><td>0.2573(0.0115)</td><td>0.2568(0.0029)</td></tr><tr><td>CIFAR-100</td><td>(0.5, 0.5)</td><td> $\gamma_1=1.0$ </td><td> $\gamma_1=0.9$ </td><td> $\gamma_1=0.7$ </td><td> $\gamma_1=0.5$ </td><td> $\gamma_1=0.3$ </td><td> $\gamma_1=0.1$ </td></tr><tr><td rowspan="6"></td><td> $\gamma_0=1.0$ </td><td></td><td>0.4454(0.0084)</td><td>0.4337(0.0097)</td><td>0.4418(0.0083)</td><td>0.4361(0.0093)</td><td>0.4405(0.0063)</td></tr><tr><td> $\gamma_0=0.9$ </td><td></td><td>0.4528(0.0069)</td><td>0.4494(0.0073)</td><td>0.4449(0.0171)</td><td>0.4337(0.0046)</td><td>0.4421(0.0058)</td></tr><tr><td> $\gamma_0=0.7$ </td><td></td><td>0.4426(0.0119)</td><td>0.4367(0.0092)</td><td>0.4414(0.0072)</td><td>0.4455(0.0046)</td><td>0.4430(0.0108)</td></tr><tr><td> $\gamma_0=0.5$ </td><td></td><td>0.4404(0.0058)</td><td>0.4388(0.0085)</td><td>0.4332(0.0079)</td><td>0.4426(0.0107)</td><td>0.4421(0.0057)</td></tr><tr><td> $\gamma_0=0.3$ </td><td></td><td>0.4313(0.0081)</td><td>0.4377(0.0104)</td><td>0.4392(0.0185)</td><td>0.4401(0.0095)</td><td>0.4384(0.0125)</td></tr><tr><td> $\gamma_0=0.1$ </td><td></td><td>0.4325(0.0006)</td><td>0.4500(0.0015)</td><td>0.4361(0.0085)</td><td>0.4355(0.0053)</td><td>0.4461(0.0213)</td></tr><tr><td>moltox21</td><td>(0.4, 0.6)</td><td> $\gamma_1=1.0$ </td><td> $\gamma_1=0.9$ </td><td> $\gamma_1=0.7$ </td><td> $\gamma_1=0.5$ </td><td> $\gamma_1=0.3$ </td><td> $\gamma_1=0.1$ </td></tr><tr><td rowspan="7"></td><td> $\gamma_0=1.0$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $\gamma_0=0.9$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $\gamma_0=0.7$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $\gamma_0=0.5$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $\gamma_0=0.3$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $\gamma_0=0.1$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $\gamma_0=0.1$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>moltox21</td><td>(0.5, 0.5)</td><td> $\gamma_1=1.0$ </td><td> $\gamma_1=0.9$ </td><td> $\gamma_1=0.7$ </td><td> $\gamma_1=0.5$ </td><td> $\gamma_1=0.3$ </td><td> $\gamma_1=0.1$ </td></tr><tr><td rowspan="8"></td><td> $\gamma_0=1.0$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $γ_0=1.0$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $γ_0=0.9$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $γ_0=0.7$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $γ_0=0.5$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $γ_0=0.3$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $γ_0=0.1$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $γ_0=0.1$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>molmuv</td><td>(0.4, 0.6)</td><td> $\gamma_1=1.0$ </td><td> $\gamma_1=0.9$ </td><td> $\gamma_1=0.7$ </td><td> $\gamma_1=0.5$ </td><td> $\gamma_1=0.3$ </td><td> $\gamma_1=0.1$ </td></tr><tr><td rowspan="5"></td><td> $γ_0=1.0$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $γ_0=0.9$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $γ_0=0.7$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $γ_0=0.5$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td> $γ_0=0.3$ </td><td></td><td></td><td></td><td></td><td></td><td></td></tr></table>

Lemma 6. $I f \ell _ { i } ( \cdot )$ is a smooth function, and has a bounded value and bounded gradient for a bounded input, then for $\lambda > 0$ the function $\hat { L } _ { k l } ( \mathrel { \cdot } ; \lambda )$ is also a smooth and boundedfunction.

Lemma 7. When $\phi _ { c } ( t ) = \mathbb { I } ( 0 \leq t \leq 1 / \beta )$ and $\phi _ { c } ^ { \prime } ( t ) = \mathbb { I } ( 0 \leq t \leq 1 / \alpha )$ with $K _ { 2 } = n _ { - } \beta$ and $K _ { 1 } = n _ { + } \alpha$ being integers, if $\ell ( \cdot )$ is monotonically decreasingfor $\ell ( \cdot ) > 0$ , we can show that

$$
F (\mathbf {w}; \phi_ {c}, \phi_ {c} ^ {\prime}) = \frac {1}{K _ {1} K _ {2}} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+} ^ {\uparrow} [ 1, K _ {1} ]} \sum_ {\mathbf {x} _ {j} \in \mathcal {S} _ {-} ^ {\downarrow} [ 1, K _ {2} ]} L (\mathbf {w}; \mathbf {x} _ {i}, \mathbf {x} _ {j}),
$$

which is also equivalent to

$$
F (\mathbf {w}; \phi_ {c}, \phi_ {c} ^ {\prime}) = \min _ {s ^ {\prime} \in \mathbb {R}, \mathbf {s} \in \mathbb {R} ^ {n _ {+}}} s ^ {\prime} + \frac {1}{n _ {+} \alpha} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} (s _ {i} + \frac {1}{\beta} \psi_ {i} (\mathbf {w}; s _ {i}) - s ^ {\prime}) _ {+}.
$$

## B.1. Proof of Lemma 6

It is easy to see if $\ell ( \mathbf { w } ) \in [ 0 , C ]$ is bounded and smooth, we have $\exp ( \frac { \ell ( \mathbf { w } ) } { \lambda } )$ is bounded and smooth due to its second order gradient is upper bounded. Then log $\mathrm { E } _ { i } \exp \bigl ( \frac { \ell _ { i } ( \mathbf { w } ) } { \lambda } \bigr )$ is bounded. Its smoothness due to that is a composition of $f = \log ( \cdot )$ and $\begin{array} { r } { g = \mathrm { E } _ { i } \exp ( \frac { \ell _ { i } ( \mathbf { w } ) } { \lambda } ) \in [ 1 , C ^ { \prime } ] } \end{array}$ and both $f , g$ are smooth and Lipschitz continuous for their inputs.

## B.2. Proof of Lemma 7

Proof. First, following Lemma 1, we have $F ( \mathbf { w } ; \phi , \phi ^ { \prime } )$ is equivalent to $\begin{array} { r } { \frac { 1 } { K _ { 1 } } \sum _ { i = 1 } ^ { K _ { 1 } } \hat { L } _ { \phi } ( \mathbf x _ { \pi _ { i } } , \mathbf w ) } \end{array}$ , where $\pi _ { i }$ denote the index of the positive example whose $\hat { L } _ { \phi } ( \mathbf { x } _ { \pi _ { i } } , \mathbf { w } )$ is the i-th largest among all positive examples. We prove that this is equivalent $\begin{array} { r } { \mathrm { ~ t o ~ } \frac { 1 } { K _ { 1 } } \sum _ { { \bf x } _ { i } \in { \cal S } _ { \bot } ^ { \uparrow } [ 1 , K _ { 1 } ] } \hat { L } _ { \phi } ( { \bf x } _ { i } , { \bf w } ) } \end{array}$ . To this end, we just need to show that if $h _ { \mathbf { w } } ( \mathbf { x } ) \geq h _ { \mathbf { w } } ( \mathbf { x } ^ { \prime } )$ then $\hat { L } _ { \phi } ( \mathbf { x } ^ { \prime } , \mathbf { w } ) \geq \hat { L } _ { \phi } ( \mathbf { x } , \mathbf { w } )$ which is true due to $\begin{array} { r } { \hat { L } _ { \phi } ( \mathbf { x } _ { i } , \mathbf { w } ) = \frac { 1 } { K _ { 2 } } \sum _ { \mathbf { x } _ { i } \in \mathcal { S } _ { - } ^ { \downarrow } [ 1 , K _ { 2 } ] } \ell ( h _ { \mathbf { w } } ( \mathbf { x } _ { i } ) - h _ { \mathbf { w } } ( \mathbf { x } _ { j } ) ) } \end{array}$ and ℓ is monotonically decreasing function. The second equation in the lemma is applying Lemma 5 twice and by noting that $( \operatorname* { m i n } _ { x } f ( x ) - s ) _ { + } = \operatorname* { m i n } _ { x } ( f ( x ) - s ) _ { + }$ □

## B.3. Proof of Theorem 1

Proof. Let us consider for a particular $\mathbf { x } _ { i } \in S _ { + }$ . When $\phi ( \cdot ) = \phi _ { c } ( \cdot ) = \mathbb { I } ( \cdot \in ( 0 , 1 / \beta ] )$ , then $\hat { L } ( \mathbf { w } ; \mathbf { x } _ { i } )$ becomes the CVaR estimator, i.e., the average of top K = n β losses of $\ell ( h _ { \mathbf { w } } ( \mathbf { x } _ { i } ) - h _ { \mathbf { w } } ( \mathbf { x } _ { j } ) )$ among $\mathbf { x } _ { j } \in { \mathcal { S } } _ { - } .$ Since $\ell ( \cdot )$ is monotonically decreasing when $\ell ( \cdot ) ) > 0$ , the top $K = n _ { - } \beta$ losses of $\ell ( h _ { \mathbf { w } } ( \mathbf { x } _ { i } ) - h _ { \mathbf { w } } ( \mathbf { x } _ { j } ) )$ among all $\mathbf { x } _ { j } \in S _ { - }$ <sub>−</sub> correspond to negative samples with top K prediction scores. Hence, $\begin{array} { r } { \hat { L } _ { \phi _ { c } } ( \mathbf { w } ; \mathbf { x } _ { i } ) = \frac { 1 } { K } \sum _ { \mathbf { x } _ { i } \in \mathcal { S } _ { - } ^ { \pm } [ 1 , K ] } \ell \big ( h _ { \mathbf { w } } ( \mathbf { x } _ { i } ) - h _ { \mathbf { w } } ( \mathbf { x } _ { j } ) \big ) } \end{array}$ . Then the equivalent problem in (9) follows from Lemma 5. □

## B.4. Proof of Theorem 2

Proof. When choosing $\phi ( \cdot ) = \phi _ { k l } ( \cdot )$ , the $\hat { L } _ { \phi } ( \mathbf { w } ; \mathbf { x } _ { i } )$ in problem (8) becomes

$$
\max _ {\mathbf {p} \in \Delta} \sum_ {\mathbf {x} _ {j} \in \mathcal {S} _ {-}} p _ {j} L (\mathbf {w}; \mathbf {x} _ {i}, \mathbf {x} _ {j}) - \lambda \sum_ {j} p _ {j} \log (n p _ {j}).
$$

With Karush-Kuhn-Tucker(KKT) conditions, it is not difficult to have $\begin{array} { r } { p _ { j } ^ { \star } = \frac { \exp ( L ( \mathbf w ; \mathbf x _ { i } , \mathbf x _ { j } ) / \lambda } { \sum _ { j } \exp ( L ( \mathbf w ; \mathbf x _ { i } , \mathbf x _ { j } ) / \lambda } . } \end{array}$ . By plugging in this back we obtain the claimed objective (10). When $\lambda = 0 .$ , the above becomes the maximal one among $\{ L ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) , \mathbf { x } _ { j } \in S _ { + } \}$ for each $\mathbf { x } _ { i } .$ . Then the object is $\begin{array} { r } { \frac { 1 } { n _ { + } } \operatorname* { m a x } _ { \mathbf { x } _ { j } \in \mathcal { S } _ { - } } L ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) } \end{array}$ , which is the surrogate of pAUC with $\mathrm { F P R } \leq 1 / n _ { - } .$ When $\lambda = \infty$ , the above becomes the average of $\{ L ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) , \mathbf { x } _ { j } \in S _ { + } \}$ , which gives the standard surrogate of AUC. □

## B.5. Proof of Lemma 2

First note that $\begin{array} { r } { F ( \mathbf { w } , \mathbf { s } ) = \frac { 1 } { n _ { + } } \sum _ { \mathbf { x } _ { i } \in { \cal S } _ { + } } \Big ( s _ { i } + \frac { 1 } { \beta } g _ { i } ( \mathbf { w } , s _ { i } ) \Big ) } \end{array}$ , and $\begin{array} { r } { g _ { i } ( \mathbf { w } , s _ { i } ) = \frac { 1 } { n _ { - } } \sum _ { \mathbf { x } _ { i } \in \mathcal { S } _ { - } } \left( L ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) - s _ { i } \right) _ { - } } \end{array}$ <sub>+</sub>. We prove that $( L ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) - s _ { i } ) .$ <sub>+</sub> is weakly convex in terms of $( \mathbf { w } , \mathbf { s } _ { i } )$ , i.e. there exists $\rho > 0$ such that $( L ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) - s _ { i } ) _ { + } +$ $\frac { \rho } { 2 } \| \mathbf { w } \| ^ { 2 } + \frac { \rho } { 2 } s _ { i } ^ { 2 }$ is jointly convex in terms of $\mathbf { w } , \mathbf { s } .$ To this end, let $\psi ( \cdot ) = [ \cdot ] .$ which is convex and Lipchitz continuous, and $\bar { q } ( \mathbf { w } , \mathbf { s } _ { i } ) = \bar { L } ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) - s _ { i }$ , which is $L _ { s }$ -smooth function with respect to $\left( \mathbf { w } , s _ { i } \right)$ due to that $L ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } )$ is $L _ { s }$ -smooth

function. Then for any $\omega \in \phi ^ { \prime } ( \psi ( \mathbf { w } ^ { \prime } , s _ { i } ^ { \prime } ) )$ we have

$$
\begin{array}{r l} & {\psi (q (\mathbf {w}, s _ {i})) \geq \psi (q (\mathbf {w} ^ {\prime}, s _ {i} ^ {\prime})) + \omega (q (\mathbf {w}, s _ {i}) - q (\mathbf {w} ^ {\prime}, s _ {i} ^ {\prime}))} \\ & {\geq \psi (q (\mathbf {w} ^ {\prime}, s _ {i} ^ {\prime})) + \omega (\nabla q (\mathbf {w} ^ {\prime}, s _ {i} ^ {\prime}) - \frac {L _ {s}}{2} (\| \mathbf {w} - \mathbf {w} ^ {\prime} \| ^ {2} + | s _ {i} - s _ {i} ^ {\prime} | ^ {2}))} \\ & {\geq \psi (q (\mathbf {w} ^ {\prime}, s _ {i} ^ {\prime})) + \partial \psi (q (\mathbf {w} ^ {\prime}, s _ {i} ^ {\prime})) - \frac {L _ {s}}{2} (\| \mathbf {w} - \mathbf {w} ^ {\prime} \| ^ {2} + | s _ {i} - s _ {i} ^ {\prime} | ^ {2})} \end{array}
$$

where we use $0 \leq \omega \leq 1$ . The above inequality implies that $\left[ L ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) - s _ { i } \right] _ { + }$ is $L _ { s }$ -weakly convex in terms of $\left( \mathbf { w } , s _ { i } \right)$ (Davis & Drusvyatskiy, 2018), i.e., $\begin{array} { r } { \frac { 1 } { n _ { - } } \sum _ { { \bf x } _ { i } \in { \cal S } _ { - } } \left\{ \big ( L ( { \bf w } ; { \bf x } _ { i } , { \bf x } _ { j } ) - s _ { i } \big ) _ { + } + \frac { L _ { s } } { 2 } \big ( \| { \bf w } \| ^ { 2 } + | s _ { i } | ^ { 2 } \big ) \right\} } \end{array}$ is convex. As a result $\begin{array} { r } { \frac { 1 } { n _ { - } } \sum _ { { \bf x } _ { i } \in { \mathcal S } _ { - } } ( L ( { \bf w } ; { \bf x } _ { i } , { \bf x } _ { j } ) - s _ { i } ) _ { + } + \frac { L _ { s } } { 2 } ( \| { \bf w } \| ^ { 2 } + \| s _ { i } \| ^ { 2 } ) } \end{array}$ is jointly convex in $\left( \mathbf { w } , s _ { i } \right)$ . Then $\begin{array} { r } { F ( \mathbf { w } , \mathbf { s } ) + \frac { L _ { s } } { 2 \beta } ( \| \mathbf { w } \| ^ { 2 } + \sum _ { i } | s _ { i } | ^ { 2 } ) } \end{array}$ is jointly convex in terms of $\mathbf { \Psi } ( \mathbf { w } , \mathbf { s } )$

## B.6. Proof of Theorem 3

Let $F ( \mathbf { w } , \mathbf { s } )$ denote the objective function, and let $\mathbf { v } = ( \mathbf { w } , \mathbf { s } )$ . Define $\begin{array} { r } { { F _ { 1 / \hat { \rho } } } ( { \bf { v } } ) = { \operatorname* { m i n } } _ { \bf { u } } F ( { \bf { u } } ) + \frac { \hat { \rho } } { 2 } \| { \bf { u } } - { \bf { v } } \| ^ { 2 } } \end{array}$ for some $\hat { \rho } > \rho$ and the minimizer is denoted by $\mathrm { p r o x } _ { F / \hat { \rho } } ( \mathbf { v } )$ . Let $\widehat { \mathbf { v } } _ { t } = \mathrm { p r o x } _ { F / \hat { \rho } } ( \mathbf { v } _ { t } )$ . Define $\| \mathbf { v } - \mathbf { v } ^ { \prime } \| ^ { 2 } = \| \mathbf { w } - \mathbf { w } ^ { \prime } \| ^ { 2 } + \| \mathbf { s } - \mathbf { s } ^ { \prime } \| ^ { 2 }$

$$
\begin{array}{r l} & {\mathrm{E} _ {t} [ F _ {1 / \hat {\rho}} (\mathbf {v} _ {t + 1}) ] = \mathrm{E} _ {t} [ F (\widehat {\mathbf {v}} _ {t}) + \frac {\hat {\rho}}{2} \| \mathbf {v} _ {t + 1} - \widehat {\mathbf {v}} _ {t} \| ^ {2} ]} \\ & {\leq F (\widehat {\mathbf {v}} _ {t}) + \frac {\hat {\rho}}{2} \mathrm{E} _ {t} [ \| \mathbf {w} _ {t} - \eta_ {1} \nabla_ {\mathbf {w}} F (\mathbf {w} _ {t}, \mathbf {s} _ {t}, \xi_ {t}) - \widehat {\mathbf {w}} _ {t} \| ^ {2} + \| \mathbf {s} _ {t + 1} - \widehat {\mathbf {s}} _ {t} \| ^ {2} ]} \\ & {\leq F (\widehat {\mathbf {v}} _ {t}) + \frac {\hat {\rho}}{2} \mathrm{E} _ {t} [ \| \mathbf {w} _ {t} - \eta_ {1} \nabla_ {\mathbf {w}} F (\mathbf {w} _ {t}, \mathbf {s} _ {{t}}, \xi_ {{t}}) - \widehat {\mathbf {w}} _ {{t}} \| ^ {2} ] + \frac {\hat {\rho}}{2} \mathrm{E} _ {t} [ \| \mathbf {s} _ {t + 1} - \widehat {\mathbf {s}} _ {{t}} \| ^ {2} ]} \\ & {\leq F (\widehat {\mathbf {x}} _ {t}) + \frac {\hat {\rho}}{2} \| \mathbf {w} _ {{t}} - \widehat {\mathbf {w}} _ {{t}} \| ^ {2} + \hat {\rho} \eta_ {{t}} \mathrm{E} _ {{t}} [ (\widehat {\mathbf {w}} _ {{t}} - \mathbf {w} _ {{t}}) ^ {\top} \nabla_ {\mathbf {w}} F (\mathbf {w} _ {{t}}, \mathbf {s} _ {{t}}) ] + \frac {\hat {\rho} \eta_ {{1}} ^ {2} G ^ {2}}{2} + \frac {\hat {\rho}}{2} \mathrm{E} _ {{t}} [ \| \mathbf {s} _ {{t + 1}} - \widehat {\mathbf {s}} _ {{t}} \| ^ {2} ]} \end{array}
$$

where we assume $\begin{array} { r } { \mathrm { E } [ \| \nabla _ { \mathbf { w } } F ( \mathbf { w } _ { t } , \mathbf { s } _ { t } , \xi _ { t } ) \| ^ { 2 } ] \leq G ^ { 2 } = \frac { C ^ { 2 } } { \beta ^ { 2 } } } \end{array}$ . According to the analysis of stochastic coordinate descent method, for any $\mathbf { s } = ( s _ { 1 } , \ldots , s _ { n _ { + } } )$ we have

$$
2 \eta_ {2} (s _ {t, i} - s _ {i}) ^ {\top} \nabla_ {s _ {i}} F (\mathbf {w} _ {t}, \mathbf {s} _ {t}; \xi_ {t}) \leq \eta_ {2} ^ {2} \| \nabla_ {s _ {i}} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) \| ^ {2} + (\| s _ {i} - s _ {t, i} \| ^ {2} - \| s _ {i} - s _ {t + 1, i} \| ^ {2})
$$

Summing the above inequality over $i \in B _ { + }$ , we have

$$
2 \eta_ {2} \sum_ {i \in \mathcal {B} _ {+}} (s _ {t, i} - s _ {i}) ^ {\top} \nabla_ {s _ {i}} F (\mathbf {w} _ {t}, \mathbf {s} _ {t}; \xi_ {t}) \leq \eta_ {2} ^ {2} \sum_ {i \in \mathcal {B} _ {+}} \| \nabla_ {s _ {i}} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) \| ^ {2} + (\| \mathbf {s} - \mathbf {s} _ {t} \| ^ {2} - \| \mathbf {s} - \mathbf {s} _ {t + 1} \| ^ {2})
$$

Taking expectation and re-arrange, we have

$$
\mathrm{E} [ \frac {1}{2} \| \mathbf {s} _ {t + 1} - \widehat {\mathbf {s}} _ {t} \| ^ {2} ] \leq \mathrm{E} [ \frac {1}{2} \| \mathbf {s} _ {t} - \widehat {\mathbf {s}} _ {t} \| ^ {2} + \eta_ {2} \frac {B _ {+}}{n _ {+}} (\widehat {\mathbf {s}} _ {t} - \mathbf {s} _ {t}) ^ {\top} \nabla_ {\mathbf {s}} F (\mathbf {w} _ {t}, \mathbf {s} _ {t}) + \frac {\eta_ {2} ^ {2} B _ {+} C _ {2} ^ {2}}{2} ]
$$

where we use the fact $\begin{array} { r } { \mathrm { E } [ | \nabla _ { s _ { i } } F ( \mathbf w , \mathbf s ) | ^ { 2 } ] \le C _ { 2 } ^ { 2 } = \frac { 1 } { n _ { \bot } ^ { 2 } } ( 1 + 1 / \beta ) ^ { 2 } . \mathrm { L e t } \eta _ { 2 } B _ { + } / n _ { + } = \eta _ { 1 } } \end{array}$ , we have

$$
\begin{array}{r l} & {\mathrm{E} _ {t} [ F _ {1 / \hat {\rho}} (\mathbf {v} _ {t + 1}) ]} \\ & {\leq F (\widehat {\mathbf {x}} _ {t}) + \frac {\hat {\rho}}{2} \| \mathbf {w} _ {t} - \widehat {\mathbf {w}} _ {t} \| ^ {2} + \hat {\rho} \eta_ {1} \mathrm{E} _ {t} [ (\widehat {\mathbf {w}} _ {t} - \mathbf {w} _ {t}) ^ {\top} \nabla_ {\mathbf {w}} F (\mathbf {w} _ {t}, \mathbf {s} _ {t}) ] + \frac {\hat {\rho}}{2} \mathrm{E} _ {t} [ \| \mathbf {s} _ {t + 1} - \widehat {\mathbf {s}} _ {t}) ] + \frac {\hat {\rho} \eta_ {1} ^ {2} G ^ {2}}{2}} \\ & {\leq F (\widehat {\mathbf {v}} _ {t}) + \frac {\hat {\rho}}{2} \| \mathbf {v} _ {t} - \widehat {\mathbf {v}} _ {t} \| ^ {2} + \hat {\rho} \eta_ {1} \mathrm{E} _ {t} [ (\widehat {\mathbf {v}} _ {t} - \mathbf {v} _ {t}) ^ {\top} \partial F (\mathbf {w} _ {t}, \mathbf {s} _ {t}) ] + \frac {\hat {\rho} \eta_ {1} ^ {2} (G ^ {2} + n _ {+} ^ {2} C _ {2} ^ {2} / B _ {+})}{2}} \\ & {\leq F _ {1 / \hat {\rho}} (\mathbf {v} _ {t}) + \hat {\rho} \eta_ {1} (F (\widehat {\mathbf {v}} _ {t}) - F (\mathbf {v} _ {t}) + \frac {\rho}{2} \| \mathbf {v} _ {t} - \widehat {\mathbf {v}} _ {t} \| ^ {2}) + \frac {\hat {\rho} \eta_ {1} ^ {2} (G ^ {2} + n _ {+} ^ {2} C _ {2} ^ {2} / B _ {+})}{2}} \end{array}
$$

As a result, we have

$$
\hat {\rho} \eta_ {1} (F (\mathbf {v} _ {t}) - F (\widehat {\mathbf {v}} _ {t}) - \rho \| \mathbf {v} _ {t} - \widehat {\mathbf {v}} _ {t} \| ^ {2}) \leq F _ {1 / \hat {\rho}} (\mathbf {v} _ {t}) - \mathrm{E} _ {t} [ F _ {1 / \hat {\rho}} (\mathbf {v} _ {t + 1}) ] + \frac {\hat {\rho} \eta_ {1} ^ {2} (G ^ {2} + n _ {+} ^ {2} C _ {2} ^ {2} / B _ {+})}{2}
$$

Since we have

$$
\begin{array}{r l} & F (\mathbf {v} _ {t}) - F (\widehat {\mathbf {v}} _ {t}) - \rho \| \mathbf {v} _ {t} - \widehat {\mathbf {v}} _ {t} \| ^ {2} = (F (\mathbf {v} _ {t}) + \hat {\rho} \| \mathbf {v} _ {t} - \mathbf {v} _ {t} \| ^ {2}) - (F (\widehat {\mathbf {v}} _ {t}) + \hat {\rho} \| \widehat {\mathbf {v}} _ {t} - \mathbf {v} _ {t} \| ^ {2}) + (\hat {\rho} - \rho) \| \mathbf {v} _ {t} - \widehat {\mathbf {v}} _ {t} \| ^ {2} \\ & \geq \frac {(2 \hat {\rho} - \rho)}{2} \| \widehat {\mathbf {v}} _ {t} - \mathbf {v} _ {t} \| ^ {2} + (\hat {\rho} - \rho) \| \mathbf {v} _ {t} - \widehat {\mathbf {v}} _ {t} \| ^ {2} = (2 \hat {\rho} - 3 / 2 \rho) \| \mathbf {v} _ {t} - \widehat {\mathbf {v}} _ {t} \| ^ {2} = \frac {(2 \hat {\rho} - 3 / 2 \rho)}{\hat {\rho} ^ {2}} \| \nabla F _ {1 / \hat {\rho}} (\mathbf {v} _ {t}) \| ^ {2} \end{array}
$$

Let $\hat { \rho } = 3 \rho / 2$ . As a result, we have

$$
\begin{array}{l} \frac {1}{T} \sum_ {t = 1} ^ {T} \| \nabla F _ {1 / \hat {\rho}} (\mathbf {v} _ {t}) \| ^ {2} \leq \frac {(F _ {1 / \hat {\rho}} (\mathbf {v} _ {1}) - \min F)}{\eta_ {1} T} + \frac {\hat {\rho} \eta_ {1} (G ^ {2} + n _ {+} ^ {2} C _ {2} ^ {2} / B _ {+})}{2} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qend{array}
$$

By setting $\eta _ { 1 } = O ( \beta \epsilon ^ { 2 } )$ and $\begin{array} { r } { T = { \cal O } ( \frac { 1 } { \epsilon ^ { 2 } \eta _ { 1 } } ) = { \cal O } ( 1 / ( \beta \epsilon ^ { 4 } ) ) } \end{array}$ we have $\mathrm { E } [ \| \nabla F _ { 1 / \hat { \rho } } ( \mathbf { v } _ { \tau } ) \| ^ { 2 } ] \leq \epsilon ^ { 2 }$ for a randomly selected $\tau \in [ T ]$

## B.7. Proof of Theorem 4

Note that the SOPA-s algorithm is just a special case of the SOX algorithm (Wang & Yang, 2022) for the more general problem min<sub>w</sub> $\begin{array} { r } { \frac { 1 } { n } \sum _ { { \bf z } _ { i } \in \mathcal { D } } \bar { f } _ { i } ( g _ { i } ( { \bf w } ) ) } \end{array}$ and the convergence proof just follows the proof of Theorem 1 in Wang & Yang (2022).

## B.8. Proof of Theorem 5

We consider the following problem:

$$
\min _ {\mathbf {w}} F (\mathbf {w}), \quad F (\mathbf {w}) = f _ {1} \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w}))\right).\tag{12}
$$

Lemma 8. $H g _ { i }$ is $C _ { g ^ { - 1 } }$ Lipschitz, $L _ { g }$ -smooth and $f _ { 1 } , f _ { 2 }$ are $C _ { f } { - } L i p s c h i t z ,$ $L _ { g ^ { - S m o o t h } } ,$ F in (12) is L -smooth and $L _ { F } =$ $L _ { f } C _ { f } ^ { 2 } C _ { g } ^ { 2 } + C _ { f } ^ { 2 } L _ { g } + \mathsf { \bar { C } } _ { f } C _ { g } L _ { f } .$

Proof. Based on the definition of $F ,$ we have

$$
\begin{array}{l} \| \nabla F (\mathbf {w}) - \nabla F (\mathbf {w} ^ {\prime}) \| \\ = \left\| \nabla f _ {1} \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w}))\right) \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} \nabla f _ {2} (g _ {i} (\mathbf {w})) \nabla g _ {i} (\mathbf {w})\right) \right. \\ \quad \left. - \nabla f _ {1} \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} ^ {\prime}))\right) \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} \nabla f _ {2} (g _ {i} (\mathbf {w} ^ {\prime})) \nabla g _ {i} (\mathbf {w} ^ {\prime})\right) \right\| \\ \leq L _ {f} \left\| \frac {1}{n} \sum_ {i \in \mathcal {S}} \nabla f _ {2} (g _ {i} (\mathbf {w})) \nabla g _ {i} (\mathbf {w}) \right\| \left\| \frac {1}{n} \sum_ {i \in \mathcal {S}} (f _ {2} (g _ {i} (\mathbf {w})) - f _ {2} (g _ {i} (\mathbf {w} ^ {\prime}))) \right\| \\ \quad + \left\| \nabla f _ {1} \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} ^ {\prime}))\right) \right\| \left\| \frac {1}{n} \sum_ {i \in \mathcal {S}} (\nabla f _ {2} (g _ {i} (\mathbf {w})) \nabla g _ {i} (\mathbf {w}) - \nabla f _ {2} (g _ {i} (\mathbf {w} ^ {\prime})) \nabla g _ {i} (\mathbf {w} ^ {\prime})) \right\|. \end{array}
$$

We can show that $\begin{array} { r } { \big \| \frac { 1 } { n } \sum _ { i \in \mathcal { S } } ( \nabla f _ { 2 } ( g _ { i } ( { \mathbf w } ) ) \nabla g _ { i } ( { \mathbf w } ) - \nabla f _ { 2 } ( g _ { i } ( { \mathbf w } ^ { \prime } ) ) \nabla g _ { i } ( { \mathbf w } ^ { \prime } ) ) \big \| \le ( C _ { f } L _ { g } + C _ { g } L _ { f } ) \| { \mathbf w } - { \mathbf w } ^ { \prime } \| } \end{array}$ . Thus,

$$
\begin{array}{r l} & {\| \nabla F (\mathbf {w}) - \nabla F (\mathbf {w} ^ {\prime}) \| \leq L _ {f} C _ {f} ^ {2} C _ {g} ^ {2} \| \mathbf {w} - \mathbf {w} ^ {\prime} \| + C _ {f} (C _ {f} L _ {g} + C _ {g} L _ {f}) \| \mathbf {w} - \mathbf {w} ^ {\prime} \|} \\ & {\qquad = (L _ {f} C _ {f} ^ {2} C _ {g} ^ {2} + C _ {f} ^ {2} L _ {g} + C _ {f} C _ {g} L _ {f}) \| \mathbf {w} - \mathbf {w} ^ {\prime} \|.} \end{array}
$$

We propose SOTA-s to solve (12).

Lemma 9. Consider a sequence $\mathbf { w } _ { t + 1 } = \mathbf { w } _ { t } - \eta \mathbf { m } _ { t }$ and the L<sub>F</sub>-smooth function F and the step size ηL $_ { F } \leq 1 / 2$

$$
F (\mathbf {w} _ {t + 1}) \leq F (\mathbf {w} _ {t}) + \frac {\eta}{2} \left\| \Delta_ {t} \right\| ^ {2} - \frac {\eta}{2} \left\| \nabla F (\mathbf {w} _ {t}) \right\| ^ {2} - \frac {\eta}{4} \left\| \mathbf {m} _ {t} \right\| ^ {2},\tag{13}
$$

where $\Delta _ { t } : = \mathbf { m } _ { t } - \nabla F ( \mathbf { w } _ { t } )$

Lemma 10. For the gradient estimator m in SOTA-s and $\Delta _ { t } = \mathbf { m } _ { t } - \nabla F ( \mathbf { w } _ { t } )$

$$
\begin{array}{r l} & {\mathrm{E} \left[ \| \Delta_ {t + 1} \| ^ {2} \right] \leq (1 - \gamma_ {2}) \mathrm{E} \left[ \| \Delta_ {t} \| ^ {2} \right] + \frac {2 L _ {F} ^ {2} \eta^ {2}}{\gamma_ {2}} \mathrm{E} \left[ \| \mathbf {m} _ {t} \| ^ {2} \right] + 1 0 \gamma_ {2} C _ {f} ^ {2} C _ {1} ^ {2} L _ {f} ^ {2} \mathrm{E} \left[ \| \Psi_ {t + 1} \| ^ {2} \right]} \\ & {\qquad + 2 0 \gamma_ {2} C _ {f} ^ {2} L _ {f} ^ {2} C _ {1} ^ {2} \mathrm{E} \left[ \frac {1}{n} \| \Xi_ {t + 1} \| ^ {2} \right] + 2 0 \gamma_ {2} C _ {f} ^ {2} L _ {f} ^ {2} C _ {1} ^ {2} \mathrm{E} \left[ \frac {1}{n} \| \mathbf {u} _ {t + 1} - \mathbf {u} _ {t} \| ^ {2} \right] + 2 \gamma_ {2} ^ {2} C _ {f} ^ {4} \left(\frac {\zeta^ {2}}{B _ {-}} + \frac {C _ {g} ^ {2}}{B _ {+}}\right)} \end{array}\tag{14}
$$

where we denote $\begin{array} { r } { \Delta _ { t } : = { \bf m } _ { t + 1 } - \nabla F ( { \bf w } _ { t } ) , \Xi _ { t } : = { \bf u } _ { t + 1 } - { \bf g } ( { \bf w } _ { t } ) \mathrm { ~ } a n d \mathrm { ~ } \Psi _ { t } : = v _ { t + 1 } - \frac { 1 } { n } \sum _ { i \in \mathcal { S } } f _ { 2 } \big ( g _ { i } ( { \bf w } _ { t } ) \big ) . } \end{array}$

Proof. Based on the update rule $\mathbf { m } _ { t + 1 } = ( 1 - \gamma _ { 2 } ) \mathbf { m } _ { t } + \gamma _ { 2 } G ( \mathbf { w } _ { t + 1 } )$ , we have

$$
\begin{array}{l} \left\| \mathbf {m} _ {t + 1} - \nabla F (\mathbf {w} _ {t + 1}) \right\| ^ {2} \\ = \left\| (1 - \gamma_ {2}) \mathbf {m} _ {t} + \gamma_ {2} \frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \nabla f _ {1} (v _ {t + 1}) \nabla f _ {2} (u _ {t} ^ {i}) \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} _ {-}) - \nabla F (\mathbf {w} _ {t + 1}) \right\| ^ {2} \\ = \left\| \underbrace {(1 - \gamma_ {2}) (\mathbf {m} _ {t} - \nabla F (\mathbf {w} _ {t}))} _ {\textcircled {a}} + \underbrace {(1 - \gamma_ {2}) (\nabla F (\mathbf {w} _ {t}) - \nabla F (\mathbf {w} _ {t + 1}))} _ {\textcircled {b}} + \gamma_ {2} \frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \nabla f _ {1} (v _ {t + 1}) \nabla f _ {2} (u _ {t} ^ {i}) \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} -) \right. \\ \left. - \gamma_ {2} \frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \nabla f _ {1} \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1}))\right) \nabla f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} -) \right. \\ \left. + \underbrace {\gamma_ {2} \left(\frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \nabla f _ {1} \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1}))\right) \nabla f _ {2} (g _ {i} ({\mathbf w} _ {t + 1})) \nabla g _ {i} ({\mathbf w} _ {t + 1} ; {\mathcal B} -) - \nabla F ({\mathbf w} _ {t + 1})\right)} _ {\textcircled {d}} \right\| ^ {2}. \end{array}
$$

We define that

$$
\begin{array}{l} \circledcirc := \gamma_ {2} \left(\frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \nabla f _ {1} (v _ {t + 1}) \nabla f _ {2} (u _ {t} ^ {i}) \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} _ {-}) \right. \\ \left. - \frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \nabla f _ {1} \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1}))\right) \nabla f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} _ {-})\right). \end{array}
$$

We define that $\Delta _ { t } : = \mathbf { m } _ { t } - \nabla F ( \mathbf { w } _ { t } )$ . Note that $\operatorname { E } \left[ \left. \bigodot , \bigodot \right. \right] = \operatorname { E } \left[ \left. \bigodot , \bigodot \right. \right] = 0$ . Then,

$$
\begin{array}{c} \mathrm{E} _ {t} \left[ \| ⓐ + ⓑ + ⓒ + ⓓ \| ^ {2} \right] = \| ⓐ \| ^ {2} + \| ⓑ \| ^ {2} + \mathrm{E} _ {t} \left[ \| ⓒ \| ^ {2} \right] + \mathrm{E} _ {t} \left[ \| ⓓ \| ^ {2} \right] + 2 \langle ⓐ, ⓑ \rangle \\ + 2 \mathrm{E} _ {t} \left[ \langle ⓐ, ⓒ \rangle \right] + 2 \mathrm{E} _ {t} \left[ \langle ⓑ, ⓒ \rangle \right] + 2 \mathrm{E} _ {t} \left[ \langle ⓒ, ⓓ \rangle \right]. \end{array}
$$

Based on the Young’s inequality for products, we have $\begin{array} { r } { 2 \left. \mathbf { a } , \mathbf { b } \right. \leq \frac { \| \mathbf { a } \| ^ { 2 } c } { 2 } + \frac { 2 \| \mathbf { b } \| ^ { 2 } } { c } \operatorname { f o r } c > 0 . } \end{array}$

$$
\begin{array}{l} \mathrm{E} _ {t} \left[ \| ⓐ + ⓑ + ⓒ + ⓓ \| ^ {2} \right] \\ \leq (1 + \gamma_ {2}) \| ⓐ \| ^ {2} + 2 (1 + 1 / \gamma_ {2}) \| ⓑ \| ^ {2} + \frac {2 + 3 \gamma_ {2}}{\gamma_ {2}} \mathrm{E} _ {t} \left[ \| ⓒ \| ^ {2} \right] + 2 \mathrm{E} _ {t} \left[ \| ⓓ \| ^ {2} \right]. \end{array}
$$

Thus, we have

$$
\mathrm{E} _ {t} [ \| \Delta_ {t + 1} \| ^ {2} ] \leq (1 - \gamma_ {2}) \| \Delta_ {t} \| ^ {2} + \frac {2 (1 + \gamma_ {2})}{\gamma_ {2}} \| ⓑ \| ^ {2} + \frac {5}{\gamma_ {2}} \mathrm{E} _ {t} [ \| ⓒ \| ^ {2} ] + 2 \mathrm{E} _ {t} [ \| ⓐ \| ^ {2} ].\tag{15}
$$

Moreover, we have

$$
\left\| ⓑ \right\| ^ {2} = (1 - \gamma_ {2}) ^ {2} \left\| \nabla F (\mathbf {w} _ {t}) - \nabla F (\mathbf {w} _ {t + 1}) \right\| ^ {2} \leq (1 - \gamma_ {2}) ^ {2} \eta^ {2} L _ {F} ^ {2} \left\| \mathbf {m} _ {t} \right\| ^ {2}.\tag{16}
$$

On the other hand,

$$
\begin{array}{l} \| \textcircled {C} \| ^ {2} \leq \frac {2 \gamma_ {2} ^ {2}}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \| \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} _ {-}) \| ^ {2} \left\| \nabla f _ {1} (v _ {t + 1}) - \nabla f _ {1} \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1}))\right) \right\| ^ {2} \left\| \nabla f _ {2} (u _ {t} ^ {i}) \right\| ^ {2} \\ + \frac {2 \gamma_ {2} ^ {2}}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \| \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} _ {-}) \| ^ {2} \left\| \nabla f _ {1} \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1}))\right) \right\| ^ {2} \left\| \nabla f _ {2} (u _ {t} ^ {i}) - \nabla f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \right\| ^ {2} \\ \leq \frac {2 \gamma_ {2} ^ {2} L _ {f} ^ {2} C _ {f} ^ {2}}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \| \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} _ {-}) \| ^ {2} \left\| v _ {t + 1} - \frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \right\| ^ {2} \\ + \frac {2 \gamma_ {2} ^ {2} L _ {f} ^ {2} C _ {f} ^ {2}}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \| \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} _ {-}) \| ^ {2} \left\| u _ {t} ^ {i} - g _ {i} (\mathbf {w} _ {t + 1}) \right\| ^ {2} \end{array}
$$

Due to $\begin{array} { r } { \mathrm { E } _ { \mathcal { B } _ { - } } \left[ \| \nabla g _ { i } ( \mathbf { w } _ { t + 1 } ; \mathcal { B } _ { - } ) \| ^ { 2 } \right] \leq C _ { g } ^ { 2 } + \zeta ^ { 2 } / \mathcal { B } _ { - } : = C _ { 1 } ^ { 2 } } \end{array}$ , we have

$$
\mathrm{E} _ {t} \left[ \| ⓒ \| ^ {2} \right] \leq \frac {2 \gamma_ {2} ^ {2} L _ {f} ^ {2} C _ {f} ^ {2} C _ {1} ^ {2}}{n} \sum_ {i \in \mathcal {S}} \mathrm{E} _ {t} \left[ \left\| v _ {t + 1} - \frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \right\| ^ {2} + \left\| u _ {t} ^ {i} - g _ {i} (\mathbf {w} _ {t + 1}) \right\| ^ {2} \right]
$$

Besides, we also have

$$
\begin{array}{l} \mathrm{E} _ {t} \left[ \| ⓐ \| ^ {2} \right] \\ \leq \gamma_ {2} ^ {2} \mathrm{E} _ {t} \left[ \left\| \frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \nabla f _ {1} \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1}))\right) \nabla f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} _ {-}) - \nabla F (\mathbf {w} _ {t + 1}) \right\| ^ {2} \right] \\ = \gamma_ {2} ^ {2} C _ {f} ^ {2} \mathrm{E} _ {t} \left[ \left\| \frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} (\nabla f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} _ {-}) - \nabla f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \nabla g _ {i} (\mathbf {w} _ {t + 1})) \right\| ^ {2} \right] \\ + \gamma_ {2} ^ {2} C _ {f} ^ {2} \mathrm{E} _ {t} \left[ \left\| \frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \nabla f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} _ {-}) - \frac {1}{n} \sum_ {i \in \mathcal {S}} \nabla f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \nabla g _ {i} (\mathbf {w} _ {t + 1}; \mathcal {B} _ {-}) \right\| ^ {2} \right] \\ \leq \frac {\gamma_ {2} ^ {2} C _ {f} ^ {4} \zeta^ {2}}{B _ {-}} + \frac {\gamma_ {2} ^ {2} C _ {f} ^ {4} C _ {g} ^ {2}}{B _ {+}}. \end{array}\tag{17}
$$

Then,

$$
\begin{array}{c} \operatorname{E} \left[ \| \Delta_ {t + 1} \| ^ {2} \right] \leq (1 - \gamma_ {2}) \operatorname{E} \left[ \| \Delta_ {t} \| ^ {2} \right] + \frac {2 L _ {F} ^ {2} \eta^ {2}}{\gamma_ {2}} \operatorname{E} \left[ \| \mathbf {m} _ {t} \| ^ {2} \right] + 1 0 \gamma_ {2} C _ {f} ^ {2} C _ {1} ^ {2} L _ {f} ^ {2} \operatorname{E} \left[ \| \Psi_ {t + 1} \| ^ {2} \right] \\ + 2 0 \gamma_ {2} C _ {f} ^ {2} L _ {f} ^ {2} C _ {1} ^ {2} \operatorname{E} \left[ \frac {1}{n} \| \Xi_ {t + 1} \| ^ {2} \right] + 2 0 \gamma_ {2} C _ {f} ^ {2} L _ {f} ^ {2} C _ {1} ^ {2} \operatorname{E} \left[ \frac {1}{n} \| \mathbf {u} _ {t + 1} - \mathbf {u} _ {t} \| ^ {2} \right] + 2 \gamma_ {2} ^ {2} C _ {f} ^ {4} \left(\frac {\zeta^ {2}}{B _ {-}} + \frac {C _ {g} ^ {2}}{B _ {+}}\right) \end{array}
$$

where we denote $\Xi _ { t } : = \mathbf { u } _ { t } - \mathbf { g } ( \mathbf { w } _ { t } )$ and $\begin{array} { r } { \Psi _ { t } : = v _ { t } - \frac { 1 } { n } \sum _ { i \in S } f _ { 2 } ( g _ { i } ( \mathbf { w } _ { t } ) ) } \end{array}$

Lemma 11. For the function value estimator $v _ { t + 1 }$ in SOTA-s and $\begin{array} { r } { \Psi _ { t } : = v _ { t } - \frac { 1 } { n } \sum _ { i \in S } f _ { 2 } \big ( g _ { i } ( \mathbf { w } _ { t } ) \big ) } \end{array}$

$$
\begin{array}{r l} & {\mathrm{E} _ {t} \left[ \| \Psi_ {t + 1} \| ^ {2} \right] \leq (1 - \gamma_ {1}) \| \Psi_ {t} \| ^ {2} + \frac {2 C _ {f} ^ {2} C _ {g} ^ {2} \eta^ {2}}{\gamma_ {1}} \| \mathbf {m} _ {t} \| ^ {2} + 5 \gamma_ {1} C _ {f} ^ {2} \mathrm{E} _ {t} \left[ \frac {1}{n} \| \Xi_ {t + 1} \| ^ {2} \right]} \\ & {\qquad + \frac {1 0 \gamma_ {1} C _ {f} ^ {2}}{n} \mathrm{E} _ {t} \left[ \| \mathbf {u} _ {t} - \mathbf {u} _ {t + 1} \| ^ {2} \right] + \frac {2 \gamma_ {1} ^ {2} C _ {f} ^ {2}}{B _ {+}}.} \end{array}\tag{18}
$$

Proof. According to the update of v in SOTA-s, we have

$$
\begin{array}{l} \left\| v _ {t + 1} - \frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \right\| ^ {2} = \left\| (1 - \gamma_ {1}) v _ {t} + \gamma_ {1} \frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} f _ {2} (u _ {t} ^ {i}) - \frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) \right\| ^ {2} \\ = \left\| (1 - \gamma_ {1}) \left(v _ {t} - \frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t}))\right) + (1 - \gamma_ {1}) \left(\frac {1}{n} \sum_ {i \in \mathcal {S}} (f _ {2} (g _ {i} (\mathbf {w} _ {t})) - f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})))\right) \right. \\ \left. + \gamma_ {1} \left(\frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} f _ {2} (u _ {t} ^ {i}) - \frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1}))\right) + \gamma_ {1} \left(\frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1})) - \frac {1}{n} \sum_ {i \in \mathcal {S}} f _ {2} (g _ {i} (\mathbf {w} _ {t + 1}))\right) \right\| ^ {2}. \end{array}
$$

Denoting $\begin{array} { r } { \Psi _ { t } : = \left\| v _ { t } - \frac { 1 } { n } \sum _ { i \in S } f _ { 2 } ( g _ { i } ( \mathbf { w } _ { t } ) ) \right\| ^ { 2 } } \end{array}$ , we have

$$
\begin{array}{r l} & {\mathrm{E} _ {t} \left[ \| \Psi_ {t + 1} \| ^ {2} \right]} \\ & {\leq (1 - \gamma_ {1}) \| \Psi_ {t} \| ^ {2} + \frac {2 (1 - \gamma_ {1}) C _ {f} ^ {2} C _ {g} ^ {2} \eta^ {2}}{\gamma_ {1}} \| \mathbf {m} _ {t} \| ^ {2} + \frac {(2 + 3 \beta) C _ {f} ^ {2}}{\gamma_ {1}} \gamma_ {1} ^ {2} \mathrm{E} _ {t} \left[ \frac {1}{B _ {+}} \sum_ {i \in \mathcal {B} _ {+}} \left\| u _ {t} ^ {i} - g _ {i} (\mathbf {w} _ {t + 1}) \right\| ^ {2} \right] + \frac {2 \gamma_ {1} ^ {2} C _ {f} ^ {2}}{B _ {+}}} \\ & {\leq (1 - \gamma_ {1}) \| \Psi_ {t} \| ^ {2} + \frac {2 C _ {f} ^ {2} C _ {g} ^ {2} \eta^ {2}}{\gamma_ {1}} \| \mathbf {m} _ {t} \| ^ {2} + \frac {5 \gamma_ {1} C _ {f} ^ {2}}{n} \mathrm{E} _ {t} \left[ \| \mathbf {u} _ {t} - \mathbf {g} (\mathbf {w} _ {t + 1}) \| ^ {2} \right] + \frac {2 \gamma_ {1} ^ {2} C _ {f} ^ {2}}{B _ {+}}} \\ & {\leq (1 - \gamma_ {1}) \| \Psi_ {t} \| ^ {2} + \frac {2 C _ {f} ^ {2} C _ {g} ^ {2} \eta^ {2}}{\gamma_ {1}} \| {\mathbf m} _ {t} \| ^ {2} + \frac {1 0 \gamma_ {1} C _ {f} ^ {2}}{n} \mathrm{E} _ {t} \left[ \| {\mathbf u} _ {t + 1} - {\mathbf g} (\mathbf w _ {t + 1}) \| ^ {2} \right] + \frac {1 0 \gamma_ {1} C _ {f} ^ {2}}{n} \mathrm{E} _ {t} \left[ \| {\mathbf u} _ {t} - {\mathbf u} _ {t + 1} \| ^ {2} \right] + \frac {2 \gamma_ {1} ^ {2} C _ {f} ^ {2}}{B _ {+}}.} \end{array}
$$

ProofofTheorem 5. Based on (13), we have

$$
\operatorname{E} \left[ F (\mathbf {w} _ {t + 1}) - F _ {\mathrm{inf}} \right] \leq \operatorname{E} \left[ F (\mathbf {w} _ {t}) - F _ {\mathrm{inf}} \right] + \frac {\eta}{2} \operatorname{E} \left[ \| \Delta_ {t} \| ^ {2} \right] - \frac {\eta}{2} \operatorname{E} \left[ \| \nabla F (\mathbf {w} _ {t}) \| ^ {2} \right] - \frac {\eta}{4} \operatorname{E} \left[ \| \mathbf {m} _ {t} \| ^ {2} \right]\tag{19}
$$

Re-arranging the terms and telescoping (19) from $t = 1$ to T leads to

$$
\frac {1}{T} \sum_ {t = 1} ^ {T} \operatorname{E} \left[ \| \nabla F (\mathbf {w} _ {t}) \| ^ {2} \right] \leq \frac {2 \operatorname{E} \left[ F (\mathbf {w} _ {1}) - F _ {\inf} \right]}{\eta T} + \underbrace {\frac {1}{T} \sum_ {t = 1} ^ {T} \operatorname{E} \left[ \| \Delta_ {t} \| ^ {2} \right]} _ {:= (\widehat {\mathsf {e}})} - \frac {1}{2 T} \sum_ {t = 1} ^ {T} \operatorname{E} \left[ \| \mathbf {m} _ {t} \| ^ {2} \right].\tag{20}
$$

Based on (14), the term ⃝e can be upper bounded as

$$
\begin{array}{l} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \Delta_ {t} \| ^ {2} \right] \leq \frac {\mathrm{E} \left[ \| \Delta_ {1} \| ^ {2} \right]}{\gamma_ {2} T} + \frac {2 L _ {F} ^ {2} \eta^ {2}}{\gamma_ {2} ^ {2}} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \mathbf {m} _ {t} \| ^ {2} \right] + 2 \gamma_ {2} C _ {f} ^ {4} \left(\frac {\zeta^ {2}}{B _ {-}} + \frac {C _ {g} ^ {2}}{B _ {+}}\right) \\ \qquad + 2 0 C _ {f} ^ {2} C _ {1} ^ {2} L _ {f} ^ {2} \sum_ {t = 1} ^ {T} \frac {1}{n} \mathrm{E} [ \| \mathbf {u} _ {t + 1} - \mathbf {u} _ {t} \| ^ {2} ] + 2 0 C _ {f} ^ {2} C _ {1} ^ {2} L _ {f} ^ {2} \left(\underbrace {\frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \Psi_ {t + 1} \| ^ {2} \right]} _ {:= ⓕ} + \underbrace {\frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \frac {1}{n} \| \Xi_ {t + 1} \| ^ {2} \right]} _ {:= ⓖ}\right). \end{array}
$$

Based on Lemma 2 in Wang & Yang (2022), the term $\textcircled{9}$ can be upper bounded as

$$
\begin{array}{r l} & {\frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \frac {1}{n} \left\| \Xi_ {t + 1} \right\| ^ {2} \right] \leq \frac {4 n \mathrm{E} \left[ \frac {1}{n} \left\| \Xi_ {2} \right\| ^ {2} \right]}{\gamma_ {0} B _ {+} T} + 2 0 C _ {g} ^ {2} \left(\frac {n \eta}{\gamma_ {0} B _ {+}}\right) ^ {2} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \left\| \mathbf {m} _ {t + 1} \right\| ^ {2} \right]} \\ & {\qquad + \frac {8 \gamma_ {0} \sigma^ {2}}{B _ {-}} - \frac {1}{\gamma_ {0} B _ {+}} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \left\| \mathbf {u} ^ {t + 1} - \mathbf {u} ^ {t} \right\| ^ {2} \right].} \end{array}
$$

With $1 / ( \gamma _ { 0 } B _ { + } ) \geq \operatorname* { m a x } ( 1 0 C _ { f } ^ { 2 } / n , 1 / n )$ , based on (18), the term $\textcircled{1}$ can be bounded as

$$
\begin{array}{l} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \Psi_ {t + 1} \| ^ {2} \right] \leq \frac {\mathrm{E} \left[ \| \Psi_ {2} \| ^ {2} \right]}{\gamma_ {1} T} + \frac {2 C _ {f} ^ {2} C _ {g} ^ {2} \eta^ {2}}{\gamma_ {1} ^ {2}} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \mathbf {m} _ {t + 1} \| ^ {2} \right] + 5 C _ {f} ^ {2} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \frac {1}{n} \| \Xi_ {t + 2} \| ^ {2} \right] + \frac {2 \gamma_ {1} C _ {f} ^ {2}}{B _ {+}} \\ \leq \frac {\mathrm{E} \left[ \| \Psi_ {2} \| ^ {2} \right]}{\gamma_ {1} T} + \frac {2 C _ {f} ^ {2} C _ {g} ^ {2} \eta^ {2}}{\gamma_ {1} ^ {2}} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E.} \left[ \| \mathbf {m} _ {t + 1} \| ^ {2} \right] + \frac {2 \gamma_ {1} C _ {f} ^ {2}}{B _ {+}} + \frac {2 0 C _ {f} ^ {2} n \mathrm{E.}}{\gamma_ {0} B _ {+} T} \\ + 1 0 0 C _ {f} ^ {2} C _ {g} ^ {2} \left(\frac {n \eta}{\gamma_ {0} B _ {+}}\right) ^ {2} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E.} \left[ \| \mathbf {m} _ {t + 2} \| ^ {2} \right] + \frac {4 0 C _ {f} ^ {2} \gamma_ {0} \sigma^ {2}}{B _ {-}}. \end{array}
$$

Plug the upper bounds of $\textcircled{1}$ and $\textcircled{9}$ into (20).

$$
\begin{array}{r l} & {\frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \nabla F (\mathbf {w} _ {t}) \| ^ {2} \right]} \\ & {\leq \frac {2 \mathrm{E} \left[ F (\mathbf {w} _ {1}) - F _ {\mathrm{inf}} \right]}{\eta T} + \frac {\mathrm{E} \left[ \| \Delta_ {1} \| ^ {2} \right]}{\gamma_ {2} T} + 2 \gamma_ {2} C _ {f} ^ {4} \left(\frac {\zeta^ {2}}{B _ {-}} + \frac {C _ {g} ^ {2}}{B _ {+}}\right)} \\ & {+ \frac {4 0 n C _ {f} ^ {2} C _ {1} ^ {2} L _ {f} ^ {2} \mathrm{E} \left[ \frac {1}{n} \| \Xi_ {2} \| ^ {2} \right]}{\gamma_ {0} B _ {+} T} - \left(\frac {1}{2} - \frac {2 L _ {F} ^ {2} \eta^ {2}}{\gamma_ {2} ^ {2}}\right) \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \mathbf {m} _ {t} \| ^ {2} \right]} \\ & {+ 2 0 0 C _ {f} ^ {2} C _ {g} ^ {2} C _ {1} ^ {2} L _ {f} ^ {2} \left(\frac {n \eta}{\gamma_ {0} B _ {+}}\right) ^ {2} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \mathbf {m} _ {t + 1} \| ^ {2} \right] + \frac {8 0 \gamma_ {0} C _ {f} ^ {2} C _ {1} ^ {2} L _ {f} ^ {2} \sigma^ {2}}{B _ {-}}} \\ & {+ \frac {1 0 C _ {f} ^ {2} C _ {1} ^ {2} L _ {f} ^ {2} \mathrm{E} \left[ \| \Psi_ {2} \| ^ {2} \right]}{\gamma_ {1} T} + \frac {2 0 C _ {f} ^ {4} C _ {g} ^ {2} C _ {1} ^ {2} L _ {f} ^ {2} \eta^ {2}}{\gamma_ {1} ^ {2}} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \mathbf {m} _ {t + 1} \| ^ {2} \right] + \frac {2 0 \gamma_ {1} C _ {f} ^ {4} C _ {1} ^ {2} L _ {f} ^ {2}}{B _ {+}}} \\ & {+ \frac {2 0 0 n C _ {f} ^ {4} C _ {1} ^ {2} L _ {f} ^ {2} \mathrm{E} \left[ \frac {1}{n} \| \Xi_ {3} \| ^ {2} \right]}{\gamma_ {0} B _ {+} T} + 1 0 0 0 C _ {f} ^ {4} C _ {1} ^ {2} C _ {g} ^ {2} \left(\frac {n \eta}{\gamma_ {0} B _ {+}}\right) ^ {2} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \mathbf {m} _ {t + 2} \| ^ {2} \right] + \frac {4 0 0 \gamma_ {0} C _ {f} ^ {4} C _ {1} ^ {2} L _ {f} ^ {2} \sigma^ {2}}{B _ {-}}.} \end{array}
$$

$$
\begin{array}{l} \text {If we choose} \eta \leq \min \left\{\frac {\gamma_ {2}}{4 L _ {F}}, \frac {\gamma_ {0} B _ {+}}{4 0 n C _ {f} C _ {g} C _ {1} \sqrt {L _ {f} ^ {2} + 5 C _ {f} ^ {2}}}, \frac {\gamma_ {1}}{1 5 C _ {f} ^ {2} C _ {g} C _ {1} L _ {f}} \right\}, \text {we have} \\ \quad - \left(\frac {1}{2} - \frac {2 L _ {F} ^ {2} \eta^ {2}}{\gamma_ {2} ^ {2}}\right) \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \mathbf {m} _ {t} \| ^ {2} \right] + 2 0 0 C _ {f} ^ {2} C _ {g} ^ {2} C _ {1} ^ {2} L _ {f} ^ {2} \left(\frac {n \eta}{\gamma_ {0} B _ {+}}\right) ^ {2} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \mathbf {m} _ {t + 1} \| ^ {2} \right] \\ \quad + \frac {2 0 C _ {f} ^ {4} C _ {g} ^ {2} C _ {1} ^ {2} L _ {f} ^ {2} \eta^ {2}}{\gamma_ {1} ^ {2}} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \mathbf {m} _ {t + 1} \| ^ {2} \right] + 1 0 0 0 C _ {f} ^ {4} C _ {1} ^ {2} C _ {g} ^ {2} \left(\frac {n \eta}{\gamma_ {0} B _ {+}}\right) ^ {2} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathrm{E} \left[ \| \mathbf {m} _ {t + 2} \| ^ {2} \right] \\ \leq \frac {\mathrm{E} \left[ \| \mathbf {m} _ {T + 1} \| ^ {2} \right] + \mathrm{E} \left[ \| \mathbf {m} _ {T + 2} \| ^ {2} \right]}{8 T}. \end{array}
$$

Besides, Lemma 2 in Wang & Yang (2022) and Lemma 11 imply that

$$
\begin{array}{r l} & {\mathrm{E} \left[ \frac {1}{n} \left\| \Xi_ {2} \right\| ^ {2} \right] \leq \mathrm{E} \left[ \frac {1}{n} \left\| \Xi_ {1} \right\| ^ {2} \right] + \frac {5 n \eta^ {2} C _ {g} ^ {2}}{\gamma_ {0} B _ {+}} \mathrm{E} \left[ \left\| \mathbf {m} _ {1} \right\| ^ {2} \right] + \frac {2 \gamma_ {0} ^ {2} \sigma^ {2} B _ {+}}{n B _ {-}}} \\ & {\qquad \leq \mathrm{E} \left[ \frac {1}{n} \left\| \Xi_ {1} \right\| ^ {2} \right] + \frac {\eta C _ {g}}{8 C _ {f} C _ {1} \sqrt {L _ {f} ^ {2} + 5 C _ {f} ^ {2}}} \mathrm{E} \left[ \left\| \mathbf {m} _ {1} \right\| ^ {2} \right] + \frac {2 \gamma_ {0} ^ {2} \sigma^ {2} B _ {+}}{n B _ {-}},} \\ & {\mathrm{E} \left[ \frac {1}{n} \left\| \Xi_ {3} \right\| ^ {2} \right] \leq \mathrm{E} \left[ \frac {1}{n} \left\| \Xi_ {1} \right\| ^ {2} \right] + \frac {\eta C _ {g}}{8 C _ {f} C _ {1} \sqrt {L _ {f} ^ {2} + 5 C _ {f} ^ {2}}} \left(\mathrm{E} \left[ \left\| \mathbf {m} _ {1} \right\| ^ {2} + \left\| \mathbf {m} _ {2} \right\| ^ {2} \right]\right) + \frac {4 \gamma_ {0} ^ {2} \sigma^ {2} B _ {+}}{n B _ {-}},} \\ & {\qquad \mathrm{E} \left[ \| \Psi_ {2} \| ^ {2} \right] \leq \mathrm{E} \left[ \| \Psi_ {1} \| ^ {2} \right] + \frac {2 C _ {g} \eta}{1 5 C _ {1} L _ {f}} \| \mathbf {m} _ {1} \| ^ {2} + 5 \gamma_ {1} C _ {f} ^ {2} \mathrm{E} \left[ \frac {1}{n} \| \Xi_ {t + 1} \| ^ {2} \right] + \frac {2 \gamma_ {1} ^ {2} C _ {f} ^ {2}}{B _ {+}}.} \end{array}
$$

If we initialize $\mathbf { m } _ { 1 } = 0$ , then $\mathrm { E } \left\lceil \left\| \mathbf { m } _ { t } \right\| ^ { 2 } \right\rceil \leq C _ { f } ^ { 2 } C _ { 1 } ^ { 2 }$ for any $t \geq 1$ . We define that $\Lambda _ { F , 1 } = \operatorname { E } \left[ F ( \mathbf { w } _ { 1 } ) - F _ { \mathrm { i n f } } \right] < + \infty ,$ Λ∆,1 = E h∥∆1∥<sup>2</sup>i < +∞, ΛΞ,2 = E h <sup>1</sup><sub>n</sub> ∥Ξ2∥<sup>2</sup>i < +∞, ΛΞ,3 = E h <sup>1</sup><sub>n</sub> ∥Ξ2∥<sup>2</sup>i < +∞, Λ<sup>2</sup><sub>Ψ</sub> = E h∥Ψ2∥<sup>2</sup>i < +∞. Then,

$$
\begin{array} { l }\Lambda _ { \Delta , 1 } = \mathrm{E} \left[ \| \Delta _ { 1 } \| ^ { 2 } \right] <   + \infty ,   \Lambda _ { \Xi , 2 } = \mathrm{E} \left[ \frac { 1 } { n } \| \Xi _ { 2 } \| ^ { 2 } \right] <   + \infty ,   \Lambda _ { \Xi , 3 } = \mathrm{E} \left[ \frac { 1 } { n } \| \Xi _ { 2 } \| ^ { 2 } \right] <   + \infty ,   \Lambda _ { \Psi } ^ { 2 } = \mathrm{E} \left[ \| \Psi _ { 2 } \| ^ { 2 } \right] <   + \infty .\\\frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathrm{E} \left[ \| \nabla F ( \mathbf { w } _ { t } ) \| ^ { 2 } \right]\\\leq \frac { 2 \Lambda _ { F , 1 } } { \eta T } + \frac { \Lambda _ { \Delta , 1 } } { \gamma _ { 2 } T } + \frac { 4 0 n C _ { f } ^ { 2 } C _ { 1 } ^ { 2 } L _ { f } ^ { 2} \Lambda _ { \Xi , 2 } } { \gamma _ { 0 } B _ { + } T } + \frac { 1 0 C _ { f } ^ { 2 } C _ { 1 } ^ { 2 } L _ { f } ^ { 2} \Lambda _ { \Psi } ^ { 2 } } { \gamma _ { 1 } T } + \frac { 2 0 0 n C _ { f } ^ { 4 } C _ { 1 } ^ { 2 } L _ { f } ^ { 2} \Lambda _ { \Xi , 3 } } { \gamma _ { 0 } B _ { + } T }\\+   2 \beta C _ { f } ^ { 4 } \left( \frac { \zeta ^ { 2 } } { B _ { - } } + \frac { C _ { g } ^ { 2 } } { B _ { + } } \right) + \frac { 8 0 \gamma _ { 0 } C _ { f } ^ { 2 } C _ { 1 } ^ { 2 } L _ { f } ^ { 2 } \sigma ^ { 2 } } { B _ { - } } + \frac { 2 0 \gamma _ { 1 } C _ { f } ^ { 4 } C _ { 1 } ^ { 2 } L _ { f } ^ { 2 } } { B _ { + } } + \frac { 4 0 0 \gamma _ { 0 } C _ { f } ^ { 4 } C _ { 1 } ^ { 2 } L _ { f } ^ { 2 } \sigma ^ { 2 } } { B _ { - } } + \frac { C _ { f } ^ { 2 } C _ { 1 } ^ { 2 } } { 4 T } .\\\textsf  S e t ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~&\\\eta \leq \operatorname * { m i n } \left\{ \frac { \gamma _ { 2 } } { 4 L _ { F } }, \frac { \gamma _ { 0 } B _ { + } } { 4 0 n C _ { f } C _ { g } C _ { 1 } \sqrt { L _ { f } ^ { 2 } + 5 C _ { f } ^ { 2 }} }, \frac { \gamma _ { 1 } } { 1 5 C _ { f } ^ { 2 } C _ { g } C _ { 1 } L _ { f } } \right\} ,\\T = \operatorname * { m a x } \left\{ \right. \frac { 1 6 0 0 \Lambda _ { F , 1} L _ { F} C _ { f } ^ { 4 } ( \zeta ^ { 2 } + C _ { g } ^ { 2 } ) } { \operatorname* { m i n } \{ B _ {-} , B _ { +} \} \epsilon ^ { 4 } }, \frac { 3 2 0 0 0 0 n \Lambda _ { F , 1} C _ { f } ^ { 3 } C _ { g } C _ { 1 } ^ { 3} L _ { f } ^ { 2 } ( 1 + 5 C _ { f } ^ { 2 } ) \sqrt { L _ { f } ^ { 2 } + 5 C _ { f } ^ { 2} }\sigma ^ { 2 }}{ B _ {-} B _ { + } \epsilon ^ { 4 }} ,\\\frac { 6 0 0 0 0 \Lambda _ { F , 1} C _ { f } ^ { 6 } C _ { g } C _ { 1 } ^ { 3} L _ { f } ^ { 3 }}{ B _ { + } \epsilon ^ { 4 }} , \frac { 2 0 0 C _ { f } ^ { 4 } ( \zeta ^ { 2 } + C _ { g } ^ { 2} ) \Lambda _ { \Delta , 1 } } { \operatorname* { m i n} \{ B _ {-} , B _ { +} \} \epsilon ^ { 4 }} , \frac  1 6 0 0 0 0 n C _ { f } ^ { 4 } C _ { 1 } ^ { 4} L _ { f } ^ { 4} \sigma ^ { 2 } ( 1 + 5 C _ { f } ^ { 2} ) \Lambda _  \Xi , - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\\\frac { 2 0 0 0 0 C _ { f } ^ { 6 } C _ { 1 } ^ { 4} L _ { f } ^ { 4} \Lambda _ { \Psi } ^ { 2 }}{ B _ { + } \epsilon ^ { 4 }} , \frac  8 0 0 0 0 0 n C _ { f } ^ { 6 } C _ { 1 } ^ { 4} L _ { f } ^ { 4} ( 1 + 5 C _ { f } ^ { 2}) \Lambda _ { \Xi , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , .}{B _ {-} B _ {-} E ^ {\prime}} .\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\.&.\\. | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A | | | A |\end{array}
$$

Then, we have $\begin{array} { r } { \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \operatorname { E } \left[ \left\| \nabla F ( \mathbf { w } _ { t } ) \right\| ^ { 2 } \right] \leq \epsilon ^ { 2 } } \end{array}$

□

## C. Optimization of CVaR-estimator of TPAUC

We have the following estimator

$$
F (\mathbf {w}) = \min _ {s ^ {\prime} \in \mathbb {R}} s ^ {\prime} + \frac {1}{n _ {+} \alpha} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} (\min _ {s _ {i}} s _ {i} + \frac {1}{\beta} g _ {i} (\mathbf {w}; s _ {i}) - s ^ {\prime}) _ {+}.
$$

It is not difficult to show that the above estimator is equlvalent to

$$
F (\mathbf {w}) = \min _ {s ^ {\prime} \in \mathbb {R}, \mathbf {s} \in \mathbb {R} ^ {n _ {+}}} s ^ {\prime} + \frac {1}{n _ {+} \alpha} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} (s _ {i} + \frac {1}{\beta} g _ {i} (\mathbf {w}; s _ {i}) - s ^ {\prime}) _ {+}.
$$

The reason is that $( \operatorname* { m i n } _ { x } f ( x ) - s ) _ { + } = \operatorname* { m i n } _ { x } ( f ( x ) - s ) _ { + }$ . Using the conjugate of $[ \cdot ] _ { + }$ , we have

$$
\min _ {\mathbf {w}, \mathbf {s} \in \mathbb {R} ^ {n +}, s ^ {\prime}} \max _ {\mathbf {u} \in [ 0, 1 ] ^ {n +}} \underbrace {s ^ {\prime} + \frac {1}{n _ {+} \alpha} \sum_ {\mathbf {x} _ {i} \in \mathcal {S} _ {+}} u _ {i} (s _ {i} + \frac {1}{\beta} g _ {i} (\mathbf {w} ; s _ {i}) - s ^ {\prime})} _ {F (\mathbf {w}, \mathbf {s}, s ^ {\prime}, \mathbf {u})}.
$$

Let $\bar { \bf w } = ( { \bf w } , { \bf s } , s ^ { \prime } )$ . We consider the function $F ( \bar { \bf w } , { \bf u } )$ , which can be proved to be weakly convex and concave. Hence, we can use the stagewise proximal point method to solve the problem (Rafique et al., 2020). At the k-th stage, we solve the following problem approximately:

$$
\min _ {\bar {\mathbf {w}}} \max _ {\mathbf {u} \in [ 0, 1 ]} F _ {k} (\bar {\mathbf {w}}, \mathbf {u}) = F (\bar {\mathbf {w}}, \mathbf {u}) + \frac {1}{2 \gamma} \| \bar {\mathbf {w}} - \bar {\mathbf {w}} _ {1} ^ {k} \| ^ {2}
$$

We will use stochastic primal-dual algorithm for solving $F _ { k }$ . However, for s we use stochastic coordinate gradient descent update, and for u we also use stochastic coordinate gradient descent update. Let $\nabla _ { 1 } F , \nabla _ { 2 } F , \nabla _ { 3 } F , \nabla _ { 4 } F$ denote the partial

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 4 SOTA

1: Set  $s_{0}=0, s_{0}^{\prime}=0, u_{0}=1$  and initialize  $w_{0}$ 

2: for  $k=1,\ldots,K$  do

3: Let  $w_{1}^{k}=w_{k-1}, s_{1}^{k}=s_{k-1}, s_{k}^{\prime}=s_{k-1}^{\prime}, u_{1}^{k}=u_{k-1}$ 

4: for  $t=1,\ldots,T_{k}$  do

5: Sample  $B_{+}\subset S_{+}$  and  $B_{-}\subset S_{-}$ 

6: Update  $w_{t+1}, s_{t+1}, s_{t+1}^{\prime}, u_{t+1}$  according to (21)

7: end for

8: Let  $w_{k}, s_{k}, s_{k}^{\prime}, u_{k}$  be the average of  $w_{t}, s_{t}, s_{t}^{\prime}, u_{t}$ , respectively

9: end for

gradient of F in terms of w, s, s', u, respectively. We consider the following update:

 $w_{t+1}=\arg\min_{w}w^{\top}\nabla_{1}F(\bar{w}_{t},u_{t};\xi_{t})+\frac{1}{2\eta_{1}}\|w-w_{t}\|^{2}+\frac{1}{2\gamma}\|w-w_{1}^{k}\|^{2}$ $s_{t+1,i}=\arg\min_{s}sU_{i}\nabla_{2}F(\bar{w}_{t},u_{t};\xi_{t})+\frac{1}{2\eta_{2}}|s-s_{t,i}|^{2}+\frac{1}{2\gamma}|s-s_{1,i}^{k}|^{2},\forall x_{i}\in B_{+}$ $s_{t+1}^{\prime}=\arg\min_{s^{\prime}}\nabla_{3}F(\bar{w}_{t},u_{t};\xi_{t})+\frac{1}{2\eta_{3}}|s^{\prime}-s_{t}^{\prime}|^{2}+\frac{1}{2\gamma}|s^{\prime}-s_{k,1}^{\prime}|^{2}$ $u_{t+1,i}=[u_{t,i}+\frac{n_{+}}{B_{+}}\eta_{4}U_{i}\nabla_{4}F(\bar{w}_{t},u_{t};\xi_{t})]_{[0,1]},\forall x_{i}\in B_{+}$ 

where  $U_{i}\in R^{1\times d}$  denotes an operation that chooses the i-th coordinate of a vector. Note that different from (Rafique et al., 2020), we use stochastic coordinate descent (ascent) to update  $s_{t+1}(u_{t+1})$ .

Next, we present the stochastic gradients.

 $\nabla_{1}F(\bar{w}_{t},u_{t};\xi_{t})=\frac{1}{B_{+}B_{-}\alpha\beta}\sum_{x_{i}\in B_{+}}\sum_{x_{j}\in B_{-}}u_{i}\mathbb{I}(L(w_{t};x_{i},x_{j})-s_{t,i}&gt;0)\nabla L(w_{t};x_{i},x_{j})$ $U_{i}\nabla_{2}F(\bar{w}_{t},u_{t};\xi_{t})=\frac{1}{n_{+}\alpha}u_{t,i}(1-\frac{1}{B_{-}\beta}\sum_{x_{j}\in B_{-}}\mathbb{I}(L(w_{t};x_{i},x_{j}))&gt;s_{t,i})$ $\nabla_{3}F(\bar{w}_{t},u_{t};\xi_{t})=1-\frac{1}{B_{+}\alpha}\sum_{x_{i}\in B_{+}}u_{t,i}$ $U_{i}\nabla_{4}F(\bar{w}_{t},u_{t};\xi_{t})=\frac{1}{n_{+}\alpha}(s_{t,i}-s'')+\frac{1}{B_{-}\beta}\sum_{x_{j}\in B_{-}}(L(w_t;x_i,x_j)-s_{t,i})_+)$ 

We have

 $E[\nabla_1F_k(\bar{w}_t,u_t;\xi_t)]=\nabla_1F_k(\bar{w}_t,u_t),\quad E[\|\nabla_1F_k(\bar{w}_t,u_t;\xi_t)\|^2]\leq\frac{C}{\alpha^2\beta^2}$ $E[n_+U_i^\top U_i\nabla_2F_k(\bar{w}_t,u_t;\xi_t)]=\nabla_2F_k(\bar{w}_t,u_t),\quad E[\|U_i\nabla_2F_k(\bar{w}_t,u_t;\xi_t)\|^2]\leq\frac{1}{n_+^2\alpha^2}(1+\frac{1}{\beta})^2$ $E[\nabla_3F_k(\bar{w}_t,u_t;\xi_t)]=\nabla_3F_k(\bar{w}_t,u_t),\quad E[\|\nabla_3F_k(\bar{w}_t,u_t;\xi_t)\|^2]\leq(1+\frac{1}{\alpha})^2$ $E[n_+U_i^\top U_i\nabla_4F_k(\bar{w}_t,u_t;\xi_t)]=\nabla_4F_k(\bar{w}_t,u_t),\quad E[\|U_i\nabla_4F(\bar{w}_t,u_t;\xi_t)\|^2]\leq\frac{4C^2}{n_+^2\alpha^2}(1+\frac{1}{\beta})^2$ 

where we assume  $\max(|s_t'|,|s_t,i|,L(w_t;x_i,x_j),\|\nabla L(w_t;x_i,x_j)|)\leq C$ . The algorithm is shown in Algorithm 4.
</div>

## C.1. Analysis

Theorem 6. Assume there exists $C > 0$ such that max $\bigl ( | s _ { t } ^ { \prime } | , | s _ { t , i } | , L ( \mathbf { w } _ { t } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) , \| \nabla L ( \mathbf { w } _ { t } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } ) \| \bigr ) \leq C$ at every stage. Let $1 / \gamma \geq \rho , \eta _ { 1 } ^ { k } = \eta _ { 3 } ^ { k } = \eta _ { 4 } ^ { k } = \eta _ { 2 } ^ { k } B _ { + } / n _ { + } = \eta _ { k } \propto 1 / k , \bar { T } _ { k } \propto \dot { k } ^ { 2 }$ . SOTA ensures that after $T = \bar { O ( 1 / \epsilon ^ { 6 } ) }$ iterations we can find an ϵ-nearly stationary solution for mi ${ \bf \delta } _ { } \mathbf { w } , { \bf s } , s ^ { \prime }  F ( \mathbf { w } , { \bf s } , s ^ { \prime } )$

We first show that $F ( \bar { \bf w } , { \bf u } )$ is weakly convex in terms of w¯ for any u.

Lemma 12. Under Assumption 2, then $F ( \bar { \mathbf { w } } , \mathbf { u } ) ~ i s ~ \rho / ( \alpha \beta )$ -weakly convex in terms ofw¯ for any u, where $\rho$ is equal to the smoothness parameter of $L ( \mathbf { w } ; \mathbf { x } _ { i } , \mathbf { x } _ { j } )$ .

Proof. Following similar analysis of Lemma 2, we can show that $\begin{array} { r } { F ( \bar { \mathbf { w } } , \mathbf { u } ) + \frac { \rho } { 2 \alpha \beta } \| \bar { \mathbf { w } } \| ^ { 2 } = F ( \bar { \mathbf { w } } , \mathbf { u } ) + \frac { 1 } { n _ { + } \alpha } \sum _ { i } { u _ { i } ( \frac { \rho } { 2 \beta } \| \mathbf { w } \| ^ { 2 } + } } \end{array}$ $\begin{array} { r } { \frac { \rho } { 2 \beta } | s _ { i } | ^ { 2 } + \frac { \rho } { 2 \beta } | s ^ { \prime } | ^ { 2 } ) + \frac { \rho } { 2 n _ { + } \alpha \beta } \sum _ { i } ( 1 - u _ { i } ) ( \| \mathbf { w } \| ^ { 2 } + | s _ { i } | ^ { 2 } + | s ^ { \prime } | ^ { 2 } ) + \frac { ( n _ { + } - 1 ) } { 2 n _ { + } \alpha \beta } \| \mathbf { s } \| ^ { 2 } } \end{array}$ is jointly convex in terms $\mathbf { w } , \mathbf { s } , s ^ { \prime }$ for any $\mathbf { u } \in [ 0 , 1 ]$ . Then $F ( \bar { \bf w } , { \bf u } )$ is $\begin{array} { r } { \rho ^ { \prime } = \frac { \rho } { \alpha \beta } } \end{array}$ -weakly convex in terms of w¯ for any u. □

We need the following lemma for analysis.

Lemma 13. Consider the proximal gradient update

$$
\mathbf {x} _ {t + 1} = \arg \min \mathbf {x} ^ {\top} G _ {t} + \frac {1}{2 \eta} \| \mathbf {x} - \mathbf {x} _ {t} \| ^ {2} + g (\mathbf {x}),
$$

we have

$$
\begin{array}{r l} & {(\mathbf {x} _ {t} - \mathbf {x}) ^ {\top} G _ {t} + g (\mathbf {x} _ {t}) - g (\mathbf {x}) + \frac {1}{2 \gamma} \| \mathbf {x} - \mathbf {x} _ {t + 1} \| ^ {2}} \\ & {\leq \eta \| G _ {t} \| ^ {2} + \frac {1}{2 \eta} (\| \mathbf {x} - \mathbf {x} _ {t} \| ^ {2} - \| \mathbf {x} - \mathbf {x} _ {t + 1} \| ^ {2}) + g (\mathbf {x} _ {t}) - g (\mathbf {x} _ {t + 1}) - \frac {1}{4 \eta} \| \mathbf {x} _ {t + 1} - \mathbf {x} _ {t} \| ^ {2}} \end{array}
$$

Proof. Due to the update of $\mathbf { x } _ { t + 1 }$ , we have

$$
\begin{array}{l} \mathbf {x} _ {t + 1} ^ {\top} G _ {t} + \frac {1}{2 \eta} \| \mathbf {x} _ {t + 1} - \mathbf {x} _ {t} \| ^ {2} + g (\mathbf {x} _ {t + 1}) + (\frac {1}{2 \eta} + \frac {1}{2 \gamma}) \| \mathbf {x} - \mathbf {x} _ {t + 1} \| ^ {2} \\ \leq \mathbf {x} ^ {\top} G _ {t} + \frac {1}{2 \eta} \| \mathbf {x} - \mathbf {x} _ {t} \| ^ {2} + g (\mathbf {x}) \end{array}
$$

As a result, we have

$$
\begin{array}{r l} & {(\mathbf {x} _ {t} - \mathbf {x}) ^ {\top} G _ {t} + g (\mathbf {x} _ {t}) - g (\mathbf {x}) + \frac {1}{2 \gamma} \| \mathbf {x} - \mathbf {x} _ {t + 1} \| ^ {2}} \\ & {\leq (\mathbf {x} _ {t} - \mathbf {x} _ {t + 1}) ^ {\top} G _ {t} + \frac {1}{2 \eta} (\| \mathbf {x} - \mathbf {x} _ {t} \| ^ {2} - \| \mathbf {x} - \mathbf {x} _ {t + 1} \| ^ {2}) + g (\mathbf {x} _ {t}) - g (\mathbf {x} _ {t + 1}) - \frac {1}{2 \eta} \| \mathbf {x} _ {t + 1} - \mathbf {x} _ {t} \| ^ {2}} \\ & {\leq \eta \| G _ {t} \| ^ {2} + \frac {1}{2 \eta} (\| \mathbf {x} - \mathbf {x} _ {t} \| ^ {2} - \| \mathbf {x} - \mathbf {x} _ {t + 1} \| ^ {2}) + g (\mathbf {x} _ {t}) - g (\mathbf {x} _ {t + 1}) - \frac {1}{4 \eta} \| \mathbf {x} _ {t + 1} - \mathbf {x} _ {t} \| ^ {2}} \end{array}
$$

Below, we let $\begin{array} { r } { g _ { 1 } ( \mathbf { w } ) = \frac { 1 } { 2 \gamma } \| \mathbf { w } - \mathbf { w } _ { 1 } ^ { k } \| ^ { 2 } , g _ { 2 } ( \mathbf { s } ) = \frac { 1 } { 2 \gamma } \| \mathbf { s } - \mathbf { s } _ { 1 } ^ { k } \| ^ { 2 } } \end{array}$ , and $\begin{array} { r } { g _ { 3 } ( s ^ { \prime } ) = \frac { 1 } { 2 \gamma } \Vert s ^ { \prime } - s _ { k , 1 } ^ { \prime } \Vert ^ { 2 } } \end{array}$ . Applying the above Lemma to $\mathbf { w } _ { t + 1 }$ , we have

$$
\begin{array}{r l} & {(\mathbf {w} _ {t} - \mathbf {w}) ^ {\top} \nabla_ {1} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) + g _ {1} (\mathbf {w} _ {t}) - g _ {1} (\mathbf {w})} \\ & {\leq \eta_ {1} \| \nabla_ {1} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) \| ^ {2} + \frac {1}{2 \eta_ {1}} (\| \mathbf {w} - \mathbf {w} _ {t} \| ^ {2} - \| \mathbf {w} - \mathbf {w} _ {t + 1} \| ^ {2}) + g _ {1} (\mathbf {w} _ {t}) - g _ {1} (\mathbf {w} _ {t + 1})} \end{array}
$$

Assume w is independent of noise and taking expectation on both sides, we have

$$
\begin{array}{r l} & {\mathrm{E} [ (\mathbf {w} _ {t} - \mathbf {w}) ^ {\top} \nabla_ {1} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}) + g _ {1} (\mathbf {w} _ {t}) - g _ {1} (\mathbf {w}) ]} \\ & {\leq \mathrm{E} [ \eta_ {1} \| \nabla_ {1} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) \| ^ {2} + \frac {1}{2 \eta_ {1}} (\| \mathbf {w} - \mathbf {w} _ {t} \| ^ {2} - \| \mathbf {w} - \mathbf {w} _ {t + 1} \| ^ {2}) + g _ {1} (\mathbf {w} _ {t}) - g _ {1} (\mathbf {w} _ {t + 1}) ]} \end{array}
$$

Applying the above Lemma to $s _ { t + 1 , i } ,$ we have

$$
\begin{array}{r l} & {(s _ {t, i} - s _ {i}) ^ {\top} U _ {i} \nabla_ {2} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) + g _ {2} (s _ {t, i}) - g _ {2} (s _ {i})} \\ & {\leq \eta_ {2} \| U _ {i} \nabla_ {2} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) \| ^ {2} + \frac {1}{2 \eta_ {2}} (\| s _ {i} - s _ {t, i} \| ^ {2} - \| s _ {i} - s _ {t + 1, i} \| ^ {2}) + g _ {2} (s _ {t, i}) - g _ {2} (s _ {t + 1, i})} \end{array}
$$

Summing the above inequality over $\mathbf { x } _ { i } \in B _ { + }$ , assuming s is independent of noise and taking expectation on both sides, we have

$$
\begin{array}{r l} & {\frac {B _ {+}}{n _ {+}} \mathrm{E} (\mathbf {s} _ {t} - \mathbf {s}) ^ {\top} \nabla_ {2} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}) + g _ {2} (\mathbf {s} _ {t}) - g _ {2} (\mathbf {s}) ]} \\ & {= \mathrm{E} [ \eta_ {2} \sum_ {i \in \mathcal {B} _ {+}} \| U _ {i} \nabla_ {2} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) \| ^ {2} + \frac {1}{2 \eta_ {2}} (\| \mathbf {s} - \mathbf {s} _ {t} \| ^ {2} - \| \mathbf {s} - \mathbf {s} _ {t + 1} \| ^ {2}) + g _ {2} (\mathbf {s} _ {t}) - g _ {2} (\mathbf {s} _ {t + 1}) ]} \end{array}
$$

Applying the above lemma to $s _ { t + 1 } ^ { \prime }$ , we have

$$
\begin{array}{r l} & {(s _ {t} ^ {\prime} - s ^ {\prime}) ^ {\top} \nabla_ {3} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) + g _ {3} (s _ {t} ^ {\prime}) - g _ {3} (s ^ {\prime})} \\ & {\leq \eta_ {2} \| \nabla_ {3} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) \| ^ {2} + \frac {1}{2 \eta_ {2}} (\| s ^ {\prime} - s _ {t} ^ {\prime} \| ^ {2} - \| s ^ {\prime} - s _ {t + 1} ^ {\prime} \| ^ {2}) + g _ {3} (s _ {t} ^ {\prime}) - g _ {3} (s _ {t + 1} ^ {\prime})} \end{array}
$$

Assume $\mathbf { s } ^ { \prime }$ is independent of noise and taking expectation on both sides, we have

$$
\begin{array}{r l} & {\mathrm{E} [ (s _ {t} ^ {\prime} - s ^ {\prime}) ^ {\top} \nabla_ {3} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}) + g _ {3} (s _ {t} ^ {\prime}) - g _ {3} (s ^ {\prime}) ]} \\ & {\leq \mathrm{E} [ \eta_ {2} \| \nabla_ {3} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) \| ^ {2} + \frac {1}{2 \eta_ {2}} (\| s ^ {\prime} - s _ {t} ^ {\prime} \| ^ {2} - \| s ^ {\prime} - s _ {t + 1} ^ {\prime} \| ^ {2}) + g _ {3} (s _ {t} ^ {\prime}) - g _ {3} (s _ {t + 1} ^ {\prime}) ]} \end{array}
$$

Adding the above inequalities for $\mathbf { w } , \mathbf { s } , s ^ { \prime }$ together we have

$$
\begin{array}{r l} & {\mathrm{E} [ \sum_ {t} (\bar {\mathbf {w}} _ {t} - \bar {\mathbf {w}}) ^ {\top} \nabla_ {\bar {\mathbf {w}}} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}) + g (\bar {\mathbf {w}} _ {t}) - g (\bar {\mathbf {w}}) ]} \\ & {\leq \eta_ {1} C _ {1} ^ {2} T + \eta_ {2} n _ {+} C _ {2} ^ {2} T + \eta_ {3} C _ {3} ^ {2} T} \\ & {+ \frac {1}{2 \eta_ {1}} (\| \mathbf {w} - \mathbf {w} _ {1} \| ^ {2}) + \frac {n _ {+}}{2 \eta_ {2} B _ {+}} (\| \mathbf {s} - \mathbf {s} _ {1} \| ^ {2}) + \frac {1}{2 \eta_ {3}} (\| s ^ {\prime} - s _ {1} ^ {\prime} \| ^ {2}) + g _ {1} (\mathbf {w} _ {1}) + \frac {n _ {+}}{B _ {+}} g _ {2} (\mathbf {s} _ {1}) + g _ {3} (s _ {1} ^ {\prime})} \end{array}
$$

As a result,

$$
\begin{array}{l} \mathrm{E} [ \sum_ {t} F _ {k} (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}) - F _ {k} (\bar {\mathbf {w}}, \mathbf {u} _ {t}) ] \leq \eta_ {1} C _ {1} ^ {2} T + \eta_ {2} n _ {+} C _ {2} ^ {2} T + \eta_ {3} C _ {3} ^ {2} T \\ + \frac {1}{2 \eta_ {1}} (\| \mathbf {w} - \mathbf {w} _ {1} \| ^ {2}) + \frac {n _ {+}}{2 \eta_ {2} B _ {+}} (\| \mathbf {s} - \mathbf {s} _ {1} \| ^ {2}) + \frac {1}{2 \eta_ {3}} (\| s ^ {\prime} - s _ {1} ^ {\prime} \| ^ {2}) \end{array}
$$

For the update of u, it is equivalent to

$$
\mathbf {u} _ {t + 1} = \arg \min _ {\mathbf {u} \in [ 0, 1 ]} \mathbf {u} ^ {\top} \widetilde {\nabla} _ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) + \frac {1}{2 \eta_ {4}} \| \mathbf {u} - \mathbf {u} _ {t} \| ^ {2}
$$

where $\begin{array} { r } { \widetilde { \nabla } _ { 4 } F ( \bar { \mathbf { w } } _ { t } , \mathbf { u } _ { t } ; \xi _ { t } ) = \frac { n _ { + } } { B _ { \perp } } \sum _ { i \in \mathcal { B } _ { \perp } } U _ { i } ^ { \top } U _ { i } \nabla _ { 4 } F ( \bar { \mathbf { w } } _ { t } , \mathbf { u } _ { t } ; \xi _ { t } ) } \end{array}$ . It is easy to show that $\mathrm { E } [ \widetilde { \nabla } _ { 4 } F ( \bar { \mathbf { w } } _ { t } , \mathbf { u } _ { t } ; \boldsymbol { \xi } _ { t } ) ] = \nabla _ { 4 } F ( \bar { \mathbf { w } } _ { t } , \mathbf { u } _ { t } )$ Applying the same analysis to the update of $\mathbf { u } _ { t }$ , we have

$$
\begin{array}{r l} & {(\mathbf {u} - \mathbf {u} _ {t}) ^ {\top} \widetilde {\nabla} _ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t})} \\ & {\leq \eta_ {4} \| \widetilde {\nabla} _ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) \| ^ {2} + \frac {1}{2 \eta_ {4}} (\| \mathbf {u} - \mathbf {u} _ {t} \| ^ {2} - \| \mathbf {u} - \mathbf {u} _ {t + 1} \| ^ {2})} \end{array}
$$

We do not assume u is independent of the randomness in order to derive the primal objective gap. As a result,

$$
\begin{array}{r l} & {(\mathbf {u} - \mathbf {u} _ {t}) ^ {\top} \nabla_ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t})} \\ & {= \eta_ {4} \| \widetilde {\nabla} _ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) \| ^ {2} + \frac {1}{2 \eta_ {4}} (\| \mathbf {u} - \mathbf {u} _ {t} \| ^ {2} - \| \mathbf {u} - \mathbf {u} _ {t + 1} \| ^ {2})} \\ & {+ (\mathbf {u} - \mathbf {u} _ {t}) ^ {\top} (\nabla_ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}) - \widetilde {\nabla} _ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}))} \end{array}
$$

Following previous analysis (e.g., Proposition A.1 in (Rafique et al., 2020)), we have

$$
\begin{array}{r l} & {(\mathbf {u} - \tilde {\mathbf {u}} _ {t}) ^ {\top} (\nabla_ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}) - \nabla_ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}))} \\ & {\leq \eta_ {4} \| \nabla_ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}) - \nabla_ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}; \xi_ {t}) \| ^ {2} + \frac {1}{2 \eta_ {4}} (\| \mathbf {u} - \tilde {\mathbf {u}} _ {t} \| ^ {2} - \| \mathbf {u} - \tilde {\mathbf {u}} _ {t + 1} \| ^ {2})} \end{array}
$$

Hence for any u, we have

$$
\mathrm{E} (\mathbf {u} - \mathbf {u} _ {t}) ^ {\top} \nabla_ {4} F (\bar {\mathbf {w}} _ {t}, \mathbf {u} _ {t}) ] \leq \frac {2 n _ {+} ^ {2}}{B _ {+}} \eta_ {4} C _ {4} ^ {2} + \frac {1}{\eta_ {4}} \| \mathbf {u} - \mathbf {u} _ {1} \| ^ {2}
$$

As a result, for any u we have

$$
\mathrm{E} [ \sum_ {t} F _ {k} (\mathbf {u}, \bar {\mathbf {w}} _ {t}) - F _ {k} (\mathbf {u} _ {t}, \bar {\mathbf {w}} _ {t}) ] \leq \frac {2 n _ {+} ^ {2}}{B _ {+}} \eta_ {4} C _ {4} ^ {2} + \frac {1}{\eta_ {4}} \| \mathbf {u} - \mathbf {u} _ {1} \| ^ {2}
$$

As a result,

$$
\begin{array}{l} \mathrm{E} [ \sum_ {t} F _ {k} (\bar {\mathbf {w}} _ {t}, \mathbf {u}) - F _ {k} (\bar {\mathbf {w}}, \mathbf {u} _ {t}) ] \leq \eta_ {1} C _ {1} ^ {2} T + \eta_ {2} n _ {+} C _ {2} ^ {2} T + \eta_ {3} C _ {3} ^ {2} T + \frac {2 n _ {+} ^ {2}}{B _ {+}} \eta_ {4} C _ {4} ^ {2} \\ + \frac {1}{2 \eta_ {1}} (\| \mathbf {w} - \mathbf {w} _ {1} \| ^ {2}) + \frac {n _ {+}}{2 \eta_ {2} B _ {+}} (\| \mathbf {s} - \mathbf {s} _ {1} \| ^ {2}) + \frac {1}{2 \eta_ {3}} (\| s ^ {\prime} - s _ {1} ^ {\prime} \| ^ {2}) + \frac {1}{\eta_ {4}} \| \mathbf {u} - \mathbf {u} _ {1} \| ^ {2} \end{array}
$$

Let $\eta _ { 1 } = \eta _ { 3 } = \eta _ { 2 } B _ { + } / n _ { + } = \eta , \eta _ { 4 } = \eta$ . Then we have

$$
\begin{array}{l} \mathrm{E} [ \sum_ {t} F _ {k} (\bar {\mathbf {w}} _ {t}, \mathbf {u}) - F _ {k} (\bar {\mathbf {w}}, \mathbf {u} _ {t}) ] \leq \eta C _ {1} ^ {2} T + \eta \frac {n _ {+} ^ {2}}{B _ {+}} C _ {2} ^ {2} T + \eta C _ {3} ^ {2} T + \frac {2 n _ {+} ^ {2}}{B _ {+}} \eta C _ {4} ^ {2} \\ + \frac {1}{2 \eta} (\| \bar {\mathbf {w}} - \bar {\mathbf {w}} _ {1} \| ^ {2}) + \frac {1}{\eta} \end{array}
$$

Then we have

$$
\begin{array}{l} \mathrm{E} [ \max _ {\mathbf {u}} F _ {k} (\widehat {\mathbf {w}} _ {T}, \mathbf {u}) - F _ {k} (\bar {\mathbf {w}} ^ {*}, \widehat {\mathbf {u}} _ {t}) ] \leq \eta C _ {1} ^ {2} T + \eta \frac {n _ {+} ^ {2}}{B _ {+}} C _ {2} ^ {2} + \eta C _ {3} ^ {2} + 2 \frac {n _ {+} ^ {2}}{B _ {+}} \eta C _ {4} ^ {2} \\ + \frac {1}{2 \eta T} (\| \bar {\mathbf {w}} ^ {*} - \bar {\mathbf {w}} _ {1} \| ^ {2}) + \frac {1}{\eta T} \end{array}
$$

where $\widehat { \bf w } _ { T }$ is the average of $\bar { \bf w } _ { t } , t = 1 , \dots , T$ and $\widehat { \mathbf { u } } _ { T }$ is the averaged solution of ${ \bf u } _ { t } , \bar { \bf w } ^ { * }$ is the optimal solution to $F _ { k } ( \bar { \mathbf { w } } )$ The above implies that

$$
\begin{array}{l} \operatorname{E} [ F _ {k} (\widehat {\mathbf {w} _ {T}}) - \min _ {\bar {\mathbf {w}}} F _ {k} (\bar {\mathbf {w}}) ] \leq \eta (\frac {C}{\alpha^ {2} \beta^ {2}} + \frac {n _ {+} ^ {2}}{B _ {+}} \frac {1}{n _ {+} ^ {2} \alpha^ {2}} (1 + \frac {1}{\beta}) ^ {2} + (1 + \frac {1}{\alpha}) ^ {2} + 2 \frac {n _ {+} ^ {2}}{B _ {+}} \frac {4 C ^ {2}}{n _ {+} ^ {2} \alpha^ {2}} (1 + \frac {1}{\beta}) ^ {2}) \\ + \frac {1}{2 \eta} (\| \bar {\mathbf {w}} ^ {*} - \bar {\mathbf {w}} _ {1} \| ^ {2}) + \frac {1}{\eta T} \\ \leq \eta O \left(\frac {C}{\alpha^ {2} \beta^ {2}}\right) + \frac {1}{2 \eta} (\| \bar {\mathbf {w}} ^ {*} - \bar {\mathbf {w}} _ {1} \| ^ {2}) + \frac {1}{\eta T} \end{array}
$$

It remains to apply the analysis in (Rafique et al., 2020, Theorem 4.1) to derive the convergence for the Moreau envelope of $F ( \mathbf { w } , \mathbf { s } , s ^ { \prime } )$ with a complexity in the order of ${ \cal O } ( 1 / \epsilon ^ { 6 } )$ by setting $\eta _ { k } \propto 1 / k$ and $T _ { k } \propto k ^ { 2 }$ and the total number of stages $K = O ( 1 / \epsilon ^ { 2 } )$