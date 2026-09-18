---
title: "2024-Kim-Gradient-Accumulation-Dense-Retriever-Memory"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/training-efficiency/2024-Kim-Gradient-Accumulation-Dense-Retriever-Memory.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# A Gradient Accumulation Method for Dense Retriever under Memory Constraint

Jaehee Kim<sup>1</sup> Yukyung Lee<sup>2</sup> Pilsung Kang<sup>1∗</sup> <sup>1</sup>Seoul National University <sup>2</sup>Boston University {jaehee\_kim, pilsung\_kang}@snu.ac.kr ylee5@bu.edu

## Abstract

InfoNCE loss is commonly used to train dense retriever in information retrieval tasks. It is well known that a large batch is essential to stable and effective training with InfoNCE loss, which requires significant hardware resources. Due to the dependency of large batch, dense retriever has bottleneck of application and research. Recently, memory reduction methods have been broadly adopted to resolve the hardware bottleneck by decomposing forward and backward or using a memory bank. However, current methods still suffer from slow and unstable training. To address these issues, we propose Contrastive Accumulation (CONTACCUM), a stable and efficient memory reduction method for dense retriever trains that uses a dual memory bank structure to leverage previously generated query and passage representations. Experiments on widely used five information retrieval datasets indicate that CONTACCUM can surpass not only existing memory reduction methods but also high-resource scenario. Moreover, theoretical analysis and experimental results confirm that CONTACCUM provides more stable dual-encoder training than current memory bank utilization methods.

## 1 Introduction

Dense retriever aims to retrieve relevant passages from a database in response to user queries with neural networks [43]. Karpukhin et al. [16] and Lee et al. [20] introduced the in-batch negative sampling for training dense retriever with InfoNCE loss [36], where relevant passages from other queries in the same batch are utilized as negative passages. This negative sampling strategy has been widely adopted in subsequent dense retriever studies, including supervised retriever [16, 31, 28, 41], retriever pre-training [7, 8, 24, 12, 5], phrase retriever [19, 25], and generative retriever [34, 13]. Training dense retriever with InfoNCE loss drives the representations of queries and relevant passages closer and pushes the representations of unrelated passages apart, which can be seen as a form of metric learning [17].

Many dense retriever methodologies utilize large batch to incorporate more negative samples [41, 7, 28, 12]. Theoretically, it has been demonstrated that more negative samples in InfoNCE loss lead to a tighter lower bound on mutual information between query and passage [36]. Empirical studies have shown that the dense retriever performs better with large batch [28, 43, 42]. However, training with large batches requires high-resource, posing a challenge for dense retriever research and applications.

A line of research has focused on overcoming these limitations by approximating the effects of large batch sizes. Gradient Accumulation (GradAccum), a common method for approximating large batch, reduces memory usage by splitting the large batch into smaller batches. However, GradAccum has limitations in the context of InfoNCE loss because it reduces negative samples per query by the smaller batch [9]. To overcome the limitation of GradAccum, Gao et al. [9] proposed the Gradient Cache (GradCache), which approximates large batch by decomposing the backpropagation process and adapts additional forwarding process for calculating gradients. However, GradCache has limitations, including significant additional training time due to computational overhead and the inability to surpass high-resource scenario where accelerators are sufficient to train large batch. Additionally, pre-batch negatives [19] caches passage representations from previous steps to secure additional negative samples, but it also shows unstable train and marginal performance gain.

In this study, we propose Contrastive Accumulation (CONTACCUM), which demonstrates high performance and stable training under memory constraints. CONTACCUM leverages previously generated query and passage representations through a memory bank, enabling the use of more negative samples. Our analysis of the gradients reveals that utilizing a memory bank for both query and passage leads to stable training. The specific contributions of this study are as follows:

• We propose CONTACCUM, a method utilizing a dual memory bank strategy that can outperform not only existing memory reduction methods but also high-resource scenario in low-resource setting.

• We show that our method is time efficient, reducing the training time compared to existing memory reduction methods.

• We demonstrate the cause of training instability in existing memory bank utilization methods through mathematical analysis and experiments, showing that the dual memory bank strategy stabilizes training.

## 2 Related works

![](images/f1720bf6496b46c5492482c05221cdcae5ba17bf471607d008083b264a3be542.jpg)  
Figure 1: Illustrations of CONTACCUM and Comparative Methods. The illustrations show a total batch size $( N _ { \mathrm { t o t a l } } )$ of 4, a local batch size $( N _ { \mathrm { l o c a l } } )$ of 2, and a memory bank size $( N _ { \mathrm { m e m o r y } } )$ of 4. (a) GradCache uses $N _ { \mathrm { t o t a l } } - 1$ negative passages. (b) GradAccum uses $N _ { \mathrm { l o c a l } } - 1$ negative passages. (c) CONTACCUM leverages $N _ { \mathrm { l o c a l } } + N _ { \mathrm { m e m o r y } } - 1$ negative samples, more than $N _ { \mathrm { t o t a l } } - 1$

## 2.1 Memory reduction in information retrieval

GradAccum is the most common method to address memory reduction problem. By using GradAccum, gradients of the total batch can be stored by sequentially processing local batches through forward and backward passes, even when the total batch cannot be processed at once. However, as shown in Figure 1 (b), GradAccum is not a proper memory reduction method for the in-batch negatives, as it uses fewer negative samples than the total batch. We will discuss the limitation of GradAccum for contrastive learning in detail in subsection 3.1.

GradCache reduces memory usage in contrastive learning by decomposing the backpropagation process. Specifically, as shown in Figure 1 (a), it calculates the loss without storing activations during the forward pass using the total batch. Then, it computes and stores the gradient from the loss to the representations. Next, it performs additional forward passes for the local batch to store activations and sequentially calculates gradients from each representation to the model weights. This allows GradCache to use the same number of negative samples as the total batch, approximating the performance of the total batch. However, GradCache cannot surpass the performance of high-resource scenario because it uses the same number of negative samples. Also, GradCache requires a significant amount of time due to the complex forward and backward processes.

## 2.2 Memory bank

The memory bank structure for metric learning was initially proposed for the vision domain, where it stores representations generated by the encoder in previous batches [40, 39]. Combined with the NCE loss [10], memory bank structures have been widely used to train uni-encoder vision models [11, 3, 38]. However, directly adapting this approach to information retrieval tasks, where a dual-encoder structure is commonly used, is challenging. This is due to several factors: In multi-modal settings, Li et al. [22, 21] have employed momentum encoders for both image and text modalities to generate cached representations. However, these approaches do not directly address the asymmetric nature of information retrieval, where the goal is to retrieve relevant passages for a given query rather than retrieving relevant queries for a given passage.

In the information retrieval task, Izacard et al. [12] proposed caching representations generated by a momentum encoder [11], but they only consider the uni-encoder setting. Lee et al. [19] introduced pre-batch negatives that extend the number of negative samples by caching passage representations with a memory bank in a dual-encoder setting. However, pre-batch negatives was applied only in the final few epochs of the training process due to the rapid changes in encoder representations early in training, which can cause instability when using a memory bank [38, 37].

In summary, existing dense retrievers depend on in-batch negative sampling, necessitating large batch sizes and costly hardware settings. While memory reduction methods have been studied to address this, they often result in slower training or unstable training. Therefore, we propose CONTACCUM, a memory reduction method designed to ensure fast and stable training of dense retrievers.

## 3 Proposed Method

## 3.1 Preliminary: InfoNCE loss with GradAccum

Before introducing our method, we first examine GradAccum with InfoNCE loss. Karpukhin et al. [16] proposed training method for dense retriever using InfoNCE loss. With a batch size $N$ , dense retrievers are trained by minimizing the negative log-likelihood over all query representations $( \mathbf { Q } )$ and passage representations. Specifically, they utilized in-batch negative sampling (P) in the same batch for efficiency, encoded by the query and passage encoders as:

