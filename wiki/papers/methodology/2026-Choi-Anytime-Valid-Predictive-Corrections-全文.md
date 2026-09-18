---
title: "2026-Choi-Anytime-Valid-Predictive-Corrections"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2026-Choi-Anytime-Valid-Predictive-Corrections.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Anytime-Valid Evidence for Prespecified Predictive Corrections

Seungjin Choi

CROID Research and aSSIST University, Seoul, Korea

## Abstract

A predictive correction is a prespecified modification of an existing predictive distribution intended to reflect an anticipated change in future outcomes given their inputs, motivated, for example, by instrument recalibration, assay drift, or a known intervention. We study how to accumulate anytimevalid evidence that such a correction predicts incoming target outcomes better than the uncorrected source predictive distribution. A fixed nonnegative tilt transforms the source predictive into a corrected predictive, and the corrected-to-source predictive likelihood ratio is a conditional e-value whose running product forms an e-process. This process remains valid under optional stopping and arbitrary input sequences, including adaptively selected ones, while its logarithm equals the cumulative predictive log-score advantage of the correction. A conditional drift decomposition characterizes evidence growth under an arbitrary target predictive distribution, and a correction-dependent half space identifies misspecified target distributions for which the same false-confirmation bound continues to hold. When the predictive likelihood ratio is strictly positive, its reciprocal yields an anytime-valid refutation boundary, while an overshoot identity explains why the realized null crossing probability may fall below the nominal level. Label-shift, conditional mean and variance, subgroup-specific, and exponential-family corrections arise as special cases. Prespecified mixtures accommodate uncertainty over corrections, predictable tilts permit adaptive betting, and beyond-tolerance comparisons target changes large enough to justify action. Cross-family calculations and synthetic experiments show that a boundary crossing supports the proposed correction relative to its reference but does not uniquely identify the mechanism responsible for the shift.

## Contents

1 Introduction 4   
2 Related Work 6   
3 General Predictive-Correction E-Process 7   
3.1 Problem Setup 7   
3.2 Anytime-Valid Relative Confirmation of a Predictive Correction 9   
3.3 Growth Under Alternatives 11   
3.4 False-Confirmation Control under Target Misspecification 17   
3.4.1 A Correction-Dependent Protected Half-Space 18   
3.4.2 What Failure of the Moment Condition Means 19   
3.5 Anytime-Valid Confirmation, Refutation, and Overshoot 19   
3.5.1 Anytime-Valid Two-Boundary Decisions 19   
3.5.2 Why the Actual Null Crossing Probability Can Be Below $\alpha$ 20   
3.6 Practical Monitoring Procedure 21   
3.7 Predictable Corrections 23   
4 Structured Conditional Predictive Corrections 23   
4.1 Label-Shift Correction 24   
4.2 Concept-Drift Corrections 25   
4.2.1 Conditional Mean Correction 25   
4.2.2 Conditional Variance Correction 26   
4.3 General Exponential-Family Predictive Tilts 27   
4.4 Prespecified Mixtures over Correction Uncertainty 28   
4.5 Beyond-Tolerance Confirmation 29   
4.6 Cross-Family Drift Calculus 31   
4.6.1 Variance Correction under an Arbitrary Target 31   
4.6.2 Mean Correction under an Arbitrary Target 32   
5 Synthetic Experiments 32   
5.1 Common setup and reproducibility protocol 32   
5.2 Label-shift sanity check 33   
5.3 Conditional mean shift 34   
5.4 Beyond-tolerance confirmation 35   
5.5 Conditional variance shift and source miscalibration 36   
5.6 Mixtures over correction magnitude 36   
5.7 Predictable plug-in corrections 37   
5.8 Adaptive input selection 37   
5.9 Cross-family false confirmation 37   
5.10 Time-uniform Type I and overshoot accounting 38   
6 Discussion and Conclusion 39   
A Proofs of Main Results and Additional Derivations 42   
A.1 Proof of Lemma 1: Normalized Tilt as a Likelihood Ratio 42   
A.2 Proof of Proposition 1: Per-Observation Conditional E-Value 42   
A.3 Proof of Theorem 1: Anytime-Valid Predictive-Correction Confirmation 42   
A.4 Additional Details on Safe Numerical Approximation of the Normalizer 42   
A.5 Proof of Proposition 2: Conditional Drift Decomposition 43   
A.6 Proof of Corollary 1: Asymptotic Growth Under I.I.D. or Stationary-Ergodic Sampling 43   
A.7 Proof of Corollary 2: Finite-Horizon Crossing Bounds 44   
A.8 Interpreting the Finite-Horizon Crossing Bounds 44

A.9 Proof of Corollary 3: Correctly Specified Predictive Correction ..... 47  
A.10 Proof of Proposition 5: Predictable Tilts ..... 47  
A.11 Proof of Proposition 3: False-Confirmation Control under Target Misspecification ..... 47  
A.12 Geometry of the Protected Half-Space ..... 47  
A.13 Proof of Proposition 4: Overshoot Identity ..... 48  
A.14 Proof of Proposition 7: Composite Tolerance Null ..... 49  
A.15 Proof of Proposition 6: Mixture and Correction Panel ..... 49  
A.16 Gaussian Exponential-Tilt Derivation for Section 4.3 ..... 49

## 1 Introduction

A predictive correction is a prespecified modification of an existing predictive distribution intended to reflect an anticipated change in future outcomes given their inputs. Such a correction may be motivated by scientific knowledge, engineering analysis, or an operational policy before the outcomes used to evaluate it are observed. Distribution shift is more commonly treated as an estimation or adaptation problem: target data are used to identify what has changed and to learn an appropriate modification of the source model. This approach is natural when target data are plentiful and the shift is suficiently identifiable. In small-batch scientific and operational settings, however, target outcomes may arrive sequentially, and a plausible correction may already be available before monitoring begins. The immediate question is then not how to estimate an unrestricted target distribution, but whether the proposed correction predicts the incoming outcomes better than retaining the original source predictive distribution.

We study this complementary problem of confirmation. Let ${ \mathcal { D } } _ { \mathrm { t r } }$ denote the source training data, and let $p _ { 0 } ( y \mid x , \mathcal { D } _ { \mathrm { t r } } )$ be a fixed source predictive distribution for an outcome y at input x, conditional on ${ \mathcal { D } } _ { \mathrm { t r } }$ Before observing the outcomes used for confirmation, the practitioner specifies a nonnegative tilt

$$
h: \mathcal {X} \times \mathcal {Y} \rightarrow [ 0, \infty)
$$

with finite and positive normalizer

$$
0 <   Z _ {h} (x, \mathcal {D} _ {\mathrm{tr}}) = \int h (x, y) p _ {0} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) d y <   \infty
$$

for every relevant input x. The tilt defines the corrected predictive distribution

$$
p _ {h} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = \frac {h (x , y) p _ {0} (y \mid x , \mathcal {D} _ {\mathrm{tr}})}{Z _ {h} (x , \mathcal {D} _ {\mathrm{tr}})}, \qquad Z _ {h} (x, \mathcal {D} _ {\mathrm{tr}}) = \int h (x, y) p _ {0} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) d y.\tag{1}
$$

In the primary setting, h, and hence $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ , is fixed before the testing outcomes are observed. The incoming pairs $( X _ { i } , Y _ { i } )$ are then used only to evaluate the proposed correction. Confirmation does not estimate the full target distribution, prove that the correction is exactly specified, or identify the mechanism responsible for the shift. It provides sequential evidence that the corrected predictive outpredicts the source predictive on the observed target stream.

Predictive corrections of this form arise naturally in applications. Calibration transfer or knowledge of a changed instrument may suggest a systematic modification of the predicted response (Workman Jr., 2018). A new laboratory batch or assay protocol may suggest a change in conditional variability (Johnson et al., 2007; Leek et al., 2010). A discrepancy model may relate simulator output to anticipated physica observations (Kennedy and O’Hagan, 2001), while an operational policy may distinguish acceptable degradation from a change large enough to require intervention (Podkopaev and Ramdas, 2022). These examples share a crucial feature: the form of the correction is motivated independently of the outcomes subsequently used to confirm it. We later allow tilts that are updated predictably using past observations, but their interpretation is diferent. They define adaptive betting strategies against the source predictive null rather than confirmation of one fixed prespecified correction.

The main construction follows from a conditional likelihood-ratio argument. Let $\mathcal { F } _ { i - 1 }$ denote the information available before observing the ith outcome, including ${ \mathcal { D } } _ { \mathrm { t r } }$ and the previous testing pairs. Under the source predictive null,

$$
H _ {0} ^ {\mathrm{pred}}: \quad Y _ {i} \mid X _ {i}, \mathcal {F} _ {i - 1} \sim p _ {0} (\cdot \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}).\tag{2}
$$

Let $\mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$ denote the class of all data-stream distributions satisfying this conditional null, with the admissible input mechanism left unrestricted. Thus, the input $X _ { i }$ may be stochastic or deterministic, depend on the past, or be selected by an adaptive experimental design. Define the one-step corrected-tosource likelihood ratio

$$
e _ {i} = \frac {p _ {h} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})}{p _ {0} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})} = \frac {h (X _ {i} , Y _ {i})}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})}.\tag{3}
$$

Conditionally on $( \mathcal F _ { i - 1 } , X _ { i } )$ , this ratio has expectation one under $H _ { 0 } ^ { \mathrm { p r e d } }$ . Thus, $e _ { i }$ is a conditional e-value, and its running product

$$
M _ {t} = \prod_ {i = 1} ^ {t} e _ {i}
$$

is a nonnegative martingale under the source predictive null. Ville’s inequality (Ville, 1939) therefore gives, for every $\alpha \in ( 0 , 1 )$ 2

$$
\sup _ {P \in \mathcal {P} _ {0} ^ {\text { pred }}} \mathbb {P} _ {P} \left\{\sup _ {t \geq 0} M _ {t} > \frac {1}{\alpha} \right\} \leq \alpha .\tag{4}
$$

Consequently, the stopping rule

$$
\tau^ {*} = \inf \left\{t \geq 1: M _ {t} > \frac {1}{\alpha} \right\}
$$

controls the probability of falsely confirming the correction under continuous monitoring and optional stopping. This guarantee holds for arbitrary input sequences because validity is established conditionally on each realized input.

With the exact normalizer, $M _ { t }$ is the sequential likelihood ratio between the source and corrected conditional predictive distributions. The procedure is therefore closely related to one-sided likelihood-ratio monitoring in Wald’s sequential probability ratio framework (Wald, 1945), but the e-process formulation emphasizes continuously reportable evidence, optional-stopping validity, and compatibility with adaptive input selection. Moreover,

$$
\log M _ {t} = \sum_ {i = 1} ^ {t} \left\{\log p _ {h} (Y _ {i} \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}) - \log p _ {0} (Y _ {i} \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}) \right\}
$$

is exactly the cumulative predictive log-score advantage of the corrected predictive over the source predictive. When $h ( x , y ) > 0 p _ { 0 } ( \cdot \mid x , D _ { \mathrm { t r } } )$ -almost surely, the reciprocal likelihood ratio yields a corresponding anytimevalid boundary for refuting the corrected predictive in favor of the source predictive.

The construction generalizes anytime-valid confirmation of label-shift corrections (Choi, 2026b). Under label shift, the tilt has the restricted form $h ( x , y ) = w ( y )$ . Allowing h to depend jointly on x and y covers conditional mean and variance corrections, subgroup-specific corrections, and general exponential-family predictive tilts. This generality also clarifies the scope of the resulting evidence. Because (3) conditions on the realized input, the process is deliberately insensitive to pure covariate shift when the conditional distribution $Y \mid X$ remains unchanged. Confirmation of a proposed covariate correction or of covariate balance is instead a problem concerning the marginal input distribution and is studied separately in Choi (2026a).

The guarantee in (4) is a statement about the source predictive null. A separate robustness question arises when the actual target predictive distribution is neither $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ nor $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ . Such a target does not satisfy the original null. Nevertheless, we show that the same false-confirmation bound continues to hold over a correction-dependent half-space of misspecified target predictive distributions characterized by a conditional moment inequality. This result does not enlarge or redefine the null; it identifies target misspecifications under which the original directional confirmation rule remains controlled. Outside this protected set, the correction may acquire positive drift under a structurally diferent target, or rare large e-values may increase the crossing probability even when the average log-growth is negative. This distinction is central to the interpretation of the method: a crossing supports the proposed correction relative to its reference predictive but does not uniquely identify the form or cause of the underlying distribution shift.

The main contributions are as follows:

• Anytime-valid relative predictive evidence. We construct a conditional e-process for a prespecified predictive correction. Its wealth is exactly the cumulative predictive likelihood ratio, and its log wealth is the cumulative log-score advantage of the corrected predictive over the source predictive. Validity holds under optional stopping and arbitrary input sequences, including adaptively selected ones.

• Evidence growth and finite-horizon behavior. We derive an inputwise conditional drift decomposition and characterize long-run growth through diferences in conditional Kullback–Leibler divergences. We also provide finite-horizon bounds on the probability that a positively drifting process has not yet crossed its confirmation boundary under i.i.d. sampling.

• False-confirmation control under target misspecification. We identify a correction-dependent half-space of misspecified target predictive distributions under which the original e-process retains the same anytime-valid bound on the confirmation boundary. This geometry explains why generic proximity to the source in Kullback–Leibler, total-variation, or Hellinger distance does not by itself preserve the bound, and it separates automatically protected misspecifications from unsupported robustness claims.

• Confirmation, refutation, and operational extensions. Strictly positive likelihood ratios support both an upper boundary for confirming the correction and a reciprocal boundary for refuting it. An overshoot identity explains why the realized null crossing probability may be below the nominal level. We further develop predictable tilts, prespecified mixtures and correction panels, and beyond-tolerance comparisons that control false confirmation over an entire tolerated region in regular one-parameter exponential families.

• Structured corrections and cross-family diagnostics. We derive label-shift, conditional mean, conditional variance, subgroup-specific, and general exponential-family corrections as special cases. Analytic calculations and synthetic experiments distinguish within-family magnitude mismatch from cross-family structural mismatch, show how an unintended mechanism can generate evidence for a proposed correction, and clarify that relative predictive confirmation is not mechanism identification.

## 2 Related Work

E-values, anytime-valid inference, and sequential likelihood ratios. E-values are nonnegative evidence measures, and predictable products of conditional e-values form e-processes that remain valid under optional stopping (Vovk and Wang, 2021; Shafer, 2021; Ramdas et al., 2023). Their time-uniform guarantee follows from Ville’s inequality (Ville, 1939), while testing by betting and game-theoretic probability connect these ideas to martingales and prequential prediction (Dawid, 1984; Vovk et al., 2005; Shafer and Vovk, 2019). For a fixed source predictive and a fixed corrected predictive, the process studied here is a sequential likelihood ratio, and the two-boundary rule of Section 3.5 is closely related to Wald’s sequential probability ratio test (Wald, 1945). Our contribution is therefore not a new likelihood-ratio test for a simple pair. It is to use a practitioner-specified predictive correction as the alternative, retain conditional validity under arbitrary and adaptively selected input sequences, and characterize the resulting evidence growth, robustness under target misspecification, and operational extensions.

Distribution shift, adaptation, and correction confirmation. Distribution shift includes covariate shift, label shift, concept shift, and more general joint shift (Qui˜nonero-Candela et al., 2009; Sugiyama and Kawanabe, 2012). Most methods estimate the target shift or adapt a source model using labeled or unlabeled target data. For example, label-shift methods estimate target class proportions using source classifiers or calibrated predictors (Lipton et al., 2018; Alexandari et al., 2020; Garg et al., 2020). The task considered here is diferent: the correction is specified before the confirming outcomes are observed, and those outcomes are used to accumulate evidence for or against that correction rather than to estimate an unrestricted target distribution. Choi (2026b) developed this confirmation perspective for prespecified label-shift corrections. The present paper extends it from label-only tilts $h ( x , y ) = w ( y )$ to corrections that may depend jointly on inputs and outcomes. Covariate-shift methods instead concern density ratios over the marginal input distribution (Sugiyama and Kawanabe, 2012); anytime-valid confirmation of a proposed covariate correction and of covariate balance is treated separately in Choi (2026a).

Sequential model monitoring and tolerated change. Sequential monitoring of deployed models is often framed as testing whether a risk, loss, or performance functional has crossed an unacceptable level. Anytime-valid procedures for monitoring such scalar functionals have been developed for deployment settings in which acceptable risk levels are specified in advance (Podkopaev and Ramdas, 2022). Our target is diferent: we compare two full conditional predictive distributions, namely a source predictive and a prespecified corrected predictive. The beyond-tolerance construction in Section 4.5 is operationally related to risk-threshold monitoring, but it compares an actionable predictive directly with a tolerated-boundary predictive and, within a regular one-parameter exponential family, controls false confirmation over the entire tolerated region.

Predictive scoring, calibration, and conformal prediction. The logarithm of the likelihood-ratio e-process is a cumulative diference in predictive log scores, linking the procedure to prequential evaluation of probabilistic forecasts (Dawid, 1984). The e-process adds an inferential guarantee to that comparison: under the source predictive null, the evidence can be monitored continuously without invalidating the error bound. This objective difers from predictive calibration and coverage. Conformal prediction provides finite-sample marginal coverage under exchangeability and has been adapted to covariate and label shift through weighted calibration (Vovk et al., 2005; Tibshirani et al., 2019; Podkopaev and Ramdas, 2021; Angelopoulos and Bates, 2023). Conformal Bayes combines Bayesian predictive information with conformal calibration to obtain finite-sample marginal coverage without requiring the Bayesian predictive model to be correctly specified (Fong and Holmes, 2021). Under label shift, Choi (2026d,c) use predictive tilting and weighted calibration to adapt conformal Bayes prediction sets. Those methods target prediction set coverage or calibration, whereas the present paper uses the corrected-to-source predictive ratio to accumulate anytime-valid evidence for a proposed correction.

## 3 General Predictive-Correction E-Process

In this section, we develop the general framework for evaluating a prespecified predictive correction as target outcomes are observed sequentially. We first show that normalization of the correction tilt produces a corrected predictive distribution whose ratio to the source predictive is a conditional e-value. The resulting product e-process provides anytime-valid relative confirmation: a boundary crossing favors the corrected predictive over the source predictive without estimating the full target distribution or identifying the mechanism responsible for the change. We then characterize evidence growth under arbitrary target predictive distributions and study the robustness of false-confirmation control under target misspecification by identifying a correction-dependent protected class. Finally, we develop reciprocal refutation, overshoot accounting, safe numerical normalization, and predictable corrections based on past observations.

## 3.1 Problem Setup

Let ${ \mathcal { D } } _ { \mathrm { t r } }$ denote the source training data, and let $p _ { 0 } ( y \mid x , \mathcal { D } _ { \mathrm { t r } } )$ be a fixed source predictive distribution for an outcome y at input x, conditional on ${ \mathcal { D } } _ { \mathrm { t r } }$ . The conditioning on $\mathcal { D } _ { \mathrm { t r } }$ includes all model fitting, posterior updating, calibration, and other training-stage operations completed before monitoring begins. A target stream consists of input–outcome pairs

$$
(X _ {1}, Y _ {1}), (X _ {2}, Y _ {2}), \dots .
$$

Let $\sigma ( Z _ { 1 } , \dots , Z _ { k } )$ denote the σ-algebra generated by the random quantities $Z _ { 1 } , \ldots , Z _ { k }$ ; it represents all information that can be determined from their observed values. Define

$$
\mathcal {F} _ {0} = \sigma (\mathcal {D} _ {\mathrm{tr}})
$$

and, for $t \geq 1$

$$
\mathcal {F} _ {t} = \sigma (\mathcal {D} _ {\mathrm{tr}}, X _ {1}, Y _ {1}, \ldots , X _ {t}, Y _ {t}).
$$

Thus, $\mathcal { F } _ { t }$ contains all information available after the first t target input–outcome pairs have been observed. Before observing $Y _ { i } ,$ , define

$$
\mathcal {G} _ {i} = \mathcal {F} _ {i - 1} \vee \sigma (X _ {i}),
$$

where ∨ denotes the smallest σ-algebra containing both $\mathcal { F } _ { i - 1 }$ and $\sigma ( X _ { i } )$ . Hence, $\mathcal { G } _ { i }$ contains the past and the current input $X _ { i } ,$ but not its corresponding outcome $Y _ { i } .$

We condition throughout on the realized training data ${ \mathcal { D } } _ { \mathrm { t r } }$ , equivalently treating it as part of the initial σ-field. All conditional densities are defined with respect to a common dominating measure on $y ;$ the same notation covers discrete outcomes, with integrals replaced by sums. When a conditional distribution $r _ { i } ( \cdot \mid X _ { i } )$ is determined by the information in $\mathcal { G } _ { i } .$ , the notation

$$
\mathbb {E} _ {Y \sim r _ {i} (\cdot | X _ {i})} [ u (X _ {i}, Y) ]
$$

means expectation with respect to that conditional distribution. Equivalently, under the specification

$$
Y _ {i} \mid \mathcal {G} _ {i} \sim r _ {i} (\cdot \mid X _ {i}),
$$

it denotes a version of

$$
\mathbb {E} \left[ u \left(X _ {i}, Y _ {i}\right) \mid \mathcal {G} _ {i} \right].
$$

The source predictive null is

$$
H _ {0} ^ {\mathrm{pred}}: \qquad Y _ {i} \mid \mathcal {G} _ {i} \sim p _ {0} (\cdot \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}) \quad \text { for   every } i.\tag{5}
$$

Let $\mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$ denote the class of all data-stream distributions satisfying (5). This class is composite because the null specifies only the conditional distribution of $Y _ { i }$ given $\mathcal { G } _ { i }$ and leaves the input mechanism unrestricted. The inputs may be deterministic or stochastic, dependent on the past, or selected by an adaptive experimental-design rule.

A nonnegative process $( E _ { t } ) _ { t \geq 0 }$ , adapted to $( \mathcal { F } _ { t } ) _ { t \geq 0 }$ and initialized at $E _ { 0 } = 1$ , is an e-process for $\mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$ if

$$
\sup _ {P \in \mathcal {P} _ {0} ^ {\mathrm{pred}}} \mathbb {E} _ {P} [ E _ {\tau} ] \leq 1\tag{6}
$$

for every stopping time τ . For a possibly infinite stopping time, we use the convention

$$
E _ {\tau} = E _ {\infty} := \liminf _ {t \to \infty} E _ {t} \qquad \text {on} \{\tau = \infty \}.
$$

Thus, continuous monitoring and data-dependent stopping do not increase the expected evidence above one under any distribution in the null class. Every nonnegative supermartingale with initial value one is an e-process: apply optional stopping to $\tau \wedge t$ and then use Fatou’s lemma as $t \to \infty$ . Exact normalization will make the primary wealth process below a martingale under every $P \in \mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$

A predictive correction is specified by a jointly measurable nonnegative tilt

$$
h: \mathcal {X} \times \mathcal {Y} \to [ 0, \infty)
$$

with finite and positive normalizer

$$
0 <   Z _ {h} (x, \mathcal {D} _ {\mathrm{tr}}) = \int h (x, y) p _ {0} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) d y <   \infty\tag{7}
$$

for every relevant input $x .$ We assume that the source predictive and the tilt are measurable so that $x \mapsto Z _ { h } ( x , \mathcal { D } _ { \mathrm { t r } } )$ is measurable. The tilt defines the corrected predictive $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ in (1). In the primary setting, $h ,$ and hence $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ , is fixed before monitoring begins; Section 3.7 later allows predictable updates based on past observations. The inferential object is the comparison between the corrected and source predictive distributions, not estimation of the unknown target distribution itself.

## 3.2 Anytime-Valid Relative Confirmation of a Predictive Correction

Suppose that the practitioner has prespecified $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ before observing the target outcomes. The operational question is whether the accumulating outcomes provide suficient evidence to reject continued use of $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ in the direction represented by $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ . The corrected predictive determines the direction in which evidence against $H _ { 0 } ^ { \mathrm { p r e d } }$ is accumulated; it is not itself assumed to be the true target predictive.

Lemma 1 (Normalized tilt as a predictive likelihood ratio). For each x satisfying (7), $p _ { h } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ is a probability distribution absolutely continuous with respect to $p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ , and

$$
\frac {p _ {h} (y \mid x , \mathcal {D} _ {\mathrm{tr}})}{p _ {0} (y \mid x , \mathcal {D} _ {\mathrm{tr}})} = \frac {h (x , y)}{Z _ {h} (x , \mathcal {D} _ {\mathrm{tr}})} \qquad p _ {0} (\cdot \mid x, \mathcal {D} _ {\mathrm{tr}}) \text {-a.s.}\tag{8}
$$

