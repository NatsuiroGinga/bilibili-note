---
title: "2021-Gorishniy-Revisiting-Deep-Learning-Tabular-Data"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2021-Gorishniy-Revisiting-Deep-Learning-Tabular-Data.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Revisiting Deep Learning Models for Tabular Data

Yury Gorishniy∗†‡ Ivan Rubachev†♣ Valentin Khrulkov† Artem Babenko†♣

Yandex Moscow Institute of Physics and Technology National Research University Higher School of Economics

## Abstract

The existing literature on deep learning for tabular data proposes a wide range of novel architectures and reports competitive results on various datasets. However, the proposed models are usually not properly compared to each other and existing works often use different benchmarks and experiment protocols. As a result, it is unclear for both researchers and practitioners what models perform best. Additionally, the field still lacks effective baselines, that is, the easy-to-use models that provide competitive performance across different problems.

In this work, we perform an overview of the main families of DL architectures for tabular data and raise the bar of baselines in tabular DL by identifying two simple and powerful deep architectures. The first one is a ResNetlike architecture which turns out to be a strong baseline that is often missing in prior works. The second model is our simple adaptation of the Transformer architecture for tabular data, which outperforms other solutions on most tasks. Both models are compared to many existing architectures on a diverse set of tasks under the same training and tuning protocols. We also compare the best DL models with Gradient Boosted Decision Trees and conclude that there is still no universally superior solution. The source code is available at https: //github.com/yandex-research/tabular-dl-revisiting-models.

## 1 Introduction

Due to the tremendous success of deep learning on such data domains as images, audio and texts (Goodfellow et al., 2016), there has been a lot of research interest to extend this success to problems with data stored in tabular format. In these problems, data points are represented as vectors of heterogeneous features, which is typical for industrial applications and ML competitions, where neural networks have a strong non-deep competitor in the form of GBDT (Chen and Guestrin, 2016; Ke et al., 2017; Prokhorenkova et al., 2018). Along with potentially higher performance, using deep learning for tabular data is appealing as it would allow constructing multi-modal pipelines for problems, where only one part of the input is tabular, and other parts include images, audio and other DL-friendly data. Such pipelines can then be trained end-to-end by gradient optimization for all modalities. For these reasons, a large number of DL solutions were recently proposed, and new models continue to emerge (Arik and Pfister, 2020; Badirli et al., 2020; Hazimeh et al., 2020; Huang et al., 2020a; Klambauer et al., 2017; Popov et al., 2020; Song et al., 2019; Wang et al., 2017, 2020a).

Unfortunately, due to the lack of established benchmarks (such as ImageNet (Deng et al., 2009) for computer vision or GLUE (Wang et al., 2019a) for NLP), existing papers use different datasets for evaluation and proposed DL models are often not adequately compared to each other. Therefore, from the current literature, it is unclear what DL model generally performs better than others and whether GBDT is surpassed by DL models. Additionally, despite the large number of novel architectures, the field still lacks simple and reliable solutions that allow achieving competitive performance with moderate effort and provide stable performance across many tasks. In that regard, Multilayer Perceptron (MLP) remains the main simple baseline for the field, however, it does not always represent a significant challenge for other competitors.

The described problems impede the research process and make the observations from the papers not conclusive enough. Therefore, we believe it is timely to review the recent developments from the field and raise the bar of baselines in tabular DL. We start with a hypothesis that well-studied DL architecture blocks may be underexplored in the context of tabular data and may be used to design better baselines. Thus, we take inspiration from well-known battle-tested architectures from other fields and obtain two simple models for tabular data. The first one is a ResNet-like architecture (He et al., 2015b) and the second one is FT-Transformer — our simple adaptation of the Transformer architecture (Vaswani et al., 2017) for tabular data. Then, we compare these models with many existing solutions on a diverse set of tasks under the same protocols of training and hyperparameters tuning. First, we reveal that none of the considered DL models can consistently outperform the ResNet-like model. Given its simplicity, it can serve as a strong baseline for future work. Second, FT-Transformer demonstrates the best performance on most tasks and becomes a new powerful solution for the field. Interestingly, FT-Transformer turns out to be a more universal architecture for tabular data: it performs well on a wider range of tasks than the more “conventional” ResNet and other DL models. Finally, we compare the best DL models to GBDT and conclude that there is still no universally superior solution.

We summarize the contributions of our paper as follows:

1. We thoroughly evaluate the main models for tabular DL on a diverse set of tasks to investigate their relative performance.

2. We demonstrate that a simple ResNet-like architecture is an effective baseline for tabular DL, which was overlooked by existing literature. Given its simplicity, we recommend this baseline for comparison in future tabular DL works.

3. We introduce FT-Transformer — a simple adaptation of the Transformer architecture for tabular data that becomes a new powerful solution for the field. We observe that it is a more universal architecture: it performs well on a wider range of tasks than other DL models.

4. We reveal that there is still no universally superior solution among GBDT and deep models.

## 2 Related work

The “shallow” state-of-the-art for problems with tabular data is currently ensembles of decision trees, such as GBDT (Gradient Boosting Decision Tree) (Friedman, 2001), which are typically the top-choice in various ML competitions. At the moment, there are several established GBDT libraries, such as XGBoost (Chen and Guestrin, 2016), LightGBM (Ke et al., 2017), CatBoost (Prokhorenkova et al., 2018), which are widely used by both ML researchers and practitioners. While these implementations vary in detail, on most of the tasks, their performances do not differ much (Prokhorenkova et al., 2018).

During several recent years, a large number of deep learning models for tabular data have been developed (Arik and Pfister, 2020; Badirli et al., 2020; Hazimeh et al., 2020; Huang et al., 2020a; Klambauer et al., 2017; Popov et al., 2020; Song et al., 2019; Wang et al., 2017). Most of these models can be roughly categorized into three groups, which we briefly describe below.

Differentiable trees. The first group of models is motivated by the strong performance of decision tree ensembles for tabular data. Since decision trees are not differentiable and do not allow gradient optimization, they cannot be used as a component for pipelines trained in the end-to-end fashion. To address this issue, several works (Hazimeh et al., 2020; Kontschieder et al., 2015; Popov et al., 2020; Yang et al., 2018) propose to “smooth” decision functions in the internal tree nodes to make the overall tree function and tree routing differentiable. While the methods of this family can outperform GBDT on some tasks (Popov et al., 2020), in our experiments, they do not consistently outperform ResNet.

Attention-based models. Due to the ubiquitous success of attention-based architectures for different domains (Dosovitskiy et al., 2021; Vaswani et al., 2017), several authors propose to employ attentionlike modules for tabular DL as well (Arik and Pfister, 2020; Huang et al., 2020a; Song et al., 2019).

In our experiments, we show that the properly tuned ResNet outperforms the existing attention-based models. Nevertheless, we identify an effective way to apply the Transformer architecture (Vaswani et al., 2017) to tabular data: the resulting architecture outperforms ResNet on most of the tasks.

Explicit modeling of multiplicative interactions. In the literature on recommender systems and click-through-rate prediction, several works criticize MLP since it is unsuitable for modeling multiplicative interactions between features (Beutel et al., 2018; Qin et al., 2021; Wang et al., 2017). Inspired by this motivation, some works (Beutel et al., 2018; Wang et al., 2017, 2020a) have proposed different ways to incorporate feature products into MLP. In our experiments, however, we do not find such methods to be superior to properly tuned baselines.

The literature also proposes some other architectural designs (Badirli et al., 2020; Klambauer et al., 2017) that cannot be explicitly assigned to any of the groups above. Overall, the community has developed a variety of models that are evaluated on different benchmarks and are rarely compared to each other. Our work aims to establish a fair comparison of them and identify the solutions that consistently provide high performance.

## 3 Models for tabular data problems

In this section, we describe the main deep architectures that we highlight in our work, as well as the existing solutions included in the comparison. Since we argue that the field needs strong easy-to-use baselines, we try to reuse well-established DL building blocks as much as possible when designing ResNet (section 3.2) and FT-Transformer (section 3.3). We hope this approach will result in conceptually familiar models that require less effort to achieve good performance. Additional discussion and technical details for all the models are provided in supplementary.

Notation. In this work, we consider supervised learning problems. $D { = } \{ ( x _ { i } , ~ y _ { i } ) \} _ { i { = } 1 } ^ { n }$ denotes a dataset, where $x _ { i } = ( x _ { i } ^ { ( n u m ) } , x _ { i } ^ { ( c a t ) } ) \in \mathbb { X }$ represents numerical $x _ { i j } ^ { ( n u m ) }$ and categorical $x _ { i j } ^ { ( c a t ) }$ features of an object and $y _ { i } \in \mathbb { Y }$ denotes the corresponding object label. The total number of features is denoted as k. The dataset is split into three disjoint subsets: $D = D _ { t r a i n } \cup D _ { v a l } \cup D _ { t e s t }$ , where $D _ { t r a i n }$ is used for training, $\bar { D _ { v a l } }$ is used for early stopping and hyperparameter tuning, and $D _ { t e s t }$ is used for the final evaluation. We consider three types of tasks: binary classification $\Breve { \mathbb { Y } } = \{ 0 , \ 1 \}$ multiclass classification $\mathbb { Y } = \{ 1 , \ . . . , C \}$ and regression $\mathbb { Y } = \mathbb { R }$

## 3.1 MLP

We formalize the $\mathrm { \bf { \tilde { \theta } M L P } } ^ { \mathrm { { s } } }$ architecture in Equation 1.

$$
\begin{array}{c} \operatorname{MLP} (x) = \text { Linear } \left(\operatorname{MLPBlock} \left(\dots (\operatorname{MLPBlock} (x))\right)\right) \\ \operatorname{MLPBlock} (x) = \text { Dropout } (\operatorname{ReLU} (\operatorname{Linear} (x))) \end{array}\tag{1}
$$

## 3.2 ResNet

We are aware of one attempt to design a ResNet-like baseline (Klambauer et al., 2017) where the reported results were not competitive. However, given ResNet’s success story in computer vision (He et al., 2015b) and its recent achievements on NLP tasks (Sun and Iyyer, 2021), we give it a second try and construct a simple variation of ResNet as described in Equation 2. The main building block is simplified compared to the original architecture, and there is an almost clear path from the input to output which we find to be beneficial for the optimization. Overall, we expect this architecture to outperform MLP on tasks where deeper representations can be helpful.

