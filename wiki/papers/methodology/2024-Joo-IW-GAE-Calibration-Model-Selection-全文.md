---
title: "2024-Joo-IW-GAE-Calibration-Model-Selection"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2024-Joo-IW-GAE-Calibration-Model-Selection.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# IW-GAE: Importance Weighted Group Accuracy Estimation for Improved Calibration and Model Selection in Unsupervised Domain Adaptation

Taejong Joo <sup>1</sup> Diego Klabjan <sup>1</sup>

## Abstract

Distribution shifts pose significant challenges for model calibration and model selection tasks in the unsupervised domain adaptation problem—a scenario where the goal is to perform well in a distribution shifted domain without labels. In this work, we tackle difficulties coming from distribution shifts by developing a novel importance weighted group accuracy estimator. Specifically, we present a new perspective of addressing the model calibration and model selection tasks by estimating the group accuracy. Then, we formulate an optimization problem for finding an importance weight that leads to an accurate group accuracy estimation with theoretical analyses. Our extensive experiments show that our approach improves state-of-the-art performances by 22% in the model calibration task and 14% in the model selection task.

## 1. Introduction

In this work, we consider a classification problem in unsupervised domain adaptation (UDA). UDA aims to transfer knowledge from a source domain with ample labeled data to enhance the performance in a target domain where labeled data is unavailable. In UDA, the source and target domains have different data generating distributions, so the core challenge is to transfer knowledge contained in the labeled dataset in the source domain to the target domain under the distribution shifts. Over the decades, significant improvements in the transferability of accuracy from source to target domains have been made, resulting in areas like domain alignment (Ben-David et al., 2010; Zhang et al., 2019) and self-training (Chen et al., 2020; Cai et al., 2021).

However, model calibration, which is about matching prediction confidence on a sample to its expected accuracy (Dawid, 1982; Guo et al., 2017), remains challenging in UDA due to the distribution shifts. Specifically, it is widely known that state-of-the-art calibrated classifiers in the independent and identically distributed (i.i.d.) settings (Guo et al., 2017; Gal & Ghahramani, 2016; Lakshminarayanan et al., 2017) begin to generate over-confident predictions in the face of distributional shifts (Ovadia et al., 2019). Further, Wang et al. (2020) show the discernible compromise in calibration performance as an offset against the enhancement of the accuracy in the target domain.

Moreover, the model selection task in UDA remains challenging due to the scarcity of labeled target domain data that are required to evaluate model performance. In the i.i.d. settings, a standard approach for model selection is a cross-validation method—constructing a hold-out dataset for selecting the model that yields the best performance on the hold-out dataset. While cross-validation provides favorable statistical guarantees (Stone, 1977; Kohavi et al., 1995), such guarantees falter in the presence of the distribution shifts due to the violation of the i.i.d. assumption. In practice, it has also been observed that performances of machine learning models measured in one domain have significant discrepancies to their performances in another distribution shifted domain (Hendrycks & Dietterich, 2019; Ovadia et al., 2019; Recht et al., 2019). Therefore, applying model selection techniques in the i.i.d. settings to the labeled source domain is suboptimal in the target domain.

In this work, we simultaneously address these critical aspects in UDA from a new perspective of predicting a group accuracy. Specifically, we partition predictions into a set of groups and then estimate the group accuracy—the average accuracy of predictions in a group. When the group accuracy estimate accurately represents the expected accuracy of a model for samples in the group (e.g., group 1 in Figure 1(a)), using the group accuracy estimate as prediction confidence induces a well-calibrated classifier. When the average of the group accuracy estimates matches the mean expected accuracy (e.g., two dotted lines in Figure 1(a) are close to each other), it becomes a good model selection criterion.

![](images/e87448bcef0f6d3b893b5ce3d7addda015e83b147ecbcbca9358d1545b37e00a.jpg)  
(a)

![](images/4487424839e5b71436a40d7d1f2be5172fa7c444f52d0742f1aeffb86e5b8347.jpg)  
(b)  
Figure 1. Figure 1(a) illustrates ideal and failure cases of IW-GAE with nine data points (red diamonds) from three groups (gray boxes). Group 1 is desirable for model calibration where the group accuracy estimation (a blue rectangle) well represents the individual expected accuracies of samples in the group. Conversely, group accuracy estimation could inaccurately represent the individual accuracies in the group due to a high variance of accuracies within the group (group 2) and a high bias of the estimator (group 3). For model selection, we aim to match the mean group accuracy estimation (the blue dotted line as an average of blue rectangles) to the mean expected accuracy (the red dotted line as an average of red diamonds), which can be induced by accurate group accuracy estimations for each group. Figure 1(b) explains the idea of encouraging two estimators close to each other. The shaded area for the IW-based estimator is possible group accuracy estimations from different IWs. IW-GAE finds the IW minimizing the opt error for reducing the group accuracy estimation error.

To this end, we propose importance weighted group accuracy estimation (IW-GAE) that aims to find importance weights (IWs) that induce an accurate group accuracy estimator under the distribution shifts. Specifically, we define two estimators for the group accuracy in the source domain (MC-based and IW-based estimators in Figure 1(b)), where only one of them depends on the IW. Then, we formulate a novel optimization problem for finding the IW that makes the two estimators close to each other (reducing opt error in Figure 1(b)). Through theoretical analyses and several experiments, we show that the optimization process results in an accurate group accuracy estimator for the target domain (small quantity of interest in Figure 1(b)), improving model calibration and model selection performances.

Our contributions can be summarized as follows: 1) We show when and why considering group accuracy, instead of the accuracy for individual samples, is statistically favorable, which can simultaneously benefit model calibration and model selection with attractive properties; 2) We propose a novel optimization problem for IW estimation that directly reduces group accuracy estimation error in UDA with theoretical analyses; 3) On average, IW-GAE improves state-of-the-art performances by 22% in the model calibration task and 14% in the model selection task.

Notation and problem setup Let $\mathcal { X } \subseteq \mathbb { R } ^ { r }$ and $\mathcal { V } = [ K ] : =$ $\{ 1 , 2 , \cdots , K \}$ be input and label spaces. Let ${ \hat { Y } } : { \mathcal { X } }  [ K ]$ be the prediction function of a model and $Y ( x )$ is a $K \mathfrak { - }$ dimensional categorical random variable related to a label at $X = x$ . When there is no ambiguity, we represent $Y ( x )$ and $\hat { Y } ( x )$ as Y and Y<sup>ˆ</sup> for brevity. We are given a labeled source dataset $\mathcal { D } _ { S } = \{ ( x _ { i } ^ { ( S ) } , y _ { i } ^ { ( S ) } ) \} _ { i = 1 } ^ { N ^ { ( S ) } }$ sampled from $p _ { S _ { X Y } }$ and an unlabeled target dataset $\mathcal { D } _ { T } = \{ x _ { i } ^ { ( T ) } \} _ { i \in [ N ^ { ( T ) } ] }$ sampled from $p _ { T _ { \lambda } }$ <sub>X</sub> where $p _ { S _ { X } } .$ is a joint data generating distribution of the source domain and $p _ { T _ { \lambda } }$ is a marginal distribution of the target domain. We also denote $\mathbb { E } _ { p } [ \cdot ]$ as the population expectation and $\hat { \mathbb { E } } _ { p } [ \cdot ]$ as its empirical counterpart. For $p _ { S _ { X Y } }$ and $p _ { T _ { X Y } }$ , we consider a covariate shift without a concept shift; i.e., $, p _ { S _ { X } } ( x ) \neq p _ { T _ { X } } ( x )$ but $p _ { S _ { Y | X } } ( y | x ) = p _ { T _ { Y | X } } ( y | x )$ for $x \in \mathcal { X }$ . For the rest of the paper, we use the same notation $p _ { S }$ for marginal distribution $p _ { S _ { X } }$ and joint distribution $p _ { S _ { X Y } }$ when there is no ambiguity. However, we use the explicit notation for $p _ { S _ { Y \mid X } }$ and $p _ { T _ { Y \mid X } }$ to avoid confusion.

## 2. Group Accuracy Estimation for Model Calibration and Selection

We address model calibration and model selection tasks in UDA by estimating the group accuracy. Specifically, we construct M groups $\{ { \mathcal { G } } _ { n } \} _ { n \in [ M ] }$ with some grouping function $I ^ { ( g ) } : \mathcal { X }  [ M ]$ Then, for each group ${ \mathcal { G } } _ { n } .$ we estimate the average accuracy of target domain samples in ${ \mathcal { G } } _ { n }$ defined as $\alpha _ { T } ( \mathcal { G } _ { n } ) : = \mathbb { E } _ { p _ { T } } [ \mathbf { 1 } ( Y ( X ) = \hat { Y } ( X ) ) | \mathcal { G } _ { n } ]$ . In the following, we first give a motivation for estimating the group accuracy, instead of an expected accuracy for each sample. Then, we explain how to construct groups and use the group accuracy estimates for simultaneously solving model calibration and selection tasks.

## 2.1. Motivation for Estimating the Group Accuracy

Suppose we are given samples $D : = \{ ( x _ { i } , y _ { i } ) \in \mathcal { G } _ { n } \} _ { i \in [ N _ { n } ] }$ and a classifier f. Let $\beta ( x _ { i } ) \ : = \ \mathbb { E } _ { Y \mid X = x _ { i } } [ \mathbf { 1 } ( Y ( x _ { i } ) \ =$ $f ( x _ { i } ) ) ]$ be an expected accuracy of $f$ at $x _ { i } ,$ which is our goal to estimate. Then, due to realization of a single label at each point, the observed accuracy ${ \hat { \beta } } ( x _ { i } ) : = \mathbf { 1 } ( y _ { i } = f ( x _ { i } ) )$ is a random sample from the Bernoulli distribution with parameter $\beta ( x _ { i } )$ that has a variance of $\sigma _ { x _ { i } } ^ { 2 } = \beta ( x _ { i } ) ( 1 - \beta ( x _ { i } ) )$ . Note that this holds when $x _ { i } \neq x _ { j }$ for $i \neq j$ , which is the case for most machine learning scenarios.

Under this setting, we show the sufficient condition that the maximum likelihood estimator (MLE) of the group accuracy outperforms the MLE of the individual accuracy.

Proposition 2.1. Let $\hat { \beta } ^ { ( i d ) }$ and $\hat { \boldsymbol { \beta } } ^ { ( g r ) }$ be MLEs ofindividual and group accuracies. Then, $\hat { \boldsymbol { \beta } } ^ { ( g r ) }$ has a lower expected mean-squared error than $\hat { \beta } ^ { ( i d ) } i f$

$$
\frac {1}{4} \bigl (\max _ {x ^ {\prime} \in \mathcal {G} _ {n}} \beta (x ^ {\prime}) - \min _ {x ^ {\prime} \in \mathcal {G} _ {n}} \beta (x ^ {\prime}) \bigr) ^ {2} \leq \frac {N _ {n} - 1}{N _ {n}} \bar {\sigma} ^ {2}\tag{1}
$$

where $\begin{array} { r } { \bar { \sigma } ^ { 2 } = \frac { 1 } { N _ { n } } \sum _ { i \in [ N _ { n } ] } \sigma _ { x _ { i } } ^ { 2 } } \end{array}$ <sup>2</sup><sub>x</sub> with $\sigma _ { x _ { i } } ^ { 2 } = \beta ( x _ { i } ) ( 1 - \beta ( x _ { i } ) )$

The proof is based on bias-variance decomposition and the Popoviciu’s inequality (Popoviciu, 1965), which is given in Appendix A.1. In Proposition 2.1, (1) is the condition under which the group accuracy estimator achieves a lower mean-squared error than the individual accuracy estimator. Crucially, we can reduce $\begin{array} { r } { \operatorname* { m a x } _ { x \in \mathcal { G } _ { n } } \beta ( x ) - \operatorname* { m i n } _ { x \in \mathcal { G } _ { n } } \beta ( x ) } \end{array}$ through a careful group construction that we discuss in Section 2.2. Further, a sufficient condition for (1) tends to be loose (cf. Appendix A.2). Therefore, under the loose condition on the group construction, the group accuracy estimator would be statistically morefavorable.

## 2.2. Group Assignment

As seen in Figure 1(a), it is important to construct groups such that the expected accuracy of samples in the same group has a low variance. Therefore, we group examples by the maximum value of the softmax output as in Guo et al. (2017) based on an observation that the maximum value of the softmax output is highly correlated with accuracy in UDA (Wang et al., 2020). In addition, we note the result that an overall scale of the maximum value of the softmax output significantly varies from one domain to another (Yu et al., 2022). Thus, we adjust the sharpness of the softmax output in the target domain by introducing a learnable temperature parameter $t \in \mathcal T$ where $\tau$ is a bounded interval in $\mathbb { R } _ { + }$

Equipped with these ideas, we first gather a set of prediction confidences under a temperature t, denoted as $\bar { \boldsymbol { \mathcal { C } } } ^ { ( t ) } : =$ $\{ m ( x _ { S } ; 1 ) | ( x _ { S } , y _ { S } ) \in \mathcal { D } _ { S } \} \cup \{ m ( x _ { T } ; t ) | x _ { T } \in \mathcal { D } _ { T } \}$ where $m ( x ; t )$ is the maximum value of the softmax output under $t \left( t = 1 \right.$ recovers the standard softmax). Then, we construct the n-th confidence group under t for $n \in [ M ]$ by

$$
\mathcal {G} _ {n} ^ {(t)} := \{x \in \mathcal {D} _ {S} | q (\frac {n - 1}{M}; \mathcal {C} ^ {(t)}) \leq m (x; 1) <   q (\frac {n}{M}; \mathcal {C} ^ {(t)}) \}
$$

$$
\cup \left\{x \in \mathcal {D} _ {T} | q (\frac {n - 1}{M}; \mathcal {C} ^ {(t)}) \leq m (x; t) <   q (\frac {n}{M}; \mathcal {C} ^ {(t)}) \right\}\tag{2}
$$

where $\textstyle q { \bigl ( } { \frac { n } { M } } ; { \mathcal { C } } ^ { ( t ) } { \bigl ) }$ is the $\frac { n } { M }$ -th quantile of $\mathcal { C } ^ { ( t ) }$ . For the rest of the paper, we let ${ \cal I } ^ { ( g ) } ( \bar { x _ { S } } ) = \operatorname * { m i n } \{ k \in [ M ] : m ( x _ { S } ; 1 ) <$ $\begin{array} { r } { q \big ( \frac { k } { M } ; \bar { \mathcal { C } } ^ { ( t ) } \big ) \big ] } \end{array}$ } if $x _ { S } \sim p _ { S }$ and $I ^ { ( g ) } ( x _ { T } ) \stackrel { \cdot } { = } \operatorname* { m i n } \{ k \in [ M ]$ $\begin{array} { r } { m ( x _ { T } ; t ) < q ( \frac { k } { M } ; { \mathcal { C } } ^ { ( t ) } ) \} } \end{array}$ if $x _ { T } \sim p _ { T }$

## 2.3. Model Selection and Model Calibration

Before explaining how to obtain an accurate group accuracy estimator $\hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } )$ in Section 3, we first show how to use $\hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } )$ to simultaneously solve model calibration and model selection tasks with attractive properties.

Model calibration We use $\hat { \alpha } _ { T } ( \mathcal { G } _ { I ^ { ( g ) } ( x ) } ^ { ( t ) } )$ as an estimate of prediction confidence on $x \sim p _ { T }$ . Then, we can address the model calibration task in UDA with a bounded calibration error. Specifically, an expected squared calibration error can be decomposed as the sum of the variance of the accuracies for samples in the same group and a squared group accuracy estimation error (cf. Proposition $\mathrm { A . 1 } ) { \mathrm { : } }$ ; that is, $\mathbb { E } _ { p _ { T } } [ ( P ( Y =$ $\begin{array} { r } { \hat { Y } ) \ - \ \hat { \alpha } _ { T } ( \mathcal G _ { I ^ { ( g ) } ( X ) } ^ { ( t ) } ) ) ^ { 2 } ] \ = \ \sum _ { n \in [ M ] } \mathbb { E } _ { p _ { T } } [ \mathbf { 1 } ( X \ \in \ \mathcal G _ { n } ^ { ( t ) } ) ] } \end{array}$ $( V a r ( P ( Y = \hat { Y } ) | \mathcal { G } _ { n } ^ { ( t ) } ) + ( \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ) - \hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ) ) ^ { 2 } )$ . Thus, combined with the guarantees about the group accuracy estimation error (cf. Proposition 3.1 and (5)), our approach can enjoy the bounded calibration error unlike previous approaches using $m ( x ; t )$ as the prediction confidence estimate (Park et al., 2020; Wang et al., 2020).

Model selection We use the average group accuracy estimate $\mathbb { E } _ { p _ { T } } [ \hat { \alpha } _ { T } ( \mathcal { G } _ { I ^ { ( g ) } ( X ) } ^ { ( t ) } ) ]$ computed with a hold-out target domain dataset as the model selection criteria. Again, this criteria estimates the average accuracy of the model with a bounded error due to the Cauchy-Schwarz inequality; that is, $| \mathbb { E } _ { p _ { T } } [ P ( Y = \hat { Y } ) ] - \mathbb { E } _ { p _ { T } } [ \hat { \alpha } _ { T } ( \mathcal { G } _ { I ^ { ( g ) } ( X ) } ^ { ( t ) } ) ] | \leq \big ( \mathbb { E } _ { p _ { T } } [ ( P ( Y =$ $\hat { Y } ) - \hat { \alpha } _ { T } ( \mathcal { G } _ { I ^ { ( g ) } ( X ) } ^ { ( t ) } ) ) ^ { 2 } ] ) ^ { 1 / 2 }$ . In addition, compared to the approaches (Sugiyama et al., 2007; You et al., 2019) aiming to estimate only the mean accuracy in $p _ { T }$ , our approach will have an additional regularization effect from encouraging accurate group accuracy estimation for each group.