Moreover,

$$
\mathbb {E} _ {Y \sim p _ {0} (\cdot | x, \mathcal {D} _ {\mathrm{tr}})} \left[ \frac {h (x , Y)}{Z _ {h} (x , \mathcal {D} _ {\mathrm{tr}})} \right] = 1.\tag{9}
$$

Proof sketch. Substituting the definition of $p _ { h } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ ) and using (7) gives unit integral, the likelihoodratio identity, and expectation one under $p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ . See Section A.1 for details. □

Canonical evidence factor outside the source support. The likelihood-ratio identity in $\operatorname { E q . } \ ( 8 )$ is an $p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ -almost-sure statement, as is standard for a Radon–Nikodym derivative. Throughout the paper we therefore take

$$
e (x, y) := \frac {h (x , y)}{Z _ {h} (x , \mathcal {D} _ {\mathrm{tr}})}\tag{10}
$$

as the canonical measurable version of the one-step evidence factor. Under the source predictive null it coincides almost surely with the corrected-to-source predictive likelihood ratio. It remains well defined for a target distribution that is not dominated by the source predictive. The literal predictive-likelihood-ratio, log-score, and KL interpretations below are invoked only when the relevant densities and logarithms are well defined.

Proposition 1 (Per-observation relative e-value). For the ith observation, define the canonical one-step factor

$$
e _ {i} := \frac {h (X _ {i} , Y _ {i})}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})}.\tag{11}
$$

Under the source predictive null, Lemma 1 gives $e _ { i } = p _ { h } ( Y _ { i } \mid X _ { i } , \mathcal { D } _ { \mathrm { t r } } ) / p _ { 0 } ( Y _ { i } \mid X _ { i } , \mathcal { D } _ { \mathrm { t r } } )$ almost surely. For every $P \in \mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$

$$
\mathbb {E} _ {P} [ e _ {i} \mid \mathcal {G} _ {i} ] = 1.\tag{12}
$$

Hence $e _ { i }$ is a conditional e-value for the source predictive null.

Proof sketch. Condition on $\mathcal { G } _ { i }$ and apply Lemma 1 under (5). See Section A.2.

Theorem 1 (Anytime-valid relative confirmation of a predictive correction). Let $M _ { 0 } = 1$ and

$$
M _ {t} := \prod_ {i = 1} ^ {t} e _ {i} = \prod_ {i = 1} ^ {t} \frac {h (X _ {i} , Y _ {i})}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})}.\tag{13}
$$

Under every $P \in \mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$ , this process agrees almost surely at every finite time with the corrected-to-source predictive likelihood-ratio product. For every $P \in \mathcal { P } _ { 0 } ^ { \mathrm { p r e d } } , ( M _ { t } ) _ { t \geq 0 }$ is a nonnegative martingale with respect to $( \mathcal { F } _ { t } ) _ { t \geq 0 }$ . Hence it is an e-process for $\mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$ , and for every $\alpha \in ( 0 , 1 )$ ,

$$
\sup _ {P \in \mathcal {P} _ {0} ^ {\text { pred }}} \mathbb {P} _ {P} \left\{\sup _ {t \geq 0} M _ {t} > \frac {1}{\alpha} \right\} \leq \alpha .\tag{14}
$$

Therefore, the stopping time

$$
\tau^ {*} := \inf \left\{t \geq 1: M _ {t} > \frac {1}{\alpha} \right\}\tag{15}
$$

satisfies

$$
\sup _ {P \in \mathcal {P} _ {0} ^ {\text { pred }}} \mathbb {P} _ {P} (\tau^ {*} <   \infty) \leq \alpha .\tag{16}
$$

The guarantee holds under continuous monitoring and for every admissible input mechanism, including adaptive selection based on past observations.

Proof sketch. Fix $P \in \mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$ . By Proposition 1 and iterated conditional expectation,

$$
\mathbb {E} _ {P} [ e _ {t} \mid \mathcal {F} _ {t - 1} ] = \mathbb {E} _ {P} [ \mathbb {E} _ {P} [ e _ {t} \mid \mathcal {G} _ {t} ] \mid \mathcal {F} _ {t - 1} ] = 1.
$$

Therefore, $\mathbb { E } _ { P } [ M _ { t } \ | \ \mathcal { F } _ { t - 1 } ] = M _ { t - 1 } , \mathrm { ~ s o ~ } ( M _ { t } )$ is a nonnegative P-martingale. Since this holds for every $P \in \mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$ , the process is an e-process for the whole null class. Ville’s inequality gives (14), and (16) follows from

$$
\left\{\tau^ {*} <   \infty \right\} = \left\{\sup _ {t \geq 0} M _ {t} > \frac {1}{\alpha} \right\}.
$$

See Section A.3.

Classical likelihood-ratio monitoring as a special case. The predictive-ratio framework includes ordinary conditional likelihood-ratio monitoring. If the source and corrected predictives are two fixed, fully specified conditional likelihoods,

$$
p _ {0} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = f (y \mid x, \theta_ {0}), \qquad p _ {h} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = f (y \mid x, \theta_ {1}),
$$

then

$$
e _ {i} = \frac {f (Y _ {i} \mid X _ {i} , \theta_ {1})}{f (Y _ {i} \mid X _ {i} , \theta_ {0})}
$$

is the classical one-step likelihood ratio, and $M _ { t }$ is its sequential product. The predictive formulation is more general because it also permits posterior predictive distributions, fitted predictive distributions treated as fixed conditional on $\mathcal { D } _ { \mathrm { t r } } .$ , and corrections specified directly at the level of the outcome distribution. When parameters are estimated from ${ \mathcal { D } } _ { \mathrm { t r } }$ , the resulting guarantee is conditional on the fitted source predictive; it does not automatically extend to an unresolved composite parametric null.

Sequential test enabled by Theorem 1. Theorem 1 gives the practitioner an explicit continuously monitored test of $H _ { 0 } ^ { \mathrm { p r e d } }$ . Starting from $M _ { 0 } = 1$ , after a new target input $X _ { t }$ and outcome $Y _ { t }$ are observed, update

$$
M _ {t} = M _ {t - 1} \frac {p _ {h} (Y _ {t} \mid X _ {t} , \mathcal {D} _ {\mathrm{tr}})}{p _ {0} (Y _ {t} \mid X _ {t} , \mathcal {D} _ {\mathrm{tr}})}.\tag{17}
$$

If $M _ { t } \le 1 / \alpha$ , monitoring may continue and the process is updated again when the next target outcome becomes available. At the first time $M _ { t } > 1 / \alpha$ , stop and reject the source predictive null. No monitoring horizon needs to be fixed in advance, the process may be inspected after every observation, and the stopping decision may depend on the entire observed history. Inputs may also be selected adaptively. Despite these freedoms, if $\dot { \boldsymbol { H } } _ { 0 } ^ { \mathrm { p r e d } }$ is true, the probability of ever rejecting it is at most α.

The formal output of this test is therefore an anytime-valid rejection of the source predictive null. Because every update in (17) is the prespecified likelihood ratio of $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ to $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ , the rejection has a directional interpretation: the incoming target outcomes have provided suficient sequential evidence favoring $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ over $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ . We call this conclusion anytime-valid relative confirmation of the proposed correction. The word “relative” emphasizes that the conclusion compares the corrected predictive with the source predictive; the theorem does not treat $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ as a null hypothesis to be accepted.

Log-score representation of the evidence. Let

$$
\mathrm{NLPD} _ {i} (p) = - \log p (Y _ {i} \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}})
$$

denote the negative log-predictive density at observation i. Whenever the two predictive log densities are finite at the observed outcome, the one-step log evidence equals the diference in predictive log scores:

$$
\begin{array}{r l} & {\log e _ {i} = \log p _ {h} (Y _ {i} | X _ {i}, \mathcal {D} _ {\mathrm{tr}}) - \log p _ {0} (Y _ {i} | X _ {i}, \mathcal {D} _ {\mathrm{tr}})} \\ & {\qquad = \mathrm{NLPD} _ {i} (p _ {0} (\cdot | \cdot , \mathcal {D} _ {\mathrm{tr}})) - \mathrm{NLPD} _ {i} (p _ {h} (\cdot | \cdot , \mathcal {D} _ {\mathrm{tr}})).} \end{array}\tag{18}
$$

Consequently,

$$
\log M _ {t} = \sum_ {i = 1} ^ {t} \left\{\mathrm{NLPD} _ {i} (p _ {0} (\cdot | \cdot , \mathcal {D} _ {\mathrm{tr}})) - \mathrm{NLPD} _ {i} (p _ {h} (\cdot | \cdot , \mathcal {D} _ {\mathrm{tr}})) \right\}.\tag{19}
$$

Thus, on paths for which these predictive log scores are finite, log $M _ { t }$ is the cumulative predictive log-score advantage of the corrected predictive over the source predictive on the observed target stream. Under the source predictive null this qualification holds almost surely whenever the one-step log evidence is finite. At a boundary crossing,

$$
\log M _ {\tau^ {*}} > \log (1 / \alpha),
$$

so the corrected predictive has accumulated more than $\log ( 1 / \alpha )$ nats of observed log-score advantage. This identity explains why rejection of the source predictive null can be interpreted as relative evidence for the prespecified correction.

What relative confirmation does and does not establish. Relative confirmation is a finite-sample, observed-data conclusion. It says that the target stream has accumulated enough evidence to reject the source predictive null in the prespecified direction $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } ) / p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ . It does not establish that $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ equals the true target predictive distribution, that the tilt h is unique or correctly specified, or that $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ is close to the target distribution in an absolute sense. The true target predictive may be a third distribution q that difers from both $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ and $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ , while $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ is nevertheless less wrong than $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ and therefore accumulates positive evidence.

The next subsection makes this population comparison precise. Under a target predictive q, positive expected log-evidence at an input is equivalent to $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ being closer to q than $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ is in conditional KL divergence, subject to the stated finiteness conditions. This is a statement of relative predictive superiority, not an absolute adequacy certificate: even when $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ is closer to q than $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ , it may still be far from $q .$ Conversely, failure to cross the boundary does not establish that the source predictive is correct or that the two predictives are equivalent; it means only that the observed stream has not supplied enough evidence for rejection at the chosen anytime-valid level.

The construction above uses the exact normalizer $Z _ { h } ( x , \mathcal { D } _ { \mathrm { t r } } )$ . Certified upper-bound normalizers preserve confirmation validity but subtract a predictable log-evidence penalty and no longer yield an exact predictive likelihood ratio. This implementation issue is treated in Section 3.6. Figure 1 summarizes the complete monitoring logic.

## 3.3 Growth Under Alternatives

The e-process guarantee controls false confirmation under the source predictive null, but it does not describe how evidence behaves under a target predictive distribution q. We now ask when the proposed correction accumulates evidence under q and how the rate of accumulation depends on the inputs observed. The main result decomposes the log e-process into conditional expected growth under q along the realized input sequence and a martingale fluctuation term. We first state this decomposition for general, possibly adaptively selected inputs; i.i.d. and stationary-ergodic limits then follow as corollaries.

For a fixed target conditional distribution q and a given input-selection mechanism, let $P _ { q }$ denote the induced distribution of the sequential data stream, and write $\mathbb { E } _ { q }$ and $\mathbb { P } _ { q }$ for expectation and probability under $P _ { q } .$ . Thus the subscript q specifies the outcome mechanism together with the input process under consideration.

![](images/ccb6f0099d34ee71c47dcc6752b3ef452b3faeb6454d560fc8a52beccce61ac9.jpg)  
Figure 1: Schematic of sequential monitoring for a prespecified predictive correction. The tilt transforms the source predictive into a corrected predictive, each incoming outcome contributes one-step evidence, and the running product is monitored continuously. The upper boundary provides anytime-valid relative confirmation under the source predictive null. The reciprocal lower boundary is available only with exact normalization and is calibrated under the corrected predictive null.

Proposition 2 (Conditional drift decomposition). Suppose that, for each i, conditional on $\mathcal { G } _ { i }$ , the outcome satisfies

$$
Y _ {i} \mid \mathcal {G} _ {i} \sim q (\cdot \mid X _ {i})
$$

for a fixed target conditional distribution q. Assume that

$$
\mathbb {E} _ {q} \left[ \left| \log \frac {h (X _ {i} , Y _ {i})}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})} \right| \right] <   \infty
$$

for every i. Define a measurable version of the per-input drift by

$$
\Gamma_ {h} (x) := \int q (y \mid x) \log \frac {h (x , y)}{Z _ {h} (x , \mathcal {D} _ {\mathrm{tr}})} d y.\tag{20}
$$

wherever the integral is finite. The preceding integrability condition ensures that $\Gamma _ { h } ( X _ { i } )$ is finite almost surely for every i. Whenever both KL divergences are finite, the drift can equivalently be written as

$$
\Gamma_ {h} (x) = D _ {\mathrm{KL}} \left(q (\cdot \mid x) \| p _ {0} (\cdot \mid x, \mathcal {D} _ {\mathrm{tr}})\right) - D _ {\mathrm{KL}} \left(q (\cdot \mid x) \| p _ {h} (\cdot \mid x, \mathcal {D} _ {\mathrm{tr}})\right).\tag{21}
$$

Then, under the target process induced by q,

$$
\mathbb {E} _ {q} [ \log e _ {i} \mid \mathcal {G} _ {i} ] = \int q (y \mid X _ {i}) \log \frac {h (X _ {i} , y)}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})} d y = \Gamma_ {h} (X _ {i}) \qquad a. s.,
$$

and $\mathbb { E } _ { q } | \Gamma _ { h } ( X _ { i } ) | < \infty$ . Consequently,

$$
N _ {t} := \log M _ {t} - \sum_ {i = 1} ^ {t} \Gamma_ {h} (X _ {i}), \qquad N _ {0} = 0,
$$

is a martingale with respect to $( \mathcal { F } _ { t } ) _ { t \geq 0 }$ under $P _ { q }$ .

If, in addition, there exists a finite constant v such that

$$
\mathbb {E} _ {q} \Big [ \left\{\log e _ {i} - \Gamma_ {h} (X _ {i}) \right\} ^ {2} \Big | \mathcal {G} _ {i} \Big ] \leq v \quad a. s. f o r e v e r y i,
$$

then

$$
\frac {N _ {t}}{t} \longrightarrow 0 \qquad a. s.
$$

Therefore, on the event

$$
\left\{\liminf _ {t \to \infty} \frac {1}{t} \sum_ {i = 1} ^ {t} \Gamma_ {h} (X _ {i}) > 0 \right\},
$$

we have log $M _ { t } \to + \infty$ and hence $\tau ^ { * } < \infty$ almost surely.

Proof sketch. Conditioning on $\mathcal { G } _ { i }$ and using $Y _ { i } \mid { \mathcal { G } } _ { i } \sim q ( \cdot \mid X _ { i } )$ gives

$$
\mathbb {E} _ {q} [ \log e _ {i} \mid \mathcal {G} _ {i} ] = \Gamma_ {h} (X _ {i}).
$$

Hence the centered increments

$$
\log e _ {i} - \Gamma_ {h} (X _ {i})
$$

form a martingale diference sequence under $P _ { q } ,$ so $N _ { t }$ is an $( \mathcal { F } _ { t } )$ -martingale under $P _ { q } .$ The conditional second-moment bound implies, by a martingale strong law, that $N _ { t } / t \to 0$ almost surely. Therefore,

$$
\frac {\log M _ {t}}{t} = \frac {1}{t} \sum_ {i = 1} ^ {t} \Gamma_ {h} (X _ {i}) + \frac {N _ {t}}{t},
$$

and a positive lower limit of the average drift forces log $M _ { t } \to + \infty$ , so the confirmation boundary is crossed in finite time. See Section A.5 for details. □

Proposition 2 has three main implications.

a. First, the sign of $\Gamma _ { h } ( x )$ measures relative predictive merit at input x. Whenever the two KL divergences in (21) are finite, $\Gamma _ { h } ( x ) > 0$ exactly when the corrected predictive $p _ { h } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ is closer to the true target conditional distribution $q ( \cdot \mid x )$ in KL divergence than the source predictive $p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ is. The correction need not coincide with the true target distribution: an incorrect magnitude, or even an imperfect structural form, can have positive expected log-growth if it predicts better than the source model. Conversely, scientific plausibility alone does not ensure positive drift. Confirmation therefore concerns the correction’s predictive advantage relative to the source, not exact estimation or identification of the shift.

b. Second, the decomposition

$$
\log M _ {t} = \sum_ {i = 1} ^ {t} \Gamma_ {h} (X _ {i}) + N _ {t}
$$

separates systematic evidence growth from random fluctuation. The first term is the cumulative conditional expected log-score advantage of the correction along the inputs actually observed; $N _ { t }$ records the deviations of the realized log scores from those conditional expectations. Under the conditional second-moment condition, $N _ { t } / t \to 0$ almost surely. Consequently, persistent positive average drift implies eventual confirmation with probability one, whereas the proposition itself does not provide a finite-horizon power function such as $\mathbb { P } _ { q } ( \tau ^ { * } \leq t )$ ; a conservative finite-horizon bound under i.i.d. sampling is given in Corollary 2.

c. Third, the input sequence afects the rate of evidence accumulation through $\Gamma _ { h } ( X _ { i } )$ . Inputs with large positive drift are more informative for comparing $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ with $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ , while inputs with drift near zero contribute little expected log evidence. The null guarantee remains valid for arbitrary adaptive input selection because it conditions on the realized $X _ { i }$ . Thus, when informative inputs can be identified from scientific knowledge or a prespecified or predictable design criterion, adaptive experimental design may accelerate confirmation without changing the source-null error guarantee. The design afects the growth rate under the target alternative, not the validity of the e-process under the null.

Corollary 1 (Asymptotic growth under i.i.d. or stationary-ergodic sampling). Suppose that either

(i) the pairs $( X _ { i } , Y _ { i } ) _ { i \geq 1 }$ are i.i.d. with joint distribution

$$
q ^ {X} (d x)   q (d y \mid x),
$$

or

(ii) the pair process $( X _ { i } , Y _ { i } ) _ { i \geq 1 }$ is stationary and ergodic with one-step distribution

$$
q ^ {X} (d x) q (d y \mid x).
$$

If

$$
\mathbb {E} _ {q ^ {X} q ^ {Y | X}} \left[ \left| \log \frac {h (X , Y)}{Z _ {h} (X , \mathcal {D} _ {\mathrm{tr}})} \right| \right] <   \infty ,
$$

then

$$
\frac {1}{t} \log M _ {t} \longrightarrow \overline {{\Gamma}} (q; h) := \mathbb {E} _ {X \sim q ^ {X}} [ \Gamma_ {h} (X) ] = \mathbb {E} _ {(X, Y) \sim q ^ {X} q ^ {Y | X}} \left[ \log \frac {h (X , Y)}{Z _ {h} (X , \mathcal {D} _ {\mathrm{tr}})} \right]\tag{22}
$$

$H ,$ in addition, the two expected predictive log losses below are finite, then this limit has the equivalent log-score representation

$$
\overline {{\Gamma}} (q; h) = \mathbb {E} _ {q ^ {X} q ^ {Y | X}} [ \mathrm{NLPD} (p _ {0} (\cdot | \cdot , \mathcal {D} _ {\mathrm{tr}})) ] - \mathbb {E} _ {q ^ {X} q ^ {Y | X}} [ \mathrm{NLPD} (p _ {h} (\cdot | \cdot , \mathcal {D} _ {\mathrm{tr}})) ].\tag{23}
$$

Consequently, if $\overline { { { \Gamma } } } ( q ; h ) > 0$ , then log $M _ { t } \to + \infty$ and $\tau ^ { * } < \infty$ almost surely. $I f \ \overline { { { \Gamma } } } ( q ; h ) < 0$ , then log $M _ { t } \to - \infty$ and ${ M _ { t } } \to 0$ almost surely.

Proof sketch. Under either assumption, the sequence

$$
\log e _ {i} = \log \frac {h (X _ {i} , Y _ {i})}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})}
$$

is integrable and is respectively i.i.d. or stationary and ergodic. The ordinary strong law or Birkhof’s ergodic theorem therefore gives

$$
\frac {1}{t} \log M _ {t} = \frac {1}{t} \sum_ {i = 1} ^ {t} \log e _ {i} \longrightarrow \mathbb {E} _ {q ^ {X} q ^ {Y | X}} [ \log e _ {1} ] = \mathbb {E} _ {q ^ {X}} [ \Gamma_ {h} (X) ] \quad \text {a.s.}
$$

The conclusions for positive and negative limits follow immediately. See Section A.6 for details. □

The corollary replaces the input-dependent cumulative drift in Proposition 2 by a single deterministic long-run growth rate. Under i.i.d. or stationary-ergodic sampling,

$$
\log M _ {t} = t \overline {{\Gamma}} (q; h) + o (t) \quad \mathrm{a.s.}
$$

Thus $\overline { { \Gamma } } ( q ; h )$ is the asymptotic number of nats of evidence gained per observation. It is positive exactly when the corrected predictive $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ has smaller expected negative log-predictive density than the source predictive $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ under the joint target distribution $q ^ { X } ( d x ) q ( d y \mid x )$ .

When $\overline { { \Gamma } } ( q ; h ) > 0$ , the e-process grows exponentially at rate $\overline { { \Gamma } } ( q ; h )$ :

$$
M _ {t} = \exp \{t \overline {{\Gamma}} (q; h) + o (t) \}.
$$

The correction is therefore eventually confirmed almost surely, and the first-order crossing-time approximation is

$$
\tau^ {*} \approx \frac {\log (1 / \alpha)}{\overline {{\Gamma}} (q ; h)}.
$$

When $\overline { { \Gamma } } ( q ; h ) < 0 .$ , the source predictive has the smaller expected log loss and the evidence process decays exponentially. When $\overline { { \Gamma } } ( q ; h ) = 0$ , neither predictive has a long-run expected log-score advantage, and the corollary alone does not determine whether a finite boundary crossing occurs.

Proposition 2 and Corollary 1 serve complementary purposes. Proposition 2 applies to general, possibly adaptively selected inputs and describes growth through the path-dependent average

$$
\frac {1}{t} \sum_ {i = 1} ^ {t} \Gamma_ {h} (X _ {i}).
$$

Corollary 1 applies when the sampling process has a stable long-run distribution and reduces this quantity to the population average

$$
\overline {{\Gamma}} (q; h) = \mathbb {E} _ {q ^ {X}} [ \Gamma_ {h} (X) ].
$$

It therefore provides a simple summary of the correction’s long-run predictive advantage and connects the sequential e-process directly to standard expected log-loss comparison.

Corollary 2 (A finite-horizon crossing bound). Suppose that the log e-values $Z _ { i } = \log e _ { i }$ are i.i.d. under $P _ { q } ,$ , with

$$
\mathbb {E} _ {q} [ Z _ {i} ] = \overline {{\Gamma}} (q; h) > 0, \quad \mathrm{Var} _ {q} (Z _ {i}) \leq v <   \infty .
$$

Let $b = \log ( 1 / \alpha )$ . For every integer t satisfying $\begin{array} { r } { t \overline { { \Gamma } } ( q ; h ) > b ; } \end{array}$

$$
\mathbb {P} _ {q} (\tau^ {*} > t) \leq \frac {t v}{t v + \{t \overline {{\Gamma}} (q ; h) - b \} ^ {2}}.\tag{24}
$$

If, in addition, the centered increments $Z _ { i } - { \overline { { \Gamma } } } ( q ; h )$ are sub-Gaussian with variance proxy $s ^ { 2 }$ , that is,

$$
\mathbb {E} _ {q} \exp \left[ \theta \{Z _ {i} - \overline {{\Gamma}} (q; h) \} \right] \leq \exp \left(\frac {\theta^ {2} s ^ {2}}{2}\right) \quad \text {   for   every   } \theta \in \mathbb {R},
$$

then the same event admits the exponential bound

$$
\mathbb {P} _ {q} (\tau^ {*} > t) \leq \exp \left[ - \frac {\{t \overline {{\Gamma}} (q ; h) - b \} ^ {2}}{2 t s ^ {2}} \right].\tag{25}
$$

If instead the increments are bounded, with $| Z _ { i } - \overline { { \Gamma } } ( q ; h ) | \leq R$ almost surely, then

