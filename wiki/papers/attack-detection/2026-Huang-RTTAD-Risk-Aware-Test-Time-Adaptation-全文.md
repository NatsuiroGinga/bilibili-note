---
title: "2026-Huang-RTTAD-Risk-Aware-Test-Time-Adaptation"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2026-Huang-RTTAD-Risk-Aware-Test-Time-Adaptation.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

Train - Normal  Test - Normal × Test - Abnormal

(c)

Pseudo NormalPseudo Abnormal

# When Normality Shifts: Risk-Aware Test-Time Adaptation for Unsupervised Tabular Anomaly Detection

Wei Huang , Hezhe Qiao , Kailai Zhang , Zaisheng Ye , Yu-Ming Shang† , Xiangling Fu†

Abstract—Unsupervised tabular anomaly detection methods typically learn feature patterns from normal samples during training and subsequently identify samples that deviate from these patterns as anomalies during testing. However, in practical scenarios, the limited scale and diversity of training data often lead to an incomplete characterization of normal patterns. While test-time adaptation offers a remedy, its isolated focus on testtime optimization ignores the critical synergy with training-phase learning. Furthermore, indiscriminate adaptation to unlabeled test data inevitably triggers anomaly contamination, preventing the model from fully realizing its discriminative capability between normal and anomalous samples. To address these issues, we propose RTTAD, a Risk-aware Test-time adaptation method for unsupervised Tabular Anomaly Detection. RTTAD holistically tackles normality shifts via a synergistic two-stage mechanism. During training, collaborative dual-task learning captures multi-level representations to establish a robust normal prior. During testing, a Test-Time Contrastive Learning (TTCL) module explicitly accounts for adaptation risk by selectively updating the model using high-confidence pseudo-normal samples while constraining anomalous ones. Additionally, TTCL incorporates a k-nearest neighbor-based contrastive objective to refine embedding distributions, thereby further enhancing the model’s discriminative capacity. Extensive experiments on 15 tabular datasets demonstrate that RTTAD achieves state-of-theart overall detection performance.

Index Terms—Tabular anomaly detection, Test-time adaptation, Normality shift, Self-supervised learning, Contrastive learning

## I. INTRODUCTION

U <sup>NSUPERVISED</sup> <sup>tabular</sup> <sup>anomaly</sup> <sup>detection</sup> <sup>plays</sup> <sup>a</sup> <sup>piv-</sup> otal role in ensuring the reliability of diverse real-world systems, such as medical diagnosis [1], network intrusion detection [2]–[4], financial fraud detection [5]–[7], and industrial inspection [8]. These unsupervised methods operate by characterizing the intrinsic feature patterns of normal samples during the training phase, and subsequently identifying instances that deviate from the established representation space as anomalies during testing.

Existing unsupervised anomaly detection methods for tabular data can be broadly classified into four categories: one-class classification methods [9], [10], clustering/feature-distributionbased methods [11]–[13], reconstruction-based methods [14], [15], and self-supervised learning methods [16]–[18]. Despite the diversity and sophistication of these design strategies, they universally rely on a rigid fundamental assumption: the normal distribution observed during testing remains strictly consistent with that encountered during training.

![](images/1c7114007d77b81d7edcef929afcebfd68e1ab23575b8fd415ad76ff7d0caeec.jpg)  
Fig. 1: Two cases of the sample distribution. (a) The normality in the test set is consistent with that in the training set. (b) The normality shift occurs between the training and test sets. (c) Our framework mitigates normality shifts by learning multilevel normal representations and performing selective, riskaware adaptation at test time.

However, in practical applications, this static assumption is frequently violated. Due to the limited scale and diversity of available training data, models often capture only a subset of the true normal manifold, resulting in an incomplete characterization of normal patterns. Consequently, when previously unseen but valid normal variations emerge at test time, a phenomenon referred to as normality shift, these representationally deficient models exhibit extreme vulnerability. Because their learned boundaries lack resilience, they erroneously flag these shifted normal instances as anomalies, leading to severe performance degradation and an unacceptable surge in false alarms. As illustrated in Figure 1, while existing unsupervised methods perform reliably under static distributions (Case a), they fail drastically when confronting normality shifts (Case b). To mitigate the impact of normality shifts, a natural intuition is to adapt the model directly to the unlabeled test data. While test-time adaptation (TTA) strategies offer a potential direction, applying them to unsupervised anomaly detection creates a severe dilemma. First, due to the lack of training supervision, the model’s initial characterization of normal patterns is often representationally deficient, leaving it highly susceptible to misguidance during adaptation. Second, and more critically, test data inherently contains unlabeled anomalies. If adaptation is performed indiscriminately across all test samples, it inevitably triggers anomaly contamination. The model blindly absorbs these anomalous patterns, rapidly and irreversibly losing its discriminative capability. Thus, achieving safe adaptation under normality shifts remains a critical bottleneck.

To address these challenges, we propose RTTAD, a Risk-aware Test-time adaptation framework for unsupervised Tabular Anomaly Detection. Unlike prior works that treat adaptation as an isolated post-hoc patch, RTTAD holistically manages distribution shifts through a synergistic two-stage paradigm. Specifically, as illustrated in Figure 1 (c), RTTAD tackles the first challenge by introducing a Collaborative Dual-task Training module. By synergizing a main feature reconstruction task with an auxiliary latent-embedding task, the model extracts multi-level feature representations. This establishes a comprehensive characterization of normality, acting as a robust anchor that reduces the risk of being misled when adapting to shifted test distributions. To resolve the second challenge, RTTAD employs a Test-Time Contrastive Learning (TTCL) module. Rather than performing indiscriminate adaptation across all test samples, TTCL executes a rigorous riskaware protocol: it selectively updates the model using highconfidence pseudo-normal samples while explicitly suppressing the influence of potentially anomalous ones. Furthermore, TTCL incorporates a k-nearest neighbor (KNN)-based contrastive objective to refine localized embedding distributions by pulling pseudo-normal samples tightly toward established normal patterns while pushing anomalies away, effectively mitigating anomaly contamination and bolstering the model’s intrinsic discriminative capability. Extensive experiments on 15 tabular datasets demonstrate that RTTAD consistently achieves state-of-the-art overall detection performance.

Our main contributions can be summarized as follows:

• We identify and formalize the phenomenon of normality shifts in unsupervised tabular anomaly detection, elucidating the inherent dilemma between mitigating distribution shifts and the critical risk of anomaly contamination during test-time adaptation.

• We propose RTTAD, a synergistic framework that bridges the training and testing phases. It establishes robust normal priors via collaborative dual-task training and performs safe, risk-aware model updates through testtime contrastive learning.

• Comprehensive evaluations on 15 tabular datasets with synthetic normality shifts demonstrate the exceptional robustness and effectiveness of the proposed method.

## II. RELATED WORK

## A. Unsupervised Tabular Anomaly Detection

Unsupervised anomaly detection, which does not rely on anomaly labels during the training phase, is one of the most practical approaches to tabular anomaly detection. Existing studies typically learn the feature patterns of normal samples during training and subsequently identify samples that deviate from the learned patterns as anomalies during testing. These methods can be broadly classified into four categories: Oneclass classification-based methods [9], [10], [19]–[22] learn a decision boundary that encloses the normal samples, classifying those that fall outside this boundary as anomalies during testing. Clustering/feature-distribution-based methods [11]– [13], [23], [24] detect anomalies by estimating the density of data points or evaluating their positions within the feature distribution. Reconstruction-based methods [14], [15], [25]– [29] learn compact embeddings to model normal feature patterns and classify samples with high reconstruction errors as anomalies. Self-supervised learning-based methods [16], [17], [30], [31] design auxiliary tasks to uncover latent data structures and patterns; samples that fail these tasks at test time are flagged as anomalies.

Although existing methods have demonstrated strong performance, they generally assume consistent normality between the training and test sets. When this assumption is violated by normality shifts, their detection performance can degrade substantially. In contrast, our method explicitly accounts for potential normality shifts. Rather than treating all deviations from the known distribution as anomalies, we introduce a riskaware test-time adaptation framework that selectively adapts the model. This fundamental difference allows our approach to maintain robust detection performance under distributional changes.

## B. Test-time Adaption

Test-time adaptation [32]–[36] aims to mitigate performance degradation under distribution shifts by enabling pre-trained models to adapt to unlabeled test data dynamically. In the realm of tabular anomaly detection, recent works such as TTAD [37] and EPHAD [38] have emerged as preliminary explorations of TTA. Specifically, TTAD generates augmented instances by retrieving the k-nearest neighbors of test samples and aggregates their predictions to alleviate shift-induced bias; meanwhile, EPHAD adopts a post-hoc calibration strategy, leveraging auxiliary classical detectors to dynamically adjust the outputs of the initial model during the testing phase, thereby reducing misclassifications.

Although these methods have achieved certain effectiveness in specific scenarios, they still exhibit several limitations. First, TTAD’s neighborhood aggregation strategy is susceptible to assimilation by surrounding dominant normal instances when anomalous samples are sparse, leading to a degradation in the model’s anomaly detection capability. Second, the posthoc calibration of EPHAD relies on the robustness of the initial detector. If the initial model suffers from an incomplete characterization of normal patterns, such limited post-hoc adjustments may fail to reverse the collapse of the model’s basic discriminative capability. More importantly, by treating adaptation merely as an isolated testing-phase patch, they overlook the intrinsic connection between the training and testing stages, making it difficult to effectively resolve the dilemma of anomaly contamination. In contrast, RTTAD tightly integrates the construction of a robust prior during the training phase with risk-aware contrastive optimization during the testing phase. It adapts to distribution shifts while explicitly suppressing anomaly contamination, effectively preserving the model’s anomaly detection capability.

![](images/c7a0533fdc69021d38a3ef77cc2daacde3d57d5430115a923624c1c893dfef38.jpg)  
Fig. 2: The framework of RTTAD. During the training phase, RTTAD employs collaborative dual-task learning to capture multi-level representations of normal samples. Specifically, the primary task reconstructs input features to extract low-level information, while the auxiliary task reconstructs latent embeddings to model high-level feature patterns. During the testing phase, the trained model is iteratively refined via the Test-Time Contrastive Learning (TTCL) module to achieve risk-aware adaptation. Specifically, TTCL selectively utilizes high-confidence pseudo-labels to guide differentiated adaptation strategies for pseudo-normal and pseudo-anomalous samples. Concurrently, a k-nearest neighbor (KNN)-based contrastive optimization is employed to further pull the representations of pseudo-normal samples toward known normal patterns while pushing pseudoanomalous representations away, thereby enhancing the model’s discriminative capability between normal and anomalous instances.

## III. METHODOLOGY

## A. Problem Statement

In this paper, we focus on unsupervised tabular anomaly detection under potential distributional changes. Given a training set $\mathcal { D } _ { t r a i n } = \{ x _ { i } ^ { t r a i n } \} _ { i = 1 } ^ { N }$ and a test set $\begin{array} { r } { \mathcal { D } _ { t e s t } = \{ x _ { i } ^ { t e s t } \} _ { i = 1 } ^ { N ^ { \prime } } , } \end{array}$ where N and $N ^ { \prime }$ represent the number of training and test samples respectively. The test set $\mathfrak { D } _ { t e s t }$ is composed of unknown normal samples and a small fraction of anomalous samples, with α denoting the contamination rate.

