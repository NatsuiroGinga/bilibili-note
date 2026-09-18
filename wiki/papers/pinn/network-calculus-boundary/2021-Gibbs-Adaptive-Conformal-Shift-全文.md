---
title: "2021-Gibbs-Adaptive-Conformal-Shift"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/network-calculus-boundary/2021-Gibbs-Adaptive-Conformal-Shift.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Adaptive Conformal Inference Under Distribution Shift

Isaac Gibbs Department of Statistics Stanford University igibbs@stanford.edu

Emmanuel J. Candès Department of Statistics Department of Mathematics Stanford University candes@stanford.edu

## Abstract

We develop methods for forming prediction sets in an online setting where the data generating distribution is allowed to vary over time in an unknown fashion. Our framework builds on ideas from conformal inference to provide a general wrapper that can be combined with any black box method that produces point predictions of the unseen label or estimated quantiles of its distribution. While previous conformal inference methods rely on the assumption that the data points are exchangeable, our adaptive approach provably achieves the desired coverage frequency over long-time intervals irrespective of the true data generating process. We accomplish this by modelling the distribution shift as a learning problem in a single parameter whose optimal value is varying over time and must be continuously re-estimated. We test our method, adaptive conformal inference, on two real world datasets and find that its predictions are robust to visible and significant distribution shifts.

## 1 Introduction

Machine learning algorithms are increasingly being employed in high stakes decision making processes. For instance, deep neural networks are currently being used in self-driving cars to detect nearby objects [2] and parole decisions are being made with the assistance of complex models that combine over a hundred features [1]. As the popularity of black box methods and the cost of making wrong decisions grow it is crucial that we develop tools to quantify the uncertainty of their predictions.

In this paper we develop methods for constructing prediction sets that are guaranteed to contain the target label with high probability. We focus specifically on an online learning setting in which we observe covariate-response pairs $\{ ( X _ { t } , Y _ { t } ) \} _ { t \in \mathbb { N } } \subseteq \mathbb { R } ^ { d } \times \mathbf { \bar { \mathbb { R } } }$ in a sequential fashion. At each time step $t \in \mathbb { N }$ we are tasked with using the previously observed data $\{ ( X _ { r } , \bar { Y } _ { r } ) \} _ { 1 \leq r \leq t - 1 }$ along with the new covariates, $X _ { t } ,$ , to form a prediction set $\hat { C } _ { t }$ for $Y _ { t }$ . Then, given a target coverage level $\alpha \in ( 0 , 1 )$ our generic goal is to guarantee that $Y _ { t }$ belongs to $\hat { C } _ { t }$ at least $1 0 0 ( 1 - \alpha ) \%$ of the time.

Perhaps the most powerful and flexible tools for solving this problem come from conformal inference [see e.g. 34, 16, 32, 22, 31, 15, 3] . This framework provides a generic methodology for transforming the outputs of any black box prediction algorithm into a prediction set. The generality of this approach has facilitated the development of a large suite of conformal methods, each specialized to a specific prediction problem of interest [e.g. 30, 11, 23, 8, 24, 21]. With only minor exceptions all of these algorithms share the same common guarantee that if the training and test data are exchangeable, then the prediction set has valid marginal coverage $\mathbb { P } ( Y _ { t } \in \hat { C } _ { t } ) = 1 - \alpha$

While exchangeability is a common assumption, there are many real-world applications in which we do not expect the marginal distribution of $( X _ { t } , Y _ { t } )$ to be stationary. For example, in finance and economics market behaviour can shift drastically in response to new legislation or major world events. Alternatively, the distribution of $( X _ { t } , Y _ { t } )$ may change as we deploy our prediction model in new environments. This paper develops adaptive conformal inference $\bar { ( \mathrm { A C I ) } }$ , a method for forming prediction sets that are robust to changes in the marginal distribution of the data. Our approach is both simple, in that it requires only the tracking of a single parameter that models the shift, and general as it can be combined with any modern machine learning algorithm that produces point predictions or estimated quantiles for the response. We show that over long time intervals ACI achieves the target coverage frequency without any assumptions on the data-generating distribution. Moreover, when the distribution shift is small and the prediction algorithm takes a certain simple form we show that ACI will additionally obtain approximate marginal coverage at most time steps.

## 1.1 Conformal inference

Suppose we are given a fitted regression model for predicting the value of $Y$ from $X$ . Let $y$ be a candidate value for $Y _ { t } .$ . To determine if y is a reasonable estimate of $Y _ { t } .$ , we define a conformity score $S ( X , Y )$ that measures how well the value y conforms with the predictions of our fitted model. For example, if our regression model produces point predictions ${ \hat { \mu } } ( { \bar { X } } )$ then we could use a conformity score that measures the distance between $\hat { \mu } ( X _ { t } )$ and $y .$ . One such example is

$$
S (X _ {t}, y) = | \hat {\mu} (X _ {t}) - y |.
$$

Alternatively, suppose our regression model outputs estimates ${ \hat { q } } ( X ; p )$ of the $p \mathrm { t h }$ quantile of the distribution of $\dot { Y | \bar { X } }$ . Then, we could use the method of conformal quantile regression (CQR) [28], which examines the signed distance between $y$ and fitted upper and lower quantiles through the score

$$
S (X _ {t}, y) = \max \{\hat {q} (X _ {t}; \alpha / 2) - y, y - \hat {q} (X _ {t}; 1 - \alpha / 2) \}.
$$

Regardless of what conformity score is chosen the key issue is to determine how small $S ( X _ { t } , y )$ should be in order to accept y as a reasonable prediction for $Y _ { t }$ . Assume we have a calibration set $\mathcal { D } _ { \mathrm { c a l } } \subseteq \{ ( X _ { r } , Y _ { r } ) \} _ { 1 \leq r \leq t - 1 }$ that is different from the data that was used to fit the regression model. Using this calibration set we define the fitted quantiles of the conformity scores to be

$$
\hat {Q} (p) := \inf \left\{s: \left(\frac {1}{| \mathcal {D} _ {\mathrm{cal}} |} \sum_ {(X _ {r}, Y _ {r}) \in \mathcal {D} _ {\mathrm{cal}}} \mathbb {1} _ {\{S (X _ {r}, Y _ {r}) \leq s \}}\right) \geq p \right\},\tag{1}
$$

and say that $y$ is a reasonable prediction for $Y _ { t }$ if $S ( X _ { t } , y ) \leq \hat { Q } ( 1 - \alpha )$

The crucial observation is that if the data $\mathcal { D } _ { \operatorname { c a l } } \cup \{ ( X _ { t } , Y _ { t } ) \}$ are exchangeable and we break ties uniformly at random then the rank of $S ( X _ { t } , Y _ { t } )$ amongst the points $\{ \bar { S } ( X _ { r } , Y _ { r } ) \} _ { ( X _ { r } , Y _ { r } ) \in \mathcal { D } _ { \mathrm { c a l } } } \cup$ $\{ S ( X _ { t } , Y _ { t } ) \}$ will be uniform. Therefore,

$$
\mathbb {P} (S (X _ {t}, Y _ {t}) \leq \hat {Q} (1 - \alpha)) = \frac {\lceil | \mathcal {D} _ {\mathrm{cal}} | (1 - \alpha) \rceil}{| \mathcal {D} _ {\mathrm{cal}} | + 1}.
$$

Thus, defining our prediction set to be $\hat { C } _ { t } : = \{ y : S ( X _ { t } , y ) \leq \hat { Q } ( 1 - \alpha ) \}$ } gives the marginal coverage guarantee

$$
\mathbb {P} (Y _ {t} \in \hat {C} _ {t}) = \mathbb {P} (S (X _ {t}, Y _ {t}) \leq \hat {Q} (1 - \alpha)) = \frac {\lceil | \mathcal {D} _ {\mathrm{cal}} | (1 - \alpha) \rceil}{| \mathcal {D} _ {\mathrm{cal}} | + 1}.
$$

By introducing additional randomization this generic procedure can be altered slightly to produce a set $\hat { C } _ { t }$ that satisfies the exact marginal coverage guarantee $\mathbb { P } ( Y _ { t } \in \hat { C } _ { t } ) = 1 - \alpha \left[ 3 4 \right]$ . For the purposes of this paper this adjustment is not critical and so we omit the details here. Additionally, we remark that the method outlined above is often referred to as split or inductive conformal inference [27, 34, 26]. This refers to the fact that we have split the observed data between a training set used to fit the regression model and a withheld calibration set. The adaptive conformal inference method developed in this article can also be easily adjusted to work with full conformal inference in which data splitting is avoided at the cost of greater computational resources [34].

## 2 Adapting conformal inference to distribution shifts

Up until this point we have been working with a single score function $S ( \cdot )$ and quantile function ${ \hat { Q } } ( \cdot )$ In the general case where the distribution of the data is shifting over time both these functions should be regularly re-estimated to align with the most recent observations. Therefore, we assume that at each time t we are given a fitted score function $S _ { t } ( \cdot )$ and corresponding quantile function $\hat { Q } _ { t } ( \cdot )$ . We define the realized miscoverage rate of the prediction set $\hat { C } _ { t } ( \alpha ) : = \{ y : S _ { t } ( X _ { t } , y ) \leq \hat { Q } _ { t } ( 1 - \alpha ) \}$ as

$$
M _ {t} (\alpha) := \mathbb {P} (S _ {t} (X _ {t}, Y _ {t}) > \hat {Q} _ {t} (1 - \alpha)),
$$

where the probability is over the test point $( X _ { t } , Y _ { t } )$ as well as the data used to fit $S _ { t } ( \cdot )$ and $\hat { Q } _ { t } ( \cdot )$

Now, since the distribution generating the data is non-stationary we do not expect $M _ { t } ( \alpha )$ to be equal, or even close $\mathrm { t o } , \alpha .$ . Even so, we can still postulate that if the conformity scores used to fit $\hat { Q } _ { t } ( \cdot )$ cover the bulk of the distribution of $S _ { t } ( X _ { t } , Y _ { t } )$ then there may be an alternative value $\alpha _ { t } ^ { * } \in [ 0 , 1 ]$ such that $M _ { t } ( \alpha _ { t } ^ { * } ) \cong \alpha$ . More rigorously, assume that with probability one, $\hat { Q } _ { t } ( \cdot )$ is continuous, non-decreasing and such that $\hat { Q } _ { t } ( 0 ) = - \infty$ and $\hat { Q } _ { t } ( 1 ) = \infty$ . This does not hold for the split conformal quantile functions defined in (1), but in the case where there are no ties amongst the conformity scores we can adjust our definition to guarantee this by smoothing over the jump discontinuities in ${ \hat { Q } } ( \cdot )$ . Then, $M _ { t } ( \cdot )$ will be non-decreasing on [0, 1] with $M _ { t } ( 0 ) = \bar { 0 }$ and $M _ { t } ( \bar { 1 } ) = 1$ and so we may define

$$
\alpha_ {t} ^ {*} := \sup \{\beta \in [ 0, 1 ]: M _ {t} (\beta) \leq \alpha \}.
$$

Moreover, if we additionally assume that

$$
\mathbb {P} (S _ {t} (X _ {t}, Y _ {t}) = \hat {Q} _ {t} (1 - \alpha_ {t} ^ {*})) = 0,
$$

then we will have that $M _ { t } ( \alpha _ { t } ^ { * } ) = \alpha$ . So, in particular we find that by correctly calibrating the argument to $\hat { Q } _ { t } ( \cdot )$ we can achieve either approximate or exact marginal coverage.

To perform this calibration we will use a simple online update. This update proceeds by examining the empirical miscoverage frequency of the previous prediction sets and then decreasing (resp. increasing) our estimate of $\alpha _ { t } ^ { * }$ if the prediction sets were historically under-covering (resp. over-covering) $Y _ { t }$ . In particular, let $\alpha _ { 1 }$ denote our initial estimate (in our experiments we will choose $\alpha _ { 1 } = \alpha )$ . Recursively define the sequence of miscoverage events

