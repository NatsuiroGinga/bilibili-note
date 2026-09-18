---
title: "2025-Su-RTTDP-Realistic-Test-Time-Poisoning"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2025-Su-RTTDP-Realistic-Test-Time-Poisoning.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# ON THE ADVERSARIAL RISK OF TEST TIME ADAPTA-TION: AN INVESTIGATION INTO REALISTIC TEST-TIME DATA POISONING

Yongyi Su<sup>1,4∗</sup>, Yushu Li<sup>1,4∗</sup>, Nanqing Liu<sup>2,4</sup>, Kui Jia<sup>3</sup>, Xulei Yang<sup>4</sup>, Chuan-Sheng Foo<sup>4</sup>, Xun Xu<sup>4†</sup> <sup>1</sup>South China University of Technology

<sup>2</sup>Southwest Jiaotong University

<sup>3</sup>The Chinese University of Hong Kong, Shenzhen

<sup>4</sup>Institute for Infocomm Research (I<sup>2</sup>R), A\*STAR

{eesuyongyi, eeyushuli}@mail.scut.edu.cn

lansing163@163.com, kuijia@cuhk.edu.cn

{yang\_xulei, foo\_chuan\_sheng, xu\_xun}@i2r.a-star.edu.sg

## ABSTRACT

Test-time adaptation (TTA) updates the model weights during the inference stage using testing data to enhance generalization. However, this practice exposes TTA to adversarial risks. Existing studies have shown that when TTA is updated with crafted adversarial test samples, also known as test-time poisoned data, the performance on benign samples can deteriorate. Nonetheless, the perceived adversarial risk may be overstated if the poisoned data is generated under overly strong assumptions. In this work, we first review realistic assumptions for test-time data poisoning, including white-box versus grey-box attacks, access to benign data, attack order, and more. We then propose an effective and realistic attack method that better produces poisoned samples without access to benign samples, and derive an effective in-distribution attack objective. We also design two TTA-aware attack objectives. Our benchmarks of existing attack methods reveal that the TTA methods are more robust than previously believed. In addition, we analyze effective defense strategies to help develop adversarially robust TTA methods. The source code is available at https://github.com/Gorilla-Lab-SCUT/RTTDP.

## 1 INTRODUCTION

Test-time adaptation (TTA) emerges as an effective measure to counter distribution shift at inference stage (Wang et al., 2020; Su et al., 2022; Zhong et al., 2022; Chen et al., 2023; Chi et al., 2024; Wu et al., 2024). Successful TTA methods leverage the testing data samples for self-training (Wang et al., 2020; Su et al., 2024b), distribution alignment (Liu et al., 2021; Su et al., 2022) or prompt tuning (Gao et al., 2022; Liu et al., 2025). Despite the continuing efforts into developing computation efficient and high caliber TTA approaches, the robustness of TTA methods has not picked up until recently, leading to studies examining the robustness of TTA methods under constant distribution shift (Song et al., 2023), correlated testing data stream (Su et al., 2024a; Niu et al., 2023), open-world testing data (Li et al., 2023), adversarial robustness (Wu et al., 2023; Cong et al., 2023), etc. Among these risks, adversarial vulnerability warrants particular attention due to its potential for evading human inspection and the significant consequences of admitting malicious samples during TTA.

Existing research frames the adversarial risk of Test-Time Adaptation (TTA) as the crafting of poisoned testing data, resulting in models updated with such data performing poorly on clean testing samples (Wu et al., 2023; Cong et al., 2023). Consequently, this task is also referred to as Test-Time Data Poisoning (TTDP). The pioneering work DIA (Wu et al., 2023) introduced a poisoning approach by crafting malicious data with access to all benign samples within a minibatch, leveraging realtime model weights for explicit gradient computing, i.e., a white-box attack. Another concurrent study (Cong et al., 2023) implements poisoning by preemptively injecting all poisoned data to attack the model even before TTA starts. While these explorations conclude that TTA methods are susceptible to poisoned data, evaluations based on unrealistic assumptions may exaggerate the adversarial risk for several reasons. i) Access to real-time model weights (white-box attack) is often considered overly optimistic, especially given that models are constantly updated during adaptation. Therefore, a grey-box or even black-box attack is preferred for TTDP. ii) The adversary is typically assumed only to be aware of the query samples submitted by themselves. Thus, benign samples submitted by other users should not be utilized for crafting poisoned data, for instance, through bi-level optimization (Wu et al., 2023). iii) Crafting poisoned data requires querying the model with testing samples (Wu et al., 2023). Repeatedly querying the model from a single user could easily trigger alerts in defensive systems. Therefore, any query sample, whether adversarial or benign, should be counted towards the attack budget. iv) Following the above concern, the adversary should not monopolize the entire testing bandwidth. This constraint translates to a scenario where poisoned data only partially occupies the testing stream, and the adversary is not allowed to inject all poisoned data at once even before TTA starts (Cong et al., 2023).

To the best of our knowledge, existing attempts at test-time poisoning have not fully addressed the above realistic concerns. In this work, we aim to propose a threat model that advances towards more Realistic Test-Time Data Poisoning (RTTDP). Firstly, we formulate the threat model under a grey-box attack scenario, where initial model weights are visible. We distill a simple surrogate model from the online model using only the adversary’s queries, enabling efficient gradient-based synthesis of poisoned data. Empirical analysis demonstrates that the distilled surrogate provides sufficient information for crafting effective poisoned data. Moreover, to constrain the attack budget, we reformulate the bi-level optimization objective proposed in prior work (Wu et al., 2023) by replacing benign samples with poisoned data only. Through reasoning on generalization error, we illustrate that the attack loss defined on poisoned data can be generalized to benign samples if the distributions between poisoned and benign samples are identical. This insight motivates us to introduce a feature distribution consistency regularization for in-distribution attacks, eliminating the need for additional benign samples to construct the outer objective. Finally, we devise two alternative attack objectives tailored to the unique features of Test-Time Adaptation (TTA) methods. We first propose a high-entropy oriented attack to generate poisoned samples biased towards high entropy. This approach proves effective in compromising TTA methods based on entropy minimization (Wang et al., 2020). However, high-entropy attacks may become less effective with the introduction of simple defense techniques, such as confidence thresholding. Therefore, we explore a low-entropy based attack objective aimed at attacking towards a non-ground-truth class. The combined threat model is applied to a diverse range of TTA methods, resulting in more effective outcomes compared to existing threat models. An overview of the overall framework is presented in Figure 1.

In addition to crafting effective threat models, we delve into exploring practices conducive to enhancing Test-Time Adaptation (TTA)’s adversarial robustness. Contrary to the reliance on adversarially trained models (Madry et al., 2018) and robust batch normalization estimation (Wu et al., 2023), we draw inspiration from empirical observations of robust TTA methods. Our validation reveals that confidence thresholding, data augmentation, exponential moving averaging (EMA), and random parameter restoration represent potential directions for improving the adversarial robustness of TTA methods.

We summarize the contributions of this work as follows.

• We argue the unrealistic assumptions, e.g. white-box attack, access to benign subset and offline attack order, made in existing attempts at TTDP may overestimate the adversarial risk of TTA methods. To address this, we first propose key criteria for defining realistic test-time data poisoning scenarios.

• Under our proposed realistic test-time protocol, we analyze the generalization error and introduce an in-distribution attack strategy with feature consistency regularization. This strategy eliminates the need for additional benign samples in evaluating the outer objective. In addition, we tailor attack objectives specifically for TTA methods, resulting in more effective poisoning.

• We perform extensive evaluations on state-of-the-art TTA methods, demonstrating the efficacy of our proposed in-distribution attack strategy. Furthermore, we identify certain practices that are conducive to improving realistic adversarial robustness.

![](images/3e2a4528525a794d818edf1c321c8f7b35ba16577b4dd95f72f1e540c9dfdef1.jpg)  
Figure 1: Illustration of the proposed Realistic Test-Time Data Poisoning (RTTDP) pipeline. $\boldsymbol { B } _ { a b }$ indicates the adversary benign subset, and $B _ { a }$ indicates the adversary poisoned subset where the samples are poisoned from the clean samples in $\boldsymbol { B } _ { a b } . \ \boldsymbol { B _ { b } }$ indicates the benign users’ subset where the samples are used to validate the adversarial risk of TTA pipeline and these samples cannot be access by the adversary. Adversary generates poisoned data by attacking a regularized objective without accessing benign samples from other users. Model is attacked when carrying out TTA on testing data stream mixed with benign and poisoned data.

## 2 RELATED WORK

Test-Time Adaptation (TTA): Wang et al. (2020; 2022); Niu et al. (2022); Su et al. (2022); Li et al. (2023); Liang et al. (2024); Wu et al. (2024) and Wang et al. (2025) have shown significant success in bridging the domain gap by using stream-based testing samples to dynamically update models in real time. The success of TTA is mainly attributed to the self-supervised learning on testing data. While it has proved sensitive to confirmation bias (Arazo et al., 2020), many solutions were proposed to minimize the influences of the wrong pseudo-labels, including minimizing sample entropy (Wang et al., 2020; Liang et al., 2020), adding regularization terms (Song et al., 2023; Su et al., 2024b), using confidence thresholding (Niu et al., 2022; 2023), updating models with exponential moving average architectures (Wang et al., 2022; Döbler et al., 2023), partially updating model weights (Wang et al., 2020; Yuan et al., 2023), and augmenting testing samples (Zhang et al., 2022; Döbler et al., 2023), all aimed at minimizing sample distribution discrepancies. However, adaptation during the testing stage remains highly risky. In this work, we aim to investigate the risk of TTA posed by data poisoning.

Robustness in Test-Time Adaptation: Recent research has increasingly focused on the robustness of TTA in realistic deployments. Wang et al. (2022) and Brahma & Rai (2023) tackle issues of catastrophic forgetting due to changing test data distributions. Niu et al. (2023), Gong et al. (2022) and Yuan et al. (2023) address non-i.i.d. and shifting label distributions in test data. Li et al. (2023) and Zhou et al. (2023) introduce open-world scenarios in TTA, where test data may include novel classes not present in the source domain. Furthermore, Wu et al. (2023) and Cong et al. (2023) investigate the threat of data poisoning in TTA, where attackers alter test data to exploit vulnerabilities in TTA methods. DIA (Wu et al., 2023) uses bi-level optimization to degrade target sample performance, assuming white-box attack access. In contrast, TePA (Cong et al., 2023) includes an exclusive offline stage for poisoning data on the source model prior to the TTA process. Inspired by these works, we focus on the severe threat of data poisoning. We examine the adversarial robustness of TTA under realistic conditions, with access only to the source model and partial test samples for data poisoning. Our attack, despite these constraints, outperforms previous methods, highlighting the significant adversarial risks that TTA methods face.

Adversarial Attack & Data Poisoning: Adversarial risk is a crucial concern for models to address for safe deployment, which can be divided into two categories: adversarial attacks and data poisoning. Adversarial attacks (Szegedy et al., 2014; Akhtar & Mian, 2018; Goodfellow et al., 2014; Madry et al., 2018; Croce & Hein, 2020; Chen et al., 2022; Chakraborty et al., 2018) manipulate models during inference by adding small perturbations to input data. White-box attacks (Szegedy et al., 2014; Tramèr et al., 2018) assume full access to the victim model, creating adversarial examples by maximizing loss gradients. In contrast, grey-box attacks (Chen et al., 2017; Ilyas et al., 2018; Ru et al., 2019) assume no model access, generating adversarial samples by estimating gradients through intensive querying. Data poisoning (Biggio et al., 2012; Yang et al., 2017; Shafahi et al., 2018; Alfeld et al., 2016; Huang et al., 2021; Fowl et al., 2021; Fan et al., 2022) compromises models by injecting manipulated data into the training set, misleading the training process. Traditional data poisoning assumes that the attacker can observe and poison the entire training set at once. Recently, online poisoning (Zhang et al., 2020) relaxes this assumption by requiring knowledge of the model updating strategies. In this work, we explore a more realistic scenario of TTA’s adversarial robustness, focusing on data poisoning without online model access and without multiple queries for the same data.

## 3 SETTING: REALISTIC TEST-TIME DATA POISONING

## 3.1 OVERVIEW OF TEST-TIME DATA POISONING

We first provide a generic overview of test-time adaptation for a K-way classification task. We denote the testing data as $\mathcal { D } = \{ x _ { i } \} _ { i = 1 } ^ { N _ { t } }$ and a pre-trained model as $\theta _ { 0 }$ . TTA methods often employ unsupervised loss, $\mathcal { L } _ { t t a }$ , to update model parameters upon observing a minibatch of testing samples $\boldsymbol { B } _ { t } = \{ x _ { i } \} _ { i = 1 } ^ { N _ { b } }$ at timestamp t. Usually, a subset of model parameters $\theta _ { t } ^ { u } \subseteq \theta _ { t }$ is subject to update at timestamp t, and we denote the BN statistics as $\theta ^ { b } ( \mathcal { B } _ { t } ) = \{ \mu ( \mathcal { B } _ { t } ) , \sigma ^ { 2 } ( \mathcal { \bar { B _ { t } } } ) \}$ and the frozen parameters as $\theta ^ { f }$ . The posterior of the sample $x _ { i }$ towards the model parameter θ is $h ( x _ { i } ; \theta ) \in [ 0 , 1 ] ^ { K }$ . The adversarial risk arises when a subset of testing samples are poisoned, $\mathrm { e . g }$ . through adding an adversarial noise $\tilde { x } = x + \epsilon , \ s . t . \ \lVert \epsilon \rVert _ { \infty } \leq b .$ The model trained on poisoned data exhibit poor performance on clean/benign testing samples. In a typical TTA scenario, the online model is queried by both adversary and benign users. Thus, we denote the query data from adversary as adversary poisoned subset $\boldsymbol { B _ { a } } = \{ \tilde { x } _ { i } \}$ . The poisoned subset could be generated from arbitrary clean testing data, denoted as ${ B _ { a b } = \{ x _ { i } \} }$ (e.g. use any public clean images). The generation follows an additive noise, i.e. $\tilde { x } _ { i } = x _ { i } + \epsilon _ { i } , \ \tilde { s . t . } \ \tilde { x } _ { i } \in \mathcal { B } _ { a } \ x _ { i } \in \mathcal { B } _ { a b }$ , where the noise $\epsilon _ { i }$ is the data poisoning to be learned. The query data from benign users is denoted as benign subset $\boldsymbol { B _ { b } } = \{ \boldsymbol { x } _ { i } \}$ , where ${ \cal B } _ { a b } \cap { \cal B } _ { b } = \emptyset$ Generally, we form the combination of both, $B _ { t } \ = \ \mathsf { B } _ { a } \cup B _ { b }$ , as a single TTA minibatch. The effectiveness of test-time poisoning is evaluated at the attack success rate (classification error) on benign subset $B _ { b }$ . An illustration of batch split is presented in the Appendix A.1.1.

