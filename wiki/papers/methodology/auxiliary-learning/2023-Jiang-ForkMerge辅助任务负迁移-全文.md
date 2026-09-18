---
title: "2023-Jiang-ForkMerge辅助任务负迁移"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/auxiliary-learning/2023-Jiang-ForkMerge辅助任务负迁移.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# ForkMerge: Mitigating Negative Transfer in Auxiliary-Task Learning

Junguang Jiang<sup>∗</sup>, Baixu Chen<sup>∗</sup>, Junwei Pan<sup>§</sup>, Ximei Wang<sup>§</sup>, Dapeng Liu<sup>§</sup>, Jie Jiang<sup>§</sup>, Mingsheng Long<sup>B</sup>

School of Software, BNRist, Tsinghua University, China

<sup>§</sup>Tencent Inc, China

{jjg20,cbx22}@mails.tsinghua.edu.cn, {jonaspan,messixmwang,rocliu,zeus}@tencent.com, mingsheng@tsinghua.edu.cn

## Abstract

Auxiliary-Task Learning (ATL) aims to improve the performance of the target task by leveraging the knowledge obtained from related tasks. Occasionally, learning multiple tasks simultaneously results in lower accuracy than learning only the target task, which is known as negative transfer. This problem is often attributed to the gradient conflicts among tasks, and is frequently tackled by coordinating the task gradients in previous works. However, these optimization-based methods largely overlook the auxiliary-target generalization capability. To better understand the root cause of negative transfer, we experimentally investigate it from both optimization and generalization perspectives. Based on our findings, we introduce ForkMerge, a novel approach that periodically forks the model into multiple branches, automatically searches the varying task weights by minimizing target validation errors, and dynamically merges all branches to filter out detrimental task-parameter updates. On a series of auxiliary-task learning benchmarks, ForkMerge outperforms existing methods and effectively mitigates negative transfer.

## 1 Introduction

Deep neural networks have achieved remarkable success in various machine learning applications, such as computer vision [23, 22], natural language processing [62, 11, 57], and recommendation systems [46]. However, one major challenge in training deep neural networks is the scarcity of labeled data. In recent years, Auxiliary-Task Learning (ATL) has emerged as a promising technique to address this challenge [67, 39, 43]. ATL improves the generalization of target tasks by leveraging the useful signals provided by some related auxiliary tasks. For instance, larger-scale tasks, such as user click prediction, can be utilized as auxiliary tasks to improve the performance of smaller-scale target tasks, such as user conversion prediction in recommendation [47, 36]. Self-supervised tasks on unlabeled data can serve as auxiliary tasks to improve the performance of the target task in computer vision and natural language processing, without requiring additional labeled data [34, 69, 11, 3].

However, in practice, learning multiple tasks simultaneously sometimes leads to performance degradation compared to learning only the target task, a phenomenon known as negative transfer [84, 75]. Even in large language models, negative transfer problems may still exist. For example, RLHF [7], a key component of ChatGPT [57], achieves negative effects on nearly half of the multiple-choice question tasks when post-training GPT-4 [58]. There has been a significant amount of methods proposed to mitigate negative transfer in ATL [71, 79, 15, 39]. Notable previous studies attribute negative transfer to the optimization difficulty, especially the gradient conflicts between different tasks, and propose to mitigate negative transfer by reducing interference between task gradients [79, 15]. Other works focus on selecting the most relevant auxiliary tasks and reducing negative transfer by avoiding task groups with severe task conflicts [71, 17]. However, despite the significant efforts to address negative transfer, its underlying causes are still not fully understood.

In this regard, we experimentally analyze potential causes of negative transfer in ATL from the perspectives of optimization and generalization. From an optimization view, our experiments suggest that gradient conflicts do not necessarily lead to negative transfer. For example, weight decay, a special auxiliary task, can conflict with the target task in gradients but still be beneficial to the target performance. From a generalization view, we observe that negative transfer is more likely to occur when the distribution shift between the multi-task training data and target test data is enlarged.

Based on our above findings, we present a new approach named ForkMerge. Since we cannot know which task distribution combination leads to better generalization in advance, and training models for each possible distribution is prohibitively expensive, we transform the problem of combining task distributions into that of combining model hypotheses. Specifically, we fork the model into multiple branches and optimize the parameters of different branches on diverse data distributions by varying the task weights. Then at regular intervals, we merge and synchronize the parameters of each branch to approach the optimal model hypothesis. In this way, we will filter out harmful parameter updates to mitigate negative transfer and keep desirable parameter updates to promote positive transfer.

The contributions of this work are summarized as follows: (1) We systematically identify the problem and analyze the causes of negative transfer in ATL. (2) We propose ForkMerge, a novel approach to mitigate negative transfer and boost the performance of ATL. (3) We conduct extensive experiments and validate that ForkMerge outperforms previous methods on a series of ATL benchmarks.

## 2 Related Work

## 2.1 Auxiliary-Task Learning

Auxiliary-Task Learning (ATL) enhances a model’s performance on a target task by utilizing knowledge from related auxiliary tasks. The two main challenges in ATL are selecting appropriate auxiliary tasks and optimizing them jointly with the target task. To find the proper auxiliary tasks for ATL, recent studies have explored task relationships by grouping positively related tasks together and assigning unrelated tasks to different groups to avoid task interference [81, 71, 17, 70]. Once auxiliary tasks are determined, most ATL methods create a unified loss by linearly combining the target and auxiliary losses. However, choosing task weights is challenging due to the exponential increase in search space with the number of tasks, and fixing the weight of each task loss can lead to negative transfer [32]. Recent studies propose various methods to automatically choose task weights, such as using one-step or multi-step gradient similarity [15, 39, 9], minimizing representation-based task distance [2] or gradient gap [67], employing a parametric cascade auxiliary network [54], or from the perspective of bargaining game [66]. However, these methods mainly address the optimization difficulty after introducing auxiliary tasks and may overlook the generalization problem.

Recently, AANG [10] formulates a novel searching space of auxiliary tasks and adopts the metalearning technique, which prioritizes target task generalization, to learn single-step task weightings. This parallel finding highlights the importance of the target task generalization and we further introduce the multi-step task weightings to reduce the estimation uncertainty. Another parallel method, ColD Fusion [12], explores collaborative multitask learning and proposes to fuse each contributor’s parameter to construct a shared model. In this paper, we further take into account the diversity of tasks and the intricacies of task relationships and derive a method for combining model parameters from the weights of task combinations.

## 2.2 Multi-Task Learning

Different from ATL, Multi-Task Learning (MTL) aims to improve the performance of all tasks by learning multiple objectives from a shared representation. To facilitate information sharing and minimize task conflict, many multi-task architectures have been designed, including hard-parameter sharing [30, 22, 24] and soft-parameter sharing [51, 64, 16, 46, 44, 48, 72]. Another line of work aims to optimize strategies to reduce task conflict. Methods such as loss balancing and gradient balancing propose to find suitable task weighting through various criteria, such as task uncertainty [28], task loss magnitudes [44], gradient norm [5], and gradient directions [79, 6, 40, 41, 25, 55].

Although MTL methods can be directly used to jointly train auxiliary and target tasks, the asymmetric task relationships in ATL are usually not taken into account in MTL.

## 2.3 Negative Transfer

Negative Transfer (NT) is a widely existing phenomenon in machine learning, where transferring knowledge from the source data or model can have negative impact on the target learner [63, 60, 27]. To mitigate negative transfer, domain adaptation methods design importance sampling or instance weighting strategies to prioritize related source data [75, 83]. Fine-tuning methods filter out detrimental pre-trained knowledge by suppressing untransferable spectral components in the representation [4]. MTL methods use gradient surgery or task weighting to reduce the gradient conflicts across tasks [79, 76, 25, 42]. Different from previous work, we propose to dynamically filter out harmful parameter updates in the training process to mitigate negative transfer. Besides, we provide an in-depth experimental analysis of the causes of negative transfer in ATL, which is rare in this field yet will be helpful for future research.

## 3 Negative Transfer Analysis

Problem and Notation. In this section, we assume that both the target task $\mathcal { T } _ { \mathrm { t g t } }$ and the auxiliary task $\mathcal { T } _ { \mathrm { a u x } }$ are given. Then the objective is to find model parameters θ that achieve higher performance on the target task by joint training with the auxiliary task,

$$
\min _ {\theta} \mathbb {E} _ {\mathcal {T} _ {\mathrm{tgt}}} \mathcal {L} _ {\mathrm{tgt}} (\theta) + \lambda \mathbb {E} _ {\mathcal {T} _ {\mathrm{aux}}} \mathcal {L} _ {\mathrm{aux}} (\theta),\tag{1}
$$

where $\mathcal { L }$ is the training loss, and λ is the relative weighting hyper-parameter between the auxiliary task and the target task. Our final objective is max $\left[ { \mathcal { P } } ( \theta ) \right]$ ], where $\mathcal { P }$ is the relative performance measure for the target task ${ \mathcal { T } } _ { \mathrm { t g t } } ,$ such as the accuracy in classification. Next we define the Transfer Gain to measure the impact of $\mathcal { T } _ { \mathrm { a u x } }$ on $\mathcal { T } _ { \mathrm { t g t } }$

Definition 3.1 (Transfer Gain, TG). Denote the model obtained by some ATL algorithm $\mathcal { A }$ as $\theta _ { \mathcal { A } } ( \mathcal { T } _ { \mathrm { t g t } } , \mathcal { T } _ { \mathrm { a u x } } , \lambda )$ and the model obtained by single-task learning on target task as $\theta ( \mathcal { T } _ { \mathrm { t g t } } )$ . Let $\mathcal { P }$ be the performance measure on the target task $\mathcal { T } _ { \mathrm { t g t } }$ . Then the algorithm A can be evaluated by

$$
T G (\lambda , \mathcal {A}) = \mathcal {P} (\theta_ {\mathcal {A}} (\mathcal {T} _ {\mathrm{tgt}}, \mathcal {T} _ {\mathrm{aux}}, \lambda)) - \mathcal {P} (\theta (\mathcal {T} _ {\mathrm{tgt}})).\tag{2}
$$

Going beyond previous work on Negative Transfer (NT) [75, 84], we further divide negative transfer in ATL into two types.

Definition 3.2 (Weak Negative Transfer, WNT). For some ATL algorithm A with weighting hyper-parameter λ , weak negative transfer occurs if $T G ( \lambda , { \mathcal { A } } ) < 0$

Definition 3.3 (Strong Negative Transfer, SNT). For some ATL algorithm A, strong negative transfer occurs if $\operatorname* { m a x } _ { \lambda > 0 } T G ( \lambda , \mathcal { A } ) < 0$

Figure 1 illustrates the difference between weak negative transfer and strong negative transfer. The most essential difference is that we might be able to avoid weak negative transfer by selecting a proper weighting hyper-parameter $\lambda ,$ yet we cannot avoid strong negative transfer in this way.

Next, we will analyze negative transfer in ATL from two different perspectives: optimization and generalization. We conduct our analysis on a multi-domain image recognition dataset DomainNet [61] with ResNet-18 [23] pre-trained on ImageNet. Specifically, we use task Painting and Quickdraw in DomainNet as target tasks respectively to showcase weak negative transfer and strong negative transfer, and mix all other tasks in DomainNet as auxiliary tasks. We will elaborate on the DomainNet dataset in Appendix C.3 and provide the detailed experiment design in Appendix B.

![](images/909c473028cf18787f098b52e308e8cb0f2c51ef55106adc2fd5abb9f35d4421.jpg)  
Figure 1: Weak Negative Transfer (WNT) vs. Strong Negative Transfer (SNT).

## 3.1 Effect of Gradient Conflicts

It is widely believed that gradient conflicts between different tasks will lead to optimization difficulties [79, 40], which in turn lead to negative transfer. The degree of gradient conflict is usually measured by the Gradient Cosine Similarity [79, 76, 15].

Definition 3.4 (Gradient Cosine Similarity, GCS). Denote $\phi _ { i j }$ as the angle between two task gradients $\mathbf { g } _ { i }$ and $\mathbf { g } _ { j }$ , then we define the gradient cosine similarity as cos $\phi _ { i j }$ and the gradients as conflicting when cos $\phi _ { i j } < 0$

In Figure 2, we plot the correlation curve between gradient cosine similarity and transfer gain. Somewhat counterintuitively, we observe that negative transfer and gradient conflicts are not strongly correlated, and negative transfer might be severer when the task gradients are highly consistent.

## Finding 1. Negative transfer is not necessarily caused by gradient conflicts and gradient conflicts do not necessarily lead to negative transfer.

It seems contradictory to the previous work [79, 15] and the reason is that previous work mainly considers the optimization convergence during training, while in our experiments we further consider the generalization during evaluation (transfer gain is estimated on the validation set). Although the conflicting gradient of the auxiliary task will increase the training loss of the target task and slow down its convergence speed [37], it may also play a role similar to regularization [32], reducing the over-fitting of the target task, thereby reducing its generalization error. To confirm our hypothesis, we repeat the above experiments with the auxiliary task replaced by $L _ { 2 }$ regularization and observe a similar phenomenon as shown in Figure 2(c)-(d), which indicates that the gradient conflict in ATL is not necessarily harmful, as it may serve as a proper regularization.

Figure 2 also indicates that the weighting hyper-parameter λ in ATL has a large impact on negative transfer. A proper λ not only reduces negative transfer but also promotes positive transfer.

![](images/18a99bdbb44815297e5abc6aa6eae1c7e9b774b47ed91379ee0d46eeb92f7bee.jpg)  
Figure 2: The effect of gradient conflicts. The correlation curve between Transfer Gain (TG) and Gradient Cosine Similarity (GCS) under different λ. For a fair comparison, each data point starts from the same model parameters in the middle of the training process and updates with one-step multi-task gradient descent. P and Q are short for Painting and Quickdraw tasks, respectively.

## 3.2 Effect of Distribution Shift

