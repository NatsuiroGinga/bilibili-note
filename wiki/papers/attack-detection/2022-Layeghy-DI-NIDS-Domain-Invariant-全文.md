---
title: "2022-Layeghy-DI-NIDS-Domain-Invariant"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2022-Layeghy-DI-NIDS-Domain-Invariant.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# DI-NIDS: Domain Invariant Network Intrusion Detection System

Siamak Layeghy<sup>a,∗</sup>, Mahsa Baktashmotlagh<sup>a</sup>, Marius Portmann<sup>a</sup>

<sup>a</sup>School ofITEE, The University ofQueensland, Brisbane, Australia

## Abstract

The performance of machine learning based network intrusion detection systems (NIDSs) severely degrades when deployed on a network with significantly diferent feature distributions from the ones of the training dataset. In various applications, such as computer vision, domain adaptation techniques have been successful in mitigating the gap between the distributions of the training and test data. In the case of network intrusion detection however, the state-of-the-art domain adaptation approaches have had limited success. According to recent studies, as well as our own results, the performance of an NIDS considerably deteriorates when the ‘unseen’ test dataset does not follow the training dataset distribution. In order to enhance the generalisibility of machine learning based network intrusion detection systems, we propose to extract domain invariant features using adversarial domain adaptation from multiple network domains, and then apply an unsupervised technique for recognising abnormalities, i.e., intrusions. More specifically, we train a domain adversarial neural network on labelled source domains, extract the domain invariant features, and train a One-Class SVM (OSVM) model to detect anomalies. At test time, we feedforward the unlabeled test data to the feature extractor network to project it into a domain invariant space, and then apply OSVM on the extracted features to achieve our final goal of detecting intrusions. Our extensive experiments on the NIDS benchmark datasets of NFv2-CIC-2018 and NFv2-UNSW-NB15 show that our proposed setup demonstrates superior cross-domain performance in comparison to the previous approaches.

Keywords: Adversarial Domain Adaptation, Network Intrusion Detection System (NIDS), Cross-Domain Evaluation, Domain Invariant Anomaly Detection, One-Class SVM

## 1. Introduction

For network anomaly/intrusion detection, labelling millions of real-world network records requires a significant amount of resources and human expertise. Various attacks do not happen all the time/everywhere, and due to privacy and security con cerns, labelled real-world network intrusion detection systems (NIDS) datasets are scarce, and rarely publicly available. Ac cordingly, the common way of training machine learning (ML) based NIDSs is by using publicly available synthetic datasets. However, as has been shown [1], there is a considerable difer ence in the feature distribution of the benign/background traffic between real-world datasets and the synthetic benchmark datasets created in research labs. Thus, the cross-domain performance, i.e., the capability of correctly classifying the test samples in the presence of distribution shifts, is essential for adapting ML-based NIDSs for successful deployment and use in real-world production networks.

However, the majority of the proposed ML-based NIDSs are evaluated only on domain-specific datasets, i.e., the training and evaluation samples are drawn from the same dataset, and cross-domain evaluation is rarely considered.

Moreover, current approaches for anomaly detection assume similar feature distributions for the training and test datasets [2]. Therefore, these models fail to perform well when there is a distribution diference between the train (i.e., source) and test (i.e., target) data. Our study shows that the performance of the existing NIDS models degrades when they are applied in a network environment that has a diferent feature distribution compared to the training environment/dataset [3, 4].

To address the domain shift problem, several domain adaptation (DA) techniques have been introduced in the literature. These techniques try to reduce the gap between the feature representations of the labeled source and unlabeled target domains, so that the classifiers trained on the source domain perform sim ilarly well on the target domain [5, 6].

Generally speaking, domain adaptation approaches follow a supervised learning strategy, and thus, they are better suited to class-balanced datasets. However, in the field of network in trusion/anomaly detection, anomalies are relatively rare events, i.e., network anomalies are in high class imbalance compared to the benign/background trafic class. Based on our experimental results, current domain adaptation techniques based on a supervised learning strategy perform poorly on finding anomalies.

To address this gap, we are proposing a new unsupervisedlearning scheme for cross-domain anomaly detection. In this method, we use a domain adaptation technique to first extract a domain-invariant representation of the data, and then apply the anomaly detection on the projected representation. For the domain adaptation, we use a Domain-Adversarial Neural Network (DANN) [7], which is one of the well-known and best working approaches. The DANN can be simply incorporated in the feature extraction network by adding a gradient reversal layer to minimize the diference between the representations of the source and target domains. We first train the DANN using the labeled source data and unlabeled target data, and then, we exploit the feature extraction branch of the DANN to obtain the domain invariant features. Finally, we apply one-class Support Vector Machines or One-Class SVM (OSVM) [8] on the extracted features to reach our final goal of cross-domain anomaly detection.

A network anomaly is a somewhat ill-defined concept that is used to describe any networking event such as network at tacks/intrusions, failure, etc., that can significantly change the overall and flow-based feature statistics of a monitored net work, e.g. the number of input bytes [9].

Note that, similar to other machine learning approaches, OSVMs fails to perform well in the presence of distribution shift. Therefore, before feeding the data to an OSVM, we project the training and test data to a common subspace using a DANN. Our results clearly indicate that projecting features to a domain invariant feature space, before feeding them into an OSVM, significantly improves the cross-domain performance of intrusion detection.

In summary, we propose a domain-invariant NIDS (DI-NIDS) framework by leveraging recent advances in the domain adaptation literature. DI-NIDS takes into account the intense class-imbalance nature of anomalies in the NIDS data when addressing the domain shift between the train and test datasets. The proposed framework is evaluated against various ML-models in both cross-domain and domain-specific evaluation scenarios, where it shows superior performance. In the rest of this paper we first discuss the related works in the next section, then explain the proposed solution in Section 3. Extensive evaluation of DI-NIDS and comparison to the state-of-the-art are discussed in Section 4, and Section 5 concludes the paper.

## 2. Related Works

For the relevant related works of this paper we considered proposed NIDSs which at least follow a partial cross-domain evaluation approach across diferent datasets. We managed to find two main groups of NIDS proposals in which some aspects of the training and evaluation datasets are diferent. While many of these works cannot be directly compared to our work, we still included them since they consider partial elements of cross-domain evaluation.

## 2.1. Separate Source and Target Domains

In the first group, cross-domain evaluation is realised via separate training (source domain) and test datasets (target do main). In this group of NIDSs, techniques such as domain adaptation and transfer learning are applied on the source domain to acquire the knowledge of anomalies/attacks, and to extend this knowledge to classify samples from the target domain.

This group can be further divided into two sub-categories; those which do not require labelled data from the target domain, and those that need a subset of the target domain to have labels. We found three studies from the first subcategory and two studies from the second subcategory as explained below.