$$
\mathcal {L} (S) = - \frac {1}{N} \sum_ {i} ^ {N} \log \frac {\exp \left(S _ {(i , i)} / \tau\right)}{\sum_ {j} ^ {N} \exp \left(S _ {(i , j)} / \tau\right)}, \quad \text { where } S = \operatorname{Softmax} (\mathbf {Q} \cdot \mathbf {P} ^ {\top}) \in \mathbb {R} ^ {N \times N}\tag{1}
$$

The in-batch negative sampling efficiently obtains $N - 1$ negative passages per query from relevant passages of other queries, as shown in Equation 1. Consequently, the number of negative passages increases with a larger batch size. Due to this characteristic of in-batch negative sampling, dense retriever is trained using extremely large batch size, ranging from 128 to 8192 [16, 12, 28, 5, 29]. However, the need to process all data in memory simultaneously requires multiple high-cost accelerators, ranging from 8 [16, 28] to 32 [12]. This creates a hardware bottleneck that constrains various research and applications.

In low-resource setting, GradAccum is employed to train models with the total batch size $( N _ { \mathrm { t o t a l } } )$ which cannot be fitted in the limited memory. GradAccum decomposes the total batch into accumulation steps, $K ,$ , and processes the local batch, $N _ { \mathrm { l o c a l } } ~ = ~ N _ { \mathrm { t o t a l } } / K$ , through forward and backpropagation K times to calculate gradients. The process of computing InfoNCE Loss with GradAccum is as follows.

First, the query, $q ,$ and document, $p ,$ are encoded by the query encoder, $f _ { \Theta } ^ { t }$ , and passage encoder, $g _ { \Lambda } ^ { t }$ at training step t respectively:

$$
\mathbf {q} ^ {t} = f _ {\Theta} ^ {t} (q) \in \mathbb {R} ^ {d _ {\text { model }}}, \quad \mathbf {p} ^ {t} = g _ {\Lambda} ^ {t} (p) \in \mathbb {R} ^ {d _ {\text { model }}}\tag{2}
$$

where $d _ { \mathrm { m o d e l } }$ denotes the dimension of query and passage representation. The query encoder, $f ,$ and passage encoder, g, are parameterized by Θ and $\Lambda$ respectively. The query and passage representations within the same local batch at the k-th accumulation step are given as follows:

$$
\mathbf {Q} _ {k} ^ {t} = \left\{\mathbf {q} _ {1} ^ {t}, \dots , \mathbf {q} _ {N _ {\text {local}}} ^ {t} \right\} \in \mathbb {R} ^ {N _ {\text {local}} \times d _ {\text {model}}}, \quad \mathbf {P} _ {k} ^ {t} = \left\{\mathbf {p} _ {1} ^ {t}, \dots , \mathbf {p} _ {N _ {\text {local}}} ^ {t} \right\} \in \mathbb {R} ^ {N _ {\text {local}} \times d _ {\text {model}}}\tag{3}
$$

![](images/913992fd19bbfbd44798e6268b1f3c402dc2f1bb9fadaaffc2d0e8b5d7da7240.jpg)  
Figure 2: Training process of CONTACCUM at each accumulation step. The illustration shows a total batch size $( \bar { N _ { \mathrm { t o t a l } } } )$ of 4, an accumulation step (K) of 2, and a memory bank size $( N _ { \mathrm { m e m o r y } } )$ of 4. The dual memory bank caches both query and passage representations. New representations are enqueued, and the oldest are dequeued at each step, maintaining the similarity matrix $( S _ { k } )$ size at $( N _ { \mathrm { l o c a l } } + N _ { \mathrm { m e m o r y } } , N _ { \mathrm { l o c a l } } + N _ { \mathrm { m e m o r y } } )$

Using Equation 1, the loss for the k-th accumulation step is calculated, and the loss for the total batch used for one weight update is obtained as shown in Equation 4:

$$
\mathcal {L} = \frac {1}{K} \sum_ {k = 1} ^ {K} \mathcal {L} (S _ {k}), \quad \text { where } S _ {k} = \operatorname{Softmax} (\mathbf {Q} _ {k} ^ {t} \cdot (\mathbf {P} _ {k} ^ {t}) ^ {\top}) \in \mathbb {R} ^ {N _ {\mathrm{local}} \times N _ {\mathrm{local}}}\tag{4}
$$

In Equation 4, the number of negative passages in each accumulation step is $N _ { \mathrm { l o c a l } } - 1$ , which is fewer than the number of negative passages when using the total batch, $N _ { \mathrm { t o t a l } } - 1$ . This reduction in the number of negative samples results from that GradAccum use $N _ { \mathrm { l o c a l } }$ passages in a single forward pass. Consequently, GradAccum cannot maintain the number of negative passages in low-resource setting, while the total amount of data used for weight updates is the same as the total batch.

## 3.2 CONTACCUM

To address the issue of fewer negative passages being used with GradAccum, we propose CONTACCUM, a method that utilizes a dual memory bank structure to cache representations for both queries and passages. The query and passage memory banks $( M _ { \mathbf { q } } , M _ { \mathbf { p } } )$ are implemented as First-In-First-Out queues storing $\mathbf { \dot { \Lambda } } _ { \mathrm { { m e m o r y } } } ^ { \mathbf { q } }$ and $N _ { \mathrm { m e m o r y } } ^ { \mathbf { p } }$ representations respectively. For example, as shown in Figure 2, the oldest representations in the memory bank $( \mathbf { P _ { 1 } ^ { t - 1 } } , \mathbf { Q _ { 1 } ^ { t - 1 } } )$ are replaced with the newly-generated ones $( \mathbf { P _ { 1 } ^ { t } } , \dot { \mathbf { Q } } _ { 1 } ^ { \mathbf { t } } )$ . Memory bank strategy is computationally efficient as it reuses generated representations from previous iterations [37, 38, 19]. Unlike Lee et al. [19], which only utilized a passage memory bank $M _ { \mathbf { p } }$ , CONTACCUM employs a dual memory bank by also utilizing a query memory bank $M _ { \mathbf { q } }$

CONTACCUM constructs the similarity matrix using both current and stored representations from the dual memory bank as illustrated in Figure 2. It is equivalent to modifying $S _ { k }$ in Equation 4 as:

$$
\mathbf {Q} = \mathbf {Q} _ {k} ^ {t} \cup \operatorname{sg} (M _ {\mathbf {q}}) \in \mathbb {R} ^ {(N _ {\text { local }} + N _ {\text { memory }} ^ {\mathbf {q}}) \times d _ {\text { model }}}\tag{5}
$$

$$
\mathbf {P} = \mathbf {P} _ {k} ^ {t} \cup \operatorname{sg} (M _ {\mathbf {p}}) \in \mathbb {R} ^ {(N _ {\text {local}} + N _ {\text {memory}} ^ {\mathbf {p}}) \times d _ {\text {model}}}\tag{6}
$$

$$
S _ {k} = \operatorname{Softmax} (\mathbf {Q} \cdot \mathbf {P} ^ {\top})\tag{7}
$$

The backpropagation process using InfoNCE loss proceeds in the same manner as in Equation 4. However, since the representations in the memory bank do not have stored activations by the stop-gradient operation(sg(·)), the gradients are not back-propagated through the representations in the memory bank.

The number of negative passages in CONTACCUM is $N _ { \mathrm { l o c a l } } + N _ { \mathrm { m e m o r y } } ^ { \mathbf { p } } - 1$ , which is greater than GradAccum. Furthermore, if $\bar { N } _ { \mathrm { m e m o r y } } ^ { \mathbf { p } } > N _ { \mathrm { l o c a l } } \times ( K - 1 )$ ), CONTACCUM can utilize more negative passages than the total batch, enabling superior performance in low-resource setting compared to high-resource scenario.

