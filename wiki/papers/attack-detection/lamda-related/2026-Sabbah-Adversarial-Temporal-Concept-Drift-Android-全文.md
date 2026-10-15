---
title: "2026-Sabbah-Adversarial-Temporal-Concept-Drift-Android"
date: 2026-10-15
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/lamda-related/2026-Sabbah-Adversarial-Temporal-Concept-Drift-Android.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Adversarial Vulnerability Under Temporal Concept Drift: A Longitudinal Study of Android Malware Detection

Ahmed Sabbah<sup>a</sup>, Mohammed F. Kharma<sup>a</sup>, Radi Jarrar<sup>a</sup>, Samer Zein<sup>a</sup>, David Mohaisen<sup>b,∗</sup>

<sup>a</sup>Department of Computer Science, Birzeit University, P.O. Box 14, Birzeit, P627, West Bank, Palestine

<sup>b</sup>Department of Computer Science, University of Central Florida, 4328 Scorpius St., Building 116, Room 246, Orlando, 32816, FL, USA

## Abstract

As intelligent malware detection systems are deployed in evolving mobile ecosystems, both benign and malicious applications change in structure and behavior, inducing non-stationary data distributions that challenge long-term model reliability. In parallel, adversarial perturbations expose additional vulnerabilities in machine learning–based detectors. Despite extensive work on concept drift and adversarial robustness independently, their interaction in adaptive intelligent systems remains insuficiently characterized.

We present a longitudinal, drift-aware evaluation of adversarial robustness across more than a decade of Android applications using static and dynamic feature representations extracted from emulator and real-device executions. The dataset is organized into yearly slices and evaluated under three deployment protocols that emulate realistic learning scenarios: (1) same-year training and testing, (2) cross-year deployment without model updates, and (3) expanding-window retraining with cumulative historical data. Across multiple classifier families, adversarial examples are generated using FGSM and SPSA under feasibility constraints. We measure clean performance, Adversarial Accuracy (AA), Attack Success Rate (ASR), and introduce temporal linkage metrics—RobustDrop, ∆ASR, and Adversarial Amplification Factor (AAF)—to quantify the relationship between distribution shift and robustness degradation.nResults show that temporal separation is associated with reduced adversarial robustness under the evaluated transferbased feature-space setting. As the train–test gap increases, clean accuracy and adversarial accuracy decline, while attack success exhibits configurationdependent increases, particularly under FGSM perturbations and static features. Expanding-window retraining mitigates, but does not eliminate, robustness loss under continued distributional evolution. These findings indicate that temporal drift should be considered when assessing the long-term robustness of intelligent detection systems under evolving data distributions and highlight the need for drift-aware robustness assessment frameworks in long-lived adversarial environments.

Keywords: Malware detection; adversarial examples; concept drift; measurements.

## 1. Introduction

The deployment of machine learning–based malware detectors in realworld environments exposes them to evolving data distributions, violating the stationarity assumption underlying conventional ofline supervised learning [1, 2, 3, 4, 5]. Intelligent decision systems operating on security data streams must contend with inherent non-stationarity, including concept drift, where the conditional relationship between inputs and labels changes as new threats, platforms, and user behaviors emerge [6, 7]. When such drift is not explicitly monitored and accommodated, models that initially achieve strong performance may degrade over time, increasing missed detections and undermining the reliability of long-lived intelligent systems.

Android provides a representative and operationally relevant setting for studying learning under distribution shift. As the dominant mobile operating system and a primary malware target [8, 9, 8, 10, 11, 12], it has motivated extensive research on data-driven detection using static, dynamic, and hybrid feature representations across both traditional and deep learning architectures [13, 14, 15]. Although many studies report high accuracy on curated benchmarks, most evaluations implicitly assume that training and test samples are drawn from the same temporal distribution. This assumption limits insight into long-term system behavior and the robustness of intelligent detectors deployed in evolving environments.

Recent work has begun to revisit this stationarity assumption by examining temporal efects in Android malware detection and related domains. Concept drift has been characterized at both dataset and behavioral levels using time-indexed collections such as KronoDroid and other longitudinal datasets [16, 17, 18]. These studies demonstrate that performance can decline when models are evaluated on future time windows or across changing environments, and that improper temporal partitioning may introduce leakage and optimistic bias [19, 20]. However, prior analyses largely emphasize clean-data performance and mitigation strategies, leaving the relationship between temporal distribution shift and adversarial vulnerability insuficiently explored from the perspective of robust intelligent systems.

In parallel, adversarial machine learning has shown that small, carefully crafted perturbations can induce misclassification across a wide range of modern models [21, 22, 23]. Within malware detection, classifiers can be evaded through both feature-space and problem-space manipulations [24, 25]. Yet most adversarial evaluations assume a fixed underlying data distribution and do not account for how vulnerability profiles may evolve as the datagenerating process shifts over time.

Consequently, two lines of research have progressed largely independently: ① the study of temporal degradation in malware detectors under concept drift and ② the analysis of adversarial evasion under static training conditions. Their interaction in time-evolving deployment scenarios remains insuficiently characterized. In particular, it is unclear whether increasing temporal separation systematically amplifies adversarial vulnerability beyond its impact on clean performance, and whether incremental retraining strategies that partially address drift also improve robustness or reshape the efective attack surface.

In this study, we investigate this interaction using static and dynamic feature representations extracted from a temporally ordered Android dataset spanning multiple years, including executions on both emulators and real devices. We evaluate two deployment protocols that emulate realistic learning scenarios: (i) a cross-year setting, where a model trained on a single year is evaluated on subsequent years without updates, and (ii) an expandingwindow setting, where the training set grows cumulatively over time to incorporate newly observed data. Our contributions are as follows.

• We present a longitudinal evaluation of intelligent malware detection systems under non-stationary data distributions. Using a time-ordered dataset with static and dynamic feature representations, we systematically quantify how predictive performance and adversarial robustness evolve as the temporal gap between training and evaluation increases under cross-year and expanding-window learning protocols.

• We conduct a drift-aware adversarial robustness analysis using transferbased feature-space attacks. Surrogate models are trained on temporally consistent splits, and adversarial examples are generated via FGSM and SPSA under explicit feasibility constraints. Robustness is assessed across diverse classifier families, including RF, GB, KNN, CNN, RNN, LSTM, and GRU, to capture heterogeneous learning behaviors.

• We define and use drift–robustness linkage metrics, RobustDrop, ∆ASR, and the Adversarial Amplification Factor (AAF), as temporal contrast measures relative to the same-year baseline. Unlike reporting AA and ASR alone for each train–test pair, these metrics make robustness loss comparable across training years, feature spaces, attacks, and deployment protocols.

• We comparatively analyze static deployment (cross-year) and adaptive retraining (expanding-window) strategies. While cumulative retraining mitigates degradation in both clean and adversarial performance, it does not fully restore same-year robustness, highlighting persistent reliability challenges in long-lived intelligent detection systems.

Organization. Section 2 outlines the motivation and formalizes the research questions in the context of learning under non-stationary and adversarial conditions. Section 3 reviews concept drift and its underlying causes, with emphasis on distributional evolution in adaptive intelligent systems. Section 4 surveys prior work on temporal robustness and adversarial vulnerability. Section 5 describes the experimental methodology, including the longitudinal dataset construction, feature representations, temporal evaluation protocols, learning models, adversarial generation procedures, and robustness metrics. Section 6 presents the empirical findings and analyzes performance trends across temporal and adversarial settings. Section 7 discusses threats to validity and experimental limitations. Section 8 concludes the paper and outlines implications for drift-aware robustness evaluation in evolving intelligent systems.

## 2. Motivation and Research Questions

Intelligent malware detection systems deployed in real-world environments operate under non-stationary conditions, where evolving application behavior induces temporal distribution shift. Such non-stationarity challenges the reliability of learned decision boundaries over time. While prior work has examined concept drift and adversarial evasion independently, their interaction in adaptive, time-evolving deployment scenarios remains insuficiently characterized from a systems perspective.

## Research Questions.

• RQ1: How does temporal concept drift afect predictive performance as the train–test year gap increases in longitudinal learning settings?

• RQ2: How does adversarial vulnerability evolve under increasing temporal separation between training and evaluation data?

• RQ3: What quantitative relationship exists between drift-induced performance degradation and adversarial vulnerability, and to what extent can expanding-window retraining mitigate this interaction in adaptive learning systems?

Temporal Evaluation. To investigate these questions, we design three complementary deployment protocols that emulate realistic intelligent system lifecycles:

① Same-year. Train on year Y and evaluate on held-out data from $Y$ establishing an in-distribution reference for both predictive accuracy and adversarial robustness.

② Cross-year. Train on year $Y _ { 1 }$ and evaluate on future years $Y _ { 2 } ~ > ~ Y _ { 1 }$ exposing a fixed model to distributional evolution without adaptation.

③ Expanding-window. Train cumulatively on data up to year $Y _ { i }$ and evaluate on $Y _ { i + 1 }$ , emulating periodic retraining with all historically available observations.

For each protocol, adversarial examples are generated using FGSM and SPSA under explicit feature-space feasibility constraints. We report predictive accuracy, Adversarial Accuracy (AA), and Attack Success Rate (ASR), and employ temporal linkage metrics (RobustDrop, ∆ASR, AAF) to systematically quantify the interaction between distributional shift and adversarial vulnerability in evolving learning environments.

## 3. Concept Drift

Concept drift refers to temporal changes in the joint distribution $P ( x , y )$ of features x and labels y [26]. In non-stationary learning environments, such distributional evolution can substantially degrade predictive performance when models trained on historical data are deployed on future observations. From the perspective of intelligent systems, concept drift challenges the stability of learned decision boundaries and necessitates evaluation frameworks that account for time-dependent data generation processes.

