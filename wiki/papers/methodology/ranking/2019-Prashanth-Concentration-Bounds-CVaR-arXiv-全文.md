---
title: "2019-Prashanth-Concentration-Bounds-CVaR-arXiv"
date: 2026-09-04
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/ranking/2019-Prashanth-Concentration-Bounds-CVaR-arXiv.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Concentration bounds for CVaR estimation: The cases of light-tailed and heavy-tailed distributions

Prashanth L. A.<sup>1</sup>, Krishna Jagannathan<sup>2</sup>, and Ravi Kumar Kolla<sup>3</sup>

<sup>1</sup>Department of Computer Science and Engineering, Indian Institute of Technology Madras <sup>2</sup>Department of Electrical Engineering , Indian Institute of Technology Madras <sup>3</sup>ABInBev, Bangalore

## Abstract

Conditional Value-at-Risk (CVaR) is a widely used risk metric in applications such as finance. We derive concentration bounds for CVaR estimates, considering separately the cases of lighttailed and heavy-tailed distributions. In the light-tailed case, we use a classical CVaR estimator based on the empirical distribution constructed from the samples. For heavy-tailed random vari ables, we assume a mild ‘bounded moment’ condition, and derive a concentration bound for a truncation-based estimator. Notably, our concentration bounds enjoy an exponential decay in the sample size, for heavy-tailed as well as light-tailed distributions. To demonstrate the applicability of our concentration results, we consider a CVaR optimization problem in a multi-armed bandit setting. Specifically, we address the best CVaR-arm identification problem under a fixed budget. We modify the well-known successive rejects algorithm to incorporate a CVaR-based criterion. Using the CVaR concentration result, we derive an upper-bound on the probability of incorrect identification by the proposed algorithm.

## 1 Introduction

In applications such as portfolio optimization in finance, the quality of a portfolio is not satisfactorily captured by the expected value of return. Indeed, in such applications, a more risk-sensitive metric is desirable, so as to capture typical losses in the case of adverse events. Value-at-Risk (VaR) and Conditional-Value-at-Risk (CVaR) are two risk-aware metrics, which are widely used in applications such as portfolio optimization and insurance. VaR at level $\alpha \in ( 0 , 1 )$ conveys the maximum loss incurred by the portfolio with a confidence of α. In other words, the portfolio incurs a loss greater than VaR at level α with probability 1 − α. In turn, CVaR at level $\alpha \in ( 0 , 1 )$ captures the expected loss incurred by the portfolio, given that the losses exceed VaR at level α. CVaR has an advantage over VaR, in that the former is a coherent<sup>1</sup> risk measure [1].

In this paper, we derive concentration bounds for CVaR estimators, for both light-tailed and heavy-tailed random variables. For light-tailed distributions, our concentration bound uses a clas sical CVaR estimator based on the empirical distribution. For the heavy-tailed case, we employ a truncation-based CVaR estimator, and derive a concentration result under a mild assumption: the pth moment of the distribution is assumed to exist, for some $p > 1$ . Notably, our concentration bounds enjoy an exponential decay in the sample size, for heavy-tailed as well as light-tailed distributions. Our results also subsume or strengthen existing CVaR concentration results, as we discuss in the next subsection. We believe our bounds are order optimal, and the dependence the number of samples as well as the accuracy cannot be improved.

In order to highlight an important application for our CVaR concentration results, we consider a stochastic bandit set-up with a risk-sensitive metric for measuring the quality of an arm. In particular, we consider a K-armed stochastic bandit setting, and study the problem of finding the arm with the lowest CVaR value (at a fixed level $\alpha \in ( 0 , 1 ) )$ in a fixed budget setting. We propose an algorithm for the best CVaR arm identification that is inspired by successive-rejects [2]. Using our CVaR concentration bound, we establish an upper bound on the probability of incorrect arm identification by our algorithm at the end of the given budget.

## 1.1 Related Work

For the case of bounded distributions, a popular CVaR estimate has been shown to exponentially concentrate around the true CVaR – see [4, 18]. In comparison to CVaR, obtaining a concentration result for VaR is easier, and does not require assumptions on the tail of the distribution – see [11], a paper which also derives a one-sided CVaR concentration bound. More recent work [15] considers CVaR concentration for distributions with bounded support on one side. In another recent paper [3], the authors derive an exponentially decaying concentration bound for the case of sub-Gaussian distributions, using a concentration result [9] for the Wasserstein distance between the empirical and the true distributions. However, the above approach leads to poor concentration bounds (with power law decay in the sample size) for other relevant disribution classes, such as light-tailed and bounded-moment distributions.

While bandit learning has a long history, dating back to [16], risk-based criteria have been considered only recently. [12] consider mean-variance optimization in a regret minimization framework. In the best arm identification setting, VaR-based criteria has been studied by [7] and [8]. CVaR-based criteria has been explored in a bandit context by [10], albeit with an assumption of bounded arms distributions.

The rest of this paper is organized as follows: Section 2 presents the preliminaries. Sections 3 and 4 present the key concentration bounds for light and heavy-tailed distributions, respectively. Section 3.3 provides bandit algorithms and their analyses for the problem of the best CVaR arm identification with fixed budget under K-armed stochastic bandits. The proofs are contained in Section 5, and Section 6 concludes the paper.

## 2 Preliminaries

Given a r.v. X with cumulative distribution function (CDF) $F ( \cdot )$ , the VaR $v _ { \alpha } ( X )$ and CVaR $c _ { \alpha } ( X )$ at level $\alpha \in ( 0 , 1 )$ are defined as follows <sup>2</sup>:

$$
v _ {\alpha} (X) = \inf \{\xi : \mathbb {P} [ X \leq \xi ] \geq \alpha \}, \mathrm{and} c _ {\alpha} (X) = v _ {\alpha} (X) + \frac {1}{1 - \alpha} \mathbb {E} [ X - v _ {\alpha} (X) ] ^ {+},\tag{1}
$$

where we have used the notation $[ X ] ^ { + } = \operatorname* { m a x } ( 0 , X )$ . Typical values of α chosen in practice are 0.95 and 0.99. We make the following assumption for the purpose of CVaR estimation as well as for the concentration bounds derived later.

(C1) The r.v. X is continuous with strictly increasing CDF.

Under $( \mathbf { C } 1 ) , v _ { \alpha } ( X )$ is a solution to $\mathbb { P } \left[ X \leq \xi \right] = \alpha , { \mathrm { i . e . , } } v _ { \alpha } ( X ) = F ^ { - 1 } ( \alpha )$ . Further, if X has a positive density at $v _ { \alpha } ( X )$ ), then $c _ { \alpha } ( X ) = \mathbb { E } \left[ X | X \geq v _ { \alpha } ( X ) \right]$ (cf. [14]).

## 3 CVaR estimation: Light-tailed case

In this section, we define empirical CVaR, provide a concentration result for CVaR estimation assuming that the underlying distribution is light-tailed, and subsequently present a multi-armed bandit application.

