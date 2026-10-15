---
title: "2023-Brignac-重放样本选择与存储改进"
authors: "Brignac, Daniel; Lobo, Niels; Mahalanobis, Abhijit"
year: 2023
date: 2026-10-15
journal: "WACV 2023 (arXiv:2308.01895)"
source_pdf: "raw/papers/attack-detection/lamda-related/2023-Brignac-ImprovingReplaySampleSelection.pdf"
tags:
  - 类型/论文
  - 主题/持续学习
  - 主题/回放缓冲区
  - 主题/缓冲区规模
  - attack-detection
key_finding: "在固定缓冲 200/500/5120 下系统对照蓄水池/herding/GSS/IPM 四种群体策略×ER/DER/GDumb/ER-ACE：小缓冲下 herding/IPM（每类 |M|/s 均分）普遍优于蓄水池（隐式比例分配）；Table 3 实测蓄水池任务份额偏差 ≤3.5 个百分点，与二项采样波动同量级。另提出按 Kaiser criterion/簇内方差的动态缓冲。"
---

> 本文件为 MinerU 全文机械转换 + 结构化摘要头。公式与表格以原件 PDF 为准。

## 结构化摘要（检索任务：固定存储预算的任务级分配）

**固定 vs 动态缓冲（§3.5，行 77）**：自称首个系统考虑动态缓冲；固定缓冲 |M|（**含 200**），动态缓冲按 intracluster variance / Kaiser criterion 依类别复杂度定每类样本数。

**蓄水池的失衡（行 83、214 + Table 3）**：作者称蓄水池偏向早期任务；**实测（N=200，5 任务）份额 23.5/19.0/16.0/22.0/19.5%**——均匀期望 20%，偏差 ≤3.5 个百分点，σ(均分, N=200)≈2.8%，**其「偏向早期」的表述证据强度有限**（更像采样波动）；但方向上「蓄水池=隐式比例分配、herding/IPM=每类 |M|/s 均分」的对照成立。

**主对照（Table 2）**：N=200 时 herding/IPM 在 FAA/FF 上普遍优于蓄水池（如 ER+Reservoir 15.35 vs ER+Herding 15.94 FAA，Split-CIFAR100）；缓冲增大（5120）后蓄水池逼近 herding/IPM。

**本课题推论**：这是与 N=200 最接近的实证环境：**小缓冲下「均分」胜「隐式比例」**，且随缓冲增大差距收窄——直接支撑我们等额规则在小缓冲下的合理性；同时提示「蓄水池≈比例分配」可作为我们报告中比例臂的实现方式之一。

**不可直接声称的内容**：其对照在类增量图像基准（每任务类数相同），「等额」与「比例」在均衡流上重合，真正被对照的是选择策略而非配额规则；我们年度流若各年度样本量不等，等额与比例的分歧才真正出现，需自建对照。
# Improving Replay Sample Selection and Storage for Less Forgetting in Continual Learning

Daniel Brignac University of Arizona Tucson, Arizona dbrignac@arizona.edu

Niels Lobo University of Central Florida Orlando, Florida niels@cs.ucf.edu

Abhijit Mahalanobis University of Arizona Tucson, Arizona amahalan@arizona.edu

## Abstract

Continual learning seeks to enable deep learners to train on a series of tasks of unknown length without suffering from the catastrophic forgetting ofprevious tasks. One effective solution is replay, which involves storing few previous experiences in memory and replaying them when learning the current task. However, there is still room for improvement when it comes to selecting the most informative samples for storage and determining the optimal number of samples to be stored. This study aims to address these issues with a novel comparison of the commonly used reservoir sampling to various alternative population strategies and providing a novel detailed analysis of how to find the optimal number ofstored samples.

## 1. Introduction

Deep learning has revolutionized the field of computer vision, achieving human-like capabilities of image understanding and perception. Unlike humans, however, deep learners consistently struggle to adopt new knowledge while maintaining performance on previously learned tasks. This is the problem known as catastrophic forgetting [25] in which a learner’s performance significantly diminishes as it acquires knowledge for new tasks. This motivates the study of continual learning [30, 38] to address the problem of catastrophic forgetting.

In continual learning, a learner is presented with a sequence of tasks of unknown length where the only data available is that of the current task at hand. As new tasks arrive, we wish to learn each new task while preserving the knowledge learned from previous tasks. During inference, we may be presented with data from any of the previously learned tasks, thus the retention of previous knowledge is imperative when adapting to new tasks.

The inference stage primarily comes in three flavors: task-incremental learning (task-IL), domain-incremental learning (domain-IL) and class-incremental learning (class-IL) [39]. Task-IL and domain-IL are generally considered the easier scenarios as we are either given the task-ID at test time in task-IL, or we must only solve for the current task at hand in domain-IL. Class-IL is significantly more challenging as we must infer for all tasks seen so far without the revealing of a task-ID. Because of this, class-IL has become a primary focus of recent continual learning works [3, 27, 5, 36].

Replay [29, 32, 4] is a commonly used approach to remedy the problem of catastrophic forgetting in both class-IL and task-IL. The concept of replay draws inspiration from Complementary Learning Systems theory of humans which posits that recent experiences stored in the hippocampus develop connections to the neocortex that become ingrained over time to eventually be encoded in long-term memory [24, 13]. As such, when replay is employed in artificial learners, a small amount of previously learned data is stored in memory to then be “replayed” during the training of the current task to emphasize the previously encoded connections of the learner and thus avoid forgetting.

When using replay methods, it is important to have a small canonical set of exemplars stored in memory that effectively capture the underlying class distributions of the dataset. Thus, the selection of which samples to store is a non-trivial task. Previous replay methods rely on reservoir sampling [32, 4, 1, 5, 2] to populate memory with past data. As reservoir sampling is a random sampling method, this could lead to the storage of redundant and potentially insignificantly informative data points in memory causing replay methods to not perform to their maximal capability as recently demonstrated in [37, 43].

There is also no consensus regarding how many samples should be stored to be used for replay. Naturally, as we store more samples in memory, we expect performance to increase, however, as this number grows, we start to deviate from the constraints of continual learning where we seek to store minimal information. There must exist some small optimal number of samples to be stored to make maximum

use of replay methods.

In this work we study the two questions which samples to store, and how many samples should be stored in memory by comparing the commonly used approach of reservoir sampling to three other memory population strategies. We show through extensive empirical evaluation that reservoir sampling leads to greater forgetting when compared with more strategic population approaches. We additionally detail two methods to address the question of how many samples should be stored based on an analysis of significant eigenvectors and eigenvalues. We proceed to show that memory populated according to these two criteria leads to overall more competitiveness and better performance of all population strategies.

## 2. Related Works

Continual learning methods can generally be grouped into three categories: (i) regularization methods, (ii) architectural methods and (iii) replay methods. Regularization methods introduce a new loss term meant to penalize significant drift from previously learned parameters [19, 22, 17, 41]. Architectural methods seek to adapt existing network architectures such that various portions of the model contain global and/or shared knowledge while others contain task-specific knowledge [26, 44, 35, 33, 27]. Historically, regularization methods and architectural methods underperform when compared directly to replay methods further motivating the study of and improvements to replay.

In replay methods, we are allowed to store some small subset of data in a memory buffer and selectively “replay” samples from this buffer when training on the current task to maintain previous task performance. Earlier works include [23] and [10], both of which use the memory buffer as a constraint on gradient updates to ensure that loss remains low on the buffer samples. These gradient-based methods for replay in general show poor performance when compared to experience replay methods [29, 32, 4, 1, 9, 7, 5]. In experience replay, it is common practice to store any of the raw data sample, the label, the logits, or a combination of all three. All the the aforementioned experience replay methods select the samples to be stored by some random sampling method, such as reservoir sampling or uniform sampling, leading to the potential storage of insignificant data.