$$
\begin{array}{c} \operatorname{ResNet} (x) = \text {Prediction} (\operatorname{ResNetBlock} (\dots (\operatorname{ResNetBlock} (\operatorname{Linear} (x)))) \\ \operatorname{ResNetBlock} (x) = x + \text {Dropout} (\operatorname{Linear} (\operatorname{Dropout} (\operatorname{ReLU} (\operatorname{Linear} (\operatorname{BatchNorm} (x)))))) \\ \operatorname{Prediction} (x) = \text {Linear} (\operatorname{ReLU} (\operatorname{BatchNorm} (x))) \end{array}\tag{2}
$$

## 3.3 FT-Transformer

In this section, we introduce FT-Transformer (Feature Tokenizer + Transformer) — a simple adaptation of the Transformer architecture (Vaswani et al., 2017) for the tabular domain. Figure 1 demonstrates the main parts of FT-Transformer. In a nutshell, our model transforms all features (categorical and numerical) to embeddings and applies a stack of Transformer layers to the embeddings. Thus, every Transformer layer operates on thefeature level of one object. We compare FT-Transformer to conceptually similar AutoInt in section 5.2.

(b)  
![](images/d8e7adb330b807ef1dc388b65522ce36547974f89349cc2aa197a5c7e75c6e9a.jpg)  
Figure 1: The FT-Transformer architecture. Firstly, Feature Tokenizer transforms features to embeddings. The embeddings are then processed by the Transformer module and the final representation of the [CLS] token is used for prediction.

![](images/3cabccfe92c72640aa96ae5c7cc70dc2daa5958a60d51e2b2be35971914e9edd.jpg)

![](images/20bd936669c7d55a5485ffbdde03e4cc6a403bed19b5d203f1466f466750cc01.jpg)  
Figure 2: (a) Feature Tokenizer; in the example, there are three numerical and two categorical features; (b) One Transformer layer.

Feature Tokenizer. The Feature Tokenizer module (see Figure 2) transforms the input features x to embeddings $T \in \mathbb { R } ^ { k \times d }$ . The embedding for a given feature $x _ { j }$ is computed as follows:

$$
T _ {j} = b _ {j} + f _ {j} (x _ {j}) \in \mathbb {R} ^ {d} \qquad f _ {j}: \mathbb {X} _ {j} \to \mathbb {R} ^ {d}.
$$

where $b _ { j }$ is the j-th feature bias, $f _ { j } ^ { ( n u m ) }$ is implemented as the element-wise multiplication with the vector $W _ { i } ^ { ( n u m ) } \in \mathbb { R } ^ { d }$ and $f _ { j } ^ { ( c a t ) }$ is implemented as the lookup table $W _ { j } ^ { ( c a t ) } \in \mathbb { R } ^ { S _ { j } \times d }$ for categorical features. Overall:

$$
\begin{array}{l l} T _ {j} ^ {(n u m)} = b _ {j} ^ {(n u m)} + x _ {j} ^ {(n u m)} \cdot W _ {j} ^ {(n u m)} & \in \mathbb {R} ^ {d}, \\ T _ {j} ^ {(c a t)} = b _ {j} ^ {(c a t)} + e _ {j} ^ {T} W _ {j} ^ {(c a t)} & \in \mathbb {R} ^ {d}, \\ T = \mathsf {s t a c k} \left[ T _ {1} ^ {(n u m)}, \ldots , T _ {k ^ {(n u m)}} ^ {(n u m)}, T _ {1} ^ {(c a t)}, \ldots , T _ {k ^ {(c a t)}} ^ {(c a t)} \right] \in \mathbb {R} ^ {k \times d}. \end{array}
$$

where $e _ { j } ^ { T }$ is a one-hot vector for the corresponding categorical feature.

Transformer. At this stage, the embedding of the [CLS] token (or “classification token”, or “output token”, see Devlin et al. (2019)) is appended to $T$ and L Transformer layers $F _ { 1 } , \ldots , F _ { L }$ are applied:

$$
T _ {0} = \mathsf {s t a c k} \left[ [ \mathrm{CLS} ], T \right] \quad T _ {i} = F _ {i} (T _ {i - 1}).
$$

We use the PreNorm variant for easier optimization (Wang et al., 2019b), see Figure 2. In the PreNorm setting, we also found it to be necessary to remove the first normalization from the first Transformer layer to achieve good performance. See the original paper (Vaswani et al., 2017) for the background on Multi-Head Self-Attention (MHSA) and the Feed Forward module. See supplementary for details such as activations, placement of normalizations and dropout modules (Srivastava et al., 2014).

Prediction. The final representation of the [CLS] token is used for prediction:

$$
\hat {y} = \text { Linear } (\text { ReLU } (\text { LayerNorm } (T _ {L} ^ {[ \text { CLS } ]}))).
$$

Limitations. FT-Transformer requires more resources (both hardware and time) for training than simple models such as ResNet and may not be easily scaled to datasets when the number of features is “too large” (it is determined by the available hardware and time budget). Consequently, widespread usage of FT-Transformer for solving tabular data problems can lead to greater CO2 emissions produced by ML pipelines, since tabular data problems are ubiquitous. The main cause of the described problem lies in the quadratic complexity of the vanilla MHSA with respect to the number of features. However, the issue can be alleviated by using efficient approximations of MHSA (Tay et al., 2020). Additionally, it is still possible to distill FT-Transformer into simpler architectures for better inference performance. We report training times and the used hardware in supplementary.

## 3.4 Other models

In this section, we list the existing models designed specifically for tabular data that we include in the comparison.

• SNN (Klambauer et al., 2017). An MLP-like architecture with the SELU activation that enables training deeper models.

• NODE (Popov et al., 2020). A differentiable ensemble of oblivious decision trees.

• TabNet (Arik and Pfister, 2020). A recurrent architecture that alternates dynamical reweigh ing of features and conventional feed-forward modules.

• GrowNet (Badirli et al., 2020). Gradient boosted weak MLPs. The official implementation supports only classification and regression problems.

• DCN V2 (Wang et al., 2020a). Consists of an MLP-like module and the feature crossing module (a combination of linear layers and multiplications).

• AutoInt (Song et al., 2019). Transforms features to embeddings and applies a series of attention-based transformations to the embeddings.

• XGBoost (Chen and Guestrin, 2016). One of the most popular GBDT implementations.

• CatBoost (Prokhorenkova et al., 2018). GBDT implementation that uses oblivious decision trees (Lou and Obukhov, 2017) as weak learners.

## 4 Experiments

In this section, we compare DL models to each other as well as to GBDT. Note that in the main text, we report only the key results. In supplementary, we provide: (1) the results for all models on all datasets; (2) information on hardware; (3) training times for ResNet and FT-Transformer.

## 4.1 Scope of the comparison

In our work, we focus on the relative performance of different architectures and do not employ various model-agnostic DL practices, such as pretraining, additional loss functions, data augmentation, distillation, learning rate warmup, learning rate decay and many others. While these practices can potentially improve the performance, our goal is to evaluate the impact of inductive biases imposed by the different model architectures.

## 4.2 Datasets

We use a diverse set of eleven public datasets (see supplementary for the detailed description). For each dataset, there is exactly one train-validation-test split, so all algorithms use the same splits. The datasets include: California Housing (CA, real estate data, Kelley Pace and Barry (1997)), Adult (AD, income estimation, Kohavi (1996)), Helena (HE, anonymized dataset, Guyon et al. (2019)),

Jannis (JA, anonymized dataset, Guyon et al. (2019)), Higgs (HI, simulated physical particles, Baldi et al. (2014); we use the version with 98K samples available at the OpenML repository (Vanschoren et al., 2014)), ALOI (AL, images, Geusebroek et al. (2005)), Epsilon (EP, simulated physics experiments), Year (YE, audio features, Bertin-Mahieux et al. (2011)), Covertype (CO, forest characteristics, Blackard and Dean. (2000)), Yahoo (YA, search queries, Chapelle and Chang (2011)), Microsoft (MI, search queries, Qin and Liu (2013)). We follow the pointwise approach to learning-to-rank and treat ranking problems (Microsoft, Yahoo) as regression problems. The dataset properties are summarized in Table 1.

Table 1: Dataset properties. Notation: “RMSE” \~ root-mean-square error, “Acc.” \~ accuracy.

<table><tr><td></td><td>CA</td><td>AD</td><td>HE</td><td>JA</td><td>HI</td><td>AL</td><td>EP</td><td>YE</td><td>CO</td><td>YA</td><td>MI</td></tr><tr><td>#objects</td><td>20640</td><td>48842</td><td>65196</td><td>83733</td><td>98050</td><td>108000</td><td>500000</td><td>515345</td><td>581012</td><td>709877</td><td>1200192</td></tr><tr><td>#num. features</td><td>8</td><td>6</td><td>27</td><td>54</td><td>28</td><td>128</td><td>2000</td><td>90</td><td>54</td><td>699</td><td>136</td></tr><tr><td>#cat. features</td><td>0</td><td>8</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>metric</td><td>RMSE</td><td>Acc.</td><td>Acc.</td><td>Acc.</td><td>Acc.</td><td>Acc.</td><td>Acc.</td><td>RMSE</td><td>Acc.</td><td>RMSE</td><td>RMSE</td></tr><tr><td>#classes</td><td>-</td><td>2</td><td>100</td><td>4</td><td>2</td><td>1000</td><td>2</td><td>-</td><td>7</td><td>-</td><td>-</td></tr></table>

## 4.3 Implementation details

Data preprocessing. Data preprocessing is known to be vital for DL models. For each dataset, the same preprocessing was used for all deep models for a fair comparison. By default, we used the quantile transformation from the Scikit-learn library (Pedregosa et al., 2011). We apply standardization (mean subtraction and scaling) to Helena and ALOI. The latter one represents image data, and standardization is a common practice in computer vision. On the Epsilon dataset, we observed preprocessing to be detrimental to deep models’ performance, so we use the raw features on this dataset. We apply standardization to regression targets for all algorithms.

Tuning. For every dataset, we carefully tune each model’s hyperparameters. The best hyperparameters are the ones that perform best on the validation set, so the test set is never used for tuning. For most algorithms, we use the Optuna library (Akiba et al., 2019) to run Bayesian optimization (the Tree-Structured Parzen Estimator algorithm), which is reported to be superior to random search (Turner et al., 2021). For the rest, we iterate over predefined sets of configurations recommended by corresponding papers. We provide parameter spaces and grids in supplementary. We set the budget for Optuna-based tuning in terms of iterations and provide additional analysis on setting the budget in terms of time in supplementary.

Evaluation. For each tuned configuration, we run 15 experiments with different random seeds and report the performance on the test set. For some algorithms, we also report the performance of default configurations without hyperparameter tuning.

Ensembles. For each model, on each dataset, we obtain three ensembles by splitting the 15 single models into three disjoint groups of equal size and averaging predictions of single models within each group.

Neural networks. We minimize cross-entropy for classification problems and mean squared error for regression problems. For TabNet and GrowNet, we follow the original implementations and use the Adam optimizer (Kingma and Ba, 2017). For all other algorithms, we use the AdamW optimizer (Loshchilov and Hutter, 2019). We do not apply learning rate schedules. For each dataset, we use a predefined batch size for all algorithms unless special instructions on batch sizes are given in the corresponding papers (see supplementary). We continue training until there are patience + 1 consecutive epochs without improvements on the validation set; we set patience = 16 for all algorithms.

Categorical features. For XGBoost, we use one-hot encoding. For CatBoost, we employ the built-in support for categorical features. For Neural Networks, we use embeddings of the same dimensionality for all categorical features.

Table 2: Results for DL models. The metric values averaged over 15 random seeds are reported. See supplementary for standard deviations. For each dataset, top results are in bold. “Top” means “the gap between this result and the result with the best score is not statistically significant”. For each dataset, ranks are calculated by sorting the reported scores; the “rank” column reports the average rank across all datasets. Notation: FT-T \~ FT-Transformer, ↓ \~ RMSE, ↑ \~ accuracy

<table><tr><td></td><td>CA ↓</td><td>AD ↑</td><td>HE ↑</td><td>JA ↑</td><td>HI ↑</td><td>AL ↑</td><td>EP ↑</td><td>YE ↓</td><td>CO ↑</td><td>YA ↓</td><td>MI ↓</td><td>rank (std)</td></tr><tr><td>TabNet</td><td>0.510</td><td>0.850</td><td>0.378</td><td>0.723</td><td>0.719</td><td>0.954</td><td>0.8896</td><td>8.909</td><td>0.957</td><td>0.823</td><td>0.751</td><td>7.5 (2.0)</td></tr><tr><td>SNN</td><td>0.493</td><td>0.854</td><td>0.373</td><td>0.719</td><td>0.722</td><td>0.954</td><td>0.8975</td><td>8.895</td><td>0.961</td><td>0.761</td><td>0.751</td><td>6.4 (1.4)</td></tr><tr><td>AutoInt</td><td>0.474</td><td>0.859</td><td>0.372</td><td>0.721</td><td>0.725</td><td>0.945</td><td>0.8949</td><td>8.882</td><td>0.934</td><td>0.768</td><td>0.750</td><td>5.7 (2.3)</td></tr><tr><td>GrowNet</td><td>0.487</td><td>0.857</td><td>-</td><td>-</td><td>0.722</td><td>-</td><td>0.8970</td><td>8.827</td><td>-</td><td>0.765</td><td>0.751</td><td>5.7 (2.2)</td></tr><tr><td>MLP</td><td>0.499</td><td>0.852</td><td>0.383</td><td>0.719</td><td>0.723</td><td>0.954</td><td>0.8977</td><td>8.853</td><td>0.962</td><td>0.757</td><td>0.747</td><td>4.8 (1.9)</td></tr><tr><td>DCN2</td><td>0.484</td><td>0.853</td><td>0.385</td><td>0.716</td><td>0.723</td><td>0.955</td><td>0.8977</td><td>8.890</td><td>0.965</td><td>0.757</td><td>0.749</td><td>4.7 (2.0)</td></tr><tr><td>NODE</td><td>0.464</td><td>0.858</td><td>0.359</td><td>0.727</td><td>0.726</td><td>0.918</td><td>0.8958</td><td>8.784</td><td>0.958</td><td>0.753</td><td>0.745</td><td>3.9 (2.8)</td></tr><tr><td>ResNet</td><td>0.486</td><td>0.854</td><td>0.396</td><td>0.728</td><td>0.727</td><td>0.963</td><td>0.8969</td><td>8.846</td><td>0.964</td><td>0.757</td><td>0.748</td><td>3.3 (1.8)</td></tr><tr><td>FT-T</td><td>0.459</td><td>0.859</td><td>0.391</td><td>0.732</td><td>0.729</td><td>0.960</td><td>0.8982</td><td>8.855</td><td>0.970</td><td>0.756</td><td>0.746</td><td>1.8 (1.2)</td></tr></table>

## 4.4 Comparing DL models

Table 2 reports the results for deep architectures.

The main takeaways:

• MLP is still a good sanity check

• ResNet turns out to be an effective baseline that none of the competitors can consistently outperform.

• FT-Transformer performs best on most tasks and becomes a new powerful solution for the field.

• Tuning makes simple models such as MLP and ResNet competitive, so we recommend tuning baselines when possible. Luckily, today, it is more approachable with libraries such as Optuna (Akiba et al., 2019).

Among other models, NODE (Popov et al., 2020) is the only one that demonstrates high performance on several tasks. However, it is still inferior to ResNet on six datasets (Helena, Jannis, Higgs, ALOI, Epsilon, Covertype), while being a more complex solution. Moreover, it is not a truly “single” model; in fact, it often contains significantly more parameters than ResNet and FT-Transformer and has an ensemble-like structure. We illustrate that by comparing ensembles in Table 3. The results indicate that FT-Transformer and ResNet benefit more from ensembling; in this regime, FT-Transformer outperforms NODE and the gap between ResNet and NODE is significantly reduced. Nevertheless, NODE remains a prominent solution among tree-based approaches.

Table 3: Results for ensembles of DL models with the highest ranks (see Table 2). For each model-dataset pair, the metric value averaged over three ensembles is reported. See supplementary for standard deviations. Depending on the dataset, the highest accuracy or the lowest RMSE is in bold. Due to the limited precision, some different values are represented with the same figures. Notation: ↓ \~ RMSE, ↑ \~ accuracy.

<table><tr><td></td><td>CA ↓</td><td>AD ↑</td><td>HE ↑</td><td>JA ↑</td><td>HI ↑</td><td>AL ↑</td><td>EP ↑</td><td>YE ↓</td><td>CO ↑</td><td>YA ↓</td><td>MI ↓</td></tr><tr><td>NODE</td><td>0.461</td><td>0.860</td><td>0.361</td><td>0.730</td><td>0.727</td><td>0.921</td><td>0.8970</td><td>8.716</td><td>0.965</td><td>0.750</td><td>0.744</td></tr><tr><td>ResNet</td><td>0.478</td><td>0.857</td><td>0.398</td><td>0.734</td><td>0.731</td><td>0.966</td><td>0.8976</td><td>8.770</td><td>0.967</td><td>0.751</td><td>0.745</td></tr><tr><td>FT-Transformer</td><td>0.448</td><td>0.860</td><td>0.398</td><td>0.739</td><td>0.731</td><td>0.967</td><td>0.8984</td><td>8.751</td><td>0.973</td><td>0.747</td><td>0.743</td></tr></table>

## 4.5 Comparing DL models and GBDT

In this section, our goal is to check whether DL models are conceptually ready to outperform GBDT. To this end, we compare the best possible metric values that one can achieve using GBDT or DL models, without taking speed and hardware requirements into account (undoubtedly, GBDT is a more lightweight solution). We accomplish that by comparing ensembles instead of single models since

GBDT is essentially an ensembling technique and we expect that deep architectures will benefit more from ensembling (Fort et al., 2020). We report the results in Table 4.

Table 4: Results for ensembles of GBDT and the main DL models. For each model-dataset pair, the metric value averaged over three ensembles is reported. See supplementary for standard deviations. Notation follows Table 3.

<table><tr><td></td><td>CA ↓</td><td>AD ↑</td><td>HE ↑</td><td>JA ↑</td><td>HI ↑</td><td>AL ↑</td><td>EP ↑</td><td>YE ↓</td><td>CO ↑</td><td>YA ↓</td><td>MI ↓</td></tr><tr><td colspan="12">Default hyperparameters</td></tr><tr><td>XGBoost</td><td>0.462</td><td>0.874</td><td>0.348</td><td>0.711</td><td>0.717</td><td>0.924</td><td>0.8799</td><td>9.192</td><td>0.964</td><td>0.761</td><td>0.751</td></tr><tr><td>CatBoost</td><td>0.428</td><td>0.873</td><td>0.386</td><td>0.724</td><td>0.728</td><td>0.948</td><td>0.8893</td><td>8.885</td><td>0.910</td><td>0.749</td><td>0.744</td></tr><tr><td>FT-Transformer</td><td>0.454</td><td>0.860</td><td>0.395</td><td>0.734</td><td>0.731</td><td>0.966</td><td>0.8969</td><td>8.727</td><td>0.973</td><td>0.747</td><td>0.742</td></tr><tr><td colspan="12">Tuned hyperparameters</td></tr><tr><td>XGBoost</td><td>0.431</td><td>0.872</td><td>0.377</td><td>0.724</td><td>0.728</td><td>-</td><td>0.8861</td><td>8.819</td><td>0.969</td><td>0.732</td><td>0.742</td></tr><tr><td>CatBoost</td><td>0.423</td><td>0.874</td><td>0.388</td><td>0.727</td><td>0.729</td><td>-</td><td>0.8898</td><td>8.837</td><td>0.968</td><td>0.740</td><td>0.741</td></tr><tr><td>ResNet</td><td>0.478</td><td>0.857</td><td>0.398</td><td>0.734</td><td>0.731</td><td>0.966</td><td>0.8976</td><td>8.770</td><td>0.967</td><td>0.751</td><td>0.745</td></tr><tr><td>FT-Transformer</td><td>0.448</td><td>0.860</td><td>0.398</td><td>0.739</td><td>0.731</td><td>0.967</td><td>0.8984</td><td>8.751</td><td>0.973</td><td>0.747</td><td>0.743</td></tr></table>

Default hyperparameters. We start with the default configurations to check the “out-of-the-box” performance, which is an important practical scenario. The default FT-Transformer implies a configuration with all hyperparameters set to some specific values that we provide in supplementary. Table 4 demonstrates that the ensemble of FT-Transformers mostly outperforms the ensembles of GBDT, which is not the case for only two datasets (California Housing, Adult). Interestingly, the ensemble of default FT-Transformers performs quite on par with the ensembles of tuned FT-Transformers. The main takeaway: FT-Transformer allows building powerful ensembles out of the box.

Tuned hyperparameters. Once hyperparameters are properly tuned, GBDTs start dominating on some datasets (California Housing, Adult, Yahoo; see Table 4). In those cases, the gaps are significant enough to conclude that DL models do not universally outperform GBDT. Importantly, the fact that DL models outperform GBDT on most of the tasks does not mean that DL solutions are “better” in any sense. In fact, it only means that the constructed benchmark is slightly biased towards “DL-friendly” problems. Admittedly, GBDT remains an unsuitable solution to multiclass problems with a large number of classes. Depending on the number of classes, GBDT can demonstrate unsatisfactory performance (Helena) or even be untunable due to extremely slow training (ALOI). The main takeaways:

• there is still no universal solution among DL models and GBDT

• DL research efforts aimed at surpassing GBDT should focus on datasets where GBDT outperforms state-of-the-art DL solutions. Note that including “DL-friendly” problems is still important to avoid degradation on such problems.

## 4.6 An intriguing property of FT-Transformer

Table 4 tells one more important story. Namely, FT-Transformer delivers most of its advantage over the “conventional” DL model in the form of ResNet exactly on those problems where GBDT is superior to ResNet (California Housing, Adult, Covertype, Yahoo, Microsoft) while performing on par with ResNet on the remaining problems. In other words, FT-Transformer provides competitive performance on all tasks, while GBDT and ResNet perform well only on some subsets of the tasks. This observation may be the evidence that FT-Transformer is a more “universal” model for tabular data problems. We develop this intuition further in section 5.1. Note that the described phenomenon is not related to ensembling and is observed for single models too (see supplementary).

## 5 Analysis

## 5.1 When FT-Transformer is better than ResNet?

In this section, we make the first step towards understanding the difference in behavior between FT-Transformer and ResNet, which was first observed in section 4.6. To achieve that, we design a sequence of synthetic tasks where the difference in performance of the two models gradually changes from negligible to dramatic. Namely, we generate and fix objects $\{ x _ { i } \} _ { i = 1 } ^ { n } ,$ perform the train-val-test split once and interpolate between two regression targets: f<sub>GBDT</sub>, which is supposed to be easier for GBDT and $f _ { D L }$ , which is expected to be easier for ResNet. Formally, for one object:

$$
x \sim \mathcal {N} (0, I _ {k}), \qquad y = \alpha \cdot f _ {G B D T} (x) + (1 - \alpha) \cdot f _ {D L} (x).
$$

where $f _ { G B D T } ( x )$ is an average prediction of 30 randomly constructed decision trees, and $f _ { D L } ( x )$ is an MLP with three randomly initialized hidden layers. Both $f _ { G B D T }$ and $f _ { D L }$ are generated once, i.e. the same functions are applied to all objects (see supplementary for details). The resulting targets are standardized before training. The results are visualized in Figure 3. ResNet and FT-Transformer perform similarly well on the ResNet-friendly tasks and outperform CatBoost on those tasks. However, the ResNet’s relative performance drops significantly when the target becomes more GBDT friendly. By contrast, FT-Transformer yields competitive performance across the whole range of tasks.

![](images/d83bb0d2776ac0ab769ae344465ef776325b08025a2b63a86a0074540d0a25f1.jpg)  
Figure 3: Test RMSE averaged over five seeds (shadows represent std. dev.). One α corresponds to one task; each task has the same set of train, validation and test features, but different targets.

The conducted experiment reveals a type of functions that are better approximated by FT-Transformer than by ResNet. Additionally,

the fact that these functions are based on decision trees correlates with the observations in section 4.6 and the results in Table 4, where FT-Transformer shows the most convincing improvements over ResNet exactly on those datasets where GBDT outperforms ResNet.

## 5.2 Ablation study

In this section, we test some design choices of FT-Transformer.

First, we compare FT-Transformer with AutoInt (Song et al., 2019), since it is the closest competitor in its spirit. AutoInt also converts all features to embeddings and applies self-attention on top of them. However, in its details, AutoInt significantly differs from FT-Transformer: its embedding layer does not include feature biases, its backbone significantly differs from the vanilla Transformer (Vaswani et al., 2017), and the inference mechanism does not use the [CLS] token.

Second, we check whether feature biases in Feature Tokenizer are essential for good performance.

We tune and evaluate FT-Transformer without feature biases following the same protocol as in section 4.3 and reuse the remaining numbers from Table 2. The results averaged over 15 runs are reported in Table 5 and demonstrate both the superiority of the Transformer’s backbone to that of AutoInt and the necessity of feature biases.

Table 5: The results of the comparison between FT-Transformer and two attention-based alternatives: AutoInt and FT-Transformer without feature biases. Notation follows Table 2.

<table><tr><td></td><td>CA ↓</td><td>HE ↑</td><td>JA ↑</td><td>HI ↑</td><td>AL ↑</td><td>YE ↓</td><td>CO ↑</td><td>MI ↓</td></tr><tr><td>AutoInt</td><td>0.474</td><td>0.372</td><td>0.721</td><td>0.725</td><td>0.945</td><td>8.882</td><td>0.934</td><td>0.750</td></tr><tr><td>FT-Transformer (w/o feature biases)</td><td>0.470</td><td>0.381</td><td>0.724</td><td>0.727</td><td>0.958</td><td>8.843</td><td>0.964</td><td>0.751</td></tr><tr><td>FT-Transformer</td><td>0.459</td><td>0.391</td><td>0.732</td><td>0.729</td><td>0.960</td><td>8.855</td><td>0.970</td><td>0.746</td></tr></table>

## 5.3 Obtaining feature importances from attention maps

In this section, we evaluate attention maps as a source of information on feature importances for FT-Transformer for a given set of samples. For the i-th sample, we calculate the average attention map $p _ { i }$ for the [CLS] token from Transformer’s forward pass. Then, the obtained individual distributions are averaged into one distribution $p$ that represents the feature importances:

$$
p = \frac {1}{n _ {s a m p l e s}} \sum_ {i} p _ {i} \qquad p _ {i} = \frac {1}{n _ {h e a d s} \times L} \sum_ {h, l} p _ {i h l}.
$$

where $p _ { i h l }$ is the h-th head’s attention map for the [CLS] token from the forward pass of the l-th layer on the i-th sample. The main advantage of the described heuristic technique is its efficiency: it requires a single forward for one sample.

In order to evaluate our approach, we compare it with Integrated Gradients (IG, Sundararajan et al. (2017)), a general technique applicable to any differentiable model. We use permutation test (PT, Breiman (2001)) as a reasonable interpretable method that allows us to establish a constructive metric, namely, rank correlation. We run all the methods on the train set and summarize results in Table 6. Interestingly, the proposed method yields reasonable feature importances and performs similarly to IG (note that this does not imply similarity to IG’s feature importances). Given that IG can be orders of magnitude slower and the “baseline” in the form of PT requires $( n _ { f e a t u r e s } + 1 )$ forward passes (versus one for the proposed method), we conclude that the simple averaging of attention maps can be a good choice in terms of cost-effectiveness

Table 6: Rank correlation (takes values in [ 1, 1]) between permutation test’s feature importances ranking and two alternative rankings: Attention Maps (AM) and Integrated Gradients (IG). Means and standard deviations over five runs are reported.

<table><tr><td></td><td>CA</td><td>HE</td><td>JA</td><td>HI</td><td>AL</td><td>YE</td><td>CO</td><td>MI</td></tr><tr><td>AM</td><td>0.81 (0.05)</td><td>0.77 (0.03)</td><td>0.78 (0.05)</td><td>0.91 (0.03)</td><td>0.84 (0.01)</td><td>0.92 (0.01)</td><td>0.84 (0.04)</td><td>0.86 (0.02)</td></tr><tr><td>IG</td><td>0.84 (0.08)</td><td>0.74 (0.03)</td><td>0.75 (0.04)</td><td>0.72 (0.03)</td><td>0.89 (0.01)</td><td>0.50 (0.03)</td><td>0.90 (0.02)</td><td>0.56 (0.02)</td></tr></table>

## 6 Conclusion

In this work, we have investigated the status quo in the field of deep learning for tabular data and improved the state of baselines in tabular DL. First, we have demonstrated that a simple ResNet-like architecture can serve as an effective baseline. Second, we have proposed FT-Transformer — a simple adaptation of the Transformer architecture that outperforms other DL solutions on most of the tasks. We have also compared the new baselines with GBDT and demonstrated that GBDT still dominates on some tasks. The code and all the details of the study are open-sourced <sup>1</sup>, and we hope that our evaluation and two simple models (ResNet and FT-Transformer) will serve as a basis for further developments on tabular DL.

## References

T. Akiba, S. Sano, T. Yanase, T. Ohta, and M. Koyama. Optuna: A next-generation hyperparameter optimization framework. In KDD, 2019.

S. O. Arik and T. Pfister. Tabnet: Attentive interpretable tabular learning. arXiv, 1908.07442v5, 2020.

J. L. Ba, J. R. Kiros, and G. E. Hinton. Layer normalization. arXiv, 1607.06450v1, 2016.

S. Badirli, X. Liu, Z. Xing, A. Bhowmik, K. Doan, and S. S. Keerthi. Gradient boosting neural networks: Grownet. arXiv, 2002.07971v2, 2020.

P. Baldi, P. Sadowski, and D. Whiteson. Searching for exotic particles in high-energy physics with deep learning. Nature Communications, 5, 2014.

T. Bertin-Mahieux, D. P. Ellis, B. Whitman, and P. Lamere. The million song dataset. In Proceedings of the 12th International Conference on Music Information Retrieval (ISMIR 2011), 2011.

A. Beutel, P. Covington, S. Jain, C. Xu, J. Li, V. Gatto, and E. H. Chi. Latent cross: Making use of context in recurrent recommender systems. In WSDM 2018: The Eleventh ACM International Conference on Web Search and Data Mining, 2018.

J. A. Blackard and D. J. Dean. Comparative accuracies of artificial neural networks and discriminant analysis in predicting forest cover types from cartographic variables. Computers and Electronics in Agriculture, 24(3):131–151, 2000.

L. Breiman. Random forests. Machine Learning, 45(1):5–32, 2001.

O. Chapelle and Y. Chang. Yahoo! learning to rank challenge overview. In Proceedings of the Learning to Rank Challenge, volume 14, 2011.

T. Chen and C. Guestrin. Xgboost: A scalable tree boosting system. In SIGKDD, 2016.

J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li, and L. Fei-Fei. Imagenet: A large-scale hierarchical image database. In CVPR, 2009.

J. Devlin, M.-W. Chang, K. Lee, and K. Toutanova. Bert: Pre-training of deep bidirectional transformers for language understanding. arXiv, 1810.04805v2, 2019.

A. Dosovitskiy, L. Beyer, A. Kolesnikov, D. Weissenborn, X. Zhai, T. Unterthiner, M. Dehghani, M. Minderer, G. Heigold, S. Gelly, et al. An image is worth 16x16 words: Transformers for image recognition at scale. In ICLR, 2021.

S. Fort, H. Hu, and B. Lakshminarayanan. Deep ensembles: A loss landscape perspective. arXiv, 1912.02757v2, 2020.

J. H. Friedman. Greedy function approximation: A gradient boosting machine. The Annals of Statistics, 29(5):1189–1232, 2001.

J. M. Geusebroek, G. J. Burghouts, , and A. W. M. Smeulders. The amsterdam library of object images. Int. J. Comput. Vision, 61(1):103–112, 2005.

I. Goodfellow, Y. Bengio, and A. Courville. Deep Learning. MIT Press, 2016. http://www. deeplearningbook.org.

I. Guyon, L. Sun-Hosoya, M. Boullé, H. J. Escalante, S. Escalera, Z. Liu, D. Jajetic, B. Ray, M. Saeed, M. Sebag, A. Statnikov, W. Tu, and E. Viegas. Analysis of the automl challenge series 2015-2018. In AutoML, Springer series on Challenges in Machine Learning, 2019.

H. Hazimeh, N. Ponomareva, P. Mol, Z. Tan, and R. Mazumder. The tree ensemble layer: Differentiability meets conditional computation. In ICML, 2020.

K. He, X. Zhang, S. Ren, and J. Sun. Delving deep into rectifiers: Surpassing human-level performance on imagenet classification. In ICCV, 2015a.

K. He, X. Zhang, S. Ren, and J. Sun. Deep residual learning for image recognition. arXiv, 1512.03385v1, 2015b.

K. He, X. Zhang, S. Ren, and J. Sun. Identity mappings in deep residual networks. In ECCV, 2016.

X. Huang, A. Khetan, M. Cvitkovic, and Z. Karnin. Tabtransformer: Tabular data modeling using contextual embeddings. arXiv, 2012.06678v1, 2020a.

X. S. Huang, F. Perez, J. Ba, and M. Volkovs. Improving transformer optimization through better initialization. In ICML, 2020b.

G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, and T.-Y. Liu. Lightgbm: A highly efficient gradient boosting decision tree. Advances in neural information processing systems, 30: 3146–3154, 2017.

R. Kelley Pace and R. Barry. Sparse spatial autoregressions. Statistics & Probability Letters, 33(3): 291–297, 1997.

D. P. Kingma and J. Ba. Adam: A method for stochastic optimization. arXiv, 1412.6980v9, 2017.

G. Klambauer, T. Unterthiner, A. Mayr, and S. Hochreiter. Self-normalizing neural networks. In NIPS, 2017.

R. Kohavi. Scaling up the accuracy of naive-bayes classifiers: a decision-tree hybrid. In KDD, 1996.

P. Kontschieder, M. Fiterau, A. Criminisi, and S. Rota Bulo. Deep neural decision forests. In Proceedings of the IEEE international conference on computer vision, 2015.

L. Liu, X. Liu, J. Gao, W. Chen, and J. Han. Understanding the difficulty of training transformers. In EMNLP, 2020.

I. Loshchilov and F. Hutter. Decoupled weight decay regularization. In ICLR, 2019.

Y. Lou and M. Obukhov. Bdt: Gradient boosted decision tables for high accuracy and scoring efficiency. In Proceedings of the 23rd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 2017.

S. Moro, P. Cortez, and P. Rita. A data-driven approach to predict the success of bank telemarketing. Decis. Support Syst., 62:22–31, 2014.

S. Narang, H. W. Chung, Y. Tay, W. Fedus, T. Fevry, M. Matena, K. Malkan, N. Fiedel, N. Shazeer, Z. Lan, Y. Zhou, W. Li, N. Ding, J. Marcus, A. Roberts, and C. Raffel. Do transformer modifications transfer across implementations and applications? arXiv, 2102.11972v1, 2021.

T. Q. Nguyen and J. Salazar. Transformers without tears: Improving the normalization of selfattention. In IWSLT, 2019.

F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, M. Blondel, P. Prettenhofer, R. Weiss, V. Dubourg, J. Vanderplas, A. Passos, D. Cournapeau, M. Brucher, M. Perrot, and E. Duchesnay. Scikit-learn: Machine learning in Python. Journal ofMachine Learning Research, 12:2825–2830, 2011.

S. Popov, S. Morozov, and A. Babenko. Neural oblivious decision ensembles for deep learning on tabular data. In ICLR, 2020.

L. Prokhorenkova, G. Gusev, A. Vorobev, A. V. Dorogush, and A. Gulin. Catboost: unbiased boosting with categorical features. In NeurIPS, 2018.

T. Qin and T. Liu. Introducing LETOR 4.0 datasets. arXiv, 1306.2597v1, 2013.

Z. Qin, L. Yan, H. Zhuang, Y. Tay, R. K. Pasumarthi, X. Wang, M. Bendersky, and M. Najork. Are neural rankers still outperformed by gradient boosted decision trees? In ICLR, 2021.

N. Shazeer. Glu variants improve transformer. arXiv, 2002.05202v1, 2020.

W. Song, C. Shi, Z. Xiao, Z. Duan, Y. Xu, M. Zhang, and J. Tang. Autoint: Automatic feature interaction learning via self-attentive neural networks. In CIKM, 2019.

N. Srivastava, G. E. Hinton, A. Krizhevsky, I. Sutskever, and R. Salakhutdinov. Dropout: a simple way to prevent neural networks from overfitting. Journal of Machine Learning Research, 15(1): 1929–1958, 2014.

S. Sun and M. Iyyer. Revisiting simple neural probabilistic language models. In NAACL, 2021.

M. Sundararajan, A. Taly, and Q. Yan. Axiomatic attribution for deep networks. In ICML, 2017.

Y. Tay, M. Dehghani, D. Bahri, and D. Metzler. Efficient transformers: A survey. arXiv, 2009.06732v1, 2020.

R. Turner, D. Eriksson, M. McCourt, J. Kiili, E. Laaksonen, Z. Xu, and I. Guyon. Bayesian optimization is superior to random search for machine learning hyperparameter tuning: Analysis of the black-box optimization challenge 2020. arXiv, https://arxiv.org/abs/2104.10201v1, 2021.

J. Vanschoren, J. N. van Rijn, B. Bischl, and L. Torgo. Openml: networked science in machine learning. arXiv, 1407.7722v1, 2014.

A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, L. Kaiser, and I. Polosukhin. Attention is all you need. In NIPS, 2017.

A. Wang, A. Singh, J. Michael, F. Hill, O. Levy, and S. R. Bowman. GLUE: A multi-task benchmark and analysis platform for natural language understanding. In ICLR, 2019a.

Q. Wang, B. Li, T. Xiao, J. Zhu, C. Li, D. F. Wong, and L. S. Chao. Learning deep transformer models for machine translation. In ACL, 2019b.

R. Wang, B. Fu, G. Fu, and M. Wang. Deep & cross network for ad click predictions. In ADKDD, 2017.

R. Wang, R. Shivanna, D. Z. Cheng, S. Jain, D. Lin, L. Hong, and E. H. Chi. Dcn v2: Improved deep & cross network and practical lessons for web-scale learning to rank systems. arXiv, 2008.13535v2, 2020a.

S. Wang, B. Z. Li, M. Khabsa, H. Fang, and H. Ma. Linformer: Self-attention with linear complexity. arXiv, 2006.04768v3, 2020b.

N. Wies, Y. Levine, D. Jannai, and A. Shashua. Which transformer architecture fits my data? a vocabulary bottleneck in self-attention. In ICLM, 2021.

F. Wilcoxon. Individual comparisons by ranking methods. Biometrics Bulletin, 1(6):80, 1945.

T. Wolf, L. Debut, V. Sanh, J. Chaumond, C. Delangue, A. Moi, P. Cistac, T. Rault, R. Louf, M. Funtowicz, J. Davison, S. Shleifer, P. von Platen, C. Ma, Y. Jernite, J. Plu, C. Xu, T. L. Scao, S. Gugger, M. Drame, Q. Lhoest, and A. M. Rush. Huggingface’s transformers: State-of-the-art natural language processing. arXiv, 1910.03771v5, 2020.

Y. Yang, I. G. Morillo, and T. M. Hospedales. Deep neural decision trees. arXiv, 1806.06988v1, 2018.

## Supplementary material

## A Software and hardware

For most model-dataset pairs the workflow was as follows:

• tune the model on any suitable hardware

• evaluate the tuned model on one or more NVidia Tesla V100 32Gb

All the experiments were conducted under the same conditions in terms of software versions. For almost all experiments the used hardware can be found in the source code.

## B Data

## B.1 Datasets

Table 7: Datasets description

<table><tr><td>Name</td><td>Abbr</td><td># Train</td><td># Validation</td><td># Test</td><td># Num</td><td># Cat</td><td>Task type</td><td>Batch size</td></tr><tr><td>California Housing</td><td>CA</td><td>13209</td><td>3303</td><td>4128</td><td>8</td><td>0</td><td>Regression</td><td>256</td></tr><tr><td>Adult</td><td>AD</td><td>26048</td><td>6513</td><td>16281</td><td>6</td><td>8</td><td>Binclass</td><td>256</td></tr><tr><td>Helena</td><td>HE</td><td>41724</td><td>10432</td><td>13040</td><td>27</td><td>0</td><td>Multiclass</td><td>512</td></tr><tr><td>Jannis</td><td>JA</td><td>53588</td><td>13398</td><td>16747</td><td>54</td><td>0</td><td>Multiclass</td><td>512</td></tr><tr><td>Higgs Small</td><td>HI</td><td>62752</td><td>15688</td><td>19610</td><td>28</td><td>0</td><td>Binclass</td><td>512</td></tr><tr><td>ALOI</td><td>AL</td><td>69120</td><td>17280</td><td>21600</td><td>128</td><td>0</td><td>Multiclass</td><td>512</td></tr><tr><td>Epsilon</td><td>EP</td><td>320000</td><td>80000</td><td>100000</td><td>2000</td><td>0</td><td>Binclass</td><td>1024</td></tr><tr><td>Year</td><td>YE</td><td>370972</td><td>92743</td><td>51630</td><td>90</td><td>0</td><td>Regression</td><td>1024</td></tr><tr><td>Covtype</td><td>CO</td><td>371847</td><td>92962</td><td>116203</td><td>54</td><td>0</td><td>Multiclass</td><td>1024</td></tr><tr><td>Yahoo</td><td>YA</td><td>473134</td><td>71083</td><td>165660</td><td>699</td><td>0</td><td>Regression</td><td>1024</td></tr><tr><td>Microsoft</td><td>MI</td><td>723412</td><td>235259</td><td>241521</td><td>136</td><td>0</td><td>Regression</td><td>1024</td></tr></table>

## B.2 Preprocessing

For regression problems, we standardize the target values:

$$
y _ {n e w} = \frac {y _ {o l d} - \mathrm{mean} (y _ {t r a i n}))}{\mathsf {s t d} (y _ {t r a i n})}\tag{3}
$$

