---
title: "2024-Zhang-UP2ME-Univariate-Pretraining-Multivariate-Finetuning"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2024-Zhang-UP2ME-Univariate-Pretraining-Multivariate-Finetuning.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# UP2ME: Univariate Pre-training to Multivariate Fine-tuning as a General-purpose Framework for Multivariate Time Series Analysis

Yunhao Zhang <sup>1</sup> Minghao Liu <sup>1</sup> Shengyang Zhou <sup>1</sup> Junchi Yan <sup>1</sup>

## Abstract

Despite the success of self-supervised pre-training in texts and images, applying it to multivariate time series (MTS) falls behind tailored methods for tasks like forecasting, imputation and anomaly detection. We propose a general-purpose framework, named UP2ME (Univariate Pre-training to Multivariate Fine-tuning). It conducts taskagnostic pre-training when downstream tasks are unspecified. Once the task and setting (e.g. forecasting length) are determined, it gives sensible solutions with frozen pre-trained parameters, which has not been achieved before. UP2ME is further refined by fine-tuning. A univariate-tomultivariate paradigm is devised to address the heterogeneity of temporal and cross-channel dependencies. In univariate pre-training, univariate instances with diverse lengths are generated for Masked AutoEncoder (MAE) pre-training, discarding cross-channel dependency. The pretrained model handles downstream tasks by formulating them into specific mask-reconstruction problems. In multivariate fine-tuning, it constructs a dependency graph among channels using the pre-trained encoder to enhance cross-channel dependency capture. Experiments on eight realworld datasets show its SOTA performance in forecasting and imputation, approaching taskspecific performance in anomaly detection. Our code is available at https://github.com/ Thinklab-SJTU/UP2ME.

![](images/61b50cae6ff38206a84be40ff4c0078cd8469a08f213d418625ae2f9708997c4.jpg)  
Figure 1: UP2ME Workflow: Given the dataset, UP2ME performs task-agnostic univariate pre-training. The resulting pre-trained model can execute immediate forecasting, imputation and anomaly detection across various settings without parameter modifications. Once the downstream task and its setting are determined, multivariate fine-tuning tailors UP2ME to the specific task for more accurate solutions.

## 1. Introduction

Recently, deep learning for multivariate time series (MTS) analysis has developed rapidly and has been applied to many tasks, such as forecasting, imputation and anomaly detection. Among these methods, task-specific ones tailored to tasks’ characteristics constitute the most significant proportion. For example, models have been developed based on trend-season decomposition for forecasting (Wu et al., 2021), conditional diffusion for imputation (Tashiro et al., 2021) and association discrepancy for anomaly detection (Xu et al., 2022). Despite the effectiveness, selecting proper task-specific methods for different tasks can be exhausting. Even within the same task, when the setting (e.g. the forecasting length) changes, the model often needs to be retrained (Bi et al., 2023).

Until recently, a few MTS backbones emerged towards the goal of general-purpose analysis (Wu et al., 2023). While the same main architecture (except the output layer) is shared within tasks, the parameters need to be trained from scratch for each task and its corresponding setting.

Self-supervised pre-training, which pre-trains a model on downstream agnostic tasks and then fine-tunes it for specific usages, is a promising way to achieve multi-task models. Following the success in natural language processing (NLP) (Devlin et al., 2019; Brown et al., 2020) and computer vision (CV) (Chen et al., 2020; He et al., 2022), pre-training methods have also been proposed for MTS, and mainly fall into contrastive learning and mask-reconstruction modeling. The former (Eldele et al., 2021; Yue et al., 2022) learns representation by discriminating pre-defined positive and negative pairs. The latter (Zerveas et al., 2021; Dong et al., 2023) masks a proportion of the data and uses the remaining to reconstruct masked parts. Different from NLP and CV, most previous pre-training methods for MTS can not rival carefully designed task-specific methods. Moreover, they only serve as model initializers and can not perform downstream tasks without parameter or architecture modification. Note that instead of pre-training on MTS data, a series of very recent works adapt pre-trained large language models (LLMs) to MTS tasks (Nate Gruver & Wilson, 2023; Zhou et al., 2023), which goes beyond the scope of this work.

To fill the gap, we propose a unified framework for MTS analysis, named UP2ME (Univariate Pre-training to Multivariate Fine-tuning). As shown in Figure 1, when data is available but the downstream tasks and settings are undetermined, UP2ME performs task-agnostic pre-training. Without any parameter modification, the pre-trained model provides initial reasonable solutions to forecasting, imputation and anomaly detection in immediate reaction (IR) mode. Once the downstream tasks and settings are determined, UP2ME further adapts to the task and provides more accurate solutions in fine-tuning (FT) mode.

Temporal dependency captures relations over time, while cross-channel dependency captures relations between data with distinct physical meanings. The latter remains relatively stable due to underlying physical dynamics (Kipf et al., 2018). Inspired by the heterogeneity, we develop a univariate to multivariate paradigm. UP2ME omits crosschannel dependency during univariate pre-training, prioritizing temporal dependency. Channel dependency is subsequently incorporated during multivariate fine-tuning. Specifically, UP2ME uses variable window length and channel decoupling (see details in Sec. 2.1.1) to generate univariate instances with diverse lengths for MAE pre-training (He et al., 2022). Formulated as specific mask-reconstruction tasks, the pre-trained model can directly execute forecasting, imputation and anomaly detection without parameter or architecture modification. Freezing the pre-trained encoder and decoder during fine-tuning, UP2ME introduces trainable Temporal-Channel (TC) layers to capture crosschannel dependency and further refine temporal dependency. TC layers require a dependency graph representing relationships among channels, and this graph is constructed using the pre-trained frozen encoder. The contributions are:

1) Inspired by the heterogeneity of temporal and crosschannel dependency, we propose a general-purpose framework for MTS named UP2ME, where univariate pre-training concentrates on temporal dependency and cross-channel dependency is incorporated in multivariate fine-tuning.

2) In univariate pre-training, variable window length and channel decoupling are used to generate instances for MAE pre-training. The pre-trained model handles multiple tasks by formulating them into specific mask-reconstruction problems. In multivariate fine-tuning, UP2ME refines temporal dependency and constructs a graph among channels via the pre-trained encoder to capture cross-channel dependency.

3) We evaluate UP2ME on eight real-world datasets, addressing three downstream tasks: forecasting, imputation and anomaly detection. Using the original Transformer and Graph Transformer without inductive-biased architectures, pre-trained UP2ME(IR) with frozen parameters is comparable with previous state-of-the-art (SOTA) methods on several datasets. The fine-tuned UP2ME(FT) surpasses all previous task-specific, general-purpose and pre-training methods in forecasting and imputation, approaching taskspecific performance in anomaly detection.

## 2. Methodology

As the overview in Figure 2 shows, we are given a multivariate time series dataset $\mathbf { X } \in \mathbb { R } ^ { T \times C }$ , where $T > 0$ is the number of timestamps and $C > 1$ is the number of channels. In Section 2.1, UP2ME is pre-trained on the given dataset in the univariate setting to capture temporal dependency. The pre-trained model can provide initial solutions in IR mode. In Section 2.2, UP2ME is fine-tuned in the multivariate setting to capture cross-channel dependency and refine temporal dependency for more accurate solutions.

## 2.1. Univariate Pre-training

For pre-training, we specifically use MAE (He et al., 2022), which has proven effective for images. Compared with previous mask-reconstruction methods for time series, we propose two techniques for instance generation: variable window length and channel decoupling.

## 2.1.1. INSTANCE GENERATION

Variable Window Length. Images are often cropped to a fixed size in CV (e.g. 224 × 224 for Imagenet), while for time series, it is unknown during pre-training and should be determined by the setting of downstream tasks (e.g. past and future window length for forecasting). To meet the uncertain requirements for window length, we make it variable during pre-training. Specifically, for each training step, we first randomly sample a window length L then generate a batch

![](images/6b1ed04c85c0f4f2436eb4089675f1a30423c2fcb1e4105604e0b93a89f0028d.jpg)  
Figure 2: Overview of UP2ME framework. Left: Univariate Pre-training. Univariate instances are generated using variable window length and channel decoupling in Sec. 2.1.1. Generated instances are fed into the encoder and decoder for MAE pre-training in Sec. 2.1.2. Formulating downstream tasks as specific mask-reconstruction problems, UP2ME can give sensible solutions without parameter modification in Sec. 2.1.3 (right part without TC layers). Right: Multivariate Fine-tuning (forecasting in this example). The pre-trained frozen encoder encodes a multivariate series into latent tokens. The tokens are used to construct a dependency graph among channels in Sec. 2.2.1. Learnable Temporal-Channel (TC) layers which take constructed graph as input, are inserted before the frozen decoder for fine-tuning in Sec. 2.2.2.

of instances with this length:

$$
n \sim \{N _ {m i n}, \ldots , N _ {m a x} \}, L = n P\tag{1}
$$

where P is the patch size to divide time series (Nie et al., 2023; Zhang & Yan, 2023), $N _ { m i n } , N _ { m a x }$ are hyperparameters for minimal/maximum patch number.

Channel Decoupling. To generate an instance of length L, previous works sample a timestamp t and get multivariate sub-series $\mathbf { X } _ { t + 1 : t + L } \ \in \ \mathbb { R } ^ { L \times C }$ as an instance for model input. With channel decoupling, we independently sample the timestamp $t \sim \{ 0 , \ldots , T - L \}$ and channel index $c \sim$ $\{ 1 , \ldots , C \}$ . The univariate sub-series with its channel index $\left( \mathbf { X } _ { t + 1 : t + L , c } , c \right)$ will be viewed as an instance.

Note that channel decoupling is different from channel independence (Nie et al., 2023). Channel independence is a technique to process multivariate sub-series: $\mathbf { X } _ { t + 1 : t + L }$ is split into $C$ univariate series and input to the model together. Though channels are processed independently, their co-occurrence reflects cross-channel dependency to some extent. With channel decoupling, we completely discard cross-channel dependency and only focus on temporal dependency during pre-training.

Another advantage of channel decoupling is its efficiency for high-dimensional data. For dataset with large $C ,$ , we can pack $B ( B < < C )$ decoupled univariate series into a mini-batch instead of processing all channels at once. Experimental evaluation of pre-training overhead with and without channel decoupling is shown in Figure 5 of Appendix C.

## 2.1.2. MASKED AUTOENCODER PRE-TRAINING

With the above two instance generation techniques, the pretraining process is similar to MAE for image (He et al., 2022). For convinence, we use $( \mathbf { x } ^ { ( p t ) } , c ) , \mathbf { x } ^ { ( p t ) } \in \mathbb { R } ^ { L } , c \in$ $\{ 1 , \ldots , C \}$ to represent a generated instance. The univariate series $\mathbf { \bar { x } } ^ { ( p t ) }$ is first split into non-overlapping patches of length $P \colon \ \{ \mathbf { x } _ { 1 } ^ { ( p a t c h ) } , \cdot \cdot \cdot , \mathbf { x } _ { N } ^ { ( p a t c h ) } \}$ , where $\mathbf { x } _ { i } ^ { ( p a t c h ) } \in$ $\mathbb { R } ^ { P } , \bar { N } = L / P$ . Then each patch is embedded into a token with $d _ { m o d e l }$ dimensions through linear projection, added with learnable positional and channel embeddings:

$$
\mathbf {h} _ {i} ^ {(p a t c h)} = \mathbf {W} ^ {(e m b)} \mathbf {x} _ {i} ^ {(p a t c h)} + \mathbf {p} _ {i} ^ {(p o s)} + \mathbf {v} _ {c} ^ {(c h)}\tag{2}
$$

where $\mathbf { W } ^ { ( e m b ) } \ \in \ \mathbb { R } ^ { d _ { m o d e l } \times P }$ is the projection matrix, $\mathbf { p } _ { i } ^ { ( p o s ) } , \mathbf { v } _ { c } ^ { ( c h ) } \in \mathbb { R } ^ { d _ { m o d e l } }$ are positional embedding for index i and channel embedding for channel $c .$ We randomly sample a subset of patches with ratio α to mask, here we use $\mathcal { M }$ to represent indices of masked patches and U for unmasked patches. Unmasked patches are input to an encoder to capture temporal dependency:

$$
\mathbf {h} _ {i} ^ {(e n c)} = \operatorname{Encoder} (\bigcup_ {j \in \mathcal {U}} \mathbf {h} _ {j} ^ {(p a t c h)}) _ {i}, \forall i \in \mathcal {U}\tag{3}
$$

These encoded unmasked patches, together with learnable tokens indicating masked patches, are input to a decoder for masked patch reconstruction:

