---
title: "2024-Kim-TTA-AD-New-Normals"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2024-Kim-TTA-AD-New-Normals.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# When Model Meets New Normals: Test-Time Adaptation for Unsupervised Time-Series Anomaly Detection

Dongmin Kim, Sunghyun Park, Jaegul Choo

KAIST

tommy.dm.kim@kaist.ac.kr, psh01087@kaist.ac.kr, jchoo@kaist.ac.kr

## Abstract

Time-series anomaly detection deals with the problem of detecting anomalous timesteps by learning normality from the sequence of observations. However, the concept of normality evolves over time, leading to a "new normal problem", where the distribution of normality can be changed due to the distribution shifts between training and test data. This paper highlights the prevalence of the new normal problem in unsupervised time-series anomaly detection studies. To tackle this issue, we propose a simple yet effective test-time adaptation strategy based on trend estimation and a self-supervised approach to learning new normalities during inference. Extensive experiments on real-world benchmarks demonstrate that incorporating the proposed strategy into the anomaly detector consistently improves the model’s performance compared to the baselines, leading to robustness to the distribution shifts.

## Introduction

In real-world monitoring systems, the continuous operation of numerous sensors generates substantial real-time measurements. Time-series anomaly detection aims to identify observations that deviate from the concept of normality (Ruff et al. 2021; Pang et al. 2022) within a sequence of observations. Examples of anomalous events include physical attacks on industrial systems (Mathur and Tippenhauer 2016; Han et al. 2021), unpredictable robot behavior (Park, Hoshi, and Kemp 2018), faulty sensors from wide-sensor networks (Wang, Kuang, and Duan 2015; Rassam, Maarof, and Zainal 2018), cybersecurity attacks (Su et al. 2019; Abdulaal, Liu, and Lancewicki 2021), and spacecraft malfunctions (Hundman et al. 2018; Shin et al. 2020; Liu, Liu, and Peng 2016).

However, detecting abnormal timesteps presents significant challenges due to several factors. Firstly, the complex nature of system dynamics, characterized by the coordination of multiple sensors, complicates the task. Secondly, the increasing volume of incoming signals to monitoring systems adds to the difficulty. Lastly, acquiring labels for abnormal behaviors is problematic. To address these challenges, unsupervised time-series anomaly detection models (Xu et al. 2022; Audibert et al. 2020; Su et al. 2019; Park, Hoshi, and Kemp 2018; Malhotra et al. 2016) have emerged, focusing on learning normal patterns from available training datasets.

Nevertheless, the concept of normality can change over time, widely known as a distribution shift (Quinonero-Candela et al. 2008; Kim et al. 2022b; Sun et al. 2020; Gulrajani and Lopez-Paz 2021; Wang et al. 2021, 2022), as can be seen in the Fig. 1-(a). We have observed that offthe-shelf models are susceptible to such shifts, leading to a "new normal problem", where the distribution of normality during test time cannot be fully characterized solely based on training data. Without consideration of distribution shifts, these models tend to rely on past observations and generate false alarms, compromising the consistency of monitoring systems (Dragoi et al. 2022; Cao, Zhu, and Pang 2023).

Recently, test-time adaptation mechanisms (Wang et al. 2021, 2022; Niu et al. 2022) have been proposed to adapt models for alleviating performance degradation due to distribution shifts between training and test datasets, especially in the computer vision field. Test-time adaptation methods update the model parameters to generalize to different data distributions, without relying on either additional supervision from labels or access to training data. Time-series anomaly detection task also shares motivation for applying test-time adaptation strategies; frequent access to past data for adaptation is costly as monitoring systems work in real-time (Abdulaal, Liu, and Lancewicki 2021; Shin et al. 2020; Su et al. 2019) and model update without supervision is desired as acquiring labels is often limited (Geiger et al. 2020; Ruff et al. 2021; Audibert et al. 2020). Motivated by these advancements, we propose a test-time adaptation for unsupervised time-series anomaly detection under distribution shifts.

Our paper highlights the prevalence of the new normal problem in time-series anomaly detection literature. To address this issue properly, we propose a simple yet effective adaptation strategy using trend estimates and model updates with normal instances based on the model’s prediction itself. Trend estimate, given by the exponential moving average of the observations, follows the expected value of a timeseries with adaptation to changing conditions (Muth 1960) with computational efficiency. After model deployment, we update the model parameters with the normalized input sequence, which is detrended by subtracting the trend estimate, to learn complicated dynamics that cannot be captured solely on the trend estimate. Our proposed method makes the model robust to such distribution shifts, thereby increasing detector performance, as shown in Fig. 1-(b) and Fig. 1-(c).

![](images/c04750c5f9e1ad3d797f9f8ba8a2d1630f75ead44b803950b74fee931106e2c2.jpg)  
(a) T-SNE Plot of SWaT Data

![](images/0eff7c8491ea7c1133341a21f3eed92a369249c7b9ecb30d9061d3315d591b60.jpg)

(b) Performance Overview  
![](images/911fb72779e395479be49be263b5df7d52c90d5a11fb7c73c7e796fc66d0a38b.jpg)  
(c) Reconstruction Results (SWaT AIT201)  
Figure 1: Motivation for learning new normals. (a) T-SNE visualization of the SWaT benchmark (Mathur and Tippenhauer 2016) reveals distinct behavior between the training (red) and test data (blue). (b) Our test-time adaptation strategy surpasses previous state-of-the-art time-series anomaly detection models in terms of F1 score, even with simple baselines such as MLP-based autoencoders. (c) This improvement arises from effectively handling significant distribution shifts in the time-series data. Over time, off-the-shelf models fail to adapt to these new normals, while our approach exhibits robustness to such distribution shifts. Consequently, previous approaches (Audibert et al. 2020; Shen, Li, and Kwok 2020) produce false positive cases due to the model’s inability to keep pace with changing dynamics, thereby "the model is staying in the past while the world is changing."

Our contributions can be summarized as follows:

• We discover that new normal problems pose a significant challenge in modeling unsupervised time-series anomaly detection under distribution shifts.

• We propose a simple yet effective adaptation strategy following the trend estimate of the time-series data and update the model parameters using a detrended sequence to address these problems.

• Through extensive experiments on various real-world datasets, our method consistently improves the model’s performance when facing a severe distribution shift problem between training data and test data.

## Related Works

Unsupervised time-series anomaly detection. Unsupervised time-series anomaly detection (Su et al. 2019; Audibert et al. 2020; Xu et al. 2022) aims to detect observations that deviate considerably from normality, assuming the non-existence of the available labels. To the extent of conventional anomaly detection approaches (Breunig et al. 2000; Schölkopf et al. 1999; Tax and Duin 1999) and deeplearning-based anomaly detection approaches (Zong et al. 2018; Ruff et al. 2018), unsupervised time-series anomaly detection models aim to build an architecture that can model the temporal dynamics of the sequence.