## 3.1 VaR and CVaR estimation

Let $\{ X _ { i } \} _ { i = 1 } ^ { n }$ be n i.i.d. samples drawn from the distribution of X. Let $\{ X _ { [ i ] } \} _ { i = 1 } ^ { n }$ be the order statistics of $\{ X _ { i } \} _ { i = 1 } ^ { n } , \mathrm { i . e . , } X _ { [ 1 ] } \geq X _ { [ 2 ] } \cdot \cdot \cdot \geq X _ { [ n ] }$ . Let $\hat { F } _ { n } ( \cdot )$ be the empirical distribution function calculated using $\{ X _ { i } \} _ { i = 1 } ^ { n }$ , defined as $\begin{array} { r } { \hat { F } _ { n } ( x ) = \frac { 1 } { n } \sum _ { i = 1 } ^ { n } \mathbb { I } \left\{ X _ { i } \leq x \right\} } \end{array}$ , ∀x ∈ R. Notice that CVaR is a Pconditional expectation, where the conditioning event requires VaR. Thus, CVaR estimation requires VaR to be estimated as well. Let $\hat { v } _ { n , \alpha }$ and $\hat { c } _ { n , \alpha }$ denote the estimates of VaR and CVaR at level α using the n samples above. These quantities are defined as follows [13]:

$$
\hat {v} _ {n, \alpha} = X _ {[ \lfloor n (1 - \alpha) \rfloor ]}, \text {and} \hat {c} _ {n, \alpha} = \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} X _ {i} \mathbb {I} \left\{X _ {i} \geq \hat {v} _ {n, \alpha} \right\}.\tag{2}
$$

## 3.2 Concentration bounds

In the case of distributions with bounded support, a concentration result for CVaR exists in the literature [18]. For the case of unbounded distributions, deriving a CVaR concentration result becomes considerably easier when the form of distributions are known, i.e., when the closed-form expressions of VaR and CVaR can be derived. To illustrate, consider the case of a Gaussian r.v. X with mean µ and variance $\sigma ^ { 2 }$ . Let $\begin{array} { r } { Q \left( \xi \right) = \frac { 1 } { \sqrt { 2 \pi } } \int _ { \xi } ^ { \infty } \exp \left( - x ^ { 2 } / 2 \right) } \end{array}$ dx. Notice that $Q ( - x ) = 1 - Q ( x )$ and also that $\begin{array} { r } { F _ { X } \left( \xi \right) = Q \left( \frac { \mu - \xi } { \sigma } \right) } \end{array}$ . Hence, $v _ { \alpha } ( X )$ is the solution to $\begin{array} { r } { Q \left( { \frac { \mu - \xi } { \sigma } } \right) = \alpha } \end{array}$ , which implies that

$$
v _ {\alpha} (X) = \mu - \sigma Q ^ {- 1} (\alpha).\tag{3}
$$

The CVaR $c _ { \alpha } ( X )$ ) for Gaussian X can be shown, using Acerbi’s formula [6, pp. 329], to be equal to $\textstyle \mu \left( { \frac { \alpha } { 1 - \alpha } } \right) + \sigma c _ { \alpha } ( Z )$ , where $Z$ is the standard Gaussian random variable i.e., $Z \sim { \mathcal { N } } ( 0 , 1 )$

It is clear from the above argument that estimates of $\mathbf { \nabla } \mu$ and σ are sufficient to estimate $c _ { \alpha } ( X )$ for the Gaussian case. Sample mean $\hat { \mu } _ { n }$ and sample variance $\hat { \sigma } _ { n } ^ { 2 }$ (computed using n samples from the distribution of X) would serve this purpose and we obtain $\begin{array} { r } { \hat { c } _ { n } = \hat { \mu } \left( \frac { \alpha } { 1 - \alpha } \right) + \hat { \sigma } c _ { \alpha } ( Z ) } \end{array}$ as a proxy for $c _ { \alpha } ( X )$ ). Given standard concentration bounds for these quantities through Hoeffding and Bernstein’s inequalities, it is straightforward to establish that $\hat { c } _ { n , \alpha }$ concentrates exponentially around $c _ { \alpha } ( X )$ Similarly, for the case of exponential random variables, we can exploit the memoryless property to derive an explicit expression for CVaR, in terms of the mean $\mu$ and the level $\alpha$

We therefore focus on distributions that do not have closed-form expressions for VaR and CVaR. In such a setting, the CVaR has to be estimated directly from the available samples. However, for establishing concentration bounds for the CVaR, which involves conditioning on a tail event, it is common to make some assumptions on the tail distribution. In [3], an exponentially decaying CVaR concentration result is derived for the class of sub-Gaussian random variables, using a Wasserstein distance approach. However, the same approach provides unsatisfactory results (with power-law decay) for light-tailed as well as heavy-tailed distributions with bounded higher moments.

We now define the class of light-tailed distributions , while heavy-tailed distributions are handled in the next section.

Definition 3.1. A r.v. X is said to be light-tailed ifthere exists a $c _ { 0 } > 0$ such that $\mathbb { E } [ \exp ( \lambda X ) ] < \infty$ for all $| \lambda | < c _ { 0 }$

The following lemma provides equivalent characterizations of light-tailed distributions – see [17, Theorem 2.2].

## Lemma 3.2. The following statements are equivalent:

1. X is light-tailed.

2. There exist constants $\eta _ { 1 } , \eta _ { 2 } > 0$ such that $\mathbb { P } \left[ | X | \geq t \right] \leq \eta _ { 1 } \exp ( - \eta _ { 2 } t ) , \quad \forall t > 0$

3. There exist non-negative parameters σ and b such that

$$
\mathbb {E} \left[ \exp (\lambda X) \right] \leq \exp \left(\frac {\lambda^ {2} \sigma^ {2}}{2}\right), f o r a n y | \lambda | <   \frac {1}{b}.\tag{4}
$$

The following result presents a concentration bound for the case of light-tailed distributions:

Theorem 3.3 (CVaR concentration: Light-tailed case). Let $\{ X _ { i } \} _ { i = 1 } ^ { n }$ be a sequence of i.i.d. r.v.s. Assume (C1). Let $\hat { c } _ { n , \alpha }$ be the CVaR estimate given in (2) formed using the above set of samples. Suppose that $X _ { i } , ~ i = 1 , \ldots , n$ are light-tailed with parameters $\sigma , b ,$ and VaR $v _ { \alpha }$ . Then, for any $\epsilon > 0 ,$ we have