In the first subcategory, consisting of studies that do not need labelled data from the target domain, [10] is the only work, to the best of our knowledge, that uses a DANN in the field of network intrusion detection. The paper focuses on detect ing attacks in smart grid networks. By applying the adversarial training to adapt learned models on normal operation data of the ISO New England grids, the authors try to detect attacks at diferent times of the day on their smart grid network. The paper shows that, due to the load demand changes during diferent times of day, conventional ML-based NIDSs fail to detect attacks, and their proposed DANN-based method improves the detection performance. The authors use false data injection attacks synthesized on the IEEE 30-bus system for the evaluation of their proposed framework. The paper shows that the proposed method has superior detection performance for persistent threats recurring in a highly dynamic smart grid, compared to conventional ML-based NIDSs.

In [11] partial domain adaptation is used to map the source and target domains to a domain-invariant feature space to ad dress the diferences between the source and target datasets. The authors use weighted adversarial networks-based domain adaptation for transferring knowledge from the publicly avail able labeled datasets, such as CIC-IDS2017 [12], to an unla belled Internet of Things (IoT) dataset, such as [13]. In or der to evaluate their proposed framework, the authors apply it to a combination of benign trafic and various common attack classes, across two datasets. They train their model on CIC-IDS201, and evaluate it on the IoT dataset. In another evalua tion, they train and test their model on diferent attack classes to evaluate the performance of their model for detecting un known attacks. The authors finally compare their framework with a DANN on a binary classification problem consisting of benign trafic and a specific attack class, and show it performs similar to a DANN. While this is an example of a partial crossdomain evaluation of NIDSs, they do not evaluate their methods on full set of classes of the datasets. In addition, the evaluation only considers one direction of the cross-domain evaluation, i.e. with training on one dataset and evaluation on the other, but not vice versa. As we show in this paper, this is a significant limi tation, since the results are highly asymmetric.

The authors of [14] propose the Energy-based Flow Classifier (EFC), an anomaly-based classifier that infers a statisti cal model based on labelled benign samples. They define the concept of quantum energy for network flows and compute a threshold for the benign flows as the 95th percentile of the be nign flows’ energy distribution. Then, they compare the energy of a given flow to this threshold and declare a flow as malicious if its energy is above the threshold. The authors use three versions of the CIC-IDS [12] dataset for the evalu ation of their proposed algorithm. The paper’s results are compared with conventional ML-based NIDSs for both domainspecific, i.e., the same dataset as the source and target, and cross-domain, i.e., diferent source and target domains. While the reported domain-specific performance is relatively high, the cross-domain performance is significantly reduced.

While these previous studies do not require labelled data from the target domain, the next two studies need a small por tion of the target domain to have labels. The first paper in this group [15] considers a host-based intrusion detection approach, rather than network intrusion detection, and aims to reduce the number of labelled samples from the target domain. The au thors use two diferent host-based intrusion detection datasets as the source and target domains respectively. By using fine tuning techniques of deep learning models, such as freezing the hidden layers, they manage to reduce the number of labelled samples from the target domain, while improving the Area Un der Curve (AUC) metric by 8%.

The last paper [16] in this subcategory uses domain adapta tion to address the scarcity of labeled training data by transferring the acquired knowledge from a publicly available labelled dataset. Initially, the authors use the UNSW-NB15 [17] dataset and divide it into two subsets of complementary attack classes, and evaluate their approach for the same feature set assessment. Then they use the NSL-KDD [18] dataset as the source and the UNSW-NB15 [17] dataset as the target domain, and evaluate their proposed method for diferent feature set assessment. Based on the provided results, the proposed method achieves a higher accuracy for various attack classes compared to the fine tuning method, for the same number of samples from the target domain. Although these two methods cannot be directly compared to our work, as they need labels from the target domain, they discuss the challenges of addressing the distribution gap between diferent intrusion detection datasets.

## 2.2. Partially Diferent Domains

In the second group of studies, the training and test datasets are the same, but the dataset is divided into subsets containing various attack classes. One subset is used as the source and the other, which might include attack classes not present in the source domain, as the target domain. Techniques such as do main adaptation and transfer learning have been used to transfer the knowledge learnt from the attack classes available in the source domain, to classify/detect the attack classes in the target domain.

In[19], a transfer learning algorithm is used to transfer the knowledge of an image-based representation of network flows. The authors train a convolutional neural network (CNN) in the source domain and augment it with one dense layer in the target domain. In [20] the authors also use a CNN architecture for transfer learning on NIDS datasets. They use two concatenated CNNs to learn network attack patterns on a divided NSL KDD dataset [18] and improve unknown/unseen attack detection performance in comparison to conventional ML-based NIDSs. Similar to [19], the authors in [21] convert divided KDD99 dataset [22] records into gray-scale images which are then processed for detecting attacks using a CNN architecture. For the purpose of transfer learning, they use samples of unseen attacks to fine tune the trained CNN.

With the exception of [14], none of the related works dis cussed in this section provides a comparable cross-domain evaluation of the proposed NIDS across diferent benchmark datasets. While the methods proposed in [15] and [16] ap ply domain adaptation techniques on network intrusion detection datasets, they are fundamentally diferent to our approach, since they rely on the availability of target domain labels, which are dificult to obtain in real-world networks. In contrast, our method proposed in this paper does not require target domain labels, and is hence much more practical.

The last three discussed studies, i.e., [19], [20] and [21], do not consider domain adaptation, and mainly focus on detecting one or more attacks that were unseen during training.

While [10] and [11] are similar to our work in the sense that they do not require any target domain labels, these works do not provide a complete cross-domain evaluation such as presented in this paper. In [10], the proposed method is evaluated against the attacks injected into a smart grid network, and there is no consideration of applying such a method on the publicly avail able NIDS datasets. In [11] the proposed method is evaluated against subsets of the target domain and performance metrics are provided for individual attack classes.

The method presented in [14] is the only approach with a cross-domain performance evaluation that is comparable to ours. However, the performance of the method proposed in [14] shows a 19% degradation (on average) of the cross-domain per formance compared to the corresponding domain-specific performance. As we will demonstrate, our proposed method performs significantly better in this critical regard.

## 3. Proposed Method (DI-NIDS)

Figure 1 shows the architecture of Domain Invariant Network Intrusion Detection System (DI-NIDS), our proposed approach, consisting of two main components, DANN and OSVM. While OSVMs generally perform well for one-class classification problems, in particular anomaly detection, they do not perform well for cross-domain data [23] in general. DANNs on the other hand, were designed to address the problem of domain gap, i.e., diferent feature distributions, in conventional machine learning models. The key idea of DI-NIDS is to enhance the domain adaptability of OSVM by leveraging the capabilities provided by a DANN.

![](images/6bcf627f254d4773d8738c7bf73b1b9df7d80bf85bd9d74e77840af9d4fd67df.jpg)  
Figure 1: Proposed DI-NIDS architecture.

