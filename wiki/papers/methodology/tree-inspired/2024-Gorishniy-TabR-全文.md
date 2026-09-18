---
title: "2024-Gorishniy-TabR"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/tree-inspired/2024-Gorishniy-TabR.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# TABR: TABULAR DEEP LEARNING MEETS NEAREST NEIGHBORS

Yury Gorishniy<sup>∗†</sup> Ivan Rubachev<sup>‡†</sup> Nikolay Kartashev<sup>‡†</sup> Daniil Shlenskii<sup>†</sup> Akim Kotelnikov<sup>‡†</sup> Artem Babenko<sup>†‡</sup>

## ABSTRACT

Deep learning (DL) models for tabular data problems (e.g. classification, regression) are currently receiving increasingly more attention from researchers. However, despite the recent efforts, the non-DL algorithms based on gradient-boosted decision trees (GBDT) remain a strong go-to solution for these problems. One of the research directions aimed at improving the position of tabular DL involves designing so-called retrieval-augmented models. For a target object, such models retrieve other objects (e.g. the nearest neighbors) from the available training data and use their features and labels to make a better prediction.

In this work, we present TabR – essentially, a feed-forward network with a custom k-Nearest-Neighbors-like component in the middle. On a set of public benchmarks with datasets up to several million objects, TabR marks a big step forward for tabular DL: it demonstrates the best average performance among tabular DL models, becomes the new state-of-the-art on several datasets, and even outperforms GBDT models on the recently proposed “GBDT-friendly” benchmark (see Figure 1). Among the important findings and technical details powering TabR, the main ones lie in the attention-like mechanism that is responsible for retrieving the nearest neighbors and extracting valuable signal from them. In addition to the higher performance, TabR is simple and significantly more efficient compared to prior retrieval-based tabular DL models. The source code is published: link.

DL wins Ties XGBoost wins

<table><tr><td>MLP (&lt; 2021)</td><td>6</td><td>9</td><td colspan="2">28</td></tr><tr><td>FT-Transformer (Gorishniy et al., 2021)</td><td>7</td><td colspan="2">17</td><td>19</td></tr><tr><td>MLP-PLR (Gorishniy et al., 2022)</td><td>11</td><td colspan="2">15</td><td>17</td></tr><tr><td>TabR (Ours, 2023)</td><td colspan="2">23</td><td>13</td><td>7</td></tr></table>

Figure 1: Comparing DL models with XGBoost (Chen and Guestrin, 2016) on 43 regression and classification tasks of middle scale (≤ 50K objects) from “Why do tree-based models still outperform deep learning on typical tabular data?” by Grinsztajn et al. (2022). TabR marks a significant step forward compared to prior tabular DL models and continues the positive trend for the field.

## 1 INTRODUCTION

Machine learning (ML) problems on tabular data, where objects are described by a set of heterogeneous features, are ubiquitous in industrial applications in medicine, finance, manufacturing, and other fields. Historically, for these tasks, the models based on gradient-boosted decision trees (GBDT) have been a go-to solution for a long time. However, lately, tabular deep learning (DL) models have been receiving increasingly more attention, and they are becoming more competitive (Klambauer et al., 2017; Popov et al., 2020; Wang et al., 2020; Hazimeh et al., 2020; Huang et al., 2020; Gorishniy et al., 2021; Somepalli et al., 2021; Kossen et al., 2021; Gorishniy et al., 2022).

In particular, several attempts to design a retrieval-augmented tabular DL model have been recently made (Somepalli et al., 2021; Qin et al., 2021; Kossen et al., 2021). For a target object, a retrievalaugmented model retrieves additional objects from the training set (e.g. the target object’s nearest neighbors, or even the whole training set) and uses them to improve the prediction for the target object. In fact, the retrieval technique is widely popular in other domains, including natural language processing (Das et al., 2021; Wang et al., 2022; Izacard et al., 2022), computer vision (Jia et al., 2021; Iscen et al., 2022; Long et al., 2022), CTR prediction (Qin et al., 2020; 2021; Du et al., 2022), and others. Compared to purely parametric (i.e. retrieval-free) models, the retrieval-based ones can achieve higher performance and also exhibit several practically important properties, such as the ability for incremental learning and better robustness (Das et al., 2021; Jia et al., 2021).

While multiple retrieval-augmented models for tabular data problems exist, in our experiments, we show that they provide if only minor benefits over the properly tuned multilayer perceptron (MLP; the simplest parametric model), while being significantly more complex and costly. Nevertheless, in this work, we show that, with certain previously overlooked design aspects in mind, it is possible to obtain a retrieval-based tabular architecture that is powerful, simple and substantially more efficient than prior retrieval-based models. We summarize our main contributions as follows:

1. We design TabR – a simple retrieval-augmented tabular DL model which, on a set of public benchmarks, demonstrates the best average performance among DL models, achieves the new state-of-the-art on several datasets and is significantly more efficient than prior deep retrievalbased tabular models.

2. In particular, TabR achieves a notable milestone for tabular DL by outperforming GBDT on the recently proposed benchmark with middle-scale tasks (Grinsztajn et al., 2022), which was originally used to illustrate the superiority of decision-tree-based models over DL models. Tree-based models, in turn, remain a more efficient solution.

3. We highlight the important degrees of freedom of the attention mechanism (the often used module in retrieval-based models) that allow designing better retrieval-based tabular models.

## 2 RELATED WORK

Gradient boosted decision trees (GBDT). GBDT-based ML models are non-DL solutions for supervised problems on tabular data that are popular within the community due to their strong performance and high efficiency. By employing the modern DL building blocks and, in particular, the retrieval technique, our new model successfully competes with GBDT and, in particular, demonstrates that DL models can be superior on non-big data by outperforming GBDT on the recently proposed benchmark with small-to-middle scale tasks (Grinsztajn et al., 2022).

Tabular deep learning. Tabular DL is a rapidly developing field with the recent advances covering parametric architectures (Klambauer et al., 2017; Wang et al., 2020; Gorishniy et al., 2021; 2022) (and many others), regularizations (Jeffares et al., 2023), pretraining (Bahri et al., 2021) and other methods (Hollmann et al., 2023). In this work, we focus specifically on architectures. In particular, the recent studies reveal that MLP-like backbones are still competitive (Kadra et al., 2021; Gorishniy et al., 2021; 2022), and that embeddings for continuous features (Gorishniy et al., 2022) significantly reduce the gap between tabular DL and GBDT. In this work, we show that a properly designed retrieval component can boost the performance of tabular DL even further.

Retrieval-augmented models in general. Usually, the retrieval-based models are designed as follows. For an input object, first, they retrieve relevant samples from available (training) data. Then, they process the input object together with the retrieved instances to produce the final prediction for the input object. One of the common motivations for designing retrieval-based schemes is the local learning paradigm (Bottou and Vapnik, 1992), and the simplest possible example of such a model is the k-nearest neighbors (kNN) algorithm (James et al., 2013). The promise of retrieval-based approaches was demonstrated across various domains, such as natural language processing (Lewis et al., 2020; Guu et al., 2020; Khandelwal et al., 2020; Izacard et al., 2022; Borgeaud et al., 2022), computer vision (Iscen et al., 2022; Long et al., 2022), CTR prediction (Qin et al., 2020; 2021; Du et al., 2022), and others. Additionally, retrieval-augmented models often have useful properties such as better interpretability (Wang and Sabuncu, 2023), robustness (Zhao and Cho, 2018) and others.

Retrieval-augmented models for tabular data problems. The classic example of non-deep retrieval based tabular models are the neighbor-based and kernel methods (James et al., 2013; Nader et al., 2022). There are also deep retrieval-based models applicable to (or directly designed for) tabular data problems (Wilson et al., 2016; Kim et al., 2019; Ramsauer et al., 2021; Kossen et al., 2021;

Somepalli et al., 2021). Notably, some of them omit the retrieval step and use all training data points as the “retrieved” instances (Somepalli et al., 2021; Kossen et al., 2021; Schäfl et al., 2022). However, we show that the existing retrieval-based tabular DL models are only marginally better than simple parametric DL models, and that often comes with a cost of using heavy Transformer-like architectures. Compared to prior work, where several layers with multiple multi-head vanilla attention modules are often used (Ramsauer et al., 2021; Kossen et al., 2021; Somepalli et al., 2021), our model TabR implements its retrieval component with just one single-head attention-like module, customized in a way that makes it better suited for tabular data problems. As a result, TabR substantially outperforms the existing retrieval-based DL models while being significantly more efficient.

## 3 TABR

In this section, we design a new retrieval-augmented deep learning model for tabular data problems.

## 3.1 PRELIMINARIES

Notation. For a given supervised learning problem on tabular data, we denote the dataset as $\{ ( x _ { i } , y _ { i } ) \} _ { i = 1 } ^ { n }$ where $x _ { i } \in \bar { \mathbb { X } }$ represents the i-th object’s features and $y _ { i } \in \mathbb { Y }$ represents the i-th object’s label. Depending on the context, the i index can be omitted. We consider three types of tasks: binary classification $\mathbb { Y } = \{ 0 , 1 \}$ , multiclass classification $\mathbb { Y } = \{ 1 , . . . , C \}$ and regression $\mathbf { \Delta } \mathbf { \hat { Y } = \mathbb { R } }$ . For simplicity, in most places, we will assume that $x _ { i }$ contains only numerical (continuous) features, and we will give additional comments on binary and categorical features when necessary. The dataset is split into three disjoint parts: $\overline { { 1 , n } } = I _ { t r a i n } \cup I _ { v a l } \cup I _ { t e s t }$ , where the “train” part is used for training, the “validation” part is used for early stopping and hyperparameter tuning, and the “test” part is used for the final evaluation. An input object for which a given model makes a prediction is referred to as “input object” or “target object”.

When the retrieval technique is used for a given target object, the retrieval is performed within the set of “context candidates” or simply “candidates”: $\bar { I } _ { c a n d } \subseteq I _ { t r a i n }$ . The retrieved objects, in turn, are called “context objects” or simply “context”. Optionally, the target object can be included in its own context. In this work, unless otherwise noted, we use the same set of candidates for all input objects and set $I _ { c a n d } = I _ { t r a i n }$ (which means retrieving from all training objects).

Experiment setup. We extensively describe our tuning and evaluation protocols in subsection D.6. The most important points are that, for any given algorithm, on each dataset, following Gorishniy et al. (2022), (1) we perform hyperparameter tuning and early stopping using the validation set; (2) for the best hyperparameters, in the main text, we report the metric on the test set averaged over 15 random seeds, and provide standard deviations in Appendix E; (3) when comparing any two algorithms, we take the standard deviations into account as described in subsection D.6; (4) to obtain ensembles of models of the same type, we split the 15 random seeds into three disjoint groups (i.e., into three ensembles) each consisting of five models, average predictions within each group, and report the average performance of the obtained three ensembles.

In this work, we mostly use the datasets from prior literature and provide their summary in Table 1 (sometimes, we refer to this set of datasets as “the default benchmark”). Additionally, in subsection 4.2, we use the recently introduced benchmark with middle-scale tasks $( \le 5 0 K$ objects) (Grinsztajn et al., 2022) where GBDT was reported to be superior to DL solutions.

Table 1: Dataset properties. “RMSE” denotes root-mean-square error, “Acc.” denotes accuracy.

<table><tr><td></td><td>CH</td><td>CA</td><td>HO</td><td>AD</td><td>DI</td><td>OT</td><td>HI</td><td>BL</td><td>WE</td><td>CO</td><td>MI</td></tr><tr><td>#objects</td><td>10000</td><td>20640</td><td>22784</td><td>48842</td><td>53940</td><td>61878</td><td>98049</td><td>166821</td><td>397099</td><td>581012</td><td>1200192</td></tr><tr><td>#num.features</td><td>7</td><td>8</td><td>16</td><td>6</td><td>6</td><td>93</td><td>28</td><td>4</td><td>118</td><td>10</td><td>131</td></tr><tr><td>#bin.features</td><td>3</td><td>0</td><td>0</td><td>1</td><td>0</td><td>0</td><td>0</td><td>1</td><td>1</td><td>44</td><td>5</td></tr><tr><td>#cat.features</td><td>1</td><td>0</td><td>0</td><td>7</td><td>3</td><td>0</td><td>0</td><td>4</td><td>0</td><td>0</td><td>0</td></tr><tr><td>metric</td><td>Acc.</td><td>RMSE</td><td>RMSE</td><td>Acc.</td><td>RMSE</td><td>Acc.</td><td>Acc.</td><td>RMSE</td><td>RMSE</td><td>Acc.</td><td>RMSE</td></tr><tr><td>#classes</td><td>2</td><td>-</td><td>-</td><td>2</td><td>-</td><td>9</td><td>2</td><td>-</td><td>-</td><td>7</td><td>-</td></tr><tr><td>majority class</td><td>79%</td><td>-</td><td>-</td><td>76%</td><td>-</td><td>26%</td><td>52%</td><td>-</td><td>-</td><td>48%</td><td>-</td></tr></table>

## 3.2 ARCHITECTURE

To build a retrieval-based tabular DL model, we choose an incremental approach, where we start from a simple retrieval-free architecture, and, step by step, add and improve a retrieval component.

Let’s consider a generic feed-forward retrieval-free network $f ( x ) = P ( E ( x ) )$ ) informally partitioned into two parts: encoder $E : \mathbb { X } \to \mathbb { R } ^ { d }$ and predictor $P : \mathbb { R } ^ { d }  \hat { \mathbb { Y } }$ . To incrementally make it retrievalbased, we add retrieval module R in a residual branch after $E$ as illustrated in Figure 2, where $\widetilde { \boldsymbol { x } } \in \mathbb { R } ^ { d }$ is the intermediate representation of the target object, $\{ \tilde { x } _ { i } \} _ { i \in I _ { c a n d } } \subset \mathbb { R } ^ { d }$ are the intermediate representations of the candidates and $\{ y _ { i } \} _ { i \in I _ { c a n d } } \bar { \subset } \mathbb { Y }$ are the labels of the candidates.

![](images/4c99caafe5f976037e3f878fa67846002920f90ef543f07b5603a2fa92822b97.jpg)  
Figure 2: The generic retrieval-based architecture introduced in subsection 3.2 and used to build TabR. First, a target object and its candidates for retrieval are encoded with the same encoder $E .$ . Then, the <sup>=</sup> retrieval module $R$ <sup>Linear BlockInput</sup> <sup>Module</sup>enriches the target object’s representation by retrieving and processing relevant(shared) labels objects from the candidates. Finally, predictor $\boldsymbol { P }$ makes a prediction. The bold path highlights theRetrieval module Information flow structure of the feed-forward retrieval-free model before the addition of the retrieval module R.

Encoder and predictor. The encoder E and predictor P modules (Figure 2) are not the focus of this work, so we keep them simple as illustrated in Figure 3.

![](images/f825d0798a9c347bdb043674d4434c2e0502165fdaec3b49b60a3b26484224b3.jpg)  
Figure 3: Encoder $E$ and predictor $P$ introduced in Figure 2. $N _ { E }$ and $N _ { P }$ denote the number of Block modules in $E$ and $P ,$ respectively. The Input Module encapsulates the input processing routines (feature normalization, one-hot encoding, etc.) and assembles a vector input for the subsequent linear layer. In particular, Input Module can contain embeddings for continuous features (Gorishniy et al., 2022). (<sup>∗</sup> LayerNorm is omitted in the first Block of $E . )$

<sup>top-m</sup>Retrieval module. We define the retrieval module R in the spirit of k-nearest neighbors as illustrated <sup>softmax</sup>in Figure 4. In the figure, the following formal details are omitted for clarity:

1. If the encoder $E$ contains at least one Block $( \mathrm { i } . \mathrm { e } . \ N _ { E } > 0 )$ , then, before being passed to $R ,$ x˜ and all ${ \tilde { x } } _ { i }$ are normalized with a shared layer normalization (Ba et al., 2016).

2. Optionally, the target object itself can be unconditionally (i.e. ignoring the top-m operation) added as the $( m + 1 )$ )-th object to its set of context objects with the similarity score $\boldsymbol { \mathcal { S } } ( \widetilde { \boldsymbol { x } } , \widetilde { \boldsymbol { x } } )$

3. Dropout is applied to the weights produced by the softmax function.

4. We use $m = 9 6$ (ablated in subsection A.6) and, unless otherwise noted, $I _ { c a n d } = I _ { t r a i n }$

Now, we iterate over possible designs of the similarity module $s$ and the value module V (introduced in Figure 4). During this process, we do not use embeddings for numerical features (Gorishniy et al., 2022) in the Input Module of the encoder E and set $\breve { N } _ { E } = 0 , N _ { P } = 1 ( \mathrm { s e e } \mathrm { F i g u r e } 3 )$

![](images/e591346fefc48217078f9ddea74ef94e88d19be84d78dd897610d39335c339ca.jpg)  
Figure 4: Simplified illustration of the retrieval module R introduced in Figure 2 (the omitted details are provided in the main text). For the target object’s representation ${ \tilde { x } } ,$ the module takes the m nearest neighbors among the candidates $\{ \tilde { x } _ { i } \}$ according to the similarity module $S : ( \mathbb { R } ^ { d } , \mathbb { R } ^ { d } ) $ R and aggregates their values produced by the value module $\mathcal { V } : ( \mathbb { R } ^ { d } , \mathbb { R } ^ { \check { d } } , \mathbb { Y } )  \mathbb { R } ^ { d }$

Step-0. The vanilla-attention-like baseline. The self-attention operation (Vaswani et al., 2017) was often used in prior work to model the interaction between a target object and candidate/context objects (Somepalli et al., 2021; Kossen et al., 2021; Schäfl et al., 2022). Then, instantiating retrieval module R as the vanilla self-attention (modulo the top-m operation) is a reasonable baseline:

$$
\mathcal {S} (\tilde {x}, \tilde {x} _ {i}) = W _ {Q} (\tilde {x}) ^ {T} W _ {K} (\tilde {x} _ {i}) \cdot d ^ {- 1 / 2} \qquad \mathcal {V} (\tilde {x}, \tilde {x} _ {i}, y _ {i}) = W _ {V} (\tilde {x} _ {i})\tag{1}
$$

where $W _ { Q } , W _ { K }$ , and $W _ { V }$ are linear layers, and the target object is added as the $( m + 1 )$ -th object to its own context (i.e., ignoring the top-m operation). As reported in Table 2, the Step-0 configuration performs similarly to MLP, which means that using the vanilla self-attention is a suboptimal strategy.

Step-1. Adding context labels. A natural attempt to improve the Step-0 configuration is to utilize labels of the context objects, for example, by incorporating them into the value module as follows:

$$
\mathcal {S} (\tilde {x}, \tilde {x} _ {i}) = W _ {Q} (\tilde {x}) ^ {T} W _ {K} (\tilde {x} _ {i}) \cdot d ^ {- 1 / 2} \qquad \mathcal {V} (\tilde {x}, \tilde {x} _ {i}, y _ {i}) = \underline {{W _ {Y} (y _ {i}) +}} W _ {V} (\tilde {x} _ {i})\tag{2}
$$

where the difference with Equation 1 is the underlined addition of $W _ { Y } : \mathbb { Y } \to \mathbb { R } ^ { d }$ , which is an embedding table for classification tasks and a linear layer for regression tasks. Table 2 shows no improvements from using labels, which is counter-intuitive. Perhaps, the similarity module $s$ taken from the vanilla attention does not allow benefiting from such a valuable signal as labels.

Step-2. Improving the similarity module S. Empirically, we observed that removing the notion of queries (i.e. removing $W _ { Q } )$ and using the $L _ { 2 }$ distance instead of the dot product significantly improves performance on several datasets in Table 2 (subsection A.1 provides more discussion):

$$
\mathcal {S} (\tilde {x}, \tilde {x} _ {i}) = - \| W _ {K} (\tilde {x}) - W _ {K} (\tilde {x} _ {i}) \| ^ {2} \cdot d ^ {- 1 / 2} \quad \mathcal {V} (\tilde {x}, \tilde {x} _ {i}, y _ {i}) = W _ {Y} (y _ {i}) + W _ {V} (\tilde {x} _ {i})\tag{3}
$$

where the difference with Equation 2 is underlined. This change is a turning point in our story, which was overlooked in prior work. Crucially, in subsection A.3, we show that removing any of the three ingredients (context labels, key-only representation, $L _ { 2 }$ distance) results in a performance drop back to the level of MLP. While the $L _ { 2 }$ distance is unlikely to be the universally best choice (even within the tabular domain), it seems to be a reasonable default choice for tabular data problems.

Step-3. Improving the value module V. After improving $s$ on Step-2, we turn to the value module V. Inspired by DNNR (Nader et al., 2022) – the recently proposed generalization of the kNN algorithm, we make V more expressive by taking the target object’s representation x˜ into account:

$$
\mathcal {S} (\tilde {x}, \tilde {x} _ {i}) = - \| W _ {K} (\tilde {x}) - W _ {K} (\tilde {x} _ {i}) \| ^ {2} \cdot d ^ {- 1 / 2} \mathcal {V} (\tilde {x}, \tilde {x} _ {i}, y _ {i}) = W _ {Y} (y _ {i}) + \underline {{T (W _ {K} (\tilde {x}) - W _ {K} (\tilde {x} _ {i}))}}\tag{4}
$$

$$
T (\cdot) = \text { LinearWithoutBias } (\text { Dropout } (\text { ReLU } (\text { Linear } (\cdot))))
$$

where the difference with Equation 3 is underlined. Table 2 shows that the new value module further improves the performance on several datasets. Intuitively, the term $W _ { Y } ( y _ { i } )$ (the embedding of the context object’s label) can be seen as the “raw” contribution of the i-th context object. The term $T ( W _ { K } ( \tilde { x } ) \dot { - } W _ { K } ( \tilde { x } _ { i } ) )$ can be seen as the “correction” term, where the module $\bar { T }$ translates the differences in the key space into the differences in the label embedding space. We provide further analysis on the new value module in subsection A.2.

Table 2: The performance of the implementations of the retrieval module R, described in subsection 3.2. If a number is underlined, then it is better than the corresponding number from the previous step at least by the standard deviation. Noticeable improvements over MLP start at Step-2. Notation: ↓ corresponds to RMSE, ↑ corresponds to accuracy.

<table><tr><td></td><td>CH ↑</td><td>CA ↓</td><td>HO ↓</td><td>AD ↑</td><td>DI ↓</td><td>OT ↑</td><td>HI ↑</td><td>BL ↓</td><td>WE ↓</td><td>CO ↑</td></tr><tr><td>MLP</td><td>0.854</td><td>0.499</td><td>3.112</td><td>0.853</td><td>0.140</td><td>0.816</td><td>0.719</td><td>0.697</td><td>1.905</td><td>0.963</td></tr><tr><td>(Step-0) The vanilla attention baseline</td><td>0.855</td><td>0.484</td><td>3.234</td><td>0.857</td><td>0.142</td><td>0.814</td><td>0.719</td><td>0.699</td><td>1.903</td><td>0.957</td></tr><tr><td>(Step-1) + Context labels</td><td>0.855</td><td>0.489</td><td>3.205</td><td>0.857</td><td>0.142</td><td>0.814</td><td>0.719</td><td>0.698</td><td>1.906</td><td>0.960</td></tr><tr><td>(Step-2) + New similarity module S</td><td>0.860</td><td>0.418</td><td>3.153</td><td>0.858</td><td>0.140</td><td>0.813</td><td>0.720</td><td>0.692</td><td>1.804</td><td>0.972</td></tr><tr><td>(Step-3) + New value module V</td><td>0.859</td><td>0.408</td><td>3.158</td><td>0.863</td><td>0.135</td><td>0.810</td><td>0.722</td><td>0.692</td><td>1.814</td><td>0.975</td></tr><tr><td>(Step-4) + Technical tweaks = TabR</td><td>0.860</td><td>0.403</td><td>3.067</td><td>0.865</td><td>0.133</td><td>0.818</td><td>0.722</td><td>0.690</td><td>1.747</td><td>0.973</td></tr></table>

Step-4. TabR. Finally, empirically, we observed that omitting the scaling term $d ^ { - 1 / 2 }$ in the similarity module and not including the target object to its own context leads to better results on average as reported in Table 2. Both aspects can be considered hyperparameters, and the above notes can be seen as our default recommendations. We call the obtained model “TabR” (Tab ∼ tabular, R ∼ retrieval). The formal complete description of how TabR implements the retrieval module R is as follows:

$$
k = W _ {K} (\tilde {x}), k _ {i} = W _ {K} (\tilde {x} _ {i}) \quad \mathcal {S} (\tilde {x}, \tilde {x} _ {i}) = - \| k - k _ {i} \| ^ {2} \quad \mathcal {V} (\tilde {x}, \tilde {x} _ {i}, y _ {i}) = W _ {Y} (y _ {i}) + T (k - k _ {i})\tag{5}
$$