Next, we will analyze negative transfer from the perspective of generalization. We notice that adjusting λ will change the data distribution that the model is fitting. For instance, when $\lambda = 0$ the model only fits the data distribution of the target task, and when $\lambda = 1$ , the model will fit the interpolated distribution of the target and auxiliary tasks. Formally, given the target distribution $\mathcal { T } _ { \mathrm { t g t } }$ and the auxiliary distribution $\mathcal { T } _ { \mathrm { a u x } }$ , the interpolated distribution of the target and auxiliary task is ${ \mathcal { T } } _ { \mathrm { i n t e r } } ,$

$$
\mathcal {T} _ {\mathrm{inter}} \sim (1 - Z) \mathcal {T} _ {\mathrm{tgt}} + Z \mathcal {T} _ {\mathrm{aux}}, Z \sim \mathrm{Bernoulli} (\frac {\lambda}{1 + \lambda}),\tag{3}
$$

where λ is the task-weighting hyper-parameter. Figure 3(a) quantitatively visualizes the distribution shift under different λ using t-SNE [74].

To quantitatively measure the distribution shift in ATL, we introduce the following definitions. Following the notations of [53], we consider multiclass classification with hypothesis space $\mathcal { F }$ of scoring functions $f : \mathcal { X } \times \mathcal { Y } $ R where $f ( x , y )$ indicates the confidence of predicting x as y.

Definition 3.5 (Confidence Score Discrepancy, CSD). Given scoring function hypothesis ${ \mathcal F } ,$ denote the optimal hypothesis on distribution D as $f _ { \mathcal { D } } ^ { * }$ , then confidence score discrepancy between

distribution D and $\mathcal { D } ^ { \prime }$ induced by $\mathcal { F }$ is defined by

$$
d _ {\mathcal {F}} (\mathcal {D}, \mathcal {D} ^ {\prime}) \triangleq 1 - \mathbb {E} _ {x \sim \mathcal {D} ^ {\prime}} \max _ {y \in \mathcal {Y}} f _ {\mathcal {D}} ^ {*} (x, y).\tag{4}
$$

Confidence score discrepancy between training and test data indicates how unconfident the model is on the test data, which is expected to increase when the data shift enlarges [59, 50].

![](images/20daa4e8e3c8a876aa92b08fa005c224f941fec1a3be55a4ad755ef3d8693855.jpg)  
Figure 3: The effect of distribution shift. (a) Visualization of training distribution and test distribution under different λ. (b) For weak negative transfer tasks, as λ increases, Confidence Score Discrepancy (CSD) first drops and then rises and Transfer Gain (TG) is first positive and then negative. For strong negative transfer tasks, CSD increases monotonically and TG remains negative.

Figure 3(b) indicates the correlation between confidence score discrepancy and transfer gain. For weak negative transfer tasks, when λ increases at first, the introduced auxiliary tasks will shift the training distribution towards the test distribution, thus decreasing the confidence score discrepancy between training and test data and improving the generalization of the target task. However, when λ continues to increase, the distribution shift gradually increases, finally resulting in negative transfer. For strong negative transfer tasks, there is a large gap between the distribution of the introduced auxiliary tasks and that of the target task. Thus, increasing λ always enlarges confidence score discrepancy and always leads to negative transfer. In summary,

Finding 2. Negative transfer is likely to occur if the introduced auxiliary task enlarges the distribution shift between training and test data for the target task.

## 4 Methods

In Section 4.1, based on our above analysis, we will introduce how to mitigate negative transfer when the auxiliary task is determined. Then in Section 4.2, we will further discuss how to use the proposed method to select appropriate auxiliary tasks and optimize them jointly with the target task simultaneously.

## 4.1 ForkMerge

In this section, we assume that the auxiliary task $\mathcal { T } _ { \mathrm { a u x } }$ is given. When updating the parameters $\theta _ { t }$ with Equation (1) at training step t, we have

$$
\theta_ {t + 1} (\lambda) = \theta_ {t} - \eta \left(\mathbf {g} _ {\mathrm{tgt}} \left(\theta_ {t}\right) + \lambda \mathbf {g} _ {\text { aux }} \left(\theta_ {t}\right)\right),\tag{5}
$$

where $\eta$ is the learning rate, $\mathbf { g } _ { \mathrm { t g t } }$ and $\mathbf { g } _ { \mathrm { a u x } }$ are the gradients calculated from ${ \mathcal { L } } _ { \mathrm { t g t } }$ and $\mathcal { L } _ { \mathrm { a u x } }$ respectively. Section 3.1 reveals that the gradient conflict between $\mathbf { g } _ { \mathrm { t g t } }$ and $\mathbf { g } _ { \mathrm { a u x } }$ does not necessarily lead to negative transfer as long as λ is carefully tuned and Section 3.2 shows that negative transfer is related to generalization. Thus we propose to dynamically adjust λ according to the target validation performance $\widehat { \mathcal P }$ to mitigate negative transfer:

$$
\max _ {\lambda} \widehat {\mathcal {P}} (\theta_ {t + 1}) = \widehat {\mathcal {P}} (\theta_ {t} - \eta (\mathbf {g} _ {\mathrm{tgt}} (\theta_ {t}) + \lambda \mathbf {g} _ {\mathrm{aux}} (\theta_ {t}))).\tag{6}
$$

![](images/75e361cc2abb8611bc03a06d8d905abaacebfcc70ba83c114ed356b65faa6e7c.jpg)

Figure 4: ForkMerge training pipeline. The model parameters will be forked into two branches, one optimized with the target task loss and the other jointly trained, and be merged at regular intervals of ∆t steps.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 ForkMerge Training Pipeline.

Require: initial model parameter $\theta_0$, total iterations $T$, interval $\Delta t$

Ensure: final model parameter $\theta_T^*$, task relevance $\lambda^*$

fork model into 2 copies $\{\theta^b\}_{b=0}^1$

for $b = 0$ to 1 do

$\theta_0^b \leftarrow \theta_0$ ▷ initialization

end for

while $t &lt; T$ do

for $b = 0$ to 1 do ▷ independent update

for $t' = t$ to $t + \Delta t - 1$ do

$\theta_{t'+1}^b = \theta_{t'}^b - \eta(\mathbf{g}_{\mathrm{tgt}}(\theta_{t'}^b) + b \cdot \mathbf{g}_{\mathrm{aux}}(\theta_{t'}^b))$

end for

end for

$\lambda^* \leftarrow \arg \max_\lambda \widehat{\mathcal{P}}((1 - \lambda)\theta_{t+\Delta t}^0 + \lambda\theta_{t+\Delta t}^1)$ ▷ search $\lambda$ on the validation set

$\theta_{t+\Delta t}^* \leftarrow (1 - \lambda^*)\theta_{t+\Delta t}^0 + \lambda^* \theta_{t+\Delta t}^1$ ▷ merge parameters

for $b = 0$ to 1 do

$\theta_{t+\Delta t}^b \leftarrow \theta_{t+\Delta t}^*$ ▷ synchronize parameters

end for

$t \leftarrow t + \Delta t$

end while
</div>

Equation (6) is a bi-level optimization problem. One common approach is to first approximate $\widehat { \mathcal P }$ with the loss of a batch of data on the validation set, and then use first-order approximation to solve λ [18, 43]. However, these approximations within a single step of gradient descent introduce large noise to the estimation of λ and also increase the risk of over-fitting the validation set. To tackle these issues, we first rewrite Equation (6) equally as

$$
\max _ {\lambda} \widehat {\mathcal {P}} \big ((1 - \lambda) \theta_ {t + 1} (0) + \lambda \theta_ {t + 1} (1) \big),\tag{7}
$$

where $\theta _ { t + 1 } ( 0 ) = \theta _ { t } - \eta \mathbf { g } _ { \mathrm { t g t } } ( \theta _ { t } )$ and $\theta _ { t + 1 } ( 1 ) = \theta _ { t } - \eta ( \mathbf { g } _ { \mathrm { t g t } } ( \theta _ { t } ) + \mathbf { g } _ { \mathrm { a u x } } ( \theta _ { t } ) )$ . The proof is in Appendix A.1. Note that we assume the optimal $\lambda ^ { * }$ satisfies $0 \leq \lambda ^ { * } \leq 1$ , which can be guaranteed by increasing the scale of $\mathcal { L } _ { \mathrm { a u x } }$ when necessary. Yet an accurate estimation of performance $\widehat { \mathcal P }$ in Equation (7) is still computationally expensive and prone to over-fitting, thus we extend the one gradient step to ∆t steps,

$$
\lambda^ {*} = \arg \max _ {\lambda} \widehat {\mathcal {P}} \big ((1 - \lambda) \theta_ {t + \Delta t} (0) + \lambda \theta_ {t + \Delta t} (1) \big).\tag{8}
$$

Algorithm. As shown in Figure 4 and Algorithm 1, the initial model parameters $\theta _ { t }$ at training step t will first be forked into two branches. The first one will be optimized only with the target task loss ${ \mathcal { L } } _ { \mathrm { t g t } }$ for $\Delta t$ iterations to obtain $\theta _ { t + \Delta t } ( 0 )$ , while the other one will be jointly trained for $\Delta t$ iterations to obtain $\theta _ { t + \Delta t } ( 1 )$ . Then we will search the optimal $\lambda ^ { * }$ that linearly combines the above two sets of parameters to maximize the validation performance ${ \widehat { \mathcal { P } } } .$ . When weak negative transfer occurs in the joint training branch, we can select a proper $\lambda ^ { * }$ between 0 and 1. And when strong negative transfer occurs, we can simply set $\lambda ^ { * }$ to 0. Finally, the newly merged parameter $\theta _ { t + \Delta t } ^ { * } = \bar { ( } 1 - \lambda ^ { * } ) \theta _ { t + \Delta t } ( 0 ) + \lambda ^ { * } \theta _ { t + \Delta t } ( 1 )$ will join in a new round, being forked into two branches again and repeating the optimization process for $\lceil \frac { T } { \Delta t } \rceil$ times.

Discussion. Compared to grid searching λ, which is widely used in practice, ForkMerge can dynamically transfer knowledge from auxiliary tasks to the target task during training with varying $\bar { \lambda ^ { * } }$ . In terms of computation cost, ForkMerge has a lower complexity as it only requires training 2 branches while grid searching has a cost proportional to the number of hyper-parameters to be searched.

## 4.2 ForkMerge for Task Selection Simultaneously

When multiple auxiliary tasks are available, we can simply mix all the auxiliary tasks together to form a single auxiliary task. This simple strategy actually works well in most scenarios (see Section 5.2) and is computationally cheap. However, when further increasing the performance is desired, we can also dynamically select the optimal weighting for each auxiliary task. Formally, the objective when optimizing the model for the target task $\mathcal { T } _ { 0 }$ with multiple auxiliary tasks $\{ \mathcal { T } _ { k } \} _ { k = 1 } ^ { K }$ is

$$
\min _ {\theta} \mathbb {E} _ {\mathcal {T} _ {0}} \mathcal {L} _ {0} (\theta) + \sum_ {k = 1} ^ {K} \lambda_ {k} \mathbb {E} _ {\mathcal {T} _ {k}} \mathcal {L} _ {k} (\theta),\tag{9}
$$

where $\textstyle \sum _ { k = 1 } ^ { K } \lambda _ { k } \leq 1$ and $\forall k , \lambda _ { k } \geq 0$ . Using gradient descent to update $\theta _ { t }$ at training step t, we have

$$
\theta_ {t + 1} (\boldsymbol {\lambda}) = \theta_ {t} - \eta \sum_ {k = 0} ^ {K} \lambda_ {k} \mathbf {g} _ {k} (\theta_ {t}),\tag{10}
$$

where $\lambda _ { 0 } = 1$ . Given K task-weighting vectors $\{ \omega ^ { k } \} _ { k = 0 } ^ { K }$ that satisfies $\omega _ { i } ^ { k } = \mathbb { 1 } [ i = k \mathrm { o r } i = 0 ]$ ], i.e., the k-th and 0-th dimensions of $\omega ^ { k }$ are 1 and the rest are 0, and a vector Λ that satisfies

