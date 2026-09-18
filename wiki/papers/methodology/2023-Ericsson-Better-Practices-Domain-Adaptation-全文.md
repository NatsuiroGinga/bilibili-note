---
title: "2023-Ericsson-Better-Practices-Domain-Adaptation"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2023-Ericsson-Better-Practices-Domain-Adaptation.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Better Practices for Domain Adaptation

Linus Ericsson $^{1}$ Da Li $^{2}$ Timothy M. Hospedales $^{1,2}$

$^{1}$ University of Edinburgh

$^{2}$ Samsung AI Center Cambridge

## Abstract

Distribution shifts are all too common in real-world applications of machine learning. Domain adaptation (DA) aims to address this by providing various frameworks for adapting models to the deployment data without using labels. However, the domain shift scenario raises a second more subtle challenge: the difficulty of performing hyperparameter optimisation (HPO) for these adaptation algorithms without access to a labelled validation set. The unclear validation protocol for DA has led to bad practices in the literature, such as performing HPO using the target test labels when, in real-world scenarios, they are not available. This has resulted in over-optimism about DA research progress compared to reality. In this paper, we analyse the state of DA when using good evaluation practice, by benchmarking a suite of candidate validation criteria and using them to assess popular adaptation algorithms. We show that there are challenges across all three branches of domain adaptation methodology including Unsupervised Domain Adaptation (UDA), Source-Free Domain Adaptation (SFDA), and Test Time Adaptation (TTA). While the results show that realistically achievable performance is often worse than expected, they also show that using proper validation splits is beneficial, as well as showing that some previously unexplored validation metrics provide the best options to date. Altogether, our improved practices covering data, training, validation and hyperparameter optimisation form a new rigorous pipeline to improve benchmarking, and hence research progress, within this important field going forward.

## 1 Introduction

Supervised deep learning models achieve impressive results when training and testing data are identically distributed. However, perhaps the main failure mode of computer vision and pattern recognition systems in practice is due to the near-ubiquitous distribution shift between data curated for model training, and real-world data encountered during deployment $[6]$ . This distribution shift issue has motivated a tremendous amount of work in the area of unsupervised domain adaptation (UDA) $[6]$ . UDA methods aim to alleviate domain shift by collecting freely available unlabelled data during deployment to a target domain and adapting vision models based on this unlabelled data.

Hundreds of unsupervised adaptation algorithms have now been proposed based on various principles from distribution alignment $[23]$ , to domain adversarial learning $[10]$ and much more. However, without exception, a key challenge for every one of these algorithms is: how do we tune hyperparameters and conduct model selection? In conventional supervised learning, hyperparameters and model selection (stopping criteria) are handled systematically by maximising accuracy on a validation split of the training set. In unsupervised domain adaptation there is no such straightforward solution because the target domain has no labels with which to compute accuracy, and the source domain is not representative of the target domain.

Despite the importance of this issue—upon which any practical application of domain adaptation hinges—there has been relatively little systematic study of validation protocols and algorithms for UDA $[48, 7, 35]$ . Worse, a recent meta-review and re-evaluation of the domain adaptation literature found that most published code did not use consistent or fair model selection criteria $[26]$ , and furthermore when evaluated under consistent and fair model selection criteria most existing results can not be replicated [26]. This mini “replication crisis” in domain adaptation highlights the need for studying validation protocols for UDA, and for fair benchmarking to drive reliable progress.

The few existing fair model selection criteria for UDA are based on diverse intuitions such as simply applying UDA algorithm objectives on the validation split of the unlabelled target set, priors on the expected distribution of labels $[7, 35]$ , or relying on the validation accuracy in the source domain $[48]$ . However there is little first principles justification to pick among these reasonable intuitions, and there is little empirical evaluation to understand which are best, and how close they come to the performance of an oracle validator, which has been the basis of many reported results in the literature $[26]$ .

These challenges exist throughout the domain adaptation literature. They arise across all three popular branches of adaptation for recognition: Unsupervised Domain Adaptation (UDA) $[10, 39, 42]$ , Source-Free Domain Adaptation (SFDA) $[20, 47]$ and Test Time Adaptation (TTA) $[45, 22]$ . They also arise across different kinds of domain adaptive learning problems from classification $[10]$ to regression $[5]$ , dense prediction $[49]$ , and detection $[16]$ .

The lack of a clear validation criterion for DA is an obstacle to its practical application. As an example, AutoML is a field with great potential to automate machine learning tasks for real-world applications $[15]$ . But in order to automate anything (e.g. algorithm, hyperparameter, checkpoint selection), we need a metric to optimise. In the case of supervised learning, this metric is naturally validation performance on an unseen labelled set. However, the choice of metric is not straightforward for UDA/SFDA/TTA due to the lack of labels. A major contribution of this paper is to clarify what such an optimisation metric should be for domain adaptation, thereby laying the foundations that allow bringing AutoML to DA.

To address this issue, we conduct a large-scale benchmark of 10 domain adaptation algorithms with 15 different validation criteria and three DA settings (UDA, SFDA, TTA). We identify which DA validators can be applied to each setting, characterise the size of the challenge in each case in terms of the gap between practically achievable and best-case DA performance, and identify the best existing validators. We identify effective practices in terms of using validation splits to estimate target performance. We highlight the risk of adaptation failure in SFDA and TTA as a likely fatal blocker for deployment in practice as existing validators do not reliably prevent this. These results should drive future practice both in DA research – which should use these validators, rather than unrealistic oracle HPO; and in validator research – which should aim to develop validators which surpass the best that we report.

## 2 Related Work

## 2.1 Domain Adaptation

There are now too many domain adaptation algorithms to review here, and we refer the reader to good surveys such as $[6, 28]$ . Most deep UDA algorithms proceed by performing supervised learning on the source domain data, and some kind of unsupervised objective on the target domain data. Representative families of approach include objectives that penalise misalignment between the source and target domain feature distributions $[23]$ , train a domain classifier that can then be used adversarially to penalise distinguishable source and target domain features $[10]$ , or penalise deviation from a prior on the expected target label distribution $[37]$ . However, all algorithms have a number of hyperparameters, such as stopping iteration and strength of the weighting factor for supervised vs unsupervised loss components. How to set these hyperparameters is not clear given the lack of a labelled target domain validation set in UDA applications.

The long-established mainstream setting for unsupervised domain adaptation (UDA) assumes that source and target data are accessed simultaneously for training. Two related problem variants have more recently gained rapid popularity, namely source-free domain adaptation (SFDA) and Test Time Adaptation (TTA). SFDA refers to the condition where pre-trained source models should be adapted to the target data without revisiting the source data $[20]$ – for example, by unsupervised fine-tuning. TTA $[45, 40]$ similarly adapts a pre-trained model without access to the source data, but assumes that the test data arrives in mini-batches, providing the opportunity to adapt to each mini-batch before making decisions on their labels. The newer SFDA and TTA have both rapidly gained traction as being more "practical" in an era of pre-trained models $[3]$ . However, algorithms for both of these settings still have many hyperparameters (e.g., learning rate, number of iterations, regularisation strengths), and hence suffer from the lack of a clear validation protocol in a DA context. Most of the seminal studies in this area do not show valid HPO criteria in their papers or code.

## 2.2 Validation Approaches for DA

Comparatively few papers have systematically studied validation criteria for UDA, given the importance of this issue for its practical application. Typical solutions applied by UDA algorithm papers include: (1) Oracle risk. Many papers use the target test set for hyperparameter selection $[26]$ , which is obviously incorrect as it can not be used in real applications; (2) Source risk. Evaluating the adapted model on the source validation set is reasonable but may not be a good validation criterion due to domain shift between source and target domains; (3) Evaluating another UDA algorithm objective (such as InfoMax $[37]$ and MMD $[23]$ ) on an unlabelled validation split of the target set; (4) Validation domain. Use of a held-out labelled validation domain, as used in the VisDA challenge $[30]$ , is fair. However, this assumes multiple labelled domains, which may not be available in practice, and also raises additional questions of whether the optimal hyperparameters for the validation domain are representative of the optimal hyperparameters for the target domain.

Besides the above strategies, a few purpose-designed validation criteria have been proposed: Deep embedded validation (DEV) [48] weights the source validation risk by the probability that each sample belongs to the target domain. Meanwhile, Silhouette score [32], batch nuclear-norm minimisation (BNM) [7], and soft neighbourhood density (SND) [35] criteria boil down to evaluating the adapted models' posterior label distribution on the target domain under different notions of a prior for the expected target domain label distribution. Mean ensemble-based validation (ENS) [32] considers a linear combination of the above criteria. However, overall it is unclear which to prefer for DA.

## 2.3 Benchmarking Domain Adaptation

There have been two major benchmarking exercises in UDA. The VisDA competition challenge $[30]$ provides a labelled validation domain for model selection and hyperparameter optimisation (HPO). However, validation domains may not be available in practice – and if they are, they may not be representative of the target domain. Thus, the vast majority of research literature on UDA has not used this approach. A recent empirical evaluation $[26, 25]$ analysed the GitHub repositories of a number of UDA methods and found that: (1) In practice different methods used very different validation criteria for empirical evaluation, making published results incomparable with each other; (2) A large number of prior studies used the oracle risk as a validation criterion, meaning that their results are not representative of how well domain adaptation would work in reality using validation criteria that can be implemented in practice; (3) Variation in existing validation criteria was high compared to variation across adaptation algorithms, and none of them was strongly correlated with recognition performance. Our evaluation extends this early study but goes beyond it in considering all three major branches of DA research (UDA, SFDA, TTA), exploring a wider variety of validators, and demonstrating how validator performance can be improved through proper use of validation splits within the target domain.

![](images/57d557987df8abfe6f6c1923e0632d8ee262e73f5c0dc5d595c62d3e2d3f9b8f.jpg)  
Figure 1: How the source and target domains are split and how each split is used for (1) the source-only model (2) UDA adaptors, (3) SFDA adaptors and (4) TTA adaptors.

## 3 Background

## 3.1 Problem Setup

