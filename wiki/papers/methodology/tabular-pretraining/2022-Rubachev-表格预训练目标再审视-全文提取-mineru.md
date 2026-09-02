# Revisiting Pretraining Objectives for Tabular Deep Learning

Ivan Rubachevα,β Artem Alekberovα,β Yury Gorishniy Artem Babenkoα αYandex βHSE University

## Abstract

Recent deep learning models for tabular data currently compete with the traditional ML models based on decision trees (GBDT). Unlike GBDT, deep models can additionally benefit from pretraining, which is a workhorse of DL for vision and NLP. For tabular problems, several pretraining methods were proposed, but it is not entirely clear if pretraining provides consistent noticeable improvements and what method should be used, since the methods are often not compared to each other or comparison is limited to the simplest MLP architectures.

In this work, we aim to identify the best practices to pretrain tabular DL models that can be universally applied to different datasets and architectures. Among our findings, we show that using the object target labels during the pretraining stage is beneficial for the downstream performance and advocate several targetaware pretraining objectives. Overall, our experiments demonstrate that properly performed pretraining significantly increases the performance of tabular DL models, which often leads to their superiority over GBDTs.

## 1 Introduction

Tabular problems are ubiquitous in industrial ML applications, which include data described by a set of heterogeneous features, such as learning-to-rank, click-through rate prediction, credit scoring, and many others. Despite the current dominance of deep learning models in the ML literature, for tabular problems, the “old-school” decision tree ensembles (e.g., GBDT) are often the top choice for practitioners. Only recently, several works have proposed the deep models that challenge the supremacy of GBDT in the tabular domain [2, 15, 37, 14] and suggest that the question “tabular DL or GBDT” is yet to be answered.

An important advantage of deep models over GBDT is that they can potentially achieve higher performance via pretraining their parameters with a properly designed objective. These pretrained parameters, then, serve as a better than random initialization for subsequent finetuning for downstream tasks. For computer vision and NLP domains, pretraining is a de facto standard and is shown to be necessary for the state-of-the-art performance [18, 10]. For tabular problems, however, such a consensus is yet to be achieved as well as the best practices of tabular pretraining are to be established. In particular, pretraining for tabular problems is typically performed directly on the downstream target datasets, unlike pretraining in vision or NLP problems, for which huge “extra” data is available on the Internet. While a large number of prior works addresses the pretraining of tabular DL models [42, 4, 39, 9], it is challenging to make reliable conclusions about pretraining efficacy in tabular DL from the literature since experimental setups vary significantly. Some evaluation protocols assume the unlabeled data is abundant but use a small subset of labels from each dataset during finetuning for evaluation – demonstrating pretraining efficacy, but somewhat limiting the performance of supervised baselines.

By contrast, in our work, we focus on the setup with fully labeled tabular datasets to understand if pretraining helps tabular DL in a fully supervised setting and compare pretraining methods to the strong supervised baselines. To this end, we perform a systematic experimental evaluation of several pretraining objectives, identify the superior ones, and describe the practical details of how to perform tabular pretraining optimally. Our main findings, which are important for practitioners, are summarized below:

• Pretraining provides substantial gains over well-tuned supervised baselines in the fully supervised setup.

• Simple self-prediction based pretraining objectives are comparable to the objective based on contrastive learning. To the best of our knowledge, this was not reported before in tabular DL.

• The object labels can be exploited for more effective pretraining. In particular, we describe several “target-aware” objectives and demonstrate their superiority over their “unsupervised” counterparts.

• The pretraining provides the most noticeable improvements for the vanilla MLP architecture. In particular, their performance after pretraining becomes comparable to the state-of-the-art models trained from scratch, which is important for practitioners, who are interested in simple and efficient solutions.

• The ensembling of pretrained models is beneficial. It indicates that the pretraining stage does not significantly decrease the diversity of the models, despite the fact that all the models are initialized by the same set of parameters.

Overall, our work provides a set of recipes for practitioners interested in tabular pretraining, which results in higher performance for most of the tasks. The code of our experiments is available online.

## 2 Related Work

Here we briefly review the lines of research that are relevant to our study.

Status Quo in tabular deep learning. A plethora of recent works have proposed a large number of deep models for tabular data [25, 32, 2, 38, 41, 3, 17, 20, 37, 15, 27]. Several systematic studies, however, reveal that these models typically do not consistently outperform the decision tree ensembles, such as GBDT (Gradient Boosting Decision Tree) [7, 33, 22], which are typically the topchoice in various ML competitions [15, 35]. Additionally, several works have shown that the existing sophisticated architectures are not consistently superior to properly tuned simple models, such as MLP and ResNet [15, 21]. Finally, the recent work [14] has highlighted that the appropriate embeddings of numerical features in the high-dimensional space are universally beneficial for different architectures. In our work, we experiment with pretraining of both traditional MLP-like models and advanced embedding-based models proposed in [14].

Pretraining in deep learning. For domains with structured data, like natural images or texts, pretraining is currently an established stage in the typical pipelines, which leads to higher general performance and better model robustness [18, 10]. Pretraining with the auto-encoding objective was also previously studied as a regularization strategy helping in the optimization process [12, 11] without large scale pretraining datasets. During the last years, several families of successful pretraining methods have been developed. An impactful line of research on pretraining is based on the paradigm of contrastive learning, which effectively enforces the invariance of the learned representations to the human-specified augmentations [8, 19]. Another line of methods exploits the idea of self-prediction, i.e., these methods require the model to predict certain parts of the input given the remaining parts [18, 10]. In the vision community, the self-prediction based methods are shown to be superior to the methods that use contrastive learning objectives [18]. In our experiments, we demonstrate that self-prediction based objectives are comparable to the contrastive learning ones on tabular data, while being much simpler.

Pretraining for the tabular domain. Numerous pretraining methods were recently proposed in several recent works on tabular DL [2, 42, 9, 39, 37, 27]. However, most of these works do not focus on the pretraining objective per se and typically introduce it as a component of their tabular DL pipeline. Moreover, the experimental setup varies significantly between methods. Therefore, it is difficult to extract conclusive evidence about pretraining effectiveness from the literature. To the best of our knowledge, there is only one systematic study on the tabular pretraining [4], but its experimental evaluation is performed only with the simplest MLP models, and we found that the superiority of the contrastive pretraining, reported in [4], does not hold for tuned models in our setup, where contrastive objective is comparable to the simpler self-prediction objectives.

## 3 Revisiting pretraining objectives

In this section, we evaluate the typical pretraining objectives under the unified experimental setup on the number of datasets from the literature on tabular DL. Our goal is to answer whether pretraining generally provides significant improvements in downstream task performance over tuned models trained from scratch and to identify the pretraining objectives that lead to the best downstream task performance.

## 3.1 Experimental setup

We mostly follow the experimental setup from [16] and describe its main details here for completeness.

Notation. Each tabular dataset is represented by a set of pairs $\{ ( x _ { i } , y _ { i } ) \} _ { i = 1 } ^ { n } ,$ where $\begin{array} { r l } { x _ { i } } & { { } = } \end{array}$ $( x _ { i } ^ { 1 } , \ldots , x _ { i } ^ { m } ) \in \mathbb { X }$ are the objects features (both numerical and categorical) and $y _ { i } ~ \in ~ \mathbb { Y }$ is the target variable. The downstream task is either regression $\mathbb { Y } = \mathbb { R }$ or classification $\mathbb { Y } = \{ 1 , \ldots , k \}$ Each model has the backbone $f ( x | \theta )$ that is followed by two separate heads: a pretraining head $h ( z | \mu )$ and a downstream task head $g ( z | \lambda )$ , with learnable parameters $\theta , \mu ,$ λ respectively, and $z = f ( x | \theta )$ denotes the output of the backbone for an input object x.