Traditionally, an unsupervised anomaly detection model M is trained on $\mathscr { D } _ { t r a i n }$ to learn the feature patterns of normal samples. The trained model $M _ { t r a i n }$ is then employed to predict the anomaly probabilities $P _ { a b n o r m a l }$ of test samples. This static process can be formulated as follows:

$$
M _ {t r a i n} = M (\mathcal {D} _ {t r a i n}),\tag{1}
$$

$$
P _ {a b n o r m a l} = M _ {t r a i n} (\mathcal {D} _ {t e s t}),\tag{2}
$$

$$
\mathcal {A} = \{x i ^ {t e s t} | p _ {i} \in T o p (P _ {a b n o r m a l}, \alpha), x _ {i} ^ {t e s t} \in \mathcal {D} _ {t e s t} \},\tag{3}
$$

where T op $P _ { a b n o r m a l } , \alpha )$ denotes the subset of instances with the highest anomaly probabilities corresponding to the top $\alpha \%$ . However, existing methods typically assume that the distribution of normal samples in the test set is consistent with that in the training set. In practical scenarios, this assumption is often violated due to shifts in normality. Such shifts cause the static model $M _ { t r a i n }$ to misclassify shifted normal samples as anomalies.

To alleviate this issue, we consider a test-time adaptation setting. Before generating the final predictions, the model $M _ { t r a i n }$ is further refined using the unlabeled test data $\boldsymbol { \mathcal { D } } _ { t e s t }$ to obtain an updated model $M _ { u p d a t e }$ . The objective is to enable the model to capture the evolved normal patterns while explicitly preventing the contamination of anomalous samples during the adaptation process.

## B. Overview of the Proposed RTTAD

RTTAD holistically coordinates model learning across both training and testing phases. By establishing robust normal priors during training and executing selective, risk-controlled updates during testing, the framework achieves effective adaptation to distribution shifts while explicitly suppressing anomaly contamination. Specifically, as illustrated in Figure 2, RTTAD leverages collaborative dual-task learning during the training phase to enhance the representation of normal samples. By capturing multi-level feature patterns, the model builds a comprehensive characterization of normality, which serves as a robust anchor to reduce the risk of being misled by shifted distributions in subsequent stages. During the testing phase, the Test-Time Contrastive Learning module enables adaptive model updates through iterative optimization. In this process, TTCL leverages high-confidence pseudo-labels to guide the adaptation, executing differentiated update strategies for pseudo-normal and pseudo-anomalous samples to mitigate the detrimental impact of latent anomalies on the model’s detection capability. Furthermore, by conducting knearest neighbor-based contrastive optimization in the embedding space, RTTAD pulls pseudo-normal samples toward the known normal distribution while pushing pseudo-anomalous samples away, which further enhances the model’s ability to discriminate between normal and anomalous instances. By coordinating these two stages, RTTAD effectively tackles normality shifts and and enhances the overall anomaly detection performance of the model.

## C. Collaborative Dual-task Training

The capability of a model to accurately characterize normal patterns relies on the richness of the informative features extracted during training. To establish a rich characterization of normal features under the constraints of limited scale and diversity in training data, RTTAD introduces a collaborative dual-task training module. Specifically, the implementation of this module entails two synergistic reconstruction tasks. First, it executes a primary feature reconstruction task on masked inputs to capture the low-level feature information of normal samples. Second, it introduces an auxiliary latentembedding reconstruction task to further model high-level feature representations. By comprehensively profiling normal patterns across multiple levels, this design constructs a robust representational anchor, providing a solid foundational capability for the subsequent risk-aware adaptation during the testing phase.

1) Backbone Model: The backbone of the model is a masked autoencoder. Give the input $\mathbf { X } \in \mathbb { R } ^ { B \times d }$ from the training set $\begin{array} { r } { \mathrm { ~ \mathscr { D } _ { \it t r a i n } . ~ } } \end{array}$ , B is the batch size, d denotes the dimension of the feature vector. The input X is first passed through the masked encoder $E ,$ which serves as a shared feature extractor for both tasks. This mask encoder E consists of two components: a mask generator $g _ { 1 }$ and an encoder $g _ { 2 } , E = g _ { 1 } + g _ { 2 }$ $g _ { 1 }$ produces multiple mask tensors ${ \bf { X } } _ { m a s k } = g _ { 1 } ( { \bf { X } } )$ of the same size as X, and leverage a sigmoid function to scale each value of $\mathbf { X } _ { m a s k }$ between 0 and 1. Element-wise multiplication is then applied between $\mathbf { X } _ { m a s k }$ and X, the obtained masked input is subsequently passed into $g _ { 2 }$ to obtain the masked representation $\mathbf { e } _ { m a s k } \ = \ E ( \mathbf { X } ) \ = \ g _ { 2 } ( \mathbf { X } _ { m a s k } \odot \mathbf { X } )$ in the embedding space.

Furthermore, to capture a broader spectrum of information from normal samples, we ensure sufficient diversity in the masking patterns. This is essential, as using similar masks may cause the model to learn redundant features, which not only fail to improve anomaly detection performance but may also degrade it. Inspired by MCM [17], the diversity of masking patterns is promoted by incorporating a dedicated loss function, as defined in Equation (4),

$$
\mathcal {L} _ {\mathrm{div}} = \sum_ {i = 1} ^ {T} \left[ \ln \left(\sum_ {j = 1} ^ {T} \left(\mathbb {I} _ {i \neq j} \cdot e ^ {\frac {<   \mathbf {x} _ {m a s k} ^ {i} , \mathbf {x} _ {m a s k} ^ {j} >}{\tau}}\right)\right) \cdot s \right],\tag{4}
$$

where $< >$ denotes the inner product operation, $\mathbb { I } _ { i \neq j }$ is the indicator function, $\mathrm { i f } \ i = j , \mathbb { I } _ { i \neq j } = 0$ , otherwise $\mathbb { I } _ { i \neq j } = 1 , \tau$ is a temperature parameter, and s is a scaling factor to adjust the range of the diversity loss, T denotes the number of masks.

2) Main task: learning low-level features: In the main task, the masked representation is fed into the decoder D to reconstruct the original input X, as shown in $\hat { \bf X } = D ( { \bf e } _ { m a s k } )$ By minimizing the reconstruction loss ${ \mathcal { L } } _ { m }$ between the input and its reconstruction, the model then learns low-level feature representations of the tabular data. The loss function is formulated as Equation (5):

$$
\mathcal {L} _ {m} = \frac {1}{T} \sum_ {i = 1} ^ {T} \| \hat {\mathbf {X}} _ {i} - \mathbf {X} \| ^ {2}.\tag{5}
$$

3) Auxiliary task: capturing high-level features: In the auxiliary task, the masked representation ${ \bf e } _ { m a s k }$ is fed into a multi-layer perceptron (MLP) to reconstruct the embedding e of the unmasked input. By minimizing the reconstruction loss between the predicted and original embeddings, the model captures the intrinsic knowledge embedded in the encoded representations, thereby learning high-level feature representations of the data. To ensure that e and ${ \bf e } _ { m a s k }$ have the same size, we replicate X $T$ times to match the size of $\mathbf { X } _ { m a s k } .$ and then pass the replicated input through the encoder g to obtain ${ \bf e } = g _ { 2 } ( { \bf X } _ { T } )$ , X<sub>T</sub> represents the input X that has been replicated T times. The auxiliary task is trained by minimizing the reconstruction loss ${ \mathcal { L } } _ { a }$ between the predicted embedding $\hat { \mathbf { e } } = M L P ( \mathbf { e } _ { m a s k } )$ and the embedding e. The loss function is formulated as Equation (6):

$$
\mathcal {L} _ {a} = \frac {1}{T} \sum_ {i = 1} ^ {T} \| \hat {\mathbf {e}} _ {i} - \mathbf {e} \| ^ {2}\tag{6}
$$

4) Model Training Loss: The overall training loss of the model integrates the reconstruction losses from the main and auxiliary tasks, as well as the mask diversity loss, and is formally defined as Equation (7),

$$
\mathcal {L} _ {T r a i n} = \mathcal {L} _ {m} + \lambda \mathcal {L} _ {a} + \gamma \mathcal {L} _ {d i v},\tag{7}
$$

where $\lambda$ and $\gamma$ are the weights used to adjust the overall loss function.

## D. Test-Time Contrastive Learning

In unsupervised test-time adaptation, the absence of groundtruth labels and the inevitable presence of anomalies within the test data make indiscriminate model updates highly susceptible to anomaly contamination, which can severely compromise the model’s fundamental discriminative capability. To mitigate this risk, the Test-Time Contrastive Learning (TTCL) module is designed to establish a safe and risk-aware adaptation mechanism. Specifically, the implementation of TTCL entails two key strategies. First, it filters high-confidence pseudo-normal and pseudo-anomalous samples based on the initial predictions to guide the adaptation process, executing differentiated updates to avert interference from ambiguous instances. Second, it introduces a k-nearest neighbor (KNN)-based contrastive optimization objective in the embedding space. By explicitly pulling pseudo-normal samples toward the established normal anchors and pushing pseudo-anomalous instances away, it further refines the feature representations. This design ensures that the model can adapt to normality shifts while effectively preserving and solidifying the decision boundary between normal and anomalous patterns.

1) High-Confidence Samples Selection: Given the test set $\boldsymbol { \mathcal { D } } _ { t e s t }$ , we first apply the trained model to output the losses for all test samples and normalize them into the range [0, 1]. Then the normalized losses of test samples can be regarded as their anomaly probability, as shown in Equation (8), Norm denotes the Min-Max Scaler.

$$
P _ {a b n o r m a l} = N o r m (M _ {t r a i n} (\mathcal {D} _ {t e s t}))\tag{8}
$$

Subsequently, TTCL selects the most confident normal and abnormal samples from the test set based on sorted anomaly scores, referring to them as pseudo-normal and pseudoanomalous samples. Here, $\gamma \mathrm { G M M }$ [39] is employed to adaptively estimate the confidence threshold, thereby eliminating the requirement for prior knowledge regarding the dataset’s contamination rate. The selected samples can be denoted as Equations (9) and (10),

$$
\mathcal {H} _ {n o r m a l} = \{h _ {i} ^ {n o r m a l} \} _ {i = 1} ^ {C _ {n o r m a l}}\tag{9}
$$

$$
\mathcal {H} _ {a b n o r m a l} = \{h _ {i} ^ {a b n o r m a l} \} _ {i = 1} ^ {C _ {a b n o r m a l}}\tag{10}
$$

where $\mathcal { H } _ { n o r m a l }$ represents the set of high-confidence normal samples and $\mathcal { H } _ { a b n o r m a l }$ represents the set of high-confidence abnormal samples, $C _ { n o r m a l }$ and $C _ { a b n o r m a l }$ denote the number of samples in two sets.

2) Risk-Aware Model Adaptation: At test time, TTCL adapts the model using both the main and auxiliary tasks on the selected samples, without requiring any test labels and thus avoiding label leakage. The adaptation process treats pseudo-normal and pseudo-abnormal samples differently: for pseudo-normal samples, the model is encouraged to learn their representations and reduce reconstruction errors to prevent false positives; for pseudo-abnormal samples, the adaptation is constrained to hinder accurate representation learning, ensuring that they retain high reconstruction errors and remain distinguishable as anomalies. The overall adaptation objective is summarized in Equation (11):

