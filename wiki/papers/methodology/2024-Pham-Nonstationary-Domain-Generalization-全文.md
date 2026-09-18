---
title: "2024-Pham-Nonstationary-Domain-Generalization"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2024-Pham-Nonstationary-Domain-Generalization.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Non-stationary Domain Generalization: Theory and Algorithm

Thai-Hoang Pham<sup>1,2</sup>

Xueru Zhang<sup>1</sup>

Ping Zhang<sup>1,2</sup>

<sup>1</sup>Department of Computer Science and Engineering, The Ohio State University, USA <sup>2</sup>Department of Biomedical Informatics, The Ohio State University, USA {pham.375,zhang.12807,zhang.10631}@osu.edu

## Abstract

Although recent advances in machine learning have shown its success to learn from independent and identically distributed (IID) data, it is vulnerable to out-of-distribution (OOD) data in an open world. Domain generalization (DG) deals with such an issue and it aims to learn a model from multiple source domains that can be generalized to unseen target domains. Existing studies on DG have largely focused on stationary settings with homogeneous source domains. However, in many applications, domains may evolve along a specific direction (e.g., time, space). Without accounting for such non-stationary patterns, models trained with existing methods may fail to generalize on OOD data. In this paper, we study domain generalization in non-stationary environment. We first examine the impact of environmental nonstationarity on model performance and establish the theoretical upper bounds for the model error at target domains. Then, we propose a novel algorithm based on adaptive invariant representation learning, which leverages the non-stationary pattern to train a model that attains good performance on target domains. Experiments on both synthetic and real data validate the proposed algorithm.

## 1 INTRODUCTION

Many machine learning (ML) systems are built based on an assumption that training and testing data are sampled independently and identically from the same distribution. However, this is commonly violated in real applications where the environment changes during model deployment, and there exist distribution shifts between training and testing data. The problem of training models that are robust under distribution shifts is typically referred to as domain adaptation (or generalization), where the goal is to train a model on source domain that can generalize well on a target domain. Specifically, domain adaptation (DA) aims to deploy model on a specific target domain, and it assumes the data from this target domain is accessible during training. In contrast, domain generalization (DG) considers a more realistic scenario where target domain data is unavailable during training; instead it leverages multiple source domains to learn models that generalize to unseen target domains.

For both DA and DG, various approaches have been proposed to learn a robust model with high performance on target domains. However, most of them assume both source and target domains are sampled from a stationary environment; they are not suitable for settings where the data distribution evolves along a specific direction (e.g., time, space). In stationary DG, the domains are treated as an unordered set, while in non-stationary DG, they form an ordered tuple with a sequential structure (see Figure 1). This defining characteristic of non-stationary DG renders this setting a challenging task, necessitating novel solutions that account for non-stationary mechanisms. In practice, evolvable data distributions have been observed in many applications. For example, satellite images change over time due to city development and climate change [Christie et al., 2018], clinical data evolves due to changes in disease prevalence [Guo et al., 2022], facial images gradually evolve because of the changes in fashion and social norms [Ginosar et al., 2015]. Without accounting for the non-stationary patterns across domains, existing methods in DA/DG designed for stationary settings may not perform well in non-stationary environments. As evidenced by Guo et al. [2022], clinical predictive models trained under existing DA/DG methods cannot perform better on future clinical data compared to empirical risk minimization.

In this paper, we study domain generalization (DG) in non-stationary environments. The goal is to learn a model from a sequence of source domains that can capture the non-stationary patterns and generalize well to (multiple) unseen target domains. We first examine the impacts of non-stationary distribution shifts and study how the mode performance attained on source domains can be affected when the model is deployed on target domains. Based on the theoretical findings, we propose an algorithm named Adaptive Invariant Representation Learning (AIRL); it minimizes the error on target domains by learning a sequence of representations that are invariant for every two consecutive source domains but are adaptive across these pairs.

In particular, AIRL consists of two components: (i) representation network, which is trained on the sequence of source domains to learn invariant representations between every two consecutive source domains, (ii) classification network that minimizes the prediction errors on source domains. Our main idea is to create adaptive representation and classification networks that can evolve in response to the dynamic environment. In other words, we aim to find networks that can effectively capture the non-stationary patterns from the sequence of source domains. At the inference stage, the representation network is used to generate the optimal representation mappings and the classification network is used to make predictions in the target domains, without the need to access their data. To verify the effectiveness of AIRL, we conduct extensive experiments on both synthetic and real data and compare AIRL with various existing methods.

## 2 RELATED WORK

This work is closely related to the literature on domain generalization, continuous (or gradual) domain adaptation, continual learning. We introduce each topic and discuss their differences with our work.

Domain generalization. The goal is to learn a model on multiple source domains that can generalize to the out-ofdistribution samples from an unseen target domain. Depending on the learning strategy, existing works for DG can be roughly classified into three categories: (i) methods based on domain-invariant representation learning [Phung et al., 2021, Nguyen et al., 2021a, Pham et al., 2023]; (ii) methods based on data manipulation [Qiao et al., 2020, Zhou et al., 2020]; (iii) methods by considering DG in general ML paradigms and using approaches such as meta-learning [Li et al., 2018a, Balaji et al., 2018], gradient operation [Rame et al., 2021, Tian et al., 2022], self-supervised learning [Jeon et al., 2021, Li et al., 2021], and distributional robustness [Koh et al., 2021, Wang et al., 2021]. However, these works assume both source and target domains are sampled from a stationary environment and they do not consider the non-stationary patterns across domains; this differs from our setting.

Non-stationary domain generalization. To the best of our knowledge, only a few concurrent works study domain generalization in non-stationary environments [Bai et al., 2022, Qin et al., 2022, Zeng et al., 2023, Xie et al., 2024, Zeng et al., 2024b,a]. However, the problem settings considered in these works are rather limited. For example, Qin et al. [2022] only focuses on the environments that evolve based on a consistent and stationary transition function; the approaches in Bai et al. [2022], Zeng et al. [2023, 2024b] can only generalize the model to a single subsequent target domain; Qin et al. [2022], Xie et al. [2024], Zeng et al. [2024a] assume that data are aligned across domain sequence. In contrast, this paper considers a more general setting where data may evolve based on non-stationary dynamics, and the proposed algorithm learned from the sequence of unaligned source domains can generate models for multiple unseen target domains.

Continuous domain adaptation. Unlike conventional DA/DG methods that only consider categorical domain labels, continuous DA admits continuous domain labels such as space, time [Ortiz-Jimenez et al., 2019, Wang et al., 2020]. Specifically, this line of research considers scenarios where the data distribution changes gradually and domain labels are continuous. Similar to conventional DA, samples from target domain are required to guide the model adaptation process. This is in contrast to this study, which considers the target domains whose samples are inaccessible during training.

Gradual domain adaptation. Similar to continuous DA, Gradual DA also considers continuous domain labels, and the samples from the target domain are accessible during training [Kumar et al., 2020, Chen et al., 2020, Chen and Chao, 2021]. The prime difference is that continuous DA focuses on the generalization from a single source domain to a target domain, whereas there are multiple source domains in gradual DA.

Continual learning. The goal is to learn a model continuously from a sequence of tasks. The main focus in continual learning is to overcome the issue of catastrophic forgetting, i.e., prevent forgetting the old knowledge as the model is learned on new tasks [Chaudhry et al., 2018, Kirkpatrick et al., 2017, Mallya and Lazebnik, 2018]. This differs from temporal-shift DG (i.e., a special case of our setting) which aims to train a model that can generalize to future domains.

## 3 PROBLEM FORMULATION

We first introduce the notations used throughout the paper and then formulate the problem. These notations and their descriptions are also summarized in Table 1.

Notations. Let X and Y denote the input and output space, respectively. We use capitalized letters X, Y to denote random variables that take values in X, Y and small letters x, y their realizations. A domain D is specified by distribution $P _ { D } ^ { X , Y } : \mathcal { X } \times \mathcal { Y }  [ 0 , 1 ]$ and labeling function ${ \mathbb { h } } _ { D } : \mathcal { X } \to \mathcal { y } ^ { \Delta }$ , where $\Delta$ is a probability simplex over Y. For simplicity, we also use $P _ { D } ^ { V }$ (or $P _ { D } ^ { V | \bar { U } } )$ to denote the induced marginal (or conditional) distributions of random variable V (given U) in the domain D.

![](images/436f8d37aa91b0a9fb221a4d34202804279496545f61fb1bfc44363ec0788e72.jpg)

![](images/450bbcad00d2edc31745228d9504f4c6a359416c48608b7b0eb1a907f3a69136.jpg)  
Figure 1: An illustrative comparison between conventional DG and DG in non-stationary environment: domains in conventional DG are independently sampled from a stationary environment, whereas DG in non-stationary environment considers domains that evolve along a specific direction. As shown in the right plot, data (i.e., images) changes over time and the model trained on past data may not have good performance on future data due to non-stationarity (i.e., temporal shift).

Non-stationary domain generalization setup. We consider a problem where a learning algorithm has access to sequence of source datasets $\{ S _ { t } \} _ { t = 1 } ^ { T }$ where $S _ { t }$ consists of n instances i.i.d sampled from source domain $D _ { t }$ . In non-stationary DG, we assume there exists a mechanism M that captures non-stationary patterns in the data. Specifically, M can generate a sequence of mapping functions $\{ \mathtt { m } _ { t } \} _ { t \in \mathbb { N } }$ in which ${ \mathrm { m } } _ { t } : { \mathcal { X } } \times { \mathcal { Y } }  { \mathcal { X } } \times { \mathcal { Y } }$ captures the transition from domain $D _ { t - 1 }$ to domain $D _ { t }$ . In other words, we can regard $\boldsymbol { P } _ { D _ { t } } ^ { X , Y }$ as the push-forward distribution induced from $P _ { D _ { t - 1 } } ^ { X , Y }$ using the mapping function $\displaystyle \mathfrak { m } _ { t - 1 } ( \mathrm { i . e . , } P _ { D _ { t } } ^ { X , Y } : = \mathfrak { m } _ { t - 1 } \sharp P _ { D _ { t - 1 } } ^ { X , Y } )$ . Note that this setup is different from conventional DG where domains are sampled independently from a meta-distribution. In non-stationary DG, domains are related to each other via mechanism M $( \mathrm { i } . \mathrm { e } . , \mathrm { m } _ { i }$ <sub>t</sub> depends on previous mappings $\mathbf { m } _ { 1 } , \mathbf { m } _ { 2 } , \cdot \cdot \cdot , \mathbf { m } _ { t - 1 } )$

Given a sequence of T source domains, our goal is to learn a sequence of models $H = \left\{ h _ { t } \right\} _ { t = T + 1 } ^ { T + K }$ , where $h _ { t } : \mathcal { X } \to \mathcal { Y } ^ { \Delta }$ in a hypothesis class H is a model corresponds to domain $D _ { t }$ , such that these models can perform well on K (unseen) target domains $\{ D _ { t } \} _ { t = T + 1 } ^ { T + K }$ . We aim to investigate under what conditions and by what algorithms we can ensure models learned from source domains can attain high accuracy at unknown target domains $\{ D _ { t } \} _ { t = T + 1 } ^ { T + K }$ in non-stationary environment. Formally, we measure the accuracy using an error metric defined below.

Error metric. Consider a model $h : \mathcal { X } \to \mathcal { Y } ^ { \Delta }$ in a hypothesis class H, we denote $h ( x ) _ { y }$ as the element on y-th dimension which predicts $\operatorname* { P r } ( Y { \overset { } { = } } y | X = x )$ . Then the expected error of h under domain D for some loss function $L : \mathcal { y } ^ { \Delta } \times \mathcal { y }  \mathbb { R } _ { + } ( \mathrm { e . g . , 0 . 1 } $ , cross-entropy loss) can be defined as $\epsilon _ { D } \left( h \right) = \mathbb { E } _ { x , y \sim D } \left[ L \left( h ( X ) , Y \right) \right]$ . Similarly, the empirical error of h over n samples S drawn i.i.d.

from $P _ { D } ^ { X , Y }$ is defined as $\begin{array} { r } { \epsilon _ { S } \left( h \right) = \frac { 1 } { n } \sum _ { x , y \in S } L \left( h ( x ) , y \right) } \end{array}$ We also denote a family of functions $\mathcal { L } _ { \mathcal { H } }$ associated with loss function L and hypothesis class H as $\mathcal { L } _ { \mathcal { H } } =$ $\{ ( x , y )  L ( h ( x ) , y ) : h \in \mathcal { H } \}$

Non-stationary mechanism M is a key component in nonstationary DG. Since M is unknown, we need to learn it from source domains. Let M be a learned mechanism in a hypothesis class M. To support theoretical analysis about M, we define the following:

• M-generated domain sequence $\{ D _ { 1 } ^ { M } , \cdot \cdot \cdot , D _ { T + K } ^ { M } \}$ where domain $D _ { t } ^ { M }$ is associated with the distribution $P _ { D _ { t } ^ { M } } ^ { X , Y } = m _ { t - 1 } \sharp P _ { D _ { t - 1 } } ^ { X , Y }$ <sup>,Y</sup> and $D _ { 1 } ^ { M } = D _ { 1 }$

• M-generated dataset sequence $\left\{ S _ { 1 } ^ { M } , \cdots , S _ { T + K } ^ { M } \right\}$ where dataset $S _ { t } ^ { M }$ is generated from dataset $S _ { t - 1 }$ by using mapping $m _ { t - 1 }$

• M-optimal model sequence $H ^ { M } = \left\{ h _ { 1 } ^ { M } , \cdot \cdot \cdot , h _ { T + K } ^ { M } \right\}$ where $h _ { t } ^ { M } = \arg \operatorname* { m i n } _ { h \in \mathcal { H } } \epsilon _ { D _ { \star } ^ { M } } \left( h \right)$

• M-empirical optimal model sequence $\begin{array} { r l } { \widehat { H } ^ { M } } & { { } = } \end{array}$ $\left\{ \widehat { h } _ { 1 } ^ { M } , \cdots , \widehat { h } _ { T + K } ^ { M } \right\}$ where $\widehat { h } _ { t } ^ { M } = \arg \operatorname* { m i n } _ { h \in \mathcal { H } } \epsilon _ { S _ { t } ^ { M } } \left( h \right)$

We also denote errors of model sequence H on source and target domains as $\begin{array} { r } { E _ { s r c } \left( H \right) = \frac { \bar { 1 } } { T } \sum _ { t = 1 } ^ { T } \epsilon _ { D _ { t } } \left( h _ { t } \right) } \end{array}$ and $\begin{array} { r } { E _ { t g t } \left( H \right) \ = \ \frac { 1 } { K } \sum _ { t = T + 1 } ^ { T + K } \epsilon _ { D _ { t } } \left( h _ { t } \right) } \end{array}$ , respectively, and on M-generated source and target domains as $E _ { s r c } ^ { M } \left( H \right) =$ $\begin{array} { r } { \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \epsilon _ { D _ { t } ^ { M } } \left( h _ { t } \right) } \end{array}$ and $\begin{array} { r } { E _ { t g t } ^ { M } \left( H \right) = \frac { 1 } { K } \sum _ { t = T + 1 } ^ { T + K } \epsilon _ { D _ { t } ^ { M } } \left( h _ { t } \right) } \end{array}$ Empirical errors of H on source and target datasets $( \widehat { E } _ { s r c }$ and $\widehat { E } _ { t g t } )$ , and on M-generated source and target datasets $( \widehat { E } _ { s r c } ^ { M }$ and $\widehat { E } _ { t g t } ^ { M } )$ are defined similarly (Table 1).

## 4 THEORETICAL RESULTS

In this section, we aim to understand how a model sequence H learned from source domain data would perform when deployed in target domains under non-stationary distribution shifts. Specifically, we will develop theoretical upper bounds of the model sequence’s errors at target domains. These theoretical findings will provide guidance for the algorithm design in Section 5. All proofs are in Appendix A.

Table 1: Notations used in this paper.

<table><tr><td>Notation</td><td>Description</td></tr><tr><td> $\mathcal{X},\mathcal{Y},\mathcal{Z}$ </td><td>input, output, representation spaces</td></tr><tr><td> $\mathcal{M},\mathcal{H}$ </td><td>mechanism and model hypothesis classes</td></tr><tr><td> $X,Y,Z$  (resp.  $x,y,z$ )</td><td>random variables (resp. realizations) in  $\mathcal{X},\mathcal{Y},\mathcal{Z}$ </td></tr><tr><td> $D_{t}$ </td><td> $t^{th}$  domain in domain sequence</td></tr><tr><td> $S_{t}$ </td><td> $t^{th}$  dataset sampled from domain  $D_{t}$ </td></tr><tr><td> $\{D_{t}\}_{t=1}^{T}$ </td><td>source domains</td></tr><tr><td> $\{D_{t}\}_{t=T+1}^{T+K}$ </td><td>target domains</td></tr><tr><td> $P_{D_{t}}^{X,Y}$ </td><td>distribution associated with domain  $D_{t}$ </td></tr><tr><td> $\mathbb{h}_{D_{t}}:\mathcal{X}\to\mathcal{Y}^{\Delta}$ </td><td>labeling function of domain  $D_{t}$ </td></tr><tr><td> $\mathbb{M}$ </td><td>ground-truth mechanism that generates  $\{\mathbb{m}_{t}\}_{t\in\mathbb{N}}$ </td></tr><tr><td> $\mathbb{m}_{t}$ </td><td>ground-truth mapping from  $D_{t}$  to  $D_{t+1}$ :  $P_{D_{t+1}}^{X,Y}= \mathbb{m}_{t}\sharp P_{D_{t}}^{X,Y}$ </td></tr><tr><td> $M\in\mathcal{M}$ </td><td>hypothesis mechanism that generates  $\{m_{t}\}_{t\in\mathbb{N}}$ </td></tr><tr><td> $h_{t}\in\mathcal{H}$ </td><td>hypothesis classifier for domain  $D_{t}$ </td></tr><tr><td> $L:\mathcal{Y}^{\Delta}\to\mathcal{Y}$ </td><td>loss function</td></tr><tr><td> $\mathcal{L}_{\mathcal{H}}$ </td><td>family of functions  $\{(x,y)\to L(h(x),y):h\in\mathcal{H}\}$ </td></tr><tr><td> $\epsilon_{D}(h)$ </td><td>expected error of classifier  $h$  on domain  $D$ </td></tr><tr><td> $\epsilon_{S}(h)$ </td><td>empirical error of classifier  $h$  on dataset  $S$ </td></tr><tr><td> $D_{t}^{M}$ </td><td>domain associated with distribution  $P_{D_{t}^{M}}^{X,Y}=m_{t-1}\sharp P_{D_{t-1}}^{X,Y}$ </td></tr><tr><td> $S_{t}^{M}$ </td><td>dataset associated with domain  $D_{t}^{M}$ </td></tr><tr><td> $h_{t}^{M}$ </td><td> $\arg\min_{h\in\mathcal{H}}\epsilon_{D_{t}^{M}}(h)$ </td></tr><tr><td> $\widehat{h}_{t}^{M}$ </td><td> $\arg\min_{h\in\mathcal{H}}\epsilon_{S_{t}^{M}}(h)$ </td></tr><tr><td> $\mathcal{D}_{JS}$ </td><td>JS-divergence</td></tr><tr><td> $E_{src}(H)$  (resp.  $E_{tgt}(H)$ )</td><td> $\frac{1}{T}\sum_{t=1}^{T}\epsilon_{D_{t}}(h_{t})$  (resp.  $\frac{1}{K}\sum_{t=T+1}^{T+K}\epsilon_{D_{t}}(h_{t})$ )</td></tr><tr><td> $E_{src}^{M}(H)$  (resp.  $E_{tgt}^{M}(H)$ )</td><td> $\frac{1}{T}\sum_{t=1}^{T}\epsilon_{D_{t}^{M}}(h_{t})$  (resp.  $\frac{1}{K}\sum_{t=T+1}^{T+K}\epsilon_{D_{t}^{M}}(h_{t})$ )</td></tr><tr><td> $\widehat{E}_{src}(H)$  (resp.  $\widehat{E}_{tgt}(H)$ )</td><td> $\frac{1}{T}\sum_{t=1}^{T}\epsilon_{S_{t}}(h_{t})$  (resp.  $\frac{1}{K}\sum_{t=T+1}^{T+K}\epsilon_{S_{t}}(h_{t})$ )</td></tr><tr><td> $\widehat{E}_{src}^{M}(H)$  (resp.  $\widehat{E}_{tgt}^{M}(H)$ )</td><td> $\frac{1}{T}\sum_{t=1}^{T}\epsilon_{S_{t}^{M}}(h_{t})$  (resp.  $\frac{1}{K}\sum_{t=T+1}^{T+K}\epsilon_{S_{t}^{M}}(h_{t})$ )</td></tr><tr><td> $D_{src}(M)$ </td><td> $\frac{1}{T}\sum_{t=1}^{T}\left(\mathcal{D}_{JS}\left(P_{D_{t}}^{X,Y}\parallel P_{D_{t}^{M}}^{X,Y}\right)\right)^{1/2}$ </td></tr><tr><td> $D_{tgt}(M)$ </td><td> $\frac{1}{K}\sum_{t=T+1}^{T+K}\left(\mathcal{D}_{JS}\left(P_{D_{t}}^{X,Y}\parallel P_{D_{t}^{M}}^{X,Y}\right)\right)^{1/2}$ </td></tr><tr><td> $\Phi(\mathcal{M},\mathcal{H})$ </td><td> $\sup_{M^{\prime}\in\mathcal{M}}\left(E_{tgt}\left(H^{M^{\prime}}\right)-E_{src}\left(H^{M^{\prime}}\right)\right)$ </td></tr><tr><td> $\Phi(\mathcal{M})$ </td><td> $\sup_{M^{\prime}\in\mathcal{M}}\left(D_{tgt}\left(M^{\prime}\right)-D_{src}\left(M^{\prime}\right)\right)$ </td></tr></table>

