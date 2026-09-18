---
title: "2026-Haiba-SIM-Tagged-TTL-Anomaly"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2026-Haiba-SIM-Tagged-TTL-Anomaly.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

Article

# Unsupervised TTL-Based Deep Learning for Anomaly Detection in SIM-Tagged Network Traffic

Babe Haiba \* and Najat Rafalia \*

Computer Science Research Laboratory (LaRI), Faculty of Sciences, Ibn Tofail University, Kenitra 14000, Morocco \* Correspondence: babe.haiba@uit.ac.ma (B.H.); najat.rafalia@uit.ac.ma (N.R.)

## Abstract

The rise of SIM cloning, identity spoofing, and covert manipulation in mobile and IoT networks has created an urgent need for continuous post-registration verification. This work introduces an unsupervised deep learning framework for detecting behavioral anomalies in SIM-tagged network flows by modeling the intrinsic structure of benign behavioral descriptors (TTL, timing drift, payload statistics). A Temporal Deep Autoencoder (TDAE) combining Conv1D layers and an LSTM encoder is trained exclusively on normal traffic and used to identify deviations through reconstruction error, enabling one-class (label-free) training. For deployment, alarms are set using an unsupervised quantile threshold τ calibrated on benign traffic with a false-alarm budget; τ<sup>∗</sup> is reported only as a diagnostic reference for model comparison. To ensure realism, a large-scale corpus of 3.6 million SIM-tagged flows was constructed by enriching public IoT traffic with pseudo-operator identifiers (synthetic SIM tags derived from device identifiers) and controlled anomaly injections. Cross-domain experiment transfer under SIM-grouped protocol: Training on clean Cassavia-like traffic and testing on attack-rich Guarascio-like flows yields a PR-AUC of 0.93 for the proposed Conv-LSTM Temporal Deep Autoencoder, outperforming Dense Autoencoder, Isolation Forest, One-Class SVM, and LOF baselines. Conversely, the reverse direction collapses to $\mathrm { P R - A U C } \approx 0 . 5 ,$ , confirming the absence of data leakage and the validity of one-class behavioral learning. Sensitivity analysis shows that performance is stable around the unsupervised quantile operating point. Overall, the proposed framework provides a lightweight, interpretable, and data-efficient behavioral verification layer for detecting cloned or unauthorized SIM activity, complementing existing registration mechanisms in next-generation telecom and IoT ecosystems.

Keywords: unsupervised learning; deep autoencoder; IoT security; SIM anomaly detection; TTL dynamics; cross-domain generalization; network behavior modeling

## Check for updates

Academic Editors: Hai Liu and Feng Tian

Received: 24 November 2025 Revised: 20 January 2026 Accepted: 21 January 2026 Published: 4 February 2026

Copyright: © 2026 by the authors. Licensee MDPI, Basel, Switzerland. This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license.

## 1. Introduction

The secure registration and continuous validation of Subscriber Identity Modules (SIMs) are essential components of modern telecommunication and IoT infrastructures. As networks grow in scale and heterogeneity, ensuring that each registered SIM corresponds to an authentic and behaviorally consistent entity has become increasingly challenging. Traditional SIM registration processes rely on document checks, operator-side verification, or cryptographic identifiers, which provide strong guarantees at enrollment but offer limited protection against post-registration threats such as SIM cloning, identity spoofing, or covert manipulation of network flows. These attacks undermine user trust, enable unauthorized access, and degrade the integrity of large distributed systems.

Recent studies have shown that low-level protocol fields can serve as reliable behavioral fingerprints for device and identity verification. Among these, the Internet Protocol (IP) Time-To-Live (TTL) value has emerged as a particularly stable indicator of communica tion patterns. Under legitimate operation, TTL distributions remain statistically consistent over time, while deviations often signal hidden routing paths, covert channels, or anoma lous device behavior [1–3]. Cassavia et al. [4] demonstrated the effectiveness of sparse autoencoders for modeling TTL-based dynamics in IoT networks, and Guarascio et al. [2] showed that unsupervised neural architectures generalize well to unseen attack patterns across heterogeneous devices. SIM-tagged monitoring adds a key constraint: anomaly evidence must be attributable to a persistent identity unit to support post-registration verification and response. This motivates SIM-level aggregation and one-class modeling of normal behavior across heterogeneous sessions, rather than device-level traces alone. Accordingly, we reformulate TTL/timing-based detection around SIM-tagged aggregates and evaluate cross-domain generalization for SIM-grouped splits in Section 3.5. When operator-grade identifiers are unavailable in public corpora, we use privacy-preserving pseudo-identifiers derived from device IDs and interpret the conclusions for this abstrac tion. Building on these insights, this study introduces a fully unsupervised deep learning framework for detecting anomalous behavior in SIM-tagged network traffic. The central idea is to train a hybrid Conv–LSTM autoencoder—referred to throughout this manuscript as the TDAE—exclusively on benign traffic so as to learn the intrinsic manifold of normal SIM communication. Flows that deviate from this learned structure, measured through reconstruction error, are flagged as anomalous without requiring any attack labels. This approach is particularly well suited to telecom environments, where attack data are scarce, evolving, or unavailable, and where large-scale monitoring must operate without violating privacy constraints.

To support a realistic evaluation, a large corpus of more than 3.6 million SIM-tagged flows was constructed by enriching public IoT traffic with pseudo-operator identifiers (synthetic SIM tags derived from device identifiers) and controlled anomaly injections. This enables cross-domain analysis across two heterogeneous sources: a clean Cassavia-like dataset and a mixed, attack-rich Guarascio-like dataset. The proposed TDAE is compared against established unsupervised baselines, including Dense Autoencoder, Isolation Forest, One-Class SVM, and Local Outlier Factor. Experiments demonstrate that models trained on benign Cassavia traffic achieve cross-domain transfer under a SIM-grouped protocol when tested on Guarascio flows, with the TDAE reaching a PR-AUC of 0.93. The opposite direction, however, collapses to PR-AUC ≈ 0.5, confirming the absence of data leakage and validating the one-class hypothesis. Compared to prior TTL-based covert-channel detection and IoT anomaly monitoring [1–3,5], we summarize our contributions as follows:

Methodological (transferable): A SIM-centric behavioral verification formulation under strict one-class learning conditions, where normality is learned from benign SIM\_tagaggregated traffic using TTL/timing descriptors.

Experimental validation (transferable protocol): A systematic cross-domain evaluation between Cassavia-like and Guarascio-like distributions, designed to reflect distribu tion shift under strict one-class assumptions.

Engineering (partially transferable): A SIM-tagged corpus derived from public IoT traffic using de-identified pseudo-identifiers (SIM tags synthesized from device IDs) and controlled anomaly injections; the construction procedure remains replicable when operator identifiers are not accessible.

By integrating behavioral analytics with SIM-level identity tracking, this study supports data-efficient post-registration monitoring for telecom and IoT traffic while avoiding reliance on subscriber-identifying metadata.

Research framework and generalizable takeaway

