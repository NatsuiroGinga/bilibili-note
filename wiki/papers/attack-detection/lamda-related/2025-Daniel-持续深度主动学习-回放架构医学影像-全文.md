---
title: "2025-Daniel-持续深度主动学习-回放架构医学影像"
date: 2026-10-15
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/lamda-related/2025-Daniel-持续深度主动学习-回放架构医学影像.pdf"
---

> 本文件由 `mineru-open-api extract` 机械转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片未落库（不保存 PDF 转换中间文件），正文中的图片引用链接已剥离。
# Continual Deep Active Learning for Medical Imaging: Replay-Base Architecture for Context Adaptation

Rui Daniel, M. Rita Verdelho, Catarina Barata, Carlos Santiago

Instituto de Sistemas e Robotica, Instituto Superior T´ ecnico - Universidade de Lisboa, Portugal´ Email: ruipcdaniel@tecnico.ulisboa.pt

Abstract—Deep Learning for medical imaging faces challenges in adapting and generalizing to new contexts. Additionally, it often lacks sufficient labeled data for specific tasks requiring significant annotation effort. Continual Learning (CL) tackles adaptability and generalizability by enabling lifelong learning from a data stream while mitigating forgetting of previously learned knowledge. Active Learning (AL) reduces the number of required annotations for effective training. This work explores both approaches (CAL) to develop a novel framework for robust medical image analysis. Based on the automatic recognition of shifts in image characteristics, Replay-Base Architecture for Context Adaptation (RBACA) employs a CL rehearsal method to continually learn from diverse contexts, and an AL component to select the most informative instances for annotation. A novel approach to evaluate CAL methods is established using a defined metric denominated IL-Score, which allows for the simultaneous assessment of transfer learning, forgetting, and final model performance. We show that RBACA works in domain and class-incremental learning scenarios, by assessing its IL-Score on the segmentation and diagnosis of cardiac images. The results show that RBACA outperforms a baseline framework without CAL, and a state-of-the-art CAL method across various memory sizes and annotation budgets. Our code is available in https://github.com/RuiDaniel/RBACA.

Index Terms—Deep Learning, Active Learning, Continual Learning, Medical Imaging.

## I. INTRODUCTION

The complexity of healthcare interventions, from diagnosis to treatment planning through segmentation, presents significant challenges, creating the need for computational systems assistance. Deep Learning (DL) has been explored for classification, detection, and segmentation tasks, and its learning capacity is already impacting computer-assisted healthcare applications. However, DL in the medical field is still unreliable. Current models are unable to adapt and generalize to new contexts, such as different scanner settings, and there is a lack of labeled data for specific tasks, which is hard to obtain.

To tackle adaptability and generalizability to new contexts, Transfer Learning [1] develops models capable of generalizing from a source domain and task to a target domain and task. In contrast, Continual Learning (CL) [2] involves incremental learning from a data stream across diverse contexts without a predefined target context. It aims to mitigate catastrophic forgetting, which occurs when models trained on new data tend to lose previously acquired capabilities. Therefore, CL is more suitable for adaptability to multiple and varying contexts.

To minimize the cost of obtaining labeled data, Active Learning (AL) [3] methods can be considered when unlabeled data is abundant, as in the case of continuous data streams. AL aims to minimize the amount of data required for effective training by identifying the most informative samples for labeling. The labeling process is performed by an oracle in annotation rounds (query rounds). In pure AL, models are retrained from scratch at each query round, which has high time complexity. Fine-tuning in each round may lead to catastrophic forgetting, while incorporating CL enables the incremental learning of new information. The fusion of the two methods is called Continual Active Learning (CAL) [4].

The objective of this work is to develop tools that enhance the capacity of DL algorithms to adapt and generalize to diverse contexts. Several contributions were achieved:

• A novel CAL framework, denominated Replay-Based Architecture for Context Adaptation (RBACA), was developed for medical image analysis. It employs a CL memory-based rehearsal method and supports various memory management and memory pruning strategies.

• RBACA promotes efficient selection of samples for annotation by considering both informativeness and diversity within an annotation budget.

• RBACA is adaptable to incremental learning of domains and classes, as demonstrated through segmentation and diagnosis of cardiac images.

• A novel approach to evaluate CAL methods was established using a defined metric, termed Incremental Learning Score (IL-Score), which simultaneously assesses transfer learning, forgetting, and final model performance.

• RBACA outperforms both a baseline framework without CAL and a state-of-the-art CAL method across various memory sizes and annotation budgets. RBACA enhances adaptation and generalization to diverse medical imaging contexts by improving the quality of memory representations.

The remainder of the paper is organized as follows: Section 2 reviews the background, Section 3 introduces the methodologies used, Section 4 describes the experimental setup, Section 5 presents the results, and Section 6 concludes the paper.

## II. RELATED WORK

The performance of many DL techniques relies on both training and test sets being drawn from the same distribution, which is unlikely in the real world. When such a shift in distribution occurs, a strategy is to rebuild models from scratch using newly collected training data, which can be unfeasible.

CL [2] involves adapting models to new contexts while maintaining performance on previously learned ones, without retraining from scratch at each new learning phase. There are three fundamental CL scenarios [2]: Domain-Incremental Learning (Domain-IL), Task-Incremental Learning (Task-IL) and Class-Incremental Learning (Class-IL).

Task-IL involves incrementally learning a set of clearly distinct contexts referred to as tasks. At all times task identity must be known. This approach allows training models with task-specific components or with distinct networks for each task. The main challenge lies in effectively sharing learned representations across tasks. Domain-IL involves incrementally learning a particular task across various contexts designated domains. At test time, the algorithm does not require domain identification, as all of them share the same potential outputs. Class-IL involves learning to discriminate among an increasing number of classes, which appear as contexts denominated episodes. Consequently, a challenge is learning to discriminate between classes that have not been observed together, as different episodes can contain different classes.

According to De Lange et al. [5], CL strategies can be categorized into 3 families: memory-based, regularization-based, and parameter isolation methods. However, certain methods utilize techniques from multiple families. Memory and replay mechanisms use storage to recall past contexts, combining new data with previous representations when learning a new context. They face challenges with memory requirements and privacy concerns, as data access is often restricted in real-world situations, such as in health applications where legislation limits long-term data storage [6].

These techniques fall into three categories: rehearsal, pseudo-rehearsal, and constrained optimization. Rehearsal methods involve replayed stored samples. However, they may lead to overfitting on the replayed subset. In van de Ven et al. [2], Experience Replay (ER) involves replayed data chosen uniformly at random from previous contexts. Zheng et al. [7] adapted ER to address brain tumor segmentation.

The memory may also contain latent representations. For instance, Incremental Classifier and Representation Learning (iCaRL) [8] learns strong classifiers and representations by storing templates closest to the feature mean of each class. Pseudo-rehearsal methods involve generating pseudo-samples using a generative model. For instance, Deep Generative Replay (DGR) [9] replays generated representations at the input level. Constrained optimization allows for greater freedom in transferring knowledge between tasks. Under Task-IL, Averaged Gradient Episodic Memory (A-GEM) [10] enforces the inequality constraint that the loss on replayed data cannot increase during optimization of the loss on new data.

Regularization-based methods involve adding a regularization term to the loss. This term penalizes changes to important parameters that represent previously learned contexts. Datafocused techniques rely on functional regularization, meaning that when training on new contexts, they aim to retain the previously learned input-output mapping at specific anchor points. For instance, Learning without Forgetting (LwF) [11] uses current context inputs as anchor points and has been applied to classifying retinal diseases in Verma et al. [12]. In contrast, prior-focused methods estimate parameter importance distribution. For example, Elastic Weight Consolidation (EWC) [13] quantifies parameter importance by utilizing the Fisher information matrix and has been applied to classifying optical coherence tomography in Verma et al. [12].

