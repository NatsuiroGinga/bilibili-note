---
title: "2024-Liu-ACON-Time-Series-Domain-Adaptation"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2024-Liu-ACON-Time-Series-Domain-Adaptation.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Boosting Transferability and Discriminability for Time Series Domain Adaptation

Mingyang Liu<sup>1</sup>, Xinyang Chen<sup>1B</sup>, Yang Shu<sup>2B</sup>, Xiucheng Li<sup>1B</sup>, Weili Guan<sup>3</sup>, Liqiang Nie<sup>1</sup> <sup>1</sup>School of Computer Science and Technology, Harbin Institute of Technology (Shenzhen) <sup>2</sup>School of Data Science and Engineering, East China Normal University <sup>3</sup>School of Electronics and Information Engineering, Harbin Institute of Technology (Shenzhen) mingyangliu1024@gmail.com, yshu@dase.ecnu.edu.cn {chenxinyang,lixiucheng,guanweili,nieliqiang}@hit.edu.cn

## Abstract

Unsupervised domain adaptation excels in transferring knowledge from a labeled source domain to an unlabeled target domain, playing a critical role in time series applications. Existing time series domain adaptation methods either ignore frequency features or treat temporal and frequency features equally, which makes it challenging to fully exploit the advantages of both types of features. In this paper, we delve into transferability and discriminability, two crucial properties in transferable representation learning. It’s insightful to note that frequency features are more discriminative within a specific domain, while temporal features show better transferability across domains. Based on the findings, we propose Adversarial CO-learning Networks (ACON), to enhance transferable representation learning through a collaborative learning manner in three aspects: (1) Considering the multi-periodicity in time series, multi-period frequency feature learning is proposed to enhance the discriminability of frequency features; (2) Temporalfrequency domain mutual learning is proposed to enhance the discriminability of temporal features in the source domain and improve the transferability of fre quency features in the target domain; (3) Domain adversarial learning is conducted in the correlation subspaces of temporal-frequency features instead of original feature spaces to further enhance the transferability of both features. Extensive experiments conducted on a wide range of time series datasets and five common applications demonstrate the state-of-the-art performance of ACON. Code is available at https://github.com/mingyangliu1024/ACON.

## 1 Introduction

Time series classification has achieved significant success in the deep learning era by leveraging discriminative features learned from extensive labeled data [18]. However, the presence of distribution shift may arise when deploying the model, potentially impeding the generalization ability of deep models [31]. Unsupervised domain adaptation [13], offering the potential to transfer knowledge from a labeled source domain to an unlabeled target domain, emerges as a promising solution.

Existing domain adaptation methods tailored for time series primarily focus on learning domaininvariant temporal features [30, 41, 29], yielding promising results. Recently, the significance of frequency features for enhancing domain-invariant representation has also been recognized [16]. However, frequency features and temporal features are treated equally, and their distinct properties are overlooked, leading to the inability to fully leverage both types of features to boost transfer learning.

In this paper, we analyze the two most important properties of features in transfer learning: transfer ability and discriminability, to investigate the characteristics of the frequency features and temporal features. We find that under the premise of adopting advanced backbones in state-of-the-art works [31, 16], frequency features are more discriminative within a specific domain, while temporal features show better transferability across domains.

Based on the findings, we propose Adversarial CO-learning Networks (ACON) to maximize the potential of temporal features and frequency features in terms of both transferability and discriminability in a collaborative learning manner. Firstly, to fully leverage the properties of multi-periodicity in time series, we propose multi-period frequency feature learning to further enhance the discriminability of frequency features. Secondly, we propose temporal-frequency domain mutual learning to enhance the discriminability of temporal features in the source domain and improve the transferability of fre quency features in the target domain. Specifically, to harness the potent discriminability of frequency features within the domain, we enable the transfer of knowledge from frequency features to temporal features within the source domain via knowledge distillation. To leverage the strong transferability of temporal features across domains, we facilitate the transfer of knowledge from temporal features to frequency features in the target domain through knowledge distillation. Thirdly, we propose to learn transferable representations via domain adversarial learning in temporal-frequency correlation subspace instead of the original temporal feature space. The temporal-frequency correlation subspace not only possesses the properties of the original temporal feature space and original frequency feature space but also incorporates the correlation between the two types of features. Learning transferable representations in the temporal-frequency correlation subspace can further enhance the transferability of features. Our main contributions can be summarized as follows:

• We uncover the characteristics wherein temporal features and frequency features cannot be equally treated in transfer learning. Specifically, we observe that frequency features are more discriminative within a specific domain, while temporal features show better transferability across domains through empirical findings.

• We design ACON, which enhances UDA in three key aspects: a multi-period feature learning module to enhance the discriminability of frequency features, a temporal-frequency domain mutual learning module to enhance the discriminability of temporal features in the source domain and improve the transferability of frequency features in the target domain, and a domain adversarial learning module in temporal-frequency correlation subspace to further enhance transferability of features.

• Experiments conducted on a wide range of time series datasets and five common applications verify the effectiveness of ACON.

## 2 Related Work

General Unsupervised Domain Adaptation Methods Unsupervised domain adaptation leverages the labeled source domain to predict the labels of a different but related, unlabeled target domain. It finds wide applications in computer vision [46, 15, 8] and natural language processing [40, 39, 44]. Existing UDA methods can be classified into three categories: (1) Methods based on adversarial training aim to learn domain-invariant representations via the game between the feature extractor and the domain discriminator. Widely used methods include DANN [13], CDAN [26] and DIRT-T [34]. (2) Methods based on statistical divergence aim to reduce the domain discrepancy by minimizing domain discrepancy in a latent feature space. Widely used methods include DAN [25], DeepCoral [36] and HoMM [5]. (3) Methods based on self-training produce pseudo-labels on unlabeled data and use confident pseudo-labels together with the labeled data to train the model. Widely used methods include PFAN[6], CST [22] and AdaMatch [2]. However, these methods are generally designed and do not fully leverage the properties of time series. Although these methods can be applied to time series through tailored feature extractors, they often obtain suboptimal performance and UDA algorithm specially designed for time series is needed.

Unsupervised Domain Adaptation for Time Series To date, a few methods have been tailored to unsupervised domain adaptation for time series data. VRADA [30] is the first UDA method for multivariate time series that uses adversarial learning for reducing domain discrepancy. In VRADA, a variational recurrent neural network (VRNN) [10] is trained in an adversarial way to learn domain-invariant temporal features. CoDATS [41] builds upon VRADA but uses a convolutional neural network for the feature extractor, proposing a solution for multi-source domain adaptation in time series classification. SASA [3] adopts LSTM [33] as feature extractors to capture the domaininvariant association, and aligns sparse associative structure between source and target domain via the minimization of maximum mean discrepancy (MMD) [38]. AdvSKM [23] modifies MMD to make it more suitable for time series data. CLUDA [29] learns contextual representation via contrastive learning, and aligns features between source and target domain via adversarial training. RAINCOAT [16] is the first to introduce frequency features into domain adaptation, aligning temporal features and frequency features respectively via Sinkhorn divergence.

Research gap In general, in terms of representation learning, most methods only focus on the temporal domain or assume that the temporal domain and the frequency domain are independent of each other, hindering the full utilization of two types of features. In terms of feature adaptation, existing works only focus on aligning temporal features or adopting simple statistical divergence to align frequency features, ignoring the different properties of the temporal features and frequency features in transfer learning. In terms of evaluation, the existing evaluations are conducted on several datasets of limited scale in a few specific tasks, and more general evaluations are needed.

## 3 Transferability and Discriminability in Time Series

## 3.1 Problem setup

In this paper, we study the UDA problem for time series classification. In time series classification problem, the model receives a set of n labeled samples $\{ ( \mathbf { x } _ { i } , \mathbf { y } _ { i } ) \} _ { i = 1 } ^ { n }$ , where i-th sample $\mathbf { x } _ { i } \in \mathbb { R } ^ { C \times T }$ contains observation of $C$ variates over $T$ time steps. We allow for both univariate and multivariate time series. In UDA setup, we are given $n _ { s }$ labeled samples from a source domain $\hat { P } = \{ ( \mathbf { x } _ { i } ^ { s } , \mathbf { y } _ { i } ^ { s } ) \} _ { i = 1 } ^ { n _ { s } }$ and $n _ { t }$ unlabeled samples from a target domain $\hat { Q } = \{ ( \mathbf { x } _ { i } ^ { t } ) \} _ { i = 1 } ^ { n _ { t } }$ , which are sampled from different distributions $P$ and $Q .$ Superscripts s and t are adopted to distinguish the source domain and the target domain. UDA for time series aims to learn a time series classification model with labeled source data $\hat { P }$ and unlabeled target data $\hat { Q } .$ , which can make accurate predictions on the target domain.

In addition to the source domain and target domain in UDA, time series naturally can be represented in the temporal domain and frequency domain. By Fast Fourier Transform (FFT), the raw time series input $\mathbf { x } _ { i }$ in the temporal domain can be transformed to corresponding frequency input $\mathbf { v } _ { i }$ in the frequency domain:

$$
\mathbf {v} _ {i} = \operatorname{FFT} \left(\mathbf {x} _ {i}\right),\tag{1}
$$

where the complex variable $\mathbf { v } _ { i } \in \mathbb { C } ^ { C \times \lfloor \frac { T } { 2 } \rfloor }$ contains observation of $C$ variates over $\left\lfloor { \frac { T } { 2 } } \right\rfloor$ different frequencies. Due to the conjugacy of frequency domain, we only consider the frequencies within $\{ 1 , { \overset { \cdot } { \dots } } , \lfloor { \frac { T } { 2 } } \rfloor \}$

## 3.2 Discriminability of frequency feature

![](images/b8f60154eac8534d2bd8b9cae38b70c8172ad23f5b048b2e14be3192a32d4866.jpg)  
(a) Temporal data vs. Frequency data

![](images/934896363303f6f542942b22f2806143ad17de3759ce71ab2a52ecbdad431d21.jpg)

![](images/e36c0ef9f5ddaa883c16be8f5af462d7925f0449899022ab783db27fc62fbeca.jpg)  
(b) Source classification  
(c) Target classification  
Figure 1: Discriminability of frequency feature: (a) The Electroencephalography (EEG) signal and corresponding frequency data of two classes in the CAP dataset: Wake and Rapid Eye Movement (REM). (b) Classification on the source domain: Temporal domain vs. Frequency domain. (c) Source-only and DANN: Temporal domain vs. Frequency domain.

As Figure 1(a) presented, compared to the uniform distribution of temporal data for different classes, the frequency data for different classes shows distinct differences in the dominant frequencies and peaks, which holds more discriminative information. To further investigate the discriminability of frequency features, we perform the single data domain classification task in the frequency domain and temporal domain respectively on all five data domains of the CAP [37, 14] dataset.

In order to minimize the impact of specific model structures, we adopt 3-layer 1D-CNN, a generic structure as the temporal feature extractor, and 1-layer linear as the frequency feature extractor, which have both widely validated for their effectiveness in existing time series analysis methods [23, 16, 42, 43]. We only retain the low-frequency data to ensure that the temporal feature extractor and the frequency feature extractor have comparable parameter quantities. For the classifiers, we uniformly use 1-layer linear. As Figure 1(b) shown, with a simple feature extractor, the frequency classification outperforms the temporal classification, demonstrating that the frequency features have better discriminability. More analysis results on different datasets are included in Appendix C.1.

## 3.3 Transferability of temporal feature

Another key criterion that characterizes the performance of domain adaptation is transferability [7]. Transferability indicates the ability to learn invariant features across domains. Since the frequency features have better discriminability within the source domain, it is natural to raise the question: Will thefrequencyfeatures also have better discriminability in the target domain?

We investigate this problem starting with the comparison of four methods: (1) Source-only-F, a model trained in the frequency domain without UDA. (2) Source-only-T, a model trained in the temporal domain without UDA. (3) DANN-F, a model aligning the source features and the target features in the frequency domain via DANN. (4) DANN-T. a model aligning the source features and the target features in the temporal domain via DANN. Figure 1(c) shows the accuracy in the target domains of four source-target domain pairs from the CAP dataset. Compared with Figure 1(b), the frequency classification, which has better discriminability performance in the source domain, actually slightly underperforms in the target domain. It indicates that better discriminability in the source domain does not necessarily imply better discriminability in the target domain. Compared with Source-only methods, the gap between DANN-F and DANN-T is further exacerbated. This suggests that the temporal feature extractor more easily learns domain-invariant features. More analysis results on different datasets are included in Appendix C.2.

The above analysis reveals two insights for time series domain adaptation: With better discriminability but worse transferability, domain adaptation in the frequency domain obtains suboptimal performance; while with better transferability, domain adaptation in the temporal domain has the potential to achieve superior performance under the guidance of more discriminative information.

## 4 Approach

Based on the above observations, our motivation is to simultaneously leverage the strong discriminability of frequency features and the strong transferability of temporal features to enhance domain adaptation. This inspires us to learn domain-invariant temporal and frequency features in a collabora tive learning manner.

Figure 2 illustrates the overall structure of our Adversarial CO-learning Networks (ACON). To avoid confusion, subscripts $T$ and $F$ are adopted to distinguish the temporal domain and the frequency domain. Specifically, in the temporal domain, we have a temporal feature extractor with temporal input $\mathbf { f } = \psi _ { T } ( \mathbf { x } )$ and a temporal classifier $\hat { \mathbf { y } } _ { T } = g _ { T } ( \mathbf { f } )$ ; while in the frequency domain, we have a frequency feature extractor with frequency input ${ \bf z } = \psi _ { F } ( { \bf v } )$ and a frequency classifier $\hat { \bf y } _ { F } = g _ { F } ( { \bf z } )$ Additionally, we have a domain discriminator $g _ { D }$ , which is trained to distinguish the source feature and the target feature. In the following, we will introduce three main contributions in ACON: multi-period frequency feature learning in Section 4.1, temporal-frequency domain mutual learning in Section 4.2, and domain adversarial learning in temporal-frequency correlation subspace in Section 4.3.

## 4.1 Multi-period frequency feature learning

The real-world time series usually present multi-periodicity, which is reflected in the frequency domain as the presence of a few dominant frequencies with significantly larger amplitudes. Data from different periods can have different discriminative patterns. Based on this, before performing FFT, we segment the raw time series according to the top-k significant periods, enhancing the discriminability of the frequency domain. Additionally, by period-based segmentation, the noises brought by meaningless high frequencies are effectively filtered out [4, 45].

![](images/b381553f49888ddad0bdf191925a4f73eb6984a200f986a77dde9727cdcf26c2.jpg)  
Figure 2: The architecture of ACON. ACON models temporal data (blue) and frequency data (green) simultaneously. Left part: Segment raw frequency data by period to capture different discriminative patterns. Middle part: Align distributions in temporal-frequency correlation subspace via adversarial training. Right part: Mutual learning between the temporal domain and frequency domain.

To capture the overall multi-periodicity, before training, we randomly sample mini-batches from the training set to perform FFT and select the frequencies with the top-k amplitudes $\{ f _ { 1 } , \ldots , f _ { k } \}$ . Given the frequency $f _ { j }$ , the corresponding period is $\begin{array} { r } { { \dot { p } } _ { j } = \lceil \frac { T } { f _ { j } } \rceil } \end{array}$ . For each selected period $p _ { j }$ in $\{ p _ { 1 } , \ldots , p _ { k } \}$ and frequency $f _ { j }$ in the corresponding $\{ f _ { 1 } , \ldots , f _ { k } \}$ , we perform the following transform on input ${ \bf x } _ { i } \mathrm { : }$

$$
\begin{array}{l} \mathbf {X} _ {i} ^ {j} = \text { Reshape } _ {p _ {j}} (\mathbf {x} _ {i}), \quad j \in \{1, \ldots , k \}, \\ \mathbf {v} _ {i} ^ {j} = \text { Avg } \left(\text { FFT } \left(\mathbf {X} _ {i} ^ {j}\right)\right). \end{array}\tag{2}
$$

