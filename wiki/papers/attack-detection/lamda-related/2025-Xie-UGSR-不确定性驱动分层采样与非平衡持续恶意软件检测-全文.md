---
title: "2025-Xie-UGSR-不确定性驱动分层采样与非平衡持续恶意软件检测"
date: 2026-10-15
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/lamda-related/2025-Xie-UGSR-不确定性驱动分层采样与非平衡持续恶意软件检测.pdf"
---

> 本文件由 `mineru-open-api extract` 机械转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片未落库（不保存 PDF 转换中间文件），正文中的图片引用链接已剥离。
# Uncertainty-Driven Hierarchical Sampling for Unbalanced Continual Malware Detection with Time-Series Update-Based Retrieval

Yi Xie, Ziyuan Yang, Yongqiang Huang, Yinyu Chen, Lei Zhang, Liang Liu, Yi Zhang, Senior Member, IEEE,

Abstract—Android malware detection continues to face persistent challenges stemming from long-term concept drift and class imbalance, as evolving malicious behaviors and shifting usage patterns dynamically reshape feature distributions. Although continual learning (CL) mitigates drift, existing replay-based methods suffer from inherent bias. Specifically, their reliance on classifier uncertainty for sample selection disproportionately prioritizes the dominant benign class, causing overfitting and reduced generalization to evolving malware. To address these limitations, we propose a novel uncertainty-guided CL framework. First, we introduce a hierarchical balanced sampler that employs a dual-phase uncertainty strategy to dynamically balance benign and malicious samples while simultaneously selecting high-information, high-uncertainty instances within each class. This mechanism ensures class equilibrium across both replay and incremental data, thereby enhancing adaptability to emerging threats. Second, we augment the framework with a vector retrieval mechanism that exploits historical malware embeddings to identify evolved variants via similarity-based retrieval, thereby complementing classifier updates. Extensive experiments demonstrate that our framework significantly outperforms stateof-the-art methods under strict low-label conditions (50 labels per phase). It achieves a true positive rate (TPR) of 92.95% and a mean accuracy (mACC) of 94.26%, which validates its efficacy for sustainable Android malware detection.

Index Terms—Continue Learning Few-shot Learning Uncertainty Sampling Malware Detection.

## I. INTRODUCTION

defenses. While machine learning-based Android malware detection models have achieved notable success in static evaluations, their performance often degrades over time due to concept drift. This degradation arises as both malicious and benign software behaviors evolve dynamically. Malware developers employ techniques such as polymorphic obfuscation, dynamic payload injection, and API call pattern mutation to evade detection, whereas benign applications continually introduce new features through regular updates, thereby altering their observable characteristics. Addressing these evolving distributions necessitates malware detectors that can continually adapt in order to sustain robust performance over time.

Continual learning (CL) has emerged as a promising solution for sustainable Android malware detection, which enables models to be incrementally updated as new data becomes available. Previous works, such as that by Chen et al. [1], have investigated the integration of contrastive learning with active learning for sample selection, which aims to preserve detection accuracy during continual updates. Nevertheless, these methods encounter inherent limitations, primarily because they rely on classifier uncertainty or pseudo-loss scores as the principal criteria for sample selection during incremental updates.

One of the major challenges inadequately addressed by existing methods is the severe class imbalance in real-world Android malware detection [2], [3], where benign samples vastly outnumber their malicious counterparts. Uncertaintydriven sample selection methods inherently bias toward the benign majority, as these samples dominate the feature space and influence uncertainty estimates. This bias leads to suboptimal replay sets, overfitting to benign classes, and degraded capacity to generalize against emerging malware behaviors.

To overcome these limitations, we propose a novel Uncertainty-Guided Sampling and Retrieval (UGSR) framework for continual Android malware detection. Specifically, UGSR introduces two core innovations: one to balance class distributions during the sampling stage and another to enhance adaptability to evolving malware during the detection stage.

For the sampling stage, we propose a hierarchical uncertainty sampling strategy that decouples the sampling process from the core detection model. Unlike conventional binary sampling methods that only distinguish between malicious and benign instances, our hierarchical sampler additionally operates on fine-grained malware family classes alongside benign applications. By independently estimating uncertainty at both the multi-class and binary levels, our hierarchical sampler ensures the selection of high-information and highuncertainty samples, while simultaneously maintaining class balance. Furthermore, the hierarchical design enhances intraclass diversity, especially among malware families, thereby ensuring a more representative and informative sample set for continual updates.

At the detection stage, we introduce an adaptive vector retrieval mechanism that reformulates the detection task as a similarity-based retrieval problem. By constructing and continuously updating a class-balanced codebook that contains only the top 50 representative benign and malware embeddings, the system can detect evolved malware variants via vector similarity rather than solely relying on classifier predictions. To further improve retrieval robustness, we incorporate the Equiangular Tight Frame (ETF) principle to maximize interclass separation and promote intra-class compactness within the codebook, reducing false positives and enhancing detection accuracy.

In summary, the main contributions of this work are as follows:

• We propose UGSR, a novel continual learning framework that decouples uncertainty-guided sample selection from Android malware detection, mitigating the limitations of shared-network approaches and improving detection robustness.

• We introduce a hierarchical uncertainty sampling strategy that dynamically balances benign and malware classes while enhancing intra-class diversity, effectively addressing the class imbalance problem in continual Android malware detection.

• We develop an adaptive vector retrieval mechanism with evolutionary codebook update and ETF-based feature regularization, which enables effective detection of malware variants while reducing false positives.

## II. RELATED WORKS

## A. Uncertainty sampling

Uncertainty sampling is a foundational technique in active learning, aimed at selecting the most informative samples by quantifying model uncertainty in its predictions. Traditional methods such as entropy-based sampling [4], least confidence [5], and margin sampling [6] have been widely adopted in image classification and text processing tasks. For instance, Settles et al. [5] demonstrated that margin-based selection accelerates model convergence by focusing on samples near decision boundaries.

With the advent of deep learning, uncertainty estimation methods have evolved. Gal et al. [6] introduced Monte Carlo Dropout to approximate Bayesian uncertainty in neural networks, which enables efficient sample selection in image segmentation. Similarly, Beluch et al. [7] showed that ensemble-based methods outperform single-model approaches in medical image analysis, highlighting the importance of model diversity.

Recent studies have explored hybrid uncertainty sampling strategies. Gissin et al. [8] combined discriminative models with uncertainty-driven sampling to reduce annotation costs in object detection tasks. Do et al. [9] leveraged adversarial perturbations to identify uncertain regions in latent spaces for semi-supervised learning. Extending these ideas to continual learning, Ahn et al. [10] proposed incorporating temporal consistency metrics to adapt uncertainty sampling to dynamic data streams. This approach addresses concept drift and provides particularly valuable insights to evolve Android malware detection, as subsequently validated in Barbero et al. [11].

However, most existing uncertainty sampling methods focus on static domains, such as image or text classification. Their direct application to sequential, non-visual tasks like Android malware detection remains underexplored, especially when considering challenges such as extreme class imbalance and the need for long-term adaptability.

## B. Continual learning

Continual learning (CL), also known as incremental learning, addresses the challenge of updating models on nonstationary data streams while mitigating catastrophic forgetting. Classic CL approaches include regularization-based methods, such as EWC [12], which preserves important parameters from previous tasks, and architectural strategies like Progressive Neural Networks [13], which expand model capacity incrementally. Rehearsal-based techniques, such as iCaRL [14], leverage exemplar storage to preserve information from past classes.

Recent CL methods predominantly focus on balancing model adaptability and memory efficiency. DER [15] dynamically expands feature representations for new tasks while freezing older parameters, whereas PODNet [16] employs distillation loss to preserve knowledge across incremental phases.