$$
\begin{array}{l} \mathbf {h} _ {i} ^ {(d e c - i n)} = \left\{ \begin{array}{l l} \mathbf {u} ^ {(m a s k)} + \mathbf {p} _ {i} ^ {(p o s)} + \mathbf {v} _ {c} ^ {(c h)} & i \in \mathcal {M} \\ \mathbf {W} ^ {(p r o j)} \mathbf {h} _ {i} ^ {(e n c)} & i \in \mathcal {U} \end{array} \right. \\ \mathbf {h} _ {i} ^ {(d e c - o u t)} = \text {Decoder} \left([ \mathbf {h} _ {1} ^ {(d e c - i n)}, \ldots , \mathbf {h} _ {N} ^ {(d e c - i n)} ]\right) _ {i} \\ \mathbf {x} _ {i} ^ {(r e c)} = \mathbf {W} ^ {(r e c)} \mathbf {h} _ {i} ^ {(d e c - o u t)}, \forall i \in \mathcal {M} \end{array}\tag{4}
$$

where $\mathbf { u } ^ { ( m a s k ) } \in \mathbb { R } ^ { d }$ <sup>model</sup> denotes the presence of a masked patch, $\mathbf { W } ^ { ( p r o j ) } ~ \in ~ \mathbb { R } ^ { d _ { m o d e l } \times d _ { m o d e l } }$ projects latent tokens from encoder space to decoder space, [·, ·] denotes concatenation, $\mathbf { W } ^ { ( \hat { r } e c ) } \in \mathbb { R } ^ { P \times d _ { m o d e l } }$ projects latent tokens to original patches. The encoder/decoder are both composed of standard Transformer layers. The normalization technique, RevIN (Kim et al., 2022), is used to reduce distribution shift.

Mean squared error (MSE) between the reconstructed and ground truth masked patches is used as pre-training loss:

$$
\mathcal {L} = \frac {1}{P | \mathcal {M} |} \sum_ {i \in \mathcal {M}} \| \mathbf {x} _ {i} ^ {(p a t c h)} - \mathbf {x} _ {i} ^ {(r e c)} \| _ {2} ^ {2}\tag{5}
$$

## 2.1.3. IMMEDIATE REACTION MODE

Different from the original MAE for images where the decoder is removed after pre-training, UP2ME preserves both the pre-trained encoder and decoder for potential downstream tasks. Formulating different downstream tasks as specific mask-reconstruction problems, UP2ME can perform immediate forecasting, anomaly detection and imputation with frozen parameters. As the immediate reaction (IR)<sup>1</sup> mode only utilizes temporal dependency and acts similarly on each channel, we only describe the computation process for a single channel in this section.

Forecasting. To forecast future time series ${ \bf x } ^ { ( f u t u r e ) } ~ \in { }$ $\mathbb { R } ^ { L _ { f } }$ based on its past $\mathbf { x } ^ { ( p a s t ) } \in \mathbb { R } ^ { L _ { p } }$ , we view past series as unmasked patches and future series as masked patches<sup>2</sup>:

$$
\begin{array}{l} \mathcal {M} ^ {\text {forecast}} = \{i | \frac {L _ {p}}{P} <   i \leq \frac {L _ {p} + L _ {f}}{P} \} \\ \mathcal {U} ^ {\text {forecast}} = \{i | 1 \leq i \leq \frac {L _ {p}}{P} \} \end{array}\tag{6}
$$

Imputation. Point-wise missing can be easily handled by traditional interpolation methods. Moreover, missing patterns in real world are often structured and appear consecutively (Tashiro et al., 2021). We focus on this more challenging scenario where continuous blocks of data are missing. Given observed data $\mathbf { x } ^ { ( i m p ) } \in \mathbb { R } ^ { L _ { i m p } }$ and a mask for missing positions m $\in [ 0 , 1 ] ^ { L _ { i m p } } ( m _ { i } = 1$ if i-th value is missing), we patch m into $\left\{ \mathbf { m } _ { 1 } ^ { \left( p a t c h \right) } , \ldots , \mathbf { m } _ { L _ { i m p } / P } ^ { \left( p a t c h \right) } \right\}$ using the same patching process for $\mathbf { x } ^ { ( i m p ) }$ . Patches containing at least one missing point are viewed as masked patches and fully-observed patches are viewed as unmasked:

$$
\begin{array}{c} \mathcal {M} ^ {i m p u t a t e} = \{i   \Big | \| \mathbf {m} _ {i} ^ {(p a t c h)} \| _ {0} \geq 1 \} \\ \mathcal {U} ^ {i m p u t a t e} = \{i   \Big | \| \mathbf {m} _ {i} ^ {(p a t c h)} \| _ {0} = 0 \} \end{array}\tag{7}
$$

Anomaly Detection. Due to the rarity and irregularity of anomalies, it is much more difficult to reconstruct them from other parts of the series than normal points. Based on this, to detect anomalies from observed series $\mathbf { x } ^ { ( d e t ) } \in \mathbb { R } ^ { L _ { d e t } }$ , we iteratively mask each patch and use other unmasked patches to reconstruct it, MSE between reconstructed series and original series is used as the anomaly score:

$$
\begin{array}{l} \text {for i = 1,\ldots, \frac {L_{det}}{P} :} \\ \mathcal {M} _ {i} ^ {d e t e c t} = \{i \} \quad \mathcal {U} _ {i} ^ {d e t e c t} = \{1, \ldots , \frac {L _ {d e t}}{P} \} \backslash \{i \} \\ \widetilde {\mathbf {x}} ^ {(d e t)} = \left[ \mathbf {x} _ {1} ^ {(r e c)}, \ldots , \mathbf {x} _ {L _ {d e t} / P} ^ {(r e c)} \right] \\ \text {AnomalyScore} (t) = | x _ {t} ^ {(d e t)} - \widetilde {x} _ {t} ^ {(d e t)} | ^ {2}, 1 \leq t \leq L _ {d e t} \end{array}\tag{8}
$$

In each iteration, we use $\mathcal { U } _ { i } ^ { d e t e c t }$ as unmasked patches to reconstruct $\mathcal { M } _ { i } ^ { d e t e c t }$ , resulting in $\mathbf { x } _ { i } ^ { ( r e c ) } \in \mathbb { R } ^ { P }$ . These reconstructed patches are concatenated into $\widetilde { \mathbf { x } } ^ { ( d e t ) } \in \mathbb { R } ^ { L _ { d e t } }$ to compute anomaly score. For multivariate data, we compute the anomaly score for each channel and use the average across channels as the final anomaly score.

Despite distributions and ratios of mask in three downstream tasks being different from those in pre-training, experiments in Section 3 show that our IR mode generalizes well and is on par with some task-specific methods.

## 2.2. Multivariate Fine-tuning

In fine-tuning, the downstream task and the corresponding setting are given. UP2ME takes a multivariate instance $\mathbf { x } ^ { ( \overline { { f } } t ) } \in \overline { { \mathbb { R } } } ^ { L _ { f t } \times C }$ as input and performs forecasting/detection/imputation. Specifically, we freeze parameters of the pre-trained encoder and decoder while incorporating learnable Temporal-Channel (TC) layers between them. The main function of the TC layer is to capture dependency among channels and, incidentally, adjust temporal dependency to reduce the gap between pre-training and downstream tasks.

## 2.2.1. SPARSE DEPENDENCY GRAPH CONSTRUCTION

A straightforward method for capturing cross-channel dependency is to employ self-attention across $C$ channels, which corresponds to constructing a fully connected dependency graph. However, the $O ( C ^ { 2 } )$ complexity limits its applicability to potentially high-dimensional datasets (Zhang & Yan, 2023). Hence, it is necessary to build a sparse graph that preserves most dependency with fewer edges to guide cross-channel dependency capturing.

Since the encoder has acquired meaningful representations through pre-training, we leverage it for sparse graph construction. Each channel of $\mathbf { x } ^ { ( f t ) }$ is first patched and then independently input to the encoder to get latent tokens, denoted as $\{ \bigcup _ { i \in \mathcal { U } _ { c } } \mathbf { h } _ { i , c } ^ { ( e n c ) } \} _ { c = 1 } ^ { C }$ , where $\mathcal { U } _ { c }$ indicates unmasked patches in channel c, $\mathbf { h } _ { i , c } ^ { ( e n c ) }$ indicates the i-th encoded patch in channel $c .$ Then we use these latent tokens to construct a dependency graph among channels:

$$
\mathbf {h} _ {c} ^ {(c h)} = \text { Max\_Pooling } (\bigcup_ {i \in \mathcal {U} _ {c}} \mathbf {h} _ {i, c} ^ {(e n c)}), \forall c \in \{1, \dots , C \}
$$

$$
\begin{array}{c} A _ {c, c ^ {\prime}} = \frac {\langle \mathbf {h} _ {c} ^ {(c h)} , \mathbf {h} _ {c ^ {\prime}} ^ {(c h)} \rangle}{\| \mathbf {h} _ {c} ^ {(c h)} \| _ {2} \| \mathbf {h} _ {c ^ {\prime}} ^ {(c h)} \| _ {2}}, \forall c, c ^ {\prime} \in \{1, \ldots , C \} \\ \mathbf {E} = \operatorname{topK} (\mathbf {A}, r C) \wedge \operatorname{KNN} (\mathbf {A}, r) \end{array}\tag{9}
$$

We use max pooling to get a token $\mathbf { h } _ { c } ^ { ( c h ) }$ representing channel c. The correlation matrix A is defined as the pairwise cosine similarity of these tokens. The intersection of $r C$ largest elements and r-nearest neighbors of each channel is used as the final graph E, with r as a constant hyperparameter.

Note that it is common to measure dependency between sentences or words using cosine similarity of latent embeddings from pre-trained models (Reimers & Gurevych, 2019; Ren et al., 2023). For MTS, Shao et al. (2022) also employs the cosine similarity of latent tokens from a separate pre-trained model to guide spatial-temporal graph neural network learning. Our graph construction process differs from previous works for MTS which use channel independence (Nie et al., 2023), low-rank approximation (Zhang & Yan, 2023), statistics or learning methods (Wu et al., 2020). Using the pre-trained encoder, we construct a non-linear and sparse graph with at most $r C$ edges. The additional computational cost incurred by the construction is minimal, as there is no learning component.

## 2.2.2. TEMPORAL-CHANNEL LAYER

Concatenating encoded patches with tokens indicating unmasked patches (Eq. 4), we get ${ \bf H } ^ { ( T C - i n ) } \in $ $\mathbb { R } ^ { \bar { N } ^ { ( d e c ) } \times C \times d _ { m o d e l } }$ , where $N ^ { ( d e c ) }$ is the number of patches in each channel for decoding. Before input to the decoder, $\mathbf { H } ^ { ( T C - i n ) }$ and the constructed dependency graph E pass through $K \geq 1$ Temporal-Channel (TC) layers to capture cross-channel dependency and adjust temporal dependency. With few inductive biases, our TC layer contains a standard Transformer layer for temporal dependency and a standard Graph Transformer layer (Dwivedi & Bresson, 2021) for cross-channel dependency :

$$
\begin{array}{l} \mathbf {H} ^ {(c h, 0)} = \mathbf {H} ^ {(T C - i n)} \\ \text { for   } k = 1, \ldots , K: \\ \quad \mathbf {H} _ {:, c} ^ {(t i m e, k)} = \text { Transformer } (\mathbf {H} _ {:, c} ^ {(c h, k - 1)}), \forall c \\ \quad \mathbf {H} _ {i,:} ^ {(c h, k)} = \text { Graph\_Transformer } (\mathbf {H} _ {i,:} ^ {(t i m e, k)}, \mathbf {E}), \forall i \\ \mathbf {H} ^ {(d e c - i n)} = \mathbf {H} ^ {(T C - o u t)} = \mathbf {H} ^ {(c h, K)} \end{array}\tag{10}
$$

where $\mathbf { H } _ { : , c } ^ { ( c h , k - 1 ) } \in \mathbb { R } ^ { N ^ { ( d e c ) } \times d _ { m o d e l } }$ denotes tokens of all steps in channel c and $\mathbf { H } _ { i , : } ^ { ( t i m e , k ) } \in \mathbb { R } ^ { C \times d _ { m o d e l } }$ denotes all channels at step i. Passing through several learnable TC layers, the final ${ \bf H } ^ { ( d e c - i n ) } \in \mathbb { R } ^ { N ^ { ( \bar { d e c } ) } \times C \times d _ { m o d e l } }$ is input to the frozen decoder to get solutions for downstream tasks. A Graph Transformer layer functionally equals a standard Transformer layer using the graph structure as the attention weight mask, but is more efficient on sparse graphs (Dwivedi & Bresson, 2021). The overall computation complexity of a TC layer is ${ \cal O } ( C N ^ { 2 } ) + { \cal O } ( r C N ) = { \cal O } ( C N ^ { 2 } )$ , which is linear w.r.t C thanks to the constructed sparse graph, making UP2ME scalable to high dimensional data.

## 3. Experiments

We conduct experiments on eight real-world datasets: 1)ETTm1, 2)Weather, 3)Electricity, 4)Traffic, 5)SMD, 6)PSM, 7)SWaT, 8)GECCO. On each dataset, we perform three different downstream tasks: forecasting, imputation and anomaly detection<sup>3</sup>. We vary the specific settings for tasks, such as prediction length for forecasting and missing ratio for imputation, etc. We pre-train one UP2ME for each dataset as the base model and fine-tune it to adapt to different downstream tasks and settings. Results of two UP2ME modes are reported: 1)UP2ME(IR): immediate reaction mode which directly provides initial solutions with the pre-trained model; 2)UP2ME(FT): fine-tuning mode which adapts to specific downstream tasks and settings. For each task, three categories of methods are compared: 1) task-specific methods; 2) general-purpose methods; 3) pretraining methods. Detailed setup is shown in Appendix A.

## 3.1. Main Results

Forecasting. We select PatchTST (Nie et al., 2023), DLinear (Zeng et al., 2023), Crossformer (Zhang & Yan, 2023), FEDformer (Zhou et al., 2022) as task-specific methods; TimesNet (Wu et al., 2023) as the general-purpose method;

TS2Vec (Yue et al., 2022) and SimMTM (Dong et al., 2023) as pre-training methods. Each method predicts future series with different lengths $( L _ { f } )$ . Evaluation metrics are Mean Square Error (mSE) and Mean Absolute Error (mAE) <sup>4</sup>.

The results are shown in Table 1. Without any adjustment to model parameters, UP2ME(IR) is comparable with previous SOTA methods on ETTm1, Electricity, Traffic and GECCO datasets. This indicates that our instance generation techniques enable the model to generalize to downstream tasks where the mask distribution and ratio are different from pretraining. After fine-tuning, UP2ME makes more accurate forecasting and outperforms previous SOTAs on all datasets. Note that our UP2ME only uses standard Transformer and Graph Transformer layers, without inductive biased architecture designs e.g. flattened projection (PatchTST, TimesNet, SimMTM), trend-season decomposition (DLinear, FEDformer), hierarchical encoder-decoder (Crossformer) or frequency domain enhancement (FEDformer, TimesNet).

Imputation. We select SAITS (Du et al., 2023), GRIN (Cini et al., 2022), LI (Linear Interpolation) and SI (Spline Interpolation) as task-specific methods; generalpurpose and pre-training methods are same as those for forecasting. We evaluate performances on different missing ratio levels and use mSE and mAE as evaluation metrics.

Table 2 shows that UP2ME(IR) outperforms most previous baselines on Electricity, Traffic, SMD and GECCO and also achieves comparable results on ETTm1 and SWaT. It is worth mentioning that the architecture and parameters are the same as those for forecasting, showing UP2ME’s capability to handle multiple tasks. Equipped with cross-channel dependency after fine-tuning, UP2ME(FT) outperforms all other methods over a large margin on 7 out of 8 datasets.

Anomaly Detection. We select DCdetector (Yang et al., 2023), AnomalyTrans (Xu et al., 2022), iForest (Liu et al., 2012), OCSVM (Scholkopf et al.¨ , 2001) as task-specific methods and use the same general and pre-training methods as forecasting and imputation. Following Yang et al. (2023); Xu et al. (2022), we use the train and validation set to select a threshold and label anomalies with it for F1-score evaluation. Moreover, to mitigate the impact of threshold selection for a more comprehensive comparison, we also threshold at every possible point to evaluate the Average Precision (AP) (Manning, 2009). The widely-used segment adjustment strategy (Shen et al., 2020; Xu et al., 2022; Yang et al., 2023) is utilized for F1-score and AP evaluation.

Table 3 shows that two task-specific SOTA methods, DCdetector and AnomalyTrans, perform better on the first three datasets, but our UP2ME still outperforms traditional taskspecific, general-purpose and pre-training methods and approaches task-specific methods. While on the more challenging GECCO dataset with various types of anomalies (Yang et al., 2023), UP2ME outperforms task-specific methods over a large margin, indicating the superiority of our univariate pre-training to multivariate fine-tuning paradigm.

## 3.2. Model Analysis

Ablations of Pre-training. As Figure 3(a) shows, training from scratch is less effective than pre-training and then fine-tuning, though the network architectures are the same. Without variable window length, the IR mode can not handle varying prediction lengths, thus performs poorly. Channel decoupling slightly improves both modes and contributes more to fine-tuning. Also, channel decoupling is indispensable for pre-training on high-dimensional datasets (e.g. Traffic (C = 862)); otherwise, the computational overhead would be unaffordable (see experiments in Appendix C)

Mask Ratio α in Pre-training. Figure 3(b) shows the influence of mask ratio in pre-training. A lower mask ratio (≤ 30%) would result in decreased performance of IR mode. While an excessively high mask ratio (≥ 70%) has negative impacts on both IR and FT modes. The optimal ratios are 40% ∼ 60%, within which both two modes perform well and outperform training from scratch (0.369). The default mask ratio used in our main experiments is 50%.

Graph Construction in Fine-tuning. Figure 3(c) shows that channel independence without graph structure performs the worst. The graph constructed by the pre-trained encoder outperforms those via random processes, Pearson correlation and Euclidean distance. We failed to evaluate Dynamic Time Wrapping (DTW) due to its quadratic complexity and non-parallelizability. UP2ME approaches the theoretical upper bound, i.e. full connection, with small computational overhead (see memory occupancy in Figure 3(d)). Note that the full connection is unaffordable for high-dimensional datasets (see Figure 6 in Appendix C). Figure 4(a) shows a correlation matrix for graph construction on Weather, where channels #4, #7, #9 and #10 are highly correlated and form a connected community. Actually, they are related to dew point, water vapor and humidity, indicating that our graph construction is reasonable.

Hyper-parameter r in Fine-tuning. Figure 3(d) shows that increasing hyper-parameter r in fine-tuning improves performance, but also increases memory occupancy. Exceeding a certain threshold, the improvement becomes marginal, but memory occupancy rises rapidly. This indicates that UP2ME can preserve the most important correlations with a relatively sparse graph. To strike a balance between performance and efficiency, the default r is set to r = min(10, ⌈0.5C⌉).

Varying Past Window for Forecasting. Zeng et al. (2023)

Table 1: mSE/mAE of forecasting. The prediction length $L _ { f }$ is set to {96, 192, 336, 720} for the first four datasets and {50, 100, 150, 200} for the last four. Results are averaged over 4 different lengths. Bold/underline indicates the best/second. Our methods are marked in gray. OOM: out-of-memory problem. See Table 5 in Appendix B for the full results.