We (i) constructed a SIM-tagged dataset from public IoT traffic with controlled anomaly injections, (ii) extracted normalized TTL/timing/payload descriptors on sliding SIM windows, and (iii) trained a strict one-class temporal autoencoder on benign source data to score target windows by reconstruction error; evaluation follows a SIM-grouped crossdomain protocol and reports PR-AUC and FAR-constrained operating-point metrics. Beyond the SIM use case, the transferable insight is that one-class reconstruction becomes deployment-relevant when paired with identity-level aggregation, leakage-safe group-wise splits, and operating-point selection with explicit false-alarm budgets—an evaluation pattern that applies to other persistent identifiers (e.g., accounts, devices, API keys) under distribution shift conditions.

## 2. Related Work

Research at the intersection of covert communication analysis, IoT anomaly detection, and behavioral traffic modeling has expanded significantly over the past decade. This section reviews the key developments that directly motivate the present SIM-oriented anomaly detection framework, with emphasis on TTL-based behavioral learning and unsupervised neural architectures.

## 2.1. Foundations of Covert Channel Detection

Covert channels were first conceptualized by Lampson [6] as unintended communication paths that bypass system policies. Rowland [7] later demonstrated that protocol header fields—specifically TTL and IP identification—could be manipulated to embed hidden information. Comprehensive taxonomies by Zander et al. [8] and Wendzel et al. [9] classified covert channels according to modulation strategy, detectability, and robustness, while Mazurczyk et al. [10] highlighted how subtle header irregularities can reveal hidden communication. Together, these studies established the conceptual basis for behavioral inspection of low-level network features.

## 2.2. Machine Learning for Covert and Irregular Traffic

As network environments grew more complex, data-driven detection gained promi nence. Early machine learning approaches, such as clustering [11] and timing-based analysis [12], focused on identifying irregular patterns without explicit signatures. Later surveys by Elsadig et al. [13] and Zillien and Wendzel [14] argued that static, rule-based systems cannot generalize to heterogeneous IoT devices, advocating adaptive models capable of learning normal behavior directly from traffic. More recent work incorporated entropy metrics and neural embeddings to detect covert manipulations in DNS and packet timing [15,16], demonstrating that unsupervised deep learning can identify anomalies even without labeled attack data.

## 2.3. Deep Learning and TTL-Based Behavioral Modeling

Deep autoencoders marked a major shift in covert-channel research. Guarascio et al. [2] showed that TTL variations can be effectively modeled as latent behavioral signatures, enabling detection of covert or irregular flows with unsupervised learning. Cassavia et al. [1] further improved this approach using sparse autoencoder ensembles, increasing stability across heterogeneous devices. Their more recent study [4] validated the method on the Sivanathan IoT dataset, demonstrating strong performance with controlled anomaly injections generated with pcapStego [17]. Liguori et al. [18] and Caviglione et al. [3] extended these paradigms to distributed and mixture-of-experts architectures, improving detection of weak covert signals.

These works collectively establish TTL as a reliable behavioral indicator and confirm the effectiveness of autoencoder-based anomaly detection—both central ingredients of the present study.

## 2.4. Behavioral Anomaly Detection in IoT Systems

Parallel researcsh trends focused on modeling device behavior rather than detecting specific signatures. Doshi et al. [19] demonstrated that reconstruction error can reveal early DDoS activity. Mirsky et al. [5] introduced Kitsune, an online ensemble of autoencoders optimized for real-time IoT anomaly detection. Subsequent work by Abusitta et al. [20] and Vidhya et al. [21] improved scalability and energy efficiency, confirming that behavioral baselines built from low-level metrics (TTL, inter-arrival time, entropy) can detect compromised or cloned IoT devices.

This line of research supports the feasibility of applying reconstruction-based behavioral learning to SIM-tagged network flows.

## 2.5. Dataset Provenance and Extension

The present work builds directly upon the contributions of Cassavia et al. and Guarascio et al. by expanding their TTL-based methodologies to a significantly larger and more heterogeneous context. Flows derived from public IoT corpora were merged, normalized, and enriched with operator-level identifiers such as SIM\_tag, Session\_ID, and device\_id, resulting in a corpus of 3.6 million SIM-tagged flows. Controlled anomalies were reinjected at low rates (1–10%) using the methodology described in [4], preserving the statistical structure of benign traffic. This design enables both in-domain and cross-domain evalua tions across two distinct distributions: a benign Cassavia-like dataset and an attack-rich Guarascio-like dataset.

## 2.6. Positioning of the Present Work

Most prior research addressed either covert-channel detection or behavioral modeling in IoT networks (Figure 1), but few studies explored their application to telecom-grade SIM verification. This study extends TTL-based autoencoder modeling to SIM-tagged traffic and demonstrates strong cross-domain generalization when training on benign flows and testing on mixed distributions. The resulting framework provides a lightweight, fully unsupervised verification layer that complements classical SIM registration without relying on sensitive identifiers or labeled attack data Table 1.

In comparison with the closest TTL-based autoencoder studies by Cassavia et al. and Guarascio et al., the main differences are methodological rather than scale-driven. First, we compute hybrid statistical descriptors over temporal windows from packet-level signals (TTL, inter-arrival time, payload size), including TTL mean/dispersion, timing drift, and payload statistics, all z-score normalized. Second, we aggregate flows by SIM\_tag to perform persistent identity-level analysis without subscriber-identifying metadata. Third, we adopt a strict one-class setting with a SIM-grouped cross-domain protocol (Cassavia like → Guarascio-like and the reverse) with controlled anomaly injections (1–10%). When operator-grade identifiers are unavailable, pseudo-identifiers derived from device IDs are used as a practical approximation, and conclusions are interpreted accordingly.

Table 1. Positioning of the present framework relative to prior research in covert-channel detection and IoT anomaly modeling.

<table><tr><td>Reference</td><td>Domain/Dataset</td><td>Methodology</td><td>Key Contribution</td><td>Limitations/Extension</td></tr><tr><td>Wendzel et al. [9,15] (2015, 2021)</td><td>Covert channels</td><td>Taxonomy, patterns</td><td>Formal classification of hiding techniques</td><td>No validation on IoT or SIM data</td></tr><tr><td>Guarascio et al. [2] (2022)</td><td>IoT traffic (TTL-based)</td><td>Sparse AE</td><td>TTL-field anomaly detection</td><td>Small-scale dataset</td></tr><tr><td>Cassavia et al. [1,4] (2022, 2024)</td><td>IoT dataset (augmented)</td><td>AE ensembles + injections</td><td>Covert TTL manipulation detection</td><td>Focused on IoT devices only</td></tr><tr><td>Liguori et al. [18] (2023)</td><td>Softwarized IoT</td><td>Distributed AE</td><td>Detection in virtualized devices</td><td>No subscriber-level identifiers</td></tr><tr><td>Caviglione et al. [3] (2024)</td><td>Cloud traffic</td><td>Mixture-of-experts</td><td>Robust to weak covert signals</td><td>No SIM-level behavioral modeling</td></tr><tr><td>This work (2025)</td><td>SIM-tagged IoT + telecom dataset (3.6 M flows)</td><td>Hybrid autoencoder TDAE</td><td>Behavioral anomaly detection for SIM identities</td><td>Extends covert TTL research to telecom ecosystems</td></tr></table>