A number of previous works suggest to either populate the memory buffer with some fixed arbitrary number of samples as new classes are encountered or to empirically find optimal buffer size for a desired task performance [1, 31]. These methods for expanding the buffer are rooted in heuristics and thus not necessarily optimal further motivating the study for optimal growth of the buffer for learning new tasks.

## 3. Methodology

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Memory Buffer Population

Input: T,  $D_{t}$ , M, buffer size (if not dynamic), populate  $\in$  {reservoir, herding, GSS, IPM}, training-strategy

 $M \leftarrow \emptyset$ 

for t in T do

    for minibatch in  $D_{t}$  do

    if  $M = \emptyset$  then

    train( $D_{t}$ ) according to training-strategy

    if populate  $\in$  {reservoir, GSS}, then

    $M \leftarrow$  populate(minibatch, buffer size)

    else

    train( $D_{t} \cup M$ ) according to training-strategy

    if populate  $\in$  {reservoir, GSS}, then

    $M \leftarrow$  populate(minibatch, buffer size)

    if populate  $\in$  {herding, IPM}, then

    $M \leftarrow$  populate( $D_{t}$ , buffer size)
</div>

Consider a sequence of $\tau$ tasks where each task has an associated dataset $\begin{array} { r c l } { \mathcal { D } _ { t } } & { = } & { \{ ( x _ { i } ^ { t } , y _ { i } ^ { t } ) \} } \end{array}$ for each $t \_ \in$ $\{ 1 , 2 , . . . , T \}$ and $i = 1 , . . . , N _ { t }$ where $\boldsymbol { x } _ { i } ^ { t }$ denotes the $i ^ { t h }$ sample of the $t ^ { t h }$ task, $y _ { i } ^ { t }$ its associated ground truth label, and $N _ { t }$ the number of samples in task t. We assume each task t contains a unique, non-overlapping set of classes drawn from an i.i.d distribution. In our continual learning formulation, we seek to sequentially learn each $\mathcal { D } _ { t }$ in an offline setting while maintaining performance on every $\mathcal { D } _ { k }$ for $k < t$ by employing a memory buffer M which is populated according to a specific population strategy. For $t = 1$ we train only on $\mathcal { D } _ { t }$ and for $t > 1$ , we train on $\mathcal { D } _ { t } \cup \mathcal { M }$

Since we are primarily concerned with strategic buffer population, the training method in which we perform continual learning is agnostic of the memory buffer population. Thus, we can use any training strategy along with any buffer population strategy studied herein. We give an overview of each population strategy studied and then present a novel scheme to identify how many samples per class should be stored in M.

We make a note of the distinction between fixed memory buffers and dynamic memory buffers. A fixed memory buffer refers to a buffer M that is fixed in the amount of data it can hold (e.g., a fixed buffer size of 200 can contain a maximum of 200 data samples) while a dynamic buffer may grow in size as new classes are encountered. We denote the size of the fixed buffer as $| { \mathcal { M } } |$ . Traditionally, fixed memory buffers are used whenever replay methods are employed. To the best of our knowledge, we are the first to consider dynamic memory buffers as discussed in Section 3.5. When the buffer is not described to be either fixed or dynamic, the method is agnostic of buffer type. An overview of our described approach is given in Algorithm 1.

## 3.1. Reservoir Sampling

In reservoir sampling [40], we are presented with a stream of data in which we randomly sample from the stream and store each sample in M. If a sample is selected to be stored when M is saturated, we then randomly replace a sample in M with the current selected sample to be stored.

In practice, reservoir sampling tends to favor the storage of samples from earlier encountered tasks. This causes the minimal storage of samples from downstream tasks and an overall unbalanced fixed buffer leading to greater forgetting, particularly when the fixed buffer size is small.

In addition to favoring the storage of earlier encountered task data, reservoir sampling has no mechanism to differentiate between whether a selected sample to be stored is informative or redundant. This leads to the potential storage of insignificant data which in turn can diminish the network’s previously learned decision boundaries [3]. This motivates the study of memory buffer population strategies that can always store the next most informative sample and mitigate forgetting.

## 3.2. The Herding Algorithm

A natural first choice of substitute to reservoir sampling is the herding algorithm as proposed in iCaRL [29] which is an extension of Welling’s herding in [42]. Herding seeks to store samples that best represent the sample’s class mean in feature space. In this sense, the herding algorithm can be thought of as a greedy mean preserving scheme as each selected sample is the closest to its learned class mean.

Formally, for a learned class mean $\mu _ { c }$ in $D .$ dimensional feature space and a mapping from image space to feature space given by $\phi : x _ { i } ^ { t , c } \to { \overline { { \mathbb { R } } } } ^ { D }$ where c denotes the class label of image $\boldsymbol { x } _ { i } ^ { t } ,$ , herding seeks to find the sample $x _ { i } ^ { t , c }$ to add to the class exemplar set $P _ { c }$ in memory buffer M that minimizes the distance to $\mu _ { c }$ as

$$
\underset {x _ {i} ^ {t, c}} {\operatorname{argmin}} \left\| \mu_ {c} - \frac {1}{K} \left(\phi (x _ {i} ^ {t, c}) + \sum_ {j = 1} ^ {K - 1} \phi (p _ {j})\right) \right\| _ {2}\tag{1}
$$

where K denotes the number of samples to be stored for class c and $p _ { j }$ denotes a sample $j$ belonging to $P _ { c }$

Because herding relies on the well learned features for each class to store samples, herding should be performed at the conclusion of each task. This makes herding most suitable for the offline continual learning scenario in which we are allowed multiple iterations through $\mathcal { D } _ { t }$ before moving to the next subsequent task.

## 3.3. Gradient Sample Selection

Gradient sample selection (GSS) is taken from [2] where the objective is to optimize the loss on current task data while maintaining minimal loss on previous task data. To ensure that loss remains low on previous tasks, GSS seeks to maximize the diversity of the buffer M by selecting samples whose gradient angle is maximal compared to all other samples currently stored (i.e., maximizing gradient direction variance). This formulation involves solving a quadratic integer programming of polynomial complexity w.r.t. the buffer size thus, a greedy formulation of GSS is used instead.

In the greedy method, GSS maintains a score $r _ { i }$ for each sample i in the buffer based on the maximal cosine similarity of the current sample with the other samples in the buffer given by

$$
r _ {i} = \max _ {i} \frac {\langle g _ {i} , G \rangle}{| | g _ {i} | | _ {2} | | G | | _ {2}}\tag{2}
$$

where $g _ { i }$ and $G$ denote the gradients of the current sample i and the set of samples stored in M respectively.

While GSS aims to select and store samples based on maintaining maximum variance of gradient direction, there is still a randomness component in determining samples to potentially be replaced. When a sample is selected and deemed appropriate for replacement, there is no guarantee that this is a least informative sample, as determined by GSS, and could thus potentially lead to greater forgetting. In addition, GSS has no mechanism for class balancing as samples are randomly added and replaced which can further hinder performance.

## 3.4. Iterative Projection and Matching

Iterative projection and matching (IPM) [16] is drawn from active learning in which we seek to find the most informative data points for training. Here, we adopt IPM to select the most informative data points for storage in M to address the shortcomings with reservoir sampling while also maintaining a balanced buffer similar to the strategy used in herding.

