---
title: "2025-Almeida-High-Probability-Risk-Control-Covariate-Shift"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2025-Almeida-High-Probability-Risk-Control-Covariate-Shift.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# High Probability Risk Control Under Covariate Shift

Duarte C. Almeida duartecaladoalmeida@tecnico.ulisboa.pt Instituto Superior T´ecnico, Universidade de Lisboa Instituto de Telecomunica¸c˜oes Feedzai

Jo˜ao Bravo joao.bravo@feedzai.com Feedzai

Jacopo Bono jacopo.bono@feedzai.com Feedzai

Pedro Bizarro Feedzai

pedro.bizarro@feedzai.com

M´ario A. T. Figueiredo Instituto Superior T´ecnico, Universidade de Lisboa Instituto de Telecomunica¸c˜oes

mario.figueiredo@tecnico.ulisboa.pt

Editor: Khuong An Nguyen, Zhiyuan Luo, Harris Papadopoulos, Tuwe L¨ofstr¨om, Lars Carlsson and Henrik Bostr¨om

## Abstract

Distribution-free uncertainty quantification is an emerging field, which encompasses risk control techniques in finite sample settings with minimal distributional assumptions, mak ing it suitable for high-stakes applications. In particular, high-probability risk control methods, namely the learn then test (LTT) framework, use a calibration set to control multiple risks with high confidence. However, these methods rely on the assumption that the calibration and target distributions are identical, which can pose challenges, for example, when controlling label-dependent risks under the absence of labeled target data. In this work, we propose a novel extension of LTT that handles covariate shifts by directly weighting calibration losses with importance weights. We validate our method on a synthetic fraud detection task, aiming to control the false positive rate while minimizing false negatives, and on an image classification task, to control the miscoverage of a set predictor while minimizing the average set size. The results show that our approach consistently yields less conservative risk control than existing baselines based on rejection sampling, which results in overall lower false negative rates and smaller prediction sets.

Keywords: High-probability risk control, covariate shift, learn then test, distribution-free uncertainty quantification, conformal prediction.

## 1. Introduction

Machine learning is increasingly used to automate high-risk and high-stakes decisions (e.g., in healthcare or finance). These decisions are often associated with specific risks representing statistical measures of inaccuracy that must be controlled to meet safety, regulatory, quality, or other standards. For example, fraud detection systems should be properly tuned to detect fraudulent transactions while avoiding hindering legitimate economic activity.

Distribution-free uncertainty quantification is an emerging field that encompasses risk control techniques in finite sample settings with minimal distributional assumptions (Angelopoulos and Bates, 2023). A cornerstone method of this family is conformal prediction (CP) (Shafer and Vovk, 2008), which calibrates a set predictor to control the miscoverage probability. Letting X and Y denote the feature and label spaces, respectively, CP uses a calibration set $\mathcal { D } = \{ ( X _ { i } , Y _ { i } ) \} _ { i = 1 } ^ { n } \subset \mathcal { X } \times \mathcal { Y }$ to generate prediction sets $ { \mathcal { C } } ( X _ { n + 1 } )$ for a new test data point $\left( X _ { n + 1 } , Y _ { n + 1 } \right)$ . Assuming only exchangeability of $\{ ( X _ { i } , Y _ { i } ) \} _ { i = 1 } ^ { n + 1 }$ (its joint distribution is permutation-invariant), CP provides a coverage/validity guarantee: $\mathbb { P } ( Y _ { n + 1 } \in \mathcal { C } ( X _ { n + 1 } ) ) \ge 1 - \alpha$ . However, CP does not guarantee the stronger conditional validity property $\mathbb { P } ( Y _ { n + 1 } \in \mathcal { C } ( X _ { n + 1 } ) \mid X _ { n + 1 } = x ) \ge 1 - \alpha , \forall x \in \mathcal { X }$ . While this property cannot be attained in general, relaxations such as group-conditional and class-conditional coverage ofer guarantees within specific feature-label subsets (Barber et al., 2021; Gibbs et al., 2025) . Furthermore, calibration-set validity is always achievable, as concentration bounds for the calibration-set conditional coverage level exist (Vovk, 2012).

Under the same exchangeability assumption, CP can be generalized to control other risks beyond miscoverage, via the calibration of some (possibly multidimensional) parameter λ. If the risk can be expressed as the expectation of a lower-bounded loss function $L ( \cdot , \cdot ; \lambda ) : \mathcal { X } \times \mathcal { Y }  \mathbb { R }$ , which is coordinate-wise non-increasing with respect to λ for all $( x , y ) \in \mathcal { X } \times \mathcal { Y }$ , conformal risk control (CRC) can be applied to compute λ<sup>ˆ</sup> that guarantees $\mathbb { E } [ L ( X _ { n + 1 } , Y _ { n + 1 } ; \hat { \lambda } ) ] \leq \alpha$ (Angelopoulos et al., 2024).

The probability and expectation in the aforementioned guarantees are taken over both the new test point and the calibration set. To rigorously control the risk, the calibration procedure must be applied each time a new test point is introduced. If calibration is only done periodically, there may be time frames where the risk exceeds the desired threshold due to an anomalous calibration sample, which could be problematic in scenarios where risk control should be as strict as possible. An alternative approach is to perform high-probability risk control (HPRC) (Angelopoulos et al., 2025; Bates et al., 2021), which bounds the probability of risk violations occurring due to a “bad” calibration set below some threshold δ. Methods for this purpose operate under slightly stronger distributional assumptions, namely, that the calibration set is i.i.d. according to the target distribution.

When models are deployed over data from a target distribution that may difer from that of the training data (the source distribution), a significant performance degradation may occur (Kouw and Loog, 2019). This is the case, e.g., when a fraud detection system is applied to transactions from a new geographical setting, or if an image classifier trained on a particular type of image $( e . g .$ , photographs) is used on other kinds of image $( e . g .$ drawings). Furthermore, the risk control techniques mentioned above cannot be applied over source calibration data, as distribution shifts violate important underlying assumptions (e.g., exchangeability and i.i.d.). While labeled target data are often unavailable, due to slow or costly labeling processes, unlabeled target data could still be used for risk control.

In this work, we introduce a novel adaptation of high-probability risk control methods, specifically of the learn then test (LTT) approach (Angelopoulos et al., 2025), that addresses covariate shift between the source and target distributions in the presence of unlabeled target data. Making use of recent advancements in hypothesis testing, we prove how calibration losses can be weighted by importance weights to achieve risk control. We experimentally validate our approach in two settings. The first is a synthetic fraud detection scenario in which a model trained on a source distribution is calibrated to control the false positive rate (FPR) on a target distribution while minimizing the false negative rate (FNR). The second setting involves an image classification task, where a model trained on a source distribution is deployed on a target domain representing a specific data subpopulation. Here, the covariate shift assumption may not hold, and the goal is to calibrate a set predictor to control the miscoverage probability while minimizing the average set size, as considered by Park et al. (2022). Our results show that our approach is less conservative than the existing covariate shift-adapted HPRC baseline in both cases (i.e., smaller FNR and average set size), while achieving the desired risk control in the synthetic setting and closing the risk gap in the second scenario.

Related Work. This work is part of a broader research avenue aimed at adapting risk control methods to handle distribution shifts. Notably, Tibshirani et al. (2019) proposed a weighting scheme for quantile calculation in CP that uses importance weights to preserve the original coverage guarantee under covariate shift. Barber et al. (2023) examined the impact of both data-independent and dependent weighting schemes on the coverage gap, providing important theoretical guidelines for designing such schemes to bridge the gap under arbitrary violations of the exchangeability assumption. This approach has been extended to conformal risk control by Farinhas et al. (2024). In the context of high-probability risk control, Park et al. (2022) introduced rejection sampling to align the calibration and target distributions under covariate shift while aiming specifically for the control of the miscoverage risk. This approach was later extended to other use cases by Zollo et al. (2024); although diferent from our method, it will be fully explained in later sections for completeness.

## 2. Background: High-Probability Risk Control

In this section, we present a review of some foundational principles of HPRC. Let X and Y denote the feature and label spaces, respectively, and let P be a probability measure on a suitable measurable space $( { \mathcal { X } } \times { \mathcal { Y } } , { \mathcal { F } } )$ For convenience, we will also use the notation P to refer to the corresponding distribution. Furthermore, consider a calibration set $\mathcal { D } =$ $\{ ( X _ { i } , Y _ { i } ) \} _ { i = 1 } ^ { n } \subset { \mathcal { X } } \times { \mathcal { Y } }$ , where $( X _ { i } , Y _ { i } ) \stackrel { \mathrm { i . i . d . } } { \sim } \mathbb { P } , \forall i \in \{ 1 , \dots , n \}$ . Let $L ( \cdot , \cdot ; \lambda ) : \mathcal { X } \times \mathcal { Y } $ R be a measurable loss parameterized by λ, and define $R _ { \mathbb { P } } ( \lambda ) = \mathbb { E } _ { ( X , Y ) \sim \mathbb { P } } [ L ( X , Y ; \lambda ) ]$ as the risk (expected loss) under P. For conciseness, we include the subscript P in the expectation defining the risk only when the underlying probability measure is not clear from the context.

A core HPRC approach is learn then test (LTT) (Angelopoulos et al., 2025). Given a predefined subset Λ of the parameter space, LTT uses a calibration set to generate a subset $\hat { \Lambda } \subseteq \Lambda$ such that the risk is uniformly controlled over all its elements, i.e.,

$$
\mathbb {P} \Bigl (\sup _ {\lambda \in \hat {\Lambda}} R (\lambda) \leq \alpha \Bigr) \geq 1 - \delta ,
$$