## 3.3 Gradient analysis with dual memory bank

We analyze the InfoNCE loss backpropagation process in information retrieval tasks, extending the analysis by Gao et al. [9] to consider using the memory bank. In the partial derivatives of the loss function with respect to the two encoders, $\begin{array} { r } { \nabla _ { \Theta } \mathcal { L } ( S _ { k } ) = \sum _ { \mathbf { q } _ { l } \in Q _ { k } ^ { t } } \frac { \partial \mathcal { L } ( S _ { k } ) } { \partial \mathbf { q } _ { l } } \cdot \frac { \partial \mathbf { q } _ { l } } { \partial \Theta } , \quad \nabla _ { \Lambda } \mathcal { L } ( S _ { k } ) = } \end{array}$ $\sum _ { \mathbf { p } _ { l } \in P _ { k } ^ { t } } \frac { \partial \mathcal { L } ( S _ { k } ) } { \partial \mathbf { p } _ { l } } \cdot \frac { \partial \mathbf { p } _ { l } } { \partial \Lambda }$ , the partial derivative terms for each representation are given by:

$$
\frac {\partial \mathcal {L} (S _ {k})}{\partial \mathbf {q} _ {l}} = - \frac {1}{N _ {\text { local }} + N _ {\text { memory }} ^ {q}} (\mathbf {p} _ {l} - \sum_ {j} ^ {N _ {\text { local }} + N _ {\text { memory }} ^ {p}} S _ {k (l, j)} \cdot \mathbf {p} _ {j})\tag{8}
$$

$$
\frac {\partial \mathcal {L} (S _ {k})}{\partial \mathbf {p} _ {l}} = - \frac {1}{N _ {\text { local }} + N _ {\text { memory }} ^ {q}} (\mathbf {q} _ {l} - \sum_ {i} ^ {N _ {\text { local }} + N _ {\text { memory }} ^ {q}} S _ {k (i, l)} \cdot \mathbf {q} _ {j}),\tag{9}
$$

where $S _ { k ( i , j ) }$ denotes the similarity between i-th query and $j \cdot$ -th passage in the similarity matrix $S _ { k }$ of the k-th accumulation step. Detailed differentiation steps are provided in Appendix 6.

Equations 8 and 9 have a similar structure, indicating that the gradients of the two encoders are influenced by the representations generated by the opposite encoder. The difference lies in the summation targets, which are determined by the size of the memory banks. The gradient calculation for the query encoder uses $N _ { \mathrm { l o c a l } } + N _ { \mathrm { m e m o r y } } ^ { \mathbf { p } }$ passage representations, while the passage encoder uses $N _ { \mathrm { l o c a l } } + \bar { N } _ { \mathrm { m e m o r y } } ^ { \dot { \mathbf { q } } }$ query representations.

Pre-batch negatives only leverages the passage memory bank where $N _ { \mathrm { { m e m o r y } } } ^ { \mathbf { p } } > N _ { \mathrm { { m e m o r y } } } ^ { \mathbf { q } } = 0$ The tendency where $| | \dot { \nabla _ { \Theta } } \mathcal { L } ( S _ { k } ) \bar { | } | _ { 2 } < | | \dot { \nabla } _ { \Lambda } \mathcal { L } ( \bar { S } _ { k } ) | | _ { 2 }$ is caused by the difference in the number of representations used for the gradient calculations of the two encoders. In dual-encoder training, if the gradient norms of the two encoders remain imbalanced, the encoder with the larger gradient norm converges faster, making balanced training challenging [4, 33]. Therefore, the unstable training with a memory bank is caused not only by rapid changes in encoder representations [37, 38], but also by the difference in the gradient norms between the dual-encoders. We refer to this problem as the gradient norm imbalance problem.

The gradient norm imbalance problem can be resolved by using memory banks of equal size for queries and passages, $N _ { \mathrm { m e m o r y } } ^ { \mathbf { q } } \doteq N _ { \mathrm { m e m o r y } } ^ { \mathbf { p } } = N _ { \mathrm { m e m o r y } }$ . This ensures that the gradient norms of the two encoders remain similar and stabilizes the training process. Further analysis is provided in Sections 5.2 and 5.5.

## 4 Experimental setups

Resources. All experiments were conducted on a single A100 80GB GPU. For high-resource scenario, we considered situations where 80GB of memory is available. For low-resource settings, we assumed available memory as widely used commercial GPUs: 11GB (GTX-1080Ti), 24GB (RTX-3080Ti, RTX-4090Ti). To ensure strict experimental conditions, we used a function from the PyTorch [27] to limit the available memory.<sup>2</sup> Unless otherwise stated, all experiments assumed low resource setting where only 11GB memory is available.

Datasets and evaluation metrics. The datasets used for the experiments were Natural Questions (NQ) [18], TriviaQA [15], Curated TREC (TREC) [1], and Web Questions (WebQ) [2] processed by DPR and MS Marco [26]. For Natural Questions, TriviaQA, Curated TREC, and Web Questions, we used the preprocessed data provided by DPR [16], which includes hard negative samples, positive passages, and answer annotations. Only queries with both positive and hard negative passages were used for training. For MS Marco, we utilized the preprocessed data from BEIR [35] and filtered BM25 [32] hard negatives using cross-encoder scores from the sentence-transformers library [30]. Specifically, we considered passages as hard negatives if their cross-encoder scores were at least 3 points higher than the positive passages’ scores, following the preprocessing pipeline provided by sentence-transformers.

For evaluation metrics, Top@k was used for Natural Questions, TriviaQA, TREC, and WebQ following DPR. Also, we evaluate MS Marco using NDCG@K and Recall@K, widely used metrics for dense retriever. NQ and TriviaQA were evaluated using test sets, while TREC, WebQ, and MS Marco were evaluated using dev sets. Additionally, the entire document set was used for evaluation.

Implementation details. The experimental code was adapted from $\scriptstyle \mathrm { n a n o - D P R } ^ { 3 }$ , which provides a simplified training and evaluation pipeline for DPR. All experiments were conducted using the BERT<sup>4</sup> [6] model. To maintain consistency with DPR’s experimental setup, NQ and TREC were trained for 40 epochs, and TriviaQA and WebQ for 100 epochs. For MS Marco, performance saturated at 10 epochs, so it was trained for 10 epochs. Other training settings were also kept consistent with DPR. Detailed settings are provided in Appendix 6.

The optimal memory bank size, $N _ { \mathrm { { m e m o r y } } } ,$ , was selected using evaluation data with candidates [128, 512, 2048], resulting in 2,048 for NQ and 512 for TriviaQA. For MS Marco, WebQ, and TREC, due to the lack of evaluation data, $N _ { \mathrm { { m e m o r y } } }$ were set based on dataset size: 1,024 for MS Marco, and 128 for WebQ and TREC.

Baselines. We established three baselines for each scenario, and all methods were trained with hard negatives. First, we reported the performance of DPR with the maximum batch size possible for each scenario. Further, we reported the performance of GradAccum with the total batch size of $N _ { \mathrm { t o t a l } } = 1 2 8$ . The local batch size $N _ { \mathrm { l o c a l } }$ varied by the scenario , with $K = N _ { \mathrm { t o t a l } } / N _ { \mathrm { l o c a l } }$ . We also conducted experiments with GradCache [9], known for approximating total batch performance, using the same $N _ { \mathrm { l o c a l } }$ for single forwarding.

## 5 Experimental results

## 5.1 Performance across different resource constraints

Table 1: Performance of different methods in low-resource settings (11GB, 24GB) and high-resource (80GB) setting. In the high-resource setting, the score of the original DPR [16] paper (original) and the reproduced implementation (implemented) are listed. The best score for each training environment is bolded, and scores surpassing the high-resource setting are marked with $\star _ { \cdot } N _ { l }$ denotes the local batch size $N _ { \mathrm { l o c a l } } , N _ { t }$ denotes the total batch size $N _ { \mathrm { t o t a l } }$ , and K represents the accumulation step.