$$
\mathbb {P} _ {q} (\tau^ {*} > t) \leq \exp \left[ - \frac {\{t \overline {{\Gamma}} (q ; h) - b \} ^ {2}}{2 t v + \frac {2}{3} R \{t \overline {{\Gamma}} (q ; h) - b \}} \right].\tag{26}
$$

Proof sketch. The event $\{ \tau ^ { * } > t \}$ implies log $M _ { t } \le b$ . All three bounds follow by applying a lower-tail inequality to log $\begin{array} { r } { M _ { t } - t \overline { { \Gamma } } ( q ; h ) = \sum _ { i = 1 } ^ { t } \{ Z _ { i } - \overline { { \Gamma } } ( q ; h ) \} } \end{array}$ at the deviation level $t \overline { { \Gamma } } ( q ; h ) - b > 0 ;$ : Cantelli’s one-sided variance inequality gives (24), using that $\bar { \sigma ^ { 2 } } \mapsto \sigma ^ { 2 } / ( \sigma ^ { 2 } + \lambda ^ { 2 } )$ is increasing, so that the variance may be replaced by the upper bound tv; the sub-Gaussian Chernof bound gives (25); and Bernstein’s inequality gives (26). See Section A.7 for details. □

The bounds make the crossing-time heuristic $\tau ^ { * } \approx b / \overline { { \Gamma } } ( q ; h )$ operational: once the expected accumulated log evidence exceeds the boundary, the probability of not yet crossing is explicitly controlled. The two difer sharply in how fast that control improves. The variance-only bound (24) decays only at the polynomial rate $v / \{ t \overline { { \Gamma } } ( q ; h ) ^ { 2 } \}$ and is therefore very conservative at moderate horizons, whereas (25) decays exponentially in t. For the Gaussian mean tilt of Section 4.2.1 with bounded g the increments are sub-Gaussian, so the exponential bound also applies. Its numerical sharpness depends entirely on the certified variance proxy; Section 5.3 evaluates both the variance-only bound and a deliberately conservative certified sub-Gaussian proxy.

The Bernstein form (26) is useful when a deterministic bound on the centered increments and a variance bound are both available, especially when the increment distribution is strongly skewed. A sub-Gaussian proxy obtained only from a worst-case range can be much looser because it discards the variance information, whereas (26) uses the variance and the range together. The two forms can cross: (24) may be sharper at short horizons, where the linear term $\scriptstyle { \frac { 2 } { 3 } } R \{ t { \bar { \Gamma } } ( q ; { \bar { h } } ) - b \}$ dominates the Bernstein denominator, while (26) can become sharper at long horizons as the quadratic numerator grows. The Bernstein bound requires valid variance and range bounds; these quantities should not be estimated from the same monitored outcomes and then treated as prospective certificates. A step-by-step interpretation of the crossing event, the sample-size heuristic, and all three finite-horizon bounds is provided in Section A.8.

Corollary 3 (Correctly specified predictive correction). Suppose that the target conditional distribution is exactly the corrected predictive:

$$
q (\cdot \mid X _ {i}) = p _ {h} (\cdot \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}) \quad a. s. f o r e v e r y i.
$$

Under the integrability hypothesis of Proposition 2,

$$
\Gamma_ {h} (X _ {i}) = D _ {\mathrm{KL}} \left(p _ {h} (\cdot \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}) \| p _ {0} (\cdot \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}})\right) \geq 0 \quad a. s.\tag{27}
$$

If, in addition, the bounded conditional second-moment condition of Proposition 2 holds, then for arbitrary, possibly adaptively selected inputs,

$$
\tau^ {*} <   \infty \qquad a. s. o n t h e e v e n t \qquad \left\{\operatorname * {l i m i n f} _ {t \to \infty} \frac {1}{t} \sum_ {i = 1} ^ {t} D _ {\mathrm{KL}} (p _ {h} (\cdot \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}) \parallel p _ {0} (\cdot \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}})) > 0 \right\}.
$$

Under either the i.i.d. or stationary-ergodic sampling regime of Corollary 1, suppose instead that its integrability condition holds. Then

$$
\frac {1}{t} \log M _ {t} \longrightarrow \gamma_ {h} := \mathbb {E} _ {X \sim q ^ {X}} [ D _ {\mathrm{KL}} (p _ {h} (\cdot | X, \mathcal {D} _ {\mathrm{tr}}) \| p _ {0} (\cdot | X, \mathcal {D} _ {\mathrm{tr}})) ] \geq 0 \quad a. s.\tag{28}
$$

In particular, $i f \gamma _ { h } > 0$ , then log $M _ { t } \to + \infty$ and $\tau ^ { * } < \infty$ almost surely. Moreover, $\gamma _ { h } = 0$ if and only if

$$
p _ {h} (\cdot \mid X, \mathcal {D} _ {\mathrm{tr}}) = p _ {0} (\cdot \mid X, \mathcal {D} _ {\mathrm{tr}}) \quad f o r q ^ {X} \text {-almost every} X.
$$

Proof sketch. Setting $q ( \cdot \mid x ) = p _ { h } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ in (21) gives

$$
\Gamma_ {h} (x) = D _ {\mathrm{KL}} (p _ {h} (\cdot \mid x, \mathcal {D} _ {\mathrm{tr}}) \parallel p _ {0} (\cdot \mid x, \mathcal {D} _ {\mathrm{tr}})),
$$

because

$$
D _ {\mathrm{KL}} (p _ {h} (\cdot \mid x, \mathcal {D} _ {\mathrm{tr}}) \| p _ {h} (\cdot \mid x, \mathcal {D} _ {\mathrm{tr}})) = 0.
$$

The arbitrary-input conclusion follows from Proposition 2, and the asymptotic growth statement follows from Corollary 1. See Section A.9 for details. □

Under correct specification, let $P _ { h }$ denote the data-stream distribution induced by the corrected predictive and the given input mechanism. The general conditional drift then reduces to an information divergence:

$$
\mathbb {E} _ {P _ {h}} [ \log e _ {i} \mid \mathcal {G} _ {i} ] = D _ {\mathrm{KL}} (p _ {h} (\cdot \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}) \| p _ {0} (\cdot \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}})).
$$

Thus no input has negative expected log-growth. An input contributes zero expected evidence when the corrected and source predictives coincide there, and positive expected evidence when they difer, subject to the stated integrability conditions.

For arbitrary, possibly adaptive, inputs, eventual confirmation requires the average KL separation along the realized input sequence to remain positive. Correct specification alone is therefore not enough if the sampling mechanism visits only regions where the two predictives are indistinguishable. This also gives the result an experimental-design interpretation: inputs with larger KL separation are more informative for confirming the correction.

Under i.i.d. or stationary-ergodic sampling, the pathwise average reduces to $\gamma _ { h } .$ , the population-average KL separation. Hence $\gamma _ { h }$ is the asymptotic number of nats of evidence gained per observation, and $\gamma _ { h } > 0$ implies exponential evidence growth and eventual confirmation almost surely. This is the clean benchmark case: when the prespecified correction is the true target predictive, its evidence rate is exactly the KL information separating it from the source predictive.

## 3.4 False-Confirmation Control under Target Misspecification

Theorem 1 controls the probability of ever confirming the correction when the source predictive null is true. In deployment, however, the true target predictive distribution q may be neither the source predictive $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ nor the proposed corrected predictive $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ . The source predictive null remains the original null hypothesis; a target distribution $q \ne p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ is not reclassified as part of that null. Instead, we ask a robustness question:

For which misspecified target predictive distributions q does the original stopping rule still control the probability of ever crossing the confirmation boundary by α?

Answering this question identifies a protected class of target misspecifications for the original directional bet. It does not enlarge the source predictive null. Rather, it clarifies when the same maximal crossing bound persists despite misspecification and when additional protection must be built into the e-process. The following condition is exactly the condition under which each one-step factor remains a conditional e-value under the misspecified target process.

Proposition 3 (Persistence of false-confirmation control under target misspecification). For each i, let $q _ { i }$ be a $\mathcal { G } _ { i }$ -measurable target conditional distribution and suppose that

$$
Y _ {i} \mid \mathcal {G} _ {i} \sim q _ {i} (\cdot \mid X _ {i}).
$$

The sequence (q ) may vary predictably with time, the past, and the current input. If

$$
\mathbb {E} _ {Y \sim q _ {i} (\cdot | X _ {i})} [ h (X _ {i}, Y) ] \leq \mathbb {E} _ {Y \sim p _ {0} (\cdot | X _ {i}, \mathcal {D} _ {\mathrm{tr}})} [ h (X _ {i}, Y) ] = Z _ {h} (X _ {i}, \mathcal {D} _ {\mathrm{tr}}) \quad a. s. f o r e v e r y i,\tag{29}
$$

then $( M _ { t } ) _ { t \geq 0 }$ is a nonnegative supermartingale under the data-stream distribution $P _ { \left( q _ { i } \right) }$ induced by (q<sub>i</sub>) and the given input mechanism. Consequently,

$$
\mathbb {P} _ {(q _ {i})} \left\{\sup _ {t \geq 0} M _ {t} > \frac {1}{\alpha} \right\} \leq \alpha .
$$

In particular, $i f$ every conditional distribution in a class $\mathcal { Q } _ { 0 }$ satisfies

$$
\mathbb {E} _ {Y \sim r (\cdot | x)} [ h (x, Y) ] \leq Z _ {h} (x, \mathcal {D} _ {\mathrm{tr}}) \quad \text {   for   every   } x,
$$

then

$$
\sup _ {(q _ {i}) \colon q _ {i} \in \mathcal {Q} _ {0}} \mathbb {P} _ {(q _ {i})} \left\{\sup _ {t \geq 0} M _ {t} > \frac {1}{\alpha} \right\} \leq \alpha ,
$$

where the supremum is over all predictable selections from $\mathcal { Q } _ { 0 }$ , and the bound holds for any input process, including an adaptively selected one.

Proof sketch. Because

$$
e _ {i} = \frac {h (X _ {i} , Y _ {i})}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})},
$$

condition (29) is equivalent to

$$
\mathbb {E} [ e _ {i} \mid \mathcal {G} _ {i} ] \leq 1.
$$

Iterated conditioning therefore makes $( M _ { t } )$ a nonnegative supermartingale under the induced process, and Ville’s inequality gives the stated crossing bound. See Section A.11 for details. □

What this result establishes. Whenever (29) holds along the inputs visited by the process, the same time-uniform crossing bound continues to hold under the misspecified target process:

$$
\mathbb {P} _ {(q _ {i})} \left\{\sup _ {t \geq 0} M _ {t} > 1 / \alpha \right\} \leq \alpha .
$$

Thus the original directional test is robust to a correction-dependent class of target misspecifications, even though those targets are not part of the source predictive null. The protected class is characterized below.

This distinction matters because a departure from $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ need not favor the proposed correction. Some departures move outcomes in the opposite direction or leave the moment targeted by h unchanged. The proposition identifies a correction-specific region in which such departures still cannot inflate the probability of false confirmation beyond α.

## 3.4.1 A Correction-Dependent Protected Half-Space

At a fixed input x, define

$$
\mathcal {H} _ {h} (x) := \left\{q (\cdot \mid x): \int h (x, y) q (d y \mid x) \leq Z _ {h} (x, \mathcal {D} _ {\mathrm{tr}}) \right\}.\tag{30}
$$

The mapping

$$
q (\cdot \mid x) \longmapsto \int h (x, y) q (d y \mid x)
$$

is linear in the target conditional distribution. Hence $\mathcal { H } _ { h } ( x )$ is the intersection of the set of conditional distributions with a linear half-space. The source predictive lies on its boundary because

$$
\int h (x, y) p _ {0} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) d y = Z _ {h} (x, \mathcal {D} _ {\mathrm{tr}}).
$$

Every target conditional distribution on the protected side makes the one-step evidence factor have conditional mean at most one. Consequently, if a predictable target sequence satisfies $q _ { i } ( \cdot \mid X _ { i } ) \in { \mathcal { H } } _ { h } ( X _ { i } )$ almost surely at every monitored step, the original wealth process remains a nonnegative supermartingale and retains the same time-uniform crossing bound. The orientation of this protected region is determined entirely by the prespecified correction $h ;$ it is a robustness region for the directional bet, not an enlargement of the original null hypothesis.

The same half-space has a direct connection to the growth analysis in Section 3.3. For any $q ( \cdot \mid x ) \in { \mathcal { H } } _ { h } ( x )$ Jensen’s inequality gives

$$
\mathbb {E} _ {q} [ \log e _ {i} \mid X _ {i} = x ] \leq \log \mathbb {E} _ {q} [ e _ {i} \mid X _ {i} = x ] \leq 0,
$$

whenever the logarithmic expectation is well defined. Thus no target on the protected side can have positive conditional expected log evidence in favor of the correction at that input.

The corrected predictive lies strictly outside this protected half-space whenever the correction is nontrivial at $x ,$ meaning that $h ( x , Y ) / Z _ { h } ( x , D _ { \mathrm { t r } } )$ is not equal to one $p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ -almost surely. Indeed,

$$
\begin{array}{r l r} & & {\mathbb {E} _ {Y \sim p _ {h} (\cdot | x, \mathcal {D} _ {\mathrm{tr}})} \left[ \frac {h (x , Y)}{Z _ {h} (x , \mathcal {D} _ {\mathrm{tr}})} \right] = \mathbb {E} _ {Y \sim p _ {0} (\cdot | x, \mathcal {D} _ {\mathrm{tr}})} \left[ \left\{\frac {h (x , Y)}{Z _ {h} (x , \mathcal {D} _ {\mathrm{tr}})} \right\} ^ {2} \right]} \\ & & {= 1 + \mathrm{Var} _ {Y \sim p _ {0} (\cdot | x, \mathcal {D} _ {\mathrm{tr}})} \left(\frac {h (x , Y)}{Z _ {h} (x , \mathcal {D} _ {\mathrm{tr}})}\right) \in (1, \infty ],} \end{array}\tag{31}
$$

where the second moment is interpreted in the extended sense. This is exactly what should happen: under the corrected predictive represented by the alternative, the one-step evidence factor is expected to grow rather than to retain the supermartingale property used for false-confirmation control.

Why generic closeness to the source is insuficient. The protected half-space is directional; it is not a KL, total-variation, or Hellinger neighborhood around the source predictive. For every nontrivial tilt, there are target distributions outside $\mathcal { H } _ { h } ( x )$ that are arbitrarily close to $p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ in total variation, Hellinger distance, and $D _ { \mathrm { K L } } ( q ( \cdot \mid x ) \parallel p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } ) )$ . Thus being close to the source in a generic distributional metric does not by itself preserve the level-α crossing guarantee. What matters for the original bet is the correction-specific moment comparison in (29). A construction establishing this claim is given in Section A.12.

## 3.4.2 What Failure of the Moment Condition Means

If (29) fails at inputs visited by the process, the one-step factor is no longer guaranteed to be a conditional e-value under q, and the original supermartingale proof is unavailable. This failure does not by itself imply that

$$
\mathbb {P} _ {q} \bigg \{\sup _ {t \geq 0} M _ {t} > \frac {1}{\alpha} \bigg \} > \alpha .
$$

The moment condition is suficient for maximal crossing control and exact for the one-step conditional e-value property, but failure of that suficient condition is not a converse false-confirmation result. The crossing probability may still be at most α for other, distribution-specific reasons; it is simply no longer controlled by Proposition 3.

Negative long-run log-drift does not restore the missing anytime-valid guarantee. Under appropriate ergodic conditions, negative drift implies log $M _ { t } \to - \infty$ almost surely, but the error criterion concerns the probability of at least one boundary crossing over the entire path. A process that eventually decays may still cross early because of high-variance increments or a single heavy-tailed jump. Thus asymptotic decay and control of the maximal process are distinct properties. The cross-family calculations in Section 4.6 and experiments in Section 5.9 illustrate both mechanisms.

The main conclusion is therefore directional. The unmodified e-process has its original level-α guarantee under the source predictive null and retains the same time-uniform crossing bound for any predictable target sequence that stays in the protected half-space at the inputs actually visited. It does not automatically protect a generic neighborhood of the source or an arbitrary user-chosen class of plausible target distributions. Broader uniform protection over a user-specified class would require redesigning the e-process for that class and is beyond the scope of the present paper.

## 3.5 Anytime-Valid Confirmation, Refutation, and Overshoot

The preceding results use an upper boundary to reject the source predictive null in the direction of the proposed correction. A practitioner may also want to stop in the opposite direction when the incoming target outcomes provide suficient evidence against the corrected predictive itself. This section asks:

Can the same monitored wealth process support both anytime-valid relative confirmation and anytime-valid refutation of the proposed correction?

## 3.5.1 Anytime-Valid Two-Boundary Decisions

The answer is yes for the original, exactly normalized likelihood-ratio process $M _ { t }$ from Theorem 1. It relies on the reciprocal likelihood ratio and therefore does not extend to a process formed using a conservative upper bound on the normalizer.

Suppose that $h ( x , y ) > 0$ for $p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ -almost every y, so that $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ and $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ are mutually absolutely continuous. Define the corrected predictive null

$$
H _ {h} ^ {\mathrm{pred}}: Y _ {i} \mid \mathcal {G} _ {i} \sim p _ {h} (\cdot \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}).
$$

Let $\mathcal { P } _ { h } ^ { \mathrm { p r e d } }$ denote the corresponding class of all data-stream distributions, again allowing any admissible input mechanism. The reciprocal e-values are

$$
e _ {i} ^ {\downarrow} = \frac {p _ {0} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})}{p _ {h} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})} = \frac {Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})}{h (X _ {i} , Y _ {i})}, \qquad M _ {t} ^ {\downarrow} = \prod_ {i = 1} ^ {t} e _ {i} ^ {\downarrow} = \frac {1}{M _ {t}}.
$$

By the same argument as Theorem 1, with the roles of $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ and $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ exchanged, $M _ { t } ^ { \downarrow }$ is a nonnegative martingale under $H _ { h } ^ { \mathrm { p r e d } }$ , so

$$
\sup _ {P \in \mathcal {P} _ {h} ^ {\text {pred}}} \mathbb {P} _ {P} \left(\inf _ {t \geq 0} M _ {t} <   \alpha\right) = \sup _ {P \in \mathcal {P} _ {h} ^ {\text {pred}}} \mathbb {P} _ {P} \left(\sup _ {t \geq 0} M _ {t} ^ {\downarrow} > \frac {1}{\alpha}\right) \leq \alpha .
$$

The two-boundary sequential decision. Monitoring the single wealth process $M _ { t }$ gives two anytimevalid rejection rules for the simple predictive pair:

$$
M _ {t} > 1 / \alpha \quad \Longrightarrow \quad \text { reject } H _ {0} ^ {\text { pred }} \text { and   relatively   confirm } p _ {h} (\cdot | \cdot , \mathcal {D} _ {\text { tr }}) \text { over } p _ {0} (\cdot | \cdot , \mathcal {D} _ {\text { tr }}),
$$

and

M<sub>t</sub> < α =⇒ reject $H _ { h } ^ { \mathrm { p r e d } }$ and refute the proposed corrected predictive in favor of $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$

The probability of ever making the upper rejection is at most α when $H _ { 0 } ^ { \mathrm { p r e d } }$ is true, and the probability of ever making the lower rejection is at most α when $H _ { h } ^ { \mathrm { p r e d } }$ is true. Neither boundary proves that the predictive distribution favored by that boundary is the true target predictive: the upper boundary rejects $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ ), whereas the lower boundary rejects $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ . If neither boundary is crossed, the procedure remains inconclusive rather than accepting either model.

This is Wald’s two-boundary sequential probability ratio test (Wald, 1945). The conditional formulation allows arbitrary adaptive input selection provided that the same input mechanism is used under the two predictive hypotheses. Each error guarantee holds only under its corresponding simple null; behavior under other target distributions is characterized in Section 3.4.

The asymmetry of that qualification deserves emphasis, because the lower boundary is the more fragile of the two in practice. The upper boundary is protected under the source predictive null and, by Proposition 3, over the whole protected half-space $\mathcal { H } _ { h } ( x )$ . The lower-boundary guarantee established here is calibrated under $H _ { h } ^ { \mathrm { p r e d } }$ , that is, when the target predictive is exactly the proposed corrected predictive. We do not develop an analogous misspecification-robustness class for the reciprocal process. A target that matches $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ in the feature the correction acts on but difers from it in some other respect is outside $\mathcal { P } _ { h } ^ { \mathrm { p r e d } }$ so the guarantee proved here does not apply. A practitioner who wants to retire a correction should therefore treat a lower crossing as rejection of the entire corrected predictive relative to the source, and not as evidence that the correction magnitude alone was wrong in the direction it was designed to test.

## 3.5.2 Why the Actual Null Crossing Probability Can Be Below α

The boundary $1 / \alpha$ gives a valid upper bound on the probability of ever falsely confirming the correction, but the actual source-null crossing probability is generally smaller than α. This does not change the decision rule; it explains its conservativeness. At the crossing time, the wealth usually jumps beyond $1 / \alpha$ rather than landing exactly on it. The following result quantifies this overshoot and, for the exact predictive likelihood ratio, separates its contribution from the probability of eventual crossing under the corrected predictive.

Proposition 4 (Overshoot identity). Let $P _ { 0 }$ denote the data-stream distribution under $H _ { 0 } ^ { \mathrm { p r e d } }$ , let $( M _ { t } )$ be a nonnegative $P _ { 0 }$ -martingale with $M _ { 0 } = 1$ , and define

$$
\tau^ {*} = \inf \{t: M _ {t} > 1 / \alpha \}.
$$

If $P _ { 0 } ( \tau ^ { * } < \infty ) > 0$ , then

$$
\mathbb {E} _ {P _ {0}} \left[ M _ {\tau^ {*}} \mathbf {1} \{\tau^ {*} <   \infty \} \right] \leq 1, \qquad P _ {0} (\tau^ {*} <   \infty) \leq \frac {1}{\mathbb {E} _ {P _ {0}} [ M _ {\tau^ {*}} \mid \tau^ {*} <   \infty ]} <   \alpha .\tag{32}
$$

For the exactly normalized predictive-correction process

$$
M _ {t} = \prod_ {i = 1} ^ {t} \frac {p _ {h} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})}{p _ {0} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})},
$$

let $P _ { h }$ denote the data-stream distribution under $H _ { h } ^ { \mathrm { p r e d } }$ and suppose that $P _ { h }$ and $P _ { 0 }$ use the same, possibly adaptive, input mechanism. Then $P _ { h } \ll P _ { 0 }$ on every $\mathcal { F } _ { t } , ~ M _ { t }$ is their likelihood ratio. This one-sided absolute continuity follows from Lemma 1 and does not require the strict-positivity assumption used for reciprocal refutation. Moreover,

$$
\mathbb {E} _ {P _ {0}} \left[ M _ {\tau^ {*}} \mathbf {1} \{\tau^ {*} <   \infty \} \right] = P _ {h} (\tau^ {*} <   \infty).\tag{33}
$$

Consequently, whenever $P _ { 0 } ( \tau ^ { * } < \infty ) > 0$

$$
P _ {0} (\tau^ {*} <   \infty) = \frac {P _ {h} (\tau^ {*} <   \infty)}{\mathbb {E} _ {P _ {0}} [ M _ {\tau^ {*}} | \tau^ {*} <   \infty ]}.\tag{34}
$$

In particular, if log $M _ { t } \to + \infty$ $P _ { h }$ -almost surely—as under the positive-drift condition of Corollary 3—then $P _ { h } ( \tau ^ { * } < \infty ) = 1$ , the null crossing probability is positive, and

$$
P _ {0} (\tau^ {*} <   \infty) = \frac {1}{\mathbb {E} _ {P _ {0}} [ M _ {\tau^ {*}} | \tau^ {*} <   \infty ]}.\tag{35}
$$

Proof sketch. Optional stopping for the stopped nonnegative martingale followed by Fatou’s lemma gives (32). For the exact identity, use $M _ { t } = d P _ { h } | _ { \mathcal { F } _ { t } } / d P _ { 0 } | _ { \mathcal { F } _ { t } }$ on each event $\{ \tau ^ { * } = t \}$ and sum over t. See Section A.13 for details. □

Interpretation of the overshoot identity. The first inequality shows strict conservativeness whenever the null crossing probability is positive, because $M _ { \tau ^ { * } } > 1 / \alpha$ on the crossing event. For the predictive likelihood-ratio process, (34) shows that two quantities determine the source-null crossing probability: the mean wealth at crossing under $P _ { 0 }$ and the probability that the upper boundary is ever reached under $P _ { h }$ If positive drift under $P _ { h }$ makes eventual crossing certain, then (35) isolates the overshoot efect exactly. This is an accounting identity, not an additional testing claim. The corresponding empirical check is whether P(cross) E[M ∗ | cross] is close to one; Section 5.10 reports this product for the Gaussian nul experiment.