Let $\begin{array} { r l r } { { \bf A } _ { c } } & { { } \in } & { \mathbb { R } ^ { N _ { c } \times D } } \end{array}$ denote the matrix of features $\phi ( \boldsymbol { x } _ { 1 } ^ { t } ) , . . . , \phi ( \boldsymbol { x } _ { N _ { c } } ^ { t } ) \ \in \ \mathbb { R } ^ { D }$ where $N _ { c }$ denotes the number of samples in class $c , D$ the dimension of features, and $\phi ~ : ~ \mathbb { R } ^ { \mathbf { \hat { H } } \times W \times C } ~ \to ~ \mathbb { R } ^ { D }$ a mapping from image space to feature space $( i . e .$ , the learned network). The ${ \bar { \mathbf { \Gamma } } } _ { n } t h$ row in $A _ { c }$ is formed by $\phi ( x _ { n _ { c } } ^ { t } ) ^ { T }$ . We seek to reduce $\mathbf { A } _ { c }$ to some $\pmb { A } _ { R } \in \mathbb { R } ^ { K \times D }$ where K is the number of samples to be stored from class c.

Let $T \subset \{ 1 , . . . , N _ { c } \}$ with $| T | = K$ be the set of selected samples. Then, we can project the rows of $A _ { c }$ onto the span of the selected rows indexed by T. We denote this operation as $\omega _ { T } ( A _ { c } )$ . As done in [11], we can now cast the replay sample selection problem as the optimization problem

$$
\operatorname * {a r g m i n} _ {| T | = K} | | \boldsymbol {A} _ {c} - \boldsymbol {\omega} _ {T} (\boldsymbol {A} _ {c}) | | _ {F} ^ {2}\tag{3}
$$

where $| | \cdot | | _ { F }$ is the Frobenius norm. This problem is NP-Hard however as we must search all subsets T over A<sub>c</sub> [46]. Thus, we use the IPM [16] algorithm to approximate 3.

We can express $\omega _ { T } ( A _ { c } )$ as a rank-K factorization $U V ^ { T }$ where $U \in \mathbf { \overline { { \mathbb { R } } } } ^ { N _ { c } \times K }$ and $V ^ { T } \in \mathbb { R } ^ { K \times D }$ and modify 3 by recasting it as two sub-problems [16, 15]

$$
(u, v) = \underset {u, v} {\operatorname{argmin}} | | \boldsymbol {A} _ {c} - \boldsymbol {u} \boldsymbol {v} ^ {T} | | _ {F} ^ {2} \text {s.t.} | | \boldsymbol {v} | | = 1\tag{4}
$$

$$
m ^ {(1)} = \underset {m} {\operatorname{argmax}} | \boldsymbol {v} ^ {T} \boldsymbol {\rho} |\tag{5}
$$

where $\pmb { \rho } = \phi ( x _ { n _ { c } } ^ { t } ) / | | \phi ( x _ { n _ { c } } ^ { t } ) | | _ { 2 } , m ^ { ( 1 ) }$ is the index of the first selected data point, and $( x _ { i } ^ { t } , y _ { i } ^ { t } ) _ { m ^ { ( 1 ) } }$ is the selected point to be stored in memory.

IPM also relies on the well learned features of each class for best performance in sample selection and thus must be performed at the conclusion of a task. This also makes IPM most suitable for the offline continual learning scenario.

Similar to herding, we again store $| \mathcal { M } | / s$ samples per class for a balanced and saturated buffer and preserve the most informative samples, as determined by IPM, by deleting the most recently added samples to each class when new data is encountered and must be stored to the fixed buffer.

## 3.5. Dynamic Memory Buffers

Traditionally, when replay methods are used, it is common for the buffer size to be fixed [32, 5, 4]. This fixed buffer size does not take into account the underlying complexity of the data and more specifically, each class within the data. To account for such dataset specific complexities, we allow the buffer to be dynamic, where we add K samples of class c to the buffer using two algorithm agnostic <sup>1</sup> methods we refer to as intracluster variance and Kaiser criterion described below. This idea is motivated by providing a guideline for determining the number of samples needed to represent the data manifold and the different classes within it as opposed to arbitrarily choosing a fixed buffer size.

Intracluster Variance. We assume that the number of images necessary for replay depends on the complexity of the underlying manifold of the data. It is well known that relations between the data points on the high dimensional manifold are preserved when the data is embedded into a lower dimension via norm preserving transformations [6, 12]. For example, the dominant eigenvectors (or principal components) of the space in which the images lie is an example of one such transformation. In fact, the number of eigenvectors needed to represent the data is an indication of the complexity of the manifold, and therefore provides some indication of the number of images required for replay. Another method for estimating the complexity of the manifold is by forming clusters in the data and by observing the change in the average intracluster variance for each cluster.

![](images/68e164fad3f4115031f7a8e3252bac3152f07a02d7bda2111bb6a58ae765d420.jpg)

![](images/716d819723a8caecade560076db1177112174ff4dd9855fdc92b5eb5dd44b957.jpg)  
(a)  
(b)  
Figure 1: (a) Average intracluster variance for varying number of clusters. (b) Average change in intracluster variance for varying number of clusters.

Assume that the data is grouped into K clusters, each with $N _ { j }$ images. Specifically, let $x _ { i , j }$ for $1 \ \leq \ i \ \leq \ N _ { j } ,$ $1 \le j \le K$ represent the $\dot { i } ^ { t h }$ training image of the $j ^ { \dot { t } h }$ cluster. The variance of any given cluster is given by $\begin{array} { r } { \sigma _ { j } ^ { 2 } \ = \ \frac { 1 } { N _ { i } } \sum _ { i = 1 } ^ { N _ { j } } ( x _ { i , j } - \mu _ { j } ) } \end{array}$ where $\begin{array} { r } { \mu _ { j } = \frac { 1 } { N _ { i } } \sum _ { i = 1 } ^ { N _ { j } } x _ { i , j } } \end{array}$ is the mean of the respective cluster. The average variance of all clusters is then simply $\begin{array} { r } { \sigma _ { K } ^ { 2 } = \frac { 1 } { K } \sum _ { j = 1 } ^ { K } \sigma _ { j } ^ { 2 } } \end{array}$ . The premise is that each cluster represents a local region on the manifold where the data is concentrated. As K increases, each cluster becomes more and more compact and their variance $\sigma _ { j } ^ { 2 }$ for $1 \le j \le K$ decreases. This causes the average variance $\sigma _ { K } ^ { 2 }$ to also decrease as shown in Figure 1a using the CIFAR10, CIFAR100 and Tiny-ImageNet datasets [20, 21] and the k-means clustering algorithm. In fact, the change in variance $\Delta _ { K } = \sigma _ { K + 1 } ^ { 2 } - \sigma _ { K } ^ { 2 }$ also tapers asymptotically as K is allowed to increase. Figure 1b shows this behavior and the rate at which the average variance decreases.

We observe that increasing the number of clusters beyond the knee of the curve, 100 for both CIFAR10 and CI-FAR100 and 160 for Tiny-ImageNet, provides diminishing gains in terms of decreasing the variance of each cluster. We assume that each cluster is as compact as possible, and the cluster mean is a good representation of the data that lies within the cluster. Therefore, we choose the number of clusters where the knee of the curve (found using the Kneedle algorithm [34]) in 1a and 1b occur as an indication of the number of representative samples that are required to adequately represent the data manifold.

With this estimate of the number of samples needed for proper representation of the underlying data manifold, we populate the buffer with K samples per class. This allows for the buffer to maintain its class balanced properly and avoid biased sampling from the buffer when training.

<table><tr><td>Dataset</td><td>Mean</td><td>Min.</td><td>Max</td></tr><tr><td>CIFAR10</td><td>248 ± 27</td><td>215</td><td>290</td></tr><tr><td>CIFAR100</td><td>50 ± 8</td><td>28</td><td>69</td></tr><tr><td>TinyImageNet</td><td>59 ± 9</td><td>41</td><td>94</td></tr></table>

