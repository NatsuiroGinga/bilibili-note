---
title: "2024-Lu-DIVERSIFY-Time-Series-OOD"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2024-Lu-DIVERSIFY-Time-Series-OOD.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# DIVERSIFY: A General Framework for Time Series Out-of-distribution Detection and Generalization

Wang Lu, Jindong Wang, Xinwei Sun, Yiqiang Chen, Senior Member, IEEE, Xiangyang Ji, Member, IEEE, Qiang Yang, Fellow, IEEE, and Xing Xie, Fellow, IEEE

Abstract—Time series remains one of the most challenging modalities in machine learning research. The out-of-distribution (OOD detection and generalization on time series tend to suffer due to its non-stationary property, i.e., the distribution changes over time. The dynamic distributions inside time series pose great challenges to existing algorithms to identify invariant distributions since they mainly focus on the scenario where the domain information is given as prior knowledge. In this paper, we attempt to exploit subdomains within a whole dataset to counteract issues induced by non-stationary for generalized representation learning. We propose DIVERSIFY, a general framework, for OOD detection and generalization on dynamic distributions of time series. DIVERSIFY takes an iterative process: it first obtains the ‘worst-case’ latent distribution scenario via adversarial training, then reduces the gap between these latent distributions. We implement DIVERSIFY via combining existing OOD detection methods according to either extracted features or outputs of models for detection while we also directly utilize outputs for classification. In addition, theoretical insights illustrate that DIVERSIFY is theoretically supported. Extensive experiments are conducted on seven datasets with different OOD settings across gesture recognition, speech commands recognition, wearable stress and affect detection, and sensor-based human activity recognition. Qualitative and quantitative results demonstrate that DIVERSIFY learns more generalized features and significantly outperforms other baselines.

Index Terms—Domain Generalization, Out-of-distribution, OOD Detection, Time Series, Representation Learning

## 1 INTRODUCTION

lems in machine learning [1], [2]. For years, there have been tremendous efforts for time series classification, such as hidden Markov models [3], RNN-based methods [4], and Transformer-based approaches [5], [6]. Time series has wide applications in a wide spectrum of applications, e.g., industrial process [7], stock predicting [8], and clinical and remote health [9]. There are several active research areas related to time series, including classification, forecasting, clustering, multivariate analysis, and high-frequency time series analysis.

The primary focus of this paper is to learn general representations for time series for better out-of-distribution (OOD) detection [10] and generalization [11]. The main difference between OOD detection and generalization is the different types of distribution shift that cause the problem: label shift and feature shift, according to variables that change in distributions. On the one hand, label shift normally occurs in classes, which means unseen targets can contain classes not present in the training data, which is studied extensively under the name of anomaly detection and OOD detection<sup>1</sup>; On the other hand, feature shift typically happens in inputs and the corresponding research field is OOD generalization that has been extensively studied [11].

OOD detection attempts to solve label shift and it has also attracted much attention recently [15]–[18]. OOD detection can be viewed as a special classification task that distinguishes between in-distribution (ID) classes and OOD classes [10], [14]. For example, Hendrycks et al. [19] trained OOD detectors against an auxiliary dataset of outliers to improve deep OOD detection while BATS [20] rectified the feature into its typical set and calculated the OOD score with the typical features to achieve reliable uncertainty estimation. As for OOD generalization, existing approaches assume the existence of several predefined domains and then endeavor to bridge gaps among domains to learn domain-invariant representations that can be seamlessly transferred to the unseen target distribution. The key in existing algorithms is to exploit the given domain information (i.e., domain index) to guide the domain-invariant representation learning. For instance, GILE [21] learned to automatically disentangle domain-agnostic and domainspecific features for generalizable sensor-based cross-person activity recognition while SDMix [22] provided a semantic data augmentation method to solve a similar problem. These methods still heavily rely on domain information.

![](images/71cc5ad0894ad006b22364510457c3ccb7b224299fe3adcaf106cb67b69d78be.jpg)

![](images/1b4132070b7cbcc2df3e7d8d76a110d51ff09e3b9496adc59a657fd0425d1e47.jpg)

![](images/a70e2d50bb97fdefec3ab26329d2c77629ce3b8976db66d044a8ad4497678724.jpg)  
Fig. 1. Illustration of D : (a) Domain generalization for image data requires known domain labels. (b) Domain labels are unknown for time series. (c) If we treat the time series data as one single domain, the sub-domains are misclassified. Different colors and shapes correspond to different classes and domains. Axes represent data values. (d) Finally, our DIVERSIFY can effectively learn the latent distributions. X-axis represents data numbers while Y-axis represents values.

Can we directly adopt existing OOD detection and generalization algorithms for time series? Unfortunately, the answer is no. Non-stationary property [23], i.e. statistical features changing over time, bring new challenges to time series OOD detection and generalization. Besides common spatial shifts in feature space, non-stationary property leads to another features shifts named temporal shifts that can occur in one class for the same subject at different times. Temporal shifts are often latent, dynamic, and variable, which makes it difficult to pre-split data and leads manual splits according to priors inaccurate. Moreover, different from computer vision, few time-series datasets are well prepartitioned. To the best of our knowledge, no work studies OOD representation by considering temporal shifts for time series OOD detection and generalization simultaneously.

Fig. 1 shows an illustrative example. OOD generalization in image classification often involves several domains whose domain labels are static and known (subfigure (a)), which can be employed to build OOD models. However, Fig. 1(b) shows that in EMG time series data [24], the distribution is changing dynamically over time and its domain information is unavailable. If no attention is paid to exploring its latent distributions (i.e., sub-domains), predictions may fail in face of diverse sub-domain distributions (subfigure (c)). This will dramatically impede existing OOD algorithms due to their reliance on domain information.

In this work, we propose DIVERSIFY, a general representation learning framework for time series OOD detection and generalization by characterizing the latent distributions inside the data. The ultimate idea of DIVERSIFY is to characterize the latent distributions inside time series without domain labels, which can then be leveraged to perform OOD detection and generalization. Concretely speaking, DIVERSIFY consists of a min-max adversarial game: on one hand, it learns to segment the time series data into several latent sub-domains by maximizing the segment-wise distribution gap to preserve diversities, i.e., the ‘worst-case’ distribution scenario; on the other hand, it learns domaininvariant representations by reducing the distribution divergence between the obtained latent domains. Such latent distributions naturally exist in time series, e.g., the activity data from multiple people follow different distributions. Additionally, our experiments show that even the data of one person still has such diversity: it can also be split into several latent distributions. After obtaining the characterized latent distributions, we can establish different implementations for downstream purposes such as OOD detection and generalization. Specifically for OOD detection, we provide two implementations, where DIVERSIFY-MAH utilizes the Mahalanobis distance with learned generalized representations while DIVERSIFY-MCP makes use of logit outputs of models. With a simple softmax activation, DIVER-SIFY can be easily used for generalization. Since DIVERSIFY can provide better representations and better predictions, all proposed implementations can significantly outperform other methods.

This paper extends our previous paper published at ICLR 2023 [15], which focuses only on OOD generalization. Compared to the previous version, this version makes substantial extensions by formulating DIVERSIFY as a general framework for both OOD detection and generalization, and then develops novel algorithms for OOD detection with more experiments and analysis.

To summarize, our contributions are four-fold:

• General framework: We propose a general framework, DIVERSIFY, to solve OOD detection and generalization simultaneously. DIVERSIFY can identify the latent distributions and learn generalized representations. We provide the theoretical insights behind DIVERSIFY to analyze its design philosophy.

• Specific implementations: For detection, we provide two implementations, DIVERSIFY-MAH and DIVERSIFY-MCP. For classification, we directly utilize outputs of DIVERSIFY with softmax activation.

• Superior performance and insightful results: Qualitative and quantitative results demonstrate the superiority of DIVERSIFY in several challenging scenarios: difficult tasks, significantly diverse datasets, and limited data. More importantly, DIVERSIFY can successfully characterize the latent distributions within a time series dataset.

• Extensibility: Besides implementations proposed in the paper, DIVERSIFY is an extensible framework, which means it can implement with more methods, e.g.

ODIN [25]. Thereby, DIVERSIFY can be applied to more applications and be further improved with more latest methods.

The remainder of this paper is organized as follows. We will introduce related work in section 2 and elaborate on the proposed method and offer a clear summary in section 3. Then, the experimental implementations and results are presented to demonstrate the superiority of DIVERSIFY for detection and generalization in section 4 and section 5 respectively while experimental analyses are provided in section 6. section 7 provides some limitations and discussions. Finally, conclusions and some possible future directions can be found in section 8.

## 2 RELATED WORK

## 2.1 Time series analysis

Time series classification is a challenging problem. Existing researches mainly focus on the modeling of temporal relations using either RNN-based methods [26] or the recentlyproposed Transformer architecture [6]. MiniRocket [27] transformed input time series using convolutional kernels and used the transformed features to train a linear classifier. MI-ShaRNN [26] was proposed to induce long-term dependencies, and yet admit parallelization. In this architecture, the first layer split inputs and ran several independent RNNs while the second layer consumed the outputs using a second RNN. PatchTST [28] segmented time series into subseries-level patches which served as input tokens to Transformer and utilized channel-independence where each channel contained a single univariate time series that shared the same embedding and Transformer weights across all the series. More related work and details can be found in the following surveys [29]–[31]. However, few studies pay attention to latent subdomains in time series to learn generalized features for OOD detection and generalization.

## 2.2 Domain/OOD generalization

Transfer learning [32], [33] trains a model on a source task and aims to enhance the performance of the model on a different but related target task. Domain generalization (DG)/out-of-distribution generalization can be viewed as a branch of transfer learning but aims at learning models that can be generalized to unseen targets whose distribution can be different from training [11], [34]. Existing methods can be categorized into three groups, namely: data manipulation [35], [36], representation learning [37], [38], and learning strategy [39], [40]. Data manipulation mainly focuses on manipulating the inputs and generating more diversified data or representations to enhance models’ generalizability. CROSSGRAD [35] utilized a Bayesian network to model dependence between label, domain, and input instance, and it parallelly a label and a domain classifier on examples perturbed by loss gradients of each other’s objectives. FACT [36] assumed that the Fourier phase information contained high-level semantics and was not easily by domain shifts. And thereby, it utilized an amplitude mix that linearly interpolated between the amplitude spectrum of two images to force the model to capture phase information. Representation learning is the most popular category in domain generalization and it can be further split into two sub-groups, domain-invariant representation learning and feature disentanglement. CIAN [37], a conditional invariant adversarial network, learned class-wise adversarial network for DG. StableNet [38] utilized a novel nonlinear feature decorrelation approach based on Random Fourier features with linear computational complexity and it could effectively partial out the irrelevant features and leverage truly relevant features for classification. Learning strategy focuses on exploiting special learning strategy to promote generalization capability. Fishr [39] introduced a new regularization and enforced domain invariance in the space of the gradients via the gradient covariance similar to CORAL [41]. SelfReg [40] proposed a new regularization method for domain generalization based on contrastive learning and it only utilized positive data pairs. More details can be found in the survey [11]. We will introduce more related work and illustrate their difference from ours.

Most domain/OOD generalization methods typically assume the availability of domain labels for training [42], [43]. Specifically, [44] also studied DG without domain labels by clustering with the style features for images, which is not applied to time series and is not end-to-end trainable. Single domain generalization is similar to our problem setting which also involves one training domain [45]–[48]. However, they treated the single domain as one distribution and did not explore latent distributions. Multi-domain learning is similar to DG which also trains on multiple domains but also tests on training distributions. [49] proposed sparse latent adapters to learn from unknown domain labels, but their work does not consider the min-max worst-case distribution scenario and optimization. In domain adaptation, [50] proposed the notion of domain index and further used variational models to learn them [51], but took a different modeling methodology since they did not consider min-max optimization. Mixture models [52] are models representing the presence of subpopulations within an overall population, e.g., Gaussian mixture models. Our approach has a similar formulation but does not use generative models. Subpopulation shift is a new setting [53] that refers to the case where the training and test domains overlap, but their relative proportions differ. Our problem does not belong to this setting since we assume that these distributions do not overlap. Distributionally robust optimization [54] shares a similar paradigm with our work, whose paradigm is also to seek a distribution that has the worst performance within a range of the raw distribution. GroupDRO [55] studied DRO at a group level. However, we study the internal distribution shift instead of seeking a global distribution close to the original one. To our best knowledge, there is only one recent work [8] that studied time series from the distribution level. However, AdaRNN is a two-stage nondifferential method that is tailored for RNN and it is mainly designed for prediction.

## 2.3 OOD detection

OOD detection has been extensively studied with a plethora of methods developed in the past few years. In simple terms, OOD detection aims to find OOD samples that belong to the classes not present in training data. Existing methods can be categorized into several groups, post-hoc methods, training-time regularization, training with Outlier Exposure, and some other methods. Comprehensive surveys can be found in [10], [14].

Post-hoc [25], [56], [57] is one of the most popular directions for its simplicity and extensibility. Odin [25] utilized temperature scaling and added small perturbations to the input to separate the softmax score distributions between ID and OOD images for more effective detection while RankFeat [56] removed the rank-1 matrix composed of the largest singular value and the associated singular vectors from the high-level feature. Another post-hoc method, ASH [57] removed a large portion of a sample’s activation at a late layer and simply adjusted the rest at inference time. Compared to post-hoc methods, training-time regularization methods require training with custom-designed goals [58], [59]. CIDER [58] jointly optimized a dispersion loss and a compactness loss to promote strong ID-OOD separability for exploiting better hyperspherical embeddings while NPOS [59] generated artificial OOD training data and facilitated learning a reliable decision boundary between ID and OOD data. Training with Outlier Exposure [60], [61] makes use of a set of collected OOD samples during training to learn the discrepancy between ID and OOD. [60] proposed a two-head deep convolutional neural network (CNN) and maximized the discrepancy between the two classifiers to detect OOD inputs while [61] proposed unsupervised dual grouping (UDG) to leverage an external unlabeled set for the joint modeling of ID and OOD data. Few studies consider feature shifts in OOD detection. [62] introduced full-spectrum OOD detection and took into account both covariate shift and semantic shift but it mainly focused on computer vision. For time series OOD detection, there still lacks effective techniques to address both two types of distribution shifts simultaneously.

## 3 METHODOLOGY

## 3.1 Problem Formulation

A time-series training dataset $\mathcal { D } ^ { t r }$ can be often preprocessed using sliding window<sup>2</sup> to N inputs: $\begin{array} { r l } { \mathcal { D } ^ { t r } } & { { } = } \end{array}$ $\{ ( \mathbf { x } _ { i } , y _ { i } ) \} _ { i = 1 } ^ { N }$ , where x<sub>i</sub> $\in \mathcal { X } \subset \mathbb { R } ^ { p }$ is the p-dimensional instance and $y _ { i } \in \mathcal { Y } = \{ 1 , . . . , C \}$ is its label. We use $\mathbb { P } ^ { t r } ( \mathbf { x } , y )$ on $\mathcal { X } \times \mathcal { V }$ to denote the joint distribution of the training dataset. Our goal is to learn a generalized model from $\mathcal { D } ^ { t \check { r } }$ to predict well on an unseen target dataset, $\mathcal { D } ^ { t e }$ , which is inaccessible in training. In our problem, the training and test datasets have the same input but different distributions, $\mathrm { i . e . , } \mathcal { X } ^ { t r } = \mathcal { X } ^ { t e }$ , but $\mathbb { P } ^ { t r } ( \mathbf { x } , y ) \dot { \neq } \mathbb { P } ^ { t e } ( \mathbf { x } , y )$

OOD detection: The testing datasets contain more classes than training datasets, i.e. $\mathcal { V } ^ { t r } \subset \mathcal { V } ^ { t e }$ . We denote the classes present in the training datasets as ID classes, $C _ { I D } = \{ 1 , \hat { 2 } , \cdots , C _ { n } \}$ , while the rest classes that only exist in the testing datasets are the OOD class, $C _ { O O D } = \{ C _ { n } + 1 \}$ We aim to train a model h from $\mathcal { D } ^ { t r }$ to detect OOD classes and achieve minimum error on $\mathcal { D } ^ { t e }$ for ID classes.

![](images/3e6029812d8669b5f48e9e25f4f76e2a7a16c514157912fe2e8647c02817e553.jpg)  
Fig. 2. Categories of distribution shifts.

OOD generalization: the training and test datasets share the same output space, i.e. $\mathcal { V } ^ { t r } = \mathcal { \bar { V } } ^ { t e }$ . We aim to train a model h from $\mathcal { D } ^ { t r }$ to achieve minimum error on $\mathcal { D } ^ { t e }$

## 3.2 Motivation

What are domain and feature distribution shifts in time series? Time series may consist of several unknown latent distributions (domains). For instance, data collected by sensors of three persons may belong to two different distributions due to their dissimilarities. This can be termed a spatial distribution shift. Surprisingly, we even find temporal distribution shifts that distributions of one person can also change at different times. Those shifts widely exist in time series, as suggested by [64], [65]. Fig. 2 gives an example where Fig. 2(a) indicates that the distribution in EMG time series data [24] is changing dynamically over time and its domain information is unavailable while Fig. 2(b) shows that the sensor data collected during walking follow different distributions across different persons. In addition, Fig. 2(c) provides an example of label shifts, where standing, running, and cycling can be in-distribution (ID) classes present in the training data while falling down is an OOD class only present in the targets.

Latent domain characterization is indispensable for OOD detection and generalization. Due to the nonstationary property, naive approaches that treat time series as one distribution fail to capture domain-invariant (OOD) features since they ignore the diversities inside the dataset. In Fig. 1(d), we assume the training domain contains two sub-domains (circle and plus points). Directly treating it as one distribution via existing OOD approaches may generate the black margin. Red star points are misclassified to the green class when predicting on the OOD domain (star points) with the learned model. Thus, multiple diverse latent distributions in time series should be characterized to learn better OOD features which are essential factors affecting performance of both OOD detection and generalization when encountering non-stationary. We name distribution shifts in Fig. 1(b) spatial distribution shifts, for which we can group data into different domains according to some specific characteristics, $\mathrm { e . g . }$ , persons, positions, and some other factors. However, in real scenarios, the information can be missing or not suitable for grouping and we only have access to a whole dataset without splits.

A brief formulation of latent domain characterization. Following the above discussions, according to feature shifts, a time series may consist of K unknown latent domains<sup>34</sup> rather than a fixed one, i.e., $\mathbb { P } ^ { t r } ( \mathbf { x } , y ) = \sum _ { i = 1 } ^ { K } \pi _ { i } \mathbb { P } ^ { i } ( \mathbf { x } , y )$ where $\mathbb { P } ^ { i } ( \mathbf { x } , y )$ is the distribution of the i-th latent one with weight $\textstyle \pi _ { i } , \sum _ { i = 1 } ^ { K } \pi _ { i } = 1 . ^ { 5 }$ There could be infinite ways to obtain $\mathbb { P } ^ { i } \mathbf { s }$ and our goal is to learn the ‘worst-case’ distribution scenario where the distribution divergence between each P<sup>i</sup> and $\mathbb { P } ^ { j }$ is maximized. Why the ‘worst-case’ scenario? It will maximally preserve the diverse information of each latent distribution, thus benefiting generalization.

![](images/81e95c6eda9a344f3e2c5a81c4329099164317e222327c046e563b4ab98c9c5e.jpg)  
Fig. 3. The framework of DIVERSIFY.

## 3.3 DIVERSIFY

In this paper, we propose DIVERSIFY to learn OOD representations for time series OOD detection and generalization. The core of DIVERSIFY is to characterize the latent distributions and then minimize the distribution divergence between each two. Concretely speaking, an iterative process is utilized: it first obtains the ’worst-case’ distribution scenario from a given dataset, then bridges the distribution gaps between each pair of latent distributions. It mainly contains four steps, where step 2 ∼ 4 are iterative:

1) Pre-processing: this step adopts the sliding window to split the entire training dataset into fixed-size windows. We argue that the data from one window is the smallest domain unit.