$$
\Lambda_ {k} = \left\{ \begin{array}{c c} 1 - \sum_ {i \neq 0} \lambda_ {i}, & k = 0, \\ \lambda_ {k}, & k \neq 0, \end{array} \right.\tag{11}
$$

then optimizing $\lambda ^ { * }$ in Equation (10) is equivalent to

$$
\boldsymbol {\Lambda} ^ {*} = \arg \max _ {\boldsymbol {\Lambda}} \widehat {\mathcal {P}} \big (\sum_ {k = 0} ^ {K} \Lambda_ {k} \theta_ {t + 1} (\boldsymbol {\omega} ^ {k}) \big).\tag{12}
$$

In Equation (12), the initial model parameters are forked into $K + 1$ branches, where one branch is optimized with the target task, and the other branches are jointly optimized with one auxiliary task and the target task. Then we find the optimal $\boldsymbol { \Lambda } ^ { * }$ that linearly combines the $K + 1$ sets of parameters to maximize the validation performance (see proof of Equation (12) and the detailed algorithm in Appendix A.2). The training computational complexity of Equation 12 is $\mathcal O ( K )$ , which is much lower than the exponential complexity of grid searching, but still quite large. Inspired by the early-stop approximation used in task grouping methods [71], we can prune the forking branches with $\Lambda _ { k } = 0$ (strong negative transfer) and only keep the branches with the largest $K ^ { \prime } < \breve { K }$ values in Λ after the early merge step. In this way, those useless branches with irrelevant auxiliary tasks can be stopped early. Additionally, we introduce a greedy search strategy in Algorithm 3 to further reduce the computation complexity when grid searching all possible values of Λ.

Lastly, we introduce a general form of ForkMerge. Assuming B candidate branches with taskweighting vectors $\pmb { \nu } ^ { b } ( b = 1 , \ldots , B )$ , the goal is to optimize $\overline { { \Lambda } } ^ { \ast } ;$

$$
\overline {{\boldsymbol {\Lambda}}} ^ {*} = \arg \max _ {\overline {{\boldsymbol {\Lambda}}}} \widehat {\mathcal {P}} \big (\sum_ {b = 1} ^ {B} \overline {{\boldsymbol {\Lambda}}} _ {b} \theta_ {t + \Delta t} (\boldsymbol {\nu} ^ {b}) \big).\tag{13}
$$

From a generalization view, the mixture distributions constructed by different ν lead to diverse data shifts from the target distribution, yet we cannot predict which ν leads to better generalization. Thus, we transform the problem of mixture distribution into that of mixture hypothesis [49] and the models trained on different distributions are combined dynamically via $\overline { { \mathbf { A } } } ^ { * }$ to approach the optimal parameters. Here, Equation 12 is a particular case by substituting $B = K + 1$ and $\pmb { \nu } _ { i } ^ { b } = \mathbb { 1 } [ i \overline { { = b - 1 } } \mathrm { o r } i = 0 ]$ By comparison, Equation 13 allows us to introduce human prior into ForkMerge by constructing more efficient branches, and also provides possibilities for combining ForkMerge with previous task grouping methods [81, 71, 17]. The detailed algorithm of Equation 13 can be found in Algorithm 2.

## 5 Experiments

We evaluate the effectiveness of ForkMerge under various settings, including multi-task learning, multi-domain learning, and semi-supervised learning. First, in Section 5.1, we illustrate the prevalence of negative transfer and explain how ForkMerge can mitigate this problem. In Section 5.2, We examine whether ForkMerge can mitigate negative transfer when joint training the auxiliary and target tasks, and compare it with other methods. In Section 5.3, we further use ForkMerge for task selection simultaneously. Experiment details can be found in Appendix C. We will provide additional analysis and comparison experiments in Appendix D. The codebase for both our method and the compared methods will be available at https://github.com/thuml/ForkMerge.

## 5.1 Motivation Experiment

Negative Transfer is widespread across different tasks. In Figure 5 (a), we visualize the transfer gains between 30 task pairs on DomainNet, where the auxiliary and target tasks are equally weighted, and we observe that negative transfer is common in such case (23 of 30 combinations lead to negative transfer). Besides, as mentioned in Definition 3.2 and 3.3, whether negative transfer occurs is related to a specific ATL algorithm, in Figure 5 (b), we observe that negative transfer in all 30 combinations can be successfully avoided when we use ForkMerge algorithm. This observation further indicates the limitation of task grouping methods [71, 17], since they use Equal Weight between tasks and may discard some useful auxiliary tasks.

Mixture of hypotheses is an approximation of mixture of distribution. Figure 6 uses the ternary heatmaps to visualize the linear combination of a set of three models optimized with different task weightings for 25K iterations, including a single-task model and two multi-task models. Similar to mixing distributions for weak negative transfer task Painting (see Figure 3), the transfer gain when mixing models Painting and Painting+Real first increases and then decreases. Also similar to mixing distributions for strong negative transfer task Quickdraw, the transfer gain when mixing models Quickdraw and Quickdraw+Real decreases monotonically. Besides, Figure 6 also indicates a good property of deep models: the loss surfaces of over-parameterized deep neural networks are quite well-behaved and smooth after convergence, which has also been mentioned by previous works [20, 35] and provides an intuitive explanation of the merge step in ForkMerge.

![](images/047a3942925b61d5e4471d39de2607ddb4ceff02a9bd2f21c7c8b8fecca80040.jpg)

![](images/b24bab86e1b2c003f18a5393556071749452a006044a00097565e6d1322d7c49.jpg)

![](images/8c294c192b00a5d65cc1bca2047febfe5b7714e03b014b6ecf9ae788b5d5ccf8.jpg)  
(a) P (WNT)

![](images/18e01bd67468b3b77a7ec6432f71e300bcf10b1fec684835008c2a77b3fc1e60.jpg)  
(b) Q (SNT)  
Figure 5: Negative Transfer on DomainNet. The rows of each matrix represent auxiliary tasks, and the columns represent target tasks. The blue and red cells correspond to negative and positive transfer gain. Deeper colors indicate stronger impacts.  
Figure 6: Ternary heatmap for mixture of model hypotheses. Each triangle vertex represents an optimized model, e.g., P+R is the model jointly optimized with Painting and Real tasks. Each point inside the triangle corresponds to a mixture of model hypotheses and its heat value measures the Transfer Gain (TG).

## 5.2 Use ForkMerge for Joint Optimization

First, we use ForkMerge only for joint training of the target and auxiliary tasks. When datasets contain multiple tasks, we will mix all tasks together to form a single auxiliary task for ForkMerge. Yet for the compared methods, a distinction is still made between different tasks for better performance.

Specifically, we compare ForkMerge with: (1) Single Task Learning (STL); (2) EW, which assigns equal weight to all tasks; (3) GCS [15], an ATL approach using gradient similarity between target and auxiliary tasks; (4) OL\_AUX [39], an ATL approach adjusting the loss weight based on gradient inner product; (5) ARML [67], an ATL approach adjusting the loss weight based on gradient difference; (6) Auto-λ [43], an ATL method that estimates loss weight through finite-difference approximation [18]; (7) Post-train, an ATL method that pre-trains the model on all tasks and then fine-tunes it for each task separately. (8) UW [28], which adjusts weights based on task uncertainty; (9) DWA [44], which adjusts weights based on loss change; (10) MGDA [65], which computes a convex combination of gradients with a minimum norm to balance tasks; (11) GradNorm [5], which rescales the gradient norms of different tasks to the same range; (12) PCGrad [79], which eliminates conflicting gradient components; (13) IMTL [41], which uses an update direction with equal projections on task gradients; (14) CAGrad [40], which optimizes for the average loss and minimum decrease rate across tasks; (15) NashMTL [55], which combines the gradients using the Nash bargaining solution. Since different tasks have varying evaluation metrics, we will report the average per-task performance improvement for each method using $\Delta _ { m }$ , as defined in Appendix C.1.

Auxiliary-Task Scene Understanding. We evaluate on the widely-used multi-task scene understand ing dataset, NYUv2 [68], which contains 3 tasks: 13-class semantic segmentation, depth estimation, and surface normal prediction. Following [55], we use 636, 159 and 654 images for training, validation, and test. Our implementation is based on LibMTL [38] and MTAN [44]. The results are presented in Table 1. Negative transfer is not severe on this dataset, where both segmentation and depth benefit from ATL and only normal task gets worse. In such cases, our method still achieves significant improvement on all tasks. We also find that Post-train serves as a strong baseline in most of our ATL experiments. Its drawback is that it fails to consider the task relationship in the pre-training phase, and suffers from catastrophic forgetting during the fine-tuning process.

Auxiliary-Domain Image Recognition. Further, we evaluate on the widely-used multi-domain image recognition dataset, DomainNet [61], which contains 6 diverse visual domains and approximately 0.6 million images distributed among 345 categories, where the task difference is reflected in the marginal distribution. Our implementation is based on TLlib [26]. As the original DomainNet does not provide a separate validation set, we randomly split 50% data from the test set as the validation set. The results are presented in Table 2. DomainNet contains both positive transfer tasks (Clipart), weak negative transfer tasks (Infograph, Painting, Real, Sketch), and strong negative transfer tasks (Quickdraw). When negative transfer occurs, previous ATL methods lead to severe performance degradation, while our method can automatically avoid strong negative transfer and improve the performance over STL in other cases.

Table 1: Performance on NYUv2 dataset.

<table><tr><td rowspan="2">Methods</td><td colspan="2">Segmentation</td><td colspan="2">Depth</td><td>Normal</td><td rowspan="2"> $\Delta_m \uparrow$ </td></tr><tr><td>mIoU↑</td><td>Pix Acc↑</td><td>Abs Err↓</td><td>Rel Err↓</td><td>Mean↓</td></tr><tr><td>STL</td><td>51.42</td><td>74.14</td><td>41.74</td><td>17.37</td><td>22.82</td><td>-</td></tr><tr><td>EW</td><td>52.13</td><td>74.51</td><td>39.03</td><td>16.43</td><td>24.14</td><td>0.30%</td></tr><tr><td>UW</td><td>52.51</td><td>74.72</td><td>39.15</td><td>16.56</td><td>23.99</td><td>0.63%</td></tr><tr><td>DWA</td><td>52.10</td><td>74.45</td><td>39.26</td><td>16.57</td><td>24.12</td><td>0.07%</td></tr><tr><td>MGDA</td><td>50.79</td><td>73.81</td><td>39.19</td><td>16.25</td><td>23.14</td><td>1.44%</td></tr><tr><td>GradNorm</td><td>52.25</td><td>74.54</td><td>39.31</td><td>16.37</td><td>23.86</td><td>0.56%</td></tr><tr><td>PCGrad</td><td>51.77</td><td>74.72</td><td>38.91</td><td>16.36</td><td>24.31</td><td>0.22%</td></tr><tr><td>IMTL</td><td>52.24</td><td>74.73</td><td>39.46</td><td>15.92</td><td>23.25</td><td>2.10%</td></tr><tr><td>CAGrad</td><td>52.04</td><td>74.25</td><td>39.06</td><td>16.30</td><td>23.39</td><td>1.41%</td></tr><tr><td>NashMTL</td><td>51.73</td><td>74.10</td><td>39.55</td><td>16.50</td><td>23.21</td><td>1.11%</td></tr><tr><td>GCS</td><td>52.67</td><td>74.59</td><td>39.72</td><td>16.64</td><td>24.10</td><td>0.09%</td></tr><tr><td>OL_AUX</td><td>52.07</td><td>74.28</td><td>39.32</td><td>16.30</td><td>23.98</td><td>0.17%</td></tr><tr><td>ARML</td><td>52.73</td><td>74.85</td><td>39.61</td><td>16.65</td><td>23.89</td><td>0.37%</td></tr><tr><td>Auto- $\lambda$ </td><td>52.40</td><td>74.62</td><td>39.25</td><td>16.25</td><td>23.38</td><td>1.17%</td></tr><tr><td>Post-train</td><td>52.08</td><td>74.86</td><td>39.58</td><td>16.77</td><td>22.98</td><td>1.49%</td></tr><tr><td>ForkMerge</td><td>53.67</td><td>75.64</td><td>38.91</td><td>16.47</td><td>22.18</td><td>4.03%</td></tr></table>

Table 2: Performance on DomainNet dataset.

<table><tr><td>Methods</td><td>C</td><td>I</td><td>P</td><td>Q</td><td>R</td><td>S</td><td>Avg</td><td> $\Delta_{m} \uparrow$ </td></tr><tr><td>STL</td><td>77.6</td><td>41.4</td><td>71.8</td><td>73.0</td><td>84.6</td><td>70.2</td><td>69.8</td><td>-</td></tr><tr><td>EW</td><td>78.0</td><td>38.1</td><td>67.2</td><td>50.8</td><td>77.1</td><td>67.0</td><td>63.0</td><td>-9.62%</td></tr><tr><td>UW</td><td>79.1</td><td>35.8</td><td>68.2</td><td>50.5</td><td>77.9</td><td>67.0</td><td>63.1</td><td>-9.98%</td></tr><tr><td>DWA</td><td>78.3</td><td>38.2</td><td>67.8</td><td>51.4</td><td>77.3</td><td>67.2</td><td>63.4</td><td>-9.15%</td></tr><tr><td>MGDA</td><td>78.1</td><td>37.2</td><td>69.2</td><td>51.0</td><td>80.0</td><td>67.3</td><td>63.8</td><td>-8.80%</td></tr><tr><td>GradNorm</td><td>78.4</td><td>38.9</td><td>69.4</td><td>52.9</td><td>79.0</td><td>67.7</td><td>64.4</td><td>-7.68%</td></tr><tr><td>PCGrad</td><td>78.3</td><td>38.0</td><td>68.2</td><td>50.4</td><td>77.4</td><td>67.3</td><td>63.3</td><td>-9.32%</td></tr><tr><td>IMTL</td><td>79.4</td><td>38.6</td><td>68.6</td><td>53.7</td><td>79.3</td><td>67.6</td><td>64.5</td><td>-7.55%</td></tr><tr><td>CAGrad</td><td>79.1</td><td>38.6</td><td>69.4</td><td>53.6</td><td>79.8</td><td>67.6</td><td>64.7</td><td>-7.35%</td></tr><tr><td>NashMTL</td><td>71.8</td><td>32.9</td><td>62.2</td><td>39.5</td><td>73.5</td><td>61.4</td><td>56.9</td><td>-18.8%</td></tr><tr><td>GCS</td><td>74.6</td><td>36.0</td><td>67.6</td><td>56.6</td><td>76.4</td><td>62.3</td><td>62.3</td><td>-11.0%</td></tr><tr><td>OL_AUX</td><td>68.2</td><td>33.5</td><td>65.3</td><td>54.1</td><td>76.3</td><td>60.9</td><td>59.7</td><td>-14.8%</td></tr><tr><td>ARML</td><td>75.6</td><td>36.8</td><td>67.8</td><td>52.4</td><td>77.6</td><td>64.2</td><td>62.4</td><td>-10.7%</td></tr><tr><td>Auto- $\lambda$ </td><td>78.3</td><td>37.8</td><td>70.2</td><td>56.3</td><td>79.7</td><td>67.1</td><td>64.9</td><td>-7.18%</td></tr><tr><td>Post-train</td><td>78.7</td><td>42.3</td><td>72.7</td><td>73.0</td><td>84.7</td><td>71.2</td><td>70.4</td><td>+1.07%</td></tr><tr><td>ForkMerge</td><td>79.9</td><td>42.7</td><td>73.5</td><td>73.0</td><td>85.2</td><td>72.0</td><td>71.1</td><td>+2.00%</td></tr></table>

## 5.3 Use ForkMerge for Task Selection Simultaneously

As mentioned in Section 4.2, when there are multiple auxiliary task candidates, we can use ForkMerge to simultaneously select auxiliary tasks and jointly train them with the target task, which is denoted as ForkMerge<sup>‡</sup>.

Auxiliary-Task Scene Understanding. In NYUv2, we have 2 auxiliary tasks for any target task, thus we can construct 3 branches with different task weights in Equation 12. In this way, we are able to select auxiliary tasks adaptively by learning different Λ for different branches in the merge step. As shown in Table 3, this strategy yields better overall performance.

Auxiliary-Domain Image Recognition. For any target task in DomainNet, we can construct up to 6 branches with different task weights in Equation 12, which is computationally expensive. As mentioned in Section 4.2, we will prune the branches after the first merge step to reduce the computation cost. Table 4 reveals the impact of the pruning strategy. As the number of branches increases, the gain brought by auxiliary tasks will enlarge, while the gain brought by each branch will reduce. Therefore, pruning is an effective strategy to achieve a better balance between performance and efficiency. In practical terms, when confronted with multiple auxiliary tasks, users have the flexibility to tailor the number of branches to align with their available computational resources.

CTR and CTCVR Prediction. We evaluate on AliExpress dataset [36], a recommendation dataset from the industry, which consists of 2 tasks: CTR and CTCVR, and 4 scenarios and more than 100M records. Our implementation is based on MTReclib [85]. For any target task in AliExpress, we can construct up to 8 branches with different task weights, and we prune to 3 branches after the first merge step. The results are presented in Table 5. Note that improving on such a large-scale dataset with auxiliary tasks is quite difficult. Still, ForkMerge achieves the best performance with $\Delta _ { m } = 1 . 3 0 \%$

Table 3: Effect of of branch number on NYUv2. Table 4: Effect of of branch number on DomainNet.

<table><tr><td rowspan="2">Methods</td><td rowspan="2">B</td><td colspan="2">Segmentation</td><td colspan="2">Depth</td><td>Normal</td><td rowspan="2"> $\Delta_{m} \uparrow$ </td></tr><tr><td>mIoU↑</td><td>Pix Acc↑</td><td>Abs Err↓</td><td>Rel Err↓</td><td>Mean↓</td></tr><tr><td>STL</td><td>1</td><td>51.42</td><td>74.14</td><td>41.74</td><td>17.37</td><td>22.82</td><td>-</td></tr><tr><td>EW</td><td>-</td><td>52.13</td><td>74.51</td><td>39.03</td><td>16.43</td><td>24.14</td><td>0.30%</td></tr><tr><td>ForkMerge</td><td>2</td><td>53.67</td><td>75.64</td><td>38.91</td><td>16.47</td><td>22.18</td><td>4.03%</td></tr><tr><td>ForkMerge‡</td><td>3</td><td>54.30</td><td>75.78</td><td>38.42</td><td>16.11</td><td>22.41</td><td>4.59%</td></tr></table>

<table><tr><td>Methods</td><td> $B$ </td><td>C</td><td>I</td><td>P</td><td>Q</td><td>R</td><td>S</td><td> $\Delta_{m} \uparrow$ </td><td> $\frac{\Delta_{m}}{B-1} \uparrow$ </td></tr><tr><td>STL</td><td>1</td><td>77.6</td><td>41.4</td><td>71.8</td><td>73.0</td><td>84.6</td><td>70.2</td><td>-</td><td>-</td></tr><tr><td rowspan="2">ForkMerge</td><td>2</td><td>79.9</td><td>42.7</td><td>73.5</td><td>73.0</td><td>85.2</td><td>72.0</td><td>2.0%</td><td>2.0%</td></tr><tr><td>3</td><td>81.1</td><td>44.0</td><td>73.7</td><td>73.0</td><td>85.2</td><td>72.7</td><td>3.0%</td><td>1.5%</td></tr><tr><td rowspan="2"> $ForkMerge^{\ddagger}$ </td><td>4</td><td>81.1</td><td>44.2</td><td>74.4</td><td>73.1</td><td>85.3</td><td>73.0</td><td>3.3%</td><td>1.1%</td></tr><tr><td>6</td><td>81.3</td><td>44.4</td><td>74.7</td><td>73.2</td><td>85.3</td><td>73.4</td><td>3.6%</td><td>0.7%</td></tr></table>

Semi-Supervised Learning (SSL). We also evaluate on two SSL datasets, CIFAR-10 [31] and SVHN [56]. Following [67], we use Self-supervised Semi-supervised Learning (S4L) [82] as our baseline algorithm and use 2 self-supervised tasks, Rotation [19] and Exempler-MT [14], as our auxiliary tasks. Table 6 presents the test error of S4L using different ATL approaches, along with other SSL methods, and shows that ForkMerge consistently outperforms the compared ATL methods. Note that we do not aim to propose a novel or state-of-the-art SSL method in this paper. Instead, we find that some SSL methods use ATL and the auxiliary task weights have a great impact (see Grid Search in Table 6). Thus, we use ForkMerge to improve the auxiliary task training within the context of SSL.

Table 5: Performance on AliExpress dataset.

<table><tr><td rowspan="2">Methods</td><td colspan="3">CTR</td><td colspan="5">CTCVR</td><td rowspan="2">Avg</td><td rowspan="2"> $\Delta_m \uparrow$ </td></tr><tr><td>ES</td><td>FR</td><td>NL</td><td>US</td><td>ES</td><td>FR</td><td>NL</td><td>US</td></tr><tr><td>STL</td><td>0.7299</td><td>0.7316</td><td>0.7237</td><td>0.7077</td><td>0.8778</td><td>0.8682</td><td>0.8652</td><td>0.8659</td><td>0.7963</td><td>-</td></tr><tr><td>EW</td><td>0.7299</td><td>0.7300</td><td>0.7248</td><td>0.7008</td><td>0.8855</td><td>0.8516</td><td>0.8606</td><td>0.8618</td><td>0.7931</td><td>-0.39%</td></tr><tr><td>UW</td><td>0.7276</td><td>0.7235</td><td>0.7250</td><td>0.7048</td><td>0.8814</td><td>0.8709</td><td>0.8599</td><td>0.8793</td><td>0.7966</td><td>+0.00%</td></tr><tr><td>DWA</td><td>0.7317</td><td>0.7284</td><td>0.7297</td><td>0.7061</td><td>0.8663</td><td>0.8695</td><td>0.8696</td><td>0.8484</td><td>0.7937</td><td>-0.28%</td></tr><tr><td>MGDA</td><td>0.6985</td><td>0.6926</td><td>0.7000</td><td>0.6676</td><td>0.8215</td><td>0.8145</td><td>0.7978</td><td>0.7917</td><td>0.7480</td><td>-5.94%</td></tr><tr><td>GradNorm</td><td>0.7239</td><td>0.7178</td><td>0.7101</td><td>0.7035</td><td>0.8851</td><td>0.8671</td><td>0.8465</td><td>0.8685</td><td>0.7903</td><td>-0.79%</td></tr><tr><td>PCGrad</td><td>0.7209</td><td>0.7193</td><td>0.7199</td><td>0.6892</td><td>0.8563</td><td>0.8621</td><td>0.8479</td><td>0.8413</td><td>0.7821</td><td>-1.76%</td></tr><tr><td>IMTL</td><td>0.7203</td><td>0.7193</td><td>0.7268</td><td>0.6852</td><td>0.8472</td><td>0.8502</td><td>0.8481</td><td>0.8282</td><td>0.7782</td><td>-2.20%</td></tr><tr><td>CAGrad</td><td>0.7280</td><td>0.7271</td><td>0.7223</td><td>0.6996</td><td>0.8712</td><td>0.8650</td><td>0.8417</td><td>0.8648</td><td>0.7900</td><td>-0.77%</td></tr><tr><td>NashMTL</td><td>0.7229</td><td>0.7245</td><td>0.7272</td><td>0.6972</td><td>0.8562</td><td>0.8606</td><td>0.8667</td><td>0.8497</td><td>0.7881</td><td>-1.00%</td></tr><tr><td>GCS</td><td>0.7229</td><td>0.7245</td><td>0.7272</td><td>0.6972</td><td>0.8562</td><td>0.8606</td><td>0.8667</td><td>0.8497</td><td>0.7881</td><td>-0.49%</td></tr><tr><td>OL_AUX</td><td>0.7311</td><td>0.7211</td><td>0.7239</td><td>0.7050</td><td>0.8779</td><td>0.8651</td><td>0.8610</td><td>0.8727</td><td>0.7947</td><td>+0.54%</td></tr><tr><td>ARML</td><td>0.7278</td><td>0.7247</td><td>0.7236</td><td>0.7030</td><td>0.8780</td><td>0.8671</td><td>0.8678</td><td>0.8670</td><td>0.7949</td><td>+0.55%</td></tr><tr><td>Auto- $\lambda$ </td><td>0.7282</td><td>0.7282</td><td>0.7263</td><td>0.7114</td><td>0.8852</td><td>0.8646</td><td>0.8640</td><td>0.8750</td><td>0.7979</td><td>+0.19%</td></tr><tr><td>Post-train</td><td>0.7291</td><td>0.7227</td><td>0.7244</td><td>0.7086</td><td>0.8889</td><td>0.8808</td><td>0.8654</td><td>0.8613</td><td>0.7977</td><td>+0.14%</td></tr><tr><td>ForkMerge $^{\ddagger}$ </td><td>0.7402</td><td>0.7427</td><td>0.7416</td><td>0.7069</td><td>0.8928</td><td>0.8786</td><td>0.8753</td><td>0.8752</td><td>0.8067</td><td>+1.30%</td></tr></table>

Table 6: Peformance (test error) on CIFAR-10 and SVHN datasets.

<table><tr><td>Methods</td><td>CIFAR-10(4000 labels)</td><td>SVHN(1000 labels)</td><td> $\Delta_{m} \uparrow$ </td></tr><tr><td>STL</td><td>20.3</td><td>12.80</td><td>-</td></tr><tr><td>II-Model [33]</td><td>16.4</td><td>7.19</td><td>31.5%</td></tr><tr><td>Mean Teacher [73]</td><td>15.9</td><td>5.65</td><td>38.8%</td></tr><tr><td>VAT [52]</td><td>13.9</td><td>5.63</td><td>43.8%</td></tr><tr><td>Pseudo-Label [34]</td><td>17.8</td><td>7.62</td><td>26.4%</td></tr><tr><td>S4L + EW</td><td>15.7</td><td>7.83</td><td>30.7%</td></tr><tr><td>S4L + GradNorm</td><td>14.1</td><td>7.68</td><td>35.3%</td></tr><tr><td>S4L + GCS</td><td>15.0</td><td>7.02</td><td>35.6%</td></tr><tr><td>S4L + OL_AUX</td><td>16.1</td><td>7.82</td><td>29.8%</td></tr><tr><td>S4L + ARML</td><td>13.7</td><td>5.89</td><td>43.2%</td></tr><tr><td>S4L + Auto- $\lambda$ </td><td>14.2</td><td>6.14</td><td>41.0%</td></tr><tr><td>S4L + Post-train</td><td>15.8</td><td>7.85</td><td>30.4%</td></tr><tr><td>S4L + Grid Search</td><td>13.8</td><td>6.07</td><td>42.3%</td></tr><tr><td>S4L + ForkMerge $^{\ddagger}$ </td><td>13.1</td><td>5.49</td><td>46.3%</td></tr></table>

## 6 Conclusion

Methods have been proposed to mitigate negative transfer in auxiliary-task learning, yet there still lacks an in-depth experimental analysis on the causes of negative transfer. In this paper, we systematically delved into the negative transfer issues and presented ForkMerge, an approach to enable auxiliary-task learning with positive transfer gains. Experimentally, ForkMerge achieves stateof-the-art accuracy on four different auxiliary-task learning benchmarks, while being computationally efficient. We view the integration of previous task grouping methods with our auxiliary task learning approach as a promising avenue for further research.

## Acknowledgements

We would like to thank many colleagues, in particular Yuchen Zhang, Jialong Wu, Haoyu Ma, Yuhong Yang, and Jincheng Zhong, for their valuable discussions. This work was supported by the National Key Research and Development Plan (2020AAA0109201), the National Natural Science Foundation of China (62022050 and 62021002), and the Beijing Nova Program (Z201100006820041).

## References

[1] Liang-Chieh Chen, Yukun Zhu, George Papandreou, Florian Schroff, and Hartwig Adam. Encoder-decoder with atrous separable convolution for semantic image segmentation. In ECCV,

2018.

[2] Shuxiao Chen, Koby Crammer, Hangfeng He, Dan Roth, and Weijie J Su. Weighted training for cross-task learning. In ICLR, 2022.

[3] Ting Chen, Simon Kornblith, Kevin Swersky, Mohammad Norouzi, and Geoffrey Hinton. Big self-supervised models are strong semi-supervised learners. In NeurIPS, 2020.

[4] Xinyang Chen, Sinan Wang, Bo Fu, Mingsheng Long, and Jianmin Wang. Catastrophic forgetting meets negative transfer: Batch spectral shrinkage for safe transfer learning. In NeurIPS, 2019.

[5] Zhao Chen, Vijay Badrinarayanan, Chen-Yu Lee, and Andrew Rabinovich. Gradnorm: Gradient normalization for adaptive loss balancing in deep multitask networks. In ICML, 2018.

[6] Zhao Chen, Jiquan Ngiam, Yanping Huang, Thang Luong, Henrik Kretzschmar, Yuning Chai, and Dragomir Anguelov. Just pick a sign: Optimizing deep multitask models with gradient sign dropout. In NeurIPS, 2020.

[7] Paul F Christiano, Jan Leike, Tom Brown, Miljan Martic, Shane Legg, and Dario Amodei. Deep reinforcement learning from human preferences. In NeurIPS, 2017.

[8] Jia Deng, Wei Dong, Richard Socher, Li-Jia Li, Kai Li, and Li Fei-Fei. Imagenet: A large-scale hierarchical image database. In CVPR, 2009.

[9] Lucio M Dery, Yann Dauphin, and David Grangier. Auxiliary task update decomposition: The good, the bad and the neutral. In ICLR, 2021.

[10] Lucio M Dery, Paul Michel, Mikhail Khodak, Graham Neubig, and Ameet Talwalkar. Aang: Automating auxiliary learning. In ICLR, 2023.

[11] Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. Bert: Pre-training of deep bidirectional transformers for language understanding. In NAACL, 2019.

[12] Shachar Don-Yehiya, Elad Venezian, Colin Raffel, Noam Slonim, Yoav Katz, and Leshem Choshen. Cold fusion: Collaborative descent for distributed multitask finetuning. arXiv preprint arXiv:2212.01378, 2022.

[13] Alexey Dosovitskiy, Lucas Beyer, Alexander Kolesnikov, Dirk Weissenborn, Xiaohua Zhai, Thomas Unterthiner, Mostafa Dehghani, Matthias Minderer, Georg Heigold, Sylvain Gelly, et al. An image is worth 16x16 words: Transformers for image recognition at scale. In ICLR, 2020.

[14] Alexey Dosovitskiy, Jost Tobias Springenberg, Martin Riedmiller, and Thomas Brox. Discriminative unsupervised feature learning with convolutional neural networks. In NeurIPS, 2014.

[15] Yunshu Du, Wojciech M Czarnecki, Siddhant M Jayakumar, Mehrdad Farajtabar, Razvan Pascanu, and Balaji Lakshminarayanan. Adapting auxiliary losses using gradient similarity. arXiv preprint arXiv:1812.02224, 2018.

[16] Chrisantha Fernando, Dylan Banarse, Charles Blundell, Yori Zwols, David Ha, Andrei A. Rusu, Alexander Pritzel, and Daan Wierstra. Pathnet: Evolution channels gradient descent in super neural networks. CoRR, abs/1701.08734, 2017.

[17] Christopher Fifty, Ehsan Amid, Zhe Zhao, Tianhe Yu, Rohan Anil, and Chelsea Finn. Efficiently identifying task groupings for multi-task learning. In NeurIPS, 2021.

[18] Chelsea Finn, Pieter Abbeel, and Sergey Levine. Model-agnostic meta-learning for fast adaptation of deep networks. In ICML, 2017.

[19] Spyros Gidaris, Praveer Singh, and Nikos Komodakis. Unsupervised representation learning by predicting image rotations. In ICLR, 2018.

[20] Ian Goodfellow, Oriol Vinyals, and Andrew Saxe. Qualitatively characterizing neural network optimization problems. In ICLR, 2015.

[21] Priya Goyal, Piotr Dollár, Ross B. Girshick, Pieter Noordhuis, Lukasz Wesolowski, Aapo Kyrola, Andrew Tulloch, Yangqing Jia, and Kaiming He. Accurate, large minibatch SGD: training imagenet in 1 hour. arXiv preprint arXiv:1706.02677, 2017.

[22] Kaiming He, Georgia Gkioxari, Piotr Dollár, and Ross Girshick. Mask r-cnn. In ICCV, 2017.

[23] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep residual learning for image recognition. In CVPR, 2016.

[24] Falk Heuer, Sven Mantowsky, Saqib Bukhari, and Georg Schneider. Multitask-centernet (mcn): Efficient and diverse multitask learning using an anchor free approach. In ICCV, 2021.

[25] Adrián Javaloy and Isabel Valera. Rotograd: Gradient homogenization in multitask learning. In ICLR, 2022.

[26] Junguang Jiang, Baixu Chen, Bo Fu, and Mingsheng Long. Transfer-learning-library. https: //github.com/thuml/Transfer-Learning-Library, 2020.

[27] Junguang Jiang, Yang Shu, Jianmin Wang, and Mingsheng Long. Transferability in deep learning: A survey. arXiv preprint arXiv:2201.05867, 2022.

[28] Alex Kendall, Yarin Gal, and Roberto Cipolla. Multi-task learning using uncertainty to weigh losses for scene geometry and semantics. In CVPR, 2018.

[29] Diederik P. Kingma and Jimmy Ba. Adam: A method for stochastic optimization. In ICLR, 2015.

[30] Iasonas Kokkinos. Ubernet: Training a ‘universal’ convolutional neural network for low-, mid-, and high-level vision using diverse datasets and limited memory. In CVPR, 2017.

[31] Alex Krizhevsky, Geoffrey Hinton, et al. Learning multiple layers of features from tiny images. Technical report, University of Toronto, 2009.

[32] Vitaly Kurin, Alessandro De Palma, Ilya Kostrikov, Shimon Whiteson, and M Pawan Kumar. In defense of the unitary scalarization for deep multi-task learning. In NeurIPS, 2022.

[33] Samuli Laine and Timo Aila. Temporal ensembling for semi-supervised learning. In ICLR, 2017.

[34] Dong-Hyun Lee. Pseudo-label: The simple and efficient semi-supervised learning method for deep neural networks. In ICML, 2013.

[35] Hao Li, Zheng Xu, Gavin Taylor, Christoph Studer, and Tom Goldstein. Visualizing the loss landscape of neural nets. In NeurIPS, 2018.

[36] Pengcheng Li, Runze Li, Qing Da, An-Xiang Zeng, and Lijun Zhang. Improving multi-scenario learning to rank in e-commerce by exploiting task relationships in the label space. In CIKM, 2020.

[37] Baijiong Lin, YE Feiyang, Yu Zhang, and Ivor Tsang. Reasonable effectiveness of random weighting: A litmus test for multi-task learning. In TMLR, 2022.

[38] Baijiong Lin and Yu Zhang. LibMTL: A python library for multi-task learning. arXiv preprint arXiv:2203.14338, 2022.

[39] Xingyu Lin, Harjatin Baweja, George Kantor, and David Held. Adaptive auxiliary task weighting for reinforcement learning. In NeurIPS, 2019.

[40] Bo Liu, Xingchao Liu, Xiaojie Jin, Peter Stone, and Qiang Liu. Conflict-averse gradient descent for multi-task learning. In NeurIPS, 2021.

[41] L Liu, Y Li, Z Kuang, J Xue, Y Chen, W Yang, Q Liao, and Wayne Zhang. Towards impartial multi-task learning. In ICLR, 2021.

[42] Shengchao Liu, Yingyu Liang, and Anthony Gitter. Loss-balanced task weighting to reduce negative transfer in multi-task learning. In AAAI, 2019.

[43] Shikun Liu, Stephen James, Andrew J Davison, and Edward Johns. Auto-lambda: Disentangling dynamic task relationships. In TMLR, 2022.

[44] Shikun Liu, Edward Johns, and Andrew J Davison. End-to-end multi-task learning with attention. In CVPR, 2019.

[45] Ilya Loshchilov and Frank Hutter. SGDR: stochastic gradient descent with warm restarts. In ICLR, 2017.

[46] Jiaqi Ma, Zhe Zhao, Xinyang Yi, Jilin Chen, Lichan Hong, and Ed H Chi. Modeling task relationships in multi-task learning with multi-gate mixture-of-experts. In SIGKDD, 2018.

[47] Xiao Ma, Liqin Zhao, Guan Huang, Zhi Wang, Zelin Hu, Xiaoqiang Zhu, and Kun Gai. Entire space multi-task model: An effective approach for estimating post-click conversion rate. In SIGIR, 2018.

[48] Kevis-Kokitsi Maninis, Ilija Radosavovic, and Iasonas Kokkinos. Attentive single-tasking of multiple tasks. In CVPR, 2019.

[49] Yishay Mansour, Mehryar Mohri, and Afshin Rostamizadeh. Domain adaptation with multiple sources. In NIPS, 2008.

[50] Matthias Minderer, Josip Djolonga, Rob Romijnders, Frances Hubis, Xiaohua Zhai, Neil Houlsby, Dustin Tran, and Mario Lucic. Revisiting the calibration of modern neural networks. In NeurIPS, 2021.

[51] Ishan Misra, Abhinav Shrivastava, Abhinav Gupta, and Martial Hebert. Cross-stitch networks for multi-task learning. In CVPR, 2016.

[52] Takeru Miyato, Shin-ichi Maeda, Masanori Koyama, and Shin Ishii. Virtual adversarial training: a regularization method for supervised and semi-supervised learning. In TPAMI, 2018.

[53] Mehryar Mohri and Andres Muñoz Medina. New analysis and algorithm for learning with drifting distributions. In International Conference on Algorithmic Learning Theory, 2012.

[54] Aviv Navon, Idan Achituve, Haggai Maron, Gal Chechik, and Ethan Fetaya. Auxiliary learning by implicit differentiation. In ICLR, 2021.

[55] Aviv Navon, Aviv Shamsian, Idan Achituve, Haggai Maron, Kenji Kawaguchi, Gal Chechik, and Ethan Fetaya. Multi-task learning as a bargaining game. In ICML, 2022.

[56] Yuval Netzer, Tao Wang, Adam Coates, Alessandro Bissacco, Bo Wu, and Andrew Y Ng. Reading digits in natural images with unsupervised feature learning. In NeurIPS, 2011.

[57] OpenAI. Introducing chatgpt, 2022.

[58] OpenAI. Gpt-4 technical report, 2023.

[59] Yaniv Ovadia, Emily Fertig, Jie Ren, Zachary Nado, David Sculley, Sebastian Nowozin, Joshua Dillon, Balaji Lakshminarayanan, and Jasper Snoek. Can you trust your model’s uncertainty? evaluating predictive uncertainty under dataset shift. In NeurIPS, 2019.

[60] Sinno Jialin Pan and Qiang Yang. A survey on transfer learning. In TKDE, 2010.

[61] Xingchao Peng, Qinxun Bai, Xide Xia, Zijun Huang, Kate Saenko, and Bo Wang. Moment matching for multi-source domain adaptation. ICCV, 2019.

[62] Alec Radford, Karthik Narasimhan, Tim Salimans, and Ilya Sutskever. Improving language understanding by generative pre-training. Technical report, OpenAI, 2018.

[63] Michael T. Rosenstein. To transfer or not to transfer. In NeurIPS, 2005.

[64] Andrei A. Rusu, Neil C. Rabinowitz, Guillaume Desjardins, Hubert Soyer, James Kirkpatrick, Koray Kavukcuoglu, Razvan Pascanu, and Raia Hadsell. Progressive neural networks. CoRR, abs/1606.04671, 2016.

[65] Ozan Sener and Vladlen Koltun. Multi-task learning as multi-objective optimization. In NeurIPS, 2018.

[66] Aviv Shamsian, Aviv Navon, Neta Glazer, Kenji Kawaguchi, Gal Chechik, and Ethan Fetaya. Auxiliary learning as an asymmetric bargaining game. arXiv preprint arXiv:2301.13501, 2023.

[67] Baifeng Shi, Judy Hoffman, Kate Saenko, Trevor Darrell, and Huijuan Xu. Auxiliary task reweighting for minimum-data learning. In NeurIPS, 2020.

[68] Nathan Silberman, Derek Hoiem, Pushmeet Kohli, and Rob Fergus. Indoor segmentation and support inference from rgbd images. In ECCV, 2012.

[69] Kihyuk Sohn, David Berthelot, Chun-Liang Li, Zizhao Zhang, Nicholas Carlini, Ekin D Cubuk, Alex Kurakin, Han Zhang, and Colin Raffel. Fixmatch: Simplifying semi-supervised learning with consistency and confidence. In NeurIPS, 2020.

[70] Xiaozhuang Song, Shun Zheng, Wei Cao, James Yu, and Jiang Bian. Efficient and effective multi-task grouping via meta learning on task combinations. In NeurIPS, 2022.

[71] Trevor Standley, Amir Zamir, Dawn Chen, Leonidas J. Guibas, Jitendra Malik, and Silvio Savarese. Which tasks should be learned together in multi-task learning? In ICML, 2020.

[72] Hongyan Tang, Junning Liu, Ming Zhao, and Xudong Gong. Progressive layered extraction (ple): A novel multi-task learning (mtl) model for personalized recommendations. In RecSys, 2020.

[73] Antti Tarvainen and Harri Valpola. Mean teachers are better role models: Weight-averaged consistency targets improve semi-supervised deep learning results. In NeurIPS, 2017.

[74] Laurens Van der Maaten and Geoffrey Hinton. Visualizing data using t-sne. In JMLR, 2008.

[75] Zirui Wang, Zihang Dai, Barnabás Póczos, and Jaime Carbonell. Characterizing and avoiding negative transfer. In CVPR, 2019.

[76] Zirui Wang, Yulia Tsvetkov, Orhan Firat, and Yuan Cao. Gradient vaccine: Investigating and improving multi-task optimization in massively multilingual models. In ICLR, 2021.

[77] Derrick Xin, Behrooz Ghorbani, Justin Gilmer, Ankush Garg, and Orhan Firat. Do current multi-task optimization methods in deep learning even help? In NeurIPS, 2022.

[78] Yang You, Jing Li, Jonathan Hseu, Xiaodan Song, James Demmel, and Cho-Jui Hsieh. Reducing BERT pre-training time from 3 days to 76 minutes. In ICLR, 2020.

[79] Tianhe Yu, Saurabh Kumar, Abhishek Gupta, Sergey Levine, Karol Hausman, and Chelsea Finn. Gradient surgery for multi-task learning. In NeurIPS, 2020.

[80] Sergey Zagoruyko and Nikos Komodakis. Wide residual networks. In BMVC, 2016.

[81] Amir Roshan Zamir, Alexander Sax, William B. Shen, Leonidas J. Guibas, Jitendra Malik, and Silvio Savarese. Taskonomy: Disentangling task transfer learning. In CVPR, 2018.

[82] Xiaohua Zhai, Avital Oliver, Alexander Kolesnikov, and Lucas Beyer. S4l: Self-supervised semi-supervised learning. In ICCV, 2019.

[83] Jing Zhang, Zewei Ding, Wanqing Li, and Philip Ogunbona. Importance weighted adversarial nets for partial domain adaptation. In CVPR, 2018.

[84] Wen Zhang, Lingfei Deng, Lei Zhang, and Dongrui Wu. A survey on negative transfer. IEEE/CAA Journal ofAutomatica Sinica, 2022.

[85] Yongchun Zhu, Yudan Liu, Ruobing Xie, Fuzhen Zhuang, Xiaobo Hao, Kaikai Ge, Xu Zhang, Leyu Lin, and Juan Cao. Learning to expand audience via meta hybrid experts and critics for recommendation and advertising. In KDD, 2021.

## A Algorithm Details

## A.1 ForkMerge

## Proof of Equation (7).

$$
\begin{array}{r l} & {\lambda^ {*} = \arg \max _ {\lambda} \widehat {\mathcal {P}} (\theta_ {t + 1})} \\ & {\quad = \arg \max _ {\lambda} \widehat {\mathcal {P}} (\theta_ {t} - \eta (\mathbf {g} _ {\mathrm{tgt}} (\theta_ {t}) + \lambda \mathbf {g} _ {\mathrm{aux}} (\theta_ {t})))} \\ & {\quad = \arg \max _ {\lambda} \widehat {\mathcal {P}} \big ((\theta_ {t} - \eta \mathbf {g} _ {\mathrm{tgt}} (\theta_ {t})) + \lambda (- \eta \mathbf {g} _ {\mathrm{aux}} (\theta_ {t})) \big)} \\ & {\quad = \arg \max _ {\lambda} \widehat {\mathcal {P}} \big ((1 - \lambda) (\theta_ {t} - \eta \mathbf {g} _ {\mathrm{tgt}} (\theta_ {t})) + \lambda (\theta_ {t} - \eta (\mathbf {g} _ {\mathrm{tgt}} (\theta_ {t}) + \mathbf {g} _ {\mathrm{aux}} (\theta_ {t}))) \big)} \\ & {\quad = \arg \max _ {\lambda} \widehat {\mathcal {P}} \big ((1 - \lambda) \theta_ {t + 1} (0) + \lambda \theta_ {t + 1} (1) \big).} \end{array}
$$

## Remarks on the search step.

We provide two search strategies as follows, and we use the first strategy in our experiments.

• Grid Search: Exhaustively searching the task-weighting hyper-parameter λ through a manually specified subset of the hyper-parameter space, such as {0, 0.2, 0.4, 0.6, 0.8, 1.0}.

• Binary Search: Repeatedly dividing the search interval of λ in half and keep the better hyper-parameter.

Random search, bayesian optimization, gradient-based optimization, and other hyper-parameter optimization methods can also be used here, and they are left to be explored in follow-up work.

In practice, the costs of estimating $\widehat { \mathcal P }$ in the search step are usually negligible. Yet when the amount of data in the validation set is relatively large, we can sample the validation set to reduce the cost of estimating $\widehat { \mathcal P }$

## Remarks on extension from the one gradient step to $\Delta t$ steps.

1. It can effectively reduce the average cost of estimating $\widehat { \mathcal P }$ at each step and avoid over-fitting the validation set.

2. It allows longer-term rewards from auxiliary tasks and leads to safer task transfer. For instance, when the accumulated gradients of some auxiliary tasks are harmful to the final target performance, the merging step can cancel the effect of these auxiliary tasks by setting their associated weights λ to 0, to mitigate strong negative transfer.

3. It increases the risk to produce bad model parameters. However, such risk is still low since deep models usually have smooth loss surfaces after convergence as shown in Section 5.1.

![](images/709871df704ac325b133444204b0aaf53c844483537fb8d2a14cc8b0e02c5f18.jpg)

![](images/023f77b6c9a06f6e4a1174d1a9e236121b0e72586779ec9083639b0316b7cf27.jpg)  
Choice of ∆t (Epochs)

![](images/dbc85c20acddcaf18147f32ea95df9548abf716faebf1f4da78ab6e58a0788ce.jpg)  
Figure 7: Effect of the merging step $\Delta t$ on NYUv2.

Figure 7 illustrates that an appropriate $\Delta t$ can effectively promote the performance of the ForkMerge algorithm, indicating the necessity of the extension from the one gradient step in previous work to $\Delta t$ steps. When ∆t is small, the estimation of λ is short-insight and might fail to remove the harmful parameter updates when negative transfer occurs, which also indicates the limitations of methods that use single-step gradient descent to estimate λ [15, 43]. When $\Delta t$ is large, the risk to get bad model parameters from the linear combination will also increase. Therefore, in our experiment, we use the validation set to pick a proper $\Delta t$ for each dataset and use it for all tasks in this dataset.

## A.2 Use ForkMerge to Select Tasks Simultaneously

Detailed Algorithm. Algorithm 2 provides the general optimization process for any task-weighting vector $\{ \nu ^ { b } \} _ { b = 1 } ^ { B }$ . For Equation (12), we have $\bar { B ^ { \prime } } = K + \bar { 1 }$ and $\pmb { \nu } _ { i } ^ { b } \doteq \mathtt { 1 } [ i = b - \mathrm { \ i } \_ { \mathrm { o r } } i = 0 ]$ . For Equation (13), we have no constraints on B or $\nu ^ { b }$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 ForkMerge Training Pipeline with Multiple Branches
Require: initial model parameter $\theta_0$, task-weighting vector $\{\pmb{\nu}^b\}_{b=1}^B$, total iterations $T$, interval $\Delta t$
Ensure: final model parameter $\theta_T^*$
1: fork model into $B$ copies $\{\theta^b\}_{b=1}^B$
2: for $b = 1$ to $B$ do
3: $\theta_0^b \leftarrow \theta_0$ ▷ initialization
4: end for
5: while $t &lt; T$ do
6:    for $b = 1$ to $B$ do ▷ independent update
7:    for $t' = t$ to $t + \Delta t - 1$ do
8:    $\theta_{t'+1}^b = \theta_{t'}^b - \eta \sum_k \nu_k^b g_k(\theta_{t'})$
9:    end for
10:    end for
11:    $\Lambda^* \leftarrow \arg \max_\Lambda \widehat{\mathcal{P}}(\sum_b \Lambda_b \theta_{t+\Delta t}^b)$
12:    ▷ search $\Lambda$ on the validation set
13:    $\theta_{t+\Delta t}^* \leftarrow \sum_b \Lambda_b^* \theta_{t+\Delta t}^b$
14:    ▷ merge parameters
15:    for $b = 1$ to $B$ do
16:    $\theta_{t+\Delta t}^b \leftarrow \theta_{t+\Delta t}^*$ ▷ synchronize parameters
17:    end for
18:    $t \leftarrow t + \Delta t$
19: end while
</div>

Proof of Equation (12).

The goal of selecting λ<sup>∗</sup> in Equation (10) is to maximize the validation performance of model $\theta _ { t + 1 }$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
$\lambda^{*} = \arg \max_{\lambda}\widehat{\mathcal{P}} (\theta_{t + 1})$ $= \arg \max_{\lambda}\widehat{\mathcal{P}} (\theta_t - \eta \sum_k\lambda_k\mathbf{g}_k(\theta_t))$ //gradient descent  
$= \arg \max_{\lambda}\widehat{\mathcal{P}} (\theta_t - \eta \lambda_0\mathbf{g}_0(\theta_t) - \eta \sum_{k\neq 0}\lambda_k\mathbf{g}_k(\theta_t))$ $= \arg \max_{\lambda}\widehat{\mathcal{P}} (\theta_t - \eta \mathbf{g}_0(\theta_t) - \eta \sum_{k\neq 0}\lambda_k\mathbf{g}_k(\theta_t))$ // $\lambda_0 = 1$ $= \arg \max_{\lambda}\widehat{\mathcal{P}} ((1 - \sum_{k\neq 0}\lambda_k)(\theta_t - \eta \mathbf{g}_0(\theta_t)) + (\sum_{k\neq 0}\lambda_k)(\theta_t - \eta \mathbf{g}_0(\theta_t)) + \sum_{k\neq 0}\lambda_k(-\eta \mathbf{g}_k(\theta_t)))$ // $\sum_{k\neq 0}\lambda_k\leq 1$ $= \arg \max_{\lambda}\widehat{\mathcal{P}} ((1 - \sum_{k\neq 0}\lambda_k)(\theta_t - \eta \mathbf{g}_0(\theta_t)) + \sum_{k\neq 0}\lambda_k(\theta_t - \eta \mathbf{g}_0(\theta_t) - \eta \mathbf{g}_k(\theta_t)))$
</div>

By definitions of Λ and $\{ \omega ^ { k } \} _ { k = 0 } ^ { K }$

$$
\begin{array}{l} \Lambda_ {k} = \left\{ \begin{array}{c c} 1 - \sum_ {i \neq 0} \lambda_ {i}, & k = 0, \\ & \lambda_ {k}, \quad k \neq 0, \end{array} \right. \\ \omega_ {i} ^ {k} = \left\{ \begin{array}{l l} 1, & i = 0 \text {   or   } i = k, \\ 0, & \text { otherwise }, \end{array} \right. \end{array}
$$

we can prove that optimizing λ in Equation (10) is equivalent to optimizing Λ as follows:

$$
\boldsymbol {\Lambda} ^ {*} = \arg \max _ {\boldsymbol {\Lambda}} \widehat {\mathcal {P}} \big (\sum_ {k} \Lambda_ {k} \theta_ {t + 1} (\boldsymbol {\omega} ^ {k}) \big).
$$

## Remarks on the search step.

Grid searching all possible values of Λ is computationally expensive especially when $\| \boldsymbol { \Lambda } \|$ is large. Thus, here we introduce a greedy search strategy in Algorithm 3, which reduces the computation complexity from exponential complexity to $\mathcal { O } ( \Vert \dot { \mathbf { A } } \Vert )$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3 Greedy Search of $\Lambda^{*}$

Require: A list of model parameters $\theta_{1},\ldots,\theta_{B}$ sorted in decreasing order of $\widehat{\mathcal{P}}(\theta_{b})$.

Ensure: optimal linear combination coefficient $\Lambda^{*}$

1: unnormalized combination coefficient $\widetilde{\Lambda} \leftarrow \mathbf{e}_{1}$ ▷ initialization
2: for $b=2$ to $B$ do
3: set upper bound $U \leftarrow \frac{1}{b-1} \sum_{m=1}^{b-1} \widetilde{\Lambda}_{m}$
4: grid search the optimal $\widetilde{\Lambda}_{m}$ in range $[0,U]$ to maximize $\widehat{\mathcal{P}}(\frac{1}{\|\widetilde{\Lambda}\|} \sum_{m=1}^{b} \widetilde{\Lambda}_{m}\theta_{m})$
5: end for
6: $\Lambda^{*} \leftarrow \frac{1}{\|\widetilde{\Lambda}\|} \widetilde{\Lambda}$ ▷ normalization
</div>

## B Analysis Details

In this section, we provide the implementation details of our analysis experiment in Section 3.

We conduct our analysis on the multi-domain image recognition dataset DomainNet [61]. In our analysis, we use task Painting and Quickdraw in DomainNet as examples of weak negative transfer and strong negative transfer, and other tasks (Real, Sketch, Infograph, Clipart) in DomainNet as auxiliary tasks. Details of these tasks are summarized in Table 8. We use ResNet-18 [23] pre-trained on ImageNet [8] for all experiments.

## B.1 Effect of Gradients Conflicts

First, we optimize the model on the target task for $T = 2 5 { \mathrm { K } }$ iterations to obtain $\theta _ { T }$ . We adopt mini-batch SGD with momentum of 0.9 and batch size of 48, and the initial learning rate is set as 0.01 with cosine annealing strategy [45].

![](images/21ecb1894f146302e9e289b841dede1040a8798f25c79aedc610d3c7721f0785.jpg)

![](images/97b224db600298d9a6f8a753f232e3dc9a45aed4b3d9c3a6cb5f09696dae310f.jpg)

![](images/a65daf046cd1f9778e3634d600f74412fbb59284d5c1c42d2d0e4d3b5967738e.jpg)

![](images/4bb21a1a3472eeb70bf284058d39ffe445b4336249e218b306671bcb7d266acf.jpg)  
Figure 8: The distribution of Gradient Cosine Similarity (GCS). P and Q are short for Painting and Quickdraw tasks, respectively.

We repeatedly sample a mini-batch of data and estimate the gradients for the target and auxiliary task $\mathbf { g } _ { \mathrm { t g t } }$ and $\mathbf { g } _ { \mathrm { a u x } } .$ . Figure 8 plots the distribution of gradient cosine similarity (GCS) between $\mathbf { g } _ { \mathrm { t g t } }$ and $\mathbf { g } _ { \mathrm { a u x } } .$ We find that the gradients of different tasks are nearly orthogonal $( \cos \phi _ { i j } \approx 0 )$ in most cases, and highly consistent gradients or severely conflicting gradients are both relatively rare.

Then, we optimize the same $\theta _ { T }$ with one-step multi-task gradient descent estimated from different data to obtain different $\theta _ { T + 1 }$

$$
\theta_ {T + 1} (\lambda) = \theta_ {T} - \eta \left(\mathbf {g} _ {\mathrm{tgt}} \left(\theta_ {T}\right) + \lambda \mathbf {g} _ {\text {aux}} \left(\theta_ {T}\right)\right),\tag{14}
$$

where $\eta = 0 . 0 1$ and λ takes values from $\{ 0 , \frac { 1 } { 1 6 } , \frac { 1 } { 8 } , \frac { 1 } { 4 } , \frac { 1 } { 2 } , 1 \}$ . We evaluate $\theta _ { T + 1 } ( \lambda )$ and $\theta _ { T + 1 } ( 0 )$ on the validation set of the target task to calculate the transfer gain (TG) from single-step multi-task gradient descent

$$
T G (\lambda) = \widehat {\mathcal {P}} (\theta_ {T + 1} (\lambda)) - \widehat {\mathcal {P}} (\theta_ {T + 1} (0)).\tag{15}
$$

Note that we omit the notation of algorithm A in Equation (14) and (15) for simplicity. Then, in Figure 2, we mark the GCS and TG of each data point and fit them with a 3-order polynomial to obtain the corresponding correlation curve.

## B.2 Effect of Distribution Shift

Qualitative Visualization. We visualize by t-SNE [74] in Figure 3(a) the representations of the training and test data by the model $\theta _ { T }$ trained in Section B.1. For better visualization, we only keep the top 10 categories with the highest frequency in DomainNet. To visualize the impact of λ on the interpolated training distribution, we let the frequency of auxiliary task points be proportional to λ. In other words, when the weighing hyper-parameter of the auxiliary task increases, the effect of the auxiliary task on the interpolated distribution will also increase.

Figure 3 provides the t-SNE visualization of training and test distributions when λ takes values from $\{ 0 , \frac { 1 } { 1 6 } , \frac { 1 } { 4 } , 1 \}$ . We observe that for weak negative transfer tasks, when λ initially increases, the area of training distribution can better cover that of the test distribution. But as λ continues to increase, the distribution shift between the test set and the training set will gradually increase. For strong negative transfer tasks, however, the shift between the interpolated training distribution and the test distribution monotonically enlarges as λ increases.

Quantitative Measure. First, we jointly optimize the model on the target task and auxiliary tasks with different weighting hyper-parameter λ for $T = 2 5 { \mathrm { K } }$ iterations to obtain $\theta _ { T } ( \lambda )$ . We adopt the same hyper-parameters as in Section B.1. Then we evaluate $\theta _ { T } ( \lambda )$ on the test set of the target tasks and calculate the average confidence on the test set. We can calculate the confidence score discrepancy (CSD) by Definition 3.5 and the transfer gain (TG) by

$$
T G (\lambda) = \widehat {\mathcal {P}} (\theta_ {T} (\lambda)) - \widehat {\mathcal {P}} (\theta_ {T} (0)).\tag{16}
$$

Again, we omit the notation of algorithm A for simplicity. Finally, we plot the curve between CSD and TG under different λ in Figure 3(b).

## C Experiment Details

## C.1 Definition of $\Delta _ { m }$

Following [55, 37], we report $\Delta _ { m }$ as the performance measure, which is the average per-task performance improvement of method m relative to the STL baseline b. Formally, $\begin{array} { r l } { \Delta _ { m } } & { { } = } \end{array}$ $\begin{array} { r l } { \frac { 1 } { K } \sum _ { k = 1 } ^ { K } ( - 1 ) ^ { z _ { k } } ( M _ { m , k } - M _ { b , k } ) / M _ { b , k } } & { { } } \end{array}$ where $M _ { b , k }$ and $M _ { m , k }$ is the performance of the k-th task obtained by the baseline method b and the compared method m. $z _ { k }$ is set to 0 if a higher value indicates better performance for the k-th task and otherwise 1.

## C.2 Auxiliary-Task Scene Understanding on NYU

Experiment Details. We use DeepLabV3+ architecture [1], where a ResNet-50 network [23] pretrained on the ImageNet dataset [8] with dilated convolutions is used as a shared encoder among tasks and the Atrous Spatial Pyramid Pooling module is used as task-specific head for each task. Following [44, 79], each method is trained for 200 epochs with the Adam optimizer [29] and batch size of 8. The initial learning rate is $1 0 ^ { - 4 }$ and halved to $5 \times 1 0 ^ { - 5 }$ after 100 epochs. In ForkMerge, the parameters are merged every 10 epochs. Table 7 presents the full evaluation results of Table 1.

Table 7: Performance on NYUv2 dataset.

<table><tr><td rowspan="3">Methods</td><td colspan="2">Segmentation</td><td colspan="2">Depth</td><td colspan="5">Normal</td><td rowspan="3"> $\Delta_m \uparrow$ </td></tr><tr><td rowspan="2">mIoU↑</td><td rowspan="2">Pix Acc↑</td><td rowspan="2">Abs Err↓</td><td rowspan="2">Rel Err↓</td><td colspan="2">Angle Distance</td><td colspan="3">Within  $t^\circ$ </td></tr><tr><td>Mean↓</td><td>Median↓</td><td>11.25↑</td><td>22.5↑</td><td>30↑</td></tr><tr><td>STL</td><td>51.42</td><td>74.14</td><td>41.74</td><td>17.37</td><td>22.82</td><td>16.23</td><td>36.58</td><td>62.75</td><td>73.52</td><td>-</td></tr><tr><td>EW</td><td>52.13</td><td>74.51</td><td>39.03</td><td>16.43</td><td>24.14</td><td>17.62</td><td>33.98</td><td>59.63</td><td>70.93</td><td>0.30%</td></tr><tr><td>UW</td><td>52.51</td><td>74.72</td><td>39.15</td><td>16.56</td><td>23.99</td><td>17.36</td><td>34.46</td><td>60.13</td><td>71.32</td><td>0.63%</td></tr><tr><td>DWA</td><td>52.10</td><td>74.45</td><td>39.26</td><td>16.57</td><td>24.12</td><td>17.62</td><td>33.88</td><td>59.72</td><td>71.08</td><td>0.07%</td></tr><tr><td>RLW</td><td>52.88</td><td>74.99</td><td>39.75</td><td>16.67</td><td>23.83</td><td>17.23</td><td>34.76</td><td>60.42</td><td>71.50</td><td>0.66%</td></tr><tr><td>MGDA</td><td>50.79</td><td>73.81</td><td>39.19</td><td>16.25</td><td>23.14</td><td>16.46</td><td>36.15</td><td>62.17</td><td>72.97</td><td>1.44%</td></tr><tr><td>GradNorm</td><td>52.25</td><td>74.54</td><td>39.31</td><td>16.37</td><td>23.86</td><td>17.46</td><td>34.13</td><td>60.09</td><td>71.45</td><td>0.56%</td></tr><tr><td>PCGrad</td><td>51.77</td><td>74.72</td><td>38.91</td><td>16.36</td><td>24.31</td><td>17.66</td><td>33.93</td><td>59.43</td><td>70.62</td><td>0.22%</td></tr><tr><td>IMTL</td><td>52.24</td><td>74.73</td><td>39.46</td><td>15.92</td><td>23.25</td><td>16.64</td><td>35.86</td><td>61.81</td><td>72.73</td><td>2.10%</td></tr><tr><td>GradVac</td><td>52.84</td><td>74.77</td><td>39.48</td><td>16.28</td><td>24.00</td><td>17.49</td><td>34.21</td><td>59.94</td><td>71.26</td><td>0.75%</td></tr><tr><td>CAGrad</td><td>52.04</td><td>74.25</td><td>39.06</td><td>16.30</td><td>23.39</td><td>16.89</td><td>35.35</td><td>61.28</td><td>72.42</td><td>1.41%</td></tr><tr><td>NashMTL</td><td>51.73</td><td>74.10</td><td>39.55</td><td>16.50</td><td>23.21</td><td>16.74</td><td>35.39</td><td>61.80</td><td>72.92</td><td>1.11%</td></tr><tr><td>GCS</td><td>52.67</td><td>74.59</td><td>39.72</td><td>16.64</td><td>24.10</td><td>17.56</td><td>34.04</td><td>59.80</td><td>71.04</td><td>0.09%</td></tr><tr><td>OL_AUX</td><td>52.07</td><td>74.28</td><td>39.32</td><td>16.30</td><td>23.98</td><td>17.87</td><td>33.89</td><td>59.53</td><td>71.08</td><td>0.17%</td></tr><tr><td>ARML</td><td>52.73</td><td>74.85</td><td>39.61</td><td>16.65</td><td>23.89</td><td>17.50</td><td>34.24</td><td>59.87</td><td>71.39</td><td>0.37%</td></tr><tr><td>Auto- $\lambda$ </td><td>52.40</td><td>74.62</td><td>39.25</td><td>16.25</td><td>23.38</td><td>17.20</td><td>34.05</td><td>61.18</td><td>72.05</td><td>1.17%</td></tr><tr><td>Post-train</td><td>52.08</td><td>74.86</td><td>39.58</td><td>16.77</td><td>22.98</td><td>16.48</td><td>36.04</td><td>62.27</td><td>73.20</td><td>1.49%</td></tr><tr><td>ForkMerge</td><td>53.67</td><td>75.64</td><td>38.91</td><td>16.47</td><td>22.18</td><td>15.60</td><td>37.93</td><td>64.29</td><td>74.81</td><td>4.03%</td></tr></table>

## C.3 Auxiliary-Domain Image Recognition on DomainNet

Dataset Details. As the original DomainNet [61] does not provide a separate validation set, we randomly split 50% data from the test set as the validation set, and use the rest 50% data as the test set. For each task, the proportions of training set, validation set, and test set are approximately 70%/15%/15%. Table 8 summarizes the statistics of this dataset. DomainNet is under Custom (research-only, non-commercial) license.

Table 8: Overview of DomainNet dataset.

<table><tr><td>Tasks</td><td>#Train</td><td>#Val</td><td>#Test</td><td>Description</td></tr><tr><td>Clipart</td><td>33.5K</td><td>7.3K</td><td>7.3K</td><td>collection of clipart images</td></tr><tr><td>Real</td><td>120.9K</td><td>26.0K</td><td>26.0K</td><td>photos and real world images</td></tr><tr><td>Sketch</td><td>48.2K</td><td>10.5K</td><td>10.5K</td><td>sketches of specific objects</td></tr><tr><td>Infograph</td><td>36.0K</td><td>7.8K</td><td>7.8K</td><td>infographic images</td></tr><tr><td>Painting</td><td>50.4K</td><td>10.9K</td><td>10.9K</td><td>painting depictions of objects</td></tr><tr><td>Quickdraw</td><td>120.7K</td><td>25.9K</td><td>25.9K</td><td>drawings of game “Quick Draw”</td></tr></table>

Experiment Details. We adopt mini-batch SGD with momentum of 0.9 and batch size of 48. We search the initial learning rate in {0.003, 0.01, 0.03} and adopt cosine annealing strategy [45] to adjust learning rate during training. We adopt ResNet-101 pretrained on ImageNet as the backbone. Each method is trained for 50K iterations. In ForkMerge, the parameters are merged every 12.5K iterations.

## C.4 CTR and CTCVR Prediction on AliExpress

Dataset Details. AliExpress [36] is gathered from the real-world traffic logs of AliExpress search system in Taobao and contains more than 100M records in total. We split the first 90% data in the time sequence to be training set and the rest 5% and 5% to be validation set and test set. AliExpress consists of 2 tasks: click-through rate (CTR) and click-through conversion rate (CTCVR), and 4 scenarios: Spain (ES), French (FR), Netherlands (NL), and America (US). Table 9 summarizes the statistics of this dataset. AliExpress is under Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) license.

Experiment Details. The architecture of most methods is based on ESMM [47], which consists of a single embedding layer shared by all tasks and multiple independent DNN towers for each task. The embedding dimension for each feature field is 128. Each method is trained for 50 epochs using the Adam optimizer, with the batch size of 2048, learning rate of $1 0 ^ { - 3 }$ and weight decay of $1 0 ^ { - 6 }$

Table 9: Overview of AliExpress dataset, where CTR = #Click / #Impression and CTCVR = #Purchase / #Impression.

<table><tr><td>Statistics</td><td>ES</td><td>FR</td><td>NL</td><td>US</td></tr><tr><td>#Product</td><td>8.7M</td><td>7.4M</td><td>6M</td><td>8M</td></tr><tr><td>#Pv</td><td>2M</td><td>1.7M</td><td>1.2M</td><td>1.8M</td></tr><tr><td>#Impression</td><td>31.6M</td><td>27.4M</td><td>17.7M</td><td>27.4M</td></tr><tr><td>#Click</td><td>841K</td><td>535K</td><td>382K</td><td>450K</td></tr><tr><td>#Purchase</td><td>19.1K</td><td>14.4K</td><td>13.8K</td><td>10.9K</td></tr><tr><td>CTR</td><td>2.66%</td><td>2.01%</td><td>2.16%</td><td>1.64%</td></tr><tr><td>CTCVR</td><td>0.60‰</td><td>0.54‰</td><td>0.78‰</td><td>0.40‰</td></tr></table>

## C.5 Semi-supervised Learning on CIFAR10 and SVHN

Dataset Details. Following [67], we first split the original training set of CIFAR10 [31] and SVHN [56] into training set and validation set. Then, we randomly sample labeled images from the training set. Table 10 summarizes the statistics of CIFAR-10 and SVHN.

Table 10: Overview of CIFAR-10 and SVHN datasets.

<table><tr><td>Datasets</td><td>#Labeled</td><td>#Unlabeled</td><td>#Val</td><td>#Test</td></tr><tr><td>CIFAR-10</td><td>4000</td><td>41000</td><td>5000</td><td>10000</td></tr><tr><td>SVHN</td><td>1000</td><td>64931</td><td>7326</td><td>26032</td></tr></table>

Experiment Details. (1) Auxiliary Tasks. Following [82, 67], we consider two self-supervised auxiliary tasks Rotation [19] and Exempler-MT [14]. In Rotation, we rotate each image by [0<sup>◦</sup>, 90<sup>◦</sup>, 180<sup>◦</sup>, 270<sup>◦</sup>] and ask the network to predict the angle. In Exemplar-MT, the model is trained to extract feature invariant to a wide range of image transformations. (2) Hyper-parameters. We adopt Adam [29] optimizer with an initial learning rate of 0.005. We train each method for 200K iterations and decay the learning rate by a factor of 0.2 at 160K iterations. We use Wide ResNet-28-2 [80] as the backbone. In ForkMerge, the parameters are merged every 10K iterations.

## C.6 Data Division Strategy for ForkMerge

As discussed in Section 4.2, in ForkMerge, we can construct branches with different sets of auxiliary tasks. Below we outline the specific data division strategy used in our experiments, which is consistent with previous ATL literature:

• For the NYUv2 dataset, multiple tasks share the same input, but their outputs are different. In this setup, each branch has the same input data, which includes the entire dataset. The distinction between different branches solely lies in the task weighting vector $\{ \nu ^ { b } \} _ { b = 1 } ^ { B }$ <sub>1</sub>.

• For DomainNet, AliExpress, CIFAR-10, and SVHN datasets, different tasks have both different inputs and outputs. In these cases, for each branch, if the task weighting of a specific task is set to 0, the data from that particular task will not be used for training the corresponding branch.

## D Additional Experiments

## D.1 Analysis on the importance of different forking branches

The importance of different forking branches is dynamic. As shown in Figure 9, the relative ratio of each forking branch is dynamic and varies from task to task, which indicates the importance of the dynamic merge mechanism.

## D.2 Analysis on the computation cost

The computation cost of Algorithm 2 is $\mathcal O ( K )$ and the computation cost of the pruned version is O(B). Usually, only one model is optimized in most previous multi-task learning methods, yet their computational costs are not necessarily O(1). Gradient balancing methods, including MGDA [65], GradNorm [5], PCGrad [79], IMTL [41], GradVac [76], CAGrad [40], NashMTL [55], GCS [15], OL\_AUX [39], and ARML [67], require computing gradients of each task, thus leading to O(K) complexity. In addition, calculating the inner product or norm of the gradients will bring a calculation cost proportional to the number of network parameters. A common practical improvement is to compute gradients of the shared representation [65]. Yet the speedup is architecture-dependent, and this technique may degrade performance [55].

![](images/c52c26485c2a83dc86362059e3b04f814cc487c9044f8b2a033706391fc16875.jpg)  
(a) Segmentation  
(b) Depth  
(c) Normal  
Figure 9: Importance of different forking branches during training on NYUv2.

In Figure 10, we also compare the actual training time across these methods on NYUv2. We can observe that ForkMerge does not require more time than most other methods. And considering the significant performance gains it brings, these additional computational costs are also worth it. Furthermore, our fork and merge mechanism enables extremely easy asynchronous optimization which is not straightforward in previous methods, thus the training time of our method can be reduced to O(1) when there are multiple GPUs available.

![](images/f5f79594dc20dfaf199f784d208c53aac05a32afb1b8d49888414d042b72a4ca.jpg)  
Figure 10: Training speed of different MTL methods on NYUv2 (10 repetitions).

## D.3 Analysis on the convergence and variance

Figure 11 plots the validation performance of STL, EW, and ForkMerge throughout the training process on NYUv2. Each curve is obtained by optimizing the same method with 5 different seeds. Compared with single-task learning or minimizing the average loss across all tasks, ForkMerge not only improves the final generalization but also speeds up the convergence and reduces the fluctuations during training.

## D.4 Comparison with grid searching λ

In Section 3, we observe that adjusting the task-weighting hyper-parameter λ can effectively reduce the negative transfer and promote the positive transfer. [77] also suggests that sweeping the task weights should be sufficient for full exploration of the Pareto frontier at least for convex setups and observe no improvements in terms of final performance from previous MTL algorithms compared with grid search.

![](images/3f2e2aa9bc9a1c0b4cfd8167972743eda589df54501579a2631a6a8e84aac373.jpg)

![](images/4ddd731bad57b8de2f770c3397d1295040acc6dc8dd32ec8133d7348561c43e9.jpg)

![](images/c9feda3f8b36709f6cc916d478738b8343d7a7ed580f2a6d4eab0baada04eb2b.jpg)  
Figure 11: Learning curves comparing different methods on NYUv2. Each curve plots the mean and standard deviation of the validation performance of a method with 5 different random seeds.

In Figure 12, we compare the performance of all methods with grid search on NYUv2. In grid search, the weighting hyper-parameter for each task takes values from {0.3, 1.0, 3.0}, and there are 3 tasks in NYUv2, thus there are 27 combinations in total. We find that previous methods simply yield performance trade-off points on the scalarization Pareto front, which has also been observed in previous work [77]. In contrast, our proposed ForkMerge yields point far away from the Pareto front and achieves significant improvement over simply optimizing a weighted average of the losses. One possible reason for the gain is that the task weighting in grid search is fixed during training and takes finite values due to the limitation of computing resources while the task weighting in ForkMerge is dynamic in time and nearly continuous in values, thus can better avoid negative transfer and promote positive transfer.

![](images/ff0b51acedecbef8bddcbf85e671c898be6d40ec508bb8a61694758d8c8a4a2a.jpg)

![](images/bd46d9c43830fc67b1b9e4290733dff84039aa4032965825e309086de5b56c44.jpg)

![](images/5b0eeda82a6787c624370c656aef6cbebea80dfe794123543a32316d3eb01c57.jpg)  
Figure 12: Comparison with grid search on NYUv2. We use mIoU for semantic segmentation, 1/ absolute error for depth estimation, and 1/ mean angle distance for surface normal prediction. We plot 2D projections of the performance profile for each pair of tasks. Top-right is better.

## D.5 Comparison with larger batch size training

In some sense, the multiple branches in ForkMerge increase the equivalent batch size. And it has been revealed that batch size may have a great effect on the performance of deep models [21, 78]. To ablate the influence of batch size, we increase the batch size of the Equal Weighting method. As shown in Table 11, the improvement brought by ForkMerge itself is significantly larger than simply increasing the batch size.

## D.6 ForkMerge with more network architectures

ForkMerge with Vision Transformers. We replace the backbone network ResNet-101 with advanced ViT-Base [13] pretrained on ImageNet-21K and repeat the experiments on the DomainNet dataset (Section 5.2). As demonstrated in Table 12, when employing the Vision Transformer model, which boasts increased capacity, the risk of overfitting with limited data becomes more pronounced.

Table 11: Comparison of different methods with larger batch size training.

<table><tr><td rowspan="3">Methods</td><td rowspan="3">Batch Size</td><td colspan="2">Segmentation</td><td colspan="2">Depth</td><td colspan="5">Normal</td><td rowspan="3"> $\Delta_m\uparrow$ </td></tr><tr><td rowspan="2">mIoU↑</td><td rowspan="2">Pix Acc↑</td><td rowspan="2">Abs Err↓</td><td rowspan="2">Rel Err↓</td><td colspan="2">Angle Distance</td><td colspan="3">Within  $t^\circ$ </td></tr><tr><td>Mean↓</td><td>Median↓</td><td>11.25↑</td><td>22.5↑</td><td>30↑</td></tr><tr><td>EW</td><td>8</td><td>52.13</td><td>74.51</td><td>39.03</td><td>16.43</td><td>24.14</td><td>17.62</td><td>33.98</td><td>59.63</td><td>70.93</td><td>0.30%</td></tr><tr><td>EW</td><td>32</td><td>51.40</td><td>73.99</td><td>38.86</td><td>16.20</td><td>23.99</td><td>17.34</td><td>34.58</td><td>60.08</td><td>70.85</td><td>0.55%</td></tr><tr><td>ForkMerge‡</td><td>8</td><td>54.30</td><td>75.78</td><td>38.42</td><td>16.11</td><td>22.41</td><td>15.72</td><td>37.81</td><td>63.89</td><td>74.35</td><td>4.59%</td></tr></table>

This makes Single Task Learning (STL) less effective and consequently leads to the Equal Weighting (EW) method outperforming STL, causing the Post-train method to fall short of EW and Auto-λ. In this case, ForkMerge still exhibited superior performance, validating its efficacy across different network architectures.

Table 12: Performance on DomainNet by replacing the ResNet-101 architecture with the ViT-Base architecture.

<table><tr><td>Methods</td><td>C</td><td>I</td><td>P</td><td>Q</td><td>R</td><td>S</td><td>Avg</td><td> $\Delta_{m} \uparrow$ </td></tr><tr><td>STL</td><td>75.7</td><td>37.8</td><td>69.0</td><td>72.1</td><td>84.4</td><td>69.0</td><td>68.0</td><td>-</td></tr><tr><td>EW</td><td>81.9</td><td>43.7</td><td>74.0</td><td>71.3</td><td>84.1</td><td>73.0</td><td>71.3</td><td>+5.90%</td></tr><tr><td>Auto- $\lambda$ </td><td>81.3</td><td>44.1</td><td>73.8</td><td>72.1</td><td>84.4</td><td>73.5</td><td>71.5</td><td>+6.62%</td></tr><tr><td>Post-train</td><td>76.2</td><td>38.8</td><td>69.5</td><td>71.7</td><td>83.2</td><td>69.7</td><td>68.2</td><td>+0.51%</td></tr><tr><td>ForkMerge</td><td>83.0</td><td>45.6</td><td>76.3</td><td>73.2</td><td>87.1</td><td>74.7</td><td>73.3</td><td>+8.97%</td></tr></table>

ForkMerge with Multi-task Architectures. ForkMerge is complementary to different multi-task architectures. In Tables 13 and 14, we provide a comparison of different optimization strategies with MTAN [44] and MMoE [46] as architectures, which are widely used in multi-task computer vision tasks and multi-task recommendation tasks respectively. On these specifically designed multi-task architectures, ForkMerge is still significantly better than other methods.

Table 13: Performance on NYUv2 dataset by replacing the DeepLabV3+ architecture with the MTAN architecture.

<table><tr><td rowspan="3">Methods</td><td colspan="2">Segmentation</td><td colspan="2">Depth</td><td colspan="5">Normal</td><td rowspan="3"> $\Delta_m\uparrow$ </td></tr><tr><td rowspan="2">mIoU↑</td><td rowspan="2">Pix Acc↑</td><td rowspan="2">Abs Err↓</td><td rowspan="2">Rel Err↓</td><td colspan="2">Angle Distance</td><td colspan="3">Within  $t^\circ$ </td></tr><tr><td>Mean↓</td><td>Median↓</td><td>11.25↑</td><td>22.5↑</td><td>30↑</td></tr><tr><td>STL</td><td>52.10</td><td>74.42</td><td>40.45</td><td>16.34</td><td>22.35</td><td>15.23</td><td>38.96</td><td>64.56</td><td>74.51</td><td>3.05%</td></tr><tr><td>EW</td><td>53.27</td><td>75.36</td><td>39.37</td><td>16.38</td><td>23.61</td><td>17.00</td><td>35.00</td><td>61.01</td><td>72.07</td><td>1.62%</td></tr><tr><td>GCS</td><td>53.05</td><td>74.79</td><td>39.50</td><td>16.49</td><td>24.05</td><td>17.49</td><td>34.14</td><td>59.88</td><td>71.13</td><td>0.57%</td></tr><tr><td>OL_AUX</td><td>52.47</td><td>74.70</td><td>39.27</td><td>16.39</td><td>23.66</td><td>17.43</td><td>34.49</td><td>59.96</td><td>71.76</td><td>0.82%</td></tr><tr><td>ARML</td><td>52.33</td><td>74.59</td><td>39.46</td><td>16.61</td><td>23.57</td><td>17.41</td><td>34.56</td><td>60.12</td><td>72.04</td><td>0.55%</td></tr><tr><td>Auto-λ</td><td>52.90</td><td>75.03</td><td>39.67</td><td>16.45</td><td>22.71</td><td>15.60</td><td>38.35</td><td>64.09</td><td>73.92</td><td>3.18%</td></tr><tr><td>ForkMerge‡</td><td>55.25</td><td>76.16</td><td>38.45</td><td>16.08</td><td>21.94</td><td>15.22</td><td>38.96</td><td>65.04</td><td>75.33</td><td>5.76%</td></tr></table>

Table 14: Performance on AliExpress dataset by replacing the ESMM architecture with the MMoE architecture.

<table><tr><td rowspan="2">Methods</td><td colspan="4">CTR</td><td colspan="4">CVCTR</td><td rowspan="2">Avg</td><td rowspan="2"> $\Delta_{m} \uparrow$ </td></tr><tr><td>ES</td><td>FR</td><td>NL</td><td>US</td><td>ES</td><td>FR</td><td>NL</td><td>US</td></tr><tr><td>EW</td><td>0.7287</td><td>0.7244</td><td>0.7225</td><td>0.7068</td><td>0.8874</td><td>0.8669</td><td>0.8688</td><td>0.8742</td><td>0.7974</td><td>0.11%</td></tr><tr><td>GCS</td><td>0.7300</td><td>0.7190</td><td>0.7270</td><td>0.7102</td><td>0.8857</td><td>0.8773</td><td>0.8680</td><td>0.8740</td><td>0.7989</td><td>0.29%</td></tr><tr><td>OL_AUX</td><td>0.7265</td><td>0.7283</td><td>0.7264</td><td>0.7146</td><td>0.8849</td><td>0.8750</td><td>0.8710</td><td>0.8770</td><td>0.8005</td><td>0.50%</td></tr><tr><td>ARML</td><td>0.7289</td><td>0.7278</td><td>0.7248</td><td>0.7081</td><td>0.8869</td><td>0.8801</td><td>0.8714</td><td>0.8610</td><td>0.7986</td><td>0.26%</td></tr><tr><td>Auto- $\lambda$ </td><td>0.7269</td><td>0.7273</td><td>0.7256</td><td>0.7111</td><td>0.8827</td><td>0.8811</td><td>0.8721</td><td>0.8726</td><td>0.7999</td><td>0.42%</td></tr><tr><td>ForkMerge $^{\ddagger}$ </td><td>0.7368</td><td>0.7349</td><td>0.7359</td><td>0.7116</td><td>0.8942</td><td>0.8791</td><td>0.8717</td><td>0.8840</td><td>0.8060</td><td>1.20%</td></tr></table>