![](images/cad3c265e2c81e22a7e682e75725e2b2930fe29ddb19488dc773e7e9892bf0ce.jpg)  
Figure 1. Chronological evolution of research directions from covert-channel analysis [1,2,5,9].

## 3. Materials and Methods

This section presents the dataset construction, feature engineering steps, autoencoder architecture, validation strategy, and experimental environment used in the proposed unsupervised framework for detecting anomalies in SIM-tagged network communications. The objective is to learn stable behavioral signatures—primarily through TTL and timing dynamics—that characterize legitimate SIM activity and to identify deviations indicative of cloning, spoofing, or unauthorized access.

## 3.1. Framework Overview

The system operates in three main stages: (i) preprocessing and aggregation of flows by SIM\_tag, (ii) extraction and normalization of behavioral statistical descriptors, and (iii) anomaly detection through reconstruction error using the TDAE.

Figure 2 illustrates the full workflow, including the adaptive feedback mechanism that enables the model to integrate newly observed benign behavior over time.

Data Preprocessing: Raw network flows are grouped by SIM\_tag, ensuring persistent identity tracking without exposing real operator metadata. Packet-level features (TTL, Inter-Arrival Time, payload size) are cleaned, time-ordered, and validated to remove corrupted entries.

Feature Representation: Hybrid statistical descriptors of benign behavior (TTL mean and dispersion, timing drift, payload statistics) are computed over temporal windows and standardized using z-score normalization to stabilize training across heterogeneous SIM identities.

Anomaly Detection: The TDAE is trained exclusively on benign sequences to learn the intrinsic manifold of normal SIM behavior. Reconstruction error is used as the anomaly score, and samples whose error exceeds a calibrated threshold are flagged as anomalous in a fully unsupervised manner.

![](images/0db898c15a9189735a7e0f40c60b46293fc83e085f96787ada0c0d372c529235.jpg)  
Figure 2. High-level architecture of the proposed TTL-based anomaly detection framework: preprocessing and SIM-level aggregation, feature extraction, one-class reconstruction learning, and alarm decision.

## Implementation details

We form sliding windows per SIM\_tag with L = 64 and stride 16, yielding $X \in \mathbb { R } ^ { N \times 6 4 \times 4 }$ over the normalized features. The model maps each window through Conv1D blocks followed by an LSTM encoder, a bottleneck representation, and a mirrored decoder to reconstruct xˆ. The anomaly score is the window-level mean squared reconstruction error $s ( x ) = \| x - { \hat { x } } \| ^ { 2 }$ averaged over time and features. Decisions use $\tau ^ { * }$ for diagnostic comparison (Table 4) or $\tau _ { \alpha }$ for fully unsupervised operation with a FAR budget (Table 5).

## 3.2. Dataset Origin and Composition

The dataset was constructed by merging two widely used IoT corpora:

Cassavia et al. (2022–2024) [1,4]: Covert-traffic-augmented IoT traces with TTL modulation and timing perturbations.

• Guarascio et al. (2022) [2]: TTL-based IoT anomaly detection dataset.

We extend these sources by introducing three metadata fields—SIM\_tag, Session\_ID, and device\_id. Because no operator-level identities exist in the public datasets, SIM\_tag is synthetically generated as:

$$
\text { SIM\_tag } = \text { hash } (\text { device\_id }) \bmod N _ {\text { SIM }},
$$

pseudo-identifiers for SIM-grouped analysis without subscriber-identifying fields.

The final corpus, Combined\_SIM\_Minimized, contains approximately:

• 3.6 million flows;

1532 synthetic SIM identities;

• 1–10% controlled anomalies, injected according to Cassavia’s methodology.

Although the “SIM-tag” field mimics operator-grade subscriber identifiers, it is entirely synthetic and derived from public IoT traces as shown in Table 2. As such, the present evaluation should be interpreted as a realistic approximation of operator scenarios rather than a study on production telecom data.

Table 2. Dataset composition and feature taxonomy.

<table><tr><td>Feature Group</td><td>Attributes</td><td>Type</td><td>Example</td></tr><tr><td>Payload</td><td>mean_pkt_size, entropy, IAT</td><td>Continuous</td><td>124.5, 0.81, 0.0042</td></tr><tr><td>Temporal</td><td>duration, start_time, end_time</td><td>Continuous</td><td>6.8 s, 12:04:11, 12:04:18</td></tr><tr><td>Protocol</td><td>ttl_proxy</td><td>Integer</td><td>57</td></tr><tr><td>Metadata</td><td>SIM_tag, Session_ID, device_id</td><td>Categorical</td><td>SIM1092, S45, IoT-cam-03</td></tr></table>

## 3.3. Autoencoder Architecture and Hyperparameters

The anomaly detector is implemented as a hybrid Conv–LSTM Temporal Deep Autoencoder designed to capture both local packet-level variations and long-range temporal dependencies in SIM-tagged network flows. The encoder first applies two Conv1D blocks to extract short-term behavioral patterns, followed by an LSTM layer that summarizes temporal structure into a compact latent vector. The decoder then reconstructs the full temporal window using a mirrored LSTM layer followed by dense time-distributed projections.

Formally, the architecture is defined as:

$$
\text { Encoder:   } \operatorname{Conv1D} (6 4) \to \operatorname{Conv1D} (6 4) \to \operatorname{LSTM} (6 4) \to \operatorname{Dense} (3 2) \to \operatorname{Dense} (8),
$$

$$
\text { Decoder:   } \text { RepeatVector } (L) \to \text { LSTM } (6 4) \to \text { TimeDistributed } (\text { Dense }) (6 4) \to \text { Dense } (n).
$$

All hidden layers use ReLU activations, while the reconstruction layer uses a linear mapping. The model is trained exclusively on benign windows, following a one-class learning paradigm.

## Hyperparameter rationale

Table 3 summarizes the fixed settings used in all experiments for reproducibility. We set $L = 6 4$ and stride 16 to capture mid-range temporal context per SIM\_tag while keeping overlap and runtime manageable. Adam $( \eta = 1 0 ^ { - 3 } )$ with early stopping stabilizes oneclass reconstruction training, and dropout/layer normalization improve robustness under cross-domain shift conditions. All hyperparameters are kept identical across folds and baselines. For comparison, a Dense Autoencoder (AE) baseline is also implemented with a fully-connected architecture: Encoder: $\begin{array} { r } { \mathrm { n }  6 4  3 2  1 6  8 } \end{array}$ , Decoder: $8  1 6  3 2 $ $6 4  \mathrm { n }$ . All hidden layers use ReLU activations, and the model is trained with the same optimizer, batch size, and early-stopping criteria as the TDAE. For the reproducibility and threshold robustness, the reader is referred to Appendix A.

## 3.4. Anomaly Scoring and Thresholding

The reconstruction error is computed as:

$$
\operatorname{MSE} (x) = \frac {1}{d} \sum_ {j = 1} ^ {d} (x _ {j} - \hat {x} _ {j}) ^ {2}.
$$

During validation, we sweep candidate thresholds and select the F1-optimal operating point $\tau ^ { * }$ on the precision–recall curve (diagnostic reference only). For deployment-oriented operation (labels unavailable), each window x is scored by MSE(x), and the alarm threshold $\tau _ { \alpha }$ is set as the (1 − α) quantile of benign-only scores collected from a rolling targetenvironment buffer, enforcing a false-alarm budget α.

