---
title: "2023-Stucchi-Kernel-QuantTree"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2023-Stucchi-Kernel-QuantTree.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Kernel QuantTree

Diego Stucchi <sup>1</sup> Paolo Rizzo <sup>1</sup> Nicoló Folloni <sup>1</sup> Giacomo Boracchi <sup>1</sup>

## Abstract

We present Kernel QuantTree (KQT), a nonparametric change detection algorithm that monitors multivariate data through a histogram. KQT constructs a nonlinear partition of the input space that matches pre-defined target probabilities and specifically promotes compact bins adhering to the data distribution, resulting in a powerful detection algorithm. We prove two key theoretical advantages of KQT: i) statistics defined over the KQT histogram do not depend on the stationary data distribution $\phi _ { 0 } ,$ so detection thresholds can be set a priori to control false positive rate, and ii) thanks to the kernel functions adopted, the KQT monitoring scheme is invariant to the rototranslation of the input data. Consequently, KQT does not require any preprocessing step like PCA. Our experiments show that KQT achieves superior detection power than non-parametric state-ofthe-art change detection methods, and can reliably control the false positive rate.

## 1. Introduction

Change Detection (CD) is the problem of detecting distribution changes $\phi _ { 0 }  \phi _ { 1 }$ in a datastream, namely detecting when the data-generating process drifts from a stationary distribution $\phi _ { 0 }$ towards an unknown post-change distribution $\phi _ { 1 }$ . Here, we address the problem of batch-wise $C D ,$ where data are analyzed in fixed-size batches that, under normal conditions, contain samples drawn from $\phi _ { 0 }$ . The timely detection of distribution changes and the control over the false alarm rate are fundamental problems that have been widely explored in both the Machine Learning (Gama et al., 2014) and Statistical Process Control (Basseville et al., 1993) literature. Among the many applications of change-detection algorithms, we mention fault detection (Tartakovsky et al., 2006), financial monitoring (Ross et al.,

2011), cryptographic attacks (Frittoli et al., 2020), and quality control (Hawkins et al., 2003).

Most CD algorithms consist of three major ingredients: i) a model $\widehat { \phi } _ { 0 }$ describing stationary data, which is usually blearned from a training set, ii) a statistical test, where a test statistic $\tau$ is computed to assess the consistency of incoming data to $\dot { \phi _ { 0 } }$ , and iii) a decision rule on $\tau$ to establish whether ba change has occurred. In many real-world multivariate scenarios, estimating a density model for the stationary data is often unfeasible. Therefore, non-parametric methods that describe stationary data by flexible models are preferred. Unfortunately, most non-parametric statistics are based on ranking (Ross & Adams, 2012) and can only be applied to univariate data. In Section 3, we overview the few nonparametric solutions to monitor multivariate datastreams. A relevant example is QuantTree (QT) (Boracchi et al., 2018), a change detection algorithm based on a histogram partitioning of the input space, which is supported by sound theoretical results. In particular, QT allows to operate at a controlled false alarm rate without knowing ϕ nor resorting to bootstrap to estimate detection thresholds.

A fundamental limitation of QT is that splits are defined along the axis, as in Figure 1(a), resulting in a partitioning that does not always adhere to the input distribution. To mitigate this problem, a preprocessing stage is typically introduced to align the split directions to the principal components of the training set, as shown in Figure 1(b). While this procedure is often beneficial, we observe (Section 6) that it can worsen the detection performance in some unpredictable cases. Moreover, many bins in Figure 1(a)(b) have non-finite volumes, which can lead to poor estimation of bin probabilities.

In this paper, we introduce Kernel QuantTree (KQT), a nonparametric and multivariate CD algorithm that constructs histogram bins via measurable kernel functions, resulting in a powerful CD test. In contrast with the QT algorithm, which constructs bins by axis-aligned splits, KQT partitions the space in K 1 compact bins defined by kernel functions evaluated on the training data. An additional bin, denoted as the residual bin, is non-compact and gathers all the points that do not fall in any other bin. Figure 1(c)-(d)-(e) shows that the KQT bins are compact subsets of the domain. Our intuition is that compact bins increase the flexibility when modeling $\phi _ { 0 }$ by fitting a histogram h to training data. Moreover, estimating the bin probabilities under $\phi _ { 0 }$ , which are fundamental to compute the test statistic $\mathcal { T } _ { h }$ , is less accurate on non-compact bins.

![](images/8c7820febfd7858af9c481c4eccc9c85664ef323a80ae45360f98b38a52de36c.jpg)  
Figure 1. QuantTree generates bins as intersection of hyperplanes, performing cuts along the axis (a). After a preprocessing through PCA, the cuts are oriented along the principal directions (b). Kernel QuantTree generates bins that are subsets of d-dimensional spheres according to the underlying kernel functions, namely the Euclidean (c), Mahalanobis (d) and Weighted Mahalanobis (e) distances.

In Section 5, we prove that KQT features two theoretical properties that have significant implications in change detection. First, the distribution of the test statistic $\mathcal { T } _ { h }$ computed from a KQT histogram h does not depend on the stationary distribution $\phi _ { 0 }$ . Consequently, detection thresholds τ can be set a priori as in QT, without knowing $\phi _ { 0 }$ . Second, the monitoring performed by KQT using specific kernel functions is not influenced by preprocessing based on roto-translations, including alignment to principal components. Thanks to these properties, KQT outperforms state-of-the-art alternatives on a broad experimental testbed illustrated in Section 6. In particular, KQT achieves better detection performance than the alternatives independently of preprocessing steps based on roto-translations.

## In summary, these are our main contributions:

i) We present Kernel QuantTree, a non-parametric CD method based on a histogram where bins are defined by kernel functions. KQT achieves state-of-the-art detection performance on multivariate datastreams;

ii) We prove that statistics defined over the KQT histograms do not depend on $\phi _ { 0 }$ , but only on few KQT parameters. This enables control of the FPR by thresholds τ set a priori, via Monte Carlo simulations;

iii) We prove that the monitoring performed by KQT is independent of any preprocessing by roto-translations.

## 2. Problem Formulation

We address the problem of change detection in batch-wise monitoring settings, where stationary data are realizations of a random vector X with unknown probability density function $\phi _ { 0 }$ . We assume that a training set of stationary samples $\mathrm { T R } = \{ { \bf x } _ { 1 } , \ldots , { \bf x } _ { N } \} \subset \mathbb { R } ^ { d }$ is provided, and that incoming data are processed in batches $W$ of $\nu \in \mathbb { N }$ samples each. We denote as $W \sim \phi _ { 0 }$ when all the samples in the batch W are drawn from $\phi _ { 0 }$

Our goal is to design a CD algorithm that: i) detects distribution changes in incoming batches, and ii) controls the False Positive Rate (FPR), namely the probability of mistakenly detecting a change in stationary data. We formulate this CD problem as a Hypothesis Test to establish whether $W \sim \phi _ { 0 }$ (null hypothesis) or $W \sim \phi _ { 1 } \neq \phi _ { 0 }$ , where $\phi _ { 1 }$ is the unknown post-change distribution. We pursue the mainstream approach of computing a test statistic $\tau$ on each batch W and detecting a change when

$$
\mathcal {T} (W) > \tau ,\tag{1}
$$

where $\tau \in$ R is the threshold that we set to control the FPR. For the sake of simplicity, we assume that a batch $W$ is either drawn from $\phi _ { 0 }$ or from a different unknown distribution $\phi _ { 1 } \neq$ ϕ<sub>0</sub>. However, CD algorithms can in principle detect batches drawn from a mixture of $\phi _ { 0 }$ and $\phi _ { 1 }$ , even though the detection power is expected to be lower in this case.

## 3. Related Work

Change detection in multivariate datastreams is a challenging problem, which can be significantly simplified when $\phi _ { 0 }$ belongs to a known parametric family since the model $\stackrel { \cdot } { \phi _ { 0 } }$ bis obtained by estimating its parameters. The most popular solutions pursuing this approach consist in monitoring the likelihood of incoming data with respect to $\widehat { \phi } _ { 0 }$ fitted on TR. Viable options for $\widehat { \phi } _ { 0 }$ bare Gaussian process (Saatçi bet al., 2010), Gaussian Mixtures (Kuncheva, 2011) or kernel density estimators (Krempl, 2011). In (Kuncheva, 2011) and (Kuncheva & Faithfull, 2013), the Semiparametric Log-Likelihood (SPLL) algorithm fits a Gaussian Mixture Model (GMM) to TR and compares incoming batches with batches from TR by a likelihood test. Moreover, in SPLL, it is not possible to set a priori the detection threshold to control the FPR, as the distribution of the test statistic depends on $\phi _ { 0 }$ Moreover, adopting a GMM to approximate $\phi _ { 0 }$ might not always fit real-world data, as demonstrated by our experiments on high-dimensional datasets.

There are only a few recent multivariate methods that perform non-parametric change detection, namely, that assume that $\phi _ { 0 }$ and $\phi _ { 1 }$ are unknown. Among these, we focus on histogram-based algorithms, since these are non-parametric by design and can efficiently process datastreams in batches. As such, histogram-based algorithms represent very practical solutions to monitor multivariate datastreams. Density Tree (Criminisi et al., 2012) constructs a space partitioning by iteratively splitting regions to maximize an informationgain metric. In this case, the distribution of the test statistic depends on $\phi _ { 0 }$ , thus detection thresholds need to be set by bootstrap on TR. Equal Intensity K-means (EIKM) (Liu et al., 2020) divides the input space using K-means clustering, resulting in bins that yield an equal probability under ϕ<sub>0</sub>. EIKM is designed to handle multimodal distributions, e.g., Gaussian Mixtures, and the detection thresholds are given by asymptotic approximations of the Pearson test statistic. QuantTree (Boracchi et al., 2018) defines a partitioning $s$ of the input space in K bins by axis-aligned cuts. The theoretical properties of QT guarantee that the distribution of test statistics defined over bin probabilities does not depend on $\phi _ { 0 } .$ , which allows to set detection thresholds a priori, with synthetically generated data through a very efficient scheme. The splits are performed such that the probability of a stationary sample to fall in each bin is close to a set of target probabilities $\left\{ \pi _ { k } \right\}$ provided as input parameters. Since the data splits are limited to the axis directions, the bins in QT require a preprocessing stage whose outcome, in terms of detection power, is uncertain, as demonstrated in our experiments (Section 6). KQT preserves the properties of QT in terms of setting detection thresholds and FPR control, and overcomes QT limitation by constructing compact bins that are not affected by roto-translations, thus better approximate the probability measure of each bin under $\phi _ { 0 }$

## 4. Kernel QuantTree

We present Kernel QuantTree $( \mathsf { K Q T } ) ^ { 1 }$ , a CD algorithm that solves a major limitation of QuantTree (QT) while generalizing and extending its theoretical guarantees. The KQT histogram is constructed by iteratively splitting the input space $\mathbb { R } ^ { d }$ into $K$ bins $\{ S _ { k } \}$ such that the probability of a stationary sample $\mathbf { x } \sim \phi _ { 0 }$ to fall in $S _ { k }$ is close to a target probability $\pi _ { k } .$ , which are provided as input parameters. The peculiarity of KQT is that each bin $S _ { k }$ for $k < K$ is defined by a measurable kernel function $f _ { k } : \mathbb { R } ^ { d } $ R and a split value $q _ { k } \in \mathbb { R }$ , and corresponds to a compact set in $\mathbb { R } ^ { d }$ We denote as Generalized QuantTree (GQT) partitioning the resulting histogram $h = \{ ( S _ { k } , \widehat { \pi } _ { k } ) \} _ { k = 1 } ^ { K }$ , which yields a partition of the input space $\mathbb { R } ^ { d }$ b, where $\widehat { \pi } _ { k }$ is the empirical probability of $\mathbf { x } \sim \phi _ { 0 }$ to fall in $S _ { k }$

![](images/d9a0d8067ab296717014f393dbe479f0e8f11e8a2e532d87a61f9b51da92009b.jpg)  
Figure 2. The Generalized QuantTree histogram is a binary splitting tree where splits isolate leaves, i.e. bins of the histogram.

As illustrated in Figure 2, a GQT partitioning corresponds to an extremely imbalanced binary tree, where each split isolates a leaf, corresponding to a bin $S _ { k }$ . In what follows (Section 4.1 and 4.2), we illustrate in detail the GQT partitioning scheme, providing a few examples of kernel functions. In Section 5, we demonstrate that the distribution of any test statistic $\mathcal { T } _ { h }$ defined over a GQT partitioning does not depend on $\phi _ { 0 } ,$ , extending the theoretical results from QT. This property enables setting the detection threshold τ in (1) a priori by Monte Carlo simulations.

The monitoring scheme by KQT operates as follows. Given an input batch W containing ν test samples, we compute the test statistic $\mathcal { T } _ { h } ( W )$ and detect changes when this exceeds the threshold τ. While the theoretical properties of KQT hold for all the statistics that only depend on $\left\{ y _ { k } \right\}$ , the numbers of samples in W falling in bins $\{ S _ { k } \}$ , we consider the Pearson $\chi ^ { 2 }$ statistic (Lehmann et al., 2005):

$$
\mathcal {T} _ {h} (W) = \mathcal {T} _ {h} (y _ {1}, y _ {2}, \dots , y _ {K}) = \sum_ {k = 1} ^ {K} \frac {(y _ {k} - \nu \pi_ {k}) ^ {2}}{\nu \pi_ {k}},\tag{2}
$$

where $\left\{ \pi _ { k } \right\}$ are the target bin probabilities. In Section 5.3, we also prove that under some mild assumption on the kernel function $f _ { k }$ , this monitoring scheme becomes independent of any roto-translation applied to the data, including the PCA preprocessing. Finally, in Section 4.4, we analyze the computational complexity of KQT both at the training and monitoring stages.

## 4.1. Generalized QuantTree (GQT) Partitioning

The two elements defining each bin in a GQT are: i) a measurable function $f _ { k } : \mathbb { R } ^ { d } $ R mapping multivariate data to a single dimension and ii) a split value $q _ { k } \in \mathbb { R }$ chosen to match the target probability $\pi _ { k } .$ . Algorithm 1 illustrates the GQT histogram construction, which requires as input a training set TR and the target probabilities $\left\{ \pi _ { k } \right\}$ The rationale underpinning the space partitioning of KQT is to iteratively construct bins by selecting sublevel sets of the kernel functions $f _ { k }$ . In particular, $S _ { 1 }$ is defined as the sublevel set of $f _ { 1 }$ with respect to the split value $q _ { 1 }$ :

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Construction of the GQT histogram
1: Input: training set  $TR = \{x_i\}_{i=1}^N \subset R^d$ , target probabilities  $\{\pi_k\}_{k=1}^K$ 
2: Output: GQT histogram  $h = \{(S_k, \widehat{\pi}_k)\}_{k=1}^K$ 
3: Set  $X_0 = TR$ 
4: for  $k = 1, \ldots, K - 1$  do
5: Compute  $\widetilde{\pi}_k = \pi_k (1 - \sum_{j&lt;k} \pi_j)^{-1}$ 
6:Compute  $\{f_k(x_i)\}$  for  $x_i \in X_{k-1}$ 
7: Set  $q_k$  as the  $\widetilde{\pi}_k$ -quantile of  $\{f_k(x_i)\}$ 
8:  $S_k = \{x \in \bigcap_{j&lt;k} \overline{S}_j \mid f_k(x) \leq q_k\}$ 
9:  $X_k = \{x \in X_{k-1} \mid f_k(x) &gt; q_k\}$ 
10: end for
11:  $S_K = R^d \setminus \bigcup_{j &lt; K} S_j$
</div>

$$
S _ {1} = \left\{\mathbf {x} \in \mathbb {R} ^ {d} \mid f _ {1} (\mathbf {x}) \leq q _ {1} \right\}.\tag{3}
$$

The other bins $S _ { k } , 1 < k < K$ are obtained by isolating sublevel sets from the space that is not yet assigned to a bin

$$
S _ {k} = \left\{\mathbf {x} \in \bigcap_ {j <   k} \overline {{{{S _ {j}}}}} \mid f _ {k} (\mathbf {x}) \leq q _ {k} \right\} \text {   for   } k <   K,\tag{4}
$$

where $\overline { { S _ { j } } }$ denotes the complement of $S _ { j }$ in $\mathbb { R } ^ { d }$ . The last bin, $S _ { K } = \bar { \mathbb { R } } ^ { d } \setminus \bigcup _ { j < K } S _ { j }$ , is the residual bin, which contains all the points that do not fall in the previous bins.

