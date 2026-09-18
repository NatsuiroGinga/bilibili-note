---
title: "2024-Liu-FOIL-Time-Series-OOD-Invariant-Learning"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2024-Liu-FOIL-Time-Series-OOD-Invariant-Learning.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Time-Series Forecasting for Out-of-Distribution Generalization Using Invariant Learning

Haoxin Liu <sup>1</sup> Harshavardhan Kamarthi <sup>1</sup> Lingkai Kong <sup>1</sup> Zhiyuan Zhao <sup>1</sup> Chao Zhang <sup>1</sup> B. Aditya Prakash <sup>1</sup>

## Abstract

Time-series forecasting (TSF) finds broad applications in real-world scenarios. Due to the dynamic nature of time-series data, it is crucial to equip TSF models with out-of-distribution (OOD) generalization abilities, as historical training data and future test data can have different distributions. In this paper, we aim to alleviate the inherent OOD problem in TSF via invariant learning. We identify fundamental challenges of invariant learning for TSF. First, the target variables in TSF may not be sufficiently determined by the input due to unobserved core variables in TSF, breaking the conventional assumption of invariant learning. Second, time-series datasets lack adequate environment labels, while existing environmental inference methods are not suitable for TSF.

To address these challenges, we propose FOIL, a model-agnostic framework that enables timeseries Forecasting for Out-of-distribution generalization via Invariant Learning. FOIL employs a novel surrogate loss to mitigate the impact of unobserved variables. Further, FOIL implements a joint optimization by alternately inferring environments effectively with a multi-head network while preserving the temporal adjacency structure, and learning invariant representations across inferred environments for OOD generalized TSF. We demonstrate that the proposed FOIL significantly improves the performance of various TSF models, achieving gains of up to 85%.

## 1. Introduction

Time-series (TS) data are ubiquitous across various domains, including public health (Kamarthi et al., 2021b; Rodriguez et al., 2021), finance (Sezer et al., 2020), and urban computing (Tabassum et al., 2021). Time-series forecasting (TSF), a foundational task in analyzing TS data, involving predicting future events or trends based on historical TS data, has received a longstanding research focus. TSF faces certain challenges due to the dynamic and complex nature of TS data: First, distributions of TS data change over time. Second, the inherent complexity of TSF is compounded by unforeseen exogenous factors, such as policy interventions and climate changes in the context of influenza forecasting.

Given the dynamic nature of TS data, where unforeseen distribution shifts can occur between historical training and future testing data, the TSF task asks for robust out-ofdistribution (OOD) generalization abilities. Instead, existing TSF models employ empirical risk minimization to greedily incorporate all correlations within the data to minimize average training errors. However, as not all correlations persist in unknown test distributions, these models may lack OOD generalization abilities. Note that existing works on temporal distribution shifts (Du et al., 2021; Kim et al., 2021; Liu et al., 2022; Fan et al., 2023) merely focus on mitigating the marginal distribution shifts of the input. These methods are not generalizable enough for the OOD problem, which consists of various types of distribution shifts (Liu et al., 2021c), such as conditional distribution shifts, etc.

In this paper, we propose to alleviate the OOD generalization problem of TSF via invariant learning (IL). IL seeks to identify and utilize invariant features that maintain stable relationships with targets across different environments while discarding unstable correlations introduced by variant features. Although IL has witnessed wide theoretical and empirical success in various domains (Koyama & Yamaguchi, 2020; Ye et al., 2023; Weber et al., 2022), it remains unexplored yet non-trivial to apply IL for TSF because of the following challenges: First, TS data breaks IL’s conventional assumption. In TS data, there are always variables that directly affect targets but remain unobserved, such as the outbreak of an epidemic, sudden temperature changes, policy adjustments, etc. IL fails to consider these unobserved core variables, leading to poor OOD generalization in TSF. Second, TS data are usually collected without explicit environment labels. Although some general IL with environment inference methods have been proposed, their neglect of TS data characteristics results in suboptimal inferred time-series environments.

Thus, we propose a novel TSF approach for out-ofdistribution generalization, namely FOIL (Forecasting for Out-of-distribution TS generalization via Invariant Learning). Our contributions are summarized as follows:

• We investigate the out-of-distribution generalization problem of time-series forecasting. To the best of our knowledge, we are the first to introduce invariant learning to TSF and identify two essential gaps, including the non-compliance of IL’s conventional assumption and the lack of environment labels.

• We propose FOIL, a practical and model-agnostic invariant learning framework for TSF. FOIL leverages a simple surrogate loss to ensure the applicability of IL and designs an efficient environment inference module tailored for time-series data.

• We conduct extensive experiments on diverse datasets along with three advanced forecasting models (‘backbones’). FOIL proves effectiveness by uniformly outperforming all baselines in better forecasting accuracy.

## 2. Preliminaries and Problem Definition

We formally introduce the TSF task and discuss why it is an OOD generalization problem. We then introduce the problem OOD-TSF, formulating TSF as an OOD problem.

We denote slanted upper-cased letters such as X as random variables and calligraphic font letters X as its sample space. Upright bold upper-cased letters such as X, bold lower-cased letters such as x and regular lower-cased letters such as x denote deterministic matrices, vectors and scalars, respectively.

## 2.1. Time-Series Forecasting: An Out-of-Distribution Generalization View

TSF models take a time series as input and output future values of some or all of its features. Let the input time-series variable be denoted as $\pmb { X } \in \mathbb { R } ^ { l \times d _ { \mathrm { i r } } }$ , where l is the length of the lookback window decided by domain experts and $d _ { \mathrm { i n } }$ is the feature dimension at each time step. The output variable of the forecasts generated of horizon window length h is denoted as $Y \in \mathbb { R } ^ { h \times d _ { \mathrm { o u t } } }$ , where $d _ { \mathrm { o u t } }$ is the dimension of targets at each time step. For the sample at time step t, denoted as $( \mathbf { X } _ { t } , \mathbf { Y } _ { t } ) , \mathbf { X } _ { t } \in X = [ \mathbf { x } _ { t - l + 1 } , \mathbf { x } _ { t - l + 2 } , \ldots , \mathbf { x } _ { t } ]$ and $\mathbf { Y } _ { t } \in Y = [ \mathbf { y } _ { t + 1 } , \mathbf { y } _ { t + 2 } , \ldots , \mathbf { y } _ { t + h } ] .$ Thus, the TSF model parameterized by θ is denoted as $f _ { \theta } : \mathcal { X }  \mathcal { Y }$

In this paper, we focus on univariate forecasting with covariates, i.e., $d _ { \mathrm { o u t } } = 1$ and $d _ { \mathrm { i n } } \geq 1$ , but our method can be easily generalized to the multivariate forecasting setting by using multiple univariate forecasting (Gruver et al., 2023; Lim & Zohren, 2021).

Existing TSF models usually assume the training distribution is the same as the test distribution and use empirical risk minimization (ERM) for model training. However, training and test sets of TSF represent historical and future data, respectively. Given the dynamic nature of time series, the test distribution may diverge from the training distribution. In this paper, we consider TSF under the more realistic situation where $P ^ { \mathrm { t r a i n } } ( X , Y ) \neq P ^ { \mathrm { t e s t } } ( X , Y )$ , i.e., unknown $P ^ { \mathrm { t e s t } } ( X , Y )$ , which can be defined as follows:

Problem 1. Out-of-Distribution Generalization for Time-Series Forecasting (OOD-TSF): Given a time-series training dataset ${ \mathcal { D } } ^ { \mathrm { t r a i n } } = \{ ( { \bf X } _ { t } , { \bf Y } _ { t } ) \} _ { t = 1 } ^ { T }$ , the task is to learn an out-of-distribution generalized forecasting model $f _ { \theta } ^ { * } : \mathcal { X } $ $\mathcal { V }$ parameterized by θ which achieves minimum error on testing set $\mathcal { D } ^ { \mathrm { t e s t } }$ with unknown distribution $P ^ { \mathrm { t e s t } } ( X , Y )$

## 2.2. Invariant Learning: Out-of-Distribution Generalization with Environments

Environment Labels. Invariant learning (IL), backed by the invariance principle (Arjovsky et al., 2019) from causality, is a popular solution for OOD generalization. IL assumes heterogeneity in observed data: dataset is collected from multiple environments, formulated as $\mathcal { D } = \cup _ { e } \mathcal { D } ^ { e } =$ $\cup _ { e } \{ ( \mathbf { X } _ { i } ^ { e } , \mathbf { Y } _ { i } ^ { e } ) \} _ { i = 1 } ^ { | \mathcal { D } ^ { e } | }$ ; each environment e has a distinct distribution $P ^ { e } ( X , Y )$ , termed heterogeneous environments. In time-series data, temporal environments can be seasons, temperatures, policies, etc. Let $\operatorname { s u p p } ( E )$ denote all environments, the objective function is formulated as:

$$
\mathcal {R} _ {\mathrm{IL}} (f _ {\theta}) = \max _ {e \in \operatorname{supp} (\boldsymbol {E})} \mathbb {E} _ {P (\boldsymbol {X}, \boldsymbol {Y} | e)} [ \ell (f _ {\theta} (\boldsymbol {X}), \boldsymbol {Y})) | e ],\tag{1}
$$