## 3.5. Validation Protocol and Baseline Models

We adopt a GroupKFold strategy based on SIM identities to avoid leakage between training and testing. This ensures realistic evaluation of generalization to unseen devices.

Table 3. Hyperparameter summary for the TDAE and baselines.

<table><tr><td>Component</td><td>Parameter</td><td>Value/Setting</td><td>Purpose</td></tr><tr><td>Conv1D blocks</td><td>Filters/kernel</td><td>64/3</td><td>Local temporal feature extraction</td></tr><tr><td>LSTM layer</td><td>Units</td><td>64</td><td>Long-range temporal modeling</td></tr><tr><td>Latent bottleneck</td><td>Dense layers</td><td>32 → 8</td><td>Compression of temporal signature</td></tr><tr><td>Decoder</td><td>LSTM + TD Dense</td><td>Mirror structure</td><td>Sequence reconstruction</td></tr><tr><td>Optimizer</td><td>Adam</td><td> $\eta = 10^{-3}$ </td><td>Stable convergence</td></tr><tr><td>Batch size/epochs</td><td>Training</td><td>256/50</td><td>Prevent overfitting</td></tr><tr><td>Regularization</td><td>Dropout/LayerNorm</td><td>0.15/yes</td><td>Stability and robustness</td></tr><tr><td>Threshold</td><td>Anomaly cutoff</td><td>Max-F1 on validationPR curve</td><td>One-class training; threshold tuned on validation</td></tr><tr><td>Isolation Forest</td><td>Contamination</td><td>0.05</td><td>Baseline comparison</td></tr><tr><td>OC-SVM</td><td>kernel/ $\nu$ </td><td>RBF/0.05</td><td>Baseline comparison</td></tr></table>

Metrics include accuracy, precision, recall, F1-score, ROC-AUC, and PR-AUC (preferred under imbalance conditions).

Baselines:

• Isolation Forest (100 estimators; contamination = 0.05);

• One-Class SVM (RBF kernel; = 0.05);

Dense Autoencoder (fully-connected AE with latent size 8, same training schedule as TDAE);

• Local Outlier Factor (35 neighbors; contamination = 0.05).

## 3.6. Experimental Procedure (Pseudocode)

The full experimental pipeline used to train and evaluate the proposed TDAE is summarized below. The procedure enforces strict identity separation through SIM-based GroupKFold, prevents any form of leakage, and performs fully unsupervised threshold calibration using reconstruction error as shown in Algorithm 1.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Training and Evaluation Pipeline for the Conv–LSTM TDAE
1: Input: IoT datasets  $D_{CAS}$ ,  $D_{GUA}$ 
2: Output: Fold-wise metrics (PR-AUC, ROC-AUC, F1)
3: Load and preprocess Cassavia-like and Guarascio-like traffic
4: Generate synthetic SIM_tag from device identifiers
5: Sort flows chronologically per SIM identity
6: for each SIM identity do
7: Aggregate packets into sliding windows
8: Compute TTL, IAT, payload and drift descriptors
9: end for
10: Normalize features with z-score using training data only
11: Split windows using GroupKFold (groups = SIM_tag)
12: for each fold k do
13: Train TDAE on benign windows of the training split
14: Compute reconstruction errors on test windows
15: Select  $\tau^{*}$  as the  $\tau_{\alpha}$  (quantile benign buffer) for deployment;  $\tau^{*}$  diagnostic only on the validation PR curve
16: Classify windows as anomalous if MSE(x) &gt;  $\tau$ 
17: Compute PR-AUC, ROC-AUC, F1, Precision, Recall
18: end for
19: Aggregate metrics across folds and report mean and variance
</div>

## 3.7. Experimental Environment and Reproducibility

All experiments were conducted on Google Colab (Tesla T4 GPU, 16 GB RAM). To support reproducibility, we fixed random seeds and report the full set of key training and evaluation settings (window length $L = 6 4$ , stride 16, feature normalization, GroupKFold by SIM\_tag, and the two thresholding regimes $\tau ^ { * } \mathbf { \Delta v s } . \tau _ { \alpha } )$ . Implementation used Python 3 with TensorFlow/Keras and scikit-learn; version details and scripts (preprocessing, training, and evaluation notebooks) will be released in an open-access archive upon acceptance.

## 4. Results and Discussion

This section reports the cross-domain detection results and robustness analyses. We evaluate anomaly detectors trained on benign SIM-tagged flows. The results are aggregated over five SIM-grouped GroupKFold splits (Section 3.5).

## 4.1. Cross-Domain Detection: Cassavia → Guarascio

Training on the benign Cassavia-like dataset and testing on the mixed Guarascio dataset yields consistently strong detection performance across all one-class models. The TDAE achieves the highest performance as shown in Table 4. Classical baselines—Dense Autoencoder, One-Class SVM, and Isolation Forest—perform similarly well, while LOF exhibits clear limitations on sparse temporal manifolds.

## Operating-point evaluation (deployment-oriented)

For deployment, labels are unavailable; therefore, we report fully unsupervised operating points for explicit false-alarm budgets $\alpha \in \{ 1 \% , 5 \% \}$ . We calibrated $\tau _ { \alpha }$ as the $( 1 - \alpha )$ quantile of benign-only scores collected from a rolling target-environment buffer and then measured recall on the target domain (Table 5). For completeness, we also report results at the $\tau _ { \alpha }$ (quantile benign buffer) for deployment and in the $\tau ^ { * }$ diagnostic only a diagnostic upper bound for like-for-like model comparison (Table 4). For very strict budgets (e.g., 1%), score overlap across domains can yield near-zero recall for some models, whereas $\alpha = 5 \%$ recovers higher recall, reflecting practical SOC/SIEM trade-offs.

Table 4. Cross-domain (Cassavia → Guarascio). The results at the diagnostic F1-optimal threshold $\tau ^ { * }$ (label-dependent), reported for model comparison.

<table><tr><td>Model</td><td>PR-AUC</td><td>F1*</td><td>Precision</td><td>Recall</td><td>Accuracy</td></tr><tr><td>TDAE</td><td>0.930 ± 0.012</td><td>0.98</td><td>0.96</td><td>0.99</td><td>0.984</td></tr><tr><td>Dense Autoencoder</td><td>0.918 ± 0.015</td><td>0.81</td><td>0.73</td><td>0.91</td><td>0.730</td></tr><tr><td>One-Class SVM</td><td>0.917 ± 0.018</td><td>0.84</td><td>0.77</td><td>0.94</td><td>0.750</td></tr><tr><td>Isolation Forest</td><td>0.911 ± 0.020</td><td>0.79</td><td>0.71</td><td>0.88</td><td>0.700</td></tr><tr><td>Local Outlier Factor</td><td>0.577 ± 0.030</td><td>0.84</td><td>0.73</td><td>1.00</td><td>0.730</td></tr></table>

F1<sup>∗</sup> is computed at the label-dependent F1-optimal threshold $\tau ^ { * }$ selected on the validation set.