$$
\mathbb {P} \left[ | \hat {c} _ {n, \alpha} - c _ {\alpha} | > \epsilon \right] \leq \left\{ \begin{array}{c} 6 \exp \left[ - \frac {c n \epsilon^ {2} (1 - \alpha) ^ {2}}{2 (\sigma^ {2} + v _ {\alpha} ^ {2})} \right],   0 \leq \epsilon \leq \frac {\sigma^ {2} + v _ {\alpha} ^ {2}}{b (1 - \alpha)}, \\ 2 \exp \left[ - \frac {n \epsilon (1 - \alpha)}{4 b} \right] + 6 \exp \left[ - c n \epsilon^ {2} (1 - \alpha) ^ {2} \right],   \epsilon > \frac {\sigma^ {2} + v _ {\alpha} ^ {2}}{b (1 - \alpha)}, \end{array} \right.
$$

where c is a distribution dependent constant.

A few remarks concerning the result above are in order.

Remark 3.4. The bound in the theorem above is significantly better than the two-sided bound obtained in [3]for the light-tailed case. In particular, the bound in the theorem above has an exponen tial tail decay irrespective of whether ǫ is large or small, while the bound in [3] has an exponential decay for small $\epsilon ,$ and a power law for large ǫ. For a light-tailed r.v., one expects a tail behavior similar to that ofGaussian with constant variancefor small $\epsilon ,$ and an exponential decayfor large ǫ, and our bound is consistent with this expected behavior.

Remark 3.5. In comparison to the one-sided bound for light-tailed r.v.s, obtained in [11], our bound exhibits much better dependence w.r.t. the number of samples n as well as the accuracy ǫ. More importantly, since our bound is two-sided, it opens avenues for a bandit application, while a one-sided bound is insufficient for this purpose.

In the following section, we provide a multi-armed bandit algorithm that incorporates a CVaR objective, and analyze the finite-time performance of this algorithm using the bound derived in Theorem 3.3.

## 3.3 Application: Multi-armed bandits

We consider a K-armed stochastic bandit problem, with arms’ distributions $\mathcal { P } _ { 1 } , \ldots , \mathcal { P } _ { K }$ . We study the problem of finding the arm with the lowest CVaR value (at a fixed level $\alpha \in ( 0 , 1 ) )$ ) in a fixed budget setting. In this setting, a bandit algorithm interacts with the environment over a given budget of n rounds. In each round $t = 1 , \ldots , n ,$ , the algorithm pulls an arm $I _ { t } \in \{ 1 , \ldots , K \}$ and observes a sample cost from the distribution $\mathcal { P } _ { I _ { t } }$ . At the end of the budget n rounds, the bandit algorithm recommends an arm $J _ { n }$ and is judged based on the probability of incorrect identification, i.e., P $[ J _ { n } \neq i ^ { * } ]$ where $i ^ { * }$ denotes the best arm. Earlier works use the expected value to define the best arm, while we use CVaR.

Let $c _ { \alpha } ^ { i }$ and $v _ { \alpha } ^ { i }$ denote the CVaR and VaR of the arm i at level α. Let $c ^ { * } = \mathrm { m i n } _ { i = 1 , \dots , K } c _ { \alpha } ^ { i }$ , and $i ^ { * }$ be the arm that achieves this minimum. The goal is to devise an algorithm for which $\mathbb { P } \left[ J _ { n } \neq i ^ { * } \right]$ is small after n rounds of sampling. Let arm-[i] denotes the $i ^ { t h }$ lowest CVaR valued arm. Let $\Delta _ { i } = c _ { \alpha } ^ { i } - c _ { \alpha } ^ { i ^ { * } }$ denote the gap between the CVaR values of arm-i and the optimal arm.

Algorithm 1 presents the pseudo code of our CVaR-SR algorithm, designed to find the CVaR optimal arm under a fixed budget. The algorithm is a variation of the regular successive rejects (SR) algorithm [2], with the following key difference: regular SR uses sample mean to estimate the expected value of each arm, while CVaR-SR used empirical CVaR, as defined in (2), to estimate CVaR for each arm. The elimination logic, i.e., having K − 1 phases, and removing the worst arm (according to sample estimates of CVaR) at the end of each phase, is borrowed from regular SR.

In the following result, we analyze the performance of CVaR-SR algorithm for light-tailed distributions.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 CVaR-SR algorithm
Initialization: Set $A_1 = \{1, \ldots, K\}$, $\overline{\log}K = \frac{1}{2} + \sum_{i=2}^{K} \frac{1}{i}, n_0 = 0, n_k = \left[\frac{1}{\overline{\log}K} \frac{n-K}{K+1-k}\right], k = 1, \ldots, K-1$.
for $k = 1, 2, \ldots, K-1$ do
    Play each arm in $A_k$ for $(n_k - n_{k-1})$ times.
    Compute the CVaR estimate $\hat{c}_{\alpha,n_k}^i$ for each arm $i \in A_k$ using (2).
    Set $A_{k+1} = A_k \setminus \arg\max_{i \in A_k} \hat{c}_{\alpha,n_k}^i$, i.e., remove the arm with the highest empirical CVaR, with ties broken arbitrarily.
end for
Output: Return the solitary element in $A_K$.
</div>

Theorem 3.6 (Probability of incorrect identification). Consider a K-armed stochastic bandit, where the arms’ distributions satisfy (C1) and are light-tailed. For a given budget $n ,$ the arm, say $J _ { n } , r e -$ turned by the CVaR-SR algorithm satisfies:

$$
\mathbb {P} \left[ J _ {n} \neq i ^ {*} \right] \leq 4 K (K - 1) \exp \left(- \frac {(n - K) (1 - \alpha) G _ {\max}}{H \overline {{\log}} K}\right),
$$

where $G _ { \mathrm { m a x } }$ is a problem dependent constant that does not depend on the underlying CVaR gaps and $n ,$ and

$$
H = \max _ {i \in \{1, 2 \dots , K \}} \frac {i}{\min \{\Delta_ {[ i ]} / 2 , \Delta_ {[ i ]} ^ {2} / 4 \}}.
$$

## 4 CVaR estimation: Heavy-tailed case

As mentioned before, an alternative proof approach using Wasserstein distance [3] provides weak concentration rates for distributions with bounded higher moments - a gap that we address in this work. In particular, we employ a truncation-based estimator for CVaR to handle the case when the underlying distribution satisfies the following assumption:

(C2) $\exists p \in ( 1 , 2 ]$ , u such that $\mathbb { E } [ | X | ^ { p } ] < u < \infty$

## 4.1 CVaR estimation

Recall that $\{ X _ { [ i ] } \} _ { i = } ^ { n }$ denote the order statistics of n i.i.d. samples drawn from the distribution of X. Using the VaR estimate $\hat { v } _ { n , \alpha } .$ , as defined earlier in Section 3.1, we propose a truncation-based estimator $\hat { c } _ { n , \alpha }$ for CVaR at level α, defined as follows:

$$
\hat {c} _ {n, \alpha} = \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} X _ {i} \mathbb {I} \left\{\hat {v} _ {n, \alpha} \leq X _ {i} \leq B _ {i} \right\}, \text {   where   } B _ {i} = \left(\frac {u i}{\log (1 / \delta)}\right) ^ {1 / p}.\tag{5}
$$