Finally, parameter isolation methods employ distinct model parameters for each context. In Fixed Networks, the architecture remains static, with fixed context-specific components to each context. In contrast, Dynamic Architectures do not impose constraints on architecture size. They involve adding new neurons to models as they encounter new contexts, which allows for knowledge preservation by updating both old and newly added parameters at a different learning pace [14].

AL strives for high accuracy with a minimal number of annotations by employing methods to select the most informative samples for labeling. The selection process involves a trained model from the labeled pool L. Newly labeled instances are added to L, and the model learns from them. In contrast to serial selection, batch-mode selection allows querying instances in groups, which enhances labeling efficiency.

In the research conducted by Settles et al. [3], three AL scenarios are introduced: Membership Query Synthesis, Stream-Based Selective Sampling, and Pool-Based Active Learning. In the first one, the learner may request labels for any unlabeled instance within the input space, including queries it generates, which can lead to outliers. On the other hand, in Stream-Based Selective Sampling, the learner decides whether to label or discard each sequentially sampled unlabeled instance. Finally, in Pool-Based Active Learning, a pool of unlabeled data is evaluated to select the best query.

Settles et al. [3] presented several methods for selecting the most informative samples to be labeled. Uncertainty Sampling [15] selects instances where the model is least confident about the labeling, with entropy [16] being the commonly used uncertainty metric. Query-By-Committee (QBC) [17] employs a committee of models, all trained on the current labeled set. The models vote on the labeling of each unlabeled instance, identifying the samples where they disagree the most. Grimova et al. [18] applied both QBC and Uncertainty Sampling to the classification of overnight polysomnography records.

In contrast, Expected Gradient Length (EGL) [19] selects the instance whose labeling would result in the greatest training gradient. However, as the true label is unknown, the gradient is computed as an expectation across potential labelings, which is computationally demanding. Another method is Estimated Error Reduction, which directly aims to minimize generalization error. However, for each sample, the model must be incrementally re-trained for every potential labeling.

Batch-mode selection aims to assemble the optimal query batch. Some strategies focus on informativeness, such as Bayesian Active Learning by Disagreement (BALD) [20] which was applied by Gal et al. [21] for skin cancer diagnosis. However, this may select a set of informative yet similar samples. To more accurately represent the input distribution, other strategies integrate diversity-based approaches. On the other hand, hybrid query strategies consider both informativeness and diversity. For example, BatchBALD [22] extends BALD by incorporating the correlation between batch data points.

DL can automatically learn and extract relevant features from imaging annotated data, leveraging techniques such as Convolutional Neural Networks (CNNs). Deep Active Learning [23] aims to minimize annotation costs while maintaining DL capabilities. A DL model typically consists of two stages: feature extraction and task learning. Consequently, the uncertainty of the DL model encompasses the uncertainty inherent in both stages. For instance, Learning Loss for Active Learning (LLAL) [24] leverages the output of multiple hidden layers as input for a loss prediction module, which guides the query strategy. DL requires a substantial volume of labeled data for effective training. One strategy for expanding the labeled sample dataset involves assigning pseudo-labels to high-confidence samples, as in Cost-Effective Active Learning (CEAL) [25].

AL presents several challenges, such as a limited labeling budget and a lack of adaptability. Models are typically retrained from scratch in each query round, using the everincreasing labeled pool, which is computationally inefficient. Re-training and fine-tuning at each round is not a viable solution due to catastrophic forgetting. CL facilitates adaptation to future domains while minimizing the risk of forgetting. However, it requires all data to be labeled. These AL and CL disadvantages give rise to CAL, wherein the model progressively learns new information in each round of annotations.

CAL methods have demonstrated the capability to surpass AL techniques, achieving noteworthy speedups. Das et al. [26] introduces Scaled Distillation w/ Submodular Sampling (CAL-SDS2). This method regularizes the model and utilizes submodular functions to capture notions of diversity and representativeness while achieving a considerable speedup in a dermatoscopy dataset. Ayub et al. [27] present Few-Shot Continual Active Learning (FoCAL) for object classification, with a CL pseudo-rehearsal strategy and an AL uncertainty sampling. Vu. et al. [4] explore CAL in Domain-IL, Task-IL and Class-IL scenarios. They propose a forgetting-learning profile to understand the relationship between the contrasting goals of low forgetting and quick learning ability.

Continual Active Learning for Scanner Adaptation (CASA), a CAL architecture developed by Perkonigg et al. [28], is designed to process a continuous stream of images in a multiscanner environment. It operates within a Domain-IL CL scenario using a replay-based rehearsal method where annotations are stored in the rehearsal memory. An AL algorithm automatically detects shifts in image characteristics, selects examples for labeling within a limited budget, and adapts training accordingly.

Several concerns have been identified with replay-based architectures. The quality of memory representations is affected by factors such as memory size, annotation budget, memory management strategies, memory pruning techniques, and AL methods. For instance, in Vu. et al. [4], a random sampling technique is used both as an AL method and as a pruning strategy. Furthermore, FoCAL focuses on achieving a good trade-off between memory storage and model performance.

Fig. 1. The RBACA architecture. Processes a data stream S and is composed of four key components: PC module, outlier memory O, training memory M, and task module. It supports various memory management (MM), pruning, and AL strategies.

On the other hand, CASA uses Least Recently Used (LRU) [29] pruning which may remove crucial data. Moreover, its AL method relies on a performance metric (Perf) on similar stored samples, which may disregard highly informative samples.

## III. METHODOLOGY

The identified concerns with the state-of-the-art, particularly replay-based methods, have motivated the development of a novel framework called Replay-Based Architecture for Context Adaptation (RBACA). This framework aims to improve the quality of context representations in memory, thereby enhancing performance. RBACA employs a CL memorybased rehearsal method and an AL component that selects informative instances.

Fig. 1 shows the RBACA architecture. The Pseudo-Context (PC) module evaluates each data stream sample, deciding whether to route it to the oracle or to the outlier memory O (AL method). When O receives a new item, an evaluation determines whether a new PC should be created and then directed to the oracle. The oracle labels and stores these instances in the rehearsal training memory M of size $K _ { M } .$ which is utilized by the task module for network training (CL component).

We build over the CASA [28] architecture, improving memory management, memory pruning, identification of relevant samples, and expanding the model to Class-IL scenarios. Both task network and style network can be designed based on the desired task (e.g., segmentation or diagnosis). Compared to CASA, RBACA employs more complex techniques; however, this is masked by its parallelizability.

## A. Memory Management

M is balanced among existing Pseudo-Contexts (PCs). Upon the addition of a new PC, pruning is executed for each PC to maintain balance. Both labeling budget $\beta$ and $K _ { M }$ influence the diversity of PCs in M and the quality of their representations. Early consumption of $\beta$ can result in the nonrepresentation of later PCs in memory. With a small $K _ { M }$ memory saturation may occur, compromising representations, especially as the number of PCs increases. On the other hand, an excessively large $K _ { M }$ may lead to an imbalance in M between PCs. These concerns can be addressed by enabling memory management (MM) to shift from Static to Dynamic.