Table 1: Kaiser Criterion stats for number of samples required for each class.

When using instracluster variance, one must have access to the entire dataset before training begins. This can be seen as unfair in the context of continual learning since in real world scenarios it would be impossible to view the entire dataset beforehand. We address this concern by using the Kaiser criterion below.

Kaiser Criterion. Instead of finding a global number of samples to be kept for each class as done in intracluster variance, we detail an additional method based on the number of most useful eigenvectors for each class.

Assume that $\mathbf { x } _ { i , c }$ is a d dimensional column vector that represents the $i ^ { t h }$ training image of class c for $1 \leq i \leq$ $N _ { c }$ For each class, we define the data matrix $\begin{array} { r l } { \boldsymbol { A } _ { c } } & { { } = } \end{array}$ $\left[ \mathbf { x } _ { 1 , c } , . . . , \mathbf { x } _ { 1 , N _ { c } } \right]$ , and compute the eigenvalues and eigenvectors of $A _ { c } A _ { c } ^ { T }$ denoted as $\lambda _ { k , c }$ and $\phi _ { k , c } ,$ respectively, for $k = 1 , . . . , d .$ Loosely speaking, the rank of this matrix is a proxy for the number of independent images required to represent the dataset and can thus be viewed as a reduced version of PCA. This in turn is related to the non-singular eigenvalues. Therefore, to determine the minimum number of images required to represent the data, we count the number of non-trivial eigenvalues (ignoring the ones that are zero or close to it). The Kaiser criterion [18] is a common method for selecting the useful eigenvectors which states that only those with eigenvalues greater than 1.0 should be retained for representing the data.

We note that this method of using raw images to form the data matrix is better suited than using network features, as that would always require the network to accurately classify the entire data, which manot not occur if a particular class is difficult for the network to classify.

We report the statistics of the Kaiser criterion for each dataset in Table 1. The benefits of using a dynamic buffer with the Kaiser criterion allow for classes with higher complexity to have more representation in the buffer, which ultimately leads to higher probability of sampling these more complex classes from the buffer and further mitigate forgetting.

Additionally, the Kaiser criterion can be used in an offline manner before the training of each task as the determination for the number of samples to be stored for each class depends only on a specific class’s data matrix. Thus, when new task data is available, we can compute the Kaiser criterion for each individual class by partitioning the task data matrix into class data matrices.

## 4. Experiments

We investigate the performance of each population strategy described above by comparing each scheme under a commonly used suite of replay-based training methods. We test using both a fixed memory buffer with commonly used buffer sizes and the newly proposed dynamic buffer scheme described in Section 3.5. Our primary focus is on the offline class-IL setting. We report offline task-IL results in the supplementary material.

Datasets. We benchmark each population strategy on three commonly used continual learning datasets: split-CIFAR10, split-CIFAR100 and split-Tiny-ImageNet [20, 45, 21]. In split-CIFAR10, the CIFAR10 dataset is split into 5 disjoint tasks where each task contains 2 classes. Split-CIFAR100 splits CIFAR100 into 10 disjoint tasks of 10 classes each. Split-Tiny-ImageNet splits Tiny-ImageNet into 10 disjoint tasks of 20 classes each. We maintain the same order in which classes are split across all tested population strategies and methods.

Compared Methods. Each population strategy studied herein is tested against four commonly compared methods in continual learning literature, namely ER [32], DER [4], GDumb [28], and ER-ACE [5]. Each of the aforementioned methods was state of the art for its time with ER-ACE being the most recently proposed state of the art method for bench-marking of current replay-based continual learning research.

All compared methods use some form of experience replay. For each $t > 1$ , all methods train on the union of task data and data stored in memory as $\mathcal { D } _ { t } \cup \mathcal { M } ,$ except in the case of GDumb where we only populate M in a balanced manner by performing one iteration through each $\mathcal { D } _ { t }$ and proceed to train solely on M at the conclusion of the final task.

Configuration and Hyperparameters. We test each of the buffer population strategies studied herein with the above described methods using the open-source codebase, Mammoth, first introduced in [4]. We use the best configuration for each compared training method when testing performance of each population strategy with a ResNet18 [14] backbone for fair comparisons. Exact hyperparmeter configuration can be found in the supplementary material.

Metrics. We judge performance with the commonly used metrics of final average accuracy (FAA) and final forgetting (FF) given by

$$
F A A = \frac {1}{\mathcal {T}} \sum_ {j = 1} ^ {\mathcal {T}} a _ {j} ^ {\mathcal {T}}\tag{6}
$$