## 3.2 REALISTIC TEST-TIME DATA POISONING PROTOCOL

The adversarial risk of TTA methods must be assessed under realistic attacks. Existing works may have exaggerated the adversarial risk when attack is implemented under an overly strong assumption. We summarize the criteria that define a more realistic attack as follows.

White-Box v.s. Grey-Box Attack: Access to real-time TTA model parameters is a key factor for crafting realistic test-time data poisoning. Contrary to the assumption adopted by white-box adversarial attack (Szegedy et al., 2014; Biggio et al., 2013) that a frozen model is deployed for inference, the TTA model parameters experience constant updating at inference stage. The update is performed on the cloud side, thus the attacker doesn’t normally have access to real-time model weights. Such a realistic assumption prompts us to explore a more relaxed grey-box test-time data poisoning, i.e. only the model architecture and initial model weights are available to the adversary, such as the open-source famous pre-trained models (He et al., 2016; Dosovitskiy et al., 2021) and popular foundation models (Radford et al., 2021; Kirillov et al., 2023; Oquab et al., 2024).

Access To Benign Subset: The effectiveness of TTDP is evaluated on the benign subset $B _ { b }$ submitted by benign users. In a standard cloud service, users are generally restricted from accessing the queries of other users. Thus the adversary should only have access to adversary subset $\scriptstyle B _ { a } .$ . This assumption prohibits the practice of crafting poisoned data by directly optimizing (minimizing) the loss on benign subset (Wu et al., 2023), on which the attack success rate (performance) is calculated.

Attack Order: Finally, attacking TTA model in a realistic way should be implemented during the adaptation stage. Attacking the model before TTA begins is deemed less practical (Cong et al., 2023).

Based on the aforementioned key criteria, we provide a summary of existing test-time data poisoning methods in Tab. 1. Our analysis indicates that none of the current methods fully satisfy all the estab lished criteria. Specifically, DIA (Wu et al., 2023) employs a white-box attack strategy, generating poisoned samples by maximizing the error rate on a subset of benign data. TePA (Cong et al., 2023) attacks the pre-trained model with an offline surrogate model prior to the commencement of test-time adaptation. In the rest of the paper, we stick to the most realistic assumptions, i.e. online grey-box poisoning and no access to benign subset, named as Realistic Test-Time Data Poisoning (RTTDP).

Table 1: Taxonomy of methods based on the criteria for realistic test-time data poisoning.

<table><tr><td>Setting</td><td>Grey-box v.s. White-box</td><td>Access to Benign Subset</td><td>Attack Order</td></tr><tr><td>DIA (Wu et al., 2023)</td><td>White-box</td><td>√</td><td>Online</td></tr><tr><td>TePA (Cong et al., 2023)</td><td>Grey-box</td><td>✕</td><td>Offline</td></tr><tr><td>RTTDP (Ours)</td><td>Grey-box</td><td>✕</td><td>Online</td></tr></table>

Adversarial Attacks on Standard Image Classification: Common grey-box or black-box adversarial attack techniques are often impractical for RTTDP due to two primary challenges. First, existing adversarial attack methods operate on a static model and inherently require multiple queries for gradient approximation or fitness evaluation, as seen in query-based attacks (Li et al., 2020; Xu et al., 2021), genetic algorithms (Chen et al., 2019), and black-box optimization (Qiu et al., 2021). However, in the test-time adaptation setting, the online model is continuously updated with each query during the inference phase. Thus, repetitive querying the model for gradient approximation or fitness evaluation is unavailable. Second, traditional adversarial attack methods focus on crafting adversarial samples to degrade the performance of the attacker’s own input data. In contrast, in a realistic test-time data poisoning scenario, poisoned samples are introduced into the test-time adaptation process to degrade the performance of benign samples submitted by other users.

## 4 METHODOLOGY

## 4.1 GREY-BOX ATTACK BY SURROGATE MODEL DISTILLATION

To tackle the challenge of access to TTA model parameters, we propose to maintain a surrogate model, denoted as $\widehat { \theta } _ { t }$ at timestamp t, for the purpose of synthesizing poisoned data. To ensure good approximation, we distill the target model $\theta _ { t }$ into the surrogate model $\widehat { \theta } _ { t }$ by leveraging the feedback of poisoned data from the online target model. Specifically, for each query to the target model, we minimize the symmetric KL-Divergence between the posteriors of the target and surrogate models, as Eq. 1. Our empirical observations demonstrate that utilizing the adversarial subset $B _ { a }$ for distillation yields performance comparable to a white-box attack, as illustrated in Fig. 2 (a).

$$
\mathcal {L} _ {d i s t} = \frac {1}{| \mathcal {B} _ {a} |} \sum_ {x _ {i} \in \mathcal {B} _ {a}} \frac {1}{2} \left[ K L D \left(h (x _ {i}; \theta_ {t}) | | h (x _ {i}; \hat {\theta} _ {t})\right) + K L D \left(h (x _ {i}; \hat {\theta} _ {t} | | h (x _ {i}; \theta_ {t}))\right) \right]\tag{1}
$$

## 4.2 IN-DISTRIBUTION TEST-TIME DATA POISONING

In this section, we further address the challenge of attacking TTA model without access to benign user’s testing samples. In the first place, we revisit DIA (Wu et al., 2023), which formulated test-time poisoned data generation as a bi-level optimization problem, in Eq. 2.

$$
\begin{array}{l} \min _ {\mathcal {B} _ {a}} \frac {1}{| \mathcal {B} _ {b} |} \sum_ {x _ {i} \in \mathcal {B} _ {b}} \mathcal {L} _ {a t k} \left(x _ {i}; \theta_ {t} ^ {*} (\mathcal {B} _ {t})\right) \\ s. t.   \mathcal {B} _ {t} = \mathcal {B} _ {a} \cup \mathcal {B} _ {b};    \theta^ {b \prime} = \{\mu (\mathcal {B} _ {t}), \sigma^ {2} (\mathcal {B} _ {t}) \}; \\ \theta_ {t} ^ {u *} = \arg \min _ {\theta^ {u}} \mathcal {L} _ {t t a} (\mathcal {B} _ {t}; \theta_ {t} ^ {*} (\mathcal {B} _ {t}));   \theta_ {t} ^ {*} (\mathcal {B} _ {t}) = \theta_ {t} ^ {u *} \cup \theta^ {b \prime} \cup \theta^ {f} \end{array}\tag{2}
$$

The above bi-level optimization problem employed in DIA (Wu et al., 2023) aims to generate adversarially poisoned data $B _ { a }$ by minimizing the loss function $\mathcal { L } _ { a t k }$ , which is computed on the benign samples $B _ { b }$ . Although DIA approximates $\theta _ { t } ^ { u * } \approx \theta _ { t } ^ { u }$ to discard the inner TTA gradient update loop and reduce the number of queries to the online model, several realistic concerns still persist under the RTTDP protocol. First, as discussed in Sec. 3.2, DIA, as a white-box attack method, must query the online TTA model $\theta _ { t } ^ { * }$ for generating poisoned samples. To mitigate this issue, we propose to leverage a surrogate model ${ \dot { \theta } } _ { t }$ as an proxy model, which is distilled by Eq. 1 with the last feedback of $B _ { a , t - \delta }$ , where δ denotes the time interval between two injected poisoned subsets. Second, DIA evaluates the outer optimization by employing the benign samples $B _ { b }$ (assuming access to benign users’ query samples). The adversarial risk mainly arises from the injection of poisoned samples into the TTA training process. However, employing the validation (benign) samples as the outer optimization objective may result in an overestimation of this risk, as the specific poisoned samples could be tailored for the attack on the inference of the current batch of benign samples (Park et al., 2024), e.g., $\theta ^ { b \prime }$ , rather than for attacking the TTA process, i.e., $\theta ^ { u }$

![](images/f550738d5c1a03551f91d908a1a69b4e29cea01f8ef18c0e9b722891fbab3511.jpg)  
Figure 2: (a) The attack performance comparison about the poisoned samples generated on Source (pretrained) Model, our proposed Surrogate Model and Online target Model (white box). (b) The T-SNE visualization of the feature points (before FC layer). Without $\mathcal { L } _ { r e g } ,$ common attack losses (e.g. maximizing cross-entropy) produce poisoned samples (orange dots) that are far from benign ones (blue dots), leading to less effective attacks. (c) The attack performance comparison between w.o. and w. $\mathcal { L } _ { r e g } .$ . (d) The average prediction entropy of the poisoned samples generated by our proposed two different attack objectives, respectively.

To prevent from using benign users’ samples for optimization and assuming grey-box attack, one possible solution is to swap the benign users’ samples $B _ { b }$ with the adversary’s clean sample $\mathcal { B } _ { a b }$ based on the assumption that $\mathcal { B } _ { a b }$ and $B _ { b }$ are drawn from similar distributions, and replacing the white-box model θ with distilled model $\hat { \theta }$ and discarding the inner TTA loop $\widehat { \theta } _ { t } ^ { * } \approx \widehat { \theta } _ { t }$ as adopted by DIA (Wu et al., 2023), resulting in the following formulation.

$$
\begin{array}{l} \min _ {\mathcal {B} _ {a}} \frac {1}{| \mathcal {B} _ {a b} |} \sum_ {x _ {i} \in \mathcal {B} _ {a b}} \mathcal {L} _ {a t k} \left(x _ {i}; \hat {\theta} _ {t} ^ {\prime} (\mathcal {B} _ {t})\right) \\ s. t. \quad \mathcal {B} _ {t} = \mathcal {B} _ {a} \cup \mathcal {B} _ {a b}; \quad \hat {\theta} ^ {b \prime} = \{\mu (\mathcal {B} _ {t}), \sigma^ {2} (\mathcal {B} _ {t}) \}; \quad \hat {\theta} _ {t} ^ {\prime} (\mathcal {B} _ {t}) = \hat {\theta} _ {t} ^ {u} \cup \hat {\theta} ^ {b \prime} \cup \hat {\theta} ^ {f} \end{array}\tag{3}
$$

Despite the above formulation alleviates the assumption of the available to access the benign users’ samples and the online model parameters, it still remains elusive to tackle. First, as most TTA methods leverage the current batch statistics to estimate the statistics on target domain, forwarding $B _ { t }$ results in esimating the BN statistics on the combination of $B _ { a }$ and $B _ { a b }$ which bias update of BN parameters. This may results in a mismatch between the feature distribution of $\mathcal { B } _ { a b }$ and $B _ { b }$ , if $B _ { b }$ is queried independently. Thus, the poisoning effect may fail to generalize to $B _ { b }$ . This is evidenced by an empirical study into the distribution of poisoned data in Fig. 2 (b) where the distribution of generated poisoned data (orange dots) deviate substantially from the benign samples (blue dots) if the Eq. 3 is directly attacked. Therefore, we are prompted to explore a solution that does not explicitly require forward pass for both $\scriptstyle { B _ { a } }$ and $\mathcal { B } _ { a b }$ simultaneously and is able to transfer the attacked effect from $B _ { a }$ to the benign subset i.e. $B _ { a b }$ or $B _ { b }$

To address this challenge, we propose introducing additional constraints and integrating the optimized target $B _ { a b }$ with the optimizing objective $B _ { a }$ into a unified objective $B _ { a } .$ , as presented in Eq. 4, where $\tilde { D ( P _ { 1 } , P _ { 2 } ) }$ is a metric of two distributions and $P _ { a }$ and $P _ { a b }$ refer to the feature distributions of $\scriptstyle { B _ { a } }$ and $\mathcal { B } _ { a b }$ . We have the follow reason why the formulation is effective. If $B _ { a }$ and $\mathcal { B } _ { a b }$ have the similar distribution, we can have $P _ { a }  P _ { a b } \stackrel {  } { \Rightarrow } \mathbb { E } _ { P _ { a } ( x ) } [ \mathcal { L } _ { a t k } ( x ) ]  \mathbb { E } _ { P _ { a b } ( x ) } [ \mathcal { L } _ { a t k } ( x ) ]$ ] according to the Probably Approximately Correct (PAC) learning framework (Valiant). Thus attack against $\scriptstyle { B _ { a } }$ has a high chance to generalize to $\mathcal { B } _ { a b }$

$$
\min _ {\mathcal {B} _ {a}} \frac {1}{| \mathcal {B} _ {a} |} \sum_ {x _ {i} \in \mathcal {B} _ {a}} \mathcal {L} _ {a t k} (x _ {i}; \hat {\theta} _ {t} ^ {\prime} (\mathcal {B} _ {a})); \quad s. t. \quad D (P _ {a}, P _ {a b}) = 0\tag{4}
$$