2) Fine-grained feature update: this step updates the feature extractor using the proposed pseudo domain-class labels as the supervision.

3) Latent distribution characterization: it aims to identify the domain label for each instance to obtain the latent distribution information. It maximizes the different distribution gaps to enlarge diversity.

4) Domain-invariant representation learning: this step utilizes pseudo domain labels from the last step to learn domain-invariant representations and train a generalizable model.

5. We use the notations $\pi _ { i }$ and $\mathbb { P } ^ { i }$ to only describe the problem, but do not formalize it.

Fine-grained Feature Update. Before characterizing latent distributions, we perform fine-grained feature updates to obtain fine-grained representation. As shown in Fig. 3 (blue), we propose a new concept: pseudo domain-class label to fully utilize the knowledge contained in domains and classes, which serves as the supervision for the feature extractor. Features are more fine-grained w.r.t. domains and labels, instead of only attached to domains or labels.

At the first iteration, there is no domain label d<sup>′</sup> and we simply initialize $d ^ { \prime } = 0$ for all samples. We treat per category per domain as a new class with label $s \in \{ \bar { 1 } , 2 , \cdots , S \}$ We have $S = K \times C ^ { 6 }$ where K is the pre-defined number of latent distributions that can be tuned in experiments. We perform pseudo domain-class label assignment to get discrete values for supervision: $s = d ^ { \prime } \times C + \bar { y }$

Let $h _ { f } ^ { ( 2 ) } , h _ { b } ^ { ( 2 ) } , h _ { c } ^ { ( 2 ) }$ be feature extractor, bottleneck, and classifier, respectively (we use superscripts to denote step number). Then, the supervised loss is computed using the cross-entropy loss ℓ:

$$
\mathcal {L} _ {s u p e r} = \mathbb {E} _ {(\mathbf {x}, y) \sim \mathbb {P} ^ {t r}} \ell \left(h _ {c} ^ {(2)} (h _ {b} ^ {(2)} (h _ {f} ^ {(2)} (\mathbf {x}))), s\right).\tag{1}
$$

Latent Distribution Characterization. This step characterizes the latent distributions contained in one dataset. As shown in Fig. 3 (green), we propose an adapted version of adversarial training to disentangle the domain labels from the class labels. However, there are no actual domain labels provided, which hinders such disentanglement. Inspired by [66], we employ a self-supervised pseudo-labeling strategy to obtain domain labels.

First, we attain the centroid for each domain with classinvariant features:

$$
\tilde {\mu} _ {k} = \frac {\sum_ {\mathbf {x} _ {i} \in \mathcal {X} ^ {t r}} \delta_ {k} (h _ {c} ^ {(3)} (h _ {b} ^ {(3)} (h _ {f} ^ {(3)} (\mathbf {x} _ {i})))) h _ {b} ^ {(3)} (h _ {f} ^ {(3)} (\mathbf {x} _ {i}))}{\sum_ {\mathbf {x} _ {i} \in \mathcal {X} ^ {t r}} \delta_ {k} (h _ {c} ^ {(3)} (h _ {b} ^ {(3)} (h _ {f} ^ {(3)} (\mathbf {x} _ {i}))))},\tag{2}
$$

6. For detection, replace C with $C _ { n }$

where $h _ { f } ^ { ( 3 ) } , h _ { b } ^ { ( 3 ) } , h _ { c } ^ { ( 3 ) }$ are feature extractor, bottleneck, and classifier, respectively. $\tilde { \mu } _ { k }$ is the initial centroid of the $k ^ { t h }$ latent domain while $\delta _ { k }$ is the $k ^ { t h }$ element of the logit softmax output. Then, we obtain the pseudo domain labels via the nearest centroid classifier using a distance function D:

$$
\tilde {d} _ {i} ^ {\prime} = \arg \min _ {k} D (h _ {b} ^ {(3)} (h _ {f} ^ {(3)} (\mathbf {x} _ {i})), \tilde {\mu} _ {k}).\tag{3}
$$

Then, we compute the centroids and obtain the updated pseudo domain labels:

$$
\begin{array}{c} \mu_ {k} = \frac {\sum_ {\mathbf {x} _ {i} \in \mathcal {X} ^ {t r}} \mathbb {I} (\tilde {d} _ {i} ^ {\prime} = k) h _ {b} ^ {(3)} (h _ {f} ^ {(3)} (\mathbf {x}))}{\sum_ {\mathbf {x} _ {i} \in \mathcal {X} ^ {t r}} \mathbb {I} (\tilde {d} _ {i} ^ {\prime} = k)}, \\ d _ {i} ^ {\prime} = \arg \min _ {k} D (h _ {b} ^ {(3)} (h _ {f} ^ {(3)} (\mathbf {x} _ {i})), \mu_ {k}), \end{array}\tag{4}
$$

where $\mathbb { I } ( a ) = 1$ when a is true, otherwise 0. After obtaining $d ^ { \prime } ,$ , we can compute the loss of step 2:

$$
\begin{array}{r} \mathcal {L} _ {s e l f} + \mathcal {L} _ {c l s} = \mathbb {E} _ {(\mathbf {x}, y) \sim \mathbb {P} ^ {t r}} \ell (h _ {c} ^ {(3)} (h _ {b} ^ {(3)} (h _ {f} ^ {(3)} (\mathbf {x}))), d ^ {\prime}) \\ + \ell (h _ {a d v} ^ {(3)} (R _ {\lambda_ {1}} (h _ {b} ^ {(3)} (h _ {f} ^ {(3)} (\mathbf {x})))), y), \end{array}\tag{5}
$$

where $h _ { a d v } ^ { ( 3 ) }$ is the discriminator for step 3 that contains several linear layers and one classification layer. $R _ { \lambda _ { 1 } }$ is the gradient reverse layer with hyperparameter $\lambda _ { 1 }$ [67]. After this step, we can obtain the pseudo domain label $d ^ { \prime }$ for x.

Domain-invariant Representation Learning. After obtaining the latent distributions, we learn domain-invariant representations for generalization. In fact, this step (purple in Fig. 3) is simple: we borrow the idea from DANN [67] and directly use adversarial training to update the classification loss $\dot { \mathcal { L } } _ { c l s }$ and domain classifier loss $\mathcal { L } _ { d o m }$ using gradient reversal layer (GRL) (a common technique that facilitates adversarial training via reversing gradients) [67]:

$$
\begin{array}{r l} & {\mathcal {L} _ {c l s} + \mathcal {L} _ {d o m} = \mathbb {E} _ {(\mathbf {x}, y) \sim \mathbb {P} ^ {t r}} \ell (h _ {c} ^ {(4)} (h _ {b} ^ {(4)} (h _ {f} ^ {(4)} (\mathbf {x}))), y)} \\ & {\qquad + \ell (h _ {a d v} ^ {(4)} (R _ {\lambda_ {2}} (h _ {b} ^ {(4)} (h _ {f} ^ {(4)} (\mathbf {x})))), d ^ {\prime}),} \end{array}\tag{6}
$$

where ℓ is the cross-entropy loss and $R _ { \lambda _ { 2 } }$ is the gradient reverse layer with hyperparameter $\lambda _ { 2 } ~ [ 6 7 ]$ . We will omit the details of GRL and adversarial training here since they are common techniques in deep learning.

Training and Complexity. We repeat these steps until convergence or max epochs. Different from existing methods, the last two steps only optimize the last few independent layers. Most of the trainable parameters are shared between modules, indicating that DIVERSIFY has the same model size as existing methods. The modules from the last step are utilized for inference.

## 3.4 DIVERSIFY for OOD detection

