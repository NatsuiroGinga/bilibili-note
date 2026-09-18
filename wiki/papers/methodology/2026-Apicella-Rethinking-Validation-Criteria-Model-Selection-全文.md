---
title: "2026-Apicella-Rethinking-Validation-Criteria-Model-Selection"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2026-Apicella-Rethinking-Validation-Criteria-Model-Selection.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Don’t stop me now: Rethinking Validation Criteria for Model Parameter Selection

Andrea Apicella<sup>2†</sup>, Francesco Isgr\`o<sup>1†</sup>, Andrea Pollastro<sup>1†</sup>, Roberto Prevete<sup>1†</sup>

<sup>1</sup>Department of Electrical Engineering and Information Technology, University of Naples Federico II, Via Claudio 21, Naples, 80125, Italy. <sup>2</sup>Department of Information Engineering, Electrical Engineering, and Applied Mathematics (DIEM), University of Salerno, Via Giovanni Paolo II, 132, Fisciano (Salerno), 84084, Italy.

Contributing authors: andapicella@unisa.it; francesco.isgro@unina.it; andrea.pollastro@unina.it; roberto.prevete@unina.it; <sup>†</sup>These authors contributed equally to this work.

## Abstract

Despite the extensive literature on training loss functions, the evaluation of generalization on the validation set remains underexplored. In this work, we conduct a systematic empirical and statistical study of how the validation criterion used for model selection afects test performance in neural classifiers, with attention to early stopping. Using fully connected networks on standard benchmarks under k-fold evaluation, we compare: (i) early stopping with patience and (ii) post-hoc selection over all epochs (i.e. no early stopping). Models are trained with crossentropy, C-Loss, or PolyLoss; the model parameter selection on the validation set is made using accuracy or one of the three loss functions, each considered independently. Three main findings emerge. (1) Early stopping based on validation accuracy performs worst, consistently selecting checkpoints with lower test accuracy than both loss-based early stopping and post-hoc selection. (2) Loss-based validation criteria yield comparable and more stable test accuracy. (3) Across datasets and folds, any single validation rule often underperforms the test-optimal checkpoint. Overall, the selected model typically achieves test-set performance statistically lower than the best performance across all epochs, regardless of the validation criterion. Our results suggest avoiding validation accuracy (in particular with early stopping) for parameter selection, favoring loss-based validation criteria.

Keywords: Machine Learning, evaluation, data split, Deep Learning, AI

## 1 Introduction

In neural network models, training and evaluation typically follow an iterative procedure — except in specific architectures such as radial basis function networks — in which each iteration corresponds to an epoch, up to a predefined maximum number of epochs. At each epoch, model parameters are updated on a designated training set through an update rule, usually driven by the gradient of a diferentiable loss function, such as cross-entropy in classification problems. Since each epoch yields a distinct parameter configuration, a separate validation set is commonly employed to estimate the model’s generalization capability and to identify the parameter setting expected to generalize best. After training and model parameter selection, the chosen model is finally evaluated on a fully unseen test set using a task-dependent metric, for example accuracy for balanced classification, F1 score under class imbalance, or AUROC for ranking tasks. This paradigm is standard in supervised learning and underlies most modern experimental protocols [1].

In practice, rather than running a fixed number of training epochs, it is common to adopt an early stopping procedure [2], whereby training is halted once performance on the validation set ceases to improve according to a predefined criterion. Early stopping can be viewed primarily as a computationally convenient trade-of between performance and training cost, as it avoids evaluating all possible intermediate models generated during training. From this perspective, overfitting is not prevented by prematurely interrupting optimization per se, but by selecting the model instance that maximizes an estimate of generalization. Importantly, the efectiveness of this selection process depends on the criterion used to assess generalization on the validation set.

Despite the widespread use of validation-based selection, the criterion adopted to evaluate generalization is not uniquely specified. While the choice of the training loss is typically guided by optimization and statistical considerations, and the test metric is dictated by the deployment objective, the validation criterion occupies an intermediate role that is not clearly tied to either parameter optimization or final evaluation. As a result, diferent criteria are often adopted in practice, largely by convention. This ambiguity is particularly evident in classification problems. Model parameters are commonly optimized by minimizing the cross-entropy loss, which arises from maximum likelihood estimation and provides a principled surrogate for learning conditional class probabilities. Final performance, however, is often assessed using accuracy or other decision-based metrics that depend on an explicit prediction rule and directly reflect deployment-level objectives. Consequently, improvements in the training or validation loss do not necessarily translate into improvements in the evaluation metric of interest, giving rise to the well-known loss–metric mismatch [3].

Motivated by this mismatch, a substantial body of work has explored alternative diferentiable loss functions designed to better align optimization with accuracyoriented objectives. Notable examples include the C-Loss proposed by [4], which targets classification error through a continuous surrogate, and PolyLoss [5], which generalizes cross-entropy by incorporating higher-order polynomial terms. Despite these developments, cross-entropy remains the dominant optimization objective in practice, and model parameter selection on the validation set is still most commonly performed using either validation loss or validation accuracy.

As a consequence, diferent choices of performance metric on the validation set induce diferent orderings over the set of candidate models. In classification tasks, this raises a fundamental question: should generalization be estimated using a probabilistic criterion such as cross-entropy, which evaluates the quality of predicted class probabilities, or using a decision-based metric such as accuracy, which directly reflects classification performance? These criteria correspond to distinct notions of risk and need not agree in practice, nor coincide with the model that maximizes test-set accuracy. This choice becomes even more consequential under early stopping: the monitored validation metric not only ranks checkpoints but also determines when training halts and which model parameters are actually chosen. As a consequence, misalignment between the monitored metric and the task objective can therefore terminate training prematurely around a suboptimal local minimum and lock in an inferior model.

While it is well understood that generalization can be improved through explicit regularization techniques—such as weight decay, data augmentation, or dropout—as well as through implicit mechanisms including early stopping itself [6, 7], our analysis addresses a distinct but related question. Rather than modifying the learning process to induce better generalization, we examine how diferent validation criteria estimate generalization for the purpose of model parameter selection.

Motivated by these considerations, this work investigates the practical and statistical implications of using validation cross-entropy versus validation accuracy, as well as alternative accuracy-aligned loss functions, as criteria for selecting models aimed at maximizing test-set accuracy. Through a systematic empirical analysis on standard supervised benchmarks under a k-fold cross-validation protocol, we assess the extent to which diferent validation criteria lead to statistically meaningful diferences in test performance.

We consider cross-entropy, C-Loss [4], and PolyLoss [5] as optimization objectives on the training set. On the validation set, generalization is evaluated using all corresponding losses as well as accuracy, and model parameter selection is performed both within a patience-based early-stopping scheme and by selecting the best-performing model across all training epochs. To explore diferent generalization regimes under controlled conditions, and following the theoretical insights of Advani et al. [8], we employ fully connected neural networks with a single hidden layer. This controlled architectural setting allows us to study model selection behavior while limiting confounding factors introduced by depth and complex optimization dynamics. Further details are provided in Section 4.2. Experiments were conducted on multiple benchmark datasets from the UCI Machine Learning Repository [9].

From our experiments, the following main findings emerge: 1) When accuracy is used as the criterion to evaluate generalization on the validation set, we consistently observe the lowest test-set performance relative to the best achievable accuracy, regardless of the loss function used during training. This efect is particularly pronounced under early stopping, where accuracy-based validation leads to a poorer alignment with test-optimal performance compared to loss-based criteria, highlighting the instability of accuracy-based as a stopping criteria. 2) In contrast, when C-Loss, PolyLoss, or standard cross-entropy are used as validation criteria, the resulting test-set performance is comparable across methods, and remains largely independent of the loss function employed during training. 3) Overall, irrespective of the validation criterion, statistical testing indicates that the selected model achieves significantly lower test performance than the test-optimal model in the majority of cases. In summary, this work makes the following contributions: (i) a systematic and statistically grounded experimental analysis of how diferent validation criteria—including cross-entropy, C-Loss, PolyLoss, and accuracy—afect model selection and test-set generalization; (ii) a quantitative assessment of the loss–metric mismatch in validation-based model parameter selection with and without early stopping; (iii) practical implications for selecting validation criteria in accuracy-based classification tasks. The remainder of the paper is organized as follows. Section 3 introduces notation, the evaluation criteria and experimental protocol; Section 4 presents datasets, models, and evaluation procedures; Section 5 reports the results discussing implications and limitations; and Section 6 concludes the work with final remarks.

## 2 Related Work

In supervised learning, models are trained on labeled data belonging to a given task, with the aim to achieve high values of a task performance measure [10]. However, in several tasks the target metric is often non-diferentiable (e.g., accuracy, F1) or yields flat/unstable gradients for gradient-based optimization. Consequently, training relies on diferentiable surrogate losses (e.g., cross-entropy) that act as proxies for the task metric. However, minimizing the training loss does not guarantee improvements in the deployment evaluation metric (loss–metric mismatch, [3]). Motivated by this gap, several works design losses that more closely reflect the task objectives: for example, the C-loss based on cross-correntropy as a surrogate to the 0-1 risk [11, 12], or probabilistic performance indices that jointly reward correctness, high probability for the true class, and low probability for the others [13], or score-oriented losses that target confusion-matrix summaries [14, 15].

Other works introduced task- and data-adaptive loss functions (e.g., PolyLoss [5]), defining parametric families in which standard objectives, such as cross-entropy, arise as special cases. Regardless of the training objective, generalization is ultimately assessed on held-out data (validation/test). While the test set is usually evaluated using the efective task-specific metric, the criterion used on the validation set can sufer from the same loss-metric mismatch: selecting checkpoints, i.e., the epoch corresponding to the model parameters to be selected, by a surrogate such as cross-entropy may fail to identify the model that maximizes the task-specic metric (e.g., accuracy).

This observation underlies methods that explicitly couple training objectives with validation feedback [3] and motivates a careful choice of validation criteria for model selection.

Furthermore, when models are evaluated iteratively on a validation set, it is common to use early stopping to truncate optimization before convergence [2]. It was shown that stopping early can yield solutions comparable to those of smaller, optimally sized models [16], and consistency results are available under specific assumptions [17]. The benefit of early stopping depends on the loss and the geometry of the optimization landscape: studies of loss surfaces and representation dynamics highlight plateaus, saddle points, overconfidence, and how regularization shapes hidden-layer encodings [18–21]. Classical analyses investigated overtraining dynamics for linear networks under quadratic loss and characterized validation-based stopping both geometrically and in time [22–24], while statistical views related early stopping to explicit regularization [6, 7].

It is interesting to notice that optimal–stopping efects appear beyond artificial neural networks, notably in boosting methods [25–28], and SVMs [29], which helps explain the widespread use of early stopping. More in general, stopping rules can be applied either on training data or on a held-out validation set [30]. Training-monitored criteria include, for example, a log-sensitivity index for rare outcomes [31] and rules driven by training-loss trajectories [32]; protocol-centric choices around how the hold-out split is constructed have also been explored [33]. However, some early procedures relied solely on training-set criteria or repeatedly re-sampled “validation” from the training pool [34, 35], practices that can bias selection and inflate performance estimates [36]. Validation-monitored rules span comparative studies and benchmarks of families and combinations [37–39], as well as practical heuristics such as fixed validation-error thresholds [40] or marginal-improvement criteria [41].

In particular, PACMAN [42] provides generalization bounds that explicitly account for the discrepancy between cross-entropy and accuracy, while other works address the loss–metric mismatch through adaptive loss design [3] or empirical analyses of generalization behavior [43]. However, these approaches do not directly examine the implications of this mismatch for validation-based model selection. In contrast, our work focuses on the statistical efectiveness of model selection procedures driven by validation criteria, explicitly comparing validation-selected models against the testoptimal model under controlled experimental settings.

In summary, prior work highlights three themes that motivate our study: (i) models are trained with surrogate losses that may not align with task metrics; (ii) validation criteria inherit this mismatch and thus critically determine which checkpoint is selected; and (iii) early stopping is often used to avoid running all epochs, so the validation signal efectively chooses the model instance among the per-epoch checkpoints—making the choice of validation metric especially important. Our study addresses these themes by comparing validation accuracy with three loss-based validation criteria (cross-entropy, C-loss, and PolyLoss) within a unified experimental protocol.

## 3 Method

## 3.1 Notation

In this work, we adopt the following notation. In supervised machine learning, a dataset $D \in { \mathcal { D } }$ consists of N input–label pairs

$$
D = \{(\mathbf {x} ^ {(i)}, y ^ {(i)}) \} _ {i = 1} ^ {N},
$$

where $\mathbf { x } ^ { ( i ) }$ denotes an input instance and $\boldsymbol y ^ { ( i ) }$ the corresponding ground-truth value. The set D denotes the collection of all possible datasets for the task under consideration.

We denote by Train, $V a l , T e s t \ \in \ \mathcal { D }$ the training, validation, and test sets, respectively.

We focus on a classification setting in which each input $\mathbf { x } ^ { ( i ) }$ is assigned to one of K mutually exclusive classes $\{ 1 , 2 , \ldots , K \}$ . For simplicity and without loss of generality, labels are treated as one-dimensional discrete values, i.e.,

$$
y ^ {(i)} \in \{1, 2, \dots , K \}.
$$

Given a model $M ( \theta )$ with parameters θ and a dataset $D \in { \mathcal { D } }$ , let

$$
\ell : \mathcal {D} \times \{1, \dots , E \} \rightarrow \mathbb {R} \quad \text { and } \quad a: \mathcal {D} \times \{1, \dots , E \} \rightarrow [ 0, 1 ]
$$

denote the loss and accuracy functions of the model at iteration e of a training procedure composed of $E \in \mathbb N$ epochs. That is, $\ell ( D , e )$ and $\alpha ( D , e )$ represent, respectively, the loss and the accuracy computed on dataset D at epoch e.

For a given dataset $D \in { \mathcal { D } }$ , define the optimal loss and accuracy values as

$$
L _ {D} ^ {\star} = \min _ {1 \leq e \leq E} \ell (D, e), \quad A _ {D} ^ {\star} = \max _ {1 \leq e \leq E} a (D, e).
$$

We further define the corresponding optimal epochs as

$$
e _ {\ell , D} ^ {\star} = \arg \min _ {1 \leq e \leq E} \ell (D, e), \qquad e _ {a, D} ^ {\star} = \arg \max _ {1 \leq e \leq E} a (D, e),
$$

i.e., the epochs achieving the minimum loss and maximum accuracy, respectively (see Figure 1).

## 3.2 Post-hoc Checkpoint Selection versus Early Stopping

We can distinguish between two validation-driven protocols that are often not clearly distinguished in the literature: (i) during training, a validation-based criterion is monitored and, once it fails, training is halted and the best checkpoint seen so far is retained. This is usually known as early stopping; (ii) training proceeds for a fixed number of epochs, after which the checkpoint with the best validation score among all saved models is selected. Here we refer to this as post-hoc checkpoint selection. Within an early stopping protocol, training is terminated according to a predefined empirical criterion. A commonly adopted strategy is early stopping with patience $T _ { \cdot }$ , whereby training halts at the first epoch such that no improvement in the validation loss has been observed for $T$ consecutive epochs. Formally, this condition is expressed as

![](images/eb13037419d04234a7ee925769802fe624f64310427f6ae4dc6d81cd845c6473.jpg)  
Fig. 1: An example of loss $\ell ( D , e )$ and accuracy $\tau ( D , e )$ across $E$ epochs on a dataset D. Vertical dashed lines mark the epochs achieving the validation-loss minimum $e _ { \ell , D } ^ { \star }$ and the validation-accuracy maximum $e _ { a , D } ^ { \star } ;$ horizontal dotted lines indicate the corresponding values $\begin{array} { r } { L _ { D } ^ { \star } = \operatorname* { m i n } _ { e } \ell ( D , e ) } \end{array}$ (blue) and $A _ { D } ^ { \star } = \operatorname* { m a x } _ { e } a \left( D , e \right)$ (orange).

$$
\exists \hat {e} _ {\ell , V a l}: \forall h \in \{1, 2, \dots , T \}, \quad \ell (V a l, \hat {e} _ {\ell , V a l} + h) \geq \ell (V a l, \hat {e} _ {\ell , V a l}).
$$

The selected model corresponds to the model with loss $\hat { L } _ { V a l } = \ell ( V a l , \hat { e } _ { \ell , V a l } )$

Instead, in post-hoc checkpoint selection the training proceeds for all the fixed E epochs and the model is selected retrospectively as the one at iteration $e _ { \ell , V a l } ^ { \star } =$ $\arg \operatorname* { m i n } _ { 1 \leq e \leq E } \ell ( V a l , e )$ . Figure 2 depicts both procedures, i.e., post-hoc checkpoint selection and early stopping—highlighting.

Note that when $T = E$ , i.e., when the patience parameter equals the total number of epochs, early stopping with patience T results in no early termination and is therefore equivalent to post-hoc checkpoint selection.

## 3.3 Statistical Comparison of Model Selection Criteria

To assess the efect of diferent model selection criteria on generalization performance, we performed a systematic evaluation comparing the test accuracy $A _ { t e s t }$ of models selected in both early stopping and post-hoc protocols, against the best achievable test accuracy observed throughout training. Our empirical analysis focused on supervised classification tasks, where models were trained using the CE loss and evaluated in terms of accuracy.

![](images/37fa1f2c077d6e70fac2b2051243f3de211607aa6a8a3f6a71e7e3969643f29f.jpg)  
Fig. 2: An example comparing early stopping with patience $T$ and post-hoc checkpoint selection on the validation loss $\ell ( \mathrm { V a l } , e )$ . The orange dashed line marks the performance value returned by early stopping (best-so-far at $\boldsymbol { \hat { e } } _ { \ell , \mathrm { V a l } }$ , with training halted at $\hat { e } _ { \ell , \mathrm { V a l } } +$ $T )$ , whereas the blue dashed line marks the best validation performance value $e _ { \ell , \mathrm { V a l } } ^ { \star }$ identified retrospectively. It is evident that the early-stopped checkpoint need not be the best-performing model: it corresponds to a local minimum reached before halting, whereas post-hoc checkpoint selection identifies the global minimum over all epochs.

Our goal was to quantify the extent to which accuracy obtained by validation-based selection, using either the minimum validation loss $L _ { V a l } ^ { \star }$ or the maximum validation accuracy $A _ { V a l } ^ { \star }$ , deviated from the test-optimal accuracy $A _ { T e s t } ^ { \star } ,$ defined as the model instance that attained the highest test accuracy $A _ { T e s t }$ across all training epochs.

In other words, we want to check how much $A _ { T e s t } ^ { \star }$ difers from a $( T e s t , e _ { \ell , V a l } ^ { \star } )$ and C $\mathfrak { i } ( T e s t , e _ { a , V a l } ^ { \star } )$ , and similarly, $a ( T e s t , \hat { e } _ { \ell , V a l } )$ and a $( T e s t , \hat { e } _ { a , V a l } )$ (see Figure 3 for a visual summary).

## 4 Experimental assessment

## 4.1 Datasets

Experiments were conducted on multiple benchmark datasets retrieved from the UCI Machine Learning Repository [9]. The list of the datasets involved in this work is shown in Table 1.

All datasets were preprocessed using a unified and dataset-agnostic pipeline in order to ensure comparability across experiments. Specifically, categorical and binary features were transformed via one-hot encoding, while numerical features were kept in their original form. No dataset-specific feature engineering or optimization was performed. We emphasize that the goal of this preprocessing was not to optimize performance on the individual datasets to reach new state-of-the-art results, but rather to provide a simple and reproducible input representation suitable for large-scale comparative analysis.

<table><tr><td>Name</td><td>Instances</td><td>N. classes</td><td>Name</td><td>Instances</td><td>N. classes</td></tr><tr><td>Pen-Based Recognition of Handwritten Digits</td><td>8409</td><td>10</td><td>Breast Cancer Coimbra</td><td>89</td><td>2</td></tr><tr><td>Page Blocks Classification</td><td>5473</td><td>5</td><td>Maternal Health Risk</td><td>776</td><td>3</td></tr><tr><td>Molecular Biology (Splice-junction Gene Sequences)</td><td>2440</td><td>3</td><td>Spambase</td><td>3519</td><td>2</td></tr><tr><td>Steel Plates Faults</td><td>1484</td><td>2</td><td>Bank Marketing</td><td>5999</td><td>2</td></tr><tr><td>Blood Transfusion Service Center</td><td>572</td><td>2</td><td>Raisin</td><td>688</td><td>2</td></tr><tr><td>Website Phishing</td><td>1035</td><td>3</td><td>Letter Recognition</td><td>15300</td><td>26</td></tr><tr><td>Taiwanese Bankruptcy Prediction</td><td>5217</td><td>2</td><td>Waveform Database Generator (Version 1)</td><td>3825</td><td>3</td></tr><tr><td>Statlog (Image Segmentation)</td><td>1767</td><td>7</td><td>Haberman&#x27;s Survival</td><td>234</td><td>2</td></tr><tr><td>Vertebral Column</td><td>237</td><td>3</td><td>Statlog (German Credit Data)</td><td>765</td><td>2</td></tr><tr><td>Optical Recognition of Handwritten Digits</td><td>4299</td><td>10</td><td>Breast Cancer</td><td>212</td><td>2</td></tr><tr><td>Drug Consumption (Quantified)</td><td>1442</td><td>7</td><td>Mammographic Mass</td><td>634</td><td>2</td></tr><tr><td>Yeast</td><td>1135</td><td>10</td><td>Credit Approval</td><td>499</td><td>2</td></tr><tr><td>Contraceptive Method Choice</td><td>1127</td><td>3</td><td>Hepatitis C Virus (HCV) for Egyptian patients</td><td>1059</td><td>4</td></tr><tr><td>Japanese Credit Screening</td><td>499</td><td>2</td><td>Chess (King-Rook vs. King-Pawn)</td><td>2445</td><td>2</td></tr><tr><td>Student Performance on an Entrance Examination</td><td>510</td><td>4</td><td>Predict Students&#x27; Dropout and Academic Success</td><td>3384</td><td>3</td></tr><tr><td>Heart Disease</td><td>227</td><td>5</td><td>SPECT Heart</td><td>204</td><td>2</td></tr><tr><td>Room Occupancy Estimation</td><td>7749</td><td>4</td><td>Differentiated Thyroid Cancer Recurrence</td><td>293</td><td>2</td></tr><tr><td>ISOLET</td><td>5965</td><td>26</td><td>Statlog (Vehicle Silhouettes)</td><td>646</td><td>4</td></tr><tr><td>Musk (Version 2)</td><td>5048</td><td>2</td><td>National Poll on Healthy Aging (NPHA)</td><td>546</td><td>3</td></tr><tr><td>Breast Cancer Wisconsin (Diagnostic)</td><td>436</td><td>2</td><td>Hayes-Roth</td><td>101</td><td>3</td></tr><tr><td>Congressional Voting Records</td><td>177</td><td>2</td><td>Cardiotocography</td><td>1626</td><td>10</td></tr><tr><td>Cirrhosis Patient Survival Prediction</td><td>211</td><td>3</td><td>Autism Screening Adult</td><td>466</td><td>2</td></tr><tr><td>SPECTF Heart</td><td>204</td><td>2</td><td>Statlog (Heart)</td><td>206</td><td>2</td></tr><tr><td>Image Segmentation</td><td>160</td><td>7</td><td>ILPD (Indian Liver Patient Dataset)</td><td>443</td><td>2</td></tr><tr><td>NHANES 2013-2014 Age Prediction Subset</td><td>1743</td><td>2</td><td>Statlog (Australian Credit Approval)</td><td>527</td><td>2</td></tr><tr><td>Ionosphere</td><td>268</td><td>2</td><td>Polish Companies Bankruptcy</td><td>15275</td><td>2</td></tr></table>

Table 1: Summary of the datasets used in the experimental evaluation retrieved from the UCI Machine Learning Repository [9]. For each dataset, we report the total number of instances and the number of target classes.

Moreover, in the analysis of the results, we explicitly account for diferences in dataset complexity by ordering datasets according to increasing linear separability between classes, as estimated by the generalized discrimination value (GDV) [44]. This allows us to assess how model selection behavior varies with dataset simplicity.

## 4.2 Models

Following the theoretical insights of [8], we employed fully connected neural networks with a single hidden layer and ReLU activation functions, in order to preserve architectural simplicity and experimental controllability while exploring diferent generalization regimes. Indeed, as shown in [8], generalization behavior depends critically on the ratio between the number of trainable parameters and the number of training samples.

Accordingly, we define a parameter-to-sample ratio r, where r = 1 corresponds to an equal number of model parameters and samples, while values below or above 1 indicate under- and over-parameterized regimes, respectively. Thus, the use of a shallow architecture allows us to systematically explore these regimes by varying the number of hidden units so as to control the total number of trainable parameters relative to the size of the training dataset. In our experiments, we consider the values r ∈ {0.3, 0.5, 0.7, 0.8, 1, 1.2, 5, 10, 50}.

Notice that we deliberately focus on shallow neural networks with a single hidden layer, as our goal is not to achieve state-of-the-art performance, but to isolate and analyze the efect of validation criteria on model selection. Deeper architectures introduce multiple additional factors–such as hierarchical representations, layer-wise implicit regularization, and complex optimization dynamics–that can confound the interpretation of validation-based selection mechanisms.

By adopting a controlled shallow setting, we are able to systematically vary the parameter-to-sample ratio and explore diferent generalization regimes while keeping architectural and optimization-related efects to a minimum. This choice enables a clearer assessment of how diferent validation criteria influence model selection, independently of depth-related phenomena.

## 4.3 Adopted losses

Cross-entropy: cross-entropy loss, widely used in classification tasks, emerges naturally from the principle of maximum likelihood estimation under the assumption that the model outputs a categorical distribution over the classes. It is defined as

$$
\ell_ {\mathrm{CE}} = - \sum_ {i = 1} ^ {N} \sum_ {k = 1} ^ {K} t _ {k} ^ {(i)} \log (m _ {k} ^ {(i)})
$$

where t is the one-hot encoded target vector $\mathbf { t } ^ { ( i ) } \in \{ 0 , 1 \} ^ { K }$ of the actual label $\boldsymbol y ^ { ( i ) }$ i.e. $t _ { k } ^ { ( i ) } = 1 \mathrm { ~ i f ~ } k = y ^ { ( i ) }$ , and $t _ { k } ^ { ( i ) } = 0$ otherwise, and $\mathbf { m } ^ { ( i ) } = ( m _ { 1 } ^ { ( i ) } , \dots , m _ { K } ^ { ( i ) } )$ is the class output probability distribution of the model M on the input $\mathbf { x } ^ { ( i ) }$

Leng et al. [5] introduce PolyLoss, a polynomial reparameterization of cross-entropy obtained via its Taylor expansion around the correct-class confidence. Denoting by $m _ { y ^ { ( i ) } }$ the predicted probability for the true class of sample i, the loss takes the form

$$
\ell_ {\mathrm{PolyLoss}} = \sum_ {j = 1} ^ {\infty} \alpha_ {j} \left(1 - m _ {y ^ {(i)}}\right) ^ {j},
$$

with coeficients $\{ \alpha _ { j } \} _ { j \ge 1 }$ to be tuned. In its natural (infinite) form, PolyLoss is impractical and does not consistently outperform standard cross-entropy. To address this, the authors propose a simplified, first-order truncation,

$$
\ell_ {\mathrm{Poly-1}} = - \log m _ {y ^ {(i)}} + \epsilon (1 - m _ {y ^ {(i)}}),
$$

controlled by a scalar hyperparameter $\epsilon .$

The C-Loss [4, 12] is a surrogate for the 0–1 loss built from the correntropy [11] between true labels and model scores. Unlike cross-entropy, the C-Loss can be more robust to outliers and label noise. In binary classification problems where $y ^ { ( i ) } \in \{ - 1 , 1 \}$ and single output $m ^ { ( i ) } = M ( \mathbf { x } ^ { ( i ) } )$ , it is defined via a positive-definite kernel $- \mathscr { k } ( \cdot )$ (typically Gaussian):

$$
\ell_ {C} (y ^ {(i)}, m ^ {(i)}) = \beta \big (1 - k _ {\sigma} (y ^ {(i)} - m ^ {(i)}) \big)
$$

with $\begin{array} { r } { { \cal { k } } _ { \sigma } ( u ) = \exp \Big ( - \frac { u ^ { 2 } } { 2 \sigma ^ { 2 } } \Big ) } \end{array}$ , β and σ parameters properly chosen. Multiclass variants can be built by applying the one-class-versus-the-rest strategy.

## 4.4 Training and Evaluation Protocol

Models were trained for a maximum of $E = 2 0 , 0 0 0$ epochs for each dataset using stochastic gradient descent with a batch size of 64 samples. The learning rate was set to 0.01 and fixed through all the training epochs. To obtain statistically reliable estimates, all results were computed under a 10-fold stratified cross-validation [45] scheme. For each fold, the 15 % of the training set was used for validation set Val using stratified sampling [45].

Prior to each training, all input features were then standardized using z-score normalization [46, 47]. The normalization parameters (mean and standard deviation) were computed exclusively on the training portion of each fold and subsequently applied to the corresponding validation and test sets, ensuring that no information from the held-out data leaked into the training process [36].

We emphasize that, as above discussed, the objective of this work is not to achieve state-of-the-art performance on these benchmarks, thus we intentionally adopt simple and uniform preprocessing rather than dataset-specific preprocessing prior to each training.

For each dataset and each fold, the model was trained while monitoring validation loss $\ell ( V a l , e )$ and validation accuracy $\alpha ( V a l , e )$ at every epoch e. Model selection was performed based solely on validation criteria, but evaluation was always carried out on the corresponding Test fold. Specifically, for each Test fold we computed:

1. the test accuracy of the model corresponding to the epoch with the minimum validation loss, denoted as $a ( T e s t , e _ { \ell , V a l } ^ { \star } )$ ;

2. the test accuracy of the model corresponding to the epoch with the maximum validation accuracy, denoted as $a ( T e s t , e _ { a , V a l } ^ { \star } ) ;$ ;

3. the test-optimal accuracy, defined as the maximum test accuracy achieved across all training epochs, denoted as $A _ { T e s t } ^ { \star } .$

These three quantities were collected for each fold, yielding paired samples of test accuracies for every dataset and every comparison. Analyses were performed through hypothesis testing. Formally, we tested:

$$
H _ {0}: \mu_ {\bar {a} (T e s t, e _ {a, V a l} ^ {\star})} = \mu_ {A _ {T e s t} ^ {\star}} \qquad \mathrm{vs.} \qquad H _ {1}: \mu_ {\bar {a} (T e s t, e _ {a, V a l} ^ {\star})} <   \mu_ {A _ {T e s t} ^ {\star}},
$$

$$
H _ {0}: \mu_ {\bar {a} (T e s t, e _ {\ell , V a l} ^ {\star})} = \mu_ {A _ {T e s t} ^ {\star}} \qquad \mathrm{vs.} \qquad H _ {1}: \mu_ {\bar {a} (T e s t, e _ {\ell , V a l} ^ {\star})} <   \mu_ {A _ {T e s t} ^ {\star}},
$$

where $\mu _ { a ( T e s t , e _ { a , V a l } ^ { \star } ) }$ denotes the mean test accuracy obtained by selecting, for each fold, the model checkpoint corresponding to the epoch that maximizes the validation accuracy a, and $\mu _ { a ( T e s t , e _ { \ell , V a l } ^ { \star } ) }$ denotes the mean test accuracy obtained by selecting the checkpoint corresponding to the epoch that minimizes the validation loss ℓ. Specifically, normality of the cross-validation results was first assessed using the Shapiro-Wilk test [46]. When normality was not rejected, a paired one-tailed t-test [46] was applied; otherwise, the one-tailed Wilcoxon signed-rank test [46] was used. The significance level was set to $\alpha = 0 . 0 5$

![](images/73582cad1da2f6960d1ec96522e49a8dfb68b0964627d5e5b3e6da7209aaabe5.jpg)  
Fig. 3: An example showing, in a single panel, the validation trajectories (loss $\ell ( \mathrm { V a l } , e )$ in blue and accuracy $\alpha ( \mathrm { V a l } , e )$ in orange, left axis) together with the test accuracy trajectory a(Test, e) (green, right axis). Vertical dashed lines indicate the validationselected epochs $e _ { a , \mathrm { V a l } } ^ { \star }$ and $e _ { \ell , \mathrm { V a l } } ^ { \star }$ , as well as the test–optimal epoch $e _ { a , \mathrm { T e s t } } ^ { \star }$ . Horizontal dotted lines mark $L _ { \mathrm { V a l } } ^ { \star }$ and $A _ { \mathrm { V a l } } ^ { \star }$ . The test accuracies achieved by the two validation–driven selections, $a \left( \mathrm { T e s t } , e _ { \ell , \mathrm { V a l } } ^ { \star } \right)$ and $a \left( \mathrm { T e s t } , e _ { a , \mathrm { V a l } } ^ { \star } \right)$ , contrasted with the best achievable $A _ { \mathrm { T e s t } } ^ { \star }$

## 4.5 Validation Criteria and Loss-Metric Combinations

Models were trained in separate runs, each using a single loss function, i.e. crossentropy loss, C-Loss, or Poly-1, as the training objective. In particular, C-Loss was used with parameters $\sigma = 0 . 5$ and $\beta = 1$ , while $\mathrm { P o l y - 1 }$ was configured with $\epsilon = 1$ For each training run, the resulting sequence of model checkpoints was evaluated on the same validation set $V a l$ using the three loss functions $\ell _ { C E } , \ell _ { C }$ , and $\ell _ { P o l y - 1 }$ and the accuracy a as validation criteria. This procedure was designed to disentangle the efect of the training objective from that of the model selection criterion; accordingly, we adopted a fully crossed experimental design. Precisely, at each training epoch we compute, on the validation set, the adopted losses and the classification accuracy, regardless of the loss used for optimization on the training data. Model selection is then performed independently for each validation criterion by identifying the epoch that optimizes the corresponding quantity. This procedure yields, for every training loss, multiple candidate models selected according to diferent quantity of validation performance. By evaluating all selected models on the same held-out test set, we can quantify how diferent validation criteria induce diferent orderings over the same set of candidate models, and how these orderings translate into test performance.

Moreover, over all the epochs for each training run, early stopping is simulated independently for each validation loss. In the case of loss-based criteria, generalization is considered to have improved whenever the validation loss decreases; for accuracybased early stopping, improvement corresponds to an increase in validation accuracy We consider three configurations: post-hoc checkpoint selection (i.e. no early stopping), corresponding to selecting the best epoch across all training iterations (or until nearperfect fitting of the training data is achieved); early stopping with patience $T = 1 0 ;$ and a more conservative patience of $T = 5 0$ epochs. For each configuration and each validation criterion, the model selected by early stopping is identified as the checkpoint corresponding to the best validation performance observed $T$ epochs before the stopping condition is met. The test accuracy of the selected checkpoint is then compared against the test-optimal accuracy $A _ { T e s t } ^ { \star } ,$ defined as the maximum test accuracy attained over the entire training trajectory. This comparison allows us to quantify the extent to which standard early-stopping practices approximate or fail to recover the test-optimal model.

## 5 Results and discussion

In the following, we report the experimental results. For each experimental setting, datasets are ordered by increasing linear separability, as measured by the generalized discrimination value (GDV), to highlight how model selection behavior varies with dataset complexity.

Results obtained using cross-entropy as training objective and early stopping with $T = 1 0$ are shown in Figure 4. When cross-entropy is used as the validation criterion, the null hypothesis is not rejected in 5.98 % of the evaluated configurations, indicating scenarios in which the diference between the test accuracy achieved by validationbased model selection and the test-optimal accuracy is not statistically significant. In these cases, models selected based on the validation set exhibit test performance that is statistically indistinguishable from the test-optimal one. A similar behavior is observed when alternative loss functions are adopted as validation criteria. Specifically, when C-Loss and PolyLoss are used as validation criteria, the null hypothesis is not rejected in the 5.34 % and 5.98 % of the cases, respectively, leading to comparable conclusions. In contrast, a diferent behavior is observed when validation accuracy is used as the selection criterion. In this case, the null hypothesis is not rejected in the 0.43 % of the evaluated configurations, indicating that accuracy-based validation is substantially less likely to select models whose test performance is statistically indistinguishable from the test-optimal accuracy. This result suggests that, despite being the final evaluation metric, validation accuracy may constitute a less reliable criterion for model selection than loss-based alternatives.

Figure 5 shows the same setup, but using early stopping with $T = 5 0$ . When crossentropy is used as the validation criterion, the null hypothesis is not rejected in 4.91 % of the evaluated configurations. Using C-Loss as validation criterion, this proportion increases to 6.20 %. With Poly-1, the null hypothesis is not rejected in 5.58 % of the configurations. When accuracy is used as the validation criterion, the null hypothesis is not rejected in 0.43 % of the evaluated configurations. These results confirm that, even with a larger early stopping patience, loss-based validation criteria provide a more reliable basis for model selection than validation accuracy to reach test-optimal accuracy.

![](images/7da68fd915ca7d65a01f8cb6ffbee47fb42dd87fc558b0430b8fafbbf0762b27.jpg)  
Fig. 4: Graphical representation of the hypothesis testing results obtained using crossentropy as the training objective and early stopping with patience $T \ = \ 1 0 .$ . Each heatmap reports the p-values obtained from hypothesis tests comparing the test accuracy of models selected using the validation set against the test-optimal accuracy $A _ { \mathrm { T e s t } } ^ { \star }$ across cross-validation folds. From left to right, panels correspond to validation based on cross-entropy loss, C-Loss, Poly-1, and validation accuracy, respectively. Rows represent datasets and columns correspond to diferent parameter-to-sample ratios r. Datasets are ordered from top to bottom according to increasing linear separability, estimated using the generalized discrimination value (GDV).

Figure 6 shows the results without the application of early stopping. When crossentropy is adopted as the validation criterion, the null hypothesis is not rejected in 5.56 % of the evaluated configurations. A comparable behavior is observed also using the other loss functions as validation criterion: using C-Loss, this proportion increases to 6.84 %, while using the Poly-1, the null hypothesis is not rejected in 6.41 % of the cases. Also in this case, when accuracy is used as the validation criterion, the null hypothesis is not rejected with a lower proportion, i.e., 2.56 % of the evaluated configurations.

Results obtained using C-Loss and Poly-1 as training objectives lead to similar conclusions; detailed statistical analyses and corresponding figures are reported in Appendix A.

A summary of the percentages of null hypothesis acceptance across all training objectives, validation criteria, and early stopping configurations is reported in Table 2. Across all training objectives and early stopping settings, loss-based validation criteria consistently yield higher proportions of configurations in which validation-selected models achieve test performance that is statistically indistinguishable from the testoptimal accuracy. In contrast, validation accuracy systematically exhibits the lowest acceptance rates in all considered scenarios.

![](images/43ecc6aea5dec0146fd2320acab76ea35bf5cc7663bd19d1a7074f602b654a5e.jpg)  
Fig. 5: Graphical representation of the hypothesis testing results obtained using crossentropy as the training objective and early stopping with patience $T \ = \ 5 0$ . Each heatmap reports the p-values obtained from hypothesis tests comparing the test accuracy of models selected using the validation set against the test-optimal accuracy $A _ { \mathrm { T e s t } } ^ { \star }$ across cross-validation folds. From left to right, panels correspond to validation based on cross-entropy loss, C-Loss, Poly-1, and validation accuracy, respectively. Rows represent datasets and columns correspond to diferent parameter-to-sample ratios r. Datasets are ordered from top to bottom according to increasing linear separability, estimated using the generalized discrimination value (GDV).

Table 2: Percentages of null hypothesis acceptance under diferent validation criteria and early stopping strategies, for each training objective. The acceptance of the null hypothesis corresponds to cases in which the validation-selected model achieves test performance statistically indistinguishable from the test-optimal model.

<table><tr><td>Training Objective</td><td>Early Stopping</td><td>Cross-Entropy</td><td>C-Loss</td><td>PolyLoss</td><td>Accuracy</td></tr><tr><td rowspan="3">Cross-Entropy</td><td>T=10</td><td>5.98%</td><td>5.34%</td><td>5.98%</td><td>0.43%</td></tr><tr><td>T=50</td><td>4.91%</td><td>6.20%</td><td>5.58%</td><td>0.43%</td></tr><tr><td>Disabled</td><td>5.56%</td><td>6.84%</td><td>6.41%</td><td>2.56%</td></tr><tr><td rowspan="3">C-Loss</td><td>T=10</td><td>17.74%</td><td>19.44%</td><td>18.38%</td><td>11.11%</td></tr><tr><td>T=50</td><td>17.95%</td><td>19.02%</td><td>18.38%</td><td>11.54%</td></tr><tr><td>Disabled</td><td>19.23%</td><td>21.15%</td><td>18.59%</td><td>13.25%</td></tr><tr><td rowspan="3">Poly-1</td><td>T=10</td><td>5.77%</td><td>6.62%</td><td>6.20%</td><td>0.64%</td></tr><tr><td>T=50</td><td>5.56%</td><td>5.98%</td><td>5.77%</td><td>0.64%</td></tr><tr><td>Disabled</td><td>5.56%</td><td>6.41%</td><td>5.98%</td><td>1.71%</td></tr></table>

![](images/06be7ea3c71910bc9316ee2071ba92a0e162fbc025eb2f9b0ddeb1e562dfe6eb.jpg)  
Fig. 6: Graphical representation of the hypothesis testing results obtained using crossentropy as the training objective, without early stopping. Each heatmap reports the p-values obtained from hypothesis tests comparing the test accuracy of models selected using the validation set against the test-optimal accuracy $A _ { \mathrm { T e s t } } ^ { \star }$ across cross-validation folds. From left to right, panels correspond to validation based on cross-entropy loss, C-Loss, Poly-1, and validation accuracy, respectively. Rows represent datasets and columns correspond to diferent parameter-to-sample ratios r. Datasets are ordered from top to bottom according to increasing linear separability, estimated using the generalized discrimination value (GDV).

Across all training objectives, diferent loss-based validation criteria exhibit closely aligned acceptance rates, indicating that the benefit arises from loss-based model selection per se, rather than from a specific choice of loss function. As a practical consequence, this suggests that, among loss-based criteria, simpler and computationally less expensive losses, such as cross-entropy, may be preferred for validation without compromising model selection efectiveness. Consistently with this observation, despite being the final evaluation metric, validation accuracy proves to be a weaker signal for model selection compared to loss-based alternatives.

The observed trends are consistent across all considered training objectives, indi cating that the superiority of loss-based validation criteria does not rely on a specific alignment between training and validation losses.

Finally, training with C-Loss is associated with higher acceptance rates across validation criteria, suggesting a potentially stronger alignment between validationbased selection and test-optimal performance. However, even in this case, the higher acceptance rate remains largely independent of the validation loss used for model selection. From a practical perspective, these results suggest that monitoring validation loss, rather than validation accuracy, constitutes a more reliable strategy for model selection when the objective is to approach test-optimal accuracy.

![](images/9dad6d0d37cc5469142c83c95dba790738aae19b6f0bf7b3f05add0e71c251a8.jpg)  
Fig. 7: Acceptance rate of the null hypothesis with $\alpha = 0 . 0 5$ as a function of the parameter-to-sample ratio r, under diferent training objectives, early stopping strategies, and validation criteria. Rows correspond to the training objective (cross-entropy, C-Loss, and Poly-1), while columns report results obtained using early stopping with $T = 1 0 , T = 5 0$ , and with early stopping disabled. Bars represent diferent validation criteria: cross-entropy, C-Loss, PolyLoss, and validation accuracy. The acceptance rate indicates the proportion of configurations in which the test accuracy of the model selected via validation is statistically indistinguishable from the test-optimal accuracy.

Figure 7 reports the acceptance rate of the null hypothesis with respect to the parameter-to-sample ratio r, under diferent training objectives (rows), early stopping strategies (columns), and validation criteria (bars). Across all training objectives and early stopping configurations, the acceptance rates remain remarkably stable as r varies over several orders of magnitude, ranging from strongly under-parameterized to highly over-parameterized regimes. No systematic trend can be observed as a function of r, suggesting that the ability of validation-based model selection to identify models whose test accuracy is statistically indistinguishable from the test-optimal one is insensitive to the degree of model parameterization.

This behavior is consistent across all validation criteria and early stopping strategies. In particular, the relative ordering between loss-based validation criteria and validation accuracy is preserved for all values of r, with loss-based criteria consistently achieving higher acceptance rates than accuracy-based validation. This suggests that the superiority of loss-based validation does not arise from a specific regime of parameterization, but rather reflects a more general property of the validation signal itself.

Overall, these results indicate that the observed advantages of loss-based model selection are robust across under-parameterized, critically parameterized, and overparameterized regimes. Consequently, the efectiveness of loss-based validation criteria in aligning validation-based model selection with test-optimal performance does not depend on fine-tuning the parameter-to-sample ratio, but persists across a wide range of model capacities.

Figure 8 reports the acceptance rate of the null hypothesis with respect to the significance level α. Results are shown for diferent training objectives (rows), early stopping strategies (columns), and validation criteria (curves). Across all configurations, the acceptance rate exhibits a monotonic increase as α decreases, as expected from the behavior of hypothesis testing procedures. Interestingly, a consistent and pronounced separation emerges between loss-based validation criteria (dashed lines) and validation accuracy (solid). For all training objectives and early stopping settings, validation based on loss functions yields substantially higher acceptance rates than validation accuracy over the entire range of significance levels considered. This indicates that loss-based criteria are systematically more likely to select models whose test performance is statistically indistinguishable from the test-optimal one.

The three loss-based validation criteria exhibit closely aligned trends, with only marginal quantitative diferences across all values of α. This observation suggests that the advantage of loss-based validation does not stem from a particular choice of loss function, which is still coherent to what was observed before. In contrast, validation accuracy, despite being the final evaluation metric, confirms to provide a weaker and less reliable signal for selecting models that generalize optimally to the test set, as evidenced by its consistently lower acceptance rates.

Finally, diferences across training objectives are also observable. In particular, training with C-Loss is associated with higher acceptance rates across all validation criteria, suggesting a stronger alignment between validation-based model selection and test-optimal performance. Nonetheless, the relative advantage of loss-based validation over accuracy-based selection persists uniformly across all training objectives, reinforcing the conclusion that monitoring validation loss constitutes a more reliable strategy for model selection than validation accuracy when the goal is to approach test-optimal accuracy.

![](images/be4208031bc18c4682c0e3a223e9ffdaee4df4d54392984db84ccd19eed0cd4e.jpg)  
Fig. 8: Acceptance rate of the null hypothesis as a function of the significance level α, under diferent training objectives, early stopping strategies, and validation criteria. The acceptance rate indicates the proportion of configurations in which the test accuracy of the model selected via validation is statistically indistinguishable from the test-optimal accuracy. Rows correspond to the training objective (cross-entropy, C-Loss, and Poly-1), while columns report results obtained using early stopping with T = 10, T = 50, and with early stopping disabled. Curves represent diferent validation criteria: loss-based criteria (cross-entropy, C-Loss, and Poly-1, dashed lines) and validation accuracy (solid lines).

## 6 Conclusions

This study examined how diferent validation criteria lead model selection when the deployment objective is test accuracy. Across datasets, generalization regimes, and early-stopping settings, accuracy, despite being the main classification task metric, underperform as a selection criterion. Indeed, loss-based validation (cross-entropy, C-Loss, PolyLoss) selects checkpoints whose test accuracy is more often statistically close to the test-optimal model than those chosen by validation accuracy. The gap persists whether early stopping is used with moderate or large patience, or disabled in favor of post-hoc checkpoint selection.

This can be due to the fact that accuracy is a discrete, thresholded indicator with low sensitivity to incremental improvements. It changes only when predictions flip around the decision boundary, so it produces long plateaus and frequent ties across epochs—especially on small validation sets—making early-stopping triggers noisy and unstable. Moreover, accuracy ignores confidence: two checkpoints with equal accuracy can difer substantially in margins. These finite-sample efects are amplified by patience-based rules, where small random oscillations can halt training early on a merely local optimum. In short, accuracy is excellent for final reporting, but it seems a poor compass to validate over an iterative training process.

Conversely, using the adopted validation loss leads to higher acceptance rates in our hypothesis tests than validation accuracy, regardless of the training loss. The advantage is robust to stopping regime (early vs. post-hoc) and persists across datasets and model sizes. The specific loss used for validation matters less than being loss-based. In fact, cross-entropy, C-Loss, and PolyLoss used on the validation set deliver closely aligned acceptance rates. Practically, this means one can prefer the simpler, cheaper cross-entropy for validation without sacrificing selection quality. Finally, acceptance rates show no systematic dependence from under- to over-parameterized.

It is also worth noting that, across validation criteria, the absolute proportion of accepted null hypothesis remains modest. Indeed, in most cases, validation-selected models do not achieve test performance that is statistically indistinguishable from the test-optimal checkpoint. This might suggests that validation-based selection alone may be insuficient and motivates further investigation into alternative analytical and methodological approaches.

This study intentionally focused on accuracy-centred evaluation under standard supervised protocols. Extending the analysis to other endpoints (e.g., F1, MCC, PR-AUC), settings with pronounced class imbalance, or larger-scale regimes would clarify when accuracy-based validation narrows the gap. It would also be valuable to study validation-set size explicitly, and to assess whether combining a loss-based selector with lightweight post-selection threshold tuning further closes the distance to the test-optimal model.

In conclusion, what we monitor matters. When model selection depends on a validation trajectory, especially under early stopping, loss-based criteria provide a more reliable estimate of generalization and, in turn, more dependable accuracy on unseen data.

## Acknowledgment

This work was partially funded by the PNRR MUR project PE0000013-FAIR (CUP: E63C25000630006).

## Funding

## References

[1] Goodfellow, I., Bengio, Y., Courville, A.: Deep Learning. MIT Press, ??? (2016)

[2] Bishop, C.M.: Regularization and complexity control in feed-forward networks (1995)

[3] Huang, C., Zhai, S., Talbott, W., Martin, M.B., Sun, S.-Y., Guestrin, C., Susskind, J.: Addressing the loss-metric mismatch with adaptive loss alignment. In: International Conference on Machine Learning, pp. 2891–2900 (2019). PMLR

[4] Singh, A., Pokharel, R., Principe, J.: The c-loss function for pattern classification. Pattern Recognition 47(1), 441–453 (2014)

[5] Leng, Z., Tan, M., Liu, C., Cubuk, E.D., Shi, J., Cheng, S., Anguelov, D.: Polyloss: A polynomial expansion perspective of classification loss functions. In: International Conference on Learning Representations (2022)

[6] Hagiwara, K.: Regularization learning, early stopping and biased estimator. Neurocomputing 48(1-4), 937–955 (2002)

[7] Evgeniou, T., Poggio, T., Pontil, M., Verri, A.: Regularization and statistical learning theory for data analysis. Computational Statistics & Data Analysis 38(4), 421–432 (2002)

[8] Advani, M.S., Saxe, A.M., Sompolinsky, H.: High-dimensional dynamics of generalization error in neural networks. Neural Networks 132, 428–446 (2020)

[9] Asuncion, A., Newman, D., et al.: UCI machine learning repository. Irvine, CA, USA (2007)

[10] Terven, J., Cordova-Esparza, D.-M., Romero-Gonz´alez, J.-A., Ram´ırez-Pedraza, A., Ch´avez-Urbiola, E.: A comprehensive survey of loss functions and metrics in deep learning. Artificial Intelligence Review 58(7), 195 (2025)

[11] Santamar´ıa, I., Pokharel, P.P., Principe, J.C.: Generalized correlation function: definition, properties, and application to blind equalization. IEEE Transactions on Signal Processing 54(6), 2187–2197 (2006)

[12] Singh, A., Principe, J.C.: A loss function for classification based on a robust similarity metric. In: The 2010 International Joint Conference on Neural Networks (IJCNN), pp. 1–6 (2010). IEEE

[13] Wang, X.-N., Wei, J.-M., Jin, H., Yu, G., Zhang, H.-W.: Probabilistic confusion entropy for evaluating classifiers. Entropy 15(11), 4969–4992 (2013)

[14] Marchetti, F., Guastavino, S., Piana, M., Campi, C.: Score-oriented loss (sol) functions. Pattern Recognition 132, 108913 (2022)

[15] Marchetti, F., Guastavino, S., Campi, C., Benvenuto, F., Piana, M.: A comprehensive theoretical framework for the optimization of neural networks classification performance with respect to weighted metrics. Optimization Letters 19(1), 169–192 (2025)

[16] Caruana, R., Lawrence, S., Giles, C.: Overfitting in neural nets: Backpropagation, conjugate gradient, and early stopping. Advances in neural information processing systems 13 (2000)

[17] Ji, Z., Li, J., Telgarsky, M.: Early-stopped neural networks are consistent. Advances in Neural Information Processing Systems 34, 1805–1817 (2021)

[18] Soudry, D., Carmon, Y.: No bad local minima: Data independent training error guarantees for multilayer neural networks. arXiv preprint arXiv:1605.08361 (2016)

[19] Swirszcz, G., Czarnecki, W.M., Pascanu, R.: Local minima in training of neural networks. arXiv preprint arXiv:1611.06310 (2016)

[20] Goodfellow, I.J., Vinyals, O., Saxe, A.M.: Qualitatively characterizing neural network optimization problems. arXiv preprint arXiv:1412.6544 (2014)

[21] Zhang, J., Ma, C., Liu, J., Shi, G.: Penetrating the influence of regularizations on neural network based on information bottleneck theory. Neurocomputing 393, 76–82 (2020)

[22] Baldi, P., Chauvin, Y.: Temporal evolution of generalization during learning in linear networks. Neural Computation 3(4), 589–603 (1991)

[23] Wang, C., Venkatesh, S., Judd, J.: Optimal stopping and efective machine complexity in learning. Advances in neural information processing systems 6 (1993)

[24] Dodier, R.: Geometry of early stopping in linear networks. Advances in neural information processing systems 8 (1995)

[25] B¨uhlmann, P., Yu, B.: Boosting with the l 2 loss: regression and classification. Journal of the American Statistical Association 98(462), 324–339 (2003)

[26] Barron, A.R., Cohen, A., Dahmen, W., DeVore, R.A.: Approximation and learning by greedy algorithms (2008)

[27] Chen, H., Li, L., Pan, Z.: Learning rates of multi-kernel regression by orthogonal greedy algorithm. Journal of Statistical Planning and Inference 143(2), 276–282 (2013)

[28] Wei, Y., Yang, F., Wainwright, M.J.: Early stopping for kernel boosting algo rithms: A general analysis with localized complexities. Advances in Neural

[29] Bandos, T.V., Camps-Valls, G., Soria-Olivas, E.: Statistical criteria for earlystopping of support vector machines. Neurocomputing 70(13-15), 2588–2592 (2007)

[30] Ferro, M.V., Mosquera, Y.D., Pena, F.J.R., Bilbao, V.M.D.: Early stopping by correlating online indicators in neural networks. Neural Networks 159, 109–124 (2023)

[31] Ennett, C.M., Frize, M., Scales, N.: Evaluation of the logarithmic-sensitivity index as a neural network stopping criterion for rare outcomes. In: 4th International IEEE EMBS Special Topic Conference on Information Technology Applications in Biomedicine, 2003., pp. 207–210 (2003). IEEE

[32] Lalis, J., Gerardo, B., Byun, Y.: An adaptive stopping criterion for backpropagation learning in feedforward neural network. International Journal of Multimedia and Ubiquitous Engineering 9(8), 149–156 (2014)

[33] Wu, X.-x., Liu, J.-g.: A new early stopping algorithm for improving neural network generalization. In: 2009 Second International Conference on Intelligent Computation Technology and Automation, vol. 1, pp. 15–18 (2009). IEEE

[34] Natarajan, S., Rhinehart, R.R.: Automated stopping criteria for neural network training. In: Proceedings of the 1997 American Control Conference (Cat. No. 97CH36041), vol. 4, pp. 2409–2413 (1997). IEEE

[35] Iyer, M.S., Rhinehart, R.R.: A novel method to stop neural network training. In: Proceedings of the 2000 American Control Conference. ACC (IEEE Cat. No. 00CH36334), vol. 2, pp. 929–933 (2000). IEEE

[36] Apicella, A., Isgr\`o, F., Prevete, R.: Don’t push the button! exploring data leakage risks in machine learning and transfer learning. Artificial Intelligence Review 58(11), 339 (2025)

[37] Prechelt, L.: Early stopping-but when? In: Neural Networks: Tricks of the Trade, pp. 55–69. Springer, ??? (2002)

[38] Lodwich, A., Rangoni, Y., Breuel, T.: Evaluation of robustness and performance of early stopping rules with multi layer perceptrons. In: 2009 International Joint Conference on Neural Networks, pp. 1877–1884 (2009). IEEE

[39] Nguyen, M.H., Abbass, H.A., McKay, R.I.: Stopping criteria for ensemble of evolutionary artificial neural networks. Applied Soft Computing 6(1), 100–107 (2005)

[40] Suliman, A., Omarov, B.: Early stopping criteria for levenberg-marquardt based

neural network training optimization. International Journal of Engineering and Technology (uae) 7(4.36), 1194–1198 (2018)

[41] Shao, Y., Taf, G.N., Walsh, S.J.: Comparison of early stopping criteria for neuralnetwork-based subpixel classification. IEEE Geoscience and Remote Sensing Letters 8(1), 113–117 (2010)

[42] Vera, M., Rey Vega, L., Piantanida, P.: Pacman: Pac-style bounds accounting for the mismatch between accuracy and negative log-loss. Information and Inference: A Journal of the IMA 13(1), 002 (2024)

[43] Liao, Q., Miranda, B., Banburski, A., Hidary, J., Poggio, T.: A surprising linear relationship predicts test performance in deep networks. arXiv preprint arXiv:1807.09659 (2018)

[44] Schilling, A., Maier, A., Gerum, R., Metzner, C., Krauss, P.: Quantifying the separability of data classes in neural networks. Neural Networks 139, 278–293 (2021) https://doi.org/10.1016/j.neunet.2021.03.035

[45] Bishop, C.M., Bishop, H.: Deep Learning: Foundations and Concepts. Springer, ??? (2023)

[46] Hastie, T.: The elements of statistical learning: data mining, inference, and prediction. Springer (2009)

[47] Apicella, A., Isgr\`o, F., Pollastro, A., Prevete, R.: On the efects of data normalization for domain adaptation on eeg data. Engineering Applications of Artificial Intelligence 123, 106205 (2023)