where $\mathbf { X } _ { i } ^ { j } \in \mathbb { R } ^ { C \times f _ { j } \times p _ { j } } , \mathbf { v } _ { i } ^ { j } \in \mathbb { C } ^ { C \times \lfloor \frac { p _ { j } } { 2 } \rfloor }$ is averaged from $f _ { j }$ dimensions by $\operatorname { A v g } ( \cdot )$ . In other words, we perform FFT on each segment obtained by segmenting x<sub>i</sub> with period $p _ { j }$ , and average the FFT results across segments to obtain the distribution $\mathbf { v } _ { i } ^ { j }$ over the frequencies within $\{ 1 , \dotsc , \left\lfloor { \frac { p _ { j } } { 2 } } \right\rfloor \}$ . In this way, we obtain the overall frequency pattern for each period. To keep the discriminative patterns derived from different periods, we concatenate the different $\mathbf { v } _ { i } ^ { j }$ , obtaining $\mathbf { v } _ { i }$ as the frequency input corresponding to the temporal input ${ \bf x } _ { i } \mathrm { : }$

$$
\mathbf {v} _ {i} = \mathbf {v} _ {i} ^ {1} \oplus \dots \oplus \mathbf {v} _ {i} ^ {k}, \quad j \in \{1, \dots , k \}.\tag{3}
$$

We extend the source sample set $\hat { P }$ and the target sample set $\hat { Q }$ to the frequency domain: $\hat { P } =$ $\{ ( \mathbf { x } _ { i } ^ { s } , \mathbf { v } _ { i } ^ { s } , \mathbf { y } _ { i } ^ { s } ) \} _ { i = 1 } ^ { n _ { s } }$ and $\hat { Q } = \{ ( \mathbf { x } _ { i } ^ { t } , \mathbf { v } _ { i } ^ { t } ) \} _ { i = 1 } ^ { n _ { t } }$ . To learn features in both real part and imaginary part of complex frequency data, we adopt a complex-valued linear layer as the frequency feature extractor $\psi _ { F }$ . Since the phase generally does not provide strong discriminative information, we only retain the amplitudes of each frequency to construct the frequency domain feature $\mathbf { z } _ { i } \mathbf { . }$

$$
\mathbf {z} _ {i} = \operatorname{Amp} \left(\psi_ {F} (\mathbf {v} _ {i})\right),\tag{4}
$$

where $\mathbf { A } \mathbf { m } \mathbf { p } ( \cdot )$ denotes the calculation of amplitude values. For multivariate time series, we convert $\mathbf { v } _ { i }$ into a single-channel vector by concatenating across different variates.

## 4.2 Temporal-frequency domain mutual learning

Discriminability and transferability are two key criteria that characterize the goodness of feature representations to enable domain adaptation. In Section 3, we reveal that the frequency features are more discriminative within the source domain, while the temporal features are more transferable across domains. Based on this discovery, we propose temporal-frequency domain mutual learning, aiming to leverage the respective advantages of the temporal domain and frequency domain.

The essence of domain mutual learning relies on how to transfer knowledge between the temporal domain and frequency domain. Inspired by model distillation, where the knowledge is transferred by matching the predictions between the teacher and student via the Kullback Leibler (KL) divergence [17], we focus mutual learning on the alignment between the temporal predictions and the frequency predictions. The KL divergence between two predictions $p _ { 1 }$ and $p _ { 2 }$ is formulated as:

$$
D _ {K L} (p _ {1} | | p _ {2}) = \sum_ {m = 1} ^ {C} p _ {1} ^ {m} \log \frac {p _ {1} ^ {m}}{p _ {2} ^ {m}}.\tag{5}
$$

The KL divergence is asymmetric, that is, $D _ { K L } ( p _ { 1 } | | p _ { 2 } )$ emphasizes aligning $p _ { 2 }$ to $p _ { 1 }$ , while $D _ { K L } ( p _ { 2 } | | p _ { 1 } )$ emphasizes aligning $p _ { 1 } \ t 0 \ p _ { 2 }$ . Based on the asymmetry, we use different alignment strategies in the source domain and target domain. Specifically, in the source domain, the frequency model serves as a more discriminative teacher, helping the temporal model make more accurate predictions; conversely, in the target domain, the temporal model acts as a more transferable teacher, assisting the frequency model in learning domain-invariant representations. We achieve temporalfrequency domain mutual learning by minimizing the KL Divergence. Formally, domain mutual learning is formulated as:

$$
\begin{array}{r l} & {\mathcal {L} _ {M _ {s}} (\psi_ {T}, g _ {T}) = \mathbb {E} _ {(\mathbf {x} _ {i} ^ {s}, \mathbf {v} _ {i} ^ {s}) \sim \hat {P}} [ D _ {K L} (\hat {\mathbf {y}} _ {F} ^ {s} | | \hat {\mathbf {y}} _ {T} ^ {s}) ],} \\ & {\mathcal {L} _ {M _ {t}} (\psi_ {F}, g _ {F}) = \mathbb {E} _ {(\mathbf {x} _ {i} ^ {t}, \mathbf {v} _ {i} ^ {t}) \sim \hat {Q}} [ D _ {K L} (\hat {\mathbf {y}} _ {T} ^ {t} | | \hat {\mathbf {y}} _ {F} ^ {t}) ],} \end{array}\tag{6}
$$

where $\hat { \mathbf { y } } _ { F } ^ { s }$ and $\hat { \mathbf { y } } _ { T } ^ { s }$ refer to the frequency prediction and temporal prediction in the source domain respectively; while $\hat { \mathbf { y } } _ { F } ^ { t }$ and $\hat { \bf y } _ { T } ^ { t }$ refer to the frequency prediction and temporal prediction in the target domain respectively. By aligning $\hat { \mathbf { y } } _ { T } ^ { s }$ to ${ \hat { \mathbf { y } } } _ { F } ^ { s } .$ , the training of the temporal feature extractor and classifier is guided with more discriminative information; by aligning $\hat { \bf y } _ { F } ^ { t }$ to $\hat { \mathbf { y } } _ { T } ^ { t }$ , the transferable knowledge contained in the temporal features is transferred to frequency domain.

## 4.3 Domain adversarial learning in temporal-frequency correlation subspace

Domain adversarial learning [13] is one of the most popular transferable representation learning methods, and it can be employed to learn transferable representation in time series. The key to the effectiveness of the method lies in how to fully utilize two types of features to learn transferable representations. Given time series in temporal domain and frequency domain, domain adversarial learning can be formulated as a minimax optimization problem with three competitive loss terms: (a) ${ \mathcal { L } } _ { C _ { T } }$ on the temporal feature extractor $\psi _ { T }$ and classifier $g _ { T }$ , which is minimized to guarantee lower source risk of the temporal classifier; (b) $\mathcal { L } _ { C _ { F } }$ on the frequency feature extractor $\psi _ { F }$ and classifier $g _ { F }$ , which is minimized to guarantee lower source risk of the frequency classifier; $\left( \mathrm { c } \right) \mathcal { L } _ { D }$ on the temporal feature extractor $\psi _ { T }$ , the frequency feature extractor $\psi _ { F }$ and the domain discriminator $g _ { D }$ which is minimized over $g _ { D }$ but maximized over $\psi _ { T }$ and $\psi _ { F } ;$

$$
\begin{array}{r l} & {\mathcal {L} _ {C _ {T}} (\psi_ {T}, g _ {T}) = \mathbb {E} _ {(\mathbf {x} _ {i} ^ {s}, \mathbf {y} _ {i} ^ {s}) \sim \hat {P}} [ \ell (g _ {T} (\psi_ {T} (\mathbf {x} _ {i} ^ {s})), \mathbf {y} _ {i} ^ {s}) ],} \\ & {\mathcal {L} _ {C _ {F}} (\psi_ {F}, g _ {F}) = \mathbb {E} _ {(\mathbf {v} _ {i} ^ {s}, \mathbf {y} _ {i} ^ {s}) \sim \hat {P}} [ \ell (g _ {F} (\psi_ {F} (\mathbf {v} _ {i} ^ {s})), \mathbf {y} _ {i} ^ {s}) ],} \\ & {\mathcal {L} _ {D} (\psi_ {T}, \psi_ {F}, g _ {D}) = - \mathbb {E} _ {(\mathbf {x} _ {i} ^ {s}, \mathbf {v} _ {i} ^ {s}) \sim \hat {P}} \mathrm{log} [ g _ {D} (\psi_ {T} (\mathbf {x} _ {i} ^ {s}), \psi_ {F} (\mathbf {v} _ {i} ^ {s})) ]} \\ & {- \mathbb {E} _ {(\mathbf {x} _ {i} ^ {t}, \mathbf {v} _ {i} ^ {t}) \sim \hat {Q}} \mathrm{log} [ 1 - g _ {D} (\psi_ {T} (\mathbf {x} _ {i} ^ {t}), \psi_ {F} (\mathbf {v} _ {i} ^ {t})) ],} \end{array}\tag{7}
$$

where ℓ denotes cross-entropy loss. Different from standard domain adversarial learning, where there is only one type of feature, domain adversarial learning in time series needs to consider the temporal features and frequency features simultaneously. A simple strategy is to concatenate the temporal feature f and the frequency feature z. However, with the concatenation strategy, the adversarial game between the domain discriminator and the feature extractors can be viewed as two independent components: the game between $g _ { D }$ and $\psi _ { T }$ and the game between $g _ { D }$ and $\psi _ { F }$ . With the worse transferability, z provides $g _ { D }$ with rich domain-label relevant information. In this case, $g _ { D }$ only needs to focus on the game with $\psi _ { F }$ , ignoring the domain adversarial learning in the temporal domain.

To achieve co-alignment in the temporal domain and frequency domain, we propose domain adversarial learning in temporal-frequency correlation subspace. The temporal-frequency correlation subspace not only possesses statistical characteristics of the original temporal feature subspace and original frequency feature subspace but also reflects the correlation between temporal features and frequency features. Reducing the discrepancy of the temporal-frequency correlation subspace not only reduces the discrepancy in the cross-domain temporal and frequency features but also decreases the differences in cross-domain temporal-frequency correlations.

Formally, the vectors in temporal-frequency correlation subspace can be calculated as the outer product  between the temporal feature f and the frequency feature z:

$$
\mathbf {f} \otimes \mathbf {z} = [ \mathbf {z} [ 1 ] \cdot \mathbf {f}, \mathbf {z} [ 2 ] \cdot \mathbf {f}, \dots , \mathbf {z} [ l ] \cdot \mathbf {f} ],\tag{8}
$$

where $\mathbf { z } \in \mathbb { R } ^ { 1 \times l }$ . By adjusting the order of dimensions, $\mathbf { z } \otimes \mathbf { f }$ is equivalent to $\mathbf { f } \otimes \mathbf { z } .$ . Considering the sparsity of the frequency domain and the modeling of long-length time series, the direct outer product leads to dimension explosion and the sparsity in temporal-frequency feature subspace. We address the problem by performing average pooling over z. Average pooling, which calculates the average value for the amplitudes of neighboring frequencies, yields dense frequency features with smaller dimensions. With outer product and average pooling, the adversarial loss $\mathcal { L } _ { D }$ is formulated as:

$$
\begin{array}{c} h (\mathbf {x} _ {i}, \mathbf {v} _ {i}) = \psi_ {T} (\mathbf {x} _ {i}) \otimes \mathbf {P} (\psi_ {F} (\mathbf {v} _ {i})), \\ \mathcal {L} _ {D} (\psi_ {T}, \psi_ {F}, g _ {D}) = - \mathbb {E} _ {(\mathbf {x} _ {i} ^ {s}, \mathbf {v} _ {i} ^ {s}) \sim \hat {P}} \mathrm{log} [ g _ {D} (h (\mathbf {x} _ {i} ^ {s}, \mathbf {v} _ {i} ^ {s})) ] - \mathbb {E} _ {(\mathbf {x} _ {i} ^ {t}, \mathbf {v} _ {i} ^ {t}) \sim \hat {Q}} \mathrm{log} [ 1 - g _ {D} (h (\mathbf {x} _ {i} ^ {t}, \mathbf {v} _ {i} ^ {t})) ], \end{array}\tag{9}
$$

where $h ( \cdot )$ denotes the mapping from the inputs of the overall model to the inputs of the domain discriminator, and $\mathrm { ~ P ~ } ( \cdot )$ denotes the calculation of average pooling.

## 4.4 Overview

During alignment, our method trains the temporal feature extractor ψ<sub>T</sub> and classifier $g _ { T }$ by minimizing the loss ${ \mathcal { L } } _ { C _ { \mathrm { { 7 } } } }$ and trains the frequency feature extractor $\psi _ { F }$ and classifier $g _ { F }$ by minimizing the loss $\mathcal { L } _ { C _ { F } }$ using the source sample set ${ \hat { P } } .$ . Additionally, our method promotes mutual learning between the temporal domain and frequency domain by minimizing the loss $\mathcal { L } _ { M _ { s } }$ on the source domain and the loss $\mathcal { L } _ { M _ { t } }$ on the target domain. Meanwhile, our method aligns distributions of the source domain and target domain in the temporal-frequency correlation subspace. With two gradient reversal layers between the two feature extractors and the domain discriminator, the adversarial training is achieved by minimizing the loss $\mathcal { L } _ { D }$ . To simplify notation, we denote $\theta _ { F }$ as parameters containing ψ and $g _ { F }$ and $\theta _ { T }$ is parameters containing ψ and $g _ { T }$ . The minimax optimization problem is formulated as:

$$
\begin{array}{l} \min _ {\theta_ {F}, \theta_ {T}} \mathcal {L} _ {C _ {F}} (\theta_ {F}) + \mathcal {L} _ {C _ {T}} (\theta_ {T}) + \mathcal {L} _ {M _ {s}} (\theta_ {T}) + \mathcal {L} _ {M _ {t}} (\theta_ {F}) - \mathcal {L} _ {D} (\psi_ {T}, \psi_ {F}, g _ {D}), \\ \min _ {g _ {D}} \mathcal {L} _ {D} (\psi_ {T}, \psi_ {F}, g _ {D}). \end{array}\tag{10}
$$

## 5 Experiments

## 5.1 Setup

Datasets We conduct extensive experiments using a wide range of time series datasets. (1) Experiments using benchmark datasets in sensor-based human activity recognition (HAR) task: UCIHAR [1], HHAR [35] and WISDM[20]. For HHAR, we first split domains from the perspective of participants, denoted as HHAR-P [16, 31] dataset. Then, we split domains from the perspective of devices, denoted as HHAR-D [12] datasets. (2) Experiments using the benchmark dataset in sleep stage classification (SSC) task: CAP [14, 37]. (3) Experiments using EMG [24, 27] dataset in gesture recognition (GR) task. (4) Experiments using PCL [32, 9, 21, 19] dataset in motor imagery classification (MIC) task. (5) Experiments using FD [31] dataset in machine fault diagnosis (MFD) task. For each dataset, following the existing DA methods on time series [2, 16], we randomly sample 10 source-target domain pairs for evaluation. If the dataset has less than 10 pairs, we evaluate all available domain pairs. Further details, processing and domain splits are included in Appendix A.

Baselines (1) We report the performance of a model without UDA (Source-only) in the temporal domain to show the overall contribution of UDA methods. (2) We implement the following stateof-the-art baselines for UDA of time series data: CODATS[41], AdvSKM[23], CLUDA[29] and RAINCOAT[16]. (3) We additionally implement general unsupervised DA methods: CDAN [26], DeepCoral [36], AdaMatch [2], HoMM [5] and DIRT-T [34].

Evaluation We report accuracy and Macro-F1 Score calculated using target test datasets. Accuracy is computed by dividing the number of correctly classified samples by the total number of samples. Macro-F1 Score is calculated using the unweighted mean of all the per-class F1 scores.

Implementation We adopt the implementation of AdaTime [31] as a benchmarking suite for domain adaptation on time series data, using 1D-CNN as the temporal feature extractor and 1-lyer complex-valued linear as the frequency feature extractor. We use the same feature extractor across all algorithms, ensuring a fair comparison. In all experiments, we use the prediction of the temporal classifier to calculate accuracy and Macro-F1 Score. More experimental details are provided in Appendix B.

Table 1: Average Accuracy (%) on Eight Datasets and Five Applications for UDA.