where OOD generalization is achieved by minimizing the empirical risk under the worst-performing environment.

Invariant Features. To optimize Eq. 1, IL proposes to identify and utilize invariant features that maintain stable relationships with target variables across different environments. For instance, in forecasting the number of flu cases, temperature changes belong to invariant features (Mourtzoukou & Falagas, 2007; Makinen et al.¨ , 2009), while hospital records are variant features since the proportion of influenza cases over all records may vary across different seasons.

Sufficiency and Invariance Assumption. Most IL methods are proposed based on the following conventional assumption (Gong et al., 2016; Rojas-Carulla et al., 2018; Chang et al., 2020; Arjovsky et al., 2019; Liu et al., 2021a; Lin et al., 2022):

Assumption 2.1 (Conventional Assumption of Invariant Learning). The input features X is a mixture of invariant features $X _ { \mathrm { I } }$ and variant features $X _ { \mathrm { V } } , \ X _ { \mathrm { I } }$ possesses the following properties:

a. Sufficiency property: $Y = g ( X _ { \mathrm { I } } ) + \epsilon .$ , where $g ( \cdot )$ can be any mapping function, and ϵ is random noise.

b. Invariance property: for all $e _ { i } , e _ { j } \in \mathrm { s u p p } ( E )$ , we have $P ^ { e _ { i } } ( Y | X _ { \mathrm { I } } ) = P ^ { e _ { j } } ( Y | X _ { \mathrm { I } } )$ holds.

Thus, $X _ { \mathrm { I } }$ is assumed to provide sufficient and invariant predictive power for Y and is theoretically proven to guarantee optimal OOD performance for Eq. 1 (Liu et al., 2021a).

To better understand the above, we employ the structural causal model (SCM) (Pearl et al., 2000) shown in Figure 1(a). We define invariant features $X _ { \mathrm { I } }$ as the subset of input features X that directly cause Y, following (Arjovsky et al., 2019; Peters et al., 2016; Lin et al., 2022). Environment E can be interpreted as the confounder between $X _ { \mathrm { I } }$ and $X _ { \mathrm { V } }$ . Specifically, the correlation between $X _ { \mathrm { V } }$ and Y is spurious, mediated through $X _ { \mathrm { V } }  E  X _ { \mathrm { I } }  Y$ Conversely, the causal relationship $X _ { \mathrm { I } }  Y$ is invariant. Generally, IL aims to achieve OOD generalization using such $X _ { \mathrm { I } }$ to predict Y .

## 3. Challenges

Considering the theoretical and empirical successes of invariant learning (Arjovsky et al., 2019; Koyama & Yamaguchi, 2020; Krueger et al., 2021; Ye et al., 2023), a natural question arises: Can we directly apply invariant learning (IL) to OOD-TSF? Unfortunately, there are two main reasons rendering a direct application problematic. Firstly, the existence of unobserved variables in time-series (TS) data breaks the conventional Assumption 2.1 of IL. Secondly, TS datasets usually lack adequate environment labels.

TS data break IL’s conventional assumption. Recall ${ \mathrm { A s } } -$ sumption 2.1, where invariant features $X _ { \mathrm { I } }$ are assumed to provide sufficient and invariant predictive power for Y in IL. However, in TSF tasks, there are always variables that directly affect Y but are not included in the input features X, such as the outbreak of a novel epidemic, sudden temperature changes, policy adjustments, etc. These unobserved core variables, denoted as $z ,$ exist due to their absence from the whole dataset or the lookback window.

In the SCM shown in Figure 1(a), we use $Z \to Y$ and the dash circle to describe the core effect of Z on Y and the unobserved issue of $z$ respectively. Clearly, there exists a gap between the SCM modeled by the existing IL methods and the SCM underlying TS data , due to the existence of Z.

The existence of unobserved Z breaks both two parts of the IL’s conventional assumption 2.1: First, Z breaks the sufficiency property part, obviously. Thus, existing IL methods actually absorb the influence of Z on Y, leading to the overfitting issue, especially with deep models. Second, Z breaks the invariance property part when Z and E are not independent, for example, influenza outbreaks occur more frequently in winter. Formally, if there exists $e _ { i } , e _ { j } \in$ supp(E) such that $P ^ { e _ { i } } ( Z | { \cal X } _ { \mathrm { I } } ) { \mathrm { ~  ~ \ne ~ } } P ^ { e _ { j } } ( Z | { \cal X } _ { \mathrm { I } } )$ , then we have $\begin{array} { r } { P ^ { e _ { i } } ( \pmb { Y } | \pmb { X } _ { \mathrm { I } } ) \ = \ \sum _ { \mathbf { Z } } P ( \pmb { Y } | \pmb { X } _ { \mathrm { I } } , \mathbf { Z } ) P ^ { e _ { i } } ( \mathbf { Z } | \pmb { X } _ { \mathrm { I } } ) \ \neq \ } \end{array}$ $P ^ { e _ { j } } \big ( { Y } | { X } _ { \mathrm { I } } \big )$ . Thus, existing IL methods lacks reliable OOD generalization ability for TSF.

![](images/e8ca80df570882c9b5cedd6b1a40864bbcb2d1bffa059ce23aeab144ef8aeff9.jpg)

![](images/4c31aa2a4ad2e34f89112d7bbf1043f4618cc61ab3f32f328dc27384f44c7b11.jpg)  
(a) Existing IL methods.  
(b) Our proposed method.  
Figure 1. The structural causal model (SCM) for (a) existing invariant learning methods and (b) our proposed method. The key difference is that our method targets the sufficiently predictable part of the target, i.e., $\mathbf { \nabla } \mathbf { Y } ^ { \mathrm { s u f } }$ rather than the raw Y , thus making invariant learning feasible.

TS datasets usually lack environment labels. Firstly, most IL methods (Arjovsky et al., 2019; Ahuja et al., 2021; Krueger et al., 2021; Pezeshki et al., 2021; Sagawa et al., 2019) require explicit environment labels as input, which are often unavailable in TSF datasets. Due to the complexity of temporal environments, manual annotation is often difficult, expensive, and sometimes suboptimal. Secondly, existing IL with environment inference methods are fundamentally not applicable for TSF: (1) Existing IL methods show certain limitations when applying to TSF tasks: HRM (Liu et al., 2021a) and KernelHRM (Liu et al., 2021b) are based on low-dimensional raw features, while TS data are typically high-dimensional; EIIL (Creager et al., 2021) needs delicate initialization; ZIN (Lin et al., 2022) requires additional information satisfying specific conditions; and EDNIL (Huang et al., 2022) is designed for classification tasks. (2) Existing IL methods primarily cater to static data and thus overlook the characteristics of time-series data, leading to suboptimal inferred environments.

## 4. Our Methodology

We propose FOIL (Forcasting for-Out-of-distribution generalization via Invariant Learning), a model-agnostic environment-aware invariant learning framework, serving as a practical solution for the OOD-TSF problem.

## 4.1. Overview

High-level Idea. Our main idea is to use IL with environment inference targeting at the sufficiently predictable part of the target (we call it $Y ^ { \mathrm { s u f } } )$ , see Figure 1(b). Specifically, inspired by the Wold’s decomposition theorem (Anderson, 2011; Nerlove et al., 2014), we assume that $\mathbf { Y }$ can be decomposed into deterministic and uncertain parts relative to the input X. Formally, $Y = q ( Y ^ { \mathrm { s u f } } , Z )$ ), with $q ( \cdot , \cdot )$ as any mapping function. Here, $\pmb { Y } ^ { \mathrm { s u f } } \in \mathcal { y }$ , determined by the input $\boldsymbol { X }$ , is deterministic, i.e., sufficiently predictable. Thus, targeting at $Y ^ { \mathrm { s u f } }$ , the Assumption 2.1 of sufficiency and invariance property holds, making invariant learning feasible. Additionally, considering the unpredictability of unobserved $Z ,$ , the optimal OOD prediction can be achieved if we are able to uncover $Y ^ { \mathrm { s u f } }$ via invariant features $X _ { \mathrm { I } }$ . To this end, we propose FOIL, which serves as a practical solution for applying IL to the OOD-TSF problem.

Overall Framework. As shown in Figure 2, FOIL consists of three parts:

(1) Label Decomposing Component $(  { \mathcal { C } } _ { \mathrm { L D } } )$ , which decomposes sufficiently predictable $Y ^ { \mathrm { s u f } }$ from observed $\mathbf { Y } .$

(2) Time-Series Environment Inference Module $( \mathcal { M } _ { \mathrm { T E I } } )$ which infers temporal environments based on learned representations from $\pmb { \mathcal { M } } _ { \mathrm { T I L } }$

(3) Time-Series Invariant Learning Module $( \mathcal { M } _ { \mathrm { T I L } } )$ , which learns invariant representations across inferred environments from $\mathcal { M } _ { \mathrm { T E I } }$

In FOIL, $c _ { \mathrm { L D } }$ is the preliminary step for $\mathbf { \mathcal { M } } _ { \mathrm { T I L } }$ and M<sub>TEI</sub>; $\mathbf { \mathcal { M } } _ { \mathrm { T I L } }$ and $\mathcal { M } _ { \mathrm { T E I } }$ are then jointly optimized via alternating updates. During the testing phase, only $\mathbf { \mathcal { M } } _ { \mathrm { T I L } }$ is utilized for prediction.