<table><tr><td rowspan="3">Fixed Buffer Size</td><td rowspan="3">Method</td><td rowspan="3">Population Strategy</td><td colspan="2">Split-CIFAR10</td><td colspan="2">Split-CIFAR100</td><td colspan="2">Split-TinyImageNet</td></tr><tr><td colspan="2">Class-IL</td><td colspan="2">Class-IL</td><td colspan="2">Class-IL</td></tr><tr><td>FAA</td><td>FF</td><td>FAA</td><td>FF</td><td>FAA</td><td>FF</td></tr><tr><td rowspan="16">200</td><td rowspan="4">ER</td><td>Reservoir</td><td> $48.39 \pm 2.01$ </td><td> $60.39 \pm 2.26$ </td><td> $15.35 \pm 0.86$ </td><td> $81.20 \pm 0.62$ </td><td> $8.40 \pm 0.16$ </td><td> $76.88 \pm 0.18$ </td></tr><tr><td>Herding</td><td> $52.32 \pm 0.77$ </td><td> $55.17 \pm 0.77$ </td><td> $15.94 \pm 0.46$ </td><td> $79.60 \pm 0.11$ </td><td> $8.81 \pm 0.05$ </td><td> $76.61 \pm 0.62$ </td></tr><tr><td>GSS</td><td> $41.45 \pm 4.65$ </td><td> $68.92 \pm 5.57$ </td><td> $11.87 \pm 0.05$ </td><td> $84.34 \pm 0.41$ </td><td>-</td><td>-</td></tr><tr><td>IPM</td><td> $48.68 \pm 1.11$ </td><td> $59.44 \pm 1.32$ </td><td> $15.0 \pm 0.26$ </td><td> $80.67 \pm 0.31$ </td><td> $8.55 \pm 0.09$ </td><td> $77.13 \pm 0.44$ </td></tr><tr><td rowspan="4">DER</td><td>Reservoir</td><td> $61.17 \pm 1.08$ </td><td> $41.27 \pm 0.53$ </td><td> $24.38 \pm 1.46$ </td><td> $70.07 \pm 1.76$ </td><td> $11.15 \pm 0.46$ </td><td> $74.22 \pm 0.65$ </td></tr><tr><td>Herding</td><td> $30.01 \pm 1.87$ </td><td> $83.12 \pm 2.01$ </td><td> $9.99 \pm 0.23$ </td><td> $87.73 \pm 0.50$ </td><td> $5.7 \pm 1.06$ </td><td> $71.92 \pm 1.87$ </td></tr><tr><td>GSS</td><td> $38.04 \pm 6.09$ </td><td> $71.95 \pm 7.60$ </td><td> $12.29 \pm 1.70$ </td><td> $78.05 \pm 0.53$ </td><td>-</td><td>-</td></tr><tr><td>IPM</td><td> $60.48 \pm 0.34$ </td><td> $30.12 \pm 1.03$ </td><td> $33.47 \pm 1.86$ </td><td> $42.32 \pm 1.71$ </td><td> $19.36 \pm 1.06$ </td><td> $45.46 \pm 0.63$ </td></tr><tr><td rowspan="4">GDumb</td><td>Reservoir</td><td> $29.26 \pm 1.18$ </td><td>N/A</td><td> $4.63 \pm 0.49$ </td><td>N/A</td><td> $2.13 \pm 0.28$ </td><td>N/A</td></tr><tr><td>Herding</td><td> $32.16 \pm 1.51$ </td><td>N/A</td><td> $7.02 \pm 0.51$ </td><td>N/A</td><td> $3.45 \pm 0.30$ </td><td>N/A</td></tr><tr><td>GSS</td><td> $28.35 \pm 1.19$ </td><td>N/A</td><td> $4.81 \pm 0.29$ </td><td>N/A</td><td>-</td><td>N/A</td></tr><tr><td>IPM</td><td> $31.60 \pm 1.83$ </td><td>N/A</td><td> $6.26 \pm 0.14$ </td><td>N/A</td><td> $2.67 \pm 0.36$ </td><td>N/A</td></tr><tr><td rowspan="4">ER-ACE</td><td>Reservoir</td><td> $63.32 \pm 2.40$ </td><td> $18.62 \pm 2.24$ </td><td> $28.78 \pm 0.66$ </td><td> $44.40 \pm 1.13$ </td><td> $12.82 \pm 0.11$ </td><td> $48.91 \pm 1.65$ </td></tr><tr><td>Herding</td><td> $61.66 \pm 0.35$ </td><td> $33.04 \pm 3.37$ </td><td> $29.64 \pm 0.29$ </td><td> $62.08 \pm 0.27$ </td><td> $15.75 \pm 0.09$ </td><td> $64.86 \pm 1.45$ </td></tr><tr><td>GSS</td><td> $26.25 \pm 9.53$ </td><td> $1.02 \pm 1.01$ </td><td> $7.525 \pm 0.13$ </td><td> $8.93 \pm 0.75$ </td><td>-</td><td>-</td></tr><tr><td>IPM</td><td> $49.41 \pm 0.56$ </td><td> $16.56 \pm 0.09$ </td><td> $28.36 \pm 0.28$ </td><td> $27.17 \pm 0.23$ </td><td> $15.02 \pm 0.53$ </td><td> $29.16 \pm 0.35$ </td></tr><tr><td rowspan="16">500</td><td rowspan="4">ER</td><td>Reservoir</td><td> $61.07 \pm 0.64$ </td><td> $44.27 \pm 1.10$ </td><td> $21.37 \pm 1.27$ </td><td> $73.55 \pm 0.77$ </td><td> $10.19 \pm 0.20$ </td><td> $75.34 \pm 0.16$ </td></tr><tr><td>Herding</td><td> $64.09 \pm 0.73$ </td><td> $39.26 \pm 1.39$ </td><td> $24.25 \pm 0.70$ </td><td> $70.46 \pm 0.57$ </td><td> $10.38 \pm 0.16$ </td><td> $75.50 \pm 0.35$ </td></tr><tr><td>GSS</td><td> $61.07 \pm 0.64$ </td><td> $44.27 \pm 1.10$ </td><td> $21.37 \pm 1.27$ </td><td> $73.55 \pm 0.77$ </td><td>-</td><td>-</td></tr><tr><td>IPM</td><td> $61.08 \pm 0.46$ </td><td> $44.33 \pm 0.68$ </td><td> $22.06 \pm 0.48$ </td><td> $72.80 \pm 0.33$ </td><td> $10.20 \pm 0.17$ </td><td> $74.98 \pm 0.18$ </td></tr><tr><td rowspan="4">DER</td><td>Reservoir</td><td> $70.07 \pm 0.95$ </td><td> $29.5 \pm 1.80$ </td><td> $34.53 \pm 1.68$ </td><td> $56.30 \pm 1.52$ </td><td> $17.15 \pm 1.40$ </td><td> $66.91 \pm 1.81$ </td></tr><tr><td>Herding</td><td> $48.20 \pm 2.94$ </td><td> $54.64 \pm 7.93$ </td><td> $13.11 \pm 0.51$ </td><td> $84.04 \pm 0.69$ </td><td> $5.32 \pm 0.78$ </td><td> $67.13 \pm 2.02$ </td></tr><tr><td>GSS</td><td> $45.94 \pm 6.22$ </td><td> $59.09 \pm 9.16$ </td><td> $16.64 \pm 1.69$ </td><td> $72.323 \pm 5.59$ </td><td>-</td><td>-</td></tr><tr><td>IPM</td><td> $65.5 \pm 2.68$ </td><td> $23.55 \pm 5.19$ </td><td> $40.51 \pm 0.43$ </td><td> $28.97 \pm 1.06$ </td><td> $20.49 \pm 0.86$ </td><td> $31.54 \pm 2.61$ </td></tr><tr><td rowspan="4">GDumb</td><td>Reservoir</td><td> $43.35 \pm 0.55$ </td><td>N/A</td><td> $9.85 \pm 0.45$ </td><td>N/A</td><td> $3.6 \pm 0.004$ </td><td>N/A</td></tr><tr><td>Herding</td><td> $42.85 \pm 0.83$ </td><td>N/A</td><td> $11.45 \pm 0.42$ </td><td>N/A</td><td> $4.83 \pm 0.19$ </td><td>N/A</td></tr><tr><td>GSS</td><td> $37.39 \pm 1.21$ </td><td>N/A</td><td> $6.2 \pm 0.29$ </td><td>N/A</td><td>-</td><td>N/A</td></tr><tr><td>IPM</td><td> $42.03 \pm 3.05$ </td><td>N/A</td><td> $9.02 \pm 0.67$ </td><td>N/A</td><td> $3.27 \pm 0.40$ </td><td>N/A</td></tr><tr><td rowspan="4">ER-ACE</td><td>Reservoir</td><td> $72.15 \pm 0.38$ </td><td> $13.18 \pm 1.26$ </td><td> $37.60 \pm 0.15$ </td><td> $38.17 \pm 1.16$ </td><td> $20.99 \pm 0.52$ </td><td> $46.60 \pm 0.55$ </td></tr><tr><td>Herding</td><td> $69.75 \pm 1.90$ </td><td> $23.00 \pm 4.32$ </td><td> $37.54 \pm 0.44$ </td><td> $53.08 \pm 0.47$ </td><td> $20.3 \pm 0.36$ </td><td> $60.48 \pm 0.06$ </td></tr><tr><td>GSS</td><td> $19.54 \pm 0.09$ </td><td> $0.22 \pm 0.11$ </td><td> $8.34 \pm 0.09$ </td><td> $7.73 \pm 0.62$ </td><td>-</td><td>-</td></tr><tr><td>IPM</td><td> $54.43 \pm 0.99$ </td><td> $14.57 \pm 1.17$ </td><td> $35.01 \pm 0.14$ </td><td> $25.50 \pm 0.91$ </td><td> $18.5 \pm 0.42$ </td><td> $34.41 \pm 8.08$ </td></tr><tr><td rowspan="16">5120</td><td rowspan="4">ER</td><td>Reservoir</td><td> $83.18 \pm 1.82$ </td><td> $14.33 \pm 1.65$ </td><td> $50.71 \pm 0.27$ </td><td> $38.92 \pm 0.44$ </td><td> $27.36 \pm 0.03$ </td><td> $54.46 \pm 0.69$ </td></tr><tr><td>Herding</td><td> $85.56 \pm 0.34$ </td><td> $12.22 \pm 0.29$ </td><td> $52.93 \pm 1.55$ </td><td> $35.21 \pm 0.93$ </td><td> $28.43 \pm 0.51$ </td><td> $52.12 \pm 0.51$ </td></tr><tr><td>GSS</td><td> $60.35 \pm 7.06$ </td><td> $43.74 \pm 8.69$ </td><td> $17.52 \pm 0.22$ </td><td> $78.74 \pm 2.28$ </td><td>-</td><td>-</td></tr><tr><td>IPM</td><td> $85.19 \pm 0.63$ </td><td> $10.97 \pm 0.91$ </td><td> $50.75 \pm 1.16$ </td><td> $36.96 \pm 0.60$ </td><td> $27.39 \pm 0.23$ </td><td> $53.43 \pm 0.12$ </td></tr><tr><td rowspan="4">DER</td><td>Reservoir</td><td> $83.35 \pm 0.72$ </td><td> $11.27 \pm 0.96$ </td><td> $57.22 \pm 0.24$ </td><td> $22.86 \pm 1.51$ </td><td> $37.09 \pm 0.50$ </td><td> $31.91 \pm 1.05$ </td></tr><tr><td>Herding</td><td> $76.21 \pm 1.08$ </td><td> $25.26 \pm 1.63$ </td><td> $52.53 \pm 0.24$ </td><td> $38.70 \pm 0.38$ </td><td> $5.09 \pm 2.59$ </td><td> $38.44 \pm 5.37$ </td></tr><tr><td>GSS</td><td> $45.86 \pm 16.34$ </td><td> $54.54 \pm 21.02$ </td><td> $56.32 \pm 1.10$ </td><td> $45.05 \pm 7.04$ </td><td>-</td><td>-</td></tr><tr><td>IPM</td><td> $67.75 \pm 0.52$ </td><td> $6.25 \pm 1.21$ </td><td> $57.30 \pm 0.51$ </td><td> $8.85 \pm 0.52$ </td><td> $34.33 \pm 0.93$ </td><td> $7.27 \pm 0.98$ </td></tr><tr><td rowspan="4">GDumb</td><td>Reservoir</td><td> $79.89 \pm 1.29$ </td><td>N/A</td><td> $42.52 \pm 0.22$ </td><td>N/A</td><td> $21.18 \pm 0.06$ </td><td>N/A</td></tr><tr><td>Herding</td><td> $77.16 \pm 0.74$ </td><td>N/A</td><td> $36.80 \pm 0.57$ </td><td>N/A</td><td> $17.38 \pm 0.40$ </td><td>N/A</td></tr><tr><td>GSS</td><td> $70.27 \pm 2.29$ </td><td>N/A</td><td> $19.64 \pm 1.40$ </td><td>N/A</td><td>-</td><td>N/A</td></tr><tr><td>IPM</td><td> $79.58 \pm 0.93$ </td><td>N/A</td><td> $42.31 \pm 0.18$ </td><td>N/A</td><td> $20.99 \pm 0.72$ </td><td>N/A</td></tr><tr><td rowspan="4">ER-ACE</td><td>Reservoir</td><td> $83.67 \pm 0.26$ </td><td> $4.93 \pm 0.30$ </td><td> $57.01 \pm 0.27$ </td><td> $21.02 \pm 0.22$ </td><td> $38.68 \pm 0.37$ </td><td> $29.41 \pm 0.74$ </td></tr><tr><td>Herding</td><td> $85.02 \pm 0.86$ </td><td> $11.83 \pm 2.08$ </td><td> $58.52 \pm 0.23$ </td><td> $26.77 \pm 0.19$ </td><td> $34.66 \pm 0.99$ </td><td> $41.91 \pm 1.08$ </td></tr><tr><td>GSS</td><td> $19.73 \pm 0.01$ </td><td> $0.05 \pm 0.02$ </td><td> $9.20 \pm 0.04$ </td><td> $4.31 \pm 0.71$ </td><td>-</td><td>-</td></tr><tr><td>IPM</td><td> $66.69 \pm 0.46$ </td><td> $6.29 \pm 0.38$ </td><td> $53.91 \pm 0.43$ </td><td> $14.69 \pm 0.46$ </td><td> $36.28 \pm 0.19$ </td><td> $18.99 \pm 0.27$ </td></tr></table>

