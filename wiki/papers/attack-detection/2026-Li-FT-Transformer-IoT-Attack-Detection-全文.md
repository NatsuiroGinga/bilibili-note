---
title: "2026-Li-FT-Transformer-IoT-Attack-Detection"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2026-Li-FT-Transformer-IoT-Attack-Detection.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

Article

# FT-Transformer-Based IoT Network Attack Detection and Cross-Dataset Generalization Analysis

Fapeng Li <sup>1</sup> , Yatong Tao <sup>1</sup> and Leilei Qu <sup>2,</sup>\*

1 College of Information Engineering, Dalian Ocean University, Dalian 116023, China; lifapeng@dlou.edu.cn (F.L.)

School of Foundation Studies, Dalian Ocean University, Dalian 116023, China

Correspondence: quleilei@dlou.edu.cn; Tel.: +86-411-84762892

## Abstract

With the large-scale deployment of Internet of Things (IoT) devices in smart homes, smart healthcare, and industrial internet scenarios, network attacks against IoT environments have become increasingly sophisticated, making reliable intrusion detection increasingly important. Focusing on tabular traffic statistical features, this study systematically evaluates an FT-Transformer-based IoT network attack detection framework across primary-dataset classification, feature-aligned external validation, feature-union validation, standardized NetFlow external validation, domain-aligned training, multi-class classification, and SHAP based interpretability analysis. CICIoT2023 is used as the primary dataset for binary and multi-class attack detection, while CICIoMT2024 is used for feature-aligned external valida tion. In addition, NF-ToN-IoT and NF-BoT-IoT are introduced as standardized NetFlow IoT datasets to provide an additional external validation scenario. Random Forest, XGBoost, MLP, TabNet, and a TabTransformer-style numerical Transformer baseline are included for comparison. Experimental results show that FT-Transformer achieves competitive performance on the CICIoT2023 binary classification task, with an accuracy of 0.980675, an attack-class F1-score of 0.980366, a ROC-AUC of 0.995014, and a PR-AUC of 0.996261. Under the controlled 38-feature aligned CICIoT2023-to-CICIoMT2024 validation setting, FT Transformer shows better ROC-AUC stability than Random Forest and XGBoost. However, the feature-union validation experiment reveals that this advantage does not necessarily extend to less constrained feature-space settings, indicating that FT-Transformer should not be interpreted as a universal cross-dataset generalization solution. In the additional standardized NetFlow NF-ToN-IoT-to-NF-BoT-IoT validation experiment, FT-Transformer achieves the strongest external validation performance among the compared models. Furthermore, the domain-aligned FT-Transformer-CORAL experiment shows that explicit source-target representation alignment can improve external validation performance, espe cially in terms of ROC-AUC. For the multi-class task, FT-Transformer achieves an accuracy of 0.809554, a Macro-F1 score of 0.724006, and a Weighted-F1 score of 0.806680. SHAP analysis further indicates that key features such as Number, HTTPS, Header\_Length, Rate, and AVG have meaningful correspondence with known attack behaviors. Overall, this study provides a systematic and reproducible empirical evaluation of FT-Transformer for tabular IoT network attack detection. The results suggest that meaningful cross-dataset robustness requires not only suitable tabular model architectures but also carefully designed validation protocols and representation-learning strategies.

## Check for updates

Academic Editor: Domenico Ursino

Received: 30 April 2026 Revised: 4 June 2026 Accepted: 4 June 2026 Published: 8 June 2026

Copyright: © 2026 by the authors. Licensee MDPI, Basel, Switzerland. This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license.

Keywords: IoT intrusion detection; network attack detection; FT-Transformer; feature-aligned external validation; domain adaptation; tabular deep learning; SHAP

## 1. Introduction

With the rapid development of Internet of Things (IoT) technologies, a large number of sensors, smart terminals, and embedded devices are continuously being connected to networks. IoT systems have been widely deployed in smart homes, smart healthcare, intelligent transportation, and industrial internet scenarios. Compared with traditional internet environments, IoT systems are typically characterized by strong device heterogeneity, diverse communication protocols, resource constraints, and long-term online connectivity. These characteristics make IoT environments more vulnerable to attacks such as distributed denial-of-service (DDoS), denial-of-service (DoS), scanning, spoofing, and malicious control. Therefore, constructing efficient, stable, and generalizable network attack detection models has become a key issue in IoT security research [1–3].

Existing network attack detection methods can generally be divided into traditional machine learning methods and deep learning methods. Traditional methods, such as Random Forest, XGBoost, and support vector machines, often achieve strong performance on structured traffic features. However, their modeling paradigms are usually model-specific, which may limit unified deep representation learning, systematic cross-dataset validation, and integration with interpretability analysis [4–7]. In recent years, deep learning methods, including convolutional neural networks (CNNs), recurrent neural networks (RNNs), long short-term memory networks (LSTMs), and Transformers, have been increasingly introduced into cybersecurity tasks [1,3]. Although these methods show advantages in feature representation and nonlinear modeling, many of them are originally designed for sequential dependencies or local pattern extraction, and thus may not be optimal for tabular tasks dominated by statistical traffic features.

FT-Transformer is a Transformer-based architecture designed for tabular data. Its core idea is to map each numerical feature into an independent feature token and then use self-attention mechanisms to model interactions among different features [8]. For structured data such as network traffic statistical features, FT-Transformer provides a suitable modeling framework [8,9]. On the one hand, it can capture complex dependencies among high-dimensional features within a unified deep learning architecture. On the other hand, it can be naturally combined with interpretability methods such as SHAP, thereby improving the analyzability and credibility of detection results [10,11].

Motivated by these observations, this study investigates the application of FT-Transformer to IoT network attack detection, with a particular focus on in-dataset clas sification performance, cross-dataset generalization, multi-class classification capability, and model interpretability. CICIoT2023 is used as the primary dataset, and CICIoMT2024 is introduced as an external validation dataset to construct a cross-dataset generalization scenario [12,13]. Considering that many existing studies still rely mainly on single-dataset evaluation, this study further follows the evaluation strategy of cross-dataset intrusion de tection research and analyzes model generalization under heterogeneous data distributions based on shared feature alignment [14,15].

The main contributions of this study are summarized as follows:

1. This study provides a systematic empirical evaluation of FT-Transformer for tabular IoT network attack detection. FT-Transformer is evaluated under binary classification, multi-class classification, external validation, and interpretability analysis, thereby clarifying both its strengths and limitations in IoT traffic statistical feature modeling.

2. This study designs multiple external validation protocols to evaluate cross-dataset robustness under different feature-space assumptions. These protocols include controlled 38-feature aligned validation between CICIoT2023 and CICIoMT2024, featureunion validation with missing-feature indicators, and standardized NetFlow IoT validation using NF-ToN-IoT and NF-BoT-IoT.

3. This study compares FT-Transformer with strong traditional and modern tabular baselines, including Random Forest, XGBoost, MLP, TabNet, and a TabTransformerstyle numerical Transformer baseline. McNemar’s test is also applied to examine whether paired prediction differences among major models are statistically significant.

4. This study evaluates a domain-aligned FT-Transformer training strategy based on CORAL representation alignment. By jointly using labeled source-domain samples and unlabeled target-domain samples, this experiment analyzes whether explicit source-target representation alignment can improve external validation performance.

5. This study integrates global and local SHAP analyses to interpret the decision behavior of FT-Transformer. In addition to global feature importance and SHAP summary plots, local SHAP explanations are provided for representative correctly classified and misclassified samples, improving the transparency of model decisions in IoT attack detection.

## 2. Related Work

## 2.1. IoT Network Attack Detection Methods

Research on IoT network attack detection has long relied on structured traffic features for classification, making traditional machine learning methods an important category of approaches in this field. Models such as Random Forest, XGBoost, support vector machines (SVMs), and k-nearest neighbors (KNN) are frequently used as baseline methods for network intrusion detection because of their nonlinear fitting capability and adaptability to tabular data [4–7,16]. In particular, tree-based models often perform well when feature thresholds are informative and class boundaries are relatively clear.

Meanwhile, deep learning methods have increasingly been introduced into IoT security scenarios [1,3]. CNNs are effective for local pattern extraction, RNNs and LSTMs are suitable for modeling sequential dependencies, and autoencoders are commonly used for anomaly detection. However, most IoT traffic features used in tabular intrusion detection are derived from statistical and aggregated flow characteristics. Such data differ from natural images and are not equivalent to standard time-series signals. Therefore, general purpose deep learning architectures do not always fully exploit the characteristics of tabular traffic data.

## 2.2. Deep Learning Methodsfor Tabular Data

In recent years, various deep learning methods have been developed for tabular data modeling, including TabNet, TabTransformer, and FT-Transformer [8,9,17]. Compared with standard multilayer perceptrons (MLPs), these models can more explicitly capture feature interactions and improve representation learning for structured data. Among them, FT Transformer has shown strong potential for tabular tasks by tokenizing numerical features and using self-attention mechanisms to model global feature interactions [8].

## 2.3. Cross-Dataset Generalization and Interpretability

A common limitation of many existing cyberattack detection studies is that training and testing are mainly conducted on a single dataset, with limited validation on external datasets [14,15,18]. As a result, it is difficult to evaluate whether a model can generalize to new scenarios, protocols, devices, or traffic distributions. In IoT network environments, different datasets may vary substantially in device types, attack categories, protocol structures, and feature spaces. Therefore, cross-dataset validation is important for assessing the robustness and practical applicability of intrusion detection models.

In addition to detection performance, cybersecurity applications also require a certain degree of model interpretability. SHAP is a widely used method for explaining tabular machine learning models, as it can quantify the contribution of each feature to model predictions [10,11,19,20]. By introducing SHAP, this study further analyzes the key discrim inative features learned by FT-Transformer in IoT attack detection, thereby improving the transparency and credibility of the detection results.

## 2.4. Pretraining-Based Traffic Representation Learning and Intelligent Data Fusion

Recent studies have increasingly explored deep traffic representation learning, pretraining-based models, and intelligent feature fusion for network traffic analysis. Different from conventional supervised intrusion detection methods that train a task-specific classifier on a single dataset, these approaches attempt to learn more generalizable traffic representations from large-scale or heterogeneous traffic data and then adapt the learned representations to downstream traffic classification or malicious traffic detection tasks.

Early end-to-end deep traffic classification studies, such as Deep Packet, reduced the dependence on manually designed traffic features by integrating feature extraction and classification into a unified deep learning framework [21]. More recently, pretraining-based Transformer models have been introduced into encrypted traffic classification. For example, ET-BERT learns contextualized datagram representations from large-scale unlabeled traffic data and then fine-tunes the pretrained model on downstream encrypted traffic classification tasks [22]. In addition, feature mining and hybrid machine learning/deep learning frameworks have also been studied for encrypted malicious traffic detection, highlighting the importance of traffic feature construction and representation learning in security scenarios [23]. Beyond packet-level or flow-level feature modeling, graph-based traffic interaction analysis has been explored to detect unknown encrypted malicious traffic by modeling flow interaction patterns [24].