$$
\begin{array}{l} \mathcal {L} _ {a d a p t} = \sigma_ {s} \cdot \frac {1}{C _ {s}} \sum_ {i = 1} ^ {C _ {s}} \left(\mathcal {L} _ {m} (h _ {i} ^ {s}) + \lambda \mathcal {L} _ {a} (h _ {i} ^ {s}) + \gamma \mathcal {L} _ {\mathrm{div}}\right), \\ \sigma_ {s} = \left\{ \begin{array}{l l} + 1, & s = \text { normal } \\ - 1, & s = \text { abnormal } \end{array} \right. \end{array}\tag{11}
$$

3) Embedding Contrastive Optimization: TTCL further refines the representations of samples in embedding space by encouraging pseudo-normal samples to move closer to known normal patterns and pushing pseudo-anomalous samples away. Rather than contrasting against all known normal samples, which is inefficient and unrealistic due to the multi-pattern nature of normal data, TTCL employs a KNN-based contrastive objective that operates on local neighborhoods. This localized formulation improves both discriminative representation learning and computational efficiency. The contrastive loss is given in Equation (12),

$$
\begin{array}{c} \mathcal {L} _ {c o n t r a} = \sigma_ {s} \cdot \frac {1}{C _ {s}} \sum_ {i = 1} ^ {C _ {s}} \| h _ {i} ^ {s} - K N N (h _ {i} ^ {s}, \mathcal {O}, k) \| ^ {2}, \\ \sigma_ {s} = \left\{ \begin{array}{l l} + 1, & s = \text { normal } \\ - 1, & s = \text { abnormal } \end{array} \right. \end{array}\tag{12}
$$

where O denotes the embeddings of known normal samples, $K N N ( x , \odot , k )$ denotes finding the k-nearest embeddings to the representation of sample x from the set of known normal embeddings O.

4) Model Update Loss: For pseudo-normal or pseudoanomalous samples, the model jointly optimizes the adaptation loss and the contrastive loss during the update process. The overall loss function is defined as Equation (13),

$$
\mathcal {L} _ {U p d a t e} = \mathcal {L} _ {a d a p t} + \delta \cdot \mathcal {L} _ {c o n t r a},\tag{13}
$$

where δ is a hyperparameter to balance two losses.

5) Update Iterations: Let the initially trained model $M _ { t r a i n }$ be denoted as $M _ { u p d a t e } ^ { ( 0 ) } ,$ and let n denote the total number of update rounds. At test time, the model is iteratively refined via TTCL. Specifically, at round t, the model is updated using the current pool of selected normal samples, the updated model can be formulated as Equation (14),

$$
M _ {u p d a t e} ^ {(t)} = T T C L (M _ {u p d a t e} ^ {(t - 1)}; \mathcal {L} _ {U p d a t e}).\tag{14}
$$

After each update, newly identified high-confidence normal samples are added to the pool, as shown in Equation (15),

$$
\mathcal {O} ^ {(t)} = \mathcal {O} ^ {(t - 1)} \cup \mathcal {H} _ {n o r m a l} ^ {(t - 1)}.\tag{15}
$$

This iterative process continues until no sufficient samples remain for further selection. After the final update, the refined model $M _ { u p d a t e } ^ { ( n ) }$ is used to compute anomaly scores $P _ { \mathrm { \it t e s t } } =$ $M _ { u p d a t e } ^ { ( n ) } ( \dot { \mathcal { D } } _ { t e s t } )$ . The predicted label for each test sample is then obtained as shown in Equation (16),

$$
y _ {i} ^ {t e s t} = \mathbb {I} (p _ {i} ^ {t e s t} \geq P e r c e n t i l e (p ^ {t e s t}, \alpha),\tag{16}
$$

where $P _ { t e s t }$ denotes the anomaly scores of test samples, $y _ { i } ^ { t e s t }$ is the predicted label of sample $i , \mathbb { I } ( \cdot )$ is the indicator function, and $\bar { P e } r c e n t i l e ( p ^ { t e s t } , \alpha )$ denotes the α-percentile of $p ^ { t e s t }$

## IV. EXPERIMENTS

## A. Normality Shift Construction

Following prior works [13], [16], [17], we systematically evaluate our method on 15 commonly used tabular datasets sourced from ODDS [40] and ADBench [41]. These datasets span a wide range of domains, scales, feature dimensions, and anomaly ratios, which enhance the generality of our evaluation and strengthens the reliability of the conclusions. Detailed statistics of datasets are provided in Table I.

TABLE I: The statistics of datasets.

<table><tr><td>Dataset</td><td>Samples</td><td>Dim</td><td>Anomaly</td><td>Category</td></tr><tr><td>Arrhythmia</td><td>452</td><td>274</td><td>66 (15%)</td><td>Healthcare</td></tr><tr><td>BreastW</td><td>683</td><td>9</td><td>239 (35%)</td><td>Healthcare</td></tr><tr><td>Cardio</td><td>1831</td><td>21</td><td>176 (9.6%)</td><td>Healthcare</td></tr><tr><td>Cardiotocography</td><td>2114</td><td>21</td><td>466 (22.04%)</td><td>Healthcare</td></tr><tr><td>Glass</td><td>214</td><td>9</td><td>9 (4.2%)</td><td>Forensic</td></tr><tr><td>Ionosphere</td><td>351</td><td>33</td><td>126 (36%)</td><td>Oryctognosy</td></tr><tr><td>Mammography</td><td>11183</td><td>6</td><td>260 (2.32%)</td><td>Healthcare</td></tr><tr><td>Optdigits</td><td>5216</td><td>64</td><td>150 (2.88%)</td><td>Image</td></tr><tr><td>Pendigits</td><td>6870</td><td>16</td><td>156 (2.27%)</td><td>Image</td></tr><tr><td>Pima</td><td>768</td><td>8</td><td>268 (35%)</td><td>Healthcare</td></tr><tr><td>Satellite</td><td>6435</td><td>36</td><td>2036 (32%)</td><td>Astronautics</td></tr><tr><td>Satimage-2</td><td>5803</td><td>36</td><td>71 (1.2%)</td><td>Astronautics</td></tr><tr><td>Thyroid</td><td>3772</td><td>6</td><td>93 (2.5%)</td><td>Healthcare</td></tr><tr><td>Wbc</td><td>278</td><td>30</td><td>21 (5.6%)</td><td>Healthcare</td></tr><tr><td>Wine</td><td>129</td><td>13</td><td>10 (7.75%)</td><td>Chemistry</td></tr></table>

Second, to simulate distribution shifts within the normal data, we synthetically construct these shifts by applying K-Means clustering exclusively to the normal samples of each dataset. Specifically, samples from the largest cluster are partitioned into both training and test sets, whereas normal samples from the remaining clusters, along with all anomalous samples, are strictly assigned to the test set. Consequently, the test set comprises normal samples that conform to the training distribution as well as those that deviate from it. To rigorously validate the rationality of this construction, we adopt the evaluation protocol established in the prior study [42], conducting comprehensive qualitative and quantitative analyses. This involves utilizing t-SNE visualization, Jeffreys Divergence (JD), and Optimal Transport Dataset Distance (OTDD). Notably, JD quantifies feature-wise distribution discrepancies via normalized histograms, while OTDD captures the geometric divergence between datasets within the original feature space. As illustrated in Figure 3, the normal samples in the test set exhibit a conspicuous distributional shift relative to the training set, a qualitative observation that is further corroborated by the JD and OTDD scores in Table II.

TABLE II: The results of Jeffreys Divergence (JD) and Optimal Transport Dataset Distance (OTDD) between the distributions of normal samples in the training and test sets across all datasets.

<table><tr><td>Metrics</td><td>arrhythmia</td><td>breastw</td><td>cardio</td><td>cardiotocography</td><td>glass</td></tr><tr><td>JD</td><td>1.39</td><td>0.48</td><td>1.72</td><td>0.46</td><td>1.28</td></tr><tr><td>OTDD</td><td>0.31</td><td>0.24</td><td>0.29</td><td>0.14</td><td>0.15</td></tr><tr><td>Metrics</td><td>ionosphere</td><td>mammography</td><td>optdigits</td><td>pendigits</td><td>pima</td></tr><tr><td>JD</td><td>9.08</td><td>2.40</td><td>0.19</td><td>0.80</td><td>1.65</td></tr><tr><td>OTDD</td><td>0.39</td><td>0.09</td><td>0.55</td><td>0.49</td><td>0.16</td></tr><tr><td>Metrics</td><td>satellite</td><td>satimage-2</td><td>thyroid</td><td>wbc</td><td>wine</td></tr><tr><td>JD</td><td>3.23</td><td>2.83</td><td>0.37</td><td>4.17</td><td>15.43</td></tr><tr><td>OTDD</td><td>0.01</td><td>0.33</td><td>0.24</td><td>0.25</td><td>0.27</td></tr></table>

## B. Experimental Setup

1) Baselines: To comprehensively evaluate the proposed approach, we benchmark it against fifteen representative baselines. These comprise thirteen standard anomaly detection methods (IForest, LOF, OCSVM, DeepSVDD, ECOD, GOAD, NeuTral AD, ICL, DIF, SLAD, LUNAR, MCM, DRL) and two recent test-time adaptation approaches (TTAD and EPHAD). The core concepts of these methods are briefly summarized as follows:

• IForest [43] isolates anomalies by recursively partitioning the data using random splits. The core idea is that anomalies are easier to isolate due to their distinctiveness, requiring fewer partitions compared to normal data points, and this isolation process is used to identify anomalies.

• LOF [23] evaluates the local density of data points by comparing the density of a point with that of its neighbors. Points with significantly lower density than their neighbors are considered anomalies, as they deviate from the expected local structure of the data.

• OCSVM [9] constructs a hyperplane in a highdimensional space that maximizes the margin around the normal data. This results in the majority of data points being mapped within the boundary, while points that deviate significantly from this boundary are identified as anomalies.

• DeepSVDD [10] learns a deep feature representation of the data while simultaneously minimizing the volume of a hypersphere that encloses the normal data. Data points that lie outside this learned hypersphere are detected as anomalies.

• ECOD [13] leverages the empirical cumulative distribution function (ECDF) to detect anomalies. For each feature in the dataset, ECOD computes the ECDF, which captures the data’s distributional properties in a robust and interpretable manner. Points that fall in the extreme tails of the distribution are assigned higher anomaly scores.

• GOAD [30] generalizes the class of transformation functions to include affine transformation which allows it to generalize to non-image data. By applying these transformations to the input data, GOAD trains a classifier to distinguish between the transformed versions. At test time, normal data will exhibit predictable patterns under these transformations, while abnormal data fails to conform to these patterns, making it easier to be identified.

• NeuTral AD [31] learns a set of neural transformations, parameterized by neural networks, which map the input data to various transformed spaces and capture the intrinsic structure of normal data. During the testing phase, samples that do not follow the learned patterns are detected as anomalies.

• ICL [16] employs contrastive loss to learn mappings that maximize the mutual information between each sample and the part that is masked out and capture the structure of the samples of the single training class. Test samples are scored by measuring whether the learned mappings lead to a small contrastive loss using the masked parts of this sample. Samples with high loss values are regarded as anomalies.

