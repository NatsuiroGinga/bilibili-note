---
title: "2021-Hu-SoRR-Sum-of-Ranked-Range-arXiv"
date: 2026-09-04
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/ranking/2021-Hu-SoRR-Sum-of-Ranked-Range-arXiv.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Sum of Ranked Range Loss for Supervised Learning

Shu Hu Department of Computer Science and Engineering University at Bufalo, State University of New York Bufalo, NY 14260-2500, USA

Yiming Ying Department of Mathematics and Statistics University at Albany, State University of New York Albany, NY 12222, USA

Xin Wang Department of Computer Science and Engineering University at Bufalo, State University of New York Bufalo, NY 14260-2500, USA

Siwei Lyu<sup>∗</sup>

Department of Computer Science and Engineering University at Bufalo, State University of New York Bufalo, NY 14260-2500, USA

Editor: Lorenzo Rosasco

shuhu@buffalo.edu

yying@albany.edu

xwang264@buffalo.edu

siweilyu@buffalo.edu

## Abstract

In forming learning objectives, one oftentimes needs to aggregate a set of individual values to a single output. Such cases occur in the aggregate loss, which combines individual losses of a learning model over each training sample, and in the individual loss for multi-label learning, which combines prediction scores over all class labels. In this work, we introduce the sum of ranked range (SoRR) as a general approach to form learning objectives. A ranked range is a consecutive sequence of sorted values of a set of real numbers. The minimization of SoRR is solved with the diference of convex algorithm (DCA). We explore two applications in machine learning of the minimization of the SoRR framework, namely the AoRR aggregate loss for binary/multi-class classification at the sample level and the TKML individual loss for multi-label/multi-class classification at the label level. A combination loss of AoRR and TKML is proposed as a new learning objective for improving the robustness of multi-label learning in the face of outliers in sample and labels alike. Our empirical results highlight the efectiveness of the proposed optimization frameworks and demonstrate the applicability of proposed losses using synthetic and real data sets.

Keywords: Learning objective, Aggregate Loss, Rank-based Losses, Multi-class classification, Multi-label classification

## 1. Introduction

Learning objective is a fundamental component in any machine learning system. In forming learning objectives, we often need to aggregate a set of individual values to a single numerical value. Such cases occur in the aggregate loss, which combines individual losses of a learning model over each training sample, and in the individual loss for multi-label learning, which combines prediction scores over all class labels. In this paper, we refer to the loss over all training data as the aggregate loss, in order to distinguish it from the individual loss that measures the quality of the model on a single training example. For a set of real numbers representing individual values, the ranking order reflects the most basic relation among them. Therefore, designing learning objectives can be achieved by choosing operations defined based on the ranking order of the individual values.

![](images/23f2463b3d85817de2309e94c3ba51f45319243a290a20e5e1dc7cf7134d46df.jpg)  
Figure 1: Illustrative examples of diferent approaches to aggregate individual values to form learning objectives in machine learning. AoRR represents the average of ranked range method.

Straightforward choices for such operations are the average and the maximum. Both are widely used in forming aggregate losses (Vapnik, 1992; Shalev-Shwartz and Wexler, 2016) and multi-label losses (Madjarov et al., 2012), yet each has its own drawbacks. The average is insensitive to minority sub-groups while the maximum is sensitive to outliers, which usually appear as the top individual values. The average top-k loss is introduced as a compromise between the average and the maximum for aggregate loss (Fan et al., 2017) and multi-label individual loss (Fan et al., 2020a). However, it dilutes but not excludes the influences of the outliers. The situation is graphically illustrated in Figure 1.

In this work, we introduce the sum of ranked range (SoRR) as a new form of learning objectives that aggregate a set of individual values to a single value. A ranked range is a consecutive sequence of sorted values of a set of real numbers. The SoRR can be expressed as the diference between two sums of the top ranked values, which are convex functions themselves. As such, the SoRR is the diference of two convex functions, and its optimization is an instance of the diference-of-convex (DC) programming problems (Le Thi and Dinh, 2018). Therefore, it is natural to adopt the existing DC algorithm (DCA) (Tao et al., 1986) to eficiently solve the SoRR related learning problems.

We explore two applications in machine learning of the minimization of the SoRR framework. The first is to use the average of ranked range (AoRR) as an aggregate loss for binary/multi-class classification. Specifically, we consider individual logistic loss and individual hinge loss in AoRR for binary classification. On the other hand, we consider softmax loss as an individual loss in AoRR for multi-class classification. The AoRR can be easily obtained by considering using an average operator on SoRR (see Section 4 for more details). Unlike previous aggregate losses, the AoRR aggregate loss can completely eliminate the influence of outliers if their proportion in training data is known. We also propose a framework that can optimize AoRR without prior knowledge about the proportion of outliers by utilizing a clean validation set extracted from the training data set. Second, we use a special case of SoRR as a new type of individual loss for multi-label, the top-k multi-label (TKML) loss, which explicitly encourages the true labels in the top k range. Furthermore, we propose a TKML-AoRR loss, which combines the AoRR and the TKML methods. The proposed loss can eliminate the outliers in the top-k multi-label learning. Then a heuristic algorithm is designed to optimize TKML-AoRR . The new learning objectives are tested and compared experimentally on several synthetic and real data sets<sup>1</sup>.

The main contributions of this work can be summarized as follows:

• We introduce SoRR as a general learning objective and show that it can be formulated as the diference of two convex functions.

• Based on SoRR, we introduce the AoRR aggregate loss for binary/multi-class classification at the sample level and the TKML individual loss for multi-label/multi-class learning at the label level. The two SoRR-based losses are further combined to form the TKML-AoRR loss that can improve the robustness of multi-label learning in the face of outliers in data and labels alike.

• We also explore several theoretical aspects of SoRR-based losses, including connecting AoRR to the Condition Value at Risk (CVaR) and explore its generalization property, establishing its classification calibration with regards to the optimal Bayes classifier.

• The learning of SoRR-based losses can be generally solved by the DC algorithm, but we also show their connections with the bilevel optimization. Furthermore, we propose practical methods to better determine the hyper-parameters in SoRR-based losses.

• We empirically demonstrate the robustness and efectiveness of the proposed AoRR, TKML, TKML-AoRR, and their optimization frameworks on both synthetic and real data sets.

This paper significantly extends our previous conference paper (Hu et al., 2020) both theoretically and experimentally in the following aspects: 1) We establish the relations between SoRR and the bilevel optimization problem (Borsos et al., 2020) (Section 3.1); 2) The AoRR aggregate loss is reformulated by the Condition Value at Risks (CVaRs) and its generalization property is studied (Section 4.2); 3) We propose a new framework for automatically determining the hyper-parameters in SoRR-based losses and empirically demonstrate its efectiveness (Section 4.3 and 4.4.2); 4) We combine AoRR aggregate loss at the sample level and TKML individual loss at the label level to reduce the influence of the outliers in the top-k multi-label learning procedure. We also propose a heuristic algorithm to optimize this combined loss and verify its efectiveness through experiments (Section 6).

The rest of the paper is organized as follows. In Section 2, we summarize the existing works that are related to this work and discuss how this work difers from them. In Section 3, we define the sum of ranked range SoRR, formulate it as a DC problem and provide a DC algorithm for solving it. Then we connect the SoRR to the bilevel optimization problem. In Section 4, we propose a new form of aggregate loss named AoRR aggregate loss based on

SoRR for binary and multi-class classification. We provide its interpretation and study its classification calibration property. We also connect it to the CVaR problem and provide a generalization bound. Furthermore, to make it more reliable in the practice, we propose a new framework for determining the hyper-parameters of AoRR. In Section 5, we define TKML individual loss based on SoRR for multi-label/multi-class learning. In Section $6 ,$ we define TKML-AoRR loss, which combines TKML loss for label level and AoRR loss for sample level. The TKML-AoRR loss can eliminate the influence of the outliers in the top-k multi-label learning. Then we propose a heuristic algorithm to optimize it. Section 7 concludes the paper with discussions.

## 2. Related Work

There are a large body of works that focus on designing diferent forms of individual losses to solve specific problems and studying their properties, especially for binary classification. The earliest work can be traced back to 1960s by Shuford et al. (1966) and Savage (1971). Specifically, Shuford et al. (1966) propose admissible probability measurement procedures as individual losses to measure students’ degree-of-belief probabilities in an educational environment. Savage (1971) characterizes scoring rules for probabilistic forecasts of categorical and binary variables. More recent work of Buja et al. (2005); Masnadi-Shirazi and Vasconcelos (2008); Lin et al. (2017); Reid and Williamson (2010) continue to study this topic. For example, Buja et al. (2005) study loss functions for binary class probability estimation and classification. Masnadi-Shirazi and Vasconcelos (2008) discuss the robustness of outliers from a theoretical aspect in designing loss functions for classification. Reid and Williamson (2010) study general composite binary losses. Many researchers prefer to select and use individua losses in terms of a convex function because of the good global convergence properties in its optimization. However, non-convex individual losses are also explored in recent work, such as Lin et al. (2017); He et al. (2010); Wu and Liu (2007); Yu et al. (2010). Concretely, to handle the imbalanced data problem, Lin et al. (2017) design focal loss for object detection. To handle the outliers problem, He et al. (2010) propose to learn a robust sparse representation for face recognition based on the correntropy (Liu et al., 2007) along with the use of an $\ell _ { 1 }$ norm penalty, which is insensitive to outliers. Wu and Liu (2007) propose a robust truncated hinge loss for SVM. Yu et al. (2010) propose a robust estimation method for classification based on loss clipping. All of them are trying to design non-convex individual losses for robust learning.

Rank-based aggregate losses are oftentimes overlooked in existing machine learning literature. One relevant topic is the data subset selection problem (Wei et al., 2015), which is about selecting a subset from a large training dataset to train a model while incurring a minimal average loss, the learning objective of which can be regarded as a special aggregate loss that averages over the individual losses corresponding to data selected into the subset. Hard example mining is an efective method in the training and is widely used in existing works (Gidaris and Komodakis, 2015; Liu et al., 2016; Shrivastava et al., 2016; Lin et al., 2017). For instance, in online hard example mining, Shrivastava et al. (2016) use top-k samples with the largest losses for each training image to update the model parameter. In object detection, Lin et al. (2017) propose a weighted cross-entropy loss, which assigns more weights on candidate bounding box with large losses. They obtain a better performance with this method than using the conventional cross-entropy loss. However, it should be mentioned that the connections of these works to the aggregate loss are incidental. The most relevant works on the rank-based aggregate loss are Fan et al. (2017) and Lyu et al. (2020). In their works, Fan et al. and Lyu et al. propose an average top-k loss as a type of aggregate loss. They also mention that the maximum loss (Shalev-Shwartz and Wexler, 2016) and the average loss (Vapnik, 1992) are two special cases of their average top-k loss. They demonstrate that their loss can alleviate the influence of data with imbalance and outlier problems in the learning process. However, as we mentioned before, their method can dilute but not completely eliminate the influence of the outliers.

Rank-based individual losses have been studied in many tasks. For example, multilabel/multi-class learning, ranking, and information retrieval. The work from Rudin (2009); Usunier et al. (2009) propose a form of individual loss that gives more weights to the samples at the top of a ranked list. This idea is further extended to multi-label learning in the work of Weston et al. (2011). Top-1 loss is commonly used in multi-class learning, which causes more penalties when the class corresponding to the top-1 prediction score inconsistent with the ground-truth class label (Crammer and Singer, 2001). Since a sample may contain multiple classes and some classes may overlap, Lapin et al. (2015, 2016, 2017) propose top-k multi-class loss that can introduce penalties when the ground-truth label does not appear in the set of top-k labels as measured by their prediction scores. In multi-label learning, many works focus on the ranking-based approaches, such as Zhang and Zhou (2006); Fan et al. (2020b). The loss functions from their methods encourage the predicted relevancy scores of the ground-truth positive labels to be higher than that of the negative ones. Similar to the motivation of the top-k multi-class classification, in multi-label learning, the classifier is expected to include as many true labels as possible in the top k outputs. However, there are no dedicated methods for the top-k multi-label learning. Therefore, in this paper, we propose TKML individual loss for multi-label learning to fill this gap.

Rank-based losses are also popular to be used at the sample and label levels simultaneously. For example, the work of Rawat et al. (2020) proposed a doubly-stochastic mining method, which combines the methods of Kawaguchi and Lu (2020) and Lapin et al. (2015). They use the average top-k methods both at the data sample and label levels to construct the final loss function. Then the constructed loss is applied to solve modern retrieval problems, which are characterized by training sets with a huge number of labels, and heterogeneous data distributions across sub-populations. However, their method does not consider the outliers or noisy labels that may exist in real-world data sets. Such problems can make the performance of the proposed model plummet. In addition, their model only works on multi-class problems and cannot be applied to multi-label learning directly. In this paper, we fill this gap and propose a TKML-AoRR loss for solving the noise problem in top-k multi-label learning. Furthermore, we design a heuristic algorithm for optimizing TKML-AoRR loss and show it can be generalized to other existing algorithms in Shen and Sanghavi (2019); Shah et al. (2020); Kawaguchi and Lu (2020); Rawat et al. (2020).

## 3. Sum of Ranked Range (SoRR)

For a set of real numbers $S = \{ s _ { 1 } , \cdots , s _ { n } \}$ , we use $s _ { [ k ] }$ to denote the top-k value, which is the k-th largest value after sorting the elements in S (ties can be broken in any consistent way). Correspondingly, we define $\begin{array} { r } { \phi _ { k } ( S ) = \sum _ { i = 1 } ^ { k } s _ { [ i ] } } \end{array}$ as the sum of the top-k values of S. For two integers k and $m , \ 0 \leq \ m < k \leq n$ , the $( m , k )$ -ranked range is the set of sorted values $\{ s _ { [ m + 1 ] } , \cdot \cdot \cdot , s _ { [ k ] } \}$ . The sum of $( m , k )$ -ranked range $( ( m , k ) – \mathbf { S } \circ \mathrm { R R } )$ is defined as $\begin{array} { r } { \psi _ { m , k } ( S ) = \sum _ { i = m + 1 } ^ { k } s _ { [ i ] } } \end{array}$ , and the average of $( m , k )$ -ranked range $( ( m , k ) – \mathtt { A o R R } )$ is $\frac { 1 } { k - m } \psi _ { m , k } ( S )$ It is easy to see that the sum of ranked range (SoRR) is the diference between two sums of top values as, $\psi _ { m , k } ( S ) = \phi _ { k } ( S ) - \phi _ { m } ( S )$ Also, the $\mathrm { t o p } { - } k$ value corresponds to the $( k - 1 , k )$ -SoRR, as $\psi _ { k - 1 , k } ( S ) = s _ { [ k ] }$ . Similarly, the median can also be obtained from AoRR, as $\frac { 1 } { \lceil \frac { n + 1 } { 2 } \rceil - \lfloor \frac { n + 1 } { 2 } \rfloor + 1 } \psi _ { \lfloor \frac { n + 1 } { 2 } \rfloor - 1 , \lceil \frac { n + 1 } { 2 } \rceil } ( S )$ . We collect symbols and notations to be used throughout the paper in Table 1.

<table><tr><td>Symbol</td><td>Description</td></tr><tr><td> $S = \{s_1, \cdots, s_n\}$ </td><td>A set of real numbers</td></tr><tr><td> $s_{[k]} (s_{[m]})$ </td><td>The  $k$ -th ( $m$ -th) largest value after sorting the elements in  $S$ </td></tr><tr><td> $s_i(\cdot)$ </td><td>The  $i$ -th individual loss</td></tr><tr><td> $\phi_k(\cdot) (\phi_m(\cdot))$ </td><td>The sum of top- $k$  (top- $m$ ) values</td></tr><tr><td> $\psi_{m,k}(\cdot)$ </td><td>The sum of  $(m, k)$ -ranked range values</td></tr><tr><td> $q_i$ </td><td>The weight of  $s_i(\cdot)$ </td></tr><tr><td> $x$ </td><td>A multi-dimensional data instance</td></tr><tr><td> $y$ </td><td>A label (class) of  $x$ </td></tr><tr><td> $f_\theta(\cdot), f(\cdot; \theta)$ </td><td>A parametric function (classifier) with parameters  $\theta$ </td></tr><tr><td> $\mathcal{L}(\cdot)$ </td><td>Loss function</td></tr><tr><td> $\mathcal{D}$ </td><td>Training data set</td></tr><tr><td> $\widetilde{\mathcal{D}}$ </td><td>Validation data set</td></tr><tr><td> $\mathcal{Y} = \{1, \cdots, l\}$ </td><td>A set of labels (classes) with size  $l$ </td></tr><tr><td> $Y$ </td><td>Ground truth labels of  $x$  and it is a subset of  $\mathcal{Y}$ </td></tr></table>

Table 1: Frequently used symbols in this paper.

In machine learning problems, we are interested in the set $S ( \theta ) = \{ s _ { 1 } ( \theta ) , \cdot \cdot \cdot , s _ { n } ( \theta ) \}$ formed from a family of functions where each $s _ { i }$ is a convex function of parameter θ. For example, in practice, s can be a convex loss function. n is the total number of training samples. $s _ { i }$ is the individual loss function of sample i. We can use SoRR to form learning objectives. In particular, we can eliminate the ranking operation and use the equivalent form of SoRR in the following result. Denote $[ a ] _ { + } = \operatorname* { m a x } \{ 0 , a \}$ as the hinge function.

Theorem 1 Suppose $s _ { i } ( \theta )$ is convex with respect to θ for any $i \in [ 1 , n ]$ , then

$$
\min _ {\theta} \psi_ {m, k} (S (\theta)) = \min _ {\theta} \left[ \min _ {\lambda \in \mathbb {R}} \left\{k \lambda + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \lambda ] _ {+} \right\} - \min _ {\hat {\lambda} \in \mathbb {R}} \left\{m \hat {\lambda} + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \hat {\lambda} ] _ {+} \right\} \right].\tag{1}
$$

Furthermore, $\hat { \lambda } > \lambda$ , when the optimal solution is achieved.

The proof of Theorem 1 is in Appendix A.1. Note that $\psi _ { m , k } ( S ( \theta ) )$ is not a convex function of θ. But its equivalence to the diference between $\phi _ { k } ( S ( \theta ) )$ and $\phi _ { m } ( S ( \theta ) )$ suggests that $\psi _ { m , k } ( S ( \theta ) )$ is a diference-of-convex (DC) function, because $\phi _ { k } ( S ( \theta ) )$ and $\phi _ { m } ( S ( \theta ) )$ are convex functions of θ in this setting. As such, a natural choice for its optimization is the DC algorithm (DCA) (Tao et al., 1986).