Compared with these pretraining-based or interaction-based traffic representation methods, the present study has a different research scope. This work focuses on tabular traffic statistical features and evaluates FT-Transformer under a controlled feature-aligned external validation setting. The proposed setting does not attempt to build a universal traffic representation model across arbitrary heterogeneous datasets. Instead, it provides an empirical assessment of whether a tabular Transformer can maintain competitive indataset performance and stable external validation behavior when the input feature space is explicitly aligned. Therefore, pretraining-based traffic representation learning, graph-based traffic interaction modeling, and intelligent data fusion are regarded as important future directions rather than direct baselines in this study.

## 3. Methodology

To provide an overview of the proposed research workflow, Figure 1 presents the overall technical roadmap of IoT network attack detection based on FT-Transformer. The workflow starts from raw traffic data and sequentially includes label inference and data preprocessing, feature cleaning and normalization, FT-Transformer model training, primary dataset testing, cross-dataset shared feature alignment, external dataset validation, and SHAP-based interpretability analysis.

As shown in Figure 1, this study does not focus only on classification results obtained from a single dataset. Instead, it constructs a complete research pipeline around primary-task detection, cross-dataset generalization, and result interpretation. Based on this framework, the following subsections describe the data preprocessing procedure, model architecture, training strategy, cross-dataset validation design, and SHAP-based explainability analysis.

Overall Framework of IoT Network Attack Detection Based on FT-Transformer

![](images/f5da1ed752264919a97dae36bcc162a4f76a5b098c1a4f086e18e3eecd011b67.jpg)  
Figure 1. Overall technical roadmap for IoT network attack detection based on FT-Transformer.

## 3.1. Data Preprocessing

This study first performs unified preprocessing on the raw CSV files from CICIoT2023 and CICIoMT2024 [12,13]. For files without explicit label columns, labels are inferred according to the file paths and filenames and are then mapped to the target classification tasks. During preprocessing, timestamp-related columns are removed, non-numeric fields are converted into numerical representations, and missing or infinite values are cleaned. In addition, all numerical features were standardized using z-score normalization implemented by StandardScaler. For each processed dataset, the scaler was fitted on the corresponding training split and then applied to the validation and test splits to improve training stability and reduce the influence of feature magnitude differences. This preprocessing strategy was used for the CICIoT2023 binary task, the CICIoT2023 multi-class task, and the CICIoMT2024 binary task. In the feature-aligned cross-dataset experiment, the aligned feature files were constructed from the preprocessed feature space, and no additional independent scaler was stored for the aligned dataset.

## 3.2. FT-Transformer Model Formulation

Based on the overall technical roadmap, Figure 2 further illustrates the FT-Transformer architecture adopted in this study. The model is designed for tabular traffic statistical features and performs attack category prediction through numerical feature tokenization, self-attention-based feature interaction modeling, and an MLP classification head.

As shown in Figure 2, the input numerical features are first mapped into feature tokens and concatenated with a learnable CLS token to form the input sequence. The sequence is then fed into a multi-layer Transformer encoder to model global interactions among different traffic features. Finally, the output corresponding to the CLS token is passed to an MLP classification head to predict the attack category. Based on this architecture, the model is formalized as follows.

The core idea of FT-Transformer is to treat each numerical feature as an independent token [8]. For an input sample $x = [ x _ { 1 } , x _ { 2 } , . . . , x _ { d } ] \in R ^ { d }$ , each numerical feature $x _ { i }$ is mapped into a corresponding feature token:

$$
t _ {i} = x _ {i} W _ {i} + b _ {i} + e _ {i}, i = 1, 2, \ldots , d\tag{1}
$$

where $W _ { i } \in R ^ { k }$ denotes the learnable projection vector for the i th feature, $b _ { i } \in R ^ { k }$ denotes the bias term, $e _ { i } \in R ^ { k }$ denotes the learnable embedding term for the i-th feature, and k denotes the token dimension.

FT-Transformer Architecture for IoT Intrusion Detection  
![](images/f91ce466e1e06701a915101b07de63dda82fee74c3161eb751b3ea51061452b8.jpg)  
Figure 2. FT-Transformer model architecture. Different colors indicate different functional modules in the architecture, including input/token components, Add & Norm, self-attention, feed-forward network, special token, feature embedding, positional embedding, and MLP components.

After obtaining all feature tokens, a learnable classification token $t _ { c l s }$ is introduced to construct the final input token sequence:

$$
T _ {0} = [ t _ {c l s}; t _ {1}; t _ {2}; \ldots ; t _ {d} ]\tag{2}
$$

where $t _ { c l s }$ denotes the learnable classification token, $T _ { 0 } \in R ^ { ( d + 1 ) \times k }$ denotes the final input token matrix, and the semicolon $\prime \prime ,$ indicates concatenation along the sequence dimension. Here, d is the total number of input features, and k is the token dimension. The constructed input sequence is then fed into a multi-layer Transformer encoder to learn global dependencies among traffic features.

For the l-th encoder layer, the scaled dot-product attention is defined as:

$$
\text { Attention } (Q, K, V) = \text { softmax } \left(\frac {Q K ^ {T}}{\sqrt {d _ {k}}}\right) V\tag{3}
$$

The corresponding multi-head attention operation is expressed as:

$$
M u l t i H e a d (Q, K, V) = C o n c a t (h e a d _ {1}, h e a d _ {2}, \ldots , h e a d _ {h}) W ^ {O}\tag{4}
$$

where $Q , K ,$ and V denote the query, key, and value matrices, respectively, and $d _ { k }$ denotes the dimension of the key vectors. hea $d _ { 1 } , h e a d _ { 2 } , . . . , h e a d _ { h }$ represent the outputs of different attention heads, $W ^ { O }$ is the output projection matrix, and h denotes the number of attention heads. Through the multi-head self-attention mechanism, the model can capture interactions among traffic features from multiple representation subspaces, thereby enhancing its ability to model complex attack patterns [8,25].

The output of the l-th Transformer encoder layer can be represented as:

$$
T _ {l} = \text { EncoderLayer } (T _ {l} - 1), l = 1, 2, \dots , L\tag{5}
$$

where $T _ { l }$ denotes the output of the l-th encoder layer, $T _ { l } - 1$ denotes the output of the previous layer, and L denotes the total number of encoder layers.

Finally, the output corresponding to the CLS token in the encoded sequence is used as the sample-level representation. The classification probability is computed as:

$$
p = \text { softmax } (M L P (h _ {c l s}))\tag{6}
$$

where $M L P ( \cdot )$ denotes the multilayer perceptron classification head, $h _ { c l s }$ denotes the final hidden representation of the CLS token, and p denotes the predicted probability distribution over all categories.

The predicted category is obtained as:

$$
\hat {y} = \operatorname{argmax} (p)\tag{7}
$$

Thus, the model performs category prediction for each input traffic sample based on the global representation aggregated by the CLS token.

## 3.3. Training Strategy

This study adopts the cross-entropy loss function for both binary and multi-class classification tasks. AdamW is used as the optimizer, and learning rate decay and early stopping are employed to control the training process. For the binary classification task, the attack-class F1-score is used as the model selection criterion. For the multi-class classification task, macro-F1 is used as the primary model selection metric.

The cross-entropy loss function is defined as:

$$
L = - \sum_ {i = 1} ^ {N} \sum_ {c = 1} ^ {C} y _ {i c} \mathrm{log} (p _ {i c})\tag{8}
$$

where N denotes the number of samples, C denotes the number of classes, $y _ { i c }$ indicates whether sample i belongs to class $c ,$ and $p _ { i c }$ denotes the predicted probability that sample i belongs to class c. During training, learning rate decay and early stopping are combined to improve convergence stability and reduce the risk of overfitting.

## 3.4. Cross-Dataset Validation Protocols

This study evaluates cross-dataset robustness using three complementary validation protocols. These protocols are designed to examine model behavior under different degrees of feature-space consistency and dataset heterogeneity, including controlled feature alignment, feature-union validation, and standardized NetFlow-based external validation.

Protocol 1 is the 38-feature aligned external validation between CICIoT2023 and CICIoMT2024. In this setting, only numerical traffic statistical features that are consistently available in both datasets are retained. Specifically, this study first identifies the processed feature columns in CICIoT2023 and CICIoMT2024 and then extracts their intersection based on exact feature-name matching. Features that appear only in one dataset or are strongly dependent on a specific acquisition environment are excluded from this protocol. Finally, 38 shared numerical features are retained to construct a common feature space. The motivation of this protocol is to evaluate model robustness under a controlled and consistent tabular feature space. Its main assumption is that the retained shared features have comparable semantic meanings across the two datasets. Therefore, this protocol is suitable for controlled feature-aligned external validation, but it should not be interpreted as a universal cross-domain generalization setting.

Protocol 2 is the feature-union external validation with missing-feature indicators. Instead of retaining only the shared feature intersection, this protocol constructs the union of numerical feature columns from CICIoT2023 and CICIoMT2024. For features that are unavailable in one dataset, zero values are used as placeholders, and additional missingfeature indicator variables are introduced to explicitly represent feature availability. The motivation of this protocol is to examine whether the model remains robust when dataset specific feature-space differences are preserved to a larger extent. Compared with the 38-feature intersection protocol, this setting provides a less constrained validation protocol and helps evaluate whether the observed external validation performance depends heavily on manual shared-feature alignment.

Protocol 3 is the standardized NetFlow IoT external validation using NF-ToN-IoT as the source dataset and NF-BoT-IoT as the external target dataset. Both datasets are represented using standardized NetFlow V1 features, which provides an independent feature representation different from the CICIoT2023–CICIoMT2024 feature space. Af ter removing label and non-feature columns, this study retains the common numerical NetFlow features that are consistently available in both NF-ToN-IoT and NF-BoT-IoT. Finally, 10 common numerical NetFlow features are used in this additional validation experiment. The motivation of this protocol is to further examine model behavior on an independent standardized NetFlow-based IoT dataset pair, thereby complementing the CICIoT2023-to-CICIoMT2024 experiments.

Together, these three protocols evaluate FT-Transformer under controlled feature alignment, less constrained feature-union validation, and standardized NetFlow-based external validation. They are intended to provide controlled and reproducible empirical evidence for tabular traffic-based external validation. However, these protocols still do not constitute a universal traffic foundation model evaluation, and more scalable generalized traffic representation learning remains an important direction for future work.

## 3.5. CORAL-Based Domain Alignment Strategy

This study uses a domain-aligned FT-Transformer training strategy to examine whether explicit source-target representation alignment can improve cross-dataset robustness. Different from the source-only training setting, which optimizes the model only using labeled source-domain samples, the domain-aligned strategy jointly uses labeled source-domain samples and unlabeled target-domain samples during training. It should be emphasized that target-domain labels are not used in the alignment process; they are used only for the final evaluation on the held-out target test set.

Specifically, the FT-Transformer first maps both source-domain and target-domain samples into hidden representations through feature tokenization and Transformer encoder layers. The supervised classification loss is computed on the labeled source-domain samples, while an additional representation alignment loss is introduced to reduce the distribution discrepancy between source and target hidden representations. In this study, CORAL-based covariance alignment is used as a lightweight domain alignment objective. The total training objective is defined as the combination of the source-domain cross-entropy loss and the CORAL representation alignment loss:

$$
L _ {t o t a l} = L _ {C E} + \lambda L _ {C O R A L}\tag{9}
$$