![](images/c45ddf0850b7504e52a800692e8caa628a8bab0542f179cd089cc5e9daa73225.jpg)  
Fig. 3: Comparison of normal sample distributions between the training and test sets for each dataset, along with the distribution of the i-th feature.

• DIF [44] uses randomly initialized neural networks to create random representation ensembles. Through random axis-parallel cuts on these representations, it realizes nonlinear partitioning in the original space. With CERE for efficient feature mapping and DEAS combining path length and feature deviation, DIF scores anomalies via isolation tree ensembles.

• SLAD [45] introduces scale learning for tabular anomaly detection, defining ”scale” as the dimensionality relationship between data sub-vectors and their representations. It uses a neural network to learn distribution alignment of subspace transformations via Jensen-Shannon divergence loss, modeling inlier structural regularities. Test instances are scored by divergence from learned scale distributions, high loss indicates anomalies.

• LUNAR [46] reframes local outlier detection as a GNN message-passing problem, where samples are nodes connected to k-nearest neighbors. It replaces fixed aggregation rules with learnable neural aggregation and trains with synthetic negatives, enabling adaptive, robust anomaly detection.

• TTAD [37] reduces prediction bias in tabular test-time augmentation by retrieving a test sample’s nearest neighbors via an adaptive Siamese distance metric, and utilizing SMOTE or k-Means centroids to generate diverse and in-distribution augmented samples.

• EPHAD [38] mitigates the performance degradation caused by data contamination by dynamically calibrating anomaly scores in a post-hoc manner, combining the prior scores of a pre-trained model with auxiliary test-time evidence such as classical anomaly detectors.

• MCM [17] adapts mask modeling to address the problem of tabular data anomaly detection. Mask generator and autoencoder are employed to capture intrinsic correlations between features existing in training tabular data and model the “characteristic patterns” by such correlations. Samples that deviate from these correlations are predicted as anomalies.

DRL [18] tackles tabular anomaly detection by mapping data into a constrained latent space, where each normal sample is represented as a weighted linear combination of fixed orthogonal basis vectors. It enhances discriminability by increasing the variance of normal weights and preserves feature correlations via alignment loss.

2) Evaluation Metrics: Following established evaluation protocols in recent literature [16]–[18], we employ AUC-PR, AUC-ROC, and the F1-score to comprehensively assess the detection performance.

3) Implementation details: Implementation Details. All models are implemented in PyTorch [47] and executed on a single NVIDIA GeForce RTX 2080 Ti GPU. During the training phase, the models are optimized for 200 epochs using the Adam optimizer with a batch size of 512 and a weight decay of $1 \times 1 0 ^ { - 5 }$ . We employ the ExponentialLR scheduler with a decay factor of 0.98. During inference, the parameter k is set to 3 across all datasets. To adaptively balance the weights between the main and auxiliary tasks across varying datasets, the hyperparameter λ is dynamically set to min $( 1 . 0 , 1 . 0 / \mathcal { L } _ { m } )$ The hyperparameter γ follows the configuration in MCM [17], and δ is set to 1 by default. For the baseline methods, iForest, LOF, OCSVM, DeepSVDD, ECOD, and LUNAR are implemented via the PyOD library [48], while DIF, GOAD, NeuTral AD, ICL, and SLAD utilize the DeepOD library [22], [44]. TTAD, EPHAD, MCM and DRL are executed using their official open-source implementations. To ensure statistical reliability, the reported results for the main and ablation experiments are averaged over three independent runs, whereas the remaining experiments report single-run outcomes.

TABLE III: Comparison of AUC-PR(↑)results between baseline methods and RTTAD on 15 datasets.

<table><tr><td></td><td>Iforest</td><td>LOF</td><td>OCSVM</td><td>DeepSVDD</td><td>ECOD</td><td>GOAD</td><td>NeuTraLAD</td><td>ICL</td><td>DIF</td><td>SLAD</td><td>LUNAR</td><td>TTAD</td><td>EPHAD</td><td>MCM</td><td>DRL</td><td>RTTAD</td></tr><tr><td>arrhythmia</td><td>0.6019</td><td>0.5676</td><td>0.6111</td><td>0.6115</td><td>0.6244</td><td>0.5867</td><td>0.5023</td><td>0.5407</td><td>0.6294</td><td>0.5372</td><td>0.5856</td><td>0.5519</td><td>0.6411</td><td>0.5657</td><td>0.5510</td><td>0.6212</td></tr><tr><td>breastw</td><td>0.8536</td><td>0.7818</td><td>0.7656</td><td>0.8256</td><td>0.7581</td><td>0.9860</td><td>0.5662</td><td>0.8508</td><td>0.9737</td><td>0.9569</td><td>0.9644</td><td>0.9836</td><td>0.8588</td><td>0.9911</td><td>0.9302</td><td>0.9921</td></tr><tr><td>cardio</td><td>0.5381</td><td>0.5581</td><td>0.5835</td><td>0.4407</td><td>0.6860</td><td>0.4606</td><td>0.2458</td><td>0.3687</td><td>0.6176</td><td>0.4277</td><td>0.4782</td><td>0.6156</td><td>0.5846</td><td>0.6849</td><td>0.4054</td><td>0.6385</td></tr><tr><td>cardiotocography</td><td>0.5529</td><td>0.5562</td><td>0.6531</td><td>0.5417</td><td>0.6120</td><td>0.3408</td><td>0.3746</td><td>0.4113</td><td>0.4944</td><td>0.3255</td><td>0.4604</td><td>0.5321</td><td>0.5155</td><td>0.4051</td><td>0.3682</td><td>0.3906</td></tr><tr><td>glass</td><td>0.1721</td><td>0.3482</td><td>0.3472</td><td>0.5118</td><td>0.1658</td><td>0.0994</td><td>0.1201</td><td>0.2309</td><td>0.1013</td><td>0.1105</td><td>0.5750</td><td>0.2134</td><td>0.1204</td><td>0.1099</td><td>0.1191</td><td>0.1504</td></tr><tr><td>ionosphere</td><td>0.8094</td><td>0.8032</td><td>0.8094</td><td>0.7772</td><td>0.6842</td><td>0.6543</td><td>0.6337</td><td>0.6063</td><td>0.8097</td><td>0.7038</td><td>0.8241</td><td>0.9708</td><td>0.8170</td><td>0.7504</td><td>0.8282</td><td>0.7552</td></tr><tr><td>mammography</td><td>0.2713</td><td>0.4927</td><td>0.4582</td><td>0.4812</td><td>0.4862</td><td>0.3293</td><td>0.0563</td><td>0.1560</td><td>0.4507</td><td>0.1467</td><td>0.4962</td><td>0.0861</td><td>0.3530</td><td>0.4781</td><td>0.1022</td><td>0.5407</td></tr><tr><td>optdigits</td><td>0.3311</td><td>0.5605</td><td>0.5290</td><td>0.0348</td><td>0.0373</td><td>0.0640</td><td>0.0528</td><td>0.0725</td><td>0.0647</td><td>0.0690</td><td>0.5526</td><td>0.1296</td><td>0.0538</td><td>0.1103</td><td>0.0997</td><td>0.4199</td></tr><tr><td>pendigits</td><td>0.3430</td><td>0.5283</td><td>0.5162</td><td>0.1523</td><td>0.4147</td><td>0.0445</td><td>0.0362</td><td>0.0431</td><td>0.5583</td><td>0.0475</td><td>0.5288</td><td>0.0944</td><td>0.2744</td><td>0.0430</td><td>0.0333</td><td>0.0964</td></tr><tr><td>pima</td><td>0.7448</td><td>0.7441</td><td>0.7763</td><td>0.6826</td><td>0.7113</td><td>0.5587</td><td>0.5373</td><td>0.5787</td><td>0.5943</td><td>0.5902</td><td>0.6611</td><td>0.5733</td><td>0.6344</td><td>0.5707</td><td>0.5347</td><td>0.5921</td></tr><tr><td>satellite</td><td>0.7169</td><td>0.7177</td><td>0.7173</td><td>0.6894</td><td>0.6437</td><td>0.7595</td><td>0.8306</td><td>0.7927</td><td>0.7173</td><td>0.8339</td><td>0.6926</td><td>0.8472</td><td>0.7020</td><td>0.8199</td><td>0.8400</td><td>0.8307</td></tr><tr><td>satimage-2</td><td>0.5006</td><td>0.5013</td><td>0.5094</td><td>0.5129</td><td>0.5931</td><td>0.6819</td><td>0.8071</td><td>0.9461</td><td>0.9754</td><td>0.9588</td><td>0.5114</td><td>0.9552</td><td>0.5800</td><td>0.9717</td><td>0.0925</td><td>0.9716</td></tr><tr><td>thyroid</td><td>0.6202</td><td>0.4433</td><td>0.4208</td><td>0.3091</td><td>0.5818</td><td>0.1503</td><td>0.1919</td><td>0.1677</td><td>0.2379</td><td>0.4751</td><td>0.5032</td><td>0.1846</td><td>0.2834</td><td>0.2925</td><td>0.0629</td><td>0.7773</td></tr><tr><td>wbc</td><td>0.6235</td><td>0.5745</td><td>0.6175</td><td>0.5703</td><td>0.5609</td><td>0.5047</td><td>0.2311</td><td>0.5735</td><td>0.4594</td><td>0.2623</td><td>0.6094</td><td>0.5239</td><td>0.4526</td><td>0.7268</td><td>0.4460</td><td>0.8147</td></tr><tr><td>wine</td><td>0.5627</td><td>0.5781</td><td>0.5610</td><td>0.5641</td><td>0.3177</td><td>0.9909</td><td>0.9667</td><td>0.8813</td><td>0.8112</td><td>0.9573</td><td>0.6667</td><td>0.8967</td><td>0.1998</td><td>0.9909</td><td>0.9430</td><td>0.9909</td></tr><tr><td>Average PR</td><td>0.5494</td><td>0.5837</td><td>0.5917</td><td>0.5136</td><td>0.5251</td><td>0.4808</td><td>0.4102</td><td>0.4814</td><td>0.5664</td><td>0.4935</td><td>0.6073</td><td>0.5439</td><td>0.4714</td><td>0.5674</td><td>0.4238</td><td>0.6388</td></tr><tr><td>Average Ranking</td><td>7.73</td><td>7.07</td><td>7.13</td><td>9.20</td><td>8.47</td><td>10.33</td><td>12.33</td><td>10.53</td><td>7.33</td><td>10.07</td><td>6.33</td><td>7.27</td><td>8.47</td><td>7.47</td><td>11.27</td><td>4.87</td></tr></table>

TABLE IV: Comparison of AUC-ROC(↑)results between baseline methods and RTTAD on 15 datasets.