Table 2: Population strategy results tested with various replay based methods with traditionally used fixed size buffer, averaged across three runs. We do not report forgetting in GDumb experiments due to the nature of GDumb only training on the fully populated, balanced buffer. Results for TinyImageNet are not reported for GSS due to intractable train times.

$$
F F = \frac {1}{\mathcal {T} - 1} \sum_ {j = 1} ^ {\mathcal {T} - 1} f _ {j} ^ {\mathcal {T}} \text {s.t.} f _ {j} ^ {\mathcal {T}} = \max _ {l \in \{1, \dots , \mathcal {T} - 1 \}} a _ {l} ^ {l} - a _ {j} ^ {\mathcal {T}}
$$

(7)

where $a _ { j } ^ { \mathcal { T } }$ and $f _ { j } ^ { \mathcal { T } }$ are interpreted as the accuracy and forgetting of task j and the end of training on T tasks respectively [8]. When judging performance, we seek maximal FAA and minimal FF.

## 4.1. Results

Fixed Buffer. Results for commonly tested fixed buffer sizes are in Table 2. We first observe that in nearly all cases, reservoir sampling leads to greater forgetting when compared to the other population strategies, specifically compared to herding and IPM. We also observe in several trials, that reservoir sampling also underperforms in FAA compared to herding and IPM. This behavior can be attributed to both herding and IPM selecting the best samples from the learned feature space at the conclusion of each task whereas reservoir sampling simply selects and replaces samples at random.

Another reason for greater forgetting in reservoir sampling is the unbalanced fixed buffers incurred by the random sampling and replacement of data in the buffer. We show the percentage of task specific data of the final fixed buffer when populated via reservoir sampling in Table 3. We can clearly see that, for smaller buffer sizes, there is a bias to the storage of earlier task data compared to more recently encountered tasks. In comparison, both herding and IPM maintain a balanced fixed buffer at all times leading to equal probability of sampling any task data for batch training. Naturally, as the buffer size increases, the unbalanced nature of the buffer populated with reservoir sampling becomes less severe and we see the reservoir population strategy become more competitive with herding and IPM in both FAA and FF.

![](images/0f3b0c46e886f72fd372b0ea040d04dd87c9f547916dc01cbc85dbe8c8efbc20.jpg)  
(a)

![](images/4a75b124f2e39ebbc713cfa63154f721f3d3a7ff6556d8234a8e754997592384.jpg)  
(b)

![](images/0edac4ae042e6f204b6dac4dbf0937eb016b994ee04a784591fae227b9e28bc7.jpg)  
(c)

![](images/5bfbbd7c8f7ae4a251c82cdd78fb7b17f9feed0e8b5ed0c7c2efa98fd32a0898.jpg)  
(d)

![](images/d82fa85a7e0d8d997b47c2a0000e1a3e34189d89edfbf8fbb7e40d97392257f4.jpg)  
(e)

![](images/6dd18b7c1d0761c07e884ee4e0d37404cfb8159195039cb6fa2878b2fa570385.jpg)  
(f)

Figure 2: A comparison of the reservoir, herding, and IPM population strategies paired with DER with a fixed buffer size of 500. Top row corresponds to Split-CIFAR10 performance and bottom row is Split-CIFAR100. The columns correspond as follows: left uses reservoir sampling, center uses herding, and right uses IPM. We do not report GSS results due to all around inferior performance.

<table><tr><td>Fixed Buffer Size</td><td>Percentage of Samples Belonging to Each Task  $(t_1/t_2/t_3/t_4/t_5)$ </td></tr><tr><td>200</td><td>23.5% / 19.0% / 16.0% / 22.0% / 19.5%</td></tr><tr><td>500</td><td>23.5% / 15.0% / 20.5% / 22.5% / 18.5%</td></tr><tr><td>5120</td><td>20.0% / 18.5% / 19.53% / 20.43% / 21.54%</td></tr></table>