where $L _ { C E }$ denotes the cross-entropy loss on the labeled source-domain samples, L denotes the covariance alignment loss between source and target hidden representations, and λ controls the strength of the alignment regularization.

The purpose of this experiment is not to build a large-scale traffic foundation model, but to provide an additional empirical analysis of whether explicit representation alignment can improve external validation performance compared with source-only FT-Transformer training. This setting also helps clarify that meaningful cross-dataset robustness may require not only a model architecture suitable for tabular feature modeling, but also a training objective designed to reduce source-target representation discrepancy.

## 3.6. SHAP-Based Interpretation Method

After model training, this study uses SHAP as an interpretation method to analyze the prediction results of FT-Transformer [11,19,20]. By selecting background samples and explanation samples, the contribution of each feature to the model output is calculated. Based on the SHAP values, this study further analyzes the influence direction and contribution magnitude of key traffic statistical features in attack classification, thereby improving the interpretability and credibility of the detection results.

## 4. Experimental Setup

## 4.1. Dataset and Task Setup

This study uses CICIoT2023 as the primary dataset for the main binary and multi-class classification experiments, and CICIoMT2024 as the external validation dataset for crossdataset generalization experiments [12,13]. In the main binary classification experiment, the training, validation, and test sets are all derived from the processed CICIoT2023 dataset. In the cross-dataset experiment, 38 shared features aligned between the primary and external datasets are used as the unified input feature space.

For the CICIoT2023 binary classification task, the processed dataset was divided into training, validation, and test sets containing 420,000, 60,000, and 120,000 samples, respectively. Each split was class-balanced, with equal numbers of attack and benign samples. Specifically, the training set contained 210,000 attack samples and 210,000 benign samples, the validation set contained 30,000 attack samples and 30,000 benign samples, and the test set contained 60,000 attack samples and 60,000 benign samples.

For the feature-aligned cross-dataset experiment, the aligned CICIoT2023 training, validation, and test sets contained 420,000, 60,000, and 120,000 samples, respectively. The external aligned CICIoMT2024 test set contained 1,612,117 samples, including 1,574,510 attack samples and 37,607 benign samples. This external test set was used only for evaluating cross-dataset generalization and was not involved in model training or validation.

For the CICIoT2023 multi-class classification task, the training, validation, and test sets contained 341,348, 48,765, and 97,529 samples, respectively. In this task, there is an obvious class imbalance among different attack categories. In the test set, most major categories, including Benign, DDoS, DoS, Mirai, and Spoofing, contain 16,000 samples, whereas Brute Force and Web-Based contain only 2613 and 1663 samples, respectively. This distribution characteristic increases the difficulty of minority-class recognition and leads to more pronounced performance differences across categories. In this study, experiments are mainly conducted under the original data distribution, and the class imbalance issue is further discussed as an important limitation and future research direction.

The detailed split statistics and class distribution statistics are provided in Supplementary Tables S2 and S3.

## 4.2. Evaluation Metrics

For the binary classification task, this study uses accuracy, precision, recall, F1-score, ROC-AUC, and PR-AUC as evaluation metrics, with particular attention paid to the attackclass F1-score. For the multi-class classification task, accuracy, macro-F1, and weighted-F1 are used as overall evaluation metrics, and the precision, recall, and F1-score of each category are further reported.

The evaluation metrics are defined as follows.

$$
P r e c i s i o n = \frac {T P}{T P + F P}\tag{10}
$$

$$
R e c a l l = \frac {T P}{T P + F N}\tag{11}
$$

$$
F 1 = \frac {2 \times \text { Precision } \times \text { Recall }}{\text { Precision } + \text { Recall }}\tag{12}
$$

$$
A c c u r a c y = \frac {T P + T N}{T P + T N + F P + F N}\tag{13}
$$

where TP, TN, FP, and FN denote the numbers of true positives, true negatives, false positives, and false negatives, respectively. In addition, ROC-AUC and PR-AUC are used for the binary classification task. ROC-AUC measures the overall discriminative ability of the model under different decision thresholds, while PR-AUC is particularly useful for evaluating detection performance under class imbalance.

## 4.3. Experimental Environment and Implementation Details

The experiments were conducted on a computer equipped with an NVIDIA GeForce RTX 3070 Ti Laptop GPU. PyCharm 2024.3.2 Community Edition was used as the development environment, Python 3.12.2 was used as the programming language, and PyTorch 2.7.0+cu128 was adopted as the deep learning framework. Scikit-learn 1.6.1, XGBoost 3.0.3, NumPy 2.2.2, and Pandas 2.2.3 were used for data preprocessing, baseline model implementation, and evaluation. In the main FT-Transformer binary classification experiment, the default configuration was set as follows: d\_token = 64, n\_layers = 4, dropout = 0.1, batch size = 2048, and learning rate $= 1 \times 1 0 ^ { - 3 }$ . An early stopping mechanism was used to select the best model during training [8]. The multi-class classification experiment used the same base model configuration to ensure consistency across experimental settings.

The main hyperparameter settings of FT-Transformer were determined with reference to the recommended configuration in the original study and were preliminarily adjusted according to the attack-class F1-score on the validation set. The lightweight ablation experiment in Section 5.6 further shows that the token dimension has only a limited influence on model performance within a certain range in the current task. Therefore, the adopted hyperparameter configuration is considered representative for the subsequent experiments.

For baseline comparison, Random Forest and XGBoost were implemented under fixed hyperparameter settings. For the main binary classification task, Random Forest used 300 estimators, no maximum depth limitation, parallel computation with n\_jobs = −1, and balanced subsampling class weights. XGBoost used 300 estimators, a maximum depth of $^ { 6 , }$ a learning rate of 0.1, a subsampling ratio of 0.8, a column sampling ratio of 0.8, the binary logistic objective, log-loss evaluation, and the histogram-based tree method. To reduce computational cost, the binary baseline experiments used at most 200,000 training samples and 100,000 test samples.

For the multi-class classification task, Random Forest used 300 estimators, no maxi mum depth limitation, min\_samples\_split = 2, and min\_samples\_leaf = 1. XGBoost used the multi:softprob objective, 350 estimators, a maximum depth of 8, a learning rate of 0.08, a subsampling ratio of 0.9, a column sampling ratio of 0.9, and mlogloss as the evaluation metric. For the cross-dataset baseline comparison, Random Forest used 300 estimators without maximum depth limitation, while XGBoost used 350 estimators, a maximum depth of $^ { 8 , }$ a learning rate of 0.08, a subsampling ratio of 0.9, and a column sampling ratio of 0.9. The baseline models were not extensively tuned; instead, they were used as strong conventional baselines under fixed and reproducible settings.

The hyperparameter settings of the Random Forest and XGBoost baselines are summarized in Table 1.

Table 1. Hyperparameter settings of Random Forest and XGBoost baselines.

<table><tr><td>Task</td><td>Model</td><td>Key Hyperparameters</td></tr><tr><td>Binary classification</td><td>Random Forest</td><td>n_estimators = 300; max_depth = None; class_weight = balanced_subsample; n_jobs = -1</td></tr><tr><td>Binary classification</td><td>XGBoost</td><td>n_estimators = 300; max_depth = 6; learning_rate = 0.1; subsample = 0.8; colsample_bytree = 0.8; objective = binary:logistic; eval_metric = logloss; tree_method = hist</td></tr><tr><td>Multi-class classification</td><td>Random Forest</td><td>n_estimators = 300; max_depth = None; min_samples_split = 2; min_samples_leaf = 1; n_jobs = -1</td></tr><tr><td>Multi-class classification</td><td>XGBoost</td><td>n_estimators = 350; max_depth = 8; learning_rate = 0.08; subsample = 0.9; colsample_bytree = 0.9; objective = multi:softprob; eval_metric = mlogloss</td></tr><tr><td>Cross-dataset binary</td><td>Random Forest</td><td>n_estimators = 300; max_depth = None; n_jobs = -1</td></tr></table>

## 5. Experimental Results and Analysis

## 5.1. Main Binary Classification Experiment Results

As shown in Table 2, FT-Transformer achieves strong performance in the binary classification task, indicating its ability to model complex interactions among statistical features of IoT network traffic. Meanwhile, Random Forest and XGBoost also achieve highly competitive results, with XGBoost slightly outperforming FT-Transformer in terms of accuracy, F1-score, and AUC-related metrics. This suggests that traditional tree-based models remain strong baselines for tabular IoT traffic-based attack detection tasks $[ 5 , 6 , 1 6 ] .$ Nevertheless, FT-Transformer still achieves performance close to these strong baselines, demonstrating that it can effectively capture complex feature relationships without relying on manually defined feature thresholds.

Table 2. Performance comparison of different models on the CICIoT2023 binary classification test set.

<table><tr><td>Model</td><td>Accuracy</td><td>Precision (Attack)</td><td>Recall (Attack)</td><td>F1 (Attack)</td><td>ROC-AUC</td><td>PR-AUC</td></tr><tr><td>FT-Transformer</td><td>0.980675</td><td>0.996283</td><td>0.964950</td><td>0.980366</td><td>0.995014</td><td>0.996027</td></tr><tr><td>Random Forest</td><td>0.981833</td><td>0.997145</td><td>0.966433</td><td>0.981549</td><td>0.995620</td><td>0.996261</td></tr><tr><td>XGBoost</td><td>0.982317</td><td>0.996160</td><td>0.968367</td><td>0.982066</td><td>0.996075</td><td>0.995997</td></tr></table>

To provide a more intuitive view of the classification behavior of the model on the binary test set, Figure 3 presents the confusion matrix of FT-Transformer on the CICIoT2023 binary classification test set.

As shown in Figure 3, the model shows strong recognition capability for both attack and benign samples. The number of correctly classified samples on the main diagonal is much larger than that in the off-diagonal regions, indicating stable overall classification performance. A closer inspection shows that most misclassifications are caused by a small number of attack samples being predicted as benign. This indicates that although the model maintains high overall detection performance, there remains some room for reducing false negatives. Nevertheless, the overall number of misclassified samples is relatively small.

In addition to the confusion matrix, the ROC curve is used to evaluate the overall discriminative ability of FT-Transformer under different decision thresholds, as shown in Figure 4.

![](images/9b1c83c3be9f580531c122ae2f19daabe000853c2009af58d44f8611f5a7b66d.jpg)  
Figure 3. Confusion matrix of FT-Transformer on the CICIoT2023 binary classification test set.

![](images/3fe261bfcaf0b0a779b53b517e9daadb640ebc28f4334d0a04719d804c8e0757.jpg)  
Figure 4. ROC curve of FT-Transformer on the CICIoT2023 binary classification test set. The dashed diagonal line represents the performance of a random classifier.

As shown in Figure 4, the ROC curve is clearly close to the upper-left corner, and the corresponding AUC value is high. This indicates that the model can effectively distinguish attack samples from benign samples under different threshold settings. This result is consistent with the ROC-AUC value reported in Table 2 and further confirms the overall discriminative capability of FT-Transformer in the binary classification task.

Considering that the balance between precision and recall is also important in network attack detection, the PR curve is further plotted, as shown in Figure 5.