In the context of Android malware detection, continual learning is critical due to the rapid evolution of threats. Pang et al. [17] introduced a rehearsal-based CL framework for malware classification that utilizes a small memory buffer to preserve representative samples from older families. Shin et al. [18] proposed a meta-incremental approach that trains models to generalize better to unseen malware classes while addressing inherent class imbalance. Gong et al. [19] integrated adversarial training with knowledge distillation to enhance model robustness against evolving features.

Despite these advances, most CL methods for malware detection focus primarily on class-incremental scenarios and often overlook the interplay between feature drift, class imbalance, and temporal dependency in malware behaviors. This gap motivates the development of our framework’s dual-level uncertainty-guided sampling and retrieval mechanism, which explicitly addresses these challenges.

## C. Continual few-shot learning for malware detection

Few-shot class-incremental learning (FSCIL) has garnered increasing attention as a promising paradigm for real-world malware detection, where labeled data is scarce and new threat variants continuously emerge [28], [29]. While initially introduced by Tao et al. [28] for general incremental learning scenarios, FSCIL faces unique challenges when adapted to Android malware detection, due to the dynamic nature of cyber threats and the severe scarcity of labeled attack samples.

Several FSCIL methods have been proposed to mitigate catastrophic forgetting and feature drift. TOPIC [28] leverages a growing neural gas network to model feature topology, which preserves learned representations while incorporating new threat classes. FSLL [30] reduces computational overhead by selectively updating only a subset of model parameters during incremental phases, which is crucial for resourceconstrained Android malware detection systems. By enhancing feature scalability, SPRR [31] effectively supports incremental learning systems - a critical capability given malware authors rapidly adapting attack strategies. Additionally, Cheraghian et al. [32] introduced semantically informed embeddings to improve knowledge retention for known malware families, which mitigates forgetting in long-term learning scenarios.

Despite these advances, applying FSCIL to Android malware detection remains challenging. Frameworks such as IMC have demonstrated the feasibility of classifying unknown malware classes while maintaining accuracy on known threats. However, IMC and similar approaches are limited to singlesession incremental learning and fail to fully address the continuous, long-term evolution of malware families. Unlike applications in image recognition [33]–[36] or vehicle recognition [37], Android malware detection faces unique challenges, such as decision boundary confusion caused by polymorphic malware variants and catastrophic forgetting of older malware families over extended learning cycles.

Most existing FSCIL methods show promising results in controlled settings but struggle to maintain stability and accuracy under real-world conditions, where new malware variants emerge frequently and labeled samples are scarce. This persistent gap highlights the need for frameworks such as ours, which explicitly balance class distributions, enhance intraclass diversity, and dynamically adapt through uncertaintyguided sampling and vector retrieval mechanisms.

## III. METHODOLOGY

## A. Overview

In this work, we propose a novel sustainable Android malware detection method, UGSR, for continual learning scenarios. An overview of the proposed UGSR framework is illustrated in Fig. 1. The training process of UGSR consists of three stages: static learning, continual learning, and testing. The continual learning stage includes two phases: sampling and learning. Initially, we perform static training using the available data to obtain an initial model. At each continual learning stage, we first use a hierarchical uncertainty sampler to select representative samples for subsequent stages. In the learning phase, the primary challenge is to preserve the knowledge acquired earlier while incorporating new knowledge from novel samples. In the testing stage, we reformulate the detection task as a retrieval problem to prevent overfitting to the dominant class.

## B. Static Learning

Given the input data and corresponding labels $( x ; y ^ { \mathrm { m u l } } ; y ^ { \mathrm { b i n } } )$ where each input data x is associated with two labels: $y ^ { \mathrm { m u l } } \in$ $\{ 0 , 1 \} ^ { C + 1 }$ (including one benign and C fine-grained malware family classes), and $y ^ { \mathrm { b i n } } \in \{ 0 , 1 \}$ , which represent one-hot encoded multi-class labels and a binary Android malware detection label for x, respectively. The training process involves sequentially learning two components: the sampler $\mathcal { F } _ { \mathrm { { S } } }$ and the detector $\mathcal { F } _ { \mathrm { D } }$

Sampler $\mathcal { F } _ { \mathbf { S } } \colon$ The sampler $\mathcal { F } _ { \mathrm { { S } } }$ is a two-stage architecture consisting of a multi-class module $\mathcal { F } _ { \mathrm { m u l } }$ , which provides reliable fine-grained multi-class Android malware detection, and a binary-class module $\mathcal { F } _ { \mathrm { b i n } }$ , which produces the final binary detection score. The two-stage operation can be formulated as:

$$
f _ {m} = \mathcal {F} _ {\mathrm{mul}} (x).\tag{1}
$$

$$
\mathcal {F} _ {\mathrm{S}} (x) = \mathcal {F} _ {\mathrm{bin}} (f _ {m}).\tag{2}
$$

Specifically, for the multi-class module $\mathcal { F } _ { \mathrm { m u l } }$ , we utilize Dempster-Shafer Theory of Evidence [38]–[41] to generate reliable fine-grained multi-class malware predictions. The logits $f _ { m }$ can be regarded as the parameters of a Dirichlet distribution, which models the density of malware probability. The density function is defined as follows:

$$
D (p _ {m} \mid f _ {m}) = \left\{ \begin{array}{l l} \frac {1}{B (f _ {m})} \prod_ {c = 1} ^ {C} p _ {m} ^ {f _ {m} ^ {c} - 1} & \text { for } p _ {m} \in \mathcal {S} ^ {C}, \\ 0 & \text { otherwise }, \end{array} \right.\tag{3}
$$

where $p _ { m }$ represents the multi-class malware probability, $B ( f _ { m } )$ is the C-dimensional multinomial beta function for the parameter $f _ { m } ,$ and $\mathit { S } _ { \mathit { C } }$ denotes the C-dimensional simplex.

We follow [38] and construct an evidence loss $\mathcal { L } _ { e v i }$ to align the multi-class malware probability $p _ { m }$ with the ground-truth label $y ^ { m u l }$ . The loss $\mathcal { L } _ { e v i }$ is formulated as follows:

$$
\begin{array}{r l} & {\mathcal {L} _ {e v i} = \int \left[ \sum_ {k = c} ^ {C} - y _ {m} ^ {c} \log {(p _ {m} ^ {c})} \right] D (p _ {m} \mid f _ {m}) d p _ {m}} \\ & {\qquad = \sum_ {c = 1} ^ {C} y _ {m} ^ {c} (\psi (S ^ {c}) - \psi (f _ {m} ^ {c})),} \end{array}\tag{4}
$$

where $\psi ( \cdot )$ is the digamma function. Then the overall loss $\mathcal { L } _ { \mathcal { F } _ { m u l } }$ for the multi-class module $\mathcal { F } _ { m u l }$ is formulated as:

$$
\mathcal {L} _ {\mathcal {F} _ {\mathrm{mul}}} = \mathcal {L} _ {\mathrm{CE}} + \lambda_ {1} \mathcal {L} _ {e v i},\tag{5}
$$

where $\lambda _ { 1 }$ is a balancing hyperparameter that prevents any loss component from dominating, and $\mathcal { L } _ { c e }$ is the cross-entropy loss, which can be defined as:

$$
\mathcal {L} _ {\mathrm{CE}} = - \sum_ {c = 0} ^ {C} y _ {c} ^ {\text { mul }} \log (f _ {\mathrm{m}} ^ {c}).\tag{6}
$$

Next, we attempt to construct the latent relationship within the multi-class logits and use the binary label to optimize ${ \mathcal { F } } _ { \mathrm { b i n } } .$ In this phase, $\mathcal { F } _ { \mathrm { m u l } }$ remains frozen, while $\mathcal { F } _ { \mathrm { b i n } }$ is trained using a hybrid loss, defined as follows:

$$
\mathcal {L} _ {\mathcal {F} _ {\mathrm{bin}}} = \mathcal {L} _ {\mathrm{supcon}} + \lambda_ {2} \mathcal {L} _ {\mathrm{BCE}},\tag{7}
$$

where $\lambda _ { 2 }$ is a balancing hyperparameter. $\mathcal { L } _ { \mathrm { B C E } }$ is the binary cross-entropy loss, formulated as:

$$
\mathcal {L} _ {\mathrm{BCE}} = - \sum_ {i = 1} ^ {M} \left[ y _ {i} ^ {\text { bin }} \log (\mathcal {F} _ {\text { bin }} (x _ {i})) + (1 - y _ {i} ^ {\text { bin }}) \log (1 - \mathcal {F} _ {\text { bin }} (x _ {i})) \right].\tag{8}
$$

Additionally, $\mathcal { L } _ { \mathrm { s u p c o n } }$ represents the supervised contrastive loss:

$$
\mathcal {L} _ {\text { supcon }} = \sum_ {i = 1} ^ {M} \frac {- 1}{| P (i) |} \sum_ {k \in P (i)} \log \frac {\exp \left(z _ {i} \cdot z _ {k} / \tau\right)}{\sum_ {a \in A (i)} \exp \left(z _ {i} \cdot z _ {a} / \tau\right)},\tag{9}
$$

where $z _ { i } = \mathcal { F } _ { \mathrm { b i n } } ( x _ { i } )$ denotes the normalized feature embedding of sample $x _ { i }$ in the feature space of the binary classifier ${ \mathcal { F } } _ { \mathrm { b i n } } .$ . The temperature hyperparameter τ controls the sharpness of the similarity distribution. The set $P ( i )$ contains positive samples (including $x _ { i }$ itself) that share the same binary label $y _ { i } ^ { \mathrm { { b i n } } }$ as $x _ { i } ,$ , while the set $A ( i )$ contains negative samples with different binary labels. The loss function encourages the model to increase the similarity between positive pairs while reducing it between negative pairs.

Fig. 1: The overall pipeline of our proposed method.

Detector $\mathcal { F } _ { \mathbf { D } } \colon$ Simultaneously, the detector $\mathcal { F } _ { \mathrm { D } }$ consists of an encoder $\mathcal { F } _ { \mathrm { e n c } } : \mathcal { X }  \mathbb { R } ^ { d }$ and a classifier $\mathcal { F } _ { \mathrm { c l s } } : \mathbb { R } ^ { d } \to \mathbb { R } ^ { 2 }$ which are jointly trained as an integrated module. To address the inherent class imbalance in Android malware detection datasets and enhance the classifier’s discriminative power, the detector employs a weighted composite loss function:

$$
\mathcal {L} _ {\mathcal {F} _ {\mathrm{D}}} = \mathcal {L} _ {\text { supcon }} + \lambda_ {3} \mathcal {L} _ {\text { w - bce }},\tag{10}
$$

$\lambda _ { 3 }$ also is a balancing hyperparameter of $\mathcal { L } _ { \mathcal { F } _ { \mathrm { D } } }$ , where ${ \mathcal { L } } _ { \mathrm { w - b c e } }$ represents the weighted binary cross-entropy loss:

$$
\mathcal {L} _ {\mathrm{w-bce}} = \sum_ {i = 1} ^ {M} w _ {i} \left[ y _ {i} ^ {\text { bin }} \log (p _ {i} ^ {D}) + (1 - y _ {i} ^ {\text { bin }}) \log (1 - p _ {i} ^ {D}) \right],\tag{11}
$$

where $p _ { i } ^ { D } = \mathcal { F } _ { \mathrm { D } } ( x _ { i } ) = \mathcal { F } _ { \mathrm { c l s } } ( \mathcal { F } _ { \mathrm { e n c } } ( x _ { i } ) )$ denotes the classifier’s prediction, and w represents the sample-specific weight.

The same supervised contrastive loss $\mathcal { L } _ { \mathrm { s u p c o n } }$ (Equation (9) ) as used for the sampler is employed, where $z _ { i } = \mathcal { F } _ { \mathrm { e n c } } ( x _ { i } )$ denotes the normalized feature embedding, with $\tau , P ( i )$ , and A(i) defined analogously to the sampler’s contrastive loss. This formulation maintains robustness against class imbalance while learning discriminative representations resilient to evolving threats and distribution shifts.

Codebook V: After training the detector, we initialize our vector codebook V by extracting 512-dimensional feature vectors from the penultimate layer of the encoder ${ \mathcal { F } } _ { \mathrm { e n c } }$ , sorted according to classifier confidence scores. The vector codebook stores tuples consisting of a label, vector, and confidence score. Specifically, the codebook contains a total of 50 benign samples $( N _ { \mathrm { b e n i g n } } ~ = ~ 5 0 )$ and up to 3 samples per malware family $( N _ { \mathrm { m a l } } = 3 )$ , where $N _ { \mathrm { b e n i g n } }$ denotes the number of benign samples and $N _ { \mathrm { m a l } }$ represents the maximum number of samples per malware family.

Inspired by the concept of prototypes and the ETF framework in prototype learning, our goal is to enhance the differentiation between benign and malware by increasing the interclass distance while simultaneously minimizing the intra-class distance within each class. To achieve this, we perform two key operations on the feature vectors stored in the codebook.

First, we compute the centroids of the feature vectors for each class (benign and malware) as follows:

$$
\mathbf {v} _ {j} ^ {\text { centroid }} = \frac {1}{N _ {j}} \sum_ {i = 1} ^ {N _ {j}} \mathbf {v} _ {j} ^ {i},\tag{12}
$$

where $\mathbf { v } _ { j } ^ { i }$ is the feature vector of the i-th sample in class $j ,$ and $N _ { j }$ is the number of samples in class j, which can belong to either $N _ { \mathrm { b e n i g n } }$ or up to $N _ { \mathrm { m a l } }$

After calculating the feature vector centroids, we update the feature vectors to bring them closer to their respective centroids:

$$
\mathbf {v} _ {j} ^ {i ^ {\prime}} = \mathbf {v} _ {j} ^ {i} + (\theta_ {1} + \theta_ {2} \cdot s _ {\text { confidence }}) \cdot (\mathbf {v} _ {j} ^ {\text { centroid }} - \mathbf {v} _ {j} ^ {i}),\tag{13}
$$

where $\mathbf { v } _ { j } ^ { i }$ is the current feature vector, $\theta _ { 1 }$ and $\theta _ { 2 }$ are hyperparameters that control the pull strength toward the j-th class’s centroid $\mathbf { v } _ { j } ^ { \mathrm { c e n t r o i d } }$ , and $s _ { \mathrm { c o n f i d e n c e } }$ represents the confidence score. This operation ensures that the feature vectors of the benign class $\mathbf { v } _ { \mathrm { b e n i g n } } ^ { 0 }$ and each malware family class $\mathbf { v } _ { \mathrm { m a l } } ^ { i }$ become more compact within their respective classes, moving closer to their centroids.

Fig. 2: The pipeline of the retrieval framework.

Next, to enhance the separation between the benign and malicious classes, we try to orthogonalize the feature vector of the benign and malicious classes. This is achieved by updating the feature vectors of the malware samples as follows:

$$
\mathbf {v} _ {j} ^ {i \prime} = \mathbf {v} _ {j} ^ {i} - \theta_ {3} \cdot c o s (\mathbf {v} _ {j} ^ {i}, \mathbf {v} _ {0} ^ {\mathrm{centroid}}) \cdot \mathbf {v} _ {0} ^ {\mathrm{centroid}},\tag{14}
$$

where $\mathbf { v } _ { j } ^ { i }$ is the feature vector of the malware sample, $\mathbf { v } _ { 0 } ^ { \mathrm { c e n t r o i d } }$ is the centroid of the benign class, and $\theta _ { 3 }$ is a hyperparameter that controls the separation intensity. This operation makes the malware feature vectors more orthogonal to the benign class vectors, thereby increasing inter-class separation and enhancing the model’s ability to distinguish between benign and malicious samples.

## C. Continual Learning

The continual learning stage consists of two key phases: sampling and learning. This approach is designed to address the challenges of catastrophic forgetting and sample imbalance in Android malware detection tasks involving time-continuous sequences. The ultimate goal is to maintain the model’s performance for malware detection.

Sampling Phase: For each incoming monthly test batch ${ \mathcal { D } } _ { n } ,$ $\mathcal { F } _ { \mathrm { { S } } }$ calculates uncertainty scores through its cascaded modules:

1) The multi-class module $\mathcal { F } _ { \mathrm { m u l } }$ computes malware familyaware uncertainty scores $\mathbf { s } _ { \mathrm { m u l } } = \mathcal { F } _ { \mathrm { m u l } } ( \mathcal { D } _ { n } )$ to preserve long-term malware family knowledge.