DIVERSIFY attempts to exploit subdomains and learn generalized representations. In this section, we provide two implementations of DIVERSIFY, DIVERSIFY-MAH and DI-VERSIFY-MCP, for time series OOD detection. In these two implementations, we first train the model with steps in section 3.3 and then combine post-hoc methods using representations and logits respectively when testing.

DIVERSIFY-MAH. Mahalanobis distance-based confidence score is a popular metric to detect OOD samples [68] and it is mainly influenced by the features/representations given by the model. We can obtain the class conditional Gaussian distributions with respect to features of the deep models under Gaussian discriminant analysis (GDA) which result in a confidence score based on the Mahalanobis distance. DIVERSIFY-MAH obtains the features of the corresponding samples using the outputs of the bottleneck,

$$
\mathbf {z} = h _ {b} ^ {(4)} (h _ {f} ^ {(4)} (\mathbf {x})).\tag{7}
$$

DIVERSIFY-MAH assumes that the class-conditional distributions of z follow multivariate Gaussian distributions,

$$
\mathbb {P} (\mathbf {z} | y = c) \sim \mathcal {N} (\mu_ {c}, \Sigma),\tag{8}
$$

where $\mu _ { c }$ is the mean of multivariate Gaussian distribution of ID class c while Σ is a tied covariance matrix,

$$
\begin{array}{l} \mu_ {c} = \frac {1}{N _ {c}} \sum_ {i: y _ {i} = c} \mathbf {z} _ {i}, \\ \Sigma = \frac {1}{N} \sum_ {c} \sum_ {i: y _ {i} = c} (\mathbf {z} _ {i} - \mu_ {c}) (\mathbf {z} _ {i} - \mu_ {c}) ^ {T}, \end{array}\tag{9}
$$

where $N _ { c }$ denotes the number of samples in class c. According to a simple theoretical connection between GDA and the softmax classifier [68]–[70], the posterior distribution defined by the generative classifier under GDA with tied covariance assumption is equivalent to the softmax classifier. Now, we can utilize the Mahalanobis distance between a test sample x and the closest class-conditional distribution as a confidence score,

$$
M (\mathbf {x}) = \max _ {c} - (\mathbf {z} - \mu_ {c}) ^ {T} \Sigma^ {- 1} (\mathbf {z} - \mu_ {c}).\tag{10}
$$

The larger $M ( \mathbf { x } )$ is, the more likely x belongs to class $c ,$ and thereby x is more likely to be an ID sample. Conversely, a small $M ( \mathbf { x } )$ illustrates that the sample can be an OOD sample. Since DIVERSIFY-MAH does not rely on the predictions of the model, it can avoid the impact of highconfidence outputs from the deep learning models.

DIVERSIFY-MCP. Maximum class probability (MCP) [19] is a popular baseline for OOD detection. It is extremely influenced by the predictions of the model since it utilizes the logit outputs of the model directly, which means that better predictions can bring better performance with MCP. Combining with MCP, we implement DIVERSIFY-MCP.

DIVERSIFY-MCP obtains an estimation vector of data as:

$$
\mathbf {y} ^ {\prime} = h _ {c} ^ {(4)} (h _ {b} ^ {(4)} (h _ {f} ^ {(4)} (\mathbf {x}))).\tag{11}
$$

Via a softmax activation, $\mathbf { y } ^ { \prime }$ can be converted into a vector ranging from 0 to 1, $\tilde { \mathbf { y } } ^ { \prime } = \operatorname { s o f t m a x } ( \mathbf { y } ^ { \prime } )$ , which can reflect the confidence of the model’s confidence to some extent. Commonly, we can view $\tilde { \mathbf { y } } ^ { \prime }$ as a probability estimation of classes.The probability $v = \mathrm { m a x } _ { y } \mathbb { P } ( y | \mathbf { x } )$ of the most likely class is the final prediction and it can also serve as an ID score. The larger v is, the more confident the model is, and thereby the sample is more likely to be an ID sample. Conversely, a small v indicates possible OOD inputs. Since modern NNs have been shown to often make over-confident softmax outputs, we can also utilize a temperature hyperparameter in the softmax activation to generate smoother predictions [71],<sup>7</sup>

7. In this paper, we simply set $T = 1 ,$

$$
\tilde {\mathbf {y}} ^ {\prime} = \operatorname{softmax} (\mathbf {y} ^ {\prime}, T), \text {   and   } \tilde {\mathbf {y}} _ {i} ^ {\prime} = \frac {\exp (\mathbf {y} _ {i} ^ {\prime} / T)}{\sum_ {j} \exp (\mathbf {y} _ {j} ^ {\prime} / T)}.\tag{12}
$$

## 3.5 DIVERSIFY for OOD generalization

DIVERSIFY can also be utilized for classification. We can directly utilize the outputs of step 4 with a softmax activation to obtain predictions,

$$
\mathbf {y} ^ {\prime} = \mathrm{softmax} (h _ {c} ^ {(4)} (h _ {b} ^ {(4)} (h _ {f} ^ {(4)} (\mathbf {x}))))\tag{13}
$$

## 3.6 Theoretical Insights

Preliminary For a distribution P with an ideal binary labeling function $h ^ { * }$ and a hypothesis $h ,$ we define the error $\varepsilon _ { \mathbb { P } } ( h )$ in accordance with [72] as:

$$
\varepsilon_ {\mathbb {P}} (h) = \mathbb {E} _ {\mathbf {x} \sim \mathbb {P}} | h (\mathbf {x}) - h ^ {*} (\mathbf {x}) |.\tag{14}
$$

We also give the definition of H-divergence according with [72]. Given two distributions $\mathbb { P } , \mathbb { Q }$ over a space X and a hypothesis class $\mathcal { H } ,$

$$
d _ {\mathcal {H}} (\mathbb {P}, \mathbb {Q}) = 2 \sup _ {h \in \mathcal {H}} | P r _ {\mathbb {P}} (I _ {h}) - P r _ {\mathbb {Q}} (I _ {h}) |,\tag{15}
$$

where $I _ { h } \ = \ \{ { \bf x } \in \mathcal { X } | h ( { \bf x } ) \ = \ 1 \}$ . We often consider the H∆H-divergence in [72] where the symmetric difference hypothesis class H∆H is the set of functions characteristic to disagreements between hypotheses.

Theorem 3.1. (Theorem 2.1 in [73], modified from Theorem 2 in [72]). Let X be a space and H be a class of hypotheses corresponding to this space. Suppose P and $\mathbb { Q }$ are distributions over $\dot { \mathcal { X } } .$ Then for any $h \in \mathcal { H } .$ , the following holds

$$
\varepsilon_ {\mathbb {Q}} (h) \leq \lambda^ {\prime \prime} + \varepsilon_ {\mathbb {P}} (h) + \frac {1}{2} d _ {\mathcal {H} \Delta \mathcal {H}} (\mathbb {Q}, \mathbb {P})\tag{16}
$$

with $\lambda ^ { \prime \prime }$ the error of an ideal joint hypothesis for $\mathbb { Q } , \mathbb { P } .$

Theorem 3.1 provides an upper bound on the targeterror. $\lambda ^ { \prime \prime }$ is a property of the dataset and hypothesis class and is often ignored. Theorem 3.1 demonstrates the necessity to learn domain invariant features.

Why DIVERSIFY can learn better representations and achieve better predictions? We present some theoretical insights to show that our approach is well motivated.

Proposition 3.2. Let X be a space and H be a class of hypotheses corresponding to this space. Let Q and the collection $\left\{ \mathbb { P } _ { i } \right\} _ { i = 1 } ^ { K }$ 1 be distributions over $\chi$ and let $\{ \bar { \varphi } _ { i } \} _ { i = 1 } ^ { K }$ be a collection of nonnegative coefficients with $\textstyle \sum _ { i } \varphi _ { i } { \dot { = } } 1$ . Let O be a set of distributions $s . t . \forall \mathbb { S } \in \mathcal { O } ,$ , the following holds

$$
d _ {\mathcal {H} \Delta \mathcal {H}} (\sum_ {i} \varphi_ {i} \mathbb {P} _ {i}, \mathbb {S}) \leq \max _ {i, j} d _ {\mathcal {H} \Delta \mathcal {H}} (\mathbb {P} _ {i}, \mathbb {P} _ {j}).\tag{17}
$$

Then, for any $h \in \mathcal { H } ,$

$$
\begin{array}{l} \varepsilon_ {\mathbb {Q}} (h) \leq \lambda^ {\prime} + \sum_ {i} \varphi_ {i} \varepsilon_ {\mathbb {P} _ {i}} (h) + \frac {1}{2} \min _ {\mathbb {S} \in \mathcal {O}} d _ {\mathcal {H} \Delta \mathcal {H}} (\mathbb {S}, \mathbb {Q}) \\ \qquad + \frac {1}{2} \max _ {i, j} d _ {\mathcal {H} \Delta \mathcal {H}} (\mathbb {P} _ {i}, \mathbb {P} _ {j}), \end{array}\tag{18}
$$

where λ<sup>′</sup> is the error of an ideal joint hypothesis. $\varepsilon _ { \mathbb { P } } ( h )$ is the error for a hypothesis h on a distribution P. $d _ { \mathcal { H } \Delta \mathcal { H } } ( \mathbb { P } , \mathbb { Q } )$ is $\mathcal { H } -$ divergence which measures differences in distribution [72].

Proof. On one hand, with Theorem 3.1, we have

$$
\varepsilon_ {\mathbb {Q}} (h) \leq \lambda_ {1} ^ {\prime} + \varepsilon_ {\mathbb {S}} (h) + \frac {1}{2} d _ {\mathcal {H} \Delta \mathcal {H}} (\mathbb {S}, \mathbb {Q}), \forall h \in \mathcal {H}, \forall \mathbb {S} \in \mathcal {O}.
$$

On the other hand, with Theorem 3.1, we have

(19)

$$
\begin{array}{r l} & {\varepsilon_ {\mathbb {S}} (h) \leq \lambda_ {2} ^ {\prime} + \varepsilon_ {\sum_ {i} \varphi_ {i} \mathbb {P} _ {i}} (h) +} \\ & {\qquad \frac {1}{2} d _ {\mathcal {H} \Delta \mathcal {H}} (\sum_ {i} \varphi_ {i} \mathbb {P} _ {i}, \mathbb {S}), \forall h \in \mathcal {H}.} \end{array}\tag{20}
$$

Since $\begin{array} { r } { d _ { \mathcal { H } \Delta \mathcal { H } } ( \sum _ { i } \varphi _ { i } \mathbb { P } _ { i } , \mathbb { S } ) ~ \leq ~ \operatorname* { m a x } _ { i , j } d _ { \mathcal { H } \Delta \mathcal { H } } ( \mathbb { P } _ { i } , \mathbb { P } _ { j } ) } \end{array}$ , and $\begin{array} { r } { \varepsilon _ { \sum _ { i } \varphi _ { i } \mathbb { P } _ { i } } ( h ) = \sum _ { i } \varphi _ { i } \varepsilon _ { \mathbb { P } _ { i } } ( h ) } \end{array}$ , we have

$$
\begin{array}{l} \varepsilon_ {\mathbb {Q}} (h) \leq \lambda^ {\prime} + \sum_ {i} \varphi_ {i} \varepsilon_ {\mathbb {P} _ {i}} (h) + \frac {1}{2} d _ {\mathcal {H} \Delta \mathcal {H}} (\mathbb {S}, \mathbb {Q}) \\ \qquad + \frac {1}{2} \max _ {i, j} d _ {\mathcal {H} \Delta \mathcal {H}} (\sum_ {i} \varphi_ {i} \mathbb {P} _ {i}, \mathbb {S}), \forall h \in \mathcal {H}, \forall \mathbb {S} \in \mathcal {O}, \end{array}\tag{21}
$$

where $\lambda ^ { \prime } = \lambda _ { 1 } ^ { \prime } + \lambda _ { 2 } ^ { \prime }$ . Equation 21 for all $\mathbb { S } ~ \in ~ \mathcal { O }$ holds. Therefore, we complete the proof.

The first item in (18), λ<sup>′</sup>, is often neglected since it is small in reality. The second item, $\textstyle \sum _ { i } \varphi _ { i } \varepsilon _ { \mathbb { P } _ { i } } ( h )$ , exists in almost all methods and can be minimized via supervision from class labels with cross-entropy loss in (6). Our main purpose is to minimize the last two items in (18). Here Q corresponds to the unseen out-of-distribution target domain.

The last term $\begin{array} { r } { \frac 1 2 \operatorname* { m a x } _ { i , j } d _ { { \mathcal { H } } \Delta { \mathcal { H } } } ( \mathbb { P } _ { i } , \mathbb { P } _ { j } ) } \end{array}$ is common in OOD theory which measures the maximum differences among source domains. This corresponds to step 4 in our approach.

Finally, the third item, $\mathbf { \frac { \dot { 1 } } { 2 } }$ $\smash { \vdots \operatorname* { m i n } _ { \mathbb { S } \in \mathcal { O } } d _ { \mathcal { H } \Delta \mathcal { H } } ( \mathbb { S } , \mathbb { Q } ) }$ , explains why we exploit sub-domains. Since our goal is to learn a model which can perform well on an unseen target domain, we cannot obtain Q. To minimize $\begin{array} { r } { \frac 1 2 \operatorname* { m i n } _ { \mathbb { S } \in { \mathcal { O } } } \breve { d } _ { \mathcal { H } \Delta \mathcal { H } } ( \mathbb { S } , \mathbb { Q } ) . } \end{array}$ we can only enlarge the range of O. We have to max $\mathbf { \Phi } _ { i , j } d _ { \mathcal { H } \Delta \mathcal { H } } \mathbf { \bar { ( P } } _ { i } , \mathbb { P } _ { j } )$ according to (17), corresponding to step 3 in our method which tries to segment the time series data into several latent sub-domains by maximizing the segment-wise distribution gap to preserve diversities, i.e. the ‘worst-case’ distribution scenario. Better representations and predictions bring improvements on OOD detection and generalization.

