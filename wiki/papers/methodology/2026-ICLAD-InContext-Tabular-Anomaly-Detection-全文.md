---
title: "2026-ICLAD-InContext-Tabular-Anomaly-Detection"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2026-ICLAD-InContext-Tabular-Anomaly-Detection.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# ICLAD: In-Context Learning for Unified Tabular Anomaly Detection Across Supervision Regimes

Jack Yi Wei $^{1,2}$ and Narges Armanfard $^{1,2}$

$^{1}$ Department of Electrical and Computer Engineering, McGill University, Canada $^{2}$ Mila - Quebec Artificial Intelligence Institute, Montreal, Canada
yi.wei4@mail.mcgill.ca, narges.armanfard@mcgill.ca

Abstract. Anomaly detection on tabular data is commonly studied under three supervision regimes, including one-class settings that assume access to anomaly-free training samples, fully unsupervised settings with unlabeled and potentially contaminated training data, and semi-supervised settings with limited anomaly labels. Existing deep learning approaches typically train dataset-specific models under the assumption of a single supervision regime, which limits their ability to leverage shared structures across anomaly detection tasks and to adapt to different supervision levels. We propose ICLAD, an in-context learning foundation model for tabular anomaly detection that generalizes across both datasets and supervision regimes. ICLAD is trained via meta-learning on synthetic tabular anomaly detection tasks, and at inference time, the model assigns anomaly scores by conditioning on the training set without updating model weights. Comprehensive experiments on 57 tabular datasets from ADBench show that our method achieves state-of-the-art performance across three supervision regimes, establishing a unified framework for tabular anomaly detection.

Keywords: Anomaly Detection · Tabular Data · In-Context Learning.

## 1 Introduction

Most real-world datasets are represented as tables, with rows corresponding to samples and columns representing attributes. Tabular anomaly detection aims to identify unusual rows within such datasets and has widespread applications in cybersecurity, healthcare, and industrial systems, where anomalies may indicate network intrusions $[2]$ , medical risks $[48]$ , or equipment failures $[34]$ .

Despite the recent popularity of deep learning, effective anomaly detection on tabular data remains challenging. Tabular data often consist of heterogeneous features with mixed continuous and discrete variables, and lack strong relation structures such as spatial, sequential or graphical dependencies $[4]$ . In tabular supervised learning, deep learning models have historically struggled to consistently outperform gradient-boosted decision trees $[42,12,23]$ . A similar trend holds for tabular anomaly detection, where numerous deep methods have been proposed but classical density-based methods remain competitive on standard benchmarks $[13,21]$ . These observations suggest that generic deep learning approaches often struggle to capture inductive biases well suited to tabular data, motivating approaches that can acquire tabular-specific inductive biases.

Beyond the challenge of tabular deep learning, tabular anomaly detection is further complicated by a diverse but fragmented set of supervision settings $[25]$ . Recent deep learning methods typically assume the one-class setting, in which the training data is clean with all normal samples $[3, 45, 41]$ . However, in practice, datasets can contain an unknown proportion of unlabeled anomalies $[7]$ , and in many cases a number of anomalies can be labeled with little cost $[38]$ . Although some works treat the one-class scenario as a special case of semi-supervised learning $[21, 36]$ , we distinguish three supervision regimes for clarity. We refer to the case of a clean training set as the one-class setting, the case of unlabeled but potentially contaminated training data as the unsupervised setting, and to that with a small number of labeled anomalies as the semi-supervised setting, where unlabeled samples are not assumed to be normal. While specialized methods exist for each regime $[38, 30]$ , their objectives are typically tied to the assumed supervision setting, and models trained under one regime may not apply to others or fail to generalize robustly when applied across settings $[21]$ .

These limitations motivate an approach that can acquire inductive biases aligned to tabular anomaly detection and adapt inference behavior to different supervision regimes. This can be achieved through in-context learning, a paradigm that allows a model to adapt inference from the training data provided as a context, without updating model parameters. In the case of anomaly detection, a model can infer the supervision regime from the labels in the context and modulate the decision function accordingly. Such in-context adaptation can be enabled through meta-learning over a distribution of tasks. With an appropriate distribution of tabular tasks, meta-learning can impart inductive biases suitable for tabular data. Recent tabular foundation models $[17, 18, 32]$ provide evidence for this approach, demonstrating that meta-learning on synthetic data can capture shared structure across tabular classification and regression problems. Contemporaneous work $[40]$ explores in-context learning for anomaly detection, yet the ability of a single model to adapt to different supervision regimes in anomaly detection remains underexplored.

We propose In-Context Learning for Anomaly Detection (ICLAD), a foundation model designed to generalize across tabular datasets and supervision regimes. A key component of our approach is the construction of a distribution of synthetic tabular anomaly detection tasks that vary in dataset characteristics, supervision assumptions, and anomaly contamination levels. ICLAD is implemented as a transformer trained on this task distribution. After this single training phase, the model can be reused on new datasets without updating its parameters. At inference time, ICLAD conditions on the training data and their associated labels as context, enabling adaptation to new datasets and supervision regimes through in-context learning. In this way, ICLAD captures generalizable patterns across tabular anomaly detection tasks and provides a unified framework for one-class, unsupervised, and semi-supervised settings.

![](images/22ffbd58b8b94069d17ca387a7dbad451215c576db3a6af177025a02fbbe5cb1.jpg)  
- Labeled Normal

![](images/108fa803a369eaa006a177b3cc375201ed9d5f076ccae01dc25fa88b74684f51.jpg)

![](images/562764a6723731bc019b46115ce76faf977c848d3d6070da13e12a79b220c203.jpg)

![](images/35c5690fc8d88b579dd46f59e0f7b8c5edb246ad59abb6023a055f94f2796988.jpg)  
(a) One-class setting

![](images/372814f7e8bf3777aa0d2a020378c83c654d565ed2733cbf9b21aa25cc3b9f02.jpg)

![](images/084af56f67cb9f6ecf399e4d287a3469a76dba6592e3f7f5fb0c90aadc464509.jpg)  
(b) Unsupervised setting  
(c) Semi-supervised setting  
Fig. 1: Each column corresponds to a training regime. The top row shows the training dataset, and the bottom row shows the test set and the anomaly-score landscape from ICLAD after conditioning on training dataset. In the test set, orange diamonds denote ground-truth anomalies and dark circles denote ground-truth normal samples. Darker regions indicate higher anomaly scores.

## The main contributions of this work are summarized as follows:

1. We introduce ICLAD, an in-context learning foundation model for tabular anomaly detection that performs task-level inference and generalizes across datasets and supervision regimes without retraining. To the best of our knowledge this work is the first to introduce a unified in-context anomaly detection model that generalize across anomaly detection supervision regimes.

2. We show that this capability arises from meta-learning on a diverse distribution of synthetic tabular tasks spanning dataset properties, supervision, and contamination levels.

3. We conduct an extensive empirical evaluation on ADBench [13], a benchmark of 57 real-world tabular datasets, comparing ICLAD with a wide range of classical and deep anomaly detection methods across unsupervised, one-class, and semi-supervised settings.

## 2 Related Work

## 2.1 One-Class and Unsupervised Tabular Anomaly Detection

Classical approaches to tabular anomaly detection typically operate directly in the input space or through shallow transformations. These include distance- and density-based methods such as kNN [33], LOF [6], CBLOF [14], and Isolation Forest [20]; one-class classification approaches such as OCSVM [39]; subspace-based methods such as PCA [43]; and statistical techniques such as HBOS [10] and ECOD [19]. Motivated by the success of deep learning, more recent work has explored using neural networks for tabular anomaly detection, including autoencoders [16], Deep SVDD [37], LUNAR [11], and various self-supervised representation learning approaches such as GOAD [3], ICL [41], MCM [47], NeutralAD [31], DRL [46], and SLAD [45]. DTE [21] introduces diffusion time as a proxy for outlier scoring, which is related to k-NN density estimation but with efficient neural approximations. While deep models offer greater representational flexibility, empirical studies suggest that they do not consistently outperform strong classical baselines on tabular datasets [21, 5, 13].

Another line of work in unsupervised tabular anomaly detection involves contamination-robust approaches. Most of the aforementioned methods, particularly deep methods, assume virtually clean training data aligned with the one-class setting. In the common scenario where there are unknown levels of contamination, these models often face deteriorating performance $[21]$ , motivating robust approaches such as the Minimum Covariance Determinant (MCD) $[35]$ and the recent iterative refinement methods like Latent Outlier Exposure (LOE) $[30]$ .

## 2.2 Semi-Supervised Anomaly Detection on Tabular Data