![](images/2aab15b38ded669ca3a75c74166bb8bd8de15c07c116d5400f4e467e88a2517b.jpg)  
Figure 5. PR curve of FT-Transformer on the CICIoT2023 binary classification test set.

As shown in Figure 5, the model maintains a high precision–recall level over most threshold ranges, indicating that it can achieve a favorable balance between precision and recall during attack detection. This result suggests that FT-Transformer not only has strong overall discriminative ability but also shows practical applicability for binary IoT attack detection.

## 5.2. Analysis of the Training Process

The training process of FT-Transformer in the binary classification task was generally stable. The key validation results of FT-Transformer on the binary classification validation set are summarized in Table 3. According to the training history, the validation attack-class F1-score gradually increased from 0.9761 to 0.9804, while the validation ROC-AUC reached approximately 0.9952. These results indicate that the model converged steadily during training, without obvious training instability or severe overfitting.

Table 3. Key results of the FT-Transformer on the binary classification validation set.

<table><tr><td>Metric</td><td>Value</td></tr><tr><td>Best Val F1 (Attack)</td><td>0.980362</td></tr><tr><td>Best Val ROC-AUC</td><td>0.995214</td></tr><tr><td>Best Accuracy</td><td>0.980683</td></tr></table>

To further analyze the training stability and convergence behavior of FT-Transformer in the binary classification task, Figure 6 illustrates the changes in training loss, validation loss, and validation attack-class F1-score during the training process.

As shown in Figure 6, both the training loss and validation loss generally decrease as the number of training epochs increases, while the validation attack-class F1-score gradually rises and then becomes stable. This trend indicates that the model achieves good convergence in the binary classification task. In addition, no severe fluctuation or obvious overfitting is observed, which further supports the effectiveness of the adopted training strategy.

![](images/60913a27ab41d7b094cdd74aee4e85b3ec964a2c3e3b199c07f2e52ccfc56bad.jpg)  
Figure 6. Training history curve of FT-Transformer for binary classification.

## 5.3. Cross-Dataset Generalization Results

To further evaluate the generalization ability of the models under heterogeneous data distributions, cross-dataset experiments were conducted using 38 shared aligned features. FT-Transformer, Random Forest, and XGBoost were compared under the same aligned feature space, and the results are reported in Table 4.

Table 4. Cross-dataset test results for different models under aligned feature conditions.

<table><tr><td>Model</td><td>Test Setting</td><td>Accuracy</td><td>Precision (Attack)</td><td>Recall (Attack)</td><td>F1 (Attack)</td><td>ROC-AUC</td><td>PR-AUC</td></tr><tr><td>FT-Transformer</td><td>Main Aligned Test</td><td>0.979725</td><td>0.996567</td><td>0.962767</td><td>0.979375</td><td>0.993277</td><td>0.995185</td></tr><tr><td>FT-Transformer</td><td>External Test</td><td>0.985987</td><td>0.988173</td><td>0.997593</td><td>0.992860</td><td>0.987292</td><td>0.999671</td></tr><tr><td>Random Forest</td><td>Main Aligned Test</td><td>0.981733</td><td>0.996735</td><td>0.966633</td><td>0.981453</td><td>0.995119</td><td>0.996258</td></tr><tr><td>Random Forest</td><td>External Test</td><td>0.982120</td><td>0.983359</td><td>0.998592</td><td>0.990917</td><td>0.957204</td><td>0.998167</td></tr><tr><td>XGBoost</td><td>Main Aligned Test</td><td>0.982442</td><td>0.996365</td><td>0.968417</td><td>0.982192</td><td>0.995671</td><td>0.996778</td></tr><tr><td>XGBoost</td><td>External Test</td><td>0.980493</td><td>0.981103</td><td>0.999275</td><td>0.990105</td><td>0.885007</td><td>0.995419</td></tr></table>

As shown in Table 4, XGBoost and Random Forest slightly outperform FT-Transformer on the main aligned test set. Specifically, XGBoost achieves an attack-class F1-score of 0.982192, while Random Forest reaches 0.981453, both of which are higher than the 0.979375 obtained by FT-Transformer. This indicates that, in the main aligned test scenario where the data distribution is closer to the training distribution, traditional tree-based models still maintain strong fitting capability.

However, on the external dataset CICIoMT2024, the advantage of FT-Transformer becomes more evident. FT-Transformer achieves an attack-class F1-score of 0.992860, which is higher than that of Random Forest (0.990917) and XGBoost (0.990105). More importantly, FT-Transformer obtains a ROC-AUC of 0.987292, which is markedly higher than Random Forest (0.957204) and XGBoost (0.885007). These results suggest that although FT-Transformer is not the best-performing model on the main aligned test set, the feature representations learned through feature tokenization and self-attention are more robust under cross-dataset distribution shifts, leading to better generalization in the external validation scenario [14,15,18].

It is also worth noting that FT-Transformer achieves a higher attack-class F1-score on CICIoMT2024 than on the main aligned test set. This may be explained by two factors. First, within the current feature space composed of 38 shared features, the boundary between attack and benign samples in CICIoMT2024 may be relatively clearer, making the samples easier to distinguish. Second, the main aligned test set is derived from CICIoT2023, which contains more diverse attack types and more complex class boundaries, resulting in a slightly more difficult classification task. In addition, strict separation between the training and test sets was maintained in the cross-dataset experiments, thereby avoiding sample overlap between training and external testing.

A further comparison of ROC-AUC stability provides an important observation. For XGBoost, the ROC-AUC decreases from 0.9957 on the main aligned test set to 0.8850 on the external test set, corresponding to a decrease of 0.111. For Random Forest, the ROC-AUC decreases from 0.9951 to 0.9572, corresponding to a decrease of 0.038. In contrast, the ROC-AUC of FT-Transformer decreases only from 0.9933 to 0.9873, with a decrease of 0.006. Although the three models achieve very similar ROC-AUC values on the main aligned test set, their performance diverges substantially on the external dataset.

This phenomenon indicates that traditional tree-based models have strong fitting capability within a single dataset, but their decision mechanisms based on feature threshold splitting may be more sensitive to distribution shifts. In contrast, FT-Transformer models global interactions among features through self-attention, and the learned feature representations show stronger robustness when facing cross-dataset distribution changes. Therefore, the stability of ROC-AUC under cross-dataset evaluation is one of the key findings of this study.

## 5.4. Analysis ofMulti-Classification Results

For the multi-class classification task, the overall performance of FT-Transformer is compared with Random Forest and XGBoost under the same dataset setting. The results are reported in Table 5.

Table 5. Overall performance comparison of different models on the CICIoT2023 multi-class classifi cation task.

<table><tr><td>Model</td><td>Accuracy</td><td>Macro-F1</td><td>Weighted-F1</td></tr><tr><td>FT-Transformer</td><td>0.809554</td><td>0.724006</td><td>0.806680</td></tr><tr><td>Random Forest</td><td>0.825642</td><td>0.749090</td><td>0.823973</td></tr><tr><td>XGBoost</td><td>0.841678</td><td>0.772167</td><td>0.840083</td></tr></table>

As shown in Table 5, FT-Transformer achieves an accuracy of 0.809554, a macro-F1 score of 0.724006, and a weighted-F1 score of 0.806680. In comparison, Random Forest achieves 0.825642, 0.749090, and 0.823973, respectively, while XGBoost further improves these values to 0.841678, 0.772167, and 0.840083. These results indicate that traditional treebased models still exhibit stronger overall classification capability in the current multi-class task, with XGBoost achieving the best performance across all three metrics.

Further category-wise analysis shows that the difficulty of identifying different attack categories varies substantially. For Random Forest, the F1-score of the Mirai category reaches 0.9983, and the DoS, Spoofing, and DDoS categories also achieve relatively strong performance.

However, the F1-scores of Brute Force and Web-Based are only 0.5441 and 0.4329, respectively. For XGBoost, the Mirai category also achieves near-perfect recognition, while the performance of DoS, Spoofing, and DDoS is further improved. The F1-scores of Brute Force and Web-Based increase to 0.5798 and 0.4939, respectively. This phenomenon suggests that the main challenges in the multi-class classification task are concentrated in minority or weak categories with smaller sample sizes and more complex class boundaries.

Overall, FT-Transformer does not outperform the traditional tree-based models in the multi-class classification task, but it still achieves competitive results. This indicates that tree-based models remain highly effective for multi-class tabular traffic classification, whereas the main research value of FT-Transformer lies in its unified deep tabular modeling framework, cross-dataset generalization potential, and compatibility with interpretability analysis.

To further examine the detailed performance of FT-Transformer across different attack categories, Table 6 reports the category-wise precision, recall, F1-score, and support on the multi-class test set.

Table 6. Category-wise performance of FT-Transformer on the multi-class test set.

<table><tr><td>Class</td><td>Precision</td><td>Recall</td><td>F1-Score</td><td>Support</td></tr><tr><td>Benign</td><td>0.6842</td><td>0.8366</td><td>0.7528</td><td>16,000</td></tr><tr><td>Brute Force</td><td>0.7220</td><td>0.4114</td><td>0.5241</td><td>2613</td></tr><tr><td>DDoS</td><td>0.9350</td><td>0.7231</td><td>0.8155</td><td>16,000</td></tr><tr><td>DoS</td><td>0.7747</td><td>0.9506</td><td>0.8537</td><td>16,000</td></tr><tr><td>Mirai</td><td>0.9984</td><td>0.9979</td><td>0.9982</td><td>16,000</td></tr><tr><td>Recon</td><td>0.7036</td><td>0.7152</td><td>0.7094</td><td>13,253</td></tr><tr><td>Spoofing</td><td>0.8450</td><td>0.7371</td><td>0.7873</td><td>16,000</td></tr><tr><td>Web-Based</td><td>0.4538</td><td>0.2862</td><td>0.3510</td><td>1663</td></tr></table>

As shown in Table 6, the multi-class classification task is substantially more challenging than the binary classification task. Although the overall accuracy exceeds 0.80, the macro-F1 score is only 0.724006, indicating noticeable performance differences among categories. Among all categories, Mirai achieves the best performance, with an F1-score of 0.9982. DoS and DDoS also achieve relatively high F1-scores of 0.8537 and 0.8155, respectively. In contrast, the Web-Based and Brute Force categories show weaker results, with F1-scores of 0.3510 and 0.5241, respectively. This suggests that FT-Transformer still has room for improvement when dealing with categories that have fewer samples or more complex decision boundaries.

To provide a more detailed analysis of the confusion relationships among different attack categories, Figure 7 presents the confusion matrix of FT-Transformer on the multiclass test set.

As shown in Figure 7, the recognition difficulty differs substantially across categories. Categories such as Mirai, DoS, and DDoS have a large number of samples located on the main diagonal, indicating that the model can recognize these categories effectively. In contrast, Web-Based, Brute Force, and some Recon and Spoofing samples are more likely to be confused with other categories. This observation is consistent with the category-wise results in Table 6, further confirming that the main difficulty of the multi-class task lies in categories with smaller sample sizes or more complex class boundaries.

In the multi-class classification task, the stability of the training process is also important. Therefore, the training history curve of FT-Transformer is further plotted, as shown in Figure 8.