The main categories of unsupervised time-series anomaly detection models include reconstruction-based models, clustering-based models, and forecasting-based models. Building upon the assumption of better reconstruction performance of normal instances compared to anomalous instances, reconstruction-based models encompass a range of approaches involving LSTM (Malhotra et al. 2016; Park, Hoshi, and Kemp 2018; Su et al. 2019) and MLP (Audibert et al. 2020) architectures, as well as the integration of GANs (Schlegl et al. 2017; Geiger et al. 2020; Han et al. 2021). Clustering-based methods include the extension of one-class support vector machine approaches (Schölkopf et al. 1999; Tax and Duin 1999), tensor decomposition-based clustering methods for the detection of anomalies (Shin et al. 2020), and the utilization of latent representations for clustering (Ruff et al. 2018; Shen, Li, and Kwok 2020). Forecastingbased methods rely on detecting anomalies by identifying substantial deviations between past sequences and ground truth labels, as exemplified by the use of ARIMA (Pena, de Assis, and Jr. 2013), LSTM (Hundman et al. 2018), and transformer (Xu et al. 2022).

Distribution shift in time-series data. Due to the nature of continually changing temporal dynamics, mitigating distribution shifts emerges as a pivotal concern within the time-series data analysis, notably within tasks such as time-series forecasting (Kim et al. 2022b; Liu et al. 2022) and anomaly detection (Sankararaman et al. 2022; Dragoi et al. 2022).

Online RNN-AD (Saurav et al. 2018) adapts to concept drift with RNN architectures, which update the model with backpropagation of anomaly scores using all stream data. Our work differentiates from this work by introducing detrending modules for model updates and selective learning of a set of normal instances in a self-supervised way. Although recent work (Sankararaman et al. 2022) also presents an adaptable framework for anomaly detection, it hinges on a dynamic window mechanism applied to historical data streams. Notably, our approach diverges from their assumption of accessibility of past sequences; we keep model parameters at hand, process input sequences immediately, and evict after.

Test-time adaptation. To alleviate the performance degradation caused by distribution shift, unsupervised domain adaptation (Ganin et al. 2016; Zou et al. 2018; Yoo, Chung, and Kwak 2022; Liang, Hu, and Feng 2020) methods have been developed in various fields. These methods align with our work from the perspective of addressing the covariate shift problem. In recent times, fully test-time adaptation (TTA) (Wang et al. 2021) methods have emerged to enhance the model performance on test data through real-time adaptation using unlabeled test samples during inference, without relying on access to the training data. Most TTA approaches employ entropy minimization (Wang et al. 2021; Niu et al. 2022; Choi et al. 2022) or pseudo labels (Wang et al. 2022) to update the model parameters using unlabeled test samples. However, simply adopting previous TTA methods may not be directly applicable to unsupervised time-series anomaly detection. This is due to the vulnerability of the model when updating the model using all test samples, as abnormal test samples have the potential to disrupt its functionality. Consequently, this work aims to successfully apply the concept of test-time adaptation to the unsupervised time-series anomaly detection task.

![](images/849ba5da4a857e431d1cc803c2fb8f853e7ab5e75b5c573166c79e54d1e09649.jpg)  
Figure 2: Illustration of the necessity for estimating trends and test-time adaptation. (a) NeurIPS-TS-UNI shows synthetic data generated based on the previous work (Lai et al. 2021), revealing an abrupt trend shift while preserving underlying dynamics. The objective of the trend estimation module is to adapt to such trend shifts successfully. (b) Solely relying on trend estimation may not be adequate to fully capture the dynamics, as demonstrated by the Yahoo-A1-R20 series. The shaded purple and yellow areas represent the standard deviations of the train and test data, respectively. To model this shift in dynamics, which cannot be fully captured alone with trend estimates, it is necessary to learn distribution shifts through test-time model updates outlined directly.

## Method

## Problem Statement

Unsupervised time-series anomaly detection aims to detect anomalous timesteps during test time without explicit supervision by learning the concept of normality. The concept of normality is defined as the probability distribution P on data D that is the ground-truth law of normal behavior in a given task (Ruff et al. 2021). Accordingly, a set of anomalies is defined as data with sufficiently small probability under such distribution, $i . e . , p ( x ) < \epsilon$ . New normal problem that we tackle can be formulated as the phenomena of underlying distribution P is not stationary, $i . e . , \mathbb { P } _ { t r a i n } \neq \mathbb { P } _ { t e s t }$

For observations over N timesteps with F features, timeseries data is specified by a sequence $\mathcal { D } = \{ X _ { 1 } , X _ { 2 } , . . . , X _ { N } \}$ where each $X _ { i } ^ { \textbf { \em i } } \in \mathbb { R } ^ { F }$ . An anomaly detector aims to map each observation to a class label $y = \{ \bar { 0 } , 1 \}$ , where $y = 0$ and $y =$

1 each denote normal and abnormal timesteps. The detector is specified by an anomaly score function $\mathcal { A } : \mathbb { R } ^ { F }  \mathbb { R }$ along with a decision threshold τ. Concretely, observation $X _ { t }$ is classified as anomalous if $\mathcal { A } ( X _ { t } ) ~ > ~ \tau$ . We denote the set of train-time instances as $\mathcal { D } _ { t r a i n }$ and the set of testtime instances as $\mathcal { D } _ { t e s t }$ . Accordingly, test-time normals and anomalies can be defined each as $\ T \ M \in { \mathcal { D } } _ { t e s t } \mid y = 0 \}$ and $\{ X \in \mathcal { D } _ { t e s t } \mid y = 1 \}$

To reflect the temporal context of time-series data to detect anomalous timestep(s), a set of observations $\mathcal { D }$ is preprocessed with a sliding window setting. Specifically, we denote a sequence of w observations until timestep t as $\begin{array} { r c l } { \mathcal { X } _ { w , t } } & { = } & { \left[ X _ { t - w + 1 } , X _ { t - w + 2 } , . . . , X _ { t - 1 } , X _ { t } \right] } \end{array}$ and its corresponding class label and prediction of the model as $\begin{array} { r c l } { y _ { w , t } } & { = } & { \left[ y _ { t - w + 1 } , y _ { t - w + 2 } , . . . , y _ { t - 1 } , y _ { t } \right] } \end{array}$ and $\begin{array} { r l } { \hat { \mathcal { V } } _ { w , t } } & { { } = } \end{array}$ $\left[ \hat { y } _ { t - w + 1 } , \hat { y } _ { t - w + 2 } , . . . , \hat { y } _ { t - 1 } , \hat { y } _ { t } \right]$ following conventional approaches of the time-series anomaly detection literatures (Shen, Li, and Kwok 2020; Su et al. 2019).