To start, we adopt two assumptions commonly used in DA/DG literature [Nguyen et al., 2021b, Kumar et al., 2020].

Assumption 1 (Bounded loss). We assume loss function L is upper bounded by a constant $C , \mathrm { i . e . , } \forall x \in \mathcal { X } , y \in \mathcal { Y }$ $h \in \mathcal H$ , we have $L ( h ( x ) , y ) \leq C$

Assumption 2 (Bounded model complexity). We assume Rademacher complexity [Bartlett and Mendelson, 2002] of function class $\mathcal { L } _ { \mathcal { H } }$ computed from all samples with size n is bounded for any distribution P considered in this paper. That is, for some constant $B > 0$ , we have:

$$
\mathcal {R} _ {n} \left(\mathcal {L} _ {\mathcal {H}}\right) = \mathbb {E} \left[ \sup _ {f \in \mathcal {L} _ {\mathcal {H}}} \frac {1}{n} \sum_ {i = 1} ^ {n} \sigma_ {i} f \left(x _ {i}\right) \right] \leq \frac {B}{\sqrt {n}}
$$

where the expectation is with respect to $x _ { i } \sim P$ and $\sigma _ { i } \sim$ $P _ { \mathcal R }$ , and $P _ { \mathcal R }$ is Rademacher distribution.

We note that these two assumptions are actually reasonable and not strong. For instance, although Assumption 1 does not hold for cross-entropy loss used in classification, we can modify this loss to make it satisfied Assumption 1. In particular, it can be bounded by C by modifying softmax output from $\left( p _ { 1 } , \cdots , p _ { | { \mathcal { V } } | } \right)$ to $\left( \hat { p } _ { 1 } , \cdots , \hat { p } _ { | \mathcal { V } | } \right)$ where $\hat { p } _ { i } =$ $p _ { i } \left( 1 - \exp \left( - C \right) | \mathcal { V } | \right) \stackrel { } { + } \exp \left( - C \right)$ . In addition, according to Liang [2016] (Theorem 11 page 82), Assumption 2 holds when input space is compact and bounded in unit $L _ { 2 }$ ball and function f in $\mathcal { L } _ { \mathcal { H } }$ is linear and Lipschitz continuous in $l _ { 2 }$ norm.

To learn a model sequence H that performs well on unseen target domains, we need to account for the non-stationary patterns across domains. However, these patterns are governed by mechanism M which is unknown and must be estimated from source domains. Therefore, we need to learn a mechanism $M \in \mathcal { M }$ that can well estimate ground-truth M and learn H by leveraging M. Because the target data is inaccessible, we expect that the model performance on the target highly depends on the accuracy of $M \in \mathcal { M }$ . To formally characterize the complexity of learning non-stationary pattern leveraging hypothesis classes $\mathcal { M } ,$ , H and source domains, we introduce two complexity terms as follows.

Definition 1 (Non-stationary complexity). Given a sequence of domains $\{ D _ { t } \} _ { t = 1 } ^ { T + K }$ , hypothesis classes M and H, the M, H-complexity term Φ $( { \mathcal { M } } , { \mathcal { H } } )$ and M-complexity term Φ (M) are defined as

$$
\begin{array}{c} \Phi (\mathcal {M}, \mathcal {H}) = \sup _ {M ^ {\prime} \in \mathcal {M}} \left(E _ {t g t} (H ^ {M ^ {\prime}}) - E _ {s r c} (H ^ {M ^ {\prime}})\right) \\ \Phi (\mathcal {M}) = \sup _ {M ^ {\prime} \in \mathcal {M}} (D _ {t g t} (M ^ {\prime}) - D _ {s r c} (M ^ {\prime})) \end{array}
$$

where $\begin{array} { r } { D _ { t g t } \left( M ^ { \prime } \right) = \frac { 1 } { K } \sum _ { t = T = 1 } ^ { T + K } { \left( \mathcal { D } _ { J S } \left( P _ { D _ { t } } ^ { X , Y } \parallel P _ { D _ { t } ^ { M ^ { \prime } } } ^ { X , Y } \right) \right) ^ { 1 / 2 } } } \end{array}$ $\begin{array} { r } { D _ { s r c } \left( M ^ { \prime } \right) \ = \ \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \left( \mathcal { D } _ { J S } \left( P _ { D _ { t } } ^ { X , Y } \parallel P _ { D _ { t } ^ { M ^ { \prime } } } ^ { X , Y } \right) \right) ^ { 1 / 2 } } \end{array}$ , and $\mathcal { D } _ { J S } \left( \cdot \parallel \cdot \right)$ is JS-divergence between two distributions.

In essence, Φ $( { \mathcal { M } } , { \mathcal { H } } )$ quantifies the gap between the source and target domains in terms of prediction errors of model sequence $H ^ { M }$ . Meanwhile, Φ (M) evaluates the disparity in performance of M regarding its ability to estimate nonstationary patterns in source and in target domain sequences. Performance is measured by the statistical distance between ground-truth and the distributions induced by M. Inspired by discrepancy measures used to quantity the differences between distributions [Mansour et al., 2009, Mohri and Muñoz Medina, 2012] $\Phi \left( \mathcal { M } , \mathcal { H } \right)$ and $\Phi \left( \mathcal { M } \right)$ explicitly take into account the hypothesis classes $\mathcal { M }$ and $\mathcal { H } ,$ , and loss function L. This ensures that the bound constructed from these terms is directly related to the learning problem at hand. Next, we present a guarantee on target domains for M-empirical optimal model sequence $\widehat { H } ^ { M }$ as follows.

Theorem 1. Given domain sequence $\{ D _ { t } \} _ { t = 1 } ^ { T + K }$ , dataset sequence $\{ S _ { t } \} _ { t = 1 } ^ { T + K }$ sampled from $\{ D _ { t } \} _ { t = 1 } ^ { \bar { T } + \bar { K } }$ , for any $M \in$ M (M can depend on $\{ S _ { t } \} _ { t = 1 } ^ { \check { T } + K } )$ and any $0 < \delta < 1$ , with probability at least $1 - \delta$ over the choice of dataset sequence

$\{ S _ { t } \} _ { t = 1 } ^ { T + K }$ , we have:

$$
\begin{array}{r l} & E _ {t g t} \left(\widehat {H} ^ {M}\right) \leq \widehat {E} _ {s r c} ^ {M} \left(\widehat {H} ^ {M}\right) + 5 \sqrt {2} C \times D _ {s r c} (M) \\ & \qquad + \Phi (\mathcal {M}) + 2 \sqrt {2} C \times \Phi (\mathcal {M}, \mathcal {H}) \\ & \qquad + \frac {6 B}{\sqrt {n}} + 3 \sqrt {\frac {\log ((T + K) / \delta)}{2 n}} \end{array}
$$

It states that the expected error of $\widehat { H } ^ { M }$ on target domains $E _ { t g t } \left( \widehat { H } ^ { M } \right)$ is upper bounded by four parts: (i) empirical error of $\widehat { H } ^ { M }$ on M-generated source datasets $\widehat { E } _ { s r c } ^ { M } \left( \widehat { H } ^ { M } \right)$ (ii) the average distance between source datasets and $\acute { M } \cdot$ generating source datasets $D _ { s r c } ( M )$ , (iii) non-stationary complexity terms $\Phi ( \mathcal { M } )$ and $\Phi ( \mathcal { M } , \mathcal { H } )$ , (iv) sample complexity term $\begin{array} { r } { \frac { 6 B } { \sqrt { n } } + 3 \sqrt { \frac { \log ( ( T + K ) / \delta ) } { 2 n } } } \end{array}$ . We note that both the third and fourth parts remain fixed given hypothesis classes $\mathcal { M }$ and ${ \mathcal { H } } ,$ and the sample size n for each dataset in the sequence. It is also noteworthy that this bound still holds when M depends on dataset sequence $\{ S _ { t } \} _ { t = 1 } ^ { T + K }$ thereby allowing us to apply this bound for M learned from $\{ S _ { t } \} _ { t = 1 } ^ { T + K }$ . In addition, $\begin{array} { r } { \widehat { E } _ { s r c } ^ { M } \left( \widehat { H } ^ { M } \right) = \operatorname* { m i n } _ { H } \widehat { E } _ { s r c } ^ { M } \left( H \right) } \end{array}$ by definition. Therefore, to minimize the expected error of ${ \widehat { H } } ^ { M }$ on target domains, Theorem 1 suggests us to find a mechanism $M ^ { * } = \arg$ min $_ { M \in \mathcal { M } } D _ { s r c } ( M )$ from source datasets $\{ S _ { t } \} _ { t = 1 } ^ { T + K }$ , and then learn model sequence $\widehat { H } ^ { M ^ { * } }$ that minimizes empirical error on $M ^ { * }$ -generated dataset sequence.

Learning $M ^ { * }$ requires the model to find the optimal mapping $m _ { t - 1 } ^ { * } : \mathcal { X } \times \mathcal { Y }  \mathcal { X } \times \mathcal { Y }$ that minimizes the distance of the joint distributions $\mathcal { D } _ { J S } \left( P _ { D _ { t } } ^ { X , Y } \parallel P _ { D _ { t } ^ { M ^ { * } } } ^ { X , Y } \right)$ for all $t \in \{ 1 , \cdots , T \}$ . To this end, we first minimize the distance of output distribution between the two domains $D _ { t } , D _ { t - 1 }$ then find an optimal mapping function in input space $\mathcal { X }$ That is, minimizing the distance of joint distributions in output and input space separately. This approach is formally stated in Proposition 1 below.

Proposition 1. Let $P _ { D _ { t - 1 } ^ { W } } ^ { X , Y }$ be the distribution inducedfrom $P _ { D _ { t - \cdot } } ^ { X , Y }$ by importance weighting with factors $\{ w _ { y } \} _ { y \in \mathcal { Y } }$ where $w _ { y } ~ = ~ P _ { D _ { t } } ^ { Y = y } / P _ { D _ { t - 1 } } ^ { Y = y } ~ ( i . e . , ~ P _ { D _ { t - 1 } ^ { W } } ^ { X = x , Y = y } ~ = ~ w _ { y } ~ \times ~$ $P _ { D _ { t - 1 } } ^ { X = x , Y = y } ) .$ . Then for any mechanism M that generates $\{ m _ { t } : \mathcal { X }  \mathcal { X } \} _ { t \in \mathbb { N } } ,$ we have the following:

$$
\mathcal {D} _ {J S} \left(P _ {D _ {t}} ^ {X, Y} \parallel P _ {D _ {t} ^ {W, M}} ^ {X, Y}\right) = \mathbb {E} _ {y \sim P _ {D _ {t}} ^ {Y}} \left[ \mathcal {D} _ {J S} \left(P _ {D _ {t}} ^ {X | Y} \parallel P _ {D _ {t} ^ {W, M}} ^ {X | Y}\right) \right]
$$

where $P _ { D _ { t } ^ { W , M } } ^ { X , Y } = m _ { t - 1 } \sharp P _ { D _ { t - 1 } ^ { W } } ^ { X , Y }$ is a push-forward distribution inducedfrom $P _ { D _ { t - 1 } ^ { W } } ^ { X , Y }$ using $m _ { t - 1 }$

Proposition 1 suggests 2-step approach to learn $m _ { t } : \mathcal { X } \times$ $y  x \times y \colon ( \mathrm { i } )$ reweight $\dot { P } _ { D _ { t - 1 } } ^ { \dot { X } , Y }$ with factors $\{ w _ { y } \} _ { y \in \mathcal { Y } }$ (i.e., to minimize the distance of output distribution between

![](images/8721a230f75762f4b22437305ce501b7d4ae266a2fc73428d49a08cf41e5b569.jpg)  
Figure 2: Visualization of learning non-stationary mapping between two domains $D _ { t } ^ { W }$ (i.e., generated from $D _ { t + 1 }$ by importance weighting) and $D _ { t + 1 } . \left( \mathbf { a } \right)$ Learning in input space X. (b) Learning in representation space $\mathcal { Z }$

$D _ { t } , D _ { t - 1 } ) ; \mathrm { ( i i ) }$ learn $m _ { t } : \mathcal { X }  \mathcal { X }$ that minimizes the distance of conditional distribution $\mathcal { D } _ { J S } \left( P _ { D _ { t } } ^ { X | Y } \parallel P _ { D _ { t } ^ { W , M } } ^ { X | Y } \right)$

We note that while the non-stationary complexity terms $\Phi ( \mathcal { M } )$ and $\Phi ( \mathcal { M } , \mathcal { H } )$ are fixed given hypothesis classes M and H, a good design of M and H will make these terms small. Since the input space X may be of high dimension, constructing these hypothesis classes in high-dimensional space can be challenging in practice. To tackle this issue, we leverage the representation learning approach to first map inputs to a representation space ${ \mathcal { Z } } .$ , which often has a lower dimension than X. In particular, instead of using $m _ { t } ^ { * } : \mathcal { X }  \mathcal { X }$ to map $P _ { D _ { t } ^ { W } } ^ { X }$ to $\lceil P _ { D _ { t + 1 } ^ { W , M ^ { * } } } ^ { X }$ in input space $x ,$ we use $f _ { t } ^ { * } : \mathcal { X }  \mathcal { Z }$ and $g _ { t } ^ { * } : \mathcal { X }  \mathcal { Z }$ to map $P _ { D _ { t } ^ { W } } ^ { X }$ and $P _ { D _ { t + 1 } } ^ { X }$ to $f _ { t } ^ { * } \sharp P _ { D _ { t } ^ { W } } ^ { Z }$ and $g _ { t } ^ { * } \sharp P _ { D _ { t + \cdot } } ^ { Z }$ in representation space $\mathcal { Z }$ such that $\mathbb { E } \left[ \mathcal { \bar { D } } _ { J S } \left( g _ { t } ^ { * } \sharp P _ { D _ { t + 1 } } ^ { Z | Y } \ \lVert \ f _ { t } ^ { * } \sharp P _ { D _ { t } ^ { W } } ^ { Z | Y } \right) \right]$ is minimal. Then, we learn a sequence of classifiers $\grave { H ^ { * } }$ from representation to output spaces that minimizes empirical errors on source domains. This representation learning-based method is visualized in Figure 2 and is summarized below.

Remark 1 (Representation learning). Given the sequence of T source domains, we estimate:

(i) Non-stationary mechanism $F ^ { * }$ and $G ^ { * }$ that generate two sequence of representation mappings $\{ f _ { t } ^ { * } : \mathcal { X } \to \mathcal { Z } \}$ and $\{ g _ { t } ^ { * } : \mathcal { X }  \mathcal { Z } \}$ with $F ^ { * } , G ^ { * }$ defined as:

$$
\underset {F \in \mathcal {F}, G \in \mathcal {G}} {\arg \min}   \frac {1}{T} \sum_ {t = 1} ^ {T} \underset {y \sim P _ {D _ {t}} ^ {Y}} {\mathbb {E}} \left[ \mathcal {D} _ {J S} \left(g _ {t - 1} \sharp P _ {D _ {t}} ^ {Z | Y} \parallel f _ {t - 1} \sharp P _ {D _ {t - 1} ^ {W}} ^ {Z | Y}\right) \right]
$$

where F and G generate sequence of representation mappings $\{ f _ { t } : \mathcal { X } \to \mathcal { Z } \}$ and $\{ g _ { t } : \mathcal { X } \to \mathcal { Z } \} , \mathcal { F }$ and G are the hypothesis classes of F and G.

(ii) Sequence of classifiers $H ^ { * } = \{ h _ { t } ^ { * } : \mathcal { Z }  \mathcal { V } ^ { \Delta } \}$ where each $h _ { t } ^ { * }$ minimizes the empirical errors with respect to distributions $f _ { t } ^ { * } \sharp P _ { D _ { t } ^ { W } } ^ { Z , Y }$ and $g _ { t } ^ { * } \sharp P _ { D _ { t + 1 } } ^ { Z , Y }$

Remark 2 (Comparison with conventional DG). A key property of non-stationary DG is that the model needs to evolve over the domain sequence to capture non-stationary patterns (i.e., learn invariant representations between two consecutive domains but adaptive across domain sequence). This differs from the conventional DG [Ganin et al., 2016, Phung et al., 2021] which (implicitly) assumes that target domains lie on or are near the mixture of source domains, then enforcing fixed invariant representations across all source domains can help generalize the model to target. We argue that this assumption does not hold in non-stationary DG where the target domains may be far from the mixture of source domains. Thus, the existing methods developed for conventional DG often fail in non-stationary DG. We further validate this empirically in Appendix C.2.

According to Remark 1, JS-divergence between two distribution $P _ { D _ { t } ^ { W } }$ and $P _ { D _ { t + 1 } }$ can be minimized through invariant representation learning. However in practice, models only have access to finite datasets $S _ { t } ^ { W }$ and $S _ { t + 1 }$ . Moreover, Goodfellow et al. [2014] has shown that minimizing JS-divergence is aligned with the objective adversarial learning in the setting of infinite data. Therefore, evaluating the performance of minimizing JS-divergence via adversarial learning in the case of finite data is important. First, definition of adversarial learning is given below.