As shown in Figure 8, both the training loss and validation loss generally decrease as training progresses, while the validation macro-F1 score gradually increases and then stabilizes in the later stages. This indicates that FT-Transformer also shows a stable con vergence trend in the multi-class classification task. Although the overall performance of the multi-class task is lower than that of the binary classification task, the training process remains relatively stable, without obvious training imbalance or severe overfitting.

Multi-Class Classification Confusion Matrix  
![](images/c5b8fa5c8de6e16ce6332975a3f543061008521e924c559872675a9d2216f047.jpg)  
Figure 7. Confusion matrix of FT-Transformer on the multi-class test set.

FT-Transformer Multi-class Training History  
![](images/0f80fd8e01a62f90426a0382b0abed6d5e85cb63d92254404dc1eea46f0c5d1f.jpg)  
Figure 8. FT-Transformer multi-classification training history curve.

## 5.5. SHAP Explainability Analysis

To explain the decision basis of FT-Transformer, this study employs SHAP to conduct global and local interpretability analyses of the model [11,19,20]. The global SHAP feature importance ranking is first presented in Figure 9.

![](images/efda933af6ffe68d08dcab7d0ec4eaabea00efd8ae69d7a7a36d2ac17c049af1.jpg)  
Figure 9. SHAP global feature importance bar chart.

Figure 9 shows the global feature importance ranking obtained from the SHAP analysis. As shown in Figure 9, features such as Number, HTTPS, Header\_Length, Rate, and AVG have relatively high importance scores. This indicates that the model mainly relies on traffic volume, protocol behavior, and packet header statistics when distinguishing attack traffic from benign traffic. The result also shows that FT-Transformer does not depend on a single feature for classification; instead, it extracts discriminative information from multiple key statistical traffic features.

From a cybersecurity perspective, the high importance of the Number feature is consistent with the behavior of DDoS and DoS attacks, which often generate large volumes of packets to overwhelm the target and therefore lead to abnormal traffic counts. The high ranking of HTTPS suggests that some attack traffic may exhibit statistical differences in protocol usage compared with normal encrypted traffic, which can be captured by the model. Header\_Length reflects packet header structure information, and attack traffic may show abnormal statistical patterns when constructing abnormal headers, manipulating payloads, or forging communication characteristics. These observations indicate that the key features used by FT-Transformer have meaningful semantic connections with known traffic behaviors of network attacks, thereby enhancing the credibility of the model’s classification results.

Based on the global feature importance analysis, the SHAP summary plot is used to show how different feature values influence the model output, as shown in Figure 10.

As shown in Figure 10, high and low values of different features influence the model output in different directions. For example, high values of some features push samples toward the attack category, whereas low values of other features may contribute to benign classification. This indicates that the decision process of FT-Transformer is based on the joint modeling of multiple traffic features rather than a simple fixed-threshold rule. Therefore, the SHAP analysis provides additional evidence that FT-Transformer makes decisions based on the joint contribution of multiple traffic features while maintaining a certain degree of interpretability.

To further complement the global SHAP analysis, this study provides local SHAP explanations for two representative samples, including one correctly classified attack sample and one attack sample misclassified as benign. The results are shown in Figure 11.

In the correctly classified attack sample, the predicted attack-class probability reaches 1.0000. The local explanation shows that Number, HTTPS, Rate, and Header\_Length make strong positive contributions to the attack-class probability, among which Number provides the largest positive contribution. This indicates that the model successfully captures abnormal traffic-volume and packet-structure characteristics for this sample.

In contrast, for the attack sample misclassified as benign, the predicted attackclass probability decreases to 0.0016. In this case, features such as Number, HTTPS, Header\_Length, AVG, Time\_To\_Live, and SSH contribute negatively to the attack-class probability, while only a few features, such as UDP and ack\_flag\_number, provide limited positive contributions. This suggests that the local feature pattern of this attack sample is closer to benign traffic, resulting in a false negative prediction.

These local explanations show that the FT-Transformer decision is not determined by a single feature or a fixed threshold, but by the combined effects of multiple traffic statistical features. They also help explain why false negatives may occur when the local feature pattern of an attack sample resembles benign traffic. Therefore, the local SHAP analysis complements the global feature importance analysis and improves the transparency of the model’s decision-making process.

## 5.6. Analysis of Lightweight Ablation Experiments

To analyze the sensitivity of FT-Transformer to key architectural hyperparameters, this study first conducted a lightweight ablation experiment on the token dimension d\_token. The binary classification results under different token dimensions are reported in Table 7.

Table 7. Binary classification ablation results of FT-Transformer under different token dimensions.

<table><tr><td>Trial</td><td>d_Token</td><td>Best Validation F1-Score</td><td>Test Accuracy</td><td>Test F1-Score</td><td>Test ROC-AUC</td><td>Test PR-AUC</td></tr><tr><td>dtoken_32</td><td>32</td><td>0.979939</td><td>0.980117</td><td>0.979787</td><td>0.994664</td><td>0.996027</td></tr><tr><td>dtoken_64 (main setting)</td><td>64</td><td>0.980400</td><td>0.980675</td><td>0.980366</td><td>0.995014</td><td>0.996261</td></tr><tr><td>dtoken_128</td><td>128</td><td>0.980110</td><td>0.980008</td><td>0.979650</td><td>0.994623</td><td>0.995997</td></tr></table>

As shown in Table 7, the main setting with d\_token = 64 achieves the best test performance among the three token-dimension settings, with a test accuracy of 0.980675, an attack-class F1-score of 0.980366, a ROC-AUC of 0.995014, and a PR-AUC of 0.996261. The differences among d\_token = 32, 64, and 128 are very small, indicating that FT-Transformer is not highly sensitive to the token dimension in the current binary classification task. This suggests that model performance is influenced more by the overall separability of the traffic features and the inherent difficulty of the task than by token dimension alone.

![](images/54f3e72b1c0aa8c516f326cb53990cd5a72a086aaa0423c0ce730292ef7d70d3.jpg)  
Figure 10. SHAP summary plot.

![](images/53d292d0afdce575983a7ee29ff4f547481a1ea628e613bebcda11fe0a76b7c9.jpg)

![](images/9915b710c7bf0dca467b9d34f0ec519200b3e6a877d9416124a57d5bf4f8dc4d.jpg)  
Figure 11. Local SHAP explanations for representative correctly classified and misclassified attack samples. Red bars indicate features that increase the attack-class probability, while blue bars indicate features that decrease the attack-class probability. Subfigure (a) shows a correctly classified attack sample with P(attack) = 1.0000, whereas subfigure (b) shows an attack sample misclassified as benign with P(attack) = 0.0016. The displayed feature values correspond to the preprocessed numerical inputs used by the model.

To further respond to the need for a more comprehensive architectural analysis, this study additionally evaluates the influence of the number of Transformer encoder layers and attention heads. Specifically, the encoder depth was varied by setting n\_layers to two, four, and six, while the number of attention heads was varied by setting n\_heads to two, four, and eight. The main configuration, d\_token = 64, n\_layers = 4, and n\_heads = 4, was used as the reference setting. The extended ablation results are shown in Table 8.

Table 8. Extended ablation results under different numbers of encoder layers and attention heads.

<table><tr><td>Trial</td><td>dToken</td><td>n_Layers</td><td>n_Heads</td><td>Best Val F1</td><td>Test Accuracy</td><td>Test F1</td><td>Test ROC-AUC</td><td>Test PR-AUC</td></tr><tr><td>main_layers_4_heads_4</td><td>64</td><td>4</td><td>4</td><td>0.980400</td><td>0.980675</td><td>0.980366</td><td>0.995014</td><td>0.996261</td></tr><tr><td>layers_2_heads_4</td><td>64</td><td>2</td><td>4</td><td>0.979876</td><td>0.979608</td><td>0.979331</td><td>0.994670</td><td>0.996022</td></tr><tr><td>layers_6_heads_4</td><td>64</td><td>6</td><td>4</td><td>0.979810</td><td>0.979917</td><td>0.979545</td><td>0.994527</td><td>0.995923</td></tr><tr><td>layers_4_heads_2</td><td>64</td><td>4</td><td>2</td><td>0.979845</td><td>0.980142</td><td>0.979776</td><td>0.994659</td><td>0.996030</td></tr><tr><td>layers_4_heads_8</td><td>64</td><td>4</td><td>8</td><td>0.979620</td><td>0.980108</td><td>0.979755</td><td>0.994841</td><td>0.996135</td></tr></table>

As shown in Table 8, reducing the number of encoder layers to two or increasing it to six does not improve the test performance compared with the main setting. The test F1-score reaches 0.979331 when n\_layers = 2 and 0.979545 when n\_layers = 6, both slightly lower than the main configuration. Similarly, changing the number of attention heads also leads to only limited performance variation. The test F1-score is 0.979776 when n\_heads = 2 and 0.979755 when n\_heads = 8, which remains close to but below the main setting.

Overall, the ablation results indicate that the current FT-Transformer configuration is relatively stable within a reasonable range of token dimensions, encoder depths, and attention-head settings. Simply increasing the model scale by using more encoder layers or more attention heads does not necessarily lead to better performance. Therefore, future improvements should focus less on blindly increasing architectural complexity and more on enhancing representation robustness, handling class imbalance, and improving weak category recognition in multi-class intrusion detection.

To further visualize the influence of token dimension on model performance, Figure 12 compares the validation F1-score and test F1-score under different d\_token settings.

FT-Transformer Binary Ablation Summary  
![](images/bfd4167fa1faa9f4fb0d4060ea45f030a171026f0e6e469dd5cd8ebef7427059.jpg)  
Figure 12. Comparison of F1 scores on the validation and test sets under different token dimensions.

As shown in Figure 12, the validation F1-score and test F1-score under $d \_ t o k e n = 3 2 ,$ 64, and 128 are very close to each other, and no substantial performance fluctuation is observed across the three settings. Although d\_token = 128 achieves the highest validation F1-score, its advantage over the other two settings is marginal, and the corresponding test performance does not show a significant improvement.

This result further confirms that, for the current task, FT-Transformer is not highly sensitive to changes in token dimension. Therefore, the proposed model maintains relatively stable performance within a reasonable token-dimension range, which also supports the reliability of the selected hyperparameter configuration in this study.

## 5.7. Statistical Significance Analysis

Because the performance differences among FT-Transformer, Random Forest, and XGBoost on the CICIoT2023 binary classification task are relatively small, McNemar’s test was further conducted to examine whether the paired prediction differences between models were statistically significant. The test was performed on the same CICIoT2023 binary test set, containing 120,000 samples, using the prediction results of FT-Transformer, Random Forest, and XGBoost under the same feature space.

The model performance values used for the statistical test are consistent with the binary classification results reported in Table 1. As shown in Table 9, the difference between FT-Transformer and Random Forest is statistically significant, with a McNemar chi-square value of 29.163859 and a p-value of $6 . 6 5 \times 1 0 ^ { - 8 }$ . Similarly, the difference between FT-Transformer and XGBoost is also statistically significant, with a McNemar chi-square value of 59.375580 and a p-value of $1 . 3 0 \times 1 0 ^ { - 1 4 }$ . The difference between Random Forest and XGBoost is also significant at the 0.05 level, with a p-value of 0.011118.