In addition to ML baselines, we include lightweight TTL heuristics (TTL-JSD divergence and a temporal change-rate rule) to quantify the gain beyond rule-based detectors. These heuristics serve as transparent sanity baselines rather than full state-of-the-art com petitors, providing context for improvements over simple TTL-only rules. They may still be preferable for lightweight monitoring or rapid triage when only TTL fields are available or when operators require fully interpretable threshold rules. With the same FAR budgets, these heuristics remain substantially below the proposed TDAE at realistic operating points (Table 5), highlighting that the performance gain is not explained by simple TTL rules.

Table 5. Operating-point metrics under the strict one-class cross-domain protocol (Cassavia → Guarascio). Thresholds are calibrated on a benign-only buffer from the target environment (quantile based) then evaluated on the target domain.

<table><tr><td>Model</td><td>R@FAR = 1%</td><td>R@FAR = 5%</td></tr><tr><td>TDAE</td><td>0.000</td><td>0.712</td></tr><tr><td>Dense AE</td><td>0.000</td><td>0.714</td></tr><tr><td>Isolation Forest</td><td>0.000</td><td>0.644</td></tr><tr><td>One-Class SVM</td><td>0.000</td><td>0.713</td></tr><tr><td>LOF</td><td>0.001</td><td>0.013</td></tr><tr><td>TTL-JSD (heuristic)</td><td>0.147</td><td>0.289</td></tr><tr><td>TTL-change-rate (heuristic)</td><td>0.072</td><td>0.223</td></tr></table>

## Interpretability (feature-wise errors and cases)

We decompose the reconstruction error into per-feature MSE on the target domain to identify which attributes dominate alarms (Figure 3). We also report representative TP/FP/FN windows under the same unsupervised $\tau _ { \alpha }$ protocol (Figure 4). Operator-facing interpretation: alarms are most reliable when driven by abrupt devia tions in flow-duration and payload statistics (clear TP signatures), whereas false positives often correspond to benign regime shifts that change these features without malicious injections. Conversely, mild or adaptive deviations that preserve duration/payload/TTL statistics may remain below $\tau _ { \alpha }$ and yield false negatives, suggesting that analysts should treat low-margin scores as weak evidence and corroborate them with drift indicators and complementary telemetry.

## Representative case studies (TP/FP/FN)

We complement the feature-wise analysis with three representative target-domain windows selected post hoc under the same unsupervised operating-point protocol as Table 5 (quantile-based $\tau _ { \alpha }$ calibrated on a benign buffer). Figure 4 shows a TP dominated by flow-duration/payload reconstruction mismatches, an FP consistent with an abrupt but plausibly benign regime change, and an FN where deviations remain below $\tau _ { \alpha }$ . These cases provide concrete feature-level evidence of what triggers (or fails to trigger) alarms under strict one-class training conditions.

Feature-wise reconstruction error (CAS GUA, FAR=5% threshold)  
![](images/bb44f522c305a7cf89b6ffc22ff32b55d8a19e8277949cd3cfce0d8e90372db4.jpg)  
Figure 3. Feature-wise reconstruction error breakdown (Cassavia → Guarascio). Per-feature MSE is reported for benign windows (TN) and for detected alarms, highlighting which behavioral attributes dominate the anomaly score.

![](images/9a3b15a8bc65f264db7da40123f33d4767adf3728b58b9f8b544af08760a97af.jpg)

![](images/827d69ac4b2597cb4586c99e335672e56421cee7385b60cfa54a56fdb5566c5f.jpg)

![](images/9ea2357755c8875fd1920a36a075ffbf3a76de82ae17a3d1cd1d02f34eddb295.jpg)

![](images/fdbcbd52d7bf050918ca92ad0b43135d86483f1ae1801c523fc4d75fbcbc9973.jpg)

FN (missed anomaly) (score=0.493) ttl\_proxy  
![](images/49f3ef98b2ec089d6c118d9329297c65b2b9d8ad88a88d4e9b36e66fb15a99ea.jpg)

![](images/05c3af72ba999089a4deff5e11b20822fc3ee3b69de4bf3fd86167ac7156a2ff.jpg)  
Figure 4. TP/FP/FN case studies (Cassavia → Guarascio) showing features driving alarms under $\tau _ { \alpha }$ .

## Interpretation

Training on clean benign traffic yields a compact reconstruction support; anomalies in the target domain tend to fall outside this support and produce higher errors (Figure 5).

## 4.2. Reverse Direction: Guarascio → Cassavia

Training on Guarascio (mixed benign/anomalous) and testing on Cassavia (benignonly) yields PR- $. \mathrm { A U C } ~ \approx ~ 0 . 5 0$ , i.e., near-random performance (Figure 6). We use this direction primarily as an integrity check: under the SIM-grouped protocol, any leakage or memorization of identity-specific artifacts would typically inflate performance in both directions, which is not observed here.

## Representation-level interpretation

The clean → mixed vs. mixed → clean asymmetry can be explained by support/coverage and score-overlap. When trained on a cleaner benign source (Cassavia), the autoencoder fits a tighter manifold of normality, so mixed-domain anomalies more often fall outside this support and incur larger reconstruction errors. Conversely, training on a heterogeneous/mixed source (Guarascio) broadens the learned support, increasing overlap between benign and anomalous reconstruction-error distributions and reducing separabil ity, which can drive PR-AUC toward random. We present this as an empirical explanation consistent with one-class reconstruction learning under distribution shift conditions, not as a guaranteed theoretical property.

![](images/fa8f63015a07d7fcd36c2e75749de964743ad9fd57a8c732d58780780333201f.jpg)  
(a) TDAE

![](images/a9bcbaeb36d3969cb1f6ded309e126a56dae14283954c5c6e621a9114ea32780.jpg)  
(b) Dense Autoencoder

![](images/9c33586cece5da6497d487448b997eedfd95aadba10818ec9a5c9a67fa4074ea.jpg)  
(c) One-Class SVM

![](images/6601407a2a40ddab732b12f70d3ba5ceb575b9ea59f862c167edd3bbd50a6f66.jpg)  
(d) Isolation Forest

![](images/3a215adf9e238ba9e1e71f07356afb4679cc6039587fba3bd0b430fb7b702ad2.jpg)  
(e) Local Outlier Factor

![](images/b30400a233dbf07a173808800763a8259e9fa92ccc44d7ea569e875503ec1180.jpg)  
(f) Aggregated PR-AUC (mean ± variance)  
Figure 5. Precision–recall curves and aggregated PR-AUC for Cassavia → Guarascio. The TDAE and Dense AE exhibit the most stable precision–recall plateaus across folds, while LOF underperforms due to density assumptions on sparse manifolds.

![](images/79a61ce1744345794fa7ae93d879726a7a0b45d0efb5b46c5d7fcf8ad5dc0c7b.jpg)  
(a) Cassavia → Guarascio

![](images/20f91da32500e8505316281b86410e6773eda3c53c171b6c47099e1e7a652da7.jpg)  
(b) Guarascio → Cassavia  
Figure 6. Directional asymmetry in cross-domain transfer (PR curves).

## 4.3. Ablation Study: Conv-Only vs. LSTM-Only Variants