Definition 2. Adversarial learning for invariant representation. Given two datasets $\begin{array} { l c l } { { \overline { { { S _ { t } ^ { w } } } } } } & { { = } } & { { \left\{ x _ { t } ^ { i } \right\} _ { i = 1 } ^ { n } } } \end{array}$ and $\begin{array} { r l r } { S _ { t + 1 } } & { { } = } & { \left\{ x _ { t + 1 } ^ { i } \right\} _ { i = 1 } ^ { n } , } \end{array}$ the goal of adversarial learning approach for invariant representation with respect to these two datasets is to achieve $\begin{array} { r l r } { \widehat { L } _ { a d v } ^ { t } } & { { } = } & { \operatorname* { i n f } _ { \alpha _ { t } , \beta _ { t } } \operatorname* { s u p } _ { \gamma _ { t } } \left( \frac { 1 } { n } \sum _ { i = 1 } ^ { n } \log \left( D _ { \gamma _ { t } } ( F _ { \alpha _ { t } } ( x _ { t } ^ { i } ) ) \right) \right. } \end{array}$ $+ \textstyle \frac { 1 } { n } \sum _ { i = 1 } ^ { n } \log \big ( 1 - D _ { \gamma _ { t } } ( G _ { \beta _ { t } } ( x _ { t + 1 } ^ { i } ) ) \big ) \big )$ where $F _ { \alpha _ { t } } : \mathcal { X }  \mathcal { Z }$ and $G _ { \beta _ { t } } : \mathcal { X } \stackrel { } {  } \mathcal { Z }$ are the representation networks parameterized by $\alpha _ { t } \in \mathcal { A }$ and $\beta _ { t } \in B$ , and $D _ { \gamma _ { t } } : \mathcal { Z } \to [ 0 , 1 ]$ are the discriminator parameterized by $\gamma _ { t } \in \Gamma$ that tries to predict which domain the representation comes from.

Then, Proposition 2 shows that the error of minimizing JSdivergences using adversarial learning on the sequence of source datasets size n is up to $\begin{array} { r l r } { \mathrm { ~ } } & { { } } & { { \mathcal { O } } \left( \frac { 1 } { \sqrt { n } } \right) } \end{array}$

Proposition 2. Let $\alpha _ { t } ^ { * } , \beta _ { t } ^ { * } , \gamma _ { t } ^ { * }$ are parameters learned by infinite data and $\widehat { \alpha } _ { t } , \widehat { \beta } _ { t } , \widehat { \gamma } _ { t }$ are parameters learned by optimizing $\widehat { L } _ { a d v } ^ { t } ,$ then we have:

$$
\begin{array}{l} \mathbb {E} \left[ D _ {s r c} (\widehat {\alpha}, \widehat {\beta}) \right] \leq D _ {s r c} (\alpha^ {*}, \beta^ {*}) \\ \qquad + \mathcal {O} \left(\left(\frac {1}{\sqrt {n}}\right) \times C (\mathcal {A}, \mathcal {B}, \Gamma)\right) \end{array}
$$

where $\begin{array} { r l r } { D _ { s r c } \left( \widehat { \alpha } , \widehat { \beta } \right) } & { = } & { \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { D } _ { J S } \left( P _ { \widehat { \alpha } _ { t } } ^ { Z } \parallel P _ { \widehat { \beta } _ { t } } ^ { Z } \right) } \end{array}$ and $\begin{array} { r l r } { D _ { s r c } \left( \alpha ^ { * } , \beta ^ { * } \right) } & { { } = } & { { \frac { 1 } { T } } \sum _ { t = 1 } ^ { T } \mathcal { D } _ { J S } \left( P _ { \alpha _ { t } ^ { * } } ^ { Z } \parallel P _ { \beta _ { t } ^ { * } } ^ { Z } \right) , \ P _ { \hat { \alpha } _ { t } } ^ { Z } , \ P _ { \hat { \beta } _ { t } } ^ { Z } } \end{array}$

![](images/564945033b73aecc592fa3a661f13a171b33ecf5ea4f08cc87d4b51a61ed6e45.jpg)  
Figure 3: Overall architecture of $\tt A I R I$ and the visualization of its learning process.

$P _ { \alpha _ { t } ^ { * } } ^ { Z } , P _ { \beta _ { t } ^ { * } } ^ { Z }$ are distributions induced by representation networks parameterized by $\widehat { \alpha } _ { t } , \widehat { \beta } _ { t } , \alpha _ { t } ^ { * } , \beta _ { t } ^ { * }$ , respectively, and $C ( A , B , \Gamma )$ is a constant specified by the parameter spaces A, B, Γ.

## 5 PROPOSED ALGORITHM

Overview. Based on Remark 1, we propose AIRL, a novel model that learns adaptive invariant representations from a sequence of T source domains. AIRL includes two components: (i) representation network which are instantiation of mechanisms $F ^ { * }$ and $G ^ { * }$ that generates representation mapping sequences $[ f _ { 1 } ^ { * } , \cdots , f _ { T + K } ^ { * } ]$ and $[ g _ { 1 } ^ { * } , \cdots , g _ { T + K } ^ { * } ]$ from input space to representation space, (ii) classification network that learns the sequence of classifiers $H ^ { * } =$ $[ h _ { 1 } ^ { * } , \cdots , h _ { T + K } ^ { * } ]$ from representation to the output spaces. Figure 3 shows the overall architecture of AIRL; the technical details of each component are presented in Appendix B. The learning and inference processes of AIRL are formally stated as follows.

## 5.1 LEARNING

Non-stationary mechanisms $F ^ { * }$ and $G ^ { * }$ , and classifiers $H ^ { * }$ in AIRL can be learned by solving an optimization problem over T source domains $\{ D _ { t } \} _ { t = 1 } ^ { T } \colon$

$$
F ^ {*}, G ^ {*}, H ^ {*} = \underset {F, G, H} {\arg \min} \sum_ {t = 1} ^ {T} \mathcal {L} _ {c l s} ^ {t} + \alpha \mathcal {L} _ {i n v} ^ {t}\tag{1}
$$

where $\mathcal { L } _ { c l s } ^ { t }$ is the prediction loss on source domains $D _ { t }$ and $D _ { t + 1 } ; \mathcal { L } _ { i n v } ^ { t }$ enforces the representations are invariant across a pair of consecutive domains $D _ { t } , D _ { t + 1 } ;$ hyper-parameter α controls the trade-off between two objectives. We note that enforcing pairwise invariance as in objective (1) does not imply global invariance (i.e., representations that are invariant across all domains). It is because we use distinct mappings for different pairs of domains. In particular, $D _ { t - 1 }$ and $D _ { t }$ are aligned by two mappings $f _ { t - 1 }$ and $g _ { t - 1 }$ while $D _ { t }$ and $D _ { t + 1 }$ are aligned by two mappings $f _ { t }$ and $g _ { t }$ .

Next, we present the detailed architecture of the representation network and the classification network. In practice, the representation mappings are often complex (e.g., ResNet [He et al., 2016] for image data, Transformer [Vaswani et al., 2017] for text data), then explicitly capturing the evolving of these mappings is challenging. We surpass this bottleneck by capturing the evolving of representation space induced by these mappings instead. Formally, our representation network consists of an encoder Enc which maps from input to representation spaces, and Transformer layer Trans which learns the non-stationary pattern from a sequence of source domains using attention mechanism. Given the batch sample $\boldsymbol { B } : = \{ x _ { t } , y _ { t } \} _ { t \le T }$ from $T$ source domains where $\{ x _ { t } , y _ { t } \} = \{ x _ { t } ^ { j } , y _ { t } ^ { j } \} _ { j = 1 } ^ { n }$ are samples for domain $D _ { t }$ , the encoder first maps each input $\boldsymbol { x } _ { t } ^ { j }$ to a representation $z _ { t } ^ { j } = \mathrm { E n c } \Big ( x _ { t } ^ { j } \Big ) , \forall t \leq T , j \leq n$ . Then, Transformer layer Trans is used to generate representation $\widehat { z } _ { t } ^ { j }$ from the sequence $z _ { \le t } ^ { j } = \left\lceil z _ { 1 } ^ { j } , z _ { 2 } ^ { j } , \cdot \cdot \cdot , z _ { t } ^ { j } \right\rceil$ . Specifically, $\forall j , t ,$ Trans leverages four feed-forward networks $Q , K , V , U$ to compute $\widehat { z } _ { t } ^ { j }$ as follow:

$$
\begin{array}{r l} & {\widehat {z} _ {t} ^ {j} = \left(a _ {\leq t} ^ {j}\right) ^ {\top} V \left(z _ {\leq t} ^ {j}\right) + U \left(z _ {t} ^ {j}\right)} \\ & {\mathrm{with} a _ {\leq t} ^ {j} = \frac {K \left(z _ {\leq t} ^ {j}\right) ^ {\top} Q \left(z _ {t} ^ {j}\right)}{\sqrt {d}}} \end{array}\tag{2}
$$

It is worth pointing out that we do not assume data are aligned across domain sequence. In particular, due to randomness in data loading, there is no alignment between the $j ^ { t h }$ sample in domain $D _ { t - 1 }$ and the $j ^ { t { \bar { h } } }$ sample in domain $D _ { t }$ . In our design, the computational paths from $x _ { t + 1 } ^ { j }$ to $z _ { t + 1 } ^ { j }$ and from $\boldsymbol { x } _ { t } ^ { j }$ to $\widehat { z } _ { t } ^ { j }$ are considered as $g _ { t }$ and $f _ { t } ,$ , respectively. In particular, $z _ { t + 1 } ^ { j } = g _ { t } ( x _ { t + 1 } ^ { j } )$ and $\widehat { z } _ { t } ^ { j } = f _ { t } ( x _ { t } ^ { j } )$ . The main goal of this design is as follows: By incorporating historical data into computation, representation space constructed by $f _ { t }$ can capture evolving pattern across domain sequence. However, this design requires access to the historical data during inference which might not be feasible in practice. To avoid it, we enforce $g _ { t }$ , which obviates the need to access historical data, to mimic representation space constructed by $f _ { t }$

As shown in Remark 1, our goal is to enforce invariant representation constraint (i.e., $\mathcal { L } _ { i n v } ^ { t }$ in objective (1)) for every pair of two consecutive domains $D _ { t } , D _ { t + 1 }$ constructed by $f _ { t }$ and $g _ { t }$ instead of learning a network that achieves invariant representations for all source domains together. Thus, the representations constructed by $f _ { t }$ and $g _ { t }$ might not be aligned with the ones constructed by $f _ { t ^ { \prime } }$ and $g _ { t ^ { \prime } }$ . After mapping data to the representation spaces, the classification network are used to generate the classifier sequence H. Due to the simplicity of the classifier in practice (i.e., 1 or 2-layer network), we leverage long short-term memory [Hochreiter and Schmidhuber, 1997] LSTM to explicitly capture the evolving of the classifier over domain sequence. Specifically, the weights of previous classifiers $h _ { < t } = [ h _ { 1 } , h _ { 2 } , \cdot \cdot \cdot , h _ { t - 1 } ]$ are vectorized and put into LSTM to generate the weights of $h _ { t }$

Because $f _ { t } , g _ { t } , h _ { t } \forall t < T$ are functions of the representation network and the classification network, the weights of these two networks are updated using the backpropagated gradients for objective (1). The pseudo-code of the complete learning process for AIRL is shown in Algorithm 1. Next, we present the details of each loss term used in optimization.

Prediction loss $\mathcal { L } _ { c l s } ^ { t } \mathrm { : \Omega }$ : We adopt cross-entropy loss for classification tasks. Specifically, $\mathcal { L } _ { c l s } ^ { t }$ for the optimization over domains $D _ { t } , D _ { t + 1 }$ is defined as follows.

$$
\begin{array}{c} \mathcal {L} _ {c l s} ^ {t} = \mathbb {E} _ {D _ {t} ^ {W}} \left[ - \log \left(\frac {h _ {t} (f _ {t} (X)) _ {Y}}{\sum_ {y ^ {\prime} \in \mathcal {Y}} h _ {t} (f _ {t} (X)) _ {y ^ {\prime}}}\right) \right] \\ + \mathbb {E} _ {D _ {t + 1}} \left[ - \log \left(\frac {h _ {t} (g _ {t} (X)) _ {Y}}{\sum_ {y ^ {\prime} \in \mathcal {Y}} h _ {t} (g _ {t} (X)) _ {y ^ {\prime}}}\right) \right] \end{array}\tag{3}
$$

Invariant representation constraint $\mathcal { L } _ { i n v } ^ { t } \colon$ It aims to minimize the distance between $f _ { t } \sharp P _ { D _ { + } ^ { W } } ^ { Z | Y = y }$ and $g _ { t } \sharp P _ { D _ { t + 1 } } ^ { Z | Y = y }$ $\forall y \in \mathcal { V }$ , two conditional distributions induced from domains $D _ { t } ^ { W }$ and $D _ { t + 1 }$ using representation mappings $f _ { t } , g _ { t } ,$ respectively. In other words, for any inputs X from domains $D _ { t } ^ { \dot { W } }$ and $X ^ { \prime }$ from $D _ { t + 1 }$ whose labels are the same, we need to find representation mappings $f _ { t } , g _ { t }$ such that the representations $\bar { f _ { t } } ( X ) , g _ { t } ( X ^ { \prime } )$ have similar distributions. Inspired by correlation alignment loss [Sun and Saenko, 2016], we enforce this constraint by using the following as loss $\mathcal { L } _ { i n v } ^ { t } \colon$

$$
\mathcal {L} _ {i n v} ^ {t} = \sum_ {y \in \mathcal {Y}} \frac {1}{4 d ^ {2}} \left\| C _ {t} ^ {y} - C _ {t + 1} ^ {y} \right\| _ {F} ^ {2}\tag{4}
$$

where d is the dimension of representation space $\mathcal { Z } , \Vert \cdot \Vert _ { F } ^ { 2 }$ is the squared matrix Frobenius norm, and $C _ { t } ^ { y }$ and $C _ { t + 1 } ^ { y }$ are covariance matrices defined as follows:

$$
\begin{array}{l} C _ {t} ^ {y} = \frac {1}{n _ {y} ^ {t} - 1} \left(f _ {t} \left(\mathbf {X} _ {t} ^ {y}\right) ^ {\top} f _ {t} \left(\mathbf {X} _ {t} ^ {y}\right) \right. \\ \left. - \frac {1}{n _ {y} ^ {t}} \left(\mathbf {1} ^ {\top} f _ {t} \left(\mathbf {X} _ {t} ^ {y}\right)\right) ^ {\top} \left(\mathbf {1} ^ {\top} f _ {t} \left(\mathbf {X} _ {t} ^ {y}\right)\right)\right) \\ C _ {t + 1} ^ {y} = \frac {1}{n _ {y} ^ {t + 1} - 1} \left(g _ {t} \left(\mathbf {X} _ {t + 1} ^ {y}\right) ^ {\top} g _ {t} \left(\mathbf {X} _ {t + 1} ^ {y}\right) \right. \\ \left. - \frac {1}{n _ {y} ^ {t + 1}} \left(\mathbf {1} ^ {\top} g _ {t} \left(\mathbf {X} _ {t + 1} ^ {y}\right)\right) ^ {\top} \left(\mathbf {1} ^ {\top} g _ {t} \left(\mathbf {X} _ {t + 1} ^ {y}\right)\right)\right) \end{array}\tag{5}
$$

(6)

where 1 is the column vector with all elements equal to 1, $\mathbf { X } _ { t } ^ { y } = \{ x _ { i } : x _ { i } \in D _ { t } ^ { W } , y _ { i } = y \}$ is the matrix whose columns are $\{ x _ { i } \} , f _ { t }$ and $g _ { t }$ are column-wise operations applied to $\mathbf { X } _ { t } ^ { y }$ and $\mathbf { X } _ { t + 1 } ^ { y }$ , respectively, and $n _ { y } ^ { t }$ is cardinality of $\mathbf { X } _ { t } ^ { y }$

```txt
Algorithm 1: Learning process for AIRL

Input: Training datasets from T source domains
{Dt}Tt=1, representation network = {Enc,
Trans}, classification network = {LSTM, h1},
α, n

Output: Trained Enc, Trans, LSTM, h1*
1 Linv = 0, Lcls = 0
/* Estimate {wyt}y∈Y,t<T for important
weighting */
2 for t = 1 : T - 1 do
3    for y ∈ Y do
4    wyt = PYt+1/PYt = y/PDt
/* Learn weights for Enc, Trans, LSTM
*/
5 while learning is not end do
6    Sample batch B = {xt, yt}Tt=1 ~ {Dt}Tt=1 where
{xt, yt} = {xtj, ytj}n
j=1
7    z1 = Enc (x1)
8    for t = 1 : T - 1 do
9    zt+1 = Enc (xt+1)
10   帽子 = Trans (z≤t)
11    {帽子(w), yt(w)} = Reweight {帽子, yt} with
    wt = {wtj}y∈y
12    Calculate Ltinv from帽子(w), zt+1 by Eq. (4)
13    Linv = Linv + Ltinv
14    if t > 1 then
15    | ht = LSTM (h<t)
16    Calculate Ltcls from
    yt(w), yt+1, ht (帽子(w)), ht (zt+1) by Eq. (3)
17    Lcls = Lcls + Ltcls
18    Update Enc, Trans, LSTM,帽子h1 by optimizing
    Linv + αLcls
```

## 5.2 INFERENCE

At the inference stage, the well-trained representation network and classification network can be used to make predictions about input x from target domain sequence $\left\{ \boldsymbol { D } _ { t } \right\} _ { t = T + 1 } ^ { T + K }$ . In particular, we first map input x in domain $D _ { t }$ to representation z using the encoder Enc in the representation network $( \mathrm { i } . \mathrm { e } . , g _ { t - 1 } ^ { \ast } )$ . Then the classification network (i.e., LSTM) is used sequentially to generate $h _ { t - 1 } ^ { * }$ from the sequence of classifiers $\left[ h _ { 1 } ^ { * } , \cdots , h _ { t - 2 } ^ { * } \right]$ , and the prediction about z can be made by $\bar { h } _ { t - 1 } ^ { * }$ . Note that at the learning stage, both $g _ { t - 1 } ^ { * }$ and $f _ { t } ^ { * }$ are used to map input x from domain $D _ { t }$ to the representation space while at the inference stage, only $g _ { t - 1 } ^ { * }$ is needed for target domain $D _ { t }$ (we do not use $f _ { t } ^ { * }$ because it requires access to data from all domains $\{ D _ { t ^ { \prime } } \} _ { t ^ { \prime } \leq t }$ which generally are not available during inference). The complete inference process is shown in Algorithm 2.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2: Inference process for AIRL
Input: Testing dataset from target domain
 $D_{t}(t \in \{T + 1, \cdots, T + K\})$ , trained
Enc, LSTM,  $h_{1}^{*}$ 
Output: Predictions for testing dataset
1 [t]
2 for  $t' = 2 : (t - 1)$  do
3 |  $h_{t'}^{*} = \text{LSTM}(h_{&lt;t'}^{*})$ 
4 while inference is not end do
5 | Sample batch  $B = x_{t} \sim D_{t}$ 
6 |  $z_{t} = \text{Enc}(x_{t})$ 
7 | Generate predictions  $h_{t-1}^{*}(z_{t})$
</div>

## 6 EXPERIMENTS

In this section, we present the experimental results of the proposed AIRL and compare AIRL with a wide range of existing algorithms. We evaluate these algorithms on synthetic and real-world datasets. Next, we first introduce the experimental setup and then present the empirical results.