As can be seen in Figure 1, a dense Multi Layer Perceptron (MLP) is used as the basis of the DANN in our model, with the main hyper-parameters listed in Table 1. As per [7], it is possible to implement a DANN using any feed-forward neural network architecture, and the type of the neural network can be selected to best match the attributes of the input data. For instance, if the input type is an image, convolutional neural net works are typically chosen. Since the NIDS data consist of a small number of numeric and categorical features, we select a basic MLP network as a starting point.

The training of our DI-NIDS follows a two-step process. In the first step, the DANN is trained using the source data, source labels, target data, and domain labels (labels that identify which domain the input belongs to, i.e., train or test dataset). Note that no target class labels are required in the training stage of the DANN. Once the training stage of the DANN is completed, we employ the trained feature extractor network $G _ { f }$ to extract domain invariant features from the data. In the second step, the OSVM is trained using the extracted domain invariant features. DANN Component: In ML-based NIDSs, as is the case in other application areas as well, it is dificult and timeconsuming to label real-world data. Consequently, synthetic datasets are often used for training and evaluation of machine learning models. However, these synthetic datasets usually do not adequately represent real-world networks and sufer from distribution shift, i.e. a significant diference in feature distributions [1]. Generally speaking, domain adaptation aims at as making the distributions of source and target domains similar, so that if a classifier or detector is trained on the source data, it can perform well on the target data. [7].

In this work, we employ adversarial domain adaptation to extract domain invariant features from the source and target do mains. The architecture of a DANN [7] is shown in Figure 2. The architecture consists of three networks: feature extractor to extract features from the source and target domains, label classifier to predict class labels, and domain classifier to predict domain labels. The domain classifier network includes a gradient reversal layer to make the distributions of the source and target features similar. Specifically, for the samples that are correctly classified by the domain classifier, a penalty is applied through multiplying their gradient by a negative factor during back propagation [10, 7].

Table 1: Parameters of three neural networks utilised in the implemented DI-NIDS architecture

<table><tr><td>Name</td><td>Function</td><td>Input Nodes</td><td>Output Nodes</td><td>No. of Hidden Layers</td><td>Hidden Layers Nodes</td></tr><tr><td> $G_f$ </td><td>Feature Extractor</td><td>39</td><td>10</td><td>2</td><td>10</td></tr><tr><td> $G_C$ </td><td>Label Classifier</td><td>10</td><td>2</td><td>0</td><td>0</td></tr><tr><td> $G_D$ </td><td>Domain Classifier</td><td>10</td><td>2</td><td>1</td><td>10</td></tr></table>

![](images/7b8cfd4e3b12d6b67be8f40f610c28dcd27fd4a06df090b23f36d9aee3222a56.jpg)  
Figure 2: Domain Adversarial Neural Network.

Definition: Assume $X ~ = ~ \{ x _ { 1 } , x _ { 2 } , . . . , x _ { n } \}$ represents the input space, ${ \cal Y } ~ = ~ \{ 0 , 1 \}$ is the set of binary labels, and η : $X ~  ~ Y$ is a binary classifier. Given the source domain, $\mathcal { D } _ { S } = \{ ( \boldsymbol { x } _ { 1 } ^ { S } , \boldsymbol { y } _ { 1 } ^ { S } ) , ( \boldsymbol { x } _ { 2 } ^ { S } , \boldsymbol { y } _ { 2 } ^ { S } ) , . . . , ( \boldsymbol { x } _ { n _ { s } } ^ { S } , \boldsymbol { y } _ { n _ { 1 } } ^ { S } ) \}$ , and the target domain, $\begin{array} { r c l } { \mathcal { D } _ { \mathcal { T } } } & { = } & { \{ ( \dot { x } _ { 1 } ^ { T } , \dot { y } _ { 1 } ^ { T } ) , ( \bar { x } _ { 2 } ^ { T } , \bar { y } _ { 2 } ^ { T } ) , . . . , ( \bar { x } _ { n _ { T } } ^ { T } , \bar { y } _ { n _ { 2 } } ^ { T } ) \} } \end{array}$ , the feature extractor neural network $G _ { f }$ can be defined as

$$
G _ {f} (\mathbf {x}; \mathbf {W}, \mathbf {b}) = \text { sigmoid } (\mathbf {W x} + \mathbf {b})\tag{1}
$$

where (W b) are network weights and biases, with $x \in D _ { S }$ . The label classifier network $G _ { C }$ can be written as

$$
G _ {C} (G _ {f} (\mathbf {x}); \mathbf {V}, c) = s i g m o i d \left(\mathbf {V} G _ {f} (\mathbf {x}) + c\right)\tag{2}
$$

with $( \mathbf { V } , c )$ representing the network parameters. Finally, the domain classifier network $G _ { D }$ can be formulated as

$$
G _ {D} (G _ {f} (\mathbf {x}); \mathbf {u}, z) = \text { sigmoid } \left(\mathbf {u} ^ {T} G _ {f} (\mathbf {x}) + z\right)\tag{3}
$$

with (u z) the network parameters.

More specifically, for a given sample-label pair (x y) x ∈ $X , y \in Y ,$ , the domain classifier loss $L _ { D } ( x , \gamma )$ is defined as follows:

$$
\begin{array}{r} L _ {D} (x _ {i}, \gamma_ {i}) = \gamma_ {i} l o g \frac {1}{G _ {D} (G _ {f} (\mathbf {x _ {i}}))} + \\ (1 - \gamma_ {i}) l o g \frac {1}{1 - G _ {D} (G _ {f} (\mathbf {x _ {i}}))} \end{array}\tag{4}
$$

where

$$
\left\{ \begin{array}{l l} \gamma_ {i} = 0 & \text {   if   } x _ {i} \in \mathcal {D} _ {S} \\ \gamma_ {i} = 1 & \text {   if   } x _ {i} \in \mathcal {D} _ {T} \end{array} \right.
$$

With the label classifier loss $L _ { y } ( x , y )$ defined as

$$
L _ {y} (x _ {i}, y _ {i}) = \log \frac {1}{G _ {C} (G _ {f} (\mathbf {x _ {i}})) _ {y _ {i}}}\tag{5}
$$

the optimisation function of the domain adversarial neural net work [7] can be written as

$$
\begin{array}{c} \underset {W, b, V, c, u, z} {\min} \left[ \frac {1}{n _ {S}} \sum_ {x \in \mathcal {D} _ {S}} L _ {y} (x, y) \right. \\ \left. - \frac {\lambda}{n _ {S}} \sum_ {x \in \mathcal {D} _ {S}} L _ {D} (x, \gamma) - \frac {\lambda}{n _ {T}} \sum_ {x \in \mathcal {D} _ {T}} L _ {D} (x, \gamma) \right] \end{array}\tag{6}
$$

![](images/094bd6a9d037f70423101d546fb65a3278982cfbd4be88e92e4a970b3719a506.jpg)  
(a) Source Label Training

![](images/9e54a3aa4ce2612069211dead05b2a9d6a749d89005ea70efaac050e60508735.jpg)  
(b) Domain classifier training  
Figure 3: Two sub-processes of DANN including: a) Source classifier training and b) Domain classifier training