## Input Normalization Using Trend Estimate

A trend estimation module aims to adapt to new normals that significantly differ in trend with preserving the underlying dynamics of the sequence. Accordingly, previous work (Lai et al. 2021) defines trend-outlier as:

$$
\Delta (\mathcal {T} (\cdot), \tilde {\mathcal {T}} (\cdot)) > \delta ,\tag{1}
$$

where $\Delta$ is a function that measures the discrepancy between two functions. $\tilde { \tau }$ is a function that returns the trend of normal sequences. $\tau$ is a trend of an arbitrary sequence to compare to the trend of normal sequences. $\mathrm { F i g . } 2 \mathrm { - } ( \mathrm { a } )$ illustrates the importance of properly estimating the trend of normalities. Even though sequences before and after the transition shares the same dynamics, observations after the trend shift are classified as anomalies without proper adaptation to trends. To address such a problem, we simply detrend with trend estimates using the exponential moving average statistics. Technically, we estimate the trend as:

$$
\tilde {\mathcal {T}} (\cdot): \mu_ {t} \leftarrow \gamma \mu_ {t - w} + (1 - \gamma) \hat {\mu},\tag{2}
$$

where $\begin{array} { r } { \hat { \mu } = \frac { 1 } { w } \Sigma _ { i = t - w + 1 } ^ { t } X _ { i } } \end{array}$ , which is the empirical mean of the stream data, and $\gamma$ is a hyperparameter that controls an exponentially moving average update rate for tracking the trend of the data stream. This procedure is one form of eliminating nonstationary trend components with mean adjustment (Shumway and Stoffer 2017), allowing models to be updated with numerical stability. Concretely, as shown in Fig. 3, along with reconstruction-based anomaly detection models, the model reconstructs detrended sequence $\mathcal { X } _ { w , t } - \mu _ { t }$ instead of $\mathcal { X } _ { w , t }$ and denormalize the reconstructed sequence by adding estimated trend for the final output.

## Model Update with New Normals

Test-time adaptation with model update aims to learn the underlying dynamics of the time series data, which cannot be fully captured by trend estimation alone, as shown in Fig. 2-(b). Specifically, our approach continuously updates the model parameters with normal sequences during test time in a fully unsupervised manner. Formally, the normal instances during test-time observations can be formulated as $\{ X \in \mathcal { D } _ { t e s t } \mid \bar { y } = 0 \}$ . To update the model parameters $\theta$ during test-time, the prediction of the model itself, $\hat { \mathcal { V } }$ acts as selection criteria for filtering normal timesteps. The model is updated based on online gradient descent (Zinkevich 2003) using the following scheme:

![](images/606a3346bc9030cfbdc7825e7e092c2c9a839661b5e39b13293a2fbaa5f0c32b.jpg)  
Figure 3: Illustration on detrend module.

$$
\theta \leftarrow \theta - \eta \nabla_ {\theta} \mathcal {L} (\mathcal {X} _ {w, t}, \hat {\mathcal {Y}} _ {w, t}, \mu_ {t}, \tau),\tag{3}
$$

where $\eta$ is the test-time learning rate for the model update. $\tau$ denotes a threshold for classifying the anomalous timesteps. Specifically, our approach uses autoencoder architectures along with reconstruction loss. Hence, mentioned updating scheme can be further described as:

$$
\mathcal {L} (\mathcal {X} _ {w, t}, \hat {\mathcal {Y}} _ {w, t}, \mu_ {t}, \tau) = (1 - \hat {\mathcal {Y}} _ {w, t} ^ {\top}) (\hat {\mathcal {X}} _ {w, t} - \mathcal {X} _ {w, t}) ^ {2},\tag{4}
$$

where $\hat { \mathcal X } _ { w , t }$ denotes reconstructed output from the model and $\hat { \mathcal { V } } _ { w , t }$ denotes predicted labels, where 0 and 1 indicate normal and abnormal, respectively.

Although we utilize the entire time-series data for trend estimate, we only incorporate the normal instances to update the model based on the model’s predictions. The rationale behind this strategy stems from the assumption that unsupervised anomaly detectors are trained using normal data before model deployment. Consequently, the inclusion of anomaly samples for model updates during test time can potentially have a detrimental impact on the model’s performance. In contrast, to enable trend estimation even in scenarios with substantial variations, it is essential to incorporate normal instances that could potentially be predicted as anomalies by the anomaly detector.

## Experiments

## Experiment Setups

Datasets. We selected datasets for experiments based on the following criteria: (i) widely used datasets in time-series anomaly detection literature (SWaT), (ii) subsets with significant distribution shifts from commonly utilized datasets (SMD, MSL, SMAP), (iii) datasets including substantial distribution shifts (WADI, Yahoo), (iv) datasets with minimal distribution shifts (CreditCard).

Descriptions for the real-world datasets we utilized are as follows. (1) The SWaT (Mathur and Tippenhauer 2016) and WADI <sup>1</sup> consist of measurements collected from water treatment system testbeds. SWaT dataset covers 11 days of measurement from 51 sensors, while WADI dataset covers

![](images/90674cc1ddef6d5c182c9c39e75b478e736a734620bb88987395bd4af1957cd7.jpg)  
Figure 4: Kullback–Leibler Divergence (KLD) of various datasets. $D _ { K L } ( \mathcal { D } _ { t e s t } | | \mathcal { D } _ { t r a i n } )$ is given, which implies how much additional information is needed to fully describe $\mathcal { D } _ { t e s t } ,$ given $\mathcal { D } _ { t r a i n }$ . The measure quantifies the distribution shift problem of the datasets.

16 days of measurement from 123 sensors. (2) The SMD dataset (Su et al. 2019) includes 5 weeks of data from 28 distinct server machines with 38-dimensional sensor inputs. For the experiment, two specific server machines (Machine 1-4 and Machine 2-1) were selected due to their distribution shift problems. (3) The SMAP and MSL (Hundman et al. 2018) datasets are derived from spacecraft monitoring systems. SMAP dataset comprises monitoring data from 28 unique machines with 55 telemetry channels, whereas MSL dataset includes data from 19 unique machines with 27 telemetry channels. Data from two specific machines with distribution shifts, MSL (P-15) and SMAP (T-3), are selected for our experiments. (4) The CreditCard dataset <sup>2</sup> consists of transactional logs spanning two days. It contains 28 PCAanonymized features along with time and transaction amount information. (5) The Yahoo dataset <sup>3</sup> is a combination of real (A1) and synthetic (A2, A3, A4) datasets. Yahoo-A1 dataset contains 67 univariate real-world datasets, with a specific focus on two datasets (A1-R20 and A1-R55) exhibiting distribution shift problems. Further details and main statistics of the datasets can be found in the supplementary.