As the first work of IL for TSF, FOIL is designed as a modelagnostic framework that seamlessly incorporates various off-the-shelf deep TSF models. Specifically, the backbone model can be any deep $T S F$ model, denoted $\phi ( X )$ . We append a regressor $\rho ( \cdot )$ , typically a fully connected layer, on top of the learned output representations from the backbone model $\phi ( \cdot )$ . We denote the combined model succinctly as as $f _ { \theta } ( X ) = \rho \left( \phi ( X ) \right)$ . $\mathbf { \mathcal { M } } _ { \mathrm { T I I } }$ and $\pmb { \mathcal { M } } _ { \mathrm { T E I } }$ leverage the output representation ϕ(X), both for achieving modelagnostic and for accommodating high-dimensional inputs of TSF. We will next introduce each part.

## 4.2. The Label Decomposing Component

$c _ { \mathrm { L D } }$ is used to decompose the sufficiently predictable Y<sup>suf</sup> from the observed Y. However, accurately obtaining Y<sup>suf</sup> is nearly unfeasible, owing to the lack of information about the underlying generation function and unobserved variables $z .$ Instead of introducing additional data, such as external datasets as the agent for $z ,$ we aim to alleviate this problem more practically via a surrogate loss to mitigate the effect of Z. Firstly, we add the following assumption:

![](images/60f2a81c168a14f843b8d4d8a683a40f9dba3555728ccfe0bd407e10a4e5d85e.jpg)  
Figure 2. The overall framework of our proposed FOIL.

$$
\boldsymbol {Y} = q (\boldsymbol {Y} ^ {\text { suf }}, \boldsymbol {Z}) = \alpha (\boldsymbol {Z}) (\boldsymbol {Y} ^ {\text { suf }}) + \beta (\boldsymbol {Z}) \mathbf {1},\tag{2}
$$

where $\alpha ( \cdot ) : \mathbb { R } ^ { d _ { Z } }  \mathbb { R }$ and $\beta ( \cdot ) : \mathbb { R } ^ { d _ { Z } }  \mathbb { R }$ could be any mapping function, and $\mathbf { 1 } \in \mathbb { R } ^ { h \times d _ { \mathrm { o u t } } }$ is an all-one matrix. This assumption follows the dynamic nature of observed $\mathbf  \} ^ { \prime } \mathbf { s }$ distribution (Cheng et al., 2015). Specifically, this assumption encompasses two aspects:

(1) The relationships between $z$ and $Y ^ { \mathrm { s u f } }$ are additive and multiplicative, which is a widely adopted assumption about unobserved variables (Hoyer et al., 2008; Maeda & Shimizu, 2021; Sancho et al., 1982; Wooldridge, 1997). (2) Z exerts a consistent influence in one horizon window, which can be readily extended by partitioning the horizon window into multiple segments. Thus, the residual Res between ground truth $\mathbf { Y }$ and predicted $\hat { Y }$ , i.e., $R e s = Y - { \hat { Y } }$ , absorb the effect of $z$ on $\mathbf { Y }$ via values of mean $\mu ( R e s )$ and standard deviation $\sigma ( R e s )$ . Thus, we propose an Instance Residual Normalization (IRN) method to mitigate the effect of $Z .$ For the residual $\mathbf { \Pi } _ { R e s _ { t } }$ of instance $t ,$ IRN method can be formulated as:

$$
\tilde {\mathbf {R e s}} _ {t} = \frac {\mathbf {Y} _ {t} - \mu (\mathbf {Y} _ {t})}{\sigma (\mathbf {Y} _ {t})} - \frac {\hat {\mathbf {Y}} _ {t} - \mu (\hat {\mathbf {Y}} _ {t})}{\sigma (\hat {\mathbf {Y}} _ {t})} = \tilde {\mathbf {Y}} _ {t} - \tilde {\hat {\mathbf {Y}}} _ {t}\tag{3}
$$

IRN in Eq. 3 ensures the residuals to have a mean of 0 and a variance of $2 - 2 \mathrm { c o v } ( \hat { \mathbf Y } , { \mathbf Y } )$ , where cov denotes the covariance.

Finally, we derive the following simple and effective surrogate loss to mitigate the effect of $z ,$ instead of directly decoupling $Y ^ { \mathrm { s u f } }$ in $c _ { \mathrm { L D } }$

$$
\ell_ {\text { suf }} (\hat {\boldsymbol {Y}}, \boldsymbol {Y}) = \text { MSE } (\tilde {\boldsymbol {R e s}}, \boldsymbol {0}) = \ell (\tilde {\hat {\boldsymbol {Y}}}, \tilde {\boldsymbol {Y}}),\tag{4}
$$

where $\begin{array} { r } { \mathrm { M S E } ( \tilde { R e } s , \mathbf { 0 } ) = \frac { 1 } { h } \sum _ { j = 1 } ^ { h } ( \tilde { \mathbf { R e } } \mathbf { s } _ { t + j } ) ^ { 2 } } \end{array}$ . Note that our IRN fundamentally differs from the existing instance normalization (IN) methods. Existing methods adopt IN to $\boldsymbol { X }$ and reverse IN to $\hat { Y }$ based on $\mu ( X )$ and $\sigma ( X )$ , aiming to address non-stationary problem of X (Kim et al., 2021; Liu et al., 2022). While, our IRN method directly aligns the mean and variance between ${ \hat { Y } } = f ( X )$ and Y, thus removing error caused by Z under the introduced assumption. Since Z is not contained in X, existing methods usually fail to achieve our goal.

## 4.3. The Time-Series Environment Inference Module

$\pmb { \mathcal { M } } _ { \mathrm { T E I } }$ aims to infer environments $\scriptstyle { E _ { \mathrm { i n f e r } } }$ , thereby providing environment labels for the time-series invariant learning module $\pmb { \mathcal { M } } _ { \mathrm { T I L } }$ . We consider inferring effective and reasonable temporal environments with two goals:

(1) Sensitive to the encoded invariant features. In FOIL, $\pmb { \mathcal { M } } _ { \mathrm { T E I } }$ and $\mathbf { \mathcal { M } } _ { \mathrm { T I I } }$ are adversarial: $\pmb { \mathcal { M } } _ { \mathrm { T E I } }$ infers environments based on the variant features not discarded by $\mathcal { M } _ { \mathrm { T I L } }$ $\mathbf { \mathcal { M } } _ { \mathrm { T I I } }$ discards variant features based on inferred environments from $\pmb { \mathcal { M } } _ { \mathrm { T E I } }$ . Ultimately, when $\mathbf { \mathcal { M } } _ { \mathrm { T I L } }$ only utilizes invariant features, $\pmb { \mathcal { M } } _ { \mathrm { T E I } }$ is unable to infer effective environments. Thus, we propose to infer informative environments that are sensitive to the variant features encoded in the currently learned representations, formulated as:

$$
\min _ {\boldsymbol {E} _ {\text { infer }}} H \left(\boldsymbol {Y} ^ {\text { suf }} | \phi^ {*} (\boldsymbol {X}), \boldsymbol {E} _ {\text { infer }}\right) - H \left(\boldsymbol {Y} ^ {\text { suf }} | \phi^ {*} (\boldsymbol {X})\right),\tag{5}
$$

where H is Shannon conditional entropy, $\phi ^ { * } ( X )$ are learned representations from $\mathbf { \mathcal { M } } _ { \mathrm { T I I } }$ and frozen in $\pmb { \mathcal { M } } _ { \mathrm { T E I } }$

(2) Preserving the temporal adjacency structures. To ensure that the inferred environments are reasonable in the context of TSF, we consider preserving the inherent characteristic of time-series data, i.e., the temporal adjacency structure. Specifically, instances that are temporally adjacent should possess similar temporal environments. This can also be viewed as a type of regularization to prevent inferred environments from overfitting to random noises.

Intuitively, the approach to infer environments is to optimize Eq. 5, with a plugin for preserving the temporal adjacency structure. To this end, we present an EM-based clustering solution in the representation space, implemented through a multi-head neural network. Each head is an environmentspecific regressor, playing the role of each cluster’s center. Specifically, the regressor $\rho ^ { ( e ) }$ is specific for environment e. And the representation $\phi ^ { * } ( X )$ is shared and frozen in $\mathbf { \mathcal { M } } _ { \mathrm { T E I } }$ . We describe the M step and E step next.

M Step: Optimizing Environment-Specific Regressors In the M step, we optimize $\{ \rho ^ { ( e ) } \}$ to better fit the data from current environment partition $E _ { \mathrm { i n f e r } }$ of E step as:

$$
\begin{array}{l} \min _ {\{\rho^ {(e)} \}} \mathcal {L} _ {\mathrm{TEI}} = \mathbb {E} _ {e \in E _ {\text {infer}}} \mathcal {R} _ {\text {suf}} ^ {(e)} (\rho^ {(e)}, \phi^ {*}) \\ = \sum_ {e \in E _ {\text {infer}}} \frac {1}{| \mathcal {D} _ {e} |} \sum_ {(\mathbf {X}, \mathbf {Y}) \in \mathcal {D} _ {e}} \ell_ {\text {suf}} \left(\rho^ {(e)} \left(\phi^ {*} (\mathbf {X})\right), \mathbf {Y}\right) \end{array}\tag{6}
$$