## 3. Accurate Group Accuracy Estimation via IW-GAE

In this section, we propose IW-GAE that aims to accurately estimate $\alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } )$ by using a novel idea tailored for UDA where $Y ( x )$ is available for $x \sim p _ { S }$ but not for $x \sim p _ { T }$ $\mathbf { A }$ core idea behind IW-GAE is to use importance weighting, which is appealing due to its statistical exactness for dealing with two different probability distributions under the absolute continuity condition (Sugiyama et al., 2007). Specifically, we define the target group accuracy of a group $\mathcal { G } _ { n } ^ { ( t ) }$ with the true IW $\begin{array} { r } { w ^ { * } ( x ) : = \frac { p _ { T } ( x ) } { p _ { S } ( x ) } } \end{array}$ as

$$
\alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}; w ^ {*}) = \mathbb {E} _ {p _ {S}} \left[ w ^ {*} (X) \mathbf {1} (Y = \hat {Y}) | \mathcal {G} _ {n} ^ {(t)} \right] \frac {P (X _ {S} \in \mathcal {G} _ {n} ^ {(t)})}{P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)})}\tag{3}
$$

where $X _ { S }$ and $X _ { T }$ are random variables having densities $p _ { S }$ and $p _ { T }$ , respectively. We denote $\hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { \ast } )$ to be the expectation with respect to the empirical measure. We also define the source group accuracy of $\mathcal { G } _ { n } ^ { ( t ) }$ as

$$
\alpha_ {S} (\mathcal {G} _ {n} ^ {(t)}; w ^ {*}) = \mathbb {E} _ {p _ {T}} \left[ \frac {\mathbf {1} (Y (X) = \hat {Y} (X))}{w ^ {*} (X)} | \mathcal {G} _ {n} ^ {(t)} \right] \frac {P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)})}{P (X _ {S} \in \mathcal {G} _ {n} ^ {(t)})}.\tag{4}
$$

![](images/ea87b51461d7c033f53818a7a5280e8dcda54311aaabe5c1f33ebde9966f0c1f.jpg)  
(a)

![](images/4561d45bb4d0d1f50ca39bd7ead6d374a2b454c7f9a39f1e6886c4659f43f45b.jpg)  
(b)

![](images/5cb5bf379fb8f495cb9cd758cb5aa197fc590c6d8328eae322634cf0a6a36a15.jpg)  
(c)  
Figure 2. Illustration of correlations between the optimization error and the source and target group accuracy estimation errors. Each point corresponds to a different IW estimator and the values are measured on the OfficeHome dataset (720 IW estimators in total). See Appendix G for more detailed discussions and analyses.

Given $\alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { \ast } )$ , the group accuracy estimation problem can be reduced to the importance weight estimation problem; that is, finding w˜ such that $\alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; \tilde { w } ) \approx \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { * } )$ . A typical approach for solving this estimation problem is to accurately approximate $\operatorname { I W } , \operatorname { i . e . , } \tilde { w } \approx w ^ { * }$ , which is challenging in high-dimensional spaces. In this work, we propose an optimization-based approach that minimizes the group accuracy estimation error during the IW estimation process, circumventing the difficulty of directly estimating $w ^ { * }$

## 3.1. Motivation for an Optimization-Based Approach

Our idea for accurately estimating the “target” group accuracy with IW estimator w˜ is to define two estimators for the “source” group accuracy defined in (4), with one estimator dependent on $\tilde { w } ,$ and to encourage the two estimators to agree with each other. This approach can be validated because the target accuracy estimation error of w˜ can be upper bounded by its source accuracy estimation error; that is,

$$
\begin{array}{l} | \alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}; w ^ {*}) - \alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}; \tilde {w}) | \leq \\ \tilde {w} _ {n} ^ {(u b)} \cdot | \alpha_ {S} (\mathcal {G} _ {n} ^ {(t)}; w ^ {*}) - \alpha_ {S} (\mathcal {G} _ {n} ^ {(t)}; \tilde {w}) | (\frac {P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)})}{P (X _ {S} \in \mathcal {G} _ {n} ^ {(t)})}) ^ {2} \end{array}\tag{5}
$$

where $\begin{array} { r } { \tilde { w } _ { n } ^ { ( u b ) } = \operatorname* { s u p } _ { x \in S u p p ( p _ { T } ( \cdot | \mathcal { G } _ { n } ^ { ( t ) } ) ) } \tilde { w } ( x ) } \end{array}$ and the bound is tight when $\tilde { w } ( x ) = \tilde { w } _ { n } ^ { ( u b ) }$ for all $x \in S u p p ( p _ { T } ( \cdot | \mathcal { G } _ { n } ^ { ( t ) } ) )$

Based on the fact that labeled samples are available in the source domain, we define a first estimator of $\alpha _ { S } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { \ast } )$ 1 with the simple Monte-Carlo estimation by

$$
\hat {\alpha} _ {S} ^ {(M C)} (\mathcal {G} _ {n} ^ {(t)}) = \hat {\mathbb {E}} _ {p _ {S}} [ \mathbf {1} (Y = \hat {Y}) | \mathcal {G} _ {n} ^ {(t)} ].\tag{6}
$$

We note that $\hat { \alpha } _ { S } ^ { ( M C ) } ( \mathcal { G } _ { n } ^ { ( t ) } )$ serves as a guide for the agreement between two estimators because it accurately estimates $\alpha _ { S } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { \ast } )$ with a small error of $\mathcal { O } ( 1 / \sqrt { | \mathcal { G } _ { n } ^ { ( t ) } ( \mathcal { D } _ { S } ) | } )$ where $\mathcal { G } _ { n } ^ { ( t ) } ( \mathcal { D } _ { S } ) : = \{ ( x _ { k } , y _ { k } ) \in \mathcal { D } _ { S } : x _ { k } \in \mathcal { G } _ { n } ^ { ( t ) } \}$

Based on the fact that input features are available both in source and target domains, we define a second estimator of $\alpha _ { S } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { \ast } )$ with importance weighting. Specifically, by assuming $\mathbb { E } _ { p _ { T _ { Y | x } } } [ 1 ( Y ( x ) = \hat { Y } ( x ) ) ] = \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { * } )$ for all $x \in \mathcal { G } _ { n } ^ { ( t ) }$ and replacing $w ^ { * }$ by w˜ in $( 4 ) .$ , we obtain the second estimator as a function of $\tilde { w } ,$ which is given by

$$
\begin{array}{r l} & {\hat {\alpha} _ {S} ^ {(I W)} (\mathcal {G} _ {n} ^ {(t)}; \tilde {w}) := \frac {\hat {P} (X _ {T} \in \mathcal {G} _ {n} ^ {(t)})}{\hat {P} (X _ {S} \in \mathcal {G} _ {n} ^ {(t)})} \cdot \hat {\mathbb {E}} _ {p _ {T}} \left[ \frac {\hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)} ; \tilde {w})}{\tilde {w} (X)} | \mathcal {G} _ {n} ^ {(t)} \right]} \\ & {\qquad = \hat {\mathbb {E}} _ {p _ {T}} [ \frac {1}{\tilde {w} (X)} | \mathcal {G} _ {n} ^ {(t)} ] \hat {\mathbb {E}} _ {p _ {S}} [ \mathbf {1} (Y = \hat {Y}) \tilde {w} (X) | \mathcal {G} _ {n} ^ {(t)} ] \quad (7. 5) \mathrm{d} X,} \end{array}
$$

where $\hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; \tilde { w } )$ is an empirical estimate of the target accuracy defined in (3), $\hat { P } ( X _ { T } \in \mathcal { G } _ { n } ^ { ( t ) } ) : = \hat { \mathbb { E } } _ { p _ { T } } [ \mathbf { 1 } ( X \ \in$ $\mathcal { G } _ { n } ^ { ( t ) } ) ]$ , and $\hat { P } ( X _ { S } \in \mathcal { G } _ { n } ^ { ( t ) } ) : = \hat { \mathbb { E } } _ { p _ { S } } [ \mathbf { 1 } ( X \in \mathcal { G } _ { n } ^ { ( t ) } ) ]$

Crucially, two estimators, $\hat { \alpha } _ { S } ^ { ( M C ) } ( \mathcal { G } _ { n } ^ { ( t ) } )$ and $\hat { \alpha } _ { S } ^ { ( I W ) } ( \mathcal { G } _ { n } ^ { ( t ) } ; \tilde { w } )$ can be similar to each other if the target group accuracy estimation with w˜ is accurate (cf. (7)); that is, $\hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; \tilde { w } ) \approx \hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { * } )$ . Therefore, by encouraging consistency between two estimators via solving the opti mization problem developed in Section 3.2, IW-GAE can accurately estimate the group accuracy not only in the source domain but also in the target domain. This conceptual attractiveness is empirically verified in Figure 2(a), which compares group accuracy estimation errors in the source and target domains from 720 IWs found by IW-GAE. Specifically, we found that under the optimal IW found by IW-GAE, group accuracy estimation errors in the source and target domains, $| \alpha _ { S } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { * } ) - \alpha _ { S } ( \mathcal { G } _ { n } ^ { ( t ) } ; \tilde { w } ) |$ and $| \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { * } ) - \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; \tilde { w } ) |$ in (5), are strongly correlated with a high Pearson correlation coefficient of 0.8.

## 3.2. Formulating an Optimization Problem

In this section, we aim to solve an optimization problem such that mi $\begin{array} { r } { \mathrm { n } _ { t , \tilde { w } } ( \hat { \alpha } _ { S } ^ { ( I W ) } ( \mathcal { G } _ { n } ^ { ( t ) } ; \tilde { w } ) - \hat { \alpha } _ { S } ^ { \tilde { ( M C ) } } ( \mathcal { G } _ { n } ^ { ( t ) } ) ) ^ { \tilde { 2 } } } \end{array}$ . Unfortunately, $\hat { \alpha } _ { S } ^ { ( I W ) } ( \mathcal { G } _ { n } ^ { ( t ) } ; \tilde { w } )$ in (7) is non-convex with respect to w˜ and non-smooth with respect to $t ,$ which is in general not effectively solvable with optimization methods (Jain et al., 2017). Further, directly solving an optimization problem in the function space of w˜ or optimizing over IW values for each $x \in \mathcal { X }$ would be computationally demanding. Therefore, we introduce the following techniques to formulate the optimization problem in a tractable way.

Relaxed reformulation We separately estimate IWs for the source and target domains, denoted as $\tilde { w } ^ { ( S ) }$ and $\tilde { w } ^ { ( T ) }$ , and then encourage their agreement through constraints. As a result, the estimator in (7) becomes $\begin{array} { r } { \hat { \alpha } _ { S } ^ { ( I W ) } ( \mathcal { G } _ { n } ^ { ( t ) } ; \tilde { w } ^ { ( S ) } , \tilde { w } ^ { ( T ) } ) = \mathbb { \hat { E } } _ { p _ { T } } [ \frac { 1 } { \tilde { w } ^ { ( T ) } ( X ) } | \mathcal { G } _ { n } ^ { ( t ) } ] \mathbb { \hat { E } } _ { p _ { S } } [ \mathbf { 1 } ( Y = } \end{array}$ $\hat { Y } ) \tilde { w } ^ { ( S ) } ( X ) | \mathcal { G } _ { n } ^ { ( t ) } ]$ , which is coordinatewise convex.

Discretize T We use a discrete set $\mathcal { T } : = \{ t _ { 1 } , t _ { 2 } , \cdot \cdot \cdot , t _ { n } \}$ based on the facts that a group separation is not sensitive to small changes in t and the inner optimization is not smooth with respect to t. We remark that the inner optimization problem with respect to $\tilde { w } ^ { ( S ) }$ and $\tilde { w } ^ { ( T ) }$ is readily solvable, so the discrete optimization over $\tau$ can be performed without much computational overhead.

Binned IWs We approximate $\tilde { w } ^ { ( S ) }$ and $\tilde { w } ^ { ( T ) }$ by the binned IWs. Specifically, X is partitioned into B number of bins: $\mathcal { X } \ = \ \cup _ { i = 1 } ^ { B } B _ { i }$ where $B _ { i } \ = \ \{ x \in \mathcal { X } | I ^ { ( B ) } ( x ) \ : = \ : i \}$ and $I ^ { ( B ) } : \dot { \mathcal { X } } \stackrel { \cdot } {  } [ B ]$ Then, we assign the same IW value to all samples in the same bin; that is, $\tilde { w } ^ { ( S ) } ( x _ { S } ) = \tilde { w } _ { j } ^ { ( S ) }$ for $x _ { S } \in B _ { j } \cap \mathcal { D } _ { S }$ and $\tilde { w } ^ { ( T ) } ( x _ { T } ) = \tilde { w } _ { j } ^ { ( T ) }$ for $x _ { T } \in B _ { j } \cap$ $\mathcal { D } _ { T }$ . In this way, the number of decision variables in the inner optimization problem is reduced to 2B. Further, we incorporate the recently proposed confidence interval (CI) estimation method for the binned IWs (Park et al., 2022) into the constraints. We denote $\Phi _ { j }$ be the CI of the true binned IW of $B _ { j }$ , which is obtained by applying the Clopper-Pearson CI (Clopper & Pearson, 1934) (cf. Appendix C.1). We let $\tilde { \mathbf { w } } ^ { ( S ) } = ( \tilde { w } _ { 1 } ^ { ( S ) } , \cdot \cdot \cdot , \tilde { w } _ { B } ^ { ( S ) } )$ and $\tilde { w } ^ { ( S ) } ( x ) = \tilde { w } _ { I ^ { ( B ) } ( x ) } ^ { ( S ) } .$ We also define $\tilde { \mathbf { w } } ^ { ( T ) }$ and $\tilde { w } ^ { ( T ) } ( x )$ in the same way.

Assembling the three techniques, we can effectively solve the group accuracy estimation problem by finding binned IWs $w ^ { \bar { \dag } } ( n ; t ^ { \dag } ) ~ \in ~ \mathbb { R } _ { + } ^ { 2 B }$ for $n \in [ M ]$ by solving the following nested optimization (see Algorithm 1 for pseudocode): $t ^ { \dagger } \in \arg \operatorname * { m i n } _ { t \in \mathcal { T } } \sum _ { n \in [ M ] } ( \hat { \alpha } _ { S } ^ { ( M C ) } ( \mathcal { G } _ { n } ^ { ( t ) } ) -$ $\hat { \alpha } _ { S } ^ { ( I W ) } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { \dagger } ( n ; t ) ) ) ^ { 2 }$ where $w ^ { \dagger } ( n ; t )$ is a solution of

min $( \hat { \alpha } _ { S } ^ { ( M C ) } ( \mathcal { G } _ { n } ^ { ( t ) } ) - \hat { \alpha } _ { S } ^ { ( I W ) } ( \mathcal { G } _ { n } ^ { ( t ) } ; \tilde { \mathbf { w } } ^ { ( S ) } , \tilde { \mathbf { w } } ^ { ( T ) } ) ) ^ { 2 }$ w˜<sup>(S)</sup>,w˜<sup>(T</sup> <sup>)</sup>

(8)

$$
\mathrm{s.t.} \tilde {w} _ {i} ^ {(S)} \in \Phi_ {i}, \quad \text { for } i \in [ B ]\tag{9}
$$

$$
\tilde {w} _ {i} ^ {(T)} \in \Phi_ {i}, \quad \mathrm{for} i \in [ B ]\tag{10}
$$

$$
\parallel \tilde {w} _ {i} ^ {(T)} - \tilde {w} _ {i} ^ {(S)} \parallel_ {2} ^ {2} \leq \delta_ {t o l}, \quad \mathrm{for} i \in [ B ]\tag{11}
$$

$$
\left| \hat {\mathbb {E}} _ {p _ {S}} [ \tilde {w} ^ {(S)} (X) | \mathcal {G} _ {n} ^ {(t)} ] - \frac {\hat {P} (X _ {T} \in \mathcal {G} _ {n} ^ {(t)})}{\hat {P} (X _ {S} \in \mathcal {G} _ {n} ^ {(t)})} \right| \leq \delta_ {p r}\tag{12}
$$

$$
\left| \hat {\mathbb {E}} _ {p _ {T}} \big [ \frac {1}{\tilde {w} ^ {(T)} (X)} | \mathcal {G} _ {n} ^ {(t)} \big ] - \frac {\hat {P} (X _ {S} \in \mathcal {G} _ {n} ^ {(t)})}{\hat {P} (X _ {T} \in \mathcal {G} _ {n} ^ {(t)})} \right| \leq \delta_ {p r}\tag{13}
$$