## 3.6 Practical Monitoring Procedure

The preceding results yield two monitoring modes that should be selected before observing the target outcomes:

1. Exact relative confirmation: use the exact normalizer, preserve the likelihood-ratio and cumulative log-score interpretations, and, when desired, monitor the reciprocal lower boundary to refute the corrected predictive.

2. Conservative source-null confirmation: use a certified upper bound on the normalizer when exact normalization is unavailable, retaining anytime-valid rejection of the source predictive null at a predictable cost in log evidence.

The core construction uses

$$
Z _ {h} (x, \mathcal {D} _ {\mathrm{tr}}) = \mathbb {E} _ {Y \sim p _ {0} (\cdot | x, \mathcal {D} _ {\mathrm{tr}})} [ h (x, Y) ].
$$

When this quantity is available in closed form, exact normalization gives the cleanest procedure. In more complicated models, one may instead use a positive, predictable, certified upper bound

$$
\widetilde {Z} _ {i} (X _ {i}) \geq Z _ {h} (X _ {i}, \mathcal {D} _ {\mathrm{tr}})\tag{36}
$$

computed after observing $X _ { i }$ but before observing Y<sub>i</sub>. Then

$$
\widetilde {e} _ {i} = \frac {h (X _ {i} , Y _ {i})}{\widetilde {Z} _ {i} (X _ {i})}
$$

satisfies

$$
\mathbb {E} [ \widetilde {e} _ {i} \mid \mathcal {G} _ {i} ] = \frac {Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})}{\widetilde {Z} _ {i} (X _ {i})} \leq 1
$$

under the source predictive null. Its running product is therefore a nonnegative supermartingale. Relative to exact normalization, the one-step log-evidence loss is

$$
\log e _ {i} - \log \widetilde {e} _ {i} = \log \frac {\widetilde {Z} _ {i} (X _ {i})}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})} \geq 0.\tag{37}
$$

A loose upper bound is safe but may substantially delay confirmation. Unless equality holds, the approximate factor is no longer the exact likelihood ratio $p _ { h } ( Y _ { i } \mid X _ { i } , \mathcal { D } _ { \mathrm { t r } } ) / p _ { 0 } ( Y _ { i } \mid X _ { i } , \mathcal { D } _ { \mathrm { t r } } )$ ; its log wealth is the exact cumulative log-score advantage minus the accumulated normalizer penalty.

The direction of approximation is essential. A denominator smaller than $Z _ { h } ( X _ { i } , { D _ { \mathrm { t r } } } )$ makes the conditional mean exceed one. An ordinary unbiased Monte Carlo estimate is not generally safe either. If a positive estimate $\widehat { Z } _ { i }$ is conditionally independent of $Y _ { i }$ given $\mathcal { G } _ { i }$ and satisfies $\mathbb { E } [ \widehat { Z } _ { i } ^ { \cdot } | \mathcal { G } _ { i } ] = \widehat { Z } _ { h } ( X _ { i } , \mathcal { D } _ { \mathrm { t r } } )$ , then Jensen’s inequality gives

$$
\mathbb {E} \left[ \frac {h (X _ {i} , Y _ {i})}{\widehat {Z} _ {i}} \mid \mathcal {G} _ {i} \right] = Z _ {h} (X _ {i}, \mathcal {D} _ {\mathrm{tr}}) \mathbb {E} \left[ \frac {1}{\widehat {Z} _ {i}} \mid \mathcal {G} _ {i} \right] \geq 1,
$$

with strict inequality unless $\widehat { Z } _ { i } = Z _ { h } ( X _ { i } , { \mathcal { D } } _ { \mathrm { t r } } )$ almost surely. Reciprocal refutation also requires exact normalization. Under the strict-positivity condition used for reciprocal refutation in Section 3.5.1, the corrected predictive null gives

$$
\mathbb {E} \left[ \frac {\widetilde {Z} _ {i} (X _ {i})}{h (X _ {i} , Y _ {i})} \mid \mathcal {G} _ {i} \right] = \frac {\widetilde {Z} _ {i} (X _ {i})}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})} \geq 1.
$$

Further numerical details are given in Section A.4; all experiments use closed-form Gaussian normalizers. In Algorithm 1, exact mode has $S _ { i } = \log M _ { i } .$ , the cumulative log-score advantage of $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ over $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ ). An upper crossing rejects $H _ { 0 } ^ { \mathrm { p r e d } }$ and gives anytime-valid relative confirmation of the corrected predictive; a lower crossing rejects $H _ { h } ^ { \mathrm { p r e d } }$ and refutes it relative to the source. With a certified upperbound normalizer, an upper crossing still rejects the source predictive null, but the accumulated wealth is conservative directional evidence and no lower refutation boundary is available. The algorithm concerns only corrections to $Y \mid X ;$ pure covariate shift requires separate input-stream methods (Choi, 2026a).

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Sequential evidence for a prespecified predictive correction
Require: Source predictive $p_0(y \mid x, \mathcal{D}_{\text{tr}})$, fixed correction $h(x, y)$, level $\alpha$, and either the exact normalizer or a predictable certified upper bound
1: $S_0 \leftarrow 0$
2: for $i = 1, 2, \ldots$ do
3: Observe $X_i$ and compute $D_i^{\text{use}} = Z_h(X_i, \mathcal{D}_{\text{tr}})$ in exact mode or $D_i^{\text{use}} = \widetilde{Z}_i(X_i)$ in conservative mode
4: Observe $Y_i$
5: Compute $\ell_i \leftarrow \log h(X_i, Y_i) - \log D_i^{\text{use}}$
6: Update $S_i \leftarrow S_{i-1} + \ell_i$
7: if $S_i &gt; \log(1/\alpha)$ then
8: stop: reject the source predictive null and report relative evidence in the direction of the correction
9: else if exact two-boundary mode and $S_i &lt; \log \alpha$ then
10: stop: reject the corrected predictive null and refute the correction relative to the source
</div>

## 3.7 Predictable Corrections

The fixed-correction setting is the cleanest for interpretation. Validity also permits corrections chosen predictably.

Proposition 5 (Predictable tilts). At time i, suppose that after observing $X _ { i }$ but before observing $Y _ { i }$ , the practitioner chooses a nonnegative function $h _ { i } ( X _ { i } , \cdot )$ that is $\mathcal { G } _ { i }$ -measurable. Let

$$
Z _ {i} (X _ {i}) = \int h _ {i} (X _ {i}, y) p _ {0} (y \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}) d y
$$

be finite and positive, and define

$$
e _ {i} = \frac {h _ {i} (X _ {i} , Y _ {i})}{Z _ {i} (X _ {i})}.
$$

Then $e _ { i }$ is a conditional e-value under $H _ { 0 } ^ { \mathrm { p r e d } }$ , and $\textstyle \prod _ { i = 1 } ^ { t } e _ { i }$ is a nonnegative martingale under $H _ { 0 } ^ { \mathrm { p r e d } }$ , hence an e-process.

Proof sketch. After conditioning on $\mathcal { G } _ { i } ,$ the predictable tilt is fixed as a function of the yet-unobserved outcome, so the same normalization argument applies. See Section A.10. □

Predictable updating can be useful for adaptive betting or safe model monitoring, but it changes the inferential object. A fixed h is designed to confirm one prespecified correction. A predictable sequence $h _ { i }$ instead shows that an adaptive betting strategy has accumulated evidence against the source predictive null; without additional precommitment, it does not confirm any single correction selected after observing the stream.

## 4 Structured Conditional Predictive Corrections

In this section, we instantiate the general construction of Section 3.2 for several structured predictive corrections. The common principle is that scientific or operational knowledge specifies, before monitoring, how the source conditional predictive $p _ { 0 } ( y \mid x , \mathcal { D } _ { \mathrm { t r } } )$ should be modified. The resulting e-process then evaluates whether that particular corrected predictive outpredicts its prespecified reference on the incoming target stream. The procedure does not estimate an unrestricted target distribution, and a crossing does not by itself identify the physical mechanism responsible for the evidence.

The corrections considered here act on $Y \mid X$ . A label-shift assumption induces a particular correction of the conditional label predictive, whereas concept drift motivates direct corrections to the conditional response distribution. Pure covariate shift changes the marginal input distribution while leaving $Y \mid X$ unchanged and therefore requires a separate input-stream construction, as developed in the covariatebalance paper (Choi, 2026a). A full joint-shift analysis would combine input-distribution evidence with the conditional predictive evidence studied here.

The subsections serve complementary purposes. Section 4.1 derives the label-shift-induced correction. Section 4.2 develops Gaussian mean and variance corrections and shows how evidence behaves when their magnitudes are misspecified. Section 4.3 gives a unifying exponential-tilt representation. Section 4.4 handles prespecified uncertainty over the correction, while Section 4.5 changes the decision problem by replacing the source reference with an operational tolerance boundary. Finally, Section 4.6 studies what the structured wealth processes do when the actual target change belongs to a diferent mechanism family. Table 1 summarizes the inferential role of each construction.

Table 1: Representative structured predictive corrections and their operational interpretations. The first two rows specify a corrected conditional predictive directly; the mixture construction aggregates prespecified correction paths, and the tolerance construction deliberately changes the reference and the null hypothesis.

<table><tr><td>Setting or con-struction</td><td>Structural premise</td><td>Inferential object</td><td>Operational question</td></tr><tr><td>Label shift</td><td> $P_{t}^{Y} \neq P_{s}^{Y}$ , with  $P_{t}^{X|Y} = P_{s}^{X|Y}$ </td><td>Label tilt  $h(x,y) = w(y)$ , inducing  $p_{h}(y \mid x, \mathcal{D}_{\text{tr}})$ </td><td>Deploy  $p_{h}(\cdot \mid \cdot, \mathcal{D}_{\text{tr}})$  or re-tain  $p_{0}(\cdot \mid \cdot, \mathcal{D}_{\text{tr}})$ ?</td></tr><tr><td>Concept drift</td><td> $P_{t}^{Y|X} \neq P_{s}^{Y|X}$ </td><td>Tilt encoding a mean, variance, subgroup, or other response correction</td><td>Apply the structured cor-rection or retain the source predictive?</td></tr><tr><td>Mixture over cor-rections</td><td>A correction family is prespeci-fied, but its index is uncertain</td><td>Weighted mixture  $M_{t}^{\text{mix}} = \int M_{t}(\theta) d\Pi(\theta)$  of full wealth paths</td><td>Has the prespecified family accumulated global evidence against the source?</td></tr><tr><td>Beyond-tolerance comparison</td><td>A tolerated region and an action-able design point are prespeci-fied</td><td>Ratio  $p_{\text{alarm}}(y \mid x, \mathcal{D}_{\text{tr}})/p_{\text{tol}}(y \mid x, \mathcal{D}_{\text{tr}})$ </td><td>Is there sufficient evi-dence to act beyond the tolerated region?</td></tr></table>

## 4.1 Label-Shift Correction

Under label shift, the conditional input distribution given the label is stable,

$$
P _ {t} ^ {X | Y} = P _ {s} ^ {X | Y},
$$

while the label marginal changes, $P _ { t } ^ { Y } \neq P _ { s } ^ { Y }$ . Let $w ( y ) \geq 0$ be a prespecified label weight with a finite, positive normalizer under $p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ at every relevant input. The corresponding tilt and corrected predictive are

$$
h (x, y) = w (y), \qquad p _ {h} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = \frac {w (y) p _ {0} (y \mid x , \mathcal {D} _ {\mathrm{tr}})}{\mathbb {E} _ {Y \sim p _ {0} (\cdot | x , \mathcal {D} _ {\mathrm{tr}})} [ w (Y) ]}.\tag{38}
$$

Multiplying w by a positive constant leaves $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ unchanged because that constant cancels in the normalizer. The one-step e-value is

$$
e _ {i} = \frac {w (Y _ {i})}{\mathbb {E} _ {Y \sim p _ {0} (\cdot | X _ {i} , \mathcal {D} _ {\mathrm{tr}})} [ w (Y) ]}.\tag{39}
$$

If the source predictive equals the source conditional law $P _ { s } ^ { Y | X }$ , the target satisfies exact label shift, and $P _ { t } ^ { Y } \ll P _ { s } ^ { Y }$ , choosing

$$
w (y) = \frac {d P _ {t} ^ {Y}}{d P _ {s} ^ {Y}} (y)
$$

recovers the target conditional law $P _ { \mathrm { \Delta } t } ^ { Y | X }$ through Bayes’ rule. If $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ is instead a fitted or posterior predictive approximation to $P _ { s } ^ { Y | X }$ , the same weighting still defines a valid prespecified predictive correction, but it need not equal the exact target conditional distribution. The e-process assesses the induced corrected predictive itself; it does not require the label-shift model to be exactly correct. This specializes the general framework to anytime-valid confirmation of a prespecified label-shift correction (Choi, 2026b).

Deploy-or-retain decision. An external study, a known intervention, historical information, or a planned change in the target population may suggest $w ( y )$ before target outcomes are observed. The operational choice is whether to retain $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ or deploy the induced $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ . This choice is especially relevant when target labels are expensive, delayed, or revealed sequentially (Lipton et al., 2018; Alexandari et al., 2020; Garg et al., 2020). An upper-boundary crossing provides anytime-valid relative evidence for deploying $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ over $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ . Failure to cross is inconclusive: the correction may not be predictively preferable, or the observed labels may simply be insuficiently informative. By Section 3.3, positive expected log-growth requires only that the induced corrected predictive be closer to the actual target predictive than the source predictive is in conditional KL divergence. The proposed label weights therefore need not coincide with the exact target label ratio to accumulate positive evidence.

## 4.2 Concept-Drift Corrections

Here concept drift refers to a change in the conditional response distribution,

$$
P _ {t} ^ {Y | X} \neq P _ {s} ^ {Y | X}.
$$

A tilt $h ( x , y )$ can encode a prespecified modification of this conditional distribution. The setting is most useful when an intervention, protocol change, new deployment site, or engineering analysis suggests a particular form of change before monitoring begins (Qin, 2012; Kelly et al., 2019; Subbaswamy and Saria 2020). The e-process then asks whether that proposed correction predicts the target outcomes better than retaining the source predictive. It is not a generic detector that searches the observed target stream for an unknown form of concept drift.

The following Gaussian examples separate two common operational questions: whether to shift the conditional center and whether to widen or narrow the conditional predictive uncertainty. They also make the relative nature of confirmation explicit: a correction may accumulate positive evidence even when its magnitude is not exactly correct.

## 4.2.1 Conditional Mean Correction

Suppose the source predictive is

$$
p _ {0} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = \mathcal {N} \big (y \mid \mu_ {0} (x), \sigma_ {0} ^ {2} (x) \big),
$$

and the proposed correction shifts the conditional mean along a known shape $g ( x )$ by a prespecified coeficient δ:

$$
p _ {h} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = \mathcal {N} \big (y \mid \mu_ {0} (x) + \delta g (x), \sigma_ {0} ^ {2} (x) \big).
$$

The one-step log e-value is

$$
\log e _ {i} = \frac {\delta g (X _ {i}) \{Y _ {i} - \mu_ {0} (X _ {i}) \}}{\sigma_ {0} ^ {2} (X _ {i})} - \frac {\delta^ {2} g ^ {2} (X _ {i})}{2 \sigma_ {0} ^ {2} (X _ {i})}.\tag{40}
$$

Thus the process compares the proposed mean-corrected predictive with the source predictive along the prespecified direction g. A constant $g ( x ) = 1$ gives a common additive ofset, whereas a nonconstant g permits the correction to vary across subgroups, doses, instruments, or other scientifically meaningful input characteristics.

Deciding whether to apply a directional ofset. Instrument recalibration, a bridging experiment, or simulator-to-reality analysis may suggest the ofset $\delta g ( x )$ before new outcomes arrive (Workman Jr., 2018; Kennedy and O’Hagan, 2001). The operational choice is whether to retain $\mu _ { 0 } ( x )$ or deploy $\mu _ { 0 } ( x ) + \delta g ( x )$ Sequential evidence is useful when calibration outcomes arrive one at a time or when data collection may stop as soon as the proposed adjustment is suficiently supported.

Magnitude mismatch. Suppose the actual target predictive is Gaussian with conditional mean $\mu _ { 0 } ( x ) + \delta ^ { * } g ( x )$ and variance $\sigma _ { 0 } ^ { 2 } ( x )$ , whereas the proposed correction uses δ. The conditional drift is

$$
\Gamma_ {\delta} (x) = \frac {g ^ {2} (x)}{\sigma_ {0} ^ {2} (x)} \left(\delta \delta^ {*} - \frac {\delta^ {2}}{2}\right) = \frac {g ^ {2} (x)}{2 \sigma_ {0} ^ {2} (x)} \delta (2 \delta^ {*} - \delta).\tag{41}
$$

At an informative input, $g ( x ) \neq 0 ,$ , positive drift is therefore equivalent to

$$
\delta (2 \delta^ {*} - \delta) > 0.
$$

For the common case $\delta ^ { * } > 0$ with a proposed positive correction, this reduces to

$$
0 <   \delta <   2 \delta^ {*}.
$$

A correction with $0 < \delta < \delta ^ { * }$ underestimates the true shift but still improves on the source predictive. A correction with $\delta ^ { * } < \delta < 2 \delta ^ { * }$ overestimates the shift but remains closer to the target mean than the source mean does. When $\delta > 2 \delta ^ { * }$ , the proposed ofset overshoots so severely that it is worse in expected log score than applying no correction. The drift is maximized at $\delta = \delta ^ { * }$

The factor

$$
\frac {g ^ {2} (x)}{\sigma_ {0} ^ {2} (x)}
$$

is the local information scale for this comparison. Inputs at which the proposed mean change is large relative to the predictive variance accumulate evidence more rapidly. This connects the structured correction directly to the adaptive-design result studied in Section 5.8.

## 4.2.2 Conditional Variance Correction

Under the same Gaussian source predictive, suppose the conditional mean is retained while the variance is multiplied by a prespecified factor $c > 0 :$

$$
p _ {h} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = \mathcal {N} \big (y \mid \mu_ {0} (x), c \sigma_ {0} ^ {2} (x) \big).
$$

Then

$$
\log e _ {i} = - \frac {1}{2} \log c + \frac {1}{2} \left(1 - \frac {1}{c}\right) \frac {\{Y _ {i} - \mu_ {0} (X _ {i}) \} ^ {2}}{\sigma_ {0} ^ {2} (X _ {i})}.\tag{42}
$$

For $c > 1$ , large standardized residuals favor variance inflation. For $0 < c < 1$ , small standardized residuals favor variance contraction.

Deciding whether predictive uncertainty should be widened or narrowed. A change in assay protocol, laboratory batch, sensor precision, or operating conditions may leave the conditional mean approximately stable while changing response variability (Johnson et al., 2007; Leek et al., 2010). A prespecified factor c then represents an operational proposal to widen or narrow the predictive distribution. Relative confirmation may support revised predictive intervals, quality-control limits, or downstream risk thresholds while controlling false confirmation under the source predictive null.

Magnitude mismatch and mechanism ambiguity. Suppose the actual target predictive is Gaussian with the same conditional mean and variance $c ^ { * } \sigma _ { 0 } ^ { 2 } ( x )$ . The conditional drift of a proposed factor c is

$$
\Gamma_ {c} (x) = - \frac {1}{2} \log c + \frac {1}{2} \left(1 - \frac {1}{c}\right) c ^ {*}.\tag{43}
$$

For $c \neq 1$ , define

$$
\rho (c) := \frac {c \log c}{c - 1}.
$$

Then