Feature Consistency Regularization for In-Distribution Attack: To achieve indistinguishable distribution between $P _ { a }$ and $P _ { a b } .$ , we propose to measure the discrepancy at feature level and introduce the discrepancy as a constraint to the optimization problem. Crucially, since the attack loss is defined in the representation extracted by the backbone network, the distribution consistency is ideally imposed on the intermediate features except for the final semantic one. Specifically, we denote the l-th intermediate feature map before each normalization layer as $\boldsymbol { z } _ { i } ^ { l ^ { \bullet } } = ~ f ^ { l } ( \bar { \boldsymbol { x _ { i } } } ) ~ \in ~ \mathbb { R } ^ { H _ { l } \times W _ { l } \times D _ { l } }$ . A single Gaussian distribution is fitted to intermediate layer features, as $\begin{array} { r } { \mu _ { i } ^ { l } \ = \ \frac { 1 } { H _ { l } W _ { l } } \sum _ { h , w } z _ { i h w } ^ { l } , ~ \breve { \Sigma } _ { i } ^ { l } \ = \ \frac { 1 } { H _ { l } W _ { l } } \sum _ { h , w } ( z _ { i h w } ^ { l } - \mu _ { i } ^ { l } ) ( z _ { i h w } ^ { l } - \mu _ { i } ^ { l } ) ^ { \top } } \end{array}$ and $\begin{array} { r } { \tilde { \mu } _ { i } ^ { l } = \frac { 1 } { H _ { l } W _ { l } } \sum _ { h , w } \tilde { z } _ { i h w } ^ { l } , ~ \tilde { \Sigma } _ { i } ^ { l } = \frac { \mathrm { i } } { H _ { l } W _ { l } } \sum _ { h , w } ( \tilde { z } _ { i h w } ^ { l } - \tilde { \mu } _ { i } ^ { l } ) ( \tilde { z } _ { i h w } ^ { l } - \tilde { \mu } _ { i } ^ { l } ) ^ { \top } } \end{array}$ , where $\tilde { z } _ { i }$ and z refer to the sample features from $B _ { a }$ and $B _ { a b } .$ , respectively. The KL-Divergence between feature distributions is introduced as the constraint.

$$
\mathcal {L} _ {r e g} = \frac {1}{L} \sum_ {l} K L D (\mathcal {N} (\mu_ {i} ^ {l}, \Sigma_ {i} ^ {l}) | | \mathcal {N} (\tilde {\mu} _ {i} ^ {l}, \tilde {\Sigma} _ {i} ^ {l}))\tag{5}
$$

With the introduced constraint $\mathcal { L } _ { r e g } = 0$ , we finally formulate the problem as Eq. 6. The problem now degenerates to a single level optimization with constraints which can be easily converted into an unconstrained optimization problem via Lagrangian multiplier (Lag, 2008). The unconstrained problem can be solved in an iterative fashion with detailed algorithm presented in the Appendix A.1.6.

$$
\begin{array}{r l} & {\underset {\mathcal {B} _ {a}} {\min} \frac {1}{| \mathcal {B} _ {a} |} \sum_ {x _ {i} \in \mathcal {B} _ {a}} \mathcal {L} _ {a t k} (x _ {i}; \hat {\theta} _ {t} ^ {\prime} (\mathcal {B} _ {a}))} \\ & {s. t. \quad \hat {\theta} ^ {b \prime} = \{\mu (\mathcal {B} _ {a}), \sigma^ {2} (\mathcal {B} _ {a}) \}; \quad \hat {\theta} _ {t} ^ {\prime} (\mathcal {B} _ {a}) = \hat {\theta} _ {t} ^ {u} \cup \hat {\theta} ^ {b \prime} \cup \hat {\theta} ^ {f}; \quad \mathcal {L} _ {r e g} = 0} \\ & {\Rightarrow \underset {\mathcal {B} _ {a}} {\min} \underset {\lambda} {\max} \frac {1}{| \mathcal {B} _ {a} |} \sum_ {x _ {i} \in \mathcal {B} _ {a}} \mathcal {L} _ {a t k} (x _ {i}; \hat {\theta} _ {t} ^ {\prime} (\mathcal {B} _ {a})) + \lambda \mathcal {L} _ {r e g}} \\ & {\Rightarrow \underset {\mathcal {B} _ {a}} {\min} \underset {\{\lambda_ {0} \dots \lambda_ {L - 1} \}} {\max} \frac {1}{| \mathcal {B} _ {a} |} \sum_ {x _ {i} \in \mathcal {B} _ {a}} \mathcal {L} _ {a t k} (x _ {i}; \hat {\theta} _ {t} ^ {\prime} (\mathcal {B} _ {a})) + \frac {1}{L} \sum_ {l} \lambda_ {l} K L D (\mathcal {N} (\mu_ {i} ^ {l}, \Sigma_ {i} ^ {l}) | | \mathcal {N} (\tilde {\mu} _ {i} ^ {l}, \tilde {\Sigma} _ {i} ^ {l})),} \end{array}\tag{6}
$$

where L is the number of intermediate feature layers. Through optimizing the above objective, now we could craft the effective poisoned data $B _ { a }$ that satisfies $\mathbb { E } _ { x _ { i } \in \mathcal { B } _ { a } } \mathcal { L } _ { a t k } ( x _ { i } ; \hat { \theta } _ { t } ) \approx \mathbb { E } _ { x _ { i } \in \mathcal { B } _ { b } } \mathcal { L } _ { a t k } ( x _ { i } ; \hat { \theta } _ { t } )$ since the approximation equation $P _ { a }  P _ { a b }  P _ { b }$ now holds. Fig. 2 (c) demonstrates the effectiveness of this in-distribution attack, where the attack performance of the attack objective combined with the feature regularization (orange bars) is always higher than that of the corresponding attack objective alone (blue bars) in different TTA methods. Next, we would introduce the attack objectives $\mathcal { L } _ { a t k }$ that we designed to effectively generate different kinds of poisoned samples.

## 4.3 TTA-AWARE ATTACK OBJECTIVE

The specific design of attack objective $\mathcal { L } _ { a t k }$ warrants careful consideration. The existing works examined both targeted and indiscriminative attacks, demonstrating that both are effective against state-of-the-art TTA methods (Wu et al., 2023). However, we argue that an attack objective is not universally effective against all TTA methods. Therefore, we investigate two types of attack objectives as follows, and the prediction entropy of poisoned samples generated via the proposed attack losses can be compared in Fig. 2 (d).

High Entropy Attack Objective: Self-Training based TTA methods, e.g. TENT, RPL, are vulnerable for out-of-distribution samples with high entropy (Niu et al., 2023), and therefore, a straightforward way to generate poisoned data to attack TTA model is by maximizing the entropy of poisoned data as proposed in TePA (Cong et al., 2023) since these poisoned samples with high prediction entropy would induce high updating gradient. However, maximizing the prediction entropy does not guarantee wrong pseudo labels. Therefore, we propose a stronger high entropy attack objective called Notch High Entropy Attack (NHE Attack). Based on the uniform distribution, we set the probability in the ground-truth label to zero and construct the target distribution Q. Then we minimize the cross-entropy against target distribution Q.

$$
\mathcal {L} _ {a t k} ^ {N H E} (\tilde {x} _ {i}) = - \sum_ {k} Q _ {i k} \log h _ {k} (\tilde {x} _ {i}) \quad s. t. \quad Q _ {i k} = \left\{ \begin{array}{l l} 0 & k = y _ {i} \\ \frac {1}{K - 1} & o t h e r s \end{array} \right.\tag{7}
$$

Low Entropy Attack Objective: High entropy attack objective is particular effective against selftraining based TTA methods because of high updating gradient, yet they could be easily defended by some defense strategies, e.g. entropy thresholding. Therefore, we further explore a new low entropy based attack objective. DIA (Wu et al., 2023) proposed to maximize the cross-entropy loss on the benign samples (indiscriminate attack) to generate the other poisoned samples. However, we empirically found that maximizing the cross-entropy loss without any constraints on one sample is prone to maximizing the probability of the most confident class (except the ground-truth) of one model, and feeding these samples into TTA model would bring up the following issues. i) The model will quickly bias towards the most confident class and collapse if without any class diversity constraints. ii) If class diversity constraints are applied (assembled in several TTA methods, e.g. EATA, ROID), this objective will become less ineffective, since class-biased poisoned samples will obtain a less updating weighting than other benign samples. Therefore, we propose a class-balanced low entropy attack, termed Balanced Low Entropy Attack (BLE Attack). Specifically, we maintain an moving average probability confusion $C \in [ 0 , 1 ] ^ { K \times K }$ to store the prediction bias in each class and find a global optimal label mapping $M \in \{ 0 , 1 \} ^ { K \times K }$ such that each class is attacked towards the most probable non ground-truth class. Details of deriving label mapping M is deferred to the

Appendix A.1.2. Finally, the BLE Attack objective is calculated as Eq. 8.

$$
\mathcal {L} _ {a t k} ^ {B L E} (\tilde {x} _ {i}) = - \sum_ {k} \mathbb {1} (k = \arg \max _ {q \neq y _ {i}} M _ {y _ {i}, q}) \log h (\tilde {x} _ {i})\tag{8}
$$

Overall Attack Strategy: We craft poisoned data by attacking the aforementioned in-distribution attack objective with regularization. Following the practice that poisoned data should be less discernible by human, we employ a 40 steps Projected Gradient Descent algorithm (Boyd & Vandenberghe, 2004) on the combined objective in Eq. 6 with a budget b. More details of the whole data poisoning algorithm are deferred to the Appendix A.1.6.

## 5 EXPERIMENT

## 5.1 EXPERIMENT DETAILS

Benchmark Poisoning Methods: We evaluated the following methods under our proposed RTTDP setting. Unlearnable Examples (Huang et al., 2021) generates the poisoned noise by minimizing the cross-entropy of $B _ { a }$ on a randomly initialized model. Adversarial Poisoning (Fowl et al., 2021) proposed to minimize the cross-entropy between the posterior probabilities of poisoned samples, $B _ { a } ,$ and their corresponding incorrect labels, $\hat { y } ,$ where the incorrect labels are defined as ${ \hat { y } } _ { i } = y _ { i } + 1$ DIA (Wu et al., 2023) is one of the first approaches towards test-time data poisoning, generating the poisoned data via maximizing the cross-entropy of other benign data. We adapt DIA to the realistic evaluation protocol by splitting $B _ { a b }$ into two subsets of 50% each, i.e. $B _ { a b } ^ { p } : B _ { a b } ^ { b } = 1 : 1$ and craft $B _ { a } ^ { p }$ to maximize the cross-entropy of $B _ { a b } ^ { b }$ . TePA (Cong et al., 2023) proposed to maximize entropy to generate poisoned data and performed attack before TTA starts. We adapt TePA to generate the poisoned data based on the source model and inject them into TTA pipeline on-the-fly. MaxCE (Madry et al., 2018) is an established way to create adversarial samples by maximizing the cross-entropy loss. Finally, we evaluate the two attack objectives proposed in this paper, i.e high entropy attack (NHE Attack) and low entropy attack against most probable and balanced non ground truth class (BLE Attack). For both NHE Attack and BLE Attack, we evaluate the attack objective subject to the constraint of our proposed feature consistency (Eq. 6). For all methods that require gradient-based optimization, we employ the Projected Gradient Descent (PGD) algorithm (Boyd & Vandenberghe, 2004) to perform the constrained optimization. We use 40 steps PGD for all methods for a fair comparison.

Datasets: We evaluate on three datasets, widely adopted for TTA benchmarking. CIFAR10-C, CIFAR100-C and ImageNet-C are synthesized from the original clean validation set by adding various types of corruptions to simulate natural distribution shifts (Hendrycks & Dietterich, 2019). We choose corruption level 5 and perform continual test-time adaptation setting (Wang et al., 2022) for evaluation. Following prior works (Wang et al., 2022; Döbler et al., 2023), we adopt the pre-trained WideResNet-28 (Zagoruyko & Komodakis, 2016), ResNeXt-29 (Xie et al., 2017), and ResNet-50 (He et al., 2016) models for experiments on the CIFAR10-C, CIFAR100-C, and ImageNet-C datasets, respectively. More experiment details can be found in the Appendix A.3.

## 5.2 EVALUATION ON TEST-TIME DATA POISONING

We present the results of comparing different attack objectives against state-of-the-art TTA methods in Tab. 2, Tab. 3 and Tab. 4 for CIFAR10-C, CIFAR100-C and ImageNet-C respectively. We make the following observations from the results. i) Contrary to the claims that TTA methods are extremely vulnerable to data poisoning, under the realistic data poisoning protocol, without accessing to benign data, it’s not trivial to transfer the adversarial risk from poisoned data to benign data, especially for the TTA methods using EMA model such as CoTTA and ROID. In particular, existing methods do not pose too much risk to more advanced TTA methods without feature consistency regularization. DIA and TePA are more effective on TENT and RPL than other TTA methods. We attribute this to the fact that both TENT and RPL are naive self-training methods without filtering testing samples, hence, poisoned data could easily mislead model update. ii) Our proposed two attack objectives generally perform better than existing poisoning methods, demonstrating a better average ranking and a higher average error rate. This is attributed to the combination of the well-designed attack objective and the regularization of feature consistency. On the other hand, low entropy attack (BLE) obtains significantly improved with our proposed feature consistency compared with the similar low entropy attack i.e. MaxCE. iii) “Non-uniform ” attack in general yields higher attack success rate than “Uniform” attack. This is probably due to consecutive attack being more effective in misleading model’s update.

Table 2: Evaluation of test-time data poisoning under the RTTDP protocol for CIFAR10-C. We report the attack success rate (higher the better) for each TTA method and the average ranking (lower the better) for each attack objective. <sup>∗</sup> indicates that the method is modified to align with the RTTDP protocol.