Unsupervised Domain Adaptation: In the UDA setup, one typically trains a model $f_{\theta}: X \mapsto Y$ on a labelled dataset, $D_{S} = \{x_{i}, y_{i}\}_{i=1}^{N_{S}}$ , consisting of data sampled from a source domain, $p_{S}$ . The goal is then to adapt $f_{\theta}$ using an unlabelled dataset, $D_{T} = \{x_{i}\}_{i=1}^{N_{T}}$ , sampled from a target domain, $p_{T}$ . The general learning objective to be minimised w.r.t. to $\theta$ can be simplified as follows,

$$
L (f _ {\pmb {\theta}}, \mathcal {D} _ {S}, \mathcal {D} _ {T}) = L _ {\mathrm{sup}} (f _ {\pmb {\theta}}, \mathcal {D} _ {S}) + L _ {\mathrm{da}} (f _ {\pmb {\theta}}, \mathcal {D} _ {S}, \mathcal {D} _ {T}),\tag{1}
$$

where $L_{\mathrm{sup}}(\cdot)$ could be cross-entropy loss for classification and mean square error for regression problems, and $L_{\mathrm{da}}(\cdot)$ is the adaptation loss, such as MMD [42], CORAL [39] and DANN [10] losses. Source-Free Domain Adaptation: The SFDA setting aims to adapt a pre-trained source domain model to the target domain, relaxing the assumption of joint occurrence of source and target domain data in UDA. So first, a source model will be optimized using source domain data: $\hat{\theta} = \arg\min_{\theta} L_{\mathrm{sup}}(f_{\theta}, \mathcal{D}_{S})$ . Then the trained source model $\hat{\theta}$ will be adapted to the target domain by

$$
\theta^ {*} = \underset {\hat {\theta}} {\arg \min} L _ {\text { sfda }} (f _ {\hat {\theta}}, \mathcal {D} _ {T}).\tag{2}
$$

where now $L_{sfda}$ is an unsupervised loss, such as clustering [47] or information maximization [20]. Test-Time Adaptation: Unlike SFDA, TTA assumes the batch-wise target domain data $X \sim D_{T}$ comes in a stream and adapts a pre-trained source model for each minibatch X as

$$
\theta^ {*} = \underset {\hat {\theta}} {\arg \min}   L _ {\mathrm{tta}}   (f _ {\hat {\theta}}, X),\tag{3}
$$

where $L_{tta}$ is commonly the unsupervised loss, such as self-supervised learning and entropy minimisation losses, which could be essentially similar to $L_{sfda}$ .

## 3.2 Model Selection

Due to the lack of target domain labels in the various domain adaptation settings we consider, the model selection process must proceed as follows. Given a set of candidate models, as configured by hyperparameters $h \in H$ , where H is the pool of hyperparameter sets, the best candidate model is selected based on its evaluation score, $d(f_{\theta}, \mathcal{D}_{V})^{1}$ , where $D_{V}$ is a validation dataset. The process can be formalised as

$$
\begin{array}{r l} & {\boldsymbol {h} ^ {*} = \underset {\boldsymbol {h}} {\arg \max} d (f _ {\boldsymbol {\theta} _ {h} ^ {*}}, \mathcal {D} _ {V}),} \\ {\mathrm{s.t.}} & {\boldsymbol {\theta} _ {h} ^ {*} = \underset {\boldsymbol {\theta}} {\arg \min} L (f _ {\boldsymbol {\theta}}, \mathcal {D} _ {S}, \mathcal {D} _ {T}; \boldsymbol {h}).} \end{array}\tag{4}
$$

Table 1: A summary of the adaptation algorithms considered

<table><tr><td></td><td>Algorithm</td><td>Approach</td></tr><tr><td rowspan="6">UDA</td><td>ATDOC [21]</td><td>Pseudo-labelling</td></tr><tr><td>BNM [7]</td><td>SVD loss</td></tr><tr><td>DANN [10]</td><td>Adversarial</td></tr><tr><td>MCC [17]</td><td>Information maximisation</td></tr><tr><td>MCD [36]</td><td>Classifier discrepancy</td></tr><tr><td>MMD [23]</td><td>Feature distance</td></tr><tr><td rowspan="3">SFDA</td><td>AAD [47]</td><td>Clustering</td></tr><tr><td>NRC [46]</td><td>Graph clustering</td></tr><tr><td>SHOT [20]</td><td>Information maximisation</td></tr><tr><td rowspan="2">TTA</td><td>SHOT [20]</td><td>Information maximisation</td></tr><tr><td>TENT [45]</td><td>Entropy minimisation</td></tr></table>

Table 2: A summary of the validators considered.

<table><tr><td>Criterion</td><td>Approach</td></tr><tr><td>RankMe [11]</td><td>Rank estimation</td></tr><tr><td>AMI [25, 32]</td><td>Cluster quality</td></tr><tr><td>ARI [31]</td><td>Cluster quality</td></tr><tr><td>V-Measure [33]</td><td>Cluster quality</td></tr><tr><td>FMI [9]</td><td>Cluster quality</td></tr><tr><td>Silhouette [25, 32]</td><td>Cluster quality</td></tr><tr><td>DBI [8]</td><td>Cluster quality</td></tr><tr><td>CHI [4]</td><td>Cluster quality</td></tr><tr><td>BNM [7]</td><td>Label prior</td></tr><tr><td>MMD [23]</td><td>Domain Alignment</td></tr><tr><td>CORAL [39]</td><td>Domain Alignment</td></tr><tr><td>SND [35]</td><td>Label prior</td></tr><tr><td>InfoMax [37]</td><td>Label prior</td></tr><tr><td>Entropy</td><td>Label prior</td></tr><tr><td>Source Accuracy</td><td>Source accuracy</td></tr></table>

However, two things in UDA complicate this process: 1) choice of the validation set $\mathcal{D}_V$ ; and 2) definition of the evaluation metric $d(\cdot, \cdot)$ when $\mathcal{D}_V = \{\boldsymbol{x}_i\}_{i=1}^{N_V}$ is an unlabelled set.

Several validators have been proposed in the literature, such as SND $[35]$ , BNM $[7]$ and DEV $[48]$ . Additionally, it is worth remarking that popular DA losses such as IM $[20]$ , and Entropy $[44, 24]$ , can also be used as validators. We explore a large number of validators in addition to these, including those based on domain alignment, like MMD $[42]$ and CORAL $[39]$ , clustering $[33]$ and feature matrix rank $[11]$ . The full list of validators we consider in shown Tab. 2 with full details in Appendix D.

## 4 Evaluation

Our evaluation extends the benchmark of $[26]$ . We make their setup more rigorous by splitting the target domain into train/val/test sets. Previous works often compute target performance on the same data that the algorithms adapt to or the same data that the validators use. This fails to properly measure generalisation performance as we will show later. Our splits and how we use them are detailed in Figure 1.

In order to compare different validation criteria, we train a large number of models across several datasets, algorithms and hyperparameter choices. We want the optimal validator to behave similarly to the target domain test performance of the corresponding algorithm. We measure the quality of each validator in two ways: 1) computing the Spearman rank correlation between validator scores and oracle test accuracy, 2) using the validator to select the best model for an algorithm/task pair and comparing the test performance of it against the best model as selected by the oracle.

Questions: Through the experimental evaluation below on three different settings, we aim to answer the following questions: (i) Are the validation criteria sufficiently good to drive HPO and model selection in UDA? We also extend this question to regression problems in Appendix A. (ii) What is the impact of validating on the training set versus an independent validation split? (iii) Are the observations still consistent when source data is absent during adaptation (SFDA), and when we must adapt to the test-set itself (TTA)?

## 4.1 Unsupervised Domain Adaptation

## 4.1.1 Setup. In this section we describe our evaluation procedure for UDA.

Datasets: We use a wide range of UDA benchmark datasets: MNIST-M [10] which consists of a domain shift from standard MNIST [19] to a modified version; The VisDA-2017 [29] dataset which contains train, validation and test domains — we consider the shifts train → validation and train → test; Office-31 [34] which consists of three domains: amazon, dslr and webcam; and Office-Home [43] with four domains: art, clipart, product and real. In total, we consider 21 different domain shifts.

Table 3: Comparison of validation criteria for model selection in UDA. Averages over all 21 domain transfers evaluated. We report (i) the target test performance for the top models selected by each validator, and (ii) the correlation coefficient between the validator scores and the test performance over all hyperparameters and checkpoints. The colour of a cell indicates whether that model/validator combination beats the source-only model (green) or not (red).