The split values $q _ { k }$ are defined at each iteration by first identifying the set $\mathcal { X } _ { k } \subset \mathrm { T R }$ which contains the training points that do not fall in any bin $\{ S _ { j } \mid j < k \}$ . In the beginning, no training samples have been assigned to a bin, thus, we set $\mathcal { X } _ { 0 } = \mathrm { T R }$ and $N _ { 0 } = | \mathrm { T R } |$ (line 3). At the k-th step, we first the percentage of points of $\mathcal { X } _ { k - 1 }$ that must fall in $S _ { k }$ to meet the target probability $\pi _ { k }$ (line 5), which we denote as:

$$
\widetilde {\pi} _ {k} = \pi_ {k} \left(1 - \sum_ {j <   k} \pi_ {j}\right) ^ {- 1},\tag{5}
$$

such that $S _ { k }$ contains $\pi _ { k } N = \widetilde { \pi } _ { k } \left| \mathcal { X } _ { k - 1 } \right|$ points. Then, we evaluate $f _ { k }$ on all the samples in $\mathcal { X } _ { k - 1 }$ (line 6), and compute the split value $q _ { k }$ as the $\widetilde { \pi } _ { k }$ -quantile of the projected samples $\{ f _ { k } ( \mathbf { x } ) , \mathbf { x } \in \mathcal { X } _ { k - 1 } \}$ e(line 7). Finally, we define $S _ { k }$ as in (4) (line 8), and we update the set of points $\mathcal { X } _ { k }$ that will be used to construct the next bin (line 9). The process results in the GQT histogram $h = \{ ( S _ { k } , \widehat { \pi } _ { k } ) \} _ { k = 1 } ^ { K } ,$ , where $\widehat { \pi } _ { k }$ bis the percentage of training points that fall in $S _ { k }$ and bapproximates the probability of $\mathbf { x } \sim \phi _ { 0 }$ to fall in $S _ { k }$

The GQT extends the partitioning scheme underpinning QT, which corresponds to using linear split functions:

$$
f _ {k} (\mathbf {x}) = \pm 1 \cdot P _ {j} \mathbf {x},\tag{6}
$$

where $P _ { j }$ is the projection over a randomly selected component j and 1 randomly introduces a sign flip for the projection. In the next section, we present specific measurable functions $f _ { k }$ that we employ in KQT.

## 4.2. Employed Kernel Functions in KQT

We define the kernel functions $f _ { k } : \mathbb { R } ^ { d } $ R as distances from a centroid $\mathbf { c } _ { k } \in \mathrm { T R }$ , selected from the training set:

$$
f _ {k} (\mathbf {x}) = \left(\mathbf {x} - \mathbf {c} _ {k}\right) ^ {T} A (\mathbf {x} - \mathbf {c} _ {k}),\tag{7}
$$

where $A \in \mathbb { R } ^ { d \times d }$ is the kernel matrix, which induces a distance measure in $\mathbb { R } ^ { d }$ . In particular, the bins $\{ S _ { k } \}$ in (4) are subsets of d-dimensional spheres centered in $\left\{ \mathbf { c } _ { k } \right\}$ and having radii $\left\{ q _ { k } \right\}$ , where the distances are measured with respect to the metric induced by A. Since spheres in $\mathbb { R } ^ { d }$ are compact sets, all the bins $S _ { k }$ of a KQT, but the residual $S _ { K }$ are compact and have a finite volume.

Here, we construct KQT using the Euclidean, the Mahalanobis, and the Weighted Mahalanobis (Tipping, 1999) distances, whose bins are illustrated in Figure 1. We obtain the Euclidean distance by setting $A = \mathbb { I } _ { d }$ , namely, the d-dimensional identity matrix, resulting in isotropic bins. Figure 1(c) shows that these bins poorly fit the data distribution. We obtain the Mahalanobis distance by setting $A = \Sigma ^ { - 1 }$ , where $\Sigma \in \mathbb { R } ^ { d \times d }$ is the sample covariance matrix of TR, and in this case, the bins are anisotropic. Figure 1(d) also shows that bins are elongated towards the directions with larger variance, resulting in a better fit to the data. However, these bins poorly approximate TR when this exhibits multiple clusters, since multiple bins might span different clusters. To promote bins containing samples from a single cluster, we adopt the Weighted Mahalanobis distance and fit a Gaussian Mixture of M components to TR, and then assign a larger distance to points that belong to different components of the GMM. In KQT, we use $M = 4$ components, and the Weighted Mahalanobis kernel matrix is then defined as:

$$
A (\mathbf {x}) = \frac {\sum_ {m = 1} ^ {M} \rho_ {m} \cdot i _ {m} (\mathbf {x} , \mathbf {c}) \cdot C _ {m} ^ {- 1}}{\sum_ {m = 1} ^ {M} \rho_ {m} \cdot i _ {m} (\mathbf {x} , \mathbf {c})},\tag{8}
$$

where $\mu _ { m } , C _ { m } .$ , and $\rho _ { m }$ denote the mean, covariance matrix, and mixing probability of the m-th Gaussian, respectively. The matrix A in (8) represents a weighted average of the inverse covariance matrices of the GMM components. As in (Tipping, 1999), the weights are proportional to the mixing probabilities $\rho _ { m }$ and $i _ { m } ( \mathbf { x } , \mathbf { c } )$ , which is a computationallytractable approximation of the distance between the point x and the bin centroid c.

In the following, we discuss the centroid selection strategy employed in KQT.

## 4.3. Centroid Selection

The criteria to select the centroids $\{ \mathbf { c } _ { k } \}$ from TR is key in KQT, as this determines both the spatial location of the bin $S _ { k }$ and the split value $q _ { k }$ associated with the kernel function $f _ { k }$ . Therefore, we select the centroid in TR by optimizing a partition-quality metric I, namely,

$$
\mathbf {c} _ {k} = \underset {\mathbf {c} \in \mathcal {X} _ {k - 1}} {\operatorname{argmax}} I [ \mathbf {c} ],\tag{9}
$$

where $\mathcal { X } _ { k - 1 }$ are the training samples used to construct $S _ { k }$ and $I [ \mathbf { c } ]$ denotes the value of the metric when we select c as a centroid. In KQT, we consider two centroid selection strategies: i) maximizing the information gain associated with the split and ii) minimizing the Gini index of the distances to the centroid. For computational reasons, when $\mathcal { X } _ { k - 1 }$ is large, we restrict the search space to a subset of randomly sampled potential centroids $\{ \mathbf { c } \} \subset \mathcal { X } _ { k - 1 }$

The information gain (Mitchell, 1997) measures the decrease in the overall entropy H after a split in the data and is typically used to assess the split quality in a data set, for example by Density Tree (Criminisi et al., 2012). The best split lowers the data entropy, maximizing the information gain. In KQT, we compute the information gain yielded by the split that divides $\mathcal { X } _ { k - 1 }$ into $\mathcal { X } _ { k }$ and $\overline { { \mathcal { X } } } _ { k } = \mathcal { X } _ { k - 1 } \backslash \mathcal { X } _ { k }$ In particular, we can compute the entropy $H ( B )$ of a set of points B using the Gaussian approximation:

$$
H (B) = (1 / 2) \log \Big ((2 \pi e) ^ {d} \det (\operatorname{cov} [ B ]) \Big).\tag{10}
$$

where $\mathrm { c o v } [ B ]$ represents the sample covariance matrix computed over B. The information gain associated with the centroid c is defined as

$$
I [ \mathbf {c} ] = | \mathcal {X} _ {k - 1} | H (\mathcal {X} _ {k - 1}) - (| \overline {{\mathcal {X} _ {k}}} | H (\overline {{\mathcal {X} _ {k}}}) + | \mathcal {X} _ {k} | H (\mathcal {X} _ {k})).\tag{11}
$$

In the supplementary material, we discuss the simplifications we introduced to lower the computational burden of assessing (11) for multiple potential centroids, like the Gaussian approximation of H, which does not influence the nonparametric nature of KQT.

The Gini index (Gini, 1912) measures the level of uniformity in an empirical distribution and takes values between 0 (perfect equality) and 1 (maximum inequality). In KQT, we use the Gini index to prevent the selection of centroids in low-density regions. Specifically, we compute the Gini index of the distances between the training samples and the centroid as

$$
I [ \mathbf {c} ] = \frac {\sum_ {i , j} | f _ {k} (\mathbf {x} _ {i}) - f _ {k} (\mathbf {x} _ {j}) |}{2 | \mathcal {X} _ {k - 1} | \sum_ {i} f _ {k} (\mathbf {x} _ {i})}.\tag{12}
$$

We select the centroid that minimizes (12) to promote bins that cover densely populated regions of the input space.

## 4.4. Computational Remarks

In terms of computation cost, the training of a KQT comprises i) the projection of TR by $f _ { k }$ , whose cost depends on the specific kernel function, ii) the computation of the split value, which costs $O ( N )$ , and iii) the centroid selection. The cost of computing the Euclidean distance is $O ( d )$ , while the Mahalanobis costs $O ( d ^ { 2 } )$ and the Weighted Mahalanobis costs $O ( M d ^ { 2 } )$ , where M is the number of Gaussian components fitted to TR. The cost of computing the information gain is dominated by the computation of the determinant in (10), which costs $O ( d ^ { 3 } )$ while computing the Gini index only requires the distances between the training samples and the centroids, already computed to define $S _ { k }$ . Overall, the cost of the index computation is multiplied by the number of centroids T tested during the selection procedure by (9). Therefore, an upper bound for the cost of KQT construction is $O ( K T ( N + \bar { M } N d ^ { 2 } + d ^ { 3 } ) )$ when using the Weighted Mahalanobis distance and the information gain. During monitoring, the only operation performed is the projection by $f _ { k }$ of the samples of a batch W, resulting in a cost of $O ( \nu K M d ^ { 2 } )$ in case of the Weighted Mahalanobis distance.

Table 1 reports the complexity of all the methods considered in our experiments, showing that KQT with the Weighted Mahalanobis distance is most computationally demanding, both in terms of training and inference. However, the experiments discussed in Section 6 prove that this cost is balanced by superior detection performance.

Table 1. Comparison of the computational complexity of KQT and the other considered methods, where M is the number of Gaussian components employed by KQT with the Weighted Mahalanobis distance, and R is the number of splits of Density Tree.

<table><tr><td>Method</td><td>Training Cost</td><td>Inference Cost</td></tr><tr><td>KQT (Weighted Maha.)</td><td> $O(KT(N + MNd^{2} + d^{3}))$ </td><td> $O(\nu KMd^{2})$ </td></tr><tr><td>QuantTree</td><td> $O(KN\log N)$ </td><td> $O(\nu K)$ </td></tr><tr><td>EIKM</td><td> $O(K^{2}N\log N)$ </td><td> $O(\nu K)$ </td></tr><tr><td>SPLL</td><td> $O(Nd^{2})$ </td><td> $O(\nu d^{2})$ </td></tr><tr><td>Density Tree</td><td> $O(KRd^{3})$ </td><td> $O(\nu K)$ </td></tr></table>

## 5. Theoretical Guarantees

This section illustrates the theoretical properties of KQT and is organized as follows. In Section 5.1, we prove that the distribution of the test statistic computed by GQT over stationary data is independent of $\phi _ { 0 }$ , hence generalizing the main result of QT from (Boracchi et al., 2018) to a more extensive set of histogram-based monitoring schemes, including KQT. Then, in Section 5.2, we show how to exploit this result to compute detection thresholds by Monte Carlo simulations such that the empirical FPR matches any target value α. Finally, in Section 5.3, we prove that KQT is invariant to roto-translations of the data when we use the kernel functions in Section 4.2.

## 5.1. Generalization of the QT Independence Theorem

The following result implies that the distribution of a test statistic like (2) computed over stationary batches by a GQT is independent of $\phi _ { 0 }$ , the input dimension d and the employed functions $f _ { k }$ . Thus, such distribution can be empirically computed via Monte Carlo simulations and used in any monitoring scenario as long as $\{ \pi _ { k } \} _ { k }$ <sub>k</sub>, the training set size $N .$ , and the batch size ν are fixed.

Theorem 5.1. Let $h = \{ ( S _ { k } , \widehat { \pi } _ { k } ) \} _ { k = 1 } ^ { K }$ be a Generalized bQuantTree histogram constructed using measurable functions $f _ { k } : \mathbb { R } ^ { d }  \mathbb { R }$ , k. Let $\mathcal { T } _ { h }$ be a statistic defined over batches W such that $\mathcal { T } _ { h } ( W )$ only depends on the number of samples $y _ { 1 } , \ldots , y _ { K }$ ofW falling in the bins ofh. Then, the distribution of $\mathcal { T } _ { h }$ over stationary batches $W \sim \phi _ { 0 }$ depends only on the batch size ν, the number oftraining points N and target probabilities $\{ \pi _ { k } \} _ { k }$

The proof of Theorem 5.1 follows three propositions as the proof of Theorem 1 in (Boracchi et al., 2018), which we generalize to a broader set of partitioning schemes. The first proposition states that the probability of a point drawn from the stationary distribution $\phi _ { 0 }$ to fall in any bin of a GQT histogram follows a Beta distribution.

Proposition 5.2. Let $\mathbf { x } _ { 1 } , \mathbf { x } _ { 2 } , \ldots , \mathbf { x } _ { M }$ be i.i.d. realizations ofa continuous random vector X defined over $\mathcal { D } \subset \mathbb { R } ^ { d } .$ . Let $f : \mathbb { R } ^ { d }  \mathbb { R }$ be a measurablefunction, and let $Z = f ( X )$ We denote with $z _ { ( 1 ) } \leq z _ { ( 2 ) } \leq \cdot \cdot \cdot \leq z _ { ( M ) }$ the sorted images $o f \left\{ \mathbf { x } _ { j } \right\}$ through f. For any $L \in \{ 1 , 2 , \ldots , M \}$ , we define the sublevel sets

$$
Q _ {f, L} := \{\mathbf {x} \in \mathcal {D}: f (\mathbf {x}) \leq z _ {(L)} \}.\tag{13}
$$

Then, the random variable $p = P _ { \mathbf { X } } ( Q _ { f , L } )$ is distributed as Beta $L , M - L + 1 )$ .

The proof of Proposition 5.2 is reported in the supplementary material. In the following, we denote the probability of a stationary point $\mathbf { x } ~ \sim ~ \phi _ { 0 }$ to fall in bin k as $p _ { k } = P _ { \phi _ { 0 } } ( \mathbf { x } \in S _ { k } )$ . Moreover, we denote as $\widetilde { p } _ { k } = P _ { \phi _ { 0 } } ( \mathbf { x } \in$ $S _ { k } \mid \mathbf { x } \not \in \bigcup _ { j < k } S _ { j } )$ e) the probability of x to fall in $S _ { k }$ and not in any of the previous bins.

Proposition 5.3. For a Generalized QuantTree histogram, the following relation holds:

$$
p _ {k} = \widetilde {p _ {k}} \cdot \left(1 - \sum_ {j <   k} p _ {j}\right) = \widetilde {p _ {k}} \prod_ {j <   k} \left(1 - \widetilde {p _ {j}}\right).\tag{14}
$$

Proposition 5.4. For a Generalized QuantTree histogram, the random variables $\{ \widetilde { p _ { k } } \}$ are independent.

The proofs of Propositions 5.3 and 5.4 are equivalent to the proofs of the Proposition 2 and 3 for QT (Boracchi et al., 2018). Finally, the proof of Theorem 5.1 follows from Propositions $5 . 2 \substack { - 5 . 3 - 5 . 4 }$ and from the following facts: i) the employed statistic (2) only depends on the number of samples falling in each bin $\left\{ y _ { k } \right\}$ , and ii) when the batch is drawn from $\phi _ { 0 }$ , the vector $[ y _ { 1 } , \dots , y _ { K } ]$ is a realization of a Multinomial distribution of parameters $\left( \nu , p _ { 1 } , \dots , p _ { K } \right)$

## 5.2. Threshold Computation for FPR Control

From Theorem 5.1, it follows that in GQT we can compute a detection threshold $\tau = \tau ( \alpha )$ yielding an FPR α when used as in (1) for any test statistic $\mathcal { T } _ { h }$ that only depends on $\left\{ y _ { k } \right\}$ . For this purpose, we estimate by Monte Carlo simulations the empirical distribution of $\mathcal { T } _ { h }$ on stationary batches. Interestingly, (Frittoli et al., 2022) prove that the empirical distribution of N samples drawn from $\phi _ { 0 }$ in a QT histogram follows a Dirichlet distribution of parameters $\{ \pi _ { 1 } N , \ldots , \pi _ { K - 1 } N , \pi _ { K } N + 1 \}$ , where $\left\{ \pi _ { k } \right\}$ are the target probabilities used for constructing the histogram. Since the projection function does not influence the proof in (Frittoli et al., 2022), the same result holds for GQT. Moreover, the distribution of a batch $W \sim \phi _ { 0 }$ in the histogram bins follows a Multinomial distribution. Thus, we can efficiently simulate the construction of a GQT and compute the values $\mathcal { T } _ { h }$ over $W \sim \phi _ { 0 }$ by Monte Carlo simulations, such that τ is the $( 1 - \alpha )$ -quantile of the resulting distribution.