Baselines. We compare our methodology with 5 baselines: MLP-based autoencoder (MLP), LSTMEncDec (LSTM) (Malhotra et al. 2016), USAD (Audibert et al. 2020), THOC (Shen, Li, and Kwok 2020) and anomaly transformer (AT) (Xu et al. 2022). LSTM, USAD, and THOC have been re-implemented based on the description of each paper. Official implementation of anomaly transformer<sup>4</sup> is utilized in our experiments. We use hyperparameters and default settings of THOC, USAD, and AT described in their papers. MLP and LSTM use the latent dimension of 128 as default. As all the approaches are fully unsupervised, we trained all the models with the assumption of normality for train datasets. During test time, our approach gets input of w non-overlapping window, which is the same input as the train-time window size. Details of hyperparameters can be found in supplementary. Evaluation metrics. We report a metric called F1-PA (Xu et al. 2018), widely utilized in the recent time-series anomaly detection studies (Xu et al. 2022; Shen, Li, and Kwok 2020; Audibert et al. 2020; Su et al. 2019). This metric views the whole successive abnormal segment as correctly detected if any of the timesteps in the segment is classified as an anomaly. Note that F1-PA metric overestimate classifier performance (Kim et al. 2022a), even though this metric has practical justifications (Xu et al. 2018).

Therefore, we consider three additional evaluation metrics, which are F1 score, area under receiver operating characteristic curve (AUROC), and area under the precision-recall curve (AUPRC). Different from F1-PA, the F1 score can measure the anomaly detection status for each individual timestep, which directly reflects the performance of the anomaly detector. We also report AUROC and AUPRC over test data anomaly scores, which gives an overall summary of anomaly detector performance for all possible candidates of thresholds τ. AUROC takes into account the performance across all possible decision thresholds, making it less sensitive to the choice of a specific threshold. We measure AUPRC, which is well-suited for imbalanced classification scenarios (Saito and Rehmsmeier 2015; Sørbø and Ruocco 2023).

For brevity, we report these four metrics in the main paper. Other metrics for adjusted and non-adjusted metrics, including accuracy, precision, recall, F1, and confusion matrix (The number of true negatives, false positives, false negatives, and true positives), are provided in the supplementary.

## Comparison with Baselines

Main results. To validate the effectiveness of our method, we conducted a comparative analysis between unsupervised time-series anomaly detection models and the MLP model combined with our approach. As presented in Table 1, the results demonstrate that our method consistently improves the performance of the MLP model across various evaluation metrics. Notably, we achieve a significant improvement of up to 13% in the AUROC of the WADI dataset and 51% in the AUPRC of MSL (P-15), which exhibits a distribution shift problem as illustrated in Fig. 4. In the case of the Yahoo A1- R20 dataset, shown in Fig. 2-(b), our method demonstrates the highest performance gain in terms of the F1 score. In contrast to most of the datasets, our method shows only marginal improvement in the CreditCard dataset.

It is due to the fact that the dataset has a minimal distribution shift problem, resulting in a limited performance gain. The dataset that exhibits lower F1 performance compared to the off-the-shelf baseline is WADI. This discrepancy is a result of the threshold setting with test anomaly scores. Specifically, the maximum anomaly score for the WADI train data using the USAD model is 0.225, while the threshold that yields the reported F1 score in the table is 585.845, which is significantly higher. Consequently, although USAD and LSTM models exhibit higher scores for F1, the overall classifier performance measured by AUROC is lower.

<table><tr><td>Dataset</td><td>Metrics</td><td>MLP</td><td>LSTM</td><td>USAD</td><td>THOC</td><td>AT</td><td>Ours</td></tr><tr><td rowspan="4">SWaT</td><td>F1</td><td>0.765</td><td>0.401</td><td>0.557</td><td>0.776</td><td>0.218</td><td>0.784</td></tr><tr><td>F1-PA</td><td>0.831</td><td>0.768</td><td>0.655</td><td>0.862</td><td>0.962</td><td>0.903</td></tr><tr><td>AUROC</td><td>0.832</td><td>0.697</td><td>0.737</td><td>0.838</td><td>0.530</td><td>0.892</td></tr><tr><td>AUPRC</td><td>0.722</td><td>0.248</td><td>0.457</td><td>0.744</td><td>0.195</td><td>0.780</td></tr><tr><td rowspan="4">WADI</td><td>F1</td><td>0.131</td><td>0.245</td><td>0.260</td><td>0.124</td><td>0.109</td><td>0.148</td></tr><tr><td>F1-PA</td><td>0.175</td><td>0.279</td><td>0.279</td><td>0.153</td><td>0.915</td><td>0.346</td></tr><tr><td>AUROC</td><td>0.485</td><td>0.525</td><td>0.530</td><td>0.484</td><td>0.501</td><td>0.624</td></tr><tr><td>AUPRC</td><td>0.052</td><td>0.195</td><td>0.205</td><td>0.144</td><td>0.059</td><td>0.081</td></tr><tr><td rowspan="4">SMD(M-1-4)</td><td>F1</td><td>0.273</td><td>0.282</td><td>0.159</td><td>0.379</td><td>0.059</td><td>0.463</td></tr><tr><td>F1-PA</td><td>0.544</td><td>0.500</td><td>0.296</td><td>0.521</td><td>0.799</td><td>0.874</td></tr><tr><td>AUROC</td><td>0.805</td><td>0.818</td><td>0.673</td><td>0.869</td><td>0.479</td><td>0.845</td></tr><tr><td>AUPRC</td><td>0.169</td><td>0.151</td><td>0.103</td><td>0.223</td><td>0.034</td><td>0.354</td></tr><tr><td rowspan="4">SMD(M-2-1)</td><td>F1</td><td>0.236</td><td>0.283</td><td>0.308</td><td>0.295</td><td>0.094</td><td>0.249</td></tr><tr><td>F1-PA</td><td>0.814</td><td>0.910</td><td>0.922</td><td>0.705</td><td>0.866</td><td>0.974</td></tr><tr><td>AUROC</td><td>0.674</td><td>0.727</td><td>0.738</td><td>0.668</td><td>0.498</td><td>0.764</td></tr><tr><td>AUPRC</td><td>0.190</td><td>0.251</td><td>0.246</td><td>0.161</td><td>0.052</td><td>0.280</td></tr><tr><td rowspan="4">MSL(P-15)</td><td>F1</td><td>0.263</td><td>0.056</td><td>0.060</td><td>0.018</td><td>0.071</td><td>0.440</td></tr><tr><td>F1-PA</td><td>0.848</td><td>0.351</td><td>0.097</td><td>0.027</td><td>0.437</td><td>0.944</td></tr><tr><td>AUROC</td><td>0.645</td><td>0.617</td><td>0.661</td><td>0.332</td><td>0.568</td><td>0.801</td></tr><tr><td>AUPRC</td><td>0.061</td><td>0.012</td><td>0.016</td><td>0.005</td><td>0.023</td><td>0.575</td></tr><tr><td rowspan="4">SMAP(T-3)</td><td>F1</td><td>0.095</td><td>0.091</td><td>0.044</td><td>0.154</td><td>0.042</td><td>0.218</td></tr><tr><td>F1-PA</td><td>0.992</td><td>0.998</td><td>0.940</td><td>0.747</td><td>0.772</td><td>0.708</td></tr><tr><td>AUROC</td><td>0.510</td><td>0.515</td><td>0.500</td><td>0.591</td><td>0.490</td><td>0.617</td></tr><tr><td>AUPRC</td><td>0.044</td><td>0.050</td><td>0.031</td><td>0.049</td><td>0.017</td><td>0.111</td></tr><tr><td rowspan="4">CreditCard</td><td>F1</td><td>0.127</td><td>0.220</td><td>0.323</td><td>0.138</td><td>0.039</td><td>0.135</td></tr><tr><td>F1-PA</td><td>0.145</td><td>0.234</td><td>0.323</td><td>0.148</td><td>0.056</td><td>0.151</td></tr><tr><td>AUROC</td><td>0.943</td><td>0.930</td><td>0.887</td><td>0.770</td><td>0.548</td><td>0.943</td></tr><tr><td>AUPRC</td><td>0.055</td><td>0.109</td><td>0.234</td><td>0.041</td><td>0.007</td><td>0.063</td></tr><tr><td rowspan="4">Yahoo(A1-R20)</td><td>F1</td><td>0.067</td><td>0.065</td><td>0.277</td><td>0.106</td><td>0.098</td><td>0.678</td></tr><tr><td>F1-PA</td><td>0.259</td><td>0.426</td><td>0.695</td><td>0.106</td><td>0.185</td><td>0.895</td></tr><tr><td>AUROC</td><td>0.367</td><td>0.394</td><td>0.668</td><td>0.198</td><td>0.525</td><td>0.971</td></tr><tr><td>AUPRC</td><td>0.056</td><td>0.057</td><td>0.161</td><td>0.067</td><td>0.048</td><td>0.637</td></tr><tr><td rowspan="4">Yahoo(A1-R55)</td><td>F1</td><td>0.366</td><td>0.446</td><td>0.281</td><td>0.059</td><td>0.010</td><td>0.633</td></tr><tr><td>F1-PA</td><td>0.424</td><td>0.446</td><td>0.320</td><td>0.059</td><td>0.010</td><td>0.744</td></tr><tr><td>AUROC</td><td>0.916</td><td>0.877</td><td>0.867</td><td>0.875</td><td>0.478</td><td>0.958</td></tr><tr><td>AUPRC</td><td>0.303</td><td>0.242</td><td>0.177</td><td>0.019</td><td>0.002</td><td>0.624</td></tr></table>