<table><tr><td>Task</td><td>GR</td><td>MFD</td><td>MI</td><td colspan="4">HAR</td><td>SSC</td></tr><tr><td>Dataset</td><td>EMG</td><td>FD</td><td>PCL</td><td>UCIHAR</td><td>HHAR-P</td><td>WISDM</td><td>HHAR-D</td><td>CAP</td></tr><tr><td>Source-only</td><td>76.24</td><td>70.04</td><td>60.95</td><td>75.12</td><td>54.25</td><td>65.78</td><td>46.82</td><td>55.86</td></tr><tr><td>CDAN</td><td>79.89</td><td> $\underline{90.56}$ </td><td>63.36</td><td>85.78</td><td>68.73</td><td>70.05</td><td>54.94</td><td>67.33</td></tr><tr><td>DeepCoral</td><td>78.71</td><td>84.10</td><td>63.51</td><td>82.01</td><td>68.03</td><td>70.80</td><td>52.55</td><td>64.88</td></tr><tr><td>AdaMatch</td><td> $\underline{80.69}$ </td><td>82.11</td><td>57.78</td><td>76.07</td><td>65.91</td><td>69.79</td><td>53.84</td><td>65.12</td></tr><tr><td>HoMM</td><td> $\underline{78.74}$ </td><td>85.72</td><td>63.83</td><td>80.99</td><td>65.01</td><td>67.26</td><td>52.33</td><td>65.67</td></tr><tr><td>DIRT-T</td><td>79.27</td><td>88.08</td><td>61.02</td><td>83.26</td><td>64.99</td><td>69.62</td><td> $\underline{56.14}$ </td><td> $\underline{70.42}$ </td></tr><tr><td>CLUDA</td><td>75.62</td><td>84.99</td><td>54.69</td><td>85.53</td><td>68.73</td><td>67.04</td><td>53.84</td><td>65.79</td></tr><tr><td>AdvSKM</td><td>78.81</td><td>83.37</td><td>63.58</td><td>83.26</td><td>66.41</td><td>66.97</td><td>52.80</td><td>64.39</td></tr><tr><td>CoDATS</td><td>80.60</td><td>87.20</td><td> $\underline{64.18}$ </td><td>75.54</td><td>68.71</td><td>70.66</td><td>56.27</td><td>68.23</td></tr><tr><td>RAINCOAT</td><td>79.93</td><td>86.75</td><td>58.99</td><td> $\underline{94.43}$ </td><td> $\underline{74.21}$ </td><td> $\underline{76.60}$ </td><td>49.07</td><td>69.13</td></tr><tr><td>Ours</td><td>82.91</td><td>91.74</td><td>65.02</td><td>97.02</td><td>81.74</td><td>84.80</td><td>65.04</td><td>74.08</td></tr><tr><td>Improve(%)</td><td>2.75</td><td>1.30</td><td>1.31</td><td>2.74</td><td>10.15</td><td>10.70</td><td>15.85</td><td>5.20</td></tr></table>

## 5.2 Results

Table 1 shows the average accuracy of each method on all datasets and tasks. Overall, our method has won 5 out of 5 tasks and 8 out of 8 datasets (2 metrics). Specifically, our method improves accuracy by 2.75% on GR task, 5.20% on SSC task, 1.31% on MI task, 9.86% on HAR task and 1.30% on MFD task over the advanced baseline on each dataset respectively.

Due to the limited pages, we report the results for selected source-target domain pairs with metric accuracy on the representative datasets EMG (GR task), CAP (SSC task) and HHAR-P (HAR task). More accuracy results are given in Table 11-15. Average macro-f1 score results are given in Table 16. Full macro-f1 score results are given in Table 17-24.

Table 2: Accuracy (%) on CAP for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→1</td><td>0→3</td><td>0→4</td><td>1→0</td><td>1→4</td><td>2→3</td><td>3→0</td><td>3→1</td><td>4→1</td><td>4→3</td><td>Avg</td></tr><tr><td>Source-only</td><td>42.44</td><td>75.75</td><td>66.09</td><td>57.98</td><td>63.26</td><td>50.75</td><td>69.47</td><td>26.88</td><td>33.90</td><td>72.09</td><td>55.86</td></tr><tr><td>CDAN</td><td>68.04</td><td>77.47</td><td>72.84</td><td>62.66</td><td>67.29</td><td>53.93</td><td>72.64</td><td>63.58</td><td>58.17</td><td>76.63</td><td>67.33</td></tr><tr><td>DeepCoral</td><td>67.44</td><td>77.34</td><td>72.33</td><td>59.18</td><td>67.71</td><td>58.09</td><td>70.66</td><td>53.02</td><td>49.12</td><td>73.94</td><td>64.88</td></tr><tr><td>AdaMatch</td><td>60.28</td><td>77.67</td><td>75.55</td><td>68.90</td><td>63.17</td><td>37.33</td><td>73.52</td><td>59.29</td><td>60.26</td><td>75.22</td><td>65.12</td></tr><tr><td>HoMM</td><td>69.89</td><td>77.11</td><td>72.27</td><td>60.36</td><td>67.89</td><td>57.96</td><td>71.58</td><td>57.61</td><td>47.52</td><td>74.49</td><td>65.67</td></tr><tr><td>DIRT-T</td><td>72.16</td><td>79.21</td><td>76.04</td><td>64.18</td><td>68.69</td><td>57.75</td><td>75.47</td><td>69.91</td><td>64.59</td><td>76.16</td><td>70.42</td></tr><tr><td>CLUDA</td><td>67.67</td><td>75.77</td><td>58.82</td><td>70.31</td><td>70.23</td><td>53.94</td><td>74.91</td><td>53.62</td><td>58.30</td><td>74.29</td><td>65.79</td></tr><tr><td>AdvSKM</td><td>63.88</td><td>77.04</td><td>72.17</td><td>60.61</td><td>66.09</td><td>58.00</td><td>70.93</td><td>55.26</td><td>46.64</td><td>73.32</td><td>64.39</td></tr><tr><td>CoDATS</td><td>70.54</td><td>78.64</td><td>70.40</td><td>67.89</td><td>72.05</td><td>57.32</td><td>76.08</td><td>53.79</td><td>60.43</td><td>75.17</td><td>68.23</td></tr><tr><td>RAINCOAT</td><td>70.58</td><td>72.80</td><td>73.47</td><td>65.34</td><td>69.62</td><td>56.08</td><td>71.34</td><td>70.86</td><td>70.47</td><td>70.70</td><td>69.13</td></tr><tr><td>Ours</td><td>75.32</td><td>80.14</td><td>76.58</td><td>70.68</td><td>73.25</td><td>57.48</td><td>77.75</td><td>75.17</td><td>75.67</td><td>78.74</td><td>74.08</td></tr></table>

Table 2 presents the results on CAP dataset. CAP contains over 40,000 samples of 3000 time steps, so adaptation on it is more challenging. Our method outperforms general DA and time series DA methods on 9 out of 10 source-target domain pairs, achieving an average improvement of 5.20% over the advanced baseline, DIRT-T. Table 3 presents the results on HHAR-P dataset. Our method significantly outperforms RAINCOAT, the state-of-the-art DA method for time series, by 10.15%.

Table 3: Accuracy (%) on HHAR-P for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→2</td><td>1→6</td><td>2→4</td><td>4→0</td><td>4→5</td><td>5→1</td><td>5→2</td><td>7→2</td><td>7→5</td><td>8→4</td><td>Avg</td></tr><tr><td>Source-only</td><td>64.51</td><td>70.63</td><td>45.42</td><td>32.81</td><td>78.32</td><td>90.63</td><td>25.67</td><td>32.37</td><td>39.26</td><td>62.92</td><td>54.25</td></tr><tr><td>CDAN</td><td>76.19</td><td>92.57</td><td>52.57</td><td>29.09</td><td>97.27</td><td>96.16</td><td>35.04</td><td>37.05</td><td>75.26</td><td>96.11</td><td>68.73</td></tr><tr><td>DeepCoral</td><td>84.23</td><td>90.14</td><td>47.08</td><td>28.13</td><td>90.49</td><td>89.91</td><td>38.39</td><td>34.45</td><td>55.73</td><td>76.88</td><td>68.03</td></tr><tr><td>AdaMatch</td><td>84.78</td><td>92.31</td><td>54.50</td><td>36.45</td><td>78.45</td><td>94.20</td><td>41.96</td><td>37.65</td><td>63.80</td><td>64.69</td><td>65.91</td></tr><tr><td>HoMM</td><td>75.67</td><td>90.79</td><td>52.83</td><td>36.61</td><td>87.66</td><td>90.78</td><td>37.23</td><td>37.32</td><td>61.29</td><td>79.88</td><td>65.01</td></tr><tr><td>DIRT-T</td><td>77.83</td><td>88.54</td><td>50.69</td><td>32.22</td><td>93.16</td><td>91.86</td><td>38.62</td><td>38.10</td><td>72.46</td><td>65.83</td><td>64.99</td></tr><tr><td>CLUDA</td><td>79.84</td><td>93.40</td><td>45.90</td><td>38.84</td><td>94.08</td><td>95.57</td><td>33.93</td><td>37.80</td><td>77.57</td><td> $\underline{96.52}$ </td><td>69.35</td></tr><tr><td>AdvSKM</td><td>78.94</td><td>87.91</td><td>52.57</td><td>33.49</td><td>92.64</td><td>92.71</td><td>36.53</td><td>39.95</td><td>65.49</td><td> $\underline{83.75}$ </td><td>66.41</td></tr><tr><td>CoDATS</td><td>79.61</td><td>90.90</td><td>60.07</td><td>21.80</td><td>97.66</td><td>97.66</td><td>41.44</td><td>38.54</td><td>58.15</td><td> $\underline{97.01}$ </td><td>68.71</td></tr><tr><td>RAINCOAT</td><td> $\underline{87.72}$ </td><td> $\underline{93.33}$ </td><td> $\underline{63.75}$ </td><td>46.46</td><td> $\underline{98.05}$ </td><td> $\underline{98.25}$ </td><td> $\underline{42.63}$ </td><td> $\underline{43.32}$ </td><td> $\underline{84.17}$ </td><td>93.75</td><td> $\underline{74.21}$ </td></tr><tr><td>Ours</td><td> $\underline{86.65}$ </td><td>93.45</td><td>79.01</td><td>53.53</td><td> $\underline{97.15}$ </td><td>98.32</td><td>65.80</td><td>65.71</td><td>88.59</td><td>89.17</td><td>81.74</td></tr></table>

Table 4: Ablation studies: Average Accuracy (%) on UCIHAR, HHAR-P and WISDM.

<table><tr><td></td><td> $\mathcal{L}_{CT}$ </td><td> $\mathcal{L}_{CF}$ </td><td>Period</td><td> $\mathcal{L}_{Ms}$ </td><td> $\mathcal{L}_{Mt}$ </td><td> $\mathcal{L}_D$ </td><td>UCIHAR</td><td>HHAR-P</td><td>WISDM</td><td>Average</td></tr><tr><td>1</td><td>√</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>75.12</td><td>54.25</td><td>65.78</td><td>65.05</td></tr><tr><td>2</td><td>-</td><td>√</td><td>-</td><td>-</td><td>-</td><td>-</td><td>66.88</td><td>51.08</td><td>56.47</td><td>58.14</td></tr><tr><td>3</td><td>-</td><td>√</td><td>√</td><td>-</td><td>-</td><td>-</td><td>73.47</td><td>53.16</td><td>59.10</td><td>61.91</td></tr><tr><td>4</td><td>√</td><td>√</td><td>√</td><td>-</td><td>-</td><td>√</td><td>94.05</td><td>79.49</td><td>74.19</td><td>82.58</td></tr><tr><td>5</td><td>√</td><td>√</td><td>√</td><td>√</td><td>√</td><td>-</td><td>90.83</td><td>57.83</td><td>67.77</td><td>72.14</td></tr><tr><td>6</td><td>√</td><td>√</td><td>√</td><td>√</td><td>√</td><td>√</td><td>97.02</td><td>81.74</td><td>84.80</td><td>87.85</td></tr></table>

## 5.3 Analysis

Ablation Study We conduct ablation experiments on three datasets, UCIHAR, HHAR-P and WISDM. For each datasets, we select the same 10 source-target domain pairs as mentioned in Section 5.1. The ablation results (average accuracy of 10 domain pairs) are presented in Table 4. We can observe that all learning modules in the proposed method are effective. Further discussions are included in Appendix C.3.

![](images/a0b67c1fb40b21d0758c350d0832f2b2fb33beebe38d52daefc929811495760f.jpg)

![](images/53396b9505e7fe514001602b7f95bd26b78b8dbd86209550d8e508d4cf0bf6c9.jpg)

![](images/bf469646a7a682aab5e4bf50379aa310092e14a4f334f0631d2111b4b95d4c9b.jpg)  
(a) Sensitivity analysis on UCIHAR (b) Sensitivity analysis on HHAR (c) Sensitivity analysis on WISDM  
Figure 3: Sensitivity Analysis on three different datasets: (a) UCIHAR (b) HHAR-P (c) WISDM. RAINCOAT: The advanced baseline that achieves suboptimal performance on the three datasets.

Sensitivity Analysis It’s worth noting that our total loss in Equation (10) does not include any hyperparameters. In UDA setup, how to search the optimal trade-offs without access to labeled target samples is still an open problem. Considering that, we choose to set all the trade-offs to 1, as it is the most intuitive choice. Without tuning the trade-offs, our proposed ACON still achieves significant improvements. To further investigate the sensitivity of ACON, we update Equation (10) as:

$$
\begin{array}{l} \min _ {\theta_ {F}, \theta_ {T}} \mathcal {L} _ {C _ {F}} (\theta_ {F}) + \mathcal {L} _ {C _ {T}} (\theta_ {T}) + \lambda_ {M _ {s}} \mathcal {L} _ {M _ {s}} (\theta_ {T}) + \lambda_ {M _ {t}} \mathcal {L} _ {M _ {t}} (\theta_ {F}) - \lambda_ {D} \mathcal {L} _ {D} (\psi_ {T}, \psi_ {F}, g _ {D}), \\ \min _ {g _ {D}} \lambda_ {D} \mathcal {L} _ {D} (\psi_ {T}, \psi_ {F}, g _ {D}), \end{array}\tag{11}
$$

where hyperparameters $\lambda _ { D } , \lambda _ { M _ { s } }$ and $\lambda _ { M _ { t } }$ control the contribution of each component. We investigate the sensitivity of the model to the hyperparameters $\lambda _ { D } , \lambda _ { M _ { s } }$ and $\lambda _ { M _ { t } } . \ \mathrm { A C O N } { - } \lambda _ { D }$ refers that the currently investigated hyperparameter is $\lambda _ { D }$ , and others are analogous. From Figure 3, we observe that the performance of ACON is quite stable to the hyperparameters in Equation (11). Although setting all the trade-offs to 1 may not achieve the optimal performance, ACON still significantly outperforms the advanced baseline. This implies that ACON can achieve superior performance on a wider range of datasets without the need for careful hyperparameter tuning.

## 6 Conclusion

In this paper, the phenomenon is revealed——that temporal features exhibit better transferability across domains, whereas frequency features tend to be more discriminative within a specific domain. Based on the findings, Adversarial CO-learning Networks (ACON) is proposed to boost the transferability and discriminability in a collaborative learning manner. Specifically, multi-period feature learning is proposed to enhance the discriminability of frequency features; temporal-frequency domain mutual learning is proposed to enhance the discriminability of temporal features in the source domain and improve the transferability of frequency features in the target domain; domain adversarial learning in temporal-frequency correlation subspace is proposed to further enhance transferability of features. ACON achieves state-of-the-art performance on a wide range of time series datasets.

## Acknowledgements

This work was supported by the National Natural Science Foundation of China (62306085, 62206074, 62406112, 62476071, 62236003), Shenzhen College Stability Support Plan (GXWD20231130151329002, GXWD20220811173233001, GXWD20220817144428005).

## References

[1] Davide Anguita, Alessandro Ghio, Luca Oneto, Xavier Parra, Jorge Luis Reyes-Ortiz, et al. A public domain dataset for human activity recognition using smartphones. In Esann, 2013.

[2] David Berthelot, Rebecca Roelofs, Kihyuk Sohn, Nicholas Carlini, and Alexey Kurakin. Adamatch: A unified approach to semi-supervised learning and domain adaptation. In ICLR, 2021.