In Android malware detection, drift may arise from multiple sources, including API evolution, changes in application development practices, behavioral shifts in benign applications, and the emergence, mutation, or disappearance of malware families. These factors induce structural and behavioral changes in feature distributions over time, afecting both classification performance and robustness properties.

Connection to adversarial settings. In this work, we distinguish natural temporal drift from test-time adversarial perturbations. Natural drift arises from ecosystem changes over time, such as platform evolution, benign application behavior, and malware-family changes. Adversarial perturbations do not create drift in our longitudinal dataset, instead, they test whether models trained on earlier distributions become more sensitive to constrained feature changes when evaluated on future data. Thus, our study examines how adversarial vulnerability changes under naturally evolving temporal distributions, rather than claiming that individual adversarial examples cause real drift.

Root Causes. Following Xiang et al. [27], drift can be categorized into three principal forms:

• Virtual drift: $P _ { t _ { 0 } } ( x ) \neq P _ { t _ { 1 } } ( x )$ while $P _ { t _ { 0 } } ( y \mid x ) = P _ { t _ { 1 } } ( y \mid x )$ . Here, the marginal feature distribution shifts over time, but the underlying conditional decision boundary remains stable. In such cases, performance degradation may result from representation shift rather than changes in class semantics.

• Real drift: $P _ { t _ { 0 } } ( x ) = P _ { t _ { 1 } } ( x )$ while $P _ { t _ { 0 } } ( y \mid x ) \neq P _ { t _ { 1 } } ( y \mid x )$ . The conditional relationship between features and labels changes, indicating that previously learned decision boundaries are no longer valid.

• Hybrid drift: Both $P ( x )$ and $P ( y \mid x )$ change simultaneously. This scenario is common in dynamic and adversarial environments, where structural feature evolution and shifting class semantics co-occur. The longitudinal setting considered in this work captures such combined efects within the KronoDroid timeline.

Understanding these drift mechanisms is essential for analyzing how predictive performance and adversarial robustness evolve in long-lived intelligent detection systems operating under temporal non-stationarity.

## 4. Related Work

## 4.1. Malware Detection and Concept Drift

Supervised learning methods are commonly developed under the assumption of stationary data distributions. Concept drift, defined as temporal changes in the relationship between inputs and targets [7], challenges this assumption and has motivated research on learning under non-stationarity [28, 29]. In Android malware detection, numerous studies demonstrate the effectiveness of machine learning approaches while recognizing the impact of temporal evolution on predictive performance [30]. Chen et al. [31] analyzed feature-space and data-space drift and quantified their respective efects on Android and PE malware detectors across heterogeneous feature representations.

Guerra-Manzanares et al. [32] examined drift using dynamic systemcall features and emphasized the importance of timestamp-aware modeling for capturing temporal evolution. They later proposed a classifier-pool framework for temporally ordered datasets, showing that time-aware training strategies influence detection accuracy [18]. Their adaptive ensemble selection highlights the need for dynamic model management in evolving environments.

Chow et al. [33] investigated the structural causes of drift and attributed performance degradation to the emergence of new malware families and the evolution of existing ones. Complementary work has shown that adversarial manipulation can further exacerbate degradation in drifted settings [34].

Abusnaina et al. [35] evaluated robustness under temporal variation and reported substantial accuracy reductions in non-stationary environments.

Ceschin et al. [28] studied temporal drift using the DREBIN and Andro-Zoo datasets over a nine-year period. Employing Word2Vec and TF-IDF representations with adaptive random forest and stochastic gradient descent classifiers, they demonstrated that evolving data distributions necessitate continual model updates. Their adaptive strategy improved F1 scores by 22.05% on DREBIN and 8.77% on AndroZoo, underscoring the importance of adaptive learning in longitudinal malware detection.

## 4.2. Adversarial Concept Drift and Robustness

In deployed intelligent detection systems, adversaries may deliberately adapt their strategies to evade learned models, inducing distributional shifts referred to as adversarial concept drift [36]. Unlike drift caused by natural ecosystem evolution, adversarial drift results from strategic manipulation intended to degrade model performance.

In Android malware detection, such adaptations include obfuscation, polymorphism, and metamorphism [37], which alter observable artifacts while preserving malicious functionality. Adversarial machine learning further enables evasion through carefully crafted perturbations that exploit model vulnerabilities [38, 39].

Adversarial attack models are typically categorized by the adversary’s knowledge. In white-box settings, access to model parameters allows gradientbased methods such as FGSM [21], PGD [22], and optimization-based attacks [23]. In black-box scenarios, attackers exploit transferability or queryeficient approaches such as ZOO [40] and related adaptations for malware classifiers [41]. Gray-box attacks assume partial knowledge and may involve problem-space manipulations tailored to malware detection [24].

Although many adversarial methods were originally developed for continuous domains, they have been adapted to discrete malware representations, including API calls, permissions, and opcode sequences. Functionalitypreserving strategies include genetic search [42], reinforcement learning–based modification [43], and GAN-based generation [44]. In Android settings, these techniques enable benign code insertion, instruction reordering, or manifest modification to alter feature distributions while maintaining executable behavior [25].

Collectively, existing research has examined temporal degradation and adversarial robustness largely in isolation. Recent studies have begun to examine their intersection in related security domains, such as adversarial perturbations under concept drift in intrusion detection [45]. However, a unified longitudinal evaluation that explicitly quantifies this interaction in Android malware detection remains limited in Android malware detection, where temporal drift, feature-space adversarial robustness, and retraining protocols are rarely evaluated together over long time spans. Our study addresses this gap by evaluating clean and adversarial performance across same-year, cross-year, expanding-window, size-matched expanding-window, and recent window settings using static and dynamic Android malware features.

## 5. Methodology

Figure 2 summarizes the longitudinal evaluation framework, including data collection, feature extraction, yearly partitioning, temporal learning protocols, surrogate-based adversarial generation, and drift-aware robustness metrics. For consistency with the notation introduced in Section 1, we use AA for Adversarial Accuracy, ASR for Attack Success Rate, RobustDrop for adversarial-accuracy reduction relative to the same-year baseline, ∆ASR for the corresponding ASR change, and AAF for the Adversarial Amplification Factor.

## 5.1. Dataset Overview

We use the KronoDroid dataset [16], which provides temporally indexed annual slices spanning 2008 to 2020. The dataset includes static features (permissions and intents) and dynamic features (system call counts) for malware and benign applications collected from both emulators and real devices. The real-device partition contains 36,755 benign samples and 41,382 malware samples, while the emulator partition contains 35,246 benign samples and 28,745 malware samples. Figure 1 shows the yearly class distribution for both partitions. Although the aggregate class balance is moderate, the yearly slices are not uniformly balanced, with noticeable variation in sample counts across years, motivating the use of stratified same-year splits and macro-averaged evaluation metrics.

![](images/5ed74f9b0bfd906185bf789e36d5b875b243b98698cd0157c00317cc1626c58e.jpg)  
Figure 1: Yearly distribution of benign and malware samples in the KronoDroid real-device and emulator partitions from 2008 to 2020.

To enable longitudinal analysis under non-stationarity, we construct peryear subsets based on each application’s last update timestamp, ensuring temporally consistent evaluation splits.

Feature spaces. We evaluate both static and dynamic feature representations, static, including binary permission and intent indicators extracted from the application package, and dynamic features, which are system-call count vectors collected during execution. In our processed data, each partition contains 166 static features and 288 dynamic features. Static features mainly reflect declared application structure and Android API usage, while dynamic features capture runtime behavior and may be more sensitive to execution environment and malware-family evolution over time.

• Validity projection. Dynamic features are constrained to non-negative integers and static features to binary values. After each adversarial update, feature vectors are projected back to the feasible domain to eliminate invalid values.

• Selective standardization. Only dynamic features are standardized using statistics computed from the corresponding training-year split. This stabilizes gradient-based perturbations while preventing temporal leakage. Static features remain unscaled. Perturbations are generated in standardized space and inverted prior to evaluation.

• Bounded edit budgets. Each attack modifies at most $k _ { \mathrm { s t a t i c } } = \left\lceil 0 . 0 5 d _ { \mathrm { s t a t i c } } \right\rceil$ and $k _ { \mathrm { d y n a m i c } } = \left\lceil 0 . 0 5 d _ { \mathrm { d y n a m i c } } \right\rceil$ features. Dynamic updates are further restricted to at most ±1 per coordinate. These constraints maintain validity in the feature representation while enabling a controlled robustness evaluation.

![](images/671d75312ef86db7b90c060d05fbc6319a53141420c0eb26fe116698bc626224.jpg)  
Figure 2: Temporal drift evaluation pipeline. Applications are executed on emulators and real devices, features are extracted and grouped by year, models are trained under sameyear, cross-year, and expanding-window protocols, and evaluated under FGSM and SPSA attacks.

These design choices ensure that adversarial samples remain within the feasible representation space, enabling systematic robustness assessment under temporal distribution shift.

## 5.2. Models and Surrogate

To examine heterogeneous learning behavior under drift, we evaluate seven target models: RF, GB, KNN, CNN, RNN, GRU, and LSTM. Because several targets are non-diferentiable or exhibit unstable gradients, we train a logistic regression surrogate on each temporally consistent training split and generate adversarial examples for transfer-based evaluation.

The surrogate consists of a single linear layer optimized with Adam (learning rate 10<sup>−2</sup>) for 20 epochs, providing stable gradients in sparse feature spaces. Standardization parameters are computed exclusively from the corresponding training-year split to avoid temporal leakage. After adversarial generation, standardized perturbations are inverted and projected to the valid domain prior to evaluation.

## 5.3. Adversarial Generation

Transfer-based surrogate attacks are commonly used to study adversarial transferability under black-box evaluation settings, including evaluations involving deep neural networks [46, 47]. In malware detection, feature-space adversarial examples have also been studied for neural malware classifiers [48]. However, we do not assume that the logistic regression surrogate accurately approximates the target decision boundary. Instead, it provides a common diferentiable reference model for generating constrained feature-space perturbations, which are then evaluated by transferring them to the target classifiers. Accordingly, the reported results should be interpreted as transferbased feature-space robustness observations rather than direct estimates of intrinsic target-model robustness.