where $\delta _ { t o l }$ and $\delta _ { p r }$ are small constants. Box constraints (9) and (10) ensure that the obtained solution is in the CI, which bounds the estimation error of $\tilde { w } _ { i } ^ { ( S ) }$ and $\tilde { w } _ { i } ^ { ( T ) }$ by $| \Phi _ { i } |$ and guarantees their asymptotic convergences to the true binned IW (Thulin, 2014). This can also bound the target group accuracy estimation error as $| \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { * } ) -$ $\begin{array} { r } { \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; \tilde { \mathbf { w } } ^ { ( S ) } ) | \le \operatorname* { m a x } _ { b \in [ B ] } | \Phi _ { b } | P ( X _ { S } \in \mathcal { G } _ { n } ^ { ( t ) } ) / P ( X _ { T } \in } \end{array}$ ${ \mathcal { G } } _ { n } ^ { ( t ) } )$ . Constraint (11) corresponds to the relaxation for removing non-convexity of the original objective, and $\delta _ { t o l } ~ = ~ 0$ recovers the original objective. Constraints (12) and (13) are based on the equalities that the true IW $w ^ { \ast } ( \cdot )$ satisfies: $\begin{array} { r } { \mathbb { E } _ { p _ { S } } [ w ^ { * } ( X ) | X \in \mathcal { G } _ { n } ^ { ( t ) } ] = \frac { P ( X _ { T } \in \mathcal { G } _ { n } ^ { ( t ) } ) } { P ( X _ { S } \in \mathcal { G } _ { n } ^ { ( t ) } ) } } \end{array}$ and $\begin{array} { r } { \mathbb { E } _ { p _ { T } } [ 1 / w ^ { * } ( X ) | X \ \in \ { \mathcal G } _ { n } ^ { ( t ) } ] \ = \ \frac { P ( X _ { S } \in { \mathcal G } _ { n } ^ { ( t ) } ) } { P ( X _ { T } \in { \mathcal G } _ { n } ^ { ( t ) } ) } } \end{array}$ . After solving the optimization, we use the first B elements of $w ^ { \dagger } ( n ; t ^ { \dagger } )$ that correspond to the optimal $\tilde { \mathbf { w } } ^ { ( S ) }$ for estimating group accuracy of ${ \mathcal { G } } _ { n }$ , which is denoted by $w ^ { \dagger } ( n )$

## 3.3. Analyzing the Optimization Problem

The optimization problem in (8)-(13) aims to estimate the truncated IW $\begin{array} { r } { w ^ { * } ( x | \mathcal { G } _ { n } ^ { ( t ) } ) : = \frac { p _ { T } ( x | \mathcal { G } _ { n } ^ { ( t ) } ) } { p _ { S } ( x | \mathcal { G } _ { n } ^ { ( t ) } ) } } \end{array}$ for each $\mathcal { G } _ { n } ^ { ( t ) }$ that can induce an accurate source group accuracy estimator. However, the astute reader might notice that the objective in (8) does not measure the source group accuracy estimation error. In the following proposition, we show that solving the optimization problem minimizes the upper bound of the source group accuracy estimation error, thereby the target group accuracy estimation error due to (5).

Proposition 3.1. Let $w ^ { \dagger } ( n )$ be a solution to the nested optimization problem with $\delta _ { t o l } ~ = ~ 0$ and $\delta _ { p r } ~ = ~ 0$ . Let $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) ) : = ( \hat { \alpha } _ { S } ^ { ( M C ) } ( \mathcal { G } _ { n } ^ { ( t ) } ) - \hat { \alpha } _ { S } ^ { ( I W ) } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { \dagger } ( n ) ) ) ^ { 2 } \iota$ be the objective value. For $\tilde { \delta } > 0 ,$ the following inequality holds with probability at least $1 - { \tilde { \delta } } .$

$$
| \alpha_ {S} (\mathcal {G} _ {n} ^ {(t)}; w ^ {*}) - \alpha_ {S} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n)) |\tag{14}
$$

$$
\leq \epsilon_ {o p t} (w ^ {\dagger} (n)) + \epsilon_ {s t a t} + I d e n t B i a s (w ^ {\dagger} (n); \mathcal {G} _ {n} ^ {(t)})\tag{15}
$$

where $\epsilon _ { s t a t } \in \mathcal { O } ( \log ( 1 / \tilde { \delta } ) / \sqrt { | \mathcal { G } _ { n } ^ { ( t ) } ( \mathcal { D } _ { S } ) | ) }$ for $\underline { w } ^ { \dagger } ( n ) : =$ $\mathrm { m i n } _ { i \in [ B ] } \{ w _ { i } ^ { \dagger } ( n ) \}$ and IdentBias $\begin{array} { r l r } { ( w ^ { \dagger } ( n ) ; \mathcal { G } _ { n } ^ { ( t ) } ) } & { { } = } & { } \end{array}$ $\begin{array} { r l }   { \frac { P ( X _ { T } \in \mathcal { G } _ { n } ^ { ( t ) } ) } { 2 P ( X _ { S } \in \mathcal { G } _ { n } ^ { ( t ) } ) } \big ( \mathbb { E } _ { p _ { T } } [ ( I ( Y = \hat { Y } ) - \hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { \dagger } ( n ) ) ) ^ { 2 } | \mathcal { G } _ { n } ^ { ( t ) } ] + } \end{array}$ $\frac { 1 } { \underline { { w } } ^ { \dagger } ( n ) ^ { 2 } } \Big )$

The proof is based on the Cauchy-Schwarz inequality, which is provided in Appendix A.4. Proposition 3.1 shows that we can reduce the source accuracy estimation error by reducing $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ ) by solving the optimization problem. Here, we note that a large value of $\epsilon _ { s t a t } + I d e n t B i a s ( w ^ { \dagger } ( n ) ; \mathcal { G } _ { n } ^ { ( t ) } )$ or a looseness of (15) could significantly decrease the effectiveness of IW-GAE. However, in the empirical analyses presented in Figures 2(b) and $2 ( \mathrm { c } )$ , it turns out that reducing $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ ) can effectively reduce the group accuracy estimation in both source and target domains. Finally, we note that Ident $B i a s ( w ^ { \dagger } ( n ) ; { \mathcal G } _ { n } )$ can be reduced by decreasing the variance of the correctness within the group, which advocates our group construction with the maximum value of the softmax output (cf. Proposition A.2).

Table 1. Model calibration benchmark results of MDD (OfficeHome) and CDAN (DomainNet and VisDa-2017). The numbers indicate the mean ECE across ten repetitions with boldface for the minimum mean ECE. Due to space limitations, we present the first six domain pairs of OfficeHome and DomainNet in the main body and the rest of them in Tables A1 and A2, respectively. However, we report average performance among all pairs in Avg\*. Oracle is obtained by applying TS with labeled test samples in the target domain.

<table><tr><td></td><td colspan="7">OfficeHome</td><td colspan="7">DomainNet</td><td>VisDa-2017</td></tr><tr><td>Method</td><td>Ar-Cl</td><td>Ar-Pr</td><td>Ar-Rw</td><td>Cl-Ar</td><td>Cl-Pr</td><td>Cl-Rw</td><td>Avg*</td><td>Cl-Pt</td><td>Cl-Rw</td><td>Cl-Sk</td><td>Pt-Cl</td><td>Pt-Rw</td><td>Pt-Sk</td><td>Avg*</td><td>Sim-Rw</td></tr><tr><td>Vanilla</td><td>40.61</td><td>25.62</td><td>15.56</td><td>33.83</td><td>25.34</td><td>24.75</td><td>24.37</td><td>13.23</td><td>6.36</td><td>12.92</td><td>9.75</td><td>6.35</td><td>15.56</td><td>10.06</td><td>21.63</td></tr><tr><td>TS</td><td>35.86</td><td>22.84</td><td>10.60</td><td>28.24</td><td>20.74</td><td>20.06</td><td>24.01</td><td>12.95</td><td>5.95</td><td>13.32</td><td>6.40</td><td>3.90</td><td>11.07</td><td>9.22</td><td>22.42</td></tr><tr><td>CPCS</td><td>22.93</td><td>22.07</td><td>10.19</td><td>26.88</td><td>18.36</td><td>14.05</td><td>19.79</td><td>5.64</td><td>21.90</td><td>7.70</td><td>5.14</td><td>7.72</td><td>7.90</td><td>9.60</td><td>22.42</td></tr><tr><td>IW-TS</td><td>32.63</td><td>22.90</td><td>11.27</td><td>28.05</td><td>19.65</td><td>18.67</td><td>23.26</td><td>16.76</td><td>16.70</td><td>12.53</td><td>5.29</td><td>7.84</td><td>4.34</td><td>10.49</td><td>22.19</td></tr><tr><td>TransCal</td><td>33.57</td><td>20.27</td><td>8.88</td><td>26.36</td><td>18.81</td><td>18.42</td><td>20.84</td><td>18.51</td><td>29.63</td><td>20.92</td><td>23.02</td><td>31.83</td><td>17.58</td><td>25.39</td><td>18.79</td></tr><tr><td>IW-GAE</td><td>12.78</td><td>4.70</td><td>12.93</td><td>7.52</td><td>4.42</td><td>4.11</td><td>8.93</td><td>6.06</td><td>8.15</td><td>5.38</td><td>7.45</td><td>3.89</td><td>3.94</td><td>6.32</td><td>14.70</td></tr><tr><td>Oracle</td><td>10.45</td><td>10.72</td><td>6.47</td><td>8.10</td><td>7.62</td><td>6.55</td><td>8.42</td><td>4.55</td><td>2.78</td><td>4.01</td><td>3.10</td><td>3.72</td><td>2.72</td><td>3.02</td><td>5.48</td></tr></table>

## 4. Experiments

In this section, we extensively evaluate IW-GAE on model calibration and selection tasks. Since both tasks are based on UDA classification tasks, we first provide the common setup and task-specific setup such as the baselines and evaluation metrics in the corresponding sections.

Datasets We use OfficeHome (Venkateswara et al., 2017) containing around 15,000 images of 65 categories from four domains (art, clipart, product, real-world), VisDA-2017 (Peng et al., 2017) containing around 280,000 images of 12 categories from two domains (real and synthetic images), and DomainNet (Peng et al., 2019) containing around 570,000 images of 345 categories from six domain pairs (clipart, real, sketch, infograph, painting, quickdraw).

Base models We consider maximum mean discrepancy (MDD; (Zhang et al., 2019)), conditional domain adversarial network (CDAN; (Long et al., 2018)), and maximum classifier discrepancy (MCD; (Saito et al., 2018)) with ResNet-50 (He et al., 2016) as the backbone neural network, which are the most popular high-performing UDA methods. Details about the training configurations are given in Appendix D.

IW-GAE implementation details We solve the optimization problem in (8)-(13) by sequential least square programming (Kraft, 1988) because it is a constrained nonlinear optimization problem with box constraints. Also, we set the number of groups M = 10 and the number of bins $B = 1 0$ for all experiments, which are taken from the standard range [10, 20] used for binning samples based on summary statistics (Guo et al., 2017; Park et al., 2022). Finally, we set $\mathcal { T } = \{ 0 . 8 5 , 0 . 9 0 , 0 . 9 5 , 1 . 0 0 , 1 . 0 5 , 1 . 1 0 \}$ . We provide further details in Appendix D.

## 4.1. Model Calibration Performance

Setup & Metric In this experiment, our goal is to match the confidence of a prediction to its expected accuracy in the target domain. Following the standard (Guo et al., 2017; Park et al., 2020; Wang et al., 2020), we use expected calibration error (ECE) on the test dataset as a measure of calibration performance. The ECE measures the average absolute difference between the confidence and accuracy of binned groups, which is defined as

$$
E C E (\mathcal {D} _ {T}) = \sum_ {n \in [ E ]} \frac {| \mathcal {M} _ {n} |}{| \mathcal {D} _ {T} |} | \hat {\mathrm{Acc}} (\mathcal {M} _ {n}) - \hat {\mathrm{Conf}} (\mathcal {M} _ {n}) |\tag{16}
$$

where $\begin{array} { r c l c r c l } { \mathcal { M } _ { n } } & { : = } & { \{ x _ { i } } & { \in } & { \mathcal { D } _ { T } | \frac { n - 1 } { E } } & { \leq } & { m ( x _ { i } ; 1 ) } & { < } & { } \end{array}$ $\textstyle { \frac { n } { E } } \}$ $\hat { \mathrm { A c c } } ( \mathcal { M } _ { n } )$ is the average accuracy in $\mathcal { M } _ { n } ,$ and $\hat { \mathrm { C o n f } } ( \mathcal { M } _ { n } )$ is the average confidence in $\mathcal { M } _ { n }$ . For IW-GAE, $\begin{array} { r l r } { \mathrm { C o n f } ( { \mathcal M } _ { n } ) } & { = } & { \frac { 1 } { | { \mathcal M } _ { n } | } \sum _ { x \in { \mathcal M } _ { n } } \hat { \alpha } _ { T } ( \mathcal G _ { I ^ { ( g ) } ( x ) } ^ { ( t ^ { \dagger } ) } ; { w ^ { \dagger } ( I ^ { ( g ) } ( x ) ) } ) } \end{array}$ which is the average of group accuracy estimations that each $x \in \mathcal { M } _ { n }$ belongs to. We use $E = 1 5$ following the standard value (Guo et al., 2017; Wang et al., 2020).

Baselines We consider the following five different baselines: The vanilla method uses a maximum value of the softmax output as the confidence of the prediction. We also consider temperature scaling-based methods that adjust the temperature parameter by maximizing the following calibration measures: Temperature scaling (TS) (Guo et al., 2017): the log-likelihood on the source validation dataset; IW temperature scaling (IW-TS): the log-likelihood on the importance weighted source validation dataset; Calibrated prediction with covariate shift (CPCS): the Brier score (Brier, 1950) on the importance weighted source validation dataset; TransCal (Wang et al., 2020): the ECE on the importance weighted source validation dataset with a bias and variance reduction technique. These methods also use a maximum value of the (temperature-scaled) softmax output as the confidence. For methods with the IW, we use a logistic regression-based IW estimator as in Wang et al. (2020) (cf. Appendix C.2).

Results As shown in Table 1, IW-GAE achieves the best average ECEs across different base models and datasets. Specifically, IW-GAE outperforms state-of-the-art performances by 53% on OfficeHome, 31% on DomainNet, and 21% on VisDa-2017. Further, in additional experiments with different base methods (CDAN and MCD) on Office-Home, IW-GAE consistently outperforms state-of-the-art performances by 2% and 5%, respectively (cf. Tables A5 and A6). Given that the second best model varies for a different dataset and a different base model, we believe that the consistent improvements by IW-GAE indicate its significant robustness compared to the baselines.

Table 2. Checkpoint selection benchmark results of MDD with ResNet-50 on OfficeHome. The numbers indicate the mean test accuracy of selected model across ten repetitions with boldface for the maximum mean test accuracy. Due to space limitations, we present the first six domain pairs in the main body and the rest of them in Tables A3 and A4. However, we report average performance among all pairs in Avg\*. Here, we also present two best methods among the target-only validation methods and the rest of them in Tables A3 and A4. Lower bound and Oracle indicate the accuracy of the models with the worst and best test accuracy, respectively.

<table><tr><td></td><td colspan="7">Hyperparameter Selection</td><td colspan="7">Checkpoint Selection</td></tr><tr><td>Method</td><td>Ar-Cl</td><td>Ar-Pr</td><td>Ar-Rw</td><td>Cl-Ar</td><td>Cl-Pr</td><td>Cl-Rw</td><td>Avg*</td><td>Ar-Cl</td><td>Ar-Pr</td><td>Ar-Rw</td><td>Cl-Ar</td><td>Cl-Pr</td><td>Cl-Rw</td><td>Avg*</td></tr><tr><td>Vanilla</td><td>53.31</td><td>70.96</td><td>77.44</td><td>59.70</td><td>65.17</td><td>69.96</td><td>65.45</td><td>47.22</td><td>74.14</td><td>77.76</td><td>61.85</td><td>70.96</td><td>71.59</td><td>67.47</td></tr><tr><td>IWCV</td><td>53.24</td><td>69.61</td><td>72.50</td><td>59.70</td><td>65.17</td><td>67.50</td><td>65.18</td><td>54.46</td><td>74.22</td><td>72.27</td><td>61.48</td><td>70.49</td><td>70.62</td><td>67.48</td></tr><tr><td>DEV</td><td>53.31</td><td>70.72</td><td>77.44</td><td>59.79</td><td>67.99</td><td>69.96</td><td>66.00</td><td>54.04</td><td>73.94</td><td>78.16</td><td>61.52</td><td>63.19</td><td>70.70</td><td>67.39</td></tr><tr><td>InfoMax</td><td>54.34</td><td>70.96</td><td>77.53</td><td>61.48</td><td>69.93</td><td>71.06</td><td>67.79</td><td>54.32</td><td>74.72</td><td>77.90</td><td>62.79</td><td>71.03</td><td>71.47</td><td>68.38</td></tr><tr><td>TransScore</td><td>54.34</td><td>70.96</td><td>77.53</td><td>61.48</td><td>69.93</td><td>71.06</td><td>67.87</td><td>54.79</td><td>74.14</td><td>77.77</td><td>61.76</td><td>70.97</td><td>71.48</td><td>68.38</td></tr><tr><td>IW-GAE</td><td>54.34</td><td>70.96</td><td>78.47</td><td>61.48</td><td>69.93</td><td>71.06</td><td>67.95</td><td>54.32</td><td>73.98</td><td>78.51</td><td>61.96</td><td>71.25</td><td>71.70</td><td>68.48</td></tr><tr><td>Lower bound</td><td>52.51</td><td>69.27</td><td>72.50</td><td>59.70</td><td>65.17</td><td>67.50</td><td>64.10</td><td>41.90</td><td>64.88</td><td>72.27</td><td>52.00</td><td>58.48</td><td>62.13</td><td>58.21</td></tr><tr><td>Oracle</td><td>54.34</td><td>70.96</td><td>78.47</td><td>61.48</td><td>69.93</td><td>71.06</td><td>68.01</td><td>54.80</td><td>74.79</td><td>78.61</td><td>62.79</td><td>71.59</td><td>72.18</td><td>68.95</td></tr></table>

Table 3. Additional model calibration benchmark with post-hoc calibration methods under unknown distribution shifts. Due to space limitations, we present the first six domain pairs in the main body and the rest of them in Table A1.