where $W _ { K }$ is a linear layer, $W _ { Y }$ is an embedding table for classification tasks and a linear layer for regression tasks, (by default) a target object is not included in its own context, (by default) the similarity scores are not scaled, and $T ( \cdot ) \stackrel { } { = } \mathtt { L i n e a r w i t h o u t B i a s } \big ( \mathtt { D r o p o u t } \big ( \mathtt { R e L U } \big ( \mathtt { L i n e a r } ( \cdot ) \big ) \big ) \big )$

Limitations. TabR has standard limitations of retrieval-augmented models, which we describe in Appendix B. We encourage practitioners to review the limitations before using TabR in practice.

## 4 EXPERIMENTS ON PUBLIC BENCHMARKS

In this section, we compare TabR (introduced in section 3) with existing retrieval-based solutions and state-of-the-art parametric models. In addition to the fully-fledged configuration of TabR (with all degrees of freedom available for E and P as described in Figure 3), we also use TabR-S $\mathrm { ( ^ { 6 6 } S ^ { , 9 } }$ stands for “simple”) – a simple configuration, which does not use feature embeddings (Gorishniy et al., 2022), has a linear encoder $( N _ { E } = 0 )$ and a one-block predictor $( N _ { P } = 1 )$ . We specify when TabR-S is used only in tables, figures, and captions but not in the text. For other details on TabR, including hyperparameter tuning, see subsection D.8.

## 4.1 EVALUATING RETRIEVAL-AUGMENTED DEEP LEARNING MODELS FOR TABULAR DATA

In this section, we compare TabR (section 3) and the existing retrieval-augmented solutions with fully parametric DL models (see Appendix D for implementation details for all algorithms). Table 3 indicates that TabR is the only retrieval-based model that provides a significant performance boost over MLP on many datasets. In particular, the full variation of TabR outperforms MLP-PLR (the modern parametric DL model with the highest average rank from Gorishniy et al. (2022)) on several datasets (CA, OT, BL, WE, CO), and performs on par with it on the rest except for the MI dataset. Regarding the prior retrieval-based solutions, we faced various technical limitations, such as incompatibility with classification problems and scaling issues (e.g., as we show in subsubsection A.4.1, it takes dramatically less time to train TabR than NPT (Kossen et al., 2021) – the closest retrieval-based competitor in Table 3). Notably, the retrieval component is not universally beneficial for all datasets.

The obtained results highlight the retrieval technique and embeddings for numerical features (Gorishniy et al., 2022) (used in MLP-PLR and TabR) as two powerful architectural elements that improve the optimization properties of tabular DL models. Interestingly, the two techniques are not fully orthogonal, but none of them can recover the full power of the other, and it depends on a given dataset whether one should prefer the retrieval, the embeddings, or a combination of both.

The main takeaway. TabR becomes a new strong deep learning solution for tabular data problems and demonstrates a good potential of the retrieval-based approach. TabR demonstrates strong average performance and achieves the new state-of-the-art on several datasets.

Table 3: Comparing TabR with existing retrieval-augmented tabular models and parametric DL models. The notation follows Table 2. The bold entries are the best-performing algorithms, which are defined with standard deviations taken into account as described in subsection D.6.

<table><tr><td></td><td>CH ↑</td><td>CA ↓</td><td>HO ↓</td><td>AD ↑</td><td>DI ↓</td><td>OT ↑</td><td>HI ↑</td><td>BL ↓</td><td>WE ↓</td><td>CO ↑</td><td>MI ↓</td><td>Avg. Rank</td></tr><tr><td>kNN</td><td>0.837</td><td>0.588</td><td>3.744</td><td>0.834</td><td>0.256</td><td>0.774</td><td>0.665</td><td>0.712</td><td>2.296</td><td>0.927</td><td>0.764</td><td>6.0 ± 1.7</td></tr><tr><td>DNNR (Nader et al., 2022)</td><td>-</td><td>0.430</td><td>3.210</td><td>-</td><td>0.145</td><td>-</td><td>-</td><td>0.704</td><td>1.913</td><td>-</td><td>0.765</td><td>4.8 ± 1.9</td></tr><tr><td>DKL (Wilson et al., 2016)</td><td>-</td><td>0.521</td><td>3.423</td><td>-</td><td>0.147</td><td>-</td><td>-</td><td>0.699</td><td>-</td><td>-</td><td>-</td><td>6.2 ± 0.5</td></tr><tr><td>ANP (Kim et al., 2019)</td><td>-</td><td>0.472</td><td>3.162</td><td>-</td><td>0.140</td><td>-</td><td>-</td><td>0.705</td><td>1.902</td><td>-</td><td>-</td><td>4.6 ± 2.5</td></tr><tr><td>SAINT (Somepalli et al., 2021)</td><td>0.860</td><td>0.468</td><td>3.242</td><td>0.860</td><td>0.137</td><td>0.812</td><td>0.724</td><td>0.693</td><td>1.933</td><td>0.964</td><td>0.763</td><td>3.8 ± 1.5</td></tr><tr><td>NPT (Kossen et al., 2021)</td><td>0.858</td><td>0.474</td><td>3.175</td><td>0.853</td><td>0.138</td><td>0.815</td><td>0.721</td><td>0.692</td><td>1.947</td><td>0.966</td><td>0.753</td><td>3.6 ± 1.0</td></tr><tr><td>MLP</td><td>0.854</td><td>0.499</td><td>3.112</td><td>0.853</td><td>0.140</td><td>0.816</td><td>0.719</td><td>0.697</td><td>1.905</td><td>0.963</td><td>0.748</td><td>3.7 ± 1.3</td></tr><tr><td>MLP-PLR</td><td>0.860</td><td>0.476</td><td>3.056</td><td>0.870</td><td>0.134</td><td>0.819</td><td>0.729</td><td>0.687</td><td>1.860</td><td>0.970</td><td>0.744</td><td>2.0 ± 1.0</td></tr><tr><td>TabR-S</td><td>0.860</td><td>0.403</td><td>3.067</td><td>0.865</td><td>0.133</td><td>0.818</td><td>0.722</td><td>0.690</td><td>1.747</td><td>0.973</td><td>0.750</td><td>1.9 ± 0.7</td></tr><tr><td>TabR</td><td>0.862</td><td>0.400</td><td>3.105</td><td>0.870</td><td>0.133</td><td>0.825</td><td>0.729</td><td>0.676</td><td>1.690</td><td>0.976</td><td>0.750</td><td>1.3 ± 0.6</td></tr></table>

## 4.2 COMPARING TABR WITH GRADIENT-BOOSTED DECISION TREES

In this section, we compare TabR with models based on gradient-boosted decision trees (GBDT): XGBoost (Chen and Guestrin, 2016), LightGBM (Ke et al., 2017) and CatBoost (Prokhorenkova et al., 2018). Specifically, we compare ensembles (e.g. an ensemble of TabRs vs. an ensemble of XGBoosts) for a fair comparison since gradient boosting is already an ensembling technique.

The default benchmark. Table 4 shows that, on the default benchmark, the tuned TabR provides noticeable improvements over tuned GBDT on several datasets (CH, CA, HO, HI, WE, CO), while being competitive on the rest, except for the MI dataset. The table also demonstrates that TabR has a competitive default configuration (defined in subsection D.8).

The benchmark from Grinsztajn et al. (2022). Now, we go further and use the recently proposed benchmark with small-to-middle-scale tasks Grinsztajn et al. (2022). Importantly, this benchmark was originally used to illustrate the superiority of GBDT over parametric DL models on datasets with ≤ 50K objects, which makes it an interesting challenge for TabR. We adjust the benchmark to our tuning and evaluation protocols (see subsection C.2 for details) and report the results in Table 5. While MLP-PLR (one of the best parametric DL models) indeed is slightly inferior to GBDT on this set of tasks, TabR makes a significant step forward and outperforms GBDT on average.

Additional analysis: in subsection A.5, we try augmenting XGBoost with a retrieval component; in subsection A.4, we compare training times and batch inference efficiency of TabR and GBDT models.

The main takeaway. After the comparison with GBDT, TabR confirms its status of a new strong solution for tabular data problems: it provides strong average performance and can provide a noticeable improvement over GBDT on some datasets.

Table 4: Comparing ensembles of TabR with ensembles of GBDT models. See subsection D.8 to learn how the “default” TabR-S was obtained. The notation follows Table 3.

<table><tr><td></td><td>CH ↑</td><td>CA ↓</td><td>HO ↓</td><td>AD ↑</td><td>DI ↓</td><td>OT ↑</td><td>HI ↑</td><td>BL ↓</td><td>WE ↓</td><td>CO ↑</td><td>MI ↓</td><td>Avg. Rank</td></tr><tr><td colspan="13">Tuned hyperparameters</td></tr><tr><td>XGBoost</td><td>0.861</td><td>0.432</td><td>3.164</td><td>0.872</td><td>0.136</td><td>0.832</td><td>0.726</td><td>0.680</td><td>1.769</td><td>0.971</td><td>0.741</td><td>2.5 ± 0.9</td></tr><tr><td>CatBoost</td><td>0.859</td><td>0.426</td><td>3.106</td><td>0.872</td><td>0.133</td><td>0.827</td><td>0.727</td><td>0.681</td><td>1.773</td><td>0.969</td><td>0.741</td><td>2.5 ± 1.1</td></tr><tr><td>LightGBM</td><td>0.860</td><td>0.434</td><td>3.167</td><td>0.872</td><td>0.136</td><td>0.832</td><td>0.726</td><td>0.679</td><td>1.761</td><td>0.971</td><td>0.741</td><td>2.4 ± 0.9</td></tr><tr><td>TabR</td><td>0.865</td><td>0.391</td><td>3.025</td><td>0.872</td><td>0.131</td><td>0.831</td><td>0.733</td><td>0.674</td><td>1.661</td><td>0.977</td><td>0.748</td><td>1.3 ± 0.9</td></tr><tr><td colspan="13">Default hyperparameters</td></tr><tr><td>XGBoost</td><td>0.856</td><td>0.471</td><td>3.368</td><td>0.871</td><td>0.143</td><td>0.817</td><td>0.716</td><td>0.683</td><td>1.920</td><td>0.966</td><td>0.750</td><td>3.4 ± 0.9</td></tr><tr><td>CatBoost</td><td>0.861</td><td>0.432</td><td>3.108</td><td>0.874</td><td>0.132</td><td>0.822</td><td>0.726</td><td>0.684</td><td>1.886</td><td>0.924</td><td>0.744</td><td>2.1 ± 0.8</td></tr><tr><td>LightGBM</td><td>0.856</td><td>0.449</td><td>3.222</td><td>0.869</td><td>0.137</td><td>0.826</td><td>0.720</td><td>0.681</td><td>1.817</td><td>0.899</td><td>0.744</td><td>2.5 ± 0.9</td></tr><tr><td>TabR-S</td><td>0.864</td><td>0.398</td><td>2.971</td><td>0.859</td><td>0.131</td><td>0.824</td><td>0.724</td><td>0.688</td><td>1.721</td><td>0.974</td><td>0.752</td><td>2.0 ± 1.3</td></tr></table>

Table 5: Comparing ensembles of DL models with ensembles of GBDT models on the benchmark from Grinsztajn et al. (2022) (e.g., an ensemble of MLPs vs ensemble of XGBoosts; note that in Figure 1, we compare single models, hence the different numbers). See subsection D.8 for the details on the “default” TabR-S. The default configuration of TabR-S is compared against the default configurations of GBDT models. The comparison is performed in a pairwise manner with standard deviations taken into account as described in subsection D.6.

<table><tr><td rowspan="2"></td><td colspan="3">vs. XGBoost</td><td colspan="3">vs. CatBoost</td><td colspan="3">vs. LightGBM</td></tr><tr><td>Win /</td><td>Tie /</td><td>Loss</td><td>Win /</td><td>Tie /</td><td>Loss</td><td>Win /</td><td>Tie /</td><td>Loss</td></tr><tr><td colspan="10">Tuned hyperparameters</td></tr><tr><td>MLP</td><td>6</td><td>11</td><td>26</td><td>6</td><td>8</td><td>29</td><td>5</td><td>11</td><td>27</td></tr><tr><td>MLP-PLR</td><td>12</td><td>17</td><td>14</td><td>10</td><td>11</td><td>22</td><td>14</td><td>15</td><td>14</td></tr><tr><td>TabR-S</td><td>21</td><td>13</td><td>9</td><td>17</td><td>11</td><td>15</td><td>21</td><td>15</td><td>7</td></tr><tr><td>TabR</td><td>26</td><td>14</td><td>3</td><td>23</td><td>13</td><td>7</td><td>26</td><td>14</td><td>3</td></tr><tr><td colspan="10">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>28</td><td>10</td><td>5</td><td>17</td><td>16</td><td>10</td><td>25</td><td>9</td><td>9</td></tr></table>

## 5 ANALYSIS

## 5.1 FREEZING CONTEXTS FOR FASTER TRAINING OF TABR

In the vanilla formulation of TabR (section 3), for each training batch, the most up-to-date contexts are mined by encoding all the candidates and computing similarities with all of them, which can be prohibitively slow on large datasets. For example, it takes more than 18 hours to train a single TabR on the full “Weather prediction” dataset (Malinin et al., 2021) (3M+ objects; with the default hyperparameters from Table 4). However, as we show in Figure 5, for an average training object, its context (i.e. the top-m candidates and the distribution over them according to the similarity module S) gradually “stabilizes” during the course of training, which gives an opportunity for simple optimization. Namely, after a fixed number of epochs, we can perform “context freeze”: i.e., compute the up-to-date contexts for all training (but not validation and test) objects for the one last time and then reuse these contexts for the rest of the training. Table 6 indicates that, on some datasets, this simple technique allows accelerating training of TabR without much loss in metrics, with more noticeable speedups on larger datasets. In particular, on the full “Weather prediction” dataset, we achieve nearly sevenfold speedup (from 18h9min to 3h15min) while maintaining competitive RMSE. See subsection D.2 for implementation details.

Table 6: The performance of TabR-S with the “context freeze” as described in subsection 5.1. TabR-S (CF-N) denotes TabR-S with the context freeze applied after N epochs. In parentheses, we provide the fraction of time spent on training compared to the training without freezing (the last row).

<table><tr><td></td><td>CA ↓</td><td>DI ↓</td><td>HI ↑</td><td>BL ↓</td><td>WE ↓</td><td>CO ↑</td><td>WE (full) ↓</td></tr><tr><td>TabR-S (CF-1)</td><td>0.414 (0.72)</td><td>0.137 (0.47)</td><td>0.718 (0.80)</td><td>0.692 (0.61)</td><td>1.770 (0.57)</td><td>0.973 (0.49)</td><td>1.325 (0.13)</td></tr><tr><td>TabR-S (CF-4)</td><td>0.409 (0.71)</td><td>0.136 (0.51)</td><td>0.717 (0.73)</td><td>0.691 (0.62)</td><td>1.763 (0.56)</td><td>0.973 (0.59)</td><td>-</td></tr><tr><td>TabR-S</td><td>0.406 (1.00)</td><td>0.133 (1.00)</td><td>0.719 (1.00)</td><td>0.691 (1.00)</td><td>1.755 (1.00)</td><td>0.973 (1.00)</td><td>1.315 (1.00)</td></tr></table>

## 5.2 UPDATING TABR WITH NEW TRAINING DATA WITHOUT RETRAINING

Getting access to new unseen training data after training a machine learning model (e.g., after collecting yet another portion of daily logs of an application) is a common practical scenario. Technically, TabR allows utilizing the new data without retraining by adding the new data to the set of candidates for retrieval. We test this approach on the full “Weather prediction” dataset (Malinin et al., 2021) (3M+ objects). Figure 6 indicates that such “online updates” may be a viable solution for incorporating new data into an already trained TabR. Additionally, this approach can be used to scale TabR to large datasets by training the model on a subset of data and retrieving from the full data. Overall, we consider the conducted experiment as a preliminary exploration and leave a systematic study of continual updates for future work. See subsection D.3 for implementation details.

![](images/d03fd7a863d5c83810e36a12884183bde59349ff5203f2b0a4fb3a3cf41e50eb.jpg)

![](images/6eb3c8deb209d3b00358b817e4fc30f73181046e6c8c7878b376e0830630e533.jpg)  
% of training data used as candidates on inference  
Figure 5: ∆-context (explained below) averaged over training objects until the early stopping while training TabR-S. On a given epoch, for a given object, ∆-context shows the portion of its context (the top-m candidates and their weights) changed compared to the previous epoch (i.e., the lower the value, the smaller the change; see subsection D.2 for formal details). The plot shows that context updates become less intensive during the course of training, which motivates the optimization described in subsection 5.1.  
Figure 6: Training TabR-S on various portions of the training data of the full “Weather prediction” dataset and gradually adding the remaining unseen training data to the set of candidates with out retraining as described in subsection 5.2. For each curve, the leftmost point corresponds to not adding any new data to the set of candidates after the training, and the rightmost point corresponds to adding all unseen training data to the set of candidates.

## 5.3 FURTHER ANALYSIS

In the appendix, we provide a more insightful analysis. A non-exhaustive list of examples:

• in subsection A.1, we analyze the key-only $L _ { 2 } \cdot$ -based similarity module S introduced on Step-2 of subsection 3.2, which was a turning point in our story. We provide intuition behind this specific implementation of S and perform an in-depth comparison with the similarity module of the vanilla attention (the dot product between queries and keys).

• in subsection A.2, we analyze the value module V introduced on Step-3 of subsection 3.2. On regression problems, we confirm the correction semantics of the module T from Equation 4.

• in subsubsection A.4.1, we compare training times of TabR with training times of all the baselines. We show that compared to prior retrieval-based tabular models, TabR makes a big step forward in terms of efficiency. While TabR is relatively slower than simple retrieval-free models, within the considered scope of dataset sizes, the absolute training times of TabR are affordable for most practical scenarios.

• in subsection A.8, we highlight additional technical properties of TabR.

## 6 CONCLUSION & FUTURE WORK

In this work, we have demonstrated that retrieval-based deep learning models have great potential in supervised machine learning problems on tabular data. Namely, we have designed TabR – a retrieval-augmented tabular DL architecture that provides strong average performance and achieves the new state-of-the-art on several datasets. Importantly, we have highlighted similarity and value modules as the important details of the attention mechanism which have a significant impact on the performance of attention-based retrieval components.

An important direction for future work is improving the efficiency of retrieval-augmented models to make them faster in general and in particular applicable to tens and hundreds of millions of data points. Also, in this paper, we focused more on the aspect of task performance, so some other properties of TabR remain underexplored. For example, the retrieval nature of TabR provides new opportunities for interpreting the model’s predictions through the influence of context objects. Also, TabR may enable better support for continual learning (we scratched the surface of this direction in subsection 5.2). Regarding architecture details, possible directions are improving similarity and value modules, as well as performing multiple rounds of retrieval and interactions with the retrieved instances.

## REPRODUCIBILITY STATEMENT

To make the results and models reproducible and verifiable, we provide our full codebase, all the results, and step-by-step usage instructions: link. In particular, (1) the results and hyperparameters reported the paper is just a summary of the results available at the provided URL (with minor exceptions); (2) implementations of TabR and all the baselines (except for NPT) are available; (3) the hyperparameter tuning, training and evaluation pipelines are available; (4) the hyperparameters are available; (5) the used datasets and splits are available; (6) hyperparameter tuning and training times are available; (7) the used hardware is available; (8) within afixed environment (i.e. fixed hardware and software versions), most of the results are bitwise reproducible.

## REFERENCES

T. Akiba, S. Sano, T. Yanase, T. Ohta, and M. Koyama. Optuna: A next-generation hyperparameter optimization framework. In KDD, 2019. 23, 24, 27, 28, 29, 30

J. L. Ba, J. R. Kiros, and G. E. Hinton. Layer normalization. arXiv, 1607.06450v1, 2016. 4

D. Bahri, H. Jiang, Y. Tay, and D. Metzler. Scarf: Self-supervised contrastive learning using random feature corruption. In ICLR, 2021. 2

P. Baldi, P. Sadowski, and D. Whiteson. Searching for exotic particles in high-energy physics with deep learning. Nature Communications, 5, 2014. 20

J. A. Blackard and D. J. Dean. Comparative accuracies of artificial neural networks and discriminant analysis in predicting forest cover types from cartographic variables. Computers and Electronics in Agriculture, 24(3):131–151, 2000. 20

S. Borgeaud, A. Mensch, J. Hoffmann, T. Cai, E. Rutherford, K. Millican, G. van den Driessche, J. Lespiau, B. Damoc, A. Clark, D. de Las Casas, A. Guy, J. Menick, R. Ring, T. Hennigan, S. Huang, L. Maggiore, C. Jones, A. Cassirer, A. Brock, M. Paganini, G. Irving, O. Vinyals, S. Osindero, K. Simonyan, J. W. Rae, E. Elsen, and L. Sifre. Improving language models by retrieving from trillions of tokens. In ICML, 2022. 2

L. Bottou and V. Vapnik. Local learning algorithms. Neural Computation, 4, 1992. 2

T. Chen and C. Guestrin. Xgboost: A scalable tree boosting system. In SIGKDD, 2016. 1, 7

R. Das, M. Zaheer, D. Thai, A. Godbole, E. Perez, J. Y. Lee, L. Tan, L. Polymenakos, and A. McCallum. Case-based reasoning for natural language queries over knowledge bases. In EMNLP, 2021. 2

K. Du, W. Zhang, R. Zhou, Y. Wang, X. Zhao, J. Jin, Q. Gan, Z. Zhang, and D. P. Wipf. Learning enhanced representation for tabular data via neighborhood propagation. In NeurIPS, 2022. 2

J. R. Gardner, G. Pleiss, D. Bindel, K. Q. Weinberger, and A. G. Wilson. Gpytorch: Blackbox matrixmatrix gaussian process inference with gpu acceleration. In Advances in Neural Information Processing Systems, 2018. 26

Y. Gorishniy, I. Rubachev, V. Khrulkov, and A. Babenko. Revisiting deep learning models for tabular data. In NeurIPS, 2021. 1, 2, 20, 28, 29

Y. Gorishniy, I. Rubachev, and A. Babenko. On embeddings for numerical features in tabular deep learning. In NeurIPS, 2022. 1, 2, 3, 4, 6, 14, 20, 22, 24, 28, 29

L. Grinsztajn, E. Oyallon, and G. Varoquaux. Why do tree-based models still outperform deep learning on typical tabular data? In NeurIPS, the "Datasets and Benchmarks" track, 2022. 1, 2, 3, 7, 8, 20, 23, 24, 30, 33

K. Guu, K. Lee, Z. Tung, P. Pasupat, and M. Chang. Retrieval augmented language model pre-training. In ICML, 2020. 2

H. Hazimeh, N. Ponomareva, P. Mol, Z. Tan, and R. Mazumder. The tree ensemble layer: Differentiability meets conditional computation. In ICML, 2020. 1

N. Hollmann, S. Müller, K. Eggensperger, and F. Hutter. Tabpfn: A transformer that solves small tabular classification problems in a second. In ICLR, 2023. 2

X. Huang, A. Khetan, M. Cvitkovic, and Z. Karnin. Tabtransformer: Tabular data modeling using contextual embeddings. arXiv, 2012.06678v1, 2020. 1

A. Iscen, T. Bird, M. Caron, A. Fathi, and C. Schmid. A memory transformer network for incremental learning. arXiv, abs/2210.04485v1, 2022. 2

G. Izacard, P. S. H. Lewis, M. Lomeli, L. Hosseini, F. Petroni, T. Schick, J. Dwivedi-Yu, A. Joulin, S. Riedel, and E. Grave. Few-shot learning with retrieval augmented language models. arXiv, abs/2208.03299v3, 2022. 2

G. James, D. Witten, T. Hastie, and R. Tibshirani. An Introduction to Statistical Learning. Springer, 2013. https://www.statlearning.com/. 2

A. Jeffares, T. Liu, J. Crabbé, F. Imrie, and M. van der Schaar. Tangos: Regularizing tabular neural networks through gradient orthogonalization and specialization. In ICLR, 2023. 2

M. Jia, B.-C. Chen, Z. Wu, C. Cardie, S. Belongie, and S.-N. Lim. Rethinking nearest neighbors for visual classification. arXiv preprint arXiv:2112.08459, 2021. 2

A. Kadra, M. Lindauer, F. Hutter, and J. Grabocka. Well-tuned simple nets excel on tabular datasets. In NeurIPS, 2021. 2

G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, and T.-Y. Liu. Lightgbm: A highly efficient gradient boosting decision tree. Advances in neural information processing systems, 30: 3146–3154, 2017. 7

R. Kelley Pace and R. Barry. Sparse spatial autoregressions. Statistics & Probability Letters, 33(3): 291–297, 1997. 19

U. Khandelwal, O. Levy, D. Jurafsky, L. Zettlemoyer, and M. Lewis. Generalization through memorization: Nearest neighbor language models. In ICLR, 2020. 2

H. Kim, A. Mnih, J. Schwarz, M. Garnelo, S. M. A. Eslami, D. Rosenbaum, O. Vinyals, and Y. W. Teh. Attentive neural processes. In ICLR, 2019. 2, 7, 26