Experimental setup. Datasets and baselines used in the experiments are briefly introduced below. Their details are shown in Appendix C.

Datasets. We consider five datasets: Circle [Pesaranghader and Viktor, 2016] (a synthetic dataset containing 30 domains where each instance is sampled from 30 two-dimensional Gaussian distributions), Circle-Hard (a synthetic dataset adapted from Circle dataset such that domains do not uniformly evolve), RMNIST (a semi-synthetic dataset constructed from MNIST [LeCun et al., 1998] by R-degree counterclockwise rotation), Yearbook [Ginosar et al., 2015] (a real dataset consisting of frontal-facing American high school yearbook photos from 1930-2013), and CLEAR [Lin et al., 2021] (a real dataset capturing the natural temporal evolution of visual concepts that spans a decade).

Baselines. We compare the proposed AIRL with existing methods from related areas, including the followings: empirical risk minimization (ERM), last domain training (LD), fine tuning (FT), domain invariant representation learning (G2DM [Albuquerque et al., 2019], DANN [Ganin et al., 2016], CDANN [Li et al., 2018b], CORAL [Sun and Saenko, 2016], IRM [Arjovsky et al., 2019]), data augmentation (MIXUP [Zhang et al., 2018]), continual learning (EWC [Kirkpatrick et al., 2017]), continuous DA (CIDA [Wang et al., 2020]), distributionally robust optimization (GroupDRO [Sagawa et al., 2019]), gradient-based DG (Fish [Shi et al., 2022]) contrastive learning-based DG $( \mathrm { i . e . , }$ SelfReg [Kim et al., 2021]), non-stationary DG (DRAIN [Bai et al., 2022], TKNets [Zeng et al., 2024b], LSSAE [Qin et al., 2022], and DDA [Zeng et al., 2023]). To ensure a fair comparison, we adopt similar architectures for AIRL and baselines, including both representation mapping and classifier. The implementation details are in Appendix B.

Table 2: Prediction performances $( \mathrm { i . e . , O O D _ { A v g } }$ and $\mathrm { O O D } _ { \mathrm { W r t } } )$ of AIRL and baselines under Eval-D scenario $( K = 5 )$ . We report average results (w. standard deviation) over 5 random seeds. For CLEAR dataset, due to only one split between train and test sets, $\mathrm { O O D } _ { \mathrm { A v g } }$ and $\mathrm { O O D } _ { \mathrm { W r t } }$ are similar.

<table><tr><td rowspan="2">Algorithm</td><td colspan="2">Circle</td><td colspan="2">Circle-Hard</td><td colspan="2">RMNIST</td><td colspan="2">Yearbook</td><td>CLEAR</td></tr><tr><td> $OOD_{Avg}$ </td><td> $OOD_{Wrt}$ </td><td> $OOD_{Avg}$ </td><td> $OOD_{Wrt}$ </td><td> $OOD_{Avg}$ </td><td> $OOD_{Wrt}$ </td><td> $OOD_{Avg}$ </td><td> $OOD_{Wrt}$ </td><td> $OOD_{Avg}/OOD_{Wrt}$ </td></tr><tr><td>ERM</td><td>89.63 (0.89)</td><td>79.84 (1.84)</td><td>66.94 (1.69)</td><td>58.43 (0.05)</td><td>56.61 (1.83)</td><td>51.85 (4.15)</td><td>90.79 (0.16)</td><td>71.03 (1.74)</td><td>69.04 (0.18)</td></tr><tr><td>LD</td><td>76.60 (6.45)</td><td>56.88 (3.74)</td><td>58.13 (1.67)</td><td>51.58 (1.87)</td><td>37.54 (2.77)</td><td>25.80 (4.12)</td><td>77.10 (0.30)</td><td>57.97 (0.88)</td><td>57.01 (2.15)</td></tr><tr><td>FT</td><td>85.57 (1.82)</td><td>71.99 (4.11)</td><td>59.02 (5.20)</td><td>50.80 (2.79)</td><td>60.73 (0.87)</td><td>47.30 (3.77)</td><td>87.04 (0.58)</td><td>66.83 (2.22)</td><td>66.71 (0.46)</td></tr><tr><td>DANN</td><td>88.80 (1.17)</td><td>78.32 (3.23)</td><td>65.10 (0.93)</td><td>56.68 (0.59)</td><td>58.25 (1.15)</td><td>53.61 (1.61)</td><td>90.57 (0.22)</td><td>69.58 (1.38)</td><td>67.48 (1.19)</td></tr><tr><td>CDANN</td><td>89.75 (0.14)</td><td>80.75 (2.97)</td><td>64.05 (1.33)</td><td>58.68 (0.22)</td><td>58.19 (0.93)</td><td>54.45 (1.40)</td><td>90.46 (0.30)</td><td>70.37 (1.44)</td><td>66.12 (0.37)</td></tr><tr><td>G2DM</td><td>89.40 (2.27)</td><td>79.61 (2.94)</td><td>67.75 (2.69)</td><td>59.65 (1.61)</td><td>57.62 (0.39)</td><td>53.93 (0.31)</td><td>87.57 (0.37)</td><td>66.69 (1.15)</td><td>56.98 (2.77)</td></tr><tr><td>CORAL</td><td>90.13 (0.52)</td><td>83.14 (1.27)</td><td>66.12 (1.48)</td><td>59.62 (1.17)</td><td>51.41 (2.63)</td><td>44.95 (3.64)</td><td>90.41 (0.20)</td><td>69.53 (2.00)</td><td>70.96 (1.06)</td></tr><tr><td>GROUPDRO</td><td>90.50 (1.75)</td><td>81.07 (6.12)</td><td>67.08 (1.67)</td><td>58.51 (0.12)</td><td>54.37 (2.98)</td><td>46.21 (5.69)</td><td>90.65 (0.20)</td><td>71.21 (1.51)</td><td>70.63 (0.04)</td></tr><tr><td>MIXUP</td><td>88.49 (0.86)</td><td>76.78 (2.49)</td><td>63.03 (1.53)</td><td>56.21 (1.20)</td><td>52.13 (2.54)</td><td>34.60 (16.81)</td><td>89.75 (0.05)</td><td>68.73 (1.36)</td><td>69.58 (0.99)</td></tr><tr><td>IRM</td><td>85.78 (1.11)</td><td>74.80 (1.73)</td><td>62.43 (2.70)</td><td>54.96 (1.78)</td><td>26.96 (1.11)</td><td>16.25 (1.87)</td><td>84.65 (0.31)</td><td>64.30 (2.44)</td><td>49.54 (1.08)</td></tr><tr><td>SELFREG</td><td>90.33 (0.14)</td><td>82.20 (0.93)</td><td>68.23 (2.47)</td><td>60.28 (0.90)</td><td>50.58 (2.35)</td><td>42.15 (4.63)</td><td>91.47 (0.12)</td><td>73.88 (0.37)</td><td>69.18 (0.68)</td></tr><tr><td>FISH</td><td>90.65 (0.25)</td><td>79.09 (2.46)</td><td>62.69 (0.63)</td><td>56.97 (0.49)</td><td>56.53 (1.32)</td><td>52.23 (1.47)</td><td>89.92 (0.20)</td><td>70.58 (0.90)</td><td>69.46 (0.47)</td></tr><tr><td>EWC</td><td>89.18 (1.72)</td><td>79.59 (4.63)</td><td>68.31 (3.31)</td><td>61.34 (2.18)</td><td>66.53 (1.26)</td><td>50.63 (5.35)</td><td>89.47 (0.17)</td><td>59.09 (7.70)</td><td>45.58 (4.92)</td></tr><tr><td>CIDA</td><td>87.25 (0.88)</td><td>77.91 (0.23)</td><td>65.38 (2.77)</td><td>58.15 (0.88)</td><td>53.42 (4.35)</td><td>35.21 (17.85)</td><td>91.29 (0.16)</td><td>70.19 (1.45)</td><td>65.10 (0.12)</td></tr><tr><td>DRAIN</td><td>86.78 (0.65)</td><td>74.57 (1.82)</td><td>67.44 (4.65)</td><td>57.76 (3.42)</td><td>67.09 (4.06)</td><td>59.49 (8.31)</td><td>89.62 (0.39)</td><td>70.36 (2.32)</td><td>64.67 (0.65)</td></tr><tr><td>TKNets</td><td>91.76 (0.16)</td><td>83.35 (1.32)</td><td>64.19 (0.95)</td><td>59.94 (0.18)</td><td>74.39 (0.23)</td><td>71.03 (0.37)</td><td>92.11 (0.26)</td><td>75.04 (1.16)</td><td>64.05 (0.64)</td></tr><tr><td> $LSSAE^1$ </td><td>90.21 (1.95)</td><td>80.92 (3.53)</td><td>66.43 (0.81)</td><td>61.22 (0.71)</td><td>33.30 (2.14)</td><td>18.83 (3.85)</td><td>60.48 (4.99)</td><td>50.35 (4.67)</td><td>22.61 (0.25)</td></tr><tr><td>DDA</td><td>72.06 (4.51)</td><td>48.81 (0.97)</td><td>65.26 (3.20)</td><td>56.16 (2.45)</td><td>78.18 (0.88)</td><td>73.70 (0.31)</td><td>86.72 (0.56)</td><td>67.60 (2.66)</td><td>70.12 (1.10)</td></tr><tr><td>AIRL</td><td>92.28 (0.27)</td><td>82.81 (2.70)</td><td>73.50 (2.21)</td><td>63.29 (1.26)</td><td>77.49 (0.86)</td><td>74.99 (0.57)</td><td>93.10 (0.21)</td><td>78.22 (0.92)</td><td>73.04 (0.67)</td></tr></table>

Table 3: Ablation study for AIRL on Circle-Hard dataset under Eval-D scenario $( K = 5 )$

<table><tr><td>LSTM</td><td>Trans</td><td> $\mathcal{L}_{inv}$ </td><td> $OOD_{Avg}$ </td><td> $OOD_{Wrt}$ </td></tr><tr><td>✗</td><td>√</td><td>√</td><td>69.06</td><td>61.05</td></tr><tr><td>√</td><td>✗</td><td>√</td><td>65.51</td><td>58.69</td></tr><tr><td>√</td><td>✗</td><td>✗</td><td>68.33</td><td>60.16</td></tr><tr><td>√</td><td>√</td><td>√</td><td>73.50</td><td>63.29</td></tr></table>

Evaluation method. In the experiments, models are trained on a sequence of source domains $\mathcal { D } _ { s r c } ,$ and their performance is evaluated on target domains $\mathcal { D } _ { t g t }$ under two different scenarios: Eval-S and Eval-D. In the scenario Eval-S, models are trained one time on the first half of domain sequence $\mathcal { D } _ { s r c } = [ D _ { 1 } , D _ { 2 } , \cdot \cdot \cdot , D _ { T } ]$ and are then deployed to make predictions on the second half of domain sequence $\mathscr { D } _ { t g t } = [ D _ { T + 1 } , D _ { T + 2 } , \cdots , D _ { 2 T } ] ( K = T )$ . In the scenario Eval-D, source and target domains are not static but are updated periodically as new data/domain becomes available. For each of these two scenarios, we use two accuracy measures, $\mathrm { O O D } _ { \mathrm { A v g } }$ and $\mathrm { O O D } _ { \mathrm { W r t } }$ , to evaluate the averageand worst-case performances. Their details are shown in Appendix C. We train each model with 5 different random seeds and report the average prediction performances.

Results. Next, we evaluate the model performance under Eval-D scenario (Results for Eval-S are in Appendix C).

Non-stationary DG results. Performance of AIRL and baselines on synthetic (i.e., Circle, Circle-Hard) and real-world (i.e., RMNIST, Yearbook) data are presented in Table 2. We observe that AIRL consistently outperforms other methods over all datasets and metrics. These results indicate that AIRL can effectively capture non-stationary patterns across domains, and such patterns can be leveraged to learn the models that generalize better on target domains compared to the baselines. Among baselines, methods designed specifically for non-stationary DG (i.e., DRAIN, DPNET, LSSAE) and continual learning method (i.e., EWC) achieve better performance than other methods. However, such improvement is inconsistent across datasets.

Comparison with non-stationary DG methods. DPNET assumes that the evolving pattern between two consecutive domains is constant and the distances between them are small. Thus, this method does not achieve good performance for Circle-Hard dataset where distance between two consecutive domains is proportional to domain index. DRAIN utilizes Bayesian framework and generates the whole models at every domain. This method, however, is only capable for small neural networks and does not scale well to realworld applications. Moreover, DPNET, DRAIN, and DDA can only generalize to a single subsequent target domain. LSSAE leverages sequential variational auto-encoder [Li and Mandt, 2018] to learn non-stationary pattern. However, this model assumes the availability of aligned data across domain sequence, which may pose challenges to its performance in non-stationary DG. In contrast, AIRL is not limited to the constantly evolving pattern. It is also scalable to large neural networks and can handle multiple target domains. In particular, compared to the base model (ERM), our method has only one extra Transformer and LSTM layers. Note that these layers are used during training only. In the inference stage, predictions are made by Enc and classifier pre-generated by LSTM which then results in a similar inference time with ERM.

![](images/892444fb4a47f7fdae09d38742abeeab8aafc377b81c5d8a70d577f3740ed815.jpg)  
Figure 4: Visualization of predictions on Circle-Hard dataset generated by ERM and AIRL.

Decision boundary visualization. We conduct a quantitative analysis for our method by visualizing its predictions on Circle-Hard dataset. We train models (i.e., AIRL and ERM) on the first 10 domains (right half) and evaluate on the remaining 10 domains (left half). As depicted in Figure 4, our method, designed to capture non-stationary patterns across domains, generates more accurate predictions for target domains compared to ERM.

Ablation studies. We conduct experiments to investigate the roles of each component in AIRL. In particular, we compare AIRL with its variants; each variant is constructed by removing LSTM (i.e., use fixed classifier instead), Trans (i.e., use fixed representation instead), $L _ { i n v }$ (i.e., without invariant constraint) from the model. As shown in Table 3, model performance deteriorates when removing any of them. These results validate our theorems and demonstrate the effectiveness of each component.

Limitations. While AIRL consistently outperforms existing methods across all datasets and metrics, we acknowledge certain limitations in our work. Regarding theoretical analysis, we presently lack an effective method to estimate non-stationary complexity from finite data. Concerning algorithm design, our method is unable to address scenarios where data from all source domains are not simultaneously available during training (i.e., online learning). Moreover, it may not be generalized to every non-stationary environment in some specific cases. This is due to the reliance of our method on the selection of hypothesis classes F, G.

## 7 CONCLUSION

In this paper, we theoretically and empirically studied domain generalization under non-stationary environments. We first established the upper bounds of prediction error on target domains, and then proposed a representation learningbased method that learns adaptive invariant representations across source domains. The resulting models trained with the proposed method can generalize well to unseen target domains. Experiments on both synthetic and real data demon strate the effectiveness of our proposed method.

## Acknowledgements

This work was funded in part by the National Science Foundation under award number IIS-2145625, by the National Institutes of Health under award number R01GM141279, and by The Ohio State University President’s Research Excellence Accelerator Grant.

## References

Isabela Albuquerque, João Monteiro, Mohammad Darvishi, Tiago H Falk, and Ioannis Mitliagkas. Generalizing to unseen domains via distribution matching. arXiv preprint arXiv:1911.00804, 2019.

Martin Arjovsky, Léon Bottou, Ishaan Gulrajani, and David Lopez-Paz. Invariant risk minimization. arXiv preprint arXiv:1907.02893, 2019.

Guangji Bai, Ling Chen, and Liang Zhao. Temporal domain generalization with drift-aware dynamic neural network. arXiv preprint arXiv:2205.10664, 2022.

Yogesh Balaji, Swami Sankaranarayanan, and Rama Chellappa. Metareg: Towards domain generalization using meta-regularization. Advances in neural information processing systems, 31, 2018.

Peter L Bartlett and Shahar Mendelson. Rademacher and gaussian complexities: Risk bounds and structural results. Journal ofMachine Learning Research, 3(Nov):463–482, 2002.

Gérard Biau, Benoît Cadre, Maxime Sangnier, and Ugo Tanielian. Some theoretical properties of GANS. The Annals ofStatistics, 48(3):1539 – 1566, 2020.

Arslan Chaudhry, Marc’Aurelio Ranzato, Marcus Rohrbach, and Mohamed Elhoseiny. Efficient lifelong learning with a-gem. In International Conference on Learning Representations, 2018.

Hong-You Chen and Wei-Lun Chao. Gradual domain adaptation without indexed intermediate domains. Advances in Neural Information Processing Systems, 34:8201–8214, 2021.

Yining Chen, Colin Wei, Ananya Kumar, and Tengyu Ma. Self-training avoids using spurious features under domain shift. Advances in Neural Information Processing Systems, 33:21061–21071, 2020.

Gordon Christie, Neil Fendley, James Wilson, and Ryan Mukherjee. Functional map of the world. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pages 6172–6180, 2018.

Yaroslav Ganin, Evgeniya Ustinova, Hana Ajakan, Pascal Germain, Hugo Larochelle, François Laviolette, Mario Marchand, and Victor Lempitsky. Domain-adversarial training of neural networks. The journal of machine learning research, 17(1):2096–2030, 2016.

Shiry Ginosar, Kate Rakelly, Sarah Sachs, Brian Yin, and Alexei A Efros. A century of portraits: A visual historical record of american high school yearbooks. In Proceedings ofthe IEEE International Conference on Computer Vision Workshops, pages 1–7, 2015.

Ian Goodfellow, Jean Pouget-Abadie, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair, Aaron Courville, and Yoshua Bengio. Generative adversarial nets. Advances in neural information processing systems, 27, 2014.

Lin Lawrence Guo, Stephen R Pfohl, Jason Fries, Alistair EW Johnson, Jose Posada, Catherine Aftandilian, Nigam Shah, and Lillian Sung. Evaluation of domain generalization and adaptation on improving model robustness to temporal dataset shift in clinical medicine. Scientific reports, 12(1):1–10, 2022.

Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep residual learning for image recognition. In Proceedings ofthe IEEE conference on computer vision and pattern recognition, pages 770–778, 2016.

Sepp Hochreiter and Jürgen Schmidhuber. Long short-term memory. Neural computation, 9(8):1735–1780, 1997.

Seogkyu Jeon, Kibeom Hong, Pilhyeon Lee, Jewook Lee, and Hyeran Byun. Feature stylization and domain-aware contrastive learning for domain generalization. In Proceedings ofthe 29th ACM International Conference on Multimedia, pages 22–31, 2021.

Daehee Kim, Youngjun Yoo, Seunghyun Park, Jinkyu Kim, and Jaekoo Lee. Selfreg: Self-supervised contrastive regularization for domain generalization. In Proceedings ofthe IEEE/CVF International Conference on Computer Vision, pages 9619–9628, 2021.

James Kirkpatrick, Razvan Pascanu, Neil Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei A Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, et al. Overcoming catastrophic forgetting in neural networks. Proceedings ofthe national academy of sciences, 114(13):3521–3526, 2017.

Pang Wei Koh, Shiori Sagawa, Henrik Marklund, Sang Michael Xie, Marvin Zhang, Akshay Balsubramani,

Weihua Hu, Michihiro Yasunaga, Richard Lanas Phillips, Irena Gao, et al. Wilds: A benchmark of in-the-wild distribution shifts. In International Conference on Machine Learning, pages 5637–5664. PMLR, 2021.

Vladimir Koltchinskii and Dmitriy Panchenko. Rademacher processes and bounding the risk of function learning. In High dimensional probability II, pages 443–457. Springer, 2000.