<table><tr><td>Attack Freq.</td><td>Attack Objective</td><td>Source</td><td>TENT</td><td>RPL</td><td>EATA</td><td>TTAC</td><td>SAR</td><td>CoTTA</td><td>ROID</td><td>Avg. Err. (↑)</td><td>Avg. Rank (↓)</td></tr><tr><td rowspan="8">Uniform</td><td>No Attack</td><td rowspan="8">43.81</td><td>19.72</td><td>21.00</td><td>18.03</td><td>17.41</td><td>18.94</td><td>16.46</td><td>16.37</td><td>18.28</td><td>7.43</td></tr><tr><td>Unlearnable Examples (Huang et al., 2021)</td><td>32.61</td><td>26.62</td><td>20.11</td><td>18.43</td><td>19.23</td><td>17.27</td><td>17.80</td><td>21.72</td><td>4.86</td></tr><tr><td>Adversarial Poisoning (Fowl et al., 2021)</td><td>19.60</td><td>19.90</td><td>18.94</td><td>18.69</td><td>19.90</td><td>18.34</td><td>19.12</td><td>19.21</td><td>3.86</td></tr><tr><td>DIA* (Wu et al., 2023)</td><td>26.04</td><td>21.87</td><td>18.94</td><td>18.56</td><td>19.46</td><td>17.72</td><td>17.77</td><td>20.05</td><td>4.86</td></tr><tr><td>TePA* (Cong et al., 2023)</td><td>33.78</td><td>22.36</td><td>23.37</td><td>17.75</td><td>19.53</td><td>16.57</td><td>18.76</td><td>21.73</td><td>4.43</td></tr><tr><td>MaxCE (Madry et al., 2018)</td><td>18.55</td><td>20.81</td><td>18.17</td><td>18.50</td><td>19.50</td><td>16.88</td><td>18.57</td><td>18.71</td><td>6.00</td></tr><tr><td>BLE Attack (Ours)</td><td>54.07</td><td>51.99</td><td>45.20</td><td>34.00</td><td>26.80</td><td>18.12</td><td>19.06</td><td>35.61</td><td>1.57</td></tr><tr><td>NHE Attack (Ours)</td><td>73.86</td><td>72.40</td><td>29.73</td><td>18.67</td><td>24.56</td><td>17.54</td><td>17.00</td><td>36.25</td><td>2.86</td></tr><tr><td rowspan="6">Non-Uniform</td><td>No Attack</td><td rowspan="6">43.55</td><td>19.29</td><td>20.36</td><td>17.75</td><td>16.89</td><td>18.74</td><td>16.18</td><td>15.81</td><td>17.86</td><td>5.71</td></tr><tr><td>DIA* (Wu et al., 2023)</td><td>22.84</td><td>25.70</td><td>19.75</td><td>18.35</td><td>19.42</td><td>19.18</td><td>17.79</td><td>20.43</td><td>4.00</td></tr><tr><td>TePA* (Cong et al., 2023)</td><td>40.31</td><td>32.32</td><td>23.03</td><td>18.06</td><td>19.49</td><td>18.07</td><td>18.50</td><td>24.25</td><td>3.43</td></tr><tr><td>MaxCE (Madry et al., 2018)</td><td>18.64</td><td>20.01</td><td>18.29</td><td>18.43</td><td>19.47</td><td>18.01</td><td>18.94</td><td>18.83</td><td>4.43</td></tr><tr><td>BLE Attack (Ours)</td><td>56.17</td><td>46.66</td><td>50.97</td><td>34.25</td><td>27.54</td><td>19.23</td><td>20.12</td><td>36.42</td><td>1.43</td></tr><tr><td>NHE Attack (Ours)</td><td>74.93</td><td>73.65</td><td>27.56</td><td>18.75</td><td>24.95</td><td>20.86</td><td>16.77</td><td>36.78</td><td>2.00</td></tr></table>

Table 3: Evaluation of test-time data poisoning under the RTTDP protocol for CIFAR100-C. We report the attack success rate (higher the better) for each TTA method and the average ranking (lower the better) for each attack objective. <sup>∗</sup> indicates that the method is modified to align with the RTTDP protocol.

<table><tr><td>Attack Freq.</td><td>Attack Objective</td><td>Source</td><td>TENT</td><td>RPL</td><td>EATA</td><td>TTAC</td><td>SAR</td><td>CoTTA</td><td>ROID</td><td>Avg. Err. (↑)</td><td>Avg. Rank (↓)</td></tr><tr><td rowspan="8">Uniform</td><td>No Attack</td><td rowspan="8">46.23</td><td>60.25</td><td>47.12</td><td>32.20</td><td>31.93</td><td>31.62</td><td>32.13</td><td>29.11</td><td>37.77</td><td>7.29</td></tr><tr><td>Unlearnable Examples (Huang et al., 2021)</td><td>75.31</td><td>72.74</td><td>37.59</td><td>33.66</td><td>41.75</td><td>32.66</td><td>31.31</td><td>46.43</td><td>3.71</td></tr><tr><td>Adversarial Poisoning (Fowl et al., 2021)</td><td>33.87</td><td>34.27</td><td>32.11</td><td>35.49</td><td>32.27</td><td>32.76</td><td>30.15</td><td>32.99</td><td>5.71</td></tr><tr><td>DIA* (Wu et al., 2023)</td><td>74.79</td><td>68.42</td><td>33.77</td><td>32.57</td><td>33.20</td><td>32.68</td><td>30.10</td><td>43.65</td><td>5.29</td></tr><tr><td>TePA* (Cong et al., 2023)</td><td>75.79</td><td>81.98</td><td>36.74</td><td>33.41</td><td>35.79</td><td>32.41</td><td>32.24</td><td>46.91</td><td>3.57</td></tr><tr><td>MaxCE (Madry et al., 2018)</td><td>42.36</td><td>39.04</td><td>34.08</td><td>40.73</td><td>32.01</td><td>32.18</td><td>31.08</td><td>35.93</td><td>5.57</td></tr><tr><td>BLE Attack (Ours)</td><td>73.93</td><td>76.71</td><td>47.30</td><td>34.58</td><td>43.25</td><td>32.81</td><td>32.27</td><td>48.69</td><td>2.28</td></tr><tr><td>NHE Attack (Ours)</td><td>92.08</td><td>91.72</td><td>37.86</td><td>33.85</td><td>56.09</td><td>32.50</td><td>31.48</td><td>53.65</td><td>2.57</td></tr><tr><td rowspan="6">Non-Uniform</td><td>No Attack</td><td rowspan="6">46.33</td><td>62.30</td><td>49.69</td><td>31.45</td><td>32.07</td><td>31.37</td><td>32.56</td><td>28.39</td><td>38.26</td><td>5.71</td></tr><tr><td>DIA* (Wu et al., 2023)</td><td>76.83</td><td>71.44</td><td>33.74</td><td>32.63</td><td>33.24</td><td>33.13</td><td>30.07</td><td>44.44</td><td>4.14</td></tr><tr><td>TePA* (Cong et al., 2023)</td><td>82.29</td><td>88.48</td><td>36.40</td><td>34.89</td><td>35.56</td><td>33.44</td><td>33.27</td><td>49.19</td><td>2.43</td></tr><tr><td>MaxCE (Madry et al., 2018)</td><td>41.89</td><td>38.05</td><td>33.20</td><td>42.12</td><td>31.90</td><td>32.78</td><td>31.66</td><td>35.94</td><td>4.43</td></tr><tr><td>BLE Attack (Ours)</td><td>71.30</td><td>72.97</td><td>47.21</td><td>35.26</td><td>41.22</td><td>33.50</td><td>32.60</td><td>47.72</td><td>2.29</td></tr><tr><td>NHE Attack (Ours)</td><td>94.46</td><td>94.58</td><td>40.05</td><td>34.14</td><td>56.48</td><td>33.52</td><td>31.45</td><td>54.95</td><td>2.00</td></tr></table>

Table 4: Evaluation of test-time data poisoning under the RTTDP protocol for ImageNet-C. We report the attack success rate (higher the better) for each TTA method and the average ranking (lower the better) for each attack objective. <sup>∗</sup> indicates that the method is modified to align with the RTTDP protocol.

<table><tr><td>Attack Freq.</td><td>Attack Objective</td><td>Source</td><td>TENT</td><td>SAR</td><td>CoTTA</td><td>ROID</td><td>Avg. Err. (↑)</td><td>Avg. Rank (↓)</td></tr><tr><td rowspan="6">Uniform</td><td>No Attack</td><td></td><td>63.49</td><td>61.26</td><td>63.02</td><td>53.42</td><td>60.30</td><td>5.50</td></tr><tr><td>DIA* (Wu et al., 2023)</td><td></td><td>67.18</td><td>62.91</td><td>64.09</td><td>56.97</td><td>62.79</td><td>4.00</td></tr><tr><td>TePA* (Cong et al., 2023)</td><td rowspan="2">82.08</td><td>75.36</td><td>64.90</td><td>62.84</td><td>59.78</td><td>65.72</td><td>3.00</td></tr><tr><td>MaxCE (Madry et al., 2018)</td><td>62.64</td><td>61.66</td><td>68.83</td><td>59.89</td><td>63.26</td><td>3.25</td></tr><tr><td>BLE Attack (Ours)</td><td></td><td>68.04</td><td>64.31</td><td>66.40</td><td>57.10</td><td>63.96</td><td>3.00</td></tr><tr><td>NHE Attack (Ours)</td><td></td><td>78.03</td><td>72.58</td><td>63.84</td><td>57.72</td><td>68.04</td><td>2.25</td></tr><tr><td rowspan="6">Non-Uniform</td><td>No Attack</td><td rowspan="4">81.98</td><td>61.81</td><td>59.52</td><td>62.51</td><td>50.36</td><td>58.55</td><td>6.00</td></tr><tr><td>DIA* (Wu et al., 2023)</td><td>66.61</td><td>62.88</td><td>63.40</td><td>55.18</td><td>62.02</td><td>4.25</td></tr><tr><td>TePA* (Cong et al., 2023)</td><td>74.98</td><td>62.31</td><td>62.78</td><td>59.29</td><td>64.84</td><td>3.50</td></tr><tr><td>MaxCE (Madry et al., 2018)</td><td>62.09</td><td>65.58</td><td>72.39</td><td>59.76</td><td>64.96</td><td>2.50</td></tr><tr><td>BLE Attack (Ours)</td><td></td><td>67.61</td><td>65.95</td><td>65.75</td><td>56.23</td><td>63.89</td><td>2.75</td></tr><tr><td>NHE Attack (Ours)</td><td></td><td>77.49</td><td>73.67</td><td>64.02</td><td>57.09</td><td>68.07</td><td>2.00</td></tr></table>

## 5.3 ABLATION STUDY ON ATTACK MODULES

In this section, we ablate our proposed modules including the surrogate model, the feature consistency regularization and two attack objectives to demonstrate their their indispensable contribution to the final results. We conduct the experiments on CIFAR10-C and CIFAR100-C datasets as shown in Tab. 5. First, comparing the use of the source model v.s. surrogate model for generating poisoned data, the surrogate model consistently delivers superior results, often approaching or even slightly surpassing those obtained with the online model, regardless of the attack objective. It demonstrates the effectiveness of our proposed surrogate model that is leveraged for generating on-the-fly poisoned data. Second, our proposed NHE attack objective is effective though using source model and without feature consistency regularization, that could be attributed to the high entropy samples easily mislead the model update and cause strong perturbation to the source knowledge. Third, under the surrogate model or online model, both BLE and NHE are significantly improved with the help of feature consistency regularization, empirically demonstrating the reasonableness and effectiveness of our method.

Table 5: The ablation study of our proposed modules under the RTTDP protocol on CIFAR10/100-C datasets.

<table><tr><td rowspan="2">Attack Model</td><td rowspan="2">Attack Objective</td><td rowspan="2">Feat. Cons. Reg.</td><td colspan="4">CIFAR10-C</td><td colspan="4">CIFAR100-C</td></tr><tr><td>TENT</td><td>EATA</td><td>SAR</td><td>AR (↑)</td><td>TENT</td><td>EATA</td><td>SAR</td><td>AR (↑)</td></tr><tr><td>Source Model</td><td>BLE</td><td>-</td><td>19.26</td><td>18.82</td><td>19.80</td><td>19.29</td><td>34.21</td><td>31.62</td><td>32.17</td><td>32.67</td></tr><tr><td>Source Model</td><td>BLE</td><td>√</td><td>38.09</td><td>23.28</td><td>21.86</td><td>27.74</td><td>67.11</td><td>34.57</td><td>33.78</td><td>45.15</td></tr><tr><td>Source Model</td><td>NHE</td><td>-</td><td>63.00</td><td>23.76</td><td>19.52</td><td>35.43</td><td>85.48</td><td>39.37</td><td>38.76</td><td>54.54</td></tr><tr><td>Source Model</td><td>NHE</td><td>√</td><td>37.27</td><td>20.79</td><td>21.07</td><td>26.38</td><td>81.81</td><td>35.96</td><td>47.06</td><td>54.94</td></tr><tr><td>Surrogate Model (Ours)</td><td>BLE</td><td>-</td><td>20.22</td><td>20.16</td><td>19.71</td><td>20.03</td><td>38.71</td><td>31.87</td><td>31.95</td><td>34.18</td></tr><tr><td>Surrogate Model (Ours)</td><td>BLE</td><td>√</td><td>54.07</td><td>45.20</td><td>26.80</td><td>42.02</td><td>73.93</td><td>47.30</td><td>43.25</td><td>54.83</td></tr><tr><td>Surrogate Model (Ours)</td><td>NHE</td><td>-</td><td>72.77</td><td>21.93</td><td>19.51</td><td>38.07</td><td>81.49</td><td>32.16</td><td>31.68</td><td>48.44</td></tr><tr><td>Surrogate Model (Ours)</td><td>NHE</td><td>√</td><td>73.86</td><td>29.73</td><td>24.56</td><td>42.72</td><td>92.08</td><td>37.86</td><td>56.09</td><td>62.01</td></tr><tr><td>Online Model</td><td>BLE</td><td>-</td><td>25.14</td><td>25.50</td><td>19.71</td><td>23.45</td><td>42.09</td><td>32.82</td><td>32.05</td><td>35.65</td></tr><tr><td>Online Model</td><td>BLE</td><td>√</td><td>56.75</td><td>52.32</td><td>27.38</td><td>45.48</td><td>77.92</td><td>49.91</td><td>44.01</td><td>57.28</td></tr><tr><td>Online Model</td><td>NHE</td><td>-</td><td>72.01</td><td>21.91</td><td>19.52</td><td>37.81</td><td>80.62</td><td>31.96</td><td>31.69</td><td>48.09</td></tr><tr><td>Online Model</td><td>NHE</td><td>√</td><td>73.62</td><td>28.73</td><td>25.03</td><td>42.46</td><td>91.15</td><td>39.01</td><td>54.67</td><td>61.61</td></tr></table>

