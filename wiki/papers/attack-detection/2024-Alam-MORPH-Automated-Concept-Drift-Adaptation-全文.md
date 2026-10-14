---
title: "2024-Alam-MORPH-Automated-Concept-Drift-Adaptation"
date: 2026-10-14
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2024-Alam-MORPH-Automated-Concept-Drift-Adaptation.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# MORPH: Towards Automated Concept Drift Adaptation for Malware Detection

Md Tanvirul Alam<sup>1</sup>, Romy Fieblinger<sup>1</sup>, Ashim Mahara<sup>1</sup>, and Nidhi Rastogi<sup>1</sup>

Rochester Institute of Technology, Rochester NY 14623, USA<sup>1</sup> {ma8235, rf7344, am7539, nidhi.rastogi}@rit.edu

Abstract. Concept drift is a significant challenge for malware detection, as the performance of trained machine learning models degrades over time, rendering them impractical. While prior research in malware concept drift adaptation has primarily focused on active learning, which involves selecting representative samples to update the model, self-training has emerged as a promising approach to mitigate concept drift. Selftraining involves retraining the model using pseudo labels to adapt to shifting data distributions. In this research, we propose MORPH – an efective pseudo-label-based concept drift adaptation method specifically designed for neural networks. Through extensive experimental analysis of Android and Windows malware datasets, we demonstrate the eficacy of our approach in mitigating the impact of concept drift. Our method ofers the advantage of reducing annotation eforts when combined with active learning. Furthermore, our method significantly improves over existing works in automated concept drift adaptation for malware detection.

Keywords: Malware Detection · Concept Drift · Neural Networks · Semi-Supervised Learning · Self-Training.

## 1 Introduction

Malware threats continue to evolve and pose a critical challenge to cyber defenses, requiring security experts to develop adaptable solutions for automated analysis and identification of malicious patterns. However, the efectiveness of these approaches depends on the statistical similarities between the trained defense models and the real-world data. Concept drift refers to a shift in the underlying distribution of the testing dataset that deviates from the training dataset (existing defense model). In the context of malware detection, this manifests in several ways, such as new malware variants emerging with malicious features or deliberate attempts by adversaries to evade existing detection methods [17]. The impact of concept drift can be far-reaching. Features that were earlier indicative of malware may become obsolete, leading to increased misclassification, false positives, or the overlooking of new threats [15,13]. It can deteriorate the efectiveness of defense models, rendering them impractical for further use [12]. It is crucial to note that concept drift is not a one-time event, and it requires continuous attention. Neglecting it may progressively impact defenses, creating a false sense of security just before a devastating cyberattack [17,7].

Prior research has addressed the onset of concept drift in various ways [14]. While periodically retraining the models using the latest annotation dataset is an efective solution, obtaining suficient high-quality annotated datasets for malware detection is often impractical [24,46]. Due to these limitations, active learning has emerged as a widely adopted method for combating concept drift [28]. The process of active learning selects a subset of representative samples from recent data, considering the challenges in labeling large volumes of data. The core idea is to choose samples the model is least confident about or those that “deviate significantly from known data distribution” [17,9]. Malware researchers then annotate these selected samples to ensure high-quality labels. As the model shows uncertainty towards these samples, they contribute significantly to adapting the decision boundary rapidly to the shifting data distribution. However, active learning methods still rely on the frequent availability of high-quality annotations, which can be costly to obtain [28]. To further alleviate the annotation efort, a model is retrained using “pseudo labels” [21,33] i.e., predictions made by the model itself. This approach, called weak supervision or self-training, although not extensively researched for malware detection, is emerging as a promising direction. We pursue these approaches in this paper.

Notable prior works in automated concept drift adaptation for malware detection include DroidEvolver [47] and its updated version, DroidEvolver++ [19], both designed specifically for Android malware classification. DroidEvolver[47] maintains a pool of five classification models and utilizes the ensemble prediction as the pseudo-label to identify aging models that deviate from the ensemble. Subsequently, these models are retrained to align with the ensemble model. However, both these models face several challenges. Firstly, they rely on linear models, which can struggle with the high-dimensional, non-linear malware data distribution. Secondly, the performance of ensemble models degrades rapidly due to self-poisoning [19], where incorrect pseudo-labels reinforce errors, leading to suboptimal adaptations.

Main Contribution. In this paper, we present MORPH (autoMated cOncept dRift adaPtation algoritHm), a novel self-training neural networkbased model for concept drift adaption in malware detection. Our approach leverages pseudo-labels to update the model, reducing the frequent need for active learning updates. While pseudo-labels may introduce noise, they provide a significant advantage: the ability to utilize unlabeled data and adjust the model’s decision boundaries accordingly [21]. However, the inherent challenges of malware datasets require a specific pseudo-label sample selection strategy, which we introduce in this research work. Our approach uses both labeled and pseudo-labeled data for semi-supervised learning within the neural network. Furthermore, we investigate the efectiveness of combining pseudo-labels with active learning to enhance concept drift adaptation and improve malware detection performance. Specifically, we address the following key research questions (RQ) in this study:

1. RQ1: Can pseudo-labeling alone enable automatic concept drift adaptation in neural network-based malware detection?

![](images/1a8896161c4a6615c5ceda76f84f23c170ab68d2519cb7cf9614cc603c74ea28.jpg)

![](images/4ca85e70bfefaa777b2a332e5decad5b5f0caa279033600b29c08b718f3dbfac.jpg)  
Fig. 1: Kernel Density Estimate [11] plot for probability distribution on Ember dataset [5] for correctly & incorrectly classified samples in Windows (left) and Android (right) application data.

To address this question, we evaluate the efectiveness of pseudo-labels for capturing and adapting to evolving malware patterns without ground truth labels.

2. RQ2: To what extent can pseudo-label-based adaptation reduce the frequency of annotation in active learning?

To explore this question, we quantify the reduction in annotation requirements by comparing the performance of the pseudo-label-based adaptation algorithm with traditional active learning approaches.

3. RQ3: How does our pseudo-label-based approach with neural networks compare to prior automated concept drift adaptation methods?