## 4 EXPERIMENTS ON OOD DETECTION

We perform evaluations on three diverse time series detection tasks: gesture recognition, wearable stress&affect detection, and sensor-based activity recognition. TABLE 1 shows the statistical information on datasets that we use.

TABLE 1  
Information on datasets.

<table><tr><td>Dataset</td><td>Subjects</td><td>Sensors</td><td>Classes</td><td>Samples</td></tr><tr><td>EMG</td><td>36</td><td>1</td><td>7</td><td>33,903,472</td></tr><tr><td>WESAD</td><td>15</td><td>8</td><td>4</td><td>63,000,000</td></tr><tr><td>DSADS</td><td>8</td><td>3</td><td>19</td><td>1,140,000</td></tr><tr><td>USC-HAD</td><td>14</td><td>2</td><td>12</td><td>5,441,000</td></tr><tr><td>UCI-HAR</td><td>30</td><td>2</td><td>6</td><td>1,310,000</td></tr><tr><td>PAMAP2</td><td>9</td><td>3</td><td>18</td><td>3,850,505</td></tr></table>

## 4.1 Setup

We utilize the sliding window technique to split data. As its name suggests, this technique involves taking a subset of data from a given array or sequence. Two main parameters of the sliding window technique are the window size, describing a subset length, and the step size, describing moving forward distance each time.

Time series OOD detection algorithms with feature shifts are currently less studied and we combine existing DG methods with MCP and Mahalanobis distance. We compare with five state-of-the-art methods. DANN [67] is a method that utilizes adversarial training to force the discriminator unable to classify domains for better domain-invariant features. It requires domain labels and splits data in advance while ours is a universal method. CORAL [41] utilizes the covariance alignment in feature layers for better domaininvariant features. It also requires domain labels and splits data in advance. GroupDRO [55] is a method that seeks a global distribution with the worst performance within a range of the raw distribution for better generalization. Ours study the internal distribution shift instead of seeking a global distribution close to the original one. ANDMask [74] is a gradient-based optimization method that belongs to special learning strategies.

For fairness, all methods use a feature net with two blocks and each block has one convolution layer, one pooling layer, and one batch normalization layer, following [75]. All methods are implemented with PyTorch [76]. The maximum training epoch is set to 150. The Adam optimizer with weight decay $\dot { 5 } \times 1 0 ^ { - 4 }$ is used. The learning rate for the rest methods is $1 0 ^ { - 2 } \ \mathrm { o r \ 1 0 ^ { - 3 } }$ . For the pooling layer, we utilize MaxPool2d.The kernel size is (1, 2) ad the stride is 2.

Some OOD methods require the domain labels known in training while ours does not, which is more challenging and practical. For these methods that require domain labels, we randomly assign domain labels to them in batches. We conduct the training-domain-validation strategy and the training data are split by 8 : 2 for training and validation. We tune all methods to report the average best performance of three trials. K in DIVERSIFY is treated as a hyperparameter and we tune it to record the best OOD performance.<sup>8</sup> We utilize three metrics on the testing datasets for evaluation, including ID accuracy which evaluates generalized classification capability and the Area Under the Receiver Operating Characteristic curve (AUROC) and the Area Under the Precision-Recall curve (AUPR) for evaluating OOD detection capability following [77].

## 4.2 Gesture Recognition

First, we evaluate DIVERSIFY on EMG for gestures Data Set [24]. Electromyography (EMG) is a typical time-series data that is based on bioelectric signals. EMG for gestures Data Set [24] contains raw EMG data recorded by MYO Thalmic bracelet. The bracelet is equipped with eight sensors equally spaced around the forearm that simultaneously acquire myographic signals. EMG data are scene and devicedependent, which means the same person may generate different data when performing the same activity with the same device at a different time (i.e., distribution shift across time [78], [79]) or with different devices at the same time. Data from 36 subjects are collected while they performed a series of static hand gestures and the number of instances is 40, 000 − 50, 000 recordings in each column. It contains 7 classes and we select 6 common classes performed by all subjects for our experiments. Ulnar deviations is selected as OOD class while the rests serve as the ID classes.

TABLE 2  
ID accuracy, AUROC, and AUPR on EMG. Bold means the best while underline means the second-best.

<table><tr><td rowspan="2">Targets Metrics</td><td rowspan="2">0</td><td rowspan="2">1</td><td rowspan="2">2 ID ACC</td><td rowspan="2">3</td><td rowspan="2">AVG</td><td colspan="2">AVG (+MCP)</td><td colspan="2">AVG (+MAH)</td></tr><tr><td>AUROC</td><td>AUPR</td><td>AUROC</td><td>AUPR</td></tr><tr><td>ERM</td><td>62.59</td><td>70.56</td><td>77.45</td><td>69.96</td><td>70.14</td><td>54.85</td><td>85.98</td><td>49.28</td><td>85.17</td></tr><tr><td>CORAL</td><td>66.88</td><td>82.71</td><td>82.53</td><td>73.88</td><td>76.50</td><td>61.42</td><td>89.02</td><td>64.32</td><td>90.71</td></tr><tr><td>DANN</td><td>69.69</td><td>76.17</td><td>80.74</td><td>75.80</td><td>75.60</td><td>61.54</td><td>88.31</td><td>58.79</td><td>89.08</td></tr><tr><td>GroupDRO</td><td>74.19</td><td>77.90</td><td>81.53</td><td>69.18</td><td>75.70</td><td>66.09</td><td>90.33</td><td>62.33</td><td>90.59</td></tr><tr><td>ANDMask</td><td>65.61</td><td>78.30</td><td>75.73</td><td>55.02</td><td>68.67</td><td>51.67</td><td>84.71</td><td>59.75</td><td>88.37</td></tr><tr><td>DIVERSIFY</td><td>81.43</td><td>90.39</td><td>87.26</td><td>86.19</td><td>86.32</td><td>70.76</td><td>92.66</td><td>78.38</td><td>94.65</td></tr></table>

For EMG, we set the window size to 200 and the step size to 100, which means there exist 50% overlaps between two adjacent samples. We normalize each sample with $\begin{array} { r } { \tilde { \mathbf { x } } ~ = ~ \frac { \ ' \mathbf { x } - \operatorname* { m i n } \mathbf { X } } { \operatorname* { m a x } \mathbf { X } - \operatorname* { m i n } \mathbf { X } } . } \end{array}$ . X contains all x. The final dimension is 8 × 1 × 200. We randomly divide 36 subjects into four domains (i.e., 0, 1, 2, 3) without overlapping and each domain contains data of 9 persons.

The results are shown in Table 2 and we gain the following observation. 1) Our method achieves the best performance on each task and has an improvement of about 10% on average compared to the second-best method, which demonstrates that our method has a good capability of ID classification. 2) For methods with MCP, DIVERSIFY-MCP achieves the best AUROC and AUPR on average. Compared to the second-best method, DIVERSIFY-MCP has improvements of 4.67% and 2.33% respectively. For methods with Mahalanobis distance DIVERSIFY-MAH achieves the best AUROC and AUPR on average. Compared to the second-best method, DIVERSIFY-MAH has improvements of 14.06% and 3.94% respectively. These results demonstrate that DIVERSIFY has a good ability to detect anomalies. 3) In most situations, ID accuracy has a positive relation to AUROC and AUPR, but there also exist some counterexamples. CORAL achieves better ID accuracy but worse AUROC(MCP) on average than GroupDRO. Therefore, we might need to select different hyperparameters and methods for different purposes. 4) Compared to DIVERSIFY-MCP, DIVERSIFY-MAH has another remarkable improvement but some methods, e.g. ERM-MAH and ERM-MCP, perform more terribly. These results demonstrate that our method can learn better generalized representations. And for time series OOD detection task, Mahalanobis distance is not influenced by the over-confidence of deep models while MCP might require further tuning.

## 4.3 Wearable Stress and Affect Detection

We further evaluate DIVERSIFY on a larger dataset, Wearable Stress and Affect Detection (WESAD) [80]. WESAD is a public dataset that contains physiological and motion data of 15 subjects with 63, 000, 000 instances. We utilize sensor modalities of chest-worn devices including electrocardiogram, electrodermal activity, electromyogram, respiration, body temperature, and three-axis acceleration. We split 15 subjects into four domains. We utilize the same preprocessing as EMG and select class stress as the OOD class.

TABLE 3  
ID accuracy, AUROC, and AUPR on WESAD. Bold means the best while underline means the second-best.

<table><tr><td rowspan="2">Targets Metrics</td><td rowspan="2">0</td><td rowspan="2">1</td><td rowspan="2">2 ID ACC</td><td rowspan="2">3</td><td rowspan="2">AVG</td><td colspan="2">AVG (+MCP)</td><td colspan="2">AVG (+MAH)</td></tr><tr><td>AUROC</td><td>AUPR</td><td>AUROC</td><td>AUPR</td></tr><tr><td>ERM</td><td>52.83</td><td>60.77</td><td>59.01</td><td>55.53</td><td>57.04</td><td>49.66</td><td>80.54</td><td>59.68</td><td>83.56</td></tr><tr><td>CORAL</td><td>51.66</td><td>55.22</td><td>50.19</td><td>52.49</td><td>52.39</td><td>69.98</td><td>87.97</td><td>72.67</td><td>90.94</td></tr><tr><td>DANN</td><td>49.22</td><td>57.12</td><td>56.47</td><td>59.96</td><td>55.69</td><td>60.34</td><td>85.97</td><td>65.97</td><td>86.86</td></tr><tr><td>GroupDRO</td><td>51.63</td><td>67.12</td><td>63.96</td><td>54.01</td><td>59.18</td><td>66.20</td><td>88.32</td><td>77.92</td><td>92.12</td></tr><tr><td>ANDMask</td><td>50.20</td><td>54.80</td><td>57.30</td><td>56.62</td><td>54.73</td><td>53.30</td><td>81.30</td><td>66.12</td><td>84.17</td></tr><tr><td>DIVERSIFY</td><td>48.79</td><td>73.18</td><td>60.49</td><td>75.01</td><td>64.37</td><td>77.24</td><td>92.57</td><td>88.68</td><td>96.47</td></tr></table>

The results are shown in Table 3 and we have the following observation. 1) Similar to EMG, our method has the best ID accuracy, AUROC, and AUPR on average, which demonstrates that our method has excellent abilities of classification and OOD detection. 2) For some tasks, our method obtains worse ID accuracy than other methods, which can be caused by two reasons. On the one hand, our method relies on adapted DANN to exploit subdomains and learn representations. When DANN performs terribly, our method can be influenced. On the other hand, K is a hyperparameter on the current method, and we can miss the best results due to limited searches. 3) No matter how the method performs in accuracy, DIVERSIFY-MAH performs the best, which indicates that the features DIVERSIFY extracted are outstanding. Moreover, compare to DIVERSIFY-MCP, DIVERSIFY-MAH still has another remarkable improvement.

## 4.4 Sensor-based Human Activity Recognition

Finally, we construct three diverse OOD settings by leveraging four sensor-based human activity recognition datasets: DSADS [81], USC-HAD [82], UCI-HAR [83], and PAMAP2 [84]. UCI daily and sports dataset (DSADS) [81] consists of 19 activities collected from 8 subjects wearing body-worn sensors on 5 body parts. USC-SIPI human activity dataset (USC-HAD) [82] is composed of 14 subjects (7 male, 7 female, aged 21 to 49) executing 12 activities with a sensor tied on the front right hip. UCI-HAR [83] is collected by 30 subjects performing 6 daily living activities with a waist-mounted smartphone. PAMAP2 [84] contains data from 18 activities, performed by 9 subjects wearing 3 sensors. These datasets are collected from different people and positions using accelerometer and gyroscope, with 11, 741, 000 instances in total. For DSADS, we directly utilize data split by the providers. The final dimension shape is $4 5 \times 1 \times 1 2 5 . 4 5 = 5 \times 3 \times 3$ where 5 means five positions, the first 3 means three sensors, and the second 3 means each sensor has three axes. For USC-HAD, the window size is 200 and the step size is 100. The final dimension shape is $6 \times 1 \times 2 0 0$ . For PAMAP2, the window size is 200 and the step size is 100. The final dimension shape is $2 7 \times 1 \times 2 0 0$ . For UCI-HAR, we directly utilize data split by the providers. The final dimension shape is $6 \times 1 \times 1 2 8 . ~ ( 1 )$ X-person generalization (Cross-person) aims to learn generalized models for different persons. This setting utilizes DSADS, USC-HAD, and PAMAP2. Within each dataset, we randomly split the data into four groups. For DSADS, we choose running, ascending stairs, descending stairs, rope jumping, and playing basketball as OOD classes. For USC-HAD, we choose Running Forward and Jumping Up as OOD classes. For PAMAP2, we choose running, Nordic walking, and rope jumping as OOD classes. (2) X-position generalization (Cross-position) aims to learn generalized models for different sensor positions. This setting uses DSADS and data from each position denotes a different domain. Thereby, a sample is split into five samples in the first dimension and the final dimension shape is $9 \times 1 \times 1 2 5$ . We choose running, ascending stairs, descending stairs, rope jumping, and playing basketball as OOD classes. (3) X-dataset generalization (Cross-dataset) aims to learn generalized models for different datasets. This setting uses all four datasets, and each dataset corresponds to a different domain. Six common classes are selected. Two sensors from each dataset that belong to the same position are selected and data is down-sampled to have the same dimension. The final dimension shape is $6 \times 1 \times 5 0$ . We choose ascending and descending as OOD classes.