Table 3: Percentage of samples in buffer belonging to each task at the end of training populated via reservoir sampling.

We pay particular interest to the scenarios where IPM yields superior FF yet inferior FAA. To analyze why this happens in certain cases, we plot each population strategy used in conjunction with DER for both split-CIFAR10 and split-CIFAR100 in Figure 2 (we omit GSS figures due to all around inferior performance). We observe the interesting behavior where for each t > 1, IPM initially has poor current task performance but then proceeds to make astonishing recoveries for each subsequent task. This indicates that IPM tends to prioritize performance on the buffer instead of the current task at hand which in turn leads to lesser forgetting. An interesting observation to make is that this behavior holds only for DER and ER-ACE (see supplementary material for additional figures). Both DER and ER-ACE are training schemes that directly optimize on logits indicating that IPM is best suited for these types of training schemes.

We take note of the relatively low forgetting of the GSS population strategy when tested with ER-ACE. To investigate why GSS achieves such low forgetting, we plot the accuracy of each previously learned task as new tasks are learned in Figure 4. From this, we can infer that GSS’s low forgetting capabilities when coupled with ER-ACE is caused by the inferior performance on subsequent tasks after t = 1 and thus, has nearly nothing to forget. We note the strong performance of t = 1 throughout the model’s life, however. This is due to GSS first populating the buffer with t = 1 data and thereafter, hardly ever finding a sample with an appropriate score to replace other samples in the buffer as described in Section 3.3. Because of this nature, we should not accept that GSS is the best forgetting performer with coupled with ER-ACE. We still observe that reservoir sampling mostly does not compare in forgetting to other strategies when ignoring GSS results.

![](images/a19f5d58eab9f19123463c8f5b3e6defbb92ccc1f319d7800c77aef6d3145fd3.jpg)  
(a)

![](images/04b670b0a55d8f1818be104b6847f3381701083699e4ab5646363f8c48719433.jpg)  
(b)

![](images/8bb5d344d97602f1d1bdc705cd224449b1872ce051aa6c0c4ec662f46d632f12.jpg)  
(c)

Figure 3: Final forgetting performance with various final buffer sizes tested with Split-CIFAR100. Final buffer sizes with a (D) indicate dynamic final size. In order from left to right are results from reservoir, herding, and IPM respectively.  
![](images/d15225ff2b39081d9aebc2a370f1104ae96ab6bfccf14b03ea16b2a5ad647e9d.jpg)  
(a)

![](images/b317dff33708cf4d3fd42bfdebf4347ce0e8cccf257a139b2c56147df218d6a4.jpg)  
(b)  
Figure 4: ER-ACE using the GSS population strategy for a fixed buffer with buffer size 200. (a) Split-CIFAR10 results. (b) Split-CIFAR100 results.

We observe the all around competitiveness of each population strategy when tested with GDumb (note, we do not report FF for GDumb as there is no forgetting to take place since GDumb trains solely on the buffer). Because GDumb only uses each observed task to populate the memory buffer, it makes sense that herding and IPM perform roughly the same with reservoir sampling since herding and IPM depend on the well learned features for population. Similarly, GSS depends on the gradients of each sample, but because GDumb takes no gradient steps until the conclusion of the final observed task, GSS has no proper way to score samples for replacement or not.

Lastly, we make the note that while no single method consistently outperforms any other, we demonstrate that in many situations, reservoir sampling yields inferior final forgetting performance. This suggests that when using replaybased methods in continual learning solutions, reservoir sampling should not be blindly used as the buffer population strategy of choice, and one should instead pay careful attention to selection of buffer population algorithm for the best performance.

Dynamic Buffer. We next perform experiments using dynamic buffers using the two criteria as described in Section 3.5 and provide tabulated results for class-IL and task-IL scenarios in the supplementary material. We omit GSS results using a dynamic buffer due to poor performance with paired with any of the fixed buffer schemes.

Overall, we observe much of the same trends as seen with fixed buffers. However, we notice that dynamic buffers seem to benefit most when paired with reservoir sampling and IPM in Figure 3 (FAA and FF for all datasets are reported in supplementary material). Because dynamic buffers find the optimal number of samples for storage, we expect the change in FF to be lower when we approach that number, which we observe in Figure 3. In general we observe the Kaiser criterion performing better than intracluster variance. This can be attributed to the ability to adapt to classs complexity for the Kaiser criterion, particularly as the number of classes increases in a dataset.

We note the curious performance of DER when coupled with dynamic replay and give a brief conjecture for why this may be in the supplemental material.

## 5. Conclusions

In this work, we compare the commonly used approach of reservoir sampling for memory buffer population in replay methods to other greedy sampling methods to answer the question of which samples should be stored in memory. We show that reservoir sampling tends to lead to higher forgetting when compared to methods that use strategic population strategies to select the best data points for storage. We then address the question of how many samples should be stored by the formulation of a dynamic buffer populated according to two criteria based on a dataset’s eigenvectors and eigenvalues. We show that dynamic buffers lead to more competitive performance for all population strategies when compared to the arbitrary fixed buffer sizes commonly used in replay methods.

## References

[1] Rahaf Aljundi, Eugene Belilovsky, Tinne Tuytelaars, Laurent Charlin, Massimo Caccia, Min Lin, and Lucas Page-Caccia. Online continual learning with maximal interfered retrieval. In Advances in Neural Information Processing Systems 32, pages 11849–11860. Curran Associates, Inc., 2019. 1, 2

[2] Rahaf Aljundi, Min Lin, Baptiste Goujaud, and Yoshua Bengio. Gradient based sample selection for online continual learning. Advances in neural information processing systems, 32, 2019. 1, 3

[3] Lorenzo Bonicelli, Matteo Boschini, Angelo Porrello, Concetto Spampinato, and Simone Calderara. On the effectiveness of lipschitz-driven rehearsal in continual learning. In Alice H. Oh, Alekh Agarwal, Danielle Belgrave, and Kyunghyun Cho, editors, Advances in Neural Information Processing Systems, 2022. 1, 3

[4] Pietro Buzzega, Matteo Boschini, Angelo Porrello, Davide Abati, and Simone Calderara. Dark experience for general continual learning: a strong, simple baseline. Advances in neural information processing systems, 33:15920–15930, 2020. 1, 2, 4, 5

[5] Lucas Caccia, Rahaf Aljundi, Nader Asadi, Tinne Tuytelaars, Joelle Pineau, and Eugene Belilovsky. New insights on reducing abrupt representation change in online continual learning. In International Conference on Learning Representations, 2022. 1, 2, 4, 5

[6] Lawrence Cayton. Algorithms for manifold learning. Univ. ofCalifornia at San Diego Tech. Rep, 12(1-17):1, 2005. 4

[7] Hyuntak Cha, Jaeho Lee, and Jinwoo Shin. Co2l: Contrastive continual learning. In Proceedings ofthe IEEE/CVF International conference on computer vision, pages 9516– 9525, 2021. 2

[8] Arslan Chaudhry, Puneet K Dokania, Thalaiyasingam Ajanthan, and Philip HS Torr. Riemannian walk for incremental learning: Understanding forgetting and intransigence. In Proceedings of the European conference on computer vision (ECCV), pages 532–547, 2018. 6

[9] Arslan Chaudhry, Albert Gordo, Puneet Dokania, Philip Torr, and David Lopez-Paz. Using hindsight to anchor past knowledge in continual learning. In Proceedings of the AAAI Conference on Artificial Intelligence, volume 35, pages 6993–7001, 2021. 2

[10] Arslan Chaudhry, Marc’Aurelio Ranzato, Marcus Rohrbach, and Mohamed Elhoseiny. Efficient lifelong learning with a-GEM. In International Conference on Learning Representations, 2019. 2