G. Klambauer, T. Unterthiner, A. Mayr, and S. Hochreiter. Self-normalizing neural networks. In NIPS, 2017. 1, 2

R. Kohavi. Scaling up the accuracy of naive-bayes classifiers: a decision-tree hybrid. In KDD, 1996. 20

J. Kossen, N. Band, C. Lyle, A. N. Gomez, T. Rainforth, and Y. Gal. Self-attention between datapoints: Going beyond individual input-output pairs in deep learning. In NeurIPS, 2021. 1, 2, 3, 5, 6, 7, 16, 27

P. S. H. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Yih, T. Rocktäschel, S. Riedel, and D. Kiela. Retrieval-augmented generation for knowledge-intensive NLP tasks. In NeurIPS, 2020. 2

A. Long, W. Yin, T. Ajanthan, V. Nguyen, P. Purkait, R. Garg, A. Blair, C. Shen, and A. van den Hengel. Retrieval augmented classification for long-tail visual recognition. In CVPR, 2022. 2

I. Loshchilov and F. Hutter. Decoupled weight decay regularization. In ICLR, 2019. 22

A. Malinin, N. Band, G. Chesnokov, Y. Gal, M. J. F. Gales, A. Noskov, A. Ploskonosov, L. Prokhorenkova, I. Provilkov, V. Raina, V. Raina, M. Shmatova, P. Tigas, and B. Yangel. Shifts: A dataset of real distributional shift across multiple large-scale tasks. ArXiv, abs/2107.07455v3, 2021. 8, 20

Y. Nader, L. Sixt, and T. Landgraf. Dnnr: Differential nearest neighbors regression. In ICML, 2022. 2, 5, 7, 14

F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, M. Blondel, P. Prettenhofer, R. Weiss, V. Dubourg, J. Vanderplas, A. Passos, D. Cournapeau, M. Brucher, M. Perrot, and E. Duchesnay. Scikit-learn: Machine learning in Python. Journal ofMachine Learning Research, 12:2825–2830, 2011. 22

S. Popov, S. Morozov, and A. Babenko. Neural oblivious decision ensembles for deep learning on tabular data. In ICLR, 2020. 1

L. Prokhorenkova, G. Gusev, A. Vorobev, A. V. Dorogush, and A. Gulin. Catboost: unbiased boosting with categorical features. In NeurIPS, 2018. 7

J. Qin, W. Zhang, X. Wu, J. Jin, Y. Fang, and Y. Yu. User behavior retrieval for click-through rate prediction. In SIGIR, 2020. 2

J. Qin, W. Zhang, R. Su, Z. Liu, W. Liu, R. Tang, X. He, and Y. Yu. Retrieval & interaction machine for tabular data prediction. In KDD, 2021. 1, 2

T. Qin and T. Liu. Introducing LETOR 4.0 datasets. arXiv, 1306.2597v1, 2013. 20

H. Ramsauer, B. Schäfl, J. Lehner, P. Seidl, M. Widrich, L. Gruber, M. Holzleitner, T. Adler, D. P. Kreil, M. K. Kopp, G. Klambauer, J. Brandstetter, and S. Hochreiter. Hopfield networks is all you need. In ICLR, 2021. 2, 3

B. Schäfl, L. Gruber, A. Bitto-Nemling, and S. Hochreiter. Hopular: Modern hopfield networks for tabular data. arXiv, abs/2206.00664, 2022. 3, 5, 27

G. Somepalli, M. Goldblum, A. Schwarzschild, C. B. Bruss, and T. Goldstein. SAINT: improved neural networks for tabular data via row attention and contrastive pre-training. arXiv, 2106.01342v1, 2021. 1, 3, 5, 7, 27

J. Vanschoren, J. N. van Rijn, B. Bischl, and L. Torgo. Openml: networked science in machine learning. arXiv, 1407.7722v1, 2014. 20

A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, L. Kaiser, and I. Polosukhin. Attention is all you need. In NIPS, 2017. 5

A. Q. Wang and M. R. Sabuncu. A flexible nadaraya-watson head can offer explainable and calibrated classification. In TMLR, 2023. 2

R. Wang, R. Shivanna, D. Z. Cheng, S. Jain, D. Lin, L. Hong, and E. H. Chi. Dcn v2: Improved deep & cross network and practical lessons for web-scale learning to rank systems. arXiv, 2008.13535v2, 2020. 1, 2

S. Wang, Y. Xu, Y. Fang, Y. Liu, S. Sun, R. Xu, C. Zhu, and M. Zeng. Training data is more valuable than you think: A simple and effective method by retrieving from training data. arXiv preprint arXiv:2203.08773, 2022. 2

A. G. Wilson, Z. Hu, R. Salakhutdinov, and E. P. Xing. Deep kernel learning. In AISTATS, 2016. 2, 7

J. Zhao and K. Cho. Retrieval-augmented convolutional neural networks for improved robustness against adversarial examples. arXiv preprint arXiv:1802.09502, 2018. 2

## SUPPLEMENTARY MATERIAL

## A ADDITIONAL ANALYSIS

## A.1 SIMILARITY MODULE OF TABR

## A.1.1 MOTIVATION

Recall that in Step-2 of subsection 3.2, the change from the similarity module of the vanilla attention to the new key-only L -driven similarity module was a turning point in our story, where a retrievalbased model started showing noticeable improvements over MLP on several datasets. In fact, in addition to the empirical results (in Table 2 and subsection A.3), this specific similarity module has a reasonable intuitive motivation, which we now provide.

• First, aligning two (query and key) representations of target and candidate objects is an additional challenge for the optimization process, and there is no clear motivation for introducing this challenge in our case. And, as demonstrated in subsection A.3, avoiding this challenge is not just beneficial, but rather necessary.

• Second, during the design process in subsection 3.2, the similarity module $s$ operates over linear transformations of the input (because, at that point, encoder E is just a linear layer, since we fixed $N _ { E } = 0 )$ . Then, a reasonable similarity measure in the original feature space may remain reasonable in the transformed feature space. And, for tabular data, $L _ { 2 }$ is usually a better similarity measure than the dot product in the original feature space. Note that the case of shallow/linear encoder is a specific, but very important case: since E is applied to many candidates on each training step, E is better to be lightweight to maintain adequate efficiency.

Combined, the above two points motivate removing query representations and switching to the $L _ { 2 }$ distance, which leads to the similarity module introduced in Step-2 of subsection 3.2.

## A.1.2 ANALYZING ATTENTION PATTERNS OVER CANDIDATES

In this section, we analyze the similarity module S introduced in Step-2 of subsection 3.2, which greatly improved the performance on several datasets in Table 2.

Formally, for a given input object, the similarity module defines a distribution over candidates (“weights” in Figure 4) with exactly m + 1 non-zero entries (m is the context size; +1 comes from adding the target object to its own context in Step-2). Intuitively, the less diverse such distributions are on average, the more frequently different input objects are augmented with similar contexts. In Table 7, we demonstrate that such distributions are more diverse on average with the new similarity module compared to the one from the vanilla attention. The implementation details are provided in subsection D.4.

Table 7: Entropy of the average distribution over candidates (the averaging is performed over individual distributions for test objects). The distributions are produced by the similarity module as explained in subsubsection A.1.2. The trained Step-1 and Step-2 models are taken directly from Table 2. The similarity module introduced at Step-2 of subsection 3.2 produces more diverse contexts.

<table><tr><td></td><td>CH</td><td>CA</td><td>HO</td><td>AD</td><td>DI</td><td>OT</td><td>HI</td><td>WE</td></tr><tr><td>Step-1</td><td>6.6</td><td>6.1</td><td>7.0</td><td>7.1</td><td>5.8</td><td>5.3</td><td>8.5</td><td>8.9</td></tr><tr><td>Step-2</td><td>8.4</td><td>9.0</td><td>9.3</td><td>9.7</td><td>10.3</td><td>10.1</td><td>10.5</td><td>9.5</td></tr><tr><td>Uniform</td><td>8.8</td><td>9.5</td><td>9.6</td><td>10.2</td><td>10.4</td><td>10.6</td><td>11.0</td><td>12.6</td></tr></table>

## A.1.3 CASE STUDIES

In this section, we consider three datasets where the transition to the key-only $L _ { 2 }$ similarity module from the vanilla dot-product-between-queries-and-keys demonstrated the most impressive performance. Formally, this is the transition from “Step-1” to “Step-2” in Table 2. For each of the three datasets, first, we notice that, for a given input object, there is a domain-specific notion of “good neighbors”, i.e., such neighbors that, from a human perspective, are very relevant to the input object and provide strong hints for making a better prediction for the input object. Then, we show that the new similarity module allows finding and exploiting those natural hints.

California housing (CA). On this dataset, the transition from the “vanilla” dot-product-betweenqueries-and-keys similarity module to the key-only $L _ { 2 }$ similarity module resulted in a substantial performance boost, as indicated by the difference between “Step-1” and “Step-2” in Table 2. On this dataset, the task is to estimate the prices of houses in California. Intuitively, for a given house from the test set, the prices of the training houses in the geographical neighborhood should be a strong hint for solving the task. Moreover, there are coordinates (longitude and latitude) among the features, which should simplify finding good neighbors. And the “Step-2” model successfully does that, which is not true for the “Step-1” model. Specifically, for an average test object, the “Step-2” model concentrates approximately 7% of the attention mass on the object itself (recall that “Step-2” includes the target object in the context objects) and approximately 77% on the context objects within the 10km radius. The corresponding numbers of the “Step-1” model are 0.07% and 1%.

Weather prediction (WE). Here, the story is seemingly similar to the one with the CA dataset analyzed in the previous paragraph, but in fact has a major difference. Again, here, for a given test data point, the dataset contains natural hints in the form of geographical neighbors from the training set which allow making a better weather forecast for a test query; and the “Step-2” model (Table 2) successfully exploits that, while the “Step-1” model cannot pay any meaningful attention to those hints. Specifically, for an average object, the “Step-2” model concentrates approximately 29% of the attention mass on the object itself (recall that “Step-2” includes the target object in the context objects) and approximately 25% on the context objects within the 200km radius. The corresponding numbers of the “Step-1” model are 0.25% and 0.5%. However, there is a crucial distinction from the CA case: in the version of the dataset WE that we used, thefeatures did not contain the coordinates. In other words, to perform the analysis, after the training, we restored the original coordinates for each row from the original dataset and observed that the model learned the “correct” notion of “good neighbors” from other features.

Facebook comments volume (FB). In this paper, this is the first time when we mention this dataset, which was used in prior work (Gorishniy et al., 2022) and which we also used for some time in this project. Notably, on this dataset, TabR was demonstrating unthinkable improvements over competitors (including GBDT and the best-in-class parametric DL models). Then we noticed a strange pattern: often, for a given input, TabR concentrated an abnormally high percentage of its attention mass on just one context object (a different one for each input object). This is how we discovered that the dataset split that we inherited from Gorishniy et al. (2022) contained a “leak”: roughly speaking, for many objects, it was possible to find their almost exact copies in the training set, and the task was dramatically simpler with this kind of hint. In practice, it was dramatically simpler for the TabR, but not for other models. Specifically, for an average object, the “Step-2” model concentrates approximately 20% of the attention mass on the object itself (recall that “Step-2” includes the target object in the context objects) and approximately 35% on its leaked almost-copies. The corresponding numbers of the “Step-1” model are 0.5% and 0.09%.

## A.2 ANALYZING THE VALUE MODULE OF TABR

In this section, we analyze the value module V of TabR (see Equation 5).

## A.2.1 MOTIVATION

Formally, we note that the output of the value module V of the vanilla attention (as defined in Equation 3, that is, before the Step-3 modification) does not depend on the target object representation x˜. This gives an opportunity for making V more expressive by taking x˜ into account. While there are numerous technical ways to use this opportunity, we decide to take inspiration from DNNR (Nader et al., 2022) – the recently proposed generalization of the kNN algorithm for regression problems.

Conceptually, while kNN captures only local label distributions, DNNR also captures local trends (formally, derivatives). Technically, contrary to kNN, in DNNR, a neighbor contributes to the prediction not only its label, but also an additional correction term that depends on the difference between the target object and the neighbor in the original feature space.

This is how we arrive at Equation 4 – the new value module V. Similarly to DNNR, this module builds its output out of two terms:

1. The embedding of the context object’s label.

2. The “correction” term, where the module T translates the differences in the key space into the differences in the label embedding space.

## A.2.2 QUANTIFYING THE “CORRECTION” SEMANTICS

Recall the formal definition of the value module V of TabR (see Equation 5):

$$
\mathcal {V} (\tilde {x}, \tilde {x} _ {i}, y _ {i}) = W _ {Y} (y _ {i}) + T (k - k _ {i}) = W _ {Y} (y _ {i}) + T (\Delta k _ {i})\tag{6}
$$

Intuitively, for a given context object, its label $y _ { i }$ can be an important part of its contribution to the prediction. Let’s consider regression problems, where, in Equation $6 , y _ { i } \in \mathbb { R }$ is embedded by $W _ { Y }$ to $\tilde { \mathbb { Y } } \subset \mathbb { R } ^ { d }$ . Since $W _ { Y }$ is a linear layer, Y<sup>˜</sup> is just a line, and each point on this line can be mapped back to the corresponding label from R. Then, the projection of the correction term $T ( \Delta k _ { i } )$ on $\tilde { \mathbb { Y } }$ can be translated to the correction of the context label y<sub>i</sub>:

$$
\mathcal {V} (\tilde {x}, \tilde {x} _ {i}, y _ {i}) = W _ {Y} (y _ {i}) + \operatorname{proj} _ {\tilde {\mathbb {Y}}} T (\Delta k _ {i}) + \operatorname{proj} _ {\tilde {\mathbb {Y}} ^ {\perp}} T (\Delta k _ {i}) = W _ {Y} (y _ {i} + \underline {{\Delta y _ {i}}}) + \operatorname{proj} _ {\tilde {\mathbb {Y}} ^ {\perp}} T (\Delta k _ {i})\tag{7}
$$

To check whether the underlined correction term $\mathrm { p r o j } _ { \tilde { \mathbb { Y } } } T ( \Delta k _ { i } )$ (or $\Delta y _ { i } )$ is important, we take a trained TabR, and reevaluate it without retraining while ignoring this projection (which is equivalent to setting $\Delta y _ { i } = 0 )$ . As a baseline, we also try ignoring the projection of $T ( \Delta k _ { i } )$ on a random one-dimensional subspace instead of $\tilde { \mathbb { Y } } .$ . Table 8 indicates that the correction along $\tilde { \mathbb { Y } }$ plays a vital role for the model. The implementation details are provided in subsection D.5.

Table 8: Evaluating RMSE of trained TabR-S while ignoring projections of $T ( \Delta k _ { i } )$ on different one-dimensional subspaces as described in subsection ${ \bf A } . 2 .$ . The first column shows the projection on which one-dimensional subspace is removed from $T ( \Delta k _ { i } )$ . The first row corresponds to not removing any projections $( \mathrm { i . e . }$ , the unmodified TabR-S). Ignoring the projection on $\tilde { \mathbb { Y } }$ (the label embedding space) breaks the model while ignoring a random projection does not have much effect.

<table><tr><td></td><td>CA ↓</td><td>HO ↓</td><td>DI ↓</td><td>BL ↓</td><td>WE ↓</td></tr><tr><td>-</td><td>0.403</td><td>3.067</td><td>0.133</td><td>0.690</td><td>1.747</td></tr><tr><td>random</td><td>0.403</td><td>3.071</td><td>0.133</td><td>0.690</td><td>1.754</td></tr><tr><td> $\tilde{\mathbb{Y}}$ </td><td>0.465</td><td>3.649</td><td>0.364</td><td>0.695</td><td>2.003</td></tr></table>

For classification problems, we tested similar hypotheses but did not obtain any interesting results. Perhaps, the value module V and specifically the T module should be designed differently to better model the nature of classification problems.

## A.3 ABLATION STUDY

Recall that on Step-2 of subsection 3.2, we mentioned that it was crucial that all changes from Step-2 compared to Step-0 (using labels + not using queries + using the $L _ { 2 }$ distance instead of the dot product) are important to provide noticeable improvements over MLP on several datasets. Note that not using queries is equivalent to sharing weights of $W _ { Q }$ and $W _ { K } \colon W _ { Q } = W _ { K }$ . Table 9 contains the results of the corresponding experiment and indeed demonstrates that the Step-2 configuration cannot be trivially simplified without loss in metrics (see the CH, CA, BL, WE datasets).

Overall, we hypothesize that both things are important: how valuable the additional signal is (Step-1) and how well we measure the distance from the target object to the source of that valuable signal (Step-2).

## A.4 EFFICIENCY

## A.4.1 COMPARING TRAINING TIMES

While TabR demonstrates strong performance, these benefits do not come for free, since, as with all retrieval-augmented models, the retrieval component of TabR brings additional overhead. In this section, we aim to quantify this overhead by comparing the training times of TabR with those of all the baselines. Table 10 shows two important things:

Table 9: The ablation study as described in subsection A.3. $W _ { Q } = W _ { K }$ means using only keys and not using queries. Step-2 is the only variation providing noticeable improvements over MLP on the CH, CA, BL, WE datasets.

<table><tr><td></td><td colspan="3"> $L_2$ ,  $W_Q = W_K$ ,  $W_Y$ </td><td>CH</td><td>CA</td><td>HO</td><td>AD</td><td>DI</td><td>OT</td><td>HI</td><td>BL</td><td>WE</td><td>Avg. Rank</td></tr><tr><td>MLP</td><td></td><td></td><td></td><td>0.854</td><td>0.499</td><td>3.112</td><td>0.853</td><td>0.140</td><td>0.816</td><td>0.719</td><td>0.697</td><td>1.905</td><td>2.4 ± 1.4</td></tr><tr><td>Step-0</td><td>X</td><td>X</td><td>X</td><td>0.855</td><td>0.484</td><td>3.234</td><td>0.857</td><td>0.142</td><td>0.814</td><td>0.719</td><td>0.699</td><td>1.903</td><td>2.4 ± 0.9</td></tr><tr><td rowspan="6">Step-1</td><td>X</td><td>X</td><td>√</td><td>0.855</td><td>0.489</td><td>3.205</td><td>0.857</td><td>0.142</td><td>0.814</td><td>0.719</td><td>0.698</td><td>1.906</td><td>2.4 ± 1.2</td></tr><tr><td>X</td><td>√</td><td>X</td><td>0.853</td><td>0.495</td><td>3.178</td><td>0.857</td><td>0.143</td><td>0.808</td><td>0.719</td><td>0.698</td><td>1.903</td><td>2.9 ± 0.8</td></tr><tr><td>X</td><td>√</td><td>√</td><td>0.857</td><td>0.495</td><td>3.217</td><td>0.857</td><td>0.141</td><td>0.808</td><td>0.717</td><td>0.698</td><td>1.881</td><td>2.7 ± 0.7</td></tr><tr><td>√</td><td>X</td><td>X</td><td>0.855</td><td>0.488</td><td>3.170</td><td>0.857</td><td>0.143</td><td>0.813</td><td>0.719</td><td>0.698</td><td>1.901</td><td>2.3 ± 1.0</td></tr><tr><td>√</td><td>X</td><td>√</td><td>0.856</td><td>0.498</td><td>3.206</td><td>0.858</td><td>0.142</td><td>0.812</td><td>0.721</td><td>0.699</td><td>1.900</td><td>2.4 ± 1.1</td></tr><tr><td>√</td><td>√</td><td>X</td><td>0.856</td><td>0.442</td><td>3.154</td><td>0.856</td><td>0.141</td><td>0.811</td><td>0.722</td><td>0.698</td><td>1.896</td><td>2.0 ± 0.7</td></tr><tr><td>Step-2</td><td>√</td><td>√</td><td>√</td><td>0.860</td><td>0.418</td><td>3.153</td><td>0.858</td><td>0.140</td><td>0.813</td><td>0.720</td><td>0.692</td><td>1.804</td><td>1.2 ± 0.4</td></tr></table>

• first, TabR is significantly more efficient (i.e. provides a significantly better trade-off between the downstream performance and training times) than prior retrieval-augmented tabular models. In particular, TabR is significantly (and, sometimes, dramatically) more efficient than NPT (Kossen et al., 2021) – the closest retrieval-based competitor according to Table 3.

• second, within the considered scope of dataset sizes, the absolute training times of TabR will be affordable in practice. Moreover, the reported execution times are achieved with our naive implementation which lacks even some of the basic optimizations.

To sum up, compared to prior work on retrieval-based tabular DL, TabR makes a big step forward in terms of efficiency. TabR is relatively slower than simple models (GBDT, parametric DL models), and improving its efficiency is an important research direction. However, given the room for technical optimizations and techniques similar to context freeze (subsection 5.1), the future of retrieval-based tabular DL looks positive.

Table 10: Training times of the tuned models (from Table 3, Table 4 and Table 6) averaged over the random seeds. The format is hh:mm:ss. TabR-S (CF-4) is TabR-S with the context freeze (subsection 5.1) applied after four epochs. Colors describe the following informal tiers:

<table><tr><td></td><td>CH</td><td>CA</td><td>HO</td><td>AD</td><td>DI</td><td>OT</td><td>HI</td><td>BL</td><td>WE</td><td>CO</td><td>MI</td></tr><tr><td>XGBoost</td><td>0:00:01</td><td>0:00:20</td><td>0:00:05</td><td>0:00:05</td><td>0:00:02</td><td>0:00:35</td><td>0:00:15</td><td>0:00:08</td><td>0:02:02</td><td>0:01:55</td><td>0:03:43</td></tr><tr><td>LightGBM</td><td>0:00:00</td><td>0:00:04</td><td>0:00:01</td><td>0:00:01</td><td>0:00:03</td><td>0:00:34</td><td>0:00:10</td><td>0:00:07</td><td>0:06:40</td><td>0:06:22</td><td>0:06:45</td></tr><tr><td>MLP</td><td>0:00:02</td><td>0:00:18</td><td>0:00:09</td><td>0:00:17</td><td>0:00:15</td><td>0:00:31</td><td>0:00:24</td><td>0:01:38</td><td>0:00:29</td><td>0:04:01</td><td>0:02:09</td></tr><tr><td>MLP-PLR</td><td>0:00:03</td><td>0:00:43</td><td>0:00:14</td><td>0:00:24</td><td>0:00:25</td><td>0:02:09</td><td>0:00:17</td><td>0:00:52</td><td>0:20:01</td><td>0:03:32</td><td>0:30:30</td></tr><tr><td colspan="12">Retrieval-augmented models</td></tr><tr><td>TabR-S (CF-4)</td><td>0:00:08</td><td>0:00:25</td><td>0:00:30</td><td>0:00:34</td><td>0:00:43</td><td>0:00:57</td><td>0:01:02</td><td>0:03:08</td><td>0:09:08</td><td>0:23:13</td><td>-</td></tr><tr><td>TabR-S</td><td>0:00:20</td><td>0:01:20</td><td>0:01:23</td><td>0:03:04</td><td>0:01:44</td><td>0:01:17</td><td>0:02:09</td><td>0:11:22</td><td>0:12:11</td><td>0:49:59</td><td>0:55:04</td></tr><tr><td>TabR</td><td>0:00:16</td><td>0:00:40</td><td>0:00:55</td><td>0:01:30</td><td>0:01:24</td><td>0:01:47</td><td>0:06:22</td><td>0:04:14</td><td>1:03:18</td><td>0:37:03</td><td>1:46:07</td></tr><tr><td>DKL</td><td>-</td><td>0:06:15</td><td>0:03:55</td><td>-</td><td>0:21:59</td><td>-</td><td>-</td><td>1:04:10</td><td>-</td><td>-</td><td>-</td></tr><tr><td>ANP</td><td>-</td><td>0:37:40</td><td>0:42:16</td><td>-</td><td>2:14:38</td><td>-</td><td>-</td><td>1:32:27</td><td>6:00:11</td><td>-</td><td>-</td></tr><tr><td>SAINT</td><td>0:00:23</td><td>0:06:04</td><td>0:01:44</td><td>0:00:58</td><td>0:01:55</td><td>0:05:37</td><td>0:03:47</td><td>0:06:22</td><td>2:55:51</td><td>6:17:20</td><td>5:39:37</td></tr><tr><td>NPT</td><td>0:08:44</td><td>0:06:58</td><td>0:12:21</td><td>0:11:22</td><td>0:54:55</td><td>10:45:42</td><td>3:26:47</td><td>0:55:04</td><td>5:28:56</td><td>12:05:28</td><td>8:07:36</td></tr></table>

## A.4.2 COMPARING INFERENCE EFFICIENCY: TABR VS. XGBOOST

In this section, we compare the inference efficiency of TabR and XGBoost. Importantly, our current implementation of TabR is naive and lacks even basic optimizations.

Table 11 indicates that the inference speeds are mostly comparable. More nuanced observations are as follows:

• On “non-simple” tasks (CA, OT, WE, CO), TabR is faster (informally, “non-simple” means that XGBoost needs many trees AND/OR XGBoost needs high depth AND/OR a dataset has more features).

• On “simple” tasks, XGBoost is faster (informally, “simple” means that XGBoost is shallow AND/OR dataset has few features).

With the growth of training size (e.g. see the MI dataset in Table 11), TabR may become slower because of the retrieval, however, there is significant room for optimizations:

• Caching candidate key representations instead of recomputing them on each forward pass.

• Performing the search in float16 instead of float32.

• Using approximate search techniques instead of the current brute force.

• Using only a subset of the training data as candidates.

• etc.

Table 11: Inference throughput (batch size 4096) of tuned TabR-S and XGBoost from Table 4 on NVIDIA 2080 Ti. The last row reports the ratio between XGBoost’s throughput and TabR-S’s throughput.

<table><tr><td></td><td>CH</td><td>CA</td><td>HO</td><td>AD</td><td>DI</td><td>OT</td><td>HI</td><td>BL</td><td>WE</td><td>CO</td><td>MI</td></tr><tr><td>#objects</td><td>6400</td><td>13209</td><td>14581</td><td>26048</td><td>34521</td><td>39601</td><td>62751</td><td>106764</td><td>296554</td><td>371847</td><td>723412</td></tr><tr><td>#features</td><td>11</td><td>8</td><td>16</td><td>14</td><td>9</td><td>93</td><td>28</td><td>9</td><td>119</td><td>54</td><td>136</td></tr><tr><td>XGBoost #trees</td><td>121</td><td>3997</td><td>1328</td><td>988</td><td>802</td><td>524</td><td>1040</td><td>1751</td><td>3999</td><td>1258</td><td>3814</td></tr><tr><td>XGBoost maximum tree depth</td><td>5</td><td>9</td><td>7</td><td>10</td><td>13</td><td>13</td><td>11</td><td>8</td><td>13</td><td>12</td><td>12</td></tr><tr><td>XGBoost throughput (obj./sec.)</td><td>2197k</td><td>33k</td><td>179k</td><td>131k</td><td>417k</td><td>19k</td><td>72k</td><td>84k</td><td>15k</td><td>10k</td><td>14k</td></tr><tr><td>TabR-S throughput (obj./sec.)</td><td>35k</td><td>35k</td><td>55k</td><td>33k</td><td>43k</td><td>40k</td><td>37k</td><td>27k</td><td>34k</td><td>23k</td><td>11k</td></tr><tr><td>Overhead</td><td>62.3</td><td>0.9</td><td>3.3</td><td>3.9</td><td>9.6</td><td>0.5</td><td>1.9</td><td>3.1</td><td>0.5</td><td>0.4</td><td>1.2</td></tr></table>

## A.5 AUGMENTING XGBOOST WITH A RETRIEVAL COMPONENT

After the successful results of TabR reported in subsection 4.2, we tried augmenting XGBoost with a simple retrieval component to ensure that we do not miss this opportunity to improve the baselines. Namely, for a given input object, we find m = 96 (equal to the context size of TabR) nearest training objects in the original feature space, average their features and labels (the label as-is for regression problems, the one-hot encoding representations for classification problems), concatenate the target object’s features with the “average neighbor’s” features and label, and the obtained vector is used as the input for XGBoost. The results in Table 12 indicate that this strategy does not lead to any noticeable profit for XGBoost. We tried to vary the number of neighbors but did not achieve any significant improvements.

Table 12: Results for ensembles of tuned models. “XGBoost + retrieval” stands for XGBoost augmented with the “average neighbor’s” features and label as described in subsection A.5.

<table><tr><td></td><td>CH ↑</td><td>CA ↓</td><td>HO ↓</td><td>AD ↑</td><td>DI ↓</td><td>OT ↑</td><td>HI ↑</td><td>BL ↓</td><td>WE ↓</td><td>CO ↑</td><td>MI ↓</td><td>Avg. Rank</td></tr><tr><td>XGBoost</td><td>0.861</td><td>0.432</td><td>3.164</td><td>0.872</td><td>0.136</td><td>0.832</td><td>0.726</td><td>0.680</td><td>1.769</td><td>0.971</td><td>0.741</td><td> $1.9 \pm 0.7$ </td></tr><tr><td>XGBoost + retrieval</td><td>0.855</td><td>0.436</td><td>3.134</td><td>0.871</td><td>0.133</td><td>0.815</td><td>0.724</td><td>0.687</td><td>1.788</td><td>0.962</td><td>0.743</td><td> $2.5 \pm 0.5$ </td></tr><tr><td>TabR</td><td>0.865</td><td>0.391</td><td>3.025</td><td>0.872</td><td>0.131</td><td>0.831</td><td>0.733</td><td>0.674</td><td>1.661</td><td>0.977</td><td>0.748</td><td> $1.2 \pm 0.6$ </td></tr></table>

## A.6 HOW THE PERFORMANCE OF TABR DEPENDS ON THE CONTEXT SIZE m?

Recall that, throughout the paper, we used the fixed m = 96 as the context size (the number of neighbors) for TabR. We evaluate other values of m in Table 13. Crucially, the choice of m must be made based on the performance on validation sets (not on the test tests). The results indicate that m = 96 is a reasonable default value.

## A.7 ADDITIONAL RESULTS FOR THE “CONTEXT FREEZE” TECHNIQUE

We report the extended results for subsection 5.1 in Figure 7, Table 14 and Table 15. For the formal definition of the ∆-context metric, see subsection D.2.

Table 13: The average ranks over datasets from Table 1 of default TabR-S with different values of $m .$

<table><tr><td></td><td>m=1</td><td>m=2</td><td>m=4</td><td>m=8</td><td>m=16</td><td>m=32</td><td>m=64</td><td>m=96</td><td>m=128</td><td>m=256</td></tr><tr><td colspan="11">Validation Set</td></tr><tr><td>Avg. Rank</td><td>5</td><td>4.5</td><td>4</td><td>3.25</td><td>2.75</td><td>2.12</td><td>2.12</td><td>1.88</td><td>1.88</td><td>1.88</td></tr><tr><td>Rank Std.</td><td>2.45</td><td>1.87</td><td>1.73</td><td>1.71</td><td>1.56</td><td>1.45</td><td>1.45</td><td>0.93</td><td>1.05</td><td>1.36</td></tr><tr><td colspan="11">Test Set</td></tr><tr><td>Avg. Rank</td><td>4.12</td><td>3.62</td><td>3.5</td><td>3.12</td><td>2.38</td><td>2.12</td><td>2</td><td>1.62</td><td>1.75</td><td>1.75</td></tr><tr><td>Rank Std.</td><td>2.2</td><td>1.8</td><td>1.5</td><td>1.05</td><td>1.41</td><td>1.27</td><td>1.41</td><td>0.99</td><td>0.97</td><td>1.09</td></tr></table>

![](images/64d19a31a13abe5bddffa177e2f0ac931bc970142e081c8614905b85fadeb3c5.jpg)  
Figure 7: The extended version of Figure 5 with more datasets.

Table 14: The extended version of Table 6. Freezing after 0 epochs means freezing with a randomly initialized model. The speedups are provided in Table 15

<table><tr><td></td><td>CH ↑</td><td>CA ↓</td><td>HO ↓</td><td>AD ↑</td><td>DI ↓</td><td>OT ↑</td><td>HI ↑</td><td>BL ↓</td><td>WE ↓</td><td>CO ↑</td><td>WE (full) ↓</td><td>Avg. Rank</td></tr><tr><td>MLP</td><td>0.854</td><td>0.499</td><td>3.112</td><td>0.853</td><td>0.140</td><td>0.816</td><td>0.719</td><td>0.697</td><td>1.905</td><td>0.963</td><td>-</td><td>2.9 ± 1.5</td></tr><tr><td>TabR-S (CF-0)</td><td>0.857</td><td>0.424</td><td>3.075</td><td>0.857</td><td>0.137</td><td>0.816</td><td>0.718</td><td>0.700</td><td>1.787</td><td>0.969</td><td>1.387</td><td>2.3 ± 1.4</td></tr><tr><td>TabR-S (CF-1)</td><td>0.856</td><td>0.414</td><td>3.065</td><td>0.856</td><td>0.137</td><td>0.816</td><td>0.718</td><td>0.692</td><td>1.770</td><td>0.973</td><td>1.325</td><td>1.8 ± 1.0</td></tr><tr><td>TabR-S (CF-2)</td><td>0.856</td><td>0.411</td><td>3.074</td><td>0.856</td><td>0.137</td><td>0.816</td><td>0.718</td><td>0.691</td><td>1.767</td><td>0.973</td><td>-</td><td>1.7 ± 0.8</td></tr><tr><td>TabR-S (CF-4)</td><td>0.858</td><td>0.409</td><td>3.087</td><td>0.857</td><td>0.136</td><td>0.816</td><td>0.717</td><td>0.691</td><td>1.763</td><td>0.973</td><td>-</td><td>1.3 ± 0.5</td></tr><tr><td>TabR-S (CF-8)</td><td>0.858</td><td>0.407</td><td>3.118</td><td>0.857</td><td>0.135</td><td>0.817</td><td>0.719</td><td>0.691</td><td>1.761</td><td>0.973</td><td>-</td><td>1.3 ± 0.5</td></tr><tr><td>TabR-S</td><td>0.859</td><td>0.406</td><td>3.093</td><td>0.858</td><td>0.133</td><td>0.816</td><td>0.719</td><td>0.691</td><td>1.755</td><td>0.973</td><td>1.315</td><td>1.0 ± 0.0</td></tr></table>

Table 15: Fraction of time spent on training in Table 14, relative to the training time without the context freeze (the last row; the format is hours:minutes:seconds).

<table><tr><td></td><td>CH</td><td>CA</td><td>HO</td><td>AD</td><td>DI</td><td>OT</td><td>HI</td><td>BL</td><td>WE</td><td>CO</td><td>WE (full)</td></tr><tr><td>TabR-S (CF-0)</td><td>0.96</td><td>0.78</td><td>0.79</td><td>0.83</td><td>0.75</td><td>0.87</td><td>1.03</td><td>0.64</td><td>0.53</td><td>0.52</td><td>0.13</td></tr><tr><td>TabR-S (CF-1)</td><td>0.88</td><td>0.72</td><td>0.89</td><td>0.89</td><td>0.47</td><td>0.80</td><td>0.80</td><td>0.61</td><td>0.57</td><td>0.49</td><td>0.13</td></tr><tr><td>TabR-S (CF-2)</td><td>0.94</td><td>0.65</td><td>0.78</td><td>0.83</td><td>0.47</td><td>0.86</td><td>0.82</td><td>0.63</td><td>0.57</td><td>0.60</td><td>-</td></tr><tr><td>TabR-S (CF-4)</td><td>1.01</td><td>0.71</td><td>0.73</td><td>0.73</td><td>0.51</td><td>0.97</td><td>0.73</td><td>0.62</td><td>0.56</td><td>0.59</td><td>-</td></tr><tr><td>TabR-S (CF-8)</td><td>1.03</td><td>0.76</td><td>0.71</td><td>0.82</td><td>0.61</td><td>0.90</td><td>0.78</td><td>0.67</td><td>0.59</td><td>0.59</td><td>-</td></tr><tr><td>TabR-S</td><td>0:00:08</td><td>0:00:36</td><td>0:00:42</td><td>0:00:46</td><td>0:01:25</td><td>0:00:58</td><td>0:01:24</td><td>0:05:03</td><td>0:16:19</td><td>0:39:13</td><td>18:08:39</td></tr></table>

## A.8 ADDITIONAL TECHNICAL NOTES ON TABR

## We highlight the following technical aspects of TabR:

1. Because of the changes introduced in the Step-3 in subsection 3.2, the value representations $\mathcal { V } ( \tilde { x } , \tilde { x } _ { i } , y _ { i } )$ of the candidates cannot be precomputed for a trained model, since they depend on the target object. This implies roughly twice less memory usage when deploying the model to production (since only the key representations and labels have to be deployed for training objects), but $\mathcal { V } ( \tilde { x } , \tilde { x } _ { i } , y _ { i } )$ has to be computed in runtime.

2. Despite the attention-like nature of the retrieval module $R ,$ contrary to prior work, TabR does not suffer from the quadratic complexity w.r.t. the number of candidates, because it computes attention only for the target object, but not for the context objects.

3. In Equation 4, T uses LinearWithoutBias in its definition. Strictly speaking, from the perspective of expressiveness, adding a bias (i.e. using Linear) would be redundant in the presence of W<sub>Y</sub> in Equation 4. And, just in case, we avoid this redundancy (we did not test using the simple Linear instead of LinearWithoutBias).

## B LIMITATIONS & PRACTICAL CONSIDERATIONS

The following limitations and practical considerations are applicable to retrieval-augmented models in general. TabR itself does not add anything new to this list.

First, for a given application, one should carefully evaluate from various perspectives (business logic, legal considerations, ethical aspects, etc.) whether using real training objects for making predictions is reasonable.

Second, depending on an application, for a given target object, one may want to retrieve only from a subset of the available data, where the subset is dynamically formed for the target object based on application-specific filters. In terms of subsection 3.1, it means $I _ { c a n d } = I _ { c a n d } ( x ) \subset I _ { t r a i n }$

Third, ideally, retrieval during training should simulate retrieval during deployment, otherwise, a retrieval-based model can lead to (highly) suboptimal performance. Examples:

• For time series, during training, TabR must be allowed to retrieve only from the past. Moreover, perhaps, this “past” should also be limited to prevent the retrieval from too old data and too recent data. The decision should be made based on the domain expertise and business logic.

• Let’s consider a task where, among all training objects, there are some “related objects”. For example, when solving a ranking problem as a point-wise regression, such “related objects” can be obtained as query-document pairs corresponding to the same query, but different documents. In some cases, during training, for a given target object, retrieving from “related objects” can be unfair, because the same will not be possible in production for new objects that do not have “related objects” in the available data. Again, this design decision should be made based on the domain expertise and business logic.

Lastly, while TabR is significantly more efficient than prior retrieval-based tabular DL models, the retrieval module R still causes overhead compared to purely parametric models, so TabR may not scale to truly large datasets as-is. We showcase a simple trick to scale TabR to larger datasets in subsection 5.1. We discuss the efficiency aspect in more detail in subsection A.4.

## C BENCHMARKS

## C.1 THE DEFAULT BENCHMARK

In Table 16, we provide more information on the datasets from Table 1. The datasets include:

• Churn Modeling<sup>1</sup>

• California Housing (real estate data, (Kelley Pace and Barry, 1997))

• House 16H<sup>2</sup>

Table 16: Details on datasets from the main benchmark. “# Num”, “# Bin”, and “# Cat” denote the number of numerical, binary, and categorical features, respectively. The “Batch size” is the default batch size used to train DL-based models.

<table><tr><td>Abbr</td><td>Name</td><td># Train</td><td># Validation</td><td># Test</td><td># Num</td><td># Bin</td><td># Cat</td><td>Task type</td><td>Batch size</td></tr><tr><td>CH</td><td>Churn Modelling</td><td>6400</td><td>1600</td><td>2000</td><td>10</td><td>3</td><td>1</td><td>Binclass</td><td>128</td></tr><tr><td>CA</td><td>California Housing</td><td>13209</td><td>3303</td><td>4128</td><td>8</td><td>0</td><td>0</td><td>Regression</td><td>256</td></tr><tr><td>HO</td><td>House 16H</td><td>14581</td><td>3646</td><td>4557</td><td>16</td><td>0</td><td>0</td><td>Regression</td><td>256</td></tr><tr><td>AD</td><td>Adult</td><td>26048</td><td>6513</td><td>16281</td><td>6</td><td>1</td><td>8</td><td>Binclass</td><td>256</td></tr><tr><td>DI</td><td>Diamond</td><td>34521</td><td>8631</td><td>10788</td><td>6</td><td>0</td><td>3</td><td>Regression</td><td>512</td></tr><tr><td>OT</td><td>Otto Group Products</td><td>39601</td><td>9901</td><td>12376</td><td>93</td><td>0</td><td>0</td><td>Multiclass</td><td>512</td></tr><tr><td>HI</td><td>Higgs Small</td><td>62751</td><td>15688</td><td>19610</td><td>28</td><td>0</td><td>0</td><td>Binclass</td><td>512</td></tr><tr><td>BL</td><td>Black Friday</td><td>106764</td><td>26692</td><td>33365</td><td>4</td><td>1</td><td>4</td><td>Regression</td><td>512</td></tr><tr><td>WE</td><td>Shifts Weather (subset)</td><td>296554</td><td>47373</td><td>53172</td><td>118</td><td>1</td><td>0</td><td>Regression</td><td>1024</td></tr><tr><td>CO</td><td>Covertype</td><td>371847</td><td>92962</td><td>116203</td><td>54</td><td>44</td><td>0</td><td>Multiclass</td><td>1024</td></tr><tr><td>WE (full)</td><td>Shifts Weather (full)</td><td>2965542</td><td>47373</td><td>531720</td><td>118</td><td>1</td><td>0</td><td>Regression</td><td>1024</td></tr></table>

• Adult (income estimation, (Kohavi, 1996))

• Diamond<sup>3</sup>

• Otto Group Product Classification<sup>4</sup>

• Higgs (simulated physical particles, (Baldi et al., 2014); we use the version with 98K samples available in the OpenML repository (Vanschoren et al., 2014))

• Black Friday<sup>5</sup>

• Weather (temperature, (Malinin et al., 2021)). We take 10% of the dataset for our experiments due to its large size.

• Weather (full) (temperature, (Malinin et al., 2021)). Original splits from the paper.

• Covertype (forest characteristics, (Blackard and Dean., 2000))

• Microsoft (search queries, (Qin and Liu, 2013)). We follow the pointwise approach to learning to rank and treat this ranking problem as a regression problem.

## C.2 THE BENCHMARK FROM GRINSZTAJN ET AL. (2022)

In this section, we describe how exactly we used the benchmark proposed in Grinsztajn et al. (2022).

• We use the same train-val-test splits.

• When there are several splits for one dataset (i.e., when the n-fold-cross-validation was performed in Grinsztajn et al. (2022)), we first treat each of them as separate datasets while tuning and evaluating algorithms as described in Appendix D, but then, we average the metrics over the splits to obtain the final numbers for the dataset. For example, if there are five splits for a given dataset, then we tune and evaluate a given algorithm five times, each of the five tuned configurations is evaluated under 15 random seeds on the corresponding splits, and the reported metric value is the average over 5 ∗ 15 = 75 runs.

• When there are multiple versions of one dataset (e.g., the original regression task and the same dataset but converted to the binary classification task or the same dataset, but with the categorical features removed, etc.), we keep only one original dataset.

• We removed the “Eye movements” dataset because there is a leak in that dataset.

• We use the tuning and evaluation protocols as described in Appendix D, which was also used in prior works on tabular DL (Gorishniy et al., 2021; 2022). Crucially, we tune hyperparameters of the GBDT models more extensively than most (if not all) prior work in terms of both budget (20 warmup iterations of random sampling followed by 180 iterations of the tree-structured Parzen estimator algorithm) and hyperparameter spaces (see the corresponding sections in Appendix D).

## D IMPLEMENTATION DETAILS

## D.1 HARDWARE

We report the used hardware in the results published along with the source code. In a nutshell, the vast majority of experiments on GPU were performed on one NVidia A100 GPU, the remaining small part of GPU experiments was performed on one Nvidia 2080 Ti GPU, and there was also a small portion of runs performed on CPU (e.g. all the experiments on LightGBM).

## D.2 IMPLEMENTATION DETAILS OF SUBSECTION 5.1

In subsection 5.1, we used TabR-S with the default hyperparameters (see subsection D.8). To compute ∆-context, we collect context distributions for training objects between training epochs. That is, after the i-th training epoch, we pause the training, collect the context distributions for all training objects, and then start the next (i + 1)-th training epoch.

∆-context. Intuitively, this heuristic metric describes in a single number how much, for a given input object, the context attention mass was updated compared to the previous epoch. Namely, it is a sum of two terms:

1. the novel attention mass, i.e. the attention mass coming from the context objects presented on the current epoch, but not presented on the previous epoch

2. the increased attention mass, i.e. we take the intersection of the current and the previous context objects and compute the increase of their total attention mass. We set it to 0.0 if actually decreased.

Now, we formally define this metric. For a given input object, let $a \in \mathbb { R } ^ { | I _ { t r a i n } | }$ and $b \in \mathbb { R } ^ { | I _ { t r a i n } | }$ denote the two distributions over the candidates from the previous and the current epochs, respectively. Let denote the sets of non-zero entries as $A = \{ i : a _ { i } > 0 \}$ and $B = \{ i : a _ { i } > 0 \}$ . Note that $| A | = | B | = m = 9 6$ . In other words, A and B are the contexts from the two epochs. Then:

$$
\Delta \text {-context} = \text { novel } + \text { increased }\tag{8}
$$

$$
\text { novel } = \sum_ {i \in B \setminus A} b _ {i}\tag{9}
$$

$$
\text { increased } = \max \left(\sum_ {i \in B \cap A} b _ {i} - \sum_ {i \in B \cap A} a _ {i}, 0. 0\right)\tag{10}
$$

## D.3 IMPLEMENTATION DETAILS OF SUBSECTION 5.2

In subsection 5.2, we used TabR-S with the default hyperparameters (see subsection D.8).

## D.4 IMPLEMENTATION DETAILS OF SUBSUBSECTION A.1.2

In subsubsection A.1.2, we performed the analysis over exactly the same model checkpoints that we used to assemble the rows “Step-1” and $\mathrm { } ^ { \mathrm { * } } \mathrm { S t e p } { \cdot } \mathrm { \bar { 2 } } ^ { \mathrm { * } }$ in Table 2.

To reiterate, this is how the entropy in Table 7 is computed:

1. First, we obtain individual distributions over candidates for all test objects. One such distribution contains exactly (m + 1) non-zero entries.

2. Then, we average all individual distributions and obtain the average distribution.

3. Table 7 reports the entropy of the average distribution.

Note that, when obtaining the distribution over candidates, the top-m operation is taken into account. Without that, if the distribution is always uniform regardless of the input object, then the average distribution will also be uniform and with the highest possible entropy, which would be misleading in the context of the story in subsubsection A.1.2.

Lastly, recall that in the Step-1 and Step-2 models, an input object is added to its own context. Then, the edge case when all input objects pay 100% attention only to themselves would lead to the highest possible entropy, which would be misleading for the story in subsubsection A.1.2. In other words, for the story in subsubsection A.1.2, we should treat the “paying attention to self” behavior similarly for all objects. To achieve that, on the first step of the above recipe, we reassign the attention mass from “self” to a new virtual context object, which is the same for all input objects.

## D.5 IMPLEMENTATION DETAILS OF SUBSECTION A.2

To build Table 8, we used TabR-S with the default hyperparameters (see subsection D.8).

## D.6 EXPERIMENT SETUP

For the most part, we simply follow Gorishniy et al. (2022), but we provide all the details for completeness. Note that some of the prior work may differ from the common protocol that we describe below, but we provide the algorithm-specific implementation details further in this section.

Data preprocessing. For each dataset, for all DL-based solutions, the same preprocessing was used for fair comparison. For numerical features, by default, we used the quantile normalization from the Scikit-learn package (Pedregosa et al., 2011), with rare exceptions when it turned out to be detrimental (for such datasets, we used the standard normalization or no normalization). For categorical features, we used one-hot encoding. Binary features (i.e. the ones that take only two distinct values) are mapped to {0, 1} without any further preprocessing.

Training neural networks. For DL-based algorithms, we minimize cross-entropy for classification problems and mean squared error for regression problems. We use the AdamW optimizer (Loshchilov and Hutter, 2019). We do not apply learning rate schedules. We do not use data augmentations. For each dataset, we used a predefined dataset-specific batch size. We continue training until there are patience + 1 consecutive epochs without improvements on the validation set; we set patience = 16 for the DL models.

How we compare algorithms. For a given dataset, first, we define the “preliminary best” algorithm as the algorithm with the best mean score. Then, we define a set of the best algorithms (i.e. their results are in bold in tables) as follows: a given algorithm is included in the best algorithms if its mean score differs from the mean score of the preliminary best algorithm by no more than the standard deviation of the preliminary best algorithm.

## D.7 EMBEDDINGS FOR NUMERICAL FEATURES

![](images/6deb6d8e34e204254cc06f9042174d4758f8990cca128ade847db5619e941fb7.jpg)  
Figure 8: (Copied from Gorishniy et al. (2022)) The vanilla MLP. The model takes two numerical features as input.

![](images/eb11b07e76c52a47f02c30700804ead031ea0c45659634cc914d31650158c586.jpg)  
Figure 9: (Copied from Gorishniy et al. (2022)) The same MLP as in Figure 8, but now with embeddings for numerical features.