The ID classification results are shown in Table 4 while OOD detection results are shown in Table 5. We have the following observation from these results. 1) Similar to EMG, our method has the best ID accuracy, AUROC, and AUPR on average, which demonstrates that our method has excellent abilities of classification and OOD detection. 2) When the task is difficult: in the X-Person setting, USC-HAD may be the most difficult task. Although it has more samples, it contains 14 subjects with only two sensors in one position, which may bring more difficulty in learning. The results prove the above argument that all methods perform terribly on this benchmark while ours has the largest improvement. 3) When datasets are significantly more diverse: compared to X-Person and X-Position settings, X-Dataset may be more difficult since all datasets are totally different and samples are influenced by subjects, devices, sensor positions, and some other factors. In this setting, our method is substantially better than others. 4) Limited data: for tasks on DSADS, the number of training data is limited, In this case, enhancing diversity can still bring a remarkable improvement and our method can boost the performance. 5) For time series OOD detection, it is better to utilize Mahalanobis distance since it is less influenced by over-confidence in deep learning models. For USC-HAD, DIVERSIFY-MAH even achieves an improvement of over 62% on average AUROC compared to DIVERSIFY-MCP.

## 5 EXPERIMENTS ON OOD GENERALIZATION

We perform evaluations on four diverse time series classification tasks: gesture recognition, speech commands recognition, wearable stress&affect detection, and sensor-based activity recognition. Settings and implementations are similar to OOD detection. Besides the comparison methods mentioned above, we add more latest methods designed for classification. Mixup [85] is a method that utilizes interpolation to generate more data for better generalization. Ours mainly focuses on generalized representation learning. RSC [86] is a self-challenging training algorithm that forces the network to activate features as much as possible by manipulating gradients. It belongs to gradient operation-based DG while ours is to learn generalized features. GILE [21] is a disentanglement method designed for cross-person human activity recognition. It is based on VAEs and requires domain labels. AdaRNN [8] is a method with a two-stage that is non-differential and is tailored for RNN. A specific algorithm is designed for splitting. Ours is universal and is differential with better performance. Per-segment accuracy is the evaluation metric.

TABLE 4  
ID accuracy under X-Person, X-Position, and X-Dataset settings. Bold means the best while underline means the second-best.

<table><tr><td>Task</td><td>DatasetsTargets</td><td>0</td><td>1</td><td>2</td><td>3</td><td>AVG</td><td>0</td><td>1</td><td>2</td><td>3</td><td>AVG</td><td>0</td><td>1</td><td>2</td><td>3</td><td>AVG</td></tr><tr><td rowspan="6">X-Person</td><td>ERM</td><td>86.37</td><td>72.32</td><td>80.77</td><td> $\underline{76.85}$ </td><td>79.08</td><td>81.85</td><td>58.99</td><td>71.61</td><td>58.25</td><td>67.68</td><td>86.84</td><td> $\underline{80.62}$ </td><td>49.65</td><td>85.64</td><td>75.69</td></tr><tr><td>CORAL</td><td>85.06</td><td>81.25</td><td>89.82</td><td>72.98</td><td>82.28</td><td>78.44</td><td>57.71</td><td>74.26</td><td>60.35</td><td>67.69</td><td>89.82</td><td>79.72</td><td>59.58</td><td>84.56</td><td>78.42</td></tr><tr><td>DANN</td><td>87.14</td><td>77.44</td><td>81.49</td><td>76.13</td><td>80.55</td><td>80.69</td><td>57.50</td><td>72.35</td><td>59.77</td><td>67.58</td><td>89.92</td><td>77.50</td><td>51.83</td><td>87.85</td><td>76.78</td></tr><tr><td>GroupDRO</td><td>85.18</td><td>76.25</td><td>83.75</td><td>75.71</td><td>80.22</td><td>79.71</td><td>62.50</td><td>74.30</td><td>58.43</td><td>68.73</td><td>91.32</td><td>78.23</td><td>60.68</td><td>88.73</td><td>79.74</td></tr><tr><td>ANDMask</td><td>85.00</td><td>75.89</td><td>84.40</td><td>71.13</td><td>79.11</td><td>76.77</td><td>59.98</td><td>72.13</td><td>56.24</td><td>66.28</td><td>89.82</td><td>77.82</td><td>50.80</td><td>90.16</td><td>77.15</td></tr><tr><td>DIVERSIFY</td><td>87.68</td><td>82.26</td><td>90.30</td><td>86.85</td><td>86.77</td><td>81.61</td><td>66.08</td><td>75.82</td><td>71.15</td><td>73.66</td><td>91.25</td><td>82.70</td><td>62.62</td><td>90.93</td><td>81.88</td></tr><tr><td></td><td>Targets</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>AVG</td><td></td><td>Targets</td><td>DSADS</td><td>USC-HAD</td><td>HAR</td><td>PAMAP2</td><td>AVG</td><td></td><td></td></tr><tr><td rowspan="6">X-Position</td><td>ERM</td><td>33.38</td><td>21.62</td><td> $\underline{35.43}$ </td><td>22.50</td><td>19.88</td><td>26.56</td><td rowspan="6">X-Dataset</td><td>ERM</td><td>37.11</td><td>53.05</td><td>58.84</td><td>34.34</td><td>45.83</td><td></td><td></td></tr><tr><td>CORAL</td><td>41.79</td><td>27.77</td><td>32.16</td><td>28.14</td><td>26.07</td><td>31.18</td><td>CORAL</td><td>40.00</td><td>51.47</td><td>59.57</td><td>62.18</td><td>53.31</td><td></td><td></td></tr><tr><td>DANN</td><td>40.04</td><td>29.64</td><td>30.74</td><td>22.59</td><td>23.93</td><td>29.39</td><td>DANN</td><td>40.96</td><td>54.49</td><td>61.44</td><td>66.24</td><td>55.78</td><td></td><td></td></tr><tr><td>GroupDRO</td><td>31.64</td><td>24.02</td><td>32.74</td><td>29.17</td><td>20.94</td><td>27.70</td><td>GroupDRO</td><td>40.00</td><td>55.77</td><td>60.99</td><td>72.10</td><td>57.22</td><td></td><td></td></tr><tr><td>ANDMask</td><td>31.93</td><td>24.03</td><td>33.41</td><td>23.93</td><td>23.45</td><td>27.35</td><td>ANDMask</td><td>39.57</td><td>48.08</td><td>58.39</td><td>61.68</td><td>51.93</td><td></td><td></td></tr><tr><td>DIVERSIFY</td><td>43.10</td><td>30.57</td><td>37.57</td><td>31.76</td><td>26.89</td><td>33.98</td><td>DIVERSIFY</td><td>70.70</td><td>60.48</td><td>64.00</td><td>74.28</td><td>67.36</td><td></td><td></td></tr></table>

TABLE 5

Average AUROC and AUPR under X-Person, X-Position, and X-Dataset settings. Bold means the best.

<table><tr><td rowspan="2"></td><td rowspan="2">Datasets Metrics</td><td colspan="2">DSADS</td><td colspan="2">USC-HAD</td><td colspan="2">PAMAP2</td></tr><tr><td>AUROC</td><td>AUPR</td><td>AUROC</td><td>AUPR</td><td>AUROC</td><td>AUPR</td></tr><tr><td rowspan="12">X-Person</td><td>ERM-MCP</td><td>66.82</td><td>80.52</td><td>15.50</td><td>78.71</td><td>45.95</td><td>91.85</td></tr><tr><td>CORAL-MCP</td><td>75.54</td><td>89.33</td><td>23.00</td><td>80.59</td><td>60.79</td><td>94.84</td></tr><tr><td>DANN-MCP</td><td>70.11</td><td>85.56</td><td>28.82</td><td>82.45</td><td>65.59</td><td>96.01</td></tr><tr><td>GroupDRO-MCP</td><td>78.02</td><td>90.42</td><td>27.98</td><td>82.47</td><td>65.50</td><td>95.59</td></tr><tr><td>ANDMask-MCP</td><td>69.60</td><td>85.41</td><td>17.71</td><td>79.35</td><td>51.15</td><td>93.51</td></tr><tr><td>DIVERSIFY-MCP</td><td>82.38</td><td>92.62</td><td>37.50</td><td>85.55</td><td>75.02</td><td>97.16</td></tr><tr><td>ERM-MAH</td><td>65.51</td><td>84.28</td><td>98.67</td><td>99.80</td><td>74.59</td><td>96.52</td></tr><tr><td>CORAL-MAH</td><td>67.96</td><td>85.02</td><td>99.22</td><td>99.89</td><td>88.31</td><td>98.89</td></tr><tr><td>DANN-MAH</td><td>63.33</td><td>78.88</td><td>99.36</td><td>99.91</td><td>86.15</td><td>98.61</td></tr><tr><td>GroupDRO-MAH</td><td>73.60</td><td>87.88</td><td>99.25</td><td>99.89</td><td>87.37</td><td>98.77</td></tr><tr><td>ANDMask-MAH</td><td>51.51</td><td>75.11</td><td>98.74</td><td>99.82</td><td>85.71</td><td>98.57</td></tr><tr><td>DIVERSIFY-MAH</td><td>93.90</td><td>97.36</td><td>99.56</td><td>99.94</td><td>90.37</td><td>99.14</td></tr><tr><td></td><td>Metrics</td><td>AUROC</td><td>AUPR</td><td></td><td>AUROC</td><td>AUPR</td><td></td></tr><tr><td rowspan="12">X-Position</td><td>ERM-MCP</td><td>42.23</td><td>67.65</td><td></td><td>40.03</td><td>75.91</td><td></td></tr><tr><td>CORAL-MCP</td><td>43.43</td><td>68.75</td><td></td><td>44.60</td><td>77.80</td><td></td></tr><tr><td>DANN-MCP</td><td>43.20</td><td>68.33</td><td></td><td>41.21</td><td>77.97</td><td></td></tr><tr><td>GroupDRO-MCP</td><td>42.95</td><td>69.11</td><td></td><td>47.91</td><td>79.24</td><td></td></tr><tr><td>ANDMask-MCP</td><td>39.14</td><td>66.57</td><td></td><td>38.97</td><td>74.38</td><td></td></tr><tr><td>DIVERSIFY-MCP</td><td>54.58</td><td>76.78</td><td></td><td>60.23</td><td>85.67</td><td></td></tr><tr><td>ERM-MAH</td><td>87.92</td><td>95.40</td><td></td><td>55.66</td><td>80.49</td><td></td></tr><tr><td>CORAL-MAH</td><td>87.35</td><td>95.26</td><td></td><td>75.17</td><td>90.77</td><td></td></tr><tr><td>DANN-MAH</td><td>87.04</td><td>95.01</td><td></td><td>65.07</td><td>85.46</td><td></td></tr><tr><td>GroupDRO-MAH</td><td>87.51</td><td>95.24</td><td></td><td>73.66</td><td>89.70</td><td></td></tr><tr><td>ANDMask-MAH</td><td>86.33</td><td>94.37</td><td></td><td>53.83</td><td>77.03</td><td></td></tr><tr><td>DIVERSIFY-MAH</td><td>91.85</td><td>97.04</td><td></td><td>85.50</td><td>94.86</td><td></td></tr></table>

## 5.1 Gesture Recognition

First, we evaluate DIVERSIFY on EMG for gestures Data Set [24]. We randomly divide 36 subjects into four domains (i.e., 0, 1, 2, 3). Fig. 4(a) shows that with the same backbone, our method achieves the best average performance and is 4.3% better than the second-best method. DIVERSIFY even outperforms AdaRNN which has a stronger backbone.

## 5.2 Speech Commands

Then, we adopt a regular speech recognition task, the Speech Commands dataset [87]. It consists of one-second audio recordings of both background noise and spoken words such as ‘left’ and ‘right’. It is collected from more than 2,000 persons, thus is more complicated. Following [88], we use 34,975 time series corresponding to ten spoken words to produce a balanced classification problem. Since this dataset is collected from multiple persons, the training and test distributions are different, which is also an OOD problem with one training domain. We do not split samples due to too many subjects and few audios per subject. Fig. 4(b) shows the results on two different backbones. Compared with GroupDRO, DIVERSIFY has over 1% improvement with a basic CNN backbone and over 0.6% improvement with a strong backbone MatchBoxNet3-1-64 [89]. It demonstrates the superiority of our method on a regular timeseries benchmark containing massive distributions.

![](images/83db76c033793f80570ef04d27258a6108ffe056c84febedf3f37377b1aa4f97.jpg)  
(a) EMG

![](images/68b7ef0ff8e26beafa6feab6b3df6977d9ce0bce13a5941e92ab9794bdf370c3.jpg)  
(b) Speech commands

![](images/2ca848a8faf5affa80f0ffdac0639b5500da2cf7632ba7fbabcf095862188a8b.jpg)  
(c) WESAD  
Fig. 4. Results on EMG, Speech commands and WESAD.

## 5.3 Wearable Stress and Affect Detection

We further evaluate DIVERSIFY on WESAD. We split 15 subjects into four domains. Results Fig. 4(c) showed that our method achieves the best performance compared to other state-of-the-art methods with an improvement of over 8% on this larger dataset.

## 5.4 Sensor-based Human Activity Recognition

Finally, we construct four diverse OOD settings on Sensorbased Human Activity Recognition. Besides the settings mentioned above, we add another difficult setting, One-Person-To-Another. One-Person-To-Another aims to learn generalized models for different persons from data of a single person. This setting adopts DSADS, USC-HAD, and PAMAP2. In each dataset, we randomly select four pairs of persons where one is the training and the other is the test. Four tasks are $1  0 , 3  2 , 5  4 .$ , and 7 → 6. Each number corresponds to one subject. And the final dimension shape is $4 5 \times 1 \times 1 2 5 , 6 \times 1 \times 2 0 0$ , and $2 7 \times 1 \times 2 0 0$ for DSADS, USC-HAD, and PAMAP2 respectively. <sup>9</sup>