<table><tr><td>Method</td><td>Ar-Cl</td><td>Ar-Pr</td><td>Ar-Rw</td><td>Cl-Ar</td><td>Cl-Pr</td><td>Cl-Rw</td><td>Avg*</td></tr><tr><td>Vanilla</td><td>40.61</td><td>25.62</td><td>15.56</td><td>33.83</td><td>25.34</td><td>24.75</td><td>27.37</td></tr><tr><td>PTS</td><td>31.91</td><td>24.36</td><td>10.65</td><td>22.81</td><td>20.42</td><td>15.92</td><td>21.91</td></tr><tr><td>AvUTS</td><td>29.59</td><td>25.55</td><td>10.40</td><td>31.81</td><td>26.06</td><td>26.15</td><td>28.17</td></tr><tr><td>TransCal</td><td>33.57</td><td>20.27</td><td>8.88</td><td>26.36</td><td>18.81</td><td>18.42</td><td>20.84</td></tr><tr><td>IW-GAE</td><td>12.78</td><td>4.70</td><td>12.93</td><td>7.52</td><td>4.42</td><td>4.11</td><td>8.93</td></tr></table>

In Table 3, we also compare IW-GAE with two recent posthoc calibration methods, called PTS (Tomani et al., 2022) and AvUTS (Krishnan & Tickoo, 2020), which are designed to perform model calibration without using target domain samples. As post-hoc calibration methods under general distribution shifts, PTS and AvUTS show compatible results with IW-GAE and outperform some baselines in some domain pairs, i.e., certain types of distribution shifts. However, they cannot achieve better average performances than baselines or IW-GAE that explicitly consider the target distribution shift through importance weighting. The results show the advantage of explicitly using the information about the distribution shifts for the model calibration task in UDA.

## 4.2. Model Selection Performance

Setup & Metric In this experiment, we perform two important model selection tasks of choosing the best checkpoint and the best hyperparameter. Specifically, for the checkpoint selection, we train MDD on the OfficeHome dataset for 30 epochs and save the checkpoint at the end of each epoch. For the hyperparameter selection, we repeat training the MDD method by changing its key hyperparameter of margin coefficient from 1 to 8 (the default value is 4). Given a set of models from different checkpoints or different hyperparameters, we choose the best model based on a model selection criterion (such as IW-GAE or other baselines). Specifically, for IW-GAE, we choose the model with the maximum value of the mean group accuracy estimations, which is computed by $\begin{array} { r } { \frac { 1 } { \vert { \mathcal D } _ { T } \vert } \sum _ { x \in { \mathcal D } _ { T } } \hat { \alpha } _ { T } ( \mathcal G _ { I ^ { ( g ) } ( x ) } ^ { ( t ^ { \dagger } ) } ; w ^ { \dagger } ( I ^ { ( g ) } ( x ) ) ) } \end{array}$ . Then, we compare the test target accuracy of the chosen models under different model selection methods.

Baselines We consider the following baselines that evaluate the model’s performance in terms of the following criterion: Vanilla: the minimum classification error on the source validation dataset; Importance weighted cross validation (IWCV) (Sugiyama et al., 2007): the minimum importanceweighted classification error on the source validation dataset; Deep embedded validation (DEV)) (You et al., 2019): the minimum deep embedded validation risk on the source validation dataset; Target-only validation methods: the maximum value of some pre-defined measures, e.g., the average negative entropy of predictions, on the unlabeled target validation dataset. Again, we use a logistic regression-based IW estimator for methods with the IW (IWCV and DEV). For the target-only validation methods, we consider InfoMax (Shi & Sha, 2012), Corr-C (Tu et al., 2023), SND (Saito et al., 2021), MixVal (Hu et al., 2024), and TransScore (Yang et al., 2024).

Results Table 2 shows that model selection with IW-GAE achieves the best average accuracy among IW-based model selection methods, improving state-of-the-art by 9% in the checkpoint selection 18% in the hyperparameter selection in terms of the relative scale of lower and upper bounds of accuracy. Note that IWCV does not improve the vanilla method on average, which could be due to the inaccurate IW estimation by the logistic regression-based method. In this sense, IW-GAE has the advantage of depending less on the performance of the IW estimator since the estimated value is used to construct bins for the CI, and then the exact value is found by solving the separate optimization problem.

Table 4. Results of an ablation study with four randomly selected domain pairs in OfficeHome. The numbers indicate the mean ECE of MDD with ResNet-50.

<table><tr><td>Method</td><td>Ar-Pr</td><td>Pr-Cl</td><td>Rw-Cl</td><td>Rw-Pr</td><td>Avg</td></tr><tr><td>Vanilla</td><td>40.61</td><td>38.62</td><td>36.51</td><td>14.01</td><td>32.44</td></tr><tr><td>CPCS</td><td>22.07</td><td>29.20</td><td>26.54</td><td>11.14</td><td>22.24</td></tr><tr><td>TransCal</td><td>20.27</td><td>29.86</td><td>29.90</td><td>10.00</td><td>22.51</td></tr><tr><td>Grouping by IW</td><td>14.18</td><td>34.67</td><td>35.08</td><td>5.30</td><td>22.31</td></tr><tr><td>W/O CI</td><td>11.00</td><td>29.73</td><td>24.44</td><td>2.09</td><td>16.82</td></tr><tr><td>IW-Mid</td><td>31.62</td><td>30.35</td><td>26.32</td><td>10.60</td><td>24.70</td></tr><tr><td>IW-GAE</td><td>4.70</td><td>17.49</td><td>9.52</td><td>8.14</td><td>9.97</td></tr></table>

In addition, we observe that all target-only validation methods except SND outperform the IW-based baselines (cf. Table 2). The results are consistent with the recent empirical observations that target-only validation methods are more favorable than IW-based methods for the model selection task in UDA (Saito et al., 2021; Hu et al., 2024). However, notably, they underperform IW-GAE in both checkpoint and hyperparameter selection tasks, which strongly supports the practical advantage of IW-GAE as a model selection method. We believe that the impressive empirical performance of IW-GAE could bring more attention to the IW-based model selection techniques in the machine learning community, which is a principled statistical method for the model selection task under distribution shifts but has been considered impractical and less effective.

## 4.3. Ablation Study

We conduct an ablation study by performing the model calibration task without key components of IW-GAE.

Group construction with the softmax output We first examine the effectiveness of group construction based on the maximum value of the softmax output by examining a group construction function based on IW. In Table 4, we can see that grouping by the IW significantly reduces the performance of IW-GAE due to a large variance of prediction accuracy within a group (cf. the case of group 2 in Figure 1(a)). Specifically, the large value of $V a r ( \mathbf { 1 } ( Y = \hat { Y } ) | \mathcal { G } _ { n } ^ { ( t ) } )$ increases the Ident $B i a s ( w ^ { \dagger } ( n ) ; { \mathcal G } _ { n } ^ { ( t ) } )$ , which can loosen the upper bound of the source group accuracy estimation error in (15). Therefore, it is important to construct groups so that each group has a low variance of the correctness of predictions, as our design developed in Section 2.2.

Constraints from the CI estimation method Next, we examine the dependency of the effectiveness of IW-GAE on the CI estimation method (Park et al., 2022) by setting only minimum and maximum values of IWs (W/O CI); that is, $\Phi _ { i } = [ 1 / 6 , 6 . 0 ]$ for $i \in [ M ]$ . In Table 4, we can see that IW-GAE outperforms strong baseline methods (CPCS and TransCal) even under this naive interval of IWs. However, the performance is reduced compared to the setting with the sophisticated CI estimator. In this regard, developing an optimization-based IW estimation method that works effectively without the CI estimator in the constraints could be an interesting future direction.

![](images/c1ba0089168544bfe6fc6f61a1fc11423d3fd4c3b42c85abf23d91ed2df4fe4f.jpg)  
Figure 3. True group accuracy and estimated group accuracy of IW-GAE and IW-Mid under MDD. The shaded areas represent possible group accuracy estimation with binned IWs in the CI. See Figure A2 for visualization of all domain pairs.

IW optimization To further show the effectiveness of the optimization in IW-GAE, we also test the method of selecting the middle point in the CI proposed in Park et al. (2022) as an IW estimator (IW-Mid), which originates herein. For IW-Mid, we perform both model calibration and selection tasks across different base models and datasets. Surprisingly, IW-Mid achieves the better average performances than other IW-based baselines in some benchmarks (cf. Tables A1- A4). However, its performance is worse and significantly unstable compared to IW-GAE, such as achieving the worse performance even than the vanilla method in experiments with CDAN (Table A5) and MCD (Table A6). This means that the CI estimation method does not effectively estimate the group accuracy without properly selecting the exact IW through our optimization method, which is consistent with the theoretical result in Proposition 3.1. The instability and inaccuracy of IW-Mid compared to IW-GAE also can be identified in the qualitative evaluation of their group accuracy estimations (cf. Figure 3), which shows that the true accuracy is close to IW-Mid only in some cases.

## 4.4. Sensitivity Analysis

We perform a sensitivity analysis with respect to key hyperparameters of the number of accuracy groups $M \in [ 4 , 2 7 ]$ and the number of bins $B \in [ 4 , 2 7 ]$ (the default value for both M and B is 10). In Figure 4, note that the average performance changes under different hyperparameter values are somewhat stable; the average changes are within the range of 10% for most cases, even though a large variance appears for extreme values such as M = 4 and $B = 2 7$ Therefore, the results show that IW-GAE would consistently outperform state-of-the-art methods under changes in M and B within their standard range [10, 20] since the best baseline (TransCal) achieves the mean ECE score about 40% higher for the selected domain pairs (cf. Table 1).

![](images/57057d835ba3acaf46c854df4229dfc07182d1d35de6109c7ae8d558f76f29f1.jpg)  
(a)

![](images/ec43b789a9c1ca6dfb699acacb2b17bafe0feb4ef70bb3bbca2f06a6430eee9c.jpg)  
(b)  
Figure 4. Sensitivity analysis with respect to M (a) and B (b) on four domain pairs (Ar-Pr, Pr-Cl, Rw-Cl, Rw-Pr) in OfficeHome. The shaded areas represent areas between the minimum and the maximum changes in ECE (lower is better).

## 5. Related Work

Model calibration in UDA Although post-hoc calibration methods (Guo et al., 2017) and Bayesian methods (Gal & Ghahramani, 2016; Lakshminarayanan et al., 2017; Sensoy et al., 2018) have been achieving impressive calibration performances in the i.i.d. setting, it has been shown that most of the calibration improvement methods fall short under distribution shifts (Ovadia et al., 2019) (see Appendix B.1 for more discussion). While there have been attempts to perform model calibration under unknown distribution shifts by simulating the distribution shifts (Salvador et al., 2021), designing a robust loss function that prevents extrapolations with high confidences (Krishnan & Tickoo, 2020; Hebbalaguppe et al., 2022; Liu et al., 2022), and learning an instant-wise temperature parameter (Tomani et al., 2022), handling model calibration problems under general distribution shifts is challenging. However, the availability of unlabeled samples in the distribution shifted target domain relaxes the difficulty of model calibration in UDA. In particular, unlabeled samples in the target domain enable an IW formulation for the quantity of interests in the shifted domain. Therefore, the post-doc calibration methods (e.g., (Guo et al., 2017)) can be applied by reweighting calibration measures such as the expected calibration error (Wang et al., 2020) and the Brier score (Park et al., 2020) in the source dataset with an IW. However, it remains unclear how the IW estimation error impacts the calibration error. Our approach, by contrast, can directly minimize the calibration error during the IW estimation process.

Model selection in UDA A standard procedure for model selection in the i.i.d. settings is the cross-validation, which enjoys statistical guarantees about bias and variance of model performance (Stone, 1977; Kohavi et al., 1995; Efron & Tibshirani, 1997). However, in UDA, the distribution shifts violate assumptions for the statistical guarantees. Furthermore, in practice, the accuracy measured in one domain is significantly changed in the face of natural/adversarial distribution shifts (Goodfellow et al., 2015; Hendrycks & Dietterich, 2019; Ovadia et al., 2019). To tackle the distribution shift problem, importance weighted cross validation (Sugiyama et al., 2007) applies importance sampling for obtaining an unbiased estimate of model performance in the distribution shifted target domain. Further, recent work in UDA controls variance of the importance-weighted cross validation with a control variate (You et al., 2019). These methods aim to accurately estimate the IW and then use an IW formula for the expected accuracy estimation. In this work, our method concerns the accuracy estimation error in the target domain during the process of IW estimation, which can potentially induce an IW estimation error but result in an accurate accuracy estimator. Finally, we remark a direction that aims to evaluate the model performance without source domain data based on neighborhood structure (Saito et al., 2021; Hu et al., 2024), prediction uncertainty in the target domain (Musgrave et al., 2022; Tu et al., 2023), and newly developed metrics (Yang et al., 2024).

## 6. Conclusion

In this work, we address the model calibration and selection tasks in UDA by estimating group accuracy, which is accurately estimated by solving a novel optimization problem. Specifically, we define a Monte-Carlo estimator and an IW-based estimator of group accuracy in the source domain. Then, we formulate an optimization problem that aims to find the IW making the two estimators close to each other. Crucially, the optimal IW provably leads to an accurate group accuracy estimator in the target domain. Our method achieves the best performances in both model calibration and selection tasks in UDA across a wide range of benchmark problems. We believe that the impressive performance gains by our method show a promising future direction of the (importance-weighted) group accuracy estimation for addressing critical challenges in UDA.

Limitations and future directions We note that all IWbased methods (CPCS, IW-TS, TransCal, IW-GAE) fail to improve the standard method in the i.i.d. scenario in our experiments with pre-trained large-language models (XLM-R (Conneau et al., 2019) and GPT-2 (Solaiman et al., 2019)). We conjecture that these models are less subject to the distribution shifts due to massive amounts of training data that may include the target domain datasets, so applying the methods in the i.i.d. setting can work effectively. In this regard, we leave the following important research questions: “Are IW-based methods less effective under mild distribution shifts?” and “Can we develop methods effective for all levels of distribution shifts?”

## Impact Statement

In this work, we consider model calibration and model selection problems under distribution shifts, which hold great significance in practice, especially in safety-critical domains such as medical diagnosis and autonomous driving. Specifically, the well-calibrated models can properly require human intervention for uncertain predictions, preventing any catastrophic consequences from overconfident predictions in automated systems. In addition, an accurate model selection allows the deployment of high-performing models in the distribution-shifted environment. Further, precisely evaluating model performance enables practitioners to rejec deploying the model if its estimated performance is below a certain acceptable level. As evidenced in our extensive evaluations, IW-GAE helps to obtain robust and trustworthy models equipped with these ideal properties in unsupervised domain adaptation settings. Also, the core idea behind IW-GAE is to introduce a notion of group accuracy and then estimate it by optimizing the importance weight, which does not depend on particular characteristics or attributes of datasets. Therefore, IW-GAE would not leverage any biases inherent in the datasets, which prevents our work from having potential negative societal consequences. To sum up, we believe in a positive broader impact of IW-GAE.

## Acknowledgement

We would like to thank Jihyeon Hyeong, Yuchen Lou, Jiezhong Wu, and anonymous reviewers for insightful discussions and helpful suggestions in writing the manuscript.

## References

Ben-David, S., Blitzer, J., Crammer, K., Kulesza, A., Pereira, F., and Vaughan, J. W. A theory of learning from different domains. Machine Learning, 79:151–175, 2010.

Bickel, S., Bruckner, M., and Scheffer, T. Discriminative¨ learning for differing training and test distributions. In International Conference on Machine Learning, 2007.

Brier, G. W. Verification of forecasts expressed in terms of probability. Monthly Weather Review, 78(1):1–3, 1950.

Cai, T., Gao, R., Lee, J., and Lei, Q. A theory of label propagation for subpopulation shift. In International Conference on Machine Learning, 2021.

Chen, Y., Wei, C., Kumar, A., and Ma, T. Self-training avoids using spurious features under domain shift. In Advances in Neural Information Processing Systems, 2020.

Clopper, C. J. and Pearson, E. S. The use of confidence or fiducial limits illustrated in the case of the binomial. Biometrika, 26(4):404–413, 1934.

Conneau, A., Khandelwal, K., Goyal, N., Chaudhary, V., Wenzek, G., Guzman, F., Grave, E., Ott, M., Zettlemoyer,´ L., and Stoyanov, V. Unsupervised cross-lingual representation learning at scale. arXiv preprint arXiv:1911.02116, 2019.

Dawid, A. P. The well-calibrated Bayesian. Journal of the American Statistical Association, 77(379):605–610, 1982.

Ebrahimi, S., Elhoseiny, M., Darrell, T., and Rohrbach, M. Uncertainty-guided continual learning with Bayesian neural networks. In International Conference on Learning Representations, 2020.

Efron, B. and Tibshirani, R. Improvements on crossvalidation: The 632+ bootstrap method. Journal of the American Statistical Association, 92(438):548–560, 1997.

Gal, Y. and Ghahramani, Z. Dropout as a Bayesian approximation: Representing model uncertainty in deep learning. In International Conference on Machine Learning, 2016.

Gal, Y., Hron, J., and Kendall, A. Concrete dropout. In Advances in Neural Information Processing Systems, 2017.

Goodfellow, I. J., Shlens, J., and Szegedy, C. Explaining and harnessing adversarial examples. In International Conference on Learning Representations, 2015.

Guo, C., Pleiss, G., Sun, Y., and Weinberger, K. Q. On calibration of modern neural networks. In International Conference on Machine Learning, 2017.

He, K., Zhang, X., Ren, S., and Sun, J. Deep residual learning for image recognition. In IEEE Conference on Computer Vision and Pattern Recognition, 2016.