Remarkably, the distribution of the test statistic does not depend on the employed kernel functions $\{ f _ { k } \}$ . Therefore, we can use the same detection thresholds for any GQT that uses any measurable function $f _ { k }$ . Moreover, these detection thresholds also work for QT, which is a special case of GQT that uses (6).

## 5.3. Roto-Translation Invariance of KQT

In this section, we prove that KQT is invariant under rototranslations when the employed kernel function is either the Euclidean, Mahalanobis or Weighted Mahalanobis distance. We denote a roto-translation as $\Phi : \mathbb { R } ^ { d }  \mathbb { R } ^ { d }$ , and the image of a set $B \subset \mathbb { R } ^ { d }$ as $\Phi ( B ) = \{ \Phi ( \mathbf { x } ) | \mathbf { x } \in B \}$ The following theorem states that the two KQT histograms $h = \{ ( S _ { k } , \widehat { \pi } _ { k } ) \}$ and $h ^ { \prime } = \{ ( S _ { k } ^ { \prime } , \widehat { \pi } _ { k } ^ { \prime } ) \}$ , constructed with and b bwithout preprocessing by Φ, respectively, are equivalent.

Theorem 5.5. Let Φ $: \mathbb { R } ^ { d }  \mathbb { R } ^ { d }$ be a roto-translation. Let $h \ = \ \{ ( S _ { k } , \widehat { \pi } _ { k } ) \}$ and $h ^ { \prime } \ = \ \{ ( S _ { k } ^ { \prime } , \widehat \pi _ { k } ^ { \prime } ) \}$ be the KQT b bhistograms constructed from the training sets $\mathrm { T R } \subset \mathbb { R } ^ { d }$ and $\mathrm { T R } ^ { \prime } = \Phi ( \mathrm { T R } )$ , where the kernel function is either the Euclidean, Mahalanobis or Weighted Mahalanobis distance. Then, we have that $S _ { k } ^ { \prime } = \Phi ( S _ { k } )$ and $\widehat { \pi } _ { k } ^ { \prime } = \widehat { \pi } _ { k } f o r$ $k = 1 \ldots , K$ b b. In particular,for any batch W, ifwe compute $W ^ { \prime } = \Phi ( W )$ , we have that $\mathcal { T } _ { h } ( W ) = \mathcal { T } _ { h ^ { \prime } } ( W ^ { \prime } )$

Theorem 5.5 proves that, for the considered kernel functions, the value of the test statistic computed over a batch $W$ of data does not change when we employ a roto-translation Φ for preprocessing, including PCA, that is sometimes required for QT to achieve good detection performance. The proof of Theorem 5.5 is reported in the supplementary material and relies on the fact that the construction of the two histograms uses the same points (up to Φ), namely $\mathcal { X } _ { k } ^ { \prime } = \Phi ( \mathcal { X } _ { k } )$ , to define each bin. In particular, we need to prove that our centroid selection strategy results in the same centroid (up to Φ) for $S _ { k }$ and $S _ { k } ^ { \prime }$ :

Lemma 5.6. Let $\mathcal { X } _ { k - 1 }$ and $\mathcal { X } _ { k - 1 } ^ { \prime } = \Phi ( \mathcal { X } _ { k - 1 } )$ be the set of points used to construct the KQT histogram bins $S _ { k }$ and $S _ { k } ^ { \prime } ,$ , respectively. Then, the centroid selection by (9) results in centroids $\mathbf { c } _ { k }$ and $\mathbf { c } _ { k } ^ { \prime } = \Phi ( \mathbf { c } _ { k } )$

In the supplementary material, we prove this lemma, and we use it in the proof of Theorem 5.5 to show by induction that $S _ { k } = S _ { k } ^ { \prime }$ for every $k .$ Consequently, every batch $W$ will result in the same value of test statistic because if a point $\mathbf { x } \in W$ falls in $S _ { k }$ , then $\Phi ( \mathbf { x } ) \in W ^ { \prime }$ will fall in $S _ { k } ^ { \prime }$

## 6. Experiments

In this section, we validate KQT through several experiments, proving that KQT i) reaches detection performance that are statistically superior than state-of-the-art algorithms, and ii) can accurately control the FPR.

## 6.1. Datasets

We present the synthetic and real-world datasets that we employ in our experiments.

In each experiment, we consider TR made of $N = 4 0 9 6$ points sampled without replacement by $\phi _ { 0 }$ . During testing, we randomly sample 5000 batches of ν samples from ϕ<sub>0</sub> and 5000 batches of ν samples from $\phi _ { 1 }$ to robustly assess detection performance.

Synthetic. We consider two synthetic settings with $d = 4$ the unimodal and the bimodal. In the unimodal setting, the stationary distribution $\phi _ { 0 }$ is a 0-mean Gaussian with a random covariance matrix. The post-change distribution $\phi _ { 1 }$ is obtained by roto-translation using the CCM framework (Alippi et al., 2017), such that the Kullback-Leibler distance between ϕ<sub>0</sub> and $\phi _ { 1 }$ is 1. In the bimodal setting, $\phi _ { 0 }$ is a Gaussian mixture of two slightly-overlapping components, and $\phi _ { 1 }$ is again generated by a roto-translation of each component of $\phi _ { 0 }$ computed using CCM. In the supplementary material, we discuss the same experiment performed with $d \in \{ 4 , 8 , 1 6 , 3 2 , 6 4 , 1 2 8 \}$

INSECTS. The INSECTS dataset (Souza et al., 2020) contains feature vectors $( d = 3 3 )$ extracted from sensor measurements describing the wing-beat frequency of six (annotated) species of flying insects. This dataset contains real changes caused by temperature modifications that affect the insects’ flying behavior. We set up the change detection experiment such that $\phi _ { 0 }$ describes measurements acquired at a temperature, and the change $\phi _ { 0 }  \phi _ { 1 }$ corresponds to a temperature change. We denote as $i  i + 1$ the considered temperature changes, with $i \in \{ 1 , 2 , 3 , 4 , 5 \}$

UCI. We employ real-world datasets from the UCI Machine Learning Repository (Dua & Graff, 2017) and from (Dal Pozzolo et al., 2017), with dimensions ranging from $d = 5 \mathrm { t o } d = 5 0$ , reported in Table 2. We standardize these datasets and add a negligible amount of noise $\eta \sim N ( 0 , \sigma )$ to each component to prevent the many repeated values from harming the histogram construction. The values of $\sigma$ for each dataset are reported in the supplementary material. These datasets contain no distribution changes, thus stationary samples are drawn by sampling the dataset. We generate a post-change distribution $\phi _ { 1 }$ by shifting stationary data in a random direction with a magnitude proportional to the variance of each component.

Swarm. The Swarm Behavior classification dataset from the UCI Machine Learning Repository (Dua & Graff, 2017) comprises high-dimensional data $( d = 2 4 0 0 )$ describing the motion of large groups of animals, which are labeled as flocking or not-flocking. We define the stationary distribution $\phi _ { 0 }$ as the distribution of data describing flocking groups of animals. In contrast, the post-change distribution $\phi _ { 1 }$ is defined by data corresponding to non-flocking animals.

High-dimensional datasets represent a challenging scenario for change detection algorithms, especially when they require estimating a density model. Therefore, these algorithms typically employ dimensionality-reduction techniques to map data to lower dimensions (Thudumu et al., 2020). To show that high-dimensional problems can be tackled by KQT upon employing such techniques, in our experiments we apply a PCA-based preprocessing step, retaining the 32 components explaining the most variance in the data.

## 6.2. Figures of Merit

We assess the performance of CD algorithms with two standard figures of merit, FPR and AUC. We set the detection thresholds in our experiments to yield an empirical FPR of $\alpha = 5 \%$ . To compare the detection power, we rank the algorithms according to their AUC, and we report their average rank (Demšar, 2006) over all the datasets and over 500 runs of each experiment. Moreover, we report the $p \textmd { - }$ values of the Nemenyi post-hoc test (Nemenyi, 1963), comparing the AUCs of each method against the best-performing one. In Table 2, we mark in bold the largest AUC achieved over each dataset. We also underline values when the Nemenyi test confirms that the difference with the second best-performing method is statistically significant. Confidence intervals are reported in the supplementary material.

Table 2. FPR/AUC achieved by the considered methods with K = 16 bins and batches of $\nu = 1 2 8$ points. We report the average ranking with respect to the AUC and the p-value of the Nemenyi test. For each dataset, we mark in bold the AUCs of the best-performing method, and underline them when found to be significantly different from the second best-performing.

<table><tr><td></td><td>d</td><td>QT (w/o PCA)</td><td>QT (w/ PCA)</td><td>KQT (Euclidean)</td><td>KQT (Mahalanobis)</td><td>KQT (Weighted Maha.)</td><td>EIkM</td><td>SPLL (C=3)</td><td>PCA-SPLL (C=3)</td><td>DT (w/o PCA)</td><td>DT (w/ PCA)</td></tr><tr><td>unimodal</td><td>4</td><td>4.83%/0.96</td><td>4.81%/0.98</td><td>4.86%/0.95</td><td>4.82%/0.99</td><td>4.83%/0.99</td><td>4.82%/0.87</td><td>5.46%/1.00</td><td>5.92%/0.99</td><td>7.84%/0.79</td><td>7.75%/0.81</td></tr><tr><td>bimodal</td><td>4</td><td>4.80%/0.90</td><td>4.81%/0.93</td><td>4.80%/0.90</td><td>4.81%/0.95</td><td>4.80%/0.97</td><td>4.82%/0.82</td><td>5.53%/0.92</td><td>6.02%/0.90</td><td>7.65%/0.75</td><td>7.62%/0.77</td></tr><tr><td>nino</td><td>5</td><td>5.04%/0.84</td><td>4.99%/0.91</td><td>5.00%/0.61</td><td>5.02%/0.90</td><td>5.01%/0.92</td><td>4.83%/0.53</td><td>6.14%/0.82</td><td>7.69%/0.84</td><td>7.55%/0.73</td><td>7.57%/0.58</td></tr><tr><td>protein</td><td>9</td><td>4.97%/0.90</td><td>4.98%/0.98</td><td>4.97%/0.62</td><td>4.98%/0.99</td><td>5.03%/0.99</td><td>4.88%/0.51</td><td>13.15%/0.92</td><td>8.42%/0.95</td><td>7.65%/0.70</td><td>7.64%/0.59</td></tr><tr><td>spruce</td><td>10</td><td>4.81%/1.00</td><td>4.83%/1.00</td><td>4.82%/0.60</td><td>4.84%/1.00</td><td>4.90%/1.00</td><td>4.86%/0.51</td><td>11.43%/1.00</td><td>11.56%/1.00</td><td>7.56%/1.00</td><td>7.57%/1.00</td></tr><tr><td>lodgepole</td><td>10</td><td>4.83%/1.00</td><td>4.82%/1.00</td><td>4.85%/0.65</td><td>4.80%/1.00</td><td>4.90%/1.00</td><td>4.92%/0.51</td><td>10.78%/1.00</td><td>10.89%/1.00</td><td>7.60%/1.00</td><td>7.58%/1.00</td></tr><tr><td>credit</td><td>28</td><td>4.83%/0.70</td><td>4.96%/0.87</td><td>4.89%/0.60</td><td>4.85%/0.78</td><td>5.06%/1.00</td><td>4.96%/0.51</td><td>8.67%/0.60</td><td>16.06%/0.66</td><td>7.63%/0.69</td><td>7.59%/0.82</td></tr><tr><td>insects (1→2)</td><td>33</td><td>4.92%/1.00</td><td>4.93%/0.96</td><td>4.91%/0.96</td><td>4.93%/0.97</td><td>5.19%/0.99</td><td>4.93%/0.84</td><td>5.90%/0.81</td><td>6.48%/0.87</td><td>7.57%/1.00</td><td>7.60%/1.00</td></tr><tr><td>insects (2→3)</td><td>33</td><td>4.93%/0.99</td><td>4.91%/1.00</td><td>4.92%/1.00</td><td>4.96%/1.00</td><td>5.25%/1.00</td><td>4.96%/0.96</td><td>5.54%/1.00</td><td>6.16%/1.00</td><td>7.60%/1.00</td><td>7.59%/1.00</td></tr><tr><td>insects (3→4)</td><td>33</td><td>4.92%/0.98</td><td>4.89%/0.90</td><td>4.90%/0.90</td><td>4.88%/0.94</td><td>5.22%/0.99</td><td>4.89%/0.83</td><td>6.09%/0.75</td><td>6.69%/0.74</td><td>7.59%/1.00</td><td>7.54%/1.00</td></tr><tr><td>insects (4→5)</td><td>33</td><td>4.92%/1.00</td><td>4.95%/1.00</td><td>4.91%/1.00</td><td>4.92%/1.00</td><td>5.25%/1.00</td><td>4.91%/0.95</td><td>5.48%/1.00</td><td>6.01%/1.00</td><td>7.63%/1.00</td><td>7.56%/1.00</td></tr><tr><td>insects (5→6)</td><td>33</td><td>4.91%/1.00</td><td>4.90%/0.97</td><td>4.90%/0.98</td><td>4.92%/0.99</td><td>5.26%/1.00</td><td>4.90%/0.96</td><td>5.86%/0.98</td><td>6.19%/0.98</td><td>7.61%/1.00</td><td>7.63%/1.00</td></tr><tr><td>sensorless</td><td>48</td><td>4.84%/0.86</td><td>5.01%/1.00</td><td>4.82%/0.54</td><td>5.01%/1.00</td><td>7.42%/1.00</td><td>4.93%/0.50</td><td>4.33%/1.00</td><td>4.83%/1.00</td><td>7.55%/0.74</td><td>7.58%/0.60</td></tr><tr><td>particle</td><td>50</td><td>4.85%/0.89</td><td>4.87%/0.93</td><td>4.81%/0.55</td><td>4.94%/0.98</td><td>5.80%/0.99</td><td>4.84%/0.51</td><td>5.93%/0.84</td><td>6.07%/0.90</td><td>7.52%/0.80</td><td>7.60%/0.54</td></tr><tr><td>Average Ranking</td><td></td><td>5.24</td><td>4.93</td><td>7.08</td><td>3.82</td><td>2.98</td><td>9.37</td><td>5.57</td><td>5.34</td><td>5.11</td><td>5.56</td></tr><tr><td>Nemenyi p-value</td><td></td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>-</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td></tr></table>

## 6.3. Methods

We configure all the histogram-based methods to partition the space in K bins with uniform target probabilities $\pi _ { k } =$ $\textstyle { \frac { 1 } { K } }$ , as advised by (Boracchi et al., 2018). The number of bins K and the batch size ν must be chosen to guarantee that batches contain enough samples for a stable measure of these target probabilities. In particular, since histograms approximate the probability of a point falling in a bin by the number of training samples per batch that falls in each bin, we expect that a larger number of points per bin (i.e., the ratio ν/K) yield better detection performance. We confirm this by considering two settings: the high-ratio setting (K = 16, ν = 128) and the low-ratio one $( K = 3 2 , \nu = 6 4 )$

QuantTree. QuantTree (Boracchi et al., 2018) uses a histogram to monitor incoming batches while controlling the FPR. Bins are constructed with axis-oriented splits along random components, and the changes are detected by the Pearson statistic. Detection thresholds are computed via Monte Carlo simulations. We test QT with and without PCA preprocessing of the data.

Equal Intensity K-Means (EIKM). EIKM (Liu et al., 2020) constructs a histogram with K bins using a K-means clustering to guarantee an equal proportion of stationary data in each bin. EIKM uses the Pearson statistic and its asymptotic approximation to set the detection thresholds.

Semiparametric Log-Likelihood (SPLL). SPLL (Kuncheva, 2011) models the stationary distribution $\phi _ { 0 }$ as a Gaussian Mixture Model (GMM) and suggests fitting $C = 3$ components. During inference, the test statistic associated with a batch W is computed by an upper bound of the log-likelihood of its samples. Since SPLL comes without a threshold computation strategy, we employ Welch’s t-test (Welch, 1947) to detect batches whose average SPLL is statistically different from the training set.

PCA-SPLL. Presented in (Kuncheva & Faithfull, 2013), PCA-SPLL extends SPLL by transforming data through the PCA and monitoring by SPLL only the components with the lowest variance. Here, we keep up to 5% of the variance and fit C = 3 Gaussians.