with $n _ { S }$ and $n _ { T }$ being the number of samples from the source and target domains.

Two simultaneous sub-processes of label classifier training and domain classifier training, as shown in Figure $3 \mathrm { - } ( \mathrm { a } )$ and $3 \mathrm { - }$ (b) respectively, contribute to the training process of the DANN. During the label classifier training, the source data and its labels are passed through the feature extractor $( G _ { f } )$ and label classifier $( G _ { C } )$ networks, and are optimised through stochastic gradient descent to update the weights in $G _ { C }$ and $G _ { f }$

In the domain classifier training sub-process, the source data, the target data, and domain labels are passed through the feature extractor $( G _ { f } )$ and domain classifier $( G _ { D } )$ . The domain labels $( \gamma )$ identify the domain to which a given input belongs, as defined in Equation 3. In this sub-process, the samples with correctly predicted domain labels are penalised by the ”Gradient Reversal” layer. The two sub-processes are optimised simultaneously, so the domain invariant and discriminative features can be learnt.

OSVM Component: In the one-class classification problem, the objective is to learn the feature distributions of the normal/benign network flows, and identify samples that deviate significantly from that distribution. This is known as anomaly detection.

Support Vector Machines (SVM) [24] were originally proposed for the multi-class classification problems and were later adopted for the one-class classification problem as proposed in [8, 25].

Assume $\begin{array} { r c l } { \chi } & { = } & { \{ ( x _ { 1 } , y _ { 1 } ) , ( x _ { 2 } , y _ { 2 } ) , . . . , ( x _ { n } , y _ { n } ) \} } \end{array}$ represents a d i hi h $x _ { i } \in \mathbb { R } ^ { d }$ is the ith data point in a d-dimensional input space I, and $y _ { i } \in \{ - 1 , 1 \}$ represents the ith output, i.e., class labels. A SVM uses a nonlinear function φ, i.e., a kernel, to project data points from their input space I to a high dimensional feature space F, in which the classes can be distinguished by a linear hyperplane $w ^ { T } x + b = 0 .$ , with $w \in \mathbb { F }$ and $b \in \mathbb { R }$ . To find this hyperplane, SVM minimises the following objective function [25]:

$$
\min _ {w, b, \xi_ {i}} \left[ \frac {\| w \| ^ {2}}{2} + C \sum_ {i = 1} ^ {n} \xi_ {i} \right]\tag{7}
$$

subject to the two constraints of:

$$
\left\{ \begin{array}{l l} y _ {i} \left(w ^ {t} \phi \left(x _ {i}\right) + b\right) \geq 1 - \xi_ {i} & \quad \forall i = 1,..., n \\ \xi_ {i} \geq 0 & \quad \forall i = 1,..., n \end{array} \right.
$$

Here, $C$ is a constant determining the number of training data points within the margin between two classes, i.e., training error, and $\xi$ is the slack variable to prevent overfitting. Solving this minimisation problem via Lagrange multipliers results in the following classification rule for a given data point x [25]:

$$
f (x) = s g n \left[ \sum_ {i = 1} ^ {n} \alpha_ {i} y _ {i} K (x, x _ {i}) + b \right]\tag{8}
$$

with $\alpha _ { i }$ being the Lagrange multipliers and the function $K ( x , x _ { i } ) = \phi ( x ) ^ { T } \phi ( x )$ being the kernelfunction.

In OSVM [8], instead of learning a hyperplane to separate two classes of data, a hyperplane is learnt to separate the abnormal data points from the normal density in the origin. Hence, the intention is to maximise the distance of the learnt hyper plane from the origin in the feature space F. An OSVM can be mathematically formulated as a minimisation of the below objective function [25]:

$$
\min _ {w, \xi_ {i}, \rho} \left[ \frac {\| w \| ^ {2}}{2} + \frac {1}{\nu n} \sum_ {i = 1} ^ {n} \xi_ {i} - \rho \right]\tag{9}
$$

subject to the following two constraints:

$$
\left\{ \begin{array}{l l} (w. \phi \left(x _ {i}\right)) \geq \rho - \xi_ {i} & \forall i = 1,..., n \\ \xi_ {i} \geq 0 & \forall i = 1,..., n \end{array} \right.
$$

with $\nu \in ( 0 , 1 )$ being the upper bound identifier for the fraction of outliers and lower bound on the support vectors, and $\rho \in \mathbb { R }$ being the ofset. The Lagrange method is used to solve the above minimisation problem which results in the following classification rule [25]:

$$
\begin{array}{r l} {f (x) = s g n \left(w \phi \left(x _ {i}\right) - \rho\right)} & \\ & {= s g n \left[ \sum_ {i = 1} ^ {n} \alpha_ {i} y _ {i} K \left(x, x _ {i}\right) - \rho \right]} \end{array}\tag{10}
$$

The hyperplane identified by w and $\mathbf { \nabla } \cdot \rho$ has the maximum distance to the origin in the feature space F, which separates anomalous data points from the normal ones concentrated in the origin.

## 4. Experimental Evaluation

## 4.1. Datasets

For the evaluation of our proposed approach and models, we used the NetFlow versions of two publicly available NIDS datasets, UNSW-NB15 [17] and CIC-2018 [12]. These are the two most-cited NIDS benchmark datasets among the recent NIDS datasets, providing a more realistic representation of to day’s network trafic in comparison to older benchmark datasets such as NSL-KDD [18].

The original UNSW-NB15 dataset was generated and published by researchers at the University of New South Wales at the Australian Defence Force Academy Canberra in 2015. The second dataset, CIC-2018, was collected from a completely different network setup and published by the Canadian Institute for Cybersecurity (CIC), University of New Brunswick (UNB), in 2018.

The original versions of these datasets are published with two very diferent feature sets, with only six common features across the two sets, out of a total of 42 and 75 features of UNSW-NB15 and CIC-2018 datasets respectively [26]. This generally makes it impossible to fairly compare the performance of ML models on both datasets.

Therefore, a common feature set was needed for the crossdomain evaluation of our ML models. Accordingly, we used the NFv2-UNSW-NB15 and NFv2-CIC-2018 datasets, that were converted to NetFlow from their original formats in [27]. Net-Flow is the de facto standard in network flow reporting and is widely deployed in real-world networks. The features in the NetFlow versions of these datasets are comprised of 43 Net-Flow version 9 fields, which represent bi-directional network flows<sup>1</sup>.

Figure 4 shows the class distributions for these two datasets. The NFv2-UNSW-NB15 dataset includes 2,390,275 flows, labelled as either Benign/background trafic, or one of the 9 attack classes. The Benign class makes up 96.02% of the entire dataset. The NFv2-CIC-2018 dataset consists of 18,893,708 flows, which are either Benign or belong to one of the 14 at tack classes, including various DoS and DDoS attacks, SQL Injection, Infiltration and Brute Force attacks. In this dataset, 88.05% of the flows are Benign.

Since the focus of this paper is on binary classification, all the various attack classes in each dataset are aggregated into a single class called Attack. However, the nature of this Attack class is totally diferent for each dataset. Indeed, the number of attack types, the number of flows belonging to each attack type and the ratio of number of flows in each attack type to total flows are diferent in each dataset. Even the attacks with similar names from two datasets, such as DoS (from NFv2-UNSW NB15) and DoS attacks-Slowloris (from NFv2-CIC-2018) rep resent completely diferent types of attacks.

Consequently, these datasets not only represent diferent network environments, as they have been generated in com pletely diferent networks, they represent domains with diferent label sets. This is also reflected in previous studies such as [4], where it is shown that the performance of conventional ML models trained on one of theses datasets severely degrades when tested on the other dataset. Another previous study [1] has also shown the diference between the feature distributions in the benign/background trafic of various NIDS datasets.

![](images/31f109b7c440a1ede3ec9c4c7c9038f27d1a55c47885b6d3f469313a10326675.jpg)  
(a) NFv2-UNSW-NB15

![](images/e86ee7771081a76cce3be3d9c8e657d8754d27d1c5a6507b5fa62012bb698395.jpg)  
(b) NFv2-CIC-2018  
Figure 4: Class distribution for the datasets used in this study a)NFv2-UNSW-NB15 and b)NFv2-CIC-2018