for some confidence level $\delta \in ( 0 , 1 )$ , where the randomness is over the calibration set. Once $\hat { \Lambda }$ is determined, a single parameter can be selected based on additional optimality criteria. For instance, in general detection (binary classification) systems, one might control the false positive rate and select the parameter in $\hat { \Lambda }$ that minimizes the false negative rate (or vice versa). Moreover, this approach does not require the risk or loss to be monotonic with respect to λ, which may even be any general mathematical object.

Hypothesis tests serve as the main building blocks of this procedure; specifically, for each value of $\lambda \in \Lambda$ , the following null hypothesis is considered:

$$
\mathcal {H} _ {0} (\lambda , \alpha): R (\lambda) > \alpha .
$$

If a rejection rule over the calibration set bounds the probability of a false rejection below $1 - \delta$ , then rejecting the null hypothesis based on it provides $1 - \delta$ confidence that λ controls the risk below α. Such procedures can be designed using valid p-values.

Definition 1 (p-value) (Angelopoulos et al., 2025) Let $\mathcal { H } _ { 0 }$ be a null hypothesis. A statistic $p$ is said to be a valid p-value for $\mathcal { H } _ { 0 }$ if it is super-uniform under $\mathcal { H } _ { 0 } , \ i . e .$ ，

$$
\mathbb {P} _ {\mathcal {H} _ {0}} (p \leq \delta) \leq \delta , \forall \delta \in [ 0, 1 ].
$$

Thus, rejecting $\mathcal { H } _ { 0 } ~ i f ~ p \leq \delta$ ensures that a false rejection occurs with probability at most δ.

The following theorem establishes how to generate p-values from concentration inequalities (such as Hoefding’s inequality).

Theorem 2 (Bates et al., 2021) Let $g ( \cdot , \cdot ) : \mathbb { R } ^ { 2 } \to \mathbb { R }$ be a function satisfying the condition

$$
\mathbb {P} \big (\hat {R} (\lambda) \leq t \big) \leq g \big (t, R (\lambda) \big), \forall t \in \mathbb {R},\tag{1}
$$

where $\begin{array} { r } { \hat { R } ( \lambda ) = \frac { 1 } { n } \sum _ { i = 1 } ^ { n } L ( X _ { i } , Y _ { i } ; \lambda ) } \end{array}$ represents the empirical risk over the calibration set and $\mathbb { E } [ L ( X _ { i } , Y _ { i } ; \lambda ) ] = R ( \lambda ) , \forall i \in \{ 1 , \dots , n \}$ . Then, $g \bigl ( \hat { R } ( \lambda ) , \alpha \bigr )$ is a valid p-value for the null hypothesis $\mathcal { H } _ { 0 } ( \lambda , \alpha ) : R ( \lambda ) > \alpha$

In some cases, the distribution of the empirical risk can be exactly specified, making it possible to replace potentially loose non-parametric bounds with an exact expression on the r.h.s. of Equation (1), leading to more powerful p-values. For instance, if the loss function is almost surely supported on $\{ 0 , 1 \}$ , then $n { \hat { R } } ( \lambda )$ follows a binomial distribution. The 0-1 loss scenario is ubiquitous, arising when controlling the miscoverage or the FPR.

Theorem 3 (Clopper-Pearson p-value) (Clopper and Pearson, 1934; Park et al., 2022) Let $L ( \cdot , \cdot ; \lambda ) : \mathcal { X } \times \mathcal { Y }  \{ 0 , 1 \}$ be a measurable loss function parametrized by λ. Let $\begin{array} { r } { \hat { R } ( \lambda ) = \frac { 1 } { n } \sum _ { i = 1 } ^ { n } L ( X _ { i } , Y _ { i } ; \lambda ) } \end{array}$ be the empirical risk computed over an i.i.d. calibration set such that $\mathbb { E } [ \bar { L } ( \bar { X } _ { i } , Y _ { i } ; \lambda ) ] = R ( \lambda ) , \forall i \in \{ 1 , \dots , n \}$ . Then, the statistic

$$
p (\lambda , \alpha) = F _ {\mathrm{Bin} (n, \alpha)} \big (n \hat {R} (\lambda) \big),
$$

where $F _ { \mathrm { B i n } ( n , \alpha ) }$ is the cumulative distribution function of the binomial distribution with n trials and success probability α, is a valid p-value for $\mathcal { H } _ { 0 } ( \lambda , \alpha ) : R ( \lambda ) > \alpha$

Obtaining $\hat { \Lambda }$ requires ensuring that all its elements control the risk below α with $1 - \delta$ confidence, rather than being $( 1 - \delta )$ -confident for each $\lambda \in { \hat { \Lambda } }$ . In hypothesis testing terminology, this is referred to as controlling the family-wise error rate (FWER) (Angelopoulos et al., 2025) at level $\delta ,$ which is defined as

$$
\operatorname{FWER} (\hat {\Lambda}) = \mathbb {P} \left(\exists \lambda \in \hat {\Lambda}: \mathcal {H} _ {0} (\lambda , \alpha) \text { holds }\right).
$$

Such approaches are called FWER-controlling and consist of strategies to aggregate p-values generated by testing the set of hypotheses $\{ \mathcal { H } _ { 0 } ( \lambda , \alpha ) : \lambda \in \Lambda \}$ . If Λ is discrete, one possible approach is fixed-sequence testing (FST) (Angelopoulos et al., 2025). In FST, hypotheses are tested in a predefined order, and all corresponding values of $\lambda$ in $\hat { \Lambda }$ are gathered until the first non-rejection at level $\delta$ occurs. The risk-controlling subset is thus defined by $\hat { \Lambda } = \{ \lambda _ { i } ^ { \prime } \} _ { i = 1 } ^ { k ^ { * } - 1 }$ , where

$$
k ^ {*} = \min \{k: p (\lambda_ {i} ^ {\prime}, \alpha) \leq \delta , \forall i <   k \},
$$

for a predefined ordering $( \lambda _ { 1 } ^ { \prime } , . . . \lambda _ { | \Lambda | } ^ { \prime } )$ of Λ. For this method to be useful, safer values for λ should be tested first. When the monotonicity relationship between λ and $R ( \lambda )$ is unclear, split fixed-sequence testing (SFST) (Angelopoulos et al., 2025; Laufer-Goldshtein et $\mathrm { a l . } .$ 2023) can be used. In this approach, the calibration set is divided into two disjoint subsets: one for defining an ordering of Λ and another for applying FST.

LTT can also be extended to simultaneously control multiple risks by considering $\mathrm { ~ a ~ p - }$ value for each individual risk and taking the maximum of all p-values. Additionally, when p-values are almost surely monotonically non-increasing or non-decreasing in λ for a fixed calibration set $\mathcal { D } ,$ it is possible to consider an interval $[ \lambda _ { - } , \lambda _ { + } ]$ as $\Lambda$ . In this case, the iterative nature of FST/SFST can be avoided by directly computing the risk-controlling half-subset $\hat { \Lambda }$ using any standard root-finding algorithm (Bates et al., 2021).

## 3. High-Probability Risk Control under Covariate Shift

Consider the problem of asserting risk control over a target distribution $\mathbb { P } _ { \mathrm { t a r g e t } }$ , from which only an unlabeled sample $\mathcal { T } = \{ X _ { i } \} _ { i = 1 } ^ { n _ { t } }$ is available. Standard risk control methods generally cannot be applied in this setting if the loss function depends on the label $Y$ , as it usually does. If we possess a labeled sample $\boldsymbol { \mathcal { S } } = \{ ( X _ { i } , Y _ { i } ) \} _ { i = 1 } ^ { n _ { s } }$ drawn from a possibly diferent source distribution $\mathbb { P } _ { \mathrm { s o u r c e } }$ , we should ask if the application of these methods on $s$ yields the desired statistical confidence guarantees.

To test $\mathcal { H } _ { 0 } ( \lambda , \alpha ) : R ( \lambda ) > \alpha$ at a significance level $\delta ,$ a general strategy is to use p-values, which require that $\mathbb { E } [ L ( X _ { i } , Y _ { i } ; \lambda ) ] = R ( \lambda )$ for any data point $( X _ { i } , Y _ { i } )$ in the calibration set. Therefore, without further assumptions, we are only guaranteed to control the source risk

$$
R _ {\mathbb {P} _ {\mathrm{source}}} (\lambda) = \mathbb {E} _ {(X, Y) \sim \mathbb {P} _ {\mathrm{source}}} [ L (X, Y; \lambda) ].
$$

For the risk to be controlled over the target distribution, the relation $R _ { \mathbb { P } _ { \mathrm { t a r g e t } } } ( \lambda ) \leq R _ { \mathbb { P } _ { \mathrm { s o u r c e } } } ( \lambda )$ should hold, which is a strong assumption that may not be verified in general.

## 3.1. The Covariate Shift Assumption and Existing HPRC Methods

Fortunately, it is possible to make use of the source dataset $s$ under some further assumptions on $\mathbb { P } _ { \mathrm { s o u r c e } }$ and $\mathbb { P } _ { \mathrm { t a r g e t } }$ . In particular, the covariate shift assumption renders this problem tractable by assuming equal feature-conditional probability measures.

Definition 4 (Covariate shift) (Qui˜noreo-Candela et al., 2009) Two probability measures $\mathbb { P }$ and $\mathbb { Q }$ defined on some measurable space $( \mathcal { X } \times \mathcal { Y } , \mathcal { F } )$ are said to difer by a covariate shift if the corresponding feature-conditional probability measures coincide, $i . e .$

$$
d \mathbb {P} (y \mid x) = d \mathbb {Q} (y \mid x), \quad \forall (x, y) \in \mathcal {X} \times \mathcal {Y}.
$$

Furthermore, under mild regularity conditions, we can define the notion of importance weight between two probability measures (also known as the Radon-Nikodym derivative).