<table><tr><td rowspan="3">Method</td><td>Batch Size</td><td colspan="4">MS Marco</td><td colspan="2">NQ</td><td colspan="2">TriviaQA</td><td colspan="2">WebQ</td><td colspan="2">TREC</td></tr><tr><td rowspan="2"> $N_{\text{I}}/K/N_{\text{t}}$ </td><td colspan="2">NDCG</td><td colspan="2">Recall</td><td colspan="2">Top</td><td colspan="2">Top</td><td colspan="2">Top</td><td colspan="2">Top</td></tr><tr><td>20</td><td>100</td><td>20</td><td>100</td><td>20</td><td>100</td><td>20</td><td>100</td><td>20</td><td>100</td><td>20</td><td>100</td></tr><tr><td colspan="14">VRAM=11GB</td></tr><tr><td>DPR</td><td>8/ 1/ 8</td><td>27.9</td><td>23.5</td><td>8.3</td><td>15.2</td><td>72.2</td><td>81.5</td><td>73.7</td><td>81.9</td><td>72.5</td><td>81.4</td><td>80.8</td><td>88.9</td></tr><tr><td>GradAccum</td><td>8/16/128</td><td>31.1</td><td>26.4</td><td>10.1</td><td>18.1</td><td>77.1</td><td>84.7</td><td>78.4</td><td>84.8</td><td>74.6</td><td>81.9</td><td>79.7</td><td>89.9</td></tr><tr><td>GradCache</td><td>8/16/128</td><td>34.9</td><td>30.6</td><td>12.8*</td><td>22.4*</td><td>79.5*</td><td>85.9</td><td>79.4</td><td>85.1</td><td>75.1*</td><td>82.3</td><td>81.6</td><td>90.2</td></tr><tr><td>CONTACCUM (ours)</td><td>8/16/128</td><td>39.1*</td><td>32.9*</td><td>14.4*</td><td>23.8*</td><td>80.1*</td><td>86.5*</td><td>79.8*</td><td>85.3*</td><td>75.4*</td><td>82.1</td><td>83.3*</td><td>90.5</td></tr><tr><td colspan="14">VRAM=24GB</td></tr><tr><td>DPR</td><td>32/1/ 32</td><td>33.1</td><td>28.6</td><td>11.5</td><td>19.6</td><td>77.0</td><td>84.8</td><td>77.5</td><td>84.2</td><td>74.8*</td><td>82.1</td><td>82.7*</td><td>89.8</td></tr><tr><td>GradAccum</td><td>32/4/128</td><td>33.1</td><td>28.2</td><td>11.8</td><td>20.0</td><td>77.9</td><td>85.4</td><td>80.0*</td><td>84.8</td><td>74.3</td><td>81.9</td><td>79.3</td><td>89.6</td></tr><tr><td>GradCache</td><td>32/4/128</td><td>35.5*</td><td>31.0*</td><td>12.8</td><td>22.1</td><td>79.6*</td><td>86.0</td><td>79.7*</td><td>85.1</td><td>74.7</td><td>81.8</td><td>81.3</td><td>89.6</td></tr><tr><td>CONTACCUM (ours)</td><td>32/4/128</td><td>39.0*</td><td>32.9*</td><td>14.6*</td><td>24.1*</td><td>80.6*</td><td>86.3*</td><td>79.4</td><td>85.1</td><td>75.0*</td><td>82.5*</td><td>81.8</td><td>89.5</td></tr><tr><td colspan="14">VRAM=80GB</td></tr><tr><td>DPR (implemented)</td><td>128/1/128</td><td>35.1</td><td>30.8</td><td>12.7</td><td>22.2</td><td>79.4</td><td>86.1</td><td>79.5</td><td>85.1</td><td>74.7</td><td>82.4</td><td>82.0</td><td>90.5</td></tr><tr><td>DPR (original)</td><td>128/1/128</td><td>-</td><td>-</td><td>-</td><td>-</td><td>78.4</td><td>85.4</td><td>79.4</td><td>85.0</td><td>73.2</td><td>81.4</td><td>79.8</td><td>89.1</td></tr></table>

CONTACCUM outperforms the high-resource DPR even under low-resource constraints. Table 1 compares the performance of CONTACCUMwith baseline methods under low-resource setting. Notably, CONTACCUM, with only 11GB of memory, surpasses the performance of DPR in the high-resource setting (80GB). This demonstrates that CONTACCUMis not only memory-efficient but also achieves superior performance compared to the baseline.

CONTACCUM maintains consistent performance across different memory constraints. CONTACCUM exhibits robust performance regardless of the memory constraint level (11GB or 24GB), with only minor variations between the two settings. In contrast, the performance of both DPR and GradAccum improves as the available memory increases from 11GB to 24GB. This suggests that the performance gains of CONTACCUM are not significantly affected by the severity of memory limitations.

The effectiveness of CONTACCUM is amplified under more severe memory constraints. While CONTACCUM consistently outperforms the baseline methods in both 11GB and 24GB scenarios, the performance gap between CONTACCUM and the baselines is more substantial in the 11GB setting. This indicates that the advantages of CONTACCUM are particularly evident when memory constraints are stringent, emphasizing its effectiveness in low-resource setting. The strong performance of CONTACCUM can be attributed to its dual memory bank strategy, which allows it to utilize more negative samples than GradCache, even in low-resource settings. Furthermore, CONTACCUM outperforms the high-resource setting in 18 out of 24 metrics, improving up to 4.9 points. In contrast, GradCache only surpasses the high-resource setting in 8 metrics, with marginal improvements likely due to randomness. These results demonstrate the fundamental advantage of CONTACCUM in achieving superior performance compared to both the baselines and the high-resource setting.

## 5.2 Influence of each components in CONTACCUM

Table 2: Results of removing the components of CONTACCUM. The DPR performance in low-resource (BSZ=8) and high-resource (BSZ=128) settings are shown as baselines. The best-performing method is highlighted in bold.

<table><tr><td colspan="2">w/ Hard Negative</td><td colspan="2">w/o Hard Negative</td></tr><tr><td>Method</td><td>Top@20</td><td>Method</td><td>Top@20</td></tr><tr><td>DPR (BSZ=8)</td><td>70.9</td><td>DPR (BSZ=8)</td><td>63.7</td></tr><tr><td>DPR (BSZ=128)</td><td>78.4</td><td>DPR (BSZ=128)</td><td>74.3</td></tr><tr><td>CONTACCUM (ours)</td><td>78.8</td><td>CONTACCUM (ours)</td><td>76.3</td></tr><tr><td>w/o.  $M_q$ </td><td>70.8</td><td>w/o.  $M_q$ </td><td>72.3</td></tr><tr><td>w/o. Past Enc.</td><td>76.5</td><td>w/o. Past Enc.</td><td>73.4</td></tr><tr><td>w/o.  $M_q$ /Past Enc.</td><td>67.8</td><td>w/o.  $M_q$ /Past Enc.</td><td>73.9</td></tr><tr><td>w/o. GradAccum</td><td>76.7</td><td>w/o. GradAccum</td><td>74.1</td></tr></table>

Table 2 shows the influence of key components in CONTACCUM by removing each component with NQ. We also reported experiments that excluded hard negatives during training to observe the tendency. The most significant performance drop occurred when the query memory bank $M _ { q }$ was removed, indicating its crucial role in CONTACCUM. The other components of CONTACCUM also contributed to the overall performance, with consistent trends regardless of using hard negatives.