<table><tr><td></td><td>RankMe</td><td>AMI</td><td>ARI</td><td>V-Measure</td><td>FMI</td><td>Silhouette</td><td>DBI</td><td>CHI</td><td>BNM</td><td>MMD</td><td>CORAL</td><td>SND</td><td>IM</td><td>Entropy</td><td>Accuracy</td><td>Oracle</td></tr><tr><td>ATDOC</td><td>58.24</td><td>67.70</td><td>67.71</td><td>67.79</td><td>67.71</td><td>46.73</td><td>49.55</td><td>16.55</td><td>64.29</td><td>52.46</td><td>55.96</td><td>24.13</td><td>64.61</td><td>61.23</td><td>68.06</td><td>72.24</td></tr><tr><td>BNM</td><td>61.36</td><td>69.32</td><td>69.48</td><td>69.29</td><td>69.48</td><td>62.42</td><td>51.58</td><td>33.10</td><td>66.88</td><td>52.64</td><td>60.92</td><td>47.70</td><td>67.01</td><td>65.98</td><td>66.02</td><td>71.09</td></tr><tr><td>DANN</td><td>62.00</td><td>64.76</td><td>64.35</td><td>64.55</td><td>63.23</td><td>56.06</td><td>53.86</td><td>36.89</td><td>62.72</td><td>51.62</td><td>60.61</td><td>46.51</td><td>62.79</td><td>62.83</td><td>62.44</td><td>68.27</td></tr><tr><td>MCC</td><td>62.36</td><td>69.65</td><td>70.06</td><td>69.66</td><td>69.68</td><td>63.21</td><td>40.48</td><td>24.72</td><td>66.84</td><td>55.12</td><td>54.66</td><td>35.13</td><td>66.79</td><td>65.28</td><td>69.11</td><td>72.41</td></tr><tr><td>MCD</td><td>60.80</td><td>60.31</td><td>46.45</td><td>60.26</td><td>31.23</td><td>16.54</td><td>28.58</td><td>8.99</td><td>63.83</td><td>51.06</td><td>47.44</td><td>13.66</td><td>64.43</td><td>56.44</td><td>63.83</td><td>67.75</td></tr><tr><td>MMD</td><td>60.37</td><td>65.98</td><td>63.56</td><td>66.00</td><td>63.56</td><td>54.83</td><td>51.93</td><td>35.22</td><td>61.37</td><td>46.66</td><td>58.41</td><td>40.08</td><td>61.57</td><td>61.06</td><td>63.83</td><td>67.44</td></tr><tr><td>Avg.</td><td>60.86</td><td>66.29</td><td>63.60</td><td>66.26</td><td>60.81</td><td>49.96</td><td>46.00</td><td>25.91</td><td>64.32</td><td>51.59</td><td>56.33</td><td>34.54</td><td>64.53</td><td>62.14</td><td>65.55</td><td>69.87</td></tr><tr><td>Avg. Rank</td><td>8.50</td><td>3.33</td><td>3.92</td><td>3.00</td><td>4.42</td><td>11.00</td><td>12.33</td><td>15.00</td><td>6.00</td><td>11.33</td><td>10.33</td><td>14.00</td><td>5.17</td><td>7.33</td><td>4.33</td><td>-</td></tr><tr><td>Correlation</td><td>0.29</td><td>0.62</td><td>0.62</td><td>0.65</td><td>0.58</td><td>0.01</td><td>-0.40</td><td>-0.60</td><td>0.35</td><td>0.30</td><td>-0.47</td><td>-0.15</td><td>0.36</td><td>0.30</td><td>0.50</td><td>-</td></tr><tr><td>Source-only</td><td>63.58</td><td>49.81</td><td>48.04</td><td>48.02</td><td>48.04</td><td>47.88</td><td>32.62</td><td>46.35</td><td>54.90</td><td>63.69</td><td>49.31</td><td>32.49</td><td>49.30</td><td>49.22</td><td>63.48</td><td>65.60</td></tr></table>

Adaptation Algorithms & Validators: We consider six representative domain adaptation algorithms, spanning both recent and classic methods and a variety of underlying principles. These include the pseudo-label based ATDOC [21]; domain-adversarial learning with the seminal DANN [10]; domain-alignment with MMD [23]; BNM and MCC which optimise the target label distribution under nuclear norm prior and minimum class confusion priors respectively, and the classifier-discrepancy-based MCD [36]. We explore tuning these models with a large number of potential validation criteria as listed in Table 2.

We start by finetuning a network on the source task. We take ResNet50 weights pretrained on ImageNet $[14]$ for all datasets apart from MNIST-M where a smaller CNN is used. The final classification layer is replaced by an MLP head consisting of two blocks of {Linear, ReLU, Dropout} followed by a final linear layer. We finetune only this head on the source task using a standard categorical cross-entropy loss. 10 models are trained with learning rates sampled uniformly at random from a logarithmic scale between $10^{-5} - 10^{-1}$ . These runs form the set of checkpoints for the source-only model. They are not used for evaluating the validation criteria, but we report performances at times for comparison. When training each adaptation algorithm, we use the source-only model weights as initialisation for both the backbone and MLP head. The specific source-only checkpoint used as initialisation is the one with the highest source validation accuracy and in case of ties we select the checkpoint trained for the fewest amount of epochs.

For each of our 6 adaptation algorithms, we sample 10 sets of hyperparameters and train one model per set. The training uses both source and target data. The number of epochs depends on the dataset and specific target domain, but in all cases, we save 20 checkpoints during the course of training. The optimizer is Adam with parameters $\{\text{betas} = (0.9, 0.999)\}$ and the weight decay is always 0.0001. The learning rate is always part of the sampled hyperparameters, and it is updated during training via cosine annealing with a warmup phase during the first $5\%$ of training. The full details of our training procedure and hyperparameter search spaces can be found in Appendix C.

4.1.2 Results. The results in Table 3 report the performance of each adaptation algorithm and validation criterion combination, averaged over all 21 domain transfer tasks – in terms of both test accuracy after HPO and the weighted Spearman correlation coefficient between validation scores and testing accuracy. More detailed correlation plots are given in Appendix E. Table 4 shows how easily tunable the algorithms are, via the percentage of all algorithm checkpoints outperforming the baseline.

Table 4: Percentage of all algorithm checkpoints which outperform the baseline source-only model, in the UDA setting. The ATDOC, BNM and MCC algorithms are the most easily tunable, with over 40% of hyperparameter choices leading to better-performing models. We also see that when selecting checkpoints with the oracle validator, 18.3% of the source-only checkpoints outperform the one selected as the baseline using the source validation accuracy validator.

<table><tr><td>Source-only</td><td>ATDOC</td><td>BNM</td><td>DANN</td><td>MCC</td><td>MCD</td><td>MMD</td></tr><tr><td>18.3</td><td>42.8</td><td>48.4</td><td>24.9</td><td>43.4</td><td>14.6</td><td>29.5</td></tr></table>

How well does unsupervised validation work? From Table 3 we can draw a rich set of observations: (1) The validation criteria have varying ability to predict the test accuracy and thus drive HPO in domain adaptation. This is visible in the correlation scores, ranging from -.60 to .65 correlation coefficient at best; and the significant variability of testing performance when using the various criteria to drive HPO. Importantly, it is also visible in the gap between the performance of the best criteria and the best-case oracle criterion. (2) The best validation criterion is the previously un-studied V-measure score, which has the best average rank of 3.0 across all the validators, and closes $70\%$ of the gap between the baseline of $63.5\%$ and oracle upper bound of $72.4\%$ when paired with the MCC adapter. (3) The DA algorithms themselves vary substantially in how easy they are to tune, with MCD and ATDOC for example being highly dependent on choice of validator, versus BNM which is comparatively insensitive to the choice of validator. Practitioners may prefer to opt for comparatively easy to tune adaptation algorithms, given the challenge of validation for DA.

What is the impact of validating on training vs validation splits? An important design choice in validation is which data split the validator is evaluated on. As discussed in $[26, 25]$ , while prior work that validates on the source domain has fairly consistently used the source validation set; prior work that validates on the unlabelled target domain has been inconsistent in the choice between validating using the train or an independent val split. Since learning is driven by applying an adaptation loss on the target train set, there is the possibility of overfitting during unsupervised adaptation. Thus we conjecture that one should validate on a disjoint split of the target domain. In Tab. 3, we avoided this issue by taking the best split for each validator. We now analyse this issue by comparing using the train vs validation split for evaluating criteria. From the results in Fig. 2 we see that for all the top-performing criteria the val split is preferred. While this result might seem unsurprising in retrospect, we emphasise that the use of a val split is NOT standard practice in the literature, even in thorough recent evaluations $[25]$ . We show that there is thus a trade-off between using held-out validation data to improve the validators, and using as much training data as possible to improve adaptation.

![](images/1777e32ab5f5ab6d0a0c8a4c7e8b21ed87c18b1ac3e84e035624d95d016e6fed.jpg)  
Figure 2: Comparison of split for evaluation of validation criteria. We report the average target test accuracy of selected models for each validator when applied on (blue) target train data and (orange) target validation data. The dashed line is the source-only model performance.

Table 5: Comparison of validation criteria for model selection in SFDA on Office-Home. We report (i) the target test performance for the top models selected by each validator, and (ii) the correlation coefficient between the validator scores and the test performance over all hyperparameters and checkpoints. For each algorithm, we include the source-only checkpoint in the pool available to validators (indicated by the “+SO” suffix). The colour of a cell indicates whether that model/validator combination beats the source-only model (green) or not (red), with a darker red colour meaning it fails to achieve half of the source-only model performance.

<table><tr><td></td><td>RankMe</td><td>AMI</td><td>ARI</td><td>V-Measure</td><td>FMI</td><td>Silhouette</td><td>DBI</td><td>CHI</td><td>BNM</td><td>SND</td><td>IM</td><td>Entropy</td><td>Accuracy</td><td>Oracle</td></tr><tr><td>AAD+SO</td><td>61.63</td><td>57.41</td><td>1.60</td><td>60.19</td><td>1.59</td><td>1.74</td><td>53.62</td><td>1.90</td><td>62.51</td><td>56.29</td><td>59.40</td><td>4.78</td><td>-</td><td>65.71</td></tr><tr><td>NRC+SO</td><td>57.30</td><td>58.44</td><td>6.74</td><td>62.73</td><td>6.70</td><td>1.62</td><td>45.12</td><td>1.70</td><td>58.18</td><td>56.84</td><td>57.71</td><td>40.70</td><td>-</td><td>64.93</td></tr><tr><td>SHOT+SO</td><td>59.20</td><td>59.73</td><td>60.88</td><td>60.99</td><td>59.38</td><td>57.54</td><td>55.41</td><td>46.72</td><td>54.14</td><td>57.13</td><td>54.52</td><td>59.51</td><td>-</td><td>64.04</td></tr><tr><td>Avg.</td><td>59.38</td><td>58.52</td><td>23.07</td><td>61.30</td><td>22.56</td><td>20.30</td><td>51.38</td><td>16.77</td><td>58.28</td><td>56.75</td><td>57.21</td><td>35.00</td><td>-</td><td>64.89</td></tr><tr><td>Avg. Rank</td><td>4.33</td><td>3.33</td><td>7.33</td><td>1.67</td><td>9.00</td><td>9.67</td><td>7.67</td><td>10.67</td><td>5.00</td><td>6.67</td><td>6.00</td><td>6.67</td><td>-</td><td>-</td></tr><tr><td>Correlation</td><td>-0.02</td><td>0.11</td><td>-0.32</td><td>0.09</td><td>-0.08</td><td>-0.54</td><td>0.01</td><td>-0.77</td><td>-0.01</td><td>0.06</td><td>0.02</td><td>-0.11</td><td>-</td><td>-</td></tr><tr><td>Source-only</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>56.49</td><td>-</td></tr></table>