In $( 2 ) , B _ { i }$ represents a truncation level of $X _ { i } ,$ , and the choice for $B _ { i }$ given above is under the assumption that $\mathbb { E } [ | X | ^ { p } ] < u < \infty$ for some $p \in ( 1 , 2 ]$ . Such a truncation based estimator has been employed in the context of expected regret minimization with heavy-tailed random variables in [5]. Intuitively, the truncation level serves to discard very large samples values early on, as $B _ { i }$ is set to grow slowly with i.

## 4.2 Concentration bounds

In particular, the following result is more general, as it can handle heavy-tailed distributions that satisfy (C2).

Theorem 4.1 (CVaR concentration: Bounded moment case). Let $\{ X _ { i } \} _ { i = 1 } ^ { n }$ be a sequence of i.i.d. r.v.s satisfying (C1) and (C2). Let $\hat { c } _ { n , \alpha }$ be the CVaR estimate given in (2)formed using the above set of samples. $F i x \epsilon > 0$

(i) For the case when $p \in ( 1 , 2 )$

$$
\mathbb {P} \left[ | \hat {c} _ {n, \alpha} - c _ {\alpha} | > \epsilon \right] \leq 8 \exp \left(- c n (1 - \alpha) ^ {\frac {p}{(p - 1)}} \epsilon^ {\frac {p}{(p - 1)}}\right),
$$

where c is a distribution-dependent constant.

(ii) For the case when the distribution ofX has a bounded second moment, $i . e . , p = 2 ,$

$$
\mathbb {P} \left[ | \hat {c} _ {n, \alpha} - c _ {\alpha} | > \epsilon \right] \leq 8 \exp \left(- c ^ {\prime} n (1 - \alpha) ^ {2} \epsilon^ {2}\right),
$$

where $c ^ { \prime }$ is a distribution-dependent constant.

Remark 4.2. A bandit application for the case of heavy-tailed distributions can be worked out using arguments similar to that in Section 3.3. The main difference is that the SR algorithm in the heavytailed case would involve a truncated estimator, and a slightly different hardness measure that is derived using Theorem 4.1. We omit the details due to space constraints.

## 5 Proofs

## 5.1 Proof of Theorem 3.3

Before providing the main proof, we note that empirical CVaR, as defined in (2), involves empirical VaR, and it is natural to expect that empirical CVaR concentration would require empirical VaR to concentrate as well. VaR concentration bounds have been derived recently in [11], and we recall their result below. This result will be used to establish the bound in Theorem 3.3.

Lemma 5.1 (VaR concentration). Suppose that (C1) holds. For any $\epsilon > 0$ , we have

$$
\mathbb {P} \left[ | \hat {v} _ {n, \alpha} - v _ {\alpha} | \geq \epsilon \right] \leq 2 \exp \left(- 2 n c \epsilon^ {2}\right),
$$

where c is a constant that depends on the value ofthe density f ofthe r.v. X in a neighbourhood of $v _ { \alpha } ( X )$ .

Proof of Theorem 3.3. Notice that

$$
\begin{array}{c} \hat {c} _ {n, \alpha} = \hat {v} _ {n, \alpha} + \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} (X _ {i} - \hat {v} _ {n, \alpha}) \mathbb {I} \left\{\hat {v} _ {n, \alpha} \leq X _ {i} \right\} \\ = v _ {\alpha} + \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} (X _ {i} - v _ {\alpha}) \mathbb {I} \left\{v _ {\alpha} \leq X _ {i} \right\} + e _ {n}, \end{array}\tag{6}
$$

where

$$
e _ {n} = \frac {\hat {v} _ {n , \alpha} - v _ {\alpha}}{1 - \alpha} \left[ \hat {F} _ {n} (\hat {v} _ {n, \alpha}) - \alpha \right] + \frac {1}{n} \sum_ {i = 1} ^ {n} \frac {X _ {i} - v _ {\alpha}}{1 - \alpha} \left[ \mathbb {I} \left\{X _ {i} \geq \hat {v} _ {n, \alpha} \right\} - \mathbb {I} \left\{X _ {i} \geq v _ {\alpha} \right\} \right].
$$

The reader is referred to the initial passage in the proof of Proposition 5 in [11] for a justification of the equality in (16).

Thus,

$$
\begin{array}{r l} & {| e _ {n} | \leq \frac {| v _ {\alpha} - \hat {v} _ {n , \alpha} |}{1 - \alpha} | \alpha - \hat {F} _ {n} (\hat {v} _ {n, \alpha}) | + \frac {| v _ {\alpha} - \hat {v} _ {n , \alpha} |}{1 - \alpha} | \hat {F} _ {n} (v _ {\alpha}) - \hat {F} _ {n} (\hat {v} _ {n, \alpha}) |} \\ & {\quad \leq \frac {| v _ {\alpha} - \hat {v} _ {n , \alpha} |}{1 - \alpha} \Big [ 2 | \hat {F} _ {n} (\hat {v} _ {n, \alpha}) - F (v _ {\alpha}) | + | \hat {F} _ {n} (v _ {\alpha}) - F (v _ {\alpha}) | \Big ].} \end{array}\tag{7}
$$

Using $| \hat { F } _ { n } ( \hat { v } _ { n , \alpha } ) - F ( v _ { \alpha } ) | \leq 1 / n$ , we obtain

$$
\begin{array}{r l} & {\mathbb {P} \left[ e _ {n} > \epsilon \right] \leq \mathbb {P} \left[ \frac {2}{n} \frac {1}{(1 - \alpha)} | \hat {v} _ {n, \alpha} - v _ {\alpha} | > \frac {\epsilon}{2} \right] + \mathbb {P} \left[ \frac {1}{1 - \alpha} | \hat {v} _ {n, \alpha} - v _ {\alpha} | | \hat {F} _ {n} (v _ {\alpha}) - F (v _ {\alpha}) | > \frac {\epsilon}{2} \right]} \\ & {\qquad \leq 2 \exp \left(- n c _ {1} (1 - \alpha) ^ {2} \epsilon^ {2}\right) + 2 \exp \left(- n (1 - \alpha) ^ {2} c _ {2} \epsilon^ {2}\right),} \end{array}
$$

where the final inequality uses the concentration result in Lemma 5.1 to obtain the first term, while the second term can be arrived at as follows: Letting $\begin{array} { r } { \epsilon ^ { \prime } = \frac { ( 1 - \alpha ) \epsilon } { 2 } } \end{array}$

$$
\mathbb {P} \left[ | \hat {v} _ {n, \alpha} - v _ {\alpha} | | \hat {F} _ {n} (v _ {\alpha}) - F (v _ {\alpha}) | > \epsilon^ {\prime} \right] \leq \mathbb {P} \left[ | \hat {v} _ {n, \alpha} - v _ {\alpha} | > \frac {\epsilon^ {\prime}}{2} \right] \leq 2 \exp \left(- \frac {n c ^ {\prime} \epsilon^ {\prime 2}}{4}\right),\tag{8}
$$