[3] Ruichu Cai, Jiawei Chen, Zijian Li, Wei Chen, Keli Zhang, Junjian Ye, Zhuozhang Li, Xiaoyan Yang, and Zhenjie Zhang. Time series domain adaptation via sparse associative structure alignment. In AAAI, 2021.

[4] Chris Chatfield and Haipeng Xing. The analysis of time series: an introduction with R. 1981.

[5] Chao Chen, Zhihang Fu, Zhihong Chen, Sheng Jin, Zhaowei Cheng, Xinyu Jin, and Xian-Sheng Hua. Homm: Higher-order moment matching for unsupervised domain adaptation. In AAAI, 2020.

[6] Chaoqi Chen, Weiping Xie, Wenbing Huang, Yu Rong, Xinghao Ding, Yue Huang, Tingyang Xu, and Junzhou Huang. Progressive feature alignment for unsupervised domain adaptation. In CVPR, 2019.

[7] Xinyang Chen, Sinan Wang, Mingsheng Long, and Jianmin Wang. Transferability vs. discriminability: Batch spectral penalization for adversarial domain adaptation. In ICML, 2019.

[8] Xinyang Chen, Sinan Wang, Jianmin Wang, and Mingsheng Long. Representation subspace distance for domain adaptation regression. In ICML, 2021.

[9] Hohyun Cho, Minkyu Ahn, Sangtae Ahn, Moonyoung Kwon, and Sung Chan Jun. Eeg datasets for motor imagery brain–computer interface. GigaScience, 2017.

[10] Junyoung Chung, Kyle Kastner, Laurent Dinh, Kratarth Goel, Aaron C Courville, and Yoshua Bengio. A recurrent latent variable model for sequential data. In NeurIPS, 2015.

[11] Jean-Christophe Gagnon-Audet, Kartik Ahuja, Mohammad Javad Darvishi Bayazi, Pooneh Mousavi, Guillaume Dumas, and Irina Rish. Woods: Benchmarks for out-of-distribution generalization in time series. TMLR.

[12] Jean-Christophe Gagnon-Audet, Kartik Ahuja, Mohammad Javad Darvishi Bayazi, Pooneh Mousavi, Guillaume Dumas, and Irina Rish. Woods: Benchmarks for out-of-distribution generalization in time series. TMLR, 2023.

[13] Yaroslav Ganin, Evgeniya Ustinova, Hana Ajakan, Pascal Germain, Hugo Larochelle, François Laviolette, Mario March, and Victor Lempitsky. Domain-adversarial training of neural networks. JMLR, 2016.

[14] Ary L Goldberger, Luis AN Amaral, Leon Glass, Jeffrey M Hausdorff, Plamen Ch Ivanov, Roger G Mark, Joseph E Mietus, George B Moody, Chung-Kang Peng, and H Eugene Stanley. Physiobank, physiotoolkit, and physionet: components of a new research resource for complex physiologic signals. Circulation, 2000.

[15] Xiaoqing Guo, Chen Yang, Baopu Li, and Yixuan Yuan. Metacorrection: Domain-aware meta loss correction for unsupervised domain adaptation in semantic segmentation. In CVPR, 2021.

[16] Huan He, Owen Queen, Teddy Koker, Consuelo Cuevas, Theodoros Tsiligkaridis, and Marinka Zitnik. Domain adaptation for time series under feature and label shifts. In ICML, 2023.

[17] Geoffrey Hinton, Oriol Vinyals, and Jeff Dean. Distilling the knowledge in a neural network. In NeurIPS Deep Learning Workshop, 2014.

[18] Hassan Ismail Fawaz, Germain Forestier, Jonathan Weber, Lhassane Idoumghar, and Pierre-Alain Muller. Deep learning for time series classification: a review. Data mining and knowledge discovery, 2019.

[19] Vinay Jayaram and Alexandre Barachant. Moabb: trustworthy algorithm benchmarking for bcis. Journal ofneural engineering, 2018.

[20] Jennifer R Kwapisz, Gary M Weiss, and Samuel A Moore. Activity recognition using cell phone accelerometers. ACM SIGKDD, 2011.

[21] Min-Ho Lee, O-Yeon Kwon, Yong-Jeong Kim, Hong-Kyung Kim, Young-Eun Lee, John Williamson, Siamac Fazli, and Seong-Whan Lee. Eeg dataset and openbmi toolbox for three bci paradigms: An investigation into bci illiteracy. GigaScience, 2019.

[22] Hong Liu, Jianmin Wang, and Mingsheng Long. Cycle self-training for domain adaptation. In NeurIPS, 2021.

[23] Qiao Liu and Hui Xue. Adversarial spectral kernel matching for unsupervised time series domain adaptation. In IJCAI, 2021.

[24] Sergey Lobov, Nadia Krilova, Innokentiy Kastalskiy, Victor Kazantsev, and Valeri A. Makarov. Latent factors limiting the performance of semg-interfaces. Sensors, 2018.

[25] Mingsheng Long, Yue Cao, Jianmin Wang, and Michael Jordan. Learning transferable features with deep adaptation networks. In ICML, 2015.

[26] Mingsheng Long, Zhangjie Cao, Jianmin Wang, and Michael I Jordan. Conditional adversarial domain adaptation. In NeurIPS, 2018.

[27] Wang Lu, Jindong Wang, Xinwei Sun, Yiqiang Chen, and Xing Xie. Out-of-distribution representation learning for time series classification. In ICLR, 2022.

[28] Wang Lu, Jindong Wang, Xinwei Sun, Yiqiang Chen, and Xing Xie. Out-of-distribution representation learning for time series classification. In ICLR, 2023.

[29] Yilmazcan Ozyurt, Stefan Feuerriegel, and Ce Zhang. Contrastive learning for unsupervised domain adaptation of time series. In ICLR, 2022.

[30] Sanjay Purushotham, Wilka Carvalho, Tanachat Nilanon, and Yan Liu. Variational recurrent adversarial deep domain adaptation. In ICLR, 2017.

[31] Mohamed Ragab, Emadeldeen Eldele, Wee Ling Tan, Chuan-Sheng Foo, Zhenghua Chen, Min Wu, Chee-Keong Kwoh, and Xiaoli Li. Adatime: A benchmarking suite for domain adaptation on time series data. ACM TKDD, 2023.

[32] Gerwin Schalk, Dennis J McFarland, Thilo Hinterberger, Niels Birbaumer, and Jonathan R Wolpaw. Bci2000: a general-purpose brain-computer interface (bci) system. IEEE Transactions on biomedical engineering, 2004.

[33] Xingjian Shi, Zhourong Chen, Hao Wang, Dit-Yan Yeung, Wai-Kin Wong, and Wang-chun Woo. Convolutional lstm network: A machine learning approach for precipitation nowcasting. In NeurIPS, 2015.

[34] Rui Shu, Hung Bui, Hirokazu Narui, and Stefano Ermon. A dirt-t approach to unsupervised domain adaptation. In ICLR, 2018.

[35] Allan Stisen, Henrik Blunck, Sourav Bhattacharya, Thor Siiger Prentow, Mikkel Baun Kjærgaard, Anind Dey, Tobias Sonne, and Mads Møller Jensen. Smart devices are different: Assessing and mitigatingmobile sensing heterogeneities for activity recognition. In ACM SenSys, 2015.

[36] Baochen Sun and Kate Saenko. Deep coral: Correlation alignment for deep domain adaptation. In ECCV, 2016.

[37] Mario Giovanni Terzano, Liborio Parrino, Adriano Sherieri, Ronald Chervin, Sudhansu Chokroverty, Christian Guilleminault, Max Hirshkowitz, Mark Mahowald, Harvey Moldofsky, Agostino Rosa, et al. Atlas, rules, and recording techniques for the scoring of cyclic alternating pattern (cap) in human sleep. Sleep medicine, 2001.

[38] Eric Tzeng, Judy Hoffman, Ning Zhang, Kate Saenko, and Trevor Darrell. Deep domain confusion: Maximizing for domain invariance. arXiv preprint arXiv:1412.3474, 2014.

[39] Rui Wang, Masao Utiyama, Andrew Finch, Lemao Liu, Kehai Chen, and Eiichiro Sumita. Sentence selection and weighting for neural machine translation domain adaptation. IEEE/ACM Transactions on Audio, Speech, and Language Processing, 2018.

[40] Rui Wang, Masao Utiyama, Lemao Liu, Kehai Chen, and Eiichiro Sumita. Instance weighting for neural machine translation domain adaptation. In EMNLP, 2017.

[41] Garrett Wilson, Janardhan Rao Doppa, and Diane J Cook. Multi-source deep domain adaptation with weak supervision for time-series sensor data. In KDD, 2020.

[42] Zhijian Xu, Ailing Zeng, and Qiang Xu. Fits: Modeling time series with 10k parameters. In ICLR, 2023.

[43] Kun Yi, Qi Zhang, Wei Fan, Shoujin Wang, Pengyang Wang, Hui He, Ning An, Defu Lian, Longbing Cao, and Zhendong Niu. Frequency-domain mlps are more effective learners in time series forecasting. In NeurIPS, 2023.

[44] Wangjie You, Pei Guo, Juntao Li, Kehai Chen, and Min Zhang. Efficient domain adaptation for non-autoregressive machine translation. In ACL, 2024.

[45] Tian Zhou, Ziqing Ma, Qingsong Wen, Xue Wang, Liang Sun, and Rong Jin. Fedformer: Frequency enhanced decomposed transformer for long-term series forecasting. In ICML, 2022.

[46] Yang Zou, Zhiding Yu, B.V.K. Vijaya Kumar, and Jinsong Wang. Unsupervised domain adaptation for semantic segmentation via class-balanced self-training. In ECCV, 2018.

## A Dataset

## A.1 Detailed Statistics

We conduct extensive experiments using a wide range of time series datasets. The detailed statistics for each dataset is included in Table 5. For EMG dataset, we use the processed version released by DIVERSIFY [28]. For PCL, CAP and HHAR-D datasets, we use the processed versions released by WOODS [11]. For UCIHAR, HHAR-P, WISDM and FD datasets, we use the processed versions released by AdaTime [31].

Table 5: Summary of datasets.

<table><tr><td>Dataset</td><td>Subjects</td><td>Channels</td><td>Length</td><td>Class</td><td>Total</td><td>Task</td></tr><tr><td>EMG</td><td>4</td><td>8</td><td>200</td><td>6</td><td>6883</td><td>GR</td></tr><tr><td>FD</td><td>4</td><td>1</td><td>5120</td><td>3</td><td>10916</td><td>FD</td></tr><tr><td>PCL</td><td>3</td><td>48</td><td>750</td><td>2</td><td>22598</td><td>MIC</td></tr><tr><td>CAP</td><td>5</td><td>19</td><td>3000</td><td>6</td><td>40387</td><td>SSC</td></tr><tr><td>UCIHAR</td><td>30</td><td>9</td><td>128</td><td>6</td><td>3290</td><td>HAR</td></tr><tr><td>HHAR-P</td><td>9</td><td>3</td><td>128</td><td>6</td><td>17934</td><td>HAR</td></tr><tr><td>WISDM</td><td>30</td><td>3</td><td>128</td><td>6</td><td>2070</td><td>HAR</td></tr><tr><td>HHAR-D</td><td>5</td><td>6</td><td>500</td><td>6</td><td>13674</td><td>HAR</td></tr></table>

## A.2 Dataset Processing

Each domain of datasets is randomly divided into 80% training, and 20% testing. We follow [31], apply Z-score normalization to both the training and testing splits of the data, using the following equation:

$$
x _ {i} ^ {\text { normalize }} = \frac {x _ {i} - x ^ {\text { mean }}}{x ^ {\text { std }}}, \quad i = 1, 2, \dots , N\tag{12}
$$

where $N = N _ { s }$ for the source domain data and $N = N _ { t }$ for the target domain data. Note that both the training and testing splits are normalized based on the training set statistics only.

## B Experimental Details

The experiments were conducted on a single NVIDIA GeForce696 RTX 4090 with 24GiB of memory. As shown in Figure 3, without tuning the trade-offs of training loss, ACON still achieves significant improvements. Here we report other key hyperparameters for ACON in Table 6. Additional hyperparameters can be found in our code. In all experiments, we adopt 3-layer 1D-CNN as the temporal feature extractor (the specific structure is kept consistent with the existing works [31, 16]). For frequency feature extraction, we adopt a 1-layer complex-valued linear as the frequency feature extractor.

Table 6: Key hyperparameters for ACON.

<table><tr><td>Hyperparameter</td><td>EMG</td><td>FD</td><td>PCL</td><td>CAP</td><td>UCIHAR</td><td>HHAR-P</td><td>WISDM</td><td>HHAR-D</td></tr><tr><td>Epoch</td><td>50</td><td>50</td><td>50</td><td>50</td><td>50</td><td>50</td><td>50</td><td>50</td></tr><tr><td>Batch Size</td><td>32</td><td>32</td><td>32</td><td>32</td><td>32</td><td>32</td><td>32</td><td>32</td></tr><tr><td>Learning Rate</td><td>0.001</td><td>0.01</td><td>0.001</td><td>0.001</td><td>0.01</td><td>0.001</td><td>0.003</td><td>0.01</td></tr></table>

## C Further Analysis

## C.1 Discriminability of Frequency Feature

In Table 7, we report the average accuracy of classification experiments under the setting of Section 3.2 using five different datasets: UCIAHR[1], HHAR-P[35], WISDM[20], CAP[14, 37] and FD[31]. For each dataset, we collect all the domains involved in the selected 10 domain pairs as mentioned in Section 5.1, and perform the classification task on them.

Table 7: Classification Accuracy (%) in the source domain: Temporal domain vs. Frequency domain.

<table><tr><td>Dataset</td><td>UCIHAR</td><td>HHAR-P</td><td>WISDM</td><td>CAP</td><td>FD</td></tr><tr><td>Temporal domain</td><td>86.18</td><td>97.01</td><td>95.63</td><td>81.63</td><td>97.99</td></tr><tr><td>Frequency domain</td><td>95.69</td><td>97.77</td><td>98.01</td><td>82.73</td><td>98.83</td></tr></table>

## C.2 Transferability of Temporal Feature

In Table 8, we report the average accuracy of classification experiments under the setting of Section 3.3 using three different datasets: UCIAHR[1], HHAR-P[35], WISDM[20], CAP[14, 37] and FD[31]. For each dataset, we perform the domain adaptation and classification task on the selected 10 domain pairs as mentioned in Section 5.1.

Table 8: Classification Accuracy (%) in the target domain: Temporal domain vs. Frequency domain.

<table><tr><td>Dataset</td><td>UCIHAR</td><td>HHAR-P</td><td>WISDM</td><td>CAP</td><td>FD</td></tr><tr><td>Source-only-T</td><td>75.12</td><td>54.25</td><td>65.78</td><td>70.14</td><td>70.04</td></tr><tr><td>Source-only-F</td><td>66.88</td><td>51.08</td><td>56.47</td><td>67.15</td><td>69.53</td></tr><tr><td>DANN-T</td><td>88.30</td><td>72.57</td><td>71.54</td><td>75.49</td><td>86.21</td></tr><tr><td>DANN-F</td><td>80.64</td><td>68.73</td><td>60.99</td><td>70.76</td><td>81.46</td></tr></table>

## C.3 Ablation Study

## C.3.1 Ablation Study on different modules

We conduct ablation experiments on three datasets, UCIHAR, HHAR-P and WISDM. For each datasets, we select the same 10 source-target domain pairs as mentioned in Section 5.1. The ablation results (average accuracy of 10 domain pairs) are presented in Table 9. We verify the effectiveness of all learning modules in the proposed method by answering the following questions.

Can multi-periodfrequencyfeature learning enhance the discriminability offrequencyfeature?By comparing the 2nd and 3rd rows, we can observe that with multi-period frequency feature learning, the model makes more accurate predictions on the target domain. Meanwhile, compared with 1st row, even with multi-period frequency feature learning, the performance on the target domain is still inferior to the classification on the temporal domain, which is consistent with our conclusion in Section 3.3 that the temporal features have better transferability.