When a new PC is found, its samples are annotated and added to M. M must have space for this new set. In Static MM, when a new PC is found, pruning is applied to all existing PCs. In contrast, in Dynamic MM, k new elements are allocated for each newly detected and annotated PC until the maximum allowed system memory is reached. However, an initial memory size of only k may be insufficient for effective training. Therefore, in a dynamic DM-i strategy, pruning occurs for the first i − 1 newly detected PCs.

## B. Memory Pruning

Dataset pruning, without synthesizing representations, summarizes the dataset into a subset valuable for training by selecting which samples to retain and which to remove. Multiple pruning techniques were considered, as their performance varies with data type and volume. One of these is LRU pruning, as employed by Perkonigg et al. [28].

Among distribution-based techniques, K-Means [30], Gaussian Mixture Models (GMMs) [31], and Density-Based Spatial Clustering of Applications with Noise (DBSCAN) [32] strategies are compared. In these approaches, the samples selected for retention are those closest to each cluster’s centroid. K-Means groups samples by assigning each point to the nearest cluster centroid, resulting in low computational complexity. However, it is sensitive to noise, does not account for variance, and requires the number of clusters in advance. In contrast, GMMs can handle clusters of arbitrary shapes by computing the probabilities of each point belonging to each cluster. Finally, DBSCAN provides a density-based approach to clustering that does not require specifying the number of clusters.

Informativeness-based techniques: Uncertainty Sampling [15] and EGL [19] were also considered. Additionally, several hybrid strategies that balance diversity and informativeness were tested, such as K-Means combined with Uncertainty Sampling (KU) and EGL combined with GMMs (EGLGMM). In these approaches, clustering is first applied. For each cluster i, k<sub>i</sub> samples are selected: the $k _ { i } / 2$ closest to the centroid, and among the remaining samples, the $k _ { i } / 2$ most informative.

## C. Informativeness-Based Query Method

When a new sample belongs to a known PC, an AL algorithm must determine whether to annotate or discard the instance. To make this decision, RBACA enables an uncertainty sampling strategy based on informativeness, using a decision threshold. The uncertainty of each sample is calculated by inferring the unlabeled data pool through the task network.

## D. Adaptation to Class-IL

RBACA is adaptable for Class-IL. This scenario begins with a classification problem within a single episode. Then, by leveraging shared learned representations across episodes, the number of classes expands. RBACA for Class-IL involved modifications in the data loading phase, the task network model, and the metrics. The most crucial adaptation occurs in the final layer of the task network. This layer initially starts with 0 units. During each training step, when a new class is detected, a corresponding unit is added to the final layer while preserving the weights of the already identified classes. Therefore, RBACA is adaptable to any classification problem, as the number of classes is not predefined, and new classes may emerge.

## IV. EXPERIMENTAL SETUP

This section describes the dataset used, tasks, training conditions, data manipulation techniques, metrics, and baselines.

## A. M&Ms Dataset

We evaluate the performance of RBACA in cardiac imaging problems using the Multi-Centre, Multi-Vendor, and Multi-Disease Cardiac Image Segmentation Challenge dataset (M&Ms) [33]. Our model is applied to Domain-IL (segmentation across multiple scanners and centers) and Class-IL (multiple disease diagnosis across multiple scanners and centers) problems. M&Ms includes cardiovascular magnetic resonance segmented 2D images with contours for the background (BG), left ventricle (LV), left ventricular myocardium (MYO), and right ventricle (RV). These correspond to segmentation classes 0, 1, 2, and 3, respectively. Each patient examination is recorded in a separate file, including an external code, vendor, center, End-Diastolic (ED) frame, and End-Systolic (ES) frame. Each file contains multiple frames, each featuring several slices. The ED frame represents the heart when the ventricles are fully filled with blood. The ES frame represents the heart when the ventricles have completed contraction. So both of these frames include the most relevant slices.

M&Ms includes the following pathologies: Hypertrophic Cardiomyopathy (HCM) - 24.6%; Dilated Cardiomyopathy (DCM) - 28.1%; Hypertensive Heart Disease (HHD) - 7.0%; Abnormal Right Ventricle (ARV) - 4.3%; Athlete Heart Syndrome (AHS) - 0.9%; Ischemic Heart Disease (IHD) - 1.4%; Left Ventricle Non-Compaction (LVNC) - 0.6%; Healthy/within normal limits (NOR) - 25.8%; and Other - 7.2%. The dataset comprises 4 vendors across 5 centers: C1 - Hospital Vall d’Hebron (Barcelona) - Siemens; C2 - Cl´ınica Sagrada Familia (Barcelona) - Philips; C3 - Universitatsklinikum Hamburg-Eppendorf (Hamburg) - Philips; C4 -¨ Hospital Universitari Dexeus (Barcelona) - General Electric; and C5 - Cl´ınica Creu Blanca (Barcelona) - Canon.

Patient-level splitting divided the dataset into a base training set (1130 slices), a continual training set (4322 slices), a validation set (922 slices), and a test set (1544 slices). The continual training set initially consists of unlabeled data, with the M&M centers appearing in the order 1, 4, 2, 3, and 5, based on Perkonigg et al. [28]. The oracle provides annotations by revealing the labels.

## B. Tasks and Training Conditions

ResNet-50 [34], a CNN pretrained on ImageNet, was used as style network across all tasks. The training conditions for both tasks included a batch size of 8, Adam optimizer with a learning rate of $1 0 ^ { - 4 }$ , 10 epochs for base training, and 3 epochs of training on the rehearsal memory, where a training step is performed whenever the number of updates without training exceeded 9. To ensure reproducibility in the experiments, a seed must be selected for each run, ensuring deterministic behavior across both CPU and multi-GPU setups.

Using M&Ms, a cardiac segmentation task was defined, where the objective is to classify each pixel. During model training, the background class (BG) is excluded from the loss calculation to ensure that the large number of background pixels does not bias the training process. A 2D-UNet [35] was used as task network. This task was addressed within Domain-IL, and various loss were tested: Cross-Entropy (CE), Focal Loss (FL) [36], Dice, DiceCE, and DiceFL.

Cardiac pathology classification task is defined as a multiclass problem under Class-IL, where the model learns new categories as new samples from distinct centers become available. M&Ms, with 9 categories, is well-suited for this, as different centers contain distinct pathologies. ResNet-50 and Vision Transformer (ViT) were tested. Based on Dosovitskiy et al. [37], the selected ViT is a transformer encoder pre-trained on ImageNet-21k and fine-tuned on ImageNet 2012, both at a resolution of 224×224. While ResNet-50 is effective with limited data and computational resources, ViT can potentially outperform it in cases with large datasets and substantial computational power. Both models were tested using CE loss.

In both tasks, the number of clusters for K-Means was set to 5, and the number of components for GMMs was set to 5. Additionally, DBSCAN is considered, with a maximum distance of 0.1 between neighbors and a minimum of 3 neighbors required for a point to be considered a core point.

## C. Data Processing

For ResNet-50 and UNet, the images were center-cropped to 240×196 pixels and normalized to a [0,1] range. In contrast, the used ViT has specific preprocessing requirements. Images were resized to 224×224 pixels and normalized across the RGB channels with a mean and standard deviation of 0.5 per channel. <sup>1</sup> To enhance generalization and performance, online data augmentation (DAug) was employed during training. In each instance, RBACA randomly applies one of ten possible transformations: no augmentation; 180-degree rotation; horizontal and vertical flips; Gaussian blur with a kernel size of (0.06, 0.06) and a standard deviation of 0.006; brightness increase/decrease by 10%; contrast increase/decrease by 10%; and Gaussian noise addition with a mean of 0 and a standard deviation of 0.035.

## D. Evaluation