TABLE 6  
Accuracy on cross-person generalization. “Target” 0 ∼ 4 denotes the unseen test set.

<table><tr><td rowspan="2">Target</td><td colspan="5">DSADS</td><td colspan="5">USC-HAD</td><td colspan="5">PAMAP2</td><td rowspan="2">ALL AVG</td></tr><tr><td>0</td><td>1</td><td>2</td><td>3</td><td>AVG</td><td>0</td><td>1</td><td>2</td><td>3</td><td>AVG</td><td>0</td><td>1</td><td>2</td><td>3</td><td>AVG</td></tr><tr><td>ERM</td><td>83.1</td><td>79.3</td><td>87.8</td><td>71.0</td><td>80.3</td><td>81.0</td><td>57.7</td><td>74.0</td><td>65.9</td><td>69.7</td><td>90.0</td><td>78.1</td><td>55.8</td><td>84.4</td><td>77.1</td><td>75.7</td></tr><tr><td>DANN</td><td>89.1</td><td>84.2</td><td>85.9</td><td>83.4</td><td>85.6</td><td>81.2</td><td>57.9</td><td>76.7</td><td>70.7</td><td>71.6</td><td>82.2</td><td>78.1</td><td>55.4</td><td>87.3</td><td>75.7</td><td>77.7</td></tr><tr><td>CORAL</td><td>91.0</td><td>85.8</td><td>86.6</td><td>78.2</td><td>85.4</td><td>78.8</td><td>58.9</td><td>75.0</td><td>53.7</td><td>66.6</td><td>86.2</td><td>77.8</td><td>49.0</td><td>87.8</td><td>75.2</td><td>75.7</td></tr><tr><td>Mixup</td><td>89.6</td><td>82.2</td><td>89.2</td><td>86.9</td><td>87.0</td><td>80.0</td><td>64.1</td><td>74.3</td><td>61.3</td><td>69.9</td><td>89.4</td><td>80.3</td><td>58.4</td><td>87.7</td><td>79.0</td><td>78.6</td></tr><tr><td>GroupDRO</td><td>91.7</td><td>85.9</td><td>87.6</td><td>78.3</td><td>85.9</td><td>80.1</td><td>55.5</td><td>74.7</td><td>60.0</td><td>67.6</td><td>85.2</td><td>77.7</td><td>56.2</td><td>85.0</td><td>76.0</td><td>76.5</td></tr><tr><td>RSC</td><td>84.9</td><td>82.3</td><td>86.7</td><td>77.7</td><td>82.9</td><td>81.9</td><td>57.9</td><td>73.4</td><td>65.1</td><td>69.6</td><td>87.1</td><td>76.9</td><td>60.3</td><td>87.8</td><td>78.0</td><td>76.9</td></tr><tr><td>ANDMask</td><td>85.0</td><td>75.8</td><td>87.0</td><td>77.6</td><td>81.4</td><td>79.9</td><td>55.3</td><td>74.5</td><td>65.0</td><td>68.7</td><td>86.7</td><td>76.4</td><td>43.6</td><td>85.6</td><td>73.1</td><td>74.4</td></tr><tr><td>GILE</td><td>81.0</td><td>75.0</td><td>77.0</td><td>66.0</td><td>74.7</td><td>78,0</td><td>62.0</td><td>77.0</td><td>63.0</td><td>70.0</td><td>83.0</td><td>68.0</td><td>42.0</td><td>76.0</td><td>67.5</td><td>70.7</td></tr><tr><td>AdaRNN</td><td>80.9</td><td>75.5</td><td>90.2</td><td>75.5</td><td>80.5</td><td>78.6</td><td>55.3</td><td>66.9</td><td>73.7</td><td>68.6</td><td>81.6</td><td>71.8</td><td>45.4</td><td>82.7</td><td>70.4</td><td>73.2</td></tr><tr><td>DIVERSIFY</td><td>90.4</td><td>86.5</td><td>90.0</td><td>86.1</td><td>88.2</td><td>82.6</td><td>63.5</td><td>78.7</td><td>71.3</td><td>74.0</td><td>91.0</td><td>84.3</td><td>60.5</td><td>87.7</td><td>80.8</td><td>81.0</td></tr></table>

TABLE 7

Classification accuracy on cross-position, cross-dataset, and one-to-another generalization.

<table><tr><td rowspan="2">Target</td><td colspan="6">Cross-position generalization</td><td colspan="5">Cross-dataset generalization</td><td colspan="4">One-Person-To-Another</td></tr><tr><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>AVG</td><td>0</td><td>1</td><td>2</td><td>3</td><td>AVG</td><td>DSADS</td><td>USC-HAD</td><td>PAMAP2</td><td>AVG</td></tr><tr><td>ERM</td><td>41.5</td><td>26.7</td><td>35.8</td><td>21.4</td><td>27.3</td><td>30.6</td><td>26.4</td><td>29.6</td><td>44.4</td><td>32.9</td><td>33.3</td><td>51.3</td><td>46.2</td><td>53.1</td><td>50.2</td></tr><tr><td>DANN</td><td>45.4</td><td>25.3</td><td>38.1</td><td>28.9</td><td>25.1</td><td>32.6</td><td>29.7</td><td>45.3</td><td>46.1</td><td>43.8</td><td>41.2</td><td>-</td><td>-</td><td>-</td><td>-</td></tr><tr><td>CORAL</td><td>33.2</td><td>25.2</td><td>25.8</td><td>22.3</td><td>20.6</td><td>25.4</td><td>39.5</td><td>41.8</td><td>39.1</td><td>36.6</td><td>39.2</td><td>-</td><td>-</td><td>-</td><td>-</td></tr><tr><td>Mixup</td><td>48.8</td><td>34.2</td><td>37.5</td><td>29.5</td><td>29.9</td><td>36.0</td><td>37.3</td><td>47.4</td><td>40.2</td><td>23.1</td><td>37.0</td><td>62.7</td><td>46.3</td><td>58.6</td><td>55.8</td></tr><tr><td>GroupDRO</td><td>27.1</td><td>26.7</td><td>24.3</td><td>18.4</td><td>24.8</td><td>24.3</td><td>51.4</td><td>36.7</td><td>33.2</td><td>33.8</td><td>38.8</td><td>51.3</td><td>48.0</td><td>53.1</td><td>50.8</td></tr><tr><td>RSC</td><td>46.6</td><td>27.4</td><td>35.9</td><td>27.0</td><td>29.8</td><td>33.3</td><td>33.1</td><td>39.7</td><td>45.3</td><td>45.9</td><td>41.0</td><td>59.1</td><td>49.0</td><td>59.7</td><td>55.9</td></tr><tr><td>ANDMask</td><td>47.5</td><td>31.1</td><td>39.2</td><td>30.2</td><td>29.9</td><td>35.6</td><td>41.7</td><td>33.8</td><td>43.2</td><td>40.2</td><td>39.7</td><td>57.2</td><td>45.9</td><td>54.3</td><td>52.5</td></tr><tr><td>DIVERSIFY</td><td>47.7</td><td>32.9</td><td>44.5</td><td>31.6</td><td>30.4</td><td>37.4</td><td>48.7</td><td>46.9</td><td>49.0</td><td>59.9</td><td>51.1</td><td>67.6</td><td>55.0</td><td>62.5</td><td>61.7</td></tr></table>

![](images/efefb4e2842bae7b3486e703d07c28132a1311605bd8566afc4c400227cb82bd.jpg)  
(a) Class-invariant feat.

![](images/d2a1b036729802e6d42f9dcec46b5c8743d2a13b77911378126a9f3cef1a6f8b.jpg)  
(b) Update feat. with d<sup>′</sup>

![](images/33667bcdc129982c0eec60f0fb39b07ab1c57fd2a35bd793c6f1a4244e46a0a3.jpg)  
(c) Update feature with y

![](images/3e5722d6704bb5107923d5dc1f117a04ad2b25f603b23e7ad5459a32d5ed0948.jpg)  
(d) #Domain K (EMG)  
Fig. 5. Ablation study of DIVERSIFY for detection.

TABLE 6 and 7 show the results on four settings for HAR, where our method significantly outperforms the second-best baseline by 2.4%, 1.4%, 9.9%, and 5.8% respectively. All results show the superiority of DIVERSIFY.

We observe more insightful conclusions similar to OOD detection. (1) When the task is difficult: In the Cross-Person setting, USC-HAD may be the most difficult task. The results prove the above argument that all methods perform terribly on this benchmark while ours has the largest improvement. (2) When datasets are significantly more diverse: Compared to Cross-Person and Cross-Position settings, Cross-Dataset may be more difficult. In this setting, our method is substantially better than others. (3) Limited data: Compared with the Cross-Person setting, One-Person-To-Another is more difficult since it has fewer data samples. In this case, enhancing diversity can bring a remarkable improvement and our method can boost the performance.

## 6 ANALYSIS

## 6.1 Ablation study

We present ablation study to answer the following three questions. (1) Why obtaining pseudo domain labels with classinvariantfeatures in step 3? If we obtain pseudo domain labels with common features, domain labels may have correlations with class labels, which may introduce contradictions when learning domain-invariant representations and lead to common performance. This is certified by the results in Fig. 5(a). (2) Why using fine-grained domain-class labels in step 2? If we utilize pseudo domain labels to update the feature net, it may make the representations seriously biased towards domain-related features and thereby leads to terrible performance on classification, which is proved in Fig. 5(b). If we only utilize class labels to update the feature net, it may make representations biased to class-related features, thus DIVERSIFY is unable to obtain true latent subdomains, as shown in Fig. 5(c). Hence, we should employ fine-grained domain-class labels to obtain representations with both domain and class information. (3) The more latent domains, the better? More latent domains may not bring better results (Fig. 5(d)) since a dataset may only have a few latent domains and introducing more may contradict its intrinsic data property. Plus, more latent domains also make it harder to obtain pseudo domain labels and learn domaininvariant features. For generalization, we can obtain similar observations to OOD detection from Fig. 6.

![](images/01c8835fd33c190b97eb83b65806d941ab5b485f4f683f6df1c648106f8c96cf.jpg)  
(a) Class-invariant feat.

![](images/d304a4be7259b5fea4e4592e39852bd1db15642e594e522d3d3cbe5e5a6aef15.jpg)  
(b) Update feat. with d<sup>′</sup>

![](images/9013e3410400ef6d7d1e4dd95bc015a89579c4cfebb9be4e6492c6a545e1271d.jpg)  
(c) Update feature with y

![](images/f942b2b4d9d2580b45bdbd32be8a17ceb6dcbd094387f26d6c1c591bcee9857f.jpg)  
(d) #Domain K (EMG)

Fig. 6. Ablation study of DIVERSIFY for generalization.  
![](images/f608ea2a67edfec22e9eb79226c5d1205f7b4e7eff7c0842ddc6f0f17c8ec4f3.jpg)  
(a) #Latent domains K

![](images/3a3258866074523633832aa1cbd2b3b7ee6556e82d23cd54b66a99c67d084d35.jpg)  
(b) λ<sub>1</sub>

![](images/8b308fa3ddce765733af9b4c4096eb9b0a965a992d56200e113bb0e2917a8e15.jpg)  
(c) λ<sub>2</sub>

![](images/d8ca73aedf4bdd6d1be188dcc1eb02dd0642dc8daedc36269bd783c0fa8ebdea.jpg)  
(d) Local epoch and Round

Fig. 7. Parameter sensitivity analysis (EMG) for detection.  
![](images/877f49681876f84e82b54c66a11bb183108d3780bc990b214184673f2e41b8fc.jpg)  
(a) #Latent domains K

![](images/fcff62878c209ae25eae88e6ae066b8f15806f99eaeb1e0521d763813300f375.jpg)  
(b) λ<sub>1</sub>

![](images/a5cdc2a15d485efb0b2f90767fc34fe8573661493ba478e2f89a56df5df5915a.jpg)  
(c) λ<sub>2</sub>

![](images/b8223e795e87197fd1f64257d547112c79b2640294d6cadc07e2002cc01f8b2d.jpg)  
(d) Local epoch and Round

Fig. 8. Parameter sensitivity analysis (EMG) for generalization.  
![](images/5d29ace6cc29846398b371650ecad179351cdbb1a30b9ea69ef7e4237d11d0f0.jpg)  
(a) ERM

![](images/3d808244423feca38cbc2b39abf7f93bdb3040589c3846a0ff96821d62c2e4aa.jpg)  
(b) ANDMask

![](images/69cd728fa9e54876ba35c7d58b3717013ded70130c558576bba3019a3ea5ff56.jpg)  
(c) Ours

![](images/819907d0b189194737fe014856c914b2d269180f503e155e9b3e6eb10815cd58.jpg)  
(d) ERM

![](images/366c6bce041ad03a618193ae5099b6b5f22f03ab4068c8d245e6985f69c30cd8.jpg)  
(e) ANDMask

![](images/08e5a343cb9fc8a16d13c15cd3ab23641ff8bd153f927c04f75f51012859caf8.jpg)  
(f) Ours  
Fig. 9. t-SNE visualization (EMG) for detection. For (a)-(c) black points are misclassified samples. For (d)-(e), black points mean OOD samples.

## 6.2 Parameter sensitivity

There are mainly four hyperparameters in our method: K which is the number of latent sub-domains, λ<sub>1</sub> for the adversarial part in step 3, λ<sub>2</sub> for the adversarial part in step 4, and local epochs and total rounds. For fairness, the product of local epochs and total rounds is the same value. We evaluate the parameter sensitivity of our method for detection in Fig. 7 where we change one parameter and fix the other to record the results. From these results, we can obtain the following observations. 1) For ID accuracy, our method achieves better performance in a wide range, demonstrating that our method is robust. 2) For AUROC, our method achieves better performance for a wide range in most situations, demonstrating that our method is robust. Sometimes, we need to tune hyperparameters for better AUROC carefully. We also evaluate the parameter sensitivity of DIVERSIFY on OOD generalization and the results are shown in Fig. 8. From these results, we can see that our method achieves better performance in a wide range, demonstrating that our method is robust.