We use FGSM and SPSA because they represent two complementary perturbation-generation mechanisms under the same constrained featurespace setting. The FGSM is a first-order gradient-based method that provides an eficient way to test the sensitivity to gradient-aligned perturbations. SPSA is a zeroth-order finite-diference method that estimates the perturbation directions without requiring analytical gradients. In our experiments, both attacks are generated on the logistic regression surrogate and then transferred to the target classifiers. Therefore, the evaluation should be interpreted as a transfer-based feature-space attack setting rather than a white-box attack on the target models. In particular, SPSA is not used as a direct black-box attack against the target classifiers because the target models are not queried during adversarial optimization.

FGSM. We apply FGSM as a surrogate-gradient attack [21]. For each input, we compute the gradient of the surrogate loss and take a single step of size ε in the sign direction. Following prior malware studies [24, 43], we use $\varepsilon = 0 . 5 5$ for static features and $\varepsilon = 0 . 2 0$ for dynamic features. Edits are restricted to the top-k gradient coordinates within each feature block and projected to the feasible domain through rounding, clamping, and bounded per-coordinate updates.

We use SPSA as a surrogate-based zeroth-order perturbation method. SPSA estimates finite-diference directions on the surrogate model and is then evaluated by transfer to the target classifiers. Thus, in this study, SPSA should not be interpreted as a direct query-based black-box attack on the target models. SPSA. We employ SPSA [49], a zeroth-order optimization

method adapted to discrete malware representations [41]. SPSA estimates finite-diference directions on the surrogate model and is then evaluated by transfer to the target classifiers. Thus, in this study, SPSA should not be interpreted as a direct query-based black-box attack on the target models. Gradients are estimated using two-sided random perturbations with scale $\delta = 0 . 0 1$ . We perform 50 optimization steps with three random restarts and apply the final perturbation with step size $\epsilon = 0 . 2 0$ . As with the FGSM, updates are restricted to blockwise top-k coordinates and projected to the feasible domain.

Projection Diagnostics. In this work, feasibility refers to representationlevel validity rather than problem-space APK validity. Static features must remain binary, dynamic features must remain non-negative integer counts, and perturbations must respect the imposed editing budget. Therefore, adversarial examples are projected back to the feasible feature domain after generation. Because this projection can weaken or remove perturbations, a low ASR should not be interpreted automatically as strong model robustness. To make this efect explicit, we report the perturbation diagnostics before and after the projection. Specifically, we measure the raw $L _ { 0 }$ perturbation size before projection, the projected $L _ { 0 }$ perturbation size after enforcing featuredomain constraints, and the projection-removal percentage, which is defined as the fraction of raw perturbation coordinates removed by the projection step. These diagnostics show whether an attack remains active after projection or whether feasible domain mapping removes most perturbations. These constraints enforce representation-level validity in the model. They do not guarantee that every perturbed feature vector corresponds to a functional, installable, or behavior-preserving APK. Accordingly, ∆ASR and AAF are not interpreted for SPSA configurations where ASR is near-zero or constant; SPSA is retained only as an auxiliary constrained diagnostic in those cases.

## 5.4. Temporal Learning Protocols

To emulate realistic intelligent system lifecycles under non-stationarity, we design three complementary evaluation protocols.

Same-year. For each year $Y$ , we construct an in-distribution baseline by splitting data into 70% training and 30% stratified holdout sets. This baseline defines reference performance under stationary conditions.

Cross-year. We train on a single year $Y _ { 1 }$ and evaluate on all years $Y _ { 2 } \geq Y _ { 1 }$ When $Y _ { 2 } > Y _ { 1 }$ , performance reflects temporal generalization without model adaptation.

Expanding-window. We train cumulatively on data from $Y _ { \mathrm { m i n } }$ through $Y _ { 1 }$ and evaluate on $Y _ { 2 } > Y _ { 1 }$ . This protocol emulates periodic retraining with all historically available data, reflecting the adaptive learning in evolving environments.

Additional control baselines. In addition to the original expandingwindow protocol, we add two control baselines. The size-matched expandingwindow protocol samples from the cumulative historical pool up to year $Y _ { 1 }$ while matching the training size of the corresponding single-year model. This controls whether expanding-window gains mainly result from larger training sets. The recent-window protocol trains only on the most recent three years up to $Y _ { 1 }$ , allowing comparison between cumulative historical training and recency-focused drift adaptation.

## 5.5. Evaluation Metrics

For each $( Y _ { 1 } , Y _ { 2 } )$ pair, we compute predictive and robustness metrics.

Predictive Metrics. Accuracy, precision, recall, and macro F1 are computed on the clean $Y _ { 2 }$ test set. When $Y _ { 1 } = Y _ { 2 }$ , results correspond to the same-year baseline; when $Y _ { 2 } > Y _ { 1 }$ , they quantify temporal generalization.

Let $\{ ( x _ { i } , y _ { i } ) \} _ { i = 1 } ^ { n }$ denote the clean test set of size $n ,$ where $x _ { i }$ is a test sample with ground-truth label $y _ { i }$ . Let $x _ { i } ^ { \prime }$ denote the adversarial counterpart of $x _ { i } , f ( \cdot )$ the evaluated classifier, and $1 [ \cdot ]$ the indicator function.

Adversarial Accuracy (AA). Adversarial Accuracy measures the fraction of adversarial samples that remain correctly classified:

$$
A A = \frac {1}{n} \sum_ {i = 1} ^ {n} \mathbf {1} [ f (x _ {i} ^ {\prime}) = y _ {i} ].
$$

Attack Success Rate (ASR). Attack Success Rate quantifies the proportion of originally correct predictions that are flipped by adversarial perturbations:

$$
\mathrm{ASR} = \frac {\sum_ {i = 1} ^ {n} \mathbf {1} [ f (x _ {i}) = y _ {i} \wedge f (x _ {i} ^ {\prime}) \neq y _ {i} ]}{\sum_ {i = 1} ^ {n} \mathbf {1} [ f (x _ {i}) = y _ {i} ]}.
$$

Drift–Robustness Linkage Metrics. To explicitly quantify the interaction between temporal separation and adversarial vulnerability, we define:

$$
\mathrm{RobustDrop} = \mathrm{AA} _ {Y _ {1}, \mathrm{baseline}} - \mathrm{AA} _ {Y _ {2}},
$$

$$
\Delta \mathrm{ASR} = \mathrm{ASR} _ {Y _ {2}} - \mathrm{ASR} _ {Y _ {1}, \mathrm{baseline}},
$$

$$
\mathrm{AAF} = \frac {\mathrm{ASR} _ {Y _ {2}}}{\mathrm{ASR} _ {Y _ {1} , \mathrm{baseline}} + 1 0 ^ {- 3}}.
$$

Here, “baseline” refers to the same-year holdout at $Y _ { 1 }$ under the corresponding protocol. Positive RobustDrop and $\Delta \mathrm { A S R }$ indicate increased vulnerability under temporal separation, while $\mathrm { A A F } > 1$ indicates higher ASR relative to the same-year baseline. Because AAF is ratio-based, it can be unstable when the baseline ASR is close to zero. Therefore, AAF is interpreted only when baseline ASR is non-negligible and is read jointly with Robust-Drop and $\Delta \mathrm { A S R }$ . The constant $1 0 ^ { - 3 }$ prevents division by zero but does not remove this interpretability limitation.

These linkage metrics complement AA and ASR. Where AA and ASR describe adversarial performance for a specific train–test pair, whereas RobustDrop, $\Delta \mathrm { A S R }$ , and AAF express how that performance changes relative to the same-year baseline. This temporal contrast makes robustness degradation easier to compare across training years, feature spaces, attacks, and deployment protocols.

## 5.6. Implementation Details

All experiments use a fixed random seed of 42 for data splitting and model initialization when supported by the implementation. RF, GB, and KNN are implemented using scikit-learn with the default settings except for fixed random states where applicable. Neural models are implemented in Keras and trained for 12 epochs with batch size 128 using binary cross-entropy and

Adam. The CNN uses two Conv1D layers with 64 and 128 filters, followed by a dense layer with 128 units and dropout 0.2. The RNN, LSTM, and GRU models use $8$ recurrent units with return sequences enabled, followed by a dense layer with 128 units and a dropout of 0.2. The logistic regression surrogate is trained for 20 epochs using Adam with a learning rate $1 0 ^ { - 2 }$

## 6. Results and Discussion

We report empirical results for both emulator and real-device datasets using static and dynamic feature representations under cross-year and expandingwindow protocols.

## 6.1. RQ1: Clean Performance Under Temporal Drift

We analyze clean detection performance as a function of temporal separation between the training year $Y _ { 1 }$ and the evaluation year $Y _ { 2 }$ . Figures 3 and 4 report accuracy and macro F1 across classifiers as functions of $Y _ { 1 } ,$ with the same-year baseline (BL) serving as the in-distribution reference. As $Y _ { 2 }$ progresses beyond $Y _ { 1 }$ , both metrics systematically decline, indicating performance degradation associated with temporal distribution shift.

![](images/7a8896e09bda1a26f18507766b3c345fa3f13be68810eb3528f0c1db961b0de0.jpg)  
(a) Real device with static features.

![](images/ff1ac6af41afab97bda0f356eb72f38433affba30a9efe15ea00a921dd8ee20a.jpg)  
(b) Real device with dynamic features.  
Figure 3: Clean performance over time under the cross-year protocol for the real device dataset, using static and dynamic features. For each training year $Y _ { 1 } .$ point plots show the distribution of accuracy and F1 score over all test years $Y _ { 2 } > Y _ { 1 }$ and all classifiers.