Can aligning distributions in temporal-frequency subspace effectively learn domain-invariant features? By comparing the 1st, 3rd and 4th rows, we can observe that distribution alignment significantly improves the performance. It indicates that by aligning the distributions in the temporal frequency subspace, the model learns more domain-invariant features.

Can temporal-frequency domain mutual learning leverage the respective advantages? By compar ing the 1st, 3rd and 5th rows, we can observe that the model with domain mutual learning outperforms the model using only the temporal domain or only the frequency domain. It demonstrates that via domain mutual learning, the temporal domain and frequency domain successfully transfer meaningful knowledge, leveraging their respective advantages.

Can the different modules mutually promote each other? By comparing the 3rd, 4th, 5th and 6th rows, we can observe that with all modules, the model achieves the optimal performance. Specifically, with multi-period frequency feature learning, the frequency domain transfers more discriminative knowledge to the temporal domain; with aligning distribution in temporal-frequency subspace, the temporal domain transfers more transferable knowledge to the frequency domain; with aligning distribution in temporal-frequency subspace and the temporal domain as a more tranferbale teacher, both the temporal domain and frequency domain learn domain-invariant features; with domain mutual learning, the frequency domain and the temporal domain enhance each other in the transfer progress, achieving a synergistic effect.

Table 9: Ablation study on different modules: Average Accuracy (%) on UCIHAR, HHAR-P and WISDM.

<table><tr><td></td><td> $\mathcal{L}_{CT}$ </td><td> $\mathcal{L}_{CF}$ </td><td>Period</td><td> $\mathcal{L}_{Ms}$ </td><td> $\mathcal{L}_{Mt}$ </td><td> $\mathcal{L}_D$ </td><td>UCIHAR</td><td>HHAR-P</td><td>WISDM</td><td>Average</td></tr><tr><td>1</td><td>√</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>75.12</td><td>54.25</td><td>65.78</td><td>65.05</td></tr><tr><td>2</td><td>-</td><td>√</td><td>-</td><td>-</td><td>-</td><td>-</td><td>66.88</td><td>51.08</td><td>56.47</td><td>58.14</td></tr><tr><td>3</td><td>-</td><td>√</td><td>√</td><td>-</td><td>-</td><td>-</td><td>73.47</td><td>53.16</td><td>59.10</td><td>61.91</td></tr><tr><td>4</td><td>√</td><td>√</td><td>√</td><td>-</td><td>-</td><td>√</td><td>94.05</td><td>79.49</td><td>74.19</td><td>82.58</td></tr><tr><td>5</td><td>√</td><td>√</td><td>√</td><td>√</td><td>√</td><td>-</td><td>90.83</td><td>57.83</td><td>67.77</td><td>72.14</td></tr><tr><td>6</td><td>√</td><td>√</td><td>√</td><td>√</td><td>√</td><td>√</td><td>97.02</td><td>81.74</td><td>84.80</td><td>87.85</td></tr></table>

## D Limitations

Although ACON boosts transferability and discriminability for time series Domain adaptation, like existing DA methods, it is still unstable enough in time series with relatively large variances. This is a problem that needs to be solved urgently in the future.

## E Broader Impacts

We investigate how to boost Transferability and discriminability for domain adaptation in time series classification. We reveal that the frequency features are more discriminative, while the temporal features are more transferable. Upon this, we propose multi-period frequency feature learning, domain mutual learning, and distribution alignment in temporal-frequency feature subspace. The purpose of our research is to advance the research progress in the relevant community without any negative social impact.

## F Full Resluts

We present all experimental results in this section. Notably, our model achieves superior performance, yielding improvements of more than 6% in terms of accuracy and 4% in terms of Macro-F1 across 8 cross-domain time series datasets and 5 common applications on average.

Table 10: Accuracy (%) on EMG for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→1</td><td>0→2</td><td>0→3</td><td>1→2</td><td>1→3</td><td>2→0</td><td>2→1</td><td>2→3</td><td>3→1</td><td>3→2</td><td>Avg</td></tr><tr><td>Source-only</td><td>84.94</td><td>74.38</td><td>73.38</td><td>74.38</td><td>73.88</td><td>73.88</td><td>82.16</td><td>73.69</td><td>79.38</td><td>72.31</td><td>76.24</td></tr><tr><td>CDAN</td><td>87.84</td><td>76.63</td><td>77.63</td><td>77.44</td><td>81.63</td><td>73.94</td><td>87.10</td><td>75.13</td><td>83.98</td><td>77.63</td><td>79.89</td></tr><tr><td>DeepCoral</td><td>87.50</td><td>76.44</td><td>76.19</td><td>77.63</td><td>77.63</td><td>74.69</td><td>84.72</td><td>75.50</td><td>81.93</td><td>74.88</td><td>78.71</td></tr><tr><td>AdaMatch</td><td>89.03</td><td>75.94</td><td>79.38</td><td>76.94</td><td>80.00</td><td>76.31</td><td>89.94</td><td>81.31</td><td>84.26</td><td>73.81</td><td>80.69</td></tr><tr><td>HoMM</td><td>87.61</td><td>76.50</td><td>75.75</td><td>77.00</td><td>77.94</td><td>73.94</td><td>84.89</td><td>75.88</td><td>82.61</td><td>75.31</td><td>78.74</td></tr><tr><td>DIRT-T</td><td>89.77</td><td>75.25</td><td>78.69</td><td>75.88</td><td>80.06</td><td>70.63</td><td>84.77</td><td>77.69</td><td>83.30</td><td>76.69</td><td>79.27</td></tr><tr><td>CLUDA</td><td>78.18</td><td>75.00</td><td>76.75</td><td>74.75</td><td>74.19</td><td>75.94</td><td>79.43</td><td>70.00</td><td>76.88</td><td>75.13</td><td>75.62</td></tr><tr><td>AdvSKM</td><td>86.42</td><td>75.94</td><td>76.25</td><td>77.25</td><td>78.00</td><td>74.88</td><td>85.06</td><td>77.25</td><td>81.76</td><td>75.31</td><td>78.81</td></tr><tr><td>CoDATS</td><td>88.24</td><td>77.44</td><td>78.31</td><td>78.44</td><td>81.81</td><td>73.75</td><td>86.65</td><td>78.88</td><td>84.43</td><td>78.06</td><td>80.60</td></tr><tr><td>RAINCOAT</td><td>89.60</td><td>77.00</td><td>78.56</td><td>78.25</td><td>83.13</td><td>73.06</td><td>85.68</td><td>76.88</td><td>83.13</td><td>74.00</td><td>79.93</td></tr><tr><td>Ours</td><td>92.50</td><td>79.06</td><td>81.75</td><td>80.13</td><td>83.13</td><td>77.94</td><td>90.91</td><td>79.75</td><td>85.11</td><td>78.88</td><td>82.91</td></tr></table>

Table 11: Accuracy (%) on PCL for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→1</td><td>0→2</td><td>1→0</td><td>1→1</td><td>2→0</td><td>2→1</td><td>Avg</td></tr><tr><td>Source-only</td><td>65.68</td><td>57.79</td><td>59.65</td><td>60.65</td><td>56.51</td><td>65.46</td><td>60.95</td></tr><tr><td>CDAN</td><td>68.37</td><td>59.77</td><td>62.79</td><td>62.44</td><td>57.50</td><td>69.27</td><td>63.36</td></tr><tr><td>DeepCoral</td><td>67.66</td><td>60.08</td><td>62.59</td><td>63.58</td><td>57.76</td><td>69.36</td><td>63.51</td></tr><tr><td>AdaMatch</td><td>66.11</td><td>54.92</td><td>58.30</td><td>58.73</td><td>53.75</td><td>54.88</td><td>57.78</td></tr><tr><td>HoMM</td><td>68.28</td><td>60.27</td><td>62.80</td><td>63.75</td><td>58.71</td><td>69.17</td><td>63.83</td></tr><tr><td>DIRT-T</td><td>61.69</td><td>57.29</td><td>60.77</td><td>62.13</td><td>56.79</td><td>67.47</td><td>61.02</td></tr><tr><td>CLUDA</td><td>56.60</td><td>53.46</td><td>60.13</td><td>57.79</td><td>49.78</td><td>50.35</td><td>54.69</td></tr><tr><td>AdvSKM</td><td>67.62</td><td>59.90</td><td>63.06</td><td>64.15</td><td>58.07</td><td>68.68</td><td>63.58</td></tr><tr><td>CoDATS</td><td>70.52</td><td>57.83</td><td>65.10</td><td>64.17</td><td>57.83</td><td>69.62</td><td>64.18</td></tr><tr><td>RAINCOAT</td><td>58.46</td><td>54.04</td><td>59.88</td><td>60.81</td><td>57.63</td><td>63.14</td><td>58.99</td></tr><tr><td>Ours</td><td>70.63</td><td>60.58</td><td>63.42</td><td>64.63</td><td>60.32</td><td>70.53</td><td>65.02</td></tr></table>

Table 12: Accuracy (%) on FD for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→1</td><td>0→2</td><td>0→3</td><td>1→0</td><td>1→2</td><td>2→0</td><td>2→1</td><td>2→3</td><td>3→0</td><td>3→2</td><td>Avg</td></tr><tr><td>Source-only</td><td>62.21</td><td>53.71</td><td>62.41</td><td>63.91</td><td>73.95</td><td>64.08</td><td>93.17</td><td>95.54</td><td>57.08</td><td>74.31</td><td>70.04</td></tr><tr><td>CDAN</td><td>91.29</td><td>71.83</td><td>90.13</td><td>96.50</td><td>90.09</td><td>83.10</td><td>99.38</td><td>99.98</td><td>95.40</td><td>87.95</td><td>90.56</td></tr><tr><td>DeepCoral</td><td>75.54</td><td>71.79</td><td>76.03</td><td>89.13</td><td>83.55</td><td>76.34</td><td>98.84</td><td>98.55</td><td>87.50</td><td>83.71</td><td>84.10</td></tr><tr><td>AdaMatch</td><td>67.81</td><td>55.38</td><td>62.88</td><td>92.21</td><td>98.57</td><td>79.08</td><td>89.96</td><td>90.40</td><td>87.23</td><td>97.57</td><td>82.11</td></tr><tr><td>HoMM</td><td>81.54</td><td>71.63</td><td>78.17</td><td>89.89</td><td>84.78</td><td>76.03</td><td>98.71</td><td>99.55</td><td>90.94</td><td>85.96</td><td>85.72</td></tr><tr><td>DIRT-T</td><td>75.94</td><td>70.85</td><td>76.36</td><td>98.10</td><td>90.27</td><td>81.92</td><td>100.0</td><td>99.98</td><td>97.06</td><td>90.29</td><td>88.08</td></tr><tr><td>CLUDA</td><td>90.47</td><td>82.63</td><td>88.68</td><td>89.06</td><td>92.23</td><td>61.92</td><td>93.91</td><td>90.80</td><td>82.01</td><td>78.17</td><td>84.99</td></tr><tr><td>AdvSKM</td><td>74.71</td><td>66.05</td><td>73.30</td><td>87.86</td><td>86.29</td><td>76.85</td><td>98.66</td><td>99.38</td><td>84.89</td><td>85.74</td><td>83.37</td></tr><tr><td>CoDATS</td><td>81.79</td><td>73.26</td><td>83.15</td><td>89.22</td><td>88.68</td><td>81.43</td><td>99.89</td><td>100.0</td><td>85.47</td><td>89.00</td><td>87.20</td></tr><tr><td>RAINCOAT</td><td>85.18</td><td>79.40</td><td>89.04</td><td>78.84</td><td>90.11</td><td>81.43</td><td>95.18</td><td>96.81</td><td>77.39</td><td>94.08</td><td>86.75</td></tr><tr><td>Ours</td><td>86.52</td><td>69.00</td><td>86.96</td><td>97.92</td><td>99.80</td><td>84.29</td><td>98.62</td><td>98.93</td><td>97.72</td><td>97.66</td><td>91.74</td></tr></table>

<table><tr><td colspan="12">Table 13: Accuracy (%) on UCIHAR for unsupervised domain adaptation.</td></tr><tr><td>Method</td><td>2→11</td><td>6→23</td><td>7→13</td><td>9→18</td><td>12→16</td><td>13→19</td><td>18→21</td><td>20→6</td><td>23→13</td><td>24→12</td><td>Avg</td></tr><tr><td>Source-only</td><td>76.56</td><td>67.36</td><td>83.68</td><td>24.65</td><td>61.11</td><td>88.89</td><td>100.0</td><td>94.10</td><td>71.18</td><td>83.68</td><td>75.12</td></tr><tr><td>CDAN</td><td>85.42</td><td>87.50</td><td>92.01</td><td>58.86</td><td>66.67</td><td>96.52</td><td>100.0</td><td>95.13</td><td>82.64</td><td>93.40</td><td>85.78</td></tr><tr><td>DeepCoral</td><td>90.63</td><td>84.38</td><td>87.50</td><td>46.88</td><td>65.28</td><td>95.49</td><td>100.0</td><td>95.49</td><td>69.79</td><td>87.50</td><td>82.01</td></tr><tr><td>AdaMatch</td><td>75.00</td><td>80.20</td><td>85.76</td><td>56.59</td><td>49.65</td><td>94.79</td><td>100.0</td><td>84.37</td><td>68.75</td><td>70.83</td><td>76.07</td></tr><tr><td>HoMM</td><td>74.06</td><td>82.71</td><td>81.88</td><td>73.96</td><td>70.21</td><td>96.67</td><td>98.75</td><td>73.33</td><td>77.71</td><td>80.63</td><td>80.99</td></tr><tr><td>DIRT-T</td><td>80.21</td><td>74.31</td><td>82.99</td><td>59.03</td><td>67.01</td><td>99.30</td><td>98.61</td><td>92.36</td><td>74.72</td><td>94.27</td><td>83.26</td></tr><tr><td>CLUDA</td><td>81.77</td><td>92.01</td><td>99.31</td><td>67.71</td><td>65.28</td><td>94.44</td><td>98.96</td><td>97.22</td><td>72.92</td><td>99.31</td><td>85.53</td></tr><tr><td>AdvSKM</td><td>98.96</td><td>88.54</td><td>92.71</td><td>74.65</td><td>69.44</td><td>93.05</td><td>100.0</td><td>85.41</td><td>79.51</td><td>96.87</td><td>83.26</td></tr><tr><td>CoDATS</td><td>68.23</td><td>74.31</td><td>77.43</td><td>63.89</td><td>66.32</td><td>94.09</td><td>99.65</td><td>70.49</td><td>56.25</td><td>82.81</td><td>75.54</td></tr><tr><td>RAINCOAT</td><td>100.0</td><td>95.83</td><td>100.0</td><td>75.69</td><td>86.52</td><td>100.0</td><td>100.0</td><td>93.41</td><td>86.52</td><td>93.75</td><td>94.43</td></tr><tr><td>Ours</td><td>100.0</td><td>96.25</td><td>99.16</td><td>91.66</td><td>85.63</td><td>100.0</td><td>100.0</td><td>97.50</td><td>100.0</td><td>100.0</td><td>97.02</td></tr></table>

Table 14: Accuracy (%) on WISDM for unsupervised domain adaptation.

