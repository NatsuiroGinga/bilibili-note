---
title: "2026-Kim-CANDI-Curated-TTA-arXiv-v1"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2026-Kim-CANDI-Curated-TTA-arXiv-v1.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

(c) Failure of Pre-trained Anomaly Detector under Distribution Shift
Test Data w/ Dist. Shift
Anomaly Scores

![](images/4a51a9f5fd51710485246ac10ac84790e56c8baaa74805acbb331708814cfb28.jpg)

# CANDI: Curated Test-Time Adaptation for Multivariate Time-Series Anomaly Detection Under Distribution Shift

HyunGi Kim $^{1}$ , Jisoo Mok $^{2}$ , Hyungyu Lee $^{1}$ , Juhyeon Shin $^{3}$ , Sungroh Yoon $^{1,3,4\dagger}$

$^{1}$ Department of ECE, Seoul National University $^{2}$ DGIST, $^{3}$ IPAI, Seoul National University, $^{4}$ AIIS, ASRI, and INMC, Seoul National University rlagusrl0128@snu.ac.kr, jmok@dgist.ac.kr, {rucy74, newjh12, sryoon}@snu.ac.kr

## Abstract

Multivariate time-series anomaly detection (MTSAD) aims to identify deviations from normality in multivariate time-series and is critical in real-world applications. However, in real-world deployments, distribution shifts are ubiquitous and cause severe performance degradation in pre-trained anomaly detector. Test-time adaptation (TTA) updates a pre-trained model on-the-fly using only unlabeled test data, making it promising for addressing this challenge. In this study, we propose CANDI (Curated test-time adaptation for multivariate time-series ANomaly detection under DIistribution shift), a novel TTA framework that selectively identifies and adapts to potential false positives while preserving pre-trained knowledge. CANDI introduces a False Positive Mining (FPM) strategy to curate adaptation samples based on anomaly scores and latent similarity, and incorporates a plug-and-play Spatiotemporally-Aware Normality Adaptation (SANA) module for structurally informed model updates. Extensive experiments demonstrate that CANDI significantly improves the performance of MTSAD under distribution shift, improving AUROC up to 14% while using fewer adaptation samples.

Code — https://github.com/kimanki/CANDI

## Introduction

Multivariate time-series anomaly detection (MTSAD) aims to identify abnormal patterns within multivariate time-series data, which contain multiple interdependent variables (Wang et al. 2025; Li and Jung 2023; Choi et al. 2021). This capability is essential for maintaining the stability, safety, and efficiency of complex real-world systems through continuous monitoring of their states and timely decision-making (Duan et al. 2024; Shin et al. 2020). Accurate and robust MTSAD models are thus crucial for ensuring the stable operation of high-stakes, time-sensitive applications, such as industrial maintenance (Tanuska et al. 2021) and healthcare monitoring (Galvão et al. 2024).

Due to the scarcity of labeled anomaly data in real-world scenarios, most MSTAD methods adopt unsupervised approaches (Xu et al. 2022; Song et al. 2023; Kim et al. 2025b). These methods generally assume that the training data consists only of normal operating conditions and learn to model normality. One common approach is reconstruction-based anomaly detection (Wu et al. 2025; Xu et al. 2022; Zhang et al. 2019). Here, the model, typically in the form of an autoencoder, is trained to reconstruct normal time-series data, and at test-time, samples that yield high reconstruction errors are identified as anomalies. Density-based methods estimate the probability density of normal time-series and flag data with low likelihoods as anomalies (Zhou et al. 2023; Dai and Chen 2022). Lastly, distance-based approaches detect anomalies by measuring the distance of test data to normal clusters in a learned embedding space (Shen, Li, and Kwok 2020; Kim et al. 2023).

![](images/4595d2cd6e2e19b61020efdf62e0edd207c666d52f807632717cb4a6fee0a0fe.jpg)

![](images/4461fe53db5ecb8aba243247869a38378c9041720f6d0ada21469e0b4a2afa3f.jpg)

![](images/df93160493b906ad474d4460cc9f54b4be7ad8a09a2afe29d07a776aba24ac6f.jpg)  
Figure 1: [Top] Real-world time-series data often exhibit non-stationarity, leading to continuous distribution shifts between training and test data. [Bottom] As shown in the later part of the anomaly scores, under distribution shift, pretrained anomaly detectors can provide excessive false positives, undermining reliability under deployment.

Despite recent advances, most MTSAD approaches assume that the training and test data belong to the same distribution. However, this assumption is often violated in real-world systems, due to numerous factors that cause a shift in the data distribution, e.g., changes in system dynamics, sensor drifts, or environmental changes (Karimi and Paul 2010). Such distribution shifts induce normality shifts, where previously unseen but normal patterns emerge in the test data (Han et al. 2023). As shown in Figure 1, MTSAD models that have not been adapted to these shifts are prone to misclassifying these new normal patterns as anomalies, leading to a substantial increase in false positives.

Test-time adaptation (TTA) refers to the paradigm of adapting a pre-trained model at inference time using only unlabeled test data (Wang et al. 2020). While TTA has shown success in tasks such as image classification and segmentation (Lee et al. 2024; Gao, Yan, and He 2023), its application to MTSAD remains largely underexplored. In MTSAD, TTA offers a promising avenue towards addressing continuously evolving distribution. A prior work (Kim, Park, and Choo 2024) performs TTA on MTSAD by updating all trainable parameters on test samples that are identified as normal. This approach suffers from two major setbacks. First, it completely disregards false positives, i.e., normal samples that are misclassified as anomalies. These false positives can provide informative learning signal as they correspond to underrepresented normal patterns, revealing regions where the model needs further adaptation. Second, adaptation of all trainable parameters may overwrite useful representations learned during pre-training.

To address the challenges of MTSAD posed by distribution shift, we propose CANDI (Curated test-time adaptation for multivariate time-series ANomaly detection under DIistribution shift), a novel TTA framework for MTSAD that adapts a pre-trained anomaly detector by curating informative test samples while preserving the original knowledge of the detector. CANDI is built on a reconstruction-based anomaly detector and introduces two key components: False Positive Mining (FPM) and Spatiotemporally-Aware Normality Adaptation (SANA). FPM identifies potential false positives based on their anomaly scores and proximity in latent space to normal validation samples. These challenging-to-detect yet reliable samples are used for adaptation.

Instead of updating the entire model, SANA provides a lightweight, plug-and-play adaptation module that captures temporal and inter-variable shifts via temporal convolutions and an attention mechanism, while keeping the backbone frozen. By combining selective adaptation signals with a safe adaptation mechanism, CANDI enhances robustness and accuracy under distribution shift without compromising the pre-trained model. Through extensive experiments, CANDI demonstrates significant gains over baselines under distribution shifts, including a 14% improvement of AUROC compared to the TTA baseline despite using less than 2% of the total test data for adaptation.

In summary, our contributions are as follows:

\- We identify and address the critical challenge of distribution shift in MTSAD, a problem that causes significant false positives in real-world systems.

\- We propose CANDI, a novel TTA framework for MT-SAD that curates informative samples via false positive mining, and adapts the model with a spatiotemporally-aware module while preserving pre-trained knowledge.

\- We demonstrate that CANDI consistently outperforms MTSAD baselines, achieving up to a $14\%$ AUROC gain while using less than $2\%$ of the data for adaptation.

## Related Works

## Unsupervised Multivariate Time-series Anomaly Detection

Unsupervised multivariate time-series anomaly detection (MTSAD) has been studied across diverse paradigms. Traditional methods like LOF (Breunig et al. 2000) and one-class SVM (Manevitz and Yousef 2001) have been applied, but often fail to capture temporal dependencies. Recent deep models fall into reconstruction-, density-, and graph-based categories. Reconstruction-based models detect anomalies based on reconstruction errors (Wu et al. 2025; Xu et al. 2022). USAD (Audibert et al. 2020) extends this approach by introducing adversarial training between dual decoders. Density-based models such as OmniAnomaly (Su et al. 2019a) use variational autoencoders to detect low-likelihood patterns. Structure-aware models focus on inter-variable relations: MSCRED (Zhang et al. 2019) reconstructs multi-scale correlation maps, GDN (Deng and Hooi 2021) applies graph neural networks, and TimesNet (Wu et al. 2022) leverages frequency-aware blocks for improved detection.

However, most unsupervised MTSAD models assume a static normal distribution after training. In reality, normality may drift due to system aging, sensor noise, or environmental changes (Zhu et al. 2023; Liu et al. 2023; Han et al. 2023). Without adaptation, false positives increase over time. Our work addresses this by enabling test-time refinement using unlabeled but selectively informative samples.

## Test-time Adaptation

Test-time adaptation (TTA) (Liang, He, and Tan 2025; Wang et al. 2020; Niu et al. 2023; Jia et al. 2024) is a paradigm that updates a pre-trained model at inference time to address distribution shifts, using only unlabeled test data. In the domain of image classification, TTA methods, such as TENT (Wang et al. 2020) and MEMO (Zhang, Levine, and Finn 2022), adjust model parameters by minimizing prediction entropy or self-supervised losses. More recent frameworks like CoTTA (Wang et al. 2022) further explore the continuous adaptation of a pre-trained image classifier while addressing the risk of catastrophic forgetting.

Due to the ever-evolving, dynamic nature of real-world time-series data, extending TTA to time-series data is a natural yet under-explored direction (Kim et al. 2025a). TTA allows models to track evolving normal distribution and maintain performance under non-stationary conditions. For instance, M2N2 (Kim, Park, and Choo 2024) proposes to adaptively detrend input signals and update model parameters using test samples predicted as normal, demonstrating the potential of TTA in MTSAD.

However, the existing TTA approach for MTSAD considers normality shift narrowly, focusing primarily on changes in overall trends while overlooking more complex temporal and inter-variable distribution shifts. Their reliance on limited adaptation cues and the practice of updating the full model can increase the risk of catastrophic forgetting by overwriting pre-trained knowledge. Furthermore, they overlook the adaptation potential of difficult-to-detect yet informative false positive samples.

![](images/8a92414ea858a3cc6eaabcd6b5ee75c82ab7d9f9bd374891feb70cc7b955b1d4.jpg)  
Figure 2: Overall framework of CANDI. [Left] Anomaly scores are first computed on a normal validation set, and latent representations of samples falling within the top $\alpha$ -percentile (e.g., 5th percentile) are extracted and stored in a reference false positive set $R_{fp}$ . [Right] For arriving test data, if the anomaly score is above the threshold, its latent representation is compared to those in $R_{fp}$ . If the distance is sufficiently small, the sample is identified as a potential false positive and used for adaptation. Adaptation is performed via the plug-and-play Spatiotemporally-Aware Normality Adaptation (SANA) module, which updates only a lightweight residual component while preserving the knowledge and latent space of the pre-trained anomaly detector.