## 5.4 EXPLORING EFFECTIVE DEFENSE PRACTICES

In this section, we explore effective defense practices. We conduct an ablation study for each of the above practices on top of a simple entropy minimization baseline method (Min. Ent.). As seen in Tab. 6, we make the observation that without any hypothesized defense practice, directly minimizing entropy is very sensitive to poisoned data, especially the high entropy attack (NHE). When entropy thresholding (Ent. Thresh.) is applied, we observe a significant improvement in robustness under high entropy attack, suggesting rejecting high entropy testing samples from TTA is an effective defense practice. Furthermore, both data augmentation (Data Aug.) and exponential moving average update (EMA) are very effective defense practices. The former could perturb the testing sample towards non-adversarial direction while the latter prevents the model from updating too quickly, thus less sensitive to poisoned data. Finally, one might expect stochastic parameter restoration (Stoch. Resto.) to be an effective defense method. Despite exhibiting improved adversarial robustness alone, parameter restoration does not further improve the robustness when combined with other effective defense methods.

Table 6: Ablation study of hypothesized defense practices on CIFAR10-C dataset.

<table><tr><td>Min. Ent.</td><td>Ent. Thresh.</td><td>Data Aug.</td><td>EMA Update</td><td>Stoch. Resto.</td><td>BLE</td><td>NHE</td></tr><tr><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td colspan="2">43.81</td></tr><tr><td>√</td><td>-</td><td>-</td><td>-</td><td>-</td><td>54.07</td><td>73.86</td></tr><tr><td>√</td><td>√</td><td>-</td><td>-</td><td>-</td><td>46.24</td><td>35.86</td></tr><tr><td>√</td><td>√</td><td>√</td><td>-</td><td>-</td><td>24.01</td><td>20.05</td></tr><tr><td>√</td><td>√</td><td>√</td><td>√</td><td>-</td><td>20.22</td><td>19.76</td></tr><tr><td>-</td><td>-</td><td>-</td><td>-</td><td>√</td><td>29.68</td><td>50.68</td></tr><tr><td>√</td><td>√</td><td>√</td><td>√</td><td>√</td><td>20.41</td><td>20.30</td></tr></table>

Table 7: The generalisation of our modules on CIFAR10-C.

<table><tr><td>Attack Objective</td><td>TENT</td><td>EATA</td></tr><tr><td>DIA</td><td>26.04</td><td>18.94</td></tr><tr><td>DIA + Ours</td><td>27.02</td><td>19.41</td></tr><tr><td>TePA</td><td>33.78</td><td>23.37</td></tr><tr><td>TePA + Ours</td><td>38.79</td><td>21.37</td></tr><tr><td>MaxCE</td><td>18.55</td><td>18.17</td></tr><tr><td>MaxCE + Ours</td><td>23.61</td><td>19.44</td></tr></table>

## 5.5 GENERALISATION OF OUR MODULES

In this section, to demonstrate the generalization of our method, we combine the existing attack objec tives with our proposed modules including the surrogate model and feature consistency regularization. The comparisons are shown in Tab. 7. First, we can observe that DIA and MaxCE could get improved additional with our proposed method. Second, TePA could obtain improvement under TENT method but slightly degraded under EATA method. It could be that TePA using maximizing entropy as an attack objective, and with the help of the surrogate model, the poisoned data would have very high prediction entropy because the attack reference model is more approximate to the online model, but fail to pass the entropy threshold and class diverse weighting using in EATA. Overall, our proposed in-distribution attack could generalize to most of the existing attacking objectives.

## 6 CONCLUSION

In this work, we reviewed the assumptions adopted by existing works for generating poisoned data at test-time and propose a few criteria that define a more realistic test-time data poisoning. Specifically, we approach from the angles of attack transparency, access to other users’ benign data, attack budget, and attack order. To craft realistic poisoned data, we proposed a grey-box in-distribution attack with attack objective tailored for TTA methods. Through extensive evaluations under the realistic evaluation protocol, we reveal that the adversarial risk of TTA method might be over estimated and, importantly, certain practices in TTA methods are empirically proven to be effective and should be considered for designing adversarial robust TTA methods in the future.

## ACKNOWLEDGEMENTS

This research work is supported by the National Natural Science Foundation of China (NSFC) (Grant Number: 62106078), the Agency for Science, Technology and Research (A\*STAR) under its MTC Programmatic Funds (Grant Number: M23L7b0021) and the Guangdong R&D key project of China (Grant Number: 2019B010155001). This work was done during Yongyi Su’s attachment with Institute for Infocomm Research (I2R), funded by China Scholarship Council (CSC).

## REFERENCES

Lagrange Multiplier, pp. 292–294. Springer New York, New York, NY, 2008. ISBN 978-0-387- 32833-1. doi: 10.1007/978-0-387-32833-1\_218.

Naveed Akhtar and Ajmal Mian. Threat of adversarial attacks on deep learning in computer vision: A survey. Ieee Access, 6:14410–14430, 2018.

Scott Alfeld, Xiaojin Zhu, and Paul Barford. Data poisoning attacks against autoregressive models. In Proceedings ofthe AAAI Conference on Artificial Intelligence, volume 30, 2016.

Eric Arazo, Diego Ortego, Paul Albert, Noel E O’Connor, and Kevin McGuinness. Pseudo-labeling and confirmation bias in deep semi-supervised learning. In Proceedings of 2020 International Joint Conference on Neural Networks, pp. 1–8. IEEE, 2020.

Battista Biggio, Blaine Nelson, and Pavel Laskov. Poisoning attacks against support vector machines. arXiv preprint arXiv:1206.6389, 2012.

Battista Biggio, Igino Corona, Davide Maiorca, Blaine Nelson, Nedim Šrndic, Pavel Laskov, Giorgio´ Giacinto, and Fabio Roli. Evasion attacks against machine learning at test time. In Joint European Conference on Machine Learning and Knowledge Discovery in Databases, 2013.

Stephen Boyd and Lieven Vandenberghe. Convex optimization. Cambridge university press, 2004.

Dhanajit Brahma and Piyush Rai. A probabilistic framework for lifelong test-time adaptation. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 3582–3591, 2023.

Anirban Chakraborty, Manaar Alam, Vishal Dey, Anupam Chattopadhyay, and Debdeep Mukhopad hyay. Adversarial attacks and defences: A survey. arXiv preprint arXiv:1810.00069, 2018.

Jiefeng Chen, Xi Wu, Yang Guo, Yingyu Liang, and Somesh Jha. Towards evaluating the robustness of neural networks learned by transduction. In International Conference on Learning Representations, 2022. URL https://openreview.net/forum?id=\_5js\_8uTrx1.

Jinyin Chen, Mengmeng Su, Shijing Shen, Hui Xiong, and Haibin Zheng. Poba-ga: Perturbation optimized black-box adversarial attacks via genetic algorithm. Computers & Security, 2019.

Pin-Yu Chen, Huan Zhang, Yash Sharma, Jinfeng Yi, and Cho-Jui Hsieh. Zoo: Zeroth order optimization based black-box attacks to deep neural networks without training substitute models. In Proceedings of the 10th ACM workshop on artificial intelligence and security, pp. 15–26, 2017.

Yijin Chen, Xun Xu, Yongyi Su, and Kui Jia. Stfar: Improving object detection robustness at test-time by self-training with feature alignment regularization. arXiv preprint arXiv:2303.17937, 2023.

Zhixiang Chi, Li Gu, Tao Zhong, Huan Liu, YUANHAO YU, Konstantinos N Plataniotis, and Yang Wang. Adapting to distribution shift by visual domain prompt generation. In The Twelfth International Conference on Learning Representations, 2024.

Tianshuo Cong, Xinlei He, Yun Shen, and Yang Zhang. Test-time poisoning attacks against test-time adaptation models. In IEEE Symposium on Security and Privacy, 2023.

Francesco Croce and Matthias Hein. Reliable evaluation of adversarial robustness with an ensemble of diverse parameter-free attacks. In International conference on machine learning, pp. 2206–2216. PMLR, 2020.

Mario Döbler, Robert A Marsden, and Bin Yang. Robust mean teacher for continual and gradual test-time adaptation. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 7704–7714, 2023.

Alexey Dosovitskiy, Lucas Beyer, Alexander Kolesnikov, Dirk Weissenborn, Xiaohua Zhai, Thomas Unterthiner, Mostafa Dehghani, Matthias Minderer, Georg Heigold, Sylvain Gelly, Jakob Uszkoreit, and Neil Houlsby. An image is worth 16x16 words: Transformers for image recognition at scale. In International Conference on Learning Representations, 2021.

Jiaxin Fan, Qi Yan, Mohan Li, Guanqun Qu, and Yang Xiao. A survey on data poisoning attacks and defenses. In 2022 7th IEEE International Conference on Data Science in Cyberspace (DSC), pp. 48–55. IEEE, 2022.

Liam Fowl, Micah Goldblum, Ping-yeh Chiang, Jonas Geiping, Wojciech Czaja, and Tom Goldstein. Adversarial examples make strong poisons. Advances in Neural Information Processing Systems, 34:30339–30351, 2021.

Yunhe Gao, Xingjian Shi, Yi Zhu, Hao Wang, Zhiqiang Tang, Xiong Zhou, Mu Li, and Dimitris N Metaxas. Visual prompt tuning for test-time domain adaptation. arXiv preprint arXiv:2210.04831, 2022.

Taesik Gong, Jongheon Jeong, Taewon Kim, Yewon Kim, Jinwoo Shin, and Sung-Ju Lee. NOTE: Robust continual test-time adaptation against temporal correlation. In Proceedings ofAdvances in Neural Information Processing Systems (NeurIPS), 2022.

Ian J Goodfellow, Jonathon Shlens, and Christian Szegedy. Explaining and harnessing adversarial examples. arXiv preprint arXiv:1412.6572, 2014.

Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep residual learning for image recognition. In Proceedings of the IEEE conference on computer vision and pattern recognition, pp. 770–778, 2016.

Dan Hendrycks and Thomas Dietterich. Benchmarking neural network robustness to common corruptions and perturbations. arXiv preprint arXiv:1903.12261, 2019.

Hanxun Huang, Xingjun Ma, Sarah Monazam Erfani, James Bailey, and Yisen Wang. Unlearnable examples: Making personal data unexploitable. In International Conference on Learning Representations, 2021. URL https://openreview.net/forum?id=iAmZUo0DxC0.

Andrew Ilyas, Logan Engstrom, Anish Athalye, and Jessy Lin. Black-box adversarial attacks with limited queries and information. In International conference on machine learning, pp. 2137–2146. PMLR, 2018.

Alexander Kirillov, Eric Mintun, Nikhila Ravi, Hanzi Mao, Chloe Rolland, Laura Gustafson, Tete Xiao, Spencer Whitehead, Alexander C Berg, Wan-Yen Lo, et al. Segment anything. In Proceedings ofthe IEEE/CVF International Conference on Computer Vision, pp. 4015–4026, 2023.

Huichen Li, Xiaojun Xu, Xiaolu Zhang, Shuang Yang, and Bo Li. Qeba: Query-efficient boundarybased blackbox attack. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, 2020.

Yushu Li, Xun Xu, Yongyi Su, and Kui Jia. On the robustness of open-world test-time training: Self-training with dynamic prototype expansion. In Proceedings of the IEEE/CVF International Conference on Computer Vision, pp. 11836–11846, 2023.

Jian Liang, Dapeng Hu, and Jiashi Feng. Do we really need to access the source data? source hypothesis transfer for unsupervised domain adaptation. In Proceedings ofInternational conference on machine learning, pp. 6028–6039, 2020.

Jian Liang, Ran He, and Tieniu Tan. A comprehensive survey on test-time adaptation under distribution shifts. International Journal ofComputer Vision, pp. 1–34, 2024.

Nanqing Liu, Xun Xu, Yongyi Su, Haojie Zhang, and Heng-Chao Li. Pointsam: Pointly-supervised segment anything model for remote sensing images. IEEE Transactions on Geoscience and Remote Sensing, 2025.

Yuejiang Liu, Parth Kothari, Bastien Van Delft, Baptiste Bellot-Gurlet, Taylor Mordan, and Alexandre Alahi. Ttt++: When does self-supervised test-time training fail or thrive? Advances in Neural Information Processing Systems, 34:21808–21820, 2021.

Aleksander Madry, Aleksandar Makelov, Ludwig Schmidt, Dimitris Tsipras, and Adrian Vladu. Towards deep learning models resistant to adversarial attacks. In International Conference on Learning Representations, 2018.

Robert A Marsden, Mario Döbler, and Bin Yang. Universal test-time adaptation through weight ensembling, diversity weighting, and prior correction. In Proceedings ofthe IEEE/CVF Winter Conference on Applications of Computer Vision, pp. 2555–2565, 2024.

Shuaicheng Niu, Jiaxiang Wu, Yifan Zhang, Yaofo Chen, Shijian Zheng, Peilin Zhao, and Mingkui Tan. Efficient test-time model adaptation without forgetting. In Proceedings of International conference on machine learning, pp. 16888–16905, 2022.

Shuaicheng Niu, Jiaxiang Wu, Yifan Zhang, Zhiquan Wen, Yaofo Chen, Peilin Zhao, and Mingkui Tan. Towards stable test-time adaptation in dynamic wild world. In Proceedings of International Conference on Learning Representations, 2023.

Maxime Oquab, Timothée Darcet, Théo Moutakanni, Huy Vo, Marc Szafraniec, Vasil Khalidov, Pierre Fernandez, Daniel Haziza, Francisco Massa, Alaaeldin El-Nouby, et al. Dinov2: Learning robust visual features without supervision. Transactions on Machine Learning Research Journal, pp. 1–31, 2024.