Definition 5 (Importance weight) (Resnick, 1999) Let $\mathbb { P }$ and $\mathbb { Q }$ be probability measures defined on a measurable space $( \mathcal { X } \times \mathcal { Y } , \mathcal { F } )$ such that Q is absolutely continuous with respect to P $( \mathbb { Q } \ll \mathbb { P } )$ , i.e.,

$$
\mathbb {P} (A) = 0 \Rightarrow \mathbb {Q} (A) = 0, \quad \forall A \in \mathcal {F}.
$$

Define the importance weight function as

$$
w (x, y) = \frac {d \mathbb {Q}}{d \mathbb {P}} (x, y), \quad \forall (x, y) \in s u p p (\mathbb {P}).
$$

Then, it holds that

$$
\mathbb {Q} (\mathcal {A}) = \int_ {\mathcal {A}} w (x, y) d \mathbb {P} (x, y), \forall \mathcal {A} \in \mathcal {F}.
$$

Under the covariate shift assumption, the importance weight function depends only on the marginal distributions over $\mathcal { X }$ (Yu and Szepesv´ari, 2012),

$$
w (x, y) = \frac {d \mathbb {P} _ {\mathrm{target}}}{d \mathbb {P} _ {\mathrm{source}}} (x, y) = \frac {d \mathbb {P} _ {\mathrm{target} , X}}{d \mathbb {P} _ {\mathrm{source} , X}} (x) := w (x),
$$

where $\mathbb { P } _ { \mathrm { s o u r c e } , X }$ and $\mathbb { P } _ { \mathrm { t a r g e t } , X }$ denote the induced source and target marginals over $\mathcal { X } .$ . Moreover, the importance weight can be estimated only from unlabeled source target data several well-established methods (You et al., 2019; Sugiyama et al., 2007; Huang et al., 2006).

To correct covariate shift between the source and target distributions, Park et al. (2022) propose aligning the calibration set with the target distribution via rejection sampling (Robert and Casella, 2004), a classical technique to generate samples from a target distribution using another (so-called proposal) distribution. The definition and correctness of this procedure are established by the following theorem.

Theorem 6 (Rejection Sampling) (Robert and Casella, 2004) Let $\mathbb { P }$ and $\mathbb { Q }$ be the target and proposal, respectively, probability measures defined on a measurable space $( { \mathcal { X } } \times { \mathcal { Y } } , { \mathcal { F } } )$ such that $\mathbb { Q } \ll \mathbb { P }$ . Define $\begin{array} { r } { \dot { w } = \frac { d \mathbb Q } { d \mathbb P } } \end{array}$ as the corresponding importance weight function, assumed to be bounded above by some constant $B < \infty$ . Let $( X , Y ) \sim \mathbb { P }$ , and define $( X ^ { \prime } , Y ^ { \prime } )$ as the pair $( X , Y )$ accepted under the event $U \ \leq \ w ( X , Y ) / B$ , where $U \sim U n i f o r m [ 0 , 1 ]$ is independent of $( X , Y )$ ; that is, $( X ^ { \prime } , Y ^ { \prime } ) = ( X , Y ) \mid w ( X ) / B \leq U$ . Then, $( X ^ { \prime } , Y ^ { \prime } ) \sim \mathbb { Q }$

Given an importance weight function $w : \mathcal { X }  \mathbb { R }$ and an upper bound $B \geq \operatorname* { s u p } \{ w ( x ) , x \in$ $\mathcal { X } \}$ , both estimated from unlabeled source and target data, rejection sampling can be applied to the labeled source set $\boldsymbol { \mathcal { S } }$ to produce a new i.i.d. sample $S ^ { \prime }$ from $\mathbb { P } _ { \mathrm { t a r g e t } }$ , assuming these estimates are accurate. This allows the application of standard risk control procedures as if $S ^ { \prime }$ was directly drawn from the target distribution.

Applying rejection sampling as described, the expected size of $S ^ { \prime }$ (the set of non-rejected samples) is inversely proportional to $B ,$ , since

$$
\mathbb {E} \left[ \sum_ {i = 1} ^ {n _ {s}} \mathbf {1} \left\{U _ {i} \leq \frac {w (X _ {i})}{B} \right\} \right] = \frac {n _ {s}}{B},
$$

where $\mathbf { 1 } \{ \cdot \}$ denotes the indicator function. If B is large, the retained sample may become too small, yielding overly conservative p-values that fail to identify useful risk-controlling values of $\lambda .$ This can degrade performance with respect to complementary metrics; for instance, a low FPR may come at the cost of a higher false negative rate and vice versa.

## 3.2. HPRC under Covariate Shift via Importance Weighting

In this section, we propose a diferent approach to HPRC under covariate shift, addressing the limitations of rejection sampling. We discuss a new method to control risks over the joint distribution (Section 3.2.1) and extend it to conditional risks (Section 3.2.2).

## 3.2.1. Controlling Risks over the Joint Feature/Label Distribution

We first propose an alternative way to deal with covariate shift when controlling risks that are the expectation of a loss $L ( X , Y ; \lambda )$ over the joint feature and label distribution induced by $\mathbb { P } _ { \mathrm { t a r g e t } }$ (e.g., miscoverage). In such cases, these can be written as expectations of the importance-weighted loss $w ( X ) L ( X , Y ; \lambda )$ over $\mathbb { P } _ { \mathrm { s o u r c e } }$ (Qui˜noreo-Candela et al., 2009):

$$
R (\lambda) = \mathbb {E} _ {(X, Y) \sim \mathbb {P} _ {\mathrm{target}}} [ L (X, Y; \lambda) ] = \mathbb {E} _ {(X, Y) \sim \mathbb {P} _ {\mathrm{source}}} [ w (X) L (X, Y; \lambda) ].\tag{2}
$$

In this way, we can perform risk control using the entirety of the labeled source data by considering the sample of importance-weighted losses $\{ w ( X _ { i } ) L ( X _ { i } , Y _ { i } ; \lambda ) \} _ { i = 1 } ^ { n _ { s } }$ , where $( X _ { i } , Y _ { i } ) \sim \mathbb { P } _ { \mathrm { s o u r c e } } , \forall i \in [ n _ { s } ]$ . We formalize this approach in the next theorem.

Theorem 7 Let $\mathbb { P } _ { s o u r c e }$ and $\mathbb { P } _ { t a r g e t }$ be probability measures on $( \mathcal { X } \times \mathcal { Y } , \mathcal { F } )$ such that $\mathbb { P } _ { t a r g e t } \ll$ $\mathbb { P } _ { s o u r c e . }$ , and assume they difer by a covariate shift. Let $\begin{array} { r } { w = \frac { d \mathbb { P } _ { t a r g e t } } { d \mathbb { P } _ { s o u r c e } } } \end{array}$ be the corresponding importance weight function, and let $L ( \cdot , \cdot ; \lambda ) : \mathcal { X } \times \mathcal { Y }  \mathbb { R }$ be a measurable loss parametrized by λ. Then, any p-value for $\mathcal { H } _ { 0 } ^ { \prime } ( \lambda , \alpha ) : \mathbb { E } _ { \mathbb { P } _ { s o u r c e } } [ w ( X ) L ( X , Y ; \lambda ) ] > \alpha$ is also a p-value for $\mathcal { H } _ { 0 } ( \lambda , \alpha ) : \mathbb { E } _ { \mathbb { P } _ { t a r g e t } } [ L ( X , Y ; \lambda ) ] > \alpha$

Proof By Equation (2), the conditions in $\mathcal { H } _ { 0 } ( \lambda , \alpha )$ and $\mathcal { H } _ { 0 } ^ { \prime } ( \lambda , \alpha )$ are equivalent. Thus, for any valid p-value $p ( \lambda , \alpha )$ for $\mathcal { H } _ { 0 } ^ { \prime } ( \lambda , \alpha )$ , we have $\mathbb { P } _ { \mathcal { H } _ { 0 } ( \lambda , \alpha ) } ( p ( \lambda , \alpha ) \leq \delta ) = \mathbb { P } _ { \mathcal { H } _ { 0 } ^ { \prime } ( \lambda , \alpha ) } ( p ( \lambda , \alpha ) \leq$ $\delta ) \leq \delta , \forall \delta \in [ 0 , 1 ]$

It is important to recognize that, while this method retains all the source data, the distribution of the weighted losses may be more challenging to handle. For instance, the introduction of weights can destroy desirable properties of the original loss that allow the use of very tight p-values—e.g., it may break the 0–1 structure and significantly broaden the range of possible values. Nevertheless, recent advances in testing by betting provide highly variance-adaptive p-values that work very well in practice, such as the Waudby-Smith–Ramdas (WSR) p-value (Waudby-Smith and Ramdas, 2024).

Theorem 8 (WSR p-value) (Bates et al., 2021; Waudby-Smith and Ramdas, 2024) Let $L ( \cdot , \cdot ; \lambda ) : \mathcal { X } \times \mathcal { Y }  [ 0 , 1 ]$ be a measurable loss parametrized by λ and let $\mathcal { D } = \{ ( X _ { i } , Y _ { i } ) \} _ { i = 1 } ^ { n }$ be a calibration set such that

$$
\mathbb {E} \left[ L \left(X _ {i}, Y _ {i}; \lambda\right) \right] = \mathbb {E} \left[ L \left(X _ {i}, Y _ {i}; \lambda\right) \mid L \left(X _ {i - 1}, Y _ {i - 1}; \lambda\right), \dots , L \left(X _ {1}, Y _ {1}; \lambda\right) \right] = R (\lambda), \forall i \in \{1, \dots , n \}.
$$

Define the following statistics:

$$
\hat {\mu} _ {i} (\lambda) = \frac {1 / 2 + \sum_ {j = 1} ^ {i} L (X _ {j} , Y _ {j} ; \lambda)}{1 + i}, \quad \hat {\sigma} _ {i} ^ {2} (\lambda) = \frac {1 / 4 + \sum_ {j = 1} ^ {i} (L (X _ {j} , Y _ {j} ; \lambda) - \hat {\mu} _ {j} (\lambda)) ^ {2}}{1 + i},
$$

$$
\nu_ {i} (\lambda) = \min \left\{1, \sqrt {\frac {2 \log (1 / \delta)}{n \hat {\sigma} _ {i - 1} ^ {2} (\lambda)}} \right\}.
$$

Furthermore, define the capital process $\{ K _ { i } ( \lambda , \alpha ) \} _ { i = 1 } ^ { n }$ as

$$
\mathcal {K} _ {i} (\lambda , \alpha) = \prod_ {j = 1} ^ {i} \bigl (1 - \nu_ {j} (\lambda) \bigl (L (X _ {j}, Y _ {j}; \lambda) - \alpha \bigr) \bigr).
$$

Then, the statistic

$$
p (\lambda , \alpha) = \left(\max _ {i \in \{1, \dots , n \}} \mathcal {K} _ {i} (\lambda , \alpha)\right) ^ {- 1}
$$

is a p-value for $\mathcal { H } _ { 0 } ( \lambda , \alpha ) : R ( \lambda ) > \alpha$

Although this p-value assumes that the loss lies between 0 and 1, it can be readily extended to our setting. If L is supported on $[ l , u ]$ , then the importance-weighted loss wL is supported on $[ l ^ { \prime } , u ^ { \prime } ]$ , where $l ^ { \prime } = \mathrm { m i n } ( 0 , B l )$ and $u ^ { \prime } = \operatorname* { m a x } ( 0 , B u )$ . It is then suficient to test the equivalent hypothesis

$$
\mathcal {H} _ {0} (\lambda , \alpha): \frac {R (\lambda) - l ^ {\prime}}{u ^ {\prime} - l ^ {\prime}} > \frac {\alpha - l ^ {\prime}}{u ^ {\prime} - l ^ {\prime}},
$$

using the rescaled importance-weighted losses $\left\{ \frac { w ( X _ { i } ) L ( X _ { i } , Y _ { i } ; \lambda ) - l ^ { \prime } } { u ^ { \prime } - l ^ { \prime } } \right\} _ { i = 1 } ^ { n _ { s } }$

Due to the sequential nature of the procedure, the order of the calibration data can afect the outcome when the source dataset is a mixture of subsources (e.g., diferent types of images). If such subsources are processed in bulk and the early part of the capital process is computed over samples from a subsource for which the risk is controlled, the capital process may surpass $\delta ^ { - 1 }$ prematurely, leading to a rejection even though the risk is not controlled over the entire source distribution. To solve this, the data can be randomized B times, yielding B capital processes $\{ \{ \mathcal { K } _ { i } ^ { ( b ) } ( \lambda , \alpha ) \} _ { i = 1 } ^ { n } \} _ { b = 1 } ^ { B }$ , which can be averaged into a new process $\begin{array} { r } { \mathcal { K } _ { i } ( \lambda , \alpha ) : = B ^ { - 1 } \sum _ { b = 1 } ^ { B } \mathcal { K } _ { i } ^ { ( b ) } ( \lambda , \alpha ) } \end{array}$ (Waudby-Smith and Ramdas, 2024).

## 3.2.2. Controlling Conditional Risks

Many risks are defined over distributions other than the joint feature and label distribution. For example, the FPR of a binary classifier $f , { \mathrm { F P R } } = \mathbb { P } ( f ( X ) = 1 \mid Y = 0 ) = \mathbb { E } [ \mathbf { 1 } \{ f ( X ) =$ $1 \} | \ Y = 0 ]$ , is evaluated over the conditional distribution of X given $Y = 0$ . Under covariate shift between $\mathbb { P } _ { \mathrm { s o u r c e } }$ and $\mathbb { P } _ { \mathrm { t a r g e t } }$ , it follows that

$$
d \mathbb {P} _ {\mathrm{target}, X \mid y} (x \mid y) = w (x) \frac {d \mathbb {P} _ {\mathrm{source} , Y}}{d \mathbb {P} _ {\mathrm{target} , Y}} (y) d \mathbb {P} _ {\mathrm{source}, X \mid y} (x \mid y),
$$

showing that covariate shift does not hold if the source and target class priors are diferent. In general, this reweighting procedure does not directly apply to risks defined over distributions other than the joint. However, it can be adapted for a broad class of risks, as shown in the following theorem.

Theorem 9 Consider the null hypothesis $\mathcal { H } _ { 0 } ( \lambda , \alpha ) : \mathbb { E } _ { \mathbb { P } _ { t a r q e t } } [ L ( X , Y ; \lambda ) | ( X , Y ) \in \mathcal { A } ( \lambda ) ] >$ α, where $\mathcal { A } ( \lambda ) \in \mathcal { X } \times \mathcal { Y }$ is a non-zero probability set and $L ( \cdot , \cdot ; \lambda ) : \mathcal { X } \times \mathcal { Y } $ R is a measurable loss parametrized by λ. Then, any p-value for $\mathcal { H } _ { 0 } ^ { \prime } ( \lambda , \alpha ) : \mathbb { E } _ { \mathbb { P } _ { s o u r c e } } [ L ^ { \prime } ( X , Y ; \lambda ) ] > \alpha$ is also a p-value for $\mathcal { H } _ { 0 } ( \lambda , \alpha )$ , where

$$
L ^ {\prime} (X, Y; \lambda) = w (X) \left(L (X, Y; \lambda) \mathbf {1} \{(X, Y) \in \mathcal {A} (\lambda) \} + \alpha \mathbf {1} \{(X, Y) \notin \mathcal {A} (\lambda) \}\right).
$$

Proof Developing the condition in $\mathcal { H } _ { 0 } ( \lambda , \alpha )$ , we have:

$$
\begin{array}{r l} & {\mathbb {E} _ {\mathbb {P} _ {\mathrm{target}}} [ L (X, Y; \lambda) | (X, Y) \in \mathcal {A} (\lambda) ] > \alpha} \\ {\Leftrightarrow} & {\mathbb {E} _ {\mathbb {P} _ {\mathrm{target}}} [ L (X, Y; \lambda) \mathbf {1} \{(X, Y) \in \mathcal {A} (\lambda) \} ] > \alpha \mathbb {P} _ {\mathrm{target}} ((X, Y) \in \mathcal {A} (\lambda))} \\ {\Leftrightarrow} & {\mathbb {E} _ {\mathbb {P} _ {\mathrm{target}}} [ L (X, Y; \lambda) \mathbf {1} \{(X, Y) \in \mathcal {A} (\lambda) \} ] > \alpha (1 - \mathbb {P} _ {\mathrm{target}} ((X, Y) \notin \mathcal {A} (\lambda)))} \\ {\Leftrightarrow} & {\mathbb {E} _ {\mathbb {P} _ {\mathrm{target}}} [ L (X, Y; \lambda) \mathbf {1} \{(X, Y) \in \mathcal {A} (\lambda) \} ] + \alpha \mathbb {P} _ {\mathrm{target}} ((X, Y) \notin \mathcal {A} (\lambda)) > \alpha} \\ {\Leftrightarrow} & {\mathbb {E} _ {\mathbb {P} _ {\mathrm{target}}} [ L (X, Y; \lambda) \mathbf {1} \{(X, Y) \in \mathcal {A} (\lambda) \} + \alpha \mathbf {1} \{(X, Y) \notin \mathcal {A} (\lambda) \} ] > \alpha .} \end{array}
$$

The result then follows from applying Theorem $7$ to the loss $L ( X , Y ; \lambda ) { \bf 1 } \{ ( X , Y ) ~ \in ~$ $\mathcal { A } ( \lambda ) \} + \alpha \mathbf { 1 } \{ ( X , Y ) \notin \mathcal { A } ( \lambda ) \}$

This result shows that any conditional risk can be reformulated as a risk over the joint feature-label distribution for the purpose of hypothesis testing. In the setting of a binary classifier $f ( \cdot ; \lambda ) : \mathcal { X } \to \{ 0 , 1 \}$ , many common classification risks fall within this family. For instance, the FPR corresponds to taking $L ( X , Y ; \lambda ) = \mathbf { 1 } \{ f ( X ; \lambda ) = 1 \}$ and $\mathcal { A } ( \lambda ) = \{ ( x , y ) \in$ $\mathcal { X } \times \mathcal { Y } : \boldsymbol { y } = 0 \}$ . Similarly, for the false discovery rate, we have $L ( X , Y ; \lambda ) = \mathbf { 1 } \{ Y = 0 \}$ and $\mathcal { A } ( \lambda ) = \{ ( x , y ) \in \mathcal { X } \times \mathcal { Y } : f ( x ; \lambda ) = 1 \}$

## 4. Results and Discussion

## 4.1. Experimental Setup

## 4.1.1. Tasks and Datasets

We evaluate our method on two tasks. The first consists in controlling the FPR of a transaction fraud detection model below $\alpha = 0 . 0 5$ with confidence $( 1 - \delta ) = 0 . 9 5$ . The model has the form $f ( x ; \lambda ) = \mathbf { 1 } \{ s ( x ) > \lambda \}$ , where $s : \mathcal { X } \to [ 0 , 1 ]$ is a trained score function that captures the likelihood of a transaction being fraudulent. We apply fixed sequence testing (FST) over a set $\Lambda = \{ s _ { ( i / 1 0 0 0 ) } \} _ { i = 1 } ^ { 1 0 0 0 }$ , where $s _ { ( q ) }$ denotes the sample q-quantile of the score distribution on source data. We test Λ in decreasing order and choose the smallest risk-controlling λ to minimize the FNR.