Hebbalaguppe, R., Prakash, J., Madan, N., and Arora, C. A stitch in time saves nine: A train-time regularizing loss for improved neural network calibration. In IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2022.

Hendrycks, D. and Dietterich, T. Benchmarking neural network robustness to common corruptions and perturbations. In International Conference on Learning Representations, 2019.

Hu, D., Liang, J., Liew, J. H., Xue, C., Bai, S., and Wang, X. Mixed samples as probes for unsupervised model selection in domain adaptation. Advances in Neural Information Processing Systems, 2024.

Jain, P., Kar, P., et al. Non-convex optimization for machine learning. Foundations and Trends® in Machine Learning, 10(3-4):142–363, 2017.

Jiang, J., Chen, B., Fu, B., and Long, M. Transferlearning-library. https://github.com/thuml/ Transfer-Learning-Library, 2020.

Joo, T., Chung, U., and Seo, M.-G. Being Bayesian about categorical probability. In International Conference on Machine Learning, 2020.

Kohavi, R. et al. A study of cross-validation and bootstrap for accuracy estimation and model selection. In International Joint Conferences on Artificial Intelligence, 1995.

Kraft, D. A software package for sequential quadratic programming. Forschungsbericht- Deutsche Forschungsund Versuchsanstaltfur Luft- und Raumfahrt, 1988.

Krishnan, R. and Tickoo, O. Improving model calibration with accuracy versus uncertainty optimization. Advances in Neural Information Processing Systems, 2020.

Lakshminarayanan, B., Pritzel, A., and Blundell, C. Simple and scalable predictive uncertainty estimation using deep ensembles. In Advances in Neural Information Processing Systems, 2017.

Liu, B., Ben Ayed, I., Galdran, A., and Dolz, J. The devil is in the margin: Margin-based label smoothing for network calibration. In IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2022.

Long, M., Cao, Z., Wang, J., and Jordan, M. I. Conditional adversarial domain adaptation. In Advances in Neural Information Processing Systems, 2018.

Maddox, W. J., Izmailov, P., Garipov, T., Vetrov, D. P., and Wilson, A. G. A simple baseline for Bayesian uncertainty in deep learning. In Advances in Neural Information Processing Systems, 2019.

Musgrave, K., Belongie, S., and Lim, S.-N. Benchmarking validation methods for unsupervised domain adaptation. arXiv preprint arXiv:2208.07360, 2(6):12, 2022.

Ovadia, Y., Fertig, E., Ren, J., Nado, Z., Sculley, D., Nowozin, S., Dillon, J., Lakshminarayanan, B., and Snoek, J. Can you trust your model’s uncertainty? Evaluating predictive uncertainty under dataset shift. In Advances in Neural Information Processing Systems, 2019.

Park, S., Bastani, O., Weimer, J., and Lee, I. Calibrated prediction with covariate shift via unsupervised domain adaptation. In International Conference on Artificial Intelligence and Statistics, 2020.

Park, S., Dobriban, E., Lee, I., and Bastani, O. PAC prediction sets under covariate shift. In International Conference on Learning Representations, 2022.

Peng, X., Usman, B., Kaushik, N., Hoffman, J., Wang, D., and Saenko, K. Visda: The visual domain adaptation challenge. arXiv preprint arXiv:1710.06924, 2017.

Peng, X., Bai, Q., Xia, X., Huang, Z., Saenko, K., and Wang, B. Moment matching for multi-source domain adaptation. In IEEE/CVF International Conference on Computer Vision, 2019.

Popoviciu, T. Sur certaines inegalit´ es qui caract´ erisent les´ fonctions convexes. Analele Stiintifice Univ.“Al. I. Cuza”, Iasi, Sectia Mat, 11:155–164, 1965.

Rahaman, R. et al. Uncertainty quantification and deep ensembles. In Advances in Neural Information Processing Systems, 2021.

Recht, B., Roelofs, R., Schmidt, L., and Shankar, V. Do Imagenet classifiers generalize to Imagenet? In International Conference on Machine Learning, 2019.

Russakovsky, O., Deng, J., Su, H., Krause, J., Satheesh, S., Ma, S., Huang, Z., Karpathy, A., Khosla, A., Bernstein, M., et al. Imagenet large scale visual recognition challenge. International Journal of Computer Vision, 115: 211–252, 2015.

Saito, K., Watanabe, K., Ushiku, Y., and Harada, T. Maximum classifier discrepancy for unsupervised domain adaptation. In IEEE Conference on Computer Vision and Pattern Recognition, 2018.

Saito, K., Kim, D., Teterwak, P., Sclaroff, S., Darrell, T., and Saenko, K. Tune it the right way: Unsupervised validation of domain adaptation via soft neighborhood density. In IEEE/CVF International Conference on Computer Vision, 2021.

Salvador, T., Voleti, V., Iannantuono, A., and Oberman, A. Frustratingly easy uncertainty estimation for distribution shift. arXiv preprint arXiv:2106.03762, 2021.

Sensoy, M., Kaplan, L., and Kandemir, M. Evidential deep learning to quantify classification uncertainty. In Advances in Neural Information Processing Systems, 2018.

Shi, Y. and Sha, F. Information-theoretical learning of discriminative clusters for unsupervised domain adaptation. In International Coference on Machine Learning, 2012.

Solaiman, I., Brundage, M., Clark, J., Askell, A., Herbert-Voss, A., Wu, J., Radford, A., Krueger, G., Kim, J. W., Kreps, S., et al. Release strategies and the social impacts of language models. arXiv preprint arXiv:1908.09203, 2019.

Stone, M. Asymptotics for and against cross-validation. Biometrika, pp. 29–35, 1977.

Sugiyama, M., Krauledat, M., and Muller, K.-R. Covariate¨ shift adaptation by importance weighted cross validation. Journal ofMachine Learning Research, 8(5), 2007.

Thulin, M. The cost of using exact confidence intervals for a binomial proportion. Electronic Journal of Statistics, 8: 817–840, 2014.

Tomani, C., Cremers, D., and Buettner, F. Parameterized temperature scaling for boosting the expressive power in post-hoc uncertainty calibration. In European Conference on Computer Vision, 2022.

Tu, W., Deng, W., Gedeon, T., and Zheng, L. Assessing model out-of-distribution generalization with softmax prediction probability baselines and a correlation method, 2023. URL https://openreview.net/forum? id=1maXoEyeqx.

Venkateswara, H., Eusebio, J., Chakraborty, S., and Panchanathan, S. Deep hashing network for unsupervised domain adaptation. In IEEE Conference on Computer Vision and Pattern Recognition, 2017.

Virtanen, P., Gommers, R., Oliphant, T. E., Haberland, M., Reddy, T., Cournapeau, D., Burovski, E., Peterson, P., Weckesser, W., Bright, J., van der Walt, S. J., Brett, M., Wilson, J., Millman, K. J., Mayorov, N., Nelson, A. R. J., Jones, E., Kern, R., Larson, E., Carey, C. J., Polat, <sup>˙</sup>I., Feng, Y., Moore, E. W., VanderPlas, J., Laxalde, D., Perktold, J., Cimrman, R., Henriksen, I., Quintero, E. A., Harris, C. R., Archibald, A. M., Ribeiro, A. H., Pedregosa, F., van Mulbregt, P., and SciPy 1.0 Contributors. SciPy 1.0: Fundamental algorithms for scientific computing in Python. Nature Methods, 17:261–272, 2020.

Wang, X., Long, M., Wang, J., and Jordan, M. Transferable calibration with lower bias and variance in domain adaptation. In Advances in Neural Information Processing Systems, 2020.

Yang, J., Qian, H., Xu, Y., Wang, K., and Xie, L. Can we evaluate domain adaptation models without targetdomain labels? In International Conference on Learning Representations, 2024.

You, K., Wang, X., Long, M., and Jordan, M. Towards accurate model selection in deep unsupervised domain adaptation. In International Conference on Machine Learning, 2019.

Yu, Y., Bates, S., Ma, Y., and Jordan, M. Robust calibration with multi-domain temperature scaling. In Advances in Neural Information Processing Systems, 2022.

Zhang, Y., Liu, T., Long, M., and Jordan, M. Bridging theory and algorithm for domain adaptation. In International Conference on Machine Learning, 2019.

## A. Proof of Claims

## A.1. Proof of Proposition 2.1

Proof. The proof consists of three parts: 1) decomposition of the expected mean-square error of an estimator $g ( x ) ; 2 )$ deriving MLEs of individual and group accuracies; 3) constructing a sufficient condition.

1) Bias-variance decomposition of the expected mean-square error The expected mean-square error of an estimator g(x) for $\beta ( x )$ at $x _ { i } \in \mathcal { G } _ { n } ^ { ( t ) }$ with respect to the realization of a label $y _ { i } \sim Y |$ |x can be decomposed by

$$
\mathbb {E} _ {D} [ (\hat {\beta} (x _ {i}) - g (x _ {i})) ^ {2} ] = V a r _ {D} (g (x _ {i}; D)) + (B i a s _ {D} (g (x _ {i}; D))) ^ {2} + \sigma_ {x _ {i}} ^ {2}\tag{17}
$$

where $V a r _ { D } ( g ( x _ { i } ; D ) ) : = \mathbb { E } _ { D } [ ( g ( x _ { i } ; D ) - \mathbb { E } _ { D } [ g ( x _ { i } ; D ) ] ) ^ { 2 } ]$ is the variance of the estimator and $B i a s _ { D } ( g ( x _ { i } ; D ) ) : =$ $\mathbb { E } _ { D } [ g ( x _ { i } ; D ) ] - \beta ( x )$ is the bias of the estimator.

2) MLEs of individual and group accuracy estimators For an individual accuracy estimator $\hat { \beta } ^ { ( i d ) } ( x ; D )$ that predicts an accuracy for each sample x given D, an MLE estimator is $\hat { \beta } ^ { ( i d ) } ( x ) = \hat { \beta } ( x )$ . This estimator is unbiased because $\mathbb { E } _ { D } ( \hat { \beta } ^ { ( i d ) } ( x ; D ) ) = \beta ( x )$ for each $x \in \mathcal { G } _ { n } ^ { ( t ) }$ . Therefore, this estimator has the average of expected errors

$$
\frac {1}{N _ {n}} \sum_ {k \in [ N _ {n} ]} \mathbb {E} _ {D} [ (\hat {\beta} (x _ {k}) - \hat {\beta} ^ {(i d)} (x _ {k}; D)) ^ {2} ] = \bar {\sigma} ^ {2} + \bar {\sigma} ^ {2}\tag{18}
$$

where $\begin{array} { r } { \bar { \sigma } ^ { 2 } : = \frac { 1 } { N _ { n } } \sum _ { i \in [ N _ { n } ] } \sigma _ { x _ { i } } ^ { 2 } } \end{array}$

For a group accuracy estimato $\hat { \beta } ^ { ( g r ) } ( x ; D )$ that predicts the same group accuracy estimate for all $x \in \mathcal { G } _ { n } ^ { ( t ) }$ , an MLE estimator can be defined by $\begin{array} { r } { \hat { \beta } ^ { ( g r ) } ( x ; D ) = \frac { 1 } { N _ { n } } \sum _ { i = 1 } ^ { N _ { n } } \hat { \beta } ( x _ { i } ) } \end{array}$ , which is a biased estimator because $\begin{array} { r } { \mathbb { E } _ { D } ( \hat { \beta } ^ { ( g r ) } ( x ; D ) ) = \frac { 1 } { N _ { n } } \sum _ { i = 1 } ^ { N _ { n } } \beta ( x _ { i } ) } \end{array}$ for each $x \in \mathcal { G } _ { n } ^ { ( t ) }$ . Therefore, this estimator has the average of expected error

$$
\frac {1}{N _ {n}} \sum_ {k \in [ N _ {n} ]} \mathbb {E} _ {D} [ (\hat {\beta} (x _ {k}) - \hat {\beta} ^ {(g r)} (x _ {k})) ^ {2} ] = \frac {1}{N _ {n}} \bar {\sigma} ^ {2} + \frac {1}{N _ {n}} \sum_ {k \in [ N _ {n} ]} (\frac {1}{N _ {n}} \sum_ {i \in [ N _ {n} ]} \beta (x _ {i}) - \beta (x _ {k})) ^ {2} + \bar {\sigma} ^ {2}\tag{19}
$$

$$
= \frac {1}{N _ {n}} \bar {\sigma} ^ {2} + V a r (\beta ; D) + \bar {\sigma} ^ {2}\tag{20}
$$

where $V a r ( \beta ; D )$ is the variance of the accuracy in group $\mathcal { G } _ { n } ^ { ( t ) }$

3) Sufficient condition Given (18) and (20), the Popoviciu’s inequality (Popoviciu, 1965) provides a sufficient condition for the group accuracy estimator $\hat { \beta } ^ { \left( g r \right) }$ to have a lower expected mean-squared error than the individual accuracy estimator $\hat { \beta } ^ { ( i d ) }$ as follows:

$$
V a r (\beta ; D) \leq \frac {1}{4} (\max _ {x ^ {\prime} \in \mathcal {G} _ {n} ^ {(t)}} \beta (x ^ {\prime}) - \min _ {x ^ {\prime} \in \mathcal {G} _ {n} ^ {(t)}} \beta (x ^ {\prime})) ^ {2} \leq \frac {N _ {n} - 1}{N _ {n}} \bar {\sigma} ^ {2} = \frac {N _ {n} - 1}{N _ {n}} (\frac {1}{N _ {n}} \sum_ {i \in [ N _ {n} ]} \beta (x _ {i}) (1 - \beta (x _ {i})))\tag{21}
$$

where the equality comes from $\begin{array} { r } { \bar { \sigma } ^ { 2 } = \frac { 1 } { N _ { n } } \sum _ { i \in \{ N _ { n } \} } \sigma _ { x _ { i } } ^ { 2 } } \end{array}$ with $\sigma _ { x _ { i } } ^ { 2 }$ is the variance of the Bernoulli distribution with a parameter $\beta ( x _ { i } )$ . □

## A.2. Sufficient Condition for (1)

To find the sufficient condition for (1), i.e., $\begin{array} { r } { \frac { 1 } { 4 } ( \operatorname* { m a x } _ { x ^ { \prime } \in \mathcal G _ { n } } \beta ( x ^ { \prime } ) - \operatorname* { m i n } _ { x ^ { \prime } \in \mathcal G _ { n } } \beta ( x ^ { \prime } ) ) ^ { 2 } \ \leq \ \frac { N _ { n } - 1 } { N _ { n } } \bar { \sigma } ^ { 2 } } \end{array}$ , note that $\bar { \sigma } ^ { 2 } \geq $ $\begin{array} { r } { \operatorname* { m i n } _ { x \in \mathcal G _ { n } } \sigma _ { x } ^ { 2 } = \tilde { \beta } ( 1 - \tilde { \beta } ) } \end{array}$ where $\begin{array} { r } { \tilde { \beta } = \operatorname* { m i n } \{ \operatorname* { m i n } _ { x ^ { \prime } \in \mathcal { G } _ { n } } \beta ( x ^ { \prime } ) , ( 1 - \operatorname* { m a x } _ { x ^ { \prime } \in \mathcal { G } _ { n } } \beta ( x ^ { \prime } ) ) \} } \end{array}$ . Therefore, the sufficient condition is $\begin{array} { r } { \operatorname* { m a x } _ { x ^ { \prime } \in \mathcal { G } _ { n } } \beta ( x ^ { \prime } ) - \operatorname* { m i n } _ { x ^ { \prime } \in \mathcal { G } _ { n } } \beta ( x ^ { \prime } ) \le 2 \cdot \sqrt { \frac { N _ { n } - 1 } { N _ { n } } \widetilde \beta } ( 1 - \widetilde \beta ) } \end{array}$ , which is described in Figure A1.

## A.3. Decomposition of the Expected Squared Calibration Error

Proposition A.1. The expected squared calibration error can be decomposed as the sum ofthe variance ofthe accuracies for samples in the same group and a squared group accuracy estimation error. That is,

$$
\mathbb {E} _ {p _ {T}} [ (P (Y = \hat {Y}) - \hat {\alpha} _ {T} (\mathcal {G} _ {I ^ {(g)} (X)} ^ {(t)})) ^ {2} ] = \sum_ {n \in [ M ]} P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)}) [ V a r (P (Y = \hat {Y}) | \mathcal {G} _ {n} ^ {(t)}) + (\alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}) - \hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)})) ^ {2} ]\tag{22}
$$

![](images/0932542ce6ae47ac789609200a86bc954e3a93e3340fee96eba6dbc8dd8961c9.jpg)  
Figure A1. The shaded area includes values of maximum and minimum expected accuracies within the group, which satisfy the sufficient condition for (1) when $N _ { n } = 1 0 0$

where $X _ { T }$ is a random variable having a density of p<sub>T</sub>.

Proof.

$$
\mathbb {E} _ {p _ {T}} [ (P (Y = \hat {Y}) - \hat {\alpha} _ {T} (\mathcal {G} _ {I ^ {(g)} (X)} ^ {(t)})) ^ {2} ] = \sum_ {n \in [ M ]} P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)}) \mathbb {E} _ {p _ {T}} [ (P (Y = \hat {Y}) - \hat {\alpha} _ {T} (\mathcal {G} _ {I ^ {(g)} (X)} ^ {(t)})) ^ {2} | X \in \mathcal {G} _ {n} ^ {(t)} ]\tag{23}
$$

$$
= \sum_ {n \in [ M ]} P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)}) \mathbb {E} _ {p _ {T}} [ (P (Y = \hat {Y}) - \alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}) + \alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}) - \hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)})) ^ {2} | X \in \mathcal {G} _ {n} ^ {(t)} ]\tag{24}
$$