In this work, we actively used embeddings for numerical features from (Gorishniy et al., 2022) (see Figure 8 and Figure 9), the technique which was reported to universally improve DL models. In a nutshell, for a given scalar numerical feature, an embedding module is a trainable module that maps this scalar feature to a vector. Then, the embeddings of all numerical features are concatenated into one flat vector which is passed to further layers. Following the original paper, when we use embeddings for numerical features, the same embedding architecture is used for all numerical features.

In this work, we used the LR (the combination of a linear layer and ReLU) and PLR (the combination of periodic embeddings, a linear layer, and ReLU) embeddings from the original paper. Also, we introduce the PLR(lite) embedding, a simplified version of the PLR embedding where the linear layer is shared across all features. We observed it to be significantly more lightweight without critical performance loss.

Hyperparameters tuning. For the LR embeddings, we tune the embedding dimension in Uniform[16, 96]. For the PLR and PLR(lite) embeddings, we tune the number of frequencies in Uniform[16, 96] (in Uniform[8, 96] for TabR on the datasets from Grinsztajn et al. (2022)), the frequency initialization scale in LogUniform[0.01, 100.0] and the embedding dimension in Uniform[16, 64] (in Uniform[4, 64] for TabR on the datasets from Grinsztajn et al. (2022)).

## D.8 TABR

The implementation, tuning hyperparameters, evaluation hyperparameters, metrics, execution times, hardware and other details are available in the source code. Here, we summarize some of the details for convenience.

Embeddings for numerical features. (see subsection D.7) For the non-simple configurations of TabR, on datasets CH, CA, HO, AD, DI, OT, HI, BL, and on all the datasets from Grinsztajn et al. (2022), we used the PLR(lite) embeddings as defined in subsection D.7. For other datasets, we used the LR embeddings.

Other details. We observed that initializing the W<sub>Y</sub> module properly may be important for good performance. Please, see the source code.

Default TabR-S. The default hyperparameters for TabR-S were obtained at some point in the project by literally averaging the tuned hyperparameters over multiple datasets. The specific set of datasets for averaging included all datasets from Table 16 plus two datasets that used to be a part of the default benchmark, but were excluded later. So, in total, 13 datasets contributed to the default hyperparameters.

Formally, this is not 100% fair to evaluate the obtained default TabR-S on the datasets which contributed to this default hyperparameters as in Table 4. However, we tested the fair leave-one-out approach as well (i.e. for a given dataset, averaging tuned hyperparameters over all datasets except for this one dataset) and did not observe any meaningful changes, so we decided to keep things simple and to have one common set of default hyperparameters for all datasets. Plus, the obtained default TabR-S demonstrates decent performance in Table 5 as well, which illustrates that the obtained default configuration is not strongly “overfitted” to the datasets from Table 16. The specific default hyperparameter values of TabR-S are as follows:

• d = 265

• Attention dropout rate = 0.38920071545944357

• Dropout rate in FFN = 0.38852797479169876

• Learning rate = 0.0003121273641315169

• Weight decay = 0.0000012260352006404615

Hyperparameters. The output size of the first linear layer of FFN and of T is 2d. We performed tuning using the tree-structured Parzen Estimator algorithm from the Akiba et al. (2019) library. The same protocol and hyperparameter spaces were used when tuning models in Table 2 and Table 9.

Table 17: The hyperparameter tuning space for TabR. Here (A) = {CH, CA, HO, AD, DI, OT, HI, BL}, (B) = {WE, CO, MI}. For the datasets from Grinsztajn et al. (2022), the tuning space is identical to (A) with the only difference that d is tuned in UniformInt[16, 384].

<table><tr><td>Parameter</td><td>(Datasets) Distribution</td><td>Comment</td></tr><tr><td>Width  $d$ </td><td>(A,B) UniformInt[96, 384]</td><td></td></tr><tr><td>Attention dropout rate</td><td>(A,B) Uniform[0.0, 0.6]</td><td></td></tr><tr><td>Dropout rate in FFN</td><td>(A,B) Uniform[0.0, 0.6]</td><td></td></tr><tr><td>Learning rate</td><td>(A,B) LogUniform[3e-5, 1e-3]</td><td></td></tr><tr><td>Weight decay</td><td>(A,B) {0, LogUniform[1e-6, 1e-3]}</td><td></td></tr><tr><td> $N_E$ </td><td>(A,B) UniformInt[0, 1]</td><td>Const[0] for TabR-S</td></tr><tr><td> $N_P$ </td><td>(A,B) UniformInt[1, 2]</td><td>Const[1] for TabR-S</td></tr><tr><td># Tuning iterations</td><td>(A) 100 (B) 50</td><td></td></tr></table>

## D.9 MLP

The implementation, tuning hyperparameters, evaluation hyperparameters, metrics, execution times, hardware and other details are available in the source code. Here, we summarize some of the details for convenience.

We used the implementation from Gorishniy et al. (2022).

Hyperparameters. We use the same hidden dimension throughout the whole network. We performed tuning using the tree-structured Parzen Estimator algorithm from the Akiba et al. (2019) library.

Table 18: The hyperparameter tuning space for MLP

<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td># layers</td><td>UniformInt[1, 6]</td></tr><tr><td>Width (hidden size)</td><td>UniformInt[64, 1024]</td></tr><tr><td>Dropout rate</td><td>{0.0, Uniform[0.0, 0.5]}</td></tr><tr><td>Learning rate</td><td>LogUniform[3e-5, 1e-3]</td></tr><tr><td>Weight decay</td><td>{0, LogUniform[1e-6, 1e-3]}</td></tr><tr><td># Tuning iterations</td><td>100</td></tr></table>

## D.10 FT-TRANSFORMER

The implementation, tuning hyperparameters, evaluation hyperparameters, metrics, execution times, hardware and other details are available in the source code. Here, we summarize some of the details for convenience.

We used the implementation from the "rtdl" Python package (version 0.0.13).

Hyperparameters. We use the rtdl.FTTransformer.make\_baseline method to create FT-Transformer, so most of hyperparameters is inherited from this method’s signature, and the rest is tuned as shown in the corresponding table.

Table 19: The hyperparameter tuning space for FT-Transformer

<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td># blocks</td><td>UniformInt[1, 4]</td></tr><tr><td> $d_{token}$ </td><td>UniformInt[16, 384]</td></tr><tr><td>Attention dropout rate</td><td>Uniform[0.0, 0.5]</td></tr><tr><td>FFN hidden dimension expansion rate</td><td>Uniform[2/3, 8/3]</td></tr><tr><td>FFN dropout rate</td><td>Uniform[0.0, 0.5]</td></tr><tr><td>Residual dropout rate</td><td>{0.0, Uniform[0.0, 0.2]}</td></tr><tr><td>Learning rate</td><td>LogUniform[1e-5, 1e-3]</td></tr><tr><td>Weight decay</td><td>{0, LogUniform[1e-6, 1e-4]}</td></tr><tr><td># Tuning iterations</td><td>100</td></tr></table>

## D.11 KNN

The implementation, tuning hyperparameters, evaluation hyperparameters, metrics, execution times, hardware and other details are available in the source code. Here, we summarize some of the details for convenience.

The features are preprocessed in the same way as for DL models. The only hyperparameter is the number of neighbors which we tune in UniformInt[1, 128].

## D.12 DNNR

The implementation, tuning hyperparameters, evaluation hyperparameters, metrics, execution times, hardware and other details are available in the source code. Here, we summarize some of the details for convenience.

We’ve used the official implementation <sup>6</sup>, but to evaluate DNNR on larger datasets with greater hyperparameters variability, we have rewritten parts of the source code to make it more efficient: enabling GPU usage, batched data processing, multiprocessing, where possible. Crucially, we leave the underlying method unchanged. We provide our efficiency-improved DNNR in the source code. There is no support for classification problems, so we evaluate DNNR only on regression problems.

Hyperparameters. We performed a grid-search over the main DNNR hyperparameters on all datasets, falling back to defaults (suggested by the authors) due to scaling issues on WE and MI.

Table 20: The hyperparameter grid used for DNNR. Here $\mathrm { { ( A ) } = \{ C A , H O \} ; \mathrm { { ( B ) } = \{ D I , B L , W E , M I \} } }$ Notation: N<sub>f</sub> – number of features for the dataset.

<table><tr><td>Parameter</td><td>(Datasets) Parameter grid</td><td>Comment</td></tr><tr><td># neighbors k</td><td>(A,B) [1, 2, 3, . . . , 128]</td><td></td></tr><tr><td>Learned scaling</td><td>(A,B) [No scaling, Trained scaling]</td><td></td></tr><tr><td># neighbors used in scaling</td><td>(A,B) [8 ·  $N_f$ , 2, 3, 4, 8, 16, 32, 64, 128]</td><td>8 ·  $N_f$  on WE, MI</td></tr><tr><td># epochs used in scaling</td><td>10</td><td></td></tr><tr><td>Cat. feature encoding</td><td>[one-hot, leave-one-out]</td><td></td></tr><tr><td rowspan="2"># neighbors for derivative k&#x27;</td><td>(A) LinSpace[2 ·  $N_f$ , 18 ·  $N_f$ , 20]</td><td></td></tr><tr><td>(B) LinSpace[2 ·  $N_f$ , 12 ·  $N_f$ , 14]</td><td></td></tr></table>

## D.13 DKL

The implementation, tuning hyperparameters, evaluation hyperparameters, metrics, execution times, hardware and other details are available in the source code. Here, we summarize some of the details for convenience.

We used DKL implementation from GPyTorch (Gardner et al., 2018). We do not evaluate DKL on WE and MI datasets due to scaling issues (tuning alone takes 1 day and 17 hours, compared to 3 hours for TabR on the medium DI dataset, for example). There is no support for classification problems, thus we evaluate DKL only on regression problems.

Hyperparameters. As with MLP we use the same hidden dimension throughout the whole network. And perform tuning using the tree-structured Parzen Estimator algorithm from the Akiba et al. [1] library.

Table 21: The hyperparameter tuning space for DKL

<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td>Kernel</td><td>{rbf, sm}</td></tr><tr><td># layers</td><td>UniformInt[1, 4]</td></tr><tr><td>Width (hidden size)</td><td>UniformInt[64, 768]</td></tr><tr><td>Dropout rate</td><td>{0.0, Uniform[0.0, 0.5]}</td></tr><tr><td>Learning rate</td><td>LogUniform[1e-5, 1e-2]</td></tr><tr><td>Weight decay</td><td>{0, LogUniform[1e-6, 1e-3]}</td></tr><tr><td># Tuning iterations</td><td>100</td></tr></table>

## D.14 ANP

While the original paper introducing ANP did not focus on the tabular data, conceptually, it is very relevant to prior work on retrieval-based tabular DL, so we consider it as one of the baselines.

The implementation, tuning hyperparameters, evaluation hyperparameters, metrics, execution times, hardware and other details are available in the source code. Here, we summarize some of the details for convenience.

We used the Pytorch implementation from an unofficial repository<sup>7</sup> and modified it with respect to the official implementation from Kim et al. (2019). Specifically, we reimplemented Decoder class exactly as it was done in Kim et al. (2019) and changed a binary cross-entropy loss with a Gaussian negative log-likelihood loss in LatentModel class since it matches with the official implementation.

We do not evaluate ANP on the MI dataset due to scaling issues. Tuning alone on the smaller WE dataset took more than four days for 20(!) iterations (instead of 50-100 used for other algorithms). Also, there is no support for classification problems, thus we evaluate ANP only on regression problems.

We used 100 tuning iterations on CA and HO, 50 on DI, and 20 on BL and WE.

Table 22: The hyperparameter tuning space for ANP

<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td># decoder layers</td><td>UniformInt[1, 3]</td></tr><tr><td># cross-attention layers</td><td>UniformInt[1, 2]</td></tr><tr><td># self-attention layers</td><td>UniformInt[1, 2]</td></tr><tr><td>Width (hidden size)</td><td>UniformInt[64, 384]</td></tr><tr><td>Learning rate</td><td>LogUniform[3e-5, 1e-3]</td></tr><tr><td>Weight decay</td><td>{0, LogUniform[1e-6, 1e-4]}</td></tr></table>

## D.15 NPT

We use the official NPT (Kossen et al., 2021) implementation <sup>8</sup>. We leave the model and training code unchanged and only adjust the datasets and their preprocessing according to our protocols.

We evaluate the NPT-Base configuration of the model and follow both NPT-Base architecture and optimization hyperparameters. We train NPT for 2000 epochs on CH, CA, AD, HO, 10000 epochs on OT, WE, MI, 15000 epochs on DI, BL, HI and 30000 epochs on CO. For all datasets that don’t fit into the A100 80GB GPU, we use batch size 4096 (as suggested in the NPT paper). We also decrease the hidden dim to 32 on WE and MI to avoid the OOM error.

Note that NPT is conceptually equivalent to other transformer-based non-parametric tabular DL solutions: (Somepalli et al., 2021; Schäfl et al., 2022). All three methods use dot-product-based self-attention modules alternating between self-attention between object features and self-attention between objects (for the whole training dataset or its random subset).

## D.16 SAINT

The implementation, tuning hyperparameters, evaluation hyperparameters, metrics, execution times, hardware and other details are available in the source code. Here, we summarize some of the details for convenience.

We use the official implementation of SAINT <sup>9</sup> with one important fix. Recall that, in SAINT, a target object interacts with its context objects with intersample attention. In the official implementation of SAINT, context objects are taken from the same dataset part, as a target object: for training objects, context objects are taken from the training set, for validation objects – from the validation set, for test objects – from the test set. This is different from the approach described in this paper, where context objects are always takenfrom the training set. Taking context objects from different dataset parts, as in the official implementation of SAINT, may be unwanted because of the following reasons:

1. model can have suboptimal validation and test performance because it is trained to operate when context objects are taken from the training set, but evaluated when context objects are taken from other dataset parts.

2. for a given validation/test object, the prediction depends on other validation/test objects. This is not in line with other retrieval-based models, which may result in inconsistent comparisons. Also, in many real-world scenarios, during deployment/test time, input objects should be processed independently, which is not the case for the official implementation of SAINT.

For the above reasons, we slightly modify SAINT such that each individual sample attends only to itself and to context samples from the training set, both during training and evaluation. See the source code for details.

On small datasets (CH, CA, HO, AD, DI, OT, HI, BL) we fix the number of attention heads at 8 and performed hyperparameter tuning using the tree-structured Parzen Estimator algorithm from the Akiba et al. (2019) library.

Table 23: The hyperparameter tuning space for SAINT

<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td>Depth</td><td>UniformInt[1, 4]</td></tr><tr><td>Width</td><td>UniformInt[4, 32, 4]</td></tr><tr><td>Feed forward multiplier</td><td>Uniform[2/3, 8/3]</td></tr><tr><td>Attention dropout</td><td>Uniform[0, 0.5]</td></tr><tr><td>Feed forward dropout</td><td>Uniform[0, 0.5]</td></tr><tr><td>Learning rate</td><td>LogUniform[3e-5, 1e-3]</td></tr><tr><td>Weight decay</td><td>{0, LogUniform[1e-6, 1e-4]}</td></tr></table>

On larger datasets (WE, CO, MI) we use slightly modified (for optimizing memory consumption) default configuration from the paper with following fixed hyperparameters:

```txt
- depth = 4
- n_heads = 8
- dim = 32
- ffn_mult = 4
- attn_head_dim = 48
- attn_dropout = 0.1
- ff_dropout = 0.8
- learning_rate = 0.0001
- weight_decay = 0.01
```

## D.17 XGBOOST

The implementation, tuning hyperparameters, evaluation hyperparameters, metrics, execution times, hardware and other details are available in the source code. Here, we summarize some of the details for convenience.

In this work, we made our best to tune GBDT models as good as possible to make sure that the comparison is fair, and the conclusions are reliable. Compared to prior work (Gorishniy et al., 2021; 2022), where GBDT is already extensively tuned, we doubled the number of tuning iterations, doubled the number of trees, increased the maximum depth and increased the number of early stopping rounds by 4x.

The following hyperparameters are fixed and not tuned:

• booster = “gbtree”

• n\_estimators = 4000

• tree\_method = “gpu\_hist”

• $\mathtt { a r l y \_ s t o p p i n g \_ r o u n d s } = 2 0 0$

We performed tuning using the tree-structured Parzen Estimator algorithm from the Akiba et al. (2019) library.

Table 24: The hyperparameter tuning space for XGBoost

<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td>colsample_bytree</td><td>Uniform[0.5, 1.0]</td></tr><tr><td>gamma</td><td>{0.0, LogUniform[0.001, 100.0]}</td></tr><tr><td>lambda</td><td>{0.0, LogUniform[0.1, 10.0]}</td></tr><tr><td>learning_rate</td><td>LogUniform[0.001, 1.0]</td></tr><tr><td>max_depth</td><td>UniformInt[3, 14]</td></tr><tr><td>min_child_weight</td><td>LogUniform[0.0001, 100.0]</td></tr><tr><td>subsample</td><td>Uniform[0.5, 1.0]</td></tr><tr><td># Tuning iterations</td><td>200</td></tr></table>

## D.18 LIGHTGBM

The implementation, tuning hyperparameters, evaluation hyperparameters, metrics, execution times, hardware and other details are available in the source code. Here, we summarize some of the details for convenience.

In this work, we made our best to tune GBDT models as good as possible to make sure that the comparison is fair, and the conclusions are reliable. Compared to prior work (Gorishniy et al., 2021; 2022), where GBDT is already extensively tuned, we doubled the number of tuning iterations, doubled the number of trees, increased the maximum depth and increased the number of early stopping rounds by 4x.

The following hyperparameters are fixed and not tuned:

• n\_estimators = 4000

• early\_stopping\_rounds = 200

We performed tuning using the tree-structured Parzen Estimator algorithm from the Akiba et al. (2019) library.

Table 25: The hyperparameter tuning space for LightGBM

<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td>feature_fraction</td><td>Uniform[0.5, 1.0]</td></tr><tr><td>lambda_12</td><td>{0.0, LogUniform[0.1, 10.0]}</td></tr><tr><td>learning_rate</td><td>LogUniform[0.001, 1.0]</td></tr><tr><td>num_leaves</td><td>UniformInt[4, 768]</td></tr><tr><td>min_sum_hessian_in_leaf</td><td>LogUniform[0.0001, 100.0]</td></tr><tr><td>bagging_fraction</td><td>Uniform[0.5, 1.0]</td></tr><tr><td># Tuning iterations</td><td>200</td></tr></table>

## D.19 CATBOOST

The implementation, tuning hyperparameters, evaluation hyperparameters, metrics, execution times, hardware and other details are available in the source code. Here, we summarize some of the details for convenience.

In this work, we made our best to tune GBDT models as good as possible to make sure that the comparison is fair, and the conclusions are reliable. Compared to prior work (Gorishniy et al., 2021; 2022), where GBDT is already extensively tuned, we doubled the number of tuning iterations, doubled the number of trees, increased the maximum depth and increased the number of early stopping rounds by 4x.

The following hyperparameters are fixed and not tuned:

• n\_estimators = 4000

• early\_stopping\_rounds = 200

• od\_pval = 0.001

We performed tuning using the tree-structured Parzen Estimator algorithm from the Akiba et al. (2019) library.

Table 26: The hyperparameter tuning space for CatBoost

<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td>bagging_temperature</td><td>Uniform[0.0, 1.0]</td></tr><tr><td>depth</td><td>UniformInt[3, 14]</td></tr><tr><td>l2_leaf_reg</td><td>Uniform[0.1, 10.0]</td></tr><tr><td>leaf_estimation_iterations</td><td>Uniform[1, 10]</td></tr><tr><td>learning_rate</td><td>LogUniform[0.001, 1.0]</td></tr><tr><td># Tuning iterations</td><td>200</td></tr></table>

## E EXTENDED RESULTS WITH STANDARD DEVIATIONS

In this section, we provide the extended results with standard deviations for the main results reported in the main text. The results for the default benchmark are in the Table 27. The results for the benchmark from Grinsztajn et al. (2022) are in the Table 28.

Table 27: Extended results for the default benchmark. Results are grouped by datasets and span multiple pages below. Notation: ↓ corresponds to RMSE, ↑ corresponds to accuracy.

CH ↑

CA ↓

$$
0. 8 3 7 \pm 0. 0 0 0
$$

$$
0. 5 8 8 \pm 0. 0 0 0
$$

$$
0. 4 3 0 \pm 0. 0 0 0
$$

$$
0. 5 2 1 \pm 0. 0 5 5
$$

$$
0. 8 5 8 \pm 0. 0 0 3
$$

$$
0. 4 7 2 \pm 0. 0 0 7
$$

$$
0. 4 7 4 \pm 0. 0 0 3
$$

$$
0. 8 6 0 \pm 0. 0 0 3
$$

$$
0. 4 6 8 \pm 0. 0 0 5
$$

$$
0. 8 5 4 \pm 0. 0 0 3
$$

$$
0. 4 9 9 \pm 0. 0 0 4
$$

$$
0. 8 6 0 \pm 0. 0 0 2
$$

$$
0. 8 6 0 \pm 0. 0 0 1
$$

$$
\mathrm{MLP-PLR}
$$

$$
0. 4 7 6 \pm 0. 0 0 4
$$

$$
0. 4 7 0 \pm 0. 0 0 1
$$

$$
0. 8 6 0 \pm 0. 0 0 2
$$

$$
0. 8 6 2 \pm 0. 0 0 2
$$

$$
0. 4 0 3 \pm 0. 0 0 2
$$

$$
0. 3 9 6 \pm 0. 0 0 1
$$

$$
0. 8 6 2 \pm 0. 0 0 2
$$

$$
0. 8 6 5 \pm 0. 0 0 1
$$

$$
0. 4 0 0 \pm 0. 0 0 3
$$

$$
0. 3 9 1 \pm 0. 0 0 2
$$

$$
0. 8 5 8 \pm 0. 0 0 2
$$

$$
0. 8 5 9 \pm 0. 0 0 1
$$

$$
0. 4 2 9 \pm 0. 0 0 1
$$

$$
0. 4 2 6 \pm 0. 0 0 0
$$

$$
0. 8 6 1 \pm 0. 0 0 2
$$

$$
0. 8 6 1 \pm 0. 0 0 1
$$

$$
0. 4 3 3 \pm 0. 0 0 2
$$

$$
0. 4 3 2 \pm 0. 0 0 1
$$

$$
0. 8 6 0 \pm 0. 0 0 1
$$

$$
0. 8 6 0 \pm 0. 0 0 0
$$

$$
0. 4 3 5 \pm 0. 0 0 2
$$

$$
0. 4 3 4 \pm 0. 0 0 1
$$

$$
0. 8 6 1 \pm 0. 0 0 1
$$

$$
0. 4 3 3 \pm 0. 0 0 1
$$

$$
0. 4 3 2 \pm 0. 0 0 1
$$

$$
0. 8 5 6 \pm 0. 0 0 0
$$

$$
0. 4 7 1 \pm 0. 0 0 0
$$

$$
0. 8 5 6 \pm 0. 0 0 0
$$

$$
0. 4 4 9 \pm 0. 0 0 0
$$

$$
0. 4 4 9 \pm 0. 0 0 0
$$

$$
0. 8 6 4 \pm 0. 0 0 1
$$

$$
0. 4 0 6 \pm 0. 0 0 3
$$

$$
0. 3 9 8 \pm 0. 0 0 1
$$

$$
0. 8 5 5 \pm 0. 0 0 3
$$

$$
0. 8 5 7 \pm 0. 0 0 2
$$

$$
0. 4 8 4 \pm 0. 0 0 6
$$

$$
0. 4 7 0 \pm 0. 0 0 5
$$

$$
0. 8 5 5 \pm 0. 0 0 3
$$

$$
0. 8 5 8 \pm 0. 0 0 2
$$

$$
0. 4 8 9 \pm 0. 0 0 7
$$

$$
0. 4 7 4 \pm 0. 0 0 5
$$

$$
0. 8 6 0 \pm 0. 0 0 2
$$

$$
0. 8 6 2 \pm 0. 0 0 3
$$

$$
0. 4 1 8 \pm 0. 0 0 2
$$

$$
0. 8 5 9 \pm 0. 0 0 2
$$

$$
0. 4 1 1 \pm 0. 0 0 0
$$

$$
0. 8 6 2 \pm 0. 0 0 2
$$

$$
0. 4 0 8 \pm 0. 0 0 3
$$

$$
0. 3 9 9 \pm 0. 0 0 2
$$