For segmentation, the Dice Similarity Coefficient (DSC) assesses agreement between prediction and target. In classification, F1 Score is calculated as the arithmetic mean of the perclass metrics. To assess forgetting, Backward Transfer (BWT) [38] measures how learning a new context affects performance on previously learned contexts. BWT is defined as

$$
\mathrm{BWT} = \frac {1}{t - 1} \sum_ {j = 1} ^ {t - 1} (a _ {t, j} - a _ {j, j}) \quad ,\tag{1}
$$

where $\boldsymbol { a } _ { x , y }$ represents the test metric (DSC or F1 Score) for context y after learning from context x, and t is the final learned context. Conversely, Forward Transfer (FWT), which is given by

$$
\mathrm{FWT} = \frac {1}{t - 1} \sum_ {j = 2} ^ {t} (a _ {j - 1, j} - \overline {{b _ {j}}}) \quad ,\tag{2}
$$

quantifies the impact of prior contexts on the performance of new contexts. Here, $\overline { { b _ { j } } }$ denotes the test metric for context j at random initialization. The relevant metrics are DSC/F1 Score (range [0,1]), BWT (range [−1,1]), and FWT (range [−1,1]). Therefore, we propose a novel approach to evaluate CAL methods by using the average of these three metrics, denominated as Incremental Learning Score (IL-Score). This metric allows for the simultaneous evaluation of transfer learning, forgetting, and final model performance. IL-Score ranges from [−2/3, 1], where higher values indicate superior performance.

## E. Model Comparison

Various baselines were established. ContextEval aims to show the impact of prior contexts on new contexts’ performance. Assuming there are C contexts, it involves using C − 1 contexts for training and one for testing in each round. This process is repeated C times, rotating the test context. Finally, the average FWT across rounds is calculated. SeqFineTune enables to assess forgetting and transfer learning, in a framework without CAL. The model is finetuned with each context sequentially, resulting in C fine-tuning procedures. FWT, BWT and task-specific metrics are obtained. In this study, each center represents a context, so C is equal to the number of centers in M&Ms, C=5. The performance of RBACA was also compared with a state-of-the-art CAL method (CASA).

## V. EXPERIMENTAL RESULTS AND DISCUSSION

This section presents and discusses the experimental results through both quantitative and qualitative analyses. For each experiment, seeds 1, 2, and 3 were used, and the results are presented as the mean ± standard deviation.

## A. Cardiac Segmentation

For the cardiac segmentation task, results were obtained without DAug as in Perkonigg et al. [28], to enable a direct comparison with CASA. Various loss functions were evaluated using RBACA, with $\beta = 4 3 0 , K _ { M } = 1 2 8$ , Static MM, Perf AL method and LRU pruning. DiceCE achieved the highest IL-Score and was selected.

TABLE I. AL $U _ { t h }$ with $\beta = 4 3 0 , K _ { M } = 1 2 8 ,$ Static MM, and LRU pruning. Label counter is the number of annotations, and train counter is the number of batch training steps performed.

<table><tr><td>AL Method</td><td>Label Counter</td><td>Train Counter</td><td>IL-Score</td></tr><tr><td> $U_{th}$ =0.001</td><td>430</td><td>140</td><td>0.426 ± 0.003</td></tr><tr><td> $U_{th}$ =0.01</td><td>430</td><td>269</td><td>0.418 ± 0.008</td></tr><tr><td> $U_{th}$ =0.02</td><td>430</td><td>1136</td><td>0.434 ± 0.006</td></tr><tr><td> $U_{th}$ =0.0225</td><td>273</td><td>879</td><td>0.426 ± 0.004</td></tr><tr><td> $U_{th}$ =0.025</td><td>427</td><td>1786</td><td>0.437 ± 0.002</td></tr><tr><td> $U_{th}$ =0.0275</td><td>234</td><td>877</td><td>0.423 ± 0.011</td></tr><tr><td> $U_{th}$ =0.03</td><td>64</td><td>860</td><td>0.424 ± 0.007</td></tr><tr><td> $U_{th}$ =0.05</td><td>52</td><td>67</td><td>0.427 ± 0.002</td></tr></table>

To determine the best uncertainty threshold, $U _ { t h }$ , for the AL method, a study was conducted using the same parameters. The results are reported in Table I. $U _ { t h } = 0 . 0 2 5$ was identified as the best configuration and serves as a reference for subsequent tests. At this threshold, the annotation budget is used ideally because it depletes as late as possible. This allows for new annotations to be made continuously until the end of the stream, leading to a more representative memory. As a result, retraining occurs more frequently.

Using ContextEval, the results are $\mathrm { D S C } = 0 . 5 6 3 \pm 0 . 0 0 3$ and $\mathrm { F W T } = 0 . 5 3 8 \pm 0 . 0 1 6$ . FWT is calculated as the difference between DSC and DSC obtained from a randomly initialized untrained model. The significant FWT observed demonstrates that training on a new context benefits when the model has been previously trained on earlier contexts.

SeqFineTune overall results are reported in Table II. The significant FWT indicates a substantial benefit in using transfer learning. However, the negative BWT shows evidence of forgetting, meaning that, generally, the performance for a center decreases after learning from other contexts.

Given that real-world problems often involve multiple constraints, such as limited annotation budgets or restricted system memory, nine configurations were considered. These configurations combine the labeling budget $\beta = \{ 1 0 8 , 4 3 0 , 8 6 0 \}$ with the memory size $K _ { M } = \{ 2 0 0 , 4 8 5 , 2 0 0 0 \}$ , representing low, medium, and high values for each variable. There are 4322 training slices in the M&Ms dataset. Thus, the $\beta$ values approximately correspond to {2.5%, 10%, 20%} of the training set size, while $K _ { M }$ represents approximately {4.6%, 11.2%, and 46.3%} of the training set size. These values were selected within the training set size to evaluate the performance of the methods under various configurations of β and $K _ { M }$

For each combination of β and memory size, RBACA was tested with MM: {Static, DM-1, DM-2, DM-3}; Pruning: {LRU, K-Means, GMMs, DBSCAN, Uncertainty, EGL, KU, EGLGMM}; and AL: {Perf, $U _ { t h } = \{ 0 . 0 2 5 , 0 . 0 2 2 5 , 0 . 0 2 \} \}$

With Static MM, LRU pruning, and Perf AL method, on average, around 5 PCs are formed. Consequently, $K _ { M } \ =$ {200, 485, 2000} will, on average, correspond to a final memory size per PC of $k = \{ 4 0 , 9 7 , 4 0 0 \}$ . In Static MM, $K _ { M }$ is fixed and k depends on the number of PCs. In contrast, in Dynamic MM, k is fixed and $K _ { M }$ depends on the number of PCs. Therefore, when applying Dynamic MM, k will be used as the defined parameter instead of $K _ { M }$

The IL-Score comparison between RBACA, CASA, and

Fig. 2. RBACA, CASA and SeqFineTune segmentation IL-Score for multiple configurations. Points are labeled using the XYZ format, where X denotes either R or $\mathrm { C } ,$ representing RBACA or CASA; Y indicates 1, 4, or 8, corresponding to β values of 108, 430, or 860; and Z represents 1, 2, or 3, relating to k values of 40, 97, or 400 in Dynamic MM, or to $K _ { M }$ values of 200, 485, or 2000 in Static MM.

SeqFineTune on the selected combinations is illustrated in Fig. 2. The detailed results are reported in Table II and in the Appendix, in Table V. SeqFineTune is used as a comparison method; its configuration remains constant, including the absence of memory and infinite $\beta .$