In the unsupervised setting, labeled anomalies can guide anomaly detection by providing prior information. In this case, anomaly detection can be framed as a semi-supervised learning problem related to positive-unlabeled (PU) learning. Representative methods include DevNet $[27]$ , PreNet $[26]$ , FEAWAD $[49]$ , and GANomaly $[1]$ . These methods rely on objectives that require labeled anomalies during training and are therefore tied to the semi-supervision regime. DeepSAD $[38]$ partially addresses this by extending Deep SVDD with the ability to utilize supervision, but still requires retraining when supervision levels change.

## 2.3 Prior-data Fitted Networks

Prior-data fitted networks (PFNs) [24] are models trained to perform in-context learning by meta-learning over a distribution of related tasks, often instantiated through synthetic datasets. PFNs amortize Bayesian inference over data-generating mechanisms into a single training stage, enabling in-context adaptation on new datasets without parameter updates. The representative PFN-based models for tabular data are TabPFN [17, 18] and TabICL [32], which achieve strong performance on tabular classification and regression. These models demonstrate that in-context learning can capture shared structure across tabular tasks and generalize effectively to unseen datasets without retraining. Recently, a similar work Fomo-0D [40] investigated a PFN framework to one-class anomaly detection, showing that outliers can be identified through in-context learning. However, a crucial direction remains under-explored, i.e., the capability of in-context learning model to adapt its inductive bias to targeted supervision settings, which we hypothesize to be a natural capability of PFNs. In this work, we also adopt the PFN paradigm for tabular anomaly detection but with a focus on in-context adaptation across supervision regimes.

## 3 In-Context Learning for Tabular AD

## 3.1 Problem Formulation

We begin by reformulating tabular anomaly detection as a task-level inference problem. We are given a training/context dataset $\mathcal{C} = (\mathcal{X}, \mathcal{Y})$ , where $X = \{x_i\}_{i=1}^N$ denotes tabular samples that may contain an unknown but typically small proportion of anomalies and $Y = \{y_i\}_{i=1}^N$ denotes labels with $y_i \in \{0, 1, \varnothing\}$ , where 0 indicates normal samples, 1 indicates anomalous samples, and $\varnothing$ denotes the absence of a label. The goal is to infer a context-conditioned anomaly scoring function $s(\cdot \mid \mathcal{C}) : \mathbb{R}^d \to \mathbb{R}$ , which, when applied to unseen (query) samples, assigns higher scores to anomalous samples than to normal samples.

This formulation unifies common supervision regimes in tabular anomaly detection as special cases of the same task-level inference problem. In the one-class setting, all samples are assumed to be normal and labeled as such, i.e., $y_{i} = 0$ for all i. In the unsupervised setting, labels are completely absent ( $y_{i} = \varnothing$ for all i), and the context may contain an unknown proportion of anomalous samples. In the semi-supervised setting, a small subset of anomalies are labeled as anomalous ( $y_{i} = 1$ ), while the remaining samples are unlabeled. Importantly, in all cases, the absence of a label does not imply normality, and neither the supervision regime nor the contamination level is assumed to be known to the model a priori, i.e. before observing the training set.

## 3.2 Context-Conditioned Anomaly Scoring

We interpret anomaly detection as estimating the probability that a query sample is anomalous given a context dataset. Concretely, given a dataset C, we define the anomaly score of a query sample x as the conditional probability

$$
s (x \mid \mathcal {C}) = p (y = 1 \mid x, \mathcal {C}),
$$

This formulation conditions the anomaly score on both the distributional patterns present in the dataset and any supervision available in the context.

From a probabilistic perspective, this conditional probability can also reflect the uncertainty over the underlying data-generating process. Let $\phi$ denote a latent data-generating mechanism drawn from a prior distribution $\Pi$ . Conditioning on the context induces a posterior over plausible mechanisms, and the anomaly score can be interpreted as a posterior predictive distribution (PPD):

$$
p (y = 1 \mid x, \mathcal {C}) = \int_ {\Pi} p (y = 1 \mid x, \phi) p (\phi \mid \mathcal {C}) d \phi .\tag{1}
$$

Although this probability is generally intractable to compute, it motivates an approach that approximates the mapping from $(x,\mathcal{C})$ to $p(y=1\mid x,\mathcal{C})$ directly. PFNs learn this mapping by training over a large number of synthetic tasks sampled from the prior distribution. During inference, a PFN estimates the PPD by in-context learning, and thus approximates Bayesian inference over data-generating mechanisms of normal and anomalous samples.

![](images/148e1c6637fb368306b63f78e728de6471d86881a41b6457ca4a350c00f0ec56.jpg)  
Fig. 2: Overview of the ICLAD framework and synthetic task construction. The top region depicts anomaly generation and the construction of supervision tasks. The bottom region shows the two-stage procedure of ICLAD. Left: prior-fitting on synthetic tasks. Right: inference on real datasets.

## 4 ICLAD Framework

We propose ICLAD, an in-context learning framework for tabular anomaly detection that unifies one-class, unsupervised, and semi-supervised settings using a single model trained on a distribution of anomaly tasks. ICLAD follows a two-stage procedure consisting of a prior-fitting stage and an inference stage.

Prior-Fitting Stage In this stage, we train an in-context learning model $q_{\theta}$ parameterized by weights $\theta$ on synthetic anomaly detection tasks sampled from a distribution $p(\mathcal{T})$ . Each task T consists of a support set $D_{support}$ and a query set $\mathcal{D}_{\mathrm{query}} = \{(x_j, y_j)\}_{j=1}^M$ . The support set defines the context, which conditions the model's predictions for query samples. The model parameters $\theta$ are optimized by minimizing the binary classification error on the query samples using the following objective:

$$
\mathcal {L} _ {B C E} = \mathbb {E} _ {\mathcal {T} \sim p (\mathcal {T})} \left[ \mathrm{BCE} \left(y _ {j}, q _ {\theta} (x _ {j} \mid \mathcal {D} _ {\mathrm{support}})\right) \right],
$$

where BCE denotes the binary cross-entropy loss, and the expectation is taken over a large number of tasks sampled from $p(\mathcal{T})$ . After training, the model $q_{\theta}$ effectively approximates the anomaly scoring as defined in Equation 1.

Inference Stage At inference time, the learned parameters $\hat{\theta}$ are fixed. Given a real dataset $D_{train}$ , we treat it as the support set and compute the context-conditioned anomaly scores for new samples using the model $q_{\hat{\theta}}(\cdot \mid \mathcal{D}_{\mathrm{train}})$ .

![](images/52f86409cc21f33885aebfbcfad7d31dae4b7a166a86c35313e006d218b05b2d.jpg)  
(a) SCM Anomalies

![](images/50c4191c9eb11e5d9a4d16d06367012f7802231b333f1715294fef6ef671a686.jpg)  
(b) Perturbation-based Anomalies  
Fig. 3: Feature interaction and t-SNE [22] plots of normal and anomalous samples. The orange rectangles are anomalies; the blue circles are normal samples.

ICLAD can thus adapt its scoring behavior based on context data, requiring only forward computations at test time. Notably, the predictions for query samples are conditionally independent given the support set and are not influenced by other query instances.

## 4.1 Synthetic Anomaly Detection Tasks

To enable generalization across tabular anomaly detection tasks with diverse data characteristics and supervision settings, we construct a synthetic task distribution that reflects this variability. Task generation consists of three stages: (i) sampling tabular datasets from structural causal models (SCMs) (ii) generating anomalies through structural and perturbation-based mechanisms, and (iii) constructing tasks under one-class, unsupervised and semi-supervised regimes.

Simulating Tabular Datasets We generate synthetic tabular datasets using the structural causal model (SCM) prior introduced in TabPFN [17]. An SCM defines a joint distribution over variables through a directed acyclic graph (DAG) $G_{scm}$ , where each variable $z_{i}$ is generated by a causal mechanism $z_{i} = f_{i}(z_{\mathrm{pa}(i)}, \epsilon_{i})$ , with $\mathrm{pa}(i)$ denoting the parents of node i, $f_{i}$ a deterministic function, and $\epsilon_{i}$ a Gaussian noise term.

Synthetic datasets are obtained by sampling from the SCM and selecting a subset of variables as observed features. One variable is discretized to form a binary label $y \in \{0,1\}$ , which induces class-conditional distributions $p_{\mathrm{scm}}(x \mid y)$ that correspond to normal $(y = 0)$ and anomalous $(y = 1)$ samples. To emulate real tabular data, a random subset of features is discretized to produce mixed continuous and categorical variables. This process creates datasets with varying dimensionality, heterogeneous feature types, and complex feature relationships.

Simulating Anomalies To model the diversity of anomalies encountered in practice, we employ two complementary anomaly generation mechanisms. The first mechanism produces structural anomalies by sampling from the anomalous class generated by the SCM, $p_{scm}(x \mid y = 1)$ , resulting in samples that exhibit global distributional shifts relative to the normal data, which are sampled from the distribution $p_{scm}(x \mid y = 0)$ . These anomalies reflect shifts in the underlying causal mechanisms and capture structured, semantic deviations relative to normal samples as shown in Figure 3a. Crucially, these samples share an underlying relational structure which, when labeled, can create meaningful supervision to guide anomaly scoring in semi-supervised setting.