## 4.2 Source-free Domain Adaptation

4.2.1 Setup. For SFDA we use the Office-Home dataset as a benchmark, covering all 12 domain shifts. The same source-only models that we produced for UDA are also used here for initialisation of the same architecture. Three recent SFDA algorithms adapt the model on target domain data, AAD [47], NRC [46] and SHOT [20]. For each algorithm, we sample 10 sets of hyperparameters and train for 200 epochs. The setup follows the UDA setting described above, with the main difference being the adaptation algorithms and validators only have access to target data (Fig. 1). As the source domain is not available in this setting, we can only apply our validators to the target domain splits. This means CORAL and MMD are not applicable, since they need both domains to compute their scores. Following our results in Section 4.1.2 we use the target validation split for all validators as the source data is absent in this case.

4.2.2 Results. Analogous to UDA, the results in Table 5 report the performance of each adaptation algorithm and validation criterion combination, averaged over all 12 domain transfer SFDA tasks – in terms of both test accuracy after HPO and the weighted Spearman correlation coefficient between validation scores and testing accuracy. More detailed correlation plots are given in Appendix E.

How does unsupervised validation work in the absence of source data? From the results in Table 5 we can draw a set of conclusions analogously to UDA. Specifically, (i) Here, the best validators are RankMe and V-measure, with V-measure closing up to 75% of the gap between the baseline and oracle when combined with NRC. (ii) However the AAD and NRC algorithms are highly sensitive to validator choice, with the weaker validators such as FMI and CHI producing catastrophically poor performance, suggesting that SHOT might be preferred in practice even though NRC has the best accuracy when paired with its preferred validator, and AAD when validated with the oracle. (iii) Many algorithm-validator combinations lead to worse performance than the baseline source-only model. This highlights an important point that in the absence of highly reliable validation criteria, DA algorithms pose a risk of making the performance even worse. This issue is one which is not widely analysed in academic DA but is obviously crucial. Please note that we also included the model initialization (i.e. the source-only model) as one of the checkpoints available for selection by the criteria. However, many validators fail to detect adaptation failure and select a safe source-only model.

## 4.3 Test-Time Adaptation

4.3.1 Setup. We next adopt the TTA setting, where a pre-trained model adapts to the test data as it comes, one batch at a time. For simplicity, we use the episodic setting $[45]$ where the model is reset after each batch. We use the most common TTA benchmark of CIFAR10-C, consisting of 15 versions of the CIFAR10 test set with various corruptions applied, including Gaussian noise, pixelation and fog. Additionally, we investigate whether existing TTA algorithms are able to deal with the more complex distribution shifts from Office-Home, using all 12 domain shift setups. For CIFAR10-C, we use the pre-trained CIFAR10 checkpoint of [22] as our source-only model and initialisation for the TTA algorithms. For Office-Home, we use the same source-only checkpoints as in the UDA and SFDA sections above. Two algorithms are trained: SHOT [20] which uses information maximisation and pseudo-labelling to align target representations and TENT [45] which adapts by minimising the entropy of its predictions on the test batch. As this setting only exposes a single batch to the model at a time, both training and validation use the same data. As in the SFDA setting, CORAL and MMD are not applicable, since they need both domains to compute their scores. This also means that there is no validator based on accuracy, as it requires source data to be computed.

Table 6: Test-Time Adaptation on CIFAR10-C, at corruption level 5. We use the episodic setup where the model is reset after each batch. For each algorithm, we include the source-only checkpoint in the pool available to validators (indicated by the “+SO” suffix). The colour of a cell indicates whether that model/validator combination beats the source-only model (green) or not (red).

<table><tr><td></td><td>RankMe</td><td>AMI</td><td>ARI</td><td>V-Measure</td><td>FMI</td><td>Silhouette</td><td>DBI</td><td>CHI</td><td>BNM</td><td>SND</td><td>IM</td><td>Entropy</td><td>Accuracy</td><td>Oracle</td></tr><tr><td>SHOT+SO</td><td>78.38</td><td>37.37</td><td>36.85</td><td>37.69</td><td>36.86</td><td>36.50</td><td>38.60</td><td>43.87</td><td>45.22</td><td>53.48</td><td>46.80</td><td>39.14</td><td>-</td><td>86.24</td></tr><tr><td>TENT+SO</td><td>84.06</td><td>84.14</td><td>84.17</td><td>84.13</td><td>84.17</td><td>84.23</td><td>81.84</td><td>75.98</td><td>84.22</td><td>79.89</td><td>84.21</td><td>83.20</td><td>-</td><td>84.76</td></tr><tr><td>Avg.</td><td>81.22</td><td>60.76</td><td>60.51</td><td>60.91</td><td>60.51</td><td>60.36</td><td>60.22</td><td>59.93</td><td>64.72</td><td>66.68</td><td>65.51</td><td>61.17</td><td>-</td><td>85.50</td></tr><tr><td>Avg. Rank</td><td>4.50</td><td>7.50</td><td>7.75</td><td>7.50</td><td>7.25</td><td>6.50</td><td>8.50</td><td>8.50</td><td>3.00</td><td>6.50</td><td>3.00</td><td>7.50</td><td>-</td><td>-</td></tr><tr><td>Correlation</td><td>0.10</td><td>0.13</td><td>0.14</td><td>0.13</td><td>0.14</td><td>0.13</td><td>-0.56</td><td>0.09</td><td>0.09</td><td>-0.55</td><td>0.08</td><td>-0.02</td><td>-</td><td>-</td></tr><tr><td>Source-only</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>70.64</td><td>-</td></tr></table>

4.3.2 Results. Tables 6 and 7 report the performance of each adaptation algorithm and validation criterion combination averaged over all CIFAR-C and Office-Home TTA tasks.

Is Test-Time Adaptation effective when performing proper model selection? The results for CIFAR in Table 6 lead to a different conclusion from that of UDA and SFDA. (i) RankMe is again the best validation criterion, and interestingly, we see that the top validators now manage to almost match the oracle performance. (ii) TENT is robust to the choice of validator, with consistently good performance close to oracle. SHOT obtains reasonable performance only when RankMe validator is used.

While TENT-based TTA plus various validators above show a success case for good practice adaptation on CIFAR10-C, we next ask whether these good results persist to a real rather than synthetic adaptation task. Table 7, shows the results of the Office-Home benchmark. From the results, we can see that: (1) There is only a 2-3% gap between the oracle best case and the baseline, suggesting that all algorithms struggle on this benchmark, even for best-case HPO. (2) Almost all algorithm-validator combinations are worse than the 57% source-only accuracy, similar to the SFDA case discussed earlier. When we compare the adaptation performance with- and without-access to the source-only model in the pool of checkpoints for HPO, SHOT has little improvement. The validators are not able to respond to the destructive adaptation and fail to pick a safe pre-adaptation model. Thus, we suggest that the strong success of TTA methods on synthetic benchmarks may not be representative of real-world adaptation problems, especially when required to use fair validation.

## 5 Conclusion

In this work, we performed a comprehensive study of HPO and model selection for domain adaptation, covering 10 algorithms and 15 validators across three settings (UDA, SFDA and TTA). We have found that previously unexplored validators like RankMe and V-Measure perform well across several settings, but the optimal validator is setting and algorithm dependent. Thus practitioners may wish to consider tuning sensitivity as a key factor for algorithm selection beyond reported performance on academic benchmarks. We have also highlighted some surprising results: (i) A strong source checkpoint can be competitive with UDA algorithms when using the RankMe or MMD validators. (ii) Even when validating among both source-only and algorithm checkpoints, performance may be worse than abandoning adaptation altogether and simply using a source-only model as selected by source accuracy – especially in SFDA and TTA. This is a major risk and failure case that will preclude deployment of adaptation in real applications, and one which we encourage future academic work to study. (iii) While TTA algorithms have attracted attention for their strong performance on simple synthetic benchmarks, they fail on more complex distribution shifts such as Office-Home. Future work should carefully consider model selection pipelines, choice of validators, data splits and, at times, whether to perform adaptation at all.

Table 7: Test-Time Adaptation on Office-Home. We use the episodic setup where the model is reset after each batch. Algorithms that include the source-only checkpoint in the pool available to validators are marked by the suffix “+SO”. The colour of a cell indicates whether that model/validator combination beats the source-only model (green) or not (red), with a darker red colour meaning it fails to achieve half of the source-only model performance.

<table><tr><td></td><td>RankMe</td><td>AMI</td><td>ARI</td><td>V-Measure</td><td>FMI</td><td>Silhouette</td><td>DBI</td><td>CHI</td><td>BNM</td><td>SND</td><td>IM</td><td>Entropy</td><td>Accuracy</td><td>Oracle</td></tr><tr><td>SHOT</td><td>20.46</td><td>9.38</td><td>10.09</td><td>9.43</td><td>10.09</td><td>14.07</td><td>34.67</td><td>12.06</td><td>9.10</td><td>35.58</td><td>10.13</td><td>7.52</td><td>-</td><td>59.05</td></tr><tr><td>TENT</td><td>42.40</td><td>37.57</td><td>42.79</td><td>43.49</td><td>40.77</td><td>2.25</td><td>39.90</td><td>3.61</td><td>44.93</td><td>39.20</td><td>44.24</td><td>2.37</td><td>-</td><td>49.28</td></tr><tr><td>SHOT+SO</td><td>20.46</td><td>9.32</td><td>12.40</td><td>9.12</td><td>12.05</td><td>14.84</td><td>34.67</td><td>11.63</td><td>9.10</td><td>35.58</td><td>10.81</td><td>7.54</td><td>-</td><td>60.20</td></tr><tr><td>TENT+SO</td><td>42.59</td><td>55.91</td><td>55.91</td><td>55.91</td><td>55.91</td><td>6.35</td><td>39.90</td><td>45.09</td><td>46.01</td><td>39.20</td><td>45.75</td><td>2.37</td><td>-</td><td>57.15</td></tr><tr><td>Avg.</td><td>31.52</td><td>32.62</td><td>34.16</td><td>32.52</td><td>33.98</td><td>10.60</td><td>37.29</td><td>28.36</td><td>27.56</td><td>37.39</td><td>28.28</td><td>4.95</td><td>-</td><td>58.68</td></tr><tr><td>Avg. Rank</td><td>5.50</td><td>5.75</td><td>3.75</td><td>6.25</td><td>4.25</td><td>7.50</td><td>5.50</td><td>7.00</td><td>8.00</td><td>5.50</td><td>7.00</td><td>12.00</td><td>-</td><td>-</td></tr><tr><td>Correlation</td><td>0.28</td><td>0.22</td><td>0.25</td><td>0.22</td><td>0.29</td><td>-0.18</td><td>0.11</td><td>-0.05</td><td>-0.02</td><td>-0.03</td><td>0.02</td><td>-0.53</td><td>-</td><td>-</td></tr><tr><td>Source-only</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>56.97</td><td>-</td></tr></table>