SeqFineTune achieved the worst results. For each combination of β and memory size, RBACA surpasses both CASA and SeqFineTune in performance. The behavior of each model was observed for a specific patient. Fig. 3 displays a cardiac slice, its target, and the agreement between each model’s prediction and the target, along with the DSC for each class, demonstrating that RBACA achieved superior performance.

The memory distribution across PCs and pathologies was analyzed for both RBACA (R11) and CASA (C11), as illustrated in the Appendix, in Fig. 6. For both, 4 PCs were created: PC 0 contains data from Center 1 (Siemens), PC 1 from Center 5 (Canon), PC 2 from Centers 2 and 3 (both Philips), and PC 3 comprises a mix of all centers. RBACA outperforms CASA, forming the same number of PCs with similar characteristics, and in this specific configuration, even with a smaller total memory $K _ { M } ~ ( 1 6 0 < 2 0 0$ samples).

## B. Cardiac Classification

The performance of ResNet-50 and ViT was assessed using RBACA, with and without DAug, under $\beta = 4 3 0 , K _ { M } = 1 2 8 .$ Static MM, Perf AL method and LRU pruning. The results are shown in the Appendix, in Table IV, indicating that ResNet-50 with DAug achieved the best performance.

ContextEval obtained $\mathrm { F W T } = 0 . 0 8 6 \pm 0 . 0 1 6$ and F1 Score $= 0 . 0 8 6 \pm 0 . 0 1 6$ for this task. In each round, the overall F1 Score is the average of the F1 Scores for the classes present in the test labels. Additionally, F1 Score from a randomly initialized untrained model is 0 because it has no units in its final layer. The positive FWT indicates that training on a new episode benefits from having been previously trained on earlier episodes, even if those contain different classes.

TABLE II. Segmentation results for RBACA, CASA, and SeqFineTune across memory sizes and $\beta .$

<table><tr><td colspan="4">Setup</td><td colspan="4">Results</td></tr><tr><td>Fig. 2 Ref.</td><td>MM</td><td>Pruning</td><td>AL Method</td><td>BWT</td><td>FWT</td><td>DSC</td><td>IL-Score</td></tr><tr><td>S</td><td>-</td><td>-</td><td>-</td><td> $-0.032 \pm 0.008$ </td><td> $0.493 \pm 0.020$ </td><td> $0.554 \pm 0.009$ </td><td> $0.338 \pm 0.010$ </td></tr><tr><td>R11</td><td>DM-3</td><td>K-Means</td><td>Perf</td><td> $-0.005 \pm 0.004$ </td><td> $0.583 \pm 0.002$ </td><td> $0.727 \pm 0.002$ </td><td> $0.435 \pm 0.003$ </td></tr><tr><td>C11</td><td>Static</td><td>LRU</td><td>Perf</td><td> $0.002 \pm 0.001$ </td><td> $0.557 \pm 0.002$ </td><td> $0.709 \pm 0.002$ </td><td> $0.423 \pm 0.002$ </td></tr><tr><td>R41</td><td>Static</td><td>DBSCAN</td><td>Perf</td><td> $0.001 \pm 0.005$ </td><td> $0.581 \pm 0.001$ </td><td> $0.741 \pm 0.003$ </td><td> $0.441 \pm 0.003$ </td></tr><tr><td>C41</td><td>Static</td><td>LRU</td><td>Perf</td><td> $0.003 \pm 0.004$ </td><td> $0.577 \pm 0.001$ </td><td> $0.729 \pm 0.005$ </td><td> $0.436 \pm 0.004$ </td></tr><tr><td>R81</td><td>Static</td><td>LRU</td><td>Perf</td><td> $0.012 \pm 0.003$ </td><td> $0.579 \pm 0.000$ </td><td> $0.743 \pm 0.002$ </td><td> $0.445 \pm 0.002$ </td></tr><tr><td>C81</td><td>Static</td><td>LRU</td><td>Perf</td><td> $0.012 \pm 0.003$ </td><td> $0.579 \pm 0.000$ </td><td> $0.743 \pm 0.002$ </td><td> $0.445 \pm 0.002$ </td></tr><tr><td>R12</td><td>DM-3</td><td>KU</td><td> $U_{th}=0.0225$ </td><td> $-0.002 \pm 0.001$ </td><td> $0.577 \pm 0.001$ </td><td> $0.719 \pm 0.003$ </td><td> $0.431 \pm 0.002$ </td></tr><tr><td>C12</td><td>Static</td><td>LRU</td><td>Perf</td><td> $-0.001 \pm 0.002$ </td><td> $0.566 \pm 0.002$ </td><td> $0.700 \pm 0.005$ </td><td> $0.422 \pm 0.003$ </td></tr><tr><td>R42</td><td>DM-3</td><td>KU</td><td>Perf</td><td> $0.008 \pm 0.007$ </td><td> $0.578 \pm 0.000$ </td><td> $0.739 \pm 0.005$ </td><td> $0.442 \pm 0.005$ </td></tr><tr><td>C42</td><td>Static</td><td>LRU</td><td>Perf</td><td> $-0.007 \pm 0.001$ </td><td> $0.581 \pm 0.001$ </td><td> $0.734 \pm 0.001$ </td><td> $0.436 \pm 0.001$ </td></tr><tr><td>R82</td><td>DM-3</td><td>EGL</td><td>Perf</td><td> $0.001 \pm 0.001$ </td><td> $0.582 \pm 0.000$ </td><td> $0.736 \pm 0.000$ </td><td> $0.440 \pm 0.001$ </td></tr><tr><td>C82</td><td>Static</td><td>LRU</td><td>Perf</td><td> $-0.013 \pm 0.009$ </td><td> $0.562 \pm 0.003$ </td><td> $0.718 \pm 0.006$ </td><td> $0.422 \pm 0.006$ </td></tr><tr><td>R13</td><td>Static</td><td>DBSCAN</td><td> $U_{th}=0.02$ </td><td> $0.004 \pm 0.002$ </td><td> $0.562 \pm 0.001$ </td><td> $0.711 \pm 0.005$ </td><td> $0.426 \pm 0.003$ </td></tr><tr><td>C13</td><td>Static</td><td>LRU</td><td>Perf</td><td> $0.005 \pm 0.002$ </td><td> $0.557 \pm 0.003$ </td><td> $0.690 \pm 0.008$ </td><td> $0.417 \pm 0.005$ </td></tr><tr><td>R43</td><td>DM-3</td><td>KU</td><td>Perf</td><td> $0.008 \pm 0.003$ </td><td> $0.582 \pm 0.002$ </td><td> $0.739 \pm 0.002$ </td><td> $0.443 \pm 0.002$ </td></tr><tr><td>C43</td><td>Static</td><td>LRU</td><td>Perf</td><td> $0.006 \pm 0.002$ </td><td> $0.575 \pm 0.002$ </td><td> $0.731 \pm 0.002$ </td><td> $0.437 \pm 0.002$ </td></tr><tr><td>R83</td><td>DM-3</td><td>LRU</td><td>Perf</td><td> $0.010 \pm 0.002$ </td><td> $0.582 \pm 0.001$ </td><td> $0.742 \pm 0.001$ </td><td> $0.445 \pm 0.001$ </td></tr><tr><td>C83</td><td>Static</td><td>LRU</td><td>Perf</td><td> $0.003 \pm 0.002$ </td><td> $0.575 \pm 0.002$ </td><td> $0.732 \pm 0.001$ </td><td> $0.437 \pm 0.002$ </td></tr></table>