To be specific, for a general DC problem formed from two convex functions $g ( \theta ) , h ( \theta )$ as $\overline { { s } } ( \theta ) = g ( \theta ) - h ( \theta )$ , DCA iteratively search for a critical point of $\overline { { s } } ( \theta )$ (Thi et al., 2017). At each iteration of DCA, we form an afine majorization of function h using its sub-gradient at $\theta ^ { ( t ) } , \ i . e . , \ \hat { \theta } ^ { ( t ) } \in \partial h ( \theta ^ { ( t ) } )$ , and then update $\boldsymbol { \theta } ^ { ( t + 1 ) } \in \operatorname { a r g m i n } _ { \boldsymbol { \theta } } \left\{ \boldsymbol { g } ( \boldsymbol { \theta } ) - \boldsymbol { \theta } ^ { \top } \hat { \boldsymbol { \theta } } ^ { ( t ) } \right\}$ . DCA is a descent method without line search, which means the objective function is monotonically decreased at each iteration (Tao and An, 1997). It does not require the diferentiability of $g ( \theta )$ and $h ( \theta )$ to assure its convergence. Moreover, it is known that DCA converges from an arbitrary initial point and often converges to a global solution (Le Thi and Dinh, 2018). For example, the authors in Tao and An (1997) proved that $\theta ^ { * }$ is a critical point of $\overline { { s } } ( \theta )$ if $\partial g ( \theta ^ { * } ) \cap \partial h ( \theta ^ { * } ) \neq \emptyset$ , or equivalently, $0 \in \partial g ( \theta ^ { * } ) - \partial h ( \theta ^ { * } )$ . A critical point can lead to a local minimizer of $\overline { { s } } ( \theta )$ if it admits a neighborhood U such that $\partial h ( \theta ) \cap \partial g ( \theta ^ { * } ) \neq \emptyset , \forall \theta \in U \cap$ dom g. While a DC problem can be solved based on standard (sub-)gradient descent methods, DCA seems to be more amenable to our task because of its appealing properties and the natural DC structure of our objective function. In addition, as shown in Piot et al. (2016) with extensive experiments, DCA empirically outperforms the gradient descent method on various problems.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1: DCA for Minimizing SoRR
1 Initialization:  $\theta^{(0)}$ ,  $\lambda^{(0)}$ ,  $\eta_{l}$ , and two hyperparameters k and m
2 for  $t = 0, 1, \ldots$  do
3 Compute  $\hat{\theta}^{(t)}$  with equation (3)
4 for  $l = 0, 1, \ldots$  do
5 | Compute  $\theta^{(l+1)}$  and  $\lambda^{(l+1)}$  with equation (2)
6 end
7 Update  $\theta^{(t+1)} \leftarrow \theta^{(l+1)}$ 
8 end
</div>

To use DCA to optimize SoRR, we need to solve the convex sub-optimization problem

$$
\min _ {\theta} \left[ \min _ {\lambda} \left\{k \lambda + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \lambda ] _ {+} \right\} - \theta^ {T} \hat {\theta} \right].
$$

This problem can be solved using a stochastic sub-gradient method (Bottou and Bousquet, 2008; Rakhlin et al., 2011; Srebro and Tewari, 2010). We first randomly sample $s _ { i _ { l } } ( \theta ^ { ( l ) } )$ from the collection of $\{ s _ { i } ( \theta ^ { ( l ) } ) \} _ { i = 1 } ^ { n }$ and then perform the following steps:

$$
\theta^ {(l + 1)} \leftarrow \theta^ {(l)} - \eta_ {l} \left(\partial s _ {i _ {l}} (\theta^ {(l)}) \cdot \mathbb {I} _ {[ s _ {i _ {l}} (\theta^ {(l)}) > \lambda^ {(l)} ]} - \hat {\theta} ^ {(t)}\right), \lambda^ {(l + 1)} \leftarrow \lambda^ {(l)} - \eta_ {l} \left(k - \mathbb {I} _ {[ s _ {i _ {l}} (\theta^ {(l)}) > \lambda^ {(l)} ]}\right),\tag{2}
$$

where $\eta _ { l }$ is the step size. $\mathbb { I } _ { [ a ] }$ is an indicator function with $\mathbb { I } _ { [ a ] } = 1$ if a is true and 0 otherwise. In equation (2), we use the fact that the sub-gradient of $\dot { \phi _ { m } } ( S ( \theta ) )$ is computed, as

$$
\hat {\theta} \in \partial \phi_ {m} (S (\theta)) = \sum_ {i = 1} ^ {n} \partial s _ {i} (\theta) \cdot \mathbb {I} _ {[ s _ {i} (\theta) > s _ {[ m ]} (\theta) ]},\tag{3}
$$

where $\partial s _ { i } ( \theta )$ is the gradient or a sub-gradient of convex function $s _ { i } ( \theta )$ (Proof can be found in Appendix $\mathrm { A . 2 } ) ^ { 2 }$ . The pseudo-code of minimizing SoRR is described in Algorithm 1. For a given outer loop size $| t | ,$ , an inner loop size |l|, and training sample size n, the time complexity of Algorithm 1 is $O ( | t | ( n \log n + | l | ) )$ .

To better understand SoRR, we provide more discussion about it. Since SoRR is non-convex, an intuitive strategy to optimize a non-convex loss function is to use a surrogate convex loss to replace it and apply existing convex optimization approaches to solve the proposed surrogate convex loss. However, there are two drawbacks to this strategy. First, a significant learning property of the surrogate loss is its consistency, which requires the optimal minimizers of the surrogate loss to be near to or exact the optimal minimizers of the original loss. As we shall see, the study of consistency is significantly more complex for SoRR. Fortunately, we rewrite SoRR to a DC problem (equation (1)), and then we can show AoRR aggregate loss (a variant of SoRR only add an additional factor) satisfies the classification calibration (a suficient condition for consistency) under several moderate conditions in Section 4.1. Second, it is very hard to find a suitable convex loss to surrogate SoRR. If we can find a surrogate convex loss, the optimal solution obtained by learning this convex loss and the actual optimal solution based on SoRR are not guaranteed to be equal. This diference comes not only from the optimization algorithm, but also from the learning objective. For example, we may select the sum of the top-k loss $\phi _ { k } ( S )$ to surrogate $\psi _ { m , k } ( S )$ since it is a convex loss. But $\phi _ { k } ( S )$ will use extremely largest values (top-1 value to top-m value) to train the model, while $\psi _ { m , k } ( S )$ is not. Therefore, they have diferent meanings in model learning. In other words, the learned models are exactly diferent. The model learned by using $\phi _ { k } ( S )$ may not satisfy the origina requirements in specific tasks such as robust to outliers. However, in equation (1), the DC term (right-hand side) is exactly equivalent to the original SoRR formula (left-hand side). Since the DC problem is well studied in the existing works and can be solved by DCA with provable convergence properties, it is beneficial and natural to use the DC function to replace the original ranking formula even if the DC function is also non-convex.

## 3.1 Connection with Bilevel Optimization

We give another intuitive interpretation of SoRR. Suppose we have 10 individual losses in the ranked list. To extract the sum of (2, 6)-ranked range, we can select a subset, which contains the bottom 8 individual losses from the ranked list in the beginning. Then we select the top 4 individual losses from this subset as the finalized (2, 6)-ranked range. Suppose $s _ { i } ( \theta ) \geq 0$ , based on this new intuition, we can reformulate SoRR. First, we sum the bottom n − m losses as follows,

$$
\sum_ {i = m + 1} ^ {n} s _ {[ i ]} (\theta) = \min _ {q} \sum_ {i = 1} ^ {n} q _ {i} s _ {i} (\theta) \quad \mathrm{s.t.} q _ {i} \in \{0, 1 \}, | | q | | _ {0} = n - m,
$$

where $q = \{ q _ { 1 } , \cdot \cdot \cdot , q _ { n } \} \in \{ 0 , 1 \} ^ { n }$ , and $q _ { i }$ is an indicator. When $q _ { i } = 0 $ , it indicates that the i-th individual loss is not included in the objective function. Otherwise, the objective function should include this individual loss. Next, we sum the $\mathrm { t o p } { - } ( k - m )$ individual losses from the bottom $n - m$ individual losses as follows,

$$
\begin{array}{l} \min _ {q} \sum_ {i = 1} ^ {k - m} (q s (\theta)) _ {[ i ]} \quad \text {s.t.} q _ {i} \in \{0, 1 \}, | | q | | _ {0} = n - m \\ = \min _ {\lambda , q} (k - m) \lambda + \sum_ {i = 1} ^ {n} [ q _ {i} s _ {i} (\theta) - \lambda ] _ {+} \quad \text {s.t.} q _ {i} \in \{0, 1 \}, | | q | | _ {0} = n - m \\ = \min _ {\lambda , q} (k - m) \lambda + \sum_ {i = 1} ^ {n} q _ {i} [ s _ {i} (\theta) - \lambda ] _ {+} \quad \text {s.t.} q _ {i} \in [ 0, 1 ], | | q | | _ {0} = n - m, \end{array}\tag{4}
$$

where $q s ( \theta ) = \{ q _ { 1 } s _ { 1 } ( \theta ) , \cdot \cdot \cdot , q _ { n } s _ { n } ( \theta ) \}$ . The first equation holds because of Lemma $\mathrm { A . 1 }$ . Since $q _ { i } s _ { i } ( \theta ) \geq 0$ , we know the optimal $\lambda ^ { * } \geq 0$ from Lemma A.1. If $q _ { i } = 0 , [ q _ { i } s _ { i } ( \theta ) - \lambda ^ { * } ] _ { + } = 0 =$ $q _ { i } [ s _ { i } ( \theta ) - \lambda ^ { * } ] _ { + }$ . If $q _ { i } = 1 , [ q _ { i } s _ { i } ( \theta ) - \lambda ^ { * } ] _ { + } = [ s _ { i } ( \theta ) - \lambda ^ { * } ] _ { + } = q _ { i } [ s _ { i } ( \theta ) - \lambda ^ { * } ] _ { + }$ . Thus the second equation holds. It should be mentioned that the discrete indicator $q _ { i }$ can be replaced by a continue one, which means $q _ { i } \in [ 0 , 1 ]$ . The reason is that the optimal $q$ is at a corner of the hypercube $[ 0 , 1 ] ^ { n }$ . In fact, with the outer minimization of model parameter $\theta ,$ the above objective function is equivalent to equation (1). Specifically, we obtain a theorem as follows,

Theorem 2 With relaxing $q$ to [0, 1], equation $( 4 )$ is equivalent to equation $( { \boldsymbol { 1 } } ) .$

$$
\begin{array}{c} \min _ {\lambda , q} (k - m) \lambda + \sum_ {i = 1} ^ {n} q _ {i} [ s _ {i} (\theta) - \lambda ] _ {+} \quad s. t. q _ {i} \in [ 0, 1 ], | | q | | _ {0} = n - m \\ = \min _ {\lambda} \Big \{k \lambda + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \lambda ] _ {+} \Big \} - \min _ {\hat {\lambda}} \Big \{m \hat {\lambda} + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \hat {\lambda} ] _ {+} \Big \}. \end{array}
$$

Proof can be found in Appendix A.3. Combining the optimization of the model parameter $\theta ,$ we can reform equation (4) to a bilevel optimization problem (Borsos et al., 2020; Jenni and Favaro, 2018) as follows,

$$
\begin{array}{l l} \min _ {\lambda , q} & (k - m) \lambda + \sum_ {i = 1} ^ {n} q _ {i} [ s _ {i} (\theta^ {*} (q)) - \lambda ] _ {+} \\ \text {s.t.} & \theta^ {*} (q) \in \underset {\theta} {\operatorname{argmin}} (k - m) \lambda + \sum_ {i = 1} ^ {n} q _ {i} [ s _ {i} (\theta) - \lambda ] _ {+} \\ & q _ {i} \in [ 0, 1 ], | | q | | _ {0} = n - m, \end{array}\tag{5}
$$

where we minimize an outer objective, here the first row of equation (5), which in turn depends on the solution $\theta ^ { * } ( q )$ to an inner optimization problem (the second row of equation (5)) with the constraint on $q .$ This problem (equation (5)) can be solved through some existing bilevel optimization algorithms (Borsos et al., 2020). For example, we can adopt the coresets via bilevel optimization algorithm from Borsos et al. (2020) to solve our cardinalityconstrained bilevel optimization problem. We only need to take our specific inner problem, outer problem, and constraints into their optimization framework.

## 4. AoRR Aggregate Loss for Binary and Multi-class Classification

SoRR provides a general framework to aggregate individual values to form a learning objective. Here, we examine its use as an aggregate loss in supervised learning problems in detail and optimize it using the DC algorithm. Specifically, we aim to find a parametric function $f _ { \theta }$ with parameter $\theta$ that can predict a target y from the input data or features x using a set of labeled training samples $\{ ( x _ { i } , y _ { i } ) \} _ { i = 1 } ^ { n }$ . We assume that the individual loss for a sample $( x _ { i } , y _ { i } )$ is $s _ { i } ( \theta ) = s ( f ( x _ { i } ; \theta ) , y _ { i } ) \geq 0$ . The learning objective for supervised learning problem is constructed from the aggregate loss ${ \mathcal { L } } ( S ( \theta ) )$ that accumulates all individual losses over training samples, $S ( \theta ) = \{ s _ { i } ( \theta ) \} _ { i = 1 } ^ { n }$ . Specifically, we define the AoRR aggregate loss as

$$
\mathcal {L} _ {a o r r} (S (\theta)) = \frac {1}{k - m} \psi_ {m, k} (S (\theta)) = \frac {1}{k - m} \sum_ {i = m + 1} ^ {k} s _ {[ i ]} (\theta).
$$

If we choose the $\ell _ { 2 }$ individual loss or the hinge individual loss, we get the learning objectives in Ortis et al. (2019) and Kanamori et al. (2017), respectively. For $m \geq 1$ , we can optimize AoRR using the DCA as described in Section 3.

The AoRR aggregate loss is related to previous aggregate losses that are widely used to form learning objectives.

• the average loss (Vapnik, 2013): $\begin{array} { r } { \mathcal { L } _ { a v g } ( S ( \theta ) ) = \frac { 1 } { n } \sum _ { i = 1 } ^ { n } s _ { i } ( \theta ) } \end{array}$

• the maximum loss (Shalev-Shwartz and Wexler, 2016): $\mathcal { L } _ { m a x } ( S ( \theta ) ) = \mathrm { m a x } _ { 1 \leq i \leq n } s _ { i } ( \theta )$

• the median loss (Ma et al., 2011): $\begin{array} { r } { \mathcal { L } _ { m e d } ( S ( \theta ) ) = \frac { 1 } { 2 } \left( s _ { \left[ \lfloor \frac { n + 1 } { 2 } \rfloor \right] } ( \theta ) + s _ { \left[ \lceil \frac { n + 1 } { 2 } \rceil \right] } ( \theta ) \right) } \end{array}$ ;

• the average top-k loss $( \mathrm { A T } _ { k } )$ (Fan et al., 2017): $\begin{array} { r } { \mathcal { L } _ { a v t - k } ( S ( \theta ) ) = \frac { 1 } { k } \sum _ { i = 1 } ^ { k } s _ { [ i ] } ( \theta ) } \end{array}$ , for $1 \leq k \leq n$

The AoRR aggregate loss generalizes the average loss $( k = n$ and $m = 0 )$ , the maximum loss $( k = 1$ and $m = 0 )$ , the median loss $\textstyle ( k = \lceil { \frac { n + 1 } { 2 } } \rceil$ 2 $m = \lfloor { \frac { n + 1 } { 2 } } \rfloor - 1 )$ , and the average top-k loss $( m = 0 )$ . Interestingly, the average of the bottom- $( n - m )$ loss, ${ \mathcal { L } } _ { a b t - m } ( S ( \theta ) ) =$ $\begin{array} { r } { \frac { 1 } { n - m } \sum _ { i = m + 1 } ^ { n } s _ { [ i ] } ( \theta ) } \end{array}$ , which is not widely studied in the literature as a learning objective, is an instance of the AoRR aggregate loss $( k = n )$ . In addition, the robust version of the maximum loss (Shalev-Shwartz and Wexler, 2016), which is a maximum loss on a subset of samples of size at least $n - ( k - 1 )$ , where the number of outliers is at most $k - 1$ , is equivalent to the top-k loss, a special case of the AoRR aggregate loss $( m = k - 1 )$

Using the AoRR aggregate loss can bring flexibility in designing learning objectives and alleviate drawbacks of previous aggregate losses. In particular, the average loss, the maximum loss, and the $\mathrm { A T } _ { k }$ loss are all influenced by outliers in training data since outliers usually correspond to extremely large individual losses and all of these methods inevitably use large individual losses to construct aggregate losses. They only difer in the degree of influence, with the maximum loss being the most sensitive to outliers. In comparison, AoRR loss can completely eliminate the influence of the top individual losses by excluding the top m individual losses from the learning objective.

In addition, traditional approaches to handling outliers focus on the design of robust individual losses over training samples, notable examples include the Huber loss (Friedman et al., 2001) and the capped hinge loss (Nie et al., 2017). Changing individual losses may not be desirable, as they are usually relevant to the learning problem and application. On the other hand, instead of changing the definition of individual losses, our method builds in robustness at the aggregate loss level, using the AoRR aggregate loss. The resulting learning algorithm based on Algorithm 1 is more flexible and allows the user to choose an individual loss form that is relevant to the learning problem.

![](images/95b1f23efac828733ed05f196a53f69e363e29fdecc595abafe56e5fb9efd19c.jpg)  
Figure 2: The AoRR loss and other losses interpreted at the individual sample level. The shaded area over 0.00 loss corresponds to data/target with the correct classification. Note that we fix $\lambda = 0 . 4$ and $\hat { \lambda } = 1 . 3$ to draw the AoRR curve.

The robustness to outliers of the AoRR loss can be more clearly understood at the individual sample level, with fixed λ and $\hat { \lambda } .$ We use binary classification to illustrate with $s _ { i } ( \theta ) = s ( y _ { i } f _ { \theta } ( x _ { i } ) )$ where $f _ { \theta }$ is the parametric predictor and $y _ { i } \in \{ \pm 1 \}$ . In this case, $y _ { i } f _ { \theta } ( x _ { i } ) > 0$ and $y _ { i } f _ { \theta } ( x _ { i } ) < 0$ corresponds to the correct and false predictions, respectively. Specifically, noting that $s _ { i } ( \theta ) \geq 0$ , we can rearrange terms in equation (1) to obtain

$$
\mathcal {L} _ {a o r r} (S (\theta)) = \frac {1}{k - m} \min _ {\lambda > 0} \max _ {\hat {\lambda} > \lambda} \sum_ {i = 1} ^ {n} \left\{[ s _ {i} (\theta) - \lambda ] _ {+} - [ s _ {i} (\theta) - \hat {\lambda} ] _ {+} \right\} + k \lambda - m \hat {\lambda}.\tag{6}
$$

We are particularly interested in the term inside the summation in equation (6)