$$
\operatorname{err} _ {t} := \left\{ \begin{array}{l} 1, \text {   if   } Y _ {t} \notin \hat {C} _ {t} (\alpha_ {t}), \\ 0, \text {   otherwise }, \end{array} \right. \quad \text { where   } \hat {C} _ {t} (\alpha_ {t}) := \{y: S _ {t} (X _ {t}, y) \leq \hat {Q} _ {t} (1 - \alpha_ {t}) \}.
$$

Then, fixing a step size parameter $\gamma > 0$ we consider the simple online update

$$
\alpha_ {t + 1} := \alpha_ {t} + \gamma (\alpha - \operatorname{err} _ {t}).\tag{2}
$$

We refer to this algorithm as adaptive conformal inference. Here, $\operatorname { e r r } _ { t }$ plays the role of our estimate of the historical miscoverage frequency. A natural alternative to this is the update

$$
\alpha_ {t + 1} = \alpha_ {t} + \gamma \left(\alpha - \sum_ {s = 1} ^ {t} w _ {s} \mathbf {e r r} _ {s}\right),\tag{3}
$$

where $\{ w _ { s } \} _ { 1 \leq s \leq t } \subseteq [ 0 , 1 ]$ is a sequence of increasing weights with $\textstyle \sum _ { s = 1 } ^ { t } w _ { s } = 1$ . This update has the appeal of more directly evaluating the recent empirical miscoverage frequency when deciding whether or not to lower or raise $\alpha _ { t }$ . In practice, we find that (2) and (3) produce almost identical results. For example, in Section ${ \mathrm { A } } . 3$ in the Appendix we show some sample trajectories for $\alpha _ { t }$ obtained using the update (3) with

$$
w _ {s} := \frac {0 . 9 5 ^ {t - s}}{\sum_ {s ^ {\prime} = 1} ^ {t} 0 . 9 5 ^ {t - s ^ {\prime}}}.
$$

We find that these trajectories are very similar to those produced by (2). The main difference is that the trajectories obtained with (3) are smoother with less local variation in $\alpha _ { t } .$ In the remainder of this article we will focus on (2) for simplicity.

## 2.1 Choosing the step size

The choice of $\dot { \mathbf { \zeta } } \gamma$ gives a tradeoff between adaptability and stability. While raising the value of $\gamma$ will make the method more adaptive to observed distribution shifts, it will also induce greater volatility in the value of $\alpha _ { t }$ . In practice, large fluctuations in $\alpha _ { t }$ may be undesirable as it allows the method to oscillate between outputting small conservative and large anti-conservative prediction sets.

In Theorem 4.2 we give an upper bound on $( M _ { t } ( \alpha _ { t } ) - \alpha ) ^ { 2 }$ that is optimized by choosing γ proportional to $\sqrt { \vert \alpha _ { t + 1 } ^ { * } - \alpha _ { t } ^ { * } \vert }$ . While not directly applicable in practice, this result supports the intuition that in environments with greater distributional shift the algorithm needs to be more adapatable and thus $\gamma$ should be chosen to be larger. In our experiments we will take $\gamma = 0 . 0 0 5$ . This value was chosen because it was found to give relatively stable trajectories for $\alpha _ { t }$ while still being sufficiently large as to allow $\alpha _ { t }$ to adapt to observed shifts. In agreement with the general principles outlined above we found that larger values of $\gamma$ also successfully protect against distribution shifts, while taking $\gamma$ to be too small causes adaptive conformal inference to perform similar to non-adaptive methods that hold $\alpha _ { t } = \alpha$ constant across time.

## 2.2 Real data example: predicting market volatility

We apply ACI to the prediction of market volatility. Let $\{ P _ { t } \} _ { 1 \leq t \leq T }$ denote a sequence of daily open prices for a stock. For all $t \geq 2 ,$ , define the return $R _ { t } : = ( \bar { P } _ { t } \bar { - } \bar { P } _ { t - 1 } ) / P _ { t - 1 }$ and realized volatility $\dot { V } _ { t } = R _ { t } ^ { 2 }$ . Our goal is to use the previously observed returns $X _ { t } : = \{ R _ { s } \} _ { 1 \leq s \leq t - 1 }$ to form prediction sets for $Y _ { t } : = V _ { t }$ . More sophisticated financial models might augment $X _ { i }$ <sub>t</sub> with additional market covariates (available to the analyst at time $t - 1 )$ . As the primary purpose of this section is to illustrate adaptive conformal inference we work with only a simple prediction method.

We start off by forming point predictions using $\mathrm { { a G A R C H } ( 1 , 1 ) }$ model [4]. This method assumes that $R _ { t } = \sigma _ { t } \epsilon _ { t }$ with $\epsilon _ { 2 } , \ldots , \epsilon _ { T }$ taken to be i.i.d. $\check { \mathcal { N } } ( 0 , 1 )$ and $\sigma _ { t }$ satisfying the recursive update

$$
\sigma_ {t} ^ {2} = \omega + \tau V _ {t - 1} + \beta \sigma_ {t - 1} ^ {2}.
$$

This is a common approach used for forecasting volatility in economics. In practice, shifting market dynamics can cause the predictions of this model to become inaccurate over large time periods. Thus, when forming point predictions we fit the model using only the last 1250 trading days (i.e. approximately 5 years) of market data. More precisely, for all times $t > 1 2 5 0$ we fit the coefficients $\hat { \omega } _ { t } , ~ \hat { \tau } _ { t } , \hat { \beta } _ { t }$ as well as the sequence of variances $\{ \hat { \sigma } _ { s } ^ { t } \} _ { 1 \leq s \leq t - 1 }$ using only the data $\{ R _ { r } \} _ { t - 1 2 5 0 \leq r < t } .$ Then, our point prediction for the realized volatility at time t is

$$
(\hat {\sigma} _ {t} ^ {t}) ^ {2} := \hat {\omega} _ {t} + \hat {\tau} _ {t} V _ {t - 1} + \hat {\beta} _ {t} (\hat {\sigma} _ {t - 1} ^ {t}) ^ {2}.
$$

To form prediction intervals we define the sequence of conformity scores

$$
S _ {t} := \frac {| V _ {t} - (\hat {\sigma} _ {t} ^ {t}) ^ {2} |}{(\hat {\sigma} _ {t} ^ {t}) ^ {2}}
$$

and the corresponding quantile function

$$
\hat {Q} _ {t} (p) := \inf \left\{x: \frac {1}{1 2 5 0} \sum_ {r = t - 1 2 5 0} ^ {t - 1} \mathbb {1} _ {S _ {r} \leq x} \geq p \right\}.
$$

Then, our prediction set at time $t$ is

$$
\hat {C} _ {t} (\alpha_ {t}) := \left\{v: \frac {| v - (\hat {\sigma} _ {t} ^ {t}) ^ {2} |}{(\hat {\sigma} _ {t} ^ {t}) ^ {2}} \leq \hat {Q} _ {t} (1 - \alpha_ {t}) \right\},
$$

where $\left\{ \alpha _ { t } \right\}$ is initialized with $\alpha _ { 1 2 5 0 } = \alpha = 0 .$ 1 and then updated recursively as in (2).

We compare this algorithm to a non-adaptive alternative that takes $\alpha _ { t } = \alpha$ fixed. To measure the performance of these methods across time we examine their local coverage frequencies defined as the average coverage rate over the most recent two years, i.e.

$$
\operatorname{localCov} _ {t} := 1 - \frac {1}{5 0 0} \sum_ {r = t - 2 5 0 + 1} ^ {t + 2 5 0} \operatorname{err} _ {r}.\tag{4}
$$

If the methods perform well then we expect the local coverage frequency to stay near the target value $1 - \alpha$ across all time points.

![](images/93c4b72f720277037e9028ef9d878f8653b49f6662b66947a62bbd1bbf0a8152.jpg)  
Figure 1: Local coverage frequencies for adaptive conformal (blue), a non-adaptive method that holds $\alpha _ { t } = \alpha$ fixed (red), and an i.i.d. Bernoulli(0.1) sequence (grey) for the prediction of stock market volatility. The coloured dotted lines mark the average coverage obtained across all time points, while the black line indicates the target level of $1 - \alpha = 0 . 9$

Daily open prices were obtained from publicly available datasets published by The Wall Street Journal. The realized local coverage frequencies for the non-adaptive and adaptive conformal methods on four different stocks are shown in Figure 1. These stocks were selected out of a total of 12 stocks that we examined because they showed a clear failure of the non-adaptive method. Adaptive conformal inference was found to perform well in all cases (see Figure 9 in the appendix).

As a visual comparator, the grey curves show the moving average $\begin{array} { r } { 1 - \frac { 1 } { 5 0 0 } \sum _ { r = t - 2 5 0 + 1 } ^ { t + 2 5 0 } I _ { r } } \end{array}$ for sequences $\left\{ I _ { t } \right\} _ { 1 \leq t \leq T }$ that are i.i.d. Bernoulli(0.1). We see that the local coverage frequencies obtained by adaptive conformal inference (blue lines) always stay within the variation that would be expected from an i.i.d. Bernoulli sequence. On the other hand, the non-adaptive method undergoes large excursions away from the target level of $1 - \alpha = 0 . 9$ (red lines). For example, in the bottom right panel we can see that the non-adaptive method fails to cover the realized volatility of Fannie Mae during the 2008 financial crisis, while the adaptive method is robust to this event (see Figure 4 in the Appendix for a plot of the price of Fannie Mae over this time period).

## 3 Related Work

Prior work on conformal inference has considered two different types of distribution shift [33, 10]. In both cases the focus was on environments in which the calibration data is drawn i.i.d. from a single distribution $P _ { 0 }$ , while the test point comes from a second distribution $P _ { 1 }$ . In this setting Tibshirani et al. [33] showed that valid prediction sets can be obtained by re-weighting the calibration data using the likelihood ratio between $P _ { 1 }$ and $P _ { 0 }$ . However, this requires the conditional distribution of $Y | X$ to be constant between training and testing and the likelihood ratio $P _ { 1 } ( X ) / P _ { 0 } ( X )$ ) to be either known or very accurately estimated. On the other hand, Cauchois et al. [10] develop methods for forming prediction sets that are valid whenever $P _ { 1 }$ and $P _ { 0 }$ are close in f-divergence. Similar to our work, they show that if $D _ { f } ( P _ { 1 } | | P _ { 0 } ) \leq \rho$ then there exists a conservative value $\alpha _ { \rho } \in ( 0 , 1 )$ such that

$$
M (\alpha_ {\rho}) := \mathbb {P} (S (X _ {t}, Y _ {t}) > \hat {Q} (1 - \alpha_ {\rho})) \leq \alpha .
$$

The difference between our approach and theirs is twofold. First, while they fix a single conservative value $\alpha _ { \rho }$ our methods aim to estimate the optimal choice $\alpha ^ { * }$ satisfying ${ \mathrm { ~ \bar { \cal M } } } ( \alpha ^ { * } ) = \alpha$ . This is not possible in the setting of [10] as they do not observe any data from which the size of the distribution shift can be estimated. Second, while they consider only one training and one testing distribution we work in a fully online setting in which the distribution is allowed to shift continuously over time.

## 4 Coverage guarantees

## 4.1 Distribution-free results

In this section we outline the theoretical coverage guarantees of adaptive conformal inference. We will assume throughout that with probability one $\alpha _ { 1 } \in [ 0 , 1 ]$ and $\hat { Q } _ { t }$ is non-decreasing with $\hat { Q } _ { t } ( x ) = - \infty$ for all $x < 0$ and $\hat { Q } _ { t } ( x ) = \infty$ for all $x > 1$ . Our first result shows that over long time intervals adaptive conformal inference obtains the correct coverage frequency irrespective of any assumptions on the data-generating distribution.

Lemma 4.1 With probability one we have that ∀t $\in \mathbb { N } , \alpha _ { t } \in [ - \gamma , 1 + \gamma ] .$

Proof: Assume by contradiction that with positive probability $\{ \alpha _ { t } \} _ { t \in \mathbb { N } }$ is such that inf $_ t \alpha _ { t } < - \gamma$ (the case where $\operatorname* { s u p } _ { t } \alpha _ { t } > 1 + \gamma$ is identical). Note that su $\begin{array} { r } { \operatorname * { l p } _ { t } \big | \alpha _ { t + 1 } - \alpha _ { t } \big | = \operatorname* { s u p } _ { t } \gamma \big | \alpha - \mathrm { e r r } _ { t } \big | < \gamma } \end{array}$ Thus, with positive probability we may find $t \in \mathbb { N }$ such that $\alpha _ { t } < 0$ and $\alpha _ { t + 1 } < \alpha _ { t }$ . However,

$$
\alpha_ {t} <   0 \implies \hat {Q} _ {t} (1 - \alpha_ {t}) = \infty \implies \operatorname{err} _ {t} = 0 \implies \alpha_ {t + 1} = \alpha_ {t} + \gamma (\alpha - \operatorname{err} _ {t}) \geq \alpha_ {t}
$$

and thus $\mathbb { P } ( \exists t$ such that $\alpha _ { t + 1 } < \alpha _ { t } < 0 ) = 0$ . We have reached a contradiction.

Proposition 4.1 With probability one we have that for all $T \in \mathbb { N } ,$

$$
\left| \frac {1}{T} \sum_ {t = 1} ^ {T} e r r _ {t} - \alpha \right| \leq \frac {\max \{\alpha_ {1} , 1 - \alpha_ {1} \} + \gamma}{T \gamma}.\tag{5}
$$

In particular, lim $\begin{array} { r } { \mathbf { \sigma } _ {  \infty } \frac { 1 } { T } \sum _ { t = 1 } ^ { T } e r r _ { t } \stackrel { a . s . } { = } \alpha } \end{array}$

Proof: By expanding the recursion defined in (2) and applying Lemma 4.1 we find that

$$
[ - \gamma , 1 + \gamma ] \ni \alpha_ {T + 1} = \alpha_ {1} + \sum_ {t = 1} ^ {T} \gamma (\alpha - \operatorname{err} _ {t}).
$$

Rearranging this gives the result.

Proposition 4.1 puts no constraints on the data generating distribution. One may immediately ask whether these results can be improved by making mild assumptions on the distribution shifts. We argue that without assumptions on the quality of the initialization the answer to this question is negative. To understand this, consider a setting in which there is a single fixed optimal target $\alpha ^ { * } \in [ 0 , 1 ]$ and assume that