Fig. 3. Image, target, and prediction agreement for a specific patient slice.

SeqFineTune results are reported in Table III. The positive FWT demonstrates the benefit of using transfer learning. However, the negative BWT indicates catastrophic forgetting, as performance on a context drops significantly after learning from other contexts because the model tends to predict only the classes from the current training context.

For each of the 9 configurations used in segmentation, RBACA was tested with MM: {Static, DM-3}; Pruning: {LRU, K-Means, GMMs, DBSCAN, Uncertainty, EGL, KU, EGLGMM}; and AL: {Perf, $U _ { t h } = \left\{ 0 . 0 2 5 , 0 . 0 2 2 5 , 0 . 0 2 \right\} ]$ }. The performance comparison for RBACA, CASA and SeqFineTune across the combinations is shown in Fig. 4. Detailed results are reported in Table III and in the Appendix, in Table VI. SeqFineTune has the poorest IL-Score performance, and RBACA outperforms CASA, which is consistent with the conclusions from segmentation, demonstrating RBACA’s adaptability to different problems. However, in this problem,

RBACA does not achieve high performance, and further advancements are needed to meet the standards required for medical applications.

The pathologies stored in memory for RBACA (R82) and CASA (C82) are presented in Fig. 5. RBACA achieves a better balance between classes and greater class representativeness in memory, as demonstrated by higher entropy [16], leading to superior performance than CASA.

## VI. CONCLUSIONS AND FUTURE WORK

This work introduces a novel CAL framework for robust medical image analysis that enhances adaptability and generalizability while reducing annotation effort. A novel approach to evaluate CAL methods is established using a defined metric denominated IL-Score, which allows for the simultaneous assessment of transfer learning, forgetting, and final model performance. The performance was evaluated in cardiac segmentation and pathology classification within Domain-IL and Class-IL scenarios, respectively. RBACA outperformed a baseline framework without CAL (SeqFineTune) and a stateof-the-art CAL method (CASA) across various memory sizes and annotation budgets in both scenarios, demonstrating its adaptability. RBACA offers a range of adjustable features for each task, memory size, and annotation budget. It supports both static and dynamic memory strategies and employs more effective pruning. Additionally, it enhances representations using an AL method that considers informativeness.

TABLE III. Classification results for RBACA, CASA, and SeqFineTune across memory sizes and $\beta .$

<table><tr><td colspan="4">Setup</td><td colspan="4">Results</td></tr><tr><td>Fig. 4 Ref.</td><td>MM</td><td>Pruning</td><td>AL Method</td><td>BWT</td><td>FWT</td><td>F1 Score</td><td>IL-Score</td></tr><tr><td>S</td><td>-</td><td>-</td><td>-</td><td>-0.733 ± 0.028</td><td>0.074 ± 0.013</td><td>0.308 ± 0.031</td><td>-0.117 ± 0.018</td></tr><tr><td>R11</td><td>Static</td><td>EGL</td><td>Perf</td><td>0.025 ± 0.002</td><td>0.178 ± 0.003</td><td>0.114 ± 0.002</td><td>0.106 ± 0.002</td></tr><tr><td>C11</td><td>Static</td><td>LRU</td><td>Perf</td><td>0.037 ± 0.007</td><td>0.165 ± 0.001</td><td>0.107 ± 0.003</td><td>0.103 ± 0.004</td></tr><tr><td>R41</td><td>DM-3</td><td>EGLGMM</td><td> $U_{th}$ =0.02</td><td>0.027 ± 0.002</td><td>0.182 ± 0.003</td><td>0.118 ± 0.003</td><td>0.109 ± 0.003</td></tr><tr><td>C41</td><td>Static</td><td>LRU</td><td>Perf</td><td>0.041 ± 0.005</td><td>0.166 ± 0.003</td><td>0.109 ± 0.004</td><td>0.105 ± 0.004</td></tr><tr><td>R81</td><td>DM-3</td><td>K-Means</td><td> $U_{th}$ =0.02</td><td>0.027 ± 0.005</td><td>0.179 ± 0.001</td><td>0.118 ± 0.001</td><td>0.108 ± 0.003</td></tr><tr><td>C81</td><td>Static</td><td>LRU</td><td>Perf</td><td>0.032 ± 0.008</td><td>0.170 ± 0.006</td><td>0.107 ± 0.006</td><td>0.103 ± 0.007</td></tr><tr><td>R12</td><td>DM-3</td><td>LRU</td><td>Perf</td><td>0.025 ± 0.009</td><td>0.178 ± 0.001</td><td>0.114 ± 0.004</td><td>0.106 ± 0.006</td></tr><tr><td>C12</td><td>Static</td><td>LRU</td><td>Perf</td><td>0.027 ± 0.009</td><td>0.163 ± 0.006</td><td>0.098 ± 0.007</td><td>0.096 ± 0.007</td></tr><tr><td>R42</td><td>DM-3</td><td>EGL</td><td>Perf</td><td>0.027 ± 0.005</td><td>0.184 ± 0.002</td><td>0.119 ± 0.003</td><td>0.110 ± 0.004</td></tr><tr><td>C42</td><td>Static</td><td>LRU</td><td>Perf</td><td>0.040 ± 0.010</td><td>0.164 ± 0.004</td><td>0.104 ± 0.006</td><td>0.103 ± 0.007</td></tr><tr><td>R82</td><td>Static</td><td>K-Means</td><td>Perf</td><td>0.035 ± 0.007</td><td>0.179 ± 0.003</td><td>0.118 ± 0.001</td><td>0.111 ± 0.004</td></tr><tr><td>C82</td><td>Static</td><td>LRU</td><td>Perf</td><td>0.035 ± 0.014</td><td>0.168 ± 0.003</td><td>0.105 ± 0.004</td><td>0.103 ± 0.009</td></tr><tr><td>R13</td><td>Static</td><td>Uncertainty</td><td> $U_{th}$ =0.0225</td><td>0.016 ± 0.005</td><td>0.181 ± 0.001</td><td>0.111 ± 0.003</td><td>0.103 ± 0.003</td></tr><tr><td>C13</td><td>Static</td><td>LRU</td><td>Perf</td><td>0.034 ± 0.014</td><td>0.166 ± 0.004</td><td>0.105 ± 0.008</td><td>0.102 ± 0.010</td></tr><tr><td>R43</td><td>Static</td><td>EGL</td><td> $U_{th}$ =0.02</td><td>0.024 ± 0.005</td><td>0.181 ± 0.002</td><td>0.118 ± 0.004</td><td>0.108 ± 0.004</td></tr><tr><td>C43</td><td>Static</td><td>LRU</td><td>Perf</td><td>0.042 ± 0.003</td><td>0.167 ± 0.004</td><td>0.109 ± 0.003</td><td>0.106 ± 0.003</td></tr><tr><td>R83</td><td>Static</td><td>EGL</td><td>Perf</td><td>0.030 ± 0.003</td><td>0.183 ± 0.003</td><td>0.119 ± 0.001</td><td>0.111 ± 0.003</td></tr><tr><td>C83</td><td>Static</td><td>LRU</td><td>Perf</td><td>0.036 ± 0.003</td><td>0.169 ± 0.001</td><td>0.108 ± 0.002</td><td>0.104 ± 0.002</td></tr></table>

Fig. 4. RBACA, CASA and SeqFineTune classification IL-Score for multiple configurations.

Fig. 5. Pathology memory distribution in classification example.