The degradation is more pronounced under the cross-year protocol, where models are deployed without updates. Models trained on earlier years $( \mathrm { e . g . , }$ 2008–2011) experience larger performance reductions when evaluated on later $Y _ { 2 } .$ suggesting substantial distributional divergence over longer temporal gaps. In Figures 3, point plot medians decrease and interquartile ranges widen as the gap increases, reflecting both reduced central performance and increased variability across classifiers.

![](images/9fe571cef075143e9f394487206c7f19a20b12a188f3233fbad39b558ddad4ef.jpg)  
(a) Emulator with static features.

![](images/08c9d19bceb55d25b157a0a0895bf613c4457472cf88b442347308baf5134b8e.jpg)  
(b) Emulator with dynamic features.  
Figure 4: Clean performance over time under the expanding window protocol for the emulator dataset, using static and dynamic features. For each training window that ends in year $Y _ { \mathrm { e n d } }$ , point plots summarize accuracy and F1 on all test years after $Y _ { \mathrm { e n d } }$

For mid-range training years (2012–2015), degradation remains observable but is comparatively attenuated, while models trained on more recent years exhibit smaller reductions when evaluated on temporally proximate data. Overall, these results demonstrate that clean predictive performance deteriorates as a monotonic function of temporal separation, consistent with increasing non-stationarity in the underlying data distribution.

The expanding-window protocol moderates this degradation by incorporating a broader temporal span of observations into training. Relative to cross-year models, median accuracy and macro F1 at future $Y _ { 2 }$ are consistently higher, and variability across classifiers is reduced (Figure 4). However, performance does not converge to the same-year baseline as temporal separation increases, indicating that cumulative retraining narrows but does not close the distributional gap.

Comparisons across feature spaces do not reveal a uniformly dominant representation. Static features frequently exhibit higher medians and narrower interquartile ranges, particularly on the real-device dataset, suggesting comparatively greater stability across classifiers. Dynamic features achieve comparable or lower performance depending on classifier family and training range, especially on the emulator dataset, and display greater variability across years. These diferences are consistent with distinct structural (static) and behavioral (dynamic) signal characteristics and their diferential sensitivity to temporal evolution.

Classifier family also influences temporal stability. Tree-based models (RF and GB) exhibit comparatively stable performance across years and generally higher medians relative to KNN, particularly for early training years (2008–2010). Neural models show improved performance when trained on more recent years, with stronger results observed in later evaluation periods (e.g., 2016–2017). This suggests that representation capacity interacts with recency of training data under non-stationary conditions.

Both emulator and real-device datasets exhibit the same overall directional trend, although real-device models attain higher absolute performance levels. Collectively, the results for RQ1 indicate that clean predictive performance degrades as temporal separation increases, and that the magnitude and stability of this degradation depend on the evaluation protocol, feature representation, and classifier family.

## 6.2. RQ2: Adversarial Vulnerability Under Drift

We examine how adversarial vulnerability evolves with increasing temporal separation between the training year Y<sub>1</sub> and the evaluation year $Y _ { 2 }$ . Vulnerability is quantified using Adversarial Accuracy (AA) and Attack Success Rate (ASR) under FGSM and SPSA, across both cross-year and expandingwindow protocols and for static and dynamic feature spaces.

Adversarial Accuracy. AA decreases systematically as the train–test gap widens. Under the cross-year protocol (Figure 5), AA declines as $Y _ { 2 }$ advances relative to Y<sub>1</sub>. For each training year $Y _ { 1 }$ , the same-year baseline (BL) consistently yields the highest AA, while evaluations on subsequent years show progressively lower medians. This pattern indicates that robustness degrades when models trained on earlier data distributions are exposed to temporally shifted inputs.

The decline is particularly pronounced for early training years (2008– 2011), where median AA decreases substantially and interquartile ranges widen, reflecting both central robustness loss and increased variability across classifiers. For more recent training years, reductions in AA are comparatively attenuated over temporally proximate evaluations, suggesting that robustness erosion correlates with the magnitude of distributional shift.

Robustness diferences also emerge across feature spaces and attack types. Under FGSM, models trained on dynamic features generally achieve higher AA than those trained on static features on the emulator dataset (Figures 5b and 5a). In contrast, under SPSA, dynamic-feature models exhibit greater variability and lower AA in several configurations. This distinction is consistent with the interaction between the query-based optimization dynamics of SPSA and the higher-dimensional, continuous-valued structure of dynamic feature representations, relative to binary static indicators.

![](images/85c074c6e0765f62ca7bcbd46ee8e4e90bd8273f079d273110268f0e4d45bb77.jpg)  
(a) Emulator with static features.

![](images/a3bcff4660a42086f1f156b2a668e6acce69a9d982d892b5685838d277af7a30.jpg)  
(b) Emulator with dynamic features.  
Figure 5: Adversarial Accuracy (AA) for cross-year evaluation on the emulator dataset using static (a) and dynamic (b) features. For each training year $Y _ { 1 } ,$ point plots summarize AA over all future evaluation years $Y _ { 2 } > Y _ { 1 }$ under FGSM and SPSA attacks. The horizontal BL line denotes the same-year baseline, where models are trained and evaluated on $Y _ { 1 }$

Expanding-window retraining improves robustness by exposing the model to a broader temporal range, but it may also retain outdated distributions from earlier years. These older samples can stabilize learning, yet they may dilute adaptation to recent benign behavior and newly emerging malware families. This explains why expanding-window retraining reduces the robustness gap relative to cross-year deployment but does not fully restore same-year robustness. On the real-device dataset (Figure 6), AA remains closer to the same-year baseline (BL) as the training window expands, and dispersion across classifiers is reduced relative to the cross-year protocol. This indicates that cumulative exposure to temporally diverse data improves stability under adversarial perturbation. To better distinguish ordinary temporal degradation from adversarial-specific degradation, we jointly examine the clean-performance trends in Figures 3–4 and the adversarial-performance trends in Figures 5–7 across increasing temporal gaps. Under the cross-year FGSM setting, adversarial accuracy declines more sharply than the corresponding clean accuracy in several configurations, particularly for early training years and static features. This suggests that the observed reduction in adversarial accuracy is not explained solely by ordinary clean-performance degradation, but is also associated with increased sensitivity to adversarial perturbations under temporal distribution shift. However, this efect is configuration-dependent and is not consistently observed across all attacks and feature spaces.

However, for suficiently distant evaluation years $Y _ { 2 } ,$ AA remains consistently below the baseline, demonstrating that residual robustness loss persists despite incremental retraining. In other words, adaptive updates narrow the robustness gap but do not fully restore in-distribution adversarial performance under substantial temporal separation.

Diferences across feature spaces remain observable under the expandingwindow protocol. Static features exhibit comparatively stable AA across years, particularly on the real-device dataset, suggesting greater resilience to temporal variability. Dynamic features benefit from retraining but retain higher sensitivity to temporal separation, especially under SPSA (Figures 6a and 6b). This pattern is consistent with the greater representational flexibility of dynamic signals, which may also render them more susceptible to distributional evolution under query-based perturbations.

Overall, these results indicate that incremental retraining attenuates, but does not fully ofset, the interaction between temporal drift and adversarial vulnerability.

![](images/a89eff6cf2e71c4b8c9754930331fcc7b62337f2384aafa8284b06a3141ea5e0.jpg)  
(a) Real device with static features.

![](images/52429b14bea964c559b76dea94448593bb0cc28880af253eeb2aacbd4d87da5f.jpg)  
(b) Real device with dynamic features.  
Figure 6: Adversarial accuracy (AA) for expanding window models on the real device, using static (a) and dynamic (b) features. For each training window that starts in 2008 and ends in year $Y _ { \mathrm { e n d } }$ , point plots aggregate AA over all corresponding test years under the FGSM and SPSA attacks. The horizontal BL line marks the reference baseline trained and evaluated on the same year.

Efect of feasibility projection. Before interpreting ASR values, we examine whether generated perturbations remain active after feasibility projection. Table 1 reports raw and projected perturbation magnitudes under the cross-year protocol. The FGSM retains non-zero projected perturbations across both datasets and feature spaces. Regarding static features, FGSM modifies 4.33 features on the emulator dataset and 4.86 features on the realdevice dataset after projection, compared with a raw budget of nine features. For dynamic features, FGSM modified 5.16 and 4.50 features after projection on the emulator and real-device datasets, respectively. In contrast, the SPSA is substantially weakened by feasibility projection. Its projected $L _ { 0 }$ is zero in both static feature settings and remains small for dynamic features. The projected ASR of the SPSA is zero across the reported cross-year configurations. The projection-removal percentages further confirm this behavior: FGSM has negligible removal in all settings, whereas SPSA removal reaches 1.000 for both static feature settings and remains high for dynamic features. Therefore, a near-zero SPSA ASR should not be interpreted as evidence of strong model robustness. Instead, this indicates that SPSA perturbations are often removed by the imposed discrete feasibility constraints. Accordingly, we retain SPSA as an auxiliary diagnostic and use FGSM as the main constrained feature-space attack in the revised adversarial analysis.

Table 1: Perturbation efectiveness after feasibility projection under the cross-year protocol for all models. The values are the medians of all seven target classifiers. $L _ { 0 }$ reports the number of modified malware features before and after the projection. Removal denotes the fraction of raw perturbation coordinates removed by projection.