<table><tr><td>Method</td><td>2→32</td><td>4→15</td><td>7→30</td><td>12→7</td><td>12→19</td><td>18→20</td><td>20→30</td><td>21→31</td><td>25→29</td><td>26→2</td><td>Avg</td></tr><tr><td>Source-only</td><td>81.16</td><td>79.86</td><td>89.32</td><td>71.53</td><td>54.29</td><td>83.74</td><td>67.96</td><td>21.29</td><td>26.11</td><td>82.52</td><td>65.78</td></tr><tr><td>CDAN</td><td>89.37</td><td>65.97</td><td>84.79</td><td>70.48</td><td>51.01</td><td>88.62</td><td>77.02</td><td>46.58</td><td>44.33</td><td>83.33</td><td>70.05</td></tr><tr><td>DeepCoral</td><td>87.92</td><td>62.50</td><td>91.26</td><td>79.86</td><td>51.77</td><td>64.23</td><td>81.88</td><td>54.62</td><td>53.89</td><td>77.44</td><td>70.80</td></tr><tr><td>AdaMatch</td><td>74.39</td><td>78.47</td><td>89.64</td><td>73.26</td><td>55.30</td><td>75.20</td><td>74.76</td><td>31.32</td><td>57.78</td><td>87.20</td><td>69.79</td></tr><tr><td>HoMM</td><td>77.10</td><td>74.58</td><td>78.64</td><td>68.13</td><td>50.61</td><td>71.22</td><td>72.82</td><td>56.39</td><td>57.00</td><td>66.10</td><td>67.26</td></tr><tr><td>DIRT-T</td><td>77.78</td><td>70.83</td><td>90.61</td><td>70.20</td><td>51.51</td><td>85.36</td><td>71.84</td><td>54.41</td><td>60.04</td><td>66.46</td><td>69.62</td></tr><tr><td>CLUDA</td><td>73.91</td><td>67.36</td><td>86.40</td><td>65.97</td><td>49.24</td><td>83.74</td><td>72.49</td><td>49.97</td><td>35.00</td><td>86.47</td><td>67.04</td></tr><tr><td>AdvSKM</td><td>70.83</td><td>95.85</td><td>93.85</td><td>77.08</td><td>47.47</td><td>81.30</td><td>21.28</td><td>44.45</td><td>74.79</td><td>74.95</td><td>66.97</td></tr><tr><td>CoDATS</td><td>77.29</td><td>70.83</td><td>83.20</td><td>70.17</td><td>47.47</td><td>76.01</td><td>82.85</td><td>52.61</td><td>53.89</td><td>83.29</td><td>70.66</td></tr><tr><td>RAINCOAT</td><td>79.71</td><td>97.91</td><td>91.28</td><td>89.80</td><td>85.00</td><td>92.23</td><td>91.66</td><td>59.09</td><td>82.97</td><td>83.50</td><td>76.60</td></tr><tr><td>Ours</td><td>89.86</td><td>86.25</td><td>98.06</td><td>98.13</td><td>77.73</td><td>83.66</td><td>91.26</td><td>63.61</td><td>60.00</td><td>99.51</td><td>84.80</td></tr></table>

Table 15: Accuracy (%) on HHAR-D for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→1</td><td>0→2</td><td>0→3</td><td>0→4</td><td>1→0</td><td>1→3</td><td>1→4</td><td>2→1</td><td>3→4</td><td>4→1</td><td>Avg</td></tr><tr><td>Source-only</td><td>65.48</td><td>33.59</td><td>31.71</td><td>39.79</td><td>34.69</td><td>44.83</td><td>49.54</td><td>38.17</td><td>86.17</td><td>44.23</td><td>46.82</td></tr><tr><td>CDAN</td><td>69.86</td><td> $\underline{48.28}$ </td><td>38.22</td><td>48.42</td><td>48.75</td><td>60.48</td><td>51.33</td><td> $\underline{47.84}$ </td><td>87.33</td><td>48.89</td><td>54.94</td></tr><tr><td>DeepCoral</td><td>68.94</td><td>42.88</td><td>40.67</td><td>47.96</td><td>35.63</td><td>55.31</td><td>56.21</td><td>44.71</td><td>87.25</td><td>45.96</td><td>52.55</td></tr><tr><td>AdaMatch</td><td>71.78</td><td>39.60</td><td>39.74</td><td>47.50</td><td> $\underline{52.50}$ </td><td>55.48</td><td>58.33</td><td>46.49</td><td>85.83</td><td>41.15</td><td>53.84</td></tr><tr><td>HoMM</td><td>69.66</td><td>40.51</td><td>39.16</td><td>50.42</td><td> $\underline{35.94}$ </td><td>55.02</td><td>57.13</td><td>42.36</td><td>86.79</td><td>46.35</td><td>52.33</td></tr><tr><td>DIRT-T</td><td>68.37</td><td>42.14</td><td>47.21</td><td> $\underline{52.92}$ </td><td>41.25</td><td>60.14</td><td>55.63</td><td>46.73</td><td> $\underline{92.25}$ </td><td> $\underline{54.81}$ </td><td> $\underline{56.14}$ </td></tr><tr><td>CLUDA</td><td>71.78</td><td>39.60</td><td>39.74</td><td>47.50</td><td>52.50</td><td>55.48</td><td>58.33</td><td>46.49</td><td>85.83</td><td>41.15</td><td>53.84</td></tr><tr><td>AdvSKM</td><td>67.93</td><td>40.71</td><td>40.19</td><td>47.33</td><td>37.19</td><td>55.65</td><td> $\underline{59.54}$ </td><td>42.69</td><td>87.46</td><td> $\underline{49.33}$ </td><td>52.80</td></tr><tr><td>CoDATS</td><td>72.50</td><td>43.35</td><td> $\underline{50.79}$ </td><td>45.50</td><td>58.44</td><td> $\underline{62.24}$ </td><td>54.54</td><td>40.14</td><td>89.63</td><td>45.53</td><td>56.27</td></tr><tr><td>RAINCOAT</td><td> $\underline{74.47}$ </td><td>36.52</td><td> $\underline{48.82}$ </td><td>35.29</td><td>51.25</td><td>41.49</td><td>41.50</td><td>34.28</td><td>88.58</td><td>38.46</td><td>49.07</td></tr><tr><td>Ours</td><td>77.50</td><td>61.36</td><td>54.69</td><td>65.46</td><td>69.38</td><td>71.30</td><td>62.13</td><td>50.10</td><td>93.63</td><td>44.86</td><td>65.04</td></tr></table>

Table 16: Average Macro-F1 Score on Eight Datasets and Five Applications for UDA.

<table><tr><td>Task</td><td>GR</td><td>MFD</td><td>MI</td><td colspan="4">HAR</td><td>SSC</td></tr><tr><td>Dataset</td><td>EMG</td><td>FD</td><td>PCL</td><td>UCIHAR</td><td>HHAR-P</td><td>WISDM</td><td>HHAR-D</td><td>CAP</td></tr><tr><td>Source-only</td><td>0.76</td><td>0.65</td><td>0.60</td><td>0.73</td><td>0.50</td><td>0.52</td><td>0.43</td><td>0.52</td></tr><tr><td>CDAN</td><td>0.80</td><td> $\underline{0.92}$ </td><td>0.63</td><td>0.86</td><td>0.68</td><td>0.54</td><td>0.53</td><td>0.62</td></tr><tr><td>DeepCoral</td><td>0.79</td><td>0.81</td><td>0.63</td><td>0.82</td><td>0.62</td><td>0.52</td><td>0.49</td><td>0.59</td></tr><tr><td>AdaMatch</td><td>0.81</td><td>0.78</td><td>0.56</td><td>0.76</td><td>0.62</td><td>0.54</td><td>0.51</td><td>0.57</td></tr><tr><td>HoMM</td><td>0.79</td><td>0.81</td><td> $\underline{0.64}$ </td><td>0.79</td><td>0.64</td><td>0.49</td><td>0.49</td><td>0.60</td></tr><tr><td>DIRT-T</td><td>0.79</td><td>0.88</td><td> $\underline{0.61}$ </td><td>0.81</td><td>0.64</td><td>0.54</td><td>0.53</td><td> $\underline{0.64}$ </td></tr><tr><td>CLUDA</td><td>0.75</td><td>0.82</td><td>0.48</td><td>0.86</td><td>0.67</td><td>0.57</td><td>0.51</td><td>0.59</td></tr><tr><td>AdvSKM</td><td>0.79</td><td>0.80</td><td>0.63</td><td>0.87</td><td>0.65</td><td>0.55</td><td>0.49</td><td>0.59</td></tr><tr><td>CoDATS</td><td> $\underline{0.81}$ </td><td>0.88</td><td>0.63</td><td>0.72</td><td>0.63</td><td>0.56</td><td> $\underline{0.55}$ </td><td>0.62</td></tr><tr><td>RAINCOAT</td><td>0.80</td><td>0.89</td><td>0.59</td><td> $\underline{0.93}$ </td><td> $\underline{0.75}$ </td><td> $\underline{0.74}$ </td><td>0.47</td><td>0.59</td></tr><tr><td>Ours</td><td>0.83</td><td>0.93</td><td>0.65</td><td>0.97</td><td>0.80</td><td>0.74</td><td>0.62</td><td>0.67</td></tr></table>

Table 17: Macro-F1 Score on EMG for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→1</td><td>0→2</td><td>0→3</td><td>1→2</td><td>1→3</td><td>2→0</td><td>2→1</td><td>2→3</td><td>3→1</td><td>3→2</td><td>Avg</td></tr><tr><td>Source-only</td><td>0.85</td><td>0.74</td><td>0.74</td><td>0.74</td><td>0.75</td><td>0.75</td><td>0.82</td><td>0.74</td><td>0.78</td><td>0.72</td><td>0.76</td></tr><tr><td>CDAN</td><td>0.88</td><td>0.77</td><td>0.78</td><td>0.78</td><td>0.82</td><td>0.74</td><td>0.87</td><td>0.76</td><td>0.84</td><td>0.78</td><td>0.80</td></tr><tr><td>DeepCoral</td><td>0.87</td><td>0.76</td><td>0.76</td><td>0.78</td><td>0.78</td><td>0.75</td><td>0.84</td><td>0.76</td><td>0.82</td><td>0.75</td><td>0.79</td></tr><tr><td>AdaMatch</td><td>0.89</td><td>0.76</td><td>0.79</td><td>0.77</td><td>0.80</td><td>0.76</td><td>0.90</td><td>0.81</td><td>0.84</td><td>0.74</td><td>0.81</td></tr><tr><td>HoMM</td><td>0.87</td><td>0.77</td><td>0.76</td><td>0.77</td><td>0.78</td><td>0.74</td><td>0.84</td><td>0.76</td><td>0.82</td><td>0.75</td><td>0.79</td></tr><tr><td>DIRT-T</td><td>0.90</td><td>0.75</td><td>0.79</td><td>0.76</td><td>0.80</td><td>0.71</td><td>0.84</td><td>0.78</td><td>0.83</td><td>0.77</td><td>0.79</td></tr><tr><td>CLUDA</td><td>0.78</td><td>0.75</td><td>0.77</td><td>0.75</td><td>0.74</td><td>0.76</td><td>0.79</td><td>0.70</td><td>0.75</td><td>0.75</td><td>0.75</td></tr><tr><td>AdvSKM</td><td>0.86</td><td>0.76</td><td>0.76</td><td>0.77</td><td>0.78</td><td>0.76</td><td>0.85</td><td>0.77</td><td>0.81</td><td>0.75</td><td>0.79</td></tr><tr><td>CoDATS</td><td>0.88</td><td>0.77</td><td>0.78</td><td>0.79</td><td>0.82</td><td>0.74</td><td>0.86</td><td>0.79</td><td>0.84</td><td>0.78</td><td>0.81</td></tr><tr><td>RAINCOAT</td><td>0.89</td><td>0.77</td><td>0.79</td><td>0.78</td><td>0.83</td><td>0.73</td><td>0.85</td><td>0.77</td><td>0.83</td><td>0.74</td><td>0.80</td></tr><tr><td>Ours</td><td>0.92</td><td>0.79</td><td>0.82</td><td>0.80</td><td>0.83</td><td>0.78</td><td>0.91</td><td>0.80</td><td>0.85</td><td>0.79</td><td>0.83</td></tr></table>

Table 18: Macro-F1 Score on CAP for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→1</td><td>0→3</td><td>0→4</td><td>1→0</td><td>1→4</td><td>2→3</td><td>3→0</td><td>3→1</td><td>4→1</td><td>4→3</td><td>Avg</td></tr><tr><td>Source-only</td><td>0.39</td><td>0.71</td><td>0.61</td><td>0.50</td><td>0.54</td><td>0.45</td><td>0.63</td><td>0.30</td><td>0.33</td><td>0.69</td><td>0.52</td></tr><tr><td>CDAN</td><td>0.62</td><td>0.73</td><td>0.66</td><td>0.58</td><td>0.59</td><td>0.48</td><td>0.68</td><td>0.61</td><td>0.55</td><td> $\underline{0.73}$ </td><td>0.62</td></tr><tr><td>DeepCoral</td><td>0.61</td><td>0.73</td><td>0.65</td><td>0.54</td><td>0.58</td><td>0.53</td><td>0.66</td><td>0.44</td><td>0.44</td><td>0.70</td><td>0.59</td></tr><tr><td>AdaMatch</td><td>0.52</td><td>0.73</td><td>0.64</td><td>0.58</td><td>0.55</td><td>0.29</td><td>0.66</td><td>0.52</td><td>0.51</td><td>0.67</td><td>0.57</td></tr><tr><td>HoMM</td><td>0.62</td><td>0.73</td><td>0.65</td><td>0.56</td><td>0.59</td><td> $\underline{0.54}$ </td><td>0.66</td><td>0.50</td><td>0.48</td><td>0.71</td><td>0.60</td></tr><tr><td>DIRT-T</td><td> $\underline{0.65}$ </td><td>0.75</td><td> $\underline{0.69}$ </td><td>0.57</td><td>0.59</td><td>0.50</td><td>0.69</td><td> $\underline{0.67}$ </td><td>0.59</td><td>0.71</td><td> $\underline{0.64}$ </td></tr><tr><td>CLUDA</td><td>0.58</td><td>0.71</td><td>0.51</td><td>0.63</td><td>0.61</td><td>0.44</td><td>0.67</td><td>0.50</td><td>0.55</td><td>0.68</td><td>0.59</td></tr><tr><td>AdvSKM</td><td>0.58</td><td>0.73</td><td>0.65</td><td>0.55</td><td>0.59</td><td>0.53</td><td>0.66</td><td>0.48</td><td>0.41</td><td>0.69</td><td>0.59</td></tr><tr><td>CoDATS</td><td> $\underline{0.64}$ </td><td> $\underline{0.75}$ </td><td>0.65</td><td> $\underline{0.61}$ </td><td> $\underline{0.63}$ </td><td>0.51</td><td> $\underline{0.70}$ </td><td>0.51</td><td>0.54</td><td>0.71</td><td>0.62</td></tr><tr><td>RAINCOAT</td><td>0.58</td><td>0.65</td><td>0.61</td><td>0.55</td><td>0.56</td><td>0.50</td><td>0.62</td><td>0.63</td><td> $\underline{0.60}$ </td><td>0.61</td><td>0.59</td></tr><tr><td>Ours</td><td> $\underline{0.64}$ </td><td> $\underline{0.76}$ </td><td> $\underline{0.68}$ </td><td>0.62</td><td>0.63</td><td>0.54</td><td>0.71</td><td>0.72</td><td>0.70</td><td>0.74</td><td>0.67</td></tr></table>

Table 19: Macro-F1 Score on PCL for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→1</td><td>0→2</td><td>1→0</td><td>1→1</td><td>2→0</td><td>2→1</td><td>Avg</td></tr><tr><td>Source-only</td><td>0.65</td><td>0.57</td><td>0.58</td><td>0.60</td><td>0.55</td><td>0.64</td><td>0.60</td></tr><tr><td>CDAN</td><td>0.68</td><td>0.59</td><td>0.62</td><td>0.62</td><td>0.57</td><td>0.69</td><td>0.63</td></tr><tr><td>DeepCoral</td><td>0.68</td><td>0.60</td><td>0.62</td><td>0.63</td><td>0.57</td><td>0.69</td><td>0.63</td></tr><tr><td>AdaMatch</td><td>0.66</td><td>0.53</td><td>0.58</td><td>0.57</td><td>0.53</td><td>0.51</td><td>0.56</td></tr><tr><td>HoMM</td><td>0.68</td><td>0.60</td><td>0.63</td><td>0.63</td><td>0.58</td><td>0.69</td><td>0.64</td></tr><tr><td>DIRT-T</td><td>0.61</td><td>0.57</td><td>0.61</td><td>0.62</td><td>0.56</td><td>0.67</td><td>0.61</td></tr><tr><td>CLUDA</td><td>0.55</td><td>0.49</td><td>0.59</td><td>0.56</td><td>0.33</td><td>0.36</td><td>0.48</td></tr><tr><td>AdvSKM</td><td>0.67</td><td>0.60</td><td>0.63</td><td>0.63</td><td>0.58</td><td>0.69</td><td>0.63</td></tr><tr><td>CoDATS</td><td>0.70</td><td>0.55</td><td>0.65</td><td>0.64</td><td>0.57</td><td>0.69</td><td>0.63</td></tr><tr><td>RAINCOAT</td><td>0.58</td><td>0.54</td><td>0.59</td><td>0.61</td><td>0.57</td><td>0.63</td><td>0.59</td></tr><tr><td>Ours</td><td>0.71</td><td>0.60</td><td>0.63</td><td>0.64</td><td>0.60</td><td>0.71</td><td>0.65</td></tr></table>