<table><tr><td rowspan="2">Methods</td><td colspan="8">Task-Specific</td><td colspan="2">General</td><td colspan="8">Pre-Training</td></tr><tr><td colspan="2">PatchTST</td><td colspan="2">DLinear</td><td colspan="2">Crossformer</td><td colspan="2">FEDformer</td><td colspan="2">TimesNet</td><td colspan="2">TS2Vec</td><td colspan="2">SimMTM</td><td colspan="2">UP2ME(IR)</td><td colspan="2">UP2ME(FT)</td></tr><tr><td>Metric</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td></tr><tr><td>ETTm1</td><td>0.353</td><td>0.382</td><td>0.358</td><td>0.379</td><td>0.443</td><td>0.461</td><td>0.427</td><td>0.447</td><td>0.393</td><td>0.408</td><td>0.787</td><td>0.651</td><td>0.350</td><td>0.384</td><td>0.360</td><td>0.372</td><td>0.341</td><td>0.374</td></tr><tr><td>Weather</td><td>0.228</td><td>0.264</td><td>0.244</td><td>0.297</td><td>0.239</td><td>0.299</td><td>0.311</td><td>0.365</td><td>0.247</td><td>0.283</td><td>0.261</td><td>0.330</td><td>0.232</td><td>0.270</td><td>0.266</td><td>0.288</td><td>0.221</td><td>0.260</td></tr><tr><td>Electricity</td><td>0.164</td><td>0.255</td><td>0.168</td><td>0.265</td><td>0.205</td><td>0.306</td><td>0.239</td><td>0.349</td><td>0.194</td><td>0.293</td><td>0.377</td><td>0.451</td><td colspan="2">OOM</td><td>0.165</td><td>0.252</td><td>0.155</td><td>0.245</td></tr><tr><td>Traffic</td><td>0.395</td><td>0.265</td><td>0.436</td><td>0.300</td><td>0.528</td><td>0.292</td><td>0.658</td><td>0.413</td><td>0.622</td><td>0.332</td><td>0.973</td><td>0.569</td><td colspan="2">OOM</td><td>0.401</td><td>0.257</td><td>0.390</td><td>0.253</td></tr><tr><td>SMD</td><td>0.893</td><td>0.174</td><td>0.992</td><td>0.199</td><td>0.925</td><td>0.185</td><td>1.020</td><td>0.236</td><td>0.995</td><td>0.188</td><td>1.289</td><td>0.427</td><td>0.894</td><td>0.187</td><td>0.924</td><td>0.201</td><td>0.872</td><td>0.169</td></tr><tr><td>PSM</td><td>0.303</td><td>0.310</td><td>0.314</td><td>0.341</td><td>0.377</td><td>0.326</td><td>0.326</td><td>0.330</td><td>0.301</td><td>0.311</td><td>0.687</td><td>0.580</td><td>0.315</td><td>0.325</td><td>0.602</td><td>0.499</td><td>0.290</td><td>0.300</td></tr><tr><td>SWaT</td><td>0.217</td><td>0.066</td><td>0.354</td><td>0.168</td><td>0.237</td><td>0.110</td><td>0.263</td><td>0.103</td><td>0.226</td><td>0.063</td><td>10.082</td><td>1.559</td><td>0.248</td><td>0.138</td><td>0.292</td><td>0.093</td><td>0.210</td><td>0.062</td></tr><tr><td>GECCO</td><td>1.656</td><td>0.322</td><td>1.703</td><td>0.457</td><td>2.637</td><td>0.657</td><td>1.735</td><td>0.383</td><td>1.655</td><td>0.314</td><td>2.469</td><td>0.771</td><td>1.615</td><td>0.331</td><td>1.476</td><td>0.328</td><td>1.413</td><td>0.299</td></tr></table>

Table 2: mSE/mAE of imputation. Results are averaged over 4 missing ratio settings (0% ∼ 12.5%, 12.5% ∼ 25%, 25% ∼ 37.5%, 37.5% ∼ 50%). See Table 6 in Appendix B for the full results.

<table><tr><td rowspan="2">Methods</td><td colspan="8">Task-Specific</td><td colspan="2">General</td><td colspan="8">Pre-Training</td></tr><tr><td colspan="2">SAITS</td><td colspan="2">GRIN</td><td colspan="2">LI</td><td colspan="2">SI</td><td colspan="2">TimesNet</td><td colspan="2">TS2Vec</td><td colspan="2">SimMTM</td><td colspan="2">UP2ME(IR)</td><td colspan="2">UP2ME(FT)</td></tr><tr><td>Metric</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td></tr><tr><td>ETTm1</td><td>0.201</td><td>0.278</td><td>0.492</td><td>0.496</td><td>0.912</td><td>0.577</td><td>2.046</td><td>1.060</td><td>0.172</td><td>0.266</td><td>0.275</td><td>0.353</td><td>0.328</td><td>0.380</td><td>0.275</td><td>0.318</td><td>0.128</td><td>0.221</td></tr><tr><td>Weather</td><td>0.103</td><td>0.160</td><td>0.232</td><td>0.306</td><td>0.179</td><td>0.198</td><td>1.016</td><td>0.741</td><td>0.113</td><td>0.166</td><td>0.125</td><td>0.201</td><td>0.171</td><td>0.228</td><td>0.150</td><td>0.191</td><td>0.079</td><td>0.108</td></tr><tr><td>Electricity</td><td>0.211</td><td>0.319</td><td>0.313</td><td>0.399</td><td>1.277</td><td>0.860</td><td>1.759</td><td>1.058</td><td>0.140</td><td>0.256</td><td>0.227</td><td>0.324</td><td colspan="2">OOM</td><td>0.107</td><td>0.204</td><td>0.097</td><td>0.193</td></tr><tr><td>Traffic</td><td>0.573</td><td>0.311</td><td>0.509</td><td>0.291</td><td>2.253</td><td>0.994</td><td>2.696</td><td>1.092</td><td>0.508</td><td>0.276</td><td>0.559</td><td>0.299</td><td colspan="2">OOM</td><td>0.338</td><td>0.223</td><td>0.294</td><td>0.197</td></tr><tr><td>SMD</td><td>0.865</td><td>0.207</td><td>1.148</td><td>0.346</td><td>1.289</td><td>0.167</td><td>3.215</td><td>0.870</td><td>0.877</td><td>0.178</td><td>1.217</td><td>0.372</td><td>0.842</td><td>0.155</td><td>0.839</td><td>0.166</td><td>0.756</td><td>0.103</td></tr><tr><td>PSM</td><td>0.601</td><td>0.450</td><td>0.821</td><td>0.486</td><td>0.232</td><td>0.257</td><td>3.026</td><td>1.132</td><td>0.302</td><td>0.330</td><td>1.497</td><td>0.733</td><td>0.225</td><td>0.269</td><td>0.340</td><td>0.334</td><td>0.144</td><td>0.197</td></tr><tr><td>SWaT</td><td>2.929</td><td>0.754</td><td>6.140</td><td>0.872</td><td>0.186</td><td>0.055</td><td>13.579</td><td>1.564</td><td>0.240</td><td>0.102</td><td>6.091</td><td>1.257</td><td>0.155</td><td>0.066</td><td>0.192</td><td>0.064</td><td>0.121</td><td>0.045</td></tr><tr><td>GECCO</td><td>3.828</td><td>1.142</td><td>5.091</td><td>1.216</td><td>1.634</td><td>0.250</td><td>11.720</td><td>2.063</td><td>1.778</td><td>0.412</td><td>6.065</td><td>1.401</td><td>1.515</td><td>0.314</td><td>1.405</td><td>0.299</td><td>1.468</td><td>0.290</td></tr></table>

Table 3: F1-score/AP (in %) of anomaly detection. See Table 7 in Appendix B for the full results.

<table><tr><td rowspan="2">Methods</td><td colspan="8">Task-Specific</td><td colspan="2">General</td><td colspan="8">Pre-Training</td></tr><tr><td colspan="2">DCdetector</td><td colspan="2">AnomalyTrans</td><td colspan="2">iForest</td><td colspan="2">OCSVM</td><td colspan="2">TimesNet</td><td colspan="2">TS2Vec</td><td colspan="2">SimMTM</td><td colspan="2">UP2ME(IR)</td><td colspan="2">UP2ME(FT)</td></tr><tr><td>Metric</td><td>F1</td><td>AP</td><td>F1</td><td>AP</td><td>F1</td><td>AP</td><td>F1</td><td>AP</td><td>F1</td><td>AP</td><td>F1</td><td>AP</td><td>F1</td><td>AP</td><td>F1</td><td>AP</td><td>F1</td><td>AP</td></tr><tr><td>SMD</td><td>84.40</td><td>82.75</td><td>90.98</td><td>93.49</td><td>54.92</td><td>80.65</td><td>67.23</td><td>73.42</td><td>83.09</td><td>90.59</td><td>74.13</td><td>87.79</td><td>83.01</td><td>93.91</td><td>82.69</td><td>93.90</td><td>83.31</td><td>93.58</td></tr><tr><td>PSM</td><td>97.50</td><td>98.73</td><td>97.37</td><td>98.80</td><td>90.82</td><td>96.61</td><td>86.53</td><td>96.86</td><td>90.53</td><td>99.70</td><td>87.44</td><td>96.48</td><td>93.37</td><td>99.73</td><td>96.05</td><td>99.75</td><td>97.16</td><td>99.76</td></tr><tr><td>SWaT</td><td>96.52</td><td>99.57</td><td>95.01</td><td>98.92</td><td>37.36</td><td>91.46</td><td>61.61</td><td>88.55</td><td>90.83</td><td>97.37</td><td>26.20</td><td>82.12</td><td>89.29</td><td>97.38</td><td>92.89</td><td>97.83</td><td>93.85</td><td>98.07</td></tr><tr><td>GECCO</td><td>31.71</td><td>31.87</td><td>34.45</td><td>48.54</td><td>26.37</td><td>38.92</td><td>52.41</td><td>62.08</td><td>46.45</td><td>68.53</td><td>16.77</td><td>37.76</td><td>47.32</td><td>63.30</td><td>55.91</td><td>65.47</td><td>63.39</td><td>65.09</td></tr></table>

![](images/7b50a497e7d8a0dbbf571c9a9f2416d85ed406f3addd85dc966da8ec349e51ff.jpg)  
(a)

![](images/64837b6f1ed2aa56b2a3a1d52f97929528fde6645d93a4951ae05d928111d69a.jpg)  
(b)

![](images/eef7c2bbc5d3a0621fe6dfb533e3de09160b60319662f0b9d7c9b9e68849fb35.jpg)  
(c)

![](images/f83605b5defbb9e857c3f2e7662c754246b1b95d36a5c11c22ae3d21015f9a42.jpg)  
(d)  
Figure 3: Analysis of pre-training and fine-tuning. (a) Forecasting mSE of ablations in pre-training on ETTm1. (b) Forecasting mSE against mask ratios α in pre-training on ETTm1. (c) Imputation mSE of different graph constructions in fine-tuning on Weather. (d) mSE and memory occupancy against r in fine-tuning on Weather with 25% ∼ 37.5% missing.

argues that many methods fail to leverage longer past windows for better forecasting. Figure 4(b) shows that besides TimesNet, performances of other models show an increasing trend while the window length increases from 120 to 720. Further increasing it to 1440, performances of PatchTST,

SimMTM and UP2ME(FT) get worse, while UP2ME(IR) can further utilize the expanded receptive field to improve forecasting. As UP2ME(IR) does not require re-training for different lengths, we can efficiently adjust the past window length to get better performance in practice.

![](images/8d34a71688a6d1b9a1a23367248886c025dd326257ab836fa48a373c25191335.jpg)  
(a)

![](images/a874a1e3dc64afebc9e430f68c55123458d22e2a55910faa982ac135f8e54e1b.jpg)  
(b)

![](images/9f17a5708da470f8c70f68a53f0751aa718ddac5140b06b1ccd45f6f5fd9f531.jpg)  
(c)  
Figure 4: (a) A correlation matrix A utilized for graph construction during imputation fine-tuning on the Weather dataset. (b) Forecasting mSE against varying past window length on ETTm1, the prediction length is set to 192. (c) Forecasting mSE on ETTm2 dataset against varying available data proportions. TimesNet and PatchTST are trained from scratch, SimMTM and UP2ME are pre-trained on ETTm1 and fine-tuned on the available ETTm2 data. 0% for UP2ME stands for IR mode.

Adaption to Limited Data Scenarios Following Dong et al. (2023), we evaluate the performance of UP2ME in limited data scenario on ETTm2 dataset in Figure 4(c). With enough data, PatchTST, SimMTM and UP2ME achieve similar performance. However, in data-limited scenarios (≤ 10%), UP2ME(IR) without fine-tuning achieves the best performance, showing our UP2ME has a certain degree of transferability, which is critical to limited data scenarios.

## 4. Related Works

## 4.1. Task-specific Methods for Time Series

Forecasting. Early works employ RNNs (Flunkert et al., 2017), CNNs (Lea et al., 2017), and GNNs (Wu et al., 2020) as backbones. Later, Transformers were adapted. Li et al. (2019b); Zhou et al. (2021) use sparse attention. Liu et al. (2022) introduces a hierarchical module that captures features at multiple scales. Wu et al. (2021); Zhou et al. (2022); Huang et al. (2023) introduce frequency domain features into Transformers. Nie et al. (2023); Zhang & Yan (2023) divide series into patches and propose channel independence/dependence to model cross-channel dependency. Besides Transformers, recent works also employ linears (Zeng et al., 2023) and MLPs (Ekambaram et al., 2023).

Imputation. Imputation fills the missing values in MTS caused by sensor issues, etc. Early methods train RNNs with supervised learning (Cao et al., 2018; Yoon et al., 2018), followed by works using Transformers (Du et al., 2023). With the development of deep generative models, VAEs (Ramchandran et al., 2021; Fortuin et al., 2020), GANs (Liu et al., 2019; Luo et al., 2019) and Diffusion models (Tashiro et al., 2021) have also been introduced for MTS imputation. Besides temporal dependency, Cini et al. (2022) incorporates GNNs to capture cross-channel dependency.

Anomaly Detection. Anomaly detection aims to identify unusual patterns or outliers caused by irregular events, etc. Early works introduce probabilistic clustering (Tariq et al., 2019) and stochastic process (Su et al., 2019) into RNNs. Zhao et al. (2020); Deng & Hooi (2021) use GNN to capture cross-channel dependency to improve detection. Li et al. (2019a); Zhou et al. (2019); Li et al. (2022) use deep generative models. Yu & Sun (2020) models it as a decision process solved by RL. More recent works introduce prior knowledge into Transformers: Xu et al. (2022) discriminates abnormal points via their local and global association patterns, Yang et al. (2023) utilizes contrastive consistency and performs detection via the difference of two views.

General-purpose Architecture. Wu et al. (2023) proposes such a general-purpose architecture for MTS analysis. It transforms data into a set of 2D tensors based on its multiple periods and utilizes CNNs to extract features. Changing the output layer and training criterion, it can perform multiple tasks with the same main architecture.

Despite the effectiveness of task-specific methods, selecting and switching between them for different tasks is challenging. Although Wu et al. (2023) maintains the main architecture, it is still required to train its parameters from scratch for each task and each setting.

## 4.2. Pre-training Methods for Time Series

Beyond CV and NLP, pre-training methods have also been devised for MTS recently and can be roughly classified into contrastive learning and mask-reconstruction.

Contrastive Learning. It learns representations by discriminating between positive and negative pairs. Methods differ in how to define pairs for MTS. Mohsenvand et al. (2020); Eldele et al. (2021) use augmentations, such as amplitude scale and time shift, to generate positive pairs.Woo et al. (2022) decomposes time series into trend and season components and performs contrastive learning on them respectively. Yang & Hong (2022) utilizes features in time and spectral domains. Zhang et al. (2022) further requires representations in two domains to be consistent. Yue et al. (2022); Franceschi et al. (2019) view overlapped timestamps of different sub-series as positive pairs. Hyvarinen & Morioka (2017); Agrawal et al. (2022) define a pair of consecutive sub-series as a positive pair, and Tonekaboni et al. regard nearby sub-series in the time domain as positive.