<table><tr><td></td><td>Iforest</td><td>LOF</td><td>OCSVM</td><td>DeepSVDD</td><td>ECOD</td><td>GOAD</td><td>NeuTraLAD</td><td>ICL</td><td>DIF</td><td>SLAD</td><td>LUNAR</td><td>TTAD</td><td>EPHAD</td><td>MCM</td><td>DRL</td><td>RTTAD</td></tr><tr><td>arrhythmia</td><td>0.7229</td><td>0.6797</td><td>0.5</td><td>0.5022</td><td>0.7175</td><td>0.7694</td><td>0.7127</td><td>0.7115</td><td>0.8167</td><td>0.7227</td><td>0.7089</td><td>0.7866</td><td>0.8248</td><td>0.7629</td><td>0.7345</td><td>0.8190</td></tr><tr><td>breastw</td><td>0.8111</td><td>0.6469</td><td>0.5973</td><td>0.7557</td><td>0.5725</td><td>0.9814</td><td>0.6669</td><td>0.8860</td><td>0.9640</td><td>0.9467</td><td>0.9609</td><td>0.9779</td><td>0.7801</td><td>0.9936</td><td>0.9660</td><td>0.9933</td></tr><tr><td>cardio</td><td>0.5943</td><td>0.6497</td><td>0.6929</td><td>0.6019</td><td>0.8388</td><td>0.6489</td><td>0.5901</td><td>0.6479</td><td>0.9244</td><td>0.7109</td><td>0.5633</td><td>0.8691</td><td>0.9002</td><td>0.6849</td><td>0.6418</td><td>0.8199</td></tr><tr><td>cardiotocography</td><td>0.4837</td><td>0.4760</td><td>0.5018</td><td>0.5480</td><td>0.6695</td><td>0.4619</td><td>0.4829</td><td>0.4679</td><td>0.7682</td><td>0.4554</td><td>0.4094</td><td>0.5737</td><td>0.6032</td><td>0.6476</td><td>0.4843</td><td>0.6402</td></tr><tr><td>glass</td><td>0.4249</td><td>0.5437</td><td>0.5384</td><td>0.6466</td><td>0.5236</td><td>0.5390</td><td>0.6194</td><td>0.6147</td><td>0.4031</td><td>0.6017</td><td>0.7287</td><td>0.8074</td><td>0.5525</td><td>0.6190</td><td>0.6076</td><td>0.7021</td></tr><tr><td>ionosphere</td><td>0.6587</td><td>0.6407</td><td>0.6587</td><td>0.5501</td><td>0.5664</td><td>0.6288</td><td>0.6342</td><td>0.6371</td><td>0.7559</td><td>0.6885</td><td>0.7048</td><td>0.9546</td><td>0.7177</td><td>0.7885</td><td>0.8112</td><td>0.7446</td></tr><tr><td>mammography</td><td>0.4956</td><td>0.5918</td><td>0.8010</td><td>0.5835</td><td>0.7321</td><td>0.8618</td><td>0.6944</td><td>0.8014</td><td>0.8561</td><td>0.7547</td><td>0.5898</td><td>0.6479</td><td>0.8371</td><td>0.8635</td><td>0.7139</td><td>0.8970</td></tr><tr><td>optdigits</td><td>0.6219</td><td>0.7765</td><td>0.5</td><td>0.465</td><td>0.4839</td><td>0.5949</td><td>0.4924</td><td>0.645</td><td>0.5466</td><td>0.6240</td><td>0.7386</td><td>0.7794</td><td>0.5088</td><td>0.8295</td><td>0.7441</td><td>0.9460</td></tr><tr><td>pendigits</td><td>0.6461</td><td>0.6945</td><td>0.8033</td><td>0.5252</td><td>0.6298</td><td>0.6016</td><td>0.5021</td><td>0.5763</td><td>0.9446</td><td>0.5895</td><td>0.6666</td><td>0.7907</td><td>0.8916</td><td>0.6447</td><td>0.4586</td><td>0.7313</td></tr><tr><td>pima</td><td>0.5626</td><td>0.5662</td><td>0.5</td><td>0.4893</td><td>0.4893</td><td>0.5769</td><td>0.5122</td><td>0.4813</td><td>0.5084</td><td>0.5574</td><td>0.5579</td><td>0.5324</td><td>0.5809</td><td>0.5251</td><td>0.6127</td><td>0.4798</td></tr><tr><td>satellite</td><td>0.5634</td><td>0.5694</td><td>0.5</td><td>0.6331</td><td>0.6086</td><td>0.7155</td><td>0.7912</td><td>0.7756</td><td>0.6738</td><td>0.8006</td><td>0.5747</td><td>0.7911</td><td>0.6441</td><td>0.8065</td><td>0.7992</td><td>0.8143</td></tr><tr><td>satimage-2</td><td>0.6724</td><td>0.6866</td><td>0.5</td><td>0.8799</td><td>0.9124</td><td>0.9640</td><td>0.9960</td><td>0.9958</td><td>0.9973</td><td>0.9972</td><td>0.5893</td><td>0.9936</td><td>0.9692</td><td>0.9986</td><td>0.7863</td><td>0.9985</td></tr><tr><td>thyroid</td><td>0.9196</td><td>0.5951</td><td>0.6239</td><td>0.5618</td><td>0.8092</td><td>0.6534</td><td>0.7277</td><td>0.6166</td><td>0.8838</td><td>0.8444</td><td>0.6500</td><td>0.7257</td><td>0.9298</td><td>0.7696</td><td>0.5262</td><td>0.9630</td></tr><tr><td>wbc</td><td>0.8289</td><td>0.7866</td><td>0.8372</td><td>0.7382</td><td>0.7694</td><td>0.9032</td><td>0.7881</td><td>0.9234</td><td>0.8877</td><td>0.8139</td><td>0.7995</td><td>0.8940</td><td>0.8329</td><td>0.9643</td><td>0.8887</td><td>0.9723</td></tr><tr><td>wine</td><td>0.7736</td><td>0.6250</td><td>0.5</td><td>0.5278</td><td>0.5875</td><td>0.9986</td><td>0.9931</td><td>0.9889</td><td>0.9542</td><td>0.9944</td><td>0.8611</td><td>0.9828</td><td>0.6241</td><td>0.9988</td><td>0.9931</td><td>0.9986</td></tr><tr><td>Average ROC</td><td>0.6520</td><td>0.6352</td><td>0.6036</td><td>0.6006</td><td>0.6665</td><td>0.7223</td><td>0.6782</td><td>0.7198</td><td>0.7956</td><td>0.7402</td><td>0.6714</td><td>0.8071</td><td>0.7465</td><td>0.7990</td><td>0.7090</td><td>0.8408</td></tr><tr><td>Average Ranking</td><td>10.40</td><td>10.87</td><td>11.27</td><td>12.60</td><td>10.07</td><td>8.20</td><td>10.47</td><td>9.07</td><td>6.00</td><td>7.67</td><td>10.20</td><td>5.60</td><td>8.07</td><td>3.80</td><td>8.80</td><td>2.73</td></tr></table>

TABLE V: Comparison of F1(↑)results between baseline methods and RTTAD on 15 datasets.

<table><tr><td></td><td>Iforest</td><td>LOF</td><td>OCSVM</td><td>DeepSVDD</td><td>ECOD</td><td>GOAD</td><td>NeuTraLAD</td><td>ICL</td><td>DIF</td><td>SLAD</td><td>LUNAR</td><td>TTAD</td><td>EPHAD</td><td>MCM</td><td>DRL</td><td>RTTAD</td></tr><tr><td>arrhythmia</td><td>0.5466</td><td>0.4842</td><td>0.3636</td><td>0.3646</td><td>0.5691</td><td>0.5909</td><td>0.5303</td><td>0.4697</td><td>0.5909</td><td>0.5152</td><td>0.5325</td><td>0.5909</td><td>0.6212</td><td>0.5</td><td>0.5</td><td>0.5455</td></tr><tr><td>breastw</td><td>0.8284</td><td>0.721</td><td>0.6938</td><td>0.7888</td><td>0.6809</td><td>0.9665</td><td>0.6360</td><td>0.7876</td><td>0.9436</td><td>0.8852</td><td>0.9590</td><td>0.9456</td><td>0.7322</td><td>0.9540</td><td>0.9205</td><td>0.9582</td></tr><tr><td>cardio</td><td>0.2964</td><td>0.3319</td><td>0.3628</td><td>0.3051</td><td>0.6509</td><td>0.5170</td><td>0.2670</td><td>0.4545</td><td>0.5909</td><td>0.4830</td><td>0.2773</td><td>0.6023</td><td>0.5454</td><td>0.3239</td><td>0.3864</td><td>0.6023</td></tr><tr><td>cardiotocography</td><td>0.4218</td><td>0.4203</td><td>0.4704</td><td>0.4433</td><td>0.5435</td><td>0.3004</td><td>0.3305</td><td>0.3004</td><td>0.5365</td><td>0.2961</td><td>0.3374</td><td>0.4270</td><td>0.4785</td><td>0.3584</td><td>0.3348</td><td>0.4099</td></tr><tr><td>glass</td><td>0.0870</td><td>0.1724</td><td>0.1695</td><td>0.2192</td><td>0.1250</td><td>0.</td><td>0.</td><td>0.2222</td><td>0.1111</td><td>0.</td><td>0.2609</td><td>0.1111</td><td>0.1111</td><td>0.</td><td>0.</td><td>0.1111</td></tr><tr><td>ionosphere</td><td>0.7654</td><td>0.7561</td><td>0.7654</td><td>0.7143</td><td>0.5398</td><td>0.5635</td><td>0.6190</td><td>0.5952</td><td>0.6746</td><td>0.6270</td><td>0.7871</td><td>0.8810</td><td>0.6746</td><td>0.6349</td><td>0.7143</td><td>0.6508</td></tr><tr><td>mammography</td><td>0.0664</td><td>0.0853</td><td>0.2836</td><td>0.0839</td><td>0.1340</td><td>0.4154</td><td>0.0038</td><td>0.2192</td><td>0.4692</td><td>0.1577</td><td>0.0848</td><td>0.0615</td><td>0.3615</td><td>0.4923</td><td>0.1</td><td>0.5407</td></tr><tr><td>optdigits</td><td>0.1709</td><td>0.2158</td><td>0.1095</td><td>0.0059</td><td>0.0081</td><td>0.</td><td>0.</td><td>0.02</td><td>0.04</td><td>0.</td><td>0.1905</td><td>0.1400</td><td>0.0200</td><td>0.0200</td><td>0.0133</td><td>0.4733</td></tr><tr><td>pendigits</td><td>0.1317</td><td>0.1181</td><td>0.1906</td><td>0.0817</td><td>0.3574</td><td>0.</td><td>0.</td><td>0.0256</td><td>0.5256</td><td>0.0385</td><td>0.1089</td><td>0.0449</td><td>0.3461</td><td>0.0064</td><td>0.0192</td><td>0.1154</td></tr><tr><td>pima</td><td>0.6689</td><td>0.6667</td><td>0.7118</td><td>0.5709</td><td>0.5738</td><td>0.5746</td><td>0.5522</td><td>0.5448</td><td>0.5821</td><td>0.5784</td><td>0.4847</td><td>0.5896</td><td>0.6082</td><td>0.5149</td><td>0.5373</td><td>0.5858</td></tr><tr><td>satellite</td><td>0.6261</td><td>0.6286</td><td>0.6059</td><td>0.6144</td><td>0.5171</td><td>0.6051</td><td>0.7194</td><td>0.6685</td><td>0.5953</td><td>0.7083</td><td>0.6102</td><td>0.7107</td><td>0.5997</td><td>0.7141</td><td>0.7269</td><td>0.7210</td></tr><tr><td>satimage-2</td><td>0.0561</td><td>0.0585</td><td>0.0369</td><td>0.1723</td><td>0.4710</td><td>0.6620</td><td>0.8592</td><td>0.9014</td><td>0.9577</td><td>0.9014</td><td>0.0446</td><td>0.8873</td><td>0.5492</td><td>0.9296</td><td>0.1268</td><td>0.9296</td></tr><tr><td>thyroid</td><td>0.4674</td><td>0.0975</td><td>0.1084</td><td>0.0942</td><td>0.5660</td><td>0.1398</td><td>0.1828</td><td>0.1613</td><td>0.1935</td><td>0.4516</td><td>0.1093</td><td>0.1720</td><td>0.3225</td><td>0.2903</td><td>0.0430</td><td>0.6667</td></tr><tr><td>wbc</td><td>0.3962</td><td>0.3725</td><td>0.4301</td><td>0.3077</td><td>0.5306</td><td>0.5238</td><td>0.2381</td><td>0.6667</td><td>0.5238</td><td>0.1905</td><td>0.3590</td><td>0.5238</td><td>0.4285</td><td>0.6667</td><td>0.5238</td><td>0.7143</td></tr><tr><td>wine</td><td>0.5</td><td>0.2703</td><td>0.2174</td><td>0.2273</td><td>0.2727</td><td>0.9</td><td>0.9</td><td>0.9</td><td>0.6</td><td>0.9</td><td>0.5</td><td>0.8</td><td>0.3</td><td>0.9</td><td>0.9</td><td>0.9</td></tr><tr><td>Average F1</td><td>0.4020</td><td>0.3599</td><td>0.3680</td><td>0.3329</td><td>0.4360</td><td>0.4506</td><td>0.3892</td><td>0.4625</td><td>0.5290</td><td>0.4489</td><td>0.3764</td><td>0.4992</td><td>0.4466</td><td>0.4870</td><td>0.3898</td><td>0.5953</td></tr><tr><td>Average Ranking</td><td>8.33</td><td>9.20</td><td>9.27</td><td>10.80</td><td>8.27</td><td>9.00</td><td>11.40</td><td>8.60</td><td>6.00</td><td>9.40</td><td>9.33</td><td>6.27</td><td>7.53</td><td>7.93</td><td>9.60</td><td>4.20</td></tr></table>