The feature preprocessing for DL models is described in the main text. Note that we add noise from $\mathcal { N } ( 0 , 1 e - 3 )$ to train numerical features for calculating the parameters (quantiles) of the quantile preprocessing as a workaround for features with few distinct values (see the source code for the exact implementation). The preprocessing is then applied to original features. We do not preprocess features for GBDTs, since this family of algorithms is insensitive to feature shifts and scaling.

## C Results for all algorithms on all datasets

To measure statistical significance in the main text and in the tables in this section, we use the one-sided Wilcoxon (1945) test with $p = 0 . 0 1$

Table 8 and Table 9 report all results for all models on all datasets.

<table><tr><td></td><td>CA ↓</td><td>AD ↑</td><td>HE ↑</td><td>JA ↑</td><td>HI ↑</td><td>AL ↑</td><td>EP ↑</td><td>YE ↓</td><td>CO ↑</td><td>YA ↓</td><td>MI ↓</td></tr><tr><td colspan="12">Baseline Neural Networks</td></tr><tr><td>TabNet</td><td> $0.510 \pm 7.6e-3$ </td><td> $0.850 \pm 5.2e-3$ </td><td> $0.378 \pm 1.7e-3$ </td><td> $0.723 \pm 3.5e-3$ </td><td> $0.719 \pm 1.7e-3$ </td><td> $0.954 \pm 1.0e-3$ </td><td> $0.8896 \pm 3.1e-3$ </td><td> $8.909 \pm 2.3e-2$ </td><td> $0.957 \pm 7.5e-3$ </td><td> $0.823 \pm 9.2e-3$ </td><td> $0.751 \pm 9.4e-4$ </td></tr><tr><td>SNN</td><td> $0.493 \pm 4.6e-3$ </td><td> $0.854 \pm 1.8e-3$ </td><td> $0.373 \pm 2.8e-3$ </td><td> $0.719 \pm 1.6e-3$ </td><td> $0.722 \pm 2.2e-3$ </td><td> $0.954 \pm 1.6e-3$ </td><td> $0.8975 \pm 2.4e-4$ </td><td> $8.895 \pm 1.9e-2$ </td><td> $0.961 \pm 2.0e-3$ </td><td> $0.761 \pm 5.3e-4$ </td><td> $0.751 \pm 5.2e-4$ </td></tr><tr><td>AutoInt</td><td> $0.474 \pm 3.3e-3$ </td><td> $0.859 \pm 1.5e-3$ </td><td> $0.372 \pm 2.5e-3$ </td><td> $0.721 \pm 2.3e-3$ </td><td> $0.725 \pm 1.7e-3$ </td><td> $0.945 \pm 1.3e-3$ </td><td> $0.8949 \pm 5.8e-4$ </td><td> $8.882 \pm 3.3e-2$ </td><td> $0.934 \pm 3.5e-3$ </td><td> $0.768 \pm 1.1e-3$ </td><td> $0.750 \pm 6.1e-4$ </td></tr><tr><td>GrowNet</td><td> $0.487 \pm 7.1e-3$ </td><td> $0.857 \pm 1.9e-3$ </td><td>-</td><td>-</td><td> $0.722 \pm 1.6e-3$ </td><td>-</td><td> $0.8970 \pm 5.7e-4$ </td><td> $8.827 \pm 3.8e-2$ </td><td>-</td><td> $0.765 \pm 1.2e-3$ </td><td> $0.751 \pm 4.7e-4$ </td></tr><tr><td>MLP</td><td> $0.499 \pm 2.9e-3$ </td><td> $0.852 \pm 1.9e-3$ </td><td> $0.383 \pm 2.6e-3$ </td><td> $0.719 \pm 1.3e-3$ </td><td> $0.723 \pm 1.8e-3$ </td><td> $0.954 \pm 1.4e-3$ </td><td> $0.8977 \pm 4.1e-4$ </td><td> $8.853 \pm 3.1e-2$ </td><td> $0.962 \pm 1.1e-3$ </td><td> $0.757 \pm 3.5e-4$ </td><td> $0.747 \pm 3.3e-4$ </td></tr><tr><td>DCN2</td><td> $0.484 \pm 2.4e-3$ </td><td> $0.853 \pm 3.9e-3$ </td><td> $0.385 \pm 3.0e-3$ </td><td> $0.716 \pm 1.5e-3$ </td><td> $0.723 \pm 1.3e-3$ </td><td> $0.955 \pm 1.2e-3$ </td><td> $0.8977 \pm 2.6e-4$ </td><td> $8.890 \pm 2.8e-2$ </td><td> $0.965 \pm 1.0e-3$ </td><td> $0.757 \pm 1.9e-3$ </td><td> $0.749 \pm 5.8e-4$ </td></tr><tr><td>NODE</td><td> $0.464 \pm 1.5e-3$ </td><td> $0.858 \pm 1.6e-3$ </td><td> $0.359 \pm 2.0e-3$ </td><td> $0.727 \pm 1.6e-3$ </td><td> $0.726 \pm 1.3e-3$ </td><td> $0.918 \pm 5.4e-3$ </td><td> $0.8958 \pm 4.7e-4$ </td><td> $8.784 \pm 1.6e-2$ </td><td> $0.958 \pm 1.1e-3$ </td><td> $0.753 \pm 2.5e-4$ </td><td> $0.745 \pm 2.0e-4$ </td></tr><tr><td>ResNet</td><td> $0.486 \pm 2.9e-3$ </td><td> $0.854 \pm 1.7e-3$ </td><td> $0.396 \pm 1.7e-3$ </td><td> $0.728 \pm 1.5e-3$ </td><td> $0.727 \pm 1.7e-3$ </td><td> $0.963 \pm 7.5e-4$ </td><td> $0.8969 \pm 4.4e-4$ </td><td> $8.846 \pm 2.4e-2$ </td><td> $0.964 \pm 1.1e-3$ </td><td> $0.757 \pm 6.2e-4$ </td><td> $0.748 \pm 3.1e-4$ </td></tr><tr><td colspan="12">FT-Transformer</td></tr><tr><td>FT-Transformerd</td><td> $0.469 \pm 3.8e-3$ </td><td> $0.857 \pm 1.1e-3$ </td><td> $0.381 \pm 2.4e-3$ </td><td> $0.725 \pm 2.3e-3$ </td><td> $0.725 \pm 1.8e-3$ </td><td> $0.953 \pm 1.1e-3$ </td><td> $0.8959 \pm 4.9e-4$ </td><td> $8.889 \pm 4.6e-2$ </td><td> $0.967 \pm 7.9e-4$ </td><td> $0.756 \pm 8.2e-4$ </td><td> $0.747 \pm 7.9e-4$ </td></tr><tr><td>FT-Transformer</td><td> $0.459 \pm 3.5e-3$ </td><td> $0.859 \pm 1.0e-3$ </td><td> $0.391 \pm 1.2e-3$ </td><td> $0.732 \pm 2.0e-3$ </td><td> $0.729 \pm 1.5e-3$ </td><td> $0.960 \pm 1.1e-3$ </td><td> $0.8982 \pm 2.8e-4$ </td><td> $8.855 \pm 3.1e-2$ </td><td> $0.970 \pm 6.6e-4$ </td><td> $0.756 \pm 8.2e-4$ </td><td> $0.746 \pm 4.9e-4$ </td></tr><tr><td colspan="12">GBDT</td></tr><tr><td>CatBoostd</td><td> $0.430 \pm 7.4e-4$ </td><td> $0.873 \pm 9.6e-4$ </td><td> $0.381 \pm 1.5e-3$ </td><td> $0.721 \pm 1.1e-3$ </td><td> $0.726 \pm 8.0e-4$ </td><td> $0.946 \pm 9.3e-4$ </td><td> $0.8880 \pm 4.5e-4$ </td><td> $8.913 \pm 5.5e-3$ </td><td> $0.908 \pm 2.4e-4$ </td><td> $0.751 \pm 2.0e-4$ </td><td> $0.745 \pm 2.3e-4$ </td></tr><tr><td>CatBoost</td><td> $0.431 \pm 1.5e-3$ </td><td> $0.873 \pm 1.2e-3$ </td><td> $0.385 \pm 1.1e-3$ </td><td> $0.723 \pm 1.5e-3$ </td><td> $0.725 \pm 1.5e-3$ </td><td>-</td><td> $0.8880 \pm 5.8e-4$ </td><td> $8.877 \pm 6.0e-3$ </td><td> $0.966 \pm 2.7e-4$ </td><td> $0.743 \pm 2.4e-4$ </td><td> $0.743 \pm 2.1e-4$ </td></tr><tr><td>XGBoostd</td><td> $0.462 \pm 0.0$ </td><td> $0.874 \pm 0.0$ </td><td> $0.348 \pm 0.0$ </td><td> $0.711 \pm 0.0$ </td><td> $0.717 \pm 0.0$ </td><td> $0.924 \pm 0.0$ </td><td> $0.8799 \pm 0.0$ </td><td> $9.192 \pm 0.0$ </td><td> $0.964 \pm 0.0$ </td><td> $0.761 \pm 0.0$ </td><td> $0.751 \pm 0.0$ </td></tr><tr><td>XGBoost</td><td> $0.433 \pm 1.6e-3$ </td><td> $0.872 \pm 4.6e-4$ </td><td> $0.375 \pm 1.2e-3$ </td><td> $0.721 \pm 1.0e-3$ </td><td> $0.727 \pm 1.0e-3$ </td><td>-</td><td> $0.8837 \pm 1.2e-3$ </td><td> $8.947 \pm 8.5e-3$ </td><td> $0.969 \pm 5.1e-4$ </td><td> $0.736 \pm 2.1e-4$ </td><td> $0.742 \pm 1.3e-4$ </td></tr></table>