Hyejin Park, Jeongyeon Hwang, Sunung Mun, Sangdon Park, and Jungseul Ok. Medbn: Robust test-time adaptation against malicious test samples. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 5997–6007, 2024.

Hao Qiu, Leonardo Lucio Custode, and Giovanni Iacca. Black-box adversarial attacks using evolution strategies. In Proceedings ofthe Genetic and Evolutionary Computation Conference Companion, 2021.

Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya Ramesh, Gabriel Goh, Sandhini Agarwal, Girish Sastry, Amanda Askell, Pamela Mishkin, Jack Clark, et al. Learning transferable visual models from natural language supervision. In International conference on machine learning, pp. 8748–8763. PMLR, 2021.

Binxin Ru, Adam Cobb, Arno Blaas, and Yarin Gal. Bayesopt adversarial attack. In International Conference on Learning Representations, 2019.

Evgenia Rusak, Steffen Schneider, George Pachitariu, Luisa Eck, Peter Vincent Gehler, Oliver Bringmann, Wieland Brendel, and Matthias Bethge. If your data distribution shifts, use selflearning. Transactions on Machine Learning Research, 2022.

Ali Shafahi, W Ronny Huang, Mahyar Najibi, Octavian Suciu, Christoph Studer, Tudor Dumitras, and Tom Goldstein. Poison frogs! targeted clean-label poisoning attacks on neural networks. Advances in neural information processing systems, 31, 2018.

Junha Song, Jungsoo Lee, In So Kweon, and Sungha Choi. Ecotta: Memory-efficient continual test-time adaptation via self-distilled regularization. In Proceedings ofthe IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 11920–11929, 2023.

Yongyi Su, Xun Xu, and Kui Jia. Revisiting realistic test-time training: Sequential inference and adaptation by anchored clustering. Proceedings ofAdvances in Neural Information Processing Systems, 35:17543–17555, 2022.

Yongyi Su, Xun Xu, and Kui Jia. Towards real-world test-time adaptation: Tri-net self-training with balanced normalization. In Proceedings ofthe AAAI Conference on Artificial Intelligence, 2024a.

Yongyi Su, Xun Xu, Tianrui Li, and Kui Jia. Revisiting realistic test-time training: Sequential inference and adaptation by anchored clustering regularized self-training. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2024b.

Christian Szegedy, Wojciech Zaremba, Ilya Sutskever, Joan Bruna, Dumitru Erhan, Ian Goodfellow, and Rob Fergus. Intriguing properties of neural networks. In International Conference on Learning Representations, 2014.

Florian Tramèr, Alexey Kurakin, Nicolas Papernot, Ian Goodfellow, Dan Boneh, and Patrick Mc-Daniel. Ensemble adversarial training: Attacks and defenses. In International Conference on Learning Representations, 2018.

Leslie G Valiant. A theory of the learnable. Communications ofthe ACM.

Dequan Wang, Evan Shelhamer, Shaoteng Liu, Bruno Olshausen, and Trevor Darrell. Tent: Fully test-time adaptation by entropy minimization. In Proceedings of International Conference on Learning Representations, 2020.

Qin Wang, Olga Fink, Luc Van Gool, and Dengxin Dai. Continual test-time domain adaptation. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 7201–7211, 2022.

Ziqiang Wang, Zhixiang Chi, Yanan Wu, Li Gu, Zhi Liu, Konstantinos Plataniotis, and Yang Wang. Distribution alignment for fully test-time adaptation with dynamic online data streams. In European Conference on Computer Vision, pp. 332–349. Springer, 2025.

Tong Wu, Feiran Jia, Xiangyu Qi, Jiachen T Wang, Vikash Sehwag, Saeed Mahloujifar, and Prateek Mittal. Uncovering adversarial risks of test-time adaptation. In Proceedings of the 40th International Conference on Machine Learning, 2023.

Yanan Wu, Zhixiang Chi, Yang Wang, Konstantinos N Plataniotis, and Songhe Feng. Test-time domain adaptation by learning domain-aware batch normalization. In Proceedings of the AAAI Conference on Artificial Intelligence, volume 38, pp. 15961–15969, 2024.

Saining Xie, Ross Girshick, Piotr Dollár, Zhuowen Tu, and Kaiming He. Aggregated residual transformations for deep neural networks. In Proceedings of the IEEE conference on computer vision and pattern recognition, pp. 1492–1500, 2017.

Ying Xu, Xu Zhong, Antonio Jimeno Yepes, and Jey Han Lau. Grey-box adversarial attack and defence for sentiment classification. In Proceedings ofthe 2021 Conference ofthe North American Chapter of the Association for Computational Linguistics: Human Language Technologies, pp. 4078–4087, 2021.

Chaofei Yang, Qing Wu, Hai Li, and Yiran Chen. Generative poisoning attack method against neural networks. arXiv preprint arXiv:1703.01340, 2017.

Longhui Yuan, Binhui Xie, and Shuang Li. Robust test-time adaptation in dynamic scenarios. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 15922–15932, 2023.

Sergey Zagoruyko and Nikos Komodakis. Wide residual networks. In Procedings of the British Machine Vision Conference, 2016.

Marvin Zhang, Sergey Levine, and Chelsea Finn. Memo: Test time robustness via adaptation and augmentation. Advances in neural information processing systems, 35:38629–38642, 2022.

Xuezhou Zhang, Xiaojin Zhu, and Laurent Lessard. Online data poisoning attacks. In Learningfor Dynamics and Control, pp. 201–210. PMLR, 2020.

Tao Zhong, Zhixiang Chi, Li Gu, Yang Wang, Yuanhao Yu, and Jin Tang. Meta-dmoe: Adapting to domain shift by meta-distillation from mixture-of-experts. Advances in Neural Information Processing Systems, 35:22243–22257, 2022.

Zhi Zhou, Lan-Zhe Guo, Lin-Han Jia, Dingchu Zhang, and Yu-Feng Li. Ods: test-time adaptation in the presence of open-world data shift. In Proceedings ofInternational Conference on Machine Learning, pp. 42574–42588, 2023.

## A APPENDIX

## A.1 ADDITIONAL DETAILS FOR METHODOLOGY

## A.1.1 ILLUSTRATION OF TEST-TIME DATA POISONING BATCH SPLIT

We visualize the batch split under realistic test-time data poisoning in Fig. 3. We present the batch split scheme for both “Uniform” and “Non-Uniform” attack frequencies. Under “Uniform” attack frequency, the poisoned minibatch is uniformly presented in the test data stream while “Non-Uniform” attack protocol simulates the situation the adversary attacks the TTA model in a short period of time with a huge amount of poisoned data.

![](images/5481b71791be7a62d4e380076f896199337b6d0f6ffb079b0ba5ee1131635b0c.jpg)  
Figure 3: Illustration of test-time data poisoning batch split.

## A.1.2 GLOBAL OPTIOMAL LABEL MAPPING

For Balanced Low Entropy Attack, we need to obtain a label mapping which mainly addresses the following issues, i) maps the GT label to one wrong label; ii) the label mapping is bijective; iii) the sum of the mapping cost is the minimal. To achieve it, we first define a probability confusion between all class pairs as $\breve { C } \in [ 0 , 1 ] ^ { K \times K }$ . The probability confusion is updated in an exponentially moving average fashion using the current posterior predictions. The label mapping $M \in \{ 0 , 1 \} ^ { K \times }$ is then obtained by optimizing the following linear assignment problem. Efficient solver, e.g. Hungarian method, can be employed to solve this problem, as Eq. 9.

$$
\begin{array}{l l} & \hat {M} = a r g \max _ {M} \sum_ {k} \sum_ {q} C _ {k, q} M _ {k, q} \\ s. t. & M _ {k, k} \neq 1, \quad \sum_ {q} M _ {k, q} = 1, \quad M \in \{0, 1 \} ^ {K \times K}, \\ & C _ {k} ^ {t} = \beta C _ {k} ^ {t} + (1 - \beta) \frac {\sum_ {\tilde {x} _ {i} \in \mathcal {B} _ {a}} \mathbb {1} (y _ {i} = k) \cdot h (\tilde {x} _ {i})}{\sum_ {x _ {i} \in \mathcal {B} _ {a}} h (x _ {i})} \end{array}\tag{9}
$$

Here, we also provide the pseudo code of the implementation of BLE Attack, as follow,

$$
\begin{array}{l} \text { def   attack\_objective(self, x, y): } \\ \quad / / x: (B, K) \text { the   predicted   logit   of   poisoned   data } \\ \quad / / y: (B,) \text { the   ground   true   label   of   poisoned   data } \\ \quad / / \text { return   the   attack   loss   value } \end{array}
$$

```python
with torch.no_grad():
    // EMA update C^t_k
    curr_prob_term = scatter_mean(x.softmax(1), y[:, None],
    → dim=0,
    → out=torch.zeros_like(self.class_wise_momentum_prob))
    new_ema_prob = self.class_wise_momentum_prob.clone()
    new_ema_prob[y.unique()] = self.momentum_coefficient *
    → new_ema_prob[y.unique()] + (1 - self.momentum_coefficient) *
    → curr_prob_term[y.unique()]

    new_ema_prob_select = new_ema_prob.clone()
    diag_mask =
    → torch.diag(torch.ones(new_ema_prob_select.shape[0]))
    new_ema_prob_select[diag_mask.bool()] = 0.

    // Find the global optimal mapping M
    label_mapping = y.new_zeros(new_ema_prob_select.shape[0], dtype=torch.long)
    for i in range(new_ema_prob_select.shape[0]):
    biased_prob, biased_class =
    → F.normalize(new_ema_prob_select, dim=-1, p=1).max(dim=-1)
    max_item = biased_prob.argmax(dim=-1)
    label_mapping[max_item] = biased_class[max_item]
    new_ema_prob_select[max_item, :] = 0.
    new_ema_prob_select[:, biased_class[max_item]] = 0.

// BLE attack loss
loss = F.cross_entropy(x, label_mapping[y])
self.current_prob = new_ema_prob.detach()
return loss
```

## A.1.3 DETAILS OF DEFENSE PRACTICES

Here, we provide the details about the defense practices evaluated in Tab. 6 of the main text.

• Entropy Thresholding is implemented through filtering the entropy below 0.05 ∗ log(K), where K is the class number of the dataset.

• Data Augmentation performs the data augmentation used into CoTTA over the input samples and constrain the consistent predictions between the augmented samples and the corresponding original samples.

• EMA Update module allow us to maintain an exponentially moving average updated model to generate robust predictions and used to supervise the online model update, and the EMA momentum is 0.999.

• Stochastic Parameter Restoration is implemented as the module used in CoTTA. We randomly reset the network weights to source model weights with probability p and p is set to 0.01.

## A.1.4 DISTINCTION BETWEEN RTTDP AND TEPA

We would like to highlight the key differences between our proposed RTTDP and TePA protocols as follows,

TePA (Cong et al., 2023) employs a fixed surrogate model before test-time adaptation begins for generating poisoning, which qualifies the method as an offline method. The surrogate model is obtained by training a separate model (different architecture from the target model) using the same source dataset. For example, on TTA for CIFAR10-C, if the target model, i.e. the model deployed for inference and is subject to test-time adaptation, is ResNet18, TePA employs VGG-11 as the surrogate model and trains VGG-11 on the same source training dataset (CIFAR10 clean training set). This is evidenced from the source code released by official repository <sup>1</sup> and the descriptions in TePA "we assume that the adversary has background knowledge of the distribution of the target model’s training dataset. This knowledge allows the adversary to construct a surrogate model with a similar distribution dataset".

TePA employs the fixed surrogate model to generate poisoned dataset $x ^ { \prime } .$ Then generated poisoned dataset is fed to test-time adaptation to update model weights. Afterwards, TTA is further conducted on clean testing data for model update and performance evaluation. The segregation of data poisoning and TTA steps further support the claim that TePA should be classified as an offline approach.

Finally, to ensure fair comparison between TePA with our proposed methods under RTTDP protocol, TePA could be adapted to online fashion and we made such an adaptation to TePA for comparison in Tab. 2, Tab. 3 and Tab. 4 of the main text. Specifically, we use TePA to generate poisoning against the initial surrogate model and inject the generated poisoning into the testing data stream, i.e. placing poisoning in between benign testing batches. In this way, poisoning will affect TTA in an online fashion. We believe this is the most fair way to compare RTTDP with TePA.

## A.1.5 MORE ANALYSIS AND DERIVATIONS ABOUT THE OPTIMIZATION OBJECTIVE

Here, we discuss the transition from the original bi-level optimization objective $( \operatorname { E q } . 2 )$ to our proposed single-level optimization objective (Eq. 4) with a feature consistency constraint.

The original optimization objective for test-time data poisoning is formulated as a bi-level optimization problem, as shown below (equivalent to the meaning of Eq. 2):

$$
\begin{array}{r l} & {\mathcal {B} _ {a} = \arg \min _ {\mathcal {B} _ {a}} E _ {(x, y) \in \mathcal {B} _ {b}} \left[ \mathcal {L} _ {a t k} (h (x; \theta_ {t} ^ {*} (\mathcal {B} _ {a} \cup \mathcal {B} _ {b})), y) \right]} \\ & {\quad s. t. \theta_ {t} ^ {*} (\mathcal {B} _ {a} \cup \mathcal {B} _ {b}) = \arg \min _ {\theta_ {t}} \mathcal {L} _ {t t a} (h (\mathcal {B} _ {a} \cup \mathcal {B} _ {b}; \theta))} \end{array}\tag{10}
$$

The above optimization involves an inner loop where the model adapts to test samples, including poisoned and benign samples, and an outer loop to optimize the attack objective. This structure is computationally intensive and impractical under the constraints of the RTTDP setting. To address this, we provide a detailed step-by-step derivation and explanation below.