where the first inequality follows by using the fact that $| \hat { F } _ { n } ( v _ { \alpha } ) - F ( v _ { \alpha } ) | \le 2$ , since the empirical/true distributions are bounded above by 1. The final inequality above uses the VaR concentration result from Lemma 5.1. Thus,

$$
\mathbb {P} \left[ e _ {n} > \epsilon \right] \leq 4 \exp \left(- n (1 - \alpha) ^ {2} c _ {3} \epsilon^ {2}\right),\tag{9}
$$

for a distribution dependent constant $c _ { 3 }$

Next, using (16), the estimation error $\hat { c } _ { n , \alpha } - c _ { \alpha }$ can be written as

$$
\hat {c} _ {n, \alpha} - c _ {\alpha} = I _ {1} + e _ {n}, \quad \text { where } I _ {1} = \frac {1}{1 - \alpha} \left[ \frac {1}{n} \sum_ {i = 1} ^ {n} (X _ {i} - v _ {\alpha}) ^ {+} - \mathbb {E} \left[ (X - v _ {\alpha}) ^ {+} \right] \right].
$$

For bounding the $I _ { 1 }$ term on the RHS above, we use the fact that $( X - v _ { \alpha } ) ^ { + }$ is a light-tailed r.v. This can be argued as follows: Letting $\mu _ { \alpha } ^ { + } = \mathbb { E } \left[ \left( X - v _ { \alpha } \right) ^ { + } \right]$

$$
\mathbb {P} \left[ \left(X _ {i} - v _ {\alpha}\right) ^ {+} - \mu_ {\alpha} ^ {+} > \epsilon \right] = \mathbb {P} \left[ X > v _ {\alpha} + \mu_ {\alpha} ^ {+} + \epsilon \right] \leq c _ {1} \exp \left(- c _ {2} (v _ {\alpha} + \epsilon)\right) \leq c _ {1} \exp (- c _ {4} \epsilon),
$$

where $c _ { 1 } , c _ { 2 }$ , and $c _ { 4 }$ are distribution-dependent constants. Next, using the fact that X is light-tailed, we have

$$
\mathbb {E} \left[ \exp \left[ \lambda \left((X - v _ {\alpha}) ^ {+} - \mu_ {\alpha} ^ {+}\right) \right] \right] \leq 1 + \frac {\lambda^ {2} \mathbb {E} X ^ {2}}{2} + \frac {\lambda^ {2} v _ {\alpha} ^ {2}}{2} + o (\lambda^ {2}).
$$

In the above, we have used the fact that E $\left\lceil \left( X - v _ { \alpha } \right) ^ { 2 } \mathbb { I } \left\{ X \geq v _ { \alpha } \right\} \right\rceil \leq \mathbb { E } X ^ { 2 } + v _ { \alpha } ^ { 2 }$ . Comparing with the following identity:

$$
\exp \left(\frac {\lambda^ {2} \sigma^ {2}}{2}\right) = 1 + \frac {\lambda^ {2} \sigma^ {2}}{2} + \frac {\lambda^ {2} v _ {\alpha} ^ {2}}{2} + o (\lambda^ {2}),
$$

it is easy to see that $\left( X - v _ { \alpha } \right) ^ { + }$ is a light-tailed r.v. with parameters $( \sigma ^ { 2 } + v _ { \alpha } ^ { 2 } , b )$ , whenever X is light-tailed with parameters $( \sigma ^ { 2 } , b )$ (see (4)).

Using a standard light-tailed concentration result (cf. Theorem 2.2. in [17]), we obtain

$$
\mathbb {P} \left[ | I _ {1} | > \epsilon \right] \leq \left\{ \begin{array}{c} 2 \exp \left(- \frac {n \epsilon^ {2} (1 - \alpha) ^ {2}}{2 (\sigma^ {2} + v _ {\alpha} ^ {2})}\right),   0 \leq \epsilon \leq \frac {\sigma^ {2} + v _ {\alpha} ^ {2}}{b (1 - \alpha)}, \\ 2 \exp \left(- \frac {n \epsilon (1 - \alpha)}{2 b}\right),   \epsilon > \frac {\sigma^ {2} + v _ {\alpha} ^ {2}}{b (1 - \alpha)}, \end{array} \right.\tag{10}
$$

The main claim follows by using

$$
\mathbb {P} \left[ | \hat {c} _ {n, \alpha} - c _ {\alpha} | > \epsilon \right] \leq \mathbb {P} \left[ | I _ {1} | > \frac {\epsilon}{2} \right] + \mathbb {P} \left[ e _ {n} > \frac {\epsilon}{2} \right],
$$

and substituting the bounds obtained in (9) and (10) in the RHS above.

## 5.2 Proof of Theorem 3.6

Proof. We begin the proof by rewriting the CVaR concentration bound present in Theorem 3.3 in a simplified manner as follows:

$$
\mathbb {P} \left[ | \hat {c} _ {n, \alpha} - c _ {\alpha} | > \epsilon \right] \leq 8 \exp \left[ - n (1 - \alpha) \min \{\epsilon , \epsilon^ {2} \} G \right],\tag{11}
$$

where $\begin{array} { r } { G = \operatorname* { m i n } \{ \frac { c ( 1 - \alpha ) } { 2 ( \sigma ^ { 2 } + v _ { \alpha } ^ { 2 } ) } , \frac { 1 } { 4 b } , c ( 1 - \alpha ) \} } \end{array}$

Note that, if the CVaR-SR algorithm has eliminated the optimal arm in phase i then it implies that at least one of the last i worst arms $i . e .$ , one of the arms in $\{ [ K ] , [ K - 1 ] , \cdots , [ K - i + 1 ] \}$ } must not have been eliminated in phase i. Hence, we obtain

$$
\begin{array}{l} \mathbb {P} \left[ J _ {n} \neq i ^ {*} \right] \leq \sum_ {k = 1} ^ {K - 1} \sum_ {i = K + 1 - k} ^ {K} \mathbb {P} \left[ \hat {c} _ {n _ {k}, \alpha} ^ {i ^ {*}} \geq \hat {c} _ {n _ {k}, \alpha} ^ {[ i ]} \right] \\ = \sum_ {k = 1} ^ {K - 1} \sum_ {i = K + 1 - k} ^ {K} \mathbb {P} \left[ \hat {c} _ {n _ {k}, \alpha} ^ {i ^ {*}} - c _ {\alpha} ^ {i ^ {*}} - \hat {c} _ {n _ {k}, \alpha} ^ {[ i ]} + c _ {\alpha} ^ {[ i ]} \geq c _ {\alpha} ^ {[ i ]} - c _ {\alpha} ^ {i ^ {*}} \right] \\ \leq \sum_ {k = 1} ^ {K - 1} \sum_ {i = K + 1 - k} ^ {K} \mathbb {P} \left[ \hat {c} _ {n _ {k}, \alpha} ^ {i ^ {*}} - c _ {\alpha} ^ {i ^ {*}} \geq \frac {\Delta_ {[ i ]}}{2} \right] + \sum_ {k = 1} ^ {K - 1} \sum_ {i = K + 1 - k} ^ {K} \mathbb {P} \left[ c _ {\alpha} ^ {[ i ]} - \hat {c} _ {n _ {k}, \alpha} ^ {[ i ]} \geq \frac {\Delta_ {[ i ]}}{2} \right] \end{array}\tag{12}
$$