## CANDI: Curated Test-time Adaptation for Multivariate Time-series Anomaly Detection

In this section, we present CANDI, a TTA framework for MTSAD. As illustrated in Figure 2, CANDI selectively adapts a pre-trained anomaly detector to curated informative test samples while preserving the pre-trained knowledge. It is comprised of two components: (1) False Positive Mining that selects potential false positives based on anomaly score distribution and similarity in the latent space, and (2) Spatiotemporally-Aware Normality Adaptation module that handles test-time distribution shifts in temporal and intervariable patterns.

## Problem Formulation

Let $X = [x_{1}, x_{2}, \ldots, x_{T}] \in R^{D \times T}$ denote a multivariate time-series with D variables over T time steps, where $x_{t} \in R^{D}$ is the observation at time t. The goal of MTSAD is to detect time steps or segments that deviate from the normal distribution. The train, validation, and test data are obtained by splitting X into contiguous segments in chronological order. Following the standard assumption in unsupervised MTSAD, the train and validation data consist solely of normal, while the test data include anomalies to be detected.

CANDI adopts a reconstruction-based approach, in which a pre-trained anomaly detector $f_{\theta}$ is an autoencoder trained to reconstruct a sliding input window of length L:

$$
\hat {\pmb {X}} _ {t - L + 1: t} = f _ {\pmb {\theta}} (\pmb {X} _ {t - L + 1: t}).\tag{1}
$$

At inference time, the anomaly score $s_{t}$ is computed as the average squared reconstruction error:

$$
s _ {t} = \frac {1}{D \cdot L} \left\| \pmb {X} _ {t - L + 1: t} - \hat {\pmb {X}} _ {t - L + 1: t} \right\| _ {2} ^ {2},\tag{2}
$$

where higher scores indicate potential anomalies. However, in real-world deployments, the test distribution may shift due to factors like sensor drift or changing system dynamics. Our goal is to adapt the model to such shifts at test-time, without relying on labeled data or retraining the full model.

## False Positive Mining

Rather than adapting to all test samples with low anomaly scores, we selectively identify samples that cannot easily be detected and thus are likely to contribute meaningfully to adaptation. This curated sample selection not only mitigates the risk of performance degradation by avoiding unreliable samples for adaptation, but also improves adaptation efficiency by reducing the number of test samples used. In particular, we focus on samples that are challenging for the model to detect, such as potential false positives that reflect ambiguous or underrepresented normality. In consequence, CANDI focuses on areas where the model's prediction is uncertain, improving robustness with fewer updates.

We first compute anomaly scores for all samples in a validation set that contains only normal data. Let $S_{val} = \{s_{i}^{val}\}_{i=1}^{N_{val}}$ denote the set of anomaly scores computed on this validation set, where $s_{i}^{val}$ is the anomaly score for the i-th validation sample and $N_{val}$ is the total number of samples in the validation set. We then define a threshold $\tau$ as the $\alpha$ -percentile of this score set:

$$
\tau = \text { Percentile } (\mathcal {S} _ {\text { val }}, \alpha).\tag{3}
$$

Following standard practice, test samples with $s_{t} > \tau$ are initially considered to be anomalous. However, since some normal samples in the validation set also exceed the same threshold $\tau$ (i.e., $s_{i}^{val} > \tau$ ), we hypothesize that a subset of high-scoring test samples may likewise be false positives—normal but difficult instances that the model failed to capture during training. To identify these false positives, we collect validation samples with $s_{i}^{val} > \tau$ and extract their latent representations using the frozen pre-trained encoder: $z_{i} = f^{\mathrm{enc}}(X_{i}^{\mathrm{val}})$ . We aggregate these into a reference set of false positive samples, denoted by $R_{fp}$ .

These reference samples reflect normal instances that exhibit unexpectedly high anomaly scores, suggesting that they lie near the decision boundary and share latent features with difficult-to-classify cases. To identify potential test-time false positives, we measure their proximity to known false positives from the validation set in the latent space using Mahalanobis distance. To provide stability, we estimate the mean $\mu$ and covariance matrix $\Sigma$ from the full set of latent representations of validation samples:

$$
\boldsymbol {\mu}, \boldsymbol {\Sigma} = \text { MeanCov } (\mathcal {R} _ {\text { val }}), \quad \mathcal {R} _ {\text { val }} = \{f ^ {\text { enc }} (X _ {i} ^ {\text { val }}) \} _ {i = 1} ^ {N _ {\text { val }}}.\tag{4}
$$

Using the full normal validation set ensures that the latent distance is measured with respect to the overall distribution of normal patterns, providing robustness and avoiding bias from sparsely sampled or ambiguous subsets like $R_{fp}$ .

For each test sample predicted as anomalous $(s_{t} > \tau)$ , we compute its latent representation $z_{t} = f^{\mathrm{enc}}(\mathbf{X}_{t-L+1:t})$ and calculate its minimum squared Mahalanobis distance to the reference set $R_{fp}$ :

$$
\mathcal {D} _ {M} ^ {2} (\boldsymbol {z} _ {t}, \boldsymbol {\mathcal {R}} _ {\mathrm{fp}}) = \min _ {\boldsymbol {z} _ {r} \in \boldsymbol {\mathcal {R}} _ {\mathrm{fp}}} \left(\boldsymbol {z} _ {t} - \boldsymbol {z} _ {r}\right) ^ {\top} \boldsymbol {\Sigma} ^ {- 1} (\boldsymbol {z} _ {t} - \boldsymbol {z} _ {r}).\tag{5}
$$

We consider $X_{t-L+1:t}$ a potential false positive and include it for adaptation if this distance is below the 5th percentile of the chi-squared distribution with latent dimension d. The threshold is defined as:

$$
\delta = F _ {\chi_ {d} ^ {2}} ^ {- 1} (0. 0 5),\tag{6}
$$

where $F_{\chi_{d}^{2}}^{-1}(\cdot)$ denotes the inverse cumulative distribution function. The inclusion criterion becomes:

$$
\mathcal {D} _ {M} ^ {2} (\boldsymbol {z} _ {t}, \boldsymbol {\mathcal {R}} _ {\mathrm{fp}}) <   \delta .\tag{7}
$$

This thresholding strategy is grounded in the statistical property that the squared Mahalanobis distance follows a chi-squared distribution with d degrees of freedom when latent representations of normal samples approximately follow a multivariate Gaussian. Thus, $\delta$ defines a tight neighborhood around the reference set in latent space, and selecting the 5th percentile ensures only test samples with representations sufficiently close to those of high-scoring validation samples are selected. These samples likely share subtle but informative patterns, making them suitable candidates for adaptation. The adaptation set A is constructed as:

$$
\pmb {\mathcal {A}} = \left\{\pmb {X} _ {t - L + 1: t} \mid (s _ {t} > \tau) \wedge \left(\mathcal {D} _ {M} ^ {2} (\pmb {z} _ {t}, \pmb {\mathcal {R}} _ {\mathrm{fp}}) <   \delta\right) \right\}\tag{8}
$$

To further improve robustness, we also incorporate predicted normal samples with moderately high anomaly scores into the adaptation process. Specifically, we identify validation samples whose scores fall within the interquartile range $(Q_{1}-Q_{3})$ and store their latent representations as a separate reference set $R_{mod}$ . These samples are not clearly anomalous but deviate enough from typical patterns to indicate areas where the model's understanding of normality may be incomplete. For each test sample whose anomaly score is smaller than the threshold $\tau$ , we compute its squared Mahalanobis distance to $R_{mod}$ using the same criterion as before. If the distance falls below the threshold $\delta$ , the sample is included in the final adaptation set A.

## Spatiotemporally-Aware Normality Adaptation

To enable stable and efficient TTA while preserving the knowledge of a pre-trained detector, we introduce a lightweight plug-and-play normality adaptation module, as illustrated in Figure 3. Motivated by TAFAS (Kim et al. 2025a), the module is attached to both the input and output of a frozen reconstruction-based anomaly detector. However, unlike TAFAS, which uses independent per-variable simple linear layers, we design a spatiotemporally-aware module composed of temporal convolution and intervariable attention (Liu et al. 2024). This allows our approach to capture distributional shifts occurring not only within each variable but also across variables through their interactions, providing a more expressive adaptation.

![](images/02be4c6c4da59ab4eaeb54293ffe1f6dffc3c2b66e675b7154c09c8ceb1b5df0.jpg)  
Figure 3: Architecture of the Spatiotemporally-Aware Normality Adaptation (SANA) module.

The input-side normality adaptation module adjusts incoming test samples to better align with the training-time normality distribution, enabling the pre-trained detector to process them effectively. Conversely, the output-side normality adaptation module transforms the reconstruction results to match the test-time normal distribution, compensating for any residual shift. This design preserves a consistent latent space, which is crucial for reliable false positive mining, while allowing flexible adaptation.

Input Normality Adaptation. Given a multivariate input window $X_{t-L+1:t} \in R^{D \times L}$ , we first model the temporal dynamics of each variable independently. For the i-th variable, the univariate sequence $\boldsymbol{X}_{t-L+1:t}^{(i)} \in \mathbb{R}^{L}$ is encoded via a 1D convolution layer:

$$
\boldsymbol {h} _ {t} ^ {(i)} = \mathrm{Conv} ^ {\mathrm{in}} (\boldsymbol {X} _ {t - L + 1: t} ^ {(i)}).\tag{9}
$$

The resulting temporal embeddings $\{\boldsymbol{h}_{t}^{(i)}\}_{i=1}^{D}$ are then processed by a single inter-variable attention layer to capture cross-variable dependencies:

$$
\{\pmb {h} _ {t} ^ {\prime (i)} \} _ {i = 1} ^ {D} = \mathrm{ATTN} ^ {\mathrm{in}} (\{\pmb {h} _ {t} ^ {(i)} \} _ {i = 1} ^ {D}).\tag{10}
$$

We apply a variable-wise linear layer to the attention output to compute the adjustment term $\mathbf{A}_t^{(i)} \in \mathbb{R}^L$ for each variable:

$$
\pmb {A} _ {t} ^ {(i)} = \mathrm{Linear} ^ {\mathrm{in}} (\pmb {h} _ {t} ^ {\prime (i)}).\tag{11}
$$

Finally, a learnable gating parameter $g^{(i)}$ , activated by a tanh function, is used to modulate the adjustment applied to each variable:

$$
\tilde {\boldsymbol {X}} _ {t - L + 1: t} ^ {(i)} = \boldsymbol {X} _ {t - L + 1: t} ^ {(i)} + \tanh (g ^ {(i)}) \cdot \boldsymbol {A} _ {t} ^ {(i)}.\tag{12}
$$

The adapted input $\tilde{X}_{t-L+1:t}$ is then passed to the frozen pre-trained anomaly detector $f_{\theta}$ to obtain the reconstruction:

$$
\hat {\boldsymbol {X}} _ {t - L + 1: t} = f _ {\theta} (\tilde {\boldsymbol {X}} _ {t - L + 1: t}).\tag{13}
$$

Output Normality Adaptation. To account for distributional shifts in the reconstructed space, we apply an output normality adaptation module with the same architectural structure. Each variable-wise reconstructed sequence $\hat{\mathbf{X}}_{t-L+1:t}^{(i)} \in \mathbb{R}^{L}$ is encoded using a 1D convolution layer:

$$
\boldsymbol {h} _ {t} ^ {(i, \mathrm{out})} = \mathrm{Conv} ^ {\mathrm{out}} (\hat {\boldsymbol {X}} _ {t - L + 1: t} ^ {(i)}).\tag{14}
$$

<table><tr><td rowspan="2">Dataset</td><td rowspan="2">Metric</td><td colspan="3">α = 0.5%</td><td colspan="3">α = 1.0%</td><td colspan="3">α = 5.0%</td></tr><tr><td>Pretrained</td><td>M2N2</td><td>CANDI</td><td>Pretrained</td><td>M2N2</td><td>CANDI</td><td>Pretrained</td><td>M2N2</td><td>CANDI</td></tr><tr><td rowspan="3">SWaT</td><td>AUROC</td><td>0.827</td><td>0.891</td><td>0.889</td><td>0.827</td><td>0.891</td><td>0.890</td><td>0.827</td><td>0.891</td><td>0.888</td></tr><tr><td>AUPRC</td><td>0.719</td><td>0.771</td><td>0.779</td><td>0.719</td><td>0.771</td><td>0.780</td><td>0.719</td><td>0.772</td><td>0.781</td></tr><tr><td>F1</td><td>0.291</td><td>0.711</td><td>0.752</td><td>0.287</td><td>0.700</td><td>0.738</td><td>0.291</td><td>0.636</td><td>0.624</td></tr><tr><td rowspan="3">SMD_1-7</td><td>AUROC</td><td>0.883</td><td>0.901</td><td>0.922</td><td>0.883</td><td>0.864</td><td>0.923</td><td>0.883</td><td>0.886</td><td>0.922</td></tr><tr><td>AUPRC</td><td>0.703</td><td>0.728</td><td>0.736</td><td>0.703</td><td>0.734</td><td>0.737</td><td>0.703</td><td>0.718</td><td>0.737</td></tr><tr><td>F1</td><td>0.103</td><td>0.662</td><td>0.107</td><td>0.562</td><td>0.707</td><td>0.688</td><td>0.724</td><td>0.723</td><td>0.725</td></tr><tr><td rowspan="3">SMD_1-8</td><td>AUROC</td><td>0.719</td><td>0.837</td><td>0.872</td><td>0.719</td><td>0.805</td><td>0.872</td><td>0.719</td><td>0.772</td><td>0.867</td></tr><tr><td>AUPRC</td><td>0.332</td><td>0.407</td><td>0.432</td><td>0.332</td><td>0.376</td><td>0.434</td><td>0.332</td><td>0.354</td><td>0.423</td></tr><tr><td>F1</td><td>0.377</td><td>0.406</td><td>0.393</td><td>0.362</td><td>0.389</td><td>0.409</td><td>0.092</td><td>0.115</td><td>0.213</td></tr><tr><td rowspan="3">SMD_2-1</td><td>AUROC</td><td>0.648</td><td>0.698</td><td>0.725</td><td>0.648</td><td>0.693</td><td>0.711</td><td>0.648</td><td>0.683</td><td>0.780</td></tr><tr><td>AUPRC</td><td>0.275</td><td>0.307</td><td>0.319</td><td>0.275</td><td>0.302</td><td>0.314</td><td>0.275</td><td>0.296</td><td>0.348</td></tr><tr><td>F1</td><td>0.265</td><td>0.266</td><td>0.266</td><td>0.296</td><td>0.295</td><td>0.292</td><td>0.273</td><td>0.309</td><td>0.327</td></tr><tr><td rowspan="3">SMD_2-4</td><td>AUROC</td><td>0.821</td><td>0.895</td><td>0.908</td><td>0.821</td><td>0.895</td><td>0.908</td><td>0.821</td><td>0.828</td><td>0.899</td></tr><tr><td>AUPRC</td><td>0.457</td><td>0.605</td><td>0.608</td><td>0.457</td><td>0.605</td><td>0.608</td><td>0.457</td><td>0.461</td><td>0.600</td></tr><tr><td>F1</td><td>0.357</td><td>0.355</td><td>0.352</td><td>0.378</td><td>0.377</td><td>0.372</td><td>0.316</td><td>0.311</td><td>0.512</td></tr><tr><td rowspan="3">SMD_3-2</td><td>AUROC</td><td>0.451</td><td>0.573</td><td>0.717</td><td>0.451</td><td>0.632</td><td>0.717</td><td>0.451</td><td>0.640</td><td>0.717</td></tr><tr><td>AUPRC</td><td>0.159</td><td>0.174</td><td>0.199</td><td>0.159</td><td>0.179</td><td>0.199</td><td>0.159</td><td>0.188</td><td>0.199</td></tr><tr><td>F1</td><td>0.017</td><td>0.017</td><td>0.017</td><td>0.031</td><td>0.030</td><td>0.030</td><td>0.247</td><td>0.194</td><td>0.262</td></tr></table>

Table 1: Performance of test-time adaptation methods for multivariate time-series anomaly detection under test-time distribution shift. Bold denotes the best result for each metric and threshold level. Each threshold is determined by the $\alpha$ -percentile of validation anomaly scores.

The resulting temporal embeddings $\{\boldsymbol{h}_{t}^{(i,\mathrm{out})}\}_{i=1}^{D}$ are passed through an inter-variable attention layer:

$$
\{\pmb {h} _ {t} ^ {\prime (i, \mathrm{out})} \} _ {i = 1} ^ {D} = \mathrm{ATTN} ^ {\mathrm{out}} (\{\pmb {h} _ {t} ^ {(i, \mathrm{out})} \} _ {i = 1} ^ {D}).\tag{15}
$$

Each attention output is then passed through a variable-wise linear layer to obtain the adjustment term:

$$
\pmb {A} _ {t} ^ {(i, \mathrm{out})} = \mathrm{Linear} ^ {\mathrm{out}} (\pmb {h} _ {t} ^ {\prime (i, \mathrm{out})}).\tag{16}
$$

Finally, a learnable gating parameter $g^{(i,\text{out})}$ modulates the adjustment via a tanh activation:

$$
\tilde {\hat {\boldsymbol {X}}} _ {t - L + 1: t} ^ {(i)} = \hat {\boldsymbol {X}} _ {t - L + 1: t} ^ {(i)} + \tanh (g ^ {(i, \mathrm{out})}) \cdot \boldsymbol {A} _ {t} ^ {(i, \mathrm{out})}.\tag{17}
$$

Adaptation Objective. Only the parameters of the SANA modules are updated during test-time, while the pre-trained backbone parameters $\theta$ remain frozen. We minimize the reconstruction loss over the selected adaptation set A:

$$
\mathcal {L} _ {\text { adapt }} = \frac {1}{D \cdot L} \sum_ {\boldsymbol {X} _ {t} \in \boldsymbol {\mathcal {A}}} \left\| \boldsymbol {X} _ {t - L + 1: t} - \tilde {\hat {\boldsymbol {X}}} _ {t - L + 1: t} \right\| _ {2} ^ {2}.\tag{18}
$$

This modular design enables the model to adapt to both temporal and relational distributional shifts at test-time, while preserving the generalization capabilities of the frozen backbone. By updating only lightweight modules with selectively chosen, informative test samples, our framework achieves robust and efficient test-time adaptation for anomaly detection.

## Experiments

## Experimental Setup

Datasets. We conduct experiments on representative multivariate time-series anomaly detection benchmarks:

SWaT (Goh et al. 2016) and SMD (Su et al. 2019a). SWaT is industrial control system datasets containing labeled normal and attack periods, reflecting real-world operational and environmental shifts. SMD is a dataset collected from server machines, organized into multiple subdatasets based on the entity. Since distribution shifts are not uniformly present across all SMD subsets, we select a representative subset of 5 server entities that exhibit prominent normality shifts: SMD\_1-7, SMD\_1-8, SMD\_2-1, SMD\_2-4 and SMD\_3-2. We also evaluate CANDI on the 200 multivariate time-series datasets provided by the TSB-AD benchmark (Liu and Paparrizos 2024) to further assess robustness under a broader and more diverse collection of real-world conditions.

Baselines. To assess the benefits of test-time adaptation, we compare our method to M2N2 (Kim, Park, and Choo 2024), a recent approach that applies TTA to time-series anomaly detection. Following the original setup in M2N2, we use an MLP-based autoencoder as the pre-trained anomaly detector for both methods. For each dataset, we report the performance of: (1) the pre-trained model without adaptation, (2) the model adapted with M2N2, and (3) the model adapted with our proposed CANDI framework. This comparison allows us to isolate the effects of different adaptation strategies under the same model backbone.

