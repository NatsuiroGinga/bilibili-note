---
title: "2024-Wang-Hierarchical-Neyman-Pearson-Classification"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2024-Wang-Hierarchical-Neyman-Pearson-Classification.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Hierarchical Neyman-Pearson Classification for Prioritizing Severe Disease Categories in COVID-19 Patient Data

Lijia Wang ∗ School of Data Science, City University of Hong Kong Y. X. Rachel Wang <sup>∗</sup> <sup>†</sup> School of Mathematics and Statistics, University of Sydney Jingyi Jessica Li Department of Statistics, University of California, Los Angeles Xin Tong Department of Data Sciences and Operations, University of Southern California October 2, 2023

## Abstract

COVID-19 has a spectrum of disease severity, ranging from asymptomatic to requiring hospitalization. Understanding the mechanisms driving disease severity is crucial for developing efective treatments and reducing mortality rates. One way to gain such understanding is using a multi-class classification framework, in which patients’ biological features are used to predict patients’ severity classes. In this severity classification problem, it is beneficial to prioritize the identification of more severe classes and control the “under-classification” errors, in which patients are misclassified into less severe categories. The Neyman-Pearson (NP) classification paradigm has been developed to prioritize the designated type of error. However, current NP procedures are either for binary classification or do not provide high probability controls on the prioritized errors in multi-class classification. Here, we propose a hierarchical NP (H-NP) framework and an umbrella algorithm that generally adapts to popular classification methods and controls the under-classification errors with high probability. On an integrated collection of single-cell RNA-seq (scRNA-seq) datasets for 864 patients, we explore ways of featurization and demonstrate the eficacy of the H-NP algorithm in controlling the under-classification errors regardless of featurization. Beyond COVID-19 severity classification, the H-NP algorithm generally applies to multi-class classification problems, where classes have a priority order.

## 1 Introduction

The COVID-19 pandemic has infected over 767 million people and caused 6.94 million deaths (27 June 2023) [World Health Organization, 2023], prompting collective eforts from statistics and other communities to address data-driven challenges. Many statistical works have modeled epidemic dynamics [Betensky and Feng, 2020, Quick et al., 2021], forecasted the case growth rates and outbreak locations [Brooks et al., 2020, Tang et al., 2021, Mc-Donald et al., 2021], and analyzed and predicted the mortality rates [James et al., 2021, Kramlinger et al., 2022]. Classification problems, such as diagnosis (positive/negative) [Wu et al., 2020, Li et al., 2020, Zhang et al., 2021] and severity prediction [Yan et al., 2020, Sun et al., 2020, Zhao et al., 2020, Ortiz et al., 2022], have been tackled by machine learning approaches (e.g., logistic regression, support vector machine (SVM), random forest, boosting, and neural networks; see Alballa and Al-Turaiki [2021] for a review).

In the existing COVID-19 classification works, the commonly used data types are CT images, routine blood tests, and other clinical data including age, blood pressure and medical history [Meraihi et al., 2022]. In comparison, multiomics data are harder to acquire but can provide better insights into the molecular features driving patient responses [Overmyer et al., 2021]. Recently, the increasing availability of single-cell RNA-seq (scRNA-seq) data ofers the opportunity to understand transcriptional responses to COVID-19 severity at the cellular level [Wilk et al., 2020, Stephenson et al., 2021, Ren et al., 2021].

More generally, genome-wide gene expression measurements have been routinely used in classification settings to characterize and distinguish disease subtypes, both in bulk-sample [Aibar et al., 2015] and, more recently, single-cell level [Arvaniti and Claassen, 2017, Hu et al., 2019]. While such genome-wide data can be costly, they provide a comprehensive view of the transcriptome and can unveil significant gene expression patterns for diseases with complex pathophysiology, where multiple genes and pathways are involved. Furthermore, as the patient-level measurements continue to grow in dimension and complexity (e.g., from a single bulk sample to thousands-to-millions of cells per patient), a supervised learning setting enables us to better establish the connection between patient-level features and their associated disease states, paving the way towards personalized treatment.

In this study, we focus on patient severity classification using an integrated collection of multi-patient scRNA-seq datasets. Based on the WHO guidelines [World Health Organization, 2020], COVID-19 patients have at least three severity categories: healthy, mild/moderate, and severe. The classical classification paradigm aims at minimizing the overall classification error. However, prioritizing the identification of more severe patients may provide important insights into the biological mechanisms underlying disease progression and severity, and facilitate the discovery of potential biomarkers for clinical diagnosis and therapeutic intervention. Consequently, it is important to prioritize the control of “under-classification” errors, in which patients are misclassified into less severe categories.

Motivated by the gap in existing classification algorithms for severity classification (Section 1.1), we propose a hierarchical Neyman-Pearson (H-NP) classification framework that prioritizes the under-classification error control in the following sense. Suppose there are I classes with class labels $[ \mathcal { T } ] = \{ 1 , 2 , \dots , \mathcal { T } \}$ ordered in decreasing severity. For $i \in [ \mathcal { I } - 1 ]$ the i-th under-classification error is the probability of misclassifying an individual in class i into any class j with $j > i$ . We develop an H-NP umbrella algorithm that controls the i-th under-classification error below a user-specified level $\alpha _ { i } \in ( 0 , 1 )$ with high probability while minimizing a weighted sum of the remaining classification errors. Similar in spirit to the NP umbrella algorithm for binary classification in Tong et al. [2018], the H-NP umbrella algorithm adapts to popular scoring-type multi-class classification methods (e.g., logistic regression, random forest, and SVM). To our knowledge, the algorithm is the first to achieve asymmetric error control with high probability in multi-class classification.

Another contribution of this study is the exploration of appropriate ways to featurize multi-patient scRNA-seq data. Following the workflow in Lin et al. [2022a], we integrate 20 publicly available scRNA-seq datasets to form a sample of 864 patients with three levels of severity. For each patient, scRNA-seq data were collected from peripheral blood mononuclear cells (PBMCs) and processed into a sparse expression matrix, which consists of tens of thousands of genes in rows and thousands of cells in columns. We propose four ways of extracting a feature vector from each of these 864 matrices. Then we evaluate the performance of each featurization way in combination with multiple classification methods under both the classical and H-NP classification paradigms. We note that our H-NP umbrella algorithm is applicable to other featurizations of scRNA-seq data, other forms of patient data, and more general disease classification problems with a severity ordering.

Below we review the NP paradigm and featurization of multi-patient scRNA-seq data as the background of our work.

## 1.1 Neyman-Pearson paradigm and multi-class classification

Classical binary classification focuses on minimizing the overall classification error, i.e., a weighted sum of type I and II errors, where the weights are the marginal probabilities of the two classes. However, the class priorities are not reflected by the class weights in many applications, especially disease severity classification, where the severe class is the minor class and has a smaller weight (e.g., HIV [Meyer and Pauker, 1987] and cancer [Dettling and B¨uhlmann, 2003]). One class of methods that addresses this error asymmetry is costsensitive learning [Elkan, 2001, Margineantu, 2002], which assigns diferent costs to type I and type II errors. However, such weights may not be easy to choose in practice, especially in a multi-class setting; nor do these methods provide high probability controls on the prioritized errors. The NP classification paradigm [Cannon et al., 2002, Scott and Nowak, 2005, Rigollet and Tong, 2011] was developed as an alternative framework to enforce class priorities: it finds a classifier that controls the population type I error (the prioritized error, e.g., misclassifying diseased patients as healthy) under a user-specified level α while minimizing the type II error (the error with less priority, e.g., misdiagnosing healthy people as sick). Practically, using an order statistics approach, Tong et al. [2018] proposed an NP umbrella algorithm that adapts all scoring-type classification methods (e.g., logistic regression) to the NP paradigm for classifier construction. The resulting classifier has the population type I error under α with high probability. Besides disease severity classification, the NP classification paradigm has found diverse applications, including social media text classification [Xia et al., 2021] and crisis risk control [Feng et al., 2021]. Nevertheless, the original NP paradigm is for binary classification only.

Although several works aimed to control prioritized errors in multi-class classification [Landgrebe and Duin, 2005, Xiong et al., 2006, Tian and Feng, 2021], they did not provide high probability control. That is, if they are applied to severe disease classification, there is a non-trivial chance that their under-classification errors exceed the desired levels.

## 1.2 ScRNA-seq data featurization

In multi-patient scRNA-seq data, every patient has a gene-by-cell expression matrix; genes are matched across patients, but cells are not. For learning tasks with patients as instances, featurization is a necessary step to ensure that all patients have feautures in the same space. A common featurization approach is to assign every patient’s cells into cell types, which are comparable across patients, by clustering [Stanley et al., 2020, Ganio et al., 2020] and/or manual annotation [Han et al., 2019]. Then, each patient’s gene-by-cell expression matrix can be converted into a gene-by-cell-type expression matrix using a summary statistic (e.g., every gene’s mean expression in a cell type), so all patients have gene-by-cell-type expression matrices with the same dimensions. We note here that most of the previous multi-patient single-cell studies with a reasonably large cohort used CyTOF data [Davis et al., 2017], which typically measures 50–100 protein markers, whereas scRNA-seq data have a much higher feature dimension, containing expression values of ∼ 10<sup>4</sup> genes. Thus further featurization is necessary to convert each patient’s gene-by-cell-type expression matrix into a feature vector for classification.

Following the data processing workflow in Lin et al. [2022a], we obtain 864 patients cell-type-by-gene expression matrices, which include 18 cell types and 3,000 genes (after filtering). We propose and compare four ways of featurizing these matrices into vectors, which difer in their treatments of 0 values and approaches to dimension reduction. Note that we perform featurization as a separate step before classification so that all classification methods are applicable. Separating the featurization step also allows us to investigate whether a featurization way maintains robust performance across classification methods.

The rest of the paper is organized as follows. In Section 2, we introduce the H-NP classification framework and propose an umbrella algorithm to control the under-classification errors with high probability. Next, we conduct extensive simulation studies to evaluate the performance of the umbrella algorithm. In Section 3, we describe four ways of featurizing the COVID-19 multi-patient scRNA-seq data and show that the H-NP umbrella algorithm consistently controls the under-classification errors in COVID-19 severity classification across all featurization ways and classification methods. Furthermore, we demonstrate that utilizing the scRNA-seq data allows us to gain biological insights into the mechanism and immune response of severe patients at both the cell-type and gene levels. Supplemen tary Materials contain technical derivations, proofs and additional numerical results.

## 2 Hierarchical Neyman-Pearson (H-NP) classification

## 2.1 Under-classification errors in H-NP classification

We first introduce the formulation of H-NP classification and define the under-classification errors, which are the probabilities of individuals being misclassified to less severe (more generally, less important) classes. In an H-NP problem with $\mathcal { Z } \geq 2$ classes, the class labels $i \in [ \mathcal { T } ] : = \{ 1 , 2 , \dots , \mathcal { T } \}$ are ranked in a decreasing order of importance, i.e., class i is more important than class j if $\dot { \textit { i } } < j$ . Let $( X , Y )$ be a random pair, where $X \in \mathcal { X } \subset \mathbb { R } ^ { d }$ represents a vector of features, and $Y \in [ \mathcal { T } ]$ denotes the class label. A classifier $\phi : \mathcal { X }  [ \mathcal { T } ]$ maps a feature vector X to a predicted class label. In the following discussion, we abbreviate $\mathbb { P } ( \cdot \mid Y = i )$ as $P _ { i } ( \cdot )$ . Our H-NP framework aims to control the under-classification errors at the population level in the sense that

$$
R _ {i \star} (\phi) = P _ {i} (\phi (X) \in \{i + 1, \dots , \mathcal {I} \}) \leq \alpha_ {i} \quad \text { for } \quad i \in [ \mathcal {I} - 1 ],\tag{1}
$$

where $\alpha _ { i } \in ( 0 , 1 )$ is the desired control level for the i-th under-classification error $R _ { i \star } ( \phi )$ Simultaneously, our H-NP framework minimizes the weighted sum of the remaining errors, which can be expressed as

$$
R ^ {c} (\phi) = \mathbb {P} (\phi (X) \neq Y) - \sum_ {i = 1} ^ {\mathcal {I} - 1} \pi_ {i} R _ {i \star} (\phi), \quad \text { where } \quad \pi_ {i} = \mathbb {P} (Y = i).\tag{2}
$$

We note that when $\mathcal { Z } = 2$ , this H-NP formulation is equivalent to the binary NP classification (prioritizing class 1 over class 2), with $R _ { 1 \star } ( \phi )$ being the population type I error.

For COVID-19 severity classification with three levels, severe patients labeled as $Y = 1$ have the top priority, and we want to control the probability of severe patients not being identified, which is $R _ { 1 \star } ( \phi )$ . The secondary priority is for moderate patients labeled as $Y = 2 ; R _ { 2 \star } ( \phi )$ is the probability of moderate patients being classified as healthy. Healthy patients that do not need medical care are labeled as $Y = 3$ . Note that $R _ { i \star } ( \cdot )$ and $R ^ { c } ( \cdot )$ are population-level quantities as they depend on the intrinsic distribution of (X, Y), and it is hard to control the $R _ { i \star } ( \cdot )$ ’s almost surely due to the randomness of the classifier.

## 2.2 H-NP algorithm with high probability control

In this section, we construct an H-NP umbrella algorithm that controls the population under-classification errors in the sense that $\mathbb { P } ( R _ { i \star } ( \widehat { \phi } ) > \alpha _ { i } ) \leq \delta _ { i }$ for $i \in [ \mathcal { I } - 1 ]$ , where $\left( \delta _ { 1 } , \ldots , \delta _ { \mathbb { Z } - 1 } \right)$ is a vector of tolerance parameters, and $\widehat { \phi }$ is a scoring-type classifier to be defined below.

Roughly speaking, we employ a sample-splitting strategy, which uses some data subsets to train the scoring functions from a base classification method and other data subsets to select appropriate thresholds on the scores to achieve population-level error controls. Here, the scoring functions refer to the scores assigned to each possible class label for a given input observation and include examples such as the output from the softmax transformation in multinomial logistic regression. For $i \in [ \mathcal { T } ]$ , let $\boldsymbol { S _ { i } } = \{ X _ { j } ^ { i } \} _ { j = 1 } ^ { N _ { i } }$ denote $N _ { i }$ independent observations from class i, where $N _ { i }$ is the size of the class. In the following discussion, the superscript on X is dropped for brevity when it is clear which class the observation comes from. Our procedure randomly splits the class-i observations into $\left( \mathrm { u p ~ t o } \right)$ three parts: $\boldsymbol { S _ { i s } }$ $( i \in [ T ] )$ for obtaining scoring functions, $S _ { i t } ~ ( i \in [ \mathcal { T } - 1 ] )$ for selecting thresholds, and $\boldsymbol { S } _ { i e }$ $( i = 2 , \ldots , T )$ for computing empirical errors. As will be made clear later, our procedure does not require $\boldsymbol { S } _ { 1 e }$ or $S _ { \mathcal { T } t }$ and splits class 1 and class I into two parts only. After splitting, we use the combination $\textstyle S _ { s } = \bigcup _ { i \in [ \mathcal { I } ] } S _ { i s }$ to train the scoring functions.

We consider a classifier that relies on $\mathcal { T } - 1$ scoring functions $T _ { 1 } , T _ { 2 } , \dots , T _ { \mathcal { T } - 1 } : \mathcal { X } \to \mathbb { R }$ where the class decision is made sequentially with each $T _ { i } ( X )$ determining whether the observation belongs to class i or one of the less prioritized classes $( i + 1 ) , \dotsc , \mathcal { T }$ . Thus at each step i, the decision is binary, allowing us to use the NP Lemma to motivate the construction of our scoring functions. Note that $\mathbb { P } ( Y = i \mid X = x ) / \mathbb { P } ( Y \in \{ i + 1 , . . . , \mathbb { Z } \}$ | $X = x ) \propto f _ { i } ( x ) / f _ { > i } ( x )$ , where $f _ { > i } ( x )$ and $f _ { i } ( x )$ represent the density function of X when $Y > i$ and $Y = i$ , respectively, and the density ratio is the statistic that leads to the most powerful test with a given level of control on one of the errors by the NP Lemma. Given a typical scoring-type classification method (e.g., logistic regression, random forest, SVM, and neural network) that provides the probability estimates ${ \widehat { \mathbb { P } } } ( Y = i \mid X )$ for $i \in [ \mathcal { T } ]$ , we can construct our scores using these estimates by defining

$$
T _ {1} (X) = \widehat {\mathbb {P}} (Y = 1 \mid X), \quad \text { and } \quad T _ {i} (X) = \frac {\widehat {\mathbb {P}} (Y = i \mid X)}{\sum_ {j = i + 1} ^ {\mathcal {I}} \widehat {\mathbb {P}} (Y = j \mid X)} \quad \text { for } \quad 1 <   i <   \mathcal {I} - 1.
$$

Given thresholds $( t _ { 1 } , t _ { 2 } , \dots , t _ { \mathbb { Z } - 1 } )$ , we consider an H-NP classifier of the form