## C. Main Results

RTTAD achieves the state-of-the-art overall detection performance. The detailed quantitative results of all evaluated methods in terms of AUC-PR, AUC-ROC, and the F1-score are tabulated in Tables III to V, respectively. These results demonstrate that the proposed RTTAD yields the most competitive overall detection performance across all 15 datasets.

To facilitate a straightforward visual comparison of the respective methods, we provide box plots to illustrate the distribution and stability of the detection performance for each approach across all datasets. Figure 4 summarizes the AUC-PR and AUC-ROC results of 16 methods evaluated on 15 datasets. Subfigures (a) and (b) present the distributions of AUC-PR and AUC-ROC across datasets, respectively, while subfigures (c) and (d) show the corresponding ranking distributions. Overall, RTTAD achieves the best average performance across datasets under both metrics. In particular, RTTAD outperforms the strongest baseline by 3.15% in AUC-PR, with an average ranking improvement of 1.46 positions, and by 3.37% in AUC-ROC, with an average ranking improvement of 1.07 positions. Figure 5 reports the F1-score performance of different methods. Subfigures (a) and (b) show the distribution of F1 scores across all datasets and the corresponding ranking distributions, respectively. Overall, RTTAD achieves the best average F1 performance, surpassing the second-best method by 9.61%, with an average ranking improvement of 2.07 positions. Subfigures (c) and (d) employ the Wilcoxon signed-rank test [49] (with α = 0.05) to assess the statistical significance of the improvements. Statistical tests reveal that, at a 95% confidence level, RTTAD achieves statistically significant performance gains compared to 11 out of the 15 baselines.

![](images/d5c870b1497d8ae9792f00198996d8a15bd47bf8258ec492792b46a2de085926.jpg)

![](images/7c0b2e6da5d1607c75400fe64341eeecbfc242337889ba7057989b94fb650f4e.jpg)

![](images/72932b775455f2a53aaa8c25a31cf7462734c54319a86949ac4249bd8b2d18a0.jpg)

![](images/95958c89003dca95753fbc94815a74c9f3899bf8efc67f760b8bfd20dce1aa1d.jpg)

Fig. 4: Comparison of all models’ performance and ranking across different datasets in terms of AUC-PR and AUC-ROC. The triangles represent the average value over all datasets. The dark blue lines in (a) and (b) indicate the confidence intervals of the method’s performance.  
![](images/80c6cf0081b266f07857e6db1086beabd20ffc6e90207cd0f43b8ce32dd2fb60.jpg)

![](images/8d406a7d4a55c91f681eaa837a6933f8b4391ff33994fa6f9c3a5604cfe71f83.jpg)

![](images/d89ce1ab6cc84410ba7ae471e87459350c8b2fd5a99b859909af2bd18c2a3570.jpg)

![](images/e5ec1cfa3e91d22372700ac92c697fe7d0992b2f8035ea0ca5e3ff8a624c7545.jpg)  
Fig. 5: Comparison of F1 scores. (a) and (b) compare the F1 scores and rankings of all models across different datasets, where the triangles denote the averages over all datasets, and the dark blue lines in (a) indicate the confidence intervals of the method’s performance. (c) and (d) conduct Wilcoxon tests across models and datasets. Blue cells indicate corresponding p-values below 0.05 (significant), while white cells indicate p-values above 0.05 (not significant).

Existing unsupervised tabular anomaly detection methods are inherently vulnerable to normality shifts due to their strict reliance on consistent data distributions. Specifically, unsupervised methods rely on the strong assumption of consistent normal patterns between the training and test sets, limiting their detection efficacy in practical scenarios. Although state-of-the-art detection methods, such as MCM and DRL, have demonstrated exceptional detection capabilities through sophisticated designs in representation learning and feature decoupling, their performance undergoes drastic fluctuations when the normal distribution of the test set deviates from that of the training set. In contrast, by synergizing multilevel feature capture during the training phase with a dynamic model adaptation mechanism during the testing phase, RTTAD effectively mitigates the performance degradation induced by normality shifts, thereby achieving superior and more robust overall detection performance.

Test-time adaptation methods exhibit superior overall detection performance compared to unsupervised anomaly de tection methods, yet they lack a unified consideration of both the training and testing phases. The fact that TTAD and EPHAD generally outperform MCM and DRL across all three evaluation metrics indicates that mitigating normality shifts yields tangible performance gains. However, their performance still lags behind that of our proposed RTTAD. Specifically, TTAD generates diverse instances by simulating a subset of k-nearest neighbors for a given sample and then aggregating their predictions to mitigate shift-induced prediction bias. While this strategy proves effective on datasets with high anomaly ratios, it critically falters when anomalies are sparse (e.g., mammography and thyroid). In such scenarios, the knearest neighbor aggregation tends to skew excessively toward normal predictions, masking the detection of latent anomalies and consequently degrading performance. EPHAD, which employs post-hoc calibration to adjust the initial detector’s predictions, achieves commendable overall performance but remains heavily bottlenecked by the initial detector. When the initial detector suffers severe performance degradation due to distribution shifts on certain datasets, the post-hoc calibration is insufficient to salvage the detection efficacy. In contrast, RT-TAD leverages multi-level features during the training phase to enhance the model’s feature extraction capability, laying a solid foundation for subsequent model adaptation. Furthermore, it introduces a risk-aware test-time contrastive learning module during the testing phase, differentially treating latent normal and anomalous samples to avert adaptation failure. By holistically coordinating the training and testing phases, RTTAD achieves substantially superior detection performance over both TTAD and EPHAD.

## D. Analysis of Pseudo-Label Noise Impact.

TABLE VI: True rate of pseudo labels in early iterations (true rate of normal labels-true rate of abnormal labels).

<table><tr><td>Dataset</td><td>iter 1</td><td>iter 2</td><td>iter 3</td><td>iter 4</td></tr><tr><td>pendigits</td><td>1.00-0.07</td><td>1.00-0.00</td><td>1.00-0.00</td><td>1.00-0.00</td></tr><tr><td>cardiotocography</td><td>0.98-0.59</td><td>0.75-0.52</td><td>0.96-0.24</td><td>0.74-0.67</td></tr><tr><td>cardio</td><td>1.00-0.88</td><td>1.00-0.82</td><td>1.00-0.76</td><td>0.91-0.88</td></tr><tr><td>breastw</td><td>1.00-1.00</td><td>1.00-1.00</td><td>1.00-1.00</td><td>1.00-1.00</td></tr></table>

TABLE VII: Average detection performance across 15 datasets under different forget rates for filtering pseudo-label noise.

<table><tr><td>Forget rate</td><td>auc-roc</td><td>auc-pr</td><td>pr</td></tr><tr><td>0%</td><td>0.8408</td><td>0.6388</td><td>0.5953</td></tr><tr><td>10%</td><td>0.7710</td><td>0.5829</td><td>0.5351</td></tr><tr><td>20%</td><td>0.8201</td><td>0.6296</td><td>0.5729</td></tr><tr><td>30%</td><td>0.7774</td><td>0.5875</td><td>0.5318</td></tr><tr><td>40%</td><td>0.8290</td><td>0.6630</td><td>0.6221</td></tr></table>

In the TTCL module of RTTAD, pseudo-labels are assigned to samples with high-confidence predictions. To examine whether noisy pseudo-labels lead to persistent performance degradation during test-time adaptation, we select four datasets (pendigits, cardiotocography, cardio, and breastw) with markedly different overall performance and track the accuracy of pseudo-labels during the early adaptation iterations. The statistical results are summarized in Table VI. We observe that pseudo-label accuracy exhibits fluctuations rather than a monotonic decline, indicating that labeling errors are not continuously amplified during adaptation. Moreover, even on the pendigits dataset, where RTTAD achieves the weakest performance and the true anomaly rate eventually drops to zero, the final detection results of RTTAD still surpass those of most baseline methods. These observations suggest that: (1) pseudo-label noise does not cause persistent degradation during test-time adaptation; and (2) despite the presence of noisy pseudo-labels, the benefits of selectively leveraging them outweigh their potential drawbacks in handling normality shifts.

Furthermore, we explore a co-teaching mechanism in which two lightweight MLPs collaboratively select low-loss samples to mitigate pseudo-label noise. As detailed in Table VII, we evaluate the model under varying forget rates of 10%,

20%, 30%, and 40%. Interestingly, increasing the forget rate does not monotonically improve performance; this is likely attributable to the fact that the supplementary supervision introduced by the co-teaching models may inherently propagate errors and misclassify certain pseudo-labels. Nevertheless, setting the forget rate to 40% yields the highest average performance across all 15 datasets, demonstrating that effectively reducing pseudo-label noise can further boost detection efficacy. These findings suggest that developing more robust and reliable pseudo-label refinement strategies constitutes a promising avenue for future research.

## E. Ablation Study.

To rigorously validate the efficacy of each core component within RTTAD, we design four variants for our ablation study:

• w/o aux: Removes the auxiliary feature reconstruction task during both the training and testing phases, aiming to evaluate the contribution of multi-level feature capture to detection performance.

• w/o TTCL: Removes the entire test-time contrastive learning module, thereby regressing the framework to a static detector, to verify whether test-time distribution adaptation effectively mitigates the performance degradation inherent in static models.