Passage memory bank alone degrades performance due to gradient norm imbalance. Specifically, using only the passage memory bank $( \mathrm { w } / \mathrm { o } , M _ { q } )$ , similar to the pre-batch negatives, led to an 8-point performance drop in Top@20 compared to CONTACCUM. This decrease can be attributed to the gradient norm imbalance problem highlighted in Section 3.3. Section 5.5 further analyzes this issue.

GradAccum and past encoder representations are crucial for stable training and performance. Moreover, when GradAccum was not applied (w/o. GradAccum), a 2.1-point performance decline was observed in Top@20, highlighting the importance of involving more data in gradient calculations for stable training in CONTACCUM. Additionally, a 2.3-point performance decrease was noted when representations generated by past encoders were not used (w/o. Past Enc.). This finding confirms that past encoder representations contribute to training, as suggested by previous studies [37, 38, 19]. However, unlike pre-batch negatives, query memory bank ${ \dot { M } } _ { q }$ demonstrates that the greatest performance improvement is achieved by employing a dual memory bank, which leverages representations generated by past query and passage encoders.

## 5.3 Memory bank size analysis

Figure 3 indicates the experimental results on the NQ dataset, demonstrating the impact of memory bank size $N _ { \mathrm { { m e m o r y } } }$ and accumulation steps K on CONTACCUM’s performance in a low-resource setting with a local batch size of 8. As the memory bank size $N _ { \mathrm { { m e m o r y } } }$ increases, more negative passages are utilized in training, and as the accumulation steps increase, more data is considered in each model update. The performance of DPR in both low-resource and high-resource scenarios( $N _ { \mathrm { t o t a l } } =$

![](images/9a376293c37bdd98f1e747d884055aeda83b91f958eb9b1ce560d72672c48f16.jpg)  
Figure 3: Analysis of accumulation step and memory bank size. DPR performance in low-resource (BSZ=8) and high-resource (BSZ=128) settings is shown as baselines, along with the performance of gradient accumulation for each total batch size $( N _ { \mathrm { t o t a l } } )$ .

![](images/376e28b6021e454ee3932e11a5a13bf0a88f7047b4d1328d181858dfc817e3f8.jpg)  
Figure 4: Comparison of the speed of one weight update for different methods as the total batch size $( N _ { \mathrm { t o t a l } } )$ changes.

32, 64, 128) is also included for comparison. Note that gradient accumulation is not used when the total batch size is 8 and only the dual memory bank is employed.

CONTACCUM consistently outperforms GradAccum and DPR regardless of the size of memory bank and accumulation step. The results show that increasing the memory bank size improves performance even when GradAccum is not used. This indicates that even without gradient accumulation, utilizing representations from the memory bank to construct a larger similarity matrix enhances performance. This trend remains consistent as the accumulation step increases. Moreover, CONTACCUM consistently outperforms GradAccum in all $N _ { \mathrm { t o t a l } }$ settings. Remarkably, CONTACCUM with $N _ { \mathrm { l o c a l } } = 8 , N _ { \mathrm { t o t a l } } = \dot { 6 } 4$ , and $N _ { \mathrm { { m e m o r y } } } = 1 2 8$ surpasses the performance of DPR in a high-resource setting $( N _ { \mathrm { t o t a l } } = N _ { \mathrm { l o c a l } } = 1 2 8 )$ . The performance improvement of CONTACCUM converges as the accumulation step and memory bank size increase, demonstrating that CONTACCUM can robustly enhance performance regardless of memory bank size and accumulation steps.

## 5.4 Train speed

In this subsection, we compare the training speed of CONTACCUM with baseline methods. Figure 4 shows the results of experiments comparing the speed of a single training iteration (1 weight update) as the accumulation step increases in a low-resource settings with 11GB of available memory. Unlike the high-resource setting, where the total batch can be processed through forward and backward pass at once, the train speed slow down in low-resource settings due to various computations and storing gradients.

CONTACCUM achieves faster iteration times than GradCache, even with large memory banks. As shown in Figure 4, CONTACCUM performs single iterations faster than GradCache in all total batch size. Notably, when $N _ { \mathrm { t o t a l } } = 5 1 2$ , GradCache is 93% slower than GradAccum, while CONTACCUM only takes 26% more time, even with the largest memory bank size of $N _ { \mathrm { m e m o r y } } = 8 1 9 2$ . This indicates that CONTACCUM completes iterations 34% faster than GradCache. The significant additional time for computing one iteration in GradCache is due to the overhead of calculating and storing gradients of representations, as well as the repetitive forward and backpropagation. In contrast, CONTACCUM incurs a relatively minor loss of speed compared to GradAccum due to the additional computations involved in storing and retrieving representations from the memory bank and calculating the enlarged similarity matrix. While pre-batch negatives [19] shows similar computational efficiency to our method, it degrades the performance as demonstrated in Table 2.

## 5.5 Gradient norm ratio

We conducted experiments comparing the gradient norms of the query and passage encoders to investigate whether the presence of a query memory bank $M _ { q }$ affects the gradient norm imbalance problem, as discussed in Section 3.3. The results are presented in Figure 5. This experiment defines the ratio of gradient norms between the two encoders as GradNormRatio $= | | \nabla _ { \boldsymbol { \Lambda } } \mathbf { \dot { | } } | _ { 2 } / | | \nabla \Theta | | _ { 2 }$ . We measured GradNormRatio during the training of the $\mathrm { N Q } . ^ { 5 }$ If the two encoders have similar gradient norms during training, GradNormRatio should be close to 1. If the passage encoder $( g _ { \Lambda } )$ has a larger gradient norm, GradNormRatio will be greater than 1.

![](images/3ad36afd58b953b68bed1e886c084c2d7c592f917443bc2e73892ed74a534cc9.jpg)  
Figure 5: Analysis of GradNormRatio throughout the training process on the NQ dataset.

Dual memory bank helps maintain gradient norm balance. The experimental results show that when the query memory bank $M _ { q }$ is not used, GradNormRatio consistently increases. In contrast, CONTACCUM, which utilizes a dual memory bank $( M _ { q } , M _ { p } )$ , maintains a GradNormRatio close to 1, similar to DPR.

This indicates that the pre-batch negatives exhibit gradient norm imbalance problem. It is because pre-batch negatives only use passage memory bank, leading to an imbalance in the number of query and passage representations used in gradient calculations, as discussed in 3.3. The gradient norm imbalance problem consistently occurred even when the timing of omitting the query memory bank $M _ { q }$ is varied during training, as shown in Figure 6.

The gradient norm imbalance problem observed during the actual training process becomes increasingly severe, causing the gradient norm of the passage encoder to be up to 30 times larger than the query encoder. As noted by Senushkin et al. [33] and Chen et al. [4], such extreme differences in gradient norms between the two models negatively impact performance. The significant performance drop observed in 5.2 when the query memory bank $M _ { q }$ is not used can be attributed to the gradient norm imbalance problem.

## 6 Conclusion

In this work, we proposed CONTACCUM, a novel memory reduction methodology for training dual-encoders with InfoNCE Loss in low-resource settings. By employing a dual memory bank structure, CONTACCUM achieves stable training and outperforms high-resource baselines, as demonstrated through extensive experiments on five information retrieval datasets. Our mathematical analysis of the dual-encoder training process underscores the importance of balanced gradient norms, which is effectively addressed by the dual memory bank approach. Furthermore, various ablation experiments showed that the accumulation step and memory bank size significantly contribute to performance improvement.

Limitations. While CONTACCUM reduces computational costs and stabilizes training, this study is limited by its focus on supervised fine-tuning. Recently, many studies have proposed a pre-training stage for dense retriever [12, 7, 8, 29]. It remains to be investigated whether the gradient norm imbalance problem arises during the pre-training stage and whether CONTACCUM can alleviate it. Additionally, CONTACCUM still relies on the softmax operation, which incurs high computational costs. Reducing this reliance on the softmax operation could lead to more efficient training and broader application of the dense retriever.