$$
\widehat {\phi} (X) = \left\{ \begin{array}{l l} 1, & T _ {1} (X) \geq t _ {1}; \\ 2, & T _ {2} (X) \geq t _ {2} \quad \text { and } \quad T _ {1} (X) <   t _ {1}; \\ \dots \\ \mathcal {I} - 1, & T _ {\mathcal {I} - 1} (X) \geq t _ {\mathcal {I} - 1} \quad \text { and } \quad T _ {1} (X) <   t _ {1}, \ldots , T _ {\mathcal {I} - 2} (X) <   t _ {\mathcal {I} - 2}; \\ \mathcal {I}, & \text { otherwise }. \end{array} \right.\tag{3}
$$

Then the i-th under-classification error for this classifier can be written as

$$
R _ {i \star} (\widehat {\phi}) = P _ {i} \left(\widehat {\phi} (X) \in \{i + 1, \ldots , \mathcal {I} \}\right) = P _ {i} \left(T _ {1} (X) <   t _ {1}, \ldots , T _ {i} (X) <   t _ {i}\right),\tag{4}
$$

where X is a new observation from the i-th class independent of the data used for score training and threshold selection. The thresholds $( t _ { 1 } , t _ { 2 } , \dots , t _ { \mathbb { Z } - 1 } )$ are selected using the observations in $S _ { 1 t } , \ldots , S _ { ( \mathcal { T } - 1 ) t }$ , and they are chosen to satisfy $\mathbb { P } ( R _ { i \star } ( \widehat { \phi } ) > \alpha _ { i } ) \leq \delta _ { i }$ for all $i \in [ \mathcal { I } - 1 ]$ . In what follows, we will develop our arguments conditional on the data $S _ { s }$ for training the scoring functions so that $T _ { i } \mathrm { { ' s } }$ can be viewed as fixed functions.

According to Eq (3), the first under-classification error $R _ { 1 \star } ( \widehat { \phi } ) = P _ { 1 } \left( T _ { 1 } ( X ) < t _ { 1 } \right)$ only depends on $t _ { 1 }$ , while the other under-classification errors $R _ { i \star } ( \widehat { \phi } )$ depend on $t _ { 1 } , \ldots , t _ { i }$ . To achieve the high probability controls with $\mathbb { P } ( R _ { i \star } ( \widehat { \phi } ) > \alpha _ { i } ) \leq \delta _ { i }$ for all $i \in [ \mathcal { I } - 1 ]$ , we select $t _ { 1 } , \dots t _ { \tau } .$ <sub>−</sub> sequentially using an order statistics approach. We start with the selection of $t _ { 1 }$ , which is covered by the following general proposition. The proof is a modification of Proposition 1 in Tong et al. [2018] and can be found in Supplementary Section B.1.

Proposition 1. For any $i \in [ \mathcal { T } ]$ , denote $\mathcal { T } _ { i } = \{ T _ { i } ( X ) ~ | ~ X \in \mathcal { S } _ { i t } \}$ , and let $t _ { i ( k ) }$ be the corresponding k-th order statistic. Further denote the cardinality of $\mathcal { T } _ { i }$ as $n _ { i }$ . Assuming that the data used to train the scoring functions and the left-out data are independent, then given a control level $\alpha ,$ for another independent observation X from class $i _ { ; }$ ,

$$
\mathbb {P} \left(P _ {i} \left[ T _ {i} (X) <   t _ {i (k)} \mid t _ {i (k)} \right] > \alpha\right) \leq v (k, n _ {i}, \alpha) := \sum_ {j = 0} ^ {k - 1} {\binom {n _ {i}} {j}} (\alpha) ^ {j} (1 - \alpha) ^ {n _ {i} - j}.\tag{5}
$$

We remark that similar to Proposition 1 in Tong et al. [2018], if $T _ { i }$ is a continuous random variable, the bound in Eq (5) is tight.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1: DeltaSearch(n, α, δ)

Input : size: n; level: α; tolerance: δ.

1 k = 0,  $v_{k} = 0$ 

2 while  $v_{k} \leq \delta$  do

3  $v_{k} = v_{k} + \binom{n}{k}(\alpha)^{k}(1 - \alpha)^{n-k}$ 

4  $k = k + 1$ 

5 end

Output: k
</div>

Let $k _ { i } = \operatorname* { m a x } \{ k \mid v ( k , n _ { i } , \alpha _ { i } ) \leq \delta _ { i } \}$ , which can be computed using Algorithm 1. Then Proposition 1 and Eq (4) imply

$$
\mathbb {P} \left(R _ {i \star} (\widehat {\phi}) > \alpha_ {i}\right) \leq \mathbb {P} \left(P _ {i} \left[ T _ {i} (X) <   t _ {i} \mid t _ {i (k _ {i})} \right] > \alpha_ {i}\right) \leq \delta_ {i} \quad \mathrm{forall} \quad t _ {i} \leq t _ {i (k _ {i})}\tag{6}
$$

We note that to have a solution for $v ( k , n _ { i } , \alpha _ { i } ) ~ \leq ~ \delta _ { i }$ among $k \ \in \ [ n _ { i } ]$ , we need $n _ { i } \geq$ log $\delta _ { i } / \log ( 1 - \alpha _ { i } )$ , the minimum sample size required for the class $S _ { i t }$ . When i = 1, the first inequality in Eq (6) becomes equality, so $t _ { 1 ( k _ { 1 } ) }$ is an efective upper bound on $t _ { 1 }$ when we later minimize the empirical counterpart of $R ^ { c } ( \cdot )$ in Eq (2) with respect to diferent feasible threshold choices. On the other hand, for $i > 1$ , the inequality is mostly strict, which means that the bound $t _ { i ( k _ { i } ) }$ on $t _ { i }$ is expected to be loose and can be improved. To this end, we note that Eq (4) can be decomposed as

$$
R _ {i \star} (\widehat {\phi}) = P _ {i} (T _ {i} (X) <   t _ {i} | T _ {1} (X) <   t _ {1}, \dots , T _ {i - 1} (X) <   t _ {i - 1}) \cdot P _ {i} (T _ {1} (X) <   t _ {1}, \dots , T _ {i - 1} (X) <   t _ {i - 1})\tag{7}
$$

leading to the following theorem that upper bounds $t _ { i }$ given the previous thresholds.

Theorem 1. Given the previous thresholds $t _ { 1 } , \ldots , t _ { i - 1 }$ , consider all the scores $T _ { i }$ on the left-out class $S _ { i t } , \ T _ { i } = \{ T _ { i } ( X ) \ | \ X \in \ S _ { i t } \}$ , and a subset of these scores depending on the previous thresholds, defined as $\mathcal T _ { i } ^ { \prime } = \{ T _ { i } ( X ) ~ | ~ X \in \mathcal S _ { i t } , T _ { 1 } ( X ) < t _ { 1 } , \ldots , T _ { i - 1 } ( X ) < t _ { i - 1 } \}$ We use $t _ { i ( k ) }$ and $t _ { i ( k ) } ^ { \prime }$ to denote the k-th order statistic of $\mathcal { T } _ { i }$ and $\mathcal { T } _ { i } ^ { \prime }$ , respectively. Let $n _ { i }$ and $n _ { i } ^ { \prime }$ be the cardinality of $\mathcal { T } _ { i }$ and $\mathcal { T } _ { i } ^ { \prime }$ , respectively, and $\alpha _ { i }$ and $\delta _ { i }$ be the prespecified control level and violation tolerance for the i-th under-classification error $R _ { i \star } ( \cdot )$ . We set

$$
\hat {p} _ {i} = \frac {n _ {i} ^ {\prime}}{n _ {i}}, p _ {i} = \hat {p} _ {i} + c (n _ {i}), \alpha_ {i} ^ {\prime} = \frac {\alpha_ {i}}{p _ {i}}, \delta_ {i} ^ {\prime} = \delta_ {i} - \exp \{- 2 n _ {i} c ^ {2} (n _ {i}) \},\tag{8}
$$

where $c ( n ) = \mathcal { O } ( 1 / \sqrt { n } )$ . Let

$$
\overline {{t}} _ {i} = \left\{ \begin{array}{l l} t _ {i (k _ {i} ^ {\prime})} ^ {\prime}, & \text { if   } n _ {i} ^ {\prime} \geq \log \delta_ {i} ^ {\prime} / \log (1 - \alpha_ {i} ^ {\prime}) \quad \text { and } \quad \alpha_ {i} ^ {\prime} <   1; \\ t _ {i (k _ {i})}, & \text { otherwise }, \end{array} \right.\tag{9}
$$

where $k _ { i } = \operatorname* { m a x } \{ k \in [ n _ { i } ] \mid v ( k , n _ { i } , \alpha _ { i } ) \leq \delta _ { i } \} \quad a n d \quad k _ { i } ^ { \prime } = \operatorname* { m a x } \{ k \in [ n _ { i } ^ { \prime } ] \mid v ( k , n _ { i } ^ { \prime } , \alpha _ { i } ^ { \prime } ) \leq \delta _ { i } ^ { \prime } \}$ Then,

$$
\mathbb {P} (R _ {i \star} (\widehat {\phi}) > \alpha_ {i}) = \mathbb {P} \left(P _ {i} \left[ T _ {1} (X) <   t _ {1}, \dots T _ {i} (X) <   t _ {i} \mid \bar {t} _ {i} \right] > \alpha_ {i}\right) \leq \delta_ {i} \quad f o r a l l \quad t _ {i} \leq \bar {t} _ {i}\tag{10}
$$

In other words, if the cardinality of $\mathcal { T } _ { i } ^ { \prime }$ exceeds a threshold, we can refine the choice of the upper bound according to Eq (9); otherwise, the bound in Proposition 1 always applies. The proof of the theorem is provided in Supplementary Section B.2; the computation of the upper bound $\bar { t } _ { i }$ is summarized in Algorithm 2. $\bar { t } _ { i }$ guarantees the required high probability control on the i-th under-classification error, while providing a tighter bound compared with Eq (4). We make two additional remarks as follows.

Remark 1. a) The minimum sample size requirement for $\boldsymbol { S } _ { i t }$ is still $n _ { i } \geq \log \delta _ { i } / \log ( 1 -$ $\alpha _ { i } )$ because $t _ { i ( k _ { i } ) }$ in Eq (9) always exists when this inequality holds. For instance, $i f$ $\alpha _ { i } = 0 . 0 5$ and $\delta _ { i } = 0 . 0 5$ , then $n _ { i } \geq 5 9$

b) The choice $o f c ( n )$ involves a trade-of between $\alpha _ { i } ^ { \prime }$ and $\delta _ { i } ^ { \prime } ,$ although under the constraint $c ( n ) = \mathcal { O } ( 1 / \sqrt { n } )$ , any changes in both quantities are small in magnitude for large n. For example, a larger c(n) leads to a smaller α<sup>′</sup> and a larger $\delta _ { i } ^ { \prime }$ , thus a looser tolerance level comes at the cost of a stricter error control level. In practice, larger α<sup>′</sup> and larger $\delta _ { i } ^ { \prime }$ values are desired since they lead to a wider region for $t _ { i }$ . We set $c ( n ) = 2 / { \sqrt { n } }$ throughout the rest of the paper. Then by Eq (8), $\alpha _ { i } ^ { \prime }$ increases as n increases, and $\delta _ { i } ^ { \prime } = \delta _ { i } - e ^ { - 4 }$ , so the diference between $\delta _ { i } ^ { \prime }$ and the prespecified $\delta _ { i }$ is suficiently small.

c) Eq (10) has two cases, as Eq (9) indicates. When $\bar { t } _ { i } = t _ { i ( k _ { i } ) }$ , the bound remains the same as Eq (6), which is not tight for $i > 1$ . When $\bar { t } _ { i } = t _ { i ( k _ { i } ^ { \prime } ) } ^ { \prime }$ , Eq (10) provides a tighter bound through the decomposition in Eq (7), where the first part is bounded by a concentration argument, and the second part achieves a tight bound the same way as Proposition 1.

With the set of upper bounds on the thresholds chosen according to Theorem 1, the next step is to find an optimal set of thresholds $( t _ { 1 } , t _ { 2 } , \dots , t _ { \mathbb { Z } - 1 } )$ satisfying these upper bounds while minimizing the empirical version of $R ^ { c } ( \widehat { \phi } )$ , which is calculated using observations in $\textstyle S _ { e } = \bigcup _ { i = 2 } ^ { \mathcal { I } } S _ { i e }$ (since class-1 observations are not needed in $R ^ { c } ( \widehat { \phi } ) )$ . For brevity, we denote all the empirical errors as $\tilde { R } , \mathrm { e . g . } , \tilde { R } ^ { c }$ . In Section 2.4, we will show numerically that

Theorem 1 provides a wider search region for the threshold $t _ { i }$ compared to Proposition 1, which benefits the minimization of $R ^ { c }$

As our COVID-19 data has three severity levels, in the next section, we will focus on the three-class H-NP umbrella algorithm and describe in more details how the above procedures can be combined to select the optimal thresholds in the final classifier.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2: UpperBound($S_{it}, \alpha_i, \delta_i, (T_1, \ldots, T_i), (t_1, \ldots, t_{i-1})$)
Input : The left-out class-$i$ samples: $S_{it}$; level: $\alpha_i$; tolerance: $\delta_i$; score functions: $(T_1, \ldots, T_i)$; thresholds: $(t_1, \ldots, t_{i-1})$.
1 $n_i \leftarrow |S_{it}|$
2 $\{t_{i(1)}, \ldots, t_{i(n_i)}\} \leftarrow \text{sort } T_i = \{T_i(X) \mid X \in S_{it}\}$
3 $k_i \leftarrow \text{DeltaSearch}(n_i, \alpha_i, \delta_i)$ // i.e., Algorithm 1
4 $\bar{t}_i \leftarrow t_{i(k_i)}$
5 if $i &gt; 1$ then
6    $T_i' \leftarrow \{t_{i(1)}', \ldots, t_{i(n_i')}'\} = \text{sort}\{T_i(X) \mid X \in S_{it}, T_1(X) &lt; t_1, \ldots, T_{i-1}(X) &lt; t_{i-1}\}$ // Note that $n_i'$ is random
7    $\hat{p}_i \leftarrow \frac{n_i'}{n_i}$, $p_i \leftarrow \hat{p}_i + c(n_i)$, $\alpha_i' \leftarrow \alpha_i / p_i$, $\delta_i' \leftarrow \delta_i - e^{-2n_ic^2(n_i)}$; // e.g., $c(n) = \frac{2}{\sqrt{n}}$
8    if $n_i' \geq \log \delta_i' / \log(1 - \alpha_i')$ and $\alpha_i' &lt; 1$ then
9    $k_i' \leftarrow \text{DeltaSearch}(n_i', \alpha_i', \delta_i')$
10    $\bar{t}_i \leftarrow t_{i(k_i')}'$
11    end
12 end
Output: $\bar{t}_i$
</div>

## 2.3 H-NP umbrella algorithm for three classes

Since our COVID-19 data groups patients into three severity categories, we introduce our H-NP umbrella algorithm for $\mathcal { T } = 3$ . In this case, there are two under-classification errors $R _ { 1 \star } ( \phi ) = P _ { 1 } ( \phi ( X ) \in \{ 2 , 3 \} )$ ) and $R _ { 2 \star } ( \phi ) = P _ { 2 } ( \phi ( X ) = 3 )$ , which need to be controlled at prespecified levels $\alpha _ { 1 } , \alpha _ { 2 }$ with tolerance levels $\delta _ { 1 } , \delta _ { 2 }$ , respectively. In addition, we wish to minimize the weighted sum of errors

$$
\begin{array}{r l} R ^ {c} (\phi) & = \mathbb {P} (\phi (X) \neq Y) - \pi_ {1} R _ {1 \star} (\phi) - \pi_ {2} R _ {2 \star} (\phi) \\ & = \pi_ {2} P _ {2} (\phi (X) = 1) + \pi_ {3} [ P _ {3} (\phi (X) = 1) + P _ {3} (\phi (X) = 2) ]. \end{array}\tag{11}
$$

When $\mathcal { T } = 3$ , our H-NP umbrella algorithm relies on two scoring functions $T _ { 1 } , T _ { 2 } : \mathcal { X }  \mathbb { R }$ 2 which can be constructed by Eq (3) using the estimates ${ \widehat { \mathbb { P } } } ( Y = i \mid X )$ from any scoring-type classification method:

$$
T _ {1} (X) = \widehat {\mathbb {P}} (Y = 1 \mid X) \quad \text { and } \quad T _ {2} (X) = \frac {\widehat {\mathbb {P}} (Y = 2 \mid X)}{\widehat {\mathbb {P}} (Y = 3 \mid X)}.\tag{12}
$$

The H-NP classifier then takes the form

$$
\widehat {\phi} (X) = \left\{ \begin{array}{l l} 1, & T _ {1} (X) \geq t _ {1}; \\ 2, & T _ {2} (X) \geq t _ {2} \quad \text { and } \quad T _ {1} (X) <   t _ {1}; \\ 3, & \text { otherwise }. \end{array} \right.\tag{13}
$$

Here $T _ { 2 }$ determines whether an observation belongs to class 2 or class 3, with a larger value indicating a higher probability for class 2. Applying Algorithm 2, we can find $\overline { { t } } _ { 1 }$ such that any threshold $t _ { 1 } \leq \bar { t } _ { 1 }$ will satisfy the high probability control on the first underclassification error, that is $\mathbb { P } ( R _ { 1 \star } ( \widehat { \phi } ) > \alpha _ { 1 } ) = \mathbb { P } \left( P _ { 1 } \left[ T _ { 1 } ( X ) < t _ { 1 } | \bar { t } _ { 1 } \right] > \alpha _ { 1 } \right) \le \delta _ { 1 }$ . Recall that the computation of $\overline { { t } } _ { 2 }$ (and consequently $t _ { 2 } )$ depends on the choice of $t _ { 1 }$ . Given a fixed $t _ { 1 }$ , the high probability control on the second under-classification errors is $\mathbb { P } ( R _ { 2 \star } ( \widehat { \phi } ) >$ $\alpha _ { 2 } ) = \mathbb { P } \left( P _ { 2 } \left[ T _ { 1 } ( X ) < t _ { 1 } , T _ { 2 } ( X ) < t _ { 2 } \ | \ \bar { t } _ { 2 } \right] > \alpha _ { 2 } \right) \le \delta _ { 2 }$ , where $\overline { { t } } _ { 2 }$ is computed by Algorithm 2 so that any $t _ { 2 } \leq \bar { t } _ { 2 }$ satisfies the constraint.

![](images/b51f946489e3850730bccfb4f0511f55fe4395dc116fd4928a63a60976bafa48.jpg)

![](images/d36d86c02bb63ace1b8651d0419a4e8b352d939ad0078c058ecd9ebd0c482863.jpg)  
(a) The construction of $\mathcal { T } _ { 2 } ^ { \prime }$ with a fixed $t _ { 1 }$ .  
(b) The efect of decreasing $t _ { 1 }$  
Figure 1: The influence of $t _ { 1 }$ on the error $P _ { 3 } \left( { \widehat { Y } } = 2 \right)$

The interaction between $t _ { 1 }$ and $t _ { 2 }$ comes into play when minimizing the remaining errors in $R ^ { c } ( \widehat { \phi } )$ . First note that using Eq (11) and (13), the other types of errors in $R ^ { c } ( \widehat { \phi } )$ are

$$
\begin{array}{l} P _ {2} \left(\widehat {\phi} (X) = 1\right) = P _ {2} \left(T _ {1} (X) \geq t _ {1}\right), P _ {3} \left(\widehat {\phi} (X) = 1\right) = P _ {3} \left(T _ {1} (X) \geq t _ {1}\right), \\ P _ {3} \left(\widehat {\phi} (X) = 2\right) = P _ {3} \left(T _ {1} (X) <   t _ {1}, T _ {2} (X) \geq t _ {2}\right). \end{array}\tag{14}
$$

To simplify the notation, let $\widehat { Y }$ denote ${ \widehat { \phi } } ( X )$ in the following discussion. For a fixed $t _ { 1 }$ , decreasing $t _ { 2 }$ leads to an increase in $P _ { 3 } ( \widehat { Y } = 2 )$ and has no efect on the other errors in (14), which means that $t _ { 2 } = \bar { t } _ { 2 }$ minimizes $R ^ { c } ( \widehat { \phi } )$ . However, the selection of $t _ { 1 }$ is not as straightforward as $t _ { 2 }$ . Figure 1a illustrates how the set $\begin{array} { r } { \mathcal { T } _ { 2 } ^ { \prime } = \{ T _ { 2 } ( X ) ~ | ~ X \in \mathcal { S } _ { 2 t } , T _ { 1 } ( X ) < t _ { 1 } \} } \end{array}$ (as appeared in Theorem 1) is constructed for a given $t _ { 1 }$ , where the elements are ordered by their $T _ { 2 }$ values. Clearly, more elements are removed from $\mathcal { T } _ { 2 } ^ { \prime }$ as $t _ { 1 }$ decreases, leading to a smaller $n _ { 2 } ^ { \prime }$ . Consider an element in the set $\mathcal { T } _ { 2 } ^ { \prime }$ which has rank k in the ordered list (colored yellow in Figure 1a). Then $k , n _ { 2 } ^ { \prime } , \alpha _ { 2 } ^ { \prime }$ , and consequently $v ( k , n _ { 2 } ^ { \prime } , \alpha _ { 2 } ^ { \prime } )$ , will all be afected by decreasing $t _ { 1 }$ , but the change is not monotonic as shown in Figure 1b. Decreasing $t _ { 1 }$ could remove elements (dashed circles in Figure 1b) either to the left side (case 1) or right side (case 2) of the yellow element, depending on the values of the scores $T _ { 1 }$ . In case 1, $v ( k , n _ { 2 } ^ { \prime } , \alpha _ { 2 } ^ { \prime } )$ decreases, resulting in a larger $\overline { { t } } _ { 2 }$ and a smaller $P _ { 3 } ( \widehat { Y } = 2 )$ error, whereas the reverse can happen in case 2. The details of how $v ( k , n _ { 2 } ^ { \prime } , \alpha _ { 2 } ^ { \prime } )$ changes can be found in Supplementary Section B.3, with additional simulations in Supplementary Figure S13. In view of the above, minimizing the empirical error $\tilde { R } ^ { c }$ requires a grid search over $t _ { 1 }$ , for which we use the set $\mathcal { T } _ { 1 } = \{ T _ { 1 } ( X ) ~ | ~ X \in \mathcal { S } _ { 1 t } \}$ , and the overall algorithm for finding the optimal thresholds and the resulting classifier is described in Algorithm 3, which we name as the H-NP umbrella algorithm. The algorithm for the general case with $\mathcal { T } > 3$ can be found in Supplementary Section E.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3: H-NP umbrella algorithm for $\mathcal{I}=3$

Input : Sample: $\mathcal{S}=\mathcal{S}_{1}\cup\mathcal{S}_{2}\cup\mathcal{S}_{3}$; levels: $(\alpha_{1},\alpha_{2})$; tolerances: $(\delta_{1},\delta_{2})$; grid set: $A_{1}$ (e.g., $\mathcal{T}_{1}$).

1 $\widehat{\pi}_{2}=|\mathcal{S}_{2}|/|\mathcal{S}|$; $\widehat{\pi}_{3}=|\mathcal{S}_{3}|/|\mathcal{S}|$

2 $\mathcal{S}_{1s},\mathcal{S}_{1t},\leftarrow$ Random split $\mathcal{S}_{1}$; $\mathcal{S}_{2s},\mathcal{S}_{2t},\mathcal{S}_{2e}\leftarrow$ Random split $\mathcal{S}_{2}$; $\mathcal{S}_{3s},\mathcal{S}_{3e}\leftarrow$ Random split $\mathcal{S}_{3}$

3 $\mathcal{S}_{s}=\mathcal{S}_{1s}\cup\mathcal{S}_{2s}\cup\mathcal{S}_{3s}$

4 $T_{1},T_{2}\leftarrow$ A base classification method($\mathcal{S}_{s}$); // c.f. Eq (12)

5 $\bar{t}_{1}\leftarrow$ UpperBound($\mathcal{S}_{1t},\alpha_{1},\delta_{1},(T_{1}),NULL$); // i.e., Algorithm 2

6 $\tilde{R}^{c}=1$

7 for $t_{1}\in A_{1}\cap(-\infty,\bar{t}_{1}]$ do

8 $t_{2}\leftarrow$ UpperBound($\mathcal{S}_{2t},\alpha_{2},\delta_{2},(T_{1},T_{2}),(t_{1})$)

9 $\widehat{\phi}\leftarrow$ a classifier with respect to $t_{1},t_{2}$

10 $e_{21}=\sum_{X\in\mathcal{S}_{2e}}\mathbb{I}\{\widehat{\phi}(X)=1\}/|\mathcal{S}_{2e}|, e_{3}=\sum_{X\in\mathcal{S}_{3e}}\mathbb{I}\{\widehat{\phi}(X)\in\{1,2\}\}\}/|\mathcal{S}_{3e}|$

11 $\tilde{R}^{c}_{new}=\widehat{\pi}_{2}e_{21}+\widehat{\pi}_{3}e_{3}$

12 if $\tilde{R}^{c}_{new}&lt;\tilde{R}^{c}$ then

13 $|\tilde{R}^{c}\leftarrow\tilde{R}^{c}_{new},\widehat{\phi}^{*}\leftarrow\widehat{\phi}$

14 end

15 end

Output: $\widehat{\phi}^{*}$
</div>

## 2.4 Simulation studies

We first examine the validity of our H-NP umbrella algorithm using simulated data from a setting denoted T1.1, where $\mathcal { T } = 3$ , and the feature vectors in class i are generated as $\left( X ^ { i } \right) ^ { \top } \sim \ N ( \mu _ { i } , I )$ , where $\mu _ { 1 } = ( 0 , - 1 ) ^ { \top } , \mu _ { 2 } = ( - 1 , 1 ) ^ { \top } , \mu _ { 3 } = ( 1 , 0 ) ^ { \top }$ and I is the $2 \times 2$ identity matrix. For each simulated dataset, we generate the feature vectors and labels with 500 observations in each of the three classes. The observations are randomly separated into parts for score training, threshold selection and computing empirical errors: $S _ { 1 }$ is split into 50%, 50% for $\begin{array} { r } { S _ { 1 s } , \ S _ { 1 t } ; \ S _ { 2 } } \end{array}$ is split into 45%, 50% and 5% for $S _ { 2 s } , \ S _ { 2 t }$ and $S _ { 2 e } ; S _ { 3 }$ is split into 95%, 5% for $S _ { 3 s } , \ : S _ { 3 e }$ , respectively. All the results in this section are based on 1,000 repetitions from a given setting. We set $\alpha _ { 1 } = \alpha _ { 2 } = 0 . 0 5$ and $\delta _ { 1 } = \delta _ { 2 } = 0 . 0 5$ To approximate and evaluate the true population errors $R _ { 1 \star } , R _ { 2 }$ <sub>⋆</sub> and $R ^ { c }$ , we additionally generate 20,000 observations for each class and refer to them as the test set.

First, we demonstrate that Algorithm 3 outputs an H-NP classifier with the desired high probability controls. More specifically, we show that any $t _ { 1 } \leq \bar { t } _ { 1 }$ and $t _ { 2 } = \overline { { t } } _ { 2 } \left( \overline { { t } } _ { 1 } , \overline { { t } } _ { 2 } \right.$ are computed by Algorithm 2) will lead to a valid threshold pair $( t _ { 1 } , t _ { 2 } )$ satisfying $\mathbb { P } ( R _ { 1 \star } ( \widehat { \phi } ) >$ $\alpha _ { 1 } ) \leq \delta _ { 1 }$ and $\begin{array} { r } { \mathbb { P } ( R _ { 2 \star } ( \widehat { \phi } ) > \alpha _ { 2 } ) \leq \delta _ { 2 } } \end{array}$ , where $R _ { 1 \star }$ and $R _ { 2 \star }$ are approximated using the test set in each round of simulation. Here, we use multinomial logistic regression to construct the scoring functions $T _ { 1 }$ and $T _ { 2 }$ , the inputs of Algorithm 3. Figure 2 displays the boxplots of various approximate errors with $t _ { 1 }$ chosen as the k-th largest element in $\mathcal { T } _ { 1 } \cap \left( - \infty , \bar { t } _ { 1 } \right]$ as k changes. In Figure 2a and 2b, where the blue diamonds mark the 95% quantiles, we can see that the violation rate of the required error bounds (red dashed lines, representing $\alpha _ { 1 }$ and $\alpha _ { 2 } )$ is about 5% or less, suggesting our procedure provides efective controls on the errors of concerns. In this case, in most simulation rounds, $\overline { { t } } _ { 1 }$ minimizes the empirical error $\tilde { R } ^ { c }$ computed on $S _ { 2 e }$ and $\displaystyle { \cal S } _ { 3 e } .$ , and $t _ { 1 } = \bar { t } _ { 1 }$ is chosen as the optimal threshold by Algorithm 3 in the final classifier. We can see this coincide with Figure 2c, which shows that the largest element in $\mathcal { T } _ { 1 } \cap ( - \infty , \overline { { t } } _ { 1 } ] \ ( \mathrm { i . e . , } \ \overline { { t } } _ { 1 } )$ minimizes the approximate error $R ^ { c }$ on the test set. We note here that the results from other splitting ratios can be found in Supplementary Section C.2, where we observe that once the sample size for threshold selection reaches about twice the minimum sample size requirement, there are little observable diferences in the results. In Supplementary Section C.3, we also compare with variations in computing the scoring functions to examine the efect of score normalization and calibration, showing that our current scoring functions are ideal for our purpose.

Next, we check whether indeed Theorem 1 gives a better upper bound on $t _ { 2 }$ than Proposition 1 for overall error minimization. Recall the two upper bounds in Eq (6) $\left( t _ { 2 \left( k _ { 2 } \right) } \right)$ and Eq (9) (t<sub>2</sub>). For each base classification algorithm $( \mathrm { e . g . }$ , logistic regression), we set $t _ { 1 } = \bar { t } _ { 1 }$ and $t _ { 2 }$ equal to these two upper bounds respectively, resulting in two classifiers with diferent $t _ { 2 }$ thresholds. We compare their performance by evaluating the approximate errors of $R _ { 2 \star } ( \widehat \phi )$ and $P _ { 3 } ( \hat { Y } = 2 )$ since, as discussed in Section 2.3, the threshold $t _ { 2 }$ only influences these two errors for a fixed $t _ { 1 }$ . Figure 3 shows the distributions of the errors and also their averages for three diferent base classification algorithms. Under each algorithm, both choices of $t _ { 2 }$ efectively control $R _ { 2 \star } ( \widehat { \phi } )$ , but the upper bound from Proposition 1 is overly conservative compared with that of Theorem 1, which results in a notable increase in $P _ { 3 } ( \hat { Y } = 2 )$ . This is undesirable since $P _ { 3 } ( \hat { Y } = 2 )$ is one component in $R ^ { c } ( \widehat { \phi } )$ , and the goal is to minimize $R ^ { c } ( \widehat { \phi } )$ under appropriate error controls.

![](images/514c6f0e4385af8a20ddd878f9bfe2d7a3a680fd577b0fcc440b5d6d4965dfc2.jpg)  
(a) $R _ { 1 }$ ⋆

![](images/92af492979706068d1b86ed1d47f4660d3ab811ec1ec6a3b075cf1bb3c4d4a5d.jpg)  
(b) $R _ { 2 \star }$

![](images/a2db785207cbeeeab052779601cce7acc4d163ea5295c580612d6cb87ef8099e.jpg)  
(c) $R ^ { c }$  
Figure 2: The distribution of approximate errors on the test set when $t _ { 1 }$ is the k-th largest element in $\mathcal { T } _ { 1 } \cap \left( - \infty , \bar { t } _ { 1 } \right)$ . The 95% quantiles of $R _ { 1 } .$ and $R _ { 2 \star }$ are marked by blue diamonds. The target control levels for $R _ { 1 \star } ( { \widehat { \phi } } )$ and $R _ { 2 \star } ( \widehat \phi )$ $( \alpha _ { 1 } = \alpha _ { 2 } = 0 . 0 5 )$ are plotted as red dashed lines.

Now we consider comparing our H-NP classifier against alternative approaches. We construct an example of “approximate” error control using the empirical ROC curve approach. In this case, each class of observations is split into two parts: one for training the base classification method, the other for threshold selection using the ROC curve. Under the setting T1.1, using similar splitting ratios as before, we separate $S _ { i }$ into 50% and 50% for $\boldsymbol { S _ { i s } }$ and $\boldsymbol { S } _ { i t }$ for i = 1, 2, 3. The same test set is used. We re-compute the scoring functions $( T _ { 1 }$ and $T _ { 2 } )$ corresponding to the new split. $t _ { 1 }$ is selected using the ROC curve generated by $T _ { 1 }$ aiming to distinguish between class 1 (samples in ${ \cal { S } } _ { 1 t } )$ and class $2 ^ { \prime }$ (samples in $\boldsymbol { S } _ { 2 t } \cup \boldsymbol { S } _ { 3 t } )$ merging classes 2 and 3, with specificity calculated as the rate of misclassifying a class-1 observation into class $2 ^ { \prime }$ . Similarly, $t _ { 2 }$ is selected using $T _ { 2 }$ dividing samples in ${ \cal S } _ { 2 t } \cup { \cal S } _ { 3 t }$ into class 2 and class 3, with specificity defined as the rate of misclassifying a class-2 observation into class 3. More specifically, in Eq (13) we use $\begin{array} { r } { t _ { 1 } = \operatorname* { s u p } \left\{ t : \frac { \sum _ { X \in { \mathcal { S } } _ { 1 t } } \mathbf { 1 } \{ T _ { 1 } ( X ) < t \} } { | { \mathcal { S } } _ { 1 t } | } \leq \alpha _ { 1 } \right\} } \end{array}$ and $\begin{array} { r } { t _ { 2 } = \operatorname* { s u p } \left\{ t : \frac { \sum _ { X \in { \mathcal { S } _ { 2 t } } } \mathbf { 1 } \{ T _ { 2 } ( X ) < t \} } { | { \mathcal { S } _ { 2 t } } | } \leq \alpha _ { 2 } \right\} } \end{array}$ to obtain the classifier for the ROC curve approach.

![](images/bb18875ddc341bcc43a9a1ac2e4308238ed93418a3c10d931a9692a229fe6d30.jpg)

<table><tr><td colspan="3">Logistic Regression</td></tr><tr><td>Method</td><td>Error23</td><td>Error32</td></tr><tr><td>Prop 1</td><td>0.006</td><td>0.082</td></tr><tr><td>Thm 1</td><td>0.020</td><td>0.046</td></tr><tr><td colspan="3">Random Forest</td></tr><tr><td>Method</td><td>Error23</td><td>Error32</td></tr><tr><td>Prop 1</td><td>0.004</td><td>0.077</td></tr><tr><td>Thm 1</td><td>0.017</td><td>0.033</td></tr><tr><td colspan="3">SVM</td></tr><tr><td>Method</td><td>Error23</td><td>Error32</td></tr><tr><td>Prop 1</td><td>0.006</td><td>0.083</td></tr><tr><td>Thm 1</td><td>0.020</td><td>0.047</td></tr></table>

Figure 3: The distribution and averages of approximate errors on the test set under the setting T1.1. “error23” and “error32” correspond to $R _ { 2 \star } ( \widehat \phi )$ and $P _ { 3 } ( \hat { Y } = 2 )$ , respectively.

The comparison between our H-NP classifier and the ROC curve approach is summarized in Figure 4. Recalling $\alpha _ { i }$ and $\delta _ { i }$ are both 0.05, we mark the 95% quantiles of the under-classification errors by solid black lines and the target error control levels by dotted red lines. First we observe that the 95% quantiles of $R _ { 1 } .$ <sub>⋆</sub> using the ROC curve approach well exceed the target level control, with their averages centering around the target. We also see the influence of $t _ { 1 }$ on the $R _ { 2 \star }$ – without suitably adjusting $t _ { 2 }$ based on $t _ { 1 }$ , the control on $R _ { 2 \star } ( \widehat { \phi } )$ in the ROC curve approach is overly conservative despite it being an approximate error control method, which in turn leads to inflation in error $P _ { 3 } ( \hat { Y } = 2 )$ In view of this, we further consider a simulation setting where the influence of $t _ { 1 }$ on $t _ { 2 }$ is smaller. The setting T2.1 moves samples in class 1 further away from classes 2 and 3 by having $\mu _ { 1 } = ( 0 , - 3 ) ^ { \top }$ , while the other parts remain the same as in the setting T1.1. $\alpha _ { i } , \delta _ { i }$ are still 0.05. As shown in Figure 5, the ROC curve approach does not provide the required level of control for $R _ { 1 } .$ <sub>⋆</sub> or $R _ { 2 } ,$ <sub>⋆</sub>.

![](images/2587d4babdcfbbaabaa7bb60535d479cbf785690495a81d29a5307b8980efb86.jpg)

<table><tr><td colspan="4">Logistic Regression</td></tr><tr><td>Method</td><td>Error1 (95% quantile)</td><td>Error23</td><td>Error32 (mean)</td></tr><tr><td>ROC</td><td>0.074</td><td>0.023</td><td>0.096</td></tr><tr><td>H-NP</td><td>0.045</td><td>0.036</td><td>0.047</td></tr><tr><td colspan="4">Random Forest</td></tr><tr><td>Method</td><td>Error1 (95% quantile)</td><td>Error23</td><td>Error32 (mean)</td></tr><tr><td>ROC</td><td>0.077</td><td>0.020</td><td>0.093</td></tr><tr><td>H-NP</td><td>0.047</td><td>0.034</td><td>0.032</td></tr><tr><td colspan="4">SVM</td></tr><tr><td>Method</td><td>Error1 (95% quantile)</td><td>Error23</td><td>Error32 (mean)</td></tr><tr><td>ROC</td><td>0.078</td><td>0.023</td><td>0.098</td></tr><tr><td>H-NP</td><td>0.048</td><td>0.037</td><td>0.047</td></tr></table>

Figure 4: The distributions of approximate errors on the test set under setting T1.1. “error1”, “error23” and “error32” correspond to $R _ { 1 \star } ( \widehat \phi ) , R _ { 2 \star } ( \widehat \phi )$ and $P _ { 3 } ( \hat { Y } = 2 )$ , respectively.

In Supplementary Sections C.4-C.6, we include more comparisons with alternative methods with diferent overall approaches to the problem, including weight-adjusted classifica-rs tion, cost-sensitive learning, and ordinal regression, and show that our H-NP framework is more ideal for our problem of interest.

![](images/cb7146eb5b47b6096f9946ac391276f42a7af08dac31ebc6769e035ca24af0ff.jpg)

![](images/711f697c92dec86d4a147bbbc839d7ce3810a4c8c2d2a12f740a11d54c298110.jpg)

![](images/9c024a02f39648dec63da0df616ff146775fa057de3010a59486bc9356a6c879.jpg)  
Figure 5: The distributions of approximate errors on the test set under setting T2.1. “error1” and “error23” correspond to the errors $R _ { 1 \star } ( \widehat { \phi } )$ and $R _ { 2 \star } ( \widehat \phi )$ , respectively.

## 3 Application to COVID-19 severity classification

## 3.1 ScRNA-seq data and featurization

We integrate 20 publicly available scRNA-seq datasets to form a total of 864 COVID-19 pa tients with three severity levels marked as “Severe/Critical” (318 patients), “Mild/Moderate” (353 patients), and “Healthy” (193 patients). The detail of each dataset and patient composition can be found in Supplementary Table S1. The severe, moderate and healthy patients are labeled as class 1, 2 and 3, respectively.

For each patient, PBMC scRNA-seq data is available in the form of a matrix recording the expression levels of genes in hundreds to thousands of cells. Following the workflow in Lin et al. [2022a], we first perform data integration including cell type annotation and batch efect removal, before selecting 3,000 highly variable genes and constructing their pseudo-bulk expression profiles under each cell type, where each gene’s expression is averaged across the cells of this type in every patient. The resulting processed data for each patient j is a matrix $A ^ { ( j ) } \in \mathbb { R } ^ { n _ { g } \times n _ { c } }$ , where $n _ { c } = 1 8$ is the number of cell types, and $n _ { g } = 3 , 0 0 0$ is the number of genes for analysis. More details of the integration process can be found in Supplementary Section A. Supplementary Figure S1 shows the distribution of the sparsity levels, i.e., the proportion of genes with zero values, under each cell type across all the patients. Several cell types, despite having a significant proportion of zeros, have varying sparsity across the three severity classes (Supplementary Figure S3), suggesting their activity level might be informative for classification. Since age information is avail able (although in diferent forms, see Supplementary Table S4) in most of the datasets we integrate, we include it as an additional clinical variable for classification. The details of processing the age variable are deferred to Supplementary Section A.

Since classical classification methods typically use feature vectors as input, appropriate featurization that transforms the expression matrices into vectors is needed. We propose four ways of featurization that difer in their considerations of the following aspects.

• As we observe the sparsity level in some cell types changes across the severity classes, we expect diferent treatments of zeros will influence the classification performance. Three approaches are proposed: 1) no special treatment (M.1); 2) remove individual zeros but keeping all cell types (M.4); 3) remove cell types with significant amount of zeros across all three classes (M.2 and M.3).

• Dimension reduction is commonly used to project the information in a matrix onto a vector. We consider performing dimension reduction along diferent directions, namely row projections, which take combinations of genes (M.2), and column projections, which combine cell types with appropriate weights (M.3 and M.4). We aim to compare choices of projection direction, so we focus on principal component analysis (PCA) as our dimension reduction method.

• We consider two approaches to generate the PCA loadings: 1) overall PCA loadings (M.2 and M.4), where we perform PCA on the whole data to output a loading vector for all patients; 2) patient-specific PCA loadings (M.3), where PCA is performed for each matrix $A ^ { ( j ) }$ to get an individual-specific loading vector.