The second mechanism generates perturbation-based anomalies by corrupting selected features of normal samples. For continuous features, we sample a feature-wise sparsity mask from a Bernoulli distribution for each sample and apply additive Gaussian noise,

$$
\tilde {x} _ {i} = x _ {i} + m _ {i} \sigma_ {i} \epsilon_ {i}, \quad \epsilon_ {i} \sim \mathcal {N} (0, 1),
$$

where $m_{i} \in \{0,1\}$ indicates whether feature i is perturbed and $\sigma_{i}$ is drawn independently per sample and feature from a log-uniform distribution. For categorical features, corruption is implemented by randomly replacing the original value with another valid category.

Constructing Supervision Tasks A central component of ICLAD is the construction of synthetic anomaly detection tasks which span the commonly encountered supervision regimes. Each task consists of a support or the context set $\mathcal{D}_{\mathrm{support}} = (X_{\mathrm{support}}, Y_{\mathrm{support}})$ and a query set $\mathcal{D}_{\mathrm{query}} = (X_{\mathrm{query}}, Y_{\mathrm{query}})$ . Query labels satisfy $Y_{query} \in \{0, 1\}$ , while support labels satisfy $Y_{support} \in \{-1, 0, 1\}$ , where -1 denotes unlabeled samples. The query set is constructed as a balanced mixture of normal and anomalous samples with equal proportions of structural and perturbation-based anomalies.

Contrary to the query set, the composition and labeling of the support set vary across tasks to simulate different supervision regimes:

1. In the one-class setting, the support set contains only normal samples drawn from $p_{\mathrm{scm}}(x \mid y = 0)$ , and all support labels are 0.

2. In the unsupervised regime, the support set is unlabeled and contaminated with anomalies. The anomaly ratio is sampled uniformly from $[0,0.4]$ and all labels in $Y_{support}$ are -1, indicating unknown.

3. In the semi-supervised regime, the support set is constructed as in the unsupervised setting, but a uniformly sampled fraction of anomalous samples is labeled as 1, while all remaining samples remain -1.

Across all regimes, all anomalous samples in the support set are drawn from the structural anomaly class induced by the SCM. Perturbation-based anomalies are applied in the query set which complements the structural anomalies and guide the model to detect anomalies beyond the support of labeled anomalies, i.e. open-set anomalies. During the prior-data fitting, we uniformly sample tasks from the one-class, unsupervised, and semi-supervised regimes, exposing the model to diverse supervision scenarios and enabling it to infer the supervision setting from its context. The resulting joint distribution over SCMs, supervision regimes, and anomaly generation mechanisms defines the prior we designed for tabular anomaly detection.

## 4.2 Model Architecture

ICLAD adopts the transformer architecture of TabPFN [17], where support and query samples are processed jointly using an asymmetric attention pattern that prevents information leakage between queries and implements $q_{\theta}(\cdot \mid \mathcal{D}_{support})$ . Input samples are zero-padded to a fixed dimension of 512 and projected to the model embedding space, and labels are embedded using a lookup table $E_{y}$ with unlabeled samples mapped to the zero vector.

FiLM Label Conditioning To incorporate supervision signals in the support set, we apply feature-wise linear modulation (FiLM) [29] to support sample embeddings. Given an embedding x and its label embedding $c = E_{y}(y)$ , FiLM computes

$$
\tilde {x} = (1 + \gamma (c)) \odot x + \beta (c),
$$

where $\gamma(\cdot)$ and $\beta(\cdot)$ are learned linear mappings. Unlabeled samples correspond to c=0, for which FiLM reduces to the identity transformation.

## 4.3 Key Implementation Details

In this section, we provide some key implementation details and defer the complete details to section A of the supplementary materials.

Training We instantiate ICLAD as a 12-layer Transformer [44] trained over 52 million tasks. Training takes about 53 hours over 4 Nvidia H100 GPUs.

Context Size and Feature Size During the prior fitting, the number of support samples is sampled uniformly from 5 to 12,000, with feature dimensions ranging from 2 to 512, which enables ICLAD to be directly applicable on moderate sized tabular datasets. Adapting to larger datasets or those with higher dimensionality is enabled through feature and context subsampling.

Ensembling Following standard PFN implementations, predictions are averaged across multiple ensemble tasks, each operating on different subsets of support samples and feature ordering or feature subsets. This generally improves performance and makes predictions more invariant to feature permutations.

KV Caching Since the predictions are conditionally independent given the support set, we decouple the processing of context samples from query evaluation using key-value (KV) caching. This allows support representations to be computed once and reused across query batches and enables an efficient two-stage fit-and-predict pipeline.

## 5 Experiments

## 5.1 Setup

We evaluate ICLAD on the ADBench benchmark suite, which contains 57 real-world anomaly detection tabular datasets. These datasets cover a wide range of data characteristics and anomaly ratios, to illustrate, dimensionality ranges from 3 to up to 1,555, and anomaly ratios vary from approximately 3% to 39%.

Experiments are conducted under the one-class, unsupervised, and semi-supervised settings. In the one-class setting, the training dataset is constructed by sampling 50% of the normal samples from the full dataset without replacement. The remaining normal samples together with all anomalous samples form the test set. In the unsupervised setting, we follow the protocol proposed by DTE [21], where the training set is obtained by bootstrapping for robustness evaluation, and the full dataset is used for testing. In the semi-supervised setting, datasets are partitioned into 70% training and 30% test data using stratified sampling to preserve the original anomaly ratio. Within the same training data, a fraction $r_{a}$ of anomalous samples is randomly selected and assigned anomaly labels, while all remaining samples remain unlabeled.

We evaluate all methods using three standard anomaly detection metrics: AUC-ROC, AUC-PR, and F1. Due to space constraints, we report mainly AUC-ROC, while AUC-PR and F1 results are provided in section E of the supplementary. The statistical significance of model performance are assessed by critical difference (CD) diagrams based on the Friedman test with Wilcoxon-Holm post-hoc analysis at a significance level of 0.05 [9]. All experiments are repeated with five random seeds, and results are reported as the average performance over the seeds and datasets.

To maintain reasonable computation time, larger datasets are subsampled to a maximum of 100,000 samples. This is substantially larger than the 10,000 sample cap used in previous works $[13, 21]$ , allowing us to evaluate the scalability of ICLAD on larger datasets.

## 5.2 Baseline Methods

Classical Baselines We compare ICLAD against several widely used classical baselines, including CBLOF, ECOD, iForest, kNN, LOF, OCSVM, PCA, MCD, HBOS, and the non-parametric version of DTE, DTE-NP.

Deep Learning Baselines For deep learning models, we include Autoencoder (AE), Deep-SVDD, SLAD, ICL, GOAD, MCM, DRL, NeuTraLAD (NTL), LU-NAR, Fomo-0D, and the parametric DTE variants, DTE-C and DTE-IG. For the unsupervised learning scenario, we include LOE with the NTL backbone.

Semi-Supervised Baselines We select well known semi-supervised approaches such as DevNet, FeaWAD, DeepSAD, PreNet and GANomaly to measure how well ICLAD utilize available labels.

For hyperparameters, we use the default PyOD [8] configurations where applicable. Other methods follow their recommended settings.

![](images/52c3e3a39bfac52098e46e3a0c06bca029c7d15b2230285ca2163b1832060dde.jpg)

(a) One-class setting  
![](images/3df8345acc4a899e1130ccbd29ccff15d2ef8907524bd6705f85b07389dff204.jpg)  
(b) Unsupervised setting  
Fig. 4: Boxplots of AUC-ROC across 57 datasets. Boxes show the interquartile range (IQR) with medians indicated by the center line and whiskers extending to 1.5 times IQR. Models are ordered by average AUC-ROC and color-coded by family: classical (green), deep learning (blue), and ICLAD (red).

## 6 Results

One-class and Unsupervised Regimes Figure 4 reports the performances in the one-class and unsupervised setting. ICLAD achieves the highest average AUC-ROC among all baselines which shows strong generalization to real world datasets. In the one-class setting, ICLAD achieves decent improvement gains over prior arts with wider performance gaps in AUC-PR and F1 scores. This is further supported by the CD-diagram in Figure 5, showing that ICLAD obtains the lowest average rank. Notably, DTE-NP, a variant of kNN, performs strongly in this regime and appears in the same top-performing clique as ICLAD under the Wilcoxon–Holm post-hoc test. This is consistent with prior observations that local-density methods are highly competitive under the one-class setting $[21, 41]$ .