$$
M _ {t} (p) = M (p) = \left\{ \begin{array}{l} \alpha + \frac {1 - \alpha}{1 - \alpha^ {*}} (p - \alpha^ {*}), \text {if} p > \alpha^ {*}, \\ \alpha + \frac {\alpha}{\alpha^ {*}} (p - \alpha^ {*}) \text {if} p \leq \alpha^ {*}. \end{array} \right.
$$

Suppose additionally that $\mathbb { E } [ \mathbf { e r r } _ { t } | \alpha _ { t } ] = M ( \alpha _ { t } ) . ^ { 1 }$ In order to simplify the calculations consider the noiseless update $\alpha _ { t + 1 } = \alpha _ { t } + \gamma ( \alpha - M ( \alpha _ { t } ) ) = \alpha _ { t } + \gamma ( \alpha - \mathbb { E } [ \operatorname { e r r } _ { t } | \alpha _ { t } ] )$ . Intuitively, the noiseless update can be viewed as the average case behaviour of (2). Now, for any initialization $\alpha _ { 1 }$ and any $\gamma \leq$ min $\textstyle \left\{ { \frac { 1 - \alpha ^ { * } } { 1 - \alpha } } , { \frac { \alpha ^ { * } } { \alpha } } \right\}$ there exists a constant $c \in \textstyle \left\{ { \frac { 1 - \alpha } { 1 - \alpha ^ { * } } } , { \frac { \alpha } { \alpha ^ { * } } } \right\}$ such that for all $t , M ( \alpha _ { t } ) - \alpha = c ( \alpha _ { t } - \alpha ^ { * } )$ So, we have that

$$
\mathbb {E} \left[ \operatorname{err} _ {t} \right] - \alpha = c \mathbb {E} \left[ \alpha_ {t} - \alpha^ {*} \right] = c \mathbb {E} \left[ \alpha_ {t - 1} + \gamma \left(\alpha - M _ {t - 1} \left(\alpha_ {t - 1}\right)\right) - \alpha^ {*} \right] = c (1 - c \gamma) \mathbb {E} \left[ \alpha_ {t - 1} - \alpha^ {*} \right].
$$

Repeating this calculation recursively gives that

$$
\mathbb {E} [ \operatorname{err} _ {t} ] - \alpha = c (1 - c \gamma) ^ {t - 1} \mathbb {E} [ \alpha_ {1} - \alpha^ {*} ] = c (1 - c \gamma) ^ {t - 1} (\alpha_ {1} - \alpha^ {*}),
$$

and thus,

$$
\left| \frac {1}{T} \sum_ {t = 1} ^ {T} \mathbb {E} [ \operatorname{err} _ {t} ] - \alpha \right| = \frac {1 - (1 - c \gamma) ^ {T}}{T \gamma} | \alpha_ {1} - \alpha^ {*} |.
$$

The comparison of this bound to $( 5 )$ is self-evident. The main difference is that we have replaced max $\{ 1 - \alpha _ { 1 } , \alpha _ { 1 } \}$ with $| \alpha _ { 1 } - \alpha ^ { * } |$ . This arises from the fact that $\alpha ^ { * } \in ( 0 , 1 )$ is arbitrary and thus max $\{ 1 - \alpha _ { 1 } , \alpha _ { 1 } \}$ is the best possible upper bound on $| \alpha _ { 1 } - \alpha ^ { * } |$ . So, we view Proposition 4.1 as both an agnostic guarantee that shows that our method gives the correct long-term empirical coverage frequency irrespective of the true data generating process, and as an approximately tight bound on the worst-case behaviour immediately after initialization.

## 4.2 Performance in a hidden Markov mode

Although we believe Proposition 4.1 is an approximately tight characterization of the behaviour after initialization, we can still ask whether better bounds can be obtained for large time steps. In this section we answer this question positively by showing that if $\alpha _ { 1 }$ is initialized appropriately and the distribution shift is small, then tighter coverage guarantees can be given. In order to obtain useful results we will make some simplifying assumptions about the data generating process. While we do not expect these assumptions to hold exactly in any real-world setting, we do consider our results to be representative of the true behaviour of adaptive conformal inference and we expect similar results to hold under alternative models.

## 4.2.1 Setting

We model the data as coming from a hidden Markov model. In particular, we let $\{ A _ { t } \} _ { t \in \mathbb { N } } \subseteq { \mathcal { A } }$ denote the underlying Markov chain for the environment and we assume that conditional on $\{ A _ { t } \} _ { t \in \mathbb { N } }$ $\{ ( X _ { t } , Y _ { t } ) \} _ { t \in \mathbb { N } }$ is an independent sequence with $( X _ { t } , Y _ { t } ) \sim P _ { A _ { i } }$ for some collection of distributions $\{ P _ { a } : a \in \mathcal { A } \}$ . In order to simplify our calculations, we assume additionally that the estimated quantile function $\hat { Q } _ { t } ( \cdot )$ and score function $S _ { t } ( \cdot )$ do not depend on t and we denote them by ${ \hat { Q } } ( \cdot )$ and $\bar { S } ( \cdot )$ . This occurs for example in the split conformal setting with fixed training and calibration sets.

In this setting, $\{ ( \alpha _ { t } , A _ { t } ) \} _ { t \in \mathbb { N } }$ forms a Markov chain on $[ - \gamma , 1 + \gamma ] \times \mathcal { A }$ . We assume that this chain has a unique stationary distribution π and that $( \alpha _ { 1 } , A _ { 1 } ) \sim \pi$ This implies that $\left( \alpha _ { t } , A _ { t } , \mathbf { e r r } _ { t } \right)$ is a stationary process and thus will greatly simplify our characterization of the behaviour of $\mathrm { e r r } _ { t }$ . While there is little doubt that the theory can be extended, recall our that main goal is to get useful and simple results. That said, what we really have in mind here is that $\{ A _ { t } \} _ { t \in \mathbb { N } }$ is sufficiently wellbehaved to guarantee that $( \alpha _ { t } , A _ { t } )$ has a limiting stationary distribution. In Section $_ { \mathrm { A . 5 } }$ we give an example where this is indeed provably the case. Lastly, the assumption that $( \alpha _ { 1 } , A _ { 1 } ) \sim \pi$ is essentially equivalent to assuming that we have been running the algorithm for long enough to exit the initialization phase described in Section 4.1.

## 4.2.2 Large deviation bound for the errors

Our first observation is that $\operatorname { e r r } _ { t }$ has the correct average value. More precisely, by Proposition 4.1 we have that lim ${ \mathrm { \Delta } } _ { T  \infty } { \mathrm { \Delta } } T ^ { - 1 } \sum _ { t = 1 } ^ { T } \operatorname { e r r } _ { t } { \stackrel { a . s . } { = } } { \mathrm { \Delta } } \alpha$ and since $\operatorname { e r r } _ { t }$ is stationary it follows that $\mathbb { E } [ \mathsf { e r r } _ { t } ] = \alpha$ . Thus, to understand the deviation of $T ^ { - 1 } \sum _ { t = 1 } ^ { T } \mathrm { e r r } _ { t }$ from α we simply need to characterize the dependence structure of $\{ \mathrm { e r r } _ { t } \} _ { t \in \mathbb { N } }$

We accomplish this in Theorem 4.1, which gives a large deviation bound on $\begin{array} { r } { | T ^ { - 1 } \sum _ { t = 1 } ^ { T } \mathrm { e r r } _ { t } - \alpha | } \end{array}$ The idea behind this result is to decompose the dependence in $\{ \mathrm { e r r } _ { t } \} _ { t \in \mathbb { N } }$ into two parts. First, there is dependence due to the fact that $\alpha _ { t }$ is a function of $\{ \mathrm { e r r } _ { r } \} _ { 1 \leq r \leq t - 1 }$ . In Section $\mathrm { A } . 7$ in the Appendix we argue that this dependence induces a negative correlation and thus the errors concentrate around their expectation at a rate no slower than that of an i.i.d. Bernoulli sequence. This gives rise to the first term in (6), which is what would be obtained by applying Hoeffding’s inequality to an i.i.d. sequence. Second, there is dependence due to the fact that $A _ { t }$ depends on $A _ { t - 1 }$ . More specifically, consider a setting in which the distribution of $Y | X$ has more variability in some states than others. The goal of adaptive conformal inference is to adapt to the level of variability and thus return larger prediction sets in states where the distribution of $\mathbf { \hat { Y } } | X$ is more spread. However, this algorithm is not perfect and as a result there may be some states $a \in { \mathcal { A } }$ in which $\mathbb { E } [ \mathbf { e r r } _ { t } | A _ { t } = a ]$ is biased away from α. Furthermore, if the environment tends to spend long stretches of time in more variable (or less variable) states this will induce a positive dependence in the errors and cause $T ^ { - 1 } \sum _ { t = 1 } ^ { T }$ err<sub>t</sub> to deviate from α. To control this dependence we use a Bernstein inequality for Markov chains to bound $\begin{array} { r } { | T ^ { - 1 } \sum _ { t = 1 } ^ { T } \mathbb { E } [ \mathrm { e r r } _ { t } | A _ { t } ] - \alpha | } \end{array}$ . This gives rise to the second term in (6).

Theorem 4.1 Assume that $\{ A _ { t } \} _ { t \in \mathbb { N } }$ has non-zero absolute spectral gap $1 - \eta > 0 .$ . Let

$$
B := \sup _ {a \in \mathcal {A}} | \mathbb {E} [ \operatorname{err} _ {t} | A _ {t} = a ] - \alpha | \quad a n d \quad \sigma_ {B} ^ {2} := \mathbb {E} [ (\mathbb {E} [ \operatorname{err} _ {t} | A _ {t} ] - \alpha) ^ {2} ].
$$

Then,

$$
\mathbb {P} \left(\left| \frac {1}{T} \sum_ {t = 1} ^ {T} \operatorname{err} _ {t} - \alpha \right| \geq \epsilon\right) \leq 2 \exp \left(- \frac {T \epsilon^ {2}}{8}\right) + 2 \exp \left(- \frac {T (1 - \eta) \epsilon^ {2}}{8 (1 + \eta) \sigma_ {B} ^ {2} + 2 0 B \epsilon}\right).\tag{6}
$$

A formal proof of this result can be found in Section $\mathbf { A . 7 . }$ The quality of this concentration inequality will depend critically on the size of the bias terms $B$ and $\sigma _ { B } ^ { 2 }$ . Before proceeding, it is important that we emphasize that the definitions of $B$ and $\sigma _ { B } ^ { 2 }$ are independent of the choice of t owing to the fact that $\left( \alpha _ { t } , A _ { t } , \mathbf { e r r } _ { t } \right)$ is assumed stationary. Now, to understand these quantities, let

$$
M (p | a) := \mathbb {P} (S (X _ {t}, Y _ {t}) > \hat {Q} (1 - p) | A _ {t} = a)
$$

denote the realized miscoverage level in state $a \in { \mathcal { A } }$ obtained by the quantile $\hat { Q } ( 1 - p )$ . Assume that $M ( p | a )$ is continuous. This will happen for example when ${ \hat { Q } } ( \cdot )$ is continuous and ${ \cal S } ( X _ { t } , Y _ { t } ) | A _ { t } = a$ is continuously distributed. Then, there exists an optimal value $\alpha _ { a } ^ { * }$ such that $M ( \alpha _ { a } ^ { * } | \dot { a } ) = \alpha$ . Lemma A.4 in the Appendix shows that if in addition $M ( \cdot | a )$ admits a second order Taylor expansion, then

$$
B \leq C \left(\gamma + \gamma^ {- 1} \sup _ {a \in \mathcal {A}} \sup _ {k \in \mathbb {N}} \mathbb {E} [ | \alpha_ {A _ {t + 1}} ^ {*} - \alpha_ {A _ {t}} ^ {*} | | A _ {t + k} = a ]\right) \quad \text { and } \quad \sigma_ {B} ^ {2} \leq B ^ {2}.
$$

Here, the constant $C$ will depend on how much $M ( \cdot | a )$ differs from the ideal case in which ${ \hat { Q } } ( \cdot )$ is the true quantile function for $\mathsf { \bar { S } } ( X _ { t } , Y _ { t } ) | A _ { t } = a$ . In this case we would have that $M ( \cdot | a )$ is the linear function $\operatorname { \dot { \cal M } } ( p | a ) = p , \forall p \in [ 0 , 1 ]$ and $\dot { C } \le 2$

We remark that the term $\mathbb { E } [ | \alpha _ { A _ { t + 1 } } ^ { * } - \alpha _ { A _ { t } } ^ { * } | | A _ { t + k } = a ]$ can be seen as a quantitative measurement of the size of the distribution shift in terms of the change in the critical value $\alpha _ { a } ^ { * }$ . Thus, we interpret these results as showing that if the distribution shift is small and ∀a $\in \mathcal { A } , \hat { Q } ( \cdot )$ gives reasonable coverage of the distribution of ${ \cal S } ( X _ { t } , Y _ { t } ) | A _ { t } = a$ , then $T ^ { - 1 } \sum _ { t = 1 } ^ { T } \mathrm { e r r } _ { t }$ will concentrate well around α.

## 4.2.3 Achieving approximate marginal coverage

Theorem 4.1 bounds the distance between the average miscoverage rate and the target level over long stretches of time. On the other hand, it provides no information about the marginal coverage frequency at a single time step. The following result shows that if the distribution shift is small, the realized marginal coverage rate $M ( \alpha _ { t } | A _ { t } )$ will be close to α on average.

Theorem 4.2 Assume that there exists a constant $L > 0$ such that for all $a \in { \mathcal { A } }$ and all $\alpha _ { 1 } , \alpha _ { 2 } \in \mathbb { R }$

$$
\left| M \left(\alpha_ {2} | a\right) - M \left(\alpha_ {1} | a\right) \right| \leq L \left| \alpha_ {2} - \alpha_ {1} \right|.
$$

Assume additionally thatfor all $a \in { \mathcal { A } }$ there exists $\alpha _ { a } ^ { * } \in ( 0 , 1 )$ such that $M ( \alpha _ { a } ^ { * } | a ) = \alpha$ . Then,

$$
\mathbb {E} \left[ \left(M \left(\alpha_ {t} \mid A _ {t}\right) - \alpha\right) ^ {2} \right] \leq \frac {L (1 + \gamma)}{\gamma} \mathbb {E} \left[ \left| \alpha_ {A _ {t + 1}} ^ {*} - \alpha_ {A _ {t}} ^ {*} \right| \right] + \frac {L}{2} \gamma .\tag{7}
$$

Once again we emphasize that (7) holds for any choice of t owing to the fact that $\left( \alpha _ { t } , A _ { t } , \mathbf { e r r } _ { t } \right)$ is assumed stationary and thus the quantities appearing in the bound are invariant across t. Proof of this result can be found in Section $\mathrm { A } . 8$ of the Appendix. We remark that the right-hand side of (7) is minimized by choosing $\gamma = ( 2 \mathbb { E } [ | \alpha _ { A _ { t + 1 } } ^ { * } - \alpha _ { A _ { t } } ^ { * } | ] ) ^ { 1 / 2 }$ , which gives the inequality

$$
\mathbb {E} [ (M (\alpha_ {t} | A _ {t}) - \alpha) ^ {2} ] \leq L (\sqrt {2} + 1) \sqrt {\mathbb {E} [ | \alpha_ {A _ {t + 1}} ^ {*} - \alpha_ {A _ {t}} ^ {*} | ]}.
$$

As above we have that in the ideal case ${ \hat { Q } } ( \cdot )$ is a perfect estimate of the quantiles of ${ \cal S } ( X _ { t } , Y _ { t } ) | A _ { t } = a$ and thus $M ( p | a ) = p$ and $L = 1$ . Moreover, we once again have the interpretation that $\mathbb { E } [ | \alpha _ { A _ { t + 1 } } ^ { * } -$ $\alpha _ { A _ { t } } ^ { * } | ]$ is a quantitative measurement of the distribution shift. Thus, this result can be interpreted as bounding the average difference between the realized and target marginal coverage in terms of the size of the underlying distribution shift. Finally, note that the choice $\gamma = ( 2 \mathbb { E } [ | \bar { \alpha _ { A _ { t + 1 } } ^ { * } } - \alpha _ { A _ { t } } ^ { * } | ] ) ^ { 1 / 2 }$ formalizes our intuition that $\gamma$ should be chosen to be larger in domains with greater distribution shift, while not being so large as to cause $\alpha _ { t }$ to be overly volatile.

## 5 Impact of $S _ { t } ( \cdot )$ on the performance

The performance of all conformal inference methods depends heavily on the design of the conformity score. Previous work has shown how carefully chosen scores or even explicit optimization of the interval width can be used to obtain smaller prediction sets [e.g. 28, 29, 20, 12]. Adaptive conformal inference can work with any conformity score $S _ { t } ( \cdot )$ and quantile function $\hat { Q } _ { t } ( \cdot )$ and thus can be directly combined with other improvements in conformal inference to obtain shorter intervals. One important caveat here is that the lengths of conformal prediction sets depend directly on the quality of the fitted regression model. Thus, to obtain smaller intervals one should re-fit the model at each time step using the most recent data to build the most accurate predictions. This is exactly what we have done in our experiments in Sections 2.2 and 6.

![](images/68e670f9bb32773c303831bc54d593524c4ed7d1f246d9e5413f0824dbeae97f.jpg)  
Figure 2: Local coverage frequencies for adaptive conformal (blue), a non-adaptive method that holds $\alpha _ { t } = \alpha$ fixed (red), and an i.i.d. Bernoulli(0.1) sequence (grey) for the prediction of stock market volatility with conformity score $\tilde { S } _ { t }$ . The coloured dotted lines mark the average coverage obtained across all time points, while the black line indicates the target level of $1 - \alpha = 0 . 9$

In addition to this, the choice of $S _ { t } ( \cdot )$ can also have a direct effect on the coverage properties of adaptive conformal inference. Theorems 4.1 and 4.2 show that the performance of adaptive conformal inference is controlled by the size of the shift in the optimal parameter $\alpha _ { t } ^ { * }$ across time. Moreover, $\alpha _ { t } ^ { * }$ itself is in one-to-one correspondence with the $1 - \alpha$ quantile of $S _ { t } ( X _ { t } ^ { \cdot } , Y _ { t } )$ ). Thus, the coverage properties of adaptive conformal inference depend on how close $S _ { t } ( X _ { t } , Y _ { t } )$ is to being stationary.