• w/o adapt: Adapts the model solely to the current test samples during the testing phase without retaining the previously learned normal patterns, exploring whether the absence of explicit constraints triggers catastrophic forgetting.

• w/o contra: Eliminates the KNN-based contrastive optimization within the embedding space during testtime adaptation, investigating whether the pseudo-labelguided representation optimization genuinely bolsters the model’s capability to discriminate between normal and anomalous samples.

The detailed quantitative results of these ablation experiments are tabulated in Table VIII. The full RTTAD framework consistently achieves the best performance across all evaluation metrics. Through an in-depth comparative analysis, we draw the following key conclusions. First, the performance drop observed in w/o aux indicates that the multi-level features provided by the auxiliary task are crucial for establishing a robust initial representation of normal patterns, serving as the solid foundation for subsequent test-time adaptation. Second, the performance of w/o TTCL corroborates that when confronted with distribution shifts, static models struggle to identify anomalies effectively and inevitably suffer from performance degradation, whereas test-time adaptation can restore and enhance the model’s discriminative capability. Most importantly, the detection performance of both w/o adapt and w/o contra is substantially inferior even to that of w/o TTCL, which performs no adaptation at all. This phenomenon underscores the paramount importance of accounting for the presence of latent anomalies and the forgetting of prior knowledge during the testing phase. Blind adaptation devoid of risk awareness will severely compromise the model’s intrinsic detection capability.

TABLE VIII: The evaluation results of ablation experiments across the datasets.

<table><tr><td rowspan="2"></td><td colspan="3">w/o aux</td><td colspan="3">w/o contra</td><td colspan="3">w/o adapt</td><td colspan="3">w/o TTCL</td><td colspan="3">RTTAD</td></tr><tr><td>auc-roc</td><td>auc-pr</td><td>f1</td><td>auc-roc</td><td>auc-pr</td><td>f1</td><td>auc-roc</td><td>auc-pr</td><td>f1</td><td>auc-roc</td><td>auc-pr</td><td>f1</td><td>auc-roc</td><td>auc-pr</td><td>f1</td></tr><tr><td>arrhythmia</td><td>0.5808</td><td>0.5295</td><td>0.4394</td><td>0.6195</td><td>0.5795</td><td>0.5152</td><td>0.4509</td><td>0.4032</td><td>0.303</td><td>0.7437</td><td>0.5612</td><td>0.5</td><td>0.819</td><td>0.6212</td><td>0.5455</td></tr><tr><td>breastw</td><td>0.9833</td><td>0.9882</td><td>0.9414</td><td>0.9856</td><td>0.9897</td><td>0.9582</td><td>0.9841</td><td>0.9886</td><td>0.9498</td><td>0.99</td><td>0.9882</td><td>0.9498</td><td>0.9933</td><td>0.9921</td><td>0.9582</td></tr><tr><td>cardio</td><td>0.7744</td><td>0.6366</td><td>0.5966</td><td>0.7283</td><td>0.6246</td><td>0.5966</td><td>0.7309</td><td>0.6382</td><td>0.5852</td><td>0.7106</td><td>0.2561</td><td>0.2273</td><td>0.8199</td><td>0.6385</td><td>0.6023</td></tr><tr><td>cardiotocography</td><td>0.3707</td><td>0.3575</td><td>0.279</td><td>0.3122</td><td>0.3368</td><td>0.2725</td><td>0.2981</td><td>0.3231</td><td>0.2618</td><td>0.5941</td><td>0.3853</td><td>0.3691</td><td>0.6402</td><td>0.3906</td><td>0.4099</td></tr><tr><td>glass</td><td>0.2726</td><td>0.0858</td><td>0.1111</td><td>0.083</td><td>0.0649</td><td>0.</td><td>0.2756</td><td>0.0797</td><td>0.</td><td>0.6974</td><td>0.1596</td><td>0.2222</td><td>0.7021</td><td>0.1504</td><td>0.1111</td></tr><tr><td>ionosphere</td><td>0.5012</td><td>0.5321</td><td>0.627</td><td>0.7009</td><td>0.7124</td><td>0.6905</td><td>0.4966</td><td>0.53</td><td>0.6429</td><td>0.715</td><td>0.7432</td><td>0.6349</td><td>0.7446</td><td>0.7552</td><td>0.6508</td></tr><tr><td>mammography</td><td>0.7249</td><td>0.1763</td><td>0.2577</td><td>0.7954</td><td>0.1955</td><td>0.2769</td><td>0.8856</td><td>0.5099</td><td>0.5692</td><td>0.8658</td><td>0.5074</td><td>0.5192</td><td>0.897</td><td>0.5407</td><td>0.5462</td></tr><tr><td>optdigits</td><td>0.2723</td><td>0.037</td><td>0.</td><td>0.3683</td><td>0.0425</td><td>0.</td><td>0.6349</td><td>0.0705</td><td>0.</td><td>0.8171</td><td>0.1337</td><td>0.0733</td><td>0.946</td><td>0.4199</td><td>0.4733</td></tr><tr><td>pendigits</td><td>0.9471</td><td>0.7146</td><td>0.6731</td><td>0.7514</td><td>0.0814</td><td>0.</td><td>0.8837</td><td>0.2974</td><td>0.3526</td><td>0.4142</td><td>0.0378</td><td>0.0192</td><td>0.7313</td><td>0.0964</td><td>0.1154</td></tr><tr><td>pima</td><td>0.4721</td><td>0.5484</td><td>0.4851</td><td>0.478</td><td>0.55</td><td>0.4813</td><td>0.4704</td><td>0.5493</td><td>0.4851</td><td>0.592</td><td>0.6311</td><td>0.6045</td><td>0.5724</td><td>0.5921</td><td>0.5858</td></tr><tr><td>satellite</td><td>0.6171</td><td>0.7131</td><td>0.5319</td><td>0.4813</td><td>0.7486</td><td>0.5648</td><td>0.5581</td><td>0.6679</td><td>0.4641</td><td>0.8054</td><td>0.8409</td><td>0.7279</td><td>0.8143</td><td>0.8307</td><td>0.721</td></tr><tr><td>satimage-2</td><td>0.9876</td><td>0.945</td><td>0.9014</td><td>0.9855</td><td>0.9383</td><td>0.9014</td><td>0.9934</td><td>0.9385</td><td>0.8794</td><td>0.9983</td><td>0.9718</td><td>0.9296</td><td>0.9985</td><td>0.9716</td><td>0.9296</td></tr><tr><td>thyroid</td><td>0.7541</td><td>0.3503</td><td>0.3333</td><td>0.4189</td><td>0.0638</td><td>0.043</td><td>0.2801</td><td>0.0349</td><td>0.</td><td>0.864</td><td>0.3749</td><td>0.3763</td><td>0.963</td><td>0.7773</td><td>0.6667</td></tr><tr><td>wbc</td><td>0.9448</td><td>0.718</td><td>0.7143</td><td>0.9448</td><td>0.718</td><td>0.7143</td><td>0.9448</td><td>0.718</td><td>0.7143</td><td>0.9356</td><td>0.6493</td><td>0.6667</td><td>0.9723</td><td>0.8147</td><td>0.7143</td></tr><tr><td>wine</td><td>0.9983</td><td>0.9909</td><td>0.9</td><td>0.9983</td><td>0.9909</td><td>0.9</td><td>0.9983</td><td>0.9909</td><td>0.9</td><td>0.9986</td><td>0.9909</td><td>0.9</td><td>0.9986</td><td>0.9909</td><td>0.9</td></tr><tr><td>Average value</td><td>0.6800</td><td>0.5548</td><td>0.5194</td><td>0.6434</td><td>0.5091</td><td>0.4609</td><td>0.6590</td><td>0.5160</td><td>0.4738</td><td>0.7827</td><td>0.5487</td><td>0.5146</td><td>0.8408</td><td>0.6388</td><td>0.5953</td></tr></table>

## F. Parameter Sensitivity Analysis.

![](images/1f7a556b772f07c724cb809210c02d446e1097f83a639fa1a25d06e8a0925273.jpg)

![](images/6ee61b823c994f6d7e3dc244b5644ed15f18d435776721c0cd6d789dd69bc53b.jpg)  
Fig. 6: Average detection performance across 15 datasets under different parameter settings

We conducted a parameter sensitivity analysis with respect to two key factors: the value of K used in the KNN-based contrastive learning module, and the weighting coefficients of the adaptation loss and contrastive loss. The resulting performance trends are presented in Figure 6.

Sensitivity to Neighborhood Size K. The model achieves peak performance across all metrics at $K = 3 .$ , maintains high stability within $K \in [ 5 , 1 0 ]$ , and exhibits a slight decline at $K = 1 5$ . This trend is intuitive: a smaller K precisely captures the highly localized manifold structure of normal samples, avoiding the erroneous forced alignment of distinct normal clusters. Conversely, given the multi-pattern nature of normal data, an excessively large K inadvertently incorporates crosscluster noise, which blurs representation boundaries and compromises the model’s discriminative capability. Consequently, $K = 3$ is adopted as the default configuration to strike the optimal balance.

Sensitivity to Loss Weights. Let a denote the weight of $\mathcal { L } _ { a d a p t }$ and c denote the weight of $\mathcal { L } _ { c o n t r a }$ . The AUC-ROC, AUC-PR, and F1 scores exhibit consistency across all configurations, yielding nearly flat trajectories. This profound indicates a synergy between the adaptation and contrastive objectives, corroborating that RTTAD’s superiority is driven by its core architectural design rather than meticulous hyperparameter tuning. Such insensitivity to weight variations alleviates the tuning burden in practical unsupervised scenarios devoid of validation data, demonstrating the framework’s robustness and utility.

## V. CONCLUSION

In this paper, we investigate the severe performance degradation of unsupervised tabular anomaly detection when confronting normality shifts at test time. Existing static methods suffer from an incomplete characterization of normality, rendering them highly vulnerable when normal patterns evolve. Furthermore, we demonstrate that directly applying indiscriminate test-time adaptation inevitably triggers catastrophic anomaly contamination due to the lack of reliable supervision and the inherent presence of latent anomalies. To address this dilemma, we propose RTTAD, a risk-aware test-time adaptation framework that holistically manages distribution shifts through a synergistic two-stage paradigm. During the training phase, RTTAD utilizes collaborative dual-task learning to capture multi-level representations, establishing a robust anchor of normal patterns. During the testing phase, it executes a rigorous risk-controlled adaptation via test-time contrastive learning. This mechanism safely adapts to shifted normal distributions while explicitly suppressing anomaly contamination to bolster the model’s intrinsic discriminative capability. Extensive experiments on both synthetic and temporally evolving normality shifts demonstrate that RTTAD consistently achieves state-of-the-art robust detection performance. Future work will explore more reliable pseudo-label refinement and dynamic risk estimation strategies to further enhance the safety of testtime adaptation in open-world scenarios.

## ACKNOWLEDGMENTS

This work was supported by the National Natural Science Foundation of China (No.72274022 & No.6240073908), the Beijing Natural Science Foundation (No.4244083) and the Fundamental Research Funds for the Central Universities (No.500422828).

## REFERENCES

[1] T. Fernando, H. Gammulle, S. Denman, S. Sridharan, and C. Fookes, “Deep learning for medical anomaly detection–a survey,” ACM Computing Surveys (CSUR), vol. 54, no. 7, pp. 1–37, 2021.