We isolate the contribution of each architectural component by comparing two simplified variants of the TDAE. The Conv-only autoencoder removes recurrent layers and relies on stacked Conv1D blocks to capture local temporal motifs. The LSTM-only autoencoder removes convolutions and uses a recurrent encoder–decoder to model temporal dependencies. All variants are trained with the same strict one-class setting and evaluated on Guarascio using the SIM-grouped cross-domain protocol. As shown in Table 6, both simplified variants perform strongly, but the full hybrid model remains superior.

Table 6. Ablation of the Conv–LSTM TDAE under the strict one-class cross-domain protocol (Cassavia → Guarascio).

<table><tr><td>Variant</td><td>PR-AUC</td><td>F1*</td></tr><tr><td>Conv-only AE (no LSTM)</td><td>0.916</td><td>0.842</td></tr><tr><td>LSTM-only AE (no Conv1D)</td><td>0.918</td><td>0.847</td></tr><tr><td>Hybrid Conv–LSTM (TDAE)</td><td> $0.930 \pm 0.012$ </td><td>0.98</td></tr></table>

F1<sup>∗</sup> is computed at the label-dependent F1-optimal threshold τ<sup>∗</sup> selected on the validation set.

## 4.4. Robustness and Qualitative Analysis

Across five SIM\_tag-grouped folds, all models except LOF achieve 0.91 ≤ PR-AUC ≤ 0.93 with σ < 0.02 (Table 4), indicating stable cross-domain performance. High-error windows concentrate on a subset of identities, supporting identity-level interpretability.

## 4.5. Visual and Quantitative Summary

Table 4 reports the mean PR-AUC (95% confidence intervals) and the fold-aggregated F1-score across the SIM-grouped folds, avoiding the need to include all fold-wise PR curves. The proposed TDAE achieves PR-AUC ≈ 0.93 with narrow confidence intervals, indicating that performance is not driven by a single favorable split. Dense AE and OC-SVM follow closely with slightly lower PR-AUC, whereas Isolation Forest shows larger variability, and LOF yields the weakest and least stable precision–recall performance.

## 4.6. Summary of Findings

• One-class learning on benign SIM-tagged flows generalizes to unseen domain anomalies.

The clean→mixed vs. mixed→clean asymmetry is analyzed in Section 4.2 as a reversetransfer sanity check.

Table 4 shows low variance and narrow confidence intervals across SIM-grouped folds, supporting reproducibility.

The TDAE provides the most stable precision–recall behavior, followed by Dense AE and OC-SVM.

Overall, the results support SIM-level behavioral anomaly monitoring for IoT/telecom traffic under the proposed strict one-class protocol.

## 4.7. Deployment Scenario and Integration in an Operator Security Stack

We position the framework as a scoring component within an operator monitoring pipeline. Telemetry records are collected from network sensors, aggregated per identity (SIM\_tag or subscriber key), and converted into sliding windows using compact descriptors (TTL-proxy and drift signal). The one-class TDAE outputs one reconstruction-error score per window, which is consumed by the security stack as an anomaly indicator. As shown in Figure 7, the reconstruction-error score produced per window serves as the anomaly signal consumed by the scoring layer. This subsection provides a proof-of-concept deployment view: our evaluation uses public IoT traces with synthetic SIM\_tag pseudo-identifiers; production validation requires operator data with real subscriber keys and operational constraints.

Distribution of Reconstruction Error (Autoencoder Output)  
![](images/0956e345ccdc6263692c577e66ec7cae3db03833062de3dabb2390278db59d63.jpg)  
Figure 7. Reconstruction-error distributions for benign and anomalous samples.

Offline vs. near-real-time operation. In offline mode, scores are computed in periodic batches for reporting and forensic triage. In near-real-time mode, scoring runs continuously, and only high-confidence alarms are forwarded to SIEM/SOC workflows. In both modes, the alarm threshold is set with an explicit operator constraint (e.g., FAR budget) and can be recalibrated on recent benign traffic when drift is detected.

Throughput note. The pipeline is streamable: feature extraction and windowing are performed per identity, and inference is a single forward pass per window. This supports micro-batch or continuous scoring depending on telemetry rate and alerting policy. We therefore emphasize compatibility with high-throughput monitoring, rather than claiming telecom-scale validation in this study.

## 4.8. Stress Test Robustness with Partially Contaminated Training Data

To probe robustness limits beyond the strict one-class setting, we added a stress test where the benign-only training assumption is deliberately violated. Specifically, we injected a controlled fraction of anomalous windows into the training set and quantify how performance degrades when training purity cannot be guaranteed (e.g., imperfect filtering or label noise). This stress test complements the main cross-domain results and does not replace the primary protocol.

Let $\gamma \in \{ 0 , 1 \% , 5 \% , 1 0 \% \}$ denote the anomaly injection ratio in training. We retrained the model with the same windowing and hyperparameters as in the main setting while mixing a fraction $\gamma$ of anomalous windows into the training pool. At deployment time, the alarm threshold is calibrated from a benign-only buffer in the target environment for a fixed FAR budget (here $\mathrm { F A R } = 5 \% ,$ consistent with Table 5). We report PR-AUC and $\mathrm { F } 1 ^ { * }$ as diagnostic metrics and $R @ \mathrm { F A R } = 5 \%$ as the deployment-oriented operating-point metric (Table 7).

Table 7. Stress test with partially contaminated training data. $\gamma$ is the anomaly injection ratio in training. Thresholds are calibrated from a benign-only target buffer under $\mathrm { F A R } = 5 \%$

<table><tr><td> $\gamma$ </td><td>PR-AUC</td><td>F1*</td><td>R@FAR = 5%</td><td> $n_{train}$ </td></tr><tr><td>0.00</td><td>0.916</td><td>0.931</td><td>0.945</td><td>120,000</td></tr><tr><td>0.01</td><td>0.729</td><td>0.677</td><td>0.467</td><td>121,212</td></tr><tr><td>0.05</td><td>0.743</td><td>0.699</td><td>0.466</td><td>126,316</td></tr><tr><td>0.10</td><td>0.845</td><td>0.821</td><td>0.676</td><td>133,333</td></tr></table>

F1<sup>∗</sup> is computed at the label-dependent F1-optimal threshold $\overline { { \tau ^ { * } } }$ selected on the validation set.

## Discussion

Even small violations of training purity can reduce recall at a fixed FAR budget. The non-monotonic variations across γ are mainly due to stochastic sampling of injected anomalous windows and training dynamics in one-class reconstruction. We therefore interpret Table 7 as an empirical robustness-boundary analysis (not a monotone trend), while the strict one-class cross-domain results (Tables 4 and 5) remain the primary reference for the intended deployment protocol.

## 4.9. Limitations and Failure Cases

Our evaluation relies on privacy-preserving pseudo-identifiers, where SIM\_tag is synthesized from device\_id. As a result, the most transferable conclusions concern the pipeline (descriptor construction, identity-level aggregation, strict one-class reconstruction), and the cross-domain protocol with controlled injections, rather than true subscriber semantics. In operational networks, a single SIM may legitimately span multiple devices and contexts, which can reduce separability; hence, results on synthetic tags may overestimate performance under higher identity churn conditions. Validation on operator data with real subscriber identifiers remains necessary.

## Relation to real-world SIM cloning/spoofing