2) The adaptive binary module $\mathcal { F } _ { \mathrm { b i n } }$ generates boundarysensitive scores $\mathbf { s } _ { \mathrm { b i n } } = \mathcal { F } _ { \mathrm { b i n } } ( \mathcal { D } _ { n } )$ via contrastive learning between benign and malware samples.

The system selects the top-k samples using a hybrid strategy:

$$
\mathcal{D}_{n}^{\prime} = \operatorname *{top}_{\substack{\mu B\\ x\in \mathcal{D}_{n}}}(\mathbf{s}_{\mathrm{mul}}(x)) + \operatorname *{top}_{\substack{(1 - \mu)B\\ x\in \mathcal{D}_{n}}}(\mathbf{s}_{\mathrm{bin}}(x)),\tag{15}
$$

where B is the fixed budget and $\mu \ = \ 0 . 5$ balances the contributions of each module. A minimum of 10% benign quota is enforced by replacing low-scoring malware samples when benign instances are underrepresented. The selected samples, $\mathcal { D } _ { n } ^ { \prime } .$ , are labeled by human experts and added to the memory bank $\mathcal { M }$

Learning Phase: In the learning phase, both the multi-class module in the sampler, ${ \mathcal { F } } _ { \mathrm { { S } } } .$ , and the detector, $\mathcal { F } _ { \mathrm { D } }$ , are finetuned. This process combines the currently selected samples, $\mathcal { D } _ { n } ^ { \prime }$ , with part of the historical data, M, from the memory bank (usually 20%), fine-tuning the model through a composite objective, similar to the static learning phase.

In this fine-tuning phase, the objective function for the sampler combines the classification loss, $\mathcal { L } _ { \mathrm { B C E } }$ (Equation (8)), computed on the current samples, $\mathcal { D } _ { n } ^ { \prime } .$ , with the contrastive loss, $\mathcal { L } _ { \mathrm { s u p c o n } }$ (Equation (9)), applied to the feature space ${ \mathcal { F } } _ { \mathrm { b i n } } .$ . Similarly, the detector is fine-tuned using the loss function, $\mathcal { L } _ { \mathcal { F } _ { \mathrm { D } } }$ (Equation (10)), where the data consists of the new samples dataset, $\mathcal { D } _ { n } ^ { \prime }$ . This regularization encourages the model to maintain clear decision boundaries by enhancing the separation between positive and negative pairs, thereby refining the feature space learned in previous iterations.

While the optimization process and loss functions are largely consistent with those used in the static learning phase, notable differences exist. Specifically, the number of training epochs is significantly reduced compared to the static learning phase.

This continual learning strategy allows the model to adapt to emerging malware and benign software, ensuring sustained high performance despite shifts in data distribution. By utilizing a few current and historical samples, the model maintains its performance while preserving knowledge from previous iterations.

## D. Retrieval-based Malware Detection

In Android malware detection, traditional deep learning approaches face two key limitations: decision boundaries that favor majority-class samples, leading to missed detections of novel variants, and architectures that cannot adapt to evolving malware characteristics. To overcome these issues, we introduce a feature vector retrieval and matching module that enhances sensitivity to minority samples while improving generalization to unseen malware through dynamic similarity matching. The pipeline of the proposed retrieval-based malware detection framework is illustrated in Fig. 2.

1) Construction and Updating of Codebook: The details of the codebook construction have been mentioned earlier. To improve retrieval and matching performance, we aim to make the feature representations of each class more compact while increasing the distance between benign and malicious classes. Following codebook construction, we further refine the feature space by applying additional operations, which are described in detail in the methodology section. In this space, the angular relationships between different categories are optimized to maximize inter-class separation while ensuring intra-class compactness.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 The learning procedure of UGSR
1: Static Learning:
2: Initialize hierarchical sampler $\mathcal{F}_S$:
3: step 1: Train multi-class module $\mathcal{F}_{mul}$
4: step 2: Train binary module $\mathcal{F}_{bin}$ while frozen $\mathcal{F}_{mul}$
5: Initialize detector $\mathcal{F}_D$
6: Construct vector codebook $\mathcal{V}$
7: while $T_n \neq \emptyset$ do
8: Testing:
9: for each testing period $t \in \{T_1, T_2...T_n...\}$ do
10: Load $\mathcal{D}_n = \{x\}$
11: $\mathbf{F}_n \leftarrow \mathcal{F}_{enc}(\mathcal{D}_n)$ (Feature Extraction)
12: Hybrid Prediction:
13: for each $x_i \in \mathcal{D}_n$ do
14: Neural network prediction ($\mathcal{F}_D$):
$p_i \leftarrow \mathcal{F}_D(x_i)$
15: Codebook similarity matching ($\mathcal{V}$):
$m_i \leftarrow \text{Top-k}(\mathcal{V}, \mathbf{F}_n, k=3)$
16: Fuse($p_i, m_i$)
17: end for
18: end for
19: Continual Learning:
20: for each evaluation period $T_n$ do
21: Load test samples $\mathcal{D}_n$
22: Active Sampling:(B is sample budget)
23: Select informative samples using $\mathcal{F}_S$:
24: - $\mu B$ highest uncertainty score samples($\mathcal{F}_{mul}$)
25: - (1-$\mu$)B highest uncertain score samples($\mathcal{F}_{bin}$)
26: Update accumulated data $\mathcal{D}_n'$ to memory bank $\mathcal{M}$
27: Model Update:
28: Fine-tune $\mathcal{F}_S$ and $\mathcal{F}_D$ on $\mathcal{M}$
29: Update $\mathcal{V}$ with new features
30: Space Optimization:
31: Apply ETF principle to $\mathcal{V}$
32: end for
33: Return $\mathcal{F}_S, \mathcal{F}_D, \mathcal{V}$
34: end while
</div>

During continual learning, our codebook updating mechanism maintains an evolving but stable feature representation through three key operations. First, for newly encountered samples, we evaluate their classifier confidence scores and selectively update the codebook by replacing existing lowerconfidence vectors of the same class, strictly adhering to predefined capacity constraints $( N _ { \mathrm { b e n i g n } } = 5 0 \ \mathrm { a n d } \ N _ { \mathrm { m a l } } = 3 )$

We maintain the optimized geometric structure by recalculating the category centroid through mean aggregation whenever vectors are added or replaced. This ensures that the updated samples in the codebook retain strong benign-malware discrimination while preserving the relationships within each malware family.

2) Vector Retrieval and Match: In the testing stage, the feature vector library is used to retrieve the similarity of input samples. The specific steps are as follows: the test sample x is passed through the encoder E to obtain a 512-dimensional vector $v _ { x }$ , after which all the feature vectors in the codebook are traversed to calculate the cosine similarity between the input feature vector $v _ { x }$ and each feature vector $v _ { i }$ in the codebook, $\mathcal { V } = \{ v _ { 1 } , v _ { 2 } , \ldots , v _ { n } \}$ . The cosine similarity metric is computed as follows:

$$
s (v _ {x}, v _ {i}) = \frac {v _ {x} \cdot v _ {i}}{\| v _ {x} \| \| v _ {i} \|},\tag{16}
$$

where $s ( \cdot , \cdot )$ denotes the similarity score ranging from -1 to 1. Retrieve the k most similar feature vectors to the input feature vector based on the similarity score $s ( v _ { x } , v _ { i } )$ , where k is a tunable hyperparameter.

Based on the matching results and the classifier’s original predictions, we propose a dynamic decision strategy: (1) when benign matches $M _ { b e n i g n }$ exceed the threshold θ (set $\theta = k )$ , we predict its class as benign; (2) when malicious matches $M _ { m a l }$ exceed $\theta ,$ we predict its class as malicious; (3) otherwise, we retain the classifier’s prediction, $p _ { i } ^ { D }$ . We propose a dynamic decision strategy formalized as:

$$
\hat {p} _ {\text { final }} = \left\{ \begin{array}{l l} 0, & \text { if } M _ {\text { benign }} = \theta \\ 1, & \text { if } M _ {\text { mal }} = \theta \\ p _ {i} ^ {D}, & \text { otherwise } \end{array} \right..\tag{17}
$$

This dual-threshold mechanism provides a robust fallback to the original classifier when retrieval evidence is inconclusive, while leveraging codebook matches when they provide strong discriminative signals. The top-k thresholding naturally adapts to varying confidence levels across different malware families

This retrieval-enhanced decision framework combines the strengths of both parametric classifier predictions and nonparametric similarity matching, achieving more robust and interpretable Android malware detection through their synergistic integration. The approach effectively balances the stability of learned classifier patterns with the adaptability of instance-based retrieval, which is particularly valuable in handling ambiguous cases where the classifier’s confidence is low.

The overall procedure is formalized in Algorithm 1, where the UGSR framework sequentially executes static model initialization, hybrid prediction (combining $\mathcal { F } _ { D }$ and codebook V), and continual learning with uncertainty-driven sampling and ETF-based space optimization.

## IV. EXPERIMENTS

## A. Dataset

We conducted evaluations on two benchmark datasets, API-Graph [42] and AndroZoo [43]. APIGraph contains about 320,000 Android applications published over seven years (2012-2018. AndroZoo contains about 100,000 Android applications published between 2019 and 2021. The ratio of benign samples to malicious samples in these datasets is approximately 9:1. The samples in both datasets are highly imbalanced. To make this more intuitive, the distributions of these datasets are illustrated in Fig. 3.

(a)  
(b)  
Fig. 3: The introduction of datasets: (a) represents the API-Graph dataset and (b) represents the Androzoo datasets.

## B. Experimental Settings

In both datasets, the first 12 months of data were used as the static training set, $\mathcal { D } _ { s } ,$ with the subsequent months reserved for continual learning. The $\mathcal { F } _ { \mathrm { m u l } }$ module in the sampler and ${ \mathcal { F } } _ { \mathrm { e n c } }$ module in the detector share the same MLP architecture, which consists of five linear layers. Similarly, the $\mathcal { F } _ { \mathrm { b i n } }$ module in the sampler and $\mathcal { F } _ { \mathrm { c l s } }$ module in the detector also share the same MLP architecture, which contains four linear layers. The only distinction between them is that the final layer of $\mathcal { F } _ { \mathrm { m u l } }$ in the sampler includes a softmax activation function.

Following the work by Chen et al. [1], in the static learning stage, we trained our sampler and detector for 200 epochs using SGD (learning rate $\eta = 3 \times 1 0 ^ { - 4 } )$ with a batch size of 1024. In the continual learning stage, we freeze $\mathcal { F } _ { \mathrm { b i n } }$ and fine-tune the remaining components for 50 epochs using Adam $( \eta = 5 \times 1 0 ^ { - 5 } )$ , while maintaining a 40% benign sample ratio in incremental batches. For the codebook, we set $N _ { \mathrm { b e n i g n } } = 5 0$ and $N _ { \mathrm { m a l } } = 3$ per family, with matching thresholds set to $\tau = 3$

## C. Metrics

We use the fundamental metrics of true positive rate (TPR) and true negative rate (TNR) to evaluate performance. Given the class imbalance in Android malware detection (with benign-malicious ratios approaching 9:1), standard accuracy becomes unreliable because it favors the majority class and may mask failures in detecting malware. Therefore, we adopt the balanced accuracy metric (mACC), which equally weights both classes to comprehensively evaluate performance. mACC is formulated as:

$$
\mathrm{mACC} = (\mathrm{TPR} + \mathrm{TNR}) / 2.\tag{18}
$$

Besides, F2 is used to evaluate the performance as follows:

$$
F 2 = \frac {(1 + 2 ^ {2}) \cdot \text { Precision } \cdot \text { Recall }}{2 ^ {2} \cdot \text { Precision } + \text { Recall }}.\tag{19}
$$

Given that Android malware detection is an unbalanced task, we evaluated the performance of different methods using F2. F2 is a suitable metric for Android malware detection as it emphasizes recall, which makes it more appropriate for security scenarios where identifying malware is of greater importance.

The geometric mean, G-Mean, is also used to evaluate performance, as it considers both TPR and TNR. G-Mean can be calculated as follows:

$$
\mathrm{G-mean} = \sqrt {\mathrm{TPR} \times \mathrm{TNR}}.\tag{20}
$$

TABLE I: Experimental Results on APIGraph Dataset.

<table><tr><td rowspan="2">Method</td><td colspan="5">Average Performance (%)</td></tr><tr><td>TPR</td><td>TNR</td><td>F2</td><td>G-mean</td><td>mACC</td></tr><tr><td>Binary MLP</td><td>76.23</td><td>99.48</td><td>79.26</td><td>87.08</td><td>87.86</td></tr><tr><td>Multiclass MLP</td><td>83.90</td><td>95.36</td><td>79.81</td><td>89.45</td><td>89.63</td></tr><tr><td>Binary SVM</td><td>83.08</td><td>99.39</td><td>85.02</td><td>90.87</td><td>91.24</td></tr><tr><td>CADE OOD [50]</td><td>63.89</td><td>87.10</td><td>55.08</td><td>74.60</td><td>75.50</td></tr><tr><td>Binary GBDT [49]</td><td>68.25</td><td>99.46</td><td>72.13</td><td>82.39</td><td>83.86</td></tr><tr><td>USENIX23 [1]</td><td>84.85</td><td>99.48</td><td>86.66</td><td>91.87</td><td>92.17</td></tr><tr><td>UGSR</td><td>92.95</td><td>95.58</td><td>86.82</td><td>94.22</td><td>94.26</td></tr></table>

TABLE II: Experimental Results on AndroZoo Dataset.

<table><tr><td rowspan="2">Method</td><td colspan="5">Average Performance (%)</td></tr><tr><td>TPR</td><td>TNR</td><td>F2</td><td>G-mean</td><td>mACC</td></tr><tr><td>Binary MLP</td><td>46.88</td><td>99.54</td><td>51.97</td><td>68.31</td><td>73.21</td></tr><tr><td>Multiclass MLP</td><td>50.14</td><td>71.48</td><td>35.47</td><td>53.56</td><td>60.81</td></tr><tr><td>Binary SVM</td><td>51.23</td><td>99.71</td><td>56.44</td><td>71.47</td><td>75.47</td></tr><tr><td>CADE OOD [50]</td><td>37.99</td><td>99.45</td><td>42.88</td><td>61.47</td><td>68.72</td></tr><tr><td>Binary GBDT [49]</td><td>49.65</td><td>99.53</td><td>54.69</td><td>70.29</td><td>74.59</td></tr><tr><td>Usenix23 [1]</td><td>72.35</td><td>99.47</td><td>75.82</td><td>84.83</td><td>85.91</td></tr><tr><td>UGSR</td><td>80.56</td><td>96.01</td><td>77.32</td><td>86.68</td><td>88.29</td></tr></table>

## D. Baselines

The first baseline applies active learning with base binary classifiers, including MLP, linear SVM, and Gradient Boosted Decision Trees (GBDT) [42], [49]. The second baseline utilizes an SVM classifier guided by CADE OOD scores [50], which were originally designed for distribution drift detection and also support the sample labeling strategy employed in our experiments. Lastly, the third baseline incorporates pseudoloss scores for sample selection [1].

## E. Results

We apply a monthly budget of 50 samples for analyst labeling to ensure a fair comparison across all methods. The results in APIGraph and AndroZoo can be found in Tables I and II, respectively. It can be seen that the other methods tend to overfit to the majority benign class, leading to low TPR and high TNR. In contrast, the results demonstrate the strong capability of UGSR in detecting the minority class. In terms of overall performance metrics, our method outperforms all other baselines. The reason lies in that our method prioritizes the most uncertain minority class samples through uncertaintydriven hierarchical sampling, effectively preventing overfitting to the majority class.

UGSR’s TPR and mACC consistently outperform all baselines across both the APIGraph and AndroZoo datasets. It demonstrates a strong capability in detecting rare malicious samples while maintaining balanced classification. Notably, UGSR also achieves a higher F2 score in both cases, consistent with the fact that failing to detect malware is significantly more costly than false alarms.

Compared to baseline methods that tend to overfit to the majority benign class, UGSR improves the detection of minority malicious samples with only a slight reduction in benign classification accuracy. This balance leads to superior

TABLE III: Few-shot Continual Learning results on the API-Graph Dataset.

<table><tr><td rowspan="2">Model</td><td rowspan="2">Sample Budget</td><td colspan="5">Average Performance (%)</td></tr><tr><td>TPR</td><td>TNR</td><td>F2</td><td>G-mean</td><td>mACC</td></tr><tr><td>USENIX23 [1]</td><td>Count = 10</td><td>77.46</td><td>99.25</td><td>79.99</td><td>87.68</td><td>88.36</td></tr><tr><td>Ours</td><td>Count = 10</td><td>89.45</td><td>95.46</td><td>83.92</td><td>92.33</td><td>92.46</td></tr><tr><td>USENIX23 [1]</td><td>Count = 2</td><td>67.63</td><td>99.13</td><td>71.12</td><td>81.88</td><td>83.38</td></tr><tr><td>Ours</td><td>Count = 2</td><td>81.62</td><td>96.14</td><td>79.03</td><td>88.58</td><td>88.88</td></tr></table>

TABLE IV: Few-shot Continual Learning results on the $\mathbf { A n - }$ droZoo Dataset.

<table><tr><td rowspan="2">Model</td><td rowspan="2">Sample Budget</td><td colspan="5">Average Performance (%)</td></tr><tr><td>TPR</td><td>TNR</td><td>F2</td><td>G-mean</td><td>mACC</td></tr><tr><td>USENIX23 [1]</td><td>Count = 10</td><td>67.07</td><td>99.48</td><td>71.09</td><td>81.68</td><td>83.27</td></tr><tr><td>Ours</td><td>Count = 10</td><td>75.41</td><td>96.24</td><td>73.47</td><td>84.14</td><td>85.83</td></tr><tr><td>USENIX23 [1]</td><td>Count = 2</td><td>59.54</td><td>99.12</td><td>62.44</td><td>74.75</td><td>79.33</td></tr><tr><td>Ours</td><td>Count = 2</td><td>62.67</td><td>97.17</td><td>62.74</td><td>75.31</td><td>79.92</td></tr></table>

G-mean and mACC scores, reflecting the model’s robustness in handling class imbalance.

Furthermore, UGSR achieves this performance with a substantially lower annotation cost. While previous optimal work [1] required 200 labeled samples to reach a 90% TPR on the APIGraph dataset, UGSR achieves comparable or better performance using only 50 labeled samples per fine-tuning iteration. This highlights its efficiency and practicality for real-world, continuously evolving Android malware detection systems.

Additionally, we conducted experiments on the APIGraph dataset under a few-shot setting, with the sample budget set to 10 and 2, respectively. In this experiment, we treat the USENIX23 as the baseline, and the results can be found in Table III. Our method achieves a more than 10% increase in TPR with only a minor reduction in TNR. Moreover, improvements are observed across nearly all key metrics, which demonstrate that our method can effectively maintain balanced and reliable detection even under limited sample budgets. Similar results are observed in AndroZoo, as shown in Table IV. These results further demonstrate the effectiveness of our approach, highlighting its robustness under the small sample budget setting.

To intuitively compare performance across different months, Fig. 4 shows the TPR changes on the APIGraph dataset when the sample budget is set to 10. It can be seen that our method is more robust than the baseline. Our method exhibits minimal fluctuation across different months, highlighting its robustness. In contrast, the baseline is highly sensitive to the data, with TPR reaching only about 20% in some months. The main reason lies in that our method not only selects the most uncertain samples for continual learning but also utilizes a codebook that retains representative samples from previously encountered benign and malware families, preserving their features.

## F. Ablation Experiments

In this subsection, to evaluate the effectiveness of transforming the traditional classification-based detection paradigm into a retrieval-based detection paradigm, we conducted related ablation experiments. The monthly results can be found in Fig. 5, where it can be seen that the retrieval module effectively stabilizes performance and prevents oscillation. For the average performance shown in Table V, TPR increases from 83.75% to 89.45%, accompanied by substantial gains in mACC and G-mean.

Fig. 4: Performance comparison between our method and USENIX23 [1].

TABLE V: Effect of the proposed vector retrieval module.

<table><tr><td rowspan="2">Model</td><td rowspan="2">Samples Budget</td><td colspan="5">Average Performance (%)</td></tr><tr><td>TPR</td><td>TNR</td><td>F2</td><td>G-mean</td><td>mACC</td></tr><tr><td>w/o retrieval</td><td>10</td><td>83.75</td><td>91.14</td><td>74.31</td><td>87.37</td><td>87.45</td></tr><tr><td>w retrieval</td><td>10</td><td>89.45</td><td>95.46</td><td>83.92</td><td>92.33</td><td>92.46</td></tr></table>

TABLE VI: Effect of selector ${ \mathcal { F } } _ { m u l } .$

<table><tr><td rowspan="2">Model</td><td rowspan="2">Samples Budget</td><td colspan="5">Average Performance (%)</td></tr><tr><td>TPR</td><td>TNR</td><td>F2</td><td>G-mean</td><td>mACC</td></tr><tr><td>w/o  $\mathcal{F}_{mul}$ </td><td>10</td><td>73.43</td><td>89.06</td><td>56.73</td><td>80.87</td><td>87.45</td></tr><tr><td>w  $\mathcal{F}_{mul}$ </td><td>10</td><td>89.45</td><td>95.46</td><td>83.92</td><td>92.33</td><td>92.46</td></tr></table>

We further evaluated the effectiveness of the hierarchical sampler, ${ \mathcal { F } } _ { \mathrm { m u l } } .$ . As evidenced by Fig. 6 and Table VI, the ablation of $\mathcal { F } _ { \mathrm { m u l } }$ induces severe continual learning instability, manifested through: (1) erratic TPR oscillations with peak-tovalley variations exceeding 16.02%, and (2) recurrent collapse events where TPR plummets to zero—a clear indicator of catastrophic overfitting wherein the model degenerates into predicting all instances as benign.

Fig. 5: Ablation study about the retrieval module. The horizontal and vertical axes represent the time series of the dataset and the TPR of malware detection, respectively.

Fig. 6: Ablation study of sampler’s multi-class module ${ \mathcal { F } } _ { m u l } .$ The horizontal and vertical axes represent the time series of the dataset and the TPR of malware detection, respectively.

TABLE VII: Effect of Budget sample counts.

<table><tr><td rowspan="2">Samples Budget</td><td colspan="5">Average Performance (%)</td></tr><tr><td>TPR</td><td>TNR</td><td>F2</td><td>G-mean</td><td>mACC</td></tr><tr><td>Count = 2</td><td>62.67</td><td>97.17</td><td>62.74</td><td>75.31</td><td>79.92</td></tr><tr><td>Count = 10</td><td>75.41</td><td>96.24</td><td>73.47</td><td>84.14</td><td>85.83</td></tr><tr><td>Count = 25</td><td>77.31</td><td>95.47</td><td>73.87</td><td>84.32</td><td>86.39</td></tr><tr><td>Count = 50</td><td>80.56</td><td>96.01</td><td>77.32</td><td>86.68</td><td>88.29</td></tr><tr><td>Count = 100</td><td>84.69</td><td>93.40</td><td>78.16</td><td>88.44</td><td>89.04</td></tr></table>

In contrast, the full model equipped with $\mathcal { F } _ { \mathrm { m u l } }$ maintains consistently high TPR throughout the 2013–2018 period, even under significant distribution shifts. These findings underscore the importance of jointly leveraging both the binary selector, $\mathcal { F } _ { \mathrm { b i n } }$ , and the multi-class selector, $\mathcal { F } _ { \mathrm { m u l } }$ , to ensure stable performance. Overall, the proposed approach demonstrates superior efficacy in prioritizing the latest and uncertain samples for annotation. This strategy not only optimizes labeling budget allocation but also enhances model performance while mitigating overfitting in low-sample, non-stationary scenarios.

We further investigated the impact of varying sample budgets during the continual learning phase on the AndroZoo dataset. As shown in Table VII, increasing the number of sampled data points from 2 to 10 leads to significant improvements across all metrics. Furthermore, it can be seen that our method can achieve promising performance with just a budget of 10.

## V. CONCLUSION

In this paper, we present a novel uncertainty-driven hierarchical sampling framework for continual Android malware detection under data imbalance. Our dual-level architecture decouples uncertainty-guided sample selection from memoryaugmented classification, enabling effective adaptation to concept drift through time-series update-based retrieval. The proposed hierarchical uncertainty quantification and dynamic vector retrieval mechanisms provide robust detection of evolving polymorphic variants while maintaining efficiency in datascarce environments. Key innovations include an adaptive temporal retrieval engine and an optimized vector codebook, which offer a practical solution for sustainable Android malware detection. Future work will focus on continual learning strategies for zero-day malware adaptation and federated continual learning for collaborative threat detection.

## REFERENCES

[1] Chen Y, Ding Z, Wagner D. Continuous learning for Android malware detection. In: 32nd USENIX Security Symposium (USENIX Security 23). 2023: 1127-1144.

[2] Kim C, Chang S Y, Kim J, Lee D, Kim J. Automated, reliable zeroday malware detection based on autoencoding architecture. In: IEEE Transactions on Network and Service Management. 2023; 20(3): 3900- 3914.

[3] Wang T, Liu M, Li H, Zhao L, Jiang C, Xia C, Cui B. ArchSentry: Enhanced Android Malware Detection via Hierarchical Semantic Extraction. In: IEEE Transactions on Network and Service Management. 2025.

[4] Wiewel F, Yang B. Entropy-based sample selection for online continual learning. In: 2020 28th European Signal Processing Conference (EUSIPCO). IEEE, 2021: 1477-1481.

[5] Settles B. Active learning literature survey. 2009.

[6] Gal Y. Uncertainty in deep learning. 2016.

[7] Beluch WH, Genewein T, Nurnberger A, et al. The power of ensembles¨ for active learning in image classification. In: Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition. 2018: 9368- 9377.

[8] Gissin D, Shalev-Shwartz S. Discriminative active learning. arXiv preprint arXiv:1907.06347, 2019.

[9] Do K, Tran T, Venkatesh S. Semi-supervised learning with variational Bayesian inference and maximum uncertainty regularization. In: Proceedings of the AAAI Conference on Artificial Intelligence. 2021, 35(8): 7236-7244.

[10] Ahn H, Cha S, Lee D, et al. Uncertainty-based continual learning with adaptive regularization. Advances in Neural Information Processing Systems, 2019, 32.

[11] Barbero F, Pendlebury F, Pierazzi F, et al. Transcending TRANSCEND: Revisiting malware classification in the presence of concept drift. 2022 IEEE Symposium on Security and Privacy (SP), 2022: 805-823.

[12] Kirkpatrick J, Pascanu R, Rabinowitz N, et al. Overcoming catastrophic forgetting in neural networks. Proceedings of the National Academy of Sciences, 2017, 114(13): 3521-3526.

[13] Rusu AA, Rabinowitz NC, Desjardins G, et al. Progressive neural networks. arXiv preprint arXiv:1606.04671, 2016.

[14] Rebuffi SA, Kolesnikov A, Sperl G, et al. iCaRL: Incremental classifier and representation learning. In: Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition. 2017: 2001-2010.

[15] Yan S, Xie J, He X. DER: Dynamically expandable representation for class incremental learning. In: Proceedings ofthe IEEE/CVF Conference on Computer Vision and Pattern Recognition. 2021: 3014-3023.

[16] Douillard A, Cord M, Ollion C, et al. PODNet: Pooled outputs distillation for small-tasks incremental learning. In: Computer Vision–ECCV 2020: 16th European Conference, Glasgow, UK, August 23–28, 2020, Proceedings, Part XX 16. Springer International Publishing, 2020: 86- 102.

[17] Pang G, van den Hengel A, Shen C, et al. Toward deep supervised anomaly detection: Reinforcement learning from partially labeled anomaly data. In: Proceedings of the 27th ACM SIGKDD Conference on Knowledge Discovery & Data Mining. 2021: 1298-1308.

[18] Shin J, Rivas E, Lucio D, et al. Towards Building Generalizable Models for Malware Detection. In: 2024 IEEE International Conference on Big Data (BigData). IEEE, 2024: 5656-5663.

[19] Gong Y, Wang S, Yu T, et al. Improving adversarial robustness using knowledge distillation guided by attention information bottleneck. Information Sciences, 2024, 665: 120401.

[20] Finn C, Abbeel P, Levine S. Model-agnostic meta-learning for fast adaptation of deep networks. In: International Conference on Machine Learning. PMLR, 2017: 1126-1135.

[21] Snell J, Swersky K, Zemel R. Prototypical networks for few-shot learning. Advances in Neural Information Processing Systems, 2017, 30.

[22] Sung F, Yang Y, Zhang L, et al. Learning to compare: Relation network for few-shot learning. In: Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition. 2018: 1199-1208.

[23] Chen Y, Liu Z, Xu H, et al. Meta-baseline: Exploring simple metalearning for few-shot learning. In: Proceedings of the IEEE/CVF International Conference on Computer Vision. 2021: 9062-9071.

[24] Dhillon GS, Chaudhari P, Ravichandran A, et al. A baseline for few-shot image classification. arXiv preprint arXiv:1909.02729, 2019.

[25] Li Y, Yuan D, Zhang T, et al. Meta-learning for multi-family android malware classification. ACM Transactions on Software Engineering and Methodology, 2024, 33(7): 1-27.

[26] Busch J, Kocheturov A, Tresp V, et al. NF-GNN: Network flow graph neural networks for malware detection and classification. In: Proceedings of the 33rd International Conference on Scientific and Statistical Database Management. 2021: 121-132.

[27] Liu C, Li B, Zhao J, et al. FewM-HGCL: Few-shot malware variants detection via heterogeneous graph contrastive learning. IEEE Transactions on Dependable and Secure Computing, 2022.

[28] Tao X, Hong X, Chang X, et al. Few-shot class-incremental learning. In: Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR). Jun. 2020: 12183-12192.

[29] Ren M, Liao R, Fetaya E, et al. Incremental few-shot learning with attention attractor networks. Adv. Neural Inform. Process. Syst. (NeurIPS), 2019, 32: 5275-5285.

[30] Mazumder P, Singh P, Rai P. Few-shot lifelong learning. Proc. AAAI Conf. Artif. Intell., 2021, 35(3): 2337-2345.

[31] Zhu K, Cao Y, Zhai W, et al. Self-promoted prototype refinement for few-shot class-incremental learning. In: Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR). Jun. 2021: 6801-6810.