Ananya Kumar, Tengyu Ma, and Percy Liang. Understanding self-training for gradual domain adaptation. In International Conference on Machine Learning, pages 5468– 5479. PMLR, 2020.

Yann LeCun, Léon Bottou, Yoshua Bengio, and Patrick Haffner. Gradient-based learning applied to document recognition. Proceedings ofthe IEEE, 86(11):2278–2324, 1998.

Da Li, Yongxin Yang, Yi-Zhe Song, and Timothy Hospedales. Learning to generalize: Meta-learning for domain generalization. In Proceedings ofthe AAAI conference on artificial intelligence, volume 32, 2018a.

Ya Li, Xinmei Tian, Mingming Gong, Yajing Liu, Tongliang Liu, Kun Zhang, and Dacheng Tao. Deep domain generalization via conditional invariant adversarial networks. In Proceedings of the European Conference on Computer Vision (ECCV), pages 624–639, 2018b.

Yingzhen Li and Stephan Mandt. Disentangled sequential autoencoder. In International conference on machine learning. PMLR, 2018.

Zheren Li, Zhiming Cui, Sheng Wang, Yuji Qi, Xi Ouyang, Qitian Chen, Yuezhi Yang, Zhong Xue, Dinggang Shen, and Jie-Zhi Cheng. Domain generalization for mammography detection via multi-style and multi-view contrastive learning. In International Conference on Medical Image Computing and Computer-Assisted Intervention, pages 98–108. Springer, 2021.

Percy Liang. Statistical learning theory (2016). URL https://web. stanford. edu/class/cs229t/notes. pdf, 2016.

Zhiqiu Lin, Jia Shi, Deepak Pathak, and Deva Ramanan. The clear benchmark: Continual learning on real-world imagery. In Thirty-fifth conference on neural information processing systems datasets and benchmarks track (round 2), 2021.

Arun Mallya and Svetlana Lazebnik. Packnet: Adding multiple tasks to a single network by iterative pruning. In Proceedings ofthe IEEE conference on Computer Vision and Pattern Recognition, pages 7765–7773, 2018.

Yishay Mansour, Mehryar Mohri, and Afshin Rostamizadeh. Domain adaptation: Learning bounds and algorithms. arXiv preprint arXiv:0902.3430, 2009.

Mehryar Mohri and Andres Muñoz Medina. New analysis and algorithm for learning with drifting distributions. In Algorithmic Learning Theory: 23rd International Conference, ALT 2012, Lyon, France, October 29-31, 2012. Proceedings 23, pages 124–138. Springer, 2012.

A Tuan Nguyen, Toan Tran, Yarin Gal, and Atilim Gunes Baydin. Domain invariant representation learning with domain density transformations. Advances in Neural Information Processing Systems, 34, 2021a.

A Tuan Nguyen, Toan Tran, Yarin Gal, Philip Torr, and Atilim Gunes Baydin. Kl guided domain adaptation. In International Conference on Learning Representations, 2021b.

Guillermo Ortiz-Jimenez, Mireille El Gheche, Effrosyni Simou, Hermina Petric Maretic, and Pascal Frossard. Cdot: Continuous domain adaptation using optimal transport. arXiv preprint arXiv:1909.11448, 2019.

Ali Pesaranghader and Herna L Viktor. Fast hoeffding drift detection method for evolving data streams. In Joint European conference on machine learning and knowledge discovery in databases, pages 96–111. Springer, 2016.

Thai-Hoang Pham, Xueru Zhang, and Ping Zhang. Fairness and accuracy under domain generalization. In The Eleventh International Conference on Learning Representations, 2023.

Trung Phung, Trung Le, Tung-Long Vuong, Toan Tran, Anh Tran, Hung Bui, and Dinh Phung. On learning domaininvariant representations for transfer learning with multiple sources. Advances in Neural Information Processing Systems, 34, 2021.

Fengchun Qiao, Long Zhao, and Xi Peng. Learning to learn single domain generalization. In Proceedings ofthe IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 12556–12565, 2020.

Tiexin Qin, Shiqi Wang, and Haoliang Li. Generalizing to evolving domains with latent structure-aware sequential autoencoder. arXiv preprint arXiv:2205.07649, 2022.

Alexandre Rame, Corentin Dancette, and Matthieu Cord. Fishr: Invariant gradient variances for out-of-distribution generalization. arXiv preprint arXiv:2109.02934, 2021.

Shiori Sagawa, Pang Wei Koh, Tatsunori B Hashimoto, and Percy Liang. Distributionally robust neural networks. In International Conference on Learning Representations, 2019.

Yuge Shi, Jeffrey Seely, Philip Torr, N Siddharth, Awni Hannun, Nicolas Usunier, and Gabriel Synnaeve. Gradient matching for domain generalization. In International Conference on Learning Representations, 2022.

Baochen Sun and Kate Saenko. Deep coral: Correlation alignment for deep domain adaptation. In European conference on computer vision, pages 443–450. Springer, 2016.

Chris Xing Tian, Haoliang Li, Xiaofei Xie, Yang Liu, and Shiqi Wang. Neuron coverage-guided domain generalization. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2022.

Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. Attention is all you need. Advances in neural information processing systems, 30, 2017.

Hao Wang, Hao He, and Dina Katabi. Continuously indexed domain adaptation. arXiv preprint arXiv:2007.01807, 2020.

Jingge Wang, Yang Li, Liyan Xie, and Yao Xie. Classconditioned domain generalization via wasserstein distributional robust optimization. arXiv preprint arXiv:2109.03676, 2021.

Binghui Xie, Yongqiang Chen, Jiaqi Wang, Kaiwen Zhou, Bo Han, Wei Meng, and James Cheng. Enhancing evolving domain generalization through dynamic latent representations. In Proceedings of the AAAI Conference on Artificial Intelligence, volume 38, 2024.

Qiuhao Zeng, Wei Wang, Fan Zhou, Charles Ling, and Boyu Wang. Foresee what you will learn: Data augmentation for domain generalization in non-stationary environments. In Proceedings ofthe AAAI conference on artificial intelligence, 2023.

Qiuhao Zeng, Changjian Shui, Long-Kai Huang, Peng Liu, Xi Chen, Charles Ling, and Boyu Wang. Latent trajectory learning for limited timestamps under distribution shift over time. In The Twelfth International Conference on Learning Representations, 2024a.

Qiuhao Zeng, Wei Wang, Fan Zhou, Gezheng Xu, Ruizh Pu, Changjian Shui, Christian Gagné, Shichun Yang, Charles X Ling, and Boyu Wang. Generalizing across temporal domains with koopman operators. In Proceedings of the AAAI Conference on Artificial Intelligence, volume 38, pages 16651–16659, 2024b.

Hongyi Zhang, Moustapha Cisse, Yann N Dauphin, and David Lopez-Paz. mixup: Beyond empirical risk minimization. In International Conference on Learning Representations, 2018.

Kaiyang Zhou, Yongxin Yang, Timothy Hospedales, and Tao Xiang. Learning to generate novel domains for do main generalization. In European conference on computer vision, pages 561–578. Springer, 2020.

# Non-stationary Domain Generalization: Theory and Algorithm (Supplementary Material)

Thai-Hoang Pham<sup>1,2</sup>

Xueru Zhang<sup>1</sup>

Ping Zhang<sup>1,2</sup>

<sup>1</sup>Department of Computer Science and Engineering, The Ohio State University, USA <sup>2</sup>Department of Biomedical Informatics, The Ohio State University, USA {pham.375,zhang.12807,zhang.10631}@osu.edu

## A PROOFS

## A.1 ADDITIONAL LEMMAS

Lemma 1. Given two domains $D _ { t }$ and $D _ { t ^ { \prime } }$ , then for any classifier $h \in \mathcal { H }$ , the expected error of h in domain $D _ { t }$ can be upper bounded:

$$
\epsilon_ {D _ {t}} (h) \leq \epsilon_ {D _ {t ^ {\prime}}} (h) + \sqrt {2} C \times \mathcal {D} _ {J S} \left(P _ {D _ {t}} ^ {X, Y} \| P _ {D _ {t ^ {\prime}}} ^ {X, Y}\right) ^ {1 / 2}
$$

where $\mathcal { D } _ { J S } \left( \cdot \parallel \cdot \right)$ is JS-divergence between two distributions.

Proof of Lemma 1 Let $D _ { K L } \left( \cdot \parallel \cdot \right)$ be KL-divergence and $U = ( X , Y )$ and $L ( U ) = L \left( h ( X ) , Y \right)$ . We first prove $\begin{array} { r } { \int _ { \mathcal E } \left| P _ { D _ { t } } ^ { U = u } - P _ { D _ { t ^ { \prime } } } ^ { U = u } \right| d u = \frac 1 2 \int \left| P _ { D _ { t } } ^ { U = u } - P _ { D _ { t ^ { \prime } } } ^ { U = u } \right| } \end{array}$ du where E is the event that $P _ { D _ { t } } ^ { U = u } \ge P _ { D _ { t ^ { \prime } } } ^ { U = u }$ (∗) as follows:

$$
\begin{array}{r l} & {\int_ {\mathcal {E}} \left| P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u} \right| d u = \int_ {\mathcal {E}} \left(P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u}\right) d u} \\ & {\qquad = \int_ {\mathcal {E} \cup \overline {{{\mathcal {E}}}}} \left(P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u}\right) d u - \int_ {\overline {{{\mathcal {E}}}}} \left(P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u}\right) d u} \\ & {\qquad \overset {(1)} {=} \int_ {\overline {{{\mathcal {E}}}}} \left(P _ {D _ {t ^ {\prime}}} ^ {U = u} - P _ {D _ {t}} ^ {U = u}\right) d u} \\ & {\qquad = \int_ {\overline {{{\mathcal {E}}}}} \left| P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u} \right| d u} \\ & {\qquad = \frac 12 \int \left| P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u} \right| d u} \end{array}
$$

where $\overline { { \mathcal { E } } }$ is the complement of E. We have $\stackrel { \left( 1 \right) } { = }$ because $\begin{array} { r } { \int _ { \mathcal { E } \cup \overline { { \mathcal { E } } } } \left( P _ { D _ { t } } ^ { U = u } - P _ { D _ { t ^ { \prime } } } ^ { U = u } \right) d u = \int _ { \mathcal { U } } \left( P _ { D _ { t } } ^ { U = u } - P _ { D _ { t ^ { \prime } } } ^ { U = u } \right) d u = 0 } \end{array}$ . Then, we have:

$$
\begin{array}{l} \epsilon_ {D _ {t}} (h) = \mathbb {E} _ {D _ {t}} [ L (U) ] \\ = \int_ {\mathcal {U}} L (u) P _ {D _ {t}} ^ {U = u} d u \\ = \int_ {\mathcal {U}} L (u) P _ {D _ {t ^ {\prime}}} ^ {U = u} d u + \int_ {\mathcal {U}} L (u) \left(P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u}\right) d u \\ = \mathbb {E} _ {D _ {t ^ {\prime}}} [ L (U) ] + \int_ {\mathcal {U}} L (u) \left(P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u}\right) d u \\ = \epsilon_ {D _ {t ^ {\prime}}} (h) + \int_ {\mathcal {E}} L (u) \left(P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u}\right) d u + \int_ {\overline {{\mathcal {E}}}} L (u) \left(P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u}\right) d u \\ \stackrel {(2)} {\leq} \epsilon_ {D _ {t ^ {\prime}}} (h) + \int_ {\mathcal {E}} L (u) \left(P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u}\right) d u \\ \stackrel {(3)} {\leq} \epsilon_ {D _ {t ^ {\prime}}} (h) + C \int_ {\mathcal {E}} \left(P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u}\right) d u \\ = \epsilon_ {D _ {t ^ {\prime}}} (h) + C \int_ {\mathcal {E}} \left| P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u} \right| d u \\ \stackrel {(4)} {=} \epsilon_ {D _ {t ^ {\prime}}} (h) + \frac {C}{2} \int \left| P _ {D _ {t}} ^ {U = u} - P _ {D _ {t ^ {\prime}}} ^ {U = u} \right| d u \\ \stackrel {(5)} {\leq} \epsilon_ {D _ {t ^ {\prime}}} (h) + \frac {C}{2} \sqrt {2 \min \left(\mathcal {D} _ {K L} \left(P _ {D _ {t ^ {\prime}}} ^ {U} \| P _ {D _ {t}} ^ {U}\right) , \mathcal {D} _ {K L} \left(P _ {D _ {t}} ^ {U} \| P _ {D _ {t ^ {\prime}}} ^ {U}\right)\right)} \\ \leq \epsilon_ {D _ {t ^ {\prime}}} (h) + \frac {C}{\sqrt 2} \sqrt {\mathcal {D} _ {K L} \left(P _ {D _ {t ^ {\prime}}} ^ {U} \| P _ {D _ {t}} ^ {U}\right)} (\ast \ast) \end{array}
$$

We have $\stackrel { ( 2 ) } { \leq }$ because $\begin{array} { r } { \int _ { \overline { { \varepsilon } } } L ( u ) \left( P _ { D _ { t } } ^ { U = u } - P _ { D _ { t ^ { \prime } } } ^ { U = u } \right) d u \leq 0 ; \stackrel { ( 3 ) } { \leq } } \end{array}$ because $L ( u )$ is non-negative function and is bounded by $C ;$ $\stackrel { \left( 4 \right) } { = }$ by using $( * ) ; { \overset { ( 5 ) } { \leq } }$ by using Pinsker’s inequality between total variation norm and KL-divergence.

Let $\begin{array} { r } { P _ { D _ { t , t ^ { \prime } } } ^ { U } = \frac { 1 } { 2 } \left( P _ { D _ { t } } ^ { U } + P _ { D _ { t ^ { \prime } } } ^ { U } \right) } \end{array}$ . Apply (∗∗) for two domains $D _ { t }$ and $D _ { t , t ^ { \prime } }$ , we have:

$$
\epsilon_ {D _ {t}} (h) \leq \epsilon_ {D _ {t, t ^ {\prime}}} (h) + \frac {C}{\sqrt {2}} \sqrt {\mathcal {D} _ {K L} \left(P _ {D _ {t}} ^ {U} \| P _ {D _ {t , t ^ {\prime}}} ^ {U}\right)}\tag{7}
$$

Apply (∗∗) again for two domains $D _ { t , t ^ { \prime } }$ and $D _ { t ^ { \prime } }$ , we have:

$$
\epsilon_ {D _ {t, t ^ {\prime}}} (h) \leq \epsilon_ {D _ {t ^ {\prime}}} (h) + \frac {C}{\sqrt {2}} \sqrt {\mathcal {D} _ {K L} \left(P _ {D _ {t ^ {\prime}}} ^ {U} \| P _ {D _ {t , t ^ {\prime}}} ^ {U}\right)}\tag{8}
$$

Adding Eq. (7) to Eq. (8) and subtracting $\epsilon _ { D _ { t , t ^ { \prime } } }$ , we have:

$$
\begin{array}{l} \epsilon_ {D _ {t}} (h) \leq \epsilon_ {D _ {t ^ {\prime}}} (h) + \frac {C}{\sqrt {2}} \left(\sqrt {\mathcal {D} _ {K L} \left(P _ {D _ {t}} ^ {U} \| P _ {D _ {t , t ^ {\prime}}} ^ {U}\right)} + \sqrt {\mathcal {D} _ {K L} \left(P _ {D _ {t ^ {\prime}}} ^ {U} \| P _ {D _ {t , t ^ {\prime}}} ^ {U}\right)}\right) \\ \stackrel {{(6)}} {{\leq}} \epsilon_ {D _ {t ^ {\prime}}} (h) + \frac {C}{\sqrt {2}} \sqrt {2 \left(\mathcal {D} _ {K L} \left(P _ {D _ {t}} ^ {U} \| P _ {D _ {t , t ^ {\prime}}} ^ {U}\right) + \mathcal {D} _ {K L} \left(P _ {D _ {t ^ {\prime}}} ^ {U} \| P _ {D _ {t , t ^ {\prime}}} ^ {U}\right)\right)} \\ = \epsilon_ {D _ {t ^ {\prime}}} (h) + \frac {C}{\sqrt {2}} \sqrt {4 \mathcal {D} _ {J S} \left(P _ {D _ {t ^ {\prime}}} ^ {U} \| P _ {D _ {t}} ^ {U}\right)} \\ = \epsilon_ {D _ {t ^ {\prime}}} (h) + \sqrt {2} C \sqrt {\mathcal {D} _ {J S} \left(P _ {D _ {t ^ {\prime}}} ^ {U} \| P _ {D _ {t}} ^ {U}\right)} \end{array}
$$

We have $\begin{array} { c } { { ( 6 ) } } \\ { { \leq } } \end{array}$ by using Cauchy–Schwarz inequality.

Lemma 2. Given domain D, then for any $\delta > 0 ,$ , with probability at least $1 - \delta$ over samples S ofsize n drawn i.i.dfrom domain $D ,$ , for all $h \in \mathcal { H } ,$ , the expected error ofh in domain $D$ can be upper bounded:

$$
\epsilon_ {D} (h) \leq \epsilon_ {S} (h) + \frac {2 B}{\sqrt {n}} + C \sqrt {\frac {\log (1 / \delta)}{2 n}}
$$

Proof of Lemma 2 We start from the Rademacher bound Koltchinskii and Panchenko [2000] which is stated as follows.

Lemma 3. Rademacher Bounds. Let F be a family of functions mapping from Z to $[ 0 , 1 ]$ . Then, for any $0 < \delta < 1$ , with probability at least $1 - \delta$ over sample $S = \{ z _ { 1 } , \cdots , z _ { n } \}$ , the following holds for all $f \in { \mathcal { F } } .$ :

$$
\mathbb {E} \left[ f ^ {Z} \right] \leq \frac {1}{n} \sum_ {i = 1} ^ {n} f (z _ {i}) + 2 \mathcal {R} _ {n} (\mathcal {F}) + \sqrt {\frac {\log (1 / \delta)}{2 n}}
$$

where $\mathcal { R } _ { n } \left( \mathcal { F } \right)$ is a Rademacher complexity of function class ${ \mathcal F } .$

We then apply Lemma 3 to our setting with $Z = ( X , Y )$ , the loss function L bounded by $C ,$ and the function class $\mathcal { L } _ { \mathcal { H } } = \{ ( x , y )  L ( h ( x ) , y ) : h \in \mathcal { H } \}$ . In particular, we scale the loss function $L \operatorname { t o } \ [ 0 , 1 ]$ by dividing by C and denote the new class of scaled loss functions as ${ \mathcal { L } } _ { \mathcal { H } } / C$ . Then, for any $\delta > 0$ , with probability at least $1 - \delta$ , we have:

$$
\begin{array}{l} \frac {\epsilon_ {D} (h)}{C} \leq \frac {\epsilon_ {S} (h)}{C} + 2 \mathcal {R} _ {n} (\mathcal {L} _ {\mathcal {H}} / C) + \sqrt {\frac {\log (1 / \delta)}{2 n}} \\ \stackrel {{(1)}} {{=}} \frac {\epsilon_ {S} (h)}{C} + \frac {2}{C} \mathcal {R} _ {n} (\mathcal {L} _ {\mathcal {H}}) + \sqrt {\frac {\log (1 / \delta)}{2 n}} \\ \stackrel {{(2)}} {{\leq}} \frac {\epsilon_ {S} (h)}{C} + \frac {2 B}{C \sqrt {n}} + \sqrt {\frac {\log (1 / \delta)}{2 n}} \end{array}\tag{9}
$$

