---
title: "2008-Bardou-VaR-CVaR-Stochastic-Approximation-arXiv"
date: 2026-09-04
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/ranking/2008-Bardou-VaR-CVaR-Stochastic-Approximation-arXiv.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Computing VaR and CVaR using Stochastic Approximation and Adaptive Unconstrained Importance Sampling

O. Bardou<sup>1</sup> , N. Frikha<sup>2</sup> , G. Pag\`es<sup>3</sup>

May 26, 2018

## Abstract

Value-at-Risk (VaR) and Conditional-Value-at-Risk (CVaR) are two risk measures which are widely used in the practice of risk management. This paper deals with the problem of estimating both VaR and CVaR using stochastic approximation (with decreasing steps): we propose a first Robbins-Monro (RM) procedure based on Rockafellar-Uryasev’s identity for the CVaR. Convergence rate of this algorithm to its target satisfies a Gaussian Central Limit Theorem. As a second step, in order to speed up the initial procedure, we propose a recursive and adaptive importance sampling (IS) procedure which induces a significant variance reduction of both VaR and CVaR procedures. This idea, which has been investigated by many authors, follows a new approach introduced in [27]. Finally, to speed up the initialization phase of the IS algorithm, we replace the original confidence level of the VaR by a slowly moving risk level. We prove that the weak convergence rate of the resulting procedure is ruled by a Central Limit Theorem with minimal variance and its eficiency is illustrated on several typical energy portfolios.

This work appeared in Monte Carlo Methods and Applications 2009.

Keywords: VaR, CVaR, Stochastic Approximation, Robbins-Monro algorithm, Importance Sampling, Girsanov.

## 1 Introduction

Following financial institutions, energy companies are developing a risk management framework to face the new price and volatility risks associated to the growth of energy markets. Valueat-Risk (VaR) and Conditional Value-at-Risk (CVaR) are certainly the best known and the most common risk measures used in this context, especially for the evaluation of extreme losses potentially faced by traders. Naturally related to rare events, the estimation of these risk measures is a numerical challenge. The Monte Carlo method, which is often the only available numerical device in such a general framework, must always be associated to eficient reduction variances techniques to encompass its slow convergence rate. In some specific cases, Gaussian approximations can lead to semi-closed form estimators. But, if these approximations can be of some interest when considering the yield of a portfolio, they turn out to be useless when estimating e.g. the VaR on the EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization) of a huge portfolio as it is often the case in the energy sector.

In this article, we introduce an alternative estimation method to estmate both VaR and CVaR, relying on the use of recursive stochastic algorithms. By definition, the VaR at level $\alpha \in ( 0 , 1 )$ $\left( \operatorname { V a R } _ { \alpha } \right)$ of a given portfolio is the lowest amount not exceeded by the loss with probability α (usually $\alpha \geq 9 5 \% )$ The Conditional Value-at-Risk at level α $\left( \mathrm { C V a R } _ { \alpha } \right)$ is the conditional expectation of the portfolio losses beyond the $\operatorname { V a R } _ { \alpha }$ level. Compared to VaR, CVaR is known to have better properties. It is a coherent risk measure in the sense of Artzner, Delbaen, Eber and Heath, see [2].

The most commonly used method to compute VaR is the inversion of the simulated empirical loss distribution function using Monte Carlo or historical simulation tools. The historical simulation method usually assumes that the asset returns in the future are independent and identically distributed, having the same distribution as they had in the past. Over a time interval [t, T], the loss is defined by $L : = V ( S _ { t } , t ) - V ( S _ { t } + \Delta S , T )$ , where $S _ { t }$ denotes the market price vector observed at time t, $\Delta S = S _ { T } - S _ { t }$ the variation of S over the time interval $[ t , T ]$ -which can be calculated using historical data- and $V ( S _ { t } , t )$ the portfolio value at time t. The distribution of this loss L can be computed with the corresponding VaR at a given probability level by the inversion of the empirical function method. However, when the market price dynamics follow a general difusion process solution of a stochastic diferential equation (SDE), the assumption of asset returns independence is no longer available.

To circumvent this problem, Monte Carlo simulation tools are generally used. Another widely used method relies on a linear (Normal approximation) or quadratic expansion (Delta-Gamma approximation) and assume a joint normal (or log-normal) distribution for $\Delta S$ . The Normal approximation method gives L a normal distribution, thus the computation of the $\operatorname { V a R } _ { \alpha }$ is straightforward. However, when there is a non-linear dependence between the portfolio value and the prices of the underlying assets (think of a portfolio with options) such approximation is no longer acceptable. The Delta-Gamma approximation tries to capture some non linearity by adding a quadratic term in the loss expansion. Then, it is possible to find the distribution of the resulting approximation in order to obtain an approximation of the VaR. For more details about these methods, we refer to [7], [8], [15], [16] and [34]. Such approximations are no longer acceptable when considering portfolios with long maturity $( T - t = 1$ year up to 10 years) or when the loss is a functional of a general path-dependent SDE.

In the context of hedging or optimizing a portfolio of financial instruments to reduce the CVaR, it is shown in [33] that it is possible to compute both VaR and CVaR (actually calculate VaR and optimize CVaR) by solving a convex optimization problem with a linear programming approach. It consists in generating loss scenarios and then in introducing constraints in the linear programming problem. Although they address a diferent problem, this method can be used to compute both VaR and CVaR. The advantage of such a method is that it is possible to estimate both VaR and CVaR simultaneously without assuming that the market prices have a specified distribution (e.g. normal, log-normal, ...). The main drawback is that the dimension (number of constraints) of the linear programming problem to be solved is equal to the number of simulated scenarios. In our approach, we are no limited by the number of generated sample paths used in the procedure.

The idea to compute both VaR and CVaR with one procedure comes from the fact that they are strongly linked as they appear as the solutions and the value of the same convex optimisation problem (see Proposition 2.1) as pointed out [33]. Moreover both the objective function of the minimization problem and its gradient read as an expectation. This leads us to define consistent and asymptotically normal estimators of both quantities as the limit of a global Robbins-Monro (RM) procedure. Consequently, we are no longer constrained by the number of samples paths used in the estimation.

A significant advantage of this recursive approach, especially in regard to the inversion of the empirical function method is that we only estimate the quantities of interest and not the whole inverse of the distribution function. Furthermore, we do not need to make approximations of the loss or of the convex optimization problem to be solved. Moreover, the implementation of the algorithm is straightforward. However to make it really eficient we need to modify it owing to the fact that VaR and CVaR computation is closely related to the simulation of rare events. That is why as a necessary improvement, we introduce a (recursive and adaptive) variance reduction method based on an importance sampling (IS) paradigm.

Let us be a bit more specific. Basically in this kind of problem we are interested in events that are observed with a very low probability (usually less that 5%, 1% or even 0.1%) so that we obtain few significant replications to update our estimates. Actually, interesting losses are those that exceed the VaR, i.e. the ones that are “in the tail” of the loss distribution. Thus in order to compute more accurate estimates of both quantities of interest, it is necessary to generate more samples in the tail of L, the area of interest. A general tool used in this situation is IS.

The basic principle of IS is to modify the distribution of L by an equivalent change of measure to obtain more “interesting” samples that will lead to better estimates of the VaR and CVaR. The main issue of IS is to find a right change of measure (among a parameterized family) that will induce a significant variance reduction. In [16] and [17], a change of measure based on a large deviation upper bound is proposed to estimate the loss probability $\mathbb { P } ( L > x )$ for several values of x. Then, it is possible to estimate the VaR by interpolating between the estimated loss probabilities.

Although this approach provides an asymptotically optimal IS distribution, it is strongly based on the fact that the Delta-Gamma approximation holds exactly and relies on the assumption that, conditionally to the past data, market moves are normally distributed. Moreover, as shown in [18], importance sampling estimators based on a large deviations change of measure can have variance that increases with the rarity of the event, and even infinite variance. In [12], the $\operatorname { V a R } _ { \alpha }$ is estimated by using a quantile estimator based on the inversion of the empirical weighted function and combined with Robbins-Monro (RM) algorithm with repeated projection devised to produce the optimal measure change for IS purpose. This kind of IS algorithm is known to converge toward the optimal importance sampling parameter only after a (long) stabilization phase and provided that the compact sets have been appropriately specified. By contrast, our parameters are optimized by an adaptive unconstrained (i.e. without projections) RM algorithm naturally combined with our VaR-CVaR procedure.

One major issue that arises when combining the VaR-CVaR algorithm with the recursive IS procedure is to ensure that the IS parameters do move appropriately toward the critical risk area. They may remain stuck at the very beginning of the IS procedure. To circumvent this problem, we make the confidence level slowly increase from a low level (say 50%) to α by introducing a deterministic sequence $( \alpha _ { n } ) _ { n \geq 0 }$ of confidence level that converges toward α. This kind of incrementa threshold increase has been proposed previously [22] in a diferent framework (use of cross entropy in rare event simulation). It speeds up the initialization phase of the IS algorithm and consequently improves the variance reduction. Thus, we can truly experiment asymptotic convergence results in practice.

The paper is organized as follows. In the next section, we present some theoretical results about VaR and CVaR. We introduce the VaR-CVaR stochastic algorithm in its first and naive version and study its convergence rate. We also introduce some background about IS using stochastic approximation algorithm. Section 3 is devoted to the design of an optimal procedure using an adaptive variance reduction procedure. We present how it modifies the asymptotic variance of our first CLT. In Section 4 we provide some extensions to the exponential change of measure and to deal with the case of infinite dimensional setting. Section 5 is dedicated to numerical examples. We propose several portfolios of options on several assets in order to challenge the algorithm and display variance reduction factors obtained using the IS procedure. To prevent the freezing of the algorithm during the first iterations of the IS procedure, we also consider a deterministic moving risk level $\alpha _ { n }$ which replace α to speed up the initialization phase and improve the reduction of variance. We prove theoretically that modifying in this way the algorithm doesn’t change the previous CLT and fasten the convergence.

Notations: $\bullet \left| . \right|$ will denote the canonical Euclidean norm on $\mathbb { R } ^ { d }$ and $\langle . , . \rangle$ will denote the canonical inner product.

$\cdot { \xrightarrow { \mathcal { L } } }$ will denote the convergence in distribution and ${ \xrightarrow { a . s . } }$ will denote the almost sure convergence. $x _ { + } : = \operatorname* { m a x } ( 0 , x )$ will denote the positive part function.

## 2 VaR, CVaR using stochastic approximation and some background on recursive IS

It is rather natural to consider that the loss of the portfolio over the considered time horizon can be written as a function of a structural finite dimensional random vector, i.e. $L = \varphi ( X )$ , where X is $\mathrm { ~ a ~ } \mathbb { R } ^ { d } .$ -valued random vector defined on the probability space $( \Omega , A , \mathbb { P } )$ and $\varphi : \mathbb { R } ^ { d }  \mathbb { R }$ is a Borel function. $\varphi$ is the function representing the composition of the portfolio which remains fixed and X is a structural random vector used to model the market prices over the time interval; therefore we do not need to specify the dynamics of the market prices and only rely on the fact that it is possible to sample from the distribution of $X .$ . For instance, in a Black-Scholes framework, X is a Gaussian vector and $\varphi$ can be a portfolio of vanilla options. In more sophisticated models or portfolio, X can be a vector of Brownian increments related to the Euler scheme of a difusion. The VaR at level $\alpha \in ( 0 , 1 )$ is the lowest α-quantile of the distribution $\varphi ( X ) ~ i . e .$

$$
\operatorname{VaR} _ {\alpha} (\varphi (X)) := \inf \left\{\xi \mid \mathbb {P} (\varphi (X) \leq \xi) \geq \alpha \right\}.
$$

Since lim ${ \mathfrak { l } } _ { \xi  + \infty } \mathbb { P } ( \varphi ( X ) \leq \xi ) \ = \ 1$ , we have $\{ \xi ~ | ~ \mathbb { P } \left( \varphi ( X ) \leq \xi \right) \geq \alpha \} ~ \neq ~ \varnothing$ . Moreover, we have $\begin{array} { r l } { \operatorname* { l i m } _ { \xi \to - \infty } \mathbb { P } \left( \varphi ( X ) \le \xi \right) = } & { { } 0 , } \end{array}$ , which implies that $\{ \xi ~ | ~ \mathbb { P } \left( \varphi ( X ) \leq \xi \right) \geq \alpha \}$ is bounded from below so that the VaR always exists. We assume that the distribution function of $\varphi ( X )$ is continuous (i.e. without atoms) so that the VaR is the lowest solution of the equation:

$$
\mathbb {P} \left(\varphi (X) \leq \xi\right) = \alpha .
$$

Three values of α are commonly considered: 0.95, 0.99, 0.995 so that it is usually close to 1 and the tail of interest has probability 1 α. If the distribution function is $\mathrm { ( s t r i c t l y ) }$ increasing, the solution of the above equation is unique, otherwise, there may be more than one solution. In fact, in what follows, we will consider that any solution of the previous equation is the VaR. Another risk measure generally used to provide information about the tail of the distribution of $\varphi ( X )$ is the Conditional Value-at-Risk (CVaR) (at level α). As soon as $\varphi ( X ) \in L ^ { 1 } ( \mathbb { P } )$ , it is defined by:

$$
\operatorname{CVaR} _ {\alpha} (\varphi (X)) := \mathbb {E} [ \varphi (X) | \varphi (X) \geq \operatorname{VaR} _ {\alpha} (\varphi (X)) ].
$$

The CVaR of $\varphi ( X )$ is simply the conditional expectation of $\varphi ( X )$ given that it lies inside the critical risk area. To capture more information on the conditional distribution of $\varphi ( X )$ , it seems natural to consider more general risk measures like for example the conditional variance. In a more general framework we can be interested in estimating the Ψ-Conditional Value at Risk (Ψ-CVaR) (at level α) where $\Psi : \mathbb { R }  \mathbb { R }$ is a continuous function. As soon as $\Psi ( \varphi ( X ) ) \in L ^ { 1 } ( \mathbb { P } )$ , it is defined by:

$$
\Psi \text {-CVaR} _ {\alpha} (\varphi (X)) := \mathbb {E} \left[ \Psi (\varphi (X)) | \varphi (X) \geq \operatorname{VaR} _ {\alpha} (\varphi (X)) \right].\tag{1}
$$

When $\Psi \equiv I d \operatorname { a n d } \varphi ( X ) \in L ^ { 1 } ( \mathbb { P } ) , ( 1 )$ is the regular CVaR of $\varphi ( X )$ . When $\Psi \equiv x \mapsto x ^ { 2 }$ , equation (1) is but the conditional quadratic norm of $\varphi ( X )$

## 2.1 Representation of VaR and Ψ-CVaR as expectations

The idea to devise a stochastic approximation procedure to compute VaR and CVaR, and more generally the Ψ-CVaR, comes from the fact that these two quantities are solutions of a convex optimization problem whose value function can be represented as an expectation as pointed out by Rockafellar and Uryasev in [32].

Proposition 2.1. Let V and $V _ { \Psi }$ be the functions defined by:

$$
V (\xi) = \mathbb {E} [ v (\xi , X) ] \quad a n d \quad V _ {\Psi} (\xi) = \mathbb {E} [ w (\xi , X) ]\tag{2}
$$

where

$$
v (\xi , x) := \xi + \frac {1}{1 - \alpha} (\varphi (X) - \xi) _ {+} a n d w (\xi , x) := \xi + \frac {1}{1 - \alpha} (\Psi (\varphi (x)) - \xi) \mathbf {1} _ {\{\varphi (x) \geq \xi \}}.\tag{3}
$$

Suppose that the distribution function of $\varphi ( X )$ is continuous and that $\varphi ( X ) \in L ^ { 1 } ( \mathbb { P } )$ . Then, the function $V$ is convex, diferentiable and the $\operatorname { V a R } _ { \alpha } ( \varphi ( X ) )$ is any point of the set:

$$
\arg \min V = \left\{\xi \in \mathbb {R} \mid V ^ {\prime} (\xi) = 0 \right\} = \left\{\xi \mid \mathbb {P} (\varphi (X) \leq \xi) = \alpha \right\},
$$

where $V ^ { \prime }$ is the derivative of V defined for every $\xi \in \mathbb { R }$ by

$$
V ^ {\prime} (\xi) = \mathbb {E} \left[ \frac {\partial v}{\partial \xi} (\xi , X) \right].\tag{4}
$$

Furthermore,

$$
\operatorname{CVaR} _ {\alpha} (\varphi (X)) = \min _ {\xi \in \mathbb {R}} V (\xi)
$$

and, $i f \ \Psi$ is continuous and that $\Psi \left( \varphi ( X ) \right) \in \ L ^ { 1 } ( \mathbb { P } )$ , for every $\xi _ { \alpha } ^ { \ast } ~ \in ~ \mathrm { a r g }$ min $V ~ ( i . e . , ~ \xi _ { \alpha } ^ { * }$ is a $\operatorname { V a R } _ { \alpha } ( \varphi ( X ) ) )$

$$
\Psi \text {-CVaR} _ {\alpha} (\varphi (X)) = V _ {\Psi} (\xi_ {\alpha} ^ {*}).
$$

Proof. Since the functions $\xi \mapsto ( \varphi ( x ) - \xi ) _ { + } , x \in \mathbb { R } ^ { d }$ , are convex, the function V is convex. $\begin{array} { r } { \mathbb { P } ( d w ) – a . s . , \frac { \partial v } { \partial \xi } ( \xi , X ( w ) ) } \end{array}$ exists at every $\xi \in \mathbb { R }$ and

$$
\mathbb {P} (d w) \text {-a.s.,} \left| \frac {\partial v}{\partial \xi} (\xi , X (w)) \right| \leq 1 \vee \frac {\alpha}{1 - \alpha}.
$$

Thanks to Lebesgue Dominated Convergence Theorem, one can interchange diferentiation and expectation, so that V is diferentiable with derivative $V ^ { \prime } ( \xi ) = 1 - \frac { 1 } { 1 - \alpha } \mathbb { P } ( \varphi ( X ) > \xi )$ and reaches its absolute minimum at any $\xi _ { \alpha } ^ { \ast }$ satisfying $\mathbb { P } ( \varphi ( X ) > \xi _ { \alpha } ^ { * } ) = 1 - \alpha \ i . e . \ \mathbb { P } ( \varphi ( X ) \leq \xi _ { \alpha } ^ { * } ) = \alpha$ Moreover, it is clear that:

$$
\begin{array}{r c l} V (\xi_ {\alpha} ^ {*}) & = & \xi_ {\alpha} ^ {*} + \frac {\mathbb {E} [ (\varphi (X) - \xi_ {\alpha} ^ {*}) _ {+} ]}{\mathbb {P} (\varphi (X) > \xi_ {\alpha} ^ {*})} \\ & = & \frac {\xi_ {\alpha} ^ {*} \mathbb {E} [ \mathbf {1} _ {\varphi (X) > \xi_ {\alpha} ^ {*}} ] + \mathbb {E} [ (\varphi (X) - \xi_ {\alpha} ^ {*}) _ {+} ]}{\mathbb {P} (\varphi (X) > \xi_ {\alpha} ^ {*})} \\ & = & \mathbb {E} \left[ \varphi (X) | \varphi (X) > \xi_ {\alpha} ^ {*} \right] \end{array}
$$

and, in the same way, $V _ { \Psi } ( \xi _ { \alpha } ^ { * } ) = \Psi \mathrm { - C V a R } _ { \alpha } ( \varphi ( X ) )$ . This completes the proof.

Remark: Actually, one could consider a more general framework by including any risk measure defined by an integral representation with respect to $X$ :

$$
\mathbb {E} [ \Lambda (\xi_ {\alpha} ^ {*}, X) ]
$$

where Λ is a (computable) Borel function.

## 2.2 Stochastic gradient and its adaptive companion procedure: a first naive approach

The above representation (4) naturally yields a stochastic gradient procedure derived from the convex Lyapunov function V which will (hopefully) converge toward $\xi _ { \alpha } ^ { * } : = \operatorname { V a R } _ { \alpha } ( \varphi ( X ) )$ . Then, a recursive companion procedure based on (2) can be easily devised having $C _ { \alpha } ^ { * } : = \Psi \mathrm { - C V a R } _ { \alpha } ( \varphi ( X ) )$ as target. There is no reason to believe that this first version can do better than the empirical quantile estimate. But, it is a necessary phase in order to understand how our recursive IS algorithm (to be devised further on) can be combined with this first procedure.

First we set

$$
H _ {1} (\xi , x) := \frac {\partial v}{\partial \xi} (\xi , x) = 1 - \frac {1}{1 - \alpha} \mathbf {1} _ {\{\varphi (x) \geq \xi \}},\tag{5}
$$

so that,

$$
V ^ {\prime} (\xi) = \mathbb {E} \left[ H _ {1} (\xi , X) \right].
$$

Since we are looking for $\xi$ for which E $[ H _ { 1 } ( \xi , X ) ] = 0 \quad$ we implement a stochastic gradient descent derived from the Lyapunov function V to approximate $\xi _ { \alpha } ^ { * } : = V a R _ { \alpha } ( \varphi ( X ) )$ , i.e., we use the RM algorithm:

$$
\xi_ {n} = \xi_ {n - 1} - \gamma_ {n} H _ {1} (\xi_ {n - 1}, X _ {n}), n \geq 1, \xi_ {0} \in L ^ {1} (\mathbb {P}),\tag{6}
$$

where $( X _ { n } ) _ { n \geq 1 }$ is an i.i.d. sequence of random variables with the same distribution as $X$ , independent of $\xi _ { 0 }$ , with $\mathbb { E } [ | \xi _ { 0 } | ] < + \infty$ and $( \gamma _ { n } ) _ { n \geq 1 }$ is a deterministic step sequence (decreasing to 0) satisfying:

$$
\sum_ {n \geq 1} \gamma_ {n} = + \infty \quad \text { and } \quad \sum_ {n \geq 1} \gamma_ {n} ^ {2} <   + \infty .\tag{A1}
$$

In order to derive the a.s. convergence of (6) we introduce the following additional assumption on the distributions of $\varphi ( X )$ and $\Psi ( \varphi ( X ) )$ ). Let $a > 0$ 2

$$
\varphi (X) \text {   has   a   continuous   distribution   function   and   } \Psi (\varphi (X)) \in L ^ {2 a} (\mathbb {P}).\tag{A2) \( _{a} \}
$$

Actually, Equation (6) can be seen either as a regular RM procedure with mean function $V ^ { \prime }$ since it is increasing (see e.g. [10] p.50 and $\mathrm { p . 6 6 } )$ or as a recursive gradient descent procedure derived from the Lyapunov function V . Both settings yield the a.s. convergence toward its target $\xi _ { \alpha } ^ { \ast }$ . To establish the a.s. convergence of $( \xi _ { n } ) _ { n \geq 1 }$ (and of our diferent RM algorithms), we will rely on the following theorem. For a proof of this slight extension of Robbins-Monro Theorem and of the a.s. convergence of $( \xi _ { n } ) _ { n \geq 1 }$ (under assumptions (A1) and $( A 2 ) _ { 1 } )$ , we refer to [13].

Theorem 2.2. (Robbins-Monro Theorem (variant)). Let $H : \mathbb { R } ^ { q } \times \mathbb { R } ^ { d }  \mathbb { R } ^ { d }$ be a Borel function and X be an $\mathbb { R } ^ { d }$ -valued random vector such that $\mathbb { E } [ | H ( z , X ) | ] < \infty \ f o r$ every $z \in \mathbb { R } ^ { d }$ . Then set

$$
\forall z \in \mathbb {R} ^ {d}, h (z) = \mathbb {E} [ H (z, X) ].
$$

Suppose that the function h is continuous and that $\mathcal { T } ^ { * } : = \{ h = 0 \}$ satisfies

$$
\forall z \in \mathbb {R} ^ {d} \setminus \mathcal {T} ^ {*}, \forall z ^ {*} \in \mathcal {T} ^ {*}, \langle z - z ^ {*}, h (z) \rangle > 0.\tag{7}
$$

Let $( \gamma _ { n } ) _ { n \geq 1 }$ be a deterministic step sequence satisfying condition (A1). Suppose that

$$
\forall z \in \mathbb {R} ^ {d}, \mathbb {E} [ | H (z, X) | ^ {2} ] \leq C (1 + | z | ^ {2})\tag{8}
$$

(which implies that $| h ( z ) | \leq C ^ { \prime } ( 1 + | z | ) )$

Let $( X _ { n } ) _ { n \geq 1 }$ be an i.i.d. sequence of random vectors having the distribution of X, let $z _ { \mathrm { 0 } }$ be a random vector independent of $( X _ { n } ) _ { n \geq 1 }$ satisfying $\mathbb { E } [ | z _ { 0 } | ] < \infty$ , all defined on the same probability space $( \Omega , A , \mathbb { P } )$ . Let $\mathcal { F } _ { n } : = \sigma ( z _ { 0 } , X _ { 1 } , . . . , X _ { n } )$ and let $( r _ { n } ) _ { n \geq 1 }$ be an ${ \mathcal { F } } _ { n }$ -measurable remainder sequence satisfying

$$
\sum_ {n} \gamma_ {n} | r _ {n} | ^ {2} <   \infty .\tag{9}
$$

Then, the recursive procedure defined for $n \geq 1$ by

$$
Z _ {n} = Z _ {n - 1} - \gamma_ {n} H (Z _ {n - 1}, X _ {n}) + \gamma_ {n} r _ {n},
$$

satisfies:

$\exists ~ z _ { \infty }$ such that $Z _ { n } \xrightarrow { { a . s . } } z _ { \infty }$ and $z _ { \infty } \in \mathcal { T } ^ { * }$ a.s.

The convergence also holds in $L ^ { p } ( \mathbb { P } ) , p \in ( 0 , 2 )$ , where $L ^ { p } ( \mathbb { P } )$ denotes the set of all random vectors defined on $( \Omega , A , \mathbb { P } )$ such that $\mathbb { E } [ | X | ^ { p } ] ^ { \frac { 1 } { p } } < \infty$

Remark: It is in fact a slight variant (see e.g. [13]) of the regular RM Theorem since $Z _ { n }$ converges to a random vector having its value in the set $\{ h = 0 \}$ even if $\{ h = 0 \}$ is not reduced to a singleton or a finite set. The remainder sequence in the above theorem plays a crucial role when we will (slightly) modify the first IS procedure to improve its eficiency.

The second step concerns procedure for the numerical computation of the $\Psi \mathrm { - C V a R } _ { \alpha }$ . A naive idea is to compute the function $V _ { \Psi }$ at the point $\xi _ { \alpha } ^ { * }$ :

$$
\Psi \text {-CVaR} _ {\alpha} = V _ {\Psi} (\xi_ {\alpha} ^ {*}) = \mathbb {E} [ w (\xi_ {\alpha} ^ {*}, X) ]
$$

using a regular Monte Carlo simulation,

$$
\frac {1}{n} \sum_ {k = 0} ^ {n - 1} w (\xi_ {\alpha} ^ {*}, X _ {k + 1}).\tag{10}
$$

However, we first need to get from (6) a good approximate of $\xi _ { \alpha } ^ { * }$ and subsequently to use another sample of the distribution X. A natural idea is to devise an adaptive companion procedure of the above quantile search algorithm by replacing $\xi _ { \alpha } ^ { * }$ in (10) by its approximation at step k, namely

$$
C _ {n} = \frac {1}{n} \sum_ {k = 0} ^ {n - 1} w (\xi_ {k}, X _ {k + 1}), n \geq 1, C _ {0} = 0.\tag{11}
$$

Hence, $( C _ { n } ) _ { n \geq 0 }$ is the sequence of empirical means of the non i.i.d. sequence $( w ( \xi _ { k } , X _ { k + 1 } ) ) _ { k \geq 1 }$ 2 which can be written recursively:

$$
C _ {n} = C _ {n - 1} - \frac {1}{n} H _ {2} \left(\xi_ {n - 1}, C _ {n - 1}, X _ {n}\right), n \geq 1,\tag{12}
$$

where $H _ { 2 } \left( \xi , c , x \right) : = c - w ( \xi , x )$

At this stage, we are facing two procedures $( \xi _ { n } , C _ { n } )$ with diferent steps. This may appear not very consistent or at least natural. A second modification to the original Monte Carlo procedure (12)

consists in considering a general step $\beta _ { n }$ satisfying condition (A1) instead of $\textstyle { \frac { 1 } { n } }$ (with in mind the possibility to set $\beta _ { n } = \gamma _ { n }$ eventually). This leads to:

$$
C _ {n} = C _ {n - 1} - \beta_ {n} H _ {2} \left(\xi_ {n - 1}, C _ {n - 1}, X _ {n}\right), n \geq 1.\tag{13}
$$

In order to prove the a.s. convergence of $( C _ { n } ) _ { n \geq 1 }$ toward $C _ { \alpha } ^ { * }$ , we set for convenience $\beta _ { 0 } : =$ $\mathrm { s u p } _ { n \geq 1 } \beta _ { n } + 1$ . Then, one defines recursively a sequence $( \Delta _ { n } ) _ { n \geq 1 }$ by

$$
\Delta_ {n + 1} = \Delta_ {n} \frac {\beta_ {n + 1}}{\beta_ {n}} \frac {\beta_ {0}}{\beta_ {0} - \beta_ {n + 1}}, n \geq 0, \Delta_ {0} = 1.
$$

Elementary computations show by induction that

$$
\beta_ {n} = \beta_ {0} \frac {\Delta_ {n}}{S _ {n}}, n \geq 0, \text { with } S _ {n} = \sum_ {k = 0} ^ {n} \Delta_ {k}.\tag{14}
$$

Furthermore, it follows from (14) that for every $n \geq 1$

$$
\log (S _ {n}) - \log (S _ {n - 1}) = - \log \left(1 - \frac {\Delta_ {n}}{S _ {n}}\right) \geq \frac {\Delta_ {n}}{S _ {n}} = \frac {\beta_ {n}}{\beta_ {0}}.
$$

Consequently,

$$
\log (S _ {n}) \geq \frac {1}{\beta_ {0}} \sum_ {k = 1} ^ {n} \beta_ {k}
$$

which implies that lim<sub>n</sub> $S _ { n } = + \infty$

Now using (13) and (14), one gets for every $n \geq 1$

$$
S _ {n} C _ {n} = S _ {n - 1} C _ {n - 1} + \Delta_ {n} \left(\Delta N _ {n + 1} + V _ {\Psi} (\xi_ {n})\right)
$$

where, $\Delta N _ { n } : = w ( \xi _ { n - 1 } , X _ { n } ) - V _ { \Psi } ( \xi _ { n - 1 } ) , n \geq 1$ , define a martingale increments sequence with respect to the natural filtration of the algorithm ${ \mathcal { F } } _ { n } : = \sigma ( \xi _ { 0 } , X _ { 1 } , \cdot \cdot \cdot , X _ { n } ) , n \geq 0$ . Consequently,

$$
C _ {n} = \frac {1}{S _ {n}} \left(\sum_ {k = 0} ^ {n - 1} \Delta_ {k + 1} \Delta N _ {k + 1} + \sum_ {k = 0} ^ {n - 1} \Delta_ {k + 1} V _ {\Psi} (\xi_ {k})\right).
$$

The second term in the right hand side of the above equality converges to $V _ { \Psi } ( \xi _ { \alpha } ^ { * } ) = \Psi \mathrm { - C V a R } _ { \alpha } ( \varphi ( X ) )$ owing to the continuity of $V _ { \Psi }$ at $\xi _ { \alpha } ^ { * }$ and Cesaro’s Lemma.

The convergence to 0 of the first term will follow from the a.s. convergence of the series

$$
N _ {n} ^ {\beta} := \sum_ {k = 1} ^ {n} \beta_ {k} \Delta N _ {k}, n \geq 1
$$

by the Kronecker Lemma since $\beta _ { n } = \beta _ { 0 } \frac { \Delta _ { n } } { S _ { n } }$ . The sequence $( N _ { n } ^ { \beta } ) _ { n \ge 1 }$ is an ${ \mathcal { F } } _ { n }$ -martingale since the $\Delta N _ { k } \mathrm { \prime }$ s are martingale increments and

$$
\mathbb {E} \left[ (\Delta N _ {n}) ^ {2} | \mathcal {F} _ {n - 1} \right] \leq \frac {1}{(1 - \alpha) ^ {2}} \mathbb {E} \left[ (\Psi (\varphi (X)) - \xi) ^ {2} \right] _ {| \xi = \xi_ {n - 1}}.
$$

Assumption $( A 2 ) _ { 1 }$ and the a.s. convergence of $\xi _ { k }$ toward $\xi _ { \alpha } ^ { * }$ imply that

$$
\sup _ {n \geq 1} \mathbb {E} [ (\Delta N _ {n}) ^ {2} | \mathcal {F} _ {n - 1} ] <   \infty \quad a. s.
$$

Consequently, assumption (A1) implies

$$
\langle N ^ {\beta} \rangle_ {\infty} = \sum_ {n \geq 1} \beta_ {n} ^ {2} \mathbb {E} [ (\Delta N _ {n}) ^ {2} | \mathcal {F} _ {n - 1} ] <   \infty
$$

which in term yields the a.s. convergence of $( N _ { n } ^ { \beta } ) _ { n \geq 1 }$ , so that $C _ { n } \xrightarrow { a . s . } \Psi \mathrm { - } C V a R _ { \alpha } ( \varphi ( X ) )$ The resulting algorithm reads as for $n \geq 1 \mathrm { { } }$ :

$$
\left\{ \begin{array}{l} \xi_ {n} = \xi_ {n - 1} - \gamma_ {n} H _ {1} \left(\xi_ {n - 1}, X _ {n}\right), \xi_ {0} \in L ^ {1} (\mathbb {P}), \\ C _ {n} = C _ {n - 1} - \beta_ {n} H _ {2} \left(\xi_ {n - 1}, C _ {n - 1}, X _ {n}\right), C _ {0} = 0, \end{array} \right.\tag{15}
$$

and converges under (A1) and (A2)<sub>1</sub>.

The question of the joint weak convergence rate of $( \xi _ { n } , C _ { n } )$ is not trivial owing to the coupling of the two procedures. The case of two diferent step scales refers to the general framework of twotime-scale stochastic approximation algorithms. Several results have been established by Borkar in [5], Konda and Tsitsiklis in [21] but the more relevant in our case are those of Mokkadem and Pelletier in [30]. The weak convergence rate of $( \xi _ { n } ) _ { n \geq 1 }$ is ruled by the CLT for “regular” (singletime scale) stochastic approximation algorithms (we refer to Kushner and Clark in [23], M´etivier and Priouret in [4], Duflo in [10] among others). In order to achieve the best asymptotic rate of convergence, one ought to set $\begin{array} { r } { \gamma _ { n } ~ = ~ \frac { \gamma _ { 0 } } { n } } \end{array}$ where the choice of $\gamma _ { 0 }$ depends on the value of the density $f _ { \varphi ( X ) }$ of $\varphi ( X )$ at $\xi _ { \alpha } ^ { \ast }$ , which is unknown. To circumvent the dificulties induced by the specification of $\gamma _ { 0 } .$ , which are classical in this field, we are led to modify again our algorithm by introducing the averaging principle independently introduced by Ruppert [35] and Polyak [19] and then widely investigated by several authors. It works both with two-time or single-time scale steps and leads to asymptotically eficient procedures, $i . e . ,$ satisfying a CLT at the optimal rate $\sqrt { n }$ and minimal variance (see also [30]). See also a variant based on a gliding window developed in [26]. Our numerical examples indicate that the averaged one-time-scale procedure provides less variance during the first iterations than the averaged procedure of the two-time-scale algorithm. Finally, we set $\gamma _ { n } \equiv \beta _ { n }$ in (15) so that, the VaR-CVaR algorithm can be written in a more synthetic way by setting $Z _ { n } = ( \xi _ { n } , C _ { n } )$ and for $n \geq 1$

$$
Z _ {n} = Z _ {n - 1} - \gamma_ {n} H (Z _ {n - 1}, X _ {n}), Z _ {0} = (\xi_ {0}, C _ {0}), \xi_ {0} \in L ^ {1} (\mathbb {P}),\tag{16}
$$

where $H ( z , x ) : = ( H _ { 1 } ( \xi , x ) , H _ { 2 } ( \xi , C , x ) )$ . Throughout the rest of this section, we assume that the distribution $\varphi ( X )$ has a positive probability density $f _ { \varphi ( X ) }$ on its support. As a consequence the $V a R _ { \alpha } ( \varphi ( X ) )$ ) is unique so that the procedure algorithm $Z _ { n }$ converges a.s. to its single target $( \operatorname { V a R } _ { \alpha } ( \varphi ( X ) ) , \Psi \mathrm { - C V a R } _ { \alpha } ( \varphi ( X ) ) )$ ). Thus, the Cesaro mean of the procedure

$$
\bar {Z} _ {n} := \frac {Z _ {0} + \cdots + Z _ {n - 1}}{n}, n \geq 1,
$$

where $Z _ { n }$ is defined by (16), converges a.s. to the same target. The Ruppert and Polyak’s Averaging Principle says that an appropriate choice of the step yields for free the smallest possible asymptotic variance. We recall below this result (following a version established in [10], see [10] (p.169) for a proof).

Theorem 2.3. (Ruppert and Polyak’s Averaging Principle) Suppose that the $\mathbb { R } ^ { d }$ -sequence $( Z _ { n } ) _ { n \geq 0 }$ is defined recursively by

$$
Z _ {n} = Z _ {n - 1} - \gamma_ {n} \left(h (Z _ {n - 1}) + \epsilon_ {n} + r _ {n}\right)
$$

where h is a Borel function. Let $\mathbb { F } : = ( \mathscr { F } _ { n } ) _ { n \geq 0 }$ be the natural filtration of the algorithm, i.e. such that the sequence $( \epsilon _ { n } ) _ { n \geq 1 }$ and $( r _ { n } ) _ { n \geq 1 }$ is $\mathbb { F } .$ adapted. Suppose that h is ${ \mathcal { C } } ^ { 1 }$ in the neighborhood of a zero $z ^ { * }$ of h and that $M = D h ( z ^ { * } )$ is a uniformly repulsive matrix (all its eigenvalues have positive real parts) and that $( \epsilon _ { n } ) _ { n \geq 1 }$ satisfies

$$
(i) \mathbb {E} [ \epsilon_ {n + 1} | \mathcal {F} _ {n} ] \mathbf {1} _ {\{| | Z _ {n} - z ^ {*} | | \leq C \}} = 0,
$$

$\exists ~ C > 0$ , such that a.s.

$$
(i i) \exists b > 2, \sup _ {n} \mathbb {E} [ | | \epsilon_ {n + 1} | | ^ {b} | \mathcal {F} _ {n} ] \mathbf {1} _ {\{| | Z _ {n} - z ^ {*} | | \leq C \}} <   + \infty ,
$$

$$
\mathbb {E} \left[ (\gamma_ {n - 1}) ^ {- 1} | r _ {n} | ^ {2} \mathbf {1} _ {\{| | Z _ {n} - z ^ {*} | | \leq C \}} \right] \to 0,\tag{17}
$$

$$
(i v) \exists \Gamma \in \mathcal {S} ^ {+} (d, \mathbb {R}) \text {   such   that   } \mathbb {E} \left[ \epsilon_ {n + 1} \epsilon_ {n + 1} ^ {T} | \mathcal {F} _ {n} \right] \xrightarrow {a . s .} \Gamma .
$$

Set $\begin{array} { r } { \gamma _ { n } = \frac { \gamma _ { 1 } } { n ^ { a } } } \end{array}$ with $\textstyle { \frac { 1 } { 2 } } < a < 1$ , and

$$
\bar {Z} _ {n + 1} := \frac {Z _ {0} + \ldots + Z _ {n}}{n + 1} = \bar {Z} _ {n} - \frac {1}{n + 1} (\bar {Z} _ {n} - Z _ {n}), n \geq 0.
$$

Then, on the set of convergence $\{ Z _ { n } \to z ^ { * } \}$

$$
\sqrt {n} \left(\bar {Z} _ {n} - z ^ {*}\right) \xrightarrow {\mathcal {L}} \mathcal {N} \left(0, M ^ {- 1} \Gamma (M ^ {- 1}) ^ {T}\right) \quad a s n \to + \infty ,
$$

where $( M ^ { - 1 } ) ^ { T }$ denotes the transpose of the matrix $M ^ { - 1 }$

To apply this theorem to our framework we are led to compute the Cesaro means of both components, namely for $n \geq 1$

$$
\left\{ \begin{array}{l} \overline {{\xi}} _ {n} := \frac {1}{n} \sum_ {k = 1} ^ {n} \xi_ {k} = \overline {{\xi}} _ {n - 1} - \frac {1}{n} (\overline {{\xi}} _ {n - 1} - \xi_ {n}), \\ \overline {{C}} _ {n} := \frac {1}{n} \sum_ {k = 1} ^ {n} C _ {k} = \overline {{C}} _ {n - 1} - \frac {1}{n} (\overline {{C}} _ {n - 1} - C _ {n}), \end{array} \right.\tag{18}
$$

where $( \xi _ { k } , C _ { k } ) , k \ge 0$ is defined by (16). In the following theorem, we provide the convergence rate of the couple ${ \bar { Z } } _ { n } : = ( { \overline { { \xi } } } _ { n } , { \overline { { C } } } _ { n } )$

Theorem 2.4. (Convergence rate of the VaR-CVaR procedure). Suppose $( A 2 ) _ { \ell }$ <sub>a</sub> holds for some $a > 1$ , the density function $f _ { \varphi ( X ) } \ o f \varphi ( X )$ is continuous, strictly positive at $\xi _ { \alpha } ^ { * } . \ I f$ the step sequence is $\begin{array} { r } { \gamma _ { n } = \frac { \gamma _ { 1 } } { n ^ { a } } } \end{array}$ with $\textstyle { \frac { 1 } { 2 } } < a < 1$ and $\gamma _ { 1 } > 0$ then

$$
\sqrt {n} \left(\bar {Z} _ {n} - z ^ {*}\right) \xrightarrow {\mathcal {L}} \mathcal {N} (0, \Sigma) \quad a s n \to + \infty
$$

where the asymptotic covariance matrix Σ is given by

$$
\left( \begin{array}{c c} \frac {\alpha (1 - \alpha)}{f _ {\varphi (X)} ^ {2} (\xi_ {\alpha} ^ {*})} & \frac {\alpha}{(1 - \alpha) f _ {\varphi (X)} (\xi_ {\alpha} ^ {*})} \mathbb {E} \left[ (\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*})   \mathbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}} \right] \\ \frac {\alpha}{(1 - \alpha) f _ {\varphi (X)} (\xi_ {\alpha} ^ {*})} \mathbb {E} \left[ (\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*})   \mathbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}} \right] & \frac {1}{(1 - \alpha) ^ {2}} \mathrm{Var} \left((\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*})   \mathbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}}\right) \end{array} \right).\tag{19}
$$

Proof. First, the procedure (16) can be written as for $n \geq 1$

$$
Z _ {n} = Z _ {n - 1} - \gamma_ {n} \left(h (Z _ {n - 1}) + \epsilon_ {n}\right), Z _ {0} = (\xi_ {0}, C _ {0}), \xi_ {0} \in L ^ {1} (\mathbb {P}),\tag{20}
$$

where $\begin{array} { r } { h ( z ) : = \mathbb { E } [ H ( z , X ) ] = \left( 1 - \frac { 1 } { 1 - \alpha } \mathbb { P } \left( \varphi ( X ) \geq \xi \right) , C - \mathbb { E } [ w ( \xi , X ) ] \right) } \end{array}$ and $\epsilon _ { n } ~ : = ~ ( \Delta M _ { n } , \Delta N _ { n } )$ 2 $n \geq 1$ , denotes the ${ \mathcal { F } } _ { n }$ -adapted martingale increment sequence with

$$
\Delta M _ {n} := \frac {1}{1 - \alpha} \left(\mathbb {P} (\varphi (X) \geq \xi) _ {| \xi = \xi_ {n - 1}} - \mathbf {1} _ {\{\varphi (X _ {n}) \geq \xi_ {n - 1} \}}\right).
$$

Owing to Assumption $( A 2 ) _ { a }$ and Lebesgue’s diferentiation Theorem, one can interchange expectation and derivation, so that the function h is diferentiable at $z ^ { * } = ( \xi _ { \alpha } ^ { * } , C _ { \alpha } ^ { * } )$ and

$$
h ^ {\prime} (z ^ {*}) = M := \left( \begin{array}{c c} \frac {1}{1 - \alpha} f _ {\varphi (X)} (\xi_ {\alpha} ^ {*}) & 0 \\ \mathbb {E} \left[ \left(\frac {\partial}{\partial \xi} w (\xi , X)\right) _ {| \xi = \xi_ {\alpha} ^ {*}} \right] & 1 \end{array} \right).\tag{21}
$$

Now, E $\begin{array} { r } { \bigg [ \bigg ( \frac { \partial } { \partial \xi } w ( \xi , X ) \bigg ) _ { \lvert \xi = \xi _ { \alpha } ^ { * } \rvert } = \bigg ( 1 - \frac { 1 } { 1 - \alpha } \mathbb { P } ( \varphi ( X ) \geq \xi _ { \alpha } ^ { * } ) \bigg ) = 0 , } \end{array}$ , so that, $M = \left( \begin{array} { c c } { { { \frac { 1 } { 1 - \alpha } } f _ { \varphi ( X ) } ( \xi _ { \alpha } ^ { * } ) } } & { { 0 } } \\ { { 0 } } & { { 1 } } \end{array} \right)$ is diagonal. Since $f _ { \varphi ( X ) }$ is continuous at $\xi _ { \alpha } ^ { * }$ , h is ${ \mathcal { C } } ^ { 1 }$ in the neighborhood of $z ^ { * }$ To apply Theorem 2.3, we need to check assumptions (i)-(iv) of (17). Let $A > 0$ . First note that

$$
\mathbb {E} \left[ \Delta M _ {n + 1} ^ {2 a} | \mathcal {F} _ {n} \right] \mathbf {1} _ {\{| Z _ {n} - z ^ {*} | \leq A \}} \leq \left(\frac {1}{1 - \alpha}\right) ^ {2 a} 2 ^ {2 a} <   + \infty .
$$

Thanks to Assumption $( A 2 ) _ { a }$ , there exists $C _ { \alpha , \Psi } > 0$ such that

$$
\mathbb {E} \left[ \Delta N _ {n + 1} ^ {2 a} | \mathcal {F} _ {n} \right] \mathbf {1} _ {\{| | Z _ {n} - z ^ {*} | | \leq A \}} \leq C _ {\alpha , \Psi} \left(1 + \xi_ {n} ^ {2 a}\right) \mathbf {1} _ {\{| | Z _ {n} - z ^ {*} | | \leq A \}} <   + \infty .
$$

Consequently, (ii) of (17) holds true with $b = 2 a > 2$ since

$$
\sup _ {n \geq 0} \mathbb {E} \left[ | \epsilon_ {n + 1} | ^ {2 a} | \mathcal {F} _ {n} \right] \mathbf {1} _ {\{| Z _ {n} - z ^ {*} | \leq A \}} <   + \infty .
$$

It remains to check (iv) for some positive definite symmetric matrix Γ. The dominated convergence theorem implies that

$$
\begin{array}{r c l}\mathbb {E} \left[ \left(\epsilon_ {n + 1} \epsilon_ {n + 1} ^ {T}\right) _ {1, 1} | \mathcal {F} _ {n} \right]&=&\left(\frac {1}{1 - \alpha}\right) ^ {2} \left(\mathbb {E} \left[ \left. \mathbf {1} _ {\{\varphi (X) \geq \xi \}} \right] _ {| \xi = \xi_ {n}} - \mathbb {E} \left[ \left. \mathbf {1} _ {\{\varphi (X) \geq \xi \}} \right] _ {| \xi = \xi_ {n}} ^ {2}\right) \right. \right.\\&\xrightarrow {a . s .}&\frac {\alpha}{1 - \alpha},\\\mathbb {E} \left[ \left(\epsilon_ {n + 1} \epsilon_ {n + 1} ^ {T}\right) _ {1, 2} | \mathcal {F} _ {n} \right]&=&\mathbb {E} \left[ \left(\epsilon_ {n + 1} \epsilon_ {n + 1} ^ {T}\right) _ {2, 1} | \mathcal {F} _ {n} \right]\\&=&\left(\frac {1}{1 - \alpha}\right) ^ {2} \mathbb {E} \left[ (\Psi (\varphi (X)) - \xi)   \left. \mathbf {1} _ {\{\varphi (X) \geq \xi \}} \right] _ {| \xi = \xi_ {n}} \right.\\&&\times \left( \right.1 - \mathbb {E} \left[ \right.\left. \mathbf {1} _ {\{\varphi (X) \geq \xi \}} \right] _ {| \xi = \xi_ {n}}\left. \right)\\&\xrightarrow {a . s .}&\frac {\alpha}{(1 - \alpha) ^ {2}} \mathbb {E} \left[ (\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*})   \left. \mathbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}} \right] _ {| \xi = \xi_ {n}}\right),\end{array}
$$

$$
\begin{array}{r c l} \mathbb {E} \left[ \left(\epsilon_ {n + 1} \epsilon_ {n + 1} ^ {T}\right) _ {2, 2} | \mathcal {F} _ {n} \right] & = & \mathbb {E} \left[ (\Delta N _ {n + 1}) ^ {2} | \mathcal {F} _ {n} \right] \\ & = & \frac {1}{(1 - \alpha) ^ {2}} \left(\mathbb {E} \left[ (\Psi (\varphi (X _ {n + 1})) - \xi) \textbf {1} _ {\{\varphi (X _ {n + 1}) \geq \xi \}} | \mathcal {F} _ {n} \right] _ {| \xi = \xi_ {n}} \right. \\ & & \left. - \mathbb {E} \left[ (\Psi (\varphi (X)) - \xi) \textbf {1} _ {\{\varphi (X) \geq \xi \}} \right] _ {| \xi = \xi_ {n}} ^ {2}\right) \\ & \xrightarrow {a. s.} & \frac {1}{(1 - \alpha) ^ {2}} \left(\mathbb {E} \left[ (\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*}) ^ {2} \textbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}} \right] \right. \\ & & \left. - \mathbb {E} \left[ (\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*}) \textbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}} \right] ^ {2}\right) \\ & = & \frac {1}{(1 - \alpha) ^ {2}} \mathrm{Var} \left((\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*}) \textbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}}\right). \end{array}
$$

Using the continuity of both functions $\xi \mapsto \mathbb { E } \left[ \left( \Psi ( \varphi ( X ) ) - \xi \right) \ \mathbf { 1 } _ { \{ \varphi ( X ) \geq \xi \} } \right]$ and $\xi \mapsto \mathbb { E } \left[ ( \Psi ( \varphi ( X ) ) - \xi ) ^ { 2 } \ \mathbf { 1 } _ { \{ \varphi ( X ) \geq \xi \} } \right]$ at $\xi _ { \alpha } ^ { * } ,$ , which follows from the continuity of Ψ and of the distribution function of $\varphi ( X )$ , finally yields the a.s. convergence of E $[ \epsilon _ { n + 1 } \epsilon _ { n + 1 } ^ { T } | \mathcal { F } _ { n } ]$ toward

$$
\Gamma = \left( \begin{array}{c c} \frac {\alpha}{1 - \alpha} & \frac {\alpha}{(1 - \alpha) ^ {2}} \mathbb {E} \left[ (\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*}) \textbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}} \right] \\ \frac {\alpha}{(1 - \alpha) ^ {2}} \mathbb {E} \left[ (\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*}) \textbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}} \right] & \frac {1}{(1 - \alpha) ^ {2}} \mathrm{Var} \left((\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*}) \textbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}}\right) \end{array} \right).
$$

If $\begin{array} { r } { \gamma _ { n } = \frac { \gamma _ { 1 } } { n ^ { a } } } \end{array}$ with $\gamma _ { 1 } > 0$ and $\textstyle { \frac { 1 } { 2 } } < a < 1$ , Ruppert-Polyak’s Theorem implies that

$$
\sqrt {n} \left(\bar {Z} _ {n} - z ^ {*}\right) \xrightarrow {\mathcal {L}} \mathcal {N} (0, \Sigma)
$$

where $\Sigma = M ^ { - 1 } \Gamma \left( M ^ { - 1 } \right) ^ { T }$ is given by (19). This completes the proof.

Remarks: It is possible to replace $w ( \xi , x )$ in (13) and (15) by $\begin{array} { r } { \tilde { w } ( \xi , x ) = \frac { 1 } { 1 - \alpha } \Psi ( \varphi ( x ) ) \mathbf { 1 } _ { \{ \varphi ( x ) \geq \xi \} } } \end{array}$ since $C _ { \alpha } ^ { * } = \mathbb { E } \left[ { \tilde { w } } \left( \xi _ { \alpha } ^ { * } , X \right) \right]$ . Thus, we only have to change also the martingale increment sequence $\left( \Delta N _ { n } \right) _ { n \ge 1 } \mathrm { b y } \left( \Delta \widetilde { N } _ { n } \right) _ { n \ge 1 }$ defined by

$$
\Delta \widetilde {N} _ {n} := \frac {1}{1 - \alpha} \left(\mathbb {E} \left[ \Psi (\varphi (X)) \mathbf {1} _ {\{\varphi (X) \geq \xi \}} \right] _ {| \xi = \xi_ {n - 1}} - \Psi (\varphi (X _ {n})) \mathbf {1} _ {\{\varphi (X _ {n}) \geq \xi_ {n - 1} \}}\right).
$$

This provides another procedure ${ \tilde { C } } _ { n }$ for the computation of the $\Psi \mathrm { - C V a R } _ { \alpha }$ which satisfies a Gaussian CLT with the same asymptotic covariance matrix.

The quantile estimate based on the inversion of the empirical distribution function satisfies a Gaussian CLT with the same asymptotic covariance matrix than the one of the procedure $\overline { { \xi } } _ { n } .$ , see for example [36] p.75. Obviously, there is no reason to believe that this first version can do better than the empirical quantile estimate. However, our quantile estimate has the advantage to be recursive: it naturally combines with a recursive IS algorithm in an adaptive way. In terms of computational complexity, once N loss samples have been generated, the behaviour of the inversion of the empirical distribution function method needs a sorting algorithm: good behaviour is $\mathcal { O } \left( N \log ( N ) \right)$ element comparisons to sort the list of loss samples. Whereas the behaviour of the recursive quantile algorithm is $\mathcal O \left( N \right)$

One shows that if we choose $\begin{array} { r } { \beta _ { n } = \frac { 1 } { n } , n \ge 1 } \end{array}$ and $\begin{array} { r } { \gamma _ { n } = \frac { 1 } { n ^ { a } } } \end{array}$ with $\textstyle { \frac { 1 } { 2 } } < a < 1$ in (15), the resulting two-time scale procedure satisfies a Gaussian CLT with the same asymptotic covariance matrix Γ (at rates $\sqrt { \gamma _ { n } ^ { - 1 } }$ and $\sqrt { n } )$ . However, by averaging the first component $\xi _ { n } ,$ the resulting procedure becomes asymptotically eficient (i.e. rate $\sqrt { n } )$

Proposition 2.5. (Estimation of variance and confidence interval) For every $n \geq 1$ , set

$$
\begin{array}{r c l} \sigma_ {n} ^ {2} & := & \frac {1}{(1 - \alpha) ^ {2}} \left(\frac {1}{n} \sum_ {k = 1} ^ {n} (\Psi (\varphi (X _ {k})) - \xi_ {k - 1}) ^ {2} \mathbf {1} _ {\{\varphi (X _ {k}) \geq \xi_ {k - 1} \}} \right. \\ & & \left. - \left(\frac {1}{n} \sum_ {k = 1} ^ {n} (\Psi (\varphi (X _ {k})) - \xi_ {k - 1})   \mathbf {1} _ {\{\varphi (X _ {k}) \geq \xi_ {k - 1} \}}\right) ^ {2}\right) \end{array}
$$

where $( \xi _ { n } ) _ { n \geq 0 }$ is the first component of (6). If (A2)<sub>a</sub> is satisfied for some $a \geq 2$ , then

$$
\sigma_ {n} ^ {2} \stackrel {a. s.} {\longrightarrow} \frac {1}{(1 - \alpha) ^ {2}} \mathrm{Var} \left((\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*}) \mathbf {1} _ {\varphi (X) \geq \xi_ {\alpha} ^ {*}}\right)
$$

and

$$
\sqrt {n} \xrightarrow [ \sigma_ {n} ]{C _ {n} - C _ {\alpha} ^ {*}} \xrightarrow {\mathcal {L}} \mathcal {N} (0, 1).\tag{22}
$$

Proof. The proof follows from standard arguments already used in the proof of the a.s. convergence of the sequence $( C _ { n } ) _ { n \geq 1 }$ defined by (13). □

In practice, the convergence of the algorithm will be chaotic. The bottleneck of this algorithm is that it is only updated on rare events since it tries to measure the tail distribution of $\varphi ( X )$ $\mathbb { P } ( \varphi ( X ) > \operatorname { V a R } _ { \alpha } ) = 1 - \alpha \approx 0$ . Another problem may be the simulation of $\varphi ( X )$ . In practice, we have to deal with large portfolios of complex derivative securities and options. Each evaluation may require a lot of computational eforts and takes a long time. So, for practical implementation it is necessary to combine the above procedure with variance reduction techniques to achieve accurate results at a reasonable cost. The most appropriate technique when dealing with rare events is IS.

## 2.3 Some background on IS using stochastic approximation algorithm

The second tool we want to introduce in this paper is a recursive IS procedure which increases the probability of simulations for which $\varphi ( X )$ exceeds ξ. Our goal is to combine it adaptively with our first naive algorithm. Assume that X has an absolutely continuous distribution $\mathbb { P } _ { X } ( d x ) =$ $p ( x ) \lambda _ { d } ( d x )$ where $\lambda _ { d }$ denotes the Lebesgue measure on $( \mathbb { R } ^ { d } , B o r ( \mathbb { R } ^ { d } ) )$ ). The main idea of importance sampling by translation applied to the computation of

$$
\mathbb {E} [ F (X) ],
$$

where $F \in L ^ { 2 } ( \mathbb { P } _ { X } )$ satisfies $\mathbb { P } ( F ( X ) \neq 0 ) > 0$ , is to use the invariance of the Lebesgue measure by translation, for every $\theta \in \mathbb { R } ^ { d }$

$$
\mathbb {E} [ F (X) ] = \mathbb {E} \left[ F (X + \theta) \frac {p (X + \theta)}{p (X)} \right],\tag{23}
$$

and among all these random vectors with the same expectation, we want to select the one with the lowest variance, i.e. the one with lowest quadratic norm

$$
Q (\theta) := \mathbb {E} \left[ F ^ {2} (X + \theta) \frac {p ^ {2} (X + \theta)}{p ^ {2} (X)} \right] \leq + \infty , \quad \theta \in \mathbb {R} ^ {d}.\tag{24}
$$

If the following assumption

$$
\forall \theta \in \mathbb {R} ^ {d}, \qquad \mathbb {E} \left[ F ^ {2} (X) \frac {p (X)}{p (X - \theta)} \right] <   + \infty\tag{B1}
$$

holds true, then $Q$ is everywhere finite and a reverse change of variable shows that:

$$
Q (\theta) = \mathbb {E} \left[ F ^ {2} (X) \frac {p (X)}{p (X - \theta)} \right], \quad \theta \in \mathbb {R} ^ {d}.\tag{25}
$$

Now if $p$ satisfies

$$
\left\{ \begin{array}{l l} (i) & \forall x \in \mathbb {R} ^ {d}, \theta \mapsto p (x - \theta) \text {is log - concave} \\ (i i) & \forall x \in \mathbb {R} ^ {d}, \lim _ {| \theta | \to + \infty} p (x - \theta) = 0 \quad \text {or} \forall x \in \mathbb {R} ^ {d}, \lim _ {| \theta | \to + \infty} \frac {p (x - \theta)}{p ^ {2} (x - \frac {\theta}{2})} = 0, \end{array} \right.\tag{B2}
$$

one shows that $Q$ is (strictly) finite, convex, goes to infinity at infinity so that arg min $Q \ =$ $\{ \nabla Q = 0 \}$ is non empty (see [1] and [27]). Provided that $\nabla Q$ admits a representation as an expectation, then it is possible to devise a recursive RM procedure to approximate the optimal parameter $\theta ^ { * }$ . Recursive IS by stochastic approximation has been first investigated by Kushner and then by several authors, see e.g. [11] and [14] in order to “optimize” or “improve” the change of measure in IS using a stochastic gradient RM algorithm based on the representation of $\nabla Q ( \theta )$ Recently, it has been brought back to light by Arouna (see [1]) in the Gaussian case, based on the natural representation of $\nabla Q$ obtained by formally diferentiating (25). Since we have no knowledge about the regularity of $F$ and do not wish to have any, we diferentiate the second representation of $Q$ in (25) and not (24). We obtain $\nabla Q ( \theta ) = \mathbb { E } \left[ K ( \theta , X ) \right]$

When $X = \mathcal { N } ( 0 , 1 ) , Q ( \theta ) = e ^ { \frac { | \theta | ^ { 2 } } { 2 } } \mathbb { E } [ F ^ { 2 } ( X ) e ^ { - \theta X } ]$ so that $K ( \theta , x ) = e ^ { \frac { | \theta | ^ { 2 } } { 2 } } F ^ { 2 } ( x ) e ^ { - \theta x } ( \theta - x )$ . However, given this resulting form of $K$ , the classical convergence results do not apply since $| | K ( \theta , X ) | | _ { 2 }$ is not sub-linear in $\theta$ (see condition (8) of Theorem 2.2). This induces the explosion of the pro cedure at almost every implementation as pointed out in [1]. This leads the author to introduce a “constrained” variant of the regular procedure based on repeated reinitializations known as the projection ${ } ^ { 6 6 } \mathrm { \dot { a } }$ la Chen”. It forces the stability of the algorithm and prevents explosion. Let us also mention a first alternative approach investigated in [1] and [3], where Arouna and Bardou change the function to be minimized by introducing an entropy based criterion. Although it is only an approximation, it turns out to be often close to the original method.

Recently, Lemaire and Pag\`es in [27] revisited the original approach and provided a new representation of $\nabla Q ( \theta )$ for which the resulting $K ( \theta , X )$ has a linear growth in $\theta$ so that all assumptions of Theorem 2.2 are satisfied. Thanks to a third translation of the variable $\theta ,$ it is possible to plug back the parameter $\theta \ ^ { \mathfrak { s } } \mathrm { i n t o } ^ { \mathfrak { s } } \ F$ , the function F having in common applications a known behaviour at infinity which makes possible to devise a “regular” and “unconstrained” stochastic algorithm. We will rely partially on this approach to devise our final procedure to compute both VaR and CVaR. To be more specific about the methodology proposed in [27], we introduce the following assumption on the probability density $p$ of X

$$
\exists b \in [ 1, 2 ] \text {   such   that   } \left\{ \begin{array}{l l} (i) & \frac {| \nabla p (x) |}{p (x)} = O (| x | ^ {b - 1}) \quad \text { as } \quad | x | \to \infty \\ (i i) & \exists \rho > 0, \log {(p (x))} + \rho | x | ^ {b} \text {   is   convex }, \end{array} \right.\tag{B3}
$$

and introduce the assumption on $F$ :

$$
\forall A > 0, \mathbb {E} \left[ F (X) ^ {2} e ^ {A | X | ^ {b - 1}} \right] <   + \infty .\tag{B4}
$$

One shows that as soon as (B1), (B2), (B3) and (B4) are satisfied, $Q _ { 1 }$ and $Q _ { 2 }$ are both finite and diferentiable on $\mathbb { R } ^ { d }$ with a gradient given by

$$
\nabla Q (\theta) := \mathbb {E} \left[ F (X - \theta) ^ {2} \underbrace {\frac {p ^ {2} (X - \theta)}{p (X) p (X - 2 \theta)} \frac {\nabla p (X - 2 \theta)}{p (X - 2 \theta)}} _ {W (\theta , X)} \right].\tag{26}
$$

This expression may look complicated at first glance but in fact the weight term $W ( \theta , X )$ can be easily controlled by a deterministic function of θ since

$$
| W (\theta , X) | \leq e ^ {2 \rho | \theta | ^ {b}} (A | x | ^ {b - 1} + A | \theta | ^ {b - 1} + B)\tag{27}
$$

for some real constants A and B. In the case of a normal distribution $X \overset { d } { = } \mathcal { N } ( 0 ; 1 )$

$$
W (\theta , X) = e ^ {\theta^ {2}} (2 \theta - X).
$$

$\mathrm { S o } ,$ , if we have a control on the growth of the function $F _ { ; }$ , typically for some positive constant c

$$
\left\{ \begin{array}{c} \forall x \in \mathbb {R} ^ {d}, | F (x) | \leq G (x) \quad \text { and } \quad G (x + y) \leq C (1 + G (x)) ^ {c} (1 + G (y)) ^ {c} \\ \mathbb {E} \left[ | X | ^ {2 (b - 1)} G (X) ^ {4 c} \right] <   + \infty , \end{array} \right.\tag{B5}
$$

then by setting

$$
\widetilde {W} (\theta , X) := \frac {e ^ {- 2 \rho | \theta | ^ {b}}}{1 + G (- \theta) ^ {2 c}} W (\theta , X),\tag{28}
$$

we can define K by

$$
K (\theta , x) := F (x - \theta) ^ {2} \widetilde {W} (\theta , X)\tag{29}
$$

so that it satisfies the linear growth assumption (8) of Theorem 2.2 and

$$
\left\{\theta \in \mathbb {R} ^ {d} \mid \mathbb {E} [ K (\theta , X) ] = 0 \right\} = \left\{\theta \in \mathbb {R} ^ {d} \mid \nabla Q (\theta) = 0 \right\}.
$$

Moreover, since $Q$ is convex $\nabla Q$ satisfies (7). Now we are in position to derive a recursive unconstrained RM algorithm

$$
\theta_ {n} = \theta_ {n - 1} - \gamma_ {n} K (\theta_ {n - 1}, X _ {n}), \theta_ {0} \in \mathbb {R} ^ {d},\tag{30}
$$

that a.s. converges to an arg min Q-valued (square integrable) random variable $\theta ^ { * }$

## 3 Design of a faster procedure: importance sampling and moving confidence level

## 3.1 Unconstrained adaptive importance sampling device

We noted previously that the bottleneck in using the above algorithm lies in its very slow and chaotic convergence owing to the fact that $\mathbb { P } ( \varphi ( X ) > \xi _ { \alpha } ^ { * } ) = 1 - \alpha$ is close to 0. This means that we observe fewer and fewer simulations for which $\varphi ( X _ { k } ) > \xi _ { k - 1 }$ as the algorithm evolves. Thus, it becomes more and more dificult to compute eficiently some estimates of $\mathrm { V a R } _ { \alpha }$ and $\mathrm { C V a R } _ { \alpha }$ when $\alpha \approx 1$ . Moreover, in the bank and energy sectors, practitioners usually deal with huge portfolio made of hundreds or thousands of risk factors and options. The evaluation step of $\varphi ( X )$ may be extremely time consuming. Consequently, to achieve accurate estimates of both $\operatorname { V a R } _ { \alpha }$ and $\mathrm { C V a R } _ { c }$ x with reasonable computational efort, the above algorithm (16) drastically needs to be speeded up by an IS procedure to “recenter” the simulations where “things do happen”, i.e. which generates scenarios for which $\varphi ( X )$ exceeds ξ.

In this section we will focus on IS by mean translation. Our aim is to combine adaptively the IS (unconstrained) recursive procedure investigated in [27] with our first “naive” approach described in (16). Doing so every new sample is used to both optimize the IS change of measure and update VaR and CVaR procedures. We plan to minimize the asymptotic variance of both components of the algorithm (in its “averaged” form, as detailed in Theorem 2.4), namely

$$
\frac {\alpha (1 - \alpha)}{f _ {\varphi (X)} (\xi_ {\alpha} ^ {*})} = \frac {\mathrm{Var} (\mathbf {1} _ {\varphi (X) \geq \xi_ {\alpha} ^ {*}})}{f _ {\varphi (X)} (\xi_ {\alpha} ^ {*})} \quad \mathrm{fortheVaR} _ {\alpha},\tag{31}
$$

and,

$$
\frac {\operatorname{Var} \left(\left(\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*}\right) \mathbf {1} _ {\varphi (\mathbf {X}) \geq \xi_ {\alpha} ^ {*}}\right)}{(1 - \alpha) ^ {2}} \quad \text {for the CVaR} _ {\alpha},\tag{32}
$$

provided the non-degeneracy assumption

$$
\forall \xi \in \arg \min V, \mathbb {P} \left(\left(\Psi (\varphi (X)) - \xi\right) ^ {2} \mathbf {1} _ {\{\varphi (X) \geq \xi \}} > 0\right) > 0,\tag{A3}
$$

holds. Since the density $f _ { \varphi ( X ) } ( \xi _ { \alpha } ^ { * } )$ is an intrinsic constant (and comes in fact from the Jacobian matrix $D h ( \xi _ { \alpha } ^ { * } , C _ { \alpha } ^ { * } )$ of the mean function h of the algorithm) we are led to apply the IS paradigm described in Section 2.3 to

$$
F _ {1} ^ {*} (X) = \mathbf {1} _ {\varphi (X) \geq \xi_ {\alpha} ^ {*}} \quad \text { and } \quad F _ {2} ^ {*} (X) = (\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*})   \mathbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}}.
$$

Let us temporary forget that of course we do not know $\xi _ { \alpha } ^ { * }$ at this stage. Those two functionals are related to the minimization of the two convex functions

$$
Q _ {1} (\theta , \xi_ {\alpha} ^ {*}) := \mathbb {E} \left[ \mathbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}} \frac {p (X)}{p (X - \theta)} \right]\tag{33}
$$

$$
Q _ {2} (\mu , \xi_ {\alpha} ^ {*}) := \mathbb {E} \left[ \left(\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*}\right) ^ {2} \mathbf {1} _ {\{\varphi (X) \geq \xi_ {\alpha} ^ {*} \}} \frac {p (X)}{p (X - \mu)} \right].\tag{34}
$$

We can apply to these functions the minimizing procedure (30) described at section 2.3. Since

$$
H _ {1} (\xi_ {\alpha} ^ {*}, x) = 1 - \frac {1}{1 - \alpha} F _ {1} ^ {*} (x) \quad \mathrm{and} \quad H _ {2} (\xi_ {\alpha} ^ {*}, C _ {\alpha} ^ {*}, x) = C _ {\alpha} ^ {*} - \xi_ {\alpha} ^ {*} - \frac {1}{1 - \alpha} F _ {2} ^ {*} (x)\tag{35}
$$

it is clear, owing to (23) that

$$
\mathbb {E} \left[ H _ {i} (\xi_ {\alpha} ^ {*}, X) \right] = \mathbb {E} \left[ H _ {i} \left(\xi_ {\alpha} ^ {*}, X + \theta\right) \frac {p (X + \theta)}{p (X)} \right] i = 1, 2.
$$

Now, since we do not know either $\xi _ { \alpha } ^ { \ast }$ and $C _ { \alpha } ^ { * }$ (the $\operatorname { V a R } _ { \alpha }$ and the $\mathrm { C V a R } _ { \alpha } )$ respectively we make the whole procedure adaptive by replacing at step n, these unknown parameters by their running approximation at step n 1. This finally justifies to introduce the following global procedure. One defines the state variable, for $n \geq 0$ ，

$$
Z _ {n} := \left(\xi_ {n}, C _ {n}, \theta_ {n}, \mu_ {n}\right),
$$

where $\xi _ { n } , \ C _ { n }$ denotes the $\operatorname { V a R } _ { \alpha }$ and the $\mathrm { C V a R } _ { \alpha }$ approximate, $\theta _ { n } , \ \mu _ { n }$ denotes the variance reducers for the VaR and the CVaR procedures. We update this state variable recursively by

$$
Z _ {n} = Z _ {n - 1} - \gamma_ {n} L \left(Z _ {n - 1}, X _ {n}\right),\tag{36}
$$

where $( X _ { n } ) _ { n \geq 1 }$ is an i.i.d. sequence with distributions X (and probability density p) and

$$
\begin{array}{r c l} L _ {1} (\xi , \theta , x) & := & e ^ {- \rho | \theta | ^ {b}} \left(1 - \frac {1}{1 - \alpha} \mathbf {1} _ {\{\varphi (x + \theta) \geq \xi \}} \frac {p (x + \theta)}{p (x)}\right), \\ L _ {2} (\xi , C, \mu , x) & := & C - \xi - \frac {1}{1 - \alpha} (\Psi (\varphi (x + \mu)) - \xi) \mathbf {1} _ {\{\varphi (x + \mu) \geq \xi \}} \frac {p (x + \mu)}{p (x)}, \\ L _ {3} (\xi , \theta , x) & := & e ^ {- 2 \rho | \theta | ^ {b}} \mathbf {1} _ {\{\varphi (x - \theta) \geq \xi \}} \frac {p ^ {2} (x - \theta)}{p (x) p (x - 2 \theta)} \frac {\nabla p (x - 2 \theta)}{p (x - 2 \theta)}, \\ L _ {4} (\xi , \mu , x) & := & \frac {e ^ {- 2 \rho | \mu | ^ {b}}}{1 + G (- \mu) ^ {2 c} + \xi^ {2}} (\Psi (\varphi (x - \mu)) - \xi) ^ {2} \end{array}\tag{37}
$$

$$
\times \mathbf {1} _ {\{\varphi (x - \mu) \geq \xi \}} \frac {p ^ {2} (x - \mu)}{p (x) p (x - 2 \mu)} \frac {\nabla p (x - 2 \mu)}{p (x - 2 \mu)}.\tag{38}
$$

The following proposition establishes the a.s. convergence of the procedure. For the sake of simplicity we will assume the uniqueness of the $\mathrm { V a R } _ { \alpha }$ of $\varphi ( X )$

Proposition 3.1. (Eficient computation of VaR and $C V a R )$ . Suppose that $\Psi ( \varphi ( X ) ) \in L ^ { 2 } \left( \mathbb { P } \right)$ , that the distribution function of $\varphi ( X )$ is continuous and increasing (so that $\operatorname { V a R } _ { \alpha } ( \varphi ( X ) )$ is unique) and that (A3) holds. Assume that, for every $\xi \in \mathbb { R } , Q _ { i } ( . , \xi ) \ ( i { = } 1 , 2 )$ satisfies (B1), i.e.

$$
\forall \theta \in \mathbb {R} ^ {d}, \mathbb {E} \left[ \left(1 + (\Psi (\varphi (X)) - \xi) ^ {2}\right) \boldsymbol {1} _ {\{\varphi (X) \geq \xi \}} \frac {p (X)}{p (X - \theta)} \right] <   + \infty .\tag{39}
$$

Suppose that p satisfies (B2) and (B3) and that

$$
\forall A > 0, \mathbb {E} \left[ (\Psi (\varphi (X)) ^ {2} + 1) e ^ {A | X | ^ {b - 1}} \right] <   + \infty .
$$

Assume that the step sequence $( \gamma _ { n } ) _ { n \geq 1 }$ satisfies (A1). Then,

$$
Z _ {n} \xrightarrow {a . s .} z ^ {*} := (\xi_ {\alpha} ^ {*}, C _ {\alpha} ^ {*}, \theta_ {\alpha} ^ {*}, \mu_ {\alpha} ^ {*})
$$

where $\xi _ { \alpha } ^ { * } = \mathrm { V a R } _ { \alpha } ( \varphi ( X ) ) , \ C _ { \alpha } ^ { * } = \Psi \mathrm { - C V a R } _ { \alpha } ( \varphi ( X ) )$ and $( \theta _ { \alpha } ^ { * } , \mu _ { \alpha } ^ { * } )$ are the optimal variance reducers (to be precise some random vectors taking values in $\{ \nabla Q _ { 1 } ( \xi _ { \alpha } ^ { * } , . ) = 0 \}$ and $\{ \nabla Q _ { 2 } ( \xi _ { \alpha } ^ { * } , . ) = 0 \}$ respectively).

Proof. We first prove the a.s. convergence of the 3-tuple $\left( \xi _ { n } , \theta _ { n } , \mu _ { n } \right)$ that of $( C _ { n } ) _ { n \geq 1 }$ will follow by the same arguments used in the proof in Section 2.2. The mean function l is defined by

$$
l (\xi , \theta , \mu) := \left(e ^ {- \rho | \theta | ^ {b}} \left(1 - \frac {1}{1 - \alpha} \mathbb {P} (\varphi (X) \geq \xi)\right), e ^ {- 2 \rho | \theta | ^ {b}} \nabla Q _ {1} (\theta , \xi), \frac {e ^ {- 2 \rho | \mu | ^ {b}}}{1 + G (- \mu) ^ {c} + \Psi (\xi) ^ {2}} \nabla Q _ {2} (\mu , \xi)\right),
$$

hence,

$$
\mathcal {T} ^ {*} = \{l = 0 \} = \{\xi_ {\alpha} ^ {*} \} \times \{\nabla Q _ {1} (\xi_ {\alpha} ^ {*},.) = 0 \} \times \{\nabla Q _ {2} (\xi_ {\alpha} ^ {*},.) = 0 \}.
$$

In order to apply the extended Robbins-Monro Theorem, we have to check the following facts:

Mean reversion: One checks that $\forall \zeta = ( \xi , \theta , \mu ) \in \mathbb { R } \times \mathbb { R } ^ { d } \times \mathbb { R } ^ { d } \setminus \mathcal { T } ^ { * } , \forall \zeta ^ { * } \in \mathcal { T } ^ { * }$

$$
\begin{array}{r c l} \langle \zeta - \zeta^ {*}, l (\zeta) \rangle & = & e ^ {- \rho | \theta | ^ {b}} (\xi - \xi_ {\alpha} ^ {*}) \frac {(\mathbb {P} (\varphi (X) \leq \xi) - \alpha)}{1 - \alpha} + \frac {e ^ {- 2 \rho | \theta | ^ {b}}}{1 - \alpha} \langle \theta - \theta_ {\alpha} ^ {*}, \nabla Q _ {1} (\theta , \xi) \rangle \\ & & + \frac {e ^ {- 2 \rho | \mu | ^ {b}}}{(1 - \alpha) (1 + F (- \mu) ^ {2 c})} \langle \mu - \mu_ {\alpha} ^ {*}, \nabla Q _ {2} (\mu , \xi) \rangle > 0, \end{array}
$$

owing to the convexity of $\theta \mapsto Q _ { 1 } ( \theta , \xi )$ and $\mu \mapsto Q _ { 2 } ( \mu , \xi )$ , for every $\xi \in \mathbb { R }$

Linear growth: Let us first deal with $L _ { 1 }$ . First note that:

$$
\mathbb {E} \left[ L _ {1} (\xi , \theta , X) ^ {2} \right] \leq C \left(1 + \mathbb {E} \left[ e ^ {- 2 \rho | \theta | ^ {b}} \mathbf {1} _ {\{\varphi (X + \theta) \geq \xi \}} \frac {p ^ {2} (X + \theta)}{p ^ {2} (X)} \right]\right) \leq C \left(1 + \mathbb {E} \left[ e ^ {- 2 \rho | \theta | ^ {b}} \frac {p (X)}{p (X - \theta)} \right]\right).
$$

Now, elementary computations show (see [27] for more details) that (B3)(ii) implies that

$$
\frac {p ^ {2} (x)}{p (x - \theta)} \leq e ^ {2 \rho | \theta | ^ {b}} p (x + \theta),
$$

so that

$$
\mathbb {E} \left[ e ^ {- 2 \rho | \theta | ^ {b}} \frac {p (X)}{p (X - \theta)} \right] \leq \mathbb {E} \left[ \frac {p (X + \theta)}{p (X)} \right] = 1.
$$

$L _ { 3 }$ and $L _ { 4 }$ can be treated by a straightforward adaptation of the proofs in [27]. Then, one can apply Theorem 2.2 which yields the announced result for $\left( \xi _ { n } , \theta _ { n } , \mu _ { n } \right)$ . The a.s. convergence of $C _ { n }$ toward $C _ { \alpha } ^ { * }$ can be deduced from the a.s. convergence of the series

$$
M _ {n} ^ {\gamma} := \sum_ {k = 1} ^ {n} \gamma_ {k} \Delta \widetilde {M _ {k}}, n \geq 1,
$$

where $\Delta \widetilde { M } _ { n }$ are martingale increments defined by

$$
\begin{array}{r c l} \Delta \widetilde {M} _ {n} & = & \mathbb {E} [ (\Psi (\varphi (X)) - \xi)   \mathbf {1} _ {\{\varphi (X) \geq \xi \}} ] _ {| \xi = \xi_ {n - 1}} \\ & & - (\Psi (\varphi (X _ {n} + \mu_ {n - 1})) - \xi_ {n - 1})   \mathbf {1} _ {\{\varphi (X _ {n} + \mu_ {n - 1}) \geq \xi_ {n - 1} \}} \frac {p (X _ {n} + \mu_ {n - 1})}{p (X _ {n})}, n \geq 1, \end{array}
$$

satisfying

$$
\mathbb {E} \left[ \Delta \widetilde {M} _ {n} ^ {2} | \mathcal {F} _ {n - 1} \right] \leq \mathbb {E} \left[ (\Psi (\varphi (X + \mu)) - \xi) \mathbf {1} _ {\{\varphi (X + \mu) \geq \xi \}} \frac {p (X + \mu)}{p (X)} \right] _ {| \xi = \xi_ {n - 1}, \theta = \theta_ {n - 1}, \mu = \mu_ {n - 1}}.
$$

We conclude by the same arguments used in the proof in Section 2.2.

Now, we are interested by the rate of convergence of the procedure. It shows that the algorithm behaves as expected under quite standard assumptions: it satisfies a Gaussian CLT with optimal rate and minimal variances.

Theorem 3.2. Suppose the assumptions of Proposition 3.1 hold true. Assume that $\Psi ( \varphi ( X ) ) \in$ $L ^ { 2 a } ( \mathbb { P } )$ for some $a > 1$ and that the step sequence is $\begin{array} { r } { \gamma _ { n } = \frac { \gamma _ { 1 } } { n ^ { p } } } \end{array}$ with $\begin{array} { r } { \frac { 1 } { 2 } < p < 1 } \end{array}$ and $\gamma _ { 1 } > 0$ . Suppose that the density $f _ { \varphi ( X ) }$ is continuous and strictly positive on its support. Let $( \overline { { \xi } } _ { n } , \overline { { C } } _ { n } ) _ { n \geq 1 }$ be the sequence of Cesaro means defined by:

$$
\overline {{\xi}} _ {n} := \frac {\xi_ {0} + \ldots + \xi_ {n - 1}}{n}, \quad \overline {{C}} _ {n} := \frac {C _ {0} + \ldots + C _ {n - 1}}{n}, n \geq 1.
$$

This sequence satisfies the following CLT:

$$
\sqrt {n} \binom{\overline {{\xi}} _ {n} - \xi_ {\alpha} ^ {*}}{\overline {{C}} _ {n} - C _ {\alpha} ^ {*}} \xrightarrow {\mathcal {L}} \mathcal {N} (0, \Sigma^ {*}) \quad a s n \to + \infty ,\tag{40}
$$

where

$$
\begin{array}{r c l} \Sigma_ {1, 1} ^ {*} & = & \frac {1}{f _ {\varphi (X)} ^ {2} (\xi_ {\alpha} ^ {*})} \mathrm{Var} \bigg (\mathbf {1} _ {\{\varphi (X + \theta_ {\alpha} ^ {*}) \geq \xi_ {\alpha} ^ {*} \}} \frac {p (X + \theta_ {\alpha} ^ {*})}{p (X)} \bigg), \\ \Sigma_ {1, 2} ^ {*} & = & \Sigma_ {2, 1} ^ {*} = \frac {1}{(1 - \alpha) f _ {\varphi (X)} (\xi_ {\alpha} ^ {*})} \mathrm{Cov} \left((\Psi (\varphi (X + \mu_ {\alpha} ^ {*})) - \xi_ {\alpha} ^ {*}) \mathbf {1} _ {\{\varphi (X + \mu_ {\alpha} ^ {*}) > \xi_ {\alpha} ^ {*} \}} \frac {p (X + \mu_ {\alpha} ^ {*})}{p (X)}, \right. \\ & & \left. \mathbf {1} _ {\{\varphi (X + \theta_ {\alpha} ^ {*}) \geq \xi_ {\alpha} ^ {*} \}} \frac {p (X + \theta_ {\alpha} ^ {*})}{p (X)}\right), \\ \Sigma_ {2, 2} ^ {*} & = & \frac {1}{(1 - \alpha) ^ {2}} \mathrm{Var} \left((\Psi (\varphi (X + \mu_ {\alpha} ^ {*})) - \xi_ {\alpha} ^ {*}) \mathbf {1} _ {\{\varphi (X + \mu_ {\alpha} ^ {*}) \geq \xi_ {\alpha} ^ {*} \}} \frac {p (X + \mu_ {\alpha} ^ {*})}{p (X)}\right). \end{array}
$$

Proof. The proof is built like the one of Theorem 2.4. If we denote h the mean function of the global algorithm $h ( z ) = \mathbb { E } [ L ( z , X ) ]$ , the algorithm (36) can be written as

$$
Z _ {n} = Z _ {n - 1} - \gamma_ {n} \left(h (Z _ {n - 1}) + \tilde {\epsilon} _ {n}\right), n \geq 1, Z _ {0} = (\xi_ {0}, 0), \xi_ {0} \in L ^ {1} (\mathbb {P}),\tag{41}
$$

where the first two components of h are the same function as the ones in the proof of Theorem 2.4 and $( \tilde { \epsilon } _ { n } ) _ { n \geq 1 }$ denotes the ${ \mathcal { F } } _ { n }$ -adapted martingale increments sequence where

$$
\begin{array}{r c l} \tilde {\epsilon} _ {1, n} & := & \frac {1}{1 - \alpha} \left(\mathbb {P} (\varphi (X) \geq \xi) _ {| \xi = \xi_ {n}} - \mathbf {1} _ {\{\varphi (X _ {n + 1} + \theta_ {n}) \geq \xi_ {n} \}} \frac {p (X _ {n + 1} + \theta_ {n})}{p (X _ {n + 1})}\right), \\ \tilde {\epsilon} _ {2, n} & := & \frac {1}{1 - \alpha} \left(\mathbb {E} [ (\Psi (\varphi (X)) - \xi)   \mathbf {1} _ {\{\varphi (X) \geq \xi \}} ] _ {| \xi = \xi_ {n}} \right. \\ & & \left. - (\Psi (\varphi (X _ {n + 1} + \mu_ {n})) - \xi_ {n})   \mathbf {1} _ {\{\varphi (X _ {n + 1} + \mu_ {n}) \geq \xi_ {n} \}} \frac {p (X _ {n + 1} + \mu_ {n})}{p (X _ {n + 1})}\right). \end{array}
$$

One can check easily that the sequence $( \widetilde { \epsilon } _ { n } ) _ { n \ge 1 }$ satisfies $( i ) - ( i v )$ of (17).

Remarks:  There exists a CLT for the whole sequence $( Z _ { n } ) _ { n \geq 1 }$ and for its empirical mean $( \overline { { Z } } _ { n } ) _ { n \geq 1 }$ according to Ruppert and Polyak averaging principle. We only stated the result for the two components of interest (the ones which converge to VaR and CVaR respectively) since we only need rough estimates for the other two (see below).

In the first Central Limit Theorem (Theorem 2.4) for quantile estimation, the factor $\alpha ( 1 - \alpha )$ is the variance of the indicator function of the event $\{ \varphi ( X ) \geq \xi _ { \alpha } ^ { * } \}$ . With our recursive IS procedure, it is replaced by the variance of the shifted indicator function modified by the measure change: Var $\left( \mathbf { 1 } _ { \{ \varphi ( X + \theta _ { \alpha } ^ { * } ) > \xi _ { \alpha } ^ { * } \} } \frac { p ( X + \theta _ { \alpha } ^ { * } ) } { p ( X ) } \right)$ . For further details on the rate of convergence of the unconstrained recursive importance sampling procedure, we refer to [27].

Now, let us point out an important issue. The algorithm (36) raises an important problem numerically speaking. Actually, we have two algorithm $\xi _ { n }$ and $( \theta _ { n } , \mu _ { n } )$ that are in competitive conditions, i.e. on one hand, we added an IS procedure to $( \xi _ { n } ) _ { n \geq 1 }$ to improve the convergence toward $\xi _ { \alpha } ^ { * }$ , and on the other hand, the adjustment of the parameters $( \theta _ { n } , \mu _ { n } )$ “need” some samples $X _ { n + 1 }$ satisfying $\varphi ( X _ { n + 1 } - \theta _ { n } ) > \xi _ { n }$ and $\varphi ( X _ { n + 1 } - \mu _ { n } ) > \xi _ { n } ~ ( \Psi \equiv I d )$ which tend to become rare events. Somehow, we postponed the problems resulting from rare events on the IS procedure itself which may “freeze”. This in term suggests to break the link between the VaR-CVaR and the IS procedures by introducing a VaR companion procedure that will drive the IS parameters to the tail distribution. A solution to do this is to make the confidence level increase slowly from a lower value (say $\alpha _ { 0 } = 5 0 \% )$ up to the target level α. This kind of incremental threshold increase has been already proposed in [22] in a diferent framework. This idea is developed in the next section.

## 3.2 How to control the move towards the critical risk area: the final procedure

From a theoretical point of view, so far, we considered the purely adaptive approach where we approximate $( \xi _ { \alpha } ^ { \ast } , C _ { \alpha } ^ { \ast } , \theta _ { \alpha } ^ { \ast } , \mu _ { \alpha } ^ { \ast } )$ using the same innovation sequences. From a numerical point of view, we only need a rough estimate of the optimal IS parameters $( \theta _ { \alpha } ^ { * } , \mu _ { \alpha } ^ { * } )$ . So that we are led to break the algorithm into two phases. Firstly, we compute a rough estimate of the optimal IS parameters $( \theta _ { M } , \mu _ { M } )$ with a small number of iterations M and in a second time, estimate the $\operatorname { V a R } _ { \alpha }$ and the $\mathrm { C V a R } _ { \alpha }$ with those optimized parameters with N iterations $( M \ll N$ in practice).

Now, in order to circumvent the problem induced by the IS procedure, we propose to introduce companion VaR procedure (without IS, $i . e .$ , based on $H _ { 1 }$ from Section 2.2) that will lead the IS parameters into the critical risk area during a first phase of the simulation, say the first M iterations. An idea to control the growth of $\theta _ { n }$ and $\mu _ { n }$ at the beginning of the algorithm, since we have no idea on how to twist the distribution of $\varphi ( X )$ , is to move slowly toward the target critical risk area (at level α) in which $\varphi ( X )$ exceeds ξ by introducing a non-decreasing sequence $\alpha _ { n }$ slowly converging to α during the first phase. Since the algorithm for the CVaR component $C _ { n }$ is free of $\alpha ,$ by doing so, we only modify the VaR procedure $\xi _ { n } .$ . The function $H _ { 1 }$ in (16) is replaced by its counterpart which depends on the moving confidence level $\alpha _ { n } .$ , namely

$$
\hat {\xi} _ {n} = \hat {\xi} _ {n - 1} - \gamma_ {n} \hat {H} _ {1} \left(\hat {\xi} _ {n - 1}, X _ {n}, \alpha_ {n}\right), n \geq 1, \hat {\xi} _ {0} = \xi_ {0} \in L ^ {1} (\mathbb {P}).\tag{42}
$$

where,

$$
\forall \xi \in \mathbb {R}, \forall x \in \mathbb {R} ^ {d}, \forall \hat {\alpha} \in ] 0, 1 [, \hat {H} _ {1} (\xi , x, \hat {\alpha}) = 1 - \frac {1}{1 - \hat {\alpha}} \mathbf {1} _ {\{\varphi (x) \geq \xi \}}.
$$

The sequence $\left( \hat { \xi } _ { n } \right) _ { n > 0 }$ is only designed to drive “smoothly” the IS procedures toward the “critical area” at the beginning of the procedure, say during the first M iterations and in no case to approximate $\xi _ { \alpha } ^ { * }$ or $C _ { \alpha } ^ { * }$ . To be more precise, we define recursively the variance reducer sequence $( \hat { \theta } _ { n } ) _ { n \geq 1 } , ( \hat { \mu } _ { n } ) _ { n \geq 1 }$ by plugging at each step $n , \hat { \xi } _ { n - 1 }$ into $L _ { 3 } ( . , \hat { \theta } _ { n - 1 } , X _ { n } )$ and $L _ { 4 } ( . , \hat { \mu } _ { n - 1 } , X _ { n } )$ as defined in Section 3.1. This reads as follows, for $n \geq 1$

$$
\left\{ \begin{array}{l} \hat {\xi} _ {n} = \hat {\xi} _ {n - 1} - \gamma_ {n} \hat {H} _ {1} \left(\hat {\xi} _ {n - 1}, X _ {n}, \alpha_ {n}\right), \hat {\xi} _ {0} \in L ^ {1} (\mathbb {P}), \\ \hat {\theta} _ {n} = \hat {\theta} _ {n - 1} - \gamma_ {n} L _ {3} \left(\hat {\xi} _ {n - 1}, \hat {\theta} _ {n - 1}, X _ {n}\right), \theta_ {0} \in \mathbb {R} ^ {d}, \\ \hat {\mu} _ {n} = \hat {\mu} _ {n - 1} - \gamma_ {n} L _ {4} \left(\hat {\xi} _ {n - 1}, \hat {\mu} _ {n - 1}, X _ {n}\right), \mu_ {0} \in \mathbb {R} ^ {d}. \end{array} \right.\tag{43}
$$

Although, we are not really interested in the asymptotic of this procedure $( \hat { \xi } _ { n } )$ , its theoretical convergence follows from Theorem 2.2: as a matter of fact if we define a remainder term $r _ { n }$ by:

$$
r _ {n} := \hat {H} _ {1} \left(\hat {\xi} _ {n - 1}, X _ {n}, \alpha_ {n}\right) - H _ {1} \left(\hat {\xi} _ {n - 1}, X _ {n}\right), n \geq 1,
$$

the procedure defined by (43) now reads

$$
\hat {\xi} _ {n} = \hat {\xi} _ {n - 1} - \gamma_ {n} (H _ {1} (\hat {\xi} _ {n - 1}, X _ {n}) + r _ {n}), n \geq 1, \hat {\xi} _ {0} \in L ^ {1} (\mathbb {P}).\tag{44}
$$

One checks that

$$
| r _ {n} | \leq \frac {| \alpha_ {n} - \alpha |}{(1 - \alpha) ^ {2}},
$$

so that Assumption (9) of Theorem 2.2 is satisfied as soon as

$$
\sum_ {n \geq 1} \gamma_ {n} (\alpha - \alpha_ {n}) ^ {2} <   + \infty .
$$

## 3.3 A final procedure for practical implementation

In practice, we divided our procedure into two phases:

✄ Phase I is devoted to the estimation of the variance reducers $( \theta _ { \alpha } ^ { * } , \mu _ { \alpha } ^ { * } )$ using (43). The moving confidence level $\alpha$ has been settled as follows $( M \approx 1 5 0 0 0 )$ :

$$
\alpha_ {n} = 50 \% \text { for } 1 \leq n \leq M _ {1} := M / 3, \alpha_ {n} = 80 \% \text { for } M _ {1} <   n \leq 2 M _ {1}, \alpha_ {n} = \alpha \text { for } 2 M _ {1} <   n \leq M.
$$

✄ Phase II produces some estimates for $( \xi _ { \alpha } ^ { * } , C _ { \alpha } ^ { * } )$ based on the procedure defined by (36) and its Cesaro mean with N iterations. Note that during this phase, we keep on updating the IS parameters adaptively.

Now, we can summarize the two phase of the final procedure by the following pseudo-code:

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Phase I: Estimation of  $(\mu_{\alpha}^{*}, \theta_{\alpha}^{*})$ .  $M \ll N$  (typically  $M \approx N/100$ ).
for n = 1 to M do
    $\hat{\xi}_{n} = \hat{\xi}_{n-1} - \gamma_{n} \hat{H}_{1} \left( \hat{\xi}_{n-1}, X_{n}, \alpha_{n} \right),$ $\hat{\theta}_{n} = \hat{\theta}_{n-1} - \gamma_{n} L_{3} \left( \hat{\xi}_{n-1}, \hat{\theta}_{n-1}, X_{n} \right),$ $\hat{\mu}_{n} = \hat{\mu}_{n-1} - \gamma_{n} L_{4} \left( \hat{\xi}_{n-1}, \hat{\mu}_{n-1}, X_{n} \right).$ 
end for
Phase II: Estimation of  $(\xi_{\alpha}^{*}, C_{\alpha}^{*})$ . Set, for instance,  $\xi_{0} = \hat{\xi}_{M}$ ,  $C_{0} = 0$ ,  $\theta_{0} = \hat{\theta}_{M}$ , and  $\mu_{0} = \hat{\mu}_{M}$ .
for n = 1 to N do
    $\xi_{n} = \xi_{n-1} - \gamma_{n} L_{1} \left( \xi_{n-1}, \theta_{n-1}, X_{n} \right),$ $C_{n} = C_{n-1} - \gamma_{n} L_{2} \left( \xi_{n-1}, C_{n-1}, \mu_{n-1}, X_{n} \right),$ $\theta_{n} = \theta_{n-1} - \gamma_{n} L_{3} \left( \xi_{n-1}, \theta_{n-1}, X_{n} \right),$ $\mu_{n} = \mu_{n-1} - \gamma_{n} L_{4} \left( \xi_{n-1}, \mu_{n-1}, X_{n} \right),$ 
    Compute the Cesaro means
    $\bar{\xi}_{n} = \bar{\xi}_{n-1} - \frac{1}{n} \left( \bar{\xi}_{n-1} - \xi_{n} \right),$ $\bar{C}_{n} = \bar{C}_{n-1} - \frac{1}{n} \left( \bar{C}_{n-1} - C_{n} \right).$ 
end for
$(\xi_{\alpha}^{*}, C_{\alpha}^{*})$  is estimated by  $(\bar{\xi}_{N}, \bar{C}_{N})$ .
</div>

An alternative, especially as concerns practical implementation, is to replace to Phase II by

Phase II’ in which the variance reducers coming from Phase I are frozen at $\hat { \theta } _ { M } , \hat { \mu } _ { M }$ The only updated sequence is $( \xi _ { n } , C _ { n } )$ , as follows

$$
\begin{array}{r c l} \xi_ {n} & = & \xi_ {n - 1} - \gamma_ {n} L _ {1} (\xi_ {n - 1}, \hat {\theta} _ {M}, X _ {n}), \\ C _ {n} & = & C _ {n - 1} - \gamma_ {n} L _ {2} (\xi_ {n - 1}, C _ {n - 1}, \hat {\mu} _ {M}, X _ {n}). \end{array}
$$

## 4 Towards some extensions

## 4.1 Extension to exponential change of measure: the Esscher transform

Considering an exponential change of measure (also called Esscher transform) instead of the mean translation is a rather natural idea that has already been investigated in [20] and [27] to extend the constrained IS stochastic approximation algorithm with repeated projections introduced in [1].

We briefly introduce the framework and give the main results without any proofs (for more details, see [27] and [13]). Let ψ denote the cumulant generating function (or log-Laplace) of $X ~ i . e .$ the function defined by $\psi ( \theta ) : = \log \mathbb { E } [ e ^ { \langle \theta , X \rangle } ]$ . We assume that $\psi ( \theta ) < + \infty$ , which implies that $\psi$ is an infinitely diferentiable convex function and define

$$
p _ {\theta} (x) = e ^ {\langle \theta , x \rangle - \psi (\theta)} p (x), \quad x \in \mathbb {R} ^ {d}.
$$

We denote by $X ^ { ( \theta ) }$ any random variable with distribution $p _ { \theta }$ . We make the following assumption on the function $\psi$

$$
\lim _ {| \theta |} \psi (\theta) - 2 \psi \left(\frac {\theta}{2}\right) = + \infty \quad \text { and } \quad \exists \delta > 0, \theta \mapsto \psi (\theta) - \delta | \theta | ^ {2} \text { is   concave. }\tag{\((H_{\delta}^{es})\}
$$

The two functionals to be minimized are

$$
{Q _ {1} (\theta , \xi_ {\alpha} ^ {*})} {:=} {\mathbb {E} \left[ \mathbf {1} _ {\{\varphi (X) > \xi_ {\alpha} ^ {*} \}} e ^ {- \langle \theta , X \rangle + \psi (\theta)} \right]}\tag{45}
$$

$$
Q _ {2} (\mu , \xi_ {\alpha} ^ {*}) := \mathbb {E} \left[ \left(\Psi (\varphi (X)) - \xi_ {\alpha} ^ {*}\right) ^ {2} \mathbf {1} _ {\{\varphi (X) > \xi_ {\alpha} ^ {*} \}} e ^ {- \langle \mu , X \rangle + \psi (\mu)} \right].\tag{46}
$$

According to Proposition 3 in [27] as soon as $\psi$ satisfies $( H _ { \delta } ^ { e s } )$ and that,

$$
\forall \xi \in \mathbb {R}, \forall \theta \in \mathbb {R} ^ {d}, \mathbb {E} [ | X | (1 + \Psi (\varphi (X)) ^ {2}) e ^ {\langle \theta , X \rangle} ] <   + \infty ,\tag{47}
$$

for every $\xi \in \mathbb { R }$ , the functions $Q _ { 1 } ( . , \xi )$ and $Q _ { 2 } ( . , \xi )$ are finite, convex, diferentiable on $\mathbb { R } ^ { d }$ , go to infinity at infinity, so that arg min $Q _ { 1 } ( . , \xi )$ and arg min $Q _ { 2 } ( . , \xi )$ are non empty. Moreover, their gradients are given by

$$
\nabla_ {\theta} Q _ {1} (\theta , \xi) = \mathbb {E} \left[ (\nabla \psi (\theta) - X ^ {(- \theta)}) \mathbf {1} _ {\{\varphi (X ^ {(- \theta)}) > \xi \}} \right] e ^ {\psi (\theta) - \psi (- \theta)}\tag{48}
$$

$$
\nabla_ {\mu} Q _ {2} (\mu , \xi) = \mathbb {E} \left[ (\nabla \psi (\mu) - X ^ {(- \mu)}) (\Psi (\varphi (X ^ {(- \mu)})) - \xi) ^ {2} \mathbf {1} _ {\{\varphi (X ^ {(- \mu)}) > \xi \}} \right] e ^ {\psi (\mu) - \psi (- \mu)}\tag{49}
$$

with $\begin{array} { r } { \nabla \psi ( \theta ) = \frac { \mathbb { E } [ X e ^ { \langle \theta , X \rangle } ] } { \mathbb { E } [ e ^ { \langle \theta , X \rangle } ] } } \end{array}$ . Now, the main result of this section is the following theorem (for more details, we refer to [27] and [13]).

Theorem 4.1. Suppose that $\psi$ satisfies $( H _ { \delta } ^ { e s } )$ and that (A2)<sub>1</sub>, (A3) hold. Assume that (47) is fulfilled and that

$$
\forall x \in \mathbb {R} ^ {d}, | \Psi (\varphi (x)) | \leq C e ^ {\frac {\lambda}{4} | x |} \quad a n d \quad \mathbb {E} [ | X | ^ {2} e ^ {\lambda | X |} ] <   + \infty .
$$

One considers the recursive procedure

$$
Z _ {n} = Z _ {n - 1} - \gamma_ {n} L (Z _ {n - 1}, X _ {n}), n \geq 1, Z _ {0} = (\xi_ {0}, C _ {0}, \theta_ {0}, \mu_ {0})\tag{50}
$$

where $( \gamma _ { n } ) _ { n \geq 1 }$ satisfies the usual step assumption $( A \ : 1 ) , \ : Z _ { n } : = ( \xi _ { n } , C _ { n } , \theta _ { n } , \mu _ { n } )$ and each component of L is defined by

$$
\left\{ \begin{array}{l} L _ {1} \left(\xi_ {n - 1}, \theta_ {n - 1}, X _ {n} ^ {(\theta_ {n - 1})}\right) := e ^ {- \frac {\psi (\theta_ {n - 1}) + \psi (- \theta_ {n - 1})}{2}} \bigg (1 - \frac {1}{1 - \alpha} \mathbf {1} _ {\left\{\varphi (X _ {n} ^ {(\theta_ {n - 1})}) > \xi_ {n - 1} \right\}}   e ^ {\psi (\theta_ {n - 1}) - \left\langle X _ {n} ^ {(\theta_ {n - 1})}, \theta_ {n - 1} \right\rangle} \bigg), \\ L _ {2} \left(\xi_ {n - 1}, C _ {n - 1}, \mu_ {n - 1}, X _ {n} ^ {(\mu_ {n - 1})}\right) := C - \bar {w} (\xi_ {n - 1}, \mu_ {n - 1}, X _ {n} ^ {(\mu_ {n - 1})}), \\ L _ {3} \left(\xi_ {n - 1}, \theta_ {n - 1}, X ^ {(- \theta_ {n - 1})}\right) := \mathbf {1} _ {\left\{\varphi (X ^ {(- \theta_ {n - 1})}) > \xi_ {n - 1} \right\}} (\nabla \psi (\theta_ {n - 1}) - X ^ {(- \theta_ {n - 1})}), \\ L _ {4} \left(\xi_ {n - 1}, \mu_ {n - 1}, X ^ {(- \mu_ {n - 1})}\right) := \frac {e ^ {- \frac {\lambda}{2} \sqrt {d} | \nabla \psi (- \mu_ {n - 1}) |}}{1 + \xi_ {n - 1} ^ {2}} (\Psi (\varphi (X ^ {(- \mu_ {n - 1})})) - \xi_ {n - 1}) ^ {2} \mathbf {1} _ {\left\{\varphi (X ^ {(- \mu_ {n - 1})}) > \xi_ {n - 1} \right\}} \\ \qquad \qquad \qquad \times (\nabla \psi (\mu_ {n - 1}) - X ^ {(- \mu_ {n - 1})}), \end{array} \right.
$$

with w¯(ξ, µ, x) := Ψ(ξ) + 1 <sup>(Ψ(ϕ(x))</sup> − <sup>Ψ(ξ))1</sup> ϕ(x)>ξ <sup>eψ(µ)−hµ,xi.</sup> 1 α

Then, $Z _ { n }$ converges a.s. toward $z ^ { * } : = ( \xi _ { \alpha } ^ { * } , C _ { \alpha } ^ { * } , \theta _ { \alpha } ^ { * } , \mu _ { \alpha } ^ { * } )$ , where $\xi _ { \alpha } ^ { * }$ is a square integrable $\operatorname { V a R } _ { \alpha ^ { - } }$ valued random variable, $C _ { \alpha } ^ { * } = \Psi \mathrm { - } \mathrm { C V a R } _ { \alpha } ( \varphi ( X ) ) , \theta _ { \alpha } ^ { * }$ is a (square integrable) arg min $Q _ { 1 } ( . , \xi _ { \alpha } ^ { * } )$ -valued random vector and $\mu _ { \alpha } ^ { * }$ is a (square integrable) arg min $Q _ { 2 } ( . , \xi _ { \alpha } ^ { * } )$ -valued random vector.

## 4.2 Extension to infinite dimensional setting

In the above sections, we proposed our algorithm in a finite dimensional setting where the value of the loss $L = \varphi ( X )$ is a function of a random vector having values in $\mathbb { R } ^ { d }$ . This is due to the fact that generally the value of a portfolio may depend on a finite number of decisions taken in the past. Thus, the value of the loss at the horizon time $T - t$ may depend on a large number of dates in the past $t _ { 0 } = t < t _ { 1 } < t _ { 2 } , \ldots < t _ { N } = T - t .$ , with $N = 2 5 0$ for a portfolio with time interval $T - t = 1$ year. For instance, if we consider a simple portfolio composed of short positions on 250 calls with a maturity at each $t _ { k }$ and a strike K. The loss at time $t _ { N } = 1$ year can be written:

$$
L = \sum_ {k = 1} ^ {N} e ^ {r (t _ {N} - t _ {k})} (S _ {t _ {k}} - K) _ {+} - e ^ {r t _ {N}} C _ {0} ^ {k},
$$

where $C _ { 0 } ^ { i }$ denotes the price of the call of maturity $t _ { i }$ and strike $K ,$ , with

$$
S _ {t _ {k + 1}} = S _ {t _ {k}} e ^ {(r - \frac {\sigma^ {2}}{2}) (t _ {k + 1} - t _ {k}) + \sigma \sqrt {(t _ {k + 1} - t _ {k})} Z _ {k}}.
$$

So that, $X = Z = ( Z _ { 1 } , . . . , Z _ { 2 5 0 } )$ is a Gaussian vector with $d \ : = \ : 2 5 0 .$ . Consequently, with our above procedure, $\theta _ { n }$ and $\mu _ { n }$ are two random vectors of dimension d and we have to control the growth of each component. If one grows too fast and take too high values, it may provides bad performance and bad estimates of both VaR and CVaR. To circumvent this problem, one can reduce the dimension of the problem by choosing the same shift parameters for several dates, i.e. for instance

$$
\theta_ {n} = (\underbrace {\theta_ {n} ^ {1} , . . , \theta_ {n} ^ {1}} _ {1 0 \text { times}},..., \underbrace {\theta_ {n} ^ {2 5} , . . , \theta_ {n} ^ {2 5}} _ {1 0 \text { times }}).
$$

Now, we can run the IS algorithm for $\theta ^ { 1 } , . . . , \theta ^ { 2 5 }$ so that, we have to deal with a procedure in dimension 25. It is sub-optimal with respect to the procedure in dimension 250 but it is more tractable. Another relevant example is a portfolio composed by only one barrier option, for instance a Down & In Call option

$$
\varphi (X) = (X _ {T} - K) _ {+} \mathbf {1} _ {\left\{\min _ {\{0 \leq t \leq T \}} X _ {t} \leq L \right\}}
$$

where the underlying X is a process solution of the path-dependent SDE

$$
\mathrm{d} X _ {t} = b (X _ {t}) \mathrm{d} t + \sigma (X _ {t}) \mathrm{d} W _ {t}, X _ {0} = x \in \mathbb {R} ^ {d},\tag{51}
$$

$W = ( W _ { t } ) _ { t \in [ 0 , T ] }$ being a standard Brownian motion. A naive approach is to discretize (51) by an Euler-Maruyama scheme $\bar { X } = ( \bar { X } _ { t _ { k } } ) _ { k \in \{ 0 , \ldots , n \} }$

$$
\bar {X} _ {t _ {k + 1}} = \bar {X} _ {t _ {k}} + b (\bar {X} _ {t _ {k}}) (t _ {k + 1} - t _ {k}) + \sigma (\bar {X} _ {t _ {k}}) (W _ {t _ {k + 1}} - W _ {t _ {k}}), \bar {X} _ {0} = x _ {0} \in \mathbb {R}.
$$

This kind of approximation is known to be poor for this kind of options. In this case, our IS parameters θ and $\mu$ are n-dimensional vectors which correspond to the number of steps in the Euler scheme. Now, if you consider a portfolio composed by several barrier options with diferent underlyings, the dimension can increase greatly and becomes an important issue, so that our first IS procedure is no longer acceptable and tractable. To overcome this problem, the idea is to shift the entire distribution of X in (51) thanks to a Girsanov transformation. This last case is analyzed and investigated in [27]. It can be adapted to our framework (see [13] for further developments).

## 5 Numerical examples

For the sake of simplicity, we focus in this section on the finite dimensional setting and on the computation of the regular $\mathrm { C V a R } _ { \alpha } ~ ( \Psi \equiv I d )$ . We first consider the usual Gaussian framework in which the exponential change of measure coincide with the mean translation change of measure. Then we illustrate the algorithm (50) in a simple case.

## 5.1 Gaussian framework

In this setting, $X \sim { \mathcal { N } } ( 0 , I _ { d } )$ and $p$ is given by

$$
p (x) = (2 \pi) ^ {- \frac {d}{2}} e ^ {- \frac {| x | ^ {2}}{2}}, \quad x \in \mathbb {R} ^ {d},
$$

so that (B3) and (B4) are satisfied with $\begin{array} { r } { \rho = \frac { 1 } { 2 } } \end{array}$ and $b = 2$ . In this setting, we already noticed that

$$
\begin{array}{r c l} L _ {3} (\xi , \theta , x) & := & \mathbf {1} _ {\{\varphi (X - \theta) \geq \xi \}} (2 \theta - x), \\ L _ {4} (\xi , \mu , x) & := & \frac {1}{1 + G (- \mu) + \xi^ {2}} (\varphi (X - \mu) - \xi) _ {+} ^ {2} (2 \mu - x). \end{array}
$$

Moreover, we use a stepwise constant sequence $\alpha _ { n }$ that slowly converges toward α as proposed in Section 3.3. We consider three diferent portfolios of options (puts and calls) on 1 and 5 underlying assets (except for the last case). In the third case, we study the behaviour of a portfolio composed by a power plant that produces electricity from gas with short positions in calls on electricity. The assets are modeled as geometric Brownian motions for the first two examples. In the third example, the assets (electricity and gas day-ahead prices) are modeled as exponentials of an Ornstein-Uhlenbeck process. This last derivative is priced using an approximation of Margrabe formulae (see e.g. [29]). We assume an annual risk free interest rate of 5%. In each example, we use three diferent values of the confidence level $\alpha = 9 5 \%$ , 99%, 99.5%, which are specified in the Tables. We use the following test portfolios:

Example 1. Short position in one put with strike $K = 1 1 0$ and maturity $T = 1$ year on a stock with initial value $S _ { 0 } = 1 0 0$ and volatility $\sigma = 2 0 \%$ . The loss is given by

$$
\varphi_ {1} (X) := (K - S _ {T}) _ {+} - e ^ {r T} P _ {0}
$$

with

$$
S _ {T} := S _ {0} e ^ {\left(\left(r - \frac {\sigma^ {2}}{2}\right) T + \sigma \sqrt {T} X\right)}
$$

where $X \sim \mathcal { N } ( 0 , 1 )$ and $P _ { 0 }$ is the initial price at which the put option was sold (it is approximately equal to 10.7). The dimension d of the structural vector X is equal to 1. The numerical results are reported in Table 1.

Example 2. Short positions in 10 calls and 10 puts on each of the five underlying assets, all options having the same maturity 0.25 year. The strikes are set to 130 for calls, to 110 for puts and the initial spot prices to 120. The underlying assets have a volatility of 20% and are assumed to be uncorrelated. The dimension d of the structural vector X is equal to 5. The numerical results are reported in Table 2.

Example 3. Short position in a power plant that produces electricity day by day with a maturity of T = 1 month and 30 long positions in calls on electricity day-ahead price with the same strike $K = 6 0$ . Electricity and gas initial spot prices are $S _ { 0 } ^ { e } = 4 0 ~ \mathbb { \ S / M \mathrm { W h } }$ and $S _ { 0 } ^ { g } \ = \ 3$ \$/MMBTU ( BTU: British Thermal Unit) with a Heat Rate equals $h _ { R } = 1 0$ BTU/kWh and generation costs $C = 5 ~ \mathrm { { ‰ } }$ . The two spot prices have a correlation of $0 . \ 4$ The payof can be written

$$
\varphi_ {3} (X) = \sum_ {k = 1} ^ {3 0} \left(e ^ {r (T - t _ {k})} \left(S _ {t _ {k}} ^ {e} - h _ {R} S _ {t _ {k}} ^ {g} - C\right) _ {+} - P _ {0} ^ {c} e ^ {r T}\right) + \left(e ^ {r T} C _ {0} - e ^ {r (T - t _ {k})} \left(S _ {t _ {k}} ^ {e} - K\right) _ {+}\right)
$$

where $P _ { 0 } ^ { c }$ is a proxy of the price of the option on the power plant and is equal to $1 \it { 4 9 . 9 }$ and $C _ { 0 }$ is the price of the call options which is equal to 3.8. This is a sum of spark spread options where we decide to exchange gas and electricity each day during one month. The dimension d of the structural vector X is equal to 60. The numerical results are reported in Table 3.

The results displayed in the following tables correspond to the VaR, the CVaR and the variance reduction ratios estimations for both VaR and CVaR procedure using a number of steps specified in the first column, still for the same three levels of α. The variance ratios correspond to the ratio of an estimation of the asymptotic variance using the averaging procedure of (16) divided by an estimation of the asymptotic variance using the averaging procedure of (36): $\mathrm { \Delta V R } _ { \mathrm { V a R } }$ corresponds to the variance reduction ratio of the VaR estimate and $\mathrm { \Delta V R _ { C V a R } }$ corresponds to the variance reduction ratio of the CVaR estimate. The results emphasize that the IS procedure yields a very significant, sometimes huge variance reduction especially when α is closed to 1. In the three examples, we define the step sequence by $\begin{array} { r } { \gamma _ { n } = \frac { 1 } { n ^ { \beta } + 1 0 0 } } \end{array}$ where $\textstyle { \beta = { \frac { 3 } { 4 } } }$

Table 1: Example 1 Results

<table><tr><td>Number of steps</td><td> $\alpha$ </td><td>VaR</td><td>CVaR</td><td> $VR_{VaR}$ </td><td> $VR_{CVaR}$ </td></tr><tr><td rowspan="3">10 000</td><td>95%</td><td>24.6</td><td>29.9</td><td>5.5</td><td>30.5</td></tr><tr><td>99%</td><td>34.4</td><td>37.5</td><td>11.1</td><td>125.3</td></tr><tr><td>99.5%</td><td>37.8</td><td>41.4</td><td>13.4</td><td>192.9</td></tr><tr><td rowspan="3">100 000</td><td>95%</td><td>24.6</td><td>30.4</td><td>6.6</td><td>32.2</td></tr><tr><td>99%</td><td>34.2</td><td>37.9</td><td>11.5</td><td>127.9</td></tr><tr><td>99.5%</td><td>37.3</td><td>40.7</td><td>15.1</td><td>185</td></tr><tr><td rowspan="3">500 000</td><td>95%</td><td>24.6</td><td>30.3</td><td>7.7</td><td>31.3</td></tr><tr><td>99%</td><td>34.2</td><td>38</td><td>14.6</td><td>118.4</td></tr><tr><td>99.5%</td><td>37.3</td><td>40.5</td><td>15.5</td><td>184</td></tr></table>

Table 2: Example 2 Results

<table><tr><td>Number of steps</td><td> $\alpha$ </td><td>VaR</td><td>CVaR</td><td>VRVaR</td><td>VRCVaR</td></tr><tr><td rowspan="3">10 000</td><td>95%</td><td>339</td><td>440.5</td><td>6.5</td><td>14.9</td></tr><tr><td>99%</td><td>493.1</td><td>561.4</td><td>10.1</td><td>24.3</td></tr><tr><td>99.5%</td><td>540.1</td><td>606.4</td><td>18.2</td><td>37.9</td></tr><tr><td rowspan="3">100 000</td><td>95%</td><td>349.8</td><td>439.7</td><td>6.7</td><td>17</td></tr><tr><td>99%</td><td>495.7</td><td>563.8</td><td>11.3</td><td>28.6</td></tr><tr><td>99.5%</td><td>544.8</td><td>607.8</td><td>18.9</td><td>40.3</td></tr><tr><td rowspan="3">500 000</td><td>95%</td><td>352.4</td><td>439.6</td><td>6.8</td><td>17.3</td></tr><tr><td>99%</td><td>495.2</td><td>563</td><td>11.1</td><td>27.7</td></tr><tr><td>99.5%</td><td>545.3</td><td>608.4</td><td>19.2</td><td>37</td></tr></table>

Table 3: Example 3 Results

<table><tr><td>Number of steps</td><td> $\alpha$ </td><td>VaR</td><td>CVaR</td><td> $VR_{VaR}$ </td><td> $VR_{CVaR}$ </td></tr><tr><td rowspan="3">10 000</td><td>95%</td><td>115.7</td><td>150.5</td><td>3.4</td><td>6.8</td></tr><tr><td>99%</td><td>169.4</td><td>196</td><td>8.4</td><td>12.9</td></tr><tr><td>99.5%</td><td>186.3</td><td>213.2</td><td>13.5</td><td>20.3</td></tr><tr><td rowspan="3">100 000</td><td>95%</td><td>118.7</td><td>150.5</td><td>4.5</td><td>8.7</td></tr><tr><td>99%</td><td>169.4</td><td>195.4</td><td>12.6</td><td>17.5</td></tr><tr><td>99.5%</td><td>188.8</td><td>212.9</td><td>15.6</td><td>29.5</td></tr><tr><td rowspan="3">500 000</td><td>95%</td><td>119.2</td><td>150.4</td><td>5</td><td>9.2</td></tr><tr><td>99%</td><td>169.8</td><td>195.7</td><td>13.1</td><td>18.6</td></tr><tr><td>99.5%</td><td>188.7</td><td>212.8</td><td>17</td><td>29</td></tr></table>

## 5.2 Esscher transform: the NIG distribution

Now, we consider a simple case of portfolio composed by a long position on a Call option with strike $K = 0 . 6$ and maturity $T = 1$ year, where the underlying is $e ^ { X _ { T } } \left( X _ { 0 } = 0 \right)$ , where $X _ { T }$ is a Normal Inverse Gaussian (NIG) variable, $X _ { T } \sim \operatorname { N I G } ( \alpha , \beta , \delta , \mu ) , \alpha > 0 , | \beta | \leq \alpha , \delta > 0 , \mu \in \mathbb { R }$ . Its density is given by

$$
p _ {X _ {T}} (x, \alpha , \beta , \delta , \mu) := \frac {\alpha \delta K _ {1} (\alpha \sqrt {\delta^ {2} + (x - \mu) ^ {2}})}{\pi \sqrt {\delta^ {2} + (x - \mu) ^ {2}}} e ^ {\delta \gamma + \beta (x - \mu)},
$$

where $K _ { 1 }$ is a modified Bessel function of the second kind and $\gamma = \sqrt { \alpha ^ { 2 } - \beta ^ { 2 } }$ . Note that the generating function of the NIG distribution is given by

$$
\psi (\theta) = \mu \theta + \delta (\gamma - \sqrt {\alpha^ {2} - (\beta + \theta) ^ {2}}),
$$

and is not well defined for every $\theta \in \mathbb { R }$ , so that we change the algorithm parametrization (see section 4.3 of [27]). The loss of the portfolio can be written $L = \varphi _ { 4 } ( X _ { T } ) = 5 0 ( e ^ { X _ { T } } - K ) _ { + } - e ^ { r T } C _ { 0 }$ Note that the price $C _ { 0 }$ is computed by a crude Monte Carlo and is approximately equal to 42. The parameters of the NIG random variable $X _ { T }$ are $\alpha = 2 . 0 , ~ \beta = 0 . 2 , ~ \delta = 0 . 8 , ~ \mu = 0 . 0 4$ . We want to compare the variance reduction achieved by the translation of the mean (see section 3.1) and the one achieved by the Esscher Transform (see section 4.1). In the Robbins-Monro procedure, we define the step sequence by $\begin{array} { r } { \gamma _ { n } = \frac { 1 } { n ^ { \beta } + 1 0 0 } } \end{array}$ where $\textstyle { \beta = { \frac { 3 } { 4 } } }$

✄ Translation case. The functions $L _ { 3 }$ and $L _ { 4 }$ of the IS procedure are defined by:

$$
\begin{array}{r c l} L _ {3} (\xi , \theta , X) & := & e ^ {- 2 | \theta |} \mathbf {1} _ {\varphi (X - \theta)} \frac {p ^ {\prime} (X - 2 \theta)}{p (X)} \left(\frac {p (X - \theta)}{p (X - 2 \theta)}\right) ^ {2}, \\ L _ {4} (\xi , \mu , X) & := & \frac {e ^ {- 2 | \mu |}}{1 + G (- \mu) + \xi^ {2}} (\varphi (X - \mu) - \xi) _ {+} ^ {2} \frac {p ^ {\prime} (X - 2 \mu)}{p (X)} \left(\frac {p (X - \mu)}{p (X - 2 \mu)}\right) ^ {2}, \end{array}
$$

where $p ^ { \prime }$ is easily obtained using the relation on the modified Bessel function $\begin{array} { r } { K _ { 1 } ^ { \prime } ( x ) = \frac { 1 } { x } K _ { 1 } ( x ) - } \end{array}$ $K _ { 2 } ( x )$

✄ Esscher Transform. In this approach, the functions $L _ { 3 }$ and $L _ { 4 }$ are defined by

$$
L _ {3} (\xi , \theta , X) := \mathbf {1} _ {\varphi (X ^ {(- \theta)}) \geq \xi} (\nabla \psi (\theta) - X ^ {(- \theta)}),
$$

$$
{L _ {4} (\xi , \mu , X)} {:=} {\frac {e ^ {- | \mu |}}{1 + \xi^ {2}} (\varphi (X ^ {(- \mu)}) - \xi) _ {+} ^ {2} (\nabla \psi (\mu) - X ^ {(- \mu)}),}
$$

where $X ^ { ( \pm \theta ) } \sim \mathrm { N I G } ( \alpha , \beta \pm \theta , \delta , \mu )$

Table 4 compares the variance reduction ratios of the $\operatorname { V a R } _ { \alpha }$ and $\mathrm { C V a R } _ { \alpha }$ algorithms achieved by the translation of the mean $( \mathrm { V R } _ { V a R } ^ { t r }$ and $\mathrm { V R } _ { C V a R } ^ { t r } )$ and the one achieved by the Esscher Transform $( \mathrm { V R } _ { V a R } ^ { e s }$ and $\mathrm { V R } _ { C V a R } ^ { e s } )$

Table 4: Example 4 Results

<table><tr><td>Number of steps</td><td> $\alpha$ </td><td>VaR</td><td>CVaR</td><td> $VR_{VaR}^{tr}$ </td><td> $VR_{CVaR}^{tr}$ </td><td> $VR_{VaR}^{es}$ </td><td> $VR_{CVaR}^{es}$ </td></tr><tr><td rowspan="3">10 000</td><td>95%</td><td>85.8</td><td>215.7</td><td>5</td><td>10</td><td>4.2</td><td>58.8</td></tr><tr><td>99%</td><td>217</td><td>518</td><td>6</td><td>12</td><td>8</td><td>60</td></tr><tr><td>99.5%</td><td>304</td><td>748</td><td>8</td><td>25</td><td>8.9</td><td>110</td></tr><tr><td rowspan="3">100 000</td><td>95%</td><td>87.2</td><td>215.1</td><td>5</td><td>12</td><td>4.5</td><td>60</td></tr><tr><td>99%</td><td>218</td><td>521</td><td>5</td><td>12</td><td>8.2</td><td>70</td></tr><tr><td>99.5%</td><td>303.5</td><td>747.8</td><td>7</td><td>30</td><td>12</td><td>100</td></tr><tr><td rowspan="3">500 000</td><td>95%</td><td>87.9</td><td>215.6</td><td>5</td><td>9</td><td>5</td><td>57</td></tr><tr><td>99%</td><td>227</td><td>518.9</td><td>5.5</td><td>11.8</td><td>11.5</td><td>68</td></tr><tr><td>99.5%</td><td>312.8</td><td>741.8</td><td>6</td><td>31</td><td>10</td><td>123</td></tr></table>

The IS procedure is very eficient when $\mathbb { P } ( \varphi ( X ) \geq \xi _ { \alpha } ^ { * } ) = 1 - \alpha$ is close to zero and becomes more and more eficient as α grows to 1. Even for the complex portfolio considered in Example $^ { 3 , }$ where X is a Gaussian vector with $d = 6 0$ , it is possible to achieve a great variance reduction for both $\operatorname { V a R } _ { \alpha }$ and $\mathrm { C V a R } _ { \alpha }$

We observed that IS based on Esscher transform is well adapted to distributions with heavy tails $( i . e ,$ . heavier tails than the normal distribution). It is therefore suitable when large values are more frequent than for the normal distribution, as it is the case when the vector X is a NIG random variable. Indeed, in this setting, the IS parameters modify the parameter $\beta$ which controls the asymmetric shape of the NIG distribution. We think that the IS procedure by Esscher transform outperforms the IS procedure by mean translation when the IS parameter impacts on the symmetry of the distribution.

## 6 Concluding remarks.

In this article, we propose a recursive procedure to compute eficiently the Value-at-Risk and the Conditional Value-at-Risk using the same innovation for both procedures. In our approach, for a given risk level $\alpha ,$ the $\operatorname { V a R } _ { \alpha }$ and the $\mathrm { C V a R } _ { \alpha }$ are estimated simultaneously by a regular RM algorithm. Ruppert and Polyak’s averaging principle provides an asymptotically eficient procedure. The estimates satisfy a Gaussian CLT. However, due to the slow convergence of the global procedure since we are interested in rare events, the regular version of this algorithm cannot be used in practice. To speed-up and thus greatly reduce the number of scenarios, we devise an unconstrained adaptive IS procedure. The resulting procedure provides estimates that satisfy a CLT with minimal variances. To optimize the move to the critical risk area, the risk level $\alpha$ can be temporarily replaced by a slowly increasing level $\alpha _ { n }$ (stepwise constant in practice) converging to $\alpha .$ This produces a VaR companion procedure $( \hat { \xi } _ { n } ) _ { n \geq 1 }$ that controls the IS change of measure parameters $( { \hat { \theta } } _ { n } , { \hat { \mu } } _ { n } )$ Numerically speaking, the resulting procedure converges eficiently and can drastically reduce the variance. It is possible to extend the methods to portfolio whose losses depend on a general difusion process, using Girsanov transform to introduce a potentially infinite dimensional variance reducer. Finally, we aim at extending the method by implementing low-discrepancy sequences in our procedure instead of pseudo-random numbers. Preliminary numerical experiments showed a significant improvement of the convergence rate . This also raises interesting theoretical problems.

See [25] for some first theoretical results in that direction in a one-dimensional framework and [13] for further developments in higher dimensional setting.

## References

[1] Arouna B. (2004). Adaptative Monte Carlo method, a variance reduction technique, Monte Carlo Methods and Appl., 10(1), p.1-24.

[2] Artzner P., Delbaen F., Eber J.-M. and Heath D. (1999). Coherent measures of risk, Math. Finance, 9, p.203-228.

[3] Arouna B., Bardou O. (2004). Eficient variance reduction for functionals of difusions by relative entropy, technical report, CERMICS-ENPC (France).

[4] Benveniste A., M´etivier M. and Priouret P. (1987). Algorithmes adaptatifs et approximations stochastiques : th´eorie et applications l’identification, au traitement du signal et la reconnaissance des formes, Applications des Math´ematiques, Masson, Paris, 367 p.

[5] Borkar V.S. (1997). Stochastic approximation with two time scales, Systems Control Lett., 29, p.291-294.

[6] Bouton C. (1998). Approximation gaussienne d’algorithmes stochastiques, Annales de l’I.H.P., section B, 24(1), p.131-155.

[7] Britten-Jones M. and Schaefer S.M. (1999). Non linear Value-at-Risk, European Finance Review, 2, p.161-187.

[8] Dufie D. and Pan J. (2001). Analytical Value-At-Risk with Jumps and Credit Risk, Finance and Stochastics, 5(2), p.155-180.

[9] Duflo M. (1997). Iterative random models, transl. from French, Springer-Verlag, 385p.

[10] Duflo M. (1996). Algorithmes Stochastiques, Springer, Berlin, 319p.

[11] Dufresne D. and V´azquez-Abad F.J. (1998). Accelerated simulation for pricing Asian options. Proceedings of the 1998 Winter Simulation Conference. Piscataway, NJ, IEEE Press, p.1493- 1500.

[12] Eglof D. and Leippold M. (2007). Quantile estimation with adaptive importance sampling, Electronic copy: http://ssrn.com/abstract=1002631.

[13] Frikha N., PhD thesis, in progress.

[14] Fu M.C. and Su Y. (2000). Optimal importance sampling in securities pricing, Journal of Computational Finance, 5(4), p.27-50.

[15] Glasserman P. and Heidelberger P. and Shahabuddin P. (2002). Portfolio Value-at-Risk with Heavy-Tailed Risk Factors, Mathematical Finance, 12, p.239-270.

[16] Glasserman P. and Heidelberger P. and Shahabuddin P. (1999). Variance reduction techniques for estimating Value-at-Risk, Management Science, 47, p.1349-1364.

[17] Glasserman P. and Heidelberger P. and Shahabuddin P. (1999). Importance Sampling and Stratification for Value-at-Risk, Computational Finance 1999, MIT press, p.7-24.

[18] Glasserman P. and Wang Y. (1997). Counterexamples in importance sampling for large deviation probabilities, Annals of Applied Probability, 7(3), p.731-746.

[19] Juditsky A.B. and Polyak B.T. (1992). Acceleration of Stochastic Approximation by Averaging, Journal on Control and optimization, 30(4), p.838-855.

[20] Kawai R. (2008). Optimal importance sampling parameter search for L´evy Processes via stochastic approximation, SIAM Journal on Numerical Analysis, 47(1), p.293-307.

[21] Konda V.R. and Tsitsiklis J.N. (2004). Convergence rate of linear two-time-scale stochastic approximation, Ann. Appl. Probab., 14(2), p.796-819.

[22] Kroese D. P. and Rubinstein R. Y. (2004). The Cross-Entropy Method: A Unified Approach to Combinatorial Optimization, Monte Carlo Simulation and Machine Learning, Springer, New York, 300 p.

[23] Kushner H.J. and Clark D.S. (1978). Stochastic Approximation Methods for Constrained and Unconstrained Systems, Springer, New York, 276 p.

[24] Kushner H.J. and Yin G.G. (1993). Stochastic Approximation with averaging of the iterates: Optimal asymptotic rate of convergence for general processes, Springer, New York, 31, p.1045- 1062

[25] Lapeyre B., Pag\`es G., Sab K. (1990). Sequences with low discrepancy. Generalization and application to Robbins-Monro algorithm, Statistics, 21(2), 251-272.

[26] Lelong J. (2007). Algorithmes stochastiques et Options parisiennes, PhD thesis ENPC, (France).

[27] Lemaire V. and Pag\`es G. (2008). Unconstrained Recursive Importance Sampling, To appear in Annals of Applied Probability.

[28] Ljung L. (1978). Strong convergence of a stochastic approximation algorithm, Ann. Statist., 6(3), p.680-696.

[29] Margrabe W. (1978). The Value of an Option to Exchange One Asset for Another. Journal of Finance, 33(1), p.177-186.

[30] Mokkadem A. and Pelletier M. (2006). Convergence rate and averaging of non linear two-timescale stochastic approximation algorithms, The Annals of Applied Probability, 16(3), p.1671- 1702.

[31] Pflug G.Ch. (2000). Some remarks on the value-at-risk and the conditional value-at-risk. In: Uryasev S. ed., Probabilistic Constrained Optimization: Methodology and Applications, Kluwer Academic Publishers, Dordrecht.

[32] Rockafellar R.T. and Uryasev S. (2002). Conditional Value-at-Risk for general loss distributions, Journal of Banking and Finance, 26(7), p.1443-1471.

[33] Rockafellar R.T. and Uryasev S. (2000). Optimization of CVaR, Journal of Risk, 2(3), p.21-41.

[34] Rouvinez C. (1997). Going Greek with VaR, Risk, 10(2), p.57-65.

[35] Ruppert D. (1991). Stochastic Approximation. Handbook of Sequential Analysis, B. K. Ghosh and P.K. Sen, eds, p.503-529. Dekker, New York.

[37] Uryasev S. (2000). Conditional Value-at-Risk: Optimization Algorithms and Applications, Financial Engineering News, 14, p.1-5.

[36] Serfling R. J. (1980). Approximation Theorems for Mathematical Statistics, Wiley, New York.