[32] Cheraghian A, Rahman S, Fang P, et al. Semantic-aware knowledge distillation for few-shot class incremental learning. In: Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR). Jun. 2021: 2534-2543.

[33] Qiang Q, et al. An incremental malware classification approach based on few-shot learning. In: Proc. IEEE Int. Conf. Commun., May 2022: 2682-2687.

[34] Zhou DW, Wang FY, Ye HJ, et al. Forward compatible few-shot classincremental learning. In: Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR). Jun. 2022: 9046-9056.

[35] Dong S, Hong X, Tao X, et al. Few-shot class-incremental learning via relation knowledge distillation. In: Proc. AAAI, 2021: 1255-1263.

[36] Achituve I, Navon A, Yemini Y, et al. GPTree: A Gaussian process classifier for few-shot incremental learning. In: Proc. Int. Conf. Mach. Learn., 2021: 54-65.

[37] Li DW, Huang H. Few-shot class-incremental learning via compact and separable features for fine-grained vehicle recognition. IEEE Trans. Intell. Transp. Syst., 2022, 23(11): 21418-21429.

[38] Sensoy M, Kaplan L, Kandemir M. Evidential deep learning to quantify classification uncertainty. Advances in Neural Information Processing Systems, 2018, 31.

[39] Chen Y, Yang Z, Shen C, Wang Z, Zhang Z, Qin Y, et al. Evidencebased uncertainty-aware semi-supervised medical image segmentation. In: Computers in Biology and Medicine. 2024; 170: 108004.