## D Additional results

## D.1 Training times

Table 10: Training times in seconds averaged over 15 runs.

<table><tr><td></td><td>CA</td><td>AD</td><td>HE</td><td>JA</td><td>HI</td><td>AL</td><td>EP</td><td>YE</td><td>CO</td><td>YA</td><td>MI</td></tr><tr><td>ResNet</td><td>72</td><td>144</td><td>363</td><td>163</td><td>91</td><td>933</td><td>704</td><td>777</td><td>4026</td><td>923</td><td>1243</td></tr><tr><td>FT-Transformer</td><td>187</td><td>128</td><td>536</td><td>576</td><td>257</td><td>2864</td><td>934</td><td>1776</td><td>5050</td><td>12712</td><td>2857</td></tr><tr><td>Overhead</td><td>2.6x</td><td>0.9x</td><td>1.5x</td><td>3.5x</td><td>2.8x</td><td>3.1x</td><td>1.3x</td><td>2.3x</td><td>1.3x</td><td>13.8x</td><td>2.3x</td></tr></table>

For most experiments, training times can be found in the source code. In Table 10, we provide the comparison between ResNet and FT-Transformer in order to “visualize” the overhead introduced by FT-Transformer compared to the main “conventional” DL baseline. The big difference on the Yahoo dataset is expected because of the large number of features (700).