Table 1: Comparison with the existing baselines. All results are based on five independent trials. This table reports the average of five trials for each metrics. Complete results with confidence intervals are reported in the supplementary.

Moreover, we compared our method to the anomaly transformer (AT), one of the state-of-the-art methods. While AT shows comparable performance in terms of F1-PA, it falls short regarding the F1 score, AUROC, and AUPRC. This disparity arises because the anomaly transformer generates positive predictions at certain intervals rather than specifying the exact moments of anomalous points. Details of test-time anomaly scores of baselines are reported in supplementary.

Analysis on ROC and Precision-Recall curves. Our method consistently outperforms previous approaches in terms of AUROC across all datasets except for SMD (M-1-4), and AUPRC across all datasets except for WADI and Creditcard. This indicates that previous off-the-shelf baselines are sensitive to threshold settings, which poses a challenge for robustness in real-world scenarios where finding an optimal threshold is difficult. Fig. 5 shows a visualization of the receiver operating curve (ROC curve) and precision-recall curve of our approach, along with baselines. Consistently, for both, our approach (red) improves the off-the-shelf classifier results (blue) significantly.

![](images/3a92120e01f2febb9cba58f5c0b0680e574b5c91c9c023d401810cc2fe24a1b8.jpg)  
Figure 5: ROC curves (left) Precision-Recall curves (right) visualizations of baselines and MLP+Ours.

## Results on AnoShift Benchmark

The AnoShift benchmark (Dragoi et al. 2022) offers a testbed for the robustness of anomaly detection algorithm under distribution shift problem. The dataset spans a decade, partitioned into a training set covering the period 2006-2010, and two distinct test sets denoted as NEAR (2011-2013) and FAR (2014-2015). Visualized in Fig. 6-(a), the data distribution progressively deviates from the train set as time progresses.

The principal objective of evaluation on the AnoShift benchmark is to investigate the effectiveness of our proposed algorithm against such distribution shifts. The evaluation entails three metrics—namely, Area Under the Receiver Operating Characteristic curve (AUROC), Area Under the Precision-Recall Curve with inliers as the positive class (AUPRC-in), and Area Under the Precision-Recall Curve with outliers as the positive class (AUPRC-out), following previous work (Dragoi et al. 2022). The performance of our method is compared to other deep-learning-based baselines, including SO-GAAL (Liu et al. 2020), deepSVDD (Ruff et al. 2018), LUNAR (Goodge et al. 2022), ICL (Shenkar and Wolf 2022), BERT (Devlin et al. 2019) for anomalies.

Table 2 demonstrates a significant improvement in performance when our method is integrated into an MLP-based autoencoder, as evidenced by an increase in AUROC of up to 0.216. Despite its simplicity, our approach markedly augments the baseline MLP performance, which previously showed inferior performance. This improvement is especially significant in FAR splits, which entail a severe distribution shift problem compared to NEAR splits. While our experiments focused on MLP, it’s worth noting that our module can be seamlessly added to other baselines.

![](images/f2d6461600aee416fa0d4895a089f1dbad3f009ddc43b7e856c334023074b493.jpg)  
Figure 6: (a) T-SNE plot according to chronological distance and (b) performance increase with respect to three different evaluation metrics: AUROC, AUPRC-in and AUPRC-out.