[2] H. Qiao and G. Pang, “Truncated affinity maximization: One-class homophily modeling for graph anomaly detection,” Advances in Neural Information Processing Systems, vol. 36, pp. 49 490–49 512, 2023.

[3] H. Qiao, Q. Wen, X. Li, E.-P. Lim, and G. Pang, “Generative semisupervised graph anomaly detection,” in Advances in Neural Information Processing Systems, 2024.

[4] C. Niu, H. Qiao, C. Chen, L. Chen, and G. Pang, “Zero-shot generalist graph anomaly detection with unified neighborhood prompts,” arXiv preprint arXiv:2410.14886, 2024.

[5] K. G. Al-Hashedi and P. Magalingam, “Financial fraud detection applying data mining techniques: A comprehensive review from 2009 to 2019,” Computer Science Review, vol. 40, p. 100402, 2021.

[6] H. Qiao, H. Tong, B. An, I. King, C. Aggarwal, and G. Pang, “Deep graph anomaly detection: A survey and new perspectives,” arXiv preprint arXiv:2409.09957, 2024.

[7] H. Qiao, C. Niu, L. Chen, and G. Pang, “Anomalygfm: Graph foundation model for zero/few-shot anomaly detection,” arXiv preprint arXiv:2502.09254, 2025.

[8] J. Liu, G. Xie, J. Wang, S. Li, C. Wang, F. Zheng, and Y. Jin, “Deep industrial image anomaly detection: A survey,” Machine Intelligence Research, vol. 21, no. 1, pp. 104–135, 2024.

[9] B. Scholkopf, R. C. Williamson, A. Smola, J. Shawe-Taylor, and J. Platt,¨ “Support vector method for novelty detection,” Advances in neural information processing systems, vol. 12, 1999.

[10] L. Ruff, R. Vandermeulen, N. Goernitz, L. Deecke, S. A. Siddiqui, A. Binder, E. Muller, and M. Kloft, “Deep one-class classification,”¨ in International conference on machine learning. PMLR, 2018, pp. 4393–4402.

[11] B. Liu, P.-N. Tan, and J. Zhou, “Unsupervised anomaly detection by robust density estimation,” in Proceedings of the AAAI Conference on Artificial Intelligence, vol. 36, 2022, pp. 4101–4108.

[12] M. Ali, P. Scandurra, F. Moretti, and H. H. R. Sherazi, “Anomaly detection in public street lighting data using unsupervised clustering,” IEEE Transactions on Consumer Electronics, 2024.

[13] Z. Li, Y. Zhao, X. Hu, N. Botta, C. Ionescu, and G. H. Chen, “Ecod: Unsupervised outlier detection using empirical cumulative distribution functions,” IEEE Transactions on Knowledge and Data Engineering, vol. 35, no. 12, pp. 12 181–12 193, 2022.

[14] T. Schlegl, P. Seebock, S. M. Waldstein, U. Schmidt-Erfurth, and¨ G. Langs, “Unsupervised anomaly detection with generative adversarial networks to guide marker discovery,” in International conference on information processing in medical imaging. Springer, 2017, pp. 146– 157.

[15] D. Gong, L. Liu, V. Le, B. Saha, M. R. Mansour, S. Venkatesh, and A. v. d. Hengel, “Memorizing normality to detect anomaly: Memoryaugmented deep autoencoder for unsupervised anomaly detection,” in Proceedings of the IEEE/CVF international conference on computer vision, 2019, pp. 1705–1714.

[16] T. Shenkar and L. Wolf, “Anomaly detection for tabular data with internal contrastive learning,” in International conference on learning representations, 2022.

[17] J. Yin, Y. Qiao, Z. Zhou, X. Wang, and J. Yang, “Mcm: Masked cell modeling for anomaly detection in tabular data,” in The Twelfth International Conference on Learning Representations, 2024.

[18] H. Ye, H. Zhao, W. Fan, M. Zhou, D. dan Guo, and Y. Chang, “Drl: Decomposed representation learning for tabular anomaly detection,” in The Thirteenth International Conference on Learning Representations, 2025.

[19] D. M. Tax and R. P. Duin, “Support vector data description,” Machine learning, vol. 54, pp. 45–66, 2004.

[20] S. Goyal, A. Raghunathan, M. Jain, H. V. Simhadri, and P. Jain, “Drocc: Deep robust one-class classification,” in International conference on machine learning. PMLR, 2020, pp. 3711–3721.

[21] F. V. Massoli, F. Falchi, A. Kantarci, S¸ . Akti, H. K. Ekenel, and G. Amato, “Mocca: Multilayer one-class classification for anomaly detection,” IEEE transactions on neural networks and learning systems, vol. 33, no. 6, pp. 2313–2323, 2021.

[22] H. Xu, Y. Wang, S. Jian, Q. Liao, Y. Wang, and G. Pang, “Calibrated one-class classification for unsupervised time series anomaly detection,” IEEE Transactions on Knowledge and Data Engineering, 2024.

[23] M. M. Breunig, H.-P. Kriegel, R. T. Ng, and J. Sander, “Lof: identifying density-based local outliers,” in Proceedings of the 2000 ACM SIGMOD international conference on Management of data, 2000, pp. 93–104.

[24] B. Zong, Q. Song, M. R. Min, W. Cheng, C. Lumezanu, D. Cho, and H. Chen, “Deep autoencoding gaussian mixture model for unsupervised anomaly detection,” in International conference on learning representations, 2018.

[25] T. Schlegl, P. Seebock, S. M. Waldstein, G. Langs, and U. Schmidt-¨ Erfurth, “f-anogan: Fast unsupervised anomaly detection with generative adversarial networks,” Medical image analysis, vol. 54, pp. 30–44, 2019.

[26] V. Zavrtanik, M. Kristan, and D. Skocaj, “Draem-a discriminativelyˇ trained reconstruction embedding for surface anomaly detection,” in Proceedings of the IEEE/CVF international conference on computer vision, 2021, pp. 8330–8339.

[27] M. Z. Zaheer, A. Mahmood, M. H. Khan, M. Segu, F. Yu, and S.-I. Lee, “Generative cooperative learning for unsupervised video anomaly detection,” in Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, 2022, pp. 14 744–14 754.

[28] X. Zhang, N. Li, J. Li, T. Dai, Y. Jiang, and S.-T. Xia, “Unsupervised surface anomaly detection with diffusion probabilistic model,” in Proceedings of the IEEE/CVF International Conference on Computer Vision, 2023, pp. 6782–6791.

[29] J. Guo, L. Jia, W. Zhang, H. Li et al., “Recontrast: Domain-specific anomaly detection via contrastive reconstruction,” Advances in Neural Information Processing Systems, vol. 36, 2024.

[30] L. Bergman and Y. Hoshen, “Classification-based anomaly detection for general data,” arXiv preprint arXiv:2005.02359, 2020.

[31] C. Qiu, T. Pfrommer, M. Kloft, S. Mandt, and M. Rudolph, “Neural transformation learning for deep anomaly detection beyond images,” in International conference on machine learning. PMLR, 2021, pp. 8703– 8714.

[32] X. Liu, X. Liu, B. Hu, W. Ji, F. Xing, J. Lu, J. You, C.-C. J. Kuo, G. El Fakhri, and J. Woo, “Subtype-aware unsupervised domain adaptation for medical diagnosis,” in Proceedings of the AAAI conference on artificial intelligence, vol. 35, 2021, pp. 2189–2197.

[33] Y. Liu, P. Kothari, B. Van Delft, B. Bellot-Gurlet, T. Mordan, and A. Alahi, “Ttt++: When does self-supervised test-time training fail or thrive?” Advances in Neural Information Processing Systems, vol. 34, pp. 21 808–21 820, 2021.

[34] M. Shu, W. Nie, D.-A. Huang, Z. Yu, T. Goldstein, A. Anandkumar, and C. Xiao, “Test-time prompt tuning for zero-shot generalization in vision-language models,” Advances in Neural Information Processing Systems, vol. 35, pp. 14 274–14 289, 2022.

[35] M. Jang, S.-Y. Chung, and H. W. Chung, “Test-time adaptation via self-training with nearest neighbor information,” in The International Conference on Learning Representations, ICLR 2023. The International Conference on Learning Representations (ICLR), 2023.

[36] D. Kim, S. Park, and J. Choo, “When model meets new normals: Test-time adaptation for unsupervised time-series anomaly detection,” in Proceedings of the AAAI Conference on Artificial Intelligence, vol. 38, 2024, pp. 13 113–13 121.

[37] S. Cohen, N. Goldshlager, L. Rokach, and B. Shapira, “Boosting anomaly detection using unsupervised diverse test-time augmentation,” Information Sciences, vol. 626, pp. 821–836, 2023.

[38] S. Patra and S. B. Taieb, “An evidence-based post-hoc adjustment framework for anomaly detection under data contamination,” in The Thirtyninth Annual Conference on Neural Information Processing Systems, 2025.

[39] L. Perini, P.-C. Burkner, and A. Klami, “Estimating the contamination¨ factor’s distribution in unsupervised anomaly detection,” in International Conference on Machine Learning. PMLR, 2023, pp. 27 668–27 679.

[40] S. Rayana, “Odds library,” 2016. [Online]. Available: https://odds.cs. stonybrook.edu

[41] S. Han, X. Hu, H. Huang, M. Jiang, and Y. Zhao, “Adbench: Anomaly detection benchmark,” Advances in Neural Information Processing Systems, vol. 35, pp. 32 142–32 159, 2022.

[42] M. Dragoi, E. Burceanu, E. Haller, A. Manolache, and F. Brad, “Anoshift: A distribution shift benchmark for unsupervised anomaly detection,” Advances in Neural Information Processing Systems, vol. 35, pp. 32 854–32 867, 2022.

[43] F. T. Liu, K. M. Ting, and Z.-H. Zhou, “Isolation forest,” in 2008 eighth ieee international conference on data mining. IEEE, 2008, pp. 413–422.

[44] H. Xu, G. Pang, Y. Wang, and Y. Wang, “Deep isolation forest for anomaly detection,” IEEE Transactions on Knowledge and Data Engineering, vol. 35, no. 12, pp. 12 591–12 604, 2023.

[45] H. Xu, Y. Wang, J. Wei, S. Jian, Y. Li, and N. Liu, “Fascinating supervisory signals and where to find them: Deep anomaly detection with scale learning,” in International Conference on Machine Learning. PMLR, 2023, pp. 38 655–38 673.

[46] A. Goodge, B. Hooi, S.-K. Ng, and W. S. Ng, “Lunar: Unifying local outlier detection methods via graph neural networks,” in Proceedings of the AAAI Conference on Artificial Intelligence, vol. 36, 2022, pp. 6737–6745.

[47] A. Paszke, S. Gross, F. Massa, A. Lerer, J. Bradbury, G. Chanan, T. Killeen, Z. Lin, N. Gimelshein, L. Antiga et al., “Pytorch: An imperative style, high-performance deep learning library,” Advances in neural information processing systems, vol. 32, 2019.

[48] Y. Zhao, Z. Nasrullah, and Z. Li, “Pyod: A python toolbox for scalable outlier detection,” Journal of machine learning research, vol. 20, no. 96, pp. 1–7, 2019.

[49] R. F. Woolson, “Wilcoxon signed-rank test,” Wiley encyclopedia of clinical trials, pp. 1–3, 2007.