## D.2 How tuning time budget affects performance?

In this section, we aim to answer the following questions:

• how does the relative performance of tuned models depends on tuning time budget?

• does the number of tuning iterations used in the main text allow models to reach most of their potential?

The first question is important for two main reasons. First, we have to make sure that longer tuning times of FT-Transformer (the number of tuning iterations is the same as for all other models) is not the reason of its strong performance. Second, we want to test FT-Transformer in the regime of low tuning time budget.

We consider four algorithms: XGBoost (as a fast GBDT implementation), MLP (as the fastest and simplest DL model), ResNet (as a stronger but slower DL model), FT-Transformer (as the strongest and the slowest DL model). We consider three datasets: California Housing, Adult, Higgs Small. On each dataset, for each algorithm, we run five independent (five random seeds) hyperparameter optimizations. Each run is constrained only by time. For each of the considered time budgets (15 minutes, 30 minutes, 1 hour, 2 hours, 3 hours, 4 hours, 5 hours, 6 hours), we pick the best model identified by Optuna on the validation set using no more than this time budget. Then, we report its performance and the number of Optuna iterations averaged over the five random seeds. The results are reported in Table 11. The takeaways are as follows:

• interestingly, FT-Transformer achieves good metrics just after several randomly sampled configurations (Optuna performs simple random sampling during the first 10 (default) iterations).