The details of each featurization method are as follows.

M.1 Simple feature screening: we consider each element $A _ { u v } ^ { ( j ) }$ (gene u under cell type v) as a possible feature for patient j and use its standard deviation across all patients, denoted as $S D _ { u v } .$ , to screen the features. Elements that hardly vary across the patients are likely to have a low discriminative power for classification. Let $S D _ { ( i ) }$ be the i-th largest element in $\{ S D _ { u v } \ | \ u \in [ n _ { g } ] , v \in [ n _ { c } ] \}$ . The feature vector for each patient consists of the entries in $\{ A _ { u v } ^ { ( j ) } \mid S D _ { u v } \geq S D _ { ( n _ { f } ) } \}$ , where $n _ { f }$ is the number of features desired and set to 3,000.

M.2 Overall gene combination: removing cell types with mostly zero expression values across all patients (details in Supplementary Section $\mathrm { A } )$ , we select 17 cell types to construct $\tilde { A } ^ { ( j ) } \in \mathbb { R } ^ { n _ { g } \times 1 7 }$ that only preserves columns in $A ^ { ( j ) }$ corresponding to the selected cell types. Then, $\tilde { A } ^ { ( 1 ) } , \ldots , \tilde { A } ^ { ( N ) }$ are concatenated column-wise to get $\tilde { A } ^ { \mathrm { a l l } } \in$ $\mathbb { R } ^ { n _ { g } \times ( N \times 1 7 ) }$ , where $N = 8 6 4$ . Let $\tilde { w } \in \mathbb { R } ^ { n _ { g } \times 1 }$ denote the first principle component loadings of $( \tilde { A } ^ { \mathrm { a l l } } ) ^ { \top }$ , and the feature vector for patient $j$ is given by $X _ { j } = \tilde { w } ^ { \top } \tilde { A } ^ { ( j ) }$

M.3 Individual-specific cell type combination: for patient $j ,$ the loading vector $\tilde { w } _ { j } \in$ $\mathbb { R } ^ { 1 \times 1 7 }$ is taken as the absolute values of first principle component loadings for $\tilde { A } ^ { ( j ) }$ the matrix with selected 17 cell types in M.2 (details in Supplementary Section A). The principle component loading vector $\tilde { w } _ { j }$ that produces $X _ { j } = ( \tilde { A } ^ { ( j ) } \tilde { w } _ { j } ) ^ { \top }$ is patientspecific, intending to reflect diferent cell type compositions in diferent individuals.

M.4 Common cell type combination: we compute an expression matrix $\overline { { A } }$ averaged over all patients defined as (i)

$$
\overline {{A}} _ {u v} = \frac {\sum_ {j \in [ N ]} A _ {u v} ^ {(j)}}{| \{j \in [ N ] | A _ {u v} ^ {(j)} \neq 0 \} |},
$$

where $| \cdot |$ is the cardinality function. Let $w \in \mathbb { R } ^ { n _ { c } \times 1 }$ denote the first principle component loadings of ${ \overline { { A } } } ,$ then the feature vector for the j-th patient is $X _ { j } = ( A ^ { ( j ) } w ) ^ { \top }$

We next evaluate the performance of these featurizations when applied as input to diferent base classification methods for H-NP classification.

## 3.2 Results of H-NP classification

After obtaining the feature vectors and applying a suitable base classification method, we apply Algorithm 3 to control the under-classification errors. Recall that Y = 1, 2, 3 represent the severe, moderate and healthy categories, respectively, and the goal is to control $R _ { 1 \star } ( \widehat { \phi } )$ and $R _ { 2 \star } ( \widehat { \phi } )$ . In this section, we evaluate the performance of the H-NP classifier applied to each combination of featurization method in Section 3.1 and base classification method (logistic regression, random forest, SVM (linear)), which is used to train the scores $( T _ { 1 }$ and $T _ { 2 } )$ . In each class, we leave out 30% of the data as the test set and split the rest 70% as follows for training the H-NP classifier: 35% and 35% of $S _ { 1 }$ form $\boldsymbol { S _ { 1 s } }$ and $S _ { 1 t } \mathbf { \Omega } _ { : }$ ; 35%, 25% and 10% of $S _ { 2 }$ form $S _ { 2 s } , S _ { 2 t }$ and $\boldsymbol { S } _ { 1 e } \boldsymbol { : }$ 35% and 35% of $S _ { 3 }$ form $\displaystyle { S _ { 3 s } }$ and $S _ { 3 \epsilon }$ . For each combination of featurization and base classification method, we perform random splitting of the observations for 50 times to produce the results in this section.

In Figure 6, the yellow halves of the violin plots show the distributions of diferent approximate errors from the classical classification methods; Supplementary Table S7 records the averages of these errors. In all the cases, the average of the approximate $R _ { 1 \star }$ error is greater than 20%, in many cases greater than 40%. On the other hand, the approximate $R _ { 2 \star }$ error under the classical paradigm is already relatively low, with the averages around 10%. Under the H-NP paradigm, we set $\alpha _ { 1 } , \alpha _ { 2 } = 0 . 2$ and $\delta _ { 1 } , \delta _ { 2 } = 0 . 2$ , i.e., we want to control each under-classification error under 20% at a 20% tolerance level.

With the prespecified $\alpha _ { 1 } , \alpha _ { 2 } , \delta _ { 1 } , \delta _ { 2 }$ , for a given base classification method Algorithm 3 outputs an H-NP classifier that controls the under-classification errors while minimizing the weighted sum of the other empirical errors. The blue half violin plots in Figure 6 show the resulting approximate errors after H-NP adjustment. We observe that the common cell type combination feature M.4 consistently leads to smaller errors under both the classical and H-NP classifiers, especially for linear classification models (logistic regression and SVM). We have also implemented a neural network classifier. However, as the training sample size is relatively small, its performance is not as good as the linear classification models, and the results are deferred to Supplementary Figure S14.

![](images/0fcaca2ecd4df34d94f3c4603886954bc02cace52c816d0f204db79a2fffbd72.jpg)

![](images/a8e53370b22e68de53bc5dc1a11bee3c67d7eb74ef903f02c9c4ec22f796d7a6.jpg)

![](images/1ca933787b0bf06a14396148fb5fe10bdc515b7c0ac874ec6dffde2505bbd2c0.jpg)

![](images/b95b70ec9d209a0b3933c69619d95af2514bae181fbc27551181bcc3b730a019.jpg)

![](images/60d383795dddcab07f759c1fc92dfe0fc8a6ff460e823c79560c439ede5251d4.jpg)  
(a) M.1

![](images/609c41ef5bb96c83f12430cf75ff9ca0b6a848bfdc55afd977416f9f3f55508b.jpg)  
(b) M.2

![](images/cff12b237c764d5f385f4ee2f77829c2864f80c593dd6e159678dc1913cb4de8.jpg)

![](images/485845e4e057f9c0cc73ec8876cd3a825a7e2a0bf01bf394a4e344f88c004d55.jpg)

![](images/8c9c23c31064901a4d1bd57acc384b86c9023b9d331002aee2dab345b1f7e94b.jpg)

![](images/4d55311ee345b3ba01661ca1d488dfce917e1f7a3baa54f076ba5f0e266efbce.jpg)

![](images/d9d82b3eeb174fc9235dfc6159bb05a45bdb68752f9653de450079b549575082.jpg)  
(c) M.3

![](images/465bd049859f13155e614c63acaecba2e044c9dae814ff95a71aa0f92a76ca7d.jpg)  
(d) M.4  
Figure 6: The distribution of approximate errors for each combination of featurization method and base classification method. “error1”, “error23”, “error21”, “error31”, “error32”, “overall” correspond to $R _ { 1 \star } ( \widehat { \phi } )$ , $R _ { 2 \star } ( \widehat { \phi } )$ ， $P _ { 2 } ( \hat { Y } = 1 )$ , P<sub>3</sub>(Y<sup>ˆ</sup> = 1), $P _ { 3 } ( \hat { Y } = 2 )$ and $P ( \hat { Y } \neq Y )$ ), respectively.

In each plot of Figure $6 ,$ the two leftmost plots are the distributions of the two approximate under-classification errors $R _ { 1 \star }$ and $R _ { 2 \star }$ . We mark the 80% quantiles of $R _ { 1 \star }$ and $R _ { 2 }$ <sub>⋆</sub> by short black lines (since $\delta _ { 1 } , \delta _ { 2 } = 0 . 2 )$ , and the desired control levels $( \alpha _ { 1 } , \alpha _ { 2 } = 0 . 2 )$ by red dashed lines. The four rightmost plots show the approximate errors for the overall risk and the three components in $R ^ { c } ( \widehat { \phi } )$ as discussed in Eq (14). For all the featurization and base classification methods, the under-classification errors are controlled at the desired levels with a slight increase in the overall error, which is much smaller than the reduction in under-classification errors. This demonstrates consistency of our method and indicates its general applicability to various base classification algorithms chosen by users.

Another interesting phenomenon is that when a classical classification method is conservative for specified $\alpha _ { i }$ and $\delta _ { i }$ , our algorithm will increase the corresponding threshold $t _ { i } ,$ which relaxes the decision boundary for classes less prioritized than i. As a result, the relaxation will benefit some components in $R ^ { c } ( \widehat { \phi } )$ . In Figure 6d, in many cases the classifier produces an approximate error $R _ { 2 \star }$ less than 0.2 under the classical paradigm, which means it is conservative for the control level $\alpha _ { 2 } = 0 . 2$ at the tolerance level $\delta _ { 2 } = 0 . 2$ . In this case, the NP classifier adjusts the threshold $t _ { 2 }$ to lower the requirement for class 3, thus notably decreasing the approximate error of $P _ { 3 } ( \hat { Y } = 2 )$ .

## 3.3 Identifying genomic features associated with severity

Finally, we show that using this integrated scRNA-seq data in a classification setting enables us to identify genomic features associated with disease severity in patients at both the cell-type and gene levels. First, by combining logistic regression with an appropriate featurization, we generate a ranked list of features (i.e., cell types or genes) that are important in predicting severity. At the cell type level, we utilize logistic regression with the featurization M.2, which compresses the expression matrix for each patient into a celltype-length vector, and rank the cell types based on their coeficients from the log odds ratios of the severe category relative to the healthy category. Supplementary Table S8 shows the top-ranked cell types are $\mathrm { C D 1 4 ^ { + } }$ monocytes, NK cells, $\mathrm { C D 8 ^ { + } }$ efector T cells, and neutrophils, all with significant p-values. This is consistent with known involvement of these cell types in the immune response of severe patients [Lucas et al., 2020, Liu et al., 2020, Rajamanickam et al., 2021].

At the gene level, we utilize logistic regression with the featurization M.4, which has the best overall classification performance, and compresses each patient’s expression matrix into a gene-length vector. Similar to the above analysis at the cell-type level, we generate a ranked gene list which leads to the identification of pathways associated with the severe condition. By performing the pathway enrichment analysis on the ranked gene list, we find that the top-ranked genes are significantly enriched in pathways involved in viral defense and leukocyte-mediated immune response (Supplementary Table S9).

Next, we perform further analysis to directly demonstrate the benefits of the H-NP classification results without relying on feature ranking. Based on the featurization M.4, we construct a gene co-expression network and identify modules with groups of genes that are potentially co-regulated and functionally related. By comparing the predicted severity labels from the H-NP classifier and the classical approach, we show that the H-NP labels are better correlated with the eigengenes from these functional modules, suggesting that the H-NP labels better capture the underlying signals in the data related to disease mechanism and immune response (Supplementary Figures S15-S17). Then, we compare the gene ontology enrichment of the functional modules constructed for the severe and healthy patients separately, using the predicted H-NP labels. We find strong evidence of immune response to the virus among severe patients, while no such evidence is observed in the healthy group (Supplementary Tables S10 and S11). Finally, we note that compared with the results from the severe patients as labeled by the classical paradigm, the H-NP paradigm shows more significantly enriched modules with specific references to important cell types, including T cells, and subtypes of T cells (Supplementary Tables S10 and S12). Together, these results demonstrate that by prioritizing the severe category in our H-NP framework, we can uncover stronger biological signals in the data related to immune response.

More detailed descriptions of the methods used and analysis of results can be found in Supplementary Sections D.4 and D.5.

## 4 Discussion

In general disease severity classification, under-classification errors are more consequential as they can increase the risk of patients receiving insuficient medical care. By assuming the classes have a prioritized ordering, we propose an H-NP classification framework and its associated algorithm (Algorithm 3) capable of controlling under-classification errors at desired levels with high probability. The algorithm performs post hoc adjustment on scoring-type classification methods and thus can be applied in conjunction with most methods preferred by users. The idea of choosing thresholds on the scoring functions based on a held-out set bears resemblance to conformal splitting methods [Lei, 2014, Wang and Qiao, 2022]. However, our approach difers in that we assign only one label to each observation, while maintaining high probability error controls. Additionally, our approach prioritizes certain misclassification errors, unlike conformal prediction which treats all classes equally.

Through simulations and the case study of COVID-19 severity classification, we demonstrate the eficacy of our algorithm in achieving the desired error controls. We have also compared diferent ways of constructing interpretable feature vectors from the multi-patient scRNA-seq data and shown that the common cell type PCA featurization overall achieves better performance under various classification settings. By performing extensive gene ontology enrichment analysis, we illustrate that the use of scRNA-seq data has allowed us to gain biological insights into the disease mechanism and immune response of severe patients.

We note here that although parts of our analysis rely on a ranked feature list obtained from logistic regression, there exist tools to perform such a feature selection step for all the other base classification methods used in this paper, including neural networks, which can utilize saliency maps and other feature selection procedures [Adebayo et al., 2018, Novakovsky et al., 2023]. We have chosen logistic regression in our illustrative analysis based on its stable classification performance and ease of interpretation. In addition, if the main objective is to build a classifier for triage diagnostics using other clinical variables, one can easily apply our method to other forms of patient-level COVID-19 data with other base classification methods.

Even though our case study has three classes, the framework and algorithm developed are general. Increasing the number of classes has no efect on the minimum size requirement of the left-out part of each class for threshold selection since it sufices for each class i to satisfy $n _ { i } \ge \log \delta _ { i } / ( 1 - \alpha _ { i } )$ . We also note that the notion of prioritized classes can be defined in a context-specific way. For example, in some diseases like Alzheimer’s disease, the transitional stage is considered to be the most important [Xiong et al., 2006].

