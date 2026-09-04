---
title: "2019-Kawaguchi-Ordered-SGD-arXiv"
date: 2026-09-04
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/ranking/2019-Kawaguchi-Ordered-SGD-arXiv.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Ordered SGD: A New Stochastic Optimization Framework for Empirical Risk Minimization

Kenji Kawaguchi MIT

## Abstract

## 1 Introduction

We propose a new stochastic optimization framework for empirical risk minimization problems such as those that arise in machine learning. The traditional approaches, such as (mini-batch) stochastic gradient descent (SGD), utilize an unbiased gradient estimator of the empirical average loss. In contrast, we develop a computationally efficient method to construct a gradient estimator that is purposely biased toward those observations with higher current losses. On the theory side, we show that the proposed method minimizes a new ordered modification of the empirical average loss, and is guaranteed to converge at a sublinear rate to a global optimum for convex loss and to a critical point for weakly convex (non-convex) loss. Furthermore, we prove a new generalization bound for the proposed algorithm. On the empirical side, the numerical experiments show that our proposed method consistently improves the test errors compared with the standard mini-batch SGD in various models including SVM, logistic regression, and deep learning problems.

Haihao Lu \* Google Research

Stochastic Gradient Descent (SGD), as the workhorse training algorithm for most machine learning applications including deep learning, has been extensively studied in recent years (e.g., see a recent review by Bottou et al. 2018). At every step, SGD draws one training sample uniformly at random from the training dataset, and then uses the (sub-)gradient of the loss over the selected sample to update the model parameters. The most popular version of SGD in prac tice is perhaps the mini-batch SGD (Bottou et al., 2018; Dean et al., 2012), which is widely implemented in the state-of-the-art deep learning frameworks, such as TensorFlow (Abadi et al., 2016), PyTorch (Paszke et al., 2017) and CNTK (Seide and Agarwal, 2016). Instead of choosing one sample per iteration, mini-batch SGD randomly selects a mini-batch of the samples, and uses the (sub-)gradient of the average loss over the selected samples to update the model parameters.

Both SGD and mini-batch SGD utilize uniform sampling during the entire learning process, so that the stochastic gradient is always an unbiased gradient estimator of the empirical average loss over all samples. On the other hand, it appears to practitioners that not all samples are equally important, and indeed most of them could be ignored after a few epochs of training without afecting the final model (Katharopoulos and Fleuret, 2018). For example, intuitively, the samples near the final decision boundary should be more important to build the model than those far away from the boundary for classification problems. In particular, as we will illustrate later in Figure 1, there are cases when those far-away samples may corrupt the model by using average loss. In order to further ex plore such structures, we propose an eficient sampling scheme on top of the mini-batch SGD. We call the resulting algorithm ordered SGD, which is used to learn a diferent type of models with the goal to improve the testing performance.

The above motivation of ordered SGD is related to that of importance sampling SGD, which has been extensively studied recently in order to improve the convergence speed of SGD (Needell et al., 2014; Zhao and Zhang, 2015; Alain et al., 2015; Loshchilov and Hutter, 2015; Gopal, 2016; Katharopoulos and Fleuret, 2018). However, our goals, algorithms and theoretical results are fundamentally diferent from those in the previous studies on importance sampling SGD. Indeed, all aforementioned studies are aimed to accelerate the minimization process for the empirical average loss, whereas our proposed method turns out to minimize a new objective function by purposely constructing a biased gradient.

Our main contributions can be summarized as follows: i) we propose a computationally eficient and easily implementable algorithm, ordered SGD, with principled motivations (Section 3), ii) we show that ordered SGD minimizes an ordered empirical risk with sublinear rate for convex and weakly convex (non-convex) loss functions (Section 4), iii) we prove a generalization bound for ordered SGD (Section 5), and iv) our numerical experiments show ordered SGD consistently improved mini-batch SGD in test errors (Section 6).

## 2 Empirical Risk Minimization

Empirical risk minimization is one of the main tools to build a model in machine learning. Let $\mathcal { D } =$ $( ( x _ { i } , y _ { i } ) ) _ { i = 1 } ^ { n }$ be a training dataset of n samples where $x _ { i } \in \mathcal { X } \subseteq \mathbb { R } ^ { d _ { x } }$ is the input vector and $y _ { i } \in \mathcal { V } \subseteq \mathbb { R } ^ { d _ { y } }$ is the target output vector for the i-th sample. The goal of empirical risk minimization is to find a prediction function $f ( \cdot ; \boldsymbol { \theta } ) : \mathbb { R } ^ { d _ { x } }  \mathbb { R } ^ { d _ { y } }$ , by minimizing

$$
L (\theta) := \frac {1}{n} \sum_ {i = 1} ^ {n} L _ {i} (\theta) + R (\theta),\tag{1}
$$