$$
= \sum_ {n \in [ M ]} P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)}) \left(\mathbb {E} _ {p _ {T}} [ (P (Y = \hat {Y}) - \alpha_ {T} (\mathcal {G} _ {n} ^ {(t)})) ^ {2} | X \in \mathcal {G} _ {n} ^ {(t)} ] + (\alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}) - \hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)})) ^ {2}\right)\tag{25}
$$

$$
= \sum_ {n \in [ M ]} P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)}) [ V a r (P (Y = \hat {Y}) | \mathcal {G} _ {n} ^ {(t)}) + (\alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}) - \hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)})) ^ {2} ]\tag{26}
$$

where the equality (25) holds due to $\begin{array} { r } { \mathbb { E } _ { p _ { T } } [ ( P ( Y ( X ) = \hat { Y } ( X ) ) - \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ) ) ( \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ) - \hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ) ) | X \in \mathcal { G } _ { n } ^ { ( t ) } ] = 0 . } \end{array}$

## A.4. Proof of Proposition 3.1

Proof. By applying triangle inequalities, we get the following inequality:

$$
\begin{array}{r l} & {| \alpha_ {S} (\mathcal {G} _ {n} ^ {(t)}; w ^ {*}) - \alpha_ {S} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n)) | \leq | \alpha_ {S} (\mathcal {G} _ {n} ^ {(t)}; w ^ {*}) - \hat {\alpha} _ {S} ^ {(M C)} (\mathcal {G} _ {n} ^ {(t)}) | + | \hat {\alpha} _ {S} ^ {(M C)} (\mathcal {G} _ {n} ^ {(t)}) - \hat {\alpha} _ {S} ^ {(I W)} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n)) |} \\ & {\qquad + | \hat {\alpha} _ {S} ^ {(I W)} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n)) - \alpha_ {S} ^ {(I W)} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n)) | + | \alpha_ {S} ^ {(I W)} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n)) - \alpha_ {S} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n)) |.} \end{array}\tag{27}
$$

Note that the first and third terms in the right hand side are coming from the Monte-Carlo approximation, so they can be bounded by $\mathcal { O } ( \log ( 1 / \tilde { \delta } ) / | \mathcal { G } _ { n } ^ { ( t ) } ( \mathcal { D } _ { S } ) | )$ with probability at least $1 - \tilde { \delta }$ based on a concentration inequality such as the Hoeffding’s inequality. Also, the second term is bounded by the optimization error $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ ). Therefore, it is enough to analyze the fourth term.

The fourth term is coming from the bias of $\mathbb { E } _ { T _ { Y | X } } [ \mathbf { 1 } ( Y ( X ) = \hat { Y } ( X ) ) ] = \hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { \dag } ( n ) )$ ), which we refer to as the bias of the identical accuracy assumption. It can be bounded by

$$
| \alpha_ {S} ^ {(I W)} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n)) - \alpha_ {S} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n)) |\tag{28}
$$

$$
= \frac {P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)})}{P (X _ {S} \in \mathcal {G} _ {n} ^ {(t)})} \bigg | \mathbb {E} _ {p _ {T}} \left[ \frac {\mathbf {1} (Y (X) = \hat {Y} (X)) - \hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)} ; w ^ {\dagger} (n))}{w ^ {\dagger} (n) (X)} \big | \mathcal {G} _ {n} ^ {(t)} \right] \bigg |\tag{29}
$$

$$
\leq \frac {P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)})}{P (X _ {S} \in \mathcal {G} _ {n} ^ {(t)})} \left(\mathbb {E} _ {p _ {T}} \left[ (\mathbf {1} (Y (X) = \hat {Y} (X)) - \hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n))) ^ {2} | \mathcal {G} _ {n} ^ {(t)} \right] \mathbb {E} _ {p _ {T}} \left[ \frac {1}{w ^ {\dagger} (n) (X) ^ {2}} | \mathcal {G} _ {n} ^ {(t)} \right]\right) ^ {1 / 2}\tag{30}
$$

$$
\leq \frac {P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)})}{2 P (X _ {S} \in \mathcal {G} _ {n} ^ {(t)})} \left(\mathbb {E} _ {p _ {T}} \left[ (\mathbf {1} (Y (X) = \hat {Y} (X)) - \hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n))) ^ {2} | \mathcal {G} _ {n} ^ {(t)} \right] + \mathbb {E} _ {p _ {T}} \left[ \frac {1}{w ^ {\dagger} (n) (X) ^ {2}} | \mathcal {G} _ {n} ^ {(t)} \right]\right)\tag{31}
$$

$$
\leq \frac {P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)})}{2 P (X _ {S} \in \mathcal {G} _ {n} ^ {(t)})} \left(\mathbb {E} _ {p _ {T}} \left[ (\mathbf {1} (Y = \hat {Y}) - \hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)}; w ^ {\dagger} (n))) ^ {2} \mid \mathcal {G} _ {n} ^ {(t)} \right] + \frac {1}{\underline {{w}} ^ {\dagger} (n) ^ {2}}\right)\tag{32}
$$

where (30) holds due to the Cauchy-Schwarz inequality, (31) holds due to the AM-GM inequality, and $\underline { w } ^ { \dagger } ( n ) : =$ $\mathrm { m i n } _ { i \in [ 2 B ] } \{ w _ { i } ^ { \dagger } ( n ) \}$ □

## A.5. Formal Statement and Proof of Proposition A.2

Proposition A.2 (Bias-variance decomposition). Let $\hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } )$ be an estimate for $\alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { \ast } )$ . Then, the bias of the identical accuracy assumption is given by

$$
I d e n t B i a s (w ^ {\dagger} (n); \mathcal {G} _ {n} ^ {(t)}) = \frac {P (X _ {T} \in \mathcal {G} _ {n} ^ {(t)})}{2 P (X _ {S} \in \mathcal {G} _ {n} ^ {(t)})} \left(\frac {1}{\underline {{w}} ^ {\dagger} (n) ^ {2}} + B i a s (\hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)})) ^ {2} + V a r (\boldsymbol {I} (Y = \hat {Y}) | \mathcal {G} _ {n} ^ {(t)})\right)\tag{33}
$$

where $B i a s ( \hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ) ) : = | \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { * } ) - \hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ) |$ is the bias of the estimate $\hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } )$ and $V a r ( I ( Y = \hat { Y } ) | \mathcal { G } _ { n } ^ { ( t ) } ) : =$ $\mathbb { E } _ { p _ { T } } \left[ \left( I ( Y = \hat { Y } ) - \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { * } ) \right) ^ { 2 } | \mathcal { G } _ { n } ^ { ( t ) } \right]$ is the variance ofthe correctness ofpredictions in $\mathcal { G } _ { n } ^ { ( t ) }$

Proof. Based on the proof of Proposition 3.1, it is enough to decompose $\mathbb { E } _ { p _ { T } } [ ( \mathbf { 1 } ( Y ( X ) = \hat { Y } ( X ) ) - \hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ) ] ^ { 2 }$ as follows

$$
\mathbb {E} _ {p _ {T}} \left[ (\mathbf {1} (Y (X) = \hat {Y} (X)) - \hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)})) ^ {2} | \mathcal {G} _ {n} ^ {(t)} \right]\tag{34}
$$

$$
= \mathbb {E} _ {p _ {T}} \left[ (\mathbf {1} (Y (X) = \hat {Y} (X)) - \alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}; w ^ {*}) + \alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}; w ^ {*}) - \hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)})) ^ {2} | \mathcal {G} _ {n} ^ {(t)} \right]\tag{35}
$$

$$
= \mathbb {E} _ {p _ {T}} \left[ (\mathbf {1} (Y (X) = \hat {Y} (X)) - \alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}; w ^ {*})) ^ {2} + (\alpha_ {T} (\mathcal {G} _ {n} ^ {(t)}; w ^ {*}) - \hat {\alpha} _ {T} (\mathcal {G} _ {n} ^ {(t)})) ^ {2} | \mathcal {G} _ {n} ^ {(t)} \right]\tag{36}
$$

where the equality (36) holds due to $\mathbb { E } _ { p _ { T _ { X } } } \mathbb { E } _ { p _ { T _ { Y } | X } } [ ( { \mathbf { 1 } } ( Y ( X ) = \hat { Y } ( X ) ) - \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { * } ) ) ( \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { * } ) - \hat { \alpha } _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ) ) | \mathcal { G } _ { n } ^ { ( t ) } ] = \mathbb { E } _ { p _ { T _ { X } } } [ ( { \mathbf { 1 } } ( Y ( X ) = \hat { Y } ( X ) ) - \alpha _ { T } ( \mathcal { G } _ { n } ^ { ( t ) } ; w ^ { * } ) ) ] .$ 0. □

## B. Discussions

## B.1. Model Calibration in the I.I.D. Settings

In a classification problem, the maximum value of the softmax output is often considered as a confidence of a neura network’s prediction. In (Guo et al., 2017), it is shown that the modern neural networks are poorly calibrated, tending to produce larger confidences than their accuracies. Based on this observation, (Guo et al., 2017) introduce a post-processing approach that adjusts a temperature parameter of the softmax function for adjusting the overall confidence level. In Bayesian approaches (such as Monte-Carlo dropout (Gal & Ghahramani, 2016; Gal et al., 2017), deep ensemble (Lakshminarayanan et al., 2017; Rahaman et al., 2021), and a last-layer Bayesian approach (Sensoy et al., 2018; Joo et al., 2020)), the confidence level adjustment is induced by posterior inference and model averaging. While both post-hoc calibration methods and Bayesian methods have been achieving impressive calibration performances in the i.i.d. setting (Maddox et al., 2019; Ovadia et al., 2019; Ebrahimi et al., 2020), it has been shown that most of the calibration improvement methods fall short under distribution shifts (Ovadia et al., 2019).

## B.2. On Choice of Non-Parametric Estimators

Our concept of determining the IW from its CI can be applied to any other valid CI estimators. For example, by analyzing a CI of the odds ratio of the logistic regression used as a domain classifier (Bickel et al., 2007; Park et al., 2020; Salvador et al., 2021), a CI of the IW can be obtained. Then, IW-GAE can be applied in the same way as developed in Section 3. As an extreme example, we apply IW-GAE by setting minimum and maximum values of IWs as CIs in an ablation study (Table

4). While IW-GAE outperforms strong baseline methods (CPCS and TransCal) even under this naive CI estimation, we observe that its performance is reduced compared to the setting with a sophisticated CI estimation (Park et al., 2022). In this regard, advancements in IW estimation or CI estimation would be beneficial for accurately estimating the group accuracy, thereby model selection and uncertainty estimation. Therefore, we leave combining IW-GAE with advanced IW estimation techniques as an important future direction of research.

## B.3. On Choice of the Number of Groups

In this work, we estimate the group accuracy by grouping predictions based on the confidence of the prediction. Therefore, a natural question to ask is how to select the number of groups. If we use a small number of groups, then there would be high $I d e n t B i a s ( w ^ { \dagger } ; \mathcal { G } _ { n } ^ { ( t ) } )$ because of the large variance of prediction correctness within a group. In addition, reporting the same accuracy estimate for a large number of predictions could be inaccurate in terms of representing uncertainty for individual predictions. Conversely, if we use a large number of bins, there would be high Monte-Carlo approximation errors, $\epsilon _ { s t a t } .$ Therefore, it would result in a loose connection between the source group accuracy estimation error and the objective in the optimization problem (cf. Proposition 3.1). Based on our experimental results with $M = 1 0$ and the sensitivity analysis (cf. Section 4.4), we would recommend to choose M from its standard range [10, 20] in the literature.

## C. Additional Details

## C.1. Obtaining CIs of Binned IWs

In this work, we use a recently proposed nonparametric estimation method (Park et al., 2022) for constructing the CI of the $\mathrm { I W } ^ { 1 }$ . In this approach, X is partitioned into B number of bins $( { \mathcal { X } } = \cup _ { i = 1 } ^ { B } B _ { i } )$ where $B _ { i } = \{ x \in \mathcal { X } | I ^ { ( B ) } ( x ) = i \}$ . Here, the partition function is defined such that $\begin{array} { r } { I ^ { ( B ) } ( x ) = j \mathrm { ~ i f ~ } q ( \frac { j - 1 } { B } ; \mathcal { W } ) < \tilde { w } \bar { ( x ) } \leq q ( \frac { j } { B } ; \mathcal { W } ) } \end{array}$ where $\mathcal { W } : = \{ \tilde { w } ( x ) | x \in \mathcal { D } _ { S } \cup \mathcal { D } _ { T } \}$ and w˜ is a rough estimate of IW (cf. Appendix C.2).

Then, confidence intervals (CIs) of the binned probabilities $\bar { p } _ { S } ( x ) = \bar { p } _ { S _ { I } ( B ) } { } _ { ( x ) }$ with $\begin{array} { r } { \bar { p } _ { S _ { j } } = \int _ { B _ { j } } p _ { S } ( x ) d x } \end{array}$ and ${ \bar { p } } _ { T } ( x ) =$ $\bar { p } _ { T _ { I } ( B ) _ { \left( x \right) } }$ with $\begin{array} { r } { \bar { p } _ { T _ { j } } ~ = ~ \int _ { \mathcal { B _ { i } } } p _ { T } ( x ) d x } \end{array}$ are constructed. Specifically, for $\bar { p } _ { S _ { j } }$ , the number of samples in a bin $n _ { j } ^ { ( S ) } : =$ $\textstyle \sum _ { i = 1 } ^ { N ^ { ( S ) } } \mathbf { 1 } ( x _ { i } ^ { ( S ) } \ \in \ B _ { j } )$ is interpreted as a sample from Binom $( N ^ { ( S ) } , \bar { p } _ { S _ { i } } )$ . Then, the Clopper–Pearson CI (Clopper & Pearson, 1934) provides the CI of $\bar { p } _ { S _ { \ i } }$ as ${ \underline { { \theta } } } _ { S } ( n _ { j } ^ { ( S ) } ; N ^ { ( S ) } , \delta / 2 ) \le { \bar { p } } _ { S _ { j } } \le { \bar { \theta } } _ { S } ( n _ { j } ^ { ( S ) } ; N ^ { ( S ) } , \delta / 2 )$ with probability at least $1 - \delta$ where ${ \bar { \theta } } ( k ; m , \delta ) : = \operatorname* { i n f } \{ \theta \in [ 0 , 1 ] | F ( k ; m , \bar { \theta } ) \leq \delta \}$ and $\underline { { \theta } } ( k ; m , \delta ) : = \operatorname* { s u p } \{ \theta \in [ 0 , 1 ] | F ( k ; m , \theta ) \geq \delta \}$ with $F$ being <sup>¯</sup>the cumulative distribution function of the binomial distribution. Similarly, we can obtain the CIs of $\bar { p } _ { T _ { i } }$ by collecting $\begin{array} { r } { n _ { j } ^ { ( T ) } : = \sum _ { i \in [ N ^ { ( T ) } ] } \mathbf { 1 } ( x _ { i } ^ { ( T ) } \in \mathcal { B } _ { j } ) } \end{array}$ and following the same procedure, which are denoted as $\underline { { \theta } } _ { T } ( n _ { j } ^ { ( T ) } ; N ^ { ( T ) } , \delta / 2 )$ and $\bar { \theta } _ { T } ( n _ { j } ^ { ( T ) } ; N ^ { ( T ) } , \delta / 2 )$

With the CIs of $p _ { S _ { j } }$ and $p _ { T _ { \mathcal { I } } }$ for $j \in [ B ]$ , the CI of the IW in $B _ { j }$ can be obtained. Specifically, for $\bar { \delta } : = \delta / 2 B$ , the following inequality holds with probability at least $1 - \delta$ (Park et al., 2022):

$$
\frac {[ \underline {{\theta}} _ {T} (n _ {j} ^ {(T)} ; N ^ {(T)} , \bar {\delta}) - G ] ^ {+}}{\bar {\theta} _ {S} (n _ {j} ^ {(S)} ; N ^ {(S)} , \bar {\delta}) + G} \leq w _ {j} ^ {*} := \frac {\bar {p} _ {T _ {j}}}{\bar {p} _ {S _ {j}}} \leq \frac {\bar {\theta} _ {T} (n _ {j} ^ {(T)} ; N ^ {(T)} , \bar {\delta}) + G}{[ \underline {{\theta}} _ {S} (n _ {j} ^ {(S)} ; N ^ {(S)} , \bar {\delta}) - G ] ^ {+}}\tag{37}
$$

where $[ a ] ^ { + } : = \operatorname* { m a x } \{ 0 , a \}$ and $G \in \mathbb { R } _ { + }$ is a constant that satisfies $\begin{array} { r } { \int _ { \mathcal { B } _ { i } } | p _ { S } ( x ) - p _ { S } ( x ^ { \prime } ) | d x ^ { \prime } \leq G } \end{array}$ and $\int _ { B _ { i } } \left| p _ { T } ( x ) \right. -$ $p _ { T } ( x ^ { \prime } ) | d x ^ { \prime } \leq G$ for all $\boldsymbol { x } \in B _ { j }$ and $j \in [ B ]$ . We refer to $\{ w _ { i } ^ { * } \} _ { i \in B }$ as binned IWs. Also, we define the CI of $\boldsymbol { w _ { j } ^ { * } }$ as

$$
\Phi_ {j} := \left[ \frac {[ \underline {{\theta}} _ {T} (n _ {j} ^ {(T)} ; N ^ {(T)} , \bar {\delta}) - G ] ^ {+}}{\bar {\theta} _ {S} (n _ {j} ^ {(S)} ; N ^ {(S)} , \bar {\delta}) + G}, \frac {\bar {\theta} _ {T} (n _ {j} ^ {(T)} ; N ^ {(T)} , \bar {\delta}) + G}{[ \underline {{\theta}} _ {S} (n _ {j} ^ {(S)} ; N ^ {(S)} , \bar {\delta}) - G ] ^ {+}} \right].\tag{38}
$$