1. Discarding the Inner Optimization: In DIA (Wu et al., 2023), the inner optimization is approximated by assuming ${ \theta } _ { t } ^ { * } \approx \theta _ { t }$ , where $\theta _ { t } ^ { * }$ represents the parameters after a full adaptation step, and $\theta _ { t }$ represents the current parameters. This approximation is justified as TTA models typically update minimally during a single minibatch iteration, resulting in minor perturbations to $\theta _ { t } .$ . Thus, the approximation retains practical relevance while simplifying the problem. The formula is derived as (this is also the DIA’s objective),

$$
\mathcal {B} _ {a} = \arg \min _ {\mathcal {B} _ {a}} E _ {(x, y) \in \mathcal {B} _ {b}} \left[ \mathcal {L} _ {a t k} (h (x; \theta_ {t} (\mathcal {B} _ {a} \cup \mathcal {B} _ {b})), y) \right]\tag{11}
$$

2. Surrogate Model for Online Parameters: In the RTTDP protocol, direct access to online model parameters $\theta _ { t }$ is unrealistic. Instead, we replace $\theta _ { t }$ with the surrogate model parameters $\widehat { \theta } _ { t }$ , which are accessible and trained to approximate the online model’s behavior.

$$
\mathcal {B} _ {a} = \arg \min _ {\mathcal {B} _ {a}} E _ {(x, y) \in \mathcal {B} _ {b}} \left[ \mathcal {L} _ {a t k} (h (x; \hat {\theta} _ {t} (\mathcal {B} _ {a} \cup \mathcal {B} _ {b})), y) \right]\tag{12}
$$

3. Removing the access to $\boldsymbol { B } _ { b } \colon$ In the RTTDP protocol, the adversary is prohibited from observing benign users’ samples when generating poisoned samples. Consequently, the $B _ { b }$ term is excluded from the optimization objective. In the main text, we introduce to leverage $\mathcal { B } _ { a b }$ to replace $B _ { b }$ , where $\mathcal { B } _ { a b }$ represents the adversary benign samples before they are poisoned.

$$
\mathcal {B} _ {a} = \arg \min _ {\mathcal {B} _ {a}} E _ {(x, y) \in \mathcal {B} _ {a b}} \left[ \mathcal {L} _ {a t k} (h (x; \hat {\theta} _ {t} (\mathcal {B} _ {a} \cup \mathcal {B} _ {a b})), y) \right]\tag{13}
$$

where $\hat { \theta } _ { t } ( B _ { a } \cup B _ { b } )$ indicates forwarding $B _ { a } \cup B _ { b }$ to update the BN statistics. This objective would lead to a trivial solution that $\scriptstyle { B _ { a } }$ is effective only for the current $B _ { a b }$ data through easily introducing biased normalization in each BN layer, and it has little effect while $\scriptstyle { B _ { a } }$ and $\mathcal { B } _ { a b }$ are in seperated batch. Therefore, it would waste a half of attack query budget for forwarding these poisoned samples (the benign samples take up half of the batch size).

4. Introducing a feature consistency constraint to improve query utilization: In the main text, we observed the feature distributions of $B _ { a }$ and $B _ { a b }$ and found out that they obviously do not overlap, so we introduced feature consistency constraint to regularize their distributions according to the PAC learning framework in order to merge the two subsets into a single one, and to improve the utilization of the poisoned data query. The final objective is derived as follows, where $P _ { a }$ and $P _ { a b }$ are the shallow feature distributions of $B _ { a }$ and $B _ { a b }$ , respectively.

$$
\mathcal {B} _ {a} = \arg \min _ {\mathcal {B} _ {a}} E _ {(x, y) \in \mathcal {B} _ {a}} \left[ \mathcal {L} _ {a t k} (h (x; \hat {\theta} _ {t} (\mathcal {B} _ {a})), y) \right], s. t. D (P _ {a}, P _ {a b}) = 0\tag{14}
$$

To this end, we can fully utilize the budget of all poisoned data query to generate poisoned data. The experimental results show that the attack performance of the attack objective will be significantly improved after using this regularization term.

In-distribution Attack Objective from a TTA Perspective: Our proposed objective leverages the dependence of TTA models on self-training mechanisms, which aim to maximize confidence on pseudo-labels for adaptation. When the TTA model adapts to poisoned samples, it learns and reinforces incorrect associations. This creates a vulnerability, as future test samples with similar shallow feature distributions are more likely to be misclassified by the online model. Since TTA methods iteratively adapt using incoming test samples, our approach leverages this dependency to propagate the error induced by poisoned samples throughout the adaptation process.

## A.1.6 DETAILED POISONING & TRAINING ALGORITHM

We present the overall algorithm for generating poisoned data and surrogate model update in Alg. 1

## A.2 EXPERIMENTAL SETUPS OF DIA, TEPA AND RTTDP

We revisit the experimental setups of the previous methods, i.e. DIA (Wu et al., 2023) and TePA Cong et al. (2023), explain the differences under our RTTDP protocol, and justify the adaptations we made to ensure fair comparisons.

Commonalities among the different protocols: The three protocols, TePA, DIA, and RTTDP, share several overarching goals and assumptions. First, all protocols aim to evaluate the adversarial risks posed to Test-Time Adaptation (TTA) by injecting poisoned samples into the test data stream. Second, all protocols allow the adversary to obtain the source model, since the source model is usually the well-known pre-trained model, e.g., ImageNet pre-trained ResNet, and the open-source foundation model, e.g., DINOv2, SAM.

Key Differences among Protocols: Despite sharing some commonalities, the protocols diverge significantly in their attack setups.

In the TePA protocol, poisoned samples are generated by maximizing the entropy of the adversary’s crafted samples with respect to the source model’s predictions. These poisoned samples are injected into the TTA pipeline before any benign users’ samples are processed, simulating an offline attack scenario. However, this approach is unrealistic in real-world settings, where adversaries cannot fully control the sequence of test samples in advance.

In contrast, the DIA protocol generates poisoned samples by optimizing them to maximize the cross-entropy loss of benign samples belonging to other users. DIA assumes direct access to the online model’s parameters and the ability to observe other users’ benign samples. Poisoned samples are injected into the TTA pipeline alongside the corresponding benign users’ samples. However, this protocol has significant limitations in realistic settings. In practice, adversaries typically lack access to or control over the online model’s parameters. Additionally, it is highly improbable for adversaries to observe benign users’ samples, let alone the validation samples required for optimizing poisoning objectives.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1: The pipeline of RTTDP

input : A minibatch of testing samples $\mathcal{B}_t = \mathcal{B}_{ab} \cup \mathcal{B}_b$, where $\mathcal{B}_{ab}$ is the adversary benign subset that is preparing for crafting poisoned data and $\mathcal{B}_b$ is other users' benign subset.

Test-time adaptation model: $h(x; \theta_t)$,

Surrogate model used by adversary: $h(x; \hat{\theta}_t)$.

Attack Objective: $\mathcal{L}_{atk}$

// generate attack samples through surrogate model.

if $\mathcal{B}_a \neq \emptyset$ then

initialize $\epsilon = \{0\}^{B \times H \times W \times 3}$, where $B = |\mathcal{B}_{ab}|$.

initialize $\lambda = \{0\}^L$, where $L$ is the number of feature layers.

for $i := 1$ to 40 do

$\mathcal{B}_a = \{\tilde{x}_i; \tilde{x}_i = x_i + \epsilon_i\}$

calculate the attack loss: $loss_1 = \frac{1}{|\mathcal{B}_a|} \sum_{\tilde{x}_i \in \mathcal{B}_a} \mathcal{L}_{atk}(\tilde{x}_i)$.

obtain all feature maps $\{\tilde{z}_i^l\}_{l=1...L}$ before the normalization layers.

calculate the feature consistency regularization term as Eq. 6:

$loss_2^l = \sum_{\tilde{x}_i \in \mathcal{B}_a} KLD(\mathcal{N}(\mu_i^l, \Sigma_i^l) || \mathcal{N}(\tilde{\mu}_i^l, \tilde{\Sigma}_i^l))$

construct the final optimized objective as Eq. 6:

$\mathcal{L} = loss_1 + \frac{1}{L} \sum_l^L \lambda_l \cdot loss_2^l$

update the adversarial noise:

$\epsilon' = \epsilon - \alpha * sign[\nabla_\epsilon \mathcal{L}]$, where $\alpha$ is PGD attack step size of 0.01.