Table 20: Macro-F1 Score on FD for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→1</td><td>0→2</td><td>0→3</td><td>1→0</td><td>1→2</td><td>2→0</td><td>2→1</td><td>2→3</td><td>3→0</td><td>3→2</td><td>Avg</td></tr><tr><td>Source-only</td><td>0.41</td><td>0.33</td><td>0.41</td><td>0.65</td><td>0.77</td><td>0.64</td><td>0.95</td><td>0.97</td><td>0.59</td><td>0.78</td><td>0.65</td></tr><tr><td>CDAN</td><td>0.91</td><td>0.76</td><td>0.90</td><td>0.95</td><td>0.92</td><td>0.86</td><td>1.00</td><td>1.00</td><td>0.94</td><td>0.91</td><td>0.92</td></tr><tr><td>DeepCoral</td><td>0.61</td><td>0.62</td><td>0.62</td><td>0.90</td><td>0.87</td><td>0.77</td><td>0.99</td><td>0.99</td><td>0.89</td><td>0.88</td><td>0.81</td></tr><tr><td>AdaMatch</td><td>0.50</td><td>0.45</td><td>0.46</td><td>0.91</td><td>0.98</td><td>0.80</td><td>0.93</td><td>0.93</td><td>0.87</td><td>0.97</td><td>0.78</td></tr><tr><td>HoMM</td><td>0.61</td><td>0.52</td><td>0.62</td><td>0.91</td><td>0.88</td><td>0.78</td><td>0.99</td><td>1.00</td><td>0.91</td><td>0.89</td><td>0.81</td></tr><tr><td>DIRT-T</td><td>0.80</td><td>0.62</td><td>0.70</td><td>0.97</td><td>0.93</td><td>0.84</td><td>1.00</td><td>1.00</td><td>0.96</td><td>0.93</td><td>0.88</td></tr><tr><td>CLUDA</td><td>0.84</td><td>0.80</td><td>0.79</td><td>0.88</td><td>0.93</td><td>0.50</td><td>0.95</td><td>0.90</td><td>0.84</td><td>0.80</td><td>0.82</td></tr><tr><td>AdvSKM</td><td>0.55</td><td>0.54</td><td>0.57</td><td>0.89</td><td>0.89</td><td>0.76</td><td>0.99</td><td>1.00</td><td>0.87</td><td>0.89</td><td>0.80</td></tr><tr><td>CoDATS</td><td>0.80</td><td>0.69</td><td>0.87</td><td>0.90</td><td>0.92</td><td>0.86</td><td>1.00</td><td>1.00</td><td>0.87</td><td>0.92</td><td>0.88</td></tr><tr><td>RAINCOAT</td><td>0.89</td><td>0.84</td><td>0.92</td><td>0.81</td><td>0.92</td><td>0.85</td><td>0.96</td><td>0.98</td><td>0.81</td><td>0.94</td><td>0.89</td></tr><tr><td>Ours</td><td>0.86</td><td>0.75</td><td>0.89</td><td>0.96</td><td>1.00</td><td>0.88</td><td>0.99</td><td>0.99</td><td>0.96</td><td>0.98</td><td>0.93</td></tr></table>

Table 21: Macro-F1 Score on UCIHAR for unsupervised domain adaptation.

<table><tr><td>Method</td><td>2→11</td><td>6→23</td><td>7→13</td><td>9→18</td><td>12→16</td><td>13→19</td><td>18→21</td><td>20→6</td><td>23→13</td><td>24→12</td><td>Avg</td></tr><tr><td>Source-only</td><td>0.69</td><td>0.63</td><td>0.84</td><td>0.17</td><td>0.58</td><td>0.91</td><td>1.00</td><td>0.94</td><td>0.71</td><td>0.84</td><td>0.73</td></tr><tr><td>CDAN</td><td>0.85</td><td>0.88</td><td>0.91</td><td>0.61</td><td>0.64</td><td>0.97</td><td>1.00</td><td> $\underline{0.95}$ </td><td>0.82</td><td>0.92</td><td>0.86</td></tr><tr><td>DeepCoral</td><td>0.91</td><td>0.81</td><td>0.87</td><td>0.44</td><td>0.65</td><td>0.95</td><td>1.00</td><td> $\underline{0.95}$ </td><td>0.70</td><td>0.88</td><td>0.82</td></tr><tr><td>AdaMatch</td><td>0.73</td><td>0.81</td><td>0.86</td><td>0.55</td><td>0.48</td><td>0.94</td><td>1.00</td><td>0.84</td><td>0.67</td><td>0.70</td><td>0.76</td></tr><tr><td>HoMM</td><td>0.73</td><td>0.78</td><td>0.81</td><td>0.69</td><td>0.69</td><td>0.96</td><td>0.99</td><td>0.71</td><td>0.75</td><td>0.78</td><td>0.79</td></tr><tr><td>DIRT-T</td><td>0.81</td><td>0.68</td><td>0.82</td><td>0.58</td><td>0.62</td><td>0.99</td><td>0.98</td><td>0.92</td><td>0.74</td><td>0.93</td><td>0.81</td></tr><tr><td>CLUDA</td><td>0.81</td><td>0.92</td><td>0.99</td><td>0.67</td><td>0.64</td><td>0.94</td><td>0.99</td><td>0.98</td><td>0.71</td><td> $\underline{0.99}$ </td><td>0.86</td></tr><tr><td>AdvSKM</td><td>0.99</td><td>0.87</td><td>0.92</td><td>0.73</td><td>0.68</td><td>0.93</td><td>1.00</td><td>0.84</td><td>0.77</td><td>0.96</td><td>0.87</td></tr><tr><td>CoDATS</td><td>0.66</td><td>0.71</td><td>0.78</td><td>0.60</td><td>0.64</td><td>0.93</td><td>0.99</td><td>0.65</td><td>0.54</td><td>0.81</td><td>0.72</td></tr><tr><td>RAINCOAT</td><td> $\underline{1.00}$ </td><td> $\underline{0.96}$ </td><td> $\underline{1.00}$ </td><td> $\underline{0.76}$ </td><td> $\underline{0.86}$ </td><td> $\underline{1.00}$ </td><td> $\underline{1.00}$ </td><td>0.94</td><td> $\underline{0.86}$ </td><td>0.94</td><td> $\underline{0.93}$ </td></tr><tr><td>Ours</td><td>1.00</td><td>0.97</td><td> $\underline{0.99}$ </td><td>0.91</td><td>0.86</td><td>1.00</td><td>1.00</td><td>0.98</td><td>1.00</td><td>1.00</td><td>0.97</td></tr></table>

Table 22: Macro-F1 Score on HHAR-P for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→2</td><td>1→6</td><td>2→4</td><td>4→0</td><td>4→5</td><td>5→1</td><td>5→2</td><td>7→2</td><td>7→5</td><td>8→4</td><td>Avg</td></tr><tr><td>Source-only</td><td>0.60</td><td>0.64</td><td>0.32</td><td>0.29</td><td>0.78</td><td>0.90</td><td>0.19</td><td>0.31</td><td>0.36</td><td>0.58</td><td>0.50</td></tr><tr><td>CDAN</td><td>0.70</td><td>0.93</td><td>0.52</td><td>0.27</td><td>0.98</td><td>0.98</td><td>0.35</td><td>0.32</td><td>0.76</td><td>0.97</td><td>0.68</td></tr><tr><td>DeepCoral</td><td>0.86</td><td>0.91</td><td>0.45</td><td>0.26</td><td>0.90</td><td>0.90</td><td>0.36</td><td>0.32</td><td>0.50</td><td>0.73</td><td>0.62</td></tr><tr><td>AdaMatch</td><td>0.83</td><td>0.93</td><td>0.46</td><td>0.32</td><td>0.76</td><td>0.94</td><td>0.40</td><td>0.37</td><td>0.60</td><td>0.61</td><td>0.62</td></tr><tr><td>HoMM</td><td>0.70</td><td>0.91</td><td>0.45</td><td>0.37</td><td>0.88</td><td>0.91</td><td>0.34</td><td>0.40</td><td>0.61</td><td>0.79</td><td>0.64</td></tr><tr><td>DIRT-T</td><td>0.76</td><td>0.86</td><td>0.51</td><td>0.30</td><td>0.93</td><td>0.90</td><td>0.36</td><td>0.34</td><td>0.73</td><td>0.64</td><td>0.64</td></tr><tr><td>CLUDA</td><td>0.82</td><td>0.94</td><td>0.44</td><td>0.40</td><td>0.94</td><td>0.96</td><td>0.37</td><td>0.36</td><td>0.65</td><td>0.84</td><td>0.67</td></tr><tr><td>AdvSKM</td><td>0.72</td><td>0.88</td><td>0.44</td><td>0.33</td><td>0.93</td><td>0.92</td><td>0.35</td><td>0.41</td><td>0.64</td><td>0.83</td><td>0.65</td></tr><tr><td>CoDATS</td><td>0.73</td><td>0.90</td><td>0.46</td><td>0.20</td><td>0.96</td><td>0.94</td><td>0.41</td><td>0.36</td><td>0.59</td><td>0.95</td><td>0.63</td></tr><tr><td>RAINCOAT</td><td>0.87</td><td>0.93</td><td>0.59</td><td>0.45</td><td>0.98</td><td>0.98</td><td>0.41</td><td>0.44</td><td>0.86</td><td>0.94</td><td>0.75</td></tr><tr><td>Ours</td><td>0.86</td><td>0.93</td><td>0.74</td><td>0.52</td><td>0.97</td><td>0.98</td><td>0.62</td><td>0.65</td><td>0.89</td><td>0.89</td><td>0.80</td></tr></table>

<table><tr><td>Method</td><td>2→32</td><td>4→15</td><td>7→30</td><td>12→7</td><td>12→19</td><td>18→20</td><td>20→30</td><td>21→31</td><td>25→29</td><td>26→2</td><td>Avg</td></tr><tr><td>Source-only</td><td>0.68</td><td>0.52</td><td>0.77</td><td>0.53</td><td>0.36</td><td>0.81</td><td>0.56</td><td>0.10</td><td>0.15</td><td>0.69</td><td>0.52</td></tr><tr><td>CDAN</td><td>0.72</td><td>0.44</td><td>0.70</td><td>0.50</td><td>0.31</td><td>0.87</td><td>0.64</td><td>0.31</td><td>0.23</td><td>0.71</td><td>0.54</td></tr><tr><td>DeepCoral</td><td>0.71</td><td>0.42</td><td>0.85</td><td>0.67</td><td>0.35</td><td>0.63</td><td>0.67</td><td>0.27</td><td>0.25</td><td>0.64</td><td>0.52</td></tr><tr><td>AdaMatch</td><td>0.59</td><td>0.54</td><td>0.76</td><td>0.67</td><td>0.38</td><td>0.66</td><td>0.54</td><td>0.16</td><td>0.24</td><td>0.74</td><td>0.54</td></tr><tr><td>HoMM</td><td>0.63</td><td>0.42</td><td>0.62</td><td>0.55</td><td>0.39</td><td>0.63</td><td>0.60</td><td>0.30</td><td>0.26</td><td>0.54</td><td>0.49</td></tr><tr><td>DIRT-T</td><td>0.65</td><td>0.41</td><td>0.78</td><td>0.56</td><td>0.39</td><td>0.67</td><td>0.65</td><td>0.28</td><td>0.21</td><td>0.54</td><td>0.54</td></tr><tr><td>CLUDA</td><td>0.64</td><td>0.61</td><td>0.81</td><td>0.59</td><td>0.41</td><td>0.70</td><td>0.70</td><td>0.27</td><td>0.26</td><td>0.75</td><td>0.57</td></tr><tr><td>AdvSKM</td><td>0.61</td><td>0.55</td><td>0.84</td><td>0.53</td><td>0.35</td><td>0.71</td><td>0.61</td><td>0.28</td><td>0.28</td><td>0.55</td><td>0.55</td></tr><tr><td>CoDATS</td><td>0.66</td><td>0.41</td><td>0.75</td><td>0.62</td><td>0.37</td><td>0.76</td><td>0.72</td><td>0.30</td><td>0.30</td><td>0.70</td><td>0.56</td></tr><tr><td>RAINCOAT</td><td>0.68</td><td>0.98</td><td>0.86</td><td>0.72</td><td>0.78</td><td>0.92</td><td>0.87</td><td>0.43</td><td>0.44</td><td>0.75</td><td>0.74</td></tr><tr><td>Ours</td><td>0.81</td><td>0.65</td><td>0.99</td><td>1.00</td><td>0.63</td><td>0.76</td><td>0.87</td><td>00.36</td><td>0.28</td><td>1.00</td><td>0.74</td></tr></table>

Table 23: Macro-F1 Score on WISDM for unsupervised domain adaptation.

Table 24: Macro-F1 Score on HHAR-D for unsupervised domain adaptation.

<table><tr><td>Method</td><td>0→1</td><td>0→2</td><td>0→3</td><td>0→4</td><td>1→0</td><td>1→3</td><td>1→4</td><td>2→1</td><td>3→4</td><td>4→1</td><td>Avg</td></tr><tr><td>Source-only</td><td>0.61</td><td>0.27</td><td>0.25</td><td>0.33</td><td>0.44</td><td>0.43</td><td>0.46</td><td>0.32</td><td>0.85</td><td>0.38</td><td>0.43</td></tr><tr><td>CDAN</td><td>0.67</td><td>0.42</td><td>0.35</td><td>0.42</td><td>0.66</td><td>0.57</td><td>0.50</td><td>0.44</td><td>0.88</td><td>0.44</td><td>0.53</td></tr><tr><td>DeepCoral</td><td>0.65</td><td>0.34</td><td>0.33</td><td>0.40</td><td>0.48</td><td>0.53</td><td>0.53</td><td>0.39</td><td>0.86</td><td>0.41</td><td>0.49</td></tr><tr><td>AdaMatch</td><td>0.69</td><td>0.36</td><td>0.36</td><td>0.41</td><td>0.60</td><td>0.49</td><td>0.56</td><td>0.41</td><td>0.86</td><td>0.36</td><td>0.51</td></tr><tr><td>HoMM</td><td>0.66</td><td>0.33</td><td>0.31</td><td>0.41</td><td>0.47</td><td>0.52</td><td>0.53</td><td>0.37</td><td>0.86</td><td>0.42</td><td>0.49</td></tr><tr><td>DIRT-T</td><td>0.66</td><td>0.38</td><td>0.40</td><td>0.44</td><td>0.52</td><td>0.60</td><td>0.53</td><td>0.39</td><td>0.93</td><td>0.49</td><td>0.53</td></tr><tr><td>CLUDA</td><td>0.69</td><td>0.36</td><td>0.36</td><td>0.41</td><td>0.60</td><td>0.49</td><td>0.56</td><td>0.41</td><td>0.86</td><td>0.36</td><td>0.51</td></tr><tr><td>AdvSKM</td><td>0.63</td><td>0.32</td><td>0.31</td><td>0.38</td><td>0.46</td><td>0.54</td><td>0.56</td><td>0.36</td><td>0.86</td><td>0.44</td><td>0.49</td></tr><tr><td>CoDATS</td><td>0.71</td><td>0.38</td><td>0.44</td><td>0.39</td><td>0.70</td><td>0.61</td><td>0.53</td><td>0.38</td><td>0.90</td><td>0.44</td><td>0.55</td></tr><tr><td>RAINCOAT</td><td>0.72</td><td>0.32</td><td>0.42</td><td>0.32</td><td>0.56</td><td>0.39</td><td>0.38</td><td>0.31</td><td>0.89</td><td>0.35</td><td>0.47</td></tr><tr><td>Ours</td><td>0.76</td><td>0.53</td><td>0.49</td><td>0.56</td><td>0.81</td><td>0.67</td><td>0.59</td><td>0.44</td><td>0.93</td><td>0.41</td><td>0.62</td></tr></table>