In the unsupervised regime, ICLAD's performance is on par with contamination robust methods such as MCD and strong classical baselines including CBLOF and iForest, as illustrated in the boxplot and CD diagram. While we do not observe significant differences in performance compared to these baselines, it is important to note that strong performing methods in the one-class setting are generally less robust under this setting. For example, DTE-NP and LUNAR exhibit large performance drops due to their sensitivity to contamination in the training data. In contrast, ICLAD demonstrates greater robustness to contamination and is the only method that consistently ranks among the top performers across both the one-class and unsupervised settings.

![](images/8e942ca00fb0ccd1591dd7d7eeaf8b0a566b3f61f429b3f56257a0988f4f0873.jpg)

(a) One-class setting  
![](images/1538a4a6ac1f6d25aaefb68dc8d7bda887864203f9ad59d1b9f450a29d4d3d3f.jpg)  
(b) Unsupervised setting  
Fig. 5: Critical difference diagrams of average AUC-ROC ranks. Models are color coded by: classical (green), deep learning (blue) and ICLAD (red)

Semi-supervised Regime In the semi-supervised setting, where partial supervision is available through labeled anomalies, substantial performance improvements are observed across all methods, as shown in Figure 6. With 5% labeled anomalies, nearly all semi-supervised baselines outperform ICLAD in the unsupervised setting, showcasing the benefit of label information. Notably, ICLAD maintains a performance margin over all baselines in both the AUC-ROC and AUC-PR curves. Furthermore, with only 10% labeled anomalies, ICLAD achieves a 10% increase in AUC-ROC compared to its unsupervised counterpart, demonstrating that the model benefits significantly from partial supervision.

## 6.1 Ablation and efficiency analysis

For the ablation study, we evaluate variants of ICLAD trained with only unsupervised tasks, only one-class tasks, and a version using only SCM-based anomalies.

![](images/00066eded977b24ba86ff9fb60c2b1a40c8c2ffa2ef9a2692350c4f74d60fb26.jpg)

Fig. 6: Semi-supervised performance curves against ratio of labeled anomalies. Left: AUC-ROC Right: AUC-PR  
![](images/170113c5b8faca1477f034b803d5aae2e6c72d3d52215d9441da99d83d6841c6.jpg)

<table><tr><td>Variants</td><td>One-class</td><td>Unsup.</td></tr><tr><td>One-class only</td><td>84.00</td><td>68.26</td></tr><tr><td>Unsup. only</td><td>82.61</td><td>74.80</td></tr><tr><td>SCM only</td><td>83.37</td><td>74.14</td></tr><tr><td>ICLAD</td><td>83.97</td><td>75.17</td></tr></table>

Fig. 7: Efficiency and ablation analysis. Left Top: average inference runtime (seconds). Left Bottom: average total runtime (training + inference)(seconds). Runtime axes use a log scale. Right: Ablation study of ICLAD variants. Performance are measured in average AUC-ROC across the respective supervision setting.

As expected, the one-class-only model performs best in the one-class setting, yet the model degrades substantially on the unsupervised benchmark as shown on the right of Figure 7. Our model has the most balanced performance out of the variants over one-class and unsupervised benchmarks. This justifies the inclusion of unsupervised tasks as well as perturbation-based anomalies in the query set.

In terms of efficiency, ICLAD exhibits moderate inference time due to the quadratic complexity of self-attention. Nevertheless, when considering the total runtime (training and inference), it remains competitive and is only outperformed by traditional baselines as shown on the left of Figure 7. All runtime measurements were conducted on a single NVIDIA H100 GPU.

## 7 Conclusion

We introduced ICLAD, an in-context learning framework for anomaly detection. The empirical results show ICLAD acquires inductive bias aligned to real-world anomaly detection problems and achieves consistently competitive performance in all three supervision settings. Our findings suggest that in-context learning provides a promising direction for more general anomaly detection systems. Future works can focus on developing better synthetic task generation strategies that improves generalization especially under the case of anomaly contamination.

## References

1. Akcay, S., Atapour-Abarghouei, A., Breckon, T.P.: GANomaly: Semi-supervised Anomaly Detection via Adversarial Training. In: Jawahar, C.V., Li, H., Mori, G., Schindler, K. (eds.) Computer Vision – ACCV 2018. pp. 622–637. Springer International Publishing, Cham (2019)

2. Alrawashdeh, K., Purdy, C.: Toward an Online Anomaly Intrusion Detection System Based on Deep Learning. In: 2016 15th IEEE International Conference on Machine Learning and Applications (ICMLA). pp. 195–200 (Dec 2016)

3. Bergman, L., Hoshen, Y.: Classification-Based Anomaly Detection for General Data. In: International Conference on Learning Representations (Sep 2019)

4. Borisov, V., Leemann, T., Seßler, K., Haug, J., Pawelczyk, M., Kasneci, G.: Deep neural networks and tabular data: A survey. IEEE transactions on neural networks and learning systems 35(6), 7499–7519 (2022)

5. Bouman, R., Bukhsh, Z., Heskes, T.: Unsupervised anomaly detection algorithms on real-world data: How many do we need? J. Mach. Learn. Res. 25(1), 105:5199–105:5232 (Jan 2024)

6. Breunig, M.M., Kriegel, H.P., Ng, R.T., Sander, J.: LOF: Identifying density-based local outliers. SIGMOD Rec. 29(2), 93–104 (May 2000)

7. Chalapathy, R., Chawla, S.: Deep learning for anomaly detection: A survey. arXiv preprint arXiv:1901.03407 (2019)

8. Chen, S., Qian, Z., Siu, W., Hu, X., Li, J., Li, S., Qin, Y., Yang, T., Xiao, Z., Ye, W., Zhang, Y., Dong, Y., Zhao, Y.: PyOD 2: A Python Library for Outlier Detection with LLM-powered Model Selection. In: Companion Proceedings of the ACM on Web Conference 2025. pp. 2807–2810. WWW '25, Association for Computing Machinery, New York, NY, USA (May 2025)

9. Demšar, J.: Statistical Comparisons of Classifiers over Multiple Data Sets. J. Mach. Learn. Res. 7, 1–30 (Dec 2006)

10. Goldstein, M., Dengel, A.: Histogram-based Outlier Score (HBOS): A fast Unsupervised Anomaly Detection Algorithm (2012)

11. Goodge, A., Hooi, B., Ng, S.K., Ng, W.S.: LUNAR: Unifying Local Outlier Detection Methods via Graph Neural Networks. Proceedings of the AAAI Conference on Artificial Intelligence 36(6), 6737–6745 (Jun 2022)

12. Grinsztajn, L., Oyallon, E., Varoquaux, G.: Why do tree-based models still outperform deep learning on typical tabular data? In: Proceedings of the 36th International Conference on Neural Information Processing Systems. pp. 507–520. NIPS '22, Curran Associates Inc., Red Hook, NY, USA (Nov 2022)

13. Han, S., Hu, X., Huang, H., Jiang, M., Zhao, Y.: ADBench: Anomaly Detection Benchmark. In: Thirty-Sixth Conference on Neural Information Processing Systems Datasets and Benchmarks Track (Jun 2022)

14. He, Z., Xu, X., Deng, S.: Discovering cluster-based local outliers. Pattern Recognition Letters 24(9), 1641–1650 (Jun 2003)

15. Hendrycks, D., Gimpel, K.: Gaussian Error Linear Units (GELUs) (Jun 2023)

16. Hinton, G.E., Salakhutdinov, R.R.: Reducing the Dimensionality of Data with Neural Networks. Science 313(5786), 504–507 (Jul 2006)

17. Hollmann, N., Müller, S., Eggensperger, K., Hutter, F.: TabPFN: A Transformer That Solves Small Tabular Classification Problems in a Second. In: The Eleventh International Conference on Learning Representations (Sep 2022)

18. Hollmann, N., Müller, S., Purucker, L., Krishnakumar, A., Körfer, M., Hoo, S.B., Schirrmeister, R.T., Hutter, F.: Accurate predictions on small data with a tabular foundation model. Nature 637(8045), 319–326 (Jan 2025)

19. Li, Z., Zhao, Y., Hu, X., Botta, N., Ionescu, C., Chen, G.H.: ECOD: Unsupervised Outlier Detection Using Empirical Cumulative Distribution Functions. IEEE Transactions on Knowledge and Data Engineering 35(12), 12181–12193 (Dec 2023)

20. Liu, F.T., Ting, K.M., Zhou, Z.H.: Isolation Forest. In: Proceedings of the 2008 Eighth IEEE International Conference on Data Mining. pp. 413–422. ICDM '08, IEEE Computer Society, USA (Dec 2008)

21. Livernoche, V., Jain, V., Hezaveh, Y., Ravanbakhsh, S.: On Diffusion Modeling for Anomaly Detection. In: The Twelfth International Conference on Learning Representations (Oct 2023)

22. van der Maaten, L., Hinton, G.: Visualizing Data using t-SNE. Journal of Machine Learning Research 9(86), 2579–2605 (2008)