We have $\stackrel { ( 1 ) } { = }$ by using the property of Redamacher complexity that $\mathcal { R } _ { n } ( \alpha \mathcal { F } ) = \alpha \mathcal { R } _ { n } ( \mathcal { F } ) , \overset { ( 2 ) } { \leq }$ because of bounded Rademacher complexity assumption. We derive Lemma 2 by multiplying Eq. (9) by C.

Lemma 4. Given domain sequence $\{ D _ { t } \}$ , dataset sequence $\{ S _ { t } \}$ sampled from $\{ D _ { t } \}$ , M-optimal model sequence $H ^ { M } =$ $\left\{ h _ { 1 } ^ { M } , \cdots , h _ { T + K } ^ { M } \right\}$ , M-empirical optimal model sequence $\widehat { H } _ { M } = \left\{ \widehat { h } _ { 1 } ^ { M } , \cdots , \widehat { h } _ { T + K } ^ { M } \right\}$ , then for any t and any $\delta > 0$ , with probability at least $1 - \delta$ over samples $S _ { t }$ ofsize n drawn i.i.dfrom domain $D _ { t } ,$ we have:

$$
\epsilon_ {D _ {t}} \left(\widehat {h} _ {t} ^ {M}\right) \leq \epsilon_ {D _ {t}} \left(h _ {t} ^ {M}\right) + 2 \sqrt {2} C \mathcal {D} _ {J S} \left(D _ {t} \| D _ {t} ^ {M}\right) ^ {1 / 2} + \frac {4 B}{\sqrt {n}} + \sqrt {\frac {2 \log (1 / \delta)}{n}}
$$

Proof of Lemma 4 We have:

$$
\begin{array}{l} \epsilon_ {D _ {t}} \left(\widehat {h} _ {t} ^ {M}\right) \stackrel {{(1)}} {{\leq}} \epsilon_ {D _ {t} ^ {M}} \left(\widehat {h} _ {t} ^ {M}\right) + \sqrt {2} C \mathcal {D} _ {J S} \left(D _ {t} \parallel D _ {t} ^ {M}\right) ^ {1 / 2} \\ \stackrel {{(2)}} {{\leq}} \epsilon_ {S _ {t} ^ {M}} \left(\widehat {h} _ {t} ^ {M}\right) + \sqrt {2} C \mathcal {D} _ {J S} \left(D _ {t} \parallel D _ {t} ^ {M}\right) ^ {1 / 2} + \frac {2 B}{\sqrt {n}} + \sqrt {\frac {\log (1 / \delta^ {\prime})}{2 n}} \quad (\mathrm{w.p} \geq 1 - \delta^ {\prime}) \\ \stackrel {{(3)}} {{\leq}} \epsilon_ {S _ {t} ^ {M}} \left(h _ {t} ^ {M}\right) + \sqrt {2} C \mathcal {D} _ {J S} \left(D _ {t} \parallel D _ {t} ^ {M}\right) ^ {1 / 2} + \frac {2 B}{\sqrt {n}} + \sqrt {\frac {\log (1 / \delta^ {\prime})}{2 n}} \\ \stackrel {{(4)}} {{\leq}} \epsilon_ {D _ {t} ^ {M}} \left(h _ {t} ^ {M}\right) + \sqrt {2} C \mathcal {D} _ {J S} \left(D _ {t} \parallel D _ {t} ^ {M}\right) ^ {1 / 2} + \frac {4 B}{\sqrt {n}} + \sqrt {\frac {2 \log (1 / \delta^ {\prime})}{n}} \quad (\mathrm{w.p} \geq 1 - \delta^ {\prime}) \\ \stackrel {{(5)}} {{\leq}} \epsilon_ {D _ {t}} \left(h _ {t} ^ {M}\right) + 2 \sqrt {2} C \mathcal {D} _ {J S} \left(D _ {t} \parallel D _ {t} ^ {M}\right) ^ {1 / 2} + \frac {4 B}{\sqrt {n}} + \sqrt {\frac {2 \log (1 / \delta^ {\prime})}{n}} \end{array}
$$

We have $\overset { ( 1 ) } { \leq }$ by using Lemma 1 for $\epsilon _ { D _ { t } } ~ \biggl ( \widehat { h } _ { t } ^ { M } \biggr ) , ~ \stackrel { ( 2 ) } { \leq }$ by using Lemma 2 for $\epsilon _ { D _ { t } ^ { M } } \Big ( \widehat { h } _ { t } ^ { M } \Big ) , \ \stackrel { ( 3 ) } { \leq }$ because $\begin{array} { r l } { \widehat { h } _ { t } ^ { M } } & { { } = } \end{array}$ arg $\begin{array} { r } { \operatorname* { m i n } _ { h \in \mathcal { H } } \epsilon _ { S _ { t } ^ { M } } \left( h \right) , \overset { ( 4 ) } { \le } } \end{array}$ by using Lemma 2 for $\epsilon _ { S _ { t } ^ { M } } \big ( h _ { t } ^ { M } \big ) , \stackrel { ( 5 ) } { \leq }$ by using Lemma 1 for $\epsilon _ { D _ { t } ^ { M } } \left( \widehat { h } _ { t } ^ { M } \right)$ . Finally, using union bound for $\stackrel { ( 2 ) } { \leq }$ and $\begin{array} { c } { { ( 4 ) } } \\ { { \leq } } \end{array}$ , and denote $\delta = 2 \delta ^ { \prime }$ , we have:

$$
\epsilon_ {D _ {t}} \left(\widehat {h} _ {t} ^ {M}\right) \leq \epsilon_ {D _ {t}} \left(h _ {t} ^ {M}\right) + 2 \sqrt {2} C \mathcal {D} _ {J S} \left(D _ {t} \| D _ {t} ^ {M}\right) ^ {1 / 2} + \frac {4 B}{\sqrt {n}} + \sqrt {\frac {2 \log (1 / \delta)}{n}}
$$

Lemma 5. Given domain sequence $\{ D _ { t } \}$ , dataset sequence $\{ S _ { t } \}$ sampled from $\{ D _ { t } \}$ , M-optimal model sequence $H ^ { M } =$ $\left\{ h _ { 1 } ^ { M } , \cdots , h _ { T + K } ^ { M } \right\}$ , M-empirical optimal model sequence $\widehat { H } _ { M } = \left\{ \widehat { h } _ { 1 } ^ { M } , \cdots , \widehat { h } _ { T + K } ^ { M } \right\}$ , then for any t, we have:

$$
\epsilon_ {D _ {t}} \left(h _ {t} ^ {M}\right) \leq \epsilon_ {D _ {t}} \left(\widehat {h} _ {t} ^ {M}\right) + 2 \sqrt {2} C \mathcal {D} _ {J S} \left(D _ {t} \| D _ {t} ^ {M}\right) ^ {1 / 2}
$$

Proof of Lemma 5 We have:

$$
\begin{array}{r l} \epsilon_ {D _ {t}} \left(h _ {t} ^ {M}\right) & \overset {(1)} {\leq} \epsilon_ {D _ {t} ^ {M}} \left(h _ {t} ^ {M}\right) + \sqrt {2} C \mathcal {D} _ {J S} \left(D _ {t} \parallel D _ {t} ^ {M}\right) ^ {1 / 2} \\ & \overset {(2)} {\leq} \epsilon_ {D _ {t} ^ {M}} \left(\widehat {h} _ {t} ^ {M}\right) + \sqrt {2} C \mathcal {D} _ {J S} \left(D _ {t} \parallel D _ {t} ^ {M}\right) ^ {1 / 2} \\ & \overset {(3)} {\leq} \epsilon_ {D _ {t}} \left(\widehat {h} _ {t} ^ {M}\right) + 2 \sqrt {2} C \mathcal {D} _ {J S} \left(D _ {t} \parallel D _ {t} ^ {M}\right) ^ {1 / 2} \end{array}
$$

We have $\overset { ( 1 ) } { \leq }$ by using Lemma 1 for $\epsilon _ { D _ { t } } \left( h _ { t } ^ { M } \right) , \stackrel { ( 2 ) } { \leq }$ because $\begin{array} { r } { h _ { t } ^ { M } \ = \ \arg \operatorname* { m i n } _ { h \in \mathcal { H } } \epsilon _ { D _ { t } ^ { M } } \big ( h \big ) , \ \stackrel { \mathrm { ( 3 ) } } { \leq } \ } \end{array}$ by using Lemma 1 for $\epsilon _ { D _ { t } ^ { M } } \left( \widehat { h } _ { t } ^ { M } \right)$

## A.2 PROOF OF MAIN THEOREMS.

## A.2.1 Proof of Theorem 1

We have:

$$
\begin{array} { l } E _ { t g t } \left( \widehat { H } ^ { M } \right) = \frac { 1 } { K } \sum _ { t = T + 1 } ^ { T + K } \epsilon _ { D _ { t } } \left( \widehat { h } _ { t } ^ { M } \right) \\ \stackrel { ( 1 ) } { \leq } \frac { 1 } { K } \sum _ { t = T + 1 } ^ { T + K } \left( \epsilon _ { D _ { t } } \left( h _ { t } ^ { M } \right) + 2 \sqrt { 2 } C \times \mathcal { D } _ { J S } \left( D _ { t } \parallel D _ { t } ^ { M } \right) ^ { 1 / 2 } + \frac { 4 B } { \sqrt { n } } + \sqrt { \frac { 2 \log ( 1 / \delta ^ { \prime } ) } { n } } \right) \quad ( \mathrm{w.p} \geq 1 - \delta ^ { \prime } ) \\ = E _ { t g t } \left( H ^ { M } \right) + 2 \sqrt { 2 } C \times D _ { t g t } ( M ) + \frac { 4 B } { \sqrt { n } } + \sqrt { \frac { 2 \log ( 1 / \delta ^ { \prime } ) } { n } } \\ = E _ { s r c } \left( H ^ { M } \right) + \left( E _ { t g t } \left( H ^ { M } \right) - E _ { s r c } \left( H ^ { M } \right) \right) + 2 \sqrt { 2 } C \times ( D _ { s r c } ( M ) + ( D _ { t g t } ( M ) - D _ { s r c } ( M ) ) ) \\ + \frac { 4 B } { \sqrt { n } } + \sqrt { \frac { 2 \log ( 1 / \delta ^ { \prime } ) } { n } } \\ \stackrel { ( 2 ) } { \leq } \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \epsilon _ { D _ { t } } \left( h _ { t } ^ { M } \right) + \Phi ( \mathcal { M } ) + 2 \sqrt { 2 } C \times D _ { s r c } ( M ) + 2 \sqrt { 2 } C \times \Phi ( \mathcal { M } , \mathcal { H } ) + \frac { 4 B } { \sqrt { n } } + \sqrt { \frac { 2 \log ( 1 / \delta ^ { \prime } ) } { n } } \\ \stackrel { ( 3 ) } { \leq } \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \left( \epsilon _ { D _ { t } } \left( \widehat h _ { t } ^ { M } \right) + 2 \sqrt { 2 } C \times \mathcal { D } _ { J S } \left( D _ { t } \parallel D _ { t } ^ { M } \right) ^ { 1 / 2 } \right) + \Phi ( \mathcal { M } ) + 2 \sqrt { 2 } C \times D _ { s r c } ( M ) + 2 \sqrt { 2 } C \times \Phi ( \mathcal { M } , \mathcal { H } ) \\ + \frac { 4 B } { \sqrt { n } } + \sqrt { \frac { 2 \log ( 1 / \delta ^ { \prime } ) } { n } } \\ \stackrel { ( 4 ) } { \leq } \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \epsilon _ { D _ { t } ^ { M } } \left( \widehat h _ { t } ^ { M } \right) + 5 \sqrt { 2 } C \times D _ { s r c } ( M ) + \Phi ( \mathcal { M } ) + 2 \sqrt { 2 } C \times \Phi ( \mathcal { M } , \mathcal { H } ) + \frac { 4 B } { \sqrt { n } } + \sqrt { \frac { 2 \log ( 1 / \delta ^ { \prime } ) } { n } } \\ \stackrel { ( 5 ) } { \leq } \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \left( \epsilon _ { S _ { t } ^ { M } } \left( \widehat h _ { t } ^ { M } \right) + \frac { 2 B } { \sqrt { n } } + \sqrt { \frac { log ( 1 / \delta ^ { \prime } ) } { 2 n } } \right) + 5 \sqrt { 2 } C \times D _ { s r c } ( M ) + \Phi ( \mathcal { M } ) + 2 \sqrt { 2 } C \times \Phi ( \mathcal { M } , \mathcal { H } ) \\ + \frac { 4 B } { \sqrt { n } } + \sum _ { t = T + 1 } ^ { T + K } {\sqrt {\frac { 2 log ( 1 / \delta ^ { \prime })}{n}}} (\mathrm{w.p}   {\geq}   1 - {\delta^ {\prime}}) \\ = {\widehat E} _ { s r c} ^ { M}   ( {\widehat H} ^ { M}) + 5 {\sqrt { 2 }} C   {\times}   D _ { s r c}   ( M ) + {\Phi} ( {\mathcal M}) + 2 {\sqrt { 2 }} C   {\times}   {\Phi} ( {\mathcal M}, {\mathcal H}) + {\frac { 6 B}{\sqrt { n }}} + 3 {\sqrt {\frac {\log ( 1 / {\delta^ {\prime}})}{2 n}}} . & & \\ & = {\widehat E} _ {{s r c}} ^ {{M}}   ( {\widehat H} ^ {{M}}) + 5 {\sqrt {{2}}} C   {\times}   D _ {{s r c}}   ( M ) + {\Phi} ( {\mathcal M}) + 2 {\sqrt {{2}}} C   {\times}   {\Phi} ( {\mathcal M}, {\mathcal H}) + \frac {}{}    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]    [   ]. & & \\ & = {\widehat E} _ {{s r c}} ^ {{M}}   ( {\widehat H} ^ {{M}}) + 5 {\sqrt {{2}}} C   {\times}   D _ {{s r c}}   ( M ) + {\Phi} ( {\mathcal M}) + 2 {\sqrt {{2}}} C   {\times}   {\Phi} ( {\mathcal M}, {\mathcal H}) + \frac {}{}
$$

We have $\begin{array} { l } { { \displaystyle \stackrel { \left( 1 \right) } { \leq } } } \end{array}$ by using Lemma 4 for $\epsilon _ { D _ { t } } \left( \widehat { h } _ { t } ^ { M } \right) , \stackrel { ( 2 ) } { \leq }$ because $\Phi \left( \mathcal { M } , \mathcal { H } \right) = \operatorname* { s u p } _ { M ^ { \prime } \in \mathcal { M } } \left( E _ { t g t } \left( H ^ { M ^ { \prime } } \right) - E _ { s r c } \left( H ^ { M ^ { \prime } } \right) \right)$ amd $\Phi \left( \mathcal { M } \right) = \operatorname* { s u p } _ { M ^ { \prime } \in \mathcal { M } } \left( D _ { t g t } \left( M ^ { \prime } \right) - D _ { s r c } \left( M ^ { \prime } \right) \right) , \stackrel { ( 3 ) } { \leq }$ by using Lemma 5 for $\epsilon _ { D _ { t } } \left( h _ { t } ^ { M } \right) , \stackrel { ( 4 ) } { \leq }$ by using Lemma 2 for $\epsilon _ { D _ { t } } \left( \widehat { h } _ { t } ^ { M } \right)$ , ≤ (5) by using Lemma 1 for $\epsilon _ { D _ { t } ^ { M } } \left( \widehat { h } _ { t } ^ { M } \right)$ . Finally, using union bound for $\stackrel { ( 2 ) } { \leq }$ and $\begin{array} { c } { { ( 4 ) } } \\ { { \leq } } \end{array}$ , and denote $\delta = ( T + K ) \delta ^ { \prime }$ , we have:

$$
E _ {t g t} \left(\widehat {H} ^ {M}\right) \leq \widehat {E} _ {s r c} ^ {M} \left(\widehat {H} ^ {M}\right) + 5 \sqrt {2} C \times D _ {s r c} (M) + \Phi (\mathcal {M}) + 2 \sqrt {2} C \times \Phi (\mathcal {M}, \mathcal {H}) + \frac {6 B}{\sqrt {n}} + 3 \sqrt {\frac {\log ((T + K) / \delta)}{2 n}}\tag{10}
$$

Note that the high probability bounds in Lemma 2 and Lemma 4 relates to hypothesis class H only. Therefore, Eq. (10) still holds for M depended on dataset sequence $\left\{ S _ { t } \right\} _ { t = 1 } ^ { T + K }$

## A.2.2 Proof of Proposition 1

$\forall y \in \mathcal { V }$ , we have the following (∗):

$$
\begin{array}{l} P _ {D _ {t - 1} ^ {W}} ^ {Y = y} = \int_ {\mathcal {X}} P _ {D _ {t - 1} ^ {W}} ^ {X = x, Y = y} d x \\ \qquad = \int_ {\mathcal {X}} w _ {y} \times P _ {D _ {t - 1}} ^ {X = x, Y = y} d x \\ \qquad = \int_ {\mathcal {X}} \frac {P _ {D _ {t}} ^ {Y = y}}{P _ {D _ {t - 1}} ^ {Y = y}} \times P _ {D _ {t - 1}} ^ {X = x, Y = y} d x \\ \qquad = P _ {D _ {t}} ^ {Y = y} \int_ {\mathcal {X}} P _ {D _ {t - 1}} ^ {X = x | Y = y} d x \\ \qquad = P _ {D _ {t}} ^ {Y = y} \end{array}
$$

We have:

$$
\begin{array}{r l} & {\mathcal {D} _ {K L} \left(P _ {D _ {t}} ^ {X, Y}, P _ {D _ {t} ^ {W, M}} ^ {X, Y}\right) = \mathbb {E} _ {P _ {D _ {t}} ^ {X, Y}} \left[ \log P _ {D _ {t}} ^ {X, Y} - \log P _ {D _ {t} ^ {W, M}} ^ {X, Y} \right]} \\ & {\qquad = \mathbb {E} _ {P _ {D _ {t}} ^ {X, Y}} \left[ \log P _ {D _ {t}} ^ {Y} + \log P _ {D _ {t}} ^ {X | Y} \right] - \mathbb {E} _ {P _ {D _ {t}} ^ {X, Y}} \left[ \log P _ {D _ {t} ^ {W, M}} ^ {Y} + \log P _ {D _ {t} ^ {W, M}} ^ {X | Y} \right]} \\ & {\qquad = \mathbb {E} _ {P _ {D _ {t}} ^ {X, Y}} \left[ \log P _ {D _ {t}} ^ {Y} - \log P _ {D _ {t} ^ {W, M}} ^ {Y} \right] + \mathbb {E} _ {P _ {D _ {t}} ^ {X, Y}} \left[ \log P _ {D _ {t}} ^ {X | Y} - \log P _ {D _ {t} ^ {W, M}} ^ {X | Y} \right]} \\ & {\stackrel {(1)} {=} \mathbb {E} _ {P _ {D _ {t}} ^ {Y}} \left[ \mathbb {E} _ {P _ {D _ {t}} ^ {X | Y}} \left[ \log P _ {D _ {t}} ^ {X | Y} - \log P _ {D _ {t} ^ {W, M}} ^ {X | Y} \right] \right]} \\ & {\qquad = \mathbb {E} _ {P _ {D _ {t}} ^ {Y}} \left[ \mathcal {D} _ {K L} \left(P _ {D _ {t}} ^ {X | Y} \| P _ {D _ {t} ^ {W, M}} ^ {X | Y}\right) \right]} \end{array}\tag{11}
$$