$$
\Gamma_ {c} (x) > 0 \quad \Longleftrightarrow \quad \left\{ \begin{array}{l l} c ^ {*} > \rho (c), & c > 1, \\ c ^ {*} <   \rho (c), & 0 <   c <   1. \end{array} \right.\tag{44}
$$

Moreover,

$$
1 <   \rho (c) <   c \quad \text { when } c > 1, \qquad c <   \rho (c) <   1 \quad \text { when } 0 <   c <   1.
$$

Thus a variance-inflation proposal may overstate the actual inflation and still outpredict the source, and a variance-contraction proposal may similarly overstate the contraction while remaining predictively preferable. Correct specification, $c = c ^ { * }$ , maximizes expected log-growth over $c > 0 .$ , but exact specification is not required for positive drift.

The interpretation is nevertheless predictive rather than mechanistic. The e-value in (42) is driven by squared residuals, which can be enlarged by a mean shift, heavy tails, outliers, or other misspecification as well as by a genuine variance increase. A crossing therefore favors the variance-corrected predictive over the source predictive; it does not establish variance change as the unique cause. The cross-family calculations in Section 4.6 quantify this limitation.

## 4.3 General Exponential-Family Predictive Tilts

The preceding examples are instances of a common exponential-tilt construction. Let $\phi ( x , y ) \in \mathbb { R } ^ { d }$ be a prespecified vector of interpretable features and let $\eta \in \mathbb { R } ^ { d }$ be a prespecified correction coeficient. Define

$$
h _ {\eta} (x, y) = \exp \{\eta^ {\top} \phi (x, y) \}, \qquad Z _ {\eta} (x) = \mathbb {E} _ {Y \sim p _ {0} (\cdot | x, \mathcal {D} _ {\mathrm{tr}})} \left[ \exp \{\eta^ {\top} \phi (x, Y) \} \right], \qquad \psi_ {x} (\eta) = \log Z _ {\eta} (x).\tag{45}
$$

Whenever $Z _ { \eta } ( x )$ is finite and positive, the corrected predictive is

$$
p _ {\eta} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = \exp \{\eta^ {\top} \phi (x, y) - \psi_ {x} (\eta) \} p _ {0} (y \mid x, \mathcal {D} _ {\mathrm{tr}}),\tag{46}
$$

and the one-step log e-value is

$$
\log e _ {i} = \eta^ {\top} \phi (X _ {i}, Y _ {i}) - \psi_ {X _ {i}} (\eta).\tag{47}
$$

The feature vector $\phi$ determines which aspects of the predictive distribution are modified, whereas η determines the proposed direction and magnitude in that feature space. In the primary confirmatory interpretation, both are fixed before target outcomes are observed. Predictable updates are valid under Section 3.7, but then the result concerns an adaptive betting strategy rather than one fixed correction.

Label-shift correction. For categorical $Y \in \{ 1 , \ldots , K \}$ , take

$$
\phi_ {k} (x, y) = \mathbf {1} \{y = k \}, \qquad k = 1, \dots , K,
$$

and set $\eta _ { k } = \log { w _ { k } }$ for positive class weights $w _ { k }$ . Then

$$
h _ {\eta} (x, y) = w _ {y}, \qquad p _ {\eta} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = \frac {w _ {y} p _ {0} (y \mid x , \mathcal {D} _ {\mathrm{tr}})}{\sum_ {k = 1} ^ {K} w _ {k} p _ {0} (k \mid x , \mathcal {D} _ {\mathrm{tr}})}.
$$

This recovers $\operatorname { E q . }$ (38). Adding the same constant to every $\eta _ { k }$ , equivalently multiplying every $w _ { k }$ by the same positive factor, leaves the corrected predictive unchanged; only relative class weights are identifiable.

Conditional mean correction. For the Gaussian source predictive, take

$$
\phi_ {\mathrm{mean}} (x, y) = \frac {g (x) \{y - \mu_ {0} (x) \}}{\sigma_ {0} ^ {2} (x)}
$$

and $\eta = \delta .$ . Then

$$
Z _ {\delta} (x) = \exp \left\{\frac {\delta^ {2} g ^ {2} (x)}{2 \sigma_ {0} ^ {2} (x)} \right\},
$$

and normalization gives

$$
p _ {\delta} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = \mathcal {N} \big (y \mid \mu_ {0} (x) + \delta g (x), \sigma_ {0} ^ {2} (x) \big).
$$

Thus the Gaussian mean correction is an exponential tilt in a variance-scaled residual.

Conditional variance correction. Under the same source predictive, take

$$
\phi_ {\mathrm{var}} (x, y) = \frac {\{y - \mu_ {0} (x) \} ^ {2}}{2 \sigma_ {0} ^ {2} (x)}, \qquad \eta = 1 - \frac {1}{c}.
$$

Then

$$
h _ {c} (x, y) = \exp \biggl \{\left(1 - \frac {1}{c}\right) \frac {\{y - \mu_ {0} (x) \} ^ {2}}{2 \sigma_ {0} ^ {2} (x)} \biggr \}, \qquad Z _ {c} (x) = \sqrt {c},
$$

and the normalized predictive is

$$
p _ {c} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = \mathcal {N} \big (y \mid \mu_ {0} (x), c \sigma_ {0} ^ {2} (x) \big).
$$

Thus the variance correction is an exponential tilt in the squared standardized residual.

Subgroup-specific and combined corrections. Interactions between response features and prespecified input indicators produce localized corrections. For example, if $\mathcal { A } _ { 1 } , \ldots , \mathcal { A } _ { J }$ are prespecified subgroups, features

$$
\phi_ {j} (x, y) = \mathbf {1} \{x \in \mathcal {A} _ {j} \} \frac {y - \mu_ {0} (x)}{\sigma_ {0} ^ {2} (x)}
$$

with coeficients $\eta _ { j }$ encode subgroup-specific mean ofsets. Interactions between class and subgroup indicators similarly encode subgroup-specific label corrections. A feature vector containing both linear and quadratic residual terms can encode a joint mean-and-variance correction, and dose, treatment, instrument, or batch variables can enter through prespecified interactions.

## 4.4 Prespecified Mixtures over Correction Uncertainty

A practitioner may know the broad form of a correction while remaining uncertain about its magnitude, direction, or mechanism index. Let $\{ h _ { \theta } : \theta \in \Theta \}$ be a prespecified family, let Π be a probability measure on Θ fixed before monitoring, and define

$$
M _ {t} (\theta) = \prod_ {i = 1} ^ {t} e _ {i} (\theta).
$$

Proposition 6 (Prespecified mixture and correction panel). Assume that every $h _ { \theta }$ satisfies (7) and that $( \theta , \omega ) \mapsto M _ { t } ( \theta ) ( \omega )$ is jointly measurable with respect to $B ( \Theta ) \otimes \mathcal { F } _ { t }$ . By Theorem 1, for every $P \in \mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$ and every $\theta ,$ the process $( M _ { t } ( \theta ) ) _ { t \geq 0 }$ is a nonnegative P-martingale with $M _ { 0 } ( \theta ) = 1$ . Then

$$
M _ {t} ^ {\mathrm{mix}} = \int M _ {t} (\theta) d \Pi (\theta)\tag{48}
$$

is a nonnegative martingale under every $P \in \mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$ , with $M _ { 0 } ^ { \mathrm { m i x } } = 1$ , and hence is an e-process for the source predictive null class. For a finite panel $\{ h ^ { ( 1 ) } , \ldots , h ^ { ( K ) } \}$ with prespecified weights $\pi _ { k } \geq 0$ satisfying $\textstyle \sum _ { k } \pi _ { k } = 1$ 2

$$
M _ {t} ^ {\mathrm{panel}} = \sum_ {k = 1} ^ {K} \pi_ {k} M _ {t} ^ {(k)}
$$

therefore provides an anytime-valid family-level test at level α.

Proof sketch. For any $P \in \mathcal { P } _ { 0 } ^ { \mathrm { p r e d } }$ , conditional Tonelli’s theorem and the component martingale property give

$$
\mathbb {E} _ {P} [ M _ {t} ^ {\mathrm{mix}} \mid \mathcal {F} _ {t - 1} ] = \int \mathbb {E} _ {P} [ M _ {t} (\theta) \mid \mathcal {F} _ {t - 1} ] d \Pi (\theta) = \int M _ {t - 1} (\theta) d \Pi (\theta) = M _ {t - 1} ^ {\mathrm{mix}}.
$$

See Section A.15 for the full argument.

The mixture in (48) averages complete wealth paths:

$$
\int \prod_ {i = 1} ^ {t} e _ {i} (\theta) d \Pi (\theta).
$$

It is generally diferent from the product of pointwise mixtures

$$
\prod_ {i = 1} ^ {t} \int e _ {i} (\theta) d \Pi (\theta).
$$

The first construction corresponds to assigning initial wealth across persistent correction indices and retaining those indices through time. It is the relevant object when the uncertainty concerns which one of a prespecified set of corrections may be useful.

Each component is individually an anytime-valid test, but inspecting many components and reporting whichever one crosses or attains the largest wealth does not control the resulting familywise or postselection claim at level α. A crossing of $M _ { t } ^ { \operatorname* { m i x } }$ supports one global statement: the prespecified weighted correction family has accumulated evidence against the source predictive null. It does not identify a unique $\theta ,$ confirm every component, or license an unadjusted claim about the data-selected best component. Simultaneous or selected componentwise claims require an explicit error allocation or another prespecified rule.

Correction uncertainty. When prior knowledge identifies the direction of a correction but leaves its magnitude uncertain, a prespecified mixture can distribute evidence across a set of plausible corrections without committing to a single one before monitoring. Choosing a particular correction for subsequent deployment, however, is a separate post-confirmation selection or decision problem unless the selection rule is itself prespecified.

## 4.5 Beyond-Tolerance Confirmation

In many applications, the relevant question is not whether the target predictive difers at all from the source, but whether the departure is large enough to justify action. This is a diferent inferential problem from the target-misspecification robustness analysis in Section 3.4. There the original null remains the source predictive and one asks where its crossing guarantee happens to persist. Here the practitioner deliberately defines a new null representing an acceptable region of change.

Let $p _ { \mathrm { t o l } } ( y \mid x , \mathcal { D } _ { \mathrm { t r } } )$ denote the predictive distribution at the largest acceptable shift, and let $p _ { \mathrm { a l a r m } } ( y \mid x , \mathcal { D } _ { \mathrm { t r } } )$ denote a prespecified actionable design point beyond that boundary. Define

$$
e _ {i} ^ {\mathrm{tol}} = \frac {p _ {\mathrm{alarm}} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})}{p _ {\mathrm{tol}} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})}, \qquad M _ {t} ^ {\mathrm{tol}} = \prod_ {i = 1} ^ {t} e _ {i} ^ {\mathrm{tol}}.\tag{49}
$$

The evidence is now anchored at the tolerated boundary rather than at the uncorrected source predictive. An upper crossing favors the actionable predictive over the tolerated-boundary predictive on the observed target stream.

Acting only on practically meaningful change. Small deviations may be scientifically real but too small to justify recalibration, process interruption, clinical review, or another costly intervention. A tolerance policy therefore specifies, before monitoring, both an acceptable region and an actionable design point. The question becomes “Is there suficient evidence to act beyond tolerance?” rather than “Has any change occurred?” (Podkopaev and Ramdas, 2022). A crossing remains a relative predictive statement: it does not estimate the exact target parameter, prove that the target has reached the nominal alarm design point, or identify a unique mechanism.

Treating (49) merely as a likelihood ratio with $p _ { \mathrm { t o l } }$ as reference would control false alarms only at that single boundary distribution. A genuine tolerance policy should control false alarms throughout the entire acceptable region. A regular one-parameter exponential-tilt family provides this stronger composite-null guarantee.

Proposition 7 (False-alarm control over a composite tolerated region). Let $\phi : \mathcal { X } \times \mathcal { Y }  \mathbb { R }$ and

$$
p _ {\eta} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = \frac {\exp \{\eta \phi (x , y) \} p _ {0} (y \mid x , \mathcal {D} _ {\mathrm{tr}})}{Z _ {\eta} (x)}, \qquad \psi_ {x} (\eta) = \log Z _ {\eta} (x),
$$

define a one-parameter tilted family. Assume that there is an open interval $\mathcal { T } ,$ common to all relevant inputs, on which every $\psi _ { x }$ is finite. Fix $\eta _ { \mathrm { t o l } } \in \mathcal { T }$ and $\eta _ { \mathrm { a l a r m } } = \eta _ { \mathrm { t o l } } + \Delta \in \mathcal { T }$ with $\Delta > 0$ , and set

$$
e _ {i} ^ {\mathrm{tol}} = \frac {p _ {\eta_ {\mathrm{alarm}}} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})}{p _ {\eta_ {\mathrm{tol}}} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})} = \exp \{\Delta \phi (X _ {i}, Y _ {i}) \} \frac {Z _ {\eta_ {\mathrm{tol}}} (X _ {i})}{Z _ {\eta_ {\mathrm{alarm}}} (X _ {i})}.
$$

Suppose that

$$
Y _ {i} \mid \mathcal {G} _ {i} \sim p _ {\eta_ {i}} (\cdot \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}),
$$

where $\eta _ { i }$ is $\mathcal { G } _ { i }$ -measurable, takes values in I, and satisfies $\eta _ { i } \leq \eta _ { \mathrm { t o l } }$ almost surely for every i. Then

$$
\mathbb {E} [ e _ {i} ^ {\mathrm{tol}} \mid \mathcal {G} _ {i} ] \leq 1.
$$

Let $\mathcal { P } _ { 0 } ^ { \mathrm { t o l } }$ denote the class of all data-stream distributions induced by predictable sequences $( \eta _ { i } )$ satisfying $\eta _ { i } \leq \eta _ { \mathrm { t o l } }$ almost surely for every i, together with any admissible input process. Consequently, $( M _ { t } ^ { \mathrm { t o l } } ) _ { t \geq 0 }$ is a nonnegative supermartingale under every $P \in \mathcal { P } _ { 0 } ^ { \mathrm { t o l } }$ and

$$
\sup _ {P \in \mathcal {P} _ {0} ^ {\mathrm{tol}}} \mathbb {P} _ {P} \left\{\sup _ {t \geq 0} M _ {t} ^ {\mathrm{tol}} > \frac {1}{\alpha} \right\} \leq \alpha .
$$

Thus the deliberately specified composite null is the collection of target streams whose conditional natural parameter never exceeds the tolerated boundary.

Proof sketch. Conditional on $X _ { i } = x$ and under $p _ { \eta _ { i } }$

$$
\mathbb {E} [ e _ {i} ^ {\mathrm{tol}} \mid \mathcal {G} _ {i} ] = \exp \{\psi_ {x} (\eta_ {i} + \Delta) - \psi_ {x} (\eta_ {i}) - \psi_ {x} (\eta_ {\mathrm{tol}} + \Delta) + \psi_ {x} (\eta_ {\mathrm{tol}}) \}.
$$

For a convex function, an increment of fixed length $\Delta$ is nondecreasing in its starting point. Since $\eta _ { i } \leq \eta _ { \mathrm { t o l } } .$ the exponent is nonpositive. See Section A.14 for the full argument. □

Remark 1 (Where evidence begins to favor action). Assume in addition that $\psi _ { x }$ is diferentiable. Under $p _ { \eta }$ , the conditional drift at input x is

$$
\mathbb {E} [ \log e _ {i} ^ {\mathrm{tol}} \mid X _ {i} = x ] = \Delta \psi_ {x} ^ {\prime} (\eta) - \{\psi_ {x} (\eta_ {\mathrm{tol}} + \Delta) - \psi_ {x} (\eta_ {\mathrm{tol}}) \}.\tag{50}
$$

The mean value theorem gives at least one $\eta _ { \mathrm { m i d } } ( x ) \in ( \eta _ { \mathrm { t o l } } , \eta _ { \mathrm { a l a r m } } )$ satisfying

$$
\psi_ {x} ^ {\prime} \{\eta_ {\mathrm{mid}} (x) \} = \frac {\psi_ {x} (\eta_ {\mathrm{tol}} + \Delta) - \psi_ {x} (\eta_ {\mathrm{tol}})}{\Delta}.
$$

If $\psi _ { x }$ is strictly convex, this point is unique and the drift is positive exactly when $\eta > \eta _ { \mathrm { m i d } } ( x )$ . Hence the parameter line has three operational regions: $\eta \leq \eta _ { \mathrm { t o l } }$ is the tolerated region with false-alarm control; $\eta _ { \mathrm { t o l } } < \eta \leq \eta _ { \mathrm { m i d } } ( x )$ lies outside tolerance but still favors the tolerated-boundary predictive in expected log score; and $\eta > \eta _ { \mathrm { m i d } } ( x )$ gives positive local evidence growth toward an alarm. Thus the procedure need not wait until the true parameter reaches $\eta _ { \mathrm { a l a r m } }$ , but not every departure just beyond tolerance has positive $d r i f t .$

When $\psi _ { x }$ is a nonconstant quadratic function, as at informative inputs in the Gaussian mean-shift family of Section 4.2.1,

$$
\eta_ {\mathrm{mid}} (x) = \frac {\eta_ {\mathrm{tol}} + \eta_ {\mathrm{alarm}}}{2}.
$$

The indiference region is therefore a structural consequence of comparing two separated predictive design points, not a peculiarity of one numerical example.

The Gaussian mean-shift case is studied in Section 5.4. Proposition 7 is deliberately one-dimensional. For a vector parameter $\eta \in \mathbb { R } ^ { d }$ and a fixed alarm direction $\Delta .$ , convexity gives an analogous ordering along the ray $\left\{ \eta _ { \mathrm { t o l } } - s \Delta : s \geq 0 \right\}$ , but $\eta \mapsto \psi _ { x } ( \eta + \Delta ) - \psi _ { x } ( \eta )$ need not define a monotone half-space over all of $\mathbb { R } ^ { d }$

## 4.6 Cross-Family Drift Calculus

The drift formula (20) can be evaluated under target distributions that do not belong to the structural family used to construct the e-process. Together with the protected-half-space analysis in Section 3.4.1, these calculations clarify a central interpretive limitation: a crossing supports the chosen corrected predictive relative to its reference, but the statistic used by that correction may also respond to a diferent physical mechanism. The following results organize the stress tests in Section 5.9.

Remark 2 (Convex tilts and mean-preserving spreads). Several corrections above use tilts that are convex in y. The mean correction uses the exponential of a linear function, and a variance-inflation correction uses the exponential of a positive quadratic. $I f q ( \cdot \mid x )$ is a mean-preserving spread of $p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ , then convex ordering gives

$$
\mathbb {E} _ {Y \sim q (\cdot | x)} [ h (x, Y) ] \geq \mathbb {E} _ {Y \sim p _ {0} (\cdot | x, \mathcal {D} _ {\mathrm{tr}})} [ h (x, Y) ],
$$

with strict inequality for a nontrivial spread when the tilt is strictly convex and the expectations are finite; the left-hand side may also be infinite. The moment condition (29) can therefore fail under dispersion or tail inflation, so the source-null e-process need not retain false-confirmation control under that misspecified target, regardless of whether the misspecification belongs to the same structural family as the proposed correction.

## 4.6.1 Variance Correction under an Arbitrary Target

Let

$$
m _ {2} (x) = \mathbb {E} _ {q} [ \{Y - \mu_ {0} (x) \} ^ {2} | X = x ]
$$

be the target conditional second moment about the source mean. For the variance correction in (42),

$$
\Gamma_ {c} (x) = - \frac {1}{2} \log c + \frac {1}{2} \left(1 - \frac {1}{c}\right) \frac {m _ {2} (x)}{\sigma_ {0} ^ {2} (x)}, \qquad \Gamma_ {c} (x) > 0 \iff \left\{ \begin{array}{l l} \frac {m _ {2} (x)}{\sigma_ {0} ^ {2} (x)} > \frac {c \log c}{c - 1}, & c > 1, \\ \frac {m _ {2} (x)}{\sigma_ {0} ^ {2} (x)} <   \frac {c \log c}{c - 1}, & 0 <   c <   1. \end{array} \right.
$$

(51)

For $c > 1$ , any mechanism that increases the second moment about the source mean beyond the threshold produces positive drift. In particular, a pure conditional mean shift $\mu _ { q } ( x ) = \mu _ { 0 } ( x ) + \delta ^ { * } g ( x )$ with unchanged target conditional variance gives

$$
m _ {2} (x) = \sigma_ {0} ^ {2} (x) + \delta^ {* 2} g ^ {2} (x),
$$

so the variance-inflation process has positive drift whenever

$$
\frac {\delta^ {* 2} g ^ {2} (x)}{\sigma_ {0} ^ {2} (x)} > \frac {c \log c}{c - 1} - 1.\tag{52}
$$

For $c = 1 . 8$ , the right-hand side is approximately 0.3225. Thus a variance-process crossing can be driven by a mean shift even when the conditional variance has not changed.

Conversely, a heavier-tailed target with the same second moment as the source leaves the long-run drift negative for $c > 1$ , but this does not restore an anytime-valid crossing bound. Rare large residuals may still produce an early boundary crossing when the moment condition of Proposition 3 fails. A variance-process crossing should therefore be interpreted as evidence for the variance-corrected predictive, not as identification of variance inflation; whether deployment is scientifically appropriate may require checking plausible mean-shift and tail-change explanations.

## 4.6.2 Mean Correction under an Arbitrary Target

For the mean correction in (40), let $\mu _ { q } ( x ) = \mathbb { E } _ { q } [ Y \mid X = x ]$ . Then

$$
\Gamma_ {\delta} (x) = \frac {\delta g (x) \{\mu_ {q} (x) - \mu_ {0} (x) \}}{\sigma_ {0} ^ {2} (x)} - \frac {\delta^ {2} g ^ {2} (x)}{2 \sigma_ {0} ^ {2} (x)}.\tag{53}
$$

The drift depends on q only through its conditional mean. Hence a mean-preserving target change gives nonpositive drift and gives strictly negative drift whenever $\delta g ( x ) \neq 0$ . This drift calculation does not imply anytime-valid protection against all mean-preserving changes. As formalized in Remark 2, the one-step factor is an exponential of a linear residual and is therefore convex; a mean-preserving spread can make its conditional mean exceed one even though its expected log is negative. Dispersion or tail changes can consequently inflate the maximal crossing probability without improving the long-run log-growth rate.

Practical diagnostic implication. Cross-family calculations are stress tests for interpretation, not alternative confirmatory guarantees. A variance-process crossing may be generated by a mean shift, and a mean-process crossing may be made more frequent by dispersion or tail changes despite negative long-run drift. When several mechanisms are scientifically plausible, their prespecified wealth paths may be inspected diagnostically, but a formal family-level claim should use the mixture construction of Proposition 6 or an explicit error allocation. When exact normalization and mutual absolute continuity hold, the lower boundary of Section 3.5 can also refute a proposed correction relative to the source predictive.

## 5 Synthetic Experiments

The experiments use an oracle Gaussian conditional so that the e-process is isolated from estimation error and can be checked against exact analytic predictions. They verify the main interpretations of the construction: the process is anytime-valid under the conditional predictive null, its growth matches the drift calculus of Sections 3.3 and 4.6, it can be anchored at an operational tolerance boundary, adaptive input selection can accelerate evidence accumulation, and the observed failure modes under target misspecification occur only where the moment condition of Proposition 3 fails. The goal is not to benchmark distribution-shift estimation.

## 5.1 Common setup and reproducibility protocol

The source predictive is the oracle Gaussian conditional

$$
p _ {0} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) = \mathcal {N} \big (y \mid \mu_ {0} (x), \sigma^ {2} \big), \qquad \mu_ {0} (x) = \sin (1. 5 x) + 0. 3 x, \qquad \sigma = 0. 8.
$$

Table 2: Baseline synthetic experiments (T = 200, α = 0.05, 5000 replications). Confirmation rate is the fraction of replications in which log M<sub>t</sub> crosses $\log ( 1 / \alpha )$ by T. With 5000 replications, the binomial Monte Carlo standard error of any reported rate is at most 0.0071. Median stopping time is reported among confirmed replications; for null conditions this conditions on the rare false confirmations.

<table><tr><td>Experiment</td><td>Method or condition</td><td>Confirm.</td><td>Median τ</td><td>Mean log MT</td></tr><tr><td>Mean shift</td><td>correct δ = 0.45</td><td>1.000</td><td>16</td><td>34.65</td></tr><tr><td>Mean shift</td><td>underspecified δ = 0.225</td><td>1.000</td><td>23</td><td>26.01</td></tr><tr><td>Mean shift</td><td>overspecified δ = 0.9</td><td>0.818</td><td>16</td><td>-0.15</td></tr><tr><td>Mean-shift null</td><td>test δ = 0.45</td><td>0.034</td><td>15</td><td>-34.81</td></tr><tr><td>Variance shift</td><td>correct c = 1.8</td><td>0.997</td><td>26</td><td>21.22</td></tr><tr><td>Variance shift</td><td>underspecified c = 1.4</td><td>0.999</td><td>33</td><td>17.78</td></tr><tr><td>Variance shift</td><td>overspecified c = 2.4</td><td>0.972</td><td>25</td><td>17.46</td></tr><tr><td>Variance-shift null</td><td>test c = 1.8</td><td>0.027</td><td>20</td><td>-14.33</td></tr></table>

Unless otherwise stated, source inputs satisfy $X \sim \mathcal { N } ( 0 , 1 )$ . We use an oracle conditional distribution to isolate the e-process behavior from estimation error. Unless otherwise stated, all tests use $\alpha = 0 . 0 5$ horizon $T = 2 0 0$ , and 5000 Monte Carlo replications. Confirmation occurs when log $M _ { t } > \log ( 1 / \alpha )$

For a proposed conditional mean correction $p _ { \delta } ( y \mid x , \mathcal { D } _ { \mathrm { t r } } ) = \mathcal { N } \big ( y \mid \mu _ { 0 } ( x ) + \delta g ( x ) , \sigma ^ { 2 } \big )$ , we use

$$
g (x) = 1 + 0. 5 \tanh (x), \quad \log e _ {i} = \frac {\delta g (X _ {i}) \{Y _ {i} - \mu_ {0} (X _ {i}) \}}{\sigma^ {2}} - \frac {\delta^ {2} g ^ {2} (X _ {i})}{2 \sigma^ {2}}.
$$

For a proposed variance correction $p _ { c } ( y \mid x , \mathcal { D } _ { \mathrm { t r } } ) = \mathcal { N } \big ( y \mid \mu _ { 0 } ( x ) , c \sigma ^ { 2 } \big )$ , we use

$$
\log e _ {i} = - \frac {1}{2} \log c + \frac {1}{2} \left(1 - \frac {1}{c}\right) \frac {\{Y _ {i} - \mu_ {0} (X _ {i}) \} ^ {2}}{\sigma^ {2}}.
$$

Seeding protocol. A root SeedSequence(20260707) is spawned into one child per experiment family; within each family, a single input matrix and a single standardized-residual matrix are drawn once and shared across all conditions of that family (residuals are rescaled per condition). Two conditions that are mathematically identical—for instance, the variance-correction null and the $c _ { \mathrm { m i s } } = 1$ row of the miscalibration sweep—therefore produce identical numbers by construction, rather than approximately equal numbers from independent streams.

Analytic cross-checks. Under this setup $\mathbb { E } [ g ^ { 2 } ( X ) ] \approx 1 . 0 9 8 6$ for $X \sim \mathcal { N } ( 0 , 1 )$ . Every mean final log-wealth in Tables 2, 4 and 6 agrees with the corresponding fixed-correction analytic drift prediction Γ · T from Sections 3.3 and 4.6 to within Monte Carlo error; for example, the correctly specified mean correction has $\overline { { \Gamma } } = \delta ^ { 2 } \mathbb { E } [ g ^ { 2 } ] / ( 2 \sigma ^ { 2 } ) = 0 . 1 7 3 8$ and observed mean log $M _ { T } = 3 4 . 6 5 \approx 0 . 1 7 3 8 \times 2 0 0$ , and the correctly specified variance correction has $\overline { { \Gamma } } = 0 . 1 0 6 1$ and observed $2 1 . 2 2 = 0 . 1 0 6 1 \times 2 0 0$ . The rows of Table 5 require separate checks because the mixture, predictable plug-in, and adaptive-design strategies do not share one fixed drift. For the five-component uniform mixture under the power condition, the leading finite-mixture approximation log $M _ { T } ^ { \mathrm { m i x } } \approx \log ( 1 / 5 ) + \operatorname* { m a x } _ { \theta } \overline { { \Gamma } } _ { \theta } T$ gives 33.15 nats, within 0.01 nats of the observed 33.14.

## 5.2 Label-shift sanity check

For Gaussian $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ , the label tilt $h ( y ) = \exp ( \beta y )$ is exactly equivalent to a global mean correction with $g \equiv 1$ and $\delta = \beta \sigma ^ { 2 }$ (Section A.16). With $\beta = 0 . 5 5$ (so $\delta = 0 . 3 5 2 )$ , the maximum absolute diference between the cumulative label-tilt log-wealth paths and the corresponding mean-correction log-wealth paths, over 1000 paths of length 200, is below $2 \times 1 0 ^ { - 1 4 }$ . This check uses 1000 rather than the 5000 paths of the other experiments because the comparison is a deterministic algebraic identity rather than a Monte Carlo estimate: the two implementations agree pathwise, so the number of paths afects only the number of opportunities to detect a coding discrepancy, not the precision of an estimate. Thus the general predictive-correction implementation recovers the label-shift construction in this special case, up to floating-point accumulation.