## NeurIPS Paper Checklist

The checklist is designed to encourage best practices for responsible machine learning research, addressing issues of reproducibility, transparency, research ethics, and societal impact. Do not remove the checklist: The papers not including the checklist will be desk rejected. The checklist should follow the references and precede the (optional) supplemental material. The checklist does NOT count towards the page limit.

Please read the checklist guidelines carefully for information on how to answer these questions. For each question in the checklist:

• You should answer [Yes] , [No] , or [NA] .

• [NA] means either that the question is Not Applicable for that particular paper or the relevant information is Not Available.

• Please provide a short (1–2 sentence) justification right after your answer (even for NA).

The checklist answers are an integral part of your paper submission. They are visible to the reviewers, area chairs, senior area chairs, and ethics reviewers. You will be asked to also include it (after eventual revisions) with the final version of your paper, and its final version will be published with the paper.

The reviewers of your paper will be asked to use the checklist as one of the factors in their evaluation. While "[Yes] " is generally preferable to "[No] ", it is perfectly acceptable to answer "[No] " provided a proper justification is given (e.g., "error bars are not reported because it would be too computationally expensive" or "we were unable to find the license for the dataset we used"). In general, answering "[No] " or "[NA] " is not grounds for rejection. While the questions are phrased in a binary way, we acknowledge that the true answer is often more nuanced, so please just use your best judgment and write a justification to elaborate. All supporting evidence can appear either in the main paper or the supplemental material, provided in appendix. If you answer [Yes] to a question, in the justification please point to the section(s) where related material for the question can be found.

## IMPORTANT, please:

• Delete this instruction block, but keep the section heading “NeurIPS paper checklist",

• Keep the checklist subsection headings, questions/answers and guidelines below.

• Do not modify the questions and only use the provided macros for your answers.

## 1. Claims

Question: Do the main claims made in the abstract and introduction accurately reflect the paper’s contributions and scope?

Answer: [Yes]

Justification: We include detailed information in Section 1.

Guidelines:

• The answer NA means that the abstract and introduction do not include the claims made in the paper.

• The abstract and/or introduction should clearly state the claims made, including the contributions made in the paper and important assumptions and limitations. A No or NA answer to this question will not be perceived well by the reviewers.

• The claims made should match theoretical and experimental results, and reflect how much the results can be expected to generalize to other settings.

• It is fine to include aspirational goals as motivation as long as it is clear that these goals are not attained by the paper.

## 2. Limitations

Question: Does the paper discuss the limitations of the work performed by the authors?

Answer: [Yes]

Justification: The limitations are included in Appendix D.

## Guidelines:

• The answer NA means that the paper has no limitation while the answer No means that the paper has limitations, but those are not discussed in the paper.

• The authors are encouraged to create a separate "Limitations" section in their paper.

• The paper should point out any strong assumptions and how robust the results are to violations of these assumptions (e.g., independence assumptions, noiseless settings, model well-specification, asymptotic approximations only holding locally). The authors should reflect on how these assumptions might be violated in practice and what the implications would be.

• The authors should reflect on the scope of the claims made, e.g., if the approach was only tested on a few datasets or with a few runs. In general, empirical results often depend on implicit assumptions, which should be articulated.

• The authors should reflect on the factors that influence the performance of the approach. For example, a facial recognition algorithm may perform poorly when image resolution is low or images are taken in low lighting. Or a speech-to-text system might not be used reliably to provide closed captions for online lectures because it fails to handle technical jargon.

• The authors should discuss the computational efficiency of the proposed algorithms and how they scale with dataset size.

• If applicable, the authors should discuss possible limitations of their approach to address problems of privacy and fairness.

• While the authors might fear that complete honesty about limitations might be used by reviewers as grounds for rejection, a worse outcome might be that reviewers discover limitations that aren’t acknowledged in the paper. The authors should use their best judgment and recognize that individual actions in favor of transparency play an important role in developing norms that preserve the integrity of the community. Reviewers will be specifically instructed to not penalize honesty concerning limitations.

## 3. Theory Assumptions and Proofs

Question: For each theoretical result, does the paper provide the full set of assumptions and a complete (and correct) proof?

Answer: [Yes]

Justification: The theory assumptions are included in Section 4.

Guidelines:

• The answer NA means that the paper does not include theoretical results.

• All the theorems, formulas, and proofs in the paper should be numbered and crossreferenced.

• All assumptions should be clearly stated or referenced in the statement of any theorems.

• The proofs can either appear in the main paper or the supplemental material, but if they appear in the supplemental material, the authors are encouraged to provide a short proof sketch to provide intuition.

• Inversely, any informal proof provided in the core of the paper should be complemented by formal proofs provided in appendix or supplemental material.

• Theorems and Lemmas that the proof relies upon should be properly referenced.

## 4. Experimental Result Reproducibility

Question: Does the paper fully disclose all the information needed to reproduce the main experimental results of the paper to the extent that it affects the main claims and/or conclusions of the paper (regardless of whether the code and data are provided or not)?

Answer: [Yes]

Justification: We include the detailed experimental settings in Appendix B.

Guidelines:

• The answer NA means that the paper does not include experiments.

• If the paper includes experiments, a No answer to this question will not be perceived well by the reviewers: Making the paper reproducible is important, regardless of whether the code and data are provided or not.

• If the contribution is a dataset and/or model, the authors should describe the steps taken to make their results reproducible or verifiable.

• Depending on the contribution, reproducibility can be accomplished in various ways. For example, if the contribution is a novel architecture, describing the architecture fully might suffice, or if the contribution is a specific model and empirical evaluation, it may be necessary to either make it possible for others to replicate the model with the same dataset, or provide access to the model. In general. releasing code and data is often one good way to accomplish this, but reproducibility can also be provided via detailed instructions for how to replicate the results, access to a hosted model (e.g., in the case of a large language model), releasing of a model checkpoint, or other means that are appropriate to the research performed.

• While NeurIPS does not require releasing code, the conference does require all submissions to provide some reasonable avenue for reproducibility, which may depend on the nature of the contribution. For example

(a) If the contribution is primarily a new algorithm, the paper should make it clear how to reproduce that algorithm.

(b) If the contribution is primarily a new model architecture, the paper should describe the architecture clearly and fully.

(c) If the contribution is a new model (e.g., a large language model), then there should either be a way to access this model for reproducing the results or a way to reproduce the model (e.g., with an open-source dataset or instructions for how to construct the dataset).

(d) We recognize that reproducibility may be tricky in some cases, in which case authors are welcome to describe the particular way they provide for reproducibility. In the case of closed-source models, it may be that access to the model is limited in some way (e.g., to registered users), but it should be possible for other researchers to have some path to reproducing or verifying the results.

## 5. Open access to data and code

Question: Does the paper provide open access to the data and code, with sufficient instructions to faithfully reproduce the main experimental results, as described in supplemental material?

Answer: [Yes]

Justification: Code is available at the anonymous link: https://anonymous.4open. science/r/ACON.

Guidelines:

• The answer NA means that paper does not include experiments requiring code.

• Please see the NeurIPS code and data submission guidelines (https://nips.cc/ public/guides/CodeSubmissionPolicy) for more details.

• While we encourage the release of code and data, we understand that this might not be possible, so “No” is an acceptable answer. Papers cannot be rejected simply for not including code, unless this is central to the contribution (e.g., for a new open-source benchmark).

• The instructions should contain the exact command and environment needed to run to reproduce the results. See the NeurIPS code and data submission guidelines (https: //nips.cc/public/guides/CodeSubmissionPolicy) for more details.

• The authors should provide instructions on data access and preparation, including how to access the raw data, preprocessed data, intermediate data, and generated data, etc.

• The authors should provide scripts to reproduce all experimental results for the new proposed method and baselines. If only a subset of experiments are reproducible, they should state which ones are omitted from the script and why.

• At submission time, to preserve anonymity, the authors should release anonymized versions (if applicable).

• Providing as much information as possible in supplemental material (appended to the paper) is recommended, but including URLs to data and code is permitted.

## 6. Experimental Setting/Details

Question: Does the paper specify all the training and test details (e.g., data splits, hyperparameters, how they were chosen, type of optimizer, etc.) necessary to understand the results?

Answer: [Yes]

Justification: We include the detailed experimental settings in Appendix B.

Guidelines:

• The answer NA means that the paper does not include experiments.

• The experimental setting should be presented in the core of the paper to a level of detail that is necessary to appreciate the results and make sense of them.

• The full details can be provided either with the code, in appendix, or as supplemental material.

## 7. Experiment Statistical Significance

Question: Does the paper report error bars suitably and correctly defined or other appropriate information about the statistical significance of the experiments?

Answer: [Yes]

Justification: The results are included in Appendix F.

Guidelines:

• The answer NA means that the paper does not include experiments.

• The authors should answer "Yes" if the results are accompanied by error bars, confidence intervals, or statistical significance tests, at least for the experiments that support the main claims of the paper.

• The factors of variability that the error bars are capturing should be clearly stated (for example, train/test split, initialization, random drawing of some parameter, or overall run with given experimental conditions).

• The method for calculating the error bars should be explained (closed form formula, call to a library function, bootstrap, etc.)

• The assumptions made should be given (e.g., Normally distributed errors).

• It should be clear whether the error bar is the standard deviation or the standard error of the mean.

• It is OK to report 1-sigma error bars, but one should state it. The authors should preferably report a 2-sigma error bar than state that they have a 96% CI, if the hypothesis of Normality of errors is not verified.

• For asymmetric distributions, the authors should be careful not to show in tables or figures symmetric error bars that would yield results that are out of range (e.g. negative error rates).

• If error bars are reported in tables or plots, The authors should explain in the text how they were calculated and reference the corresponding figures or tables in the text.

## 8. Experiments Compute Resources

Question: For each experiment, does the paper provide sufficient information on the computer resources (type of compute workers, memory, time of execution) needed to reproduce the experiments?

Answer: [Yes]

Justification: All the experiments in this paper are conducted on a single NVIDIA GeForce RTX 4090 with 24GiB of memory.

Guidelines:

• The answer NA means that the paper does not include experiments.

• The paper should indicate the type of compute workers CPU or GPU, internal cluster, or cloud provider, including relevant memory and storage.

• The paper should provide the amount of compute required for each of the individual experimental runs as well as estimate the total compute.

• The paper should disclose whether the full research project required more compute than the experiments reported in the paper (e.g., preliminary or failed experiments that didn’t make it into the paper).

## 9. Code Of Ethics

Question: Does the research conducted in the paper conform, in every respect, with the NeurIPS Code of Ethics https://neurips.cc/public/EthicsGuidelines?

Answer: [Yes]

Justification: In every respect in the paper, we follow the NeurIPS Code of Ethics.

Guidelines:

• The answer NA means that the authors have not reviewed the NeurIPS Code of Ethics.

• If the authors answer No, they should explain the special circumstances that require a deviation from the Code of Ethics.

• The authors should make sure to preserve anonymity (e.g., if there is a special consideration due to laws or regulations in their jurisdiction).

## 10. Broader Impacts

Question: Does the paper discuss both potential positive societal impacts and negative societal impacts of the work performed?

Answer: [Yes]

Justification: Broader impacts is included in Appendix E.

Guidelines:

• The answer NA means that there is no societal impact of the work performed.

• If the authors answer NA or No, they should explain why their work has no societal impact or why the paper does not address societal impact.

• Examples of negative societal impacts include potential malicious or unintended uses (e.g., disinformation, generating fake profiles, surveillance), fairness considerations (e.g., deployment of technologies that could make decisions that unfairly impact specific groups), privacy considerations, and security considerations.

• The conference expects that many papers will be foundational research and not tied to particular applications, let alone deployments. However, if there is a direct path to any negative applications, the authors should point it out. For example, it is legitimate to point out that an improvement in the quality of generative models could be used to generate deepfakes for disinformation. On the other hand, it is not needed to point out that a generic algorithm for optimizing neural networks could enable people to train models that generate Deepfakes faster.

• The authors should consider possible harms that could arise when the technology is being used as intended and functioning correctly, harms that could arise when the technology is being used as intended but gives incorrect results, and harms following from (intentional or unintentional) misuse of the technology.

• If there are negative societal impacts, the authors could also discuss possible mitigation strategies (e.g., gated release of models, providing defenses in addition to attacks, mechanisms for monitoring misuse, mechanisms to monitor how a system learns from feedback over time, improving the efficiency and accessibility of ML).

## 11. Safeguards

Question: Does the paper describe safeguards that have been put in place for responsible release of data or models that have a high risk for misuse (e.g., pretrained language models, image generators, or scraped datasets)?

Answer:[NA]

Justification: The paper poses no such risks.

Guidelines:

• The answer NA means that the paper poses no such risks.

• Released models that have a high risk for misuse or dual-use should be released with necessary safeguards to allow for controlled use of the model, for example by requiring that users adhere to usage guidelines or restrictions to access the model or implementing safety filters.

• Datasets that have been scraped from the Internet could pose safety risks. The authors should describe how they avoided releasing unsafe images.

• We recognize that providing effective safeguards is challenging, and many papers do not require this, but we encourage authors to take this into account and make a best faith effort.

## 12. Licenses for existing assets

Question: Are the creators or original owners of assets (e.g., code, data, models), used in the paper, properly credited and are the license and terms of use explicitly mentioned and properly respected?

Answer: [Yes]

Justification: All data, models, and code in the paper respect the license.

Guidelines:

• The answer NA means that the paper does not use existing assets.

• The authors should cite the original paper that produced the code package or dataset.

• The authors should state which version of the asset is used and, if possible, include a URL.

• The name of the license (e.g., CC-BY 4.0) should be included for each asset.

• For scraped data from a particular source (e.g., website), the copyright and terms of service of that source should be provided.

• If assets are released, the license, copyright information, and terms of use in the package should be provided. For popular datasets, paperswithcode.com/datasets has curated licenses for some datasets. Their licensing guide can help determine the license of a dataset.

• For existing datasets that are re-packaged, both the original license and the license of the derived asset (if it has changed) should be provided.

• If this information is not available online, the authors are encouraged to reach out to the asset’s creators.

## 13. New Assets

Question: Are new assets introduced in the paper well documented and is the documentation provided alongside the assets?

Answer: [NA]

Justification: The paper does not release new assets.

Guidelines:

• The answer NA means that the paper does not release new assets.

• Researchers should communicate the details of the dataset/code/model as part of their submissions via structured templates. This includes details about training, license, limitations, etc.

• The paper should discuss whether and how consent was obtained from people whose asset is used.

• At submission time, remember to anonymize your assets (if applicable). You can either create an anonymized URL or include an anonymized zip file.

## 14. Crowdsourcing and Research with Human Subjects

Question: For crowdsourcing experiments and research with human subjects, does the paper include the full text of instructions given to participants and screenshots, if applicable, as well as details about compensation (if any)?

Answer: [NA]

Justification: The paper does not involve crowdsourcing nor research with human subjects.

## Guidelines:

• The answer NA means that the paper does not involve crowdsourcing nor research with human subjects.

• Including this information in the supplemental material is fine, but if the main contribution of the paper involves human subjects, then as much detail as possible should be included in the main paper.

• According to the NeurIPS Code of Ethics, workers involved in data collection, curation, or other labor should be paid at least the minimum wage in the country of the data collector.

## 15. Institutional Review Board (IRB) Approvals or Equivalent for Research with Human Subjects

Question: Does the paper describe potential risks incurred by study participants, whether such risks were disclosed to the subjects, and whether Institutional Review Board (IRB) approvals (or an equivalent approval/review based on the requirements of your country or institution) were obtained?

Answer: [NA]

Justification: The paper does not involve crowdsourcing nor research with human subjects. Guidelines:

• The answer NA means that the paper does not involve crowdsourcing nor research with human subjects.

• Depending on the country in which research is conducted, IRB approval (or equivalent) may be required for any human subjects research. If you obtained IRB approval, you should clearly state this in the paper.

• We recognize that the procedures for this may vary significantly between institutions and locations, and we expect authors to adhere to the NeurIPS Code of Ethics and the guidelines for their institution.

• For initial submissions, do not include any information that would break anonymity (if applicable), such as the institution conducting the review.