There are several interesting directions for future work. For small data problems where the minimum sample size requirement is not full-filled, we might consider adopting a parametric model, under which we can not only develop a new algorithm without minimum sample size requirement, but also study the oracle type properties of the classifiers. In terms of featurizing multi-patient scRNA-seq data, we have chosen PCA as the dimension reduction method to focus on other aspects of comparison; more dimension reduction methods can be explored in future work. It is also conceivable that the class labels in the case study are noisy with possibly biased diagnosis. Accounting for label noise with a realistic noise model and extending the work of Yao et al. [2022] to a multi-class NP classification setting will be another interesting direction to pursue.

## Acknowledgements

The authors would like to thank the Editor, Associate Editor, and two anonymous reviewers for their valuable comments, which have led to a much improved version of this paper. The authors would also like to thank Dr Yingxin Lin and the Sydney Precision Data Science Centre for their generous help with curating and processing the COVID-19 scRNA-seq data. The authors gratefully acknowledge: the UT Austin Harrington Faculty Fellowship to Y.X.R.W. and NSF DMS-2113754 to J.J.L. and X.T. The authors report there are no competing interests to declare.

## References

World Health Organization. COVID-19 dashboard, 2023. URL https://covid19.who. int/. Accessed: April 23, 2023.

Rebecca A Betensky and Yang Feng. Accounting for incomplete testing in the estimation of epidemic parameters. Int J Epidemiol, 49(5):1419–1426, 2020.

Corbin Quick, Rounak Dey, and Xihong Lin. Regression models for understanding covid-19 epidemic dynamics with incomplete data. JASA, 116(536):1561–1577, 2021.

Logan C Brooks, Evan L Ray, et al. Comparing ensemble approaches for short-term probabilistic covid-19 forecasts in the us. International Institute of Forecasters, 2020.

Francesca Tang, Yang Feng, et al. The interplay of demographic variables and social distancing scores in deep prediction of us covid-19 cases. JASA, 116(534):492–506, 2021.

Daniel J McDonald, Jacob Bien, et al. Can auxiliary indicators improve covid-19 forecasting and hotspot prediction? PNAS, 118(51), 2021.

Nick James, Max Menzies, and Peter Radchenko. Covid-19 second wave mortality in europe and the united states. Chaos, 31(3):031105, 2021.

Peter Kramlinger, Tatyana Krivobokova, and Stefan Sperlich. Marginal and conditional multiple inference for linear mixed model predictors. JASA, 0(ja):1–31, 2022. doi: 10.1080/01621459.2022.2044826. URL https://doi.org/10.1080/01621459. 2022.2044826.

Jiangpeng Wu, Pengyi Zhang, et al. Rapid and accurate identification of covid-19 infection through machine learning based on clinical available blood test results. MedRxiv, 2020.

Wei Tse Li, Jiayan Ma, et al. Using machine learning of clinical data to diagnose covid-19: a systematic review and meta-analysis. BMC Med Inform Decis Mak, 20(1):1–13, 2020.

Jiawei Zhang, Jie Ding, and Yuhong Yang. Is a classification procedure good enough?—a goodness-of-fit assessment tool for classification learning. JASA, pages 1–11, 2021.

Li Yan, Hai-Tao Zhang, et al. Prediction of criticality in patients with severe covid-19 infection using three clinical features: a machine learning-based prognostic model with clinical data in wuhan. MedRxiv, 27:2020, 2020.

Liping Sun, Fengxiang Song, et al. Combination of four clinical indicators predicts the severe/critical symptom of patients infected covid-19. J. Clin. Virol, 128:104431, 2020.

Zirun Zhao, Anne Chen, et al. Prediction model and risk scores of icu admission and mortality in covid-19. PloS one, 15(7):e0236618, 2020.

Anthony Ortiz, Anusua Trivedi, et al. Efective deep learning approaches for predicting covid-19 outcomes from chest computed tomography volumes. Sci Rep, 12(1):1–10, 2022.

Norah Alballa and Isra Al-Turaiki. Machine learning approaches in covid-19 diagnosis, mortality, and severity risk prediction: A review. IMU, 24:100564, 2021.

Yassine Meraihi, Asma Benmessaoud Gabis, et al. Machine learning-based research for covid-19 detection, diagnosis, and prediction: A survey. SN computer science, 3(4):286, 2022.

Katherine A Overmyer, Evgenia Shishkova, et al. Large-scale multi-omic analysis of covid-19 severity. Cell Syst., 12(1):23–40, 2021.

Aaron J Wilk, Arjun Rustagi, et al. A single-cell atlas of the peripheral immune response in patients with severe covid-19. Nat. Med., 26(7):1070–1076, 2020.

Emily Stephenson, Gary Reynolds, et al. Single-cell multi-omics analysis of the immune response in covid-19. Nat. Med., 27(5):904–916, 2021.

Xianwen Ren, Wen Wen, et al. Covid-19 immune features revealed by a large-scale singlecell transcriptome atlas. Cell, 184(7):1895–1913, 2021.

Sara Aibar, Celia Fontanillo, et al. Analyse multiple disease subtypes and build associated gene networks using genome-wide expression profiles. BMC genomics, 16:1–10, 2015.

Eirini Arvaniti and Manfred Claassen. Sensitive detection of rare disease-associated cell subsets via representation learning. Nat. Commun., 8(1):1–10, 2017.

Zicheng Hu, Benjamin S Glicksberg, and Atul J Butte. Robust prediction of clinical outcomes using cytometry data. Bioinformatics, 35(7):1197–1203, 2019.

World Health Organization. Who r&d blueprint novel coronavirus covid-19 therapeutic trial synopsis. World Health Organization, pages 1–9, 2020.

Xin Tong, Yang Feng, and Jingyi Jessica Li. Neyman-pearson classification algorithms and np receiver operating characteristics. Sci. Adv., 4(2):eaao1659, 2018.

Yingxin Lin, Lipin Loo, et al. Scalable workflow for characterization of cell-cell communication in covid-19 patients. PLoS Comp Biol, 18(10):e1010495, 2022a.

Klemens B Meyer and Stephen G Pauker. Screening for hiv: can we aford the false positive rate?, 1987.

Marcel Dettling and Peter B¨uhlmann. Boosting for tumor classification with gene expression data. Bioinformatics, 19(9):1061–1069, 2003.

Charles Elkan. The foundations of cost-sensitive learning. In International joint conference on artificial intelligence, volume 17, pages 973–978. Lawrence Erlbaum Associates Ltd, 2001.

Dragos D Margineantu. Class probability estimation and cost-sensitive classification decisions. In Machine Learning: ECML 2002: 13th European Conference on Machine Learning Helsinki, Finland, August 19–23, 2002 Proceedings 13, pages 270–281. Springer, 2002.

Adam Cannon, James Howse, et al. Learning with the neyman-pearson and min-max criteria. Los Alamos National Laboratory, Tech. Rep. LA-UR, pages 02–2951, 2002.

Clayton Scott and Robert Nowak. A neyman-pearson approach to statistical learning. IEEE Trans. Inf. Theory, 51(11):3806–3819, 2005.

Philippe Rigollet and Xin Tong. Neyman-pearson classification, convexity and stochastic constraints. JMLR, 2011.

Lucy Xia, Richard Zhao, et al. Intentional control of type i error over unconscious data distortion: A neyman–pearson approach to text classification. JASA, 116(533):68–81, 2021.

Yang Feng, Xin Tong, and Weining Xin. Targeted crisis risk control: A neyman-pearson approach. Available at SSRN 3945980, 2021.

Thomas Landgrebe and R Duin. On neyman-pearson optimisation for multiclass classifiers. In Proceedings 16th Annual Symposium of the Pattern Recognition Association of South Africa. PRASA, pages 165–170, 2005.

Chengjie Xiong, Gerald van Belle, et al. Measuring and estimating diagnostic accuracy when there are three ordinal diagnostic groups. Statistics in Medicine, 25(7):1251–1273, 2006.

Ye Tian and Yang Feng. Neyman-pearson multi-class classification via cost-sensitive learning. arXiv preprint arXiv:2111.04597, 2021.

Natalie Stanley, Ina A Stelzer, et al. Vopo leverages cellular heterogeneity for predictive modeling of single-cell data. Nat. Commun., 11(1):1–9, 2020.

Edward A Ganio, Natalie Stanley, et al. Preferential inhibition of adaptive immune system dynamics by glucocorticoids in patients after acute surgical trauma. Nat. Commun., 11 (1):1–12, 2020.

Xiaoyuan Han, Mohammad S Ghaemi, et al. Diferential dynamics of the maternal immune system in healthy pregnancy and preeclampsia. Front Immunol., page 1305, 2019.

Mark M Davis, Cristina M Tato, and David Furman. Systems immunology: just getting started. Nat. Immunol., 18(7):725–732, 2017.

Carolina Lucas, Patrick Wong, et al. Longitudinal analyses reveal immunological misfiring in severe covid-19. Nature, 584(7821):463–469, 2020.

Jing Liu, Sumeng Li, et al. Longitudinal characteristics of lymphocyte responses and cytokine profiles in the peripheral blood of sars-cov-2 infected patients. EBioMedicine, 55:102763, 2020.

Anuradha Rajamanickam, Nathella Pavan Kumar, et al. Dynamic alterations in monocyte numbers, subset frequencies and activation markers in acute and convalescent covid-19 individuals. Sci. Rep., 11(1):20254, 2021.

Jing Lei. Classification with confidence. Biometrika, 101(4):755–769, 2014.

Wenbo Wang and Xingye Qiao. Set-valued support vector machine with bounded error rates. JASA, pages 1–13, 2022.

Julius Adebayo, Justin Gilmer, et al. Sanity checks for saliency maps. NeurIPS, 31, 2018.

Gherman Novakovsky, Nick Dexter, et al. Obtaining genetics insights from deep learning via explainable artificial intelligence. Nat. Rev. Genet., 24(2):125–137, 2023.

Shunan Yao, Bradley Rava, et al. Asymmetric error control under imperfect supervision: A label-noise-adjusted neyman–pearson umbrella algorithm. JASA, pages 1–13, 2022.

Davis J McCarthy, Kieran R Campbell, et al. Scater: pre-processing, quality control, normalization and visualization of single-cell rna-seq data in r. Bioinformatics, 33(8): 1179–1186, 2017.

Yingxin Lin, Yue Cao, et al. Atlas-scale single-cell multi-sample multi-condition data integration using scmerge2. bioRxiv, pages 2022–12, 2022b.

Yingxin Lin, Yue Cao, et al. scclassify: sample size estimation and multiscale classification of cells using single and multiple reference. Mol Syst Biol, 16(6):e9389, 2020.

Aaron TL Lun, Davis J McCarthy, and John C Marioni. A step-by-step workflow for low-level analysis of single-cell rna-seq data with bioconductor. F1000Research, 5, 2016.

Prabhu S Arunachalam, Florian Wimmers, et al. Systems biological assessment of immunity to mild versus severe covid-19 infection in humans. Science, 369(6508):1210–1220, 2020.

Pierre Bost, Francesco De Sanctis, et al. Deciphering the state of immune silence in fatal covid-19 patients. Nat. Commun., 12(1):1428, 2021.

COMBAT, David J Ahern, et al. A blood atlas of covid-19 defines hallmarks of disease severity and specificity. MedRxiv, pages 2021–05, 2021.

Alexis J Combes, Tristan Courau, et al. Global absence and targeting of protective immune states in severe covid-19. Nature, 591(7848):124–130, 2021.

Jeong Seok Lee, Seongwan Park, et al. Immunophenotyping of covid-19 and influenza highlights the role of type i interferons in development of severe covid-19. Sci Immunol, 5(49):eabd1554, 2020.

Can Liu, Andrew J Martins, et al. Time-resolved systems immunology reveals a late juncture linked to fatal covid-19. Cell, 184(7):1836–1857, 2021.

Anjali Ramaswamy, Nina N Brodsky, et al. Immune dysregulation and autoreactivity correlate with disease severity in sars-cov-2-associated multisystem inflammatory syndrome in children. Immunity, 54(5):1083–1095, 2021.

Jonas Schulte-Schrepping, Nico Reusch, et al. Severe covid-19 is marked by a dysregulated myeloid cell compartment. Cell, 182(6):1419–1440, 2020.

Alex R Schuurman, Tom DY Reijnders, et al. Integrated single-cell analysis unveils diverging immune features of covid-19, influenza, and other community-acquired pneumonia. Elife, 10:e69661, 2021.

Aymeric Silvin, Nicolas Chapuis, et al. Elevated calprotectin and abnormal myeloid cell subsets discriminate severe from mild covid-19. Cell, 182(6):1401–1418, 2020.

Sarthak Sinha, Nicole L Rosin, et al. Dexamethasone modulates immature neutrophils and interferon programming in severe covid-19. Nat. Med., 28(1):201–211, 2022.

Yapeng Su, Daniel Chen, et al. Multi-omics resolves a sharp disease-state shift between mild and moderate covid-19. Cell, 183(6):1479–1495, 2020.

Elizabeth A Thompson, Katherine Cascino, et al. Metabolic programs define dysfunctional immune responses in severe covid-19 patients. Cell reports, 34(11):108863, 2021.

Avraham Unterman, Tomokazu S Sumida, et al. Single-cell multi-omics reveals dyssynchrony of the innate and adaptive immune system in progressive covid-19. Nat. Commun., 13(1):440, 2022.

Changfu Yao, Stephanie A Bora, et al. Cell-type-specific immune dysregulation in severely ill covid-19 patients. Cell reports, 34(1):108590, 2021.

Xiang-Na Zhao, Yue You, et al. Single-cell immune profiling reveals distinct immune response in asymptomatic covid-19 patients. Signal Transduct Target Ther, 6(1):342, 2021.

Linnan Zhu, Penghui Yang, et al. Single-cell sequencing of peripheral mononuclear cells reveals distinct immune response landscapes of covid-19 and influenza patients. Immunity, 53(3):685–696, 2020.

Bianca Zadrozny and Charles Elkan. Transforming classifier scores into accurate multiclass probability estimates. In Proceedings of the eighth ACM SIGKDD international conference on Knowledge discovery and data mining, pages 694–699, 2002.

Alan Agresti. Categorical data analysis second edition, 2002.

Roman Hornung. Ordinal forests. J Classif, 37:4–17, 2020.

Eibe Frank and Mark Hall. A simple approach to ordinal classification. In Machine Learn-

ing: ECML 2001: 12th European Conference on Machine Learning Freiburg, Germany,

September 5–7, 2001 Proceedings 12, pages 145–156. Springer, 2001.

Jaime Cardoso and Joaquim Pinto da Costa. Learning to classify ordinal data: The data replication method. JMLR, 2007.

Ziyang Ma and Jeongyoun Ahn. Feature-weighted ordinal classification for predicting drug response in multiple myeloma. Bioinformatics, 37(19):3270–3276, 2021.

Marmar Moussa and Ion I M˘andoiu. Single cell rna-seq data clustering using tf-idf based methods. BMC genomics, 19(6):31–45, 2018.

Gennady Korotkevich, Vladimir Sukhov, et al. Fast gene set enrichment analysis. BioRxiv, page 060012, 2016.

Yanchun Peng, Alexander J Mentzer, et al. Broad and strong memory cd4+ and cd8+ t cells induced by sars-cov-2 in uk convalescent individuals following covid-19. Nat Immunol., 21(11):1336–1345, 2020.

Bin Zhang and Steve Horvath. A general framework for weighted gene co-expression network analysis. Stat Appl Genet Mol Biol, 4(1), 2005.

Peter Langfelder and Steve Horvath. Tutorials for the wgcna package. UCLA. Los Ageles, 2014.

Tianzhi Wu, Erqiang Hu, et al. clusterprofiler 4.0: A universal enrichment tool for interpreting omics data. The Innovation, 2(3):100141, 2021.

Chaolin Huang, Yeming Wang, et al. Clinical features of patients infected with 2019 novel coronavirus in wuhan, china. The lancet, 395(10223):497–506, 2020.

Yifan Que, Chao Hu, et al. Cytokine release syndrome in covid-19: a major mechanism of morbidity and mortality. Int Rev Immunol, 41(2):217–230, 2022.

## Supplementary Materials

## A Preprocessing of the integrated COVID-19 data

We integrate 20 collections of scRNA-seq datasets from peripheral blood mononuclear cells (PBMCs). A total of 864 patients are available and their severity levels can be found in Table S1. Table S2 summarizes populations and geographic locations covered by the datasets. We note that some of these datasets contain patients with longitudinal records; we take only one sample from these multiple measurements to ensure independence.

Before integration, we performed size factor standardization and log transformation on the raw count expression matrices using the logNormCount function in the R package scater (version 1.16.2) [McCarthy et al., 2017] and generated log transformed gene expression matrices. All the PBMC datasets are integrated by scMerge2 [Lin et al., 2022b], which is specifically designed for merging multi-sample and multi-condition studies. Following the standard pipeline for assessing the quality of integration, in Figure S2, we show the UMAP projections of all cells from all the studies, obtained from the top 20 principle components of the merged gene-by-cell expression matrix, for (a) before integration and (b) after integration. The cells are colored by their cell types (left column) or which study (or batch) they come from (right column). Before integration, cells from the same cell type are split into separate clusters based on batch labels, indicating the presence of batch efects. After integration, cells from the same cell type are significantly better mixed while the distinctions among cell types are preserved.

To construct pseudo-bulk expression profiles, we input the cell types annotated by scClassify [Lin et al., 2020] (using cell types in Stephenson et al. [2021] as reference) into scMerge2. The resulting profiles are used to identify mutual nearest subgroups as pseudoreplicates and to estimate parameters of the scMerge2 model. We select the top 3,000 highly variable genes through the function modelGeneVar in R package scran [Lun et al., 2016], and for each patient calculate the average expression of each cell type for selected genes, i.e., for each patient, the integrated dataset provides a $n _ { g } \times n _ { c }$ matrix recording the average gene expressions, where $n _ { g }$ is the number of genes $( n _ { g } = 3 , 0 0 0 )$ and $n _ { c }$ is the number of cell types $( n _ { c } = 1 8 )$

In the featurization methods M.2 and M.3, we remove the cell type ILC with its zero proportion hardly changing across all three classes (Figure S3) and an average zero proportion greater than 95% (Table S3). 17 cell types are left: B, CD14 Mono, CD16 Mono, CD4 T, CD8 T, DC,gdT, HSPC, MAST, Neutrophil, NK, NKT, Plasma, Platelet, RBC,

<table><tr><td>Publication</td><td>Severe/Critical</td><td>Mild/Moderate</td><td>Healthy</td><td>Total</td></tr><tr><td>Arunachalam et al. [2020]</td><td>4</td><td>3</td><td>5</td><td>12</td></tr><tr><td>Bost et al. [2021]</td><td>21</td><td>6</td><td>5</td><td>32</td></tr><tr><td>COMBAT et al. [2021]</td><td>62</td><td>31</td><td>10</td><td>103</td></tr><tr><td>Combes et al. [2021]</td><td>9</td><td>11</td><td>14</td><td>34</td></tr><tr><td>Lee et al. [2020]</td><td>3</td><td>4</td><td>5</td><td>12</td></tr><tr><td>Liu et al. [2021]</td><td>30</td><td>3</td><td>14</td><td>47</td></tr><tr><td>Ramaswamy et al. [2021]*</td><td>-</td><td>-</td><td>19</td><td>19</td></tr><tr><td>Ren et al. [2021]</td><td>70</td><td>61</td><td>20</td><td>151</td></tr><tr><td>Schulte-Schrepping et al. [2020]</td><td>17</td><td>19</td><td>38</td><td>74</td></tr><tr><td>Schuurman et al. [2021]</td><td>2</td><td>6</td><td>4</td><td>12</td></tr><tr><td>Silvin et al. [2020]</td><td>5</td><td>2</td><td>3</td><td>10</td></tr><tr><td>Sinha et al. [2022]</td><td>21</td><td>-</td><td>-</td><td>21</td></tr><tr><td>Stephenson et al. [2021]</td><td>28</td><td>53</td><td>32</td><td>113</td></tr><tr><td>Su et al. [2020]</td><td>12</td><td>117</td><td>-</td><td>129</td></tr><tr><td>Thompson et al. [2021]</td><td>5</td><td>-</td><td>3</td><td>8</td></tr><tr><td>Unterman et al. [2022]*</td><td>10</td><td>-</td><td>-</td><td>10</td></tr><tr><td>Wilk et al. [2020]</td><td>11</td><td>20</td><td>8</td><td>39</td></tr><tr><td>Yao et al. [2021]</td><td>6</td><td>5</td><td>-</td><td>11</td></tr><tr><td>Zhao et al. [2021]</td><td>1</td><td>8</td><td>10</td><td>19</td></tr><tr><td>Zhu et al. [2020]</td><td>1</td><td>4</td><td>3</td><td>8</td></tr><tr><td>Total</td><td>318</td><td>353</td><td>193</td><td>864</td></tr></table>

Table S1: Number of patients under each severity level in each dataset. The datasets marked with \* were utilized by both studies [Ramaswamy et al., 2021, Unterman et al., 2022] in their respective analyses.

<table><tr><td>Publication</td><td>Population</td><td>Country</td></tr><tr><td>Arunachalam et al. [2020]</td><td>Black, Caucasian</td><td>US</td></tr><tr><td>Bost et al. [2021]</td><td>-</td><td>Italy</td></tr><tr><td>COMBAT et al. [2021]</td><td>-</td><td>UK</td></tr><tr><td>Combes et al. [2021]</td><td>-</td><td>US</td></tr><tr><td>Lee et al. [2020]</td><td>-</td><td>South Korea</td></tr><tr><td>Liu et al. [2021]</td><td>Asian, Caucasian</td><td>Italy</td></tr><tr><td>Ramaswamy et al. [2021]</td><td>-</td><td>US</td></tr><tr><td>Ren et al. [2021]</td><td>Asian</td><td>China</td></tr><tr><td>Schulte-Schrepping et al. [2020]</td><td>-</td><td>Germany</td></tr><tr><td>Schuurman et al. [2021]</td><td>Black, Caucasian</td><td>Netherlands</td></tr><tr><td>Silvin et al. [2020]</td><td>-</td><td>France</td></tr><tr><td>Sinha et al. [2022]</td><td>Asian, Black, Caucasian, Others</td><td>Canada</td></tr><tr><td>Stephenson et al. [2021]</td><td>-</td><td>UK</td></tr><tr><td>Su et al. [2020]</td><td>Asian, Black, Caucasian, Others</td><td>US</td></tr><tr><td>Thompson et al. [2021]</td><td>-</td><td>US</td></tr><tr><td>Unterman et al. [2022]</td><td>-</td><td>US</td></tr><tr><td>Wilk et al. [2020]</td><td>Asian, Black, Caucasian, Hispanic/Latino, Others</td><td>US</td></tr><tr><td>Yao et al. [2021]</td><td>Asian, Black, Caucasian, Hispanic/Latino, Others</td><td>US</td></tr><tr><td>Zhao et al. [2021]</td><td>-</td><td>China</td></tr><tr><td>Zhu et al. [2020]</td><td>Asian</td><td>China</td></tr></table>

Table S2: Populations and geographic locations covered by the datasets.

DN, MAIT. Also, in M.3, we find that using the absolute values of PCA loadings notably increase the prediction performance under the classical paradigm (even though it is still not as good as M.4).

![](images/bc8163eca94a8611dc479899bf6d436f25e6ca01dd7e4e94e80f749ca5387810.jpg)

![](images/e67d0b0079ca59480ac4090da7ac78a339fb22b24aaaa971218157945fddac0f.jpg)  
Figure S1: The distribution of the proportion of zero values across patients for each cell type.

<table><tr><td>cell type</td><td>zero proportion</td><td>cell type</td><td>zero proportion</td></tr><tr><td>B</td><td>0.054</td><td>Neutrophil</td><td>0.514</td></tr><tr><td>CD14 Mono</td><td>0.028</td><td>NK</td><td>0.025</td></tr><tr><td>CD16 Mono</td><td>0.142</td><td>NKT</td><td>0.099</td></tr><tr><td>CD4 T</td><td>0.024</td><td>Plasma</td><td>0.243</td></tr><tr><td>CD8 T</td><td>0.042</td><td>Platelet</td><td>0.232</td></tr><tr><td>DC</td><td>0.186</td><td>RBC</td><td>0.730</td></tr><tr><td>gdT</td><td>0.209</td><td>DN</td><td>0.524</td></tr><tr><td>HSPC</td><td>0.548</td><td>MAIT</td><td>0.220</td></tr><tr><td>MAST</td><td>0.786</td><td>ILC</td><td>0.972</td></tr></table>