23. McElfresh, D., Khandagale, S., Valverde, J., C., V.P., Ramakrishnan, G., Goldblum, M., White, C.: When do neural nets outperform boosted trees on tabular data? In: Proceedings of the 37th International Conference on Neural Information Processing Systems. pp. 76336–76369. NIPS '23, Curran Associates Inc., Red Hook, NY, USA (Dec 2023)

24. Müller, S., Hollmann, N., Arango, S.P., Grabocka, J., Hutter, F.: Transformers Can Do Bayesian Inference. In: International Conference on Learning Representations (Oct 2021)

25. Pang, G., Shen, C., Cao, L., Hengel, A.V.D.: Deep Learning for Anomaly Detection: A Review. ACM Comput. Surv. 54(2), 38:1–38:38 (Mar 2021)

26. Pang, G., Shen, C., Jin, H., van den Hengel, A.: Deep Weakly-supervised Anomaly Detection. In: Proceedings of the 29th ACM SIGKDD Conference on Knowledge Discovery and Data Mining. pp. 1795–1807. KDD '23, Association for Computing Machinery, New York, NY, USA (Aug 2023)

27. Pang, G., Shen, C., van den Hengel, A.: Deep Anomaly Detection with Deviation Networks. In: Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining. pp. 353–362. KDD '19, Association for Computing Machinery, New York, NY, USA (Jul 2019)

28. Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., Duchesnay, É.: Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research 12(85), 2825–2830 (2011)

29. Perez, E., Strub, F., de Vries, H., Dumoulin, V., Courville, A.: FiLM: Visual reasoning with a general conditioning layer. In: Proceedings of the Thirty-Second AAAI

Conference on Artificial Intelligence and Thirtieth Innovative Applications of Artificial Intelligence Conference and Eighth AAAI Symposium on Educational Advances in Artificial Intelligence. pp. 3942–3951. AAAI'18/IAAI'18/EAAI'18, AAAI Press, New Orleans, Louisiana, USA (Feb 2018)

30. Qiu, C., Li, A., Kloft, M., Rudolph, M., Mandt, S.: Latent Outlier Exposure for Anomaly Detection with Contaminated Data. In: Proceedings of the 39th International Conference on Machine Learning. pp. 18153–18167. PMLR (Jun 2022)

31. Qiu, C., Pfrommer, T., Kloft, M., Mandt, S., Rudolph, M.: Neural Transformation Learning for Deep Anomaly Detection Beyond Images. In: Proceedings of the 38th International Conference on Machine Learning. pp. 8703–8714. PMLR (Jul 2021)

32. Qu, J., Holzmüller, D., Varoquaux, G., Morvan, M.L.: TabICL: A Tabular Foundation Model for In-Context Learning on Large Data. In: Forty-Second International Conference on Machine Learning (Jun 2025)

33. Ramaswamy, S., Rastogi, R., Shim, K.: Efficient algorithms for mining outliers from large data sets. SIGMOD Rec. 29(2), 427–438 (May 2000)

34. Ringler, N., Knittel, D., Nouari, M., Ponsart, J.C., Yakob, A., Romani, D.: Unsupervised Anomaly Detection using Vibration Signals for Milling Processes. 20th CIRP Conference on Modeling of Machining Operations in Mons 133, 710–715 (Jan 2025)

35. Rousseeuw, P.J.: Least Median of Squares Regression. Journal of the American Statistical Association 79(388), 871–880 (Dec 1984)

36. Ruff, L., Kauffmann, J.R., Vandermeulen, R.A., Montavon, G., Samek, W., Kloft, M., Dietterich, T.G., Müller, K.R.: A unifying review of deep and shallow anomaly detection. Proceedings of the IEEE 109(5), 756–795 (2021)

37. Ruff, L., Vandermeulen, R., Goernitz, N., Deecke, L., Siddiqui, S.A., Binder, A., Müller, E., Kloft, M.: Deep One-Class Classification. In: Proceedings of the 35th International Conference on Machine Learning. pp. 4393–4402. PMLR (Jul 2018)

38. Ruff, L., Vandermeulen, R.A., Görnitz, N., Binder, A., Müller, E., Müller, K.R., Kloft, M.: Deep Semi-Supervised Anomaly Detection. In: International Conference on Learning Representations (Sep 2019)

39. Schölkopf, B., Williamson, R.C., Smola, A., Shawe-Taylor, J., Platt, J.: Support Vector Method for Novelty Detection. In: Advances in Neural Information Processing Systems. vol. 12. MIT Press (1999)

40. Shen, Y., Wen, H., Akoglu, L.: FoMo-0D: A Foundation Model for Zero-shot Tabular Outlier Detection. Transactions on Machine Learning Research (May 2025)

41. Shenkar, T., Wolf, L.: Anomaly Detection for Tabular Data with Internal Contrastive Learning. In: International Conference on Learning Representations (Oct 2021)

42. Shwartz-Ziv, R., Armon, A.: Tabular data: Deep learning is not all you need. Information Fusion 81, 84–90 (May 2022)

43. Shyu, M.L., Chen, S.C., Sarinnapakorn, K., Chang, L.: A novel anomaly detection scheme based on principal component classifier (2003)

44. Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A.N., ukasz Kaiser, Ł., Polosukhin, I.: Attention is All you Need. In: Advances in Neural Information Processing Systems. vol. 30. Curran Associates, Inc. (2017)

45. Xu, H., Wang, Y., Wei, J., Jian, S., Li, Y., Liu, N.: Fascinating supervisory signals and where to find them: Deep anomaly detection with scale learning. In: Proceedings of the 40th International Conference on Machine Learning. ICML'23, vol. 202, pp. 38655–38673. JMLR.org, Honolulu, Hawaii, USA (Jul 2023)

46. Ye, H., Zhao, H., Fan, W., Zhou, M., dan Guo, D., Chang, Y.: DRL: Decomposed Representation Learning for Tabular Anomaly Detection. In: The Thirteenth International Conference on Learning Representations (Oct 2024)

47. Yin, J., Qiao, Y., Zhou, Z., Wang, X., Yang, J.: MCM: Masked Cell Modeling for Anomaly Detection in Tabular Data. In: The Twelfth International Conference on Learning Representations (Oct 2023)

48. Yousef, H., Feng, S.F., Jelinek, H.F.: Exploratory risk prediction of type II diabetes with isolation forests and novel biomarkers. Scientific Reports 14(1), 14409 (Jun 2024)

49. Zhou, Y., Song, X., Zhang, Y., Liu, F., Zhu, C., Liu, L.: Feature Encoding With Autoencoders for Weakly Supervised Anomaly Detection. IEEE Transactions on Neural Networks and Learning Systems 33(6), 2454–2465 (Jun 2022)

## A Additional Implementation Details

## A.1 Model Architecture

We adapt the Transformer encoder architecture $[44]$ from TabPFN $[18]$ in our implementation of ICLAD. The transformer encoder consists of 12 layers, each with 4 attention heads, a hidden dimension of 512, and a feed-forward network with an intermediate dimension of 1024. The feed-forward networks employs the GELU activation function $[15]$ . We adopt a post-normalization architecture, following the original Transformer implementation, but omit positional encodings to respect the permutation invariance of independent tabular samples. The model contains approximately 26.5 million trainable parameters.

## A.2 Input Preprocessing

All features are standardized using z-score normalization and clipped to the range [-100, 100] to improve numerical stability during optimization. The ICLAD model assumes that all inputs are preprocessed in this manner. For each task, consisting of a support set and a query set, normalization is performed using the mean and standard deviation computed from the support set only. Specifically, for each feature j, we compute the mean $\mu_{j}$ and standard deviation $\sigma_{j}$ over the support set, and normalize each sample's jth dimension x as

$$
\tilde {x} _ {j} = \frac {x _ {j} - \mu_ {j}}{\sigma_ {j}}.
$$

These statistics are then applied to both the support and query samples to prevent information leakage from the query set. Note that the z-score normalization is applied uniformly to all features, without distinguishing between continuous and discrete variables. This feature-type agnostic design aligns with previous anomaly detection approaches, which typically operate directly on vectorized features without specialized embeddings for categorical or ordinal variables. Following established protocols, we embed inputs as a vector, and all features are treated uniformly by the model. Features with zero variance are left unchanged, following the behavior of standard Scikit-learn implementation $[28]$ .

The maximum number of features admissible for the ICLAD transformer, $d_{max}$ , is set to 512, corresponding to the model hidden dimension. Input samples with fewer than $d_{max}$ features are zero-padded to $d_{max}$ , following TabPFN.

To ensure consistent input magnitudes across datasets with varying numbers of features $d_{in}$ , we rescale each zero-padded input vector $\tilde{x} \in R^{d_{max}}$ as

$$
x = \sqrt {\frac {d _ {\mathrm{max}}}{d _ {\mathrm{in}}}} \tilde {x}.
$$