• FT-Transformer is slower to train, which is expected

• extended tuning (in terms of iterations) for other algorithms does not lead to any meaningful improvements

Table 11: Performance of tuned models with different tuning time budgets. Tuned model performance and the number of Optuna iterations (in parentheses) are reported (both metrics are averaged over five random seeds). Best results among DL models are in bold, overall best results are in bold red.

<table><tr><td></td><td>0.25h</td><td>0.5h</td><td>1h</td><td>2h</td><td>3h</td><td>4h</td><td>5h</td><td>6h</td></tr><tr><td colspan="9">California Housing</td></tr><tr><td>XGBoost</td><td>0.437 (31)</td><td>0.436 (56)</td><td>0.434 (120)</td><td>0.433 (252)</td><td>0.433 (410)</td><td>0.432 (557)</td><td>0.433 (719)</td><td>0.432 (867)</td></tr><tr><td>MLP</td><td>0.503(16)</td><td>0.496(42)</td><td>0.493(103)</td><td>0.488(230)</td><td>0.489(349)</td><td>0.489(466)</td><td>0.488(596)</td><td>0.488(724)</td></tr><tr><td>ResNet</td><td>0.488(7)</td><td>0.487(15)</td><td>0.483(30)</td><td>0.481(64)</td><td>0.482(101)</td><td>0.482(131)</td><td>0.482(164)</td><td>0.484(197)</td></tr><tr><td>FT-Transformer</td><td>0.466 (4)</td><td>0.464 (9)</td><td>0.465 (20)</td><td>0.460 (47)</td><td>0.458 (74)</td><td>0.458 (99)</td><td>0.457 (124)</td><td>0.459 (153)</td></tr><tr><td colspan="9">Adult</td></tr><tr><td>XGBoost</td><td>0.871 (165)</td><td>0.873 (311)</td><td>0.872 (638)</td><td>0.872 (1296)</td><td>0.872 (1927)</td><td>0.872 (2478)</td><td>0.872 (2999)</td><td>0.872 (3500)</td></tr><tr><td>MLP</td><td>0.856(20)</td><td>0.857(37)</td><td>0.858(71)</td><td>0.857(130)</td><td>0.856(190)</td><td>0.856(247)</td><td>0.856(310)</td><td>0.856(375)</td></tr><tr><td>ResNet</td><td>0.856(8)</td><td>0.854(16)</td><td>0.854(32)</td><td>0.856(69)</td><td>0.855(105)</td><td>0.855(140)</td><td>0.856(174)</td><td>0.855(208)</td></tr><tr><td>FT-Transformer</td><td>0.861 (6)</td><td>0.860 (12)</td><td>0.859 (27)</td><td>0.859 (52)</td><td>0.860 (78)</td><td>0.860 (99)</td><td>0.860 (125)</td><td>0.860 (148)</td></tr><tr><td colspan="9">Higgs Small</td></tr><tr><td>XGBoost</td><td>0.725(88)</td><td>0.725(153)</td><td>0.724(291)</td><td>0.725(573)</td><td>0.725(823)</td><td>0.726(1069)</td><td>0.725(1318)</td><td>0.725(1559)</td></tr><tr><td>MLP</td><td>0.721(16)</td><td>0.720(29)</td><td>0.723(62)</td><td>0.722(137)</td><td>0.724(220)</td><td>0.723(300)</td><td>0.724(375)</td><td>0.724(447)</td></tr><tr><td>ResNet</td><td>0.724(8)</td><td>0.727(14)</td><td>0.727(32)</td><td>0.728(61)</td><td>0.728(84)</td><td>0.728(107)</td><td>0.728(132)</td><td>0.728(154)</td></tr><tr><td>FT-Transformer</td><td>0.727 (2)</td><td>0.729 (5)</td><td>0.728 (12)</td><td>0.728 (23)</td><td>0.729 (34)</td><td>0.729 (44)</td><td>0.730 (56)</td><td>0.729 (66)</td></tr></table>

## E FT-Transformer

In this section, we formally describe the details of FT-Transformer its tuning and evaluation. Also, we share additional technical experience and observations that were not used for final results in the paper but may be of interest to researchers and practitioners.

## E.1 Architecture

Formal definition.

FT-Transformer(x) = Prediction(Block(. . . (Block(AppendCLS(FeatureTokenizer(x))))))

$$
\operatorname{Block} (x) = \text { ResidualPreNorm } (\text { FFN }, \text { ResidualPreNorm } (\text { MHSA }, x))
$$

ResidualPreNorm(Module, x) = x + Dropout(Module(Norm(x)))

$$
\operatorname{FFN} (x) = \text { Linear } (\text { Dropout } (\text { Activation } (\text { Linear } (x))))
$$

We use LayerNorm (Ba et al., 2016) as the normalization. See the main text for the description of Prediction and FeatureTokenizer. For MHSA, we set $n _ { h e a d s } = 8$ and do not tune this parameter.

Activation. Throughout the whole paper we used the ReGLU activation, since it is reported to be superior to the usually used GELU activation (Narang et al., 2021; Shazeer, 2020). However, we did not observe strong difference between ReGLU and ReLU in preliminary experiments.

Dropout rates. We observed that the attention dropout is always beneficial and FFN-dropout is also usually set by the tuning process to some non-zero value. As for the final dropout of each residual branch, it is rarely set to non-zero values by the tuning process.

PreNorm vs PostNorm. We use the PreNorm variant of Transformer, i.e. normalizations are placed at the beginning of each residual branch. The PreNorm variant is known for better optimization properties as opposed to the original Transformer, which is a PostNorm-Transformer (Liu et al., 2020; Nguyen and Salazar, 2019; Wang et al., 2019b). The latter one may produce better models in terms of target metrics (Liu et al., 2020), but it usually requires additional modifications to the model and/or the training process, such as learning rate warmup or complex initialization schemes (Huang et al., 2020b; Liu et al., 2020). While the PostNorm variant can be an option for practitioners seeking for the best possible model, we use the PreNorm variant in order to keep the optimization simple and same for all models. Note that in the PostNorm formulation the LayerNorm in the "Prediction" equation (see the section “FT-Transformer” in the main text) should be omitted.

## E.2 The default configuration(s)

Table 12 describes the configuration of FT-Transformer referred to as “default” in the main text. Note that it includes hyperparameters for both the model and the optimization. In fact, the configuration is a result of an “educated guess” and we did not invest much resources in its tuning.