Mask-Reconstruction. It learns representations by masking a proportion of the data and reconstructing it via the remaining unmasked parts (Devlin et al., 2019; Brown et al., 2020; He et al., 2022). As for MTS, Zerveas et al. (2021) masks consecutive sub-series in the original space and uses a Transformer with a linear output layer to reconstruct them. Nie et al. (2023) divides time series into patches and masks patches in the latent space. Following MAE in CV (He et al., 2022), decoupled encoder-decoders are used to perform point-wise (Li et al., 2023) and patch-wise (Shao et al., 2022) mask-reconstruction. Dong et al. (2023) reconstructs the original time series from multiple randomly masked series. Instead of reconstruction, Cheng et al. (2023) proposes masked codeword classification and representation regression for learning in latent space.

Besides the above two, there are alternative paradigms (Malhotra et al., 2017; Lyu et al., 2018; Sarkar & Etemad, 2020). Unlike NLP (Radford et al., 2019) and CV (Bai et al., 2023), to our knowledge, existing pre-training methods, cannot solve downstream tasks without parameter modification, and they can hardly rival those carefully designed task-specific methods. Recent efforts involve adapting pre-trained large language models (LLMs) for time series tasks instead of pre-training models with MTS datasets (Nate Gruver & Wilson, 2023; Zhou et al., 2023; Chang et al., 2024), which extends beyond the scope of this work.

## 5. Conclusion, Limitations and Future Works

We have proposed UP2ME as a general-purpose framework for MTS analysis. Technically, it utilizes a univariate pretraining to multivariate fine-tuning paradigm which captures temporal dependency during pre-training and incorporates cross-channel dependency during fine-tuning. Functionally, the pre-trained UP2ME provides initial sensible solutions to forecasting, imputation and anomaly detection without parameter modification, which has not been achieved before. Further accuracy is achieved through fine-tuning.

Due to the different data formats and the feasibility of conducting classification without parameter modification in IR mode, UP2ME currently does not support classification. Unlike NLP foundation models, which are pre-trained on multiple datasets and can execute downstream tasks in zero-shot mode on unseen data, our approach pre-trains one model on a single dataset and adapts it to multiple downstream tasks within the same dataset, consistent with prior works for MTS (Yue et al., 2022; Dong et al., 2023). But our univariate-to-multivariate paradigm is suitable for large-scale multi-dataset pre-training: 1) univariate pretraining ensures that varying numbers of channels across datasets do not hinder pre-training; 2) when the downstream dataset is determined, multivariate fine-tuning further incorporates channel dependency to enhance performance. However, building a foundation model that can adapt to diverse datasets for MTS remains an open question for future exploration.

## Acknowledgement

This work was in part supported by National Natural Science Foundation of China (62222607, 92370201, 72342023).

## Impact Statement

This paper presents work whose goal is to advance the field of Machine Learning. There are many potential societal consequences of our work, none which we feel must be specifically highlighted here.

## References

Agrawal, M. N., Lang, H., Offin, M., Gazit, L., and Sontag, D. Leveraging time irreversibility with order-contrastive pre-training. In International Conference on Artificial Intelligence and Statistics (AISTATS), 2022.

Bai, Y., Geng, X., Mangalam, K., Bar, A., Yuille, A., Darrell, T., Malik, J., and Efros, A. A. Sequential modeling enables scalable learning for large vision models. arXiv preprint arXiv:2312.00785, 2023.

Bi, K., Xie, L., Zhang, H., Chen, X., Gu, X., and Tian, Q. Accurate medium-range global weather forecasting with 3d neural networks. Nature, 2023.

Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., et al. Language models are few-shot learners. In Advances in Neural Information Processing Systems (NeurIPS), 2020.

Cao, W., Wang, D., Li, J., Zhou, H., Li, L., and Li, Y. Brits: Bidirectional recurrent imputation for time series. In Advances in Neural Information Processing Systems (NeurIPS), 2018.

Chang, C., Wang, W.-Y., Peng, W.-C., and Chen, T.-F. Llm4ts: Aligning pre-trained llms as data-efficient time-

series forecasters. arXiv preprint arXiv:2308.08469, 2024.

Chen, T., Kornblith, S., Norouzi, M., and Hinton, G. A simple framework for contrastive learning of visual representations. In International Conference on Machine Learning (ICML), 2020.

Cheng, M., Liu, Q., Liu, Z., Zhang, H., Zhang, R., and Chen, E. Timemae: Self-supervised representations of time series with decoupled masked autoencoders. arXiv preprint arXiv:2303.00320, 2023.

Cini, A., Marisca, I., and Alippi, C. Filling the g ap s: Multivariate time series imputation by graph neural networks. In International Conference on Learning Representations (ICLR), 2022.

Deng, A. and Hooi, B. Graph neural network-based anomaly detection in multivariate time series. In AAAI Conference on Artificial Intelligence (AAAI), 2021.

Devlin, J., Chang, M.-W., Lee, K., and Toutanova, K. Bert: Pre-training of deep bidirectional transformers for language understanding. In Annual Conference of the North American Chapter ofthe Associationfor Computational Linguistics (NAACL-HLT), 2019.

Dong, J., Wu, H., Zhang, H., Zhang, L., Wang, J., and Long, M. Simmtm: A simple pre-training framework for masked time-series modeling. In Advances in Neural Information Processing Systems (NeurIPS), 2023.

Du, W., Cotˆ e, D., and Liu, Y. Saits: Self-attention-based´ imputation for time series. Expert Systems with Applications, 2023.

Dwivedi, V. P. and Bresson, X. A generalization of transformer networks to graphs. AAAI Workshop on Deep Learning on Graphs: Methods and Applications, 2021.

Ekambaram, V., Jati, A., Nguyen, N., Sinthong, P., and Kalagnanam, J. Tsmixer: Lightweight mlp-mixer model for multivariate time series forecasting. In ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (KDD), 2023.

Eldele, E., Ragab, M., Chen, Z., Wu, M., Keong, C., Kwoh, X. L., and Guan, C. Time-series representation learning via temporal and contextual contrasting. In International Joint Conference on Artificial Intelligence (IJCAI), 2021.

Flunkert, V., Salinas, D., and Gasthaus, J. Deepar: Probabilistic forecasting with autoregressive recurrent networks. International Journal ofForecasting, 2017.

Fortuin, V., Baranchuk, D., Ratsch, G., and Mandt, S. Gp-¨ vae: Deep probabilistic time series imputation. In International Conference on Artificial Intelligence and Statistics (AISTATS), 2020.

Franceschi, J.-Y., Dieuleveut, A., and Jaggi, M. Unsupervised scalable representation learning for multivariate time series. In Advances in Neural Information Processing Systems (NeurIPS), 2019.

He, K., Chen, X., Xie, S., Li, Y., Dollar, P., and Girshick,´ R. Masked autoencoders are scalable vision learners. In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2022.

Huang, Q., Shen, L., Zhang, R., Ding, S., Wang, B., Zhou, Z., and Wang, Y. CrossGNN: Confronting noisy multivariate time series via cross interaction refinement. In Advances in Neural Information Processing Systems (NeurIPS), 2023.

Hyvarinen, A. and Morioka, H. Nonlinear ica of temporally dependent stationary sources. In International Conference on Artificial Intelligence and Statistics (AISTATS), 2017.

Kim, T., Kim, J., Tae, Y., Park, C., Choi, J.-H., and Choo, J. Reversible instance normalization for accurate time-series forecasting against distribution shift. In International Conference on Learning Representations (ICLR), 2022.

Kipf, T., Fetaya, E., Wang, K.-C., Welling, M., and Zemel, R. Neural relational inference for interacting systems. In International Conference on Machine Learning (ICML), 2018.

Lea, C. S., Flynn, M. D., Vidal, R., Reiter, A., and Hager, G. Temporal convolutional networks for action segmentation and detection. In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2017.

Li, D., Chen, D., Jin, B., Shi, L., Goh, J., and Ng, S.-K. Mad-gan: Multivariate anomaly detection for time series data with generative adversarial networks. In International Conference on Artificial Neural Networks (ICANN), 2019a.

Li, L., Yan, J., Wen, Q., Jin, Y., and Yang, X. Learning robust deep state space for unsupervised anomaly detec tion in contaminated time-series. IEEE Transactions on Knowledge and Data Engineering (TKDE), 2022.

Li, S., Jin, X., Xuan, Y., Zhou, X., Chen, W., Wang, Y.-X., and Yan, X. Enhancing the locality and breaking the memory bottleneck of transformer on time series forecasting. In Advances in Neural Information Processing Systems (NeurIPS), 2019b.

Li, Z., Wang, P., Rao, Z., Pan, L., and Xu, Z. Ti-MAE: Self-supervised masked time series autoencoders. arXiv preprint arXiv:2301.08871, 2023.

Liu, F. T., Ting, K. M., and Zhou, Z.-H. Isolation-based anomaly detection. ACM Transactions on Knowledge Discoveryfrom Data (TKDD), 2012.

Liu, S., Yu, H., Liao, C., Li, J., Lin, W., Liu, A. X., and Dustdar, S. Pyraformer: Low-complexity pyramidal attention for long-range time series modeling and forecasting. In International Conference on Learning Representations (ICLR), 2022.

Liu, Y., Yu, R., Zheng, S., Zhan, E., and Yue, Y. Naomi: Non-autoregressive multiresolution sequence imputation. In Advances in Neural Information Processing Systems (NeurIPS), 2019.

Luo, Y., Zhang, Y., Cai, X., and Yuan, X. E2gan: End-toend generative adversarial network for multivariate time series imputation. In International Joint Conference on Artificial Intelligence (IJCAI), 2019.

Lyu, X., Hueser, M., Hyland, S. L., Zerveas, G., and Raetsch, G. Improving clinical predictions through unsupervised time series representation learning. Machine Learning for Health (ML4H) Workshop at NeurIPS, 2018.

Ma, J. and Perkins, S. Time-series novelty detection using one-class support vector machines. In International Joint Conference on Neural Networks (IJCNN), 2003.

Malhotra, P., TV, V., Vig, L., Agarwal, P., and Shroff, G. Timenet: Pre-trained deep recurrent neural network for time series classification. In European Symposium on Artificial Neural Networks, Computational Intelligence and Machine Learning (ESANN), 2017.

Manning, C. D. An introduction to information retrieval. Cambridge university press, 2009.

Mohsenvand, M. N., Izadi, M. R., and Maes, P. Contrastive representation learning for electroencephalogram classification. In Machine Learningfor Health (ML4H), 2020.

Nate Gruver, Marc Finzi, S. Q. and Wilson, A. G. Large Language Models Are Zero Shot Time Series Forecasters. In Advances in Neural Information Processing Systems (NeurIPS), 2023.

Nie, Y., H. Nguyen, N., Sinthong, P., and Kalagnanam, J. A time series is worth 64 words: Long-term forecasting with transformers. In International Conference on Learning Representations (ICLR), 2023.

Radford, A., Wu, J., Child, R., Luan, D., Amodei, D., Sutskever, I., et al. Language models are unsupervised multitask learners. OpenAI blog, 2019.

Ramchandran, S., Tikhonov, G., Kujanpa¨a, K., Koskinen,¨ M., and Lahdesm ¨ aki, H. Longitudinal variational autoen-¨ coder. In International Conference on Artificial Intelligence and Statistics (AISTATS), 2021.

Reimers, N. and Gurevych, I. Sentence-bert: Sentence embeddings using siamese bert-networks. In Conference on Empirical Methods in Natural Language Processing (EMNLP), 2019.

Ren, S., Wu, Z., and Zhu, K. Q. Emo: Earth mover distance optimization for auto-regressive language modeling. arXiv preprint arXiv:2310.04691, 2023.

Sarkar, P. and Etemad, A. Self-supervised ecg representation learning for emotion recognition. IEEE Transactions on Affective Computing (TAC), 2020.

Scholkopf, B., Platt, J. C., Shawe-Taylor, J., Smola, A. J.,¨ and Williamson, R. C. Estimating the support of a highdimensional distribution. Neural computation, 2001.

Shao, Z., Zhang, Z., Wang, F., and Xu, Y. Pre-training enhanced spatial-temporal graph neural network for multivariate time series forecasting. In ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (KDD), 2022.

Shen, L., Li, Z., and Kwok, J. Timeseries anomaly detection using temporal hierarchical one-class network. In Advances in Neural Information Processing Systems (NeurIPS), 2020.

Su, Y., Zhao, Y., Niu, C., Liu, R., Sun, W., and Pei, D. Robust anomaly detection for multivariate time series through stochastic recurrent neural network. In ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (KDD), 2019.

Tariq, S., Lee, S., Shin, Y., Lee, M. S., Jung, O., Chung, D., and Woo, S. S. Detecting anomalies in space using multivariate convolutional lstm with mixtures of probabilistic pca. In ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (KDD), 2019.

Tashiro, Y., Song, J., Song, Y., and Ermon, S. Csdi: Conditional score-based diffusion models for probabilistic time series imputation. In Advances in Neural Information Processing Systems (NeurIPS), 2021.

Tonekaboni, S., Eytan, D., and Goldenberg, A. Unsupervised representation learning for time series with temporal neighborhood coding. In International Conference on Learning Representations (ICLR).

Woo, G., Liu, C., Sahoo, D., Kumar, A., and Hoi, S. CoST: Contrastive learning of disentangled seasonal-trend representations for time series forecasting. In International Conference on Learning Representations (ICLR), 2022.

Wu, H., Xu, J., Wang, J., and Long, M. Autoformer: Decomposition transformers with auto-correlation for long-term series forecasting. In Advances in Neural Information Processing Systems (NeurIPS), 2021.

Wu, H., Hu, T., Liu, Y., Zhou, H., Wang, J., and Long, M. Timesnet: Temporal 2d-variation modeling for general time series analysis. In International Conference on Learning Representations (ICLR), 2023.

Wu, Z., Pan, S., Long, G., Jiang, J., Chang, X., and Zhang, C. Connecting the dots: Multivariate time series forecasting with graph neural networks. In ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (KDD), 2020.

Xu, J., Wu, H., Wang, J., and Long, M. Anomaly transformer: Time series anomaly detection with association discrepancy. In International Conference on Learning Representations (ICLR), 2022.

Yang, L. and Hong, S. Unsupervised time-series representation learning with iterative bilinear temporal-spectral fusion. In International Conference on Machine Learning (ICML), 2022.

Yang, Y., Zhang, C., Zhou, T., Wen, Q., and Sun, L. Dcdetector: Dual attention contrastive representation learning for time series anomaly detection. In ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (KDD), 2023.

Yoon, J., Zame, W. R., and van der Schaar, M. Estimating missing data in temporal data streams using multidirectional recurrent neural networks. IEEE Transactions on Biomedical Engineering, 2018.

Yu, M. and Sun, S. Policy-based reinforcement learning for time series anomaly detection. Engineering Applications ofArtificial Intelligence, 2020.

Yue, Z., Wang, Y., Duan, J., Yang, T., Huang, C., Tong, Y., and Xu, B. Ts2vec: Towards universal representation of time series. In AAAI Conference on Artificial Intelligence (AAAI), 2022.

Zeng, A., Chen, M., Zhang, L., and Xu, Q. Are transformers effective for time series forecasting? In AAAI Conference on Artificial Intelligence (AAAI), 2023.

Zerveas, G., Jayaraman, S., Patel, D., Bhamidipaty, A., and Eickhoff, C. A transformer-based framework for multivariate time series representation learning. In ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (KDD), 2021.

Zhang, X., Zhao, Z., Tsiligkaridis, T., and Zitnik, M. Selfsupervised contrastive pre-training for time series via time-frequency consistency. In Advances in Neural Information Processing Systems (NeurIPS), 2022.

Zhang, Y. and Yan, J. Crossformer: Transformer utilizing cross-dimension dependency for multivariate time series

forecasting. In International Conference on Learning Representations (ICLR), 2023.

Zhao, H., Wang, Y., Duan, J., Huang, C., Cao, D., Tong, Y., Xu, B., Bai, J., Tong, J., and Zhang, Q. Multivariate timeseries anomaly detection via graph attention network. In IEEE International Conference on Data Mining (ICDM), 2020.