Datasets. We evaluate the pretraining methods on a curated set of eleven middle to large scale datasets used in prior literature on tabular deep learning. The benchmark is biased towards tasks, where tuned $\mathrm { { \bf { M L P } } }$ models were shown to be inferior to GBDT [16] since we aim to understand if pretraining can help the deep models to beat the “shallow” ones. The datasets represent a diverse set of tabular data problems with classification and regression targets. The main dataset properties are summarized in Table 1.

Table 1: Datasets used for the experiments
<table><tr><td>Abbr</td><td>Name</td><td># Train</td><td># Validation</td><td># Test</td><td># Num</td><td># Cat</td><td>Task type</td><td>Batch size</td></tr><tr><td>GE</td><td>Gesture Phase</td><td>6318</td><td>1580</td><td>1975</td><td>32</td><td>0</td><td>Multiclass</td><td>128</td></tr><tr><td>CH</td><td>Churn Modelling</td><td>6400</td><td>1600</td><td>2000</td><td>10</td><td>1</td><td>Binclass</td><td>128</td></tr><tr><td>CA</td><td>California Housing</td><td>13209</td><td>3303</td><td>4128</td><td>8</td><td>0</td><td>Regression</td><td>128</td></tr><tr><td>HO</td><td>House 16H</td><td>14581</td><td>3646</td><td>4557</td><td>16</td><td>0</td><td>Regression</td><td>128</td></tr><tr><td>AD</td><td>Adult ROC</td><td>26048</td><td>6513</td><td>16281</td><td>6</td><td>8</td><td>Binclass</td><td>256</td></tr><tr><td>OT</td><td>Otto Group Products LogLoss</td><td>39601</td><td>9901</td><td>12376</td><td>93</td><td>0</td><td>Multiclass</td><td>256</td></tr><tr><td>HI</td><td>Higgs Small</td><td>62751</td><td>15688</td><td>19610</td><td>28</td><td>0</td><td>Binclass</td><td>512</td></tr><tr><td>FB</td><td>Facebook Comments Volume</td><td>157638</td><td>19722</td><td>19720</td><td>50</td><td>1</td><td>Regression</td><td>512</td></tr><tr><td>WE</td><td>Shifts Weather (subset)</td><td>296554</td><td>47373</td><td>53172</td><td>123</td><td>0</td><td>Regression</td><td>1024</td></tr><tr><td>CO</td><td>Covertype</td><td>371847</td><td>92962</td><td>116203</td><td>54</td><td>0</td><td>Multiclass</td><td>1024</td></tr><tr><td>MI</td><td>MSLR-WEB10K (Fold 1)</td><td>723412</td><td>235259</td><td>241521</td><td>136</td><td>0</td><td>Regression</td><td>1024</td></tr></table>

We report ROC-AUC for all binary classification datasets, accuracy for multi-class classification datasets and RMSE for regression datasets, with OT being the one exception, where we report log-loss, as it was used as a default metric in the corresponding Kaggle competition. We use the quantiletransform from the Scikit-learn library [31] to preprocess the numerical features for all datasets except OT, where the absence of such transformation was shown to be superior [14]. Additional information about the datasets is provided in Appendix A.

Models. We use MLP as a simple deep baseline to compare and ablate the methods. Our implementation of MLP exactly follows [16], the model is regularized by dropout and weight decay. As more advanced deep models, we evaluate MLP equipped with numerical feature embeddings, specifically, target-aware piecewise linear encoding (MLP-T-LR) and embeddings with periodic activations (MLP-PLR) from [14]. These models represent the current state-of-the-art solution for tabular DL [14], and are of interest as most prior work on pretraining in tabular DL focus on pretraining with the simplest

MLP models in evaluation. The implementation of models with numerical embeddings follows [14]. We use AdamW [28] optimizer, do not use learning rate schedules and fix batch sizes for each dataset based on the dataset size.

Pretraining. Pretraining is always performed directly on the target dataset and does not exploit additional data. The learning process thus comprises two stages. On the first stage, the model parameters are optimized w.r.t. the pretraining objective. On the second stage, the model is initialized with the pretrained weights and finetuned on the downstream classification or regression task. We focus on the fully-supervised setup, i.e., assume that target labels are provided for all dataset objects. Typically, pretraining stage involves the input corruption: for instance, to generate positive pairs in contrastive-like objectives or to corrupt the input for reconstruction in self-prediction based objectives. We use random feature resampling as a proven simple baseline for input corruption in tabular data [4, 42]. Learning rate and weight decay are shared between the two stages (see Table 11 for the ablation). We fix the maximum number of pretraining iterations for each dataset at 100k. On every 10k-th iteration, we compute the value of the pretraining objective using the hold-out validation objects for early-stopping on large-scale WE, CO and MI datasets. On other datasets we directly finetune the current model every 10k-th iteration and perform early-stopping based on the target metric after finetuning (we do not observe much difference between early stopping by loss or by downstream metric, see Table 12).

Hyperparameters & Evaluation. Hyperparameter tuning is crucial for a fair comparison, therefore, we use Optuna [1] to optimize the model and pretraining hyperparameters for each method on each dataset. We use the validation subset of each dataset for hyperparameter tuning. The exact search spaces for the hyperparameters of each method are provided in Appendix B.

We run the tuned configuration of each pretraining method with 15 random seeds and report the average metric on the test splits. When comparing to GBDT, we obtain three ensembles by splitting the fifteen single model predictions into three disjoint subsets of five models and averaging predictions within each subset. Then, we report the average metric over the three ensembles.

## 3.2 Comparing pretraining objectives

Here we compare the contrastive learning and self-prediction objectives from prior work in the described setup. For contrastive learning, we follow the method described in [4]: use InfoNCE loss, consider corrupted inputs xˆ as positives for x and the rest of the batch as negatives. For self-prediction methods, we evaluate two objectives: the first one is the reconstruction of the original x, given the corrupted input xˆ (the reconstruction loss is computed for all columns), the second one is the binary mask prediction, where the objective is to predict the mask vector m indicating the corrupted columns from the corrupted input xˆ. The results of the comparison are in Table 2. We summarize our key findings below.

Contrastive is not superior. Both the reconstruction and the mask prediction objectives are preferable to the contrastive objective. The two self-prediction objectives have the advantage of being conceptually simpler, and easier to implement, while also being less resource-intensive (no need for the second view of augmented examples in each batch, simpler loss function). We thus recommend the self-prediction based objectives as a practical solution for pretraining in tabular DL.

Pretraining is beneficial for the state-of-the-art models. Models with the numerical feature embeddings also benefit from pretraining with either reconstruction or mask prediction demonstrating the top performance on the downstream task. However, the improvement is typically less noticeable compared to the vanilla MLPs.

There is no universal solution between self-prediction objectives. We observe that for some datasets the reconstruction objective outperforms the mask prediction (OT, WE, CO, MI), while on others the mask prediction is better (GE, CH, HI, AD). We also note that the mask prediction objective sometimes leads to unexpected performance drops for models with numerical embeddings (WE, MI), we do not observe significant performance drops for the reconstruction objective.

The main takeaway: simple pretraining strategies based on self-prediction lead to significant improvements in the downstream accuracy compared to the tuned supervised baselines learned from scratch across different tabular DL models and datasets. In practice, we recommend trying both reconstruction and mask prediction as tabular pretraining baselines, as either one might show superior performance depending on the dataset being used.