Injected anomalies capture data-plane symptoms consistent with practical misuse $( \mathrm { e . g . , }$ hop-count/TTL shifts from relocation/roaming/proxying and timing/payload disruptions from automated bursts). However, they do not emulate control-plane fingerprints of cloning (e.g., IMSI/IMEI binding, radio access procedures, SS7/core-network traces). Blind spots thus include attacks whose evidence lies primarily in operator-only metadata and adaptive adversaries that mimic benign TTL/timing statistics. Routing-policy changes and feature degradation (missing/noisy TTL or payload fields) may also increase false alarms until recalibration. Mitigation: drift monitoring with benign-buffer recalibration and feature diversification (e.g., timing/volume descriptors) can reduce reliance on TTL stability.

## 5. Conclusions and Perspectives

This work shows that unsupervised deep learning can characterize SIM-level behavioral patterns from low-level network descriptors, with emphasis on TTL and timing dynamics. Trained exclusively on benign traffic and evaluated on a heterogeneous corpus enriched with controlled anomaly injections, the proposed Conv–LSTM Temporal Deep Autoencoder achieves the strongest performance among the considered one-class baselines (PR-AUC = 0.93 in Cassavia → Guarascio). These results indicate that models learned from clean distributions can transfer to previously unseen anomalous behaviors without requiring labeled attack data.

A key observation is the directional asymmetry in cross-domain evaluation. In the reverse Guarascio → Cassavia transfer, performance collapses to PR-AUC ≈ 0.5. This behavior is consistent with the two sources capturing distinct distributions, and it makes unintended identity leakage unlikely under the SIM-grouped GroupKFold protocol. Together, these elements support a clear and replicable evaluation setup for SIM-level behavioral anomaly detection under distribution shift conditions.

From an operational perspective, the framework provides a proof-of-concept scoring component that produces a single reconstruction-error score per window. It supports one-class monitoring when labeled attacks are scarce. Deployment-oriented operation is achieved via percentile/quantile-based threshold calibration on benign buffers with explicit false-alarm budgets. Label-dependent thresholds are used only as a diagnostic reference for model comparison.

Future work will prioritize two extensions aligned with the limitations in Section 4.9. First, we will investigate an attention-based temporal variant (temporal self-attention) to better capture non-local dependencies and regime shifts (e.g., routing-policy changes). This is also expected to improve interpretability via time-step attribution. Second, we will explore partial supervision where a small set of analyst-confirmed events is used for threshold calibration and/or a lightweight discriminative head. We will preserve strict one-class training on benign traffic, with the goal of stabilizing operating points under drift conditions and improving robustness to adaptive attackers.

Overall, the study establishes a data-efficient framework for SIM-tagged behavioral anomaly detection without relying on subscriber-identifying metadata. It also makes deployment constraints explicit (operating-point selection, drift monitoring, and adversarial adaptation). These elements guide operator-oriented evaluation on real subscriber identifiers in future work.

Author Contributions: Conceptualization, B.H. and N.R.; methodology, B.H.; software, B.H.; validation, B.H. and N.R.; formal analysis, B.H.; investigation, B.H.; resources, B.H.; data curation, B.H.; writing—original draft preparation, B.H.; writing—review and editing, N.R.; visualization, B.H.; supervision, N.R.; project administration, N.R. All authors have read and agreed to the published version of the manuscript.

Funding: This research received no external funding.

Data Availability Statement: The processed feature dataset (Combined\_SIM\_Minimized, ∼3.6 M flows) is derived from public IoT corpora and enriched with de-identified SIM-tag pseudo-identifiers and controlled injections. Redistribution of the fully enriched corpus is restricted by third-party licenses and our de-identification policy. De-identified feature matrices, model weights, and re producible notebooks will be shared upon reasonable request and deposited in a public repository upon acceptance.

Acknowledgments: The authors thank LaRI (Ibn Tofail University) for administrative support. Experiments were conducted on Google Colab (T4 GPU).

Conflicts of Interest: The authors declare no conflict of interest. The funders had no role in the design of the study; in the collection, analyses, or interpretation of data; in the writing of the manuscript; or in the decision to publish the results.

## Abbreviations

SIM Subscriber Identity Module

IAT Inter-Arrival Time

MSE Mean Squared Error

ROC-AUC Area Under the Receiver Operating Characteristic Curve

PR–AUC Area Under the Precision–Recall Curve

t-SNE t-Distributed Stochastic Neighbor Embedding

## Appendix A. Reproducibility and Sensitivity Analysis

This appendix supports reproducibility and threshold robustness. It reports the key TDAE training settings (Table A1) and documents the threshold protocol: main results use the F1-optimal τ<sup>∗</sup> from the validation PR curve, while robustness is assessed with percentile thresholds τ ∈ {90, 92, 95, 97, 99}% (Figure A1, Table A2).

Table A1. Key hyperparameters for reproducibility.

<table><tr><td>Component</td><td>Setting</td><td>Notes</td></tr><tr><td>Encoder/decoder</td><td>Conv-LSTM TDAE (Conv1D + LSTM encoder, dense bottleneck, mirrored decoder)</td><td>ReLU in hidden layers; linear reconstruction layer</td></tr><tr><td>Regularization</td><td> $L1 = 10^{-5}$ </td><td>Promotes sparsity and stability</td></tr><tr><td>Optimizer</td><td>Adam ( $\eta = 10^{-3}$ )</td><td>Default  $\beta_1 = 0.9$ ,  $\beta_2 = 0.999$ </td></tr><tr><td>Batch size and epochs</td><td>256; 50</td><td>Early stopping on validation loss</td></tr><tr><td>Thresholding</td><td>F1-optimal threshold on validation PR curve</td><td>Percentile thresholds (e.g., 95th) used only for robustness analysis</td></tr><tr><td>Baselines</td><td>IF (cont. 0.05), OC-SVM ( $\nu = 0.05$ , RBF)</td><td>Identical scaling</td></tr></table>

![](images/eb978889402a2fb397dc37563e73103284292a3abe4381b30b64bd4025ec8d40.jpg)  
Figure A1. Sensitivity to the percentile threshold τ: F1 remains stable for $\tau \in [ 9 0 , 9 7 ] \%$ and peaks near the PR-curve F1-optimal $\tau ^ { * } ;$ precision increases while recall decreases as τ grows. Thresholds around 95% approximate the main operating point.

Table A2. Performance variation with respect to the percentile threshold τ (robustness analysis).

<table><tr><td>Threshold (τ)</td><td>Precision</td><td>Recall</td><td>F1-Score</td></tr><tr><td>90%</td><td>0.82</td><td>0.97</td><td>0.89</td></tr><tr><td>92%</td><td>0.85</td><td>0.94</td><td>0.89</td></tr><tr><td>95%</td><td>0.89</td><td>0.92</td><td>0.90</td></tr><tr><td>97%</td><td>0.92</td><td>0.83</td><td>0.87</td></tr><tr><td>99%</td><td>0.96</td><td>0.72</td><td>0.82</td></tr></table>

Percentile thresholds are reported for robustness; all main quantitative results use the F1-optimal threshold $\tau ^ { * }$ selected from the validation precision–recall curve.