[40] Chen Y, Yang Z, Shen C, Wang Z, Qin Y, Zhang Y. EVIL: Evidential inference learning for trustworthy semi-supervised medical image segmentation. In: 2023 IEEE 20th International Symposium on Biomedical Imaging (ISBI). 2023: 1–5.

[41] Yang, Z., Chen, Y., Wang, Z., Shan, H., Chen, Y., Zhang, Y. Patient-level anatomy meets scanning-level physics: Personalized federated low-dose ct denoising empowered by large language model. In: Proceedings of the Computer Vision and Pattern Recognition Conference. 2025: 5154– 5163.

[42] Zhang X, Zhang Y, Zhong M, et al. Enhancing state-of-the-art classifiers with API semantics to detect evolved Android malware. In: Proc. 2020 ACM SIGSAC Conf. Comput. Commun. Secur., 2020: 757-770.

[43] AndroZoo. https://androzoo.uni.lu/.

[44] VirusTotal. https://www.virustotal.com/.

[45] VirusShare. https://virusshare.com/.

[46] Arp D, Quiring E, Pendlebury F, et al. Dos and don’ts of machine learning in computer security. In: 31th USENIX Security Symposium (USENIX Security 22), 2022: 3971-3988.

[47] Allix K, Bissyande TF, Klein J, et al. AndroZoo: Collecting millions´ of Android apps for the research community. In: Proc. 13th Int. Conf. Mining Softw. Repositories, 2016: 468-471.