<table><tr><td rowspan="2">Method</td><td colspan="3">NEAR</td><td colspan="3">FAR</td></tr><tr><td>ROC</td><td>PRC (in)</td><td>PRC (out)</td><td>ROC</td><td>PRC (in)</td><td>PRC (out)</td></tr><tr><td> $SO-GAAL^†$ </td><td>0.545</td><td>0.435</td><td>0.877</td><td>0.493</td><td>0.107</td><td>0.927</td></tr><tr><td> $deepSVDD^†$ </td><td>0.870</td><td>0.717</td><td>0.942</td><td>0.345</td><td>0.100</td><td>0.823</td></tr><tr><td> $LUNAR^†$ </td><td>0.490</td><td>0.294</td><td>0.809</td><td>0.282</td><td>0.093</td><td>0.794</td></tr><tr><td> $ICL^†$ </td><td>0.523</td><td>0.273</td><td>0.819</td><td>0.225</td><td>0.088</td><td>0.775</td></tr><tr><td> $BERT^†$ </td><td>0.861</td><td>0.589</td><td>0.960</td><td>0.281</td><td>0.082</td><td>0.784</td></tr><tr><td> $MLP^†$ </td><td>0.441</td><td>0.262</td><td>0.730</td><td>0.200</td><td>0.085</td><td>0.757</td></tr><tr><td>MLP</td><td>0.441</td><td>0.207</td><td>0.776</td><td>0.208</td><td>0.085</td><td>0.758</td></tr><tr><td>MLP+Ours</td><td>0.639(+0.194)</td><td>0.404(+0.197)</td><td>0.841(+0.065)</td><td>0.424(+0.216)</td><td>0.259(+0.173)</td><td>0.838(+0.081)</td></tr></table>

Table 2: Performance on Anoshift benchmark. † denotes that metrics are reported from the results in the original paper. AUROC and AUPRC are denoted as ROC and PRC.

## Ablation Study

As shown in Table 3, we perform the ablation study on our method to analyze the effectiveness of each component. MLP with detrend module and test-time adaptation with the model update is consistently showing better results, compared to the cases when used alone (MLP+DT, MLP+TTA) and none of them used (MLP). Here, DT and TTA denote a detrend module and test-time adaptation with model updates, respectively. Moreover, Fig. 7 also demonstrates that when the appropriate threshold is selected MLP model with our full method consistently outperforms these baselines, including the best performance of the off-the-shelf MLP model.

<table><tr><td rowspan="2">DT</td><td rowspan="2">TTA</td><td colspan="4">SWaT</td><td colspan="4">SMD (M-2-1)</td><td colspan="4">MSL (P-15)</td></tr><tr><td>F1</td><td>F1-PA</td><td>AUROC</td><td>AUPRC</td><td>F1</td><td>F1-PA</td><td>AUROC</td><td>AUPRC</td><td>F1</td><td>F1-PA</td><td>AUROC</td><td>AUPRC</td></tr><tr><td>X</td><td>X</td><td>0.765</td><td>0.834</td><td>0.832</td><td>0.722</td><td>0.236</td><td>0.814</td><td>0.674</td><td>0.190</td><td>0.263</td><td>0.848</td><td>0.645</td><td>0.061</td></tr><tr><td>√</td><td>X</td><td>0.762</td><td>0.837</td><td>0.846</td><td>0.738</td><td>0.234</td><td>0.855</td><td>0.749</td><td>0.205</td><td>0.221</td><td>0.703</td><td>0.799</td><td>0.124</td></tr><tr><td>X</td><td>√</td><td>0.784</td><td>0.907</td><td>0.888</td><td>0.778</td><td>0.239</td><td>0.881</td><td>0.689</td><td>0.204</td><td>0.019</td><td>0.027</td><td>0.640</td><td>0.060</td></tr><tr><td>√</td><td>√</td><td>0.784</td><td>0.903</td><td>0.892</td><td>0.780</td><td>0.249</td><td>0.974</td><td>0.764</td><td>0.280</td><td>0.440</td><td>0.944</td><td>0.801</td><td>0.575</td></tr></table>

Table 3: Ablation study on our proposed method. DT and TTA indicate a detrend module and test-time adaptation, respectively.

![](images/de0b6908acbab4df81a61333790c94f72f4912801cde7968a893f0cbbac52782.jpg)  
Figure 7: F1 scores according to various thresholds.

![](images/5ed5af9d36a0e9e6a0bdca36360bae477c8e8050c2158d3d85a2f52780d0e983.jpg)  
(a) Reconstruction Results of MSL (P-15)  
(b) ROC Curve  
Figure 8: Ablation study on the proposed method using the MSL (P-15) dataset.

This behavior can be further described in Fig. 8-(a), illustrating those four options at once. (1) Our approach (red) shows better reconstruction compared to off-the-shelf MLP (blue). The off-the-shelf MLP model is constantly generating reconstruction errors even after the transition of an overall trend, which results in many false positive cases. (2) Also, the detrend module alone fails to detect anomalies, showing less sensitivity compared to our approach, although they share the same EMA parameter γ. This shows model update can contribute to such sensitivity of the anomaly detector, as it keeps updating with recent observations. (3) Without proper update of such trend estimate, test-time adaptation with model updates alone (green) can harm the robustness of the model, as it can be overfitted to sequence before trend shift, with a lack of ability to adapt to newly coming sequences.

## Discussion and Limitation

Threshold for Anomaly Detection. Existing unsupervised time-series anomaly detection studies (Audibert et al. 2020; Xu et al. 2022) have a major limitation in that they determine the threshold for normality by inferring the entire test data and selecting it based on the best performance. However, this approach is not practically feasible in real-world scenarios. Therefore, we report AUROC to evaluate overall performance and decide the threshold based on the training data statistics in our experiments. We posit that the performance of the anomaly detector could be further enhanced with an appropriate choice of threshold.

Inconsistent Labeling in Anomaly Detection. In the timeseries anomaly detection task, the criteria of anomaly vary for each scenario, making it difficult to establish consistent labels. For this reason, distinguishing whether test samples with significant differences from the normal in train sets are abnormal or normal with distribution shifts is challenging. In our case, based on the assumption that there are more normal instances in test sets, we employ trend estimation and model predictions for test-time adaptation. To improve the adaptation performance, employing active learning (Ren et al. 2021) where human annotators provide labels for a subset of test data can be a valuable research direction.

## Conclusion

In this work, we highlighted the distribution shift problem in unsupervised time-series anomaly detection. We have shown that the concept of normality may change over time. This can be a significant challenge for designing robust time-series anomaly detection frameworks, leading to many false positives, which harms the system’s consistency. To mitigate this issue, we propose a simple yet effective strategy of incorporating new normals into the model architecture, by following trend estimates along with test-time adaptation. Concretely, our method consistently outperforms standard baselines for real-world benchmarks with such problems.

## Acknowledgements

This work was supported by the Institute of Information & communications Technology Planning & Evaluation (IITP) grant funded by the Korea government (MSIT) (No.2019-0-00075, Artificial Intelligence Graduate School Program (KAIST)) and by the National Research Foundation of Korea (NRF) grant funded by the Korea government (MSIT) (No. NRF-2022R1A2B5B02001913 & No. 2022R1A5A708390812).