Broader impacts. CONTACCUM is designed to train dense retrievers efficiently, which allows it to be applied to various knowledge-intensive systems with limited resources. Examples of such applications include search engines, retrieval-augmented generation, and fact verification on local machines. However, we strongly discourage the use of CONTACCUM in high-risk domains such as medical and legal fields, where the retrieval of incorrect information could have a serious impact.

Future works. In future work, we plan to extend CONTACCUM to the pre-training phase with a uni-encoder structure to assess its broader applicability. We also aim to investigate efficient training strategies to mitigate the substantial computational burden caused by the softmax operation. By addressing these areas, we hope to encourage further research on optimizing dual-encoder training for low-resource settings in the field of information retrieval.

## Acknowledgements

This work was supported by the National Research Foundation of Korea(NRF) grant funded by the Korea government(MSIT)(RS-2024-00407803). This work was also supported by Institute of Information & Communications Technology Planning & Evaluation (IITP) grant funded by the Korea government (MSIT) (RS-2024-00460011, Climate and Environmental Data Platform for Enhancing Climate Technology Capabilities in the Anthropocene (CEDP).

We would like to express our sincere gratitude to Keonwoo Kim, Joonwon Jang, Hyowon Cho, Minjin Jeon, and Sangyeop Kim for their valuable feedback and insightful comments. We also deeply appreciate our collegues; Joonghoon Kim, Saeran Park, SangMin Lee, Jiyoon Lee, Jaewon Cheon, and Seonghee Hong - for their constructive discussions and support throughout this work.

## References

[1] Petr Baudiš and Jan Šedivý. 2015. Modeling of the Question Answering Task in the YodaQA System. In Experimental IR Meets Multilinguality, Multimodality, and Interaction, pages 222–228, Cham. Springer International Publishing.

[2] Jonathan Berant, Andrew K. Chou, Roy Frostig, and Percy Liang. 2013. Semantic Parsing on Freebase from Question-Answer Pairs. In Conference on Empirical Methods in Natural Language Processing.

[3] Xinlei Chen, Haoqi Fan, Ross Girshick, and Kaiming He. 2020. Improved Baselines with Momentum Contrastive Learning. arXiv preprint arXiv:2003.04297.

[4] Zhao Chen, Vijay Badrinarayanan, Chen-Yu Lee, and Andrew Rabinovich. 2018. GradNorm: Gradient Normalization for Adaptive Loss Balancing in Deep Multitask Networks. In Proceedings of the 35th International Conference on Machine Learning, volume 80 of Proceedings of Machine Learning Research, pages 794–803. PMLR.

[5] Zhuyun Dai, Vincent Y Zhao, Ji Ma, Yi Luan, Jianmo Ni, Jing Lu, Anton Bakalov, Kelvin Guu, Keith Hall, and Ming-Wei Chang. 2023. Promptagator: Few-shot Dense Retrieval From 8 Examples. In The Eleventh International Conference on Learning Representations.

[6] Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. 2019. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. In Proceedings ofthe 2019 Conference ofthe North American Chapter ofthe Associationfor Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers), pages 4171–4186, Minneapolis, Minnesota. Association for Computational Linguistics.

[7] Luyu Gao and Jamie Callan. 2021. Condenser: a Pre-training Architecture for Dense Retrieval. In Proceedings ofthe 2021 Conference on Empirical Methods in Natural Language Processing, pages 981–993, Online and Punta Cana, Dominican Republic. Association for Computational Linguistics.

[8] Luyu Gao and Jamie Callan. 2022. Unsupervised Corpus Aware Language Model Pre-training for Dense Passage Retrieval. In Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), pages 2843–2853, Dublin, Ireland. Association for Computational Linguistics.

[9] Luyu Gao, Yunyi Zhang, Jiawei Han, and Jamie Callan. 2021. Scaling Deep Contrastive Learning Batch Size under Memory Limited Setup. In Proceedings of the 6th Workshop on Representation Learning for NLP.

[10] Michael Gutmann and Aapo Hyvärinen. 2010. Noise-contrastive estimation: A new estimation principle for unnormalized statistical models. In Proceedings of the Thirteenth International Conference on Artificial Intelligence and Statistics, volume 9 of Proceedings of Machine Learning Research, pages 297–304, Chia Laguna Resort, Sardinia, Italy. PMLR.

[11] K. He, H. Fan, Y. Wu, S. Xie, and R. Girshick. 2020. Momentum Contrast for Unsupervised Visual Representation Learning. In 2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pages 9726–9735, Los Alamitos, CA, USA. IEEE Computer Society.

[12] Gautier Izacard, Mathilde Caron, Lucas Hosseini, Sebastian Riedel, Piotr Bojanowski, Armand Joulin, and Edouard Grave. 2022. Unsupervised Dense Information Retrieval with Contrastive Learning. Transactions on Machine Learning Research.

[13] Bowen Jin, Hansi Zeng, Guoyin Wang, Xiusi Chen, Tianxin Wei, Ruirui Li, Zhengyang Wang, Zheng Li, Yang Li, Hanqing Lu, Suhang Wang, Jiawei Han, and Xianfeng Tang. 2023. Language Models As Semantic Indexers.

[14] Jeff Johnson, Matthijs Douze, and Hervé Jégou. 2021. Billion-Scale Similarity Search with GPUs. IEEE Transactions on Big Data, 7(3):535–547.

[15] Mandar Joshi, Eunsol Choi, Daniel S. Weld, and Luke Zettlemoyer. 2017. TriviaQA: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension. In Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics, Vancouver, Canada. Association for Computational Linguistics.

[16] Vladimir Karpukhin, Barlas Oguz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, and Wen-tau Yih. 2020. Dense Passage Retrieval for Open-Domain Question Answering. In Proceedings ofthe 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP), pages 6769–6781, Online. Association for Computational Linguistics.

[17] Brian Kulis. 2013. Metric learning: A survey. Foundations and Trends in Machine Learning, 5(4):287–364.

[18] Tom Kwiatkowski, Jennimaria Palomaki, Olivia Redfield, Michael Collins, Ankur Parikh, Chris Alberti, Danielle Epstein, Illia Polosukhin, Matthew Kelcey, Jacob Devlin, Kenton Lee, Kristina N. Toutanova, Llion Jones, Ming-Wei Chang, Andrew Dai, Jakob Uszkoreit, Quoc Le, and Slav Petrov. 2019. Natural Questions: a Benchmark for Question Answering Research. Transactions ofthe Association ofComputational Linguistics.

[19] Jinhyuk Lee, Mujeen Sung, Jaewoo Kang, and Danqi Chen. 2021. Learning Dense Representations of Phrases at Scale. In Association for Computational Linguistics (ACL).

[20] Kenton Lee, Ming-Wei Chang, and Kristina Toutanova. 2019. Latent Retrieval for Weakly Supervised Open Domain Question Answering. In Proceedings ofthe 57th Annual Meeting of the Associationfor Computational Linguistics, pages 6086–6096, Florence, Italy. Association for Computational Linguistics.

[21] Junnan Li, Dongxu Li, Caiming Xiong, and Steven C. H. Hoi. 2022. BLIP: Bootstrapping Language-Image Pre-training for Unified Vision-Language Understanding and Generation. In International Conference on Machine Learning.

[22] Junnan Li, Ramprasaath Selvaraju, Akhilesh Gotmare, Shafiq Joty, Caiming Xiong, and Steven Chu Hong Hoi. 2021. Align before Fuse: Vision and Language Representation Learning with Momentum Distillation. In Advances in Neural Information Processing Systems, volume 34, pages 9694–9705. Curran Associates, Inc.

[23] Ilya Loshchilov and Frank Hutter. 2019. Decoupled Weight Decay Regularization. In International Conference on Learning Representations.