In this first task, we simulate a situation in which new unlabeled transaction data becomes available and previously collected labeled data are used to ensure risk control. For that purpose, we partition the Bank Account Fraud (BAF) dataset (Jesus et al., 2022) into three domains based on the credit risk of the client performing the transaction (low, medium, and high). Each domain is treated as the target in turn, with the remaining two combined to form the source. All domains are designed to difer solely in terms of covariate shift. Details on the partitioning procedure are provided in Appendix A. Furthermore, we use 70% of each domain’s data for model training and the remaining 30% for risk control. We use LightGBM classifiers (Ke et al., 2017), trained with 5-fold cross-validation, and tune hyperparameters to maximize the AUROC using Optuna’s implementation of TPE (Watanabe, 2023; Akiba et al., 2019). The hyperparameter grid is specified in Appendix F.

In the second task, we control the miscoverage of an image set predictor of the form $f ( x ; \lambda ) = \{ y \in \mathcal { Y } : s ( x , y ) > \lambda \}$ below 0.10 with confidence 0.95, where $s : \mathcal { X } \times \mathcal { Y }  [ 0 , 1 ]$ is a trained score function such that $s ( x , y )$ estimates the posterior probability of class y for an image x. We perform FST over $\Lambda = \{ s _ { ( i / 1 0 0 0 ) } ^ { * } \} _ { i = 1 } ^ { 1 0 0 0 }$ , where $s _ { ( q ) } ^ { * }$ denotes the empirical q-quantile of the true-class scores on the source data. Here, Λ is tested in increasing order and the largest risk-controlling $\lambda \in \Lambda$ is selected to minimize the average set size.

We use the DomainNet dataset (Peng et al., 2019), which consists of 6 domains: clipart, real, infograph, painting, sketch, and quickdraw. We consider each domain as target and all domains as sources, simulating a setting where a model is trained on broad data but is deployed on some (potentially unknown) subpopulation. We use the same ResNet model as Park et al. (2022) and use the original test and validation splits for risk control.

## 4.1.2. Estimation of Importance Weights

To estimate importance weights, we apply kernel mean matching (KMM), which minimizes the maximum mean discrepancy (MMD) between empirical kernel mean embeddings of the target distribution and the reweighted source distribution (Qui˜noreo-Candela et al., 2009). Given a reproducing kernel Hilbert space (RKHS) H associated with a universal kernel $k ,$ KMM estimates the weights at the source datapoints $\{ w ( x _ { j } ) : x _ { j } \in S \}$ that minimize

$$
\left\| \frac {1}{n _ {t}} \sum_ {x _ {i} \in \mathcal {T}} k (x _ {i}, \cdot) - \frac {1}{n _ {s}} \sum_ {x _ {j} \in \mathcal {S}} w (x _ {j})   k (x _ {j}, \cdot) \right\| _ {\mathcal {H}} ^ {2}
$$

subject to w $( x _ { j } ) \geq 0 , \forall x _ { j } \in S$ , and $\begin{array} { r } { | \frac { 1 } { n _ { s } } \sum _ { x _ { j } \in \mathcal { S } } w ( x _ { j } ) - 1 | \leq \epsilon } \end{array}$ . Following Huang et al. (2006), we set $\epsilon = 1 - 1 / \sqrt { n _ { s } }$

We consider a Gaussian kernel $k ( x , x ^ { \prime } ) = \exp ( - \| x - x ^ { \prime } \| ^ { 2 } / \sigma ^ { 2 } )$ , using one-hot encodings for categorical variables when computing distances. We set $\sigma$ to the median of pairwise distances between all the points in the source and target datasets, following Sugiyama et al. (2009). Additionally, the maximum admissible importance weight is set at 10,000. To accelerate this procedure, we use the very fast KMM (VFKMM) algorithm proposed by Chandra et al. (2016), averaging importance weights computed across bootstrap samples of size 1000 from the source dataset, with the number of bootstrap samples set to ensure that each point is sampled at least once with probability 0.9999. Moreover, we consider the maximum estimated importance weight as an estimate for the upper bound B.

The second image classification task poses challenges due to the high dimensionality of the input, afecting the stability of importance weight estimates and increasing runtime. These challenges can be attenuated by considering a lower-dimensional feature transformation $h : \mathbb { R } ^ { n }  \mathbb { R } ^ { d }$ with $d \ll n ,$ , such that X and $Y$ are conditionally independent given $h ( X )$ One such transformation is $h ( \boldsymbol { x } ) \ = \ \left( \mathbb { P } ( \boldsymbol { Y } = y _ { 1 } \mid \boldsymbol { X } = \boldsymbol { x } ) , \ldots , \mathbb { P } ( \boldsymbol { Y } = y _ { d } \mid \boldsymbol { X } = \boldsymbol { x } ) \right)$ ， where $\mathcal { Y } = \{ y _ { 1 } , \ldots , y _ { d } \}$ is the label space (Stojanov et al., 2019). This motivates our choice to use the model’s predicted class scores as features for importance weight computation.

Park et al. (2022) propose a method to account for uncertainty in the estimation of importance weights. In short, the observations are binned into K equal-mass bins $\{ B _ { i } \} _ { i = 1 } ^ { K }$ according to an estimate of the importance weights. Then, a δ-upper confidence bound

$$
w ^ {+} (x) = \frac {\mathbb {P} _ {\mathrm{target}} ^ {+} (X \in B (x)) + E}{\left(\mathbb {P} _ {\mathrm{source}} ^ {-} (X \in B (x)) - E\right) _ {+}}
$$

can be obtained for $w ( x )$ , where $B ( x )$ is the bin containing $x , \ \mathbb { P } ^ { + }$ and $\mathbb { P } ^ { - }$ denote $\delta / 2$ Clopper-Pearson upper and lower-confidence bounds, respectively, and $E$ is a predefined smoothness constant to account for the histogram approximation. However, there are no theoretical guidelines for choosing K and E. Thus, we opt for more established procedures and proceed under the assumption that the estimates are accurate.

## 4.1.3. Baselines and Evaluation Procedure

We compare our proposed importance-weighted LTT method based on the WSR p-value (Waudby-Smith and Ramdas, 2024) (LTT-IW) against two baselines: LTT with rejection sampling and the Clopper-Pearson p-value (Clopper and Pearson, 1934) (LTT-RS), and LTT without importance weights (LTT) (i.e., directly controlling the source risk). Variations of our method for diferent p-values can be found in Appendix B.

At the beginning of the procedure, we estimate the importance weights using the source and target splits allocated for risk control. We then run 1,000 iterations of LTT, each time over a diferent subsample of source data drawn without replacement. In the first task, we use the entire target dataset to evaluate the resulting target risk, while in the second baseline (where the target domain is contained in the source domain), we only use the part that was not sampled. To evaluate sample eficiency, we vary the source sample size, but always use the full source and target datasets to get the most accurate importance weight estimates. Finally, we estimate (1 − δ)-quantiles of the risk estimates computed over all iterations to assess if risk control is achieved. To evaluate how conservative the methods are, we also report the mean FNR and average set size obtained over all runs. In addition, Appendix C contains a brief analysis of the computational cost of the proposed method.

## 4.2. Results

Figure 1 reports the 0.95-quantile of the FPR for diferent values of the source sample size N. Ignoring covariate shift (LTT) can either make risk control overly conservative (for target domains low and medium), or outright invalid, as is the case of target domain high, where the risk is controlled at twice the intended level. Both weighted variants (LTT-IW and LTT-RS) control the FPR in nearly all cases, with the exception being in medium, where a residual risk gap of ≈ 0.0025 likely stems from errors in the estimated importance weights. Figure 2 further indicates that LTT-IW consistently achieves a lower average FNR than LTT-RS, showing that our method of direct importance weighting yields a less conservative and more stable risk control than rejection sampling in this case.

We perform a similar analysis for the second task. Figure 3 shows that the risk is only controlled when real or quickdraw serve as the target, indicating that the covariate-shift assumption does not hold. In fact, we are actually controlling the risk over a distribution $\mathbb { P } _ { \mathrm { a l i g n e d } }$ that matches the target feature marginal, but maintains the source featureconditional distribution of the labels. With high probability, the true target risk can exceed α by at most the total-variation distance $d _ { \mathrm { T V } } \big ( \mathbb { P } _ { \mathrm { t a r g e t } } , \mathbb { P } _ { \mathrm { a l i g n e d } } \big )$ (Angelopoulos et al., 2024).

Nevertheless, we see that using importance weights (LTT-IW and LTT-RS) can bring the efective risk level closer to α: for the clipart, infograph, painting, and sketch cases, it bridges the risk gap, while making the procedure less conservative for quickdraw. In the real domain, however, the efect is minimal for LTT-IW, and LTT-RS deviates further from the target level. While both methods perform comparably on miscoverage, our method (LTT-IW) yields smaller average set sizes compared to LTT-RS (Figure 4). We notice that, on real-world data where the covariate shift assumption may be violated, higher sample eficiency makes the procedure less conservative, but may exacerbate risk violations.

![](images/dba03e8545338be81d4dbe2364f9cba77bb5d9affdaca5cde3e8e8e0456aa217.jpg)  
(a) low

![](images/fc0e84e57d56e37b04b81ad13938aee4019db8a647dd3935bf47cf56888b0e21.jpg)  
(b) medium

![](images/80167f890b5ec0b35190c976a51add549733a1778f35aa42b07c5f3c322bf7ad.jpg)  
(c) high

Figure 1: 0.95 FPR quantiles (vertical axis) vs. source sample size (horizontal axis) for each target domain in BAF (low, medium and high panels). Ignoring covariate shift (LTT) results in overly conservative or overly invalid risk control.  
![](images/5207a08ae451583757548a10c35bb5e98d3e8468f3199cda395f1ab8e1965d04.jpg)  
(a) low