For a simple example illustrating the impact of this dependence, note that in Section 2.2 we formed prediction sets using the conformity score

$$
S _ {t} := \frac {| V _ {t} - \hat {\sigma} _ {t} ^ {2} |}{\hat {\sigma} _ {t} ^ {2}}.
$$

An a priori reasonable alternative to this is the unnormalized score

$$
\tilde {S} _ {t} := | V _ {t} - \hat {\sigma} _ {t} ^ {2} |.
$$

However, after a more careful examination it becomes unsurprising that normalization by $\hat { \sigma } _ { t } ^ { 2 }$ is critical for obtaining an approximately stationary conformity score and thus $\tilde { S } _ { t }$ leads to much worse coverage properties. Figure 2 shows the local coverage frequency (see (4)) of adaptive conformal inference using $\tilde { S } _ { t }$ . In comparison to Figure 1 the coverage now undergoes much wider swings away from the target level of 0.9. This issue can be partially mitigated by choosing a larger value of $\gamma$ that gives greater adaptivity to the algorithm.

## 6 Real data example: election night predictions

During the 2020 US presidential election The Washington Post used conformalized quantile regression (CQR) (see (1) and Section 1.1) to produce county level predictions of the vote total on election night [13]. Here we replicate the core elements of this method using both fixed and adaptive quantiles.

![](images/92e17dfe3ba6720d108941cddd55af43839207b9623451bd8f178931309a3a2e.jpg)  
Figure 3: Local coverage frequencies of adaptive conformal (blue), a non-adaptive method that holds $\alpha _ { t } = \alpha$ fixed (red), and an i.i.d. Bernoulli(0.1) sequence (grey) for county-level election predictions. Coloured dotted lines show the average coverage across all time points, while the black line indicates the target coverage level of $1 - \alpha = 0 . 9$

To make the setting precise, let $\{ Y _ { t } \} _ { 1 \leq t \leq T }$ denote the number of votes cast for presidential candidate Joe Biden in the 2020 election in each of approximately $T = 3 0 0 0$ counties in the United States. Let $X _ { t }$ denote a set of demographic covariates associated to the tth county. In our experiment $X _ { t }$ will include information on the make-up of the county population by ethnicity, age, sex, median income and education (see Section A.6.1 for details). On election night county vote totals were observed as soon as the vote count was completed. If the order in which vote counts completed was uniformly random $\{ ( X _ { t } , Y _ { t } ) \} _ { 1 \leq t \leq T }$ would be an exchangeable sequence on which we could run standard conformal inference methods. In reality, larger urban counties tend to report results later than smaller rural counties and counties on the east coast of the US report earlier than those on the west coast. Thus, the distribution of $( X _ { t } , Y _ { t } )$ can be viewed as drifting throughout election night.

We apply CQR to predict the county-level vote totals (see Section A.6.2 for details). To replicate the east to west coast bias observed on election night we order the counties by their time zone with eastern time counties appearing first and Hawaiian counties appearing last. Within each time zone counties are ordered uniformly at random. Figure 3 shows the realized local coverage frequency over the most recent 300 counties (see (4)) for the non-adaptive and adaptive conformal methods. We find that the non-adaptive method fails to maintain the desired 90% coverage level, incurring large troughs in its coverage frequency during time zone changes. On the other hand, the adaptive method maintains approximate 90% coverage across all time points with deviations in its local coverage level comparable to what is observed in Bernoulli sequences.

## 7 Discussion

There are still many open problems in this area. The methods we develop are specific to cases where $Y _ { t }$ is revealed at each time point. However, there are many settings in which we receive the response in a delayed fashion or in large batches. In addition, our theoretical results in Section 4.2 are limited to a single model for the data generating distribution and the special case where the quantile function $\hat { Q } _ { t } ( \cdot )$ is fixed across time. It would be interesting to determine if similar results can be obtained in settings where $\hat { Q } _ { t } ( \cdot )$ is fit in an online fashion on the most recent data. Another potential area for improvement is in the choice of the step size $\gamma .$ In Section 2.1 we give some heuristic guidelines for choosing $\gamma$ based on the size of the distribution shift in the environment. Ideally however we would like to be able to determine $\gamma$ adaptively without prior knowledge. Finally, our experimental results are limited to just two domains. Additional work is needed to determine if our methods can successfully protect against a wider variety of real-world distribution shifts.

## 8 Acknowledgements

E.C. was supported by Office of Naval Research grant N00014-20-12157, by the National Science Foundation grants OAC 1934578 and DMS 2032014, by the Army Research Office (ARO) under grant W911NF-17-1-0304, and by the Simons Foundation under award 814641. We thank John Cherian for valuable discussions related to Presidential Election Night 2020 and Lihua Lei for helpful comments on the relationship to online learning.

## References

[1] Julia Angwin, Jeff Larson, Surya Mattu, and Lauren Kirchner. Machine bias: There’s software used across the country to predict future criminals. and it’s biased against blacks, 2016. URL https://www.propublica.org/article/ machine-bias-risk-assessments-in-criminal-sentencing.

[2] Claudine Badue, Rânik Guidolini, Raphael Vivacqua Carneiro, Pedro Azevedo, Vinicius B. Cardoso, Avelino Forechi, Luan Jesus, Rodrigo Berriel, Thiago M. Paixão, Filipe Mutz, Lucas de Paula Veronese, Thiago Oliveira-Santos, and Alberto F. De Souza. Self-driving cars: A survey. Expert Systems with Applications, 165:113816, 2021. ISSN 0957-4174. doi: https: //doi.org/10.1016/j.eswa.2020.113816. URL https://www.sciencedirect.com/science/ article/pii/S095741742030628X.

[3] Rina Foygel Barber, Emmanuel J. Candès, Aaditya Ramdas, and Ryan J. Tibshirani. Predictive inference with the jackknife+. The Annals ofStatistics, 49(1):486 – 507, 2021. doi: 10.1214/ 20-AOS1965. URL https://doi.org/10.1214/20-AOS1965.

[4] Tim Bollerslev. Generalized autoregressive conditional heteroskedasticity. Journal of Econometrics, 31(3):307–327, 1986. ISSN 0304-4076. doi: https://doi.org/10.1016/ 0304-4076(86)90063-1. URL https://www.sciencedirect.com/science/article/ pii/0304407686900631.

[5] United States Census Bureau. County characteristics resident population estimates, 2019. data retrieved from https://www.census.gov/data/tables/time-series/demo/popest/ 2010s-counties-detail.html.

[6] United States Census Bureau. 2015-2019 american community survey 5-year average countylevel estimates, 2019. data retrieved from https://www.ers.usda.gov/data-products/ county-level-data-sets/download-data/.

[7] United States Census Bureau. Small area income and poverty estimates: 2019, 2019. data retrieved from https://www.ers.usda.gov/data-products/ county-level-data-sets/download-data/.

[8] Emmanuel J. Candès, Lihua Lei, and Zhimei Ren. Conformalized survival analysis. arXiv preprint, 2021. arXiv:2103.09763.

[9] X. Cao, J. Zhang, and H. V. Poor. On the time-varying distributions of online stochastic optimization. In 2019 American Control Conference (ACC), pages 1494–1500, 2019. doi: 10.23919/ACC.2019.8814889.

[10] Maxime Cauchois, Suyash Gupta, Alnur Ali, and John C. Duchi. Robust validation: Confident predictions even when distributions shift. arXiv preprint, 2020. arXiv:2008.04267.

[11] Maxime Cauchois, Suyash Gupta, and John C. Duchi. Knowing what you know: valid and validated confidence sets in multiclass and multilabel prediction. Journal ofMachine Learning Research, 22(81):1–42, 2021. URL http://jmlr.org/papers/v22/20-753.html.

[12] Haoxian Chen, Ziyi Huang, Henry Lam, Huajie Qian, and Haofeng Zhang. Learning prediction intervals for regression: Generalization and calibration. In Proceedings ofThe 24th International Conference on Artificial Intelligence and Statistics, volume 130 of Proceedings of Machine Learning Research, pages 820–828. PMLR, 13–15 Apr 2021.

[13] John Cherian and Lenny Bronner. How the washington post estimates outstanding votes for the 2020 presidential election. https://elex-models-prod.s3.amazonaws.com/ 2020-general/write-up/election\_model\_writeup.pdf, 2020.

[14] MIT Election Data and Science Lab. County Presidential Election Returns 2000-2016, 2018. URL https://doi.org/10.7910/DVN/VOQCHQ.

[15] Rina Foygel Barber, Emmanuel J Candès, Aaditya Ramdas, and Ryan J Tibshirani. The limits of distribution-free conditional predictive inference. Information and Inference: A Journal of the IMA, 08 2020. ISSN 2049-8772. doi: 10.1093/imaiai/iaaa017. URL https: //doi.org/10.1093/imaiai/iaaa017. iaaa017.

[16] Alexander Gammerman and Vladimir Vovk. Hedging predictions in machine learning. The Computer Journal, 50(2):151–163, 2007. doi: 10.1093/comjnl/bxl065.

[17] Elad Hazan. Introduction to online convex optimization. arXiv preprint, 2019. arXiv:1909.05207.

[18] Wassily Hoeffding. Probability inequalities for sums of bounded random variables. Journal of the American Statistical Association, 58(301):13–30, 1963. doi: 10.1080/01621459.1963. 10500830.

[19] Bai Jiang, Qiang Sun, and Jianqing Fan. Bernstein’s inequality for general markov chains. arXiv preprint, 2020. arXiv:1805.10721.

[20] Danijel Kivaranovic, Kory D. Johnson, and Hannes Leeb. Adaptive, distribution-free prediction intervals for deep networks. In Proceedings of the Twenty Third International Conference on Artificial Intelligence and Statistics, volume 108 of Proceedings ofMachine Learning Research, pages 4346–4356. PMLR, 26–28 Aug 2020.

[21] Danijel Kivaranovic, Robin Ristl, Martin Posch, and Hannes Leeb. Conformal prediction intervals for the individual treatment effect. arXiv preprint, 2020. arXiv:2006.01474.

[22] Jing Lei and Larry Wasserman. Distribution-free prediction bands for non-parametric regression. Journal ofthe Royal Statistical Society: Series B (Statistical Methodology), 76, 01 2014. doi: 10.1111/rssb.12021.

[23] Jing Lei, Max G’Sell, Alessandro Rinaldo, Ryan J. Tibshirani, and Larry Wasserman. Distribution-free predictive inference for regression. Journal of the American Statistical Association, 113(523):1094–1111, 2018. doi: 10.1080/01621459.2017.1307116. URL https://doi.org/10.1080/01621459.2017.1307116.

[24] Lihua Lei and Emmanuel J. Candès. Conformal inference of counterfactuals and individual treatment effects. arXiv preprint, 2021. arXiv:2006.06138.

[25] David Leip. Dave leip’s atlas of u.s. presidential elections., 2020. http://uselectionatlas. org.

[26] Harris Papadopoulos. Inductive conformal prediction: Theory and application to neural networks. In Tools in Artificial Intelligence,, pages 315–330, 2008.

[27] Harris Papadopoulos, Kostas Proedrou, Volodya Vovk, and Alex Gammerman. Inductive confidence machines for regression. In Tapio Elomaa, Heikki Mannila, and Hannu Toivonen, editors, Machine Learning: ECML 2002, pages 345–356, Berlin, Heidelberg, 2002. Springer Berlin Heidelberg. ISBN 978-3-540-36755-0.