![](images/a795708d05a174f2f4f8a15874432e833ad94fb8a43d7b3e56cdddcc9f357b09.jpg)  
(a) Initial domain split

![](images/73d2b71a84688b0b55fedcb0e6e4a1a8cff49f5f05258e6d0b52eeda7217cea5.jpg)  
(b) Our domain split

![](images/919c4ecc0d720e69b14f4c4aacb9e79564c81fbb178f1e6b1545c62b39a72d4b.jpg)  
(c) ANDMask

![](images/5fb155073c6137b32df2c54101c370e5a177735331c6a94fe17e73e3e4b44de0.jpg)  
(d) Our classification

Fig. 10. t-SNE visualizations for domain splits ((a) (b)) and classification ((c) (d)) on EMG data.  
![](images/3ccea5544f6c2314d73d9b1550360515da051aec47e903b42c2cb288fd7eeb71.jpg)  
(a) Temporal shift

![](images/6404c45196dcd664dad0e4fcf66a5ccde4c1ae2cf48b7a2ee551efd12cf9d869.jpg)  
(b) Spatial shift

![](images/6e56ac85bc35197e192d76eb6b1f1ddbb665e3b141ba467ba3401302ebd1ebe3.jpg)  
(c) Temporal shift

![](images/05256d8f050cd64e17eaf96a09032bd9df7b94dafe725e4976d43c6c57a15439.jpg)  
(d) Spatial shift  
Fig. 11. Latent distributions obtained by our method on two datasets. X-axis is data numbers while Y-axis is its values. (a)(b) are for detection while (c)(d) are for generalization.

## 6.3 Visualization study

We present some visualizations to show the rationales of DIVERSIFY. For detection, Fig. 9(a) and 9(c) show that DI-VERSIFY can learn better margins and generate few misclassifications while Fig. 9(d) and 9(f) show that DIVERSIFY can compact and discriminate OOD samples. For generalization, data points with different initial domain labels are mixed together in Fig. 10(a) while DIVERSIFY can characterize different latent distributions and separate them well in Fig. 10(b). Fig. 10(d) and 10(c) show that DIVERSIFY can learn better domain-invariant representations compared to the latest method ANDMask. To sum up, DIVERSIFY can find better representations to enhance generalization.

## 6.4 Existence of latent subdomains

What exactly can our DIVERSIFY learn? In Fig. 11(a), for the first subject in EMG, there is more than one latent distribution for class wrist extension, showing the existence of temporal distribution shifts: the distribution of the same activity could change. For spatial distribution shift, Fig. 11(b) on EMG dataset shows that our algorithm found two latent distributions from the EMG data of the first person and the third person. These results indicate the existence of latent distributions with both temporal and spatial distribution shifts. For generalization, there exist similar phenomena.

## 6.5 Quantitative analysis for ‘worst-case’ distributions

We present quantitative analysis by computing the Hdivergence [72] to show the effectiveness of our ‘worst-case distribution’. In Fig. 12(a) and 12(b), compared to initial domain splits, latent sub-domains generated by our method have larger H-divergence among each other. According to Prop. 3.2, larger H-divergence among domains brings better generalization. This again shows the efficacy of DIVERSIFY in computing the ’worst-case’ distribution scenario.

![](images/94aef7b973ed66f3859f4f149955da1db0994ce34b9eba339ce2f5c1f1dc9779.jpg)

![](images/cb26618e64f86d97a03cb118ef3bba769522dd980311baa8cba9957a2a45f21a.jpg)  
(a) Initial splits  
(b) Our splits  
Fig. 12. H-divergence among domains with initial splits and our splits on PAMAP2. Axes are domain numbers.

## 6.6 Extensibility

To demonstrate that our method is extensible, we also provide implementations with ODIN [25]. The OOD detection results are shown in Fig. 13(a). We have the following observations. 1) Our method still achieves the best average AUROC and AUPR on both EMG and WESAD, which demonstrates the superiority of DIVERSIFY. 2) Implementations with ODIN perform similarly to implementations with MCP, since both ODIN and MCP are dependent on models’ predictions. For some datasets, e.g. EMG, implementations with ODIN bring improvements compared to MCP but for some datasets, e.g. WESAD, implementations with ODIN perform worse. Therefore, for specific applications, we need to select the best detection techniques.

## 6.7 Varying backbones

For generalization, we attempt to demonstrate that DI-VERSIFY is robust to varying backbones. Fig. 13(b) shows the results using small, medium, and large backbones, respectively (we implement them with different numbers of layers.). Results indicate that larger models tend to achieve better OOD generalization performance. Our method outperforms others in all backbones, showing that DIVERSIFY presents consistently strong OOD performance in different architectures. We also try Transformer [90] as the backbone for comparisons. As shown in [91], Transformer often has a better generalization ability compared to CNN, which implies improving with Transformer is more difficult. From Fig. 13(c), we can see that each method with Transformer has a remarkable improvement on the first task of cross-dataset. Compared to ERM, DANN and RSC have no improvements but ours still has further improvements and achieves the best performance. DANN even performs worse than ERM, which demonstrates the importance of more accurate subdomain labels. Overall, for all architectures, our method achieves the best performance.

![](images/db69fe6f6bfb1499eafbcd014abffdcc698f531fa6e8270c2d9c4d0d2012ad42.jpg)  
(a) Extensibility

![](images/88fdae26bfc1d204ccc9d1edd44292d50ebcd2228e7126a8871c2944ead0ea6b.jpg)  
(b) Different CNNs

![](images/e3cb4ed767c084be3c73dffd003bb1def0294d1544939c73077785eadc230aa4.jpg)  
(c) Transformers

![](images/65391773f9e7fb97563cb0e800f53315dbbd504b45b7a02a16af295e0fc3a544.jpg)  
(d) Time complexity

![](images/90a999c857c4dac591a7336c44a5d4c131b1ba69fcabc0e1ad2c03f6d1ba0e23.jpg)  
(e) Convergence  
Fig. 13. Experimental analysis. (a) Extensibility on EMG and WESAD. (b)-(c) Results with different backbones on EMG and X-dataset. (d)-(e) Time complexity and convergence.

## 6.8 Time Complexity and Convergence Analysis

We also provide some analysis on time complexity and convergence. Since we only optimize the feature extractor in Step 2, our method does not cost too much time. And the results in Fig. 13(d) prove this argument empirically. The convergence results are shown in Fig. 13(e). Our method is convergent. Although there are some little fluctuations, these fluctuations exist widely in all domain generalization methods due to different distributions of different samples.

## 7 LIMITATION AND DISCUSSION

DIVERSIFY could be more perfect by pursuing the following avenues. 1) Estimate the number of latent distributions K automatically: we currently treat it as a hyperparameter. 2) Seek the semantics behind latent distributions: can adding more human knowledge obtain better latent distributions? 3) Extend DIVERSIFY beyond detection and generalization but for forecasting problems.

Moreover, we argue that dynamic distributions not only exist in time series but also in general machine learning data such as images and text [49], [51]. Thus, it is of great interest to apply our approach to these domains to further improve their performance.

## 8 CONCLUSION

We proposed DIVERSIFY, a universe framework, to learn generalized representation for time series detection and generalization. DIVERSIFY employs an adversarial game that maximizes the ‘worst-case’ distribution scenario while minimizing their distribution divergence. We provide DI-VERSIFY-MAH and DIVERSIFY-MCP via representations and predictions respectively for detection while we directly utilize DIVERSIFY for generalization. We demonstrated its effectiveness in different applications. We are surprised that one dataset can contain several latent distributions. Characterizing such latent distributions will greatly improve the generalization performance on unseen datasets.

## REFERENCES

[1] Q. Xiao, B. Wu, Y. Zhang, S. Liu, M. Pechenizkiy, E. Mocanu, and D. C. Mocanu, “Dynamic sparse network for time series classification: Learning what to “see”,” Advances in Neural Information Processing Systems, vol. 35, pp. 16 849–16 862, 2022.

[2] W. Tang, G. Long, L. Liu, T. Zhou, M. Blumenstein, and J. Jiang, “Omni-scale cnns: a simple and effective kernel size configuration for time series classification,” in International Conference on Learning Representations, 2022.

[3] B. D. Fulcher and N. S. Jones, “Highly comparative feature-based time-series classification,” IEEE Transactions on Knowledge and Data Engineering, vol. 26, no. 12, pp. 3026–3037, 2014.

[4] M. Husken and P. Stagge, “Recurrent neural networks for time ¨ series classification,” Neurocomputing, vol. 50, pp. 223–235, 2003.

[5] S. Li, X. Jin, Y. Xuan, X. Zhou, W. Chen, Y.-X. Wang, and X. Yan, “Enhancing the locality and breaking the memory bottleneck of transformer on time series forecasting,” Advances in Neural Information Processing Systems, vol. 32, pp. 5243–5253, 2019.

[6] A. Drouin, E. Marcotte, and N. Chapados, “Tactis: Transformer-<sup>´</sup> attentional copulas for time series,” in International Conference on Machine Learning, ICML, vol. 162, 2022, pp. 5447–5493.

[7] Y. Wang, C. Qian, and S. J. Qin, “Attention-mechanism based dipls-lstm and its application in industrial process time series big data prediction,” Computers & Chemical Engineering, p. 108296, 2023.

[8] Y. Du, J. Wang, W. Feng, S. Pan, T. Qin, R. Xu, and C. Wang, “Adarnn: Adaptive learning and forecasting of time series,” in Proceedings of the 30th ACM International Conference on Information & Knowledge Management, 2021, pp. 402–411.

[9] F. Di Martino and F. Delmastro, “Explainable ai for clinical and remote health applications: a survey on tabular and time series data,” Artificial Intelligence Review, vol. 56, no. 6, pp. 5261–5315, 2023.

[10] J. Yang, K. Zhou, Y. Li, and Z. Liu, “Generalized out-of-distribution detection: A survey,” arXiv preprint arXiv:2110.11334, 2021.

[11] J. Wang, C. Lan, C. Liu, Y. Ouyang, W. Zeng, and T. Qin, “Generalizing to unseen domains: A survey on domain generalization,” IEEE Transactions on Knowledge and Data Engineering (TKDE), 2022.

[12] A. Lehner, S. Gasperini, A. Marcos-Ramiro, M. Schmidt, M.-A. N. Mahani, N. Navab, B. Busam, and F. Tombari, “3d-vfield: Adversarial augmentation of point clouds for domain generalization in 3d object detection,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2022, pp. 17 295–17 304.

[13] V. Vidit, M. Engilberge, and M. Salzmann, “Clip the gap: A single domain generalization approach for object detection,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2023, pp. 3219–3229.

[14] J. Yang, P. Wang, D. Zou, Z. Zhou, K. Ding, W. Peng, H. Wang, G. Chen, B. Li, Y. Sun et al., “Openood: Benchmarking generalized out-of-distribution detection,” Advances in Neural Information Processing Systems, vol. 35, pp. 32 598–32 611, 2022.

[15] Q. Wang, J. Ye, F. Liu, Q. Dai, M. Kalander, T. Liu, H. Jianye, and B. Han, “Out-of-distribution detection with implicit outlier transformation,” in The Eleventh International Conference on Learning Representations, 2023.

[16] Y. Wang, J. Zou, J. Lin, Q. Ling, Y. Pan, T. Yao, and T. Mei, “Out-of-distribution detection via conditional kernel independence model,” Advances in Neural Information Processing Systems, vol. 35, pp. 36 411–36 425, 2022.

[17] J. Ren, J. Luo, Y. Zhao, K. Krishna, M. Saleh, B. Lakshminarayanan, and P. J. Liu, “Out-of-distribution detection and selective generation for conditional language models,” in The Eleventh International Conference on Learning Representations, 2023.

[18] Z. Fang, Y. Li, J. Lu, J. Dong, B. Han, and F. Liu, “Is out-ofdistribution detection learnable?” Advances in Neural Information Processing Systems, vol. 35, pp. 37 199–37 213, 2022.

[19] D. Hendrycks, M. Mazeika, and T. Dietterich, “Deep anomaly detection with outlier exposure,” in International Conference on Learning Representations, 2019.

[20] Y. Zhu, Y. Chen, C. Xie, X. Li, R. Zhang, H. Xue, X. Tian, Y. Chen et al., “Boosting out-of-distribution detection with typical features,” Advances in Neural Information Processing Systems, vol. 35, pp. 20 758–20 769, 2022.

[21] H. Qian, S. J. Pan, C. Miao, H. Qian, S. Pan, and C. Miao, “Latent independent excitation for generalizable sensor-based crossperson activity recognition,” in Proceedings of the AAAI Conference on Artificial Intelligence, vol. 35, no. 13, 2021, pp. 11 921–11 929.

[22] W. Lu, J. Wang, Y. Chen, S. J. Pan, C. Hu, and X. Qin, “Semanticdiscriminative mixup for generalizable sensor-based cross-domain activity recognition,” Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies, vol. 6, no. 2, pp. 1–19, 2022.

[23] V. Kuznetsov and M. Mohri, “Learning theory and algorithms for forecasting non-stationary time series,” Advances in neural information processing systems, vol. 28, 2015.

[24] S. Lobov, N. Krilova, I. Kastalskiy, V. Kazantsev, and V. A. Makarov, “Latent factors limiting the performance of semginterfaces,” Sensors, vol. 18, no. 4, p. 1122, 2018.

[25] S. Liang, Y. Li, and R. Srikant, “Enhancing the reliability of out-ofdistribution image detection in neural networks,” in International Conference on Learning Representations, 2018.