Table S3: The average proportion of zero values across patients for each cell type.

Other than scRNA-seq data, we also include age as a predictor in the integrated dataset. Most of the datasets used in our study recorded age information either as an exact number or an age group, while the rest did not provide this information (see Table S4). In the

![](images/15323a31e98606ee08f8a8b900dcb0765ef3894e2ce15bd18f405b2c8a237eff.jpg)

![](images/f45faf0728b204addbff040590de5109be74330bb96026b272e44c67c43563ba.jpg)

(a) Before integration.  
![](images/88a374480eedbbcbce629b017db043370a8bb35a1ffa06db3a28ddce6b9d8668.jpg)

![](images/bcabd559e7d5552500c89a0aa3f823800afb1d8711ace6726ab1638ea0a77d38.jpg)  
(b) After integration through scMerge.

Figure S2: Two left UMAPs plots are colored based on cell types predicted by scClassify (using Stephenson et al. [2021] as reference). Two right UMAPs plots are colored by the batches.

integrated dataset, we use the lower end of the age group recorded for patients with no exact age, and replace the missing values with the average age (52.23).

![](images/78dbaa393e77dc505d87f284b3f45f5ab8476d442b77b5e7a3cc38cc3e857f31.jpg)  
Figure S3: The proportions of zeros for diferent severity classes.

<table><tr><td>Publication</td><td>Age recording format</td><td>Example</td></tr><tr><td>Arunachalam et al. [2020]</td><td>exact age</td><td>64</td></tr><tr><td>Bost et al. [2021]</td><td>not available</td><td>NA</td></tr><tr><td>COMBAT et al. [2021]</td><td>age group</td><td>61-70</td></tr><tr><td>Combes et al. [2021]</td><td>exact age</td><td>64</td></tr><tr><td>Lee et al. [2020]</td><td>exact age</td><td>64</td></tr><tr><td>Liu et al. [2021]</td><td>exact age</td><td>64</td></tr><tr><td>Ramaswamy et al. [2021]</td><td>exact age</td><td>64</td></tr><tr><td>Ren et al. [2021]</td><td>exact age</td><td>64</td></tr><tr><td>Schulte-Schrepping et al. [2020]</td><td>age group</td><td>61-65</td></tr><tr><td>Schuurman et al. [2021]</td><td>exact age</td><td>64</td></tr><tr><td>Silvin et al. [2020]</td><td>exact age</td><td>64</td></tr><tr><td>Sinha et al. [2022]</td><td>exact age</td><td>64</td></tr><tr><td>Stephenson et al. [2021]</td><td>age group</td><td>60-69</td></tr><tr><td>Su et al. [2020]</td><td>exact age</td><td>64</td></tr><tr><td>Thompson et al. [2021]</td><td>not available</td><td>NA</td></tr><tr><td>Unterman et al. [2022]</td><td>exact age</td><td>64</td></tr><tr><td>Wilk et al. [2020]</td><td>age group</td><td>60-69</td></tr><tr><td>Yao et al. [2021]</td><td>not available</td><td>NA</td></tr><tr><td>Zhao et al. [2021]</td><td>exact age</td><td>64</td></tr><tr><td>Zhu et al. [2020]</td><td>exact age</td><td>64</td></tr></table>

Table S4: Format of age information in each dataset. An example record for a 64-year-old patient is provided for each dataset.

## B Proofs of the main results

## B.1 Proof of Proposition 1

Recall that $\mathcal { T } _ { i } = \{ T _ { i } ( X ) ~ | ~ X \in \mathcal { S } _ { i t } \}$ , and $t _ { i ( 1 ) } , \ldots , t _ { i ( n _ { i } ) }$ are the order statistics, with $n _ { i }$ being the cardinality of $\mathcal { T } _ { i } .$ Let $t _ { i ( k ) }$ be the k-th order statistic. Suppose $T _ { i } ( X )$ is the classification score of an independent observation from class $i ,$ and $F _ { i }$ is the cumulative distribution function for $- T _ { i } ( X )$ . Then,

$$
P _ {i} \left[ T _ {i} (X) <   t _ {i (k)} \mid t _ {i (k)} \right] = P _ {i} \left[ - T _ {i} (X) > - t _ {i (k)} \mid t _ {i (k)} \right] = 1 - F _ {i} \left(- t _ {i (k)}\right),
$$

and

$$
\begin{array}{l} \mathbb {P} \left(P _ {i} \left[ T _ {i} (X) <   t _ {i (k)} \mid t _ {i (k)} \right] > \alpha\right) \\ = \mathbb {P} \left[ 1 - F _ {i} \left(- t _ {i (k)}\right) > \alpha \right] = \mathbb {P} \left[ - t _ {i (k)} <   F _ {i} ^ {- 1} (1 - \alpha) \right] \\ = \mathbb {P} \left[ - t _ {i (k)} <   F _ {i} ^ {- 1} (1 - \alpha), - t _ {i (k + 1)} <   F _ {i} ^ {- 1} (1 - \alpha), \dots , - t _ {i (n _ {i})} <   F _ {i} ^ {- 1} (1 - \alpha) \right] \\ = \mathbb {P} \left[ \text {at least} n _ {i} - k + 1 \text {elements in} \mathcal {T} _ {i} \text {are less than} F _ {i} ^ {- 1} (1 - \alpha) \right] \\ = \sum_ {j = n _ {i} - k + 1} ^ {n _ {i}} {\binom {n _ {i}} {j}} \mathbb {P} \left[ - T _ {i} (X) <   F _ {i} ^ {- 1} (1 - \alpha) \right] ^ {j} \left(1 - \mathbb {P} \left[ - T _ {i} (X) <   F _ {i} ^ {- 1} (1 - \alpha) \right]\right) ^ {n _ {i} - j} \\ = \sum_ {j = 0} ^ {k - 1} {\binom {n _ {i}} {j}} \left(1 - \mathbb {P} \left[ - T _ {i} (X) <   F _ {i} ^ {- 1} (1 - \alpha) \right]\right) ^ {j} \mathbb {P} \left[ - T _ {i} (X) <   F _ {i} ^ {- 1} (1 - \alpha) \right] ^ {n _ {i} - j} \\ = (n _ {i} + 1 - k) {\binom {n _ {i}} {k - 1}} \int_ {0} ^ {\mathbb {P} \left[ - T _ {i} (X) <   F _ {i} ^ {- 1} (1 - \alpha) \right]} u ^ {n _ {i} - k} (1 - u) ^ {k - 1} d u \\ \leq (n _ {i} + 1 - k) {\binom {n _ {i}} {k - 1}} \int_ {0} ^ {1 - \alpha} u ^ {n _ {i} - k} (1 - u) ^ {k - 1} d u \\ = \sum_ {j = 0} ^ {k - 1} {\binom {n _ {i}} {j}} (\alpha) ^ {j} (1 - \alpha) ^ {n _ {i} - j} = v (k, n _ {i}, \alpha) \end{array}\tag{S.1}
$$

The inequality holds because IP $\left[ - T _ { i } ( X ) < F _ { i } ^ { - 1 } ( 1 - \alpha ) \right] \leq 1 - \alpha$ , and it becomes an equality when $F _ { i }$ is continuous.

## B.2 Proof of Theorem 1

Given $\left( t _ { 1 } , t _ { 2 } , \ldots , t _ { i - 1 } \right)$ , recall that $t _ { i ( k ) }$ and $t _ { i ( k ) } ^ { \prime }$ are the k-th order statistic of the sets

$$
\mathcal {T} _ {i} = \left\{T _ {i} (X) \mid X \in \mathcal {S} _ {i t} \right\} \quad \text { and } \quad \mathcal {T} _ {i} ^ {\prime} = \left\{T _ {i} (X) \mid X \in \mathcal {S} _ {i t}, T _ {1} (X) <   t _ {1}, \dots , T _ {i - 1} (X) <   t _ {i - 1} \right\},
$$

respectively, where $\boldsymbol { S } _ { i t }$ is the left-out class-i samples, and $\left( t _ { 1 } , t _ { 2 } , \ldots , t _ { i - 1 } \right)$ are the thresholds for the previous decisions in the classifier (3). $n _ { i }$ and $n _ { i } ^ { \prime }$ are the cardinalities of $\mathcal { T } _ { i }$ and $\mathcal { T } _ { i } ^ { \prime }$ Obviously, $n _ { i } ^ { \prime } \leq n _ { i }$ . Also, we set

$$
\hat {p} _ {i} = \frac {n _ {i} ^ {\prime}}{n _ {i}}, p _ {i} = \hat {p} _ {i} + c (n _ {i}), \alpha_ {i} ^ {\prime} = \frac {\alpha_ {i}}{p _ {i}}, \delta_ {i} ^ {\prime} = \delta_ {i} - \exp \{- 2 n _ {i} c ^ {2} (n _ {i}) \},
$$

where $\alpha _ { i }$ and $\delta _ { i }$ are the prespecified control level and violation tolerance level, $\alpha _ { i } ^ { \prime }$ and $\delta _ { i } ^ { \prime }$ are the adjusted counterparts, and $c ( n ) = \mathcal { O } ( 1 / \sqrt { n } )$ . With the adjusted $\alpha _ { i } ^ { \prime }$ and $\delta _ { i } ^ { \prime } ,$ , we consider the following two cases when selecting the upper bound of threshold:

$$
\bar {t} _ {i} = \left\{ \begin{array}{l l} t _ {i (k _ {i} ^ {\prime})} ^ {\prime}, & \text { if } n _ {i} ^ {\prime} \geq \log \delta_ {i} ^ {\prime} / \log (1 - \alpha_ {i} ^ {\prime}) \quad \text { and } \quad \alpha_ {i} ^ {\prime} <   1; \\ t _ {i (k _ {i})}, & \text { otherwise }, \end{array} \right.\tag{S.2}
$$

where $k _ { i } = \operatorname* { m a x } \{ k \mid v ( k , n _ { i } , \alpha _ { i } ) \leq \delta _ { i } \}$ and $k _ { i } ^ { \prime } = \operatorname* { m a x } \{ k \mid v ( k , n _ { i } ^ { \prime } , \alpha _ { i } ^ { \prime } ) \leq \delta _ { i } ^ { \prime } \}$ . We are going to prove that $\mathbb { P } ( P _ { i } [ T _ { 1 } ( X ) < t _ { 1 } , \ldots , T _ { i - 1 } ( X ) < t _ { i - 1 } $ and $T _ { i } ( X ) < \bar { t } _ { i } \vert \bar { t } _ { i } ] > \alpha _ { i } ) \ \leq \delta _ { i }$ by two cases.

Case 1: We consider the set $\mathcal { E } = \{ n _ { i } ^ { \prime } \geq \log \delta _ { i } ^ { \prime } / \log ( 1 - \alpha _ { i } ^ { \prime } )$ and $1 - \alpha _ { i } ^ { \prime } > 0 \}$ (case 1

in Eq (S.2)). Under this event, and we want to show that

$$
\mathbb {P} \left(P _ {i} \left[ T _ {1} (X) <   t _ {1}, \dots , T _ {i - 1} (X) <   t _ {i - 1}, \quad \text { and } \quad T _ {i} (X) <   t _ {i (k _ {i} ^ {\prime})} ^ {\prime} \mid t _ {i (k _ {i} ^ {\prime})} ^ {\prime} \right] > \alpha_ {i} \mid \mathcal {E}\right) \leq \delta_ {i}.
$$

Suppose that $T _ { i } ( X )$ is the classification score of an independent observation from class i. $F _ { i } ^ { \prime }$ is the cumulative distribution function for the classification score $- T _ { i } ( X )$ when $T _ { 1 } ( X ) < t _ { 1 } , \ldots , T _ { i - 1 } ( X ) < t _ { i - 1 }$ . Then, similar to the proof of Proposition 1,

$$
P _ {i} \left[ T _ {i} (X) <   t _ {i (k)} ^ {\prime} \mid t _ {i (k)} ^ {\prime}, T _ {1} (X) <   t _ {1}, \dots , T _ {i - 1} (X) <   t _ {i - 1} \right] = 1 - F _ {i} ^ {\prime} \left(- t _ {i (k)} ^ {\prime}\right).
$$

Note that $\alpha _ { i } ^ { \prime }$ is determined by $n _ { i } , n _ { i } ^ { \prime } , \alpha _ { i }$ . Meanwhile, $\delta _ { i } ^ { \prime }$ is fixed, as it only depends on the given values $n _ { i }$ and $\delta _ { i }$ . We have

$$
\begin{array}{l} \mathbb {P} \left(P _ {i} \left[ T _ {i} (X) <   t _ {i (k)} ^ {\prime} \big | t _ {i (k)} ^ {\prime}, T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1} \right] > \alpha_ {i} ^ {\prime} \mid n _ {i} ^ {\prime}\right) \\ = \mathbb {P} \left[ - t _ {i (k)} ^ {\prime} > (F _ {i} ^ {\prime}) ^ {- 1} (1 - \alpha_ {i} ^ {\prime}) \mid n _ {i} ^ {\prime} \right] \\ = \frac {\mathbb {P} \left[ - t _ {i (k)} ^ {\prime} > (F _ {i} ^ {\prime}) ^ {- 1} (1 - \alpha_ {i} ^ {\prime}) \quad \text { and } \quad | \mathcal {T} _ {i} | = n _ {i} ^ {\prime} \right]}{\mathbb {P} (| \mathcal {T} _ {i} | = n _ {i} ^ {\prime})} \end{array}\tag{S.3}
$$

Note that the event $\{ - t _ { i ( k ) } ^ { \prime } > ( F _ { i } ^ { \prime } ) ^ { - 1 } ( 1 - \alpha _ { i } ^ { \prime } )$ and $| \mathcal { T } _ { i } | = n _ { i } ^ { \prime } \}$ indicates that $n _ { i } ^ { \prime }$ elements in $\boldsymbol { S } _ { i t }$ satisfy $\{ T _ { 1 } ( X ) < t _ { 1 } , \ldots , T _ { i - 1 } ( X ) < t _ { i - 1 } \}$ ; among these elements, at least $n _ { i } ^ { \prime } -$ $k + 1$ elements have $T _ { i } ( X )$ less than $( F _ { i } ^ { \prime } ) ^ { - 1 } ( 1 - \alpha _ { i } ^ { \prime } )$ . We can consider $\boldsymbol { S } _ { i t }$ as independent draws from a multinomial distribution with three kinds of outcomes $( A _ { 1 } , A _ { 2 } , A _ { 3 } )$ defined in Supplementary Figure S4. Therefore,

$$
\mathbb {P} \left[ - t _ {i (k)} ^ {\prime} > (F _ {i} ^ {\prime}) ^ {- 1} (1 - \alpha_ {i} ^ {\prime}) \quad \mathrm{and} \quad | \mathcal {T} _ {i} | = n _ {i} ^ {\prime} \right]
$$

$$
\begin{array}{l} \text {A} _ {2} \\ \text {A} _ {1} \end{array} \quad \begin{array}{l} \text {A} _ {3} \\ \text {A} _ {1} \end{array} \quad \begin{array}{l} \text {A} _ {1}: T _ {j} (X) \geq t _ {j} \text {for some j\in[i-1]} \\ \text {A} _ {2}: T _ {j} (X) <   t _ {j} \text {for all j\in[i-1], and T_{i} (X)\geq(F_{i} ^{\prime})^{-1}(1- \alpha_{i}^{\prime})} \\ \text {A} _ {3}: T _ {j} (X) <   t _ {j} \text {for all j\in[i-1], and T_{i} (X)<   (F_{i} ^{\prime})^{-1}(1- \alpha_{i}^{\prime})} \\ \text {●: the elements in S_{it}} \end{array}
$$

Figure S4: Partition of $\boldsymbol { S } _ { i t }$ into three kinds of outcomes.

$$
\begin{array}{l} = \sum_ {j = n _ {i} ^ {\prime} - k + 1} ^ {n _ {i} ^ {\prime}} \binom {n _ {i}} {n _ {i} - n _ {i} ^ {\prime}, n _ {i} ^ {\prime} - j, j} P _ {i} (A _ {1}) ^ {n _ {i} - n _ {i} ^ {\prime}} P _ {i} (A _ {2}) ^ {n _ {i} ^ {\prime} - j} P _ {i} (A _ {3}) ^ {j}; \\ \mathbb {P} (| \mathcal {T} _ {i} | = n _ {i} ^ {\prime}) \\ = \binom {n _ {i}} {n _ {i} - n _ {i} ^ {\prime}} P _ {i} (A _ {1}) ^ {n _ {i} - n _ {i} ^ {\prime}} P _ {i} (A _ {2} \cup A _ {3}) ^ {n _ {i} ^ {\prime}}. \end{array}
$$

Then, by Eq (S.3),

$$
\begin{array}{r l}&{\mathbb {P} \left( \right.P _ {i} \left[ \right. T _ {i} (X) <   t _ {i (k)} ^ {\prime} \left. \right| t _ {i (k)} ^ {\prime}, T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1} \left. \right] > \alpha_ {i} ^ {\prime} \mid n _ {i} ^ {\prime}\left. \right)}\\&{= \sum_ {j = n _ {i} ^ {\prime} - k + 1} ^ {n _ {i} ^ {\prime}} \binom {n _ {i} ^ {\prime}} {j} \left(\frac {P _ {i} (A _ {2})}{P _ {i} (A _ {2} \cup A _ {3})}\right) ^ {n _ {i} ^ {\prime} - j} \left(\frac {P _ {i} (A _ {3})}{P _ {i} (A _ {2} \cup A _ {3})}\right) ^ {j}}\\&{= \sum_ {j = n _ {i} ^ {\prime} - k + 1} ^ {n _ {i} ^ {\prime}} \binom {n _ {i} ^ {\prime}} {j} (1 - P _ {i} \left[ - T _ {i} (X) <   (F _ {i} ^ {\prime}) ^ {- 1} (1 - \alpha) \mid T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1} \right]) ^ {n _ {i} ^ {\prime} - j}}\\&{\qquad \times P _ {i} \left[ - T _ {i} (X) <   (F _ {i} ^ {\prime}) ^ {- 1} (1 - \alpha_ {i} ^ {\prime}) \mid T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1} \right] ^ {j}}\\&{= \sum_ {j = 0} ^ {k - 1} \binom {n _ {i} ^ {\prime}} {j} (1 - P _ {i} \left[ - T _ {i} (X) <   (F _ {i} ^ {\prime}) ^ {- 1} (1 - \alpha) \mid T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 2} \right]) ^ {j}}\\&{\qquad \times P _ {i} \left[ - T _ {i} (X) <   (F _ {i} ^ {\prime}) ^ {- 1} (1 - \alpha_ {i} ^ {\prime}) \mid T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 2} \right] ^ {n _ {i} ^ {\prime} - j}}\\&{\leq \sum_ {j = 0} ^ {k - 1} \binom {n _ {i} ^ {\prime}} {j} (\alpha_ {i} ^ {\prime}) ^ {j} (1 - \alpha_ {i} ^ {\prime}) ^ {n _ {i} ^ {\prime} - j} = v (k, n _ {i} ^ {\prime}, \alpha_ {i} ^ {\prime}).}\end{array}
$$

The last inequality holds because

$$
P _ {i} \left[ - T _ {i} (X) <   (F _ {i} ^ {\prime}) ^ {- 1} (1 - \alpha_ {i} ^ {\prime}) \mid T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1} \right] \leq 1 - \alpha_ {i} ^ {\prime},
$$

and it becomes an equality when $( F _ { i } ^ { \prime } ) ^ { - 1 }$ is continuous.

Also,

$$
\mathbb {P} \left(P _ {i} \left[ T _ {i} (X) <   t _ {i (k _ {i} ^ {\prime})} ^ {\prime} \Big | t _ {i (k _ {i} ^ {\prime})} ^ {\prime}, T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1} \right] > \alpha_ {i} ^ {\prime} \mid n _ {i} ^ {\prime}\right) \leq \delta_ {i} ^ {\prime}
$$

since $k _ { i } ^ { \prime } = \operatorname* { m a x } \{ k \mid v ( k , n _ { i } ^ { \prime } , \alpha _ { i } ^ { \prime } ) \leq \delta _ { i } ^ { \prime } \}$ . Then,

$$
\begin{array}{l} \mathbb {P} \left(P _ {i} \left[ T _ {i} (X) <   t _ {i (k _ {i} ^ {\prime})} ^ {\prime} \Big | t _ {i (k _ {i} ^ {\prime})} ^ {\prime}, T _ {1} (X) <   t _ {1}, \dots , T _ {i - 1} (X) <   t _ {i - 1} \right] > \alpha_ {i} ^ {\prime} \Big | \mathcal {E}\right) \\ = \mathbb {E} \left[ \sum_ {j = 0} ^ {k _ {i} ^ {\prime} - 1} \binom {n _ {i} ^ {\prime}} {j} (\alpha_ {i} ^ {\prime}) ^ {j} (1 - \alpha_ {i} ^ {\prime}) ^ {n _ {i} ^ {\prime} - j} \Bigg | \mathcal {E} \right] \end{array}\tag{S.4}
$$

$$
\leq \mathbb {E} [ \delta_ {i} ^ {\prime} \mid \mathcal {E} ] = \delta_ {i} ^ {\prime}.
$$

On the other hand, note that the event $\mathcal { E } = \{ \alpha _ { i } ^ { \prime } < 1$ and $n _ { i } ^ { \prime } \geq \log \delta _ { i } ^ { \prime } / \log ( 1 - \alpha _ { i } ^ { \prime } ) \}$ is equivalent to

$$
\left(1 - \frac {\alpha_ {i} n _ {i}}{n _ {i} ^ {\prime} + n _ {i} c (n _ {i})}\right) ^ {n _ {i} ^ {\prime}} \leq \delta_ {i} ^ {\prime}\tag{S.5}
$$

and

$$
\frac {\alpha_ {i} n _ {i}}{n _ {i} ^ {\prime} + n _ {i} c (n _ {i})} <   1.\tag{S.6}
$$

The left part of the inequality (S.6) is decreasing with respect to $n _ { i } ^ { \prime }$ . Also, the left part of the inequality (S.5) is nonincreasing in $n _ { i } ^ { \prime }$ when the inequality (S.6) holds, which implies

that

$$
\mathbb {E} [ n _ {i} ^ {\prime} \mid n _ {i} ^ {\prime} \geq \log \delta_ {i} ^ {\prime} \log (1 - \alpha_ {i} ^ {\prime}) \text {and} \alpha_ {i} ^ {\prime} <   1 ] \geq \mathbb {E} [ n _ {i} ^ {\prime} \mid n _ {i} ^ {\prime} <   \log \delta_ {i} ^ {\prime} / \log (1 - \alpha_ {i} ^ {\prime}) \text {or} \alpha_ {i} ^ {\prime} \geq 1 ],
$$

i.e., $E [ n _ { i } ^ { \prime } \mid \mathcal { E } ] \ge E [ n _ { i } ^ { \prime } \mid \mathcal { E } ^ { c } ]$ . Immediately,

$$
P _ {i} \left(T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1}\right) = \mathbb {E} \left[ \frac {n _ {i} ^ {\prime}}{n _ {i}} \right] \leq \mathbb {E} \left[ \frac {n _ {i} ^ {\prime}}{n _ {i}} \bigg |   \mathcal {E} \right] = \mathbb {E} [ \hat {p} _ {i} \mid \mathcal {E} ]  ,
$$

so

$$
\begin{array}{l} \mathbb {P} (P _ {i} (T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1}) > p _ {i} | \mathcal {E}) \\ = \mathbb {P} (P _ {i} (T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1}) - \hat {p} _ {i} > c (n _ {i}) | \mathcal {E}) \\ \leq \mathbb {P} (\mathbb {E} [ \hat {p} _ {i} | \mathcal {E} ] - \hat {p} _ {i} > c (n _ {i}) | \mathcal {E}) \\ = \mathbb {P} \left(\mathbb {E} \left[ \frac {n _ {i} ^ {\prime}}{n _ {i}} \bigg | \mathcal {E} \right] - \frac {n _ {i} ^ {\prime}}{n _ {i}} > c (n _ {i}) \bigg | \mathcal {E}\right) \\ = \mathbb {P} \left(\mathbb {E} [ n _ {i} ^ {\prime} | \mathcal {E} ] - n _ {i} ^ {\prime} > n _ {i} c (n _ {i}) | \mathcal {E}\right) \\ \leq e ^ {- 2 n _ {i} c ^ {2} (n _ {i})}. \end{array}
$$