[28] Yaniv Romano, Evan Patterson, and Emmanuel Candes. Conformalized quantile regression. In H. Wallach, H. Larochelle, A. Beygelzimer, F. d'Alché-Buc, E. Fox, and R. Garnett, editors, Advances in Neural Information Processing Systems, volume 32. Curran Associates, Inc., 2019. URL https://proceedings.neurips.cc/paper/2019/file/ 5103c3584b063c431bd1268e9b5e76fb-Paper.pdf.

[29] Yaniv Romano, Matteo Sesia, and Emmanuel Candes. Classification with valid and adaptive coverage. In Advances in Neural Information Processing Systems, volume 33, pages 3581–3591, 2020. URL https://proceedings.neurips.cc/paper/2020/file/ 244edd7e85dc81602b7615cd705545f5-Paper.pdf.

[30] Yaniv Romano, Matteo Sesia, and Emmanuel Candes. Classification with valid and adaptive coverage. In H. Larochelle, M. Ranzato, R. Hadsell, M. F. Balcan, and H. Lin, editors, Advances in Neural Information Processing Systems, volume 33, pages 3581–3591. Curran Associates, Inc., 2020. URL https://proceedings.neurips.cc/paper/2020/ file/244edd7e85dc81602b7615cd705545f5-Paper.pdf.

[31] Mauricio Sadinle, Jing Lei, and Larry Wasserman. Least ambiguous set-valued classifiers with bounded error levels. Journal ofthe American Statistical Association, 114(525):223–234, 2019. doi: 10.1080/01621459.2017.1395341. URL https://doi.org/10.1080/01621459.2017. 1395341.

[32] Glenn Shafer and Vladimir Vovk. A tutorial on conformal prediction. Journal of Machine Learning Research, 9(12):371–421, 2008. URL http://jmlr.org/papers/v9/shafer08a. html.

[33] Ryan J Tibshirani, Rina Foygel Barber, Emmanuel Candes, and Aaditya Ramdas. Conformal prediction under covariate shift. In H. Wallach, H. Larochelle, A. Beygelzimer, F. d'Alché-Buc, E. Fox, and R. Garnett, editors, Advances in Neural Information Processing Systems, volume 32. Curran Associates, Inc., 2019. URL https://proceedings.neurips.cc/paper/2019/ file/8fb21ee7a2207526da55a679f0332de2-Paper.pdf.

[34] Vladimir Vovk, Alex Gammerman, and Glenn Shafer. Algorithmic Learning in a Random World. Springer-Verlag, Berlin, Heidelberg, 2005. ISBN 0387001522.

[35] Jingyi Zhu and James Spall. Tracking capability of stochastic gradient algorithm with constant gain. In 2016 IEEE 55th Conference on Decision and Control (CDC), pages 4522–4527, 12 2016. doi: 10.1109/CDC.2016.7798957.

## A Appendix

## A.1 Connection to online learning

In Section 2 we motivated the update (2) as a way to adjust the size of our prediction sets in response to the realized historical miscoverage frequency. Alternatively, one could also derive (2) as an online gradient descent algorithm with respect to the pinball loss. To be more precise let

$$
\beta_ {t} := \sup \{\beta : Y _ {t} \in \hat {C} _ {t} (\beta) \},
$$

where we remark that $\hat { C } _ { t } ( \beta _ { t } )$ can be thought of as the smallest prediction set containing Y . Additionally, define the pinball loss

$$
\rho_ {\alpha} (u) = \left\{ \begin{array}{l} \alpha u, u > 0, \\ - (1 - \alpha) u, u \leq 0. \end{array} \right..
$$

and consider the loss $\ell ( \alpha _ { t } , \beta _ { t } ) = \rho _ { \alpha } ( \beta _ { t } - \alpha _ { t } )$ . Then, one directly computes that

$$
\alpha_ {t} - \gamma \partial_ {\alpha_ {t}} \ell (\alpha_ {t}, \beta_ {t}) = \alpha_ {t} + \gamma (\alpha - \mathbb {1} _ {\alpha_ {t} > \beta_ {t}}) = \alpha_ {t} + \gamma (\alpha - \operatorname{err} _ {t}).
$$

Because the pinball loss is convex, this gradient descent update falls within a well understood class of algorithms that have been extensively studied in the online learning literature (see e.g. [17]). A standard analysis may then be to bound the regret of $\alpha _ { t }$ defined as

$$
\operatorname{Reg} _ {T} := \sum_ {t = 1} ^ {T} \ell (\alpha_ {t}, \beta_ {t}) - \min _ {\beta} \sum_ {t = 1} ^ {T} \ell (\beta , \beta_ {t}).
$$

Unfortunately, this notion of regret fails to capture our intuition that $\alpha _ { t }$ is adaptively tracking the moving target $\alpha _ { t } ^ { * }$ . Thus, we make the connection to online gradient descent only in passing and develop alternative theoretical tools in Section 4.

## A.2 Stock prices

Figure 4 shows daily open prices for the four stocks considered in Section 2.2.

![](images/bb8a914712961d2a8eb1c0606669e65663bd79ea8e708bcd6ee9b71f687e0da5.jpg)  
Figure 4: Daily open prices for the four stocks considered in Section 2.2.

## A.3 Trajectories of $\pmb { \alpha } _ { t }$

In this section we show the realized trajectories of $\alpha _ { t }$ obtained in our experiments from Sections 2.2 and 6.

![](images/73df87c8edac274e4d83776c90a8bfb3a44f189c0bb8f5a1874041284ebc2e15.jpg)  
Figure 5: Realized trajectories of $\alpha _ { t }$ for predicting stock market volatility as outlined in Section 2.2 using update (2).

![](images/9a9e693b745110efcd2c5828dee56650f2551ab7d418e6f387f2b8abe5f74a2d.jpg)  
Figure 6: Realized trajectories of $\alpha _ { t }$ for predicting stock market volatility as outlined in Section 2.2 using update (3) with $\dot { w } _ { s } \propto 0 . 9 5 ^ { t - s }$

![](images/13aefc0a3196b752d8913bc7fed781b57fdac6110190eea9d4cceefc92deea8b.jpg)  
Figure 7: Realized trajectory of $\alpha _ { t }$ for election night forecasting as outlined in Section 6 using update (2).

![](images/f41b3e265b37ffe613f3186f729225037f5e1709b82a1bfb859c6d61cbf288a9.jpg)  
Figure 8: Realized trajectory of $\alpha _ { t }$ for election night forecasting as outlined in Section 6 using update (3) with $w _ { s } \propto 0 . 9 5 ^ { t - \bar { s } }$

## A.4 Coverage for additional stocks

Figure 9 shows the local coverage level of adaptive and non-adaptive conformal inference for the prediction of market volatility (see Section 2.2) for 8 additional stocks/indices.

![](images/0072041c941791e91d2fe2579e495d6c6ad989b5a359ed6fa260b65018aee9f9.jpg)  
Figure 9: Local coverage frequencies for adaptive conformal (blue), a non-adaptive method that holds $\alpha _ { t } = \alpha$ fixed (red), and an i.i.d. Bernoulli(0.1) sequence (grey) for the prediction of market volatility. The coloured dotted lines mark the average coverage obtained across all time points, while the black line indicates the target level of $1 - \alpha = 0 . 9$

## A.5 Existence of a stationary distribution for $( \alpha _ { t } , A _ { t } )$

In this section we give one simple example in which the Markov chain $\{ ( \alpha _ { t } , A _ { t } ) \} _ { t \in \mathbb { N } }$ will have a unique stationary distribution. The setting considered here is the same as the one described in Section 4.2.

Let $\alpha _ { t }$ be initialized with $\alpha _ { 1 } \in \{ \alpha + k \gamma \alpha : k \in \mathbb { Z } \}$ . Assume that A is finite. Let P be the transition matrix of $\{ A _ { t } \} _ { t \in \mathbb { N } }$ and assume that for all $a _ { 1 } , a _ { 2 } \in \mathcal { A } , P _ { a _ { 1 } , a _ { 2 } } = \mathbb { P } ( A _ { t + 1 } = a _ { 2 } | A _ { t } = a _ { 1 } ) > 0$ Assume that α satisfies $\alpha ^ { - 1 } ( 1 - \alpha ) \in \mathbb { N }$ . This will hold for common choices of α such as $\alpha = 0 . 1$ and $\alpha = 0 . 0 5$ . Finally, assume that for all $a \in { \mathcal { A } }$ and all $p \in ( 0 , 1 ) , \mathbb { P } ( S ( X _ { t } , Y _ { t } ) \leq \hat { Q } ( p ) | A = a ) \in$ $( 0 , 1 )$ . This will occur for example when $S ( X _ { t } , Y _ { t } ) | A _ { t } = a$ is supported on R and ${ \hat { Q } } ( \cdot )$ is finite valued for all $p \in ( 0 , 1 )$ ).

We claim that in this case $\{ ( \alpha _ { t } , A _ { t } ) \} _ { t \in \mathbb { N } }$ has a unique stationary distribution. To prove this it is sufficient to show that this chain is irreducible and has a finite state space. To check that it has a finite state space it is sufficient to show that $\alpha _ { t }$ has a finite state space. We claim that with probability one we have that for all $t \in \mathbb { N } , \alpha _ { t } \in \{ \alpha + k \gamma \alpha : k \in \mathbb { Z } \}$ . To prove this we proceed by induction. The base case is given by our choice of $\alpha _ { 1 }$ . For the inductive step note that