## C.2. IW Estimator

IW estimation is required for implementing baseline methods and construct bins for estimating the CI of the IW. We adopt a logistic regression model on top of the neural network’s representation as the discriminative learning-based estimation (Bickel et al., 2007), following Wang et al. (2020). Specifically, it first upsamples from one domain to make $| \mathcal { D } _ { S } | = | \mathcal { D } _ { T } |$ and then it labels samples with the domain index: $\{ ( h ( x ) , 1 ) | x \in \mathcal { D } _ { T } \}$ and $\{ ( h ( x ) , 0 ) | x \in \mathcal { D } _ { S } \}$ where h is the feature map of the neural network. After training the logistic regression model v with a quasi-Newton method until convergence, the IW can be estimated as $\tilde { w } ( x ) = v ( h ( x ) ) / ( 1 - v ( h ( x ) ) )$ ).

## C.3. Algorithm

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Pseudocode of IW-GAE

Input: Source dataset $\mathcal{D}_S = \{(x_i^{(S)}, y_i^{(S)})\}_{i=1}^{N(S)}$, Target dataset $\mathcal{D}_T = \{x_i^{(T)}\}_{i \in [N(T)]}$

Hyperparameters: The numbers of bins and groups (B and M), level of CI $\bar{\delta}$, search space $\mathcal{T}$

# Prepare a UDA model (Wang et al., 2020)

Partition $\mathcal{D}_S$ into $\mathcal{D}_S^{tr}$ and $\mathcal{D}_S^{val}$

Train a neural network $g$ on $(\mathcal{D}_S^{tr}, \mathcal{D}_T)$ with any UDA method

Upsample $\mathcal{D}_S^{tr}$ or $\mathcal{D}_T$ to make $|\mathcal{D}_S^{tr}| = |\mathcal{D}_T|$

Compute $\mathcal{F}_S^{tr} = \{g(x) | x \in \mathcal{D}_S^{tr}\}$, $\mathcal{F}_S^{val} = \{g(x) | x \in \mathcal{D}_S^{val}\}$, and $\mathcal{F}_T = \{g(x) | x \in \mathcal{D}_T\}$

Train a logistic regression model $H$ that discriminates $\mathcal{F}_S^{tr}$ and $\mathcal{F}_T$

# Obtain CIs of binned IWs (Park et al., 2022)

Gather IWs $\mathcal{W}_{S \cup T} = \{(1 - H(g(x))) / H(g(x)) : x \in \mathcal{D}_S^{val} \cup \mathcal{D}_T\}$

Compute quantiles $q(i) = i / (B + 1)$-th quantile of $\mathcal{W}_{S \cup T}$ for $i \in [B + 1]$

Construct bins $\mathcal{B}_i = \{x \in \mathcal{D}_S^{val} \cup \mathcal{D}_T : q(i) \leq (1 - H(g(x))) / H(g(x)) \leq q(i + 1)\}$ for $i \in [B]$

Compute $\Phi_i$ using (37) for each $i \in [B]$

# IW-GAE

$f^\dagger = \infty$

for $t \in \mathcal{T}$ do

Obtain $w(n; t)$ by solving the optimization problem in (8)-(13) for $n \in [M]$

if $\sum_{n \in [M]} \left( \hat{\alpha}_S^{(MC)}(\mathcal{G}_n^{(t)}) - \hat{\alpha}_S^{(IW)}(\mathcal{G}_n^{(t)}; w(n; t)) \right)^2 \leq f^\dagger$ then

$f^\dagger = \sum_{n \in [M]} \left( \hat{\alpha}_S^{(MC)}(\mathcal{G}_n^{(t)}) - \hat{\alpha}_S^{(IW)}(\mathcal{G}_n^{(t)}; w(n; t)) \right)^2$ $t^\dagger = t$ $w^\dagger(n; t^\dagger) = w(n; t)$ for $n \in [M]$

end if

end for
</div>

## D. Experimental Details

We follow the exact same training configurations as those used in the Transfer Learning Library (Jiang et al., 2020), except we separate 20% as the validation dataset from the source domain (in the original implementation, validation is performed with the test dataset for OfficeHome). The configuration of training MDD for OfficeHome is as follows: MDD is trained for 30 epochs with SGD with momentum parameter 0.9 and weight decay of 0.0005. The learning rate is schedule by $\alpha \cdot ( 1 + \gamma \cdot t ) ^ { - \eta }$ where t is the iteration counter, $\alpha = 0 . 0 0 4 , \gamma = 0 . 0 0 0 2 , \eta = 0 . 7 5$ , and the stochastic gradient is computed with minibatch of 32 samples from the source domain and 32 samples from the target domain. Also, it uses the margin coefficient of 4 as the MDD-specific hyperparamter. For the model architecture, it uses ResNet-50 pre-trained on ImageNet (Russakovsky et al., 2015) with the bottleneck dimension of 2,048. For the large-scale VisDa-2017, only the architecture is changed to ResNet-101 with the bottleneck dimension of 1,024 under the same training configuration.

IW-GAE specific details For CI estimation, we follow the same configuration with the original method (Park et al., 2022). Specifically, we use constant $G = 0 . 0 0 1$ , CI level $\bar { \delta } = 0 . 0 5$ , and the number of bins $B = 1 0$ . In addition, we use the maximum IW value $\tilde { w } _ { n } ^ { ( u b ) } = 6 . 0$ and the minimum IW value $\underline { w } ^ { \dagger } ( n ) = 1 / 6$ for $n \in [ M ] .$ , which is a common technique in IW-based estimations (Wang et al., 2020; Park et al., 2022). For the constraint relaxation constants in IW-GAE, we use $\delta _ { t o l } = 0 . 1$ and $\delta _ { p r } = 0 . 3$ . For implementing sequential least square programming, we use the SciPy Library (Virtanen et al., 2020) with tolerance $1 0 ^ { - 8 }$ that is used to check a convergence condition (other optimizer-specific values follow the default values in SciPy) and choose the middle points from CIs of binned IW as an initial solution.

## E. Missing Tables

Table A1. Model calibration benchmark results of MDD with ResNet-50 on Office-Home. We repeat experiments for ten times and report the average value of ECE.

<table><tr><td>Method</td><td>Ar-Cl</td><td>Ar-Pr</td><td>Ar-Rw</td><td>Cl-Ar</td><td>Cl-Pr</td><td>Cl-Rw</td><td>Pr-Ar</td><td>Pr-Cl</td><td>Pr-Rw</td><td>Rw-Ar</td><td>Rw-Cl</td><td>Rw-Pr</td><td>Avg</td></tr><tr><td>Vanilla</td><td>40.61</td><td>25.62</td><td>15.56</td><td>33.83</td><td>25.34</td><td>24.75</td><td>33.45</td><td>38.62</td><td>16.76</td><td>23.37</td><td>36.51</td><td>14.01</td><td>27.37</td></tr><tr><td>TS</td><td>35.86</td><td>22.84</td><td>10.60</td><td>28.24</td><td>20.74</td><td>20.06</td><td>32.47</td><td>37.20</td><td>14.89</td><td>18.36</td><td>34.62</td><td>12.28</td><td>24.01</td></tr><tr><td>CPCS</td><td>22.93</td><td>22.07</td><td>10.19</td><td>26.88</td><td>18.36</td><td>14.05</td><td>28.28</td><td>29.20</td><td>12.06</td><td>15.76</td><td>26.54</td><td>11.14</td><td>19.79</td></tr><tr><td>IW-TS</td><td>32.63</td><td>22.90</td><td>11.27</td><td>28.05</td><td>19.65</td><td>18.67</td><td>30.77</td><td>38.46</td><td>15.10</td><td>17.69</td><td>32.20</td><td>11.77</td><td>23.26</td></tr><tr><td>TransCal</td><td>33.57</td><td>20.27</td><td>8.88</td><td>26.36</td><td>18.81</td><td>18.42</td><td>27.35</td><td>29.86</td><td>10.48</td><td>16.17</td><td>29.90</td><td>10.00</td><td>20.84</td></tr><tr><td>PTS</td><td>31.91</td><td>24.36</td><td>10.65</td><td>22.81</td><td>20.42</td><td>15.92</td><td>26.55</td><td>39.34</td><td>12.38</td><td>21.83</td><td>26.31</td><td>10.44</td><td>21.91</td></tr><tr><td>AvUTS</td><td>29.59</td><td>25.55</td><td>10.40</td><td>31.81</td><td>26.06</td><td>26.15</td><td>37.10</td><td>46.04</td><td>20.75</td><td>27.70</td><td>41.27</td><td>15.61</td><td>28.17</td></tr><tr><td>IW-Mid</td><td>23.25</td><td>31.62</td><td>12.99</td><td>17.15</td><td>18.71</td><td>9.23</td><td>27.75</td><td>30.35</td><td>9.02</td><td>13.64</td><td>26.32</td><td>10.60</td><td>19.22</td></tr><tr><td>IW-GAE</td><td>12.78</td><td>4.70</td><td>12.93</td><td>7.52</td><td>4.42</td><td>4.11</td><td>9.50</td><td>17.49</td><td>8.40</td><td>7.62</td><td>9.52</td><td>8.14</td><td>8.93</td></tr><tr><td>Oracle</td><td>10.45</td><td>10.72</td><td>6.47</td><td>8.10</td><td>7.62</td><td>6.55</td><td>11.88</td><td>9.39</td><td>5.93</td><td>7.54</td><td>10.72</td><td>5.70</td><td>8.42</td></tr></table>

Table A2. Large-scale model calibration benchmark results of CDAN with ResNet-50 on DomainNet. The numbers indicate the mean ECE across ten repetitions. Cl, Pt, Rw, and Sk correspond to clipart, painting, real, and sketch, respectively.

<table><tr><td>Method</td><td>Cl-Pt</td><td>Cl-Rw</td><td>Cl-Sk</td><td>Pt-Cl</td><td>Pt-Rw</td><td>Pt-Sk</td><td>Rw-Cl</td><td>Rw-Pt</td><td>Rw-Sk</td><td>Sk-Cl</td><td>Sk-Pt</td><td>Sk-Rw</td><td>Avg</td></tr><tr><td>Vanilla</td><td>13.23</td><td>6.36</td><td>12.92</td><td>9.75</td><td>6.35</td><td>15.56</td><td>9.44</td><td>9.70</td><td>14.34</td><td>6.63</td><td>11.25</td><td>5.23</td><td>10.06</td></tr><tr><td>TS</td><td>12.95</td><td>5.95</td><td>13.32</td><td>6.40</td><td>3.90</td><td>11.07</td><td>8.64</td><td>10.49</td><td>16.08</td><td>3.17</td><td>5.58</td><td>13.09</td><td>9.22</td></tr><tr><td>CPCS</td><td>5.64</td><td>21.90</td><td>7.70</td><td>5.14</td><td>7.72</td><td>7.90</td><td>9.35</td><td>11.17</td><td>17.06</td><td>3.46</td><td>2.23</td><td>15.90</td><td>9.60</td></tr><tr><td>IW-TS</td><td>16.76</td><td>16.70</td><td>12.53</td><td>5.29</td><td>7.84</td><td>4.34</td><td>9.60</td><td>10.58</td><td>16.80</td><td>5.40</td><td>2.98</td><td>17.11</td><td>10.49</td></tr><tr><td>TransCal</td><td>18.51</td><td>29.63</td><td>20.92</td><td>23.02</td><td>31.83</td><td>17.58</td><td>27.88</td><td>28.83</td><td>20.31</td><td>31.66</td><td>23.06</td><td>31.46</td><td>25.39</td></tr><tr><td>IW-Mid</td><td>7.61</td><td>11.01</td><td>5.89</td><td>8.84</td><td>7.58</td><td>5.36</td><td>8.70</td><td>7.49</td><td>7.53</td><td>10.24</td><td>8.10</td><td>10.21</td><td>8.21</td></tr><tr><td>IW-GAE</td><td>6.06</td><td>8.15</td><td>5.38</td><td>7.45</td><td>3.89</td><td>3.94</td><td>7.01</td><td>5.58</td><td>6.73</td><td>6.80</td><td>6.82</td><td>8.00</td><td>6.32</td></tr><tr><td>Oracle</td><td>4.55</td><td>2.78</td><td>4.01</td><td>3.10</td><td>3.72</td><td>2.72</td><td>3.10</td><td>2.79</td><td>2.83</td><td>3.13</td><td>1.70</td><td>1.77</td><td>3.02</td></tr></table>

Table A3. Hyperparameter selection benchmark results of MDD with ResNet-50 on Office-Home. We repeat experiments for ten times and report the average test accuracy of selected model.

<table><tr><td>Method</td><td>Ar-Cl</td><td>Ar-Pr</td><td>Ar-Rw</td><td>Cl-Ar</td><td>Cl-Pr</td><td>Cl-Rw</td><td>Pr-Ar</td><td>Pr-Cl</td><td>Pr-Rw</td><td>Rw-Ar</td><td>Rw-Cl</td><td>Rw-Pr</td><td>Avg</td></tr><tr><td>Vanilla</td><td>53.31</td><td>70.96</td><td>77.44</td><td>59.70</td><td>65.17</td><td>69.96</td><td>57.07</td><td>50.95</td><td>74.75</td><td>68.81</td><td>57.11</td><td>80.13</td><td>65.45</td></tr><tr><td>IWCV</td><td>53.24</td><td>69.61</td><td>72.50</td><td>59.70</td><td>65.17</td><td>67.50</td><td>57.07</td><td>55.21</td><td>74.75</td><td>68.81</td><td>58.51</td><td>80.13</td><td>65.18</td></tr><tr><td>DEV</td><td>53.31</td><td>70.72</td><td>77.44</td><td>59.79</td><td>67.99</td><td>69.96</td><td>57.07</td><td>52.50</td><td>77.12</td><td>70.50</td><td>53.38</td><td>82.27</td><td>66.00</td></tr><tr><td>InfoMax</td><td>54.34</td><td>70.96</td><td>77.53</td><td>61.48</td><td>69.93</td><td>71.06</td><td>62.79</td><td>54.41</td><td>78.79</td><td>71.32</td><td>58.51</td><td>82.36</td><td>67.79</td></tr><tr><td>SND</td><td>44.55</td><td>68.14</td><td>75.57</td><td>58.86</td><td>66.04</td><td>66.46</td><td>61.13</td><td>53.20</td><td>70.38</td><td>62.54</td><td>56.15</td><td>80.20</td><td>63.60</td></tr><tr><td>Corr-C</td><td>50.88</td><td>70.96</td><td>78.47</td><td>60.74</td><td>68.60</td><td>71.06</td><td>62.79</td><td>54.41</td><td>78.79</td><td>71.32</td><td>58.51</td><td>82.36</td><td>67.41</td></tr><tr><td>TransScore</td><td>54.34</td><td>70.96</td><td>77.53</td><td>61.48</td><td>69.93</td><td>71.06</td><td>62.79</td><td>54.41</td><td>78.79</td><td>71.32</td><td>58.51</td><td>82.36</td><td>67.87</td></tr><tr><td>MixVal</td><td>54.34</td><td>70.09</td><td>77.43</td><td>60.74</td><td>59.34</td><td>70.17</td><td>61.00</td><td>55.21</td><td>78.35</td><td>71.32</td><td>57.89</td><td>82.36</td><td>66.52</td></tr><tr><td>IW-Mid</td><td>54.13</td><td>69.27</td><td>78.47</td><td>61.48</td><td>68.03</td><td>71.06</td><td>59.99</td><td>55.21</td><td>78.79</td><td>70.50</td><td>57.11</td><td>83.10</td><td>67.26</td></tr><tr><td>IW-GAE</td><td>54.34</td><td>70.96</td><td>78.47</td><td>61.48</td><td>69.93</td><td>71.06</td><td>62.79</td><td>55.21</td><td>78.79</td><td>70.50</td><td>58.51</td><td>83.31</td><td>67.95</td></tr><tr><td>Lower bound</td><td>52.51</td><td>69.27</td><td>72.50</td><td>59.70</td><td>65.17</td><td>67.50</td><td>57.07</td><td>50.95</td><td>74.75</td><td>68.81</td><td>50.90</td><td>80.13</td><td>64.10</td></tr><tr><td>Oracle</td><td>54.34</td><td>70.96</td><td>78.47</td><td>61.48</td><td>69.93</td><td>71.06</td><td>62.79</td><td>55.21</td><td>78.79</td><td>71.32</td><td>58.51</td><td>83.31</td><td>68.01</td></tr></table>

Table A4. Checkpoint selection benchmark results of MDD with ResNet-50 on Office-Home. We repeat experiments for ten times and report the average test accuracy of selected model.