<table><tr><td>Dataset</td><td>Features</td><td>FGSM raw  $L_0$ </td><td>FGSM proj.  $L_0$ </td><td>FGSM removal</td><td>FGSM ASR</td><td>SPSA raw  $L_0$ </td><td>SPSA proj.  $L_0$ </td><td>SPSA removal</td><td>SPSA ASR</td></tr><tr><td>Emulator</td><td>Dynamic</td><td>18.11</td><td>5.16</td><td>0.003</td><td>0.003</td><td>4.78</td><td>0.00</td><td>0.971</td><td>0.000</td></tr><tr><td>Emulator</td><td>Static</td><td>9.00</td><td>4.33</td><td>0.000</td><td>0.222</td><td>9.00</td><td>0.00</td><td>1.000</td><td>0.000</td></tr><tr><td>Real device</td><td>Dynamic</td><td>18.52</td><td>4.50</td><td>0.006</td><td>0.002</td><td>6.15</td><td>0.57</td><td>0.434</td><td>0.000</td></tr><tr><td>Real device</td><td>Static</td><td>9.00</td><td>4.86</td><td>0.000</td><td>0.182</td><td>9.00</td><td>0.00</td><td>1.000</td><td>0.000</td></tr></table>

Attack Success Rate. The Attack Success Rate (ASR) provides a complementary perspective on adversarial vulnerability by measuring the proportion of originally correct predictions that are flipped by perturbations. In cross-year experiments on the real-device dataset (Figure 7), the largest deviations from the same-year baseline occur under FGSM on static features (Figure 7a). In these configurations, ASR increases for early training years and interquartile ranges widen, indicating both a higher incidence of successful perturbations and greater variability across classifiers as temporal separation grows.

In contrast, dynamic features exhibit ASR values close to zero across most years, and SPSA produces near-zero ASR for both feature spaces (Figure 7b). Under the imposed feasibility constraints and bounded edit budgets, SPSA rarely induces explicit label flips. As a result, its impact is more prominently reflected in reductions in Adversarial Accuracy (AA) rather than large increases in ASR. This distinction highlights that diferent attack mechanisms interact diferently with temporal drift, depending on feature representation and perturbation structure.

![](images/6983d3c5ff479d14238346cac380da190c1d8bee8257bff9690f85673ee50468.jpg)  
(a) Real device with static features.

![](images/d4a542b5e1b33e907bb0b5fdf61baeded5dec01b34b32594ae3bf428ee747578.jpg)  
(b) Real device with dynamic features.  
Figure 7: Attack success rate (ASR) for cross year models on the real device, using static (a) and dynamic (b) features. For each training year $Y _ { 1 }$ , point plots aggregate ASR over all test years $Y _ { 2 } ~ > ~ Y _ { 1 }$ under the FGSM and SPSA attacks. Higher ASR means that adversarial perturbations are more successful.

Expanding-window retraining shifts AA closer to the same-year baseline relative to cross-year deployment, particularly on the real-device dataset (Figure 6). Dispersion across classifiers is also reduced. Nonetheless, for suficiently distant evaluation years $Y _ { 2 }$ , AA remains below BL, reflecting persistent robustness sensitivity under temporal separation.

Overall, expanding-window retraining attenuates attack success relative to cross-year deployment, indicating that cumulative exposure to temporally diverse data improves robustness. However, residual vulnerability persists under FGSM for specific model–feature combinations, demonstrating that incremental updates do not fully neutralize adversarial susceptibility under sustained distributional evolution.

Summary. Increasing temporal separation is associated with elevated adversarial vulnerability, reflected primarily by declining AA under cross-year evaluation and, in selected configurations, higher ASR for early training years. Expanding-window retraining narrows this gap relative to the sameyear baseline but does not eliminate it under continued distributional shift. Residual vulnerability is most pronounced under FGSM, particularly for static features, whereas SPSA and dynamic-feature ASR remain near zero except for isolated outliers. Collectively, these results indicate that temporal separation is associated with disproportionate adversarial degradation in selected configurations, while adaptive retraining provides partial but incomplete mitigation.

![](images/b858177ecaf7eb5187667f0677272a73c9b502852ddc13a1c0a7017d4e8dc800.jpg)  
(a) Emulator dataset with static features.

![](images/ce523c2fd29b06a5e66860ad893dd13d62b4de3ec8bf883bac0eae8ca751f510.jpg)  
(b) Emulator dataset with dynamic features.  
Figure 8: Attack success rate (ASR) for expanding window (incremental) models on the emulator device, using static (a) and dynamic (b) features. For each training window end year, point plots aggregate ASR over all corresponding test years under the FGSM and SPSA attacks. Lower ASR than in the cross year case shows that incremental retraining mitigates drift induced adversarial vulnerability.

Table 2: Spearman association between temporal gap $\Delta T$ and FGSM RobustDrop under the cross-year protocol. RobustDrop measures the reduction in adversarial accuracy relative to the same-year baseline.

<table><tr><td>Dataset</td><td>Features</td><td>Spearman ρ</td><td>p-value</td></tr><tr><td rowspan="2">Emulator</td><td>Dynamic</td><td>0.681</td><td>0.010</td></tr><tr><td>Static</td><td>0.758</td><td>0.003</td></tr><tr><td rowspan="2">Real device</td><td>Dynamic</td><td>0.560</td><td>0.046</td></tr><tr><td>Static</td><td>0.692</td><td>0.009</td></tr></table>

## 6.3. RQ3: Quantifying Drift and Adversarial Vulnerability

This research question examines the association between temporal drift and adversarial vulnerability, and the extent to which expanding-window retraining moderates this relationship. The linkage metrics are used to express robustness changes as temporal contrasts relative to the same-year baseline, rather than as replacements for AA and ASR. For each $( Y _ { 1 } , Y _ { 2 } )$ pair, we compute ① RobustDrop (RD), defined as the reduction in adversarial accuracy relative to the same-year baseline; $\textcircled { 2 } \ \Delta \mathrm { A S R }$ , the change in attack success rate relative to baseline; and ③ AAF, the ratio of attack success in $Y _ { 2 }$ to its baseline value. Figures 9 and 10 report the RD (top rows) and $\Delta \mathrm { A S R }$ (bottom rows) across years under the cross-year and expanding-window protocols. Table 4 summarizes Spearman correlations and median AAF values.

To support the temporal-gap analysis, we compute bootstrap 95% confidence intervals for median metrics by $\Delta T$ and Spearman correlation coeficients with corresponding p-values between $\Delta T$ and each robustness metric. We report the cross-year RobustDrop association in the main text because it directly captures non-adaptive deployment under increasing temporal separation. The results show a positive association between the temporal gap and FGSM RobustDrop across both datasets and feature spaces. This indicates that a larger train–test temporal separation is associated with a greater adversarial accuracy reduction under the cross-year deployment protocol. We use RobustDrop for this summary because it remains interpretable when ASR is low, unlike ratio-based measures such as AAF.

RD exhibits a consistent temporal pattern across devices and feature spaces. Under cross-year evaluation (left columns of Figures 9 and 10), RD is largest for early training years and decreases as $Y _ { 1 }$ increases, indicating greater reductions in adversarial accuracy for models trained on temporally distant data. Under expanding-window retraining (right columns), RD values are consistently smaller and vary more smoothly across years, indicating partial mitigation of robustness loss through cumulative retraining.

Table 4 quantifies this trend: $\rho _ { X } ( \mathrm { R D } ) ~ < ~ 0$ across all evaluated settings, demonstrating a negative association between training year and robustness degradation. The magnitude of this association is stronger for static features under expanding-window retraining (e.g., emulator static features: $\rho _ { X } ( \mathrm { R D } ) \ : = \ : - 0 . 5 6 2$ for FGSM and −0.531 for SPSA), consistent with the visual patterns in the corresponding figures.

∆ASR provides complementary information and varies across attack types and feature spaces. For static features, FGSM exhibits the largest earlyyear deviations from zero (Figures 9a and 10a, bottom-left panels), reflecting greater increases in attack-induced label flips for models trained on earlier years. Under expanding-window retraining (bottom-right panels), these deviations are reduced, consistent with attenuation of vulnerability relative to cross-year deployment.

For SPSA, ∆ASR remains close to zero in multiple configurations, particularly for static features. In such cases, correlations are undefined (“–”) in Table 4, as limited variation in ASR precludes meaningful rank association. For dynamic features, ∆ASR values are generally small and characterized by localized peaks rather than monotonic trends (Figures 9b and 10b), suggesting year- or model-specific efects rather than a consistent temporal pattern. One contributing factor is projection to a discrete feasible domain, where quantized updates may limit boundary crossings and reduce systematic amplification of attack success over time.

The Adversarial Amplification Factor (AAF) evaluates whether attack success in $Y _ { 2 }$ exceeds its same-year baseline. Table 4 reports AAF values greater than 1 in several expanding-window configurations, particularly for dynamic features, indicating amplification relative to baseline. Because AAF is normalized by baseline ASR, its magnitude is sensitive when baseline ASR is near zero. Accordingly, AAF is interpreted jointly with RD and ∆ASR rather than in isolation.

Interpretation of Drift–Robustness Coupling. One plausible mechanism underlying the observed association is geometric. Temporal drift alters feature distributions and may reshape the efective decision boundary learned at $Y _ { 1 }$ . When evaluated on future data $Y _ { 2 }$ , samples may lie closer to this boundary due to distributional shift, even if clean classification remains correct. Reduced margin or altered gradient alignment can increase the sensitivity of predictions to small perturbations, thereby amplifying adversarial vulnerability beyond what is explained by clean accuracy degradation alone. Under expanding-window retraining, the boundary adapts to a broader temporal span, which stabilizes margins and partially mitigates this efect, but continued evolution may still induce boundary misalignment over time.

Table 3: Protocol comparison across temporal deployment strategies. Cross-year trains on a single year and tests on future years. Expanding Window (EW)-full trains on all historical data up to Y . EW-size-matched samples from the same historical pool while matching the single-year training size. Recent-window trains on the most recent three years up to $Y _ { 1 }$ . Values are the medians over all seven classifiers.