$$
\begin{array}{l} \alpha_ {t} \in \{\alpha + k \gamma \alpha : k \in \mathbb {Z} \} \\ \implies \alpha_ {t + 1} = \alpha_ {t} + \gamma (\alpha - \operatorname{err} _ {t}) = \left\{ \begin{array}{l l} \alpha_ {t} + \gamma \alpha , \text {   if   } \operatorname{err} _ {t} = 0, \\ \alpha_ {t} - \gamma \alpha (\alpha^ {- 1} (1 - \alpha)), \text {   if   } \operatorname{err} _ {t} = 1, \end{array} \right. \quad \in \{\alpha + k \gamma \alpha : k \in \mathbb {Z} \}. \end{array}
$$

Since $\alpha _ { t }$ is also bounded (see Lemma 4.1) this implies that $\alpha _ { t }$ has a finite state space.

Finally, the fact that $\{ ( \alpha _ { t } , A _ { t } ) \} _ { t \in \mathbb { N } }$ is irreducible follows easily from our assumptions on $\{ A _ { t } \} _ { t \in \mathbb { N } }$ ${ \hat { Q } } ( \cdot )$ , and $\mathbb { P } ( S ( X _ { t } , Y _ { t } ) \le \hat { Q } ( p ) | A = a )$

## A.6 Additional information for Section 6

## A.6.1 Dataset description

The county-level demographic characteristics used for prediction were the proportion of the total population that fell into each of the following race categories (either alone or in combination): black or African American, American Indian or Alaska Native, Asian, Native Hawaiian or other Pacific islander. In addition to this, we also used the proportion of the total population that was male, of Hispanic origin, and that fell within each of the age ranges 20-29, 30-44, 45-64, and 65+. Demographic information was obtained from 2019 estimates published by the United States Census Bureau and available at [5]. To supplement these demographic features we also used the median household income and the percentage of individuals with a bachelors degree or higher as covariates. Data on county-level median household incomes was based on 2019 estimates obtained from [7]. The percentage of individuals with a bachelors degree or higher was computed based on data collected during the years 2015-2019 and published at [6]. As an aside, we remark that we used 2019 estimates because this was the most recent year for which data was available.

Vote counts for the 2016 election were obtained from [14], while 2020 election data was taken from [25]. In total, matching covariate and election vote count data were obtained for 3111 counties.

## A.6.2 Detailed prediction algorithm

Algorithm 1 below outlines the core conformal inference method used to predict election results. An R implementation of this algorithm as well as the core method outlined in Section 2.2 can be found at https: $/ / { \tt g i }$ thub.com/isgibbs/AdaptiveConformal.

## A.7 Large deviation bounds for the error sequence

In this section we prove Theorem 4.1. So, throughout we define the sequences $\{ \alpha _ { t } \} _ { t \in \mathbb { N } } , \{ \mathrm { e r r } _ { t } \} _ { t \in \mathbb { N } } .$ and $\{ A _ { t } \} _ { t \in \mathbb { N } }$ as in Section 4.2 and we assume that $\{ ( \alpha _ { t } , A _ { t } ) \} _ { t \in \mathbb { N } }$ is a stationary Markov chain from which it follows immediately that $\{ ( \alpha _ { t } , A _ { t } , \mathbf { e r r } _ { t } ) \} _ { t \in \mathbb { N } }$ is also stationary. Additionally, we assume that ${ \hat { Q } } ( \cdot )$ and $S ( \cdot )$ are fixed functions such that ${ \hat { Q } } ( \cdot )$ is non-decreasing with $\hat { Q } ( x ) = - \infty$ for all $x < 0$ and $\hat { Q } ( x ) = \infty$ for all $x > 1$ . The proof of Theorem 4.1 will rely on the following lemmas.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1: CQR method for election night prediction
Data: Observed sequence of county-level votes counts and covariates $\{(X_t, Y_t)\}_{1 \leq t \leq T}$ and vote counts for the democratic candidate in the previous election $\{Y_t^{\text{prev}}\}_{1 \leq t \leq T}$.
for $t = 1, 2, \ldots, T$ do
    Compute the residual $r_t = (Y_t - Y_t^{\text{prev}})/Y_t^{\text{prev}}$
for $t = 501, 502, \ldots, T$ do
    // We start making predictions once 500 counties have been observed.
    Randomly split the data $\{(X_l, r_l)\}_{1 \leq l \leq t-1}$ into a training set $\mathcal{D}_{\text{train}}$ and a calibration set $\mathcal{D}_{\text{cal}}$ with $|\mathcal{D}_{\text{train}}| = \lfloor (t-1) \cdot 0.75 \rfloor$;
    Fit a linear quantile regression model $\hat{q}(x; p)$ on $\mathcal{D}_{\text{train}}$;
    for $(X_l, r_l) \in \mathcal{D}_{\text{cal}}$ do
    Compute the conformity score $S_l = \max\{\hat{q}(X_l; \alpha/2) - r_l, r_l - \hat{q}(X_l; 1 - \alpha/2)\}$;
    Define the quantile function $\hat{Q}_t(p) = \inf\left\{x : \left( \frac{1}{|\mathcal{D}_{\text{cal}}|} \sum_{(X_l, r_l) \in \mathcal{D}_{\text{cal}}} \mathbb{1}_{S_l \leq x} \right) \geq p \right\}$;
    Return the prediction set
    $\hat{C}_t(\alpha) := \{y : \max\{\hat{q}(X_t; \alpha/2) - \frac{y - Y_t^{\text{prev}}}{Y_t^{\text{prev}}}, \frac{y - Y_t^{\text{prev}}}{Y_t^{\text{prev}}} - \hat{q}(X_t; 1 - \alpha/2) \} \leq \hat{Q}_t(1 - \alpha)\}$;
</div>

Lemma A.1 Let $f : \mathbb { R } \to \mathbb { R }$ and $g : \mathbb { R } $ R be bounded functions such that either

1. f is non-increasing and g is non-decreasing,

2. or f is non-decreasing and g is non-increasing.

Then,for any random variable Y

$$
\mathbb {E} [ f (Y) g (Y) ] \leq \mathbb {E} [ f (Y) ] \mathbb {E} [ g (Y) ].
$$

The proof of this result is straightforward and can be found in Section A.10.

Lemma A.2 For any $\lambda \in \mathbb { R }$ and $t \in \mathbb { N }$ we have that

$$
\mathbb {E} \left[ \prod_ {s = 1} ^ {t} \exp (\lambda (\operatorname{err} _ {s} - \mathbb {E} [ \operatorname{err} _ {s} | A _ {s} ])) \right] \leq \exp (\lambda^ {2} / 2) \mathbb {E} \left[ \prod_ {s = 1} ^ {t - 1} \exp (\lambda (\operatorname{err} _ {s} - \mathbb {E} [ \operatorname{err} _ {s} | A _ {s} ])) \right].\tag{8}
$$

Proof: By conditioning on $\alpha _ { 1 }$ and $A _ { 1 } , \ldots , A _ { t }$ on both the left and right-hand side of (8) we may view these quantities as fixed. Thus, while for readability we do not denote this conditioning explicitly, the following calculations should be read as conditional on $\alpha _ { 1 }$ and $A _ { 1 } , \ldots , A _ { t }$ . Then,

$$
\begin{array}{l} \mathbb {E} \left[ \prod_ {s = 1} ^ {t} \exp (\lambda (\operatorname{err} _ {s} - \mathbb {E} [ \operatorname{err} _ {s} | A _ {s} ])) \right] \\ = \mathbb {E} \left[ \prod_ {s = 1} ^ {t - 1} \exp (\lambda (\operatorname{err} _ {s} - \mathbb {E} [ \operatorname{err} _ {s} | A _ {s} ])) \mathbb {E} \left[ \exp (\lambda (\operatorname{err} _ {t} - \mathbb {E} [ \operatorname{err} _ {t} | A _ {t} ])) \Bigg | \operatorname{err} _ {1}, \ldots , \operatorname{err} _ {t - 1} \right] \right]. \end{array}
$$

Recall that $\begin{array} { r } { \alpha _ { t } = \alpha _ { 1 } + \gamma \sum _ { s = 1 } ^ { t - 1 } ( \alpha - \mathrm { e r r } _ { s } ) } \end{array}$ is a deterministic function of $\alpha _ { 1 }$ and $\sum _ { s = 1 } ^ { t - 1 } \mathrm { e r r } _ { s }$ . So, we may define the functions $\begin{array} { r } { f ( \sum _ { s = 1 } ^ { t - 1 } \operatorname { e r r } _ { s } ) = \prod _ { s = 1 } ^ { t - 1 } \exp ( \lambda ( \operatorname { e r r } _ { s } - \mathbb { E } [ \operatorname { e r r } _ { s } | A _ { s } ] ) ) } \end{array}$ and

$$
\begin{array}{l} g (\sum_ {s = 1} ^ {t - 1} \mathsf {e r r} _ {s}) := \mathbb {E} \left[ \exp (\lambda (\mathsf {e r r} _ {t} - \mathbb {E} [ \mathsf {e r r} _ {t} | A _ {t} ])) | \mathsf {e r r} _ {1}, \ldots , \mathsf {e r r} _ {t - 1} \right] \\ \qquad = P _ {A _ {t}} (S (X _ {t}, Y _ {t}) \leq \hat {Q} (1 - \alpha_ {t})) \exp (- \lambda \mathbb {E} [ \mathsf {e r r} _ {t} | A _ {t} ]) \\ \qquad + (1 - P _ {A _ {t}} (S (X _ {t}, Y _ {t}) \leq \hat {Q} (1 - \alpha_ {t}))) \exp (\lambda (1 - \mathbb {E} [ \mathsf {e r r} _ {t} | A _ {t} ])), \end{array}
$$

where we emphasize that on the last line $A _ { t }$ and $\alpha _ { t }$ should be viewed as fixed quantities. Now, since $\alpha _ { t }$ is monotonically decreasing in $\textstyle \sum _ { s = 1 } ^ { t - 1 } \mathrm { e r r } _ { s }$ it should be clear that if $\lambda \geq 0$ then $g$ is non-increasing (resp. non-decreasing for $\lambda < 0 )$ and f is non-decreasing (resp. non-increasing for $\lambda < 0 )$ ). So, by Lemma A.1 we have that

$$
\begin{array}{l} \mathbb {E} \left[ \prod_ {s = 1} ^ {t - 1} \exp (\lambda (\mathrm{err} _ {s} - \mathbb {E} [ \mathrm{err} _ {s} | A _ {s} ])) \mathbb {E} \Big [ \exp (\lambda (\mathrm{err} _ {t} - \mathbb {E} [ \mathrm{err} _ {t} | A _ {t} ]))   \Big | \mathrm{err} _ {1}, \ldots , \mathrm{err} _ {t - 1} \Big ] \right] \\ \leq \mathbb {E} \left[ \prod_ {s = 1} ^ {t - 1} \exp (\lambda (\mathrm{err} _ {s} - \mathbb {E} [ \mathrm{err} _ {s} | A _ {s} ])) \right] \mathbb {E} \left[ \mathbb {E} \Big [ \exp (\lambda (\mathrm{err} _ {t} - \mathbb {E} [ \mathrm{err} _ {t} | A _ {t} ]))   \Big | \mathrm{err} _ {1}, \ldots , \mathrm{err} _ {t - 1} \Big ] \right] \\ = \mathbb {E} \left[ \prod_ {s = 1} ^ {t - 1} \exp (\lambda (\mathrm{err} _ {s} - \mathbb {E} [ \mathrm{err} _ {s} | A _ {s} ])) \right] \mathbb {E} [ \exp (\lambda (\mathrm{err} _ {t} - \mathbb {E} [ \mathrm{err} _ {t} | A _ {t} ])) ] \\ \leq \mathbb {E} \left[ \prod_ {s = 1} ^ {t - 1} \exp (\lambda (\mathrm{err} _ {s} - \mathbb {E} [ \mathrm{err} _ {s} | A _ {s} ])) \right] \exp (\lambda^ {2} / 2), \end{array}
$$

where the last inequality follows by Hoeffding’s lemma (see Lemma A.5).

The final result we will need in order to prove Theorem 4.1 is a large deviation bound for Markov chains.

Definition A.1 Let $\{ X _ { i } \} _ { i \in \mathbb { N } } \subseteq \mathcal { X }$ be a Markov chain with transition kernel P and stationary distribution π. Define the inner product space

$$
L ^ {2} (\mathcal {X}, \pi) = \left\{h: \int_ {\mathcal {X}} h (x) ^ {2} \pi (d x) <   \infty \right\}
$$

with inner product

$$
\langle h _ {1}, h _ {2} \rangle_ {\pi} = \int_ {\mathcal {X}} h _ {1} (x) h _ {2} (x) \pi (d x).
$$

For any $h \in L ^ { 2 } ( \mathcal { X } , \pi )$ , let

$$
L ^ {2} (\mathcal {X}, \pi) \ni P h := \int h (y) P (\cdot , d y).
$$

Then, we say that $\{ X _ { i } \} _ { i \in \mathbb { N } }$ has non-zero absolute spectral gap $1 - \eta i f$

$$
\eta := \sup \left\{\sqrt {\langle P h , P h \rangle_ {\pi}}: \langle h, h \rangle_ {\pi} = 1, \int_ {\mathcal {X}} h (x) \pi (d x) = 0 \right\} <   1.
$$

Theorem A.1 (Theorem 1 in [19]) Let $\{ X _ { i } \} _ { i \in \mathbb { N } } \subseteq \mathcal { X }$ be a stationary Markov chain with invariant distribution π and non-zero absolute spectral gap $1 - \eta > 0 .$ . Let $f _ { i } : \mathcal { X }  [ - C , C ]$ be a sequence offunctions with $\pi ( f _ { i } ) = 0$ and define $\textstyle { \dot { \sigma } } ^ { 2 } : = { \dot { \sum _ { i = 1 } ^ { n } \pi } } ( { \dot { f _ { i } } } ) / n$ . Then,for $\forall \epsilon > 0 ;$

$$
\mathbb {P} _ {\pi} \left(\frac {1}{n} \sum_ {i = 1} ^ {n} f _ {i} (X _ {i}) \geq \epsilon\right) \leq \exp \left(- \frac {n (1 - \eta) \epsilon^ {2} / 2}{(1 + \eta) \sigma^ {2} + 5 C \epsilon}\right).
$$

Finally, we are ready to prove Theorem 4.1.

Proof: [Proof of Theorem 4.1.] Write

$$
\begin{array}{l} \mathbb {P} \left(\left| \frac {1}{T} \sum_ {t = 1} ^ {T} \operatorname{err} _ {t} - \alpha \right| > \epsilon\right) \\ \leq \mathbb {P} \left(\left| \frac {1}{T} \sum_ {t = 1} ^ {T} \operatorname{err} _ {t} - \mathbb {E} [ \operatorname{err} _ {t} | A _ {t} ] \right| > \epsilon / 2\right) + \mathbb {P} \left(\left| \frac {1}{T} \sum_ {t = 1} ^ {T} \mathbb {E} [ \operatorname{err} _ {t} | A _ {t} ] - \alpha \right| > \epsilon / 2\right) \end{array}\tag{9}
$$

(10)

By applying lemma A.2 inductively we have that for all $\lambda > 0$

$$
\begin{array}{l} \mathbb {P} \left(\frac {1}{T} \sum_ {t = 1} ^ {T} \operatorname{err} _ {t} - \mathbb {E} [ \operatorname{err} _ {t} | A _ {t} ] > \epsilon / 2\right) \leq \exp (- T \lambda \epsilon / 2) \mathbb {E} \left[ \prod_ {t = 1} ^ {T} \exp (\lambda (\operatorname{err} _ {t} - \mathbb {E} [ \operatorname{err} _ {t} | A _ {t} ])) \right] \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qend{array}
$$

with an identical bound on the left tail. Choosing $\lambda = \epsilon / 2$ gives the bound

$$
\mathbb {P} \left(\left| \frac {1}{T} \sum_ {t = 1} ^ {T} \operatorname{err} _ {t} - \mathbb {E} [ \operatorname{err} _ {t} | A _ {t} ] \right| > \epsilon / 2\right) \leq 2 \exp (- T \epsilon^ {2} / 8).
$$

On the other hand, the second term in (10) can be bounded directly using Theorem A.1. 

## A.8 Approximate marginal coverage

In this section we prove Theorem 4.2.

Proof: [Proof of Theorem 4.2] Our proof follows similar steps to those presented in previous works on stochastic gradient descent under distribution shift [9, 35]. First, note that

$$
(\alpha_ {t + 1} - \alpha_ {A _ {t}} ^ {*}) ^ {2} = (\alpha_ {t} - \alpha_ {A _ {t}} ^ {*}) ^ {2} + 2 \gamma (\alpha - \mathfrak {e r r} _ {t}) (\alpha_ {t} - \alpha_ {A _ {t}} ^ {*}) + \gamma^ {2} (\alpha - \mathfrak {e r r} _ {t}) ^ {2}.
$$

Now recalling that $M ( \alpha _ { A _ { t } } ^ { * } | A _ { t } ) = \alpha$ , we find that

$$
\begin{array}{r l} & {- \mathbb {E} [ (\alpha - \mathsf {e r r} _ {t}) (\alpha_ {t} - \alpha_ {A _ {t}} ^ {*}) ] = \mathbb {E} [ \mathbb {E} [ (\mathsf {e r r} _ {t} - \alpha) (\alpha_ {t} - \alpha_ {A _ {t}} ^ {*}) | A _ {t}, \alpha_ {t} ] ]} \\ & {\qquad = \mathbb {E} [ (M (\alpha_ {t} | A _ {t}) - M (\alpha_ {A _ {t}} ^ {*} | A _ {t})) (\alpha_ {t} - \alpha_ {A _ {t}} ^ {*}) ]} \\ & {\qquad \geq \frac {1}{L} \mathbb {E} [ (M (\alpha_ {t} | A _ {t}) - M (\alpha_ {A _ {t}} ^ {*} | A _ {t})) ^ {2} ]} \\ & {\qquad = \frac {1}{L} \mathbb {E} [ (M (\alpha_ {t} | A _ {t}) - \alpha) ^ {2} ].} \end{array}
$$

Thus it follows that