Table 9. McNemar’s test results for pairwise model comparison on the CICIoT2023 binary test set.

<table><tr><td>Model A</td><td>Model B</td><td>Accuracy A</td><td>Accuracy B</td><td>b</td><td>c</td><td>McNemar  $\chi^2$ </td><td>p -Value</td><td>Significant at 0.05</td></tr><tr><td>FT-Transformer</td><td>Random Forest</td><td>0.980675</td><td>0.981833</td><td>257</td><td>396</td><td>29.163859</td><td> $6.65 \times 10^{-8}$ </td><td>Yes</td></tr><tr><td>FT-Transformer</td><td>XGBoost</td><td>0.980675</td><td>0.982317</td><td>225</td><td>422</td><td>59.375580</td><td> $1.30 \times 10^{-14}$ </td><td>Yes</td></tr><tr><td>Random Forest</td><td>XGBoost</td><td>0.981833</td><td>0.982317</td><td>223</td><td>281</td><td>6.446429</td><td>0.011118</td><td>Yes</td></tr></table>

Note: b denotes the number of samples correctly classified by Model A but incorrectly classified by Model B, while c denotes the number of samples incorrectly classified by Model A but correctly classified by Model B.

These results indicate that, although the numerical differences among the three models are small, the paired prediction differences are statistically significant on the large-scale binary test set. In particular, Random Forest and XGBoost slightly but significantly outperform FT-Transformer on the primary in-dataset binary task. This finding further supports the positioning of this study: FT-Transformer should not be interpreted as uniformly superior to traditional tree-based baselines on the primary dataset; rather, its main value lies in providing competitive in-dataset performance and improved robustness under feature-aligned external validation.

## 5.8. Evaluation ofModern Tabular Baselines

This study evaluates several modern tabular learning baselines, including MLP, Tab-Net, and a TabTransformer-style numerical Transformer baseline. Since the traffic features used in this study are mainly numerical statistical features rather than categorical fields, the TabTransformer-style model is implemented as a numerical Transformer baseline adapted to the current input format, instead of a direct reproduction of the original categoricalfeature-based TabTransformer architecture. These models are compared under both the original CICIoT2023 binary classification setting and the 38-feature aligned external validation setting. The results are shown in Table 10.

Table 10. Comparison with additional modern tabular learning baselines.

<table><tr><td>Scenario</td><td>Model</td><td>Eval Set</td><td>Accuracy</td><td>F1_Attack</td><td>ROC-AUC</td><td>PR-AUC</td></tr><tr><td>CICloT2023 Binary</td><td>MLP</td><td>Main Test</td><td>0.979542</td><td>0.979142</td><td>0.993856</td><td>0.995383</td></tr><tr><td>CICloT2023 Binary</td><td>TabTransformer-style</td><td>Main Test</td><td>0.979042</td><td>0.978687</td><td>0.994354</td><td>0.995798</td></tr><tr><td>CICloT2023 Binary</td><td>TabNet</td><td>Main Test</td><td>0.979850</td><td>0.979466</td><td>0.993581</td><td>0.995251</td></tr><tr><td>Feature-Aligned External Validation</td><td>MLP</td><td>External Test</td><td>0.678953</td><td>0.805735</td><td>0.725747</td><td>0.989195</td></tr><tr><td>Feature-Aligned External Validation</td><td>TabTransformer-style</td><td>External Test</td><td>0.977376</td><td>0.988539</td><td>0.961118</td><td>0.998986</td></tr><tr><td>Feature-Aligned External Validation</td><td>TabNet</td><td>External Test</td><td>0.930358</td><td>0.963497</td><td>0.488869</td><td>0.948149</td></tr></table>

Note: FT-Transformer results from the corresponding main binary classification and feature-aligned external validation experiments are used as the reference results. The additional baselines were trained using the same 200,000-sample training subset for computational feasibility.

On the CICIoT2023 binary test set, the three additional baselines achieve competitive performance. The MLP, TabTransformer-style model, and TabNet obtain ROC-AUC values of 0.993856, 0.994354, and 0.993581, respectively. These results are close to but slightly lower than the corresponding main FT-Transformer result. This indicates that modern tabular deep learning models can effectively model IoT traffic statistical features, but their advantage over strong tree-based models remains limited in the in-dataset setting.

Under the 38-feature aligned external validation setting, the TabTransformer-style model achieves a relatively strong external ROC-AUC of 0.961118 and an attack-class F1-score of 0.988539. However, its external ROC-AUC remains lower than that of FT Transformer under the same 38-feature aligned external validation setting. In contrast, MLP and TabNet show weaker external ROC-AUC values. These results further indicate that Transformer-based tabular models can be useful for feature-aligned external validation, but their performance varies considerably across architectures.

## 5.9. Additional Feature-Union External Validation

The feature-union external validation setting is designed to examine whether the observed external validation behavior depends on the shared-feature intersection protocol. Instead of retaining only the common feature intersection between CICIoT2023 and CICIoMT2024, this protocol uses the union of numerical feature columns from both datasets. Features missing from one dataset are filled with zero values, and additional missing-feature indicator variables are added to explicitly represent feature availability. This protocol results in 92 input dimensions and provides a less restrictive evaluation setting than the 38-feature intersection protocol. The results are shown in Table 11.

Table 11. Additional feature-union external validation with missing-feature indicators.

<table><tr><td>Model</td><td>Eval Set</td><td>Accuracy</td><td>F1_Attack</td><td>ROC-AUC</td><td>PR-AUC</td><td>Training Time (s)</td><td>Inference ms/Sample</td></tr><tr><td>Random Forest</td><td>Main Test</td><td>0.981650</td><td>0.981358</td><td>0.995539</td><td>0.996525</td><td>13.681739</td><td>0.005919</td></tr><tr><td>Random Forest</td><td>External Test</td><td>0.984229</td><td>0.991978</td><td>0.871547</td><td>0.995103</td><td>13.681739</td><td>0.004760</td></tr><tr><td>XGBoost</td><td>Main Test</td><td>0.982375</td><td>0.982129</td><td>0.996010</td><td>0.996961</td><td>1.985035</td><td>0.000821</td></tr><tr><td>XGBoost</td><td>External Test</td><td>0.982822</td><td>0.991272</td><td>0.971213</td><td>0.999088</td><td>1.985035</td><td>0.000698</td></tr><tr><td>MLP</td><td>Main Test</td><td>0.979658</td><td>0.979263</td><td>0.993911</td><td>0.995423</td><td>20.072872</td><td>0.000207</td></tr><tr><td>MLP</td><td>External Test</td><td>0.675541</td><td>0.803383</td><td>0.652072</td><td>0.982731</td><td>20.072872</td><td>0.000195</td></tr><tr><td>FT-Transformer</td><td>Main Test</td><td>0.978442</td><td>0.978014</td><td>0.993280</td><td>0.995081</td><td>347.975249</td><td>0.026886</td></tr><tr><td>FT-Transformer</td><td>External Test</td><td>0.983026</td><td>0.991340</td><td>0.527226</td><td>0.955529</td><td>347.975249</td><td>0.026950</td></tr></table>

On the main CICIoT2023 test set, Random Forest and XGBoost still achieve the strongest overall performance, with ROC-AUC values of 0.995539 and 0.996010, respectively. FT-Transformer obtains a ROC-AUC of 0.993280 and an attack-class F1-score of 0.978014, which are slightly lower than those of the tree-based baselines. This confirms that traditional tree-based models remain highly competitive for tabular traffic statistical features.

On the external CICIoMT2024 test set, the feature-union protocol reveals an important limitation. Although FT-Transformer obtains a high attack-class F1-score of 0.991340, its ROC-AUC decreases to 0.527226. This indicates that the model can still produce many correct threshold-based predictions on the highly imbalanced external test set, but its overall ranking and discrimination ability are not stable under the feature-union setting. In contrast, XGBoost achieves the best external ROC-AUC of 0.971213 under this protocol, suggesting stronger ranking stability in this less constrained feature representation.

These results suggest that the previously observed advantage of FT-Transformer should be interpreted conservatively. FT-Transformer demonstrates promising ROC-AUC stability under the controlled 38-feature aligned validation setting, but this advantage does not necessarily transfer to the less constrained feature-union protocol. Therefore, this study does not claim genuine universal cross-dataset generalization. Instead, the results support a more limited conclusion: FT-Transformer is competitive under controlled feature-aligned validation, whereas more scalable cross-dataset traffic representation learning remains an important future direction.

## 5.10. Additional Validation on Standardized NetFlow IoT Datasets

A standardized NetFlow IoT external validation setting is used to evaluate model behavior on an independent dataset pair with a different feature representation. Specif ically, NF-ToN-IoT is used as the training source dataset, and NF-BoT-IoT is used as an independent external test dataset. Both datasets are represented using standardized Net

Flow V1 features, which provides a common feature representation without relying on the CICIoT2023–CICIoMT2024 shared-feature intersection. The experiment includes Random Forest, XGBoost, MLP, FT-Transformer, and a TabTransformer-style numerical Transformer baseline. The results are shown in Table 12. Although NetFlow V1 datasets provide a standardized feature representation, this study retained only the common numerical features that were consistently available in both NF-ToN-IoT and NF-BoT-IoT after removing label and non-feature columns. Finally, 10 common numerical NetFlow features were used in this validation experiment.

Table 12. Additional external validation on standardized NetFlow IoT datasets.

<table><tr><td>Model</td><td>Eval Set</td><td>Accuracy</td><td>F1_Attack</td><td>ROC-AUC</td><td>PR-AUC</td><td>Training Time (s)</td><td>Inference ms/Sample</td></tr><tr><td>Random Forest</td><td>NF-ToN-IoT internal test</td><td>0.999083</td><td>0.999430</td><td>0.999887</td><td>0.999946</td><td>8.871812</td><td>0.003000</td></tr><tr><td>Random Forest</td><td>NF-BoT-IoT external test</td><td>0.287940</td><td>0.427172</td><td>0.517249</td><td>0.981737</td><td>8.871812</td><td>0.002311</td></tr><tr><td>XGBoost</td><td>NF-ToN-IoT internal test</td><td>0.999075</td><td>0.999425</td><td>0.999986</td><td>0.999997</td><td>0.758246</td><td>0.000755</td></tr><tr><td>XGBoost</td><td>NF-BoT-IoT external test</td><td>0.250607</td><td>0.382734</td><td>0.534526</td><td>0.980331</td><td>0.758246</td><td>0.000667</td></tr><tr><td>MLP</td><td>NF-ToN-IoT internal test</td><td>0.985417</td><td>0.991009</td><td>0.997656</td><td>0.999305</td><td>19.386569</td><td>0.000123</td></tr><tr><td>MLP</td><td>NF-BoT-IoT external test</td><td>0.167322</td><td>0.259150</td><td>0.674060</td><td>0.986717</td><td>19.386569</td><td>0.000139</td></tr><tr><td>FT-Transformer</td><td>NF-ToN-IoT internal test</td><td>0.985558</td><td>0.991093</td><td>0.997890</td><td>0.999459</td><td>68.442232</td><td>0.004044</td></tr><tr><td>FT-Transformer</td><td>NF-BoT-IoT external test</td><td>0.649392</td><td>0.782564</td><td>0.785781</td><td>0.993169</td><td>68.442232</td><td>0.004075</td></tr><tr><td>TabTransformer-style</td><td>NF-ToN-IoT internal test</td><td>0.991975</td><td>0.995022</td><td>0.998864</td><td>0.999575</td><td>48.557839</td><td>0.003146</td></tr><tr><td>TabTransformer-style</td><td>NF-BoT-IoT external test</td><td>0.524743</td><td>0.683403</td><td>0.639132</td><td>0.988211</td><td>48.557839</td><td>0.003142</td></tr></table>