The threshold sensitivity analysis shows that the detector remains stable across a wide operating range. For $\tau \in [ 9 0 , 9 2 ] \% ,$ , the F1-score stays around 0.89, with high recall $\left( \geq 0 . 9 4 \right)$ and slightly lower precision. A balanced trade-off is obtained near $\tau = 9 5 \%$ (precision = 0.89, recall = 0.92, F1 = 0.90). More conservative thresholds $( \tau \geq 9 7 \% )$ further increase precision (up to 0.96) but reduce recall (down to 0.72). In the main experiments, $\tau ^ { * }$ is selected to maximize F1 on the validation set; the percentile-based analysis confirms that the conclusions remain stable for small variations around this operating point.

## Appendix B. License and Data Ethics

All third-party corpora were used under their original licenses. The enriched SIM-tag fields were generated exclusively for research purposes and remain fully de-identified in compliance with privacy and operator policy requirements.

## References

1. Cassavia, N.; Caviglione, L.; Guarascio, M.; Liguori, A.; Zuppelli, M. Ensembling Sparse Autoencoders for Network Covert Channel Detection in IoT Ecosystems. In AIxIA 2022—Advances in Artificial Intelligence; Lecture Notes in Computer Science; Springer: Berlin/Heidelberg, Germany, 2022; Volume 13515, pp. 209–218. [CrossRef]

2. Guarascio, M.; Zuppelli, M.; Cassavia, N.; Manco, G.; Caviglione, L. Detection of Network Covert Channels in IoT Ecosystems Using Machine Learning. In Proceedings of the ICDL 2022—CEUR Workshop Proceedings, Örebro, Sweden, 15–17 June 2022; Volume 3260, pp. 102–113. Available online: https://ceur-ws.org/Vol-3260/paper7,pdf (accessed on 23 June 2022)

3. Caviglione, L.; Guarascio, M.; Pisani, F.S.; Zuppelli, M. A Few to Unveil Them All: Leveraging Mixture of Experts on Minimal Data for Detecting Covert Channels in Containerized Cloud Infrastructures. In Proceedings of the 2024 IEEE Eu ropean Symposium on Security and Privacy Workshops (EuroS&PW), Vienna, Austria, 8–12 July 2024; pp. 731–739. Avail able online: https://www.semanticscholar.org/paper/A-Few-to-Unveil-Them-All%3A-Leveraging-Mixture-of-on-Caviglione-Guarascio/dea68588503b2b3762a7abf4262ddbd078f96b43 (accessed on 16 July 2024).

4. Cassavia, N.; Caviglione, L.; Guarascio, M.; Liguori, A.; Zuppelli, M. Learning Autoencoder Ensembles for Detecting Malware Hidden Communications in IoT Ecosystems. J. Intell. Inf. Syst. 2024, 62, 925–949. [CrossRef]

5. Mirsky, Y.; Doitshman, T.; Elovici, Y.; Shabtai, A. Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection. In Proceedings of the Network and Distributed System Security Symposium (NDSS), San Diego, CA, USA, 18–21 February 2018. [CrossRef]

6. Lampson, B.W. A Note on the Confinement Problem. Commun. ACM 1973, 16, 613–615. [CrossRef]

7. Rowland, C.H. Covert Channels in the TCP/IP Protocol Suite. First Monday 1997, 2. [CrossRef]

8. Zander, S.; Armitage, G.; Branch, P. A Survey of Covert Channels and Countermeasures in Computer Network Protocols. IEEE Commun. Surv. Tutor. 2007, 9, 44–57. [CrossRef]

9. Wendzel, S.; Zander, S.; Fechner, B.; Herdin, C. Pattern-Based Survey and Categorization of Network Covert Channel Techniques. ACM Comput. Surv. 2015, 47, 1–26. [CrossRef]

10. Mazurczyk, W.; Caviglione, L. Information Hiding in Network Protocols: Fundamentals, Mechanisms, Applications, and Countermeasures. IEEE Commun. Surv. Tutor. 2016, 18, 1887–1926. Available online: https://www.researchgate.net/publication/ 293452666\_Information\_Hiding\_in\_Communication\_Networks\_Fundamentals\_Mechanisms\_and\_Applications (accessed on 1 March 2016).

11. Crotti, M.; Dusi, M.; Gringoli, F.; Salgarelli, L. Traffic Classification through Simple Statistical Fingerprinting. Acm Sigcomm Comput. Commun. Rev. 2007, 37, 5–16.

12. Rezaei, F.; Hempel, M.; Sharif, H. Towards a Reliable Detection of Covert Timing Channels over Real-Time Network Traffic. IEEE Trans. Dependable Secur. Comput. 2017, 14, 249–264. [CrossRef]

13. Elsadig, M.A.; Gafar, A. Covert Channel Detection: Machine Learning Approaches. Preprint, 2022. Available online: https://www.researchgate.net/publication/359735672 (accessed on 2 April 2022).

14. Zillien, S.; Wendzel, S. Weaknesses of Popular and Recent Covert Channel Detection Methods and a Remedy. IEEE Trans. Dependable Secur. Comput. 2023, 20, 5156–5167. [CrossRef]

15. Mileva, A.; Velinov, A.; Hartmann, L.; Wendzel, S.; Mazurczyk, W. Comprehensive Analysis of MQTT 5.0 Susceptibility to Network Covert Channels. Comput. Secur. 2021, 104, 102207. [CrossRef]

16. Cabaj, K.; Zórawski, P.; Nowakowski, P.; Purski, M.; Mazurczykl, W. Efficient distributed network covert channels for Internet of<sup>˙</sup> things environments. IEEE Commun. Surv. Tutor. 2020, 20, 2785–2813. [CrossRef]

17. Zuppelli, M.; Caviglione, L. pcapStego: A Tool for Generating Traffic Traces for Experimenting with Network Covert Channels. In Proceedings of the 16th International Conference on Availability, Reliability and Security (ARES), Vienna, Austria, 17–20 August 2021; ACM: New York, NY, USA, 2021. [CrossRef]

18. Liguori, A.; Mungari, S.; Zuppelli, M.; Comito, C.; Caviglione, L. Using AI to Face Covert Attacks in IoT and Softwarized Scenarios: Challenges and Opportunities. In Proceedings of the Ital-IA Workshop, CEUR Workshop Proceedings, Pisa, Italy, 29–30 May 2023; Volume 3486, pp. 1–6. Available online: https://ceur-ws.org/Vol-3486/37.pdf (accessed on 1 June 2023).

19. Doshi, R.; Apthorpe, N.; Feamster, N. Machine Learning DDoS Detection for Consumer IoT Devices. In Proceedings of the 2018 IEEE Security and Privacy Workshops (SPW), San Francisco, CA, USA, 24 May 2018; pp. 29–35. [CrossRef]

20. Abusitta, A.; de Carvalho, G.H.S.; Abdel Wahab, O.; Halabi, T.; Fung, B.C.M.; Al Mamoori, S. Deep Learning-Enabled Anomaly Detection for IoT Systems. Internet Things 2022, 20, 100656. [CrossRef]

21. Rathinasamy, V.; Lognathan, D.; Saranya, S.; Sumathi, S. Anomaly Detection in IoT Networks Using Federated Machine Learning Approaches. Int. J. Comput. Exp. Sci. Eng. 2025, 11. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.