$$
\begin{array}{l} 2 \gamma L ^ {- 1} \sum_ {t = 1} ^ {T} \mathbb {E} [ (M (\alpha_ {t} | A _ {t}) - \alpha) ^ {2} ] \leq \sum_ {t = 1} ^ {T} \mathbb {E} [ (\alpha_ {t} - \alpha_ {A _ {t}} ^ {*}) ^ {2} - (\alpha_ {t + 1} - \alpha_ {A _ {t}} ^ {*}) ^ {2} + \gamma^ {2} (\alpha - \mathrm{err} _ {t}) ^ {2} ] \\ \leq \sum_ {t = 1} ^ {T} \mathbb {E} [ (\alpha_ {t + 1} - \alpha_ {A _ {t + 1}} ^ {*}) ^ {2} - (\alpha_ {t + 1} - \alpha_ {A _ {t}} ^ {*}) ^ {2} ] + \mathbb {E} [ (\alpha_ {1} - \alpha_ {A _ {1}} ^ {*}) ^ {2} ] + \gamma^ {2} T \\ \leq \sum_ {t = 1} ^ {T} \mathbb {E} [ 2 \alpha_ {t + 1} (\alpha_ {A _ {t}} ^ {*} - \alpha_ {A _ {t + 1}} ^ {*}) ] + (\alpha_ {A _ {T + 1}} ^ {*}) ^ {2} + \mathbb {E} [ (\alpha_ {1} - \alpha_ {A _ {1}} ^ {*}) ^ {2} ] + \gamma^ {2} T \\ \leq \sum_ {t = 1} ^ {T} 2 (1 + \gamma) \mathbb {E} [ | \alpha_ {A _ {t + 1}} ^ {*} - \alpha_ {A _ {t}} ^ {*} | ] + (\alpha_ {A _ {T + 1}} ^ {*}) ^ {2} + \mathbb {E} [ (\alpha_ {1} - \alpha_ {A _ {1}} ^ {*}) ^ {2} ] + \gamma^ {2} T, \end{array}
$$

where the last inequality follows from Lemma 4.1. So, re-arranging we get the inequality

$$
\begin{array}{l} \frac {1}{T} \sum_ {t = 1} ^ {T} \mathbb {E} [ (M (\alpha_ {t} | A _ {t}) - \alpha) ^ {2} ] \\ \leq \frac {L}{2 T \gamma} \left(\sum_ {t = 1} ^ {T} 2 (1 + \gamma) \mathbb {E} [ | \alpha_ {A _ {t + 1}} ^ {*} - \alpha_ {A _ {t}} ^ {*} | ] + (\alpha_ {A _ {T + 1}} ^ {*}) ^ {2} + \mathbb {E} [ (\alpha_ {1} - \alpha_ {A _ {1}} ^ {*}) ^ {2} ] + \gamma^ {2} T\right). \end{array}
$$

Finally, since $\{ ( A _ { t } , \alpha _ { t } ) \} _ { t \in \mathbb { N } }$ is stationary we may let $T \to \infty$ to get that

$$
\mathbb {E} [ (M (\alpha_ {t} | A _ {t}) - \alpha) ^ {2} ] \leq \frac {L (1 + \gamma)}{\gamma} \mathbb {E} [ | \alpha_ {A _ {t + 1}} ^ {*} - \alpha_ {A _ {t}} ^ {*} | ] + \frac {L \gamma}{2}
$$

as claimed.

## A.9 Bounds on B and $\pmb { \sigma _ { B } ^ { 2 } }$

In this section we bound the constants B and $\sigma _ { B } ^ { 2 }$ appearing in the statement of Theorem 4.1. Let

$$
\epsilon_ {1} = \sup _ {k \in \{0, 1, 2, \dots \}} \sup _ {a \in \mathcal {A}} \mathbb {E} [ | \alpha_ {A _ {T - k}} ^ {*} - \alpha_ {A _ {T - k - 1}} ^ {*} | | A _ {T} = a ]
$$

$$
\text { and } \epsilon_ {2} = \sup _ {k \in \{0, 1, 2, \dots \}} \sup _ {a \in \mathcal {A}} \mathbb {E} [ (\alpha_ {A _ {T - k}} ^ {*} - \alpha_ {A _ {T - k - 1}} ^ {*}) ^ {2} | A _ {T} = a ].
$$

Then, our main result is Lemma A.4 which shows that

$$
B \leq C (\gamma + \gamma^ {- 1} (\epsilon_ {1} + \epsilon_ {2})) \quad \text { and } \quad \sigma_ {B} ^ {2} \leq B ^ {2},\tag{11}
$$

where the constant C depends on how close $M ( \cdot | a )$ is to the ideal linear function $M ( p | a ) = p$

Plugging (11) into Theorem 4.1 gives a concentration inequality for $\begin{array} { r } { | T ^ { - 1 } \sum _ { t = 1 } ^ { T } \mathrm { e r r } _ { t } - \alpha | } \end{array}$ . In particular, suppose we use an optimal stepsize of $\gamma \propto \sqrt { \epsilon _ { 1 } }$ . Then, combining (11) with Theorem 4.1 roughly tells us that

$$
\left| \frac {1}{T} \sum_ {t = 1} ^ {T} \operatorname{err} _ {t} - \alpha \right| \leq O \left(\max \left\{\frac {1}{\sqrt {T}}, \frac {\sqrt {\epsilon_ {1}}}{\sqrt {T (1 - \eta)}}, \frac {\sqrt {\epsilon_ {1}}}{T (1 - \eta)} \right\}\right).\tag{12}
$$

As a comparison it may be instructive to note that the more naive bound given in Proposition 4.1 can be written as

$$
\left| \frac {1}{T} \sum_ {t = 1} ^ {T} \operatorname{err} _ {t} - \alpha \right| \leq O \left(\frac {1}{T \gamma}\right) = O \left(\frac {1}{T \sqrt {\epsilon_ {1}}}\right).\tag{13}
$$

A sharp reader may notice that the naive bound given in (13) actually goes to 0 faster in $T$ than the HMM-based bound shown in $( 1 2 )$ . While this is true, the bound (13) has the highly undesirable property of increasing in $1 / \sqrt { \epsilon _ { 1 } } ,$ , i.e. the bound increases as the size of the distribution shift decreases. On the other hand, the HMM-based bound has the more intuitive property of decreasing with the distribution shift.

The only remaining issue is to determine the size of $\sqrt { \epsilon _ { 1 } / ( 1 - \eta ) }$ . To provide some insight into this quantity note that there are two main regimes in which we expect $\begin{array} { r } { | T ^ { - 1 } \sum _ { t = 1 } ^ { T } \mathrm { e r r } _ { t } - \alpha | } \end{array}$ to be small:

1. Environments in which the state $A _ { t }$ changes frequently, but $| \alpha _ { A _ { t + 1 } } ^ { * } - \alpha _ { A _ { t } } ^ { * } |$ is always small. In this case it is reasonable to expect $1 - \eta$ to not be too small and so we anticipate that (12) will give a reasonable bound.

2. Environments in which the state changes very infrequently. In this case $\{ A _ { t } \} _ { t \in \mathbb { N } }$ will mix slowly and so we expect $1 - \eta$ to be quite small. Additionally, we also have that $\alpha _ { A _ { t + 1 } } ^ { * } = \alpha _ { A } ^ { * }$ a large proportion of the time and thus $\epsilon _ { 1 }$ will also be small. As a result, it is not immediately clear what (12) tells us about $\begin{array} { r } { | T ^ { - 1 } \sum _ { t = 1 } ^ { T } \mathrm { e r r } _ { t } - \alpha | } \end{array}$ . Below we give one simple example that demonstrates that (12) can also be a reasonable bound in this instance.

Example A.1 Let $\{ A _ { t } \} _ { t \in \mathbb { N } }$ be the Markov chain with states $\{ 1 , \ldots , n \}$ and transition matrix

$$
P = \left(p - \frac {1 - p}{n - 1}\right) I + \frac {1 - p}{n - 1} 1 1 ^ {T},
$$

where $p \in [ 0 , 1 ]$ is taken to be very close to 1. Let $\Delta : = \mathrm { m a x } _ { i \neq j } | \alpha _ { i } ^ { * } - \alpha _ { i } ^ { * } |$ . Then, we have that $\epsilon _ { 1 } , \epsilon _ { 2 } \leq \Delta ( 1 - p )$ . Moreover, note that this chain has spectral gap $1 - \eta \cong 1 - p .$ Thus, (12) simplifies to

$$
\left| \frac {1}{T} \sum_ {t = 1} ^ {T} e r r _ {t} - \alpha \right| \leq O \left(\max \left\{\frac {1}{\sqrt {T}}, \frac {\sqrt {\Delta}}{T \sqrt {1 - p}} \right\}\right).\tag{14}
$$

In particular,for $T > \Delta / ( 1 - p )$ wefind that the error sequence concentrates at a rate of ${ \cal O } ( 1 / \sqrt { T } )$ which is consistent with the behaviour of an i.i.d. Bernoulli sequence. Finally, to understand this restriction on T note that given a starting state $j \in \{ 1 , \ldots , n \}$ we expect $\alpha _ { t }$ to contract towards $\alpha _ { j } ^ { * }$ at a rate of $( 1 - \gamma )$ and therefore to have that

$$
\frac {1}{T} \sum_ {t = 1} ^ {T} | \alpha_ {t} - \alpha_ {j} ^ {*} | \propto \frac {1}{T} \sum_ {t = 1} ^ {T} (1 - \gamma) ^ {t - 1} | \alpha_ {1} - \alpha_ {j} ^ {*} | \leq \frac {\Delta}{T \gamma} = \frac {\sqrt {\Delta}}{T \sqrt {1 - p}},
$$

where here we assumed that $\alpha _ { 1 } \in \{ \alpha _ { 1 } ^ { * } , \ldots , \alpha _ { n } ^ { * } \}$ . Thus, the second term in the maximum in $( I 4 )$ can be seen as accountingfor the rate ofcovergence $o f \alpha _ { t } t o \alpha _ { j } ^ { * }$ during the time that the Markov chain is in state j and given that $\alpha _ { 1 }$ starts at some $\alpha _ { i } ^ { * } , 1 \leq i \leq n .$

We now derive (11).

Lemma A.3 Assume that ∃0 $< c < 1 / ( 2 \gamma )$ such thatfor all $a \in { \mathcal { A } }$ and all $p \in [ - \gamma , 1 + \gamma ]$

$$
| M (p | a) - M (\alpha_ {a} ^ {*} | a) | \geq c | p - \alpha_ {a} ^ {*} |.
$$

Then, for all $a \in \mathcal { A } , k \in \{ 0 , 1 , 2 , . . . \}$ , and $T \in \mathbb { N }$

$$
\begin{array}{l} \mathbb {E} [ (\alpha_ {1} - \alpha_ {A _ {1}} ^ {*}) ^ {2} | A _ {1 + k} = a ] \\ \leq (1 - 2 c \gamma) ^ {T - 1} \mathbb {E} [ (\alpha_ {1} - \alpha_ {A _ {1}} ^ {*}) ^ {2} | A _ {T + k} = a ] \\ + \sum_ {t = 2} ^ {T} (1 - 2 c \gamma) ^ {T - t} \bigg (\gamma^ {2} + 2 (1 + \gamma) \mathbb {E} [ | \alpha_ {A _ {t - 1}} ^ {*} - \alpha_ {A _ {t}} ^ {*} | | A _ {T + k} = a ] + \mathbb {E} [ (\alpha_ {A _ {t - 1}} ^ {*} - \alpha_ {A _ {t}} ^ {*}) ^ {2} | A _ {T + k} = a ] \bigg). \end{array}
$$

Furthermore, $i f$ we assume that $\forall a \in { \mathcal { A } }$ and $k \in \{ 0 , 1 , 2 , \ldots \}$

$$
\mathbb {E} [ | \alpha_ {A _ {t - k}} ^ {*} - \alpha_ {A _ {t - k - 1}} ^ {*} | | A _ {t} = a ] \leq \epsilon_ {1} a n d \mathbb {E} [ (\alpha_ {A _ {t - k}} ^ {*} - \alpha_ {A _ {t - k - 1}} ^ {*}) ^ {2} | A _ {t} = a ] \leq \epsilon_ {2},
$$

then we find that

$$
\mathbb {E} [ (\alpha_ {1} - \alpha_ {A _ {1}} ^ {*}) ^ {2} | A _ {1 + k} = a ] \leq \frac {1}{2 c \gamma} \left(\gamma^ {2} + 2 (1 + \gamma) \epsilon_ {1} + \epsilon_ {2}\right).
$$

Proof: Fix any $T \in \mathbb { N } ,$ . Since $\{ ( \alpha _ { t } , A _ { t } ) \} _ { t \in \mathbb { N } }$ is stationary we have that

$$
\mathbb {E} [ (\alpha_ {1} - \alpha_ {A _ {1}} ^ {*}) ^ {2} | A _ {1 + k} ] = \mathbb {E} [ (\alpha_ {T} - \alpha_ {A _ {T}} ^ {*}) ^ {2} | A _ {T + k} ].
$$

Now note that

$$
\begin{array}{l} \mathbb {E} [ (\alpha_ {T} - \alpha_ {A _ {T}} ^ {*}) ^ {2} | A _ {T + k} ] = \mathbb {E} [ (\alpha_ {T} - \alpha_ {A _ {T - 1}} ^ {*}) ^ {2} | A _ {T + k} ] + 2 \mathbb {E} [ (\alpha_ {T} - \alpha_ {A _ {T - 1}} ^ {*}) (\alpha_ {A _ {T - 1}} ^ {*} - \alpha_ {A _ {T}} ^ {*}) | A _ {T + k} ] \\ \qquad + \mathbb {E} [ (\alpha_ {A _ {T - 1}} ^ {*} - \alpha_ {A _ {T}} ^ {*}) ^ {2} | A _ {T + k} ] \\ \qquad \leq \mathbb {E} [ (\alpha_ {T} - \alpha_ {A _ {T - 1}} ^ {*}) ^ {2} | A _ {T + k} ] + 2 (1 + \gamma) \mathbb {E} [ | \alpha_ {A _ {T - 1}} ^ {*} - \alpha_ {A _ {T}} ^ {*} | | A _ {T + k} ] \\ \qquad + \mathbb {E} [ (\alpha_ {A _ {T - 1}} ^ {*} - \alpha_ {A _ {T}} ^ {*}) ^ {2} | A _ {T + k} ], \end{array}
$$

where on the last line we have applied Lemma 4.1. The first term above can be bounded as