Implementation Details. We evaluate detection performance using the standard metrics: AUROC and AUPRC. In addition, we report F1 scores at fixed false positive rate (FPR) thresholds determined by the $\alpha$ -percentile of validation anomaly scores. Specifically, we report results for $\alpha \in \{0.5\%, 1\%, 5\%$ . The pre-trained models are trained using the Adam optimizer (Kingma and Ba 2015) with an initial learning rate of 0.001 and cosine learning rate scheduling (Loshchilov and Hutter 2017) for 30 epochs. M2N2 is re-implemented to match our experimental setup for fair comparison. All experiments are conducted using three different random seeds, and we report the average performance. Full results, including standard deviations and additional implementation details, are included in the Appendix.

<table><tr><td rowspan="2">FPM</td><td rowspan="2">SANA</td><td colspan="3">SWaT</td><td colspan="3">SMD_1-8</td><td colspan="3">SMD_2-1</td><td colspan="3">SMD_2-4</td><td colspan="3">SMD_3-2</td></tr><tr><td>ROC</td><td>PRC</td><td>F1</td><td>ROC</td><td>PRC</td><td>F1</td><td>ROC</td><td>PRC</td><td>F1</td><td>ROC</td><td>PRC</td><td>F1</td><td>ROC</td><td>PRC</td><td>F1</td></tr><tr><td colspan="2">w/o TTA</td><td>0.83</td><td>0.72</td><td>0.29</td><td>0.72</td><td>0.33</td><td>0.10</td><td>0.65</td><td>0.28</td><td>0.27</td><td>0.82</td><td>0.46</td><td>0.32</td><td>0.45</td><td>0.16</td><td>0.25</td></tr><tr><td>X</td><td>X</td><td>0.89</td><td>0.77</td><td>0.64</td><td>0.77</td><td>0.35</td><td>0.12</td><td>0.68</td><td>0.30</td><td>0.31</td><td>0.83</td><td>0.46</td><td>0.31</td><td>0.64</td><td>0.19</td><td>0.19</td></tr><tr><td>√</td><td>X</td><td>0.80</td><td>0.71</td><td>0.22</td><td>0.69</td><td>0.32</td><td>0.01</td><td>0.71</td><td>0.34</td><td>0.20</td><td>0.93</td><td>0.66</td><td>0.25</td><td>0.74</td><td>0.22</td><td>0.21</td></tr><tr><td>X</td><td>√</td><td>0.89</td><td>0.78</td><td>0.64</td><td>0.83</td><td>0.36</td><td>0.15</td><td>0.71</td><td>0.32</td><td>0.33</td><td>0.83</td><td>0.46</td><td>0.37</td><td>0.68</td><td>0.19</td><td>0.25</td></tr><tr><td>√</td><td>√</td><td>0.89</td><td>0.78</td><td>0.62</td><td>0.87</td><td>0.42</td><td>0.21</td><td>0.78</td><td>0.35</td><td>0.33</td><td>0.90</td><td>0.60</td><td>0.51</td><td>0.72</td><td>0.20</td><td>0.26</td></tr></table>

Table 2: Ablation study of CANDI across five datasets at $\alpha = 5.0\%$ . FPM and SANA denote False Positive Mining and Spatiotemporally-Aware Normality Adaptation, respectively. ROC and PRC denote AUROC and AUPRC, respectively.

## Evaluating Test-time Adaptation in Multivariate Time-series Anomaly Detection

Table 1 compares the performance of the pre-trained anomaly detector, M2N2, and CANDI under test-time distribution shift on multiple multivariate time-series anomaly detection benchmarks. We report AUROC, AUPRC, and F1 scores across three anomaly score thresholds, $\alpha \in \{0.5\%, 1.0\%, 5.0\%\}$ , with $\tau$ set as the $\alpha$ -percentile of validation scores. Smaller $\alpha$ yields stricter thresholds with fewer false positives, while larger $\alpha$ reflects more relaxed thresholds, admitting more ambiguous cases.

CANDI consistently matches or outperforms both baselines, with the largest gains seen where the pre-trained model struggles. For instance, on SMD\_1-8, CANDI improves AUROC from 0.719 (pre-trained) and 0.772 (M2N2) to 0.867 at $\alpha = 5.0\%$ . Similarly, on SMD\_3-2, AUROC rises from 0.451 to 0.717—a $59.0\%$ relative improvement—showing CANDI's strength in challenging conditions.

Notably, at $\alpha = 5.0\%$ , where many false positives emerge due to a lower threshold, CANDI turns this challenge into an advantage. The false positive mining selects informative samples close to trusted normal patterns in latent space and adapts using the lightweight SANA module. As a result, CANDI achieves substantial gains; for example, on SMD\_2-4, F1 improves from 0.316 (pre-trained) and 0.311 (M2N2) to 0.512, with AUPRC increasing to 0.600. We provide further evaluation results on the large-scale TSB-AD benchmark (Liu and Paparrizos 2024) in the Appendix.

## Ablation Study

Table 2 presents an ablation study evaluating the contributions of the two core components of CANDI: False Positive Mining (FPM) and Spatiotemporally-Aware Normality Adaptation (SANA), across five datasets at $\alpha = 5.0\%$ . When FPM is disabled, the model performs adaptation using all test samples whose anomaly scores fall below the threshold. When SANA is disabled, entire parameters of the pre-trained anomaly detector are updated during adaptation. When both FPM and SANA are disabled, the model corresponds to M2N2, which adapts the entire pre-trained anomaly detector using all test samples whose anomaly scores fall below the threshold. This setting serves as a baseline for assessing the effectiveness of each component.

When FPM is used without SANA, we observe performance degradation across several datasets. For example, on SWaT, F1 drops from 0.64 (M2N2) to 0.22, and on SMD\_2-1, from 0.31 to 0.20. This suggests that although FPM improves the adaptation sample quality by mining informative candidates, the adaptation process without the structural constraint of SANA updates distorts the pre-trained latent space, undermining the reliability of FPM's latent similarity calculations. These results underscore the necessity of freezing the pre-trained model and adapting only the SANA module to preserve latent consistency.

In contrast, using only SANA without FPM leads to consistent gains over M2N2. For instance, on SMD\_2-4, F1 improves from 0.31 to 0.37, and on SMD\_1-8, from 0.12 to 0.15. This shows that even without selective sample mining, restricting updates to a lightweight, structurally-informed module like SANA prevents catastrophic forgetting and enables stable test-time adaptation. However, this configuration does not leverage the informative signals present in potential false positives, which limits its ability to fully recover useful patterns missed during training.

The proposed CANDI framework, with both FPM and SANA enabled, achieves the best performance across the majority of datasets despite using fewer adaptation samples than M2N2. These results demonstrate that combining sample selection through FPM with the localized and structured updates enabled by SANA provides a robust and efficient adaptation strategy. By leveraging latent-consistent false positives while preserving the integrity of the pretrained detector, CANDI achieves both superior accuracy and stable performance under distribution shift.

Analysis on ROC and PR Curves. Figure 4 shows the Receiver Operating Characteristic (ROC) and Precision-Recall (PR) curves to further compare the detection capabilities. ROC curves show that CANDI consistently achieves a significantly higher true positive rate (TPR) at low false positive rates (e.g., FPR = 0.1) compared to all baselines. This indicates that CANDI is more effective at identifying true anomalies while keeping false alarms low—a critical property in real-world deployment scenarios.

We also evaluate CANDI Hard, a variant that uses only the hard samples identified through false positive mining, excluding moderate samples. Despite using fewer adaptation samples, this variant still outperforms the baselines and achieves performance close to the original CANDI. These results highlight that even partial adaptation guided by carefully curated samples can offer substantial benefits, and that the CANDI framework further enhances performance by incorporating additional reliable test-time samples.

<table><tr><td>Dataset</td><td>Method</td><td>Mod. Samples</td><td>Ano. in Mod.</td><td>Hard Samples</td><td>Ano. in Hard</td><td>Total Adapt</td><td>Total Test</td><td>Total Ano.</td><td>ROC</td><td>PRC</td><td>F1</td></tr><tr><td rowspan="4">SMD_1-8</td><td>M2N2</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>11,760</td><td rowspan="4">23,690</td><td rowspan="4">943</td><td>0.772</td><td>0.354</td><td>0.115</td></tr><tr><td>CANDI Hard</td><td>N/A</td><td>N/A</td><td>5,437</td><td>527</td><td>5,437</td><td>0.861</td><td>0.416</td><td>0.166</td></tr><tr><td>CANDI Mod.</td><td>11,038</td><td>114</td><td>N/A</td><td>N/A</td><td>11,038</td><td>0.826</td><td>0.362</td><td>0.142</td></tr><tr><td>CANDI (Hard + Mod.)</td><td>14,924</td><td>178</td><td>4,332</td><td>497</td><td>19,256</td><td>0.867</td><td>0.423</td><td>0.213</td></tr><tr><td rowspan="4">SMD_2-1</td><td>M2N2</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>22,573</td><td rowspan="4">23,685</td><td rowspan="4">1,287</td><td>0.683</td><td>0.296</td><td>0.309</td></tr><tr><td>CANDI Hard</td><td>N/A</td><td>N/A</td><td>353</td><td>78</td><td>353</td><td>0.735</td><td>0.323</td><td>0.262</td></tr><tr><td>CANDI Mod.</td><td>13,940</td><td>184</td><td>N/A</td><td>N/A</td><td>13,940</td><td>0.717</td><td>0.317</td><td>0.328</td></tr><tr><td>CANDI (Hard + Mod.)</td><td>10,948</td><td>107</td><td>310</td><td>76</td><td>11,258</td><td>0.780</td><td>0.348</td><td>0.327</td></tr></table>

Table 3: Comparison of different adaptation sample configurations on SMD\_1-8 and SMD\_2-1. “Mod.” and “Hard” refer to the difficulty levels of the samples used. “Ano.” refers to anomaly. “Total Adapt” denotes the number of adaptation samples.

![](images/de78f777ec6cd991a4aac53cdc4d6d60ae5a389e2d599fb0b32eeb51b0a0e55f.jpg)

![](images/ea646e1b8443d603b27787e99192178b140998bbe44b4fb31d51d9663bfebc87.jpg)

![](images/d32035ea66a717d76b9ce75599dda21967b0bf8e45d576739ab1d148f63caf65.jpg)

![](images/60e64eb8865642dd503bf95f868f5032e9cf5ddaf2dc4721e1c44a5adecba28c.jpg)  
Figure 4: Receiver Operating Characteristic (ROC) and Precision-Recall (PR) curves for anomaly detection. The value in parentheses indicates the area under each curve.

Comparison of Adaptation Sample Configurations. Table 3 compares the effectiveness of different adaptation sample configurations, including the proposed CANDI variants and M2N2. Notably, CANDI with only hard samples outperforms M2N2 while using significantly fewer adaptation samples—less than half on SMD\_1-8 (5,437 vs. 11,760) and less than 2% on SMD\_2-1 (353 vs. 22,573). Despite this drastic reduction, it achieves superior AUROC and AUPRC, highlighting the efficiency of our curated adaptation.

Among the samples identified as potential false positives for adaptation, some fraction are actual anomalies: approximately 10% on SMD\_1-8 and 25% on SMD\_2-1. This indicates that CANDI sometimes performs adaptation on mislabeled anomalous data. Nevertheless, it still outperforms the baseline, suggesting robustness to moderate contamination. These results highlight that enhancing the accuracy of false positive mining, thereby reducing the potential negative impact of anomaly adaptation, is an important future direction for TTA frameworks in MTSAD.

<table><tr><td rowspan="2">Method</td><td colspan="3">SMD_1-8</td><td colspan="3">SMD_2-1</td></tr><tr><td>ROC</td><td>PRC</td><td>F1</td><td>ROC</td><td>PRC</td><td>F1</td></tr><tr><td>Linear</td><td>0.840</td><td>0.415</td><td>0.115</td><td>0.673</td><td>0.294</td><td>0.275</td></tr><tr><td>SANA</td><td>0.867</td><td>0.423</td><td>0.213</td><td>0.780</td><td>0.348</td><td>0.327</td></tr></table>

Table 4: Comparison between Linear and SANA adaptation modules on SMD\_1-8 and SMD\_2-1. ROC and PRC denote AUROC and AUPRC, respectively.

Among all configurations, the best performance is achieved when both moderate and hard samples are used together. The results demonstrate that combining reliable moderate samples with carefully mined hard samples enables more comprehensive and effective test-time adaptation under distribution shift.

Effectiveness of SANA Architecture. Table 4 compares the proposed SANA module with a linear adaptation head on SMD\_1-8 and SMD\_2-1. Across all metrics, SANA outperforms the linear approach—achieving notably higher F1 scores (0.213 vs. 0.115 on SMD\_1-8 and 0.327 vs. 0.275 on SMD\_2-1). This indicates that SANA provides more effective test-time adaptation. The performance gap highlights the importance of structure-aware adaptation. Unlike linear updates, SANA captures temporal and variable-wise dependencies while preserving the pre-trained model's latent space. This allows SANA to adapt meaningfully under distribution shifts without degrading the original detector.

## Conclusion

Multivariate time-series anomaly detection in deployment environments suffers from performance degradation due to distribution shift. To address this, we proposed CANDI, a test-time adaptation framework that curates informative false positives and adapts using a lightweight, structure-aware module. CANDI combines False Positive Mining (FPM) to identify reliable adaptation samples with Spatiotemporally-Aware Normality Adaptation (SANA), a plug-and-play module that preserves pre-trained knowledge. Experiments show that CANDI significantly outperforms prior methods, especially under relaxed anomaly thresholds.

## Acknowledgments

This work was supported by Institute of Information & communications Technology Planning & Evaluation (IITP) grant funded by the Korea government (MSIT) [No.RS-2021-II211343, Artificial Intelligence Graduate School Program (Seoul National University); No.RS-2024-00357879, AI-based Biosignal Fusion and Generation Technology for Intelligent Personalized Chronic Disease Management], the National Research Foundation of Korea (NRF) grant funded by the Korea government (MSIT) (No. 2022R1A3B1077720; 2022R1A5A708390811; No.RS-2023-00212484, xAI for Motion Prediction in Complex, Real-World Driving Environment), the BK21 FOUR program of the Education and the Research Program for Future ICT Pioneers, Seoul National University in 2025, Hyundai Motor Company, and Samsung Electronics Co., Ltd (IO250624-13143-01).

## References

Audibert, J.; Michiardi, P.; Guyard, F.; Marti, S.; and Zuluaga, M. A. 2020. Usad: Unsupervised anomaly detection on multivariate time series. In Proceedings of the 26th ACM SIGKDD international conference on knowledge discovery & data mining, 3395–3404.

Breunig, M. M.; Kriegel, H.-P.; Ng, R. T.; and Sander, J. 2000. LOF: identifying density-based local outliers. In Proceedings of the 2000 ACM SIGMOD international conference on Management of data, 93–104.

Choi, K.; Yi, J.; Park, C.; and Yoon, S. 2021. Deep learning for anomaly detection in time-series data: Review, analysis, and guidelines. IEEE access, 9: 120043–120065.

Dai, E.; and Chen, J. 2022. Graph-Augmented Normalizing Flows for Anomaly Detection of Multiple Time Series. In International Conference on Learning Representations.

Deng, A.; and Hooi, B. 2021. Graph neural network-based anomaly detection in multivariate time series. In Proceedings of the AAAI conference on artificial intelligence, volume 35, 4027–4035.

Duan, Y.; Xue, K.; Sun, H.; Bao, H.; Wei, Y.; You, Z.; Zhang, Y.; Jiang, X.; Yang, S.; Chen, J.; Duan, B.; and Ou, Z. 2024. LogEDL: Log Anomaly Detection via Evidential Deep Learning. Applied Sciences, 14(16).

Galvão, Y. M.; Castro, L.; Ferreira, J.; Neto, F. B. d. L.; Fagundes, R. A. d. A.; and Fernandes, B. J. 2024. Anomaly detection in smart houses for healthcare: Recent advances, and future perspectives. SN Computer Science, 5(1): 136.

Gao, Z.; Yan, S.; and He, X. 2023. ATTA: Anomaly-aware Test-Time Adaptation for Out-of-Distribution Detection in Segmentation. In Thirty-seventh Conference on Neural Information Processing Systems.

Goh, J.; Adepu, S.; Junejo, K. N.; and Mathur, A. 2016. A dataset to support research in the design of secure water treatment systems. In International conference on critical information infrastructures security, 88–99. Springer.

Han, D.; Wang, Z.; Chen, W.; Wang, K.; Yu, R.; Wang, S.; Zhang, H.; Wang, Z.; Jin, M.; Yang, J.; et al. 2023. Anomaly

Detection in the Open World: Normality Shift Detection, Explanation, and Adaptation. In NDSS.

Jia, H.; Kwon, Y.; Orsino, A.; Dang, T.; Talia, D.; and Mascolo, C. 2024. TinyTTA: Efficient Test-time Adaptation via Early-exit Ensembles on Edge Devices. Advances in Neural Information Processing Systems, 37: 43274–43299.

Karimi, A.; and Paul, M. R. 2010. Extensive chaos in the Lorenz-96 model. Chaos: An interdisciplinary journal of nonlinear science, 20(4).

Kim, D.; Park, S.; and Choo, J. 2024. When model meets new normals: Test-time adaptation for unsupervised time-series anomaly detection. In Proceedings of the AAAI conference on artificial intelligence, volume 38, 13113–13121.

Kim, H.; Kim, S.; Min, S.; and Lee, B. 2023. Contrastive Time-Series Anomaly Detection. IEEE Transactions on Knowledge and Data Engineering.

Kim, H.; Kim, S.; Mok, J.; and Yoon, S. 2025a. Battling the non-stationarity in time series forecasting via test-time adaptation. In Proceedings of the AAAI Conference on Artificial Intelligence, volume 39, 17868–17876.

Kim, H.; Mok, J.; Lee, D.; Lew, J.; Kim, S.; and Yoon, S. 2025b. Causality-Aware Contrastive Learning for Robust Multivariate Time-Series Anomaly Detection. In Forty-second International Conference on Machine Learning.

Kingma, D. P.; and Ba, J. 2015. Adam: A Method for Stochastic Optimization. In Bengio, Y.; and LeCun, Y., eds., 3rd International Conference on Learning Representations, ICLR 2015, San Diego, CA, USA, May 7-9, 2015, Conference Track Proceedings.

Lee, J.; Jung, D.; Lee, S.; Park, J.; Shin, J.; Hwang, U.; and Yoon, S. 2024. Entropy is not Enough for Test-Time Adaptation: From the Perspective of Disentangled Factors. In The Twelfth International Conference on Learning Representations.

Li, G.; and Jung, J. J. 2023. Deep learning for anomaly detection in multivariate time series: Approaches, applications, and challenges. Information Fusion, 91: 93–102.

Liang, J.; He, R.; and Tan, T. 2025. A comprehensive survey on test-time adaptation under distribution shifts. International Journal of Computer Vision, 133(1): 31–64.

Liu, J.; Yang, D.; Zhang, K.; Gao, H.; and Li, J. 2023. Anomaly and change point detection for time series with concept drift. World Wide Web, 26(5): 3229–3252.

Liu, Q.; and Paparrizos, J. 2024. The elephant in the room: Towards a reliable time-series anomaly detection benchmark. Advances in Neural Information Processing Systems, 37: 108231–108261.

Liu, Y.; Hu, T.; Zhang, H.; Wu, H.; Wang, S.; Ma, L.; and Long, M. 2024. iTransformer: Inverted Transformers Are Effective for Time Series Forecasting. In The Twelfth International Conference on Learning Representations.

Loshchilov, I.; and Hutter, F. 2017. SGDR: Stochastic Gradient Descent with Warm Restarts. In 5th International Conference on Learning Representations, ICLR 2017, Toulon, France, April 24-26, 2017, Conference Track Proceedings. OpenReview.net.

Manevitz, L. M.; and Yousef, M. 2001. One-class SVMs for document classification. Journal of machine Learning research, 2(Dec): 139–154.

Müller, M.; and Hein, M. 2025. Mahalanobis++: Improving OOD Detection via Feature Normalization. In Singh, A.; Fazel, M.; Hsu, D.; Lacoste-Julien, S.; Berkenkamp, F.; Maharaj, T.; Wagstaff, K.; and Zhu, J., eds., Proceedings of the 42nd International Conference on Machine Learning, volume 267 of Proceedings of Machine Learning Research, 45151–45184. PMLR.

Niu, S.; Wu, J.; Zhang, Y.; Wen, Z.; Chen, Y.; Zhao, P.; and Tan, M. 2023. Towards Stable Test-time Adaptation in Dynamic Wild World. In The Eleventh International Conference on Learning Representations.

Paparrizos, J.; Boniol, P.; Palpanas, T.; Tsay, R. S.; Elmore, A.; and Franklin, M. J. 2022. Volume under the surface: a new accuracy evaluation measure for time-series anomaly detection. Proceedings of the VLDB Endowment, 15(11):2774–2787.

Shen, L.; Li, Z.; and Kwok, J. 2020. Timeseries Anomaly Detection using Temporal Hierarchical One-Class Network. In Larochelle, H.; Ranzato, M.; Hadsell, R.; Balcan, M.; and Lin, H., eds., Advances in Neural Information Processing Systems, volume 33, 13016–13026. Curran Associates, Inc.

Shin, Y.; Lee, S.; Tariq, S.; Lee, M. S.; Jung, O.; Chung, D.; and Woo, S. S. 2020. Itad: integrative tensor-based anomaly detection system for reducing false positives of satellite systems. In Proceedings of the 29th ACM international conference on information & knowledge management, 2733–2740.

Song, J.; Kim, K.; Oh, J.; and Cho, S. 2023. MEMTO: Memory-guided Transformer for Multivariate Time Series Anomaly Detection. In Oh, A.; Naumann, T.; Globerson, A.; Saenko, K.; Hardt, M.; and Levine, S., eds., Advances in Neural Information Processing Systems, volume 36, 57947–57963. Curran Associates, Inc.

Su, Y.; Zhao, Y.; Niu, C.; Liu, R.; Sun, W.; and Pei, D. 2019a. Robust anomaly detection for multivariate time series through stochastic recurrent neural network. In Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, 2828–2837.

Su, Y.; Zhao, Y.; Niu, C.; Liu, R.; Sun, W.; and Pei, D. 2019b. Robust anomaly detection for multivariate time series through stochastic recurrent neural network. In Proceedings of the 25th ACM SIGKDD international conference on knowledge discovery & data mining, 2828–2837.

Tanuska, P.; Spendla, L.; Kebisek, M.; Duris, R.; and Stremy, M. 2021. Smart anomaly detection and prediction for assembly process maintenance in compliance with industry 4.0. Sensors, 21(7): 2376.

Tuli, S.; Casale, G.; and Jennings, N. R. 2022. TranAD: deep transformer networks for anomaly detection in multivariate time series data. Proc. VLDB Endow., 15(6): 1201–1214.

Wang, D.; Shelhamer, E.; Liu, S.; Olshausen, B.; and Darrell, T. 2020. Tent: Fully test-time adaptation by entropy minimization. arXiv preprint arXiv:2006.10726.

Wang, F.; Jiang, Y.; Zhang, R.; Wei, A.; Xie, J.; and Pang, X. 2025. A Survey of Deep Anomaly Detection in Multivariate

Time Series: Taxonomy, Applications, and Directions. Sensors (Basel, Switzerland), 25(1): 190.

Wang, Q.; Fink, O.; Van Gool, L.; and Dai, D. 2022. Continual test-time domain adaptation. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 7201–7211.

Wu, H.; Hu, T.; Liu, Y.; Zhou, H.; Wang, J.; and Long, M. 2022. Timesnet: Temporal 2d-variation modeling for general time series analysis. arXiv preprint arXiv:2210.02186.

Wu, X.; Qiu, X.; Li, Z.; Wang, Y.; Hu, J.; Guo, C.; Xiong, H.; and Yang, B. 2025. CATCH: Channel-Aware Multivariate Time Series Anomaly Detection via Frequency Patching. In The Thirteenth International Conference on Learning Representations.

Xu, J.; Wu, H.; Wang, J.; and Long, M. 2022. Anomaly Transformer: Time Series Anomaly Detection with Association Discrepancy. In International Conference on Learning Representations.

Zhang, C.; Song, D.; Chen, Y.; Feng, X.; Lumezanu, C.; Cheng, W.; Ni, J.; Zong, B.; Chen, H.; and Chawla, N. V. 2019. A deep neural network for unsupervised anomaly detection and diagnosis in multivariate time series data. In Proceedings of the AAAI conference on artificial intelligence, volume 33, 1409–1416.

Zhang, M.; Levine, S.; and Finn, C. 2022. Memo: Test time robustness via adaptation and augmentation. Advances in neural information processing systems, 35: 38629–38642.

Zhou, Q.; Chen, J.; Liu, H.; He, S.; and Meng, W. 2023. Detecting Multivariate Time Series Anomalies with Zero Known Label. Proceedings of the AAAI Conference on Artificial Intelligence, 37(4): 4963–4971.

Zhu, J.; Cai, S.; Deng, F.; Ooi, B. C.; and Zhang, W. 2023. METER: A Dynamic Concept Adaptation Framework for Online Anomaly Detection. Proc. VLDB Endow., 17(4):794–807.

# Supplementary Material for CANDI

## Dataset Characteristics

We evaluate our method on widely adopted benchmarks for multivariate time-series anomaly detection (MTSAD): the SWaT (Goh et al. 2016) and SMD (Su et al. 2019a) datasets. These datasets are curated from distinct domains—industrial control and IT infrastructure—and offer realistic, labeled time-series data that reflect complex system dynamics. Their domain-specific characteristics and high-fidelity anomaly labels make them essential for developing and benchmarking robust anomaly detection algorithms.

The SWaT dataset, created by the iTrust research group, captures the behavior of a water treatment plant operating under an industrial control system (ICS). It comprises sensor and actuator readings recorded during both normal operation and simulated cyber-attacks. These attacks are deliberately designed to induce faults in the system, providing ground truth labels for abnormal events. The intricate dependencies among variables and the presence of subtle anomalies make SWaT a challenging and widely used benchmark in ICS anomaly detection research.

On the other hand, the Server Machine Dataset (SMD) reflects monitoring data from large-scale server clusters. It contains multivariate metrics such as CPU usage, memory load, and disk activity, collected over long time periods. The dataset includes both normal and anomalous intervals, with anomalies representing issues like hardware failures or performance bottlenecks. SMD is well-suited for evaluating anomaly detection in IT operations and has become a standard benchmark for studying distribution shifts and temporal variability in system behavior.

SMD\_3-2 Variable 2 Over Time (from 0)  
SMD\_2-1 Variable 5 Over Time (from 0)

<table><tr><td>Dataset</td><td>Variables</td><td>Train Steps</td><td>Test Steps</td><td>Anomaly Ratio</td><td>ADF Statistics</td><td>p-value</td></tr><tr><td>SWaT</td><td>51</td><td>495,000</td><td>449,919</td><td>0.121</td><td>-0.780</td><td>0.83</td></tr><tr><td>SMD_1-7</td><td>38</td><td>23,697</td><td>23,697</td><td>0.101</td><td>-2.474</td><td>0.12</td></tr><tr><td>SMD_1-8</td><td>38</td><td>23,698</td><td>23,699</td><td>0.032</td><td>-3.305</td><td>0.01</td></tr><tr><td>SMD_2-1</td><td>38</td><td>23,693</td><td>23,694</td><td>0.049</td><td>-3.211</td><td>0.02</td></tr><tr><td>SMD_2-4</td><td>38</td><td>23,689</td><td>23,689</td><td>0.072</td><td>-3.650</td><td>0.00</td></tr><tr><td>SMD_3-2</td><td>38</td><td>23,702</td><td>23,703</td><td>0.047</td><td>-1.430</td><td>0.56</td></tr></table>

Table 5: Summary of the statistical characteristics of MTSAD datasets: the number of variables, the total time steps of train and test data, the ratio of anomalous time steps in test data, and the degree of stationarity measured using Augmented Dickey-Fuller (ADF) test statistics and the corresponding p-value.

![](images/4b63fbf98fc9587e23cdc10e69abf42f6b130ae0a094a776b97370582989e88a.jpg)  
SMD\_1-8 Variable 0 Over Time (from 0)

![](images/eb0825c333bb9e8ca77bad9cec7a025a25655222a6b4eb3468bcc285b8ee446c.jpg)

![](images/3ae8c14b0588a2078a3e39774fcd66499d1ca734b58eb630a2429e2e780d2599.jpg)

![](images/4143474da7622759aba66d2abfae410766ca6afb9503a52e836e81319c9a1f3d.jpg)

![](images/785bc34fe1061d371f3bff7da8aeb3b03001235e168d0b105c80f41ce0b2b334.jpg)

![](images/55a47796a4006a0d5c16bbde071af801eedb5eed9b454e9dae6dc6e310dc594b.jpg)  
Figure 5: Examples of distribution shifts in test data, with red shaded areas indicating true anomalies.

Table 5 summarizes the key characteristics of the MTSAD datasets used in our study, including the number of variables, the number of time steps for training and testing, the proportion of anomalies in the test set, and the stationarity of the data assessed using the Augmented Dickey-Fuller (ADF) test. The ADF test evaluates whether a time-series is stationary by testing for the presence of a unit root; a low p-value (typically < 0.05) indicates that the time-series is likely stationary, while a high p-value suggests non-stationarity. As shown, the SWaT dataset exhibits strong non-stationarity (ADF statistic = -0.780, p-value = 0.83), while datasets like SMD\_2-4 show stronger stationarity (ADF statistic = -3.650, p-value = 0.00). This variation in stationarity across datasets may influence the behavior and performance of time-series anomaly detection models.

For each dataset, we perform the ADF test on every variable individually and report the ADF statistic and the corresponding p-value of the variable with the largest p-value, representing the least stationary dimension in the dataset. This conservative reporting approach helps highlight the worst-case stationarity scenario within each dataset, which may be critical for model robustness. As shown, the SWaT dataset exhibits strong non-stationarity (ADF statistic = -0.780, p-value = 0.83), while datasets like SMD\_2-4 show stronger stationarity (ADF statistic = -3.650, p-value = 0.00). This variation in stationarity across datasets may influence the behavior and performance of time-series anomaly detection models. Figure 5 illustrates examples of distribution shifts observed in the test data of each dataset. The red shaded regions indicate periods where anomalies actually occurred.

## Additional Implementation Details

In all experiments, we set the window length to L = 10 and used a batch size of 256 for both training and testing. Since none of the datasets provided an explicit validation split, we used the last 20% of the training data as validation data. For the SWaT dataset, due to its large size, we applied a downsampling rate of 5. To ensure stability during test-time adaptation, we employed gradient clipping with a norm threshold of 0.5. Following common practices in the test-time adaptation literature, we did not apply a single-step update but instead introduced the number of adaptation steps as a hyperparameter. Adaptation was performed using stochastic gradient descent (SGD) with Nesterov momentum of 0.9 and a weight decay of 0.0001. For CANDI, we used a hidden dimension of h = 512 for the SANA module and conducted hyperparameter tuning over learning rates of 0.001, 0.003, 0.01, 0.03, and 0.1; gating parameter initialization values of 0.0, 0.1, and 0.5; and adaptation steps of 1 and 5. For M2N2, we searched over the same set of learning rates and evaluated exponential moving average (EMA) decay rates $\gamma$ of 0.9, 0.99, 0.999, and 0.9999 for the EMA update. In CANDI, both hard and moderate samples were accumulated into their respective curated adaptation sets, and adaptation was performed only when at least 16 samples had been gathered, ensuring stable model updates. To further support reliable adaptation, all latent representations were L2-normalized. This promotes a Gaussian-like latent distribution, as shown in Mahalanobis++ (Müller and Hein 2025), and stabilizes the distance-based false-positive selection used in our thresholding strategy. All experiments were conducted on a single NVIDIA A40 GPU.

Additional Experimental Results  
Parameter-Efficient Adaptation via Lightweight SANA

<table><tr><td rowspan="2">h Dimension</td><td rowspan="2">Additional Params (MB)</td><td colspan="3">SMD_1-8</td><td colspan="3">SMD_2-4</td></tr><tr><td>AUROC</td><td>AUPRC</td><td>F1</td><td>AUROC</td><td>AUPRC</td><td>F1</td></tr><tr><td>Pre-trained</td><td>0.00</td><td>0.719</td><td>0.332</td><td>0.092</td><td>0.821</td><td>0.457</td><td>0.316</td></tr><tr><td>512</td><td>7.07</td><td>0.867</td><td>0.423</td><td>0.213</td><td>0.899</td><td>0.600</td><td>0.512</td></tr><tr><td>256</td><td>2.03</td><td>0.878</td><td>0.423</td><td>0.195</td><td>0.883</td><td>0.564</td><td>0.426</td></tr><tr><td>128</td><td>0.64</td><td>0.853</td><td>0.400</td><td>0.156</td><td>0.861</td><td>0.537</td><td>0.348</td></tr><tr><td>64</td><td>0.23</td><td>0.851</td><td>0.389</td><td>0.129</td><td>0.849</td><td>0.522</td><td>0.312</td></tr><tr><td>32</td><td>0.09</td><td>0.825</td><td>0.375</td><td>0.109</td><td>0.831</td><td>0.480</td><td>0.308</td></tr></table>

Table 6: Performance comparison across different hidden dimensions h. As h decreases, the number of additional parameters is reduced, with a moderate trade-off in performance for SMD\_1-8 and SMD\_2-4. The first row shows the performance of the frozen pre-trained anomaly detector without TTA.

Table 6 presents the performance of CANDI with varying hidden dimensions h in the SANA module, which directly determines the number of additional parameters used for test-time adaptation. The results show that CANDI achieves substantial performance gains over the pre-trained model even with minimal parameter overhead. For example, with just 2.03MB of additional parameters (h = 256), CANDI improves AUROC from 0.719 to 0.878 on SMD\_1-8, and from 0.821 to 0.883 on SMD\_2-4, surpassing the pre-trained model by up to +22.1% and +7.6%, respectively. Notably, even with a very small footprint of only 0.64MB (h = 128), CANDI still improves AUROC by +13.4% and +4.0% over the non-adaptive baseline.

As h decreases further, the number of additional parameters drops significantly (e.g., 0.09MB at h = 32), and although performance degrades slightly, the results still outperform the pre-trained model in most metrics. For instance, at h = 32,

CANDI's F1 on SMD\_1-8 is 0.109, which is $+18.5\%$ higher than the pre-trained baseline (0.092), despite requiring less than 0.1MB of additional parameters.

These results confirm that CANDI enables highly parameter-efficient test-time adaptation. With minimal increases in model size, it significantly boosts anomaly detection accuracy across multiple benchmarks, making it practical for deployment in resource-constrained settings such as embedded systems or edge devices.

## Stability Across Random Seeds

<table><tr><td rowspan="2">Dataset</td><td rowspan="2">Metric (Std)</td><td colspan="3"> $\alpha = 0.5\%$ </td><td colspan="3"> $\alpha = 1.0\%$ </td><td colspan="3"> $\alpha = 5.0\%$ </td></tr><tr><td>Pre.</td><td>M2N2</td><td>CANDI (p)</td><td>Pre.</td><td>M2N2</td><td>CANDI (p)</td><td>Pre.</td><td>M2N2</td><td>CANDI (p)</td></tr><tr><td rowspan="3">SWaT</td><td>AUROC</td><td>0.000</td><td>0.000</td><td>0.005 (0.35)</td><td>0.000</td><td>0.000</td><td>0.002 (0.12)</td><td>0.000</td><td>0.000</td><td>0.002 (0.09)</td></tr><tr><td>AUPRC</td><td>0.000</td><td>0.000</td><td>0.004 (0.03)</td><td>0.000</td><td>0.000</td><td>0.001 (0.00)</td><td>0.000</td><td>0.000</td><td>0.002 (0.01)</td></tr><tr><td>F1</td><td>0.000</td><td>0.000</td><td>0.002 (0.00)</td><td>0.000</td><td>0.000</td><td>0.000 (0.00)</td><td>0.000</td><td>0.000</td><td>0.001 (0.00)</td></tr><tr><td rowspan="3">SMD_1-7</td><td>AUROC</td><td>0.000</td><td>0.000</td><td>0.018 (0.96)</td><td>0.000</td><td>0.000</td><td>0.018 (0.07)</td><td>0.000</td><td>0.000</td><td>0.018 (0.25)</td></tr><tr><td>AUPRC</td><td>0.000</td><td>0.000</td><td>0.019 (0.35)</td><td>0.000</td><td>0.000</td><td>0.019 (0.23)</td><td>0.000</td><td>0.000</td><td>0.019 (0.81)</td></tr><tr><td>F1</td><td>0.000</td><td>0.000</td><td>0.002 (0.00)</td><td>0.000</td><td>0.000</td><td>0.115 (0.18)</td><td>0.000</td><td>0.000</td><td>0.001 (0.07)</td></tr><tr><td rowspan="3">SMD_1-8</td><td>AUROC</td><td>0.000</td><td>0.000</td><td>0.001 (0.00)</td><td>0.000</td><td>0.000</td><td>0.001 (0.00)</td><td>0.000</td><td>0.000</td><td>0.002 (0.00)</td></tr><tr><td>AUPRC</td><td>0.000</td><td>0.000</td><td>0.002 (0.00)</td><td>0.000</td><td>0.000</td><td>0.002 (0.00)</td><td>0.000</td><td>0.000</td><td>0.001 (0.00)</td></tr><tr><td>F1</td><td>0.000</td><td>0.000</td><td>0.001 (0.00)</td><td>0.000</td><td>0.000</td><td>0.002 (0.00)</td><td>0.000</td><td>0.000</td><td>0.006 (0.00)</td></tr><tr><td rowspan="3">SMD_2-1</td><td>AUROC</td><td>0.000</td><td>0.000</td><td>0.004 (0.01)</td><td>0.000</td><td>0.000</td><td>0.002 (0.00)</td><td>0.000</td><td>0.000</td><td>0.041 (0.15)</td></tr><tr><td>AUPRC</td><td>0.000</td><td>0.000</td><td>0.002 (0.02)</td><td>0.000</td><td>0.000</td><td>0.001 (0.00)</td><td>0.000</td><td>0.000</td><td>0.021 (0.12)</td></tr><tr><td>F1</td><td>0.000</td><td>0.000</td><td>0.000 (0.00)</td><td>0.000</td><td>0.000</td><td>0.001 (0.01)</td><td>0.000</td><td>0.000</td><td>0.011 (0.09)</td></tr><tr><td rowspan="3">SMD_2-4</td><td>AUROC</td><td>0.000</td><td>0.000</td><td>0.001 (0.00)</td><td>0.000</td><td>0.000</td><td>0.000 (0.00)</td><td>0.000</td><td>0.000</td><td>0.009 (0.01)</td></tr><tr><td>AUPRC</td><td>0.000</td><td>0.000</td><td>0.001 (0.07)</td><td>0.000</td><td>0.000</td><td>0.001 (0.02)</td><td>0.000</td><td>0.000</td><td>0.034 (0.03)</td></tr><tr><td>F1</td><td>0.000</td><td>0.000</td><td>0.002 (0.42)</td><td>0.000</td><td>0.000</td><td>0.009 (0.17)</td><td>0.000</td><td>0.000</td><td>0.025 (0.01)</td></tr><tr><td rowspan="3">SMD_3-2</td><td>AUROC</td><td>0.000</td><td>0.000</td><td>0.006 (0.00)</td><td>0.000</td><td>0.000</td><td>0.006 (0.00)</td><td>0.000</td><td>0.000</td><td>0.008 (0.01)</td></tr><tr><td>AUPRC</td><td>0.000</td><td>0.000</td><td>0.002 (0.00)</td><td>0.000</td><td>0.000</td><td>0.002 (0.01)</td><td>0.000</td><td>0.000</td><td>0.002 (0.02)</td></tr><tr><td>F1</td><td>0.000</td><td>0.000</td><td>0.000 (0.00)</td><td>0.000</td><td>0.000</td><td>0.000 (0.00)</td><td>0.000</td><td>0.000</td><td>0.000 (0.00)</td></tr></table>

Table 7: Standard deviation and p-values of test-time adaptation performance across three random seeds. Pre. denotes a pretrained model without test-time adaptation. Pretrained and M2N2 are deterministic (std = 0.000). p-values indicate the statistical significance of CANDI's performance over M2N2.

To assess the robustness of CANDI under different initializations, we report the standard deviation of its performance across three random seeds in Table 7. CANDI exhibits consistently low variance across AUROC, AUPRC, and F1 metrics, with standard deviation values generally below 0.01 across most datasets and threshold settings. This indicates that CANDI maintains stable performance despite the inherent stochasticity of test-time adaptation, ensuring reliable and consistent detection under distribution shift.

To further assess the statistical reliability of these gains, we conducted paired t-tests comparing CANDI and M2N2 results. The table includes p-values computed from these tests. In many cases—particularly on SMD\_1-8, SMD\_2-1, and SMD\_3-2—the improvements by CANDI are statistically significant (e.g., $p < 0.05$ ), indicating that the observed gains are unlikely to be due to chance. Notably, AUPRC and F1 scores show strong significance on these datasets. However, on certain benchmarks like SMD\_1-7 and SMD\_2-4 under specific threshold settings, the p-values are higher, suggesting that performance improvements are less consistent or marginal in those cases. These results validate that CANDI not only performs stably but also provides statistically meaningful improvements over baselines in most scenarios.

## Hyperparameter Robustness Analysis

Table 8 shows the performance of CANDI under different combinations of learning rate and gating parameter initialization on SMD\_1-8. We observe that CANDI consistently achieves high performance across a wide range of hyperparameter settings, indicating strong robustness. In particular, performance remains stable when the learning rate is set to 0.03 or 0.003, with AUROC ranging from 0.860 to 0.872 and AUPRC from 0.398 to 0.424 across different gating initializations. While the F1 score shows some variation depending on the specific combination, CANDI still outperforms the baseline by a large margin in most settings.

We also evaluate the sensitivity of CANDI to the test-time batch size, an important factor in test-time adaptation since batch size determines the amount of temporal context available and often varies in practice due to latency or memory constraints. As shown in Table 9, CANDI maintains stable performance across batch sizes ranging from 64 to 512, with AUROC increasing moderately from 0.91 to 0.93 and AUPRC from 0.72 to 0.74, while the F1 score remains essentially unchanged at 0.73. These

<table><tr><td>lr</td><td>gating_init</td><td>AUROC</td><td>AUPRC</td><td>F1</td></tr><tr><td rowspan="3">0.03</td><td>0.5</td><td>0.871</td><td>0.424</td><td>0.223</td></tr><tr><td>0.1</td><td>0.860</td><td>0.403</td><td>0.254</td></tr><tr><td>0.0</td><td>0.862</td><td>0.398</td><td>0.227</td></tr><tr><td rowspan="3">0.01</td><td>0.5</td><td>0.878</td><td>0.411</td><td>0.177</td></tr><tr><td>0.1</td><td>0.852</td><td>0.400</td><td>0.205</td></tr><tr><td>0.0</td><td>0.827</td><td>0.390</td><td>0.155</td></tr><tr><td rowspan="3">0.003</td><td>0.5</td><td>0.872</td><td>0.418</td><td>0.221</td></tr><tr><td>0.1</td><td>0.796</td><td>0.367</td><td>0.123</td></tr><tr><td>0.0</td><td>0.735</td><td>0.342</td><td>0.094</td></tr></table>

Table 8: Robustness of CANDI to learning rate and gating parameter initialization on SMD\_1-8.

<table><tr><td>Batch Size</td><td>AUROC</td><td>AUPRC</td><td>F1</td></tr><tr><td>64</td><td>0.91</td><td>0.72</td><td>0.73</td></tr><tr><td>128</td><td>0.92</td><td>0.73</td><td>0.73</td></tr><tr><td>256</td><td>0.93</td><td>0.74</td><td>0.73</td></tr><tr><td>512</td><td>0.92</td><td>0.74</td><td>0.73</td></tr></table>

Table 9: Sensitivity of CANDI to different test-time batch sizes on the SMD\_1-7 dataset.  
results demonstrate that CANDI's adaptation dynamics are not overly dependent on test-time batch size, further confirming its robustness under practical test-time conditions.

## Effectiveness of CANDI Across Architectures

<table><tr><td rowspan="2">Model</td><td rowspan="2">Metric</td><td colspan="3">SMD_1-8</td><td colspan="3">SMD_2-4</td><td colspan="3">SMD_3-2</td></tr><tr><td>Pretrained</td><td>M2N2</td><td>CANDI</td><td>Pretrained</td><td>M2N2</td><td>CANDI</td><td>Pretrained</td><td>M2N2</td><td>CANDI</td></tr><tr><td rowspan="3">MLP</td><td>AUROC</td><td>0.719</td><td>0.772</td><td>0.867</td><td>0.821</td><td>0.828</td><td>0.899</td><td>0.451</td><td>0.640</td><td>0.717</td></tr><tr><td>AUPRC</td><td>0.332</td><td>0.354</td><td>0.423</td><td>0.457</td><td>0.461</td><td>0.600</td><td>0.159</td><td>0.188</td><td>0.199</td></tr><tr><td>F1</td><td>0.092</td><td>0.115</td><td>0.213</td><td>0.316</td><td>0.311</td><td>0.512</td><td>0.247</td><td>0.194</td><td>0.262</td></tr><tr><td rowspan="3">TimesNet</td><td>AUROC</td><td>0.606</td><td>0.683</td><td>0.910</td><td>0.762</td><td>0.818</td><td>0.762</td><td>0.712</td><td>0.740</td><td>0.769</td></tr><tr><td>AUPRC</td><td>0.256</td><td>0.305</td><td>0.375</td><td>0.388</td><td>0.523</td><td>0.388</td><td>0.145</td><td>0.162</td><td>0.162</td></tr><tr><td>F1</td><td>0.075</td><td>0.112</td><td>0.153</td><td>0.180</td><td>0.299</td><td>0.180</td><td>0.065</td><td>0.054</td><td>0.106</td></tr></table>

Table 10: Performance comparison of test-time adaptation methods across three SMD benchmarks for different model architectures.

Table 10 presents a comprehensive comparison of test-time adaptation methods—Pretrained (no adaptation), M2N2, and CANDI—applied to two different backbone architectures (MLP and TimesNet (Wu et al. 2022)) across three subsets of the SMD dataset. Across most settings, CANDI consistently outperforms both Pretrained and M2N2 baselines, demonstrating its effectiveness and generalizability. For example, with the MLP model on SMD\_1-8, CANDI improves AUROC from 0.719 (Pretrained) and 0.772 (M2N2) to 0.867. Similarly, on the challenging SMD\_3-2 subset, it shows substantial gains across all metrics, highlighting its robustness under severe distribution shifts. For TimesNet, which has strong baseline performance, CANDI still brings noticeable improvements—particularly on SMD\_1-8, where AUROC improves from 0.606 (Pretrained) and 0.683 (M2N2) to 0.910. These gains indicate that even high-performing models can benefit from CANDI's targeted adaptation mechanism. However, we observe relatively marginal improvements on SMD\_2-4 with TimesNet, where the performance of CANDI nearly matches that of the Pretrained model. One possible explanation is that SMD\_2-4 exhibits minimal distribution shift between training and test data, reducing the benefit of test-time adaptation. In such cases, the initial model may already generalize well, leaving little room for improvement. Another possibility is that the test-time false positives in SMD\_2-4 are less informative or less concentrated, making it harder for the False Positive Mining module to curate effective adaptation samples. Despite this, CANDI shows no sign of performance degradation, demonstrating its safety and stability even when adaptation brings limited gains. These results highlight CANDI's robustness and adaptability across varying degrees of distribution shift and model architectures.

## Evaluation on Large-Scale MTSAD Benchmark

To further validate the generality and robustness of CANDI, we additionally evaluated it on the large-scale TSB-AD benchmark (Liu and Paparrizos 2024), which provides over 1000 carefully curated TSAD datasets and addresses several well-known limitations of prior benchmarks. This benchmark covers diverse conditions, including both non-stationary and relatively stationary time-series datasets, enabling a more comprehensive evaluation of model behavior. In this setting, we report not only standard metrics such as AUPRC and AUROC but also VUS-PR and VUS-ROC (Paparrizos et al. 2022), as these metrics offer a more holistic assessment of anomaly-detection performance. Traditional threshold-based metrics like F1 are highly sensitive to the choice of anomaly-score threshold, and even threshold-free metrics such as AUROC and AUPRC remain affected by how strictly anomaly boundaries are defined in time series. VUS-PR and VUS-ROC mitigate this boundary-sensitivity by evaluating PR and ROC curves across a full range of plausible boundary tolerances, producing a continuous surface over thresholds and buffer widths. Following the protocol in (Liu and Paparrizos 2024), and because our method targets multivariate TSAD, we conducted evaluations on the designated subset of 200 multivariate datasets.

Across all five evaluation metrics—AUPRC, AUROC, VUS-PR, VUS-ROC, and F1—CANDI achieves the strongest performance among all competing methods, as shown in Table 11. Notably, the improvements on VUS-PR and VUS-ROC are particularly substantial, outperforming both established MTSAD baselines such as OmniAnomaly (Su et al. 2019b), TranAD (Tuli, Casale, and Jennings 2022), and TimesNet (Wu et al. 2022), as well as recent adaptation-based approaches including M2N2 (Kim, Park, and Choo 2024). These results indicate that CANDI not only excels on conventional MTSAD benchmarks but also sustains top-tier performance under the more rigorous and diverse evaluation setting of (Liu and Paparrizos 2024), underscoring its reliability and scalability for real-world multivariate anomaly detection.

<table><tr><td>Model</td><td>AUPRC</td><td>AUROC</td><td>VUS-PR</td><td>VUS-ROC</td><td>F1</td></tr><tr><td>CNN</td><td>0.32</td><td>0.73</td><td>0.31</td><td>0.76</td><td>0.37</td></tr><tr><td>OmniAnomaly</td><td>0.27</td><td>0.65</td><td>0.31</td><td>0.69</td><td>0.32</td></tr><tr><td>TranAD</td><td>0.14</td><td>0.59</td><td>0.18</td><td>0.65</td><td>0.21</td></tr><tr><td>TimesNet</td><td>0.13</td><td>0.56</td><td>0.19</td><td>0.64</td><td>0.20</td></tr><tr><td>M2N2</td><td>0.32</td><td>0.74</td><td>0.32</td><td>0.78</td><td>0.38</td></tr><tr><td>CANDI</td><td>0.35</td><td>0.75</td><td>0.42</td><td>0.80</td><td>0.43</td></tr></table>

Table 11: Performance on the multivariate subset of the TSB-AD benchmark, which comprises 200 carefully curated multivariate time-series datasets. Alongside standard metrics (AUPRC, AUROC, F1), we also report VUS-PR and VUS-ROC, which offer boundary-tolerance-aware, parameter-free evaluation of anomaly detection performance.

## Qualitative Results of CANDI on Anomaly Scoring

Figure 6 compares the test scores with and without the application of CANDI. The threshold was set with $\alpha = 5.0$ . Red shaded regions indicate the true anomaly intervals. When CANDI is applied, the test scores for normal samples tend to be lower compared to the case without CANDI, resulting in fewer false positives.

## Limitations and Future Work

CANDI addresses key challenges in TTA for MTSAD, but several directions remain open for future work. First, we follow the standard assumption in unsupervised multivariate time-series anomaly detection, where training data is presumed to contain only normal patterns. However, real-world scenarios may involve contaminated or noisy data even in the training data. Developing mechanisms to detect and handle such cases would further enhance robustness. We also focus on adapting model parameters, not detection thresholds. Under distribution shift, threshold adjustment may be necessary to control false positives or maintain sensitivity. CANDI minimizes the risk of adapting to anomalies by curating reliable adaptation samples through false positive mining, rather than indiscriminately updating on all test inputs. This selective strategy helps avoid learning from anomalous patterns that could degrade performance. However, exploring failure recovery mechanisms and strategies to enhance resilience under extreme distribution shifts would be valuable directions for future work. We see these directions as promising steps toward more resilient and versatile TTA systems for MTSAD.

![](images/03a2e9ba47cfd5edc5c36d9b564dd754188af586e2b406c87539f55da316f380.jpg)

SMD\_1-7 - Test Scores vs Test Scores w/ CANDI  
![](images/c688ec9e0a1f14aad4d718e14062932d41a3a539408158c748468545ea783fc0.jpg)

SMD\_1-8 - Test Scores vs Test Scores w/ CANDI  
![](images/24900c3d5c917389dc115af2019cdcb8999f33ca0b2ae75dcd06adc39de07220.jpg)

SMD\_2-1 - Test Scores vs Test Scores w/ CANDI  
![](images/f2fa6b049813a963745d7ba7bac8b1027dc3560f30418a0cffabd0ebbae1dc99.jpg)

![](images/5f3ea5e4c8f6e5ce1824135f831b24bd28b1bc78d7692f0403fe94571e645242.jpg)

![](images/b157ca9d878208ddab559d512d48ef8c27408396f2d7166f5e656f057f792cf1.jpg)  
Figure 6: Comparison of test scores with and without CANDI ( $\alpha = 5.0$ ); red shaded regions indicate true anomalies. CANDI lowers scores for normal samples, reducing false positives.