<table><tr><td>Dataset</td><td>Features</td><td>Protocol</td><td>Clean Acc.</td><td>FGSM AA</td><td>FGSM ASR</td><td>RobustDrop</td><td>Train size</td></tr><tr><td rowspan="8">Emulator</td><td rowspan="4">Dynamic</td><td>Cross-year</td><td>0.743</td><td>0.728</td><td>0.003</td><td>0.180</td><td>2,220</td></tr><tr><td>EW-full</td><td>0.605</td><td>0.572</td><td>0.031</td><td>0.227</td><td>23,746</td></tr><tr><td>EW-size-matched</td><td>0.539</td><td>0.491</td><td>0.026</td><td>0.234</td><td>3,668</td></tr><tr><td>Recent-window</td><td>0.634</td><td>0.604</td><td>0.029</td><td>0.202</td><td>8,414</td></tr><tr><td rowspan="4">Static</td><td>Cross-year</td><td>0.807</td><td>0.498</td><td>0.222</td><td>0.105</td><td>2,220</td></tr><tr><td>EW-full</td><td>0.827</td><td>0.563</td><td>0.256</td><td>0.036</td><td>23,746</td></tr><tr><td>EW-size-matched</td><td>0.805</td><td>0.539</td><td>0.288</td><td>0.068</td><td>3,668</td></tr><tr><td>Recent-window</td><td>0.807</td><td>0.508</td><td>0.298</td><td>0.105</td><td>8,414</td></tr><tr><td rowspan="8">Real device</td><td rowspan="4">Dynamic</td><td>Cross-year</td><td>0.782</td><td>0.773</td><td>0.002</td><td>0.169</td><td>3,747</td></tr><tr><td>EW-full</td><td>0.693</td><td>0.666</td><td>0.026</td><td>0.187</td><td>25,386</td></tr><tr><td>EW-size-matched</td><td>0.651</td><td>0.626</td><td>0.023</td><td>0.185</td><td>3,747</td></tr><tr><td>Recent-window</td><td>0.688</td><td>0.675</td><td>0.015</td><td>0.175</td><td>12,646</td></tr><tr><td rowspan="4">Static</td><td>Cross-year</td><td>0.861</td><td>0.596</td><td>0.182</td><td>0.096</td><td>3,747</td></tr><tr><td>EW-full</td><td>0.874</td><td>0.615</td><td>0.236</td><td>0.014</td><td>25,386</td></tr><tr><td>EW-size-matched</td><td>0.865</td><td>0.642</td><td>0.188</td><td>0.036</td><td>3,747</td></tr><tr><td>Recent-window</td><td>0.860</td><td>0.530</td><td>0.278</td><td>0.068</td><td>12,646</td></tr></table>

Efect of control baselines. Table 3 compares cross-year deployment with full expanding-window, size-matched expanding-window, and recentwindow retraining. The results show that retraining efects are configurationdependent. Static features generally benefit from expanding-window variants, while dynamic features do not always improve under cumulative historical training. The size-matched baseline further shows that the observed changes cannot be explained by the training-set size alone. Overall, the added baselines indicate that robustness under temporal drift depends on temporal coverage, recency, and feature representation.

Summary. The linkage metrics collectively indicate a measurable association between temporal separation and adversarial vulnerability under the evaluated feature-space setting. RobustDrop consistently captures this relationship across devices, feature spaces, and evaluation protocols, showing larger reductions in adversarial accuracy for earlier training years and partial mitigation under incremental retraining. In contrast, ∆ASR and AAF are most informative when ASR is non-negligible, and are interpreted cautiously for SPSA configurations where ASR is near-zero or constant. Overall, the evidence supports a temporal association with adversarial-accuracy degradation, while ASR amplification remains configuration-dependent.

In contrast, ∆ASR and AAF vary across attack types and feature representations. Amplification relative to baseline is most visible under FGSM, particularly in settings where attack-induced label flips are non-trivial. When ASR remains near zero due to discrete validity constraints, ∆ASR and AAF exhibit limited variation. These findings indicate that the strength and form of the drift–robustness linkage depend on both the attack mechanism and the structure of the feasible feature domain.

![](images/d4670155c3976ca7a5d35c0c8bbb85f46d1e0dc5dfdecc88fc1dd504ac0aea4e.jpg)

![](images/dcde1e4c172449489aa2ce89de0914fd1ec88961aa724a62cc989e92f9dccf8b.jpg)

![](images/795a4a214eb25fa918f6752e0a1e6fb80178f25aa8f0cac0e820cc74d025577a.jpg)

![](images/aa65a7d06c81d8e8916070194acff9fbae31343487d2fbbb5e20784549399ac3.jpg)  
Training Range (End Year)

(a) Emulator dataset with static features.  
![](images/810a2094f82fab6ee1da6b1d93d540a950c33cc5ab53fc752e805c3724d39f2e.jpg)

![](images/529297e8b143950766cc1451eb27d24ddee919abc49be8e61ff39c635a721959.jpg)

![](images/3a6eaf67bee437d8c4fc920e303fa2ad0c370d1778180aaef324468efce970e4.jpg)

![](images/b461643f95c97c61cac36f6e8ab05af4319166c77742696dbd91c1550a90ae5b.jpg)  
Training Range (End Year)  
(b) Emulator dataset with dynamic features.

Figure 9: Linkage metrics for the emulator device. Each $2 \times 2$ panel uses the training year or training window end year and shows the median RobustDrop (top row) and ∆ASR (bottom row) for FGSM and SPSA, aggregated over $( Y _ { 1 } , Y _ { 2 } )$ pairs.

![](images/90f59ae67e0a934b88b3823a8122b73233b2ca76231a3c26df80cad0dc60b15b.jpg)

![](images/a283d980236bd9f55f97544d3bac50dedd58d2d3cf2f2053308b151bc2ff81fb.jpg)

![](images/21a729cf215b075063c15ce3bbff40df9884d54033a2fc42e011b9f4d01a5a0d.jpg)

![](images/7758e9ec7151a67ef2a438e6d4e2d2c9dc5e6ec007eef51e38d768188163123f.jpg)  
Training Range (End Year)

(a) Real device with static features.  
![](images/43c817fad91b67037f4167d199321dd2a3476a8f35e0feaca17b2905c97e4928.jpg)

![](images/fb455a0c39af15d86206743590db21df374e4105663b8ab1855c5feebd356d12.jpg)

![](images/93b66a03583db301b56afaab8f2c4ef1ab877b99b0ca3a1dc40203c3e3283d8e.jpg)

![](images/3ce2c30b2ba2282a934f9a4ec5f1a924f7ef27300c8db99718dd85b15bec2718.jpg)  
Training Range (End Year)  
(b) Real device with dynamic features.

Figure 10: Linkage metrics for the real device. The panels summarize how RobustDrop, $\Delta \mathrm { A S R }$ , and $\mathrm { A A F }$ evolve as the training data move forward in time, under both FGSM and SPSA attacks.

Table 4: Linkage summary (Spearman). (CY) cross-year, (EW) expanding-window, (Dyn) dynamic, (Sta) static. X denotes the training year for CY and EW). Each entry reports FGSM / SPSA and is aggregated over all $( Y _ { 1 } , Y _ { 2 } )$ pairs and all seven target models. “–” indicates undefined correlation due to near-constant ∆ASR.

<table><tr><td rowspan="2">Dataset</td><td rowspan="2">Features</td><td rowspan="2">Prot.</td><td> $\rho_X(RD)$ </td><td> $\rho_X(\Delta ASR)$ </td><td>AAF</td></tr><tr><td>FGSM / SPSA</td><td>FGSM / SPSA</td><td>FGSM / SPSA</td></tr><tr><td rowspan="4">Emulator</td><td rowspan="2">Dyn</td><td>CY</td><td>-0.360 / -0.369</td><td>0.076 / 0.014</td><td>0.223 / 0.164</td></tr><tr><td>EW</td><td>-0.287 / -0.339</td><td>0.347 / -0.039</td><td>1.553 / 1.610</td></tr><tr><td rowspan="2">Sta</td><td>CY</td><td>-0.461 / -0.432</td><td>-0.246 / -</td><td>1.015 / 0</td></tr><tr><td>EW</td><td>-0.562 / -0.531</td><td>-0.415 / -</td><td>1.812 / 0</td></tr><tr><td rowspan="4">Real device</td><td rowspan="2">Dyn</td><td>CY</td><td>-0.342 / -0.347</td><td>-0.022 / 0.033</td><td>0.169 / 0.436</td></tr><tr><td>EW</td><td>-0.126 / -0.170</td><td>-0.051 / -0.195</td><td>1.109 / 1.170</td></tr><tr><td rowspan="2">Sta</td><td>CY</td><td>-0.415 / -0.426</td><td>-0.195 / -</td><td>0.999 / 0</td></tr><tr><td>EW</td><td>-0.469 / -0.444</td><td>-0.339 / -</td><td>1.314 / 0</td></tr></table>

We note that the reported trends should be interpreted as associations observed under the evaluated transfer-based feature-space setting rather than as causal evidence that temporal drift directly increases adversarial vulnerability across all deployment conditions.

## 7. Threats to Validity

Internal validity. Adversarial evaluation was conducted in feature space under explicit feasibility constraints. Each attack modifies at most $k _ { \mathrm { s t a } } =$ $\left\lceil 0 . 0 5 d _ { \mathrm { s t a } } \right\rceil$ and $k _ { \mathrm { d y n } } = \lceil 0 . 0 5 d _ { \mathrm { d y n } } \rceil$ features, with fixed perturbation strengths $( \epsilon _ { \mathrm { s t a } } = 0 . 5 5 , \epsilon _ { \mathrm { d y n } } = 0 . 2 0 )$ . Dynamic perturbations are generated in standardized space and subsequently mapped back to count-based representations. After inverse scaling, rounding, and enforcing a per-feature cap of one count change, many continuous perturbations may be removed or reduced to 0 or ±1 count changes. To make this limitation explicit, we report projection diagnostics before and after enforcing feature-domain constraints. These diagnostics show that FGSM generally remains active after projection, whereas SPSA is often substantially weakened because many of its raw perturbation coordinates are removed by the projection step. Therefore, near-zero SPSA ASR is not interpreted as evidence of strong model robustness. Instead, SPSA is treated as an auxiliary constrained diagnostic, and the main adversarial analysis relies primarily on FGSM and projected adversarial accuracy.

