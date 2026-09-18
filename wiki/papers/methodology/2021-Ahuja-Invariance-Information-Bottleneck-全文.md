---
title: "2021-Ahuja-Invariance-Information-Bottleneck"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2021-Ahuja-Invariance-Information-Bottleneck.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Invariance Principle Meets Information Bottleneck for Out-of-Distribution Generalization

Kartik Ahuja<sup>†</sup>

Ethan Caballero<sup>∗</sup> <sup>†</sup>

Dinghuai Zhang<sup>∗</sup> <sup>†</sup>

Jean-Christophe Gagnon-Audet <sup>†</sup>

Yoshua Bengio <sup>†</sup> Ioannis Mitliagkas<sup>†</sup>

Irina Rish<sup>†</sup>

## Abstract

The invariance principle from causality is at the heart of notable approaches such as invariant risk minimization (IRM) that seek to address out-of-distribution (OOD) generalization failures. Despite the promising theory, invariance principle-based approaches fail in common classification tasks, where invariant (causal) features capture all the information about the label. Are these failures due to the methods failing to capture the invariance? Or is the invariance principle itself insufficient? To answer these questions, we revisit the fundamental assumptions in linear regression tasks, where invariance-based approaches were shown to provably generalize OOD. In contrast to the linear regression tasks, we show that for linear classification tasks we need much stronger restrictions on the distribution shifts, or otherwise OOD generalization is impossible. Furthermore, even with appropriate restrictions on distribution shifts in place, we show that the invariance principle alone is insufficient. We prove that a form of the information bottleneck constraint along with invariance helps address key failures when invariant features capture all the information about the label and also retains the existing success when they do not. We propose an approach that incorporates both of these principles and demonstrate its effectiveness in several experiments.

## 1 Introduction

Recent years have witnessed an explosion of examples showing deep learning models are prone to exploiting shortcuts (spurious features) (Geirhos et al., 2020; Pezeshki et al., 2020) which make them fail to generalize out-of-distribution (OOD). In Beery et al. (2018), a convolutional neural network was trained to classify camels from cows; however, it was found that the model relied on the background color (e.g., green pastures for cows) and not on the properties of the animals (e.g., shape). These examples become very concerning when they occur in real-life applications (e.g., COVID-19 detection (DeGrave et al., 2020)).

To address these out-of-distribution generalization failures, invariant risk minimization (Arjovsky et al., 2019) and several other works were proposed (Ahuja et al., 2020; Pezeshki et al., 2020; Krueger et al., 2020; Robey et al., 2021; Zhang et al., 2021). The invariance principle from causality (Peters et al., 2015; Pearl, 1995) is at the heart of these works. The principle distinguishes predictors that only rely on the causes of the label from those that do not. The optimal predictor that only focuses on the causes is invariant and min-max optimal (Rojas-Carulla et al., 2018; Koyama and Yamaguchi, 2020; Ahuja et al., 2021) under many distribution shifts but the same is not true for other predictors.

Our contributions. Despite the promising theory, invariance principle-based approaches fail in settings (Aubin et al., 2021) where invariant features capture all information about the label contained in the input. A particular example is image classification (e.g., cow vs. camel) (Beery et al., 2018) where the label is a deterministic function of the invariant features (e.g., shape of the animal), and does not depend on the spurious features (e.g., background). To understand such failures, we revisit the fundamental assumptions in linear regression tasks, where invariance-based approaches were shown to provably generalize OOD. We show that, in contrast to the linear regression tasks, OOD generalization is significantly harder for linear classification tasks; we need much stronger restrictions in the form of support overlap assumptions<sup>3</sup> on the distribution shifts, or otherwise it is not possible to guarantee OOD generalization under interventions on variables other than the target class. We then proceed to show that, even under the right assumptions on distribution shifts, the invariance principle is insufficient. However, we establish that information bottleneck (IB) constraints (Tishby et al., 2000), together with the invariance principle, provably works in both settings – when invariant features completely capture the information about the label and also when they do not. (Table 1 summarizes our theoretical results presented later). We propose an approach that combines both these principles and demonstrate its effectiveness on linear unit tests (Aubin et al., 2021) and on different real datasets.

<table><tr><td rowspan="2">Task</td><td rowspan="2">Invariant features capture label info</td><td rowspan="2">Support overlap invariant features</td><td rowspan="2">Support overlap spurious features</td><td colspan="4">OOD generalization guarantee ( $\mathcal{E}_{tr} \rightarrow \mathcal{E}_{all}$ )</td></tr><tr><td>ERM</td><td>IRM</td><td>IB-ERM</td><td>IB-IRM</td></tr><tr><td rowspan="5">Linear Classification</td><td>Full/Partial</td><td>No</td><td>Yes/No</td><td colspan="4">Impossible for any algorithm to generalize OOD [Thm2]</td></tr><tr><td>Full</td><td>Yes</td><td>No</td><td>X</td><td>X</td><td>√</td><td>[Thm3,4]</td></tr><tr><td>Partial</td><td>Yes</td><td>No</td><td>X</td><td>X</td><td>X</td><td>[Appendix]</td></tr><tr><td>Full</td><td>Yes</td><td>Yes</td><td>√</td><td>√</td><td>√</td><td>[Thm3,4]</td></tr><tr><td>Partial</td><td>Yes</td><td>Yes</td><td>X</td><td>√</td><td>X</td><td>√</td></tr><tr><td rowspan="2">Linear Regression</td><td>Full</td><td>No</td><td>No</td><td>√</td><td>√</td><td>√</td><td>[Thm4]</td></tr><tr><td>Partial</td><td>No</td><td>No</td><td>X</td><td>√</td><td>X</td><td>√</td></tr></table>

Table 1: Summary of the new and existing results (Arjovsky et al., 2019; Rosenfeld et al., 2021). IB-ERM (IRM): information bottleneck - empirical (invariant) risk minimization ERM (IRM).

## 2 OOD generalization and invariance: background & failures