## E Step: Estimating Environment Labels

Next, in the E step, we reallocate the environment partitions. For instance $( \mathbf { X } _ { t } , \mathbf { Y } _ { t } )$ , we reassign its environment label $\mathbf { \mathit { E } } _ { \mathrm { { i n f e r } } } ( t )$ via the following two steps:

• Step 1: Reallocating based on the distances with the center of each cluster (environment). We use the loss with respect to regressor $\rho ^ { ( e ) }$ to describe the distance with the center of cluster e. Thus, we reassign $\mathbf { \mathit { E } } _ { \mathrm { { i n f e r } } } ( t )$ according to the shortest distance, as follows:

$$
\boldsymbol {E} _ {\mathrm{infer}} (t) \leftarrow \arg \min _ {e \in \boldsymbol {E} _ {\mathrm{infer}}} \left\{\ell_ {\mathrm{suf}} \left(\rho^ {(e)} \left(\phi^ {*} (\mathbf {X} _ {t})\right), \mathbf {Y} _ {t}\right) \right\}\tag{7}
$$

• Step 2: Reallocating to preserve temporal adjacency structure. We propose an environment label propagation solution to achieve this goal, as follows:

$$
\boldsymbol {E} _ {\text { infer }} (t) \leftarrow \text { mode } \left\{\boldsymbol {E} _ {\text { infer }} (t + j) \right\} _ {j = - r} ^ {r},\tag{8}
$$

where mode implements majority voting by considered temporal neighbors selected via the radius $r \in \mathbb { Z } ^ { + }$

In summary, we iteratively execute M step and E step to obtain the inferred environments $E _ { \mathrm { i n f e r } } ^ { * }$ . Due to the fixed second term of Eq. 5, our solution represents a practical instantiation of Eq. 5.

## 4.4. The Time-Series Invariant Learning Module

$\mathbf { \mathcal { M } } _ { \mathrm { T I L } }$ is used to learn invariant representations $\phi ^ { * } ( X )$ across inferred environments $E _ { \mathrm { i n f e r } } ^ { \ast }$ from $\pmb { \mathcal { M } } _ { \mathrm { T E I } }$ . Specifically, $\mathbf { \mathcal { M } } _ { \mathrm { T I L } }$ aims to learn the $\phi ^ { * } ( X )$ which encode and solely encode all the information of invariant features $X _ { \mathrm { I } }$ thus achieving both invariant and sufficient predictive capability targeting at $Y ^ { \mathrm { s u f } }$ . Such $\phi ^ { * } ( X )$ has been theoretically proven (Liu et al., 2021a) to be obtained by optimizing the following objective function:

$$
\phi^ {*} = \arg \max _ {\phi} I (\mathbf {Y} ^ {\text { suf }}; \phi (\mathbf {X}) - I (\mathbf {Y} ^ {\text { suf }}; E _ {\text { learn }} ^ {*} | \phi (\mathbf {X})),\tag{9}
$$

where $I ( \cdot ; \cdot )$ measures Shannon mutual information. The first and second terms correspond to ensure sufficiency and invariance property of $\phi ( X )$ , respectively.

Considering the unavailability of $Y ^ { \mathrm { s u f } }$ , we present the following practical loss function as the instantiation of Eq. 9 via our surrogate loss in Eq. 4:

$$
\begin{array}{r l} & {\underset {\rho , \phi} {\min} \mathcal {L} _ {\mathrm{TIL}} = \mathbb {E} _ {e \in \boldsymbol {E} _ {\mathrm{infer}} ^ {*}} \boldsymbol {\mathcal {R}} _ {\mathrm{suf}} ^ {(e)} (\rho , \phi) + \lambda_ {1} \boldsymbol {\mathcal {R}} _ {\mathrm{ERM}} (\rho , \phi)} \\ & {\qquad + \lambda_ {2} \mathrm{Var} _ {e \in \boldsymbol {E} _ {\mathrm{infer}} ^ {*}} \left[ \boldsymbol {\mathcal {R}} _ {\mathrm{suf}} ^ {(e)} (\rho , \phi) \right],} \end{array}\tag{10}
$$

where $\lambda _ { 1 } , \lambda _ { 2 }$ are hyper-parameters, $\begin{array} { r l } { \mathcal { R } _ { \mathrm { E R M } } ( \rho , \phi ) } & { { } = } \end{array}$ $\mathbb { E } _ { \mathbf { X } , \mathbf { Y } } \left[ \ell ( \rho ( \phi ( \mathbf { X } ) ) , \mathbf { Y } ) \right]$ is the ERM loss on raw $\mathbf { Y } .$

$\mathcal { R } _ { \mathrm { s u f } } ^ { e } ( \rho , \phi )$ defined in Eq. 10 is the loss of inferred environment e on $\mathbf { Y } ^ { \mathrm { s u f } } .$ , and $\mathrm { V a r } _ { e \in E _ { \mathrm { i n f e r } } ^ { * } } \left\lceil \mathcal { R } _ { \mathrm { s u f } } ^ { ( e ) } ( \rho , \phi ) \right\rceil$ implies the variance of loss across inferred environments. The first and second terms are jointly used to ensure the sufficient predictive power of $\phi ( X )$ for $Y ^ { \mathrm { s u f } }$ , where $\lambda _ { 1 }$ controls the trade-off between introducing information of $\mu ( Y ^ { \mathrm { s u f } } ) , \sigma ( Y ^ { \mathrm { s u f } } )$ and the influence of $Z .$ . The third term further balanced by $\lambda _ { 2 }$ ensures the invariance property and is robust to marginal distribution shifts of input, theoretically guaranteed by (Krueger et al., 2021) and further balanced by $\lambda _ { 2 }$

The overall algorithm is summarized in Appendix A. Compared to the backbone, FOIL slightly increases the parameter count due to additional multiple regressors.

## 5. Experiments

## 5.1. Setup

Datasets. We conduct experiments on four popular realworld datasets commonly used as benchmarks: the daily reported exchange rates dataset (Exchange) (Lai et al., 2018), the weekly reported ratios of patients seen with influenzalike illness dataset (ILI) (Kamarthi et al., 2021a), and two hourly reported electricity transformer temperature datasets (ETTh1 and ETTh2) (Zhou et al., 2021). We adhere to the general setups and target variables selections, following previous literatures (Wu et al., 2021; 2022; Nie et al., 2022).

Backbones. As previously mentioned, our proposed FOIL is a model-agnostic framework. We select three different types of TSF models as backbones. Informer (Zhou et al., 2021) proposes an efficient transformer for long-term TSF. Crossformer (Zhang & Yan, 2022) better utilizes crossdimension dependency, making it more sensitive to spuriouse correlations. PatchTST (Nie et al., 2022) employs channel-independent and patching strategies to achieve stateof-the-art performance.

Baselines. We comprehensively compare the following twelve distribution shifts baselines: (1) Two advanced methods for handling temporal distribution shifts in TSF: NST (Liu et al., 2022) and RevIN (Kim et al., 2021). (2) Six well-acknowledged general OOD methods following (Gagnon-Audet et al., 2022), adopted due to the lack of OOD methods for TSF: (a) Methods requiring environment labels: GroupDRO (Sagawa et al., 2019), IRM (Arjovsky et al., 2019), IB-ERM (Ahuja et al., 2021), VREx (Krueger et al., 2021) and SD (Pezeshki et al., 2021). (b) Methods not requiring environment labels: EIIL (Creager et al., 2021). (3) Two hybrid methods: IRM+RevIN and EIIL+RevIN.

Implementation. Regarding the horizon window length, we considered a range from short to long-term TSF tasks. For ETTh1, ETTh2, and Exchange, the lengths are [24, 48, 96, 168, 336, 720] with a fixed lookback window size of

96 and a consistent label window size of 48 for the decoder. For the weekly reported ILI, the lengths are [4, 8, 12, 16, 20, 24], representing the next one month to six months, with a fixed lookback window size of 36 and a consistent label window size of 18 for the decoder.. Note that, we lack the availability of suitable environment labels. We address this by dividing the training set into k, tuned from 2 to 10, equallength time segments to serve as predefined environment labels. When the backbone is equipped with our FOIL, the model architecture of the backbone remains unchanged.

Evaluation. We employ the widely-adopted evaluation metrics: mean squared error (MSE) and mean absolute error (MAE). We report average performance over three independent runs for each model.

Reproducibility. All training data, testing data and code are available at: https://github.com/AdityaLab/ FOIL. More experimental details are revealed in Appendix B.

## 5.2. Results

As shown in Table 1, we present results for both original versions and corresponding FOIL equipped versions of backbones, yielding the following observations:

(1) Overall, FOIL consistently and significantly improves the performance of various TSF backbones across all datasets and forecasting lengths with improvements reaching up to 85% on MSE, thereby demonstrating FOIL’s effectiveness. For the state-of-the-art PatchTST, FOIL consistently enhances performance, achieving up to 30% improvement. For the lower-performing Informer, FOIL shows more significant improvements, frequently by an order of magnitude, yielding competitive results.

(2) FOIL excels in short-term forecasting compared to longterm forecasting, as the higher uncertainty of the latter hinders learning invariant features. Moreover, FOIL’s most significant improvement in the ILI dataset is attributed to the serious OOD shifts in its test data, particularly during the unseen COVID-19 period.

## 5.3. Comparison with Distribution Shifts Methods

In this section, we conduct a comparative analysis of the performance disparities between FOIL and existing distribution shifts methods. We employ the Informer as the forecasting backbone. The forecasting length is set as 16 for ILI and 96 for others. Similar observations are found in other settings. We measure the relative improvement compared to the best-performing baseline on each metric and dataset.

As shown in Table 2, our observations include:

(1) FOIL achieves the best performance across all datasets. The average improvements on MSE and MAE are more than 10% and 5.5% respectively, showing the benefits of FOIL over existing distribution shift methods. Notably, though hybrid models additionally alleviate the temporal distribution shift problem and exhibit better performance than general OOD baselines, FOIL still outperforms hybrid models by over 11%. Therefore, our proposed surrogate loss in Eq. 4 is irreplaceable by current instance normalization methods as discussed in Section 4.2 and exhibits important benefits for alleviating unobserved core covariates issues in the TSF task.

Time-Series Forecasting for Out-of-Distribution Generalization Using Invariant Learning

<table><tr><td colspan="2">Method</td><td colspan="2">Informer(AAAI&#x27;21)</td><td colspan="2">with FOIL</td><td colspan="2">Crossformer(ICLR&#x27;23)</td><td colspan="2">with FOIL</td><td colspan="2">PatchTST(ICLR&#x27;23)</td><td colspan="2">with FOIL</td></tr><tr><td colspan="2">Metric</td><td>MSE</td><td>MAE</td><td>MSE</td><td>MAE</td><td>MSE</td><td>MAE</td><td>MSE</td><td>MAE</td><td>MSE</td><td>MAE</td><td>MSE</td><td>MAE</td></tr><tr><td rowspan="7">Exchange</td><td>24</td><td>0.812</td><td>0.736</td><td>0.036</td><td>0.146</td><td>0.083</td><td>0.233</td><td>0.029</td><td>0.129</td><td>0.092</td><td>0.229</td><td>0.031</td><td>0.136</td></tr><tr><td>48</td><td>0.715</td><td>0.682</td><td>0.063</td><td>0.191</td><td>0.164</td><td>0.328</td><td>0.054</td><td>0.175</td><td>0.090</td><td>0.243</td><td>0.052</td><td>0.171</td></tr><tr><td>96</td><td>0.782</td><td>0.710</td><td>0.142</td><td>0.274</td><td>0.214</td><td>0.381</td><td>0.111</td><td>0.240</td><td>0.142</td><td>0.291</td><td>0.107</td><td>0.235</td></tr><tr><td>192</td><td>0.708</td><td>0.701</td><td>0.236</td><td>0.369</td><td>0.709</td><td>0.716</td><td>0.213</td><td>0.349</td><td>0.364</td><td>0.468</td><td>0.226</td><td>0.351</td></tr><tr><td>336</td><td>1.587</td><td>1.063</td><td>0.546</td><td>0.591</td><td>2.158</td><td>1.231</td><td>0.471</td><td>0.500</td><td>0.512</td><td>0.540</td><td>0.465</td><td>0.486</td></tr><tr><td>720</td><td>3.922</td><td>1.793</td><td>0.712</td><td>0.679</td><td>2.093</td><td>1.215</td><td>1.193</td><td>0.833</td><td>0.957</td><td>0.738</td><td>0.925</td><td>0.722</td></tr><tr><td>IMP.</td><td></td><td></td><td>80.58%</td><td>61.24%</td><td></td><td></td><td>61.90%</td><td>45.06%</td><td></td><td></td><td>30.60%</td><td>21.11%</td></tr><tr><td rowspan="7">ILI</td><td>4</td><td>3.212</td><td>1.530</td><td>0.736</td><td>0.593</td><td>2.147</td><td>1.232</td><td>0.332</td><td>0.400</td><td>1.043</td><td>0.587</td><td>0.616</td><td>0.507</td></tr><tr><td>8</td><td>3.668</td><td>1.642</td><td>0.881</td><td>0.667</td><td>2.678</td><td>1.403</td><td>0.569</td><td>0.512</td><td>0.638</td><td>0.557</td><td>0.586</td><td>0.546</td></tr><tr><td>12</td><td>3.974</td><td>1.722</td><td>1.069</td><td>0.768</td><td>2.914</td><td>1.476</td><td>0.706</td><td>0.575</td><td>0.959</td><td>0.795</td><td>0.560</td><td>0.519</td></tr><tr><td>16</td><td>4.187</td><td>1.773</td><td>1.047</td><td>0.779</td><td>3.496</td><td>1.628</td><td>0.701</td><td>0.568</td><td>0.726</td><td>0.563</td><td>0.696</td><td>0.555</td></tr><tr><td>20</td><td>4.296</td><td>1.806</td><td>1.011</td><td>0.797</td><td>3.589</td><td>1.653</td><td>0.702</td><td>0.596</td><td>0.807</td><td>0.705</td><td>0.571</td><td>0.541</td></tr><tr><td>24</td><td>4.445</td><td>1.844</td><td>1.014</td><td>0.806</td><td>3.513</td><td>1.633</td><td>0.686</td><td>0.604</td><td>1.072</td><td>0.850</td><td>0.663</td><td>0.625</td></tr><tr><td>IMP.</td><td></td><td></td><td>75.80%</td><td>57.37%</td><td></td><td></td><td>79.99%</td><td>64.03%</td><td></td><td></td><td>27.04%</td><td>16.91%</td></tr><tr><td rowspan="7">ETTh1</td><td>24</td><td>0.219</td><td>0.392</td><td>0.038</td><td>0.146</td><td>0.194</td><td>0.400</td><td>0.028</td><td>0.126</td><td>0.031</td><td>0.136</td><td>0.027</td><td>0.126</td></tr><tr><td>48</td><td>0.474</td><td>0.638</td><td>0.065</td><td>0.190</td><td>0.270</td><td>0.465</td><td>0.042</td><td>0.156</td><td>0.044</td><td>0.160</td><td>0.041</td><td>0.154</td></tr><tr><td>96</td><td>0.965</td><td>0.892</td><td>0.088</td><td>0.224</td><td>0.146</td><td>0.312</td><td>0.056</td><td>0.181</td><td>0.061</td><td>0.190</td><td>0.056</td><td>0.182</td></tr><tr><td>192</td><td>1.029</td><td>0.967</td><td>0.148</td><td>0.299</td><td>0.241</td><td>0.420</td><td>0.075</td><td>0.209</td><td>0.082</td><td>0.223</td><td>0.078</td><td>0.215</td></tr><tr><td>336</td><td>0.677</td><td>0.769</td><td>0.136</td><td>0.296</td><td>0.246</td><td>0.425</td><td>0.088</td><td>0.233</td><td>0.100</td><td>0.246</td><td>0.092</td><td>0.237</td></tr><tr><td>720</td><td>1.086</td><td>0.973</td><td>0.132</td><td>0.288</td><td>0.392</td><td>0.554</td><td>0.104</td><td>0.254</td><td>0.154</td><td>0.310</td><td>0.120</td><td>0.272</td></tr><tr><td>IMP.</td><td></td><td></td><td>85.38%</td><td>68.14%</td><td></td><td></td><td>73.04%</td><td>54.43%</td><td></td><td></td><td>10.48%</td><td>5.80%</td></tr><tr><td rowspan="7">ETTh2</td><td>24</td><td>0.668</td><td>0.705</td><td>0.121</td><td>0.275</td><td>0.136</td><td>0.299</td><td>0.071</td><td>0.198</td><td>0.080</td><td>0.215</td><td>0.071</td><td>0.197</td></tr><tr><td>48</td><td>0.999</td><td>0.866</td><td>0.258</td><td>0.407</td><td>0.122</td><td>0.274</td><td>0.106</td><td>0.248</td><td>0.106</td><td>0.248</td><td>0.103</td><td>0.241</td></tr><tr><td>96</td><td>3.070</td><td>1.628</td><td>0.222</td><td>0.369</td><td>0.256</td><td>0.408</td><td>0.137</td><td>0.286</td><td>0.156</td><td>0.309</td><td>0.140</td><td>0.289</td></tr><tr><td>192</td><td>3.548</td><td>1.768</td><td>0.699</td><td>0.682</td><td>1.257</td><td>1.034</td><td>0.198</td><td>0.352</td><td>0.217</td><td>0.374</td><td>0.201</td><td>0.356</td></tr><tr><td>336</td><td>2.663</td><td>1.526</td><td>0.801</td><td>0.756</td><td>1.305</td><td>1.027</td><td>0.234</td><td>0.389</td><td>0.233</td><td>0.390</td><td>0.216</td><td>0.372</td></tr><tr><td>720</td><td>2.335</td><td>1.422</td><td>0.730</td><td>0.725</td><td>1.579</td><td>1.158</td><td>0.253</td><td>0.402</td><td>0.317</td><td>0.448</td><td>0.238</td><td>0.391</td></tr><tr><td>IMP.</td><td></td><td></td><td>78.03%</td><td>58.82%</td><td></td><td></td><td>59.61%</td><td>44.42%</td><td></td><td></td><td>10.65%</td><td>6.64%</td></tr></table>

Table 1. Performance comparison between original and FOIL equipped versions of backbones. The top-performing version is marked in bold. IMP. is the average percentage improvement across lengths of horizon window compared to the original version. FOIL consistently and significantly enhances the performance of various TSF backbones on all datasets and metrics across horizon window lengths.

(2) General OOD methods exhibit poor performances. This verifies that directly applying existing invariant learning methods for the TSF task is inappropriate, as discussed in Section 3.

(3) Among the existing general OOD methods, EIIL exhibits better performance than other baselines, due to their capability to infer proper environments from the data. Besides, the performances of EIIL also suggest the advantages of inferring environments at representation spaces as opposed to raw feature spaces for TSF’s high-dimensional input. These observed advantages align with the considerations made in FOIL.

## 5.4. Ablation Study

To demonstrate the effectiveness of each module or loss in FOIL, we conduct an ablation study that introduces three ablated versions of FOIL: (1) FOIL \Suf: remove the surrogate loss in Eq. 4 for decomposing Sufficiently predictable Y<sup>suf</sup> (2) FOIL \TEI: remove the whole Time-series Environment Inference module detailed in Section 4.3,i.e. set the number of environment as 1.(3) FOIL \LP: removed the Label Propagation approach in M<sub>TEI</sub> in Eq. 8. All other experiment setups follow Section 5.3. The ablation study results are shown in Figure 3(a).

Though FOIL outperforms all ablated versions in forecasting accuracy, all designed modules and loss in FOIL show individual effectiveness through the ablation study. Specifically, the performance FOIL \Suf drops significantly more than other ablated versions, which indicates the necessity of mitigating unobserved covariate issues when applying invariant learning for TSF. Moreover, FOIL \TEI consistently outperforms FOIL \LP across all datasets, which validates the effectiveness of preserving the temporal adjacency structure for Time Series Forecasting (TSF).

Time-Series Forecasting for Out-of-Distribution Generalization Using Invariant Learning

<table><tr><td colspan="3">Dataset</td><td colspan="2">Exchange</td><td colspan="2">ILI</td><td colspan="2">ETTh1</td><td colspan="2">ETTh2</td></tr><tr><td>Type</td><td>Env. Known?</td><td>Method</td><td>MSE</td><td>MAE</td><td>MSE</td><td>MAE</td><td>MSE</td><td>MAE</td><td>MSE</td><td>MAE</td></tr><tr><td>Base</td><td>No</td><td>ERM</td><td>0.782</td><td>0.710</td><td>3.974</td><td>1.722</td><td>0.965</td><td>0.892</td><td>3.070</td><td>1.628</td></tr><tr><td rowspan="6">General OOD (Invariant Learning)</td><td rowspan="5">Yes</td><td>GroupDRO</td><td>0.781</td><td>0.715</td><td>3.721</td><td>1.888</td><td>0.880</td><td>0.863</td><td>3.192</td><td>1.647</td></tr><tr><td>IRM</td><td>0.716</td><td>0.688</td><td>3.608</td><td>1.732</td><td>0.495</td><td>0.646</td><td>2.910</td><td>1.581</td></tr><tr><td>VREx</td><td>0.781</td><td>0.715</td><td>3.671</td><td>1.875</td><td>0.874</td><td>0.859</td><td>3.238</td><td>1.662</td></tr><tr><td>SD</td><td>0.782</td><td>0.716</td><td>3.674</td><td>1.677</td><td>0.891</td><td>0.870</td><td>3.246</td><td>1.664</td></tr><tr><td>IB-ERM</td><td>0.787</td><td>0.719</td><td>3.673</td><td>1.677</td><td>0.883</td><td>0.865</td><td>3.209</td><td>1.654</td></tr><tr><td>No</td><td>EIIL</td><td>0.540</td><td>0.630</td><td>3.251</td><td>1.648</td><td>0.673</td><td>0.783</td><td>1.252</td><td>1.013</td></tr><tr><td rowspan="2">Temporal Shifts</td><td rowspan="2">NA</td><td>RevIN</td><td>0.169</td><td>0.296</td><td>1.350</td><td>0.867</td><td>0.108</td><td>0.248</td><td>0.236</td><td>0.387</td></tr><tr><td>NST</td><td>0.151</td><td>0.281</td><td>1.351</td><td>0.871</td><td>0.118</td><td>0.260</td><td>0.258</td><td>0.406</td></tr><tr><td rowspan="2">Hybrid</td><td>Yes</td><td>IRM+RevIN</td><td>0.160</td><td>0.291</td><td>1.328</td><td>0.863</td><td>0.105</td><td>0.244</td><td>0.234</td><td>0.381</td></tr><tr><td>No</td><td>EIIL+RevIN</td><td>0.170</td><td>0.309</td><td>1.205</td><td>0.820</td><td>0.097</td><td>0.241</td><td>0.343</td><td>0.483</td></tr><tr><td>Ours</td><td>No</td><td>FOIL</td><td>0.136</td><td>0.274</td><td>1.047</td><td>0.768</td><td>0.088</td><td>0.224</td><td>0.210</td><td>0.358</td></tr><tr><td colspan="3">Improvement(%)</td><td>+9.93</td><td>+2.50</td><td>+12.94</td><td>+5.00</td><td>+9.27</td><td>+7.05</td><td>+10.26</td><td>+6.04</td></tr></table>

Table 2. Comparison with existing distribution shifts methods across four datasets using Informer backbone. The best results are in bold. NA means not considering environments. Our FOIL outperforms all existing distribution shift methods on all datasets and both metrics.

## 5.5. Case Study: Analysis of Inferred Environments

To justify the reasonableness of the environments inferred by FOIL, we conduct a case study on the ILI dataset by demonstrating the contribution disparities among three major components (Summer, i.e., June to August annually; Winter, i.e., December to February annually; and the H1N1-09 period, i.e., April 2009 to August 2010) when the total number of inferred environments is set to 2. The visualization of contributions from each component is shown in Figure 3(b). The visualization results align with public health perspectives in two ways: First, the major components of Environment 1 and 2 are distinguished by Winter and Summer, as influenza is a seasonal disease and typically spreads during the winter and ends before the summer. Second, the H1N1-09 period has more contributions in Environment 1 than 2, which aligns with the fact that the H1N1-09 period and winter flu seasons exhibit similarities. These observations support the ability of FOIL to infer meaningful environments in real-world TSF applications.

## 6. Additional Related Works

## 6.1. Time Series Forecasting

Classical TSF models (Tsay, 2000; Ariyo et al., 2014; Zhang, 2003) often face limitations in capturing complex patterns due to their inherent model constraints. Recent advancements in deep learning methods, such as Recurrent Neural Networks (RNN) and Transformer (Rumelhart et al., 1986; Hochreiter & Schmidhuber, 1997; Vaswani et al., 2017), have led to sophisticated deep TSF models including Informer, Reformer, Autoformer, Fedformer, and PatchTST (Zhou et al., 2021; Kitaev et al., 2020; Wu et al., 2021; Zhou et al., 2022; Nie et al., 2022), significantly improving forecasting accuracy. However, these advanced models primarily rely on ERM with simple IID assumptions. Consequently, they exhibit shortcomings in OOD generalization when faced with potential distribution shifts in TS data.

![](images/8cfd363c5dc92d397104bc803ad6e27fa2d28681fe867db82f56e2593ab013db.jpg)

![](images/ae02126bde733817e17328feaa69abdc88d05cedfc124dfb2c5e42cdd00758d0.jpg)  
(a) Ablation study of our (b) Analysis of two inferred enmethod and three ablated ver- vironments on ILI showing sigsions showing the effectiveness nificant differences in compoof the model design. nent weights.  
Figure 3. Results of analytical experiments.

## 6.2. Distribution Shifts in Time-Series Forecasting.

In addition to the aforementioned TSF methods in handling marginal distribution shifts (Passalis et al., 2019; Kim et al., 2021; Liu et al., 2022; Fan et al., 2023; Du et al., 2021), there are some efforts that have tackled OOD challenges in TSF. However, all have certain limitations. For example, DIVERSITY (Lu et al., 2022; 2023) is specifically designed for time series classification and detection tasks. OneNet (Zhang et al., 2023) is tailored for online forecasting scenarios by online ensembling. Pets (Zhao et al., 2023) focuses on distribution shifts induced by the specific phenomenon of performativity. This highlights the need for a general OOD method applicable across diverse TSF scenarios and models.

Despite the existing benchmark WOODS (Gagnon-Audet et al., 2022) that evaluates IL methods combined with TSF models with a focus on TS classification tasks, our proposed approach addresses diverse datasets under realistic TSF scenarios, offering different and comprehensive problem formulation, methodology, and evaluations.

## 7. Conclusion and Discussion

In this paper, we formally study the fundamental outof-distribution challenges in time-series forecasting tasks (OOD-TSF). We identify specific gaps when applying existing invariant learning methods to OOD-TSF, including theoretical violations of sufficiency and invariance assumptions and the empirical absence of environment labels in time-series datasets. To address these challenges, we introduce a model-agnostic framework named FOIL, which employs an innovative surrogate loss to alleviate the impact of unobserved variables. FOIL features a joint optimization strategy, which learns invariant representations and preserves temporal adjacency structure. Empirical evaluations demonstrate the effectiveness of FOIL by consistently improving the performances of different TSF models and outperforming other OOD solutions.

Beyond the scope of FOIL, it is important to recognize that invariant learning is not the only solution to enhance OOD generalization in TSF tasks. Alternative approaches or interpretations can require advanced causal analysis, feature selections, or learning dynamic temporal patterns. The using of additional information to enhance the sufficiency of predictions also deserves to be explored. We also emphasize the need for conscientious evaluations on underrepresented subgroups when implementing our approach in real-world scenarios for promoting fairness among subgroups. We expect that future research will delve into these open questions, contributing both theoretically and practically to advance the understanding of OOD-TSF challenges and achieve more reliable TSF models.

## Impact Statement

Our work introduces a new methodology to improve the out-of-distribution generalization of time-series forecasting models and is applicable across wide range of domains and real-world applications including sensitive applications in public health, economics, etc. Therefore, care should be taken in alleviating biases and disparities in dataset as well as making sure the predictions of model do not pose ethical risks or lead to inequitable outcomes across various stakeholders relevant to specific applications our methods are used.

## Acknowledgements

We thank the anonymous reviewers for their helpful comments. This paper was supported in part by the NSF (Expeditions CCF-1918770, CAREER IIS-2028586, Medium IIS-1955883, Medium IIS-2106961, PIPP CCF-2200269, IIS-2008334, CAREER IIS-2144338), CDC MInD program, Meta faculty gifts, and funds/computing resources from Georgia Tech.

## References

Ahuja, K., Caballero, E., Zhang, D., Gagnon-Audet, J.-C., Bengio, Y., Mitliagkas, I., and Rish, I. Invariance principle meets information bottleneck for out-of-distribution generalization. Advances in Neural Information Processing Systems, 34:3438–3450, 2021.

Anderson, T. W. The statistical analysis of time series. John Wiley & Sons, 2011.

Ariyo, A. A., Adewumi, A. O., and Ayo, C. K. Stock price prediction using the arima model. In 2014 UKSim-AMSS 16th international conference on computer modelling and simulation, pp. 106–112. IEEE, 2014.

Arjovsky, M., Bottou, L., Gulrajani, I., and Lopez-Paz, D. Invariant risk minimization. arXiv preprint arXiv:1907.02893, 2019.

Chang, S., Zhang, Y., Yu, M., and Jaakkola, T. Invariant rationalization. In International Conference on Machine Learning, pp. 1448–1458. PMLR, 2020.

Cheng, C., Sa-Ngasoongsong, A., Beyca, O., Le, T., Yang, H., Kong, Z., and Bukkapatnam, S. T. Time series forecasting for nonlinear and non-stationary processes: a review and comparative study. Iie Transactions, 47(10): 1053–1071, 2015.

Creager, E., Jacobsen, J.-H., and Zemel, R. Environment inference for invariant learning. In International Conference on Machine Learning, pp. 2189–2200. PMLR, 2021.

Du, Y., Wang, J., Feng, W., Pan, S., Qin, T., Xu, R., and Wang, C. Adarnn: Adaptive learning and forecasting of time series. In Proceedings ofthe 30th ACM international conference on information & knowledge management, pp. 402–411, 2021.

Fan, W., Wang, P., Wang, D., Wang, D., Zhou, Y., and Fu, Y. Dish-ts: a general paradigm for alleviating distribution shift in time series forecasting. In Proceedings of the AAAI Conference on Artificial Intelligence, volume 37, pp. 7522–7529, 2023.

Gagnon-Audet, J.-C., Ahuja, K., Darvishi-Bayazi, M.-J., Mousavi, P., Dumas, G., and Rish, I. Woods: Benchmarks for out-of-distribution generalization in time series. arXiv preprint arXiv:2203.09978, 2022.

Gong, M., Zhang, K., Liu, T., Tao, D., Glymour, C., and Scholkopf, B. Domain adaptation with conditional trans-¨ ferable components. In International conference on machine learning, pp. 2839–2848. PMLR, 2016.

Gruver, N., Finzi, M., Qiu, S., and Wilson, A. G. Large language models are zero-shot time series forecasters. arXiv preprint arXiv:2310.07820, 2023.

Hochreiter, S. and Schmidhuber, J. Long short-term memory. Neural computation, 9(8):1735–1780, 1997.

Hoyer, P., Janzing, D., Mooij, J. M., Peters, J., and Scholkopf, B. Nonlinear causal discovery with additive¨ noise models. Advances in neural information processing systems, 21, 2008.

Huang, B.-W., Liao, K.-T., Kao, C.-S., and Lin, S.-D. Environment diversification with multi-head neural network for invariant learning. Advances in Neural Information Processing Systems, 35:915–927, 2022.

Kamarthi, H., Kong, L., Rodriguez, A., Zhang, C., and Prakash, B. A. When in doubt: Neural non-parametric uncertainty quantification for epidemic forecasting. Advances in Neural Information Processing Systems, 34: 19796–19807, 2021a.

Kamarthi, H., Kong, L., Rodriguez, A., Zhang, C., and Prakash, B. A. When in doubt: Neural non-parametric uncertainty quantification for epidemic forecasting. Advances in Neural Information Processing Systems, 34: 19796–19807, 2021b.

Kamarthi, H., Kong, L., Rodr´ıguez, A., Zhang, C., and Prakash, B. A. Camul: Calibrated and accurate multiview time-series forecasting. In Proceedings of the ACM Web Conference 2022, pp. 3174–3185, 2022.

Kim, T., Kim, J., Tae, Y., Park, C., Choi, J.-H., and Choo, J. Reversible instance normalization for accurate time-series forecasting against distribution shift. In International Conference on Learning Representations, 2021.

Kitaev, N., Kaiser, Ł., and Levskaya, A. Reformer: The efficient transformer. arXiv preprint arXiv:2001.04451, 2020.

Koyama, M. and Yamaguchi, S. When is invariance useful in an out-of-distribution generalization problem? arXiv preprint arXiv:2008.01883, 2020.

Krueger, D., Caballero, E., Jacobsen, J.-H., Zhang, A., Binas, J., Zhang, D., Le Priol, R., and Courville, A. Outof-distribution generalization via risk extrapolation (rex). In International Conference on Machine Learning, pp. 5815–5826. PMLR, 2021.

Lai, G., Chang, W.-C., Yang, Y., and Liu, H. Modeling long-and short-term temporal patterns with deep neural networks. In The 41st international ACM SIGIR conference on research & development in information retrieval, pp. 95–104, 2018.

Lim, B. and Zohren, S. Time-series forecasting with deep learning: a survey. Philosophical Transactions of the Royal Society A, 379(2194):20200209, 2021.

Lin, Y., Zhu, S., Tan, L., and Cui, P. Zin: When and how to learn invariance without environment partition? Advances in Neural Information Processing Systems, 35: 24529–24542, 2022.

Liu, J., Hu, Z., Cui, P., Li, B., and Shen, Z. Heterogeneous risk minimization. In International Conference on Machine Learning, pp. 6804–6814. PMLR, 2021a.

Liu, J., Hu, Z., Cui, P., Li, B., and Shen, Z. Integrated latent heterogeneity and invariance learning in kernel space. Advances in Neural Information Processing Systems, 34: 21720–21731, 2021b.

Liu, J., Shen, Z., He, Y., Zhang, X., Xu, R., Yu, H., and Cui, P. Towards out-of-distribution generalization: A survey. arXiv preprint arXiv:2108.13624, 2021c.

Liu, Y., Wu, H., Wang, J., and Long, M. Non-stationary transformers: Exploring the stationarity in time series forecasting. Advances in Neural Information Processing Systems, 35:9881–9893, 2022.

Lu, W., Wang, J., Sun, X., Chen, Y., and Xie, X. Out-ofdistribution representation learning for time series classification. In The Eleventh International Conference on Learning Representations, 2022.

Lu, W., Wang, J., Sun, X., Chen, Y., Ji, X., Yang, Q., and Xie, X. Diversify: A general framework for time series out-of-distribution detection and generalization. arXiv preprint arXiv:2308.02282, 2023.

Maeda, T. N. and Shimizu, S. Causal additive models with unobserved variables. In Uncertainty in Artificial Intelligence, pp. 97–106. PMLR, 2021.

Makinen, T. M., Juvonen, R., Jokelainen, J., Harju,¨ T. H., Peitso, A., Bloigu, A., Silvennoinen-Kassinen, S., Leinonen, M., and Hassi, J. Cold temperature and low humidity are associated with increased occurrence of respiratory tract infections. Respiratory medicine, 103(3): 456–462, 2009.

Mourtzoukou, E. and Falagas, M. E. Exposure to cold and respiratory tract infections. The International Journal of Tuberculosis and Lung Disease, 11(9):938–943, 2007.

Nerlove, M., Grether, D. M., and Carvalho, J. L. Analysis of economic time series: a synthesis. Academic Press, 2014.

Nie, Y., Nguyen, N. H., Sinthong, P., and Kalagnanam, J. A time series is worth 64 words: Long-term forecasting with transformers. In The Eleventh International Conference on Learning Representations, 2022.

Passalis, N., Tefas, A., Kanniainen, J., Gabbouj, M., and Iosifidis, A. Deep adaptive input normalization for time series forecasting. IEEE transactions on neural networks and learning systems, 31(9):3760–3765, 2019.

Pearl, J. et al. Causality: Models, reasoning and inference. Cambridge, UK: CambridgeUniversityPress, 19(2): 3, 2000.

Peters, J., Buhlmann, P., and Meinshausen, N. Causal in-¨ ference by using invariant prediction: identification and confidence intervals. Journal ofthe Royal Statistical Society Series B: Statistical Methodology, 78(5):947–1012, 2016.

Pezeshki, M., Kaba, O., Bengio, Y., Courville, A. C., Precup, D., and Lajoie, G. Gradient starvation: A learning proclivity in neural networks. Advances in Neural Information Processing Systems, 34:1256–1272, 2021.

Rodriguez, A., Tabassum, A., Cui, J., Xie, J., Ho, J., Agarwal, P., Adhikari, B., and Prakash, B. A. Deepcovid: An operational deep learning-driven framework for explainable real-time covid-19 forecasting. In Proceedings ofthe AAAI Conference on Artificial Intelligence, volume 35, pp. 15393–15400, 2021.

Rojas-Carulla, M., Scholkopf, B., Turner, R., and Peters, J.¨ Invariant models for causal transfer learning. The Journal ofMachine Learning Research, 19(1):1309–1342, 2018.

Rumelhart, D. E., Hinton, G. E., and Williams, R. J. Learning representations by back-propagating errors. nature, 323(6088):533–536, 1986.

Sagawa, S., Koh, P. W., Hashimoto, T. B., and Liang, P. Distributionally robust neural networks for group shifts: On the importance of regularization for worst-case generalization. arXiv preprint arXiv:1911.08731, 2019.

Sancho, J. M., San Miguel, M., Katz, S., and Gunton, J. Analytical and numerical studies of multiplicative noise. Physical Review A, 26(3):1589, 1982.

Sezer, O. B., Gudelek, M. U., and Ozbayoglu, A. M. Financial time series forecasting with deep learning: A systematic literature review: 2005–2019. Applied soft computing, 90:106181, 2020.

Tabassum, A., Chinthavali, S., Tansakul, V., and Prakash, B. A. Actionable insights in multivariate time-series for urban analytics. 2021.

Tsay, R. S. Time series and forecasting: Brief history and future research. Journal ofthe American Statistical Association, 95(450):638–643, 2000.

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., and Polosukhin, I. Attention is all you need. Advances in neural information processing systems, 30, 2017.

Weber, M. G., Li, L., Wang, B., Zhao, Z., Li, B., and Zhang, C. Certifying out-of-domain generalization for blackbox functions. In International Conference on Machine Learning, pp. 23527–23548. PMLR, 2022.

Wooldridge, J. M. Multiplicative panel data models without the strict exogeneity assumption. Econometric Theory, 13(5):667–678, 1997.

Wu, H., Xu, J., Wang, J., and Long, M. Autoformer: Decomposition transformers with auto-correlation for long-term series forecasting. Advances in Neural Information Processing Systems, 34:22419–22430, 2021.

Wu, H., Hu, T., Liu, Y., Zhou, H., Wang, J., and Long, M. Timesnet: Temporal 2d-variation modeling for general time series analysis. arXiv preprint arXiv:2210.02186, 2022.

Ye, N., Zhu, L., Wang, J., Zeng, Z., Shao, J., Peng, C., Pan, B., Li, K., and Zhu, J. Certifiable out-of-distribution generalization. In Proceedings ofthe AAAI Conference on Artificial Intelligence, volume 37, pp. 10927–10935, 2023.

Zhang, G. P. Time series forecasting using a hybrid arima and neural network model. Neurocomputing, 50:159–175, 2003.

Zhang, Y. and Yan, J. Crossformer: Transformer utilizing cross-dimension dependency for multivariate time series forecasting. In The Eleventh International Conference on Learning Representations, 2022.

Zhang, Y.-F., Wen, Q., Wang, X., Chen, W., Sun, L., Zhang, Z., Wang, L., Jin, R., and Tan, T. Onenet: Enhancing time series forecasting models under concept drift by online ensembling. arXiv preprint arXiv:2309.12659, 2023.

Zhao, Z., Rodriguez, A., and Prakash, B. A. Performative time-series forecasting. arXiv preprint arXiv:2310.06077, 2023.

Zhou, H., Zhang, S., Peng, J., Zhang, S., Li, J., Xiong, H., and Zhang, W. Informer: Beyond efficient transformer for long sequence time-series forecasting. In Proceedings of the AAAI conference on artificial intelligence, volume 35, pp. 11106–11115, 2021.

Zhou, T., Ma, Z., Wen, Q., Wang, X., Sun, L., and Jin, R. Fedformer: Frequency enhanced decomposed transformer for long-term series forecasting. In International Conference on Machine Learning, pp. 27268–27286. PMLR, 2022.

## A. Algorithm

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 The training procedure of our FOIL.

Require: Time-series dataset  $\mathcal{D} = \{(\mathbf{X}_{i}, \mathbf{Y}_{i})\}_{i=1}^{N}$ 

Ensure: An optimized predictor  $\rho(\phi(\cdot)) : \mathcal{X} \to \mathcal{Y}$ 

Initialize  $\rho(\cdot), \{\rho^{(e)}(\cdot)\}, \phi(\cdot)$ 

Random assign environment label for each  $(\mathbf{X}_{i}, \mathbf{Y}_{i})$ .

while not converged do

Stage 1: Time-series Invariant Learning: Update  $\phi(\cdot), \rho(\cdot)$  according to Equation 10.

Stage 2: Time-series Environment Inference:

M Step: Fit models according to Equation 6, update  $\{\rho^{(e)}\}$ .

E Step: Reallocate environment labels according to Equation 7 and Equation 8.

end while

return  $\rho(\cdot)$  and  $\phi(\cdot)$ .
</div>

## B. Additional Experimental Details

## B.1. Datasets

We conduct experiments on four real-world datasets, commonly used as benchmark datasets:

• Exchange dataset records the daily exchange rates of eight currencies.

• ETTh1 and ETTh2 datasets record the hourly electricity transformer temperature, comprising two years of data collected from two separate counties in China. They include seven variables. We omitted ETTm1 and ETTm2 as they share the same data source as ETTh1 and ETTh2, but with different sampling frequencies.

• ILI dataset collects data on influenza-like illness patients weekly, with eight variables. We mainly follow (Wu et al., 2022) to preprocess data, split datasets into train/validation/test sets and select the target variables. All datasets are preprocessed using the zero-mean normalization method.

## B.2. Backbones

As aforementioned, our proposed FOIL is a model-agnostic framework. We select three different types of TSF models as backbones. Informer (Zhou et al., 2021) proposes an efficient transformer for long-term TSF. Crossformer (Zhang & Yan, 2022) better utilizes cross-dimension dependency, making it more sensitive to spuriouse correlations. PatchTST (Nie et al., 2022) employs channel-independent and patching strategies to achieve state-of-the-art performance.

## B.3. Baselines: General OOD Methods

• Methods with Environment Labels: IRM (Arjovsky et al., 2019) introduces a penalty to learn invariant predictors across different environments. On the basis of the invariance principle of IRM, IB-ERM (Ahuja et al., 2021) incorporates the information bottleneck constraint. VREx (Krueger et al., 2021) propose a penalty on the variance of training risks between environments as a simple agent of risk extrapolation. SD (Pezeshki et al., 2021) proposes a regularization method aimed at decoupling feature learning dynamics to achieve better OOD generalization.GroupDRO (Sagawa et al., 2019), a regularizer for worst-case group generalization, often considered to have general OOD generalization capabilities.

• Methods without Environment Labels: EIIL (Creager et al., 2021) infers the most informative environments for downstream learning invariant predictors by maximizing the penalty in IRM.

We omit AdaRNN (Du et al., 2021) for not being model-agnostic; DIVERSITY (Lu et al., 2022; 2023), as it’s specific to time series classification and detection tasks; and multi-view TSF methods (Kamarthi et al., 2022), which treat each covariate as one view and inflate the parameter count, leading to unfair comparison.

## B.4. Implementation

For the backbones, we utilize implementations and hyperparameter settings from the Time Series Library<sup>1</sup>. For general OOD methods, we employ the implementations and tune hyperparameter suggested by DomainBed<sup>2</sup>. For TSF methods, we use the implementations and hyperparameter settings from their corresponding papers. We have added an MLP to the end of PatchTST to utilize covariates effectively. For our proposed framework FOIL, we also incorporate RevIN like PatchTST to address the issue of non-stationarity. We perform affine transformation on each dimension of the raw covariate through learnable weight variables to better find invariant features and improve out-of-distribution generalization capabilities.