The results underscore the significance of CAL in medical imaging. However, there is potential for further improvements. A promising research direction is to combine techniques from different CL families to mitigate their respective drawbacks and enhance their capabilities. Another suggestion is to evaluate state-of-the-art methods across a range of problems within Domain-IL, Class-IL, and Task-IL scenarios. A potential approach for adapting rehearsal techniques to Task-IL is to utilize multiple task-specific networks while maintaining a single rehearsal memory shared across tasks.

CAL methods with storage mechanisms raise data privacy concerns, particularly when dealing with sensitive or proprietary data. An interesting research direction is to explore solutions that incorporate privacy-preserving representations. In the case of RBACA, a feasible approach could involve storing a latent representation of each PC instead of raw data.

DL models require a large number of labeled samples for effective training, which can be problematic for CAL methods if the base training dataset is too small. A possible solution is to assign pseudo-labels to high-confidence samples, thereby expanding the base training set so that the CAL method can begin processing the continuous data stream after being effectively trained for the base context. This enhances the model’s transfer learning capabilities to new contexts.

[1] Pan and Yang, “A survey on transfer learning,” IEEE Transactions on Knowledge and Data Engineering, vol. 22, no. 10, pp. 1345–1359, 2009.

[2] Gido M van de Ven, Tinne Tuytelaars, and Andreas S Tolias, “Three types of incremental learning,” Nature Machine Intelligence, vol. 4, no. 12, pp. 1185–1197, 2022.

[3] Burr Settles, “Active learning literature survey,” Machine Learning, vol. 15, no. 2, pp. 201–221, 1994.

[4] Thuy-Trang Vu, Shahram Khadivi, Mahsa Ghorbanali, Dinh Phung, and Gholamreza Haffari, “Active continual learning: On balancing knowledge retention and learnability,” arXiv e-prints, pp. arXiv–2305, 2023.

[5] Matthias De Lange, Rahaf Aljundi, Marc Masana, Sarah Parisot, Xu Jia, Ales Leonardis, Gregory Slabaugh, and Tinne Tuytelaars, “A continualˇ learning survey: Defying forgetting in classification tasks,” IEEE Transactions on Pattern Analysis and Machine Intelligence, vol. 44, no. 7, pp. 3366–3385, 2021.

[6] Marc Masana, Xialei Liu, Bartłomiej Twardowski, Mikel Menta, Andrew D Bagdanov, and Joost Van De Weijer, “Class-incremental learning: survey and performance evaluation on image classification,” IEEE Transactions on Pattern Analysis and Machine Intelligence, vol. 45, no. 5, pp. 5513–5533, 2022.

[7] Guangyao Zheng, Samson Zhou, Vladimir Braverman, Michael A Jacobs, and Vishwa Sanjay Parekh, “Selective experience replay compression using coresets for lifelong deep reinforcement learning in medical imaging,” in Medical Imaging with Deep Learning. PMLR, 2024, pp. 1751–1764.

[8] Sylvestre-Alvise Rebuffi, Alexander Kolesnikov, Georg Sperl, and Christoph H Lampert, “icarl: Incremental classifier and representation learning,” in Proceedings of the IEEE conference on Computer Vision and Pattern Recognition, 2017, pp. 2001–2010.

[9] Hanul Shin, Jung Kwon Lee, Jaehong Kim, and Jiwon Kim, “Continual learning with deep generative replay,” Advances in Neural Information Processing Systems, vol. 30, 2017.

[10] Arslan Chaudhry, Ranzato Marc’Aurelio, Marcus Rohrbach, and Mohamed Elhoseiny, “Efficient lifelong learning with a-gem,” in 7th International Conference on Learning Representations, ICLR 2019. International Conference on Learning Representations, ICLR, 2019.

[11] Zhizhong Li and Derek Hoiem, “Learning without forgetting,” IEEE Transactions on Pattern Analysis and Machine Intelligence, vol. 40, no. 12, pp. 2935–2947, 2017.

[12] Tanvi Verma, Liyuan Jin, Jun Zhou, Jia Huang, Mingrui Tan, Benjamin Chen Ming Choong, Ting Fang Tan, Fei Gao, Xinxing Xu, Daniel S Ting, et al., “Privacy-preserving continual learning methods for medical image classification: a comparative analysis,” Frontiers in Medicine, vol. 10, 2023.

[13] James Kirkpatrick, Razvan Pascanu, Neil Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei A Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, et al., “Overcoming catastrophic forgetting in neural networks,” Proceedings of the National Academy of Sciences, vol. 114, no. 13, pp. 3521–3526, 2017.

[14] Wang et al., “Growing a brain: Fine-tuning by increasing model capacity,” in Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, 2017, pp. 2471–2480.

[15] David D Lewis, “A sequential algorithm for training text classifiers: Corrigendum and additional data,” in Acm Sigir Forum. ACM New York, NY, USA, 1995, vol. 29, pp. 13–19.

[16] Shannon, “A mathematical theory of communication,” The Bell System Technical Journal, vol. 27, no. 3, pp. 379–423, 1948.

[17] H Sebastian Seung, Manfred Opper, and Haim Sompolinsky, “Query by committee,” in Proceedings of the fifth annual workshop on Computational learning theory, 1992, pp. 287–294.

[18] Nela Grimova and Martin Macas, “Query-by-committee framework used for semi-automatic sleep stages classification,” Multidisciplinary Digital Publishing Institute Proceedings, vol. 31, no. 1, pp. 80, 2019.

[19] Burr Settles, Mark Craven, and Soumya Ray, “Multiple-instance active learning,” Advances in Neural Information Processing Systems, vol. 20, 2007.

[20] Neil Houlsby, Ferenc Huszar, Zoubin Ghahramani, and M´ at´ e Lengyel,´ “Bayesian active learning for classification and preference learning,” Stat, vol. 1050, pp. 24, 2011.

[21] Yarin Gal, Riashat Islam, and Zoubin Ghahramani, “Deep bayesian active learning with image data,” in International conference on machine learning. PMLR, 2017, pp. 1183–1192.

[22] Andreas Kirsch, Joost Van Amersfoort, and Yarin Gal, “Batchbald: Efficient and diverse batch acquisition for deep bayesian active learning,” Advances in Neural Information Processing Systems, vol. 32, 2019.

[23] Pengzhen Ren, Yun Xiao, Xiaojun Chang, Po-Yao Huang, Zhihui Li, Brij B Gupta, Xiaojiang Chen, and Xin Wang, “A survey of deep active learning,” ACM Computing Surveys (CSUR), vol. 54, no. 9, pp. 1–40, 2021.

[24] Donggeun Yoo and In So Kweon, “Learning loss for active learning,” in Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, 2019, pp. 93–102.

[25] Keze Wang, Dongyu Zhang, Ya Li, Ruimao Zhang, and Liang Lin, “Cost-effective active learning for deep image classification,” IEEE Transactions on Circuits and Systems for Video Technology, vol. 27, no. 12, pp. 2591–2600, 2016.

[26] Arnav Mohanty Das, Gantavya Bhatt, Megh Manoj Bhalerao, Vianne R Gao, Rui Yang, and Jeff Bilmes, “Accelerating batch active learning using continual learning techniques,” Transactions on Machine Learning Research, 2023.

[27] Ali Ayub and Carter Fendley, “Few-shot continual active learning by a robot,” Advances in Neural Information Processing Systems, vol. 35, pp. 30612–30624, 2022.

[28] Matthias Perkonigg, Johannes Hofmanninger, Christian Herold, Helmut Prosch, Georg Langs, et al., “Continual active learning using pseudodomains for limited labelling resources and changing acquisition characteristics,” Machine Learning for Biomedical Imaging, vol. 1, no. IPMI 2021 special issue, pp. 1–28, 2022.