## 6 Limitations

Since this paper covers multiple settings and many algorithms, we were only able to run each algorithm on each domain shift with 10 hyperparameter choices. Ideally, this number would be higher, but adapting many models is expensive, and in reality a practitioner would also face computational limitations. If we had been able to increase this number, the effects would likely be minor improvements in the highest scores achievable by the algorithms, but it would not guarantee that any given validator would choose a better checkpoint. A second limitation is our preliminary study of regression adaptation. Many validators are designed for classification and performance when applied to regression may suffer. However, we view this as a call for study of validation criteria across the full range of adaptation applications from regression to segmentation and detection.

## 7 Broader Impact Statement

As distribution shifts often occur in real-world problems, the use of domain adaptation techniques to tackle them has become commonplace. We have highlighted weaknesses in the standard practice found in DA literature which, if applied in safety-critical scenarios, could lead to catastrophic outcomes. We have therefore outlined a set of better practices for practitioners looking to apply DA to their problems and presented a more realistic view of the field's current potential. Our hope is that this will decrease the likelihood of bad outcomes in its real-world application. The environmental impact of running a large-scale benchmarking study is significant. However, we aim to provide a clear pipeline for future work to use, which can ultimately reduce unnecessary computation due to bad practice.

[1] Andrea Agostinelli, Michal Pándy, Jasper R. R. Uijlings, Thomas Mensink, and Vittorio Ferrari. How stable are transferability metrics evaluations? In ECCV, 2022.

[2] Pablo Arbelaez, Michael Maire, Charless Fowlkes, and Jitendra Malik. Contour detection and hierarchical image segmentation. IEEE Trans. Pattern Anal. Mach. Intell., 2011.

[3] Rishi Bommasani et al. On the opportunities and risks of foundation models. arXiv:2108.07258, 2021.

[4] Tadeusz Caliński and Joachim Harabasz. A dendrite method for cluster analysis. Communications in Statistics-theory and Methods, 1974.

[5] Corinna Cortes and Mehryar Mohri. Domain adaptation in regression. In Algorithmic Learning Theory, 2011.

[6] Gabriela Csurka, Timothy M Hospedales, Mathieu Salzmann, and Tatiana Tommasi. Visual domain adaptation in the deep learning era. Synthesis Lectures on Computer Vision, 2022.

[7] Shuhao Cui, Shuhui Wang, Junbao Zhuo, Liang Li, Qingming Huang, and Qi Tian. Towards discriminability and diversity: Batch nuclear-norm maximization under label insufficient situations. In CVPR, 2020.

[8] David L. Davies and Donald W. Bouldin. A cluster separation measure. IEEE Transactions on Pattern Analysis and Machine Intelligence, 1979.

[9] E. B. Fowlkes and Colin L. Mallows. A method for comparing two hierarchical clusterings. Journal of the American Statistical Association, 1983.

[10] Yaroslav Ganin, Evgeniya Ustinova, Hana Ajakan, Pascal Germain, Hugo Larochelle, François Laviolette, Mario Marchand, and Victor Lempitsky. Domain-adversarial training of neural networks. Journal of Machine Learning Research, 2016.

[11] Quentin Garrido, Randall Balestriero, Laurent Najman, and Yann Lecun. Rankme: Assessing the downstream performance of pretrained self-supervised representations by their rank. In ICML, 2023.

[12] Xavier Glorot and Yoshua Bengio. Understanding the difficulty of training deep feedforward neural networks. In AISTATS, 2010.

[13] Ian J. Goodfellow, Jean Pouget-Abadie, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair, Aaron Courville, and Yoshua Bengio. Generative adversarial nets. In NeurIPS, 2014.

[14] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep residual learning for image recognition. In CVPR, 2016.

[15] Xin He, Kaiyong Zhao, and Xiaowen Chu. AutoML: A Survey of the State-of-the-Art. Knowledge-Based Systems, 2019.

[16] Han-Kai Hsu, Chun-Han Yao, Yi-Hsuan Tsai, Wei-Chih Hung, Hung-Yu Tseng, Maneesh Singh, and Ming-Hsuan Yang. Progressive domain adaptation for object detection. In WACV, 2020.

[17] Ying Jin, Ximei Wang, Mingsheng Long, and Jianmin Wang. Minimum Class Confusion for Versatile Domain Adaptation. In ECCV, 2020.

[18] Y. Lecun, L. Bottou, Y. Bengio, and P. Haffner. Gradient-based learning applied to document recognition. Proceedings of the IEEE, 1998.

[19] Yann LeCun, Corinna Cortes, and C J Burges. MNIST handwritten digit database, 2010.

[20] Jian Liang, Dapeng Hu, and Jiashi Feng. Do we really need to access the source data? source hypothesis transfer for unsupervised domain adaptation. In International Conference on Machine Learning, 2020.

[21] Jian Liang, Dapeng Hu, and Jiashi Feng. Domain Adaptation with Auxiliary Target Domain-Oriented Classifier. In CVPR, 2021.

[22] Yuejiang Liu, Parth Kothari, Bastien van Delft, Taylor Mordan Baptiste Bellot-Gurlet, and Alexandre Alahi. TTT++: When does self-supervised test-time training fail or thrive? In NeurIPS, 2021.

[23] Mingsheng Long, Yue Cao, Jianmin Wang, and Michael I. Jordan. Learning Transferable Features with Deep Adaptation Networks. In ICML, 2015.

[24] Pietro Morerio, Jacopo Cavazza, and Vittorio Murino. Minimal-entropy correlation alignment for unsupervised deep domain adaptation. ICLR, 2018.

[25] Kevin Musgrave, Serge Belongie, and Ser-Nam Lim. Benchmarking validation methods for unsupervised domain adaptation. arXiv preprint arXiv:2208.07360, 2022.

[26] Kevin Musgrave, Cornell Tech, Serge Belongie, and Ser-Nam Lim. Unsupervised Domain Adaptation: A Reality Check. In ECCV, 2020.

[27] Adam Paszke, Sam Gross, Soumith Chintala, Gregory Chanan, Edward Yang, Zachary DeVito, Zeming Lin, Alban Desmaison, Luca Antiga, and Adam Lerer. Automatic differentiation in PyTorch, 2017.

[28] V. Patel, R. Gopalan, R. Li, and R. Chellappa. Visual domain adaptation: A survey of recent advances. Signal Processing Magazine, IEEE, 2015.

[29] Xingchao Peng, Ben Usman, Neela Kaushik, Judy Hoffman, Dequan Wang, and Kate Saenko. Visda: The visual domain adaptation challenge, 2017.

[30] Xingchao Peng, Ben Usman, Neela Kaushik, Dequan Wang, Judy Hoffman, and Kate Saenko. Visda: A synthetic-to-real benchmark for visual domain adaptation. In ICCV Workshops, 2018.

[31] W. M. Rand. Objective criteria for the evaluation of clustering methods. Journal of the American Statistical Association, 1971.

[32] Luca Robbiano, Muhammad Rameez Ur Rahman, Fabio Galasso, Barbara Caputo, and Fabio Maria Carlucci. Adversarial branch architecture search for unsupervised domain adaptation. In WACV, 2022.

[33] Andrew Rosenberg and Julia Hirschberg. V-measure: A conditional entropy-based external cluster evaluation measure. In Conference on Empirical Methods in Natural Language Processing, 2007.

[34] Kate Saenko, Brian Kulis, Mario Fritz, and Trevor Darrell. Adapting visual category models to new domains. In ECCV, 2010.

[35] Kuniaki Saito, Donghyun Kim, Piotr Teterwak, Stan Sclaroff, Trevor Darrell, and Kate Saenko. Tune it the right way: Unsupervised validation of domain adaptation via soft neighborhood density. In ICCV, 2021.

[36] Kuniaki Saito, Kohei Watanabe, Yoshitaka Ushiku, and Tatsuya Harada. Maximum Classifier Discrepancy for Unsupervised Domain Adaptation. In CVPR, 2018.

[37] Yuan Shi and Sha Fei. Information-Theoretical Learning of Discriminative Clusters for Unsupervised Domain Adaptation. In ICML, 2012.

[38] Rui Shu, Hung H. Bui, Hirokazu Narui, and Stefano Ermon. A dirt-t approach to unsupervised domain adaptation. In ICLR, 2018.

[39] Baochen Sun and Kate Saenko. Deep coral: Correlation alignment for deep domain adaptation. In ECCV 2016 Workshops, 2016.

[40] Yu Sun, Xiaolong Wang, Zhuang Liu, John Miller, Alexei Efros, and Moritz Hardt. Test-time training with self-supervision for generalization under distribution shifts. In ICML, 2020.

[41] Eric Tzeng, Judy Hoffman, Kate Saenko, and Trevor Darrell. Adversarial discriminative domain adaptation. In CVPR, 2017.

[42] Eric Tzeng, Judy Hoffman, Ning Zhang, Kate Saenko, and Trevor Darrell. Deep domain confusion: Maximizing for domain invariance. In CVPR, 2014.