Under the assumption that features are standardized, this scaling normalizes the expected squared $\ell_{2}$ -norm of the input vectors, making it approximately invariant to $d_{in}$ . This normalization step helps stabilize training and improves generalization across tabular datasets with varying dimensionality.

## A.3 Training and Optimization Details

The ICLAD model is trained for 100 epochs during the prior fitting stage using the Adam optimizer with no weight decay. Training is distributed across 4× NVIDIA H100 GPUs using mixed precision.

Each epoch consists of 2048 training steps. At each step, every GPU processes 16 tasks, resulting in a per-step batch size of 64 across all GPUs. We employ gradient accumulation over 8 steps, resulting in an effective batch size of 512 with 256 optimization steps per epoch. A learning rate schedule with linear warm-up (3 epochs) followed by cosine annealing is used, with a maximum learning rate of $1 \times 10^{-4}$ .

In total, ICLAD is trained on 13,107,200 synthetic anomaly detection tasks. Training takes approximately 55 wall-clock hours per GPU, corresponding to about 220 GPU hours in total.

## A.4 Key-Value Caching

We employ key-value (KV) caching to accelerate both training and inference by exploiting the asymmetric structure of in-context learning. In particular, query samples attend only to support samples, while support samples do not attend to queries. This allows the in-context learning inference to be decomposed into two stages.

Fitting stage Given a support set $X_{s}$ , we compute and cache the key and value representations at each layer:

$$
(K _ {s} ^ {(\ell)}, V _ {s} ^ {(\ell)}) = \mathrm{KVProj} ^ {(\ell)} (X _ {s}), \quad \ell = 1, \ldots , L.
$$

Predict stage Given a query set $X_{q}$ , we compute query representations and attend only to the cached support keys and values:

$$
\text { Attention } ^ {(\ell)} = \text { softmax } \left(\frac {Q _ {q} ^ {(\ell)} (K _ {s} ^ {(\ell)}) ^ {\top}}{\sqrt {d}}\right) V _ {s} ^ {(\ell)}.
$$

Compare to using full attention with specialized masks as in TabPFN $[17]$ , this avoids recomputing support representations for each query and reduces redundant attention operations, leading to improved efficiency.

## B Additional Details of Synthetic Prior Task Generation

In this section, we describe the construction of synthetic prior tasks used to train ICLAD. Following the prior-data fitted networks (PFN) framework, tasks are created using data-generating processes that define both the input distribution and the associated prediction objective. These processes are based on structural causal models (SCMs) and perturbation-based corruption mechanisms, each parameterized by task-specific hyperparameters.

![](images/e35d6a7e2caf99db6603cf8846db679ef60d214aadedd3db6a204c5af00ff4b5.jpg)  
Fig. 8: Two visual examples of SCM that can be sampled from the SCM prior. Gray circles represent observed variables and white circles are latent variables. $x_{i}$ are selected features and y is the (continuous) target variable.

## B.1 SCM Data Generation

While TabPFN considers a mixture of structural causal models (SCMs) and Bayesian neural networks (BNNs) during prior-data fitting, we adopt only the SCM prior. This choice is motivated by prior ablations showing that the SCM prior alone is sufficient to achieve strong performance across a wide range of tabular tasks, suggesting better alignment with real-world tabular data.

We briefly describe the SCM generation process (see Appendix C.1 of [17] for full details). A directed acyclic graph (DAG) is first sampled to define dependencies among variables:

1. Sample the architecture of a multi-layer perceptron (MLP), including the number of layers $\ell \sim p(\ell)$ and hidden nodes per layer $h \sim p(h)$ .

2. Initialize network weights using normal distributions and randomly drop connections to induce sparsity, resulting in a DAG structure, $G_{scm}$ .

3. Define each node as an affine transformation of its parent nodes followed by a randomly sampled activation function.

4. Assign each node a noise distribution $p(\epsilon)$ , sampled from a meta-distribution over noise distributions.

This defines a structured causal model, where each node is defined as $z_{i} = f_{i}(z_{\mathrm{pa}(i)},\epsilon_{i})$ . Given the sampled SCM, a tabular dataset is generated as follows:

1. Sample root variables (causes) from a mixture of Gaussian, multinomial, and Zipfian distributions.

2. Propagate samples through the DAG with additive noise, i.e., $\tilde{x} = x + \epsilon_i$ , where $\epsilon_i \sim p(\epsilon)$ and $i$ is the index of the node.

3. Randomly select $d_{in}$ nodes as input features $x_{i}$ and one node as the continuous target $\hat{y}$ .

4. With probability 0.5 generate mixed-type datasets, where each feature is independently converted to a discrete variable with probability $p \sim \mathcal{U}(0,1)$ . Otherwise, we generate homogeneous datasets: with probability 0.5 all features are discretized, and with probability 0.5 all features remain continuous. For categorical features, the number of categories is sampled as $k \sim \max(\text{round}(\text{Gamma}(1,8)), 1)$ , and values are obtained mapping values to interval indices, following the procedure used in TabPFN.

5. Discretize the continuous target $\hat{y}$ into a binary label y either by thresholding at its median or by assigning samples in the lower and upper quantiles (e.g., 25th and 75th percentiles) with probability 0.5 for each case.

Finally, this procedure allows the generation of synthetic tabular datasets while also enabling sampling from two distributions $p(x \mid y = 0)$ and $p(x \mid y = 1)$ . This forms the basis for the generation of normal samples and SCM anomalies.

## B.2 Perturbation-based Anomalies

In addition to SCM-based labels, we generate anomalies through feature-level perturbations. This approach produces anomalous samples independently of the SCM label and complements the SCM anomaly. For instance, SCM anomalies rarely represent large feature-wise deviations. These are large feature spikes are captured by the perturbation-based anomalies.

1. Generate a dataset using the SCM prior (steps 1–4 above).

2. Sample support and query sets according to the supervision regime.

3. Z-score normalize the features using statistics from the support set.

4. Apply corruption to half of the query samples labeled as anomalous:

(a) Categorical corruption Sample a corruption rate $\lambda \sim \mathcal{U}(0, \lambda_{\max})$ where $\lambda_{\max} = 1$ . For each categorical feature, replace its value with a uniformly sampled category with probability $\lambda$ .

(b) Continuous corruption For each sample, draw a sparsity rate $s \sim \mathcal{U}(0,1)$ . For each feature j, sample a mask $m_{j} \sim \text{Bernoulli}(s)$ . Apply the Gaussian noise:

$$
\tilde {x} _ {j} = x _ {j} + m _ {j} \sigma_ {j} \epsilon_ {j}, \quad \epsilon_ {j} \sim \mathcal {N} (0, 1),
$$

where $\sigma_{j}\sim\mathrm{LogUniform}(\sigma_{\mathrm{min}},\sigma_{\mathrm{max}})$ .

## B.3 Synthetic Tasks Hyperparameters

In this section, we summarize the hyperparameters in task generation. The SCM hyperparameters are listed in Tables 1 and 2, while hyperparameters for general task construction and perturbation-based anomalies are provided in Table 3.

Table 1: Categorical Hyperparameters and configuration settings for SCMs. Each is sampled independently with uniform probability per dataset.

<table><tr><td>Hyperparameter</td><td>Choices</td></tr><tr><td>Share node-wise noise</td><td>True, False</td></tr><tr><td>Apply blockwise dropout</td><td>True, False</td></tr><tr><td>Preserve feature order</td><td>True, False</td></tr><tr><td>Blockwise feature selection</td><td>True, False</td></tr><tr><td>Activation function</td><td>Tanh, ELU, Sigmoid, Identity, Sine, Softplus, Heaviside</td></tr></table>

Table 2: Continuous hyperparameter distributions used in synthetic SCM generation. TNLU( $\mu$ , $\tilde{\mu}$ , round, min) denotes log-uniform distribution over parameter $\mu$ followed by a truncated log normal distribution with minimal values and potentially rounding the sampled value to the nearest integer.

<table><tr><td>Hyperparameter</td><td colspan="5">Distribution</td></tr><tr><td>MLP weight dropout</td><td colspan="5">0.9 Beta(a,b), where a,b~U(0.1,5.0)</td></tr><tr><td></td><td></td><td>Max μ</td><td>Min μ̃</td><td>Round</td><td>Min</td></tr><tr><td>MLP depth</td><td>TNLU</td><td>8</td><td>1</td><td>Yes</td><td>2</td></tr><tr><td>MLP width (hidden nodes)</td><td>TNLU</td><td>180</td><td>5</td><td>Yes</td><td>4</td></tr><tr><td>Number of Causes (Nodes at layer 1)</td><td>TNLU</td><td>12</td><td>1</td><td>Yes</td><td>1</td></tr><tr><td>SCM Node noise Std.</td><td>TNLU</td><td>0.3</td><td>0.0001</td><td>No</td><td>0.0</td></tr><tr><td>SCM Weight Std.</td><td>TNLU</td><td>10.0</td><td>0.01</td><td>No</td><td>0.0</td></tr></table>