[24] Shuqi Lu, Di He, Chenyan Xiong, Guolin Ke, Waleed Malik, Zhicheng Dou, Paul Bennett, Tie-Yan Liu, and Arnold Overwijk. 2021. Less is More: Pretrain a Strong Siamese Encoder for Dense Text Retrieval Using a Weak Decoder. In Proceedings ofthe 2021 Conference on Empirical Methods in Natural Language Processing, pages 2780–2791, Online and Punta Cana, Dominican Republic. Association for Computational Linguistics.

[25] Sewon Min, Weijia Shi, Mike Lewis, Xilun Chen, Wen-tau Yih, Hannaneh Hajishirzi, and Luke Zettlemoyer. 2023. Nonparametric Masked Language Modeling. In Findings of the Association for Computational Linguistics: ACL 2023, pages 2097–2118, Toronto, Canada. Association for Computational Linguistics.

[26] Tri Nguyen, Mir Rosenberg, Xia Song, Jianfeng Gao, Saurabh Tiwary, Rangan Majumder, and Li Deng. 2016. MS MARCO: A human generated machine reading comprehension dataset. In CoCo@ NIPS.

[27] Adam Paszke, Sam Gross, Francisco Massa, Adam Lerer, James Bradbury, Gregory Chanan, Trevor Killeen, Zeming Lin, Natalia Gimelshein, Luca Antiga, Alban Desmaison, Andreas Kopf, Edward Yang, Zachary DeVito, Martin Raison, Alykhan Tejani, Sasank Chilamkurthy, Benoit Steiner, Lu Fang, Junjie Bai, and Soumith Chintala. 2019. PyTorch: An Imperative Style, High-Performance Deep Learning Library. In Advances in Neural Information Processing Systems 32, pages 8024–8035. Curran Associates, Inc.

[28] Yingqi Qu, Yuchen Ding, Jing Liu, Kai Liu, Ruiyang Ren, Wayne Xin Zhao, Daxiang Dong, Hua Wu, and Haifeng Wang. 2021. RocketQA: An Optimized Training Approach to Dense Passage Retrieval for Open-Domain Question Answering. In Proceedings ofthe 2021 Conference ofthe North American Chapter of the Association for Computational Linguistics: Human Language Technologies, pages 5835–5847, Online. Association for Computational Linguistics.

[29] Ori Ram, Gal Shachaf, Omer Levy, Jonathan Berant, and Amir Globerson. 2022. Learning to Retrieve Passages without Supervision. In Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, pages 2687–2700, Seattle, United States. Association for Computational Linguistics.

[30] Nils Reimers and Iryna Gurevych. 2019. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. In Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing. Association for Computational Linguistics.

[31] Ruiyang Ren, Shangwen Lv, Yingqi Qu, Jing Liu, Wayne Xin Zhao, Qiaoqiao She, Hua Wu, Haifeng Wang, and Ji-Rong Wen. 2021. PAIR: Leveraging Passage-Centric Similarity Relation for Improving Dense Passage Retrieval. In Findings of the Association for Computational Linguistics: ACL/IJCNLP 2021, Online Event, August 1-6, 2021, volume ACL/IJCNLP 2021 of Findings of ACL, pages 2173–2183. Association for Computational Linguistics.

[32] Stephen Robertson and Hugo Zaragoza. 2009. The Probabilistic Relevance Framework: BM25 and Beyond. Foundations and Trends in Information Retrieval, 3:333–389.

[33] Dmitry Senushkin, Nikolay Patakin, Arseny Kuznetsov, and Anton Konushin. 2023. Independent Component Alignment for Multi-Task Learning. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pages 20083–20093.

[34] Weiwei Sun, Lingyong Yan, Zheng Chen, Shuaiqiang Wang, Haichao Zhu, Pengjie Ren, Zhumin Chen, Dawei Yin, Maarten Rijke, and Zhaochun Ren. 2023. Learning to Tokenize for Generative Retrieval. In Advances in Neural Information Processing Systems, volume 36, pages 46345–46361. Curran Associates, Inc.

[35] Nandan Thakur, Nils Reimers, Andreas Rücklé, Abhishek Srivastava, and Iryna Gurevych. 2021. BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models. In Proceedings ofthe Neural Information Processing Systems Track on Datasets and Benchmarks, volume 1.

[36] Aäron van den Oord, Yazhe Li, and Oriol Vinyals. 2018. Representation Learning with Contrastive Predictive Coding. CoRR, abs/1807.03748.

[37] Jinpeng Wang, Jieming Zhu, and Xiuqiang He. 2021. Cross-Batch Negative Sampling for Training Two-Tower Recommenders. In Proceedings of the 44th International ACM SIGIR Conference on Research and Development in Information Retrieval, SIGIR ’21, page 1632–1636, New York, NY, USA. Association for Computing Machinery.

[38] Xun Wang, Haozhi Zhang, Weilin Huang, and Matthew R Scott. 2020. Cross-Batch Memory for Embedding Learning. In CVPR.

[39] Z. Wu, Y. Xiong, S. X. Yu, and D. Lin. 2018. Unsupervised Feature Learning via Non-parametric Instance Discrimination. In 2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pages 3733–3742, Los Alamitos, CA, USA. IEEE Computer Society.

[40] Zhirong Wu, Alexei A. Efros, and Stella X. Yu. 2018. Improving Generalization via Scalable Neighborhood Component Analysis. In Proceedings of the European Conference on Computer Vision (ECCV).

[41] Lee Xiong, Chenyan Xiong, Ye Li, Kwok-Fung Tang, Jialin Liu, Paul N. Bennett, Junaid Ahmed, and Arnold Overwijk. 2021. Approximate Nearest Neighbor Negative Contrastive Learning for Dense Text Retrieval. In International Conference on Learning Representations.

[42] Zhen Yang, Zhou Shao, Yuxiao Dong, and Jie Tang. 2024. TriSampler: A Better Negative Sampling Principle for Dense Retrieval. Proceedings of the AAAI Conference on Artificial Intelligence, 38(8):9269–9277.

[43] Wayne Xin Zhao, Jing Liu, Ruiyang Ren, and Ji-Rong Wen. 2024. Dense Text Retrieval Based on Pretrained Language Models: A Survey. ACM Trans. Inf. Syst., 42(4).

A. Derivatives of InfoLoss with memory bank