[43] Hemanth Venkateswara, Jose Eusebio, Shayok Chakraborty, and Sethuraman Panchanathan. Deep hashing network for unsupervised domain adaptation. CoRR, 2017.

[44] Tuan-Hung Vu, Himalaya Jain, Maxime Bucher, Mathieu Cord, and Patrick Pérez. Advent: Adversarial entropy minimization for domain adaptation in semantic segmentation. In CVPR, 2019.

[45] Dequan Wang, Evan Shelhamer, Shaoteng Liu, Bruno Olshausen, and Trevor Darrell. Tent: Fully test-time adaptation by entropy minimization. In ICLR, 2021.

[46] Shiqi Yang, Joost van de Weijer, Luis Herranz, Shangling Jui, et al. Exploiting the intrinsic neighborhood structure for source-free domain adaptation. In NeurIPS, 2021.

[47] Shiqi Yang, Yaxing Wang, Kai Wang, Shangling Jui, et al. Attracting and dispersing: A simple approach for source-free domain adaptation. In Advances in Neural Information Processing Systems, 2022.

[48] Kaichao You, Ximei Wang, Mingsheng Long, and Michael Jordan. Towards accurate model selection in deep unsupervised domain adaptation. In ICML, 2019.

[49] Yang Zou, Zhiding Yu, B.V.K. Vijaya Kumar, and Jinsong Wang. Unsupervised domain adaptation for semantic segmentation via class-balanced self-training. In ECCV, 2018.

Table 8: Comparison of validation criteria for model selection in UDA for a regression task. We report the target test MSE for the top models selected by each validator. Lower is better. The colour of a cell indicates whether that model/validator combination beats the source-only model (green) or not (red), with a darker red colour meaning it gets more than twice the MSE of the source-only model performance.

<table><tr><td></td><td>RankMe</td><td>AMI</td><td>ARI</td><td>V-Measure</td><td>FMI</td><td>Silhouette</td><td>DBI</td><td>CHI</td><td>BNM</td><td>MMD</td><td>CORAL</td><td>SND</td><td>IM</td><td>Entropy</td><td>MSE</td><td>Oracle</td></tr><tr><td>ADDA</td><td>17.52</td><td>43.96</td><td>44.44</td><td>43.96</td><td>44.44</td><td>46.69</td><td>16.50</td><td>18.31</td><td>46.69</td><td>16.76</td><td>17.49</td><td>17.52</td><td>17.49</td><td>16.50</td><td>46.27</td><td>16.50</td></tr><tr><td>CORAL</td><td>45.06</td><td>45.12</td><td>46.09</td><td>45.12</td><td>46.09</td><td>45.22</td><td>44.98</td><td>46.68</td><td>47.02</td><td>47.02</td><td>47.02</td><td>45.71</td><td>47.02</td><td>47.02</td><td>47.11</td><td>43.60</td></tr><tr><td>DANN</td><td>81.63</td><td>42.17</td><td>42.17</td><td>42.17</td><td>46.95</td><td>79.15</td><td>54.40</td><td>55.18</td><td>74.76</td><td>81.63</td><td>53.99</td><td>35.22</td><td>81.63</td><td>54.32</td><td>45.41</td><td>35.22</td></tr><tr><td>GAN</td><td>16.29</td><td>42.06</td><td>43.37</td><td>42.06</td><td>43.22</td><td>53.75</td><td>47.28</td><td>49.41</td><td>47.60</td><td>16.29</td><td>16.80</td><td>53.74</td><td>40.53</td><td>31.59</td><td>44.10</td><td>16.29</td></tr><tr><td>MMD</td><td>64.96</td><td>46.86</td><td>46.94</td><td>46.86</td><td>46.94</td><td>90.67</td><td>55.63</td><td>138.98</td><td>138.98</td><td>64.96</td><td>63.46</td><td>45.41</td><td>138.98</td><td>90.67</td><td>61.47</td><td>45.12</td></tr><tr><td>VADA</td><td>17.54</td><td>44.69</td><td>57.33</td><td>44.69</td><td>57.33</td><td>48.26</td><td>17.54</td><td>41.73</td><td>51.65</td><td>14.38</td><td>14.95</td><td>46.27</td><td>14.38</td><td>55.82</td><td>48.44</td><td>14.38</td></tr><tr><td>Avg. ↓</td><td>40.50</td><td>44.14</td><td>46.72</td><td>44.14</td><td>47.50</td><td>60.62</td><td>39.39</td><td>58.38</td><td>67.78</td><td>40.17</td><td>35.62</td><td>40.64</td><td>56.67</td><td>49.32</td><td>48.80</td><td>28.52</td></tr><tr><td>Avg. Rank ↓</td><td>6.33</td><td>5.42</td><td>8.42</td><td>5.42</td><td>8.58</td><td>11.33</td><td>5.50</td><td>10.00</td><td>12.58</td><td>6.92</td><td>6.25</td><td>6.25</td><td>8.50</td><td>8.33</td><td>10.17</td><td>-</td></tr><tr><td>Correlation ↑</td><td>-0.31</td><td>0.13</td><td>-0.09</td><td>0.13</td><td>-0.16</td><td>-0.17</td><td>0.05</td><td>0.12</td><td>-0.25</td><td>0.17</td><td>0.12</td><td>-0.03</td><td>-0.07</td><td>-0.25</td><td>-0.29</td><td>-</td></tr><tr><td>Source-only</td><td>49.06</td><td>49.06</td><td>49.06</td><td>49.06</td><td>49.06</td><td>49.06</td><td>49.06</td><td>49.06</td><td>49.06</td><td>49.06</td><td>49.06</td><td>49.06</td><td>49.06</td><td>49.06</td><td>46.96</td><td>42.28</td></tr></table>

## A Regression

Setup: We construct a regression dataset with a domain shift akin to MNIST-M [12]. The source domain consists of 32x32 images where, for each image, a single digit taken from MNIST is pasted onto a black background. The digit is randomly scaled between 4x4 and 16x16 pixels and its location is randomised while ensuring the entire digit is visible. The label accompanying the image is the top left $(x_{1},y_{1})$ and bottom right $(x_{2},y_{2})$ coordinates of the digit bounding box. The target domain is constructed similarly, but instead of a black background, we use 32x32 regions cropped from the BSDS500 dataset [2].

We discretize the label space as follows. The bounding box labels and predictions take the following form $\{x_{1}, y_{1}, x_{2}, y_{2}\}$ , where each element is a real value between 0 and 1. The function q discretizes each element in the vector into one of 8 uniformly spaced classes between 0 and 1. The class of the full vector is then $c = q(x_{1}) + 8q(y_{1}) + 8^{2}q(x_{2}) + 8^{3}q(y_{2})$ . This transformation into class values is performed for all labels and predictions.

The architecture is the same as used for the MNIST-M experiments in the classification setting, with an adjusted final layer for regression. The loss used on the source data is the mean squared error. All other details are the same as in the above UDA setting. For this setup we train six algorithms, ADDA $[41]$ , CORAL $[39]$ , DANN $[10]$ , GAN $[13]$ , MMD $[42]$ , VADA $[38]$ . Many of the validators we have considered so far rely on categorical labels and predictions. In this regression setup we, therefore, discretize the label space as described above.

Results: Table 8 shows the results on this regression task.

Are conclusions still valid beyond image classification? The overall results show a similar trend to the observation of UDA for image classification. 1) Now, CORAL works as the best validator. However, there is no one validator working consistently well for all methods. 2) CORAL, as a UDA method, works most robustly with all validation criteria, leading to all selected results close to its oracle performance, which, though, is not ideal. However, we can see now the correlations are very low for all validators, indicating that there is no reliable validator in this case that works robustly to select a good UDA model.

## B Assets

Code: Our anonymized code base is available at https://anon-github.automl.cc/r/better-da-4936. In this work, we make use of the KevinMusgrave/pytorch-adapt, DequanWang/tent, vita-epfl/ttt-plus-plus and matthijsz/weightedcorr libraries, all available on GitHub and all released under the MIT License.

Data: The creators of the MNIST [19], MNIST-M [10] and Office-31 [34] datasets have not provided obvious licenses, but both datasets were created for open academic use. Both VisDA-2017 [29] and

Office-Home [43] are released under custom licenses allowing non-commercial research and use for educational purposes.

## C Training Details

## C.1 Settings

To fully clarify our adaptation settings, we present in algorithms 1, 2 and 3 the benchmarking procedure for UDA, SFDA and TTA, respectively.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 UDA benchmarking setup.

Require: Source data  $D_{S}$ , target data  $D_{T}$ , algorithm A, parameters  $\theta$ , hyperparameter search space H, validator V.

for hyperparameters  $h \sim H$  do

 $\theta_{h}^{*} = \arg \min_{\theta} \mathcal{A}(\theta, \mathcal{D}_{S}, \mathcal{D}_{T}; h)$ 

end for

 $h^{*} = \arg \max_{h} V(\theta_{h}^{*}, \mathcal{D}_{S}, \mathcal{D}_{T})$ 

▷ Sample hyperparameters

▷ Optimise model

▷ Select best hyperparameters

Algorithm 2 SFDA benchmarking setup.

Require: Target data  $D_{T}$ , algorithm A, parameters  $\theta$ , hyperparameter search space H, validator V.

for hyperparameters  $h \sim H$  do

 $\theta_{h}^{*} = \arg \min_{\theta} \mathcal{A}(\theta, \mathcal{D}_{T}; h)$ 

▷ Sample hyperparameters

▷ Optimise model

end for

 $h^{*} = \arg \max_{h} V(\theta_{h}^{*}, \mathcal{D}_{T})$ 

▷ Select best hyperparameters

Algorithm 3 TTA benchmarking setup.

Require: Test data  $D_{T}$ , algorithm A, parameters  $\phi$ , hyperparameter search space H, validator V.

for each batch  $X \sim D_{T}$  do

for hyperparameters  $h \sim H$  do

 $\theta = \phi$ $\theta_{h}^{*} = \arg \min_{\theta} \mathcal{A}(\theta, X; h)$ 