Density Tree. Inspired by (Criminisi et al., 2012), the bins of Density Tree minimize the entropy after each split. Density Tree employs the Pearson test statistic, and sets the detection threshold via bootstrapping over a portion of training data. We test Density Tree with and without PCA preprocessing of the data.

## 6.4. Results and Discussion

Table 2 reports the FPR and AUC achieved by all the considered methods in the high-ratio setting, averaged over 500 runs. Here, we only report the performance of KQT maximizing the information gain (11) to select centroids. In the supplementary material, we also report the results for the low-ratio and a comparison showing that minimizing the Gini index (12) leads to comparable performance.

Table 3. FPR and AUC achieved by QuantTree and Kernel Quant-Tree on the Swarm dataset processed by a PCA to retain d = 32 components. In parenthesis, the standard deviation of the results.

<table><tr><td></td><td>FPR</td><td>AUC</td></tr><tr><td>QuantTree</td><td>4.61% (1.65%)</td><td>1.00 (0.00)</td></tr><tr><td>KQT (Euclidean)</td><td>4.53% (1.63%)</td><td>1.00 (0.00)</td></tr><tr><td>KQT (Mahalanobis)</td><td>4.50% (1.58%)</td><td>1.00 (0.00)</td></tr><tr><td>KQT (Weighted Maha.)</td><td>4.61% (1.67%)</td><td>1.00 (0.00)</td></tr></table>

In most experiments, the empirical FPR achieved by KQT is

close to the target α = 5% for all the considered kernel functions. However, the KQT with the Weighted Mahalanobis distance struggles to control the FPR when d is large. This is a known limitation of high-dimensional settings, where the estimated GMM might be poorly conditioned when TR is not sufficiently large. Therefore, when the GMM fit from TR yields Gaussians having covariances with large condition numbers, it is convenient to use KQT with the Mahalanobis distance. This latter, in fact, can control the FPR and usually achieves comparable detection performance with the Weighted Mahalanobis distance.

To further investigate how the dimension d influences the detection performance of KQT, we run another experiment where we train KQT on synthetic data with d 4, 8, 16, 32, 64, 128 and with $N \in \{ 4 0 9 6 , 1 6 3 8 4 \}$ . The results reported in the supplementary material prove that the FPR control worsens when d increases, but also that using large training sets heavily mitigates this problem. Moreover, this issue can be avoided by employing dimensionality reduction techniques on high-dimensional data. To this purpose, we run an experiment on the Swarm dataset (d = 2400) preprocessed by a PCA transformation that retains only the first 32 principal components. Table 3 shows that thanks to this preprocessing, KQT can seamlessly operate without incurring the loss of FPR control observed on some UCI datasets. The large AUC achieved by all the methods on this dataset proves that classes are very far apart, and we argue that a similar situation would have happened if we had artificially added a change (which would not correspond to a real-world problem) to offset each component. In fact, even a small perturbation would result in a very apparent change. This is probably the reason why change detection benchmarks are of lower dimensions (e.g., INSECTS d=33).

As for the other methods, QT and EIKM accurately control the FPR. In contrast, SPLL and PCA-SPLL mostly exceed the target, and we speculate that the distribution of the SPLL test statistic does not satisfy the t-test assumptions. Finally, Density Tree largely overshoots the target FPR, being unable to learn a detection threshold from bootstrapping.

KQT with the Weighted Mahalanobis and the Mahalanobis distance represent the best and second-best method in terms of AUC, mostly outperforming the alternatives in most settings. In particular, the advantage over the third-ranked method (QT w/ PCA) is considerable, and the p-values of the Nemenyi post-hoc test show that the advantage of KQT is also statistically significant. However, when using the Euclidean distance on real-world data, the performance of KQT worsens because its anisotropic bins cannot model the intricate data distributions of real data. As for the other methods, SPLL performs well over the synthetic datasets but fails over the INSECTS and UCI, achieving significantly low performance on the latter. Instead, PCA-SPLL mainly improves the performance of SPLL, even though it cannot compete with the top-performing methods. Finally, Density Tree mostly achieves low detection performance, except on the INSECTS dataset, where it surpasses the other methods.

Our experiments show that preprocessing by PCA is in general beneficial for QT, as the average rank of QT w/PCA is lower than QT w/o PCA. However, in some settings, QT w/o PCA performs better. In contrast, KQT achieves the best AUC independently of the PCA preprocessing, thanks to the invariance to roto-translation proved in Section 5.3, and Density Tree is also not affected by the PCA.

The supplementary material reports the detection results in the low-ratio setting $( K = 3 2 , \nu = 6 4 )$ . Overall, the results conform to those in the high-ratio setting and confirm that a larger expected number of points per bin improves the detection performance for all the methods. For the same reason, QT and KQT achieve lower FPR in the low-ratio setting than in the high-ratio, since the Pearson statistic assumes fewer distinct values. Thus, while still controlling the FPR, this results in a slightly lower percentage of false alarms. The KQT with the Weighted Mahalanobis distance achieves the highest AUC in the low-ratio setting, with a statistically significant advantage over the competitors.

We conclude by remarking that data in the INSECTS and UCI datasets are not drawn from multivariate Gaussian distributions, as suggested by the low performance achieved by SPLL, which is based on a GMM. To confirm this, we run the Shapiro-Wilk normality test on the marginals of our real-world data, showing that these are not univariate Gaussians. In the supplementary material, we report the p-values of these tests, which are in the range of 10−<sup>20</sup>.

## 7. Conclusions

In this paper we presented KQT, a non-parametric multivariate change detection method for batch-wise monitoring. KQT constructs a space partitioning via kernel functions, resulting in bins which are compact and lead to superior detection power. We compare our method to several stateof-the-art approaches for CD, achieving the best results in terms of detection power and false positives control. Future work includes integrating KQT in a sequential monitoring scheme, where data are processed in a continuous stream.

## 8. Acknowledgments

This paper is supported by the PNRR-PE-AI FAIR project funded by the NextGeneration EU program.

## References

Alippi, C., Boracchi, G., and Carrera, D. Ccm: Controlling the change magnitude in high dimensional data. In Angelov, P., Manolopoulos, Y., Iliadis, L., Roy, A., and Vellasco, M. (eds.), Advances in Big Data, pp. 216–225, Cham, 2017. Springer International Publishing. ISBN 978-3-319-47898-2.

Basseville, M., Nikiforov, I. V., et al. Detection of abrupt changes: theory and application, volume 104. prentice Hall Englewood Cliffs, 1993.

Boracchi, G., Carrera, D., Cervellera, C., and Maccio, D. Quanttree: Histograms for change detection in multivariate data streams. In International Conference on Machine Learning, pp. 639–648. PMLR, 2018.

Criminisi, A., Shotton, J., and Konukoglu, E. Decision forests: A unified framework for classification, regression, density estimation, manifold learning and semisupervised learning. Foundations and trends® in computer graphics and vision, 7(2–3):81–227, 2012.

Dal Pozzolo, A., Boracchi, G., Caelen, O., Alippi, C., and Bontempi, G. Credit card fraud detection: a realistic modeling and a novel learning strategy. IEEE transactions on neural networks and learning systems, 29(8):3784–3797, 2017.

Demšar, J. Statistical comparisons of classifiers over multiple data sets. The Journal of Machine Learning Research, 7:1–30, 2006.

Dua, D. and Graff, C. UCI machine learning repository, 2017. URL http://archive.ics.uci.edu/ml.

Frittoli, L., Matteo, B., Silvia, M., Carrera, D., Beatrice, R., Fragneto, P., Ruggero, S., and Boracchi, G. Strengthening sequential side-channel attacks through change detection. In Conference on Cryptographic Hardware and Embedded Systems (CHES), volume 3, pp. 1–21, 2020.

Frittoli, L., Carrera, D., and Boracchi, G. Nonparametric and online change detection in multivariate datastreams using quanttree. IEEE Transactions on Knowledge and Data Engineering, 2022.

Gama, J., Žliobaite, I., Bifet, A., Pechenizkiy, M., and ˙ Bouchachia, A. A survey on concept drift adaptation. ACM computing surveys (CSUR), 46(4):1–37, 2014.

Gini, C. Variabilità e mutabilità: contributo allo studio delle distribuzioni e delle relazioni statistiche.[Fasc. I.]. Tipogr. di P. Cuppini, 1912.

Hawkins, D. M., Qiu, P., and Kang, C. W. The changepoint model for statistical process control. Journal of quality technology, 35(4):355, 2003.

Krempl, G. The algorithm apt to classify in concurrence of latency and drift. In Proceedings of the Intelligent Data Analysis (IDA), pp. 222–233, 2011.

Kuncheva, L. I. Change detection in streaming multivariate data using likelihood detectors. IEEE transactions on knowledge and data engineering, 25(5):1175–1180, 2011.

Kuncheva, L. I. and Faithfull, W. J. Pca feature extraction for change detection in multidimensional unlabeled data. IEEE transactions on neural networks and learning systems, 25(1):69–80, 2013.

Lehmann, E. L., Romano, J. P., and Casella, G. Testing statistical hypotheses, volume 3. Springer, 2005.

Liu, A., Lu, J., and Zhang, G. Concept drift detection via equal intensity k-means space partitioning. IEEE transactions on cybernetics, 51(6):3198–3211, 2020.

Mitchell, T. M. Machine learning, volume 1. McGraw-hill New York, 1997.

Nemenyi, P. B. Distribution-free multiple comparisons. Princeton University, 1963.

Ross, G. J. and Adams, N. M. Two nonparametric control charts for detecting arbitrary distribution changes. Journal ofQuality Technology, 44(2):102, 2012.

Ross, G. J., Tasoulis, D. K., and Adams, N. M. Nonparametric monitoring of data streams for changes in location and scale. Technometrics, 53(4):379–389, 2011.

Saatçi, Y., Turner, R. D., and Rasmussen, C. E. Gaussian process change point models. In Proceedings of the International Conference on Machine Learning (ICML), pp. 927–934, 2010.

Souza, V. M., dos Reis, D. M., Maletzke, A. G., and Batista, G. E. Challenges in benchmarking stream learning algorithms with real-world data. Data Mining and Knowledge Discovery, 34(6):1805–1858, 2020.

Tartakovsky, A. G., Rozovskii, B. L., Blazek, R. B., and Kim, H. A novel approach to detection of intrusions in computer networks via adaptive sequential and batchsequential change-point detection methods. IEEE TSP, 54(9):3372–3382, 2006.

Thudumu, S., Branch, P., Jin, J., and Singh, J. A comprehensive survey of anomaly detection techniques for high dimensional big data. Journal ofBig Data, 7:1–30, 2020.

Tipping, M. E. Deriving cluster analytic distance functions from gaussian mixture models. 1999.

Welch, B. L. The generalization of ‘student’s’problem when several different population varlances are involved. Biometrika, 34(1-2):28–35, 1947.

# Kernel QuantTree (Supplementary Material)

## 1 Introduction

This document provides additional material omitted from the main article due to space limitations. Section 2 reports the proofs of the theoretical results supporting the Kernel QuantTree (KQT) algorithm, namely, the independence of the test statistic from the stationary distribution (Theorem 1) and the roto-translational invariance of KQT (Theorem 2). Then, Section 3 illustrates additional experimental settings that complete the empirical analysis of the KQT algorithm. In particular, we test the normality of the employed real-world datasets (Section 3.1), investigate the performance on high-dimensional datasets (Section 3.2), compare the performance of the proposed centroid selection strategies (Section 3.3), and report the complete results of the experiments from the main article (Section 3.4).

## 2 Theoretical Results

In this section, we report the proofs of the theorems introduced in Section 5 of the main article. To make this section self-contained and improve the overall readability, we recall some definitions that were already introduced in the article

## 2.1 Controlling the False Alarm Rate

The Generalized QuantTree (GQT) histogram $h = \{ ( S _ { k } , \widehat { \pi } _ { k } ) \}$ partitions the input space $\mathbb { R } ^ { d }$ such that the probability $\widehat { \pi } _ { k }$ of a stationary sample $\mathbf { x } \sim \phi _ { 0 }$ to fall in bin $S _ { k }$ is close to a target probability $\pi _ { k }$ provided as an input parameter. During testing, GQT monitors batches W of ν samples by computing a test statistic $\mathcal { T } _ { h }$ whose value only depends on the number of samples of W falling in each bin. Then, the test statistic is compared against a detection threshold $\tau \in \mathbb { R }$ , and a change is detected when

$$
\mathcal {T} _ {h} (W) > \tau .\tag{1}
$$

A peculiarity of GQT is that each bin $S _ { K }$ is defined as a subset of the sublevel set of a measurable kernel function $f _ { k } : \mathbb { R } ^ { d }  \mathbb { R }$ . In this section, we prove Theorem 5.1 of the main article, which we recall here:

Theorem 1. Let $h = \{ ( S _ { k } , \widehat { \pi } _ { k } ) \} _ { k = 1 } ^ { K }$ be a Generalized QuantTree histogram constructed using measurable functions $f _ { k } : \mathbb { R } ^ { d }  \mathbb { R } \forall k$ . Let $\mathcal { T } _ { h }$ be a statistic defined over batches W such that $\mathcal { T } _ { h } ( W )$ only depends on the number of samples y<sub>1</sub>, . . . , y<sub>K</sub> of W falling in the bins of h. Then, the distribution of $\mathcal { T } _ { h }$ over stationary batches W ∼ ϕ<sub>0</sub> depends only on the batch size ν, the number of training points N and target probabilities $\{ \pi _ { k } \} _ { k }$

Theorem 1 implies that the distribution of $\mathcal { T } _ { h }$ computed over stationary batches by a GQT is independent of $\phi _ { 0 } ,$ d or $\{ f _ { k } \}$ , thus allowing us to empirically estimate its distribution and compute a threshold τ such that the False Positive Rate (FPR) achieved by GQT is controlled. The threshold computation strategy is presented in Section 5.2 of the main article. Theorem 1 is a generalization of Theorem 1 from [Boracchi et al., 2018] and its proof follows the same structure based on three propositions. Here, we prove the first of these propositions:

Proposition 1. Let $\mathbf { x } _ { 1 } , \mathbf { x } _ { 2 } , \ldots , \mathbf { x } _ { M }$ be i.i.d. realizations of a continuous random vector X defined over $\mathcal { D } \subset \mathbb { R } ^ { d }$ . Let $f : \mathbb { R } ^ { d }  \mathbb { R }$ be a measurable function, and let $Z = f ( X )$ . We denote with $z _ { ( 1 ) } \leq$ $z _ { ( 2 ) } \leq \cdots \leq z _ { ( M ) }$ the sorted images of $\{ \mathbf { x } _ { j } \}$ through f. For any $L \in \{ 1 , 2 , \dots , M \}$ , we define the sublevel sets

$$
Q _ {f, L} := \{\mathbf {x} \in \mathcal {D}: f (\mathbf {x}) \leq z _ {(L)} \}.\tag{2}
$$

Then, the random variable $p = P _ { \mathbf { X } } ( Q _ { f , L } )$ is distributed as $B e t a ( L , M - L + 1 )$

Proof. We prove the proposition by showing that p is an order statistic of the uniform distribution, which in turn follows a Beta distribution [Lehmann et al., 2005]. Since f is a measurable function for the considered probability space and X is a continuous random variable (r.v.) in $\mathbb { R } ^ { d }$ , by the properties of continuous r.v. [Papoulis and Pillai, 2002], we have that $Z = f ( X )$ is also a continuous r.v. in R. Then, we define $U = F _ { Z } ( Z )$ , where $F _ { Z }$ is the cdf of Z. Since $F _ { Z }$ is monotonically non-decreasing, we can also define the inverse cdf as:

$$
F _ {Z} ^ {- 1} (t) = \inf \left\{z \in \mathbb {R} \mid F _ {Z} (z) \geq t \right\}.\tag{3}
$$

Then, we have that

$$
\begin{array}{r l} & F _ {U} (u) = P _ {U} (U \leq u) = P _ {Z} (F _ {Z} (Z) \leq u) = \\ & \qquad = P _ {Z} (Z \leq F _ {Z} ^ {- 1} (u)) = F _ {Z} (F _ {Z} ^ {- 1} (u)) = u, \end{array}\tag{4}
$$

hence U is a uniform random variable, since its cumulative density function is the identity. Recall that we assumed that X is defined over D, i.e., $P _ { \mathbf { X } } ( \mathbb { R } \setminus \mathcal { D } ) = 0$ . Then, exploiting (4), we can express $p$ as follows:

$$
\begin{array}{l} p = P _ {X} (Q _ {f, L}) = P _ {X} (\mathbf {x} \in \mathcal {D} \mid f (\mathbf {x}) \leq z _ {(L)}) = \\ \quad = P _ {Z} (z \in \mathbb {R} \mid z \leq z _ {(L)}) = \\ \quad = P _ {U} (u \in [ 0, 1 ] \mid u \leq u _ {(L)}) = u _ {(L)}, \end{array}\tag{5}
$$

where we define $u _ { ( L ) } = F _ { Z } \bigl ( z _ { ( L ) } \bigr )$ . From (5), we have that p is the L-th order statistic of M samplings of the uniform distribution, and its distribution is Beta $( L , M - L + 1 )$ [Balakrishnan and Rao, 1998].

We refer the reader to [Boracchi et al., 2018] for a thorough description of the derivation of the proof of Theorem 1 from Proposition 1.

## 2.2 Centroid Selection and Invariance to Roto-Translation

Kernel QuantTree (KQT) defines a partition of the input space by iteratively splitting it in bins $S _ { k }$ that match a target probability, as shown in Figure 2 of the main article. The KQT bins are defined as subsets of sublevel sets of the adopted measurable kernel functions $f _ { k }$ . We report here the formal definition of the KQT histogram bins:

$$
\left\{ \begin{array}{l} S _ {1} = \{\mathbf {x} \in \mathbb {R} ^ {d} \mid f _ {1} (\mathbf {x}) \leq q _ {1} \} \\ S _ {k} = \{\mathbf {x} \in \bigcap_ {j <   k} \overline {{S _ {j}}} \mid f _ {k} (\mathbf {x}) \leq q _ {k} \} \text {for} k <   K \\ S _ {K} = \mathbb {R} ^ {d} \setminus \bigcup_ {j <   K} S _ {j} \end{array} \right.,\tag{6}
$$

where $\overline { { S _ { j } } }$ denotes the complement of $S _ { j }$ in $\mathbb { R } ^ { d }$ , and $q _ { k }$ is the split value computed as a quantile of the training samples projected via $f _ { k }$

Section 4.2 of the main article illustrates the kernel functions $f _ { k } : \mathbb { R } ^ { d }  \mathbb { R }$ adopted by KQT, which are defined as distances from a selected centroid $\mathbf { c } _ { k } \in \mathrm { T R }$ :

$$
f _ {k} (\mathbf {x}) = \left(\mathbf {x} - \mathbf {c} _ {k}\right) ^ {\intercal} A \left(\mathbf {x} - \mathbf {c} _ {k}\right),\tag{7}
$$

where $A \in \mathbb { R } ^ { d \times d }$ is the kernel matrix, which determines the employed distance. In our experiments, we construct KQT using the Euclidean, the Mahalanobis, and the Weighted Mahalanobis [Tipping, 1999] distances. The corresponding kernel matrices are $A = \mathbb { I } _ { d }$ for the Euclidean distance, $\mathbf { \bar { A } } = \operatorname { c o v } [ \mathrm { T R } ] ^ { - 1 }$ for the Mahalanobis distance and

$$
A = \frac {\sum_ {m = 1} ^ {M} \rho_ {m} \cdot i _ {m} (\mathbf {x} , \mathbf {c}) \cdot C _ {m} ^ {- 1}}{\sum_ {m = 1} ^ {M} \rho_ {m} \cdot i _ {m} (\mathbf {x} , \mathbf {c})}\tag{8}
$$

for the Weighted Mahalanobis distance, where $\mu _ { m } , C _ { m }$ , and $\rho _ { m }$ denote the mean, covariance matrix, and mixing probability of the m-th Gaussian component of a GMM fitted to TR, and the term $i _ { m } ( \mathbf { x } , \mathbf { c } )$ approximates the integral over the path from x to c with respect to the measure induced by the Gaussian Mixture Model (GMM). We refer the reader to [Tipping, 1999] for an explanation of the rationale behind this distance.

## 2.2.1 Selecting Centroids by Maximizing the Information Gain

In Section 4.3 of the paper, we propose a centroid selection strategy that consists in maximizing the information gain introduced by the split that divides $\mathcal { X } _ { k - 1 }$ in $\mathcal { X } _ { k }$ and $\overline { { \mathcal { X } _ { k } } } = \mathcal { X } _ { k - 1 } \backslash \mathcal { X } _ { k } .$ , namely:

$$
\mathbf {c} _ {k} = \underset {\mathbf {c} \in \mathcal {X} _ {k - 1}} {\operatorname{argmax}} I [ \mathbf {c} ] = \underset {\mathbf {c} \in \mathcal {X} _ {k - 1}} {\operatorname{argmax}} \left\{H (\mathcal {X} _ {k - 1}) - \frac {| \overline {{\mathcal {X} _ {k}}} | H (\overline {{\mathcal {X} _ {k}}}) + | \mathcal {X} _ {k} | H (\mathcal {X} _ {k})}{| \mathcal {X} _ {k - 1} |} \right\},\tag{9}
$$

where $H ( B )$ is the entropy of a set of points $B \subset \mathbb { R } ^ { d }$ , which we compute by its Gaussian approximation, that is

$$
H (B) = (1 / 2) \log \Big ((2 \pi e) ^ {d} \det (\operatorname{cov} [ B ]) \Big),\tag{10}
$$

where e is Euler’s number. This approximation is only used to ease the computation of $H ( B )$ for centroid selection purposes, and does not influence the non-parametric nature of KQT. The expression in (10) can be reformulated:

$$
H (B) = \frac {d}{2} (\log (2 \pi) + 1) + \widetilde {H} (B)\tag{11}
$$

where $\begin{array} { r } { \widetilde { H } ( B ) = \log \operatorname* { d e t } \left( \operatorname { c o v } [ B ] \right) } \end{array}$ . This gives rise to an optimization problem equivalent to (9), where the centroid is selected by

$$
\mathbf {c} _ {k} = \underset {\mathbf {c} \in \mathcal {X} _ {k - 1}} {\operatorname{argmin}} \Big \{\widetilde {H} (\overline {{\mathcal {X}}} _ {k}) + \beta \widetilde {H} (\mathcal {X} _ {k}) \Big \},\tag{12}
$$

where $\beta$ is a constant that can be derived by (9) through algebraic manipulation. Solving this minimization problem is computationally less demanding than the original maximization, thus lowering the computational burden of such centroid selection strategy.

## 2.2.2 Invariance to roto-translations

In Section 5.3 of the main article, we state that KQT is invariant under roto-translations when the employed kernel function is either the Euclidean, Mahalanobis or Weighted Mahalanobis distance. Here, we prove it together with an intermediate result. In the following, we define a roto-translation $\Phi : \mathbb { R } ^ { d }  \mathbb { R } ^ { d }$ as

$$
\Phi (\mathbf {x}) = R (\mathbf {x} - \mu),\tag{13}
$$

where $R \in S O ( d )$ is the rotation matrix and $\mu \in \mathbb { R } ^ { d }$ is the shift vector. Moreover, we denote as $\Phi ( B ) = \{ \Phi ( \mathbf { x } ) \mid \mathbf { x } \in B \}$ the image of a set $B \subset \mathbb { R } ^ { d }$ . From basic calculus, it is easy to show that the covariance of a set $B \subset  { \mathbb { R } } ^ { d }$ after roto-translation Φ factorizes as

$$
\operatorname{cov} [ \Phi (B) ] = R \operatorname{cov} [ B ] R ^ {\intercal}.\tag{14}
$$

Moreover, in our discussion, we will denote as $D : \mathbb { R } ^ { d }  \mathbb { R } ^ { d }$ the distance employed by KQT when no preprocessing is employed, while we denote as $D ^ { \prime }$ the same distance when data are preprocessed by a roto-translation Φ. D and $D ^ { \prime }$ coincide when we employ the Euclidean distance, where A is simply the indentity matrix. However, the kernel matrices for the Mahalanobis and Weighted Mahalanobis distances depend on the training set TR, thus change when we transform it to $\mathrm { T R } ^ { \prime } = \Phi ( \mathrm { T R } )$ Nevertheless, all the considered distances are invariant under roto-translation, namely it holds that

$$
D (\mathbf {x}, \mathbf {y}) = D ^ {\prime} (\Phi (\mathbf {x}), \Phi (\mathbf {y}))\tag{15}
$$

for any $\mathbf { x } , \mathbf { y } \in \mathbb { R } ^ { d }$ . The identity in (15) can be derived from algebraic manipulation of the definition of the adopted distances and considering (14).

Theorem 5.5 of the main article, which we report here, states that the histograms $h = \{ ( S _ { k } , \widehat { \pi } _ { k } ) \}$ and $h ^ { \prime } = \{ ( S _ { k } ^ { \prime } , \widehat { \pi } _ { k } ^ { \prime } ) \}$ , respectively constructed by KQT with and without preprocessing TR by Φ, are equivalent.

Theorem 2. Let $\Phi : \mathbb { R } ^ { d }  \mathbb { R } ^ { d }$ be a roto-translation. Let $h = \{ ( S _ { k } , \widehat { \pi } _ { k } ) \}$ and $h ^ { \prime } = \{ ( S _ { k } ^ { \prime } , \widehat { \pi } _ { k } ^ { \prime } ) \}$ be the KQT histograms constructed from the training sets $\mathrm { T R } \subset \mathbb { R } ^ { d }$ and $\mathrm { T R } ^ { \prime } = \Phi ( \mathrm { T R } )$ , where the employed kernel function is either the Euclidean, Mahalanobis or Weighted Mahalanobis distance. Then, we have that $S _ { k } ^ { \prime } = \Phi ( S _ { k } )$ and $\widehat { \pi } _ { k } ^ { \prime } = \widehat { \pi } _ { k } ~ f o r ~ k = 1 \ldots , K$ . In particular, for any batch W and $W ^ { \prime } = \Phi ( W )$ we have that $\mathcal { T } _ { h } ( W ) = \mathcal { T } _ { h ^ { \prime } } ( W ^ { \prime } )$

Theorem 2 proves that, for specific choices of kernel functions, the value of the test statistic computed over a batch W of data does not change if we employ a roto-translation-based preprocessing. As such, KQT does not require preprocessing by PCA, which is sometimes necessary for QT to achieve good detection performance. To prove the theorem, we first prove an intermediate result regarding the centroid selection:

Lemma 1 (Information Gain). Let $\mathcal { X } _ { k - 1 }$ and $\mathcal { X } _ { k - 1 } ^ { \prime } = \Phi ( \mathcal { X } _ { k - 1 } )$ be the set of points used to construct the KQT histogram bins $S _ { k }$ and $S _ { k } ^ { \prime }$ , respectively. Then, the centroid selection by maximizing the information gain as in (9) results in centroids $\mathbf { c } _ { k }$ and $\mathbf { c } _ { k } ^ { \prime } = \Phi ( \mathbf { c } _ { k } )$

Proof. As showed in Section 2.2.1, maximizing (9) is equivalent to minimizing (12). Let $\mathbf { c } \in \mathcal { X } _ { k - 1 }$ be an available training sample, then there exists $\mathbf { c } ^ { \prime } = \boldsymbol { \Phi } ( \mathbf { c } ) \in \mathcal { X } _ { k - 1 } ^ { \prime }$ . If we assume that $\mathcal { X } _ { k } ^ { \prime }$ is the set of training samples falling in $S _ { k } ^ { \prime }$ when we use c as a centroid, we have that

$$
\begin{array}{l} \mathcal {X} _ {k} ^ {\prime} = \{\mathbf {x} ^ {\prime} \in \mathcal {X} _ {k - 1} ^ {\prime} \mid D ^ {\prime} (\mathbf {x} ^ {\prime}, \mathbf {c} ^ {\prime}) \leq q _ {k} ^ {\prime} \} = \\ \quad = \{\Phi (\mathbf {x}) \mid \mathbf {x} \in \mathcal {X} _ {k - 1}, D ^ {\prime} (\Phi (\mathbf {x}), \Phi (\mathbf {c})) \leq q _ {k} ^ {\prime} \} = \\ \quad = \{\Phi (\mathbf {x}) \mid \mathbf {x} \in \mathcal {X} _ {k - 1}, D (\mathbf {x}, \mathbf {c}) \leq q _ {k} \} = \\ \quad = \Phi \left(\{\mathbf {x} \in \mathcal {X} _ {k - 1} \mid D (\mathbf {x}, \mathbf {c}) \leq q _ {k} \}\right) = \Phi (\mathcal {X} _ {k}), \end{array}\tag{16}
$$

where we used (15) to substitute $q _ { k } ^ { \prime }$ with $q _ { k }$ . Analogously, we have that $\overline { { \mathcal { X } } } _ { k } ^ { \prime } = \Phi ( \overline { { \mathcal { X } } } _ { k } )$ . Then, from (12), we have that

$$
\begin{array}{r l} & {\widetilde {H} (\mathcal {X} _ {k} ^ {\prime}) = \mathrm{logdet} (\mathrm{cov} [ \mathcal {X} _ {k} ^ {\prime} ]) =} \\ & {\qquad = \mathrm{logdet} (R \mathrm{cov} [ \mathcal {X} _ {k} ] R ^ {\intercal}) =} \\ & {\qquad = \mathrm{logdet} (\mathrm{cov} [ \mathcal {X} _ {k} ]) + 2 \mathrm{logdet} (R) = \widetilde {H} (\mathcal {X} _ {k}) + \gamma ,} \end{array}\tag{17}
$$

where $\gamma$ is a constant which depends only on R. In (17), we used the factorization (14) and the fact

that R is orthogonal. The same relation holds for $\overline { { \mathcal { X } } } _ { k } ^ { \prime }$ , and we can finally prove that

$$
\begin{array}{l} \mathbf {c} _ {k} ^ {\prime} = \underset {\mathbf {c} \in \mathcal {X} _ {k - 1} ^ {\prime}} {\operatorname{argmin}} \left\{\widetilde {H} (\overline {{\mathcal {X}}} _ {k} ^ {\prime}) + \beta \widetilde {H} (\mathcal {X} _ {k} ^ {\prime}) \right\} = \\ \qquad = \Phi \left(\underset {\mathbf {c} \in \mathcal {X} _ {k - 1}} {\operatorname{argmin}} \left\{\widetilde {H} (\overline {{\mathcal {X}}} _ {k}) + \beta \widetilde {H} (\mathcal {X} _ {k}) + \gamma (1 + \beta) \right\}\right) = \\ \qquad = \Phi \left(\underset {\mathbf {c} \in \mathcal {X} _ {k - 1}} {\operatorname{argmin}} \left\{\widetilde {H} (\overline {{\mathcal {X}}} _ {k}) + \beta \widetilde {H} (\mathcal {X} _ {k}) \right\}\right) = \Phi (\mathbf {c} _ {k}). \end{array}\tag{18}
$$

Lemma 2 (Gini Index). Let $\mathcal { X } _ { k - 1 }$ and $\mathcal { X } _ { k - 1 } ^ { \prime } = \Phi ( \mathcal { X } _ { k - 1 } )$ be the set $o f$ points used to construct the $K Q T$ histogram bins $S _ { k }$ and $S _ { k } ^ { \prime }$ , respectively. Then, the centroid selection $b y$ minimizing the Gini index in results in centroids $\mathbf { c } _ { k }$ and $\mathbf { c } _ { k } ^ { \prime } = \Phi ( \mathbf { c } _ { k } )$

Proof. It can be shown by simple algebraic manipulation of the definition of Gini index.

Lemma 1 and Lemma 2 ensure that the construction of the histograms h and $h ^ { \prime }$ will maintain the correspondance through Φ of all their elements, including the selected centroids. We can now prove Theorem 2.

Proof of Theorem 2. Here, we show by induction that every bin $S _ { k } ^ { \prime }$ of $h ^ { \prime }$ is the result of the rototranslation of the corresponding bin $S _ { k }$ of h. First, we have that $\ddot { \mathcal { X } } _ { 0 } ^ { \prime } = \mathrm { T R } ^ { \prime } = \Phi ( \mathrm { T R } ) = \Phi ( \mathcal { X } _ { 0 } )$ by definition. Then, for $k = 1$ , Lemma 1 and 2 state that $\mathbf { c } _ { 1 } ^ { \prime } = \Phi ( \mathbf { c } _ { 1 } )$ . Moreover,

$$
\begin{array}{r l} & S _ {1} ^ {\prime} = \left\{\mathbf {x} ^ {\prime} \in \mathbb {R} ^ {d} \mid D ^ {\prime} (\mathbf {x} ^ {\prime}, \mathbf {c} _ {1} ^ {\prime}) \leq q _ {1} ^ {\prime} \right\} = \\ & \qquad = \left\{\Phi (\mathbf {x}) \mid \mathbf {x} \in \mathbb {R} ^ {d}, D ^ {\prime} (\Phi (\mathbf {x}), \mathbf {c} _ {1} ^ {\prime}) \leq q _ {1} ^ {\prime} \right\} = \\ & \qquad = \left\{\Phi (\mathbf {x}) \mid \mathbf {x} \in \mathbb {R} ^ {d}, D (\mathbf {x}, \mathbf {c} _ {1}) \leq q _ {1} \right\} = \Phi (S _ {1}). \end{array}\tag{19}
$$

In the same manner, we prove that

$$
\begin{array}{c} X _ {1} ^ {\prime} = \{\mathbf {x} ^ {\prime} \in \mathcal {X} _ {0} ^ {\prime} \mid D ^ {\prime} (\mathbf {x} ^ {\prime}, \mathbf {c} _ {1} ^ {\prime}) > q _ {1} ^ {\prime} \} = \\ = \{\Phi (\mathbf {x}) \mid \mathbf {x} \in \mathcal {X} _ {0}, D (\mathbf {x}, \mathbf {c} _ {1}) > q _ {1} ^ {\prime} \} = \Phi (\mathcal {X} _ {1}), \end{array}\tag{20}
$$

and $\overline { { \mathcal { X } } } _ { 1 } ^ { \prime } = \Phi ( \overline { { \mathcal { X } } } _ { 1 } )$

Now, suppose that $\forall j < k$ we have that $\mathbf { c } _ { j } ^ { \prime } = \Phi ( \mathbf { c } _ { j } ) , S _ { j } ^ { \prime } = \Phi ( S _ { j } )$ and $\mathcal { X } _ { j } ^ { \prime } = \Phi ( \mathcal { X } _ { j } )$ . Then, we have that $\begin{array} { r } { \mathbf { x } \in \bigcap _ { j < k } \overline { { S _ { j } } } \iff \mathbf { x } ^ { \prime } = \Phi ( \mathbf { x } ) \in \bigcap _ { j < k } \overline { { S _ { j } ^ { \prime } } } } \end{array}$ , and, with the same derivation as in the case $k = 1$ ，

$$
\begin{array}{l} S _ {k} ^ {\prime} = \left\{\mathbf {x} ^ {\prime} \in \bigcap_ {j <   k} \overline {{S _ {j} ^ {\prime}}} \mid D ^ {\prime} (\mathbf {x} ^ {\prime}, \mathbf {c} _ {k} ^ {\prime}) \leq q _ {k} \right\} = \\ \qquad = \Phi \Big (\left\{\mathbf {x} \in \bigcap_ {j <   k} \overline {{S _ {j}}} \mid D (\mathbf {x}, \mathbf {c} _ {k}) \leq q _ {k}) \right\} \Big) = \Phi (S _ {k}). \end{array}\tag{21}
$$