![](images/7f15cf7c878b69fdde8295002239ad9836c93d2d5107e09bfe6f6afe386e4339.jpg)  
(b) medium

![](images/c8e5c6767e563db04f32c56021a183781a00d98f955cefd2010f3af3e9ac5913.jpg)  
(c) high  
Figure 2: Average FNR (vertical axis) vs. source sample size (horizontal axis) for each target domain in BAF (low, medium and high panels). LTT-IW consistently results in lower FNR compared to LTT-RS.

## 5. Conclusion and Future Work

In this work, we showed that using importance-weighted losses is a viable approach to tackle high-probability risk control under covariate shift. The experimental results show that our method outperforms the rejection-sampling baseline in terms of auxiliary performance measures. Although caveats remain, as these approaches rely on the covariate-shift assumption, the results show that the use of importance weights can narrow the risk gap, bringing the risk closer to the prescribed level even if the covariate-shift assumption is violated.

While the results presented show LTT-IW to be less conservative than LTT-RS in general, there may be individual cases where the opposite happens. An interesting research avenue consists of automatically selecting the better method. Further work could also extend the LTT-IW framework to support other risk functionals and develop strategies to increase p-value power (e.g., via variance-reduction techniques). Appendix D discusses some limitations of one such approach.

Both methods herein considered assume accurate importance weight estimates. The upper-confidence bounds provided by Park et al. (2022) address this uncertainty but assume the knowledge of hyperparameters for which there are no tuning guidelines, as well as

![](images/205f33f1349220f0a372029cdeb80c6b2b5819cb2427a172a29bdc2188c962cd.jpg)  
(a) clipart

![](images/9a4a0fcac4e1893ef50a6021f0cb4684418e2a82a7e7ebf0eaec929b4ba0c7c0.jpg)  
(b) real

![](images/7f11c9060a0ba6d10d587730f3d4550269d5ebc22c1547e7c23bacc48b980627.jpg)  
(c) infograph

![](images/782583add786c7c0cdf1e3e7406c289111a6a52f83c9bc827c31667c574c3229.jpg)  
(d) painting

![](images/1cbe386bf33dd1b196ea388ef81815f0c1f32df1414b16267f43a5d489b74bbc.jpg)  
(e) sketch

![](images/e103f88db0dad992cb16b7957ce0538b7f3ea6fea5bb41818f3867da29b2d4de.jpg)  
(f ) quickdraw

Figure 3: 0.90 miscoverage quantiles (vertical axis) vs. source sample size (horizontal axis) for each target domain in DomainNet. The use of HPRC methods bridges the risk gap for clipart, infograph, painting and sketch.

![](images/ee34a012351a4bceeb5004755ee07ad14657a725e3d6f1b685495be4bd6a7944.jpg)  
(a) clipart

![](images/6c6252899f6267c576d5a0a81a6a51f567c4648a01a202cb81c1ead9218f8bb2.jpg)  
(b) real

![](images/ba1c3c8f83aef8d48c72493b4679aed70999e4be41515dc8ac692d155045a00a.jpg)  
(c) infograph

![](images/9611eddc55a3463ed2c86c1a34be13ae3837601a3ac9005eb2d0c0cf72e06d22.jpg)  
(d) painting

![](images/152bd74a6f52095e7d6f2b56999279f099219d4704645f00cf3d9bb234e085db.jpg)  
(e) sketch

![](images/0a3050c7419d828f50c4c5565312a3fb665ae305149d4e1acf50e79f0b44536c.jpg)  
(f ) quickdraw  
Figure 4: Mean average set size (vertical axis) vs. source sample size (horizontal axis) for each target domain in DomainNet. LTT-IW achieves smaller average set sizes than LTT-RS, but with increased risk violations due to concept shift.

Lipschitz-continuous densities, which may not be appropriate for dealing with mixed categorical and numerical feature spaces. Future work could relax this assumption or develop alternatives to account for uncertainty. Furthermore, these methods assume a known upper bound B on the importance weights. Appendix E presents a sensitivity analysis on B, along with a discussion of alternative self-normalized approaches. The design of bound-free methods is also a promising direction for future research.

## References

T. Akiba, S. Sano, T. Yanase, T. Ohta, and M. Koyama. Optuna: A next-generation hyperparameter optimization framework. In Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, pages 2623—-2631, 2019.

A. N. Angelopoulos and S. Bates. Conformal prediction: A gentle introduction. Foundations and Trends Machine Learning, 16(4):494—-591, 2023.

A. N. Angelopoulos, S. Bates, A. Fisch, L. Lei, and T. Schuster. Conformal risk control. In The 12th International Conference on Learning Representations (ICLR), 2024.