## 4.2. Domain Invariant Projection

The main purpose of the DANN component is the projection of the input data into a domain invariant space. In order to investigate this for the two NIDS datasets used in this study, we compare the separation of the two datasets before and after the domain invariant projection via DANN. The input datasets have 43 features, and after passing them through the Feature Extractor $( G _ { f } )$ of the DANN component, are reduced to 10 features (number of nodes on the output layer of $G _ { f } )$ , as can be seen in Figure 1.

Figure 5-(a) shows the visualisation of the two embed ded input datasets. This visualisation is generated by reducing the dimensionality of the data from 43 to 2, using the isomap [28] embedding algorithm. Similarly, Figure 5-(b) and (c) show the visualisation of datasets after projection via DANN $( G _ { f }$ network), trained on NFv2-UNSW-NB15 (referred

![](images/fb31e22e2c14fb53181c333d4d9eb3b63ec2efc32bc8a8a90a4d656d7937a6c5.jpg)  
(a) Embedded Input Data

![](images/f330be4d5f232f3df92719e3639d933ec2636c97ec2ba06feb2c389c6144e45c.jpg)  
(b) Embedded DANN-1 Projected Data

![](images/99df762402231e2ec4a650ba2a009d482c7006b522b316ebe0a5cd99c51a6fcc.jpg)  
(c) Embedded DANN-2 Projected Data  
Figure 5: Illustrating the domain shift before and after DANN projection for the two NIDS datasets used in this study. (a) Input data, and DANN projection via training on b) NFv2-UNSW-NB15 and (c) NFv2-CIC-2018

to as DANN1) and trained on NFv2-CIC-2018 (referred to as DANN2) datasets respectively. As in the case of the original input datasets, isomap is used to reduce the dimensions of the DANN-projected datasets from 10 to 2. As can be seen, the separation of the two embedded input datasets is significant in Figure 5-(a). This means that there is a considerable distribu tion shift between the two input datasets. Accordingly, it is not expected that an ML model trained on one of these datasets to perform well when evaluated on the other dataset. However, after the DANN projection, as can be seen in both Figure 5- (b) and Figure 5-(c), the embedded data points show significantly less separation, indicating that the feature distributions are much closer, which was the aim. Hence, we expect an ML model, such as OSVM, trained on either of the DANN projected features, to perform well on the other one, and we therefore expect the DI-NIDS to exhibit a higher degree of domain invariance. We will confirm this expectation via a detailed experimental evaluation of DI-NIDS in following subsection.

## 4.3. Results

In order to evaluate the proposed DI-NIDS framework, we performed three sets of experiments. In the first set of experi ments, DI-NIDS was evaluated in a domain-specific setup on our chosen two benchmark datasets, i.e., it was trained and tested on the same dataset, for each dataset separately. In the second and third sets of experiments, we evaluated DI-NIDS in a cross-domain setup, i.e., with training on one dataset and testing on the other. First, one dataset was used as the train/source, and the other dataset as the test/target dataset. Then, we swapped the train/source and test/target datasets and ran the evaluation again, in order to obtain the cross-domain performance in both directions. The domain-specific evaluation mainly serves as a baseline, i.e., to compare the performance to the cross-domain evaluation scenario.

Since there is no previous study of domain adaptation using the same NIDS datasets that we are using in this study, we rely on the results published in one of our previous works [4], which includes both cross-domain and domain-specific evaluation of conventional deep and shallow machine learning mod els. The models used from this study include a long short-term memory (LSTM) model and two shallow learning methods, i.e., Extra-Tree and Random-Forest. In addition to the model performance results provided in [4], we also used an MLP (Feed Forward) model in this study, to provide an additional baseline result. This MLP model is similar to the MLP model utilised to create the DANN, i.e., a combination of the $G _ { f }$ and $G _ { C }$ blocks of the DANN, as shown in Figure 3-(a). Selecting similar models in the DANN component of DI-NIDS and the baseline MLP allowed us to evaluate the role of the augmenting block $G _ { D }$ in the cross-domain evaluation. Tables 2 and 3 show the parameters of the conventional deep and shallow learning models used for the comparison.

Table 2: The model parameters for two deep learning-based NIDSs along with the other parameters for training and evaluation of the models

<table><tr><td>Parameter</td><td>Feed Forward</td><td>LSTM</td></tr><tr><td>No. Hidden Layers</td><td>3</td><td>4</td></tr><tr><td>No. Nodes (each layer)</td><td>10</td><td>10</td></tr><tr><td>Learning Rate</td><td>0.0001</td><td>0.0001</td></tr><tr><td>Dropout Ratio</td><td>0.2</td><td>0.2</td></tr><tr><td>Batch Size</td><td>512</td><td>512</td></tr><tr><td>Validation Split</td><td>0.3</td><td>0.3</td></tr><tr><td>No. of Folds</td><td>5</td><td>5</td></tr></table>

Table 3: The model parameters for two shallow learning-based NIDSs along with the other parameters for training and evaluation of the models

<table><tr><td>Parameter</td><td>Random Forest</td><td>Extra Tree</td></tr><tr><td>ccp_alpha</td><td>0.001</td><td>0.001</td></tr><tr><td>Batch Size</td><td>512</td><td>512</td></tr><tr><td>Validation Split</td><td>0.3</td><td>0.3</td></tr><tr><td>No. of Folds</td><td>5</td><td>5</td></tr></table>