Zhou, B., Liu, S., Hooi, B., Cheng, X., and Ye, J. Beatgan: Anomalous rhythm detection using adversarially generated time series. In International Joint Conference on Artificial Intelligence (IJCAI), 2019.

Zhou, H., Zhang, S., Peng, J., Zhang, S., Li, J., Xiong, H., and Zhang, W. Informer: Beyond efficient transformer for long sequence time-series forecasting. In AAAI Conference on Artificial Intelligence (AAAI), 2021.

Zhou, T., Ma, Z., Wen, Q., Wang, X., Sun, L., and Jin, R. Fedformer: Frequency enhanced decomposed transformer for long-term series forecasting. In International Conference on Machine Learning (ICML), 2022.

Zhou, T., Niu, P., Wang, X., Sun, L., and Jin, R. One fits all: Power general time series analysis by pretrained LM. In Advances in Neural Information Processing Systems (NeurIPS), 2023.

## A. Details of Experiments

## A.1. Datasets

We conduct experiments on the following eight datasets following Wu et al. (2023); Yang et al. (2023):

1) ETTm1 records 7 crucial indicators of an electricity transformer, including high useful load and oil temperature, etc. Data points are recorded every 15 minutes and the entire dataset covers a period of two years. We use data from the first 20 months and split it into train/valid/test sets with a ratio of 0.6:0.2:0.2.

2) Weather records 21 meteorological indicators in Beutenberg, including air temperature and dewpoint, etc. Data points are recorded every 10 minutes and the entire dataset covers the whole 2020 year. Train/valid/test sets are split by a ratio of 0.7:0.1,0.2.

3) Electricity records hourly electricity consumption (in kW) of 321 clients from 2012 to 2014. Train/valid/test sets are split by a ratio of 0.7:0.1,0.2.

4) Traffic contains San Francisco Bay area freeways’ road occupancy rates measured by 862 sensors from 2016.07 to 2018.06. Data points are recorded every hour and train/valid/test sets are split by a ratio of 0.7:0.1,0.2.

5) SMD records 38 indicators of a server machine from a large Internet company, including CPU load, network usage, etc. The entire dataset covers a period of 5 weeks.

6) PSM records 25 indicators of application server nodes at eBay, including CPU and memory utilization, etc. The training set covers 13 weeks, followed by 8 weeks for testing.

7) SWaT records indicators measured by 51 sensors of a modern industrial control system.

8) GECCO records 9 indicators about the drinking-water quality, including PH value and amount of chlorine dioxide, etc. Data points are recorded every minute.

The first four datasets are often used in forecasting and imputation tasks and our train/val/test splits are the same as Wu et al. (2021); Nie et al. (2023). The last four datasets are often used in anomaly detection tasks. Each of them is originally divided into two parts for training and testing. Only testing parts are labeled with ground truth anomaly annotations. Following Wu et al. (2023), we further split the original training set by a ratio of 0.8:0.2 for our training and validation. Table 4 shows the statistical characteristics of each dataset.

The first 7 datasets are publicly available at https://github.com/thuml/Time-Series-Library and GECCO is available at https://github.com/DAMO-DI-ML/KDD2023-DCdetector.

Table 4: Statistical characteristics of datasets used in experiments.

<table><tr><td>Dataset</td><td>Channels</td><td>Train Timestamps</td><td>Valid Timestamps</td><td>Test Timestamps</td><td>Field</td></tr><tr><td>ETTm1</td><td>7</td><td>34,560</td><td>11,520</td><td>11,520</td><td>electricity transformer indicators</td></tr><tr><td>Weather</td><td>21</td><td>36,887</td><td>5,270</td><td>10,539</td><td>meteorological weather indicators</td></tr><tr><td>Electricity</td><td>321</td><td>18,412</td><td>2,632</td><td>5,260</td><td>electricity consumption</td></tr><tr><td>Traffic</td><td>862</td><td>12,280</td><td>1,756</td><td>3,508</td><td>road occupancy rates</td></tr><tr><td>SMD</td><td>38</td><td>566,724</td><td>141,681</td><td>708,420</td><td>server machine indicators</td></tr><tr><td>PSM</td><td>25</td><td>105,984</td><td>26,497</td><td>87,841</td><td>application server indicators</td></tr><tr><td>SWaT</td><td>51</td><td>396,000</td><td>99,000</td><td>449,919</td><td>industrial control system indicators</td></tr><tr><td>GECCO</td><td>9</td><td>55,408</td><td>13,852</td><td>69,261</td><td>drinking-water quality</td></tr></table>

## A.2. General-purpose and Pre-training Baselines

General-purpose Baseline We select TimesNet (Wu et al., 2023) as the general-purpose baseline. TimesNet discovers multiple periods of MTS by Fast Fourier Transform and then transforms time series into a set of 2D tensors according to these periods. These 2D tensors are processed by inception blocks for feature extraction. TimesNet conducts multiple tasks by changing the output layer and training criterion. The source code is available at https://github.com/thuml/ Time-Series-Library.

Pre-training Baselines We select the following 2 pre-training methods for comparison:

1) TS2Vec (Yue et al., 2022) is a contrastive learning based pre-training method for MTS. It uses timestamp masking and random cropping to generate contexts and representations at the same timestamp in two contexts are viewed as positive pairs for contrastive learning. Max pooling is used to perform hierarchical contrastive learning at multiple scales. The source code is available at https://github.com/yuezhihan/ts2vec.

2) SimMTM (Dong et al., 2023) is a mask-reconstruction based pre-training method for MTS. It reconstructs the original time series with multiple masked series with different masks. A contrastive-style manifold constraint is further used to learn series-wise representation. The source code is available at https://github.com/thuml/SimMTM.

## A.3. Experiments for Forecasting

Task-specific Baselines We select the following 4 task-specific baselines for forecasting:

1) PatchTST (Nie et al., 2023) is the current SOTA for MTS forecasting. It divides the input MTS into patches and uses a Transformer encoder with channel independence to process these patches. The encoder output is then flattened and linearly projected to desired lengths for final forecasting. The source code is available at https: //github.com/yuqinie98/PatchTST.

2) DLinear (Zeng et al., 2023) is a light-weight MTS forecaster. It decomposes input MTS into trend and season components and applies a linear model on each component respectively. The source code is available at https: //github.com/cure-lab/LTSF-Linear.

3) Crossformer (Zhang & Yan, 2023) is a Transformer that explicitly captures cross-channel dependency for MTS forecasting. It divides MTS into patches like PatchTST and proposes a two-stage attention mechanism to capture both temporal and cross-channel dependency. A hierarchical encoder-decoder is constructed for forecasting. The source code is available at https://github.com/Thinklab-SJTU/Crossformer.

4) FEDformer (Zhou et al., 2022) is a Transformer that uses seasonal-trend decomposition with frequency-enhanced blocks to capture temporal dependency for MTS forecasting. The source code is available at https://github. com/MAZiqing/FEDformer.

Setup We use the common protocol for MTS forecasting (Zhou et al., 2021; Wu et al., 2021; Nie et al., 2023): train/val/test sets are normalized with the mean and standard deviation of the training set. On ETTm1, Weather, Electricity and Traffic, we forecast the future L<sub>f</sub> = {96, 192, 337, 720} steps with the default past window length set to 336. Considering that FEDformer and TimesNet may prefer a shorter past window, we select past lengths from {96, 192, 336, 720} via grid search for these two methods. On datasets containing anomaly points, i.e. SMD, PSM, SWaT and GECCO, we forecast the future L<sub>f</sub> = {50, 100, 150, 200} steps with the default past window length set to 400. Similarly, past lengths for FEDformer and TimesNet are chosen from {50, 100, 200, 400} via grid search. All experiments are repeated 3 times and the averaged Mean Square Error (mSE) and Mean Absolute Error (mAE) are reported.

## A.4. Experiments for Imputation

Task-specific Baselines We select the following 4 task-specific baselines for Imputation:

1) SAITS (Du et al., 2023) is a self-attention-based method for MTS imputation. The model is optimized via two joint tasks: 1) missing series imputation to fill the missing values and 2) observed series reconstruction to help the model converge to the distribution of the dataset. The source code is available at https://github.com/WenjieDu/SAITS

2) GRIN (Cini et al., 2022) proposes an encoder-decoder that utilizes RNN and GNN for MTS imputation. It uses a bidirectional architecture to process the input MTS. Furthermore, a two-stage imputation process is devised, where the first stage utilizes the features extracted GNN, followed by the second stage utilizing represen tations from RNN to refine the first-stage imputation. The source code is available at https://github.com/ Graph-Machine-Learning-Group/grin.

3) LI (Linear Interpolation) is a traditional method for MTS imputation which fills the missing values by constructing a linear curve between adjacent observed data points. We use its Pandas implementation, which is available at https: //pandas.pydata.org/docs/reference/api/pandas.DataFrame.interpolate.html.

4) SI (Spline Interpolation) is a traditional method for MTS imputation which fills the missing values with piecewise low-degree polynomial curves rather than a single, high-degree polynomial curve. We also use its Pandas implementation, which is available at https://pandas.pydata.org/docs/reference/api/pandas. DataFrame.interpolate.html.

Setup Considering that point-wise missing is easy to solve with traditional interpolation methods and missing patterns in the real world are often structured and appear consecutively (Tashiro et al., 2021), we conduct experiments on block-wise imputation: we set the observed window length for imputation to $L _ { i m p } = 6 0 0$ for all 8 datasets. On each dataset, we evaluate imputation performance at 4 different missing range levels: {0% ∼ 12.5%, 12.5% ∼ 25%, 25% ∼ 37.5%, 37.5% ∼ 50%}. To generate an instance with block-wise missing, we first sample a mask ratio from the corresponding range level for each channel. Subsequently, a randomly sampled consecutive block of this ratio is masked in each channel. Similar to forecasting, all experiments are repeated 3 times and the averaged Mean Square Error (mSE) and Mean Absolute Error (mAE) are reported.

## A.5. Experiments for Anomaly Detection

Task-specific Baselines We select the following 4 task-specific baselines for Anomaly Detection:

1) DCdetector (Yang et al., 2023) is a contrastive representation-based attention model for MTS anomaly detection. The motivation is that it is easier to learn shared patterns among different views of normal points than abnormal ones. Thus, DCdetector learns permutation invariant representations and uses the representation discrepancy between two views as the anomaly score. The source code is available at https://github.com/DAMO-DI-ML/ KDD2023-DCdetector.

2) AnomalyTrans (Xu et al., 2022) is an association discrepancy-based Transformer for MTS anomaly detection. The motivation is that it is difficult for abnormal points to build nontrivial associations with the whole series. Therefore, the discrepancy between the learned attention distribution and an adjacent-concentrated Gaussian distribution is used as the anomaly score. The source code is available at https://github.com/thuml/Anomaly-Transformer.

3) iForest (Isolation Forest) (Liu et al., 2012) is a traditional algorithm for anomaly detection. The main idea is that anomalies can be isolated more easily than normal points. By employing a tree-based structure with random feature selection and splits, anomalies tend to be isolated with shorter paths. Anomaly score is defined as the depth of the leaf containing this point, which is equivalent to the number of splittings required to isolate it. To adapt iForest for time series, we fold multiple adjacent timestamps around a center point to form a sample following Ma & Perkins (2003). We use the sklearn implementation of iForest, which is available at https://scikit-learn.org/stable/ modules/generated/sklearn.ensemble.IsolationForest.html.

4) OCSVM (One-Class Support Vector Machine) (Scholkopf et al.¨ , 2001) is a traditional algorithm for anomaly detection. It constructs a hyperplane that encapsulates the majority normal data points in a high-dimensional space. Samples lying outside this hyperplane are considered potential anomalies and signed distance to the hyperplane is used as the anomaly score. Similar to iForest, we fold adjacent timestamps to adapt OCSVM to time series and use the sklearn implementation, which is available at https://scikit-learn.org/stable/modules/ generated/sklearn.svm.OneClassSVM.html.

Setup We use the common protocol for MTS anomaly detection (Xu et al., 2022; Wu et al., 2023; Yang et al., 2023): models undergoes unsupervised learning on training and validation sets. The testing sets are divided into non-overlapped sub-series of length 100 for metric evaluation. All experiments are repeated 3 times and the averaged metrics are reported.

We evaluate two anomaly detection metrics: F1-score and Average Precision (AP) (Manning, 2009). F1-score is a commonly used metric for MTS anomaly detection (Xu et al., 2022; Wu et al., 2023; Yang et al., 2023) and it needs a threshold to transform anomaly scores into labels. Following Yang et al. (2023), the threshold is chosen by ensuring that δ fraction of points in training and validation sets surpass the specified threshold. Then, the selected threshold is used to label the testing set. δ is set to 0.5% for SMD, 1% for PSM and SWaT, 2% for GECCO. Considering anomaly scores of different methods have different physical meanings and the F1-score is sensitive to the threshold selection process, we also evaluate AP as a more comprehensive metric. To evaluate AP, we threshold at every possible value and get M precision-recall pairs $\{ ( P _ { i } , R _ { i } ) \} _ { i = 1 } ^ { M } , \forall j : R _ { j } \leq R _ { j + 1 }$ , and AP is computed as $\begin{array} { r } { A P = \sum _ { i = 2 } ^ { M } ( R _ { i } - R _ { i - 1 } ) P _ { i } } \end{array}$ . Note that the selected threshold for F1-score corresponds to a single pair in $\{ ( P _ { i } , R _ { i } ) \} _ { i = 1 } ^ { M }$

The widely-used segment adjustment strategy (Shen et al., 2020; Xu et al., 2022; Yang et al., 2023; Wu et al., 2023) is used for F1-score and AP evaluation: if a single timestamp within a contiguous anomaly segment is accurately detected, the entire anomalies within that same segment are also deemed correctly identified. This strategy relies on the fact that, in time series analysis, human operators often prioritize the overall anomaly segment rather than the point-wise anomaly. Hence, triggering an alert at any point within a contiguous anomaly segment is deemed acceptable.

## A.6. Implementation Details

Pre-training For all datasets, the encoder consists of 4 standard Transformer layers and the decoder consists of 1 standard Transformer layer. The dimension of hidden state $d _ { m o d e l }$ is set to 256 and the head number of multi-head attention is set to 4. For ETTm1, Weather, Electricity and Traffic, we set patch size, min and max patch number to $P = 1 2 , N _ { m i n } = 2 0 , N _ { m a x } = 2 0 0$ ; for datasets containing anomaly points, i.e. SMD, PSM, SWaT and GECCO, we set $P = 1 0 , N _ { m i n } = 5 , N _ { m a x } = 1 0 0 .$

As for parameter optimization, the mask ratio is set to $\alpha = 0 . 5$ . The batch size is set to 256. Adam optimizer with a constant learning rate of 1e-4 is used for optimization. The maximum training step is set to 500,000. The model undergoes validation every 5,000 steps on the validation set, and if the validation loss fails to decrease over 10 consecutive validations, the pre-training process is terminated early. The model with the lowest validation loss is retained.

Fine-tuning For all 3 downstream tasks on all 8 datasets, we insert one TC layer between the frozen encoder and decoder for fine-tuning. $d _ { m o d e l }$ and the head number are the same as pre-training. Adam optimizer with a constant learning rate is used for optimization. The learning rate is set to 1e-5 for forecasting and anomaly detection and 5e-4 for imputation. The maximum training epoch is set to 20. If the validation loss fails to decrease over 3 consecutive validations, the training process is stopped early. The hyper-parameter r in Equation 9 for graph construction is set as $r = \operatorname* { m i n } ( 1 0 , \lceil 0 . 5 C \rceil )$ , i.e. r = 4 for ETTm1, r = 5 for GECCO and r = 10 for all other 6 datasets.

All deep learning methods, including our UP2ME, are implemented in PyTorch and run on 2 NVIDIA GeForce RTX 3090 GPUs with 24GB memory.

## B. Full Results

Due to the space limitation in the main text, we place the full results of Section 3.1 here. mSE/mAE evaluation of forecasting on different prediction lengths is shown in Table 5; mSE/mAE evaluation of imputation on different missing levels is shown in Table 6; Precision, recall, F1-score and AP evaluation of anomaly detection is shown in Table 7.