$$
\begin{array}{r l} & {\mathbb {E} [ (\alpha_ {T} - \alpha_ {A _ {T - 1}} ^ {*}) ^ {2} | A _ {T + k} ]} \\ & {\leq \mathbb {E} [ (\alpha_ {T - 1} - \alpha_ {A _ {T - 1}} ^ {*}) ^ {2} | A _ {T + k} ] + 2 \mathbb {E} [ \gamma (\alpha - \mathtt {e r r} _ {T - 1}) (\alpha_ {T - 1} - \alpha_ {A _ {T - 1}} ^ {*}) | A _ {T + k} ] + \gamma^ {2},} \end{array}
$$

where we additionally have that

$$
\begin{array}{r l} & {\mathbb {E} [ (\alpha - \mathtt {e r r} _ {T}) (\alpha_ {T - 1} - \alpha_ {A _ {T - 1}} ^ {*}) | A _ {T + k} ]} \\ & {= \mathbb {E} [ (\alpha - \mathbb {E} [ \mathtt {e r r} _ {T - 1} | A _ {T - 1}, \alpha_ {T - 1}, A _ {T + k} ]) (\alpha_ {T - 1} - \alpha_ {A _ {T - 1}} ^ {*}) | A _ {T + k} ]} \\ & {= \mathbb {E} [ (M (\alpha_ {A _ {T - 1}} ^ {*} | A _ {T _ {1}}) - M (\alpha_ {T - 1} | A _ {T - 1})) (\alpha_ {T - 1} - \alpha_ {A _ {T - 1}} ^ {*}) | A _ {T + k} ]} \\ & {\leq - c \mathbb {E} [ (\alpha_ {T - 1} - \alpha_ {A _ {T - 1}} ^ {*}) ^ {2} | A _ {T + k} ].} \end{array}
$$

Whence,

$$
\mathbb {E} [ (\alpha_ {T} - \alpha_ {A _ {T - 1}} ^ {*}) ^ {2} | A _ {T + k} ] \leq (1 - 2 c \gamma) \mathbb {E} [ (\alpha_ {T - 1} - \alpha_ {A _ {T - 1}} ^ {*}) ^ {2} | A _ {T + k} ] + \gamma^ {2},
$$

and plugging this into our first inequality yields

$$
\begin{array}{r l} & {\mathbb {E} [ (\alpha_ {T} - \alpha_ {A _ {T}} ^ {*}) ^ {2} | A _ {T + k} ] \leq (1 - 2 c \gamma) \mathbb {E} [ (\alpha_ {T - 1} - \alpha_ {A _ {T - 1}} ^ {*}) ^ {2} | A _ {T + k} ] + \gamma^ {2}} \\ & {\qquad + 2 (1 + \gamma) \mathbb {E} [ | \alpha_ {A _ {T - 1}} ^ {*} - \alpha_ {A _ {T}} ^ {*} | | A _ {T + k} ] + \mathbb {E} [ (\alpha_ {A _ {T - 1}} ^ {*} - \alpha_ {A _ {T}} ^ {*}) ^ {2} | A _ {T + k} ].} \end{array}
$$

Repeating this argument inductively gives

$$
\begin{array}{l} \mathbb {E} [ (\alpha_ {T} - \alpha_ {A _ {T}} ^ {*}) ^ {2} | A _ {T + k} = a ] \\ \leq (1 - 2 c \gamma) ^ {T - 1} \mathbb {E} [ (\alpha_ {1} - \alpha_ {A _ {1}} ^ {*}) ^ {2} | A _ {T + k} = a ] \\ + \sum_ {t = 2} ^ {T} (1 - 2 c \gamma) ^ {T - t} \bigg (\gamma^ {2} + 2 (1 + \gamma) \mathbb {E} [ | \alpha_ {A _ {t - 1}} ^ {*} - \alpha_ {A _ {t}} ^ {*} | | A _ {T + k} = a ] + \mathbb {E} [ (\alpha_ {A _ {t - 1}} ^ {*} - \alpha_ {A _ {t}} ^ {*}) ^ {2} | A _ {T + k} = a ] \bigg). \end{array}
$$

The final part of the lemma follows by sending $T \to \infty$

Lemma A.4 Assume thatfor all $a \in { \mathcal { A } }$ and $p \in [ - \gamma , 1 + \gamma ] , M ( \cdot | a )$ admits the second order Taylor expansion

$$
M (p | a) - M (\alpha_ {a} ^ {*} | a) = C _ {a} ^ {1} (p - \alpha_ {a} ^ {*}) + C _ {p, a} ^ {2} (p - \alpha_ {a} ^ {*}) ^ {2},
$$

where $0 < c _ { 1 } \leq C _ { a } ^ { 1 } \leq C _ { 1 } < 1 / \gamma a n d | C _ { p , a } ^ { 2 } | \leq C _ { 2 }$ . Then, for all $T \in \mathbb { N }$ and $a \in { \mathcal { A } } ,$

$$
\begin{array}{l} | \mathbb {E} [ \mathrm{err} _ {1} | A _ {1} = a ] - \alpha | \leq C _ {1} (1 - \gamma c _ {1}) ^ {T - 1} \mathbb {E} [ | \alpha_ {1} - \alpha_ {A _ {1}} ^ {*} | | A _ {T} = a ] \\ \qquad + \sum_ {t = 1} ^ {T - 1} C _ {1} C _ {2} \gamma (1 - c _ {1} \gamma) ^ {T - t - 1} \mathbb {E} [ (\alpha_ {t} - \alpha_ {A _ {t} ^ {*}}) ^ {2} | A _ {T} = a ] \\ \qquad + \sum_ {t = 1} ^ {T - 1} C _ {1} (1 - c _ {1} \gamma) ^ {T - t - 1} \mathbb {E} [ | \alpha_ {A _ {t + 1}} ^ {*} - \alpha_ {A _ {t}} ^ {*} | | A _ {T} ] + C _ {2} \mathbb {E} [ (\alpha_ {T} - \alpha_ {A _ {T}} ^ {*}) ^ {2} | A _ {T} = a ]. \end{array}
$$

Furthermore, suppose the assumptions ofLemma A.3 hold and that $\forall a \in { \mathcal { A } }$ and $k \in \{ 0 , 1 , 2 , \ldots \}$ ,

$$
\mathbb {E} [ | \alpha_ {A _ {T - k}} ^ {*} - \alpha_ {A _ {T - k - 1}} ^ {*} | | A _ {T} = a ] \leq \epsilon_ {1}   a n d   \mathbb {E} [ (\alpha_ {A _ {T - k}} ^ {*} - \alpha_ {A _ {T - k - 1}} ^ {*}) ^ {2} | A _ {T} = a ] \leq \epsilon_ {2}.
$$

Then ∀a $\in { \mathcal { A } } ,$

$$
\left| \mathbb {E} \left[ \operatorname{err} _ {1} \mid A _ {1} = a \right] - \alpha \right| \leq \left(C _ {1} C _ {2} \frac {1}{c _ {1}} + C _ {2}\right) \frac {1}{2 c \gamma} \left(\gamma^ {2} + 2 (1 + \gamma) \epsilon_ {1} + \epsilon_ {2}\right) + \frac {C _ {1}}{c _ {1} \gamma} \epsilon_ {1}.
$$

Proof: Fix any $T \in \mathbb { N } ,$ . Since $\{ ( \mathsf { e r r } _ { t } , A _ { t } ) \} _ { t \in \mathbb { N } }$ is stationary we have that

$$
\mathbb {E} [ \operatorname{err} _ {1} | A _ {1} = a ] = \mathbb {E} [ \operatorname{err} _ {T} | A _ {T} = a ].
$$

Then, by Taylor expanding $M ( \cdot | A _ { T } )$ we find that

$$
\begin{array}{l} | \mathbb {E} [ \mathrm{err} _ {T} | A _ {T} = a ] - \alpha | = \big | \mathbb {E} [ M (\alpha_ {T} | A _ {T}) - M (\alpha_ {A _ {T}} ^ {*} | A _ {T}) | A _ {T} ] \big | \\ \leq \big | \mathbb {E} [ C _ {A _ {T}} ^ {1} (\alpha_ {T} - \alpha_ {A _ {T}} ^ {*}) | A _ {T} ] \big | + \mathbb {E} [ C _ {\alpha_ {T}, A _ {T}} ^ {2} (\alpha_ {T} - \alpha_ {A _ {T}} ^ {*}) ^ {2} | A _ {T} ] \\ \leq \big | \mathbb {E} [ C _ {A _ {T}} ^ {1} (\alpha_ {T} - \alpha_ {A _ {T}} ^ {*}) | A _ {T} ] \big | + C _ {2} \mathbb {E} [ (\alpha_ {T} - \alpha_ {A _ {T}} ^ {*}) ^ {2} | A _ {T} ]. \end{array}
$$

The first term above can be further bounded as

$$
\begin{array}{l} \big | \mathbb {E} [ C _ {A _ {T}} ^ {1} (\alpha_ {T} - \alpha_ {A _ {T}} ^ {*}) | A _ {T} ] \big | \\ = \Big | \mathbb {E} [ C _ {A _ {T}} ^ {1} (\alpha_ {T - 1} + \gamma (\alpha - \mathtt {e r r} _ {T - 1}) - \alpha_ {A _ {T - 1}} ^ {*}) | A _ {T} ] + \mathbb {E} [ C _ {A _ {T}} ^ {1} (\alpha_ {A _ {T - 1}} ^ {*} - \alpha_ {A _ {T}} ^ {*}) | A _ {T} ] \Big | \\ \leq \Big | \mathbb {E} [ C _ {A _ {T}} ^ {1} (\alpha_ {T - 1} - \alpha_ {A _ {T - 1}} ^ {*}) ] + \gamma \mathbb {E} [ C _ {A _ {T}} ^ {1} (M (\alpha_ {A _ {T - 1}} ^ {*} | A _ {T - 1}) - M (\alpha_ {T - 1} | A _ {T - 1})) | A _ {T} ] \Big | \\ \qquad + C _ {1} \mathbb {E} [ | \alpha_ {A _ {T - 1}} ^ {*} - \alpha_ {A _ {T}} ^ {*} | | A _ {T} ] \\ = \Big | \mathbb {E} [ C _ {A _ {T}} ^ {1} (1 - \gamma C _ {A _ {T - 1}} ^ {1}) (\alpha_ {T - 1} - \alpha_ {A _ {T - 1}} ^ {*}) | A _ {T} ] \Big | + C _ {1} C _ {2} \gamma \mathbb {E} [ (\alpha_ {T - 1} - \alpha_ {A _ {T - 1}} ^ {*}) ^ {2} | A _ {T} ] \\ \qquad + C _ {1} \mathbb {E} [ | \alpha_ {A _ {T - 1}} ^ {*} - \alpha_ {A _ {T}} ^ {*} | | A _ {T} ]. \end{array}
$$

The desired result follows by repeating this process inductively. Finally, the last part of the Lemma follows by sending $T \to \infty$ and applying the result of Lemma ${ \mathrm { A } } . 3$

As a final aside we remark that in the main text we claimed that in the ideal case where $M ( p | a ) = p$ for all $p \in [ 0 , 1 ]$ this bound can be replaced by

$$
\left| \mathbb {E} \left[ \operatorname{err} _ {1} \mid A _ {1} = a \right] - \alpha \right| \leq 2 \left(\gamma + \gamma^ {- 1} \epsilon_ {1}\right).
$$

This can be justified by using the fact that in this case we have that for all $p \in [ - \gamma , 1 + \gamma ]$

$$
M (p | a) - M (\alpha_ {a} ^ {*} | a) = (p - \alpha_ {a} ^ {*}) + C _ {p, a} ^ {2}
$$

with $| C _ { p , a } ^ { 2 } | \leq \gamma$ . The desired result then follows by repeating the argument of Lemma A.4.

## A.10 Technical lemmas

Proof: [Proof of Lemma A.1:] We assume without loss of generality that f is non-decreasing and g is non-increasing as otherwise one can simply multiply both f and $g \ b y - 1$

Let $g ^ { U } : = \operatorname* { s u p } \{ g ( y ) : f ( y ) > \mathbb { E } [ f ( Y ) ]$ and $g ^ { L } : = \qquad $ inf $\{ g ( y ) : f ( y ) \leq \mathbb { E } [ f ( Y ) ]$ ]. By the monotonicity of $f$ and g we clearly have that $\begin{array} { r } { \dot { g } ^ { L } \ge \dot { g } ^ { U } } \end{array}$ . Therefore,

$$
\begin{array}{r l} & {\mathbb {E} [ f (Y) g (Y) ] - \mathbb {E} [ f (Y) ] \mathbb {E} [ g (Y) ] = \mathbb {E} [ (f (Y) - \mathbb {E} [ f (Y) ]) g (Y) ]} \\ & {\leq \mathbb {E} [ (f (Y) - \mathbb {E} [ f (Y) ]) g ^ {L} \mathbb {1} _ {f (Y) \leq \mathbb {E} [ f (Y) ]} ] + \mathbb {E} [ (f (Y) - \mathbb {E} [ f (Y) ]) g ^ {U} \mathbb {1} _ {f (Y) > \mathbb {E} [ f (Y) ]} ]} \\ & {\leq \mathbb {E} [ (f (Y) - \mathbb {E} [ f (Y) ]) g ^ {L} \mathbb {1} _ {f (Y) \leq \mathbb {E} [ f (Y) ]} ] + \mathbb {E} [ (f (Y) - \mathbb {E} [ f (Y) ]) g ^ {L} \mathbb {1} _ {f (Y) > \mathbb {E} [ f (Y) ]} ]} \\ & {= 0,} \end{array}
$$

as desired.



$$
\mathbb {E} [ \exp (\lambda X) ] \leq \exp \left(\lambda^ {2} \frac {(b - a) ^ {2}}{8}\right).
$$

Lemma A.5 [Hoeffding’s Lemma [18]] Let X be a mean 0 random variable such that $X \in [ a , b ]$ almost surely. Then,for all $\lambda \in \mathbb { R }$