In addition to these conventional ML models, we also in cluded the OSVM and DANN blocks individually in our eval uation. This allowed us to evaluate the performance of DI-NIDS and compare it with the performance of its key building blocks separately. For the evaluation of OSVM and DANN, each of these models was separately trained and evaluated. In the case of domain-specific evaluation, these models were trained and tested on NFv2-UNSW-NB15 and NFv2-CIC-2018 datasets separately. In the case of the cross-domain evaluation, each model was once trained on NFv2-UNSW-NB15 and tested on NFv2-CIC-2018 and then trained on NFv2-CIC-2018 and tested against NFv2-UNSW-NB15.

Table 4 shows the results (F1-Score) of domain-specific performance evaluation for DI-NIDS, and the six baseline ML models used for comparison. As can be seen, while the per formance of all the models are largely similar on both NIDS datasets, DANN and DI-NIDS show the best performance on the NFv2-CIC-2018 and NFv2-UNSW-NB15 datasets respectively.

Figure 6 shows the average domain-specific performance (F1-Score) of the considered models for the two datasets, as stated in Table 4. As can be seen, DI-NIDS has the highest av erage performance on these two datasets, closely followed by OSVM and DANN. While the main idea of proposing DI-NIDS is to address the low cross-domain performance of conven tional ML-based NIDSs, the fact that DI-NIDS has the highest domain-specific performance among all the considered models is very promising.

![](images/1c1d6a64b80e2bf16f2b7cd5dddea4c5a6682429f8b4242f24db1240bf8ac9d5.jpg)  
Figure 6: Average domain-specific F1-Score of various ML models on two datasets NFv2-CIC-2018 and NFv2-UNSW-NB15 (shown in Table 4) where the test and training datasets are the same

Table 4: Domain-specific performance (F1-Score (%)) of various ML models compared to DANN, OSVM and DI-NIDS when trained and evaluated on the same dataset

<table><tr><td>ML Model</td><td>NFv2-CIC-2018</td><td>NFv2-UNSW-NB15</td></tr><tr><td>Random-Forest [4]</td><td>95.44%</td><td>92.17%</td></tr><tr><td>Extra Tree [4]</td><td>84.62%</td><td>91.73%</td></tr><tr><td>LSTM NN [4]</td><td>90.17%</td><td>92.82%</td></tr><tr><td>Feed Forward NN*</td><td>97.72%</td><td>92.24%</td></tr><tr><td>OSVM</td><td>92.97%</td><td>98.28%</td></tr><tr><td>DANN</td><td>97.81%</td><td>93.38%</td></tr><tr><td>DI-NIDS</td><td>93.23%</td><td>98.68%</td></tr></table>

\* The Feed Forward Neural Network as depicted in Figure 3-a

In the next set of experiments, we compared the performance of DI-NIDS to the other models in two cross-domain setups. In this setting, first each model is trained on the NFv2- CIC-2018 dataset, and then tested against the NFv2-UNSW-NB15 dataset.Then the source and target domains are swapped, i.e., the models are trained on NFv2-UNSW-NB15 and tested against NFv2-CIC-2018. Tables 5 and 6 show the results of these evaluations respectively. Similar to the domain-specific evaluation, we used the results of the Random-Forest, Extra-Tree and LSTM models on the same datasets from [4] for crossdomain evaluation. For the Feed Forward model (MLP), simi lar to the domain-specific evaluation, we used the same network setting/parameters as mentioned in Table 2.

In both tables, the first column shows the model name, the second column shows its cross-domain performance and the third column shows the diference between the cross-domain performance and its corresponding domain-specific evaluation. For instance, in Table 5 the Random-Forest model has a F1- Score of 0 84% when trained on NFv2-CIC-2018 and tested against NFv2-UNSW-NB15. This is 94 60% lower than its performance (F1-Score) when trained and tested on NFv2-CIC 2018, as shown in the first column of Table 4. Accordingly, the third column of Table 5 shows 94 60% for the performance degradation of the Random-Forest model.

As can be seen, OSVM is the best performing model when NFv2-CIC-2018 is the source and NFv2-UNSW-NB15 is the target domain. In this case, the performance (F1-Score) of DI-NIDS is only 0 36% lower than ons-class SVM, i.e., 85 79%. While this is a great result for OSVM in regards to domain adaptation, the next evaluation shows an entirely diferent results.

Table 5: Cross-domain performance (F1-Score (%)) and its diference to the corresponding domain-specific performance of DI-NIDS and conventional ML models for the case where source domain is NFv2-CIC-2018 and the target domain is NFv2-UNSW-NB15

<table><tr><td>ML Model</td><td>F1-Score (%)</td><td>Performance Degradation</td></tr><tr><td>Random-Forest [4]</td><td>0.84%</td><td>94.60%</td></tr><tr><td>Extra Tree [4]</td><td>0.57%</td><td>84.05%</td></tr><tr><td>LSTM NN [4]</td><td>9.63%</td><td>80.54%</td></tr><tr><td>Feed Forward NN*</td><td>3.09%</td><td>94.63%</td></tr><tr><td>OSVM</td><td>86.15%</td><td>6.79%</td></tr><tr><td>DANN</td><td>17.31%</td><td>80.50%</td></tr><tr><td>DI-NIDS</td><td>85.79%</td><td>7.44%</td></tr></table>

\* The Feed Forward Neural Network as depicted in Figure 3-a

Table 6: Cross-domain performance (F1-Score (%)) and its diference to the corresponding domain-specific performance of DI-NIDS and conventional ML models for the case where source domain is NFv2-UNSW-NB15 and the target domain is NFv2-CIC-2018

<table><tr><td>ML Model</td><td>F1-Score (%)</td><td>Performance Degradation</td></tr><tr><td>Random-Forest [4]</td><td>7.70%</td><td>84.47%</td></tr><tr><td>Extra Tree [4]</td><td>17.47%</td><td>74.26%</td></tr><tr><td>LSTM NN [4]</td><td>14.20%</td><td>78.62%</td></tr><tr><td>Feed Forward NN*</td><td>30.79%</td><td>61.45%</td></tr><tr><td>OSVM</td><td>15.74%</td><td>82.54%</td></tr><tr><td>DANN</td><td>61.94%</td><td>31.44%</td></tr><tr><td>DI-NIDS</td><td>93.29%</td><td>5.39%</td></tr></table>

\* The Feed Forward Neural Network as depicted in Figure 3-a

The results in Table 6 indicate that DI-NIDS is the best performing model in the second experiment, with a signifi cant advantage over the other models. In fact, DI-NIDS is the only model capable of maintaining its performance over the two cross-domain experiments. It has a 7 44% performance degradation in the first cross-domain experiment and 5 39%. OSVM, which was the best performing model in the first experiment, only achieves an F1-Score of 15 74% in this experiment, with 82 54% degradation compared to its corresponding domain-specific performance.