<table><tr><td>Method</td><td>Ar-Cl</td><td>Ar-Pr</td><td>Ar-Rw</td><td>Cl-Ar</td><td>Cl-Pr</td><td>Cl-Rw</td><td>Pr-Ar</td><td>Pr-Cl</td><td>Pr-Rw</td><td>Rw-Ar</td><td>Rw-Cl</td><td>Rw-Pr</td><td>Avg</td></tr><tr><td>Vanilla</td><td>47.22</td><td>74.14</td><td>77.76</td><td>61.85</td><td>70.96</td><td>71.59</td><td>60.98</td><td>53.63</td><td>78.93</td><td>71.57</td><td>57.04</td><td>83.96</td><td>67.47</td></tr><tr><td>IWCV</td><td>54.46</td><td>74.22</td><td>72.27</td><td>61.48</td><td>70.49</td><td>70.62</td><td>61.30</td><td>51.13</td><td>78.37</td><td>72.94</td><td>58.43</td><td>84.00</td><td>67.48</td></tr><tr><td>DEV</td><td>54.04</td><td>73.94</td><td>78.16</td><td>61.52</td><td>63.19</td><td>70.70</td><td>60.43</td><td>53.63</td><td>78.93</td><td>71.57</td><td>58.62</td><td>83.89</td><td>67.39</td></tr><tr><td>InfoMax</td><td>54.32</td><td>74.72</td><td>77.90</td><td>62.79</td><td>71.03</td><td>71.47</td><td>61.39</td><td>53.15</td><td>78.75</td><td>72.89</td><td>58.53</td><td>83.94</td><td>68.38</td></tr><tr><td>SND</td><td>47.67</td><td>73.06</td><td>77.71</td><td>62.67</td><td>70.47</td><td>71.17</td><td>61.43</td><td>52.14</td><td>78.75</td><td>70.71</td><td>57.66</td><td>79.80</td><td>67.23</td></tr><tr><td>Corr-C</td><td>54.46</td><td>74.72</td><td>77.53</td><td>61.76</td><td>70.88</td><td>71.24</td><td>61.30</td><td>52.47</td><td>78.40</td><td>72.59</td><td>58.53</td><td>83.89</td><td>68.24</td></tr><tr><td>TransScore</td><td>54.79</td><td>74.14</td><td>77.77</td><td>61.76</td><td>70.97</td><td>71.48</td><td>61.17</td><td>53.15</td><td>78.93</td><td>72.89</td><td>58.53</td><td>83.89</td><td>68.38</td></tr><tr><td>MixVal</td><td>54.45</td><td>74.35</td><td>77.77</td><td>61.93</td><td>70.70</td><td>71.43</td><td>61.30</td><td>53.29</td><td>78.93</td><td>72.89</td><td>58.53</td><td>83.89</td><td>68.37</td></tr><tr><td>IW-Mid</td><td>54.04</td><td>72.63</td><td>78.37</td><td>62.05</td><td>71.28</td><td>71.45</td><td>61.25</td><td>54.39</td><td>79.07</td><td>73.19</td><td>58.75</td><td>80.06</td><td>68.04</td></tr><tr><td>IW-GAE</td><td>54.32</td><td>73.98</td><td>78.51</td><td>61.96</td><td>71.25</td><td>71.70</td><td>61.10</td><td>54.30</td><td>78.91</td><td>73.22</td><td>58.70</td><td>83.86</td><td>68.48</td></tr><tr><td>Lower bound</td><td>41.90</td><td>64.88</td><td>72.27</td><td>52.00</td><td>58.48</td><td>62.13</td><td>53.52</td><td>38.33</td><td>70.92</td><td>63.41</td><td>44.81</td><td>75.83</td><td>58.21</td></tr><tr><td>Oracle</td><td>54.80</td><td>74.79</td><td>78.61</td><td>62.79</td><td>71.59</td><td>72.18</td><td>61.64</td><td>54.64</td><td>79.44</td><td>73.42</td><td>59.43</td><td>84.12</td><td>68.95</td></tr></table>

Table A5. Model calibration benchmark results of CDAN with ResNet-50 on Office-Home. The numbers indicate the mean ECE across ten repetitions.

<table><tr><td>Method</td><td>Ar-Cl</td><td>Ar-Pr</td><td>Ar-Rw</td><td>Cl-Ar</td><td>Cl-Pr</td><td>Cl-Rw</td><td>Pr-Ar</td><td>Pr-Cl</td><td>Pr-Rw</td><td>Rw-Ar</td><td>Rw-Cl</td><td>Rw-Pr</td><td>Avg</td></tr><tr><td>Vanilla</td><td>30.73</td><td>18.38</td><td>14.37</td><td>25.63</td><td>22.44</td><td>19.10</td><td>27.54</td><td>36.72</td><td>12.48</td><td>19.93</td><td>31.12</td><td>10.88</td><td>22.44</td></tr><tr><td>TS</td><td>29.68</td><td>19.40</td><td>14.40</td><td>22.15</td><td>19.97</td><td>16.88</td><td>28.82</td><td>38.03</td><td>12.99</td><td>20.46</td><td>31.91</td><td>11.83</td><td>22.21</td></tr><tr><td>CPCS</td><td>18.78</td><td>18.09</td><td>14.74</td><td>22.18</td><td>20.74</td><td>16.33</td><td>29.30</td><td>34.92</td><td>11.92</td><td>20.99</td><td>31.41</td><td>11.07</td><td>20.87</td></tr><tr><td>IW-TS</td><td>12.38</td><td>16.79</td><td>14.85</td><td>21.75</td><td>20.06</td><td>16.92</td><td>29.30</td><td>38.84</td><td>13.30</td><td>20.82</td><td>31.10</td><td>11.37</td><td>20.62</td></tr><tr><td>TransCal</td><td>7.94</td><td>14.05</td><td>12.91</td><td>7.82</td><td>9.25</td><td>10.23</td><td>9.37</td><td>12.60</td><td>14.29</td><td>9.92</td><td>9.76</td><td>17.51</td><td>11.30</td></tr><tr><td>IW-Mid</td><td>36.05</td><td>47.70</td><td>26.82</td><td>21.08</td><td>22.95</td><td>21.55</td><td>18.88</td><td>28.99</td><td>15.39</td><td>21.16</td><td>28.16</td><td>25.27</td><td>26.17</td></tr><tr><td>IW-GAE</td><td>13.98</td><td>29.82</td><td>9.44</td><td>6.55</td><td>5.59</td><td>10.16</td><td>5.29</td><td>13.47</td><td>11.01</td><td>11.12</td><td>7.26</td><td>9.84</td><td>11.13</td></tr><tr><td>Oracle</td><td>7.91</td><td>8.80</td><td>6.05</td><td>7.57</td><td>7.93</td><td>6.76</td><td>9.07</td><td>9.14</td><td>4.04</td><td>7.16</td><td>9.19</td><td>5.65</td><td>7.44</td></tr></table>

Table A6. Model calibration benchmark results of MCD with ResNet-50 on Office-Home. The numbers indicate the mean ECE across ten repetitions.

<table><tr><td>Method</td><td>Ar-Cl</td><td>Ar-Pr</td><td>Ar-Rw</td><td>Cl-Ar</td><td>Cl-Pr</td><td>Cl-Rw</td><td>Pr-Ar</td><td>Pr-Cl</td><td>Pr-Rw</td><td>Rw-Ar</td><td>Rw-Cl</td><td>Rw-Pr</td><td>Avg</td></tr><tr><td>Vanilla</td><td>38.91</td><td>26.39</td><td>18.86</td><td>32.85</td><td>26.69</td><td>19.36</td><td>35.87</td><td>36.70</td><td>18.61</td><td>24.57</td><td>36.87</td><td>14.79</td><td>27.54</td></tr><tr><td>TS</td><td>31.84</td><td>22.55</td><td>13.49</td><td>26.16</td><td>20.10</td><td>10.72</td><td>33.98</td><td>31.91</td><td>15.59</td><td>21.62</td><td>31.59</td><td>12.46</td><td>22.67</td></tr><tr><td>CPCS</td><td>13.07</td><td>20.09</td><td>47.15</td><td>9.78</td><td>21.82</td><td>8.02</td><td>32.65</td><td>25.61</td><td>15.27</td><td>20.53</td><td>40.38</td><td>7.84</td><td>21.85</td></tr><tr><td>IW-TS</td><td>12.88</td><td>21.44</td><td>61.15</td><td>10.56</td><td>16.40</td><td>11.72</td><td>33.03</td><td>36.37</td><td>14.09</td><td>19.96</td><td>41.95</td><td>19.30</td><td>24.91</td></tr><tr><td>TransCal</td><td>19.23</td><td>15.09</td><td>6.55</td><td>17.91</td><td>11.60</td><td>3.91</td><td>22.98</td><td>15.81</td><td>6.11</td><td>13.77</td><td>21.40</td><td>4.02</td><td>13.20</td></tr><tr><td>IW-Mid</td><td>50.68</td><td>28.93</td><td>23.92</td><td>38.24</td><td>33.48</td><td>28.58</td><td>39.76</td><td>37.45</td><td>22.40</td><td>27.15</td><td>44.15</td><td>18.07</td><td>32.73</td></tr><tr><td>IW-GAE</td><td>22.21</td><td>10.68</td><td>2.38</td><td>15.96</td><td>9.30</td><td>3.53</td><td>23.54</td><td>22.73</td><td>6.37</td><td>11.78</td><td>20.75</td><td>1.63</td><td>12.57</td></tr><tr><td>Oracle</td><td>5.88</td><td>9.91</td><td>3.19</td><td>7.75</td><td>4.64</td><td>3.66</td><td>4.17</td><td>7.70</td><td>3.09</td><td>4.51</td><td>8.09</td><td>3.54</td><td>5.51</td></tr></table>

## F. Additional Experiments

In this section, we show the effectiveness of IW-GAE with two different base models. First, we perform additional experiments with conditional domain adversarial network (CDAN; (Long et al., 2018)) which is also a popular UDA method. As in the experiments with MDD, we use ResNet-50 as the backbone network and OfficeHome as the dataset. The learning rate schedule for CDAN is $\alpha \cdot ( 1 + \gamma \cdot t ) ^ { - \eta }$ where t is the iteration counter, α = 0.01, γ = 0.001, and $\eta = 0 . 7 5$ . The remaining training configuration for CDAN is the same as the MDD training configuration except it uses the bottleneck dimension of 256 and weight decay of 0.0005 (cf. Appendix D). As we can see from Table A5, IW-GAE achieves the best performance among all considered methods, achieving the best ECE in 8 out of the 12 cases as well as the lowest mean ECE. We note that TransCal achieves a performance comparable to IW-GAE in this experiment, but considering the results in the other tasks, IW-GAE is still an appealing method for performing the model calibration task.

We also perform additional experiments with maximum classifier discrepancy (MCD; (Saito et al., 2018)). Following the previous experiments with MDD and CDAN, we use ResNet-50 as the backbone network and OfficeHome as the dataset. The training configuration is the same as the MDD training configuration except it uses the fixed learning rate of 0.001 with weight decay of 0.0005 and bottleneck dimension of 1,024 (cf. Appendix D). Consistent to other benchmark results, IW-GAE achieves the best performance among all methods (Table A6). Specifically, IW-GAE achieves the best average model calibration performance, and its ECE is lowest in 7 out of 12 domain pairs. Note that IW-Mid’s performance with MCD is significantly lower compared to other benchmark results. However, IW-GAE still significantly improves the performance, indicating that IW-GAE does not strongly depends on accuracy of the CI estimation discussed in Section C.1.

## F.1. Qualitative Evaluation of IW-GAE

To qualitatively analyze IW-GAE, we also visualize reliability curves that compare the estimated group accuracy with the average accuracy in Figure A2. We first note that IW-GAE tends to accurately estimate the true group accuracy for most groups under different cases compared to IW-Mid. The accurate group accuracy estimation behavior of IW-GAE explains the results that the IW-GAE improves IW-Mid for most cases in the model calibration and selection tasks (cf. Tables A1-A6). For most cases, true accuracy is in between the lower and upper IW estimators, albeit the interval length tends to increase for high-confidence groups. This means that the CI of the IW based on the Clopper-Pearson method successfully captures the IW in the CI. We also note that the true accuracy is close to the lower IW estimator in the lower confidence group and the middle IW estimator in the high confidence group. An observation that the true accuracy’s relative positions in CIs varies from one group to another group motivates why an adaptive selection of binned IWs as ours is needed.

![](images/955e23314a14e959059ae90264bae9bfb1a13c5c3be3d659f5fa3767b647e184.jpg)  
Figure A2. True group accuracy and estimated group accuracy of IW-GAE and IW-Mid under MDD. The shaded areas represent possible group accuracy estimation with binned IWs in the CI. The title of a figure represents “Source-Target.” For IW-Mid and IW-GAE, we clip the accuracy estimations when they exceed 1, which can occur when the upper bound of CI is large. Also, the number of groups in the figure is different for some domain pairs because there can be a group that contains no target samples (we set $M = 1 0$ for all cases).

## G. Analysis of $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ and Ident $B i a s ( w ^ { \dagger } ( n ) ; { \mathcal G } _ { n } )$ of IW and Their Relation to Source and Target Group Accuracy Estimation Errors

In this section, we aim to answer the following question about the central idea of this work: “Does solving the optimization problem in $( 8 ) – ( 1 3 )$ result in an accurate target group accuracy estimato $r ? ^ { \dprime }$ Specifically, we analyze the relationship between the optimization error $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ ), the bias of the identical accuracy assumption Ident $B i a s ( w ^ { \dagger } ( n ) ; { \mathcal G } _ { n } )$ , the source group accuracy estimation error $| \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { \dagger } ( n ) ) |$ , and the target group accuracy estimation error $| \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { \dagger } ( n ) ) |$ from the perspective of (5) and $( 1 5 ) ^ { 2 }$ . To this end, we gather $w ^ { \dagger } ( n )$ obtained by solving the optimization problem under all temperature parameters in the search space $t \in \tau$ with MDD on the OfficeHome dataset (720 IWs from 6 values of the temperature parameter, 12 domain pairs, and 10 groups). Then, by using the test dataset in the source and the target domains, we obtain the following observations.

In (5), we show that $| \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { \dagger } ( n ) ) |$ is upper bounded by $| \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { \dagger } ( n ) ) |$ . However, the inequality could be loose since the inequality is obtained by taking the maximum over the IW values. Considering that the optimization problem is formulated for finding $w ^ { \dagger } ( n )$ that achieves small $| \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { \dagger } ( n ) ) |$ (cf. Proposition 3.1), the loose connection between the source and target group accuracy estimation errors can potentially enlighten a fundamental difficulty to our approach. However, as we can see from Figure A4, it turns out that $| \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { * } ) - $ $\alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { \dag } ( n ) ) |$ is strongly correlated with $| \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { \dagger } ( n ) )$ |. This result validates our approach of reducing the source accuracy estimation error of the IW-based estimator for obtaining an accurate group accuracy estimator in the target domain.

In (15), we show that $| \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { \dagger } ( n ) ) | \le \epsilon _ { o p t } ( w ^ { \dagger } ( n ) ) + \epsilon _ { s t a t } + I d e n t B i a s ( w ^ { \dagger } ( n ) ; \mathcal { G } _ { n } )$ , which motivates us to solve the optimization problem for reducing $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ (cf. Section 3) and to construct groups based on the maximum value of softmax for reducing Ident $B i a s ( w ^ { \dagger } ( n ) ; { \mathcal G } _ { n } )$ (cf. Section 2.2). Again, if these terms are loosely connected to $| \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { \dagger } ( n ) ) |$ , a fundamental difficulty arises for our approach. In this regard, we analyze the relationship between $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ , IdentBias $( w ^ { \dagger } ( n ) ; { \mathcal G } _ { n } )$ , and $| \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { S } ( \mathcal { G } _ { n } ; w ^ { \dag } ( n ) )$ |. From Figure A3, we can see that both $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ and Iden $: B i a s ( w ^ { \dagger } ( n ) ; { \mathcal G } _ { n } )$ are strongly correlated to the source group accuracy estimation error. Combined with the observation in Figure A4, this observation explains the impressive performance gains by IW-GAE developed for reducing $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ and $I d e n t B i a s ( w ^ { \dagger } ( n ) ; \mathcal { G } _ { n } )$

![](images/1cce0863df9a31f4531f7c5f4cdfb8b6d463df04ebf046210a06c99e1622d4bf.jpg)

![](images/375b6797f9a98441208714cd37bf95206f9a32ce34bfcbea9bc548b5742daea1.jpg)

Figure A3. The relationship between between $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ and the source group accuracy estimation error (left) and the relationship between IdentBias $( w ^ { \dagger } ( n ) ; { \mathcal G } _ { n } )$ and the source group accuracy estimation error (right).  
![](images/27d19ca25aa3b500c0adb6d49d8ed274e33a70ec51e1483d998244404ce30852.jpg)  
Figure A4. The relationship between source and target group accuracy estimation errors.

![](images/22a2010ea6f213c4d95665ca000bba969866a404275ef6bf3f36abb3dadd3386.jpg)  
Figure A5. The relationship between $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ and the target group accuracy estimation error.

Next, we analyze the efficacy of solving the optimization problem for obtaining an accurate target group accuracy estimator. To this end, we analyze the relationship between $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ ) and $| \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { \dagger } ( n ) ) |$ . From Figure A5, $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ ) is correlated with $| \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { T } ( \mathcal { G } _ { n } ; \bar { w ^ { \dag } } ( n ) ) |$ |, which explains the performance gains in the model calibration and selection tasks by IW-GAE. However, the correlation is weaker than the cases analyzed in Figure A4 and Figure A3. We conjecture that this is because $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ is connected to $| \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { \dagger } ( n ) )$ | through two inequalities (5) and (15), and this results in a somewhat loose connection between $\epsilon _ { o p t } ( w ^ { \dagger } ( n ) )$ and $| \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { * } ) - \alpha _ { T } ( \mathcal { G } _ { n } ; w ^ { \dagger } ( n ) )$ |.

In Figure A5, we also note that the optimization problem is subject to a non-identifiability issue that the solutions with the same optimization error can have significantly different target group accuracy estimation errors (e.g., points achieving the zero optimization error in Figure A5). We remark that the non-identifiability issue motivates an important future direction of research that develops a more sophisticated objective function and a regularization function that can distinguish estimators with different target group accuracy estimation errors.