▷ Sample hyperparameters

▷ Reset model

▷ Optimise model

end for

 $h_{X}^{*} = \arg \max_{h} V(\theta_{h}^{*}, X)$ 

▷ Select best hyperparameters

end for
</div>

Data splits: We split all domains of all datasets into train (60%), val (20%) and test (20%) splits. Optimisation: The optimiser for UDA classification, UDA regression, and SFDA is Adam with parameters $\{\text{betas}=(0.9, 0.999)\}$ and weight decay of 1e-4. For TTA the optimizer is SGD with a momentum of 0.9 (the optimizer is reset after each batch, like the model parameters). The learning rate across all settings is sampled from a log-uniform distribution over $[1e-5, 1e-1]$ .

We train for 100 epochs for MNIST-M and MNIST-MR, 200 on VisDA-2017 and Office-Home. On Office-31 it is 200 if amazon is the target and 2000 otherwise. The number of saved checkpoints is always 20. For our episodic TTA setup, we perform 20 updates on each batch, saving a checkpoint after each update.

Architecture: The backbone for experiments on MNIST-M and our regression version MNIST-MR is a LeNet- $5^{2}$ [18], and for all other experiments, a ResNet50 [14]. The classifier/regressor is an MLP with two blocks of {Linear, ReLU, Dropout} followed by a final linear layer.