Figure 7 shows the average performance (F1-Score) of the models for the two cross-domain experiments. As can be seen, all the conventional ML models, including Random-Forest, Extra-Tree, LSTM and Feed Forward, have very low average cross-domain performance, no better than 16 94%. The OSVM and DANN models are somewhat better, with average cross-domain performances of 50 96% and 39 63% respec tively. However, they are still far from a truly domain invariant model, i.e., a model that is capable of maintaining its perfor mance in the presence of domain shifts. This is in clear contrast to DI-NIDS, which largely maintains its performance, with an average cross-domain performance of 89.54/

![](images/c55dd78db9a548278a0f39b9d92037184795607486adb477adbd21f5244e5a02.jpg)  
Figure 7: Averaged cross-domain performance (F1-Score) of ML models across two cross-domain experiments

## 4.4. Comparison to Baseline Results

While there is no previous work evaluating the crossdomain performance of NIDSs using the same set of datasets as used in this study, there is a previous work [14] running similar experiments using other datasets. The authors of [14] used two versions of the CIC-IDS dataset in their original format [12], CIC-2017 and CIC-2019, for their cross-domain evaluations. Although we cannot compare the absolute performance numbers, we believe it is possible to compare the corresponding degree of performance degradation from the domain-specific to the cross-domain evaluation scenario.

Table 7 shows the performances of DI-NIDS compared to the relevant state-of-the-art [14]. Here, each model is indepen dently trained on two datasets, and evaluated on the training dataset (domain-specific evaluation), as well as the other, unseen dataset (cross-domain evaluation). The cross-domain results are shown as shaded cells in the table. The first column indicates the model, followed by the training dataset and the test dataset. The fourth column shows the corresponding F1- Scores.

The fifth column presents the cross-domain degradation, i.e. the diference between the F1-Score achieved in the domain-specific evaluation and the corresponding crossdomain evaluation. Finally, the sixth column shows the crossdomain degradation average across the two test and train dataset combinations.

While the absolute performance numbers of DI-NIDS and [14] in the table might not be comparable due the the use of diferent datasets, we argue that it is reasonable to compare the corresponding cross-domain degradation figures. We can see that the cross-domain degradation values of DI-NIDS are 7.44% and 5.39% for the two ’directions’ of evaluation, compared to 11.10% and 27.50% of [14].

Table 7: Cross-domain performance comparison degradation (Degr.) comparison

<table><tr><td>Model</td><td>Train Dataset</td><td>Test Dataset</td><td>F1-Score (%)</td><td>Degr. (%)</td><td>Avg. Degr. (%)</td></tr><tr><td rowspan="4">Pontes et al. [14]</td><td rowspan="2">CIC-2017</td><td>CIC-2017</td><td>89.80</td><td rowspan="2">11.10</td><td rowspan="4">19.30</td></tr><tr><td>CIC-2019</td><td>78.70</td></tr><tr><td rowspan="2">CIC-2019</td><td>CIC-2019</td><td>91.60</td><td rowspan="2">27.50</td></tr><tr><td>CIC-2017</td><td>64.10</td></tr><tr><td rowspan="4">DI-NIDS</td><td rowspan="2">NFv2-CIC-2018</td><td>NFv2-CIC-2018</td><td>93.23</td><td rowspan="2">7.44</td><td rowspan="4">6.42</td></tr><tr><td>NFv2-UNSW-NB15</td><td>85.79</td></tr><tr><td rowspan="2">NFv2-UNSW-NB15</td><td>NFv2-UNSW-NB15</td><td>98.68</td><td rowspan="2">5.39</td></tr><tr><td>NFv2-CIC-2018</td><td>93.29</td></tr></table>

One of the benefits of DI-NIDS is that its performance degradation is relatively consistent across the two directions of cross-domain evaluation, with only a (absolute) diference of 2% between the two values. In contrast, the the model pro posed in [14] is sensitive to the direction of cross-domain eval uation, and exhibits a higher degree of variance, with diference of more than 16% between the two directions of evaluation.

Furthermore, and more importantly, the average crossdomain degradation of DI-NIDS is only 6.42%, compared to 19.3% to the relevant state-of-the-art [14]. This is a significant improvement in terms of cross-domain performance, and represents a step towards more domain invariant, and hence practical ML-based NIDSs.

## 5. Conclusion

This paper proposes a domain-invariant network intrusion detection system (NIDS) framework to address the shortcomings of the existing NIDSs in regards to distribution shifts in data. While domain adaptation methods to address the problem of distribution shift have been extensively studied in a range of machine learning application areas, it has not received significant attention in the context of ML-based NIDSs. This is despite the fact there are likely to be significant distribution shifts between training datasets and test data, in particular be tween (synthetic) training datasets and real-world production networks, such as shown in [1]. As we demonstrate in this pa per, standard domain adaptation (DA) methods based on a supervised learning approach do not work very well for NIDSs. One of the key reasons is that the existing DA approaches generally assume balanced datasets. Realistic datasets (and net work trafic in general) in the context of NIDS are highly im balanced, with attack or anomalous trafic representing only a small proportion of the overall network trafic.

In order to address this gap, this paper proposes DI-NIDS, a domain invariant NIDS framework that takes into account the highly imbalanced nature of network trafic, while eficiently addressing the distribution shift between source and target do mains. DI-NIDS achieves this by using a Domain-Adversarial Neural Network (DANN) to project the data into a domaininvariant feature space. The DANN is trained using data and labels from the source domain, and unlabelled data from the target domain. DI-NIDS learns features that discriminate be tween classes in the source domain, but that do not discrimi nate between the source and target domains. It leverages the feature extractor network of the trained DANN, and uses an OSVM model for the downstream task of trafic classification and anomaly detection. Our experimental results show that, in addition to achieving excellent domain-specific classifica tion performance, DI-NIDS significantly improves the crossdomain performance over the relevant state-of-the-art. We be lieve that improving the domain invariance, and robustness against feature distribution shifts, for ML-based NIDSs is an important step towards a more widespread deployment of such systems in practical real-world networks.

## 6. Acknowledgement

This research is made possible by an Advance Queensland Industry Research Fellowship, grant number RM2019002409.

## References

[1] S. Layeghy, M. Gallagher, and M. Portmann, “Benchmarking the Benchmark - Analysis of Synthetic NIDS Datasets,” arXiv preprint arXiv:2104.09029, 2021.

[2] S. M. Erfani, M. Baktashmotlagh, M. Moshtaghi, V. Nguyen, C. Leckie, J. Bailey, and K. Ramamohanarao, “Robust Domain Generalisation by Enforcing Distribution Invariance,” in IJCAI International Joint Confer ence on Artificial Intelligence, vol. 2016-Janua, pp. 1455–1461, 2016.