These constraints preserve representation level validity and ensure that adversarial samples remain within the feasible domain of feature vector. However, they also restrict attack flexibility and may limit decision-boundary crossings. As a result, ASR may remain low in certain configurations—particularly for SPSA and dynamic features—even when AA decreases. More permissive edit budgets, alternative feasibility projections, or problem-space manipulations could produce diferent attack efectiveness. Accordingly, our conclusions apply within the defined feature-space threat model.

Problem-space realizability. Our adversarial evaluation is conducted in feature space and does not construct modified APKs. Although the projection step ensures that perturbed vectors satisfy representation-level constraints, such as binary static features and non-negative integer dynamic counts, this does not guarantee problem-space realizability. In particular, a modified permission, intent, or system-call-count vector may not correspond to a functional, installable, and behavior-preserving Android application. Therefore, the reported adversarial results should be interpreted as featurespace robustness evidence, not as direct measurement of real-world APK evasion success.

External validity. Our analysis is based on static and dynamic feature representations extracted from emulator and real-device executions within the KronoDroid dataset. Alternative datasets, feature extraction pipelines, platform versions, or data collection procedures may exhibit diferent temporal dynamics and distributional shifts.

Similarly, the relative behavior of FGSM and SPSA may vary under different feature encodings or attack implementations. We evaluated a fixed set of target models and employed a logistic regression surrogate for transferbased attacks. Diferent model families, surrogate architectures, or stronger adaptive attackers could alter quantitative vulnerability levels. Therefore, the reported findings should be interpreted as representative of the evaluated configurations rather than universally generalizable across all Android malware detection systems.

Construct validity. Robustness is quantified using AA, ASR, and the linkage metrics RobustDrop, $\Delta \mathrm { A S R }$ , and AAF. These metrics capture complementary aspects of adversarial vulnerability but are sensitive to baseline behavior and attack constraints. In particular, AAF is normalized by baseline ASR and can become unstable when baseline ASR approaches zero. For this reason, AAF is interpreted jointly with RobustDrop and $\Delta \mathrm { A S R }$ rather than independently.

More broadly, the measured association between temporal drift and adversarial vulnerability depends on the operationalization of drift through temporal separation and on the selected robustness metrics. Alternative drift characterizations or robustness definitions may yield diferent quantitative magnitudes, although the qualitative trends observed here are consistent across devices, feature spaces, and evaluation protocols.

## 8. Conclusion

We presented a longitudinal evaluation of temporal drift and adversarial robustness in Android malware detection using the KronoDroid dataset (2008–2020), with the objective of characterizing their association under transfer-based feature-space adversarial evaluation. Across cross-year and expanding-window settings, increasing temporal separation between training and evaluation data is consistently associated with declines in clean predictive performance and reductions in adversarial accuracy relative to sameyear baselines. In selected configurations, attack success rates also increase for models trained on earlier years, indicating amplified vulnerability under sustained distributional evolution.

Expanding-window retraining mitigates these efects relative to cross-year deployment by increasing temporal coverage. However, robustness does not fully recover under continued temporal separation, likely because cumulative training retains older distributions, whereas newly emerging malware and benign behaviors may not be fully represented by historical static and dynamic features. Thus, cumulative retraining narrows, but does not eliminate, robustness loss within the evaluated feature-space threat model.

The results indicate a measurable association between temporal separation and reduced adversarial accuracy in the evaluated Android malware detection setting. More broadly, they underscore the importance of explicitly accounting for non-stationary data distributions when evaluating the robustness of intelligent detection systems. These findings motivate future work on drift monitoring mechanisms, adaptive retraining strategies, and robustness-aware temporal learning frameworks designed for evolving, adversarial environments.

Beyond the Android setting, these findings highlight a broader systemslevel implication: robustness in intelligent detection systems is inherently time-dependent. Evaluations conducted under stationary assumptions may overestimate long-term reliability when models are deployed in evolving environments. As a result, adversarial robustness should be assessed not only against perturbation strength but also against temporal separation between training and deployment data. Incorporating drift-aware evaluation protocols into robustness assessment frameworks may therefore be necessary for realistic appraisal of intelligent security systems operating in non-stationary, adversarial domains. These conclusions are limited to the evaluated Android dataset family, static and dynamic KronoDroid feature representations, selected classifier families, and constrained transfer-based feature-space attacks.

## References

[1] A. Abusnaina, A. Anwar, M. Saad, A. Alabduljabbar, R. Jang, S. Salem, D. Mohaisen, One step forward, two steps back: Ml-based malware detection under concept drift, Computing 107 (11) (2025) 207. doi:10.1007/S00607-025-01543-7. URL https://doi.org/10.1007/s00607-025-01543-7

[2] A. Sabbah, R. Jarrar, S. Zein, D. Mohaisen, Understanding concept drift with deprecated permissions in android malware detection, CoRR abs/2507.22231 (2025). arXiv:2507.22231, doi:10.48550/ARXIV.2507.22231. URL https://doi.org/10.48550/arXiv.2507.22231

[3] A. Sabbah, R. Jarrar, S. Zein, D. Mohaisen, Empirical evaluation of concept drift in ml-based android malware detection, CoRR abs/2507.22772 (2025). arXiv:2507.22772, doi:10.48550/ARXIV.2507.22772. URL https://doi.org/10.48550/arXiv.2507.22772

[4] A. Abusnaina, A. Anwar, M. Saad, A. Alabduljabbar, R. Jang, S. Salem, D. Mohaisen, Exposing the limitations of machine learning for malware detection under concept drift, in: M. Barhamgi, H. Wang, X. Wang (Eds.), Web Information Systems Engineering - WISE 2024 - 25th International Conference, Doha, Qatar, December 2-5, 2024, Proceedings, Part II, Vol. 15437 of Lecture Notes in Computer Science, Springer, 2024, pp. 273–289. doi:10.1007/978-981-96-0567-5\_20. URL https://doi.org/10.1007/978-981-96-0567-5\_20

[5] A. Mohaisen, O. Alrawi, M. Mohaisen, AMAL: high-fidelity, behaviorbased automated malware analysis and classification, Comput. Secur.

52 (2015) 251–266. doi:10.1016/J.COSE.2015.04.001. URL https://doi.org/10.1016/j.cose.2015.04.001

[6] J. G. Moreno-Torres, T. Raeder, R. Alaíz-Rodríguez, N. V. Chawla, F. Herrera, A unifying view on dataset shift in classification, Pattern Recognit. 45 (1) (2012) 521–530. doi:10.1016/J.PATCOG.2011.06.019.

[7] J. Gama, I. Zliobaite, A. Bifet, M. Pechenizkiy, A. Bouchachia, A survey on concept drift adaptation, ACM Comput. Surv. 46 (4) (2014) 44:1– 44:37. doi:10.1145/2523813.

[8] F. Shen, J. D. Vecchio, A. Mohaisen, S. Y. Ko, L. Ziarek, Android malware detection using complex-flows, IEEE Trans. Mob. Comput. 18 (6) (2019) 1231–1245. doi:10.1109/TMC.2018.2861405.

[9] H. Alasmary, A. Khormali, A. Anwar, J. Park, J. Choi, A. Abusnaina, A. Awad, D. Nyang, A. Mohaisen, Analyzing and detecting emerging internet of things malware: A graph-based approach, IEEE Internet Things J. 6 (5) (2019) 8977–8988. doi:10.1109/JIOT.2019.2925929. URL https://doi.org/10.1109/JIOT.2019.2925929

[10] Mobile operating system market share worldwide | statcounter global stats, https://gs.statcounter.com/os-market-share/mobile/worldwide, (Accessed on 03/29/2025).

[11] Malware statistics & trends report | av-test, https://www.av-test.org/ en/statistics/malware/, (Accessed on 03/29/2025).

[12] Kaspersky’s report on mobile threats in 2023 | securelist, https://se curelist.com/mobile-malware-report-2023/111964/, (Accessed on 03/29/2025).

[13] Y. Pan, X. Ge, C. Fang, Y. Fan, A systematic literature review of android malware detection using static analysis, IEEE Access 8 (2020) 116363–116379. doi:10.1109/ACCESS.2020.3002842. URL https://doi.org/10.1109/ACCESS.2020.3002842

[14] A. Alzubaidi, Recent advances in android mobile malware detection: A systematic literature review, IEEE Access 9 (2021) 146318–146349. doi:10.1109/ACCESS.2021.3123187.

[15] M. Li, Z. Fang, J. Wang, L. Cheng, Q. Zeng, T. Yang, Y. Wu, J. Geng, A systematic overview of android malware detection, Appl. Artif. Intell. 36 (1) (2022). doi:10.1080/08839514.2021.2007327.

[16] A. Guerra-Manzanares, H. Bahsi, S. Nõmm, Kronodroid: Timebased hybrid-featured dataset for efective android malware detection and characterization, Comput. Secur. 110 (2021) 102399. doi:10.1016/J.COSE.2021.102399. URL https://doi.org/10.1016/j.cose.2021.102399

[17] A. Guerra-Manzanares, M. Luckner, H. Bahsi, Android malware concept drift using system calls: Detection, characterization and challenges, Expert Syst. Appl. 206 (2022) 117200. doi:10.1016/J.ESWA.2022.117200.

[18] A. Guerra-Manzanares, H. Bahsi, On the relativity of time: Implications and challenges of data drift on long-term efective android malware detection, Comput. Secur. 122 (2022) 102835. doi:10.1016/J.COSE.2022.102835.