## References

Abdulaal, A.; Liu, Z.; and Lancewicki, T. 2021. Practical Approach to Asynchronous Multivariate Time Series Anomaly Detection and Localization. In Proc. the ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD).

Audibert, J.; Michiardi, P.; Guyard, F.; Marti, S.; and Zuluaga, M. A. 2020. USAD: UnSupervised Anomaly Detection on Multivariate Time Series. In Proc. the ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD).

Breunig, M. M.; Kriegel, H.; Ng, R. T.; and Sander, J. 2000. LOF: Identifying Density-Based Local Outliers. In Proceedings ofthe 2000 ACM SIGMOD International Conference on Management of Data, May 16-18, 2000, Dallas, Texas, USA. Cao, T.; Zhu, J.; and Pang, G. 2023. Anomaly Detection under Distribution Shift. CoRR, abs/2303.13845.

Choi, S.; Yang, S.; Choi, S.; and Yun, S. 2022. Improving test-time adaptation via shift-agnostic weight regularization and nearest source prototypes. In Proc. of the European Conference on Computer Vision (ECCV), 440–458. Springer.

Devlin, J.; Chang, M.; Lee, K.; and Toutanova, K. 2019. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. In Burstein, J.; Doran, C.; and Solorio, T., eds., Proc. ofThe Annual Conference ofthe North American Chapter ofthe Associationfor Computational Linguistics (NAACL).

Dragoi, M.; Burceanu, E.; Haller, E.; Manolache, A.; and Brad, F. 2022. AnoShift: A Distribution Shift Benchmark for Unsupervised Anomaly Detection. In NeurIPS.

Ganin, Y.; Ustinova, E.; Ajakan, H.; Germain, P.; Larochelle, H.; Laviolette, F.; Marchand, M.; and Lempitsky, V. 2016. Domain-adversarial training of neural networks. The journal ofmachine learning research, 17(1): 2096–2030.

Geiger, A.; Liu, D.; Alnegheimish, S.; Cuesta-Infante, A.; and Veeramachaneni, K. 2020. TadGAN: Time Series Anomaly Detection Using Generative Adversarial Networks. In 2020 IEEE International Conference on Big Data (IEEE BigData 2020), Atlanta, GA, USA, December 10-13, 2020, 33–43. IEEE.

Goodge, A.; Hooi, B.; Ng, S.; and Ng, W. S. 2022. LUNAR: Unifying Local Outlier Detection Methods via Graph Neural Networks. In Proc. the AAAI Conference on Artificial Intelligence (AAAI).

Gulrajani, I.; and Lopez-Paz, D. 2021. In Search of Lost Domain Generalization. In Proc. the International Conference on Learning Representations (ICLR).

Han, C.; Rundo, L.; Murao, K.; Noguchi, T.; Shimahara, Y.; Milacski, Z. Á.; Koshino, S.; Sala, E.; Nakayama, H.; and Satoh, S. 2021. MADGAN: unsupervised medical anomaly detection GAN using multiple adjacent brain MRI slice reconstruction. BMC Bioinform., 22-S(2): 31.

Hundman, K.; Constantinou, V.; Laporte, C.; Colwell, I.; and Söderström, T. 2018. Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding. In Proc. the ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD).

Kim, S.; Choi, K.; Choi, H.; Lee, B.; and Yoon, S. 2022a. Towards a Rigorous Evaluation of Time-Series Anomaly Detection. In Proc. the AAAI Conference on Artificial Intelligence (AAAI).

Kim, T.; Kim, J.; Tae, Y.; Park, C.; Choi, J.; and Choo, J. 2022b. Reversible Instance Normalization for Accurate Time-Series Forecasting against Distribution Shift. In Proc. the International Conference on Learning Representations (ICLR).

Lai, K.; Zha, D.; Xu, J.; Zhao, Y.; Wang, G.; and Hu, X. 2021. Revisiting Time Series Outlier Detection: Definitions and Benchmarks. In Proc. the Advances in Neural Information Processing Systems (NeurIPS).

Liang, J.; Hu, D.; and Feng, J. 2020. Do we really need to access the source data? source hypothesis transfer for unsupervised domain adaptation. In International Conference on Machine Learning, 6028–6039. PMLR.

Liu, L.; Liu, D.; and Peng, Y. 2016. Detection and identification of sensor anomaly for aerospace applications. In 2016 Annual Reliability and Maintainability Symposium (RAMS), 1–6. IEEE.

Liu, Y.; Li, Z.; Zhou, C.; Jiang, Y.; Sun, J.; Wang, M.; and He, X. 2020. Generative Adversarial Active Learning for Unsupervised Outlier Detection. IEEE Trans. Knowl. Data Eng., 32(8): 1517–1528.

Liu, Y.; Wu, H.; Wang, J.; and Long, M. 2022. Non-stationary Transformers: Exploring the Stationarity in Time Series Forecasting. In NeurIPS.

Malhotra, P.; Ramakrishnan, A.; Anand, G.; Vig, L.; Agarwal, P.; and Shroff, G. 2016. LSTM-based Encoder-Decoder for Multi-sensor Anomaly Detection. CoRR, abs/1607.00148.

Mathur, A. P.; and Tippenhauer, N. O. 2016. SWaT: a water treatment testbed for research and training on ICS security. In 2016 International Workshop on Cyber-physical Systems for Smart Water Networks, CySWater@CPSWeek 2016, Vienna, Austria, April 11, 2016.

Muth, J. F. 1960. Optimal properties of exponentially weighted forecasts. Journal ofthe american statistical association, 55(290): 299–306.

Niu, S.; Wu, J.; Zhang, Y.; Chen, Y.; Zheng, S.; Zhao, P.; and Tan, M. 2022. Efficient test-time model adaptation without forgetting. In Proc. the International Conference on Machine Learning (ICML), 16888–16905. PMLR.

Pang, G.; Shen, C.; Cao, L.; and van den Hengel, A. 2022. Deep Learning for Anomaly Detection: A Review. ACM Comput. Surv., 54(2): 38:1–38:38.

Park, D.; Hoshi, Y.; and Kemp, C. C. 2018. A Multimodal Anomaly Detector for Robot-Assisted Feeding Using an LSTM-Based Variational Autoencoder. IEEE Robotics Autom. Lett.

Pena, E. H. M.; de Assis, M. V. O.; and Jr., M. L. P. 2013. Anomaly Detection Using Forecasting Methods ARIMA and HWDS. In 32nd International Conference of the Chilean Computer Science Society, SCCC 2013, Temuco, Cautin, Chile, November 11-15, 2013, 63–66. IEEE Computer Society.