$\epsilon_i = clamp(x_i + \epsilon'_i, 0, 1) - x_i$, $x_i \in \mathcal{B}_a$.

update the $\lambda_l$:

$\lambda_l = \lambda_l + 0.001 \cdot \nabla_{\lambda_l} \mathcal{L}$

// feed into TTA model and obtain the prediction.

$y_i = h(x_i, \theta_t)$, $x_i \in \mathcal{B}_t$

// update the surrogate model if $\mathcal{B}_a \neq \emptyset$.

if $\mathcal{B}_a \neq \emptyset$ then

$\hat{\theta}_{t,0} = \hat{\theta}_t$

for $j := 1$ to iters do

$p_i^a = h(x_i^a, \theta_t)$, $x_i^a \in \mathcal{B}_a$.

$\hat{p}_i^a = h(x_i^a, \hat{\theta}_{t,j-1})$, $x_i^a \in \mathcal{B}_a$.

calculate the distillation loss $\mathcal{L}_{dist}$ as Eq. 1.

$\hat{\theta}_{t,j} = \hat{\theta}_{t,j-1} - lr * \nabla_{\hat{\theta}} \mathcal{L}_{dist}$ $\hat{\theta}_{t+1} = \hat{\theta}_{t,iters}$.
</div>

The proposed RTTDP protocol addresses these limitations by operating under more realistic assumptions. In RTTDP, the adversary neither has access to other users’ benign samples nor the parameters of the online model. Instead, RTTDP employs a surrogate model, initialized as the source model, to generate poisoned samples. This surrogate model is iteratively updated based on feedback from previously injected poisoned samples. Poisoned samples are then injected into the TTA pipeline, either uniformly or non-uniformly, depending on the attack frequency in RTTDP protocol.

Adaptations of Competing Methods to RTTDP protocol: To ensure fair comparisons under RTTDP protocol, we made the following adjustments to the competing methods:

For TePA method, we preserved TePA’s original poisoning objective, i.e. maximizing entropy, but adapted the poisoned data injection strategy from an offline manner to an online manner, i.e. placing poisoning in between benign testing batches according to RTTDP.

For DIA method, (1) Replacing Online Model Parameters: DIA’s original objective relies on online model parameters, which are inaccessible in RTTDP. We replaced these parameters with the initial surrogate model, i.e. source model. (2) No Access to Benign Users’ Samples for Optimization: DIA uses benign users’ samples as optimization targets in its original setup. To meet RTTDP’s constraints, we split $B _ { a b }$ into two equal subsets, $B _ { a b } ^ { p }$ and $B _ { a b } ^ { \breve { b } } .$ , with a 1:1 ratio. We then generate poisoned samples B<sup>p</sup> by maximizing the cross-entropy loss of $B _ { a b } ^ { b }$ . The specific formula can be found in Eq. 15.

## A.3 ADDITIONAL DETAILS FOR EXPERIMENT

Benchmark TTA Methods: We investigate several state-of-the-art TTA methods under our RTTDP protocol to evaluate their adversarial robustness. Source serves as the baseline for inference performance without adaptation. TENT (Wang et al., 2020) updates BN parameters through minimizing entropy. RPL (Rusak et al., 2022) performs self-training with a generalized cross-entropy (GCE) loss, which aids in more robust adaptation under label noise. EATA (Niu et al., 2022) minimizes entropy with the Fisher regularization term to prevent forgetting knowledge from the source domain. TTAC (Su et al., 2022) adapts all backbone parameters by jointly optimizing global and class-wise distribution alignment with the source distribution. SAR (Niu et al., 2023) updates BN parameters with a sharpness-aware optimizer to filter out noisy labels and help escape local minima. CoTTA (Wang et al., 2022) leverages a teacher-student structure, optimizing all parameters of the student model and updating the teacher model using an exponential moving average. To better prevent forgetting during continual adaptation, it incorporates parameter random resetting and data augmentation methods. ROID (Marsden et al., 2024) updates BN parameters with loss of self-label refinement (SLR) weighed by certainty and diversity while continually weighting the online model and the source model to prevent forgetting.

Evaluation Protocol: We devise a evaluation plan respecting the realistic test-time data poisoning criteria. First, we investigate the frequency of injecting poisoned data. The “Uniform” scheme indicates that the poisoned minibatch is uniformly present in the test data stream, simulating the scenario that the adversary is periodically injecting the poisoned data. We further evaluate “Non-Uniform” scheme by allowing the adversary to concentrate the attack budget within a short period of time. We fix the overall attack budget as $\begin{array} { r } { r = \frac { \left| B _ { a } \right| } { \left| B _ { a } \right| + \left| B _ { b } \right| } } \end{array}$ throughout the experiments. We report the attack success rate as the evaluation metric, which is measured as the percentage of misclassified benign samples in the benign subset $B _ { b }$ . Additionally, for easier comparison, we also calculate the average error rate (higher the better) and the average ranking (lower the better) for each poisoning method.

Hyperparameters: For all competing methods, we employ the 40 steps $L _ { \infty }$ PGD attack to generate poisoned data. The maximum perturbation budget b is 0.3 and the attack step size is 0.01. Additionally, within each PGD iteration, we update $\lambda _ { l }$ via $\lambda _ { l } ^ { \prime } = \lambda _ { l } + 0 . 0 0 1 \cdot \nabla _ { \lambda _ { l } } \mathcal { L }$ for Eq. 6, where $\lambda _ { l }$ is initialized as zero before PGD attack. Unless otherwise noted, the overall attack budget r is 50% throughout the experiment. For surrogate model distillation module, we adopt SGD optimizer with 0.1 learning rate for 10 iterations to update the surrogate model in each update stage.

Implementation Details: For a fair comparison, we implement various data poisoning methods within a unified poisoning framework. This framework utilizes a 40-step Projected Gradient Descent (PGD Boyd & Vandenberghe (2004)) optimization process tailored to the respective objectives of each method. The poisoned samples generated are then injected into the TTA pipeline in an online manner, adhering to the RTTDP protocol. Specifically, the respective objectives of different competing poisoning methods are shown as follows,

• DIA (Wu et al., 2023):

$$
\mathcal {B} _ {a} ^ {p} = \arg \min _ {\mathcal {B} _ {a} ^ {p}} E _ {(x, y) \in \mathcal {B} _ {a b} ^ {b}} \left[ - C r o s s E n t r o p y L o s s (h (x; \hat {\theta} _ {0} (\mathcal {B} _ {a b} ^ {b} \cup \mathcal {B} _ {a} ^ {p})), y) \right]\tag{15}
$$

• TePA (Cong et al., 2023):

$$
\mathcal {B} _ {a} = \arg \min _ {\mathcal {B} _ {a}} E _ {(x, y) \in \mathcal {B} _ {a}} \left[ - E n t r o p y (h (x; \hat {\theta} _ {0} (\mathcal {B} _ {a}))) \right]\tag{16}
$$

• MaxCE (Madry et al., 2018):

$$
\mathcal {B} _ {a} = \arg \min _ {\mathcal {B} _ {a}} E _ {(x, y) \in \mathcal {B} _ {a}} \left[ - C r o s s E n t r o p y L o s s (h (x; \hat {\theta} _ {0} (\mathcal {B} _ {a})), y) \right]\tag{17}
$$

• Unlearnable Examples (Huang et al., 2021):

$$
\mathcal {B} _ {a} = \arg \min _ {\mathcal {B} _ {a}} E _ {(x, y) \in \mathcal {B} _ {a}} \left[ C r o s s E n t r o p y L o s s (h (x; \theta_ {i n i t} (\mathcal {B} _ {a})), y) \right]\tag{18}
$$

• Adversarial Poisoning (Fowl et al., 2021):

$$
\mathcal{B}_{a} = \arg \min_{\mathcal{B}_{a}}E_{(x,y)\in \mathcal{B}_{a}}\left[CrossEntropyLoss(h;\hat{\theta}_{0}(\mathcal{B}_{a}),\hat{y})\right],\text{where}\hat{y} = (y + 1)\% K.\tag{19}
$$

• NHE Attack (Ours):

$$
\mathcal {B} _ {a} = \arg \min _ {\mathcal {B} _ {a}} \max _ {\lambda} E _ {(x, y) \in \mathcal {B} _ {a}} \left[ \mathcal {L} _ {a t k} ^ {N H E} (x; \hat {\theta} _ {t} (\mathcal {B} _ {a})) + \lambda \mathcal {L} _ {r e g} \right]\tag{20}
$$

• BLE Attack (Ours):

$$
\mathcal {B} _ {a} = \arg \min _ {\mathcal {B} _ {a}} \max _ {\lambda} E _ {(x, y) \in \mathcal {B} _ {a}} \left[ \mathcal {L} _ {a t k} ^ {B L E} (x; \hat {\theta} _ {t} (\mathcal {B} _ {a})) + \lambda \mathcal {L} _ {r e g} \right]\tag{21}
$$

where $\widehat { \theta } _ { 0 }$ indicates the initial surrogate model parameters, $\theta _ { i n i t }$ indicates the randomly initialized parameters and K is the number of the category in the dataset. Since under the RTTDP protocol the real-time model parameters are unavailable to access, we leverage the initial surrogate model, to replace the online model they might have used in their original paper, as the threat model for the competing methods. The surrogate model is initialized as source model. For our proposed methods, we employ the proposed surrogate model distillation module to update the surrogate model, and during each PGD iteration, the variables $B _ { a }$ and λ are updated simultaneously using gradient descent for $B _ { a }$ and gradient ascent for λ, respectively. More details about our proposed methods can be found in Alg. 1.

## A.4 ADDITIONAL EMPIRICAL ANALYSIS

## A.4.1 COMPARISON WITH ADVERSARIAL ATTACK METHODS

Adversarial attack methods are designed to generate perturbations on input samples to mislead the model into making incorrect predictions. Here, we aim to investigate whether the adversarial effects of poisoned samples, generated using advanced adversarial attack methods (Madry et al., 2018; Croce & Hein, 2020; Chen et al., 2022), can be effectively transferred to benign users’ samples under the RTTDP protocol.

We conduct the experiments on CIFAR10-C and ImageNet-C datasets with a Uniform attack frequency under our proposed RTTDP protocol. The results are shown in Tab. 8 and Tab. 9. We make the following observations. (i) The objectives of adversarial attack methods and data poisoning methods differ fundamentally. Adversarial attack methods focus on generating adversarial noise to mislead model predictions on the perturbed test samples. In contrast, data poisoning methods aim to inject carefully crafted poisoned samples to degrade the model’s performance on subsequent benign samples after adaptation. (ii) While AutoAttack (Croce & Hein, 2020) represents a more advanced adversarial attack method, its performance is inferior to that of MaxCE-PGD (Madry et al., 2018) on ImageNet-C. (iii) Furthermore, certain complex adversarial attack methods, such as GMSA-MIN and GMSA-AVG (Chen et al., 2022), require generating adversarial perturbations separately for each class, a process that incurs substantial computational costs and limits scalability (which is why these methods are excluded from comparison on ImageNet-C), and still fall short compared to the efficacy of our proposed data poisoning methods.

Table 8: Comparison with different adversarial attack methods with our proposed data poisoning methods on CIFAR10-C dataset under the RTTDP protocol.

<table><tr><td>Attack Objective</td><td>TENT</td><td>EATA</td><td>SAR</td><td>ROID</td><td>Avg</td></tr><tr><td>NoAttack</td><td>19.72</td><td>18.03</td><td>18.94</td><td>16.37</td><td>18.27</td></tr><tr><td>MaxCE-PGD (Madry et al., 2018)</td><td>18.55</td><td>18.17</td><td>19.50</td><td>18.57</td><td>18.70</td></tr><tr><td>AutoAttack (Croce &amp; Hein, 2020)</td><td>26.29</td><td>19.12</td><td>19.56</td><td>18.67</td><td>20.91</td></tr><tr><td>GMSA-MIN (Chen et al., 2022)</td><td>35.92</td><td>22.78</td><td>19.99</td><td>18.65</td><td>24.33</td></tr><tr><td>GMSA-AVG (Chen et al., 2022)</td><td>38.80</td><td>21.89</td><td>19.95</td><td>18.51</td><td>24.79</td></tr><tr><td>BLE Attack (Ours)</td><td>54.07</td><td>45.20</td><td>26.80</td><td>19.06</td><td>36.28</td></tr><tr><td>NHE Attack (Ours)</td><td>73.86</td><td>29.73</td><td>24.56</td><td>17.00</td><td>36.29</td></tr></table>

Table 9: Comparison with different adversarial attack methods with our proposed data poisoning methods on ImageNet-C dataset under the RTTDP protocol.

<table><tr><td>Attack Objective</td><td>TENT</td><td>SAR</td><td>CoTTA</td><td>ROID</td><td>Avg</td></tr><tr><td>NoAttack</td><td>63.49</td><td>61.26</td><td>63.02</td><td>53.42</td><td>60.30</td></tr><tr><td>MaxCE-PGD (Madry et al., 2018)</td><td>62.64</td><td>61.66</td><td>68.83</td><td>59.89</td><td>63.26</td></tr><tr><td>AutoAttack (Croce &amp; Hein, 2020)</td><td>64.48</td><td>61.42</td><td>63.03</td><td>54.78</td><td>60.93</td></tr><tr><td>BLE Attack (Ours)</td><td>68.04</td><td>64.31</td><td>66.40</td><td>57.10</td><td>63.96</td></tr><tr><td>NHE Attack (Ours)</td><td>78.03</td><td>72.58</td><td>66.40</td><td>57.72</td><td>68.68</td></tr></table>

## A.4.2 ABLATION STUDY ON QUERY COUNTS

Regarding varying query attempts, we add an additional evaluation as follows. Nonetheless, we want to highlight that the query attempts do not have to be limited for our method because all queries are submitted to the surrogate model rather than the online model. More queries simply makes generating poisoning slower. In this study, we vary the query steps from 10 to 60 for the projected gradient descent optimization (Boyd & Vandenberghe, 2004). We evaluate varying attack query counts for two TTA methods under their respective strongest attack objectives. The results in the Tab. 10 are obtained on CIFAR10-C dataset with a Uniform attack frequency. We make the following observations. (i) Increasing the number of queries could improve the performance at a low query budget. (ii) When the budget is increased to beyond 40 queries, the performance saturates. We draw the conclusion that allowing sufficient queries to the surrogate model is necessary for generating effective data poisoning, and, importantly, this procedure will not create alert to the online model.

## A.4.3 ANALYSIS ON SYMMETRIC KLD USED FOR DISTILLING SURROGATE MODEL

In this work, we adopt the common practice of symmetrizing the Kullback-Leibler Divergence (KLD) to ensure balanced alignment between distributions in the surrogate model distillation. Following the definitions provided in the main text, the forward KLD is expressed as $K L D ( h ( x _ { i } ; \theta _ { t } ) | | h ( x _ { i } ; \hat { \theta } _ { t } ) )$ 2 while the reverse KLD is defined as $K L D ( h ( x _ { i } ; \hat { \theta } _ { t } ) | | h ( x _ { i } ; \theta _ { t } ) )$ .

Table 10: The ablation study on query counts. These results are obtained on CIFAR10-C dataset with a Uniform attack frequency under RTTDP protocol. We choose 40 queries throughout the experiments.

<table><tr><td>TTA Method</td><td>10</td><td>20</td><td>30</td><td>40</td><td>50</td><td>60</td></tr><tr><td>TENT (NHE Attack)</td><td>66.95</td><td>74.36</td><td>74.34</td><td>73.86</td><td>73.51</td><td>73.66</td></tr><tr><td>EATA (BLE Attack)</td><td>35.73</td><td>39.70</td><td>42.36</td><td>45.20</td><td>45.99</td><td>45.89</td></tr></table>

Forward KLD emphasizes penalizing discrepancies where the distilled (surrogate) model $\widehat { \theta } _ { t }$ assigns low probability to samples that the source (real-time target) model θ deems important. It encourages the distilled model to mimic the behavior of the target model by focusing on areas of high confidence in $\theta \mathbf { \bar { s } }$ posterior.

Reverse KLD, in contrast, focuses on matching $\theta \mathbf { \bar { s } }$ predictions where $\hat { \theta }$ assigns high probabilities. This can result in sharper, more focused distributions but might dismiss less probable regions of $\theta \mathrm { { ^ { \circ } s } }$ posterior.

The symmetric KLD balances the above two objectives. The forward KLD may be more suitable when surrogate model is significantly smaller than the target model and the objective is to allow the surrogate model to mimic the target model’s certainty. When the surrogate model is of the same capacity with target model, using the symmetric KLD may better align the two models in both high confident and low confident predictions. In this work, the capacity of surrogate is similar to target model. Thus, we hypothesize that the symmetric KLD could be better.

We further use empirical observations in the Tab. 11 below to support the hypothesis. With symmetric KLD the performance is slightly better than using the forward KLD.

Table 11: Comparison between Symmetric KLD and Forward KLD used for surrogate model distillation. These results are obtained on CIFAR10-C dataset with a Uniform attack frequency under RTTDP protocol.

<table><tr><td>TTA Method</td><td>Symmetric KLD</td><td> $KLD(h(x_i;\theta_t)||h(x_i;\hat{\theta}_t))$ </td></tr><tr><td>TENT (NHE Attack)</td><td>73.86</td><td>74.35</td></tr><tr><td>EATA (BLE Attack)</td><td>45.20</td><td>43.99</td></tr><tr><td>SAR (BLE Attack)</td><td>26.80</td><td>26.35</td></tr></table>

Nevertheless, we do acknowledge that both symmetric KLD and forward KLD give competitive results. The choice depends on computation affordability and empirical observations.

## A.4.4 DIFFERENT ATTACK BUDGETS

We further evaluate the effectiveness of proposed poisoning approach under different attack budgets. Specifically, we evaluated at $r = 0 . 1 , r = 0 . 2$ and $r = 0 . 5$ . We clearly observe that both high entropy and low entropy attacks are effective regardless of attack budgets.

## A.4.5 VISUALIZATION OF POISONED SAMPLES

We visualize selected samples before and after test-time data poisoning in Fig. 4. The high corruption level makes the adversarial noise less noticeable, suggesting the poisoned data could even evade human inspection.

Table 12: Comparing the attack performance of test-time data poisoning under different attack budgets.

<table><tr><td>TTA</td><td>Attack Obj.</td><td>0.1</td><td>0.2</td><td>0.5</td></tr><tr><td rowspan="3">TENT</td><td>No Attack</td><td>20.72</td><td>20.39</td><td>19.72</td></tr><tr><td>BLE Attack</td><td>22.44</td><td>27.60</td><td>54.07</td></tr><tr><td>NHE Attack</td><td>39.20</td><td>62.19</td><td>73.86</td></tr><tr><td rowspan="3">EATA</td><td>No Attack</td><td>17.99</td><td>17.76</td><td>18.03</td></tr><tr><td>BLE Attack</td><td>22.20</td><td>28.29</td><td>45.20</td></tr><tr><td>NHE Attack</td><td>19.59</td><td>20.10</td><td>29.73</td></tr><tr><td rowspan="3">SAR</td><td>No Attack</td><td>18.95</td><td>18.90</td><td>18.94</td></tr><tr><td>BLE Attack</td><td>19.90</td><td>21.30</td><td>26.80</td></tr><tr><td>NHE Attack</td><td>19.33</td><td>20.74</td><td>24.56</td></tr></table>

![](images/719238d3f1be8c3a55879f5c48976c11e8ecaf2aa42fe66110397abdb6f9776d.jpg)  
Figure 4: Visualizing of selected samples before and after test-time data poisoning.