Table 3: Hyperparameter distributions or constants used in task generation and perturbation-based anomalies.

<table><tr><td>Hyperparameter</td><td>Distribution / Constant</td></tr><tr><td>Dataset dimension  $d_{in}$ </td><td> $\mathcal{U}(2,512)$ </td></tr><tr><td>Support set size  $N_s$ </td><td> $\mathcal{U}(5,12000)$ </td></tr><tr><td>Query set size  $N_q$ </td><td>1024</td></tr><tr><td>Perturbation Noise Std. ( $\sigma_j$ )</td><td>LogUniform(0.1, 10.0)</td></tr><tr><td>Categorical corruption rate  $\lambda$ </td><td> $\mathcal{U}(0,1)$ </td></tr></table>

## B.4 Pseudocode for Tasks Construction across Supervision Regimes

Algorithm 1 provides a high-level description of the task construction procedure across supervision regimes.

Particularly, in line 2, the contamination ratio $\rho$ ranges from little to no anomaly contamination in the near 0 case to the extreme case of $40\%$ contamination. Line 14 to 16 shows supervision levels ranging from $0\%$ anomalies labeled to full partial supervision where $100\%$ of anomalies are labeled. Here, we also see that the unsupervised scenario is a special case of semi-supervised scenario where no supervision is available and one-class setting is a special case of unsupervised scenario.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Synthetic task construction across supervision regimes
Require: support size $N_{s}$, query size $N_{q}$, supervision regime weights $\pi$
Ensure: support set $(X_{s}, Y_{s})$ and query set $(X_{q}, Y_{q})$
1: Sample scenario $r \sim$ Categorical $(\pi)$, where $\pi = (\pi_{\text{one-class}}, \pi_{\text{unsup}}, \pi_{\text{semi}})$
2: Sample contamination ratio $\rho \sim \mathcal{U}(0, 0.4)$
3: Generate dataset $\mathcal{D}$ using the SCM prior
Support set construction
4: if $r =$ one-class then
5: Sample $N_{s}$ normal samples from $\mathcal{D}$
6: Set $Y_{s} \leftarrow 0$
7: else if $r =$ unsupervised then
8: Sample $N_{s}$ samples with contamination ratio $\rho$
9: Mark $N_{a} =$ round $(\rho N_{s})$ anomalous samples.
10: Set $Y_{s} \leftarrow -1$
11: else if $r =$ semi-supervised then
12: Sample $N_{s}$ samples with contamination ratio $\rho$
13: Mark $N_{a} =$ round $(\rho N_{s})$ anomalous samples.
14: Sample supervision ratio $\rho_{\text{sup}} \sim \mathcal{U}(0, 1)$
15: Mark $N_{sup} =$ round $(\rho_{sup} N_{a})$ anomalous samples to reveal labels.
16: Set $Y_{s} = 1$ for revealed anomalies and $Y_{s} = -1$ otherwise
17: end if
Query set construction
18: Sample $N_{q}/2$ normal samples and $N_{q}/2$ anomalous samples
19: Assign anomaly types for anomalous samples.
20: Replace half of query anomalous samples with SCM anomalies.
21: Replace the other half with perturbation-based anomalies.
Post-processing
22: Z-score normalize all samples using statistics from the support set
23: Apply perturbation-based corruption where required
24: return $(X_{s}, Y_{s}), (X_{q}, Y_{q})$
</div>

pervised setting where there is no contamination. This gradual transition from one setting to another motivates the need for a model that can adapt seamlessly to the full spectrum of supervision and contamination levels.

## C Additional Visualizations of SCM and Perturbation-based Anomalies

![](images/d0644c531c4b3ebbfa869c6556f3e8b388400c3f23c4fcde5d888fedb9844490.jpg)  
Fig. 9: Feature interaction and t-SNE plots of normal samples and SCM anomalies.

![](images/d3aeac76f6f412ea7c918d4c36d7dde8f7a157a61837c493cd64c5888a577072.jpg)  
Fig. 10: Feature interaction and t-SNE plots of normal and perturbation-based anomaly samples. The orange rectangles are anomalies and the blue circles represent normal samples.

## D Model and Synthetic Tasks Validation

We validate our models and synthetic tasks using a small development set and do not perform extensive per-dataset tuning. This design choice reflects our goal of evaluating ICLAD as a general-purpose in-context learner, rather than optimizing performance for individual datasets.

## D.1 Development Datasets

We validate ICLAD on a development set consisting of 7 datasets that are not part of the ADBench test suite. This separation helps prevent meta-overfitting to the test benchmarks during development. The development set includes 5 real-world datasets from [41], namely abalone, arrhythmia, ecoli, mulcross, and seismic. In addition, we construct two synthetic two-dimensional datasets based on the Scikit-learn moons and circles generators.

Supervision Regimes For each dataset, we construct three evaluation scenarios corresponding to our supervision regimes. These scenarios are designed to match the testing protocol we used for ADBench.

One-class setting Following the one-class protocols from previous works, we split the normal class into two disjoint subsets. One subset is used as the training set that contains only normal samples, while the other subset is combined with all anomaly samples to form the test set.

Unsupervised setting We construct the training set by sampling with replacement from the full dataset, resulting in a dataset with anomaly contamination. The test set is the full dataset.

Semi-supervised setting Starting from the unsupervised setting, we randomly label 10% of the anomalies in the training set, while the remaining samples remain unlabeled.

## E Additional Experimental Results

## E.1 One-class Setting Box Plots

![](images/233008b11e818c47f19ee95379d3fcced0673a6f790451ea9969c2cae1166218.jpg)  
Fig. 11: Boxplots for one-class setting. Boxes show the interquartile range (IQR) with medians indicated by the center line and whiskers extending to 1.5 times IQR. Models are ordered by average AUC-PR or F1 and color-coded by family: classical (green), deep learning (blue), and ICLAD (red).

Figures 11 shows the boxplots for AUC-PR and F1 in the one-class setting. The overall trends for both metrics are consistent with the AUC-ROC results reported in the main paper. We highlight the noticeable improvement in F1 over the baselines methods.

## E.2 Unsupervised Setting Box Plots

![](images/5482b34486c8eb2ef9f407f74df20d28dc9d090ccdd5647f25aba05791be1e13.jpg)  
Fig. 12: Boxplots for the unsupervised setting. Boxes show the interquartile range (IQR) with medians indicated by the center line and whiskers extending to 1.5 times IQR. Models are ordered by average AUC-PR or F1 and color-coded by family: classical (green), deep learning (blue), and ICLAD (red).

Figure 12 suggests that the AUC-PR and F1 results for ICLAD are on par with the best performing deep learning approaches but fall short of strong classical baselines. In contrast with the strong AUC-ROC results, this discrepancy suggest that contamination still degrades the model's ability to form a sharp decision boundary, affecting precision in the high anomaly score region. This result shows the persistent challenge in the unsupervised regime for deep learning approaches. Nevertheless, our framework partially bridges this gap by maintaining strong global ranking performance under contamination. This challenge also underlines the importance of supervision for deep learning approaches where even minimal labeled anomalies consistently lead to substantial improvements.

## E.3 One-class Setting Critical Difference Diagrams

![](images/4423ca0d88507dc89abe968798ecee0cde04663210f70054eb1eeb6f172a29dd.jpg)

(a) AUC-PR Ranks  
![](images/6087f828270a23269d61f624ebd072d5120001e066327f0d94cf072475700450.jpg)  
(b) F1 Ranks  
Fig. 13: Critical difference diagrams for the one-class setting.

Figure 13 further strengthens ICLAD superior performance in the one-class regime, particularly in terms of F1. While ICLAD is statistically competitive with the top-performing method LUNAR, it achieves a lower (better) average rank and improves upon strong baselines such as kNN and DTE-NP.

## E.4 Unsupervised Setting Critical Difference Diagrams

![](images/99f7eb9e406c043b9c1c37c6e39ad469ae7a4d1d1281e93abc9311f5f4d7f07e.jpg)

(a) AUC-PR Ranks  
![](images/86ed0e32e5b15728607d7820596cdbdcdda349a43799d34bae5421b487352e78.jpg)  
(b) F1 Ranks  
Fig. 14: Critical difference diagrams for the unsupervised setting.

The critical difference diagram in Figure 14 shows comparable performance across all methods in terms of AUC-PR and F1, with CBLOF achieving the best overall performance. ICLAD lies within the same statistical group as the top-performing methods, indicating competitive performance. Consistent with the bar plot results, deep learning models generally exhibit a loss in precision under anomaly contamination, whereas ICLAD demonstrates comparatively stronger robustness to contamination.

## E.5 Semi-supervised Setting F1 Curves

![](images/e7ee256c5f2dbfb10af6d881cf622bf46c6dfb8993ee216f4b843d7f6489ae1c.jpg)  
Fig. 15: Semi-supervised performance curves measured by F1 (%) against ratio of labeled anomalies.