We have $\stackrel { ( 1 ) } { = }$ because $P _ { D _ { \epsilon } ^ { W , M } } ^ { Y } = m _ { t - 1 } \sharp P _ { D _ { t - 1 } ^ { W } } ^ { Y } = P _ { D _ { t - 1 } ^ { W } } ^ { Y }$ for $m _ { t - 1 } : \mathcal { X } \to \mathcal { X }$ and $P _ { D _ { t - 1 } ^ { W } } ^ { Y } = P _ { D _ { t } } ^ { Y }$ by (∗). For JS-divergence −1 $\mathcal { D } _ { J S }$ , let $\begin{array} { r } { P _ { D _ { t } ^ { \prime } } ^ { X , Y } = \frac { 1 } { 2 } \left( P _ { D _ { t } } ^ { X , Y } + P _ { D _ { t } ^ { W , M } } ^ { X , Y } \right) } \end{array}$ . Then, we have:

$$
\begin{array}{r l} & {\mathcal {D} _ {J S} \left(P _ {D _ {t}} ^ {X, Y} \parallel P _ {D _ {t} ^ {W, M}} ^ {X, Y}\right)} \\ & {= \frac {1}{2} \mathcal {D} _ {K L} \left(P _ {D _ {t}} ^ {X, Y} \parallel P _ {D _ {t} ^ {\prime}} ^ {X, Y}\right) + \frac {1}{2} \mathcal {D} _ {K L} \left(P _ {D _ {t} ^ {W, M}} ^ {X, Y} \parallel P _ {D _ {t} ^ {\prime}} ^ {X, Y}\right)} \\ & {\overset {(2)} {=} \frac {1}{2} \left(\mathbb {E} _ {P _ {D _ {t}} ^ {Y}} \left[ \mathcal {D} _ {K L} \left(P _ {D _ {t}} ^ {X | Y} \parallel P _ {D _ {t} ^ {\prime}} ^ {X | Y}\right) \right] + \mathbb {E} _ {P _ {D _ {t} ^ {W, M}} ^ {Y}} \left[ \mathcal {D} _ {K L} \left(P _ {D _ {t} ^ {W, M}} ^ {X | Y} \parallel P _ {D _ {t} ^ {\prime}} ^ {X | Y}\right) \right]\right)} \\ & {= \mathbb {E} _ {P _ {D _ {t}} ^ {Y}} \left[ \frac {1}{2} \left(\mathcal {D} _ {K L} \left(P _ {D _ {t}} ^ {X | Y} \parallel P _ {D _ {t} ^ {\prime}} ^ {X | Y}\right) + \mathcal {D} _ {K L} \left(P _ {D _ {t} ^ {W, M}} ^ {X | Y} \parallel P _ {D _ {t} ^ {\prime}} ^ {X | Y}\right)\right) \right]} \\ & {= \mathbb {E} _ {P _ {D _ {t}} ^ {Y}} \left[ D _ {J S} \left(P _ {D _ {t}} ^ {X | Y} \parallel P _ {D _ {t} ^ {W, M}} ^ {X | Y}\right) \right]} \end{array}
$$

We have $\stackrel { ( 2 ) } { = }$ by applying Eq. (11) for $\mathcal { D } _ { K L } \left( P _ { D _ { t } } ^ { X , Y } \parallel P _ { D _ { t } ^ { \prime } } ^ { X , Y } \right)$ and $\mathcal { D } _ { K L } \left( P _ { D _ { t } ^ { W , M } } ^ { X , Y } \parallel P _ { D _ { t } ^ { \prime } } ^ { X , Y } \right)$

## A.2.3 Proof of Proposition 2

First, we show that for any $t \in [ 1 , \cdots , T ]$ , we have:

$$
\mathbb {E} \left[ \mathcal {D} _ {J S} \left(P _ {\widehat {\alpha} _ {t}} ^ {Z} \| P _ {\widehat {\beta} _ {t}} ^ {Z}\right) \right] \leq \mathcal {D} _ {J S} \left(P _ {\alpha_ {t} ^ {*}} ^ {Z} \| P _ {\beta_ {t} ^ {*}} ^ {Z}\right) + \mathcal {O} \left(\left(\frac {1}{\sqrt {n}}\right) \times C (\mathcal {A}, \mathcal {B}, \Gamma)\right)\tag{12}
$$

Proposition 2 is then obtained by applying Eq.( 12) for all $t \in [ 1 , \cdots , T ]$ followed by averaging over t.

Proof of Eq.( 12). To simplify the mathematical notation, we omit the index t in the following. Our proof is based on the proof provided for GAN model by Biau et al. [2020]. Let $\begin{array} { r } { L ( \alpha , \beta , \gamma ) = \int _ { \mathcal Z } \Big ( \log \left( D _ { \gamma } ( z ) \right) P _ { \alpha } ^ { z } + \log \left( 1 - D _ { \gamma } ( z ) \right) P _ { \beta } ^ { z } \Big ) } \end{array}$ dz and $\widehat { L } ( \alpha , \beta , \gamma )$ is the corresponding empirical error, we have:

$$
\begin{array}{l} 2 \mathcal {D} _ {J S} \left(P _ {\widehat {\alpha}} ^ {Z} \parallel P _ {\widehat {\beta}} ^ {Z}\right) = L (\widehat {\alpha}, \widehat {\beta}, \widehat {\gamma}) + \log (4) \\ \qquad \leq \sup _ {\gamma} L (\widehat {\alpha}, \widehat {\beta}, \gamma) + \log (4) \\ \qquad \leq \sup _ {\gamma} \left(\widehat {L} (\widehat {\alpha}, \widehat {\beta}, \gamma) + \left| \widehat {L} (\widehat {\alpha}, \widehat {\beta}, \gamma) - L (\widehat {\alpha}, \widehat {\beta}, \gamma) \right|\right) + \log (4) \\ \qquad \leq \sup _ {\gamma} \widehat {L} (\widehat {\alpha}, \widehat {\beta}, \gamma) + \sup _ {\gamma} \left| \widehat {L} (\widehat {\alpha}, \widehat {\beta}, \gamma) - L (\widehat {\alpha}, \widehat {\beta}, \gamma) \right| + \log (4) \\ \qquad \leq \inf _ {\alpha , \beta} \sup _ {\gamma} \widehat {L} (\alpha , \beta , \gamma) + \sup _ {\alpha , \beta , \gamma} \left| \widehat {L} (\alpha , \beta , \gamma) - L (\alpha , \beta , \gamma) \right| + \log (4) \\ \qquad \leq \inf _ {\alpha , \beta} \sup _ {\gamma} L (\alpha , \beta , \gamma) + \left| \inf _ {\alpha , \beta} \sup _ {\gamma} \widehat {L} (\alpha , \beta , \gamma) - \inf _ {\alpha , \beta} \sup _ {\gamma} L (\alpha , \beta , \gamma) \right| \\ +   \sup _ {\alpha , \beta , \gamma} \left| \widehat {L} (\alpha , \beta , \gamma) - L (\alpha , \beta , \gamma) \right| + \log (4) \\ \qquad^ {(1)}   \leq   \inf _ {\alpha , \beta}   \sup _ {\gamma} L (\alpha , \beta , \gamma) + \sup _ {\alpha , \beta}   \left| \sup _ {\gamma}   \widehat {L} (\alpha , \beta , \gamma) - \sup _ {\gamma} L (\alpha , \beta , \gamma)   \right| \\ +   \sup _ {\alpha , \beta , \gamma}   \left|   \widehat {L} (\alpha , \beta , \gamma) - L (\alpha , \beta , \gamma)   \right| + \log (4) \\ \qquad^ {(2)}   \leq   \inf _ {\alpha , \beta}   \sup _ {\gamma} L (\alpha , \beta , \gamma) + 2   \sup _ {\alpha , \beta , \gamma}   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
    = 2 D _ {J S} (P _ {\alpha^ {*}} ^ {Z} \| P _ {\beta^ {*}} ^ {Z}) + 2   \sup _ {\alpha , \beta , \gamma} |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    .    ..
$$

We have $\begin{array} { l } { { \displaystyle \stackrel { \left( 1 \right) } { \leq } } } \end{array}$ by using inequality | inf A − inf $B | \leq \operatorname* { s u p } | A - B | , \stackrel { ( 2 ) } { \leq }$ by using inequality | sup $A - \operatorname* { s u p } B | \leq \operatorname* { s u p } | A - B |$ Take the expectation and rearrange the both sides, we have:

$$
\begin{array}{r l}&{\mathbb {E} \left[ \mathcal {D} _ {J S} \left(P _ {\widehat {\alpha}} ^ {Z} \parallel P _ {\widehat {\beta}} ^ {Z}\right) \right] - \mathcal {D} _ {J S} \left(P _ {\alpha^ {*}} ^ {Z} \parallel P _ {\beta^ {*}} ^ {Z}\right)}\\&{\leq \mathbb {E} \left[ \sup _ {\alpha , \beta , \gamma} \left| \widehat {L} (\alpha , \beta , \gamma) - L (\alpha , \beta , \gamma) \right| \right]}\\&{= \mathbb {E} \left[ \sup _ {\alpha , \beta , \gamma} \left| \frac {1}{n} \sum_ {i = 1} ^ {n} \log \left(D _ {\gamma} ((z _ {t} ^ {i}))\right) + \frac {1}{n} \sum_ {i = 1} ^ {n} \log \left(1 - D _ {\gamma} (z _ {t + 1} ^ {i})\right) \right. \right.}\\&{\left. - \int_ {\mathcal {Z}} \left(\log \left(D _ {\gamma} (z)\right) P _ {\alpha} ^ {z} + \log \left(1 - D _ {\gamma} (z)\right) P _ {\beta} ^ {z}\right) d z \right| ]}\\&{\leq \mathbb {E} \left[ \right. \sup _ {\alpha , \beta , \gamma} \left| \underbrace {\frac {1}{n} \sum_ {i = 1} ^ {n} \log \left(D _ {\gamma} ((z _ {t} ^ {i}))\right) - \int_ {\mathcal {Z}} (\log (D _ {\gamma} (z)) P _ {\alpha} ^ {z}) d z} _ {A _ {s} (\alpha , \beta , \gamma)} \right| ]}\\&{+ \mathbb {E} \left[ \right. \sup _ {\alpha , \beta , \gamma} \left| \underbrace {\frac {1}{n} \sum_ {i = 1} ^ {n} \log (1 - D _ {\gamma} (z _ {t + 1} ^ {i})) - \int_ {\mathcal {Z}} (\log (1 - D _ {\gamma} (z)) P _ {\beta} ^ {z}) d z} _ {A _ {t} (\alpha , \beta , \gamma)} \right| ]}\end{array}
$$

Note that $\left( A _ { s } \left( \alpha , \beta , \gamma \right) \right) _ { \alpha \in A , \beta \in B , \gamma \in \Gamma }$ and $\left( A _ { t } \left( \alpha , \beta , \gamma \right) \right) _ { \alpha \in A , \beta \in B , \gamma \in \Gamma }$ are the subgaussian processes in the metric spaces $( \mathcal { A } \times \mathcal { B } \times \Gamma , C _ { 1 } \| \cdot \| / \sqrt { n } )$ and $( { \mathcal { A } } \times { \mathcal { B } } \times \Gamma , C _ { 1 } \| { \cdot } \| / { \sqrt { n } } )$ where $C _ { 1 }$ is a constant and $\lVert \cdot \rVert$ is the Euclidean norm on $\boldsymbol { \mathcal { A } } \times \boldsymbol { B } \times \Gamma$ Then using Dudley’s entropy integral, we have:

$$
\begin{array}{l} \mathbb {E} \left[ \mathcal {D} _ {J S} \left(P _ {\widehat {\alpha}} ^ {Z} \parallel P _ {\widehat {\beta}} ^ {Z}\right) \right] - \mathcal {D} _ {J S} \left(P _ {\alpha^ {*}} ^ {Z} \parallel P _ {\beta^ {*}} ^ {Z}\right) \\ \leq \mathbb {E} \left[ \sup _ {\alpha , \beta , \gamma} A _ {s} (\alpha , \beta , \gamma) | | \right] + \mathbb {E} \left[ \sup _ {\alpha , \beta , \gamma} A _ {t} (\alpha , \beta , \gamma) | | \right] \\ \leq 1 2 \int_ {0} ^ {\infty} \left(\sqrt {\log N (\mathcal {A} \times \mathcal {B} \times \Gamma , C \| \cdot \| / \sqrt {n} , \epsilon)} + \sqrt {\log N (\mathcal {A} \times \mathcal {B} \times \Gamma , C \| \cdot \| / \sqrt {n} , \epsilon)}\right) d \epsilon \\ = \frac {2 4 C _ {1}}{\sqrt {n}} \int_ {0} ^ {\infty} \sqrt {\log N (\mathcal {A} \times \mathcal {B} \times \Gamma , \| \cdot \| , \epsilon)} d \epsilon \\ \stackrel {(3)} {=} \frac {2 4 C _ {1}}{\sqrt {n}} \int_ {0} ^ {\mathrm{diam} (\mathcal {A} \times \mathcal {B} \times \Gamma)} \sqrt {\log N (\mathcal {A} \times \mathcal {B} \times \Gamma , \| \cdot \| , \epsilon)} d \epsilon \\ \stackrel {(4)} {\leq} \frac {2 4 C _ {1}}{\sqrt {n}} \int_ {0} ^ {\mathrm{diam} (\mathcal {A} \times \mathcal {B} \times \Gamma)} \sqrt {\log \left(\left(\frac {2 C _ {2} \sqrt {\dim (\mathcal {A} \times \mathcal {B} \times \Gamma)}}{\epsilon}\right) ^ {\dim (\mathcal {A} \times \mathcal {B} \times \Gamma)}\right)} d \epsilon \\ = O \left(\left(\frac {1}{\sqrt {n}}\right) \times C (\mathcal {A}, \mathcal {B}, \Gamma)\right) \end{array}
$$

where diam(·) and dim(·) are the diameter and the dimension of the metric space, and $C ( A , B , \Gamma )$ is the function of (4) diam $( \mathcal { A } \times \mathcal { B } \times \Gamma )$ and dim $( \mathcal { A } \times \mathcal { B } \times \Gamma )$ . We have $\stackrel { \left( 3 \right) } { = }$ because $N ( \mathcal { A } \times \mathcal { B } \times \Gamma , \left. \cdot \right. , \epsilon ) = 1 \mathrm { f o r } \epsilon > \mathrm { d i a m } ( \mathcal { A } \times \mathcal { B } \times \Gamma ) , \overset { \cdot \cdot } { \leq }$ by using inequality $\begin{array} { r } { N ( \mathcal { T } , \| \cdot \| , \epsilon ) \le \left( \frac { 2 C _ { 2 } \sqrt { d } } { \epsilon } \right) ^ { d } } \end{array}$ where $\tau$ lied in Euclidean space $\mathbb { R } ^ { d }$ is the set of vectors whose length is at most $C _ { 2 }$

## B MODEL DETAILS

Our proposed model AIRL consists of three components: (i) encoder Enc that maps inputs to representation (i.e., equivalent to $g _ { t }$ in our theoretical results), (ii) transformer layer Trans that helps to enforce the invariant representation (i.e., Enc + Trans equivalent to $f _ { t }$ in our theoretical results), and (iii) classification network LSTM that generates classifiers mapping representations to the output space. At each target domain, LSTM layer is used to generate the new classifier based on the sequences of previous classifiers. The detailed architectures of these networks used in our experiment are presented in Tables 4 and 5 below.

Table 4: Detailed architecture of AIRL for RMNIST (n\_channel = 1, n\_output = 10), Yearbook (n\_channel = 3, n\_output = 1), and CLEAR (n\_channel = 3, n\_output = 10) datasets.

<table><tr><td>Networks</td><td>Layers</td></tr><tr><td rowspan="12">Representation Mapping G</td><td>Conv2d(input channel = n_channel, output channel = 32, kernel = 3, padding = 1)</td></tr><tr><td>BatchNorm2d</td></tr><tr><td>ReLU</td></tr><tr><td>MaxPool2d</td></tr><tr><td>Conv2d(input channel = 32, output channel = 32, kernel = 3, padding = 1)</td></tr><tr><td>BatchNorm2d</td></tr><tr><td>ReLU</td></tr><tr><td>MaxPool2d</td></tr><tr><td>Conv2d(input channel = 32, output channel = 32, kernel = 3, padding = 1)</td></tr><tr><td>BatchNorm2d</td></tr><tr><td>ReLU</td></tr><tr><td>MaxPool2d</td></tr><tr><td rowspan="7">Transformer Trans</td><td>Q: Linear(input dim = 32, output dim = 32)</td></tr><tr><td>K: Linear(input dim = 32, output dim = 32)</td></tr><tr><td>V: Linear(input dim = 32, output dim = 32)</td></tr><tr><td>U: Linear(input dim = 32, output dim = 32)</td></tr><tr><td>Linear(input dim = 32, output dim = 32)</td></tr><tr><td>Batchnorm1d</td></tr><tr><td>LeakyReLU</td></tr><tr><td rowspan="3">Classification Network LSTM</td><td>Linear(input dim = (32 * 32 + 32) + (32 * n_output + n_output), output dim = 128)</td></tr><tr><td>LSTM(input dim = 128, output dim = 128)</td></tr><tr><td>Linear(input dim = 128, output dim = (32 * 32 + 32) + (32 * n_output + n_output))</td></tr><tr><td rowspan="3"> $\widehat{h}_{t}$ (Output of LSTM)</td><td>Linear(input dim = 32, output dim = 32)</td></tr><tr><td>ReLU</td></tr><tr><td>Linear(input dim = 32, output dim = n_output)</td></tr></table>

Table 5: Detailed architecture of AIRL for Circle and Circle-Hard datasets.

<table><tr><td>Networks</td><td>Layers</td></tr><tr><td rowspan="7">Encoder Enc</td><td>Linear(input dim = 2, output dim = 32)</td></tr><tr><td>ReLU</td></tr><tr><td>Linear(input dim = 32, output dim = 32)</td></tr><tr><td>ReLU</td></tr><tr><td>Linear(input dim = 32, output dim = 32)</td></tr><tr><td>ReLU</td></tr><tr><td>Linear(input dim = 32, output dim = 32)</td></tr><tr><td rowspan="7">Transformer Trans</td><td>Q: Linear(input dim = 32, output dim = 32)</td></tr><tr><td>K: Linear(input dim = 32, output dim = 32)</td></tr><tr><td>V: Linear(input dim = 32, output dim = 32)</td></tr><tr><td>U: Linear(input dim = 32, output dim = 32)</td></tr><tr><td>Linear(input dim = 32, output dim = 32)</td></tr><tr><td>Batchnorm1d</td></tr><tr><td>LeakyReLU</td></tr><tr><td rowspan="3">Classification Network LSTM</td><td>Linear(input dim = (32 * 32 + 32) + (32 * 1 + 1), output dim = 128)</td></tr><tr><td>LSTM(input dim = 128, output dim = 128)</td></tr><tr><td>Linear(input dim = 128, output dim = (32 * 32 + 32) + (32 * 1 + 1))</td></tr><tr><td rowspan="3"> $\widehat{h}_{t}$ (Output of LSTM)</td><td>Linear(input dim = 32, output dim = 32)</td></tr><tr><td>ReLU</td></tr><tr><td>Linear(input dim = 32, output dim = 1)</td></tr></table>

## C DETAILS OF EXPERIMENTAL SETUP AND ADDITIONAL RESULTS