Table 5: Full mSE/mAE evaluation of forecasting. The prediction length $L _ { f }$ is set to {96, 192, 336, 720} for the first four datasets and {50, 100, 150, 200} for the last four. Bold/underline indicates the best/second. Our method is marked in gray. OOM indicates out-of-memory.

<table><tr><td rowspan="2" colspan="2">Methods</td><td colspan="8">Task-Specific</td><td colspan="2">General</td><td colspan="8">Pre-Training</td></tr><tr><td colspan="2">PatchTST</td><td colspan="2">DLinear</td><td colspan="2">Crossformer</td><td colspan="2">FEDformer</td><td colspan="2">TimesNet</td><td colspan="2">TS2Vec</td><td colspan="2">SimMTM</td><td colspan="2">UP2ME(IR)</td><td colspan="2">UP2ME(FT)</td></tr><tr><td colspan="2">Metric</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td></tr><tr><td rowspan="5">ETTml</td><td>96</td><td>0.290</td><td>0.340</td><td>0.299</td><td>0.343</td><td>0.322</td><td>0.387</td><td>0.377</td><td>0.422</td><td>0.329</td><td>0.367</td><td>0.673</td><td>0.566</td><td>0.292</td><td>0.349</td><td>0.292</td><td>0.330</td><td>0.287</td><td>0.334</td></tr><tr><td>192</td><td>0.330</td><td>0.369</td><td>0.335</td><td>0.365</td><td>0.391</td><td>0.422</td><td>0.403</td><td>0.438</td><td>0.382</td><td>0.400</td><td>0.732</td><td>0.623</td><td>0.329</td><td>0.373</td><td>0.337</td><td>0.359</td><td>0.323</td><td>0.361</td></tr><tr><td>336</td><td>0.369</td><td>0.394</td><td>0.370</td><td>0.386</td><td>0.452</td><td>0.472</td><td>0.447</td><td>0.457</td><td>0.415</td><td>0.422</td><td>0.823</td><td>0.681</td><td>0.364</td><td>0.393</td><td>0.378</td><td>0.383</td><td>0.351</td><td>0.381</td></tr><tr><td>720</td><td>0.422</td><td>0.426</td><td>0.427</td><td>0.423</td><td>0.607</td><td>0.562</td><td>0.480</td><td>0.472</td><td>0.444</td><td>0.443</td><td>0.917</td><td>0.735</td><td>0.414</td><td>0.422</td><td>0.435</td><td>0.418</td><td>0.405</td><td>0.419</td></tr><tr><td>Avg</td><td>0.353</td><td>0.382</td><td>0.358</td><td>0.379</td><td>0.443</td><td>0.461</td><td>0.427</td><td>0.447</td><td>0.393</td><td>0.408</td><td>0.787</td><td>0.651</td><td>0.350</td><td>0.384</td><td>0.360</td><td>0.372</td><td>0.341</td><td>0.374</td></tr><tr><td rowspan="5">Weather</td><td>96</td><td>0.150</td><td>0.198</td><td>0.174</td><td>0.234</td><td>0.154</td><td>0.227</td><td>0.231</td><td>0.322</td><td>0.163</td><td>0.217</td><td>0.179</td><td>0.262</td><td>0.158</td><td>0.211</td><td>0.180</td><td>0.222</td><td>0.144</td><td>0.192</td></tr><tr><td>192</td><td>0.195</td><td>0.241</td><td>0.216</td><td>0.274</td><td>0.198</td><td>0.270</td><td>0.283</td><td>0.353</td><td>0.212</td><td>0.259</td><td>0.225</td><td>0.305</td><td>0.200</td><td>0.249</td><td>0.231</td><td>0.265</td><td>0.187</td><td>0.237</td></tr><tr><td>336</td><td>0.250</td><td>0.284</td><td>0.261</td><td>0.312</td><td>0.276</td><td>0.338</td><td>0.340</td><td>0.383</td><td>0.269</td><td>0.304</td><td>0.282</td><td>0.349</td><td>0.249</td><td>0.286</td><td>0.289</td><td>0.306</td><td>0.237</td><td>0.277</td></tr><tr><td>720</td><td>0.319</td><td>0.334</td><td>0.326</td><td>0.367</td><td>0.329</td><td>0.362</td><td>0.389</td><td>0.404</td><td>0.344</td><td>0.353</td><td>0.360</td><td>0.403</td><td>0.319</td><td>0.336</td><td>0.366</td><td>0.360</td><td>0.316</td><td>0.331</td></tr><tr><td>Avg</td><td>0.228</td><td>0.264</td><td>0.244</td><td>0.297</td><td>0.239</td><td>0.299</td><td>0.311</td><td>0.365</td><td>0.247</td><td>0.283</td><td>0.261</td><td>0.330</td><td>0.232</td><td>0.270</td><td>0.266</td><td>0.288</td><td>0.221</td><td>0.260</td></tr><tr><td rowspan="5">Electricity</td><td>96</td><td>0.130</td><td>0.223</td><td>0.141</td><td>0.238</td><td>0.156</td><td>0.264</td><td>0.211</td><td>0.326</td><td>0.165</td><td>0.269</td><td>0.366</td><td>0.446</td><td rowspan="4" colspan="2">OOM</td><td>0.130</td><td>0.220</td><td>0.123</td><td>0.214</td></tr><tr><td>192</td><td>0.149</td><td>0.241</td><td>0.155</td><td>0.252</td><td>0.184</td><td>0.292</td><td>0.226</td><td>0.339</td><td>0.185</td><td>0.286</td><td>0.370</td><td>0.447</td><td>0.149</td><td>0.238</td><td>0.143</td><td>0.233</td></tr><tr><td>336</td><td>0.166</td><td>0.260</td><td>0.170</td><td>0.269</td><td>0.213</td><td>0.312</td><td>0.243</td><td>0.354</td><td>0.197</td><td>0.299</td><td>0.379</td><td>0.452</td><td>0.169</td><td>0.257</td><td>0.160</td><td>0.250</td></tr><tr><td>720</td><td>0.210</td><td>0.299</td><td>0.205</td><td>0.302</td><td>0.268</td><td>0.356</td><td>0.276</td><td>0.378</td><td>0.227</td><td>0.320</td><td>0.394</td><td>0.458</td><td>0.213</td><td>0.293</td><td>0.193</td><td>0.282</td></tr><tr><td>Avg</td><td>0.164</td><td>0.255</td><td>0.168</td><td>0.265</td><td>0.205</td><td>0.306</td><td>0.239</td><td>0.349</td><td>0.194</td><td>0.293</td><td>0.377</td><td>0.451</td><td colspan="2">OOM</td><td>0.165</td><td>0.252</td><td>0.155</td><td>0.245</td></tr><tr><td rowspan="5">Traffic</td><td>96</td><td>0.365</td><td>0.250</td><td>0.413</td><td>0.288</td><td>0.485</td><td>0.273</td><td>0.629</td><td>0.402</td><td>0.588</td><td>0.315</td><td>0.942</td><td>0.563</td><td rowspan="4" colspan="2">OOM</td><td>0.369</td><td>0.241</td><td>0.358</td><td>0.235</td></tr><tr><td>192</td><td>0.383</td><td>0.258</td><td>0.425</td><td>0.293</td><td>0.506</td><td>0.282</td><td>0.635</td><td>0.397</td><td>0.614</td><td>0.327</td><td>0.940</td><td>0.558</td><td>0.392</td><td>0.251</td><td>0.382</td><td>0.249</td></tr><tr><td>336</td><td>0.396</td><td>0.264</td><td>0.439</td><td>0.301</td><td>0.538</td><td>0.300</td><td>0.669</td><td>0.419</td><td>0.631</td><td>0.338</td><td>0.959</td><td>0.563</td><td>0.404</td><td>0.257</td><td>0.393</td><td>0.254</td></tr><tr><td>720</td><td>0.435</td><td>0.287</td><td>0.468</td><td>0.319</td><td>0.583</td><td>0.315</td><td>0.698</td><td>0.432</td><td>0.655</td><td>0.348</td><td>1.051</td><td>0.592</td><td>0.439</td><td>0.278</td><td>0.426</td><td>0.274</td></tr><tr><td>Avg</td><td>0.395</td><td>0.265</td><td>0.436</td><td>0.300</td><td>0.528</td><td>0.292</td><td>0.658</td><td>0.413</td><td>0.622</td><td>0.332</td><td>0.973</td><td>0.569</td><td colspan="2">OOM</td><td>0.401</td><td>0.257</td><td>0.390</td><td>0.253</td></tr><tr><td rowspan="5">SMD</td><td>50</td><td>0.843</td><td>0.140</td><td>0.916</td><td>0.158</td><td>0.863</td><td>0.140</td><td>0.948</td><td>0.206</td><td>1.012</td><td>0.156</td><td>1.236</td><td>0.404</td><td>0.836</td><td>0.152</td><td>0.837</td><td>0.150</td><td>0.818</td><td>0.132</td></tr><tr><td>100</td><td>0.880</td><td>0.165</td><td>0.971</td><td>0.189</td><td>0.901</td><td>0.165</td><td>0.999</td><td>0.227</td><td>0.961</td><td>0.186</td><td>1.270</td><td>0.418</td><td>0.876</td><td>0.177</td><td>0.899</td><td>0.189</td><td>0.858</td><td>0.160</td></tr><tr><td>150</td><td>0.911</td><td>0.185</td><td>1.020</td><td>0.214</td><td>0.943</td><td>0.212</td><td>1.044</td><td>0.247</td><td>0.996</td><td>0.201</td><td>1.312</td><td>0.437</td><td>0.913</td><td>0.199</td><td>0.958</td><td>0.221</td><td>0.890</td><td>0.181</td></tr><tr><td>200</td><td>0.940</td><td>0.205</td><td>1.059</td><td>0.236</td><td>0.991</td><td>0.223</td><td>1.088</td><td>0.266</td><td>1.012</td><td>0.208</td><td>1.338</td><td>0.448</td><td>0.949</td><td>0.219</td><td>1.003</td><td>0.243</td><td>0.923</td><td>0.201</td></tr><tr><td>Avg</td><td>0.893</td><td>0.174</td><td>0.992</td><td>0.199</td><td>0.925</td><td>0.185</td><td>1.020</td><td>0.236</td><td>0.995</td><td>0.188</td><td>1.289</td><td>0.427</td><td>0.894</td><td>0.187</td><td>0.924</td><td>0.201</td><td>0.872</td><td>0.169</td></tr><tr><td rowspan="5">PSM</td><td>50</td><td>0.196</td><td>0.241</td><td>0.198</td><td>0.258</td><td>0.261</td><td>0.273</td><td>0.221</td><td>0.265</td><td>0.197</td><td>0.244</td><td>0.512</td><td>0.501</td><td>0.213</td><td>0.260</td><td>0.378</td><td>0.379</td><td>0.191</td><td>0.237</td></tr><tr><td>100</td><td>0.274</td><td>0.293</td><td>0.271</td><td>0.316</td><td>0.353</td><td>0.323</td><td>0.292</td><td>0.314</td><td>0.267</td><td>0.293</td><td>0.658</td><td>0.567</td><td>0.281</td><td>0.306</td><td>0.575</td><td>0.490</td><td>0.261</td><td>0.283</td></tr><tr><td>150</td><td>0.337</td><td>0.334</td><td>0.354</td><td>0.371</td><td>0.411</td><td>0.365</td><td>0.361</td><td>0.351</td><td>0.336</td><td>0.333</td><td>0.753</td><td>0.609</td><td>0.348</td><td>0.347</td><td>0.687</td><td>0.545</td><td>0.325</td><td>0.323</td></tr><tr><td>200</td><td>0.403</td><td>0.374</td><td>0.433</td><td>0.418</td><td>0.482</td><td>0.399</td><td>0.432</td><td>0.390</td><td>0.406</td><td>0.373</td><td>0.825</td><td>0.641</td><td>0.418</td><td>0.387</td><td>0.766</td><td>0.583</td><td>0.385</td><td>0.359</td></tr><tr><td>Avg</td><td>0.303</td><td>0.310</td><td>0.314</td><td>0.341</td><td>0.377</td><td>0.326</td><td>0.326</td><td>0.330</td><td>0.301</td><td>0.311</td><td>0.687</td><td>0.580</td><td>0.315</td><td>0.325</td><td>0.602</td><td>0.499</td><td>0.290</td><td>0.300</td></tr><tr><td rowspan="5">SWaT</td><td>50</td><td>0.132</td><td>0.043</td><td>0.196</td><td>0.102</td><td>0.156</td><td>0.082</td><td>0.163</td><td>0.078</td><td>0.139</td><td>0.040</td><td>11.366</td><td>1.525</td><td>0.170</td><td>0.064</td><td>0.168</td><td>0.056</td><td>0.123</td><td>0.040</td></tr><tr><td>100</td><td>0.198</td><td>0.060</td><td>0.298</td><td>0.149</td><td>0.211</td><td>0.102</td><td>0.244</td><td>0.100</td><td>0.204</td><td>0.058</td><td>9.835</td><td>1.504</td><td>0.230</td><td>0.080</td><td>0.274</td><td>0.087</td><td>0.186</td><td>0.056</td></tr><tr><td>150</td><td>0.247</td><td>0.075</td><td>0.422</td><td>0.198</td><td>0.261</td><td>0.115</td><td>0.300</td><td>0.110</td><td>0.260</td><td>0.072</td><td>9.547</td><td>1.566</td><td>0.275</td><td>0.094</td><td>0.331</td><td>0.105</td><td>0.243</td><td>0.070</td></tr><tr><td>200</td><td>0.290</td><td>0.087</td><td>0.499</td><td>0.224</td><td>0.319</td><td>0.141</td><td>0.345</td><td>0.124</td><td>0.301</td><td>0.084</td><td>9.581</td><td>1.644</td><td>0.318</td><td>0.107</td><td>0.395</td><td>0.123</td><td>0.285</td><td>0.082</td></tr><tr><td>Avg</td><td>0.217</td><td>0.066</td><td>0.354</td><td>0.168</td><td>0.237</td><td>0.110</td><td>0.263</td><td>0.103</td><td>0.226</td><td>0.063</td><td>10.082</td><td>1.559</td><td>0.248</td><td>0.138</td><td>0.292</td><td>0.093</td><td>0.210</td><td>0.062</td></tr><tr><td rowspan="5">GECCO</td><td>50</td><td>1.380</td><td>0.259</td><td>1.449</td><td>0.338</td><td>2.241</td><td>0.531</td><td>1.619</td><td>0.317</td><td>1.443</td><td>0.247</td><td>2.071</td><td>0.665</td><td>1.404</td><td>0.270</td><td>1.288</td><td>0.263</td><td>1.225</td><td>0.232</td></tr><tr><td>100</td><td>1.572</td><td>0.308</td><td>1.712</td><td>0.464</td><td>2.564</td><td>0.622</td><td>1.769</td><td>0.357</td><td>1.607</td><td>0.302</td><td>2.395</td><td>0.747</td><td>1.585</td><td>0.322</td><td>1.450</td><td>0.322</td><td>1.394</td><td>0.287</td></tr><tr><td>150</td><td>1.812</td><td>0.348</td><td>1.796</td><td>0.506</td><td>2.900</td><td>0.724</td><td>1.776</td><td>0.413</td><td>1.671</td><td>0.339</td><td>2.624</td><td>0.811</td><td>1.683</td><td>0.352</td><td>1.531</td><td>0.352</td><td>1.489</td><td>0.326</td></tr><tr><td>200</td><td>1.860</td><td>0.374</td><td>1.853</td><td>0.522</td><td>2.845</td><td>0.751</td><td>1.778</td><td>0.446</td><td>1.902</td><td>0.367</td><td>2.787</td><td>0.862</td><td>1.788</td><td>0.380</td><td>1.635</td><td>0.376</td><td>1.543</td><td>0.353</td></tr><tr><td>Avg</td><td>1.656</td><td>0.322</td><td>1.703</td><td>0.457</td><td>2.637</td><td>0.657</td><td>1.735</td><td>0.383</td><td>1.655</td><td>0.314</td><td>2.469</td><td>0.771</td><td>1.615</td><td>0.331</td><td>1.476</td><td>0.328</td><td>1.413</td><td>0.299</td></tr></table>