To investigate, we benchmark our model performance against DroidEvolver [47] and DroidEvolver++ [19] to demonstrate the eficacy of the proposed neural network-based method.

We experimentally assess the eficacy of our approach on two benchmark malware detection datasets- an Android malware dataset [12] and a Windows malware dataset [5]. Our rigorous experiments analyze the performance of our proposed approach on diference metrics, F1 score, False Positive Rate (FPR), and False Negative Rate (FNR). Our approach and subsequent findings contribute insights into the eficacy of using pseudo-labels and active learning for efective concept drift adaptation in malware detection.

## 2 Motivation

Concept drift presents a significant challenge in malware detection, where the underlying data distribution is continuously evolving due to new malware families and malware variants being written frequently. Supervised learning-based malware detection models rely on malware application-labeled data for training, requiring extensive manual annotation eforts for both application and features (such as malicious behavior, code patterns, malware origin, and threat level)[3,31,2] to keep the detection model up-to-date. However, this approach is time-consuming and expensive since getting the latest malware files for training is not always practical. It is relatively easier to collect unlabeled application datasets than labeled ones for malware detection since manual annotation of malware requires significant efort from an expert [24]. Therefore, pseudo-labeling can be an efective method in these situations as it leverages unlabeled data for semi-supervised learning [21] when the labeled dataset available is small.

![](images/a4874e2b1713c49afd5d51e58b295f55a6eaeea9d5923f1f4f8e8b318c149358.jpg)  
Fig. 2: Gradual adaptation to distribution shift for a binary classifier. The solid line represents the original classifier and the dotted lines represent the adapted classifier trained with pseudo-labels.

Research shows that a neural network’s predictions are more confident for correctly classified samples than incorrectly classified ones [39]. We illustrate this in Figure 1, which displays the softmax probability distribution plot for a malware classifier trained on a neural network using Android and Windows malware datasets. The correctly classified samples generally exhibit higher probabilities than the incorrect ones. However, there are instances where incorrect predictions can also have high confidence. This phenomenon arises from the lack of proper calibration in neural network predictions, which causes the output probabilities from a softmax layer to deviate from the true probabilities for model prediction [33]. So, even highly confident model predictions can sometimes be incorrect, leading to undetected malware. Despite this calibration issue, neural networks often demonstrate some degree of robustness to label noise. Wu et al. [46] have explored the application of semi-supervised learning to address the problem of ‘noisy labels’ in malware detection. They modified a semi-supervised learning method designed initially for image classification [38] and then demonstrated semi-supervised learning in mitigating the impact of noisy labels. However, further research on utilizing pseudo-labels to adapt neural networks-based malware detection models to concept drift is crucial.

In a similar vein, self-training has been shown useful in gradual domain adaptation scenarios, especially where the data distribution undergoes gradual changes over time (such as malware data) [20]. This phenomenon is efectively represented in Figure 2. When we directly apply the source model to the target domain, as illustrated at time step t=3, its performance deteriorates, resulting in a random classifier due to the increasing mismatch between the source and target distributions. However, By gradually updating the model at intermediate steps, we can incorporate correctly classified pseudo labels into the training process, enabling the model to adjust its decision boundary in response to the evolving target domain. The iterative nature of self-training in concept drift allows the model to continuously refine its decision boundaries, enhancing its performance on the evolving target domain. By incorporating additional labeled samples obtained through active learning at regular intervals, the model can actively adapt to the changing data distribution. This motivates using active learning [12] with self-training for efectively addressing concept drift. Previous studies on adapting to malware concept drift have investigated active learning [12,9] or pseudolabeling [47,19] separately. However, we are the first to explore the combination of these techniques in mitigating concept drift.

## 3 Background and Related Work

Concept Drift. Concept drift refers to the phenomenon where the statistical properties of a target domain unpredictably shift [22], posing a critical challenge to machine learning models used in malware detection. Concept drift can manifest in multiple ways, including changes in feature distributions $( \mathrm { e . g . }$ , new APIs) [49], class distributions $( \mathrm { e . g . }$ , new malware families) [49], and even class definitions $( \mathrm { e . g . }$ , evolving criteria for malicious behavior) [22,19]. As the statistical properties of the target domain evolve, the model’s performance can gradually deteriorate, rendering it unsuitable for accurate detection. In the malware domain, concept drift arises due to multiple reasons. When Android releases a major app update, it introduces new features and shifts distributions [45]. A significant culprit is the adversaries actively attempting to evade detection [1,6] by manipulating their software to trick detectors, leading to increased false negatives and a weakened defense system [1,6,28,19].

Pseudo-labeling. Also called self-training, pseudo-labeling is a semi-supervised learning technique in which a security expert can assign malware labels to unlabeled application data based on malware detection model predictions. Mathematically, pseudo-labeling is defined as follows:

Let $\mathbf { \mathcal { D } } = \{ ( \mathbf { x } _ { i } , y _ { i } ) \} _ { i = 1 } ^ { N _ { l } }$ be the labeled dataset, where $\mathbf { x } _ { i }$ represents the input sample and $y _ { i }$ denotes its corresponding true label. Additionally, let $\mathcal { U } = \{ \mathbf { x } _ { j } \} _ { j = 1 } ^ { N _ { u } }$ be the unlabeled dataset, where $N _ { l }$ and $N _ { u }$ are the numbers of labeled and unlabeled samples, respectively.

Given a neural network model $f ( \mathbf { x } ; \theta )$ parameterized by θ, the model’s predictions for the unlabeled samples can be computed as $\hat { y } _ { j } = f ( \mathbf { x } _ { j } ; \theta )$

Pseudo-labeling involves selecting a threshold τ to assign labels to the unlabeled samples based on the model’s confidence in its predictions. The pseudolabel $\tilde { y } _ { j }$ for an unlabeled sample $\mathbf { x } _ { j }$ is defined as:

$$
\tilde {y} _ {j} = \left\{ \begin{array}{l l} \arg \max _ {k} \hat {y} _ {j} ^ {(k)}, & \text { if } \max _ {k} \hat {y} _ {j} ^ {(k)} \geq \tau \\ \text { unlabeled }, & \text { otherwise } \end{array} \right.
$$

where $\hat { y } _ { j } ^ { ( k ) }$ denotes the predicted probability of the k-th class for the unlabeled sample $\mathbf { x } _ { j }$ . If the maximum predicted probability exceeds the threshold $\tau ,$ the sample is assigned the label corresponding to the class with the highest probability. Otherwise, the sample remains unlabeled. By incorporating these pseudo-labels into the training process, the semi-supervised learning algorithm can jointly optimize the model parameters θ using both the labeled and pseudolabeled samples.

Semi-Supervised Learning (SSL). It is halfway between supervised and unsupervised learning, where it utilizes both labeled data and unlabeled data for model training [10]. The goal is to improve model accuracy beyond what is achievable with labeled data only by leveraging the unlabeled data to help the model distinguish the decision boundary between diferent classes. SSL works under several key assumptions [27]:

1. If two data points in a high-density region are close, their corresponding output should also be close. Conversely, two points separated by a lowdensity region should have outputs that are distant from each other.

2. Data points belonging to the same cluster are likely to belong to the same class, implying that the decision boundary should lie in low-density regions.

3. The high-dimensional feature lies in a relatively low-dimensional manifold, enabling extraction of a low-dimensional representation through the use of unlabeled data to learn the simplified task.

Prior work has used various SSL methods, such as consistency regularization, proxy labels, and generative models [43,48]. Santos et al. used SSL to reduce the labeling efort required for malware detection from static features by 50% [35]. Mahdavifar et al. [23] used semi-supervised learning with neural networks for malware category classification. MORSE, a deep neural network-based approach, leveraged SSL to learn from noisy labels of malware families [46].

Active Learning. It aims to maximize the performance of a machine learning model by strategically selecting a minimal number of data samples for manual annotations, thereby minimizing labeling cost [32]. It chooses samples that the model is most uncertain about [8]. For instance, a binary classification task, like malware detection, might involve prioritizing data points with a posterior probability closest to 0.5 since they have the potential to improve the model’s performance more than randomly selected data points. There are three major approaches for sample selection in active learning: uncertainty-based, diversitybased, and expected model change. The uncertainty-based approach defines and measures uncertainties of new data points, selecting the least confident ones for annotation [18,41]. The diversity-based approach focuses on selecting data points that better represent the overall distribution of unlabeled samples [26,36]. Lastly, the expected model change approach selects samples that would have the most significant impact on the current model parameters [34].

While active learning is relatively understudied in the context of malware detection, uncertainty sampling has emerged as the prevalent popular approach. Equivalently, this can be viewed as a form of out-of-distribution (OOD) sample selection, targeting data samples with the highest uncertainty scores. Prediction confidence is a commonly used baseline for OOD sample selection. However, since the model’s predicted probabilities may not accurately reflect its confidence, the predictions require calibration [16]. Transcend [17], a parametric statistical framework for assessing model uncertainty and identifying potential concept drift through nonconformity measures, leverages two metrics, namely model confidence, and credibility, to reject test samples that may have experienced drift. Transcendent [9] improves upon Transcend by refining the framework and introducing two new conformal evaluators, significantly reducing computational overhead. However, both Transcend [17] and Transcendent [9] assume that data distributions remain stationary within certain time windows. This assumption might not always hold in real-world scenarios where drift can occur gradually or in more complex patterns.

![](images/f0d8678cd159a09103938b51b786cdc3083010f8e4de9f2dbd95944b8a282b58.jpg)  
Fig. 3: Proposed concept drift adaptation algorithm, MORPH

## 4 Proposed Methodology

Figure 3 presents MORPH, our methodology for adapting to concept drift in malware detection. Our approach deploys a continual learning neural network model, initially trained on labeled samples. Since it is crucial to retrain at regular intervals, and while existing work has explored optimal timing, our work focuses on a simplified scenario for simplicity. Following Chen et al. [12], we retrain the model monthly using new samples, generating pseudo-labels from the model predictions on unlabeled data. Our novel sample-selection algorithm then chooses malware and benign samples for inclusion in the training process, and the model is retrained via semi-supervised learning, leveraging both original labeled and pseudo-labeled data.

## 4.1 Sample Selection Algorithm

The unique threat of concept drift in malware classification is its bias towards false negatives, where malware instances are erroneously classified as benign. This is a consequence of, for example, malware authors actively attempting to evade existing detection methods, resulting in significant variations between newer and older malware characteristics. As a result, when a model predicts a new sample as malware, the likelihood of being correct is higher due to the relatively low occurrence of false positives. Therefore, even predictions with low confidence tend to be accurate. Conversely, low-confidence predictions are more likely to be incorrect in the case of benign predictions. This phenomenon is illustrated on the left half of Figure 4, where the malware predictions (true positives) have a broader probability distribution compared to benign predictions (true negatives). This suggests that low-confidence malware classifications are likely accurate due to the rarity of false positives. Similarly, the right side of Figure 4 further reveals that drifted malware samples, which deviate from the training data, exhibit even broader distributions. These observations emphasize the importance of treating benign and malware samples and their associated pseudo-labels diferently.

![](images/2f95c24622d5206ae25aaa1f4cf614a7acf2cc4dcb9c88a20f7e56175035c5e7.jpg)  
Fig. 4: Kernel Density Estimate [11] plot for probability distribution on Andro-Zoo [4] dataset for (left) True Positive and True Negative sample and (right) drifted vs not-drifted malware samples

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1: MORPH: Pseudo-labeling Algorithm

Input : Test samples
Output: Pseudo-labeled malware and benign samples

1 Calculate model's prediction on test samples
2  $D_{M} \leftarrow$  samples predicted as malware
3  $D_{B} \leftarrow$  samples predicted as benign
4 Select  $N_{M}$  samples randomly from  $D_{M}$  with probability  $&gt;\tau_{m}$ 
5 Select top  $N_{M}$  samples with highest confidence from  $D_{B}$  with probability  $&gt;\tau_{b}$ 
6 Return the pseudo-labeled malware and benign samples selected
</div>

To build on this insight, we propose a targeted pseudo-label strategy. For predicted malware, we prioritize incorporating uncertain instances into training. This exposure allows the model to adapt to emerging threats and evolving malware characteristics. Conversely, for predicted benign samples, we prioritize high-confidence predictions to minimize erroneous inclusions. Through this asymmetry, we efectively address the unique complexities of concept drift in malware detection.

Algorithm 1 outlines the steps involved in the sample selection algorithm. In Step 1, the algorithm predicts the model’s labels for the unlabeled test data. Based on these predicted probabilities, pseudo-labeled samples are generated. In

<table><tr><td rowspan="2">Dataset</td><td colspan="3"># Months</td><td colspan="3">Benign Apps</td><td colspan="3">Malicious Apps</td></tr><tr><td>Train</td><td>Dev</td><td>Test</td><td>Train</td><td>Dev</td><td>Test</td><td>Train</td><td>Dev</td><td>Test</td></tr><tr><td>AndroZoo</td><td>12</td><td>6</td><td>18</td><td>40947</td><td>18109</td><td>30797</td><td>4542</td><td>2028</td><td>3631</td></tr><tr><td>Ember</td><td>1</td><td>1</td><td>22</td><td>17180</td><td>32820</td><td>650000</td><td>32761</td><td>27239</td><td>730904</td></tr></table>

Table 1: Summary of AndroZoo and Ember datasets

Step 2, a selected number, $N _ { M }$ , of samples is chosen from the predicted malware samples, using a probability threshold, $\tau _ { m }$ . The value of $N _ { M }$ can be adjusted as a hyperparameter to control the utilization of unlabeled data, especially in the case of large datasets. Similarly, in Step ${ \mathcal { B } } ,$ an equal number of samples are selected from the predicted benign samples, but with a diferent confidence threshold, $\tau _ { b } .$ , where $\tau _ { m }$ is smaller than $\tau _ { b } .$ . In Step $^ { 4 , }$ we randomly sample pseudolabeled malware samples as long as they are above $\tau _ { m } ,$ , ensuring drifted samples are included. However, in Step 5, for benign samples, the algorithm prioritizes the selection of the most confidently predicted instances. Finally, in Step $\delta ,$ the hyperparameter $\tau _ { b }$ may be omitted when a significantly higher number of samples are predicted as benign compared to malware. This is often the case in malware datasets due to the larger proportion of benign applications in the wild [17]. By sampling an equal number of malware and benign samples, the value of $\tau _ { b }$ approaches 1, efectively diminishing the inclusion of false negative samples during the training phase.

## 4.2 Semi-Supervised Training

After the sample detector identifies relevant instances, we leverage semi-supervised learning to retrain the model by combining both ground truth and pseudolabeled samples. To achieve this, we form mini-batches comprising an equal number of original ground truth data and pseudo-labeled data. During training, the objective function balances two losses:

$$
L = L _ {s} + \lambda L _ {u}
$$

Here, $L _ { s }$ represents the standard supervised loss for the manually annotated samples, while $L _ { u }$ represents the loss for the pseudo-labeled samples. The hyperparameter $\lambda$ controls the relative contribution of each loss. During the training phase, we select an equal number of samples from the labeled and unlabeled data, ensuring that one sample from each dataset is seen during one epoch of training on the labeled data. Based on empirical observation, we set λ to 1.

## 5 Datasets

We employ two distinct datasets– AndroZoo [4] and EMBER [5], to experimentally evaluate our approach, MORPH, for concept drift in malware detection on

Android and Windows platforms. The AndroZoo dataset is a comprehensive collection of Android applications, including millions of APKs analyzed by multiple AntiVirus products to identify malware. On the other hand, EMBER is a labeled benchmark dataset used for training machine learning models to statically detect malicious Windows portable executable files, with features extracted from over a million binary files. The summaries of these two datasets are presented in Table 1 and further details are provided below.

## 5.1 Android dataset

This dataset was introduced by Chen et al. [12] and is derived from AndroZoo [4]. It consists of Android applications spanning three years from 2019 to 2021 and consists of 16,978 binary features indicating diferent API usage. Each application in the dataset has over 20 types of metadata, such as VirusTotal reports. We use the data from the first year to construct our training dataset, while the data from the first month of 2018 serves as the validation dataset. The data from the remaining 23 months, spanning the second and third years, is set aside for the testing. The training dataset comprises 121 malware families, whereas the test datasets from 2020 and 2021 include 82 and 51 families, respectively.

## 5.2 Windows Dataset

We use the EMBER dataset for Windows PE malware detection [5]. This dataset ofers features extracted from each file using the LIEF project [40]. Each file is characterized by a 2381-dimensional feature vector that encapsulates various aspects of the executable file: byte-level sequences, imported functions, and header information. We make use of the features from the years 2017 and 2018. We train our model using data from the first month of 2017, while data from the second month of 2017 is used for validation. The remaining 22 months of data are used for testing. The 2018 samples in the dataset were deliberately selected for their classification dificulty, leading to the expectation of bad performance from the model trained on earlier data during the test month. During our experiments, we standardize the feature set using the Scikit-learn StandardScaler.

## 6 Experiments and Results

## 6.1 Experimental Settings

In our experimental setup, we conducted training and validation using two distinct datasets: AndroZoo [4] for Android applications and Ember [5] for Windows applications. For the AndroZoo dataset, we trained our model using the first 12 months of available data. However, due to the larger size of the Ember dataset and its nearly equal proportion of malware and benign samples, we trained the model using only the first month of training data from Ember [5].

Our baseline classifier is a multilayer perceptron that takes input features of dimension 2381 for the EMBER and 16,978 for the AndroZoo. The hidden layer dimensions are 512-384-256-128. We fine-tuned the batch size, learning rate, dropout rate, and training epochs separately for each dataset using their respective validation sets to optimize the model’s performance.

Following the training phase, we evaluated the model’s performance on the remaining test data. We measured the F1 score, False Positive Rate (FPR), and False Negative Rate (FNR) for each test month. Instead of training from scratch each month, we performed fine-tuning to adapt the model to concept drift. Importantly, we retained the original training data during each test month. This approach served two purposes: firstly, it helped mitigate the potential impact of self-poisoning [19] by using high-quality ground truth annotations for the selected samples, and secondly, it prevented catastrophic forgetting that may occur when removing the knowledge of the initial malware samples [30].

We identified the optimal value for $\tau _ { m }$ using the AndroZoo dataset since we noticed a more severe drift in the dataset, resulting in poorer model performance. We use the first six months of data for this, following the approach in [12], which used the same dataset for optimizing parameters for the active learning algorithm. We use the obtained $\tau _ { m } = 0 . 6$ for AndroZoo and EMBER to prevent overfitting on a separate dataset. As mentioned in Section 4.1, we can omit the parameter $\tau _ { b }$ as more samples are predicted as benign due to a more significant proportion of benign samples and the presence of more false negatives in the test dataset.

## 6.2 Utility of Pseudo Labels

The performance of our proposed method is shown in Figure 6 and Figure 5 for the Ember and AndroZoo datasets, respectively. For the Ember dataset [5], we observe a significant performance drop in test month 11, which corresponds to data from January 2018. This decline was expected, as the data collected in 2018 presented more significant challenges for the classification model, as noted in [5]. However, our proposed method efectively recovers performance in the subsequent months, as evidenced by improved F1-score and lower false negative rate (FNR). Similarly, for the AndroZoo dataset, our adaptation method outperforms the baseline neural network following significant drift. We can efectively incorporate drifted samples into the model by leveraging semi-supervised learning. While we observe a slight self-poisoning efect towards the end, our proposed method demonstrates greater robustness than prior work, as discussed in Section 6.4, as the onset of such poisoning efects is significantly delayed.

Overall, our proposed method yields substantial improvements over the baseline neural network. On average, we achieve a 4.07% increase in F1-score for the AndroZoo dataset and a 0.83% increase for the Ember dataset. Moreover, the false negative rate is reduced by 14.78% and 5.74% for the AndroZoo and Ember [5] datasets, respectively.

## We arrive at the following conclusions for our RQ1

1. Pseudo labels generated by neural networks can provide suficient information for concept drift adaptation for malware detection.

![](images/b49087dca3ae9a59d3919c29b43060a416a7859ec477063f3822bc7a1330c86a.jpg)

![](images/24aa568fcdca08503c8ad226aa5f0c98809a8fdf5b9ebb333e8b563762d0748b.jpg)

![](images/6a18bad921f57655aa430a0de4cc900a957818dad597563e125bdac24a542eec.jpg)  
Fig. 5: F1 score (left), FNR (middle), and FPR (right) for test months on AndroZoo dataset with MORPH and baseline (Static) neural network.

![](images/28a16b271cef54e8b6c01be926d65913a820c6374db512383f285955bc9840e8.jpg)

![](images/1eba2bc0626cb334a128b17316431c5a8c1a8791084c70edaf3602088dda630c.jpg)

![](images/1e7ea256f63da4ad6289e2594887c06c582920a504d080c51efb139922438e43.jpg)  
Fig. 6: F1 score (left), FNR (middle), and FPR (right) for test months on Ember dataset with MORPH and baseline (Static) neural network.

2. As the drift becomes more severe, pseudo labels can provide more benefits to improve model performance.

Impact of Varying Known Malware Families To illustrate our second conclusion further, we investigate the impact of varying the number of known malware families in the Ember dataset [5] on the performance of our concept drift adaptation algorithm. Specifically, we explore the efect of selecting samples exclusively from the top-k most frequent malware families for the training data while retaining all samples in the test data. By limiting the training data to samples from a subset of the most prevalent malware families, we simulate a scenario where the model has limited exposure to diverse malware patterns during training.

We show the results in Figure 7. When the training data contains smaller malware families, the test data exhibits a noticeable concept drift for the malware class. As a result, the model’s performance sufers, leading to high false negative rates and reduced overall F1 score. However, our adaptation algorithm efectively mitigates the impact of concept drift. By incorporating the selected samples from the limited set of malware families into the training process, the algorithm adapts the model to the changing malware patterns present in the test data. We observe improvements in the model’s performance as it becomes more adept at detecting and classifying malware instances despite the evolving nature of the malware families. We notice a significant improvement in the F1 score (e.g., 36.6% for five malware families). However, this naturally leads to a larger FPR, especially in the later months compared to the baseline model.

![](images/b0fc1b339e3905586456db0fea0c78e40cf0c49abd7ae5ee8f5910948b2d7b86.jpg)

![](images/4475d0121de27cea7601e14650ff0c05b971f20cd73b6894caba6d50c82c6608.jpg)

![](images/aeae31e14906a47fe9d6e5e8ebc731e5a455ac5cdca48333f1fd17fc8706851b.jpg)  
Fig. 7: F1-score (left), FNR (center), and FPR(right) for test months on Ember dataset [5] with (Adapted) and without (Static) concept drift adaptation method as the number of families in the training dataset is varied. The number in the legend indicates the number of malware families in the training dataset.

![](images/8aa3f6bb34b476dbb7fb00b5e738b124042bb78507ad39869743fbaf49a53b77.jpg)

![](images/6431879ecbdce30ba64c38b61c8190b56a26fbe46a76b5792e3edb577ebfa11a.jpg)

![](images/0fbffc9743e401b6000e70c94b0261a74ad495f0ae241ea76602324842ba8a45.jpg)  
Fig. 8: F1-score (left), FNR (middle), and FPR (right) as active learning (AL) is combined with MORPH. AL: only active learning is applied each month, MORPH+AL: Active learning and MORPH are applied every other month.

## 6.3 Combination with Active Learning

To address our research question RQ2, we conducted experiments that combined the proposed method with active learning. Specifically, we sampled the most uncertain predictions (i.e., lowest probability output from the softmax layer) for active learning annotations. The number of annotated samples depended on the available human efort for this task. Ideally, we would prefer to simulate a scenario where samples arrive daily, which would closely resemble real-world conditions [42]. However, since our data is only available at a monthly granularity, we performed active learning at specific month intervals. During the active learning process, we first selected samples from the test data that required annotation and then added them to the training data with their annotated ground truth labels.

We show the result in 8 as we reduce the active learning updates and replace them with pseudo-label updates. For active learning updates, we annotate 100 samples per month. We then replace the active learning update with MORPHbased update updates when simulating the efect when both are used in tandem. This efectively reduces the number of active learning updates by 50%. The result suggests the model can retain comparable performance with regular active learning updates, even when we periodically replace them with pseudo-labelbased updates.

![](images/af377505456d83bf2031a3ec966a773b3272e7436594925c79124f70bb06e9ed.jpg)

![](images/d18a1f44e8c5de874b28c3493f4747a4fe55cea13a77bcdc45a2129666a30b34.jpg)

![](images/49749d734d2520f4dbd40c6fe32150e0645fc0a3699f3f04d7fb2fc84ce20dc8.jpg)  
Fig. 9: F1 score (left), FNR (middle), and FPR(right) for Hi-Enc (Hierarchical Contrastive Learning) [12] active learning with MORPH updates. The numbers in brackets indicate the amount of labeled samples used for active learning updates each month.

Utility of Unlabeled Data: We conduct additional experiments to assess the efectiveness of our proposed algorithm in conjunction with state-of-the-art neural networks and active learning methods. Specifically, we adopt the approach introduced by Chen et al. [12] and treat the unannotated samples after active learning update as unlabeled data. Subsequently, we employed MORPH to update the model using monthly pseudo-labels assigned to these unlabeled samples. With successive active learning and semi-supervised updates each month, we expect the model to be able to adjust to both sudden and gradual shifts in data distribution. The results, depicted in Figure 9 for the AndroZoo dataset, demonstrate that MORPH consistently enhances performance by leveraging the unlabeled samples instead of only performing active learning updates. When using a 100 annotation budget for active learning, MORPH improves the F1 score by 3.46%. It is important to consider that the AndroZoo dataset typically consists of 300 or fewer malware samples each month. Thus, we anticipate even more promising outcomes as the number of unlabeled malware samples increases in the dataset.

## We arrive at the following conclusions for our RQ2

1. MORPH can reduce the number of active learning updates required to maintain stable model performance.

2. Active learning can mitigate the efect of self-poisoning introduced by noisy pseudo labels.

3. MORPH can be used with other active learning methods to improve model performance.

## 6.4 Comparison With DroidEvolver++

DroidEvolver [47] and its updated version, DroidEvolver++ [19], are significant prior works in automated malware concept drift adaptation. These methods operate by maintaining a set of models and adapting to changes in data distribution as the model pool evolves. However, comparing our approach with DroidEvolver is challenging due to the diferent model architectures used. Nonetheless, we compare our experimental results with the DE model update using pseudo labels.

![](images/e946579a1db9fef62f740e99b17730c29585a59f39e6eba601ff6b5dbe83d0bd.jpg)

![](images/3cd2536c49eb7961fb09efb13d55191542cc7926b78c6a6a5f069f14c59a6a20.jpg)

![](images/8a010ed40e685cffe2eceb90ecc1d23c88e1828a2255d125cc81a806bdbee410.jpg)  
Fig. 10: F1 score (left), FNR (middle), and FPR(right) for DE++ ensemble model with and without model updates, compared against MORPH.

DroidEvolver utilizes an ensemble of five linear online learning models. The ensemble is trained using an initial dataset of labeled malware and goodware. During testing, DroidEvolver aggregates the predictions of the underlying models using a weighted sum of decision scores as the ensemble decision function. Predictions of individual models that deviate from the ensemble predictions are excluded. The model is then retrained using samples that difer from the ensemble prediction, treating the ensemble prediction as the ground truth annotation. Further details about DE++ can be found in the original paper by Kan et al. [19]. Figure 10 shows the result for DE++ performance, with and without model updates. The linear models do not perform well as concept drift settles in, and the ensemble-based model update further deteriorates their performance by 2.65% F1 score. On average, DE++ achieves a 23.3% F1 score, whereas our method achieves a significantly higher F1 score of 53.8%.

We arrive at the following conclusions regarding our RQ3:

1. Neural networks are more robust to concept drift than linear online learning models or an ensemble of such models.

2. Our proposed method is more robust to self-poisoning than a pseudo-labelbased algorithm applied to an ensemble of linear classifiers.

## 7 Discussion

## 7.1 Diference in Datasets

Our results demonstrate that the impact of concept drift is less severe in the Windows dataset. Even when introducing concept drift by limiting the number of malware families in the training dataset, MORPH can adapt to the new distribution. The primary reason for this is the scale of the dataset. The total number of introduced malware samples in each test month is much smaller in AndroZoo [4] compared to the EMBER dataset [5], approximately 100 times smaller. The large number of malware samples in the EMBER dataset [5] allows for more variations of each new malware family to be included. As a result, the model can correctly predict some of these variations, even when encountering an entirely new family. However, in AndroZoo [4], the model will likely fail to accurately identify any samples from a new malware family, resulting in their exclusion from the training phase. The number of samples for diferent families in the training set is significantly lower in AndroZoo [4], with only 45 of 122 families having at least five samples. This indicates that AndroZoo [4] has a relatively higher number of samples from new families during testing, leading to a higher degree of concept drift, as observed in our experimental results.

## 7.2 Feasibility of Complete Automation

While MORPH shows promising results, fully automated concept drift adaptation is not always possible. When a new malware family exhibits behavior that significantly difers from the samples in the training set, adapting to these samples without manual annotation may not be feasible. This is because we need at least some of these samples to be correctly pseudo-labeled to incorporate them in the training with accurate annotation. It can also violate the gradual drift assumption discussed in Section 2. Active learning becomes the only viable approach to identify and include these samples in the training data with the appropriate ground truth annotation.

## 7.3 Need for Better Features

Using API usage-based features for malware detection presents a significant drawback: adversaries can evade detection by incorporating spurious API usage into their malicious code. These shortcomings of malware detection based on static analysis have been studied extensively in prior literature [25,1]. One potential avenue for future research in this direction involves leveraging Transformerbased [44] models to learn features directly from the source code [29,37]. By focusing on the behavioral aspects rather than relying solely on API usage, detection can become more efective and resistant to concept drifts.

## 8 Conclusion

This research addresses the critical challenge of concept drift in malware detection, where trained models struggle with evolving threats. We propose a novel self-training approach utilizing pseudo-labels on a neural network-based malware classifier, achieving automatic adaptation and significantly reducing annotation demands compared to traditional active learning. Our method outperforms existing works, efectively handling diverse malware landscapes on both Android and Windows datasets. However, fully automating adaptation might not always be feasible for significantly diferent malware families. To address this, future research can explore features like behavioral patterns and Transformer-based models for enhanced robustness and efectiveness against evolving threats. Finally, this research paves the way for next-generation malware detection systems capable of continuous adaptation and protection against emerging dangers.

## References

1. Aghakhani, H., Gritti, F., Mecca, F., Lindorfer, M., Ortolani, S., Balzarotti, D., Vigna, G., Kruegel, C.: When malware is packin’heat; limits of machine learning classifiers based on static analysis features. In: Network and Distributed Systems Security (NDSS) Symposium 2020 (2020)

2. Alam, M.T., Bhusal, D., Park, Y., Rastogi, N.: Cyner: A python library for cybersecurity named entity recognition. arXiv preprint arXiv:2204.05754 (2022)

3. Alam, M.T., Bhusal, D., Park, Y., Rastogi, N.: Looking beyond iocs: Automatically extracting attack patterns from external cti. In: Proceedings of the 26th International Symposium on Research in Attacks, Intrusions and Defenses. pp. 92–108 (2023)

4. Allix, K., Bissyand´e, T.F., Klein, J., Le Traon, Y.: Androzoo: Collecting millions of android apps for the research community. In: Proceedings of the 13th International Conference on Mining Software Repositories. pp. 468–471. MSR ’16, ACM, New York, NY, USA (2016). https://doi.org/10.1145/2901739.2903508, http://doi. acm.org/10.1145/2901739.2903508

5. Anderson, H.S., Roth, P.: EMBER: An Open Dataset for Training Static PE Malware Machine Learning Models. ArXiv e-prints (Apr 2018)

6. Anderson, H.S., Kharkar, A., Filar, B., Evans, D., Roth, P.: Learning to evade static pe machine learning malware models via reinforcement learning. arXiv preprint arXiv:1801.08917 (2018)

7. Andresini, G., Pendlebury, F., Pierazzi, F., Loglisci, C., Appice, A., Cavallaro, L.: Insomnia: towards concept-drift robustness in network intrusion detection. In: Proceedings of the 14th ACM workshop on artificial intelligence and security. pp. 111–122 (2021)

8. Atlas, L., Cohn, D., Ladner, R.: Training connectionist networks with queries and selective sampling. Advances in neural information processing systems 2 (1989)

9. Barbero, F., Pendlebury, F., Pierazzi, F., Cavallaro, L.: Transcending transcend: Revisiting malware classification in the presence of concept drift. In: 2022 IEEE Symposium on Security and Privacy (SP). pp. 805–823. IEEE (2022)

10. Chapelle, O., Scholkopf, B., Zien, A.: Semi-supervised learning (chapelle, o. et al., eds.; 2006)[book reviews]. IEEE Transactions on Neural Networks 20(3), 542–542 (2009)

11. Chen, Y.C.: A tutorial on kernel density estimation and recent advances. Biostatistics & Epidemiology 1(1), 161–187 (2017)

12. Chen, Y., Ding, Z., Wagner, D.A.: Continuous learning for android malware detection. In: Calandrino, J.A., Troncoso, C. (eds.) 32nd USENIX Security Symposium, USENIX Security 2023, Anaheim, CA, USA, August 9-11, 2023. pp. 1127–1144. USENIX Association (2023), https://www.usenix.org/conference/ usenixsecurity23/presentation/chen-yizheng

13. Chen, Y., Wang, S., She, D., Jana, S.: On training robust pdf malware classifiers. In: Proceedings of the 29th USENIX Conference on Security Symposium. pp. 2343– 2360 (2020)

14. Gama, J., Zliobait˙e, I., Bifet, A., Pechenizkiy, M., Bouchachia, A.: A survey on <sup>ˇ</sup> concept drift adaptation. ACM computing surveys (CSUR) 46(4), 1–37 (2014)

15. Garcia-Teodoro, P., Diaz-Verdejo, J., Maci´a-Fern´andez, G., V´azquez, E.: Anomalybased network intrusion detection: Techniques, systems and challenges. computers & security 28(1-2), 18–28 (2009)

16. Guo, C., Pleiss, G., Sun, Y., Weinberger, K.Q.: On calibration of modern neural networks. In: International conference on machine learning. pp. 1321–1330. PMLR (2017)

17. Jordaney, R., Sharad, K., Dash, S.K., Wang, Z., Papini, D., Nouretdinov, I., Cavallaro, L.: Transcend: Detecting concept drift in malware classification models. In: 26th USENIX security symposium (USENIX security 17). pp. 625–642 (2017)

18. Joshi, A.J., Porikli, F., Papanikolopoulos, N.: Multi-class active learning for image classification. In: 2009 IEEE conference on computer vision and pattern recognition. pp. 2372–2379. IEEE (2009)

19. Kan, Z., Pendlebury, F., Pierazzi, F., Cavallaro, L.: Investigating labelless drift adaptation for malware detection. In: Proceedings of the 14th ACM Workshop on Artificial Intelligence and Security. pp. 123–134 (2021)

20. Kumar, A., Ma, T., Liang, P.: Understanding self-training for gradual domain adaptation. In: International Conference on Machine Learning. pp. 5468–5479. PMLR (2020)

21. Lee, D.H., et al.: Pseudo-label: The simple and eficient semi-supervised learning method for deep neural networks. In: Workshop on challenges in representation learning, ICML. vol. 3, p. 896. Atlanta (2013)

22. Lu, N., Zhang, G., Lu, J.: Concept drift detection via competence models. Artificial Intelligence 209, 11–28 (2014)

23. Mahdavifar, S., Kadir, A.F.A., Fatemi, R., Alhadidi, D., Ghorbani, A.A.: Dynamic android malware category classification using semi-supervised deep learning. In: 2020 IEEE Intl Conf on Dependable, Autonomic and Secure Computing, Intl Conf on Pervasive Intelligence and Computing, Intl Conf on Cloud and Big Data Computing, Intl Conf on Cyber Science and Technology Congress (DASC/PiCom/CBDCom/CyberSciTech). pp. 515–522. IEEE (2020)

24. Mohaisen, A., Alrawi, O.: Av-meter: An evaluation of antivirus scans and labels. In: Detection of Intrusions and Malware, and Vulnerability Assessment: 11th International Conference, DIMVA 2014, Egham, UK, July 10-11, 2014. Proceedings 11. pp. 112–131. Springer (2014)

25. Moser, A., Kruegel, C., Kirda, E.: Limits of static analysis for malware detection. In: Twenty-third annual computer security applications conference (ACSAC 2007). pp. 421–430. IEEE (2007)

26. Nguyen, H.T., Smeulders, A.: Active learning using pre-clustering. In: Proceedings of the twenty-first international conference on Machine learning. p. 79 (2004)

27. Ouali, Y., Hudelot, C., Tami, M.: An overview of deep semi-supervised learning. arXiv preprint arXiv:2006.05278 (2020)

28. Pendlebury, F., Pierazzi, F., Jordaney, R., Kinder, J., Cavallaro, L., et al.: Tesseract: Eliminating experimental bias in malware classification across space and time. In: Proceedings of the 28th USENIX Security Symposium. pp. 729–746. USENIX Association (2019)

29. Rahali, A., Akhloufi, M.A.: Malbert: Malware detection using bidirectional encoder representations from transformers. In: 2021 IEEE International Conference on Systems, Man, and Cybernetics (SMC). pp. 3226–3231. IEEE (2021)

30. Rahman, M.S., Coull, S., Wright, M.: On the limitations of continual learning for malware classification. In: Conference on Lifelong Learning Agents. pp. 564–582. PMLR (2022)

31. Rastogi, N., Dutta, S., Gittens, A., Zaki, M.J., Aggarwal, C.: Tinker: A framework for open source cyberthreat intelligence. In: 2022 IEEE International Conference on Trust, Security and Privacy in Computing and Communications (TrustCom). pp. 1569–1574. IEEE (2022)

32. Ren, P., Xiao, Y., Chang, X., Huang, P.Y., Li, Z., Gupta, B.B., Chen, X., Wang, X.: A survey of deep active learning. ACM computing surveys (CSUR) 54(9), 1–40 (2021)

33. Rizve, M.N., Duarte, K., Rawat, Y.S., Shah, M.: In defense of pseudo-labeling: An uncertainty-aware pseudo-label selection framework for semi-supervised learning. arXiv preprint arXiv:2101.06329 (2021)

34. Roy, N., McCallum, A.: Toward optimal active learning through monte carlo estimation of error reduction. ICML, Williamstown 2, 441–448 (2001)

35. Santos, I., Nieves, J., Bringas, P.G.: Semi-supervised learning for unknown malware detection. In: International Symposium on Distributed Computing and Artificial Intelligence. pp. 415–422. Springer (2011)

36. Sener, O., Savarese, S.: Active learning for convolutional neural networks: A coreset approach. arXiv preprint arXiv:1708.00489 (2017)

37. Seneviratne, S., Sharifdeen, R., Rasnayaka, S., Kasthuriarachchi, N.: Selfsupervised vision transformers for malware detection. IEEE Access 10, 103121– 103135 (2022)

38. Sohn, K., Berthelot, D., Carlini, N., Zhang, Z., Zhang, H., Rafel, C.A., Cubuk, E.D., Kurakin, A., Li, C.L.: Fixmatch: Simplifying semi-supervised learning with consistency and confidence. Advances in neural information processing systems 33, 596–608 (2020)

39. St˚ahl, N., Falkman, G., Karlsson, A., Mathiason, G.: Evaluation of uncertainty quantification in deep learning. In: International Conference on Information Processing and Management of Uncertainty in Knowledge-Based Systems. pp. 556– 568. Springer (2020)

40. Thomas, R.: Lief - library to instrument executable formats. https://lief.quarkslab.com/ (apr 2017)

41. Tong, S., Koller, D.: Support vector machine active learning with applications to text classification. Journal of machine learning research 2(Nov), 45–66 (2001)

42. Ugarte-Pedrero, X., Graziano, M., Balzarotti, D.: A close look at a daily dataset of malware samples. ACM Transactions on Privacy and Security (TOPS) 22(1), 1–30 (2019)

43. Van Engelen, J.E., Hoos, H.H.: A survey on semi-supervised learning. Machine learning 109(2), 373–440 (2020)

44. Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A.N., Kaiser, L., Polosukhin, I.: Attention is all you need. Advances in neural information processing systems 30 (2017)

45. Wikipedia: Android Version History (2023), https://en.wikipedia.org/wiki/ Android\_version\_history

46. Wu, X., Guo, W., Yan, J., Coskun, B., Xing, X.: From grim reality to practical solution: Malware classification in real-world noise. In: 2023 IEEE Symposium on Security and Privacy (SP). pp. 2602–2619. IEEE Computer Society (2023)

47. Xu, K., Li, Y., Deng, R., Chen, K., Xu, J.: Droidevolver: Self-evolving android malware detection system. In: 2019 IEEE European Symposium on Security and Privacy (EuroS&P). pp. 47–62. IEEE (2019)

48. Yang, X., Song, Z., King, I., Xu, Z.: A survey on deep semi-supervised learning. IEEE Transactions on Knowledge and Data Engineering (2022)

49. Zhang, X., Zhang, Y., Zhong, M., Ding, D., Cao, Y., Zhang, Y., Zhang, M., Yang, M.: Enhancing state-of-the-art classifiers with api semantics to detect evolved android malware. In: Proceedings of the 2020 ACM SIGSAC conference on computer and communications security. pp. 757–770 (2020)