Quinonero-Candela, J.; Sugiyama, M.; Schwaighofer, A.; and Lawrence, N. D. 2008. Dataset shift in machine learning. Mit Press.

Rassam, M. A.; Maarof, M. A.; and Zainal, A. 2018. A distributed anomaly detection model for wireless sensor networks based on the one-class principal component classifier. Int. J. Sens. Networks, 27(3): 200–214.

Ren, P.; Xiao, Y.; Chang, X.; Huang, P.-Y.; Li, Z.; Gupta, B. B.; Chen, X.; and Wang, X. 2021. A survey of deep active learning. ACM computing surveys (CSUR), 54(9): 1–40.

Ruff, L.; Görnitz, N.; Deecke, L.; Siddiqui, S. A.; Vandermeulen, R. A.; Binder, A.; Müller, E.; and Kloft, M. 2018. Deep One-Class Classification. In Proc. the International Conference on Machine Learning (ICML).

Ruff, L.; Kauffmann, J. R.; Vandermeulen, R. A.; Montavon, G.; Samek, W.; Kloft, M.; Dietterich, T. G.; and Müller, K. 2021. A Unifying Review of Deep and Shallow Anomaly Detection. Proc. IEEE, 109(5): 756–795.

Saito, T.; and Rehmsmeier, M. 2015. The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. PloS one, 10(3): e0118432.

Sankararaman, A.; Narayanaswamy, B.; Singh, V. Y.; and Song, Z. 2022. FITNESS: (Fine Tune on New and Similar Samples) to detect anomalies in streams with drift and outliers. In Proc. the International Conference on Machine Learning (ICML).

Saurav, S.; Malhotra, P.; TV, V.; Gugulothu, N.; Vig, L.; Agarwal, P.; and Shroff, G. 2018. Online anomaly detection with concept drift adaptation using recurrent neural networks. In Proceedings of the ACM India Joint International Conference on Data Science and Management of Data, COMAD/CODS 2018, Goa, India, January 11-13, 2018.

Schlegl, T.; Seeböck, P.; Waldstein, S. M.; Schmidt-Erfurth, U.; and Langs, G. 2017. Unsupervised Anomaly Detection with Generative Adversarial Networks to Guide Marker Discovery. In Information Processing in Medical Imaging - 25th International Conference, IPMI 2017, Boone, NC, USA, June 25-30, 2017, Proceedings, volume 10265 of Lecture Notes in Computer Science, 146–157. Springer.

Schölkopf, B.; Williamson, R. C.; Smola, A. J.; Shawe-Taylor, J.; and Platt, J. C. 1999. Support Vector Method for Novelty Detection. In Solla, S. A.; Leen, T. K.; and Müller, K., eds., Proc. the Advances in Neural Information Processing Systems (NeurIPS).

Shen, L.; Li, Z.; and Kwok, J. T. 2020. Timeseries Anomaly Detection using Temporal Hierarchical One-Class Network. In Proc. the Advances in Neural Information Processing Systems (NeurIPS).

Shenkar, T.; and Wolf, L. 2022. Anomaly Detection for Tabular Data with Internal Contrastive Learning. In Proc. the International Conference on Learning Representations (ICLR).

Shin, Y.; Lee, S.; Tariq, S.; Lee, M. S.; Jung, O.; Chung, D.; and Woo, S. S. 2020. ITAD: Integrative Tensor-based Anomaly Detection System for Reducing False Positives of

Satellite Systems. In Proc. the ACM Conference on Information and Knowledge Management (CIKM).

Shumway, R. H.; and Stoffer, D. S. 2017. Time series analysis and its applications: With R examples. Springer.

Sørbø, S.; and Ruocco, M. 2023. Navigating the Metric Maze: A Taxonomy of Evaluation Metrics for Anomaly Detection in Time Series. CoRR, abs/2303.01272.

Su, Y.; Zhao, Y.; Niu, C.; Liu, R.; Sun, W.; and Pei, D. 2019. Robust Anomaly Detection for Multivariate Time Series through Stochastic Recurrent Neural Network. In Proc. the ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD).

Sun, Y.; Wang, X.; Liu, Z.; Miller, J.; Efros, A. A.; and Hardt, M. 2020. Test-Time Training with Self-Supervision for Generalization under Distribution Shifts. In Proc. the International Conference on Machine Learning (ICML).

Tax, D. M. J.; and Duin, R. P. W. 1999. Data domain description using support vectors. In 7th European Symposium on Artificial Neural Networks, ESANN 1999, Bruges, Belgium, April 21-23, 1999, Proceedings.

Wang, D.; Shelhamer, E.; Liu, S.; Olshausen, B. A.; and Darrell, T. 2021. Tent: Fully Test-Time Adaptation by Entropy Minimization. In Proc. the International Conference on Learning Representations (ICLR).

Wang, J.; Kuang, Q.; and Duan, S. 2015. A new online anomaly learning and detection for large-scale service of Internet of Thing. Pers. Ubiquitous Comput., 19(7): 1021– 1031.

Wang, Q.; Fink, O.; Gool, L. V.; and Dai, D. 2022. Continual Test-Time Domain Adaptation. In Proc. ofthe IEEE conference on computer vision and pattern recognition (CVPR).

Xu, H.; Chen, W.; Zhao, N.; Li, Z.; Bu, J.; Li, Z.; Liu, Y.; Zhao, Y.; Pei, D.; Feng, Y.; Chen, J.; Wang, Z.; and Qiao, H. 2018. Unsupervised Anomaly Detection via Variational Auto-Encoder for Seasonal KPIs in Web Applications. In Proc. the International Conference on World Wide Web (WWW).

Xu, J.; Wu, H.; Wang, J.; and Long, M. 2022. Anomaly Transformer: Time Series Anomaly Detection with Associa tion Discrepancy. In Proc. the International Conference on Learning Representations (ICLR).

Yoo, J.; Chung, I.; and Kwak, N. 2022. Unsupervised Domain Adaptation for One-Stage Object Detector Using Offsets to Bounding Box. In Proc. of the European Conference on Computer Vision (ECCV), 691–708. Springer.

Zinkevich, M. 2003. Online Convex Programming and Generalized Infinitesimal Gradient Ascent. In Proc. the International Conference on Machine Learning (ICML).

Zong, B.; Song, Q.; Min, M. R.; Cheng, W.; Lumezanu, C.; Cho, D.; and Chen, H. 2018. Deep Autoencoding Gaussian Mixture Model for Unsupervised Anomaly Detection. In Proc. the International Conference on Learning Representations (ICLR).

Zou, Y.; Yu, Z.; Kumar, B.; and Wang, J. 2018. Unsupervised domain adaptation for semantic segmentation via classbalanced self-training. In Proc. ofthe European Conference on Computer Vision (ECCV), 289–305.