Table 12: Default FT-Transformer used in the main text.

<table><tr><td>Layer count</td><td>3</td><td></td></tr><tr><td>Feature embedding size</td><td>192</td><td></td></tr><tr><td>Head count</td><td>8</td><td></td></tr><tr><td>Activation &amp; FFN size factor</td><td>(ReLU, 4/3)</td><td></td></tr><tr><td>Attention dropout</td><td>0.2</td><td></td></tr><tr><td>FFN dropout</td><td>0.1</td><td></td></tr><tr><td>Residual dropout</td><td>0.0</td><td></td></tr><tr><td>Initialization</td><td>Kaiming</td><td>(He et al., 2015a)</td></tr><tr><td>Parameter count</td><td>929K</td><td>The value is given for 100 numerical features</td></tr><tr><td>Optimizer</td><td>AdamW</td><td></td></tr><tr><td>Learning rate</td><td>1e-4</td><td></td></tr><tr><td>Weight decay</td><td>1e-5</td><td>0.0 for Feature Tokenizer, LayerNorm and biases</td></tr></table>

where “FFN size factor” is a ratio of the FFN’s hidden size to the feature embedding size.

We also designed a heuristic scaling rule to produce “default” configurations with the number of layers from one to six. We applied it on the Epsilon and Yahoo datasets in order to reduce the number of tuning iterations. However, we did not dig into the topic and our scaling rule may be suboptimal, see Wies et al. (2021) for a theoretically sound scaling rule.

In Table 13, we provide hyperparameter space used for Optuna-driven tuning (Akiba et al., 2019). For Epsilon, however, we iterated over several “default” configurations using a heuristic scaling rule, since the full tuning procedure turned out to be too time consuming. For Yahoo, we did not perform tuning at all, since the default configuration already performed well. In the main text, for FT-Transformer on Yahoo, we report the result of the default FT-Transformer.

Table 13: FT-Transformer hyperparameter space. Here (A) = {CA, AD, HE, JA, HI} and (B) = {AL, YE, CO, MI}

<table><tr><td>Parameter</td><td>(Datasets) Distribution</td></tr><tr><td># Layers</td><td>(A) UniformInt[1, 4], (B) UniformInt[1, 6]</td></tr><tr><td>Feature embedding size</td><td>(A,B) UniformInt[64, 512]</td></tr><tr><td>Residual dropout</td><td>(A) {0, Uniform[0, 0.2]}, (B) Const(0.0)</td></tr><tr><td>Attention dropout</td><td>(A,B) Uniform[0, 0.5]</td></tr><tr><td>FFN dropout</td><td>(A,B) Uniform[0, 0.5]</td></tr><tr><td>FFN factor</td><td>(A) Uniform[2/3, 8/3], (B) Const(4/3)</td></tr><tr><td>Learning rate</td><td>(A) LogUniform[1e-5, 1e-3], (B) LogUniform[3e-5, 3e-4]</td></tr><tr><td>Weight decay</td><td>(A,B) LogUniform[1e-6, 1e-3]</td></tr><tr><td># Iterations</td><td>(A) 100, (B) 50</td></tr></table>

## E.3 Training

On the Epsilon dataset, we scale FT-Transformer using the technique proposed by Wang et al. (2020b) with the “headwise” sharing policy; we set the projection dimension to 128. We follow the popular “transformers” library (Wolf et al., 2020) and do not apply weight decay to Feature Tokenizer, biases in linear layers and normalization layers.

## F Models

In this section, we describe the implementation details for all models. See section E.1 for details on FT-Transformer.

## F.1 ResNet

Architecture. The architecture is formally described in the main text.

We tested several configurations and observed measurable difference in performance between all of them. We found the ones with “clear main path” (i.e. with all normalizations (except the last one) placed only in residual branches as in He et al. (2016) or Wang et al. (2019b)) to perform better. As expected, it is also easier for them to train deeper configurations. We found the block design inspired by Transformer (Vaswani et al., 2017) to perform better or on par with the one inspired by the ResNet from computer vision (He et al., 2015b).

We observed that in the “optimal” configurations (the result of the hyperparameter optimization process) the inner dropout rate (not the last one) of one block was usually set to higher values compared to the outer dropout rate. Moreover, the latter one was set to zero in many cases.

Implementation. Ours, see the source code.

In Table 14, we provide hyperparameter space used for Optuna-driven tuning (Akiba et al., 2019).

Table 14: ResNet hyperparameter space. Here (A) = {CA, AD, HE, JA, HI, AL} and (B) = {EP, YE, CO, YA, MI}

<table><tr><td>Parameter</td><td>(Datasets) Distribution</td></tr><tr><td># Layers</td><td>(A) UniformInt[1, 8], (B) UniformInt[1, 16]</td></tr><tr><td>Layer size</td><td>(A) UniformInt[64, 512], (B) UniformInt[64, 1024]</td></tr><tr><td>Hidden factor</td><td>(A,B) Uniform[1, 4]</td></tr><tr><td>Hidden dropout</td><td>(A,B) Uniform[0, 0.5]</td></tr><tr><td>Residual dropout</td><td>(A,B) {0, Uniform[0, 0.5]}</td></tr><tr><td>Learning rate</td><td>(A,B) LogUniform[1e-5, 1e-2]</td></tr><tr><td>Weight decay</td><td>(A,B) {0, LogUniform[1e-6, 1e-3]}</td></tr><tr><td>Category embedding size</td><td>({AD}) UniformInt[64, 512]</td></tr><tr><td># Iterations</td><td>100</td></tr></table>

## F.2 MLP

Architecture. The architecture is formally described in the main text.

Implementation. Ours, see the source code.

In Table 15, we provide hyperparameter space used for Optuna-driven tuning (Akiba et al., 2019). Note that the size of the first and the last layers are tuned and set separately, while the size for “in-between” layers is the same for all of them.

## F.3 XGBoost

Implementation. We fix and do not tune the following hyperparameters:

• booster = "gbtree"

• early-stopping-rounds = 50

• n-estimators = 2000

Table 15: MLP hyperparameter space. Here (A) = {CA, AD, HE, JA, HI, AL} and (B) = {EP, YE, CO, YA, MI}

<table><tr><td>Parameter</td><td>(Datasets) Distribution</td></tr><tr><td># Layers</td><td>(A) UniformInt[1, 8], (B) UniformInt[1, 16]</td></tr><tr><td>Layer size</td><td>(A) UniformInt[1, 512], (B) UniformInt[1, 1024]</td></tr><tr><td>Dropout</td><td>(A,B) {0, Uniform[0, 0.5]}</td></tr><tr><td>Learning rate</td><td>(A,B) LogUniform[1e-5, 1e-2]</td></tr><tr><td>Weight decay</td><td>(A,B) {0, LogUniform[1e-6, 1e-3]}</td></tr><tr><td>Category embedding size</td><td>({AD}) UniformInt[64, 512]</td></tr><tr><td># Iterations</td><td>100</td></tr></table>

In Table 16, we provide hyperparameter space used for Optuna-driven tuning (Akiba et al., 2019).

Table 16: XGBoost hyperparameter space. Here (A) = {CA, AD, HE, JA, HI} and (B) = {EP, YE, CO, YA, MI}

<table><tr><td>Parameter</td><td>(Datasets) Distribution</td></tr><tr><td>Max depth</td><td>(A) UniformInt[3, 10], (B) UniformInt[6, 10]</td></tr><tr><td>Min child weight</td><td>(A,B) LogUniform[1e-8, 1e5]</td></tr><tr><td>Subsample</td><td>(A,B) Uniform[0.5, 1]</td></tr><tr><td>Learning rate</td><td>(A,B) LogUniform[1e-5, 1]</td></tr><tr><td>Col sample by level</td><td>(A,B) Uniform[0.5, 1]</td></tr><tr><td>Col sample by tree</td><td>(A,B) Uniform[0.5, 1]</td></tr><tr><td>Gamma</td><td>(A,B) {0, LogUniform[1e-8, 1e2]}</td></tr><tr><td>Lambda</td><td>(A,B) {0, LogUniform[1e-8, 1e2]}</td></tr><tr><td>Alpha</td><td>(A,B) {0, LogUniform[1e-8, 1e2]}</td></tr><tr><td># Iterations</td><td>100</td></tr></table>

## F.4 CatBoost

Implementation. We fix and do not tune the following hyperparameters:

• early-stopping-rounds = 50

• od-pval = 0.001

• iterations = 2000

In Table 17, we provide hyperparameter space used for Optuna-driven tuning (Akiba et al., 2019). We set the task\_type parameter to “GPU” (the tuning was unacceptably slow on CPU).

Evaluation. We set the task\_type parameter to “CPU”, since for the used version of the CatBoost library it is crucial for performance in terms of target metrics.

## F.5 SNN

Implementation. Ours, see the source code.

In Table 18, we provide hyperparameter space used for Optuna-driven tuning (Akiba et al., 2019).

## F.6 NODE

Implementation. We used the official implementation: https://github.com/Qwicen/node.

Table 17: CatBoost hyperparameter space. Here (A) = {CA, AD, HE, JA, HI} and (B) = {EP, YE, CO, YA, MI}

<table><tr><td>Parameter</td><td>(Datasets) Distribution</td></tr><tr><td>Max depth</td><td>(A) UniformInt[3, 10], (B) UniformInt[6, 10]</td></tr><tr><td>Learning rate</td><td>(A,B) LogUniform[1e-5, 1]</td></tr><tr><td>Bagging temperature</td><td>(A,B) Uniform[0, 1]</td></tr><tr><td>L2 leaf reg</td><td>(A,B) LogUniform[1, 10]</td></tr><tr><td>Leaf estimation iterations</td><td>(A,B) UniformInt[1, 10]</td></tr><tr><td># Iterations</td><td>100</td></tr></table>

Table 18: SNN hyperparameter space. Here (A) = {CA, AD, HE, JA, HI, AL} and (B) = {EP, YE, CO, YA, MI}

<table><tr><td>Parameter</td><td>(Datasets) Distribution</td></tr><tr><td># Layers</td><td>(A) UniformInt[2, 16], (B) UniformInt[2, 32]</td></tr><tr><td>Layer size</td><td>(A) UniformInt[1, 512], (B) UniformInt[1, 1024]</td></tr><tr><td>Dropout</td><td>(A,B) {0, Uniform[0, 0.1]}</td></tr><tr><td>Learning rate</td><td>(A,B) LogUniform[1e-5, 1e-2]</td></tr><tr><td>Weight decay</td><td>(A,B) {0, LogUniform[1e-5, 1e-3]}</td></tr><tr><td>Category embedding size</td><td>({AD}) UniformInt[64, 512]</td></tr><tr><td># Iterations</td><td>100</td></tr></table>

Tuning. We iterated over the parameter grid from the original paper (Popov et al., 2020) plus the default configuration from the original paper. For multiclass datasets, we set the tree dimension being equal to the number of classes. For the Helena and ALOI datasets there was no tuning since NODE does not scale to classification problems with a large number of classes (for example, the minimal non-default configuration of NODE contains 600M+ parameters on the Helena dataset), so the reported results for these datasets are obtained with the default configuration.

## F.7 TabNet

Implementation. We used the official implementation:

https://github.com/google-research/google-research/tree/master/tabnet. We always set feature-dim equal to output-dim. We also fix and do not tune the following hyperparameters (let A = {CA, AD}, B = {HE, JA, HI, AL}, C = {EP, YE, CO, YA, MI}):

• virtual-batch-size = (A) 2048, (B) 8192, (C) 16384

• batch-size = (A) 256, (B) 512, (C) 1024

In Table 19, we provide hyperparameter space used for Optuna-driven tuning (Akiba et al., 2019).

## F.8 GrowNet

Implementation. We used the official implementation: https://github.com/sbadirli/ GrowNet. Note that it does not support multiclass problems, hence the gaps in the main tables for multiclass problems. We use no more than 40 small MLPs, each MLP has 2 hidden layers, boosting rate is learned – as suggested by the authors.