Note: For computational feasibility, all models were trained using 200,000 stratified samples from the NF-ToN-IoT training split and evaluated on the internal NF-ToN-IoT test set and the full NF-BoT-IoT external test set.

On the NF-ToN-IoT internal test set, Random Forest and XGBoost achieve near-perfect performance, with F1-scores above 0.999 and ROC-AUC values close to 1.000. This indicates that tree-based models still have very strong fitting capability when the training and test data come from the same NetFlow dataset. The deep tabular models, including MLP, FT-Transformer, and TabTransformer-style, also achieve high internal test performance, but their scores are slightly lower than those of the tree-based baselines.

However, the results on the NF-BoT-IoT external test set reveal a clear distributionshift effect. The performance of Random Forest and XGBoost decreases substantially, with external ROC-AUC values of 0.517249 and 0.534526, respectively. In contrast, FT-Transformer achieves the best external validation performance among all compared models, with an accuracy of 0.649392, an attack-class F1-score of 0.782564, a ROC-AUC of 0.785781, and a PR-AUC of 0.993169. The TabTransformer-style model also performs better than the tree-based baselines in terms of external F1-score, but its external ROC-AUC remains lower than that of FT-Transformer.

These additional NetFlow-based results provide further evidence that Transformerbased tabular models may offer stronger robustness than traditional tree-based methods under certain external validation scenarios. At the same time, the substantial performance degradation from the internal test set to the external test set confirms that cross-dataset intrusion detection remains challenging, even when standardized NetFlow features are used. Therefore, this experiment supports a more balanced conclusion: FT-Transformer can be competitive and sometimes more robust under external validation, but it should not be interpreted as a universal solution to cross-dataset generalization.

## 5.11. Domain-Aligned FT-Transformer Training

A domain-aligned FT-Transformer training strategy based on CORAL representation alignment is evaluated to examine whether explicit source-target representation alignment can improve external validation performance. Different from the source-only training setting, the domain-aligned strategy jointly uses labeled source-domain samples and unlabeled target-domain samples during training. The target-domain labels are not used for optimization; they are used only for final evaluation on the held-out target test set. The results are shown in Table 13.

Table 13. Comparison between source-only and domain-aligned FT-Transformer.

<table><tr><td>Scenario</td><td>Training Strategy</td><td>Eval Set</td><td>Accuracy</td><td>F1_Attack</td><td>ROC-AUC</td><td>PR-AUC</td></tr><tr><td>CICIoT2023-to-CICIoMT2024</td><td>Source-onlyFT-Transformer</td><td>CICIoT2023 internal aligned test</td><td>0.978958</td><td>0.978592</td><td>0.993191</td><td>0.995115</td></tr><tr><td>CICIoT2023-to-CICIoMT2024</td><td>Source-onlyFT-Transformer</td><td>CICIoMT2024held-out target test</td><td>0.978024</td><td>0.988864</td><td>0.914362</td><td>0.997600</td></tr><tr><td>CICIoT2023-to-CICIoMT2024</td><td>Domain-aligned FT-Transformer-CORAL</td><td>CICIoT2023 internal aligned test</td><td>0.979000</td><td>0.978596</td><td>0.993174</td><td>0.995084</td></tr><tr><td>CICIoT2023-to-CICIoMT2024</td><td>Domain-aligned FT-Transformer-CORAL</td><td>CICIoMT2024held-out target test</td><td>0.976548</td><td>0.988128</td><td>0.989185</td><td>0.999739</td></tr><tr><td>NF-ToN-IoT-to-NF-BoT-IoT</td><td>Source-onlyFT-Transformer</td><td>NF-ToN-IoT internal test</td><td>0.985792</td><td>0.991233</td><td>0.998027</td><td>0.999452</td></tr><tr><td>NF-ToN-IoT-to-NF-BoT-IoT</td><td>Source-onlyFT-Transformer</td><td>NF-BoT-IoT held-out target test</td><td>0.322113</td><td>0.470034</td><td>0.725706</td><td>0.991274</td></tr><tr><td>NF-ToN-IoT-to-NF-BoT-IoT</td><td>Domain-aligned FT-Transformer-CORAL</td><td>NF-ToN-IoT internal test</td><td>0.985925</td><td>0.991317</td><td>0.998240</td><td>0.999545</td></tr><tr><td>NF-ToN-IoT-to-NF-BoT-IoT</td><td>Domain-aligned FT-Transformer-CORAL</td><td>NF-BoT-IoT held-out target test</td><td>0.413491</td><td>0.572263</td><td>0.777260</td><td>0.993027</td></tr></table>

Note: In the domain-aligned setting, unlabeled target-domain samples were used only for representation align ment, while target labels were used only for held-out target test evaluation. The CORAL loss weight was set to λ = 0.05.

For the CICIoT2023-to-CICIoMT2024 setting, the source-only FT-Transformer achieves a ROC-AUC of 0.914362 on the CICIoMT2024 held-out target test set. After introducing CORAL-based representation alignment, the external ROC-AUC increases to 0.989185, and the PR-AUC also increases from 0.997600 to 0.999739. Although the external accuracy and attack-class F1-score decrease slightly, the substantial improvement in ROC-AUC indicates that representation alignment improves the model’s ranking and discrimination ability under target-domain distribution shift.

For the NF-ToN-IoT-to-NF-BoT-IoT setting, the domain-aligned FT-Transformer also improves the external validation results. Compared with the source-only FT-Transformer, the CORAL-based model increases the external accuracy from 0.322113 to 0.413491, the attack-class F1-score from 0.470034 to 0.572263, the ROC-AUC from 0.725706 to 0.777260, and the PR-AUC from 0.991274 to 0.993027. Meanwhile, the internal NF-ToN-IoT test performance remains stable, suggesting that the alignment objective does not substantially damage source-domain classification performance.

These results suggest that meaningful cross-dataset robustness cannot be achieved solely by changing the classifier architecture. Instead, training objectives that explicitly reduce source-target representation discrepancy can provide additional benefits for external validation. Therefore, the domain-aligned FT-Transformer experiment provides a more direct response to the question of what training methodology may help improve crossdataset robustness in tabular traffic-based intrusion detection.

## 6. Discussion

The experimental results highlight the importance of evaluating cross-dataset robustness under multiple validation protocols. In the external validation on CICIoMT2024, the ROC-AUC of FT-Transformer decreases only from 0.993 on the main aligned test set to 0.987 on the external test set, corresponding to a decrease of 0.006. In contrast, the ROC-AUC of XGBoost decreases from 0.996 to 0.885, with a decrease of 0.111, while that of Random Forest decreases from 0.995 to 0.957. These results indicate that although tra ditional tree-based models have strong fitting capability within a single dataset, they are more sensitive to feature distribution shifts than FT-Transformer. The main empirical value of FT-Transformer lies in its ROC-AUC stability under the controlled 38-feature aligned external validation setting. However, the additional feature-union experiment shows that this advantage does not necessarily extend to a less constrained union-feature protocol.

It should also be noted that the feature-aligned validation strategy used in this study is a controlled pairwise evaluation protocol rather than a universal cross-domain pretraining framework. Since CICIoT2023 and CICIoMT2024 have different feature spaces, this study constructs a common tabular feature space by retaining shared statistical features. This design enables external validation under consistent input dimensions, but it also has limitations. When more heterogeneous datasets are introduced, the shared feature intersection may become smaller, and some dataset-specific but useful information may be discarded. Therefore, the proposed setting should be understood as feature-aligned external vali dation for tabular traffic statistics, rather than a scalable traffic foundation model. More general pretraining-based traffic representation learning remains an important direction for future work.

The standardized NetFlow experiment complements the feature-aligned and featureunion experiments. In the NF-ToN-IoT to NF-BoT-IoT external validation setting, all models show a clear performance drop compared with the internal NF-ToN-IoT test set, confirming that cross-dataset intrusion detection remains difficult even under standardized NetFlow features. Nevertheless, FT-Transformer achieves the highest external accuracy, attack-class F1-score, ROC-AUC, and PR-AUC among the compared models in this setting. This result provides additional evidence that Transformer-based tabular modeling can be beneficial in some external validation scenarios. However, the result should still be interpreted cautiously because the feature-union experiment shows that this advantage is not universal across all external validation protocols.

The domain-aligned FT-Transformer experiment shows that cross-dataset robustness depends not only on the model architecture but also on the training objective. Compared with the source-only FT-Transformer, CORAL-based representation alignment substantially improves the external ROC-AUC in the CICIoT2023-to-CICIoMT2024 setting and improves all external evaluation metrics in the NF-ToN-IoT-to-NF-BoT-IoT setting. This indicates that explicitly reducing source-target representation discrepancy can be beneficial for external validation. However, the improvement is not uniform across all metrics; for example, in the CICIoT2023-to-CICIoMT2024 setting, ROC-AUC improves clearly, whereas accuracy and attack-class F1-score change only slightly. Therefore, domain-aligned training should be regarded as a promising but still preliminary strategy, while more advanced pretraining, transfer learning, and domain adaptation methods remain important future directions.

In the main binary classification task, FT-Transformer achieves accuracy, F1-score, and AUC-related metrics that are close to those of Random Forest and XGBoost. This suggests that Transformer-based tabular modeling is competitive for IoT traffic statistical feature tasks. However, an important observation should also be emphasized: Random Forest and XGBoost slightly outperform the current FT-Transformer model on the primary binary test set. This indicates that, for tasks dominated by statistical tabular traffic features, traditional tree-based models remain very strong baselines [6,16].

The McNemar test further confirms that the paired prediction differences between FT-Transformer and the two tree-based baselines on the primary binary test set are statistically significant. Therefore, the in-dataset results should be interpreted conservatively: traditional tree-based models remain slightly stronger on the primary binary task, whereas the main advantage of FT-Transformer is reflected in its cross-dataset ROC-AUC stability under feature-aligned external validation. Accordingly, the contribution of this study should not be interpreted as claiming that FT-Transformer outperforms traditional methods across all metrics. Instead, FT-Transformer should be viewed as an effective and extensible deep learning solution for IoT tabular traffic detection, with particular value in feature-aligned cross-dataset validation and interpretability analysis.

The SHAP analysis shows that the key discriminative features learned by the model, such as Number, HTTPS, and Header\_Length, have clear semantic correspondence with known attack behaviors. This indicates that the model does not rely only on abstract numerical fitting but also captures traffic characteristics that are meaningful from a cybersecurity perspective. Therefore, SHAP-based analysis further enhances the interpretability and credibility of the detection results.