[3] S. Al-riyami, F. Coenen, and A. Lisitsa, “A Re-evaluation of Intrusion Detection Accuracy : an Alternative Evaluation Strategy,” in ACM SIGSAC Conference on Computer and Communications Security, pp. 2195–2197, 2018.

[4] S. Layeghy and M. Portmann, “On Generalisability of Machine Learningbased Network Intrusion Detection Systems,” 2022.

[5] Mohammad J. Hashemi, Detecting Anomalies in Network Systems by Leveraging Neural Networks. PhD thesis, University of Colorado, 2021.

[6] M. Baktashmotlagh, M. T. Harandi, B. C. Lovell, and M. Salzmann, “Unsupervised Domain Adaptation by Domain Invariant Projection,” Proceedings of the IEEE International Conference on Computer Vision, pp. 769–776, 2013.

[7] Y. Ganin, E. Ustinova, H. Ajakan, P. Germain, H. Larochelle, F. Laviolette, M. Marchand, V. Lempitsky, U. Dogan, M. Kloft, F. Orabona, T. Tommasi, and A. Ganin, “Domain-Adversarial Training of Neural Net works,” Journal ofMachine Learning Research, vol. 17, pp. 1–35, 2016.

[8] B. Scholkopf, R. Williamson, A. Smola, J. Shawe-taylor, and J. Platt, “Support Vector Method for Novelty Detection,” in Advances in Neural Information Processing Systems 12, pp. 1–7, 1999.

[9] D. Brauckhof, A. Wagner, and M. May, “FLAME: A Flow-Level Anomaly Modeling Engine,” in Workshop on Cyber Security Experimentation and Test (Terry Benzel, ed.), (San Jose, California, USA - CSET), p. 6, USENIX Association, 2008.

[10] Y. Zhang and J. Yan, “Semi-Supervised Domain-Adversarial Training for Intrusion Detection against False Data Injection in the Smart Grid,” Proceedings ofthe International Joint Conference on Neural Networks, 2020.

[11] Y. Fan, Y. Li, H. Cui, H. Yang, and Y. Zhang, “An Intrusion Detection Framework for IoT Using Partial Domain Adaptation,” in International Conference on Science of Cyber Security, vol. 2, pp. 36–50, Springer International Publishing, 2021.

[12] I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, “Toward Generating a New Intrusion Detection Dataset and Intrusion Trafic Characterization,” ICISSP 2018 - Proceedings ofthe 4th International Conference on Information Systems Security and Privacy, vol. 2018-January, pp. 108–116, 2018.

[13] Yisroel Mirsky, Tomer Doitshman, Yuval Elovici, Asaf Shabtai, Y. Mirsky, T. Doitshman, Y. Elovici, and A. Shabtai, “Kitsune: an Ensemble of Autoencoders for Online Network Intrusion Detection,” arXiv preprint arXiv:1802.09089, no. February, pp. 18–21, 2018.

[14] C. F. T. Pontes, M. M. C. D. Souza, J. J. C. Gondim, M. Bishop, and M. A. Marotta, “A New Method for Flow-Based Network Intrusion Detection Using the Inverse Potts Model,” IEEE Transaction on Network and Service Management, vol. 18, no. 2, pp. 1125–1136, 2021.

[15] O. Ajayi and A. Gangopadhyay, “DAHID : Domain Adaptive Host-based Intrusion Detection,” in IEEE International Conference on Cyber Security and Resilience (CSR) Workshops DAHID:, pp. 467–472, IEEE, 2021.

[16] A. Singla, E. Bertino, and D. Verma, “Preparing Network Intrusion Detection Deep Learning Models with Minimal Data Using Adversarial Domain Adaptation,” in ACM SIGSAC Conference on Computer and Communications Security, pp. 127–140. 2020

[17] N. Moustafa and J. Slay, “UNSW-NB15: A Comprehensive Data Set for Network Intrusion Detection Systems (UNSW-NB15 Network Data Set),” in Military communications and information systems conference (MilCIS) (pp. 1-6). IEEE., pp. 1–6, IEEE, 2015.

[18] M. Tavallaee, E. Bagheri, W. Lu, and A. A. Ghorbani, “A detailed Analysis of the KDD CUP 99 Data Set,” in 2009 IEEE Symposium on Computational Intelligence for Security and Defense Applications, pp. 1–6, 2009.

[19] A. G. B, I. Odebode, and Y. Yesha, “A Domain Adaptation Technique for Deep Learning in Cybersecurity,” in OTM Confederated International Conferences” On the Move to Meaningful Internet Systems”, vol. 1, pp. 221–228, Springer International Publishing, 2020.

[20] P. Wu, H. Guo, and R. Buckland, “A Transfer Learning Approach for Network Intrusion Detection,” in 4th IEEE International Conference on Big Data Analytics, 2019.

[21] Y. X. Yingying Xu, Zhi Liu, Yanmiao Li, Yushuo Zheng, Haixia Hou, Mingcheng Gao, Yongsheng Song, Y. Xu, Z. Liu, Y. Li, Y. Zheng, H. M. G. Hou, Y. Song, and Y. Xin, “Intrusion Detection Based on Fusing Deep Neural Networks and Transfer Learning,” in International Forum on Digital TV and Wireless Multimedia Communications., vol. 1, pp. 212– 221, Springer Singapore, 2020.

[22] University of California, Irvine, “KDD Cup 1999 Data.” http://kdd. ics.uci.edu/databases/kddcup99/kddcup99.html, 1999. Ac cessed: 2020-07-30.

[23] P. Oza, H. V. Nguyen, and V. M. Patel, “Multiple Class Novelty Detection Under Data Distribution Shift,” Lecture Notes in Computer Science (including subseries Lecture Notes in Artificial Intelligence and Lecture Notes in Bioinformatics), vol. 12352 LNCS, pp. 432–449, 2020.

[24] C. Cortes and V. Vapnik, “Support-Vector Networks,” Machine Learning, vol. 20, no. 3, pp. 273–297, 1995.

[25] R. Vlasveld, “Introduction to One-Class Support Vector Machines.” http://rvlasveld.github.io/blog/2013/07/12/ introduction-to-one-class-support-vector-machines/, Jul 2013.

[26] M. Sarhan, S. Layeghy, N. Moustafa, and M. Portmann, “Netflow Datasets for Machine Learning-based Network Intrusion Detection Systems,” arXiv preprint arXiv:2011.09144, 2020.

[27] M. Sarhan, S. Layeghy, N. Moustafa, and M. Portmann, “Towards a Standard Feature Set of NIDS Datasets,” arXiv preprint arXiv:2101.11315, 2021.

[28] J. B. Tenenbaum, V. De Silva, and J. C. Langford, “A global geometric framework for nonlinear dimensionality reduction,” Science, vol. 290, no. 5500, pp. 2319–2323, 2000.