[11] Ehsan Elhamifar, Guillermo Sapiro, and Rene Vidal. See all´ by looking at a few: Sparse modeling for finding representative objects. In 2012 IEEE Conference on Computer Vision and Pattern Recognition, pages 1600–1607, 2012. 3

[12] Charles Fefferman, Sanjoy Mitter, and Hariharan Narayanan. Testing the manifold hypothesis. Journal of the American Mathematical Society, 29(4):983–1049, 2016. 4

[13] Tyler L Hayes, Giri P Krishnan, Maxim Bazhenov, Hava T

Siegelmann, Terrence J Sejnowski, and Christopher Kanan. Replay in deep learning: Current approaches and missing biological elements. Neural computation, 33(11):2908–2950, 2021. 1

[14] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep residual learning for image recognition. In Proceedings ofthe IEEE conference on computer vision and pattern recognition, pages 770–778, 2016. 5

[15] Mohsen Joneidi, Saeed Vahidian, Ashkan Esmaeili, Weijia Wang, Nazanin Rahnavard, Bill Lin, and Mubarak Shah. Select to better learn: Fast and accurate deep learning using data selection from nonlinear manifolds. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), June 2020. 4

[16] Mohsen Joneidi, Alireza Zaeemzadeh, Nazanin Rahnavard, and Mubarak Shah. Iterative projection and matching: Finding structure-preserving representatives and its application to computer vision. Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pages 5409– 5418, 2019. 3, 4

[17] Heechul Jung, Jeongwoo Ju, Minju Jung, and Junmo Kim. Less-forgetful learning for domain expansion in deep neural networks. In Proceedings ofthe AAAI Conference on Artificial Intelligence, volume 32, 2018. 2

[18] Henry F Kaiser. The application of electronic computers to factor analysis. Educational and psychological measurement, 20(1):141–151, 1960. 5

[19] James Kirkpatrick, Razvan Pascanu, Neil Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei A Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, et al. Overcoming catastrophic forgetting in neural networks. Proceedings of the National Academy of Sciences, 114(13):3521–3526, 2017. 2

[20] Alex Krizhevsky, Geoffrey Hinton, et al. Learning multiple layers of features from tiny images. 2009. 4, 5

[21] Ya Le and Xuan S. Yang. Tiny imagenet visual recognition challenge. 2015. 4, 5

[22] Zhizhong Li and Derek Hoiem. Learning without forgetting. IEEE Transactions on Pattern Analysis and Machine Intelligence, 40(12):2935–2947, 2017. 2

[23] David Lopez-Paz and Marc’Aurelio Ranzato. Gradient episodic memory for continual learning. Advances in Neural Information Processing Systems, 30, 2017. 2

[24] James L McClelland, Bruce L McNaughton, and Randall C O’Reilly. Why there are complementary learning systems in the hippocampus and neocortex: insights from the successes and failures of connectionist models of learning and memory. Psychological review, 102(3):419, 1995. 1

[25] Michael McCloskey and Neal J Cohen. Catastrophic interference in connectionist networks: The sequential learning problem. In Psychology of learning and motivation, volume 24, pages 109–165. Elsevier, 1989. 1

[26] Nikhil Mehta, Kevin Liang, Vinay Kumar Verma, and Lawrence Carin. Continual learning using a bayesian nonparametric dictionary of weight factors. In International Conference on Artificial Intelligence and Statistics, pages 100–108. PMLR, 2021. 2

[27] Quang Pham, Chenghao Liu, and Steven HOI. Dualnet: Continual learning, fast and slow. In A. Beygelzimer, Y.

Dauphin, P. Liang, and J. Wortman Vaughan, editors, Advances in Neural Information Processing Systems, 2021. 1, 2

[28] Ameya Prabhu, Philip HS Torr, and Puneet K Dokania. Gdumb: A simple approach that questions our progress in continual learning. In Computer Vision–ECCV 2020: 16th European Conference, Glasgow, UK, August 23–28, 2020, Proceedings, Part II 16, pages 524–540. Springer, 2020. 5

[29] Sylvestre-Alvise Rebuffi, Alexander Kolesnikov, Georg Sperl, and Christoph H Lampert. icarl: Incremental classifier and representation learning. In Proceedings ofthe IEEE conference on Computer Vision and Pattern Recognition, pages 2001–2010, 2017. 1, 2, 3

[30] Mark B Ring. Child: A first step towards continual learning. In Learning to learn, pages 261–292. Springer, 1998. 1

[31] Anthony V. Robins. Catastrophic forgetting, rehearsal and pseudorehearsal. Connect. Sci., 7:123–146, 1995. 2

[32] David Rolnick, Arun Ahuja, Jonathan Schwarz, Timothy Lillicrap, and Gregory Wayne. Experience replay for continual learning. Advances in Neural Information Processing Systems, 32, 2019. 1, 2, 4, 5

[33] Andrei A Rusu, Neil C Rabinowitz, Guillaume Desjardins, Hubert Soyer, James Kirkpatrick, Koray Kavukcuoglu, Razvan Pascanu, and Raia Hadsell. Progressive neural networks. arXiv preprint arXiv:1606.04671, 2016. 2

[34] Ville Satopaa, Jeannie Albrecht, David Irwin, and Barath Raghavan. Finding a ”kneedle” in a haystack: Detecting knee points in system behavior. In 2011 31st International Conference on Distributed Computing Systems Workshops, pages 166–171, 2011. 4

[35] Pravendra Singh, Vinay Kumar Verma, Pratik Mazumder, Lawrence Carin, and Piyush Rai. Calibrating cnns for lifelong learning. Advances in Neural Information Processing Systems, 33:15579–15590, 2020. 2

[36] Qing Sun, Fan Lyu, Fanhua Shang, Wei Feng, and Liang Wan. Exploring example influence in continual learning. In Alice H. Oh, Alekh Agarwal, Danielle Belgrave, and Kyunghyun Cho, editors, Advances in Neural Information Processing Systems, 2022. 1

[37] Shengyang Sun, Daniele Calandriello, Huiyi Hu, Ang Li, and Michalis Titsias. Information-theoretic online memory selection for continual learning. In International Conference on Learning Representations, 2022. 1

[38] Sebastian Thrun and Tom M Mitchell. Lifelong robot learning. Robotics and autonomous systems, 15(1-2):25–46, 1995. 1

[39] Gido M Van de Ven and Andreas S Tolias. Three scenarios for continual learning. arXiv preprint arXiv:1904.07734, 2019. 1

[40] Jeffrey S Vitter. Random sampling with a reservoir. ACM Transactions on Mathematical Software (TOMS), 11(1):37– 57, 1985. 3

[41] Johannes von Oswald, Christian Henning, Benjamin F. Grewe, and Joao Sacramento. Continual learning with hy-˜ pernetworks. In International Conference on Learning Representations, 2020. 2

[42] Max Welling. Herding dynamical weights to learn. In Proceedings of the 26th Annual International Conference on Machine Learning, pages 1121–1128, 2009. 3

[43] Jaehong Yoon, Divyam Madaan, Eunho Yang, and Sung Ju Hwang. Online coreset selection for rehearsal-based continual learning. In International Conference on Learning Representations, 2022. 1

[44] Jaehong Yoon, Eunho Yang, Jeongtae Lee, and Sung Ju Hwang. Lifelong learning with dynamically expandable networks. In International Conference on Learning Representations, 2018. 2

[45] Friedemann Zenke, Ben Poole, and Surya Ganguli. Continual learning through synaptic intelligence. In International Conference on Machine Learning, pages 3987–3995. PMLR, 2017. 5

[46] A. C¸ ivril. Column subset selection problem is ug-hard. Journal ofComputer and System Sciences, 80(4):849–859, 2014. 4