Table 6: Full mSE/mAE evaluation of imputation. Missing ratios are set into 4 levels: {0% ∼ 12.5%, 12.5% ∼ 25%, 25% ∼ 37.5%, 37.5% ∼ 50%}. Bold/underline indicates the best/second. Our method is marked in gray. OOM indicates out-ofmemory.

<table><tr><td rowspan="2" colspan="2">Methods</td><td colspan="8">Task-Specific</td><td colspan="2">General</td><td colspan="8">Pre-Training</td></tr><tr><td colspan="2">SAITS</td><td colspan="2">GRIN</td><td colspan="2">LI</td><td colspan="2">SI</td><td colspan="2">TimesNet</td><td colspan="2">TS2Vec</td><td colspan="2">SimMTM</td><td colspan="2">UP2ME(IR)</td><td colspan="2">UP2ME(FT)</td></tr><tr><td colspan="2">Metric</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td><td>mSE</td><td>mAЕ</td></tr><tr><td rowspan="5">ETTml</td><td>0%~12.5%</td><td>0.090</td><td>0.186</td><td>0.286</td><td>0.385</td><td>0.606</td><td>0.454</td><td>2.138</td><td>1.086</td><td>0.094</td><td>0.201</td><td>0.142</td><td>0.249</td><td>0.262</td><td>0.338</td><td>0.213</td><td>0.277</td><td>0.060</td><td>0.158</td></tr><tr><td>12.5%~25%</td><td>0.131</td><td>0.227</td><td>0.538</td><td>0.534</td><td>0.971</td><td>0.599</td><td>2.072</td><td>1.067</td><td>0.146</td><td>0.250</td><td>0.254</td><td>0.349</td><td>0.323</td><td>0.374</td><td>0.264</td><td>0.311</td><td>0.098</td><td>0.198</td></tr><tr><td>25%~37.5%</td><td>0.236</td><td>0.314</td><td>0.526</td><td>0.518</td><td>1.028</td><td>0.622</td><td>2.015</td><td>1.051</td><td>0.194</td><td>0.288</td><td>0.311</td><td>0.384</td><td>0.349</td><td>0.395</td><td>0.295</td><td>0.332</td><td>0.146</td><td>0.239</td></tr><tr><td>37.5%~50%</td><td>0.349</td><td>0.385</td><td>0.620</td><td>0.545</td><td>1.042</td><td>0.631</td><td>1.959</td><td>1.036</td><td>0.256</td><td>0.327</td><td>0.393</td><td>0.432</td><td>0.377</td><td>0.414</td><td>0.328</td><td>0.352</td><td>0.209</td><td>0.288</td></tr><tr><td>Avg</td><td>0.201</td><td>0.278</td><td>0.492</td><td>0.496</td><td>0.912</td><td>0.577</td><td>2.046</td><td>1.060</td><td>0.172</td><td>0.266</td><td>0.275</td><td>0.353</td><td>0.328</td><td>0.380</td><td>0.275</td><td>0.318</td><td>0.128</td><td>0.221</td></tr><tr><td rowspan="5">Weather</td><td>0%~12.5%</td><td>0.067</td><td>0.115</td><td>0.243</td><td>0.322</td><td>0.111</td><td>0.124</td><td>1.043</td><td>0.750</td><td>0.085</td><td>0.141</td><td>0.082</td><td>0.147</td><td>0.127</td><td>0.184</td><td>0.102</td><td>0.135</td><td>0.055</td><td>0.081</td></tr><tr><td>12.5%~25%</td><td>0.094</td><td>0.151</td><td>0.224</td><td>0.306</td><td>0.178</td><td>0.199</td><td>1.026</td><td>0.744</td><td>0.093</td><td>0.142</td><td>0.110</td><td>0.186</td><td>0.142</td><td>0.197</td><td>0.136</td><td>0.180</td><td>0.067</td><td>0.093</td></tr><tr><td>25%~37.5%</td><td>0.116</td><td>0.180</td><td>0.157</td><td>0.239</td><td>0.198</td><td>0.222</td><td>1.006</td><td>0.738</td><td>0.121</td><td>0.174</td><td>0.139</td><td>0.221</td><td>0.168</td><td>0.224</td><td>0.165</td><td>0.211</td><td>0.086</td><td>0.116</td></tr><tr><td>37.5%~50%</td><td>0.134</td><td>0.194</td><td>0.304</td><td>0.359</td><td>0.228</td><td>0.248</td><td>0.989</td><td>0.732</td><td>0.154</td><td>0.206</td><td>0.168</td><td>0.249</td><td>0.248</td><td>0.304</td><td>0.195</td><td>0.238</td><td>0.108</td><td>0.141</td></tr><tr><td>Avg</td><td>0.103</td><td>0.160</td><td>0.232</td><td>0.306</td><td>0.179</td><td>0.198</td><td>1.016</td><td>0.741</td><td>0.113</td><td>0.166</td><td>0.125</td><td>0.201</td><td>0.171</td><td>0.228</td><td>0.150</td><td>0.191</td><td>0.079</td><td>0.108</td></tr><tr><td rowspan="5">Electricity</td><td>0%~12.5%</td><td>0.206</td><td>0.317</td><td>0.320</td><td>0.413</td><td>1.230</td><td>0.832</td><td>1.896</td><td>1.101</td><td>0.134</td><td>0.252</td><td>0.224</td><td>0.324</td><td rowspan="4" colspan="2">OOM</td><td>0.085</td><td>0.181</td><td>0.080</td><td>0.174</td></tr><tr><td>12.5%~25%</td><td>0.208</td><td>0.316</td><td>0.263</td><td>0.368</td><td>1.285</td><td>0.864</td><td>1.805</td><td>1.072</td><td>0.136</td><td>0.253</td><td>0.223</td><td>0.321</td><td>0.102</td><td>0.199</td><td>0.091</td><td>0.187</td></tr><tr><td>25%~37.5%</td><td>0.212</td><td>0.318</td><td>0.179</td><td>0.292</td><td>1.298</td><td>0.872</td><td>1.713</td><td>1.044</td><td>0.141</td><td>0.257</td><td>0.227</td><td>0.322</td><td>0.114</td><td>0.211</td><td>0.102</td><td>0.199</td></tr><tr><td>37.5%~50%</td><td>0.220</td><td>0.324</td><td>0.493</td><td>0.524</td><td>1.294</td><td>0.872</td><td>1.622</td><td>1.017</td><td>0.149</td><td>0.265</td><td>0.235</td><td>0.328</td><td>0.128</td><td>0.224</td><td>0.114</td><td>0.211</td></tr><tr><td>Avg</td><td>0.211</td><td>0.319</td><td>0.313</td><td>0.399</td><td>1.277</td><td>0.860</td><td>1.759</td><td>1.058</td><td>0.140</td><td>0.256</td><td>0.227</td><td>0.324</td><td colspan="2">OOM</td><td>0.107</td><td>0.204</td><td>0.097</td><td>0.193</td></tr><tr><td rowspan="5">Traffic</td><td>0%~12.5%</td><td>0.565</td><td>0.309</td><td>0.482</td><td>0.275</td><td>2.183</td><td>0.974</td><td>2.888</td><td>1.140</td><td>0.492</td><td>0.271</td><td>0.553</td><td>0.300</td><td rowspan="4" colspan="2">OOM</td><td>0.307</td><td>0.209</td><td>0.228</td><td>0.173</td></tr><tr><td>12.5%~25%</td><td>0.567</td><td>0.307</td><td>0.499</td><td>0.282</td><td>2.276</td><td>1.000</td><td>2.759</td><td>1.109</td><td>0.505</td><td>0.273</td><td>0.551</td><td>0.296</td><td>0.334</td><td>0.221</td><td>0.274</td><td>0.189</td></tr><tr><td>25%~37.5%</td><td>0.573</td><td>0.310</td><td>0.504</td><td>0.290</td><td>2.287</td><td>1.004</td><td>2.631</td><td>1.076</td><td>0.513</td><td>0.277</td><td>0.558</td><td>0.297</td><td>0.346</td><td>0.227</td><td>0.315</td><td>0.206</td></tr><tr><td>37.5%~50%</td><td>0.586</td><td>0.317</td><td>0.551</td><td>0.319</td><td>2.269</td><td>1.000</td><td>2.504</td><td>1.044</td><td>0.521</td><td>0.283</td><td>0.572</td><td>0.301</td><td>0.366</td><td>0.237</td><td>0.358</td><td>0.219</td></tr><tr><td>Avg</td><td>0.573</td><td>0.311</td><td>0.509</td><td>0.291</td><td>2.253</td><td>0.994</td><td>2.696</td><td>1.092</td><td>0.508</td><td>0.276</td><td>0.559</td><td>0.299</td><td colspan="2">OOM</td><td>0.338</td><td>0.223</td><td>0.294</td><td>0.197</td></tr><tr><td rowspan="5">SMD</td><td>0%~12.5%</td><td>0.790</td><td>0.167</td><td>1.038</td><td>0.281</td><td>1.194</td><td>0.138</td><td>3.328</td><td>0.878</td><td>0.845</td><td>0.155</td><td>1.147</td><td>0.331</td><td>0.812</td><td>0.127</td><td>0.694</td><td>0.120</td><td>0.729</td><td>0.083</td></tr><tr><td>12.5%~25%</td><td>0.850</td><td>0.207</td><td>1.252</td><td>0.426</td><td>1.270</td><td>0.157</td><td>3.226</td><td>0.873</td><td>0.844</td><td>0.164</td><td>1.183</td><td>0.360</td><td>0.828</td><td>0.151</td><td>0.864</td><td>0.150</td><td>0.733</td><td>0.092</td></tr><tr><td>25%~37.5%</td><td>0.893</td><td>0.221</td><td>1.366</td><td>0.463</td><td>1.372</td><td>0.174</td><td>3.180</td><td>0.868</td><td>0.884</td><td>0.184</td><td>1.241</td><td>0.386</td><td>0.847</td><td>0.163</td><td>0.877</td><td>0.182</td><td>0.768</td><td>0.111</td></tr><tr><td>37.5%~50%</td><td>0.928</td><td>0.234</td><td>0.938</td><td>0.215</td><td>1.319</td><td>0.199</td><td>3.127</td><td>0.864</td><td>0.934</td><td>0.210</td><td>1.296</td><td>0.412</td><td>0.882</td><td>0.179</td><td>0.921</td><td>0.212</td><td>0.796</td><td>0.128</td></tr><tr><td>Avg</td><td>0.865</td><td>0.207</td><td>1.148</td><td>0.346</td><td>1.289</td><td>0.167</td><td>3.215</td><td>0.870</td><td>0.877</td><td>0.178</td><td>1.217</td><td>0.372</td><td>0.842</td><td>0.155</td><td>0.839</td><td>0.166</td><td>0.756</td><td>0.103</td></tr><tr><td rowspan="5">PSM</td><td>0%~12.5%</td><td>0.543</td><td>0.419</td><td>0.422</td><td>0.308</td><td>0.171</td><td>0.210</td><td>3.083</td><td>1.147</td><td>0.255</td><td>0.298</td><td>1.463</td><td>0.716</td><td>0.152</td><td>0.215</td><td>0.171</td><td>0.220</td><td>0.103</td><td>0.164</td></tr><tr><td>12.5%~25%</td><td>0.568</td><td>0.432</td><td>0.493</td><td>0.351</td><td>0.210</td><td>0.244</td><td>3.043</td><td>1.136</td><td>0.276</td><td>0.313</td><td>1.481</td><td>0.725</td><td>0.203</td><td>0.255</td><td>0.279</td><td>0.305</td><td>0.116</td><td>0.173</td></tr><tr><td>25%~37.5%</td><td>0.615</td><td>0.458</td><td>1.656</td><td>0.818</td><td>0.257</td><td>0.273</td><td>3.001</td><td>1.126</td><td>0.312</td><td>0.337</td><td>1.507</td><td>0.738</td><td>0.254</td><td>0.290</td><td>0.405</td><td>0.380</td><td>0.155</td><td>0.208</td></tr><tr><td>37.5%~50%</td><td>0.677</td><td>0.490</td><td>0.712</td><td>0.469</td><td>0.290</td><td>0.301</td><td>2.975</td><td>1.119</td><td>0.365</td><td>0.371</td><td>1.536</td><td>0.753</td><td>0.293</td><td>0.318</td><td>0.504</td><td>0.433</td><td>0.205</td><td>0.245</td></tr><tr><td>Avg</td><td>0.601</td><td>0.450</td><td>0.821</td><td>0.486</td><td>0.232</td><td>0.257</td><td>3.026</td><td>1.132</td><td>0.302</td><td>0.330</td><td>1.497</td><td>0.733</td><td>0.225</td><td>0.269</td><td>0.340</td><td>0.334</td><td>0.144</td><td>0.197</td></tr><tr><td rowspan="5">SWaT</td><td>0%~12.5%</td><td>2.660</td><td>0.694</td><td>4.981</td><td>0.773</td><td>0.105</td><td>0.031</td><td>13.606</td><td>1.569</td><td>0.191</td><td>0.091</td><td>6.313</td><td>1.386</td><td>0.083</td><td>0.048</td><td>0.086</td><td>0.035</td><td>0.065</td><td>0.031</td></tr><tr><td>12.5%~25%</td><td>2.750</td><td>0.714</td><td>6.088</td><td>0.873</td><td>0.172</td><td>0.049</td><td>13.592</td><td>1.566</td><td>0.218</td><td>0.095</td><td>6.146</td><td>1.263</td><td>0.139</td><td>0.061</td><td>0.167</td><td>0.056</td><td>0.109</td><td>0.041</td></tr><tr><td>25%~37.5%</td><td>2.975</td><td>0.764</td><td>6.615</td><td>0.916</td><td>0.217</td><td>0.064</td><td>13.571</td><td>1.563</td><td>0.255</td><td>0.106</td><td>6.112</td><td>1.227</td><td>0.185</td><td>0.073</td><td>0.228</td><td>0.074</td><td>0.141</td><td>0.048</td></tr><tr><td>37.5%~50%</td><td>3.332</td><td>0.845</td><td>6.876</td><td>0.927</td><td>0.249</td><td>0.074</td><td>13.545</td><td>1.559</td><td>0.298</td><td>0.116</td><td>5.794</td><td>1.152</td><td>0.215</td><td>0.081</td><td>0.287</td><td>0.094</td><td>0.171</td><td>0.059</td></tr><tr><td>Avg</td><td>2.929</td><td>0.754</td><td>6.140</td><td>0.872</td><td>0.186</td><td>0.055</td><td>13.579</td><td>1.564</td><td>0.240</td><td>0.102</td><td>6.091</td><td>1.257</td><td>0.155</td><td>0.066</td><td>0.192</td><td>0.064</td><td>0.121</td><td>0.045</td></tr><tr><td rowspan="5">GECCO</td><td>0%~12.5%</td><td>3.564</td><td>1.088</td><td>5.954</td><td>1.369</td><td>1.132</td><td>0.173</td><td>11.913</td><td>2.077</td><td>1.761</td><td>0.398</td><td>6.101</td><td>1.397</td><td>1.453</td><td>0.275</td><td>1.136</td><td>0.196</td><td>1.438</td><td>0.256</td></tr><tr><td>12.5%~25%</td><td>4.107</td><td>1.217</td><td>5.618</td><td>1.329</td><td>1.670</td><td>0.235</td><td>11.750</td><td>2.071</td><td>1.692</td><td>0.406</td><td>6.057</td><td>1.430</td><td>1.395</td><td>0.294</td><td>1.055</td><td>0.282</td><td>1.321</td><td>0.266</td></tr><tr><td>25%~37.5%</td><td>3.765</td><td>1.119</td><td>4.548</td><td>1.155</td><td>1.767</td><td>0.277</td><td>11.609</td><td>2.045</td><td>1.825</td><td>0.418</td><td>6.072</td><td>1.393</td><td>1.597</td><td>0.331</td><td>1.735</td><td>0.343</td><td>1.524</td><td>0.301</td></tr><tr><td>37.5%~50%</td><td>3.875</td><td>1.142</td><td>4.246</td><td>1.010</td><td>1.969</td><td>0.313</td><td>11.608</td><td>2.061</td><td>1.835</td><td>0.427</td><td>6.029</td><td>1.385</td><td>1.616</td><td>0.356</td><td>1.693</td><td>0.375</td><td>1.590</td><td>0.339</td></tr><tr><td>Avg</td><td>3.828</td><td>1.142</td><td>5.091</td><td>1.216</td><td>1.634</td><td>0.250</td><td>11.720</td><td>2.063</td><td>1.778</td><td>0.412</td><td>6.065</td><td>1.401</td><td>1.515</td><td>0.314</td><td>1.405</td><td>0.299</td><td>1.468</td><td>0.290</td></tr></table>