In Table 20, we provide hyperparameter space used for Optuna-driven tuning (Akiba et al., 2019).

Table 19: TabNet hyperparameter space.

<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td># Decision steps</td><td>UniformInt[3, 10]</td></tr><tr><td>Layer size</td><td>{8, 16, 32, 64, 128}</td></tr><tr><td>Relaxation factor</td><td>Uniform[1, 2]</td></tr><tr><td>Sparsity loss weight</td><td>LogUniform[1e-6, 1e-1]</td></tr><tr><td>Decay rate</td><td>Uniform[0.4, 0.95]</td></tr><tr><td>Decay steps</td><td>{100, 500, 2000}</td></tr><tr><td>Learning rate</td><td>Uniform[1e-3, 1e-2]</td></tr><tr><td># Iterations</td><td>100</td></tr></table>

Table 20: GrowNet hyperparameter space.

<table><tr><td>Parameter</td><td>(Datasets) Distribution</td></tr><tr><td>Correct epochs</td><td>(all) {1, 2}</td></tr><tr><td>Epochs per stage</td><td>(all) {1, 2}</td></tr><tr><td>Hidden dimension</td><td>(all) UniformInt[32, 512]</td></tr><tr><td>Learning rate</td><td>(all) LogUniform[1e-5, 1e-2]</td></tr><tr><td>Weight decay</td><td>(all) {0, LogUniform[1e-6, 1e-3]}</td></tr><tr><td>Category embedding size</td><td>({AD}) UniformInt[32, 512]</td></tr><tr><td># Iterations</td><td>100</td></tr></table>

## F.9 DCN V2

Architecture. There are two variats of DCN V2, namely, “stacked” and “parallel”. We tuned and evaluated both and did not observe strong superiority of any of them. We report numbers for the “parallel” variant as it was slightly better on large datasets.

Implementation. Ours, see the source code.

In Table 21, we provide hyperparameter space used for Optuna-driven tuning (Akiba et al., 2019).

Table 21: DCN V2 hyperparameter space. Here (A) = {CA, AD, HE, JA, HI, AL} and (B) = {EP, YE, CO, YA, MI}

<table><tr><td>Parameter</td><td>(Datasets) Distribution</td></tr><tr><td># Cross layers</td><td>(A) UniformInt[1, 8], (B) UniformInt[1, 16]</td></tr><tr><td># Hidden layers</td><td>(A) UniformInt[1, 8], (B) UniformInt[1, 16]</td></tr><tr><td>Layer size</td><td>(A) UniformInt[64, 512], (B) UniformInt[64, 1024]</td></tr><tr><td>Hidden dropout</td><td>(A,B) Uniform[0, 0.5]</td></tr><tr><td>Cross dropout</td><td>(A,B) {0, Uniform[0, 0.5]}</td></tr><tr><td>Learning rate</td><td>(A,B) LogUniform[1e-5, 1e-2]</td></tr><tr><td>Weight decay</td><td>(A,B) {0, LogUniform[1e-6, 1e-3]}</td></tr><tr><td>Category embedding size</td><td>({AD}) UniformInt[64, 512]</td></tr><tr><td># Iterations</td><td>100</td></tr></table>

## F.10 AutoInt

Implementation. Ours, see the source code. We mostly follow the original paper (Song et al., 2019), however, it turns out to be necessary to introduce some modifications such as normalization in order to make the model competitive. We fix $n _ { h e a d s } = 2$ as recommended in the original paper.

In Table 22, we provide hyperparameter space used for Optuna-driven tuning (Akiba et al., 2019).

Table 22: AutoInt hyperparameter space. Here (A) = {CA, AD, HE, JA, HI} and (B) = {AL, YE, CO, MI}

<table><tr><td>Parameter</td><td>(Datasets) Distribution</td></tr><tr><td># Layers</td><td>(A,B) UniformInt[1, 6]</td></tr><tr><td>Feature embedding size</td><td>(A,B) UniformInt[8, 64]</td></tr><tr><td>Residual dropout</td><td>(A) {0, Uniform[0.0, 0.2]}, (B) Const(0.0)</td></tr><tr><td>Attention dropout</td><td>(A,B) Uniform[0.0, 0.5]</td></tr><tr><td>Learning rate</td><td>(A) LogUniform[1e-5, 1e-3], (B) LogUniform[3e-5, 3e-4]</td></tr><tr><td>Weight decay</td><td>(A,B) LogUniform[1e-6, 1e-3]</td></tr><tr><td># Iterations</td><td>(A) 100, (B) 50</td></tr></table>

## G Analysis

## G.1 When FT-Transformer is better than ResNet?

Data. Train, validation and test set sizes are 500 000, 50 000 and 100 000 respectively. One object is generated as $x \sim \mathcal { N } ( 0 , I _ { 1 0 0 } )$ . For each object, the first 50 features are used for target generation and the remaining 50 features play the role of “noise”.

$f _ { D L }$ . The function is implemented as an MLP with three hidden layers, each of size 256. Weights are initialized with Kaiming initialization (He et al., 2015a), biases are initialized with the uniform distribution $\mathcal { U } ( - a , \ a )$ , where $a = d _ { i n p u t } ^ { - 0 . 5 }$ . All the parameters are fixed after initialization and are not trained.

$f _ { G B D T }$ . The function is implemented as an average prediction of 30 randomly constructed decision trees. The construction of one random decision tree is demonstrated in algorithm 1. The inference process for one decision tree is the same as for ordinary decision trees.

CatBoost. We use the default hyperparameters.

FT-Transformer. We use the default hyperparameters. Parameter count: 930K.

ResNet. Residual block count: 4. Embedding size: 256. Dropout rate inside residual blocks: 0.5. Parameter count: 820K.

## G.2 Ablation study

Table 23 is a more detailed version of the corresponding table from the main text.

Table 23: The results of the comparison between FT-Transformer and two attention-based alternatives. Means and standard deviations over 15 runs are reported

<table><tr><td></td><td>CA ↓</td><td>HE ↑</td><td>JA ↑</td><td>HI ↑</td><td>AL ↑</td><td>YE ↓</td><td>CO ↑</td><td>MI ↓</td></tr><tr><td>AutoInt</td><td> $0.474 \pm 3.3e-3$ </td><td> $0.372 \pm 2.5e-3$ </td><td> $0.721 \pm 2.3e-3$ </td><td> $0.725 \pm 1.7e-3$ </td><td> $0.945 \pm 1.3e-3$ </td><td> $8.882 \pm 3.3e-2$ </td><td> $0.934 \pm 3.5e-3$ </td><td> $0.750 \pm 6.1e-4$ </td></tr><tr><td>FT-Transformer (w/o feature biases)</td><td> $0.470 \pm 5.7e-3$ </td><td> $0.381 \pm 1.6e-3$ </td><td> $0.724 \pm 3.9e-3$ </td><td> $0.727 \pm 1.9e-3$ </td><td> $0.958 \pm 1.2e-3$ </td><td> $8.843 \pm 2.5e-2$ </td><td> $0.964 \pm 6.2e-4$ </td><td> $0.751 \pm 5.6e-4$ </td></tr><tr><td>FT-Transformer</td><td> $0.459 \pm 3.5e-3$ </td><td> $0.391 \pm 1.2e-3$ </td><td> $0.732 \pm 2.0e-3$ </td><td> $0.729 \pm 1.5e-3$ </td><td> $0.960 \pm 1.1e-3$ </td><td> $8.855 \pm 3.1e-2$ </td><td> $0.970 \pm 6.6e-4$ </td><td> $0.746 \pm 4.9e-4$ </td></tr></table>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1: Construction of one random decision tree.

Result: Random Decision Tree
set of leaves $L = \{\text{root}\}$;
depths - mapping from nodes to their depths;
left - mapping from nodes to their left children;
right - mapping from nodes to their right children;
features - mapping from nodes to splitting features;
thresholds - mapping from nodes to splitting thresholds;
values - mapping from leaves to their associated values;
$n = 0$ - number of nodes;
$k = 100$ - number of features;
while $n &lt; 100$ do
    randomly choose leaf $z$ from $L$ s.t. depths[$z$] &lt; 10;
    features[$z$] ~ UniformInt[1, ..., $k$];
    thresholds[$z$] ~ $\mathcal{N}(0, 1)$;
    add two new nodes $l$ and $r$ to $L$;
    remove $z$ from $L$;
    unset values[$z$];
    left[$z$] = $l$;
    right[$z$] = $r$;
    depths[$l$] = depths[$r$] = depths[$z$] + 1;
    values[$l$] ~ $\mathcal{N}(0, 1)$;
    values[$r$] ~ $\mathcal{N}(0, 1)$;
    $n = n + 2$;

end
return Random Decision Tree as {L, left, right, features, thresholds, values}.
</div>

## H Additional datasets

Here, we report results for some datasets that turned out to be non-informative benchmarks, that is, where all models perform similarly. We report the average results over 15 random seeds for single models that are tuned and trained under the same protocol as described in the main text. The datasets include Bank (Moro et al., 2014), Kick <sup>2</sup>, MiniBooNe <sup>3</sup>, Click <sup>4</sup>. The dataset properties are given in Table 24 and the results are reported in Table 25.

Table 24: Additional datasets

<table><tr><td>Dataset</td><td># objects</td><td># Num</td><td># Cat</td><td>Task type (metric)</td></tr><tr><td>Bank</td><td>45211</td><td>7</td><td>9</td><td>Binclass (accuracy)</td></tr><tr><td>Kick</td><td>72983</td><td>14</td><td>18</td><td>Binclass (accuracy)</td></tr><tr><td>MiniBooNe</td><td>130064</td><td>50</td><td>0</td><td>Binclass (accuracy)</td></tr><tr><td>Click</td><td>1000000</td><td>3</td><td>8</td><td>Binclass (accuracy)</td></tr></table>

Table 25: Results for single models on additional datasets.

<table><tr><td></td><td>Bank</td><td>Kick</td><td>MiniBooNE</td><td>Click</td></tr><tr><td>SNN</td><td>0.9076 (0.0016)</td><td>0.9014 (0.0007)</td><td>0.9493 (0.0006)</td><td>0.6613 (0.0006)</td></tr><tr><td>Grownet</td><td>0.9093 (0.0012)</td><td>0.9016 (0.0006)</td><td>0.9494 (0.0007)</td><td>0.6614 (0.0009)</td></tr><tr><td>DCNv2</td><td>0.9085 (0.0010)</td><td>0.9014 (0.0007)</td><td>0.9496 (0.0005)</td><td>0.6615 (0.0003)</td></tr><tr><td>AutoInt</td><td>0.9065 (0.0014)</td><td>0.9005 (0.0005)</td><td>0.9478 (0.0008)</td><td>0.6614 (0.0005)</td></tr><tr><td>MLP</td><td>0.9059 (0.0014)</td><td>0.9012 (0.0004)</td><td>0.9501 (0.0006)</td><td>0.6617 (0.0006)</td></tr><tr><td>ResNet</td><td>0.9072 (0.0014)</td><td>0.9017 (0.0005)</td><td>0.9508 (0.0006)</td><td>0.6612 (0.0007)</td></tr><tr><td>FT-Transformer</td><td>0.9090 (0.0014)</td><td>0.9016 (0.0003)</td><td>0.9491 (0.0007)</td><td>0.6606 (0.0009)</td></tr><tr><td>FT-Transformer (default)</td><td>0.9088 (0.0013)</td><td>0.9013 (0.0006)</td><td>0.9476 (0.0007)</td><td>0.6610 (0.0007)</td></tr><tr><td>CatBoost</td><td>0.9068 (0.0015)</td><td>0.9021 (0.0009)</td><td>0.9465 (0.0005)</td><td>0.6635 (0.0002)</td></tr><tr><td>XgBoost</td><td>0.9087 (0.0009)</td><td>0.9034 (0.0003)</td><td>0.9461 (0.0005)</td><td>0.6399 (0.0006)</td></tr></table>