[26] D. Dennis, D. A. E. Acar, V. Mandikal, V. S. Sadasivan, V. Saligrama, H. V. Simhadri, and P. Jain, “Shallow rnn: accurate time-series classification on resource constrained devices,” Advances in Neural Information Processing Systems, vol. 32, 2019.

[27] A. Dempster, D. F. Schmidt, and G. I. Webb, “Minirocket: A very fast (almost) deterministic transform for time series classification,” in Proceedings of the 27th ACM SIGKDD conference on knowledge discovery & data mining, 2021, pp. 248–257.

[28] Y. Nie, N. H. Nguyen, P. Sinthong, and J. Kalagnanam, “A time series is worth 64 words: Long-term forecasting with transformers,” in The Eleventh International Conference on Learning Representations, 2023.

[29] H. Ismail Fawaz, G. Forestier, J. Weber, L. Idoumghar, and P.-A. Muller, “Deep learning for time series classification: a review,” Data mining and knowledge discovery, vol. 33, no. 4, pp. 917–963, 2019.

[30] K. Benidis, S. S. Rangapuram, V. Flunkert, Y. Wang, D. Maddix, C. Turkmen, J. Gasthaus, M. Bohlke-Schneider, D. Salinas, L. Stella et al., “Deep learning for time series forecasting: Tutorial and literature survey,” ACM Computing Surveys, vol. 55, no. 6, pp. 1–36, 2022.

[31] Q. Wen, T. Zhou, C. Zhang, W. Chen, Z. Ma, J. Yan, and L. Sun, “Transformers in time series: A survey,” arXiv preprint arXiv:2202.07125, 2022.

[32] S. J. Pan and Q. Yang, “A survey on transfer learning,” IEEE Transactions on knowledge and data engineering, vol. 22, no. 10, pp. 1345–1359, 2009.

[33] D. L. Silver, Q. Yang, and L. Li, “Lifelong machine learning systems: Beyond learning algorithms,” in 2013 AAAI spring symposium series, 2013.

[34] K. Zhou, Z. Liu, Y. Qiao, T. Xiang, and C. C. Loy, “Domain generalization: A survey,” IEEE Transactions on Pattern Analysis and Machine Intelligence, 2022.

[35] S. Shankar, V. Piratla, S. Chakrabarti, S. Chaudhuri, P. Jyothi, and S. Sarawagi, “Generalizing across domains via cross-gradient training,” in International Conference on Learning Representations, 2018.

[36] Q. Xu, R. Zhang, Y. Zhang, Y. Wang, and Q. Tian, “A fourierbased framework for domain generalization,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2021, pp. 14 383–14 392.

[37] Y. Li, X. Tian, M. Gong, Y. Liu, T. Liu, K. Zhang, and D. Tao, “Deep domain generalization via conditional invariant adversarial networks,” in Proceedings of the European conference on computer vision (ECCV), 2018, pp. 624–639.

[38] X. Zhang, P. Cui, R. Xu, L. Zhou, Y. He, and Z. Shen, “Deep stable learning for out-of-distribution generalization,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2021, pp. 5372–5382.

[39] A. Rame, C. Dancette, and M. Cord, “Fishr: Invariant gradient variances for out-of-distribution generalization,” in International Conference on Machine Learning, 2022, pp. 18 347–18 377.

[40] D. Kim, Y. Yoo, S. Park, J. Kim, and J. Lee, “Selfreg: Self-supervised contrastive regularization for domain generalization,” in Proceedings of the IEEE/CVF International Conference on Computer Vision, 2021, pp. 9619–9628.

[41] B. Sun and K. Saenko, “Deep coral: Correlation alignment for deep domain adaptation,” in European conference on computer vision. Springer, 2016, pp. 443–450.

[42] X. Peng, Z. Huang, X. Sun, and K. Saenko, “Domain agnostic learning with disentangled representations,” in International Conference on Machine Learning. PMLR, 2019, pp. 5102–5112.

[43] H. Zhang, Y.-F. Zhang, W. Liu, A. Weller, B. Scholkopf, and E. P.¨ Xing, “Towards principled disentanglement for domain generalization,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2022, pp. 8024–8034.

[44] T. Matsuura and T. Harada, “Domain generalization using a mixture of multiple latent domains,” in AAAI, 2020.

[45] X. Fan, Q. Wang, J. Ke, F. Yang, B. Gong, and M. Zhou, “Adversarially adaptive normalization for single domain generalization,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2021, pp. 8208–8217.

[46] L. Li, K. Gao, J. Cao, Z. Huang, Y. Weng, X. Mi, Z. Yu, X. Li, and B. Xia, “Progressive domain expansion network for single domain generalization,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2021, pp. 224–233.

[47] Z. Wang, Y. Luo, R. Qiu, Z. Huang, and M. Baktashmotlagh, “Learning to diversify for single domain generalization,” in ICCV, 2021.

[48] R. Zhu and S. Li, “Crossmatch: Cross-classifier consistency regularization for open-set single domain generalization,” in International Conference on Learning Representations, 2022.

[49] L. Deecke, T. Hospedales, and H. Bilen, “Visual representation learning over latent domains,” in International Conference on Learning Representations, 2022.

[50] H. Wang, H. He, and D. Katabi, “Continuously indexed domain adaptation,” in Proceedings of the 37th International Conference on Machine Learning, 2020, pp. 9898–9907.

[51] Z. Xu, G.-Y. Hao, H. He, and H. Wang, “Domain-indexing variational bayes: Interpretable domain index for domain adaptation,” in The Eleventh International Conference on Learning Representations, 2023.

[52] C. E. Rasmussen et al., “The infinite gaussian mixture model.” in NIPS, vol. 12. Citeseer, 1999, pp. 554–560.

[53] P. W. Koh, S. Sagawa, S. M. Xie, M. Zhang, A. Balsubramani et al., “Wilds: A benchmark of in-the-wild distribution shifts,” in ICML, 2021, pp. 5637–5664.

[54] E. Delage and Y. Ye, “Distributionally robust optimization under moment uncertainty with application to data-driven problems,” Operations research, vol. 58, no. 3, pp. 595–612, 2010.

[55] S. Sagawa, P. W. Koh, T. B. Hashimoto, and P. Liang, “Distributionally robust neural networks for group shifts: On the importance of regularization for worst-case generalization,” in International Conference on Learning Representations (ICLR), 2020.

[56] Y. Song, N. Sebe, and W. Wang, “Rankfeat: Rank-1 feature removal for out-of-distribution detection,” Advances in Neural Information Processing Systems, vol. 35, pp. 17 885–17 898, 2022.

[57] A. Djurisic, N. Bozanic, A. Ashok, and R. Liu, “Extremely simple activation shaping for out-of-distribution detection,” in The Eleventh International Conference on Learning Representations, 2023.

[58] Y. Ming, Y. Sun, O. Dia, and Y. Li, “How to exploit hyperspherical embeddings for out-of-distribution detection?” in The Eleventh International Conference on Learning Representations, 2023.

[59] L. Tao, X. Du, J. Zhu, and Y. Li, “Non-parametric outlier synthesis,” in The Eleventh International Conference on Learning Representations, 2023.

[60] Q. Yu and K. Aizawa, “Unsupervised out-of-distribution detection by maximum classifier discrepancy,” in Proceedings of the IEEE/CVF international conference on computer vision, 2019, pp. 9518–9526.

[61] J. Yang, H. Wang, L. Feng, X. Yan, H. Zheng, W. Zhang, and Z. Liu, “Semantically coherent out-of-distribution detection,” in Proceedings of the IEEE/CVF International Conference on Computer Vision, 2021, pp. 8301–8309.

[62] J. Yang, K. Zhou, and Z. Liu, “Full-spectrum out-of-distribution detection,” International Journal of Computer Vision, pp. 1–16, 2023.

[63] G. Das, K.-I. Lin, H. Mannila, G. Renganathan, and P. Smyth, “Rule discovery from time series.” in KDD, vol. 98, no. 1, 1998, pp. 16–22.

[64] W. Zhang, M. Ragab, and R. Sagarna, “Robust domain-free domain generalization with class-aware alignment,” in ICASSP 2021- 2021 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP). IEEE, 2021, pp. 2870–2874.

[65] M. Ragab, Z. Chen, W. Zhang, E. Eldele, M. Wu, C.-K. Kwoh, and X. Li, “Conditional contrastive domain generalization for fault diagnosis,” IEEE Transactions on Instrumentation and Measurement, vol. 71, pp. 1–12, 2022.

[66] M. Caron, P. Bojanowski, A. Joulin, and M. Douze, “Deep clustering for unsupervised learning of visual features,” in Proceedings of the European Conference on Computer Vision (ECCV), 2018, pp. 132– 149.

[67] Y. Ganin, E. Ustinova, H. Ajakan, P. Germain, H. Larochelle, F. Laviolette, M. Marchand, and V. Lempitsky, “Domainadversarial training of neural networks,” The journal of machine learning research, vol. 17, no. 1, pp. 2096–2030, 2016.

[68] K. Lee, K. Lee, H. Lee, and J. Shin, “A simple unified framework for detecting out-of-distribution samples and adversarial attacks,” Advances in neural information processing systems, vol. 31, 2018.

[69] J. A. Lasserre, C. M. Bishop, and T. P. Minka, “Principled hybrids of generative and discriminative models,” in 2006 IEEE Computer Society Conference on Computer Vision and Pattern Recognition (CVPR’06), vol. 1. IEEE, 2006, pp. 87–94.

[70] K. P. Murphy, Machine learning: a probabilistic perspective. MIT press, 2012.

[71] G. Hinton, O. Vinyals, and J. Dean, “Distilling the knowledge in a neural network,” arXiv preprint arXiv:1503.02531, 2015.

[72] S. Ben-David, J. Blitzer, K. Crammer, A. Kulesza, F. Pereira, and J. W. Vaughan, “A theory of learning from different domains,” Machine learning, vol. 79, no. 1, pp. 151–175, 2010.

[73] A. Sicilia, X. Zhao, and S. J. Hwang, “Domain adversarial neural networks for domain generalization: When it works and how to improve,” arXiv preprint arXiv:2102.03924, 2021.

[74] G. Parascandolo, A. Neitz, A. Orvieto, L. Gresele, and B. Scholkopf, “Learning explanations that are hard to vary,” in ¨ ICLR, 2021.

[75] J. Wang, Y. Chen, S. Hao, X. Peng, and L. Hu, “Deep learning for sensor-based activity recognition: A survey,” Pattern recognition letters, vol. 119, pp. 3–11, 2019.

[76] A. Paszke, S. Gross, F. Massa, A. Lerer, J. Bradbury, G. Chanan, T. Killeen, Z. Lin, N. Gimelshein, L. Antiga et al., “Pytorch: An imperative style, high-performance deep learning library,” vol. 32, 2019, pp. 8026–8037.

[77] D. Hendrycks and K. Gimpel, “A baseline for detecting misclassified and out-of-distribution examples in neural networks,” in International Conference on Learning Representations, 2017.

[78] G. Wilson, J. R. Doppa, and D. J. Cook, “Multi-source deep domain adaptation with weak supervision for time-series sensor data,” in Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, 2020, pp. 1768–1778.

[79] S. Purushotham, W. Carvalho, T. Nilanon, and Y. Liu, “Variational recurrent adversarial deep domain adaptation,” 2016.

[80] P. Schmidt, A. Reiss, R. Duerichen, C. Marberger, and K. Van Laerhoven, “Introducing wesad, a multimodal dataset for wearable stress and affect detection,” in Proceedings of the 20th ACM international conference on multimodal interaction, 2018, pp. 400–408.

[81] B. Barshan and M. C. Yuksek, “Recognizing daily and sports ac-¨ tivities in two open source machine learning environments using body-worn sensor units,” The Computer Journal, vol. 57, no. 11, pp. 1649–1667, 2014.

[82] M. Zhang and A. A. Sawchuk, “Usc-had: a daily activity dataset for ubiquitous activity recognition using wearable sensors,” in

Proceedings of the 2012 ACM conference on ubiquitous computing, 2012, pp. 1036–1043.

[83] D. Anguita, A. Ghio, L. Oneto, X. Parra, and J. L. Reyes-Ortiz, “Human activity recognition on smartphones using a multiclass hardware-friendly support vector machine,” in International workshop on ambient assisted living. Springer, 2012, pp. 216–223.

[84] A. Reiss and D. Stricker, “Introducing a new benchmarked dataset for activity monitoring,” in 2012 16th international symposium on wearable computers. IEEE, 2012, pp. 108–109.

[85] H. Zhang, M. Cisse, Y. N. Dauphin, and D. Lopez-Paz, “mixup: Beyond empirical risk minimization,” in International Conference on Learning Representations, 2018.

[86] Z. Huang, H. Wang, E. P. Xing, and D. Huang, “Self-challenging improves cross-domain generalization,” in ECCV, 2020, pp. 124– 140.

[87] P. Warden, “Speech commands: A dataset for limited-vocabulary speech recognition,” arXiv preprint arXiv:1804.03209, 2018.

[88] P. Kidger, J. Morrill, J. Foster, and T. Lyons, “Neural Controlled Differential Equations for Irregular Time Series,” Advances in Neural Information Processing Systems, 2020.

[89] S. Majumdar and B. Ginsburg, “Matchboxnet: 1d time-channel separable convolutional neural network architecture for speech commands recognition,” in Interspeech 2020, 21st Annual Conference of the International Speech Communication Association, Virtual Event, Shanghai, China, 25-29 October 2020. ISCA, 2020, pp. 3356–3360.

[90] A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, Ł. Kaiser, and I. Polosukhin, “Attention is all you need,” Advances in neural information processing systems, vol. 30, 2017.

[91] C. Zhang, M. Zhang, S. Zhang, D. Jin, Q. Zhou, Z. Cai, H. Zhao, X. Liu, and Z. Liu, “Delving deep into the generalization of vision transformers under distribution shifts,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2022, pp. 7277–7286.