![](images/829a41f863f5e6dbe994b65146dace445de5441209a73c5777ce031ea1dbc1b3.jpg)

![](images/27b39fa0e2454d9f52db0f84e2efbbb20bdf8eaf72ecfc6a37903ea0f3f471dd.jpg)  
Figure 2: Log-wealth trajectories (median and interquartile band over 5000 replications; dashed line at $\log ( 1 / \alpha ) )$ . (a) Within-family behavior: correctly specified mean and variance corrections grow linearly at the predicted drifts, while the null process drifts down. (b) Cross-family false confirmation: a pure mean shift drives the variance-correction e-process upward at the drift predicted by (51); a mean-preserving variance inflation drives the mean-correction e-process down in median, yet individual paths can cross because the supermartingale condition fails; and under a heavy-tailed target (gray sample paths, t with matched variance) crossings occur by single-observation jumps despite negative drift.

## 5.3 Conditional mean shift

We generate

$$
Y \mid X = x \sim \mathcal {N} \big (\mu_ {0} (x) + 0. 4 5 g (x), \sigma^ {2} \big).
$$

The correctly specified mean correction confirms in all replications with median stopping time 16 (Fig. 2a). An underspecified correction $\delta = 0 . 2 2 5$ remains powerful but slower, confirming in all replications with median stopping time 23. An overspecified correction $\delta = 0 . 9$ has exactly zero log-drift under this target—by (53), $\Gamma _ { \delta } \propto \delta ^ { * } \delta - \delta ^ { 2 } / 2$ vanishes at $\delta = 2 \delta ^ { * } -$ and correspondingly confirms in probability 0.818 with mean final log wealth −0.15. This illustrates the sensitivity of direct confirmation to correction magnitude. Under the predictive null $( \delta ^ { * } = 0 )$ , the same $\delta = 0 . 4 5$ e-process confirms in probability 0.034.

Checking the finite-horizon bound. This condition also calibrates Corollary 2. For the correctly specified correction the increments log $e _ { i }$ are i.i.d. with $\overline { { \Gamma } } = \delta ^ { 2 } \mathbb { E } [ g ^ { 2 } ] / ( 2 \sigma ^ { 2 } ) = 0 . 1 7 3 8$ and, since log $e _ { i } =$ $\bar { \delta ^ { 2 } } g ^ { 2 } ( X _ { i } ) / ( 2 \sigma ^ { 2 } ) + \delta g ( X _ { i } ) \varepsilon _ { i } / \sigma$ with $\varepsilon _ { i } \sim \mathcal { N } ( 0 , 1 )$ independent of $X _ { i } ,$

$$
\operatorname{Var} \left(\log e _ {i}\right) = \left\{\frac {\delta^ {2}}{2 \sigma^ {2}} \right\} ^ {2} \operatorname{Var} \left\{g ^ {2} (X) \right\} + \frac {\delta^ {2}}{\sigma^ {2}} \mathbb {E} \left[ g ^ {2} (X) \right] = 0. 3 5 7 6,
$$

using $\mathbb { E } [ g ^ { 2 } ] = 1 . 0 9 8 6$ and $\mathbb { E } [ g ^ { 4 } ] = 1 . 6 0 7 3$ . With $b = \log 2 0 = 2 . 9 9 6$ , the variance-only bound (24) gives $\mathbb { P } ( \tau ^ { * } > t ) \le 0 . 6 8 6 , 0 . 3 5 6$ , and 0.066 at $t = 3 0$ , 50, and 200. These are valid but very loose against an observed median stopping time of 16 and a confirmation rate of 1.000 by $t = 2 0 0$ , which is the expected behavior of a variance-only bound whose decay is only of order $\mathrm { V a r } ( \log e _ { i } ) / \{ t \overline { { \Gamma } } ^ { 2 } \}$ . A certified sub-Gaussian proxy is also available. Since $g ( x ) \in ( 0 . 5 , 1 . 5 ) \subseteq [ 0 . 5 , 1 . 5 ]$ , Hoefding’s lemma controls the bounded $g ^ { 2 } ( X _ { i } )$ term. The Gaussian term is conditionally sub-Gaussian with a variance proxy bounded uniformly in $X _ { i }$

Consequently, if $A _ { i }$ denotes the centered bounded term and $B _ { i }$ the centered Gaussian term, then the tower property gives

$$
\mathbb {E} \exp \{\lambda (A _ {i} + B _ {i}) \} = \mathbb {E} \big [ e ^ {\lambda A _ {i}} \mathbb {E} \big (e ^ {\lambda B _ {i}} \mid X _ {i} \big) \big ] \leq \exp \left(\frac {\lambda^ {2} s _ {B} ^ {2}}{2}\right) \mathbb {E} e ^ {\lambda A _ {i}} \leq \exp \left(\frac {\lambda^ {2} (s _ {A} ^ {2} + s _ {B} ^ {2})}{2}\right).
$$

Thus the two proxies add in this particular dependent decomposition, yielding

$$
s ^ {2} = \frac {1}{4} \left\{\frac {\delta^ {2}}{2 \sigma^ {2}} (1. 5 ^ {2} - 0. 5 ^ {2}) \right\} ^ {2} + \frac {\delta^ {2}}{\sigma^ {2}} (1. 5) ^ {2} = 0. 7 3 6 9.
$$

Substitution into (25) gives the bounds 0.895, 0.644, and 0.033 at $t = 3 0 , 5 0$ , and 200. The certified proxy is deliberately conservative and is therefore looser than Cantelli’s bound at the two shorter horizons, but its exponential decay becomes sharper by $t = 2 0 0$

## 5.4 Beyond-tolerance confirmation

In practice the actionable question may not be whether any shift is present. A deployment policy may tolerate shifts up to a boundary $\delta _ { \mathrm { t o l } }$ and ask for anytime-valid evidence only when the correction appears to exceed that tolerance. In the one-sided Gaussian mean-shift family below, the correct likelihood ratio is not the actionable correction against the unshifted source, since that would also react to acceptable changes. Instead, for an actionable level $\delta _ { \mathrm { a l a r m } } > \delta _ { \mathrm { t o l } }$ , we compare the actionable predictive to the tolerated-boundary predictive:

$$
e _ {i} ^ {\mathrm{tol}} = \frac {p _ {\delta_ {\mathrm{alarm}}} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})}{p _ {\delta_ {\mathrm{tol}}} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})}.
$$

For the Gaussian mean-correction family this gives

$$
\log e _ {i} ^ {\mathrm{tol}} = \frac {(\delta_ {\mathrm{alarm}} - \delta_ {\mathrm{tol}}) g (X _ {i}) \{Y _ {i} - \mu_ {0} (X _ {i}) \}}{\sigma^ {2}} - \frac {(\delta_ {\mathrm{alarm}} ^ {2} - \delta_ {\mathrm{tol}} ^ {2}) g ^ {2} (X _ {i})}{2 \sigma^ {2}}.
$$

This family is the exponential-family tilt of Proposition 7 with the standardized-residual feature $\phi ( x , y ) =$ $g ( x ) \{ y - \mu _ { 0 } ( x ) \} / \sigma ^ { 2 }$ of Section 4.3 and $\eta = \delta$ , so that $\eta _ { \mathrm { t o l } } = \delta _ { \mathrm { t o l } }$ and $\eta _ { \mathrm { a l a r m } } = \delta _ { \mathrm { a l a r m } }$ with no rescaling. Within the Gaussian mean-shift family with unchanged conditional variance $\sigma ^ { 2 }$ , the level is controlled over the whole tolerated parameter set and not merely at its boundary. Here the moment can be written in closed form: under a Gaussian target with true mean-shift parameter $\delta ^ { * }$ and conditional variance $\sigma ^ { 2 }$

$$
\mathbb {E} _ {\delta^ {*}} \left[ e _ {i} ^ {\mathrm{tol}} \mid X _ {i} = x, \mathcal {F} _ {i - 1} \right] = \exp \left\{\frac {g ^ {2} (x) (\delta_ {\mathrm{alarm}} - \delta_ {\mathrm{tol}}) (\delta^ {*} - \delta_ {\mathrm{tol}})}{\sigma^ {2}} \right\},\tag{54}
$$

which is at most one for every x exactly when $\delta ^ { * } \leq \delta _ { \mathrm { t o l } }$ (here $g ( x ) > 0$ for every x). Therefore, within this Gaussian family, $\Pi _ { i } e _ { i } ^ { \mathrm { t o l } }$ is a valid e-process uniformly over the composite tolerated parameter regime $\{ \delta ^ { * } \le \delta _ { \mathrm { t o l } } \}$ . The composite null is composite in the mean-shift parameter only; the guarantee does not automatically extend to target distributions outside this family, such as targets with an additional variance or tail change. The test is intentionally not a sharp detector of every $\delta ^ { * } > \delta _ { \mathrm { t o l } } :$ because $\psi _ { x }$ is quadratic here, Remark 1 places the drift sign change exactly at the midpoint $( \delta _ { \mathrm { t o l } } + \delta _ { \mathrm { a l a r m } } ) / 2$ , giving a practical indiference region between acceptable and clearly actionable shifts.

We set $\delta _ { \mathrm { t o l } } = 0 . 2 5$ and $\delta _ { \mathrm { a l a r m } } = 0 . 5 5$ , with the same source predictive, $T = 2 0 0 , \alpha = 0 . 0 5$ , and 5000 replications as above. Table 3 shows that confirmation remains below α at and below the tolerance boundary, while becoming frequent once the true correction is clearly beyond tolerance.

This experiment gives the direct predictive-correction framework a policy interpretation. The practitioner can prespecify a tolerance boundary, choose an actionable alternative beyond it, and obtain an anytimevalid alarm for evidence favoring the actionable correction over the tolerated one. The price is the usual likelihood-ratio geometry: there is an indiference region between the two design points, and larger separation between $\delta _ { \mathrm { t o l } }$ and $\delta _ { \mathrm { a l a r m } }$ gives a more conservative alarm near the boundary.

Table 3: Beyond-tolerance confirmation for the direct model-based e-process. The tested likelihood ratio is $p _ { \delta _ { \mathrm { a l a r m } } } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } ) / p _ { \delta _ { \mathrm { t o l } } } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ with $\delta _ { \mathrm { t o l } } = 0 . 2 5$ and $\delta _ { \mathrm { a l a r m } } = 0 . 5 5$ . Median stopping time is reported among confirmed paths and is unstable when confirmation is extremely rare.

<table><tr><td>True δ*</td><td>Confirmation</td><td>Median τ</td><td>Mean log MT</td></tr><tr><td>0.00</td><td>&lt; 0.001</td><td>12</td><td>-41.02</td></tr><tr><td>0.15</td><td>0.004</td><td>17.5</td><td>-25.87</td></tr><tr><td>0.25</td><td>0.039</td><td>32</td><td>-15.42</td></tr><tr><td>0.35</td><td>0.271</td><td>52</td><td>-5.25</td></tr><tr><td>0.45</td><td>0.830</td><td>54</td><td>5.23</td></tr><tr><td>0.55</td><td>0.996</td><td>33</td><td>15.41</td></tr><tr><td>0.70</td><td>1.000</td><td>19</td><td>30.96</td></tr></table>

Table 4: Miscalibration sweep: data generated with variance $c _ { \mathrm { m i s } } \sigma ^ { 2 } .$ , e-process computed with model variance $\sigma ^ { 2 }$ and correction $c = 1 . 8 ,$ . All rows share the same standardized residual draws.

<table><tr><td> $c_{\text{mis}}$ </td><td>1.0</td><td>1.25</td><td>1.5</td><td>1.8</td><td>2.2</td></tr><tr><td>Confirmation rate</td><td>0.027</td><td>0.376</td><td>0.892</td><td>0.997</td><td>1.000</td></tr><tr><td>Mean  $\log M_T$ </td><td>-14.33</td><td>-3.22</td><td>7.89</td><td>21.22</td><td>39.00</td></tr></table>

## 5.5 Conditional variance shift and source miscalibration

We generate

$$
Y \mid X = x \sim \mathcal {N} \big (\mu_ {0} (x), c _ {\mathrm{mis}} \sigma^ {2} \big),
$$

and run the variance-correction e-process with model variance $\sigma ^ { 2 }$ . The correctly specified correction $( c = c _ { \mathrm { m i s } } = 1 . 8 )$ confirms in probability 0.997 with median stopping time 26. Magnitude-misspecified corrections $c = 1 . 4$ and $c = 2 . 4$ also confirm frequently (0.999 and 0.972) but with smaller average final log wealth (17.78 and 17.46 versus 21.22), matching the drifts 0.0889 and 0.0873 from (51). Under the predictive null $( c _ { \mathrm { m i s } } = 1 )$ , the $c = 1 . 8$ correction confirms in probability 0.027.

The same construction doubles as a stress test for source predictive miscalibration: if the deployment distribution equals the data-level source but the fitted predictive variance is too small by the factor $c _ { \mathrm { m i s } }$ , the model-based predictive null is false, and the $c = 1 . 8$ e-process confirms at the rates in Table 4. Because all rows share the same standardized residuals, the $c _ { \mathrm { m i s } } = 1$ row is the variance-null row and the $c _ { \mathrm { m i s } } = 1 . 8$ row is the correctly specified row of Table 2. This does not contradict Theorem 1, since the model-based predictive null is false when $c _ { \mathrm { m i s } } \neq 1$ . It highlights the operational limitation of direct predictive-correction confirmation and motivates reference-calibrated variants.

## 5.6 Mixtures over correction magnitude

For the true mean shift $\delta ^ { * } = 0 . 4 5$ , we form a uniform mixture over

$$
\{- 0. 4 5, 0. 2 2 5, 0. 4 5, 0. 6 7 5, 0. 9 \}.
$$

The mixture confirms in all replications with median stopping time 19: slower than the oracle single correction (median 16) but robust to uncertainty about the correction magnitude. Under the predictive null, the same mixture confirms in probability 0.031, verifying that the mixture e-process retains Type I control.

Table 5: Robustness and adaptivity experiments (T = 200, 5000 replications). Power rows use the true mean shift $\delta ^ { * } = 0 . 4 5 ;$ Type I rows use the predictive null. The binomial Monte Carlo standard error of each reported confirmation rate is at most 0.0071.

<table><tr><td>Strategy</td><td>Condition</td><td>Confirm.</td><td>Median  $\tau$ </td><td>Mean  $\log M_T$ </td></tr><tr><td>Mixture over  $\delta$ </td><td>power</td><td>1.000</td><td>19</td><td>33.14</td></tr><tr><td>Mixture over  $\delta$ </td><td>Type I</td><td>0.031</td><td>18</td><td>-10.23</td></tr><tr><td>Predictable plug-in  $\hat{\delta}_i$ </td><td>power</td><td>1.000</td><td>25</td><td>32.03</td></tr><tr><td>Predictable plug-in  $\hat{\delta}_i$ </td><td>Type I</td><td>0.025</td><td>16.5</td><td>-2.38</td></tr><tr><td>Adaptive input selection</td><td>power</td><td>0.998</td><td>14</td><td>52.19</td></tr><tr><td>Adaptive input selection</td><td>Type I</td><td>0.031</td><td>14</td><td>-17.99</td></tr></table>

## 5.7 Predictable plug-in corrections

To exercise Proposition 5, we replace the fixed δ by a predictable ridge estimate

$$
\hat {\delta} _ {i} = \mathrm{clip} \left(\frac {\sum_ {j <   i} g (X _ {j}) \{Y _ {j} - \mu_ {0} (X _ {j}) \} / \sigma^ {2}}{1 + \sum_ {j <   i} g ^ {2} (X _ {j}) / \sigma^ {2}}, [ - 1. 5, 1. 5 ]\right),
$$

computed from strictly past data, and bet with log $e _ { i }$ evaluated at $\hat { \delta } _ { i }$ . Under the true shift $\delta ^ { * } = 0 . 4 5$ the plug-in strategy confirms in all replications with median stopping time 25 and mean final log wealth 32.03—slower than the oracle (16, 34.65) and comparable to the mixture (19, 33.14), the price of learning the magnitude inside the wealth process. Under the null it confirms in probability 0.025, confirming validity. As Proposition 5 notes, what is confirmed here is that an adaptive betting strategy found evidence against the source predictive null, not a single prespecified correction.

## 5.8 Adaptive input selection

The conditional drift $\Gamma _ { h } ( x )$ of Proposition 2 depends on the input, so an experimenter who controls the inputs can accelerate confirmation. We implement an ε-greedy bandit $( \varepsilon = 0 . 2 )$ over the input arms $\{ - 2 , 0 , 2 \}$ , with realized log $e _ { i }$ as the reward, so the design depends on past outcomes and is genuinely adaptive. Under the true shift $\delta ^ { * } = 0 . 4 5$ , the correctly specified per-arm drifts are $D _ { \mathrm { K L } } ( x ) =$ $\delta ^ { 2 } g ^ { 2 } ( x ) / ( 2 \sigma ^ { 2 } ) \in \{ 0 . 0 4 2 , 0 . 1 5 8 , 0 . 3 4 7 \}$ ; the bandit concentrates on $x = 2$ and achieves mean final log wealth 52.19 versus 34.65 under i.i.d. $\mathcal { N } ( 0 , 1 )$ inputs (median stopping time 14 versus $1 6 ;$ the modest median gain reflects initialization and exploration overhead, while the 1.5× drift gain compounds over the horizon). Under the null the same adaptive design confirms in probability 0.031: validity is unafected by outcome-dependent input selection, exactly as Theorem 1 asserts.

## 5.9 Cross-family false confirmation

This experiment quantifies the limits established in Sections 3.4 and 4.6: when the target predictive difers from the source, the moment condition (29) is what preserves the same supermartingale proof, and both failure mechanisms of Section 3.4.2 can occur at practically alarming rates when that condition breaks. Results are in Table 6 and Fig. 2b.

Positive drift under the wrong family. A pure conditional mean shift with unchanged conditional variance inflates the second moment about $\mu _ { 0 } .$ . Because $\Gamma _ { c } ( x )$ in (51) is afine in $m _ { 2 } ( x )$ , averaging the pointwise condition (52) over the input distribution gives positive average drift once $\delta ^ { * 2 } \mathbb { E } [ g ^ { 2 } ] / \sigma ^ { 2 } > 0 . \bar { 3 } 2 2 5$ . At $\delta ^ { * } = 0 . 4 5$ the margin is thin $( \overline { { \Gamma } } = + 0 . 0 0 6 )$ , yet the confirmation rate is already 0.619; at $\delta ^ { * } = 0 . 6$ $( \overline { { \Gamma } } = + 0 . 0 6 6 )$ it is 0.972. A practitioner who proposed a noise-inflation correction would confirm it with near certainty when the actual change is a response shift with no dispersion change at all.

Table 6: Cross-family confirmation $( T = 2 0 0$ , 5000 replications). Γ is the analytic per-step drift from (51) or (53). No target in this table satisfies the moment condition (29) for the tested correction: in the first, second, and fourth rows the relevant tilt moment is finite but strictly larger than the normalizer, while in the third and fifth rows (the two $t _ { 5 }$ targets) it is $+ \infty$ . In all rows the predictive null is false, so the source-null guarantee of Theorem 1 does not apply. The binomial Monte Carlo standard error of each reported confirmation rate is at most 0.0071

<table><tr><td>Target distribution</td><td>Tested correction</td><td> $\overline{\Gamma}$ </td><td>Confirm.</td><td>Median  $\tau$ </td><td>Mean  $\log M_{T}$ </td></tr><tr><td>Mean shift  $\delta^{*}=0.45$ </td><td>variance  $c=1.8$ </td><td>+0.006</td><td>0.619</td><td>55</td><td>1.16</td></tr><tr><td>Mean shift  $\delta^{*}=0.6$ </td><td>variance  $c=1.8$ </td><td>+0.066</td><td>0.972</td><td>36</td><td>13.16</td></tr><tr><td> $t_{5}$ , matched variance</td><td>variance  $c=1.8$ </td><td>-0.072</td><td>0.191</td><td>30</td><td>-14.24</td></tr><tr><td>Variance inflation 1.8</td><td>mean  $\delta=0.45$ </td><td>-0.174</td><td>0.141</td><td>13</td><td>-35.01</td></tr><tr><td> $t_{5}$ , matched variance</td><td>mean  $\delta=0.45$ </td><td>-0.174</td><td>0.037</td><td>13.5</td><td>-34.80</td></tr></table>

Negative drift does not protect. Under a mean-preserving variance inflation $( c _ { \mathrm { m i s } } = 1 . 8$ , mean unchanged), the mean-correction e-process has strongly negative drift $( \overline { { \Gamma } } = - 0 . 1 7 4 ;$ mean final log wealth $- 3 5 . 0 1 )$ , yet it confirms in probability 0.141, nearly three times the nominal level. The mechanism is Proposition 3: the mean tilt is convex in y, so conditionally on the input $\mathbb { E } _ { q } [ e _ { i } \mid X _ { i } = x ] = \exp \{ ( c _ { \mathrm { m i s } } -$ $1 ) \delta ^ { 2 } g ^ { 2 } ( x ) / ( 2 \sigma ^ { 2 } ) \} > 1$ , breaking the supermartingale condition at every input. Averaging over the input distribution—taking the expectation of the exponential, not the exponential of the expectation—predicts

$$
\mathbb {E} _ {q} [ e _ {i} ] = \mathbb {E} _ {X} \left[ \exp \biggl \{\frac {(c _ {\mathrm{mis}} - 1) \delta^ {2} g ^ {2} (X)}{2 \sigma^ {2}} \biggr \} \right] = 1. 1 5 2 9,
$$

against an empirical mean of 1.154; the corresponding Jensen lower bound $\exp \{ ( c _ { \mathrm { m i s } } - 1 ) \delta ^ { 2 } \mathbb { E } [ g ^ { 2 } ] / ( 2 \sigma ^ { 2 } ) \} =$ 1.1492 is not the right prediction and understates the violation. Under the heavy-tailed $t _ { 5 }$ target with matched variance, the variance-correction e-process likewise has negative drift (−0.072) but confirms in probability 0.191; here the mechanism is jumps rather than variance: 72% of the crossings are produced by a single observation whose quadratic log e-value exceeds the entire threshold (median crossing increment 4.9 nats against a threshold of 3.0). The only row resembling nominal behavior is the mean correction under the $t _ { 5 }$ target (0.037), and even that is not guaranteed by the present argument: the linear tilt has no moment generating function under a t distribution, so $\mathbb { E } _ { q } [ h ( x , Y ) ] = + \infty$ , (29) fails as badly as it can, and the rate merely happens to be small at this horizon. This example emphasizes that failure of the conditional e-value moment condition can be severe even when the observed finite-horizon crossing rate happens to be small.

Interpretation. Confirmation is Neyman–Pearson evidence for $p _ { h } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } )$ against $p _ { 0 } ( \cdot \mid \cdot , \mathcal { D } _ { \mathrm { t r } } ) ;$ it identifies neither the shift family nor the physical mechanism generating the evidence. Where several prespecified mechanisms are scientifically plausible, the corresponding wealth paths can be inspected diagnostically, but a family-level confirmatory decision should use the panel mixture of Proposition 6 or an explicit error allocation. The refutation boundary of Section 3.5 can additionally retire a wrongly proposed predictive correction when the source predictive accumulates suficient relative evidence against it.

## 5.10 Time-uniform Type I and overshoot accounting

Finally, we verify that the sub-α null confirmation rate is an overshoot efect, not a truncation efect. Running the $\delta = 0 . 4 5$ mean-correction e-process under the null for 5000 replications to horizon $T = 5 0 0 0$ (an independent replication of the null condition), the cumulative confirmation rate is 0.0366 at $t = 2 0 0$ and identical at t = 1000 and $t = 5 0 0 0$ : with null drift −0.174 per step, every crossing observed in this simulation occurs within the first few dozen observations, so the realized rate is not an artifact of stopping at $T = 2 0 0$