and also $\mathcal { X } _ { k } ^ { \prime } = \Phi ( \mathcal { X } _ { k } )$ . In conclusion, we proved that $S _ { k } ^ { \prime } = \Phi ( S _ { k } ) { \mathrm { ~ f o r ~ } } \forall k = 1 , \dots , K$ . In particular, we conclude that

$$
\begin{array}{r l} \mathbf {x} \in S _ {k} & \Longleftrightarrow D (\mathbf {x}, \mathbf {c} _ {j}) > q _ {j} \forall j <   k \land D (\mathbf {x}, \mathbf {c} _ {k}) \leq q _ {k} \Longleftrightarrow \\ & \Longleftrightarrow D ^ {\prime} (\Phi (\mathbf {x}), \mathbf {c} _ {j} ^ {\prime}) > q _ {j} \forall j <   k \land D ^ {\prime} (\Phi (\mathbf {x}), \mathbf {c} _ {k} ^ {\prime}) \leq q _ {k} \Longleftrightarrow \\ & \Longleftrightarrow \Phi (\mathbf {x}) \in S _ {k} ^ {\prime}, \end{array}\tag{22}
$$

and, consequently, the number of samples from any batch $W \subset \mathbb { R } ^ { d }$ falling in the $S _ { k }$ is the same as the number of samples of $W ^ { \prime } = \Phi ( W )$ falling in $S _ { k } ^ { \prime }$ . Then, we have that $\widehat { \pi } _ { k } = \widehat { \pi } _ { k } ^ { \prime }$ and ${ \mathcal { T } } _ { h } ( W ) =$ $\mathcal { T } _ { h ^ { \prime } } ( W ^ { \prime } )$ □

## 3 More Experiments and Discussion

This section extends the experimental evaluation of KQT from Section 6 of the main article to cor roborate the findings discussed there. First, we investigate the real-world datasets employed in our experiments, proving that these do not follow a Gaussian distribution. Then, we perform additional experiments on high-dimensional data to investigate the control of the FPR in this challenging sce nario. Finally, we extend the results from the main article by comparing the proposed centroid selection strategies and reporting the complete results for both the low- and high-ratio settings.

## 3.1 Remarks about the real-world datasets

In Section 6.1 of the main article, we introduce the real-world datasets that are used in our experiments. The INSECTS dataset [Souza et al., 2020] is a benchmark for concept-drift detection algorithms and comprises data describing the wing-beat frequency of six species of insects at diferent temperatures. The other datasets are from the UCI Machine Learning Repository [Dua and Graf, 2017] and from [Dal Pozzolo et al., 2017], and comprise data following a unique distribution, thus require the introduction of artificial distribution changes for our experiments. We standardize these datasets and add a negligible amount of noise $\eta \sim N ( 0 , \sigma )$ to each component to prevent the many repeated values from harming the histogram construction. Table 1 lists all the datasets and reports their dimension d and the level σ of noise applied to their components.

Since data in the synthetic settings are drawn from Gaussian distributions, one could argue that KQT provided with the Mahalanobis or Weighted Mahalanobis kernels have an advantage over the alternatives. However, this is not true for the real-world datasets considered in our experiments, which are far from Gaussian. This claim is empirically supported by the low detection performance of SPLL, which is itself based on a GMM. To confirm this intuition, we also run the Shapiro-Wilk normality test [Shapiro and Wilk, 1965], an Hypothesis Test used to determine whether a population $\{ x _ { i } \} _ { i = 1 } ^ { n } \subset \mathbb { R }$ is drawn from a univariate Gaussian distribution. If the p-values associated to the HT is lower than 0.05, than we can conclude that the population is not normally distributed. Since the marginals of a multivariate Gaussian distribution are univariate Gaussian distributions, we show that the real-world datasets introduced in Section 6.1 of the main article are not drawn from multivariate Gaussians by showing that their covariates are not. For this purpose, we extract a subset of $n = 4 0 9 6$ samples from the real-world datasets and perform the Shapiro-Wilk test on each of their covariates. Table 1 reports the p-values yielded by the test, averaged over the covariates and over 250 iteration of the test performed over diferent subsets. The p-values obtained in these tests are in the range of $1 0 ^ { - 2 0 }$ , thus confirming that the real-world datasets employed in our experiments are not drawn from multivariate Gaussian distributions.

Table 1: List of the real-world datasets employed in the experiments. For each dataset, we report the dimension d, the noise level σ and the average p-value of the Shapiro-Wilk test computed on the marginals.

<table><tr><td>Dataset</td><td>Name</td><td>d</td><td>σ</td><td>p-value</td><td>Reference</td></tr><tr><td>El Nino Southern Oscillation</td><td>nino</td><td>5</td><td> $10^{-3}$ </td><td> $3.3 \times 10^{-3}$ </td><td>[Dua and Graff, 2017]</td></tr><tr><td>Physicochemical Properties of PTS</td><td>protein</td><td>9</td><td>-</td><td> $7.5 \times 10^{-8}$ </td><td>[Dua and Graff, 2017]</td></tr><tr><td>ForestCovertype I</td><td>spruce</td><td>10</td><td> $10^{-1}$ </td><td> $2.5 \times 10^{-9}$ </td><td>[Dua and Graff, 2017]</td></tr><tr><td>ForestCovertype II</td><td>lodgepole</td><td>10</td><td> $10^{-1}$ </td><td> $1.8 \times 10^{-8}$ </td><td>[Dua and Graff, 2017]</td></tr><tr><td>Credit Card Fraud Detection</td><td>credit</td><td>28</td><td> $10^{-3}$ </td><td> $9.9 \times 10^{-8}$ </td><td>[Dal Pozzolo et al., 2017]</td></tr><tr><td>Insects&#x27; Flying Behavior</td><td>INSECTS</td><td>33</td><td>-</td><td> $< 10^{-16}$ </td><td>[Souza et al., 2020]</td></tr><tr><td>Sensorless Drive Diagnosis</td><td>sensorless</td><td>48</td><td> $10^{-3}$ </td><td> $4.9 \times 10^{-8}$ </td><td>[Dua and Graff, 2017]</td></tr><tr><td>MiniBooNE Particle Identification</td><td>particle</td><td>50</td><td> $10^{-3}$ </td><td> $8.5 \times 10^{-3}$ </td><td>[Dua and Graff, 2017]</td></tr><tr><td>UNSW Swarm Behavior</td><td>swarm</td><td>2400</td><td>-</td><td> $1.8 \times 10^{-9}$ </td><td>[Dua and Graff, 2017]</td></tr></table>

## 3.2 Curse of dimensionality

In this section, we investigate the ability of KQT to control the FPR as the data dimension d increases. Our experiments (Section 6.4 of the main article) have shown that the Kernel QuantTree with the Weighted Mahalanobis distance deviates from the desired FPR when the data dimension grows. As discussed in the article, this deviation is due to the challenge of fitting a Gaussian Mixture Model (GMM) to high-dimensional data. To analyze the impact of the dimensionality on Kernel QuantTree, we perform experiments in three synthetic settings with d $\in \{ 4 , 8 , 1 6 , 3 2 , 6 4 , 1 2 8 \}$ . In these settings, denoted as unimodal, bimodal, and trimodal, the stationary distribution ϕ is defined as a GMM with 1, 2, and 3 Gaussian components, respectively. Then, we use the CCM framework [Alippi et al., 2017] to generate a post-change distribution by applying a roto-translation to each Gaussian component of $\phi _ { 0 }$ such that the Kullback-Leibler distance between these and the three resulting post-change components is fixed to 1. We perform each experiment twice, one with $N = 4 0 9 6$ training samples and the other with $N = 1 6 3 8 4$ , to show that when a large training set is available the limitation of the KQT with Weighted Mahalanobis is avoidable.

Table 2 reports the FPR achieved by KQT adopting diferent distances in the unimodal, bimodal and trimodal settings for all the considered dimensions d and training set sizes N. In all experiments we construct a KQT histogram with $K = 1 6$ bins, we set the detection thresholds to yield an FPR $\alpha = 5 \%$ , and we test KQT on 5000 stationary batches with $\nu = 1 2 8$ samples. In the experiment with $N = 4 0 9 6$ (left columns), we notice that when d increases, the FPR achieved by KQT when using the Mahalanobis and Weighted Mahalanobis distances deviates further from the target value. In contrast, when we train KQT on N = 16384 samples (right columns), the deviation from the target FPR is significantly reduced. To further corroborate our hypothesis that the issue is in the GMM fitting, we compute the average condition number of the covariance matrices of the GMM components yielded when using KQT with the Weighted Mahalanobis distance. These results show that, in the high-dimensional datasets, using a larger training set yields covariance matrices with smaller condition numbers.

## 3.3 Comparing the centroid selection strategies

In the main article, we propose two strategies for the centroid selection, namely, maximizing the information gain introduced by splitting $\mathcal { X } _ { k - 1 }$ in $\mathcal { X } _ { k }$ and $\overline { { \mathcal { X } } } _ { k }$ and minimizing the Gini index of the distances between the centroid and the training samples in $\mathcal { X } _ { k - 1 }$ . In Table 1 of the article, we report the average FPR and AUC achieved by KQT using the maximization of the information gain as a centroid selection strategy. Here, Table 3 reports the results achieved by KQT with the Euclidean, Mahalanobis, and Weighted Mahalanobis distance for both strategies and proves that their performance is comparable in every experimental setting.

## 3.4 Complete experimental results

In this section, we report the complete results of the high- and low-ratio experiments presented in Section 6 of the main article. For each result, we include the corresponding confidence interval.

Table 5 reports the FPR and AUC achieved by the methods presented in Section 6.3 of the main article in the high-ratio setting, namely when $\nu = 1 2 8$ and $K = 1 6$ . As already discussed in the paper, QuantTree, Kernel QuantTree and EIKM achieve an empirical FPR close to the target $\alpha = 5 \%$ in most experiments. In contrast, SPLL and PCA-SPLL mostly exceed the target and Density Tree largely overshoots it. However, the KQT with the Weighted Mahalanobis distance does not control the FPR accurately when d increases, and we speculate that this is due to the GMM underlying the definition of distance. This known limitation is discussed in Section 6.4 of the main article and investigated in Section 3.2 of this document.

As for the AUC, KQT with the Weighted Mahalanobis distances outperforms the alternatives in most settings. At the bottom of Table 5, we report the ranking of each method computed from the

Table 2: Comparison between the FPR achieved by KQT using the Euclidean, Mahalanobis, and Weighted Mahalanobis distances in the synthetic settings for various dimensions d and training set sizes N. In parenthesis, the average condition numbers of the covariance matrices of the GMM used by KQT with the Weighted Mahalanobis distance. The underlined values indicate an FPR above the target of 5%.

<table><tr><td rowspan="2"></td><td colspan="2">KQT(Euclidean)</td><td colspan="2">KQT(Mahalanobis)</td><td colspan="2">KQT(Weighted Mahalanobis)</td></tr><tr><td>N=4096</td><td>N=16384</td><td>N=4096</td><td>N=16384</td><td>N=4096</td><td>N=16384</td></tr><tr><td>d=4</td><td>4.88%</td><td>-</td><td>4.77%</td><td>4.84%</td><td>4.79% (20.1)</td><td>4.85% (16.3)</td></tr><tr><td>d=8</td><td>4.83%</td><td>-</td><td>4.81%</td><td>4.86%</td><td>4.71% (32.1)</td><td>4.83% (37.7)</td></tr><tr><td>d=16</td><td>4.81%</td><td>-</td><td>4.81%</td><td>4.89%</td><td>4.88% (99.5)</td><td>4.79% (67.7)</td></tr><tr><td>d=32</td><td>4.84%</td><td>-</td><td>4.95%</td><td>4.88%</td><td>4.99% (150.6)</td><td>4.81% (123.6)</td></tr><tr><td>d=64</td><td>4.84%</td><td>-</td><td> $\underline{5.80\%}$ </td><td>4.95%</td><td> $\underline{5.81\%}$  (315.2)</td><td>4.87% (223.8)</td></tr><tr><td>d=128</td><td>4.91%</td><td>-</td><td> $\underline{16.52\%}$ </td><td>5.31%</td><td> $\underline{77.74\%}$  (344.0)</td><td>5.45% (307.0)</td></tr><tr><td>d=4</td><td>4.83%</td><td>-</td><td>4.76%</td><td>4.88%</td><td>4.77% (12.9)</td><td>4.89% (13.7)</td></tr><tr><td>d=8</td><td>4.88%</td><td>-</td><td>4.86%</td><td>4.87%</td><td>4.79% (40.0)</td><td>4.84% (36.3)</td></tr><tr><td>d=16</td><td>4.83%</td><td>-</td><td>4.88%</td><td>4.82%</td><td>4.88% (68.3)</td><td>4.87% (90.3)</td></tr><tr><td>d=32</td><td>4.86%</td><td>-</td><td>4.95%</td><td>4.86%</td><td> $\underline{5.36\%}$  (177.2)</td><td>4.83% (120.4)</td></tr><tr><td>d=64</td><td>4.89%</td><td>-</td><td> $\underline{5.66\%}$ </td><td>4.86%</td><td> $\underline{5.70\%}$  (253.9)</td><td> $\underline{5.03\%}$  (220.3)</td></tr><tr><td>d=128</td><td>4.84%</td><td>-</td><td> $\underline{15.44\%}$ </td><td>5.32%</td><td> $\underline{76.60\%}$  (276.9)</td><td>5.46% (244.7)</td></tr><tr><td>d=4</td><td>4.72%</td><td>-</td><td>4.86%</td><td>4.85%</td><td>4.82% (24.9)</td><td>4.84% (16.1)</td></tr><tr><td>d=8</td><td>4.84%</td><td>-</td><td>4.79%</td><td>4.82%</td><td>4.83% (31.7)</td><td>4.80% (38.2)</td></tr><tr><td>d=16</td><td>4.85%</td><td>-</td><td>4.85%</td><td>4.80%</td><td>4.86% (66.1)</td><td>4.83% (59.9)</td></tr><tr><td>d=32</td><td>4.81%</td><td>-</td><td>4.91%</td><td>4.84%</td><td> $\underline{5.13\%}$  (108.7)</td><td>4.86% (120.7)</td></tr><tr><td>d=64</td><td>4.93%</td><td>-</td><td> $\underline{5.67\%}$ </td><td>4.87%</td><td> $\underline{5.53\%}$  (209.4)</td><td>5.01% (176.9)</td></tr><tr><td>d=128</td><td>4.81%</td><td>-</td><td> $\underline{15.86\%}$ </td><td>5.37%</td><td> $\underline{77.49\%}$  (258.1)</td><td> $\underline{5.47\%}$  (214.2)</td></tr></table>