<table><tr><td colspan="3">HO ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>kNN</td><td>3.744 ± 0.000</td><td>-</td></tr><tr><td>DNNR</td><td>3.210 ± 0.000</td><td>-</td></tr><tr><td>DKL</td><td>3.423 ± 0.393</td><td>-</td></tr><tr><td>ANP</td><td>3.162 ± 0.028</td><td>-</td></tr><tr><td>NPT</td><td>3.175 ± 0.032</td><td>-</td></tr><tr><td>SAINT</td><td>3.242 ± 0.059</td><td>-</td></tr><tr><td>MLP</td><td>3.112 ± 0.036</td><td>-</td></tr><tr><td>MLP-PLR</td><td>3.056 ± 0.021</td><td>2.993 ± 0.019</td></tr><tr><td>TabR-S</td><td>3.067 ± 0.040</td><td>2.996 ± 0.027</td></tr><tr><td>TabR</td><td>3.105 ± 0.041</td><td>3.025 ± 0.010</td></tr><tr><td>CatBoost</td><td>3.117 ± 0.013</td><td>3.106 ± 0.002</td></tr><tr><td>XGBoost</td><td>3.177 ± 0.010</td><td>3.164 ± 0.007</td></tr><tr><td>LightGBM</td><td>3.177 ± 0.009</td><td>3.167 ± 0.005</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>CatBoost</td><td>3.122 ± 0.011</td><td>3.108 ± 0.002</td></tr><tr><td>XGBoost</td><td>3.368 ± 0.000</td><td>3.368 ± 0.000</td></tr><tr><td>LightGBM</td><td>3.222 ± 0.000</td><td>3.222 ± 0.000</td></tr><tr><td>TabR-S</td><td>3.093 ± 0.060</td><td>2.971 ± 0.017</td></tr><tr><td colspan="3">Tuned hyperparameters (Table 2)</td></tr><tr><td>step-0</td><td>3.234 ± 0.053</td><td>3.144 ± 0.034</td></tr><tr><td>step-1</td><td>3.205 ± 0.056</td><td>3.104 ± 0.043</td></tr><tr><td>step-2</td><td>3.153 ± 0.031</td><td>3.117 ± 0.012</td></tr><tr><td>step-3</td><td>3.158 ± 0.017</td><td>3.117 ± 0.006</td></tr></table>

<table><tr><td colspan="3">AD ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>kNN</td><td> $0.834 \pm 0.000$ </td><td>-</td></tr><tr><td>DNNR</td><td>-</td><td>-</td></tr><tr><td>DKL</td><td>-</td><td>-</td></tr><tr><td>ANP</td><td>-</td><td>-</td></tr><tr><td>NPT</td><td> $0.853 \pm 0.010$ </td><td>-</td></tr><tr><td>SAINT</td><td> $0.860 \pm 0.002$ </td><td>-</td></tr><tr><td>MLP</td><td> $0.853 \pm 0.001$ </td><td>-</td></tr><tr><td>MLP-PLR</td><td> $0.870 \pm 0.002$ </td><td> $0.873 \pm 0.001$ </td></tr><tr><td>TabR-S</td><td> $0.865 \pm 0.002$ </td><td> $0.868 \pm 0.002$ </td></tr><tr><td>TabR</td><td> $0.870 \pm 0.001$ </td><td> $0.872 \pm 0.001$ </td></tr><tr><td>CatBoost</td><td> $0.871 \pm 0.001$ </td><td> $0.872 \pm 0.001$ </td></tr><tr><td>XGBoost</td><td> $0.872 \pm 0.001$ </td><td> $0.872 \pm 0.000$ </td></tr><tr><td>LightGBM</td><td> $0.871 \pm 0.001$ </td><td> $0.872 \pm 0.000$ </td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>CatBoost</td><td> $0.873 \pm 0.001$ </td><td> $0.874 \pm 0.001$ </td></tr><tr><td>XGBoost</td><td> $0.871 \pm 0.000$ </td><td> $0.871 \pm 0.000$ </td></tr><tr><td>LightGBM</td><td> $0.869 \pm 0.000$ </td><td> $0.869 \pm 0.000$ </td></tr><tr><td>TabR-S</td><td> $0.858 \pm 0.001$ </td><td> $0.859 \pm 0.000$ </td></tr><tr><td colspan="3">Tuned hyperparameters (Table 2)</td></tr><tr><td>step-0</td><td> $0.857 \pm 0.002$ </td><td> $0.858 \pm 0.000$ </td></tr><tr><td>step-1</td><td> $0.857 \pm 0.002$ </td><td> $0.860 \pm 0.000$ </td></tr><tr><td>step-2</td><td> $0.858 \pm 0.002$ </td><td> $0.862 \pm 0.001$ </td></tr><tr><td>step-3</td><td> $0.863 \pm 0.002$ </td><td> $0.866 \pm 0.001$ </td></tr></table>

DI ↓

OT ↑

$$
0. 2 5 6 \pm 0. 0 0 0
$$

$$
0. 1 4 5 \pm 0. 0 0 0
$$

$$
0. 7 7 4 \pm 0. 0 0 0
$$

$$
0. 1 4 7 \pm 0. 0 0 5
$$

$$
0. 1 4 0 \pm 0. 0 0 1
$$

$$
0. 1 3 8 \pm 0. 0 0 1
$$

$$
0. 8 1 5 \pm 0. 0 0 2
$$

$$
0. 1 3 7 \pm 0. 0 0 2
$$

$$
0. 8 1 2 \pm 0. 0 0 2
$$

$$
0. 1 4 0 \pm 0. 0 0 1
$$

$$
0. 8 1 6 \pm 0. 0 0 3
$$

$$
0. 1 3 4 \pm 0. 0 0 1
$$

$$
0. 1 3 3 \pm 0. 0 0 0
$$

$$
\mathrm{MLP-PLR}
$$

$$
0. 8 1 9 \pm 0. 0 0 2
$$

$$
0. 8 2 2 \pm 0. 0 0 2
$$

$$
0. 1 3 3 \pm 0. 0 0 1
$$

$$
0. 1 3 1 \pm 0. 0 0 0
$$

$$
0. 8 1 8 \pm 0. 0 0 2
$$

$$
0. 8 2 4 \pm 0. 0 0 1
$$

$$
0. 1 3 3 \pm 0. 0 0 1
$$

$$
0. 1 3 1 \pm 0. 0 0 0
$$

$$
0. 8 2 5 \pm 0. 0 0 2
$$

$$
0. 8 3 1 \pm 0. 0 0 1
$$

$$
0. 1 3 4 \pm 0. 0 0 1
$$

$$
0. 1 3 3 \pm 0. 0 0 0
$$

$$
0. 8 2 5 \pm 0. 0 0 1
$$

$$
0. 8 2 7 \pm 0. 0 0 0
$$

$$
0. 1 3 7 \pm 0. 0 0 0
$$

$$
0. 1 3 6 \pm 0. 0 0 0
$$

$$
0. 8 3 0 \pm 0. 0 0 1
$$

$$
0. 8 3 2 \pm 0. 0 0 1
$$

$$
0. 8 3 0 \pm 0. 0 0 1
$$

$$
0. 8 3 2 \pm 0. 0 0 1
$$

$$
0. 8 2 0 \pm 0. 0 0 1
$$

$$
0. 8 2 2 \pm 0. 0 0 1
$$

$$
0. 8 1 7 \pm 0. 0 0 0
$$

$$
0. 1 3 7 \pm 0. 0 0 0 0. 1 3 7 \pm 0. 0 0 0
$$

$$
0. 1 3 1 \pm 0. 0 0 0
$$

$$
0. 8 2 6 \pm 0. 0 0 0
$$

$$
0. 8 1 6 \pm 0. 0 0 2
$$

$$
0. 8 2 4 \pm 0. 0 0 0
$$

$$
0. 1 4 2 \pm 0. 0 0 1
$$

$$
0. 1 3 9 \pm 0. 0 0 1
$$

$$
0. 8 1 4 \pm 0. 0 0 2
$$

$$
0. 8 2 3 \pm 0. 0 0 2
$$

$$
0. 1 4 2 \pm 0. 0 0 2
$$

$$
0. 1 3 8 \pm 0. 0 0 0
$$

$$
0. 8 1 4 \pm 0. 0 0 2
$$

$$
0. 8 2 4 \pm 0. 0 0 1
$$

$$
0. 1 4 0 \pm 0. 0 0 1
$$

$$
0. 1 3 9 \pm 0. 0 0 1
$$

$$
0. 8 1 3 \pm 0. 0 0 2
$$

$$
0. 8 1 8 \pm 0. 0 0 1
$$

$$
0. 1 3 5 \pm 0. 0 0 1
$$

$$
0. 1 3 3 \pm 0. 0 0 1
$$

$$
\mathrm{step-3}
$$

$$
0. 8 1 0 \pm 0. 0 0 2
$$

$$
0. 8 1 4 \pm 0. 0 0 1
$$

<table><tr><td colspan="3">HI ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>kNN</td><td>0.665 ± 0.000</td><td>-</td></tr><tr><td>DNNR</td><td>-</td><td>-</td></tr><tr><td>DKL</td><td>-</td><td>-</td></tr><tr><td>ANP</td><td>-</td><td>-</td></tr><tr><td>NPT</td><td>0.721 ± 0.003</td><td>-</td></tr><tr><td>SAINT</td><td>0.724 ± 0.002</td><td>-</td></tr><tr><td>MLP</td><td>0.719 ± 0.002</td><td>-</td></tr><tr><td>MLP-PLR</td><td>0.729 ± 0.002</td><td>0.735 ± 0.000</td></tr><tr><td>TabR-S</td><td>0.722 ± 0.001</td><td>0.726 ± 0.001</td></tr><tr><td>TabR</td><td>0.729 ± 0.001</td><td>0.733 ± 0.001</td></tr><tr><td>CatBoost</td><td>0.726 ± 0.001</td><td>0.727 ± 0.001</td></tr><tr><td>XGBoost</td><td>0.725 ± 0.002</td><td>0.726 ± 0.001</td></tr><tr><td>LightGBM</td><td>0.726 ± 0.001</td><td>0.726 ± 0.001</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>CatBoost</td><td>0.725 ± 0.001</td><td>0.726 ± 0.001</td></tr><tr><td>XGBoost</td><td>0.716 ± 0.000</td><td>0.716 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.720 ± 0.000</td><td>0.720 ± 0.000</td></tr><tr><td>TabR-S</td><td>0.719 ± 0.002</td><td>0.724 ± 0.000</td></tr><tr><td colspan="3">Tuned hyperparameters (Table 2)</td></tr><tr><td>step-0</td><td>0.719 ± 0.002</td><td>0.727 ± 0.000</td></tr><tr><td>step-1</td><td>0.719 ± 0.002</td><td>0.724 ± 0.001</td></tr><tr><td>step-2</td><td>0.720 ± 0.002</td><td>0.723 ± 0.001</td></tr><tr><td>step-3</td><td>0.722 ± 0.002</td><td>0.724 ± 0.000</td></tr></table>

<table><tr><td colspan="3">BL ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>kNN</td><td>0.712 ± 0.000</td><td>-</td></tr><tr><td>DNNR</td><td>0.704 ± 0.000</td><td>-</td></tr><tr><td>DKL</td><td>0.699 ± 0.001</td><td>-</td></tr><tr><td>ANP</td><td>0.705 ± 0.005</td><td>-</td></tr><tr><td>NPT</td><td>0.692 ± 0.001</td><td>-</td></tr><tr><td>SAINT</td><td>0.693 ± 0.001</td><td>-</td></tr><tr><td>MLP</td><td>0.697 ± 0.001</td><td>-</td></tr><tr><td>MLP-PLR</td><td>0.687 ± 0.000</td><td>0.684 ± 0.000</td></tr><tr><td>TabR-S</td><td>0.690 ± 0.000</td><td>0.688 ± 0.000</td></tr><tr><td>TabR</td><td>0.676 ± 0.001</td><td>0.674 ± 0.001</td></tr><tr><td>CatBoost</td><td>0.682 ± 0.000</td><td>0.681 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.681 ± 0.000</td><td>0.680 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.680 ± 0.000</td><td>0.679 ± 0.000</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>CatBoost</td><td>0.685 ± 0.000</td><td>0.684 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.683 ± 0.000</td><td>0.683 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.681 ± 0.000</td><td>0.681 ± 0.000</td></tr><tr><td>TabR-S</td><td>0.691 ± 0.000</td><td>0.688 ± 0.000</td></tr><tr><td colspan="3">Tuned hyperparameters (Table 2)</td></tr><tr><td>step-0</td><td>0.699 ± 0.001</td><td>0.694 ± 0.001</td></tr><tr><td>step-1</td><td>0.698 ± 0.001</td><td>0.693 ± 0.001</td></tr><tr><td>step-2</td><td>0.692 ± 0.001</td><td>0.690 ± 0.000</td></tr><tr><td>step-3</td><td>0.692 ± 0.001</td><td>0.688 ± 0.000</td></tr></table>

WE ↓

$$
2. 2 9 6 \pm 0. 0 0 0
$$

$$
1. 9 1 3 \pm 0. 0 0 0
$$

$$
1. 9 0 2 \pm 0. 0 0 9
$$

$$
1. 9 4 7 \pm 0. 0 0 6
$$

$$
1. 9 3 3 \pm 0. 0 2 8
$$

$$
1. 9 0 5 \pm 0. 0 0 5
$$

$$
1. 8 6 0 \pm 0. 0 0 2
$$

$$
1. 8 3 3 \pm 0. 0 0 2
$$

$$
1. 7 4 7 \pm 0. 0 0 2
$$

$$
1. 7 1 8 \pm 0. 0 0 1
$$

$$
1. 6 9 0 \pm 0. 0 0 3
$$

$$
1. 6 6 1 \pm 0. 0 0 2
$$

$$
1. 8 0 7 \pm 0. 0 0 2
$$

$$
1. 7 7 3 \pm 0. 0 0 1
$$

$$
1. 7 8 4 \pm 0. 0 0 1
$$

$$
1. 7 7 1 \pm 0. 0 0 1
$$

$$
1. 7 6 9 \pm 0. 0 0 1
$$

$$
1. 7 6 1 \pm 0. 0 0 1
$$

$$
1. 8 8 6 \pm 0. 0 0 0
$$

$$
1. 8 9 5 \pm 0. 0 0 1
$$

$$
1. 9 2 0 \pm 0. 0 0 0
$$

$$
1. 9 2 0 \pm 0. 0 0 0
$$

$$
1. 8 1 7 \pm 0. 0 0 1
$$

$$
1. 8 4 5 \pm 0. 0 0 3
$$

$$
1. 7 2 1 \pm 0. 0 0 2
$$

$$
1. 7 5 5 \pm 0. 0 0 2
$$

$$
1. 8 3 5 \pm 0. 0 0 4
$$

$$
1. 8 4 5 \pm 0. 0 0 1
$$

$$
1. 9 0 3 \pm 0. 0 0 4
$$

$$
1. 9 0 6 \pm 0. 0 0 3
$$

$$
1. 7 5 4 \pm 0. 0 0 1
$$

$$
1. 7 6 5 \pm 0. 0 0 1
$$

$$
1. 8 0 4 \pm 0. 0 0 3
$$

$$
1. 8 1 4 \pm 0. 0 0 3
$$

<table><tr><td colspan="3">CO ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>kNN</td><td>0.927 ± 0.000</td><td>-</td></tr><tr><td>DNNR</td><td>-</td><td>-</td></tr><tr><td>DKL</td><td>-</td><td>-</td></tr><tr><td>ANP</td><td>-</td><td>-</td></tr><tr><td>NPT</td><td>0.966 ± 0.001</td><td>-</td></tr><tr><td>SAINT</td><td>0.964 ± 0.010</td><td>-</td></tr><tr><td>MLP</td><td>0.963 ± 0.001</td><td>-</td></tr><tr><td>MLP-PLR</td><td>0.970 ± 0.001</td><td>0.974 ± 0.000</td></tr><tr><td>TabR-S</td><td>0.973 ± 0.000</td><td>0.974 ± 0.000</td></tr><tr><td>TabR</td><td>0.976 ± 0.000</td><td>0.977 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.968 ± 0.000</td><td>0.969 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.971 ± 0.000</td><td>0.971 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.971 ± 0.000</td><td>0.971 ± 0.000</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>CatBoost</td><td>0.923 ± 0.000</td><td>0.924 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.966 ± 0.000</td><td>0.966 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.884 ± 0.016</td><td>0.899 ± 0.005</td></tr><tr><td>TabR-S</td><td>0.973 ± 0.001</td><td>0.974 ± 0.000</td></tr><tr><td colspan="3">Tuned hyperparameters (Table 2)</td></tr><tr><td>step-0</td><td>0.957 ± 0.002</td><td>0.965 ± 0.001</td></tr><tr><td>step-1</td><td>0.960 ± 0.002</td><td>0.967 ± 0.001</td></tr><tr><td>step-2</td><td>0.972 ± 0.000</td><td>0.973 ± 0.000</td></tr><tr><td>step-3</td><td>0.975 ± 0.001</td><td>0.976 ± 0.000</td></tr></table>

<table><tr><td colspan="3">MI ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>kNN</td><td> $0.764 \pm 0.000$ </td><td>-</td></tr><tr><td>DNNR</td><td> $0.765 \pm 0.000$ </td><td>-</td></tr><tr><td>DKL</td><td>-</td><td>-</td></tr><tr><td>ANP</td><td>-</td><td>-</td></tr><tr><td>NPT</td><td> $0.753 \pm 0.001$ </td><td>-</td></tr><tr><td>SAINT</td><td> $0.763 \pm 0.007$ </td><td>-</td></tr><tr><td>MLP</td><td> $0.748 \pm 0.000$ </td><td>-</td></tr><tr><td>MLP-PLR</td><td> $0.744 \pm 0.000$ </td><td> $0.743 \pm 0.000$ </td></tr><tr><td>TabR-S</td><td> $0.750 \pm 0.001$ </td><td> $0.749 \pm 0.000$ </td></tr><tr><td>TabR</td><td> $0.750 \pm 0.001$ </td><td> $0.748 \pm 0.000$ </td></tr><tr><td>CatBoost</td><td> $0.741 \pm 0.000$ </td><td> $0.741 \pm 0.000$ </td></tr><tr><td>XGBoost</td><td> $0.741 \pm 0.000$ </td><td> $0.741 \pm 0.000$ </td></tr><tr><td>LightGBM</td><td> $0.742 \pm 0.000$ </td><td> $0.741 \pm 0.000$ </td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>CatBoost</td><td> $0.745 \pm 0.000$ </td><td> $0.744 \pm 0.000$ </td></tr><tr><td>XGBoost</td><td> $0.750 \pm 0.000$ </td><td> $0.750 \pm 0.000$ </td></tr><tr><td>LightGBM</td><td> $0.747 \pm 0.000$ </td><td> $0.744 \pm 0.000$ </td></tr><tr><td>TabR-S</td><td> $0.757 \pm 0.001$ </td><td> $0.752 \pm 0.001$ </td></tr></table>

Table 28: Extended results for Grinsztajn et al. (2022) benchmark. Results are grouped by datasets and span multiple pages below. Notation: ↓ corresponds to RMSE, ↑ corresponds to accuracy.

Ailerons ↓

$$
1. 6 2 4 \pm 0. 0 3 5
$$

$$
1. 6 2 0 \pm 0. 0 3 7
$$

$$
1. 5 9 1 \pm 0. 0 2 1
$$

$$
1. 5 8 2 \pm 0. 0 1 9
$$

$$
1. 6 2 0 \pm 0. 0 3 0
$$

$$
1. 5 9 5 \pm 0. 0 2 2
$$

$$
4 3. 2 0 3 \pm 0. 1 3 2
$$

$$
1. 6 1 5 \pm 0. 0 3 5
$$

$$
1. 5 8 5 \pm 0. 0 4 2
$$

$$
4 1. 4 7 0 \pm 0. 3 2 4
$$

$$
1. 5 3 3 \pm 0. 0 3 4
$$

$$
1. 5 2 7 \pm 0. 0 3 7
$$

$$
4 2. 3 3 9 \pm 0. 4 1 5
$$

$$
1. 5 6 5 \pm 0. 0 4 0
$$

$$
1. 5 7 1 \pm 0. 0 4 1
$$

$$
4 1. 2 2 7 \pm 0. 6 1 5
$$

$$
1. 5 7 7 \pm 0. 0 4 0
$$

$$
4 0. 5 5 2 \pm 0. 0 9 0
$$

$$
1. 5 8 1 \pm 0. 0 3 8
$$

$$
4 2. 6 0 6 \pm 0. 0 3 9
$$

$$
1. 5 9 9 \pm 0. 0 2 9
$$

$$
4 2. 3 4 2 \pm 0. 1 4 9
$$

$$
1. 5 3 8 \pm 0. 0 4 3
$$

$$
1. 6 1 5 \pm 0. 0 2 9
$$

$$
1. 5 4 2 \pm 0. 0 4 1
$$

$$
1. 6 4 4 \pm 0. 0 4 8
$$

$$
1. 5 9 4 \pm 0. 0 5 3
$$

$$
1. 6 4 4 \pm 0. 0 4 6
$$

$$
4 2. 3 6 9 \pm 0. 3 5 4
$$

$$
1. 5 9 4 \pm 0. 0 5 1
$$

$$
4 2. 8 4 8 \pm 0. 2 5 6
$$

$$
4 2. 6 2 6 \pm 0. 2 4 3
$$

$$
4 3. 4 8 6 \pm 0. 5 7 3
$$

$$
4 5. 1 0 0 \pm 0. 3 8 1
$$

<table><tr><td colspan="3">Brazilian houses ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.049 ± 0.018</td><td>0.046 ± 0.021</td></tr><tr><td>MLP-PLR</td><td>0.043 ± 0.019</td><td>0.040 ± 0.022</td></tr><tr><td>TabR-S</td><td>0.049 ± 0.015</td><td>0.045 ± 0.017</td></tr><tr><td>TabR</td><td>0.045 ± 0.016</td><td>0.041 ± 0.017</td></tr><tr><td>CatBoost</td><td>0.047 ± 0.031</td><td>0.046 ± 0.033</td></tr><tr><td>XGBoost</td><td>0.054 ± 0.027</td><td>0.053 ± 0.029</td></tr><tr><td>LightGBM</td><td>0.060 ± 0.025</td><td>0.059 ± 0.027</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.052 ± 0.016</td><td>0.048 ± 0.018</td></tr><tr><td>CatBoost</td><td>0.043 ± 0.027</td><td>0.042 ± 0.029</td></tr><tr><td>XGBoost</td><td>0.052 ± 0.025</td><td>0.052 ± 0.027</td></tr><tr><td>LightGBM</td><td>0.071 ± 0.021</td><td>0.071 ± 0.022</td></tr></table>

$$
4 3. 0 8 9 \pm 0. 1 0 3
$$

$$
4 5. 1 0 0 \pm 0. 4 1 0
$$

$$
4 3. 0 8 9 \pm 0. 1 1 1
$$

$$
4 0. 9 2 7 \pm 0. 2 3 2
$$

$$
4 2. 6 1 5 \pm 0. 4 1 5
$$

$$
4 2. 5 0 3 \pm 0. 1 9 0
$$

$$
4 2. 6 4 9 \pm 0. 9 3 9
$$

$$
4 2. 7 6 6 \pm 0. 1 2 6
$$

$$
4 3. 6 3 7 \pm 0. 6 8 1
$$

<table><tr><td colspan="3">KDDCup09 upselling ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td> $0.776 \pm 0.011$ </td><td> $0.782 \pm 0.009$ </td></tr><tr><td>MLP-PLR</td><td> $0.797 \pm 0.009$ </td><td> $0.802 \pm 0.010$ </td></tr><tr><td>TabR-S</td><td> $0.784 \pm 0.014$ </td><td> $0.786 \pm 0.017$ </td></tr><tr><td>TabR</td><td> $0.791 \pm 0.012$ </td><td> $0.803 \pm 0.008$ </td></tr><tr><td>CatBoost</td><td> $0.799 \pm 0.012$ </td><td> $0.801 \pm 0.012$ </td></tr><tr><td>XGBoost</td><td> $0.793 \pm 0.011$ </td><td> $0.795 \pm 0.010$ </td></tr><tr><td>LightGBM</td><td> $0.793 \pm 0.012$ </td><td> $0.797 \pm 0.011$ </td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td> $0.772 \pm 0.013$ </td><td> $0.781 \pm 0.013$ </td></tr><tr><td>CatBoost</td><td> $0.804 \pm 0.008$ </td><td> $0.804 \pm 0.006$ </td></tr><tr><td>XGBoost</td><td> $0.794 \pm 0.008$ </td><td> $0.794 \pm 0.009$ </td></tr><tr><td>LightGBM</td><td> $0.789 \pm 0.007$ </td><td> $0.789 \pm 0.007$ </td></tr></table>

Bike Sharing Demand ↓

$$
4 5. 7 0 2 \pm 0. 7 5 6
$$

<table><tr><td colspan="3">Higgs ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.723 ± 0.002</td><td>0.725 ± 0.001</td></tr><tr><td>MLP-PLR</td><td>0.728 ± 0.001</td><td>0.730 ± 0.001</td></tr><tr><td>TabR-S</td><td>0.725 ± 0.001</td><td>0.728 ± 0.000</td></tr><tr><td>TabR</td><td>0.730 ± 0.001</td><td>0.733 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.729 ± 0.000</td><td>0.730 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.729 ± 0.001</td><td>0.730 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.727 ± 0.001</td><td>0.728 ± 0.000</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.722 ± 0.001</td><td>0.727 ± 0.001</td></tr><tr><td>CatBoost</td><td>0.727 ± 0.001</td><td>0.728 ± 0.001</td></tr><tr><td>XGBoost</td><td>0.718 ± 0.000</td><td>0.718 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.721 ± 0.000</td><td>0.721 ± 0.000</td></tr></table>