where $\theta \in \mathbb { R } ^ { d _ { \theta } }$ is the parameter vector of the prediction model, $L _ { i } ( \theta ) : = \ell ( f ( x _ { i } ; \theta ) , y _ { i } )$ with the function \` : $\mathbb { R } ^ { d _ { y } } \times \mathcal { y }  \mathbb { R } _ { > 0 }$ is the loss of the i-th sample, and $R ( \theta ) \geq 0$ is a regularizer. For example, in logistic regression, $f ( x ; \theta ) = \theta ^ { T } x$ is a linear function of the input vector x, and $\ell ( a , y ) = \log ( 1 + \exp ( - y a ) )$ is the logistic loss function with $y \in \{ - 1 , 1 \}$ . For a neural network, $f ( x ; \theta )$ represents the pre-activation output of the last layer.

## 3 Algorithm

In this section, we introduce ordered SGD and provide an intuitive explanation of the advantage of ordered SGD by looking at 2-dimension toy examples with linear classifiers and small artificial neural networks (ANNs). Let us first introduce a new notation q-argmax as an extension to the standard notation argmax:

Definition 1. Given a set of n real numbers $( a _ { 1 } , a _ { 2 } , \ldots , a _ { n } )$ , an index subset $S ~ \subseteq ~ \{ 1 , 2 , \dots , n \}$ 2 and a positive integer number $q \ \leq \ | S | .$ , we define $\mathrm { q - a r g m a x } _ { j \in S } a _ { j }$ such that $Q \ \in \ { \mathrm { q - a r g m a x } } _ { j \in S } a _ { j }$ is a set of q indexes of the q largest values of $( a _ { j } ) _ { j \in S } ;$ i.e., $\operatorname { q - a r g m a x } _ { j \in S } a _ { j } = \operatorname { a r g m a x } _ { Q \subseteq S , | Q | = q } \sum _ { i \in Q } a _ { i } .$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Ordered Stochastic Gradient Descent (ordered SGD)

1: Inputs: an initial vector $\theta^0$ and a learning rate sequence $(\eta_k)_k$
2: for $t = 1,2,\ldots$ do
3: Randomly choose a mini-batch of samples: $S \subseteq \{1,2,\ldots,n\}$ such that $|S| = s$.
4: Find a set $Q$ of top-$q$ samples in $S$ in term of loss values: $Q \in \mathrm{q-argmax}_{i \in S} L_i(\theta^t)$.
5: Compute a subgradient $\tilde{g}^t$ of the top-$q$ samples $L_Q(\theta^t)$: $\tilde{g}^t \in \partial L_Q(\theta^t)$ where $L_Q(\theta^t) = \frac{1}{q} \sum_{i \in Q} L_i(\theta^t) + R(\theta^t)$ and $\partial L_Q$ is the set of subgradient$^1$of function $L_Q$.
6: Update parameters $\theta$: $\theta^{t+1} = \theta^t - \eta_t \tilde{g}^t$
</div>

Algorithm 1 describes the pseudocode of our proposed algorithm, ordered SGD. The procedures of ordered SGD follow those of mini-batch SGD except the following modification: after drawing a mini-batch of size $s ,$ ordered SGD updates the parameter vector θ based on the (sub-)gradient of the average loss over the top-q samples in the mini-batch in terms of individual loss values (lines 4 and 5 of Algorithm 1). This modification is used to purposely build and utilize a biased gradient estimator with more weights on the samples having larger losses. As it can be seen in Algorithm 1, ordered SGD is easily implementable, requiring to change only a single line or few lines on top of a minibatch SGD implementation.

Figure 1 illustrates the motivation of ordered SGD by looking at two-dimensional toy problems of binary classification. To avoid an extra freedom due to the hyper-parameter q, we employed a single fixed procedure to set the hyper-parameter q in the experiments for Figure 1 and other experiments in Section 6, which is further explained in Section 6. The details of the experimental settings for Figure 1 are presented in Section 6 and in Appendix C.

It can be seen from Figure 1 that ordered SGD adapts better to imbalanced data distributions compared with mini-batch SGD. It can better capture the information of the smaller sub-clusters that contribute less to the empirical average loss L(θ): e.g., the small sub-clusters in the middle of Figures 1a and 1b, as well as the small inner ring structure in Figures 1c and 1d (the two inner rings contain only 40 data points while the two outer rings contain 960 data points). The smaller subclusters are informative for training a classifier when they are not outliers or by-products of noise. A subcluster of data points would be less likely to be an outlier as the size of the sub-cluster increases. The value of $q$ in ordered SGD can control the size of subclusters that a classifier should be sensitive to. With smaller q, the output model becomes more sensitive to smaller sub-clusters. In an extreme case with $q =$ 1 and $n \ = \ s .$ , ordered SGD minimizes the maximal loss (Shalev-Shwartz and Wexler, 2016) that is highly sensitive to every smallest sub-cluster of each single data point.

![](images/32504efe35a3f74b8416a2730edf3b4561d5acbf327c3deaf3f275f148c537ca.jpg)

![](images/de887e00c4e356dd2a0e2308ce00ab359afb98d5494fe6e6679aae759fa3a6c1.jpg)

![](images/fe60eebe6db427740a62f2649f799866d04d54b8fe1e293743f56e7f05a1da6b.jpg)  
(a) with linear classifier

![](images/65ea3f65e259b1a00286bd1503ca7b816c1e7ce10cdb595a7c914f335b4f6215.jpg)

![](images/b8695d1a487874070dd1fb338f20dfa640cbbdd6b9afdf91fe376f17394e4bcf.jpg)  
(b) with linear classifier

![](images/47fa79da437d8210e98714587428869eb56486542e6f7a4ab16822b6e2b2f182.jpg)

![](images/d71cae62ac555df35af460aeba0bbf0d3c2a046c340e244d89349a31bf55058f.jpg)  
(c) with small ANN

![](images/c1c17a5dd828cb6663c9089dec39774cf05734ddc2361661b12d297529216ba2.jpg)  
(d) with tiny ANN  
Figure 1: Decision boundaries of mini-batch SGD predictors (top row) and ordered SGD predictors (bottom row) with 2D synthetic datasets for binary classification. In these examples, ordered SGD predictors correctly classify more data points than mini-batch SGD predictors, because a ordered SGD predictor can focus more on a smaller yet informative subset of data points, instead of focusing on the average loss dominated by a larger subset of data points.

## 4 Optimization Theory

In this section, we answer the following three questions: (1) what objective function does ordered SGD solve as an optimization method, (2) what is the convergence rate of ordered SGD for minimizing the new objective function, and (3) what is the asymptotic structure of the new objective function.

Similarly to the notation of order statistics, we first introduce the notation of ordered indexes: given a model parameter θ, let $L _ { ( 1 ) } ( \theta ) \ \geq \ L _ { ( 2 ) } ( \theta ) \ \geq \ \cdot \cdot \ \geq$ $L _ { ( n ) } ( \theta )$ be the decreasing values of the individual losses $L _ { 1 } ( \theta ) , \ldots , L _ { n } ( \theta )$ , where $( j ) \in \{ 1 , \ldots , n \}$ (for all $j \in \{ 1 , \ldots , n \} )$ . That is, $\{ ( 1 ) , \ldots , ( n ) \}$ as a perturbation of $\{ 1 , \ldots , n \}$ defines the order of sample indexes by loss values. Throughout this paper, whenever we encounter ties on the values, we employ a tie-breaking rule in order to ensure the uniqueness of such an order.<sup>2</sup> Theorem 1 shows that ordered SGD is a stochastic first-order method for minimizing the new ordered

empirical loss $L _ { q } ( \theta )$

Theorem 1. Consider the following objective function: 1 <sup>n</sup>

$$
L _ {q} (\theta) := \frac {1}{q} \sum_ {j = 1} ^ {n} \gamma_ {j} L _ {(j)} (\theta) + R (\theta),\tag{2}
$$

where the parameter $\gamma _ { j }$ depends on the tuple $( n , s , q )$ and is defined by

$$
\gamma_ {j} := \frac {\sum_ {l = 0} ^ {q - 1} \binom {j - 1} {l} \binom {n - j} {s - l - 1}}{\binom {n} {s}}.\tag{3}
$$

Then, ordered SGD is a stochastic first-order method for minimizing $L _ { q } ( \theta )$ in the sense that $\tilde { g } ^ { t }$ used in ordered SGD is an unbiased estimator ofa (sub-)gradient of $L _ { q } ( \theta )$

Although the order of individual losses change with diferent $\theta , L _ { q }$ is a well-defined function. For any given $\theta ,$ the order of individual losses is fixed and $L _ { q } ( \theta )$ has a unique value, which means $L _ { q } ( \theta )$ is a function of θ.

All proofs in this paper are deferred to Appendix A. As we can see from Theorem 1, the objective function minimized by ordered SGD $\operatorname { ( i . e . , } L _ { q } ( \theta ) \operatorname { ) }$ depends on the hyper-parameters of the algorithm through the values of $\gamma _ { j }$ . Therefore, it is of practical interest to obtain deeper understandings on how the hyper-parameters $( n , s , q )$ ) afects the objective function $L _ { q } ( \theta )$ through $\gamma _ { j }$ The next proposition presents the asymptotic value of $\gamma _ { j } \ \mathrm { ( w h e n } \ n \  \ \infty )$ , which shows that a rescaled $\gamma _ { j }$ converges to the cumulative distribution function of a Beta distribution:

Proposition 1. Denote $\begin{array} { r l r } { z } & { { } = } & { \frac { j } { n } } \end{array}$ and $\begin{array} { r l } { \gamma ( z ) } & { { } : = } \end{array}$ $\begin{array} { r } { \sum _ { l = 0 } ^ { q - 1 } z ^ { l } ( 1 - z ) ^ { s - l - 1 } \frac { s ! } { l ! ( s - l - 1 ) ! } } \end{array}$ . Then, it holds that

$$
\lim _ {j, n \to \infty , j / n = z} \gamma_ {j} = \frac {1}{n} \gamma (z).
$$

![](images/39406c38a3f076ad9fd58c3646f4c4c92290340bf0cb22c467b3712e63d0565c.jpg)  
(a) (s, q) = (10, 3)

![](images/09ef762f818002f60ef016e2f749f915138a385cbdb4509dec9a04b2188d622d.jpg)

![](images/f52b68d705383d64264521f16c69fd2def9db0dc75d1cb49006a17c053a919c2.jpg)  
(b) (s, q) = (100, 30)  
(c) (s, q) = (100, 60)  
Figure 2: ˆγ(z) and $\gamma ( z )$ for diferent $( n , s , q )$ where $\hat { \gamma }$ is a rescaled version of $\gamma _ { j } \colon \hat { \gamma } ( j / n ) = n \gamma _ { j }$

Moreover, it holds that $1 - { \textstyle \frac { 1 } { s } } \gamma ( z )$ is the cumulative distribution function of $B e t a ( z ; q , s - q )$

To better illustrate the structure of $\gamma _ { j }$ in the nonasymptotic regime, Figure 2 plots $\hat { \gamma } ( z )$ and $\gamma ( z )$ for diferent values of $( n , s , q )$ where $\hat { \gamma } ( z )$ is a rescaled version of $\gamma _ { j }$ defined by $\hat { \gamma } ( j / n ) = n \gamma _ { j }$ (and the value of $\hat { \gamma } ( \cdot )$ between $j / n$ and $( j + 1 ) / n$ is defined by linear interpolation for better visualization). As we can see from Figure $2 , { \hat { \gamma } } ( z )$ monotonically decays. In each subfigure, with fixed $s , q ,$ , the clif gets smoother and $\hat { \gamma } ( z )$ converges to $\gamma ( z )$ as n increases. Comparing Figures 2a and $\mathrm { 2 b }$ , we can see that as $s , \ q$ and n all increase proportionally, the clif gets steeper. Comparing Figures 2b and 2c, we can see that with fixed n and $q ,$ the clif shifts to the right as q increases.

As a direct extension of Theorem 1, we can now obtain the computational guarantees of ordered SGD for minimizing $L _ { q } ( \theta )$ by taking advantage of the classic convergence results of SGD:

Theorem 2. Let $( \theta ^ { t } ) _ { t = 0 } ^ { T }$ be a sequence generated $b y$ ordered SGD (Algorithm 1). Suppose that $L _ { i } ( \cdot )$ is $G _ { 1 } -$ Lipschitz continuous $f o r i = 1 , \ldots , n ,$ , and $R ( \cdot )$ is $G _ { 2 ^ { - } }$ Lipschitz continuous. Suppose that there exists a finite $\theta ^ { * } \in \mathrm { \ a r g m i n } _ { \theta } L _ { q } ( \theta )$ and $L _ { q } ( \theta ^ { * } )$ is finite. Then, the following two statements hold:

(1) (Convex setting). If $L _ { i } ( \cdot )$ and $R ( \cdot )$ are both convex, for any step-size $\eta _ { t } ,$ it holds that

$$
\begin{array}{l} \min _ {0 \leq t \leq n} \mathbb {E} [ L _ {q} (\theta^ {t}) - L _ {q} (\theta^ {*}) ] \\ \leq \frac {2 (G _ {1} ^ {2} + G _ {2} ^ {2}) \sum_ {t = 0} ^ {T} \eta_ {t} ^ {2} + \| \theta^ {*} - \theta^ {0} \| ^ {2}}{2 \sum_ {t = 0} ^ {T} \eta_ {t}}. \end{array}
$$

(2) (Weakly convex setting) Suppose that $L _ { i } ( \cdot )$ is $\rho -$ weakly convex $\begin{array} { r l } { ( i . e . , L _ { i } ( \theta ) + \frac { \rho } { 2 } \| \theta \| ^ { 2 } } \end{array}$ is convex) and $R ( \cdot )$ is convex. Recall the definition of Moreau envelope: $L _ { q } ^ { \lambda } ( \theta ) : =$ min<sub>β</sub> $\begin{array} { r } { \{ L _ { q } ( \beta ) + \frac { 1 } { 2 \lambda } \| \dot { \beta } - \theta \| ^ { 2 } \} } \end{array}$ Denote $\bar { \theta } ^ { T }$ as a random variable taking value in $\{ \theta ^ { 0 } , \theta ^ { 1 } , \dots , \theta ^ { T } \}$ according to the probability distribution $\begin{array} { r } { \mathbb { P } ( \bar { \theta } ^ { T } = \theta ^ { t } ) = \frac { \eta _ { t } } { \sum _ { t = 0 } ^ { T } \eta _ { t } } } \end{array}$ . Then for any constant $\hat { \rho } > \rho ,$ it holds that

$$
\begin{array}{l} \mathbb {E} [ \| \nabla L _ {q} ^ {1 / \hat {\rho}} (\bar {\theta} ^ {T}) \| ^ {2} ] \\ \leq \frac {\hat {\rho}}{\hat {\rho} - \rho} \frac {\left(L _ {q} ^ {1 / \hat {\rho}} (\theta^ {0}) - L _ {q} (\theta^ {*})\right) + \hat {\rho} (G _ {1} ^ {2} + G _ {2} ^ {2}) \sum_ {t = 0} ^ {T} \eta_ {t} ^ {2}}{\sum_ {t = 0} ^ {T} \eta_ {t}}. \end{array}
$$

Theorem 2 shows that in particular, if we choose $\eta _ { t } \sim$ $O ( 1 / \sqrt { t } )$ , the optimality gap min<sub>t</sub> $L _ { q } ( \theta ^ { t } ) - L _ { q } ( \theta ^ { * } )$ and $\mathbb { E } [ \| \nabla L _ { q } ^ { 1 / \hat { \rho } } ( \bar { \theta } _ { T } ) \| ^ { 2 } ]$ decay at the rate of ${ \tilde { O } } ( 1 / { \sqrt { t } } )$ (note that lim<sub>T→∞</sub> $\frac { \sum _ { t = 0 } ^ { T } \eta _ { t } ^ { 2 } } { \sum _ { t = 0 } ^ { T } \eta _ { t } } = 0$ with $\eta _ { t } \sim O ( 1 / { \sqrt { t } } ) )$ .

The Lipschitz continuity assumption in Theorem 2 is a standard assumption for the analysis of stochastic optimization algorithms. This assumption is generally satisfied with logistic loss, hinge loss and Huber loss without any constraints on $\theta ^ { t } { } _ { ; }$ , and with square loss when one can presume that $\theta ^ { t }$ stays in a compact space (which is typically the case being interested in practice). For the weakly convex setting, $\mathbb { E } \| \nabla \varphi ^ { 1 / 2 \rho } ( \bar { \theta } ^ { k } ) \| ^ { 2 }$ (appeared in Theorem $2 \ ( 2 ) )$ is a natural measure of the near-stationarity for a non-diferentiable weakly convex function $\varphi : \theta \mapsto \varphi ( \theta )$ (Davis and Drusvyatskiy, 2018). The weak convexity (also known as negative strong convexity or almost convexity) is a standard assumption for analyzing non-convex optimization problem in optimization literature (Davis and Drusvyatskiy, 2018; Allen-Zhu, 2017). With a standard loss criterion such as logistic loss, the individual objective $L _ { i } ( \cdot )$ with a neural network using sigmoid or tanh activation functions is weakly convex (neural network with ReLU activation function is not weakly convex and falls out of our setting).

## 5 Generalization Bound

This section presents the generalization theory for ordered SGD. To make the dependence on a train ing dataset D explicit, we define $\begin{array} { r l } { L ( \boldsymbol { \theta } ; \mathcal { D } ) } & { { } : = } \end{array}$ $\begin{array} { r } { \frac { 1 } { n } \sum _ { i = 1 } ^ { n } L _ { i } ( \theta ; \mathcal { D } ) } \end{array}$ and $\begin{array} { r } { L _ { q } ( \theta ; \mathcal { D } ) : = \frac { 1 } { q } \sum _ { j = 1 } ^ { m } \gamma _ { j } L _ { ( j ) } ( \theta ; \mathcal { D } ) } \end{array}$ by rewriting $L _ { i } ( \theta ; { \mathcal { D } } ) ~ = ~ L _ { i } ( \theta )$ and $L _ { ( j ) } ( \theta ; \mathcal { D } ) ~ =$

$L _ { ( j ) } ( \theta )$ , where $( ( j ) ) _ { j = 1 } ^ { n }$ defines the order of sample indexes by the loss value, as stated in Section 4. Denote $\begin{array} { r } { r _ { i } ( \theta ; \mathcal { D } ) = \sum _ { i = 1 } ^ { n } \mathbb { 1 } \{ i = ( j ) \} \gamma _ { j } } \end{array}$ where (j) depends on $( \theta , { \mathcal { D } } )$ . Given an arbitrary set $\Theta \subseteq \mathbb { R } ^ { d _ { \theta } }$ , we define $\Re _ { n } ( \Theta )$ as the (standard) Rademacher complexity of the set $\{ ( x , y ) \mapsto \ell ( f ( x ; \theta ) , y ) : \theta \in \Theta \}$

$$
\mathfrak {R} _ {n} (\Theta) = \mathbb {E} _ {\bar {\mathcal {D}}, \xi} \left[ \sup _ {\theta \in \Theta} \frac {1}{n} \sum_ {i = 1} ^ {n} \xi_ {i} \ell (f (\bar {x} _ {i}; \theta), \bar {y} _ {i}) \right],
$$

where $\begin{array} { c c l } { \overline { { \mathcal D } } } & { = } & { ( ( \bar { x } _ { i } , \bar { y } _ { i } ) ) _ { i = 1 } ^ { n } , } \end{array}$ and $\xi _ { 1 } , \ldots , \xi _ { n }$ are independent uniform random variables taking values in $\{ - 1 , 1 \} ( \mathrm { i . e . }$ , Rademacher variables). Given a tuple $( \ell , f , \Theta , \mathcal { X } , \mathcal { Y } )$ , define M as the least upper bound on the diference of individual loss values: $| \ell ( f ( x ; \theta ) , y ) - \ell ( f ( x ^ { \prime } ; \theta ) , y ^ { \prime } ) | \leq M$ for all $\theta \in \Theta$ and all $( x , y ) , ( x ^ { \prime } , y ^ { \prime } ) \in \mathcal { X } \times \mathcal { Y }$ . For example, $M = 1 { \mathrm { ~ i f ~ } } \ell$ is the 0-1 loss function. Theorem 3 presents a generalization bound for ordered SGD:

Theorem 3. Let Θ be a fixed subset of $\mathbb { R } ^ { d _ { \theta } }$ . Then, for any $\delta > 0$ , with probability at least $1 - \delta$ over an iid draw of n examples $\mathcal { D } = ( ( x _ { i } , y _ { i } ) ) _ { i = 1 } ^ { n }$ , the following holds for all $\theta \in \Theta .$

$$
\leq L _ {q} (\theta ; \mathcal {D}) + 2 \Re_ {n} (\Theta) + \frac {M s}{q} \sqrt {\frac {\ln (1 / \delta)}{2 n}} - \mathcal {Q} _ {n} (\Theta ; s, q),\tag{4}
$$

where $\begin{array} { r l r } { \mathcal { Q } _ { n } ( \Theta ; s , q ) } & { { } : = } & { \mathbb { E } _ { \bar { D } } [ \mathrm { i n f } _ { \theta \in \Theta } \sum _ { i = 1 } ^ { n } ( \frac { r _ { i } ( \theta ; \bar { D } ) } { q } - } \end{array}$ $\begin{array} { r } { \frac { 1 } { n } ) \ell ( f ( \bar { x } _ { i } ; \theta ) , \bar { y } _ { i } ) ] \ge 0 . } \end{array}$

The expected error $\mathbb { E } _ { ( x , y ) } [ \ell ( f ( x ; \theta ) , y ) ]$ in the left-hand side of Equation (4) is a standard objective for generalization, whereas the right-hand side is an upper bound with the dependence on the algorithm parameters q and s. Let us first look at the asymptotic case when $n  \infty$ . Let Θ be constrained such that $\Re _ { n } ( \Theta )  0$ as $n  \infty$ , which has been shown to be satisfied for various models and sets Θ (Bartlett and Mendelson, 2002; Mohri et al., 2012; Bartlett et al., 2017; Kawaguchi et al., 2017). With $s / q$ being bounded, the third term in the right-hand side of Equation (4) disappear as $n \to \infty$ . Thus, it holds with high probability that $\begin{array} { r } { \mathbb { E } _ { ( { \boldsymbol { x } } , { \boldsymbol { y } } ) } [ \ell ( { \boldsymbol { f } } ( { \boldsymbol { x } } ; { \boldsymbol { \theta } } ) , { \boldsymbol { y } } ) ] \leq L _ { q } ( { \boldsymbol { \theta } } ; { \mathcal { D } } ) - \bar { \mathcal { Q } } _ { n } ( \bar { \boldsymbol { \Theta } } ; { \boldsymbol { s } } , { \boldsymbol { q } } ) \leq } \end{array}$ $L _ { q } ( \theta ; { \mathcal { D } } )$ , where $L _ { q } ( \theta ; { \mathcal { D } } )$ is minimized by ordered SGD as shown in Theorem 1 and Theorem 2. From this viewpoint, ordered SGD minimizes the expected error for generalization when $n \to \infty$

A special case of Theorem 3 recovers the standard generalization bound of the empirical average loss (e.g., Mohri et al., 2012), That is, if $q \ : = \ : s .$ ordered SGD becomes the standard mini-batch SGD and Equation

(4) becomes

$$
\mathbb {E} _ {(x, y)} [ \ell (f (x; \theta), y) ] \leq L (\theta ; \mathcal {D}) + 2 \Re_ {n} (\Theta) + M \sqrt {\frac {\ln \frac {1}{\delta}}{2 n}},\tag{5}
$$

which is the standard generalization bound $( \mathrm { e . g . } $ Mohri et al., 2012). This is because if $q \ = \ s ,$ , then $\begin{array} { r } { \frac { r _ { i } ( \theta ; \bar { D } ) } { q } = \frac { 1 } { n } } \end{array}$ and hence $\mathcal { Q } _ { n } ( \Theta ; s , q ) = 0$

For the purpose of a simple comparison of ordered SGD and (mini-batch) SGD, consider the case where we fix a single subset $\Theta \subseteq \mathbb { R } ^ { d _ { \theta } }$ Let $\hat { \theta } _ { q }$ and $\hat { \theta } _ { s }$ be the parameter vectors obtained by ordered SGD and (mini-batch) SGD respectively as the results of training. Then, when $n \to \infty$ , with $s / q$ being bounded, the upper bound on the expected error for ordered SGD (the right hand-side of Equation 4) is (strictly) less than that for (mini-batch) SGD (the right hand-side of Equation 5) if $\mathcal { Q } _ { n } ( \Theta ; s , q ) + L ( \hat { \theta } _ { s } ; \mathcal { D } ) - L _ { q } ( \hat { \theta } _ { q } ; \mathcal { D } ) > 0$ or if $L ( \hat { \theta } _ { s } ; \mathcal { D } ) - L _ { q } ( \hat { \theta } _ { q } ; \mathcal { D } ) > 0 ,$

For a given model $f ,$ whether Theorem 3 provides a non-vacuous bound depends on the choice of Θ. In $\mathrm { A p \mathrm { - } }$ pendix B, we discuss this efect as well as a standard way to derive various data-dependent bounds from Theorem 3.

## 6 Experiments

In this section, we empirically evaluate ordered SGD with various datasets, models and settings. To avoid an extra freedom due to the hyper-parameter q, we introduce a single fixed setup of the adaptive values of $q$ as the default setting: $q = s$ at the beginning of training, $q = \lfloor s / 2 \rfloor$ once train acc ≥ 80%, $q = \lfloor s / 4 \rfloor$ once train acc $\ge ~ 9 0 \% , ~ q = ~ \lfloor s / 8 \rfloor$ once train acc ≥ 95%, and $q = \lfloor s / 1 6 \rfloor$ once train acc $\geq 9 9 . 5 \%$ , where train acc represents training accuracy. The value of $q$ was automatically updated at the end of each epoch based on this simple rule. This rule was derived based on the intuition that in the early stage of training, all samples are informative to build a rough model, while the samples around the boundary (with larger losses) are more helpful to build the final classifier in later stage. In the figures and tables of this section, we refer to ordered SGD with this rule as ‘OSGD’, and ordered SGD with a fixed value $q = \bar { q } \mathrm { ~ a s ~ } { } ^ { \cdot } \mathrm { O S G D } { : } q = \bar { q } ^ { }$

Experiment with fixed hyper-parameters. For this experiment, we fixed all hyper-parameters a priori across all diferent datasets and models by using a standard hyper-parameter setting of mini-batch SGD, instead of aiming for state-of-the-art test errors for each dataset with a possible issue of over-fitting to test and validation datasets (Dwork et al., 2015; Rao et al., 2008). We fixed the mini-batch size s to be 64, the weight decay rate to be $1 0 ^ { - 4 } ,$ , the initial learning rate to be 0.01, and the momentum coeficient to be 0.9. See Appendix C for more details of the experimental settings. The code to reproduce all the results is publicly available at: [the link is hidden for anonymous submission].

Table 1: Test errors (%) of mini-batch SGD and ordered SGD (OSGD). The last column labeled “Improve” shows relative improvements (%) from mini-batch SGD to ordered SGD. In the other columns, the numbers indicate the mean test errors (and standard deviations in parentheses) over ten random trials. The first column shows ‘No’ for no data augmentation, and ‘Yes’ for data augmentation.

<table><tr><td>Data Aug</td><td>Datasets</td><td>Model</td><td>mini-batch SGD</td><td>OSGD</td><td>Improve</td></tr><tr><td>No</td><td>Semeion</td><td>Logistic model</td><td>10.76 (0.35)</td><td>9.31 (0.42)</td><td>13.48</td></tr><tr><td>No</td><td>MNIST</td><td>Logistic model</td><td>7.70 (0.06)</td><td>7.35 (0.04)</td><td>4.55</td></tr><tr><td>No</td><td>Semeion</td><td>SVM</td><td>11.05 (0.72)</td><td>10.25 (0.51)</td><td>7.18</td></tr><tr><td>No</td><td>MNIST</td><td>SVM</td><td>8.04 (0.05)</td><td>7.66 (0.07)</td><td>4.60</td></tr><tr><td>No</td><td>Semeion</td><td>LeNet</td><td>8.06 (0.61)</td><td>6.09 (0.55)</td><td>24.48</td></tr><tr><td>No</td><td>MNIST</td><td>LeNet</td><td>0.65 (0.04)</td><td>0.57 (0.06)</td><td>11.56</td></tr><tr><td>No</td><td>KMNIST</td><td>LeNet</td><td>3.74 (0.08)</td><td>3.09 (0.14)</td><td>17.49</td></tr><tr><td>No</td><td>Fashion-MNIST</td><td>LeNet</td><td>8.07 (0.16)</td><td>8.03 (0.26)</td><td>0.57</td></tr><tr><td>No</td><td>CIFAR-10</td><td>PreActResNet18</td><td>13.75 (0.22)</td><td>12.87 (0.32)</td><td>6.41</td></tr><tr><td>No</td><td>CIFAR-100</td><td>PreActResNet18</td><td>41.80 (0.40)</td><td>41.32 (0.43)</td><td>1.17</td></tr><tr><td>No</td><td>SVHN</td><td>PreActResNet18</td><td>4.66 (0.10)</td><td>4.39 (0.11)</td><td>5.95</td></tr><tr><td>Yes</td><td>Semeion</td><td>LeNet</td><td>7.47 (1.03)</td><td>5.06 (0.69)</td><td>32.28</td></tr><tr><td>Yes</td><td>MNIST</td><td>LeNet</td><td>0.43 (0.03)</td><td>0.39 (0.03)</td><td>9.84</td></tr><tr><td>Yes</td><td>KMNIST</td><td>LeNet</td><td>2.59 (0.09)</td><td>2.01 (0.13)</td><td>22.33</td></tr><tr><td>Yes</td><td>Fashion-MNIST</td><td>LeNet</td><td>7.45 (0.07)</td><td>6.49 (0.19)</td><td>12.93</td></tr><tr><td>Yes</td><td>CIFAR-10</td><td>PreActResNet18</td><td>8.08 (0.17)</td><td>7.04 (0.12)</td><td>12.81</td></tr><tr><td>Yes</td><td>CIFAR-100</td><td>PreActResNet18</td><td>29.95 (0.31)</td><td>28.31 (0.41)</td><td>5.49</td></tr><tr><td>Yes</td><td>SVHN</td><td>PreActResNet18</td><td>4.45 (0.07)</td><td>4.00 (0.08)</td><td>10.08</td></tr></table>

Table 1 compares the testing performance of ordered SGD and mini-batch SGD for diferent models and datasets. Table 1 consistently shows that ordered SGD improved mini-batch SGD in test errors. The table reports the mean and the standard deviation of test errors (i.e., 100 × the average of 0-1 losses on test dataset) over 10 random experiments with diferent random seeds. The table also summarises the relative improvements of ordered SGD over mini-batch SGD, which is defined as [100× ((mean test error of minibatch SGD) - (mean test error of ordered SGD)) / (mean test error of mini-batch SGD)]. Logistic model refers to linear multinomial logistic regression model, SVM refers to linear multiclass support vector machine, LeNet refers to a standard variant of LeNet (LeCun et al., 1998) with ReLU activations, and Pre-ActResNet18 refers to pre-activation ResNet with 18 layers (He et al., 2016).

Figure 3 shows the test error and the average training loss of mini-batch SGD and ordered SGD versus the number of epoch. As shown in the figure, ordered SGD with the fixed q value also outperformed minibatch SGD in general. In the figures, the reported training losses refer to the standard empirical average loss $\textstyle { \frac { 1 } { n } } \sum _ { i = 1 } ^ { n } L _ { i } ( \theta )$ measured at the end of each epoch. When compared to mini-batch SGD, ordered SGD had lower test errors while having higher training losses in Figures 3a, 3d and ${ \mathrm { 3 g } } ,$ because ordered SGD optimizes over the ordered empirical loss instead. This is consistent with our motivation and theory of ordered SGD in Sections 3, 4 and 5. The qualitatively similar behaviors were also observed with all of the 18 various problems as shown in Appendix C.

Moreover, ordered SGD is a computationally eficient algorithm. Table 2 shows the wall-clock time in illustrative four experiments, whereas Table 4 in Appendix C summarizes the wall-clock time in all experiments. The wall-clock time of ordered SGD measures the time spent by all computations of ordered SGD, including the extra computation of finding top-q samples in a mini-batch (line 4 of Algorithm 1). The extra computation is generally negligible and can be completed in O(s log q) or O(s) by using a sorting/selection algorithm. The ordered SGD algorithm can be faster than mini-batch SGD because ordered SGD only computes the (sub-)gradient $\tilde { g } ^ { t }$ of the top-q samples (in line 5 of Algorithm 1). As shown in Tables 2 and 4, ordered SGD was faster than mini-batch SGD for all larger models with PreActResNet18. This is because the computational reduction of the back-propagation in ordered SGD can dominate the small extra cost of finding top-q samples in larger problems.

![](images/741e9ca4f6ed39d5d27e4622638aaf5a4b6fcd9dd4362ac887daeb60f0d3912f.jpg)  
(a) MNIST & Logistic

![](images/f965dc45df8c7b94050ea98ba42a22a1c70d014e14c6f68050ba636dc0096a76.jpg)  
(b) MNIST & LeNet

![](images/54b5d24fa6cee54549fd6a74eac53d9b79e111caf4d1f0b1d3f8d0ba5c156745.jpg)  
(c) KMNIST

![](images/50cebf4a91ca37f4257fdd05bd7f8c972cec0a09ff6a281941add09018f496c8.jpg)  
(d) CIFAR-10

![](images/af20c82072233cd8081846216693c12628d070b98797b07f11c92ebc18c4754d.jpg)  
(e) Semeion & LeNet

![](images/804b0751e981446dbc6b25e53d1b1dc7a2a2d278e1ba807cff7bee6831b1b686.jpg)  
(f) KMNIST

![](images/b737fc51ebb6a3d34f4fa12b5323dc11a330ca5b9d8ff85b2e38929dbac61edc.jpg)  
(g) CIFAR-100

![](images/7a842c9c7992ed23ce0574e2f8b0361e12a2de7ec8c7a54aefa6f26745344ffc.jpg)  
(h) SVHN  
Figure 3: Test error and training loss (in log scales) versus the number of epoch. These are without data augmentation in subfigures (a)-(d), and with data augmentation in subfigures (e)-(h). The lines indicate the mean values over 10 random trials, and the shaded regions represent intervals of the sample standard deviations.

Table 2: Average wall-clock time (seconds) per epoch with data augmentation. PreActResNet18 was used for CIFAR-10, CIFAR-100, and SVHN, while LeNet was used for MNIST and KMNIST.

<table><tr><td>Datasets</td><td>mini-batch SGD</td><td>OSGD</td></tr><tr><td>MNIST</td><td>14.44 (0.54)</td><td>14.77 (0.41)</td></tr><tr><td>KMNIST</td><td>12.17 (0.33)</td><td>11.42 (0.29)</td></tr><tr><td>CIFAR-10</td><td>48.18 (0.58)</td><td>46.40 (0.97)</td></tr><tr><td>CIFAR-100</td><td>47.37 (0.84)</td><td>44.74 (0.91)</td></tr><tr><td>SVHN</td><td>72.29 (1.23)</td><td>67.95 (1.54)</td></tr></table>

![](images/cbadcdfa298680833bab311460b451f92994f90bbce592a5c8055da3aadc4467.jpg)  
Figure 4: Efect of diferent q values with CIFAR-10.

Experiment with diferent q values. Figure 4 shows the efect of diferent fixed q values for CIFAR-10 with PreActResNet18. Ordered SGD improved the test errors of mini-batch SGD with diferent fixed q values. We also report the same observation with different datasets and models in Appendix C.

Experiment with diferent learning rates and mini-batch sizes. Figures 5 and 6 in Appendix C consistently show the improvement of ordered SGD over mini-batch SGD with diferent diferent learning rates and mini-batch sizes.

Table 3: Test errors (%) by using the best learning rate of mini-batch SGD with various data augmentation methods for CIFAR-10.

<table><tr><td>Data Aug</td><td>mini-batch SGD</td><td>OSGD</td><td>Improve</td></tr><tr><td>Standard</td><td>6.94</td><td>6.46</td><td>6.92</td></tr><tr><td>RE</td><td>3.24</td><td>3.06</td><td>5.56</td></tr><tr><td>Mixup</td><td>3.31</td><td>3.05</td><td>7.85</td></tr></table>

Experiment with the best learning rate, mixup, and random erasing. Table 3 summarises the experimental results with the data augmentation methods of random erasing (RE) (Zhong et al., 2017) and mixup (Zhang et al., 2017; Verma et al., 2019) by using CIFAR-10 dataset. For this experiment, we purposefully adopted the setting that favors mini-batch SGD. That is, for both mini-batch SGD and ordered SGD, we used hyper-parameters tuned for mini-batch SGD. For RE and mixup data, we used the same tuned hyper-parameter settings (including learning rates) and the codes as those in the previous studies that used mini-batch SGD (Zhong et al., 2017; Verma et al., 2019) (with WRN-28-10 for RE and with PreActRes-Net18 for mixup). For standard data augmentation, we first searched the best learning rate of mini-batch SGD based on the test error (purposefully overfitting to the test dataset for mini-batch SGD) by using the grid search with learning rates of 1.0, 0.5, 0.1, 0.05. 0.01, 0.005, 0.001, 0.0005, 0.0001. Then, we used the best learning rate of mini-batch SGD for ordered SGD (instead of using the best learning rate of ordered SGD for ordered SGD). As shown in Table 3, ordered SGD with hyper-parameters tuned for mini-batch SGD still outperformed fine-tuned mini-batch SGD with the different data augmentation methods.

## 7 Related work and extension

Although there is no direct predecessor of our work, the following fields are related to this paper.

Other mini-batch stochastic methods. The proposed sampling strategy and our theoretical analyses are generic and can be extended to other (mini-batch) stochastic methods, including Adam (Kingma and Ba, 2014), stochastic mirror descent (Beck and Teboulle, 2003; Nedic and Lee, 2014; Lu, 2017; Lu et al., 2018; Zhang and He, 2018), and proximal stochastic subgradient methods (Davis and Drusvyatskiy, 2018). Thus, our results open up the research direction for further studying the proposed stochastic optimization framework with diferent base algorithms such as Adam and AdaGrad. To illustrate it, we presented ordered Adam and reported the numerical results in Appendix C.

Importance Sampling SGD. Stochastic gradient descent with importance sampling has been an active research area for the past several years (Needell et al., 2014; Zhao and Zhang, 2015; Alain et al., 2015; Loshchilov and Hutter, 2015; Gopal, 2016; Katharopoulos and Fleuret, 2018). In the convex setting, (Zhao and Zhang, 2015; Needell et al., 2014) show that the optimal sampling distribution for minimizing L(θ) is proportional to the per-sample gradient norm. However, maintaining the norm of gradient for individual samples can be computationally expensive when the dataset size n or the parameter vector size $d _ { \theta }$ is large in particular for many applications of deep learning. These importance sampling methods are inherently diferent from ordered SGD in that importance sampling is used to reduce the number of iterations for minimizing L(θ), whereas ordered SGD is designed to learn a diferent type of models by minimizing the new objective function $L _ { q } ( \theta )$

Average Top-k Loss. The average top-k loss is introduced by Fan et al. (2017) as an alternative to the empirical average loss L(θ). The ordered loss function $L _ { q } ( \theta )$ difers from the average top-k loss as shown in Section 4. Furthermore, our proposed framework is fundamentally diferent from the average top-k loss. First, the algorithms are diferent – the stochastic method proposed in Fan et al. (2017) utilizes duality of the function and is unusable for deep neural networks (and other non-convex problems), while our proposed method is a modification of mini-batch SGD that is usable for deep neural networks (and other non-convex problems) and scales well for large problems. Second, the optimization results are diferent, and in particular, the objective functions are diferent and we have convergence analysis for weakly convex (non-convex) functions. Finally, the focus of generalization property is diferent – Fan et al. (2017) focuses on the calibration for binary classification problem, while we focus on the generalization bound that works for general classification and regression problems.

Random-then-Greedy Procedure. Ordered SGD randomly picks a subset of samples and then greedily utilizes a part of the subset, which is related to the random-then-greedy procedure proposed recently in the diferent topic – the greedy weak learner for gradient boosting (Lu and Mazumder, 2018).

## 8 Conclusion

We have presented an eficient stochastic first-order method, ordered SGD, for learning an efective predictor in machine learning problems. We have shown that ordered SGD minimizes a new ordered empirical loss $L _ { q } ( \theta )$ , based on which we have developed the optimization and generalization properties of ordered SGD. The numerical experiments confirmed the efectiveness of our proposed algorithm.

## References

Abadi, M., Barham, P., Chen, J., Chen, Z., Davis, A., Dean, J., Devin, M., Ghemawat, S., Irving, G., Isard, M., et al. (2016). Tensorflow: A system for large-scale machine learning. In 12th {USENIX} Symposium on Operating Systems Design and Implementation ({OSDI} 16), pages 265–283.

Alain, G., Lamb, A., Sankar, C., Courville, A., and Bengio, Y. (2015). Variance reduction in sgd by distributed importance sampling. arXiv preprint arXiv:1511.06481.

Allen-Zhu, Z. (2017). Natasha: Faster non-convex stochastic optimization via strongly non-convex parameter. In Proceedings of the 34th International Conference on Machine Learning-Volume 70, pages 89–97. JMLR. org.

Bartlett, P. L., Foster, D. J., and Telgarsky, M. J. (2017). Spectrally-normalized margin bounds for neural networks. In Advances in Neural Information Processing Systems, pages 6240–6249.

Bartlett, P. L. and Mendelson, S. (2002). Rademacher and gaussian complexities: Risk bounds and structural results. Journal of Machine Learning Research, 3(Nov):463–482.

Beck, A. and Teboulle, M. (2003). Mirror descent and nonlinear projected subgradient methods for convex optimization. Operations Research Letters, 31(3):167–175.

Bottou, L., Curtis, F. E., and Nocedal, J. (2018). Optimization methods for large-scale machine learning. Siam Review, 60(2):223–311.

Boyd, S. and Mutapcic, A. (2008). Stochastic subgradient methods. Lecture Notes for EE364b, Stanford University.

Davis, D. and Drusvyatskiy, D. (2018). Stochastic subgradient method converges at the rate $O ( k ^ { - 1 / 4 } )$ on weakly convex functions. arXiv preprint arXiv:1802.02988.

Dean, J., Corrado, G., Monga, R., Chen, K., Devin, M., Mao, M., Senior, A., Tucker, P., Yang, K., Le, Q. V., et al. (2012). Large scale distributed deep networks. In Advances in neural information processing systems, pages 1223–1231.

Dwork, C., Feldman, V., Hardt, M., Pitassi, T., Reingold, O., and Roth, A. (2015). The reusable holdout: Preserving validity in adaptive data analysis. Science, 349(6248):636–638.

Fan, Y., Lyu, S., Ying, Y., and Hu, B. (2017). Learning with average top-k loss. In Advances in Neural Information Processing Systems, pages 497–505.

Gopal, S. (2016). Adaptive sampling for SGD by exploiting side information. In International Conference on Machine Learning, pages 364–372.

He, K., Zhang, X., Ren, S., and Sun, J. (2016). Identity mappings in deep residual networks. In European Conference on Computer Vision, pages 630– 645. Springer.

Katharopoulos, A. and Fleuret, F. (2018). Not all samples are created equal: Deep learning with importance sampling. In International Conference on Machine Learning, pages 2530–2539.

Kawaguchi, K., Kaelbling, L. P., and Bengio, Y. (2017). Generalization in deep learning. arXiv preprint arXiv:1710.05468.

Kingma, D. P. and Ba, J. (2014). Adam: A method for stochastic optimization. arXiv preprint arXiv:1412.6980.

LeCun, Y., Bottou, L., Bengio, Y., and Hafner, P. (1998). Gradient-based learning applied to document recognition. Proceedings of the IEEE, 86(11):2278–2324.

Loshchilov, I. and Hutter, F. (2015). Online batch selection for faster training of neural networks. arXiv preprint arXiv:1511.06343.

Lu, H. (2017). ” relative-continuity” for non-lipschitz non-smooth convex optimization using stochastic (or deterministic) mirror descent. arXiv preprint arXiv:1710.04718.

Lu, H., Freund, R., and Mirrokni, V. (2018). Accelerating greedy coordinate descent methods. In International Conference on Machine Learning, pages 3263–3272.

Lu, H. and Mazumder, R. (2018). Randomized gradient boosting machine. arXiv preprint arXiv:1810.10158.

Mohri, M., Rostamizadeh, A., and Talwalkar, A. (2012). Foundations of machine learning. MIT press.

Nedic, A. and Lee, S. (2014). On stochastic subgradi ent mirror-descent algorithm with weighted averaging. SIAM Journal on Optimization, 24(1):84–107.

Needell, D., Ward, R., and Srebro, N. (2014). Stochastic gradient descent, weighted sampling, and the randomized kaczmarz algorithm. In Advances in Neural Information Processing Systems, pages 1017–1025.

Paszke, A., Gross, S., Chintala, S., Chanan, G., Yang, E., DeVito, Z., Lin, Z., Desmaison, A., Antiga, L., and Lerer, A. (2017). Automatic diferentiation in pytorch. In Autodif Workshop at Conference on Neural Information Processing Systems.

Rao, R. B., Fung, G., and Rosales, R. (2008). On the dangers of cross-validation. an experimental evaluation. In Proceedings of the 2008 SIAM international conference on data mining, pages 588–596. SIAM.

Rockafellar, R. T. and Wets, R. J.-B. (2009). Variational analysis, volume 317. Springer Science & Business Media.

Seide, F. and Agarwal, A. (2016). Cntk: Microsoft’s open-source deep-learning toolkit. In Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, pages 2135–2135. ACM.

Shalev-Shwartz, S. and Wexler, Y. (2016). Minimizing the maximal loss: How and why. In International Conference on Machine Learning, pages 793–801.

Verma, V., Lamb, A., Beckham, C., Najafi, A., Mitliagkas, I., Lopez-Paz, D., and Bengio, Y. (2019). Manifold mixup: Better representations by interpolating hidden states. In International Conference on Machine Learning, pages 6438–6447.

Weston, J., Watkins, C., et al. (1999). Support vector machines for multi-class pattern recognition. In Esann, volume 99, pages 219–224.

Zhang, H., Cisse, M., Dauphin, Y. N., and Lopez-Paz, D. (2017). mixup: Beyond empirical risk minimization. arXiv preprint arXiv:1710.09412.

Zhang, S. and He, N. (2018). On the convergence rate of stochastic mirror descent for nonsmooth nonconvex optimization. arXiv preprint arXiv:1806.04781.

Zhao, P. and Zhang, T. (2015). Stochastic optimization with importance sampling for regularized loss minimization. In international conference on machine learning, pages 1–9.

Zhong, Z., Zheng, L., Kang, G., Li, S., and Yang, Y. (2017). Random erasing data augmentation. arXiv preprint arXiv:1708.04896.

## Appendix

## A Proofs

In Appendix A, we provide complete proofs of the theoretical results.

## A.1 Proof of Theorem 1

Proof. We just need to show that ˜g is an unbiased estimator of a sub-gradient of $L _ { q } ( \theta )$ at $\theta ^ { t }$ , namely $\mathbb { E } \tilde { g } \in \partial L _ { q } ( \theta ^ { t } )$ At first, it holds that

$$
\mathbb {E} \tilde {g} ^ {t} = \frac {1}{q} \mathbb {E} \sum_ {i \in Q} g _ {i} ^ {t} + g _ {R} ^ {t} = \frac {1}{q} \sum_ {i = 1} ^ {n} P (i \in Q) g _ {i} ^ {t} + g _ {R} ^ {t} = \frac {1}{q} \sum_ {j = 1} ^ {n} P ((j) \in Q) g _ {(j)} ^ {t} + g _ {R} ^ {t},
$$

where $g _ { i } ^ { t } \in \partial L _ { i } ( \theta ^ { t } )$ is a sub-gradient of $L _ { i }$ at $\theta ^ { t }$ and $g _ { R } ^ { t } \in \partial R ( \theta ^ { t } )$ . In the above equality chain, the third equality is simply the definition of expectation, and the last equality is because $( ( 1 ) , ( 2 ) , \ldots , ( n ) )$ is a permutation of $( 1 , 2 , \ldots , n )$

For any given index j, define $A _ { j } = ( ( 1 ) , ( 2 ) , \dotsc , ( j - 1 ) )$ , then

$$
\begin{array}{r l} {P ((j) \in Q)} & {= P \left((j) \in \mathrm{q-argmax} _ {i \in S} L _ {i} (\theta)\right)} \\ & {= P \left((j) \in S \text {and} S \text {contains at most} q - 1 \text {items in} A _ {j}\right)} \\ & {= P \left((j) \in S\right) P \left(S \text {contains at most} q - 1 \text {items in} A _ {j} | (j) \in S\right)} \\ & {= P \left((j) \in S\right) \sum_ {l = 0} ^ {q - 1} P \left(S \text {contains l items in} A _ {j} | (j) \in S\right).} \end{array}\tag{6}
$$

Notice that S is randomly chosen from sample index set $( 1 , 2 , \ldots , n )$ without replacement. There are in total $\binom { n } { s }$ diferent sets S such that $| S | = s$ . Among them, there are $\binom { n - 1 } { s - 1 }$ diferent sets $S$ which contains the index (j), thus

$$
P \left((j) \in S\right) = \frac {\binom {n - 1} {s - 1}}{\binom {n} {s}} .\tag{7}
$$

Given the condition $( j ) \in S , s$ S contains l items in $A _ { j }$ means $S$ contains $s - l - 1$ items in $\{ ( j + 1 ) , ( j + 2 ) \ldots , ( n ) \}$ thus there are $\binom { j - 1 } { l } \binom { n - j } { s - l - 1 }$ such possible set $S _ { \mathrm { { ; } } }$ whereby it holds that

$$
P \left(S \text {   contains   } l \text {   items   in   } A _ {j} | (j) \in S\right) = \frac {\binom {j - 1} {l} \binom {n - j} {s - l - 1}}{\binom {n - 1} {s - 1}} .\tag{8}
$$

Substituting Equations (7) and (8) into Equation (6), we arrive at

$$
P ((j) \in T) = \frac {\binom {n - 1} {s - 1}}{\binom {n} {s}} \sum_ {l = 0} ^ {q - 1} \frac {\binom {j - 1} {l} \binom {n - j} {s - l - 1}}{\binom {n - 1} {s - 1}} = \frac {\sum_ {l = 0} ^ {q - 1} \binom {j - 1} {l} \binom {n - j} {s - l - 1}}{\binom {n} {s}} = \gamma_ {j} .
$$

Therefore,

$$
\mathbb {E} \tilde {g} ^ {t} = \frac {1}{q} \sum_ {j = 1} ^ {n} P ((j) \in Q) g _ {(j)} ^ {t} + g _ {R} ^ {t} = \frac {1}{q} \sum_ {j = 1} ^ {n} \gamma_ {j} g _ {(j)} ^ {t} + g _ {R} ^ {t} \in \partial L _ {q} (\theta^ {t}),
$$

where the last inequality is due to the aditivity of sub-gradient (for both convex and weakly convex function)

## A.2 Proof of Proposition 1

We just need to show that

$$
\lim _ {j, n \to \infty , j / n = z} \gamma_ {j} = \sum_ {l = 0} ^ {q - 1} \frac {1}{n} \left(\frac {j}{n}\right) ^ {l} \left(\frac {n - j}{n}\right) ^ {s - l - 1} \frac {s !}{l ! (s - l - 1) !},\tag{9}
$$

then we finish the proof by changing variable $\textstyle z = { \frac { j } { n } }$

At first, the Stirling’s approximation yields that when n and j are both suficiently large, it holds that

$$
\binom {n} {j} \sim \sqrt {\frac {n}{2 \pi j (n - j)}} \frac {n ^ {n}}{j ^ {j} (n - j) ^ {n - j}}  .\tag{10}
$$

Thus,

$$
\lim _ {j, n \to \infty , j / n = z} \frac {\binom {n - s} {j - 1 - l}}{\binom {n - 1} {j - 1}} = \frac {\frac {n ^ {n - s}}{j ^ {j - 1 - l} (n - j) ^ {n - j - s + 1 + l}}}{\frac {n ^ {n - 1}}{j ^ {j - 1} (n - j) ^ {n - j}}} = \frac {j ^ {l} (n - j) ^ {s - l - 1}}{n ^ {s - 1}} = \left(\frac {j}{n}\right) ^ {l} \left(\frac {n - j}{n}\right) ^ {s - l - 1},\tag{11}
$$

where the first equality utilize Equation (10) and the fact that $s , l , \bar { . }$ 1 are negligible in the limit case (except the exponent terms).

On the other hand, it holds by rearranging the factorial numbers that

$$
\frac {1}{n} \frac {\binom {n - s} {j - 1 - l}}{\binom {n - 1} {j - 1}} \frac {s !}{l ! (s - l - 1) !} = \frac {\binom {j - 1} {l} \binom {n - j} {s - l - 1}}{\binom {n} {s}} .\tag{12}
$$

Combining Equations (11) and (12) and summing l, we arrive at Equation (9).

By noticing $s > q ,$ it holds that

$$
\begin{array}{l} \frac {d}{d z} \gamma (z) = \sum_ {l = 1} ^ {q - 1} l z ^ {l - 1} (1 - z) ^ {s - l - 1} \frac {s !}{l ! (s - l - 1) !} - \sum_ {l = 0} ^ {q - 1} (s - l - 1) z ^ {l} (1 - z) ^ {s - l - 2} \frac {s !}{l ! (s - l - 1) !} \\ \qquad = \sum_ {l = 1} ^ {q - 1} z ^ {l - 1} (1 - z) ^ {s - l - 1} \frac {s !}{(l - 1) ! (s - l - 1) !} - \sum_ {l = 0} ^ {q - 1} z ^ {l} (1 - z) ^ {s - l - 2} \frac {s !}{l ! (s - l - 2) !} \\ \qquad = \sum_ {l = 0} ^ {q - 2} z ^ {l} (1 - z) ^ {s - l - 2} \frac {s !}{l ! (s - l - 2) !} - \sum_ {l = 0} ^ {q - 1} z ^ {l} (1 - z) ^ {s - l - 2} \frac {s !}{l ! (s - l - 2) !} \\ \qquad = - z ^ {q - 1} (1 - z) ^ {s - q - 1} \frac {s !}{l ! (s - l - 2) !} \\ \qquad \propto - z ^ {q - 1} (1 - z) ^ {s - q - 1}. \end{array}
$$

In other word, $1 - { \textstyle \frac { 1 } { s } } \gamma ( z )$ is the cumulative of Beta $( q , s - q )$ when $n \to \infty$

## A.3 Proof of Theorem 2

Proof. Notice that $\tilde { g } ^ { t }$ is a sub-gradient of $L _ { Q } ( \theta ^ { t } )$ where $\begin{array} { r } { L _ { Q } ( \theta ^ { t } ) ~ = ~ \frac { 1 } { a } \sum _ { i \in Q } L _ { i } ( \theta ^ { t } ) + R ( \theta ^ { t } ) } \end{array}$ . Suppose $\tilde { g } ^ { t } \ =$ $\begin{array} { r } { \frac { 1 } { q } \sum _ { i \in Q } g _ { i } ( \theta ^ { t } ) + g _ { R } ( \theta ^ { t } ) } \end{array}$ where $g _ { i } ( \theta ^ { t } )$ is a sub-gradient of $L _ { i } ( \theta ^ { t } )$ and $g _ { R } ( \theta ^ { t } )$ is a sub-gradient of $R ( \theta ^ { t } )$ . Then

$$
\| \tilde {g} ^ {t} \| ^ {2} = \left\| \frac {1}{q} \sum_ {i \in Q} g _ {i} (\theta^ {t}) + g _ {R} (\theta^ {t}) \right\| ^ {2} \leq 2 \left(\left\| \frac {1}{q} \sum_ {i \in Q} g _ {i} (\theta^ {t}) \right\| ^ {2} + \left\| g _ {R} (\theta^ {t}) \right\| ^ {2}\right) \leq 2 (G _ {1} ^ {2} + G _ {2} ^ {2}).\tag{13}
$$

Meanwhile, it follows Theorem 1 that $\tilde { g } ^ { t }$ is an unbiased estimator of a sub-gradient of $L _ { q } ( \theta ^ { t } )$ . Together with Equation (13), we obtain the statement (1) by the analysis of convex stochastic sub-gradient descent in Boyd and Mutapcic (2008).

Furthermore, suppose $\begin{array} { r } { L _ { i } ( \theta ) + \frac { \rho } { 2 } \lVert \theta \rVert ^ { 2 } } \end{array}$ is convex for any $i ,$ then $\begin{array} { r } { L _ { q } ( \theta ) + \frac { \rho } { 2 } \| \theta \| ^ { 2 } = \frac { 1 } { q } \sum _ { j = 1 } ^ { n } \gamma _ { j } \left( L _ { ( j ) } ( \theta ) + \frac { \rho } { 2 } \| \theta \| ^ { 2 } \right) + R ( \theta ) } \end{array}$ is also convex, whereby $L _ { q } ( \theta )$ is ρ-weakly convex. We obtain the statement $( 2 )$ by substituting into Theorem 2.1 in Davis and Drusvyatskiy (2018). □

## A.4 Proof of Theorem 3

Before proving Theorem 3, we first show the following proposition, which gives an upper bound for $\gamma _ { j } \colon$ Proposition 2. For any $j \in \{ 1 , \dots , n \} , \ \gamma _ { j } \leq { \frac { s } { n } }$

Proof. The value of $\gamma _ { j }$ is equal to the probability of ordered SGD choosing the j-th sample in the ordered sequence $( L _ { ( 1 ) } ( \theta ; { \mathcal { D } } ) , \ldots , L _ { ( n ) } ( { \dot { \theta } } ; { \mathcal { D } } ) )$ , which is at most the probability of mini-batch SGD choosing the j-th sample. The probability of mini-batch SGD choosing the j-th sample is $\textstyle { \frac { s } { n } }$ □

We are now ready to prove Theorem 3 by finding an upper bound on $\begin{array} { r l } {  { \operatorname* { s u p } _ { \theta \in \Theta } \mathbb { E } _ { ( x , y ) } [ \ell ( f ( x ; \theta ) , y ) ] - L _ { q } ( \theta ; \mathcal { D } ) } \quad } & { { } } \end{array}$ based on McDiarmid’s inequality.

Proof of Theorem 3. Define $\begin{array} { r } { \Phi ( \mathcal D ) = \operatorname* { s u p } _ { \theta \in \Theta } \mathbb E _ { ( x , y ) } [ \ell ( f ( x ; \theta ) , y ) ] - L _ { q } ( \theta ; \mathcal D ) } \end{array}$ . In this proof, our objective is to provide the upper bound on $\Phi ( \mathcal { D } )$ by using McDiarmid’s inequality. To apply McDiarmid’s inequality to $\Phi ( { \mathcal { D } } )$ we first show that $\Phi ( \mathcal { D } )$ satisfies the remaining condition of McDiarmid’s inequality. Let D and $\mathcal { D } ^ { \prime }$ be two datasets difering by exactly one point of an arbitrary index $i _ { 0 } ;$ i.e., $\mathcal { D } _ { i } = \mathcal { D } _ { i } ^ { \prime }$ for all $i \neq i _ { 0 }$ and $\mathcal { D } _ { i _ { 0 } } \neq \mathcal { D } _ { i _ { 0 } } ^ { \prime }$ . Then, we provide an upper bound on $\Phi ( \mathcal { D } ^ { \prime } ) - \Phi ( \mathcal { D } )$ as follows:

$$
\begin{array}{l} \Phi (\mathcal {D} ^ {\prime}) - \Phi (\mathcal {D}) \leq \sup _ {\theta \in \Theta} L _ {q} (\theta ; \mathcal {D}) - L _ {q} (\theta ; \mathcal {D} ^ {\prime}). \\ \qquad = \sup _ {\theta \in \Theta} \frac {1}{q} \sum_ {j = 1} ^ {n} \gamma_ {j} (L _ {(j)} (\theta ; \mathcal {D}) - L _ {(j)} (\theta ; \mathcal {D} ^ {\prime})) \\ \qquad \leq \sup _ {\theta \in \Theta} \frac {1}{q} \sum_ {j = 1} ^ {n} | \gamma_ {j} | | L _ {(j)} (\theta ; \mathcal {D}) - L _ {(j)} (\theta ; \mathcal {D} ^ {\prime}) | \\ \qquad \leq \sup _ {\theta \in \Theta} \frac {1}{q} \frac {s}{n} \sum_ {j = 1} ^ {n} | L _ {(j)} (\theta ; \mathcal {D}) - L _ {(j)} (\theta ; \mathcal {D} ^ {\prime}) | \end{array}
$$

where the first line follows the property of the supremum, $\operatorname* { s u p } ( a ) - \operatorname* { s u p } ( b ) \leq \operatorname* { s u p } ( a - b )$ , the second line follows the definition of $L _ { q } .$ , and the last line follows Proposition $2 \ ( | \gamma _ { j } | \leq \frac { s } { n } )$

We now bound the last term $\begin{array} { r l } { \sum _ { j = 1 } ^ { n } | L _ { ( j ) } ( \theta ; \mathcal { D } ) - L _ { ( j ) } ( \theta ; \mathcal { D } ^ { \prime } ) | } & { { } } \end{array}$ . This requires a careful examination because $| L _ { ( j ) } ( \theta ; \mathcal { D } ) - L _ { ( j ) } ( \theta ; \mathcal { D } ^ { \prime } ) | \neq 0$ for more than one index j (although D and $\mathcal { D } ^ { \prime }$ difer only by exactly one point). This is because it is possible to have $( j ; \mathcal { D } ) \neq ( j ; \mathcal { D } ^ { \prime } )$ for many indexes $j$ where $\left( j ; \mathcal { D } \right) = \left( j \right)$ in $L _ { \left( j \right) } ( \theta ; \mathcal { D } )$ and $\left( j ; \mathcal { D } ^ { \prime } \right) = \left( j \right)$ in $L _ { \left( j \right) } ( \theta ; \mathcal { D } ^ { \prime } )$ . To analyze this efect, we now conduct case analysis. Define $l ( i ; \mathcal { D } )$ such that $( j ) = i$ where $\boldsymbol { j } = \boldsymbol { l } ( i ; \mathcal { D } ) ; \mathrm { i . e . , ~ } L _ { i } ( \boldsymbol { \theta } ; \mathcal { D } ) = L _ { ( \boldsymbol { l } ( i ; \mathcal { D } ) ) } ( \boldsymbol { \theta } ; \mathcal { D } )$

Consider the case where $l ( i _ { 0 } ; \mathcal { D } ^ { \prime } ) \ge l ( i _ { 0 } ; \mathcal { D } )$ . Let $j _ { 1 } = l ( i _ { 0 } ; \mathcal { D } )$ and $j _ { 2 } = l ( i _ { 0 } ; \mathcal { D } ^ { \prime } )$ . Then,

$$
\begin{array}{l} \sum_ {j = 1} ^ {n} | L _ {(j)} (\theta ; \mathcal {D}) - L _ {(j)} (\theta ; \mathcal {D} ^ {\prime}) | = \sum_ {j = j _ {1}} ^ {j _ {2} - 1} | L _ {(j)} (\theta ; \mathcal {D}) - L _ {(j)} (\theta ; \mathcal {D} ^ {\prime}) | + | L _ {(j _ {2})} (\theta ; \mathcal {D}) - L _ {(j _ {2})} (\theta ; \mathcal {D} ^ {\prime}) | \\ \qquad = \sum_ {j = j _ {1}} ^ {j _ {2} - 1} | L _ {(j)} (\theta ; \mathcal {D}) - L _ {(j + 1)} (\theta ; \mathcal {D}) | + | L _ {(j _ {2})} (\theta ; \mathcal {D}) - L _ {(j _ {2})} (\theta ; \mathcal {D} ^ {\prime}) | \\ \qquad = \sum_ {j = j _ {1}} ^ {j _ {2} - 1} (L _ {(j)} (\theta ; \mathcal {D}) - L _ {(j + 1)} (\theta ; \mathcal {D})) + L _ {(j _ {2})} (\theta ; \mathcal {D}) - L _ {(j _ {2})} (\theta ; \mathcal {D} ^ {\prime}) \\ \qquad = L _ {(j _ {1})} (\theta ; \mathcal {D}) - L _ {(j _ {2})} (\theta ; \mathcal {D} ^ {\prime}) \\ \qquad \leq M, \end{array}
$$

where the first line uses the fact that $j _ { 2 } = l ( i _ { 0 } ; \mathcal { D } ^ { \prime } ) \ge l ( i _ { 0 } ; \mathcal { D } ) = j _ { 1 }$ where $i _ { 0 }$ is the index of samples difering in $\mathcal { D }$ and $\mathcal { D } ^ { \prime }$ . The second line follows the equality $( j ; \mathcal { D } ^ { \prime } ) = ( j + 1 ; \mathcal { D } )$ from $j _ { 1 }$ to $j _ { 2 } - 1$ in this case. The third line follows the definition of the ordering of the indexes. The fourth line follows the cancellations of the terms from the third line.

Consider the case where $l ( i _ { 0 } ; \mathcal { D } ^ { \prime } ) < l ( i _ { 0 } ; \mathcal { D } )$ . Let $j _ { 1 } = l ( i _ { 0 } ; \mathcal { D } ^ { \prime } )$ and $j _ { 2 } = l ( i _ { 0 } ; \mathcal { D } )$ . Then,

$$
\begin{array}{l} \sum_ {j = 1} ^ {n} | L _ {(j)} (\theta ; \mathcal {D}) - L _ {(j)} (\theta ; \mathcal {D} ^ {\prime}) | = | L _ {(j _ {1})} (\theta ; \mathcal {D}) - L _ {(j _ {1})} (\theta ; \mathcal {D} ^ {\prime}) | + \sum_ {j = j _ {1} + 1} ^ {j _ {2}} | L _ {(j)} (\theta ; \mathcal {D}) - L _ {(j)} (\theta ; \mathcal {D} ^ {\prime}) | \\ \qquad = | L _ {(j _ {1})} (\theta ; \mathcal {D}) - L _ {(j _ {1})} (\theta ; \mathcal {D} ^ {\prime}) | + \sum_ {j = j _ {1} + 1} ^ {j _ {2}} | L _ {(j)} (\theta ; \mathcal {D}) - L _ {(j - 1)} (\theta ; \mathcal {D}) | \\ \qquad = L _ {(j _ {1})} (\theta ; \mathcal {D}) - L _ {(j _ {1})} (\theta ; \mathcal {D} ^ {\prime}) + \sum_ {j = j _ {1} + 1} ^ {j _ {2}} (L _ {(j)} (\theta ; \mathcal {D}) - L _ {(j - 1)} (\theta ; \mathcal {D})) \\ \qquad = L _ {(j _ {1})} (\theta ; \mathcal {D} ^ {\prime}) - L _ {(j _ {2})} (\theta ; \mathcal {D}) \\ \qquad \leq M. \end{array}
$$

where the first line uses the fact that $j _ { 1 } = l ( i _ { 0 } ; \mathcal { D } ^ { \prime } ) < l ( i _ { 0 } ; \mathcal { D } ) = j _ { 2 }$ where $i _ { 0 }$ is the index of samples difering in $\mathcal { D }$ and $\mathcal { D } ^ { \prime }$ . The second line follows the equality $( j ; \mathcal { D } ^ { \prime } ) = ( j - 1 ; \mathcal { D } )$ from $j _ { 1 } + 1$ to $j _ { 2 }$ in this case. The third line follows the definition of the ordering of the indexes. The fourth line follows the cancellations of the terms from the third line.

Therefore, in both cases of $l ( i _ { 0 } ; \mathcal { D } ^ { \prime } ) \ge l ( i _ { 0 } ; \mathcal { D } )$ and $l ( i _ { 0 } ; \mathcal { D } ^ { \prime } ) < l ( i _ { 0 } ; \mathcal { D } )$ , we have that

$$
\Phi (\mathcal {D} ^ {\prime}) - \Phi (\mathcal {D}) \leq \frac {s}{q} \frac {M}{n}.
$$

Similarly, $\begin{array} { r } { \Phi ( \mathcal { D } ) - \Phi ( \mathcal { D } ^ { \prime } ) \leq \frac { s } { q } \frac { M } { n } } \end{array}$ , and hence $\begin{array} { r } { | \Phi ( \mathcal { D } ) - \Phi ( \mathcal { D } ^ { \prime } ) | \leq \frac { s } { q } \frac { M } { n } } \end{array}$ . Thus, by McDiarmid’s inequality, for any $\delta > 0$ , with probability at least $1 - \delta .$

$$
\Phi (\mathcal {D}) \leq \mathbb {E} _ {\bar {\mathcal {D}}} [ \Phi (\bar {\mathcal {D}}) ] + \frac {M s}{q} \sqrt {\frac {\ln (1 / \delta)}{2 n}}.
$$

Moreover, since

$$
\sum_ {i = 1} ^ {n} r _ {i} (\theta ; \mathcal {D}) L _ {i} (\theta ; \mathcal {D}) = \sum_ {j = 1} ^ {n} \gamma_ {j} \sum_ {i = 1} ^ {n} \mathbb {1} \{i = (j) \} L _ {i} (\theta ; \mathcal {D}) = \sum_ {j = 1} ^ {n} \gamma_ {j} L _ {(j)} (\theta ; \mathcal {D}),
$$

we have that

$$
L _ {q} (\theta ; \mathcal {D}) = \frac {1}{q} \sum_ {i = 1} ^ {n} r _ {i} (\theta ; \mathcal {D}) L _ {i} (\theta ; \mathcal {D}) + R (\theta).
$$

Therefore,

$$
\begin{array}{l} \mathbb {E} _ {\bar {\mathcal {D}}} [ \Phi (\bar {\mathcal {D}}) ] \\ = \mathbb {E} _ {\bar {\mathcal {D}}} \left[ \sup _ {\theta \in \Theta} \mathbb {E} _ {(\bar {x} ^ {\prime}, \bar {y} ^ {\prime})} [ \ell (f (\bar {x} ^ {\prime}; \theta), \bar {y} ^ {\prime}) ] - L (\theta ; \bar {\mathcal {D}}) + L (\theta ; \bar {\mathcal {D}}) - L _ {q} (\theta ; \bar {\mathcal {D}}) \right] \\ \leq \mathbb {E} _ {\bar {\mathcal {D}}} \left[ \sup _ {\theta \in \Theta} \mathbb {E} _ {(\bar {x} ^ {\prime}, \bar {y} ^ {\prime})} [ \ell (f (\bar {x} ^ {\prime}; \theta), \bar {y} ^ {\prime}) ] - L (\theta ; \bar {\mathcal {D}}) \right] - \mathcal {Q} _ {n} (\Theta ; s, q) \\ \leq \mathbb {E} _ {\bar {\mathcal {D}}, \bar {\mathcal {D}} ^ {\prime}} \left[ \sup _ {\theta \in \Theta} \frac {1}{n} \sum_ {i = 1} ^ {n} (\ell (f (\bar {x} _ {i} ^ {\prime}; \theta), \bar {y} _ {i} ^ {\prime}) - \ell (f (\bar {x} _ {i}; \theta), \bar {y} _ {i})) \right] - \mathcal {Q} _ {n} (\Theta ; s, q) \\ \leq \mathbb {E} _ {\xi , \bar {\mathcal {D}}, \bar {\mathcal {D}} ^ {\prime}} \left[ \sup _ {\theta \in \Theta} \frac {1}{n} \sum_ {i = 1} ^ {n} \xi_ {i} (\ell (f (\bar {x} _ {i} ^ {\prime}; \theta), \bar {y} _ {i} ^ {\prime}) - \ell (f (\bar {x} _ {i}; \theta), \bar {y} _ {i})) \right] - \mathcal {Q} _ {n} (\Theta ; s, q) \\ \leq 2 \Re_ {n} (\Theta) - \mathcal {Q} _ {n} (\Theta ; s, q). \end{array}
$$

where the third line and the last line follow the subadditivity of supremum, the forth line follows the Jensen’s inequality and the convexity of the supremum, the fifth line follows that for each $\xi _ { i } \in \{ - 1 , + 1 \}$ , the distribution of each term $\xi _ { i } ( \ell ( f ( \bar { x } _ { i } ^ { \prime } ; \theta ) , \bar { y } _ { i } ^ { \prime } ) - \ell ( f ( \bar { x } _ { i } ; \theta ) , \bar { y } _ { i } ) )$ is the distribution of $\left( \ell ( f ( \bar { x } _ { i } ^ { \prime } ; \theta ) , \bar { y } _ { i } ^ { \prime } ) - \ell ( f ( \bar { x } _ { i } ; \theta ) , \bar { y } _ { i } ) \right)$ since $\bar { \mathcal D }$ and $\bar { \mathcal { D } } ^ { \prime }$ are drawn iid with the same distribution. Therefore, for any $\delta > 0$ , with probability at least $1 - \delta$

$$
\Phi (\mathcal {D}) \leq 2 \Re_ {n} (\Theta) - \mathcal {Q} _ {n} (\Theta ; s, q) + \frac {M s}{q} \sqrt {\frac {\ln (1 / \delta)}{2 n}}.
$$

## B Additional discussion

The subset Θ in Theorem 3 characterizes the hypothesis space that is $\{ x \mapsto f ( x ; \theta ) : \theta \in \Theta \}$ . An important subtlety here is that given a parameterized model $f ,$ one can apply Theorem 3 to a subset Θ that depends on an algorithm and a distribution (but not directly on a dataset) such as $\Theta = \{ \theta \in \mathbb { R } ^ { d _ { y } } : ( \exists D \in$ $A ) [ \theta$ is the possible output of ordered SGD given $( f , \mathcal { D } ) ] \}$ where A is a fixed set of the training datasets such that ${ \mathcal { D } } \in A$ with high probability. Thus, even for the exact same model f and problem setting, Theorem 3 might provide non-vacuous bounds for some choices of Θ but not for other choices of Θ.

Moreover, we can easily obtain data-dependent bounds from Theorem 3 by repeatedly applying Theorem 3 to several subsets Θ and taking an union bound. For example, given a sequence $( \Theta _ { k } ) _ { k \in \mathbb { N } ^ { + } }$ , by applying Theorem 3 to each $\Theta _ { k }$ with $\delta = \delta ^ { \prime } \frac { 6 } { \pi ^ { 2 } k ^ { 2 } }$ (for each k) and by taking a union bound over all $k \in \mathbb { N } ^ { + }$ , the following statement holds: for any $\delta ^ { \prime } > 0$ , with probability at least $1 - \delta ^ { \prime }$ over an iid draw of n examples $\mathcal { D } = ( ( x _ { i } , y _ { i } ) ) _ { i = 1 } ^ { n }$ , we have that for all $k \in \mathbb { N } ^ { + }$ and $\theta \in \Theta _ { k }$

$$
\mathbb {E} _ {(x, y)} [ \ell (f (x; \theta), y) ] \leq L _ {q} (\theta ; \mathcal {D}) + 2 \Re_ {n} (\Theta_ {k}) + \frac {M s}{q} \sqrt {\frac {\ln (\pi^ {2} k ^ {2} / 6 \delta^ {\prime})}{2 n}} - \mathcal {Q} _ {n} (\Theta_ {k}; s, q).
$$

For example, let us choose $\Theta _ { k } = \{ \theta \in \mathbb { R } ^ { d _ { y } } : \left\| \theta \right\| \leq c _ { k } \}$ with some constants $c _ { 1 } < c _ { 2 } < \cdots$ Then, when we obtain a $\hat { \theta } _ { q }$ after training based on a particular training dataset D such that $c _ { \bar { k } - 1 } < \| \hat { \theta } _ { q } \| \leq c _ { \bar { k } }$ for some <sup>¯</sup>k, we can conclude the following: with probability at least $1 - \delta ^ { \prime } , \mathbb { E } _ { ( x , y ) } [ \ell ( f ( x ; \theta ) , y ) ] \le L _ { q } ( \widehat { \theta } _ { q } ; \mathcal { D } ) + 2 \Re _ { n } ( \Theta _ { \bar { k } } ) +$ $\begin{array} { r l r } { \frac { M s } { q } \sqrt { \frac { \ln ( \pi k ^ { 2 } / 6 \delta ^ { \prime } ) } { 2 n } } - \mathcal { Q } _ { n } ( \Theta _ { \bar { k } } ; s , q ) } \end{array}$ . This is data-dependent in the sense that $\Theta _ { \bar { k } }$ is selected in the data-dependent manner from $( \Theta _ { k } ) _ { k \in \mathbb { N } ^ { + } }$ . This is in contrast to the fact that as logically indicated in the theorem statement, one cannot directly apply Theorem 3 to a single subset Θ that directly depends on training dataset; e.g., one cannot apply Theorem 3 to a singleton set $\hat { \Theta } ( \mathcal { D } ) = \{ \hat { \theta } ( \mathcal { D } ) \}$ where $ { \hat { \theta } } (  { \mathcal { D } } )$ is the output of training given D.

## C Additional experimental results and details

## C.1 Additional results

Wall-clock time. Table 4 summarises the wall-clock time values (in seconds) of mini-batch SGD and ordered SGD. The wall-clock time was computed with identical, independent, and freed GPUs for fair comparison. The wall-clock time measures the time of the whole computations, including the extra computation of finding a set Q of top-q samples in S in term of loss values. As it can be seen, the extra computation of finding a set Q of top-q samples is generally negligible. Furthermore, for larger scale problems, ordered SGD tends to be faster per epoch because of the computational saving of not using the full mini-batch for the backpropagation computation.

Efect of diferent learning rates and mini-batch sizes. Figures 5 and 6 show the results with diferent learning rates and mini-batch sizes. Both use the same setting as that for CIFAR-10 with no data augmentation in others results shown in Table 1 and Figure 3. Figures 5 and 6 consistently show improvement of ordered SGD over mini-batch SGD for all learning rates and mini-batch sizes.

Behaviors with diferent datasets. Figure 7 shows the behaviors of mini-batch SGD vs ordered SGD. As it can be seen, ordered SGD generally improved mini-batch SGD in terms of test errors. With data argumentation, we also tried linear logistic regression for the Semeion dataset, and obtained the mean test errors of 19.11 for mini-batch SGD and 16.54 for ordered SGD (the standard deviations were 1.48 and 1.24); i.e., ordered SGD improved over mini-batch SGD, but the mean test errors without data-augmentation were better for both minibatch SGD and ordered SGD. This is because the data augmentation made it dificult to fit the augmented training dataset with linear models.

![](images/192a0ec9dffc80dec1101cc597016bcc936fc3d6e16f7628c79a8aac9bd2c81b.jpg)  
Figure 5: Test error and training loss (in log scales) versus the number of epoch with CIFAR-10 and no data augmentation by using diferent learning rates (LRs). The plotted values indicate the mean values over 10 random trials. The training loss values of LR=0.5 were ‘nan’ for both methods.

![](images/8df0b10119cd4386c3138af2ba34c2262ce6f292bb9950166a817f8f11ea6620.jpg)

![](images/73aaf5289ab7eca21ca90cba7259df2f128379d8766d9589f5170201a50d0494.jpg)  
Figure 6: Test error versus the number of epoch with CIFAR-10 and no data augmentation by using diferent mini-batch sizes s.

Efect of diferent values of q. Figure 8 shows the behaviors of mini-batch SGD vs ordered SGD with diferent q values. In the figure, label ‘ordered SGD’ corresponds to ordered SGD with the fixed adaptive rule, and other labels (e.g., ‘ordered SGD: q = 10’) corresponds to ordered SGD with the fixed value of q over the whole training procedure (e.g., with q = 10). All experiments in the figure were conducted with data augmentations. PreActResNet18 was used for CIFAR-10, while LeNet was used for other datasets. As it can be seen in Figure 8, ordered SGD generally improved the test errors of mini-batch SGD, even with fixed q values. When the value of q is fixed to be small as in q = 10, the small q value can be efective during the latter stage of training (e.g., Figure 8 b) while the training can be ineficient during the initial stage of training (e.g., Figure 8 c).

Results with ordered Adam. Table 5 compares the testing performance of ordered Adam and (standard) Adam for diferent models and datasets. The table reports the mean and the standard deviation of test errors (i.e., 100 × the average of 0-1 losses on test dataset) over 10 random experiments with diferent random seeds. The procedures of ordered Adam follow those of Adam except the additional sample strategy (line 3 - 4 of Algorithm 1). Table 5 shows that ordered Adam improved Adam for all settings, except CIFAR-10 with data augmentation. For CIFAR-10 with data augmentation, ordered SGD preformed the best among mini-batch SGD, Adam, ordered SGD, and ordered Adam, as it can be seen in Tables 1 and 5.

Table 4: Average wall-clock time (seconds) per epoch.

<table><tr><td>Data Aug</td><td>Datasets</td><td>Model</td><td>mini-batch SGD</td><td>ordered SGD</td><td>difference</td></tr><tr><td>No</td><td>Semeion</td><td>Logistic model</td><td>0.15 (0.01)</td><td>0.15 (0.01)</td><td>0.00</td></tr><tr><td>No</td><td>MNIST</td><td>Logistic model</td><td>7.16 (0.27)</td><td>7.32 (0.24)</td><td>-0.16</td></tr><tr><td>No</td><td>Semeion</td><td>SVM</td><td>0.17 (0.01)</td><td>0.17 (0.01)</td><td>0.00</td></tr><tr><td>No</td><td>MNIST</td><td>SVM</td><td>8.60 (0.31)</td><td>8.72 (0.29)</td><td>-0.12</td></tr><tr><td>No</td><td>Semeion</td><td>LeNet</td><td>0.18 (0.01)</td><td>0.18 (0.01)</td><td>0.00</td></tr><tr><td>No</td><td>MNIST</td><td>LeNet</td><td>9.00 (0.34)</td><td>9.12 (0.27)</td><td>-0.12</td></tr><tr><td>No</td><td>KMNIST</td><td>LeNet</td><td>9.23 (0.33)</td><td>9.04 (0.55)</td><td>0.19</td></tr><tr><td>No</td><td>Fashion-MNIST</td><td>LeNet</td><td>8.56 (0.48)</td><td>9.45 (0.31)</td><td>-0.90</td></tr><tr><td>No</td><td>CIFAR-10</td><td>PreActResNet18</td><td>45.55 (0.47)</td><td>43.72 (0.93)</td><td>1.82</td></tr><tr><td>No</td><td>CIFAR-100</td><td>PreActResNet18</td><td>46.83 (0.90)</td><td>43.95 (1.03)</td><td>2.89</td></tr><tr><td>No</td><td>SVHN</td><td>PreActResNet18</td><td>71.95 (1.40)</td><td>66.94 (1.67)</td><td>5.01</td></tr><tr><td>Yes</td><td>Semeion</td><td>LeNet</td><td>0.28 (0.02)</td><td>0.28 (0.02)</td><td>0.00</td></tr><tr><td>Yes</td><td>MNIST</td><td>LeNet</td><td>14.44 (0.54)</td><td>14.77 (0.41)</td><td>-0.32</td></tr><tr><td>Yes</td><td>KMNIST</td><td>LeNet</td><td>12.17 (0.33)</td><td>11.42 (0.29)</td><td>0.75</td></tr><tr><td>Yes</td><td>Fashion-MNIST</td><td>LeNet</td><td>12.23 (0.40)</td><td>12.38 (0.37)</td><td>-0.14</td></tr><tr><td>Yes</td><td>CIFAR-10</td><td>PreActResNet18</td><td>48.18 (0.58)</td><td>46.40 (0.97)</td><td>1.78</td></tr><tr><td>Yes</td><td>CIFAR-100</td><td>PreActResNet18</td><td>47.37 (0.84)</td><td>44.74 (0.91)</td><td>2.63</td></tr><tr><td>Yes</td><td>SVHN</td><td>PreActResNet18</td><td>72.29 (1.23)</td><td>67.95 (1.54)</td><td>4.34</td></tr></table>

![](images/0688b00d321b4c1ef8a4e2fdc19b511b52d734a86cb0a16a266cca1c660ec757.jpg)  
(a) Semeion & Logistic

![](images/1ca2296ae1d1236efaf8afcaabd888962706a253c843ded6446a57c02ee3117a.jpg)  
(b) MNIST & Logistic

![](images/d0c42b6874fedc7c4836545d293e41c2ac3cd713adf4519b772b1e2531d9b3a3.jpg)  
(c) Semeion & SVM

![](images/54e0e51356d05d7001e1981aef1fb30dbffd11f00904d30fc92643fb1d187861.jpg)  
(d) MNIST & SVM

![](images/1e94b524dfc807528221ad2f830e99d6e0c33cf4fb5e51d6bf97502030f46e14.jpg)  
(e) Semeion & LeNet

![](images/7dd6ac2096780af8f32be2d0bc7144594ca732566151408406a6c989c5389697.jpg)  
(f) MNIST & LeNet

![](images/9079d6aea440640314ec5cce1b9b0bf1de7c95749b984314d5e53785983e1008.jpg)  
(g) KMNIST

![](images/45040cd3b4e652d56019b03a2a51405884d97a27c5def6c2c0c89ad6e4bace89.jpg)  
(h) Fashion-MNIST

![](images/c2e1abf0dcb9b22b55bc1d0dfbf013786da8e108db8b6552a71dc6fa17a82712.jpg)  
(i) CIFAR-10

![](images/967ba4f39c720461099ee67456d921bb26a885fc354eda533eaa865d575b62ca.jpg)  
(j) CIFAR-100

![](images/bea6b5ed9a87004fa07ce3f60c9e554a026b30ccc427ecd3291b495e53280104.jpg)  
(k) SVHN

![](images/3c0daffc22d867066922603add5f8eab15860e7abc191becda787401c690a178.jpg)  
(l) Semeion & LeNet

![](images/285e27936d03186d20edab8fdc2950ae658c972c701a5364821c01bde9f39e9b.jpg)  
(m) MNIST & LeNet

![](images/2b9fdedf78345d65e3e6a5fa9871c3746fab151727aff382c115d56b5eaf1404.jpg)  
(n) KMNIST

![](images/bed6a524628de5c5860e64aab761f051b4bb2a130ca905131890a43b77ad8312.jpg)  
(o) Fashion-MNIST

![](images/dd3f0e05ac9e6df4f81326a06b2031b75d33c4f43f970e67d84df660d502bd48.jpg)  
(p) CIFAR-10

![](images/23ac6d192c5245cadcab1bd76841ada00e79cd7d5e4179c988a3f9e2db827d51.jpg)  
(q) CIFAR-100

![](images/b7b2532765c7278ad8342259327a18f0f700baeb9c46fb10bcccb26558ef5b48.jpg)  
(r) SVHN

Figure 7: Test error and training loss (in log scales) versus epoch for all experiments with mini-batch SGD and ordered SGD. These are without data augmentation in subfigures (a)-(k), and with data augmentation in subfigures (l)-(r). The plotted values are the mean values over ten random trials.

![](images/4f6774504a8f460d785a451c8b328981d66b2faa00475d176fb3d4ee4dfdf194.jpg)

![](images/7765d2060bb6ca76087ad03d3865a34502375dad7577c5e5eb9aebba49516d84.jpg)

![](images/0cdce77258786bbaf7847c5ed9e85bf9e4f7aa6827a12c972f798aa72fc9921f.jpg)

(a) CIFAR-10  
![](images/e19d293ea115cbf26f050876986596f067bae7f5687c26317bac9e46b65ea8b4.jpg)  
(c) Fashion-MNIST

(b) KMNIST  
![](images/0bea224346191faccba8771103be932e19ec78762bfaa90beefd8f8b57ead856.jpg)  
(d) Semeion  
Figure 8: Efect of diferent values of q.

Table 5: Test errors (%) of Adam and ordered Adam. The last column labeled “Improve” shows relative improvements (%) from Adam to ordered Adam. In the other columns, the numbers indicate the mean test errors (and standard deviations in parentheses) over ten random trials. The first column shows ‘No’ for no data augmentation, and ‘Yes’ for data augmentation.

<table><tr><td>Data Aug</td><td>Datasets</td><td>Model</td><td>Adam</td><td>ordered Adam</td><td>Improve</td></tr><tr><td>No</td><td>Semeion</td><td>Logistic model</td><td>12.12 (0.71)</td><td>10.37 (0.77)</td><td>14.46</td></tr><tr><td>No</td><td>MNIST</td><td>Logistic model</td><td>7.34 (0.03)</td><td>7.20 (0.03)</td><td>1.97</td></tr><tr><td>No</td><td>Semeion</td><td>SVM</td><td>11.45 (0.90)</td><td>10.91 (0.86)</td><td>4.71</td></tr><tr><td>No</td><td>MNIST</td><td>SVM</td><td>7.53 (0.03)</td><td>7.43 (0.02)</td><td>1.38</td></tr><tr><td>No</td><td>Semeion</td><td>LeNet</td><td>6.21 (0.64)</td><td>5.75 (0.42)</td><td>7.34</td></tr><tr><td>No</td><td>MNIST</td><td>LeNet</td><td>0.70 (0.04)</td><td>0.63 (0.04)</td><td>10.07</td></tr><tr><td>No</td><td>KMNIST</td><td>LeNet</td><td>3.14 (0.13)</td><td>3.13 (0.14)</td><td>0.60</td></tr><tr><td>No</td><td>Fashion-MNIST</td><td>LeNet</td><td>7.79 (0.17)</td><td>7.79 (0.21)</td><td>0.01</td></tr><tr><td>No</td><td>CIFAR-10</td><td>PreActResNet18</td><td>13.21 (0.42)</td><td>12.98 (0.27)</td><td>1.68</td></tr><tr><td>No</td><td>CIFAR-100</td><td>PreActResNet18</td><td>45.33 (0.89)</td><td>44.42 (0.72)</td><td>2.01</td></tr><tr><td>No</td><td>SVHN</td><td>PreActResNet18</td><td>4.72 (0.12)</td><td>4.64 (0.09)</td><td>1.52</td></tr><tr><td>Yes</td><td>Semeion</td><td>LeNet</td><td>5.80 (0.85)</td><td>5.70 (0.60)</td><td>1.74</td></tr><tr><td>Yes</td><td>MNIST</td><td>LeNet</td><td>0.45 (0.05)</td><td>0.44 (0.02)</td><td>3.10</td></tr><tr><td>Yes</td><td>KMNIST</td><td>LeNet</td><td>2.01 (0.08)</td><td>1.94 (0.16)</td><td>3.49</td></tr><tr><td>Yes</td><td>Fashion-MNIST</td><td>LeNet</td><td>6.61 (0.14)</td><td>6.56 (0.14)</td><td>0.82</td></tr><tr><td>Yes</td><td>CIFAR-10</td><td>PreActResNet18</td><td>7.92 (0.28)</td><td>8.03 (0.13)</td><td>-1.39</td></tr><tr><td>Yes</td><td>CIFAR-100</td><td>PreActResNet18</td><td>32.24 (0.52)</td><td>32.03 (0.52)</td><td>0.65</td></tr><tr><td>Yes</td><td>SVHN</td><td>PreActResNet18</td><td>4.42 (0.12)</td><td>4.19 (0.11)</td><td>5.29</td></tr></table>

## C.2 Additional details

For all experiments, mini-batch SGD and ordered SGD (as well as Adam and ordered Adam) were run with the same machine and the same PyTorch codes except a single-line modification:

• loss = torch.mean(loss) for mini-batch SGD and Adam

• loss = torch.mean(torch.topk(loss, min(q, s), sorted=False, dim=0)[0]) for ordered SGD and ordered Adam.

For 2-D illustrations in Figure 1. We used the (binary) cross entropy loss, s = 100, and 2 dimensional synthetic datasets with n = 200 in Figures 1a–1b and n = 1000 in Figures 1c–1d. The artificial neural network (ANN) used in Figures 1c and 1d is a fully-connected feedforward neural network with rectified linear units (ReLUs) and three hidden layers, where each hidden layer contained 20 neurons in Figures 1c and 10 neurons in Figures 1d.

For other numerical results. For mixup and random erasing, we used the same setting as in the corresponding previous papers (Zhong et al., 2017; Verma et al., 2019). For others, we divided the learning rate by 10 at the beginning of 10th epoch for all experiments (with and without data augmentation), and of 100th epoch for those with data augmentation. With $y \in \{ 1 , \dotsc , d _ { y } \}$ , we used the cross entropy loss $\begin{array} { r } { \ell ( a , y ) = - \log { \frac { \exp ( a _ { y } ) } { \sum _ { k ^ { \prime } } \exp ( a _ { k ^ { \prime } } ) } } } \end{array}$ for neural networks as well as multinomial logistic models, and a multiclass hinge loss $\begin{array} { r } { \ell ( a , y ) = \sum _ { k \neq y } ^ { - \infty } \operatorname* { m a x } ( 0 , 1 + } \end{array}$ $a _ { k } - a _ { y } )$ for SVMs (Weston et al., 1999). For the variant of LeNet, we used the following architecture with five layers (three hidden layers):

## 1. Input layer

2. Convolutional layer with 64 5 × 5 filters, followed by max pooling of size of 2 by 2 and ReLU.

3. Convolutional layer with 64 5 × 5 filters, followed by max pooling of size of 2 by 2 and ReLU.

4. Fully connected layer with 1014 output units, followed by ReLU.

5. Fully connected layer with the number of output units being equal to the number of target classes.