AUC, together with the p-value of the Nemenyi post-hoc statistic, which proves that the advantage of the best-performing method is statistically significant. In the main article, we also discuss the performance of QuantTree, which shows how the preprocessing by PCA decreases the detection performance in some cases. Remarkably, the KQT monitoring is invariant under roto-translations (see Section 5.3 of the main article) and surpasses QuantTree independently of the application of the PCA preprocessing.

Table 4 reports the FPR and AUC achieved by the considered methods in the low-ratio setting, namely when ν = 64 and K = 32. The results of this experiment are overall in line with the high-ratio setting. However, as we speculate in Section 6.3 of the main article, histogram can better model a data distribution when the expected number of points per bin ν/K is large. This low-ratio setting confirms our speculation, as the considered methods achieve an AUC lower than in the high-ratio experiment on most datasets. However, KQT with the Weighted Mahalanobis distance still achieves the best AUC with a statistically significant advantage over the alternatives, as demonstrated by the Nemenyi post-hoc test. Moreover, the Pearson test statistic is discrete and in the low-ratio setting assumes fewer distinct values. Thus, it is more challenging to set detection thresholds and the results show that the empirical FPR of QuantTree and Kernel QuantTree is slightly lower than in the high-ratio experiment.

Table 3: Comparison between the detection performance achieved by KQT with the Euclidean, Mahalanobis and Weighted Mahalanobis distances, when selecting the centroids by maximization of the Information Gain (left) and minimization of the Gini Index (right), in the high-ratio setting (K = 16, ν = 128 points). The table reports the achieved FPR (top) and AUC (bottom). In parenthesis the standard deviation.

<table><tr><td rowspan="2"></td><td colspan="3">Information Gain</td><td colspan="3">Gini Index</td></tr><tr><td>Euclidean</td><td>Mahalanobis</td><td>Weighted Maha.</td><td>Euclidean</td><td>Mahalanobis</td><td>Weighted Maha.</td></tr><tr><td>unimodal</td><td>4.86% (0.47%)</td><td>4.82% (0.45%)</td><td>4.83% (0.48%)</td><td>4.83% (0.47%)</td><td>4.81% (0.48%)</td><td>4.83% (0.49%)</td></tr><tr><td>bimodal</td><td>4.80% (0.46%)</td><td>4.81% (0.44%)</td><td>4.80% (0.45%)</td><td>4.81% (0.47%)</td><td>4.84% (0.46%)</td><td>4.83% (0.46%)</td></tr><tr><td>nino</td><td>5.00% (0.53%)</td><td>5.02% (0.53%)</td><td>5.01% (0.54%)</td><td>5.02% (0.55%)</td><td>5.06% (0.54%)</td><td>5.02% (0.54%)</td></tr><tr><td>protein</td><td>4.97% (0.52%)</td><td>4.98% (0.54%)</td><td>5.03% (0.55%)</td><td>4.99% (0.54%)</td><td>5.03% (0.56%)</td><td>5.06% (0.53%)</td></tr><tr><td>spruce</td><td>4.82% (0.47%)</td><td>4.84% (0.49%)</td><td>4.90% (0.47%)</td><td>4.84% (0.49%)</td><td>4.85% (0.48%)</td><td>4.88% (0.49%)</td></tr><tr><td>lodgepole</td><td>4.85% (0.49%)</td><td>4.80% (0.47%)</td><td>4.90% (0.50%)</td><td>4.84% (0.50%)</td><td>4.82% (0.49%)</td><td>4.93% (0.51%)</td></tr><tr><td>credit</td><td>4.89% (0.48%)</td><td>4.85% (0.46%)</td><td>5.06% (0.56%)</td><td>4.89% (0.50%)</td><td>4.90% (0.52%)</td><td>5.10% (0.61%)</td></tr><tr><td>insects (1 → 2)</td><td>4.91% (0.50%)</td><td>4.93% (0.52%)</td><td>5.19% (0.64%)</td><td>4.90% (0.49%)</td><td>4.92% (0.54%)</td><td>5.19% (0.61%)</td></tr><tr><td>insects (2 → 3)</td><td>4.92% (0.52%)</td><td>4.96% (0.52%)</td><td>5.25% (0.62%)</td><td>4.88% (0.50%)</td><td>4.93% (0.52%)</td><td>5.24% (0.63%)</td></tr><tr><td>insects (3 → 4)</td><td>4.90% (0.52%)</td><td>4.88% (0.53%)</td><td>5.22% (0.64%)</td><td>4.91% (0.55%)</td><td>4.92% (0.53%)</td><td>5.24% (0.64%)</td></tr><tr><td>insects (4 → 5)</td><td>4.91% (0.51%)</td><td>4.92% (0.54%)</td><td>5.25% (0.65%)</td><td>4.92% (0.52%)</td><td>4.95% (0.49%)</td><td>5.28% (0.66%)</td></tr><tr><td>insects (5 → 6)</td><td>4.90% (0.56%)</td><td>4.92% (0.53%)</td><td>5.26% (0.72%)</td><td>4.90% (0.55%)</td><td>4.91% (0.57%)</td><td>5.29% (0.71%)</td></tr><tr><td>sensorless</td><td>4.82% (0.49%)</td><td>5.01% (0.56%)</td><td>7.42% (1.61%)</td><td>4.87% (0.48%)</td><td>4.98% (0.58%)</td><td>7.54% (1.56%)</td></tr><tr><td>particle</td><td>4.81% (0.46%)</td><td>4.94% (0.52%)</td><td>5.80% (1.02%)</td><td>4.84% (0.48%)</td><td>4.93% (0.52%)</td><td>5.86% (1.00%)</td></tr><tr><td>unimodal</td><td>0.946 (0.105)</td><td>0.993 (0.016)</td><td>0.994 (0.013)</td><td>0.946 (0.103)</td><td>0.994 (0.015)</td><td>0.994 (0.014)</td></tr><tr><td>bimodal</td><td>0.904 (0.118)</td><td>0.954 (0.060)</td><td>0.968 (0.042)</td><td>0.903 (0.119)</td><td>0.955 (0.056)</td><td>0.970 (0.039)</td></tr><tr><td>nino</td><td>0.607 (0.072)</td><td>0.904 (0.138)</td><td>0.922 (0.122)</td><td>0.609 (0.071)</td><td>0.903 (0.139)</td><td>0.922 (0.122)</td></tr><tr><td>protein</td><td>0.617 (0.074)</td><td>0.993 (0.035)</td><td>0.995 (0.027)</td><td>0.615 (0.074)</td><td>0.993 (0.030)</td><td>0.994 (0.030)</td></tr><tr><td>spruce</td><td>0.601 (0.066)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.600 (0.068)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td></tr><tr><td>lodgepole</td><td>0.654 (0.099)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.653 (0.099)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td></tr><tr><td>credit</td><td>0.602 (0.053)</td><td>0.780 (0.146)</td><td>1.000 (0.000)</td><td>0.605 (0.055)</td><td>0.787 (0.141)</td><td>1.000 (0.000)</td></tr><tr><td>insects (1 → 2)</td><td>0.962 (0.035)</td><td>0.972 (0.039)</td><td>0.993 (0.019)</td><td>0.961 (0.038)</td><td>0.970 (0.037)</td><td>0.994 (0.015)</td></tr><tr><td>insects (2 → 3)</td><td>1.000 (0.001)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>1.000 (0.001)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td></tr><tr><td>insects (3 → 4)</td><td>0.904 (0.054)</td><td>0.942 (0.049)</td><td>0.990 (0.024)</td><td>0.903 (0.058)</td><td>0.946 (0.044)</td><td>0.989 (0.025)</td></tr><tr><td>insects (4 → 5)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td></tr><tr><td>insects (5 → 6)</td><td>0.985 (0.016)</td><td>0.992 (0.008)</td><td>1.000 (0.000)</td><td>0.986 (0.014)</td><td>0.991 (0.009)</td><td>1.000 (0.001)</td></tr><tr><td>sensorless</td><td>0.542 (0.027)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.543 (0.026)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td></tr><tr><td>particle</td><td>0.555 (0.030)</td><td>0.976 (0.051)</td><td>0.985 (0.039)</td><td>0.556 (0.032)</td><td>0.977 (0.051)</td><td>0.985 (0.042)</td></tr></table>

Table 4: FPR (top) and AUC (bottom) achieved by the considered methods in the high-ratio setting, namely when histogram-based methods define K = 32 bins and the monitored batches contain ν = 64 points. In parenthesis, the width of the 95%-confidence interval of the results.

<table><tr><td></td><td>QT</td><td>QT (PCA)</td><td>KQT (Euclidean)</td><td>KQT (Mahalanobis)</td><td>KQT (Weighted Maha.)</td><td>ElkM</td><td>SPLL(C=3)</td><td>SPLL(C=3) (PCA)</td><td>DT</td><td>DT (PCA)</td></tr><tr><td>unimodal</td><td>4.29% (0.34%)</td><td>4.27% (0.32%)</td><td>4.30% (0.32%)</td><td>4.30% (0.34%)</td><td>4.28% (0.33%)</td><td>4.91% (0.44%)</td><td>6.10% (0.66%)</td><td>7.24% (1.03%)</td><td>7.08% (1.01%)</td><td>7.06% (1.00%)</td></tr><tr><td>bimodal</td><td>4.31% (0.32%)</td><td>4.27% (0.32%)</td><td>4.29% (0.33%)</td><td>4.32% (0.33%)</td><td>4.29% (0.33%)</td><td>4.91% (0.44%)</td><td>6.29% (0.79%)</td><td>7.57% (1.26%)</td><td>6.99% (1.00%)</td><td>6.92% (0.97%)</td></tr><tr><td>nino</td><td>5.01% (0.38%)</td><td>5.18% (0.38%)</td><td>5.23% (0.37%)</td><td>5.18% (0.38%)</td><td>5.21% (0.38%)</td><td>4.91% (0.48%)</td><td>7.28% (1.16%)</td><td>9.60% (1.75%)</td><td>6.77% (0.98%)</td><td>6.86% (1.09%)</td></tr><tr><td>protein</td><td>4.98% (0.38%)</td><td>5.13% (0.39%)</td><td>5.17% (0.39%)</td><td>5.19% (0.40%)</td><td>5.21% (0.43%)</td><td>4.92% (0.47%)</td><td>15.38% (3.01%)</td><td>10.74% (2.28%)</td><td>6.81% (0.98%)</td><td>6.73% (1.08%)</td></tr><tr><td>spruce</td><td>4.26% (0.33%)</td><td>4.29% (0.32%)</td><td>4.30% (0.32%)</td><td>4.29% (0.33%)</td><td>4.29% (0.34%)</td><td>4.85% (0.45%)</td><td>13.42% (3.15%)</td><td>13.64% (3.18%)</td><td>6.76% (0.99%)</td><td>6.89% (1.08%)</td></tr><tr><td>lodgepole</td><td>4.27% (0.32%)</td><td>4.27% (0.34%)</td><td>4.29% (0.35%)</td><td>4.30% (0.36%)</td><td>4.31% (0.34%)</td><td>4.93% (0.52%)</td><td>12.57% (3.45%)</td><td>12.73% (3.46%)</td><td>6.89% (1.00%)</td><td>6.74% (1.06%)</td></tr><tr><td>credit</td><td>4.34% (0.39%)</td><td>4.46% (0.46%)</td><td>4.39% (0.43%)</td><td>4.38% (0.42%)</td><td>4.47% (0.44%)</td><td>4.91% (0.61%)</td><td>11.88% (2.16%)</td><td>23.23% (3.66%)</td><td>6.74% (1.04%)</td><td>6.75% (1.02%)</td></tr><tr><td>insects (1→2)</td><td>4.69% (0.47%)</td><td>4.84% (0.57%)</td><td>4.84% (0.58%)</td><td>4.84% (0.56%)</td><td>4.97% (0.59%)</td><td>4.91% (0.45%)</td><td>6.73% (1.63%)</td><td>8.05% (1.95%)</td><td>6.86% (1.04%)</td><td>6.77% (1.10%)</td></tr><tr><td>insects (2→3)</td><td>4.73% (0.50%)</td><td>4.87% (0.59%)</td><td>4.85% (0.56%)</td><td>4.86% (0.60%)</td><td>5.04% (0.61%)</td><td>4.90% (0.45%)</td><td>6.67% (1.51%)</td><td>8.02% (1.77%)</td><td>6.83% (1.03%)</td><td>6.77% (1.04%)</td></tr><tr><td>insects (3→4)</td><td>4.72% (0.49%)</td><td>4.84% (0.56%)</td><td>4.85% (0.58%)</td><td>4.84% (0.58%)</td><td>5.02% (0.60%)</td><td>4.93% (0.48%)</td><td>7.29% (1.75%)</td><td>8.71% (2.03%)</td><td>6.80% (1.07%)</td><td>6.75% (1.03%)</td></tr><tr><td>insects (4→5)</td><td>4.69% (0.50%)</td><td>4.84% (0.58%)</td><td>4.82% (0.57%)</td><td>4.83% (0.60%)</td><td>4.99% (0.64%)</td><td>4.90% (0.44%)</td><td>6.56% (1.55%)</td><td>7.89% (1.87%)</td><td>6.83% (1.03%)</td><td>6.71% (1.03%)</td></tr><tr><td>insects (5→6)</td><td>4.77% (0.53%)</td><td>4.90% (0.56%)</td><td>4.90% (0.56%)</td><td>4.89% (0.58%)</td><td>5.07% (0.60%)</td><td>4.86% (0.43%)</td><td>7.18% (1.72%)</td><td>8.09% (1.89%)</td><td>6.77% (1.04%)</td><td>6.76% (1.00%)</td></tr><tr><td>sensorless</td><td>4.29% (0.35%)</td><td>4.43% (0.39%)</td><td>4.30% (0.34%)</td><td>4.35% (0.36%)</td><td>5.32% (0.65%)</td><td>4.94% (0.49%)</td><td>4.93% (1.19%)</td><td>4.29% (0.71%)</td><td>6.53% (1.06%)</td><td>6.67% (1.07%)</td></tr><tr><td>particle</td><td>4.28% (0.32%)</td><td>4.32% (0.36%)</td><td>4.30% (0.35%)</td><td>4.33% (0.35%)</td><td>4.71% (0.46%)</td><td>4.86% (0.50%)</td><td>6.92% (1.52%)</td><td>8.80% (1.96%)</td><td>6.70% (1.12%)</td><td>6.78% (1.12%)</td></tr><tr><td>unimodal</td><td>0.883 (0.101)</td><td>0.936 (0.059)</td><td>0.881 (0.115)</td><td>0.957 (0.031)</td><td>0.957 (0.031)</td><td>0.779 (0.157)</td><td>0.975 (0.016)</td><td>0.972 (0.047)</td><td>0.676 (0.148)</td><td>0.712 (0.174)</td></tr><tr><td>bimodal</td><td>0.796 (0.109)</td><td>0.825 (0.102)</td><td>0.821 (0.112)</td><td>0.868 (0.075)</td><td>0.885 (0.062)</td><td>0.709 (0.130)</td><td>0.859 (0.132)</td><td>0.845 (0.154)</td><td>0.636 (0.106)</td><td>0.652 (0.122)</td></tr><tr><td>nino</td><td>0.736 (0.143)</td><td>0.804 (0.170)</td><td>0.555 (0.042)</td><td>0.809 (0.173)</td><td>0.830 (0.163)</td><td>0.511 (0.012)</td><td>0.739 (0.176)</td><td>0.771 (0.191)</td><td>0.630 (0.111)</td><td>0.545 (0.048)</td></tr><tr><td>protein</td><td>0.848 (0.104)</td><td>0.980 (0.055)</td><td>0.582 (0.048)</td><td>0.985 (0.050)</td><td>0.991 (0.035)</td><td>0.508 (0.009)</td><td>0.906 (0.118)</td><td>0.945 (0.098)</td><td>0.638 (0.117)</td><td>0.599 (0.081)</td></tr><tr><td>spruce</td><td>1.000 (0.003)</td><td>1.000 (0.000)</td><td>0.590 (0.060)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.504 (0.005)</td><td>1.000 (0.002)</td><td>1.000 (0.002)</td><td>1.000 (0.001)</td><td>1.000 (0.001)</td></tr><tr><td>lodgepole</td><td>1.000 (0.001)</td><td>1.000 (0.001)</td><td>0.639 (0.085)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.506 (0.006)</td><td>1.000 (0.002)</td><td>1.000 (0.002)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td></tr><tr><td>credit</td><td>0.611 (0.043)</td><td>0.813 (0.144)</td><td>0.550 (0.021)</td><td>0.685 (0.137)</td><td>1.000 (0.000)</td><td>0.504 (0.005)</td><td>0.565 (0.060)</td><td>0.624 (0.108)</td><td>0.603 (0.051)</td><td>0.739 (0.116)</td></tr><tr><td>insects (1→2)</td><td>0.976 (0.022)</td><td>0.887 (0.054)</td><td>0.902 (0.041)</td><td>0.967 (0.025)</td><td>0.959 (0.037)</td><td>0.698 (0.057)</td><td>0.733 (0.033)</td><td>0.786 (0.031)</td><td>1.000 (0.000)</td><td>0.999 (0.002)</td></tr><tr><td>insects (2→3)</td><td>0.968 (0.031)</td><td>0.981 (0.018)</td><td>0.994 (0.005)</td><td>0.999 (0.001)</td><td>1.000 (0.001)</td><td>0.895 (0.052)</td><td>1.000 (0.000)</td><td>0.999 (0.000)</td><td>0.987 (0.008)</td><td>0.996 (0.009)</td></tr><tr><td>insects (3→4)</td><td>0.915 (0.045)</td><td>0.804 (0.068)</td><td>0.821 (0.046)</td><td>0.909 (0.036)</td><td>0.940 (0.051)</td><td>0.688 (0.066)</td><td>0.691 (0.021)</td><td>0.687 (0.023)</td><td>0.995 (0.003)</td><td>0.987 (0.007)</td></tr><tr><td>insects (4→5)</td><td>0.989 (0.015)</td><td>0.991 (0.015)</td><td>0.998 (0.003)</td><td>1.000 (0.001)</td><td>1.000 (0.000)</td><td>0.878 (0.071)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.999 (0.001)</td><td>0.994 (0.010)</td></tr><tr><td>insects (5→6)</td><td>0.974 (0.017)</td><td>0.890 (0.044)</td><td>0.922 (0.023)</td><td>0.961 (0.019)</td><td>0.982 (0.011)</td><td>0.860 (0.051)</td><td>0.932 (0.007)</td><td>0.933 (0.008)</td><td>0.997 (0.001)</td><td>0.996 (0.002)</td></tr><tr><td>sensorless</td><td>0.832 (0.112)</td><td>0.999 (0.008)</td><td>0.523 (0.013)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.501 (0.003)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.715 (0.139)</td><td>0.582 (0.083)</td></tr><tr><td>particle</td><td>0.860 (0.129)</td><td>0.876 (0.107)</td><td>0.530 (0.015)</td><td>0.922 (0.101)</td><td>0.941 (0.089)</td><td>0.503 (0.004)</td><td>0.786 (0.143)</td><td>0.861 (0.127)</td><td>0.706 (0.143)</td><td>0.526 (0.035)</td></tr><tr><td>Average Ranking</td><td>5.32</td><td>4.96</td><td>7.28</td><td>3.78</td><td>2.96</td><td>9.54</td><td>5.26</td><td>4.97</td><td>5.33</td><td>5.60</td></tr><tr><td>Nemenyi p-value</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>-</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td></tr></table>