The multi-class classification experiments further reveal the limitations of the current model. Although the model performs well in identifying categories such as Mirai, DoS, and DDoS, its performance decreases noticeably for Web-Based and Brute Force categories. This may be related to the smaller sample sizes, more ambiguous class boundaries, and more complex attack patterns of these categories. Therefore, future research should further investigate class imbalance handling, weak-class enhancement, feature selection optimization, and loss functions that are more suitable for multi-class intrusion detection.

The lightweight ablation results indicate that simply increasing the token dimension does not significantly improve model performance. This suggests that future improvements should not rely only on enlarging the model scale. Instead, more attention should be paid to enhancing the modeling capability for complex categories, introducing stronger generalization constraints, and improving the recognition of underrepresented classes in multi-class classification tasks.

To further examine the class imbalance issue, this study additionally introduces a class-weighting strategy into FT-Transformer training. The supplementary results show that, after applying weighted cross-entropy, the accuracy, macro-F1, and weighted-F1 on the test set are 0.7878, 0.7038, and 0.7984, respectively, which are lower than those of the original FT-Transformer. From the category-wise results, the recall of Brute Force and Web-Based increases, but their precision decreases substantially, resulting in no effective improvement in the corresponding F1-scores. This indicates that simple class weighting can increase the model’s sensitivity to minority classes but may also introduce more false positives and weaken the overall classification performance. Therefore, class imbalance remains an important challenge in the current multi-class IoT attack detection task, and relying solely on simple weighting is insufficient to solve this problem. Future work should explore more systematic imbalance handling strategies, such as cost-sensitive learning, data augmentation, or synthetic minority-class generation.

## 7. Conclusions

This study investigates the application of FT-Transformer to IoT network attack detection and systematically evaluates its performance in primary-dataset binary classification, feature-aligned external validation, feature-union validation, standardized NetFlow external validation, domain-aligned training, multi-class classification, and interpretability analysis. The experimental results show that FT-Transformer achieves competitive accuracy, F1-score, and AUC-related metrics on the CICIoT2023 binary classification task and shows stable ROC-AUC performance under the controlled 38-feature aligned external validation setting. Meanwhile, the multi-class classification experiments and SHAP analysis indicate that the model can support both classification and interpretation of complex IoT traffic features within a unified deep tabular learning framework.

Comparative experiments show that Random Forest and XGBoost remain strong baselines for tabular traffic detection tasks, and the current FT-Transformer model does not significantly outperform them on the primary binary and multi-class classification tasks. However, the external validation results provide a more nuanced view. FT-Transformer shows better ROC-AUC stability under the controlled 38-feature aligned CICIoT2023-to CICIoMT2024 validation setting and achieves the strongest external validation performance among the compared models in the additional standardized NetFlow NF-ToN-IoT to NF-BoT-IoT experiment. Nevertheless, the feature-union validation experiment also indicates that this advantage should not be interpreted as genuine universal cross-dataset generalization. Furthermore, the domain-aligned FT-Transformer-CORAL experiment shows that explicit source-target representation alignment can improve external validation performance, especially in terms of ROC-AUC. Therefore, the main contribution of this study lies in providing a systematic and reproducible empirical evaluation of FT-Transformer across multiple external validation protocols and training strategies, rather than claiming that it universally outperforms all traditional and modern tabular baselines.

Future work will focus on more scalable traffic representation learning, pretrainingbased transfer learning, domain adaptation, class imbalance handling, weak-class enhance ment in multi-class classification, and more in-depth interpretability analysis, with the aim of improving the overall performance and reliability of the model in complex IoT security scenarios.

Supplementary Materials: The following supporting information can be downloaded at: https:// www.mdpi.com/article/10.3390/electronics15122516/s1, Table S1, list of the 38 shared features used for cross-dataset alignment; Table S2, dataset split statistics used in the experiments; Table S3, class distribution statistics used in the experiments.

Author Contributions: Conceptualization, F.L. and L.Q.; methodology, F.L.; software, F.L.; vali dation, F.L.; formal analysis, F.L.; investigation, F.L. and Y.T.; resources, F.L.; data curation, F.L.; writing—original draft preparation, F.L. and Y.T.; writing—review and editing, F.L. and L.Q.; visualization, F.L. and Y.T.; supervision, L.Q.; project administration, L.Q. All authors have read and agreed to the published version of the manuscript.

Funding: This research received no external funding.

Data Availability Statement: The CICIoT2023 and CICIoMT2024 datasets analyzed in this study are publicly available from the Canadian Institute for Cybersecurity, University of New Brunswick. The processed data and source code generated during the current study are available from the corresponding author upon reasonable request.

Conflicts of Interest: The authors declare no conflicts of interest.

## Abbreviations

The following abbreviations are used in this manuscript:

IoT Internet of Things

IoMT Internet of Medical Things

IDS Intrusion Detection System DDoS Distributed Denial-of-Service DoS Denial-of-Service CNN Convolutional Neural Network RNN Recurrent Neural Network LSTM Long Short-Term Memory MLP Multilayer Perceptron SHAP Shapley Additive Explanations ROC-AUC Area Under the Receiver Operating Characteristic Curve PR-AUC Area Under the Precision–Recall Curve

## References

1. Fatima, R.; Sheeba, S.; Rafa, R. AI-Driven Intrusion Detection System: A Survey of Techniques, Datasets, and Evaluation Frameworks. J. Syst. Eng. Electron. 2025, 35, 212.

2. Almomani, O.; Oukaira, A.; El Guemmat, K.; Atouf, I.; Ouahabi, S.; Talea, M.; Bouragba, T. Network Intrusion Detection Datasets: A Comprehensive Review and Comparative Analysis. Comput. Secur. 2024, 139, 103682.

3. Rakine, I.; Oukaira, A.; Guemmat, K.E.; Atouf, I.; Ouahabi, S.; Talea, M.; Bouragba, T. Comprehensive Review of Intrusion Detection Techniques: ML and DL in Different Networks. IEEE Access 2025, 13, 104348–104372. [CrossRef]

4. Ajagbe, S.A.; Awotunde, J.B.; Florez, H. Intrusion Detection: A Comparison Study of Machine Learning Models Using Unbalanced Datasets. SN Comput. Sci. 2024, 5, 1028. [CrossRef]

5. Talukder, M.A.; Islam, M.M.; Uddin, M.A.; Hasan, K.F.; Sharmin, S.; Alyami, S.A.; Moni, A.A. Machine Learning-Based Network Intrusion Detection for Big and Imbalanced Data Using Oversampling, Stacking Feature Embedding and Feature Extraction. J. Big Data 2024, 11, 33. [CrossRef]

6. Musthafa, M.B.; Huda, S.; Kodera, Y.; Ali, M.A.; Araki, S.; Mwaura, J.; Nogami, Y. Optimizing IoT Intrusion Detection Using Balanced Class Distribution, Feature Selection, and Ensemble Machine Learning Techniques. Sensors 2024, 24, 4293. [CrossRef]

7. Fan, Z.; Sohail, S.; Sabrina, F.; Gu, X. Sampling-Based Machine Learning Models for Intrusion Detection in Imbalanced Datasets. Electronics 2024, 13, 1878. [CrossRef]

8. Gorishniy, Y.; Rubachev, I.; Khrulkov, V.; Babenko, A. Revisiting Deep Learning Models for Tabular Data. arXiv 2021, arXiv:2106.11959.

9. Huang, X.; Khetan, A.; Cvitkovic, M.; Karnin, Z. TabTransformer: Tabular Data Modeling Using Contextual Embeddings. arXiv 2020, arXiv:2012.06678. [CrossRef]

10. Mohale, V.Z.; Obagbuwa, I.C. A Systematic Review on the Integration of Explainable Artificial Intelligence in Intrusion Detection Systems. Front. Artif. Intell. 2025, 8, 1526221. [CrossRef]

11. Hulayyil, S.B.; Li, S.; Saxena, N. Explainable AI-Based Intrusion Detection in IoT Systems. IEEE Internet Things J. 2025, 31, 101589. [CrossRef]

12. Neto, E.C.P.; Dadkhah, S.; Ferreira, R.; Zohourian, A.; Lu, R.; Ghorbani, A.A. CICIoT2023: A Real-Time Dataset and Benchmark for Large-Scale Attacks in IoT Environments. Sensors 2023, 23, 5941. [CrossRef] [PubMed]

13. Canadian Institute for Cybersecurity. CICIoMT2024 Dataset; University of New Brunswick: Fredericton, NB, Canada, 2024.

14. Xin, C.; Xu, K. Cross-Dataset Transformer-IDS with Calibration and AUC Optimization. Cybersecurity 2025, 7, 483.

15. Sharma, R.; Sikdar, S. Cross-Dataset Validation of a Deep Learning-Driven Intrusion Detection Framework for IoT Security. Int. Res. J. Mod. Eng. Technol. Sci. 2025, 7, 68060.

16. Farooqi, A.H.; Akhtar, S.; Rahman, H.; Sadiq, T.; Abbass, W. Enhancing Network Intrusion Detection Using an Ensemble Voting Classifier for Internet of Things. Sensors 2024, 24, 127. [CrossRef] [PubMed]

17. Arik, S.Ö.; Pfister, T. TabNet: Attentive Interpretable Tabular Learning. In Proceedings of the AAAI Conference on Artificial Intelligence, Online, 2–9 February 2021; Volume 35.

18. Cantone, M.; Marrocco, C.; Bria, A. On the Cross-Dataset Generalization of Machine Learning for Network Intrusion Detection. arXiv 2024, arXiv:2402.10974. [CrossRef]

19. Mia, M.; Pritom, M.M.A.; Islam, T.; Hasan, K. Visually Analyze SHAP Plots to Diagnose Misclassifications in ML-Based Intrusion Detection. arXiv 2024, arXiv:2411.02670. [CrossRef]

20. Mohale, V.Z.; Obagbuwa, I.C. Evaluating Machine Learning-Based Intrusion Detection Systems with Explainable AI. Front. Comput. Sci. 2025, 7, 1520741. [CrossRef]

21. Lotfollahi, M.; Zade, R.S.H.; Siavoshani, M.J.; Saberian, M. Deep Packet: A Novel Approach for Encrypted Traffic Classification Using Deep Learning. Soft Comput. 2020, 24, 1999–2012. [CrossRef]

22. Lin, X.; Xiong, G.; Gou, G.; Li, Z.; Shi, J.; Yu, J. ET-BERT: A Contextualized Datagram Representation with Pre-training Transformers for Encrypted Traffic Classification. arXiv 2022, arXiv:2202.06335.

23. Wang, Z.; Thing, V.L.L. Feature Mining for Encrypted Malicious Traffic Detection with Deep Learning and Other Machine Learning Algorithms. arXiv 2023, arXiv:2304.03691. [CrossRef]

24. Fu, C.; Li, Q.; Xu, K. Detecting Unknown Encrypted Malicious Traffic in Real Time via Flow Interaction Graph Analysis. arXiv 2023, arXiv:2301.13686. [CrossRef]

25. Vaswani, A.; Shazeer, N.; Parmar, N.; Uszkoreit, J.; Jones, L.; Gomez, A.N.; Kaiser, Ł.; Polosukhin, I. Attention Is All You Need. Adv. Neural Inf. Process. Syst. 2017, arXiv:1706.03762.

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.