The last inequality is by Hoefding’s inequality. Then,

$$
\begin{array}{l} \mathbb {P} (P _ {i} (T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1}, \quad \text { and } \quad T _ {i} (X) <   t _ {i (k _ {i} ^ {\prime})} ^ {\prime} \mid t _ {i (k _ {i} ^ {\prime})} ^ {\prime}) > \alpha_ {i} \mid \mathcal {E}) \\ = \mathbb {P} \left[ P _ {i} (T _ {i} (X) <   t _ {i (k _ {i} ^ {\prime})} ^ {\prime} \mid t _ {i (k _ {i} ^ {\prime})} ^ {\prime}, T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1}) \right. \\ \qquad \times P _ {i} (T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1}) > \alpha_ {i} \mid \mathcal {E} ] \\ \leq \mathbb {P} [ P _ {i} (T _ {i} (X) <   t _ {i (k _ {i} ^ {\prime})} ^ {\prime} \mid t _ {i (k _ {i} ^ {\prime})} ^ {\prime}, T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1}) > \alpha_ {i} / p _ {i} \mid \mathcal {E} ] \\ \qquad + \mathbb {P} [ P _ {i} (T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1}) > p _ {i} \mid \mathcal {E} ] \end{array}
$$

$$
\leq \delta_ {i} ^ {\prime} + e ^ {- 2 n _ {i} c ^ {2} (n _ {i})} = \delta_ {i},\tag{S.7}
$$

Case 2: We consider the event $\mathcal { E } ^ { c } = \{ n _ { i } ^ { \prime } < \log \delta _ { i } ^ { \prime } / \log ( 1 - \alpha _ { i } ^ { \prime } ) \quad \mathrm { o r } \quad 1 - \alpha _ { i } ^ { \prime } \leq 0 \}$ . Under this event, $\bar { t } _ { i } = t _ { i ( k _ { i } ) }$ . Since $n _ { i }$ is deterministic, we have

$$
\mathbb {P} \left(P _ {i} \left[ T _ {i} (X) <   t _ {i (k)} \big | t _ {i (k)} \right] > \alpha_ {i} \big | \mathcal {E} ^ {c}\right) \leq \sum_ {j = 0} ^ {k - 1} \binom {n _ {i}} {j} (\alpha_ {i}) ^ {j} (1 - \alpha_ {i}) ^ {n _ {i} - j} = v (k, n _ {i}, \alpha_ {i}).
$$

The proof is similar to that of Eq (S.1) and (S.4), and even easier since $n _ { i }$ is deterministic. We do not repeat the argument here. Recall that $k _ { i } = \operatorname* { m a x } \{ k \mid v ( k , n _ { i } , \alpha _ { i } ) \leq \delta _ { i } \}$ , so

$$
\begin{array}{l} \mathbb {P} \left(P _ {i} \left[ T _ {1} (X) <   t _ {1}, \ldots , T _ {i - 1} (X) <   t _ {i - 1}, \quad \text { and } \quad T _ {i} (X) <   t _ {i (k _ {i})} \mid t _ {i (k _ {i})} \right] > \alpha_ {i} \big |   \mathcal {E} ^ {c}\right) \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \leq \mathbb {P} \left(P _ {i} \left[ T _ {i} (X) <   t _ {i (k _ {i})} \mid t _ {i (k _ {i})} \right] > \alpha_ {i} \big |   \mathcal {E} ^ {c}\right) \leq \delta_ {i}. \end{array}\tag{S.8}
$$

Eq (S.8) implies

By Eq (S.2), (S.7) and (S.8),

$$
\mathbb {P} \left(P _ {i} \left[ T _ {1} (X) <   t _ {1}, \dots , T _ {i - 1} (X) <   t _ {i - 1}, \quad \text { and } \quad T _ {i} (X) <   \bar {t} _ {i} \mid \bar {t} _ {i} \right] > \alpha_ {i}\right) \leq \delta_ {i},
$$

which implies the inequality (10) in Theorem 1.

## B.3 The change of $v ( k , n _ { 2 } ^ { \prime } , \alpha _ { 2 } ^ { \prime } )$ in Figure 1b

In the end of Section 2.3, we discuss the selection of $t _ { 1 }$ and $t _ { 2 }$ to minimize $R ^ { c }$ . Recall that k denotes the position of yellow ball $( \mathrm { i n } \ T _ { 2 } ^ { \prime } )$ in Figure 1b; $\alpha _ { 2 } ^ { \prime }$ and $\delta _ { 2 } ^ { \prime }$ are the adjusted control level and violation tolerance for the second under-classification error $R _ { 2 \star } ( \widehat { \phi } ) ; n _ { 2 } ^ { \prime }$ is the cardinality of $\mathcal { T } _ { 2 } ^ { \prime } . \ k , \ \alpha _ { 2 } ^ { \prime }$ and $n _ { 2 } ^ { \prime }$ are functions of $t _ { 1 }$ . In the following discussion, we will show that the change in $v ( k , n _ { 2 } ^ { \prime } , \alpha _ { 2 } ^ { \prime } )$ with respect to changing $t _ { 1 }$ is not monotonic.

We consider a random variable $Z \sim { \mathrm { B i n o m i a l } } ( n , \alpha )$ . We abbreviate $P _ { n , \alpha } ( z ) = P _ { n , \alpha } ( Z =$ $z )$ and $F _ { n , \alpha } ( z ) \ : = \ : P _ { n , \alpha } ( Z \ : \leq \ : z )$ . Note that $F _ { n , \alpha } ( z ) \ : = \ : v ( z , n , \alpha )$ . We will explore how the change of $n \ ( \mathrm { i . e . }$ , the change of $n _ { 2 } ^ { \prime } )$ afect the value of $F _ { n , \alpha } ( z )$ . The following lemma discusses the changes in case 1 of Figure 1b.

Lemma 1. Let $Z \sim B i n o m i a l ( n , \alpha _ { n } )$ , where $\textstyle \alpha _ { n } = { \frac { c _ { 1 } } { n + c _ { 2 } } }$ for some positive constant $c _ { 1 }$ and $c _ { 2 }$ , then $F _ { n , \alpha _ { n } } ( z - 1 ) < F _ { n + 1 , \alpha _ { n + 1 } } ( z )$

Proof. Let $Y = Z + X$ , where $Z \sim$ Binomial $( n , \alpha )$ and $X \sim$ Bernoulli(α) are independent. Then, $Y \sim$ Binomia $( n + 1 , \alpha )$ and

$$
\begin{array}{l} F _ {n + 1, \alpha} (z) = P (Y \leq z) = P (X + Z \leq z) \\ \qquad = P (X \leq 1 \mid Z \leq z - 1) P (Z \leq z - 1) + P (X = 0 \mid Z = z) P (Z = z) \\ \qquad = P (X \leq 1) F _ {n, \alpha} (z - 1) + P (X = 0) P _ {n, \alpha} (z) \\ \qquad = F _ {n, \alpha} (z - 1) + (1 - \alpha) P _ {n, \alpha} (z). \end{array}\tag{S.9}
$$

Also, for fixed z and n, we have

$$
\begin{array}{c} \frac {d F _ {n , \alpha} (z)}{d \alpha} = \frac {d}{d \alpha} (n - z) \binom {n} {z} \int_ {0} ^ {1 - \alpha} u ^ {n - z - 1} (1 - u) ^ {z} d u \\ = - (n - z) \binom {n} {z} \alpha^ {z} (1 - \alpha) ^ {n - z - 1} = - n P _ {n - 1, \alpha} (z). \end{array}
$$

Therefore, there exists a constant $c \in [ \alpha _ { n + 1 } , \alpha _ { n } ]$ such that

$$
\frac {F _ {n , \alpha_ {n + 1}} (z) - F _ {n , \alpha_ {n}} (z)}{\alpha_ {n} - \alpha_ {n + 1}} = n P _ {n - 1, c} (z).\tag{S.10}
$$

Note that $\alpha _ { n } - \alpha _ { n + 1 } > 0$ . Then,

$$
\begin{array}{l} F _ {n + 1, \alpha_ {n + 1}} (z) - F _ {n, \alpha_ {n}} (z - 1) \\ = F _ {n + 1, \alpha_ {n + 1}} (z) - F _ {n, \alpha_ {n + 1}} (z - 1) + F _ {n, \alpha_ {n + 1}} (z - 1) - F _ {n, \alpha_ {n}} (z - 1) \\ \geq (1 - \alpha_ {n + 1}) P _ {n, \alpha_ {n + 1}} (z) > 0. \end{array}
$$

Note that

$$
\alpha_ {2} ^ {\prime} = \frac {\alpha_ {2}}{p _ {2}} = \frac {\alpha_ {2}}{n _ {2} ^ {\prime} / n _ {2} + c (n _ {2})} = \frac {\alpha_ {2} n _ {2}}{n _ {2} ^ {\prime} + c (n _ {2}) n _ {2}}.
$$

Since $n _ { 2 }$ is fixed, we can write $\alpha _ { 2 }$ in the form of $\frac { c _ { 1 } } { n _ { 2 } ^ { \prime } + c _ { 2 } }$ for some positive constants $c _ { 1 }$ and $c _ { 2 }$ . In other words, if we remove an element to the left of the yellow element in Figure 1b case 1, the value of $v ( k , n _ { 2 } ^ { \prime } , \alpha _ { 2 } ^ { \prime } )$ will decrease.

By contrast, there are situations in case 2 of Figure 1b that will increase $v ( k , n _ { 2 } ^ { \prime } , \alpha _ { 2 } ^ { \prime } )$ R as discussed in the following lemma.

Lemma 2. Let $Z \sim$ Binomia $l ( n , \alpha _ { n } )$ , where $\textstyle \alpha _ { n } \ = \ { \frac { c _ { 1 } } { n + c _ { 2 } } }$ and $c _ { 2 } \geq c _ { 1 } > 0$ . Fix $z > 0$ $F _ { n , \alpha _ { n } } ( z )$ is decreasing with respect to $n \geq n _ { l }$ where $n _ { l } = \operatorname* { m i n } \{ n \mid ( n - 1 ) \alpha _ { n + 1 } \geq z \}$

Proof. Eq (S.9) implies

$$
F _ {n + 1, \alpha} (z) - F _ {n, \alpha} (z) = - \alpha P _ {n, \alpha} (z).\tag{S.11}
$$

On the other hand, for fixed n and $z ,$