Table 5: FPR (top) and AUC (bottom) achieved by the considered methods in the high-ratio setting, namely when histogram-based methods define K = 16 bins and the monitored batches contain ν = 128 points. In parenthesis, the width of the 95%-confidence interval of the results.

<table><tr><td></td><td>QT</td><td>QT (PCA)</td><td>KQT (Euclidean)</td><td>KQT (Mahalanobis)</td><td>KQT (Weighted Maha.)</td><td>ElkM</td><td>SPLL(C=3)</td><td>SPLL(C=3) (PCA)</td><td>DT</td><td>DT (PCA)</td></tr><tr><td>unimodal</td><td>4.83% (0.48%)</td><td>4.81% (0.46%)</td><td>4.86% (0.47%)</td><td>4.82% (0.45%)</td><td>4.83% (0.48%)</td><td>4.82% (0.53%)</td><td>5.46% (0.75%)</td><td>5.92% (1.04%)</td><td>7.84% (1.16%)</td><td>7.75% (1.17%)</td></tr><tr><td>bimodal</td><td>4.80% (0.45%)</td><td>4.81% (0.46%)</td><td>4.80% (0.46%)</td><td>4.81% (0.44%)</td><td>4.80% (0.45%)</td><td>4.82% (0.51%)</td><td>5.53% (0.75%)</td><td>6.02% (1.06%)</td><td>7.65% (1.20%)</td><td>7.62% (1.09%)</td></tr><tr><td>nino</td><td>5.04% (0.49%)</td><td>4.99% (0.50%)</td><td>5.00% (0.53%)</td><td>5.02% (0.53%)</td><td>5.01% (0.54%)</td><td>4.83% (0.55%)</td><td>6.14% (1.21%)</td><td>7.69% (2.05%)</td><td>7.55% (1.20%)</td><td>7.57% (1.16%)</td></tr><tr><td>protein</td><td>4.97% (0.50%)</td><td>4.98% (0.56%)</td><td>4.97% (0.52%)</td><td>4.98% (0.54%)</td><td>5.03% (0.55%)</td><td>4.88% (0.61%)</td><td>13.15% (3.54%)</td><td>8.42% (2.33%)</td><td>7.65% (1.25%)</td><td>7.64% (1.25%)</td></tr><tr><td>spruce</td><td>4.81% (0.50%)</td><td>4.83% (0.48%)</td><td>4.82% (0.47%)</td><td>4.84% (0.49%)</td><td>4.90% (0.47%)</td><td>4.86% (0.59%)</td><td>11.43% (3.93%)</td><td>11.56% (3.97%)</td><td>7.56% (1.21%)</td><td>7.57% (1.16%)</td></tr><tr><td>lodgepole</td><td>4.83% (0.47%)</td><td>4.82% (0.50%)</td><td>4.85% (0.49%)</td><td>4.80% (0.47%)</td><td>4.90% (0.50%)</td><td>4.92% (0.57%)</td><td>10.78% (4.64%)</td><td>10.89% (4.68%)</td><td>7.60% (1.14%)</td><td>7.58% (1.12%)</td></tr><tr><td>credit</td><td>4.83% (0.47%)</td><td>4.96% (0.54%)</td><td>4.89% (0.48%)</td><td>4.85% (0.46%)</td><td>5.06% (0.56%)</td><td>4.96% (0.68%)</td><td>8.67% (2.26%)</td><td>16.06% (3.63%)</td><td>7.63% (1.15%)</td><td>7.59% (1.23%)</td></tr><tr><td>insects (1→2)</td><td>4.92% (0.50%)</td><td>4.93% (0.51%)</td><td>4.91% (0.50%)</td><td>4.93% (0.52%)</td><td>5.19% (0.64%)</td><td>4.93% (0.63%)</td><td>5.90% (2.04%)</td><td>6.48% (2.15%)</td><td>7.57% (1.16%)</td><td>7.60% (1.20%)</td></tr><tr><td>insects (2→3)</td><td>4.93% (0.53%)</td><td>4.91% (0.54%)</td><td>4.92% (0.52%)</td><td>4.96% (0.52%)</td><td>5.25% (0.62%)</td><td>4.96% (0.65%)</td><td>5.54% (1.85%)</td><td>6.16% (1.96%)</td><td>7.60% (1.19%)</td><td>7.59% (1.23%)</td></tr><tr><td>insects (3→4)</td><td>4.92% (0.48%)</td><td>4.89% (0.52%)</td><td>4.90% (0.52%)</td><td>4.88% (0.53%)</td><td>5.22% (0.64%)</td><td>4.89% (0.58%)</td><td>6.09% (1.99%)</td><td>6.69% (2.11%)</td><td>7.59% (1.19%)</td><td>7.54% (1.17%)</td></tr><tr><td>insects (4→5)</td><td>4.92% (0.50%)</td><td>4.95% (0.52%)</td><td>4.91% (0.51%)</td><td>4.92% (0.54%)</td><td>5.25% (0.65%)</td><td>4.91% (0.61%)</td><td>5.48% (1.76%)</td><td>6.01% (1.84%)</td><td>7.63% (1.24%)</td><td>7.56% (1.17%)</td></tr><tr><td>insects (5→6)</td><td>4.91% (0.54%)</td><td>4.90% (0.54%)</td><td>4.90% (0.56%)</td><td>4.92% (0.53%)</td><td>5.26% (0.72%)</td><td>4.90% (0.64%)</td><td>5.86% (2.05%)</td><td>6.19% (2.11%)</td><td>7.61% (1.22%)</td><td>7.63% (1.24%)</td></tr><tr><td>sensorless</td><td>4.84% (0.50%)</td><td>5.01% (0.55%)</td><td>4.82% (0.49%)</td><td>5.01% (0.56%)</td><td>7.42% (1.61%)</td><td>4.93% (0.61%)</td><td>4.33% (1.03%)</td><td>4.83% (0.76%)</td><td>7.55% (1.19%)</td><td>7.58% (1.22%)</td></tr><tr><td>particle</td><td>4.85% (0.50%)</td><td>4.87% (0.51%)</td><td>4.81% (0.46%)</td><td>4.94% (0.52%)</td><td>5.80% (1.02%)</td><td>4.84% (0.61%)</td><td>5.93% (2.01%)</td><td>6.07% (2.05%)</td><td>7.52% (1.10%)</td><td>7.60% (1.19%)</td></tr><tr><td>unimodal</td><td>0.957 (0.079)</td><td>0.976 (0.057)</td><td>0.946 (0.105)</td><td>0.993 (0.016)</td><td>0.994 (0.013)</td><td>0.874 (0.154)</td><td>0.996 (0.006)</td><td>0.989 (0.040)</td><td>0.786 (0.167)</td><td>0.806 (0.190)</td></tr><tr><td>bimodal</td><td>0.900 (0.110)</td><td>0.930 (0.090)</td><td>0.904 (0.118)</td><td>0.954 (0.060)</td><td>0.968 (0.042)</td><td>0.821 (0.158)</td><td>0.915 (0.126)</td><td>0.895 (0.164)</td><td>0.751 (0.155)</td><td>0.767 (0.160)</td></tr><tr><td>nino</td><td>0.845 (0.143)</td><td>0.905 (0.135)</td><td>0.607 (0.072)</td><td>0.904 (0.138)</td><td>0.922 (0.122)</td><td>0.528 (0.029)</td><td>0.816 (0.172)</td><td>0.841 (0.183)</td><td>0.726 (0.152)</td><td>0.582 (0.081)</td></tr><tr><td>protein</td><td>0.899 (0.104)</td><td>0.985 (0.051)</td><td>0.617 (0.074)</td><td>0.993 (0.035)</td><td>0.995 (0.027)</td><td>0.514 (0.015)</td><td>0.918 (0.118)</td><td>0.954 (0.093)</td><td>0.704 (0.148)</td><td>0.595 (0.085)</td></tr><tr><td>spruce</td><td>0.999 (0.014)</td><td>1.000 (0.000)</td><td>0.601 (0.066)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.507 (0.007)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>1.000 (0.002)</td><td>1.000 (0.002)</td></tr><tr><td>lodgepole</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.654 (0.099)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.511 (0.016)</td><td>1.000 (0.002)</td><td>1.000 (0.002)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td></tr><tr><td>credit</td><td>0.698 (0.079)</td><td>0.867 (0.127)</td><td>0.602 (0.053)</td><td>0.780 (0.146)</td><td>1.000 (0.000)</td><td>0.508 (0.011)</td><td>0.597 (0.085)</td><td>0.660 (0.132)</td><td>0.695 (0.091)</td><td>0.820 (0.131)</td></tr><tr><td>insects (1→2)</td><td>0.998 (0.005)</td><td>0.962 (0.048)</td><td>0.962 (0.035)</td><td>0.972 (0.039)</td><td>0.993 (0.019)</td><td>0.836 (0.071)</td><td>0.810 (0.035)</td><td>0.866 (0.029)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td></tr><tr><td>insects (2→3)</td><td>0.993 (0.017)</td><td>0.995 (0.012)</td><td>1.000 (0.001)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.962 (0.014)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.999 (0.002)</td><td>1.000 (0.001)</td></tr><tr><td>insects (3→4)</td><td>0.983 (0.029)</td><td>0.897 (0.078)</td><td>0.904 (0.054)</td><td>0.942 (0.049)</td><td>0.990 (0.024)</td><td>0.835 (0.084)</td><td>0.753 (0.025)</td><td>0.745 (0.028)</td><td>1.000 (0.000)</td><td>1.000 (0.001)</td></tr><tr><td>insects (4→5)</td><td>0.998 (0.008)</td><td>0.997 (0.008)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.950 (0.021)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.999 (0.004)</td></tr><tr><td>insects (5→6)</td><td>0.999 (0.003)</td><td>0.971 (0.033)</td><td>0.985 (0.016)</td><td>0.992 (0.008)</td><td>1.000 (0.000)</td><td>0.963 (0.017)</td><td>0.979 (0.004)</td><td>0.979 (0.005)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td></tr><tr><td>sensorless</td><td>0.862 (0.120)</td><td>1.000 (0.004)</td><td>0.542 (0.027)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.502 (0.003)</td><td>1.000 (0.000)</td><td>1.000 (0.000)</td><td>0.738 (0.179)</td><td>0.595 (0.104)</td></tr><tr><td>particle</td><td>0.886 (0.116)</td><td>0.931 (0.090)</td><td>0.555 (0.030)</td><td>0.976 (0.051)</td><td>0.985 (0.039)</td><td>0.506 (0.006)</td><td>0.838 (0.135)</td><td>0.901 (0.112)</td><td>0.798 (0.140)</td><td>0.542 (0.054)</td></tr><tr><td>Average Ranking</td><td>5.24</td><td>4.93</td><td>7.08</td><td>3.82</td><td>2.98</td><td>9.37</td><td>5.57</td><td>5.34</td><td>5.11</td><td>5.56</td></tr><tr><td>Nemenyi p-value</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>-</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td><td>&lt; 10-16</td></tr></table>

## References

[Alippi et al., 2017] Alippi, C., Boracchi, G., and Carrera, D. (2017). Ccm: Controlling the change magnitude in high dimensional data. In Angelov, P., Manolopoulos, Y., Iliadis, L., Roy, A., and Vellasco, M., editors, Advances in Big Data, pages 216–225, Cham. Springer International Publishing.

[Balakrishnan and Rao, 1998] Balakrishnan, N. and Rao, C. R. (1998). Handbook of statistics. v. 16: Order statistics: theory and methods.

[Boracchi et al., 2018] Boracchi, G., Carrera, D., Cervellera, C., and Maccio, D. (2018). Quanttree: Histograms for change detection in multivariate data streams. In International Conference on Machine Learning, pages 639–648. PMLR.

[Dal Pozzolo et al., 2017] Dal Pozzolo, A., Boracchi, G., Caelen, O., Alippi, C., and Bontempi, G. (2017). Credit card fraud detection: a realistic modeling and a novel learning strategy. IEEE transactions on neural networks and learning systems, 29(8):3784–3797.

[Dua and Graf, 2017] Dua, D. and Graf, C. (2017). UCI machine learning repository.

[Lehmann et al., 2005] Lehmann, E. L., Romano, J. P., and Casella, G. (2005). Testing statistical hypotheses, volume 3. Springer.

[Papoulis and Pillai, 2002] Papoulis, A. and Pillai, S. U. (2002). Probability, random variables, and stochastic processes. Tata McGraw-Hill Education.

[Shapiro and Wilk, 1965] Shapiro, S. S. and Wilk, M. B. (1965). An analysis of variance test for normality (complete samples). Biometrika, 52(3/4):591–611.

[Souza et al., 2020] Souza, V. M., dos Reis, D. M., Maletzke, A. G., and Batista, G. E. (2020). Challenges in benchmarking stream learning algorithms with real-world data. Data Mining and Knowledge Discovery, 34(6):1805–1858.

[Tipping, 1999] Tipping, M. E. (1999). Deriving cluster analytic distance functions from gaussian mixture models.