Source Training: The source model consists of the backbone and classifier/regressor as defined above. When using a ResNet50 backbone, we initialise it with ImageNet pre-trained weights (available in PyTorch [27] as resnet50(weights=ResNet50\_Weights.IMAGENET1K\_V1) and freeze the backbone during source training, thereby only updating the classification head. When using a LeNet backbone, we update the entire network during source training. For TTA on CIFAR10-C we use the pre-trained CIFAR10 checkpoint provided by [22] as initialisation. In all other cases, the best model checkpoint as selected by source validation accuracy is used as the initialisation for all adaptation algorithms.

Adaptation: During UDA adaptation, the model receives a batch consisting of 64 source examples (with labels) and 64 target examples (without labels). For SFDA, the model only receives the target examples.

## C.2 Hyperparameters

Throughout the experiments conducted in this work, we perform random search for finding the best hyperparameters, with 10 random choices per algorithm. Better performance can potentially be reached by using e.g. BayesOpt. In this work, we focus on analysis and prefer the simpler random search to (1) enable computing a correlation score between the validation criteria and test performance (correlation computed over both high and low-quality checkpoints), as we report in our main tables. Also (2) because our comparisons involve comparing the “best” possible checkpoint with the one discovered by each validator, we did not want to risk aggressively optimising a bad validator and thus having no good checkpoints available for selection by the oracle. The hyperparameter search spaces for all algorithms are specified in Tab. 9. Whenever possible, these are identical to those used in [26].

## D Validation Details

## D.1 Validators

A recent work systematically investigated the possible validation criteria for UDA, which we summarise below using $\hat{y}$ to denote the one-hot predictions of the model and y as the one-hot ground truth labels. Source accuracy: d is simply the accuracy metric and $D_{V}$ can be a training or validation set from a source domain.

$$
d (f _ {\pmb {\theta}}, \mathcal {D} _ {V}) = \frac {1}{N _ {V}} \sum_ {i = 1} ^ {N _ {V}} \mathbf {1} (\hat {\pmb {y}} = \pmb {y}),\tag{5}
$$

where $\mathbf{1}(\cdot)$ is the indicator function that evaluates to one if its argument is true and zero otherwise. Entropy: Entropy has been used in an adaptation loss [45] as well as for model selection. In this case, d computes the confidence of the model predictions, as measured by the entropy of the predicted label distribution, and $D_{V}$ is typically the training or validation set from an unlabelled target domain. We further investigate the effect when $D_{V}$ comes from the source domain.

$$
d (f _ {\pmb {\theta}}, \mathcal {D} _ {V}) = \frac {1}{N _ {V}} \sum_ {i = 1} ^ {N _ {V}} H (\pmb {p} _ {i}), \pmb {p} _ {i} = f _ {\pmb {\theta}} (\pmb {x} _ {i}),\tag{6}
$$

where

$$
H (\boldsymbol {p}) = - \sum_ {j = 1} ^ {K} p _ {[ j ]} \log p _ {[ j ]},\tag{7}
$$

computes the entropy of the categorical distribution, p. Information maximisation (IM): IM is often used as an adaptation loss as well [37] to maximise the diversity of prediction in addition to

Table 9: Hyperparameter search spaces for all algorithms considered. Some algorithms are used in multiple settings (e.g. DANN and MMD are used for UDA classification and regression and SHOT is used for SFDA and TTA). In such cases, the search spaces are the same across settings.

<table><tr><td>Algorithm</td><td>Hyperparameter</td><td>Search Space</td></tr><tr><td rowspan="3">ATDOC</td><td> $\lambda_{atdoc}$ </td><td>[0, 1]</td></tr><tr><td> $K_{atdoc}$ </td><td>int([5, 25], step=5)</td></tr><tr><td> $\lambda_L$ </td><td>[0, 1]</td></tr><tr><td rowspan="2">BNM</td><td> $\lambda_{bnm}$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_L$ </td><td>[0, 1]</td></tr><tr><td rowspan="3">DANN</td><td> $\lambda_D$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_{grl}$ </td><td>log([0.1, 10])</td></tr><tr><td> $\lambda_L$ </td><td>[0, 1]</td></tr><tr><td rowspan="3">MCC</td><td> $\lambda_{mcc}$ </td><td>[0, 1]</td></tr><tr><td> $T_{mcc}$ </td><td>[0.2, 5])</td></tr><tr><td> $\lambda_L$ </td><td>[0, 1]</td></tr><tr><td rowspan="3">MCD</td><td> $N_{mcd}$ </td><td>int([1, 10])</td></tr><tr><td> $\lambda_{disc}$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_L$ </td><td>[0, 1]</td></tr><tr><td rowspan="3">MMD</td><td> $\lambda_F$ </td><td>[0, 1]</td></tr><tr><td> $\gamma_{exp}$ </td><td>int([1, 8])</td></tr><tr><td> $\lambda_L$ </td><td>[0, 1]</td></tr><tr><td rowspan="2">ADDA</td><td> $\lambda_D$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_G$ </td><td>[0, 1]</td></tr><tr><td rowspan="2">CORAL</td><td> $\lambda_F$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_L$ </td><td>[0, 1]</td></tr><tr><td rowspan="3">GAN</td><td> $\lambda_D$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_G$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_L$ </td><td>[0, 1]</td></tr><tr><td rowspan="5">VADA</td><td> $\lambda_D$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_G$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_V$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_E$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_L$ </td><td>[0, 1]</td></tr><tr><td rowspan="2">AAD</td><td> $\lambda_{aad}$ </td><td>[0, 1]</td></tr><tr><td> $K_{aad}$ </td><td>int([3, 5]</td></tr><tr><td rowspan="3">NRC</td><td> $\lambda_L$ </td><td>[0, 1]</td></tr><tr><td> $K_{nrc}$ </td><td>int([2, 5]</td></tr><tr><td> $KK_{nrc}$ </td><td>int([2, 5]</td></tr><tr><td rowspan="3">SHOT</td><td> $\lambda_{cls}$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_{ent}$ </td><td>[0, 1]</td></tr><tr><td> $\lambda_L$ </td><td>[0, 1]</td></tr><tr><td>TENT</td><td> $\lambda_L$ </td><td>[0, 1]</td></tr></table>

confidence.

$$
d (f _ {\boldsymbol {\theta}}, \mathcal {D} _ {V}) = H (\frac {1}{N _ {V}} \sum_ {i = 1} ^ {N _ {V}} \pmb {p} _ {i}) - \frac {1}{N _ {v}} \sum_ {i = 1} ^ {N _ {v}} H (\pmb {p} _ {i}).\tag{8}
$$

Adjusted Mutual Information (AMI): This is the adjusted mutual information between predicted and cluster labels.

$$
d (f _ {\boldsymbol {\theta}}, \mathcal {D} _ {V}) = \operatorname{AMI} (\boldsymbol {p}, \operatorname{CL} (\mathcal {D} _ {V}))\tag{9}
$$

where $\mathrm{CL}(\mathcal{D}_{V})$ is the cluster labels for validation set $D_{V}$ , which can be the target training or validation set.

V-Measure: Similarly to AMI, this is a metric defined over clustering labels and predictions. It is defined as the harmonic mean between homogeneity and completeness $[33]$ .

Other clustering measures: Along with AMI and V-Measure, we compute several other related clustering measures, namely, adjusted Rand index, Fowlkes–Mallows index, silhouette score, Davies–Bouldin index and Calinski-Harabasz index.

RankMe: Originally proposed for estimating the transferability of self-supervised representations [11], RankMe approximates the rank of the feature matrix on pre-training data. We investigate its application to both source and target domain data.

CORAL: CORAL is an adaptation algorithm that aligns the feature distributions of the source and target data by minimising second-order statistics $[39]$ . Their loss can be used as a validator and is defined as the difference between the covariance matrices of the two domains, $C_{S}$ and $C_{T}$ .

$$
d (f _ {\pmb {\theta}}, \mathcal {D} _ {V}) = \mathrm{CORAL} (\mathcal {D} _ {S}, \mathcal {D} _ {T}) = \frac {1}{4 d ^ {2}} \| C _ {S} - C _ {T} \| _ {F} ^ {2}\tag{10}
$$

Maximum mean discrepancy (MMD): A common metric used to compute the discrepancy of feature distributions from source and target domains $[42]$ , which can be used with the assumption that the trained model may have a good target performance when the source and target domain features are aligned.

$$
\begin{array}{l} d (f _ {\boldsymbol {\theta}}, \mathcal {D} _ {V}) = \mathrm{MMD} (\mathcal {D} _ {S}, \mathcal {D} _ {T}) \\ = \frac {1}{N _ {S} (N _ {S} - 1)} \sum_ {i = 1} ^ {N _ {S}} \sum_ {j \neq i} ^ {N _ {S}} k (\boldsymbol {s} _ {i}, \boldsymbol {s} _ {j}; f _ {\boldsymbol {\theta}}) \\ + \frac {1}{N _ {T} (N _ {T} - 1)} \sum_ {i = 1} ^ {N _ {T}} \sum_ {j \neq i} ^ {N _ {T}} k (\boldsymbol {t} _ {i}, \boldsymbol {t} _ {j}) \\ - \frac {2}{N _ {S} N _ {T}} \sum_ {i = 1} ^ {N _ {S}} \sum_ {j = 1} ^ {N _ {T}} k (\boldsymbol {s} _ {i}, \boldsymbol {t} _ {j}), \\ k (a, b) = \exp \biggl \{\frac {- \| a - b \| _ {2} ^ {2}}{e} \biggr \}, \end{array}\tag{11}
$$

where s and t are the features extracted for the data from source and target domains, respectively. When MMD is used for validation, the validation set combines the train sets or validation sets of source and target domains. Soft neighbourhood density (SND): SND computes the entropy based on the gram matrix of the validation features.

$$
\begin{array}{l} {d (f _ {\boldsymbol {\theta}}, \mathcal {D} _ {V}) = H (\alpha (\boldsymbol {X}, \tau)),} \\ {\boldsymbol {X} = \boldsymbol {v} ^ {T} \boldsymbol {v},} \end{array}\tag{12}
$$

where v are the data features, $\alpha(\cdot)$ and $\tau$ are softmax function and temperature. Here $D_{V}$ can be the train or validation set of source or target domains. Batch nuclear-norm maximisation (BNM):

![](images/7a5f767598d4774736683beb6ef09e9d799588bb13a17acfec6f95dda95fe093.jpg)

![](images/0526df7ecf7b3abbbfc013aae65dd6e71e76d05e53175abdf41dc38ea73f53be.jpg)  
Figure 3: Computation time of UDA validators on (top) Office31-AD and (bottom) VisDA-TV. The clustering-based validators are all significantly more compute-intensive, though it still takes only half a second to compute for a total of 200k datapoints on the VisDA dataset.

BNM was originally a UDA algorithm, which maximises the nuclear norm of the prediction matrix in a batch, being repurposed as a validation criterion.

$$
d (f _ {\boldsymbol {\theta}}, \mathcal {D} _ {V}) = \| \boldsymbol {P} \| _ {*}, \boldsymbol {P} = f _ {\boldsymbol {\theta}} (\mathcal {D} _ {V})\tag{13}
$$

where $P \in R^{N_{V} \times C}$ the prediction matrix of whole data in $D_{V}$ using $f_{\theta}$ . And $\| \cdot \|_{*}$ computes the nuclear norm.

## D.2 Time Complexity

Most validators are very quick to compute, requiring only a loop through the features, logits or predictions or some matrix multiplications on the same. Those requiring the extra clustering step (AMI, ARI, CHI, DBI, FMI, V-Measure and Silhouette) all take significantly longer. Nonetheless, no validator is prohibitively expensive compared to the time required to adapt the models. See Fig. 3 for numbers on two representative datasets.

## D.3 Validator Versions in Main Paper

For the tables and figures in the main document, we present a single version of each validator, the one that gives the highest performance when averaged over algorithms and datasets. However, there are multiple options for each, for example, which data split is used or whether we use features, logits or prediction vectors to compute the score. Table 10 shows which versions are used for each validator.

## E Correlations

Previous works have focused on identifying the validators that have the strongest correlation with the oracle $[25, 1]$ . Our main focus is on finding the ones that select the top-performing models and as we see in the main document, these different methods do not always lead to the same selection. For completeness, we include in Figs. 4 to 7 the weighted Spearman correlations (as used in $[25]$ ) of all validators considered. Additionally, the comparison of train and val splits for validators in terms of correlation is shown in Fig. 8.

Table 10: Summary of which version of each validator is presented in the tables of the main document. $S_V$ : source val split, $T_T$ : target train split, $T_V$ : target val split.

<table><tr><td>Setting</td><td>Option</td><td>RankMe</td><td>AMI</td><td>ARI</td><td>V-Measure</td><td>FMI</td><td>Silhouette</td><td>DBI</td><td>CHI</td><td>BNM</td><td>MMD</td><td>CORAL</td><td>-SND</td><td>IM</td><td>Entropy</td><td>Accuracy/MSE</td></tr><tr><td>UDA (Classification)</td><td>Split Layer</td><td> $S_V + T_V$ Predictions</td><td> $S_V + T_V$ Logits</td><td> $S_V + T_V$ Logits</td><td> $S_V + T_V$ Logits</td><td> $S_V + T_V$ Logits</td><td> $S_V + T_T$ Logits</td><td> $S_V + T_V$ Logits</td><td> $S_V + T_V$ Logits</td><td> $S_V + T_T$ Predictions</td><td> $S_V + T_V$ Predictions</td><td> $S_V + T_V$ Predictions</td><td> $T_T$ Predictions</td><td> $S_V + T_T$ Predictions</td><td> $S_V + T_T$ Predictions</td><td> $S_V$ Predictions</td></tr><tr><td>UDA (Regression)</td><td>Split Layer</td><td> $T_V$ Predictions</td><td> $S_V + T_T$ Features</td><td> $S_V + T_T$ Features</td><td> $S_V + T_T$ Features</td><td> $S_V + T_V$ Features</td><td> $S_V + T_T$ Features</td><td> $S_V + T_V$ Features</td><td> $S_V + T_T$ Logits</td><td> $T_T$ Predictions</td><td> $S_V + T_V$ Predictions</td><td> $S_V + T_T$ Features</td><td> $T_V$ Predictions</td><td> $T_T$ Predictions</td><td> $T_T$ Predictions</td><td> $S_V$ Predictions</td></tr><tr><td>SFDA</td><td>Split Layer</td><td> $T_T$ Predictions</td><td> $T_T$ Features</td><td> $T_V$ Logits</td><td> $T_T$ Features</td><td> $T_T$ Features</td><td> $T_T$ Logits</td><td> $T_T$ Logits</td><td> $T_T$ Features</td><td> $T_T$ Predictions</td><td>-</td><td>-</td><td> $T_V$ Predictions</td><td> $T_T$ Predictions</td><td> $T_T$ Predictions</td><td>-</td></tr><tr><td>TTA (CIFAR10-C)</td><td>Split Layer</td><td> $T_T$ Predictions</td><td> $T_T$ Logits</td><td> $T_T$ Logits</td><td> $T_T$ Logits</td><td> $T_T$ Logits</td><td> $T_T$ Logits</td><td> $T_T$ Features</td><td> $T_T$ Logits</td><td> $T_T$ Predictions</td><td>-</td><td>-</td><td> $T_T$ Predictions</td><td> $T_T$ Predictions</td><td> $T_T$ Predictions</td><td>-</td></tr><tr><td>TTA (Office-Home)</td><td>Split Layer</td><td> $T_T$ Logits</td><td> $T_T$ Features</td><td> $T_T$ Features</td><td> $T_T$ Features</td><td> $T_T$ Features</td><td> $T_T$ Features</td><td> $T_T$ Features</td><td> $T_T$ Features</td><td> $T_T$ Predictions</td><td>-</td><td>-</td><td> $T_T$ Predictions</td><td> $T_T$ Predictions</td><td> $T_T$ Predictions</td><td>-</td></tr></table>

## F Compute Resources

The majority of experiments were run on an 8xA6000 internal cluster machine. The total number of algorithms we have trained and validated in this work is 2,440. Assuming on average the training time is 1h per algorithm, this means 2,440 GPU hours have been used.

![](images/3d1d632148e3604b88c31afeba728d07fd61dda0a1ae47d35e2824b4ca162639.jpg)  
Figure 4: Left: Correlations with target test accuracy on UDA benchmarks. Error bars are standard error across domains. Middle: Average gap between the best model as selected by each validator and the oracle. Right: Maximum gap between the best model as selected by each validator and the oracle.

![](images/fb4cf887654359747299ad4d09b02bf8fc2fd4d3edd646c9bc4b52cda56f1c54.jpg)  
Figure 5: Left: Correlations with target test accuracy on SFDA benchmarks. Error bars are standard error across domains. Middle: Average gap between the best model as selected by each validator and the oracle. Right: Maximum gap between the best model as selected by each validator and the oracle.

![](images/b16abb34e73536d0fd6d7c8e7a5f4f80a9e4a0f4e3e2f137daaa86a58fe007f3.jpg)

Figure 6: Left: Correlations with target test accuracy on TTA CIFAR10-C. Error bars are standard error across domains. Middle: Average gap between the best model as selected by each validator and the oracle. Right: Maximum gap between the best model as selected by each validator and the oracle.  
![](images/e70ade39dfbd16516c03bbf5f611e4436753bac69ea7c71a611c8f3febcb6886.jpg)

![](images/6b27cf4f2fca042780e1ae172f06a26ca82c6905c287e44285295ca70a6dfbd8.jpg)

![](images/9d3d6c88d21837f224c8079c8965149d92d36f38a1b08b1705721079597d5755.jpg)

Figure 7: Left: Correlations with target test accuracy on TTA Office-Home. Error bars are standard error across domains. Middle: Average gap between the best model as selected by each validator and the oracle. Right: Maximum gap between the best model as selected by each validator and the oracle.  
![](images/d6e3922e41e68f3c97cdb4ee517e97c3fa2f639f54d8df4c89b3d503bc38765d.jpg)

![](images/b525dc4bee230bf5c17e13e8628714202c95f8bb4d2a5b94f96e82848574c0e4.jpg)

![](images/f5d32e6670c73d0a306068ded19c79e8ed957eb74c37aa89d86ed34096cbcf89.jpg)  
Figure 8: Comparison of split for evaluation of validation criteria in the UDA (classification) setting. We report the average weighted Spearman rank correlation between each validator and target test accuracy when using the following data splits for computing validators: (orange) target train data and (blue) target validation data.