[48] Wei F, Li Y, Roy S, et al. Deep ground truth analysis of current Android malware. In: Detection of Intrusions and Malware, and Vulnerability Assessment, 2017: 252-276.

[49] Yang L, Ciptadi A, Laziuk I, et al. BODMAS: An open dataset for learning based temporal analysis of PE malware. In: 2021 IEEE Security and Privacy Workshops (SPW), 2021: 78-84.

[50] Yang L, Guo W, Hao Q, et al. CADE: Detecting and explaining concept drift samples for security applications. In: 30th USENIX Security Symposium (USENIX Security 21), 2021: 2327-2344.

## VI. BIOGRAPHY SECTION

Yi Xie received the B.S. degree in Artificial Intelligence from Wuhan University of Technology, Wuhan, China, in 2023. He is currently pursuing the M.S. degree with the School of Cyber Science and Engineering at Sichuan University. His research interests include adversarial attacks on AI models and malware detection.

Ziyuan Yang received his Ph.D. from Sichuan University in 2025. He was a research intern at the Centre for Frontier AI Research, Agency for Science, Technology and Research (A\*STAR), Singapore. In the last few years, he has published over 30 papers in leading machine learning conferences and journals, including CVPR, IJCV, TIFS, TNNLS, TCSVT, etc. He was the reviewer for leading journals or conferences, including TPAMI, TIP, TIFS, TMI, CVPR, ICCV, etc.

Yongqiang Huang received the M.S. degree from Sichuan University, Chengdu, China, in 2021. He is currently a PhD candidate with the School of Cyber Science and Engineering at Sichuan University. His current research interests include data privacy preservation and generative AI.

Yinyu Chen received the B.S. degree in Software Engineering from the College of Software Engineering, Sichuan University, Chengdu, China. He is currently pursuing his Ph.D. degree with the College of Computer Science, Sichuan University, Chengdu, China. His research interests include machine learning, deep learning, and medical image analysis.

Lei Zhang received the M.S. and Ph.D. degrees in computer science and technology from Sichuan University, Chengdu, Sichuan, China. He is currently an assistant researcher in the School of Cyber Science and Engineering, Sichuan University. His research focuses on malware detection and analysis.

Liang Liu received the M.S. and Ph.D. degrees from Sichuan University, Chengdu, China, in 2009 and 2021, respectively. He is currently an Associate Professor with the School of Cyber Science and Engineering at Sichuan University. His current research interests include malware detection, network security, system security, and artificial intelligence.

Yi Zhang (Senior Member, IEEE) received the B.S., M.S., and Ph.D. degrees in computer science and technology from the College of Computer Science, Sichuan University, Chengdu, China, in 2005, 2008, and 2012, respectively. From 2014 to 2015, he was with the Department of Biomedical Engineering, Rensselaer Polytechnic Institute, Troy, NY, USA, as a Postdoctoral Researcher. He is currently a Full Professor at the School of Cyber Science and Engineering, Sichuan University, and is the Director of the Deep Imaging Group (DIG). His research interests include medical imaging, compressive sensing, and deep learning. He authored more than 80 papers in the field of image processing. These papers were published in several leading journals, including IEEE TRANSACTIONS ON MEDICAL IMAGING, IEEE TRANSACTIONS ON COMPUTATIONAL IMAGING, Medical Image Analysis, European Radiology, Optics Express, etc., and reported by the Institute of Physics (IOP) and during the Lindau Nobel Laureate Meeting. He received major funding from the National Key R&D Program of China, the National Natural Science Foundation of China, and the Science and Technology Support Project of Sichuan Province, China. He is a Guest Editor of the International Journal of Biomedical Imaging, Sensing and Imaging, and an Associate Editor of IEEE TRANSACTIONS ON MEDICAL IMAGING and IEEE TRANSACTIONS ON RADIATION AND PLASMA MEDICAL SCIENCES.