$$
\begin{array} { l } \nabla _ { \Theta } \mathcal { L } ( S _ { k } ) = \sum _ { \mathbf { q } _ { l } \in Q _ { k } ^ { t } } = \frac { \partial \mathcal { L } ( S _ { k } ) } { \partial \mathbf { q } _ { l } } \cdot \frac { \partial \mathbf { q } _ { l } } { \partial \Theta } \\ \frac { \partial \mathcal { L } ( S _ { k } ) } { \partial \mathbf { q } _ { l } } = \frac { \partial } { \partial \mathbf { q } _ { l } } ( - \frac { 1 } { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { q } } ) \sum _ { i } ^ { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { q } } \log \frac { \exp ( \mathbf { q } _ { i } \cdot \mathbf { p } _ { i } ^ { \top } ) } { \sum _ { j } ^ { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { I } p } \exp ( \mathbf { q } _ { i } \cdot \mathbf { p } _ { j } ^ { \top } ) } \\ = - \frac { 1 } { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { q } } \sum _ { i } ^ { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { q } } \left[ \frac { \partial } { \partial \mathbf { q } _ { l } } ( \mathbf { q } _ { i } \cdot \mathbf { p } _ { i } ^ { \top } ) - \frac { \partial } { \partial \mathbf { q } _ { l } } \log \sum _ { j } ^ { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { p } } \exp ( \mathbf { q } _ { i } \cdot \mathbf { p } _ { j } ^ { \top } ) \right] \\ = - \frac { 1 } { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { q } } \left( \mathbf { p } _ { l } - \sum _ { i } ^ { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { q } } \sum _ { j } ^ { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { p } } \left[ \frac { \exp ( \mathbf { q } _ { i } \cdot \mathbf { p } _ { j } ^ { \top } ) } { \sum _ { k } ^ { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { p } } \exp ( \mathbf { q } _ { i } \cdot \mathbf { p } _ { k } ^ { \top } ) } \cdot \frac { \partial } { \partial \mathbf { q } _ { j } } ( \mathbf { q } _ { i } \cdot \mathbf { p } _ { j } ^ { \top } ) \right] \right) \\ = - \frac { 1 } { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { q } } \left( \mathbf { p } _ { l } - \sum _ { i } ^ { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { q } } \sum _ { j } ^ { N _ { \mathrm{local} } + N ^ { p } m o r y} [ S _ { k ( i , j ) } \cdot \frac { \partial } { \partial \mathbf { q } _ { l }} ( \mathbf { q } _ { i } \cdot \mathbf { p } _ { j } ^ { \top } ) ]\right) \\ = - \frac { 1 } { N _ { \mathrm{local} } + N _ { \mathrm{memory} } ^ { q } } \left( \mathbf { p } _ { l } - \sum _ { j } ^ { N _ { \mathrm{local} } + N _ { m e m o r y} ^ { p }} [ S _ { k ( l , j ) } \cdot \mathbf { p } _ { j} ]\right) \\ \nabla _ { \Lambda } \mathcal { L } ( S _ { k ) } = 2 / 3 . 5 6 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 8 . \\ = - ( n ) ^ {\prime   |   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^{|   |} = - ( n ) ^{|   |} = - ( n ) ^{|   |} = - ( n ) ^{|   |} = - ( n ) ^{|   |} = - ( n ) ^{|   |} = - ( n ) ^{|   |} = - ( n ) ^{|   |} = - ( n ) ^{|   |} = - ( n ) ^{|   |} = - ( n ) ^|   |   | \\ = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |}, \\ = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ {|   |}, \\ = - ( n ) ^ {|   |} = - ( n ) ^ {|   |} = - ( n ) ^ |   |
| . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
$$

## B. Details on hyperparameters

Hyperparameters. The hyperparameters for training were set as follows: the warmup step was 1,237 steps, weight decay was set to 0, and a customized scheduler with a linear decay of the learning rate after the warmup was used. The optimizer was AdamW [23] with epsilon set to 1e-8, and the learning rate was 2e-5. Gradient clipping was applied at a value of 2.0, and τ was set to 1. For retrieval, we used the FAISS [14] library to perform exact nearest neighbor search with default hyperparameters.

## C. Similarity Mass

To verify whether representations generated by past encoders aid the current encoder’s training, we conducted an experiment measuring the similarity mass of passage representations at different time steps. The results are shown in Figure 6. The similarity mass is defined as the sum of similarities after passing through a softmax function for all current time t queries with passage representations generated at past time steps t − k, as shown in Equation 10:

Figure 6: Experiments on similarity probability mass.  
![](images/80770f6ec7bba3f56d8f99c4f5a907a87f8b6fab3fae416b0ccbf967dfcaf433.jpg)

$$
\operatorname{SimMass} _ {t - k} = \frac {1}{| \mathbf {Q} ^ {t} |} \sum_ {i = 1} ^ {| \mathbf {Q} ^ {t} |} \sum_ {j = 1} ^ {| \mathbf {P} ^ {t - k} |} \mathbf {Q} _ {i} ^ {t} \cdot \left(\mathbf {P} _ {j} ^ {t - k}\right) ^ {\top}\tag{10}
$$

Passage representations of the current and previous encoder have similar importance as negative passage. The results indicate that there is no significant difference in the similarity mass between the in-batch negative passage representations at the current training step and the passage representations from up to six previous steps. As shown in Equation 8 and 9, the gradients of the two encoders are proportional to the magnitude of the similarities. This means that negative passages with high similarity to a single query produce large gradients, which aids in training the dense retrieval model [41]. This finding suggests that past representations can be beneficial from the early stages of training, contrary to previous studies [37, 38].

Additionally, as illustrated in Figure 6, CONTACCUM demonstrates the same similarity mass trend as DPR, validating the effectiveness of utilizing past representations from the early stages of training with CONTACCUM.

## D. Gradient Norm Ratio of Omitting the Query Memory Bank

Figure 7: Experimental results of omitting query memory bank during training.  
![](images/a8ffdfda9e1cafe6da94b8f61db0ab7112c99508d9e30953cca43efe52ea7823.jpg)

Gradient norm imbalance problem occurs when the query memory bank is omitted. We omitted the query memory bank during training at various epochs: [10, 20, 30]. As shown in Figure 7, the gradient norm imbalance problem arises immediately after the query memory bank is excluded. Additionally, irrespective of when the query memory bank is omitted, all experiments without the query memory bank exhibit very high gradient norm ratios in the later stages of training. This indicates that gradient norm imbalance problem can cause unstable training during the entire training process, unlike previous studies which mentioned the major cause of unstable training is rapid changes in encoder representations in the early epochs [38, 37].

## E. Actual Memory Usage

ContAccum uses few memory for dual memory bank but it works greatly Theoretically, CONTACCUM’s query and passage memory banks $( M _ { q } , M _ { p } )$ do not cache activation values, requiring only additional memory for the stored representations compared to GradAccum. The memory usage of the dual memory bank can be calculated as follows:

$$
\mathbf {N} _ {\text { memory }} \times \dim_ {\text { embed }} \times 2 \times 4\tag{11}
$$

where 2 represents the query and passage memory bank and 4 denotes full precision (4 bytes).

Table 3: Comparison of Memory Usage

<table><tr><td rowspan="2">Method</td><td rowspan="2"> $N_{local}/K/N_{total}/N_{memory}$ </td><td rowspan="2">Memory (GB)</td><td colspan="2">Additional Memory</td></tr><tr><td>Actual</td><td>Theoretical</td></tr><tr><td>DPR</td><td>8/ 1/128/ 0</td><td>7.483</td><td>-</td><td>-</td></tr><tr><td>GradCache</td><td>8/16/128/ 0</td><td>5.158</td><td>-</td><td>-</td></tr><tr><td>GradAccum</td><td>8/16/128/ 0</td><td>8.340</td><td>-</td><td>-</td></tr><tr><td>CONTACCUM</td><td>8/16/128/ 128</td><td>8.342</td><td>0.002</td><td>0.0007</td></tr><tr><td>CONTACCUM</td><td>8/16/128/ 512</td><td>8.346</td><td>0.006</td><td>0.0029</td></tr><tr><td>CONTACCUM</td><td>8/16/128/1024</td><td>8.353</td><td>0.013</td><td>0.0059</td></tr><tr><td>CONTACCUM</td><td>8/16/128/5096</td><td>8.382</td><td>0.042</td><td>0.0117</td></tr></table>

Moreover, we measured each method’s actual memory usage in a VRAM=11GB environment and the results are reported in table 3. The results show that CONTACCUM uses only up to 0.5% more memory than GradAccum, which is a maximum of 12MB even in the largest memory bank $\mathrm { s i z e ( N _ { m e m o r y } = 5 0 9 6 ) }$ . This demonstrates that CONTACCUM is a memory-efficient method that consumes very limited additional memory compared to GradAccum. Furthermore, while GradCache uses less memory than DPR by decomposing complex forward and backward processes, it has the limitation of very slow training speed, as shown in Figure 4.

## F. License

The licenses for the assets used in this paper are as follows:

• Overall train code and partial evaluation code from nano-DPR: CC-BY-NC 4.0

• Train and evaluation datasets preprocessed by DPR: CC-BY-NC 4.0

• Partial evaluation code, and train and evaluation dataset preprocessed by Beir: Apache-2.0

• Hard negative score generated by sentence-transformers library: Apache-2.0