<table><tr><td colspan="3">MagicTelescope ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.853 ± 0.006</td><td>0.857 ± 0.004</td></tr><tr><td>MLP-PLR</td><td>0.860 ± 0.007</td><td>0.863 ± 0.007</td></tr><tr><td>TabR-S</td><td>0.868 ± 0.006</td><td>0.873 ± 0.004</td></tr><tr><td>TabR</td><td>0.864 ± 0.005</td><td>0.868 ± 0.002</td></tr><tr><td>CatBoost</td><td>0.859 ± 0.007</td><td>0.859 ± 0.008</td></tr><tr><td>XGBoost</td><td>0.855 ± 0.009</td><td>0.859 ± 0.011</td></tr><tr><td>LightGBM</td><td>0.855 ± 0.008</td><td>0.856 ± 0.009</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.868 ± 0.006</td><td>0.871 ± 0.005</td></tr><tr><td>CatBoost</td><td>0.860 ± 0.007</td><td>0.860 ± 0.008</td></tr><tr><td>XGBoost</td><td>0.856 ± 0.011</td><td>0.856 ± 0.012</td></tr><tr><td>LightGBM</td><td>0.859 ± 0.009</td><td>0.859 ± 0.010</td></tr></table>

Mercedes Benz Greener Manufacturing ↓

MiamiHousing2016 ↓

$$
8. 3 8 3 \pm 0. 8 5 4
$$

$$
8. 3 3 6 \pm 0. 8 8 8
$$

$$
8. 3 8 3 \pm 0. 8 5 4
$$

$$
8. 3 3 6 \pm 0. 8 8 8
$$

$$
0. 1 6 1 \pm 0. 0 0 3
$$

$$
0. 1 5 7 \pm 0. 0 0 3
$$

$$
8. 3 5 1 \pm 0. 8 1 5
$$

$$
8. 2 6 9 \pm 0. 8 4 0
$$

$$
0. 1 5 0 \pm 0. 0 0 2
$$

$$
0. 1 4 7 \pm 0. 0 0 2
$$

$$
0. 1 4 2 \pm 0. 0 0 2
$$

$$
8. 3 1 9 \pm 0. 8 1 9
$$

$$
0. 1 3 9 \pm 0. 0 0 2
$$

$$
8. 2 4 4 \pm 0. 8 4 4
$$

$$
0. 1 3 9 \pm 0. 0 0 2
$$

$$
0. 1 3 6 \pm 0. 0 0 2
$$

$$
8. 1 6 3 \pm 0. 8 1 9
$$

$$
8. 1 5 5 \pm 0. 8 4 4
$$

$$
0. 1 4 2 \pm 0. 0 0 2
$$

$$
0. 1 4 1 \pm 0. 0 0 3
$$

$$
8. 2 1 8 \pm 0. 8 1 7
$$

$$
8. 2 0 9 \pm 0. 8 4 6
$$

$$
0. 1 4 4 \pm 0. 0 0 3
$$

$$
0. 1 4 3 \pm 0. 0 0 3
$$

$$
8. 2 0 8 \pm 0. 8 2 3
$$

$$
8. 1 6 2 \pm 0. 8 5 7
$$

$$
0. 1 4 6 \pm 0. 0 0 2
$$

$$
0. 1 4 5 \pm 0. 0 0 3
$$

$$
8. 2 9 0 \pm 0. 8 3 8
$$

$$
8. 2 2 3 \pm 0. 8 6 5
$$

$$
0. 1 4 1 \pm 0. 0 0 2
$$

$$
0. 1 3 9 \pm 0. 0 0 2
$$

$$
8. 1 6 7 \pm 0. 8 2 5
$$

$$
8. 1 6 4 \pm 0. 8 4 8
$$

$$
0. 1 4 2 \pm 0. 0 0 3
$$

$$
0. 1 4 1 \pm 0. 0 0 3
$$

$$
8. 3 7 1 \pm 0. 7 8 7
$$

$$
8. 3 7 1 \pm 0. 8 1 0
$$

$$
0. 1 6 0 \pm 0. 0 0 3
$$

$$
0. 1 6 0 \pm 0. 0 0 3
$$

$$
8. 2 8 0 \pm 0. 8 4 5
$$

$$
8. 2 8 0 \pm 0. 8 6 9
$$

$$
0. 1 5 2 \pm 0. 0 0 4
$$

$$
0. 1 5 2 \pm 0. 0 0 4
$$

$$
0. 9 4 7 \pm 0. 0 0 1
$$

$$
0. 9 4 7 \pm 0. 0 0 1
$$

$$
0. 9 4 8 \pm 0. 0 0 1
$$

$$
0. 9 4 9 \pm 0. 0 0 1
$$

$$
0. 9 4 9 \pm 0. 0 0 0
$$

$$
0. 9 4 8 \pm 0. 0 0 1
$$

$$
0. 9 5 0 \pm 0. 0 0 0
$$

$$
0. 9 4 5 \pm 0. 0 0 1
$$

$$
0. 9 4 9 \pm 0. 0 0 0
$$

$$
0. 9 4 4 \pm 0. 0 0 1
$$

$$
0. 9 4 6 \pm 0. 0 0 1
$$

$$
0. 9 4 5 \pm 0. 0 0 0
$$

$$
0. 9 4 2 \pm 0. 0 0 1
$$

$$
0. 9 4 3 \pm 0. 0 0 0
$$

$$
0. 9 4 7 \pm 0. 0 0 1
$$

$$
0. 9 5 0 \pm 0. 0 0 1
$$

$$
0. 9 4 5 \pm 0. 0 0 1
$$

$$
0. 9 4 5 \pm 0. 0 0 0
$$

$$
0. 9 4 2 \pm 0. 0 0 0
$$

$$
0. 9 4 2 \pm 0. 0 0 0
$$

$$
0. 9 4 4 \pm 0. 0 0 0
$$

<table><tr><td colspan="3">SGEMM GPU kernel performance ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.016 ± 0.000</td><td>0.016 ± 0.000</td></tr><tr><td>MLP-PLR</td><td>0.015 ± 0.000</td><td>0.015 ± 0.000</td></tr><tr><td>TabR-S</td><td>0.017 ± 0.001</td><td>0.016 ± 0.000</td></tr><tr><td>TabR</td><td>0.015 ± 0.000</td><td>0.015 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.017 ± 0.000</td><td>0.017 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.017 ± 0.000</td><td>0.017 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.017 ± 0.000</td><td>0.017 ± 0.000</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.017 ± 0.001</td><td>0.016 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.017 ± 0.000</td><td>0.017 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.017 ± 0.000</td><td>0.017 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.017 ± 0.000</td><td>0.017 ± 0. 000</td></tr></table>

$$
0. 9 4 4 \pm 0. 0 0 0
$$

<table><tr><td colspan="3">OnlineNewsPopularity ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.862 ± 0.001</td><td>0.860 ± 0.000</td></tr><tr><td>MLP-PLR</td><td>0.862 ± 0.001</td><td>0.860 ± 0.000</td></tr><tr><td>TabR-S</td><td>0.868 ± 0.001</td><td>0.863 ± 0.001</td></tr><tr><td>TabR</td><td>0.862 ± 0.001</td><td>0.859 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.853 ± 0.000</td><td>0.853 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.854 ± 0.000</td><td>0.854 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.855 ± 0.000</td><td>0.854 ± 0.000</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.870 ± 0.001</td><td>0.864 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.855 ± 0.000</td><td>0.854 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.874 ± 0.000</td><td>0.874 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.862 ± 0.000</td><td>0.862 ± 0.000</td></tr></table>

<table><tr><td colspan="3">analcatdata supreme ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.078 ± 0.009</td><td>0.077 ± 0.010</td></tr><tr><td>MLP-PLR</td><td>0.079 ± 0.008</td><td>0.077 ± 0.008</td></tr><tr><td>TabR-S</td><td>0.080 ± 0.007</td><td>0.076 ± 0.005</td></tr><tr><td>TabR</td><td>0.081 ± 0.009</td><td>0.075 ± 0.005</td></tr><tr><td>CatBoost</td><td>0.078 ± 0.007</td><td>0.073 ± 0.002</td></tr><tr><td>XGBoost</td><td>0.080 ± 0.013</td><td>0.077 ± 0.011</td></tr><tr><td>LightGBM</td><td>0.078 ± 0.012</td><td>0.077 ± 0.011</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.077 ± 0.007</td><td>0.074 ± 0.007</td></tr><tr><td>CatBoost</td><td>0.071 ± 0.004</td><td>0.071 ± 0.004</td></tr><tr><td>XGBoost</td><td>0.076 ± 0.006</td><td>0.076 ± 0.006</td></tr><tr><td>LightGBM</td><td>0.073 ± 0.006</td><td>0.073 ± 0.006</td></tr></table>

bank-marketing ↑

black friday ↓

$$
0. 7 8 6 \pm 0. 0 0 6
$$

$$
0. 7 9 0 \pm 0. 0 0 4
$$

$$
0. 7 9 5 \pm 0. 0 0 5
$$

$$
0. 7 9 8 \pm 0. 0 0 4
$$

$$
0. 3 6 9 \pm 0. 0 0 0
$$

$$
0. 3 6 7 \pm 0. 0 0 0
$$

$$
0. 3 6 3 \pm 0. 0 0 0
$$

$$
0. 8 0 0 \pm 0. 0 0 5
$$

$$
0. 3 6 3 \pm 0. 0 0 0
$$

$$
0. 8 0 2 \pm 0. 0 0 4
$$

$$
0. 3 6 4 \pm 0. 0 0 0
$$

$$
0. 3 6 3 \pm 0. 0 0 0
$$

$$
0. 8 0 2 \pm 0. 0 0 9
$$

$$
0. 8 0 4 \pm 0. 0 1 0
$$

$$
0. 3 6 2 \pm 0. 0 0 2
$$

$$
0. 3 5 9 \pm 0. 0 0 1
$$

$$
0. 8 0 3 \pm 0. 0 0 7
$$

$$
0. 8 0 6 \pm 0. 0 0 8
$$

$$
0. 3 6 1 \pm 0. 0 0 0
$$

$$
0. 3 6 0 \pm 0. 0 0 0
$$

$$
0. 8 0 1 \pm 0. 0 0 8
$$

$$
0. 8 0 3 \pm 0. 0 0 8
$$

$$
0. 3 6 0 \pm 0. 0 0 0
$$

$$
0. 3 6 0 \pm 0. 0 0 0
$$

$$
0. 8 0 1 \pm 0. 0 0 8
$$

$$
0. 8 0 1 \pm 0. 0 0 7
$$

$$
0. 3 6 0 \pm 0. 0 0 0
$$

$$
0. 3 6 0 \pm 0. 0 0 0
$$

$$
0. 8 0 0 \pm 0. 0 0 6
$$

$$
0. 8 0 1 \pm 0. 0 0 5
$$

$$
0. 3 6 4 \pm 0. 0 0 0
$$

$$
0. 3 6 3 \pm 0. 0 0 0
$$

$$
0. 8 0 3 \pm 0. 0 0 9
$$

$$
0. 8 0 3 \pm 0. 0 0 9
$$

$$
0. 3 6 1 \pm 0. 0 0 0
$$

$$
0. 8 0 0 \pm 0. 0 0 9
$$

$$
0. 3 6 1 \pm 0. 0 0 0
$$

$$
0. 8 0 0 \pm 0. 0 0 9
$$

$$
0. 3 6 2 \pm 0. 0 0 0
$$

$$
0. 8 0 3 \pm 0. 0 0 4
$$

$$
0. 3 6 2 \pm 0. 0 0 0
$$

$$
0. 8 0 3 \pm 0. 0 0 4
$$

$$
0. 3 6 1 \pm 0. 0 0 0
$$

$$
0. 3 6 1 \pm 0. 0 0 0
$$

$$
0. 1 4 9 \pm 0. 0 0 2
$$

$$
0. 1 4 6 \pm 0. 0 0 1
$$

$$
0. 1 3 8 \pm 0. 0 0 1
$$

$$
0. 7 6 8 \pm 0. 0 0 5
$$

$$
0. 1 3 5 \pm 0. 0 0 0
$$

$$
0. 7 7 6 \pm 0. 0 0 6
$$

$$
0. 7 8 3 \pm 0. 0 0 7
$$

$$
0. 1 2 4 \pm 0. 0 0 1
$$

$$
0. 1 2 1 \pm 0. 0 0 0
$$

$$
0. 7 9 6 \pm 0. 0 0 6
$$

$$
0. 8 6 3 \pm 0. 0 0 3
$$

$$
0. 8 7 0 \pm 0. 0 0 3
$$

$$
0. 1 2 2 \pm 0. 0 0 1
$$

$$
0. 1 2 0 \pm 0. 0 0 0
$$

$$
0. 8 7 1 \pm 0. 0 0 3
$$

$$
0. 8 7 9 \pm 0. 0 0 1
$$

$$
0. 1 2 9 \pm 0. 0 0 0
$$

$$
0. 1 2 8 \pm 0. 0 0 0
$$

$$
0. 7 7 1 \pm 0. 0 0 4
$$

$$
0. 7 7 5 \pm 0. 0 0 3
$$

$$
0. 1 3 1 \pm 0. 0 0 1
$$

$$
0. 1 3 0 \pm 0. 0 0 0
$$

$$
0. 8 1 9 \pm 0. 0 0 5
$$

$$
0. 8 2 2 \pm 0. 0 0 3
$$

$$
0. 1 3 1 \pm 0. 0 0 1
$$

$$
0. 1 3 0 \pm 0. 0 0 0
$$

$$
0. 7 7 1 \pm 0. 0 0 3
$$

$$
0. 7 7 3 \pm 0. 0 0 3
$$

$$
0. 1 2 4 \pm 0. 0 0 1
$$

$$
0. 1 2 2 \pm 0. 0 0 0
$$

$$
0. 8 6 5 \pm 0. 0 0 4
$$

$$
0. 8 7 0 \pm 0. 0 0 1
$$

$$
0. 1 2 9 \pm 0. 0 0 0
$$

$$
0. 1 2 9 \pm 0. 0 0 0
$$

$$
0. 7 5 8 \pm 0. 0 0 2
$$

$$
0. 7 6 0 \pm 0. 0 0 1
$$

$$
0. 1 4 1 \pm 0. 0 0 0
$$

$$
0. 1 4 1 \pm 0. 0 0 0
$$

$$
0. 7 5 1 \pm 0. 0 0 0
$$

$$
0. 1 3 5 \pm 0. 0 0 0
$$

$$
0. 7 5 1 \pm 0. 0 0 0
$$

$$
0. 1 3 5 \pm 0. 0 0 0
$$

$$
0. 7 6 2 \pm 0. 0 0 4
$$

$$
0. 7 6 2 \pm 0. 0 0 4
$$

<table><tr><td colspan="3">covertype ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.929 ± 0.001</td><td>0.934 ± 0.001</td></tr><tr><td>MLP-PLR</td><td>0.944 ± 0.002</td><td>0.950 ± 0.001</td></tr><tr><td>TabR-S</td><td>0.953 ± 0.000</td><td>0.954 ± 0.000</td></tr><tr><td>TabR</td><td>0.957 ± 0.000</td><td>0.958 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.938 ± 0.000</td><td>0.939 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.940 ± 0.000</td><td>0.940 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.939 ± 0.000</td><td>0.939 ± 0.000</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.952 ± 0.000</td><td>0.953 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.912 ± 0.000</td><td>0.913 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.927 ± 0.000</td><td>0.927 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.936 ± 0.000</td><td>0.936 ± 0.000</td></tr></table>

<table><tr><td colspan="3">cpu act ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td> $2.712 \pm 0.207$ </td><td> $2.544 \pm 0.052$ </td></tr><tr><td>MLP-PLR</td><td> $2.270 \pm 0.048$ </td><td> $2.214 \pm 0.059$ </td></tr><tr><td>TabR-S</td><td> $2.298 \pm 0.053$ </td><td> $2.223 \pm 0.050$ </td></tr><tr><td>TabR</td><td> $2.128 \pm 0.078$ </td><td> $2.063 \pm 0.050$ </td></tr><tr><td>CatBoost</td><td> $2.124 \pm 0.049$ </td><td> $2.109 \pm 0.050$ </td></tr><tr><td>XGBoost</td><td> $2.524 \pm 0.353$ </td><td> $2.472 \pm 0.379$ </td></tr><tr><td>LightGBM</td><td> $2.222 \pm 0.089$ </td><td> $2.207 \pm 0.092$ </td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td> $2.285 \pm 0.045$ </td><td> $2.214 \pm 0.032$ </td></tr><tr><td>CatBoost</td><td> $2.185 \pm 0.088$ </td><td> $2.162 \pm 0.091$ </td></tr><tr><td>XGBoost</td><td> $2.910 \pm 0.463$ </td><td> $2.910 \pm 0.486$ </td></tr><tr><td>LightGBM</td><td> $2.274 \pm 0.128$ </td><td> $2.274 \pm 0.135$ </td></tr></table>

credit ↑

$$
0. 7 7 4 \pm 0. 0 0 3
$$

$$
0. 7 7 4 \pm 0. 0 0 4
$$

$$
0. 7 7 5 \pm 0. 0 0 6
$$

$$
0. 0 8 6 \pm 0. 0 0 0
$$

$$
0. 0 9 1 \pm 0. 0 0 2
$$

$$
0. 7 7 3 \pm 0. 0 0 4
$$

$$
0. 7 7 4 \pm 0. 0 0 4
$$

$$
0. 0 8 7 \pm 0. 0 0 1
$$

$$
0. 0 8 4 \pm 0. 0 0 1
$$

diamonds ↓

$$
0. 7 7 2 \pm 0. 0 0 4
$$

$$
0. 7 7 5 \pm 0. 0 0 3
$$

$$
0. 0 8 3 \pm 0. 0 0 1
$$

$$
0. 0 8 2 \pm 0. 0 0 0
$$

$$
0. 7 7 3 \pm 0. 0 0 3
$$

$$
0. 0 8 3 \pm 0. 0 0 1
$$

$$
0. 0 8 1 \pm 0. 0 0 0
$$

$$
0. 7 7 5 \pm 0. 0 0 4
$$

$$
0. 0 8 4 \pm 0. 0 0 0
$$

$$
0. 0 8 3 \pm 0. 0 0 0
$$

$$
0. 7 7 0 \pm 0. 0 0 3
$$

$$
0. 7 7 1 \pm 0. 0 0 3
$$

$$
0. 0 8 5 \pm 0. 0 0 0
$$

$$
0. 0 8 4 \pm 0. 0 0 0
$$

$$
0. 7 6 9 \pm 0. 0 0 3
$$

$$
0. 7 7 3 \pm 0. 0 0 3
$$

$$
0. 0 8 5 \pm 0. 0 0 0
$$

$$
0. 0 8 5 \pm 0. 0 0 0
$$

$$
0. 7 7 2 \pm 0. 0 0 5
$$

$$
0. 7 7 4 \pm 0. 0 0 5
$$

$$
0. 0 8 4 \pm 0. 0 0 1
$$

$$
0. 0 8 2 \pm 0. 0 0 1
$$

$$
0. 7 7 1 \pm 0. 0 0 5
$$

$$
0. 7 7 3 \pm 0. 0 0 2
$$

$$
0. 0 8 4 \pm 0. 0 0 0
$$

$$
0. 7 7 2 \pm 0. 0 0 2
$$

$$
0. 0 8 4 \pm 0. 0 0 0
$$

$$
0. 7 7 2 \pm 0. 0 0 2
$$

$$
0. 0 8 8 \pm 0. 0 0 0
$$

$$
0. 7 7 1 \pm 0. 0 0 3
$$

$$
0. 7 7 1 \pm 0. 0 0 3
$$

$$
0. 0 8 8 \pm 0. 0 0 0
$$

$$
0. 0 8 6 \pm 0. 0 0 0
$$

$$
0. 0 8 6 \pm 0. 0 0 0
$$

<table><tr><td colspan="3">electricity ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.832 ± 0.004</td><td>0.841 ± 0.002</td></tr><tr><td>MLP-PLR</td><td>0.841 ± 0.004</td><td>0.849 ± 0.000</td></tr><tr><td>TabR-S</td><td>0.924 ± 0.003</td><td>0.929 ± 0.001</td></tr><tr><td>TabR</td><td>0.937 ± 0.002</td><td>0.942 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.880 ± 0.002</td><td>0.882 ± 0.001</td></tr><tr><td>XGBoost</td><td>0.890 ± 0.001</td><td>0.891 ± 0.001</td></tr><tr><td>LightGBM</td><td>0.887 ± 0.001</td><td>0.887 ± 0.001</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.887 ± 0.004</td><td>0.893 ± 0.002</td></tr><tr><td>CatBoost</td><td>0.875 ± 0.001</td><td>0.877 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.882 ± 0.000</td><td>0.882 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.890 ± 0.000</td><td>0.890 ± 0.000</td></tr></table>

<table><tr><td colspan="3">fifa ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.803 ± 0.013</td><td>0.801 ± 0.015</td></tr><tr><td>MLP-PLR</td><td>0.794 ± 0.011</td><td>0.792 ± 0.012</td></tr><tr><td>TabR-S</td><td>0.790 ± 0.012</td><td>0.786 ± 0.012</td></tr><tr><td>TabR</td><td>0.791 ± 0.014</td><td>0.787 ± 0.016</td></tr><tr><td>CatBoost</td><td>0.783 ± 0.012</td><td>0.782 ± 0.011</td></tr><tr><td>XGBoost</td><td>0.780 ± 0.011</td><td>0.780 ± 0.011</td></tr><tr><td>LightGBM</td><td>0.781 ± 0.012</td><td>0.779 ± 0.012</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.790 ± 0.013</td><td>0.786 ± 0.012</td></tr><tr><td>CatBoost</td><td>0.782 ± 0.012</td><td>0.781 ± 0.013</td></tr><tr><td>XGBoost</td><td>0.790 ± 0.012</td><td>0.790 ± 0.013</td></tr><tr><td>LightGBM</td><td>0.780 ± 0.011</td><td>0.780 ± 0.011</td></tr></table>

<table><tr><td colspan="3">elevators ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.005 ± 0.000</td><td>0.005 ± 0.000</td></tr><tr><td>MLP-PLR</td><td>0.002 ± 0.000</td><td>0.002 ± 0.000</td></tr><tr><td>TabR-S</td><td>0.005 ± 0.000</td><td>0.005 ± 0.000</td></tr><tr><td>TabR</td><td>0.002 ± 0.000</td><td>0.002 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.002 ± 0.000</td><td>0.002 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.002 ± 0.000</td><td>0.002 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.002 ± 0.000</td><td>0.002 ± 0.000</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.005 ± 0.000</td><td>0.005 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.002 ± 0.000</td><td>0.002 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.002 ± 0.000</td><td>0.002 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.002 ± 0.000</td><td>0.002 ± 0.100</td></tr></table>

<table><tr><td colspan="3">house 16H ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.598 ± 0.012</td><td>0.587 ± 0.004</td></tr><tr><td>MLP-PLR</td><td>0.594 ± 0.003</td><td>0.589 ± 0.002</td></tr><tr><td>TabR-S</td><td>0.608 ± 0.016</td><td>0.590 ± 0.006</td></tr><tr><td>TabR</td><td>0.629 ± 0.024</td><td>0.599 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.599 ± 0.005</td><td>0.596 ± 0.003</td></tr><tr><td>XGBoost</td><td>0.591 ± 0.007</td><td>0.585 ± 0.004</td></tr><tr><td>LightGBM</td><td>0.575 ± 0.002</td><td>0.573 ± 0.001</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.603 ± 0.015</td><td>0.583 ± 0.003</td></tr><tr><td>CatBoost</td><td>0.591 ± 0.002</td><td>0.590 ± 0.001</td></tr><tr><td>XGBoost</td><td>0.589 ± 0.000</td><td>0.589 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.593 ± 0.000</td><td>0.593 ± 0.000</td></tr></table>

$$
0. 1 8 1 \pm 0. 0 0 1
$$

$$
0. 1 7 8 \pm 0. 0 0 0
$$

$$
0. 1 6 9 \pm 0. 0 0 1
$$

$$
0. 1 6 8 \pm 0. 0 0 0
$$

$$
0. 2 3 3 \pm 0. 0 0 2
$$

$$
0. 2 2 7 \pm 0. 0 0 1
$$

$$
0. 2 2 8 \pm 0. 0 0 2
$$

$$
0. 1 6 9 \pm 0. 0 0 1
$$

$$
0. 2 2 4 \pm 0. 0 0 0
$$

$$
0. 1 6 6 \pm 0. 0 0 0
$$

$$
0. 1 9 9 \pm 0. 0 0 1
$$