$$
\frac {d \log (P _ {n , \alpha} (z))}{d \alpha} = \frac {z}{\alpha} - \frac {n - z}{1 - \alpha} \left\{ \begin{array}{l l} > 0, & \alpha <   z / n; \\ = 0, & \alpha = z / n; \\ <   0, & \alpha > z / n, \end{array} \right.\tag{S.12}
$$

so $P _ { n - 1 , c } ( z )$ is decreasing on $[ \alpha _ { n + 1 } , \alpha _ { n } ]$ when $( n - 1 ) \alpha _ { n + 1 } \geq z$ . Then, according to Eq (S.10)

$$
F _ {n, \alpha_ {n + 1}} (z) - F _ {n, \alpha_ {n}} (z) \leq n (\alpha_ {n} - \alpha_ {n + 1}) P _ {n - 1, \alpha_ {n + 1}} (z).\tag{S.13}
$$

By Eq (S.11) and (S.13), for $( n - 1 ) \alpha _ { n + 1 } \geq z$

$$
\begin{array}{r l} & F _ {n + 1, \alpha_ {n + 1}} (z) - F _ {n, \alpha_ {n}} (z) = F _ {n + 1, \alpha_ {n + 1}} (z) - F _ {n, \alpha_ {n + 1}} (z) + F _ {n, \alpha_ {n + 1}} (z) - F _ {n, \alpha_ {n}} (z) \\ & \qquad \leq - \alpha_ {n + 1} P _ {n, \alpha_ {n + 1}} (z) + n (\alpha_ {n} - \alpha_ {n + 1}) P _ {n - 1, \alpha_ {n + 1}} (z) \\ & \qquad = - \binom {n} {z} (\alpha_ {n + 1}) ^ {z + 1} (1 - \alpha_ {n + 1}) ^ {n - z} \\ & \qquad \qquad + \frac {n}{n + c _ {2}} \binom {n - 1} {z} (\alpha_ {n + 1}) ^ {z + 1} (1 - \alpha_ {n + 1}) ^ {n - z - 1} \\ & \qquad = \left(\alpha_ {n + 1} - 1 + \frac {n - z}{n + c _ {2}}\right) \binom {n} {z} (\alpha_ {n + 1}) ^ {z + 1} (1 - \alpha_ {n + 1}) ^ {n - z - 1} \\ & \qquad \leq \left(- \frac {n + 1 + c _ {2} - c _ {1}}{n + 1 + c _ {2}} + \frac {n}{n + c _ {2}}\right) \binom {n} {z} (\alpha_ {n + 1}) ^ {z + 1} (1 - \alpha_ {n + 1}) ^ {n - z - 1} \\ & \qquad = - \frac {(c _ {2} - c _ {1}) (n + c _ {2}) + c _ {2}}{(n + c _ {2}) (n + c _ {2} + 1)} \binom {n} {z} (\alpha_ {n + 1}) ^ {z + 1} (1 - \alpha_ {n + 1}) ^ {n - z - 1} \\ & <   0, \end{array}
$$

since $c _ { 2 } \geq c _ { 1 } > 0$

Furthermore,

$$
(n - 1) \alpha_ {n + 1} = \frac {n - 1}{n + 1 + c _ {2}} c _ {1}
$$

is increasing in n, i.e, any $n \geq n _ { l }$ satisfies $( n - 1 ) \alpha _ { n + 1 } \geq z$ . It establishes that $F _ { n , \alpha _ { n } } ( z )$ is decreasing with respect to n when $n \geq n _ { l }$ □

This lemma presents a situation for case 2 in Figure 1b, where $v ( k , n _ { 2 } ^ { \prime } , \alpha _ { 2 } ^ { \prime } )$ will increase.

## C Additional results for simulation studies

## C.1 Summary of simulation settings

In the simulation studies, we consider I = 3 and the feature vectors in class i are generated as $\left( X ^ { i } \right) ^ { \top } \sim N ( \mu _ { i } , I )$ . The following simulation settings are used throughout the paper:

• Setting T1.1: $N _ { i } = 5 0 0 , \mu _ { 1 } = ( 0 , - 1 ) ^ { \top } , \mu _ { 2 } = ( - 1 , 1 ) ^ { \top } , \mu _ { 3 } = ( 1 , 0 ) ^ { \top }$ . When applying the H-NP method, the observations are randomly separated into parts for score training, threshold selection, and computing empirical errors: $S _ { 1 }$ is split into 50%, 50% for $\begin{array} { r } { S _ { 1 s } , \ S _ { 1 t } ; \ S _ { 2 } } \end{array}$ is split into 45%, 50% and 5% for $S _ { 2 s } , \ S _ { 2 t }$ and $S _ { 2 e } ; \ S _ { 3 }$ is split into 95%, 5% for $S _ { 3 s } , S _ { 3 e }$ , respectively.

• Setting T2.1: ${ { N } _ { i } } = 5 0 0 , { { \mu } _ { 1 } } = { { ( 0 , - 1 ) } ^ { \top } } , { { \mu } _ { 2 } } = { { ( - 1 , 1 ) } ^ { \top } } , { { \mu } _ { 1 } } = { { ( 0 , - 3 ) } ^ { \top } }$ . The data splitting is the same as in the setting T1.1 when applying the H-NP method.

• Setting T3.1: $N _ { 1 } = 1 , 0 0 0 , N _ { 2 } = 2 0 0 , N _ { 3 } = 8 0 0 . \ \mu _ { 1 } = ( 0 , 0 ) ^ { \top } , \mu _ { 2 } = ( - 0 . 5 , 0 . 5 ) ^ { \top }$ , and $\mu _ { 3 } = ( 2 , 2 ) ^ { \top }$ . The data splitting is the same as in the setting T1.1 when applying the H-NP method.

All the results in the simulation studies are based on 1,000 repetitions from a given setting. To approximate and evaluate the true population errors, we additionally generate 60,000 observations as the test set. The ratio of the three classes in the test set is the same as $N _ { 1 } : N _ { 2 } : N _ { 3 }$

We further consider simulation settings T1.2-T1.7, which are variations of T1.1 with the same values of $\mu _ { i }$ . The details of these simulation settings can be found in Table S5. In the following subsections, these settings allow us to investigate the impact of diferent splitting settings, score functions, and imbalanced class sizes on the performance of our H-

NP classifier. We also compare the performance of our method with cost-sensitive learning, ordinal classification and weight-adjusted classification.

<table><tr><td></td><td>Class</td><td colspan="3">1</td><td colspan="4">2</td><td colspan="3">3</td></tr><tr><td>Setting</td><td>Method</td><td> $S_{1s}$ (%)</td><td> $S_{1t}$ (%)</td><td> $N_1$ (size)</td><td> $S_{2s}$ (%)</td><td> $S_{2t}$ (%)</td><td> $S_{2e}$ (%)</td><td> $N_2$ (size)</td><td> $S_{3s}$ (%)</td><td> $S_{3e}$ (%)</td><td> $N_3$ (size)</td></tr><tr><td colspan="12">Basic setting</td></tr><tr><td rowspan="2">T1.1</td><td>classical</td><td>100</td><td>-</td><td>500</td><td>100</td><td>-</td><td>-</td><td>500</td><td>100</td><td>-</td><td>500</td></tr><tr><td>H-NP</td><td>50</td><td>50</td><td>500</td><td>45</td><td>50</td><td>5</td><td>500</td><td>95</td><td>5</td><td>500</td></tr><tr><td rowspan="2">T1.2</td><td>classical</td><td>100(90,10)</td><td>-</td><td>500</td><td>100(90,10)</td><td>-</td><td>-</td><td>500</td><td>100(90,10)</td><td>-</td><td>500</td></tr><tr><td>H-NP</td><td>50(40,10)</td><td>50</td><td>500</td><td>45(35,10)</td><td>50</td><td>5</td><td>500</td><td>95(85,10)</td><td>5</td><td>500</td></tr><tr><td colspan="12">Different splitting ratios (smaller  $S_{it}$ )</td></tr><tr><td>T1.3</td><td>H-NP</td><td>80</td><td>20</td><td>500</td><td>75</td><td>20</td><td>5</td><td>500</td><td>95</td><td>5</td><td>500</td></tr><tr><td>T1.4</td><td>H-NP</td><td>70</td><td>30</td><td>500</td><td>65</td><td>30</td><td>5</td><td>500</td><td>95</td><td>5</td><td>500</td></tr><tr><td>T1.5</td><td>H-NP</td><td>60</td><td>40</td><td>500</td><td>55</td><td>40</td><td>5</td><td>500</td><td>95</td><td>5</td><td>500</td></tr><tr><td colspan="12">Different splitting ratios (larger  $S_{it}$ )</td></tr><tr><td>T1.6</td><td>H-NP</td><td>30</td><td>70</td><td>500</td><td>25</td><td>70</td><td>5</td><td>500</td><td>95</td><td>5</td><td>500</td></tr><tr><td colspan="12">Imbalanced class sizes</td></tr><tr><td rowspan="2">T1.7</td><td>classical</td><td>100</td><td>-</td><td>500</td><td>100</td><td>-</td><td>-</td><td>500</td><td>100</td><td>-</td><td>1,000</td></tr><tr><td>H-NP</td><td>50</td><td>50</td><td>500</td><td>45</td><td>50</td><td>5</td><td>500</td><td>95</td><td>5</td><td>1,000</td></tr></table>

Table S5: Data splitting and class sizes in the setting T1.1 and its variations. The feature vectors in class i are generated as $\left( X ^ { i } \right) ^ { \top } \sim N ( \mu _ { i } , I )$ , where $\mu _ { 1 } = ( 0 , - 1 ) ^ { \top } , \mu _ { 2 } = ( - 1 , 1 ) ^ { \top }$ $\mu _ { 3 } = ( 1 , 0 ) ^ { \top }$ and I is the $2 \times 2$ identity matrix. Under T1.2, we use 10% of the data (split from $S _ { i s } )$ to calibrate the probability estimates ${ \widehat { \mathbb { P } } } ( Y = i \mid X )$ for $i \in [ \mathcal { T } ]$ before computing the score $T _ { i }$ . To approximate the true population errors, we additionally generate 60,000 observations and divide them into each class following the ratio $N _ { 1 } : N _ { 2 } : N _ { 3 }$

## C.2 The influence of diferent splitting settings

We compare diferent splitting ratios in simulation settings T1.3-T1.6, assigning larger or smaller proportions of the data to select thresholds (see Table S5 for more details).

Under the settings T1.6 (larger threshold sets) and T1.4 (smaller threshold sets), Figures S5 and S6 and show similar trends as Figure 2 in the main paper. As the minimum sample size requirement on $\boldsymbol { S } _ { i t }$ is 59 in this case, the setting in Figure 2 already exceeds the requirement. Further increasing its size makes minimal diference in the performance of the H-NP classifier.

Figure S7 shows a comprehensive comparison of settings T1.3-1.5 and the basic setting T1.1, which demonstrate that again these splitting ratios lead to no notable changes. We note that the setting T1.3 only assigns 100 samples to each threshold selection set $\boldsymbol { S } _ { i t }$ which is about twice the minimum sample size requirement.

![](images/17077014ad013f459babdc0b600ad47b5590a613e44d89317c21228fc301cd67.jpg)  
(a) $R _ { 1 \star }$

![](images/f0da0b86892ed285462994001b87a8bfefaa7b46a92b929fc82b6a6b88f9d432.jpg)  
(b) $R _ { 2 \star }$

![](images/587cf32a232e11b2832e2516016479afd5a6ffb1f344522a9f4782a9e3a42e86.jpg)  
(c) $R ^ { c }$  
Figure S5: The distribution of approximate errors when $t _ { 1 }$ is the k-th largest element in $\mathcal { T } _ { 1 } \cap \left( - \infty , \overline { { t } } _ { 1 } \right)$ . The 95% quantiles of $R _ { 1 }$ <sub>⋆</sub> and $R _ { 2 \star }$ <sub>⋆</sub> are marked by blue diamonds. The target control levels for $R _ { 1 \star } ( \widehat { \phi } )$ and $R _ { 2 \star } ( \widehat { \phi } ) \left( \alpha _ { 1 } = \alpha _ { 2 } = 0 . 0 5 \right)$ are plotted as red dashed lines. The data are generated under the setting T1.6 (details in Table S5). The setting is the same as setting T1.1 except a diferent sample splitting ratio is used: samples in $S _ { 1 }$ are randomly split into 30% for $\boldsymbol { S _ { 1 s } }$ (score), 70% for $S _ { 1 t }$ (threshold); $S _ { 2 }$ are split into 25% for $S _ { 2 s }$ , 70% for $S _ { 2 t }$ , 5% for $S _ { 2 e }$ (evaluation); $S _ { 3 }$ are split into 95% for $\displaystyle { S _ { 3 s } }$ and 5% for $\displaystyle { \cal S } _ { 3 e }$

![](images/7738ac2ea8372f5bd364dc6e3a0bbaf17c8be610014220b72525e1928e7d424f.jpg)  
(a) $R _ { 1 } ,$ ⋆

![](images/832acb89bceffbed7b3ea303b13b45a9ccc32e358b4ec4086a6bb2bb5e102269.jpg)  
(b) $R _ { 2 \star }$

![](images/6311a777728350be603470e80fe2966a1567a339e164387bcf4a4beff919d6cc.jpg)  
(c) $R ^ { c }$  
Figure S6: The distribution of approximate errors when $t _ { 1 }$ is the k-th largest element in $\mathcal { T } _ { 1 } \cap \left( - \infty , \bar { t } _ { 1 } \right)$ . The 95% quantiles of $R _ { 1 \star }$ and $R _ { 2 \star }$ are marked by blue diamonds. The target control levels for $R _ { 1 \star } ( \widehat { \phi } )$ and $R _ { 2 \star } ( \widehat { \phi } ) \left( \alpha _ { 1 } = \alpha _ { 2 } = 0 . 0 5 \right)$ are plotted as red dashed lines. The data are generated under the setting T1.4 (details in Table S5). The setting is the same as setting T1.1 except a diferent sample splitting ratio is used: samples in $S _ { 1 }$ are randomly split into 70% for $\boldsymbol { S _ { 1 s } }$ , 30% for $\begin{array} { r } { S _ { 1 t } ; S _ { 2 } } \end{array}$ are split into 65% for $S _ { 2 s }$ , 30% for $S _ { 2 t }$ , 5% for $S _ { 2 e }$ ; $S _ { 3 }$ are split into 95% for $ { \boldsymbol { S } } _ { 3 s }$ and 5% for $\displaystyle { S _ { 3 e } }$

## C.3 Variations in calculating the scoring functions

As mentioned in Section 2.2, we have normalized each scoring function by the factor ${ \textstyle \sum _ { j = i + 1 } ^ { \mathcal { T } } } \widehat { \mathbb { P } } ( Y = j \mid X )$ , motivated by the NP lemma. To illustrate the benefit of normalization empirically, we compare the performance of the normalized scoring functions, $T _ { i } ( X ) \ = \ { \widehat { \mathbb { P } } } ( Y \ = \ i \mid X ) / \sum _ { j = i + 1 } ^ { Z } { \widehat { \mathbb { P } } } ( Y \ = \ j \ \mid X )$ , with that of the non-normalized ones, $T _ { i } ( X ) = \hat { \mathbb { P } } ( Y = i \mid X )$ , under the simulation setting T1.1 (see Table S5 for details), the same setting that generated Figure 5 in the main paper. Figure S8 shows the results for two sets of $\alpha _ { i } , \delta _ { i }$ values. Both scoring functions efectively control the under-classification errors, namely “error1” and “error23”, below the desired levels. However, the non-normalized approach controls “error23” in a conservative manner, which results in higher values of $^ { \mathrm { . . } } \mathrm { e r r o r 3 2 ^ { \cdot } } \ ( \mathrm { i . e . , } P _ { 3 } ( \widehat { Y } = 2 ) )$ . The other errors not depicted in the plots do not exhibit any noticeable diferences.

Next, we note that for general machine learning models such as the random forest and SVM, a probability calibration procedure is often applied to “correct” the output scores for more accurate predicted probabilities. Under the setting T1.1, we compare the original scores from each base classifier with the calibrated scores calculated by the function CalibratedClassifierCV [Zadrozny and Elkan, 2002] in the Python package sklearn. The latter is denoted as T1.2 in Table S5, where 10% of each dataset was used for calibration. Figure S9 shows the efect of calibration for all the errors under two diferent sets of $\alpha _ { i } , \delta _ { i }$ values. Little diferences can be seen for logistic regression and random forest. For SVM, the scores with no calibration perform better in $P _ { 3 } ( \hat { Y } = 1 )$ $P _ { 3 } ( \hat { Y } = 2 )$ and $P ( \hat { Y } \neq Y )$ . In all cases, the H-NP approach maintains efective control over the under-classification errors, regardless of the type of scores used.

![](images/f3afb6e61a86e17ec6c451a7741bee0b18f7cf65ce33df8fb05e1a975a172656.jpg)

![](images/617852712ccf2754d46c20f5ab9ec43c6db187d37820744b9784b0f56f249cc6.jpg)

Overall  
![](images/d369fdfbda04d6b8005b46ef620cca06a09b6a197a152e4faa07f51ceac3c1f3.jpg)

Error1  
![](images/7ffddc154ce71c70c57bf9049851e35197bbc1f5277589a6e9c8a73e8aefaf4a.jpg)

(a) Logistic Regression  
![](images/f62dbe48467459a824e0ba41f9385366e9be72f5d44b5eab9557afc798b2bc70.jpg)

Overall  
![](images/306e1db5ac7d03b52cd0ab653fb39c0125f211f39ac82fb56c9d8ca20ca58ec8.jpg)

![](images/e733baf021f2eb00bea1945e1ed559c8c962ede128bb3ba1444748b4a41977cb.jpg)

(b) Random Forest  
![](images/01509c46d09d42360ce76e54d8f2e35da32ffd7737c4a5773c572cb77450abc6.jpg)

![](images/c3993e3d168a4bcc1eb394589f30c7f49b1a5ad01f37fa939ce3d17d4075d508.jpg)  
(c) SVM  
Figure S7: The distribution of errors when using 20% (T1.3), 30% (T1.4), 40% (T1.5), and 50% (T1.1) of the samples for threshold selection, and $\alpha _ { 1 } , \alpha _ { 2 } , \delta _ { 1 } , \delta _ { 2 } = 0 . 0 5$ . The $\left( 1 - \delta _ { 1 } \right)$ % quantiles of $R _ { 1 } ^ { \star }$ and $( 1 - \delta _ { 2 } ) \%$ quantiles of $R _ { 2 } ^ { \star }$ are marked by blue diamonds. Red dashed lines represent the control levels $\alpha _ { 1 }$ and $\alpha _ { 2 }$ “error1”, “error23”, and “overall” correspond to $R _ { 1 \star } ( \widehat { \phi } )$ , $R _ { 2 \star } ( \widehat \phi )$ , and $P ( \hat { Y } \neq Y )$ , respectively.

![](images/74e0917955bdc1df74742dac904ba86cfe0a2414309f9057d3ef344e9bff8aef.jpg)

![](images/19f89fb11f85ba5c95b3a4359036e5456f21a81fecee34db57835f7c4220718d.jpg)

![](images/3be9df1da9264e5e9dceca898910ba4b42cb193262c8a2fb7befe8c08c32258a.jpg)

![](images/a27997dfd5367547180be7aac3eff7f3b4001b2acc418ba9bf165001ed317ea8.jpg)

![](images/2bd0d07b4e12c8f5805e7953ca7ca63093461c8251e2c93c29ae6f09c2b1f6f4.jpg)

![](images/b14de159f73915d6cb4ccd3767f22cb54bead349a5e794458863859d02d064b6.jpg)  
(a) $\alpha _ { i } , \delta _ { i } = 0 . 0 5$ (b) $\alpha _ { i } , \delta _ { i } = 0 . 2$ method non−normalized normalized  
Figure S8: We compare the normalized scoring functions proposed in Section 2.2 with the non-normalized version (i.e., let $T _ { i } ( X ) = \hat { \mathbb { P } } ( Y = i \mid X ) )$ under the setting T1.1. “error1”, “error23”, and “error32” correspond to the errors $R _ { 1 \star } ( \widehat \phi ) , R _ { 2 \star } ( \widehat \phi )$ , and $P _ { 3 } ( \hat { Y } = 2 )$

## C.4 Imbalanced class sizes and weight-adjusted classification

Imbalanced class sizes can lead to more dificulty in controlling prioritized errors. To investigate this efect, we consider the simulation setting T1.7 (with sample sizes of $N _ { 1 } =$ 500, $N _ { 2 } = 5 0 0 , N _ { 3 } = 1 { , } 0 0 0$ , see Table S5), where the prioritized classes have smaller sample sizes. We compare the results from the classical, H-NP, and weight-adjusted paradigms, where heavier weights are assigned to classes 1 and 2 when computing the empirical loss during optimization.

Logistic Regression  
![](images/66e0b7342e55bb38889a0d9f2c91976546ec09c78aec55e39234107fca3de9a9.jpg)

Logistic Regression  
![](images/296c4166330400de4e8ee59a4b09fc2dd066edd0b4a5883c1265535f34a22aaa.jpg)

Random Forest  
![](images/c0b6e8b335d70e9de4afee6deb430895430eb9812651e1f4ee4ffd9097a1f3aa.jpg)

Random Forest  
![](images/3ce90078eb472f40035f6aa22a52c4b88b11eeabe3d6c66d591534748f0ce4d7.jpg)

![](images/17e9c0adec01cc94a008f929a0fefcbb3c63be548fc377ce1a626fcae9f1ac20.jpg)  
(a) $\alpha _ { i } , \delta _ { i } = 0 . 0 5$

![](images/4fac026537c7bffa84673444a647883ace9f7ab980266691af36133df0b06eba.jpg)  
(b) $\alpha _ { i } , \delta _ { i } = 0 . 2$  
method calibration (T1.2) no calibration (T1.1)  
Figure S9: The distribution of errors when using the original (T1.1) and calibrated (T1.2) scores. “error1”, “error23”, “error21”, “error31”, “error32”, “overall” correspond to $R _ { 1 \star } ( \widehat { \phi } )$ $R _ { 2 \star } ( \widehat \phi ) , P _ { 2 } ( \hat { Y } = 1 ) , P _ { 3 } ( \hat { Y } = 1 ) , P _ { 3 } ( \hat { Y } = 2 )$ and $P ( \hat { Y } \neq Y )$ , respectively.

Table S6 shows the averages of the approximate errors and the relevant quantiles based on our chosen tolerance levels, with visualizations provided in Figure S10. As expected, the imbalanced setting significantly increased the under-classification errors under the classical paradigm compared with the balanced setting. We implemented H-NP with two sets of $\alpha _ { i } , \delta _ { i }$ values, and in both settings the under-classification errors are efectively controlled under the specified levels.

<table><tr><td colspan="5">Logistic Regression</td></tr><tr><td>Paradigm</td><td></td><td>Error1</td><td>Error23</td><td>Overall</td></tr><tr><td rowspan="4">classical</td><td>mean</td><td>0.491</td><td>0.176</td><td>0.264</td></tr><tr><td>90% quantile</td><td>0.509</td><td>0.188</td><td></td></tr><tr><td>80% quantile</td><td>0.504</td><td>0.184</td><td></td></tr><tr><td>70% quantile</td><td>0.499</td><td>0.181</td><td></td></tr><tr><td rowspan="2">H-NP $(\alpha_i, \delta_i = 0.10)$ </td><td>mean</td><td>0.075</td><td>0.058</td><td>0.464</td></tr><tr><td>90% quantile</td><td>0.098</td><td>0.077</td><td></td></tr><tr><td rowspan="2">weight80:50:1</td><td>mean</td><td>0.135</td><td>0.007</td><td>0.466</td></tr><tr><td>90% quantile</td><td>0.145</td><td>0.010</td><td></td></tr><tr><td rowspan="2">H-NP $(\alpha_i, \delta_i = 0.20)$ </td><td>mean</td><td>0.179</td><td>0.149</td><td>0.35</td></tr><tr><td>80% quantile</td><td>0.199</td><td>0.167</td><td></td></tr><tr><td rowspan="2">weight15:12:1</td><td>mean</td><td>0.203</td><td>0.032</td><td>0.36</td></tr><tr><td>80% quantile</td><td>0.211</td><td>0.036</td><td></td></tr><tr><td colspan="5">Random Forest</td></tr><tr><td>Paradigm</td><td></td><td>Error1</td><td>Error23</td><td>Overall</td></tr><tr><td rowspan="4">classical</td><td>mean</td><td>0.489</td><td>0.184</td><td>0.271</td></tr><tr><td>90% quantile</td><td>0.529</td><td>0.213</td><td></td></tr><tr><td>80% quantile</td><td>0.514</td><td>0.202</td><td></td></tr><tr><td>70% quantile</td><td>0.504</td><td>0.195</td><td></td></tr><tr><td rowspan="2">H-NP $(\alpha_i, \delta_i = 0.10)$ </td><td>mean</td><td>0.075</td><td>0.056</td><td>0.468</td></tr><tr><td>90% quantile</td><td>0.098</td><td>0.074</td><td></td></tr><tr><td rowspan="2">weight15:10:1</td><td>mean</td><td>0.139</td><td>0.002</td><td>0.538</td></tr><tr><td>90% quantile</td><td>0.158</td><td>0.006</td><td></td></tr><tr><td rowspan="2">H-NP $(\alpha_i, \delta_i = 0.20)$ </td><td>mean</td><td>0.178</td><td>0.148</td><td>0.354</td></tr><tr><td>80% quantile</td><td>0.198</td><td>0.167</td><td></td></tr><tr><td rowspan="2">weight4:4:1</td><td>mean</td><td>0.203</td><td>0.045</td><td>0.365</td></tr><tr><td>80% quantile</td><td>0.223</td><td>0.053</td><td></td></tr></table>

Table S6: The averages and quantiles of approximate errors under the setting T1.7. ${ } ^ { 6 6 } \mathrm { e r } .$ ror1”, “error23”, and “overall” correspond to $R _ { 1 \star } ( \widehat { \phi } )$ , $R _ { 2 \star } ( \widehat \phi )$ , and $P ( \hat { Y } \neq Y )$ , respectively.

When choosing the weights for the weight-adjusted paradigm, we note that there is no direct correspondence between the weights and our parameters $\alpha _ { i } , \delta _ { i }$ . For a fair comparison, we performed a grid search on the weights to find weight combinations that led to an overall error roughly similar to that of the H-NP classifier. The grid search is computationally intensive, and the weights are more dificult to interpret than $\alpha _ { i }$ and $\delta _ { i }$ . Table S6 and Figure S10 show the matched H-NP and weight-adjusted classifications as pairs adjacent to each other for easy comparison. We find that significantly diferent weights are needed for logistic regression and random forest to achieve similar under-diagnostic errors, suggesting that the choice of weights is not robust across diferent base classifiers, while the H-NP method is much more consistent. At similar overall error levels, the weight-adjusted classification gives higher $R _ { 1 \star } ( \widehat { \phi } )$ , while the control on $R _ { 2 \star } ( \widehat { \phi } )$ is more conservative.

![](images/9809288092f4e51d30895448bf729d06162f457c7c3b2c534b14c72b375f5244.jpg)  
Figure S10: The distributions of approximate errors in the classical, H-NP and weightadjusted classification paradigms under the setting T1.7. For H-NP, the values in parentheses indicate the values of $\alpha _ { i }$ and $\delta _ { i }$ . For weight-adjusted classification, the values in the parentheses indicate the weights assigned to classes 1,2, and 3, respectively. “error1”, “error23”, and “overall” correspond to $\bar { R _ { 1 \star } } ( \widehat \phi ) , R _ { 2 \star } ( \widehat \phi )$ , and $P ( \hat { Y } \neq Y )$ , respectively.

## C.5 Comparing with cost-sensitive learning

Cost-sensitive learning is an alternative approach to asymmetric error control. However, the costs assigned to diferent types of errors can be less interpretable and harder to select from a practitioner’s perspective (especially in the multi-class setting) than our parameters $\alpha _ { i }$ and $\delta _ { i } ,$ which represent an upper bound on error rate and a tolerance level in probability, respectively. To perform numerical comparisons, we first note that there is no direct correspondence between our $\alpha _ { i } , \delta _ { i }$ values and the error costs. The only work we are aware of connecting the multi-class NP (NPMC) problem with cost-sensitive learning is Feng et al. [2021]. Diferent from our problem setting, the NPMC method controls $R _ { 1 \star } ( { \hat { \phi } } )$ and $P _ { 2 } ( \hat { Y } \neq 2 )$ at levels $\tilde { \alpha } _ { 1 }$ and ${ \tilde { \alpha } } _ { 2 }$ by computing the appropriate cost assignment. Since $P _ { 2 } ( \hat { Y } \neq 2 )$ is a sum of $R _ { 2 \star } ( \hat { \phi } )$ and $P _ { 2 } ( \hat { Y } = 1 )$ , for a fairer comparison, we set the control levels in NPMC and H-NP to be $\tilde { \alpha } _ { 2 } = 2 \alpha _ { 2 }$ . We compared NPMC and H-NP under the simulation setting T1.1 (details in Table S5) for feasible choices $\tilde { \alpha } _ { i }$ . Setting $\tilde { \alpha } _ { 1 } , \tilde { \alpha } _ { 2 } = 0 . 2$ for NPMC and $\alpha _ { 1 } = 0 . 2 , \alpha _ { 2 } = 0 . 1$ , and $\delta _ { 1 } , \delta _ { 2 } = 0 . 1$ for H-NP, Figure S11 shows the distributions of the approximate under-classification errors from logistic regression and SVM, with the red dashed lines representing the 90% quantiles. The distributions of $R _ { 1 \star } ( \widehat { \phi } )$ highlight the diference between the approximate control by NPMC and the high probability control by H-NP. The NPMC’s control on $R _ { 2 \star } ( \widehat { \phi } )$ appears to be slightly more conservative, resulting in slightly higher $P _ { 3 } ( \hat { Y } = 2 )$ values.

![](images/be22baebe4ef3acf3a9f4ee24c2695bdb624e3fb363d7a899a8dbd55cc6f3487.jpg)  
(a) Logistic regression

![](images/4a4519509cfdc996f48884a9520028db9329b9039fcc204d1012baecf80a7306.jpg)  
(b) SVM  
Figure S11: The distributions of approximate errors on the test set under the setting T1.1 for NPMC and H-NP approaches. “error1” “error23”, and “error32” correspond to the errors $R _ { 1 \star } ( \widehat \phi ) , R _ { 2 \star } ( \widehat \phi )$ , and $P _ { 3 } ( \hat { Y } = 2 )$ ), respectively.

## C.6 Comparison with ordinal classification

We conduct comparisons with ordinal classification methods, including:

• cumulative link models (CLMs), which are a type of generalized linear models that use cumulative probabilities to characterize ordinal outcomes. We include both the logit and probit link functions [Agresti, 2002], denoted as CLM (logit/probit) in the results below. We also include the method from [Hornung, 2020] denoted as ordinalForest, which uses a similar approach using the probit link function but based on random forest;

• methods based on decomposing the multi-class classification problem into multiple binary classification problems. We compare with the method FH01 from Frank and Hall [2001], which combines the results from $\mathcal { T } - 1$ binary classifiers for classes $\{ 1 , \ldots , i \}$ versus classes $\{ i + 1 , \ldots , \mathbb { Z } \}$ , and the method oSVM from Cardoso and da Costa [2007], which considers the binary classification problem of classes $\{ i - k , \ldots , i \}$ versus classes $\{ i + 1 , \ldots , i + 1 + k \}$ for some fixed constant k. We use logistic regression and support vector machine (SVM) as the classifiers in FH01 and oSVM respectively;

• the recent method FWOC by Ma and Ahn [2021], which prioritizes important features that are highly correlated with the ordinal structure by incorporating feature weighting in linear discriminant analysis to construct the classifier.

The comparison is performed under the simulation setting T1.1 in Table S5 and the results are shown in Figure S12. The averages of approximate under-classification errors, $R _ { 1 \star } ( \widehat { \phi } )$ and $R _ { 2 \star } ( \widehat { \phi } )$ , for all ordinal methods vary widely between 0.1 and 0.4, and these two errors are not guaranteed to be lower than the other errors. Most importantly, these methods do not allow users to specify a control level on the errors of interest. For an easy comparison, we set $\alpha _ { i } , \delta _ { i } = 0 . 2 \ ( i = 1 , 2 )$ in our H-NP classifier, and as shown in Figure $\mathrm { S 1 2 ( a ) }$ , the under-classification errors are efectively controlled under the desired levels.

## C.7 Non-monotonicity in simulation studies

Finally, we provide a simulation example to exhibit that the influence of $t _ { 1 }$ on the weighted sum of errors $R ^ { c } ( \widehat { \phi } )$ is not monotonic. The cause of the non-monotonicity is explained at the end of Section 2.3. Here, the setting T3.1 sets the proportion of each class by setting $N _ { 1 } =$ $1 , 0 0 0 , N _ { 2 } = 2 0 0 , N _ { 3 } = 8 0 0$ . As a result, the weight for $P _ { 3 } ( \widehat { Y } \in \{ 1 , 2 \} )$ ) in $R ^ { c } ( \widehat { \phi } )$ increases, and the weight for $P _ { 2 } ( \widehat { Y } = 1 )$ decreases. We set $\mu _ { 1 } = ( 0 , 0 ) ^ { \top } , \mu _ { 2 } = ( - 0 . 5 , 0 . 5 ) ^ { \top }$ , and $\mu _ { 3 } = ( 2 , 2 ) ^ { \top }$ . Under this setting, class-1 and 2 are closer in Euclidean distance compared to class 3. We increase $\alpha _ { 1 }$ and $\alpha _ { 2 }$ to 0.1 to get a wider search region for $t _ { 1 }$ so that the pattern of $R ^ { c }$ is easier to observe. To approximate the true errors $R _ { 1 \star } , \ R _ { 2 }$ <sub>⋆</sub> and $R ^ { c }$ on a test set, we generate 30,000, 6,000 and 2,4000 observations for class 1, 2, 3, respectively. The ratio of the three classes in the test set is the same as $N _ { 1 } : N _ { 2 } : N _ { 3 }$ . Other settings are the same as in the setting T1.1. The results of this new simulation setting are presented in Figure S13. We can observe that $R ^ { c }$ is not monotonically decreasing, but our procedure still maintains efective controls on the under-classification errors.

![](images/9c1228986e134501d8bdd2620bb7aa3b6aaf62c66b92fe8d8e20376b0bb70482.jpg)

![](images/2027fa99efe7d4b083550427a53905c0a8b38e5c7128d0e274cfb383b35432d8.jpg)

![](images/253e927f0184593a3a5a1f2546c5de2c085eeb38d2e5fa16064920376cffdce6.jpg)  
(c) CLM (probit)

(a) $\mathrm { H - N P } ( \alpha _ { i } , \delta _ { i } = 0 . 2 0 )$  
(b) CLM (logit)  
![](images/955d24f4eb7a3021a1fbee3e0411f637529052045a486541e55c8c422e7ac74f.jpg)

![](images/a40304f36c34b01cb92df094a6c063e43f6baf77d376111c05b96b232de68715.jpg)

![](images/15157de097fbabd4a8e9591b8118a08d7846d46196dfe2332d517c7c8cc3beca.jpg)

(d) ordinalforest  
(e) FH01  
![](images/7478eaa0f383d41a15fefdccc7f470a1101bcb88b955404d04d809610b10b179.jpg)  
(f) oSVM  
(g) FWOC  
Figure S12: The distributions of approximate errors under the setting T1.1 for H-NP and ordinal classification methods. (a) H-NP with $\alpha _ { i } , \delta _ { i } = 0 . 2 ~ ( i = 1 , 2 )$ . Ordinal classification methods: (b) and (c) CLM Agresti [2002] with logit and probit link; (d) method based on random forest [Hornung, 2020]; (e) method based on logistic regression [Frank and Hall, 2001]; (f) method based on SVM [Cardoso and da Costa, 2007]; (e) method based on LDA [Ma and Ahn, 2021]. “error1”, “error23”, “error21”, “error31”, “error32”, “overall” correspond to R<sub>1⋆</sub>(ϕb), $R _ { 2 \star } ( \widehat \phi )$ $P _ { 2 } ( \hat { Y } = 1 )$ , $P _ { 3 } ( \hat { Y } = 1 )$ $P _ { 3 } ( \hat { Y } = 2 )$ and $P ( \hat { Y } \neq Y )$ , respectively.

![](images/d415bda75ec3d5a0873bddac976e192f4ef46d77d1e0996dca5950f144d62cfd.jpg)  
(a) $R _ { 1 }$

![](images/d5135b0f3c7964e22d044f4da5d356131aa21181059de482bf668cb6a305f1a9.jpg)  
(b) $R _ { 2 }$ ⋆

![](images/cc326e1d9fc594d8bb36175e9847c60464a4bee589896246a6e1611a315fc238.jpg)  
(c) $R ^ { c }$  
Figure S13: The distribution of approximate errors when $t _ { 1 }$ is the k-th largest element in $\mathcal { T } _ { 1 } \cap \left( - \infty , \bar { t } _ { 1 } \right)$ . The 95% quantiles $( \delta _ { 1 } = \delta _ { 2 } = 0 . 0 5 )$ of $R _ { 1 \star }$ and $R _ { 2 } ,$ <sub>⋆</sub> are marked by blue diamonds. The target control levels for $R _ { 1 \star } ( { \widehat { \phi } } )$ and $R _ { 2 \star } ( \widehat { \phi } ) \ ( \alpha _ { 1 } = \alpha _ { 2 } = 0 . 1 )$ are plotted as red dashed lines. Also, the averages of the $R ^ { c }$ are marked by red points in (c).

## D Additional results for COVID-19 severity classification

## D.1 Additional table of classification results