Table 7: Precision (P), Recall (R), F1-score, Average Precision (AP) evaluation of anomaly detection. Bold/underline indicates the best/second. Our method is marked in gray.

<table><tr><td rowspan="2" colspan="2">Methods</td><td colspan="4">Task-Specific</td><td>General</td><td colspan="4">Pre-Training</td></tr><tr><td>DCdetector</td><td>AnomalyTrans</td><td>iForest</td><td>OCSVM</td><td>TimesNet</td><td>TS2Vec</td><td>SimMTM</td><td>UP2ME(IR)</td><td>UP2ME(FT)</td></tr><tr><td rowspan="4">SMD</td><td>P</td><td>87.21</td><td>88.21</td><td>38.80</td><td>87.87</td><td>80.71</td><td>65.12</td><td>80.61</td><td>80.22</td><td>82.85</td></tr><tr><td>R</td><td>79.49</td><td>93.92</td><td>93.94</td><td>54.44</td><td>85.63</td><td>86.02</td><td>85.56</td><td>85.32</td><td>83.78</td></tr><tr><td>F1</td><td>84.40</td><td>90.98</td><td>54.92</td><td>67.23</td><td>83.09</td><td>74.13</td><td>83.01</td><td>82.69</td><td>83.31</td></tr><tr><td>AP</td><td>82.75</td><td>93.49</td><td>80.65</td><td>73.42</td><td>90.59</td><td>87.79</td><td>93.91</td><td>93.90</td><td>93.58</td></tr><tr><td rowspan="4">PSM</td><td>P</td><td>97.21</td><td>97.32</td><td>96.22</td><td>99.00</td><td>99.16</td><td>84.82</td><td>99.27</td><td>98.94</td><td>99.02</td></tr><tr><td>R</td><td>97.79</td><td>97.41</td><td>86.00</td><td>76.85</td><td>83.28</td><td>90.24</td><td>88.14</td><td>93.33</td><td>95.38</td></tr><tr><td>F1</td><td>97.50</td><td>97.37</td><td>90.82</td><td>86.53</td><td>90.53</td><td>87.44</td><td>93.37</td><td>96.05</td><td>97.16</td></tr><tr><td>AP</td><td>98.73</td><td>98.80</td><td>96.61</td><td>96.86</td><td>99.70</td><td>96.48</td><td>99.73</td><td>99.75</td><td>99.76</td></tr><tr><td rowspan="4">SWaT</td><td>P</td><td>93.28</td><td>90.49</td><td>23.20</td><td>47.63</td><td>89.12</td><td>15.27</td><td>91.18</td><td>92.06</td><td>91.98</td></tr><tr><td>R</td><td>100.00</td><td>100.00</td><td>95.86</td><td>87.18</td><td>92.60</td><td>92.42</td><td>87.47</td><td>93.74</td><td>95.81</td></tr><tr><td>F1</td><td>96.52</td><td>95.01</td><td>37.36</td><td>61.61</td><td>90.83</td><td>26.20</td><td>89.29</td><td>92.89</td><td>93.85</td></tr><tr><td>AP</td><td>99.57</td><td>98.92</td><td>91.46</td><td>88.55</td><td>97.37</td><td>82.12</td><td>97.38</td><td>97.83</td><td>98.07</td></tr><tr><td rowspan="4">GECCO</td><td>P</td><td>22.40</td><td>24.92</td><td>20.09</td><td>93.33</td><td>52.44</td><td>10.73</td><td>72.19</td><td>41.67</td><td>50.57</td></tr><tr><td>R</td><td>54.25</td><td>55.75</td><td>38.36</td><td>36.44</td><td>41.68</td><td>38.36</td><td>35.20</td><td>84.93</td><td>84.93</td></tr><tr><td>F1</td><td>31.71</td><td>34.45</td><td>26.37</td><td>52.41</td><td>46.45</td><td>16.77</td><td>47.32</td><td>55.91</td><td>63.39</td></tr><tr><td>AP</td><td>31.87</td><td>48.54</td><td>38.92</td><td>62.08</td><td>68.53</td><td>37.76</td><td>63.30</td><td>65.47</td><td>65.09</td></tr></table>

## C. Additional Experiments about Computational Overhead

Ablation of Channel Decoupling in Pre-training. Figure 5 shows the memory occupancy and time cost of pre-training with and without channel decoupling against the number of channels C. We can see that without channel decoupling, both memory occupancy and time cost increase linearly w.r.t $C$ and the pre-training process encounters the out-of-memory (OOM) problem on one NVIDIA Quadro RTX 8000 GPU with 48GB memory when $C > 3 0 0$ , even with a small batch size 8. Incontrast, with channel decoupling, the memory occupancy and time cost are irrelative to C, enabling UP2ME to scale effectively to high-dimensional datasets, such as Electricity $( C = 3 2 1 )$ and Traffic $( C = 8 6 2 )$

![](images/94ec97b098be8546993a67bf6cc46d5b7fb5bffd1f3885611625a408f4e228b5.jpg)  
(a)

![](images/2db48a8ebc763203d5799e88beea9307e7cc0ff98b6e6c58bf4bc92a4a82e574.jpg)  
(b)  
Figure 5: Efficieny evaluation of channel decoupling in pre-training. (a) Pre-training memory occupancy with and without channel decoupling against the number of channels C on synthetic datasets with different numbers of channels. (b) Pretraining time cost with and without channel decoupling against the number of channels. Experiments are conducted on a single NVIDIA Quadro RTX 8000 GPU with 48GB memory. The batch size is set to 256 for channel decoupling and 8 for without channel decoupling. The x-axis is in the log scale.

Hyper-parameter r in Graph Construction of Fine-tuning. Figure 6 illustrates the memory occupancy of fine-tuning against hyper-parameter r in graph construction. The memory occupancy increases rapidly when $r > 1 0$ , reaching the OOM scenario when $r > 2 0 .$ . This underscores the challenge of employing fully connected graphs for high-dimensional datasets and emphasizes the necessity of our sparse graph construction.

![](images/c5c9a6a4f47b29750ed92a96a4c7b6625256c9b5b9c98a47c4ce5003434c2d2d.jpg)  
Figure 6: Fine-tuning memory occupancy against hyper-parameter r in graph construction on Electricity $( C = 3 2 1 )$ ).

## D. Visualization

## D.1. Mask-Reconstruction

Figure 7 shows some mask-reconstruction cases using UP2ME. The pre-trained UP2ME can leverage complex temporal dependency to reconstruct time series of different lengths from different channels.

![](images/76d9c530285942e4ecdbd1604c41c49ae9e6fae1b0ad2877fe882a8cf5ded029.jpg)

![](images/b7b9a5802d18b806e3d38e2831eaec81beb5c0d3d03a3b55f136ac48f11e9b39.jpg)

![](images/23b6985d93779c8e576024b9459941a5e42e91a8972f075dab5111232a5c1721.jpg)

![](images/e5f5fdfe0653e8d974b6aa0b1c390cb0841b90296302c103b45bd4b195557753.jpg)

![](images/88d05a122b2152b45e98301ec882783a1dcf32c6cd9fc6dfb7208cdba73177db.jpg)

![](images/6fb2748d2f9e1a467c7268a1311e4827f47b64bc4df5fa85352f21ef7dded906.jpg)

![](images/b1f8d2748d6baa64c546a62f1bf17de4e1ed8f42257d07ccb749ba3f6b2bd53c.jpg)

![](images/4e6470365dd9f6323e02380e6a1b44b567ae0fd4c9faa3e0ec40f43b5ca762d2.jpg)

![](images/0db330adc22ad90ca6cf772649cdaf0a8468c5def74fecf6ba45a907ffbd2486.jpg)

![](images/561ec907637173d5a3bfc5f358a0d4a06066a9d1348018abe3921d66021046ba.jpg)

![](images/7b2fcf81cdf29193b7a6d123d159ab822e217b529c5277aa6baea29924edd368.jpg)

![](images/7bb2f53ab2f41c5759256130d3322f22f8c8ef7f4edd5b247e90e8457e17c4b8.jpg)

![](images/0e97b9513b7258869147f83ef31392f5059c3adf45c6e026ae2ea551cd2be844.jpg)  
Figure 7: Mask-reconstruction cases using UP2ME. Every two rows represent the same dataset. The orange/red/blue curves stand for the unmasked/masked/reconstructed series. Cases of different channels with different lengths on the same dataset are generated by the same pre-trained model.

## D.2. Forecasting

Figure 8 shows the forecasting cases of three channels in the ETTm1 dataset. For channels #1 and #2, all methods successfully predict the periodic pattern. For channel #7, PatchTST, TimesNet and SimMTM fail to predict the additional increasing trend. And predictions of our UP2ME(IR) and UP2ME(FT) are closer to the ground truth compared with DLinear.

![](images/98d40b43eba74696b43c8db1c5b0d7b7d50fd9f1522da2fe6498cf7ac9ebbddc.jpg)

![](images/5f65554b34ad5c8cc21180c5c2f3ce484a74bfcf652143ee52c24e32f3fbdd2b.jpg)

![](images/6e3ead9bb152d64d7fa42952014d0729fa919c9e52691ee209b30a5888c2a70c.jpg)

![](images/2f686100b94919ca57b7ed6a611b4633593aa59d286105ef9ae78c16a4692079.jpg)

![](images/c950b06b8b64c036b71d9ccf3407285448f6becc2d1f8d927cd402cb6c056b59.jpg)

![](images/6ce67e3dac060babd38670e4e578f47a646bd3c4b1671143e5be27a41add0076.jpg)

![](images/7d5252e806bfd2fdcf49abd74179fc7358dab0e66f2e0a8a73efc17f7a555e77.jpg)

![](images/3b2e6cf40fc06a96aa1f5207c48feb6c008856f3c0fe814d8411ad8428d8a6e7.jpg)

![](images/1249981ea04b038b03e91053529db8eae9daa51e2b85e7d045e4007947c27b26.jpg)

![](images/4d588163f9256d17f90fbb6c46d89c9838734daca0d2f4b4697e2b20d134150b.jpg)

![](images/afe83afc0e8bbc3225a6424e2ba86db5902b5880e4f4545b7d3dfddeba5b866f.jpg)

![](images/d3391c208bdd5170f9ac85a355416de7075b8cd70722ed7e23653a5ecf653d9e.jpg)

![](images/3bdd1d090cf9aa4d43c3875fbd558f42f2e238c44db0ed84208047ef073a3a35.jpg)

![](images/03b610a934a66bf5435f9b236cb0f488a853ae9e5bc768753b85441e7597b7b9.jpg)

![](images/c7f746b015c6377dfc1d3b0402eb6f53e9e34f8e0ad8933777b01482a668fc35.jpg)

![](images/4f6cd7e44f52d639231e16da60f518fd2a2041453e61edc76bec0726f7654a87.jpg)  
(a) Channel #1

![](images/198f3251d991bd1258d2436feda6c611bcf548abe39d939d3edb2958b8b91a73.jpg)  
(b) Channel #2

![](images/dc39abfeb61f1fe6826a235163774c38d1bf3e73b682c9eb353de9e31755d740.jpg)  
(c) Channel #7  
Figure 8: Forecasting cases for 3 channels in the ETTm1 dataset. The prediction length is set to 336; all methods except TimesNet utilize the past 336 points for forecasting, while TimesNet employs the past 96 points, as experiments indicate its preference for a shorter window for improved results. The orange/red/blue curves represent past/future/predicted time series. Each row corresponds to one method, and each column corresponds to one channel.

## D.3. Imputation

Figure 9 shows the imputation cases of three channels in the Weather dataset. Our UP2ME(IR) rivals the most competitive task-specific models. Additionally, UP2ME(FT) achieves remarkably faithful imputation compared to the ground truth. Moreover, the outputs of our UP2ME are more continuous with less oscillation.

![](images/ffc1be645cb933e9e09b8aeb5cca04f54e8eddc740388c93ac0dbbb54817f8dd.jpg)

![](images/0bd25aaf8cdd64387f6e6e2c7498434d205cef3ba2a4ec774096ce64d2fd7605.jpg)

![](images/c506bf54590115296b69ef095515a73f4a5310589d1b5c9749dd605c64f2bb94.jpg)

![](images/fd203392f405916faea9fcc84192c01ccf3bcfbf128b0a6f31e7f4633f767e02.jpg)

![](images/6c4bd5ea932b3c6d3df77103c6330c7140866ac8b468c79f872c90d7c001f016.jpg)

![](images/34b32982809a3f0b48d05053f6ad1aea11e95caa2f744cd1fbafcebd4c7fb86f.jpg)

![](images/2bb842d35f76b9ba5e21186d6d1747666e7ee599fd87826706b848e0a40a0e8d.jpg)

![](images/e74532eff5cb3150fe965466f5b1c059ea3619299cc3f12d717a86c2e579e27b.jpg)

![](images/71566d8a22721f788f1473d411a1d502f35b637e5e7e5c9abdd498f382baaf7a.jpg)

![](images/63857c04ad0157c1428b81ff410197683ee67834a2a07a9d47fde96ba6e88a17.jpg)

![](images/4db5f674f978b896fb17aadc526f74dd034d0e22cf3400713c07a53e3625e977.jpg)

![](images/a4ea366256af3d04e4908a19067f62db3e6b0de043d5b8f075deb22156b62f6c.jpg)

![](images/e353fc10a8eba3ab5a36407306412e726441d6919407d0d12004e4547b082ac9.jpg)

![](images/d53fdebb04808e02879b352891df88e58f46c2bb51fd015dec4ac30f12d6581d.jpg)

![](images/f111ddba24e1bc7c9acf21ddc0ce954859a301fbc04765db6b098dd568f8b0eb.jpg)

![](images/ba9d12d5734aceddce74462d5815d36c0d00ac3016604709c4686bf938c887eb.jpg)  
(a) Channel #7

![](images/e2a96c2c89ebdf89233a74540b4ffab51a0be178f83d0dc4f6bf3743a76b4a2d.jpg)  
(b) Channel #10

![](images/8b819bfaa94d6d3fa75602ffc68139ae9fdfce2104053c60095c619d8442a7ef.jpg)  
(c) Channel #16  
Figure 9: Imputation cases for 3 channels in the Weather dataset. The observed window length is set to 600, with the missing ratio of $1 2 . 5 \% \sim 2 5 \%$ . The orange/red/blue curves represent observed/ground-truth/imputed series. Each row corresponds to one method, and each column corresponds to one channel.

Input  
![](images/3ec5df55469c284a2165a3fe783028901f64b15de79be724e94ef13ee6a43162.jpg)  
Figure 10: Anomaly detection cases on the GECCO dataset. The first three rows illustrate three channels of the input instance, with each row corresponding to one channel. Input values are repeated three times along the column axis to align with the anomaly scores below for better visualization. Ground truth anomaly timestamps are highlighted in red. The last two rows display anomaly scores generated by different methods.

## D.4. Anomaly Detection

Figure 10 illustrates anomaly detection cases on the GECCO dataset. While DCdetector fails to identify the abnorma segment, AnomalyTrans detects two points within the segment. TimesNet, SimMTM, and UP2ME(IR) recognize anomalies at the end of the abnormal segment. After fine-tuning, UP2ME(FT) successfully identifies the entire abnormal segment.