$$
[ s (y f _ {\theta} (x)) - \lambda ] _ {+} - [ s (y f _ {\theta} (x)) - \hat {\lambda} ] _ {+} = \left\{ \begin{array}{c c} \hat {\lambda} - \lambda & s (y f _ {\theta} (x)) > \hat {\lambda} \\ s (y f _ {\theta} (x)) - \lambda & \lambda <   s (y f _ {\theta} (x)) \leq \hat {\lambda} \\ 0 & s (y f _ {\theta} (x)) \leq \lambda \end{array} \right..
$$

According to this, at the level of individual training samples, the equivalent efect of using the AoRR loss is to uniformly reduce the individual losses by λ, but truncate the reduced individual loss at values below zero or above $\hat { \lambda } .$ The situation is illustrated in Figure 2 for the logistic individual loss $s ( y f ( x ) ) = \log _ { 2 } ( 1 + e ^ { - y f ( x ) } )$ , which is a convex and smooth surrogate to the ideal 01-loss. The efect of reducing and truncating from below and above has two interesting consequences. First, note that the use of convex and smooth surrogate loss inevitably introduces penalties to samples that are correctly classified but are “too close” to the boundary. The reduction of the individual loss alleviates that improper penalty. This property is also shared by the $\mathrm { A T } _ { k }$ loss. On the other hand, the ideal 01-loss exerts the same penalty to all incorrect classified samples regardless of their margin value, while the surrogate has unbounded penalties. This is the exact cause of the sensitivity to outliers of the previous aggregate losses, but the truncation of AoRR loss is similar to the 01-loss, and thus is more robust to the outliers. It is worth emphasizing that the above explanation of the AoRR loss has been illustrated at the individual sample level with fixed λ and λ.<sup>ˆ</sup> The aggregate AoRR loss defined by equation (6) as a whole is not an average sample-based loss because it can not be decomposed into the summation of individual losses over samples.

## 4.1 Classification Calibration

A fundamental question in learning theory for classification (Bartlett et al., 2006; Vapnik, 2013) is to investigate when the best possible estimator from a learning objective is consistent with the best possible, i.e., the Bayes rule. Here we investigate this statistical question for the AoRR loss by considering its infinite sample case, i.e., $n \to \infty$ . As mentioned above, the AoRR loss as a whole is not the average of individual losses over samples, and therefore the analysis for the standard ERM (Bartlett et al., 2006; Lin, 2004) does not apply to our case.

We assume that the training data $\{ ( x _ { i } , y _ { i } ) \} _ { i = 1 } ^ { n }$ are i.i.d. from an unknown distribution p on $\mathcal { X } \times \{ \pm 1 \}$ . The misclassification error measures the quality of a classifier $f : \mathcal { X } \to \{ \pm 1 \}$ and is denoted by $\mathcal { R } ( f ) = \mathrm { P r } ( Y \neq f ( X ) ) = \mathbb { E } [ \mathbb { I } _ { Y f ( X ) \leq 0 } ]$ . The Bayes error leads to the least expected error, which is defined by $\mathcal { R } ^ { * } = \operatorname* { i n f } _ { f } \mathcal { R } ( f )$ . No function can achieve the Bayes error than the Bayes rule $f _ { c } ( x ) = \mathrm { s i g n } ( \eta ( x ) - { \textstyle { \frac { 1 } { 2 } } } )$ , where $\eta ( x ) = P ( Y = 1 | X = x )$ . It is well noted that, in practice, one uses a surrogate loss $\ell : \mathbb { R } \to [ 0 , \infty )$ which is a continuous function and upper-bounds the 01-loss. Its true risk is given by $\mathcal { E } _ { \ell } ( f ) = \mathbb { E } [ \ell ( Y f ( X ) ) ]$ . Denote the optimal \`-risk by $\mathcal { E } _ { \ell } ^ { * } = \operatorname* { i n f } _ { f } \mathcal { E } _ { \ell } ( f )$ , the classification calibration (point-wise form of Fisher consistency) for loss \` (Bartlett et al., 2006; Lin, 2004) holds true if the minimizer $f _ { \ell } ^ { * } = \operatorname* { i n f } _ { f } \mathcal { E } _ { \ell } ( f )$ has the same sign as the Bayes rule $f _ { c } ( x ) , i . e . ,$ , sign $( f _ { \ell } ^ { * } ( x ) ) = \mathrm { s i g n } ( f _ { c } ( x ) )$ whenever $f _ { c } ( x ) \neq 0$

In analogy, we can investigate the classification calibration property of the AoRR loss. Specifically, we first obtain the population form of the AoRR loss using the infinite limit of the empirical one given by equation (6). Indeed, we know from (Bhat and Prashanth, 2019; Brown, 2007) that, for any bounded f and $\alpha \in ( 0 , 1 ]$ , there holds $\begin{array} { r } { \operatorname* { i n f } _ { \lambda \geq 0 } \alpha \lambda + \frac { 1 } { n } \sum _ { i = 1 } ^ { n } [ s ( y _ { i } f _ { \theta } ( x _ { i } ) ) - } \end{array}$ $\begin{array} { r } { \lambda ] _ { + } \to \operatorname* { i n f } _ { \lambda \geq 0 } \alpha \lambda + \mathbb { E } [ s ( Y f ( X ) ) - \lambda ] _ { + } } \end{array}$ as $n \to \infty$ . Consequently, we have the limit case of the AoRR loss $\mathcal { L } _ { a o r r } ( S ( \theta ) )$ restated as follows:

$$
\begin{array}{r l}&{\frac {n}{k - m} \Bigg [ \min _ {\lambda} \Big \{\frac {k}{n} \lambda + \frac {1}{n} \sum_ {i = 1} ^ {n} [ s (y _ {i} f _ {\theta} (x _ {i})) - \lambda ] _ {+} \Big \} - \min _ {\hat {\lambda}} \Big \{\frac {m}{n} \hat {\lambda} + \frac {1}{n} \sum_ {i = 1} ^ {n} [ s (y _ {i} f _ {\theta} (x _ {i})) - \hat {\lambda} ] _ {+} \Big \} \Bigg ]}\\&{\frac {\frac {k}{n} \rightarrow \nu , \frac {m}{n} \rightarrow \mu}{n \rightarrow \infty} \xrightarrow [ n \rightarrow \infty ]{} \frac {n}{k - m} \Bigg [ \min _ {\lambda \geq 0} \Big \{\mathbb {E} [ [ s (Y f (X)) - \lambda ] _ {+} ] + \nu \lambda \Big \} - \min _ {\hat {\lambda} \geq 0} \Big \{\mathbb {E} [ [ s (Y f (X)) - \hat {\lambda} ] _ {+} ] + \mu \hat {\lambda} \Big \} \Bigg ].}\end{array}\tag{7}
$$

Throughout the paper, we assume that $\nu > \mu$ which is reasonable as $k > m$ . In particular, we assume that $\mu > 0$ since if $\mu = 0$ then it will lead to $\hat { \lambda } = \infty$ and this case is reduced to the population version of the average top-k case in Fan et al. (2017). As such, the population version of our AoRR loss (equation (6)) is given by

$$
(f_{0}^{*},\lambda^{*},\hat{\lambda}^{*}) = \arg \inf_{f,\lambda \geq 0}\sup_{\substack{\hat{\lambda}\geq 0}}\left\{\mathbb{E}[ [s(Yf(X)) - \lambda ]_{+} - [s(Yf(X)) - \hat{\lambda}]_{+}] + (\nu \lambda -\mu \hat{\lambda})\right\} .\tag{8}
$$

It is dificult to directly work on the optima $f _ { 0 } ^ { * }$ since the problem in equation (8) is a non-convex min-max problem and the standard min-max theorem does not apply here. Instead, we assume the existence of $\lambda ^ { * }$ and $\hat { \lambda } ^ { * }$ in equation (8) and work with the minimizer $f ^ { * } = \arg$ inf $_ f \mathcal { L } ( f , \lambda ^ { * } , \hat { \lambda } ^ { * } )$ where $\mathcal { L } ( f , \lambda ^ { * } , \hat { \lambda } ^ { * } ) : = \mathbb { E } [ [ s ( Y f ( X ) ) - \lambda ^ { * } ] _ { + } - [ s ( Y f ( X ) ) - \hat { \lambda } ^ { * } ] _ { + } ] +$ $( \nu \lambda ^ { * } - \mu \hat { \lambda } ^ { * } )$ . Now we can define the classification calibration for the AoRR loss.

Definition 3 The AoRR loss is called classification calibrated if, for any $x ,$ there is a minimizer $f ^ { * } = \arg \operatorname* { i n f } _ { f } \mathcal { L } ( f , \lambda ^ { * } , \hat { \lambda } ^ { * } )$ such as $f ^ { * } ( x ) > 0 \ i f \eta ( x ) > 1 / 2$ and $f ^ { * } ( x ) < 0 \ i f \eta ( x ) < 1 / 2$

We can then obtain the following theorem. Its proof can be found in Appendix A.4.

Theorem 4 Suppose the individual loss $s : \mathbb { R } \to \mathbb { R } ^ { + }$ is non-increasing, convex, diferentiable at 0 and $s ^ { \prime } ( 0 ) < 0 . \ I f 0 \leq \lambda ^ { * } < \hat { \lambda } ^ { * }$ , then the AoRR loss is classification calibrated.

The assumptions in Theorem 4 are easily to be satisfied. Indeed, the commonly used individual losses such as the hinge loss $s ( t ) = [ 1 - t ] _ { + }$ and the logistic loss $s ( t ) = \log _ { 2 } ( 1 +$ $e ^ { - t } )$ satisfy the conditions of non-increasing, convex, diferentiable at 0, and $s ^ { \prime } ( 0 ) < 0$ Furthermore, according to Theorem 1 and $0 \leq m < k \leq n ,$ we obtain $\lambda ^ { * } < \hat { \lambda } ^ { * }$ . Suppose the individual loss $s ( t )$ is non-negative (this holds for the above-mentioned individual losses), we have $0 \leq \lambda ^ { * } < \hat { \lambda } ^ { * }$ . We also provide several examples that cannot make the assumptions hold. For example, the least square loss $s ( t ) = ( 1 - t ) ^ { 2 }$ is not a non-increasing individual loss. Therefore, using it as an individual loss cannot guarantee the AoRR aggregate loss satisfies classification calibration. In addition, if $k \leq m$ , the hypothesis $0 \leq \lambda ^ { * } < \hat { \lambda } ^ { * }$ will not be held. So we also cannot obtain a classification calibrated AoRR aggregate loss.

## 4.2 Connection with Conditional Value at Risk

It is worthy of mentioning that the average of the top-k method is also related to the risk measure called conditional value at risk (CVaR) at level $\textstyle \alpha = { \frac { k } { n } }$ (Shapiro et al., 2014, Chapter 6) in portfolio optimization for efective risk management.

Let (Ω, Σ, P) be a probability space. The conditional value at risk (CVaR) at level $\alpha \in ( 0 , 1 )$ of a random variable $s : \Omega \to { \mathbb { R } }$ is defined as $\begin{array} { r } { C _ { \alpha } [ s ] : = \operatorname* { i n f } _ { \lambda } \{ \lambda + \frac { 1 } { \alpha } \mathbb { E } [ [ s - \lambda ] _ { + } ] \} } \end{array}$ . If s is a continuous random variable, then $C _ { \alpha } [ s ] = \mathbb { E } [ s | s \geq V _ { \alpha } [ s ] ]$ , where $V _ { \alpha } [ s ]$ is called the value at risk (VaR) and defined as $V _ { \alpha } [ s ] : = \operatorname* { s u p } \{ \lambda \in \mathbb { R } | \operatorname* { P r } ( s \geq \lambda ) \geq \alpha \}$ . A sample-based estimate of $C _ { \alpha } [ s ]$ can be denoted by $\begin{array} { r } { \widehat { C } _ { \alpha } [ s ] : = \operatorname* { i n f } _ { \lambda \in \mathbb { R } } \{ \lambda + \frac { 1 } { n \alpha } \sum _ { i = 1 } ^ { n } [ s _ { i } - \lambda ] _ { + } \} } \end{array}$ , which is also called the empirical of $C _ { \alpha } [ s ]$ . The CVaR has a natural distributionally robust optimization interpretation (Shapiro et al., 2014). Therefore, from equation (8), we know the population version of AoRR $\mathcal { L } ( f , \lambda , \hat { \lambda } ) = \operatorname* { i n f s u p } _ { \lambda } \left\{ \mathbb { E } [ [ s ( Y f ( X ) ) - \lambda ] _ { + } - [ s ( Y f ( X ) ) - \hat { \lambda } ] _ { + } ] + ( \nu \lambda - \mu \hat { \lambda } ) \right\}$ can be expressed by diference of two CVaRs. We call it as Interval Conditional Value at Risks (ICVaRs).

$$
\mathcal {L} (f, \lambda , \hat {\lambda}) = \nu C _ {\nu} [ s (\theta) ] - \mu C _ {\mu} [ s (\theta) ].\tag{9}
$$

![](images/1b3184d838cd18dff29eba9dd945d3607a6d43aa38c5237d92535ce8e979e972.jpg)  
Figure 3: The yellow area between two red dash lines represents ICVaRs

Figure 3 is an interpretation of ICVaRs. We denote the empirical form of $\mathcal { L } ( f , \lambda , \hat { \lambda } )$ by $\widehat { \mathcal { L } } ( \bar { f } , \lambda , \widehat { \lambda } )$ , and

$$
\widehat {\mathcal {L}} (f, \lambda , \widehat {\lambda}) = \nu \widehat {C} _ {\nu} [ s (\theta) ] - \mu \widehat {C} _ {\mu} [ s (\theta) ].\tag{10}
$$

The following theorem provides some deviation convergence bounds for estimating $\psi _ { m , k } ( S ( \theta ) )$ from a finite number of independent samples.

Theorem 5 If supp $( s ( \theta ) ) \subseteq [ a , b ]$ and s has a continuous distribution function, then for any $\delta \in ( 0 , 1 ]$ 2

$$
\begin{array}{r l} & {\operatorname * {P r} \left(\mathcal {L} (f, \lambda , \hat {\lambda}) - \widehat {\mathcal {L}} (f, \lambda , \hat {\lambda}) \leq (b - a) \left[ \sqrt {\frac {5 k \ln (3 / \delta)}{n ^ {2}}} + \sqrt {\frac {\ln (1 / \delta)}{2 n}} \right]\right) \geq 1 - \delta ,} \\ & {\operatorname * {P r} \left(\mathcal {L} (f, \lambda , \hat {\lambda}) - \widehat {\mathcal {L}} (f, \lambda , \hat {\lambda}) \geq - (b - a) \left[ \sqrt {\frac {5 m \ln (3 / \delta)}{n ^ {2}}} + \sqrt {\frac {\ln (1 / \delta)}{2 n}} \right]\right) \geq 1 - \delta .} \end{array}
$$

Proof can be found in Appendix A.5. It should be mentioned that we can derive better generalization bounds in some mild conditions (sub-Gaussian, light-tailed, and heavy-tailed data distributions) according to Prashanth et al. (2020); Thomas and Learned-Miller (2019). Note that the non-asymptotic relation between the excess generalization induced by AoRR and the target classification problem (e.g. excess misclassification error) is a fundamentally important question. However, it is very hard to establish this relation since the AoRR involves that the diference of two possible convex losses, i.e. $[ s ( y f _ { \theta } ( x ) ) - \lambda ] _ { + } - [ s ( y f _ { \theta } ( x ) ) - \hat { \lambda } ] _ { + }$ . We leave this relation for future study.

## 4.3 Determine k and m

Hyper-parameters k and m are very important for the final performance of the AoRR aggregate loss. However, before actually training the model, it is dificult to determine their suitable values so that the model can achieve the best performance. We cannot fix them to some specific values. For diferent data sets, they may have diferent suitable values. Greedy search is a good method for us to find the optimal k and m in a finite time, but it only works on simple data sets that contain a small number of samples. For large data sets, the greedy search method is not eficient and could be very time-consuming.

In practice, for large-scale data sets, we can decide on an approximate value of m if we have prior knowledge about the faction of outliers in the data set. To avoid extra freedom due to the value of $k ,$ we follow a very popular adaptive setting that has been applied in previous works $\left( \mathrm { e . g . } \right.$ , Kawaguchi and Lu (2020)). At the beginning of training, k equals to the size (n) of training data, $k = \lfloor \frac { n } { 2 } \rfloor$ once training accuracy $\geq 7 0 \% , k = \lfloor \frac { n } { 4 } \rfloor$ once training accuracy $\geq 8 0 \% , k = \lfloor \frac { n } { 8 } \rfloor$ once training accuracy $\geq 9 0 \% , k = \lfloor \frac { n } { 1 6 } \rfloor$ once training accuracy $\geq 9 5 \%$ $\begin{array} { r } { k = \lfloor \frac { n } { 3 2 } \rfloor } \end{array}$ once training accuracy $\geq 9 9 . 5 \%$ . However, if we do not have prior knowledge about the fraction of outliers in the data set, the adaptive setting method still needs to try diferent values of m from its feasible space and then find the optimal values of k and $m .$ . Obviously, the time complexity is dominated by the size of $m \mathrm { { s } }$ feasible set. Therefore, this method will take a long time to search for the optimal hyper-parameters if we apply it to a large data set.

Many existing works on label corruption or label noise problem assume that training data is not clean and potentially includes noise and outliers. However, in general, there are many trusted samples are available. These trusted data can be collected to create a clean validation set. This assumption has been analyzed in Charikar et al. (2017) and also been used by other works for designing a robust learning model (Hendrycks et al., 2018; Ren et al., 2018; Veit et al., 2017; Li et al., 2017b). Hendrycks et al. (2018) proposes a loss correction technique for deep neural network classifiers that use clean data to alleviate the influences of label noise. Li et al. (2017b) proposes a distillation framework by using a clean data set to reduce the risk of learning from noisy labels. We apply this assumption to our problem. Specifically, we extract a clean validation set from training data to determine the values of k and m. According to Theorem 1, fix $\theta ,$ we will get the optimal values of λ and $\hat { \lambda }$ if we know the values of k and $m$ . Based on the values of λ and $\hat { \lambda } ,$ we can calculate how many individual losses are larger than them. These also provide us information about k and m. Therefore, we can directly calculate the optimal λ and $\hat { \lambda }$ based on the validation set instead of determining the optimal values of k and $m .$

According to the above analysis, we propose a framework (Figure 4) to combine hyperparameters learning and Algorithm 1. To better learn the parameters of $\lambda$ and $\hat { \lambda } ,$ we first use the average aggregate loss to “warm-up” the model for some epochs by training on the training data $\mathcal { D } ,$ , which contains outliers. This pre-processing has been used in many existing works such as Li et al. (2020a); Hendrycks et al. (2018). As shown in Figure 4, to “warm-up” the model, one needs to use forward and backward (see Steps 1 and 2) to update the model parameter $\theta ^ { ( t ) }$ with learning rate $\eta _ { t }$ . After a few epochs, with a stopping criterion (Step 3), we use model $\theta ^ { ( t ) }$ on the clean validation set $\widetilde { \mathcal { D } }$ to learn the individual losses (Step 4). Through simple operations 1 and $^ { 2 , }$ we can get $\hat { \lambda }$ and $\lambda .$ . For example, we can calculate the mean value plus one standard deviation of all individual losses from $\widetilde { \mathcal { D } }$ and then regard it as operation 1 and regard the mean value minus two standard deviations of all individual losses from $\widetilde { \mathcal { D } }$ as operation 2. Note that we should keep $\hat { \lambda } > \lambda$ according to Theorem 1. When we have $\hat { \lambda } ,$ we can obtain sub-gradient $\hat { \theta }$ based on training data $\mathcal { D }$ and equation (3). With D, $\hat { \theta }$ and $\lambda ,$ we use an inner loop and stochastic gradient descent method with learning rate $\eta _ { l }$ to update the inner convex model parameter $\theta ^ { ( l ) }$ . Meanwhile, apply $\theta ^ { ( l ) }$ on $\widetilde { \mathcal { D } }$ and re-use operation 2 to update the parameter $\lambda .$ . This procedure (Steps 5, 6, and 7) is similar to equation (2). With another stopping criterion (Step 8), we can update $\theta ^ { ( t ) }$ by using $\theta ^ { ( l ) }$ and redo steps 4, 5, 6, 7, and 8 repeatedly until the final stopping criterion is satisfied. We list detailed step-by-step pseudo-code in Algorithm 2. For a given outer loop size |t|, an inner loop size |l|, the “warm-up” loop size $| p |$ , training sample size $n ,$ and the validation sample size $\widetilde { n } .$ , the time complexity of Algorithm 2 is $O ( ( | p | + | t | ) n + | t | \cdot | l | \cdot \widetilde { n } )$

![](images/c0d9f93b3402ee638e47a0a5f69a1e399cef49362946a46c20b53c3387762212.jpg)  
Figure 4: The framework of learning hyper-parameters. Note that we calculate the mean value plus one standard deviation of all individual losses from $\widetilde { \mathcal { D } }$ and then regard it as operation 1 and regard the mean value minus two standard deviations of all individual losses from $\widetilde { \mathcal { D } }$ as operation 2 in practice.

## 4.4 Experiments

We empirically demonstrate the efectiveness of the AoRR aggregate loss combined with two types of individual losses for binary classification, namely, the logistic loss and the hinge loss. For simplicity, we consider a linear prediction function $f ( x ; \theta ) = \theta ^ { T }$ x with parameter θ, and the $\ell _ { 2 }$ regularizer $\frac { 1 } { 2 C } | | \theta | | _ { 2 } ^ { 2 }$ with $C > 0$ . For binary classification, we apply the greedy search method to select optimal hyper-parameters k and $m$ . We use the MNIST data set with symmetric (i.e. uniformly random) label noise to verify the efectiveness of our Algorithm 2 for learning hyper-parameters and show the AoRR aggregate loss can also be extended to multi-class classification. All algorithms are implemented in $\mathrm { P y }$ thon 3.6 and trained and tested on an Intel(R) Xeon(R) CPU W5590 @3.33GHz with 48GB of RAM.

## 4.4.1 AoRR for Binary Classification

Synthetic data. We generate two sets of 2D synthetic data (Figure 5). Each data set contains 200 samples from Gaussian distributions with diferent means and variances. We consider both the case of the balanced (Figure 5 (a,b)) and the imbalanced (Figure 5 (c,d)) data distributions, in the former the training data for the two classes are approximately equal while in the latter one class has a dominating number of samples in comparison to the other. The learned linear classifiers with diferent aggregate losses are shown in Figure 5. Both data sets have an outlier in the blue class (shown as ×).

To optimally remove the efect of outliers, we need to set k larger than the number of outliers in the training data set. Since there is one outlier in this synthetic data set, we select k = 2 here as an example. As shown in Figure 5, neither the maximum loss nor the average loss performs well on the synthetic data set, due to the existence of outliers and the multi-modal nature of the data. Furthermore, Figure 5 also shows that the $\mathrm { A T } _ { k }$ loss does not bode well: it is still afected by outliers. The reason can be that the training process with the $\mathrm { A T } _ { k }$ loss with $k = 2$ will most likely pick up one individual loss from the outlier for optimization. In contrast, the AoRR loss with k=2 and m=1, which is equivalent to the top-2 or second-largest individual loss, yields better classification results. Intuitively, we avoid the direct efects of the outlier since it has the largest individual loss value. Furthermore, we perform experiments to show misclassification rates of AoRR with respect to diferent values of k in Figure 5 (e), (f), (g), (h) for each case and compare with the $\mathrm { A T } _ { k }$ loss and optimal Bayes classifier. The results show that for k values other than $2 ,$ the AoRR loss still exhibits an advantage over the $\mathrm { A T } _ { k }$ loss. Our experiments are based on a grid search for selecting the value of k and m because we found it is simple and often yields comparable performance.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2: DCA for Minimizing AoRR without Setting k and m

1 Initialization:  $\theta^{(0)}$ ,  $\eta_t$ ,  $\eta_l$ ,  $\hat{\lambda} = 0$ ,  $\lambda = 0$ , flag=0, training data set D (with outliers), and validation data set  $\widetilde{D}$  (without outliers).

2 for t = 0, 1, ... do

3 if flag == 0 then

4 for p = 0, 1, ... do

5  $\theta^{(p+1)} \leftarrow \theta^{(p)} - \frac{\eta_t}{|\mathcal{D}|} \sum_{i \in \mathcal{D}} \partial s_i(\theta)$ 

6 if Stopping criterion then

7  $\hat{\lambda} \leftarrow \text{operation1}(\{s_j(\theta^{(p+1)})|j \in \widetilde{\mathcal{D}}\})$ 

8  $\lambda \leftarrow \text{operation2}(\{s_j(\theta^{(p+1)})|j \in \widetilde{\mathcal{D}}\})$ 

9 flag  $\leftarrow 1$ ,  $\theta^{(0)} \leftarrow \theta^{(p+1)}$ 

10 break

11 end

12 end

13 else

14 Compute  $\hat{\theta}^{(t)} \in \frac{1}{|\mathcal{D}|} \sum_{i \in \mathcal{D}} \partial s_i(\theta^{(t)}) \cdot \mathbb{I}_{[s_i(\theta^{(t)}) &gt; \hat{\lambda}]}$ 

15 for l = 0, 1, ... do

16 Randomly sample  $s_{i_l}(\theta^{(l)})$  from the collection of  $\{s_i(\theta^{(l)})\}_{i \in D}$ 

17  $\theta^{(l+1)} \leftarrow \theta^{(l)} - \eta_l (\partial s_{i_l}(\theta^{(l)}) \cdot \mathbb{I}_{[s_{i_l}(\theta^{(l)}) &gt; \lambda]} - \hat{\theta}^{(t)})$ 

18  $\lambda \leftarrow \text{operation2}(\{s_j(\theta^{(l+1)})|j \in \widetilde{\mathcal{D}}\})$ 

19 end

20 Update  $\theta^{(t+1)} \leftarrow \theta^{(l+1)}$ 

21  $\hat{\lambda} \leftarrow \text{operation1}(\{s_j(\theta^{(t+1)})|j \in \widetilde{\mathcal{D}}\}), \lambda \leftarrow \text{operation2}(\{s_j(\theta^{(t+1)})|j \in \widetilde{\mathcal{D}}\})$ 

22 end

23 end
</div>

![](images/cd5047d05fe7ea95c2f1e9eef9bebee651835c2c52044a8220e7ec1775dee28f.jpg)  
Figure 5: Comparison of diferent aggregate losses for binary classification on a balanced but multi-modal synthetic data set and with outliers with logistic loss (a) and hinge loss (b), and an imbalanced synthetic data set with outliers with logistic loss (c) and hinge loss (d). Outliers in data are shown as × in blue class. The figures (e), (f), (g) and (h) show the misclassification rates of AoRR w.r.t. diferent values of k for each case and compare with the $\mathrm { A T } _ { k }$ and the optimal Bayes classifier.

In order to evaluate the efects of diferent aggregate losses on more than one outlier, we also conduct additional experiments on the multi-modal toy example that includes more outliers. We consider six cases as follows,

• Case 1 (2 outliers). In Figure 6 (a) and (b), there exist two outliers. Let hyperparameters k = 3 and m = 2.

• Case 2 (3 outliers). Figure 6 (c) and (d) contain three outliers. In this scenario, k = 4 and m = 3.

• Case 3 (4 outliers). Figure 6 (e) and (f) include four outliers and we set $k = 5$ and $m = 4$

• Case 4 (5 outliers). There are five outliers in Figure 6 (g) and (h). We set $k = 6$ and $m = 5$

• Case 5 (10 outliers). Ten outliers have been included in Figure 6 (i) and (j). Let k = 11 and m = 10 in this case.

• Case 6 (20 outliers). We create twenty outliers in Figure 6 (k) and (l) and make k = 21 and m = 20.

Seeing on cases 1, 2, 3, and 4, the linear classifier learned from average aggregate loss cross some red samples from minor distribution even though the data is separable. The reason is that the samples close to the decision boundary are sacrificed to reduce the total loss over the whole data set. The $\mathrm { A T } _ { k }$ loss selects k largest individual losses which contain many outliers to train the classifier. It leads to the instability of the learned classifier. This phenomenon can be found when we compare all cases. Similarly, the maximum aggregate loss cannot fit this data very well in all cases. This loss is very sensitive to outliers.

In cases $5$ and $6 ,$ the average aggregate loss with individual logistic loss achieves better results than with individual hinge loss. A possible reason is that for correctly classified samples with a margin greater than 1, the penalty caused by hinge loss is 0. However, it is non-zero when using logistic loss. Since many outliers in the blue class, to reduce the average loss, the decision boundary will close to the blue class. Especially, when we compare (i) and (k), it is obvious that average loss can achieve a better result while the number of outliers is increasing.

![](images/57ab789480a6a5bd72bbe87f432927dd8605b7b60460bc7f57c32d18e80665cc.jpg)

Figure 6: Comparison of diferent aggregate losses on 2D synthetic data with 200 samples for binary classification with individual logistic loss (a, c, e, g, i, k) and individual hinge loss (b, d, f, h, j, l). Outliers are shown as × in blue class.

<table><tr><td>Data Sets</td><td>#Classes</td><td>#Samples</td><td>#Features</td><td>Class Ratio</td></tr><tr><td>Monk</td><td>2</td><td>432</td><td>6</td><td>1.12</td></tr><tr><td>Australian</td><td>2</td><td>690</td><td>14</td><td>1.25</td></tr><tr><td>Phoneme</td><td>2</td><td>5,404</td><td>5</td><td>2.41</td></tr><tr><td>Titanic</td><td>2</td><td>2,201</td><td>3</td><td>2.10</td></tr><tr><td>Splice</td><td>2</td><td>3,175</td><td>60</td><td>1.08</td></tr></table>

Table 2: Statistical information of five real data sets.

As we discussed, the hinge loss has less penalty for correctly classified samples than logistic loss. This causes outliers to be more prominent than normal samples while using the individual hinge loss. This result can be verified in the experiment when we compare the individual logistic loss and the individual hinge loss. For example, (i) and (j), (k) and (l), etc. We find the decision boundaries of maximum loss and $\mathrm { A T } _ { k }$ loss are close to outliers in the individual hinge loss scenario because both of them are sensitive to outliers in our cases.

Real data. We use five benchmark data sets from the UCI (Dua and Graf, 2017) and the KEEL (Alcalá-Fdez et al., 2011) data repositories (statistical information of each data set is given in Table 2). For each data set, we first randomly select 50% samples for training, and the remaining 50% samples are randomly split for validation and testing (each contains 25% samples). Hyper-parameters $C , k ,$ and m are selected based on the validation set. Specifically, parameter $C$ is chosen from $\{ 1 0 ^ { 0 } , 1 0 ^ { 1 } , 1 0 ^ { 2 } , 1 0 ^ { 3 } , 1 0 ^ { 4 } , 1 0 ^ { 5 } \}$ , parameter $k \in \{ 1 \} \cup [ 0 . 1 : 0 . 1 : 1 ] n .$ where n is the number of training samples, and parameter $m$ is selected in the range of [1, k). The following results are based on the optimal values of k and m obtained based on the validation set. The random splitting of the training/validation/testing sets is repeated 10 times and the average error rates, as well as the standard derivation on the testing set are reported in Table 3. In (Shalev-Shwartz and Wexler, 2016), the authors introduce slack variables to indicate outliers and propose a robust version of the maximum loss. We term it as Robust\_Max loss and compare it to our method as one of the baselines. As these results show, compared to the maximum, Robust\_Max, average, and $\mathrm { A T } _ { k }$ losses, the AoRR loss achieves the best performance on all five data sets with both individual logistic loss and individual hinge loss. For individual logistic loss, the AoRR loss significantly improves the classification performance on Monk and Phoneme data sets and a slight improvement on data sets Titanic and Splice. More specifically, the performance of maximum aggregate loss is very poor in all cases due to its high sensitivity to outliers or noisy data. The optimization of the Robust\_Max loss uses convex relaxation on the domain of slack variables constraint and using $l _ { 2 }$ norm to replace the $l _ { 1 }$ norm in the constraint. Therefore, it can alleviate the sensitivity to outliers, but cannot exclude their influence. The average aggregate loss is more robust to noise and outliers than the maximum loss and the Robust\_Max loss on all data sets. However, as data distributions may be very complicated, the average loss may sacrifice samples from rare distributions to pursue a lower loss on the whole training set and obtains sub-optimal solutions accordingly. The $\mathrm { A T } _ { k }$ loss is not completely free from the influence of outliers and noisy data either, which can be observed in particular on the Monk data set. On the Monk data set, in comparison to the $\mathrm { A T } _ { k }$ loss, the AoRR loss reduce the misclassification rates by 4.07% for the individual logistic loss and 3.87% for the individual hinge loss, respectively.

<table><tr><td rowspan="2">Data Sets</td><td colspan="5">Logistic Loss</td><td colspan="5">Hinge Loss</td></tr><tr><td>Maximum</td><td>R_Max</td><td>Average</td><td> $AT_k$ </td><td>AoRR</td><td>Maximum</td><td>R_Max</td><td>Average</td><td> $AT_k$ </td><td>AoRR</td></tr><tr><td>Monk</td><td>22.41(2.95)</td><td>21.69(2.62)</td><td>20.46(2.02)</td><td>16.76(2.29)</td><td>12.69(2.34)</td><td>22.04(3.08)</td><td>20.61(3.38)</td><td>18.61(3.16)</td><td>17.04(2.77)</td><td>13.17(2.13)</td></tr><tr><td>Australian</td><td>19.88(6.64)</td><td>17.65(1.3)</td><td>14.27(3.22)</td><td>11.7(2.82)</td><td>11.42(1.01)</td><td>19.82(6.56)</td><td>15.88(1.05)</td><td>14.74(3.10)</td><td>12.51(4.03)</td><td>12.5(1.55)</td></tr><tr><td>Phoneme</td><td>28.67(0.58)</td><td>26.71(1.4)</td><td>25.50(0.88)</td><td>24.17(0.89)</td><td>21.95(0.71)</td><td>28.81(0.62)</td><td>24.21(1.7)</td><td>22.88(1.01)</td><td>22.88(1.01)</td><td>21.95(0.68)</td></tr><tr><td>Titanic</td><td>26.50(3.35)</td><td>24.15(3.12)</td><td>22.77(0.82)</td><td>22.44(0.84)</td><td>21.69(0.99)</td><td>25.45(2.52)</td><td>25.08(1.2)</td><td>22.82(0.74)</td><td>22.02(0.77)</td><td>21.63(1.05)</td></tr><tr><td>Splice</td><td>23.57(1.93)</td><td>23.48(0.76)</td><td>17.25(0.93)</td><td>16.12(0.97)</td><td>15.59(0.9)</td><td>23.40(2.10)</td><td>22.82(2.63)</td><td>16.25(1.12)</td><td>16.23(0.97)</td><td>15.64(0.89)</td></tr></table>

Table 3: Average error rate (%) and standard derivation of diferent aggregate losses combined with individual logistic loss and hinge loss over 5 data sets. The best results are shown in bold. (R\_Max: Robust\_Max)

To further compare with the $\mathrm { A T } _ { k }$ loss, we investigate the influence of m in the AoRR loss. Specifically, we select the best k value based on the $\mathrm { A T } _ { k }$ results and vary m in the range of [1, k −1]. We use the individual logistic loss and plot tendency curves of misclassification error rates w.r.t m in the first row of Figure 7, together with those from the average, maximum and Robust\_Max losses. As these plots show, on all four data sets, there is a clear range of m with better performance than the corresponding $\mathrm { A T } _ { k }$ loss. We observe a trend of decreasing error rates with m increasing. This is because outliers correspond to large individual losses, and excluding them from the training loss helps improve the overall performance of the learned classifier. However, when m becomes large, the classification performance is decreasing, as many samples with small losses are included in the AoRR objective and dominate the training process. Similar results based on the hinge loss can be found in the second row of Figure 7.

![](images/0f85ced2cdaa499c7e24b7b064ad9d11f4cc5b273572f430916bc14b3999e417.jpg)  
Figure 7: Tendency curves of error rate of learning AoRR loss w.r.t. m on four data sets.

## 4.4.2 AoRR for Multi-class Classification

The AoRR aggregate loss can also be extended to multi-class classification. Let $\mathcal { V } = \{ 1 , \cdots , l \}$ where l represents the number of classes. We consider softmax loss as an individual loss. For sample $( x _ { i } , y _ { i } )$ , it is defined as

$$
s _ {i} (\theta) = - \log \Bigl (\frac {\exp (f _ {y _ {i}} (x _ {i} ; \theta))}{\sum_ {j = 1} ^ {l} \exp (f _ {j} (x _ {i} ; \theta))} \Bigr),
$$

where $f _ { j } ( x _ { i } ; \theta )$ is the prediction of j-th class, and $y _ { i } \in \mathcal { V }$ is the ground-truth label of $x _ { i }$

We use this multi-class classification task to verify the efectiveness of Algorithm 2. We conduct experiments on the MNIST data set (LeCun et al., 1998), which contains 60, 000 training samples and 10, 000 testing samples that are images of handwritten digits. To create a validation set, We randomly extract 10, 000 samples from training samples. Therefore, the remaining training data size is 50, 000. To simulate outliers caused by errors that occurred when labeling the data in the training set, as in the work of Wang et al. (2019), we use the symmetric (uniform) noise creation method to randomly change labels of the training samples to one of the other class labels with a given proportion. The label is chosen at random with probability $p = 0 . 2 , 0 . 3 , 0 . 4$ . We use the average loss and $\mathrm { A T } _ { k }$ loss as baselines. For $\mathrm { A T } _ { k }$ loss, we also apply the same “warm-up” procedure and the same operation 2 to determine the hyper-parameter k. We extract the mean value plus one standard deviation of all individual losses from the validation set as operation 1’s result. For operation 2, we use the mean value minus two standard deviations of all individual losses from the validation set. After multiple training epochs in the “warm-up” procedure, if the validation loss does not decrease, we stop the “warm-up” procedure. The result of this procedure can also be regarded as the result by using the average loss. After “warm-up”, we do the training for $\mathrm { A T } _ { k }$ loss and AoRR loss.

<table><tr><td>Methods\Noise Level</td><td>0.2</td><td>0.3</td><td>0.4</td></tr><tr><td>Average</td><td>89.69 (0.08)</td><td>88.71 (0.10)</td><td>87.77 (0.02)</td></tr><tr><td> $AT_k$ </td><td>89.71 (0.07)</td><td>88.73 (0.11)</td><td>87.62 (0.04)</td></tr><tr><td>AoRR</td><td>92.42 (0.03)</td><td>92.26 (0.07)</td><td>91.87 (0.11)</td></tr></table>

Table 4: Testing accuracy (%) of diferent aggregate losses combined with individual logistic loss on MNIST with diferent levels of symmetric noisy labels. The average accuracy and standard deviation of 5 random runs are reported and the best results are shown in bold.

<table><tr><td>m\Noise Level</td><td>0.2</td><td>0.3</td><td>0.4</td></tr><tr><td>Ground Truth</td><td>10000</td><td>15000</td><td>20000</td></tr><tr><td>Estimation</td><td>11722 (23)</td><td>16431 (17)</td><td>21026 (24)</td></tr></table>

Table 5: The estimation of hyper-parameter m. The average and standard deviation of 5 random runs are reported.

All models randomly run 5 times. The performance of testing accuracy is reported in Table 4. From Table 4, we can find that AoRR outperforms all other two baseline methods for all diferent noise levels. Specifically, our AoRR method obtains 2.71% improvement on $p = 0 . 2 , 3 . 5 3 \%$ improvement on $p = 0 . 3$ , and 4.25% improvement on $p = 0 . 4$ when comparing to $\mathrm { A T } _ { k }$ . It is obvious that Algorithm 2 works successfully and efectively. In addition, we also compare the estimated m value based on $\hat { \lambda }$ to the optimal m because we know the number of noisy data in the training set according to the noise level. From Table $5 ,$ we can find all estimated values are close to the ground truth values. It should be noted that we can modify operation 2 to slightly increase the return value $\hat { \lambda }$ so that the diference between the estimated value and the ground truth will be smaller.

## 5. TKML Loss for Multi-label Learning

We use SoRR to construct the individual loss for multi-label/multi-class classification, where a sample x can be associated with a set of labels $\emptyset \neq Y \subset \{ 1 , \cdots , l \}$ . Our goal is to construct a linear predictor $f _ { \Theta } ( x ) = \Theta ^ { T } x$ with $\Theta = \left( \theta _ { 1 } , \cdots , \theta _ { l } \right)$ . The final classifier outputs labels for x with the top k $( 1 \leq k < l )$ prediction scores, i.e., $\theta _ { [ 1 ] } ^ { \top } x \ge \theta _ { [ 2 ] } ^ { \top } x \ge \dots \ge \theta _ { [ k ] } ^ { \top } x$ . In training, the classifier is expected to include as many true labels as possible in the top k outputs. This can be evaluated by the “margin”, i.e., the diference between the (k + 1)-th largest score of all the labels, $\theta _ { [ k + 1 ] } ^ { \top } x$ and the lowest prediction score of all the ground-truth labels, $\mathrm { m i n } _ { y \in Y } \theta _ { y } ^ { \top } x$

<table><tr><td>Data Sets</td><td>#Samples</td><td>#Features</td><td>#Labels</td><td> $\bar{c}$ </td></tr><tr><td>Emotions</td><td>593</td><td>72</td><td>6</td><td>1.81</td></tr><tr><td>Scene</td><td>2,407</td><td>294</td><td>6</td><td>1.06</td></tr><tr><td>Yeast</td><td>2,417</td><td>103</td><td>14</td><td>4.22</td></tr></table>

Table 6: Statistical information of each data set for multi-label learning, where c represents the average number of positive labels per instance.

If we have $\begin{array} { r } { \theta _ { [ k + 1 ] } ^ { \top } x < \operatorname* { m i n } _ { y \in Y } \theta _ { y } ^ { \top } x } \end{array}$ , then all ground-truth labels have prediction scores ranked in the top k positions. If this is not the case, then at least one ground-truth label has a prediction score not ranked in the top k. This induces the following metric for multi-label classification as $\begin{array} { r } { \mathbb { I } _ { [ \theta _ { [ k + 1 ] } ^ { \top } x \ge \operatorname* { m i n } _ { y \in Y } \theta _ { y } ^ { \top } x ] } . } \end{array}$ . Replacing the indicator function with the hinge function and let $S ( \theta ) = \{ s _ { j } ( \theta ) \} _ { j = 1 } ^ { l }$ , where $\begin{array} { r } { s _ { j } ( \theta ) = \left[ 1 + \theta _ { j } ^ { \top } x - \mathrm { m i n } _ { y \in Y } \theta _ { y } ^ { \top } x \right] _ { + } } \end{array}$ , we obtain a continuous surrogate loss, as $\psi _ { k , k + 1 } ( S ( \theta ) ) = s _ { [ k + 1 ] } ( \theta )$ . We term this loss as the top-k multi-label (TKML) loss. According to the existing works from Crammer and Singer (2003) and Lapin et al. (2017), the conventional multi-label loss is defined as $\begin{array} { r } { \left[ 1 + \operatorname* { m a x } _ { y \not \in Y } \theta _ { y } ^ { \top } x - \operatorname* { m i n } _ { y \in Y } \theta _ { y } ^ { \top } x \right] _ { + } } \end{array}$ When $k = | Y |$ , we have the following proposition and its proof can be found in Appendix A.6,

Proposition 6 The TKML loss is a lower-bound to the conventional multi-label loss (Crammer and Singer, 2003), as $\begin{array} { r } { \left[ 1 + \operatorname* { m a x } _ { y \notin Y } \theta _ { y } ^ { \top } x - \operatorname* { m i n } _ { y \in Y } \theta _ { y } ^ { \top } x \right] _ { + } \geq \psi _ { | Y | , | Y | + 1 } ( S ( \theta ) ) } \end{array}$

The TKML loss generalizes the conventional multi-class loss $( | Y | = k = 1 )$ and the top-k consistent k-guesses multi-class classification (Yang and Koyejo, 2020) $( 1 = | Y | \leq k < l )$ . A similar learning objective is proposed in Lapin et al. (2015) corresponds to $s _ { [ k ] } ( \theta )$ , however, as proved in Yang and Koyejo (2020), it is not multi-class top-k consistent. Another work in Chang et al. (2017) proposes a robust top-k multi-class SVM based on the convex surrogate of $s _ { [ k ] } ( \theta )$ to address the outliers by using a hyperparameter to cap the values of the individual losses. This approach is diferent from ours since we directly address the original top-k multi-class SVM problem using our TKML loss without introducing its convex surrogate and it is consistent. For a set of training data $( x _ { 1 } , Y _ { 1 } ) , \cdot \cdot \cdot , ( x _ { n } , Y _ { n } )$ , if we denote $\psi _ { k , k + 1 } ( S ( x , Y ; \Theta ) ) = \psi _ { k , k + 1 } ( S ( \theta ) )$ , the data loss on TKML can be written as $\begin{array} { r } { \mathcal { L } _ { \mathtt { T K M L } } ( \Theta ) = \frac { 1 } { n } \sum _ { i = 1 } ^ { n } \psi _ { k , k + 1 } ( S ( x _ { i } , Y _ { i } ; \Theta ) ) } \end{array}$ , which can be optimized using the Algorithm 1.

## 5.1 Experiments

We use the same $\ell _ { 2 }$ regularizer, $\begin{array} { r } { R ( \theta ) = \frac { 1 } { 2 C } | | \theta | | _ { 2 } ^ { 2 } } \end{array}$ and cross-validate hyper-parameter C in the range $1 0 ^ { 0 }$ to $1 0 ^ { 5 }$ , extending it when the optimal value appears.

Multi-label classification. We use three benchmark data sets (Emotions, Scene, and Yeast) from the KEEL data repository to verify the efectiveness of our TKML loss. More details about these three data sets can be found in Table 6. For comparison, we compare TKML with logistic regression (LR) model (i.e. minimize a surrogate hamming loss (Zhang and Zhou, 2013)), and a ranking based method (LSEP, Li et al. (2017a)). For these two baseline methods, we use a sigmoid operator on the linear predictor as $f _ { \Theta } ( x ) = 1 / ( 1 + \exp ( - \Theta ^ { T } x ) )$ Since TKML is based on the value of k, we use five diferent k values $( k \in \{ 1 , 2 , 3 , 4 , 5 \} )$ to evaluate the performance. For each data set, we randomly partition it to 50%/25%/25% samples for training/validation/testing, respectively. This random partition is repeated 10 times, and the average performance on testing data is reported in Table 7. We use a metric (top k multi-label accuracy) $\textstyle { \frac { 1 } { n } } \sum _ { i = 1 } ^ { n } \mathbb { I } _ { [ ( Z _ { i } \subseteq Y _ { i } ) \lor ( Y _ { i } \subseteq Z _ { i } ) ] }$ to evaluate the performance, where n is the size of the sample set. For instance, $( x _ { i } , Y _ { i } )$ with $Y _ { i }$ be its ground-truth set, $f _ { \Theta } ( x _ { i } ) \in \mathbb { R } ^ { l }$ be its predicted scores, and $Z _ { i }$ be a set of top k predictions according to $f _ { \Theta } ( x _ { i } )$ . This metric reflects the performance of a classifier can get as many true labels as possible in the top k range. More settings can be found in Appendix B.3.

<table><tr><td>Data Sets</td><td>Methods</td><td>k=1</td><td>k=2</td><td>k=3</td><td>k=4</td><td>k=5</td></tr><tr><td rowspan="3">Emotions</td><td>LR</td><td>73.54(3.98)</td><td>57.48(3.35)</td><td>73.20(4.69)</td><td>86.60(3.02)</td><td>96.46(1.71)</td></tr><tr><td>LSEP</td><td>72.18(4.56)</td><td>55.85(3.37)</td><td>72.18(3.74)</td><td>85.58(2.92)</td><td>95.85(1.07)</td></tr><tr><td>TKML</td><td>76.80(2.66)</td><td>62.11(2.85)</td><td>77.62(2.81)</td><td>90.14(2.22)</td><td>96.94(0.63)</td></tr><tr><td rowspan="3">Scene</td><td>LR</td><td>73.2(0.57)</td><td>85.31(0.47)</td><td>94.79(0.79)</td><td>97.88(0.63)</td><td>99.7(0.30)</td></tr><tr><td>LSEP</td><td>69.22(3.43)</td><td>83.83(4.83)</td><td>92.46(4.78)</td><td>96.35(3.5)</td><td>98.56(1.94)</td></tr><tr><td>TKML</td><td>74.06(0.45)</td><td>85.36(0.79)</td><td>88.92(1.47)</td><td>91.94(0.87)</td><td>95.01(0.61)</td></tr><tr><td rowspan="3">Yeast</td><td>LR</td><td>77.57(0.91)</td><td>70.59(1.16)</td><td>52.65(1.23)</td><td>43.26(1.16)</td><td>43.49(1.33)</td></tr><tr><td>LSEP</td><td>75.5(1.03)</td><td>66.84(2.9)</td><td>49.72(1.26)</td><td>41.90(1.91)</td><td>43.01(1.02)</td></tr><tr><td>TKML</td><td>76.94(0.49)</td><td>67.19(2.79)</td><td>45.41(0.71)</td><td>43.47(1.06)</td><td>44.69(1.14)</td></tr></table>

Table 7: Top k multi-label accuracy with its standard derivation (%) on three data sets. The best performance is shown in bold.

<table><tr><td>Methods\Data Sets</td><td>Emotions</td><td>Scene</td><td>Yeast</td></tr><tr><td>LR</td><td>74.85</td><td>71.6</td><td>73.56</td></tr><tr><td>LSEP</td><td>82.66</td><td>85.43</td><td>74.26</td></tr><tr><td>TKML</td><td>84.82</td><td>86.38</td><td>74.32</td></tr></table>

Table 8: AP (%) results on three data sets. The best performance is shown in bold.

From Table $^ { 7 , }$ we note that the TKML loss in general improves the performance on the Emotions data set for all diferent k values. These results illustrate the efectiveness of the TKML loss. More specifically, our TKML method obtains 4.63% improvement on k = 2 and 4.42% improvement on $k = 3$ when comparing to LR. This rate of improvement becomes higher (6.26% improvement on $k = 2 )$ when compare to LSEP. We also compare the performance of the method based on the TKML loss on diferent k values. If we choose the value of k close to the number of the ground-truth labels, the corresponding classification method outperforms the two baseline methods. For example, in the case of the Emotions data set, the average number of positive labels per instance is 1.81, and our method based on the TKML loss achieves the best performance for $k = 1 , 2 .$ . As another example, the average number of true labels for the Yeast data set is 4.22, so the method based on the TKML loss achieves the best performance for $k = 4 , 5$

We also adopt a widely used multi-label learning metric named average precision (AP) for performance evaluation. It is calculated by (Zhang and Zhou, 2013)

$$
\mathrm{AP} = \frac {1}{n} \sum_ {i = 1} ^ {n} \frac {1}{| Y _ {i} |} \sum_ {j \in Y _ {i}} \frac {| \{\tau \in Y _ {i} | r a n k _ {f} (x _ {i} , \tau) <   r a n k _ {f} (x _ {i} , j) \} |}{r a n k _ {f} (x _ {i} , j)},
$$

where $r a n k _ { f } ( x _ { i } , j )$ returns the rank of $f _ { j } ( x _ { i } )$ in descending according to $\{ f _ { a } ( x _ { i } ) \} _ { a = 1 } ^ { l }$ . From Table 8, we can find our TKML method outperforms the other two baseline approaches on all data sets. For the Emotions data set, the AP score of TKML is 2.16% higher than the LSEP method and near 10% higher than the LR. The performance is also slightly improved on Scene and Yeast data sets. These results demonstrate the efectiveness of our TKML method.

<table><tr><td>Noise Level</td><td>Methods</td><td>Top-1 Acc.</td><td>Top-2 Acc.</td><td>Top-3 Acc.</td><td>Top-4 Acc.</td><td>Top-5 Acc.</td></tr><tr><td rowspan="2">0.2</td><td> $SVM_{\alpha}$ </td><td>78.33(0.18)</td><td>90.66(0.29)</td><td>95.12(0.2)</td><td>97.28(0.09)</td><td>98.49(0.1)</td></tr><tr><td>TKML</td><td>83.06(0.94)</td><td>94.17(0.19)</td><td>97.24(0.13)</td><td>98.47(0.05)</td><td>99.22(0.01)</td></tr><tr><td rowspan="2">0.3</td><td> $SVM_{\alpha}$ </td><td>74.65(0.17)</td><td>89.31(0.24)</td><td>94.14(0.2)</td><td>96.73(0.23)</td><td>98.19(0.07)</td></tr><tr><td>TKML</td><td>80.13(1.24)</td><td>93.37(0.1)</td><td>96.81(0.22)</td><td>98.21(0.05)</td><td>99.08(0.05)</td></tr><tr><td rowspan="2">0.4</td><td> $SVM_{\alpha}$ </td><td>68.32(0.32)</td><td>86.71(0.42)</td><td>93.14(0.49)</td><td>96.16(0.32)</td><td>97.84(0.18)</td></tr><tr><td>TKML</td><td>75(1.15)</td><td>92.41(0.14)</td><td>96.2(0.13)</td><td>97.95(0.1)</td><td>98.89(0.04)</td></tr></table>

Table 9: Testing accuracy (%) of two methods on MNIST with diferent levels of asymmetric noisy labels. The average accuracy and standard deviation of 5 random runs are reported and the best results are shown in bold. (Acc.: Accuracy)

![](images/0c10d3b952b211b74d04569b865bf0bbda6d905c96527984fdc7cf818b019e69.jpg)

![](images/6c75007719f20614404ca2d6f9f6429fa20da1a35c0c9f4104e05cc3a26490a5.jpg)

![](images/1a5ea80eccd17ffafff2d1380dd36aaf808aaef9228ec7eeb80583d007db6c60.jpg)  
Figure 8: The class-wise error rates of two methods with diferent noise level data.

Robustness analysis. As a special case of AoRR, the TKML loss exhibit similar robustness with regards to outliers, which can be elucidated with experiments in the multi-class setting $( i . e . , k { = } 1 \mathrm { a n d } | Y | { = } 1 )$ . We conduct experiments on the MNIST data set (LeCun et al., 1998), which contains 60, 000 training samples and 10, 000 testing samples. To simulate outliers caused by errors that occurred when labeling the data, as in the work of Wang et al. (2019), we use the asymmetric (class-dependent) noise creation method (Patrini et al., 2017; Zhang and Sabuncu, 2018) to randomly change labels of the training data $( 2 {  } 7 , 3 {  } 8 , 5 {  } 6 .$ , and 7→1) with a given proportion. The flipping label is chosen at random with probability $p = 0 . 2 , 0 . 3 , 0 . 4$ . As a baseline, we use the top-k multi-class SVM (SVM<sub>α</sub>) (Lapin et al., 2015). The performance is evaluated with the top 1, top 2, · · · , top 5 accuracy on the testing samples. More details about the settings can be found in Appendix B.4.

From Table 9, it is clear that our method TKML consistently outperforms the baseline $\mathrm { S V M } _ { \alpha }$ among all top 1-5 accuracies. The gained improvement in performance is getting more significant as the level of noise increases. Since our flipping method only works between two diferent labels, we expected the performance of TKML has some significant improvements on top 1 and 2 accuracies. Indeed, this expectation is correctly verified as Table 9 clearly indicates that the performance of our method is better than $\mathrm { S V M } _ { \alpha }$ by nearly 7% accuracy (see Top-1 accuracy in the noise level 0.4). These results also demonstrate our optimization framework works well.

To evaluate our method is better than SVM<sub>α</sub> especially on the flipped class, we plot the class-wise error rate w.r.t diferent noise level data. As seen in Figure 8, our method TKML outperforms $\mathrm { S V M } _ { \alpha }$ on the flipping classes such as 2 and 3, especially in class 5. As the noise level increases, the performance gap becomes more pronounced. For flipping class 7, the performance in this class is increased when the noise level increases from 0.3 to 0.4. TKML also gets good performance in class 6 when the noise level is 0.2 and 0.3.

## 6. Combination of AoRR and TKML

The TKML individual loss applies to the multi-label learning problem at the label level. However, it may also be the case that the training samples for a multi-label learning problem include outliers. It is thus a natural idea to combine the TKML individual loss at the label level and the AoRR aggregate loss at the sample level to construct a more robust learning objective.

To the best of our knowledge, considering robustness for multi-label learning at both the label and the sample level has not been extensively studied in the literature. The most relevant work is Rawat et al. (2020), which considers robustness at both levels for multi-class classification (i.e., out of multiple class labels, only one is the true label). The doubly-stochastic mining method in Rawat et al. (2020) uses the $\mathrm { A T } _ { k }$ aggregate loss on the sample level and top-k multi-class SVM loss on the label level. As we discussed before, $\mathrm { A T } _ { k }$ loss cannot eliminate the outliers and top-k multi-class SVM does not satisfy the multi-class top-k consistent. Furthermore, the proposed method from their work cannot deal with the top-k multi-label learning problem where there are multiple true labels for each instance.

We consider a learning objective that combines AoRR and TKML for multi-label learning. Theorem 2 tells us that we can get the same optimal solution of SoRR problem (equation (1)) by solving the problem of equation (4). However, it is hard to deal with the cardinality constraint $\| q \| _ { 0 } = n - m$ in equation (4). Thus, we need to reformulate the equation (4) in order to remove the cardinality constraint. Before we introduce the new formulation, we provide an useful Lemma as follows,

Lemma $\begin{array} { r } { 7 \ \sum _ { i = m + 1 } ^ { n } s _ { [ i ] } } \end{array}$ is a concave function of the elements of S. Furthermore, we have $\begin{array} { r } { \sum _ { i = m + 1 } ^ { n } s _ { [ i ] } = \operatorname* { m a x } _ { \lambda \in \mathbb { R } } \bigg \{ ( n - m ) \lambda - \sum _ { i = 1 } ^ { n } [ \lambda - s _ { i } ] _ { + } \bigg \} } \end{array}$ , of which $s _ { [ m ] }$ is an optimum solution.

Proof can be found in Appendix A.7. According to equation (4), we can substitute the optimal $q ^ { * }$ to the constraint. Using Lemma $^ { 7 , }$ we get

$$
\begin{array}{c} \min _ {\lambda} (k - m) \lambda + \sum_ {i = m + 1} ^ {n} [ [ s (\theta) - \lambda ] _ {+} ] _ {[ i ]} \\ = \min _ {\lambda} (k - m) \lambda + \max _ {\hat {\lambda}} \Bigl \{(n - m) \hat {\lambda} - \sum_ {i = 1} ^ {n} [ \hat {\lambda} - [ s _ {i} (\theta) - \lambda ] _ {+} ] _ {+} \Bigr \}. \end{array}
$$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3: Combination of AoRR and TKML
1 Initialization:  $\theta^{(0)}$ ,  $\lambda^{(0)}$ ,  $\hat{\lambda}^{(0)}$ ,  $\eta_{t}$ ,  $k'$ , k, and m
2 for  $t = 0, 1, \ldots$  do
3 Compute  $s_{i}(\theta^{(t)}) = [1 + \theta_{[k'+1]}^{(t)\top} x_{i} - \min_{y \in Y_{i}} \theta_{y}^{(t)\top} x_{i}]_{+}, \forall i \in \{1, \cdots, n\}$ 
4 Update parameters  $\theta^{(t+1)}$ ,  $\lambda^{(t+1)}$ , and  $\hat{\lambda}^{(t+1)}$  with equation (12)
5 end
</div>

Finally, we obtain a new objective function that the combination of TKML and AoRR as follows,

$$
\begin{array}{r l r} & & {\mathcal {L} _ {\mathrm{TKML-AoRR}} (S (\theta)) = \frac {\psi_ {m , k} (S (\theta))}{k - m} = \underset {\lambda} {\min} \underset {\hat {\lambda}} {\max} \lambda + \frac {n - m}{k - m} \hat {\lambda} - \frac {1}{k - m} \sum_ {i = 1} ^ {n} [ \hat {\lambda} - [ s _ {i} (\theta) - \lambda ] _ {+} ] _ {+}} \\ & & {= \frac {1}{k - m} \underset {\lambda} {\min} \underset {\hat {\lambda}} {\max} (k - m) \lambda - m \hat {\lambda} + \sum_ {i = 1} ^ {n} \hat {\lambda} - [ \hat {\lambda} - [ s _ {i} (\theta) - \lambda ] _ {+} ] _ {+}.} \end{array}\tag{11}
$$

For $s _ { i } ( \theta )$ , we use TKML individual loss to replace it. So we have $s _ { i } ( \theta ) = [ 1 + \theta _ { [ k ^ { \prime } + 1 ] } ^ { \top } x _ { i } -$ $\mathrm { m i n } _ { y \in Y _ { i } } \theta _ { y } ^ { \top } x _ { i } ] _ { + }$ , where we use $k ^ { \prime }$ in the label level to distinguish k in the sample level. Then, we develop a heuristic algorithm for learning ${ \mathcal { L } } _ { \mathrm { T K M L - A o R R } } ( S ( \theta ) )$ . For a set of training data $\{ ( x _ { i } , Y _ { i } ) \} _ { i = 1 } ^ { n }$ , where sample $x _ { i }$ is associated with a set of labels $\emptyset \neq Y _ { i } \subset \{ 1 , \cdots , l \}$ . The algorithm iteratively updates the parameters $\theta , \lambda$ and $\hat { \lambda }$ based on the $\mathcal { L } _ { \mathrm { T K M I } }$ −AoRR $( S ( \theta ) )$ over training samples with the following steps:

$$
\begin{array}{r l} & {\theta^ {(t + 1)} = \theta^ {(t)} - \eta_ {l} \Big (\frac {1}{k - m} \sum_ {i = 1} ^ {n} \partial s _ {i} (\theta^ {(t)}) \cdot \mathbb {I} _ {[ \hat {\lambda} ^ {(t)} > [ s _ {i} (\theta^ {(t)}) - \lambda^ {(t)} ] _ {+} ]} \cdot \mathbb {I} _ {[ s _ {i} (\theta^ {(t)}) > \lambda^ {(t)} ]} \Big),} \\ & {\lambda^ {(t + 1)} = \lambda^ {(t)} - \eta_ {l} \Big (1 - \frac {1}{k - m} \sum_ {i = 1} ^ {n} \mathbb {I} _ {[ \hat {\lambda} ^ {(t)} > [ s _ {i} (\theta^ {(t)}) - \lambda^ {(t)} ] _ {+} ]} \cdot \mathbb {I} _ {[ s _ {i} (\theta^ {(t)}) > \lambda^ {(t)} ]} \Big),} \\ & {\hat {\lambda} ^ {(t + 1)} = \hat {\lambda} ^ {(t)} + \eta_ {l} \Big (\frac {n - m}{k - m} - \frac {1}{k - m} \sum_ {i = 1} ^ {n} \mathbb {I} _ {[ \hat {\lambda} ^ {(t)} > [ s _ {i} (\theta^ {(t)}) - \lambda^ {(t)} ] _ {+} ]} \Big),} \end{array}\tag{12}
$$

where $0 \leq m < k \leq n , 1 \leq k ^ { \prime } < l ,$ η<sub>l</sub> is the step size, and $\partial s _ { i } ( \theta ^ { ( t ) } )$ denotes the (sub)gradient of $s _ { i } ( \theta ^ { ( t ) } )$ with respect to $\boldsymbol { \theta } ^ { ( t ) }$ . Algorithm 3 describes the pseudo-code of the proposed heuristic algorithm. For a given loop size |t| and training sample size $n ,$ the time complexity of Algorithm 3 is $O ( | t | \cdot n )$

It should be mentioned that the mini-batch SGD method can be applied to Algorithm 3 when the training sample size is large. We can also use more complex non-linear models such as deep neural networks to replace the linear model in the TKML individual loss $s _ { i } ( \theta )$ Furthermore, Algorithm 3 with mini-batch B setting will become a general algorithm. It can be generalized to other types of existing algorithms for multi-class learning with setting diferent hyper-parameter values of $k ^ { \prime } , k ,$ and $m$ . For example, if $| Y _ { i } | = 1 = k ^ { \prime } , \forall i .$ , and $m = 0$ , it becomes OSGD algorithm (Kawaguchi and Lu, 2020), which updates the model parameter based on the average loss over the top-k largest individual losses in the mini-batch.

<table><tr><td>Noise Level</td><td>Methods</td><td> $k' = 1$ </td><td> $k' = 2$ </td><td> $k' = 3$ </td><td> $k' = 4$ </td><td> $k' = 5$ </td></tr><tr><td rowspan="3">0</td><td>TKML-Average</td><td>73.78 (1.59)</td><td>73.64 (1.53)</td><td>43.90 (2.99)</td><td>34.94 (3.78)</td><td>43.55 (0.96)</td></tr><tr><td> $TKML-AT_k$ </td><td>74.38 (1.56)</td><td>73.84 (1.25)</td><td>49.44 (1.76)</td><td>43.16 (2.16)</td><td>45.99 (2.13)</td></tr><tr><td>TKML-AoRR</td><td>74.94 (1.82)</td><td>73.88 (1.26)</td><td>50.25 (1.39)</td><td>45.93 (2.15)</td><td>46.13 (1.77)</td></tr><tr><td rowspan="3">0.1</td><td>TKML-Average</td><td>73.08 (1.55)</td><td>73.24 (1.52)</td><td>43.80 (4.78)</td><td>34.22 (4.72)</td><td>43.48 (0.65)</td></tr><tr><td> $TKML-AT_k$ </td><td>74.28 (1.36)</td><td>73.44 (1.34)</td><td>49.26 (0.80)</td><td>41.12 (1.91)</td><td>45.72 (1.97)</td></tr><tr><td>TKML-AoRR</td><td>74.55 (1.62)</td><td>73.68 (1.52)</td><td>50.19 (0.81)</td><td>45.52 (2.35)</td><td>46.05 (2.20)</td></tr><tr><td rowspan="3">0.2</td><td>TKML-Average</td><td>72.71 (3.68)</td><td>72.64 (0.88)</td><td>43.38 (2.00)</td><td>33.96 (4.31)</td><td>43.30 (1.09)</td></tr><tr><td> $TKML-AT_k$ </td><td>73.88 (1.03)</td><td>73.24 (1.25)</td><td>49.15 (1.45)</td><td>39.24 (1.15)</td><td>45.62 (1.70)</td></tr><tr><td>TKML-AoRR</td><td>74.36 (1.61)</td><td>73.50 (1.38)</td><td>49.73 (1.41)</td><td>45.48 (2.35)</td><td>46.00 (1.59)</td></tr><tr><td rowspan="3">0.3</td><td>TKML-Average</td><td>71.32 (3.86)</td><td>71.94 (1.06)</td><td>43.16 (2.78)</td><td>33.78 (3.03)</td><td>41.44 (4.09)</td></tr><tr><td> $TKML-AT_k$ </td><td>73.78 (1.09)</td><td>73.04 (1.21)</td><td>47.48 (1.90)</td><td>36.90 (1.91)</td><td>45.06 (2.01)</td></tr><tr><td>TKML-AoRR</td><td>74.31 (1.40)</td><td>73.48 (1.36)</td><td>49.69 (1.07)</td><td>44.71 (2.11)</td><td>45.79 (1.98)</td></tr></table>

Table 10: Top k multi-label accuracy and its standard derivation (%) on the Yeast data set with diferent levels of symmetric noisy labels. The average best performance is shown in bold based on 10 random runs.

$\mathrm { I f ~ } | Y _ { i } | = 1 = k ^ { \prime } ,$ ∀i, $m = | \boldsymbol { B } | - k$ , and $k = | \boldsymbol { B } |$ , it becomes ITLM algorithm (Shen and Sanghavi, 2019), which selects the bottom-k smallest individual losses in each mini-batch and then uses them to update the model parameter. If $| Y _ { i } | = 1 = k ^ { \prime } , \forall i , m = | B | - 1$ , and $k = | \boldsymbol { B } |$ , our algorithm is MKL-SGD (Shah et al., 2020). This method selects a sample with the smallest individual loss in the mini-batch set, then use the gradient of this individual loss to update the model parameters. In addition, if $| Y _ { i } | = 1 , \forall i ,$ , and $m = 0$ , our Algorithm is similar to the doubly-stochastic mining method in Rawat et al. (2020).

## 6.1 Experiments

The Yeast data set is selected to show the eficiency of our loss function equation (11) and Algorithm 3. We randomly split Yeast data into two parts, which are 80% samples for training and 20% samples for testing. This random partition is repeated 10 times. The average performances on testing data are reported and they are based on the optimal values of hyper-parameters. To compare the combined TKML and AoRR method (TKML-AoRR), we consider other two combination methods, which use the average (TKML-Average) and the $\mathrm { A T } _ { k }$ $\left( \mathrm { T K M L - A T } _ { k } \right)$ aggregate loss on the sample level for top-k multi-label learning. Assuming the training data size is n, the hyper-parameter k is selected in the range of [1, n) for TKML $\mathrm { A T } _ { k }$ method. After finding the optimal value k for $\mathrm { T K M L - A T } _ { k }$ method, we apply it to our TKML-AoRR method. Then hyper-parameter m in our method is selected in the range of [1, k). Note that we can also apply the method from Section 4.3 to determine the hyper-parameters k and m in practice. However, we use this grid search method to show the performance changes of our method as the hyper-parameters change in the experiment. On the other hand, since we use AoRR aggregate method, we should expect that our method also exhibits robustness with regards to outliers. Therefore, we introduce noise data to the training set of Yeast. Following Li et al. (2020b), we generate symmetric label noise. Specifically, we randomly choose training samples with probability $p = 0 . 1 , 0 . 2 , 0 . 3$ and change each of their labels to another random label. We use top-k multi-label accuracy as a metric to evaluate the performance as we have applied in Section 5.1. All results are shown in the Table 10. More details about the settings can be found in Appendix B.5.

![](images/1130cb47275255952e238ae789128d577372daface1da97974e1dec345717572.jpg)  
Figure 9: Tendency curves of TKML accuracy of learning TKML-AoRR loss w.r.t. m on four noise level settings $( p = 0 . 0 , 0 . 1 , 0 . 2 , 0 . 3 )$ . The left figures are based on the $k ^ { \prime } = 1$ setting. The middle figures are based on the $k ^ { \prime } = 3$ setting. The right figures are based on the $k ^ { \prime } = 5$ setting.

From Table 10, we can find that our TKML-AoRR method outperforms the other two methods in all noise levels and all $k ^ { \prime }$ values. Especially, there is more than 10% improvement when compared with TKML-Average method in $k ^ { \prime } = 4$ . The results show that our algorithm works eficiently. As the noise level increases, the top-k multi-label accuracy of the same method is decreasing. The performance declines slowly with the increase of noise level while using our method. For example, from noise level 0 to noise level 0.3, the performance only has less than $1 \%$ diference in $k ^ { \prime } = 1 , 2 , 3 , 5$ . For $k ^ { \prime } = 4 ,$ , the gap is 1.22% from noise level 0 to 0.3 using our method. However, the performance is decreased near 10% for the $\mathrm { T K M L - A T } _ { k }$ method. As we mentioned before, the performance of the $\mathrm { T K M L } { \cdot } \mathrm { A T } _ { k }$ method is better than the TKML-Average method. But it cannot eliminate the influence of the outliers. Therefore, the performance can be further improved by using our method. To see how the performance change with setting diferent values of the hyper-parameter $m ,$ we show the tendency curves of TKML accuracy for the learning TKML-AoRR loss w.r.t. m in Figure 9. From Figure 9, we can find there is a clear range of m with better performance than the corresponding TKML-Average and $\mathrm { T K M L - A T } _ { k }$ loss.

## 7. Conclusion

In this work, we have introduced a general approach to form learning objectives, $i . e .$ , the sum of ranked range, which corresponds to the sum of a consecutive sequence of sorted values of a set of real numbers. We show that SoRR can be expressed as the diference between two convex problems and optimized with the diference-of-convex algorithm (DCA). We also show that SoRR can be reformed as a bilevel optimization problem.

We explored two applications in machine learning of the minimization of the SoRR framework, namely the AoRR aggregate loss for binary/multi-class classification at the data sample level and the TKML individual loss for multi-label/multi-class classification at the data label level. For the AoRR aggregate loss, we discussed its connection with CVaRs and explore its generalization bound. We also proposed a method for learning hyper-parameters, which can make AoRR works more eficiently in practice. Furthermore, we combine the AoRR aggregate loss at the sample level and the TKML individual loss at the label level to enhance the robustness in the top-k multi-label learning. A heuristic algorithm is proposed to optimize the combined loss. We conducted extensive experiments to show the efectiveness of the proposed frameworks on achieving superior generalization and robust performance on synthetic and real data sets.

There are several potential limitations to our proposed methods. First, Algorithm 1 and Algorithm 2 are based on the DCA. We use a stochastic sub-gradient method to iterative optimize the model parameter in the inner loop, which may introduce bias about the optimal value of the learned model parameters θ. Furthermore, using the inner loop to find the optimal solution in each outer loop may introduce a high time complexity. As we analyzed the time complexity of Algorithm 1 and Algorithm 2, both of them are increased by increasing the size of the inner loop size |l|. Second, in Algorithm 2, we need a clean validation set to learn the hyper-parameters k and m. However, it is very hard to guarantee the extracted validation set from the training set is clean. If it is not clean, the learned result through Algorithm 2 may not reliable. Third, although experiments show that Algorithm 3 is successful and efective, its theoretical convergence has not been studied. The learning objective (11) is a minimax optimization problem, which is worth exploring its convergence property and optimization error.

For future works, we will try to address the above-mentioned limitations of our proposed methods. We also plan to further study the statistical consistency of TKML loss for multi-label learning and the extension of our SoRR framework with deep neural network structures. Testing the vulnerability of the deep learning models that incorporate the TKML loss is also worthy to explore. We have done such works in Hu et al. (2021). However, how to protect TKML based models against adversarial attacks is important for future work.

## Acknowledgments

This work is supported by NSF research grants (IIS-1816227, IIS-2008532, DMS-2110836, and IIS-2110546) as well as an Army Research Ofice grant (agreement number: W911 NF-18-1-0297).

## Appendix A. Proofs

## A.1 Proof of Theorem 1

Proof To prove Theorem 1, we need the following lemma.

Lemma A.1 (Ogryczak and Tamir (2003)) . $\phi _ { k } ( S )$ is a convex function of the elements of S. Furthermore, for any $i \in [ 1 , n ]$ , we have $\begin{array} { r } { \sum _ { i = 1 } ^ { k } s _ { [ i ] } = m i n _ { \lambda \in \mathbb { R } } \{ k \lambda + \sum _ { i = 1 } ^ { n } [ s _ { i } - \lambda ] _ { + } \} } \end{array}$ , of which $s _ { [ k ] }$ is an optimum solution.

From Lemma A.1, we have

$$
\begin{array}{l} \min _ {\theta} \psi_ {m, k} (S (\theta)) = \min _ {\theta} \big [ \phi_ {k} (S (\theta)) - \phi_ {m} (S (\theta)) \big ] \\ = \min _ {\theta} \left[ \min _ {\lambda \in \mathbb {R}} \Big \{k \lambda + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \lambda ] _ {+} \Big \} - \min _ {\hat {\lambda} \in \mathbb {R}} \Big \{m \hat {\lambda} + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \hat {\lambda} ] _ {+} \Big \} \right]. \end{array}
$$

If the optimal solution $\theta ^ { * }$ is achieved, from Lemma $\mathrm { A . 1 }$ , we get $\lambda = s _ { [ k ] }$ and $\hat { \lambda } = s _ { [ m ] }$ Therefore, $\hat { \lambda } > \lambda$ because $k > m$

## A.2 Proof of Equation (3)

Proof Before introducing the sub-gradient of $\phi _ { m } ( S ( \theta ) )$ , we provide a very useful characterization of diferentiable properties of the optimal value function (Bertsekas, 1971, Proposition A.22), which is also an extension of Danskin’s theorem (Danskin, 2012).

Lemma A.2 Let $\phi : \mathbb { R } ^ { n } \times \mathbb { R } ^ { m }  ( - \infty , \infty ]$ be a function and let Y be a compact subset of $\mathbb { R } ^ { m }$ . Assume further that for every vector $y \in Y$ the function $\phi ( \cdot , y ) : \mathbb { R } ^ { n } \to ( - \infty , \infty ]$ is a closed proper convex function. Consider the function f defined as $f ( x ) = s u p _ { y \in Y } \phi ( x , y )$ , then if f is finite somewhere, it is a closed proper convex function. Furthermore, $i f i n t ( d o m f ) \neq \emptyset$ and $\phi$ is continuous on the set $i n t ( d o m f ) \times Y$ , then for every $x \in i n t ( d o m f )$ we have $\partial f ( x ) =$ conv $\{ \partial \phi ( x , \overline { { y } } ) | \overline { { y } } \in \overline { { Y } } ( x ) \}$ , where $\overline { { Y } } ( \boldsymbol { x } )$ is the set $\overline { { Y } } ( x ) = \{ \overline { { y } } \in Y | \phi ( x , \overline { { y } } ) = m a x _ { y \in Y } \phi ( x , y ) \}$

We apply Lemma A.2 with a new notation $\phi _ { m } ( \theta , \hat { \lambda } ) = m \hat { \lambda } + \textstyle \sum _ { i = 1 } ^ { n } [ s _ { i } ( \theta ) - \hat { \lambda } ] _ { + }$ . Suppose $\theta \in \mathbb { R } ^ { n }$ and $\hat { \lambda } \in \mathbb { R }$ , the function $\phi _ { m } : \mathbb { R } ^ { n } \times \mathbb { R }  ( - \infty , \infty ]$ . Let Y be a compact subset of R and for every $\hat { \lambda } \in Y$ , it is obvious that the function $\phi _ { m } ( \cdot , \hat { \lambda } ) : \mathbb { R } ^ { n }  ( - \infty , \infty ]$ is a closed proper convex function w.r.t θ from the second term of $\operatorname { E q . } ( 1 )$ .

Consider a function f defined as $f ( \theta ) = \operatorname* { s u p } _ { \hat { \lambda } \in Y } \phi ( \theta , \lambda )$ , since $f$ is finite somewhere, it is a closed proper convex function. The interior of the efective domain of f is nonempty, and that $\phi _ { m }$ is continuous on the set $i n t ( d o m f ) \times Y$ . The condition of lemma A.2 is satisfied.

$\forall \theta \in i n t ( d o m f )$ , we have

$$
\partial f (\theta) = c o n v \{\partial \phi_ {m} (\theta , \overline {{\lambda}}) | \overline {{\lambda}} \in \overline {{Y}} (\theta) \},
$$

where

$$
\overline {{Y}} (\theta) = \{\overline {{\lambda}} \in Y | \phi_ {m} (\theta , \overline {{\lambda}}) = m a x _ {\hat {\lambda} \in Y} \phi_ {m} (\theta , \hat {\lambda}) \} = \{\overline {{\lambda}} \in Y | - \phi_ {m} (\theta , \overline {{\lambda}}) = - m i n _ {\hat {\lambda} \in Y} \phi_ {m} (\theta , \hat {\lambda}) \}.
$$

As we know $- m i n _ { \hat { \lambda } \in Y } \phi _ { m } ( \theta , \hat { \lambda } ) = - \phi _ { m } ( S ( \theta ) )$ . This means the subdiferential of f w.r.t θ exists when we set the optimal value of $\hat { \lambda }$ .

From the above and the lemma A.1, we can get the sub-gradient $\hat { \theta } \in \partial \phi _ { m } ( S ( \theta ) ) =$ $\textstyle \sum _ { i = 1 } ^ { n } \partial s _ { i } ( \theta ) \cdot \mathbb { I } _ { [ s _ { i } ( \theta ) > \hat { \lambda } ] }$ , where λ<sup>ˆ</sup> equals to $s _ { [ m ] } ( \theta )$ .

## A.3 Proof of Theorem 2

Proof The proof of this proposition is similar to the proof of proposition 1 in the paper Fujiwara et al. (2017). However, they only discuss the linear case of $s _ { i } ( \theta )$ . Under the constraints, we can rewrite the formula in Theorem 2 as

$$
\begin{array}{c} (k - m) \lambda + \sum_ {i = 1} ^ {n} q _ {i} [ s _ {i} (\theta) - \lambda ] _ {+} = (k - m) \lambda + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \lambda ] _ {+} - \sum_ {i = 1} ^ {n} (1 - q _ {i}) [ s _ {i} (\theta) - \lambda ] _ {+} \\ = k \lambda + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \lambda ] _ {+} - \sum_ {i = 1} ^ {n} (1 - q _ {i}) \{[ s _ {i} (\theta) - \lambda ] _ {+} + \lambda \}. \end{array}
$$

The last equality holds because $\begin{array} { r } { \sum _ { i = 1 } ^ { n } ( 1 - q _ { i } ) = n - ( n - m ) = m } \end{array}$

For the term $\textstyle \sum _ { i = 1 } ^ { n } ( 1 - q _ { i } ) \{ [ s _ { i } ( \theta ) - \lambda ] _ { + } + \lambda \} $ , we assume $s _ { i } ( \theta ^ { * } ) , \forall i$ , are sorted in descending order when getting the optimal model parameter $\theta ^ { * }$ . For example, $s _ { 1 } ( \theta ^ { * } ) \geq s _ { 2 } ( \theta ^ { * } ) \geq \cdot \cdot \cdot \geq$ $s _ { n } ( \theta ^ { * } )$ . Since $\lambda ^ { * } \geq 0$ , the optimal $q ^ { * }$ should be $q _ { 1 } ^ { * } = \cdot \cdot \cdot = q _ { m } ^ { * } = 0 , q _ { m + 1 } ^ { * } = \cdot \cdot \cdot = q _ { n } ^ { * } = 1$ Note that $\lambda ^ { * }$ must be an optimal solution of the problem

$$
\min _ {\lambda} (k - m) \lambda + \sum_ {i = m + 1} ^ {n} q _ {i} ^ {*} [ s _ {i} (\theta^ {*}) - \lambda ] _ {+}.
$$

From Lemma A.1, we know $s _ { m + 1 } ( \theta ^ { * } ) \geq \lambda ^ { * }$ , which implies that $s _ { i } ( \theta ^ { * } ) - \lambda ^ { * } \geq 0$ holds for $q _ { i } < 1$ . Therefore, $\begin{array} { r } { \sum _ { i = 1 } ^ { n } ( 1 - q _ { i } ) \{ [ s _ { i } ( \theta ) - \lambda ] _ { + } + \lambda \} = \sum _ { i = 1 } ^ { n } ( 1 - q _ { i } ) s _ { i } ( \theta ) } \end{array}$ . Furthermore, we know

$$
\min _ {\hat {\lambda}} \left\{m \hat {\lambda} + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \hat {\lambda} ] _ {+} \right\} = \max _ {q} \left\{\sum_ {i = 1} ^ {n} (1 - q _ {i}) s _ {i} (\theta) \Big | q _ {i} \in [ 0, 1 ], | | q | | _ {0} = n - m \right\}.
$$

Then we get

$$
\begin{array}{c} \min _ {\lambda , q} (k - m) \lambda + \sum_ {i = 1} ^ {n} q _ {i} [ s _ {i} (\theta) - \lambda ] _ {+} \quad s. t. q _ {i} \in [ 0, 1 ], | | q | | _ {0} = n - m \\ = \min _ {\lambda} \left\{k \lambda + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \lambda ] _ {+} \right\} - \min _ {\hat {\lambda}} \left\{m \hat {\lambda} + \sum_ {i = 1} ^ {n} [ s _ {i} (\theta) - \hat {\lambda} ] _ {+} \right\}. \end{array}
$$

## A.4 Proof of Theorem 4

Proof Without loss of generality, by normalization we can assume $s ( 0 ) = 1$ which can be satisfied by scaling. For any fixed $x \in \mathcal { X }$ , by the definition of $f ^ { * } = \arg$ inf $\mathcal { L } ( f , \lambda ^ { * } , \hat { \lambda } ^ { * } )$ , we know that

$$
f ^ {*} (x) = t ^ {*} = \arg \inf _ {t \in \mathbb {R}} \mathbb {E} \Big [ [ s (Y t) - \lambda^ {*} ] _ {+} - [ s (Y t) - \hat {\lambda} ^ {*} ] _ {+} \Big | X = x \Big ].
$$

Notice the assumption $\hat { \lambda } ^ { * } > \lambda ^ { * }$ and recall $\eta ( x ) = P ( y = 1 | x )$ . We need to show that $t ^ { * } > 0$ for $\eta ( x ) > 1 / 2$ and $t ^ { * } < 0 \mathrm { i f } \eta ( x ) < 1 / 2$ . Indeed, if ${ t ^ { * } } \neq 0$ , then, by the definition of $t ^ { * }$ , we have that

$$
\mathbb {E} \left[ \left[ s (Y t ^ {*}) - \lambda^ {*} \right] _ {+} - \left[ s (Y t ^ {*}) - \hat {\lambda} ^ {*} \right] _ {+} \mid X = x \right] <   \mathbb {E} \left[ \left[ s (- Y t ^ {*}) - \lambda^ {*} \right] _ {+} - \left[ s (- Y t ^ {*}) - \hat {\lambda} ^ {*} \right] _ {+} \mid X = x \right].
$$

The above inequality is identical to

$$
\left[ \left((s (t ^ {*}) - \lambda^ {*}) _ {+} - (s (t ^ {*}) - \hat {\lambda} ^ {*}) _ {+}\right) - \left((s (- t ^ {*}) - \lambda^ {*}) _ {+} - (s (- t ^ {*}) - \hat {\lambda} ^ {*}) _ {+}\right) \right] [ 2 \eta (x) - 1 ] <   0.
$$

Since $\hat { \lambda } ^ { * } > \lambda ^ { * }$ , we have that that $g ( s ) = ( s - \lambda ^ { * } ) _ { + } - ( s - { \hat { \lambda } } ^ { * } ) .$ <sub>+</sub> is a non-decreasing function of variable s. Then, if $\begin{array} { r } { \eta ( { \boldsymbol x } ) > \frac { 1 } { 2 } } \end{array}$ we must have $g ( s ( t ^ { * } ) ) < g ( s ( - t ^ { * } ) )$ which indicates $s ( t ^ { * } ) < s ( - t ^ { * } )$ . From the non-increasing property of s on $\mathbb { R } , s ( t )$ is also a convex function and $s ^ { \prime } ( 0 ) < 0$ immediately indicates $t ^ { * } > 0$ . Likewise, we can show that $t ^ { * } < 0$ for $\eta ( x ) < 1 / 2$

To prove $t = 0$ is not a minimizer, without loss of generality, assume $\begin{array} { r } { \eta ( x ) > \frac { 1 } { 2 } } \end{array}$ . We need to consider two conditions as follows,

1. If $0 \leq \lambda ^ { * } < \hat { \lambda } ^ { * } \leq 1$ and $s ( 0 ) = 1$ , then

$$
\begin{array}{l} A = \mathbb {E} \Big [ [ s (0) - \lambda^ {*} ] _ {+} - [ s (0) - \hat {\lambda} ^ {*} ] _ {+} \Big | X = x \Big ] \\ \qquad = [ 1 - \lambda^ {*} ] _ {+} - [ 1 - \hat {\lambda} ^ {*} ] _ {+} \\ \qquad = \hat {\lambda} ^ {*} - \lambda^ {*}. \end{array}
$$

Since $s ^ { \prime } ( 0 ) < 0$ and s is non-increasing, there exists $t ^ { 0 } > t ^ { * } = 0 > - t ^ { 0 }$ , and $s ( - t ^ { 0 } ) > s ( 0 ) \geq$ $\hat { \lambda } ^ { * } > s ( t ^ { 0 } ) > \lambda ^ { * }$ . Let

$$
\begin{array}{r l} & B = \mathbb {E} \Big [ [ s (Y t ^ {0}) - \lambda^ {*} ] _ {+} - [ s (Y t ^ {0}) - \hat {\lambda} ^ {*} ] _ {+} \big | X = x \Big ] \\ & \quad = \Big ([ s (t ^ {0}) - \lambda^ {*} ] _ {+} - [ s (t ^ {0}) - \hat {\lambda} ^ {*} ] _ {+} \Big) \eta (x) + \Big ([ s (- t ^ {0}) - \lambda^ {*} ] _ {+} - [ s (- t ^ {0}) - \hat {\lambda} ^ {*} ] _ {+} \Big) \Big (1 - \eta (x) \Big) \\ & \quad = \Big ([ s (- t ^ {0}) - \lambda^ {*} ] _ {+} - [ s (- t ^ {0}) - \hat {\lambda} ^ {*} ] _ {+} \Big) \\ & \quad + \Big [ \Big ([ s (t ^ {0}) - \lambda^ {*} ] _ {+} - [ s (t ^ {0}) - \hat {\lambda} ^ {*} ] _ {+} \Big) - \Big ([ s (- t ^ {0}) - \lambda^ {*} ] _ {+} - [ s (- t ^ {0}) - \hat {\lambda} ^ {*} ] _ {+} \Big) \Big ] \eta (x) \\ & \quad = \hat {\lambda} ^ {*} - \lambda^ {*} + \Big [ s (t ^ {0}) - \lambda^ {*} - (\hat {\lambda} ^ {*} - \lambda^ {*}) \Big ] \eta (x). \end{array}
$$

Then

$$
B - A = (s (t ^ {0}) - \hat {\lambda} ^ {*}) \eta (x) <   0.
$$

Therefore, $t = 0$ is not a minimizer.

2. If $0 \leq \lambda ^ { * } \leq 1 < \hat { \lambda } ^ { * }$ and s(0) = 1, then

$$
\begin{array}{r l} & {\frac {d}{d t} \mathbb {E} [ [ s (Y t) - \lambda^ {*} ] _ {+} - [ s (Y t) - \hat {\lambda} ^ {*} ] _ {+} ] | _ {t = 0}} \\ & {= \frac {d}{d t} [ \eta (x) ([ s (t) - \lambda^ {*} ] _ {+} - [ s (t) - \hat {\lambda} ^ {*} ] _ {+}) + (1 - \eta (x)) ([ s (- t) - \lambda^ {*} ] _ {+} - [ s (- t) - \hat {\lambda} ^ {*} ] _ {+}) ] | _ {t = 0}} \\ & {= \frac {d}{d t} [ \eta (x) (s (t) - \lambda^ {*}) + (1 - \eta (x)) (s (- t) - \lambda^ {*}) ] | _ {t = 0}} \\ & {= [ \eta (x) s ^ {\prime} (t) - (1 - \eta (x)) s ^ {\prime} (- t) ] | _ {t = 0}} \\ & {= (2 \eta (x) - 1) s ^ {\prime} (0) <   0.} \end{array}
$$

Thus t = 0 is not a minimizer.

## A.5 Proof of Theorem 5

Proof First, we introduce a lemma from Brown (2007) and (Thomas and Learned-Miller, 2019, Theorem 1 and 2) as follows,

Lemma A.3 (Brown (2007); Thomas and Learned-Miller (2019)) Let $C _ { \alpha } [ s ] = \mathbb { E } [ s \vert s \geq V _ { \alpha } [ s ] ]$ and $\begin{array} { r } { \widehat { C } _ { \alpha } [ s ] : = \operatorname* { i n f } _ { \lambda \in \mathbb { R } } \{ \lambda + \frac { \mathrm { i } } { n \alpha } \sum _ { i = 1 } ^ { n } [ s _ { i } - \lambda ] _ { + } \} } \end{array}$ , if $s u p p ( s ) \subseteq [ a , b ]$ and s has a continuous distribution function, then for any $\delta \in ( 0 , 1 ]$

$$
\begin{array}{l} \operatorname * {P r} \left(C _ {\alpha} [ s ] \leq \widehat {C} _ {\alpha} [ s ] + (b - a) \sqrt {\frac {5 \ln (3 / \delta)}{\alpha n}}\right) \geq 1 - \delta , \\ \operatorname * {P r} \left(C _ {\alpha} [ s ] \geq \widehat {C} _ {\alpha} [ s ] - \frac {b - a}{\alpha} \sqrt {\frac {\ln (1 / \delta)}{2 n}}\right) \geq 1 - \delta . \end{array}
$$

This lemma tells us that bound the deviation of the empirical CVaR from the true CVaR with high probability. Based on this lemma, we can get

$$
\operatorname * {P r} \left(\nu (C _ {\nu} [ s (\theta) ] - \widehat {C} _ {\nu} [ s (\theta) ]) \leq \nu (b - a) \sqrt {\frac {5 \ln (3 / \delta)}{\nu n}}\right) \geq 1 - \delta ,\tag{A.1}
$$

$$
\operatorname * {P r} \left(\nu (C _ {\nu} [ s (\theta) ] - \widehat {C} _ {\nu} [ s (\theta) ]) \geq - (b - a) \sqrt {\frac {\ln (1 / \delta)}{2 n}}\right) \geq 1 - \delta ,\tag{A.2}
$$

$$
\operatorname * {P r} \left(- \mu (C _ {\mu} [ s (\theta) ] - \widehat {C} _ {\mu} [ s (\theta) ]) \geq - \mu (b - a) \sqrt {\frac {5 \ln (3 / \delta)}{\mu n}}\right) \geq 1 - \delta ,\tag{A.3}
$$

$$
\operatorname * {P r} \left(- \mu (C _ {\mu} [ s (\theta) ] - \widehat {C} _ {\mu} [ s (\theta) ]) \leq (b - a) \sqrt {\frac {\ln (1 / \delta)}{2 n}}\right) \geq 1 - \delta .\tag{A.4}
$$

Combining Eq.(A.1) and Eq.(A.4), we obtain

$$
\operatorname * {P r} \left(\mathcal {L} (f, \lambda , \hat {\lambda}) - \widehat {\mathcal {L}} (f, \lambda , \hat {\lambda}) \leq (b - a) \left[ \sqrt {\frac {5 \nu \ln (3 / \delta)}{n}} + \sqrt {\frac {\ln (1 / \delta)}{2 n}} \right]\right) \geq 1 - \delta .\tag{A.5}
$$

Combining Eq.(A.2) and Eq.(A.3), we obtain

$$
\operatorname * {P r} \left(\mathcal {L} (f, \lambda , \hat {\lambda}) - \widehat {\mathcal {L}} (f, \lambda , \hat {\lambda}) \geq - (b - a) \left[ \sqrt {\frac {5 \mu \ln (3 / \delta)}{n}} + \sqrt {\frac {\ln (1 / \delta)}{2 n}} \right]\right) \geq 1 - \delta .\tag{A.6}
$$

Substituting $\nu = k / n$ and $\mu = m / n$ into Eq.(A.5) and $\mathrm { E q . ( A . 6 ) }$ , we get desired results.

## A.6 Proof of Proposition 6

Proof We just need to prove that $\begin{array} { r } { \operatorname* { m a x } _ { y \notin Y } \theta _ { y } ^ { \top } x \ge \theta _ { [ | Y | + 1 ] } ^ { \top } x } \end{array}$ . If this is not the case, then for any label $y \not \in Y$ , then its rank in the ranked list is no more than $| Y | + 2$ , then the sum of total number of such labels is not larger than $l - ( | Y | + 2 ) + 1 = l - | Y | - 1$ . And the total number of labels will be $| Y | + | \{ y \not \in Y \} | \leq l - 1 \neq l$ , which is a contradiction.

## A.7 Proof of Lemma 7

Proof

$$
\begin{array}{l} \sum_ {i = m + 1} ^ {n} s _ {[ i ]} = \sum_ {i = 1} ^ {n} s _ {i} - \sum_ {i = 1} ^ {m} s _ {[ i ]} \\ \qquad = \sum_ {i = 1} ^ {n} s _ {i} - \min _ {\lambda} \bigg \{m \lambda + \sum_ {i = 1} ^ {n} [ s _ {i} - \lambda ] _ {+} \bigg \} \\ \qquad = - \min _ {\lambda} \bigg \{- \sum_ {i = 1} ^ {n} (s _ {i} - \lambda) - (n - m) \lambda + \sum_ {i = 1} ^ {n} [ s _ {i} - \lambda ] _ {+} \bigg \}. \\ \qquad = - \min _ {\lambda} \bigg \{- (n - m) \lambda + \sum_ {i = 1} ^ {n} [ \lambda - s _ {i} ] _ {+} \bigg \} \\ \qquad = \max _ {\lambda} \bigg \{(n - m) \lambda - \sum_ {i = 1} ^ {n} [ \lambda - s _ {i} ] _ {+} \bigg \} \end{array}
$$

The second equation holds because of Lemma A.1. The fourth equation holds because the fact of $[ a ] _ { + } - a = [ - a ] _ { + }$ . Define $\begin{array} { r } { L ( \lambda ) = ( n - m ) \lambda - \sum _ { i = 1 } ^ { n } [ \lambda - s _ { i } ] _ { + } } \end{array}$ . Let $\lambda = \alpha \lambda _ { 1 } + ( 1 - \alpha ) \lambda _ { 2 }$ where $1 \geq \alpha \geq 0$ , we have

$$
\begin{array}{l} L (\alpha \lambda_ {1} + (1 - \alpha) \lambda_ {2}) \\ = \alpha (n - m) \lambda_ {1} + (1 - \alpha) (n - m) \lambda_ {2} - \sum_ {i = 1} ^ {n} [ \alpha \lambda_ {1} + (1 - \alpha) \lambda_ {2} - s _ {i} ] _ {+} \\ = \alpha (n - m) \lambda_ {1} + (1 - \alpha) (n - m) \lambda_ {2} - \sum_ {i = 1} ^ {m} [ \alpha (\lambda_ {1} - s _ {i}) + (1 - \alpha) (\lambda_ {2} - s _ {i}) ] _ {+} \\ \geq \alpha (n - m) \lambda_ {1} + (1 - \alpha) (n - m) \lambda_ {2} - \alpha \sum_ {i = 1} ^ {n} [ \lambda_ {1} - s _ {i} ] _ {+} - (1 - \alpha) \sum_ {i = 1} ^ {n} [ \lambda_ {2} - s _ {i} ] _ {+} \\ = \alpha L (\lambda_ {1}) + (1 - \alpha) L (\lambda_ {2}). \end{array}
$$

Therefore, $\scriptstyle \sum _ { i = m + 1 } ^ { n } s _ { [ i ] }$ is a concave function.

## Appendix B. Additional Experimental Details

## B.1 Training Settings on Toy Examples for Aggregate Loss

To reproduce the experimental results of AoRR on synthetic data, we provide the details about the settings when we are training the model in Table 11. For example, the learning rate, the number of epochs for the outer loop, and the number of epochs for the inner loop.

<table><tr><td rowspan="2">Data Sets</td><td rowspan="2">Outliers</td><td colspan="3">Logistic loss</td><td colspan="3">Hinge loss</td></tr><tr><td>LR</td><td># OE</td><td># IE</td><td>LR</td><td># OE</td><td># IE</td></tr><tr><td rowspan="7">Multi-modal data</td><td>1</td><td>0.01</td><td>100</td><td>1000</td><td>0.01</td><td>5</td><td>1000</td></tr><tr><td>2</td><td>0.01</td><td>100</td><td>1000</td><td>0.01</td><td>5</td><td>1000</td></tr><tr><td>3</td><td>0.01</td><td>100</td><td>1000</td><td>0.01</td><td>5</td><td>1000</td></tr><tr><td>4</td><td>0.01</td><td>100</td><td>1000</td><td>0.01</td><td>5</td><td>1000</td></tr><tr><td>5</td><td>0.01</td><td>100</td><td>1000</td><td>0.01</td><td>5</td><td>1000</td></tr><tr><td>10</td><td>0.01</td><td>100</td><td>1000</td><td>0.01</td><td>5</td><td>1000</td></tr><tr><td>20</td><td>0.01</td><td>100</td><td>1000</td><td>0.01</td><td>5</td><td>1000</td></tr><tr><td>Imbalanced data</td><td>1</td><td>0.01</td><td>100</td><td>1000</td><td>0.01</td><td>5</td><td>1000</td></tr></table>

LR: Learning Rate, OE: Outer Epochs, IE: Inner epochs  
Table 11: AoRR settings on toy experiments.

## B.2 Training Settings on Real Data Sets for Aggregate Loss

We provide a reference for setting parameters to reproduce our AoRR experiments on real data sets. Table 12 contains the settings for individual logistic loss. Table 13 is for individual hinge loss. Table 14 is for multi-class learning.

<table><tr><td>Data Sets</td><td>k</td><td>m</td><td>C</td><td># Outer epochs</td><td># Inner epochs</td><td>Learning rate</td></tr><tr><td>Monk</td><td>70</td><td>20</td><td> $10^{4}$ </td><td>5</td><td>2000</td><td>0.01</td></tr><tr><td>Australian</td><td>80</td><td>3</td><td> $10^{4}$ </td><td>10</td><td>1000</td><td>0.01</td></tr><tr><td>Phoneme</td><td>1400</td><td>100</td><td> $10^{4}$ </td><td>10</td><td>1000</td><td>0.01</td></tr><tr><td>Titanic</td><td>500</td><td>10</td><td> $10^{4}$ </td><td>10</td><td>1000</td><td>0.01</td></tr><tr><td>Splice</td><td>450</td><td>50</td><td> $10^{4}$ </td><td>10</td><td>1000</td><td>0.01</td></tr></table>

Table 12: AoRR settings on real data sets for individual logistic loss.

<table><tr><td>Data Sets</td><td>k</td><td>m</td><td>C</td><td># Outer epochs</td><td># Inner epochs</td><td>Learning rate</td></tr><tr><td>Monk</td><td>70</td><td>45</td><td> $10^{4}$ </td><td>5</td><td>1000</td><td>0.01</td></tr><tr><td>Australian</td><td>80</td><td>3</td><td> $10^{4}$ </td><td>5</td><td>1000</td><td>0.01</td></tr><tr><td>Phoneme</td><td>1400</td><td>410</td><td> $10^{4}$ </td><td>10</td><td>500</td><td>0.01</td></tr><tr><td>Titanic</td><td>500</td><td>10</td><td> $10^{4}$ </td><td>5</td><td>500</td><td>0.01</td></tr><tr><td>Splice</td><td>450</td><td>50</td><td> $10^{4}$ </td><td>10</td><td>1000</td><td>0.01</td></tr></table>

Table 13: AoRR settings on real data sets for individual hinge loss.

<table><tr><td>Data Sets</td><td>Learning rate (“warm-up”)</td><td>Learning rate (“non-warm-up”)</td><td># Outer epochs</td><td># Inner epochs</td></tr><tr><td>MNIST</td><td>0.4</td><td>0.5</td><td>20</td><td>5000</td></tr></table>

Table 14: AoRR settings on MNIST for multi-class learning.

## B.3 Training Settings for Multi-label Learning

The settings for TKML on three real data sets are shown in Table 15.

<table><tr><td>Data Sets</td><td>C</td><td>#Outer epochs</td><td>#Inner epochs</td><td>Learning rate</td></tr><tr><td>Emotions</td><td> $10^{4}$ </td><td>20</td><td>1000</td><td>0.1</td></tr><tr><td>Scene</td><td> $10^{4}$ </td><td>20</td><td>1000</td><td>0.1</td></tr><tr><td>Yeast</td><td> $10^{4}$ </td><td>20</td><td>1000</td><td>0.1</td></tr></table>

Table 15: TKML settings on each data set.

## B.4 Training Settings for Multi-class Learning

Training settings for the MNIST data set in diferent noise level can be found in Table 16.

<table><tr><td>Noise level</td><td>#Outer epochs</td><td>#Inner epochs</td><td>Learning rate</td></tr><tr><td>0.2</td><td>27</td><td>2000</td><td>0.1</td></tr><tr><td>0.3</td><td>25</td><td>2000</td><td>0.1</td></tr><tr><td>0.4</td><td>21</td><td>2000</td><td>0.1</td></tr></table>

Table 16: TKML settings on the MNIST data set in diferent noise levels.

## B.5 Training Settings for TKML-AoRR Learning

Training settings for the Yeast data set in diferent noise level can be found in Table 17.

<table><tr><td>Noise level</td><td>#Epochs</td><td>Learning rate</td></tr><tr><td>0</td><td>1000</td><td>0.3</td></tr><tr><td>0.1</td><td>1000</td><td>0.3</td></tr><tr><td>0.2</td><td>1000</td><td>0.3</td></tr><tr><td>0.3</td><td>1000</td><td>0.3</td></tr></table>

Table 17: TKML-AoRR settings on the Yeast data set in diferent noise levels.

## References

Jesús Alcalá-Fdez, Alberto Fernández, Julián Luengo, Joaquín Derrac, Salvador García, Luciano Sánchez, and Francisco Herrera. Keel data-mining software tool: data set repository, integration of algorithms and experimental analysis framework. Journal of Multiple-Valued Logic & Soft Computing, 17, 2011.

Peter L Bartlett, Michael I Jordan, and Jon D McAulife. Convexity, classification, and risk bounds. Journal of the American Statistical Association, 101(473):138–156, 2006.

Dimitri P Bertsekas. Control of uncertain systems with a set-membership description of the uncertainty. PhD thesis, Massachusetts Institute of Technology, 1971.

Sanjay P Bhat and LA Prashanth. Concentration of risk measures: A wasserstein distance approach. In Advances in Neural Information Processing Systems, pages 11739–11748, 2019.

Zalán Borsos, Mojmir Mutny, and Andreas Krause. Coresets via bilevel optimization for continual learning and streaming. Advances in Neural Information Processing Systems, 33, 2020.

Léon Bottou and Olivier Bousquet. The tradeofs of large scale learning. In Advances in neural information processing systems, pages 161–168, 2008.

David B Brown. Large deviations bounds for estimating conditional value-at-risk. Operations Research Letters, 35(6):722–730, 2007.

Andreas Buja, Werner Stuetzle, and Yi Shen. Loss functions for binary class probability estimation and classification: Structure and applications. Working draft, November, 3, 2005.

Xiaojun Chang, Yao-Liang Yu, and Yi Yang. Robust top-k multiclass svm for visual category recognition. In Proceedings of the 23rd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, pages 75–83, 2017.

Moses Charikar, Jacob Steinhardt, and Gregory Valiant. Learning from untrusted data. In Proceedings of the 49th Annual ACM SIGACT Symposium on Theory of Computing, pages 47–60, 2017.

Koby Crammer and Yoram Singer. On the algorithmic implementation of multiclass kernelbased vector machines. Journal of machine learning research, 2(Dec):265–292, 2001.

Koby Crammer and Yoram Singer. A family of additive online algorithms for category ranking. Journal of Machine Learning Research, 3(Feb):1025–1058, 2003.

John M Danskin. The theory of max-min and its application to weapons allocation problems, volume 5. Springer Science & Business Media, 2012.

Dheeru Dua and Casey Graf. UCI machine learning repository, 2017. URL http://archive. ics.uci.edu/ml.

Yanbo Fan, Siwei Lyu, Yiming Ying, and Baogang Hu. Learning with average top-k loss. In Advances in neural information processing systems, pages 497–505, 2017.

Yanbo Fan, Baoyuan Wu, Ran He, Bao-Gang Hu, Yong Zhang, and Siwei Lyu. Groupwise ranking loss for multi-label learning. IEEE Access, 8:21717–21727, 2020a.

Yanbo Fan, Baoyuan Wu, Ran He, Baogang Hu, Yong Zhang, and Siwei Lyu. Groupwise ranking loss for multi-label learning. IEEE Access, to appear, 2020b.

Jerome Friedman, Trevor Hastie, and Robert Tibshirani. The elements of statistical learning, volume 1. Springer series in statistics New York, 2001.

Shuhei Fujiwara, Akiko Takeda, and Takafumi Kanamori. Dc algorithm for extended robust support vector machine. Neural computation, 29(5):1406–1438, 2017.

Spyros Gidaris and Nikos Komodakis. Object detection via a multi-region and semantic segmentation-aware cnn model. In Proceedings of the IEEE international conference on computer vision, pages 1134–1142, 2015.

Ran He, Wei-Shi Zheng, and Bao-Gang Hu. Maximum correntropy criterion for robust face recognition. IEEE Transactions on Pattern Analysis and Machine Intelligence, 33(8): 1561–1576, 2010.

Dan Hendrycks, Mantas Mazeika, Duncan Wilson, and Kevin Gimpel. Using trusted data to train deep networks on labels corrupted by severe noise. In Advances in neural information processing systems, pages 10456–10465, 2018.

Shu Hu, Yiming Ying, Xin Wang, and Siwei Lyu. Learning by minimizing the sum of ranked range. Advances in Neural Information Processing Systems, 33, 2020.

Shu Hu, Lipeng Ke, Xin Wang, and Siwei Lyu. Tkml-ap: Adversarial attacks to top-k multilabel learning. In Proceedings of the IEEE/CVF International Conference on Computer Vision, pages 7649–7657, 2021.

Simon Jenni and Paolo Favaro. Deep bilevel learning. In Proceedings of the European conference on computer vision (ECCV), pages 618–633, 2018.

Takafumi Kanamori, Shuhei Fujiwara, and Akiko Takeda. Robustness of learning algorithms using hinge loss with outlier indicators. Neural Networks, 94:173–191, 2017.

Kenji Kawaguchi and Haihao Lu. Ordered sgd: A new stochastic optimization framework for empirical risk minimization. In International Conference on Artificial Intelligence and Statistics, pages 669–679, 2020.

Maksim Lapin, Matthias Hein, and Bernt Schiele. Top-k multiclass svm. In Advances in Neural Information Processing Systems, pages 325–333, 2015.

Maksim Lapin, Matthias Hein, and Bernt Schiele. Loss functions for top-k error: Analysis and insights. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pages 1468–1477, 2016.

Maksim Lapin, Matthias Hein, and Bernt Schiele. Analysis and optimization of loss functions for multiclass, top-k, and multilabel classification. IEEE transactions on pattern analysis and machine intelligence, 40(7):1533–1554, 2017.

Hoai An Le Thi and Tao Pham Dinh. Dc programming and dca: thirty years of developments. Mathematical Programming, 169(1):5–68, 2018.

Yann LeCun, Léon Bottou, Yoshua Bengio, and Patrick Hafner. Gradient-based learning applied to document recognition. Proceedings of the IEEE, 86(11):2278–2324, 1998.

Junnan Li, Richard Socher, and Steven CH Hoi. Dividemix: Learning with noisy labels as semi-supervised learning. arXiv preprint arXiv:2002.07394, 2020a.

Junnan Li, Caiming Xiong, Richard Socher, and Steven Hoi. Towards noise-resistant object detection with noisy annotations. arXiv preprint arXiv:2003.01285, 2020b.

Yuncheng Li, Yale Song, and Jiebo Luo. Improving pairwise ranking for multi-label image classification. In Proceedings of the IEEE conference on computer vision and pattern recognition, pages 3617–3625, 2017a.

Yuncheng Li, Jianchao Yang, Yale Song, Liangliang Cao, Jiebo Luo, and Li-Jia Li. Learning from noisy labels with distillation. In Proceedings of the IEEE International Conference on Computer Vision, pages 1910–1918, 2017b.

Tsung-Yi Lin, Priya Goyal, Ross Girshick, Kaiming He, and Piotr Dollár. Focal loss for dense object detection. In Proceedings of the IEEE international conference on computer vision, pages 2980–2988, 2017.

Yi Lin. A note on margin-based loss functions in classification. Statistics & probability letters, 68(1):73–82, 2004.

Wei Liu, Dragomir Anguelov, Dumitru Erhan, Christian Szegedy, Scott Reed, Cheng-Yang Fu, and Alexander C Berg. Ssd: Single shot multibox detector. In European conference on computer vision, pages 21–37. Springer, 2016.

Weifeng Liu, Puskal P Pokharel, and Jose C Principe. Correntropy: Properties and applications in non-gaussian signal processing. IEEE Transactions on signal processing, 55(11): 5286–5298, 2007.

Siwei Lyu, Yanbo Fan, Yiming Ying, and Bao-Gang Hu. Average top-k aggregate loss for supervised learning. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2020.

Yifei Ma, Li Li, Xiaolin Huang, and Shuning Wang. Robust support vector machine using least median loss penalty. IFAC Proceedings Volumes, 44(1):11208–11213, 2011.

Gjorgji Madjarov, Dragi Kocev, Dejan Gjorgjevikj, and Sašo Džeroski. An extensive experimental comparison of methods for multi-label learning. Pattern recognition, 45(9): 3084–3104, 2012.

Hamed Masnadi-Shirazi and Nuno Vasconcelos. On the design of loss functions for classification: theory, robustness to outliers, and savageboost. In Proceedings of the 21st International Conference on Neural Information Processing Systems, pages 1049–1056, 2008.

Feiping Nie, Xiaoqian Wang, and Heng Huang. Multiclass capped lp-norm svm for robust classifications. In Thirty-First AAAI Conference on Artificial Intelligence (AAAI 2017), 2017.

Wlodzimierz Ogryczak and Arie Tamir. Minimizing the sum of the k largest functions in linear time. Information Processing Letters, 85(3):117–122, 2003.

Alessandro Ortis, Giovanni Maria Farinella, and Sebastiano Battiato. Predicting social image popularity dynamics at time zero. IEEE Access, 7:171691–171706, 2019.

Giorgio Patrini, Alessandro Rozza, Aditya Krishna Menon, Richard Nock, and Lizhen Qu. Making deep neural networks robust to label noise: A loss correction approach. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pages 1944–1952, 2017.

Bilal Piot, Matthieu Geist, and Olivier Pietquin. Diference of convex functions programming applied to control with expert data. arXiv preprint arXiv:1606.01128, 2016.

LA Prashanth, Krishna Jagannathan, and Ravi Kolla. Concentration bounds for cvar estimation: The cases of light-tailed and heavy-tailed distributions. In International Conference on Machine Learning, pages 5577–5586. PMLR, 2020.

Alexander Rakhlin, Ohad Shamir, and Karthik Sridharan. Making gradient descent optimal for strongly convex stochastic optimization. arXiv preprint arXiv:1109.5647, 2011.

Ankit Singh Rawat, Aditya Krishna Menon, Andreas Veit, Felix Yu, Sashank J Reddi, and Sanjiv Kumar. Doubly-stochastic mining for heterogeneous retrieval. arXiv preprint arXiv:2004.10915, 2020.

Mark D Reid and Robert C Williamson. Composite binary losses. Journal of Machine Learning Research, 11(Sep):2387–2422, 2010.

Mengye Ren, Wenyuan Zeng, Bin Yang, and Raquel Urtasun. Learning to reweight examples for robust deep learning. arXiv preprint arXiv:1803.09050, 2018.

Cynthia Rudin. The p-norm push: A simple convex ranking algorithm that concentrates at the top of the list. Journal of Machine Learning Research, 10(78):2233–2271, 2009.

Leonard J Savage. Elicitation of personal probabilities and expectations. Journal of the American Statistical Association, 66(336):783–801, 1971.

Vatsal Shah, Xiaoxia Wu, and Sujay Sanghavi. Choosing the sample with lowest loss makes sgd robust. In International Conference on Artificial Intelligence and Statistics, pages 2120–2130. PMLR, 2020.

Shai Shalev-Shwartz and Yonatan Wexler. Minimizing the maximal loss: How and why. In ICML, pages 793–801, 2016.

Alexander Shapiro, Darinka Dentcheva, and Andrzej Ruszczyński. Lectures on stochastic programming: modeling and theory. SIAM, 2014.

Yanyao Shen and Sujay Sanghavi. Learning with bad training data via iterative trimmed loss minimization. In International Conference on Machine Learning, pages 5739–5748. PMLR, 2019.

Abhinav Shrivastava, Abhinav Gupta, and Ross Girshick. Training region-based object detectors with online hard example mining. In Proceedings of the IEEE conference on computer vision and pattern recognition, pages 761–769, 2016.

Emir H Shuford, Arthur Albert, and H Edward Massengill. Admissible probability measurement procedures. Psychometrika, 31(2):125–145, 1966.

Nathan Srebro and Ambuj Tewari. Stochastic optimization for machine learning. ICML Tutorial, 2010.

Pham Dinh Tao and Le Thi Hoai An. Convex analysis approach to dc programming: theory, algorithms and applications. Acta mathematica vietnamica, 22(1):289–355, 1997.

Pham Dinh Tao et al. Algorithms for solving a class of nonconvex optimization problems. methods of subgradients. In North-Holland Mathematics Studies, volume 129, pages 249–271. Elsevier, 1986.

Hoai An Le Thi, Hoai Minh Le, Duy Nhat Phan, and Bach Tran. Stochastic dca for the large-sum of non-convex functions problem and its application to group variable selection in classification. In Proceedings of the 34th International Conference on Machine Learning-Volume 70, pages 3394–3403. JMLR. org, 2017.

Hoai An Le Thi, Hoai Minh Le, Duy Nhat Phan, and Bach Tran. Stochastic dca for minimizing a large sum of dc functions with application to multi-class logistic regression. arXiv preprint arXiv:1911.03992, 2019.

Philip Thomas and Erik Learned-Miller. Concentration inequalities for conditional value at risk. In International Conference on Machine Learning, pages 6225–6233. PMLR, 2019.

Nicolas Usunier, David Bufoni, and Patrick Gallinari. Ranking with ordered weighted pairwise classification. In Proceedings of the 26th annual international conference on machine learning, pages 1057–1064, 2009.

Vladimir Vapnik. Principles of risk minimization for learning theory. In Advances in neural information processing systems, pages 831–838, 1992.

Vladimir Vapnik. The nature of statistical learning theory. Springer science & business media, 2013.

Andreas Veit, Neil Alldrin, Gal Chechik, Ivan Krasin, Abhinav Gupta, and Serge Belongie. Learning from noisy large-scale datasets with minimal supervision. In Proceedings of the IEEE conference on computer vision and pattern recognition, pages 839–847, 2017.

Yisen Wang, Xingjun Ma, Zaiyi Chen, Yuan Luo, Jinfeng Yi, and James Bailey. Symmetric cross entropy for robust learning with noisy labels. In Proceedings of the IEEE International Conference on Computer Vision, pages 322–330, 2019.

Kai Wei, Rishabh Iyer, and Jef Bilmes. Submodularity in data subset selection and active learning. In International Conference on Machine Learning, pages 1954–1963. PMLR, 2015.

Jason Weston, Samy Bengio, and Nicolas Usunier. Wsabie: scaling up to large vocabulary image annotation. In Proceedings of the Twenty-Second international joint conference on Artificial Intelligence-Volume Volume Three, pages 2764–2770, 2011.

Yichao Wu and Yufeng Liu. Robust truncated hinge loss support vector machines. Journal of the American Statistical Association, 102(479):974–983, 2007.

Forest Yang and Sanmi Koyejo. On the consistency of top-k surrogate losses. In International Conference on Machine Learning, pages 10727–10735. PMLR, 2020.

Yaoliang Yu, Min Yang, Linli Xu, Martha White, and Dale Schuurmans. Relaxed clipping: A global training method for robust regression and classification. In NIPS, pages 2532–2540, 2010.

Min-Ling Zhang and Zhi-Hua Zhou. Multilabel neural networks with applications to functional genomics and text categorization. IEEE transactions on Knowledge and Data Engineering, 18(10):1338–1351, 2006.

Min-Ling Zhang and Zhi-Hua Zhou. A review on multi-label learning algorithms. IEEE transactions on knowledge and data engineering, 26(8):1819–1837, 2013.

Zhilu Zhang and Mert Sabuncu. Generalized cross entropy loss for training deep neural networks with noisy labels. In Advances in neural information processing systems, pages 8778–8788, 2018.