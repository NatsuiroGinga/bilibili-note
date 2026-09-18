---
title: "2018-Boracchi-QuantTree-Change-Detection"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2018-Boracchi-QuantTree-Change-Detection.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# QuantTree: Histograms for Change Detection in Multivariate Data Streams

Giacomo Boracchi <sup>1</sup> Diego Carrera <sup>1</sup> Cristiano Cervellera <sup>2</sup> Danilo Maccio\` <sup>2</sup>

## Abstract

We address the problem of detecting distribution changes in multivariate data streams by means of histograms. Histograms are very general and flexible models, which have been relatively ignored in the change-detection literature as they often require a number of bins that grows unfeasibly with the data dimension. We present QuantTree, a recursive binary splitting scheme that adaptively defines the histogram bins to ease the detection of any distribution change. Our design scheme implies that i) we can easily control the overall number of bins and ii) the bin probabilities do not depend on the distribution of stationary data. This latter is a very relevant aspect in change detection, since thresholds of tests statistics based on these histograms (e.g., the Pearson statistic or the total variation) can be numerically computed from univariate and synthetically generated data, yet guaranteeing a controlled false positive rate. Our experiments show that the proposed histograms are very effective in detecting changes in high dimensional data streams, and that the resulting thresholds can effectively control the false positive rate, even when the number of training samples is relatively small.

## 1. Introduction

Change detection, namely the problem of analyzing a data stream to detect changes in the data-generating distribution, is very relevant in machine-learning and is typically addressed in an unsupervised manner. This approach is generally dictated by many practical aspects, which include the unpredictability of the change and the fact that the training set often contains only stationary data. As a matter of fact, most change-detection tests in the literature (Basseville & Nikiforov, 1993; Lung-Yut-Fong et al., 2011; Ross et al., 2011; Kuncheva, 2013) consist of three major ingredients: i) a model describing the distribution of stationary data, φ<sub>0</sub>, that is typically learned from a training set, ii) a test statistic T used to assess the conformance of test data with the learned model, and iii) a decision rule that monitors T to detect changes in φ . Needless to say, all these have to be wisely designed and combined to yield a sound test that can provide prompt detections as well as a controlled False Positive Rate (FPR), which is one of the primary concerns in change detection. Unfortunately, when it comes to monitoring multivariate data, it is difficult to find good density models and test statistics that do not depend on φ : this represents a severe limitation for real-world monitoring problems, where the stream distribution is unknown. Our work presents an efficient change-detection test for multivariate data that overcomes this limitation.

The first change-detection tests were developed to monitor univariate data streams in the statistical process control literature (Basseville & Nikiforov, 1993). In classification problems, changes in the data stream are known as concept drift (Gama et al., 2014) and are detected by monitoring the sequence of classification errors on supervised data (Harel et al., 2014; Alippi et al., 2013; Bifet & Gavalda, 2007). Many change-detection tests are parametric, i.e., they assume that φ<sub>0</sub> belongs to a known family, e.g., (Page, 1954), or are based on ad-hoc statistics that detect specific changes, e.g., the Hotelling statistic (Lehmann & Romano, 2006). Most nonparametric statistics are instead based on ranking, e.g., the Kolmogorov-Smirnov (Ross & Adams, 2012) and Lepage (Ross et al., 2011) statistics, and can be applied exclusively to univariate data.

There exist a few multivariate tests able to detect any distribution change (Lung-Yut-Fong et al., 2011; Justel et al., 1997). Two popular approaches consists either in reducing the data dimension by PCA (Kuncheva, 2013; Qahtan et al., 2015) or computing the likelihood with respect to a model fitted on a training set, e.g., a Gaussian mixture (Kuncheva, 2013; Alippi et al., 2016), a Gaussian process (Saatc¸i et al., 2010) or a kernel density estimator (Krempl, 2011). In the latter case the change-detection problem boils down to monitoring a univariate stream. Unfortunately, in these cases, T often depends on φ , and detection rules become heuristic in nature (Kuncheva, 2013; Ditzler & Polikar, 2011) preventing a proper control over the FPR. Histograms, which are perhaps the most natural candidates for describing densities, enable a different form of monitoring that is based on a comparison among distributions (Ditzler & Polikar, 2011; Boracchi et al., 2017). However, they are often implemented over regular grids and require a number of bins that grows exponentially with the data dimension. Only a few change-detection solutions (Dasu et al., 2006; Boracchi et al., 2017) adopt alternative partitioning schemes that scale well in high dimensions. In particular, kqd-trees (Dasu et al., 2006) were introduced as a variant of kd-trees (Bentley, 1975) to guarantee that all the leaves contain a minimum number of training samples and have a minimum size. In (Boracchi et al., 2017) it is shown that histograms built on uniform-density partitions rather than regular grids provide superior detection performance.

Our main contribution is QuantTree, a recursive binary splitting scheme that defines histograms for changedetection purposes. The most prominent advantage of using QuantTree is that the distribution of any statistic defined over the resulting histograms does not depend on φ<sub>0</sub>. This implies that decision rules to be used in multivariate change-detection problems do not depend on the data, and can be numerically computed from synthetically generated univariate sequences. Moreover, histograms defined by QuantTree can have a pre-assigned number of bins and can be represented as a tree, thus enabling a very efficient computation of test statistics.

QuantTree (Section 3) iteratively divides the input space by means of binary splits on a single covariate, where the cutting points are defined by the quantiles of the marginal distributions. This splitting strategy is similar to the one adopted by kd-trees (Bentley, 1975), where the split is performed w.r.t. the median value of the marginal. Such a simple construction scheme can be handled analytically, as it is possible to prove (Section 4) that the distribution of each bin probability does not depend on $\phi _ { 0 } .$ . Our experiments (Section 5) show that QuantTree enables good detection performance in high dimensional streams. Moreover, when testing few samples, QuantTree guarantees a better FPR control than the Pearson goodness-of-fit test and tests based on empirical thresholds computed through bootstrap. We also show that histograms constructed with a few bins gathering the same density under $\phi _ { 0 }$ achieve higher power than monitoring schemes based on different histograms.

## 2. Problem Formulation

Before the change, namely in stationary conditions, data in the monitored stream $\mathbf { x } \in \mathbb { R } ^ { d }$ are independent and identically distributed (i.i.d.) realizations of a continuous random vector $\mathbf { X } _ { 0 }$ having an unknown probability density function (pdf) $\phi _ { 0 }$ , whose support is $\mathcal { X } \subseteq \mathbb { R } ^ { d } .$ . We assume that a training set $T R = \{ \mathbf { x } _ { i } \in \mathcal { X } , i = 1 , \dots , N \}$ } containing N stationary data $( { \mathrm { i . e . , x } } _ { i } \sim \phi _ { 0 } )$ is provided.

Histograms: we define a histogram as:

$$
h = \{(S _ {k}, \widehat {\pi} _ {k}) \} _ {k = 1, \dots , K},\tag{1}
$$

where the K subsets $S _ { k } \subseteq { \mathcal { X } }$ form a partition of $\mathbb { R } ^ { d }$ , i.e., $\cup _ { k = 1 } ^ { K } S _ { k } = \mathbb { R } ^ { d }$ and $S _ { j } \cap S _ { i } = \emptyset$ , for $j \neq i ,$ and each $\widehat { \pi } _ { k } \in [ 0 , 1 ]$ corresponds to the probability for data generated from φ to fall inside $S _ { k }$ . Both the subsets $\{ S _ { k } \} _ { k }$ and probabilities $\{ \widehat { \pi } _ { k } \} _ { k }$ can be adaptively defined from training data $T R _ { : }$ , and in particular $\widehat { \pi } _ { k }$ is typically estimated as $\widehat { \pi } _ { k } = L _ { k } / N$ , i.e. the number of training samples $L _ { K }$ belonging to $S _ { k }$ over the number of points in $T R .$

Batch-wise monitoring: for the sake of simplicity, we analyze the incoming data in batches $W = \{ \mathbf { x } _ { 1 } , \ldots , \mathbf { x } _ { \nu } \}$ of ν samples. We detect changes by an hypothesis test (HT) which assesses whether data in W are consistent with a reference histogram h learned from T R. In particular, this hypothesis test can be stated as follows:

$$
H _ {0}: W \sim \phi_ {0} \qquad v s \qquad H _ {1}: W \sim \phi_ {1} \neq \phi_ {0}\tag{2}
$$

where $\phi _ { 1 }$ represents the unknown post-change distribution. We focus on HTs that are based on a test statistic $\mathcal { T } _ { h }$ defined over the histogram $h ,$ like for instance the Pearson statistic (Lehmann & Romano, 2006). Thus, $\mathcal { T } _ { h }$ uniquely depends on $\{ y _ { k } \} _ { k = 1 , \ldots , K } .$ , where $y _ { k }$ denotes the number of samples in W falling in $S _ { k }$ . We detect a change in the incoming W when

$$
\mathcal {T} _ {h} (W) = \mathcal {T} _ {h} (y _ {1}, \dots , y _ {K}) > \tau ,\tag{3}
$$

where $\tau \in \mathbb { R }$ is a threshold that controls the FPR, namely the proportion of type I errors (Lehmann & Romano, 2006).

Goal: our goal is two-fold, i) learn a histogram h from TR to be used for change-detection purposes and ii) for each given test statistic $\bar { \mathcal { T } _ { h } }$ and reference FPR value $\alpha ,$ define a threshold τ such that

$$
P _ {\phi_ {0}} \left(\mathcal {T} _ {h} (W) > \tau\right) \leq \alpha ,\tag{4}
$$

where $P _ { \phi _ { 0 } }$ denotes the probability under the null hypothesis that W contains samples generated from $\phi _ { 0 }$

There are two important comments. First, while (3) might seem an oversimplified monitoring scheme, this is enough to demonstrate that when histograms are built through QuantTree, the monitoring can be performed independently of $\phi _ { 0 }$ . As a consequence, test statistics $\mathcal { T } _ { h }$ can be potentially employed in sequential monitoring schemes like (Ross & Adams, 2012). Second, we focus on generalpurpose tests, which are able to detect any distribution change $\phi _ { 0 }  \phi _ { 1 }$ as well as on histograms that can model densities in high dimensions, i.e., d  1.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 QuantTree

Input: Training set TR containing N stationary points in X; number of bins K; target probabilities  $\{\pi_{k}\}_{k}$ .

Output: The histogram  $h = \{(S_{k}, \widehat{\pi}_{k})\}_{k}$ .

1: Set  $N_{0} = N, L_{0} = 0$ .

2: for  $k = 1, \ldots, K$  do

3: Set  $N_{k} = N_{k-1} - L_{k-1}, X_{k} = X \setminus \bigcup_{j &lt; k} S_{j}$ , and  $L_{k} = \text{round}(\pi^{k} N)$ .

4: Choose a random component  $i \in \{1, \ldots, d\}$ .

5: Define  $z_{n} = [\mathbf{x}_{n}]_{i}$  for each  $x_{n} \in X_{k}$ .

6: Sort  $\{z_{n}\}: z_{(1)} \leq z_{(2)} \leq \ldots z_{(N_{k})}$ .

7: Draw  $\gamma \in \{0, 1\}$  from a Bernoulli(0.5).

8: if  $\gamma = 0$  then

9: Define  $S_{k} = \{x \in X_{k}, [x]_{i} \leq z_{(L_{k})}\}$ .

10: else

11: Define  $S_{k} = \{x \in X_{k}, [x]_{i} \geq z_{(N_{k} - L_{k} + 1)}\}$ .

12: end if

13: Set  $\widehat{\pi}_{k} = L_{k}/N$ .

14: end for
</div>

## 3. The QuantTree Algorithm

Here we describe QuantTree<sup>1</sup>, an algorithm to define histograms h through a recursive binary splitting of the input space $\mathcal { X } .$ This algorithm takes as input a training set $T R$ containing N stationary points, the number of bins K in the histogram, and the target probabilities on each bin $\{ \pi _ { k } \} _ { k = 1 , \dots , K }$ , and returns a histogram $\begin{array} { r l } { h } & { { } = } \end{array}$ $\{ ( S _ { k } , \widehat { \pi } _ { k } ) \} _ { k = 1 , \ldots , K } .$ , where each $\widehat { \pi } _ { k }$ represents an estimate of the probability for a sample drawn from φ<sub>0</sub> to fall in $S _ { k }$

Algorithm 1 presents in detail the iterative formulation of QuantTree, which constructs a new bin of h at each step k. We denote by $\mathcal { X } _ { k } \subseteq \mathcal { X }$ the subset of the input space that still has to be partitioned $( \mathrm { i . e . , ~ } \mathcal { X } _ { k } = \mathcal { X } \setminus \bar { \bigcup } _ { i < k } \bar { S } _ { k } )$ and by $N _ { k }$ the number of points of TR belonging to $\mathcal { X } _ { k }$ . We compute (line 3) the number of training points that has to fall inside $S _ { k }$ as $L _ { k } = \mathrm { r o u n d } ( \pi _ { k } N )$ . The subset $S _ { k }$ is then defined by splitting $\mathcal { X } _ { k }$ along a component $i \in \{ 1 , \ldots , d \}$ that is randomly chosen with uniform probability (line 4). The splitting point is defined by sorting $z _ { n } = [ \mathbf { x } _ { n } ] _ { i } , \mathrm { i . e . }$ , the values of the i-th component for each $\mathbf { x } _ { n } \in \mathcal { X } _ { k }$ (lines 5). We thus obtain $z _ { ( 1 ) } \le z _ { ( 2 ) } \le \cdot \cdot \cdot \le z _ { ( N _ { k } ) }$ (line 6) and we define $S _ { k }$ by splitting $\mathcal { X } _ { k }$ w.r.t. $z _ { ( L _ { k } ) } \mathrm { o r } z _ { ( N _ { k } - L _ { k } + 1 ) }$ (lines 7-11). In both cases $S _ { k }$ contains $L _ { k }$ points among the N in $\mathcal { X } .$ , thus the estimated probability of $S _ { k }$ is $\widehat { \pi } _ { k } = L _ { k } / N$ (line 13). This procedure is iterated until K subsets are extracted.

QuantTree divides X in a given number of subsets, where each $S _ { k }$ has an estimated probability $\widehat { \pi } _ { k } \simeq \pi _ { k }$ , and the equality holds when $\pi _ { k } N$ is integer. Since the probabilities $\pi _ { k }$ are set a priori, in what follows we use $\pi _ { k }$ in place of $\widehat { \pi } _ { k }$ Indexes i and parameter γ are randomly chosen to add variability to the histogram construction. Figure 1(a) shows a tree obtained from a bivariate Gaussian training set, defined by K = 4 bins, each having probability $\pi _ { k } = N / 4$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 Numerical procedure to compute thresholds
Input: Test statistic  $T_{h}$ ; arbitrarily chosen  $\psi_{0}$ ; the number B of datasets and batches to compute the threshold; the number of points  $\nu$  in each batch; N, K, and  $\widehat{\pi}_{k}$  as in Algorithm 1; the desired FPR  $\alpha$ .
Output: The value  $\tau$  of the threshold
1: for  $b = 1, \ldots, B$  do
2: Draw from  $\psi_{0}$  a training set  $TR_{b}$  of N samples.
3: Use QuantTree to compute the histogram  $h_{b}$  with K bins and target probabilities  $\{\pi_{k}\}_{k}$  over TR.
4: Draw a batch  $W_{b}$  containing  $\nu$  points from  $\phi_{0}$ .
5: Compute the value  $t_{b} = \mathcal{T}_{h}(W)$ .
6: end for
7: Compute the threshold  $\tau$  as in (5).
</div>

## 3.1. Computation of Distribution-Free Test Statistics

A key feature of a histogram computed by QuantTree is that any statistic $\mathcal { T } _ { h }$ built over it has a distribution that is independent from $\phi _ { 0 }$ . This result follows from Theorem 1, that is proved in Section 4.

Theorem 1. Let $\mathcal { T } _ { h } ( \cdot )$ be defined as in (3) over the histogram h computed by QuantTree. When $W \sim \phi _ { 0 } ,$ , the distribution of $\mathcal { T } _ { h } ( W )$ depends only on ν, N and $\{ \pi _ { k } \} _ { k }$

Theorem 1 implies that we can numerically compute the thresholds for any statistic $\mathcal { T } _ { h }$ defined on histograms, provided $\nu , N$ and $\left\{ \pi _ { k } \right\}$ , thus disregarding φ<sub>0</sub> and the data dimension d. To this end, we synthetically generate data from a conveniently chosen distribution $\psi _ { 0 } ,$ , and we follow the procedure outlined in Algorithm 2 to estimate the threshold τ for HT in (2) yielding a desired FPR $\alpha$ . At first we generate B training sets $\{ T R _ { b } \} _ { b = 1 , \dots , B } ,$ , sampling N points from ψ<sub>0</sub> and, for each training set, we build a histogram $h _ { b }$ using QuantTree (lines 2-3). Then, for each $h _ { b }$ we generate a batch $W _ { b }$ of $\nu$ points drawn from $\psi _ { 0 }$ , and compute the value of the statistic $t _ { b } = \mathcal { T } _ { h } ( W _ { b } )$ (lines 4-5). Finally, we estimate τ (line 7) from the set $T _ { B } = \{ t _ { 1 } , \dots , t _ { B } \}$ as the $1 - \alpha$ quantile of the empirical distribution of $\mathcal { T } _ { h }$ over the generated batches, i.e.

$$
\tau = \min \Bigl \{t \in T _ {B}: \# \{v \in T _ {B}: v > t \} \leq \alpha B \Bigr \},\tag{5}
$$

where $\# A$ denotes the cardinality of a set A.

To take full advantage of the distribution-free nature of the procedure, we set $\psi _ { 0 }$ to a univariate uniform distribution

$U ( 0 , 1 )$ . This allows to obtain high accuracy on the estimation of the thresholds, since we can use very large values of B with limited computational cost.

## 3.2. Considered Statistics

We consider two meaningful examples of statistics $\mathcal { T } _ { h }$ that can be employed for batch-wise monitoring through histograms: the Pearson statistic and the total variation (Lehmann & Romano, 2006). The Pearson statistic is defined as

$$
\mathcal {T} _ {h} ^ {P} (W) = \sum_ {k = 1} ^ {K} \frac {(y _ {k} - \nu \pi_ {k}) ^ {2}}{\nu \pi_ {k}},\tag{6}
$$

while the total variation is defined as

$$
\mathcal {T} _ {h} ^ {T V} (W) = \frac {1}{2} \sum_ {k = 1} ^ {K} \left| y _ {k} - \nu \pi_ {k} \right|.\tag{7}
$$

It is well known that, when $\{ \pi _ { k } \} _ { k }$ are the true probabilities of the bins $\{ S _ { k } \} _ { k }$ , under the null hypothesis the statistic $\mathcal { T } _ { h } ^ { P } ( W )$ is asymptotically distributed as a $\chi _ { K - 1 } ^ { 2 }$ . However, when the $\pi _ { k }$ are estimated, the threshold obtained from the $\chi _ { K - 1 } ^ { 2 }$ distribution does not allow to properly control the FPR, and this effect is more evident when y<sub>k</sub> is small. In contrast, thresholds defined by Algorithm 2 hold also in case of limited sample size, since they are not based on an asymptotic result.

These two statistics will be used for our experiments in Section 5, using thresholds reported in Table 1 for different values of $N , K ,$ ν and choosing $\pi _ { k } = 1 / K , k = 1 , \dots , K$ These values have been computed applying the procedure described in Algorithm 2 with $B = 2 . 5 \cdot 1 0 ^ { 6 }$ . We note that both statistics $\mathcal { T } _ { h } ^ { P }$ and $\mathcal { T } _ { h } ^ { T V }$ assume only discrete values, therefore it is not always possible to set the threshold τ yielding the FPR exactly equal to α, but only to ensure that the FPR does not exceed α.

## 3.3. Computational Remarks

We remark that since the histogram h computed by QuantTree is exclusively defined on the marginal probabilities of single components, the dimensionality of the input data d does not impact the overall computational cost. In fact, the computational cost of building a QuantTree is dominated by sorting the covariates (Algorithm 1 line 6), which is performed K times on an progressively smaller number of samples at each iteration. Therefore, the overal complexity of constructing a QuantTree is O(KN log N). In case of univariate distribution $( \mathrm { i } . \mathrm { e } . , d = 1 )$ ), the complexity is reduced to O(N log N), since the partition $\{ S _ { k } \} _ { k }$ can be defined through a single sorting operation.

Since any histogram h computed by QuantTree can be represented as a tree structure, it is very efficient to identify the bin where any testing point belongs to. In fact, during monitoring, at most K IF-THEN operations (that reduces to log K when $d = 1 )$ have to be performed for each input sample x. Moreover, in contrast with histograms based on regular grids, the number of bins K is here a priori defined, and does not need to grow exponentially with d.

<table><tr><td rowspan="2">α</td><td colspan="2">Pearson</td><td colspan="2">Total Variation</td><td rowspan="2">N</td><td rowspan="2">ν</td></tr><tr><td>K=32</td><td>K=128</td><td>K=32</td><td>K=128</td></tr><tr><td rowspan="2">0.001</td><td>64</td><td>192</td><td>25</td><td>43</td><td>4096</td><td>64</td></tr><tr><td>62.75</td><td>187</td><td>52</td><td>85</td><td>16384</td><td>256</td></tr><tr><td rowspan="2">0.01</td><td>54</td><td>172</td><td>23</td><td>42</td><td>4096</td><td>64</td></tr><tr><td>53.25</td><td>171</td><td>47</td><td>81</td><td>16384</td><td>256</td></tr><tr><td rowspan="2">0.05</td><td>46</td><td>156</td><td>21</td><td>41</td><td>4096</td><td>64</td></tr><tr><td>45.75</td><td>157</td><td>44</td><td>78</td><td>16384</td><td>256</td></tr></table>

Table 1: Examples of thresholds τ that guarantee FPR below α in HT (2) using a uniform histogram h, i.e. by settings $\pi _ { k } = 1 / K ,$ $k = 1 , \ldots , K$ . The thresholds are computed by Algorithm 2 using $U ( 0 , 1 )$ as ψ<sub>0</sub> and different values of N, ν and K.

## 4. Theoretical Analysis

We prove Theorem 1 showing that the distribution of any test statistic $\mathcal { T } _ { h }$ defined over an histogram h computed by QuantTree does not depend on $\phi _ { 0 }$ . To this end, we first prove some preliminary propositions to characterize the distribution of the true probability of each bin $S _ { k }$ under φ<sub>0</sub>:

$$
p _ {k} = P _ {\phi_ {0}} (S _ {k}),\tag{8}
$$

which is also a random variable as it depends on the training data TR.

For the sake of simplicity, we assume that QuantTree always splits with respect to the left tail, $\mathrm { i } . \mathrm { e } . , \gamma = 0$ in line 8 of Algorithm 1 (proofs hold when $\gamma \sim$ Bernoulli(0.5)) and, to simplify the notation, we will omit the subscript $\phi _ { 0 }$ from $P _ { \phi _ { 0 } }$ , thus $P$ denotes the probability computed w.r.t. $\phi _ { 0 }$ . The following proposition will be used to derive the distributions of $p _ { k }$

Proposition 1. Let $\mathbf { x } _ { 1 } , \ldots , \mathbf { x } _ { M }$ be i.i.d. realizations of a continuous random vector X defined over $\mathcal { D } \subseteq \mathbb { R } ^ { d } .$ . Let us define the i-th component of x as $z = [ \mathbf { x } ] _ { i }$ <sub>i</sub>, and denote with $z _ { ( 1 ) } \leq z _ { ( 2 ) } \leq \cdot \cdot \cdot \leq z _ { ( M ) }$ the M sorted components of $\mathbf { x } _ { 1 } , \ldots , \mathbf { x } _ { M } .$ For any $L \doteq \bigl \{ 1 , \ldots , M \bigr \}$ we define the set

$$
Q _ {i, L} := \{\mathbf {x} \in \mathcal {D}: [ \mathbf {x} ] _ {i} \leq z _ {(L)} \}.\tag{9}
$$

Then, for each $i \in \{ 1 , \ldots , d \}$ , the random variable $p =$ $P _ { \mathbf { X } } ( Q _ { i , L } )$ is distributed as a Beta $( L , M - L + 1 )$ .

Proof. The proof consists of showing that $p$ is an order statistic of the uniform distribution, which in turns follows a Beta distribution. For this purpose, we consider X defined over $\mathbb { R } ^ { d }$ and $P _ { \mathbf { X } } ( \mathbb { R } ^ { d } \backslash \mathcal { D } ) = 0$ , thus p can be expressed as

$$
\begin{array}{l} p = P _ {\mathbf {X}} (Q _ {i, L}) = P _ {\mathbf {X}} (\mathbf {x} \in \mathbb {R} ^ {d}: [ \mathbf {x} ] _ {i} \leq z _ {(L)}) = \\ \quad = P _ {Z} (z \in \mathbb {R}: z \leq z _ {(L)}), \end{array}\tag{10}
$$

![](images/0b634d0474a46b2040015c1ba0bea07df22836ccd656998cd9c76f236c0dcdbf.jpg)  
Figure 1: (a) A histogram $\{ S _ { k } \} _ { k = 1 , \dots , 4 }$ computed by QuantTree to yield uniform density on the bins. (b)-(d) Examples of values assumed by $\widetilde { L } _ { k }$ in three different configurations, when $N = 9$ and $L _ { 1 } = L _ { 2 } = L _ { 3 } = 3$ . In these cases $\widetilde { L } _ { 1 } = L _ { 1 }$ , while in (b) $\widetilde L _ { 2 } = 3 .$ in (c) $\widetilde { L } _ { 2 } = 5 ,$ and in (d) $\widetilde { L } _ { 2 } = 6$ . Note that when QuantTree chooses always the same component, we have that $\widetilde { L } _ { 2 } = L _ { 1 } + L _ { 2 } ,$ as in (d).

where $P _ { Z }$ denotes the marginal probability of $Z = [ \mathbf { X } ] _ { i } ,$ namely the marginal of X w.r.t. the component i. We denote with $F _ { Z }$ the cumulative distribution of Z and define $U = F _ { Z } ^ { - 1 } ( Z )$ and $u _ { n } = F _ { Z } ^ { - 1 } ( z _ { n } ) , n = 1 , \dots , M$ , where

$$
F _ {Z} ^ {- 1} (z) = \inf \{t \in \mathbb {R}: F _ {Z} (t) > z \}.\tag{11}
$$

The function $F _ { Z } ^ { - 1 } ( \cdot )$ is monotonically nondecreasing, thus it preserves the order and the L-th sorted value of $\{ u _ { n } \}$ can be computed as $u _ { ( L ) } = F _ { Z } ^ { - 1 } ( z _ { ( L ) } )$ ). Then, (10) becomes

$$
\begin{array}{l} p = P _ {Z} (z \in \mathbb {R}: z \leq z _ {(L)}) = \\ = P _ {U} (u \in [ 0, 1 ]: u \leq u _ {(L)}) = F _ {U} (u _ {(L)}) = u _ {(L)}. \end{array} \tag {1}\tag{12}
$$

Since U follows a uniform distribution over [0, 1], it follows that $p$ is the L-th order statistic of the uniform distribution, that is a distributed as a Beta $( L , M - L + 1 )$ (Balakrishnan & Rao, 1998). □

Thus, $p _ { 1 }$ in (8), namely the probability of $S _ { 1 }$ under $\phi _ { 0 }$ , is distributed as a Beta $( L _ { 1 } , N - L _ { 1 } + 1 )$ . To derive the distribution of the remaining $p _ { k } , k \ge 2$ , we define the conditional probability

$$
P _ {S _ {1}} (\mathbf {x} \in A) = P _ {\phi_ {0}} (\mathbf {x} \in A \mid \mathbf {x} \notin S _ {1}),\tag{13}
$$

where A is any Borel subset of X . Then, from the definition of conditional probability and the fact that $\mathbf { x } _ { 1 } , \ldots , \mathbf { x } _ { N }$ are i.i.d. according to $\phi _ { 0 }$ , it can be easily proved that the $N - L _ { 1 }$ points that do not belong to $S _ { 1 }$ are i.i.d. according to $P _ { S _ { 1 } }$ . Therefore, we can apply Proposition 1 to the subset of the $N - L _ { 1 }$ points that do not fall in $S _ { 1 }$ by setting $\mathcal { D } = \mathbb { R } ^ { d } \backslash S _ { 1 }$ and considering $P _ { S _ { 1 } }$ in place of $P _ { \mathbf { X } }$ Thus, the random variable $\widetilde { p } _ { 2 } = P _ { S _ { 1 } } ( S _ { 2 } )$ is distributed as $\mathsf { B e t a } ( L _ { 2 } , N _ { 2 } - L _ { 2 } , 1 )$ , where $N _ { 2 } = N - N _ { 1 }$ . Iterating the above procedure, we obtain that all the random variables $\widetilde { p } _ { k } , k = 1 , \ldots , K$ , defined as<sup>2</sup>

$$
\widetilde {p} _ {k} = P _ {\bigcup_ {j = 1} ^ {k - 1} S _ {j}} (S _ {k}),\tag{14}
$$

are distributed as Beta $( L _ { k } , N _ { k } - L _ { k } + 1 )$ , where $N _ { k } \ =$ $\begin{array} { r } { N - \sum _ { j = 1 } ^ { k - 1 } N _ { j } } \end{array}$

We remark the different roles of $p _ { k }$ and $\widetilde { p } _ { k }$ . While $p _ { k }$ in (8) the measure of the bin $S _ { k }$ under $\phi _ { 0 } , \widetilde { p } _ { k }$ in (14) is the ratio between $p _ { k }$ and the measure under φ of $\mathcal { X } _ { k } = \mathbb { R } ^ { d } \backslash$ $\textstyle \bigcup _ { j } ^ { k - 1 } S _ { j }$ , namely the space that remains to be partitioned at step k. As an example, for a tree with $K = 3$ leaves, if we set target probabilities $\pi _ { 1 } = \pi _ { 2 } = \pi _ { 3 } = 1 / 3$ , we obtain $\widetilde { p } _ { 1 } = 1 / 3 , \widetilde { p } _ { 2 } = 1 / 2$ and $\widetilde { p } _ { 3 } = 1$ . To prove Theorem 1 we need to derive the distribution of $p _ { k }$ , that are expressed in terms of $\widetilde { p } _ { k }$ by the following proposition.

Proposition 2. In case of histograms defined by QuantTree, thefollowing relation holds between p<sub>k</sub> and $\widetilde { p } _ { k } .$

$$
p _ {k} = \widetilde {p} _ {k} \cdot (1 - \sum_ {j = 1} ^ {k - 1} p _ {j}) = \widetilde {p} _ {k} \prod_ {j = 1} ^ {k - 1} (1 - \widetilde {p} _ {j}).\tag{15}
$$

Proof. From the law of total probability we have that

$$
\begin{array}{l} p _ {k} = P _ {\phi_ {0}} (\mathbf {x} \in S _ {k}) = \\ \quad = P _ {\phi_ {0}} \left(\mathbf {x} \in S _ {k} \mid \mathbf {x} \notin \cup_ {j = 1} ^ {k - 1} S _ {j}\right) \cdot P _ {\phi_ {0}} \left(\mathbf {x} \notin \cup_ {j = 1} ^ {k - 1} S _ {j}\right) + \\ \quad + P _ {\phi_ {0}} \left(\mathbf {x} \in S _ {k} \mid \mathbf {x} \in \cup_ {j = 1} ^ {k - 1} S _ {j}\right) \cdot P _ {\phi_ {0}} \left(\mathbf {x} \in \cup_ {j = 1} ^ {k - 1} S _ {j}\right). \end{array}\tag{16}
$$

Since sets $\{ S _ { k } \}$ defined by QuantTree are disjoint, it follows that $S _ { k }$ and $\textstyle \bigcup _ { i = 1 } ^ { k - 1 } S _ { j }$ are also disjoint, thus the second term in the sum in (16) is equal to 0. The first equality in (15) follows from the definition of $\widetilde { p } _ { k } = P _ { \phi _ { 0 } } ( \mathbf { x _ { \alpha } } \in$ $S _ { k } \mid \mathbf { x } \not \in \bigcup _ { j = 1 } ^ { k - 1 } S _ { j } )$ and the fact that $\begin{array} { r } { P _ { \phi _ { 0 } } ( \mathbf { x } \notin \bigcup _ { j = 1 } ^ { k - 1 } S _ { j } ) = } \end{array}$ $\textstyle 1 - \sum _ { j = 1 } ^ { k - 1 } p _ { j }$ . The second equality in (15) can be proved by induction over $j$ . □

The following proposition allows us to express $p _ { j }$ as a product of independent Beta distributions.

Proposition 3. The random variables pe defined over histograms computed by QuantTree are independent.

Proof. To prove the independence of the $\widetilde { p } _ { k } , k = 1 , \ldots , K$ we show that $\widetilde { p } _ { k }$ is independent from $\widetilde { p } _ { j } , j = 1 , \ldots , k - 1$ In particular, we prove that

$$
P _ {\phi_ {0}} (\widetilde {p} _ {k} \leq t _ {k} \mid \widetilde {p} _ {j} = t _ {j}, j = 1, \dots , k - 1) = P _ {\phi_ {0}} (\widetilde {p} _ {k} \leq t _ {k}).\tag{17}
$$

To this end, we follow the proof of Proposition 1, and express $\widetilde { p } _ { k }$ as an order statistic of the uniform distribution.

At iteration k, QuantTree randomly selects a dimension $i _ { k }$ and performs a split w.r.t. the $L _ { k } – \mathrm { t h }$ order statistic of the $i _ { k }$ components over the remaining $N _ { k }$ points (line 9 of Algorithm 1). Let $\widetilde { L } _ { k }$ be the position of this splitting point in $\{ z _ { n } ~ = ~ [ \mathbf { x } _ { n } ] _ { i _ { k } } , n ~ = ~ 1 , \dots , N \}$ , namely the sequence of ordered $i _ { k }$ components of all the points in T R. The value of $\widetilde { L } _ { k } \in$ N depends on realizations $\mathbf { x } _ { 1 } , \ldots , \mathbf { x } _ { N }$ and is a random variable ranging in $\{ L _ { k } , \ldots , M _ { k } \}$ , where $\begin{array} { r } { M _ { k } = \sum _ { j = 1 } ^ { k } L _ { j } } \end{array}$ . Obviously, at the first iteration $L _ { 1 } = \widetilde { L } _ { 1 }$ but then the two may differ, as shown in Figure 1. Let us now consider the splitting point with respect to $L _ { k }$ , i.e., $z _ { ( \widetilde { L } _ { k } ) }$ . From the definition of $\widetilde { p } _ { k }$ we have that

$$
\widetilde {p} _ {k} = P _ {\bigcup_ {j = 1} ^ {k - 1} S _ {j}} (S _ {k}) = P _ {\bigcup_ {j = 1} ^ {k - 1} S _ {j}} (z \leq z _ {(\widetilde {L} _ {k})}).\tag{18}
$$

As in the proof of Proposition 1, we denote with $F _ { Z }$ the cdf of $Z = [ \mathbf { X } ] _ { i _ { k } }$ , and define $U = F _ { Z } ^ { - 1 } ( Z )$ , that has a uniform distribution on [0, 1]. Therefore it holds that

$$
\begin{array}{l} \widetilde {p} _ {k} = P _ {\bigcup_ {j = 1} ^ {k - 1} S _ {j}} (z \leq z _ {(\widetilde {L} _ {k})}) = P _ {\bigcup_ {j = 1} ^ {k - 1} S _ {j}} (u \leq u _ {(\widetilde {L} _ {k})}) = \\ = F _ {U} (u _ {(\widetilde {L} _ {k})}) = u _ {(\widetilde {L} _ {k})}. \end{array} \tag {19}
$$

We use the law of total probability w.r.t. the events $\{ \widetilde { L } _ { k } =$ $a \} , a \in \{ L _ { k } , \ldots , M _ { k } \}$ , to decompose the left hand side in (17) as (for simpler notation we omit the expression $j =$ $1 , \ldots , k - 1$ in what follows):

$$
P _ {\phi_ {0}} (\widetilde {p} _ {k} \leq t _ {k} \mid \widetilde {p} _ {j} = t _ {j}) = P _ {\phi_ {0}} (u _ {(\widetilde {L} _ {k})} \leq t _ {k} \mid \widetilde {p} _ {j} = t _ {j}) =
$$

$$
= \sum_ {a = L _ {k}} ^ {M _ {k}} P _ {\phi_ {0}} (u _ {(\widetilde {L} _ {k})} \leq t _ {k} \mid \widetilde {L} _ {k} = a, \widetilde {p} _ {j} = t _ {j}) \cdot P _ {\phi_ {0}} (\widetilde {L} _ {k} = a)
$$

$$
= \sum_ {a = L _ {k}} ^ {M _ {k}} P _ {\phi_ {0}} (u _ {(a)} \leq t _ {k} \mid \widetilde {p} _ {j} = t _ {j}) \cdot P _ {\phi_ {0}} (\widetilde {L} _ {k} = a).\tag{20}
$$

Since the distribution of $u _ { ( a ) }$ does not depend on $\widetilde { p } _ { j }$ , we have that $P _ { \phi _ { 0 } } ( u _ { ( a ) } \le t _ { k } \ | \ \tilde { \ p } _ { j } = t _ { j } ) = P _ { \phi _ { 0 } } ( u _ { ( a ) } \le t _ { k } )$ therefore it follows

$$
\begin{array}{l} P _ {\phi_ {0}} \left(\widetilde {p} _ {k} \leq t _ {k} \mid \widetilde {p} _ {j} = t _ {j}\right) = \\ = \sum_ {a = L _ {k}} ^ {M _ {k}} P _ {\phi_ {0}} \left(u _ {(a)} \leq t _ {k}\right) \cdot P _ {\phi_ {0}} \left(\widetilde {L} _ {k} = a\right) \\ = \sum_ {a = L _ {k}} ^ {M _ {k}} P _ {\phi_ {0}} \left(u _ {\left(\widetilde {L} _ {k}\right)} \leq t _ {k} \mid \widetilde {L} _ {k} = a\right) \cdot P _ {\phi_ {0}} \left(\widetilde {L} _ {k} = a\right) = \\ = P _ {\phi_ {0}} \left(u _ {\left(\widetilde {L} _ {k}\right)} \leq t _ {k}\right) = P _ {\phi_ {0}} \left(\widetilde {p} _ {k} \leq t _ {k}\right), \end{array} \tag {2}\tag{21}
$$

and (17) is proved.

The proof of Theorem 1 follows from Proposition 3.

Proof of Theorem 1. For any stationary distribution $\phi _ { 0 }$ , the random vector $[ y _ { 1 } , \dots , y _ { K } ]$ conditioned on $p _ { 1 } , \ldots , p _ { K }$ follows a Multinomial distribution with parameters $\left( \nu , p _ { 1 } , \ldots , p _ { K } \right)$ (White et al., 2009). From Proposition 3 each $p _ { k }$ is a product of independent Beta distributions, thus depends only on $\{ L _ { k } \}$ and it is independent from $\phi _ { 0 }$

Therefore any statistic $\mathcal { T } _ { h }$ that is a function of $\left\{ y _ { k } \right\}$ depends only on ν, and on N and $\left\{ \pi _ { k } \right\}$ which determines $\{ L _ { k } \}$ □

## 5. Experiments

We quantitatively assess the advantages of changedetection tests based on QuantTree w.r.t. other generalpurpose tests able to detect any distribution change φ<sub>0</sub> → $\phi _ { 1 }$ . In particular, we show that: i) thresholds provided by Algorithm 2 can better control the FPR w.r.t. alternatives based on asymptotic results or bootstrap ii) HT based on histograms provided by QuantTree yielding a uniformdensity partition of $\mathbb { R } ^ { d }$ achieve higher power than other partitioning schemes.

## 5.1. Datasets and Change Models

We employ both synthetic and real-world datasets: $\operatorname { S y n - }$ thetic datasets are generated by choosing, for each dimension $d \in \{ 2 , 8 , 3 2 , 6 4 \}$ , 250 pairs $( \phi _ { 0 } , \phi _ { 1 } )$ of Gaussians, where φ has a randomly defined covariance, and $\phi _ { 1 } = \phi _ { 0 } ( Q \cdot + \mathbf { v } )$ is a roto-transalation of $\phi _ { 0 }$ such that the symmetric Kullback-Leibler divergence sKL ${ \bf \nabla } _ { \cdot } ( \phi _ { 0 } , \phi _ { 1 } ) = 1$ We control $\mathrm { s K L } ( \phi _ { 0 } , \phi _ { 1 } )$ by the CCM framework (Carrera & Boracchi, 2017), which guarantees all the changes to have the same magnitude. This is required when comparing detection performance in different dimensions.

We also employ four real-world high-dimensional sets: MiniBooNE particle identification (“particle”, $d \ = \ 5 0 )$ Physicochemical Properties of Protein Tertiary Structure (“protein”, $d = 9 )$ , Sensorless Drive Diagnosis (“sensorless”, $d \ : = \ : 4 8 )$ from the UCI Machine Learning Repository (Lichman, 2013), and Credit Card Fraud Detection (“credit”, $d = 2 9 )$ from (Dal Pozzolo et al., 2015). We standardize these datasets and add to each component of the “particle” and “sensorless” an imperceivable amount of noise $\eta \sim N ( 0 , 0 . 0 0 1 )$ ) to scramble the many repeated values, which harms histogram construction. For each dataset we simulate 150 changes $\phi _ { 0 }  \phi _ { 1 }$ by randomly selecting $T R$ and defining a random shift drawn from a normal distribution.

## 5.2. Change Detection Methods

Four of the considered methods rely on the same histogram computed through QuantTree (Algorithm 1) to provide a uniform density partition of $\mathbb { R } ^ { d }$ , i.e. the target probabilities are $\pi _ { k } = 1 / K$ , ∀k. These methods differ only for the threshold adopted and have been considered mainly to investigate the control over false positives.

Pearson Distribution Free / TV Distribution Free: thresholds are computed by Algorithm 2 for the Pearson $\mathcal { T } _ { h } ^ { P }$ (6) and the total variation $\bar { \mathcal { T } } _ { h } ^ { T V }$ statistics $( 7 ) ,$ respectively. The adopted thresholds are reported in Table 1.

Gaussian Datasets: FPR, K = 32, ν = 64, N = 4096

(g)  
![](images/95b89deff42002496375906ff661d59d0245915f8229f1a7d51a9233387494ca.jpg)  
(a)

![](images/abce5449f2f06792b0a588f8fed8608c2d8391be60cb8d2472147959081af3a9.jpg)  
(b)

![](images/3829bfa4dfb155626f35f421a5896ff91a1e0b7f5f5a2c82f841286ad0cce608.jpg)

![](images/c5a5f619bdb4dfaeeb630683249bfae45c8a82cf174ca3ff75380cd232c60ed9.jpg)

![](images/b5ddb98bdfa8f2f7f678327fe776379e2564acd4f0ebec5ff1220efdaffb528a.jpg)  
(e)

![](images/fc9dd52c4bad3b3c30a34e5e891a1e56ab06d48d7991208d265a1a79f06301dc.jpg)

![](images/180b85c2645c9641c3d2c30a2a4228d9f4962119cefbc8f1a449d9e25686353b.jpg)  
(f)

![](images/08481c30e7129dc5a2525684da02a44b5aa191d80468f97ba36174b4e21845e5.jpg)  
(h)  
Figure 2: Results on both synthetic (a)-(d) and real world (e)-(h) datasets using the small TR configuration. In (a) and (b) we report the FPR computed on the Gaussian datasets using K = 32 and $K = 1 2 8$ bins, respectively, while (c) and (d) reports the corresponding powers. Thresholds computed by Algorithm 2 successfully yield averaged FPR values smaller than the desired value α disregarding the data dimension d, as expected by Theorem 1. Moreover, the methods based on histograms computed by QuantTree achieve the highest power. The FPR obtained on the real datasets are shown in (e) and (f), for $K = 3 { \bar { 2 } }$ and $K = 1 2 8$ , respectively, and the powers are reported in (g) and (h). Also in this cases Algorithm 2 provides thresholds that successfully control the FPR and, as on Gaussian datasets, methods based on uniform histograms outperform the other in terms of power.

Pearson Asymptotic: thresholds for $\mathcal { T } _ { h } ^ { P }$ are provided from the classic $\chi ^ { 2 }$ goodness-of-fit test (Lehmann & Romano, 2006), which provides an asymptotic control over the FPR.

TV Bootstrap: thresholds for $\mathcal { T } _ { h } ^ { T V }$ are computed empirically by bootstrapping TR.

Three other methods built on different density models have been considered to assess the advantages – also in terms of HT power – of histograms providing uniform density.

Voronoi: a histogram where the $\{ S _ { k } \} _ { k }$ are defined as Voronoi cells around K randomly chosen centers in TR.

Here we compute $\mathcal { T } _ { h } ^ { T V }$ and use thresholds estimated by bootstrapping over T R.

Density Tree: A binary tree aiming at approximating $\phi _ { 0 } .$ where splits are defined by a maximum information-gain criterion, in a similar fashion to random density trees like (Criminisi et al., 2011). We use $\mathcal { T } _ { h } ^ { T V }$ with thresholds empirically computed by bootstrap over $T R .$

Parametric: in the synthetic experiments we consider also an HT based on a parametric density model. In particular, we fit a Gaussian density on TR, compute the loglikelihood (Song et al., 2007; Kuncheva, 2013) of each incoming batch W, and detect changes by means of the t-test. Since this method exploits the true density model, it has to be considered as an ideal reference.

All the methods are configured and tested on the same T R and tested on the same batches W. We perform a PCA transformation, estimated from TR, to all the methods based on trees as density models. We have in fact experienced that this improves the change-detection performance, since it aligns the coordinate axes – along which splits are performed – with the principal components that become parallel to the bin boundaries.

## 5.3. Test Design and Performance Measures

We consider a small TR configuration, where $N = 4 0 9 6$ and $\nu = 6 4 .$ , and a large TR configuration, where $N =$ 16384 and $\nu = 2 5 6$ . Both configurations have been tested with a number of bins $K = 3 2$ and $K = 1 2 8$ , leading to 4 different combinations $( N , \nu , K )$ . In all our experiments, the target FPR has been set to $\alpha = 0 . 0 5$

We empirically compute the FPR as the ratio of detections over 100 stationary batches $W \sim \phi _ { 0 } ,$ , for each considered φ<sub>0</sub>. Similarly, for each change $\phi _ { 0 }  \phi _ { 1 }$ , we estimate the test power over 100 batches $W \sim \phi _ { 1 }$ . The average FPR and power computed over the whole datasets are reported as dots in Figure 2. To illustrate the distribution of the FPR and power we report their boxplots.

## 5.4. Results and Discussion

Figure 2 shows the FPR and the power of all the methods in the small T R configuration. Figures 2(a-b),(e-f) confirm that QuantTree effectively controls the FPR, for both the Pearson and total variation statistics, which is very important in change-detection. The peculiar QuantTree construction and Algorithm 2 provide very accurate thresholds resulting in FPR below the reference value $\alpha = 0 . 0 5$ . Moreover, even if histograms defined by QuantTree feature a small number of bins, they are able to effectively monitor high-dimensional datastreams.

The FPRs of the total variation statistic are typically lower than others: this is due to the discrete nature of the statistics, which affects both testing and quantile estimation. The same problem occurs, but to a lesser extent, in the Pearson statistic, since the expression (6) contains a square that allows this statistic to assume a larger number of distinct values. Clearly, increasing $K$ attenuates this problem, bringing the FPR closer to α. Thresholds used in the traditional Pearson test achieve larger FPR values, as the number of training samples in each bin is too low for the asymptotic approximation to hold: in the large TR configuration, the problem attenuates (plots and tables of average values are reported in the Appendix). Since the likelihood values do not follow a Gaussian distribution, the FPR are not properly controlled in the t-test of the Parametric method either. In all these tests, smaller values of K provide a better control over FPR, since the number of samples in each bin is larger.

Concerning the power, Figures 2(c-d) show a clear decay when d increases: this is consistent with the Detectability loss problem, which has been analytically studied in (Alippi et al., 2016) when monitoring the log-likelihood (as the Parametric). In general, all the methods on Synthetic datasets achieve satisfactory performance, and uniform histograms obtained through the QuantTree appear a better choice than Density Tree and Voronoi. There are minor differences among methods based on QuantTree which are nevertheless consistent with the FPR in Figure 2(a-b). Uniform density histograms outperforms others on real world datasets, see Figure 2(g-h), indicating that their partitioning scheme is better at detecting changes. Obviously, increasing N and ν provides superior performance (see the results reported in the supplementary materials).

## 6. Conclusions

In this paper we have presented QuantTree, an algorithm to build histograms for change detection through a recursive binary splitting of the input space. Our theoretical analysis allows a characterization of the probability of each bin defined by QuantTree and shows that this probability is independent from the distribution $\phi _ { 0 }$ of stationary data. This implies that statistics defined over such histograms are non parametric and thresholds can be estimated through numerical simulation on synthetically generated data. Experiments show that our thresholds (estimated using samples drawn from a univariate uniform distribution) enable a better control of the FPR than asymptotic ones or those estimated by bootstrap, which is no longer necessary when using such histograms. Ongoing work investigates how to mitigate the impact of test statistics assuming a limited number of discrete values, asymptotic results for histograms generated by QuantTree, and extensions to sequential monitoring schemes.

## References

Alippi, C., Boracchi, G., and Roveri, M. Just-in-time classifiers for recurrent concepts. IEEE Transactions on Neural Networks and Learning Systems, 24(4):620–634, 2013.

Alippi, C., Boracchi, G., Carrera, D., and Roveri, M. Change detection in multivariate datastreams: Likelihood and detectability loss. In Proceedings of the International Joint Conference on Artificial Intelligence (IJ-CAI), volume 2, pp. 1368–1374, 2016.

Balakrishnan, N. and Rao, C. R. Order statistics: theory & methods. Elsevier Amsterdam, 1998.

Basseville, M. and Nikiforov, I. V. Detection of abrupt changes: theory and application. Prentice Hall Englewood Cliffs, 1993.

Bentley, J. L. Multidimensional binary search trees used for associative searching. Communications of the ACM, 18(9):509–517, 1975.

Bifet, A. and Gavalda, R. Learning from time-changing data with adaptive windowing. In Proceedings of the SIAM International Conference on Data Mining, volume 7, pp. 2007–2023, 2007.

Boracchi, G., Cervellera, C., and Maccio, D. Uniform his-\` tograms for change detection in multivariate data. In Proceedings of the IEEE International Joint Conference of Neural Networks (IJCNN), pp. 1732–1739, 2017.

Carrera, D. and Boracchi, G. Generating high-dimensional datastreams for change detection. Big Data Research, 2017.

Criminisi, A., Shotton, J., and Konukoglu, E. Decision forests for classification, regression, density estimation, manifold learning and semi-supervised learning. Microsoft Research, 2011.

Dal Pozzolo, A., Caelen, O., Johnson, R. A., and Bontempi, G. Calibrating probability with undersampling for unbalanced classification. In Proceedings of the IEEE Symposium Series on Computational Intelligence and Data Mining (CIDM), pp. 159–166, 2015.

Dasu, T., Krishnan, S., Venkatasubramanian, S., and Yi, K. An information-theoretic approach to detecting changes in multi-dimensional data streams. In Proceedings of the Symposium on the Interface of Statistics, Computing Science, and Applications, 2006.

Ditzler, G. and Polikar, R. Hellinger distance based drift detection for nonstationary environments. In Proceedings of the IEEE Symposium on Computational Intelligence in Dynamic and Uncertain Environments (CIDUE), pp. 41–48, 2011.

Gama, J., Zliobaite, I., Bifet, A., Pechenizkiy, M., and Bouchachia, A. A survey on concept drift adaptation. ACM Computing Surveys (CSUR), 46(4):1–44, 2014.

Harel, M., Mannor, S., El-Yaniv, R., and Crammer, K. Concept drift detection through resampling. In Proceedings of the International Conference on Machine Learning (ICML), pp. 1009–1017, 2014.

Justel, A., Pena, D., and Zamar, R. A multivariate˜ kolmogorov-smirnov test of goodness of fit. Statistics & Probability Letters, 35(3):251–259, 1997.

Krempl, G. The algorithm apt to classify in concurrence of latency and drift. In Proceedings of the Intelligent Data Analysis (IDA), pp. 222–233, 2011.

Kuncheva, L. I. Change detection in streaming multivariate data using likelihood detectors. IEEE Transactions on Knowledge and Data Engineering, 25(5):1175–1180, 2013.

Lehmann, E. L. and Romano, J. P. Testing statistical hypotheses. Springer, 2006.

Lichman, M. UCI machine learning repository, 2013. URL http://archive.ics.uci.edu/ml.

Lung-Yut-Fong, A., Levy-Leduc, C., and Capp ´ e, O. Ro-´ bust changepoint detection based on multivariate rank statistics. In Proceedings of the IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP), pp. 3608–3611, 2011.

Page, E. S. Continuous inspection schemes. Biometrika, 41(1/2):100–115, 1954.

Qahtan, A. A., Alharbi, B., Wang, S., and Zhang, X. A pcabased change detection framework for multidimensional data streams: Change detection in multidimensional data streams. In Proceedings of the ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD), pp. 935–944, 2015.

Ross, G. J. and Adams, N. M. Two nonparametric control charts for detecting arbitrary distribution changes. Journal ofQuality Technology, 44(2):102, 2012.

Ross, G. J., Tasoulis, D. K., and Adams, N. M. Nonparametric monitoring of data streams for changes in location and scale. Technometrics, 53(4):379–389, 2011.

Saatc¸i, Y., Turner, R. D., and Rasmussen, C. E. Gaussian process change point models. In Proceedings of the International Conference on Machine Learning (ICML), pp. 927–934, 2010.

Song, X., Wu, M., Jermaine, C., and Ranka, S. Statistical change detection for multi-dimensional data. In Proceedings of the International Conference on Knowledge Discovery and Data Mining (KDD), pp. 667–676, 2007.

White, L. F., Bonetti, M., and Pagano, M. The choice of the number of bins for the m statistic. Computational statistics & data analysis, 53(10):3640–3649, 2009.