Background. We consider a supervised training data D gathered from a set of training environments $\mathcal { E } _ { t r } \colon D = \{ D ^ { e } \} _ { e \in \mathcal { E } _ { t r } }$ , where $D ^ { e } = \{ x _ { i } ^ { e } , y _ { i } ^ { e } \} _ { i = 1 } ^ { n ^ { e } }$ is the dataset from environment $e \in \mathcal { E } _ { t r }$ and $n ^ { e }$ is the number of instances in environment e. $x _ { i } ^ { e } \in \mathbb { R } ^ { d }$ and $y _ { i } ^ { e } \in \mathcal { V } \subseteq \mathbb { R } ^ { k }$ correspond to the input feature value and the label for $i ^ { t h }$ instance respectively. Each $( x _ { i } ^ { e } , y _ { i } ^ { e } )$ is an i.i.d. draw from $\mathbb { P } ^ { e }$ , where $\mathbb { P } ^ { e }$ is the joint distribution of the input feature and the label in environment e. Let $\mathcal { X } ^ { e }$ be the support of the input feature values in the environment e. The goal of OOD generalization is to use training data D to construct a predictor $f : \mathbb { R } ^ { d }  \mathbb { R } ^ { k }$ that performs well across many unseen environments in ${ \mathcal { E } } _ { a l l }$ where $\mathcal { E } _ { a l l } \supset \bar { \mathcal { E } } _ { t r }$ . Define the risk of $f$ in environment e as $R ^ { e } ( f ) \doteq \mathbb { E } \bigl [ \ell ( f ( X ^ { e } ) , Y ^ { e } ) \bigr ]$ , where for example \` can be 0-1 loss, logistic loss, square loss, $( X ^ { e } , Y ^ { e } ) \sim { \mathbb { P } } ^ { e }$ , and the expectation E is w.r.t. $\mathbb { P } ^ { e }$ . Formally stated, our goal is to use the data from training environments $\mathcal { E } _ { t r }$ to find $f : \mathbb { R } ^ { d }  \mathcal { V }$ to minimize e

$$
\min _ {f} \max _ {e \in \mathcal {E} _ {a l l}} R ^ {e} (f).\tag{1}
$$

So far we did not state any restrictions on ${ \mathcal { E } } _ { a l l }$ . Consider binary classification: without any restrictions on ${ \mathcal { E } } _ { a l l }$ , no method can reduce the above objective (\` is 0-1 loss) to below one. Suppose a method outputs $f ^ { * } ; \mathrm { i f } \exists e \in \mathcal { E } _ { a l l } \ \backslash \mathcal { E } _ { t \tau }$ with labels based on $1 - f ^ { * }$ , then it achieves an error of one. Some assumptions on ${ \mathcal { E } } _ { a l l }$ are thus necessary. Consider how ${ \mathcal { E } } _ { a l l }$ is restricted using invariance for linear regressions (Arjovsky et al., 2019).

Assumption 1. Linear regression structural equation model (SEM). In each $e \in \mathcal { E } _ { a l l }$

$$
\begin{array}{l} Y ^ {e} \leftarrow w _ {\mathrm{inv}} ^ {*} \cdot Z _ {\mathrm{inv}} ^ {e} + \epsilon^ {e}, \quad Z _ {\mathrm{inv}} ^ {e} \perp \epsilon^ {e}, \quad \mathbb {E} [ \epsilon^ {e} ] = 0, \mathbb {E} \big [ | \epsilon^ {e} | ^ {2} \big ] \leq \sigma_ {\mathrm{sup}} ^ {2} \\ X ^ {e} \leftarrow S (Z _ {\mathrm{inv}} ^ {e}, Z _ {\mathrm{spu}} ^ {e}) \end{array}\tag{2}
$$

where $w _ { \mathsf { i n v } } ^ { * } \in \mathbb { R } ^ { m } , Z _ { \mathsf { i n v } } ^ { e } \in \mathbb { R } ^ { m } , Z _ { \mathsf { s p u } } \in \mathbb { R } ^ { o } , S \in \mathbb { R } ^ { d \times ( m + o ) }$ , S is invertible $( m + o = d ) .$ . Wefocus on invertible S but several results extend to non-invertible S as well (see Appendix).

Assumption 1 states how $Y ^ { e }$ and $X ^ { e }$ are generated from latent invariant features $Z _ { \mathrm { i n v } } ^ { e \mathrm { ~ 4 ~ } }$ , latent spurious features $Z _ { \mathsf { s p u } } ^ { e }$ and noise $\epsilon ^ { e }$ . The relationship between label and invariant features is invariant, $i . e .$ $w _ { \mathrm { i n v } } ^ { \ast }$ is fixed across all environments. However, the distributions of $Z _ { \mathrm { i n v } } ^ { e } , Z _ { \mathsf { s p u } } ^ { e } .$ , and $\epsilon ^ { e }$ are allowed to change arbitrarily across all the environments. Suppose S is identity. If we regress only on the invariant features $\dot { Z } _ { \mathrm { i n v } } ^ { e }$ , then the optimal solution is $w _ { \mathrm { i n v } } ^ { \ast }$ , which is independent of the environment, and the error it achieves is bounded above by the variance of $\epsilon ^ { e } ( \sigma _ { \mathsf { s u p } } ^ { 2 } )$ . If we regress on the entire $Z ^ { e }$ and the optimal predictor places a non-zero weight on $Z _ { \mathsf { s p u } } ^ { e } ( \mathsf { e . g . } , Z _ { \mathsf { s p u } } ^ { e } \gets \bar { Y } ^ { e } + \zeta ^ { e } )$ , then this predictor fails to solve equation $( 1 ) \left( \exists e \in \mathcal { E } _ { a l l } , Z _ { \mathsf { s o u } } ^ { e } \to \infty \right.$ , error → ∞, see Appendix for details). Also, not only regressing on $Z _ { \mathrm { i n v } } ^ { e }$ is better than on $Z ^ { e }$ , it can be shown that it is optimal, i.e., it solves equation (1) under Assumption 1 and achieves a value of $\sigma _ { \mathsf { s u p } } ^ { 2 }$ for the objective in equation (1).

Invariant predictor. Define a linear representation map $\Phi : \mathbb { R } ^ { r \times d }$ (that transforms $X ^ { e }$ as $\Phi ( X ^ { e } ) )$ and define a linear classifier $\boldsymbol { w } : \mathbb { R } ^ { k \times r }$ (that operates on the representation $w \cdot \Phi ( X ^ { e } ) )$ . We want to search for representations Φ such that ${ \mathbb E } [ Y ^ { e } | \dot { \Phi } ( X ^ { e } ) ]$ is invariant (in Assumption 1 if $\begin{array} { r } { \tilde { \Phi } ( X ^ { e } ) = Z _ { \mathsf { i n v } } ^ { e } , } \end{array}$ then ${ \mathbb E } [ Y ^ { e } | \dot { \Phi ( X ^ { e } ) } ]$ is invariant). We say that a data representation Φ elicits an invariant predictor $w \cdot \Phi$ across the set of training environments $\mathcal { E } _ { t r }$ if there is a predictor w that simultaneously achieves the minimum risk, i.e., w ∈ arg min<sub>w˜</sub> $R ^ { e } ( \tilde { w } \cdot \Phi )$ ), ∀e $\in \mathcal { E } _ { t r }$ . The main objective of IRM is stated as

$$
\min _ {w \in \mathbb {R} ^ {k \times r}, \Phi \in \mathbb {R} ^ {r \times d}} \frac {1}{| \mathcal {E} _ {t r} |} \sum_ {e \in \mathcal {E} _ {t r}} R ^ {e} (w \cdot \Phi) \quad \text {s.t.} w \in \arg \min _ {\tilde {w} \in \mathbb {R} ^ {k \times r}} R ^ {e} (\tilde {w} \cdot \Phi),   \forall e \in \mathcal {E} _ {t r}.\tag{3}
$$

Observe that if we drop the constraints in the above which search only over invariant predictors, then we get the standard empirical risk minimization (ERM) (Vapnik, 1992) (assuming all the training environments occur with equal probability). In all our theorems, we use 0-1 loss for binary classification $\mathcal { V } = \{ 0 , 1 \}$ and square loss for regression $\mathcal { V } = \mathbb { R }$ . For binary classification, the output of the predictor is given as $\mathsf { I } ( w \cdot \Phi ( X ^ { e } ) )$ , where $\mathsf { I } ( \cdot )$ is the indicator function that takes 1 if the input is $\geq 0$ and 0 otherwise, and the risk is $R ^ { e } ( w \cdot \Phi ) = \dot { \mathbb { E } } \big \lvert | 1 ( w \cdot \Phi ( X ^ { e } ) ) - Y ^ { e } \rvert \big \rvert$ . For regression, the output of the predictor is $w \cdot \Phi ( X ^ { e } )$ and the corresponding risk is $R ^ { e } ( w \cdot \Phi ) = \bar { \mathbb { E } } \big [ ( w \cdot \Phi ( X ^ { e } ) - Y ^ { e } ) ^ { 2 } \big ]$ . We now present the main OOD generalization result from Arjovsky et al. (2019) for linear regressions.

Theorem 1. (Informal) IfAssumption 1 is satisfied, $\mathsf { R a n k } [ \Phi ] > 0 , \vert \mathcal { E } _ { t r } \vert > 2 d ,$ , and $\mathcal { E } _ { t r }$ lie in a linear general position (a mild condition on the data in $\mathcal { E } _ { t r }$ , defined in the Appendix), then each solution to equation (3) achieves OOD generalization (solves equation (1), @ $e \in \mathcal { E } _ { a l l }$ with $r i s k > \sigma _ { \mathsf { s u p } } ^ { 2 } )$

Despite the above guarantees, IRM has been shown to fail in several cases including linear SEMs in (Aubin et al., 2021). We take a closer look at these failures next.

Understanding the failures: fully informative invariant features vs. partially informative invariant features (FIIF vs. PIIF). We define properties salient to the datasets/SEMs used in the OOD generalization literature. Each $e \in \mathcal { E } _ { a l l }$ , the distribution $( X ^ { e } , Y ^ { e } ) \sim \mathbb { P } ^ { e }$ satisfies the following properties. a) ∃ a map $\Phi ^ { * }$ (linear or not), which we call an invariant feature map, such that $\mathbb { E } \lceil Y ^ { e } \rceil \bar { \Phi ^ { * } } \bar { ( X ^ { e } ) } \rceil$ is the same for all $e \in \mathcal { E } _ { a l l }$ and $Y ^ { e } \not \downarrow \Phi ^ { * } ( X ^ { e } )$ . These conditions ensure $\Phi ^ { * }$ maps to features that have a finite predictive power and have the same optimal predictor across ${ \mathcal { E } } _ { a l l }$ . For the SEM in Assumption ${ \bar { 1 , \Phi ^ { * } } }$ maps to $Z _ { \mathrm { i n v } } ^ { e } . \mathrm { \bf ~ b } ) \exists$ a map $\Psi ^ { * }$ (linear or not), which we call spurious feature map, such that $\mathbb { E } \lceil Y ^ { e } \rceil \Psi ^ { * } \left( X ^ { e } \right) \rceil$ is not the same for all $e \in \mathcal { E } _ { a l l }$ and $Y ^ { e } \not \downarrow \Psi ^ { * } ( X ^ { e } )$ for some environments. $\Psi ^ { * }$ often creates a hindrance in learning predictors that only rely on $\Phi ^ { * }$ . Note that $\Psi ^ { * }$ should not be a transformation of some $\Phi ^ { * }$ . For the SEM in Assumption 1, suppose $Z _ { \mathsf { s p u } } ^ { e }$ is anti-causally related to $Y ^ { e }$ , then $\Psi ^ { * }$ maps to $Z _ { \mathsf { s p u } } ^ { e }$ (See Appendix for an example).

In the colored MNIST (CMNIST) dataset (Arjovsky et al., 2019), the digits are colored in such a way that in the training domain, color is highly predictive of the digit label but this correlation being spurious breaks down at test time. Suppose the invariant feature map $\Phi ^ { * }$ extracts the uncolored digit and the spurious feature map $\Psi ^ { * }$ extracts the background color. Ahuja et al. (2021) studied two variations of the colored MNIST dataset, which differed in the way final labels are generated from original MNIST labels (corrupted with noise or not). They showed that the IRM exhibits good OOD generalization (50% improvement over ERM) in anti-causal-CMNIST (AC-CMNIST, original data from Arjovsky et al. (2019)) but is no different from ERM and fails in covariate shift-CMNIST (CS CMNIST). In AC-CMNIST, the invariant features $\Phi ^ { * } ( X ^ { e } )$ (uncolored digit) are partially informative about the label, i.e., Y $\nmid X ^ { e } | \Phi ^ { * } ( X ^ { e } )$ , and color contains information about label not contained in the uncolored digit. On the other hand in CS-CMNIST, invariant features are fully informative about the label, i.e., $Y \perp X ^ { e } | \Phi ^ { * } ( X ^ { e } )$ , i.e., they contains all the information about the label that is contained in input $X ^ { e }$ . Most human labelled datasets have fully informative invariant features; the labels (digit value) only depend on the invariant features (uncolored digit) and spurious features (color of the digit) do not affect the label. <sup>5</sup> In the rare case, when the humans are asked to label images in which the object being labelled itself is blurred, humans can rely on spurious features such as the background making such a data representative of PIIF setting. In Table 2, we divide the different datasets used in the literature based on informativeness of the invariant features. We observe that when the invariant features are fully informative, both IRM and ERM fail but only in classification tasks and not in regression tasks (Ahuja et al., 2021); this is consistent with the linear regression result in Theorem 1, where IRM succeeds regardless of whether $Y ^ { e } \perp X ^ { e } | Z _ { \mathsf { i n v } } ^ { e }$ holds or not. Motivated by this observation, we take a closer look at the classification tasks where invariant features are fully informative.

<table><tr><td>Fully informative invariant features (FIIF)  $\forall e \in {\mathcal{E}}_{all},{Y}^{e} \perp {X}^{e}\left| {\Phi }^{ * }\left( {X}^{e}\right) \right.$ </td><td>Partially informative invariant features (PIIF)  $\exists e \in {\mathcal{E}}_{all}{Y}^{e}\not\perp {X}^{e}\left| {\Phi }^{ * }\left( {X}^{e}\right) \right.$ </td></tr><tr><td>Task: classification Example 2/2S, CS-CMNIST SEM in Assumption 2 ERM and IRM fail Theorem 3,4 (This paper)</td><td>Task: classification or regression Example 1/1S, Example 3/3S, AC-CMNIST SEM in Rosenfeld et al. (2021) ERM fails, IRM succeeds sometimes Theorem 9, 5.1 (Arjovsky et al., 2019; Rosenfeld et al., 2021)</td></tr></table>

Table 2: Categorization of OOD evaluation datasets and SEMs. Example 1/1S, 2/2S, 3/3S from (Aubin et al., 2021), AC-CMNIST(Arjovsky et al., 2019), CS-CMNIST(Ahuja et al., 2021).

## 3 OOD generalization theory for linear classification tasks

A two-dimensional example with fully informative invariant features. We start with a 2D classification example (based on Nagarajan et al. (2021)), which can be understood as a simplified version of the CS-CMNIST dataset (Ahuja et al., 2021), Example 2/2S of Aubin et al. (2021), where both IRM and ERM fail. The example goes as follows. In each training environment $e \in \mathcal { E } _ { t r }$

$$
\begin{array}{l} Y ^ {e} \leftarrow \mathsf {I} \Big (X _ {\text {inv}} ^ {e} - \frac {1}{2} \Big), \text {where} X _ {\text {inv}} ^ {e} \in \{0, 1 \} \text {is Bernoulli} \Big (\frac {1}{2} \Big), \\ X _ {\text {spu}} ^ {e} \leftarrow X _ {\text {inv}} ^ {e} \oplus W ^ {e}, \text {where} W ^ {e} \in \{0, 1 \} \text {is Bernoulli} \big (1 - p ^ {e} \big) \text {with selection bias} p ^ {e} > \frac {1}{2}, \end{array}\tag{4}
$$

where Bernoulli(a) takes value 1 with probability a and 0 otherwise. Each training environment is characterized by the probability $p ^ { e }$ . Following Assumption 1, we assume that the labelling function does not change from $\mathcal { E } _ { t r } \mathrm { \ t o \ } \mathcal { E } _ { a l l }$ , thus the relation between the label and the invariant features does not change. Assume that the distribution of $X _ { \mathrm { i n v } } ^ { e }$ and $X _ { \mathsf { s p u } } ^ { e }$ can change arbitrarily. See Figure 1a) for a pictorial representation of this example illustrating the gist of the problem: there are many classifiers with the same error on $\mathcal { E } _ { t r }$ while only the one identical to the labelling function $\vert ( X _ { \mathrm { i n v } } ^ { e } - \frac { 1 } { 2 } )$ generalizes correctly OOD. Define a classifier $\begin{array} { r } { \mathsf { I } \big ( w _ { \mathsf { i n v } } x _ { \mathsf { i n v } } + w _ { \mathsf { s p u } } x _ { \mathsf { s p u } } - \frac { 1 } { 2 } \big ( w _ { \mathsf { i n v } } + w _ { \mathsf { s p u } } \big ) \big ) } \end{array}$ . Define a set of classifiers $\mathcal { S } = \{ ( w _ { \mathsf { i n v } } , w _ { \mathsf { s p u } } )$ s.t. $w _ { \mathsf { i n v } } > | w _ { \mathsf { s p u } } | \}$ . Observe that all the classifiers in S achieve a zero classification error on the training environments. However, only classifiers for which $w _ { \mathsf { s p u } } = 0$ solve the OOD generalization (eq. (1)). With Φ as the identity, it can be shown that all the classifiers S form an invariant predictor (satisfy the constraint in equation (3) over all the training environments when \` is the 0-1 loss). Observe that increasing the number of training environments to infinity does not address the problem, unlike with the linear regression result discussed in Theorem 1 (Arjovsky et al., 2019), where it was shown that if the number of environments increases linearly in the dimension of the data, then the solution to IRM also solves the OOD generalization (eq. (1)). <sup>6</sup> We use the above example to construct general SEMs for linear classification when the invariant features are fully informative. We follow the structure of the SEM from Assumption 1 in our construction.

![](images/560e5f533211d78c81405d2f0b152a28e141ecbbf874f0f1327bc15bec5723df.jpg)  
Figure 1: a) 2D classification example illustrating multiple invariant predictors: Most of these predictors rely on spurious features and each of them achieve zero error across all $\mathcal { E } _ { t r } , \mathfrak { b } )$ illustration of the impossibility result. If latent invariant features in the training environments are separable, then there are multiple equally good candidates that could have generated the data, and the algorithm cannot distinguish between these.

Assumption 2. Linear classification structural equation model (FIIF). In each $e \in \mathcal { E } _ { a l l }$

$$
\begin{array}{l} Y ^ {e} \leftarrow \mathsf {I} \big (w _ {\text {inv}} ^ {*} \cdot Z _ {\text {inv}} ^ {e} \big) \oplus N ^ {e}, \quad N ^ {e} \sim \mathsf {B e r n o u l l i} (q), q <   \frac {1}{2}, \quad N ^ {e} \perp (Z _ {\text {inv}} ^ {e}, Z _ {\text {spu}} ^ {e}), \\ X ^ {e} \leftarrow S \big (Z _ {\text {inv}} ^ {e}, Z _ {\text {spu}} ^ {e} \big), \end{array}\tag{5}
$$

where $\boldsymbol { w _ { \mathrm { i n v } } ^ { * } } \in \mathbb { R } ^ { m }$ with $\| w _ { \mathrm { i n v } } ^ { * } \| = 1$ is the labelling hyperplane, $Z _ { \mathsf { i n v } } ^ { e } \in \mathbb { R } ^ { m } , Z _ { \mathsf { s p u } } ^ { e } \in \mathbb { R } ^ { o } , N ^ { e }$ is binary noise with identical distribution across environments, ⊕ is the XOR operator, S is invertible.

If noise level q is zero, then the above SEM covers linearly separable problems. See Figure 2a) for the directed acyclic graph (DAG) corresponding to this SEM. From the DAG observe that $\mathbf { \bar { \boldsymbol { Y } } } ^ { e } \perp \bar { X } ^ { e } | Z _ { \mathsf { i n v } } ^ { e } ,$ which implies that the invariant features are fully informative. Contrast this with a DAG that follows Assumption 1 shown in Figure 2b), where $Y ^ { e } \downarrow \bar { X ^ { e } } | Z _ { \mathrm { i n v } } ^ { e }$ and thus the invariant features are not fully informative. If ${ \mathcal { E } } _ { a l l }$ follows the SEM in Assumption 2 and suppose the distribution of $Z _ { \mathsf { i n v } } ^ { e } , Z _ { \mathsf { s p } \mathsf { \bar { \imath } } } ^ { e }$ can change arbitrarily, then it can be shown that only a classifier identical to the labelling function $1 ( w _ { \mathrm { i n v } } ^ { \ast } \cdot \bar { Z } _ { \mathrm { i n v } } ^ { e } )$ can solve the OOD generalization (eq. (1)); such a classifier achieves an error of q (noise level) in all the environments. As a result, if for a classifier we can find $e \in \mathcal { E } _ { a l l }$ that follows Assumption 2 where the error is greater than $q ,$ then such a classifier does not solve equation (1). Now we ask – what are the minimal conditions on training environments $\mathcal { E } _ { t r }$ to achieve OOD generalization when ${ \mathcal { E } } _ { a l l }$ follow Assumption 2? To achieve OOD generalization for linear regressions, in Theorem 1, it was required that the number of training environments grows linearly in the dimension of the data. However, there was no restriction on the support of the latent invariant and latent spurious features, and they were allowed to change arbitrarily from train to test (for further discussion on this, see the Appendix). Can we continue to work with similar assumptions for the SEM in Assumption 2 and solve the OOD generalization (eq. (1))? We state some assumptions and notations to answer that. Define the support of the invariant (spurious) features $Z _ { \mathrm { i n v } } ^ { e } ( Z _ { \mathsf { s p u } } ^ { e } )$ in environment e as $\mathcal { Z } _ { \mathrm { i n v } } ^ { e } ( \mathcal { Z } _ { \mathsf { s p u } } ^ { e } )$

Assumption 3. Bounded invariantfeatures. $\cup _ { e \in { \mathcal E } _ { t r } } { \mathcal Z } _ { \mathfrak { i n v } } ^ { e }$ is a bounded set.<sup>7</sup>

Assumption 4. Bounded spuriousfeatures. $\cup _ { e \in { \mathcal E } _ { t r } } { \mathcal Z } _ { \mathsf { s p u } } ^ { e }$ is a bounded set.

Assumption 5. Invariant feature support overlap. ∀e $\in \mathcal { E } _ { a l l } , \mathcal { Z } _ { \mathsf { i n v } } ^ { e } \subseteq \cup _ { e ^ { \prime } \in \mathcal { E } _ { t r } } \mathcal { Z } _ { \mathsf { i n v } } ^ { e ^ { \prime } }$

Assumption 6. Spurious feature support overlap. $\forall e \in \mathcal { E } _ { a l l } , \mathcal { Z } _ { \mathsf { s p u } } ^ { e } \subseteq \cup _ { e ^ { \prime } \in \mathcal { E } _ { t r } } \mathcal { Z } _ { \mathsf { s p u } } ^ { e ^ { \prime } }$

Assumption 5 (6) states that the support of the invariant (spurious) features for unseen environments is the same as the union of the support over the training environments. It is important to note that support overlap does not imply that the distribution over the invariant features does not change. We now define a margin that measures how much the is training support of invariant features $Z _ { \mathrm { i n v } } ^ { \overline { { e } } }$ separated by the labelling hyperplane $w _ { \mathrm { i n v } } ^ { \ast }$ . Define Inv- $\begin{array} { r } { \cdot \mathsf { M a r g i n } = \operatorname* { m i n } _ { z \in \cup _ { e \in \mathcal { E } _ { t r } } \mathcal { Z } _ { \mathsf { i n v } } ^ { e } } \mathsf { s g n } \left( w _ { \mathsf { i n v } } ^ { * } \cdot z \right) \left( w _ { \mathsf { i n v } } ^ { * } \cdot z \right) } \end{array}$ . This margin only coincides with the standard margin in support vector machines when the noise level q is 0 (linearly separable) and S is identity. If Inv-Margin > 0, then the labelling hyperplane $w _ { \mathrm { i n v } } ^ { \ast }$ separates the support into two halves (see Figure 1b)).

Assumption 7. Strictly separable invariantfeatures. Inv-Margin $> 0 .$

Next, we show the importance of support overlap for invariant features.

Theorem 2. Impossibility of guaranteed OOD generalization for linear classification. Suppose each $e \in \mathcal { E } _ { a l l }$ follows Assumption 2. If for all the training environments $\mathcal { E } _ { t r } ,$ the latent invariant features are bounded and strictly separable, i.e., Assumption 3 and 7 hold, then every deterministic algorithm fails to solve the OOD generalization (eq. (1)), i.e., for the output of every algorithm ∃ $e \in \mathcal { E } _ { a l l }$ in which the error exceeds the minimum required value q (noise level).

The proofs to all the theorems are in the Appendix. We provide a high-level intuiton as to why invariant feature support overlap is crucial to the impossibility result. In Figure 1b), we show that if the support of latent invariant features are strictly separated by the labelling hyperplane $w _ { \mathrm { i n v } } ^ { \ast } ,$ then we can find another valid hyperplane $w _ { \mathrm { i n v } } ^ { + }$ that is equally likely to have generated the same data. There is no algorithm that can distinguish between $w _ { \mathrm { i n v } } ^ { \ast }$ and $w _ { \mathrm { i n v } } ^ { + }$ . As a result, if we use data from the region where the hyperplanes disagree (yellow region Figure 1b)), then the algorithm fails.

Significance of Theorem 2. We showed that without the support overlap assumption on the invariant features, OOD generalization is impossible for linear classification tasks. This is in contrast to linear regression in Theorem 1 (Arjovsky et al., 2019), where even in the absence of the support overlap assumption, guaranteed OOD generalization was possible. Applying the above Theorem 2 to the 2D case (eq. (4)) implies that we cannot assume that the support of invariant latent features can change, or else that case is also impossible to solve.

Next, we ask what further assumptions are minimally needed to be able to solve the OOD generalization $( \mathrm { e q . } \ ( 1 ) )$ . Each classifier can be written as $\bar { w } \cdot \dot { X ^ { e } } = \bar { w } \cdot S ( Z _ { \mathsf { i n v } } ^ { e } , Z _ { \mathsf { s p u } } ^ { e } ) = \tilde { w } _ { \mathsf { i n v } } \cdot Z _ { \mathsf { i n v } } ^ { e } + \tilde { w } _ { \mathsf { s p u } } Z _ { \mathsf { s p u } } ^ { e } .$ $\mathrm { I f } \tilde { w } _ { \mathsf { s p u } } \neq 0$ , then the classifier w¯ is said to rely on spurious features.

Theorem 3. Sufficiency and Insufficiency of ERM and IRM. Suppose each $\textit { e } \in \mathcal { E } _ { a l l }$ follows Assumption 2. Assume that a) the invariant features are strictly separable, bounded, and satisfy support overlap, b) the spurious features are bounded (Assumptions 3-5, 7 hold).

• Sufficiency: Ifthe spuriousfeatures satisfy support overlap (Assumption 6 holds), then both ERM and IRM solve the OOD generalization problem (eq. (1)). Also, there exist solutions to ERM and IRM solutions that rely on the spurious features and still achieve OOD generalization.

• Insufficiency: If spurious features do not satisfy support overlap, then both ERM and IRM fail at solving the OOD generalization problem (eq. (1)). Also, there exist no such classifiers that rely on spurious features and also achieve OOD generalization.

Significance of Theorem 3. From the first part, we learn that if the support overlap is satisfied for both the invariant features and the spurious features, then either ERM or IRM can solve the OOD generalization (eq. (1)). Interestingly, in this case we can have classifiers that rely on the spurious features and yet solve the OOD generalization (eq. (1)). For the 2D case (eq. (4)) this case implies that the entire set S solves the OOD generalization (eq. (1)). From the second part, we learn that if support overlap holds for invariant features but not for spurious features, then the ideal OOD optimal predictors rely only on the invariant features. In this case, methods like ERM and IRM continue to rely on spurious features and fail at OOD generalization. For the above 2D case (eq. (4)) this implies that only the predictors that rely only on $X _ { \mathrm { i n v } } ^ { e }$ in the set S solve the OOD generalization (eq. (1)).

To summarize, we looked at SEMs for classification tasks when invariant features are fully informative, and find that the support overlap assumption over invariant features is necessary. Even in the presence of support overlap for invariant features, we showed that ERM and IRM can easily fail if the support overlap is violated for spurious features. This raises a natural question – Can we even solve the case with the support overlap assumption only on the invariant features? We will now show that the information bottleneck principle can help tackle these cases.

## 4 Information bottleneck principle meets invariance principle

Why the information bottleneck? The information bottleneck principle prescribes to learn a representation that compresses the input X as much as possible while preserving all the relevant information about the target label Y (Tishby et al., 2000). Mutual information $I ( \breve { X } ; \Phi ( X ) )$ is used to measure information compression. If representation $\Phi ( X )$ is a deterministic transformation of $X ,$ then in principle we can use the entropy of $\Phi ( X )$ to measure compression (Kirsch et al., 2020). Let us revisit the 2D case (eq. (4)) and apply this principle to it. Following the second part of Theorem 3, where ERM and IRM failed, assume that invariant features satisfy the support overlap assumption, but make no such assumption for the spurious features. Consider three choices for Φ: identity (selects both features), selects invariant feature only, selects spurious feature only. The entropy of ${ \dot { H } } ( \Phi ( X ^ { e } ) )$ ) when Φ is the identity is $H ( p ^ { e } ) + \log ( 2 )$ , where $\bar { H ( p ^ { e } ) }$ is the Shannon entropy in Bernoulli $( p ^ { e } )$ . If Φ selects the invariant/spurious features only, then $\tilde { H } ( \Phi ( X ^ { e } ) ) = \log ( 2 )$ . Among all three choices, the one that has the least entropy and also achieves zero error is the representation that focuses on the invariant feature. We could find the OOD optimal predictor in this example just by using information bottleneck. Does it mean the invariance principle isn’t needed? We answer this next.

(a) FIIF (this work)  
![](images/923dc40d34dd68c23b4f20ecc7c0993ab4543fb974a0b1b0c5c48318d862d7b0.jpg)

![](images/d47202061ce305cbb4d1e91dab09cc1a6159d408c4c90e54191d7ab14d484494.jpg)  
(b) PIIF (Arjovsky et al., 2019)

![](images/d7f19a0ea414f006f843f4d44ef787144da6e61f9104263ce65092e6aadb0371.jpg)  
(c) PIIF (Rosenfeld et al., 2021)  
Figure 2: Comparison of the DAG from Assumption 2 (fully informative invariant features) vs. DAGs from Rosenfeld et al. (2021); Arjovsky et al. (2019) (partially informative invariant features).

Why invariance? Consider a simple classification SEM. In each $e \in { \mathcal { E } } _ { t r } , Y ^ { e } \gets X _ { \mathsf { i n v } } ^ { 1 , e } \oplus X _ { \mathsf { i n v } } ^ { 2 , e } \oplus N ^ { e }$ and $X _ { \mathsf { s u } } ^ { e }  Y ^ { e } \oplus V ^ { e }$ , where all the random variables involved are binary valued, noise $N ^ { e } , V ^ { e }$ are Bernoulli with parameters q (identical across $\mathcal { E } _ { t r } ) , c ^ { e }$ (varies across $\mathcal { E } _ { t r } )$ respectively. If $c ^ { e } < q .$ then in $\mathcal { E } _ { t r }$ predictions based on $X _ { \mathsf { s p u } } ^ { e }$ are better than predictions based on $\dot { X } _ { \mathfrak { i n v } } ^ { 1 , e } , X _ { \mathfrak { i n v } } ^ { \bar { 2 } , e }$ . If both $X _ { \mathrm { i n v } } ^ { 1 , e } , X _ { \mathrm { i n v } } ^ { 2 , e }$ are uniform Bernoulli, then these features have a higher entropy than $X _ { \mathsf { s p u } } ^ { e } .$ . In this case, the information bottleneck would bar using $X _ { \mathsf { i n v } } ^ { 1 , e } , X _ { \mathsf { i n v } } ^ { 2 , e }$ . Instead, we want the model to focus on $X _ { \mathsf { i n v } } ^ { 1 , e }$ $X _ { \mathsf { i n v } } ^ { 2 , e }$ and not on $X _ { \mathsf { s p u } } ^ { e }$ . Invariance constraints encourage the model to focus on $X _ { \mathrm { i n v } } ^ { 1 , e } , X _ { \mathrm { i n v } } ^ { 2 , e }$ . In this example, observe that invariant features are partially informative unlike the 2D case (eq. (4)).

Why invariance and information bottleneck? We have illustrated through simple examples when the information bottleneck is needed but not invariance and vice-versa. We now provide a simple example where both these constraints are needed at the same time. This example combines the 2D case (eq. (4)) and the example we highlighted in the paragraph above: $Y ^ { \ ' e } \gets X _ { \mathsf { i n v } } ^ { e } \oplus N ^ { e }$ $X _ { \mathsf { s p u } } ^ { 1 , e } \gets X _ { \mathsf { i n v } } ^ { e } \oplus W ^ { e }$ , and $X _ { \mathsf { s p u } } ^ { 2 , e }  Y ^ { e } \oplus V ^ { \overline { { e } } }$ . In this case, the invariance constraint does not allow representations that use $X _ { \mathsf { s p u } } ^ { 2 , e }$ but does not prohibit representations that rely on $X _ { \mathsf { s p u } } ^ { 1 , e }$ . However, information bottleneck constraints on top ensure that representations that only use $X _ { \mathrm { i n v } } ^ { e }$ are used. We now describe an objective <sup>8</sup> that combines both these principles:

$$
\min _ {w, \Phi} \sum_ {e \in \mathcal {E} _ {t r}} h ^ {e} (w \cdot \Phi) \quad \text {s.t.} \frac {1}{| \mathcal {E} _ {t r} |} \sum_ {e \in \mathcal {E} _ {t r}} R ^ {e} (w \cdot \Phi) \leq r ^ {\mathrm{th}}, w \in \arg \min _ {\tilde {w} \in \mathbb {R} ^ {k \times r}} R ^ {e} (\tilde {w} \cdot \Phi), \forall e \in \mathcal {E} _ {t r},\tag{6}
$$

where $h ^ { e }$ in the above is a lower bounded differential entropy defined below and $r ^ { \mathrm { t h } }$ is the threshold on the average risk. Typical information bottleneck based optimization in neural networks involves minimization of the entropy of the representation output from a certain hidden layer. For both analytical convenience and also because the above setup is a linear model, we work with the simplest form of bottleneck which directly minimizes the entropy of the output layer. Recall the definition of differential entropy of a random variable X, $h ( X ) = - \mathbf { \dot { \mathbb { E } } } _ { X } [ \log d \mathbb { P } _ { X } ]$ and $d \mathbb { P } _ { X }$ is the Radon-Nikodym derivative of $\mathbb { P } _ { X }$ with respect to Lebesgue measure. Because in general differential entropy has no lower bound, we add a small independent noise term ζ (Kirsch et $\mathrm { { a l . } }$ , 2020) to the classifier to ensure that the entropy is bounded below. We call the above optimization information bottleneck based invariant risk minimization (IB-IRM). In summary, among all the highly predictive invariant predictors we pick the ones that have the least entropy. If we drop the invariance constraint from the above optimization, we get information bottleneck based empirical risk minimization (IB-ERM). In the above formulation and following result, we assume that $\dot { X ^ { e } }$ are continuous random variables; the results continue to hold for discrete $X ^ { e }$ as well (See Appendix for details).

## Theorem 4. IB-IRM and IB-ERM vs. IRM and ERM

• Fully informative invariantfeatures (FIIF). Suppose each $e \in \mathcal { E } _ { a l l }$ follows Assumption 2. Assume that the invariant features are strictly separable, bounded, and satisfy support overlap (Assumptions $^ { 3 , 5 }$ and 7 hold). Also, for each $e \in \bar { \mathcal { E } } _ { t r } Z _ { \mathsf { s p u } } ^ { e }  A Z _ { \mathsf { i n v } } ^ { e } + W ^ { e }$ , where $\mathbf { \bar { A } } \in \mathbb { R } ^ { o \times \hat { m } } , \ W ^ { e } \in \mathbf { \bar { R } } ^ { o }$ is continuous, bounded, and zero mean noise. Each solution to IB-IRM (eq. (6), with \` as 0-1 loss, and $r ^ { \mathsf { t h } } = q )$ , and IB-ERM solves the OOD generalization (eq. (1)) but ERM and IRM (eq.(3))fail.

• Partially informative invariantfeatures (PIIF). Suppose each $e \in \mathcal { E } _ { a l l }$ follows Assumption 1 and $\exists \ e \in { \mathcal { E } } _ { t r }$ such that $\mathbb { E } [ \epsilon ^ { e } Z _ { \mathsf { s p u } } ^ { e } ] \neq 0 . \ I f \left| \mathcal { E } _ { t r } \right| > 2 d$ and the set $\mathcal { E } _ { t r }$ lies in a linear general position (a mild condition defined in the Appendix), then each solution to IB-IRM (eq. (6), with \` as square loss, $\sigma _ { \epsilon } ^ { 2 } < r ^ { \mathsf { t h } } \le \sigma _ { Y } ^ { 2 }$ , where $\sigma _ { Y } ^ { 2 }$ and $\sigma _ { \epsilon } ^ { 2 }$ are the variance in the label and noise across $\mathcal { E } _ { t r } )$ and IRM $( e q . ( 3 ) )$ solves OOD generalization (eq. (1)) but IB-ERM and ERMfail.

Significance of Theorem 4 and remarks. In the first part (FIIF), IB-ERM and IB-IRM succeed without assuming support overlap for the spurious features, which was crucial for success of ERM and IRM in Theorem 3. This establishes that support overlap of spurious features is not a necessary condition. Observe that when invariant features are fully informative, IB-ERM and IB-IRM succeed, but when invariant features are partially informative IB-IRM and IRM succeed. In real data settings, we do not know if the invariant features are fully or partially informative. Since IB-IRM is the only common winner in both the settings, it would be pragmatic to use it in the absence of domain knowledge about the informativeness of the invariant features. In the paragraph preceding the objective in equation (6), we discussed examples where both the IB and IRM constraints were needed at the same time. In the Appendix, we generalize that example and show that if we change the assumptions in linear classification SEM in Assumption 2 such that the invariant features are partially informative, then we see the joint benefit of IB and IRM constraints. At this point, it is also worth pointing to a result in Rosenfeld et al. (2021), which focused on linear classification SEMs (DAG shown in Figure 2c) with partially informative invariant features. Under the assumption of complete support overlap for spurious and invariant features, authors showed IRM succeeds.

## 4.1 Proposed approach

We take the three terms from the optimization in equation (6) and create a weighted combination as

$$
\sum_ {e} \Big (R ^ {e} (\Phi) + \lambda \| \nabla_ {w, w = 1. 0} R ^ {e} (w \cdot \Phi) \| ^ {2} + \nu h ^ {e} (\Phi) \Big) \leq \sum_ {e} \Big (R ^ {e} (\Phi) + \lambda \| \nabla_ {w, w = 1. 0} R ^ {e} (w \cdot \Phi) \| ^ {2} + \nu h (\Phi) \Big).
$$

In the LHS above, the first term corresponds to the risks across environments, the second term approximates invariance constraint (follows the IRMv1 objective (Arjovsky et al., 2019)), and the third term is the entropy of the classifier in each environment.

In the RHS, h(Φ) is the entropy of Φ unconditional on the environment (the entropy on the left-hand side is entropy conditional on the environment assuming all the environments are equally likely). Optimizing over differential entropy is not easy, and thus we resort to minimizing an upper bound of it (Kirsch et al., 2020). We use the standard result that among all continuous random variables with the same variance, Gaussian has the maximum differential entropy. Since the entropy of Gaussian increases with its variance, we use the variance of Φ instead of the differential entropy (For further details, see the Appendix). Our final objective is given as

![](images/b66a29fb272e834ee692193ccb47adc6dca7d41b773b8e03e78b7337b8885098.jpg)  
Figure 3: Comparing convergence of $\frac { \lvert w _ { \mathsf { s p u } } \rvert } { \sqrt { w _ { \mathsf { s p u } } ^ { 2 } + w _ { \mathsf { i n v } } ^ { 2 } } }$ (metric from Nagarajan et al. (2021)) for average selection bias $p = 0 . 9$

$$
\sum_ {e} \Big (R ^ {e} (\Phi) + \lambda \| \nabla_ {w, w = 1. 0} R ^ {e} (w \cdot \Phi) \| ^ {2} + \gamma \mathsf {V a r} (\Phi) \Big).\tag{7}
$$

On the behavior of gradient descent with and without informa-

tion bottleneck. In the entire discussion so far, we have focused on ensuring that the set of optimal solutions to the desired objective (IB-IRM, IB-ERM, etc.) correspond to the solutions of the OOD generalization problem (eq. (1)). In some simple cases, such as the 2D case (eq. (4)), it can be shown that gradient descent is biased towards selecting the ideal classifier (Soudry et al., 2018; Nagarajan et al., 2021). Even though gradient descent can eventually learn the ideal classifier that only relies on the invariant features, training is frustratingly slow as was shown by Nagarajan et al. (2021). In the next theorem, we characterize the impact of using IB penalty $( \mathsf { V a r } ( \Phi ) )$ in the 2D example (eq. (4)). We compare the methods in terms of $| \frac { w _ { \mathsf { s p u } } ( t ) } { w _ { \mathsf { i n v } } ( t ) }$ |, which was the metric used in Nagarajan et al. (2021); $w _ { \mathsf { s p u } } ( t )$ and $w _ { \mathsf { i n v } } ( t )$ are the weights for the spurious feature and the invariant feature at time t of training (assuming training happens with continuous time gradient descent).

Theorem 5. Impact of IB on learning speed. Suppose each $\textit { e } \in \mathcal { E } _ { t r }$ follows the 2D case from equation (4). Set $\lambda = 0 , \gamma > 0$ in equation (7) to get the IB-ERM objective with \` as exponential loss. Continuous-time gradient descent on this IB-ERM objective achieves $| \frac { w _ { \mathsf { s p u } } ( t ) } { w _ { \mathsf { i n v } } ( t ) } | \leq \epsilon$ in time less than $\frac { W _ { 0 } ( \frac { 1 } { 2 \gamma } ) } { 2 ( 1 - p ) \epsilon } \ : ( W _ { 0 } ( \cdot )$ denotes the principal branch ofthe Lambert W function), while in the same time the ratio for $\begin{array} { r } { E R M | \frac { w _ { \mathrm { s p u } } ( t ) } { w _ { \mathrm { i n v } } ( t ) } | \geq \ln ( \frac { 1 + 2 p } { 3 - 2 p } ) / \ln \big ( 1 + \frac { W _ { 0 } ( \frac { 1 } { 2 \gamma } ) } { 2 ( 1 - p ) \epsilon } \big ) } \end{array}$ , where $\begin{array} { r } { p = \frac { 1 } { \left| \mathcal { E } _ { t r } \right| } \sum _ { e \in \mathcal { E } _ { t r } } p ^ { e } } \end{array}$

$| \frac { w _ { \mathsf { s p u } } ( t ) } { w _ { \mathsf { i n v } } ( t ) } |$ converges to zero for both methods, but it converges much faster for IB-ERM (for $p =$ $0 . 9 , \epsilon = 0 . 0 0 1 , \gamma = 0 . 5 8$ , the ratio for IB-ERM is $| \frac { w _ { \mathsf { s p u } } ( t ) } { w _ { \mathsf { i n v } } ( t ) } | \leq 0 . 0 0 1$ and ratio for ERM is $| \frac { w _ { \mathsf { s p u } } ( t ) } { w _ { \mathsf { i n v } } ( t ) } | \geq$ 0.09). In the above theorem, we analyzed the impact of information bottleneck only. The convergence analysis for both the penalties jointly comes with its own challenges, and we hope to explore this in future work. However, we carried out experiments with gradient descent on all the objectives for the 2D example (eq. (4)). See Figure 3 for the comparisons.

## 5 Experiments

Methods, datasets & metrics. We compare our approaches – information bottleneck based ERM (IB-ERM) and information bottleneck based IRM (IB-IRM) with ERM and IRM. We also compare with an Oracle model trained on data where spurious features are permuted to remove spurious correlations. We use all the datasets in Table 2, Terra Incognita dataset (Beery et al., 2018), and COCO (Ahmed et al., 2021). We follow the same protocol for tuning hyperparameters from Aubin et al. (2021); Arjovsky et al. (2019) for their respective datasets (see the Appendix for more details). As is reported in literature, for Example 2/2S, Example 3/3S we use classification error and for AC-CMNIST, CS-CMNIST, Terra Incognita, and COCO we use accuracy. For Example 1/1S, we use mean square error (MSE). The code for experiments can be found at https://github.com/ahujak/IB-IRM.

Summary of results. In Table 3, we provide a comparison of methods for different examples in linear unit tests (Aubin et al., 2021) for three and six training environments. In Table 4, we provide a comparison of the methods for different CMNIST datasets, Terra Incognita and COCO dataset. Based on our Theorem 4, we do not expect ERM and IB-ERM to do well on Example 1/1S, Example 3/3S and AC-CMNIST as these datasets fall in the PIIF category, i.e, the invariant features are partially informative. On these examples, we find that IRM and IB-IRM do better than ERM and IB-ERM (for Example 3/3S when there are three environments all methods perform poorly). Based on our Theorem 4, we do not expect IRM and ERM to do well on Example 2/2S, CS-CMNIST, Terra Incognita and COCO dataset,<sup>9</sup> as these datasets fall in the FIIF category, i.e., the invariant features are fully informative. On these FIIF examples, we find that IB-ERM always performs well (close to oracle), and in some cases IB-IRM also performs well. Our experiments confirm that IB penalty has a crucial role to play in FIIF settings and IRMv1 penalty has a crucial role to play in PIIF settings (to further this claim, we provide an ablation study in the Appendix). On Example 1/1S, AC-CMNIST, we find that IB-IRM is able to extract the benefit of IRMv1 penalty. On CS-CMNIST and Example 2/2S we find that IB-IRM is able to extract the benefit of IB penalty. In settings such as COCO dataset, where IB-IRM does not perform as well as IB-ERM, better hyperparameter tuning strategies should be able to help IB-IRM adapt and put a higher weight on IB penalty. Overall, we can conclude that IB-ERM improves over ERM (significantly in FIIF and marginally in PIIF settings), and IB-IRM improves over IRM (improves in FIIF settings and retains advantages in PIIF settings).

Remark. As we move from three to six environments, we observe that MSE in Example 1/1S exhibits a larger variance. This is because of the way data is generated, the new environments that are sampled have labels that have a higher noise level (we follow the same procedure as in Aubin et al. (2021)).

## 6 Extensions, limitations, and future work

Extension to non-linear models and multi-class classification. In this work our theoretical analysis focused on linear models. Consider the map $X  S ( Z _ { \mathsf { i n v } } , Z _ { \mathsf { s p u } } )$ in Assumption 2. Suppose S is non-linear and bijective. We can divide the learning task into two parts a) invert S to obtain $\bar { Z } _ { \mathrm { i n v } } , Z _ { \mathsf { s p u } }$ and b) learn a linear model that only relies on the invariant features $Z _ { \mathrm { i n v } }$ to predict the label Y. For part b), we can rely on the approaches proposed in this work. For part a), we need to leverage advancements in the field of non-linear ICA (Khemakhem et al., 2020). The current state-of-the-art to solve part a) requires strong structural assumptions on the dependence between all the components of $Z _ { \mathrm { i n v } } , \dot { Z } _ { \mathsf { s p u } }$ (Lu et al., 2021). Therefore, solving part a) and part b) in conjunction with minimal assumptions forms an exciting future work. In the entire work, the discussion was focused on binary classification tasks and regression tasks. For multi-class classification settings, we consider natural extension of the SEM in Assumption 2 (See the Appendix) and our main results continue to hold.

<table><tr><td></td><td>#Envs</td><td>ERM</td><td>IB-ERM</td><td>IRM</td><td>IB-IRM</td><td>Oracle</td></tr><tr><td>Example1</td><td>3</td><td> $13.36 \pm 1.49$ </td><td> $12.96 \pm 1.30$ </td><td> $11.15 \pm 0.71$ </td><td> $11.68 \pm 0.90$ </td><td> $10.42 \pm 0.16$ </td></tr><tr><td>Example1s</td><td>3</td><td> $13.33 \pm 1.49$ </td><td> $12.92 \pm 1.30$ </td><td> $11.07 \pm 0.68$ </td><td> $11.74 \pm 1.03$ </td><td> $10.45 \pm 0.19$ </td></tr><tr><td>Example2</td><td>3</td><td> $0.42 \pm 0.01$ </td><td> $0.00 \pm 0.00$ </td><td> $0.45 \pm 0.00$ </td><td> $0.00 \pm 0.00$ </td><td> $0.00 \pm 0.00$ </td></tr><tr><td>Example2s</td><td>3</td><td> $0.45 \pm 0.01$ </td><td> $0.00 \pm 0.01$ </td><td> $0.45 \pm 0.01$ </td><td> $0.06 \pm 0.12$ </td><td> $0.00 \pm 0.00$ </td></tr><tr><td>Example3</td><td>3</td><td> $0.48 \pm 0.07$ </td><td> $0.49 \pm 0.06$ </td><td> $0.48 \pm 0.07$ </td><td> $0.48 \pm 0.07$ </td><td> $0.01 \pm 0.00$ </td></tr><tr><td>Example3s</td><td>3</td><td> $0.49 \pm 0.06$ </td><td> $0.49 \pm 0.06$ </td><td> $0.49 \pm 0.07$ </td><td> $0.49 \pm 0.07$ </td><td> $0.01 \pm 0.00$ </td></tr><tr><td>Example1</td><td>6</td><td> $33.74 \pm 60.18$ </td><td> $32.03 \pm 57.05$ </td><td> $23.04 \pm 40.64$ </td><td> $25.66 \pm 45.96$ </td><td> $22.21 \pm 39.25$ </td></tr><tr><td>Example1s</td><td>6</td><td> $33.62 \pm 59.80$ </td><td> $31.92 \pm 56.70$ </td><td> $22.92 \pm 40.60$ </td><td> $25.60 \pm 45.62$ </td><td> $22.13 \pm 38.93$ </td></tr><tr><td>Example2</td><td>6</td><td> $0.37 \pm 0.06$ </td><td> $0.02 \pm 0.05$ </td><td> $0.46 \pm 0.01$ </td><td> $0.43 \pm 0.11$ </td><td> $0.00 \pm 0.00$ </td></tr><tr><td>Example2s</td><td>6</td><td> $0.46 \pm 0.01$ </td><td> $0.02 \pm 0.06$ </td><td> $0.46 \pm 0.01$ </td><td> $0.45 \pm 0.10$ </td><td> $0.00 \pm 0.00$ </td></tr><tr><td>Example3</td><td>6</td><td> $0.33 \pm 0.18$ </td><td> $0.26 \pm 0.20$ </td><td> $0.14 \pm 0.18$ </td><td> $0.19 \pm 0.19$ </td><td> $0.01 \pm 0.00$ </td></tr><tr><td>Example3s</td><td>6</td><td> $0.36 \pm 0.19$ </td><td> $0.27 \pm 0.20$ </td><td> $0.14 \pm 0.18$ </td><td> $0.19 \pm 0.19$ </td><td> $0.01 \pm 0.00$ </td></tr></table>

Table 3: Comparisons on linear unit tests in terms of mean square error (regression) and classification error (classification). “#Envs” means the number of training environments.

<table><tr><td></td><td>ERM</td><td>IB-ERM</td><td>IRM</td><td>IB-IRM</td></tr><tr><td>CS-CMNIST</td><td>60.27 ± 1.21</td><td>71.80 ± 0.69</td><td>61.49 ± 1.45</td><td>71.79 ± 0.70</td></tr><tr><td>AC-CMNIST</td><td>16.84 ± 0.82</td><td>50.24 ± 0.47</td><td>66.98 ± 1.65</td><td>67.67 ± 1.78</td></tr><tr><td>Terra Incognita</td><td>49.80 ± 4.40</td><td>56.40 ± 2.10</td><td>54.60 ± 1.30</td><td>54.10 ± 2.00</td></tr><tr><td>COCO</td><td>22.70 ± 1.04</td><td>31.66 ± 2.39</td><td>18.47 ± 10.20</td><td>25.10 ± 1.03</td></tr></table>

Table 4: Classification accuracy percentage on colored MNISTs, Terra Incognita and COCO dataset.

On the choice for IB penalty and IRMv1 penalty. We use the approximation for entropy (in equation (7)) described in Kirsch et al. (2020). The approximation (even though an upper bound) serves as an effective proxy for the true information bottleneck as shown in the experiments in Kirsch et al. (2020) (e.g., see their experiment on Imagenette dataset). Also, our experiments validate this approximation even in moderately high dimensions, as an example in CS-CMNIST, the dimension of the layer at which bottleneck constraints are applied is 256. Developing tighter approximations for information bottleneck in high dimensions and analyzing their impact on OOD generalization is an important future work. In recent works (Rosenfeld et al., 2021; Kamath et al., 2021; Gulrajani and Lopez-Paz, 2021), there has been criticism of different aspects of IRM, e.g., failure of IRMv1 penalty in non-linear models, the tuning of IRMv1 penalty, etc. Since we use IRMv1 penalty in our proposed loss, these criticisms apply to our objective as well. Other approximations of invariance have been proposed in the literature (Koyama and Yamaguchi, 2020; Ahuja et al., 2020; Chang et al., 2020). Exploring their benefits together with information bottleneck is a fruitful future work. Before concluding, we want to remark that we have already discussed the closest related works. However, we also provide a detailed discussion of the broader related literature in the Appendix.

## 7 Conclusion

In this work, we revisited the fundamental assumptions for OOD generalization for settings when invariant features capture all the information about the label. We showed how linear classification tasks are different and need much stronger assumptions than linear regression tasks. We provide a sharp characterization of performance of ERM and IRM under different assumptions on support overlap of invariant and spurious features. We showed that support overlap of invariant features is necessary or otherwise OOD generalization is impossible. However, ERM and IRM seem to fail even in the absence of support overlap of spurious features. We prove that a form of the information bottleneck constraint along with invariance goes a long way in overcoming the failures while retaining the existing provable guarantees.

## Acknowledgements

We thank Reyhane Askari Hemmat, Adam Ibrahim, Alexia Jolicoeur-Martineau, Divyat Mahajan, Ryan D’Orazio, Nicolas Loizou, Manuela Girotti, and Charles Guille-Escuret for the feedback. Kartik Ahuja would also like to thank Karthikeyan Shanmugam for discussions pertaining to the related works.

## Funding disclosure

We would like to thank Samsung Electronics Co., Ldt. for funding this research. Kartik Ahuja acknowledges the support provided by IVADO postdoctoral fellowship funding program. Yoshua Bengio acknowledges the support from CIFAR and IBM. Ioannis Mitliagkas acknowledges support from an NSERC Discovery grant (RGPIN-2019-06512), a Samsung grant, Canada CIFAR AI chair and MSR collaborative research grant. Irina Rish acknowledges the support from Canada CIFAR AI Chair Program and from the Canada Excellence Research Chairs Program. We thank Compute Canada for providing computational resources.

## References

Ahmed, F., Bengio, Y., van Seijen, H., and Courville, A. (2021). Systematic generalisation with group invariant predictions. In International Conference on Learning Representations.

Ahuja, K., Shanmugam, K., Varshney, K., and Dhurandhar, A. (2020). Invariant risk minimization games. In International Conference on Machine Learning, pages 145–155. PMLR.

Ahuja, K., Wang, J., Dhurandhar, A., Shanmugam, K., and Varshney, K. R. (2021). Empirical or invariant risk minimization? a sample complexity perspective. In International Conference on Learning Representations.

Arjovsky, M., Bottou, L., Gulrajani, I., and Lopez-Paz, D. (2019). Invariant risk minimization. arXiv preprint arXiv:1907.02893.

Aubin, B., Słowik, A., Arjovsky, M., Bottou, L., and Lopez-Paz, D. (2021). Linear unit-tests for invariance discovery. arXiv preprint arXiv:2102.10867.

Beery, S., Van Horn, G., and Perona, P. (2018). Recognition in terra incognita. In Proceedings of the European Conference on Computer Vision, pages 456–473.

Chang, S., Zhang, Y., Yu, M., and Jaakkola, T. S. (2020). Invariant rationalization. In International Conference on Machine Learning, 2020.

DeGrave, A. J., Janizek, J. D., and Lee, S.-I. (2020). AI for radiographic COVID-19 detection selects shortcuts over signal. medRxiv.

Geirhos, R., Jacobsen, J.-H., Michaelis, C., Zemel, R., Brendel, W., Bethge, M., and Wichmann, F. A. (2020). Shortcut learning in deep neural networks. Nature Machine Intelligence, 2(11):665–673.

Gulrajani, I. and Lopez-Paz, D. (2021). In search of lost domain generalization. In International Conference on Learning Representations.

Kamath, P., Tangella, A., Sutherland, D. J., and Srebro, N. (2021). Does invariant risk minimization capture invariance? arXiv preprint arXiv:2101.01134.

Khemakhem, I., Kingma, D., Monti, R., and Hyvarinen, A. (2020). Variational autoencoders and nonlinear ica: A unifying framework. In International Conference on Artificial Intelligence and Statistics, pages 2207–2217. PMLR.

Kirsch, A., Lyle, C., and Gal, Y. (2020). Unpacking information bottlenecks: Unifying informationtheoretic objectives in deep learning. arXiv preprint arXiv:2003.12537.

Koyama, M. and Yamaguchi, S. (2020). Out-of-distribution generalization with maximal invariant predictor. arXiv preprint arXiv:2008.01883.

Krueger, D., Caballero, E., Jacobsen, J.-H., Zhang, A., Binas, J., Zhang, D., Priol, R. L., and Courville, A. (2020). Out-of-distribution generalization via risk extrapolation (rex). arXiv preprint arXiv:2003.00688.

Lu, C., Wu, Y., Hernández-Lobato, J. M., and Schölkopf, B. (2021). Nonlinear invariant risk minimization: A causal approach. arXiv preprint arXiv:2102.12353.

Nagarajan, V., Andreassen, A., and Neyshabur, B. (2021). Understanding the failure modes of out-of-distribution generalization. In International Conference on Learning Representations.

Pearl, J. (1995). Causal diagrams for empirical research. Biometrika, 82(4):669–688.

Peters, J., Bühlmann, P., and Meinshausen, N. (2015). Causal inference using invariant prediction: identification and confidence intervals. arXiv preprint arXiv:1501.01332.

Pezeshki, M., Kaba, S.-O., Bengio, Y., Courville, A., Precup, D., and Lajoie, G. (2020). Gradient starvation: A learning proclivity in neural networks. arXiv preprint arXiv:2011.09468.

Robey, A., Pappas, G. J., and Hassani, H. (2021). Model-based domain generalization. arXiv preprint arXiv:2102.11436.

Rojas-Carulla, M., Schölkopf, B., Turner, R., and Peters, J. (2018). Invariant models for causal transfer learning. The Journal ofMachine Learning Research, 19(1):1309–1342.

Rosenfeld, E., Ravikumar, P. K., and Risteski, A. (2021). The risks of invariant risk minimization. In International Conference on Learning Representations.

Soudry, D., Hoffer, E., Nacson, M. S., Gunasekar, S., and Srebro, N. (2018). The implicit bias of gradient descent on separable data. The Journal ofMachine Learning Research, 19(1):2822–2878.

Tishby, N., Pereira, F. C., and Bialek, W. (2000). The information bottleneck method. arXiv preprint physics/0004057.

Vapnik, V. (1992). Principles of risk minimization for learning theory. In Advances in neural information processing systems, pages 831–838.

Zhang, D., Ahuja, K., Xu, Y., Wang, Y., and Courville, A. C. (2021). Can subnetwork structure be the key to out-of-distribution generalization? In ICML.

## Checklist

1. For all authors...

(a) Do the main claims made in the abstract and introduction accurately reflect the paper’s contributions and scope? [Yes] See Section 2-5 and the additional details such as the proofs in the supplementary material.

(b) Did you describe the limitations of your work? [Yes] See Section 4.1 and Section 6.

(c) Did you discuss any potential negative societal impacts of your work? [Yes] See Section A.1 in the Appendix in the supplementary material.

(d) Have you read the ethics review guidelines and ensured that your paper conforms to them? [Yes]

2. If you are including theoretical results...

(a) Did you state the full set of assumptions of all theoretical results? [Yes] See Section 2-4.

(b) Did you include complete proofs of all theoretical results? [Yes] See the Appendix in the Supplementary Material.

3. If you ran experiments...

(a) Did you include the code, data, and instructions needed to reproduce the main experimental results (either in the supplemental material or as a URL)? [Yes] See https://github.com/ahujak/IB-IRM

(b) Did you specify all the training details (e.g., data splits, hyperparameters, how they were chosen)? [Yes] See Section A.2 in the Appendix in the supplementary material.

(c) Did you report error bars (e.g., with respect to the random seed after running experiments multiple times)? [Yes] See Section A.2 in the Appendix in the supplementary material.

(d) Did you include the total amount of compute and the type of resources used (e.g., type of GPUs, internal cluster, or cloud provider)? [Yes] See Section A.2 in the Appendix in the supplementary material.

4. If you are using existing assets (e.g., code, data, models) or curating/releasing new assets...

(a) If your work uses existing assets, did you cite the creators? [Yes] We use the codes from following github repositories https://github.com/ facebookresearch/DomainBed, https://github.com/facebookresearch/ InvariantRiskMinimization and https://github.com/facebookresearch/ InvarianceUnitTests and we have cited the creators in the Section A.2 in the Appendix in the supplementary material.

(b) Did you mention the license of the assets? [Yes] All the repositories mentioned above use MIT license. We have mentioned this in Section A.2 in the Appendix in the supplementary material.

(c) Did you include any new assets either in the supplemental material or as a URL? [Yes] We have included code for our experiments in the supplementary material.

(d) Did you discuss whether and how consent was obtained from people whose data you’re using/curating? [N/A]

(e) Did you discuss whether the data you are using/curating contains personally identifiable information or offensive content? [N/A]

5. If you used crowdsourcing or conducted research with human subjects...

(a) Did you include the full text of instructions given to participants and screenshots, if applicable? [N/A]

(b) Did you describe any potential participant risks, with links to Institutional Review Board (IRB) approvals, if applicable? [N/A]

(c) Did you include the estimated hourly wage paid to participants and the total amount spent on participant compensation? [N/A]