Table 2: Results for pretraining deep models with different objectives. We report metrics averaged over 15 seeds, bold entries correspond to results that are statistically significantly better (we use Tukey HSD test). The comparisons are separate for different models. ↑ corresponds to accuracy and ROC-AUC metrics, ↓ corresponds to RMSE and log-loss for OT. "no pretraining" stands for the supervised baseline, initialized with random weights
<table><tr><td>CH↑ CA↓ HO↓OT↓</td><td>GE↑</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>HI↑ FB↓ AD↑ WE↓ CO↑ MI↓</td></tr><tr><td colspan="10">MLP</td></tr><tr><td>no pretraining 0.635 0.849 0.506 3.156 0.479 0.801 5.737 0.908 1.909 0.963</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.749</td></tr><tr><td>contrastive</td><td></td><td></td><td>0.672 0.855 0.455 3.056 0.469</td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.813 5.697 0.910 1.881 0.960</td><td>0.748</td></tr><tr><td>rec</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.662 0.853 0.445 3.044 0.466 0.805 5.641 0.910 1.875 0.965 0.746</td></tr><tr><td>mask</td><td></td><td></td><td>0.691 0.857 0.454 3.113 0.472 0.814 5.681 0.912 1.883</td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.964</td><td>0.748</td></tr><tr><td colspan="10">MLP-PLR no pretraining 0.668 0.858 0.469 3.008 0.483 0.809 5.608 0.926 1.890 0.969</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>rec</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.746 0.667 0.852 0.439 3.031 0.472 0.808 5.571 0.926 1.877 0.971 0.745</td></tr><tr><td>mask</td><td>0.685 0.863 0.434 3.007 0.477 0.818 5.586 0.927 1.911 0.970</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.748</td></tr><tr><td colspan="10">MLP-T-LR</td></tr><tr><td>no pretraining 0.634 0.866 0.444 3.113 0.482 0.805 5.520 0.925 1.897 0.968</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>rec</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.749 0.652 0.857 0.424 3.109 0.472 0.808 5.363 0.924 1.861 0.969 0.746</td></tr><tr><td>mask</td><td>0.654 0.868 0.424 3.045 0.472 0.818 5.544</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.926 1.916 0.969</td><td>0.748</td></tr></table>

## 4 Target-aware pretraining objectives

In this section, we show that exploiting the target variables during the pretraining stage can further increase the downstream performance. Specifically, we evaluate several strategies to leverage information about targets during pretraining, identify the best ones and compare them to GBDT. Below we describe a list of target-aware pretraining objectives that we investigate.

Supervised loss with augmentations. A straightforward way to incorporate the target variable into the pretraining is by using the input corruption as an augmentation for the standard supervised learning objective. An important difference of this baseline in our setup to the one in [4] is that we treat learning on corrupted samples as a pretraining stage and finetune the entire model on the full uncorrupted dataset afterwards (we ablate this in subsection 5.3).

Supervised loss with augmentations + self-prediction. We evaluate a natural extension to the above baseline: a combination of the supervised objective with the unsupervised self-prediction. Note, that during the pretraining stage both losses are calculated on corrupted inputs, while the finetuning is performed on the non-corrupted dataset. For the self-prediction objectives we evaluate both the reconstruction and the mask prediction. We use different prediction heads for supervised and self-prediction objectives. We sum supervised and self-prediction losses with equal weights.

Target-aware pretraining. An alternative to the approaches described above is the modification of the pretraining task itself. An example of this approach is supervised contrastive learning [24], where the target variable is used to sample positive and negative examples. We introduce the target variable into the self-prediction based objectives with two modifications.

First, we condition the mask prediction or the reconstruction head on the original input’s target by concatenating the hidden representation from the backbone network $z = f ( { \hat { x } } )$ with the target variable representation before passing it to the pretraining head to obtain predictions $p = h ( \mathsf { c o n c a t } [ z , y ] )$ For classification datasets we encode y with one-hot-encoding, for regression targets we use the standard scaling.

Second, we change the input corruption scheme by sampling the replacement from the feature target conditional distribution where a target is different to the original. Intuitively, corrupting the input object x in the direction of the target different to the original makes the pretraining task more correlated with the downstream target prediction. Concretely, given an object-target pair $( x _ { i } , y _ { i } )$ , we sample a new target $\hat { y } _ { i }$ from a uniform distribution over the set $\mathbf { \bar { \{ } }  y \mid y \neq y _ { i } \mathbf  \bar { \} } ^ { 1 }$ , then each feature $x ^ { j }$ is replaced with a sample from the $p ( x ^ { j } | \hat { y } _ { i } )$ distribution, instead of $p ( x ^ { j } )$

Table 3: Variations of the target-aware pretraining schemes. Notation follows Table 2. Bold results indicate statistically significant winners across all models and methods. "+ target" denotes targetconditioned pretraining, "+ sup" denotes auxiliary supervised head.
<table><tr><td></td><td>GE↑</td><td>CH↑</td><td>CA ↓</td><td>HO ↓</td><td>OT ↓</td><td>HI↑</td><td>FB ↓</td><td>AD ↑</td><td>WE ↓</td><td>CO ↑</td><td>MI↓</td><td> Avg. Rank</td></tr><tr><td colspan="13">MLP</td></tr><tr><td>no pretraining</td><td>0.635</td><td>0.849</td><td>0.506</td><td>3.156</td><td>0.479</td><td>0.801</td><td>5.737</td><td>0.908</td><td>1.909</td><td>0.963</td><td>0.749</td><td>5.5 ± 1.4</td></tr><tr><td>mask</td><td>0.691</td><td>0.857</td><td>0.454 0.445</td><td>3.113 3.044</td><td>0.472</td><td>0.814</td><td>5.681</td><td>0.912</td><td>1.883</td><td>0.964 0.965</td><td>0.748</td><td>3.8 ± 1.4</td></tr><tr><td>rec</td><td>0.662</td><td>0.853</td><td>0.441</td><td>3.077</td><td>0.466</td><td>0.805</td><td>5.641</td><td>0.910</td><td>1.875</td><td></td><td>0.746</td><td> $3 . 6 \pm 1 . 5$ </td></tr><tr><td>sup</td><td>0.693</td><td>0.856</td><td></td><td></td><td>0.459</td><td>0.814</td><td>5.689</td><td>0.914</td><td>1.883</td><td>0.968</td><td>0.748</td><td>3.0 ± 1.0</td></tr><tr><td>mask + target</td><td>0.683</td><td>0.857</td><td>0.434</td><td>3.056</td><td>0.468</td><td>0.819</td><td>5.633</td><td>0.914</td><td>1.876</td><td>0.965</td><td>0.748</td><td>2.9 ± 1.3</td></tr><tr><td>rec + target</td><td>0.659</td><td>0.853</td><td>0.454</td><td>3.044 3.099 0.458</td><td>0.463</td><td>0.806</td><td>5.636</td><td>0.909</td><td>1.884</td><td>0.965</td><td>0.745</td><td>3.7 ± 1.9</td></tr><tr><td>mask + sup</td><td>0.693</td><td>0.857</td><td>0.436</td><td></td><td></td><td>0.817</td><td>5.685</td><td>0.915</td><td>1.873</td><td>0.967</td><td>0.748</td><td>2.7 ± 1.2</td></tr><tr><td>rec + sup</td><td>0.684</td><td>0.854</td><td>0.436</td><td></td><td>3.012 0.456 MLP-PLR</td><td>0.815</td><td>5.672</td><td>0.911</td><td>1.862</td><td>0.967</td><td>0.747</td><td>2.6 ± 1.5</td></tr><tr><td colspan="9"></td><td>1.890</td><td>0.969</td><td>0.746</td><td>3.5 ± 1.7</td></tr><tr><td>no pretraining mask rec sup</td><td>0.668 0.685 0.667 0.710</td><td>0.858 0.863 0.852 0.859</td><td>0.469 0.434 0.439 0.433</td><td>3.008 3.007 3.031 3.136</td><td>0.483 0.477 0.472 0.479</td><td>0.809 0.818 0.808 0.811</td><td>5.608 5.586 5.571 5.521</td><td>0.926 0.927 0.926 0.924</td><td>1.911 1.877 1.873</td><td>0.970 0.971 0.971</td><td>0.748 0.745 0.748</td><td>2.8 ± 1.7 2.6 ± 1.2</td></tr><tr><td>mask + target rec + target</td><td>0.694 0.688</td><td>0.862 0.860</td><td>0.425 0.445</td><td>3.023 3.064</td><td>0.474 0.475</td><td>0.821 0.812</td><td>5.537 5.507</td><td>0.929 0.927</td><td>1.911 1.887</td><td>0.969 0.971</td><td>0.749 0.748</td><td>2.5 ± 1.2 2.5 ± 1.9 2.7 ± 1.3</td></tr><tr><td>mask + sup rec + sup</td><td>0.711 0.709</td><td>0.866 0.858</td><td>0.441 0.433 3.059</td><td>3.129</td><td>0.480 0.465</td><td>0.813 0.807</td><td>5.480 5.571</td><td>0.925 0.927 1.865 0.971 0.745</td><td>1.875</td><td>0.969</td><td>0.745</td><td> $2 . 5 \pm 1 . 4$ </td></tr><tr><td></td><td></td><td></td><td></td><td></td><td>MLP-T-LR</td><td></td><td></td><td></td><td></td><td></td><td></td><td> $1 . 9 \pm 1 . 2$ </td></tr><tr><td colspan="9"></td><td></td><td></td><td></td><td></td></tr><tr><td>no pretraining mask 0.652</td><td>0.654</td><td>0.634 0.866 0.444 0.868 0.424 3.045 0.857</td><td></td><td>3.113</td><td>0.482 0.472</td><td>0.805 0.818</td><td>5.520 5.544</td><td>0.925 0.926</td><td>1.897 1.916</td><td>0.968 0.969</td><td>0.749 0.748</td><td>3.9 ± 1.7</td></tr><tr><td</table>