Figure 15 show the improvements over F1 with increasing ratio of labeled anomalies provided to the semi-supervised models. As with AUC-ROC and AUC-PR, all methods except for GANomaly benefit significantly from partial supervision. Although ICLAD's F1 performance is generally comparable to PreNet and DevNet when $1\%$ of anomalies are labeled, ICLAD's performance gap with stronger baselines start to manifest when $10\%$ of anomalies are available with the gap increasing with more labeled anomalies. This trend shows that ICLAD utilizes labeled more effectively than other semi-supervised models.

## E.6 Total Time vs Average AUC-ROC plots

![](images/6e25dd5696b50e87cefa4a7900c00e9f0c163ed12db0a7f43a489e71acd1f876.jpg)  
Fig. 16: Average Total Time (Fit + Predict) in seconds vs. Average AUC-ROC in one-class setting.

![](images/5047b67612054a6ab8f9a3f671fed1013d8c2083c0fb7c9d509a431761a09317.jpg)  
Fig. 17: Average Total Time (Fit + Predict) in seconds vs. Average AUC-ROC in the unsupervised setting.

## F Benchmark Dataset Details

<table><tr><td>Dataset</td><td>#Samples</td><td>#Feat.</td><td>#Anom.</td><td>%Anom.</td><td>Category</td></tr><tr><td>ALOI</td><td>49534</td><td>27</td><td>1508</td><td>3.04</td><td>Image</td></tr><tr><td>annthyroid</td><td>7200</td><td>6</td><td>534</td><td>7.42</td><td>Healthcare</td></tr><tr><td>backdoor</td><td>95329</td><td>196</td><td>2329</td><td>2.44</td><td>Network</td></tr><tr><td>breastw</td><td>683</td><td>9</td><td>239</td><td>34.99</td><td>Healthcare</td></tr><tr><td>campaign</td><td>41188</td><td>62</td><td>4640</td><td>11.27</td><td>Finance</td></tr><tr><td>cardio</td><td>1831</td><td>21</td><td>176</td><td>9.61</td><td>Healthcare</td></tr><tr><td>Cardiotocography</td><td>2114</td><td>21</td><td>466</td><td>22.04</td><td>Healthcare</td></tr><tr><td>celeba</td><td>202599</td><td>39</td><td>4547</td><td>2.24</td><td>Image</td></tr><tr><td>census</td><td>299285</td><td>500</td><td>18568</td><td>6.20</td><td>Sociology</td></tr><tr><td>cover</td><td>286048</td><td>10</td><td>2747</td><td>0.96</td><td>Botany</td></tr><tr><td>donors</td><td>619326</td><td>10</td><td>36710</td><td>5.93</td><td>Sociology</td></tr><tr><td>fault</td><td>1941</td><td>27</td><td>673</td><td>34.67</td><td>Physical</td></tr><tr><td>fraud</td><td>284807</td><td>29</td><td>492</td><td>0.17</td><td>Finance</td></tr><tr><td>glass</td><td>214</td><td>7</td><td>9</td><td>4.21</td><td>Forensic</td></tr><tr><td>Hepatitis</td><td>80</td><td>19</td><td>13</td><td>16.25</td><td>Healthcare</td></tr><tr><td>http</td><td>567498</td><td>3</td><td>2211</td><td>0.39</td><td>Web</td></tr><tr><td>InternetAds</td><td>1966</td><td>1555</td><td>368</td><td>18.72</td><td>Image</td></tr><tr><td>Ionosphere</td><td>351</td><td>33</td><td>126</td><td>35.90</td><td>Oryctognosy</td></tr><tr><td>landsat</td><td>6435</td><td>36</td><td>1333</td><td>20.71</td><td>Astronautics</td></tr><tr><td>letter</td><td>1600</td><td>32</td><td>100</td><td>6.25</td><td>Image</td></tr><tr><td>Lymphography</td><td>148</td><td>18</td><td>6</td><td>4.05</td><td>Healthcare</td></tr><tr><td>magic.gamma</td><td>19020</td><td>10</td><td>6688</td><td>35.16</td><td>Physical</td></tr><tr><td>mammography</td><td>11183</td><td>6</td><td>260</td><td>2.32</td><td>Healthcare</td></tr><tr><td>mnist</td><td>7603</td><td>100</td><td>700</td><td>9.21</td><td>Image</td></tr><tr><td>musk</td><td>3062</td><td>166</td><td>97</td><td>3.17</td><td>Chemistry</td></tr><tr><td>optdigits</td><td>5216</td><td>64</td><td>150</td><td>2.88</td><td>Image</td></tr><tr><td>PageBlocks</td><td>5393</td><td>10</td><td>510</td><td>9.46</td><td>Document</td></tr><tr><td>pendigits</td><td>6870</td><td>16</td><td>156</td><td>2.27</td><td>Image</td></tr><tr><td>Pima</td><td>768</td><td>8</td><td>268</td><td>34.90</td><td>Healthcare</td></tr><tr><td>satellite</td><td>6435</td><td>36</td><td>2036</td><td>31.64</td><td>Astronautics</td></tr><tr><td>satimage-2</td><td>5803</td><td>36</td><td>71</td><td>1.22</td><td>Astronautics</td></tr><tr><td>shuttle</td><td>49097</td><td>9</td><td>3511</td><td>7.15</td><td>Astronautics</td></tr><tr><td>skin</td><td>245057</td><td>3</td><td>50859</td><td>20.75</td><td>Image</td></tr><tr><td>smtp</td><td>95156</td><td>3</td><td>30</td><td>0.03</td><td>Web</td></tr><tr><td>SpamBase</td><td>4207</td><td>57</td><td>1679</td><td>39.91</td><td>Document</td></tr><tr><td>speech</td><td>3686</td><td>400</td><td>61</td><td>1.65</td><td>Linguistics</td></tr><tr><td>Stamps</td><td>340</td><td>9</td><td>31</td><td>9.12</td><td>Document</td></tr><tr><td>thyroid</td><td>3772</td><td>6</td><td>93</td><td>2.47</td><td>Healthcare</td></tr><tr><td>vertebral</td><td>240</td><td>6</td><td>30</td><td>12.50</td><td>Biology</td></tr><tr><td>vowels</td><td>1456</td><td>12</td><td>50</td><td>3.43</td><td>Linguistics</td></tr><tr><td>Waveform</td><td>3443</td><td>21</td><td>100</td><td>2.90</td><td>Physics</td></tr><tr><td>WBC</td><td>223</td><td>9</td><td>10</td><td>4.48</td><td>Healthcare</td></tr><tr><td>WDBC</td><td>367</td><td>30</td><td>10</td><td>2.72</td><td>Healthcare</td></tr><tr><td>Wilt</td><td>4819</td><td>5</td><td>257</td><td>5.33</td><td>Botany</td></tr><tr><td>wine</td><td>129</td><td>13</td><td>10</td><td>7.75</td><td>Chemistry</td></tr><tr><td>WPBC</td><td>198</td><td>33</td><td>47</td><td>23.74</td><td>Healthcare</td></tr><tr><td>yeast</td><td>1484</td><td>8</td><td>507</td><td>34.16</td><td>Biology</td></tr></table>

Table 4: Characteristics of classical tabular datasets from ADBench (Part 1).

Table 5: Characteristics of classical tabular datasets from ADBench (Part 2).

<table><tr><td>Dataset</td><td>#Samples</td><td>#Feat.</td><td>#Anom.</td><td>%Anom.</td><td>Category</td></tr><tr><td>CIFAR10</td><td>5263</td><td>512</td><td>263</td><td>5.00</td><td>Image</td></tr><tr><td>FashionMNIST</td><td>6315</td><td>512</td><td>315</td><td>5.00</td><td>Image</td></tr><tr><td>MNIST-C</td><td>10000</td><td>512</td><td>500</td><td>5.00</td><td>Image</td></tr><tr><td>MVTec-AD</td><td>5354</td><td>512</td><td>1258</td><td>23.50</td><td>Image</td></tr><tr><td>SVHN</td><td>5208</td><td>512</td><td>260</td><td>5.00</td><td>Image</td></tr><tr><td>Agnews</td><td>10000</td><td>768</td><td>500</td><td>5.00</td><td>NLP</td></tr><tr><td>Amazon</td><td>10000</td><td>768</td><td>500</td><td>5.00</td><td>NLP</td></tr><tr><td>Imdb</td><td>10000</td><td>768</td><td>500</td><td>5.00</td><td>NLP</td></tr><tr><td>Yelp</td><td>10000</td><td>768</td><td>500</td><td>5.00</td><td>NLP</td></tr><tr><td>20newsgroups</td><td>11905</td><td>768</td><td>591</td><td>4.96</td><td>NLP</td></tr></table>

Table 6: Characteristics of embedding-based datasets (image and text) from ADBench.