A. N. Angelopoulos, S. Bates, E. J. Cand\`es, M. I. Jordan, and L. Lei. Learn then test: Calibrating predictive algorithms to achieve risk control. Annals of Applied Statistics, 19 (2):1641–1662, 2025.

R. F. Barber, E. J. Candes, A. Ramdas, and R. J. Tibshirani. The limits of distribution-free conditional predictive inference. Information and Inference: A Journal of the IMA, 10 (2):455–482, 2021.

R. F. Barber, E. J. Candes, A. Ramdas, and R. J. Tibshirani. Conformal prediction beyond exchangeability. Annals of Statistics, 51(2):816–845, 2023.

S. Bates, A. Angelopoulos, L. Lei, J. Malik, and M. Jordan. Distribution-free, riskcontrolling prediction sets. Journal of the ACM, 68(6):1–43, 2021.

S. Chandra, A. Haque, L. Khan, and C. Aggarwal. Eficient sampling-based kernel mean matching. In IEEE Interna. Conference on Data Mining (ICDM), pages 811–816, 2016.

C. J. Clopper and E. S. Pearson. The use of confidence or fiducial limits illustrated in the case of the binomial. Biometrika, 26(4):404–413, 1934.

A. Farinhas, C. Zerva, D. Ulmer, and A. F. T. Martins. Non-exchangeable conformal risk control. In International Conference on Learning Representations (ICLR), 2024.

I. Gibbs, J. J. Cherian, and E. J. Cand\`es. Conformal prediction with conditional guarantees. Journal of the Royal Statistical Society Series B: Statistical Methodology, 2025.

P. Glasserman. Monte Carlo Methods in Financial Engineering. Springer, New York, 2003.

J. Huang, A. Gretton, Ka. Borgwardt, B. Sch¨olkopf, and A. Smola. Correcting sample selection bias by unlabeled data. In Neural Information Processing Systems, pages 601– 608. MIT Press, 2006.

S. Jesus, J. Pombal, D. Alves, A. Cruz, P. Saleiro, R. P. Ribeiro, J. Gama, and P. Bizarro. Turning the tables: Biased, imbalanced, dynamic tabular datasets for ML evaluation. In Neural Information Processing Systems, 2022.

G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, and T. Liu. LightGBM: A highly eficient gradient boosting decision tree. In Neural Information Processing Systems, volume 30. Curran Associates, 2017.

W. Kouw and M. Loog. An introduction to domain adaptation and transfer learning, 2019. URL https://arxiv.org/abs/1812.11806.

I. Kuzborskij and C. Szepesv´ari. Efron-Stein PAC-Bayesian inequalities, 2020. URL https: //arxiv.org/abs/1909.01931.

B. Laufer-Goldshtein, A. Fisch, R. Barzilay, and T. S. Jaakkola. Eficiently controlling multiple risks with Pareto testing. In Intern. Conf. on Learning Representations, 2023.

S. Park, E. Dobriban, I. Lee, and O. Bastani. PAC prediction sets under covariate shift. In International Conference on Learning Representations, 2022.

X. Peng, Q. Bai, X. Xia, Z. Huang, K. Saenko, and B. Wang. Moment matching for multisource domain adaptation. In International Conference on Computer Vision (ICCV), pages 1406–1415, 2019.

J. Qui˜noreo-Candela, M. Sugiyama, A. Schwaighofer, and N. D. Lawrence. Dataset Shift in Machine Learning. MIT Press, 2009.

S. Resnick. A Probability Path. Birkh¨auser, 1999.

C. Robert and G. Casella. Monte Carlo Statistical Methods. Springer-Verlag, New York, 2nd edition, 2004.

G. Shafer and V. Vovk. A tutorial on conformal prediction. Journal of Machine Learning Research, 9:371–421, 2008.

P. Stojanov, M. Gong, J. Carbonell, and K. Zhang. Low-dimensional density datio dstimation for covariate shift correction. In 22nd International Conference on Artificial Intelligence and Statistics (AISTATS), pages 3449–3458, 2019.

M. Sugiyama, S. Nakajima, H. Kashima, P. Buenau, and M. Kawanabe. Direct importance estimation with model selection and its application to covariate shift adaptation. In Neural Information Processing Systems, 2007.

M. Sugiyama, T. Kanamori, T. Suzuki, S. Hido, J. Sese, I. Takeuchi, and L. Wang. A density-ratio framework for statistical data processing. Information and Media Technologies, 4(4):962–987, 2009.

R. J. Tibshirani, R. F. Barber, E. J. Cand\`es, and A. Ramdas. Conformal prediction under covariate shift. In Neural Information Processing Systems, 2019.

V. Vovk. Conditional validity of inductive conformal predictors. In Asian Conference on Machine Learning, pages 475–490, 2012.

S. Watanabe. Tree-structured Parzen estimator: Understanding its algorithm components and their roles for better empirical performance, 2023. URL https://arxiv.org/abs/ 2304.11127.

I. Waudby-Smith and A. Ramdas. Estimating means of bounded random variables by betting. Journal of the Royal Statistical Society Series B: Statistical Methodology, 86(1): 1–27, 2024.

K. You, X. Wang, M. Long, and M. Jordan. Towards accurate model selection in deep unsupervised domain adaptation. In 36th International Conference on Machine Learning (ICML), pages 7124–7133, 2019.

Y. Yu and C. Szepesv´ari. Analysis of kernel mean matching under covariate shift. In 29th International Coference on Machine Learning (ICML), pages 1147–1154, 2012.

T. P. Zollo, T. Morrill, Z. Deng, J. Snell, T. Pitassi, and R. Zemel. Prompt risk control: A rigorous framework for responsible deployment of large language models. In International Conference on Learning Representations, 2024.

## Appendix A. Dataset Generation

In this appendix, we provide details on the generation of domains from the BAF dataset. During preprocessing, missing numerical values are imputed with the mean and standardized using z-score normalization, while categorical features are imputed with the mode. To eliminate any temporal drift, the month feature is excluded.

To generate the disjoint covariate-shifted datasets, we employ a strategy similar to that of Huang et al. (2006). Let $c ( x )$ be the value of the feature credit risk score of sample $x ,$ and let $q _ { \mathrm { l o w } } , q _ { \mathrm { m e d } } , q _ { \mathrm { h i g h } }$ be the empirical 0.25, 0.50, 0.75 quantiles of $c ( x )$ , respectively. Sampling proceeds in stages: each observation is included in the low-risk domain with probability $\begin{array} { r } { p _ { \mathrm { l o w } } ( x ) = \exp \left( - \frac { ( c ( x ) - q _ { \mathrm { l o w } } ) ^ { 2 } } { 2 \sigma _ { \mathrm { l o w } } ^ { 2 } } \right) } \end{array}$ ; if not selected, it enters the medium-risk domain with probability $p _ { \mathrm { m e d } } ( x )$ defined analogously using $q _ { \mathrm { m e d } }$ and $\sigma _ { \mathrm { m e d } } ;$ any remaining sample is assigned to the high-risk with probability $p _ { \mathrm { h i g h } } ( x )$ , defined similarly. The bandwidths $\{ \sigma _ { \mathrm { l o w } } , \sigma _ { \mathrm { m e d } } , \sigma _ { \mathrm { h i g h } } \}$ are optimized to maximize the largest importance weight between any pair of domains while ensuring the expected dataset sizes lie in $[ 5 \times 1 0 ^ { 4 } , 1 . 5 \times 1 0 ^ { 5 } ]$

Since the sampling procedure is label-independent, the resulting domains difer solely by covariate shift. Let $S _ { i }$ be the indicator that a sample is assigned to domain $i ,$ and let $\mathbb { P } _ { i } , \mathbb { P } _ { j }$ be the corresponding distributions. Then, the importance weight is

$$
\frac {d \mathbb {P} _ {i}}{d \mathbb {P} _ {j}} (x, y) = \frac {\mathbb {P} (S _ {i} = 1 \mid x)}{\mathbb {P} (S _ {j} = 1 \mid x)} \frac {\mathbb {P} (S _ {j} = 1)}{\mathbb {P} (S _ {i} = 1)},
$$

which is a function of x alone, confirming the covariate shift assumption. Under the sequential scheme, we have $\mathbb { P } ( S _ { \mathrm { l o w } } = 1 \mid x ) = p _ { \mathrm { l o w } } ( x ) , \mathbb { P } ( S _ { \mathrm { m e d } } = 1 \mid x ) = ( 1 - p _ { \mathrm { l o w } } ( x ) ) p _ { \mathrm { m e d } } ( x )$ and $\mathbb { P } ( S _ { \mathrm { h i g h } } = 1 \mid x ) = \left( 1 - p _ { \mathrm { l o w } } ( x ) \right) \left( 1 - p _ { \mathrm { m e d } } ( x ) \right) p _ { \mathrm { h i g h } } ( x )$ . Marginal selection probabilities can be estimated via Monte Carlo as ${ \mathbb { P } } ( S _ { k } = 1 ) { \ ' } \approx n ^ { - 1 } \sum _ { i = 1 } ^ { n } { \mathbb { P } } ( S _ { k } = 1 \mid x _ { i } )$ , for $k \in \{ \mathrm { l o w , m e d , h i g h } \}$ , and used to estimate dataset sizes.

## Appendix B. P-value ablations

In this appendix, we compare the use of the WSR p-value against other possible p-values. We consider the Hoefding-Bentkus p-value for testing $\mathcal { H } _ { 0 } ( \lambda , \alpha )$ (Angelopoulos et al., 2025). Since this approach only works for losses supported in [0, 1], we consider the rescaled hypothesis $\begin{array} { r } { \mathcal { H } _ { 0 } ( \lambda , \alpha ) : \frac { R ( \lambda ) - l ^ { \prime } } { u ^ { \prime } - l ^ { \prime } } > \frac { \alpha - l ^ { \prime } } { u ^ { \prime } - l ^ { \prime } } } \end{array}$ (see Section 3), yielding the following p-value:

$$
p (\lambda , \alpha) = \min \left(\exp \left\{- n h \left(\frac {\hat {R} _ {w} (\lambda) - l ^ {\prime}}{u ^ {\prime} - l ^ {\prime}}, \frac {\alpha - l ^ {\prime}}{u ^ {\prime} - l ^ {\prime}}\right)\right\}, e F _ {\operatorname{Bin} \left(n, \frac {\alpha - l ^ {\prime}}{u ^ {\prime} - l ^ {\prime}}\right)} \left(\left\lceil n \frac {\hat {R} _ {w} (\lambda) - l ^ {\prime}}{u ^ {\prime} - l ^ {\prime}} \right\rceil\right)\right),
$$

where $\begin{array} { r } { R _ { w } ( \lambda ) = n _ { s } ^ { - 1 } \sum _ { i = 1 } ^ { n _ { s } } w ( X _ { i } ) L ( X _ { i } , Y _ { i } ; \lambda ) } \end{array}$ and $h ( a , b ) = a \log ( a / b ) + ( 1 - a ) \log ( ( 1 - a ) / ( 1 -$ b)). We also consider the application of Bernstein’s inequality for this hypothesis test (Bates et al., 2021). In particular, we reject $\mathcal { H } _ { 0 } ( \lambda , \alpha )$ if

$$
\frac {\hat {R} _ {w} (\lambda) - l ^ {\prime}}{u ^ {\prime} - l ^ {\prime}} + \frac {\hat {\sigma} _ {w} (\lambda)}{u ^ {\prime} - l ^ {\prime}} \sqrt {\frac {2 \log (2 / \delta)}{n}} + \frac {7 \log (2 / \delta)}{3 (n - 1)} \leq \frac {\alpha - l ^ {\prime}}{u ^ {\prime} - l ^ {\prime}},
$$

where $\begin{array} { r } { \hat { \sigma } _ { w } ( \lambda ) = \sqrt { ( n _ { s } - 1 ) ^ { - 1 } \sum _ { i = 1 } ^ { n _ { s } } ( L ( X _ { i } , Y _ { i } ; \lambda ) - \hat { R } _ { w } ( \lambda ) ) ^ { 2 } } } \end{array}$ denotes the empirical importanceweighted risk standard deviation. For brevity, we report only the BAF results, where the covariate shift assumption is guaranteed to hold. Figures 5 and 6 replicate the analysis of Section 4. Results show that the WSR p-value is the least conservative of the three, bringing the FPR the closest to α and achieving the lowest average FNR.

![](images/6cd52a63bef22d38c9f749903937b180cfd83ebbd7c276d57b2811d525745e52.jpg)  
(a) low

![](images/339da5f7d8fd8c80558d9898b06fdf9b0d74df65dd5538f2da17c8615f425d3d.jpg)  
(b) medium

![](images/3d7d3bd86604d85ee8daeeb94841fa33a4fd253c81b75f1168498b4e358f3d59.jpg)  
(c) high

Figure 5: 0.95 FPR quantiles (vertical axis) vs. source sample size (horizontal axis) for each target domain in BAF. WSR yields 0.95 FPR quantiles closest to 0.05.  
![](images/d4383f731c2481ed4bbc612b63853a4287dc4458461876c3ad6f94c2e65402ec.jpg)  
(a) low

![](images/92bcc8a040ed194811f352b55298e18816a392cff17d03223ce0f952810cd49f.jpg)  
(b) medium

![](images/da066b7b1a096f263d724f56a797e90e8b37cf8424c8df23b6439353ab610646.jpg)  
(c) high  
Figure 6: Mean FNR (vertical axis) vs. source sample size (horizontal axis) for each target domain in BAF. Out of the three p-values, WSR achieves the lowest FNR values.

## Appendix C. Computational Considerations

We now conduct a brief analysis of the computational cost of LTT-IW. All experiments were run on a machine with a 14-core CPU and 20-core GPU Apple M4 chip, 24GB of RAM, and a 512GB SSD. We first analyze KMM, which dominates runtime due to the need to solve multiple quadratic programs. Table 1 presents runtime, peak memory usage, and source/target dataset sizes $( n _ { s } , n _ { t } )$ for each target domain in both datasets.

LTT can be made lightweight by precomputing model scores once before running the procedure. To evaluate scalability, we measure the average runtime and peak memory usage across all LTT runs on the low domain of BAF, varying the size of the subsampled calibration set N. Figure 7 shows that both metrics grow roughly linearly with N.

Table 1: Execution time, peak memory usage, and dataset size statistics for KMM.

(a) BAF

<table><tr><td>Domain</td><td>Time (min)</td><td>Mem. (GB)</td><td> $n_s$ </td><td> $n_t$ </td></tr><tr><td>low</td><td>9.28</td><td>1.303</td><td>56,196</td><td>16,224</td></tr><tr><td>medium</td><td>6.03</td><td>1.493</td><td>31,537</td><td>40,883</td></tr><tr><td>high</td><td>9.45</td><td>1.296</td><td>57,107</td><td>15,313</td></tr></table>

(b) DomainNet

<table><tr><td>Domain</td><td>Time (min)</td><td>Mem. (GB)</td><td> $n_s$ </td><td> $n_t$ </td></tr><tr><td>clipart</td><td>33.23</td><td>4.597</td><td>176,743</td><td>14,604</td></tr><tr><td>real</td><td>46.20</td><td>4.790</td><td>176,743</td><td>52,041</td></tr><tr><td>infograph</td><td>35.56</td><td>4.603</td><td>176,743</td><td>15,582</td></tr><tr><td>painting</td><td>38.25</td><td>4.635</td><td>176,743</td><td>21,850</td></tr><tr><td>sketch</td><td>37.22</td><td>4.630</td><td>176,743</td><td>20,916</td></tr><tr><td>quickdraw</td><td>46.75</td><td>4.719</td><td>176,743</td><td>51,750</td></tr></table>

![](images/8eedb0cb1539ba6e3b6f3488a9aad6b204c496bf7780c8594eab8c81bb915567.jpg)

![](images/1fb82c96add51f3fd3e0504559932a0435021aa066ec652dc437a0e13cd3d86a.jpg)  
Figure 7: Runtime (left panel) and peak memory usage (right panel) of LTT-IW as a function of calibration subset size on the low domain of BAF. Both scale approximately linearly.

## Appendix D. Variance Reduction Techniques

High-variance losses can inflate p-values, reducing the power to detect risk-controlling configurations. One classical approach to mitigate this is to use a control variate $T ( X , Y ; \lambda )$ (Glasserman, 2003), which yields the following adjusted loss with the same expectation:

$$
L _ {\mathrm{cv}} (X, Y; \lambda) = w (X) L (X, Y; \lambda) + \eta (T (X, Y; \lambda) - \mathbb {E} [ T (X, Y; \lambda) ]),
$$

where $\eta = - \mathrm { C o v } [ w ( X ) L ( X , Y ; \lambda ) , T ( X , Y ; \lambda ) ] / \mathrm { V a r } [ T ( X , Y ; \lambda ) ]$ is chosen to to minimize the variance of $L _ { \mathrm { c v } }$ . We choose $T ( X , Y ; \lambda ) = w ( X )$ , since $\mathbb { E } _ { \mathbb { P } _ { \mathrm { s o u r c e } } } [ w ( X ) ] = 1$ (You et al., 2019). Figures 8 and 9 show the results for LTT-IW with and without control variates. To preserve the i.i.d. nature of the data, we use half of the source data to estimate η and perform risk control on the other half. The introduction of control variates yields more conservative results; the variance reduction obtained may be outweighed by the fewer data used for hypothesis testing. Future work could explore more sample-eficient variance reduction techniques or smarter ways to allocate data for variance reduction. It is important to note that the range of the loss changes from $[ 0 , B ]$ to $\left[ \operatorname* { m i n } ( \eta B , 0 ) - \eta , \operatorname* { m a x } ( ( 1 + \eta ) B , 0 ) - \eta \right]$ . For $\eta > 0$ , it expands from B to $( 1 + \eta ) B$ , meaning variance reduction comes at the cost of a wider range, which may reduce p-value power.

![](images/16f190abecaa0890c8ab00c87c34aca13e3a19beffcb6cb2728b3de9e5ead957.jpg)  
(a) low

![](images/bfa3371591981056614760bd7ea64be921b076a5a2f113ee39d39e69300e55ce.jpg)  
(b) medium

![](images/631c19a3db3d902f82a0fdb5e4fdb1530c2beebf349b719a0796cff4116e7695.jpg)  
(c) high

Figure 8: 0.95 FPR quantiles (vertical axis) vs. source sample size (horizontal axis) for each target domain in BAF. Control variates yield more conservative risk levels.  
![](images/6fdb4e60a31ce18efd72b926293d36662614c5973791c0a404989f3743860ce0.jpg)  
(a) low

![](images/10b6813c47abf315f87789b508de1f2a87d7b6878cfc55b20022afe40fccafff.jpg)  
(b) medium

![](images/e16a887e819164a6924294f27b4d9153057116d02b0f7cfd9241650276480628.jpg)  
(c) high  
Figure 9: Mean FNR (vertical axis) vs. source sample size (horizontal axis) for each target domain in BAF. Using control variates results in higher FNR.

## Appendix E. Sensitivity to the Importance Weight Upper Bound

This appendix reports a sensitivity analysis regarding the choice of the importance weight upper bound B, comparing the WSR p-value to the (asymptotically valid) normal p-value (Angelopoulos et al., 2025):

$$
p (\lambda , \alpha) = \Phi \left(\frac {n _ {s} ^ {- 1} \sum_ {i = 1} ^ {n _ {s}} w (X _ {i}) L (X _ {i} , Y _ {i} ; \lambda) - \alpha}{\sqrt {\hat {\sigma} _ {w} ^ {2} / n _ {s}}}\right),
$$

which eliminates the need to specify B. We consider the BAF dataset and 10,000 calibration points, setting $B = \gamma \hat { B }$ for $\gamma \in \{ 1 , 1 . 5 , 2 , 2 . 5 , 3 . 0 \}$ , where $\hat { B }$ is the sample maximum importance weight. As shown in Figures 10 and 11, LTT-IW becomes increasingly conservative with larger γ, while the normal p-value remains unafected, as expected.

Kuzborskij and Szepesv´ari (2020) propose a self-normalized high-probability lower bound on the true risk. Let L be a loss supported in $[ 0 , 1 ] ;$ ; then, with probability at least $1 - ( n _ { s } + 1 ) e ^ { - x }$ , for $x \ge 2$ and $y \geq 0$ , we have

$$
R _ {\mathbb {P} _ {\mathrm{target}}} (\lambda) \geq \frac {N _ {x} (n _ {s})}{n _ {s}} \left(\frac {\sum_ {i = 1} ^ {n _ {s}} w (X _ {i}) L (X _ {i} , Y _ {i} ; \lambda)}{\sum_ {i = 1} ^ {n _ {s}} w (X _ {i})} - \sqrt {2 (2 V _ {\mathrm{W}} + y) \left(1 + \ln \left(\sqrt {1 + 2 V _ {\mathrm{W}} / y}\right)\right) x}\right),
$$

![](images/46639eb063d3b3f0fc3321a374b9c5d2e5e0602c5513713031678c1fa4bd9cfe.jpg)  
(a) low

![](images/f8eb7a3bc98c687de6a764cd942d8ad612addddfa7d51defb1f20d3cbc60d5aa.jpg)  
(b) medium

![](images/087925d8cdd1f763d1e576107b7b0128919d73270221454a92a6c292941588f3.jpg)  
(c) high

Figure 10: 0.95 FPR quantiles (vertical axis) vs. source sample size (horizontal axis) for each target domain in BAF as a function of the multiplicative factor $\gamma$  
![](images/80d78df22eb968e365590e51e41e41ca5589d6fd057fab423dc7ed6f9fa6c1f1.jpg)  
(a) low

![](images/e08d7656496ec6193d19b7b61a100e605100f2a53cacbf8ef0da1818a2fecc03.jpg)  
(b) medium

![](images/cfb1ea95be967728a088783a29469a563578cd8b08d605d59725ec6ba747fc02.jpg)  
(c) high  
Figure 11: Mean FNR (vertical axis) vs. source sample size (horizontal axis) for each target domain in BAF as function of the multiplicative factor $\gamma .$

where $N _ { x } ( n _ { s } ) = \left( n _ { s } - \sqrt { 2 x n _ { s } \mathbb { E } [ w ^ { 2 } ( X ) ] } \right)$ and $\begin{array} { r } { V _ { \mathrm { W } } = \frac { 1 } { N _ { x } ^ { 2 } ( n _ { s } ) } \sum _ { i = 1 } ^ { n _ { s } } \left( w ^ { 2 } ( X _ { i } ) + \mathbb { E } [ w ^ { 2 } ( X ) ] \right) } \end{array}$ + From here, an upper bound can be derived for hypothesis testing by setting $L ^ { \prime } = 1 - L .$ identifying the l.h.s. with $1 - \mathbb { E } [ L ( X , Y ; \lambda ) ]$ and solving the inequality for $\mathbb { E } [ L ( X , Y ; \lambda ) ]$ However, it assumes that $\mathbb { E } [ w ^ { 2 } ( X ) ]$ is known. Future work could address this limitation, as well as investigate optimal choices of $y .$

## Appendix F. LightGBM Parameter Grid

Table 2: Hyperparameter grid used for LightGBM

<table><tr><td>Parameter</td><td>Suggestion type</td><td>Range</td></tr><tr><td>learning rate</td><td>log-uniform</td><td>[0.01, 0.50]</td></tr><tr><td>max. number of leaves</td><td>integer</td><td>[10, 201]</td></tr><tr><td>max. depth</td><td>integer</td><td>[-1, 21]</td></tr><tr><td>min. points per leaf</td><td>integer</td><td>[20, 101]</td></tr><tr><td>data subsample fraction</td><td>uniform</td><td>[0.5, 1.0]</td></tr><tr><td>feature subsample fraction</td><td>uniform</td><td>[0.5, 1.0]</td></tr><tr><td>boosting iterations</td><td>integer</td><td>[50, 1000]</td></tr><tr><td> $L_2$  regularisation constant</td><td>log-uniform</td><td>[10, 10000]</td></tr><tr><td>negative-class subsample fraction</td><td>uniform</td><td>[0.01, 0.5]</td></tr><tr><td>early-stopping rounds</td><td>integer</td><td>[20, 100]</td></tr></table>