[29] Laszlo A Belady, Robert A Nelson, and Gerald S Shedler, “An anomaly in space-time characteristics of certain programs running in a paging machine,” Communications of the ACM, vol. 12, no. 6, pp. 349–353, 1969.

[30] Macqueen, Some methods for classification and analysis of multivariate observations, University of California Press, 1967.

[31] Douglas A Reynolds et al., “Gaussian mixture models.,” Encyclopedia of biometrics, vol. 741, no. 659-663, 2009.

[32] Martin Ester, Hans-Peter Kriegel, Jorg Sander, Xiaowei Xu, et al.,¨ “A density-based algorithm for discovering clusters in large spatial databases with noise,” in kdd, 1996, vol. 96, pp. 226–231.

[33] Victor M Campello, Polyxeni Gkontra, Cristian Izquierdo, Carlos Martin-Isla, Alireza Sojoudi, Peter M Full, Klaus Maier-Hein, Yao Zhang, Zhiqiang He, Jun Ma, et al., “Multi-centre, multi-vendor and multi-disease cardiac segmentation: the m&ms challenge,” IEEE Transactions on Medical Imaging, vol. 40, no. 12, pp. 3543–3554, 2021.

[34] Shaoqing Ren, Kaiming He, Ross Girshick, and Jian Sun, “Faster rcnn: Towards real-time object detection with region proposal networks,” IEEE Transactions on Pattern Analysis and Machine Intelligence, vol. 39, no. 6, pp. 1137–1149, 2016.

[35] Olaf Ronneberger, Philipp Fischer, and Thomas Brox, “U-net: Convolutional networks for biomedical image segmentation,” in Medical Image Computing and Computer-Assisted Intervention–MICCAI 2015: 18th International Conference, Munich, Germany, October 5-9, 2015, Proceedings, Part III 18. Springer, 2015, pp. 234–241.

[36] Tsung-Yi Lin, Priya Goyal, Ross Girshick, Kaiming He, and Piotr Dollar, “Focal loss for dense object detection,” IEEE Transactions on Pattern Analysis & Machine Intelligence, vol. 42, no. 02, pp. 318–327, 2020.

[37] Dosovitskiy et al., “An image is worth 16x16 words: Transformers for image recognition at scale,” in International Conference on Learning Representations, 2020.

[38] David Lopez-Paz and Marc’Aurelio Ranzato, “Gradient episodic memory for continual learning,” Advances in Neural Information Processing Systems, vol. 30, 2017.

## APPENDIX

TABLE IV. RBACA classification results with $\beta = 4 3 0 , K _ { M } = 1 2 8$ , Static MM, Perf AL method and LRU pruning, for ResNet-50 and ViT, with and without data augmentation (DAug).

<table><tr><td>Model</td><td>BWT</td><td>FWT</td><td>F1 Score</td><td>IL-Score</td></tr><tr><td>ResNet-50 DAug</td><td> $0.041 \pm 0.002$ </td><td> $0.165 \pm 0.002$ </td><td> $0.107 \pm 0.002$ </td><td> $0.104 \pm 0.002$ </td></tr><tr><td>ResNet-50</td><td> $0.033 \pm 0.005$ </td><td> $0.163 \pm 0.002$ </td><td> $0.105 \pm 0.004$ </td><td> $0.100 \pm 0.004$ </td></tr><tr><td>ViT</td><td> $0.005 \pm 0.007$ </td><td> $0.144 \pm 0.001$ </td><td> $0.097 \pm 0.004$ </td><td> $0.082 \pm 0.005$ </td></tr><tr><td>ViT DAug</td><td> $0.003 \pm 0.004$ </td><td> $0.138 \pm 0.003$ </td><td> $0.096 \pm 0.004$ </td><td> $0.079 \pm 0.004$ </td></tr></table>

CASA  
TABLE V. Segmentation $\beta$ and memory configurations for RBACA and CASA.

<table><tr><td>Framework</td><td colspan="9">RBACA</td><td colspan="9">CASA</td></tr><tr><td>Fig. 2 Ref.</td><td>R11</td><td>R41</td><td>R81</td><td>R12</td><td>R42</td><td>R82</td><td>R13</td><td>R43</td><td>R83</td><td>C11</td><td>C41</td><td>C81</td><td>C12</td><td>C42</td><td>C82</td><td>C13</td><td>C43</td><td>C83</td></tr><tr><td> $\beta$ </td><td>108</td><td>430</td><td>860</td><td>108</td><td>430</td><td>860</td><td>108</td><td>430</td><td>860</td><td>108</td><td>430</td><td>860</td><td>108</td><td>430</td><td>860</td><td>108</td><td>430</td><td>860</td></tr><tr><td> $K_M$ </td><td>160</td><td>200</td><td>200</td><td>582</td><td>388</td><td>388</td><td>2000</td><td>2000</td><td>2400</td><td>200</td><td>200</td><td>200</td><td>485</td><td>485</td><td>485</td><td>2000</td><td>2000</td><td>2000</td></tr><tr><td>k</td><td>40</td><td>40</td><td>40</td><td>97</td><td>97</td><td>97</td><td>333</td><td>400</td><td>400</td><td>50</td><td>33</td><td>40</td><td>121</td><td>97</td><td>80</td><td>500</td><td>333</td><td>285</td></tr><tr><td>no. PCs</td><td>4</td><td>5</td><td>5</td><td>6</td><td>4</td><td>4</td><td>6</td><td>5</td><td>6</td><td>4</td><td>6</td><td>5</td><td>4</td><td>5</td><td>6</td><td>4</td><td>6</td><td>7</td></tr></table>

TABLE VI. Classification $\beta$ and memory configurations for RBACA and CASA.

<table><tr><td>Framework</td><td colspan="9">RBACA</td><td colspan="9">CASA</td></tr><tr><td>Fig. 4 Ref.</td><td>R11</td><td>R41</td><td>R81</td><td>R12</td><td>R42</td><td>R82</td><td>R13</td><td>R43</td><td>R83</td><td>C11</td><td>C41</td><td>C81</td><td>C12</td><td>C42</td><td>C82</td><td>C13</td><td>C43</td><td>C83</td></tr><tr><td> $\beta$ </td><td>108</td><td>430</td><td>860</td><td>108</td><td>430</td><td>860</td><td>108</td><td>430</td><td>860</td><td>108</td><td>430</td><td>860</td><td>108</td><td>430</td><td>860</td><td>108</td><td>430</td><td>860</td></tr><tr><td> $K_M$ </td><td>200</td><td>160</td><td>120</td><td>291</td><td>485</td><td>485</td><td>2000</td><td>2000</td><td>2000</td><td>200</td><td>200</td><td>200</td><td>485</td><td>485</td><td>485</td><td>2000</td><td>2000</td><td>2000</td></tr><tr><td>k</td><td>50</td><td>40</td><td>40</td><td>97</td><td>97</td><td>121</td><td>666</td><td>400</td><td>400</td><td>50</td><td>40</td><td>40</td><td>161</td><td>121</td><td>97</td><td>666</td><td>400</td><td>333</td></tr><tr><td>no. PCs</td><td>4</td><td>4</td><td>3</td><td>3</td><td>5</td><td>4</td><td>3</td><td>5</td><td>5</td><td>4</td><td>5</td><td>5</td><td>3</td><td>4</td><td>5</td><td>3</td><td>5</td><td>6</td></tr></table>

Fig. 6. Pathology and center distribution per PC in segmentation example.