<table><tr><td colspan="8">Logistic Regression</td></tr><tr><td>Featurization</td><td>Paradigm</td><td>Error1</td><td>Error23</td><td>Error21</td><td>Error31</td><td>Error32</td><td>Overall</td></tr><tr><td rowspan="2">M.1</td><td>classical</td><td>0.313</td><td>0.110</td><td>0.241</td><td>0.078</td><td>0.241</td><td>0.330</td></tr><tr><td>H-NP</td><td>0.160</td><td>0.119</td><td>0.416</td><td>0.177</td><td>0.122</td><td>0.344</td></tr><tr><td rowspan="2">M.2</td><td>classical</td><td>0.466</td><td>0.153</td><td>0.280</td><td>0.267</td><td>0.370</td><td>0.491</td></tr><tr><td>H-NP</td><td>0.172</td><td>0.091</td><td>0.640</td><td>0.587</td><td>0.215</td><td>0.542</td></tr><tr><td rowspan="2">M.3</td><td>classical</td><td>0.248</td><td>0.115</td><td>0.226</td><td>0.060</td><td>0.178</td><td>0.284</td></tr><tr><td>H-NP</td><td>0.159</td><td>0.129</td><td>0.336</td><td>0.108</td><td>0.134</td><td>0.303</td></tr><tr><td rowspan="2">M.4</td><td>classical</td><td>0.241</td><td>0.108</td><td>0.216</td><td>0.050</td><td>0.157</td><td>0.267</td></tr><tr><td>H-NP</td><td>0.169</td><td>0.131</td><td>0.305</td><td>0.093</td><td>0.109</td><td>0.285</td></tr><tr><td colspan="8">Random Forest</td></tr><tr><td>Featurization</td><td>Paradigm</td><td>Error1</td><td>Error23</td><td>Error21</td><td>Error31</td><td>Error32</td><td>Overall</td></tr><tr><td rowspan="2">M.1</td><td>classical</td><td>0.262</td><td>0.049</td><td>0.257</td><td>0.091</td><td>0.228</td><td>0.293</td></tr><tr><td>H-NP</td><td>0.177</td><td>0.121</td><td>0.356</td><td>0.096</td><td>0.072</td><td>0.297</td></tr><tr><td rowspan="2">M.2</td><td>classical</td><td>0.361</td><td>0.095</td><td>0.256</td><td>0.216</td><td>0.452</td><td>0.426</td></tr><tr><td>H-NP</td><td>0.158</td><td>0.122</td><td>0.491</td><td>0.402</td><td>0.247</td><td>0.455</td></tr><tr><td rowspan="2">M.3</td><td>classical</td><td>0.314</td><td>0.039</td><td>0.200</td><td>0.113</td><td>0.369</td><td>0.321</td></tr><tr><td>H-NP</td><td>0.178</td><td>0.116</td><td>0.386</td><td>0.148</td><td>0.126</td><td>0.332</td></tr><tr><td rowspan="2">M.4</td><td>classical</td><td>0.300</td><td>0.036</td><td>0.219</td><td>0.130</td><td>0.353</td><td>0.323</td></tr><tr><td>H-NP</td><td>0.162</td><td>0.120</td><td>0.407</td><td>0.175</td><td>0.115</td><td>0.340</td></tr><tr><td colspan="8">SVM</td></tr><tr><td>Featurization</td><td>Paradigm</td><td>Error1</td><td>Error23</td><td>Error21</td><td>Error31</td><td>Error32</td><td>Overall</td></tr><tr><td rowspan="2">M.1</td><td>classical</td><td>0.275</td><td>0.091</td><td>0.253</td><td>0.081</td><td>0.219</td><td>0.309</td></tr><tr><td>H-NP</td><td>0.159</td><td>0.118</td><td>0.394</td><td>0.104</td><td>0.158</td><td>0.326</td></tr><tr><td rowspan="2">M.2</td><td>classical</td><td>0.437</td><td>0.164</td><td>0.280</td><td>0.281</td><td>0.365</td><td>0.487</td></tr><tr><td>H-NP</td><td>0.175</td><td>0.110</td><td>0.613</td><td>0.542</td><td>0.258</td><td>0.539</td></tr><tr><td rowspan="2">M.3</td><td>classical</td><td>0.227</td><td>0.082</td><td>0.229</td><td>0.041</td><td>0.157</td><td>0.255</td></tr><tr><td>H-NP</td><td>0.175</td><td>0.123</td><td>0.295</td><td>0.045</td><td>0.106</td><td>0.269</td></tr><tr><td rowspan="2">M.4</td><td>classical</td><td>0.229</td><td>0.077</td><td>0.222</td><td>0.037</td><td>0.160</td><td>0.251</td></tr><tr><td>H-NP</td><td>0.172</td><td>0.119</td><td>0.288</td><td>0.040</td><td>0.104</td><td>0.261</td></tr></table>

Table S7: The averages of approximate errors. “error1”, “error23”, “error21”, “error31”, “error32”, “overall” correspond to $R _ { 1 \star } ( \widehat { \phi } )$ , R<sub>2⋆</sub>(ϕb), $P _ { 2 } ( \widehat { Y } = 1 )$ ), $P _ { 3 } ( \widehat { Y } = 1 )$ ), $P _ { 3 } ( \widehat { Y } = 2 )$ and $P ( \widehat { Y } \neq Y )$ , respectively.

## D.2 A neural network classifier

We apply the Term Frequency - Inverse Document Frequency (TF-IDF) transformation [Moussa and M˘andoiu, 2018] to the matrix $( A ^ { ( 1 ) } , \ldots , A ^ { ( N ) } ) \in \mathbb { R } ^ { n _ { g } \times ( 1 8 \times N ) }$ , and let the vector

$A _ { \mathrm { T F I D F } } ^ { ( j ) } \in \mathbb { R } ^ { ( 1 8 \times n _ { g } ) \times 1 }$ be the concatenated TF-IDF scores belonging to the j-th patient. To extract features, we use PCA to reduce the dimension of $( A _ { \mathrm { T F I D F } } ^ { ( 1 ) } , \dotsc , A _ { \mathrm { T F I D F } } ^ { ( N ) } ) ^ { \intercal } \in$ $\mathbb { R } ^ { N \times ( 1 8 \times n _ { g } ) } { \mathrm { ~ t o ~ } } N \times 5 1 2$ , i.e., for patient $j ,$ we obtain a feature vector $X _ { j } \in \mathbb { R } ^ { 5 1 2 }$ . Then, we use a fully connected neural network with one hidden layer with 32 nodes, and the results are presented in Supplementary Figure S14.

![](images/9945b1d10a378c2f6b3a01a3d4c3b4e9451b89e50fb17846ed78b4ac82da13a9.jpg)

<table><tr><td colspan="7">Neural Network</td></tr><tr><td>Paradigm</td><td>Error1</td><td>Error23</td><td>Error21</td><td>Error31</td><td>Error32</td><td>Overall</td></tr><tr><td>classical</td><td>0.403</td><td>0.153</td><td>0.370</td><td>0.404</td><td>0.304</td><td>0.520</td></tr><tr><td>H-NP</td><td>0.164</td><td>0.087</td><td>0.666</td><td>0.683</td><td>0.141</td><td>0.552</td></tr></table>

Figure S14: The distributions and averages of approximate errors for the neural network approach and the H-NP classifier. “error1”, “error23”, “error21”, “error32”, “overall” correspond to $R _ { 1 \star } ( \widehat \phi ) , R _ { 2 \star } ( \widehat \phi ) , P _ { 2 } ( \widehat { Y } = 1 ) , P _ { 3 } ( \widehat { Y } = 1 ) , P _ { 3 } ( \widehat { Y } = 2 )$ and $P ( \widehat { Y } \neq Y )$ , respectively.

## D.3 Importance of cell types in severe COVID-19 outcomes

Additional results ranking importance of cell types in Table S8.

<table><tr><td>cell type</td><td>p-value</td><td>cell type</td><td>p-value</td></tr><tr><td>CD14 Mono</td><td>1.38e-05</td><td>RBC</td><td>3.91e-01</td></tr><tr><td>NK</td><td>9.95e-04</td><td>CD4 T</td><td>4.12e-01</td></tr><tr><td>CD8 T</td><td>9.10e-03</td><td>MAIT</td><td>4.16e-01</td></tr><tr><td>Neutrophil</td><td>9.54e-03</td><td>DN</td><td>4.26e-01</td></tr><tr><td>B</td><td>9.49e-02</td><td>NKT</td><td>6.13e-01</td></tr><tr><td>gdT</td><td>1.16e-01</td><td>MAST</td><td>7.81e-01</td></tr><tr><td>HSPC</td><td>2.47e-01</td><td>Plasma</td><td>8.61e-01</td></tr><tr><td>CD16 Mono</td><td>3.52e-01</td><td>DC</td><td>9.34e-01</td></tr><tr><td>Platelet</td><td>3.73e-01</td><td></td><td></td></tr></table>

Table S8: Ranking cell types by their coeficients that quantify the efect of the predictors (cell type expression) on the log odds ratios of the severe category relative to the healthy category in logistic regression with the featurization M.2.

## D.4 Gene ontology (GO) enrichment analysis of the ranked gene list

We demonstrate the utility of genome-wide expression measurements in a classification setting by identifying genes and pathways associated with disease severity. To achieve this, we employ logistic regression with the featurization M.4, which has the best overall performance in Table S7. Specifically, we rank the genes based on the coeficients that quantify the efect of the predictors (gene expression) on the log odds ratios of the outcome categories (severe) relative to a reference category (healthy) in a multinomial logistic regression model. A relatively high level of gene expression in the severe group is reflected as a larger positive coeficient, while a relatively high level of gene expression in healthy controls results in a negative coeficient. Thus, ranking the genes by their coeficients allows us to identify genes that are strongly associated with severe COVID-19.

To determine whether the ranked gene list is enriched in certain biological pathways, we use the R package fgsea [Korotkevich et al., 2016] and the Gene Ontology: Biolog ical Process (GOBP) pathway database in the R package msigdbr to perform gene set enrichment analysis. Table S9 shows the significant pathways and their corresponding adjusted p-values. Most of the pathways identified in the analysis are directly associated with various aspects of the immune response related to viral infections. Specifically, the leukocyte-mediated cytotoxicity pathway has been supported by biological studies, which have shown that leukocytes such as NK and $\mathrm { C D 8 ^ { + } ~ T }$ cells play critical roles in recognizing and targeting viral-infected cells for destruction through cytotoxicity [Peng et al., 2020, Liu et al., 2020].

<table><tr><td colspan="2">Severe vs. Healthy</td></tr><tr><td>pathway</td><td>p.adjust</td></tr><tr><td>response to virus</td><td>2.46e-02</td></tr><tr><td>defense response to symbiont</td><td>2.46e-02</td></tr><tr><td>positive regulation of dna binding transcription factor activity</td><td>2.46e-02</td></tr><tr><td>regulation of dna binding transcription factor activity</td><td>2.46e-02</td></tr><tr><td>leukocyte mediated cytotoxicity</td><td>2.46e-02</td></tr><tr><td>regulation of leukocyte migration</td><td>3.85e-02</td></tr><tr><td>cell activation involved in immune response</td><td>3.85e-02</td></tr></table>

Table S9: The most significant GOBP pathways and their corresponding adjusted p-values, using the ranked gene list from logistic regression and the featurization M.4.

## D.5 Gene functional modules from co-expression network analysis

The above analysis relies on a ranked feature list from a chosen base classifier and does not directly account for correlation patterns among genes. Next, we remove the need for feature ranking and construct gene co-expression networks by measuring pairwise correlations between gene expression levels across diferent patient samples. By identifying clusters or modules of co-expressed genes, these networks can provide valuable insights into the functional relationships between genes and the underlying biological processes. Furthermore, we will relate these functional modules to the H-NP classification result. In this analysis, we adopt the same data splitting strategy as in Section 3.2, where 70% of the data is used for training the H-NP classifier, and the remaining 30% of the data is preserved for testing the classifier and constructing gene co-expression networks and performing gene ontology enrichment analysis. We again employ logistic regression with the featurization M.4 and the control and tolerance levels remain the same as in Section 3.2.

We begin by analyzing significant biological processes in all severity groups using the held-out data. The featurization M.4 generates a feature vector with the same dimension as the number of genes for each patient. We then construct a gene co-expression network by computing the correlations between gene pairs across all patients, following the standard workflow in Zhang and Horvath [2005]. We use the TOMdist function from the R package WGCNA (version 1.71) [Langfelder and Horvath, 2014] to compute dissimilarity measures between gene pairs for performing hierarchical clustering, followed by using the cutreeDynamic function from the R package dynamicTreeCut to detect functional modules. Figure S15 shows the correlations between the module eigengenes (computed by WGCNA) and the predicted severity labels from the H-NP and classical paradigms. Overall, the H-NP labels have stronger associations with most of the eigengenes, suggesting that they better capture the underlying signals in the data as represented by these functional modules. In particular, module 1 and module 3 have the strongest association, and a closer inspection of their GO terms shows that they are significantly enriched in genes related to B cell activation and immune response to virus (Figures S16–S17, obtained using the R package clusterProfiler [Wu et al., 2021]).

Furthermore, we study diferences in the pathway enrichment between severe and healthy patients. Using the H-NP predicted labels and the test data, we construct gene coexpression matrices for the severe and healthy patients separately, followed by performing the same GO enrichment analysis as above. The top 3 enriched pathways for each module are summarized in Tables S10 (severe) and S11 (healthy). The tables show significantly diferent GO terms between the two groups; there is strong evidence of immune and viral response among the severe patients, while no such evidence is observed in the healthy group. In particular, the GO terms in the severe group are consistent with the literature that suggests severe COVID-19 is caused by an overactive immune response [Huang et al., 2020, Que et al., 2022], known as a cytokine storm, that leads to inflammation and tissue damage. Understanding the mechanisms underlying this immune response is crucial for developing efective treatments for severe COVID-19. Finally, comparing the GO terms from the severe patients with their labels given by the H-NP paradigm (Table S10) and classical paradigm (Tables S12) respectively, H-NP captures more significantly enriched modules with specific references to important cell types, including T cells, and subtypes of T cells.

![](images/98716748b72c0651b49402c3e353efe2bd5461e4b50f4ed2f5cee785a4044e5d.jpg)  
Figure S15: Correlations between consensus module eigengenes and severity labels predicted by the H-NP and classical approaches. The numbers in parentheses indicate pvalues. The results with p-values less than 0.05 are in bold.

![](images/5386c5445fb1c6dc07e3ad428c5a7fa369e57f1db70b2e94ce0d31b8554c527c.jpg)  
Figure S16: Significant GO terms in Module 1 of Figure S15. The number of genes and significance level of each dot are represented by the dot’s size and color, respectively.

![](images/67d3bfca8b9a35141478f32203c03b14bd764652d89e384c6b5320fcb10b195a.jpg)  
Figure S17: Significant GO terms in Module 3 of Figure S15. The number of genes and significance level of each dot are represented by the dot’s size and color, respectively.

<table><tr><td colspan="3">H-NP: Severe</td></tr><tr><td>module</td><td>pathway</td><td>p.adjust</td></tr><tr><td rowspan="3">1</td><td>cell activation involved in immune response</td><td>1.33e-22</td></tr><tr><td>leukocyte activation involved in immune response</td><td>2.30e-22</td></tr><tr><td>leukocyte migration</td><td>5.92e-21</td></tr><tr><td rowspan="3">2</td><td>positive regulation of cytokine production</td><td>8.65e-13</td></tr><tr><td>myeloid cell differentiation</td><td>1.22e-10</td></tr><tr><td>cytoplasmic translation</td><td>1.86e-10</td></tr><tr><td rowspan="3">3</td><td>defense response to virus</td><td>6.90e-10</td></tr><tr><td>defense response to symbiont</td><td>6.90e-10</td></tr><tr><td>negative regulation of viral process</td><td>1.54e-09</td></tr><tr><td rowspan="3">4</td><td>positive regulation of inflammatory response</td><td>1.16e-05</td></tr><tr><td>CD4-positive, alpha-beta T cell differentiation</td><td>1.16e-05</td></tr><tr><td>leukocyte cell-cell adhesion</td><td>1.16e-05</td></tr><tr><td rowspan="3">5</td><td>B cell activation</td><td>4.84e-06</td></tr><tr><td>B cell differentiation</td><td>1.68e-04</td></tr><tr><td>B cell proliferation</td><td>2.29e-04</td></tr><tr><td rowspan="3">6</td><td>regulation of T cell apoptotic process</td><td>6.29e-03</td></tr><tr><td>T cell apoptotic process</td><td>2.24e-02</td></tr><tr><td>regulation of lymphocyte apoptotic process</td><td>2.43e-02</td></tr></table>

Table S10: Top 3 GO terms for each module and their corresponding adjusted p-values. The module detection is conducted on the severe group as labeled by H-NP.

<table><tr><td colspan="3">H-NP: Healthy</td></tr><tr><td>module</td><td>pathway</td><td>p.adjust</td></tr><tr><td rowspan="3">1</td><td>mononuclear cell differentiation</td><td>3.84e-37</td></tr><tr><td>lymphocyte differentiation</td><td>2.41e-34</td></tr><tr><td>cell activation involved in immune response</td><td>1.35e-33</td></tr><tr><td rowspan="3">2</td><td>cytoplasmic translation</td><td>2.04e-11</td></tr><tr><td>ribosomal small subunit biogenesis</td><td>2.02e-02</td></tr><tr><td>ribosomal small subunit assembly</td><td>4.08e-02</td></tr><tr><td>3</td><td>platelet activation</td><td>1.01e-02</td></tr><tr><td rowspan="3">4</td><td>histone modification</td><td>1.23e-04</td></tr><tr><td>peptidyl-lysine modification</td><td>1.16e-02</td></tr><tr><td>lymphocyte apoptotic process</td><td>3.81e-02</td></tr></table>

Table S11: Top 3 GO terms for each module and their corresponding adjusted p-values. The module detection is conducted on the healthy group as labeled by H-NP.

<table><tr><td colspan="3">Classical: Severe</td></tr><tr><td>module</td><td>pathway</td><td>p.adjust</td></tr><tr><td rowspan="3">1</td><td>positive regulation of cytokine production</td><td>3.35e-30</td></tr><tr><td>mononuclear cell differentiation</td><td>1.29e-27</td></tr><tr><td>leukocyte cell-cell adhesion</td><td>1.29e-27</td></tr><tr><td rowspan="3">2</td><td>B cell activation</td><td>1.04e-07</td></tr><tr><td>histone modification</td><td>3.28e-07</td></tr><tr><td>B cell proliferation</td><td>5.50e-07</td></tr><tr><td rowspan="3">3</td><td>positive regulation of nitric-oxide synthase biosynthetic process</td><td>4.08e-02</td></tr><tr><td>urogenital system development</td><td>4.08e-02</td></tr><tr><td>nitric-oxide synthase biosynthetic process</td><td>4.08e-02</td></tr><tr><td rowspan="3">4</td><td>regulation of epidermal growth factor-activated receptor activity</td><td>2.6e-02</td></tr><tr><td>positive regulation of transforming growth factor beta receptor signaling pathway</td><td>2.6e-02</td></tr><tr><td>positive regulation of cellular response to transforming growth factor beta stimulus</td><td>2.6e-02</td></tr></table>

Table S12: Top 3 GO terms for each module and their corresponding adjusted p-values. The module detection is conducted on the severe groups as labeled by the classical paradigm.

## E General H-NP umbrella algorithm for I classes

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 4: General H-NP umbrella algorithm for $\mathcal{I}$ classes

Input : Sample: $\mathcal{S} = \cup_{i \in [\mathcal{I}]} \mathcal{S}_i$; levels: $(\alpha_1, \ldots, \alpha_{\mathcal{I}-1})$; tolerances: $(\delta_1, \ldots, \delta_{\mathcal{I}-1})$;

grid set: $A_1, \ldots, A_{\mathcal{I}-2}$ (e.g., $\mathcal{T}_1, \ldots, \mathcal{T}_{\mathcal{I}-2}$).

1 $\widehat{\pi}_i = |\mathcal{S}_i| / |\mathcal{S}|$;

2 $\mathcal{S}_{1s}, \mathcal{S}_{1t} \leftarrow$ Random split $\mathcal{S}_1$;

3 $\mathcal{S}_{is}, \mathcal{S}_{it}, \mathcal{S}_{ie} \leftarrow$ Random split $\mathcal{S}_i$ for $i = 2, \ldots, \mathcal{I}-1$;

4 $\mathcal{S}_{\mathcal{I}s}, \mathcal{S}_{\mathcal{I}e} \leftarrow$ Random split $\mathcal{S}_\mathcal{I}$;

5 $\mathcal{S}_s = \cup_{i \in [\mathcal{I}]} \mathcal{S}_{is}$;

6 $T_1, \ldots, T_{\mathcal{I}-1} \leftarrow$ A base classification method($\mathcal{S}_s$) ;

7 $\bar{t}_1 \leftarrow$ UpperBound($\mathcal{S}_{1t}, \alpha_1, \delta_1, (T_1), NULL$);

8 $\tilde{R}^c = 1$;

9 for $t_1 \in A_1 \cap (-\infty, \bar{t}_1]$ do

10 $\bar{t}_2 \leftarrow$ UpperBound($\mathcal{S}_{2t}, \alpha_2, \delta_2, (T_1, T_2), (t_1)$);

11 for $t_2 \in A_2 \cap (-\infty, \bar{t}_2]$ do

12 $\bar{t}_3 \leftarrow$ UpperBound($\mathcal{S}_{3t}, \alpha_3, \delta_3, (T_1, T_2, T_3), (t_1, t_2)$);

13 $\cdots\cdots$;

14 for $t_{\mathcal{I}-2} \in A_{\mathcal{I}-2} \cap (-\infty, \bar{t}_{\mathcal{I}-2}]$ do

15 $\bar{t}_{\mathcal{I}-1} \leftarrow$ UpperBound($\mathcal{S}_{\mathcal{I}-1t}, \alpha_{\mathcal{I}-1}, \delta_{\mathcal{I}-1}, (T_1, \ldots, T_{\mathcal{I}-1}), (t_1, \ldots, t_{\mathcal{I}-2}))$;

16 $\hat{\phi} \leftarrow$ a classifier with respect to $t_1, \ldots, t_{\mathcal{I}-1}$;

17 $\tilde{R}^c_{\text {new}} = \sum_{i=2}^{\mathcal{I}} (\hat{\pi}_i / |\mathcal{S}_{ie}|) \sum_{X \in S_{ie}} \mathbb{I}\{\hat{\phi}(X) &lt; i\}$;

18 if $\tilde{R}^c_{\text {new}} &lt; \tilde{R}^c$ then

19 | $\tilde{R}^c \leftarrow \tilde{R}^c_{\text {new}}, \hat{\phi}^* \leftarrow \hat{\phi}$

20 end

21 end

22 end

23 end

Output: $\hat{\phi}^*$
</div>

For a general $\mathcal { T } ,$ we conduct a grid search over dimension $\mathcal { Z } - 2$ . For $1 \leq i < \tau - 2$ each grid point $t _ { i }$ is selected from the set $\mathcal { T } _ { i } \cap \left( - \infty , \bar { t } _ { i } \right]$ . Thus the grid size is smaller than $C ^ { \mathcal { I } - 2 }$ , where C is typically much smaller than the cardinality of any thresholding set $| S _ { i t } |$ due to restriction of the selection region by imposed by $\bar { t } _ { i }$ . To visualize how the computational time changes with the number of classes $\mathcal { T } ,$ we compare the computational time for training the scoring function and selecting the thresholds (i.e., running our H-NP algorithm) in Figure S18 for $\mathcal { T } = 3 , 6 , 9 , 1 2$ . For this experiment, we set $N _ { i } = 1 { , } 0 0 0$ for $i \in [ \mathcal { T } ]$ , and $\alpha _ { i } = \delta _ { i } = 0 . 0 5$ for $i \in [ \mathcal { T } - 1 ]$ . We generate feature vectors in class i as $\left( X ^ { i } \right) ^ { \top } \sim N ( \mu _ { i } , I )$ , where $\mu _ { i } \in \mathbb { R } ^ { 2 0 0 }$ and the entries are independently drawn from the normal distribution with mean 0 and standard deviation 0.05. For classes 1, $\cdots , T - 1$ 2 we randomly select ${ \sim } 1 0 \%$ observations from each class for threshold selection. For classes $2 , \ldots , \tau .$ we randomly select $5 \%$ of observations to compute the empirical errors. The remaining observations are used to compute the scoring function with logistic regression as the base classification method. As expected, the computational times of both processes increase with $\mathcal { T } ,$ but overall selecting the thresholds takes a much smaller fraction of time than the training itself.

![](images/2e425b9da1dee7de36719ef5ce307b3b66fae3ea4bcdcd11f00b8b1f6b56420e.jpg)  
Figure S18: The computational times for training the scoring function and selecting the thresholds using the H-NP algorithm with $\mathcal { T } = 3 , 6 , 9 , 1 2$ . The points represent the average times, and the shade represents the magnitude of the standard deviation, from 100 repetitions.