$$
0. 1 9 6 \pm 0. 0 0 0
$$

$$
0. 1 6 4 \pm 0. 0 0 1
$$

$$
0. 1 6 1 \pm 0. 0 0 0
$$

$$
0. 2 0 1 \pm 0. 0 0 2
$$

$$
0. 1 9 7 \pm 0. 0 0 0
$$

$$
0. 1 6 7 \pm 0. 0 0 0
$$

$$
0. 1 6 7 \pm 0. 0 0 0
$$

$$
0. 2 1 6 \pm 0. 0 0 1
$$

$$
0. 2 1 4 \pm 0. 0 0 0
$$

$$
0. 1 6 9 \pm 0. 0 0 0
$$

$$
0. 1 6 9 \pm 0. 0 0 0
$$

$$
0. 2 1 9 \pm 0. 0 0 1
$$

$$
0. 2 1 7 \pm 0. 0 0 0
$$

$$
0. 1 6 9 \pm 0. 0 0 0
$$

$$
0. 1 6 9 \pm 0. 0 0 0
$$

$$
0. 2 1 9 \pm 0. 0 0 1
$$

$$
0. 2 1 7 \pm 0. 0 0 0
$$

$$
0. 1 6 9 \pm 0. 0 0 1
$$

$$
0. 1 6 7 \pm 0. 0 0 0
$$

$$
0. 2 0 0 \pm 0. 0 0 1
$$

$$
0. 1 9 7 \pm 0. 0 0 1
$$

$$
0. 1 6 7 \pm 0. 0 0 0
$$

$$
0. 1 6 7 \pm 0. 0 0 0
$$

$$
0. 2 1 6 \pm 0. 0 0 0
$$

$$
0. 1 7 9 \pm 0. 0 0 0
$$

$$
0. 2 1 6 \pm 0. 0 0 0
$$

$$
0. 1 7 9 \pm 0. 0 0 0
$$

$$
0. 2 3 4 \pm 0. 0 0 0
$$

$$
0. 1 7 3 \pm 0. 0 0 0
$$

$$
0. 2 3 4 \pm 0. 0 0 0
$$

$$
0. 1 7 3 \pm 0. 0 0 0
$$

$$
0. 2 2 6 \pm 0. 0 0 0
$$

$$
0. 2 2 6 \pm 0. 0 0 0
$$

$$
2. 2 2 3 \pm 0. 1 8 9
$$

$$
2. 0 3 7 \pm 0. 1 0 6
$$

$$
2. 2 2 4 \pm 0. 1 5 6
$$

$$
0. 7 8 5 \pm 0. 0 0 3
$$

$$
2. 0 3 0 \pm 0. 1 0 3
$$

$$
0. 7 8 7 \pm 0. 0 0 2
$$

$$
1. 9 7 6 \pm 0. 1 7 4
$$

$$
0. 7 9 9 \pm 0. 0 0 3
$$

$$
1. 7 6 3 \pm 0. 1 5 2
$$

$$
0. 8 0 4 \pm 0. 0 0 1
$$

$$
0. 7 9 8 \pm 0. 0 0 2
$$

$$
1. 9 9 2 \pm 0. 1 8 1
$$

$$
0. 8 0 2 \pm 0. 0 0 2
$$

$$
0. 8 0 5 \pm 0. 0 0 2
$$

$$
0. 8 1 1 \pm 0. 0 0 1
$$

$$
2. 8 6 7 \pm 0. 0 1 4
$$

$$
2. 8 4 8 \pm 0. 0 0 2
$$

$$
0. 7 9 8 \pm 0. 0 0 2
$$

$$
0. 8 0 1 \pm 0. 0 0 1
$$

$$
2. 7 5 7 \pm 0. 0 4 7
$$

$$
2. 7 2 9 \pm 0. 0 3 7
$$

$$
0. 7 9 7 \pm 0. 0 0 2
$$

$$
0. 8 0 0 \pm 0. 0 0 1
$$

$$
2. 7 0 1 \pm 0. 0 3 0
$$

$$
2. 6 9 0 \pm 0. 0 2 9
$$

$$
0. 7 9 6 \pm 0. 0 0 2
$$

$$
0. 7 9 7 \pm 0. 0 0 1
$$

$$
1. 9 9 5 \pm 0. 1 5 6
$$

$$
1. 7 5 4 \pm 0. 1 0 6
$$

$$
0. 7 9 5 \pm 0. 0 0 2
$$

$$
0. 8 0 0 \pm 0. 0 0 1
$$

$$
2. 8 9 5 \pm 0. 0 2 0
$$

$$
2. 8 6 3 \pm 0. 0 1 3
$$

$$
0. 7 9 5 \pm 0. 0 0 1
$$

$$
0. 7 9 7 \pm 0. 0 0 0
$$

$$
3. 3 6 8 \pm 0. 0 1 0
$$

$$
3. 3 6 8 \pm 0. 0 1 1
$$

$$
0. 7 8 3 \pm 0. 0 0 0
$$

$$
2. 9 5 3 \pm 0. 0 5 6
$$

$$
0. 7 8 3 \pm 0. 0 0 0
$$

$$
2. 9 5 3 \pm 0. 0 5 8
$$

$$
0. 7 9 4 \pm 0. 0 0 0
$$

$$
0. 7 9 4 \pm 0. 0 0 0
$$

<table><tr><td colspan="3">kdd ipums la 97-small ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.880 ± 0.007</td><td>0.880 ± 0.006</td></tr><tr><td>MLP-PLR</td><td>0.883 ± 0.005</td><td>0.883 ± 0.005</td></tr><tr><td>TabR-S</td><td>0.880 ± 0.008</td><td>0.882 ± 0.008</td></tr><tr><td>TabR</td><td>0.883 ± 0.005</td><td>0.884 ± 0.005</td></tr><tr><td>CatBoost</td><td>0.879 ± 0.009</td><td>0.880 ± 0.010</td></tr><tr><td>XGBoost</td><td>0.883 ± 0.009</td><td>0.883 ± 0.008</td></tr><tr><td>LightGBM</td><td>0.879 ± 0.007</td><td>0.880 ± 0.007</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.877 ± 0.006</td><td>0.878 ± 0.007</td></tr><tr><td>CatBoost</td><td>0.879 ± 0.007</td><td>0.881 ± 0.007</td></tr><tr><td>XGBoost</td><td>0.883 ± 0.010</td><td>0.883 ± 0.011</td></tr><tr><td>LightGBM</td><td>0.884 ± 0.005</td><td>0.884 ± 0.005</td></tr></table>

<table><tr><td colspan="3">medical charges ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.082 ± 0.000</td><td>0.081 ± 0.000</td></tr><tr><td>MLP-PLR</td><td>0.081 ± 0.000</td><td>0.081 ± 0.000</td></tr><tr><td>TabR-S</td><td>0.081 ± 0.000</td><td>0.081 ± 0.000</td></tr><tr><td>TabR</td><td>0.081 ± 0.000</td><td>0.081 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.082 ± 0.000</td><td>0.082 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.082 ± 0.000</td><td>0.082 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.082 ± 0.000</td><td>0.082 ± 0.000</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.082 ± 0.000</td><td>0.081 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.082 ± 0.000</td><td>0.082 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.084 ± 0.000</td><td>0.084 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.083 ± 0.000</td><td>0.083 ± 0.000</td></tr></table>

nyc-taxi-green-dec-2016 ↓

particulate-matter-ukair-2017 ↓

$$
0. 3 9 7 \pm 0. 0 0 1
$$

$$
0. 3 9 1 \pm 0. 0 0 1
$$

$$
0. 3 6 8 \pm 0. 0 0 2
$$

$$
0. 3 6 4 \pm 0. 0 0 0
$$

$$
0. 3 7 7 \pm 0. 0 0 1
$$

$$
0. 3 7 4 \pm 0. 0 0 0
$$

$$
0. 3 6 7 \pm 0. 0 0 1
$$

$$
0. 3 6 6 \pm 0. 0 0 0
$$

$$
0. 3 5 8 \pm 0. 0 2 2
$$

$$
0. 3 3 8 \pm 0. 0 0 3
$$

$$
0. 3 6 1 \pm 0. 0 0 0
$$

$$
0. 3 5 9 \pm 0. 0 0 0
$$

$$
0. 3 7 2 \pm 0. 0 0 9
$$

$$
0. 3 5 0 \pm 0. 0 0 3
$$

$$
0. 3 6 0 \pm 0. 0 0 0
$$

$$
0. 3 5 8 \pm 0. 0 0 0
$$

$$
0. 3 6 5 \pm 0. 0 0 1
$$

$$
0. 3 6 3 \pm 0. 0 0 0
$$

$$
0. 3 6 5 \pm 0. 0 0 0
$$

$$
0. 3 6 4 \pm 0. 0 0 0
$$

$$
0. 3 7 9 \pm 0. 0 0 0
$$

$$
0. 3 7 9 \pm 0. 0 0 0
$$

$$
0. 3 6 4 \pm 0. 0 0 0
$$

$$
0. 3 6 4 \pm 0. 0 0 0
$$

$$
0. 3 6 9 \pm 0. 0 0 0
$$

$$
0. 3 6 8 \pm 0. 0 0 0
$$

$$
0. 3 6 4 \pm 0. 0 0 0
$$

$$
0. 3 6 3 \pm 0. 0 0 0
$$

$$
0. 3 8 9 \pm 0. 0 0 1
$$

$$
0. 3 8 5 \pm 0. 0 0 0
$$

$$
0. 3 6 1 \pm 0. 0 0 1
$$

$$
0. 3 5 9 \pm 0. 0 0 0
$$

$$
0. 3 6 6 \pm 0. 0 0 0
$$

$$
0. 3 6 6 \pm 0. 0 0 0
$$

$$
0. 3 6 6 \pm 0. 0 0 0
$$

$$
0. 3 8 6 \pm 0. 0 0 0
$$

$$
0. 3 6 6 \pm 0. 0 0 0
$$

$$
0. 3 8 6 \pm 0. 0 0 0
$$

$$
0. 3 7 2 \pm 0. 0 0 0
$$

$$
0. 3 6 8 \pm 0. 0 0 0
$$

$$
0. 3 6 8 \pm 0. 0 0 0
$$

$$
0. 3 7 2 \pm 0. 0 0 0
$$

$$
0. 3 6 6 \pm 0. 0 0 0
$$

$$
0. 3 6 6 \pm 0. 0 0 0
$$

$$
0. 8 5 1 \pm 0. 0 1 4
$$

$$
0. 8 6 1 \pm 0. 0 1 3
$$

$$
0. 8 6 6 \pm 0. 0 1 2
$$

$$
5. 6 5 9 \pm 0. 5 4 3
$$

$$
0. 8 7 5 \pm 0. 0 1 2
$$

$$
5. 1 4 3 \pm 0. 5 7 9
$$

$$
2. 6 1 5 \pm 0. 1 3 7
$$

$$
0. 8 7 8 \pm 0. 0 1 0
$$

$$
0. 8 8 4 \pm 0. 0 0 5
$$

$$
2. 4 4 5 \pm 0. 0 7 3
$$

$$
6. 0 7 1 \pm 0. 5 3 7
$$

$$
5. 5 5 8 \pm 0. 4 0 4
$$

$$
0. 8 7 7 \pm 0. 0 0 9
$$

$$
0. 8 8 5 \pm 0. 0 0 7
$$

$$
2. 5 7 7 \pm 0. 1 6 9
$$

$$
2. 3 2 6 \pm 0. 0 5 8
$$

$$
0. 8 8 3 \pm 0. 0 1 2
$$

$$
0. 8 9 0 \pm 0. 0 0 5
$$

$$
3. 6 3 2 \pm 0. 1 0 1
$$

$$
3. 5 5 1 \pm 0. 0 9 0
$$

$$
0. 8 6 8 \pm 0. 0 1 7
$$

$$
0. 8 7 7 \pm 0. 0 1 6
$$

$$
4. 2 9 6 \pm 0. 0 6 4
$$

$$
4. 2 5 5 \pm 0. 0 4 9
$$

$$
0. 8 7 0 \pm 0. 0 1 3
$$

$$
0. 8 7 3 \pm 0. 0 1 3
$$

$$
4. 2 3 2 \pm 0. 3 3 7
$$

$$
4. 1 8 8 \pm 0. 3 1 1
$$

$$
0. 8 7 7 \pm 0. 0 0 7
$$

$$
0. 8 8 0 \pm 0. 0 0 3
$$

$$
6. 2 0 0 \pm 0. 3 9 6
$$

$$
5. 8 0 4 \pm 0. 2 4 8
$$

$$
0. 8 7 9 \pm 0. 0 1 1
$$

$$
0. 8 8 1 \pm 0. 0 1 2
$$

$$
4. 4 7 9 \pm 0. 0 5 1
$$

$$
4. 4 0 0 \pm 0. 0 3 9
$$

$$
0. 8 7 0 \pm 0. 0 1 6
$$

$$
0. 8 7 0 \pm 0. 0 1 6
$$

$$
5. 2 4 9 \pm 0. 1 8 3
$$

$$
0. 8 7 4 \pm 0. 0 0 7
$$

$$
5. 2 4 9 \pm 0. 1 9 7
$$

$$
0. 8 7 4 \pm 0. 0 0 7
$$

$$
4. 3 8 2 \pm 0. 1 9 5
$$

$$
4. 3 8 2 \pm 0. 2 1 0
$$

<table><tr><td colspan="3">rl ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.671 ± 0.013</td><td>0.677 ± 0.013</td></tr><tr><td>MLP-PLR</td><td>0.744 ± 0.019</td><td>0.767 ± 0.027</td></tr><tr><td>TabR-S</td><td>0.874 ± 0.008</td><td>0.880 ± 0.006</td></tr><tr><td>TabR</td><td>0.884 ± 0.016</td><td>0.891 ± 0.013</td></tr><tr><td>CatBoost</td><td>0.790 ± 0.007</td><td>0.793 ± 0.005</td></tr><tr><td>XGBoost</td><td>0.797 ± 0.012</td><td>0.799 ± 0.012</td></tr><tr><td>LightGBM</td><td>0.781 ± 0.010</td><td>0.787 ± 0.007</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.871 ± 0.008</td><td>0.876 ± 0.007</td></tr><tr><td>CatBoost</td><td>0.785 ± 0.010</td><td>0.790 ± 0.004</td></tr><tr><td>XGBoost</td><td>0.775 ± 0.003</td><td>0.775 ± 0.003</td></tr><tr><td>LightGBM</td><td>0.778 ± 0.003</td><td>0.778 ± 0.003</td></tr></table>

<table><tr><td colspan="3">road-safety ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.786 ± 0.001</td><td>0.789 ± 0.000</td></tr><tr><td>MLP-PLR</td><td>0.785 ± 0.002</td><td>0.789 ± 0.001</td></tr><tr><td>TabR-S</td><td>0.840 ± 0.001</td><td>0.844 ± 0.000</td></tr><tr><td>TabR</td><td>0.837 ± 0.001</td><td>0.843 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.801 ± 0.001</td><td>0.802 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.810 ± 0.002</td><td>0.813 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.798 ± 0.001</td><td>0.800 ± 0.000</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.791 ± 0.003</td><td>0.796 ± 0.003</td></tr><tr><td>CatBoost</td><td>0.792 ± 0.001</td><td>0.793 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.796 ± 0.000</td><td>0.796 ± 0.000</td></tr><tr><td>LightGBM</td><td>0.803 ± 0.000</td><td>0.803 ± 0.000</td></tr></table>

sulfur ↓

<table><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.022 ± 0.002</td><td>0.021 ± 0.002</td></tr><tr><td>MLP-PLR</td><td>0.020 ± 0.002</td><td>0.019 ± 0.003</td></tr><tr><td>TabR-S</td><td>0.022 ± 0.002</td><td>0.021 ± 0.002</td></tr><tr><td>TabR</td><td>0.022 ± 0.003</td><td>0.020 ± 0.003</td></tr><tr><td>CatBoost</td><td>0.019 ± 0.002</td><td>0.019 ± 0.002</td></tr><tr><td>XGBoost</td><td>0.020 ± 0.002</td><td>0.020 ± 0.002</td></tr><tr><td>LightGBM</td><td>0.020 ± 0.002</td><td>0.020 ± 0.002</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.021 ± 0.003</td><td>0.021 ± 0.002</td></tr><tr><td>CatBoost</td><td>0.019 ± 0.002</td><td>0.019 ± 0.003</td></tr><tr><td>XGBoost</td><td>0.022 ± 0.002</td><td>0.022 ± 0.002</td></tr><tr><td>LightGBM</td><td>0.021 ± 0.001</td><td>0.021 ± 0.001</td></tr></table>

$$
0. 1 3 8 \pm 0. 0 1 2
$$

$$
0. 1 5 8 \pm 0. 0 6 7
$$

$$
0. 3 9 8 \pm 0. 3 5 2
$$

$$
0. 1 3 2 \pm 0. 0 1 0
$$

$$
0. 2 2 7 \pm 0. 2 6 4
$$

$$
0. 1 4 4 \pm 0. 0 6 0
$$

$$
0. 3 8 7 \pm 0. 3 7 5
$$

$$
0. 0 5 5 \pm 0. 0 0 6
$$

$$
0. 1 7 6 \pm 0. 0 7 1
$$

$$
0. 2 0 2 \pm 0. 1 4 7
$$

$$
0. 0 6 2 \pm 0. 0 1 6
$$

$$
0. 0 4 7 \pm 0. 0 0 6
$$

$$
0. 1 5 4 \pm 0. 0 5 4
$$

$$
0. 0 6 2 \pm 0. 0 1 7
$$

$$
0. 3 2 7 \pm 0. 2 5 4
$$

$$
0. 0 6 4 \pm 0. 0 0 5
$$

$$
0. 3 1 0 \pm 0. 2 5 7
$$

$$
0. 0 6 6 \pm 0. 0 0 9
$$

$$
0. 0 6 1 \pm 0. 0 1 3
$$

$$
0. 0 5 8 \pm 0. 0 0 5
$$

$$
0. 0 6 6 \pm 0. 0 1 0
$$

$$
0. 0 6 1 \pm 0. 0 1 4
$$

<table><tr><td colspan="3">wine quality ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.672 ± 0.015</td><td>0.659 ± 0.016</td></tr><tr><td>MLP-PLR</td><td>0.654 ± 0.018</td><td>0.634 ± 0.018</td></tr><tr><td>TabR-S</td><td>0.632 ± 0.010</td><td>0.620 ± 0.010</td></tr><tr><td>TabR</td><td>0.641 ± 0.011</td><td>0.620 ± 0.007</td></tr><tr><td>CatBoost</td><td>0.609 ± 0.013</td><td>0.606 ± 0.014</td></tr><tr><td>XGBoost</td><td>0.604 ± 0.013</td><td>0.602 ± 0.014</td></tr><tr><td>LightGBM</td><td>0.613 ± 0.014</td><td>0.612 ± 0.014</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.628 ± 0.015</td><td>0.614 ± 0.015</td></tr><tr><td>CatBoost</td><td>0.628 ± 0.012</td><td>0.626 ± 0.012</td></tr><tr><td>XGBoost</td><td>0.648 ± 0.008</td><td>0.648 ± 0.008</td></tr><tr><td>LightGBM</td><td>0.641 ± 0.011</td><td>0.641 ± 0.012</td></tr></table>

superconduct ↓

$$
1 0. 7 2 4 \pm 0. 0 6 2
$$

$$
1 0. 5 6 6 \pm 0. 0 5 8
$$

$$
1 0. 8 8 4 \pm 0. 1 0 7
$$

$$
1 0. 4 5 5 \pm 0. 0 0 5
$$

$$
1 0. 3 8 4 \pm 0. 0 5 6
$$

$$
1 0. 3 3 4 \pm 0. 0 2 8
$$

$$
1 0. 2 4 2 \pm 0. 0 2 2
$$

$$
1 0. 4 8 0 \pm 0. 0 2 8
$$

$$
1 0. 1 6 1 \pm 0. 0 2 0
$$

$$
1 0. 4 7 1 \pm 0. 0 0 0
$$

$$
1 0. 1 3 7 \pm 0. 0 2 3
$$

$$
1 0. 1 6 3 \pm 0. 0 1 2
$$

$$
1 0. 2 1 2 \pm 0. 0 0 6
$$

$$
1 0. 1 4 1 \pm 0. 0 0 2
$$

$$
1 0. 1 5 5 \pm 0. 0 0 5
$$

$$
1 0. 7 3 6 \pm 0. 0 0 0
$$

$$
1 0. 8 1 2 \pm 0. 1 1 0
$$

$$
1 0. 2 6 3 \pm 0. 0 2 8
$$

$$
1 0. 7 3 6 \pm 0. 0 0 0
$$

$$
1 0. 4 2 3 \pm 0. 0 4 6
$$

$$
1 0. 4 7 1 \pm 0. 0 0 0
$$

$$
1 0. 2 2 2 \pm 0. 0 0 6
$$

<table><tr><td colspan="3">wine ↑</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.769 ± 0.015</td><td>0.784 ± 0.010</td></tr><tr><td>MLP-PLR</td><td>0.771 ± 0.016</td><td>0.783 ± 0.014</td></tr><tr><td>TabR-S</td><td>0.794 ± 0.011</td><td>0.805 ± 0.006</td></tr><tr><td>TabR</td><td>0.780 ± 0.015</td><td>0.795 ± 0.012</td></tr><tr><td>CatBoost</td><td>0.799 ± 0.013</td><td>0.806 ± 0.010</td></tr><tr><td>XGBoost</td><td>0.795 ± 0.018</td><td>0.801 ± 0.019</td></tr><tr><td>LightGBM</td><td>0.789 ± 0.016</td><td>0.793 ± 0.011</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.791 ± 0.012</td><td>0.800 ± 0.008</td></tr><tr><td>CatBoost</td><td>0.796 ± 0.010</td><td>0.799 ± 0.010</td></tr><tr><td>XGBoost</td><td>0.796 ± 0.010</td><td>0.796 ± 0.010</td></tr><tr><td>LightGBM</td><td>0.798 ± 0.004</td><td>0.798 ± 0.004</td></tr></table>

<table><tr><td colspan="3">year ↓</td></tr><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td> $8.964 \pm 0.018$ </td><td> $8.901 \pm 0.003$ </td></tr><tr><td>MLP-PLR</td><td> $8.927 \pm 0.013$ </td><td> $8.901 \pm 0.006$ </td></tr><tr><td>TabR-S</td><td> $9.007 \pm 0.015$ </td><td> $8.913 \pm 0.009$ </td></tr><tr><td>TabR</td><td> $8.972 \pm 0.010$ </td><td> $8.917 \pm 0.003$ </td></tr><tr><td>CatBoost</td><td> $9.037 \pm 0.007$ </td><td> $9.005 \pm 0.003$ </td></tr><tr><td>XGBoost</td><td> $9.031 \pm 0.003$ </td><td> $9.024 \pm 0.001$ </td></tr><tr><td>LightGBM</td><td> $9.020 \pm 0.002$ </td><td> $9.013 \pm 0.001$ </td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td> $9.067 \pm 0.022$ </td><td> $8.893 \pm 0.008$ </td></tr><tr><td>CatBoost</td><td> $9.073 \pm 0.008$ </td><td> $9.046 \pm 0.001$ </td></tr><tr><td>XGBoost</td><td> $9.376 \pm 0.000$ </td><td> $9.376 \pm 0.000$ </td></tr><tr><td>LightGBM</td><td> $9.214 \pm 0.000$ </td><td> $9.214 \pm 0.000$ </td></tr></table>

yprop 4 1 ↓

<table><tr><td>Method</td><td>Single model</td><td>Ensemble</td></tr><tr><td colspan="3">Tuned Hyperparameters</td></tr><tr><td>MLP</td><td>0.027 ± 0.001</td><td>0.027 ± 0.001</td></tr><tr><td>MLP-PLR</td><td>0.027 ± 0.001</td><td>0.027 ± 0.001</td></tr><tr><td>TabR-S</td><td>0.027 ± 0.000</td><td>0.027 ± 0.001</td></tr><tr><td>TabR</td><td>0.027 ± 0.000</td><td>0.027 ± 0.000</td></tr><tr><td>CatBoost</td><td>0.027 ± 0.000</td><td>0.027 ± 0.001</td></tr><tr><td>XGBoost</td><td>0.027 ± 0.001</td><td>0.027 ± 0.001</td></tr><tr><td>LightGBM</td><td>0.027 ± 0.000</td><td>0.027 ± 0.000</td></tr><tr><td colspan="3">Default hyperparameters</td></tr><tr><td>TabR-S</td><td>0.027 ± 0.001</td><td>0.027 ± 0.001</td></tr><tr><td>CatBoost</td><td>0.027 ± 0.000</td><td>0.027 ± 0.000</td></tr><tr><td>XGBoost</td><td>0.027 ± 0.001</td><td>0.027 ± 0.001</td></tr><tr><td>LightGBM</td><td>0.027 ± 0.000</td><td>0.027 ± 0.000</td></tr></table>