We now bound the above terms individually as follows.

$$
\begin{array}{l} \sum_ {k = 1} ^ {K - 1} \sum_ {i = K + 1 - k} ^ {K} \mathbb {P} \left[ c _ {\alpha} ^ {[ i ]} - \hat {c} _ {n _ {k}, \alpha} ^ {[ i ]} \geq \frac {\Delta_ {[ i ]}}{2} \right] \leq \sum_ {k = 1} ^ {K - 1} \sum_ {i = K + 1 - k} ^ {K} \mathbb {P} \left[ | \hat {c} _ {n _ {k}, \alpha} ^ {[ i ]} - c _ {\alpha} ^ {[ i ]} | \geq \frac {\Delta_ {[ i ]}}{2} \right] \\ \stackrel {(a)} {\leq} \sum_ {k = 1} ^ {K - 1} \sum_ {i = K + 1 - k} ^ {K} 8 \exp \left(- n (1 - \alpha) \min \{\frac {\Delta_ {[ i ]}}{2}, \frac {\Delta_ {[ i ]} ^ {2}}{4} \} G _ {[ i ]}\right) \\ \stackrel {} {\leq} \sum_ {k = 1} ^ {K - 1} \sum_ {i = K + 1 - k} ^ {K} 8 \exp \left(- n (1 - \alpha) \min \{\frac {\Delta_ {[ i ]}}{2}, \frac {\Delta_ {[ i ]} ^ {2}}{4} \} G _ {\max}\right), \\ \stackrel {} {\leq} \sum_ {k = 1} ^ {K - 1} 8 k \exp \left(- n (1 - \alpha) \min \{\frac {\Delta_ {[ K + 1 - k ]}}{2}, \frac {\Delta_ {[ K + 1 - k ]} ^ {2}}{4} \} \times G _ {\max}\right), \end{array}\tag{13}
$$

where (a) is due to Theorem 3.3 and(11), and $G _ { \operatorname* { m a x } } = \operatorname* { m a x } _ { i } G _ { i }$ . Further, note that

$$
n \min \{\frac {\Delta_ {[ K + 1 - k ]}}{2}, \frac {\Delta_ {[ K + 1 - k ]} ^ {2}}{4} \} \geq \frac {n - K}{H \overline {{\log}} K},
$$

where H is as defined in the theorem statement. By substituting the above in (13), we obtain

$$
\sum_ {k = 1} ^ {K - 1} \sum_ {i = K + 1 - k} ^ {K} \mathbb {P} \left[ c _ {\alpha} ^ {[ i ]} - \hat {c} _ {n _ {k}, \alpha} ^ {[ i ]} \geq \frac {\Delta_ {[ i ]}}{2} \right] \leq \sum_ {k = 1} ^ {K - 1} 8 k \exp \left(- \frac {(n - K) (1 - \alpha) G _ {\max}}{H \overline {{\log}} K}\right).\tag{14}
$$

Similarly, we can show that

$$
\sum_ {k = 1} ^ {K - 1} \sum_ {i = K + 1 - k} ^ {K} \mathbb {P} \left[ \hat {c} _ {n _ {k}, \alpha} ^ {i ^ {*}} - c _ {\alpha} ^ {i ^ {*}} - \geq \frac {\Delta_ {[ i ]}}{2} \right] \leq \sum_ {k = 1} ^ {K - 1} 8 k \exp \left(- \frac {(n - K) (1 - \alpha) G _ {\max}}{H \overline {{\log}} K}\right).\tag{15}
$$

The main claim follows by substituting (14) and (15) in (12).

## 5.3 Proof of Theorem 4.1

Proof. Notice that

$$
\begin{array}{l} \hat {c} _ {n, \alpha} = \hat {v} _ {n, \alpha} + \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} (X _ {i} - \hat {v} _ {n, \alpha}) \mathbb {I} \left\{\hat {v} _ {n, \alpha} \leq X _ {i} \leq B _ {i} \right\} \\ = v _ {\alpha} + \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} (X _ {i} - v _ {\alpha}) \mathbb {I} \left\{v _ {\alpha} \leq X _ {i} \leq B _ {i} \right\} + e _ {n}, \text {   where   } \end{array}\tag{16}
$$

$$
\begin{array}{l} e _ {n} = (\hat {v} _ {n, \alpha} - v _ {\alpha}) + \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} (X _ {i} - \hat {v} _ {n, \alpha}) [ \mathbb {I} \{\hat {v} _ {n, \alpha} \leq X _ {i} \leq B _ {i} \} - \mathbb {I} \{v _ {\alpha} \leq X _ {i} \leq B _ {i} \} ] \\ = (\hat {v} _ {n, \alpha} - v _ {\alpha}) + \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} (v _ {\alpha} - \hat {v} _ {n, \alpha}) \mathbb {I} \{\hat {v} _ {n, \alpha} \leq X _ {i} \leq B _ {i} \} \\ \quad + \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} (X _ {i} - v _ {\alpha}) [ \mathbb {I} \{\hat {v} _ {n, \alpha} \leq X _ {i} \leq B _ {i} \} - \mathbb {I} \{v _ {\alpha} \leq X _ {i} \leq B _ {i} \} ] \\ = (\hat {v} _ {n, \alpha} - v _ {\alpha}) + \frac {(v _ {\alpha} - \hat {v} _ {n , \alpha})}{(1 - \alpha)} (\hat {F} _ {n} (B _ {i}) - \hat {F} _ {n} (\hat {v} _ {n, \alpha})) \\ \quad + \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} (X _ {i} - v _ {\alpha}) [ \mathbb {I} \{\hat {v} _ {n, \alpha} \leq X _ {i} \leq B _ {i} \} - \mathbb {I} \{v _ {\alpha} \leq X _ { i} \leq B _ {i} \} ] \end{array}
$$

Thus,

$$
\begin{array}{r l} & {| e _ {n} | \leq \frac {| v _ {\alpha} - \hat {v} _ {n , \alpha} |}{1 - \alpha} | \alpha - \hat {F} _ {n} (\hat {v} _ {n, \alpha}) | + \frac {| v _ {\alpha} - \hat {v} _ {n , \alpha} |}{1 - \alpha} | \hat {F} _ {n} (v _ {\alpha}) - \hat {F} _ {n} (\hat {v} _ {n, \alpha}) |} \\ & {\quad \leq \frac {| v _ {\alpha} - \hat {v} _ {n , \alpha} |}{1 - \alpha} \Big [ 2 | \hat {F} _ {n} (\hat {v} _ {n, \alpha}) - F (v _ {\alpha}) | + | \hat {F} _ {n} (v _ {\alpha}) - F (v _ {\alpha}) | \Big ].} \end{array}\tag{17}
$$