[19] F. Pendlebury, F. Pierazzi, R. Jordaney, J. Kinder, L. Cavallaro, TESSERACT: eliminating experimental bias in malware classification across space and time, in: N. Heninger, P. Traynor (Eds.), USENIX, 2019, pp. 729–746.

[20] F. Barbero, F. Pendlebury, F. Pierazzi, L. Cavallaro, Transcending TRANSCEND: revisiting malware classification in the presence of concept drift, in: SP, IEEE, 2022, pp. 805–823. doi:10.1109/SP46214.2022.9833659.

[21] I. J. Goodfellow, J. Shlens, C. Szegedy, Explaining and harnessing adversarial examples, in: Y. Bengio, Y. LeCun (Eds.), 3rd International Conference on Learning Representations, ICLR 2015, San Diego, CA, USA, May 7-9, 2015, Conference Track Proceedings, 2015.

[22] A. Madry, A. Makelov, L. Schmidt, D. Tsipras, A. Vladu, Towards deep learning models resistant to adversarial attacks, in: 6th International Conference on Learning Representations, ICLR 2018, Vancouver, BC, Canada, April 30 - May 3, 2018, Conference Track Proceedings, Open-Review.net, 2018.

[23] N. Carlini, D. A. Wagner, Towards evaluating the robustness of neural networks, in: 2017 IEEE Symposium on Security and Privacy, SP 2017, San Jose, CA, USA, May 22-26, 2017, IEEE Computer Society, 2017, pp. 39–57. doi:10.1109/SP.2017.49.

[24] F. Pierazzi, F. Pendlebury, J. Cortellazzi, L. Cavallaro, Intriguing properties of adversarial ML attacks in the problem space, in: 2020 IEEE Symposium on Security and Privacy, SP 2020, San Francisco, CA, USA, May 18-21, 2020, IEEE, 2020, pp. 1332–1349. doi:10.1109/SP40000.2020.00073.

[25] H. Bostani, V. Moonsamy, Evadedroid: A practical evasion attack on machine learning for black-box android malware detection, Comput. Secur. 139 (2024) 103676. doi:10.1016/J.COSE.2023.103676.

[26] J. C. Schlimmer, R. H. Granger, Incremental learning from noisy data, Mach. Learn. 1 (3) (1986) 317–354. doi:10.1023/A:1022810614389.

[27] Q. Xiang, L. Zi, X. Cong, Y. Wang, Concept drift adaptation methods under the deep learning framework: A literature review, Applied Sciences 13 (11) (2023) 6515.

[28] F. Ceschin, M. Botacin, H. M. Gomes, F. A. Pinage, L. S. Oliveira, A. Grégio, Fast & furious: On the modelling of malware detection as an evolving data stream, Expert Syst. Appl. 212 (2023) 118590. doi:10.1016/J.ESWA.2022.118590. URL https://doi.org/10.1016/j.eswa.2022.118590

[29] J. Tripathi, H. M. Gomes, M. Botacin, Towards explainable drift detection and early retrain in ml-based malware detection pipelines, in: M. Egele, V. Moonsamy, D. Gruss, M. Carminati (Eds.), Detection of Intrusions and Malware, and Vulnerability Assessment - 22nd International Conference, DIMVA 2025, Graz, Austria, July 9-11, 2025, Proceedings, Part II, Vol. 15748 of Lecture Notes in Computer Science, Springer, 2025, pp. 3–24. doi:10.1007/978-3-031-97623-0\_1. URL https://doi.org/10.1007/978-3-031-97623-0\_1

[30] D. Hu, Z. Ma, X. Zhang, P. Li, D. Ye, B. Ling, The concept drift problem in android malware detection and its solution, Secur. Commun. Networks 2017 (2017) 4956386:1–4956386:13. doi:10.1155/2017/4956386.

[31] Z. Chen, Z. Zhang, Z. Kan, L. Yang, J. Cortellazzi, F. Pendlebury, F. Pierazzi, L. Cavallaro, G. Wang, Is it overkill? analyzing featurespace concept drift in malware detectors, in: IEEE, IEEE, 2023, pp. 21–28. doi:10.1109/SPW59333.2023.00007.

[32] A. Guerra-Manzanares, M. Luckner, H. Bahsi, Corrigendum to concept drift and cross-device behavior: Challenges and implications for efective android malware detection computers & security, volume 120, 102757, Comput. Secur. 124 (2023) 102998. doi:10.1016/J.COSE.2022.102998.

[33] T. Chow, Z. Kan, L. Linhardt, L. Cavallaro, D. Arp, F. Pierazzi, Drift forensics of malware classifiers, in: M. Pintor, X. Chen, F. Tramèr (Eds.), ACM, ACM, 2023, pp. 197–207. doi:10.1145/3605764.3623918.

[34] A. Abusnaina, Y. Wang, S. S. Arora, K. Wang, M. Christodorescu, D. Mohaisen, Burning the adversarial bridges: Robust windows malware detection against binary-level mutations, CoRR abs/2310.03285 (2023). arXiv:2310.03285, doi:10.48550/ARXIV.2310.03285.

[35] A. Abusnaina, A. Anwar, S. Alshamrani, A. Alabduljabbar, R. Jang, D. Nyang, D. Mohaisen, Systematically evaluating the robustness of ml-based iot malware detection systems, in: RAID, ACM, 2022, pp. 308–320.

[36] F. Hinder, V. Vaquet, B. Hammer, Adversarial attacks for drift detection, CoRR abs/2411.16591 (2024). arXiv:2411.16591, doi:10.48550/ARXIV.2411.16591.

[37] P. Faruki, R. Bhan, V. Jain, S. Bhatia, N. E. Madhoun, R. Pamula, A survey and evaluation of android-based malware evasion techniques and detection frameworks, Inf. 14 (7) (2023) 374. doi:10.3390/INFO14070374.

[38] T. S. Sethi, M. M. Kantardzic, Handling adversarial concept drift in streaming data, Expert Syst. Appl. 97 (2018) 18–40. doi:10.1016/J.ESWA.2017.12.022.

[39] L. Korycki, B. Krawczyk, Adversarial concept drift detection under poisoning attacks for robust data stream mining, Mach. Learn. 112 (10) (2023) 4013–4048. doi:10.1007/S10994-022-06177-W.

[40] P. Chen, H. Zhang, Y. Sharma, J. Yi, C. Hsieh, ZOO: zeroth order optimization based black-box attacks to deep neural networks without training substitute models, in: Proceedings of the 10th ACM Workshop on Artificial Intelligence and Security, AISec@CCS 2017, Dallas, TX, USA, November 3, 2017, ACM, 2017, pp. 15–26. doi:10.1145/3128572.3140448.

[41] I. Rosenberg, A. Shabtai, Y. Elovici, L. Rokach, Query-eficient blackbox attack against sequence-based malware classifiers, in: ACSAC ’20: Annual Computer Security Applications Conference, Virtual Event / Austin, TX, USA, 7-11 December, 2020, ACM, 2020, pp. 611–626. doi:10.1145/3427228.3427230.

[42] J. Yuste, E. G. Pardo, J. Tapiador, Optimization of code caves in malware binaries to evade machine learning detectors, Comput. Secur. 116 (2022) 102643. doi:10.1016/J.COSE.2022.102643.

[43] H. S. Anderson, A. Kharkar, B. Filar, D. Evans, P. Roth, Learning to evade static PE machine learning malware models via reinforcement learning, CoRR abs/1801.08917 (2018). arXiv:1801.08917.

[44] W. Hu, Y. Tan, Generating adversarial malware examples for black-box attacks based on GAN, in: Data Mining and Big Data - 7th International Conference, DMBD 2022, Beijing, China, November 21-24, 2022, Proceedings, Part II, Vol. 1745 of Communications in Computer and Information Science, Springer, 2022, pp. 409–423. doi:10.1007/978-981- 19-8991-9\_29.

[45] G. Apruzzese, A. Fass, F. Pierazzi, When adversarial perturbations meet concept drift: An exploratory analysis on ML-NIDS, in: AISec 2024, Salt Lake City, UT, USA, October 14-18, 2024, ACM, 2024, pp. 149– 160. doi:10.1145/3689932.3694757. URL https://doi.org/10.1145/3689932.3694757

[46] N. Papernot, P. D. McDaniel, I. J. Goodfellow, S. Jha, Z. B. Celik, A. Swami, Practical black-box attacks against machine learning, in: Proceedings of the 2017 ACM on Asia Conference on Computer and Communications Security, AsiaCCS 2017, Abu Dhabi, United Arab Emirates, April 2-6, 2017, ACM, 2017, pp. 506–519. doi:10.1145/3052973.3053009. URL https://doi.org/10.1145/3052973.3053009

[47] Y. Liu, X. Chen, C. Liu, D. Song, Delving into transferable adversarial examples and black-box attacks, in: 5th International Conference on Learning Representations, ICLR 2017, Toulon, France, April 24-26, 2017, Conference Track Proceedings, OpenReview.net, 2017. URL https://openreview.net/forum?id=Sys6GJqxl

[48] K. Grosse, N. Papernot, P. Manoharan, M. Backes, P. D. McDaniel, Adversarial examples for malware detection, in: Computer Security - ESORICS 2017 - 22nd European Symposium on Research in Computer Security, Oslo, Norway, September 11-15, 2017, Proceedings, Part II, Lecture Notes in Computer Science, Springer, 2017, pp. 62– 79. doi:10.1007/978-3-319-66399-9\_4. URL https://doi.org/10.1007/978-3-319-66399-9\_4

[49] J. Uesato, B. O’Donoghue, P. Kohli, A. van den Oord, Adversarial risk and the dangers of evaluating against weak attacks, in: Proceedings of the 35th International Conference on Machine Learning, ICML 2018, Stockholmsmässan, Stockholm, Sweden, July 10-15, 2018, Vol. 80 of Proceedings of Machine Learning Research, PMLR, 2018, pp. 5032– 5041.