The equality (35) applies here, since under $q = p _ { h } ( \cdot , \cdot , { \mathcal { D } } _ { \mathrm { t r } } )$ the drift is $D _ { \mathrm { K L } } = \delta ^ { 2 } \mathbb { E } [ g ^ { 2 } ] / ( 2 \sigma ^ { 2 } ) = 0 . 1 7 3 8 > 0$ and hence log $M _ { t }  + \infty \ P _ { h }$ -almost surely. The mean wealth at crossing is $\mathbb { E } [ M _ { \tau ^ { * } } \ | \ \mathrm { c r o s s } ] = 2 7 . 7$ , so the identity predicts $1 / 2 7 . 7 = 0 . 0 3 6 1$ , equivalently a product

$$
\mathbb {P} (\text { cross }) \cdot \mathbb {E} [ M _ {\tau^ {*}} \mid \text { cross } ] = 0. 0 3 6 6 \times 2 7. 7 = 1. 0 1 4,
$$

against the theoretical value 1. There are 183 crossing paths, and the binding uncertainty is the heavytailed conditional mean $\mathbb { E } [ M _ { \tau ^ { * } } \ ]$ cross]. A separate 5000-path null check (seed 12345, horizon $T = 2 0 0 )$ gives a Monte Carlo standard error of 0.95 for this conditional mean and 0.083 for the directly checked product $M _ { \tau ^ { * } } \mathbf { 1 } \{ \tau ^ { * } < \infty \}$ . Thus the residual 1.4% is well within Monte Carlo error; we do not claim agreement to a fixed number of digits. For reference, the independent $T = 2 0 0$ replication of Table 2 gives 0.0342 for the same condition, so the run-to-run spread in the rate itself is of the same order as the discrepancy above. The gap between the nominal $\alpha = 0 . 0 5$ and the realized $\approx 0 . 0 3 6$ is therefore accounted for by the discrete overshoot $M _ { \tau ^ { * } } > 1 / \alpha$ in this experiment, and would shrink only if the per-step evidence increments were made smaller.

## 6 Discussion and Conclusion

We developed an anytime-valid framework for evaluating a prespecified predictive correction from sequentially observed target outcomes. Conditional on the realized training data, a nonnegative tilt transforms the source predictive distribution into a corrected predictive distribution, and the resulting corrected-to-source predictive ratio yields a conditional e-value. Its running product forms a nonnegative martingale under the source predictive null, so the correction can be monitored continuously and evaluated at data-dependent stopping times without inflating the probability of false confirmation. The logarithm of this wealth process is the cumulative predictive log-score advantage of the corrected predictive over the source predictive. A boundary crossing therefore provides anytime-valid relative confirmation: it supports replacing the source predictive by the proposed correction, but does not imply that the corrected predictive is the true target predictive or that the mechanism encoded by the correction uniquely explains the observed shift.

The drift analysis clarifies when such evidence should accumulate. For a target conditional distribution q,

$$
\Gamma_ {h} (x) = D _ {\mathrm{KL}} (q (\cdot \mid x) \| p _ {0} (\cdot \mid x, \mathcal {D} _ {\mathrm{tr}})) - D _ {\mathrm{KL}} (q (\cdot \mid x) \| p _ {h} (\cdot \mid x, \mathcal {D} _ {\mathrm{tr}}))
$$

whenever the relevant divergences are finite. Thus, positive drift means that the corrected predictive is closer to the target than the source predictive in conditional Kullback–Leibler divergence. Exact specification is suficient but not necessary. Under stable sampling, the average drift gives the asymptotic evidence gained per observation, while the finite-horizon bounds translate this growth rate into explicit control of delayed confirmation. Validity can also persist beyond the source predictive null: targets satisfying

$$
\mathbb {E} _ {Y \sim q _ {i} (\cdot | X _ {i})} [ h (X _ {i}, Y) ] \leq Z _ {h} (X _ {i}, \mathcal {D} _ {\mathrm{tr}})
$$

keep the evidence process supermartingale-like and therefore preserve the same time-uniform falseconfirmation bound. This protected region is a robustness property of the directional betting strategy, not an enlargement of the scientific null. Conversely, negative long-run drift alone does not imply time-uniform protection, since early variability or rare large jumps may still produce a boundary crossing.

The same construction accommodates a range of structured predictive corrections. Label tilts represent label-shift corrections, Gaussian linear and quadratic tilts yield conditional mean and variance corrections, subgroup interactions permit localized changes, and exponential-family tilts provide a general representation for prespecified feature directions. Mixtures allow uncertainty over a collection of corrections to be incorporated without choosing one component before monitoring, whereas predictable tilts allow the betting strategy to adapt to past observations and the current input. Beyond-tolerance comparisons address a diferent operational question by testing whether the shift is large enough to favor an actionable correction over an entire tolerated region rather than merely detecting any departure from the source predictive.

Exact normalization provides additional structure. When the source and corrected predictives are mutually absolutely continuous, the reciprocal likelihood ratio yields an anytime-valid lower boundary for refuting the corrected predictive in favor of the source predictive. The two boundaries correspond to distinct rejection guarantees under diferent predictive nulls; neither establishes that one of the two predictives is the true target distribution. The overshoot identity explains why the realized source-null crossing probability can be strictly below the nominal level. A certified upper bound on the normalizer still preserves conservative upper-bound validity, but generally sacrifices the exact log-score interpretation and the reciprocal refutation guarantee.

The synthetic experiments support these theoretical conclusions in controlled settings. Correctly specified mean and variance corrections accumulate evidence at their predicted rates, moderate mismatch can slow evidence growth without eliminating it, and severe mismatch can reverse the drift. Adaptive input selection can accelerate evidence accumulation without compromising source-null validity, while cross family experiments illustrate the principal interpretive limitation: a correction-specific evidence process can respond to changes generated by a diferent mechanism. The evidence therefore concerns predictive advantage relative to the source reference rather than unique mechanistic identification.

Several limitations remain. The guarantees are conditional on the fitted source predictive and therefore do not automatically account for source-model misspecification or uncertainty introduced during model fitting. The reciprocal refutation guarantee developed here is calibrated under the corrected predictive null, and we do not characterize a broader misspecification class for the lower boundary. The correction, mixture weights, tolerance boundary, and monitoring rule must be prespecified or chosen predictably under the stated filtration, and useful evidence accumulation requires inputs that are informative for distinguishing the source and corrected predictives. Pure covariate shift is outside the present conditional-outcome framework and requires separate monitoring of the input distribution.

Natural extensions include reference-calibrated or conformal layers that protect against source-predictive misspecification, experimental-design procedures that select informative inputs while preserving anytime validity, family-level methods for principled post-confirmation selection among competing corrections, and evaluation with fitted predictive models and application-driven corrections on real-world data. Overall, the framework provides a direct path from a scientifically motivated predictive correction to continuously monitored, finite-sample-valid relative evidence.

## References

Alexandari, A. M., Kundaje, A., and Shrikumar, A. (2020). Maximum likelihood with bias-corrected calibration is hard-to-beat at label shift adaptation. In Proceedings of the International Conference on Machine Learning (ICML).

Angelopoulos, A. N. and Bates, S. (2023). Conformal prediction: A gentle introduction. Foundations and Trends<sup>®</sup> in Machine Learning, 16(4):494–591.

Choi, S. (2026a). Anytime-valid confirmation of covariate balance for prespecified corrections. Preprint arXiv:2607.23157.

Choi, S. (2026b). Anytime-valid confirmation of label-shift corrections. In ICML 2026 Workshop on Hypothesis Testing.

Choi, S. (2026c). Conformal Bayes for two-sided censored Gaussian regression under label shift. Preprint arXiv:2607.02173.

Choi, S. (2026d). Conformal Bayes under label shift: Post-hoc calibration vs. in-training adaptation. In The 2nd Workshop on Epistemic Intelligence in Machine Learning.

Dawid, A. P. (1984). Present position and potential developments: Some personal views: Statistical theory: The prequential approach. Journal of the Royal Statistical Society Series A, 147(2):278–292.

Fong, E. and Holmes, C. (2021). Conformal Bayesian computation. In Advances in Neural Information Processing Systems (NeurIPS).

Garg, S., Wu, Y., Balakrishnan, S., and Lipton, Z. C. (2020). A unified view of label shift estimation. In Advances in Neural Information Processing Systems (NeurIPS).

Johnson, W. E., Li, C., and Rabinovic, A. (2007). Adjusting batch efects in microarray expression data using empirical Bayes methods. Biostatistics, 8(1):118–127.

Kelly, C. J., Karthikesalingam, A., Suleyman, M., Corrado, G., and King, D. (2019). Key challenges for delivering clinical impact with artificial intelligence. BMC Medicine, 17(1).

Kennedy, M. C. and O’Hagan, A. (2001). Bayesian calibration of computer model. Journal of the Royal Statistical Society Series B, 63(3):425–464.

Leek, J. T., Scharpf, R. B., Bravo, H. C., Simcha, D., Langmead, B., Johnson, W. E., Geman, D., Baggerly, K., and Irizarry, R. A. (2010). Tackling the widespread and critical impact of batch efects in high-throughput data. Nature Review Genetics, 11:733–739.

Lipton, Z. C., Wang, Y.-X., and Smola, A. J. (2018). Detecting and correcting for label shift with black box predictors. In Proceedings of the International Conference on Machine Learning (ICML).

Podkopaev, A. and Ramdas, A. (2021). Distribution-free uncertainty quantification for classification under label shift. In Proceedings of the Annual Conference on Uncertainty in Artificial Intelligence (UAI).

Podkopaev, A. and Ramdas, A. (2022). Tracking the risk of a deployed model and detecting harmful distribution shifts. In Proceedings of the International Conference on Learning Representations (ICLR).

Qin, S. J. (2012). Survey on data-driven industrial process monitoring and diagnosis. Annual Reviews in Control, 36(2):220–234.

Qui˜nonero-Candela, J., Sugiyama, M., Schwaighofer, A., and Lawrence, N. D., editors (2009). Dataset Shift in Machine Learning. MIT Press.

Ramdas, A., Gr¨unwald, P., Vovk, V., and Shafer, G. (2023). Game-theoretic statistics and safe anytimevalid inference. Statistical Science, 38(4):576–601.

Shafer, G. (2021). Testing by betting: A strategy for statistical and scientific communication. Journal of the Royal Statistical Society Series A, 184(2):407–431.

Shafer, G. and Vovk, V. (2019). Game-Theoretic Foundations for Probability and Finance. Wiley.

Subbaswamy, A. and Saria, S. (2020). From development to deployment: dataset shift, causality, and shift-stable models in health AI. Biostatistics, 21(2):345–352.

Sugiyama, M. and Kawanabe, M. (2012). Machine Learning in Non-Stationary Environments: Introduction to Covariate Shift Adaptation. MIT Press.