Using $| \hat { F } _ { n } ( \hat { v } _ { n , \alpha } ) - F ( v _ { \alpha } ) | \leq 1 / n$ , we obtain

$$
\begin{array}{l} \mathbb {P} \left[ e _ {n} > \epsilon \right] \leq \mathbb {P} \left[ \frac {2}{n} \frac {1}{(1 - \alpha)} | \hat {v} _ {n, \alpha} - v _ {\alpha} | > \frac {\epsilon}{2} \right] + \mathbb {P} \left[ \frac {1}{1 - \alpha} | \hat {v} _ {n, \alpha} - v _ {\alpha} | | \hat {F} _ {n} (v _ {\alpha}) - F (v _ {\alpha}) | > \frac {\epsilon}{2} \right] \\ \quad \leq 2 \exp \left(- n c _ {1} (1 - \alpha) ^ {2} \epsilon^ {2}\right) + 2 \exp \left(- n (1 - \alpha) ^ {2} c _ {2} \epsilon^ {2}\right), \end{array}
$$

where the final inequality uses the concentration result in Lemma 5.1 to obtain the first term, while the second term can be arrived at as in the proof of Theorem 3.3. In particular, letting $\begin{array} { r } { \epsilon ^ { \prime } = \frac { ( 1 - \alpha ) \epsilon } { 2 } } \end{array}$ and using (8), we have

$$
\mathbb {P} \left[ | \hat {v} _ {n, \alpha} - v _ {\alpha} | | \hat {F} _ {n} (v _ {\alpha}) - F (v _ {\alpha}) | > \epsilon^ {\prime} \right] \leq 2 \exp \left(- \frac {n c ^ {\prime} \epsilon^ {\prime 2}}{4}\right),
$$

where the final inequality follows by using DKW inequality for the first term, and VaR concentration result from Lemma 5.1 for the second term, together with the fact that $\hat { F } _ { n } ( v _ { \alpha } ) \leq 1$ . Thus,

$$
\mathbb {P} \left[ e _ {n} > \epsilon \right] \leq 4 \exp \left(- n (1 - \alpha) ^ {2} c _ {3} \epsilon^ {2}\right), \text {   or,   equivalently,   } e _ {n} \leq \sqrt {\frac {\log (4 / \delta)}{c _ {3} n}} \text {   w.p.   } (1 - \delta).\tag{18}
$$

Hence, we have

$$
c _ {\alpha} - \hat {c} _ {n, \alpha} = \frac {1}{1 - \alpha} \left[ \mathbb {E} \left[ (X - v _ {\alpha}) \mathbb {I} \{v _ {\alpha} \leq X \} \right] - \frac {1}{n} \sum_ {i = 1} ^ {n} (X _ {i} - v _ {\alpha}) \mathbb {I} \{v _ {\alpha} \leq X _ {i} \leq B _ {i} \} \right] + e _ {n}
$$

$$
= I _ {1} - I _ {2} + e _ {n},
$$

where $\begin{array} { r } { I _ { 1 } = \frac { 1 } { 1 - \alpha } \mathbb { E } \left[ X \mathbb { I } \left\{ v _ { \alpha } \leq X \right\} \right] - \frac { 1 } { n ( 1 - \alpha ) } \sum _ { i = 1 } ^ { n } X _ { i } \mathbb { I } \left\{ v _ { \alpha } \leq X _ { i } \leq B _ { i } \right\} } \end{array}$ , and $\begin{array} { r } { I _ { 2 } = \frac { 1 } { 1 - \alpha } \mathbb { E } \left[ v _ { \alpha } \mathbb { I } \left\{ v _ { \alpha } \leq X \right\} \right] - \frac { 1 } { n ( 1 - \alpha ) } \sum _ { i = 1 } ^ { n } v _ { \alpha } \mathbb { I } \left\{ v _ { \alpha } \leq X _ { i } \leq B _ { i } \right\} } \end{array}$ . We bound the $I _ { 1 }$ term, using a technique from [5], as follows:

$$
\begin{array}{l} \frac {1}{1 - \alpha} \mathbb {E} [ X \mathbb {I} \{v _ {\alpha} \leq X \} ] - \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} X _ {i} \mathbb {I} \{v _ {\alpha} \leq X _ {i} \leq B _ {i} \} \\ = \frac {1}{n (1 - \alpha)} \left(\sum_ {i = 1} ^ {n} \mathbb {E} [ X \mathbb {I} \{X > B _ {i} \} ] + \sum_ {i = 1} ^ {n} \mathbb {E} [ X \mathbb {I} \{v _ {\alpha} \leq X \leq B _ {i} \} ] - X _ {i} \mathbb {I} \{v _ {\alpha} \leq X _ {i} \leq B _ {i} \}\right) \end{array}\tag{19}
$$

$$
\leq \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} \frac {u}{B _ {i} ^ {p - 1}} + \frac {1}{(1 - \alpha)} \sqrt {\frac {2 B _ {n} ^ {2 - p} u \log (1 / \delta)}{n}} + \frac {1}{(1 - \alpha)} \frac {2 B _ {n} \log (1 / \delta)}{3 n}, \text { holds   w.p. } (1 - \delta),
$$

where we have used the fact that $\mathbb { E } ( X ^ { p } ) \geq B ^ { p - 1 } \mathbb { E } \left[ X \mathbb { I } \left\{ X > B \right\} \right]$ to handle the first term in (19), and Bernstein’s inequality to bound the second term there.

Along similar lines, the term $I _ { 2 }$ is bounded as follows:

$$
\begin{array}{l} \frac {1}{1 - \alpha} \mathbb {E} [ v _ {\alpha} \mathbb {I} \{v _ {\alpha} \leq X \} ] - \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} v _ {\alpha} \mathbb {I} \{v _ {\alpha} \leq X _ {i} \leq B _ {i} \} \\ = \frac {v _ {\alpha}}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} \mathbb {E} [ \mathbb {I} \{X > B _ {i} \} ] + \frac {v _ {\alpha}}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} \left(\mathbb {E} [ \mathbb {I} \{v _ {\alpha} \leq X \leq B _ {i} \} ] - \mathbb {I} \{v _ {\alpha} \leq X _ {i} \leq B _ {i} \}\right) \end{array}\tag{20}
$$

$$
\leq \frac {1}{n (1 - \alpha)} \sum_ {i = 1} ^ {n} \frac {u}{B _ {i} ^ {p - 1}} + \frac {v _ {\alpha}}{(1 - \alpha)} \sqrt {\frac {\log (1 / \delta)}{2 n}}, \text { holds   w.p. } (1 - \delta),
$$