## 4.1 Comparing target-aware objectives

Here we compare the strategies of incorporating the target variable into pretraining. The results of the comparison are in Table 3. Our key findings are formulated below.

Supervised loss with augmentations is another strong baseline for MLP. Pretraining with the supervised loss on corrupted data consistently improves over supervised training from scratch for the MLP. This objective is a strong baseline along with the self-prediction based objectives. However, for models with numerical embeddings the supervised objective with corruptions is less consistent and sometimes is inferior to training from scratch, thus for these models we recommend the self-prediction objectives alone as baselines.

Target-aware objectives demonstrate the best performance. Both the supervised loss with selfprediction and modified self-prediction objectives improve over the unsupervised pretraining baselines across datasets and model architectures.

For the objective with the combination of supervised and self-prediction losses the variation with the reconstruction loss is the most consistent across models and dataset with no performance drops below the pretraining-free baseline. The variant with mask prediction shows similar performance and stability for the MLP, but is not as good as reconstruction for models with numerical embeddings.

For the target-aware self-prediction objectives, the modified mask prediction delivers significant improvements over its unsupervised counterpart. Modified reconstruction objective, however, does not improve over unsupervised reconstruction objective.

Main takeaways: Target-aware objectives help further increase the downstream performance, improving upon their unsupervised counterparts. For the reconstruction based self-prediction baseline the addition of the supervised loss is most beneficial ("rec + sup" from Table 3), for the mask prediction objective it’s target-aware modification provides more improvements $( " \mathrm { m a s k } + \mathrm { t a r g e t } ^ { \prime \prime }$ from Table 3). A simple MLP model pretrained with those "target-aware" objectives often reaches or surpasses complex models with numerical embeddings trained from scratch. In practice, we recommend first trying the baseline pretraining objectives ("rec", "mask", "sup" from Table 3), choosing the suitable baseline for the dataset and improving it accordingly: supervised loss for the reconstruction and target-aware modification for the mask prediction.

## 4.2 Comparison to GBDT

Here we compare MLPs and MLPs with numerical feature embeddings pretrained with the supervised loss with reconstruction and the target-aware mask prediction objectives to the GBDTs. Table 4 shows the results of the comparison.

Table 4: Comparison of pretrained models to GBDT. Notation follows Table 2. Results represent ensembles of models. Bold entries correspond to the overall statistically significant best entries.
<table><tr><td></td><td>GE↑</td><td>CH↑</td><td>CA↓</td><td>HO ↓</td><td></td><td>OT ↓</td><td>HI↑</td><td>FB ↓</td><td>AD ↑</td><td>WE↓</td><td>CO ↑</td><td></td><td>MI ↓ | Avg. Rank</td></tr><tr><td>CatBoost</td><td>0.692</td><td>0.864</td><td></td><td>0.430</td><td>3.093</td><td>0.450</td><td>0.807</td><td>5.226</td><td>0.928</td><td>1.801</td><td>0.967</td><td>0.741</td><td> $2 . 6 \pm 1 . 4$ </td></tr><tr><td>XGBoost</td><td>0.683</td><td>0.860</td><td></td><td>0.434</td><td>3.152</td><td>0.454</td><td>0.805</td><td>5.338</td><td>0.927</td><td>1.782</td><td>0.969</td><td>0.742</td><td> $3 . 0 \pm 1 . 5$ </td></tr><tr><td colspan="10">MLP</td><td></td><td></td><td></td><td></td></tr><tr><td>no pretraining</td><td>0.656</td><td>0.852</td><td></td><td>0.482 3.055</td><td></td><td>0.467</td><td>0.805</td><td>5.666</td><td>0.910 1.850</td><td></td><td>0.968</td><td>0.747</td><td> $4 . 8 \pm 1 . 1$ </td></tr><tr><td>mask + target</td><td>0.709</td><td>0.860</td><td>0.414</td><td>2.949</td><td></td><td>0.457</td><td>0.828</td><td>5.551</td><td>0.916</td><td>1.809</td><td>0.969</td><td>0.746</td><td> $2 . 8 \pm 1 . 2$ </td></tr><tr><td>rec + sup</td><td>0.709</td><td>0.859</td><td></td><td>0.419 2.951</td><td></td><td>0.442</td><td>0.817</td><td>5.531</td><td>0.913</td><td>1.801</td><td>0.973</td><td>0.745</td><td> $2 . 5 \pm 1 . 2$ </td></tr><tr><td colspan="10">MLP-P-LR</td><td colspan="7"></td></tr><tr><td>no pretraining</td><td>0.695 0.864 0.454 2.953</td><td></td><td></td><td></td><td></td><td>0.470</td><td>0.814</td><td>5.324 0.928</td><td></td><td> 1.835 0.974 0.744</td><td></td><td></td><td></td><td> $2 . 6 \pm 1 . 2$ </td></tr><tr><td>mask + target</td><td>0.719 0.866 0.407</td><td></td><td></td><td></td><td>2.952</td><td>0.458</td><td>0.828</td><td></td><td></td><td>5.373 0.930 1.849</td><td></td><td>0.973 0.745</td><td></td><td> $2 . 1 \pm 1 . 2$ </td></tr><tr><td>rec + sup</td><td>0.737 0.862</td><td></td><td></td><td>0.424</td><td>2.964</td><td>0.449</td><td>0.811</td><td></td><td>5.124 0.929</td><td>1.813</td><td></td><td></td><td>0.974 0.744</td><td> $2 . 0 \pm 1 . 0$ </td></tr><tr><td colspan="10">MLP-T-LR</td><td colspan="7"></td></tr><tr><td>no pretraining</td><td></td><td>0.662 0.868 0.437</td><td></td><td></td><td>3.028</td><td> 0.472</td><td>0.808</td><td>5.424</td><td>0.927</td><td></td><td>1.850</td><td>0.972</td><td>0.747</td><td> $3 . 7 \pm 1 . 1$ </td></tr><tr><td>mask + target</td><td>0.673 0.868 0.410 2.894 0.460</td><td></td><td></td><td></td><td></td><td></td><td>0.827</td><td>5.458</td><td>0.930</td><td>1.849</td><td></td><td>0.972 0.746</td><td></td><td> $2 . 4 \pm 1 . 4$ </td></tr><tr><td> $\mathrm { r e c } + \mathrm { s u p }$ </td><td>0.705</td><td>0.866 0.425</td><td></td><td></td><td>3.057</td><td>0.444</td><td>0.814</td><td>5.422</td><td>0.927</td><td>1.811</td><td></td><td></td><td>0.974 0.746</td><td> $2 . 5 \pm 1 . 1$ </td></tr></table>

In this section, we provide a possible explanation of why the incorporation of the target variable into pretraining can lead to better downstream task performance. We do this through the experiments on the controllable synthetic data. Here we describe the properties and the generation process of the data and our observations on the differences of the pretraining schemes.

We observe that both pretraining with target aware objectives and using numerical feature embeddings consistently improve the performance of the simple MLP backbone. In particular, MLP coupled with target aware pretraining starts to outperform GBDT on 4 datasets (GE, CA, OT, HI). Combined with numerical feature embeddings, pretraining improves MLP performance further, making it superior to GBDT on the majority of the datasets, with two exceptions in WE and MI.

## 5 Analysis

## 5.1 Investigating the properties of pretrained models

<!-- image-->  
Figure 1: The decodability of object feature from the intermediate representations computed by the pretrained models and the models trained from scratch. The pretrained models decently capture the information about all the features, while the randomly initialized models capture the most informative features and suppress the others.

We follow the synthetics generation protocol described in [16] with a modification that allows for the manual control of the feature importance for the particular prediction task. Concretely, we generate the objects features $\left\{ x _ { i } \right\} _ { i = 1 } ^ { n }$ as samples from the multivariate Gaussian distribution with zero mean and covariance matrix Σ with identical diagonal and a constant $c = 0 . 5$ everywhere else. To generate the corresponding objects targets $\{ y _ { i } \} _ { i = 1 } ^ { n }$ we sample a vector $p \in \mathbb { R } ^ { m }$ from the Dirichlet distribution $p \sim \operatorname { D i r } ( 1 _ { m } )$ and let p define the influence of the objects features on the target. Then, we build an ensemble of 10 random oblivious decision trees $\left\{ T _ { i } ( x ) \right\} _ { i = 1 } ^ { 1 0 }$ of depth 10, where on each tree level we sample a feature $j \sim \operatorname { C a t } ( p )$ and a threshold $t \sim \operatorname { U n i f } ( \operatorname* { m i n } ( x ^ { j } )$ , max(xj )) for a decision rule. For each tree leaf, we sample a scalar $l \sim \mathcal { N } ( 0 , 1 )$ , representing a logit in binary classification. We define the binary targets as follows: $\begin{array} { r } { y ( x ) = \operatorname { I } \left\{ { \frac { 1 } { 1 0 } } \sum _ { i = 1 } ^ { 1 0 } T _ { i } ( x ) > 0 \right\} } \end{array}$

Intuitively if a particular feature is often used for splitting in the nodes of a decision tree, it would have more influence on the target variable. Indeed, we find the feature importances2 correlate well with the predefined vector p. We set the size of the dataset $n = 5 0 . 0 0 0$ and the number of features $m = 8$ and generate 50 datasets with different feature importance vectors p for the analysis.

For each generated dataset, we then check whether the finetuned models capture the information about object features in their intermediate representations. Specifically, we train an MLP to predict the value of the i-th object feature given the frozen embeddings produced by a finetuned network initialized from (a) random initialization, (b) mask prediction pretraining, (c) target-aware mask prediction pretraining. The separate MLP is used for each feature and the RMSE learning objective is used. Then we report the RMSE on the test set for all features i ∈ [0, m] along with their importance rank in the dataset on Figure 1. Here, the lower ranks correspond to the more important features.

Figure 1 reveals that the target-aware pretraining enables the model to capture more information about the informative features compared to the “unsupervised” pretraining and, especially, to the learning from scratch. The latter one successfully captures the most informative feature from the training data, while suppressing the less important, but still significant features. We conjecture that this is the source of superiority of the target-aware pretraining.

## 5.2 Efficient ensembling

In this section we show, that it is possible to construct ensembles from one pretraining checkpoint (pretrained with the target conditioned mask prediction objective). To this end, we run finetuning with 15 different random seeds starting from the one pretrained checkpoint. Table 5 shows the results.

Both ensembling the models from a shared pretrain checkpoint and ensembling multiple independent pretraining runs produces strong ensembles, which shows that it is sufficient to pretrain once and create ensembles by several independent finetuning processes. This is important in practice since

Table 5: Efficient ensembling for MLP mask + target
<table><tr><td>GE ↑ CH↑CA↓HO↓</td><td></td><td></td><td></td><td>OT ↓</td><td>HI↑</td><td></td><td>FB↓AD↑WE↓</td><td></td><td></td><td>CO ↑MI↓</td></tr><tr><td>single</td><td>0.683 0.857</td><td>0.434</td><td>3.056</td><td></td><td>0.468</td><td>0.819</td><td>5.633</td><td>0.914</td><td>1.876</td><td>0.965 0.748</td></tr><tr><td>standard ensemble</td><td>0.709 0.860</td><td>0.414</td><td>2.949</td><td></td><td>0.457</td><td>0.828</td><td>5.551</td><td>0.916 1.809</td><td></td><td>0.969 0.746</td></tr><tr><td>efficient ensemble</td><td>0.702 0.861</td><td>0.411</td><td>2.967 0.461</td><td></td><td></td><td>0.825 5.590</td><td></td><td>0.917 1.820</td><td>0.969</td><td>0.746</td></tr></table>

finetuninig is typically cheaper (i.e. requires fewer iterations), and still is able to produce diverse models from the one pretraining checkpoint for ensembles of comparable quality.

## 5.3 On importance of finetuning on clean data

Here we show, that the second stage of finetuning the model on the entire dataset without input corruption is often necessary for the best downstream performance. To this end we compare finetuning the models on clean data with using models right after pretraining for two objectives: supervised loss and supervised loss with the reconstruction objective.

Table 6: Finetuning MLP on clean data versus using the model trained on corrupted inputs only
<table><tr><td>GE↑ CH↑ CA↓HO↓ OT↓ HI↑ FB↓ AD↑ WE↓ CO↑ MI↓</td></tr><tr><td>0.635 0.849 0.506 3.156 0.479 0.801 5.737 0.908 1.909 0.963 0.749</td></tr><tr><td>no pretraining</td></tr><tr><td>sup 0.693 0.856 0.441 3.077 0.459 0.814 5.689 0.914 1.883 0.968 0.748 0.674 0.853 0.464 3.251 0.461 0.808 6.167 0.910 1.938 0.958 0.752</td></tr><tr><td>sup I no finetune rec + sup 0.684 0.854 0.436 3.012 0.456 0.815 5.672 0.911 1.862 0.967 0.747</td></tr></table>

Across all datasets for both methods finetuning on uncorrupted data with the supervised loss proves to be essential for the best performance. Sometimes excluding the second finetuning stage degrades the performance below the tuned supervised baseline of training from scratch.

## 5.4 Does pretraining require more compute?

In this section we investigate how much more time is spent on pretraining, compared to training the models from scratch. We run pretraining with "rec + sup" objective with 50k, 100k and 150k pretraining iterations thresholds (early-stopping, in theory, could make 100k and more iterations equivalent to the 50k, but in practice it was not the case). We report downstream performance along with average time spent to pretrain and finetune a model in Table 7.

Table 7: Comparison of time spent for MLP training from scratch and "rec + sup" pretraining with 50k, 100k and 150k max-iterations threshold. Second row in each group reports average time spent training one model in seconds on an A100 GPU.
<table><tr><td>GE↑ CH↑ CA↓ HO↓ OT↓ HI↑ FB↓ AD↑ WE↓ CO↑ MI↓</td></tr><tr><td>no pretraining 0.635 0.849 0.506 3.156 0.479 0.801 5.737 0.908 1.909 0.963 0.749</td></tr><tr><td>29s 10s 25s 26s 38s 29s 159s 12s 57s 352s 211s</td></tr><tr><td>rec + sup | 50k 0.679 0.857 0.441 3.064 0.462 0.813 5.650 0.910 1.879 0.966 0.747 327s 227s 280s 277s 355s 256s 624s 403s 242s 593s 292s</td></tr><tr><td>rec + sup | 100k 0.684 0.854 0.436 3.012 0.456 0.815 5.672 ( 0.911 1.862 0.967 0.747</td></tr><tr><td>661s 312s 533s 455s 570s 526s 740s 759s 439s 649s 472s rec + sup | 150k 0.692 0.859 0.435 3.012 0.456 0.816 5.629 0.910 1.866 0.968 0.746</td></tr></table>

Pretraining often requires by an order of magnitude more compute, it is especially apparent on smaller scale datasets like GE, CH, CA, HO, OT, HI, AD. However, the absolute time spent on pretraining is

still acceptable, as the original training from scratch takes seconds on small datasets. Generally the more iterations you use for pretraining, the better downstream quality you get.

## 6 Conclusion

In this work, we have systematically evaluated typical pretraining objectives for tabular deep learning. We have revealed several important recipes for optimal pretraining performance that can be universally beneficial across various problems and models. Our findings confirm that pretraining can significantly improve the performance of tabular deep models and provide additional evidence that tabular DL can become a strong alternative to GBDT.

## References

[1] Takuya Akiba, Shotaro Sano, Toshihiko Yanase, Takeru Ohta, and Masanori Koyama. Optuna: A next-generation hyperparameter optimization framework. In KDD, 2019. 4

[2] Sercan O. Arik and Tomas Pfister. Tabnet: Attentive interpretable tabular learning. arXiv, 1908.07442v5, 2020. 1, 2

[3] Sarkhan Badirli, Xuanqing Liu, Zhengming Xing, Avradeep Bhowmik, Khoa Doan, and Sathiya S. Keerthi. Gradient boosting neural networks: Grownet. arXiv, 2002.07971v2, 2020. 2

[4] Dara Bahri, Heinrich Jiang, Yi Tay, and Donald Metzler. Scarf: Self-supervised contrastive learning using random feature corruption. In International Conference on Learning Representations, 2022. 1, 3, 4, 5

[5] P. Baldi, P. Sadowski, and D. Whiteson. Searching for exotic particles in high-energy physics with deep learning. Nature Communications, 5, 2014. 13

[6] Jock A. Blackard and Denis J. Dean. Comparative accuracies of artificial neural networks and discriminant analysis in predicting forest cover types from cartographic variables. Computers and Electronics in Agriculture, 24(3):131–151, 2000. 13

[7] Tianqi Chen and Carlos Guestrin. Xgboost: A scalable tree boosting system. In SIGKDD, 2016. 2

[8] Ting Chen, Simon Kornblith, Mohammad Norouzi, and Geoffrey Hinton. A simple framework for contrastive learning of visual representations. In International conference on machine learning, pages 1597–1607. PMLR, 2020. 2

[9] Sajad Darabi, Shayan Fazeli, Ali Pazoki, Sriram Sankararaman, and Majid Sarrafzadeh. Contrastive mixup: Self-and semi-supervised learning for tabular domain. arXiv preprint arXiv:2108.12296, 2021. 1, 2

[10] Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. Bert: Pre-training of deep bidirectional transformers for language understanding. arXiv, 1810.04805v2, 2019. 1, 2

[11] Alaaeldin El-Nouby, Gautier Izacard, Hugo Touvron, Ivan Laptev, Hervé Jegou, and Edouard Grave. Are large-scale datasets necessary for self-supervised pre-training? arXiv preprint arXiv:2112.10740, 2021. 2

[12] Dumitru Erhan, Yoshua Bengio, Aaron Courville, Pierre-Antoine Manzagol, Pascal Vincent, and Samy Bengio. Why does unsupervised pre-training help deep learning? J. Mach. Learn. Res., 11:625–660, mar 2010. 2

[13] David Freedman and Persi Diaconis. On the histogram as a density estimator:l 2 theory. Z. Wahrscheinlichkeitstheorie verw Gebiete, 57(4):453–476, December 1981. 6

[14] Yura Gorishniy, Ivan Rubachev, and Artem Babenko. On embeddings for numerical features in tabular deep learning. arXiv preprint arXiv:2203.05556, 2022. 1, 2, 3, 4

[15] Yury Gorishniy, Ivan Rubachev, Valentin Khrulkov, and Artem Babenko. Revisiting deep learning models for tabular data. In NeurIPS, 2021. 1, 2

[16] Yury Gorishniy, Ivan Rubachev, Valentin Khrulkov, and Artem Babenko. Revisiting deep learning models for tabular data. Advances in Neural Information Processing Systems, 34, 2021. 3, 8

[17] Hussein Hazimeh, Natalia Ponomareva, Petros Mol, Zhenyu Tan, and Rahul Mazumder. The tree ensemble layer: Differentiability meets conditional computation. In ICML, 2020. 2

[18] Kaiming He, Xinlei Chen, Saining Xie, Yanghao Li, Piotr Dollár, and Ross Girshick. Masked autoencoders are scalable vision learners. arXiv preprint arXiv:2111.06377, 2021. 1, 2

[19] Kaiming He, Haoqi Fan, Yuxin Wu, Saining Xie, and Ross Girshick. Momentum contrast for unsupervised visual representation learning. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 9729–9738, 2020. 2

[20] Xin Huang, Ashish Khetan, Milan Cvitkovic, and Zohar Karnin. Tabtransformer: Tabular data modeling using contextual embeddings. arXiv, 2012.06678v1, 2020. 2

[21] Arlind Kadra, Marius Lindauer, Frank Hutter, and Josif Grabocka. Well-tuned simple nets excel on tabular datasets. In NeurIPS, 2021. 2

[22] Guolin Ke, Qi Meng, Thomas Finley, Taifeng Wang, Wei Chen, Weidong Ma, Qiwei Ye, and Tie-Yan Liu. Lightgbm: A highly efficient gradient boosting decision tree. Advances in neural information processing systems, 30:3146–3154, 2017. 2

[23] R. Kelley Pace and Ronald Barry. Sparse spatial autoregressions. Statistics & Probability Letters, 33(3):291–297, 1997. 13

[24] Prannay Khosla, Piotr Teterwak, Chen Wang, Aaron Sarna, Yonglong Tian, Phillip Isola, Aaron Maschinot, Ce Liu, and Dilip Krishnan. Supervised contrastive learning. Advances in Neural Information Processing Systems, 33:18661–18673, 2020. 5

[25] Günter Klambauer, Thomas Unterthiner, Andreas Mayr, and Sepp Hochreiter. Self-normalizing neural networks. In NIPS, 2017. 2

[26] Ron Kohavi. Scaling up the accuracy of naive-bayes classifiers: a decision-tree hybrid. In KDD, 1996. 13

[27] Jannik Kossen, Neil Band, Clare Lyle, Aidan N. Gomez, Tom Rainforth, and Yarin Gal. Selfattention between datapoints: Going beyond individual input-output pairs in deep learning. In NeurIPS, 2021. 2

[28] Ilya Loshchilov and Frank Hutter. Decoupled weight decay regularization. In ICLR, 2019. 4

[29] Renata C. B. Madeo, Clodoaldo Ap. M. Lima, and Sarajane Marques Peres. Gesture unit segmentation using support vector machines: segmenting gestures from rest positions. In Proceedings of the 28th Annual ACM Symposium on Applied Computing, SAC, 2013. 13

[30] Andrey Malinin, Neil Band, German Chesnokov, Yarin Gal, Mark John Francis Gales, Alexey Noskov, Andrey Ploskonosov, Liudmila Prokhorenkova, Ivan Provilkov, Vatsal Raina, Vyas Raina, Mariya Shmatova, Panos Tigas, and Boris Yangel. Shifts: A dataset of real distributional shift across multiple large-scale tasks. ArXiv, abs/2107.07455, 2021. 13

[31] F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, M. Blondel, P. Prettenhofer, R. Weiss, V. Dubourg, J. Vanderplas, A. Passos, D. Cournapeau, M. Brucher, M. Perrot, and E. Duchesnay. Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12:2825–2830, 2011. 3

[32] Sergei Popov, Stanislav Morozov, and Artem Babenko. Neural oblivious decision ensembles for deep learning on tabular data. In ICLR, 2020. 2

[33] Liudmila Prokhorenkova, Gleb Gusev, Aleksandr Vorobev, Anna Veronika Dorogush, and Andrey Gulin. Catboost: unbiased boosting with categorical features. In NeurIPS, 2018. 2

[34] Tao Qin and Tie-Yan Liu. Introducing LETOR 4.0 datasets. arXiv, 1306.2597v1, 2013. 13

[35] Ravid Shwartz-Ziv and Amitai Armon. Tabular data: Deep learning is not all you need. arXiv, 2106.03253v1, 2021. 2

[36] Kamaljot Singh, Ranjeet Kaur Sandhu, and Dinesh Kumar. Comment volume prediction using neural networks and decision trees. In IEEE UKSim-AMSS 17th International Conference on Computer Modelling and Simulation, UKSim, 2015. 13

[37] Gowthami Somepalli, Micah Goldblum, Avi Schwarzschild, C. Bayan Bruss, and Tom Goldstein. SAINT: improved neural networks for tabular data via row attention and contrastive pre-training. arXiv, 2106.01342v1, 2021. 1, 2

[38] Weiping Song, Chence Shi, Zhiping Xiao, Zhijian Duan, Yewen Xu, Ming Zhang, and Jian Tang. Autoint: Automatic feature interaction learning via self-attentive neural networks. In CIKM, 2019. 2

[39] Talip Ucar, Ehsan Hajiramezanali, and Lindsay Edwards. Subtab: Subsetting features of tabular data for self-supervised representation learning. Advances in Neural Information Processing Systems, 34, 2021. 1, 2

[40] Joaquin Vanschoren, Jan N. van Rijn, Bernd Bischl, and Luís Torgo. Openml: networked science in machine learning. arXiv, 1407.7722v1, 2014. 13

[41] Ruoxi Wang, Bin Fu, Gang Fu, and Mingliang Wang. Deep & cross network for ad click predictions. In ADKDD, 2017. 2

[42] Jinsung Yoon, Yao Zhang, James Jordon, and Mihaela van der Schaar. Vime: Extending the success of self- and semi-supervised learning to tabular domain. In NeurIPS, 2020. 1, 2, 4

## A Datasets

We used the following datasets:

• Gesture Phase Prediction ([29])

• Churn Modeling3

• California Housing (real estate data, [23])

• House 16H4

• Adult (income estimation, [26])

• Otto Group Product Classification5

• Higgs (simulated physical particles, [5]; we use the version with 98K samples available at the OpenML repository [40])

• Facebook Comments ([36])

• Covertype (forest characteristics, [6])

• Microsoft (search queries, [34]). We follow the pointwise approach to learning-to-rank and treat this ranking problem as a regression problem.

• Weather (temperature, [30]). We take 10% of the dataset for our experiments due to the its large size.

## B Hyperparameters

## B.1 CatBoost

We fix and do not tune the following hyperparameters:

• early-stopping-rounds = 50

• od-pval = 0.001

• iterations = 2000

For tuning on the MI and CO datasets, we set the task_type parameter to “GPU”. In all other cases (including the evaluation on these two datasets), we set this parameter to “CPU”.

Table 8: CatBoost hyperparameter space

<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td>Max depth</td><td>UniformInt[1, 10]</td></tr><tr><td>Learning rate</td><td>LogUniform[0.001, 1]</td></tr><tr><td>Bagging temperature</td><td>Uniform[0, 1]</td></tr><tr><td>L2 leaf reg</td><td>LogUniform[1, 10]</td></tr><tr><td>Leaf estimation iterations UniformInt[1, 10]</td><td></td></tr><tr><td># Iterations</td><td>100</td></tr></table>

## B.2 XGBoost

We fix and do not tune the following hyperparameters:

• booster = "gbtree"

• early-stopping-rounds = 50

• n-estimators = 2000

Table 9: XGBoost hyperparameter space.
<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td>Max depth</td><td>UniformInt[3, 10]</td></tr><tr><td>Min child weight</td><td>LogUniform[0.0001, 100]</td></tr><tr><td>Subsample</td><td>Uniform[0.5, 1]</td></tr><tr><td>Learning rate</td><td>LogUniform[0.001, 1]</td></tr><tr><td>Col sample by tree</td><td>Uniform[0.5, 1]</td></tr><tr><td>Gamma</td><td>{0, LogUniform[0.001, 100]}</td></tr><tr><td>Lambda</td><td>{0, LogUniform[0.1, 10]}</td></tr><tr><td># Iterations</td><td>100</td></tr></table>

## B.3 MLP

We fix and do not tune the following hyperparameters:

• Layer size = 512

• Head hidden size = 512

Table 10: MLP hyperparameter space.
<table><tr><td>Parameter</td><td>Distribution</td></tr><tr><td># Layers</td><td>UniformInt[1, 8]</td></tr><tr><td>Dropout</td><td>{0, Uniform[0, 0.5]}</td></tr><tr><td>Learning rate</td><td>LogUniform[5e-5, 0.005]</td></tr><tr><td>Weight decay</td><td>{0, LogUniform[1e-6, 1e-3]}</td></tr><tr><td>Corrupt Probability</td><td>{0, Uniform[0.2, 0.8]}</td></tr><tr><td># Iterations</td><td>100</td></tr></table>

## B.4 Embedding Hyperparameters

We fix and do not tune the following hyperparameters:

• Layer size = 512

• Head hidden size = 512

The distribution for the output dimensions of linear layers is UniformInt[1, 128].

PLR, T-LR. We share the same hyperparameter space for models with embeddings across all datasets.

For the target-aware embeddings (tree-based) T-LR, the distribution for the number of leaves is UniformInt[2, 256], the distribution for the minimum number of items per leaf is UniformInt[1, 128] and the distribution for the minimum information gain required for making a split is LogUniform[1e-9, 0.01].

For the periodic embeddings PLR. The distribution for k is UniformInt[1, 128], the distribution for the σ parameter is LogUniform[0.01, 100]

## C Share or split learning rate and weight decay between pretraining and finetuning?

Here we demonstrate that tuning and using the same learning rate and weight decay for both pretraining and finetuning results in similar performance to tuning these parameters separately for the

two stages. We opt for sharing the learning rate and weight decay for pretraining and finetuning in all the experiments in the paper.

Table 11: Results for single models with MLP mask + target pretraining
<table><tr><td></td><td>GE ↑</td><td>CH↑</td><td>CA ↓</td><td>HO ↓</td><td>OT ↓</td><td>HI↑</td><td>FB ↓</td><td>AD ↑</td><td>WE↓</td><td>CO ↑</td><td>MI ↓</td></tr><tr><td>shared wd  $/ s h a r e e d \mid \pi \mid \alpha \mid 6 8 8 3 s _ { 1 } + \pi = 2 0 . 8 5 7 + 2 e s = 0 . 4 3 4 + \pi = 3  . 0 5 6 + \alpha = 2 . 0 4 6 8 + 2 e s = 0 . 8 1 9 + 2 e s = 5 . 6 6 3 3 + \alpha = 2 . 0 9 1 + \alpha = 3 . 1 . 8 7 6 - \alpha = 0 . 9 6 5 + \pi = 0 . 7 4 8 s + \alpha = 6 . 0 9 1 + \pi = 0 . 0 9 1 + \alpha = 3 . 1 . 0 7 7 + 2 e s = 0 . 4 9 1 + \pi = 0 . 0 9 1 + \alpha = 3 . 1 . 0 7 7 + 2 e s = 0 . 4 9 1 + \pi = 0 . 2 0 7 + \alpha = 3 . 1 . 0 7 7 + 2 e s = 0 . 4 9 1 + \pi = 0 . 2 0 7 + \alpha = 3 . 2 4 . 7 5 + 2 e s = 0 . 4 4 + \pi = 0 . 2 4 8 e s$ </td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>shared wd / split lr</td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.97±0.857±3e30.431±7e33.032±3e0.469±230.819±2e35.647±0.915±9e41.934±830.964±9e40.748±4</td><td></td><td></td><td></td><td></td></tr><tr><td>split wd / split lr</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.688±0.856±3e30.430±3.046±e0.471±3e-0.821±745.734±e0.914±7e4.891±630.964±1e30.748±e4</td><td></td></tr><tr><td>split wd / split lr</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.694±1e0.858±2e30.431±63.066±e0.468±20.821±2e35.632±40.914±1e31.878±430.966±1e30.748±3e4</td><td></td></tr></table>

## D Early-stopping criterions

Here we demonstrate that early stopping the pretraining by the value of the pretraining objective on the hold-out validation set is comparable to the early stopping by the downstream metric on the hold-out validation set after finetuning. See Table 12 for the results. This is an important practical observation, as computing pretraining objective is much faster than the full finetuning of the model, especially on large scale datasets.

Table 12: Results for single models with MLP mask + target pretraining
<table><tr><td>GE↑ CH↑ CA↓HO↓ OT↓ HI↑ FB↓ AD↑</td></tr><tr><td>finetune early stop 0.683 0.857 0.434 3.056 0.468 0.819 5.633 0.914 pretrain early stop 0.674 0.855 0.434 3.031 0.469 0.818 5.738 0.914</td></tr></table>

## E Extended Tables With Experimental Results

The scores with standard deviations for single models and ensembles are provided in 13 and 14 respectively.

<table><tr><td rowspan=2 colspan=2>no pretraining  0.61790090994mask           0.691108168109194rec             0.±1±040161910±1964</td></tr><tr><td rowspan=1 colspan=1>mask</td></tr><tr><td rowspan=1 colspan=1>rec</td><td rowspan=1 colspan=1>2±1.0e-</td></tr><tr><td rowspan=1 colspan=2>sup             0.6104409816899194</td></tr><tr><td rowspan=1 colspan=2>supcon         0.64100060911964mask + sup     0.809980091±709684rec + sup       0.68401009110.964</td></tr><tr><td rowspan=1 colspan=2>mask + target   0.08089±1091769644</td></tr><tr><td rowspan=1 colspan=2>rec + target     0.9041019098964</td></tr><tr><td rowspan=1 colspan=2>001064</td></tr></table>

<table><tr><td rowspan="3">no pretraining mask rec sup</td><td>0.9019099094 0.880008099110904</td></tr><tr><td>0.790980914</td></tr><tr><td>0710±±479011192974 0.71.19±19994</td></tr><tr><td>mask + sup rec + sup</td><td>079±.1090719974 0.0099</td></tr><tr><td>mask + target rec + target</td><td>a0 0.600009894 a04</td></tr></table>

<table><tr><td rowspan=1 colspan=1>no pretraining  0.64±6009994mask           0.04081921984</td></tr><tr><td rowspan=1 colspan=1>rec             0.61090910994sup             0.6±011000990.914mask + sup     0.678099901094rec + sup       0.678±701090904</td></tr><tr><td rowspan=1 colspan=1>mask + target   0690099400</td></tr><tr><td rowspan=1 colspan=1>rec + target     0.1019099.4a0</td></tr></table>

<table><tr><td></td><td>0.0.0670910019</td></tr><tr><td>no pretraining mask</td><td>0.70178091±810.96</td></tr><tr><td></td><td></td></tr><tr><td>rec</td><td>0.679±1960171091109</td></tr><tr><td>contrastive sup</td><td>0.78910691964 0.7780116091897</td></tr><tr><td>supcon</td><td>0.8016109179±919705</td></tr><tr><td>mask + sup</td><td>0.719080618191601910974</td></tr><tr><td>rec + sup</td><td>0.7999518911974</td></tr><tr><td>mask + target</td><td>0.7090191910999</td></tr><tr><td></td><td>a100</td></tr><tr><td>rec + target</td><td>0.67789191094</td></tr><tr><td></td><td></td></tr></table>

<table><tr><td>no pretraining mask</td><td>0.6190191974 00.86192790097</td></tr></table>

<table><tr><td>no pretraining mask rec</td><td>0.01109009 0.791193010100.9094</td></tr><tr><td></td><td>0.±6101901±09109210094</td></tr><tr><td>sup</td><td>0.68109109909±</td></tr><tr><td>mask + sup 0.61008±00909</td><td>0.709110974</td></tr><tr><td>rec + sup</td><td></td></tr><tr><td>mask + target 0.6710.81010.809049094</td><td></td></tr><tr><td>4 rec + target</td><td>090109094 a1</td></tr></table>