## C.1 EXPERIMENTAL SETUP

Datasets. Our experiments are conducted on two synthetic and two real-world datasets. The data statistics of these datasets are presented in Table 6. For Eval-S scenario, the first half of domains in the domain sequences are used for training and the following domains are used for testing. For Eval-D scenario, we vary the size of the training set starting from the first half of domains by sequentially adding new domains to this set. In both scenarios, we split the training set into smaller subsets with a ratio 81 : 9 : 10; these subsets are used as training, validation, and in-distribution testing sets. The data descriptions are given as follow:

• Circle [Pesaranghader and Viktor, 2016]: A synthetic dataset containing 30 domains. Features $X : = [ X _ { 1 } , X _ { 2 } ] ^ { T }$ in domain t are two-dimensional and Gaussian distributed with mean $\hat { X } ^ { t } = [ r \cos ( \pi t / 3 0 ) , r \sin ( \pi t / 3 0 ) ]$ where r is radius of semicircle; the distributions of different domains have the same covariance matrix but different means that uniformly evolve from right to left on a semicircle. Binary label $Y$ are generated based on labeling function $Y = \mathbb { 1 } \left[ ( X _ { 1 } - x _ { 1 } ^ { o } ) ^ { 2 } + ( X _ { 2 } - \overset { \cdot } { x } _ { 2 } ^ { o } ) ^ { 2 } \leq r \right]$ , where $( x _ { 1 } ^ { o } , x _ { 2 } ^ { o } )$ are center of semicircle. Models trained on the right part are evaluated on the left part of the semicircle.

• Circle-Hard: A synthetic dataset adapted from Circle dataset, where mean ${ \bar { X } } ^ { t }$ does not uniformly evolve. Instead, $\hat { X } ^ { t } = [ r \cos ( \theta _ { t } ) , r \sin ( \theta _ { t } ) ]$ where $\theta _ { t } = \theta _ { t - 1 } + \pi ( t - 1 ) / 1 8 0$ and $\theta _ { 1 } = 0 \mathrm { r a d }$

• RMNIST: A dataset constructed from MNIST [LeCun et al., 1998] by R-degree counterclockwise rotation. We evenly select 30 rotation angles R from $0 ^ { \circ }$ to 180<sup>◦</sup> with step size $6 ^ { \circ }$ ; each angle corresponds to a domain. The domains with $R \leq r$ are considered source domains, those with $R > r$ are the target domains used for evaluation. In this dataset, the goal is to train a multi-class classifier on source domains that predicts the digits of images in target.

• Yearbook [Ginosar et al., 2015]: A real dataset consisting of frontal-facing American high school yearbook photos from 1930-2013. Due to the evolution of fashion, social norms, and population demographics, the distribution of facia images changes over time. In this dataset, we aim to train a binary classifier using historical data to predict the genders of images in the future.

• CLEAR [Lin et al., 2021]: A real dataset built from existing large-scale image collections (YFCC100M) which captures the natural temporal evolution of visual concepts in the real world that spans a decade (2004-2014). In this dataset, we aim to train a multi-class classifier using historical data to predict 10 object types in future images.

Table 6: Data statistics.

<table><tr><td></td><td>Data type</td><td>Label type</td><td>#instance</td><td>#domain</td></tr><tr><td>Circle</td><td>Synthetic</td><td>Binary</td><td>30000</td><td>30</td></tr><tr><td>Circle-Hard</td><td>Synthetic</td><td>Binary</td><td>30000</td><td>30</td></tr><tr><td>RMNIST</td><td>Semi-synthetic</td><td>Multi</td><td>30000</td><td>30</td></tr><tr><td>Yearbook</td><td>Real-world</td><td>Binary</td><td>33431</td><td>84</td></tr><tr><td>CLEAR</td><td>Real-world</td><td>Multi</td><td>29747</td><td>10</td></tr></table>

Non-stationary mechanisms in synthetic datasets. We note that in synthetic datasets, we precisely known the nonstationary mappings that generate domain sequences.

• Circle: A synthetic dataset containing 30 domains. Features $X : = [ X _ { 1 } , X _ { 2 } ] ^ { T }$ in domain t are two-dimensional and Gaussian distributed with mean $\hat { X } ^ { t } = [ r \cos ( \pi t / 3 0 ) , r \sin ( \pi t / 3 0 ) ]$ where r is radius of semicircle; the distributions of different domains have the same covariance matrix but different means that uniformly evolve from right to left on a semicircle. Binary label $Y$ are generated based on labeling function $Y = \mathbb { 1 } \left[ ( X _ { 1 } - x _ { 1 } ^ { \bar { o } } ) ^ { 2 } + ( X _ { 2 } - x _ { 2 } ^ { o } ) ^ { 2 } \leq r \right]$ , where $( x _ { 1 } ^ { o } , x _ { 2 } ^ { o } )$ are center of semicircle.

$$
\Rightarrow \mathbb {m} _ {t} = \left[ \begin{array}{c c} \cos (\pi / 3 0) & - \sin (\pi / 3 0) \\ \sin (\pi / 3 0) & \cos (\pi / 3 0) \end{array} \right] \forall t \in [ 1, \dots , 2 9 ]
$$

• Circle-Hard: A synthetic dataset adapted from Circle dataset, where mean ${ \bar { X } } ^ { t }$ does not uniformly evolve. Instead, $\hat { X } ^ { t } = [ r \cos ( \theta _ { t } ) , r \sin ( \theta _ { t } ) ]$ where $\theta _ { t } = \theta _ { t - 1 } + \pi ( t - 1 ) / 1 8 0$ and $\theta _ { 1 } = 0 \mathrm { r a d }$

$$
\Rightarrow \mathbb {m} _ {t} = \left[ \begin{array}{c c} \cos (\pi t / 1 8 0) & - \sin (\pi t / 1 8 0) \\ \sin (\pi t / 1 8 0) & \cos (\pi t / 1 8 0) \end{array} \right] \forall t \in [ 1, \dots , 1 9 ]
$$

• RMNIST: A dataset constructed from MNIST by R-degree counterclockwise rotation. We evenly select 30 rotation angles R from $0 ^ { \circ } \mathrm { ~ t o ~ } 1 8 0 ^ { \circ }$ with step size $6 ^ { \circ }$ ; each angle corresponds to a domain.

$$
\Rightarrow \mathfrak {m} _ {t} = \left[ \begin{array}{c c} \cos (6 ^ {\circ}) & - \sin (6 ^ {\circ}) \\ \sin (6 ^ {\circ}) & \cos (6 ^ {\circ}) \end{array} \right] \forall t \in [ 1, \dots , 2 9 ]
$$

Baseline methods. We compare the proposed AIRL with existing methods from related areas, including the followings:

• Empirical risk minimization (ERM): A simple method that considers all source domains as one domain.

• Last domain (LD): A method that only trains model using the most recent source domain.

• Fine tuning (FT): The baseline trained on all source domains in a sequential manner.

• Domain invariant representation learning: Methods that learn the invariant representations across source domains and train a model based on the representations. We experiment with G2DM [Albuquerque et al., 2019], DANN [Ganin et al., 2016], CDANN [Li et al., 2018b], CORAL [Sun and Saenko, 2016], IRM [Arjovsky et al., 2019].

• Data augmentation: We experiment with MIXUP [Zhang et al., 2018] that generates new data using convex combinations of source domains to enhance the generalization capability of models.

• Continual learning: We experiment with EWC [Kirkpatrick et al., 2017], method that learns model from data streams that overcomes catastrophic forgetting issue.

• Continuous domain adaptation: We experiment with CIDA [Wang et al., 2020], an adversarial learning method designed for DA with continuous domain labels.

• Distributionally robust optimization: We experiment with GROUPDRO [Sagawa et al., 2019] that minimizes the worst-case training loss over pre-defined groups through regularization.

• Gradient-based DG: We experiment with FISH [Shi et al., 2022] that targets domain generalization by maximizing the inner product between gradients from different domains.

• Contrastive learning-based DG: We experiment with SELFREG [Kim et al., 2021] that utilizes the self-supervised contrastive losses to learn domain-invariant representation by mapping the latent representation of the same-class samples close together.

• Non-stationary environment DG: We experiment with DRAIN [Bai et al., 2022], TKNets [Zeng et al., 2024b], LSSAE [Qin et al., 2022]. and DDA [Zeng et al., 2023]. DRAIN, DPNET, and DDA focus on domain $D _ { T + 1 }$ only so we use the same model when making predictions for all target domains $\{ D _ { t } \} _ { t > T }$

Evaluation method. In the experiments, models are trained on a sequence of source domains $\mathcal { D } _ { s r c } .$ and their performance is evaluated on target domains $\mathcal { D } _ { t g t }$ under two different scenarios: Eval-S and Eval-D.

In the scenario Eval-S, models are trained one time on the first half of domain sequence $\mathcal { D } _ { s r c } = [ D _ { 1 } , D _ { 2 } , \cdot \cdot \cdot , D _ { T } ]$ and are then deployed to make predictions on the next K domains in the second half of domain sequence $\begin{array} { r } { \mathcal { D } _ { t g t } \ = } \end{array}$ $\left[ D _ { T + 1 } , D _ { T + 2 } , \cdot \cdot \cdot , D _ { T + K } \right] \left( T + 1 \leq K \leq 2 T \right)$ . The average and worst-case performances can be evaluated using two matrices $\mathrm { O O D } _ { \mathrm { A v g } }$ and $\mathrm { O O D } _ { \mathrm { W r t } }$ defined below.

$$
\mathrm{OOD} _ {\text { Avg }} = \frac {1}{K} \sum_ {k = 1} ^ {K} \operatorname{acc} _ {T + k}; \quad \mathrm{OOD} _ {\text { Wrt }} = \min _ {k \in [ K ]} \operatorname{acc} _ {T + k}
$$

where $\mathrm { a c c } _ { T + k }$ denotes the accuracy of model on target domain $D _ { T + k }$

In the scenario Eval-D, source and target domains are not static but are updated periodically as new data/domain becomes available. This allows us to update models based on new source domains. Specifically, at time step $t \in [ T , 2 T - K ]$ models are updated on source domains $\mathcal { D } _ { s r c } = [ D _ { 1 } , D _ { 2 } , \cdot \cdot \cdot , D _ { t } ]$ and are used to predict target domains $\begin{array} { r l } { \mathcal { D } _ { t g t } } & { { } = } \end{array}$ $[ D _ { t + 1 } , D _ { t + 2 } , \cdot \cdot \cdot , D _ { t + K } ]$ . The average and worst-case performances of models in this scenario can be defined as fol lows.

$$
\mathrm{OOD} _ {\mathrm{Avg}} = \frac {1}{(T - K + 1) K} \sum_ {t = T} ^ {2 T - K} \sum_ {k = 1} ^ {K} \mathrm{acc} _ {t + k}
$$

$$
\mathrm{OOD} _ {\mathrm{Wrt}} = \min _ {t \in [ T, 2 T - K ]} \frac {1}{K} \sum_ {k = 1} ^ {K} \mathrm{acc} _ {t + k}
$$

In our experiment, the time step t starts from the index denoting half of the domain sequence.

Table 7: Performances of DANN on RMNIST dataset.

<table><tr><td>Target Domain</td><td> $0^{\circ}$ -rotated</td><td> $15^{\circ}$ -rotated</td><td> $30^{\circ}$ -rotated</td><td> $45^{\circ}$ -rotated</td><td> $60^{\circ}$ -rotated</td></tr><tr><td>Model Performance</td><td>51.2</td><td>59.1</td><td>70.0</td><td>69.2</td><td>53.9</td></tr></table>

Table 8: The average training times (i.e., seconds) of non-stationary DG methods for Circle,Circle-Hard, RMNIST Yearbook, and CLEAR datasets.

<table><tr><td></td><td>Circle</td><td>Circle-Hard</td><td>RMNIST</td><td>Yearbook</td><td>CLEAR</td></tr><tr><td>AIRL</td><td>32</td><td>25</td><td>382</td><td>749</td><td>1504</td></tr><tr><td>LSSAE</td><td>184</td><td>175</td><td>1727</td><td>1850</td><td>13287</td></tr><tr><td>DRAIN</td><td>460</td><td>230</td><td>2227</td><td>5538</td><td>1920</td></tr><tr><td>TKNets</td><td>18</td><td>13</td><td>208</td><td>448</td><td>1542</td></tr></table>

Implementation and training details. Data, model implementation, and training script are included in the supplementary material. We train each model on each setting with 5 different random seeds and report the average prediction performances. All experiments are conducted on a machine with 24-Core CPU, 4 RTX A4000 GPUs, and 128G RAM.

## C.2 ADDITIONAL EXPERIMENT RESULTS

Performance gap between in-distribution and out-of-distribution predictions. This study is motivated based on the assumption that the environment changes over time and that there exist distribution shifts between training and test data. To verify this assumption in our datasets, we compare the performances of ERM on in-distribution and out-of-distribution testing sets. Specifically, we show the gaps between the performances of ERM measured on the in-distribution $( \mathrm { i . e . , I D _ { A v g } ) }$ and out-of-distribution $( \mathrm { i . e . , O O D _ { A v g } ) }$ testing sets under Eval-D scenario (i.e., K = 5) in Figure 5.

Performance of fixed invariant representation learning in conventional and non-stationary DG settings. A key distinction from non-stationary DG is that the model evolves over the domain sequence to capture non-stationary patterns (i.e., learn invariant representations between two consecutive domains but adaptive across domain sequence). This stands in contrast to the conventional DG [Ganin et al., 2016, Phung et al., 2021] which relies on an assumption that target domains lie on or are near the mixture of source domains, then enforcing fixed invariant representations across all source domains can help to generalize the model to target domains. We argue that this assumption may not hold in non-stationary DG where the target domains may be far from the mixture of source domains resulting in the failure of the existing methods.

To verify this argument, we conduct an experiment on rotated RMNIST dataset with DANN [Ganin et al., 2016] – a mode that learns fixed invariant representations across all domains. Specifically, we create 5 domains by rotating images by 0, 15, 30, 45, and 60 degrees, respectively, and follow leave-one-out evaluation (i.e., one domain is target while the remaining domains are source). Clearly, the setting where the target domain are images rotated by 0 or 60 degrees can be considered as non-stationary domain generalization while other settings can be considered as conventional domain generalization. The performances of DANN with different target domains are shown in Table 7. As we can see, the accuracy drops significantly when the target domain are images rotated by 0 or 60 degrees. This result demonstrates that learning fixed invariant representations across all domains is not suitable for non-stationary DG.

Computation complexity of non-stationary DG methods. Compared to existing works for non-stationary DG, our method also shows better computational efficiency. It’s because of our effective design to capture non-stationary patterns. Specifically, LSSAE and DRAIN have more complex architectures and objective functions resulting in much more training time than our method. While TKNets has slightly better training time than ours, this model requires storing previous data to make predictions and is not generalized to multiple target domains. To further support our claim, the average training times (i.e., seconds) of these methods for different datasets are shown in Table 8.

Experimental results for Eval-S scenario. The prediction performances of AIRL and baselines on synthetic (i.e., Circle, Circle-Hard) and real-world (i.e., RMNIST, Yearbook) data under Eval-S scenario are presented in Figure 6 below. In this scenario, the training set is fixed as the first half of domains while the testing set is varied from the five subsequent domains to the second half of domains in the domain sequences. We report averaged results with error bars (std) for training over 5 different random seeds.

![](images/1d4859bdcfd62e0a97f728685f71e869fb4e099dab7c77cf70301a7a6c87046a.jpg)  
(a) Circle

![](images/c8c139e372e54ea09279b45a73cc1384def423c7f25ead457e6a5dbcdda8b682.jpg)  
(b) Circle-Hard

![](images/317f63a767699a1514225b2837f3983fae31d8bb2989173bc01486c8c2ee42ec.jpg)  
(c) RMNIST

![](images/3cb5a419f61f101942a0ed03fd7048c2b2d3388357325067cb3336e48474a6e3.jpg)  
(d) Yearbook  
Figure 5: Gaps between the performances of ERM measured on the in-distribution and out-of-distribution testing sets (i.e., $\mathrm { I D } _ { \mathrm { A v g } } - \mathrm { O O D } _ { \mathrm { A v g } } )$ under Eval-D scenario (i.e., K = 5). This experiment is conducted on Circle, Circle-Hard, RMNIST, and Yearbook datasets.

We can see that AIRL consistently outperforms baselines in most datasets. We also observe that the prediction performances decreases when the predictions are made for the distant target domains (i.e., the number of testing domain increases) for al models in Circle, Circle-Hard, and RMNIST datasets. This pattern is reasonable because domains in these datasets are generated monotonically. For Yearbook dataset, the performance curves are U-shaped that they decrease first but increase later. This dataset is from a real-world environment so we expect the shapes of the curves are more complex compared to those in the other datasets.

<table><tr><td>ERM</td><td>G2DM</td><td>MIXUP</td><td>CIDA</td><td>DRAIN</td><td>SELFREG</td></tr><tr><td>DANN</td><td>CORAL</td><td>IRM</td><td>LD</td><td>LSSAE</td><td>DDA</td></tr><tr><td>CDANN</td><td>GROUPDRO</td><td>EWC</td><td>FT</td><td>FISH</td><td>AIRL</td></tr></table>

![](images/09de4715808d3dd44b68c6d2bc12d31705badac7b6c9fce600ffe06edffaef5a.jpg)  
(a) Circle

<table><tr><td>ERM</td><td>G2DM</td><td>MIXUP</td><td>CIDA</td><td>DRAIN</td><td>SELFREG</td></tr><tr><td>DANN</td><td>CORAL</td><td>IRM</td><td>LD</td><td>LSSAE</td><td>DDA</td></tr><tr><td>CDANN</td><td>GROUPDRO</td><td>EWC</td><td>FT</td><td>FISH</td><td>AIRL</td></tr></table>

![](images/a615a238cdb548a97147c0427398eb3122ceb096eb19d7b6ef34ea6a8f75b21d.jpg)  
(b) Circle-Hard

<table><tr><td>ERM</td><td>G2DM</td><td>MIXUP</td><td>CIDA</td><td>DRAIN</td><td>SELFREG</td></tr><tr><td>DANN</td><td>CORAL</td><td>IRM</td><td>LD</td><td>LSSAE</td><td>DDA</td></tr><tr><td>CDANN</td><td>GROUPDRO</td><td>EWC</td><td>FT</td><td>FISH</td><td>AIRL</td></tr></table>

![](images/f519696aa415390322f13c7f72cf0c23d8c8a0208fc3b9c6e9d5b983cb112f34.jpg)  
(c) RMNIST

<table><tr><td>ERM</td><td>G2DM</td><td>MIXUP</td><td>CIDA</td><td>DRAIN</td><td>SELFREG</td></tr><tr><td>DANN</td><td>CORAL</td><td>IRM</td><td>LD</td><td>LSSAE</td><td>DDA</td></tr><tr><td>CDANN</td><td>GROUPDRO</td><td>EWC</td><td>FT</td><td>FISH</td><td>AIRL</td></tr></table>

![](images/0a933cc28f58f0675002554fbe1a996d9d87b88edae7262f885c5655ae075290.jpg)  
(d) Yearbook  
Figure 6: Prediction performances $( \mathrm { i . e . , O O D _ { A v g } ) }$ of AIRL and baselines under Eval-S scenario. The training set is fixed as the first half of domains while the testing set is varied from the five subsequent domains to the second half of domains in the domain sequences. We report average results for training over 5 different random seeds. This experiment is conducted on Circle, Circle-Hard, RMNIST, and Yearbook datasets.