Tibshirani, R. J., Barber, R. F., Cand\`es, E. J., and Ramdas, A. (2019). Conformal prediction under covariate shift. In Advances in Neural Information Processing Systems (NeurIPS).

Ville, J. (1939). Etude Critique de la Notion de Collectif <sup>´</sup> . PhD thesis, Universit´e de Paris.

Vovk, V., Gammerman, A., and Shafer, G. (2005). Algorithmic Learning in a Random World. Springer.

Vovk, V. and Wang, R. (2021). E-values: Calibration, combination and applications. The Annals of Statistics, 49(3):1736–1754.

Wald, A. (1945). Sequential tests of statistical hypotheses. The Annals of Mathematical Statistics, 16(2):117–186.

Workman Jr., J. J. (2018). A review of calibration transfer practices and instrument diferences in spectroscopy. Applied Spectroscopy, 72(3):340–365.

## A Proofs of Main Results and Additional Derivations

## A.1 Proof of Lemma 1: Normalized Tilt as a Likelihood Ratio

For each fixed x, nonnegativity of h and (7) imply

$$
\int p _ {h} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) d y = \frac {1}{Z _ {h} (x , \mathcal {D} _ {\mathrm{tr}})} \int h (x, y) p _ {0} (y \mid x, \mathcal {D} _ {\mathrm{tr}}) d y = 1.
$$

Thus $p _ { h } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ is a probability distribution. It is absolutely continuous with respect to $p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ because its density is obtained by multiplying the source density by the nonnegative factor $h ( x , \cdot ) / Z _ { h } ( x , \mathcal { D } _ { \mathrm { t r } } )$ The Radon–Nikodym ratio is therefore $h ( x , y ) / Z _ { h } ( x , \mathcal { D } _ { \mathrm { t r } } ) \ p _ { 0 } ( \cdot \ | \ x , \mathcal { D } _ { \mathrm { t r } } )$ -a.s., and integrating this ratio under $p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ gives one.

## A.2 Proof of Proposition 1: Per-Observation Conditional E-Value

Condition on $\mathcal { G } _ { i } = \sigma ( \mathcal { F } _ { i - 1 } , X _ { i } )$ . Under $H _ { 0 } ^ { \mathrm { p r e d } }$ , the conditional distribution of $Y _ { i }$ is $p _ { 0 } ( \cdot \mid X _ { i } , \mathcal { D } _ { \mathrm { t r } } )$ , while $X _ { i }$ and $Z _ { h } ( X _ { i } , { D } _ { \mathrm { t r } } )$ are fixed. Hence

$$
\mathbb {E} [ e _ {i} \mid \mathcal {G} _ {i} ] = \frac {1}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})} \int h (X _ {i}, y) p _ {0} (y \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}) d y = 1.
$$

This is exactly the conditional e-value property.

## A.3 Proof of Theorem 1: Anytime-Valid Predictive-Correction Confirmation By Proposition 1,

$$
\mathbb {E} [ e _ {t} \mid \mathcal {F} _ {t - 1} ] = \mathbb {E} [ \mathbb {E} [ e _ {t} \mid \mathcal {G} _ {t} ] \mid \mathcal {F} _ {t - 1} ] = 1.
$$

Since $M _ { t - 1 }$ is $\mathcal { F } _ { t - 1 }$ -measurable,

$$
\mathbb {E} [ M _ {t} \mid \mathcal {F} _ {t - 1} ] = M _ {t - 1} \mathbb {E} [ e _ {t} \mid \mathcal {F} _ {t - 1} ] = M _ {t - 1}.
$$

Thus $( M _ { t } )$ is a nonnegative martingale with $M _ { 0 } = 1$ . Ville’s inequality gives

$$
\sup _ {P \in \mathcal {P} _ {0} ^ {\text { pred }}} \mathbb {P} _ {P} \left(\sup _ {t \geq 0} M _ {t} > \frac {1}{\alpha}\right) \leq \alpha ,
$$

and the stopping-time statement follows because $\{ \tau ^ { * } < \infty \} = \{ \operatorname* { s u p } _ { t } M _ { t } > 1 / \alpha \}$

## A.4 Additional Details on Safe Numerical Approximation of the Normalizer

Let $\widetilde { Z } _ { i } ( X _ { i } )$ be positive, $\mathcal { G } _ { i }$ -measurable, and satisfy $\widetilde { Z } _ { i } ( X _ { i } ) \ge Z _ { h } ( X _ { i } , { \mathcal { D } } _ { \mathrm { t r } } )$ almost surely. Then

$$
\mathbb {E} \left[ \frac {h (X _ {i} , Y _ {i})}{\widetilde {Z} _ {i} (X _ {i})} \Bigg | \mathcal {G} _ {i} \right] = \frac {Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})}{\widetilde {Z} _ {i} (X _ {i})} \leq 1,
$$

so sequential composition yields a nonnegative supermartingale. Relative to exact normalization, the log increment is reduced by

$$
\log \frac {\widetilde {Z} _ {i} (X _ {i})}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})}.
$$

For a random numerical estimate, two conditioning arguments show the problem. First, once a positive estimate $\widehat { Z } _ { i }$ is generated before $Y _ { i }$ and included in the pre-outcome information, the conditional mean of the approximate factor is $Z _ { h } ( X _ { i } , { D _ { \mathrm { t r } } } ) / \widehat { Z } _ { i }$ and exceeds one on every undershoot. Second, suppose instead that the auxiliary randomness is averaged out, is conditionally independent of $Y _ { i }$ given $\mathcal { G } _ { i } ,$ and satisfies $\mathbb { E } [ \widehat { Z } _ { i } \mid \mathcal { G } _ { i } ] = Z _ { h } ( X _ { i } , \mathcal { D } _ { \mathrm { t r } } )$ . Then

$$
\mathbb {E} \left[ \frac {h (X _ {i} , Y _ {i})}{\widehat {Z} _ {i}} \mid \mathcal {G} _ {i} \right] = Z _ {h} (X _ {i}, \mathcal {D} _ {\mathrm{tr}}) \mathbb {E} \left[ \frac {1}{\widehat {Z} _ {i}} \mid \mathcal {G} _ {i} \right] \geq 1
$$

by Jensen’s inequality, with strict inequality unless the estimate is exact almost surely. Thus unbiasedness of $\widehat { Z } _ { i }$ does not imply validity after inversion.

Finally, replacing $Z _ { h } ( X _ { i } , { D _ { \mathrm { t r } } } )$ by an upper bound changes the reciprocal factor from $Z _ { h } ( X _ { i } , D _ { \mathrm { t r } } ) / h ( X _ { i } , Y _ { i } )$ to $\widetilde { Z } _ { i } ( X _ { i } ) / h ( X _ { i } , Y _ { i } )$ . Under the strict-positivity condition imposed in Section 3.5.1, $H _ { h } ^ { \mathrm { p r e d } }$ gives the latter conditional mean $\widetilde { Z } _ { i } ( X _ { i } ) / Z _ { h } ( X _ { i } , { \mathcal { D } } _ { \mathrm { t r } } ) \geq 1$ , so it is not generally an e-value for refutation. The lower boundary in Section 3.5 therefore requires exact normalization.

## A.5 Proof of Proposition 2: Conditional Drift Decomposition

The identity $\mathbb { E } _ { q } [ \log e _ { i } \ | \ { \mathcal { G } } _ { i } ] = \Gamma _ { h } ( X _ { i } )$ follows from $Y _ { i } \mid { \mathcal { G } } _ { i } \sim q ( \cdot \mid X _ { i } )$ and the definition of $e _ { i } .$ . The hypothesis $\mathbb { E } _ { q } | \log e _ { i } | < \infty$ gives

$$
\mathbb {E} _ {q} | \Gamma_ {h} (X _ {i}) | = \mathbb {E} _ {q} \big | \mathbb {E} _ {q} [ \log e _ {i} | \mathcal {G} _ {i} ] \big | \leq \mathbb {E} _ {q} | \log e _ {i} | <   \infty
$$

by conditional Jensen. Hence log $\begin{array} { r } { M _ { t } , \sum _ { i < t } \Gamma _ { h } ( X _ { i } ) } \end{array}$ , and $N _ { t }$ are integrable. When the two $\mathrm { K L }$ terms are finite, adding and subtracting log $q ( y \mid x )$ gives

$$
\begin{array}{r l} & {\Gamma_ {h} (x) = \int q (y \mid x) \log \frac {q (y \mid x)}{p _ {0} (y \mid x , \mathcal {D} _ {\mathrm{tr}})} d y - \int q (y \mid x) \log \frac {q (y \mid x)}{p _ {h} (y \mid x , \mathcal {D} _ {\mathrm{tr}})} d y} \\ & {\qquad = D _ {\mathrm{KL}} \{q (\cdot \mid x) \| p _ {0} (\cdot \mid x, \mathcal {D} _ {\mathrm{tr}}) \} - D _ {\mathrm{KL}} \{q (\cdot \mid x) \| p _ {h} (\cdot \mid x, \mathcal {D} _ {\mathrm{tr}}) \}.} \end{array}
$$

The increments $D _ { i } = \log e _ { i } - \Gamma _ { h } ( X _ { i } )$ satisfy $\mathbb { E } _ { q } [ D _ { i } \ | \ { \mathcal { G } } _ { i } ] = 0$ and therefore also $\mathbb { E } _ { q } [ D _ { i } \ | \ F _ { i - 1 } ] = 0$ , so $\begin{array} { r } { N _ { t } = \sum _ { i \leq t } D _ { i } } \end{array}$ is a martingale under $P _ { q }$ . Under $\begin{array} { r } { \mathrm { \ i u p } _ { i } \mathbb { E } [ D _ { i } ^ { 2 } \mid \mathcal { G } _ { i } ] \leq v . } \end{array}$ 2

$$
\sum_ {i = 1} ^ {\infty} \frac {\mathbb {E} _ {q} [ D _ {i} ^ {2} ]}{i ^ {2}} \leq v \sum_ {i = 1} ^ {\infty} i ^ {- 2} <   \infty .
$$

The martingale strong law, equivalently Chow’s theorem followed by Kronecker’s lemma, yields $N _ { t } / t \to 0$ almost surely. On the event

$$
\liminf _ {t \to \infty} \frac {1}{t} \sum_ {i = 1} ^ {t} \Gamma_ {h} (X _ {i}) > 0,
$$

choose $\epsilon > 0$ smaller than half this liminf. Then $N _ { t } / t \geq - \epsilon$ eventually and the average drift is at least $2 \epsilon$ eventually, so log $M _ { t } \geq \epsilon t$ eventually. Hence log $M _ { t } \to \infty$ and $\tau ^ { * } < \infty$

## A.6 Proof of Corollary 1: Asymptotic Growth Under I.I.D. or Stationary-Ergodic Sampling

In the i.i.d. case, the sequential assumptions imply that the pairs $( X _ { i } , Y _ { i } )$ are i.i.d. with joint distribution $q ^ { X } ( d x ) q ( d y \mid x )$ . In the more general case, stationarity and ergodicity of the pair process are assumed directly. Since log $e _ { i }$ is a fixed measurable function of $( X _ { i } , Y _ { i } )$ and $\mathbb { E } _ { q ^ { X } q } | \log e _ { 1 } | < \infty$ , the ordinary strong law, respectively Birkhof’s theorem, gives

$$
\frac {1}{t} \log M _ {t} = \frac {1}{t} \sum_ {i = 1} ^ {t} \log e _ {i} \longrightarrow \mathbb {E} _ {q ^ {X} q ^ {Y | X}} [ \log e _ {1} ] = \mathbb {E} _ {q ^ {X}} [ \Gamma_ {h} (X) ] \quad \text {a.s.}
$$

## A.7 Proof of Corollary 2: Finite-Horizon Crossing Bounds

Write $\begin{array} { r } { \gamma = \overline { { \Gamma } } ( q ; h ) > 0 , S _ { t } = \log M _ { t } = \sum _ { i = 1 } ^ { t } Z _ { i } } \end{array}$ , and $a _ { t } = t \gamma - b > 0$ . Since $\{ \tau ^ { * } > t \} \subseteq \{ S _ { t } \leq b \}$

$$
\mathbb {P} _ {q} \left(\tau^ {*} > t\right) \leq \mathbb {P} _ {q} \left\{S _ {t} - t \gamma \leq - a _ {t} \right\}.
$$

Independence and $\mathrm { V a r } _ { q } ( Z _ { i } ) \leq v$ imply $\operatorname { V a r } _ { q } ( S _ { t } ) \leq t v$ . Cantelli’s one-sided inequality therefore yields

$$
\mathbb {P} _ {q} (\tau^ {*} > t) \leq \frac {\mathrm{Var} _ {q} (S _ {t})}{\mathrm{Var} _ {q} (S _ {t}) + a _ {t} ^ {2}} \leq \frac {t v}{t v + a _ {t} ^ {2}},
$$

which is (24).

If each centered increment is sub-Gaussian with variance proxy $s ^ { 2 } .$ , independence gives

$$
\mathbb {E} _ {q} \exp \{\theta (S _ {t} - t \gamma) \} \leq \exp \left(\frac {t \theta^ {2} s ^ {2}}{2}\right).
$$

Applying the Chernof bound $\mathrm { t o } - ( S _ { t } - t \gamma )$ and optimizing at $\theta = a _ { t } / ( t s ^ { 2 } )$ gives

$$
\mathbb {P} _ {q} (S _ {t} - t \gamma \leq - a _ {t}) \leq \exp \left(- \frac {a _ {t} ^ {2}}{2 t s ^ {2}}\right),
$$

which is (25).

Finally, if $| Z _ { i } - \gamma | \leq R$ almost surely, the one-sided Bernstein inequality for independent centered increments with total variance at most tv gives

$$
\mathbb {P} _ {q} (S _ {t} - t \gamma \leq - a _ {t}) \leq \exp \left(- \frac {a _ {t} ^ {2}}{2 t v + \frac {2}{3} R a _ {t}}\right),
$$

which is (26).

## A.8 Interpreting the Finite-Horizon Crossing Bounds

This subsection gives an elementary interpretation of Corollary 2. It does not introduce a new result; its purpose is to explain what the three bounds say, why the quantity $t { \overline { { \Gamma } } } ( q ; h ) - b$ appears, and how the bounds should be used.

Accumulated evidence and the confirmation boundary. Write

$$
\gamma = \overline {{\Gamma}} (q; h) > 0, \quad S _ {t} = \log M _ {t} = \sum_ {i = 1} ^ {t} Z _ {i}, \quad b = \log (1 / \alpha).
$$

The correction is confirmed at

$$
\tau^ {*} = \inf \{t \geq 1: S _ {t} > b \}.
$$

Thus $S _ { t }$ is the accumulated log evidence and b is the amount of log evidence required for confirmation. For example, when $\alpha = 0 . 0 5$ ，

$$
b = \log 2 0 \approx 3.
$$

Under the assumptions of Corollary 2,

$$
\mathbb {E} _ {q} [ S _ {t} ] = t \gamma .
$$

Ignoring random fluctuation, the accumulated evidence reaches the boundary when $t \gamma \approx b$ . This gives the first-order crossing-time heuristic

$$
\tau^ {*} \approx \frac {b}{\gamma} = \frac {\log (1 / \alpha)}{\overline {{\Gamma}} (q ; h)}.\tag{55}
$$

A larger average log-score advantage γ therefore means faster expected confirmation, while a more stringent level α raises the boundary and requires more observations.

Why delayed confirmation is a lower-tail event. The event $\{ \tau ^ { * } > t \}$ means that the process has not crossed the boundary at any time up to t. In particular, its endpoint must satisfy $S _ { t } \leq b .$ Consequently,

$$
\begin{array}{c} \{\tau^ {*} > t \} \subseteq \{S _ {t} \leq b \} \\ = \{S _ {t} - t \gamma \leq - \{t \gamma - b \} \}. \end{array}\tag{56}
$$

When $t \gamma > b ,$ the mean accumulated evidence is already above the boundary. Failure to confirm by time t then requires a downward fluctuation of at least $t \gamma - b$ . The three inequalities in Corollary 2 are simply three ways to bound the probability of this unfavorable fluctuation.

The inclusion in (56) is one-way. A path may cross before time t and later return below $b ,$ in which case $S _ { t } \leq b$ but $\tau ^ { * } \leq t$ . The concentration bounds may therefore be conservative even before accounting for looseness in the concentration inequality itself.

Cantelli bound. If only the one-step variance bound $\mathrm { V a r } _ { q } ( Z _ { i } ) \leq v$ is available, then $\mathrm { V a r } _ { q } ( S _ { t } ) \leq t v$ Cantelli’s one-sided inequality gives

$$
\mathbb {P} _ {q} (\tau^ {*} > t) \leq \frac {t v}{t v + (t \gamma - b) ^ {2}}.
$$

The numerator tv measures accumulated noise, while $( t \gamma - b ) ^ { 2 }$ is the squared evidence margin above the boundary. In schematic form,

$$
\text { delayed - confirmation   probability } \lesssim \frac {\text { noise }}{\text { noise } + \text { squared   signal   margin }}.
$$

For large t, the bound behaves approximately as

$$
\frac {v}{t \gamma^ {2}},
$$

so it decreases at the polynomial rate $1 / t .$ Its advantage is that it requires only a finite variance bound.

Sub-Gaussian bound. If the centered increments have sub-Gaussian variance proxy $s ^ { 2 } .$ , then

$$
\mathbb {P} _ {q} (\tau^ {*} > t) \leq \exp \left\{- \frac {(t \gamma - b) ^ {2}}{2 t s ^ {2}} \right\}.
$$

The same squared evidence margin appears in the numerator, but stronger tail control yields an exponential bound. For large $t ,$

$$
\exp \left\{- \frac {(t \gamma - b) ^ {2}}{2 t s ^ {2}} \right\} \approx \exp \left\{- \frac {t \gamma^ {2}}{2 s ^ {2}} \right\}.
$$

Hence the probability of delayed confirmation can decrease exponentially rather than at the $1 / t$ rate. The practical usefulness of this bound depends on the quality of the certified proxy $s ^ { 2 } { : }$ a very loose proxy can make the exponential bound numerically weak at moderate horizons.

Bernstein bound. If the centered increments are bounded by R and have variance at most $v ,$ then

$$
\mathbb {P} _ {q} (\tau^ {*} > t) \leq \exp \left\{- \frac {(t \gamma - b) ^ {2}}{2 t v + \frac {2}{3} R (t \gamma - b)} \right\}.
$$

This bound uses both the typical scale of fluctuation, represented by v, and the largest possible fluctuation, represented by R. It can improve on a range-based sub-Gaussian bound when the variance is much smaller than the worst-case range would suggest. The Cantelli and Bernstein bounds need not be ordered uniformly: Cantelli can be sharper near the nominal crossing time, while Bernstein can become substantially sharper at longer horizons.

From a delayed-crossing bound to finite-horizon power. Each displayed inequality has the form

$$
\mathbb {P} _ {q} (\tau^ {*} > t) \leq B _ {t}.
$$

Equivalently,

$$
\mathbb {P} _ {q} (\tau^ {*} \leq t) \geq 1 - B _ {t}.\tag{57}
$$

Thus the corollary provides a conservative lower bound on the probability that the correction has been confirmed by time t. It does not give the exact distribution of $\tau ^ { * }$ , and the bounds are informative only after the expected accumulated evidence exceeds the boundary, that is, after $t \gamma > b .$

A numerical illustration. Take $\alpha = 0 . 0 5 ,$ so $b = \log 2 0 \approx 3 .$ and suppose

$$
\gamma = 0. 1, \qquad v = 0. 2, \qquad s ^ {2} = 0. 2.
$$

The heuristic (55) gives

$$
\tau^ {*} \approx \frac {3}{0 . 1} = 3 0.
$$

At $t = 5 0$ , the expected accumulated log evidence is 5, only about 2 above the boundary. The Cantelli bound is

$$
\mathbb {P} _ {q} (\tau^ {*} > 5 0) \leq \frac {5 0 (0 . 2)}{5 0 (0 . 2) + 2 ^ {2}} = \frac {1 0}{1 4} \approx 0. 7 1 4,
$$

while the sub-Gaussian bound is

$$
\mathbb {P} _ {q} (\tau^ {*} > 5 0) \leq \exp \left\{- \frac {2 ^ {2}}{2 (5 0) (0 . 2)} \right\} = e ^ {- 0. 2} \approx 0. 8 1 9.
$$

The exponential bound is not automatically sharper at a short horizon, especially when its variance proxy is conservative.

At t = 200, the evidence margin is $2 0 - 3 = 1 7$ . The two bounds become

$$
\mathbb {P} _ {q} (\tau^ {*} > 2 0 0) \leq \frac {4 0}{4 0 + 1 7 ^ {2}} \approx 0. 1 2 2
$$

and

$$
\mathbb {P} _ {q} (\tau^ {*} > 2 0 0) \leq \exp \left\{- \frac {1 7 ^ {2}}{2 (2 0 0) (0 . 2)} \right\} \approx 0. 0 2 7.
$$

The latter implies

$$
\mathbb {P} _ {q} (\tau^ {*} \leq 2 0 0) \geq 0. 9 7 3.
$$

This example illustrates the basic message: positive mean log evidence determines the approximate crossing time, while concentration controls how likely random fluctuation is to delay confirmation beyond a chosen horizon.

Summary. The logical chain is

positive mean log evidence ⇓ expected evidence reaches the boundary near $b / \gamma$ ⇓ concentration bounds the probability of a delayed crossing.

Finite variance yields a broadly applicable polynomial bound, sub-Gaussian tails yield an exponential bound, and bounded increments together with a variance bound yield the Bernstein alternative. The corollary therefore strengthens the asymptotic statement of eventual confirmation into an explicit finitehorizon guarantee.

## A.9 Proof of Corollary 3: Correctly Specified Predictive Correction

If $q ( \cdot \mid x ) = p _ { h } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$ , then the KL decomposition in (21) gives

$$
\begin{array}{r l} & {\Gamma_ {h} (x) = D _ {\mathrm{KL}} \{p _ {h} (\cdot | x, \mathcal {D} _ {\mathrm{tr}}) \| p _ {0} (\cdot | x, \mathcal {D} _ {\mathrm{tr}}) \} - D _ {\mathrm{KL}} \{p _ {h} (\cdot | x, \mathcal {D} _ {\mathrm{tr}}) \| p _ {h} (\cdot | x, \mathcal {D} _ {\mathrm{tr}}) \}} \\ & {\qquad = D _ {\mathrm{KL}} \{p _ {h} (\cdot | x, \mathcal {D} _ {\mathrm{tr}}) \| p _ {0} (\cdot | x, \mathcal {D} _ {\mathrm{tr}}) \} \geq 0.} \end{array}
$$

The adaptive-input conclusion follows from Proposition 2. Under either sampling regime of Corollary 1, that corollary yields $t ^ { - 1 } \log M _ { t } \to \gamma _ { h }$ almost surely, and $\gamma _ { h } > 0$ implies eventual crossing. Finally, the conditional KL divergence is nonnegative, so $\gamma _ { h } = 0$ if and only if $D _ { \mathrm { K L } } ( p _ { h } ( \cdot \mid X , \mathcal { D } _ { \mathrm { t r } } ) \mid \mid p _ { 0 } ( \cdot \mid X , \mathcal { D } _ { \mathrm { t r } } ) ) = 0$ for $q ^ { X }$ -almost every X, which is equivalent to $p _ { h } ( \cdot \mid X , \mathcal { D } _ { \mathrm { t r } } ) = p _ { 0 } ( \cdot \mid X , \mathcal { D } _ { \mathrm { t r } } )$ there.

## A.10 Proof of Proposition 5: Predictable Tilts

Condition on $\mathcal { G } _ { i }$ . By assumption, $h _ { i } ( X _ { i } , \cdot )$ and $Z _ { i } ( X _ { i } )$ are then fixed functions of the yet-unobserved outcome, while $Y _ { i } \sim p _ { 0 } ( \cdot \mid X _ { i } , D _ { \mathrm { t r } } )$ under the null. Therefore

$$
\mathbb {E} [ e _ {i} \mid \mathcal {G} _ {i} ] = \frac {1}{Z _ {i} (X _ {i})} \int h _ {i} (X _ {i}, y) p _ {0} (y \mid X _ {i}, \mathcal {D} _ {\mathrm{tr}}) d y = 1.
$$

Iterating conditional expectations and multiplying sequentially gives the e-process property exactly as in Section A.3.

## A.11 Proof of Proposition 3: False-Confirmation Control under Target Misspecification

Under $Y _ { i } \mid { \mathcal { G } } _ { i } \sim q _ { i } ( \cdot \mid X _ { i } )$

$$
\mathbb {E} [ e _ {i} \mid \mathcal {G} _ {i} ] = \frac {\mathbb {E} _ {Y \sim q _ {i} (\cdot | X _ {i})} [ h (X _ {i} , Y) ]}{Z _ {h} (X _ {i} , \mathcal {D} _ {\mathrm{tr}})}.
$$

If (29) holds at $X _ { i }$ almost surely for every $i ,$ then this conditional expectation is at most one. Consequently,

$$
\mathbb {E} [ M _ {t} \mid \mathcal {F} _ {t - 1} ] = M _ {t - 1} \mathbb {E} [ e _ {t} \mid \mathcal {F} _ {t - 1} ] \leq M _ {t - 1},
$$

where the inequality follows by conditioning first on $\mathcal { G } _ { t }$ and then on $\mathcal { F } _ { t - 1 }$ . Thus $( M _ { t } )$ is a nonnegative supermartingale and Ville’s inequality gives the α bound. If the pointwise condition holds for every $x ,$ the argument applies to every input process. Failure of the condition only removes this supermartingale proof; it does not imply a converse, as explained in Section 3.4.2.

## A.12 Geometry of the Protected Half-Space

Fix x and abbreviate $P _ { 0 } = p _ { 0 } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } ) , Z = Z _ { h } ( x , \mathcal { D } _ { \mathrm { t r } } )$ , and $H ( Y ) = h ( x , Y )$ . Suppose H is not $P _ { 0 } .$ -almost surely constant. If $P _ { 0 } ( H > Z ) = 0$ , then $H \leq Z$ almost surely; nonconstancy then forces $P _ { 0 } ( H < Z ) > 0$ , whence $\mathbb { E } _ { P _ { 0 } } H < Z$ contradicting $\mathbb { E } _ { P _ { 0 } } H = Z$ . Hence the set $A = \{ H > Z \}$ has positive $P _ { 0 } .$ -probability. Let $R = P _ { 0 } ( \cdot | \ A )$ and $Q _ { \varepsilon } = ( 1 - \varepsilon ) P _ { 0 } + \varepsilon R$ . Then $R \ll P _ { 0 }$ and $\mathbb { E } _ { R } H > Z$ , so

$$
\mathbb {E} _ {Q _ {\varepsilon}} H = (1 - \varepsilon) Z + \varepsilon \mathbb {E} _ {R} H > Z
$$

for every $\varepsilon > 0$ . Thus $Q _ { \varepsilon } \notin \mathcal { H } _ { h } ( x )$ . Its density relative to $P _ { 0 }$ is

$$
\frac {d Q _ {\varepsilon}}{d P _ {0}} = 1 - \varepsilon + \varepsilon \frac {\mathbf {1} _ {A}}{P _ {0} (A)},
$$

which converges uniformly to one as $\varepsilon \downarrow 0$ . Hence total variation, Hellinger distance, and $D _ { \mathrm { K L } } ( Q _ { \varepsilon } \Vert P _ { 0 } )$ all converge to zero. This proves the neighborhood claim.

At the corrected predictive,

$$
\mathbb {E} _ {p _ {h} (\cdot | x, \mathcal {D} _ {\mathrm{tr}})} \left[ \frac {H}{Z} \right] = \int \frac {H}{Z} \frac {H}{Z} d P _ {0} = \mathbb {E} _ {P _ {0}} \left[ \left(\frac {H}{Z}\right) ^ {2} \right] = 1 + \operatorname{Var} _ {P _ {0}} \left(\frac {H}{Z}\right),
$$

with the final quantity interpreted in the extended sense. It exceeds one for every nontrivial tilt. Finally, if $Q \in \mathcal { H } _ { h } ( x )$ , then $\mathbb { E } _ { Q } [ e ] \le 1$ , and Jensen gives

$$
\mathbb {E} _ {Q} [ \log e ] \leq \log \mathbb {E} _ {Q} [ e ] \leq 0
$$

whenever the logarithmic expectation is well defined.

## A.13 Proof of Proposition 4: Overshoot Identity

The inequality. $( M _ { t \wedge \tau ^ { * } } )$ is a nonnegative $P _ { 0 } .$ -martingale with $\mathbb { E } _ { P _ { 0 } } [ M _ { t \wedge \tau ^ { * } } ] = 1$ . As $t \to \infty$

$$
M _ {t \wedge \tau^ {*}} \longrightarrow M _ {\tau^ {*}} \mathbf {1} \{\tau^ {*} <   \infty \} + M _ {\infty} \mathbf {1} \{\tau^ {*} = \infty \} \quad \mathrm{a.s.}
$$

The limit $M _ { \infty }$ exists by nonnegative martingale convergence. Fatou’s lemma gives

$$
\mathbb {E} _ {P _ {0}} \left[ M _ {\tau^ {*}} \mathbf {1} \left\{\tau^ {*} <   \infty \right\} \right] \leq 1.
$$

Since $M _ { \tau ^ { * } } > 1 / \alpha$ on $\{ \tau ^ { * } < \infty \}$ , factor the left side as

$$
P _ {0} (\tau^ {*} <   \infty) \mathbb {E} _ {P _ {0}} [ M _ {\tau^ {*}} | \tau^ {*} <   \infty ]
$$

to obtain (32).

The exact identity. Let $P _ { 0 }$ and $P _ { h }$ denote the distributions of the data stream under $H _ { 0 } ^ { \mathrm { p r e d } }$ and $H _ { h } ^ { \mathrm { p r e d } }$ with the same conditional input mechanism under both. By Lemma 1, $P _ { h } \ll P _ { 0 }$ on each $\mathcal { F } _ { t }$ even without strict positivity of $h ;$ the input factors then cancel, and

$$
\frac {d P _ {h} | _ {\mathcal {F} _ {t}}}{d P _ {0} | _ {\mathcal {F} _ {t}}} = \prod_ {i = 1} ^ {t} \frac {p _ {h} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})}{p _ {0} (Y _ {i} \mid X _ {i} , \mathcal {D} _ {\mathrm{tr}})} = M _ {t}.
$$

For every finite $t , \{ \tau ^ { * } = t \} \in \mathcal { F } _ { t }$ , so

$$
P _ {h} (\tau^ {*} = t) = \mathbb {E} _ {P _ {0}} [ M _ {t} {\bf 1} \{\tau^ {*} = t \} ] = \mathbb {E} _ {P _ {0}} [ M _ {\tau^ {*}} {\bf 1} \{\tau^ {*} = t \} ].
$$

Summing over $t \geq 1$ and using monotone convergence gives

$$
\mathbb {E} _ {P _ {0}} \left[ M _ {\tau^ {*}} \mathbf {1} \{\tau^ {*} <   \infty \} \right] = P _ {h} (\tau^ {*} <   \infty),
$$

which is $( 3 3 ) ;$ factoring the left side gives (34) whenever $P _ { 0 } ( \tau ^ { * } < \infty ) > 0$ . If log $M _ { t }  + \infty \ P _ { h }$ -almost surely, then $P _ { h } ( \tau ^ { * } < \infty ) = 1$ . This also forces $P _ { 0 } ( \tau ^ { * } < \infty ) > 0 \colon$ otherwise $P _ { 0 } ( \tau ^ { * } = t ) = 0$ for every finite $t ,$ and the finite-time change-of-measure identity would give

$$
P _ {h} (\tau^ {*} = t) = \mathbb {E} _ {P _ {0}} [ M _ {t} \mathbf {1} \{\tau^ {*} = t \} ] = 0 \quad \text {   for   every   } t,
$$

contradicting $P _ { h } ( \tau ^ { * } < \infty ) = 1$ . Therefore (35) follows.

On the uniform-integrability route. If $M _ { \infty } = 0$ almost surely, uniform integrability of $( M _ { t \wedge \tau ^ { * } } )$ is equivalent to $L ^ { 1 }$ convergence to $M _ { \tau ^ { * } } \mathbf { 1 } \{ \tau ^ { * } < \infty \}$ and hence to preservation of the expectation at the limit. It is therefore equivalent to the desired equality rather than an independently checkable suficient condition. The change-of-measure argument avoids this circularity.

## A.14 Proof of Proposition 7: Composite Tolerance Null

Condition on $\mathcal { G } _ { i }$ and write $x = X _ { i }$ and $\eta = \eta _ { i }$ . Under $Y _ { i } \sim p _ { \eta } ( \cdot \mid x , \mathcal { D } _ { \mathrm { t r } } )$

$$
\mathbb {E} [ \exp \{\Delta \phi (x, Y _ {i}) \} \mid \mathcal {G} _ {i} ] = \frac {Z _ {\eta + \Delta} (x)}{Z _ {\eta} (x)}.
$$

Therefore

$$
\begin{array}{r l} & {\mathbb {E} [ e _ {i} ^ {\mathrm{tol}} \mid \mathcal {G} _ {i} ] = \frac {Z _ {\eta + \Delta} (x)}{Z _ {\eta} (x)} \frac {Z _ {\eta_ {\mathrm{tol}}} (x)}{Z _ {\eta_ {\mathrm{tol}} + \Delta} (x)}} \\ & {\qquad = \exp ([ \psi_ {x} (\eta + \Delta) - \psi_ {x} (\eta) ] - [ \psi_ {x} (\eta_ {\mathrm{tol}} + \Delta) - \psi_ {x} (\eta_ {\mathrm{tol}}) ]).} \end{array}
$$

Because $\psi _ { x }$ is convex, the increment map

$$
\eta \longmapsto \psi_ {x} (\eta + \Delta) - \psi_ {x} (\eta)
$$

is nondecreasing wherever both endpoints lie in the common interval I. Here $\eta + \Delta \in \mathcal { I }$ follows automatically because I is an interval containing η and $\eta _ { \mathrm { t o l } } + \Delta$ , with $\eta \le \eta + \Delta \le \eta _ { \mathrm { t o l } } + \Delta$ . Thus the exponent is nonpositive when $\eta \leq \eta _ { \mathrm { t o l } }$ , proving $\mathbb { E } [ e _ { i } ^ { \mathrm { t o l } } \mid { \mathcal { G } } _ { i } ] \leq 1$ . Sequential composition gives the supermartingale and Ville bounds. Strict convexity is needed only for a strict or converse implication.

## A.15 Proof of Proposition 6: Mixture and Correction Panel

For each $\theta , \ ( M _ { t } ( \theta ) )$ is a nonnegative martingale with $M _ { 0 } ( \theta ) = 1$ under the null. Assume that $( \theta , \omega ) \mapsto$ $M _ { t } ( \theta ) ( \omega )$ is jointly measurable with respect to $B ( \Theta ) \otimes \mathcal { F } _ { t }$ , which follows, for example, when $( \theta , x , y ) \mapsto$ $h _ { \theta } ( x , y )$ is jointly measurable. Conditional Tonelli then gives

$$
\mathbb {E} \left[ M _ {t} ^ {\text { mix }} \mid \mathcal {F} _ {t - 1} \right] = \int \mathbb {E} [ M _ {t} (\theta) \mid \mathcal {F} _ {t - 1} ] d \Pi (\theta) = \int M _ {t - 1} (\theta) d \Pi (\theta) = M _ {t - 1} ^ {\text { mix }},
$$

provided Π is fixed before testing. Hence $M _ { t } ^ { \operatorname* { m i x } }$ is a nonnegative martingale.

## A.16 Gaussian Exponential-Tilt Derivation for Section 4.3

Let $p _ { 0 } ( y \mid x , \mathcal { D } _ { \mathrm { t r } } ) = \mathcal { N } \big ( y \mid \mu _ { 0 } ( x ) , \sigma _ { 0 } ^ { 2 } ( x ) \big )$ and choose $h _ { \eta } ( x , y ) = \exp \{ \eta g ( x ) y \}$ . The normalizer is

$$
Z _ {\eta} (x) = \exp \left\{\eta g (x) \mu_ {0} (x) + \frac {1}{2} \eta^ {2} g ^ {2} (x) \sigma_ {0} ^ {2} (x) \right\}.
$$

The corrected predictive is Gaussian with mean

$$
\mu_ {0} (x) + \eta g (x) \sigma_ {0} ^ {2} (x)
$$

and unchanged variance $\sigma _ { 0 } ^ { 2 } ( x )$ . Thus an exponential tilt in $g ( x ) y$ is equivalent to a conditional mean correction whose size scales with the source predictive variance; with $g \equiv 1$ and $\eta = \beta$ this is the label-shif equivalence used in the sanity check.

The raw feature $g ( x ) y$ and the standardized-residual feature $\phi _ { \mathrm { m e a n } } ( x , y ) = g ( x ) \{ y - \mu _ { 0 } ( x ) \} / \sigma _ { 0 } ^ { 2 } ( x )$ are related, but the parameter mapping must respect heteroscedasticity. Indeed

$$
\exp \left\{\frac {\delta g (x) \{y - \mu_ {0} (x) \}}{\sigma_ {0} ^ {2} (x)} \right\} = \exp \left\{- \frac {\delta g (x) \mu_ {0} (x)}{\sigma_ {0} ^ {2} (x)} \right\} \exp \left\{\frac {\delta g (x) y}{\sigma_ {0} ^ {2} (x)} \right\},
$$

and the first factor depends only on $x ,$ so it cancels in the normalization (1). Thus the standardized feature is equivalent to a raw linear tilt with input-dependent coeficient $\eta ( x ) = \delta / \sigma _ { 0 } ^ { 2 } ( x )$ . If the source variance is homoscedastic, $\sigma _ { 0 } ^ { 2 } ( x ) \equiv \sigma _ { 0 } ^ { 2 }$ , this reduces to the scalar relation $\delta = \eta \sigma _ { 0 } ^ { 2 }$ . With a scalar η and heteroscedastic $\sigma _ { 0 } ^ { 2 } ( x )$ , however, the raw feature $g ( x ) y$ produces the diferent mean correction $\eta g ( x ) \sigma _ { 0 } ^ { 2 } ( x )$ The standardized form is used in the main text because its scalar parameter $\eta = \delta$ is directly the additive shift multiplier in $\mu _ { 0 } ( x ) + \delta g ( x )$ , which is the parametrization used in Proposition $7$ and Remark 1.