where we have used Hoeffding’s inequality, and $B _ { i } ^ { p } \geq B _ { i } ^ { p - 1 }$ for bounding the second $\mathrm { t e r m } ^ { 3 }$ in (20), while the first term is bounded using an argument similar to that used in bounding $I _ { 1 }$ term above.

Using $\begin{array} { r } { B _ { i } = \left( \frac { u i } { \log ( 1 / \delta ) } \right) ^ { 1 / p } } \end{array}$ , we have, w.p. (1 − δ),

$$
I _ {1} \leq \frac {4 u ^ {1 / p}}{(1 - \alpha)} \left(\frac {\log (1 / \delta)}{n}\right) ^ {1 - 1 / p}, \text {   and   } I _ {2} \leq \frac {u ^ {1 / p}}{(1 - \alpha)} \left(\frac {\log (1 / \delta)}{n}\right) ^ {1 - 1 / p} + \sqrt {\frac {\log (1 / \delta)}{c _ {4} n}}.
$$

Combining the bound above, with that in (18), we obtain

$$
\begin{array}{l} c _ {\alpha} - \hat {c} _ {n, \alpha} \leq \frac {5 u ^ {1 / p}}{(1 - \alpha)} \left(\frac {\log (1 / \delta)}{n}\right) ^ {1 - 1 / p} + \sqrt {\frac {\log (4 / \delta)}{c _ {5} n}} \\ \quad \leq \frac {5 u ^ {1 / p}}{(1 - \alpha)} \max \left(\log (4 / \delta) ^ {1 - 1 / p}, \log (4 / \delta) ^ {1 / 2}\right) \frac {1}{n ^ {1 - 1 / p}}, \text {for} 1 <   p \leq 2. \end{array}\tag{21}
$$

If the second moment is bounded, $\mathrm { i } . \mathrm { e } . , p = 2$ , we have

$$
\mathbb {P} \left[ c _ {\alpha} - \hat {c} _ {n, \alpha} > \epsilon \right] \leq 4 \exp \left(- c n (1 - \alpha) ^ {2} \epsilon^ {2}\right),
$$

where c is a distribution-dependent constant. Along similar lines, a concentration bound for the other tail can be obtained. Thus, we have

$$
\mathbb {P} \left[ | \hat {c} _ {n, \alpha} - c _ {\alpha} | > \epsilon \right] \leq 8 \exp \left(- c n (1 - \alpha) ^ {2} \epsilon^ {2}\right).
$$

Similarly, from (21), for the case when $p \in ( 1 , 2 )$ ), we obtain

$$
\mathbb {P} \left[ | \hat {c} _ {n, \alpha} - c _ {\alpha} | > \epsilon \right] \leq 8 \exp \left(- c ^ {\prime} n (1 - \alpha) ^ {\frac {p}{(p - 1)}} \epsilon^ {\frac {p}{(p - 1)}}\right),
$$

where $c ^ { \prime }$ is a distribution-dependent constant.

## 6 Concluding Remarks

We derived concentration bounds for CVaR estimation, separately considering light-tailed and heavytailed distributions. For light-tailed distributions, our concentration bound uses a classical CVaR estimator based on the empirical distribution. For the heavy-tailed case, we employ a truncation based CVaR estimator, and derive a concentration result under a mild bounded-moment assumption. Our concentration bound enjoys exponential decay in the sample size even for heavy-tailed random vari ables. We highlighted the applicability of the CVaR concentration result by considering a risk-aware best bandit arm selection problem. We proposed an adaptation of the successive rejects algorithm to the setting where the goal is to find an arm with the lowest CVaR. Using the CVaR concentration bound, we established error bounds for the proposed algorithm.

## References

[1] Philippe Artzner, Freddy Delbaen, Jean-Marc Eber, and David Heath, Coherent measures of risk, Mathematical finance 9 (1999), no. 3, 203–228.

[2] J. Y. Audibert, S. Bubeck, and R. Munos, Best arm identification in multi-armed bandits, Conference on Learning Theory, 2010, pp. 41–53.

[3] Sanjay P. Bhat and Prashanth L. A, Improved Concentration Bounds for Conditional Valueat-Risk and Cumulative Prospect Theory using Wasserstein distance, arXiv e-prints (2019), arXiv:1902.10709.

[4] David B Brown, Large deviations boundsfor estimating conditional value-at-risk, Operations Research Letters 35 (2007), no. 6, 722–730.

[5] S´ebastien Bubeck, Nicolo Cesa-Bianchi, and G´abor Lugosi, Bandits with heavy tail, IEEE Transactions on Information Theory 59 (2013), no. 11, 7711–7717.

[6] Rupak Chatterjee, Practical methods of financial engineering and risk management: tools for modernfinancial professionals, Apress, 2014.

[7] Yahel David and Nahum Shimkin, Pure exploration for max-quantile bandits, Joint European Conference on Machine Learning and Knowledge Discovery in Databases, Springer, 2016, pp. 556–571.

[8] Yahel David, Bal´azs Sz¨or´enyi, Mohammad Ghavamzadeh, Shie Mannor, and Nahum Shimkin, Pac bandits with risk constraints, International Symposium on Artificial Intelligence and Mathematics, 2018.

[9] Nicolas Fournier and Arnaud Guillin, On the rate of convergence in wasserstein distance of the empirical measure, Probability Theory and Related Fields 162 (2015), no. 3-4, 707–738.

[10] Nicolas Galichet, Michele Sebag, and Olivier Teytaud, Exploration vs exploitation vs safety: Risk-aware multi-armed bandits, Asian Conference on Machine Learning, 2013, pp. 245–260.

[11] R. K. Kolla, L. A. Prashanth, S. P. Bhat, and K. Jagannathan, Concentration boundsfor empir ical conditional value-at-risk: The unbounded case, ArXiv e-prints (2018).

[12] A. Sani, A. Lazaric, and R. Munos, Risk-aversion in multi-armed bandits, Advances in Neural Information Processing Systems, 2012, pp. 3275–3283.

[13] Robert J Serfling, Approximation theorems of mathematical statistics, vol. 162, John Wiley & Sons, 2009.

[14] Lihua Sun and L Jeff Hong, Asymptotic representations for importance-sampling estimators of value-at-risk and conditional value-at-risk, Operations Research Letters 38 (2010), no. 4, 246–251.

[15] Philip Thomas and Erik Learned-Miller, Concentration inequalities for conditional value at risk, International Conference on Machine Learning, 2019, pp. 6225–6233.

[16] William R Thompson, On the likelihood that one unknown probability exceeds another in view ofthe evidence oftwo samples, Biometrika 25 (1933), no. 3/4, 285–294.

[17] Martin J Wainwright, High-dimensional statistics: A non-asymptotic viewpoint, vol. 48, Cambridge University Press, 2019.

[18] Ying Wang and Fuqing Gao, Deviation inequalitiesfor an estimator of the conditional valueat-risk, Operations Research Letters 38 (2010), no. 3, 236–239.